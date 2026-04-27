# Protocol Independent Multicast (PIM): Complete Technical Reference

> **Kernel version context:** Primary references are Linux 6.8/6.9 (net-next).  
> Version-dependent behaviors are flagged explicitly.  
> Source paths are relative to the kernel tree root.

---

## Table of Contents

1. [IP Multicast Foundations](#1-ip-multicast-foundations)
2. [PIM Protocol Overview](#2-pim-protocol-overview)
3. [PIM-DM: Dense Mode](#3-pim-dm-dense-mode)
4. [PIM-SM: Sparse Mode](#4-pim-sm-sparse-mode)
5. [Rendezvous Point Mechanisms](#5-rendezvous-point-mechanisms)
6. [PIM-SSM: Source-Specific Multicast](#6-pim-ssm-source-specific-multicast)
7. [PIM-BIDIR: Bidirectional PIM](#7-pim-bidir-bidirectional-pim)
8. [IGMP and MLD Integration](#8-igmp-and-mld-integration)
9. [Linux Kernel Multicast Routing Architecture](#9-linux-kernel-multicast-routing-architecture)
10. [Kernel Data Structures Deep Dive](#10-kernel-data-structures-deep-dive)
11. [Multicast Forwarding Cache (MFC)](#11-multicast-forwarding-cache-mfc)
12. [PIM Packet Processing in the Kernel](#12-pim-packet-processing-in-the-kernel)
13. [Virtual Interfaces (VIF)](#13-virtual-interfaces-vif)
14. [IPv6 Multicast and PIM6](#14-ipv6-multicast-and-pim6)
15. [Userspace Daemon Interaction (SIOCADDMRT/mrouted/FRR)](#15-userspace-daemon-interaction)
16. [PIM State Machines](#16-pim-state-machines)
17. [Assert Mechanism](#17-assert-mechanism)
18. [PIM Packet Formats](#18-pim-packet-formats)
19. [Debugging and Tracing](#19-debugging-and-tracing)
20. [eBPF and XDP for Multicast](#20-ebpf-and-xdp-for-multicast)
21. [Configuration Reference](#21-configuration-reference)
22. [Security Considerations](#22-security-considerations)
23. [Performance Tuning](#23-performance-tuning)

---

## 1. IP Multicast Foundations

### 1.1 Multicast Addressing

IP multicast uses Class D addresses: `224.0.0.0/4` (IPv4) and `ff00::/8` (IPv6).

```
IPv4 Multicast Address Space:
 ┌─────────────────────────────────────────────────────────────┐
 │  1110xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx  (224.0.0.0/4)         │
 │                                                             │
 │  224.0.0.0/24   - Local Network Control Block (TTL=1)       │
 │    224.0.0.1    - All hosts on subnet                       │
 │    224.0.0.2    - All routers on subnet                     │
 │    224.0.0.5    - OSPF all routers                          │
 │    224.0.0.6    - OSPF DR/BDR                               │
 │    224.0.0.13   - PIM routers                               │
 │    224.0.0.22   - IGMPv3 (All MLDv2-capable routers)        │
 │                                                             │
 │  224.0.1.0/24   - Internetwork Control Block                │
 │    224.0.1.1    - NTP                                       │
 │                                                             │
 │  232.0.0.0/8    - Source-Specific Multicast (SSM)           │
 │  233.0.0.0/8    - GLOP Addressing (RFC 3180)                │
 │  234.0.0.0/8    - Unicast-Prefix-Based (RFC 3306)           │
 │  239.0.0.0/8    - Organization-Local Scope                  │
 └─────────────────────────────────────────────────────────────┘

IPv6 Multicast Address Space (ff00::/8):
 ┌─────────────────────────────────────────────────────────────┐
 │  ff|flgs|scop|group-id  (16 bytes total)                    │
 │                                                             │
 │  Flags (4 bits):  0RPT                                      │
 │    R: Rendezvous Point embedded                             │
 │    P: Unicast-Prefix-Based                                  │
 │    T: 0=well-known, 1=transient                             │
 │                                                             │
 │  Scope (4 bits):                                            │
 │    0x1 = Interface-local                                    │
 │    0x2 = Link-local                                         │
 │    0x4 = Admin-local                                        │
 │    0x5 = Site-local                                         │
 │    0x8 = Organization-local                                 │
 │    0xe = Global                                             │
 │                                                             │
 │  ff02::d  = All PIM routers (link-local)                    │
 │  ff02::16 = MLDv2-capable routers                           │
 │  ff3e::/32 = SSM range (global scope)                       │
 └─────────────────────────────────────────────────────────────┘
```

### 1.2 Ethernet MAC Mapping

IPv4 multicast maps to Ethernet MAC `01:00:5e:xx:xx:xx`:

```
  IPv4:   1110 0000 . 0001 0000 . 0000 0001 . 0000 0001
                                   ^^^^^^^^   ^^^^^^^^
  MAC:    01:00:5e:  0001 0000  . 0000 0001 . 0000 0001
                     (low 23 bits of IPv4 mapped directly)

  Note: 5 bits are lost → 32:1 address ambiguity
  e.g., 224.1.1.1 and 225.1.1.1 map to same MAC 01:00:5e:01:01:01
```

IPv6 uses `33:33:xx:xx:xx:xx` (last 32 bits of IPv6 address).

**Kernel path:** `include/linux/if_ether.h`, `net/ethernet/eth.c:eth_header()`  
**MAC computation:** `net/ipv4/ipmr.c`, `ip_mr_forward()` → `dev_queue_xmit()`

### 1.3 Multicast Distribution Tree Types

```
  Shared Tree (RPT - Rooted at RP):
  ══════════════════════════════════
                      RP
                     /|\
                    / | \
                   R1 R2 R3
                  /       \
                R4         R5
               /             \
            Source           Receiver

  Source Tree (SPT - Shortest Path Tree):
  ════════════════════════════════════════
            Source
              |
              R1
             / \
            R2  R3
           /     \
         R4       R5
          \       /
           Receivers

  (S,G) entry: Specific source, specific group
  (*,G) entry: Any source, specific group (used with RPT)
```

### 1.4 Reverse Path Forwarding (RPF)

RPF is the fundamental anti-loop mechanism. A router forwards a multicast packet on an interface only if the packet arrived on the interface that the router would use to reach the source (or RP for *,G).

```
RPF Check Logic:
═════════════════
  1. Packet arrives on iif
  2. Lookup unicast routing table for source address (S) or RP (for *,G)
  3. If best route to S/RP is via iif → RPF passes → forward to OIL
  4. If best route to S/RP is NOT via iif → RPF fails → drop packet

  Kernel implementation:
  net/ipv4/ipmr.c: ipmr_find_mfc() → ipmr_cache_report() [upcall on miss]
  net/ipv4/route.c: ip_route_input_slow() → ip_multicast_rpf_check() [v6.1+]
```

---

## 2. PIM Protocol Overview

### 2.1 PIM Variants Comparison

```
  ┌───────────────┬──────────────┬──────────────┬─────────────┬──────────────┐
  │ Feature       │  PIM-DM      │  PIM-SM      │  PIM-SSM    │  PIM-BIDIR   │
  ├───────────────┼──────────────┼──────────────┼─────────────┼──────────────┤
  │ RFC           │  3973        │  7761        │  4607       │  5015        │
  │ Tree type     │  SPT only    │  RPT + SPT   │  SPT only   │  BIDIR tree  │
  │ RP needed     │  No          │  Yes         │  No         │  Yes(DF-RP)  │
  │ IGMP version  │  v1/v2/v3    │  v1/v2/v3    │  v3 only    │  v1/v2/v3    │
  │ State type    │  (S,G)       │  (*,G),(S,G) │  (S,G)      │  (*,G,rpt)   │
  │ Scalability   │  Poor        │  Good        │  Excellent  │  Good        │
  │ Source regs.  │  No          │  Yes         │  No         │  No          │
  │ Prune delay   │  Yes (3s)    │  No          │  No         │  No          │
  │ Use case      │  Dense       │  General     │  1-to-many  │  Many-to-many│
  └───────────────┴──────────────┴──────────────┴─────────────┴──────────────┘
```

### 2.2 PIM Message Types (RFC 7761)

```
  PIM Header (always):
  ┌─────────┬─────────┬───────────────────────────────────────┐
  │ Ver (4) │ Type(4) │            Reserved (8)               │
  ├─────────┴─────────┴───────────────────────────────────────┤
  │                    Checksum (16)                          │
  └───────────────────────────────────────────────────────────┘

  Type values:
  ┌──────┬────────────────────────────────┬──────────────────┐
  │ Type │ Message                        │ Destination      │
  ├──────┼────────────────────────────────┼──────────────────┤
  │  0   │ Hello                          │ 224.0.0.13       │
  │  1   │ Register                       │ Unicast to RP    │
  │  2   │ Register-Stop                  │ Unicast to DR    │
  │  3   │ Join/Prune                     │ Upstream neighbor│
  │  4   │ Bootstrap (BSR)                │ 224.0.0.13       │
  │  5   │ Assert                         │ 224.0.0.13       │
  │  6   │ Graft (DM only)                │ Upstream neighbor│
  │  7   │ Graft-Ack (DM only)            │ Unicast          │
  │  8   │ Candidate-RP-Advertisement     │ Unicast to BSR   │
  │  9   │ State-Refresh (DM only)        │ 224.0.0.13       │
  │  10  │ DF Election (BIDIR)            │ 224.0.0.13       │
  │  12  │ PFM (ECMP, RFC 7761 §4.9)      │ 224.0.0.13       │
  └──────┴────────────────────────────────┴──────────────────┘
```

### 2.3 PIM Hello Mechanism

Hello messages are sent every `Hello_Period` (default 30s) to:
- Discover PIM neighbors
- Elect the Designated Router (DR)
- Negotiate holdtime and options

```
PIM Hello Option TLVs:
  ┌─────────────────┬──────────────────────────────────────────┐
  │ Option Type (2B)│ Description                              │
  ├─────────────────┼──────────────────────────────────────────┤
  │  1              │ Holdtime (default 3.5 × Hello_Period)    │
  │  2              │ LAN Prune Delay (T, propagation_delay,   │
  │                 │   override_interval)                     │
  │  19             │ DR Priority (default 1)                  │
  │  20             │ Generation ID (random, changes on reset) │
  │  24             │ Address List (secondary addresses)       │
  │  25             │ Bidirectional Capable                    │
  └─────────────────┴──────────────────────────────────────────┘

DR Election (on LAN):
  - Highest DR Priority wins
  - Tie: Highest IP address wins
  - If any neighbor does NOT send DR Priority option → revert to IP-only comparison
```

---

## 3. PIM-DM: Dense Mode

### 3.1 Flood and Prune Operation

PIM-DM assumes all routers want multicast traffic. It floods first, then prunes.

```
  Phase 1: Flood (t=0)
  ═════════════════════
  Source S sends to group G.
  
  S ──→ R1 ──→ R2 ──→ R3 ──→ Receiver
              │
              └──→ R4 (no receivers)
  
  R1 creates (S,G) state, forwards on all PIM interfaces except RPF iif.
  R4 receives, has no downstream receivers.
  
  Phase 2: Prune (t=0 + prune_delay)
  ═════════════════════════════════════
  R4 sends Prune(S,G) upstream to R1.
  R1 starts PruneTimer (default 210s).
  
  After PruneTimer expires → re-flood.
  
  Phase 3: State Refresh (RFC 4601, optional)
  ═════════════════════════════════════════════
  First-hop router (R1) sends State-Refresh every State_Refresh_Interval (60s).
  Refreshes (S,G) Prune state → avoids re-flooding.
  
  Assert: When multiple routers on same LAN receive same traffic,
  Assert winner continues forwarding; loser sets Assert state.
```

### 3.2 PIM-DM State Machine (per interface per (S,G))

```
  Downstream Interface FSM:
  
        +-------------------+
        |  NoInfo (NI)      |◄────────────────────────────────┐
        +-------------------+                                  │
              │                                                │
              │ [Receive Prune(S,G)]                           │
              ▼                                                │
        +-------------------+    [PruneTimer expires]         │
        │  Pruned (P)       │ ─────────────────────────────── ┘
        +-------------------+
              │
              │ [Receive Join(S,G) OR
              │  Receive Graft(S,G)]
              ▼
        +-------------------+
        │  PrunePending(PP) │
        +-------------------+
              │
              │ [PrunePendingTimer expires]
              ▼
        +-------------------+
        │  Pruned (P)       │
        +-------------------+
```

---

## 4. PIM-SM: Sparse Mode

PIM-SM (RFC 7761, obsoletes RFC 4601) is the dominant protocol. It assumes receivers must explicitly join.

### 4.1 Complete Join/Register Flow

```
Network Topology:
═════════════════
     S (10.1.1.1)
     │
  [eth0] DR1 (First-Hop Router) [10.1.1.254]
     │
  [Internet / Core]
     │
  [eth1] RP  (Rendezvous Point) [10.0.0.1]
     │
  [eth2] R2
     │
  [eth3] DR2 (Last-Hop Router) [10.2.2.254]
     │
     R (Receiver, subscribed to G=239.1.1.1)

═══════════════════════════════════════════════════════
Step-by-step flow for first packet from S to G:
═══════════════════════════════════════════════════════

[1] Receiver sends IGMP Membership Report for 239.1.1.1
    DR2 creates (*,G) state, sends Join(*,G) upstream toward RP
    
[2] Join(*,G) propagates hop-by-hop toward RP
    Each router creates (*,G) state and adds interface to OIL
    
    DR2 → R2 → RP : Join(*,G) [RPF toward RP]
    
[3] Source S sends first packet to 239.1.1.1
    DR1 receives packet:
      - No (S,G) entry yet
      - Encapsulates in PIM Register message
      - Unicasts Register to RP
    
[4] RP receives Register:
      - Decapsulates inner packet
      - Forwards toward receivers via (*,G) tree
      - Creates (S,G,rpt) state
      
[5] RP sends Join(S,G) upstream toward source S (RPF toward S)
    RP → [core] → DR1 : Join(S,G)
    This builds the (S,G) SPT from RP toward S
    
[6] Once native traffic reaches RP via (S,G) SPT:
      - RP sends Register-Stop to DR1
      - DR1 stops encapsulating
      - Traffic flows S → DR1 → [SPT to RP] → [RPT to receivers]
    
[7] SPT Switchover (at DR2, last-hop):
    DR2 measures traffic rate from RP-RPT path
    If rate > SPT_Threshold (default 0 bps in most impls):
      - DR2 sends Join(S,G) toward S (RPF toward S)
      - Builds direct SPT: S → DR1 → [core] → DR2 → R
      - DR2 sends Prune(S,G,rpt) toward RP
      - (*,G) path for this source is pruned from DR2
```

### 4.2 PIM-SM State Entries

```
  (*,G) Entry [Shared Tree]:
  ┌──────────────────────────────────────────────────────────┐
  │  RP address                                              │
  │  Upstream state: Joined / NotJoined                      │
  │  Upstream RPF neighbor (toward RP)                       │
  │  Upstream Join/Prune timer                               │
  │  OIL (Outgoing Interface List):                          │
  │    - Interface, downstream join state, assert state      │
  └──────────────────────────────────────────────────────────┘

  (S,G) Entry [Source Tree]:
  ┌──────────────────────────────────────────────────────────┐
  │  Source address S                                        │
  │  Group address G                                         │
  │  Upstream state: Joined / Pruned / NotJoined             │
  │  Upstream RPF neighbor (toward S)                        │
  │  SPT bit: indicates SPT has been established             │
  │  Local membership: any local receivers?                  │
  │  OIL:                                                    │
  │    - Interface, downstream join state, assert state      │
  └──────────────────────────────────────────────────────────┘

  (S,G,rpt) Entry [Source on Shared Tree - Prune Override]:
  ┌──────────────────────────────────────────────────────────┐
  │  Prune state: Pruned / Not-Pruned                        │
  │  Override timer                                          │
  │  Used when source traffic should NOT use RPT             │
  └──────────────────────────────────────────────────────────┘
```

### 4.3 Designated Router Election

```
DR Election Timeline on LAN segment:
═════════════════════════════════════

t=0:    All routers boot, send Hello with Gen-ID, DR-Priority
        
  R1: Hello [pri=100, gen_id=0xDEAD, holdtime=105]
  R2: Hello [pri=100, gen_id=0xBEEF, holdtime=105]  ← higher IP → wins
  R3: Hello [pri=50,  gen_id=0xCAFE, holdtime=105]  ← lower priority

Election rules (in order):
  1. Highest DR Priority (if all neighbors support option 19)
  2. If tie in priority: highest IP address
  3. If any neighbor missing priority option: highest IP wins regardless

DR responsibilities:
  - Send IGMP Queries (also handled by IGMP separately)
  - Register source traffic to RP (first-hop DR)
  - Send Join(*,G) upstream for local receivers (last-hop DR)
  - Track (S,G) state for local sources

Non-DR behavior:
  - Listens to IGMP reports (for Assert fallback)
  - Maintains neighbor state
  - Participates in Join/Prune (can override DR on assert loss)
```

### 4.4 SPT Switchover Mechanism (RFC 7761 §4.2.1)

```
SPT Switchover Decision at Last-Hop Router (DR2):
══════════════════════════════════════════════════

Condition: DR2 is receiving traffic for (S,G) via (*,G) RPT path.
DR2 evaluates: should it switch to direct SPT?

Standard trigger (from RFC):
  KeepaliveTimer(S,G): reset whenever (S,G) traffic arrives
  If KeepaliveTimer expires → source inactive → no SPT switchover

FRRouting/pimd implementation uses bandwidth threshold:
  - Default: 0 kbps (immediate switchover on first packet)
  - Configurable: ip pim spt-switchover infinity-and-beyond [prefix-list]

Sequence:
  1. DR2 receives (S,G) packet via (*,G) OIL
  2. DR2 installs (S,G) entry with iif = RPF-iif(S)
  3. DR2 sends Join(S,G) upstream toward S
  4. SPT builds: S → ... → DR2
  5. DR2 now receives packets on correct iif (SPT) AND wrong iif (RPT)
  6. DR2 sends Prune(S,G,rpt) toward RP on (*,G) path
     This is encoded in same J/P message: Join(S,G) + Prune(S,G,rpt)
  7. RP prunes DR2 from (S,G) RPT OIL
  8. DR2 only receives via SPT now

Kernel-side: The (S,G) MFC entry iif field is updated when SPT established.
  net/ipv4/ipmr.c: ipmr_mfc_add() → mfc_cache.mfc_parent updated
```

---

## 5. Rendezvous Point Mechanisms

### 5.1 Static RP Configuration

```
Simplest deployment: all routers configured with same RP address.

  # FRRouting (vtysh):
  router pim
   rp 10.0.0.1 224.0.0.0/4
   
  # Linux kernel side: RP info is maintained in userspace daemon
  # Kernel only sees Join/Prune decisions from daemon via MRT socket
```

### 5.2 Bootstrap Router (BSR) Mechanism (RFC 5059)

BSR automates RP discovery across a PIM domain without Anycast.

```
BSR Election and RP Distribution:
═══════════════════════════════════

Phase 1: BSR Election
─────────────────────
  All Candidate-BSRs (C-BSR) send Bootstrap messages.
  Bootstrap msg: {BSR-address, BSR-priority, BSR-hash-mask}
  
  Election: highest priority wins. Tie → highest IP.
  
  Bootstrap messages flood through PIM domain:
    - Each router forwards Bootstrap on all PIM interfaces except RPF(BSR)
    - Suppression: router only forwards if received Bootstrap is "better"

Phase 2: Candidate-RP Advertisement
─────────────────────────────────────
  Each Candidate-RP (C-RP) unicasts C-RP-Adv to elected BSR:
    {RP-address, group-prefix, priority, holdtime}
  
  BSR collects all C-RP-Advs into RP-Set.

Phase 3: RP-Set Distribution  
──────────────────────────────
  BSR embeds RP-Set in Bootstrap messages → floods domain.
  Each router receives RP-Set and applies hash to select RP per group.

Phase 4: RP Selection (Hash Function)
───────────────────────────────────────
  For group G, among RPs covering G's prefix:
  
  value(G, M, RP_i) = [1103515245 × ((1103515245 × (G & M) + 12345)
                        XOR RP_i) + 12345] mod 2^31
  
  Where M = BSR hash mask (e.g., /30 → 0xFFFFFFFC)
  Highest value wins.
  
  Purpose of mask: groups within same /30 map to same RP → 
  improves locality, reduces RP load variance.

BSR Message Format:
┌──────────────────────────────────────────────────────────────┐
│ Fragment Tag (2B) │ Hash Mask Len (1B) │ BSR Priority (1B)   │
├──────────────────────────────────────────────────────────────┤
│                    BSR Address (Encoded Unicast)              │
├──────────────────────────────────────────────────────────────┤
│ Group Address (Encoded Group) │ RP Count (1B) │ Frag RP Cnt  │
├──────────────────────────────────────────────────────────────┤
│              RP Address (Encoded Unicast)                     │
│              Holdtime (2B) │ RP Priority (1B) │ Reserved      │
│              ... (repeat for each RP)                        │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Auto-RP (Cisco proprietary, widely deployed)

```
Auto-RP uses two well-known multicast groups:
  224.0.1.39 - Cisco-RP-Announce (C-RP sends to MA)
  224.0.1.40 - Cisco-RP-Discovery (MA sends RP mappings)

MA = Mapping Agent (analogous to BSR)

Flow:
  C-RP1 → Announce(224.0.1.39) → MA selects highest-priority RP per group
  MA → Discovery(224.0.1.40) → all routers learn RP mappings

Problem: chicken-and-egg
  To receive 224.0.1.40, routers need RP info.
  Solution: "sparse-dense" mode OR configure static RP for 224.0.1.39/40

FRR supports Auto-RP in receive-only mode.
pimd has fuller support.
```

### 5.4 Anycast-RP (RFC 4610)

```
Multiple routers share same RP IP address. Used for RP redundancy + load sharing.

            Anycast-RP Set: {RP1: 10.0.0.1/32, RP2: 10.0.0.1/32}
            Physical:        RP1 = 10.0.0.2,    RP2 = 10.0.0.3

  Source S1 (near RP1):      Source S2 (near RP2):
  DR1 registers to RP1       DR2 registers to RP2
  
  Problem: Receiver joined at RP2, source registered at RP1.
  
  Solution: Anycast-RP peers exchange Register messages:
    RP1 receives Register(S1,G) from DR1
    RP1 → unicasts Register(S1,G) to RP2 (MSDP or RFC 4610 mechanism)
    RP2 has (*,G) state → forwards to receivers
    RP2 sends Join(S1,G) toward S1 → RP1 gets Join → SPT forms
    
  RFC 4610 (PIM-based Anycast RP):
    - No MSDP needed
    - RP1 encapsulates and forwards Register to each Anycast-RP peer
    - Simpler than MSDP for single-domain

MSDP (Multicast Source Discovery Protocol, RFC 3618):
  Used for inter-domain multicast (between PIM-SM domains).
  Each domain's RP participates in MSDP peering.
  SA (Source Active) messages: {S, G, RP}
  Legacy protocol, largely replaced by PIM-SSM in modern designs.
```

---

## 6. PIM-SSM: Source-Specific Multicast

### 6.1 SSM Overview (RFC 4607)

SSM eliminates the RP entirely. Receivers specify both group AND source.

```
SSM Channel: (S, G) where G ∈ 232.0.0.0/8 (IPv4) or ff3x::/32 (IPv6)

Traditional ASM flow:             SSM flow:
──────────────────────────────    ──────────────────────────────────
1. Receiver joins (*,G)           1. Receiver sends IGMPv3 INCLUDE(S,G)
2. Traffic goes via RP            2. DR sends Join(S,G) directly toward S
3. Optional SPT switchover        3. SPT built immediately
4. RP is single point of failure  4. No RP, no Register, no RPT

Benefits:
  - No RP complexity
  - No inter-domain RP coordination
  - Built-in source authentication (RPF enforces source address)
  - Linear scaling
  - No MSDP needed

Requirement: IGMPv3 on last-hop segment (for source specification)
  MLDv2 for IPv6

Kernel requirement: IGMPv3 source filtering via socket option
  setsockopt(sock, IPPROTO_IP, IP_ADD_SOURCE_MEMBERSHIP, ...)
  Struct: ip_mreq_source { imr_multiaddr, imr_interface, imr_sourceaddr }
```

### 6.2 IGMPv3 Source Filtering

```
IGMPv3 Group Record Types:
  MODE_IS_INCLUDE(S1,S2)  → receive only from listed sources
  MODE_IS_EXCLUDE(S1,S2)  → receive from all EXCEPT listed sources
  CHANGE_TO_INCLUDE(S)    → leave group except for S
  CHANGE_TO_EXCLUDE(S)    → join group except for S  
  ALLOW_NEW_SOURCES(S)    → add sources to current filter
  BLOCK_OLD_SOURCES(S)    → remove sources from current filter

For SSM:
  - Only INCLUDE records matter
  - Router receives INCLUDE(S,G) → installs (S,G) join
  - DR sends PIM Join(S,G) upstream

Kernel socket API path:
  net/ipv4/igmp.c: ip_mc_source() 
  → igmp_send_report() 
  → ip_mc_join_group_ssm()
  
  Relevant structures:
  include/linux/igmp.h: ip_mc_socklist, ip_sf_socklist
  net/ipv4/igmp.c: ip_mc_msfilter (per-socket multicast source filter)
```

---

## 7. PIM-BIDIR: Bidirectional PIM

### 7.1 BIDIR Concept

BIDIR creates a bidirectional shared tree. Traffic flows toward AND away from RP.

```
ASM/SM Tree (Unidirectional):         BIDIR Tree:
══════════════════════════════════════════════════════════

Sources send TOWARD RP (Register or SPT)    Sources send on same tree as distribution
Receivers receive FROM RP (RPT or SPT)      Both directions use same shared tree

  S1 → RP → R                               S1
  S2 → RP → R                               │
                                             RP ── R
                                             │
                                             S2

BIDIR Benefits:
  - No (S,G) state at RP (only (*,G,bidir))
  - No Register messages
  - Scales to many sources (O(G) state instead of O(S×G))
  - Ideal for many-to-many conferencing

BIDIR Limitations:
  - Traffic from sources travels UP toward RP even if receivers are closer
  - Suboptimal for widely distributed sources
  - No SPT switchover possible
```

### 7.2 Designated Forwarder (DF) Election

BIDIR requires a DF per RP per link to prevent loops on the upstream path.

```
DF Election (RFC 5015 §3.3):
════════════════════════════

For each RP address, on each link, one router is elected DF.
The DF is responsible for forwarding traffic TOWARD RP on that link.

Election process: Modified assert mechanism using DF Election messages.
  Type 10 (PIM DF Election):
    ┌─────────────────────────────────────────────────────┐
    │ RP Address │ Metric Pref │ Metric │ DF Election Data │
    └─────────────────────────────────────────────────────┘
  
  Sub-types:
    Offer:   "I could be DF, my metric to RP is M"
    Winner:  "I am the DF winner"
    Backoff: "I'm backing off, winner is W"
    Pass:    "I'm passing DF role to you" (graceful handover)
  
  Winner selection: best unicast route metric to RP.
  Tie-break: highest IP address.

DF role on link:
  DF: forwards multicast from downstream sources toward RP
  Non-DF: must NOT forward upstream (would create duplicates)
  
  Non-DF receiving traffic from downstream source:
    → drops it (DF will handle)
  
  DF receiving traffic from upstream (toward receivers):
    → forwards downstream normally
```

---

## 8. IGMP and MLD Integration

### 8.1 IGMP Version Comparison

```
  ┌──────────────┬──────────────┬──────────────┬──────────────┐
  │ Feature      │   IGMPv1     │   IGMPv2     │   IGMPv3     │
  ├──────────────┼──────────────┼──────────────┼──────────────┤
  │ RFC          │  1112        │  2236        │  3376        │
  │ Leave group  │  No          │  Yes         │  Yes         │
  │ Src filter   │  No          │  No          │  Yes         │
  │ SSM support  │  No          │  No          │  Yes         │
  │ Querier elec │  No          │  Yes         │  Yes         │
  │ Spec. query  │  No          │  Yes         │  Yes         │
  │ Robustness   │  No          │  Param.      │  Param.      │
  └──────────────┴──────────────┴──────────────┴──────────────┘

IGMPv3 Report message (sent to 224.0.0.22):
  ┌────────────────────────────────────────────────┐
  │ Type=0x22 │ Reserved │ Checksum                │
  ├────────────────────────────────────────────────┤
  │ Reserved  │ Number of Group Records             │
  ├────────────────────────────────────────────────┤
  │ Record Type │ Aux Len │ Number of Sources       │
  │ Multicast Address                               │
  │ Source Address [0]                              │
  │ Source Address [1]                              │
  │ ... (up to Number of Sources)                   │
  │ Auxiliary Data (Aux Len × 4 bytes)              │
  └────────────────────────────────────────────────┘
```

### 8.2 IGMP Kernel Implementation

```
Key files:
  net/ipv4/igmp.c          - IGMP protocol implementation
  include/linux/igmp.h     - IGMP structures
  net/ipv4/ip_sockglue.c   - Socket options (IP_ADD_MEMBERSHIP etc.)

Key functions:
  igmp_rcv()               - Receive IGMP messages (Protocol 2)
  igmp_heard_query()       - Process Query from querier
  igmp_heard_report()      - Process Report from host
  igmp_send_report()       - Send IGMP report
  ip_mc_join_group()       - Join multicast group (socket op)
  ip_mc_leave_group()      - Leave multicast group

Key structures:
  struct ip_mc_list {        // Per-interface per-group state
      struct in_device *interface;
      __be32 multiaddr;
      struct ip_sf_list *sources;     // IGMPv3 source list
      struct ip_sf_list *tomb;        // Sources being removed
      unsigned int sfmode;            // MCAST_INCLUDE/EXCLUDE
      unsigned long sfcount[2];
      union { struct ip_msfilter *sflist; } ifs;
      struct timer_list timer;        // IGMP report timer
      int users;
      atomic_t refcnt;
      spinlock_t lock;
      char tm_running;
      char reporter;
      char unsolicit_count;
      char loaded;
      unsigned char gsquery;
      unsigned char crcount;
      struct rcu_head rcu;
  };

  struct in_device {         // net/core/inetdev.c
      ...
      struct ip_mc_list __rcu *mc_list;  // linked list of mc groups
      ...
  };

IGMP querier election:
  igmp_heard_query():
    if received query source < our address:
      become non-querier, start other_querier_present timer
    else:
      stay as querier
  
  Timer expiry → become querier again, restart sending queries.
```

### 8.3 MLD (Multicast Listener Discovery) for IPv6

```
MLD is the IPv6 equivalent of IGMP, implemented as ICMPv6 messages.

  MLDv1 (RFC 2710) ≈ IGMPv2
  MLDv2 (RFC 3810) ≈ IGMPv3

Key files:
  net/ipv6/mcast.c         - MLD implementation
  include/net/if_inet6.h   - IPv6 multicast structures

MLDv2 uses source address ::  (unspecified) for reports
  (prevents routing of MLD messages)

  struct ifmcaddr6 {         // Per-interface per-group (IPv6)
      struct in6_addr mca_addr;
      struct inet6_dev *idev;
      struct ifmcaddr6 *next;
      struct ip6_sf_list *mca_sources;
      struct ip6_sf_list *mca_tomb;
      unsigned int mca_sfmode;
      unsigned char mca_crcount;
      unsigned long mca_sfcount[2];
      struct delayed_work mca_work;
      unsigned int mca_flags;
      int mca_users;
      atomic_t mca_refcnt;
      spinlock_t mca_lock;
      unsigned long mca_cstamp;
      unsigned long mca_tstamp;
  };
```

---

## 9. Linux Kernel Multicast Routing Architecture

### 9.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USERSPACE                                        │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │    pimd      │  │  FRRouting   │  │  smcrouted   │                  │
│  │  (RFC 7761)  │  │ (pim daemon) │  │  (static MC) │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         └────────────┬────┘                  │                          │
│                      │  SIOCADDMRT / MRT socket                         │
│                      │  (PF_INET, SOCK_RAW, IPPROTO_IGMP)               │
└──────────────────────┼──────────────────────────────────────────────────┘
                       │ [MRT_INIT, MRT_ADD_VIF, MRT_ADD_MFC, ...]
┌──────────────────────┼──────────────────────────────────────────────────┐
│                   KERNEL SPACE                                          │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                  net/ipv4/ipmr.c                               │     │
│  │                                                                │     │
│  │  ipmr_socket (per netns)    VIF Table (MAXVIFS=32 by default) │     │
│  │  ┌────────────────┐         ┌─────┬─────┬─────┬──── ─ ─ ─ ┐  │     │
│  │  │ mr_table       │         │VIF0 │VIF1 │VIF2 │ ...        │  │     │
│  │  │ .mroute_sk     │         │eth0 │eth1 │tunl0│            │  │     │
│  │  │ .vif_table[]   │         └─────┴─────┴─────┴──── ─ ─ ─ ┘  │     │
│  │  │ .mfc_cache[]   │                                            │     │
│  │  │ .mfc_unres_q   │    MFC Hash Table (mfc_cache)              │     │
│  │  └────────────────┘    ┌──────────────────────────────────┐   │     │
│  │                        │ (S,G) → {iif, oifs[], pkt_cnt}   │   │     │
│  │                        │ (*,G) → {iif, oifs[], ...}       │   │     │
│  │                        └──────────────────────────────────┘   │     │
│  │                                                                │     │
│  │  ip_mr_forward()   ipmr_mfc_add()   ipmr_cache_report()       │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                       │                    │                             │
│                       ▼                    ▼                             │
│            Packet forwarding         Upcall to daemon                   │
│            (netif_rx / xmit)         (IGMPMSG_NOCACHE etc.)             │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │              net/ipv4/ip_input.c / ip_forward.c              │       │
│  │  ip_rcv() → ip_rcv_finish() → ip_route_input() →            │       │
│  │  ip_mr_input() [if multicast dest] → ip_mr_forward()        │       │
│  └──────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 MRT Socket and Control Interface

The userspace daemon controls multicast routing via a raw socket:

```c
/* Userspace daemon setup (simplified): */
int mrt_sock = socket(AF_INET, SOCK_RAW, IPPROTO_IGMP);
/* Enable MRT: */
setsockopt(mrt_sock, IPPROTO_IP, MRT_INIT, &version, sizeof(version));

/* Add virtual interface: */
struct vifctl vc = {
    .vifc_vifi    = 0,
    .vifc_flags   = 0,              /* or VIFF_TUNNEL, VIFF_REGISTER */
    .vifc_threshold = 1,
    .vifc_rate_limit = 0,
    .vifc_lcl_addr = { .s_addr = inet_addr("10.1.1.254") },
    .vifc_rmt_addr = { .s_addr = INADDR_ANY },
};
setsockopt(mrt_sock, IPPROTO_IP, MRT_ADD_VIF, &vc, sizeof(vc));

/* Add MFC entry: */
struct mfcctl mc = {
    .mfcc_origin   = { .s_addr = inet_addr("10.1.1.1") },  /* source */
    .mfcc_mcastgrp = { .s_addr = inet_addr("239.1.1.1") }, /* group */
    .mfcc_parent   = 0,   /* incoming VIF index */
    .mfcc_ttls     = { [1]=1, [2]=1 },  /* outgoing VIF TTLs; 0=no fwd */
};
setsockopt(mrt_sock, IPPROTO_IP, MRT_ADD_MFC, &mc, sizeof(mc));
```

**MRT socket options** (`include/uapi/linux/mroute.h`):

```
  MRT_INIT          (200) - Initialize MRT
  MRT_DONE          (201) - Teardown MRT
  MRT_ADD_VIF       (202) - Add virtual interface
  MRT_DEL_VIF       (203) - Delete virtual interface
  MRT_ADD_MFC       (204) - Add multicast forwarding cache entry
  MRT_DEL_MFC       (205) - Delete MFC entry
  MRT_VERSION       (206) - Get MRT version
  MRT_ASSERT        (207) - Enable PIM assert processing
  MRT_PIM           (208) - Enable PIM mode (sends Register msgs up)
  MRT_TABLE         (209) - Select MRT table (multiple tables, v2.6.37+)
  MRT_ADD_MFC_PROXY (210) - Add (*,*,G) proxy entry (v3.10+)
  MRT_DEL_MFC_PROXY (211) - Delete (*,*,G) proxy entry
  MRT_FLUSH         (212) - Flush MFC (v5.2+)
```

### 9.3 Upcall Messages (Kernel → Userspace)

When a multicast packet arrives with no MFC entry, the kernel sends an upcall to the daemon:

```c
/* include/uapi/linux/mroute.h */
struct igmpmsg {
    __u32  unused1, unused2;
    unsigned char im_msgtype;   /* IGMPMSG_* */
    unsigned char im_mbz;       /* must be zero */
    unsigned char im_vif;       /* VIF index */
    unsigned char im_vif_hi;    /* upper 8 bits of VIF index (v4.18+) */
    struct in_addr im_src;      /* source address */
    struct in_addr im_dst;      /* destination (group) address */
};

/* Message types: */
#define IGMPMSG_NOCACHE     1   /* No MFC entry - install one */
#define IGMPMSG_WRONGVIF    2   /* Packet on wrong VIF (for assert) */
#define IGMPMSG_WHOLEPKT    3   /* Whole packet (for PIM register) */
#define IGMPMSG_WRVIFWHOLE  4   /* Wrong VIF + whole pkt (v4.18+) */
```

**Kernel path for upcall:**
```
net/ipv4/ipmr.c:
  ipmr_cache_report()
    → skb_push() adds igmpmsg header
    → sock_queue_rcv_skb(mroute_sk, skb)
    → daemon's recv() returns igmpmsg + original IP packet
```

---

## 10. Kernel Data Structures Deep Dive

### 10.1 mr_table (Multicast Routing Table)

```c
/* net/ipv4/ipmr.c (simplified from kernel source) */
/* Full definition: include/linux/mroute_base.h (since v4.18) */

struct mr_table {
    struct list_head    list;
    possible_net_t      net;
    u32                 id;
    struct sock __rcu   *mroute_sk;     /* controlling socket */
    struct timer_list   ipmr_expire_timer;
    struct list_head    mfc_unres_queue; /* unresolved MFC entries */
    struct vif_device   vif_table[MAXVIFS]; /* VIF array */
    struct rhltable     mfc_hash;       /* resolved MFC hash (rhashtable) */
    struct list_head    mfc_cache_list; /* all MFC entries */
    int                 maxvif;         /* highest VIF index in use */
    atomic_t            cache_resolve_queue_len;
    bool                mroute_do_assert;
    bool                mroute_do_pim;
    bool                mroute_do_wrvifwhole;
    int                 mroute_reg_vif_num;
};

/* Multiple routing tables (MRT_TABLE option, v2.6.37+):
   Allows multiple independent multicast routing instances.
   Each table has separate VIF table + MFC.
   Identified by table ID (0 = RT_TABLE_DEFAULT).
   
   Kernel config: CONFIG_IP_MROUTE_MULTIPLE_TABLES
   
   Lookup path:
     ipmr_get_table() → finds mr_table by ID
     ip_mr_forward() → uses table from route lookup result
*/
```

### 10.2 vif_device (Virtual Interface)

```c
/* include/linux/mroute_base.h */
struct vif_device {
    struct net_device   *dev;           /* underlying net device */
    netdevice_tracker   dev_tracker;
    unsigned long       bytes_in, bytes_out;
    unsigned long       pkt_in, pkt_out;
    unsigned long       rate_limit;     /* tokens/sec */
    unsigned char       threshold;      /* TTL threshold */
    unsigned short      flags;          /* VIFF_* flags */
    __be32              local, remote;  /* for VIFF_TUNNEL */
    int                 link;           /* device ifindex */
};

/* VIFF flags (include/uapi/linux/mroute.h): */
#define VIFF_TUNNEL     0x1   /* use IP-in-IP tunnel */
#define VIFF_SRCRT      0x2   /* NI */
#define VIFF_REGISTER   0x4   /* PIM Register VIF (virtual, no real if) */
#define VIFF_USE_IFINDEX 0x8  /* use vifc_lcl_ifindex instead of addr */

/*
 * VIFF_REGISTER creates a special "register" VIF used by PIM:
 * When first-hop DR needs to send PIM Register to RP, it routes
 * the packet to the register VIF, which triggers IGMPMSG_WHOLEPKT
 * upcall → daemon encapsulates in PIM Register and unicasts to RP.
 *
 * Kernel: ipmr_reg_vif_setup() creates a dummy_net device "pimreg"
 * File: net/ipv4/ipmr.c, net/ipv4/ipmr_base.c
 */
```

### 10.3 mfc_cache (Multicast Forwarding Cache Entry)

```c
/* include/linux/mroute.h */
struct mfc_cache_cmp_arg {
    __be32 mfc_mcastgrp;
    __be32 mfc_origin;
};

struct mfc_cache {
    struct mr_mfc _c;           /* base class (mroute_base.h) */
    union {
        struct {
            __be32 mfc_mcastgrp;    /* group address */
            __be32 mfc_origin;      /* source address (0 = wildcard *,G) */
        };
        struct mfc_cache_cmp_arg cmparg;
    };
};

/* mr_mfc: generic multicast forwarding cache entry */
struct mr_mfc {
    struct rhlist_head  mnode;          /* hash table node */
    unsigned short      mfc_parent;     /* incoming VIF (RPF interface) */
    int                 mfc_flags;      /* MFC_STATIC, MFC_NOTIFY */
    union {
        struct {
            unsigned long   expires;
            struct sk_buff_head unresolved; /* pkts waiting for MFC */
        } unres;                        /* unresolved entry */
        struct {
            unsigned long   last_assert;
            int             minvif;     /* first OIF index */
            int             maxvif;     /* last OIF index + 1 */
            u32             bytes;
            u32             pkt;
            u32             wrong_if;   /* wrong-VIF packet count */
            unsigned long   last_use;
            unsigned char   ttls[MAXVIFS]; /* TTL threshold per OIF */
                                           /* 0 = not forwarded */
                                           /* 1..255 = min TTL to fwd */
        } res;                          /* resolved entry */
    } mfc_un;
    struct list_head    list;
    struct rcu_head     rcu;
};
```

### 10.4 MFC Hash Table (rhashtable, since v4.1)

```
Before v4.1: Simple hash table with chaining
  struct mfc_cache *mfc_cache_array[MFC_LINES][MAXVIFS]
  MFC_LINES = 64, simple mod hash

Since v4.1: rhashtable (resizable concurrent hash)
  net/ipv4/ipmr.c: ipmr_mfc_htable_params
  Key: (mfc_mcastgrp, mfc_origin) → mfc_cache_cmp_arg
  
  Lookup: ipmr_cache_find() / ipmr_cache_find_any()
    ipmr_cache_find_any() checks (*,G) wildcard entries:
      - First tries exact (S,G) match
      - Falls back to (0,G) wildcard
      - Falls back to (0,0) catch-all (if MFC_NOTIFY set)

  ipmr_cache_find_any_parent() for RPF lookup:
    Finds parent VIF for RPF check on (*,G) entries.
```

---

## 11. Multicast Forwarding Cache (MFC)

### 11.1 MFC Lookup and Forwarding Path

```
Complete packet processing path:
═════════════════════════════════

net/ipv4/ip_input.c:
  ip_rcv()
    └─ ip_rcv_finish()
         └─ ip_route_input_noref()
              └─ ip_route_input_slow()
                   └─ [if dst is multicast]
                        ip_route_input_mc()
                          Sets skb->dst → special multicast route
                          rt->dst.input = ip_mr_input  [if MRT enabled]
                                        = ip_local_deliver [if local member]

net/ipv4/ipmr.c:
  ip_mr_input(skb):
    1. Check IGMP (Protocol 2) → handle locally via raw socket
    2. Check PIM (Protocol 103) if mroute_do_pim → pim_rcv()
    3. ipmr_cache_find(net, saddr, daddr) → mfc entry?
       YES: ip_mr_forward(net, rt, skb, cache, local)
       NO:  ipmr_cache_report(net, skb, vif, IGMPMSG_NOCACHE)
            queue skb in mfc_un.unres.unresolved
            wake up daemon to install MFC entry
    
  ip_mr_forward(net, rt, skb, cache, local):
    1. RPF check: skb arriving on correct VIF?
       cache->mfc_un.res.mfc_parent == vif_index?
       NO → ipmr_cache_report(IGMPMSG_WRONGVIF) [assert trigger]
    2. For each OIF in ttls[] where ttls[i] > 0 AND skb TTL > ttls[i]:
         ipmr_queue_xmit(net, rt, skb, cache, i)
    3. Decrement TTL, fix IP checksum
    4. Call dev_queue_xmit() on output device

  ipmr_queue_xmit():
    - Creates skb clone for each OIF
    - Sets output device
    - ip_decrease_ttl() [TTL-1]
    - Calls ip_send_check() [recalculate checksum]
    - Calls NF_HOOK(NFPROTO_IPV4, NF_INET_FORWARD, ...) 
      → goes through netfilter FORWARD chain
    - ipmr_forward_finish() → dst_output()
```

### 11.2 MFC Wildcard Entries

```
Wildcard matching hierarchy (ipmr_cache_find_any):

  1. Exact match: (S=10.1.1.1, G=239.1.1.1)  ← (S,G) SPT entry
  2. Source wildcard: (S=0.0.0.0, G=239.1.1.1)  ← (*,G) RPT entry
  3. Both wildcard: (S=0.0.0.0, G=0.0.0.0)  ← catch-all

(*,G) entries: used when SPT not yet established
  mfc_parent = VIF toward RP
  ttls[] = set for interfaces where (*,G) join received

(S,G) entries: used after SPT established
  mfc_parent = VIF toward source (RPF VIF)
  ttls[] = set for SPT OIFs

Note: In kernel MFC, there is no semantic distinction between
(*,G) and (S,G) in data structures—the difference is:
  - (S,G): mfc_origin != 0
  - (*,G): mfc_origin == 0
  
Behavior controlled entirely by userspace daemon setting
correct mfc_parent (iif) and ttls (OIF set).
```

### 11.3 MFC Expiry and Cleanup

```c
/* Timer: ipmr_expire_timer (per mr_table) */
/* Default unresolved entry lifetime: 10 seconds */
#define MCAST_UNRES_TTL  10 * HZ

static void ipmr_expire_process(struct timer_list *t):
    spin_lock(&mfc_unres_lock);
    list_for_each_entry_safe(c, next, &mrt->mfc_unres_queue, _c.list):
        if time_after(c->_c.mfc_un.unres.expires, now):
            update next_timer
        else:
            /* Entry expired: notify daemon, free queued skbs */
            ipmr_cache_report(mrt, skb, vifi, IGMPMSG_NOCACHE)
            ipmr_destroy_unres(mrt, c)
    spin_unlock(&mfc_unres_lock);

/* Resolved entries: no automatic expiry in kernel.
   Daemon is responsible for:
   - Removing inactive (S,G) entries via MRT_DEL_MFC
   - Updating OIL when IGMP membership changes
   - Handling assert winner changes
*/
```

---

## 12. PIM Packet Processing in the Kernel

### 12.1 PIM Protocol Handler

```c
/* PIM uses IP protocol number 103 (IPPROTO_PIM) */
/* net/ipv4/ipmr.c: pim_rcv() / pim_rcv_v1() */

/* PIM is registered as raw protocol + special mroute handler */
static const struct net_protocol pim_protocol = {
    .handler    = pim_rcv,
    .netns_ok   = 1,
};

/* Registration: net/ipv4/ipmr.c: ipmr_net_init() */
/* inet_add_protocol(&pim_protocol, IPPROTO_PIM) */

int pim_rcv(struct sk_buff *skb):
    1. Parse outer IP header
    2. Check IP proto == 103 (PIM)
    3. Parse PIM header: version=2, type
    4. If type == PIM_REGISTER:
         pim_rcv_v1() → decapsulate inner packet
         ipmr_demux_mroute() → re-inject inner pkt into routing
    5. All other PIM types: deliver to mroute_sk (daemon's raw socket)
       → daemon handles Hello, J/P, Assert, BSR, etc.

/* Note: The kernel only handles PIM Register decapsulation.
   ALL other PIM message processing (Hello, Join/Prune, Assert,
   BSR, RP election) is done entirely in USERSPACE by the daemon.
   
   This is by design - kernel is multicast FORWARDER only.
   Policy (which interfaces join, RP selection) is userspace.
*/
```

### 12.2 PIM Register Processing

```
PIM Register Flow (kernel perspective):
════════════════════════════════════════

At First-Hop DR (sender of Register):
  1. Multicast packet arrives from local source
  2. No (S,G) MFC entry yet (or register VIF in OIL)
  3. IGMPMSG_NOCACHE upcall → daemon creates MFC entry
     with OIF = register VIF (VIFF_REGISTER)
  4. Packet routed to pimreg device (dummy device)
  5. Daemon receives IGMPMSG_WHOLEPKT upcall
  6. Daemon encapsulates in PIM Register:
     Outer IP: src=DR_addr, dst=RP_addr, proto=103, TTL=64
     PIM header: type=1 (Register)
     Inner IP: original multicast packet
  7. Sends unicast to RP

At RP (receiver of Register):
  1. pim_rcv() called for incoming PIM packet
  2. type=1 → pim_rcv_v1() 
  3. Decapsulates inner IP packet from Register payload
  4. Calls ipmr_demux_mroute() → re-injects into ip_rcv()
  5. Inner packet processed as normal multicast
     → forwarded via (*,G) MFC entry to receivers
  
  Simultaneously, daemon:
  6. Builds (S,G) SPT: sends PIM Join(S,G) upstream toward source
  7. Once native traffic arrives at RP via SPT:
     Sends Register-Stop to DR → DR stops encapsulating

Register-Stop (kernel side):
  8. DR receives Register-Stop → daemon processes it
  9. Daemon removes register VIF from (S,G) OIL
  10. Daemon may set up "null register" keepalive timer:
      Periodically sends Register with Null-Register bit set
      to check if RP still wants the traffic
```

---

## 13. Virtual Interfaces (VIF)

### 13.1 VIF Types and Setup

```
VIF Types:
  ┌─────────────────┬───────────────────────────────────────────┐
  │ Type            │ Description                               │
  ├─────────────────┼───────────────────────────────────────────┤
  │ Physical (flags=0)│ Normal interface (eth0, bond0, etc.)   │
  │ Tunnel (VIFF_TUNNEL)│ IP-in-IP tunnel (legacy, RFC 1075)  │
  │ Register (VIFF_REGISTER)│ PIM Register (pimreg device)    │
  └─────────────────┴───────────────────────────────────────────┘

Physical VIF creation:
  struct vifctl vc = {
      .vifc_vifi = 0,
      .vifc_flags = 0,
      .vifc_threshold = 1,    /* min TTL, packets with TTL <= this dropped */
      .vifc_lcl_addr.s_addr = if_addr,
  };
  setsockopt(fd, IPPROTO_IP, MRT_ADD_VIF, &vc, sizeof(vc));

Kernel: ipmr_vif_add() → vif_add()
  - Finds net_device by local address (or ifindex if VIFF_USE_IFINDEX)
  - Sets up vif_device entry
  - Calls dev_set_allmulti(dev, 1) → enables promiscuous multicast
  - Registers notifier for device events

Register VIF:
  .vifc_flags = VIFF_REGISTER
  → ipmr_reg_vif_setup() called
  → Creates "pimreg" alloc_netdev() dummy device
  → dev->netdev_ops = &reg_vif_netdev_ops
  → reg_vif_xmit() → ipmr_cache_report(IGMPMSG_WHOLEPKT)
```

### 13.2 VIF Tunnel Mode (Legacy)

```
VIFF_TUNNEL: encapsulates multicast in unicast IP-in-IP (proto 4).
Used for inter-domain multicast over non-multicast-capable links.

  struct vifctl vc = {
      .vifc_vifi = 2,
      .vifc_flags = VIFF_TUNNEL,
      .vifc_lcl_addr.s_addr = local_addr,   /* tunnel local */
      .vifc_rmt_addr.s_addr = remote_addr,  /* tunnel remote */
  };

Kernel: vif_add() with VIFF_TUNNEL
  → ipip_tunnel_create() or existing tunnel lookup
  → vif_device.dev = tunnel_device

Rarely used in modern deployments; VXLAN/GRE preferred for overlay.
```

---

## 14. IPv6 Multicast and PIM6

### 14.1 IPv6 MRT Architecture

```
IPv6 multicast routing mirrors IPv4 but with separate infrastructure:

  net/ipv6/ip6mr.c     - IPv6 multicast routing (analogous to ipmr.c)
  net/ipv6/mcast.c     - MLD implementation
  include/linux/mroute6.h - IPv6 MRT structures

Control socket:
  socket(AF_INET6, SOCK_RAW, IPPROTO_ICMPV6)
  setsockopt(fd, IPPROTO_IPV6, MRT6_INIT, ...)

Key differences from IPv4:
  1. Protocol: PIM6 uses same PIM (proto 103) but with IPv6
  2. Link-local: PIM Hellos use link-local source addresses
     (required by RFC 7761 §4.9.1)
  3. All-PIM-routers: ff02::d
  4. MLD instead of IGMP
  5. RPF uses IPv6 routing table

VIF equivalent: MIF (Multicast Interface)
  MRT6_ADD_MIF / MRT6_DEL_MIF
  struct mif6ctl (analogous to vifctl)
  MAXMIFS = 32 (same as MAXVIFS)

MFC equivalent: MF6C (Multicast Forwarding Cache v6)
  MRT6_ADD_MFC / MRT6_DEL_MFC
  struct mf6cctl (analogous to mfcctl)
  
  struct mf6cache {
      struct mr_mfc _c;
      struct in6_addr mf6c_origin;   /* source */
      struct in6_addr mf6c_mcastgrp; /* group */
  };
```

### 14.2 PIM6 and MLD Interaction

```
IPv6 Link-Local Address Requirement:
  PIM Hello src = fe80::/10 (link-local)
  Routers MUST have link-local on PIM-enabled interfaces
  (kernel auto-assigns via EUI-64 from MAC)

PIM6 packet: identical format to PIM4 but:
  - Carried in IPv6 (next header = 103)
  - Addresses in PIM messages use encoded-unicast IPv6 format
  - All-PIM-routers = ff02::d (scope=2, link-local)

PIM Register for IPv6:
  Outer IPv6: src=DR_link_addr, dst=RP_global_addr
  PIM type=1 Register
  Inner IPv6: original multicast packet

MLD Querier election:
  Lowest IPv6 link-local address wins (not highest like IGMPv2)
  RFC 3810: Querier's query interval code encoding differs from IGMPv2
```

---

## 15. Userspace Daemon Interaction

### 15.1 pimd (PIM-SM Daemon)

```
pimd is the reference PIM-SM implementation for Linux.
GitHub: troglobit/pimd (modern maintained fork)

Architecture:
  ┌──────────────────────────────────────────────────────┐
  │                      pimd                           │
  │                                                     │
  │  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
  │  │ PIM I/O  │  │ IGMP I/O │  │   Timer engine    │  │
  │  │ (raw sk) │  │ (raw sk) │  │ (select/timerfd)  │  │
  │  └────┬─────┘  └────┬─────┘  └───────────────────┘  │
  │       │              │                               │
  │  ┌────▼──────────────▼────────────────────────────┐  │
  │  │              Main event loop                   │  │
  │  │  pim_proto_handler() / igmp_proto_handler()    │  │
  │  └──────────────────────┬─────────────────────────┘  │
  │                         │                            │
  │  ┌──────────────────────▼─────────────────────────┐  │
  │  │           Routing policy engine                │  │
  │  │  - RP selection (static/BSR/Auto-RP)           │  │
  │  │  - Join/Prune timer management                 │  │
  │  │  - Register send/receive                       │  │
  │  │  - Assert processing                           │  │
  │  └──────────────────────┬─────────────────────────┘  │
  │                         │                            │
  │  ┌──────────────────────▼─────────────────────────┐  │
  │  │           Kernel MRT interface                 │  │
  │  │  MRT_ADD_VIF / MRT_ADD_MFC / upcall handler    │  │
  │  └────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────┘

pimd configuration (/etc/pimd.conf):
  # Define RP
  rp-address 10.0.0.1 224.0.0.0/4
  
  # Or use BSR candidate
  bsr-candidate eth0 priority 128
  rp-candidate eth0 priority 128 group-list 224.0.0.0/4
  
  # Interface config
  phyint eth0 enable
  phyint eth1 enable
  
  # SPT threshold (0 = immediate switchover)
  spt-threshold rate 0 interval 100
```

### 15.2 FRRouting (FRR) PIM

```
FRR (frrouting.org) is the dominant production-grade implementation.
Daemon: pimd (FRR's own pimd, distinct from standalone pimd)
Config: vtysh or frr.conf

FRR PIM sources:
  pimd/pim_*.c  (within FRR source tree)
  
Relevant FRR config (vtysh):
  router pim
   rp 10.0.0.1 224.0.0.0/4
   bsm                          ! BSR message processing
   unicast-bsm                  ! Unicast BSR (for VXLAN)
   ecmp                         ! ECMP multicast routing
   ecmp rebalance                ! Rebalance flows on topology change
  
  interface eth0
   ip pim
   ip pim hello 30 105          ! Hello interval, holdtime
   ip pim drpriority 100
   ip igmp
   ip igmp version 3
   ip igmp query-interval 125
   ip igmp last-member-query-interval 10

FRR uses Zebra daemon as RIB:
  pim → (zapi) → zebra → kernel routes
  PIM queries unicast routes via ZAPI for RPF lookups
  
  Zebra nexthop tracking: ZNH watches for RPF interface changes
  → triggers PIM to update MFC parent / send Join on new path
```

### 15.3 smcrouted (Static Multicast Routing)

```
smcrouted: simple daemon for static multicast routes.
Useful for: simple setups, testing, IPTV head-ends without PIM.

Configuration (/etc/smcroute.conf):
  mgroup from eth0 group 239.1.1.1
  mroute from eth0 group 239.1.1.1 to eth1 eth2

  mgroup: triggers IGMP join on the interface (keeps upstream happy)
  mroute: installs static MFC entry (no PIM needed)

smcrouted internals:
  Uses same MRT socket interface as pimd
  MRT_ADD_VIF for each interface
  MRT_ADD_MFC for each static route
  
  Advantage: Zero overhead, deterministic, no PIM state
  Disadvantage: No dynamic RP discovery, no SPT switchover
```

---

## 16. PIM State Machines

### 16.1 Upstream (S,G) State Machine

```
Upstream (S,G) State Machine (RFC 7761 §4.5.7):
════════════════════════════════════════════════

States: NotJoined (NJ), Joined (J)

Timers:
  - JoinTimer: Periodic Join refresh (default t_periodic = 60s)
  - KeepaliveTimer: Detects inactive sources
  - UpstreamOverrideTimer: Suppresses redundant Joins on shared LANs

        ┌─────────────────────────────────────────┐
        │        NotJoined (NJ)                   │◄──────────────────┐
        └──────────────────────┬──────────────────┘                   │
                               │                                      │
          [olist(S,G) != NULL  │                                      │
           AND (SPT bit set    │                                      │
           OR JoinDesired(*,G))│                                      │
           AND RPF'(S,G) !=NULL│                                      │
           AND NOT RPF'(S,G)   │                                      │
           is directly conn.]  │                                      │
                               ▼                                      │
        ┌──────────────────────────────────────────┐                  │
        │           Joined (J)                     │                  │
        │   - send Join(S,G) to RPF'(S,G)          │                  │
        │   - start JoinTimer                      │                  │
        └──────────────┬────────────┬──────────────┘                  │
                       │            │                                  │
     [JoinTimer exp.]  │            │ [olist(S,G) → NULL              │
     send Join(S,G)    │            │  OR !JoinDesired                │
     restart timer     │            │  OR RPF' changed]               │
                       │            │ send Prune(S,G) upstream  ──────┘
                       │            │
                       └────────────┘

JoinDesired(S,G) = TRUE if:
  (immediate_olist(S,G) != NULL)
  OR (KeepaliveTimer(S,G) running AND olist(*,G) != NULL)
  OR (inherited_olist(S,G,rpt) != NULL AND KeepaliveTimer running)
```

### 16.2 Downstream (S,G) Interface State Machine

```
Per-interface Downstream (S,G) State Machine:
══════════════════════════════════════════════

States: NoInfo (NI), Join (J), PrunePending (PP)

        ┌──────────────────────────────────────┐
        │           NoInfo (NI)                │◄───────────────────┐
        └─────────────────┬────────────────────┘                    │
                          │                                         │
          [Recv Join(S,G) │                                         │
           from downstream│                                         │
           on this iface] │                                         │
                          ▼                                         │
        ┌─────────────────────────────────────┐                     │
        │              Join (J)               │                     │
        │  - interface in OIL for (S,G)       │                     │
        │  - Expiry timer running             │                     │
        └────────┬────────────────────────────┘                     │
                 │                                                   │
   [Recv Prune(S,G)        [ExpiryTimer expires] ──────────────────►┘
    from downstream]                        
                 │                                                   
                 ▼                                                   
        ┌─────────────────────────────────────┐                     
        │         PrunePending (PP)           │                     
        │  - start PPT (= J/P Override Int.)  │                     
        └────────┬────────────────────────────┘                     
                 │                                                   
   [PPT expires] │     [Recv Join(S,G)] ──────────────────────────► J
                 ▼                                                   
           Remove from OIL                                          
           Transition to NoInfo                                      

Note: PrunePending state exists to allow other routers on shared
LAN to "override" the prune with a join (LAN prune delay mechanism).
```

### 16.3 (*,G) Upstream State Machine

```
(*,G) Upstream State Machine:
═════════════════════════════

States: NotJoined (NJ), Joined (J)

Conditions for join:
  JoinDesired(*,G) = immediate_olist(*,G) != NULL
                  OR (olist(*,G) != NULL AND
                      EXISTS s : KeepaliveTimer(s,G) running)

  When in Joined state, router sends periodic Join(*,G) to RPF'(*,G)
  (the upstream PIM neighbor toward RP).
  
  RPF'(*,G) = upstream neighbor from unicast route to RP(G)

Critical interaction with (S,G,rpt):
  When SPT is established for source S:
  - (S,G) state exists with SPT bit
  - Router wants to STOP receiving S via RPT
  - Sends Prune(S,G,rpt) in same J/P message as Join(*,G)
  
  J/P message can contain:
    groups:
      239.1.1.1:
        join_list: [(*,G), (S1,G,rpt=wildcard)]  ← * joins
        prune_list: [(S2,G,rpt)]  ← sources to prune from RPT
      ...

Holdtime in J/P: default 210 seconds (3.5 × t_periodic)
  If no refresh received within holdtime → prune upstream
```

---

## 17. Assert Mechanism

### 17.1 Assert Process

Assert resolves duplicate forwarders on a multi-access LAN.

```
Scenario: Two routers R1 and R2 both forwarding (S,G) onto same LAN

   Source S ──→ R1 ──→ [LAN] ──→ Receivers
                R2 ──→ [LAN] ──→ (duplicate!)

Assert Trigger:
  R1 receives its own multicast packet arriving from the LAN
  (i.e., packet it forwarded is looped back = "wrong VIF" condition)
  OR
  R2 receives packet from R1 on the LAN while R2 is also forwarding

Assert Message:
  ┌──────────────────────────────────────────────────────────┐
  │ PIM Type=5 (Assert)                                      │
  │ Group Address: 239.1.1.1 (Encoded-Group)                 │
  │ Source Address: 10.1.1.1 (Encoded-Unicast)               │
  │ R bit: 0 = (S,G) assert, 1 = (*,G) assert               │
  │ Metric Preference: administrative distance of best route │
  │ Metric: routing metric to source (or RP for *,G)         │
  └──────────────────────────────────────────────────────────┘

Assert Winner Selection:
  1. Lowest Metric Preference (admin distance) wins
  2. Tie → Lowest Metric wins
  3. Tie → Highest IP address wins

Assert State Machine:
  NoInfo → [recv inferior Assert OR send Assert] → Winner/Loser
  
  Winner: continues forwarding, sends periodic Assert refresh
  Loser:  stops forwarding, sets AssertTimer (Assert_Time=180s)
          When AssertTimer expires → revert to NoInfo → re-assert

Kernel handling:
  Wrong VIF packet → ipmr_cache_report(IGMPMSG_WRONGVIF)
  Daemon receives → evaluates metrics → sends Assert via raw socket
  
  If daemon wins assert: do nothing (already forwarding)
  If daemon loses assert: remove interface from MFC OIL
    MRT_ADD_MFC with updated ttls[] (set losing iif ttl to 0)
```

---

## 18. PIM Packet Formats

### 18.1 Encoded Address Formats

PIM uses special address encoding in messages:

```
Encoded-Unicast Address (IPv4):
  ┌────────────┬─────────────┬──────────────────────────────┐
  │ AF (1B)    │ Encoding(1B)│ Unicast Address (4B)         │
  │  1=IPv4    │  0=native   │                              │
  └────────────┴─────────────┴──────────────────────────────┘

Encoded-Group Address (IPv4):
  ┌────┬──────┬──┬────────┬──────────────┬──────────────────┐
  │ AF │ Enc. │B │ Z │Res │ Mask Len (1B)│ Group Addr (4B)  │
  │(1B)│ (1B) │  │   │    │              │                  │
  └────┴──────┴──┴────┴────┴──────────────┴──────────────────┘
  B=1: BIDIR group
  Z=1: Zone-ID present (after group addr)

Encoded-Source Address (IPv4):
  ┌────┬──────┬────────┬──────────────┬──────────────────────┐
  │ AF │ Enc. │S│W│R│Re│ Mask Len (1B)│ Source Addr (4B)     │
  │(1B)│ (1B) │ │ │ │  │              │                      │
  └────┴──────┴─┴─┴─┴──┴──────────────┴──────────────────────┘
  S=1: Sparse (PIM-SM)
  W=1: WildCard bit (* in J/P)
  R=1: RPT bit (prune from shared tree)
```

### 18.2 Join/Prune Message Format

```
PIM Join/Prune Message:
┌──────────────────────────────────────────────────────────────┐
│ PIM Ver=2 │ Type=3 │ Reserved │ Checksum                     │
├──────────────────────────────────────────────────────────────┤
│ Upstream Neighbor (Encoded-Unicast) ← target of J/P         │
├──────────────────────────────────────────────────────────────┤
│ Reserved │ Num Groups │ Holdtime                             │
├──────────────────────────────────────────────────────────────┤
│ Multicast Group Address [0] (Encoded-Group)                  │
├──────────────────────────────────────────────────────────────┤
│ Num Joined Sources │ Num Pruned Sources                      │
├──────────────────────────────────────────────────────────────┤
│ Joined Source [0] (Encoded-Source) ← W+R bits for *,G       │
│ Joined Source [1]                                            │
│ ...                                                          │
├──────────────────────────────────────────────────────────────┤
│ Pruned Source [0] (Encoded-Source)                           │
│ ...                                                          │
├──────────────────────────────────────────────────────────────┤
│ Multicast Group Address [1] ...                              │
└──────────────────────────────────────────────────────────────┘

Example: (*,G) Join:
  Upstream Neighbor = RPF'(*,G)
  Group = 239.1.1.1/32
  Joined Source = 0.0.0.0/32 with W=1, R=1 (wildcard, RPT)

Example: (S,G) Join + (S,G,rpt) Prune:
  Group = 239.1.1.1/32
  Joined Sources  = [10.1.1.1/32, W=0, R=0]  ← (S,G) join
  Pruned Sources  = [10.1.1.1/32, W=0, R=1]  ← (S,G,rpt) prune
  
  This is typical SPT switchover message from last-hop router.
```

### 18.3 Hello Message Options (TLV format)

```
PIM Hello:
┌─────────────────────────────────────────────────────────────┐
│ Type=0 │ Reserved │ Checksum                                │
├─────────────────────────────────────────────────────────────┤
│ OptionType (2B) │ OptionLength (2B)                        │
│ OptionValue (OptionLength bytes)                            │
│  ... (repeat)                                               │
└─────────────────────────────────────────────────────────────┘

Option 1 (Holdtime): 2 bytes
  Value = 0xFFFF → neighbor never expires (static config)
  Value = 0 → neighbor should immediately expire (graceful restart)
  
Option 2 (LAN Prune Delay): 4 bytes
  T bit (1) │ Propagation_Delay (15) │ Override_Interval (16)
  T=1: neighbor can suppress its own prune in favor of join
  Propagation_Delay: time for Join/Prune to propagate on LAN (ms)
  Override_Interval: J/P override timer value (ms)
  
  J/P_Override_Interval = J/P_HoldTime - effective_propagation_delay

Option 20 (Generation ID): 4 bytes - random, changes on restart
  Neighbor detecting Gen-ID change → treats neighbor as rebooted
  → sends Join(S,G) if needed (re-establish state)

Option 24 (Address List): list of Encoded-Unicast
  Secondary addresses on this interface
```

---

## 19. Debugging and Tracing

### 19.1 Kernel MFC Inspection

```bash
# Current MFC entries (IPv4):
cat /proc/net/ip_mr_cache

# Output format:
# Group    Origin   Iif  Pkts  Bytes  Wrong  Oifs
# EF010101 0A010101  0    142   18832  0      01:1

# Field meanings:
# Group/Origin: hex (network byte order) → 239.1.1.1 = EF010101
# Iif: incoming VIF index
# Pkts/Bytes: forwarded packet/byte counts
# Wrong: packets arriving on wrong VIF (assert triggers)
# Oifs: list of "VIF:TTL" pairs (hex)

# IPv4 VIF table:
cat /proc/net/ip_mr_vif

# IPv6 equivalents:
cat /proc/net/ip6_mr_cache
cat /proc/net/ip6_mr_vif

# IGMP group membership:
cat /proc/net/igmp
cat /proc/net/igmp6

# Multicast socket stats:
cat /proc/net/snmp | grep -i multi
# UdpInDatagrams, MCastIn, MCastOut in /proc/net/dev
```

### 19.2 ftrace for Multicast Path

```bash
# Trace ipmr forwarding path:
cd /sys/kernel/debug/tracing

# Trace all ipmr functions:
echo 'ipmr*' > set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on
# ... generate traffic ...
cat trace

# Trace specific function with call graph:
echo ip_mr_forward > set_graph_function
echo function_graph > current_tracer
echo 1 > tracing_on
cat trace | head -100

# Trace MFC cache misses (upcall):
echo ipmr_cache_report >> set_ftrace_filter
echo function > current_tracer

# Example trace output:
# <idle>-0  [001] ....  1234.5678: ip_mr_input <-ip_local_deliver_finish
# <idle>-0  [001] ....  1234.5679: ipmr_cache_find <-ip_mr_input
# <idle>-0  [001] ....  1234.5680: ipmr_cache_report <-ip_mr_input
```

### 19.3 eBPF/bpftrace Multicast Tracing

```c
/* bpftrace: trace MFC cache misses */
/* Usage: bpftrace mcast_trace.bt */

/* File: mcast_trace.bt */
BEGIN {
    printf("Tracing multicast cache misses...\n");
}

/* Trace ipmr_cache_report() - upcall to daemon */
kprobe:ipmr_cache_report {
    $skb = (struct sk_buff *)arg1;
    $vifi = (int)arg2;
    $assert = (int)arg3;
    
    /* Read IP header from skb->data */
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    
    printf("MFC miss: src=%s dst=%s vif=%d type=%d\n",
           ntop(AF_INET, $iph->saddr),
           ntop(AF_INET, $iph->daddr),
           $vifi,
           $assert);  /* 1=NOCACHE, 2=WRONGVIF, 3=WHOLEPKT */
    
    @misses[ntop(AF_INET, $iph->daddr)] = count();
}

/* Trace ip_mr_forward() - successful forwarding */
kprobe:ip_mr_forward {
    @forwards = count();
}

/* Trace wrong-VIF packets (assert trigger) */
kprobe:ipmr_cache_report / arg3 == 2 / {
    $skb = (struct sk_buff *)arg1;
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    printf("Wrong-VIF: src=%s dst=%s\n",
           ntop(AF_INET, $iph->saddr),
           ntop(AF_INET, $iph->daddr));
    @wrong_vif[ntop(AF_INET, $iph->daddr)] = count();
}

END {
    printf("\nMFC miss counts per group:\n");
    print(@misses);
    printf("\nWrong-VIF counts:\n");
    print(@wrong_vif);
    printf("\nTotal forwards: %d\n", @forwards);
}
```

### 19.4 perf for Multicast Performance

```bash
# Profile multicast forwarding hotspots:
perf record -g -e cycles:u -p $(pgrep pimd) -- sleep 10
perf report --no-children

# Trace kernel multicast functions:
perf probe -a 'ip_mr_forward skb iif'
perf record -e probe:ip_mr_forward -ag -- sleep 5
perf script

# Count MFC lookups:
perf stat -e 'syscalls:sys_enter_setsockopt' \
    -e 'net:net_dev_xmit' \
    -- sleep 10

# Flamegraph for multicast:
perf record -F 99 -ag -e cycles -- sleep 10
perf script | stackcollapse-perf.pl | flamegraph.pl > mcast.svg

# Tracepoints available:
perf list 'net:*'
# net:net_dev_xmit - packet transmission
# net:netif_receive_skb - packet reception
# net:net_dev_queue - packet queued

# Custom tracepoint for MFC:
perf probe --add 'ipmr_mfc_add mfc->mfc_un.res.mfc_parent:u8'
```

### 19.5 tcpdump/Wireshark PIM Capture

```bash
# Capture PIM traffic:
tcpdump -i eth0 -n 'ip proto 103' -w pim.pcap

# Capture PIM + IGMP:
tcpdump -i eth0 -n '(ip proto 103) or (ip proto 2)' -w pim_igmp.pcap

# Capture multicast group traffic:
tcpdump -i eth0 -n 'dst 239.1.1.1'

# Capture PIM to all-PIM-routers:
tcpdump -i eth0 -n 'dst 224.0.0.13'

# Decode PIM in text:
tcpdump -i eth0 -v 'ip proto 103'

# Sample output:
# 14:23:01.123456 IP 10.1.1.1 > 224.0.0.13: PIMv2, length 34
#   Hello, cksum 0x1234 (correct)
#   Holdtime Option (1), length 2, value: 105s
#   DR Priority Option (19), length 4, value: 1
#   Generation ID Option (20), length 4, value: 0xdeadbeef

# Capture PIM Register (unicast, harder to filter):
tcpdump -i eth0 -n 'ip proto 103 and not dst 224.0.0.13'

# ss for multicast socket state:
ss -n -p --no-header state all | grep igmp
ip mroute show    # iproute2 - shows kernel MFC (human readable)
ip mroute show table all
```

### 19.6 iproute2 Multicast Commands

```bash
# Show multicast routes (MFC):
ip mroute show
# Output:
# (10.1.1.1, 239.1.1.1)        Iif: eth0    Oifs: eth1  eth2

# Show all tables:
ip mroute show table all

# Show multicast route for specific group:
ip mroute show 239.1.1.1

# Show multicast stats:
ip -s mroute show

# IGMP group membership (via rtnetlink):
ip maddr show
ip -6 maddr show

# ip maddr output:
# 2:  eth0
#     link  01:00:5e:00:00:01
#     inet  224.0.0.1
#     inet  239.1.1.1   users 1  static
#     inet6 ff02::1
#     inet6 ff02::d     users 1  static
```

### 19.7 Kernel Sysctl Parameters

```bash
# Enable IP multicast routing (required for MRT):
sysctl -w net.ipv4.conf.all.mc_forwarding=1
# Note: This is set automatically by kernel when MRT_INIT is called.
# Manual set needed only for special cases.

# Per-interface multicast parameters:
# (net.ipv4.conf.eth0.*)
sysctl net.ipv4.conf.eth0.mc_forwarding    # R/O: 1 if MRT enabled
sysctl net.ipv4.conf.eth0.force_igmp_version  # 0=auto, 1/2/3=force

# IPv4 multicast TTL:
# Note: TTL is per-socket (IP_MULTICAST_TTL), not global sysctl.

# IGMP parameters:
sysctl net.ipv4.igmp_max_memberships       # max per socket (default 20)
sysctl net.ipv4.igmp_max_msf               # max source filter entries (10)
sysctl net.ipv4.igmp_qrv                   # Query Robustness Variable (2)
sysctl net.ipv4.igmp_link_local_mcast_reports  # report link-local groups

# IPv6 MLD:
sysctl net.ipv6.mld_qrv                    # MLDv2 QRV (2)
sysctl net.ipv6.mld_max_msf                # max source filter entries

# Neighbor table (affects RPF lookups):
sysctl net.ipv4.neigh.default.gc_thresh3   # max ARP entries

# RPDB policy rules (for multiple MRT tables):
ip rule add iif eth0 lookup 100
ip mrule add iif eth0 lookup 100  # multicast-specific rules (iproute2)
```

---

## 20. eBPF and XDP for Multicast

### 20.1 eBPF Multicast Forwarding Acceleration

```c
/* XDP program for fast-path multicast forwarding
 * Bypasses kernel MFC for known (S,G) flows
 * File: xdp_mcast_fwd.c
 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* Map: (src_ip, grp_ip) → output ifindex */
struct mcast_key {
    __u32 src;
    __u32 grp;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct mcast_key);
    __type(value, __u32);  /* output ifindex */
    __uint(max_entries, 1024);
} mcast_fwd_map SEC(".maps");

/* Map: ifindex → MAC address */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);
    __type(value, __u8[ETH_ALEN]);
    __uint(max_entries, 64);
} if_mac_map SEC(".maps");

SEC("xdp")
int xdp_mcast_forward(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    /* Only handle IPv4 */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    /* Only multicast destinations */
    if ((bpf_ntohl(iph->daddr) >> 28) != 0xE)
        return XDP_PASS;

    /* SSM range check: 232.0.0.0/8 */
    struct mcast_key key = {
        .src = iph->saddr,
        .grp = iph->daddr,
    };

    __u32 *oif = bpf_map_lookup_elem(&mcast_fwd_map, &key);
    if (!oif)
        return XDP_PASS;  /* Fall through to kernel MFC */

    /* TTL check and decrement */
    if (iph->ttl <= 1)
        return XDP_DROP;

    /* Decrement TTL (must update checksum) */
    __u32 csum = bpf_csum_diff(0, 0, (__be32 *)iph, sizeof(*iph), 0);
    iph->ttl--;
    iph->check = 0;
    iph->check = ~((csum >> 16) + (csum & 0xFFFF));

    /* Rewrite destination MAC to multicast MAC */
    /* 01:00:5e:xx:xx:xx where xx = low 23 bits of group IP */
    __u32 grp = bpf_ntohl(iph->daddr);
    eth->h_dest[0] = 0x01;
    eth->h_dest[1] = 0x00;
    eth->h_dest[2] = 0x5e;
    eth->h_dest[3] = (grp >> 16) & 0x7F;
    eth->h_dest[4] = (grp >> 8) & 0xFF;
    eth->h_dest[5] = grp & 0xFF;

    /* Set source MAC from output interface map */
    __u8 *src_mac = bpf_map_lookup_elem(&if_mac_map, oif);
    if (src_mac) {
        __builtin_memcpy(eth->h_source, src_mac, ETH_ALEN);
    }

    return bpf_redirect(*oif, 0);
}

char _license[] SEC("license") = "GPL";
```

### 20.2 TC-BPF for Multicast Replication

```c
/* TC BPF for multicast replication to multiple interfaces
 * Uses BPF_MAP_TYPE_DEVMAP for multi-output
 * Requires kernel v5.8+ for BPF_MAP_TYPE_DEVMAP_HASH
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* Devmap for multicast output interfaces */
struct {
    __uint(type, BPF_MAP_TYPE_DEVMAP_HASH);
    __type(key, __u32);       /* ifindex */
    __type(value, struct bpf_devmap_val);
    __uint(max_entries, 32);
} mcast_oif_map SEC(".maps");

/* Group → devmap lookup */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);       /* group address */
    __type(value, __u32);     /* devmap program fd or marker */
    __uint(max_entries, 1024);
} group_map SEC(".maps");

SEC("tc")
int tc_mcast_clone(struct __sk_buff *skb) {
    /* Use bpf_clone_redirect for each output interface */
    /* Note: bpf_redirect_map with DEVMAP handles cloning */
    
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    struct iphdr *iph = data + sizeof(struct ethhdr);
    
    if ((void *)(iph + 1) > data_end)
        return TC_ACT_OK;

    __u32 grp = iph->daddr;
    __u32 *marker = bpf_map_lookup_elem(&group_map, &grp);
    if (!marker)
        return TC_ACT_OK;

    /* bpf_redirect_map with BPF_F_BROADCAST replicates to all devmap entries */
    return bpf_redirect_map(&mcast_oif_map, 0, BPF_F_BROADCAST | BPF_F_EXCLUDE_INGRESS);
}
char _license[] SEC("license") = "GPL";
```

### 20.3 BPF Multicast Socket Interception

```c
/* Intercept IGMP joins for monitoring/policy enforcement */
/* Uses cgroup/sock_addr BPF program type */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct igmp_event {
    __u32 pid;
    __u32 group;
    __u8  type;  /* 0=join, 1=leave */
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096);
} igmp_events SEC(".maps");

/* Trace IGMP group joins via kprobe on ip_mc_join_group */
SEC("kprobe/ip_mc_join_group")
int kprobe__ip_mc_join_group(struct pt_regs *ctx) {
    /* arg1 = struct sock *sk, arg2 = struct ip_mreqn *imr */
    struct igmp_event *event;
    
    event = bpf_ringbuf_reserve(&igmp_events, sizeof(*event), 0);
    if (!event)
        return 0;
    
    event->pid = bpf_get_current_pid_tgid() >> 32;
    /* Read imr_multiaddr from ip_mreqn */
    /* struct ip_mreqn { struct in_addr imr_multiaddr; ... } */
    bpf_probe_read_kernel(&event->group, 4, (void *)PT_REGS_PARM2(ctx));
    event->type = 0;
    
    bpf_ringbuf_submit(event, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

---

## 21. Configuration Reference

### 21.1 Complete FRRouting PIM Configuration

```
# /etc/frr/frr.conf - Complete PIM-SM configuration

frr defaults traditional
hostname pim-router
log syslog informational

!
interface lo
 ip address 10.0.0.1/32
 ip pim
!
interface eth0
 description Upstream / Core
 ip address 10.1.0.1/30
 ip pim
 ip pim hello 30 105
 ip pim drpriority 100
 ip ospf area 0
!
interface eth1
 description Access / Downstream
 ip address 10.2.0.1/24
 ip pim
 ip igmp
 ip igmp version 3
 ip igmp query-interval 60
 ip igmp query-max-response-time 10
 ip igmp last-member-query-count 2
 ip igmp last-member-query-interval 10
 ip igmp robustness-variable 2
!
router pim
 ! RP Configuration
 rp 10.0.0.1 224.0.0.0/4
 
 ! BSR Configuration (this router as C-BSR)
 bsm
 bsr-candidate lo priority 200 hash-mask-length 30
 rp-candidate lo group-list PIM-RP-GROUPS priority 0 interval 60
 
 ! SSM Range
 ssm prefix-list SSM-RANGES
 
 ! SPT Switchover (0 = immediate)
 spt-switchover infinity-and-beyond prefix-list NO-SPT-GROUPS
 
 ! ECMP
 ecmp
 ecmp rebalance
 
 ! Register suppression
 register-suppress-time 60
 
 ! Send Joins only to RPF neighbor (default)
 join-prune-interval 60
 keepalive-timer 210
!
ip prefix-list PIM-RP-GROUPS seq 5 permit 224.0.0.0/4
ip prefix-list SSM-RANGES seq 5 permit 232.0.0.0/8
ip prefix-list NO-SPT-GROUPS seq 5 permit 239.0.0.0/8

! OSPF for underlay (RPF lookups need unicast routes)
router ospf
 network 10.0.0.0/8 area 0
 passive-interface eth1

line vty
!
```

### 21.2 smcrouted Static Configuration

```
# /etc/smcroute.conf

# Join multicast group on upstream interface
# (prevents upstream router from pruning)
mgroup from eth0 group 239.1.1.1
mgroup from eth0 group 239.1.1.2

# Static multicast routes
# Forward all traffic for 239.1.1.1 from eth0 to eth1 and eth2
mroute from eth0 group 239.1.1.1 to eth1 eth2

# Source-specific static route
mroute from eth0 source 10.1.1.1 group 239.1.1.1 to eth1

# VLAN interfaces work too:
mroute from eth0.100 group 239.2.0.0/24 to eth1.200 eth1.201

# Systemd service:
# systemctl enable --now smcroute
```

### 21.3 Kernel Module Configuration

```bash
# Required kernel config options:
# CONFIG_IP_MULTICAST=y          - Basic multicast support
# CONFIG_IP_MROUTE=y             - Multicast routing (MRT)
# CONFIG_IP_MROUTE_MULTIPLE_TABLES=y  - Multiple MRT tables
# CONFIG_IP_PIMSM_V1=y           - PIMv1 receive support
# CONFIG_IP_PIMSM_V2=y           - PIMv2 Register handling
# CONFIG_IPV6_MROUTE=y           - IPv6 multicast routing
# CONFIG_IPV6_PIMSM_V2=y         - IPv6 PIM Register
# CONFIG_IPV6_MROUTE_MULTIPLE_TABLES=y

# Verify at runtime:
cat /proc/net/ip_mr_cache  # fails if CONFIG_IP_MROUTE not set
ls /proc/net/ip_mr_vif

# Load relevant modules (usually built-in):
modinfo ip_tunnel    # for tunnel VIF
modinfo vxlan        # for VXLAN-based multicast

# Check IGMP/PIM socket capability:
cat /proc/sys/net/ipv4/conf/all/mc_forwarding
```

### 21.4 Network Namespace Multicast

```bash
# Multicast routing in network namespaces (v4.18+):
# Each netns has independent mr_table, VIFs, MFC.

# Create namespace:
ip netns add mcast-ns

# Enable multicast routing in namespace:
ip netns exec mcast-ns ip link set lo up
ip netns exec mcast-ns ip addr add 10.0.0.1/32 dev lo

# Run daemon in namespace:
ip netns exec mcast-ns pimd --config /etc/pimd-ns.conf

# Important: Each netns's PIM daemon gets its own MRT socket.
# MRT_INIT in one netns doesn't affect others.

# Veth pair for cross-namespace multicast testing:
ip link add veth0 type veth peer name veth1 netns mcast-ns
ip addr add 10.1.0.1/30 dev veth0
ip netns exec mcast-ns ip addr add 10.1.0.2/30 dev veth1

# Enable multicast on veth:
ip link set veth0 multicast on
ip netns exec mcast-ns ip link set veth1 multicast on
```

---

## 22. Security Considerations

### 22.1 PIM Authentication

```
PIM has NO built-in authentication in RFC 7761.
Mitigations:

1. ACL on PIM interfaces (prevent unauthorized PIM neighbors):
   FRR: ip pim passive  ← accept IGMP but not PIM Hellos from downstream
   
2. IPsec for PIM protection:
   AH/ESP on IP proto 103
   Rarely deployed due to operational complexity
   
3. PIM Hello authentication (draft, not standardized):
   Some implementations support HMAC-MD5 in Hello TLV
   Option type not standardized
   
4. Register message protection:
   Register is unicast → can be protected by standard ACL
   RP should ACL MRT socket to accept Register only from known DRs
   
5. BSR protection:
   BSR messages can be spoofed → false RP distribution
   Mitigation: BSR accept-RP list (FRR config)
   FRR: ip pim bsm  (enable BSR) + ACL on interface

6. Assert flooding:
   Attacker can send Assert messages to become forwarder
   Mitigation: same as above - interface ACL for 224.0.0.13
```

### 22.2 Multicast Amplification Attack

```
Multicast can amplify traffic:
  - One source → many receivers
  - Attacker spoofs source, legitimate multicast stream hits victim

Mitigations:
  1. RPF check (kernel enforces): drops spoofed sources
  2. Ingress filtering (BCP38 / RFC 2827):
     ISPs filter sources not matching customer prefix
  3. SSM: receivers specify source → eliminates (*,G) amplification
  4. Rate limiting MFC upcalls:
     Limit IGMPMSG_NOCACHE rate to prevent upcall flooding:
     
     # iptables rate limit (before packet reaches MRT):
     iptables -A FORWARD -d 224.0.0.0/4 -m limit \
       --limit 1000/sec --limit-burst 2000 -j ACCEPT
     iptables -A FORWARD -d 224.0.0.0/4 -j DROP
```

---

## 23. Performance Tuning

### 23.1 MFC Hash Table Sizing

```c
/* Default MFC hash size: determined by rhashtable (auto-resize) */
/* Manual tuning for high-scale deployments (v4.18+):            */

/* Kernel: net/ipv4/ipmr.c */
static const struct rhashtable_params ipmr_rht_params = {
    .head_offset   = offsetof(struct mr_mfc, mnode),
    .key_offset    = offsetof(struct mfc_cache, cmparg),
    .key_len       = sizeof(struct mfc_cache_cmp_arg),
    .nelem_hint    = 3,          /* initial hint (rhashtable auto-grows) */
    .obj_cmpfn     = ipmr_hash_cmp,
    .automatic_shrinking = true,
};

/* For large deployments (millions of (S,G) entries):
   - rhashtable auto-resizes, but initial hint matters
   - Patch ipmr_rht_params.nelem_hint for your scale
   - NUMA: rhashtable allocates hash buckets on init NUMA node
     → ensure pimd runs on same NUMA node as NIC
*/
```

### 23.2 Multicast Socket Buffer Tuning

```bash
# MRT socket receive buffer (daemon reads upcalls from here):
# Default: net.core.rmem_default (usually 212992 bytes)
# Increase for high-rate deployments (many MFC misses):
sysctl -w net.core.rmem_max=16777216

# In daemon code:
int bufsize = 16 * 1024 * 1024;
setsockopt(mrt_sock, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));

# Check socket buffer usage:
ss -mnp | grep pimd

# If upcall queue fills up:
# Unresolved entries are dropped when mfc_unres_queue exceeds max
# Kernel: atomic_read(&mrt->cache_resolve_queue_len) > IPMR_MAX_UNRES_QUEUE (3)
# → new unresolved entries dropped
# → increase IPMR_MAX_UNRES_QUEUE in ipmr.c or tune daemon responsiveness
```

### 23.3 Interrupt and NAPI Coalescing

```bash
# For high-rate multicast (IPTV, financial data):
# Tune interrupt coalescing on NIC:
ethtool -C eth0 rx-usecs 50 tx-usecs 50

# Enable RSS for multicast (NIC distributes flows across CPUs):
ethtool -X eth0 equal 8  # spread across 8 RX queues

# Multicast hash steering (Intel/Mellanox):
ethtool --features eth0 ntuple on
# NIC can steer multicast based on group address

# CPU affinity for IRQs:
cat /proc/interrupts | grep eth0
echo 3 > /proc/irq/45/smp_affinity  # pin to CPU 0 and 1

# RPS (Receive Packet Steering) for multicast:
echo ff > /sys/class/net/eth0/queues/rx-0/rps_cpus

# GRO (Generic Receive Offload) - normally beneficial:
ethtool -K eth0 gro on
# Note: GRO does NOT merge multicast packets (different destinations)
```

### 23.4 Multicast Forwarding Offload (ASIC)

```
For hardware-assisted multicast (switches/routers with ASIC):

Linux switchdev API allows offloading MFC to ASIC:
  net/switchdev/ - switchdev framework
  drivers/net/ethernet/mellanox/mlxsw/spectrum_mr.c - Mellanox example

ASIC multicast offload flow:
  1. Kernel installs MFC entry
  2. switchdev notifier: SWITCHDEV_FDB_ADD_TO_DEVICE
  3. Driver programs ASIC multicast group table
  4. ASIC forwards at line rate without CPU involvement
  5. Kernel MFC still needed for software fallback

VXLAN multicast (overlay):
  Multicast group on physical underlay = VXLAN flood domain
  BUM (Broadcast/Unknown/Multicast) traffic:
    VXLAN tunnels use multicast group for flooding
    CONFIG_VXLAN + CONFIG_IP_MROUTE needed
    Daemon must route underlay multicast group
```

---

## Appendix A: Key Kernel Source Files Reference

```
net/ipv4/
  ipmr.c              - IPv4 multicast routing core
  ipmr_base.c         - Shared MR base (IPv4/IPv6) [since v4.18]
  igmp.c              - IGMP implementation
  ip_input.c          - ip_mr_input() entry point
  ip_forward.c        - ip_forward() (unicast, shares code)
  ip_sockglue.c       - IP socket options (IP_ADD_MEMBERSHIP etc.)
  raw.c               - Raw socket (PIM daemon receives PIM msgs here)
  route.c             - ip_route_input_mc() RPF check

net/ipv6/
  ip6mr.c             - IPv6 multicast routing
  mcast.c             - MLD implementation
  ip6_input.c         - IPv6 multicast input

include/linux/
  mroute.h            - IPv4 MRT kernel structures
  mroute6.h           - IPv6 MRT kernel structures
  mroute_base.h       - Shared structures (mr_table, mr_mfc, vif_device)
  igmp.h              - IGMP structures (ip_mc_list, ip_sf_list)
  
include/uapi/linux/
  mroute.h            - Userspace MRT API (vifctl, mfcctl, MRT_*)
  mroute6.h           - Userspace IPv6 MRT API
  igmp.h              - IGMP protocol definitions (igmpmsg)

Documentation/networking/
  ip-sysctl.rst       - Multicast sysctl documentation
  multicast.rst       - Multicast overview (if present)
```

## Appendix B: Glossary

```
ASM     - Any-Source Multicast (traditional PIM-SM)
BSR     - Bootstrap Router (RP election mechanism)
C-BSR   - Candidate BSR
C-RP    - Candidate Rendezvous Point
DF      - Designated Forwarder (BIDIR)
DR      - Designated Router (PIM-SM)
MFC     - Multicast Forwarding Cache
MIF     - Multicast Interface (IPv6 VIF equivalent)
MLD     - Multicast Listener Discovery (IPv6 IGMP)
MSDP    - Multicast Source Discovery Protocol
OIL     - Outgoing Interface List
PIM     - Protocol Independent Multicast
RPF     - Reverse Path Forwarding
RPT     - Rendezvous Point Tree (shared tree)
RP      - Rendezvous Point
SPT     - Shortest Path Tree (source tree)
SSM     - Source-Specific Multicast
VIF     - Virtual Interface (MRT term for routing interface)
```

Now I'll write the comprehensive PIM guide as a `.md` file. This will be large and deeply technical.**2,609 lines / ~104KB** of dense technical reference. Here's what's covered:

**Protocol Coverage:**
- PIM-DM (RFC 3973) — flood/prune, state-refresh, graft
- PIM-SM (RFC 7761) — full (*,G)/(S,G)/(S,G,rpt) state, Register/Register-Stop, SPT switchover
- PIM-SSM (RFC 4607) — IGMPv3 source filter integration
- PIM-BIDIR (RFC 5015) — DF election, bidirectional tree
- BSR (RFC 5059), Auto-RP, Anycast-RP (RFC 4610), MSDP

**Kernel Internals:**
- Full `net/ipv4/ipmr.c` architecture with function call chains
- `mr_table`, `vif_device`, `mfc_cache`, `mr_mfc` — every field explained
- `rhashtable` MFC (v4.1+), wildcard `(*,G)` matching hierarchy
- MRT socket control interface (`MRT_INIT` → `MRT_ADD_VIF` → `MRT_ADD_MFC`)
- Upcall path: `ipmr_cache_report()` → `IGMPMSG_NOCACHE/WRONGVIF/WHOLEPKT`
- PIM Register kernel decapsulation in `pim_rcv()`
- IPv6 `ip6mr.c` / MLD / MIF parallel architecture

**Debugging:**
- ftrace function graph through `ip_mr_forward()`
- bpftrace script tracing MFC misses and wrong-VIF packets with struct derefs
- perf probe on `ipmr_mfc_add`, flamegraph workflow
- All `iproute2` multicast commands, `/proc/net/ip_mr_cache` field decoding

**eBPF:**
- XDP fast-path forwarder with TTL decrement + multicast MAC rewrite
- TC-BPF with `BPF_MAP_TYPE_DEVMAP_HASH` + `BPF_F_BROADCAST` for replication
- `kprobe/ip_mc_join_group` ringbuf monitoring