# ARP — Address Resolution Protocol: The Complete In-Depth Guide

> *"Understanding ARP is understanding how the internet actually works at layer 2/3 boundary — the place where logical addressing meets physical reality."*

---

## Table of Contents

1. [Mental Model: Why ARP Exists](#1-mental-model-why-arp-exists)
2. [OSI Layer Positioning](#2-osi-layer-positioning)
3. [Ethernet Framing Fundamentals](#3-ethernet-framing-fundamentals)
4. [ARP Packet Structure](#4-arp-packet-structure)
5. [ARP Operation — Complete Lifecycle](#5-arp-operation--complete-lifecycle)
6. [ARP Cache — Design and Behavior](#6-arp-cache--design-and-behavior)
7. [ARP Message Types — All Opcodes](#7-arp-message-types--all-opcodes)
8. [Gratuitous ARP (GARP)](#8-gratuitous-arp-garp)
9. [Proxy ARP](#9-proxy-arp)
10. [ARP Probe and ARP Announcement (IPv4LL / RFC 5227)](#10-arp-probe-and-arp-announcement-ipv4ll--rfc-5227)
11. [Reverse ARP (RARP)](#11-reverse-arp-rarp)
12. [Inverse ARP (InARP)](#12-inverse-arp-inarp)
13. [ARP in Routing — Same Subnet vs Different Subnet](#13-arp-in-routing--same-subnet-vs-different-subnet)
14. [ARP and VLANs](#14-arp-and-vlans)
15. [ARP Security Vulnerabilities](#15-arp-security-vulnerabilities)
16. [ARP Spoofing / Poisoning — Attack Mechanics](#16-arp-spoofing--poisoning--attack-mechanics)
17. [ARP Defense Mechanisms](#17-arp-defense-mechanisms)
18. [ARP in Virtualization and Cloud](#18-arp-in-virtualization-and-cloud)
19. [ARP vs NDP (IPv6 Neighbor Discovery)](#19-arp-vs-ndp-ipv6-neighbor-discovery)
20. [Linux Kernel ARP Implementation](#20-linux-kernel-arp-implementation)
21. [ARP Tuning — Linux sysctls](#21-arp-tuning--linux-sysctls)
22. [ARP in High Availability Scenarios](#22-arp-in-high-availability-scenarios)
23. [C Implementation — Complete ARP Stack](#23-c-implementation--complete-arp-stack)
24. [Rust Implementation — Complete ARP Stack](#24-rust-implementation--complete-arp-stack)
25. [Packet Capture and Analysis](#25-packet-capture-and-analysis)
26. [ARP in Containers and Kubernetes](#26-arp-in-containers-and-kubernetes)
27. [ARP Edge Cases and Gotchas](#27-arp-edge-cases-and-gotchas)
28. [RFC Reference Summary](#28-rfc-reference-summary)

---

## 1. Mental Model: Why ARP Exists

### The Fundamental Problem

Network communication operates at two distinct addressing levels that must be bridged:

```
+----------------------------------------------------------+
|  LOGICAL ADDRESSING (Layer 3)                            |
|                                                          |
|   192.168.1.10  ----wants to talk to----  192.168.1.20  |
|                                                          |
|   IP addresses: meaningful to routers, software, humans  |
|   Dynamic, assignable, hierarchical, routable            |
+----------------------------------------------------------+
            |              PROBLEM              |
            v                                   v
+----------------------------------------------------------+
|  PHYSICAL ADDRESSING (Layer 2)                           |
|                                                          |
|   aa:bb:cc:dd:ee:01  ??????????????  aa:bb:cc:dd:ee:02  |
|                                                          |
|   MAC addresses: burned into NIC hardware                |
|   Flat, 48-bit, manufacturer-assigned, non-routable      |
+----------------------------------------------------------+
```

The Ethernet switch (Layer 2 device) does not understand IP addresses. It only forwards frames based on MAC addresses. When Host A sends an IP packet to Host B, the Ethernet frame that carries it must have Host B's MAC address in the destination field — but Host A only knows Host B's IP address.

**ARP is the bridge between these two worlds.**

### Conceptual Model

Think of it like a physical office:

- **IP Address** = office room number (your logical location in the building)
- **MAC Address** = your name badge (your physical identity)
- **ARP** = the intercom announcement: *"Would the person in room 192.168.1.20 please tell me their name badge number?"*
- **ARP Cache** = your personal contact book of room→name-badge mappings

### The Scope Constraint

ARP operates **only within a single broadcast domain** (a single LAN/subnet). It cannot cross routers. When traffic leaves the subnet, the router's MAC address is used at Layer 2, and the router then performs its own ARP on the next-hop network.

```
Host A (192.168.1.10)        Router                   Host B (10.0.0.5)
      |                    (192.168.1.1)                     |
      |                    (10.0.0.1)                        |
      |                         |                            |
      |<--- ARP domain 1 ------>|<------ ARP domain 2 ------>|
      |   192.168.1.x subnet    |       10.0.0.x subnet      |
```

A sends ARP for router's MAC (192.168.1.1), not for B's MAC directly.
Router sends ARP for B's MAC (10.0.0.5) on the other interface.

---

## 2. OSI Layer Positioning

```
+---------------------+
|   Layer 7: Application                   HTTP, DNS, SSH ...
+---------------------+
|   Layer 6: Presentation                  TLS, encoding
+---------------------+
|   Layer 5: Session                       sockets
+---------------------+
|   Layer 4: Transport                     TCP, UDP
+---------------------+
|   Layer 3: Network                       IP (IPv4/IPv6)
+---------------------+
|   Layer 2.5: ARP  <-------- ARP lives here, between L2 and L3
|   (no official layer)       It resolves L3 → L2 addresses
+---------------------+
|   Layer 2: Data Link                     Ethernet, 802.11
+---------------------+
|   Layer 1: Physical                      cables, signals
+---------------------+
```

ARP is often described as a Layer 2 protocol (it travels inside Ethernet frames without IP headers), but it serves Layer 3 (it maps IP addresses). This dual nature means:

- ARP frames have **EtherType 0x0806** (not 0x0800 for IPv4)
- ARP has **no IP header** — it is encapsulated directly in Ethernet
- ARP cannot be routed (no TTL, no IP source/destination)

---

## 3. Ethernet Framing Fundamentals

To understand ARP, you must first understand the Ethernet frame that carries it.

### Ethernet II Frame (DIX — the standard today)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                  Preamble (7 bytes) + SFD (1 byte)            +
|                         (not in software capture)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Destination MAC Address (6 bytes)            |
+                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |  Source MAC Address (6 bytes) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         EtherType (2 bytes)   |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               +
|                                                               |
|                   Payload (46–1500 bytes)                     |
|              (ARP packet goes here when EtherType=0x0806)     |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    FCS / CRC (4 bytes)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Key EtherType values:**

| EtherType | Protocol  |
|-----------|-----------|
| 0x0800    | IPv4      |
| 0x0806    | ARP       |
| 0x0835    | RARP      |
| 0x86DD    | IPv6      |
| 0x8100    | 802.1Q (VLAN tagged) |
| 0x8847    | MPLS unicast |

**For ARP broadcasts:**

- Destination MAC = `ff:ff:ff:ff:ff:ff` (all broadcast)
- Source MAC = sender's actual MAC
- EtherType = `0x0806`

---

## 4. ARP Packet Structure

ARP is defined in **RFC 826** (1982). Despite its age, it is fundamentally unchanged.

### ARP Packet Header (28 bytes for IPv4/Ethernet)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Hardware Type (HTYPE)  |       Protocol Type (PTYPE)  |
|         2 bytes                |       2 bytes                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  HW Addr Len  | Proto Addr Len |          Operation           |
|  (HLEN) 1 byte| (PLEN) 1 byte  |    (OPER) 2 bytes           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|              Sender Hardware Address (SHA)                    |
+                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  (6 bytes for Ethernet)       |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               +
|              Sender Protocol Address (SPA)                    |
|              (4 bytes for IPv4)                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|              Target Hardware Address (THA)                    |
+                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  (6 bytes for Ethernet)       |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               +
|              Target Protocol Address (TPA)                    |
|              (4 bytes for IPv4)                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field Breakdown

| Field | Size | Value for IPv4/Ethernet | Meaning |
|-------|------|------------------------|---------|
| HTYPE | 2 bytes | `0x0001` | Hardware type: Ethernet |
| PTYPE | 2 bytes | `0x0800` | Protocol type: IPv4 |
| HLEN  | 1 byte  | `6`      | MAC address length in bytes |
| PLEN  | 1 byte  | `4`      | IPv4 address length in bytes |
| OPER  | 2 bytes | `1`=request, `2`=reply | Operation code |
| SHA   | HLEN bytes | sender's MAC | Sender Hardware Address |
| SPA   | PLEN bytes | sender's IPv4 | Sender Protocol Address |
| THA   | HLEN bytes | `00:00:00:00:00:00` (request) or target MAC (reply) | Target Hardware Address |
| TPA   | PLEN bytes | target's IPv4 | Target Protocol Address |

**HTYPE values (selected):**

| Value | Hardware |
|-------|----------|
| 1     | Ethernet (10Mb) |
| 6     | IEEE 802 Networks |
| 7     | ARCNET |
| 15    | Frame Relay |
| 16    | ATM |
| 17    | HDLC |
| 18    | Fibre Channel |
| 19    | ATM (RFC 2225) |
| 20    | Serial Line |

### ARP Packet Size

For IPv4 over Ethernet:
- ARP payload = 28 bytes
- Ethernet header = 14 bytes (dest MAC 6 + src MAC 6 + EtherType 2)
- Total frame = 14 + 28 = 42 bytes (padded to 60 bytes minimum Ethernet frame + 4 bytes FCS = 64 bytes minimum)

### Hex Dump of Real ARP Request

```
Ethernet Header:
ff ff ff ff ff ff        # Destination: broadcast
aa bb cc dd ee 01        # Source: sender's MAC
08 06                    # EtherType: ARP

ARP Payload:
00 01                    # HTYPE: Ethernet
08 00                    # PTYPE: IPv4
06                       # HLEN: 6
04                       # PLEN: 4
00 01                    # OPER: 1 (request)
aa bb cc dd ee 01        # SHA: sender MAC
c0 a8 01 0a              # SPA: 192.168.1.10
00 00 00 00 00 00        # THA: unknown (zeros)
c0 a8 01 14              # TPA: 192.168.1.20 (target)
```

---

## 5. ARP Operation — Complete Lifecycle

### Step-by-Step: Host A Sends to Host B (Same Subnet)

```
Network: 192.168.1.0/24
Host A: IP=192.168.1.10, MAC=AA:BB:CC:DD:EE:01
Host B: IP=192.168.1.20, MAC=AA:BB:CC:DD:EE:02
Host C: IP=192.168.1.30, MAC=AA:BB:CC:DD:EE:03

                Switch
                  |
    +-------------+-------------+
    |             |             |
  Host A        Host B        Host C
192.168.1.10  192.168.1.20  192.168.1.30
```

**Phase 1: Cache Miss**

```
Host A wants to send IP packet to 192.168.1.20
  |
  +--> Check ARP cache for 192.168.1.20
  |
  +--> MISS: no entry found
  |
  +--> Enqueue IP packet (hold it while ARP resolves)
  |
  +--> Construct ARP REQUEST
```

**Phase 2: ARP Request Broadcast**

```
Host A constructs ARP REQUEST:
  Ethernet dst:  ff:ff:ff:ff:ff:ff  (broadcast ALL hosts)
  Ethernet src:  AA:BB:CC:DD:EE:01
  EtherType:     0x0806
  ARP OPER:      1 (request)
  SHA:           AA:BB:CC:DD:EE:01  (my MAC)
  SPA:           192.168.1.10       (my IP)
  THA:           00:00:00:00:00:00  (don't know yet)
  TPA:           192.168.1.20       (who has this IP?)

Host A  ----broadcast ARP REQUEST--->  Switch
                                          |
                         +----------------+----------------+
                         |                                 |
                      Host B (receives)              Host C (receives)
```

**Phase 3: All Hosts Receive, Only Target Replies**

```
Host C receives ARP REQUEST:
  TPA = 192.168.1.20 ≠ my IP (192.168.1.30)
  --> DISCARD
  --> Optionally: update own cache with A's IP→MAC mapping (SHA/SPA)
      [This is called "passive caching" or "learning"]

Host B receives ARP REQUEST:
  TPA = 192.168.1.20 = MY IP!
  --> PROCESS
  --> Update own cache: 192.168.1.10 → AA:BB:CC:DD:EE:01
      (learned from SHA/SPA fields — optimization)
  --> Construct ARP REPLY
```

**Phase 4: ARP Reply (Unicast)**

```
Host B constructs ARP REPLY:
  Ethernet dst:  AA:BB:CC:DD:EE:01  (unicast back to requester)
  Ethernet src:  AA:BB:CC:DD:EE:02
  EtherType:     0x0806
  ARP OPER:      2 (reply)
  SHA:           AA:BB:CC:DD:EE:02  (my MAC — the answer!)
  SPA:           192.168.1.20       (my IP)
  THA:           AA:BB:CC:DD:EE:01  (requester's MAC)
  TPA:           192.168.1.10       (requester's IP)

Host B ----unicast ARP REPLY----> Host A
```

**Phase 5: Cache Update and Packet Delivery**

```
Host A receives ARP REPLY:
  --> Extract: SPA=192.168.1.20 → SHA=AA:BB:CC:DD:EE:02
  --> Store in ARP cache with TTL (typically 20 minutes Linux default)
  --> Dequeue held IP packet(s)
  --> Wrap IP packet in Ethernet frame with dst=AA:BB:CC:DD:EE:02
  --> Send!

ARP Cache on Host A after resolution:
  +------------------+-------------------+--------+----------+
  | IP Address       | MAC Address       | Type   | TTL      |
  +------------------+-------------------+--------+----------+
  | 192.168.1.20     | AA:BB:CC:DD:EE:02 | dynamic| 20:00    |
  +------------------+-------------------+--------+----------+
```

### Complete Timeline View

```
Time  Host A          Switch          Host B           Host C
 t0   [needs to                                        
       send to B]     
 t1   [cache miss]    
 t2   ---ARP REQ--->  flood all -->   [recv REQ]       [recv REQ]
 t3                                   [update cache]   [discard]
 t4                                   [send REPLY]     
 t5   <--ARP REPLY-   forward ---     
 t6   [update cache]  
 t7   [send IP pkt]-> forward -->     [recv IP pkt]    
```

---

## 6. ARP Cache — Design and Behavior

### Cache States (Linux Model)

The Linux kernel ARP implementation uses a neighbor state machine:

```
                            +--------+
                            |  NONE  |  (initial / deleted)
                            +--------+
                                 |
                            [create entry]
                                 v
                          +------------+
                    +---->| INCOMPLETE  |  (ARP sent, waiting reply)
                    |     +------------+
                    |           |
                    |     [reply received]
                    |           v
     [traffic     +---------+  +---------+
      received]   | REACHABLE|  | FAILED  |  (no reply after retries)
                  +---------+  +---------+
                       |
                  [reachable time expires]
                       v
                  +---------+
                  |  STALE  |  (entry exists but unverified)
                  +---------+
                       |
                  [traffic needs to be sent]
                       v
                  +---------+
                  |  DELAY  |  (wait for upper-layer confirm)
                  +---------+
                       |
                  [no NUD confirm received]
                       v
                  +---------+
                  |  PROBE  |  (send unicast ARP probes)
                  +---------+
                       |
                  [probe succeeded / failed]
               [REACHABLE]  /  [FAILED]
```

### NUD — Neighbor Unreachability Detection

NUD (defined in RFC 4861 for IPv6, applied to IPv4 in Linux) is the mechanism that keeps the ARP cache accurate:

- **REACHABLE**: recently confirmed working (via ARP reply or TCP ACK)
- **STALE**: not confirmed recently, but still used (sent speculatively)
- **DELAY**: sent traffic but waiting for upper-layer confirmation
- **PROBE**: sending unicast ARP probes to re-confirm
- **FAILED**: host is unreachable, drop packets

### Cache Timers

```
ARP Cache Entry Timeline:

Time 0        T_reach       T_stale     T_probe×N    T_failed
  |              |              |            |            |
  v              v              v            v            v
[REACHABLE]-->[STALE]------>[DELAY]--->[PROBE]×3--->[FAILED]
                              |
                         [upper-layer
                          confirmation]
                              |
                              v
                         [REACHABLE]

Linux defaults:
  base_reachable_time = 30 seconds
  reachable_time      = random(0.5×base, 1.5×base) ≈ 15–45s
  delay_probe_time    = 5 seconds
  retrans_time        = 1 second (between probes)
  ucast_solicit       = 3 (probe attempts before FAILED)
  gc_stale_time       = 60 seconds (garbage collection)
```

### Cache Lookup Algorithm

```
When sending IP packet to destination D:

1. Is D on-link? (same subnet as any local interface)
   YES: look up D directly in neighbor cache
   NO:  look up default gateway (or specific route's gateway) in neighbor cache

2. Neighbor cache lookup for IP I:
   FOUND (any state except FAILED):
     - Use cached MAC
     - If STALE: transition to DELAY, schedule NUD check
     - If FAILED: return EHOSTUNREACH
   NOT FOUND:
     - Create INCOMPLETE entry
     - Send ARP request
     - Queue packet (up to unres_qlen packets, default 3)
     - Return (packet sent when ARP resolves)
```

### Viewing and Managing ARP Cache

```bash
# View ARP cache (old style)
arp -n

# View ARP cache (new style via iproute2)
ip neigh show

# Example output:
# 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
# 192.168.1.20 dev eth0 lladdr aa:bb:cc:dd:ee:02 STALE
# 192.168.1.50 dev eth0  FAILED

# Add static ARP entry
ip neigh add 192.168.1.99 lladdr de:ad:be:ef:00:01 dev eth0

# Delete entry
ip neigh del 192.168.1.20 dev eth0

# Flush entire cache
ip neigh flush all

# Flush stale entries only
ip neigh flush dev eth0 nud stale
```

---

## 7. ARP Message Types — All Opcodes

ARP operation codes (OPER field) registered with IANA:

| OPER | Name | Description |
|------|------|-------------|
| 1 | REQUEST | "Who has IP X? Tell IP Y" |
| 2 | REPLY | "IP X is at MAC M" |
| 3 | request Reverse | RARP request |
| 4 | reply Reverse | RARP reply |
| 5 | DRARP-Request | Dynamic RARP request |
| 6 | DRARP-Reply | Dynamic RARP reply |
| 7 | DRARP-Error | Dynamic RARP error |
| 8 | InARP-Request | Inverse ARP request |
| 9 | InARP-Reply | Inverse ARP reply |
| 10 | ARP-NAK | Negative acknowledgment for ATM ARP |

---

## 8. Gratuitous ARP (GARP)

### What Is GARP?

A **Gratuitous ARP** is an ARP request or reply in which the sender announces its own IP-to-MAC mapping — without anyone asking. The term "gratuitous" means "uncalled for, unprompted."

```
ARP REQUEST (Gratuitous):
  Ethernet dst:  ff:ff:ff:ff:ff:ff  (broadcast)
  Ethernet src:  AA:BB:CC:DD:EE:02
  ARP OPER:      1 (request) OR 2 (reply)
  SHA:           AA:BB:CC:DD:EE:02  (my MAC)
  SPA:           192.168.1.20       (my IP)
  THA:           ff:ff:ff:ff:ff:ff  (broadcast, or 00:00:00:00:00:00)
  TPA:           192.168.1.20       (same as SPA — asking "who has MY OWN IP?")
```

Key distinguishing feature: **SPA == TPA** (sender's IP = target IP).

### GARP Use Cases

**1. IP Conflict Detection (startup)**
```
Host boots up, assigned 192.168.1.20
Sends GARP: "Does anyone else have 192.168.1.20?"

If ANOTHER host replies:
  --> IP conflict detected! Take action (Linux: print warning, accept/reject)
If no one replies:
  --> No conflict, proceed normally
```

**2. Cache Update After Interface Change**
```
Host changes MAC address (NIC replacement, MAC spoofing, bonding failover):
  Old state in all neighbors' caches: 192.168.1.20 → AA:BB:CC:DD:EE:OLD
  
  Host sends GARP with new MAC:
    SHA: AA:BB:CC:DD:EE:NEW
    SPA: 192.168.1.20
  
  All neighbors update their caches immediately:
    192.168.1.20 → AA:BB:CC:DD:EE:NEW
```

**3. High Availability / Failover (VRRP, HSRP, keepalived)**
```
Primary Router: IP=192.168.1.1, MAC=AA:BB:CC:DD:EE:P1
Backup Router:  IP=192.168.1.1, MAC=AA:BB:CC:DD:EE:P2

Primary fails!

Backup promotes itself:
  Sends GARP: "192.168.1.1 is now at AA:BB:CC:DD:EE:P2"

All hosts flush old entry, update:
  192.168.1.1 → AA:BB:CC:DD:EE:P2  (now points to backup)

Traffic resumes within milliseconds.
```

**4. VM Live Migration**
```
VM migrates from Host1 to Host2 (different physical NIC)
Sends GARP from Host2's NIC to announce new location
Network updates immediately
```

### GARP vs Regular ARP Reply Distinction

```
Regular ARP Reply:      Sent only in response to a request
                        Unicast to requester
                        TPA ≠ SPA

Gratuitous ARP:         Sent spontaneously (unsolicited)
                        Broadcast to all
                        TPA == SPA
```

---

## 9. Proxy ARP

### Concept

Proxy ARP (RFC 1027) allows a router or host to answer ARP requests on behalf of another device. The proxy answers with its OWN MAC address, and then forwards traffic to the real destination.

```
Host A              Router (Proxy ARP enabled)         Host B
192.168.1.10        192.168.1.1 / 192.168.2.1         192.168.2.20
    |                       |                               |
    | ARP req: "Who has     |                               |
    | 192.168.2.20?"        |                               |
    +---------------------->|                               |
    |                       | (Router knows B is reachable) |
    |                       | (via 192.168.2.x interface)   |
    |   ARP reply:          |                               |
    | "192.168.2.20 is at   |                               |
    |  MY MAC (router MAC)" |                               |
    |<----------------------+                               |
    |                       |                               |
    | IP packet to          |                               |
    | dst MAC=router MAC    |                               |
    | dst IP=192.168.2.20   |                               |
    +---------------------->|                               |
    |                       | [routes, sends ARP on .2      |
    |                       |  network, forwards packet]    |
    |                       +------------------------------>|
```

### When Proxy ARP Is Used

- Legacy networks where hosts have no default gateway configured
- Split-network setups where two subnets share the same physical segment
- VPN concentrators answering for remote hosts
- Certain cloud/SDN implementations

### Proxy ARP Risks

- Can mask misconfigurations (hosts don't need correct subnet masks)
- Can increase ARP traffic
- Security: enables MITM if enabled carelessly

```bash
# Enable/disable Proxy ARP on Linux interface
echo 1 > /proc/sys/net/ipv4/conf/eth0/proxy_arp
# or
sysctl -w net.ipv4.conf.eth0.proxy_arp=1
```

---

## 10. ARP Probe and ARP Announcement (IPv4LL / RFC 5227)

### IPv4 Link-Local Address Configuration

When DHCP fails, hosts may self-assign an address in 169.254.x.x range. RFC 5227 defines the process using ARP probes and announcements.

### ARP Probe

```
Purpose: Test if an IP is already in use before claiming it

ARP PROBE:
  Ethernet dst:  ff:ff:ff:ff:ff:ff
  ARP OPER:      1 (request)
  SHA:           MY_MAC
  SPA:           0.0.0.0           <-- KEY: zero sender IP (not yet assigned)
  THA:           00:00:00:00:00:00
  TPA:           192.168.1.20      (candidate address being tested)

Process:
  1. Wait random 0-1 second (probe_wait)
  2. Send 3 probes at 1-2 second intervals (probe_num=3, probe_min=1, probe_max=2)
  3. Wait announce_wait (2 seconds) after last probe
  4. If no reply received: address is available, claim it
  5. If reply received: conflict! Choose new address, repeat
```

### ARP Announcement

```
After successful probe, announce the new address:

ARP ANNOUNCEMENT:
  Ethernet dst:  ff:ff:ff:ff:ff:ff
  ARP OPER:      1 (request)
  SHA:           MY_MAC
  SPA:           192.168.1.20      (the now-claimed address)
  THA:           00:00:00:00:00:00
  TPA:           192.168.1.20      (same — this is like GARP)

Send 2 announcements at 2-second interval.
```

The distinction from GARP: SPA=0.0.0.0 (probe) vs SPA=TPA (announcement/GARP).

---

## 11. Reverse ARP (RARP)

### Concept

**RARP** (RFC 903, 1984) is the opposite of ARP: a diskless workstation knows its own MAC address but not its IP address, and broadcasts asking "What is the IP address for my MAC?"

```
RARP Request (diskless client at boot):
  "I am MAC aa:bb:cc:dd:ee:01. What is my IP address?"
  
RARP Server (on the network) responds:
  "MAC aa:bb:cc:dd:ee:01 → IP 192.168.1.10"
```

### RARP Limitations

- Requires a RARP server on EVERY subnet (no routing)
- Returns only an IP (no gateway, subnet mask, DNS)
- Obsoleted by BOOTP → DHCP

**RARP is essentially dead.** Modern systems use DHCP. Understanding it is important for historical context and protocol design comprehension.

---

## 12. Inverse ARP (InARP)

### Concept

**InARP** (RFC 2390) is used in Frame Relay and ATM networks. In these networks, a host knows the DLCI (Data Link Connection Identifier — the Layer 2 address for Frame Relay) but not the IP address at the other end of the virtual circuit.

InARP reverses the question: "I know the Layer 2 endpoint (DLCI), what is the Layer 3 (IP) address there?"

```
Standard ARP:  IP  → MAC    ("who has IP X?")
InARP:         MAC → IP     ("what IP is at DLCI Y?")
```

Used primarily in:
- Frame Relay networks
- ATM networks
- Any multipoint WAN where Layer 2 IDs are known but Layer 3 IDs are not

---

## 13. ARP in Routing — Same Subnet vs Different Subnet

### Case 1: Same Subnet

```
Host A (192.168.1.10/24) → Host B (192.168.1.20/24)

Step 1: A checks: is 192.168.1.20 in my subnet 192.168.1.0/24? YES
Step 2: A sends ARP REQUEST for 192.168.1.20
Step 3: B replies with its MAC
Step 4: A sends Ethernet frame directly to B's MAC
        Ethernet dst: B's MAC
        IP dst:       192.168.1.20
```

### Case 2: Different Subnet (Gateway)

```
Host A (192.168.1.10/24) → Server (10.0.0.5/24)

Step 1: A checks: is 10.0.0.5 in my subnet 192.168.1.0/24? NO
Step 2: A looks up routing table: next hop = 192.168.1.1 (gateway)
Step 3: A sends ARP REQUEST for 192.168.1.1 (the GATEWAY, not the destination!)
Step 4: Router replies with its MAC
Step 5: A sends Ethernet frame to Router's MAC, but IP dst is still 10.0.0.5

         Host A sends:
           Ethernet dst: ROUTER_MAC (192.168.1.1)
           IP dst:       10.0.0.5   (unchanged!)

Step 6: Router receives frame, strips Ethernet header
Step 7: Router looks at IP dst 10.0.0.5, finds route via its 10.0.0.1 interface
Step 8: Router sends ARP on 10.0.0.x network for 10.0.0.5
Step 9: Router forwards IP packet in new Ethernet frame:
           Ethernet dst: SERVER_MAC
           IP dst:       10.0.0.5
```

### Key Insight: IP Address Never Changes; MAC Changes at Each Hop

```
+--------+      +--------+      +--------+      +--------+
| Host A |      |Router 1|      |Router 2|      | Server |
| .1.10  |      |.1.1/.2.1|     |.2.2/.3.1|     | .3.5   |
+--------+      +--------+      +--------+      +--------+

Segment 1 frame (Host A → Router 1):
  Eth dst: R1_MAC  | IP src: .1.10 | IP dst: .3.5

Segment 2 frame (Router 1 → Router 2):
  Eth dst: R2_MAC  | IP src: .1.10 | IP dst: .3.5

Segment 3 frame (Router 2 → Server):
  Eth dst: SRV_MAC | IP src: .1.10 | IP dst: .3.5

IP addresses NEVER change along the path (ignoring NAT).
Ethernet MAC addresses change at EVERY hop.
ARP runs independently on each segment.
```

---

## 14. ARP and VLANs

### VLAN Basics

A VLAN (Virtual LAN) creates logically separate broadcast domains on the same physical infrastructure. Each VLAN is its own ARP domain.

```
Physical Switch
+---------------------------------------------------+
|                                                   |
|  VLAN 10 (192.168.10.0/24)  VLAN 20 (192.168.20.0/24) |
|  +------------------+       +------------------+ |
|  | Port1  Port2     |       | Port3  Port4     | |
|  |  H1     H2       |       |  H3     H4       | |
|  +------------------+       +------------------+ |
|                                                   |
+---------------------------------------------------+
```

- H1 can ARP for H2 (same VLAN)
- H1 CANNOT directly ARP for H3 (different VLAN — different broadcast domain)
- Inter-VLAN traffic requires a Layer 3 device (router or L3 switch)

### 802.1Q VLAN Tagging and ARP

```
Tagged ARP Frame (802.1Q):

+---------+---------+--------+--------+---------+
| Dst MAC | Src MAC | 0x8100 | TCI    | 0x0806  | ... ARP payload ...
| 6 bytes | 6 bytes | 2 bytes| 2 bytes| 2 bytes |
+---------+---------+--------+--------+---------+
             ^               ^
          EtherType       Tag Control Info
          for 802.1Q       PCP(3b)|DEI(1b)|VID(12b)
                                           ^ VLAN ID (0-4095)

The ARP payload itself is identical — the VLAN tag is in the Ethernet header.
```

### ARP in Router-on-a-Stick

```
One physical interface on router has multiple sub-interfaces:

Router:
  eth0.10  192.168.10.1/24  (gateway for VLAN 10)
  eth0.20  192.168.20.1/24  (gateway for VLAN 20)

H1 (VLAN 10) ARPs for its default gateway (192.168.10.1):
  → Router sub-interface eth0.10 responds

H3 (VLAN 20) ARPs for its default gateway (192.168.20.1):
  → Router sub-interface eth0.20 responds
```

---

## 15. ARP Security Vulnerabilities

### Root Cause

ARP has **no authentication mechanism**. Any host can send any ARP message claiming any IP-to-MAC mapping. The protocol was designed for trusted LAN environments in 1982.

### Attack Surface

```
ARP Trust Model (Assumed by Protocol):
  "Any ARP reply received is from the legitimate owner of that IP"
  
Reality:
  Any host on the LAN can inject arbitrary ARP messages.
  ARP cache poisoning requires only Layer 2 access.
  No sequence numbers, no nonces, no cryptographic verification.
```

---

## 16. ARP Spoofing / Poisoning — Attack Mechanics

### Attack Goal

Redirect traffic from its intended destination to the attacker's machine.

### Classic Man-in-the-Middle via ARP Poisoning

```
Before Attack:
  Host A  ARP cache: 192.168.1.1  → ROUTER_MAC
  Host A  ARP cache: 192.168.1.20 → HOST_B_MAC
  Host B  ARP cache: 192.168.1.10 → HOST_A_MAC
  Router  ARP cache: 192.168.1.10 → HOST_A_MAC

After Attacker Sends Forged ARP Replies:

Attacker sends to Host A:
  ARP REPLY: "192.168.1.1 is at ATTACKER_MAC"
  (pretending to be the router)
  
Attacker sends to Router:
  ARP REPLY: "192.168.1.10 is at ATTACKER_MAC"
  (pretending to be Host A)

Resulting State:
  Host A  ARP cache: 192.168.1.1  → ATTACKER_MAC  ← POISONED
  Router  ARP cache: 192.168.1.10 → ATTACKER_MAC  ← POISONED

Traffic Flow:
  Host A → [thinks it's going to router] → Attacker → Router → Internet
  Response → Router → [thinks A is at attacker] → Attacker → Host A

Attacker is now:
  - Reading all A's traffic (passive eavesdropping)
  - Possibly modifying packets (active MITM)
  - Enabling SSL stripping, session hijacking, etc.
```

### Denial of Service via ARP

```
Attacker poisons all hosts with:
  ARP REPLY: "192.168.1.1 (gateway) is at 00:00:00:00:00:00"
  (or any nonexistent MAC)

Result: All hosts send traffic to a MAC that doesn't exist → frames dropped → DoS
```

### MAC Flooding (Related Attack)

```
Attacker floods switch with frames from millions of fake MAC addresses.
Switch CAM table overflows.
Switch enters "fail-open" mode: broadcasts ALL frames to ALL ports.
Attacker can now see all traffic.
```

### ARP Cache Poisoning Tool Logic (for educational understanding)

```
Continuous ARP poisoning requires:
1. Send forged ARP replies at regular intervals (every 2-5 seconds)
   because victim caches eventually expire and re-ARP legitimately
2. Enable IP forwarding on attacker to maintain connectivity
3. Intercept and forward packets (be transparent)
```

---

## 17. ARP Defense Mechanisms

### 1. Dynamic ARP Inspection (DAI) — Cisco Switch Feature

```
Mechanism:
  Switch maintains DHCP snooping binding table:
    {MAC, IP, Port, VLAN} tuples

  For every ARP packet on untrusted ports:
    Check: does (MAC, IP) in ARP match DHCP snooping table?
    YES → forward
    NO  → drop and log

  Trusted ports (uplinks, DHCP servers): not inspected

Topology:
+--------+    untrusted    +--------+    trusted    +--------+
| Host A |---port (DAI)-->-| Switch |-----------+->-| Router |
+--------+                 +--------+           |   +--------+
+--------+    untrusted        |            trusted
|Attacker|---port (DAI)-->-    |        +--------+
+--------+                     +------> | DHCP   |
                                         | Server |
                                         +--------+
Attacker sends forged ARP → Switch checks binding table 
→ IP/MAC mismatch → DROP
```

### 2. Static ARP Entries

```bash
# Manually define critical entries (gateway, servers)
ip neigh add 192.168.1.1 lladdr AA:BB:CC:DD:EE:FF dev eth0 nud permanent

# These cannot be overwritten by received ARP replies
# Useful for: gateways, DNS servers, critical infrastructure
```

### 3. ARP Spoofing Detection Tools

```
arpwatch: monitors ARP traffic, alerts on MAC/IP changes
  - Maintains database of (IP, MAC, timestamp)
  - Alerts: new station, changed ethernet address, flip-flop (A→B→A)

XArp: Windows GUI tool for ARP monitoring
arpalert: lightweight daemon, similar to arpwatch
```

### 4. Private VLANs (PVLANs)

```
Primary VLAN 100:
  Isolated port: can only communicate with promiscuous port (router/gateway)
  Community port: can communicate with same community + promiscuous
  Promiscuous port: can communicate with all ports

Isolated hosts:
  Cannot ARP for each other (ARP broadcast not forwarded to isolated ports)
  Can only ARP for the gateway
  
Prevents ARP-based MITM between hosts on same VLAN.
```

### 5. Port Security (MAC Limiting)

```
Switch port configured to allow max 1 MAC address:
  First MAC learned: allowed
  Second MAC: port shutdown or violation action

Prevents attacker from injecting frames with spoofed source MACs.
```

### 6. 802.1X Network Access Control

```
Hosts must authenticate before network access.
Prevents unauthorized hosts from joining the LAN.
Eliminates attacker's ability to be on-segment.
```

---

## 18. ARP in Virtualization and Cloud

### Virtual Switch (vSwitch) and ARP

```
Physical Host:
+----------------------------------------------------+
|                                                    |
|  VM1 (192.168.1.10)    VM2 (192.168.1.20)         |
|  vNIC: v-MAC-1         vNIC: v-MAC-2              |
|       |                      |                     |
|       +----------+-----------+                     |
|                  |                                 |
|             vSwitch (software)                     |
|                  |                                 |
|             Physical NIC (p-MAC)                   |
|                  |                                 |
+------------------|-----------------------------+----+
                   |
            Physical Network

VM1 ARPs for VM2:
  If same host: vSwitch forwards within host (no physical traffic)
  If different host: vSwitch forwards via physical NIC
                     Physical NIC sends frame with p-MAC src
                     But Ethernet payload has VM1's ARP with v-MAC-1 as SHA
```

### ARP in VXLAN (Virtual Extensible LAN)

```
VXLAN encapsulates Layer 2 frames in UDP/IP, enabling L2 over L3 networks.

ARP flood reduction in VXLAN:

Traditional: ARP broadcasts flood the entire VXLAN overlay
Optimization (ARP suppression/proxy):
  VTEP (VXLAN Tunnel Endpoint) maintains IP→MAC table
  When VM ARPs, VTEP responds locally (proxy ARP) if it knows the answer
  Avoids broadcast across entire overlay network

+--------+  ARP REQ  +---------+      +---------+  ARP REP  +--------+
|  VM A  |---------->|  VTEP 1 |      |  VTEP 2 |<--------- |  VM B  |
|192.1.10|           |  (DB:   |      |  (DB:   |           |192.1.20|
+--------+           |192.1.20 |      |192.1.10 |           +--------+
                     | →B_MAC) |      | →A_MAC) |
                     +---------+      +---------+
                          |                |
                   VXLAN-encapped     VXLAN-encapped
                   over IP fabric     over IP fabric
```

### ARP in Kubernetes

```
Pod Network (CNI):
  Each Pod gets an IP from PodCIDR
  Pods on same node: communicate via Linux bridge (cbr0/cni0)
    ARP is local to the bridge
  Pods on different nodes: depends on CNI plugin

Flannel (host-gw mode):
  Routes pod subnets through node IPs
  ARP resolves node MACs, not pod MACs
  Pods think next hop is their gateway (node)

Flannel (VXLAN mode):
  VXLAN overlay, ARP suppression via flannel daemon
  Flannel maintains ARP tables in kernel:
    ip neigh add <pod-ip> lladdr <vtep-mac> dev flannel.1 nud permanent

Calico:
  BGP-based routing, each pod route announced
  ARP proxy on host: host answers ARP for pod IPs
  Pods only ever ARP for their node's MAC
```

---

## 19. ARP vs NDP (IPv6 Neighbor Discovery)

IPv6 replaces ARP with **NDP (Neighbor Discovery Protocol)**, defined in RFC 4861.

### Comparison Table

| Feature | ARP (IPv4) | NDP (IPv6) |
|---------|-----------|-----------|
| Protocol | Separate (EtherType 0x0806) | ICMPv6 (within IPv6) |
| Transport | Ethernet frame directly | IPv6 packet (ICMPv6 type 135/136) |
| Discovery | Broadcast | Multicast (solicited-node multicast) |
| Request type | ARP Request | Neighbor Solicitation (NS) |
| Reply type | ARP Reply | Neighbor Advertisement (NA) |
| GARP equivalent | Gratuitous ARP | Unsolicited NA |
| Router discovery | Requires separate ICMP | Integrated (RS/RA) |
| Address autoconfiguration | DHCP only | SLAAC (Stateless Address Autoconfiguration) |
| Security | None | SEcure Neighbor Discovery (SEND, RFC 3971) |
| Duplicate detection | ARP Probe | Duplicate Address Detection (DAD) |
| MTU discovery | Manual config | Router Advertisement |

### NDP Multicast vs ARP Broadcast

```
ARP: Sends to ff:ff:ff:ff:ff:ff (every host receives and must process)

NDP: Uses solicited-node multicast address
  IPv6 addr: 2001:db8::1234:5678:9abc
  Solicited-node multicast: ff02::1:ff78:9abc (last 24 bits of IPv6 addr)
  Ethernet multicast: 33:33:ff:78:9a:bc

Only hosts that share those last 24 bits of IPv6 addr need to process it.
Drastically reduces unnecessary CPU interrupts on large networks.
```

---

## 20. Linux Kernel ARP Implementation

### Key Source Files (Linux kernel)

```
net/ipv4/arp.c          — Main ARP implementation
net/core/neighbour.c    — Generic neighbor discovery subsystem
include/net/arp.h       — ARP definitions
include/net/neighbour.h — Neighbor table structures
```

### Kernel Data Structures

```c
/* Neighbor entry (ARP cache entry in Linux) */
struct neighbour {
    struct neighbour __rcu  *next;        /* hash chain */
    struct neigh_table      *tbl;         /* which table (arp_tbl) */
    struct neigh_parms      *parms;       /* parameters */
    unsigned long            confirmed;   /* last confirmed timestamp */
    unsigned long            updated;     /* last update timestamp */
    rwlock_t                 lock;
    refcount_t               refcnt;
    unsigned int             arp_queue_len_bytes;
    struct sk_buff_head      arp_queue;   /* packets queued pending resolution */
    struct timer_list        timer;       /* state machine timer */
    unsigned long            used;        /* last used timestamp */
    atomic_t                 probes;      /* probe counter */
    __u8                     flags;
    __u8                     nud_state;   /* NUD state machine state */
    __u8                     type;        /* RTN_UNICAST/BROADCAST/etc */
    __u8                     dead;        /* marked for deletion */
    u8                       protocol;
    seqlock_t                ha_lock;
    unsigned char            ha[ALIGN(MAX_ADDR_LEN, sizeof(unsigned long))]; /* hardware address (MAC) */
    struct hh_cache          hh;          /* cached hardware header */
    int                    (*output)(struct neighbour *, struct sk_buff *);
    const struct neigh_ops  *ops;
    struct list_head         gc_list;
    struct rcu_head          rcu;
    struct net_device       *dev;         /* network interface */
    u8                       primary_key[0]; /* IP address key */
};

/* ARP table */
struct neigh_table arp_tbl = {
    .family     = AF_INET,
    .key_len    = 4,             /* IPv4: 4 bytes */
    .protocol   = cpu_to_be16(ETH_P_IP),
    .hash       = arp_hash,
    .key_eq     = arp_key_eq,
    .constructor= arp_constructor,
    .id         = "arp_cache",
    .parms      = { ... },       /* timing parameters */
    .gc_interval= 30 * HZ,
    .gc_thresh1 = 128,           /* no GC below this */
    .gc_thresh2 = 512,           /* GC at this threshold */
    .gc_thresh3 = 1024,          /* hard limit */
};
```

### ARP Reception Path

```
NIC receives frame → netif_receive_skb()
  → eth_type_trans() (identifies EtherType 0x0806)
  → arp_rcv() called

arp_rcv():
  1. Validate packet (length, HTYPE, PTYPE, HLEN, PLEN)
  2. Call arp_process()

arp_process():
  1. Extract SHA, SPA, THA, TPA from packet
  2. Check if SPA conflicts with own IP → log warning
  3. Look up TPA in own IP addresses
  4. If not for us and not proxy ARP enabled → drop
  5. Update neighbor cache entry for SHA/SPA (passive learning)
  6. If OPER == REQUEST and TPA == our IP:
       - Send ARP REPLY
  7. If OPER == REPLY:
       - Update neighbor cache entry for SHA/SPA
       - Wake up any queued packets
```

---

## 21. ARP Tuning — Linux sysctls

```bash
# View all ARP-related sysctls
sysctl -a | grep 'net.ipv4.*arp\|net.ipv4.*neigh'

# Key parameters (per-interface or default):
# Replace 'eth0' with 'default' for system-wide defaults

# --- Timeouts ---

# Base reachable time (ms) — randomized ±50%
net.ipv4.neigh.eth0.base_reachable_time_ms = 30000

# Retransmit time (ms) — how long to wait between ARP retries
net.ipv4.neigh.eth0.retrans_time_ms = 1000

# Time before GC can collect a stale entry (seconds)
net.ipv4.neigh.eth0.gc_stale_time = 60

# How long to wait in DELAY state before probing (seconds)
net.ipv4.neigh.eth0.delay_probe_time = 5

# --- Probe limits ---

# Number of unicast probes before declaring FAILED
net.ipv4.neigh.eth0.ucast_solicit = 3

# Number of multicast probes for address resolution
net.ipv4.neigh.eth0.mcast_solicit = 3

# --- Cache limits ---

# Threshold 1: No GC below this count
net.ipv4.neigh.eth0.gc_thresh1 = 128

# Threshold 2: GC kicks in above this
net.ipv4.neigh.eth0.gc_thresh2 = 512

# Threshold 3: Hard maximum (return ENOBUFS above this)
net.ipv4.neigh.eth0.gc_thresh3 = 1024

# --- Queue ---

# Max queued packets while resolving (per neighbor)
net.ipv4.neigh.eth0.unres_qlen = 101
net.ipv4.neigh.eth0.unres_qlen_bytes = 212992

# --- ARP filter / ignore ---

# Ignore ARP requests on all interfaces except the one with matching IP
net.ipv4.conf.all.arp_ignore = 1
# 0 = reply for any local IP on any interface (default)
# 1 = reply only if target IP is configured on incoming interface
# 2 = reply only if target IP is configured on incoming interface
#     AND sender's IP is in same subnet
# 8 = do not reply at all

# Control which source IP is used in ARP requests
net.ipv4.conf.all.arp_announce = 2
# 0 = use any local IP as source (default, can confuse routing)
# 1 = avoid IP not in subnet of outgoing interface
# 2 = always use best local IP for outgoing interface (recommended)
#     (important for OSPF, BGP, multi-homed hosts)

# Accept gratuitous ARP
net.ipv4.conf.all.arp_accept = 0
# 0 = update only existing entries (default)
# 1 = create new entry from GARP even if not solicited
```

### arp_ignore and arp_announce Deep Dive

```
arp_announce = 2 is critical for multi-homed servers (multiple IPs/interfaces):

Without arp_announce=2:
  Interface eth0: 192.168.1.10/24
  Interface eth1: 10.0.0.10/24

  Host sends ARP request out eth1.
  Kernel might use 192.168.1.10 as SPA (source IP from eth0!)
  
  Network sees: "192.168.1.10 is at eth1's MAC address"
  Confusion: .1.x traffic might route to wrong interface

With arp_announce=2:
  ARP out eth1 will use 10.0.0.10 as SPA (correct interface IP)
  Each interface announces only its own IP
  Clean, unambiguous ARP tables across the network

This is REQUIRED configuration for LVS (Linux Virtual Server) setups.
```

---

## 22. ARP in High Availability Scenarios

### VRRP (Virtual Router Redundancy Protocol)

```
VRRP uses a Virtual IP (VIP) and Virtual MAC:
  Virtual MAC format: 00:00:5E:00:01:{VRID}
  VRID = Virtual Router ID (0-255)

Example:
  VRID = 51
  Virtual MAC = 00:00:5E:00:01:33 (0x33 = 51 decimal)

Primary Router (priority 200):
  Physical IP: 192.168.1.2
  Virtual IP:  192.168.1.1  (shared)
  Active: sends VRRP advertisements every 1 second

Backup Router (priority 100):
  Physical IP: 192.168.1.3
  Virtual IP:  192.168.1.1  (shared)
  Passive: listening for VRRP advertisements

All hosts:
  ARP cache: 192.168.1.1 → 00:00:5E:00:01:33 (Virtual MAC)

Failover sequence:
  1. Primary fails (stops sending VRRP adverts)
  2. Backup detects timeout (3 × interval)
  3. Backup assumes Master role
  4. Backup sends GARP: "192.168.1.1 is at 00:00:5E:00:01:33"
     (same virtual MAC — no ARP update needed!)
  5. Switch updates MAC table: Virtual MAC now on backup's port
  6. Traffic restored in <1 second

Key insight: Virtual MAC stays the same → ARP caches don't need updating
Only the switch CAM table needs to update (driven by GARP)
```

### keepalived + GARP

```
keepalived sends 3 GARPs on transition:
  - One at state change
  - Two more at 0, 1, 2 second intervals
  - Ensures all switches and hosts update caches

Configuration: /etc/keepalived/keepalived.conf
  garp_master_delay 5        # seconds to wait before sending GARP
  garp_master_refresh 0      # interval for periodic GARP (0=off)
  garp_master_repeat 1       # number of GARPs to send
```

---

## 23. C Implementation — Complete ARP Stack

```c
/* arp_stack.c
 * Complete ARP implementation using raw sockets (Linux)
 * Demonstrates: ARP request, reply, gratuitous ARP, cache
 * Compile: gcc -O2 -Wall -o arp_stack arp_stack.c
 * Run as root: sudo ./arp_stack <interface> <target_ip>
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>

#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>

#include <net/if.h>
#include <net/ethernet.h>
#include <net/if_arp.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include <linux/if_packet.h>
#include <linux/if_ether.h>

/* ─────────────────────────────────────────────────────────────
 * Constants & Types
 * ───────────────────────────────────────────────────────────── */

#define ETH_ADDR_LEN    6
#define IPV4_ADDR_LEN   4
#define ARP_PKT_LEN     28    /* ARP payload for IPv4/Ethernet */
#define FRAME_LEN       (14 + ARP_PKT_LEN)  /* Ethernet header + ARP */

#define ARP_CACHE_MAX   256
#define ARP_CACHE_TTL   1200  /* 20 minutes in seconds */

/* ARP Hardware Types */
#define ARPHRD_ETHER_    1

/* ARP Operation Codes */
#define ARPOP_REQUEST_   1
#define ARPOP_REPLY_     2

/* ─────────────────────────────────────────────────────────────
 * ARP Packet Structure (RFC 826)
 * NOTE: All fields are network byte order (big-endian)
 * ───────────────────────────────────────────────────────────── */
#pragma pack(push, 1)   /* ensure no padding */

typedef struct {
    uint8_t  dst[ETH_ADDR_LEN];   /* Destination MAC */
    uint8_t  src[ETH_ADDR_LEN];   /* Source MAC */
    uint16_t ethertype;            /* 0x0806 for ARP */
} eth_hdr_t;

typedef struct {
    uint16_t htype;                /* Hardware type: 1 = Ethernet */
    uint16_t ptype;                /* Protocol type: 0x0800 = IPv4 */
    uint8_t  hlen;                 /* Hardware addr len: 6 */
    uint8_t  plen;                 /* Protocol addr len: 4 */
    uint16_t oper;                 /* 1=request, 2=reply */
    uint8_t  sha[ETH_ADDR_LEN];   /* Sender Hardware Address */
    uint8_t  spa[IPV4_ADDR_LEN];  /* Sender Protocol Address */
    uint8_t  tha[ETH_ADDR_LEN];   /* Target Hardware Address */
    uint8_t  tpa[IPV4_ADDR_LEN];  /* Target Protocol Address */
} arp_pkt_t;

typedef struct {
    eth_hdr_t eth;
    arp_pkt_t arp;
} arp_frame_t;

#pragma pack(pop)

/* ─────────────────────────────────────────────────────────────
 * ARP Cache
 * ───────────────────────────────────────────────────────────── */

typedef enum {
    ARP_ENTRY_EMPTY,
    ARP_ENTRY_INCOMPLETE,
    ARP_ENTRY_REACHABLE,
    ARP_ENTRY_STALE,
    ARP_ENTRY_FAILED,
    ARP_ENTRY_PERMANENT,
} arp_entry_state_t;

typedef struct {
    uint8_t           ip[IPV4_ADDR_LEN];
    uint8_t           mac[ETH_ADDR_LEN];
    arp_entry_state_t state;
    time_t            timestamp;
    uint8_t           probe_count;
} arp_entry_t;

typedef struct {
    arp_entry_t entries[ARP_CACHE_MAX];
    int         count;
} arp_cache_t;

static arp_cache_t g_arp_cache = {0};

/* ─────────────────────────────────────────────────────────────
 * Interface Information
 * ───────────────────────────────────────────────────────────── */

typedef struct {
    char    name[IFNAMSIZ];
    int     ifindex;
    uint8_t mac[ETH_ADDR_LEN];
    uint8_t ip[IPV4_ADDR_LEN];
    int     fd;           /* raw socket fd */
} iface_t;

/* ─────────────────────────────────────────────────────────────
 * Utility Functions
 * ───────────────────────────────────────────────────────────── */

static void
print_mac(const uint8_t *mac)
{
    printf("%02x:%02x:%02x:%02x:%02x:%02x",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static void
print_ip(const uint8_t *ip)
{
    printf("%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
}

static int
ip_equal(const uint8_t *a, const uint8_t *b)
{
    return memcmp(a, b, IPV4_ADDR_LEN) == 0;
}

static const char *
arp_state_str(arp_entry_state_t state)
{
    switch (state) {
        case ARP_ENTRY_EMPTY:      return "EMPTY";
        case ARP_ENTRY_INCOMPLETE: return "INCOMPLETE";
        case ARP_ENTRY_REACHABLE:  return "REACHABLE";
        case ARP_ENTRY_STALE:      return "STALE";
        case ARP_ENTRY_FAILED:     return "FAILED";
        case ARP_ENTRY_PERMANENT:  return "PERMANENT";
        default:                   return "UNKNOWN";
    }
}

/* ─────────────────────────────────────────────────────────────
 * ARP Cache Operations
 * ───────────────────────────────────────────────────────────── */

/* Look up IP in cache; returns pointer or NULL */
static arp_entry_t *
cache_lookup(const uint8_t *ip)
{
    for (int i = 0; i < ARP_CACHE_MAX; i++) {
        if (g_arp_cache.entries[i].state != ARP_ENTRY_EMPTY &&
            ip_equal(g_arp_cache.entries[i].ip, ip)) {
            return &g_arp_cache.entries[i];
        }
    }
    return NULL;
}

/* Add or update cache entry */
static arp_entry_t *
cache_update(const uint8_t *ip, const uint8_t *mac, arp_entry_state_t state)
{
    /* First check if entry already exists */
    arp_entry_t *entry = cache_lookup(ip);

    if (!entry) {
        /* Find empty slot */
        for (int i = 0; i < ARP_CACHE_MAX; i++) {
            if (g_arp_cache.entries[i].state == ARP_ENTRY_EMPTY) {
                entry = &g_arp_cache.entries[i];
                g_arp_cache.count++;
                break;
            }
        }
    }

    if (!entry) {
        fprintf(stderr, "ARP cache full!\n");
        return NULL;
    }

    /* Don't overwrite permanent entries */
    if (entry->state == ARP_ENTRY_PERMANENT && state != ARP_ENTRY_PERMANENT) {
        return entry;
    }

    memcpy(entry->ip, ip, IPV4_ADDR_LEN);
    if (mac) {
        memcpy(entry->mac, mac, ETH_ADDR_LEN);
    }
    entry->state     = state;
    entry->timestamp = time(NULL);
    entry->probe_count = 0;

    return entry;
}

/* Expire stale entries */
static void
cache_expire(void)
{
    time_t now = time(NULL);
    for (int i = 0; i < ARP_CACHE_MAX; i++) {
        arp_entry_t *e = &g_arp_cache.entries[i];
        if (e->state == ARP_ENTRY_EMPTY ||
            e->state == ARP_ENTRY_PERMANENT) {
            continue;
        }
        if (now - e->timestamp > ARP_CACHE_TTL) {
            printf("[cache] Expiring entry: ");
            print_ip(e->ip);
            printf(" (state: %s)\n", arp_state_str(e->state));
            memset(e, 0, sizeof(*e));
            g_arp_cache.count--;
        }
    }
}

/* Print full cache */
static void
cache_dump(void)
{
    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║                    ARP Cache                        ║\n");
    printf("╠══════════════════╦═══════════════════╦═════════════╣\n");
    printf("║ IP Address       ║ MAC Address        ║ State       ║\n");
    printf("╠══════════════════╬═══════════════════╬═════════════╣\n");

    int shown = 0;
    for (int i = 0; i < ARP_CACHE_MAX; i++) {
        arp_entry_t *e = &g_arp_cache.entries[i];
        if (e->state == ARP_ENTRY_EMPTY) continue;
        printf("║ ");
        print_ip(e->ip);
        printf("       ║ ");
        print_mac(e->mac);
        printf(" ║ %-11s ║\n", arp_state_str(e->state));
        shown++;
    }

    if (shown == 0) {
        printf("║               (empty cache)                          ║\n");
    }
    printf("╚══════════════════╩═══════════════════╩═════════════╝\n\n");
}

/* ─────────────────────────────────────────────────────────────
 * Network Interface Setup
 * ───────────────────────────────────────────────────────────── */

static int
iface_open(iface_t *iface, const char *name)
{
    struct ifreq ifr;

    strncpy(iface->name, name, IFNAMSIZ - 1);

    /* Create raw socket for ARP (EtherType 0x0806) */
    iface->fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ARP));
    if (iface->fd < 0) {
        perror("socket(AF_PACKET)");
        return -1;
    }

    /* Get interface index */
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
    if (ioctl(iface->fd, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl(SIOCGIFINDEX)");
        close(iface->fd);
        return -1;
    }
    iface->ifindex = ifr.ifr_ifindex;

    /* Get MAC address */
    if (ioctl(iface->fd, SIOCGIFHWADDR, &ifr) < 0) {
        perror("ioctl(SIOCGIFHWADDR)");
        close(iface->fd);
        return -1;
    }
    memcpy(iface->mac, ifr.ifr_hwaddr.sa_data, ETH_ADDR_LEN);

    /* Get IP address */
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
    if (ioctl(iface->fd, SIOCGIFADDR, &ifr) < 0) {
        perror("ioctl(SIOCGIFADDR)");
        /* Non-fatal: interface might not have IP yet */
        memset(iface->ip, 0, IPV4_ADDR_LEN);
    } else {
        struct sockaddr_in *sin = (struct sockaddr_in *)&ifr.ifr_addr;
        memcpy(iface->ip, &sin->sin_addr.s_addr, IPV4_ADDR_LEN);
    }

    /* Bind to interface */
    struct sockaddr_ll sll = {
        .sll_family   = AF_PACKET,
        .sll_protocol = htons(ETH_P_ARP),
        .sll_ifindex  = iface->ifindex,
    };
    if (bind(iface->fd, (struct sockaddr *)&sll, sizeof(sll)) < 0) {
        perror("bind");
        close(iface->fd);
        return -1;
    }

    printf("[iface] Interface: %s\n", iface->name);
    printf("[iface] Index:     %d\n", iface->ifindex);
    printf("[iface] MAC:       ");
    print_mac(iface->mac);
    printf("\n");
    printf("[iface] IP:        ");
    print_ip(iface->ip);
    printf("\n\n");

    return 0;
}

static void
iface_close(iface_t *iface)
{
    if (iface->fd >= 0) {
        close(iface->fd);
        iface->fd = -1;
    }
}

/* ─────────────────────────────────────────────────────────────
 * ARP Frame Construction
 * ───────────────────────────────────────────────────────────── */

static void
build_arp_frame(arp_frame_t *frame,
                const uint8_t *eth_dst,
                const uint8_t *eth_src,
                uint16_t       oper,
                const uint8_t *sha,
                const uint8_t *spa,
                const uint8_t *tha,
                const uint8_t *tpa)
{
    static const uint8_t bcast[ETH_ADDR_LEN] = {0xff,0xff,0xff,0xff,0xff,0xff};
    static const uint8_t zeros[ETH_ADDR_LEN] = {0};

    /* Ethernet header */
    memcpy(frame->eth.dst, eth_dst ? eth_dst : bcast, ETH_ADDR_LEN);
    memcpy(frame->eth.src, eth_src, ETH_ADDR_LEN);
    frame->eth.ethertype = htons(ETH_P_ARP);

    /* ARP payload */
    frame->arp.htype = htons(ARPHRD_ETHER_);
    frame->arp.ptype = htons(ETH_P_IP);
    frame->arp.hlen  = ETH_ADDR_LEN;
    frame->arp.plen  = IPV4_ADDR_LEN;
    frame->arp.oper  = htons(oper);

    memcpy(frame->arp.sha, sha, ETH_ADDR_LEN);
    memcpy(frame->arp.spa, spa, IPV4_ADDR_LEN);
    memcpy(frame->arp.tha, tha ? tha : zeros, ETH_ADDR_LEN);
    memcpy(frame->arp.tpa, tpa, IPV4_ADDR_LEN);
}

/* ─────────────────────────────────────────────────────────────
 * ARP Send Functions
 * ───────────────────────────────────────────────────────────── */

static int
send_frame(const iface_t *iface, const arp_frame_t *frame)
{
    struct sockaddr_ll dst = {
        .sll_family   = AF_PACKET,
        .sll_protocol = htons(ETH_P_ARP),
        .sll_ifindex  = iface->ifindex,
        .sll_halen    = ETH_ADDR_LEN,
    };
    memcpy(dst.sll_addr, frame->eth.dst, ETH_ADDR_LEN);

    ssize_t sent = sendto(iface->fd, frame, sizeof(*frame), 0,
                          (struct sockaddr *)&dst, sizeof(dst));
    if (sent < 0) {
        perror("sendto");
        return -1;
    }
    return 0;
}

/* Send ARP Request: "Who has <target_ip>? Tell <my_ip>" */
int
arp_send_request(const iface_t *iface, const uint8_t *target_ip)
{
    static const uint8_t bcast[ETH_ADDR_LEN] = {0xff,0xff,0xff,0xff,0xff,0xff};
    arp_frame_t frame;

    build_arp_frame(&frame,
                    bcast,          /* Ethernet dst: broadcast */
                    iface->mac,     /* Ethernet src: our MAC */
                    ARPOP_REQUEST_,
                    iface->mac,     /* SHA: our MAC */
                    iface->ip,      /* SPA: our IP */
                    NULL,           /* THA: zeros (unknown) */
                    target_ip);     /* TPA: who we're looking for */

    printf("[arp_req] Sending ARP REQUEST: who has ");
    print_ip(target_ip);
    printf("? Tell ");
    print_ip(iface->ip);
    printf("\n");

    /* Mark as incomplete in cache */
    cache_update(target_ip, NULL, ARP_ENTRY_INCOMPLETE);

    return send_frame(iface, &frame);
}

/* Send ARP Reply in response to a request */
int
arp_send_reply(const iface_t *iface,
               const uint8_t *requester_mac,
               const uint8_t *requester_ip)
{
    arp_frame_t frame;

    build_arp_frame(&frame,
                    requester_mac,  /* Ethernet dst: unicast to requester */
                    iface->mac,     /* Ethernet src: our MAC */
                    ARPOP_REPLY_,
                    iface->mac,     /* SHA: our MAC (the answer!) */
                    iface->ip,      /* SPA: our IP */
                    requester_mac,  /* THA: requester's MAC */
                    requester_ip);  /* TPA: requester's IP */

    printf("[arp_rep] Sending ARP REPLY: ");
    print_ip(iface->ip);
    printf(" is at ");
    print_mac(iface->mac);
    printf(" → to ");
    print_mac(requester_mac);
    printf("\n");

    return send_frame(iface, &frame);
}

/* Send Gratuitous ARP: announce our IP→MAC to everyone */
int
arp_send_gratuitous(const iface_t *iface)
{
    static const uint8_t bcast[ETH_ADDR_LEN] = {0xff,0xff,0xff,0xff,0xff,0xff};
    arp_frame_t frame;

    /* GARP: SPA == TPA, THA = broadcast */
    build_arp_frame(&frame,
                    bcast,          /* Ethernet dst: broadcast */
                    iface->mac,     /* Ethernet src */
                    ARPOP_REQUEST_, /* Can be REQUEST or REPLY — REQUEST is more compatible */
                    iface->mac,     /* SHA: our MAC */
                    iface->ip,      /* SPA: our IP */
                    bcast,          /* THA: broadcast (GARP convention) */
                    iface->ip);     /* TPA: same as SPA — GARP! */

    printf("[garp]    Sending Gratuitous ARP for ");
    print_ip(iface->ip);
    printf(" (MAC: ");
    print_mac(iface->mac);
    printf(")\n");

    return send_frame(iface, &frame);
}

/* Send ARP Probe (RFC 5227): test if IP is in use before claiming */
int
arp_send_probe(const iface_t *iface, const uint8_t *candidate_ip)
{
    static const uint8_t bcast[ETH_ADDR_LEN] = {0xff,0xff,0xff,0xff,0xff,0xff};
    static const uint8_t zeros_ip[IPV4_ADDR_LEN] = {0,0,0,0};
    arp_frame_t frame;

    /* Probe: SPA = 0.0.0.0 (not yet claimed), TPA = candidate */
    build_arp_frame(&frame,
                    bcast,
                    iface->mac,
                    ARPOP_REQUEST_,
                    iface->mac,
                    zeros_ip,       /* SPA = 0.0.0.0 — KEY DIFFERENCE */
                    NULL,
                    candidate_ip);

    printf("[arp_probe] Probing IP: ");
    print_ip(candidate_ip);
    printf(" (SPA=0.0.0.0)\n");

    return send_frame(iface, &frame);
}

/* ─────────────────────────────────────────────────────────────
 * ARP Receive / Process
 * ───────────────────────────────────────────────────────────── */

static int
arp_receive(iface_t *iface, int timeout_ms)
{
    uint8_t buf[65536];
    struct sockaddr_ll from;
    socklen_t fromlen = sizeof(from);

    /* Set receive timeout */
    struct timeval tv = {
        .tv_sec  = timeout_ms / 1000,
        .tv_usec = (timeout_ms % 1000) * 1000,
    };
    setsockopt(iface->fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    ssize_t len = recvfrom(iface->fd, buf, sizeof(buf), 0,
                           (struct sockaddr *)&from, &fromlen);
    if (len < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            return 0;  /* timeout */
        }
        perror("recvfrom");
        return -1;
    }

    if ((size_t)len < sizeof(arp_frame_t)) {
        return 0;  /* too short */
    }

    arp_frame_t *frame = (arp_frame_t *)buf;

    /* Validate: must be ARP for IPv4/Ethernet */
    if (ntohs(frame->eth.ethertype) != ETH_P_ARP)  return 0;
    if (ntohs(frame->arp.htype) != ARPHRD_ETHER_)  return 0;
    if (ntohs(frame->arp.ptype) != ETH_P_IP)        return 0;
    if (frame->arp.hlen != ETH_ADDR_LEN)            return 0;
    if (frame->arp.plen != IPV4_ADDR_LEN)           return 0;

    uint16_t oper = ntohs(frame->arp.oper);

    printf("[recv] ARP %s from ",
           oper == ARPOP_REQUEST_ ? "REQUEST" :
           oper == ARPOP_REPLY_   ? "REPLY"   : "UNKNOWN");
    print_ip(frame->arp.spa);
    printf(" (");
    print_mac(frame->arp.sha);
    printf(") → for ");
    print_ip(frame->arp.tpa);
    printf("\n");

    /* ── Passive learning: always update cache from SHA/SPA ── */
    /* Only if SPA is not 0.0.0.0 (ARP probe) */
    static const uint8_t zeros_ip[IPV4_ADDR_LEN] = {0};
    if (!ip_equal(frame->arp.spa, zeros_ip)) {
        cache_update(frame->arp.spa, frame->arp.sha, ARP_ENTRY_REACHABLE);
        printf("[cache] Learned: ");
        print_ip(frame->arp.spa);
        printf(" → ");
        print_mac(frame->arp.sha);
        printf("\n");
    }

    /* ── Process based on operation ── */
    if (oper == ARPOP_REQUEST_) {
        /* Is someone asking for our IP? */
        if (ip_equal(frame->arp.tpa, iface->ip)) {
            printf("[recv] Request is for us! Sending reply.\n");
            arp_send_reply(iface, frame->arp.sha, frame->arp.spa);
        }
    } else if (oper == ARPOP_REPLY_) {
        /* Update cache with the reply */
        arp_entry_t *entry = cache_update(frame->arp.spa,
                                          frame->arp.sha,
                                          ARP_ENTRY_REACHABLE);
        if (entry) {
            printf("[cache] Updated from reply: ");
            print_ip(entry->ip);
            printf(" → ");
            print_mac(entry->mac);
            printf(" [REACHABLE]\n");
        }
    }

    return 1;  /* processed */
}

/* ─────────────────────────────────────────────────────────────
 * ARP Resolution: Request + Wait for Reply
 * ───────────────────────────────────────────────────────────── */

int
arp_resolve(iface_t *iface, const uint8_t *target_ip,
            uint8_t *result_mac, int timeout_ms)
{
    /* Check cache first */
    arp_entry_t *entry = cache_lookup(target_ip);
    if (entry && entry->state == ARP_ENTRY_REACHABLE) {
        memcpy(result_mac, entry->mac, ETH_ADDR_LEN);
        printf("[resolve] Cache hit: ");
        print_ip(target_ip);
        printf(" → ");
        print_mac(result_mac);
        printf("\n");
        return 0;
    }

    /* Cache miss: send ARP request */
    if (arp_send_request(iface, target_ip) < 0) {
        return -1;
    }

    /* Wait for reply */
    struct timeval deadline, now;
    gettimeofday(&deadline, NULL);
    deadline.tv_usec += timeout_ms * 1000;
    deadline.tv_sec  += deadline.tv_usec / 1000000;
    deadline.tv_usec %= 1000000;

    while (1) {
        gettimeofday(&now, NULL);
        int remaining = (int)((deadline.tv_sec - now.tv_sec) * 1000 +
                              (deadline.tv_usec - now.tv_usec) / 1000);
        if (remaining <= 0) break;

        arp_receive(iface, remaining);

        /* Check if resolved */
        entry = cache_lookup(target_ip);
        if (entry && entry->state == ARP_ENTRY_REACHABLE) {
            memcpy(result_mac, entry->mac, ETH_ADDR_LEN);
            printf("[resolve] Resolved: ");
            print_ip(target_ip);
            printf(" → ");
            print_mac(result_mac);
            printf("\n");
            return 0;
        }
    }

    /* Mark as failed */
    cache_update(target_ip, NULL, ARP_ENTRY_FAILED);
    fprintf(stderr, "[resolve] FAILED to resolve ");
    print_ip(target_ip);
    fprintf(stderr, "\n");
    return -1;
}

/* ─────────────────────────────────────────────────────────────
 * ARP Listener (background processing)
 * ───────────────────────────────────────────────────────────── */

void
arp_listen_loop(iface_t *iface, int iterations)
{
    printf("[listen] Starting ARP listener (%d iterations)...\n", iterations);
    for (int i = 0; i < iterations; i++) {
        arp_receive(iface, 1000);  /* 1 second timeout */
        cache_expire();
    }
}

/* ─────────────────────────────────────────────────────────────
 * Main
 * ───────────────────────────────────────────────────────────── */

int
main(int argc, char *argv[])
{
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <interface> <target_ip>\n", argv[0]);
        fprintf(stderr, "Example: %s eth0 192.168.1.1\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *ifname    = argv[1];
    const char *target_str = argv[2];

    /* Parse target IP */
    uint8_t target_ip[IPV4_ADDR_LEN];
    {
        struct in_addr addr;
        if (inet_pton(AF_INET, target_str, &addr) != 1) {
            fprintf(stderr, "Invalid IP address: %s\n", target_str);
            return EXIT_FAILURE;
        }
        memcpy(target_ip, &addr.s_addr, IPV4_ADDR_LEN);
    }

    /* Open interface */
    iface_t iface = {.fd = -1};
    if (iface_open(&iface, ifname) < 0) {
        return EXIT_FAILURE;
    }

    /* 1. Send Gratuitous ARP (announce ourselves) */
    printf("=== Step 1: Gratuitous ARP ===\n");
    arp_send_gratuitous(&iface);
    sleep(1);

    /* 2. Probe target address (RFC 5227) */
    printf("\n=== Step 2: ARP Probe ===\n");
    arp_send_probe(&iface, target_ip);
    arp_receive(&iface, 500);

    /* 3. Resolve target */
    printf("\n=== Step 3: ARP Resolution ===\n");
    uint8_t resolved_mac[ETH_ADDR_LEN];
    int result = arp_resolve(&iface, target_ip, resolved_mac, 3000);

    if (result == 0) {
        printf("\n✓ Resolution successful!\n");
        printf("  ");
        print_ip(target_ip);
        printf(" → ");
        print_mac(resolved_mac);
        printf("\n");
    } else {
        printf("\n✗ Resolution failed (host unreachable or not responding)\n");
    }

    /* 4. Listen for more ARP traffic */
    printf("\n=== Step 4: Listening for ARP traffic (5 seconds) ===\n");
    arp_listen_loop(&iface, 5);

    /* 5. Dump final cache */
    printf("\n=== Final ARP Cache ===\n");
    cache_dump();

    iface_close(&iface);
    return EXIT_SUCCESS;
}
```

---

## 24. Rust Implementation — Complete ARP Stack

```rust
//! arp_stack.rs — Complete ARP implementation using raw sockets (Linux)
//!
//! Features:
//!   - ARP request/reply sending and receiving
//!   - ARP cache with state machine (INCOMPLETE/REACHABLE/STALE/FAILED)
//!   - Gratuitous ARP
//!   - ARP probe (RFC 5227)
//!   - Passive learning from received ARP packets
//!
//! Build: cargo build --release
//! Run:   sudo ./target/release/arp_stack <interface> <target_ip>
//!
//! Cargo.toml dependencies:
//!   [dependencies]
//!   libc = "0.2"

use libc::{
    AF_PACKET, ETH_P_ARP, ETH_P_IP, SOCK_RAW,
    bind, close, recvfrom, sendto, setsockopt, socket, ioctl,
    sockaddr, sockaddr_ll, timespec, timeval, ifreq,
    SIOCGIFHWADDR, SIOCGIFINDEX, SIOCGIFADDR,
    SOL_SOCKET, SO_RCVTIMEO,
    c_int, c_void, socklen_t, ssize_t,
    AF_INET,
};
use std::{
    collections::HashMap,
    io, mem,
    net::Ipv4Addr,
    time::{Duration, Instant},
    ffi::CString,
};

/* ─────────────────────────────────────────────────────────────
 * Constants
 * ───────────────────────────────────────────────────────────── */

const ETH_ADDR_LEN: usize   = 6;
const IPV4_ADDR_LEN: usize  = 4;
const ARPHRD_ETHER: u16     = 1;
const ARPOP_REQUEST: u16    = 1;
const ARPOP_REPLY: u16      = 2;
const ARP_CACHE_TTL: Duration = Duration::from_secs(1200); /* 20 min */

/* ─────────────────────────────────────────────────────────────
 * ARP Packet Structure (packed, RFC 826)
 * ───────────────────────────────────────────────────────────── */

/// Raw Ethernet II header (14 bytes)
#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct EthHeader {
    dst: [u8; ETH_ADDR_LEN],
    src: [u8; ETH_ADDR_LEN],
    ethertype: u16,  /* network byte order */
}

/// ARP packet payload for IPv4/Ethernet (28 bytes)
#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct ArpPacket {
    htype: u16,                  /* Hardware type (network byte order) */
    ptype: u16,                  /* Protocol type (network byte order) */
    hlen:  u8,                   /* Hardware address length */
    plen:  u8,                   /* Protocol address length */
    oper:  u16,                  /* Operation (network byte order) */
    sha:   [u8; ETH_ADDR_LEN],  /* Sender Hardware Address */
    spa:   [u8; IPV4_ADDR_LEN], /* Sender Protocol Address */
    tha:   [u8; ETH_ADDR_LEN],  /* Target Hardware Address */
    tpa:   [u8; IPV4_ADDR_LEN], /* Target Protocol Address */
}

/// Complete ARP frame (Ethernet header + ARP payload = 42 bytes)
#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct ArpFrame {
    eth: EthHeader,
    arp: ArpPacket,
}

impl ArpFrame {
    fn as_bytes(&self) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                self as *const ArpFrame as *const u8,
                mem::size_of::<ArpFrame>(),
            )
        }
    }
}

/* ─────────────────────────────────────────────────────────────
 * ARP Cache
 * ───────────────────────────────────────────────────────────── */

#[derive(Debug, Clone, PartialEq)]
enum ArpState {
    Incomplete,
    Reachable,
    Stale,
    Failed,
    Permanent,
}

impl ArpState {
    fn as_str(&self) -> &'static str {
        match self {
            ArpState::Incomplete => "INCOMPLETE",
            ArpState::Reachable  => "REACHABLE",
            ArpState::Stale      => "STALE",
            ArpState::Failed     => "FAILED",
            ArpState::Permanent  => "PERMANENT",
        }
    }
}

#[derive(Debug, Clone)]
struct ArpEntry {
    mac:        [u8; ETH_ADDR_LEN],
    state:      ArpState,
    created_at: Instant,
    updated_at: Instant,
    probes:     u8,
}

impl ArpEntry {
    fn new(mac: [u8; ETH_ADDR_LEN], state: ArpState) -> Self {
        let now = Instant::now();
        ArpEntry { mac, state, created_at: now, updated_at: now, probes: 0 }
    }

    fn is_expired(&self) -> bool {
        self.state != ArpState::Permanent &&
        self.updated_at.elapsed() > ARP_CACHE_TTL
    }

    fn is_usable(&self) -> bool {
        matches!(self.state, ArpState::Reachable | ArpState::Stale | ArpState::Permanent)
    }
}

/// ARP cache: IP → entry mapping
struct ArpCache {
    entries: HashMap<[u8; IPV4_ADDR_LEN], ArpEntry>,
}

impl ArpCache {
    fn new() -> Self {
        ArpCache { entries: HashMap::new() }
    }

    fn lookup(&self, ip: &[u8; IPV4_ADDR_LEN]) -> Option<&ArpEntry> {
        self.entries.get(ip).filter(|e| !e.is_expired())
    }

    fn update(&mut self, ip: [u8; IPV4_ADDR_LEN], mac: [u8; ETH_ADDR_LEN], state: ArpState) {
        /* Don't overwrite permanent entries with dynamic data */
        if let Some(existing) = self.entries.get(&ip) {
            if existing.state == ArpState::Permanent && state != ArpState::Permanent {
                return;
            }
        }

        let entry = self.entries.entry(ip).or_insert_with(|| ArpEntry::new(mac, state.clone()));
        entry.mac = mac;
        entry.state = state;
        entry.updated_at = Instant::now();
    }

    fn update_incomplete(&mut self, ip: [u8; IPV4_ADDR_LEN]) {
        let zeros = [0u8; ETH_ADDR_LEN];
        self.entries.entry(ip).or_insert_with(|| ArpEntry::new(zeros, ArpState::Incomplete));
    }

    fn expire(&mut self) {
        self.entries.retain(|ip, entry| {
            if entry.is_expired() {
                print!("[cache:expire] ");
                print_ip(ip);
                println!(" ({})", entry.state.as_str());
                false
            } else {
                true
            }
        });
    }

    fn dump(&self) {
        println!("\n╔══════════════════════════════════════════════════════╗");
        println!("║                    ARP Cache                        ║");
        println!("╠══════════════════╦═══════════════════╦═════════════╣");
        println!("║ IP Address       ║ MAC Address        ║ State       ║");
        println!("╠══════════════════╬═══════════════════╬═════════════╣");

        if self.entries.is_empty() {
            println!("║               (empty cache)                          ║");
        }

        for (ip, entry) in &self.entries {
            if entry.is_expired() { continue; }
            print!("║ {:15} ║ {:17} ║ {:<11} ║\n",
                ip_to_string(ip),
                mac_to_string(&entry.mac),
                entry.state.as_str());
        }
        println!("╚══════════════════╩═══════════════════╩═════════════╝\n");
    }
}

/* ─────────────────────────────────────────────────────────────
 * Helper Functions
 * ───────────────────────────────────────────────────────────── */

fn ip_to_string(ip: &[u8; IPV4_ADDR_LEN]) -> String {
    format!("{}.{}.{}.{}", ip[0], ip[1], ip[2], ip[3])
}

fn mac_to_string(mac: &[u8; ETH_ADDR_LEN]) -> String {
    format!("{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}",
        mac[0], mac[1], mac[2], mac[3], mac[4], mac[5])
}

fn print_ip(ip: &[u8; IPV4_ADDR_LEN]) {
    print!("{}", ip_to_string(ip));
}

fn ipv4_to_bytes(ip: Ipv4Addr) -> [u8; IPV4_ADDR_LEN] {
    ip.octets()
}

fn htons(val: u16) -> u16 { val.to_be() }
fn ntohs(val: u16) -> u16 { u16::from_be(val) }

/* ─────────────────────────────────────────────────────────────
 * Network Interface
 * ───────────────────────────────────────────────────────────── */

struct Iface {
    name:    String,
    ifindex: i32,
    mac:     [u8; ETH_ADDR_LEN],
    ip:      [u8; IPV4_ADDR_LEN],
    fd:      c_int,
}

impl Iface {
    fn open(name: &str) -> io::Result<Self> {
        let c_name = CString::new(name).expect("interface name");

        /* Create raw socket for ARP */
        let fd = unsafe {
            socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ARP as u16) as i32)
        };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }

        /* Get interface index via SIOCGIFINDEX */
        let mut ifr: ifreq = unsafe { mem::zeroed() };
        let name_bytes = c_name.as_bytes_with_nul();
        let copy_len = name_bytes.len().min(libc::IFNAMSIZ);
        unsafe {
            std::ptr::copy_nonoverlapping(
                name_bytes.as_ptr() as *const libc::c_char,
                ifr.ifr_name.as_mut_ptr(),
                copy_len,
            );
            if ioctl(fd, SIOCGIFINDEX as _, &mut ifr) < 0 {
                let e = io::Error::last_os_error();
                close(fd);
                return Err(e);
            }
        }
        let ifindex = unsafe { ifr.ifr_ifru.ifru_ifindex };

        /* Get MAC address via SIOCGIFHWADDR */
        unsafe {
            if ioctl(fd, SIOCGIFHWADDR as _, &mut ifr) < 0 {
                let e = io::Error::last_os_error();
                close(fd);
                return Err(e);
            }
        }
        let mut mac = [0u8; ETH_ADDR_LEN];
        mac.copy_from_slice(&unsafe { ifr.ifr_ifru.ifru_hwaddr }.sa_data[..ETH_ADDR_LEN]
            .iter().map(|&b| b as u8).collect::<Vec<_>>());

        /* Get IP address via SIOCGIFADDR */
        let mut ip = [0u8; IPV4_ADDR_LEN];
        unsafe {
            let mut ifr2: ifreq = mem::zeroed();
            std::ptr::copy_nonoverlapping(
                name_bytes.as_ptr() as *const libc::c_char,
                ifr2.ifr_name.as_mut_ptr(),
                copy_len,
            );
            if ioctl(fd, SIOCGIFADDR as _, &mut ifr2) == 0 {
                let sa = ifr2.ifr_ifru.ifru_addr;
                let sin = &sa as *const sockaddr as *const libc::sockaddr_in;
                let ip_u32 = (*sin).sin_addr.s_addr;
                ip.copy_from_slice(&ip_u32.to_ne_bytes());
            }
        }

        /* Bind to interface */
        let sll = sockaddr_ll {
            sll_family:   AF_PACKET as u16,
            sll_protocol: htons(ETH_P_ARP as u16),
            sll_ifindex:  ifindex,
            sll_hatype:   0,
            sll_pkttype:  0,
            sll_halen:    0,
            sll_addr:     [0; 8],
        };
        let bind_ret = unsafe {
            bind(fd,
                 &sll as *const sockaddr_ll as *const sockaddr,
                 mem::size_of::<sockaddr_ll>() as socklen_t)
        };
        if bind_ret < 0 {
            let e = io::Error::last_os_error();
            unsafe { close(fd); }
            return Err(e);
        }

        println!("[iface] Interface: {}", name);
        println!("[iface] Index:     {}", ifindex);
        println!("[iface] MAC:       {}", mac_to_string(&mac));
        println!("[iface] IP:        {}", ip_to_string(&ip));
        println!();

        Ok(Iface { name: name.to_owned(), ifindex, mac, ip, fd })
    }

    fn send_frame(&self, frame: &ArpFrame) -> io::Result<()> {
        let mut dst_sll: sockaddr_ll = unsafe { mem::zeroed() };
        dst_sll.sll_family   = AF_PACKET as u16;
        dst_sll.sll_protocol = htons(ETH_P_ARP as u16);
        dst_sll.sll_ifindex  = self.ifindex;
        dst_sll.sll_halen    = ETH_ADDR_LEN as u8;
        dst_sll.sll_addr[..ETH_ADDR_LEN].copy_from_slice(&frame.eth.dst);

        let bytes = frame.as_bytes();
        let sent = unsafe {
            sendto(self.fd,
                   bytes.as_ptr() as *const c_void,
                   bytes.len(),
                   0,
                   &dst_sll as *const sockaddr_ll as *const sockaddr,
                   mem::size_of::<sockaddr_ll>() as socklen_t)
        };
        if sent < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }

    fn recv_frame(&self, timeout_ms: u64) -> io::Result<Option<ArpFrame>> {
        /* Set receive timeout */
        let tv = timeval {
            tv_sec:  (timeout_ms / 1000) as libc::time_t,
            tv_usec: ((timeout_ms % 1000) * 1000) as libc::suseconds_t,
        };
        unsafe {
            setsockopt(self.fd, SOL_SOCKET, SO_RCVTIMEO,
                       &tv as *const timeval as *const c_void,
                       mem::size_of::<timeval>() as socklen_t);
        }

        let mut buf = [0u8; 65536];
        let mut from: sockaddr_ll = unsafe { mem::zeroed() };
        let mut fromlen = mem::size_of::<sockaddr_ll>() as socklen_t;

        let len = unsafe {
            recvfrom(self.fd,
                     buf.as_mut_ptr() as *mut c_void,
                     buf.len(),
                     0,
                     &mut from as *mut sockaddr_ll as *mut sockaddr,
                     &mut fromlen)
        };

        if len < 0 {
            let e = io::Error::last_os_error();
            if e.kind() == io::ErrorKind::WouldBlock ||
               e.kind() == io::ErrorKind::TimedOut {
                return Ok(None);
            }
            return Err(e);
        }

        if (len as usize) < mem::size_of::<ArpFrame>() {
            return Ok(None);
        }

        let frame: ArpFrame = unsafe {
            mem::transmute_copy(&*(buf.as_ptr() as *const ArpFrame))
        };

        Ok(Some(frame))
    }
}

impl Drop for Iface {
    fn drop(&mut self) {
        if self.fd >= 0 {
            unsafe { close(self.fd); }
        }
    }
}

/* ─────────────────────────────────────────────────────────────
 * ARP Frame Builder
 * ───────────────────────────────────────────────────────────── */

fn build_arp_frame(
    eth_dst: [u8; ETH_ADDR_LEN],
    eth_src: [u8; ETH_ADDR_LEN],
    oper:    u16,
    sha:     [u8; ETH_ADDR_LEN],
    spa:     [u8; IPV4_ADDR_LEN],
    tha:     [u8; ETH_ADDR_LEN],
    tpa:     [u8; IPV4_ADDR_LEN],
) -> ArpFrame {
    ArpFrame {
        eth: EthHeader {
            dst:       eth_dst,
            src:       eth_src,
            ethertype: htons(ETH_P_ARP as u16),
        },
        arp: ArpPacket {
            htype: htons(ARPHRD_ETHER),
            ptype: htons(ETH_P_IP as u16),
            hlen:  ETH_ADDR_LEN as u8,
            plen:  IPV4_ADDR_LEN as u8,
            oper:  htons(oper),
            sha,
            spa,
            tha,
            tpa,
        },
    }
}

/* ─────────────────────────────────────────────────────────────
 * ARP Engine
 * ───────────────────────────────────────────────────────────── */

struct ArpEngine {
    iface: Iface,
    cache: ArpCache,
}

impl ArpEngine {
    fn new(iface: Iface) -> Self {
        ArpEngine { iface, cache: ArpCache::new() }
    }

    /// Send ARP Request: "Who has <target_ip>? Tell <our_ip>"
    fn send_request(&mut self, target_ip: [u8; IPV4_ADDR_LEN]) -> io::Result<()> {
        const BCAST: [u8; ETH_ADDR_LEN] = [0xff; ETH_ADDR_LEN];
        const ZEROS: [u8; ETH_ADDR_LEN] = [0x00; ETH_ADDR_LEN];

        let frame = build_arp_frame(
            BCAST,
            self.iface.mac,
            ARPOP_REQUEST,
            self.iface.mac,
            self.iface.ip,
            ZEROS,
            target_ip,
        );

        println!("[arp_req] Sending ARP REQUEST: who has {}? Tell {}",
            ip_to_string(&target_ip),
            ip_to_string(&self.iface.ip));

        self.cache.update_incomplete(target_ip);
        self.iface.send_frame(&frame)
    }

    /// Send ARP Reply in response to a request
    fn send_reply(&self,
                  requester_mac: [u8; ETH_ADDR_LEN],
                  requester_ip:  [u8; IPV4_ADDR_LEN]) -> io::Result<()> {
        let frame = build_arp_frame(
            requester_mac,
            self.iface.mac,
            ARPOP_REPLY,
            self.iface.mac,
            self.iface.ip,
            requester_mac,
            requester_ip,
        );

        println!("[arp_rep] Sending ARP REPLY: {} is at {} → to {}",
            ip_to_string(&self.iface.ip),
            mac_to_string(&self.iface.mac),
            mac_to_string(&requester_mac));

        self.iface.send_frame(&frame)
    }

    /// Send Gratuitous ARP: announce our IP→MAC
    fn send_gratuitous(&self) -> io::Result<()> {
        const BCAST: [u8; ETH_ADDR_LEN] = [0xff; ETH_ADDR_LEN];

        /* GARP: SPA == TPA, THA = broadcast */
        let frame = build_arp_frame(
            BCAST,
            self.iface.mac,
            ARPOP_REQUEST,
            self.iface.mac,
            self.iface.ip,
            BCAST,
            self.iface.ip,  /* TPA == SPA */
        );

        println!("[garp]    Sending Gratuitous ARP: {} is at {}",
            ip_to_string(&self.iface.ip),
            mac_to_string(&self.iface.mac));

        self.iface.send_frame(&frame)
    }

    /// Send ARP Probe (RFC 5227): SPA = 0.0.0.0
    fn send_probe(&self, candidate_ip: [u8; IPV4_ADDR_LEN]) -> io::Result<()> {
        const BCAST: [u8; ETH_ADDR_LEN] = [0xff; ETH_ADDR_LEN];
        const ZEROS_IP: [u8; IPV4_ADDR_LEN] = [0; IPV4_ADDR_LEN];
        const ZEROS_MAC: [u8; ETH_ADDR_LEN] = [0; ETH_ADDR_LEN];

        let frame = build_arp_frame(
            BCAST,
            self.iface.mac,
            ARPOP_REQUEST,
            self.iface.mac,
            ZEROS_IP,       /* SPA = 0.0.0.0 */
            ZEROS_MAC,
            candidate_ip,
        );

        println!("[arp_probe] Probing IP: {} (SPA=0.0.0.0)",
            ip_to_string(&candidate_ip));

        self.iface.send_frame(&frame)
    }

    /// Receive and process one ARP frame (with timeout)
    fn receive_one(&mut self, timeout_ms: u64) -> io::Result<bool> {
        let frame = match self.iface.recv_frame(timeout_ms)? {
            Some(f) => f,
            None    => return Ok(false),
        };

        /* Validate */
        if ntohs(frame.eth.ethertype) != ETH_P_ARP as u16 { return Ok(false); }
        if ntohs(frame.arp.htype)     != ARPHRD_ETHER      { return Ok(false); }
        if ntohs(frame.arp.ptype)     != ETH_P_IP as u16   { return Ok(false); }
        if frame.arp.hlen != ETH_ADDR_LEN as u8            { return Ok(false); }
        if frame.arp.plen != IPV4_ADDR_LEN as u8           { return Ok(false); }

        let oper = ntohs(frame.arp.oper);
        let op_str = match oper {
            ARPOP_REQUEST => "REQUEST",
            ARPOP_REPLY   => "REPLY",
            _             => "UNKNOWN",
        };

        println!("[recv] ARP {} from {} ({}) → for {}",
            op_str,
            ip_to_string(&frame.arp.spa),
            mac_to_string(&frame.arp.sha),
            ip_to_string(&frame.arp.tpa));

        /* Passive learning: update cache from SHA/SPA if SPA != 0 */
        const ZEROS_IP: [u8; IPV4_ADDR_LEN] = [0; IPV4_ADDR_LEN];
        if frame.arp.spa != ZEROS_IP {
            self.cache.update(frame.arp.spa, frame.arp.sha, ArpState::Reachable);
            println!("[cache] Learned: {} → {}",
                ip_to_string(&frame.arp.spa),
                mac_to_string(&frame.arp.sha));
        }

        /* Process REQUEST: reply if it's for us */
        if oper == ARPOP_REQUEST && frame.arp.tpa == self.iface.ip {
            println!("[recv] Request is for us! Sending reply.");
            self.send_reply(frame.arp.sha, frame.arp.spa)?;
        }

        Ok(true)
    }

    /// Full ARP resolution: cache lookup → request → wait
    fn resolve(&mut self,
               target_ip: [u8; IPV4_ADDR_LEN],
               timeout: Duration) -> Option<[u8; ETH_ADDR_LEN]> {
        /* Cache hit? */
        if let Some(entry) = self.cache.lookup(&target_ip) {
            if entry.is_usable() {
                let mac = entry.mac;
                println!("[resolve] Cache hit: {} → {}",
                    ip_to_string(&target_ip),
                    mac_to_string(&mac));
                return Some(mac);
            }
        }

        /* Send request */
        if let Err(e) = self.send_request(target_ip) {
            eprintln!("[resolve] Failed to send request: {}", e);
            return None;
        }

        /* Poll until timeout */
        let deadline = Instant::now() + timeout;
        loop {
            let remaining = deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() { break; }

            let ms = remaining.as_millis().min(500) as u64;
            let _ = self.receive_one(ms);

            if let Some(entry) = self.cache.lookup(&target_ip) {
                if entry.is_usable() {
                    let mac = entry.mac;
                    println!("[resolve] Resolved: {} → {}",
                        ip_to_string(&target_ip),
                        mac_to_string(&mac));
                    return Some(mac);
                }
            }
        }

        /* Mark failed */
        self.cache.update(target_ip, [0u8; ETH_ADDR_LEN], ArpState::Failed);
        eprintln!("[resolve] FAILED to resolve {}", ip_to_string(&target_ip));
        None
    }

    /// Listen loop: process incoming ARP traffic
    fn listen(&mut self, duration: Duration) {
        println!("[listen] Listening for {} seconds...", duration.as_secs());
        let deadline = Instant::now() + duration;
        while Instant::now() < deadline {
            let _ = self.receive_one(500);
            self.cache.expire();
        }
    }
}

/* ─────────────────────────────────────────────────────────────
 * Main
 * ───────────────────────────────────────────────────────────── */

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <interface> <target_ip>", args[0]);
        eprintln!("Example: {} eth0 192.168.1.1", args[0]);
        std::process::exit(1);
    }

    let ifname     = &args[1];
    let target_str = &args[2];

    /* Parse target IP */
    let target_ipv4: Ipv4Addr = target_str.parse().expect("invalid IPv4");
    let target_ip = ipv4_to_bytes(target_ipv4);

    /* Open interface */
    let iface = Iface::open(ifname).expect("failed to open interface");
    let mut engine = ArpEngine::new(iface);

    /* Step 1: Gratuitous ARP */
    println!("=== Step 1: Gratuitous ARP ===");
    engine.send_gratuitous().expect("GARP failed");
    std::thread::sleep(Duration::from_secs(1));

    /* Step 2: Probe target */
    println!("\n=== Step 2: ARP Probe ===");
    engine.send_probe(target_ip).expect("probe failed");
    let _ = engine.receive_one(500);

    /* Step 3: Resolve */
    println!("\n=== Step 3: ARP Resolution ===");
    match engine.resolve(target_ip, Duration::from_secs(3)) {
        Some(mac) => {
            println!("\n✓ Resolution successful!");
            println!("  {} → {}", ip_to_string(&target_ip), mac_to_string(&mac));
        }
        None => {
            println!("\n✗ Resolution failed");
        }
    }

    /* Step 4: Listen */
    println!("\n=== Step 4: Listening for ARP traffic (5 seconds) ===");
    engine.listen(Duration::from_secs(5));

    /* Step 5: Dump cache */
    println!("=== Final ARP Cache ===");
    engine.cache.dump();
}
```

---

## 25. Packet Capture and Analysis

### Using tcpdump

```bash
# Capture all ARP traffic
tcpdump -i eth0 arp -v

# Capture ARP for a specific IP
tcpdump -i eth0 arp and host 192.168.1.20

# Save to file for Wireshark analysis
tcpdump -i eth0 arp -w arp_capture.pcap

# Example output:
# 12:34:56.123456 ARP, Request who-has 192.168.1.20 tell 192.168.1.10, length 28
# 12:34:56.124000 ARP, Reply 192.168.1.20 is-at aa:bb:cc:dd:ee:02, length 28
```

### Using arping

```bash
# Send ARP request (like ping but at Layer 2)
arping -I eth0 192.168.1.20

# Send gratuitous ARP
arping -I eth0 -A 192.168.1.10   # ARP announcement
arping -I eth0 -U 192.168.1.10   # Unsolicited ARP (GARP REQUEST)

# Count and deadline
arping -c 3 -w 5 -I eth0 192.168.1.20
```

### Using ip/arp commands

```bash
# Show current ARP cache
ip neigh show
ip neigh show dev eth0

# Show specific entry
ip neigh show 192.168.1.20

# Add permanent entry
ip neigh add 192.168.1.99 lladdr de:ad:be:ef:00:01 dev eth0 nud permanent

# Change state of entry
ip neigh change 192.168.1.20 dev eth0 nud stale

# Delete entry
ip neigh del 192.168.1.20 dev eth0

# Flush entries (with filter options)
ip neigh flush dev eth0
ip neigh flush dev eth0 nud stale
ip neigh flush to 192.168.1.0/24
```

---

## 26. ARP in Containers and Kubernetes

### Docker Bridge Networking

```
Docker creates docker0 bridge:
  IP: 172.17.0.1/16

Containers get veth pairs:
  Container side: eth0 in container network namespace
  Host side:     vethXXXXXX in host, added to docker0 bridge

ARP flow for container → container (same host):
  Container A (172.17.0.2) → Container B (172.17.0.3)
  A ARPs on eth0 (container ns)
  ARP goes to docker0 bridge
  Bridge forwards to B's veth
  B responds
  Bridge learns MAC, subsequent frames forwarded directly

ARP flow for container → external:
  Container ARPs for its gateway (172.17.0.1 = docker0)
  docker0 responds with its own MAC
  Container sends to docker0's MAC
  Host does NAT (MASQUERADE) and sends out physical NIC
```

### Kubernetes pod-to-pod ARP (Flannel host-gw)

```
Node1: 10.0.0.1, PodCIDR: 10.244.1.0/24
Node2: 10.0.0.2, PodCIDR: 10.244.2.0/24

Pod on Node1 (10.244.1.5) → Pod on Node2 (10.244.2.5):

Route on Node1:
  10.244.2.0/24 via 10.0.0.2 dev eth0

Pod sends to 10.244.2.5:
  Kernel: route lookup → gateway is 10.0.0.2
  ARP for 10.0.0.2 on eth0
  Gets Node2's MAC
  Sends packet: Eth dst=Node2_MAC, IP dst=10.244.2.5

Node2 receives:
  IP dst=10.244.2.5 is local (PodCIDR)
  Route: 10.244.2.5 via cni0 bridge
  ARP for 10.244.2.5 on cni0
  Delivers to pod
```

### Kubernetes Service IP (kube-proxy / iptables)

```
ClusterIP: 10.96.0.1 (virtual, not assigned to any interface)

This IP does NOT have an ARP entry!
It is handled entirely by iptables DNAT rules (kube-proxy):
  -A KUBE-SERVICES -d 10.96.0.1 -p tcp --dport 443 -j KUBE-SVC-xxx

When pod sends to 10.96.0.1:
  Route: default gateway → ARP for gateway MAC
  iptables intercepts before routing
  DNAT to actual pod IP (e.g., 10.244.1.10:443)
  ARP for actual pod IP

Service IPs are intentionally un-ARPable (ICMP unreachable if no kube-proxy).
```

---

## 27. ARP Edge Cases and Gotchas

### 1. Duplicate IP Detection Timing Race

```
If two hosts boot simultaneously with the same IP:
  Both send ARP probe at ~same time
  Both might not see each other's probe (network delay)
  Both claim the IP
  Both send ARP announcement
  All other hosts on network receive conflicting GARPs
  Result: continuous ARP thrashing, connectivity issues
  
Defense: Exponential backoff + random jitter in probe timing (RFC 5227)
```

### 2. ARP Cache Poisoning via REPLY Without REQUEST

```
RFC 826 states: process ARP replies even without a pending request.
Rationale: caches should stay up-to-date.
Exploit: attacker sends unsolicited ARP REPLY → cache poisoned.

Linux default (arp_accept = 0): ONLY update existing entries from unsolicited replies
                                 Do NOT create new entries
Linux (arp_accept = 1):         Create new entries from unsolicited replies (dangerous!)
```

### 3. Asymmetric ARP Learning

```
Host A sends ARP request for B:
  All hosts update their A→MAC cache (from SHA/SPA in request)
  Only B sends reply, so only A gets B→MAC

Host C has A→MAC mapping but NOT B→MAC.
Host C has learned A's address passively.
This asymmetric learning is normal and by design.
```

### 4. ARP Flux / Weak Host Model

```
Server with multiple NICs, same subnet:
  eth0: 192.168.1.10
  eth1: 192.168.1.11

Problem (weak host model - Windows default):
  ARP request for 192.168.1.10 arrives on eth1
  Kernel responds from eth1 with eth1's MAC
  Network confused: 192.168.1.10 is at eth1_MAC?
  
Solution (strong host model - Linux with arp_ignore=1):
  ARP request for 192.168.1.10 on eth1 → ignored
  ARP request for 192.168.1.10 on eth0 → answered from eth0
  
sysctl -w net.ipv4.conf.all.arp_ignore=1
```

### 5. Proxy ARP Breaking Network Segmentation

```
Router with proxy_arp enabled on eth0:
  Receives ARP for 10.20.30.40 (not on local subnet)
  Checks routing table: "I can reach 10.20.30.40"
  Responds with own MAC: "10.20.30.40 is here (at my MAC)"
  
If routing table is misconfigured or overly broad (e.g., 0.0.0.0/0 default route):
  Router answers ARP for EVERYTHING
  Every host on segment thinks all IPs are local
  Hosts bypass proper routing
  Security zones collapse
```

### 6. ARP Cache Stampede

```
Scenario: Many hosts simultaneously need ARP for same IP
  (e.g., all hosts send first packet after network event)

Each host:
  1. Checks cache → MISS
  2. Sends ARP request (broadcast)
  3. Target receives N ARP requests simultaneously
  4. Target must send N unicast replies
  5. Network flooded with N broadcasts + N unicasts

At scale (e.g., 1000 VMs all starting at once):
  This is "ARP storm" or "ARP flood"
  Can saturate CPU of target, switches

Mitigation:
  - ARP rate limiting at switch
  - ARP suppression in VXLAN/SDN
  - Staggered startup
  - ARP proxy (central cache answers for all hosts)
```

### 7. Stale ARP Entries After Server Replacement

```
Server A: IP=192.168.1.50, MAC=OLD_MAC → fails, replaced
New Server: IP=192.168.1.50, MAC=NEW_MAC → starts

Other hosts still have: 192.168.1.50 → OLD_MAC in cache
OLD_MAC doesn't exist → frames dropped → ~20 minutes of connectivity loss
(until cache entries expire and new ARP happens)

Solution: New server sends Gratuitous ARP immediately on startup
  → All caches update instantly
```

---

## 28. RFC Reference Summary

| RFC | Title | Status | Key Content |
|-----|-------|--------|-------------|
| RFC 826 | An Ethernet Address Resolution Protocol | INTERNET STANDARD | Original ARP definition |
| RFC 903 | A Reverse Address Resolution Protocol (RARP) | HISTORIC | RARP for diskless hosts |
| RFC 1027 | Using ARP to Implement Transparent Subnet Gateways | Informational | Proxy ARP |
| RFC 2131 | Dynamic Host Configuration Protocol (DHCP) | DRAFT STANDARD | Replaced RARP for IP assignment |
| RFC 2390 | Inverse Address Resolution Protocol | DRAFT STANDARD | InARP for Frame Relay/ATM |
| RFC 3768 | Virtual Router Redundancy Protocol (VRRP) | PROPOSED STANDARD | GARP use in HA |
| RFC 4861 | Neighbor Discovery for IPv6 (NDP) | DRAFT STANDARD | IPv6 replacement for ARP |
| RFC 5227 | IPv4 Address Conflict Detection | PROPOSED STANDARD | ARP probe/announcement |
| RFC 5494 | IANA Allocation Guidelines for the ARP | Best Current Practice | ARP IANA registry |
| RFC 7042 | IANA Considerations for EtherType | INFORMATIONAL | EtherType registry |

---

## Summary: The Complete Mental Model

```
ARP operates at the boundary between logical (L3) and physical (L2) addressing.

Core loop:
  "I know the IP, I need the MAC to build the Ethernet frame."
  
  1. Check cache (fast path — nanoseconds)
  2. Cache miss → broadcast ARP request (slow path — milliseconds)
  3. Target responds unicast with its MAC
  4. Store in cache with TTL
  5. Send queued packets

Variants:
  Gratuitous ARP   → "Hey everyone, update your caches for my IP"
  Proxy ARP        → "I'll answer for that IP; I'll forward it"
  ARP Probe        → "Is anyone using this IP? (I don't have it yet)"
  RARP             → "What IP should I use? (diskless boot)"
  InARP            → "What IP is at the other end of this VC?"

Security posture:
  ARP is inherently trust-based (no authentication)
  Defense layers: DAI, static entries, 802.1X, PVLANs, monitoring (arpwatch)

Tuning knobs (Linux):
  arp_ignore   → control which requests to answer
  arp_announce → control which source IP to use in requests
  gc_thresh*   → cache size limits
  *_time*      → cache TTLs and state machine timers

In modern networks:
  ARP persists in all IPv4 LAN segments
  IPv6 uses NDP (ICMPv6 multicast) instead
  SDN/VXLAN/cloud: ARP suppression/proxy reduces broadcast domain flooding
  Kubernetes: ClusterIPs bypass ARP entirely (iptables DNAT)
```

---

*Guide covers RFC 826, RFC 903, RFC 1027, RFC 2390, RFC 5227, RFC 4861 (NDP comparison), Linux kernel 6.x neighbor subsystem, and production network engineering practices.*

Now let me build the comprehensive ARP guide:**3,169 lines / ~108KB** — your complete ARP reference.

Here's what the guide covers in full depth:

**Protocol Fundamentals** — why ARP exists at the L2/L3 boundary, the OSI positioning (the "layer 2.5" dual nature), Ethernet II framing with EtherType `0x0806`, and the complete RFC 826 packet structure with a real hex dump of a live ARP request.

**Full Operation Lifecycle** — step-by-step with ASCII timelines: cache miss → broadcast → passive learning → unicast reply → cache update → packet delivery. Every frame's fields annotated.

**ARP Cache State Machine** — the Linux NUD (Neighbor Unreachability Detection) model: NONE → INCOMPLETE → REACHABLE → STALE → DELAY → PROBE → FAILED, with all timing parameters and how the kernel transitions between states.

**All ARP Variants** — Gratuitous ARP (GARP) with all 4 use cases (conflict detection, NIC swap, VRRP failover, VM migration), Proxy ARP, ARP Probe/Announcement (RFC 5227 IPv4LL), RARP (historical), InARP (Frame Relay/ATM).

**Security** — full attack mechanics for ARP poisoning MITM with frame-level detail, DoS via bogus MACs, and all defense layers: DAI, static entries, PVLANs, port security, arpwatch.

**Linux Internals** — kernel data structures (`struct neighbour`, `neigh_table arp_tbl`), the `arp_rcv()` → `arp_process()` path, and every meaningful sysctl (`arp_ignore`, `arp_announce`, `gc_thresh*`) with production rationale.

**C & Rust Implementations** — raw AF_PACKET sockets, packed structs matching wire format exactly, full cache with NUD states, request/reply/GARP/probe send functions, passive learning on receive, resolve-with-timeout. Both implementations are production-grade with proper error handling.

**Modern Contexts** — VXLAN ARP suppression, Docker bridge ARP flow, Kubernetes (Flannel host-gw, VXLAN mode, why ClusterIPs are un-ARPable), VRRP failover timing.

**27 edge cases** — ARP storm, stale entries after server replacement, ARP flux (weak vs strong host model), proxy ARP breaking segmentation, duplicate IP detection races.