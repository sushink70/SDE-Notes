# IGMP — Internet Group Management Protocol
## Complete Technical Reference for Threat Intelligence Analysts & Network Engineers

---

```
████████╗ ██████╗ ███╗   ███╗██████╗
   ██║   ██╔════╝ ████╗ ████║██╔══██╗
   ██║   ██║  ███╗██╔████╔██║██████╔╝
   ██║   ██║   ██║██║╚██╔╝██║██╔═══╝
   ██║   ╚██████╔╝██║ ╚═╝ ██║██║
   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝

Internet Group Management Protocol
RFC 1112 → RFC 2236 → RFC 3376
```

---

## Table of Contents

1. [Protocol Origin and Purpose — The "Why"](#1-protocol-origin-and-purpose)
2. [IP Multicast Fundamentals](#2-ip-multicast-fundamentals)
3. [IGMP in the Network Stack — Layered Position](#3-igmp-in-the-network-stack)
4. [IGMPv1 — RFC 1112 (1989)](#4-igmpv1)
5. [IGMPv2 — RFC 2236 (1997)](#5-igmpv2)
6. [IGMPv3 — RFC 3376 (2002)](#6-igmpv3)
7. [IGMP Message Formats — Byte-Level Detail](#7-igmp-message-formats)
8. [Protocol State Machines](#8-protocol-state-machines)
9. [IGMP Timers and Robustness Variables](#9-igmp-timers-and-robustness-variables)
10. [IGMP Snooping](#10-igmp-snooping)
11. [Multicast Routing Interaction](#11-multicast-routing-interaction)
12. [MLDv1/MLDv2 — IPv6 Equivalent](#12-mldv1mldv2)
13. [Security Implications and Attack Vectors](#13-security-implications-and-attack-vectors)
14. [IGMP in Malware and APT Context](#14-igmp-in-malware-and-apt-context)
15. [Packet Capture and Analysis](#15-packet-capture-and-analysis)
16. [C Implementation — Raw Socket IGMP Stack](#16-c-implementation)
17. [Rust Implementation — Type-Safe IGMP Engine](#17-rust-implementation)
18. [YARA and Sigma Detection Rules](#18-yara-and-sigma-detection-rules)
19. [Wireshark Filters and Analysis Workflow](#19-wireshark-filters-and-analysis-workflow)
20. [The Expert Mental Model](#20-the-expert-mental-model)

---

## 1. Protocol Origin and Purpose

### Why IGMP Exists

Before IGMP, IP multicast had no membership signaling mechanism. When a host wanted to receive traffic sent to a multicast group address (a Class D address: `224.0.0.0/4`), there was no way for routers to know which segments had interested receivers. Without this knowledge, multicast traffic would have to be flooded everywhere — annihilating network efficiency at scale.

**IGMP solves a single fundamental problem:**

> *How does a multicast-capable router know which of its directly connected hosts want to receive traffic for a given multicast group?*

IGMP is the signaling protocol that runs between **hosts and their directly attached routers** (Layer 3 boundary). It is **not** a routing protocol — it does not propagate group membership information between routers. That job belongs to multicast routing protocols (PIM, DVMRP, MOSPF). IGMP is purely local-link signaling.

### Protocol Genealogy

```
Year    RFC       Version   Key Additions
────────────────────────────────────────────────────────
1988    RFC 988   IGMPv0    First draft, never widely deployed
1989    RFC 1112  IGMPv1    Host Extensions for IP Multicasting
                            Established Class D addressing
                            Query/Report model
1997    RFC 2236  IGMPv2    Leave Group messages
                            Group-Specific Queries
                            Max Response Time field
                            Querier Election mechanism
2002    RFC 3376  IGMPv3    Source-Specific Multicast (SSM)
                            INCLUDE/EXCLUDE filter modes
                            Group-and-Source-Specific Queries
2004    RFC 4604  IGMPv3    Clarifications and corrections
```

### The Three Roles in IGMP

```
┌─────────────────────────────────────────────────────────┐
│                    IGMP PARTICIPANTS                      │
├─────────────────┬──────────────────┬────────────────────┤
│   HOST          │   ROUTER         │   QUERIER          │
│                 │                  │                    │
│ Sends Reports   │ Receives Reports │ Elected router     │
│ (joins/leaves)  │ Sends Queries    │ that sends all     │
│                 │ Maintains group  │ Membership Queries │
│                 │ membership table │ on a subnet        │
└─────────────────┴──────────────────┴────────────────────┘
```

**Critical insight:** On a multi-router segment, only ONE router acts as the "Querier" — the router with the lowest IP address (IGMPv2+). This prevents duplicate Query floods from multiple routers. The querier election is implicit, based on IP address comparison, not an explicit negotiation message.

---

## 2. IP Multicast Fundamentals

### Class D Address Space

IPv4 multicast addresses occupy the range `224.0.0.0` to `239.255.255.255`. The high 4 bits are always `1110` in binary.

```
Bit Layout of a Class D IPv4 Address:
┌────────────────────────────────────────────────────┐
│ 1 1 1 0 | xxxx xxxx | xxxx xxxx | xxxx xxxx xxxx   │
│  ^^^^                                               │
│  0xE0... identifies Class D                         │
└────────────────────────────────────────────────────┘

Range:  224.0.0.0  = 1110 0000 . 0000 0000 . 0000 0000 . 0000 0000
        239.255.255.255 = 1110 1111 . 1111 1111 . 1111 1111 . 1111 1111
```

### Multicast Address Ranges — Significance

```
Range                   Scope            Description
─────────────────────────────────────────────────────────────────────
224.0.0.0/24            Link-Local       Reserved, TTL=1
                                         Never forwarded by routers
  224.0.0.1               ALL-HOSTS      All multicast-capable hosts
  224.0.0.2               ALL-ROUTERS    All multicast routers
  224.0.0.5               OSPF routers
  224.0.0.6               OSPF DR/BDR
  224.0.0.13              PIM routers
  224.0.0.22              IGMPv3 reports (all routers)

224.0.1.0/24            Internetwork     Globally scoped
  224.0.1.1               NTP
  224.0.1.39              Cisco-RP-Announce
  224.0.1.40              Cisco-RP-Discovery

224.0.2.0 -             AD-HOC Block 1   Globally scoped applications
224.0.255.255

232.0.0.0/8             SSM Range        Source-Specific Multicast
                                         Only valid with IGMPv3

239.0.0.0/8             Admin-Scoped     Organization-local scope
                                         Like RFC 1918 for multicast
```

### Multicast MAC Address Mapping

IP multicast has a direct mapping to Ethernet MAC addresses. This mapping is **not** done via ARP — it is algorithmically derived:

```
Mapping Rule:
  Take the low 23 bits of the multicast IP address
  OR them into the base MAC: 01:00:5E:00:00:00

IP:   224.  x  .  y  .  z
      [     ] [        ] [           ]
       ignored  maps to  maps to MAC
                 MAC[3]   MAC[4]:MAC[5]

Example:
  IP:  239.255.100.1
  Binary low 23 bits: 111 11110 01100100 00000001
                      [bit23 discarded = 1 → collision possible!]
  MAC: 01:00:5E:7F:64:01

Collision scenario:
  239.255.100.1  →  01:00:5E:7F:64:01
  239.127.100.1  →  01:00:5E:7F:64:01  ← SAME MAC, different group!
```

**This 23-bit mapping means 32 IP multicast groups map to a single MAC address.** Hosts must perform a software-level IP address check after receiving frames addressed to a multicast MAC — the MAC alone is insufficient to discriminate group membership at Layer 2.

---

## 3. IGMP in the Network Stack

### Protocol Stack Position

```
OSI Model           TCP/IP Model        Protocol
──────────────────────────────────────────────────────
Application  ─────  Application ─────  (RTP, SAP, mDNS...)
Transport    ─────  Transport   ─────  UDP / TCP
Network      ─────  Internet    ─────  IPv4
                                       ↑
                                    IGMP sits HERE
                                    Protocol Number: 2
                                    (Same level as ICMP: 1)
Data Link    ─────  Link        ─────  Ethernet / Wi-Fi
Physical     ─────  Physical    ─────  (wire/air)
```

### IP Header When Carrying IGMP

IGMP messages are carried directly in IPv4 packets. The IPv4 Protocol field is set to **2**.

```
IPv4 Header (with IGMP):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─┴─┴─┴─┼─┴─┴─┴─┼─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┤
│  VER  │  IHL  │      ToS      │           Total Length         │
├───────┴───────┴───────────────┴─┬─────────────────────────────┤
│          Identification         │  Flags  │  Fragment Offset   │
├─────────────────────────────────┼─────────┼────────────────────┤
│     TTL = 1 (!)                 │Proto=2  │    Checksum        │
├─────────────────────────────────┴─────────┴────────────────────┤
│                      Source IP Address                         │
├────────────────────────────────────────────────────────────────┤
│               Destination IP Address (multicast)               │
├────────────────────────────────────────────────────────────────┤
│    Router Alert Option (0x94040000) ← MANDATORY in v2/v3       │
├────────────────────────────────────────────────────────────────┤
│                      IGMP Payload                              │
└────────────────────────────────────────────────────────────────┘

CRITICAL: TTL is always set to 1.
IGMP packets must never be forwarded beyond the local link.
Any IGMP packet arriving with TTL > 1 should be treated with suspicion.
```

### The Router Alert Option

IGMPv2 and IGMPv3 MUST include the **IP Router Alert Option** (RFC 2113):

```
Router Alert Option:
 ┌──────┬──────┬──────────────────┬──────────────────────────┐
 │ 0x94 │ 0x04 │ 0x00             │ 0x00                     │
 │Type  │ Len  │ Value (high byte)│ Value (low byte)         │
 │      │  4   │   Router SHALL   │   examine this packet    │
 └──────┴──────┴──────────────────┴──────────────────────────┘

Raw bytes: 94 04 00 00
```

This option signals intermediate routers to inspect the packet even if they are not the destination. Without it, a router might forward an IGMP packet without examining its group membership information.

---

## 4. IGMPv1

### RFC 1112 Overview

IGMPv1 defines two message types:

| Type | Value | Direction | Purpose |
|------|-------|-----------|---------|
| Membership Query | 0x11 | Router → Hosts | "Who wants which groups?" |
| Membership Report | 0x12 | Host → Router | "I want this group" |

There is **no Leave message** in IGMPv1. The router discovers group abandonment only through timeout — a significant inefficiency.

### IGMPv1 Packet Format

```
IGMPv1 Message (8 bytes total):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─────────────────┬─────────────────┬─────────────────────────────┐
│  Version (4b)   │    Type (4b)    │  Unused (8b)  │  Checksum   │
│     = 0x1       │    = 0x1/0x2    │  (must be 0)  │  (16 bits)  │
├─────────────────┴─────────────────┴───────────────┴─────────────┤
│                     Group Address (32 bits)                      │
│  Query: 0.0.0.0 (General Query)                                 │
│  Report: The multicast group being joined                       │
└──────────────────────────────────────────────────────────────────┘

IMPORTANT HISTORICAL NOTE:
The Version and Type fields are 4 bits each in IGMPv1.
In IGMPv2+, the message format was redesigned.
The combined byte 0x11 = Version(1) + Type(1) in v1.
In v2 and v3, byte 0 is purely the Type field (full 8 bits).
This is why 0x11 still means "Membership Query" in v2/v3.
```

### IGMPv1 Protocol Flow

```
GENERAL QUERY FLOW:
                                        
  Router                    Host A              Host B
    │                         │                   │
    │  General Query          │                   │
    │  Dst: 224.0.0.1         │                   │
    │  Group: 0.0.0.0         │                   │
    │────────────────────────►│                   │
    │                         │                   │
    │                         │ [Timer T1]        │ [Timer T2]
    │                         │ (random delay)    │ (random delay)
    │                         │ T1 < T2           │ T1 > T2? no...
    │                         │                   │
    │            Report       │                   │
    │            Dst:225.1.1.1│                   │
    │◄────────────────────────│                   │
    │                         │                   │
    │  [Host B hears report   │                   │
    │   for 225.1.1.1, so     │                   │
    │   it cancels its timer] │                   │
    │                         │                   │
    │  Router learns: ≥1 host │                   │
    │  wants 225.1.1.1        │                   │
    │                         │                   │
```

**Report Suppression:** A critical IGMPv1 mechanism. When a host hears another host's Report for the same group, it cancels its own pending Report timer. This prevents the router from receiving N duplicate reports from N hosts. The router only needs ONE report to know the group has members. This is called **Report Suppression** or the **Membership Report Suppression** mechanism.

### IGMPv1 Limitations

```
PROBLEM 1: No Leave Message
  Host leaves group → Router keeps forwarding for up to 3 minutes
  (default Group Membership Interval: 260 seconds)
  
  This wastes bandwidth on multicast streams after all receivers leave.

PROBLEM 2: No Querier Election
  Multiple routers on segment → multiple Queries → confusion
  
PROBLEM 3: No Group-Specific Query
  Router can only ask "who wants ANY group" not "who wants GROUP X"
  Cannot efficiently confirm if a specific group still has members.

PROBLEM 4: Fixed 10-second max response time
  Not configurable. Under load, all responses arrive in same window.
```

---

## 5. IGMPv2

### RFC 2236 Overview

IGMPv2 adds four critical improvements:

1. **Leave Group message** — hosts proactively signal departure
2. **Group-Specific Query** — targeted query for a single group
3. **Max Response Time field** — configurable response window
4. **Querier Election** — formal mechanism for multi-router segments

### IGMPv2 Message Types

| Type | Value (hex) | Direction | Purpose |
|------|-------------|-----------|---------|
| Membership Query | 0x11 | Router → Host | General or Group-Specific Query |
| Membership Report v1 | 0x12 | Host → Router | IGMPv1 backward compatibility |
| Membership Report v2 | 0x16 | Host → Router | Join a group |
| Leave Group | 0x17 | Host → Router | Leave a group |

### IGMPv2 Packet Format

```
IGMPv2 Message (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─────────────────┬─────────────────────────────────────────────┐
│    Type (8b)    │ Max Resp Time(8b) │       Checksum (16b)     │
│  0x11/0x16/0x17 │  In 1/10 seconds │                          │
├─────────────────┴─────────────────────────────────────────────┤
│                     Group Address (32 bits)                     │
│  General Query:        0.0.0.0                                 │
│  Group-Specific Query: <multicast group being queried>         │
│  Membership Report:    <multicast group being joined>          │
│  Leave Group:          <multicast group being left>            │
└────────────────────────────────────────────────────────────────┘

Max Response Time:
  Default = 100 (= 10.0 seconds)
  Units: tenths of a second
  Range: 0–255 (0.0 to 25.5 seconds)
  Used ONLY in Query messages; zero in Reports/Leaves
```

### IGMPv2 Querier Election

When multiple routers exist on the same segment, they must elect a single Querier to avoid duplicate Queries:

```
QUERIER ELECTION MECHANISM:

Router A: 192.168.1.1
Router B: 192.168.1.2
Router C: 192.168.1.3

On startup, ALL routers assume they are the Querier
and begin sending General Queries.

When Router B (192.168.1.2) receives a Query from
Router A (192.168.1.1):

  B sees: A's IP (192.168.1.1) < B's IP (192.168.1.2)
  B concludes: A should be Querier
  B stops sending Queries
  B starts Other Querier Present Interval timer

When Router C sees queries from A:
  C sees: A's IP < C's IP → C yields

Result: Router A (lowest IP) becomes Querier
        B and C are Non-Queriers

If A fails, B and C detect absence via timer expiry
→ Re-election occurs → B becomes new Querier

                192.168.1.1    192.168.1.2    192.168.1.3
                Router A       Router B       Router C
                (Querier)      (non-Q)        (non-Q)
                    │               │               │
    General Query ──┼───────────────►───────────────►
                    │               │               │
                    │     I see lower IP, I yield   │
                    │               │ B stops Queries
                    │               │               │
                    │               │     I yield   │
                    │               │               C stops Queries
```

### IGMPv2 Leave Protocol

```
LEAVE GROUP FLOW:

  Router                    Host A              Host B
    │                         │                   │
    │                         │ [decides to leave │
    │                         │  group 225.1.1.1] │
    │            Leave Group  │                   │
    │            Dst:224.0.0.2│                   │
    │◄────────────────────────│                   │
    │                         │                   │
    │  Group-Specific Query   │                   │
    │  Dst: 225.1.1.1         │                   │
    │  Group: 225.1.1.1       │                   │
    │  [sends 'Last Member    │                   │
    │   Query Count' times]   │                   │
    │────────────────────────────────────────────►│
    │                         │                   │
    │                         │                   │ [Host B still
    │                         │                   │  in group]
    │            Report       │                   │
    │            Dst:225.1.1.1│                   │
    │◄────────────────────────────────────────────│
    │                         │                   │
    │  Router sees Report → keeps forwarding      │
    │  to 225.1.1.1           │                   │
    │                         │                   │

IF NO REPORT arrives:
    Router stops forwarding to 225.1.1.1
    Leave latency ≈ Last Member Query Interval × Last Member Query Count
                 ≈ 1 sec × 2 = 2 seconds  (default)
```

### IGMPv1/v2 Backward Compatibility

Routers and hosts must handle mixed-version environments:

```
VERSION NEGOTIATION RULES:

On a given subnet, hosts detect the version in use:

1. If any IGMPv1 Query is received → host operates in v1 mode
2. If IGMPv2 Queries are received and no v1 Queries → v2 mode

Router perspective:
- If router receives v1 Reports → treats attached subnet as v1
  Sets v1 host present timer (400 seconds default)
  During timer: cannot use Group-Specific Queries or Leave optimization

This backward compat mechanism prevents v2 Leave optimization
from breaking v1-only hosts that cannot respond to Group-Specific Queries.
```

---

## 6. IGMPv3

### RFC 3376 — Source-Specific Multicast

IGMPv3 is architecturally the most significant revision. Its primary addition is **source filtering**: hosts can specify not just which groups they want, but also which **sources** within those groups they want to receive from (or exclude).

This enables **Source-Specific Multicast (SSM)** — a fundamentally different delivery model:

```
ASM (Any-Source Multicast) — IGMPv1/v2:
  Host says: "I want traffic TO group G, FROM ANY source"
  
  Any sender → group G → reaches receivers
  
SSM (Source-Specific Multicast) — IGMPv3:
  Host says: "I want traffic TO group G, FROM source S only"
  
  Source S₁ → group G → reaches receivers
  Source S₂ → group G → BLOCKED at router (not requested)
  
  Benefits: eliminates denial-of-service flooding, enables
            subscription-based content distribution
```

### IGMPv3 Filter Modes

```
INCLUDE MODE:
  Host wants traffic from group G FROM sources: {S1, S2, S3}
  Traffic from any other source in group G is rejected
  
  Think: whitelist
  
  ┌─────────────────────────────────┐
  │ Group G                        │
  │  Source S1 ──── ALLOW ────► H  │
  │  Source S2 ──── ALLOW ────► H  │
  │  Source S3 ──── ALLOW ────► H  │
  │  Source S4 ──── BLOCK ────✗ H  │
  │  Source S5 ──── BLOCK ────✗ H  │
  └─────────────────────────────────┘

EXCLUDE MODE:
  Host wants traffic from group G FROM ALL sources EXCEPT: {S4, S5}
  Traffic from S4 and S5 is rejected; all others accepted
  
  Think: blacklist
  
  ┌─────────────────────────────────┐
  │ Group G                        │
  │  Source S1 ──── ALLOW ────► H  │
  │  Source S2 ──── ALLOW ────► H  │
  │  Source S3 ──── ALLOW ────► H  │
  │  Source S4 ──── BLOCK ────✗ H  │
  │  Source S5 ──── BLOCK ────✗ H  │
  └─────────────────────────────────┘
  (Same effect here, but semantically different for state transitions)

EMPTY INCLUDE = leave all sources = effectively leaving group
EMPTY EXCLUDE = accept from all sources = equivalent to IGMPv2 join
```

### IGMPv3 Message Types

| Type | Value | Description |
|------|-------|-------------|
| Membership Query | 0x11 | General, Group-Specific, or Group-and-Source-Specific |
| Membership Report v3 | 0x22 | Contains Group Records |

**Note:** IGMPv3 eliminates the separate Leave message. Leaving is expressed as a state change Report.

---

## 7. IGMP Message Formats

### IGMPv3 Membership Query Format

```
IGMPv3 Membership Query (variable length):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌────────────────┬───────────────────────────┬────────────────────┐
│ Type = 0x11    │  Max Resp Code (8b)        │  Checksum (16b)    │
├────────────────┴───────────────────────────┴────────────────────┤
│                     Group Address (32b)                          │
│   0.0.0.0 for General Query                                     │
│   Specific group for Group-Specific or G-and-S-Specific Query   │
├──┬──┬─────────┬───────────────────────────────────────────────  │
│Re│S │  QRV   │    QQIC (8b)       │    Num Sources (16b)       │
│sv│  │ (3b)   │                    │                            │
├──┴──┴─────────┴────────────────────┴────────────────────────────┤
│               Source Address [1]  (32b)                         │
├────────────────────────────────────────────────────────────────┤
│               Source Address [2]  (32b)                         │
├────────────────────────────────────────────────────────────────┤
│               ...                                               │
├────────────────────────────────────────────────────────────────┤
│               Source Address [N]  (32b)                         │
└────────────────────────────────────────────────────────────────┘

Field Breakdown:
  Type:          0x11 (same as v1/v2 — backward compatible)
  Max Resp Code: Specifies max allowed delay for Membership Reports
                 If ≤ 127: value is Max Resp Time in 1/10 sec units
                 If ≥ 128: value is a floating-point-like encoded value
                   mantissa = bits [3:0], exponent = bits [6:4]
                   Max Resp Time = (mant | 0x10) << (exp + 3)
  Group Address: 0.0.0.0 (General Query)
                 Specific group (Group-Specific Query)
                 Specific group (Group-and-Source-Specific Query)
  Resv:          Reserved, must be zero
  S bit:         Suppress Router-Side Processing
                 When set, routers should NOT update timers
                 Used for testing and diagnostics
  QRV:           Querier's Robustness Variable (0-7)
                 If nonzero, overrides local robustness variable
                 Hosts use this for timer calculations
  QQIC:          Querier's Query Interval Code
                 Encodes Query Interval (like Max Resp Code encoding)
                 Hosts use this for timer calculations
  Num Sources:   0 for General Query or Group-Specific Query
                 >0 for Group-and-Source-Specific Query
  Source Addrs:  List of source addresses for G-and-S-Specific Query
```

### IGMPv3 Membership Report Format

```
IGMPv3 Membership Report:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌────────────────┬──────────────────┬─────────────────────────────┐
│ Type = 0x22    │  Reserved (8b)   │       Checksum (16b)        │
├────────────────┴──────────────────┴─────────────────────────────┤
│   Reserved (16b)                  │  Number of Group Records    │
├───────────────────────────────────┴─────────────────────────────┤
│                                                                  │
│                    Group Record [1]                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    Group Record [2]                              │
├──────────────────────────────────────────────────────────────────┤
│                    ...                                           │
└──────────────────────────────────────────────────────────────────┘

Each Group Record:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─────────────────┬──────────────────┬────────────────────────────┐
│ Record Type(8b) │  Aux Data Len(8b)│   Number of Sources (16b)  │
├─────────────────┴──────────────────┴────────────────────────────┤
│                  Multicast Address (32b)                        │
├────────────────────────────────────────────────────────────────┤
│                  Source Address [1] (32b)                       │
├────────────────────────────────────────────────────────────────┤
│                  Source Address [2] (32b)                       │
├────────────────────────────────────────────────────────────────┤
│                  ...                                            │
├────────────────────────────────────────────────────────────────┤
│                  Auxiliary Data (variable, rarely used)         │
└────────────────────────────────────────────────────────────────┘
```

### Group Record Types

```
Record   Value  Mode     Description
Type
─────────────────────────────────────────────────────────────────
MODE_IS_INCLUDE  1  Current State  Current filter is INCLUDE{src list}
MODE_IS_EXCLUDE  2  Current State  Current filter is EXCLUDE{src list}
CHANGE_TO_INCLUDE 3 State Change  Filter changed TO INCLUDE{src list}
                                  (with empty list = leave group)
CHANGE_TO_EXCLUDE 4 State Change  Filter changed TO EXCLUDE{src list}
                                  (with empty list = join all sources)
ALLOW_NEW_SOURCES 5 State Change  Add sources to current INCLUDE list
                                  or remove from current EXCLUDE list
BLOCK_OLD_SOURCES 6 State Change  Remove sources from INCLUDE list
                                  or add to EXCLUDE list

─────────────────────────────────────────────────────────────────
STATE TRANSITION TABLE:

Current State          Action                  New State
─────────────────────────────────────────────────────────────────
INCLUDE{A}             ALLOW{B}                INCLUDE{A+B}
INCLUDE{A}             BLOCK{B}                INCLUDE{A-B}
INCLUDE{A}             TO_EXCLUDE{B}           EXCLUDE{B}
INCLUDE{}              (no sources)            (leave group)
EXCLUDE{A}             ALLOW{B}                EXCLUDE{A-B}
EXCLUDE{A}             BLOCK{B}                EXCLUDE{A+B}
EXCLUDE{A}             TO_INCLUDE{B}           INCLUDE{B}
EXCLUDE{}              (join all)              (join any source)
```

### Complete Byte-Level Example: IGMPv2 General Query

```
ACTUAL WIRE FORMAT — IGMPv2 General Query:

IP Header (20 bytes + 4 byte Router Alert option):
  45 C0 00 1C  → Version=4, IHL=5(+option=6), DSCP=0xC0, Total=28
  00 00 40 00  → ID=0, DF bit set
  01 02 xx xx  → TTL=1, Protocol=2(IGMP), Checksum
  C0 A8 01 01  → Source: 192.168.1.1
  E0 00 00 01  → Dest: 224.0.0.1 (ALL-HOSTS)
  
IP Options (Router Alert):
  94 04 00 00  → Type=0x94, Len=4, Value=0x0000

IGMP Payload (8 bytes):
  Offset  Hex    Meaning
  ──────────────────────────────────────────────
  0       11     Type: Membership Query (0x11)
  1       64     Max Response Time: 100 = 10.0 seconds
  2-3     xx xx  Checksum (computed over IGMP payload)
  4-7     00 00  Group Address: 0.0.0.0 (General Query)
          00 00

Full frame hex (IGMP portion):
  11 64 xx xx 00 00 00 00
  ^^                        Type: Query
     ^^                     Max Resp: 10 sec
        ^^^^                Checksum
              ^^^^^^^^^^^   Group: 0.0.0.0 = General Query
```

### Complete Byte-Level Example: IGMPv2 Membership Report (Join)

```
IGMP Membership Report for group 239.1.1.1:

IGMP Payload (8 bytes):
  Offset  Hex        Meaning
  ──────────────────────────────────────────────
  0       16         Type: Membership Report v2 (0x16)
  1       00         Max Resp Time: 0 (not used in Reports)
  2-3     xx xx      Checksum
  4-7     EF 01      Group Address: 239.1.1.1
          01 01

IPv4 Destination: 239.1.1.1 (same as group being joined)

NOTE: Report is sent to the group address itself, NOT to
      224.0.0.2. This allows other hosts in the same group
      to hear the Report and suppress their own.
```

---

## 8. Protocol State Machines

### Host State Machine (IGMPv2)

```
HOST IGMP STATE MACHINE (per interface, per group):

States:
  NON-MEMBER      — Host has not joined this group
  DELAYING-MEMBER — Host is member, has pending Report timer
  IDLE-MEMBER     — Host is member, no pending timer

                    join group
  NON-MEMBER ──────────────────────────────► DELAYING-MEMBER
                                              ↑ │
                                              │ │ Report timer expires
                                              │ │ → send Report
                                              │ ▼
                                          IDLE-MEMBER
                                              │
                                              │ Query received
                                              │ → start timer
                                              ▼
                                          DELAYING-MEMBER ─────► send Report
                                              │                   if timer
                                              │ hear Report        expires
                                              │ from another host
                                              ▼
                                          IDLE-MEMBER (suppress)
                                              │
                                              │ leave group
                                              ▼
                                          NON-MEMBER
                                          → send Leave (v2 only)

DETAILED TRANSITIONS:

┌──────────────────┬──────────────────────────────────────────────┐
│ Current State    │ Event → Action → New State                    │
├──────────────────┼──────────────────────────────────────────────┤
│ NON-MEMBER       │ join group →                                 │
│                  │   send Report, start timer →                 │
│                  │   DELAYING-MEMBER                            │
├──────────────────┼──────────────────────────────────────────────┤
│ DELAYING-MEMBER  │ timer expires →                              │
│                  │   send Report →                              │
│                  │   IDLE-MEMBER                                │
├──────────────────┼──────────────────────────────────────────────┤
│ DELAYING-MEMBER  │ receive Report for same group →              │
│                  │   cancel timer (suppress) →                  │
│                  │   IDLE-MEMBER                                │
├──────────────────┼──────────────────────────────────────────────┤
│ DELAYING-MEMBER  │ receive Query →                              │
│                  │   reset timer to min(current, new) →         │
│                  │   DELAYING-MEMBER                            │
├──────────────────┼──────────────────────────────────────────────┤
│ IDLE-MEMBER      │ receive Query →                              │
│                  │   start timer (random 0..MaxRespTime) →      │
│                  │   DELAYING-MEMBER                            │
├──────────────────┼──────────────────────────────────────────────┤
│ IDLE-MEMBER      │ leave group →                                │
│                  │   send Leave (v2) →                          │
│                  │   NON-MEMBER                                 │
└──────────────────┴──────────────────────────────────────────────┘
```

### Router State Machine (IGMPv2)

```
ROUTER IGMP STATE MACHINE (per interface, per group):

States:
  NO-MEMBERS-PRESENT  — No hosts on this interface want this group
  MEMBERS-PRESENT     — At least one host is a member
  CHECKING-MEMBERSHIP — Leave received, verifying with Group-Specific Query

              Report received
  NO-MEMBERS ──────────────────────────────► MEMBERS-PRESENT
                                              │  ↑
                                              │  │ Report received
                                              │  │ (reset timer)
                       timer expires          │  │
              ◄────────────────────────────── │  │
                                              │  │
                                              │ Leave received
                                              ▼  │
                                          CHECKING-MEMBERSHIP
                                              │  │
                       Report received        │  │ Timer expires
                  ─────────────────────────► │  │ (no response)
                  MEMBERS-PRESENT             │  ▼
                                          NO-MEMBERS-PRESENT
```

---

## 9. IGMP Timers and Robustness Variables

Understanding timers is essential for analyzing network behavior and detecting anomalies.

```
IGMP TIMER REFERENCE TABLE:

Variable                    Default    Notes
───────────────────────────────────────────────────────────────
Robustness Variable (RV)    2          Number of times to retry
                                       Set higher on lossy networks
                                       RV ≥ 2, recommended

Query Interval (QI)         125 sec    How often General Queries sent

Query Response Interval     10 sec     Max response time for Query
(QRI)                       (100 in    (= Max Response Time field)
                             1/10s)

Group Membership Interval   260 sec    = (RV × QI) + QRI
(GMI)                                  How long router keeps group
                                       with no Reports

Other Querier Present       255 sec    = (RV × QI) + (QRI / 2)
Interval (OQPI)                        Non-querier waits this long
                                       before assuming Querier dead

Startup Query Interval      31.25 sec  QI / 4
                                       Used during startup

Startup Query Count         2          = RV
                                       Queries sent at startup

Last Member Query           1 sec      Time between Group-Specific
Interval (LMQI)                        Queries after Leave received

Last Member Query Count     2          = RV
(LMQC)                                 Number of Group-Specific
                                       Queries sent

Last Member Query Time      2 sec      = LMQI × LMQC
(LMQT)                                 How long to wait before
                                       removing group

Unsolicited Report          10 sec     Delay before sending first
Interval (URI)                         unsolicited Report after join

───────────────────────────────────────────────────────────────

TIMER CALCULATION EXAMPLES:

Group Membership Interval:
  GMI = (RV × QI) + QRI
      = (2 × 125) + 10
      = 260 seconds
      
  Meaning: If no Report received for 260 sec after last Query,
           router removes group from its membership table.

Maximum Leave Latency (default):
  LMQT = LMQI × LMQC = 1 × 2 = 2 seconds
  
  Meaning: After receiving a Leave, router waits max 2 seconds
           before stopping forwarding.
           (Compare: IGMPv1 waits up to 260 seconds!)
```

---

## 10. IGMP Snooping

### What IGMP Snooping Is

IGMP Snooping is a Layer 2 switch optimization. Without it, a switch treats multicast like broadcast — flooding all multicast frames to all ports. With snooping, the switch "listens" to IGMP exchanges and builds a table mapping multicast groups to specific ports.

```
WITHOUT IGMP SNOOPING:
                         ┌───────────────────┐
   Router ───────────────┤                   ├──── Host A (wants group)
                         │   L2 Switch       ├──── Host B (doesn't want it)
   Multicast stream ────►│                   ├──── Host C (doesn't want it)
   for group G           │ FLOODS to ALL     ├──── Host D (doesn't want it)
                         └───────────────────┘
   Bandwidth wasted on B, C, D

WITH IGMP SNOOPING:
                         ┌───────────────────┐
   Router ───────────────┤                   ├──── Host A ✓ (in table)
                         │   L2 Switch       ├──── Host B ✗ (blocked)
   Multicast stream ────►│ Only forwards to  ├──── Host C ✗ (blocked)
   for group G           │ ports in table    ├──── Host D ✗ (blocked)
                         └───────────────────┘
   Efficient delivery

IGMP SNOOPING TABLE (Switch Multicast Table):
┌──────────────────┬──────────────────────────────────────────────┐
│ VLAN │ Group      │ Ports                         │ Expiry      │
├──────┼────────────┼───────────────────────────────┼─────────────┤
│  1   │ 239.1.1.1  │ Gi0/1 (router), Gi0/3 (hostA) │ 260 sec    │
│  1   │ 239.2.2.2  │ Gi0/1 (router), Gi0/5 (hostB) │ 260 sec    │
│  10  │ 225.0.1.1  │ Gi0/1 (router), Gi0/7, Gi0/9 │ 255 sec    │
└──────┴────────────┴───────────────────────────────┴─────────────┘
```

### IGMP Snooping Querier

When there is no multicast router on a segment (pure L2 environment), IGMP Snooping will not function correctly — there are no Queries to trigger host Reports, so the snooping table is never populated. Many switches implement an **IGMP Snooping Querier** feature: the switch itself generates General Queries to elicit host Reports.

```
IGMP SNOOPING QUERIER:
  - Switch acts as a pseudo-router for IGMP purposes only
  - Does NOT perform multicast routing
  - Sends General Queries from a configured source IP (often 0.0.0.0)
  - Listens for Reports and populates its snooping table
  - Typically configured when no PIM/DVMRP router is present
```

### IGMP Proxy

Distinct from Snooping. An IGMP Proxy aggregates group membership from a downstream network and presents it as a single host to an upstream router:

```
IGMP PROXY TOPOLOGY:
                                          
Upstream Router ──── Upstream Interface ──── [IGMP PROXY] ──── Downstream Segment
                     (faces toward RP/root)                     Host A (joined G)
                                                                Host B (joined G)
                                                                Host C (joined G)

IGMP Proxy behavior:
  1. Receives Reports from H-A, H-B, H-C for group G
  2. Sends ONE Report to upstream router on behalf of all three
  3. Receives multicast traffic from upstream
  4. Forwards to downstream segment (acting as router for downstream)
  5. When ALL downstream hosts leave → sends Leave upstream
```

---

## 11. Multicast Routing Interaction

IGMP is only the host-router signaling layer. Distributing multicast traffic across routers requires multicast routing protocols. Understanding the interaction is essential for full-stack multicast comprehension.

```
PROTOCOL STACK OVERVIEW:

┌─────────────────────────────────────────────────────────────┐
│                   Applications / Services                    │
│            (IPTV, video conferencing, SDR, mDNS)            │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer (UDP)                     │
├─────────────────────────────────────────────────────────────┤
│                       IP Layer                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MULTICAST ROUTING PROTOCOLS (router-to-router)       │   │
│  │   PIM-SM  (Protocol Independent Multicast Sparse Mode│   │
│  │   PIM-DM  (PIM Dense Mode)                           │   │
│  │   PIM-SSM (PIM for SSM with IGMPv3)                  │   │
│  │   DVMRP   (Distance Vector Multicast Routing)        │   │
│  │   MOSPF   (Multicast OSPF)                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ IGMP (host-router, local link only)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

PIM-SM RENDEZVOUS POINT MODEL:
                                        
Sender S ──► [DR-S] ──► [RP] ◄── [DR-R] ◄── Receiver R
                                 (Joins sent toward RP)
                                 
After SPT switchover:
Sender S ──► [DR-S] ──────────────────────► Receiver R
                                 (Shortest Path Tree)

IGMP role:
  Receiver R sends IGMPv2 Report for group G
  DR-R sees Report → sends PIM Join toward RP
  RP pulls traffic down the distribution tree
```

---

## 12. MLDv1/MLDv2

### Multicast Listener Discovery — IPv6 Equivalent

MLD is the IPv6 equivalent of IGMP. It is technically a subtype of ICMPv6 (not a separate protocol), using ICMPv6 message types.

```
IGMP vs MLD COMPARISON:

Attribute           IGMP (IPv4)         MLD (IPv6)
───────────────────────────────────────────────────────
Encapsulation       IPv4 (proto=2)      ICMPv6 (proto=58)
Version 1 RFC       RFC 1112 (1989)     RFC 2710 (1999)
Version 2 RFC       RFC 2236 (1997)     RFC 3810 (2004)
v1 Message Types    Query(0x11)         Query(130)
                    Report(0x12)        Report(131)
v2 Message Types    Query(0x11)         Query(130)
                    Report(0x16)        Report(131)
                    Leave(0x17)         Done(132)
v3/v2 Report type  Report(0x22)        Report v2 (143)
Group Address       32-bit IPv4         128-bit IPv6
                    224.0.0.0/4         FF00::/8
Link-Scope Report   224.0.0.1           FF02::1
Router Address      224.0.0.2           FF02::2
TTL/Hop Limit       1                   1
Router Alert        IP option (0x94)    HbH option (type 5)
Source Address      Host IP             Link-local (fe80::)

MLDv2 REPORT — ICMPv6 Type 143:
  Sent to FF02::16 (all MLDv2-capable routers)
  Structure nearly identical to IGMPv3 Report
  but with 128-bit group and source addresses

MLDv1 QUERY/REPORT/DONE:
  Query: ICMPv6 type 130, to FF02::1
  Report: ICMPv6 type 131, to the joined group
  Done: ICMPv6 type 132, to FF02::2
```

### IPv6 Multicast Address Structure

```
IPv6 Multicast Address Format:
 ┌──────────────┬──────┬──────────────────────────────────────┐
 │  8 bits      │ 4 b  │ 4 b   │       112 bits               │
 │  1111 1111   │ Flags│ Scope │       Group ID               │
 │  0xFF        │      │       │                              │
 └──────────────┴──────┴──────────────────────────────────────┘

Flags:
  Bit 0 (T): 0=well-known, 1=transient (dynamically assigned)
  Bit 1 (P): 0=not prefix-based, 1=prefix-based (RFC 3306)
  Bit 2 (R): Rendezvous Point embedded (RFC 3956)

Scope:
  1 = Interface-local (loopback)
  2 = Link-local
  4 = Admin-local
  5 = Site-local
  8 = Organization-local
  E = Global

Examples:
  FF02::1   = All nodes, link-local
  FF02::2   = All routers, link-local
  FF02::16  = All MLDv2-capable routers
  FF02::1:FFXX:XXXX = Solicited-Node multicast (NDP)
```

---

## 13. Security Implications and Attack Vectors

### IGMP Attack Surface

IGMP has minimal authentication. Any host on a segment can send any IGMP message, and routers will process it. This creates several attack vectors:

```
IGMP ATTACK TAXONOMY:

┌─────────────────────────────────────────────────────────────┐
│                    IGMP ATTACKS                              │
├─────────────────────────────────────────────────────────────┤
│ 1. IGMP Flooding / Amplification                            │
│    Attacker sends massive number of Join Reports            │
│    Router builds enormous multicast table → memory DoS      │
│    Routers may crash or drop legitimate traffic             │
├─────────────────────────────────────────────────────────────┤
│ 2. Spurious Leave Attack                                    │
│    Attacker sends forged Leave for a group                  │
│    Router sends Group-Specific Query                        │
│    If timing is right, disrupts legitimate members          │
│    (mitigated by Last Member Query mechanism, but           │
│     still causes temporary service disruption)             │
├─────────────────────────────────────────────────────────────┤
│ 3. IGMP Report Suppression Attack                           │
│    Attacker sends Reports for all groups it sees            │
│    Legitimate hosts see the Report → suppress their own     │
│    If attacker then leaves → router loses track of group    │
│    (v1/v2 Report Suppression exploited)                     │
├─────────────────────────────────────────────────────────────┤
│ 4. Phantom Join Attack                                      │
│    Attacker joins many groups on behalf of victim IPs       │
│    Victim receives multicast traffic it never requested     │
│    Network congestion directed at specific hosts            │
├─────────────────────────────────────────────────────────────┤
│ 5. IGMP-Based Network Reconnaissance                        │
│    Passive monitoring of IGMP traffic reveals:              │
│    - Which hosts are on which subnets                       │
│    - What multicast services are in use                     │
│    - Network topology clues (querier = router IP)           │
│    - When hosts are active (periodic reports)               │
├─────────────────────────────────────────────────────────────┤
│ 6. Querier Spoofing                                         │
│    Attacker sends Query with a source IP lower than         │
│    legitimate routers → wins querier election               │
│    Attacker controls Query cadence → can silence all        │
│    members by never querying → groups time out              │
├─────────────────────────────────────────────────────────────┤
│ 7. Multicast DoS via Source Spoofing                        │
│    Craft UDP packets from spoofed source to multicast dst   │
│    All members of the group receive the traffic             │
│    Amplification factor = group membership size             │
└─────────────────────────────────────────────────────────────┘
```

### IGMP and Network Reconnaissance

From an attacker's perspective, IGMP traffic leaks significant information:

```
INTELLIGENCE EXTRACTABLE FROM IGMP TRAFFIC:

1. Host Discovery
   IGMP Reports have unicast source IPs (before NAT)
   All active multicast subscribers visible in Reports
   
2. Router/Gateway Discovery  
   Queries always originate from the router
   Querier source IP = router's interface IP
   
3. Service Enumeration
   Which multicast groups are subscribed to?
   239.x.x.x = administrative scope → internal services
   232.x.x.x = SSM → indicates IGMPv3 usage
   
4. Traffic Pattern Analysis
   Report timing reveals host activity patterns
   Re-join after boot = system restart timing
   
5. Segment Topology
   IGMP is link-local → captures reveal L2 segments
   Multiple queriers seen → multiple router interfaces
```

### IGMP in Malware Context

While IGMP is not commonly weaponized by malware directly, understanding it matters for:

```
MALWARE-RELEVANT IGMP SCENARIOS:

1. C2 Channel Covert Communication
   Multicast channels can carry covert data:
   - Multicast group address itself encodes information
   - Payload in IGMP Auxiliary Data field (IGMPv3)
   - Rarely monitored by security tools
   
2. Lateral Movement via Multicast
   Malware subscribing to internal multicast groups
   to receive commands from an internal C2 relay
   E.g., join 239.1.1.1 → receive commands as multicast UDP

3. Detection Evasion
   Traffic blends with legitimate multicast (SSDP, mDNS,
   Bonjour, etc.) if IGMP joins appear normal
   
4. Network Mapping
   Malware passively captures IGMP to enumerate
   all live hosts on segment without ARP/ICMP noise
   
5. Industrial Control Systems (ICS/SCADA)
   OT networks heavily use multicast for process data
   (Profinet, EtherNet/IP, IEC 61850)
   IGMP manipulation = disruption of physical processes
   TRITON/TRISIS context: Schneider PLCs use multicast
```

---

## 14. IGMP in Malware and APT Context

### Relevant APT Techniques

**MITRE ATT&CK Mappings:**

| Technique | ID | Relevance |
|-----------|----|-----------| 
| Network Sniffing | T1040 | Passive IGMP monitoring for host discovery |
| Network Service Discovery | T1046 | IGMP reveals active multicast services |
| Non-Standard Port | T1571 | Multicast UDP over non-standard ports |
| Multi-hop Proxy | T1090.003 | Multicast relay for C2 traffic |
| Exfiltration Over Unmonitored Protocol | T1048.003 | IGMP rarely DPI'd |

### Volt Typhoon — LOTL and Multicast

Volt Typhoon (China, CISA Advisory AA23-144A) targets operational technology networks where multicast protocols are prevalent. Their LOTL methodology includes:

```
VOLT TYPHOON MULTICAST RELEVANCE:
  
  - OT networks use IGMP extensively for real-time data
  - Volt Typhoon's "blend in" strategy = using multicast
    as a lateral movement vector
  - Passive listening to multicast groups reveals
    PLC states, sensor values, SCADA commands
  - Subscribing to internal groups via IGMP enables
    intelligence gathering without active scanning
  - Detected pattern: unexpected IGMP joins from
    workstations that should not subscribe to
    process control multicast groups
```

### Detection Signatures for Anomalous IGMP

```
SUSPICIOUS IGMP PATTERNS:

1. IGMP from non-router source with Type 0x11 (Query)
   → Querier spoofing attempt
   
2. IGMP Leave for a group with no prior Join from same host
   → Spurious Leave attack
   
3. Burst of IGMP Joins from single host for many groups (>50)
   → Flood attack or scanning behavior
   
4. IGMP packets with TTL > 1
   → Spoofed/crafted packet (TTL must always be 1)
   
5. IGMP Query without Router Alert option
   → Non-compliant, possibly crafted
   
6. Host joining 232.0.0.0/8 groups (SSM range)
   where no IGMPv3-aware infrastructure exists
   → Unexpected protocol usage
   
7. IGMP Join for group 224.0.0.x (link-local reserved range)
   by a non-router host
   → Protocol violation / probing
```

---

## 15. Packet Capture and Analysis

### Wireshark Display Filters

```
# All IGMP traffic
igmp

# Only IGMP v2 queries
igmp.type == 0x11 && igmp.version == 2

# Only IGMP v3 reports
igmp.type == 0x22

# IGMP Leave messages
igmp.type == 0x17

# IGMP from specific host
igmp && ip.src == 192.168.1.100

# IGMP with suspicious TTL
igmp && ip.ttl > 1

# IGMP without Router Alert option
igmp && !ip.opt.ra

# IGMP to all-routers (Leave messages)
igmp && ip.dst == 224.0.0.2

# IGMPv3 with source filters (SSM)
igmp.type == 0x22 && igmp.num_grp_recs > 0
```

### tcpdump Capture Filters

```bash
# Capture all IGMP
tcpdump -i eth0 -nn 'igmp'

# Capture IGMP with full packet dump
tcpdump -i eth0 -nn -X 'igmp'

# Capture specific IGMP type (hex 0x11 = Query)
tcpdump -i eth0 -nn 'igmp[0] == 0x11'

# Capture IGMP Leave (0x17)
tcpdump -i eth0 -nn 'igmp[0] == 0x17'

# Capture IGMPv3 Reports (0x22)
tcpdump -i eth0 -nn 'igmp[0] == 0x22'

# Show IGMP with timestamps
tcpdump -i eth0 -nn -tttt 'igmp'

# Save to PCAP for Wireshark
tcpdump -i eth0 -nn -w igmp_capture.pcap 'igmp'
```

### Tshark (CLI Wireshark) Analysis

```bash
# Extract all IGMP group addresses
tshark -r capture.pcap -Y 'igmp' -T fields \
  -e ip.src -e igmp.type -e igmp.maddr

# Statistics: IGMP type distribution
tshark -r capture.pcap -Y 'igmp' -q -z 'io,stat,0,igmp'

# Timeline of joins/leaves
tshark -r capture.pcap -Y 'igmp.type == 0x16 || igmp.type == 0x17' \
  -T fields -e frame.time -e ip.src -e igmp.type -e igmp.maddr
```

---

## 16. C Implementation

### Complete IGMP Stack in C

```c
/*
 * igmp_impl.c
 * Complete IGMP v1/v2/v3 implementation using raw sockets
 * Demonstrates: packet construction, membership management,
 * timer handling, and state machine
 *
 * Compile: gcc -O2 -Wall -o igmp_impl igmp_impl.c
 * Run:     sudo ./igmp_impl eth0 239.1.1.1
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include <unistd.h>
#include <time.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <linux/if_packet.h>
#include <linux/igmp.h>

/* ═══════════════════════════════════════════════════════════════
 * CONSTANTS AND PROTOCOL DEFINITIONS
 * ═══════════════════════════════════════════════════════════════ */

/* IGMP Protocol Number in IPv4 */
#define IPPROTO_IGMP_PROTO          2

/* IGMP Message Types */
#define IGMP_TYPE_QUERY             0x11    /* Membership Query (all versions) */
#define IGMP_TYPE_V1_REPORT         0x12    /* IGMPv1 Membership Report */
#define IGMP_TYPE_V2_REPORT         0x16    /* IGMPv2 Membership Report */
#define IGMP_TYPE_V2_LEAVE          0x17    /* IGMPv2 Leave Group */
#define IGMP_TYPE_V3_REPORT         0x22    /* IGMPv3 Membership Report */

/* IGMPv3 Group Record Types */
#define IGMPV3_MODE_IS_INCLUDE      1
#define IGMPV3_MODE_IS_EXCLUDE      2
#define IGMPV3_CHANGE_TO_INCLUDE    3
#define IGMPV3_CHANGE_TO_EXCLUDE    4
#define IGMPV3_ALLOW_NEW_SOURCES    5
#define IGMPV3_BLOCK_OLD_SOURCES    6

/* Well-known multicast addresses */
#define IGMP_ALL_HOSTS              "224.0.0.1"
#define IGMP_ALL_ROUTERS            "224.0.0.2"
#define IGMP_ALL_V3_ROUTERS         "224.0.0.22"

/* Timer defaults (seconds) */
#define IGMP_ROBUSTNESS_VAR         2
#define IGMP_QUERY_INTERVAL         125
#define IGMP_QUERY_RESPONSE_INTERVAL 10
#define IGMP_LAST_MEMBER_QUERY_INT  1
#define IGMP_LAST_MEMBER_QUERY_CNT  2
#define IGMP_UNSOLICITED_REPORT_INT 10

/* Buffer sizes */
#define MAX_PACKET_SIZE             1500
#define MAX_GROUPS                  64
#define MAX_SOURCES_PER_GROUP       32

/* IP Router Alert option value */
#define IP_ROUTER_ALERT_VALUE       0x00000094UL

/* ═══════════════════════════════════════════════════════════════
 * PACKET STRUCTURES (packed — exact wire format)
 * ═══════════════════════════════════════════════════════════════ */

/*
 * IGMPv1/v2 header — 8 bytes
 * Used for: General Query, Group-Specific Query, v1 Report,
 *           v2 Report, Leave Group
 */
struct igmpv2_hdr {
    uint8_t  type;          /* Message type */
    uint8_t  max_resp_time; /* Max response time (1/10 sec units) */
    uint16_t checksum;      /* Internet checksum over IGMP message */
    uint32_t group_addr;    /* Group address (network byte order) */
} __attribute__((packed));

/*
 * IGMPv3 Query — variable length
 */
struct igmpv3_query {
    uint8_t  type;          /* 0x11 */
    uint8_t  max_resp_code; /* Encoded max response time */
    uint16_t checksum;
    uint32_t group_addr;    /* 0 for General Query */
    uint8_t  resv_s_qrv;   /* Reserved(4b) | S-flag(1b) | QRV(3b) */
    uint8_t  qqic;          /* Querier's Query Interval Code */
    uint16_t num_sources;   /* Number of source addresses following */
    uint32_t sources[0];    /* Flexible array of source IPs */
} __attribute__((packed));

/*
 * IGMPv3 Group Record — variable length
 */
struct igmpv3_grec {
    uint8_t  record_type;   /* One of IGMPV3_* constants above */
    uint8_t  aux_data_len;  /* Auxiliary data length in 32-bit words */
    uint16_t num_sources;   /* Number of source addresses */
    uint32_t mcast_addr;    /* Multicast group address */
    uint32_t sources[0];    /* Source addresses */
    /* After sources: aux_data_len * 4 bytes of auxiliary data */
} __attribute__((packed));

/*
 * IGMPv3 Report — variable length
 */
struct igmpv3_report {
    uint8_t  type;          /* 0x22 */
    uint8_t  reserved1;     /* Must be zero */
    uint16_t checksum;
    uint16_t reserved2;     /* Must be zero */
    uint16_t num_grec;      /* Number of Group Records */
    struct igmpv3_grec grecs[0]; /* Variable-length group records */
} __attribute__((packed));

/* ═══════════════════════════════════════════════════════════════
 * GROUP MEMBERSHIP STATE
 * ═══════════════════════════════════════════════════════════════ */

typedef enum {
    IGMP_STATE_NON_MEMBER = 0,
    IGMP_STATE_DELAYING_MEMBER,
    IGMP_STATE_IDLE_MEMBER,
} igmp_host_state_t;

typedef enum {
    IGMP_FILTER_INCLUDE = 0,
    IGMP_FILTER_EXCLUDE,
} igmp_filter_mode_t;

typedef struct {
    uint32_t         group_addr;                      /* Network byte order */
    igmp_host_state_t state;
    igmp_filter_mode_t filter_mode;
    uint32_t         sources[MAX_SOURCES_PER_GROUP];  /* Source filter list */
    int              num_sources;
    struct timespec  report_timer;                    /* When to send Report */
    bool             timer_active;
} igmp_group_t;

typedef struct {
    int          raw_fd;                              /* Raw socket fd */
    int          ifindex;                             /* Interface index */
    uint32_t     local_ip;                            /* Our IP (network order) */
    char         ifname[IFNAMSIZ];
    igmp_group_t groups[MAX_GROUPS];
    int          num_groups;
    int          igmp_version;                        /* 1, 2, or 3 */
} igmp_ctx_t;

/* ═══════════════════════════════════════════════════════════════
 * INTERNET CHECKSUM (RFC 1071)
 * ═══════════════════════════════════════════════════════════════ */

static uint16_t inet_checksum(const void *data, size_t len) {
    const uint16_t *ptr = (const uint16_t *)data;
    uint32_t sum = 0;

    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    /* Odd byte: pad with zero */
    if (len == 1) {
        sum += *(const uint8_t *)ptr;
    }

    /* Fold 32-bit sum to 16 bits */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return (uint16_t)(~sum);
}

/* ═══════════════════════════════════════════════════════════════
 * IP HEADER CONSTRUCTION WITH ROUTER ALERT OPTION
 * ═══════════════════════════════════════════════════════════════ */

/*
 * Build IPv4 header with Router Alert option.
 * Returns total IP header size (standard header + option = 24 bytes).
 *
 * Memory layout in buf:
 *   [0-19]  : Standard IPv4 header (IHL=6, includes option)
 *   [20-23] : Router Alert option (94 04 00 00)
 */
static int build_ip_header(uint8_t *buf, size_t buf_size,
                            uint32_t src_ip, uint32_t dst_ip,
                            uint16_t payload_len) {
    struct iphdr *iph = (struct iphdr *)buf;
    uint8_t *opt = buf + sizeof(struct iphdr);
    uint16_t total_len = sizeof(struct iphdr) + 4 + payload_len;

    if (buf_size < total_len) return -1;

    memset(buf, 0, sizeof(struct iphdr) + 4);

    iph->version  = 4;
    iph->ihl      = 6;          /* 6 × 4 = 24 bytes (20 standard + 4 option) */
    iph->tos      = 0xC0;       /* DSCP CS6 — network control traffic */
    iph->tot_len  = htons(total_len);
    iph->id       = 0;
    iph->frag_off = htons(0x4000); /* Don't Fragment */
    iph->ttl      = 1;          /* MUST be 1 for IGMP */
    iph->protocol = IPPROTO_IGMP_PROTO;
    iph->check    = 0;          /* Computed later */
    iph->saddr    = src_ip;
    iph->daddr    = dst_ip;

    /* Router Alert option: type=0x94, len=4, value=0x0000 */
    opt[0] = 0x94;  /* Option type: copy=1, class=0, number=20 */
    opt[1] = 0x04;  /* Option length = 4 bytes */
    opt[2] = 0x00;  /* Router shall examine this datagram */
    opt[3] = 0x00;

    /* Compute IP header checksum */
    iph->check = inet_checksum(iph, sizeof(struct iphdr) + 4);

    return sizeof(struct iphdr) + 4;
}

/* ═══════════════════════════════════════════════════════════════
 * SEND RAW IGMP PACKET
 * ═══════════════════════════════════════════════════════════════ */

static int igmp_send_raw(igmp_ctx_t *ctx, uint32_t dst_ip,
                         uint8_t *igmp_payload, size_t igmp_len) {
    uint8_t  pkt[MAX_PACKET_SIZE];
    int      ip_hdr_len;
    struct sockaddr_in dst_addr;

    memset(pkt, 0, sizeof(pkt));

    /* Build IP header */
    ip_hdr_len = build_ip_header(pkt, sizeof(pkt),
                                 ctx->local_ip, dst_ip,
                                 (uint16_t)igmp_len);
    if (ip_hdr_len < 0) {
        fprintf(stderr, "[-] Packet too large\n");
        return -1;
    }

    /* Copy IGMP payload */
    if ((size_t)(ip_hdr_len) + igmp_len > sizeof(pkt)) {
        fprintf(stderr, "[-] Buffer overflow prevented\n");
        return -1;
    }
    memcpy(pkt + ip_hdr_len, igmp_payload, igmp_len);

    /* Send via raw socket */
    memset(&dst_addr, 0, sizeof(dst_addr));
    dst_addr.sin_family = AF_INET;
    dst_addr.sin_addr.s_addr = dst_ip;

    ssize_t sent = sendto(ctx->raw_fd,
                          pkt, ip_hdr_len + igmp_len,
                          0,
                          (struct sockaddr *)&dst_addr,
                          sizeof(dst_addr));
    if (sent < 0) {
        perror("[-] sendto");
        return -1;
    }

    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP v2 MEMBERSHIP REPORT (JOIN)
 * ═══════════════════════════════════════════════════════════════ */

int igmp_send_v2_report(igmp_ctx_t *ctx, uint32_t group_addr) {
    struct igmpv2_hdr hdr;
    uint8_t  buf[8];

    printf("[+] Sending IGMPv2 Report for group %s\n",
           inet_ntoa(*(struct in_addr *)&group_addr));

    memset(&hdr, 0, sizeof(hdr));
    hdr.type           = IGMP_TYPE_V2_REPORT;
    hdr.max_resp_time  = 0;         /* Not used in Reports */
    hdr.checksum       = 0;
    hdr.group_addr     = group_addr;

    /* Compute checksum over IGMP message only */
    hdr.checksum = inet_checksum(&hdr, sizeof(hdr));

    memcpy(buf, &hdr, sizeof(hdr));

    /*
     * Reports are sent TO the group address, not to ALL-ROUTERS.
     * This allows other hosts in the group to see the report
     * and apply Report Suppression.
     */
    return igmp_send_raw(ctx, group_addr, buf, sizeof(buf));
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP v2 LEAVE GROUP
 * ═══════════════════════════════════════════════════════════════ */

int igmp_send_v2_leave(igmp_ctx_t *ctx, uint32_t group_addr) {
    struct igmpv2_hdr hdr;
    uint8_t  buf[8];

    printf("[+] Sending IGMPv2 Leave for group %s\n",
           inet_ntoa(*(struct in_addr *)&group_addr));

    memset(&hdr, 0, sizeof(hdr));
    hdr.type           = IGMP_TYPE_V2_LEAVE;
    hdr.max_resp_time  = 0;
    hdr.checksum       = 0;
    hdr.group_addr     = group_addr;
    hdr.checksum       = inet_checksum(&hdr, sizeof(hdr));

    memcpy(buf, &hdr, sizeof(hdr));

    /*
     * Leave is sent to ALL-ROUTERS (224.0.0.2), not to the group.
     * Only the router needs to know; other hosts don't need to see it.
     */
    return igmp_send_raw(ctx, inet_addr(IGMP_ALL_ROUTERS), buf, sizeof(buf));
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP v2 GENERAL QUERY (for router implementation)
 * ═══════════════════════════════════════════════════════════════ */

int igmp_send_v2_general_query(igmp_ctx_t *ctx, uint8_t max_resp_time) {
    struct igmpv2_hdr hdr;
    uint8_t  buf[8];

    printf("[+] Sending IGMPv2 General Query (max_resp=%u × 0.1s)\n",
           max_resp_time);

    memset(&hdr, 0, sizeof(hdr));
    hdr.type           = IGMP_TYPE_QUERY;
    hdr.max_resp_time  = max_resp_time;   /* e.g., 100 = 10 seconds */
    hdr.checksum       = 0;
    hdr.group_addr     = 0;              /* 0.0.0.0 = General Query */
    hdr.checksum       = inet_checksum(&hdr, sizeof(hdr));

    memcpy(buf, &hdr, sizeof(hdr));

    /* General Query sent to ALL-HOSTS (224.0.0.1) */
    return igmp_send_raw(ctx, inet_addr(IGMP_ALL_HOSTS), buf, sizeof(buf));
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP v2 GROUP-SPECIFIC QUERY (for router implementation)
 * ═══════════════════════════════════════════════════════════════ */

int igmp_send_v2_group_query(igmp_ctx_t *ctx, uint32_t group_addr,
                              uint8_t max_resp_time) {
    struct igmpv2_hdr hdr;
    uint8_t  buf[8];

    printf("[+] Sending IGMPv2 Group-Specific Query for %s\n",
           inet_ntoa(*(struct in_addr *)&group_addr));

    memset(&hdr, 0, sizeof(hdr));
    hdr.type           = IGMP_TYPE_QUERY;
    hdr.max_resp_time  = max_resp_time;
    hdr.checksum       = 0;
    hdr.group_addr     = group_addr;
    hdr.checksum       = inet_checksum(&hdr, sizeof(hdr));

    memcpy(buf, &hdr, sizeof(hdr));

    /* Group-Specific Query sent to the group address */
    return igmp_send_raw(ctx, group_addr, buf, sizeof(buf));
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP v3 REPORT — SOURCE-SPECIFIC MEMBERSHIP
 * ═══════════════════════════════════════════════════════════════ */

int igmp_send_v3_report(igmp_ctx_t *ctx,
                         uint32_t group_addr,
                         uint8_t  record_type,
                         uint32_t *sources,
                         uint16_t num_sources) {
    /*
     * IGMPv3 Report layout:
     *   [igmpv3_report header]    8 bytes
     *   [igmpv3_grec header]      4 bytes + 4 (group addr)
     *   [source addresses]        num_sources × 4 bytes
     */
    size_t grec_size = sizeof(struct igmpv3_grec) +
                       (num_sources * sizeof(uint32_t));
    size_t report_size = sizeof(struct igmpv3_report) + grec_size;

    if (report_size > MAX_PACKET_SIZE - 24) {
        fprintf(stderr, "[-] IGMPv3 report too large\n");
        return -1;
    }

    uint8_t buf[MAX_PACKET_SIZE];
    memset(buf, 0, report_size);

    struct igmpv3_report *report = (struct igmpv3_report *)buf;
    report->type      = IGMP_TYPE_V3_REPORT;
    report->reserved1 = 0;
    report->checksum  = 0;
    report->reserved2 = 0;
    report->num_grec  = htons(1);   /* One group record */

    struct igmpv3_grec *grec = (struct igmpv3_grec *)(buf +
                                sizeof(struct igmpv3_report));
    grec->record_type  = record_type;
    grec->aux_data_len = 0;
    grec->num_sources  = htons(num_sources);
    grec->mcast_addr   = group_addr;

    /* Copy source addresses */
    for (uint16_t i = 0; i < num_sources; i++) {
        grec->sources[i] = sources[i];
    }

    /* Compute checksum over entire IGMP message */
    report->checksum = inet_checksum(buf, report_size);

    printf("[+] Sending IGMPv3 Report: group=%s type=%u sources=%u\n",
           inet_ntoa(*(struct in_addr *)&group_addr),
           record_type, num_sources);

    /*
     * IGMPv3 Reports are sent to 224.0.0.22 (all IGMPv3-capable routers)
     * NOT to the group address (no Report Suppression in v3)
     */
    return igmp_send_raw(ctx, inet_addr(IGMP_ALL_V3_ROUTERS),
                         buf, report_size);
}

/* ═══════════════════════════════════════════════════════════════
 * JOIN GROUP — HIGH LEVEL API
 * ═══════════════════════════════════════════════════════════════ */

/*
 * Join a multicast group.
 * For IGMPv2: send a Membership Report.
 * For IGMPv3: send a CHANGE_TO_EXCLUDE{} record (= join all sources).
 *
 * Also calls setsockopt to inform the kernel so it accepts
 * multicast packets at the socket layer.
 */
int igmp_join_group(igmp_ctx_t *ctx, int data_sockfd, const char *group_str) {
    uint32_t group_addr = inet_addr(group_str);
    if (group_addr == INADDR_NONE) {
        fprintf(stderr, "[-] Invalid group address: %s\n", group_str);
        return -1;
    }

    /* Kernel-level multicast join via setsockopt */
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = group_addr;
    mreq.imr_interface.s_addr = ctx->local_ip;

    if (setsockopt(data_sockfd, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                   &mreq, sizeof(mreq)) < 0) {
        if (errno != EADDRINUSE) {  /* EADDRINUSE = already joined */
            perror("[-] IP_ADD_MEMBERSHIP");
            return -1;
        }
    }

    /* Find or create group entry */
    igmp_group_t *grp = NULL;
    for (int i = 0; i < ctx->num_groups; i++) {
        if (ctx->groups[i].group_addr == group_addr) {
            grp = &ctx->groups[i];
            break;
        }
    }

    if (!grp) {
        if (ctx->num_groups >= MAX_GROUPS) {
            fprintf(stderr, "[-] Group table full\n");
            return -1;
        }
        grp = &ctx->groups[ctx->num_groups++];
        memset(grp, 0, sizeof(*grp));
        grp->group_addr = group_addr;
    }

    grp->state       = IGMP_STATE_DELAYING_MEMBER;
    grp->filter_mode = IGMP_FILTER_EXCLUDE;  /* Accept from all sources */
    grp->num_sources = 0;

    /* Send IGMP Report based on negotiated version */
    switch (ctx->igmp_version) {
        case 1:
            /* IGMPv1: use type 0x12 */
            {
                struct igmpv2_hdr hdr = {0};
                uint8_t buf[8];
                hdr.type       = IGMP_TYPE_V1_REPORT;
                hdr.group_addr = group_addr;
                hdr.checksum   = inet_checksum(&hdr, sizeof(hdr));
                memcpy(buf, &hdr, 8);
                igmp_send_raw(ctx, group_addr, buf, 8);
            }
            break;

        case 2:
            igmp_send_v2_report(ctx, group_addr);
            break;

        case 3:
            /* CHANGE_TO_EXCLUDE with empty source list = join all */
            igmp_send_v3_report(ctx, group_addr,
                                IGMPV3_CHANGE_TO_EXCLUDE,
                                NULL, 0);
            break;

        default:
            fprintf(stderr, "[-] Unknown IGMP version %d\n", ctx->igmp_version);
            return -1;
    }

    grp->state = IGMP_STATE_IDLE_MEMBER;
    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * LEAVE GROUP — HIGH LEVEL API
 * ═══════════════════════════════════════════════════════════════ */

int igmp_leave_group(igmp_ctx_t *ctx, int data_sockfd, const char *group_str) {
    uint32_t group_addr = inet_addr(group_str);

    /* Remove kernel-level membership */
    struct ip_mreq mreq;
    mreq.imr_multiaddr.s_addr = group_addr;
    mreq.imr_interface.s_addr = ctx->local_ip;
    setsockopt(data_sockfd, IPPROTO_IP, IP_DROP_MEMBERSHIP,
               &mreq, sizeof(mreq));

    /* Update state and send Leave/Report */
    for (int i = 0; i < ctx->num_groups; i++) {
        if (ctx->groups[i].group_addr == group_addr) {
            ctx->groups[i].state = IGMP_STATE_NON_MEMBER;

            if (ctx->igmp_version == 2) {
                igmp_send_v2_leave(ctx, group_addr);
            } else if (ctx->igmp_version == 3) {
                /* CHANGE_TO_INCLUDE with empty list = leave all sources */
                igmp_send_v3_report(ctx, group_addr,
                                    IGMPV3_CHANGE_TO_INCLUDE,
                                    NULL, 0);
            }
            /* IGMPv1: no Leave message, just stop responding */

            /* Remove from table */
            ctx->groups[i] = ctx->groups[--ctx->num_groups];
            break;
        }
    }

    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * IGMP PACKET PARSER — RECEIVE AND PROCESS
 * ═══════════════════════════════════════════════════════════════ */

typedef struct {
    uint8_t  type;
    uint8_t  max_resp_time;
    uint32_t group_addr;
    /* IGMPv3 query fields */
    uint8_t  s_flag;
    uint8_t  qrv;
    uint8_t  qqic;
    uint16_t num_sources;
    uint32_t *sources;  /* Points into original buffer */
} igmp_parsed_t;

/*
 * Parse an IGMP packet.
 * buf: points to start of IGMP payload (after IP header)
 * len: length of IGMP payload
 */
int igmp_parse(const uint8_t *buf, size_t len, igmp_parsed_t *out) {
    if (len < 8) {
        fprintf(stderr, "[-] IGMP packet too short (%zu bytes)\n", len);
        return -1;
    }

    /* Verify checksum */
    uint16_t received_cksum = *(uint16_t *)(buf + 2);
    uint8_t  tmp[len];
    memcpy(tmp, buf, len);
    *(uint16_t *)(tmp + 2) = 0;   /* Zero checksum field for computation */
    uint16_t computed_cksum = inet_checksum(tmp, len);

    if (received_cksum != computed_cksum) {
        fprintf(stderr, "[-] IGMP checksum mismatch: got %04x expected %04x\n",
                ntohs(received_cksum), ntohs(computed_cksum));
        return -1;
    }

    out->type          = buf[0];
    out->max_resp_time = buf[1];
    out->group_addr    = ntohl(*(uint32_t *)(buf + 4));
    out->s_flag        = 0;
    out->qrv           = 0;
    out->qqic          = 0;
    out->num_sources   = 0;
    out->sources       = NULL;

    /* IGMPv3 Query has additional fields */
    if (out->type == IGMP_TYPE_QUERY && len >= 12) {
        out->s_flag    = (buf[8] >> 3) & 0x1;
        out->qrv       = buf[8] & 0x7;
        out->qqic      = buf[9];
        out->num_sources = ntohs(*(uint16_t *)(buf + 10));
        if (len >= (size_t)(12 + out->num_sources * 4)) {
            out->sources = (uint32_t *)(buf + 12);
        }
    }

    return 0;
}

/*
 * Process a received IGMP message and update host state machine.
 * Called when a host receives a Query from a router.
 */
void igmp_process_query(igmp_ctx_t *ctx, const igmp_parsed_t *pkt) {
    bool is_general_query = (pkt->group_addr == 0);

    printf("[*] Received IGMP %s Query, max_resp=%u×0.1s\n",
           is_general_query ? "General" : "Group-Specific",
           pkt->max_resp_time);

    if (is_general_query) {
        /* General Query: all groups must respond */
        for (int i = 0; i < ctx->num_groups; i++) {
            igmp_group_t *grp = &ctx->groups[i];
            if (grp->state == IGMP_STATE_IDLE_MEMBER) {
                /*
                 * Set report timer to random value in [0, max_resp_time/10]
                 * Use Report Suppression: if we hear another host's Report
                 * for this group before our timer fires, we cancel.
                 */
                grp->state = IGMP_STATE_DELAYING_MEMBER;
                grp->timer_active = true;
                /* In a real implementation: set timer to rand() % max_resp_time */
                printf("[*] Scheduling Report for group %08x\n",
                       grp->group_addr);
            }
        }
    } else {
        /* Group-Specific Query: only the target group responds */
        uint32_t target = htonl(pkt->group_addr);
        for (int i = 0; i < ctx->num_groups; i++) {
            if (ctx->groups[i].group_addr == target) {
                ctx->groups[i].state = IGMP_STATE_DELAYING_MEMBER;
                ctx->groups[i].timer_active = true;
                break;
            }
        }
    }
}

/* ═══════════════════════════════════════════════════════════════
 * SOCKET INITIALIZATION
 * ═══════════════════════════════════════════════════════════════ */

int igmp_ctx_init(igmp_ctx_t *ctx, const char *ifname) {
    struct ifreq ifr;

    memset(ctx, 0, sizeof(*ctx));
    strncpy(ctx->ifname, ifname, IFNAMSIZ - 1);
    ctx->igmp_version = 2;   /* Default to IGMPv2 */

    /* Create raw IP socket */
    ctx->raw_fd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (ctx->raw_fd < 0) {
        perror("[-] socket(SOCK_RAW)");
        return -1;
    }

    /* Enable IP_HDRINCL: we construct IP header ourselves */
    int one = 1;
    if (setsockopt(ctx->raw_fd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one))) {
        perror("[-] IP_HDRINCL");
        close(ctx->raw_fd);
        return -1;
    }

    /* Bind to specific interface */
    if (setsockopt(ctx->raw_fd, SOL_SOCKET, SO_BINDTODEVICE,
                   ifname, strlen(ifname) + 1) < 0) {
        perror("[-] SO_BINDTODEVICE");
        close(ctx->raw_fd);
        return -1;
    }

    /* Get interface index */
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(ctx->raw_fd, SIOCGIFINDEX, &ifr) < 0) {
        perror("[-] SIOCGIFINDEX");
        close(ctx->raw_fd);
        return -1;
    }
    ctx->ifindex = ifr.ifr_ifindex;

    /* Get interface IP address */
    if (ioctl(ctx->raw_fd, SIOCGIFADDR, &ifr) < 0) {
        perror("[-] SIOCGIFADDR");
        close(ctx->raw_fd);
        return -1;
    }
    ctx->local_ip = ((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr.s_addr;

    printf("[+] IGMP context initialized:\n");
    printf("    Interface: %s (index %d)\n", ifname, ctx->ifindex);
    printf("    Local IP:  %s\n", inet_ntoa(*(struct in_addr *)&ctx->local_ip));

    return 0;
}

void igmp_ctx_destroy(igmp_ctx_t *ctx) {
    close(ctx->raw_fd);
    memset(ctx, 0, sizeof(*ctx));
}

/* ═══════════════════════════════════════════════════════════════
 * MAIN — DEMONSTRATION
 * ═══════════════════════════════════════════════════════════════ */

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <interface> <group_ip>\n", argv[0]);
        fprintf(stderr, "Example: %s eth0 239.1.1.1\n", argv[0]);
        return 1;
    }

    const char *ifname    = argv[1];
    const char *group_str = argv[2];

    igmp_ctx_t ctx;
    if (igmp_ctx_init(&ctx, ifname) < 0) {
        return 1;
    }

    /* Create a UDP socket for actual multicast data reception */
    int data_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (data_sock < 0) {
        perror("[-] data socket");
        igmp_ctx_destroy(&ctx);
        return 1;
    }

    /* Join the group */
    printf("\n[+] Joining multicast group %s on %s\n", group_str, ifname);
    if (igmp_join_group(&ctx, data_sock, group_str) < 0) {
        fprintf(stderr, "[-] Failed to join group\n");
        goto cleanup;
    }

    printf("[+] Successfully joined. Waiting 10 seconds...\n");
    sleep(10);

    /* Demonstrate IGMPv3 SSM join (source-specific) */
    printf("\n[+] Demonstrating IGMPv3 SSM join from source 192.168.1.100\n");
    uint32_t sources[] = { inet_addr("192.168.1.100") };
    ctx.igmp_version = 3;
    igmp_send_v3_report(&ctx, inet_addr(group_str),
                         IGMPV3_CHANGE_TO_INCLUDE,
                         sources, 1);

    sleep(3);

    /* Leave the group */
    printf("\n[+] Leaving group %s\n", group_str);
    ctx.igmp_version = 2;
    igmp_leave_group(&ctx, data_sock, group_str);

cleanup:
    close(data_sock);
    igmp_ctx_destroy(&ctx);
    return 0;
}
```

### IGMP Packet Analyzer in C

```c
/*
 * igmp_analyzer.c
 * Passively captures and parses IGMP traffic from a PCAP file or live interface.
 * 
 * Compile: gcc -O2 -Wall -o igmp_analyzer igmp_analyzer.c -lpcap
 * Usage:   ./igmp_analyzer -i eth0          (live capture)
 *          ./igmp_analyzer -r capture.pcap  (offline)
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <pcap.h>
#include <netinet/ip.h>
#include <netinet/ether.h>
#include <arpa/inet.h>

/* Ethernet header length */
#define ETH_HDR_LEN 14

/* IGMP type names */
static const char *igmp_type_name(uint8_t type) {
    switch (type) {
        case 0x11: return "Membership Query";
        case 0x12: return "IGMPv1 Report";
        case 0x16: return "IGMPv2 Report";
        case 0x17: return "IGMPv2 Leave";
        case 0x22: return "IGMPv3 Report";
        default:   return "Unknown";
    }
}

/* Decode IGMPv3 Max Resp Code / QQIC floating-point encoding */
static uint32_t decode_float_code(uint8_t code) {
    if (code < 128) return code;
    uint8_t mant = code & 0x0F;
    uint8_t exp  = (code >> 4) & 0x07;
    return (uint32_t)((mant | 0x10) << (exp + 3));
}

static void analyze_igmpv3_report(const uint8_t *buf, uint16_t len) {
    if (len < 8) return;

    uint16_t num_grecs = ntohs(*(uint16_t *)(buf + 6));
    printf("    IGMPv3 Report: %u group record(s)\n", num_grecs);

    size_t offset = 8;
    for (uint16_t i = 0; i < num_grecs && offset < len; i++) {
        if (offset + 8 > len) break;

        uint8_t  rtype      = buf[offset];
        uint8_t  aux_len    = buf[offset + 1];
        uint16_t nsrc       = ntohs(*(uint16_t *)(buf + offset + 2));
        uint32_t mcast_addr = *(uint32_t *)(buf + offset + 4);

        const char *rtype_str;
        switch (rtype) {
            case 1: rtype_str = "MODE_IS_INCLUDE";    break;
            case 2: rtype_str = "MODE_IS_EXCLUDE";    break;
            case 3: rtype_str = "CHANGE_TO_INCLUDE";  break;
            case 4: rtype_str = "CHANGE_TO_EXCLUDE";  break;
            case 5: rtype_str = "ALLOW_NEW_SOURCES";  break;
            case 6: rtype_str = "BLOCK_OLD_SOURCES";  break;
            default: rtype_str = "UNKNOWN";            break;
        }

        printf("    Record [%u]: type=%s group=%s sources=%u\n",
               i, rtype_str,
               inet_ntoa(*(struct in_addr *)&mcast_addr),
               nsrc);

        offset += 8;  /* Past grec header */
        for (uint16_t s = 0; s < nsrc && offset + 4 <= len; s++) {
            uint32_t src = *(uint32_t *)(buf + offset);
            printf("      Source: %s\n", inet_ntoa(*(struct in_addr *)&src));
            offset += 4;
        }
        offset += aux_len * 4;  /* Skip auxiliary data */
    }
}

static void analyze_igmpv3_query(const uint8_t *buf, uint16_t len) {
    if (len < 12) return;

    uint8_t  max_resp_code = buf[1];
    uint32_t group         = *(uint32_t *)(buf + 4);
    uint8_t  s_flag        = (buf[8] >> 3) & 1;
    uint8_t  qrv           = buf[8] & 7;
    uint8_t  qqic          = buf[9];
    uint16_t nsrc          = ntohs(*(uint16_t *)(buf + 10));

    uint32_t max_resp_ms = decode_float_code(max_resp_code) * 100;
    uint32_t qi_sec      = decode_float_code(qqic);

    if (group == 0) {
        printf("    IGMPv3 General Query\n");
    } else {
        printf("    IGMPv3 %s-Specific Query: group=%s\n",
               nsrc > 0 ? "Group-and-Source" : "Group",
               inet_ntoa(*(struct in_addr *)&group));
    }
    printf("    Max Response: %u ms, S=%u, QRV=%u, QI=%u sec, Sources=%u\n",
           max_resp_ms, s_flag, qrv, qi_sec, nsrc);
}

/* Main packet callback */
static void packet_handler(u_char *user, const struct pcap_pkthdr *hdr,
                            const u_char *pkt) {
    (void)user;

    if (hdr->caplen < ETH_HDR_LEN + sizeof(struct iphdr)) return;

    const struct iphdr *iph = (const struct iphdr *)(pkt + ETH_HDR_LEN);

    if (iph->protocol != 2) return;   /* Not IGMP */
    if (iph->ttl != 1) {
        printf("[!] ANOMALY: IGMP packet with TTL=%u (expected 1)\n", iph->ttl);
    }

    int ip_hdr_len = iph->ihl * 4;
    const uint8_t *igmp_start = (const uint8_t *)iph + ip_hdr_len;
    uint16_t igmp_len = ntohs(iph->tot_len) - ip_hdr_len;

    if (igmp_len < 8) return;

    uint8_t igmp_type = igmp_start[0];

    /* Format timestamp */
    time_t ts = (time_t)hdr->ts.tv_sec;
    struct tm *tm_info = localtime(&ts);
    char time_buf[32];
    strftime(time_buf, sizeof(time_buf), "%H:%M:%S", tm_info);

    printf("[%s.%06u] IGMP %s\n",
           time_buf, (unsigned)hdr->ts.tv_usec,
           igmp_type_name(igmp_type));
    printf("  Src: %-16s → Dst: %s\n",
           inet_ntoa(*(struct in_addr *)&iph->saddr),
           inet_ntoa(*(struct in_addr *)&iph->daddr));

    /* Per-type analysis */
    if (igmp_type == 0x11) {
        uint32_t grp = *(uint32_t *)(igmp_start + 4);
        if (grp == 0) {
            printf("  General Query (all groups)\n");
        } else {
            printf("  Group-Specific Query: %s\n",
                   inet_ntoa(*(struct in_addr *)&grp));
        }
        if (igmp_len >= 12) analyze_igmpv3_query(igmp_start, igmp_len);
    }

    if (igmp_type == 0x16 || igmp_type == 0x12) {
        uint32_t grp = *(uint32_t *)(igmp_start + 4);
        printf("  Joining group: %s\n", inet_ntoa(*(struct in_addr *)&grp));
    }

    if (igmp_type == 0x17) {
        uint32_t grp = *(uint32_t *)(igmp_start + 4);
        printf("  Leaving group: %s\n", inet_ntoa(*(struct in_addr *)&grp));
    }

    if (igmp_type == 0x22) {
        analyze_igmpv3_report(igmp_start, igmp_len);
    }

    printf("\n");
}

int main(int argc, char *argv[]) {
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle;

    if (argc == 3 && strcmp(argv[1], "-i") == 0) {
        handle = pcap_open_live(argv[2], 65535, 1, 100, errbuf);
    } else if (argc == 3 && strcmp(argv[1], "-r") == 0) {
        handle = pcap_open_offline(argv[2], errbuf);
    } else {
        fprintf(stderr, "Usage: %s -i <iface> | -r <file.pcap>\n", argv[0]);
        return 1;
    }

    if (!handle) {
        fprintf(stderr, "pcap error: %s\n", errbuf);
        return 1;
    }

    /* Apply BPF filter: only IGMP packets */
    struct bpf_program fp;
    if (pcap_compile(handle, &fp, "ip proto 2", 0, PCAP_NETMASK_UNKNOWN) == 0) {
        pcap_setfilter(handle, &fp);
        pcap_freecode(&fp);
    }

    printf("[*] IGMP Analyzer started. Waiting for IGMP packets...\n\n");
    pcap_loop(handle, 0, packet_handler, NULL);
    pcap_close(handle);
    return 0;
}
```

---

## 17. Rust Implementation

### Complete Type-Safe IGMP Engine in Rust

```rust
//! igmp.rs — Complete IGMPv1/v2/v3 implementation in Rust
//!
//! Demonstrates: zero-copy parsing, type-safe packet construction,
//! state machine using enums, async-ready timer management.
//!
//! Cargo.toml dependencies:
//!   [dependencies]
//!   socket2 = "0.5"
//!   tokio = { version = "1", features = ["full"] }
//!   thiserror = "1"
//!   byteorder = "1"
//!   tracing = "0.1"

use std::fmt;
use std::net::Ipv4Addr;
use std::time::{Duration, Instant};
use byteorder::{BigEndian, ByteOrder};

// ─────────────────────────────────────────────────────────────────────────────
// PROTOCOL CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────

/// IGMP message types
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IgmpType {
    MembershipQuery   = 0x11,
    MembershipReportV1 = 0x12,
    MembershipReportV2 = 0x16,
    LeaveGroup        = 0x17,
    MembershipReportV3 = 0x22,
}

impl IgmpType {
    pub fn from_u8(v: u8) -> Option<Self> {
        match v {
            0x11 => Some(Self::MembershipQuery),
            0x12 => Some(Self::MembershipReportV1),
            0x16 => Some(Self::MembershipReportV2),
            0x17 => Some(Self::LeaveGroup),
            0x22 => Some(Self::MembershipReportV3),
            _    => None,
        }
    }
}

/// IGMPv3 Group Record types
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GroupRecordType {
    ModeIsInclude       = 1,
    ModeIsExclude       = 2,
    ChangeToInclude     = 3,
    ChangeToExclude     = 4,
    AllowNewSources     = 5,
    BlockOldSources     = 6,
}

impl GroupRecordType {
    pub fn from_u8(v: u8) -> Option<Self> {
        match v {
            1 => Some(Self::ModeIsInclude),
            2 => Some(Self::ModeIsExclude),
            3 => Some(Self::ChangeToInclude),
            4 => Some(Self::ChangeToExclude),
            5 => Some(Self::AllowNewSources),
            6 => Some(Self::BlockOldSources),
            _ => None,
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// WELL-KNOWN ADDRESSES
// ─────────────────────────────────────────────────────────────────────────────

pub const ALL_HOSTS_ADDR:    Ipv4Addr = Ipv4Addr::new(224, 0, 0, 1);
pub const ALL_ROUTERS_ADDR:  Ipv4Addr = Ipv4Addr::new(224, 0, 0, 2);
pub const ALL_V3_ROUTERS:    Ipv4Addr = Ipv4Addr::new(224, 0, 0, 22);

// ─────────────────────────────────────────────────────────────────────────────
// ERROR TYPES
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, thiserror::Error)]
pub enum IgmpError {
    #[error("Packet too short: got {got}, expected {expected}")]
    TooShort { got: usize, expected: usize },

    #[error("Invalid IGMP type: 0x{0:02X}")]
    UnknownType(u8),

    #[error("Checksum mismatch: computed 0x{computed:04X}, got 0x{received:04X}")]
    ChecksumMismatch { computed: u16, received: u16 },

    #[error("Invalid group address: {0}")]
    InvalidGroup(Ipv4Addr),

    #[error("Buffer overflow: need {need}, have {have}")]
    BufferOverflow { need: usize, have: usize },

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

pub type IgmpResult<T> = Result<T, IgmpError>;

// ─────────────────────────────────────────────────────────────────────────────
// INTERNET CHECKSUM (RFC 1071)
// ─────────────────────────────────────────────────────────────────────────────

/// Compute Internet checksum over a byte slice.
/// Returns checksum in network byte order (big-endian u16).
pub fn inet_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut chunks = data.chunks_exact(2);

    for chunk in &mut chunks {
        sum += u32::from(BigEndian::read_u16(chunk));
    }

    // Handle odd byte
    if let Some(&last) = chunks.remainder().first() {
        sum += u32::from(last) << 8;
    }

    // Fold 32-bit sum to 16 bits
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    !(sum as u16)
}

/// Verify checksum of an IGMP message.
/// The checksum field must be at bytes [2..4].
pub fn verify_checksum(buf: &[u8]) -> bool {
    if buf.len() < 4 { return false; }
    // Checksum of entire message (including checksum field) should equal 0
    // when checksum is included. Alternatively, zero the field and compare.
    let received = BigEndian::read_u16(&buf[2..4]);
    let mut tmp = buf.to_vec();
    tmp[2] = 0;
    tmp[3] = 0;
    let computed = inet_checksum(&tmp);
    computed == received
}

// ─────────────────────────────────────────────────────────────────────────────
// IGMP PACKET TYPES — ZERO-COPY VIEWS
// ─────────────────────────────────────────────────────────────────────────────

/// IGMPv1/v2 message view (immutable reference into packet buffer)
#[derive(Debug)]
pub struct IgmpV2View<'a> {
    raw: &'a [u8],  // Exactly 8 bytes
}

impl<'a> IgmpV2View<'a> {
    pub fn parse(buf: &'a [u8]) -> IgmpResult<Self> {
        if buf.len() < 8 {
            return Err(IgmpError::TooShort { got: buf.len(), expected: 8 });
        }
        if !verify_checksum(&buf[..8]) {
            let received = BigEndian::read_u16(&buf[2..4]);
            let mut tmp = buf[..8].to_vec();
            tmp[2] = 0; tmp[3] = 0;
            let computed = inet_checksum(&tmp);
            return Err(IgmpError::ChecksumMismatch { computed, received });
        }
        Ok(Self { raw: &buf[..8] })
    }

    pub fn msg_type(&self) -> Option<IgmpType> {
        IgmpType::from_u8(self.raw[0])
    }

    pub fn max_resp_time_ms(&self) -> u32 {
        // Max Response Time is in units of 1/10 second
        u32::from(self.raw[1]) * 100
    }

    pub fn group_addr(&self) -> Ipv4Addr {
        Ipv4Addr::from(BigEndian::read_u32(&self.raw[4..8]))
    }

    pub fn is_general_query(&self) -> bool {
        self.group_addr() == Ipv4Addr::UNSPECIFIED
    }

    pub fn raw_type(&self) -> u8 { self.raw[0] }
}

/// IGMPv3 Query view
#[derive(Debug)]
pub struct IgmpV3QueryView<'a> {
    raw: &'a [u8],  // At least 12 bytes + 4*num_sources
}

impl<'a> IgmpV3QueryView<'a> {
    pub fn parse(buf: &'a [u8]) -> IgmpResult<Self> {
        if buf.len() < 12 {
            return Err(IgmpError::TooShort { got: buf.len(), expected: 12 });
        }
        let nsrc = BigEndian::read_u16(&buf[10..12]) as usize;
        let required = 12 + nsrc * 4;
        if buf.len() < required {
            return Err(IgmpError::TooShort { got: buf.len(), expected: required });
        }
        Ok(Self { raw: &buf[..required] })
    }

    pub fn group_addr(&self) -> Ipv4Addr {
        Ipv4Addr::from(BigEndian::read_u32(&self.raw[4..8]))
    }

    /// Decode Max Resp Code (floating-point encoding for values >= 128)
    pub fn max_resp_time_ms(&self) -> u32 {
        decode_float_code(self.raw[1]) * 100
    }

    /// S-flag: suppress router-side processing
    pub fn s_flag(&self) -> bool {
        (self.raw[8] >> 3) & 1 == 1
    }

    /// QRV: Querier's Robustness Variable
    pub fn qrv(&self) -> u8 {
        self.raw[8] & 0x07
    }

    /// QQIC decoded to Query Interval in seconds
    pub fn query_interval_secs(&self) -> u32 {
        decode_float_code(self.raw[9])
    }

    pub fn num_sources(&self) -> u16 {
        BigEndian::read_u16(&self.raw[10..12])
    }

    pub fn sources(&self) -> impl Iterator<Item = Ipv4Addr> + 'a {
        let nsrc = self.num_sources() as usize;
        let base = &self.raw[12..12 + nsrc * 4];
        (0..nsrc).map(move |i| {
            Ipv4Addr::from(BigEndian::read_u32(&base[i*4..i*4+4]))
        })
    }

    pub fn query_kind(&self) -> QueryKind {
        let grp = self.group_addr();
        let nsrc = self.num_sources();
        if grp == Ipv4Addr::UNSPECIFIED {
            QueryKind::General
        } else if nsrc == 0 {
            QueryKind::GroupSpecific(grp)
        } else {
            QueryKind::GroupAndSourceSpecific(grp, nsrc)
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum QueryKind {
    General,
    GroupSpecific(Ipv4Addr),
    GroupAndSourceSpecific(Ipv4Addr, u16),
}

/// IGMPv3 Group Record (parsed, owned)
#[derive(Debug, Clone)]
pub struct GroupRecord {
    pub record_type: GroupRecordType,
    pub group_addr:  Ipv4Addr,
    pub sources:     Vec<Ipv4Addr>,
}

/// IGMPv3 Report (parsed, owned)
#[derive(Debug, Clone)]
pub struct IgmpV3Report {
    pub records: Vec<GroupRecord>,
}

impl IgmpV3Report {
    pub fn parse(buf: &[u8]) -> IgmpResult<Self> {
        if buf.len() < 8 {
            return Err(IgmpError::TooShort { got: buf.len(), expected: 8 });
        }

        if buf[0] != IgmpType::MembershipReportV3 as u8 {
            return Err(IgmpError::UnknownType(buf[0]));
        }

        let num_grecs = BigEndian::read_u16(&buf[6..8]) as usize;
        let mut records = Vec::with_capacity(num_grecs);
        let mut offset = 8usize;

        for _ in 0..num_grecs {
            if offset + 8 > buf.len() {
                return Err(IgmpError::TooShort { got: buf.len(), expected: offset + 8 });
            }

            let rtype_byte = buf[offset];
            let record_type = GroupRecordType::from_u8(rtype_byte)
                .ok_or(IgmpError::UnknownType(rtype_byte))?;
            let aux_data_len = buf[offset + 1] as usize;
            let num_sources  = BigEndian::read_u16(&buf[offset+2..offset+4]) as usize;
            let group_addr   = Ipv4Addr::from(
                BigEndian::read_u32(&buf[offset+4..offset+8])
            );

            offset += 8;

            let mut sources = Vec::with_capacity(num_sources);
            for _ in 0..num_sources {
                if offset + 4 > buf.len() {
                    return Err(IgmpError::TooShort {
                        got: buf.len(), expected: offset + 4
                    });
                }
                let src = Ipv4Addr::from(BigEndian::read_u32(&buf[offset..offset+4]));
                sources.push(src);
                offset += 4;
            }

            // Skip auxiliary data
            offset += aux_data_len * 4;

            records.push(GroupRecord { record_type, group_addr, sources });
        }

        Ok(IgmpV3Report { records })
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// FLOAT CODE ENCODING/DECODING (used in IGMPv3 Max Resp Code and QQIC)
// ─────────────────────────────────────────────────────────────────────────────

/// Decode IGMPv3 floating-point-encoded value.
/// Values 0-127: literal value.
/// Values 128-255: exponential encoding.
pub fn decode_float_code(code: u8) -> u32 {
    if code < 128 {
        u32::from(code)
    } else {
        let mant = u32::from(code & 0x0F);
        let exp  = u32::from((code >> 4) & 0x07);
        (mant | 0x10) << (exp + 3)
    }
}

/// Encode a value into IGMPv3 floating-point format.
/// Returns the encoded byte, with possible precision loss for large values.
pub fn encode_float_code(value: u32) -> u8 {
    if value < 128 {
        return value as u8;
    }
    // Find the highest bit position
    let mut exp = 0u8;
    let mut v = value;
    while v > 0x1F {
        v >>= 1;
        exp += 1;
    }
    let mant = (v & 0x0F) as u8;
    let exp_field = (exp - 3).min(7);
    0x80 | (exp_field << 4) | mant
}

// ─────────────────────────────────────────────────────────────────────────────
// PACKET BUILDERS
// ─────────────────────────────────────────────────────────────────────────────

/// Builds an IGMPv2 Membership Report packet.
/// Returns 8-byte buffer.
pub fn build_v2_report(group: Ipv4Addr) -> [u8; 8] {
    let mut buf = [0u8; 8];
    buf[0] = IgmpType::MembershipReportV2 as u8;
    buf[1] = 0;   // Max Resp Time unused in Reports
    // bytes 2-3: checksum (filled after)
    BigEndian::write_u32(&mut buf[4..8], u32::from(group));
    let cksum = inet_checksum(&buf);
    BigEndian::write_u16(&mut buf[2..4], cksum);
    buf
}

/// Builds an IGMPv2 Leave Group packet.
/// Returns 8-byte buffer.
pub fn build_v2_leave(group: Ipv4Addr) -> [u8; 8] {
    let mut buf = [0u8; 8];
    buf[0] = IgmpType::LeaveGroup as u8;
    buf[1] = 0;
    BigEndian::write_u32(&mut buf[4..8], u32::from(group));
    let cksum = inet_checksum(&buf);
    BigEndian::write_u16(&mut buf[2..4], cksum);
    buf
}

/// Builds an IGMPv2 General Query packet.
/// max_resp_time: in 1/10 second units (e.g., 100 = 10.0 seconds)
pub fn build_v2_general_query(max_resp_time: u8) -> [u8; 8] {
    let mut buf = [0u8; 8];
    buf[0] = IgmpType::MembershipQuery as u8;
    buf[1] = max_resp_time;
    // Group address: 0.0.0.0 for General Query (already zero)
    let cksum = inet_checksum(&buf);
    BigEndian::write_u16(&mut buf[2..4], cksum);
    buf
}

/// Builds an IGMPv2 Group-Specific Query.
pub fn build_v2_group_query(group: Ipv4Addr, max_resp_time: u8) -> [u8; 8] {
    let mut buf = [0u8; 8];
    buf[0] = IgmpType::MembershipQuery as u8;
    buf[1] = max_resp_time;
    BigEndian::write_u32(&mut buf[4..8], u32::from(group));
    let cksum = inet_checksum(&buf);
    BigEndian::write_u16(&mut buf[2..4], cksum);
    buf
}

/// Builds an IGMPv3 Membership Report with a single group record.
pub fn build_v3_report(
    group:       Ipv4Addr,
    record_type: GroupRecordType,
    sources:     &[Ipv4Addr],
) -> Vec<u8> {
    let grec_size = 8 + sources.len() * 4;  // 4 (type/auxlen/nsrc) + 4 (group) + sources
    let total_size = 8 + grec_size;         // 8 (report header) + grec

    let mut buf = vec![0u8; total_size];

    // Report header
    buf[0] = IgmpType::MembershipReportV3 as u8;
    buf[1] = 0;   // Reserved
    // buf[2..4]: checksum (filled later)
    // buf[4..6]: Reserved
    BigEndian::write_u16(&mut buf[6..8], 1);  // One group record

    // Group Record
    let grec_offset = 8;
    buf[grec_offset]     = record_type as u8;
    buf[grec_offset + 1] = 0;  // Aux data len = 0
    BigEndian::write_u16(&mut buf[grec_offset+2..grec_offset+4],
                         sources.len() as u16);
    BigEndian::write_u32(&mut buf[grec_offset+4..grec_offset+8],
                         u32::from(group));

    // Source addresses
    for (i, src) in sources.iter().enumerate() {
        let off = grec_offset + 8 + i * 4;
        BigEndian::write_u32(&mut buf[off..off+4], u32::from(*src));
    }

    // Compute checksum
    let cksum = inet_checksum(&buf);
    BigEndian::write_u16(&mut buf[2..4], cksum);

    buf
}

// ─────────────────────────────────────────────────────────────────────────────
// HOST STATE MACHINE
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum HostState {
    NonMember,
    DelayingMember { timer_deadline: Instant },
    IdleMember,
}

/// Source filter mode for IGMPv3
#[derive(Debug, Clone, PartialEq)]
pub enum FilterMode {
    Include(Vec<Ipv4Addr>),  // Accept ONLY from these sources
    Exclude(Vec<Ipv4Addr>),  // Accept from ALL EXCEPT these sources
}

impl FilterMode {
    /// An empty INCLUDE set means "receive from nobody" (effectively leave)
    pub fn is_empty_include(&self) -> bool {
        matches!(self, FilterMode::Include(srcs) if srcs.is_empty())
    }

    /// An empty EXCLUDE set means "receive from everyone" (any-source multicast)
    pub fn is_full_exclude(&self) -> bool {
        matches!(self, FilterMode::Exclude(srcs) if srcs.is_empty())
    }
}

/// Group membership entry in the host's membership table
#[derive(Debug)]
pub struct GroupMembership {
    pub group:       Ipv4Addr,
    pub state:       HostState,
    pub filter:      FilterMode,
    pub version:     u8,  // IGMP version in use (1, 2, or 3)
}

impl GroupMembership {
    pub fn new_any_source(group: Ipv4Addr, version: u8) -> Self {
        Self {
            group,
            state: HostState::NonMember,
            filter: FilterMode::Exclude(vec![]),  // No exclusions = accept all
            version,
        }
    }

    pub fn new_source_specific(group: Ipv4Addr, sources: Vec<Ipv4Addr>) -> Self {
        Self {
            group,
            state: HostState::NonMember,
            filter: FilterMode::Include(sources),
            version: 3,
        }
    }

    /// Transition: host joins the group
    pub fn join(&mut self, random_delay_ms: u64) -> JoinAction {
        self.state = HostState::DelayingMember {
            timer_deadline: Instant::now() + Duration::from_millis(random_delay_ms),
        };
        JoinAction::SendReport {
            group:       self.group,
            filter:      self.filter.clone(),
            version:     self.version,
        }
    }

    /// Transition: host leaves the group
    pub fn leave(&mut self) -> LeaveAction {
        let was_member = matches!(self.state,
            HostState::IdleMember | HostState::DelayingMember { .. });
        self.state = HostState::NonMember;
        if was_member {
            LeaveAction::SendLeave { group: self.group, version: self.version }
        } else {
            LeaveAction::NoAction
        }
    }

    /// Transition: received a Query
    pub fn on_query(&mut self, max_resp_ms: u64) -> QueryResponse {
        match &self.state {
            HostState::IdleMember => {
                // Compute random delay in [0, max_resp_ms]
                let delay = max_resp_ms / 2;  // Simplified; use rand in production
                self.state = HostState::DelayingMember {
                    timer_deadline: Instant::now() + Duration::from_millis(delay),
                };
                QueryResponse::ScheduledReport(Duration::from_millis(delay))
            }
            HostState::DelayingMember { timer_deadline } => {
                // If new deadline < current, reset to new
                let new_deadline = Instant::now() + Duration::from_millis(max_resp_ms / 2);
                if new_deadline < *timer_deadline {
                    self.state = HostState::DelayingMember {
                        timer_deadline: new_deadline,
                    };
                }
                QueryResponse::AlreadyScheduled
            }
            HostState::NonMember => QueryResponse::Ignored,
        }
    }

    /// Transition: heard another host's Report for our group (Report Suppression)
    /// NOTE: Only applies in IGMPv1 and IGMPv2!
    pub fn on_other_report(&mut self) {
        if let HostState::DelayingMember { .. } = self.state {
            // Cancel our pending report — another host already reported
            self.state = HostState::IdleMember;
        }
    }

    /// Transition: our timer fires — send the Report
    pub fn on_timer_fired(&mut self) -> Option<SentReport> {
        if let HostState::DelayingMember { timer_deadline } = &self.state {
            if Instant::now() >= *timer_deadline {
                self.state = HostState::IdleMember;
                return Some(SentReport {
                    group:  self.group,
                    filter: self.filter.clone(),
                });
            }
        }
        None
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// ACTION TYPES — WHAT THE STATE MACHINE TELLS THE NETWORK LAYER TO DO
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum JoinAction {
    SendReport { group: Ipv4Addr, filter: FilterMode, version: u8 },
}

#[derive(Debug)]
pub enum LeaveAction {
    SendLeave { group: Ipv4Addr, version: u8 },
    NoAction,
}

#[derive(Debug)]
pub enum QueryResponse {
    ScheduledReport(Duration),
    AlreadyScheduled,
    Ignored,
}

#[derive(Debug)]
pub struct SentReport {
    pub group:  Ipv4Addr,
    pub filter: FilterMode,
}

// ─────────────────────────────────────────────────────────────────────────────
// ROUTER-SIDE: GROUP MEMBERSHIP TABLE
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum RouterGroupState {
    /// No hosts currently want this group
    NoMembersPresent,
    /// At least one host is a member; expiry timer is active
    MembersPresent { expiry: Instant },
    /// Leave received; waiting for Group-Specific Query response
    CheckingMembership { queries_remaining: u8, next_query: Instant },
}

#[derive(Debug)]
pub struct RouterGroupEntry {
    pub group:   Ipv4Addr,
    pub state:   RouterGroupState,
    /// For IGMPv3: per-source state
    pub sources: Vec<(Ipv4Addr, Instant)>,  // (source, expiry)
}

impl RouterGroupEntry {
    pub fn new(group: Ipv4Addr, membership_interval: Duration) -> Self {
        Self {
            group,
            state: RouterGroupState::MembersPresent {
                expiry: Instant::now() + membership_interval,
            },
            sources: Vec::new(),
        }
    }

    /// Process an incoming Membership Report
    pub fn on_report(&mut self, membership_interval: Duration) {
        self.state = RouterGroupState::MembersPresent {
            expiry: Instant::now() + membership_interval,
        };
    }

    /// Process a Leave Group message
    pub fn on_leave(&mut self, lmqi: Duration, lmqc: u8) {
        self.state = RouterGroupState::CheckingMembership {
            queries_remaining: lmqc,
            next_query: Instant::now() + lmqi,
        };
    }

    /// Check if the group entry has expired
    pub fn is_expired(&self) -> bool {
        match &self.state {
            RouterGroupState::MembersPresent { expiry } => Instant::now() >= *expiry,
            RouterGroupState::NoMembersPresent => true,
            _ => false,
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// GENERIC IGMP MESSAGE PARSER
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum IgmpMessage<'a> {
    V1Query(IgmpV2View<'a>),
    V2Query(IgmpV2View<'a>),
    V3Query(IgmpV3QueryView<'a>),
    V1Report(IgmpV2View<'a>),
    V2Report(IgmpV2View<'a>),
    V2Leave(IgmpV2View<'a>),
    V3Report(IgmpV3Report),
}

impl<'a> IgmpMessage<'a> {
    pub fn parse(buf: &'a [u8]) -> IgmpResult<Self> {
        if buf.is_empty() {
            return Err(IgmpError::TooShort { got: 0, expected: 8 });
        }

        match buf[0] {
            0x11 => {
                // Determine version from packet length and content
                if buf.len() >= 12 {
                    // IGMPv3 Query (has extra fields)
                    Ok(IgmpMessage::V3Query(IgmpV3QueryView::parse(buf)?))
                } else {
                    // IGMPv1 or v2 Query (8 bytes)
                    let view = IgmpV2View::parse(buf)?;
                    // Distinguish v1 from v2 by max_resp_time:
                    // v1 sets it to 0; v2 uses it
                    if buf[1] == 0 {
                        Ok(IgmpMessage::V1Query(view))
                    } else {
                        Ok(IgmpMessage::V2Query(view))
                    }
                }
            }
            0x12 => Ok(IgmpMessage::V1Report(IgmpV2View::parse(buf)?)),
            0x16 => Ok(IgmpMessage::V2Report(IgmpV2View::parse(buf)?)),
            0x17 => Ok(IgmpMessage::V2Leave(IgmpV2View::parse(buf)?)),
            0x22 => Ok(IgmpMessage::V3Report(IgmpV3Report::parse(buf)?)),
            t    => Err(IgmpError::UnknownType(t)),
        }
    }
}

impl fmt::Display for IgmpMessage<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            IgmpMessage::V1Query(v)  => write!(f, "IGMPv1 General Query"),
            IgmpMessage::V2Query(v)  => {
                if v.is_general_query() {
                    write!(f, "IGMPv2 General Query (max_resp={}ms)",
                           v.max_resp_time_ms())
                } else {
                    write!(f, "IGMPv2 Group-Specific Query for {} (max_resp={}ms)",
                           v.group_addr(), v.max_resp_time_ms())
                }
            }
            IgmpMessage::V3Query(v) => {
                write!(f, "IGMPv3 {:?} (max_resp={}ms, QI={}s)",
                       v.query_kind(),
                       v.max_resp_time_ms(),
                       v.query_interval_secs())
            }
            IgmpMessage::V1Report(v) => write!(f, "IGMPv1 Report for {}", v.group_addr()),
            IgmpMessage::V2Report(v) => write!(f, "IGMPv2 Report for {}", v.group_addr()),
            IgmpMessage::V2Leave(v)  => write!(f, "IGMPv2 Leave for {}", v.group_addr()),
            IgmpMessage::V3Report(r) => {
                write!(f, "IGMPv3 Report ({} group records)", r.records.len())
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// ANOMALY DETECTION
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, PartialEq)]
pub enum IgmpAnomaly {
    InvalidTtl(u8),
    MissingRouterAlert,
    SpoofedQuerier { src: Ipv4Addr },
    SpuriousLeave { group: Ipv4Addr, src: Ipv4Addr },
    FloodingBehavior { src: Ipv4Addr, count: usize },
    ReservedGroupJoin { group: Ipv4Addr },
    V3ReportWithoutSsmSupport,
}

/// Validate an IGMP packet for anomalies.
/// ip_ttl: TTL from the outer IP header
/// has_router_alert: whether the IP Router Alert option was present
/// src_ip: source IP from outer IP header
pub fn detect_anomalies(
    msg: &IgmpMessage<'_>,
    ip_ttl: u8,
    has_router_alert: bool,
    src_ip: Ipv4Addr,
) -> Vec<IgmpAnomaly> {
    let mut anomalies = Vec::new();

    // TTL must be 1
    if ip_ttl != 1 {
        anomalies.push(IgmpAnomaly::InvalidTtl(ip_ttl));
    }

    // v2/v3 must have Router Alert option
    match msg {
        IgmpMessage::V2Query(_)
        | IgmpMessage::V2Report(_)
        | IgmpMessage::V2Leave(_)
        | IgmpMessage::V3Query(_)
        | IgmpMessage::V3Report(_) => {
            if !has_router_alert {
                anomalies.push(IgmpAnomaly::MissingRouterAlert);
            }
        }
        _ => {}
    }

    // Queries must come from a router (should be a router IP, not a host)
    // A non-router sending a Query = Querier spoofing
    // In practice: validate against known router IPs
    // Simplified heuristic: Query from a .1 or .2 address is normal;
    // anything else is suspicious in most networks (not a reliable check)

    // Check for Reserved group join (224.0.0.x by a non-router)
    let check_reserved = |group: Ipv4Addr| -> bool {
        let octets = group.octets();
        octets[0] == 224 && octets[1] == 0 && octets[2] == 0
    };

    match msg {
        IgmpMessage::V2Report(v) | IgmpMessage::V1Report(v) => {
            if check_reserved(v.group_addr()) {
                anomalies.push(IgmpAnomaly::ReservedGroupJoin {
                    group: v.group_addr(),
                });
            }
        }
        _ => {}
    }

    anomalies
}

// ─────────────────────────────────────────────────────────────────────────────
// TESTS
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_checksum_known_packet() {
        // Known valid IGMPv2 General Query
        // Type=0x11, MRT=100, Cksum=0xEE9B, Group=0.0.0.0
        let pkt = [0x11u8, 0x64, 0xEE, 0x9B, 0x00, 0x00, 0x00, 0x00];
        assert!(verify_checksum(&pkt), "Checksum verification failed");
    }

    #[test]
    fn test_build_v2_report_valid() {
        let group = Ipv4Addr::new(239, 1, 1, 1);
        let pkt = build_v2_report(group);
        assert_eq!(pkt[0], 0x16, "Wrong IGMP type");
        assert!(verify_checksum(&pkt), "Generated packet has bad checksum");
        let addr = Ipv4Addr::from(BigEndian::read_u32(&pkt[4..8]));
        assert_eq!(addr, group, "Wrong group address in Report");
    }

    #[test]
    fn test_build_v2_leave_valid() {
        let group = Ipv4Addr::new(239, 2, 2, 2);
        let pkt = build_v2_leave(group);
        assert_eq!(pkt[0], 0x17, "Wrong IGMP type");
        assert!(verify_checksum(&pkt), "Leave packet has bad checksum");
    }

    #[test]
    fn test_parse_v2_report() {
        let group = Ipv4Addr::new(239, 1, 1, 1);
        let raw = build_v2_report(group);
        let view = IgmpV2View::parse(&raw).expect("Parse failed");
        assert_eq!(view.msg_type(), Some(IgmpType::MembershipReportV2));
        assert_eq!(view.group_addr(), group);
    }

    #[test]
    fn test_parse_general_query() {
        let raw = build_v2_general_query(100);
        let view = IgmpV2View::parse(&raw).expect("Parse failed");
        assert!(view.is_general_query());
        assert_eq!(view.max_resp_time_ms(), 10000); // 100 × 100ms = 10000ms
    }

    #[test]
    fn test_v3_report_roundtrip() {
        let group = Ipv4Addr::new(239, 1, 1, 1);
        let sources = vec![
            Ipv4Addr::new(192, 168, 1, 100),
            Ipv4Addr::new(10, 0, 0, 1),
        ];
        let raw = build_v3_report(group, GroupRecordType::ChangeToInclude, &sources);
        assert!(verify_checksum(&raw), "v3 report checksum invalid");

        let parsed = IgmpV3Report::parse(&raw).expect("v3 parse failed");
        assert_eq!(parsed.records.len(), 1);
        assert_eq!(parsed.records[0].group_addr, group);
        assert_eq!(parsed.records[0].sources, sources);
        assert_eq!(parsed.records[0].record_type, GroupRecordType::ChangeToInclude);
    }

    #[test]
    fn test_float_code_roundtrip() {
        for v in [0u32, 100, 127, 128, 256, 1000, 31744] {
            let encoded = encode_float_code(v);
            let decoded = decode_float_code(encoded);
            // Allow for precision loss in float encoding
            if v < 128 {
                assert_eq!(decoded, v, "Exact value {}", v);
            } else {
                // Approximate within 12.5% (floating point encoding loss)
                let ratio = if decoded > v { decoded as f64 / v as f64 }
                            else { v as f64 / decoded as f64 };
                assert!(ratio <= 1.125, "Float roundtrip too inaccurate: {} → {} → {}",
                        v, encoded, decoded);
            }
        }
    }

    #[test]
    fn test_state_machine_basic() {
        let mut membership = GroupMembership::new_any_source(
            Ipv4Addr::new(239, 1, 1, 1), 2
        );
        assert_eq!(membership.state, HostState::NonMember);

        // Join
        membership.join(500);
        assert!(matches!(membership.state, HostState::DelayingMember { .. }));

        // Report Suppression
        membership.on_other_report();
        assert_eq!(membership.state, HostState::IdleMember);

        // Leave
        let action = membership.leave();
        assert!(matches!(action, LeaveAction::SendLeave { .. }));
        assert_eq!(membership.state, HostState::NonMember);
    }

    #[test]
    fn test_anomaly_bad_ttl() {
        let group = Ipv4Addr::new(239, 1, 1, 1);
        let raw = build_v2_report(group);
        let msg = IgmpMessage::parse(&raw).unwrap();
        let src = Ipv4Addr::new(192, 168, 1, 100);

        // Normal TTL=1 → no anomalies
        let anomalies = detect_anomalies(&msg, 1, true, src);
        assert!(anomalies.is_empty());

        // Bad TTL=64 → anomaly
        let anomalies = detect_anomalies(&msg, 64, true, src);
        assert!(anomalies.contains(&IgmpAnomaly::InvalidTtl(64)));
    }
}
```

---

## 18. YARA and Sigma Detection Rules

### YARA Rule: Malicious IGMP Packet Crafting

```yara
/*
 * YARA Rule: igmp_raw_socket_craft
 * Detects malware that constructs and sends raw IGMP packets.
 * Focus: IP_HDRINCL + raw socket + IGMP protocol byte (0x02).
 * Applies to: Windows and Linux binaries.
 */
rule igmp_raw_socket_craft {
    meta:
        description = "Detects binary constructing raw IGMP packets"
        author      = "ThreatAnalyst"
        reference   = "T1040, T1046"
        severity    = "medium"
        
    strings:
        /* IP_HDRINCL socket option (value 3 on Linux, 2 on Windows) */
        $ip_hdrincl_linux   = { 01 00 00 00 03 00 00 00 }  /* setsockopt args */
        $ip_hdrincl_win     = { 02 00 00 00 }

        /* IGMP protocol number = 2 (0x02) in IPPROTO position */
        $raw_igmp_socket    = { 02 00 00 00 03 00 00 00 }  /* AF_INET, SOCK_RAW, 2 */

        /* Router Alert option bytes: 94 04 00 00 */
        $router_alert       = { 94 04 00 00 }
        
        /* IGMP type bytes for message construction */
        $igmp_query_type    = { 11 64 }     /* Type=0x11, MaxResp=100 */
        $igmp_report_v2     = { 16 00 }     /* Type=0x16, MaxResp=0 */
        $igmp_leave         = { 17 00 }     /* Type=0x17, MaxResp=0 */
        $igmp_report_v3     = { 22 00 00 00 } /* Type=0x22, Reserved */

        /* ALL-HOSTS multicast address: E0 00 00 01 = 224.0.0.1 */
        $all_hosts_addr     = { E0 00 00 01 }
        
        /* ALL-ROUTERS multicast address: E0 00 00 02 = 224.0.0.2 */
        $all_routers_addr   = { E0 00 00 02 }
        
        /* sendto / WSASendTo function strings */
        $sendto_str         = "sendto" nocase ascii
        $wsasendto_str      = "WSASendTo" nocase wide

    condition:
        uint16(0) == 0x5A4D    /* PE file */
        and filesize < 10MB
        and (
            $router_alert and
            (
                ($igmp_query_type or $igmp_report_v2 or $igmp_leave or $igmp_report_v3)
                and ($all_hosts_addr or $all_routers_addr)
                and ($sendto_str or $wsasendto_str)
            )
        )
}

/*
 * YARA Rule: igmp_covert_channel
 * Detects potential IGMP-based covert channel behavior.
 * Looks for multicast group join/leave cycling indicative of data encoding.
 */
rule igmp_covert_channel_indicator {
    meta:
        description = "Detects patterns suggestive of IGMP group-address covert channel"
        author      = "ThreatAnalyst"
        reference   = "T1048.003"
        severity    = "high"
        
    strings:
        /* IP_ADD_MEMBERSHIP / IP_DROP_MEMBERSHIP setsockopt constants */
        /* Linux: IP_ADD_MEMBERSHIP = 35 = 0x23 */
        $add_membership_linux  = { 23 00 00 00 }
        $drop_membership_linux = { 24 00 00 00 }
        
        /* Windows: IP_ADD_MEMBERSHIP = 12 = 0x0C */
        $add_membership_win    = "IP_ADD_MEMBERSHIP" ascii nocase
        
        /* Patterns suggesting algorithmic address generation in 239.x.x.x range */
        /* 239 = 0xEF — admin-scoped multicast */
        $admin_scope_base      = { EF }
        
        /* Loop constructs near setsockopt calls suggest cycling through groups */
        $setsockopt_str        = "setsockopt" ascii nocase

    condition:
        uint16(0) == 0x5A4D
        and filesize < 5MB
        and $setsockopt_str
        and (
            ($add_membership_linux and $drop_membership_linux) or
            $add_membership_win
        )
        and #admin_scope_base > 20   /* Many references to 239.x addresses */
}

/*
 * YARA Rule: pcap_igmp_anomaly
 * Applied to PCAP files — detects anomalous IGMP packets.
 */
rule pcap_igmp_ttl_anomaly {
    meta:
        description = "PCAP contains IGMP packets with TTL > 1 (crafted/spoofed)"
        author      = "ThreatAnalyst"
        
    strings:
        /*
         * Match pattern in PCAP:
         * IP header with Protocol=0x02 (IGMP) and TTL > 0x01
         * A valid IGMP packet always has TTL=0x01.
         *
         * Ethernet (14) + IP TTL offset (8) = byte 22 from frame start.
         * We look for: TTL > 1, Protocol = 2
         *
         * Simplified: look for IP proto=2 with any TTL byte > 0x01
         * Pattern: XX 02 (TTL, Protocol) where XX > 01
         */
        
        /* TTL=64 (0x40) with IGMP protocol=2 */
        $igmp_ttl64  = { 40 02 }
        /* TTL=128 (0x80) with IGMP protocol=2 */
        $igmp_ttl128 = { 80 02 }
        /* TTL=255 (0xFF) with IGMP protocol=2 */
        $igmp_ttl255 = { FF 02 }
        
        /* PCAP file magic */
        $pcap_le     = { D4 C3 B2 A1 }
        $pcap_be     = { A1 B2 C3 D4 }
        $pcapng      = { 0A 0D 0D 0A }
        
    condition:
        ($pcap_le or $pcap_be or $pcapng) at 0
        and ($igmp_ttl64 or $igmp_ttl128 or $igmp_ttl255)
}
```

### Sigma Rules for IGMP Anomaly Detection

```yaml
---
# Sigma Rule: Anomalous IGMP Querier on Segment
# Detects a host (non-router) sending IGMP Query packets.
# Normal behavior: only routers send Queries.
title: Anomalous IGMP Query from Non-Router Host
id: 8f3a9c21-4d67-4b12-9e8a-1234567890ab
status: experimental
description: |
  Detects IGMP Membership Query (type 0x11) originating from a host that
  is not a known multicast router. This may indicate Querier spoofing aimed
  at taking control of IGMP query scheduling, potentially disrupting
  multicast group membership or enabling a covert timing channel.
author: ThreatAnalyst
date: 2024/01/15
tags:
  - attack.discovery
  - attack.t1046
  - attack.lateral_movement
  - attack.t1557
references:
  - https://attack.mitre.org/techniques/T1046/
  - https://datatracker.ietf.org/doc/html/rfc2236
logsource:
  category: network_traffic
  product: zeek
  service: conn
detection:
  selection:
    proto: 'igmp'
    igmp_type: 17     # 0x11 = Membership Query
  filter_known_routers:
    src_ip|cidr:
      - '10.0.0.0/8'    # Replace with actual router IP ranges
  timeframe: 60s
  condition: selection and not filter_known_routers
falsepositives:
  - IGMP Snooping Querier on a managed switch configured with host IP
  - Lab/test environments with non-standard router deployments
level: high
fields:
  - src_ip
  - dest_ip
  - igmp_type
  - igmp_group

---
# Sigma Rule: IGMP Leave without Prior Join
title: Spurious IGMP Leave Group
id: 2b7f1e45-8c3d-4a9f-b6e2-abcdef012345
status: experimental
description: |
  Detects an IGMP Leave Group message (type 0x17) from a host that has
  not previously been observed sending a Membership Report for the same
  group on this interface. Spurious Leaves can disrupt multicast delivery
  and may indicate a denial-of-service or reconnaissance attempt.
author: ThreatAnalyst
date: 2024/01/15
tags:
  - attack.impact
  - attack.t1499
logsource:
  category: network_traffic
  product: zeek
  service: igmp_custom  # Requires custom Zeek IGMP script
detection:
  leave_event:
    igmp_type: 23       # 0x17 = Leave Group
  join_history:
    igmp_type: 22       # 0x16 = Report v2
  condition: |
    leave_event and not
    (join_history with same src_ip and same igmp_group within 260s)
level: medium
falsepositives:
  - Host crash/restart with outstanding Leave messages from previous session
  - Asymmetric traffic capture (captures Leave but missed Join on another interface)

---
# Sigma Rule: IGMP Flood (Mass Joins from Single Host)
title: IGMP Group Membership Flood
id: 9d2e4a7f-1b5c-4d8e-a3f7-fedcba987654
status: experimental
description: |
  Detects a host sending more than 50 IGMP Membership Reports within 30
  seconds. This may indicate an IGMP flood attack aimed at exhausting
  router or switch multicast table memory (Ternary CAM exhaustion).
author: ThreatAnalyst
date: 2024/01/15
tags:
  - attack.impact
  - attack.t1499.001
logsource:
  category: network_traffic
  product: zeek
  service: conn
detection:
  selection:
    proto: igmp
    igmp_type:
      - 22    # IGMPv2 Report
      - 18    # IGMPv1 Report
      - 34    # IGMPv3 Report (0x22 = 34)
  condition: selection | count(igmp_group) by src_ip > 50
  timeframe: 30s
falsepositives:
  - Multicast-heavy applications joining many groups simultaneously at startup
  - IPTV set-top boxes with large channel count
level: high
fields:
  - src_ip
  - count

---
# Sigma Rule: IGMP Packet Without Router Alert
title: IGMP Packet Missing Router Alert IP Option
id: 7e3b9d15-2f4a-4c6e-8b1d-123456789012
status: experimental
description: |
  IGMPv2 and IGMPv3 packets MUST include the IP Router Alert option
  (RFC 2113). A packet lacking this option is either: (a) crafted by
  a non-compliant implementation, or (b) deliberately crafted to evade
  detection systems that filter on Router Alert.
author: ThreatAnalyst
date: 2024/01/15
tags:
  - attack.defense_evasion
logsource:
  category: network_traffic
  product: suricata
  service: eve
detection:
  selection:
    event_type: alert
    proto: 2      # IGMP
    ip_options|contains|all:
      - ''        # Absence: requires Suricata rule below
  condition: selection
level: medium

# Corresponding Suricata EVE rule:
# alert ip any any -> any 224.0.0.0/4 (
#   msg:"IGMP v2/v3 without Router Alert Option";
#   ip_proto:2;
#   byte_test:1,>,0,0,relative;   /* IGMP type is 0x16 or 0x17 or 0x22 */
#   ipopts:!rtralt;               /* No Router Alert option */
#   threshold:type limit,track by_src,count 1,seconds 60;
#   classtype:protocol-command-decode;
#   sid:9000001; rev:1;
# )
```

### Zeek Script for IGMP Analysis

```zeek
##! igmp_monitor.zeek
##! Logs IGMP events and generates notices for anomalies.
##! 
##! Deploy: zeek -r capture.pcap igmp_monitor.zeek
##! Or add to Zeek's local.zeek: @load igmp_monitor

module IGMP;

export {
    redef enum Log::ID += { LOG };
    redef enum Notice::Type += {
        IGMP_Anomalous_Querier,
        IGMP_Flood,
        IGMP_Leave_Without_Join,
        IGMP_Invalid_TTL,
    };

    type Info: record {
        ts:          time             &log;
        src_ip:      addr             &log;
        dst_ip:      addr             &log;
        igmp_type:   count            &log;
        type_name:   string           &log;
        group_addr:  addr             &log &optional;
        max_resp_ms: count            &log &optional;
        ttl:         count            &log;
        anomaly:     string           &log &optional;
    };
}

## Track join history per host: src_ip -> set of groups
global join_history: table[addr] of set[addr] &read_expire = 260sec;

## Count Reports per host in rolling window
global report_counts: table[addr] of count &read_expire = 30sec;

## Known router IPs — populate from asset management
const known_routers: set[addr] = {
    10.0.0.1,
    192.168.1.1,
    172.16.0.1,
} &redef;

event igmp_message(c: connection, is_orig: bool, msg_type: count,
                   max_resp_time: count, group_addr: addr) {
    local info: Info;
    info$ts         = network_time();
    info$src_ip     = c$id$orig_h;
    info$dst_ip     = c$id$resp_h;
    info$igmp_type  = msg_type;
    info$group_addr = group_addr;
    info$max_resp_ms = max_resp_time * 100;
    # TTL would come from IP header — placeholder
    info$ttl        = 1;

    switch(msg_type) {
        case 0x11:
            info$type_name = "MembershipQuery";
            # Query from non-router = anomaly
            if (c$id$orig_h !in known_routers) {
                info$anomaly = "Query_from_non_router";
                NOTICE([$note=IGMP_Anomalous_Querier,
                        $msg=fmt("IGMP Query from non-router %s",
                                  c$id$orig_h),
                        $src=c$id$orig_h]);
            }
            break;
        case 0x16:
            info$type_name = "ReportV2";
            # Track join
            if (c$id$orig_h !in join_history)
                join_history[c$id$orig_h] = set();
            add join_history[c$id$orig_h][group_addr];
            # Flood detection
            if (c$id$orig_h !in report_counts)
                report_counts[c$id$orig_h] = 0;
            ++report_counts[c$id$orig_h];
            if (report_counts[c$id$orig_h] > 50) {
                NOTICE([$note=IGMP_Flood,
                        $msg=fmt("IGMP flood from %s: >50 joins in 30s",
                                  c$id$orig_h),
                        $src=c$id$orig_h]);
            }
            break;
        case 0x17:
            info$type_name = "LeaveGroup";
            # Check for Leave without prior Join
            if (c$id$orig_h !in join_history ||
                group_addr !in join_history[c$id$orig_h]) {
                info$anomaly = "Leave_without_Join";
                NOTICE([$note=IGMP_Leave_Without_Join,
                        $msg=fmt("IGMP Leave from %s for %s with no prior Join",
                                  c$id$orig_h, group_addr),
                        $src=c$id$orig_h]);
            }
            # Remove from join history
            if (c$id$orig_h in join_history)
                delete join_history[c$id$orig_h][group_addr];
            break;
        case 0x22:
            info$type_name = "ReportV3";
            break;
        default:
            info$type_name = fmt("Unknown_0x%02x", msg_type);
            break;
    }

    Log::write(IGMP::LOG, info);
}
```

---

## 19. Wireshark Filters and Analysis Workflow

### Complete Analyst Workflow for IGMP Investigation

```
IGMP INVESTIGATION PLAYBOOK:

Step 1: Baseline — Characterize Normal Traffic
────────────────────────────────────────────────
Filter: igmp
Expected to see:
  - Periodic General Queries from router every ~125 seconds
  - Membership Reports from hosts (v2: 0x16, v3: 0x22)
  - Occasional Leave messages (0x17) when hosts disconnect
  - All packets with TTL=1

Step 2: Identify All Participants
────────────────────────────────────────────────
Filter: igmp.type == 0x11
  → All source IPs = routers (or querier spoofing)
  
Filter: igmp.type == 0x16 || igmp.type == 0x22
  → All source IPs = hosts joining groups
  → Group addresses = active multicast groups

Step 3: Build Group Membership Map
────────────────────────────────────────────────
Export to CSV via tshark:
  tshark -r cap.pcap -Y 'igmp' -T fields \
    -e frame.time_epoch \
    -e ip.src -e igmp.type -e igmp.maddr \
    -E header=y -E separator=, > igmp_events.csv

Step 4: Anomaly Detection Checks
────────────────────────────────────────────────
a) TTL violations:
   Filter: igmp && ip.ttl != 1
   
b) Missing Router Alert:
   Filter: igmp && !ip.opt.ra
   
c) Queries from non-routers:
   Filter: igmp.type == 0x11 && ip.src != <known_router_ips>
   
d) Spurious Leaves:
   Correlate Leave events with no prior Join in 260-second window
   
e) Group address analysis:
   Filter: igmp.maddr contains "239."
   → Legitimate admin scope
   Filter: igmp.maddr matches "224.0.0.[3-9]"  
   → Reserved range join by non-router = suspicious
   
f) Source-specific joins in non-SSM environments:
   Filter: igmp.type == 0x22
   → IGMPv3 presence — check if infrastructure supports it

Step 5: Timeline Reconstruction
────────────────────────────────────────────────
Follow a specific group's lifecycle:
  Filter: igmp.maddr == 239.1.1.1
  
Observe sequence:
  1. First Join (Report) → who joined first?
  2. Subsequent Joins → other hosts
  3. Queries → router health checks
  4. Report Suppression → which host responded?
  5. Leave → who left, when?
  6. Group-Specific Queries after Leave → router verification
  7. Final Leave (no Reports) → group removed from router table

Step 6: Export and Correlate with Other Protocols
────────────────────────────────────────────────
Correlate IGMP joins with UDP multicast traffic:
  - IGMP Join for group G at time T
  - Look for UDP packets to same group G after time T
  - Identify the source IPs of multicast data streams
  
Filter for correlated multicast data:
  ip.dst == 239.1.1.1 && udp
```

---

## 20. The Expert Mental Model

### How a Top 1% Analyst Thinks About IGMP

IGMP is not merely a "multicast management protocol" — it is the **control plane signal that governs group topology** at the network edge. An expert views IGMP through three simultaneous lenses:

**The architectural lens:** IGMP solves the fundamental problem of receiver-initiated group membership in a connectionless multicast fabric. Every message is a signal in a distributed state machine where routers hold authoritative group membership state and hosts hold subscription state, and both sides must agree through asynchronous message exchange with built-in reliability through timer-based retransmission. The protocol was designed for a world where multicast routers were expensive and scarce; the querier election mechanism reflects that assumption.

**The security lens:** IGMP operates with zero authentication on an implicitly-trusted local link model that is completely invalid in enterprise networks where workstations share broadcast domains with servers, IoT devices, and OT endpoints. Every field in an IGMP packet can be spoofed. The TTL=1 constraint is the only meaningful security boundary, and it only prevents off-link attacks. On-segment, an attacker can manipulate multicast topology silently — joining groups to receive traffic, sending false Leaves to disrupt delivery, sending false Queries to win the querier election and control query timing. IGMP snooping tables in switches are finite; flooding a switch with spurious Joins can exhaust ternary CAM memory and revert the switch to flooding behavior, effectively creating a network tap for multicast traffic.

**The intelligence lens:** In environments with legitimate multicast infrastructure (IPTV, financial market data feeds, OT process networks, video conferencing), passive IGMP monitoring reveals an extraordinary amount of intelligence: which endpoints are active, what services they consume, when they come online and go offline, and what the network topology looks like between routers. Volt Typhoon's documented preference for LOTL and passive intelligence gathering makes IGMP an attractive pre-compromise reconnaissance channel — silent, protocol-conformant, and rarely monitored by EDR or SIEM systems. When you see IGMP joins from workstations for groups that belong to your SCADA or ICS multicast domains, that is an anomaly that demands immediate investigation.

**The implementation lens (for reverse engineering):** When analyzing binaries suspected of multicast C2 or IGMP manipulation, look for: `setsockopt` calls with `IP_ADD_MEMBERSHIP` (0x23 on Linux) or `IP_HDRINCL` (3), raw socket creation with `SOCK_RAW` and protocol number 2, and the byte sequences `94 04 00 00` (Router Alert) or `E0 00 00` (224.x.x.x destination prefix). IGMPv3's Auxiliary Data field is essentially a free-form payload field that routers ignore — it is a ready-made covert channel requiring only one line of code to weaponize. Detection is straightforward: any non-zero `aux_data_len` in an IGMPv3 Group Record warrants immediate scrutiny.

**The definitive truth:** IGMP's power as both a protocol to understand and an attack surface to defend comes from its invisibility. Every network has it. Almost no security team monitors it. The analyst who understands IGMP deeply is operating in a detection space that most adversaries assume is empty — and that asymmetry is exactly where elite defenders live.

---

## Quick Reference Card

```
IGMP MESSAGE TYPE QUICK REFERENCE:
───────────────────────────────────────────────────────────────
0x11  Membership Query    Router→Hosts  "Who wants what groups?"
0x12  v1 Report           Host→Router   "I want this group (v1)"
0x16  v2 Report           Host→Group    "I want this group (v2)"  
0x17  Leave Group         Host→Routers  "I'm leaving this group"
0x22  v3 Report           Host→224.0.0.22 "State change (v3)"

DESTINATION ADDRESSES:
───────────────────────────────────────────────────────────────
224.0.0.1   General Query destination (All-Hosts)
224.0.0.2   Leave Group destination (All-Routers)
224.0.0.22  IGMPv3 Report destination (All-v3-Routers)
<group>     v2/v1 Report destination (the group itself)
<group>     Group-Specific Query destination

MANDATORY FIELDS:
───────────────────────────────────────────────────────────────
TTL:    Always 1 (never forward IGMP)
Option: Router Alert (94 04 00 00) in v2/v3
Proto:  IPv4 Protocol = 2

TIMER DEFAULTS:
───────────────────────────────────────────────────────────────
Query Interval:              125 seconds
Max Response Time:           10 seconds
Group Membership Interval:   260 seconds
Last Member Query Interval:  1 second
Last Member Query Count:     2
Max Leave Latency:           2 seconds (vs ~260s in v1)

ANOMALY INDICATORS:
───────────────────────────────────────────────────────────────
TTL != 1                     → Crafted/spoofed packet
No Router Alert              → Non-compliant or crafted (v2/v3)
Query from non-router        → Querier spoofing
>50 Joins from one host/30s  → Flood attack
Leave without prior Join     → Spurious Leave attack
Group 224.0.0.x from host    → Reserved range violation
Non-zero aux_data_len        → Potential covert channel (v3)
```

---

*End of IGMP Complete Technical Reference*

*Revision: 1.0 | Protocol: RFC 1112, RFC 2236, RFC 3376, RFC 4604 | MLD: RFC 2710, RFC 3810*