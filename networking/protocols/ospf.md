# OSPF — Open Shortest Path First: A Complete, In-Depth Reference

> *Everything you need to build a precise mental model of OSPF — from first principles through wire-level packet formats, algorithm internals, area design, failure handling, security, and real C/Rust implementations.*

---

## Table of Contents

1. [Why OSPF Exists — The Problem Space](#1-why-ospf-exists)
2. [OSPF at a Glance — Big Picture Mental Model](#2-ospf-at-a-glance)
3. [OSPF Standards and Versions](#3-ospf-standards-and-versions)
4. [Fundamental Concepts](#4-fundamental-concepts)
   - Router ID
   - Link-State vs Distance-Vector
   - Autonomous System
   - Cost Metric
5. [Neighbors and Adjacencies](#5-neighbors-and-adjacencies)
   - Hello Protocol
   - Neighbor State Machine (all 8 states)
   - DR/BDR Election
6. [OSPF Packet Types — Wire Format](#6-ospf-packet-types--wire-format)
   - Common OSPF Header
   - Hello (Type 1)
   - DBD (Type 2)
   - LSR (Type 3)
   - LSU (Type 4)
   - LSAck (Type 5)
7. [Link-State Advertisements (LSAs)](#7-link-state-advertisements-lsas)
   - LSA Header
   - Type 1 — Router LSA
   - Type 2 — Network LSA
   - Type 3 — Summary LSA
   - Type 4 — ASBR Summary LSA
   - Type 5 — AS External LSA
   - Type 7 — NSSA External LSA
   - Type 8/9/10/11 — Opaque LSAs
8. [The Link-State Database (LSDB)](#8-the-link-state-database-lsdb)
9. [Dijkstra's SPF Algorithm — Deep Dive](#9-dijkstras-spf-algorithm--deep-dive)
   - Conceptual walkthrough
   - Pseudocode
   - OSPF-specific SPF scheduling
10. [OSPF Areas — Architecture and Design](#10-ospf-areas--architecture-and-design)
    - Why Areas?
    - Backbone Area (Area 0)
    - Regular Areas
    - Stub Area
    - Totally Stubby Area
    - NSSA
    - Totally NSSA
    - Virtual Links
11. [Router Roles](#11-router-roles)
    - Internal Router
    - Backbone Router
    - ABR (Area Border Router)
    - ASBR (Autonomous System Boundary Router)
    - DR / BDR
12. [Route Types and Preference](#12-route-types-and-preference)
13. [Database Exchange Process — Full Walkthrough](#13-database-exchange-process--full-walkthrough)
14. [LSA Flooding and Reliability](#14-lsa-flooding-and-reliability)
15. [LSA Aging and MaxAge](#15-lsa-aging-and-maxage)
16. [OSPF Timers](#16-ospf-timers)
17. [OSPFv3 — IPv6 OSPF](#17-ospfv3--ipv6-ospf)
18. [OSPF Authentication](#18-ospf-authentication)
19. [Traffic Engineering and Opaque LSAs](#19-traffic-engineering-and-opaque-lsas)
20. [OSPF Convergence and Fast Reroute](#20-ospf-convergence-and-fast-reroute)
21. [OSPF Scalability and Tuning](#21-ospf-scalability-and-tuning)
22. [OSPF vs Other Protocols](#22-ospf-vs-other-protocols)
23. [C Implementation](#23-c-implementation)
24. [Rust Implementation](#24-rust-implementation)
25. [Troubleshooting and Debug Mindset](#25-troubleshooting-and-debug-mindset)
26. [Mental Model Summary](#26-mental-model-summary)

---

## 1. Why OSPF Exists

### The Routing Problem

In a network of N routers, each router must know *how to reach every destination*. The naive solution — static routes — breaks when:
- Links fail (no automatic reconvergence)
- The network grows (O(N²) management burden)
- Paths need to be optimal (static routes can't dynamically pick the best)

### Distance-Vector Limitations (RIP)

Before OSPF, RIP (Routing Information Protocol) was dominant. RIP uses **distance-vector**: each router only knows the distance to a destination and which neighbor to send packets through. It does NOT know the full topology.

Problems with distance-vector:
- **Count-to-infinity**: When a route fails, routers can loop, incrementing the hop count to 16 (infinity in RIP) before converging.
- **Slow convergence**: Triggered updates + hold-down timers can take minutes.
- **Hop count only**: No awareness of bandwidth — a 56 Kbps serial link counts the same as a 10 Gbps Ethernet link.
- **Scalability**: Routing table exchanges every 30 seconds flood the network.

### The Link-State Answer

OSPF solves this by giving **every router a complete, identical map of the network**. Each router independently runs Dijkstra's shortest path algorithm on this map to compute optimal routes. Because every router has the same map, there are no loops by construction.

---

## 2. OSPF at a Glance — Big Picture Mental Model

```
  ┌──────────────────────────────────────────────────────────────┐
  │                      OSPF BIG PICTURE                        │
  └──────────────────────────────────────────────────────────────┘

  Phase 1: DISCOVERY
  ┌──────────┐   Hello    ┌──────────┐
  │ Router A │──────────▶│ Router B │   Routers discover neighbors
  │          │◀──────────│          │   via multicast Hello packets
  └──────────┘   Hello   └──────────┘

  Phase 2: DATABASE EXCHANGE
  ┌──────────┐   DBD/LSR  ┌──────────┐
  │ Router A │◀──────────▶│ Router B │   Routers exchange LSA
  │   LSDB   │   LSU/Ack  │   LSDB   │   summaries then full LSAs
  └──────────┘            └──────────┘   until LSDBs are identical

  Phase 3: SPF COMPUTATION
  ┌──────────┐
  │ Router A │   Dijkstra's algorithm runs on the LSDB
  │  SPF Run │   to produce a shortest-path tree rooted
  │   Tree   │   at this router
  └──────────┘

  Phase 4: ROUTE INSTALLATION
  ┌──────────┐
  │ Router A │   Best routes from SPF tree are installed
  │ RIB/FIB  │   into the routing table and forwarding table
  └──────────┘

  Phase 5: ONGOING MAINTENANCE
  ┌──────────┐   Hello    ┌──────────┐
  │ Router A │──────────▶│ Router B │   Hellos maintain neighbor
  │          │   LSA      │          │   relationships; topology
  └──────────┘  Flood     └──────────┘   changes trigger LSA floods
                                         and SPF re-runs
```

**Core insight**: OSPF is a *distributed algorithm* for maintaining a *consistent, shared topology database* from which each node independently computes optimal paths. The key invariant is: **all routers in an area have identical LSDBs**.

---

## 3. OSPF Standards and Versions

| Version | RFC | IP Version | Key Notes |
|---------|-----|-----------|-----------|
| OSPFv1  | RFC 1131 (1989) | IPv4 | Historic, never deployed widely |
| OSPFv2  | RFC 2328 (1998, updated 2008) | IPv4 | Current standard for IPv4 |
| OSPFv3  | RFC 5340 (2008) | IPv6 (also IPv4 with addr-family ext.) | Redesigned for IPv6 |

**OSPFv2 (RFC 2328)** is what this guide primarily covers. OSPFv3 differences are covered in Section 17.

OSPF runs directly over **IP protocol number 89**. It is NOT TCP or UDP. It handles its own reliability through acknowledgment mechanisms.

---

## 4. Fundamental Concepts

### 4.1 Router ID (RID)

Every OSPF router has a unique 32-bit identifier called the **Router ID (RID)**, written in dotted-decimal notation (e.g., `10.0.0.1`), even in IPv6 networks.

**Selection order** (OSPFv2):
1. Manually configured `router-id` command (highest priority)
2. Highest IP address on any loopback interface
3. Highest IP address on any non-loopback interface

**Why the RID matters**: The RID identifies a router in all LSAs it originates. If the RID changes, OSPF restarts. Using a loopback or manual assignment prevents RID instability when interfaces go up/down.

```
  ┌─────────────────────────────────────────┐
  │           Router ID Selection           │
  │                                         │
  │  manual config?  YES ──▶ use that       │
  │       │ NO                              │
  │       ▼                                 │
  │  loopback up?    YES ──▶ highest loopback IP │
  │       │ NO                              │
  │       ▼                                 │
  │  any interface?  YES ──▶ highest interface IP│
  └─────────────────────────────────────────┘
```

### 4.2 Link-State vs Distance-Vector

**Distance-Vector** ("routing by rumor"):
- Each router tells neighbors its *distance* to all destinations
- Routers don't see the full topology
- Bellman-Ford algorithm
- Examples: RIP, IGRP, BGP (path-vector variant)

**Link-State** ("routing by map"):
- Each router floods its *local link information* to ALL routers
- Every router builds a complete topology map (the LSDB)
- Dijkstra's SPF algorithm
- Examples: OSPF, IS-IS

```
  DISTANCE-VECTOR                    LINK-STATE
  ─────────────                      ──────────
  
  A says to B: "I can               A floods to ALL: "A is
  reach X in 3 hops"                connected to B (cost 1)
                                     and C (cost 5)"
  B doesn't know WHY
  or what path A uses               B, C, D all have a map
                                     and run SPF independently
  Count-to-infinity
  possible on failure               No loops possible —
                                     consistent map = consistent
                                     independent computation
```

### 4.3 Autonomous System (AS)

An AS is a collection of routers under a single administrative domain running a common routing policy. OSPF is an **Interior Gateway Protocol (IGP)** — it routes *within* an AS. BGP routes *between* ASes.

### 4.4 OSPF Cost Metric

OSPF uses **cost** as its only metric. Cost is a dimensionless, administratively assigned value.

**Default formula** (Cisco reference):
```
  Cost = Reference Bandwidth / Interface Bandwidth
  
  Reference Bandwidth = 100 Mbps (default, configurable)
  
  Interface        Bandwidth    Cost
  ─────────────────────────────────
  Serial (56K)     56 Kbps      1785
  T1               1.544 Mbps   64
  Ethernet         10 Mbps      10
  FastEthernet     100 Mbps     1
  GigabitEthernet  1 Gbps       1  ← same as FE with default ref!
  10GigE           10 Gbps      1  ← same problem
```

**Problem**: With 100 Mbps reference bandwidth, anything ≥ 100 Mbps gets cost 1, making GigE indistinguishable from FastEthernet. **Best practice**: Set reference bandwidth to 100 Gbps or higher.

```
  auto-cost reference-bandwidth 100000  (100 Gbps in Mbps)
```

**Path cost** = sum of costs on all outgoing interfaces along the path. OSPF selects the path with the **lowest total cost**.

---

## 5. Neighbors and Adjacencies

### 5.1 The Hello Protocol

OSPF uses **Hello packets** to discover and maintain neighbor relationships. Hellos are sent to the multicast address **224.0.0.5** (AllSPFRouters) on most networks, or **224.0.0.6** (AllDRRouters) for DR/BDR communication.

**Hello fields that must match to form a neighbor relationship**:

| Field | Meaning | Must Match? |
|-------|---------|------------|
| Area ID | The area both interfaces belong to | YES |
| Hello Interval | How often Hellos are sent | YES |
| Dead Interval | How long until neighbor declared dead | YES |
| Authentication | Auth type and credentials | YES |
| Stub Area Flag | Whether area is stub | YES |
| Subnet/Mask | Network address and mask | YES (on broadcast networks) |
| MTU | (in DBD, not Hello, but affects exchange) | Should match |

**Fields that do NOT need to match**:
- Router ID (obviously — that's the unique identifier)
- DR/BDR (learned, not matched)
- Cost (local policy)

### 5.2 Neighbor State Machine — All 8 States

This is one of the most important concepts in OSPF. Each neighbor relationship progresses through up to 8 states:

```
  ┌────────────────────────────────────────────────────────────────────┐
  │                   OSPF NEIGHBOR STATE MACHINE                      │
  └────────────────────────────────────────────────────────────────────┘

  ┌─────────┐
  │  DOWN   │  No Hello received within Dead Interval
  └────┬────┘
       │ Hello received from neighbor
       ▼
  ┌─────────┐
  │  INIT   │  We received a Hello, but our RID not in
  └────┬────┘  neighbor's Hello neighbor list yet
       │ Our RID appears in neighbor's Hello
       ▼
  ┌─────────┐
  │ 2-WAY   │  Bidirectional communication established
  └────┬────┘  (DR/BDR election happens here)
       │ Decision to become adjacent (point-to-point,
       │ or we/they are DR/BDR on broadcast)
       ▼
  ┌─────────┐
  │ EXSTART │  Master/Slave negotiation via DBD packets
  └────┬────┘  (higher RID becomes Master)
       │ Initial DBD exchange complete
       ▼
  ┌─────────┐
  │EXCHANGE │  Full DBD packets exchanged (LSA headers)
  └────┬────┘
       │ DBD exchange done
       ▼
  ┌─────────┐
  │ LOADING │  Sending LSR for missing/stale LSAs
  └────┬────┘  Receiving LSU with full LSA content
       │ All LSAs received and acknowledged
       ▼
  ┌─────────┐
  │  FULL   │  Databases synchronized — full adjacency!
  └─────────┘  (routing can now happen)

  Special state:
  ┌─────────┐
  │ ATTEMPT │  Used only with NBMA networks and
  └─────────┘  statically configured neighbors
```

**Critical distinction — Neighbor vs Adjacent**:
- **Neighbor**: Any router you've exchanged Hellos with (2-WAY or above)
- **Adjacent**: A neighbor with whom you've fully synchronized LSDBs (FULL state)

On broadcast networks (Ethernet), not all neighbors become adjacent — only pairs involving the DR or BDR form full adjacencies. This reduces flooding overhead.

### 5.3 DR and BDR Election

**Why DR/BDR?** On a broadcast network with N routers, full mesh adjacencies = N(N-1)/2 adjacencies, and each topology change floods N(N-1) times. This is O(N²) — catastrophic at scale.

**Solution**: Elect a **Designated Router (DR)** and **Backup DR (BDR)**. All other routers (DROther) only form full adjacencies with DR and BDR.

```
  WITHOUT DR/BDR (5 routers, full mesh):
  
  R1 ──── R2
  │ ╲   ╱ │
  │  ╲ ╱  │   10 adjacencies
  │   X   │   Each LSA floods 10 times
  │  ╱ ╲  │
  │ ╱   ╲ │
  R3 ──── R4
       │
      R5
  
  WITH DR/BDR (R1=DR, R2=BDR):
  
      R1(DR)
     ╱|╲
    ╱ | ╲
  R3  R4  R5     DROthers (R3,R4,R5) form adjacency
    ╲ | ╱        ONLY with DR and BDR
     ╲|╱
      R2(BDR)    4 adjacencies instead of 10
                 LSA sent to 224.0.0.6 (DR/BDR)
                 DR re-floods to 224.0.0.5
```

**Election algorithm**:

1. Router with highest **OSPF Priority** wins DR (default priority = 1, range 0-255)
2. Tie broken by highest **Router ID**
3. Priority 0 = ineligible for DR/BDR
4. **Non-preemptive**: Once elected, DR/BDR keep their role until they go down, even if a higher-priority router appears. This prevents unnecessary reconvergence.

```
  ELECTION PROCESS:

  Wait for Dead Interval (or all neighbors have declared their
  DR/BDR in Hello packets)
  
  Step 1: Collect all routers with Priority > 0 and not
          already claiming to be DR
  Step 2: Among those, elect BDR = highest priority,
          break tie with highest RID
  Step 3: Among routers claiming to be DR, elect DR =
          highest priority, break tie with highest RID
  Step 4: If no routers claim DR, BDR becomes DR,
          new BDR election runs
```

**DR/BDR on different network types**:

| Network Type | DR/BDR? | Hellos | Notes |
|-------------|---------|--------|-------|
| Broadcast (Ethernet) | YES | Multicast | Default |
| Point-to-Point | NO | Multicast | Always full adjacency |
| NBMA (Frame Relay) | YES | Unicast | Manual neighbor config |
| Point-to-Multipoint | NO | Multicast | Sub-interfaces |
| Loopback | N/A | N/A | Advertised as /32 |

---

## 6. OSPF Packet Types — Wire Format

All OSPF packets share a common header, then have type-specific bodies.

### 6.1 Common OSPF Header (24 bytes)

```
   0                   1                   2                   3
   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |   Version #   |     Type      |         Packet Length         |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          Router ID                            |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                           Area ID                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |           Checksum            |   AuType      |               |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Authentication                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Authentication                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  
  Version   : 2 (OSPFv2) or 3 (OSPFv3)
  Type      : 1=Hello, 2=DBD, 3=LSR, 4=LSU, 5=LSAck
  Router ID : RID of originating router (4 bytes, dotted-decimal)
  Area ID   : Area this packet belongs to (4 bytes)
  Checksum  : Standard IP checksum over entire OSPF packet
              (not computed over Auth fields in some auth modes)
  AuType    : 0=None, 1=Simple Password, 2=MD5 Cryptographic
  Auth      : 8 bytes, meaning depends on AuType
```

### 6.2 Hello Packet (Type 1)

```
  OSPF COMMON HEADER (24 bytes)
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                        Network Mask                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |         HelloInterval         |    Options    | Rtr Pri       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     RouterDeadInterval                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                      Designated Router                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                   Backup Designated Router                    |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          Neighbor 1                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          Neighbor 2                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                            ...                                |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  Network Mask      : Subnet mask of sending interface
  HelloInterval     : Seconds between Hellos (must match)
  Options           : Capability bits (E=external routing, N=NSSA,
                      DC=demand circuits, L=LLS, O=opaque LSAs)
  Router Priority   : DR/BDR election priority
  RouterDeadInterval: Seconds until neighbor declared dead
  Designated Router : IP of DR on this segment (0 if none)
  Backup DR         : IP of BDR on this segment (0 if none)
  Neighbor list     : RIDs of all routers this router has
                      heard from (enables 2-WAY detection)
```

**Options byte breakdown**:
```
  Bit 7 (DN): Down bit for VPN/super-backbone
  Bit 6 (O) : Opaque LSA capable
  Bit 5 (DC): Demand Circuit capable
  Bit 4 (L) : LLS data block present
  Bit 3 (N/P): NSSA capable / P-bit (propagate NSSA external)
  Bit 2 (MC): Multicast routing
  Bit 1 (E) : External routing capable (0 in stub areas)
  Bit 0 (MT): Multi-topology
```

### 6.3 Database Description (DBD) Packet — Type 2

```
  OSPF COMMON HEADER (24 bytes)
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |         Interface MTU         |    Options    |0|0|0|0|0|I|M|MS
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     DD sequence number                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  |                      LSA Header 1                             |
  |                         (20 bytes)                            |
  |                                                               |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  |                      LSA Header 2                             |
  ...

  Interface MTU : MTU of sending interface (must match or exchange fails)
  I (Init)      : 1 = this is the first DBD packet in exchange
  M (More)      : 1 = more DBD packets to follow
  MS (Master)   : 1 = this router is Master in exchange
  DD seq number : Sequence number for reliable delivery
  LSA Headers   : Summaries of LSAs in LSDB (just headers, no content)
```

**Master/Slave**: Higher RID = Master. Master controls the sequence number. Slave only sends DBD in response to Master's DBD. This creates a reliable, ordered exchange.

### 6.4 Link State Request (LSR) — Type 3

```
  OSPF COMMON HEADER (24 bytes)
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          LS type                              |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Link State ID                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     Advertising Router                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  (repeat for each LSA requested)                              |
  ...

  This packet says: "Give me these specific LSAs"
  The triple (LS type, Link State ID, Advertising Router) 
  uniquely identifies each LSA.
```

### 6.5 Link State Update (LSU) — Type 4

```
  OSPF COMMON HEADER (24 bytes)
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       # advertisements                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  |                         LSA 1                                 |
  |                    (header + body)                            |
  |                                                               |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                         LSA 2                                 |
  ...

  LSUs carry complete LSAs (headers + bodies).
  Used both for responding to LSRs AND for flooding new LSAs.
```

### 6.6 Link State Acknowledgment (LSAck) — Type 5

```
  OSPF COMMON HEADER (24 bytes)
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  |                      LSA Header 1                             |
  |                         (20 bytes)                            |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                      LSA Header 2                             |
  ...

  Acknowledges received LSAs by echoing their headers.
  Can batch-acknowledge multiple LSAs in one packet.
```

**Two acknowledgment modes**:
- **Direct**: Unicast LSAck sent immediately to the sender
- **Delayed**: LSAck collected and sent as multicast (to 224.0.0.5 or 224.0.0.6) within a short window to batch ACKs

---

## 7. Link-State Advertisements (LSAs)

LSAs are the data units that routers flood to share topology information. Every LSA has a **20-byte common header** followed by type-specific content.

### 7.1 LSA Common Header (20 bytes)

```
   0                   1                   2                   3
   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |            LS age             |    Options    |    LS type     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                        Link State ID                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     Advertising Router                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     LS sequence number                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |         LS checksum           |             length            |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  LS age           : Seconds since LSA originated (max 3600 = MaxAge)
  Options          : Same options byte as Hello
  LS type          : 1-11, determines LSA content
  Link State ID    : Meaning depends on type (see per-type below)
  Advertising Router: RID of router that created this LSA
  LS sequence number: 32-bit signed, starts at 0x80000001,
                      increments each re-origination
                      Larger = newer; wraps around
  LS checksum      : Fletcher checksum (NOT over LS age field)
  length           : Total LSA length including header
```

**LSA uniqueness**: The triple **(LS type, Link State ID, Advertising Router)** uniquely identifies an LSA instance. **LS sequence number** determines which instance is newer.

**Newer LSA detection** (in order of precedence):
1. Higher sequence number wins
2. If equal sequence numbers: higher checksum wins
3. If equal checksums: lower age wins (fresher)
4. If one is MaxAge (3600): MaxAge version wins (forces removal)

### 7.2 Type 1 — Router LSA

**Flooded**: Within originating area only  
**Link State ID**: Router's own RID  
**Originator**: Every router originates one per area it belongs to

```
  ROUTER LSA BODY:
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |    0    |V|E|B|        0      |       # links                 |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          Link ID                              |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                         Link Data                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |     Type      |     # TOS     |            metric             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  (repeat for additional TOS, then repeat entire block per link)|
  ...

  V bit: Virtual link endpoint
  E bit: ASBR (AS Boundary Router)
  B bit: ABR (Area Border Router)
```

**Four link types in Router LSA**:

```
  Link Type  | Link ID            | Link Data          | Meaning
  ──────────────────────────────────────────────────────────────────
  1 (p2p)    | Neighbor's RID     | Local interface IP | Point-to-point link
  2 (transit)| DR's interface IP  | Local interface IP | Broadcast/NBMA segment
  3 (stub)   | Network IP         | Subnet mask        | Stub network (no OSPF neighbor)
  4 (virtual)| Neighbor's RID     | Local interface IP | Virtual link
```

**Example — Router LSA for a router with 3 interfaces**:
```
  Router 10.0.0.1 has:
  - Ethernet0/0: 192.168.1.1/24, connected to segment with DR=192.168.1.2
  - Serial0/0: 10.1.1.1/30, point-to-point to 10.1.1.2 (RID 10.0.0.2)
  - Loopback0: 1.1.1.1/32

  Router LSA contains:
  Link 1: Type=2 (transit), LinkID=192.168.1.2 (DR's IP), Data=192.168.1.1, Cost=1
  Link 2: Type=1 (p2p),     LinkID=10.0.0.2 (neighbor RID), Data=10.1.1.1, Cost=64
  Link 3: Type=3 (stub),    LinkID=1.1.1.1, Data=255.255.255.255, Cost=0
```

### 7.3 Type 2 — Network LSA

**Flooded**: Within originating area only  
**Link State ID**: DR's interface IP on the segment  
**Originator**: DR only (one per broadcast/NBMA segment)  

The Network LSA represents the broadcast segment itself as a node in the SPF graph.

```
  NETWORK LSA BODY:
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                         Network Mask                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Attached Router 1 (RID)                 |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Attached Router 2 (RID)                 |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                            ...                                |
  
  Lists ALL routers (including DR itself) on the segment.
  SPF algorithm treats this as a pseudo-node with cost 0
  to all attached routers.
```

### 7.4 Type 3 — Summary LSA (ABR-originated)

**Flooded**: Into an area from another area (inter-area)  
**Link State ID**: Destination network address  
**Originator**: ABR

ABRs originate Type 3 LSAs to advertise networks from one area into another. They do NOT simply flood Type 1/2 LSAs across area boundaries — they re-originate as Type 3.

```
  TYPE 3 LSA BODY:
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                         Network Mask                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |    0          |                  metric                       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  (TOS/metric pairs, mostly unused in modern OSPF)             |
  ...
```

**Critical**: The metric in the Type 3 LSA = cost from the ABR to the destination. Receiving routers add their own cost to reach the ABR.

### 7.5 Type 4 — ASBR Summary LSA

**Flooded**: Throughout OSPF domain except originating area  
**Link State ID**: RID of the ASBR  
**Originator**: ABR  

Type 4 LSAs tell routers in other areas *how to reach the ASBR* that originates external routes. Without Type 4, routers in other areas wouldn't know the cost to reach the ASBR.

```
  TYPE 4 LSA BODY: (same format as Type 3)
  The "network" being advertised IS the ASBR's RID,
  and the metric is the ABR's cost to reach the ASBR.
```

### 7.6 Type 5 — AS External LSA

**Flooded**: Throughout entire OSPF domain (NOT into stub areas)  
**Link State ID**: External destination network  
**Originator**: ASBR  

Type 5 LSAs carry routes from outside the OSPF domain (redistributed from BGP, static, RIP, etc.).

```
  TYPE 5 LSA BODY:
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                         Network Mask                          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |E|    0        |                  metric                       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |               Forwarding Address (optional)                   |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    External Route Tag                         |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  E bit: 0 = Type 1 external (metric added to OSPF cost)
         1 = Type 2 external (metric used as-is, OSPF cost ignored)
  Forwarding Address: If non-zero, forward to this IP instead of ASBR
  External Route Tag: 32-bit tag for policy (BGP community use)
```

**External route metric types**:

```
  Type 1 (E1): Total cost = OSPF cost to ASBR + external metric
               Comparable with internal routes
               Preferred when you want OSPF to influence path selection

  Type 2 (E2): Total cost = external metric only (OSPF cost ignored)
               All routers see the same metric to this external route
               Preferred when external metric is authoritative (BGP MED)

  E1 preferred over E2 when tied on external metric.
```

**Forwarding Address**: When non-zero, packets to the external destination should be forwarded to this address, NOT to the ASBR. This is used when the ASBR learned the route from a protocol whose next-hop is accessible via OSPF without going through the ASBR itself.

### 7.7 Type 7 — NSSA External LSA

**Flooded**: Within NSSA area only  
**Converted to Type 5**: By ABR when leaving the NSSA  

NSSAs (Not-So-Stubby Areas) can import external routes but don't receive Type 5 floods. ASBRs inside an NSSA originate Type 7 LSAs. The ABR converts them to Type 5 when advertising to the rest of the domain.

The P-bit (propagate) in the Type 7 header controls whether the ABR converts the Type 7 to Type 5.

### 7.8 Opaque LSAs — Types 9, 10, 11

Opaque LSAs are extension containers for OSPF. They carry arbitrary application-specific data using OSPF's flooding infrastructure.

| Type | Flooding Scope | Link State ID Format | Usage |
|------|---------------|---------------------|-------|
| 9 | Link-local (not flooded beyond interface) | App-specific | GRACE LSA (hitless restart) |
| 10 | Area-local | App-specific | Traffic Engineering (OSPF-TE), LDP synchronization |
| 11 | AS-wide | App-specific | Rare, router capabilities |

**Type 10 (Area-scope Opaque) for Traffic Engineering**:  
The OSPF-TE extension (RFC 3630) uses Type 10 LSAs to flood:
- Maximum bandwidth
- Maximum reservable bandwidth
- Unreserved bandwidth (per TE class)
- TE metric (separate from routing metric)
- Link color/affinities

This allows MPLS-TE path computation (CSPF) to account for bandwidth constraints.

---

## 8. The Link-State Database (LSDB)

### Structure

The LSDB is a database of all LSAs known to the router, indexed by the LSA identity triple:

```
  LSDB Index:
  ┌─────────────────────────────────────────────────────┐
  │  Key: (LS Type, Link State ID, Advertising Router)  │
  │  Value: Complete LSA (header + body)                 │
  └─────────────────────────────────────────────────────┘

  Example LSDB entries for a 3-router, single-area network:
  
  (1, 1.1.1.1, 1.1.1.1) → Router LSA from R1
  (1, 2.2.2.2, 2.2.2.2) → Router LSA from R2
  (1, 3.3.3.3, 3.3.3.3) → Router LSA from R3
  (2, 192.168.1.2, 2.2.2.2) → Network LSA for Eth segment (DR=R2)
```

### Per-Area Databases

Each OSPF area has its own LSDB. An ABR maintains **separate LSDBs per area it belongs to**. Types 1 and 2 are area-scoped. Types 3, 4, 5 may exist in multiple areas' LSDBs.

### LSDB Consistency Guarantee

**Every router in the same area must have an identical LSDB.** This is enforced by:
1. Reliable flooding (LSAck)
2. Retransmission timers
3. Sequence number tracking
4. Periodic LSA refresh (every 1800 seconds, half of MaxAge)

---

## 9. Dijkstra's SPF Algorithm — Deep Dive

### 9.1 Graph Model

OSPF builds a directed weighted graph from the LSDB:

```
  Nodes (vertices):
  - Each router (from Router LSAs)
  - Each transit network (from Network LSAs, as a pseudo-node)
  
  Edges (directed arcs):
  - Router → Transit network: Router LSA Type-2 link, cost = link cost
  - Transit network → Router: Network LSA, cost = 0 (free to reach any router on segment)
  - Router → Router: Router LSA Type-1 link (p2p), cost = link cost
  - Router → Stub network: Router LSA Type-3 link, cost = link cost
  
  The graph is DIRECTED: cost from A→B may differ from B→A
  (asymmetric link costs are valid but can cause suboptimal routing)
```

**Example topology graph**:
```
  Routers: R1(RID=1.1.1.1), R2(RID=2.2.2.2), R3(RID=3.3.3.3)
  Ethernet segment (DR=R2): Net-A = 192.168.1.0/24
  P2P link R2-R3: cost 10

        cost=1          cost=10
  R1 ──────── [Net-A] ──────── R2 ──────── R3
               │                     cost=10
               │ cost=0 to attached
               │ routers
               └── R1, R2 attached

  SPF tree rooted at R1:
  R1 (cost 0)
  └── Net-A (cost 1)
      ├── R2 (cost 1+0 = 1)    [zero cost from pseudo-node to router]
      │   └── R3 (cost 1+10 = 11)
      └── R1 already visited
```

### 9.2 SPF Algorithm — Pseudocode

```
  SPF (LSDB, root_router):
  
  CANDIDATE = priority queue (min-heap by cost)
  SHORTEST  = map: node → (cost, next_hop)
  
  1. Insert root into CANDIDATE with cost 0, next_hop = self
  
  2. LOOP while CANDIDATE not empty:
     a. Extract node N with minimum cost C from CANDIDATE
     b. If N already in SHORTEST, skip (already found optimal path)
     c. Add N to SHORTEST with cost C
  
     d. For each link L in N's LSA:
        - Determine neighbor node M = L.link_id or pseudo-node
        - Link cost = L.metric (or 0 if transit network→router)
        - New cost = C + link cost
        
        - If M not in SHORTEST:
            - If M already in CANDIDATE:
                - If new cost < current cost in CANDIDATE:
                    - Update CANDIDATE entry (decrease-key)
            - Else:
                - Insert M into CANDIDATE with new cost
  
  3. SHORTEST now contains optimal cost to every reachable node
  
  4. Build routing table:
     For each stub network in Router LSAs:
       - Find the router that owns it in SHORTEST
       - Route cost = SHORTEST[router].cost + stub cost
       - Next hop = SHORTEST[router].next_hop
```

**Next-hop calculation subtlety**:
When building the SPF tree, the "next hop" for directly attached neighbors is their interface IP (from the Link Data field in Router LSA), NOT their RID. For nodes reached transitively, the next hop is inherited from the first hop.

### 9.3 OSPF SPF Scheduling

SPF is computationally expensive. OSPF uses **SPF throttling** to avoid thrashing during instability:

```
  SPF Throttle Parameters:
  
  spf-start  : Initial delay after topology change before SPF runs
                (e.g., 50ms — allows LSA bundling)
  spf-hold   : Hold time after SPF; next SPF can't run until hold expires
                (doubles with each consecutive run, up to max)
  spf-max    : Maximum hold time
  
  Timeline during instability:
  
  t=0ms    : LSA received (topology change)
  t=50ms   : SPF runs #1
  t=200ms  : Hold = 200ms; if another change arrives:
  t=400ms  : SPF runs #2
  t=800ms  : Hold = 800ms; next SPF no earlier than t=1600ms
  
  This exponential back-off prevents CPU overload during flapping links.
```

**Partial SPF (iSPF)**: RFC 5715 describes incremental SPF — only recompute affected subtrees rather than full SPF. Reduces CPU for large networks.

**PRC (Partial Route Calculation)**: For leaf changes (stub networks appearing/disappearing without topology change), run only PRC instead of full SPF. Much faster.

---

## 10. OSPF Areas — Architecture and Design

### 10.1 Why Areas?

In a flat OSPF network with 1000 routers:
- Every router stores 1000 Router LSAs + potentially thousands of Network LSAs
- Every topology change triggers SPF on all 1000 routers
- LSA flooding affects the entire network

Areas solve this by **partitioning the network**:
- Each area has its own LSDB (only Type 1/2 LSAs)
- SPF runs are area-local
- ABRs summarize inter-area routes as Type 3 LSAs (much smaller than the full topology)

```
  ┌────────────────────────────────────────────────────────────────┐
  │                    OSPF AREA HIERARCHY                         │
  │                                                                │
  │     Area 1          Area 0 (Backbone)        Area 2           │
  │  ┌─────────┐       ┌─────────────────┐     ┌──────────┐       │
  │  │ R1──R2  │──ABR1─│ R5──R6──R7      │─ABR2─│ R9──R10 │       │
  │  │ │   │  │       │      │           │     │ │        │       │
  │  │ R3──R4  │       │      R8          │     │ R11─R12 │       │
  │  └─────────┘       └─────────────────┘     └──────────┘       │
  │                                                                │
  │  Type 1/2 LSAs      Type 1/2 LSAs           Type 1/2 LSAs     │
  │  stay in Area 1     stay in Area 0          stay in Area 2    │
  │                     Type 3 LSAs cross area boundaries         │
  └────────────────────────────────────────────────────────────────┘
```

### 10.2 Backbone Area (Area 0)

**All areas must connect to Area 0.** Area 0 is the transit area — all inter-area traffic must pass through it. This prevents routing loops in a two-level hierarchy.

**Why must all areas connect to Area 0?**  
If Area 1 and Area 2 both connect to Area 3 (not Area 0), Area 3 ABRs would receive Type 3 LSAs from both areas and might create sub-optimal or looped paths. The Area 0 requirement enforces a hub-and-spoke topology at the area level, making the inter-area routing loop-free by design.

### 10.3 Stub Area

In a stub area:
- **Type 5 LSAs (external) NOT allowed** (no external routes flooded into area)
- Instead, ABR injects a **default route** (Type 3 LSA for 0.0.0.0/0) into the stub area
- Routers in stub area use the default route to reach external destinations
- **Type 4 LSAs also suppressed** (no ASBRs inside stub area)

```
  Normal Area:
  ABR floods Type 3 + Type 5 into area → large LSDB

  Stub Area:
  ABR floods Type 3 (intra-domain summaries) + default route only
  → smaller LSDB, less SPF computation
  
  Routers in stub area: "I don't know external routes,
  just send unknown destinations to ABR via default"

  Configuration requirement: ALL routers in a stub area must
  be configured as stub (enforced via Hello Options E-bit)
```

### 10.4 Totally Stubby Area (Cisco Proprietary Extension)

More aggressive than stub:
- Type 5 LSAs blocked (like stub)
- **Type 3 LSAs also blocked** (inter-area summaries)
- Only Type 1, Type 2, and ONE Type 3 (the default route) exist
- Smallest possible LSDB

**When to use**: Hub-and-spoke topologies where stub areas have only one path to the backbone — they need no knowledge of other areas or external routes.

### 10.5 NSSA (Not-So-Stubby Area) — RFC 3101

The problem: What if a stub area has an ASBR (redistribution point) but you still want stub benefits?

NSSA solution:
- External routes in the NSSA are carried as **Type 7 LSAs** (not Type 5)
- Type 7 LSAs are flooded only within the NSSA
- Type 5 LSAs from outside are NOT flooded into NSSA (stub behavior)
- ABR converts selected Type 7 LSAs to Type 5 LSAs for the rest of the domain

```
  NSSA Topology:

  Internet ──── ASBR_outside                         ASBR_inside ──── Legacy_Network
                     │                                    │
                  [Area 0]                            [NSSA Area 2]
                     │                                    │
                   ABR ──────────────────────────────── ABR
                   
  ASBR_inside originates Type 7 LSAs in NSSA Area 2
  ABR converts Type 7 → Type 5 and floods into Area 0
  Type 5 from ASBR_outside does NOT enter NSSA Area 2
  ABR injects a Type 3 default route into NSSA instead
```

### 10.6 Totally NSSA

NSSA + totally stubby: Block Type 3 AND Type 5; allow Type 7 for local external injection; ABR generates only one Type 3 (default).

### 10.7 Virtual Links

**Problem**: Area 0 connectivity requirement is sometimes architecturally inconvenient. What if an area doesn't physically connect to Area 0?

**Virtual Link**: A logical link through a transit area that extends Area 0 connectivity.

```
  Physical topology:
  Area 0 ──── ABR1 ──── Area 2 ──── ABR2 ──── Area 3
  
  Area 3 has no direct connection to Area 0.
  
  Virtual link: configured between ABR1 and ABR2,
  running THROUGH Area 2 (transit area).
  Area 3 is now logically connected to Area 0.
  
  ┌──────────────────────────────────────────────────┐
  │  Area 0  │         Area 2         │   Area 3     │
  │          │                        │              │
  │  [R1]──[ABR1]════════════════[ABR2]──[R4]        │
  │          │  ←virtual link→   │                   │
  │          └──── Area 2 ────────┘                  │
  └──────────────────────────────────────────────────┘

  Virtual link restrictions:
  - Transit area CANNOT be a stub area
  - Virtual links are a design workaround, not preferred
  - Use them temporarily; redesign the area layout when possible
```

**Virtual link parameters**: Virtual links share the same Hello/Dead timers as normal links. The virtual link endpoint router must have OSPF adjacency through the transit area.

---

## 11. Router Roles

### Internal Router
All interfaces in the same single area. Maintains one area's LSDB only. Simplest role.

### Backbone Router
Has at least one interface in Area 0. May also be an internal or ABR.

### ABR (Area Border Router)
Connected to **two or more areas**, including Area 0.

ABR responsibilities:
1. Maintains **separate LSDB per area**
2. Runs **separate SPF per area**
3. Originates **Type 3 LSAs** to advertise routes between areas
4. Can perform **route summarization** (aggregate multiple Type 3 into one)
5. Originates **Type 4 LSAs** to advertise ASBRs from its areas

**ABR summarization** — critical for scalability:
```
  Without summarization (ABR floods every subnet):
  Area 1 has: 10.1.1.0/24, 10.1.2.0/24, ..., 10.1.100.0/24
  → 100 Type 3 LSAs in Area 0 LSDB
  
  With summarization:
  ABR aggregates to: 10.1.0.0/16
  → 1 Type 3 LSA in Area 0 LSDB
  
  Configuration: area 1 range 10.1.0.0 255.255.0.0
  
  Benefit: Hides internal instability — individual prefix flaps
  don't trigger SPF in other areas
```

### ASBR (AS Boundary Router)
Redistributes routes from external protocols (BGP, static, RIP, EIGRP) into OSPF as Type 5 LSAs. Sets the E bit in its Router LSA.

### DR / BDR
Not a router "role" per se — it's an **interface-level election**. A router can be DR on one segment and DROther on another segment simultaneously.

---

## 12. Route Types and Preference

OSPF routes have a strict preference hierarchy:

```
  Priority (highest to lowest):
  
  1. Intra-area routes (O)       ← Type 1/2 LSAs, SPF-computed
     "Best — I have the full topology of this area"
  
  2. Inter-area routes (O IA)    ← Type 3 LSAs, distance-vector-like
     "Good — ABR summarized this from another area"
  
  3. External Type 1 (O E1)      ← Type 5/7, cumulative cost
     "External but OSPF cost included in comparison"
  
  4. External Type 2 (O E2)      ← Type 5/7, flat external metric
     "External, OSPF cost irrelevant to selection"

  Within same type: lower metric wins
  Across types: higher priority wins regardless of metric

  Example: O (intra-area, cost 1000) ALWAYS beats O IA (cost 1)
```

---

## 13. Database Exchange Process — Full Walkthrough

This is the complete step-by-step process of two routers forming a full adjacency on a broadcast network. Assume R1 and R2, with R2 elected as DR.

```
  STEP 1: DOWN → INIT (Hello Reception)
  ─────────────────────────────────────
  R1 sends Hello to 224.0.0.5 every HelloInterval
  R2 receives Hello; adds R1 to its neighbor table as INIT
  R2 sends Hello; R1's neighbor list in R2's Hello is empty initially

  STEP 2: INIT → 2-WAY (Bidirectional)
  ─────────────────────────────────────
  R2 sends Hello with R1's RID in neighbor list
  R1 sees its own RID in R2's Hello → transitions to 2-WAY
  R1 sends Hello with R2's RID → R2 transitions to 2-WAY
  
  [DR/BDR election runs if needed]
  
  R2 is DR; R1 is DROther. Decision: R1 forms adjacency with R2 (DR).

  STEP 3: 2-WAY → EXSTART (Master/Slave Negotiation)
  ────────────────────────────────────────────────────
  Both routers send DBD with:
    I=1 (Init), M=1 (More), MS=1 (claiming master)
    DD sequence number = some random value
  
  R2 has higher RID (2.2.2.2 > 1.1.1.1) → R2 becomes Master
  R1 becomes Slave; adopts R2's sequence number

  STEP 4: EXSTART → EXCHANGE (LSA Header Exchange)
  ──────────────────────────────────────────────────
  R2 (Master) sends DBD with LSA headers from its LSDB
    DD seq = N, M=1 (more to come)
  R1 (Slave) responds with DBD (DD seq = N, its own LSA headers)
  
  R2 sends next DBD (DD seq = N+1) to acknowledge Slave's response
  ... continues until all headers exchanged
  
  Final DBD from Master: M=0 (no more)
  Transition to LOADING

  STEP 5: EXCHANGE → LOADING (Request Missing LSAs)
  ───────────────────────────────────────────────────
  R1 examines received LSA headers vs its own LSDB:
  - LSAs R1 has that are newer → R1 will send in its DBD (already done)
  - LSAs R2 has that R1 lacks or R1 has older copies → send LSR

  R1 sends LSR to R2: "Please send me LSAs X, Y, Z"
  R2 responds with LSU containing full LSAs X, Y, Z
  R1 sends LSAck
  
  R2 similarly sends LSR for anything it needs
  R1 responds with LSU
  R2 sends LSAck

  STEP 6: LOADING → FULL
  ───────────────────────
  When both sides have no outstanding LSRs, transition to FULL.
  LSDBs are now synchronized.
  SPF re-runs on both routers.

  PACKET FLOW DIAGRAM:
  
  R1 (Slave, lower RID)            R2 (Master, higher RID, DR)
  ─────────────────────            ───────────────────────────
       Hello ─────────────────────────────────────────▶
                         ◀──────────────────────── Hello
                    [2-WAY established, EXSTART begins]
       DBD(I=1,M=1,MS=1,seq=100) ──────────────────▶ [R2 ignores, higher RID wins]
                         ◀──────────── DBD(I=1,M=1,MS=1,seq=999) [R2 claims Master]
       DBD(I=0,M=1,MS=0,seq=999, headers...) ──────▶ [Slave acks with seq=999]
                         ◀──── DBD(I=0,M=1,MS=1,seq=1000, headers...)
       DBD(I=0,M=1,MS=0,seq=1000, headers...) ─────▶
                         ◀──── DBD(I=0,M=0,MS=1,seq=1001) [Master done]
       DBD(I=0,M=0,MS=0,seq=1001) ──────────────────▶ [Exchange done → LOADING]
       LSR(LSA types R1 needs) ─────────────────────▶
                         ◀──────────────────── LSU(full LSAs)
       LSAck ────────────────────────────────────────▶
                         ◀─────────────────────── LSR(LSAs R2 needs)
       LSU(full LSAs) ───────────────────────────────▶
                         ◀────────────────────────── LSAck
                              [FULL adjacency achieved]
```

---

## 14. LSA Flooding and Reliability

### Flooding Algorithm

When a router receives a new or updated LSA (via LSU):

```
  RECEIVE LSA (lsa, receiving_interface, from_neighbor):
  
  1. Look up existing LSA in LSDB by (type, link-state-id, adv-router)
  
  2. If new LSA is OLDER than existing:
     - Send LSU with existing (newer) LSA back to sender (implicit ACK of the older)
     - STOP (don't flood the older one)
  
  3. If new LSA is SAME AGE AND INSTANCE as existing:
     - Send LSAck (already have it)
     - STOP
  
  4. If new LSA is NEWER:
     a. Install in LSDB (replace old)
     b. Send LSAck to sender
     c. Schedule SPF if topology change
     d. Flood to ALL interfaces EXCEPT receiving_interface:
        - On point-to-point: unicast to neighbor
        - On broadcast: 
          * If we are DR or BDR: send to 224.0.0.5
          * If DROther: send to 224.0.0.6 (DR/BDR pick it up and re-flood)
     e. Add LSA to retransmission list for each neighbor
        until acknowledged
```

### Retransmission and Reliability

OSPF flooding is reliable through:

1. **Retransmission lists**: Every router tracks which LSAs it has sent to each neighbor but not yet acknowledged
2. **Retransmission timer (RxmtInterval)**: Typically 5 seconds. If no ACK received, retransmit LSU
3. **LSAck**: Explicit acknowledgment; can be delayed and batched

```
  Retransmission mechanism:

  Router A sends LSU to Router B
  ├── Adds LSA to B's retransmission list
  ├── Starts retransmit timer (5s default)
  │
  ├── B sends LSAck → A removes LSA from retransmit list
  │
  └── [No ACK] Timer fires → A retransmits LSU to B
```

### Duplicate LSA Suppression

If a router receives the same LSA it just sent (echo from flooding), it must handle it carefully:
- If received within MinLSArrival (1 second default): discard as duplicate
- If from the same neighbor that acknowledged it: normal echo, discard

---

## 15. LSA Aging and MaxAge

Every LSA has an **LS Age** field that increments with time. This solves the "phantom route" problem: if the originating router crashes without withdrawing its LSA, the LSA naturally ages out.

```
  LSA AGING LIFECYCLE:

  Age 0: LSA created by originator
  │
  ├── Age increments as LSA sits in LSDBs
  │
  Age 1800 (CheckAge): Router validates checksum, refreshes if originator
  │                    If you're the originator: re-originate with Age=0
  │
  ├── Age continues incrementing during transit (transit delay added)
  │
  Age 3600 (MaxAge): LSA is DEAD
  │    - Flooded with MaxAge so all routers can delete it
  │    - After flood complete, deleted from LSDB
  │
  └── If originator still alive, it re-originates the LSA with Age=0

  TRANSIT DELAY:
  When forwarding an LSA, router ADDS InfTransDelay (default 1s) to LS Age
  in the packet header. This accounts for propagation time through the network.
  The copy in the local LSDB is NOT modified — only the transmitted copy.
```

**MaxAge flushing — how to withdraw a route**:

When a link goes down, the router re-originates its Router LSA WITHOUT that link. The old LSA with the link is replaced by the new one. To explicitly remove an LSA (e.g., when an ASBR stops redistributing), the originator sends the LSA with Age = MaxAge (3600). All routers flood this MaxAge LSA, then delete it.

---

## 16. OSPF Timers

| Timer | Default | Description |
|-------|---------|-------------|
| Hello Interval | 10s (broadcast/p2p), 30s (NBMA) | Hello sending frequency |
| Dead Interval | 4× Hello (40s or 120s) | Neighbor declared dead after this |
| Retransmit Interval | 5s | LSU retransmit if no ACK |
| Transmit Delay | 1s | Added to LSA age before transmitting |
| LSA Refresh Time | 1800s | Re-originate own LSAs (half of MaxAge) |
| MaxAge | 3600s | LSA expires and must be flushed |
| MinLSArrival | 1s | Minimum time between same LSA instances |
| MinLSInterval | 5s | Minimum time between re-originating same LSA |
| SPF Start | 0-5s | Delay before first SPF after change |
| SPF Hold | 0-10s | Hold time between consecutive SPF runs |

**BFD (Bidirectional Forwarding Detection)** integration: BFD runs sub-second failure detection (10-50ms). OSPF uses BFD as an asynchronous notification that a neighbor is down — bypassing the Dead Interval wait. This is the standard way to achieve fast failure detection without tuning OSPF timers.

```
  Without BFD: failure detected in Dead Interval = 40 seconds
  With BFD:    failure detected in ~50ms
               BFD notifies OSPF → OSPF immediately marks neighbor DOWN
               → SPF runs → routes updated
```

---

## 17. OSPFv3 — IPv6 OSPF

OSPFv3 (RFC 5340) is a redesign of OSPF for IPv6. Key differences:

### Protocol-level Changes

| Feature | OSPFv2 | OSPFv3 |
|---------|--------|--------|
| IP version | IPv4 | IPv6 |
| Runs over | IP protocol 89 | IP protocol 89 |
| Neighbor discovery | IPv4 multicast | IPv6 multicast (FF02::5, FF02::6) |
| Authentication | IP-level auth fields | IPsec (AH/ESP) |
| Router ID | IPv4 address or manual | Always 32-bit, configured manually |
| Address families | IPv4 only | Multi-AF (RFC 5838) |

### Structural Changes

**Addressing removed from Router/Network LSAs**:
- OSPFv2 Router/Network LSAs carry IP addresses
- OSPFv3 Router/Network LSAs carry ONLY topology (no addresses!)
- Addresses are in separate **Intra-Area-Prefix LSAs**

**New LSA types in OSPFv3**:

| Type | Name | Function |
|------|------|----------|
| 0x2001 | Router | Topology only (no addresses) |
| 0x2002 | Network | Topology only |
| 0x2003 | Inter-Area-Prefix | Replaces Type 3 Summary |
| 0x2004 | Inter-Area-Router | Replaces Type 4 |
| 0x4005 | AS-External | Like Type 5, IPv6 addresses |
| 0x2007 | NSSA | Like Type 7 |
| 0x0008 | Link-LSA | Per-link IPv6 addresses, options |
| 0x2009 | Intra-Area-Prefix | IPv6 prefixes for routers/networks |

**Link-LSA (Type 8)**: Each router originates one per interface, containing:
- Link-local IPv6 address
- IPv6 prefixes on that link
- Options

**OSPFv3 Header changes**:
- No Authentication fields (use IPsec)
- Instance ID field (allows multiple OSPFv3 instances per link)
- No Options field in header (options moved to Hello body)

### OSPFv3 Packet Header

```
   0                   1                   2                   3
   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |   Version #   |     Type      |         Packet Length         |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                          Router ID                            |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                           Area ID                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |           Checksum            |  Instance ID  |   0           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  No Authentication fields!
  Instance ID: Allows multiple OSPFv3 processes on same link
```

---

## 18. OSPF Authentication

### Type 0 — Null Authentication
No authentication. Anyone can inject fake LSAs. Never use in production.

### Type 1 — Simple Password (Cleartext)

```
  Auth field in OSPF header contains 8-byte password in cleartext.
  Trivially sniffable. Only slightly better than nothing.
  Deprecated in RFC 5709.
```

### Type 2 — MD5 Cryptographic Authentication (RFC 2154)

```
  OSPF HEADER (AuType=2):
  Auth field:
  ┌────────────────┬────────────────┬────────────────┬────────────┐
  │   0 (2 bytes)  │ Key ID (1byte) │Auth data len(1)│Crypto seq# │
  └────────────────┴────────────────┴────────────────┴────────────┘
  
  After OSPF packet: 16-byte MD5 digest (appended, not in checksum)
  
  MD5 digest = MD5(OSPF_packet || shared_key)
  
  Crypto Sequence Number: monotonically increasing, prevents replay attacks
  Key ID: allows key rollover without disrupting adjacency
```

**MD5 auth process**:
1. Sender fills OSPF packet, sets checksum to 0 (auth packets don't use IP checksum for auth data)
2. Appends shared key
3. Computes MD5, appends 16-byte digest after packet
4. Receiver: recomputes MD5 with its key, verifies match, checks seq number

### SHA Authentication (RFC 5709)

Modern alternative using SHA-1, SHA-256, SHA-384, SHA-512 HMAC. Stronger than MD5. Supported in OSPFv2 via cryptographic authentication extension.

### OSPFv3 Authentication

OSPFv3 relies on **IPsec (RFC 4552)**:
- AH (Authentication Header) for integrity
- ESP (Encapsulating Security Payload) for encryption + integrity
- SA configured per-interface using IKE or manual

---

## 19. Traffic Engineering and Opaque LSAs

### OSPF-TE (RFC 3630)

OSPF-TE extends OSPF to carry traffic engineering information via Type 10 Opaque LSAs. This enables **MPLS Traffic Engineering** with Constraint-Based Shortest Path First (CSPF).

**TE LSA TLV Structure**:
```
  Type 10 Opaque LSA body:
  ┌─────────────────────────────────────────────────────┐
  │  Router Address TLV (type=1):                       │
  │    TE router address (stable, usually loopback)     │
  ├─────────────────────────────────────────────────────┤
  │  Link TLV (type=2):                                 │
  │    Sub-TLV 1: Link type (1=p2p, 2=multiaccess)     │
  │    Sub-TLV 2: Link ID (neighbor RID or DR IP)       │
  │    Sub-TLV 3: Local interface IP                    │
  │    Sub-TLV 4: Remote interface IP                   │
  │    Sub-TLV 5: TE metric (separate from routing)     │
  │    Sub-TLV 6: Max bandwidth (bytes/s)               │
  │    Sub-TLV 7: Max reservable bandwidth              │
  │    Sub-TLV 8: Unreserved bandwidth (8 TE classes)   │
  │    Sub-TLV 9: Administrative group (color/affinity) │
  └─────────────────────────────────────────────────────┘
```

**CSPF Algorithm**: Like SPF but with constraints:
- Bandwidth constraint: only use links with sufficient available bandwidth
- Affinity/color constraints: include/exclude links based on admin group
- SRLG (Shared Risk Link Group): avoid links sharing physical fiber

### Segment Routing with OSPF (RFC 8665)

Modern extension: Prefix-SID and Adjacency-SID advertised via Prefix-SID Sub-TLV in Extended Prefix LSAs (Type 7 Opaque). Enables source-routing via MPLS label stack.

---

## 20. OSPF Convergence and Fast Reroute

### Convergence Sequence

```
  LINK FAILURE EVENT TIMELINE:

  t=0ms    : Physical link fails
  t=10ms   : BFD detects failure (if configured)
             OR
  t=40000ms: Dead Interval expires (without BFD!)
  
  t+0ms    : OSPF marks neighbor DOWN
  t+50ms   : SPF delay expires (spf-start timer)
  t+50ms   : Router re-originates Router LSA (removes failed link)
  t+50ms   : LSA flooded to all routers in area
  t+100ms  : All area routers have new LSA
  t+150ms  : SPF computation completes
  t+150ms  : New routes installed in FIB
  t+150ms  : Traffic rerouted
  
  With BFD: total convergence ~200ms
  Without BFD: total convergence ~40+ seconds
```

### Loop-Free Alternate (LFA) — RFC 5286

LFA provides **pre-computed backup next-hops** that are installed BEFORE failure. When BFD detects a failure, the backup next-hop is immediately activated — NO SPF required.

**LFA condition** (neighbor N is a loop-free alternate for destination D via primary next-hop P):
```
  dist(N, D) < dist(N, P) + dist(P, D)
  
  N must have a shorter path to D that does NOT go through P.
  
  If this holds: N is a valid LFA.
  If not: sending to N would create a loop.
```

**Types of LFA**:
- **Local LFA**: Neighbor provides loop-free path (works for ~50-80% of failures)
- **Remote LFA (rLFA)**: Tunnel to a remote PQ node that is loop-free (RFC 7490)
- **Topology-Independent LFA (TI-LFA)**: Segment Routing based; 100% coverage

### IPFRR (IP Fast ReRoute)

Framework (RFC 5714) for protecting against link/node failures with sub-50ms reroute using pre-computed alternates.

---

## 21. OSPF Scalability and Tuning

### Scalability Limits

| Resource | Practical Limit | Notes |
|----------|----------------|-------|
| Routers per area | 50-100 | SPF computation time |
| Areas per ABR | 3-5 | LSDB memory; ABR runs SPF per area |
| LSAs in LSDB | 10,000-50,000 | Memory and SPF time |
| Neighbors per router | 60 | DBD/LSAck overhead |

### Design Best Practices

```
  1. HIERARCHICAL DESIGN
     ────────────────────
     Area 0: Backbone only (ABRs + backbone routers)
     Non-zero areas: Access/distribution routers
     ABRs: Connect exactly two areas ideally
  
  2. SUMMARIZATION AT ABR
     ─────────────────────
     Assign contiguous address blocks per area
     Use "area X range" commands on ABR
     Reduces inter-area LSA count drastically
  
  3. SUMMARIZATION AT ASBR
     ─────────────────────
     Use "summary-address" on ASBR for external routes
     Reduces Type 5 LSA count
  
  4. STUB AREAS AGGRESSIVELY
     ──────────────────────
     Any area with single exit = stub or totally stubby
     Reduces LSDB size and SPF scope
  
  5. REFERENCE BANDWIDTH TUNING
     ───────────────────────────
     auto-cost reference-bandwidth 100000 (100G)
     Apply consistently across ALL routers
  
  6. SPF THROTTLE TUNING
     ────────────────────
     In stable networks: spf-start 200ms, spf-hold 1000ms, spf-max 10000ms
     In unstable networks: increase spf-hold to dampen thrashing
  
  7. LSA THROTTLE TUNING
     ─────────────────────
     lsa-arrival 1000ms (minimum gap between same LSA instances)
     lsa-group-pacing (batch LSA refreshes to prevent flooding storms)
```

---

## 22. OSPF vs Other Protocols

| Feature | OSPF | IS-IS | EIGRP | RIP |
|---------|------|-------|-------|-----|
| Algorithm | Dijkstra (link-state) | Dijkstra (link-state) | DUAL (diffusing) | Bellman-Ford (DV) |
| Metric | Cost (bandwidth) | Metric (configurable) | Composite (BW, delay, etc.) | Hop count |
| Convergence | Fast (BFD+SPF) | Fast (similar to OSPF) | Very fast (DUAL) | Slow (30s updates) |
| Scalability | High (areas) | High (levels) | Medium | Low (15 hop limit) |
| Standards | Open (RFC 2328) | Open (ISO 10589) | Cisco proprietary (now open) | Open (RFC 2453) |
| IPv6 | OSPFv3 | IS-ISv6 | EIGRPv6 | RIPng |
| Complexity | High | High | Medium | Low |
| Max metric | 65535 | 16777215 | 4294967295 | 15 |

**IS-IS vs OSPF**:
- IS-IS runs over Layer 2 directly (not IP) — more resilient to IP misconfiguration
- IS-IS uses router-level (not interface-level) area assignment
- IS-IS has two levels (L1/L2) instead of areas
- IS-IS is preferred by large ISPs (Tier 1) — simpler to scale
- OSPF is more common in enterprise

---

## 23. C Implementation

The following implementation covers the core OSPF data structures, packet serialization/deserialization, neighbor state machine, Hello sending, and a simplified SPF computation. This is a functional skeleton, not a full production OSPF daemon (which would be tens of thousands of lines).

```c
/*
 * ospf_core.c - OSPF Core Implementation
 * Covers: packet structures, neighbor FSM, Hello, LSA, basic SPF
 * Compile: gcc -O2 -Wall -o ospf_core ospf_core.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>
#include <stdbool.h>

/* =====================================================================
 * CONSTANTS
 * ===================================================================== */

#define OSPF_VERSION            2
#define OSPF_HEADER_LEN         24
#define LSA_HEADER_LEN          20

#define OSPF_PROTO              89
#define OSPF_ALL_ROUTERS        "224.0.0.5"
#define OSPF_DR_ROUTERS         "224.0.0.6"

/* Packet types */
#define OSPF_TYPE_HELLO         1
#define OSPF_TYPE_DBD           2
#define OSPF_TYPE_LSR           3
#define OSPF_TYPE_LSU           4
#define OSPF_TYPE_LSACK         5

/* LSA types */
#define LSA_TYPE_ROUTER         1
#define LSA_TYPE_NETWORK        2
#define LSA_TYPE_SUMMARY        3
#define LSA_TYPE_ASBR_SUMMARY   4
#define LSA_TYPE_EXTERNAL       5
#define LSA_TYPE_NSSA           7

/* OSPF Link types (in Router LSA) */
#define LINK_TYPE_P2P           1
#define LINK_TYPE_TRANSIT       2
#define LINK_TYPE_STUB          3
#define LINK_TYPE_VIRTUAL       4

/* Neighbor states */
typedef enum {
    OSPF_NBR_DOWN     = 0,
    OSPF_NBR_ATTEMPT  = 1,
    OSPF_NBR_INIT     = 2,
    OSPF_NBR_2WAY     = 3,
    OSPF_NBR_EXSTART  = 4,
    OSPF_NBR_EXCHANGE = 5,
    OSPF_NBR_LOADING  = 6,
    OSPF_NBR_FULL     = 7,
} ospf_nbr_state_t;

/* Network types */
typedef enum {
    NET_BROADCAST     = 0,
    NET_POINT2POINT   = 1,
    NET_NBMA          = 2,
    NET_P2MP          = 3,
    NET_LOOPBACK      = 4,
} ospf_net_type_t;

/* Timers */
#define DEFAULT_HELLO_INTERVAL  10
#define DEFAULT_DEAD_INTERVAL   40
#define DEFAULT_RXMT_INTERVAL   5
#define DEFAULT_TRANS_DELAY     1
#define LSA_MAXAGE              3600
#define LSA_REFRESH_TIME        1800
#define LSA_MIN_ARRIVAL         1
#define LSA_MIN_INTERVAL        5
#define OSPF_MAX_COST           65535

#define MAX_NEIGHBORS           64
#define MAX_LSDB_ENTRIES        4096
#define MAX_INTERFACES          16
#define MAX_LINKS_PER_LSA       64
#define MAX_NODES               256

/* =====================================================================
 * DATA STRUCTURES
 * ===================================================================== */

/* 32-bit Router ID / IP address wrapper */
typedef uint32_t ospf_rid_t;
typedef uint32_t ospf_area_t;

/* Convert dotted-decimal string to uint32 (network byte order) */
static inline ospf_rid_t rid_from_str(const char *s) {
    struct in_addr a;
    inet_aton(s, &a);
    return a.s_addr;
}

static inline void rid_to_str(ospf_rid_t rid, char *buf, size_t len) {
    struct in_addr a;
    a.s_addr = rid;
    snprintf(buf, len, "%s", inet_ntoa(a));
}

/* ─── OSPF Common Header ─────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    uint8_t  version;
    uint8_t  type;
    uint16_t length;        /* total packet length including header */
    uint32_t router_id;
    uint32_t area_id;
    uint16_t checksum;
    uint8_t  au_type;
    uint8_t  pad;           /* RFC: first byte of au_type for simple */
    uint64_t authentication;
} ospf_header_t;

/* ─── Hello Packet ───────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    ospf_header_t hdr;
    uint32_t  network_mask;
    uint16_t  hello_interval;
    uint8_t   options;
    uint8_t   rtr_priority;
    uint32_t  dead_interval;
    uint32_t  dr;           /* Designated Router IP */
    uint32_t  bdr;          /* Backup DR IP */
    uint32_t  neighbors[0]; /* Variable-length neighbor list */
} ospf_hello_t;

/* ─── DBD Packet ─────────────────────────────────────────────────── */
#define DBD_FLAG_MS  0x01
#define DBD_FLAG_M   0x02
#define DBD_FLAG_I   0x04

typedef struct __attribute__((packed)) {
    ospf_header_t hdr;
    uint16_t  interface_mtu;
    uint8_t   options;
    uint8_t   flags;       /* I/M/MS bits */
    uint32_t  dd_seqnum;
    /* Followed by LSA headers */
} ospf_dbd_t;

/* ─── LSR Entry ──────────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    uint32_t  ls_type;
    uint32_t  link_state_id;
    uint32_t  adv_router;
} ospf_lsr_entry_t;

/* ─── LSA Header ─────────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    uint16_t  ls_age;
    uint8_t   options;
    uint8_t   ls_type;
    uint32_t  link_state_id;
    uint32_t  adv_router;
    int32_t   ls_seqnum;    /* signed: 0x80000001 to 0x7FFFFFFF */
    uint16_t  ls_checksum;
    uint16_t  length;
} ospf_lsa_header_t;

/* ─── Router LSA Link ────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    uint32_t  link_id;
    uint32_t  link_data;
    uint8_t   type;
    uint8_t   num_tos;
    uint16_t  metric;
} ospf_router_link_t;

/* ─── Router LSA ─────────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    ospf_lsa_header_t  hdr;
    uint8_t            flags;    /* V/E/B bits */
    uint8_t            pad;
    uint16_t           num_links;
    ospf_router_link_t links[0]; /* variable */
} ospf_router_lsa_t;

/* ─── Network LSA ────────────────────────────────────────────────── */
typedef struct __attribute__((packed)) {
    ospf_lsa_header_t hdr;
    uint32_t          network_mask;
    uint32_t          attached_routers[0]; /* variable */
} ospf_network_lsa_t;

/* ─── Summary LSA (Type 3 / Type 4) ─────────────────────────────── */
typedef struct __attribute__((packed)) {
    ospf_lsa_header_t hdr;
    uint32_t          network_mask;
    uint8_t           pad;
    uint8_t           metric_hi;  /* top byte of 3-byte metric */
    uint16_t          metric_lo;
} ospf_summary_lsa_t;

/* ─── In-memory LSA node (for LSDB) ─────────────────────────────── */
typedef struct lsdb_entry {
    ospf_lsa_header_t  header;
    uint8_t           *body;          /* body bytes (after header) */
    size_t             body_len;
    time_t             recv_time;     /* when first received */
    struct lsdb_entry *next;          /* hash chain */
} lsdb_entry_t;

/* ─── LSDB ───────────────────────────────────────────────────────── */
#define LSDB_HASH_SIZE 256

typedef struct {
    lsdb_entry_t *buckets[LSDB_HASH_SIZE];
    size_t        count;
    ospf_area_t   area_id;
} ospf_lsdb_t;

/* ─── Neighbor ───────────────────────────────────────────────────── */
typedef struct ospf_neighbor {
    ospf_rid_t           rid;
    struct in_addr       src_ip;       /* Neighbor's source IP */
    ospf_nbr_state_t     state;
    uint8_t              priority;
    uint32_t             dr;           /* DR as seen by neighbor */
    uint32_t             bdr;
    uint32_t             dd_seqnum;    /* DD exchange seq num */
    bool                 is_master;    /* Are WE master? */
    bool                 dd_more;      /* More DBDs to come */
    time_t               last_hello;   /* Time of last Hello received */
    ospf_lsr_entry_t    *req_list;     /* LSR list (LSAs we need) */
    size_t               req_count;
    ospf_lsa_header_t   *rxmt_list;   /* Retransmit list */
    size_t               rxmt_count;
    struct ospf_neighbor *next;
} ospf_neighbor_t;

/* ─── Interface ──────────────────────────────────────────────────── */
typedef struct ospf_iface {
    char             name[16];
    int              fd;           /* raw socket */
    struct in_addr   ip;
    struct in_addr   mask;
    ospf_area_t      area_id;
    ospf_net_type_t  net_type;
    uint16_t         cost;
    uint8_t          priority;
    uint16_t         hello_interval;
    uint32_t         dead_interval;
    uint32_t         dr;
    uint32_t         bdr;
    uint16_t         mtu;
    ospf_neighbor_t *neighbors;    /* linked list */
    size_t           neighbor_count;
} ospf_iface_t;

/* ─── OSPF Instance ──────────────────────────────────────────────── */
typedef struct {
    ospf_rid_t    router_id;
    ospf_area_t   backbone_area; /* 0.0.0.0 */
    ospf_iface_t  interfaces[MAX_INTERFACES];
    size_t        iface_count;
    ospf_lsdb_t   lsdbs[MAX_INTERFACES]; /* one per area */
    size_t        lsdb_count;
    int32_t       lsa_seqnum;   /* current LSA sequence number */
} ospf_instance_t;

/* ─── SPF Graph Node ─────────────────────────────────────────────── */
typedef struct {
    ospf_rid_t  node_id;         /* RID or pseudo-node ID */
    bool        is_pseudo;       /* True if transit network node */
    uint32_t    cost;            /* cost from root */
    int         parent;          /* index of parent in array, -1 if root */
    ospf_rid_t  next_hop_ip;
    bool        in_shortest;
    bool        in_candidate;
} spf_node_t;

/* ─── SPF Result ─────────────────────────────────────────────────── */
typedef struct {
    uint32_t    dest_net;
    uint32_t    dest_mask;
    uint32_t    cost;
    uint32_t    next_hop;
    ospf_rid_t  adv_router;
} spf_route_t;

/* =====================================================================
 * CHECKSUM UTILITIES
 * ===================================================================== */

/* Fletcher-16 checksum as used in OSPF LSAs (RFC 905) */
static void fletcher16_checksum(uint8_t *buf, size_t len,
                                 size_t c0_off, size_t c1_off) {
    int32_t c0 = 0, c1 = 0;
    buf[c0_off] = 0;
    buf[c1_off] = 0;
    for (size_t i = 0; i < len; i++) {
        c0 = (c0 + buf[i]) % 255;
        c1 = (c1 + c0)    % 255;
    }
    int32_t x = ((int32_t)(len - c0_off - 1) * c0 - c1) % 255;
    if (x <= 0) x += 255;
    buf[c0_off] = (uint8_t)x;
    buf[c1_off] = (uint8_t)(510 - c0 - x);
}

/* Standard Internet checksum (for OSPF packet header) */
static uint16_t inet_checksum(const void *data, size_t len) {
    const uint16_t *p = (const uint16_t *)data;
    uint32_t sum = 0;
    while (len > 1) {
        sum += *p++;
        len -= 2;
    }
    if (len) sum += *(const uint8_t *)p;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (uint16_t)~sum;
}

/* =====================================================================
 * LSDB OPERATIONS
 * ===================================================================== */

static uint32_t lsdb_hash(uint8_t type, uint32_t lsid, uint32_t adv) {
    return (type * 2654435761u ^ lsid ^ adv) % LSDB_HASH_SIZE;
}

static lsdb_entry_t *lsdb_lookup(ospf_lsdb_t *db, uint8_t type,
                                   uint32_t lsid, uint32_t adv) {
    uint32_t idx = lsdb_hash(type, lsid, adv);
    for (lsdb_entry_t *e = db->buckets[idx]; e; e = e->next) {
        if (e->header.ls_type     == type &&
            e->header.link_state_id == lsid &&
            e->header.adv_router  == adv) {
            return e;
        }
    }
    return NULL;
}

/*
 * Compare two LSA headers for newness.
 * Returns: >0 if a is newer, <0 if b is newer, 0 if same
 */
static int lsa_compare(const ospf_lsa_header_t *a,
                        const ospf_lsa_header_t *b) {
    /* Higher sequence number = newer */
    if (ntohl(a->ls_seqnum) != ntohl(b->ls_seqnum))
        return (int32_t)(ntohl(a->ls_seqnum) - ntohl(b->ls_seqnum));
    /* Same seqnum: higher checksum = newer */
    if (ntohs(a->ls_checksum) != ntohs(b->ls_checksum))
        return (int)(ntohs(a->ls_checksum) - ntohs(b->ls_checksum));
    /* Same checksum: lower age = newer */
    if (ntohs(a->ls_age) != ntohs(b->ls_age))
        return (int)(ntohs(b->ls_age) - ntohs(a->ls_age));
    /* MaxAge: MaxAge version wins for flushing */
    if (ntohs(a->ls_age) == LSA_MAXAGE) return 1;
    if (ntohs(b->ls_age) == LSA_MAXAGE) return -1;
    return 0;
}

/*
 * Install or replace an LSA in the LSDB.
 * Returns: 1 if installed (newer), 0 if existing is newer/same.
 */
static int lsdb_install(ospf_lsdb_t *db, const ospf_lsa_header_t *hdr,
                         const uint8_t *body, size_t body_len) {
    uint8_t   type = hdr->ls_type;
    uint32_t  lsid = hdr->link_state_id;
    uint32_t  adv  = hdr->adv_router;
    uint32_t  idx  = lsdb_hash(type, lsid, adv);

    lsdb_entry_t *existing = lsdb_lookup(db, type, lsid, adv);
    if (existing) {
        int cmp = lsa_compare(hdr, &existing->header);
        if (cmp <= 0) return 0; /* existing is same or newer */
        /* Replace */
        free(existing->body);
        existing->header   = *hdr;
        existing->body     = body_len ? malloc(body_len) : NULL;
        if (existing->body) memcpy(existing->body, body, body_len);
        existing->body_len = body_len;
        existing->recv_time = time(NULL);
        return 1;
    }

    /* New entry */
    lsdb_entry_t *e = calloc(1, sizeof(*e));
    if (!e) return -1;
    e->header    = *hdr;
    e->body      = body_len ? malloc(body_len) : NULL;
    if (e->body) memcpy(e->body, body, body_len);
    e->body_len  = body_len;
    e->recv_time = time(NULL);
    e->next      = db->buckets[idx];
    db->buckets[idx] = e;
    db->count++;
    return 1;
}

/* Remove MaxAge LSAs from LSDB */
static void lsdb_purge_maxage(ospf_lsdb_t *db) {
    for (int i = 0; i < LSDB_HASH_SIZE; i++) {
        lsdb_entry_t **prev = &db->buckets[i];
        lsdb_entry_t *e = db->buckets[i];
        while (e) {
            uint16_t age = ntohs(e->header.ls_age);
            /* Age the LSA */
            time_t elapsed = time(NULL) - e->recv_time;
            age = (uint16_t)((age + elapsed) > LSA_MAXAGE ?
                              LSA_MAXAGE : age + elapsed);
            if (age >= LSA_MAXAGE) {
                *prev = e->next;
                free(e->body);
                free(e);
                db->count--;
                e = *prev;
            } else {
                prev = &e->next;
                e = e->next;
            }
        }
    }
}

/* =====================================================================
 * OSPF PACKET BUILDING
 * ===================================================================== */

static void ospf_fill_header(ospf_header_t *hdr, uint8_t type,
                              uint16_t length, ospf_rid_t router_id,
                              ospf_area_t area_id) {
    hdr->version     = OSPF_VERSION;
    hdr->type        = type;
    hdr->length      = htons(length);
    hdr->router_id   = router_id;
    hdr->area_id     = area_id;
    hdr->checksum    = 0;
    hdr->au_type     = 0;
    hdr->pad         = 0;
    hdr->authentication = 0;
}

/*
 * Build an OSPF Hello packet.
 * neighbors: array of neighbor RIDs to include
 * Returns: allocated buffer (caller frees), sets *out_len
 */
uint8_t *ospf_build_hello(ospf_instance_t *ospf, ospf_iface_t *iface,
                           ospf_rid_t *nbrs, size_t nbr_count,
                           size_t *out_len) {
    size_t pkt_len = sizeof(ospf_hello_t) + nbr_count * 4;
    uint8_t *buf   = calloc(1, pkt_len);
    if (!buf) return NULL;

    ospf_hello_t *hello = (ospf_hello_t *)buf;
    ospf_fill_header(&hello->hdr, OSPF_TYPE_HELLO, (uint16_t)pkt_len,
                     ospf->router_id, iface->area_id);

    hello->network_mask    = iface->mask.s_addr;
    hello->hello_interval  = htons(iface->hello_interval);
    hello->options         = 0x02; /* E bit — external capable */
    hello->rtr_priority    = iface->priority;
    hello->dead_interval   = htonl(iface->dead_interval);
    hello->dr              = iface->dr;
    hello->bdr             = iface->bdr;

    for (size_t i = 0; i < nbr_count; i++) {
        hello->neighbors[i] = nbrs[i];
    }

    /* Compute checksum (over entire packet, auth fields zeroed) */
    hello->hdr.checksum = inet_checksum(buf, pkt_len);
    *out_len = pkt_len;
    return buf;
}

/*
 * Build a Router LSA for this router.
 * links: array of link structs
 * Returns: allocated buffer, sets *out_len
 */
uint8_t *ospf_build_router_lsa(ospf_instance_t *ospf,
                                ospf_area_t area_id,
                                ospf_router_link_t *links,
                                size_t link_count,
                                size_t *out_len) {
    size_t body_off = sizeof(ospf_lsa_header_t);
    size_t lsa_len  = body_off + 4 + link_count * sizeof(ospf_router_link_t);
    uint8_t *buf    = calloc(1, lsa_len);
    if (!buf) return NULL;

    ospf_router_lsa_t *rlsa = (ospf_router_lsa_t *)buf;

    /* LSA header */
    rlsa->hdr.ls_age        = htons(0);
    rlsa->hdr.options       = 0x02;
    rlsa->hdr.ls_type       = LSA_TYPE_ROUTER;
    rlsa->hdr.link_state_id = ospf->router_id;
    rlsa->hdr.adv_router    = ospf->router_id;
    rlsa->hdr.ls_seqnum     = htonl(ospf->lsa_seqnum++);
    rlsa->hdr.length        = htons((uint16_t)lsa_len);

    /* Router LSA body */
    rlsa->flags     = 0; /* Set B or E bit as appropriate */
    rlsa->pad       = 0;
    rlsa->num_links = htons((uint16_t)link_count);
    memcpy(rlsa->links, links, link_count * sizeof(ospf_router_link_t));

    /* Fletcher checksum over LSA (skip LS age = bytes 0-1) */
    fletcher16_checksum(buf + 2, lsa_len - 2,
                        offsetof(ospf_lsa_header_t, ls_checksum) - 2,
                        offsetof(ospf_lsa_header_t, ls_checksum) - 1);

    *out_len = lsa_len;
    return buf;
}

/* =====================================================================
 * NEIGHBOR STATE MACHINE
 * ===================================================================== */

static const char *nbr_state_names[] = {
    "DOWN", "ATTEMPT", "INIT", "2-WAY",
    "EXSTART", "EXCHANGE", "LOADING", "FULL"
};

static void nbr_change_state(ospf_neighbor_t *nbr,
                              ospf_nbr_state_t new_state) {
    char rid_str[20];
    rid_to_str(nbr->rid, rid_str, sizeof(rid_str));
    printf("[FSM] Neighbor %s: %s → %s\n",
           rid_str,
           nbr_state_names[nbr->state],
           nbr_state_names[new_state]);
    nbr->state = new_state;
}

/* Process received Hello — update neighbor state */
static void ospf_process_hello(ospf_instance_t *ospf,
                                ospf_iface_t *iface,
                                const ospf_hello_t *hello,
                                struct in_addr src_ip) {
    ospf_rid_t sender_rid = hello->hdr.router_id;
    uint16_t hello_int    = ntohs(hello->hello_interval);
    uint32_t dead_int     = ntohl(hello->dead_interval);

    /* Parameter validation */
    if (hello->network_mask != iface->mask.s_addr) {
        printf("[HELLO] Mask mismatch, ignoring neighbor\n");
        return;
    }
    if (hello_int != iface->hello_interval) {
        printf("[HELLO] Hello interval mismatch (%u vs %u)\n",
               hello_int, iface->hello_interval);
        return;
    }
    if (dead_int != iface->dead_interval) {
        printf("[HELLO] Dead interval mismatch (%u vs %u)\n",
               dead_int, iface->dead_interval);
        return;
    }

    /* Find or create neighbor */
    ospf_neighbor_t *nbr = NULL;
    for (ospf_neighbor_t *n = iface->neighbors; n; n = n->next) {
        if (n->rid == sender_rid) { nbr = n; break; }
    }
    if (!nbr) {
        nbr = calloc(1, sizeof(*nbr));
        if (!nbr) return;
        nbr->rid   = sender_rid;
        nbr->state = OSPF_NBR_DOWN;
        nbr->next  = iface->neighbors;
        iface->neighbors = nbr;
        iface->neighbor_count++;
    }

    nbr->src_ip  = src_ip;
    nbr->priority = hello->rtr_priority;
    nbr->dr       = hello->dr;
    nbr->bdr      = hello->bdr;
    nbr->last_hello = time(NULL);

    /* Transition to INIT if not already */
    if (nbr->state == OSPF_NBR_DOWN) {
        nbr_change_state(nbr, OSPF_NBR_INIT);
    }

    /* Check if our RID is in neighbor's neighbor list → 2-WAY */
    size_t num_nbrs = (ntohs(hello->hdr.length) - sizeof(ospf_hello_t)) / 4;
    bool seen_by_nbr = false;
    for (size_t i = 0; i < num_nbrs; i++) {
        if (hello->neighbors[i] == ospf->router_id) {
            seen_by_nbr = true;
            break;
        }
    }

    if (seen_by_nbr && nbr->state == OSPF_NBR_INIT) {
        nbr_change_state(nbr, OSPF_NBR_2WAY);

        /* Decide whether to form adjacency:
         * - Point-to-point: always
         * - Broadcast: only if we or neighbor is DR/BDR */
        bool form_adj = false;
        if (iface->net_type == NET_POINT2POINT) {
            form_adj = true;
        } else {
            /* Broadcast: form if either side is DR or BDR */
            bool we_are_dr  = (iface->dr  == iface->ip.s_addr);
            bool we_are_bdr = (iface->bdr == iface->ip.s_addr);
            bool nbr_is_dr  = (hello->dr  == sender_rid);
            bool nbr_is_bdr = (hello->bdr == sender_rid);
            form_adj = we_are_dr || we_are_bdr || nbr_is_dr || nbr_is_bdr;
        }

        if (form_adj) {
            nbr_change_state(nbr, OSPF_NBR_EXSTART);
            /* Initiate Master/Slave negotiation */
            nbr->dd_seqnum = (uint32_t)time(NULL); /* random-ish */
            nbr->is_master = (ospf->router_id > sender_rid);
            printf("[DBD] Starting EXSTART with %x, we are %s\n",
                   sender_rid, nbr->is_master ? "MASTER" : "SLAVE");
        }
    } else if (!seen_by_nbr && nbr->state >= OSPF_NBR_2WAY) {
        /* Neighbor stopped listing us → back to INIT */
        nbr_change_state(nbr, OSPF_NBR_INIT);
    }
}

/*
 * Timer check — expire dead neighbors
 */
static void ospf_check_dead_timers(ospf_iface_t *iface) {
    time_t now = time(NULL);
    ospf_neighbor_t **prev = &iface->neighbors;
    ospf_neighbor_t *nbr   = iface->neighbors;
    while (nbr) {
        if (nbr->state != OSPF_NBR_DOWN &&
            (now - nbr->last_hello) > iface->dead_interval) {
            char rid_str[20];
            rid_to_str(nbr->rid, rid_str, sizeof(rid_str));
            printf("[TIMER] Neighbor %s DEAD (no Hello in %u sec)\n",
                   rid_str, iface->dead_interval);
            nbr_change_state(nbr, OSPF_NBR_DOWN);
            /* Remove from list */
            *prev = nbr->next;
            free(nbr->req_list);
            free(nbr->rxmt_list);
            free(nbr);
            nbr = *prev;
        } else {
            prev = &nbr->next;
            nbr  = nbr->next;
        }
    }
}

/* =====================================================================
 * DIJKSTRA SPF IMPLEMENTATION
 * ===================================================================== */

/*
 * Simple min-heap for SPF candidate list.
 * In production: use a proper Fibonacci heap or indexed priority queue.
 */
typedef struct {
    int      node_idx;
    uint32_t cost;
} heap_entry_t;

typedef struct {
    heap_entry_t *data;
    size_t        size;
    size_t        cap;
} min_heap_t;

static void heap_init(min_heap_t *h) {
    h->cap  = 64;
    h->size = 0;
    h->data = malloc(h->cap * sizeof(heap_entry_t));
}

static void heap_push(min_heap_t *h, int idx, uint32_t cost) {
    if (h->size >= h->cap) {
        h->cap *= 2;
        h->data = realloc(h->data, h->cap * sizeof(heap_entry_t));
    }
    size_t i = h->size++;
    h->data[i] = (heap_entry_t){idx, cost};
    /* Bubble up */
    while (i > 0) {
        size_t parent = (i - 1) / 2;
        if (h->data[parent].cost <= h->data[i].cost) break;
        heap_entry_t tmp   = h->data[parent];
        h->data[parent]    = h->data[i];
        h->data[i]         = tmp;
        i = parent;
    }
}

static heap_entry_t heap_pop(min_heap_t *h) {
    heap_entry_t top = h->data[0];
    h->data[0] = h->data[--h->size];
    /* Sift down */
    size_t i = 0;
    while (1) {
        size_t left  = 2*i+1, right = 2*i+2, smallest = i;
        if (left  < h->size && h->data[left].cost  < h->data[smallest].cost)
            smallest = left;
        if (right < h->size && h->data[right].cost < h->data[smallest].cost)
            smallest = right;
        if (smallest == i) break;
        heap_entry_t tmp       = h->data[smallest];
        h->data[smallest]      = h->data[i];
        h->data[i]             = tmp;
        i = smallest;
    }
    return top;
}

/*
 * Run SPF on the LSDB and produce a routing table.
 *
 * This is a simplified implementation:
 * - Processes only Type 1 (Router) and Type 2 (Network) LSAs
 * - Builds node array from LSDB, then runs Dijkstra
 * - Produces routes for stub networks
 *
 * Production SPF handles: virtual links, transit networks as pseudo-nodes,
 * ECMP, inter-area and external routes.
 */
static void ospf_run_spf(ospf_instance_t *ospf, ospf_lsdb_t *db,
                          spf_route_t *routes, size_t *route_count) {
    /* Step 1: Collect all Router nodes from LSDB */
    spf_node_t  nodes[MAX_NODES];
    size_t      node_count = 0;
    size_t      root_idx   = SIZE_MAX;

    /* Collect all router LSAs */
    for (int i = 0; i < LSDB_HASH_SIZE && node_count < MAX_NODES; i++) {
        for (lsdb_entry_t *e = db->buckets[i]; e; e = e->next) {
            if (e->header.ls_type != LSA_TYPE_ROUTER) continue;
            spf_node_t *n = &nodes[node_count];
            memset(n, 0, sizeof(*n));
            n->node_id       = e->header.adv_router;
            n->is_pseudo     = false;
            n->cost          = UINT32_MAX;
            n->parent        = -1;
            n->in_shortest   = false;
            n->in_candidate  = false;
            if (n->node_id == ospf->router_id) {
                root_idx = node_count;
            }
            node_count++;
        }
    }

    if (root_idx == SIZE_MAX || node_count == 0) {
        *route_count = 0;
        return;
    }

    /* Step 2: Initialize root */
    nodes[root_idx].cost         = 0;
    nodes[root_idx].in_candidate = true;

    /* Step 3: Dijkstra */
    min_heap_t heap;
    heap_init(&heap);
    heap_push(&heap, (int)root_idx, 0);

    while (heap.size > 0) {
        heap_entry_t top = heap_pop(&heap);
        int n_idx = top.node_idx;
        if (n_idx < 0 || (size_t)n_idx >= node_count) continue;
        spf_node_t *curr = &nodes[n_idx];
        if (curr->in_shortest) continue;
        curr->in_shortest = true;

        /* Find this router's LSA */
        lsdb_entry_t *lsa_entry = lsdb_lookup(db, LSA_TYPE_ROUTER,
                                               curr->node_id, curr->node_id);
        if (!lsa_entry || !lsa_entry->body) continue;

        /* Parse links from Router LSA body */
        uint8_t *body = lsa_entry->body;
        uint16_t num_links = ntohs(*(uint16_t *)(body + 2));
        ospf_router_link_t *links =
            (ospf_router_link_t *)(body + 4); /* skip flags/pad/num_links */

        for (uint16_t l = 0; l < num_links; l++) {
            ospf_router_link_t *link = &links[l];
            uint32_t link_cost = curr->cost + ntohs(link->metric);

            if (link->type == LINK_TYPE_P2P) {
                /* Find neighbor node by RID (= link_id for p2p) */
                for (size_t j = 0; j < node_count; j++) {
                    if (nodes[j].node_id == link->link_id &&
                        !nodes[j].in_shortest) {
                        if (link_cost < nodes[j].cost) {
                            nodes[j].cost   = link_cost;
                            nodes[j].parent = n_idx;
                            if (n_idx == (int)root_idx) {
                                nodes[j].next_hop_ip = link->link_data;
                            } else {
                                nodes[j].next_hop_ip = curr->next_hop_ip;
                            }
                            heap_push(&heap, (int)j, link_cost);
                        }
                    }
                }
            } else if (link->type == LINK_TYPE_STUB) {
                /* Stub network → direct route */
                if (*route_count < MAX_NODES) {
                    spf_route_t *r = &routes[(*route_count)++];
                    r->dest_net  = link->link_id;
                    r->dest_mask = link->link_data;
                    r->cost      = link_cost;
                    r->next_hop  = (n_idx == (int)root_idx) ?
                                   0 /* directly connected */ :
                                   nodes[n_idx].next_hop_ip;
                    r->adv_router = curr->node_id;
                }
            }
        }
    }
    free(heap.data);

    /* Print SPF tree */
    printf("\n[SPF] Shortest Path Tree (from root %x):\n", ospf->router_id);
    for (size_t i = 0; i < node_count; i++) {
        char rid_str[20], nh_str[20];
        rid_to_str(nodes[i].node_id, rid_str, sizeof(rid_str));
        rid_to_str(nodes[i].next_hop_ip, nh_str, sizeof(nh_str));
        if (nodes[i].in_shortest) {
            printf("  Node %-16s cost=%u  next_hop=%s\n",
                   rid_str, nodes[i].cost, nh_str);
        }
    }
}

/* =====================================================================
 * DR/BDR ELECTION
 * ===================================================================== */

/*
 * Elect DR and BDR for a broadcast interface.
 * RFC 2328 Section 9.4
 */
static void ospf_elect_dr_bdr(ospf_instance_t *ospf, ospf_iface_t *iface) {
    typedef struct {
        ospf_rid_t rid;
        uint8_t    priority;
        uint32_t   declared_dr;
        uint32_t   declared_bdr;
        uint32_t   ip;
    } candidate_t;

    candidate_t cands[MAX_NEIGHBORS + 1];
    size_t      nc = 0;

    /* Add self */
    cands[nc].rid          = ospf->router_id;
    cands[nc].priority     = iface->priority;
    cands[nc].declared_dr  = iface->dr;
    cands[nc].declared_bdr = iface->bdr;
    cands[nc].ip           = iface->ip.s_addr;
    nc++;

    /* Add all 2-way+ neighbors */
    for (ospf_neighbor_t *nbr = iface->neighbors; nbr; nbr = nbr->next) {
        if (nbr->state < OSPF_NBR_2WAY) continue;
        if (nbr->priority == 0)         continue; /* ineligible */
        cands[nc].rid          = nbr->rid;
        cands[nc].priority     = nbr->priority;
        cands[nc].declared_dr  = nbr->dr;
        cands[nc].declared_bdr = nbr->bdr;
        cands[nc].ip           = nbr->src_ip.s_addr;
        nc++;
    }

    /* Step 1: Elect BDR among those NOT declaring themselves DR */
    uint32_t new_bdr_rid  = 0;
    uint8_t  bdr_priority = 0;
    for (size_t i = 0; i < nc; i++) {
        if (cands[i].declared_dr == cands[i].ip) continue; /* skip DR decl */
        if (cands[i].priority > bdr_priority ||
            (cands[i].priority == bdr_priority &&
             cands[i].rid > new_bdr_rid)) {
            bdr_priority = cands[i].priority;
            new_bdr_rid  = cands[i].rid;
        }
    }

    /* Step 2: Elect DR among those declaring themselves DR */
    uint32_t new_dr_rid   = 0;
    uint8_t  dr_priority  = 0;
    bool     dr_contested = false;
    for (size_t i = 0; i < nc; i++) {
        if (cands[i].declared_dr != cands[i].ip) continue;
        dr_contested = true;
        if (cands[i].priority > dr_priority ||
            (cands[i].priority == dr_priority &&
             cands[i].rid > new_dr_rid)) {
            dr_priority = cands[i].priority;
            new_dr_rid  = cands[i].rid;
        }
    }

    /* Step 3: If no DR declared, BDR becomes DR */
    if (!dr_contested) {
        new_dr_rid = new_bdr_rid;
        /* Re-elect BDR */
        bdr_priority = 0;
        new_bdr_rid  = 0;
        for (size_t i = 0; i < nc; i++) {
            if (cands[i].rid == new_dr_rid) continue;
            if (cands[i].priority > bdr_priority ||
                (cands[i].priority == bdr_priority &&
                 cands[i].rid > new_bdr_rid)) {
                bdr_priority = cands[i].priority;
                new_bdr_rid  = cands[i].rid;
            }
        }
    }

    /* Find IPs for the elected DR and BDR */
    uint32_t new_dr_ip  = 0;
    uint32_t new_bdr_ip = 0;
    for (size_t i = 0; i < nc; i++) {
        if (cands[i].rid == new_dr_rid)  new_dr_ip  = cands[i].ip;
        if (cands[i].rid == new_bdr_rid) new_bdr_ip = cands[i].ip;
    }

    printf("[ELECT] DR=%x BDR=%x\n", new_dr_ip, new_bdr_ip);
    iface->dr  = new_dr_ip;
    iface->bdr = new_bdr_ip;
}

/* =====================================================================
 * MAIN EVENT LOOP (skeleton)
 * ===================================================================== */

/*
 * A production OSPF daemon would use select()/epoll() multiplexing
 * raw sockets, with separate timer management. This skeleton shows
 * the structure.
 */
static void ospf_event_loop(ospf_instance_t *ospf) {
    time_t last_hello[MAX_INTERFACES] = {0};
    time_t last_dead_check = 0;
    uint8_t recv_buf[65536];

    printf("[OSPF] Starting event loop. Router ID: %x\n", ospf->router_id);

    while (1) {
        time_t now = time(NULL);

        /* Send Hellos on each interface */
        for (size_t i = 0; i < ospf->iface_count; i++) {
            ospf_iface_t *iface = &ospf->interfaces[i];
            if (now - last_hello[i] >= iface->hello_interval) {
                last_hello[i] = now;

                /* Collect neighbor RIDs */
                ospf_rid_t nbr_rids[MAX_NEIGHBORS];
                size_t     nbr_count = 0;
                for (ospf_neighbor_t *nbr = iface->neighbors;
                     nbr && nbr_count < MAX_NEIGHBORS;
                     nbr = nbr->next) {
                    if (nbr->state >= OSPF_NBR_INIT)
                        nbr_rids[nbr_count++] = nbr->rid;
                }

                size_t   pkt_len;
                uint8_t *pkt = ospf_build_hello(ospf, iface,
                                                nbr_rids, nbr_count,
                                                &pkt_len);
                if (pkt) {
                    /* In real code: sendto(iface->fd, pkt, pkt_len, ...)
                     * to 224.0.0.5 */
                    printf("[TX] Hello on %s (%zu bytes, %zu nbrs)\n",
                           iface->name, pkt_len, nbr_count);
                    free(pkt);
                }
            }
        }

        /* Check dead timers */
        if (now - last_dead_check >= 1) {
            last_dead_check = now;
            for (size_t i = 0; i < ospf->iface_count; i++) {
                ospf_check_dead_timers(&ospf->interfaces[i]);
            }
        }

        /* Receive and process packets (non-blocking in real impl) */
        /* [receive loop with select()/epoll() omitted for brevity] */

        usleep(100000); /* 100ms tick */
    }
}

/* =====================================================================
 * EXAMPLE / DEMO
 * ===================================================================== */

int main(void) {
    ospf_instance_t ospf = {0};

    /* Configure router */
    ospf.router_id   = rid_from_str("1.1.1.1");
    ospf.lsa_seqnum  = 0x80000001; /* RFC minimum start value */

    /* Configure interface */
    ospf.iface_count = 1;
    ospf_iface_t *iface = &ospf.interfaces[0];
    strncpy(iface->name, "eth0", sizeof(iface->name));
    inet_aton("192.168.1.1", &iface->ip);
    inet_aton("255.255.255.0", &iface->mask);
    iface->area_id        = 0x00000000; /* Area 0 */
    iface->net_type       = NET_BROADCAST;
    iface->cost           = 1;
    iface->priority       = 1;
    iface->hello_interval = DEFAULT_HELLO_INTERVAL;
    iface->dead_interval  = DEFAULT_DEAD_INTERVAL;
    iface->mtu            = 1500;

    /* Configure LSDB */
    ospf.lsdb_count = 1;
    ospf.lsdbs[0].area_id = 0x00000000;

    /* Demo: install a dummy Router LSA */
    ospf_router_link_t demo_links[2];
    /* Link 1: Transit network (Ethernet segment) */
    demo_links[0].link_id   = htonl(0xC0A80102); /* 192.168.1.2 = DR IP */
    demo_links[0].link_data = iface->ip.s_addr;
    demo_links[0].type      = LINK_TYPE_TRANSIT;
    demo_links[0].num_tos   = 0;
    demo_links[0].metric    = htons(1);
    /* Link 2: Stub loopback */
    demo_links[1].link_id   = rid_from_str("1.1.1.1");
    demo_links[1].link_data = htonl(0xFFFFFFFF); /* /32 mask */
    demo_links[1].type      = LINK_TYPE_STUB;
    demo_links[1].num_tos   = 0;
    demo_links[1].metric    = htons(0);

    size_t   lsa_len;
    uint8_t *rlsa = ospf_build_router_lsa(&ospf, iface->area_id,
                                           demo_links, 2, &lsa_len);
    if (rlsa) {
        ospf_lsa_header_t *hdr = (ospf_lsa_header_t *)rlsa;
        lsdb_install(&ospf.lsdbs[0], hdr,
                     rlsa + sizeof(ospf_lsa_header_t),
                     lsa_len - sizeof(ospf_lsa_header_t));
        printf("[LSDB] Installed Router LSA, length=%zu, seqnum=%x\n",
               lsa_len, ntohl(hdr->ls_seqnum));
        free(rlsa);
    }

    /* Demo: run SPF */
    spf_route_t routes[MAX_NODES];
    size_t route_count = 0;
    ospf_run_spf(&ospf, &ospf.lsdbs[0], routes, &route_count);

    printf("\n[RIB] Computed %zu routes:\n", route_count);
    for (size_t i = 0; i < route_count; i++) {
        char net_str[20], mask_str[20], nh_str[20];
        struct in_addr a;
        a.s_addr = routes[i].dest_net;  snprintf(net_str,  sizeof(net_str),  "%s", inet_ntoa(a));
        a.s_addr = routes[i].dest_mask; snprintf(mask_str, sizeof(mask_str), "%s", inet_ntoa(a));
        a.s_addr = routes[i].next_hop;  snprintf(nh_str,   sizeof(nh_str),   "%s", inet_ntoa(a));
        printf("  %s/%s via %s cost=%u\n",
               net_str, mask_str, nh_str, routes[i].cost);
    }

    /* Demo: simulate receiving a Hello from neighbor */
    uint8_t fake_hello[sizeof(ospf_hello_t) + 4];
    memset(fake_hello, 0, sizeof(fake_hello));
    ospf_hello_t *fh = (ospf_hello_t *)fake_hello;
    fh->hdr.version      = OSPF_VERSION;
    fh->hdr.type         = OSPF_TYPE_HELLO;
    fh->hdr.length       = htons(sizeof(fake_hello));
    fh->hdr.router_id    = rid_from_str("2.2.2.2");
    fh->hdr.area_id      = iface->area_id;
    fh->network_mask     = iface->mask.s_addr;
    fh->hello_interval   = htons(DEFAULT_HELLO_INTERVAL);
    fh->dead_interval    = htonl(DEFAULT_DEAD_INTERVAL);
    fh->rtr_priority     = 1;
    fh->neighbors[0]     = 0; /* R1 not listed yet */

    struct in_addr nbr_ip;
    inet_aton("192.168.1.2", &nbr_ip);
    printf("\n[SIM] Receiving Hello from 192.168.1.2 (RID 2.2.2.2)\n");
    ospf_process_hello(&ospf, iface, fh, nbr_ip);

    /* Now simulate R2 listing R1 in its next Hello */
    fh->neighbors[0] = ospf.router_id;
    printf("[SIM] Receiving Hello with our RID listed (→ 2-WAY)\n");
    ospf_process_hello(&ospf, iface, fh, nbr_ip);

    /* Show neighbor state */
    printf("\n[NBR TABLE] Interface %s:\n", iface->name);
    for (ospf_neighbor_t *nbr = iface->neighbors; nbr; nbr = nbr->next) {
        char rid_str[20];
        rid_to_str(nbr->rid, rid_str, sizeof(rid_str));
        printf("  RID=%-16s State=%-10s Priority=%u\n",
               rid_str, nbr_state_names[nbr->state], nbr->priority);
    }

    /* Cleanup */
    for (ospf_neighbor_t *nbr = iface->neighbors; nbr; ) {
        ospf_neighbor_t *next = nbr->next;
        free(nbr->req_list);
        free(nbr->rxmt_list);
        free(nbr);
        nbr = next;
    }
    for (int b = 0; b < LSDB_HASH_SIZE; b++) {
        for (lsdb_entry_t *e = ospf.lsdbs[0].buckets[b]; e; ) {
            lsdb_entry_t *next = e->next;
            free(e->body);
            free(e);
            e = next;
        }
    }

    return 0;
}
```

---

## 24. Rust Implementation

```rust
//! ospf_core.rs — OSPF Core Implementation in Rust
//!
//! Covers: packet structures, LSDB, neighbor FSM, Hello parsing,
//! SPF (Dijkstra), DR/BDR election, LSA checksum.
//!
//! Build: rustc ospf_core.rs -o ospf_core
//! Or with Cargo: add to src/main.rs

use std::collections::{BinaryHeap, HashMap};
use std::cmp::Ordering;
use std::net::Ipv4Addr;
use std::time::{Duration, Instant};

// =====================================================================
// CONSTANTS
// =====================================================================

const OSPF_VERSION: u8      = 2;
const OSPF_PROTO: u8        = 89;
const LSA_MAXAGE: u16       = 3600;
const LSA_REFRESH_TIME: u32 = 1800;
const OSPF_MAX_COST: u32    = u32::MAX;
const MIN_LSA_SEQNUM: i32   = -0x7FFFFFFF; // 0x80000001 as signed

// Packet types
const TYPE_HELLO: u8  = 1;
const TYPE_DBD: u8    = 2;
const TYPE_LSR: u8    = 3;
const TYPE_LSU: u8    = 4;
const TYPE_LSACK: u8  = 5;

// LSA types
const LSA_ROUTER: u8   = 1;
const LSA_NETWORK: u8  = 2;
const LSA_SUMMARY: u8  = 3;
const LSA_ASBR_SUM: u8 = 4;
const LSA_EXTERNAL: u8 = 5;
const LSA_NSSA: u8     = 7;

// Link types in Router LSA
const LINK_P2P: u8     = 1;
const LINK_TRANSIT: u8 = 2;
const LINK_STUB: u8    = 3;
const LINK_VIRTUAL: u8 = 4;

// =====================================================================
// TYPE ALIASES
// =====================================================================

type RouterId = u32;  // 32-bit, displayed as dotted-decimal
type AreaId   = u32;
type Ipv4Raw  = u32;  // network byte order u32

fn rid_to_str(rid: RouterId) -> String {
    let a = Ipv4Addr::from(rid.to_be_bytes());
    a.to_string()
}

fn str_to_rid(s: &str) -> RouterId {
    let a: Ipv4Addr = s.parse().unwrap();
    u32::from_be_bytes(a.octets())
}

// =====================================================================
// NEIGHBOR STATE
// =====================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum NbrState {
    Down     = 0,
    Attempt  = 1,
    Init     = 2,
    TwoWay   = 3,
    Exstart  = 4,
    Exchange = 5,
    Loading  = 6,
    Full     = 7,
}

impl std::fmt::Display for NbrState {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        let s = match self {
            NbrState::Down     => "DOWN",
            NbrState::Attempt  => "ATTEMPT",
            NbrState::Init     => "INIT",
            NbrState::TwoWay   => "2-WAY",
            NbrState::Exstart  => "EXSTART",
            NbrState::Exchange => "EXCHANGE",
            NbrState::Loading  => "LOADING",
            NbrState::Full     => "FULL",
        };
        write!(f, "{}", s)
    }
}

// =====================================================================
// NETWORK TYPE
// =====================================================================

#[derive(Debug, Clone, Copy, PartialEq)]
enum NetType {
    Broadcast,
    PointToPoint,
    Nbma,
    PointToMultipoint,
    Loopback,
}

// =====================================================================
// OSPF PACKET STRUCTURES
// =====================================================================

/// OSPF Common Header (24 bytes)
#[derive(Debug, Clone)]
struct OspfHeader {
    version:        u8,
    pkt_type:       u8,
    length:         u16,
    router_id:      RouterId,
    area_id:        AreaId,
    checksum:       u16,
    au_type:        u8,
    authentication: u64,
}

impl OspfHeader {
    fn new(pkt_type: u8, length: u16, router_id: RouterId, area_id: AreaId) -> Self {
        OspfHeader {
            version: OSPF_VERSION,
            pkt_type,
            length,
            router_id,
            area_id,
            checksum: 0,
            au_type: 0,
            authentication: 0,
        }
    }

    fn to_bytes(&self) -> Vec<u8> {
        let mut v = Vec::with_capacity(24);
        v.push(self.version);
        v.push(self.pkt_type);
        v.extend_from_slice(&self.length.to_be_bytes());
        v.extend_from_slice(&self.router_id.to_be_bytes());
        v.extend_from_slice(&self.area_id.to_be_bytes());
        v.extend_from_slice(&self.checksum.to_be_bytes());
        v.push(self.au_type);
        v.push(0u8); // pad
        v.extend_from_slice(&self.authentication.to_be_bytes());
        v
    }

    fn parse(buf: &[u8]) -> Option<Self> {
        if buf.len() < 24 { return None; }
        Some(OspfHeader {
            version:        buf[0],
            pkt_type:       buf[1],
            length:         u16::from_be_bytes([buf[2], buf[3]]),
            router_id:      u32::from_be_bytes([buf[4],buf[5],buf[6],buf[7]]),
            area_id:        u32::from_be_bytes([buf[8],buf[9],buf[10],buf[11]]),
            checksum:       u16::from_be_bytes([buf[12],buf[13]]),
            au_type:        buf[14],
            authentication: u64::from_be_bytes(
                buf[16..24].try_into().unwrap_or([0u8;8])
            ),
        })
    }
}

/// Hello Packet
#[derive(Debug, Clone)]
struct HelloPacket {
    header:          OspfHeader,
    network_mask:    u32,
    hello_interval:  u16,
    options:         u8,
    rtr_priority:    u8,
    dead_interval:   u32,
    dr:              Ipv4Raw,
    bdr:             Ipv4Raw,
    neighbors:       Vec<RouterId>,
}

impl HelloPacket {
    fn new(
        router_id: RouterId,
        area_id: AreaId,
        network_mask: u32,
        hello_interval: u16,
        dead_interval: u32,
        priority: u8,
        dr: Ipv4Raw,
        bdr: Ipv4Raw,
        neighbors: Vec<RouterId>,
    ) -> Self {
        let total_len = (24 + 20 + neighbors.len() * 4) as u16;
        HelloPacket {
            header: OspfHeader::new(TYPE_HELLO, total_len, router_id, area_id),
            network_mask,
            hello_interval,
            options: 0x02, // E bit
            rtr_priority: priority,
            dead_interval,
            dr,
            bdr,
            neighbors,
        }
    }

    fn to_bytes(&self) -> Vec<u8> {
        let mut v = self.header.to_bytes();
        v.extend_from_slice(&self.network_mask.to_be_bytes());
        v.extend_from_slice(&self.hello_interval.to_be_bytes());
        v.push(self.options);
        v.push(self.rtr_priority);
        v.extend_from_slice(&self.dead_interval.to_be_bytes());
        v.extend_from_slice(&self.dr.to_be_bytes());
        v.extend_from_slice(&self.bdr.to_be_bytes());
        for nbr in &self.neighbors {
            v.extend_from_slice(&nbr.to_be_bytes());
        }
        // Compute and inject checksum
        let csum = inet_checksum(&v);
        v[12] = (csum >> 8) as u8;
        v[13] = (csum & 0xFF) as u8;
        v
    }

    fn parse(buf: &[u8]) -> Option<Self> {
        if buf.len() < 44 { return None; }
        let header = OspfHeader::parse(buf)?;
        let total = header.length as usize;
        if buf.len() < total { return None; }

        let network_mask   = u32::from_be_bytes(buf[24..28].try_into().ok()?);
        let hello_interval = u16::from_be_bytes([buf[28], buf[29]]);
        let options        = buf[30];
        let rtr_priority   = buf[31];
        let dead_interval  = u32::from_be_bytes(buf[32..36].try_into().ok()?);
        let dr             = u32::from_be_bytes(buf[36..40].try_into().ok()?);
        let bdr            = u32::from_be_bytes(buf[40..44].try_into().ok()?);

        let nbr_count = (total - 44) / 4;
        let mut neighbors = Vec::with_capacity(nbr_count);
        for i in 0..nbr_count {
            let off = 44 + i * 4;
            neighbors.push(u32::from_be_bytes(buf[off..off+4].try_into().ok()?));
        }

        Some(HelloPacket {
            header, network_mask, hello_interval, options,
            rtr_priority, dead_interval, dr, bdr, neighbors,
        })
    }
}

// =====================================================================
// LSA STRUCTURES
// =====================================================================

/// LSA Header (20 bytes)
#[derive(Debug, Clone, PartialEq, Eq)]
struct LsaHeader {
    ls_age:        u16,
    options:       u8,
    ls_type:       u8,
    link_state_id: u32,
    adv_router:    RouterId,
    ls_seqnum:     i32,   // signed; 0x80000001 initial
    ls_checksum:   u16,
    length:        u16,
}

impl LsaHeader {
    fn new(ls_type: u8, link_state_id: u32, adv_router: RouterId,
           ls_seqnum: i32, length: u16) -> Self {
        LsaHeader {
            ls_age: 0,
            options: 0x02,
            ls_type,
            link_state_id,
            adv_router,
            ls_seqnum,
            ls_checksum: 0,
            length,
        }
    }

    fn to_bytes(&self) -> Vec<u8> {
        let mut v = Vec::with_capacity(20);
        v.extend_from_slice(&self.ls_age.to_be_bytes());
        v.push(self.options);
        v.push(self.ls_type);
        v.extend_from_slice(&self.link_state_id.to_be_bytes());
        v.extend_from_slice(&self.adv_router.to_be_bytes());
        v.extend_from_slice(&(self.ls_seqnum as u32).to_be_bytes());
        v.extend_from_slice(&self.ls_checksum.to_be_bytes());
        v.extend_from_slice(&self.length.to_be_bytes());
        v
    }

    fn parse(buf: &[u8]) -> Option<Self> {
        if buf.len() < 20 { return None; }
        Some(LsaHeader {
            ls_age:        u16::from_be_bytes([buf[0], buf[1]]),
            options:       buf[2],
            ls_type:       buf[3],
            link_state_id: u32::from_be_bytes(buf[4..8].try_into().ok()?),
            adv_router:    u32::from_be_bytes(buf[8..12].try_into().ok()?),
            ls_seqnum:     i32::from_be_bytes(buf[12..16].try_into().ok()?),
            ls_checksum:   u16::from_be_bytes([buf[16], buf[17]]),
            length:        u16::from_be_bytes([buf[18], buf[19]]),
        })
    }

    /// LSA identity key for LSDB lookup
    fn key(&self) -> LsaKey {
        LsaKey {
            ls_type:       self.ls_type,
            link_state_id: self.link_state_id,
            adv_router:    self.adv_router,
        }
    }

    /// Is this LSA newer than `other`?
    fn is_newer_than(&self, other: &LsaHeader) -> bool {
        lsa_compare(self, other) > 0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct LsaKey {
    ls_type:       u8,
    link_state_id: u32,
    adv_router:    RouterId,
}

/// Compare two LSA headers for newness.
/// Returns: >0 if a newer, <0 if b newer, 0 if same
fn lsa_compare(a: &LsaHeader, b: &LsaHeader) -> i32 {
    // Higher seqnum = newer
    if a.ls_seqnum != b.ls_seqnum {
        return a.ls_seqnum - b.ls_seqnum;
    }
    // Same seqnum: higher checksum
    if a.ls_checksum != b.ls_checksum {
        return a.ls_checksum as i32 - b.ls_checksum as i32;
    }
    // Same checksum: lower age = newer
    if a.ls_age != b.ls_age {
        return b.ls_age as i32 - a.ls_age as i32;
    }
    // MaxAge wins for flushing
    if a.ls_age == LSA_MAXAGE { return 1; }
    if b.ls_age == LSA_MAXAGE { return -1; }
    0
}

/// Router Link within a Router LSA
#[derive(Debug, Clone)]
struct RouterLink {
    link_id:   u32,
    link_data: u32,
    link_type: u8,
    metric:    u16,
}

/// Router LSA
#[derive(Debug, Clone)]
struct RouterLsa {
    header: LsaHeader,
    flags:  u8,   // B=0x01, E=0x02, V=0x04
    links:  Vec<RouterLink>,
}

impl RouterLsa {
    fn new(router_id: RouterId, seqnum: i32, flags: u8,
           links: Vec<RouterLink>) -> Self {
        let len = 20 + 4 + links.len() as u16 * 12;
        RouterLsa {
            header: LsaHeader::new(LSA_ROUTER, router_id, router_id, seqnum, len),
            flags,
            links,
        }
    }

    fn to_bytes(&self) -> Vec<u8> {
        let mut v = self.header.to_bytes();
        v.push(self.flags);
        v.push(0u8); // pad
        v.extend_from_slice(&(self.links.len() as u16).to_be_bytes());
        for link in &self.links {
            v.extend_from_slice(&link.link_id.to_be_bytes());
            v.extend_from_slice(&link.link_data.to_be_bytes());
            v.push(link.link_type);
            v.push(0u8); // num_tos = 0
            v.extend_from_slice(&link.metric.to_be_bytes());
        }
        // Apply Fletcher checksum (skip bytes 0-1 = ls_age)
        fletcher16_lsa(&mut v);
        v
    }

    fn parse(buf: &[u8]) -> Option<Self> {
        if buf.len() < 24 { return None; }
        let header = LsaHeader::parse(buf)?;
        let flags = buf[20];
        let num_links = u16::from_be_bytes([buf[22], buf[23]]) as usize;
        if buf.len() < 24 + num_links * 12 { return None; }
        let mut links = Vec::with_capacity(num_links);
        for i in 0..num_links {
            let off = 24 + i * 12;
            links.push(RouterLink {
                link_id:   u32::from_be_bytes(buf[off..off+4].try_into().ok()?),
                link_data: u32::from_be_bytes(buf[off+4..off+8].try_into().ok()?),
                link_type: buf[off+8],
                metric:    u16::from_be_bytes([buf[off+10], buf[off+11]]),
            });
        }
        Some(RouterLsa { header, flags, links })
    }
}

/// Network LSA
#[derive(Debug, Clone)]
struct NetworkLsa {
    header:           LsaHeader,
    network_mask:     u32,
    attached_routers: Vec<RouterId>,
}

impl NetworkLsa {
    fn new(dr_ip: u32, dr_rid: RouterId, network_mask: u32,
           attached: Vec<RouterId>, seqnum: i32) -> Self {
        let len = 20 + 4 + attached.len() as u16 * 4;
        NetworkLsa {
            header: LsaHeader::new(LSA_NETWORK, dr_ip, dr_rid, seqnum, len),
            network_mask,
            attached_routers: attached,
        }
    }

    fn to_bytes(&self) -> Vec<u8> {
        let mut v = self.header.to_bytes();
        v.extend_from_slice(&self.network_mask.to_be_bytes());
        for r in &self.attached_routers {
            v.extend_from_slice(&r.to_be_bytes());
        }
        fletcher16_lsa(&mut v);
        v
    }
}

// =====================================================================
// LSDB
// =====================================================================

#[derive(Debug, Clone)]
struct LsdbEntry {
    header:    LsaHeader,
    body:      Vec<u8>,
    recv_time: Instant,
}

#[derive(Debug)]
struct Lsdb {
    area_id: AreaId,
    entries: HashMap<LsaKey, LsdbEntry>,
}

impl Lsdb {
    fn new(area_id: AreaId) -> Self {
        Lsdb { area_id, entries: HashMap::new() }
    }

    /// Install an LSA. Returns true if installed (newer), false if stale.
    fn install(&mut self, header: LsaHeader, body: Vec<u8>) -> bool {
        let key = header.key();
        if let Some(existing) = self.entries.get(&key) {
            if lsa_compare(&header, &existing.header) <= 0 {
                return false; // existing is same or newer
            }
        }
        self.entries.insert(key, LsdbEntry {
            header,
            body,
            recv_time: Instant::now(),
        });
        true
    }

    fn lookup(&self, key: &LsaKey) -> Option<&LsdbEntry> {
        self.entries.get(key)
    }

    fn all_router_lsas(&self) -> Vec<&LsdbEntry> {
        self.entries.values()
            .filter(|e| e.header.ls_type == LSA_ROUTER)
            .collect()
    }

    /// Age out MaxAge LSAs (would also trigger flood in real impl)
    fn purge_maxage(&mut self) {
        let now = Instant::now();
        self.entries.retain(|_, e| {
            let age = e.header.ls_age as u64
                    + now.duration_since(e.recv_time).as_secs();
            age < LSA_MAXAGE as u64
        });
    }

    fn count(&self) -> usize {
        self.entries.len()
    }
}

// =====================================================================
// NEIGHBOR
// =====================================================================

#[derive(Debug)]
struct Neighbor {
    rid:         RouterId,
    src_ip:      Ipv4Raw,
    state:       NbrState,
    priority:    u8,
    dr:          Ipv4Raw,
    bdr:         Ipv4Raw,
    dd_seqnum:   u32,
    is_master:   bool,
    last_hello:  Instant,
    req_list:    Vec<LsaKey>,    // LSAs we need from neighbor
    rxmt_list:   Vec<LsaHeader>, // LSAs we sent, waiting for ACK
}

impl Neighbor {
    fn new(rid: RouterId, src_ip: Ipv4Raw, priority: u8) -> Self {
        Neighbor {
            rid,
            src_ip,
            state:      NbrState::Down,
            priority,
            dr:         0,
            bdr:        0,
            dd_seqnum:  0,
            is_master:  false,
            last_hello: Instant::now(),
            req_list:   Vec::new(),
            rxmt_list:  Vec::new(),
        }
    }

    fn change_state(&mut self, new_state: NbrState) {
        println!("[FSM] Neighbor {}: {} → {}",
                 rid_to_str(self.rid), self.state, new_state);
        self.state = new_state;
    }

    fn is_dead(&self, dead_interval: u32) -> bool {
        self.last_hello.elapsed() > Duration::from_secs(dead_interval as u64)
    }
}

// =====================================================================
// INTERFACE
// =====================================================================

#[derive(Debug)]
struct Interface {
    name:           String,
    ip:             Ipv4Raw,
    mask:           Ipv4Raw,
    area_id:        AreaId,
    net_type:       NetType,
    cost:           u16,
    priority:       u8,
    hello_interval: u16,
    dead_interval:  u32,
    dr:             Ipv4Raw,
    bdr:            Ipv4Raw,
    mtu:            u16,
    neighbors:      Vec<Neighbor>,
}

impl Interface {
    fn new(name: &str, ip: Ipv4Raw, mask: Ipv4Raw, area_id: AreaId,
           net_type: NetType, cost: u16, priority: u8) -> Self {
        Interface {
            name:           name.to_string(),
            ip, mask, area_id, net_type, cost, priority,
            hello_interval: 10,
            dead_interval:  40,
            dr:             0,
            bdr:            0,
            mtu:            1500,
            neighbors:      Vec::new(),
        }
    }

    fn find_neighbor_mut(&mut self, rid: RouterId) -> Option<&mut Neighbor> {
        self.neighbors.iter_mut().find(|n| n.rid == rid)
    }

    fn find_neighbor(&self, rid: RouterId) -> Option<&Neighbor> {
        self.neighbors.iter().find(|n| n.rid == rid)
    }

    fn process_hello(&mut self, ospf_rid: RouterId, hello: &HelloPacket) {
        let sender_rid = hello.header.router_id;
        let src_ip     = hello.dr; // simplified; real code uses IP layer src

        // Parameter checks
        if hello.network_mask != self.mask {
            println!("[HELLO] Mask mismatch, ignoring");
            return;
        }
        if hello.hello_interval != self.hello_interval {
            println!("[HELLO] Hello interval mismatch");
            return;
        }
        if hello.dead_interval != self.dead_interval {
            println!("[HELLO] Dead interval mismatch");
            return;
        }

        // Create or update neighbor
        if self.find_neighbor(sender_rid).is_none() {
            let nbr = Neighbor::new(sender_rid, src_ip, hello.rtr_priority);
            self.neighbors.push(nbr);
        }

        let nbr_idx = self.neighbors.iter()
            .position(|n| n.rid == sender_rid)
            .unwrap();

        self.neighbors[nbr_idx].last_hello = Instant::now();
        self.neighbors[nbr_idx].priority   = hello.rtr_priority;
        self.neighbors[nbr_idx].dr         = hello.dr;
        self.neighbors[nbr_idx].bdr        = hello.bdr;

        // State transitions
        if self.neighbors[nbr_idx].state == NbrState::Down {
            self.neighbors[nbr_idx].change_state(NbrState::Init);
        }

        let seen_by_nbr = hello.neighbors.contains(&ospf_rid);

        if seen_by_nbr && self.neighbors[nbr_idx].state == NbrState::Init {
            self.neighbors[nbr_idx].change_state(NbrState::TwoWay);

            // Decide adjacency
            let form_adj = match self.net_type {
                NetType::PointToPoint | NetType::PointToMultipoint => true,
                NetType::Broadcast | NetType::Nbma => {
                    let we_dr   = self.dr  == self.ip;
                    let we_bdr  = self.bdr == self.ip;
                    let nbr_dr  = hello.dr  == sender_rid;
                    let nbr_bdr = hello.bdr == sender_rid;
                    we_dr || we_bdr || nbr_dr || nbr_bdr
                }
                _ => false,
            };

            if form_adj {
                let is_master = ospf_rid > sender_rid;
                self.neighbors[nbr_idx].is_master  = is_master;
                self.neighbors[nbr_idx].dd_seqnum  = 1000; // random in practice
                self.neighbors[nbr_idx].change_state(NbrState::Exstart);
                println!("[DBD] EXSTART: we are {}",
                         if is_master { "MASTER" } else { "SLAVE" });
            }
        } else if !seen_by_nbr
               && self.neighbors[nbr_idx].state >= NbrState::TwoWay {
            self.neighbors[nbr_idx].change_state(NbrState::Init);
        }
    }

    fn check_dead_neighbors(&mut self) {
        let dead_int = self.dead_interval;
        let dead_rids: Vec<RouterId> = self.neighbors.iter()
            .filter(|n| n.state != NbrState::Down && n.is_dead(dead_int))
            .map(|n| n.rid)
            .collect();
        for rid in dead_rids {
            if let Some(nbr) = self.find_neighbor_mut(rid) {
                println!("[TIMER] Neighbor {} DEAD", rid_to_str(rid));
                nbr.change_state(NbrState::Down);
            }
        }
        self.neighbors.retain(|n| n.state != NbrState::Down);
    }
}

// =====================================================================
// DR/BDR ELECTION
// =====================================================================

struct DrElection {
    rid:          RouterId,
    ip:           Ipv4Raw,
    priority:     u8,
    declared_dr:  Ipv4Raw,
    declared_bdr: Ipv4Raw,
}

fn elect_dr_bdr(
    my_rid: RouterId, my_ip: Ipv4Raw, my_priority: u8,
    my_dr: Ipv4Raw, my_bdr: Ipv4Raw,
    neighbors: &[&Neighbor],
) -> (Ipv4Raw, Ipv4Raw) {
    let mut candidates: Vec<DrElection> = vec![
        DrElection { rid: my_rid, ip: my_ip, priority: my_priority,
                     declared_dr: my_dr, declared_bdr: my_bdr }
    ];
    for nbr in neighbors {
        if nbr.state >= NbrState::TwoWay && nbr.priority > 0 {
            candidates.push(DrElection {
                rid:          nbr.rid,
                ip:           nbr.src_ip,
                priority:     nbr.priority,
                declared_dr:  nbr.dr,
                declared_bdr: nbr.bdr,
            });
        }
    }

    // Elect BDR: highest priority not claiming to be DR
    let bdr_winner = candidates.iter()
        .filter(|c| c.declared_dr != c.ip)
        .max_by(|a, b| {
            a.priority.cmp(&b.priority)
             .then(a.rid.cmp(&b.rid))
        });
    let bdr_ip = bdr_winner.map(|c| c.ip).unwrap_or(0);
    let bdr_rid = bdr_winner.map(|c| c.rid).unwrap_or(0);

    // Elect DR: highest priority claiming to be DR
    let dr_contestants: Vec<_> = candidates.iter()
        .filter(|c| c.declared_dr == c.ip)
        .collect();

    let (dr_ip, dr_rid) = if dr_contestants.is_empty() {
        // BDR becomes DR; re-elect BDR
        let new_dr_ip  = bdr_ip;
        let new_bdr = candidates.iter()
            .filter(|c| c.ip != new_dr_ip)
            .max_by(|a, b| a.priority.cmp(&b.priority).then(a.rid.cmp(&b.rid)));
        let new_bdr_ip = new_bdr.map(|c| c.ip).unwrap_or(0);
        return (new_dr_ip, new_bdr_ip);
    } else {
        let winner = dr_contestants.iter()
            .max_by(|a, b| a.priority.cmp(&b.priority).then(a.rid.cmp(&b.rid)))
            .unwrap();
        (winner.ip, winner.rid)
    };

    println!("[ELECT] DR={} BDR={}",
             Ipv4Addr::from(dr_ip.to_be_bytes()),
             Ipv4Addr::from(bdr_ip.to_be_bytes()));
    (dr_ip, bdr_ip)
}

// =====================================================================
// CHECKSUMS
// =====================================================================

fn inet_checksum(data: &[u8]) -> u16 {
    let mut sum = 0u32;
    let mut i = 0;
    while i + 1 < data.len() {
        sum += u16::from_be_bytes([data[i], data[i+1]]) as u32;
        i += 2;
    }
    if i < data.len() {
        sum += (data[i] as u32) << 8;
    }
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    !(sum as u16)
}

/// Fletcher-16 checksum for LSAs (RFC 905)
/// Applied over bytes [2..len] (skipping ls_age bytes 0-1)
/// Result written at bytes [16, 17] of LSA (ls_checksum field)
fn fletcher16_lsa(lsa: &mut Vec<u8>) {
    // Zero checksum bytes
    lsa[16] = 0;
    lsa[17] = 0;

    let (mut c0, mut c1): (i32, i32) = (0, 0);
    for b in &lsa[2..] {
        c0 = (c0 + *b as i32) % 255;
        c1 = (c1 + c0)        % 255;
    }

    // Checksum byte offsets within the portion starting at byte 2
    let x_pos = 16 - 2; // ls_checksum[0] offset from byte 2
    let y_pos = 17 - 2; // ls_checksum[1] offset from byte 2
    let len = (lsa.len() - 2) as i32;

    let mut x = ((len - x_pos as i32 - 1) * c0 - c1) % 255;
    if x <= 0 { x += 255; }
    let y = 510 - c0 - x;
    let y = if y > 255 { y - 255 } else { y };

    lsa[16] = x as u8;
    lsa[17] = y as u8;
}

// =====================================================================
// SPF (DIJKSTRA)
// =====================================================================

/// SPF candidate list entry (for BinaryHeap)
#[derive(Debug, Clone, Eq, PartialEq)]
struct Candidate {
    cost:     u32,
    node_id:  RouterId,
    next_hop: Ipv4Raw,
    parent:   Option<RouterId>,
}

impl Ord for Candidate {
    fn cmp(&self, other: &Self) -> Ordering {
        // Min-heap: reverse ordering
        other.cost.cmp(&self.cost)
            .then(other.node_id.cmp(&self.node_id))
    }
}
impl PartialOrd for Candidate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// SPF result entry
#[derive(Debug)]
struct SpfRoute {
    dest_net:   u32,
    dest_mask:  u32,
    cost:       u32,
    next_hop:   Ipv4Raw,
    adv_router: RouterId,
}

/// Run Dijkstra's SPF on the LSDB.
/// Returns a list of routes (stub networks reachable from root).
fn run_spf(lsdb: &Lsdb, root: RouterId) -> Vec<SpfRoute> {
    let mut shortest: HashMap<RouterId, (u32, Ipv4Raw)> = HashMap::new();
    let mut heap     = BinaryHeap::new();
    let mut routes   = Vec::new();

    // Initialize
    heap.push(Candidate {
        cost:     0,
        node_id:  root,
        next_hop: 0,
        parent:   None,
    });

    while let Some(curr) = heap.pop() {
        // Skip if already settled
        if shortest.contains_key(&curr.node_id) { continue; }
        shortest.insert(curr.node_id, (curr.cost, curr.next_hop));

        // Look up this router's LSA
        let key = LsaKey {
            ls_type:       LSA_ROUTER,
            link_state_id: curr.node_id,
            adv_router:    curr.node_id,
        };
        let entry = match lsdb.lookup(&key) {
            Some(e) => e,
            None    => continue,
        };

        // Parse Router LSA body
        let lsa = match RouterLsa::parse(&{
            let mut full = entry.header.to_bytes();
            full.extend_from_slice(&entry.body);
            full
        }) {
            Some(l) => l,
            None    => continue,
        };

        for link in &lsa.links {
            let link_cost = curr.cost.saturating_add(link.metric as u32);

            match link.link_type {
                LINK_P2P => {
                    // Neighbor's RID = link_id
                    let nbr_rid = link.link_id;
                    if !shortest.contains_key(&nbr_rid) {
                        let next_hop = if curr.node_id == root {
                            link.link_data // Local interface IP = next hop
                        } else {
                            curr.next_hop
                        };
                        heap.push(Candidate {
                            cost:     link_cost,
                            node_id:  nbr_rid,
                            next_hop,
                            parent:   Some(curr.node_id),
                        });
                    }
                }
                LINK_STUB => {
                    // Stub network = destination route
                    routes.push(SpfRoute {
                        dest_net:   link.link_id,
                        dest_mask:  link.link_data,
                        cost:       link_cost,
                        next_hop:   if curr.node_id == root { 0 } else { curr.next_hop },
                        adv_router: curr.node_id,
                    });
                }
                LINK_TRANSIT => {
                    // Find the DR's Network LSA, then all attached routers
                    let net_key = LsaKey {
                        ls_type:       LSA_NETWORK,
                        link_state_id: link.link_id, // DR interface IP
                        adv_router:    link.link_id, // simplified
                    };
                    if let Some(net_entry) = lsdb.lookup(&net_key) {
                        // Each attached router connected via pseudo-node (cost 0)
                        let n_rids = parse_network_lsa_routers(&net_entry.body);
                        for nbr_rid in n_rids {
                            if nbr_rid != curr.node_id
                               && !shortest.contains_key(&nbr_rid) {
                                let next_hop = if curr.node_id == root {
                                    link.link_data
                                } else {
                                    curr.next_hop
                                };
                                heap.push(Candidate {
                                    cost:     link_cost, // +0 from pseudo-node
                                    node_id:  nbr_rid,
                                    next_hop,
                                    parent:   Some(curr.node_id),
                                });
                            }
                        }
                    }
                }
                _ => {}
            }
        }
    }

    println!("\n[SPF] Tree rooted at {}:", rid_to_str(root));
    for (rid, (cost, nh)) in &shortest {
        println!("  {} cost={} next_hop={}",
                 rid_to_str(*rid), cost,
                 Ipv4Addr::from(nh.to_be_bytes()));
    }

    routes
}

fn parse_network_lsa_routers(body: &[u8]) -> Vec<RouterId> {
    // Body: 4-byte mask + N*4-byte router IDs
    if body.len() < 4 { return vec![]; }
    let count = (body.len() - 4) / 4;
    (0..count).filter_map(|i| {
        let off = 4 + i * 4;
        body.get(off..off+4)
            .and_then(|b| b.try_into().ok())
            .map(u32::from_be_bytes)
    }).collect()
}

// =====================================================================
// OSPF INSTANCE
// =====================================================================

struct OspfInstance {
    router_id:   RouterId,
    lsa_seqnum:  i32,
    interfaces:  Vec<Interface>,
    lsdbs:       Vec<Lsdb>,
}

impl OspfInstance {
    fn new(router_id: &str) -> Self {
        OspfInstance {
            router_id:  str_to_rid(router_id),
            lsa_seqnum: MIN_LSA_SEQNUM,
            interfaces: Vec::new(),
            lsdbs:      Vec::new(),
        }
    }

    fn next_seqnum(&mut self) -> i32 {
        let s = self.lsa_seqnum;
        self.lsa_seqnum = self.lsa_seqnum.wrapping_add(1);
        s
    }

    fn add_interface(&mut self, iface: Interface) {
        let area_id = iface.area_id;
        self.interfaces.push(iface);
        if !self.lsdbs.iter().any(|db| db.area_id == area_id) {
            self.lsdbs.push(Lsdb::new(area_id));
        }
    }

    fn lsdb_for_area_mut(&mut self, area_id: AreaId) -> Option<&mut Lsdb> {
        self.lsdbs.iter_mut().find(|db| db.area_id == area_id)
    }

    fn lsdb_for_area(&self, area_id: AreaId) -> Option<&Lsdb> {
        self.lsdbs.iter().find(|db| db.area_id == area_id)
    }

    fn originate_router_lsa(&mut self, area_id: AreaId) {
        let seqnum = self.next_seqnum();
        let rid    = self.router_id;

        // Collect links from all interfaces in this area
        let links: Vec<RouterLink> = self.interfaces.iter()
            .filter(|i| i.area_id == area_id)
            .flat_map(|iface| {
                let mut ls = Vec::new();
                // Stub: loopback or no neighbor
                ls.push(RouterLink {
                    link_id:   iface.ip,
                    link_data: iface.mask,
                    link_type: LINK_STUB,
                    metric:    iface.cost,
                });
                // Transit: if DR exists on broadcast interface
                if iface.net_type == NetType::Broadcast && iface.dr != 0 {
                    ls.push(RouterLink {
                        link_id:   iface.dr,
                        link_data: iface.ip,
                        link_type: LINK_TRANSIT,
                        metric:    iface.cost,
                    });
                }
                ls
            })
            .collect();

        let rlsa = RouterLsa::new(rid, seqnum, 0, links);
        let bytes = rlsa.to_bytes();

        if let Some(db) = self.lsdb_for_area_mut(area_id) {
            let hdr = rlsa.header.clone();
            let body = bytes[20..].to_vec();
            if db.install(hdr, body) {
                println!("[LSA] Originated Router LSA, seqnum=0x{:08x}, \
                          len={}", seqnum as u32, bytes.len());
            }
        }
    }

    fn print_lsdb(&self, area_id: AreaId) {
        if let Some(db) = self.lsdb_for_area(area_id) {
            println!("\n[LSDB] Area {} ({} entries):",
                     rid_to_str(area_id), db.count());
            for (key, entry) in &db.entries {
                println!("  Type={} LSID={} AdvRtr={} Seq=0x{:08x} Age={}",
                         key.ls_type,
                         rid_to_str(key.link_state_id),
                         rid_to_str(key.adv_router),
                         entry.header.ls_seqnum as u32,
                         entry.header.ls_age);
            }
        }
    }

    fn run_spf_for_area(&self, area_id: AreaId) -> Vec<SpfRoute> {
        if let Some(db) = self.lsdb_for_area(area_id) {
            run_spf(db, self.router_id)
        } else {
            vec![]
        }
    }
}

// =====================================================================
// MAIN / DEMO
// =====================================================================

fn main() {
    println!("=== OSPF Rust Implementation Demo ===\n");

    // Create OSPF instance
    let mut ospf = OspfInstance::new("10.0.0.1");
    println!("[INIT] Router ID: {}", rid_to_str(ospf.router_id));

    // Add an interface
    let iface = Interface::new(
        "eth0",
        str_to_rid("192.168.1.1"),  // interface IP
        str_to_rid("255.255.255.0"), // mask
        0x00000000,                  // Area 0
        NetType::Broadcast,
        10,  // cost
        1,   // priority
    );
    ospf.add_interface(iface);

    // Originate a Router LSA
    ospf.originate_router_lsa(0x00000000);

    // Simulate receiving a Router LSA from neighbor 10.0.0.2
    let neighbor_links = vec![
        RouterLink {
            link_id:   str_to_rid("192.168.1.1"),  // DR IP
            link_data: str_to_rid("192.168.1.2"),  // neighbor's iface IP
            link_type: LINK_TRANSIT,
            metric:    10,
        },
        RouterLink {
            link_id:   str_to_rid("10.1.1.0"),     // stub net
            link_data: str_to_rid("255.255.255.0"),
            link_type: LINK_STUB,
            metric:    1,
        },
    ];
    let mut fake_seqnum: i32 = MIN_LSA_SEQNUM;
    let nbr_lsa = RouterLsa::new(str_to_rid("10.0.0.2"), fake_seqnum, 0, neighbor_links);
    let nbr_bytes = nbr_lsa.to_bytes();
    let nbr_hdr = LsaHeader::parse(&nbr_bytes).unwrap();
    let nbr_body = nbr_bytes[20..].to_vec();

    if let Some(db) = ospf.lsdb_for_area_mut(0) {
        let installed = db.install(nbr_hdr, nbr_body);
        println!("[LSDB] Neighbor Router LSA installed: {}", installed);
    }

    // Print LSDB
    ospf.print_lsdb(0);

    // Run SPF
    let routes = ospf.run_spf_for_area(0);
    println!("\n[RIB] SPF Routing Table ({} routes):", routes.len());
    for r in &routes {
        println!("  {}/{} via {} cost={} (adv: {})",
                 Ipv4Addr::from(r.dest_net.to_be_bytes()),
                 Ipv4Addr::from(r.dest_mask.to_be_bytes()),
                 Ipv4Addr::from(r.next_hop.to_be_bytes()),
                 r.cost,
                 rid_to_str(r.adv_router));
    }

    // Simulate Hello exchange FSM
    println!("\n=== Neighbor FSM Demo ===");
    let mut iface = Interface::new(
        "eth0",
        str_to_rid("192.168.1.1"),
        str_to_rid("255.255.255.0"),
        0x00000000,
        NetType::Broadcast,
        10, 1,
    );

    // First Hello from neighbor (R1 not in neighbor list)
    let hello1 = HelloPacket::new(
        str_to_rid("10.0.0.2"),  // sender RID
        0,                         // area
        str_to_rid("255.255.255.0"),
        10,   // hello interval
        40,   // dead interval
        1,    // priority
        0,    // DR (none yet)
        0,    // BDR (none yet)
        vec![], // no neighbors listed
    );
    println!("\n[SIM] Receiving Hello from 10.0.0.2 (not listing us):");
    iface.process_hello(ospf.router_id, &hello1);

    // Second Hello listing R1 → should go to 2-WAY
    let hello2 = HelloPacket::new(
        str_to_rid("10.0.0.2"),
        0,
        str_to_rid("255.255.255.0"),
        10, 40, 1,
        0, 0,
        vec![ospf.router_id], // now lists R1
    );
    println!("\n[SIM] Receiving Hello listing our RID (→ 2-WAY/EXSTART):");
    iface.process_hello(ospf.router_id, &hello2);

    // Print neighbor table
    println!("\n[NBR TABLE] Interface {}:", iface.name);
    for nbr in &iface.neighbors {
        println!("  RID={:<16} State={:<10} Priority={}",
                 rid_to_str(nbr.rid), nbr.state, nbr.priority);
    }

    // DR/BDR election demo
    println!("\n=== DR/BDR Election Demo ===");
    let nbr_refs: Vec<&Neighbor> = iface.neighbors.iter().collect();
    let (dr, bdr) = elect_dr_bdr(
        ospf.router_id,
        str_to_rid("192.168.1.1"),
        1,  // our priority
        0, 0,
        &nbr_refs,
    );
    println!("[RESULT] Elected DR={} BDR={}",
             Ipv4Addr::from(dr.to_be_bytes()),
             Ipv4Addr::from(bdr.to_be_bytes()));

    // Verify Hello serialization
    println!("\n=== Hello Packet Serialization ===");
    let test_hello = HelloPacket::new(
        ospf.router_id, 0,
        str_to_rid("255.255.255.0"),
        10, 40, 1, dr, bdr,
        vec![str_to_rid("10.0.0.2")],
    );
    let bytes = test_hello.to_bytes();
    println!("[TX] Hello packet: {} bytes", bytes.len());
    print!("[TX] Hex: ");
    for (i, b) in bytes.iter().enumerate() {
        if i < 32 { print!("{:02x} ", b); }
    }
    println!("...");

    // Verify parsing round-trip
    if let Some(parsed) = HelloPacket::parse(&bytes) {
        println!("[RX] Parsed back: RID={} hello_int={} dead_int={} nbrs={}",
                 rid_to_str(parsed.header.router_id),
                 parsed.hello_interval,
                 parsed.dead_interval,
                 parsed.neighbors.len());
    }

    // Fletcher checksum verification
    println!("\n=== LSA Checksum Verification ===");
    let test_links = vec![RouterLink {
        link_id: str_to_rid("192.168.1.0"),
        link_data: str_to_rid("255.255.255.0"),
        link_type: LINK_STUB,
        metric: 10,
    }];
    let test_lsa = RouterLsa::new(ospf.router_id, MIN_LSA_SEQNUM, 0, test_links);
    let lsa_bytes = test_lsa.to_bytes();
    println!("[LSA] Router LSA: {} bytes, checksum bytes=[0x{:02x}, 0x{:02x}]",
             lsa_bytes.len(), lsa_bytes[16], lsa_bytes[17]);

    println!("\n=== Demo Complete ===");
}
```

---

## 25. Troubleshooting and Debug Mindset

### The Diagnostic Hierarchy

When OSPF isn't working, always follow this hierarchy:

```
  1. PHYSICAL LAYER
     ─────────────
     Interface up/up? IP addresses? Duplex mismatch?
     
  2. HELLO PARAMETERS
     ─────────────────
     Mismatched Hello interval, Dead interval, or area?
     → Neighbors stay in INIT or never form
     
     Command: debug ip ospf hello
     Look for: "Mismatched hello parameters"
  
  3. NEIGHBOR STATE
     ──────────────
     Stuck in INIT?  → One-way communication (ACL, multicast issue)
     Stuck in 2-WAY? → Not DR/BDR on broadcast network (normal for DROther)
     Stuck in EXSTART? → MTU mismatch (DBD packets getting fragmented)
     Stuck in EXCHANGE? → MTU mismatch or access-list blocking
     Stuck in LOADING? → LSA corruption or filtering
  
  4. LSDB CONSISTENCY
     ─────────────────
     Show ip ospf database on both routers — should be identical
     Check for missing LSAs or different sequence numbers
     
     Type 3 LSAs from an unexpected ABR → routing loop possible
  
  5. ROUTING TABLE
     ──────────────
     Route in LSDB but not in routing table?
     → Route might be less preferred than existing route
     → Check AD (administrative distance): OSPF=110
     → Another protocol might be winning
  
  6. FORWARDING
     ──────────
     Route in routing table but traffic not flowing?
     → FIB/CEF issue, hardware programming
     → Access-list blocking
     → RPF check failing (for multicast)
```

### Common OSPF Problems and Root Causes

| Symptom | Probable Cause | Diagnostic Command |
|---------|---------------|-------------------|
| Neighbor stuck in INIT | One-way communication, ACL blocking OSPF | `debug ip ospf hello` |
| Neighbor stuck in EXSTART | MTU mismatch | `ip ospf mtu-ignore` (workaround) |
| Neighbor flapping | Hello/Dead timer mismatch, unstable link | `debug ip ospf adj` |
| Missing routes | Area type mismatch, summarization | `show ip ospf database` |
| Suboptimal routing | Cost not configured correctly | `show ip ospf interface` |
| High CPU during convergence | SPF thrashing, no throttle | `show processes cpu` + tune SPF timers |
| Route not in table despite LSDB | AD conflict (BGP/static preferred) | `show ip route` |
| Type 5 LSAs in stub area | Router not configured as stub | Check options byte in Hello |

### Key Show Commands (Cisco IOS)

```
  show ip ospf neighbor                → Neighbor states and DR/BDR
  show ip ospf neighbor detail         → Full neighbor info (timers, etc.)
  show ip ospf interface               → Interface OSPF config (Hello interval, cost, DR/BDR)
  show ip ospf database                → LSDB summary (all LSA types)
  show ip ospf database router         → All Router LSAs
  show ip ospf database network        → All Network LSAs
  show ip ospf database summary        → All Summary (Type 3) LSAs
  show ip ospf database external       → All External (Type 5) LSAs
  show ip ospf database router adv-router X.X.X.X → Specific router's LSA
  show ip ospf statistics              → SPF run counts, timing
  show ip route ospf                   → OSPF routes in RIB
```

---

## 26. Mental Model Summary

Understanding OSPF at depth means internalizing these conceptual pillars:

```
  ┌───────────────────────────────────────────────────────────────┐
  │                    OSPF MENTAL MODEL                          │
  │                                                               │
  │  PILLAR 1: CONSISTENT DISTRIBUTED MAP                         │
  │  ─────────────────────────────────                            │
  │  All routers in an area share an identical LSDB.              │
  │  LSA flooding with reliable acknowledgment enforces this.     │
  │  SPF is just an independent computation on this shared map.   │
  │                                                               │
  │  PILLAR 2: EVENTS AND REACTIONS                               │
  │  ──────────────────────────────                               │
  │  Every OSPF action is event-driven:                           │
  │  • Hello received → update neighbor state                     │
  │  • New/updated LSA → flood it, schedule SPF                   │
  │  • Neighbor down → re-originate Router LSA, run SPF           │
  │  • Timer fires → send Hello / retransmit LSU / age LSA        │
  │                                                               │
  │  PILLAR 3: TWO-LEVEL HIERARCHY                                │
  │  ────────────────────────────                                 │
  │  Intra-area: full topology, Dijkstra, precise                 │
  │  Inter-area: summarized, distance-vector-like via ABR         │
  │  External: redistributed, Type 5/7 carry external info        │
  │  Area 0 backbone enforces loop-freedom at inter-area level    │
  │                                                               │
  │  PILLAR 4: RELIABILITY WITHOUT TCP                            │
  │  ─────────────────────────────────                            │
  │  OSPF implements its own reliable delivery:                   │
  │  • Retransmission lists + timers for unACKed LSUs             │
  │  • Explicit LSAck (direct or delayed/batched)                 │
  │  • Sequence numbers prevent replay and detect stale LSAs      │
  │                                                               │
  │  PILLAR 5: SCALABILITY THROUGH AGGREGATION                    │
  │  ──────────────────────────────────────────                   │
  │  Areas limit Type 1/2 flooding scope                          │
  │  ABR summarization hides internal detail                      │
  │  Stub/NSSA areas further reduce LSDB size                     │
  │  DR/BDR on broadcast reduces O(N²) flooding to O(N)          │
  │                                                               │
  │  PILLAR 6: FAST CONVERGENCE PIPELINE                          │
  │  ────────────────────────────────────                         │
  │  BFD detects failure (50ms)                                   │
  │  → OSPF notified immediately (no Dead Interval wait)          │
  │  → SPF start delay (50ms, for LSA bundling)                   │
  │  → LSA flood reaches all routers                              │
  │  → SPF runs (~10-50ms depending on topology)                  │
  │  → Routes installed in RIB/FIB                                │
  │  Total with BFD: <200ms for most topologies                   │
  └───────────────────────────────────────────────────────────────┘
```

### The OSPF Invariants to Always Keep in Mind

1. **LSDB identity per area**: If two routers in the same area have different LSDBs, routing is inconsistent. This is always a bug — find the cause.

2. **Area 0 required**: All areas must connect to Area 0, directly or via virtual link. Violation = routing loops.

3. **DR non-preemptive**: The DR stays as DR until it fails. Higher-priority newcomer doesn't unseat the DR.

4. **SPF loop freedom**: Because all routers compute SPF from the same LSDB, the computed trees are guaranteed loop-free within an area. Inter-area can loop if ABR design violates rules.

5. **Sequence number monotonicity**: An LSA's sequence number must always increase on re-origination. Decreasing = stale LSA rejected. Wrap-around is handled via MaxAge flushing before sequence rollover.

6. **MaxAge = withdrawal**: The universal mechanism to remove an LSA from all databases. Setting Age=3600 and flooding causes global deletion.

7. **Cost asymmetry is valid but dangerous**: OSPF supports different costs in each direction (A→B=1, B→A=100). This can cause traffic to take non-intuitive paths or even suboptimal asymmetric routing. In practice, keep costs symmetric.

---

*This guide covers OSPFv2 per RFC 2328, OSPFv3 per RFC 5340, OSPF-TE per RFC 3630, OSPF Authentication per RFC 5709, LFA per RFC 5286, and the NSSA extension per RFC 3101.*

*For production OSPF daemon implementations, refer to: FRRouting (frrouting.org), BIRD, OpenOSPFd.*