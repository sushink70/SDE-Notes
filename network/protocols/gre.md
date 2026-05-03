# GRE Protocol — Complete, In-Depth Guide
> *Generic Routing Encapsulation: From Fundamentals to Expert-Level Understanding*

---

## Table of Contents

1. [What is GRE? — The Mental Model](#1-what-is-gre--the-mental-model)
2. [Core Vocabulary — Terms You Must Know](#2-core-vocabulary--terms-you-must-know)
3. [The OSI Model Context](#3-the-osi-model-context)
4. [GRE Packet Structure — Every Bit Explained](#4-gre-packet-structure--every-bit-explained)
5. [How GRE Encapsulation Works — Step by Step](#5-how-gre-encapsulation-works--step-by-step)
6. [GRE Tunnel Establishment](#6-gre-tunnel-establishment)
7. [GRE Routing — How Packets Are Forwarded](#7-gre-routing--how-packets-are-forwarded)
8. [GRE Keepalives](#8-gre-keepalives)
9. [GRE and MTU — The Hidden Complexity](#9-gre-and-mtu--the-hidden-complexity)
10. [mGRE — Multipoint GRE](#10-mgre--multipoint-gre)
11. [DMVPN — Dynamic Multipoint VPN (Built on mGRE)](#11-dmvpn--dynamic-multipoint-vpn-built-on-mgre)
12. [GRE over IPsec](#12-gre-over-ipsec)
13. [GRE over IPv6 (GRE6)](#13-gre-over-ipv6-gre6)
14. [IPv6 over GRE (6in4)](#14-ipv6-over-gre-6in4)
15. [GRE Security — Threats and Mitigations](#15-gre-security--threats-and-mitigations)
16. [GRE vs Other Tunneling Protocols](#16-gre-vs-other-tunneling-protocols)
17. [GRE in Linux — Implementation Deep Dive](#17-gre-in-linux--implementation-deep-dive)
18. [Troubleshooting GRE — Expert Methodology](#18-troubleshooting-gre--expert-methodology)
19. [Real-World Use Cases](#19-real-world-use-cases)
20. [Mental Models and Summary](#20-mental-models-and-summary)

---

## 1. What is GRE? — The Mental Model

### The Envelope Analogy

Imagine you want to send a **letter written in French** through a postal system that **only handles English documents**. What do you do? You put the French letter inside an English envelope. The postal system sees only the English envelope, routes it to the destination, and the receiver opens it to find the French letter inside.

**GRE does exactly this — but for network packets.**

GRE (Generic Routing Encapsulation) is a **tunneling protocol** developed by **Cisco Systems** (originally by Glenn Farinacci et al.) and standardized in:

- **RFC 1701** (1994) — Original GRE
- **RFC 1702** (1994) — GRE over IPv4
- **RFC 2784** (2000) — Revised GRE (simplified, deprecated checksum/routing fields)
- **RFC 2890** (2000) — GRE with Key and Sequence Number extensions

GRE allows you to **encapsulate any network layer protocol** (the "passenger") inside another network layer protocol (the "transport/delivery"). The tunnel acts as a **virtual point-to-point link** between two endpoints.

### What Problem Does GRE Solve?

```
PROBLEM WITHOUT GRE:
=====================
Router A ----[Internet: only speaks IPv4]---- Router B
     |                                             |
  Site A                                        Site B
 (has IPv6,                                   (has IPv6,
  IPX, CLNS)                                   IPX, CLNS)

The Internet in between CANNOT route IPv6, IPX, or CLNS packets.
They would be dropped.

SOLUTION WITH GRE:
==================
Router A =====[GRE Tunnel: wrapped in IPv4]===== Router B
     |                                                 |
  Site A                                            Site B
 (has IPv6,                                        (has IPv6,
  IPX, CLNS)                                        IPX, CLNS)

Now IPv6/IPX/CLNS packets are WRAPPED inside IPv4 packets.
The Internet sees only IPv4 and routes them correctly.
At the other end, Router B UNWRAPS them back to original.
```

### Key Characteristics of GRE

| Property             | Value/Description                              |
|----------------------|------------------------------------------------|
| **Protocol Number**  | IP Protocol 47                                 |
| **Header Size**      | Minimum 4 bytes, maximum 20 bytes              |
| **Encapsulation**    | Any Layer-3 protocol inside any Layer-3 proto  |
| **Authentication**   | None (by itself — needs IPsec for security)    |
| **Encryption**       | None (by itself)                               |
| **Stateful?**        | No — it is stateless by default                |
| **Multicast Support**| YES — this is a KEY advantage over IPsec       |
| **Overhead**         | Minimum 24 bytes (4 GRE + 20 IPv4 outer)       |
| **RFC**              | 2784, 2890                                     |

---

## 2. Core Vocabulary — Terms You Must Know

Before going deeper, internalize these terms. Each one is a building block.

### Tunnel
A **virtual point-to-point link** created by encapsulating packets of one protocol inside packets of another. The "tunnel" is not a physical cable — it is a logical abstraction maintained by the routers at each end.

### Encapsulation
The process of **wrapping** a packet (the passenger) inside another packet (the carrier). Like putting a letter inside an envelope.

### Decapsulation
The reverse: **unwrapping** the outer packet to retrieve the inner packet. Like opening the envelope to read the letter.

### Passenger Protocol
The protocol being carried **inside** the tunnel. Examples: IPv6, IPv4, IPX, CLNS, MPLS, Ethernet.

### Carrier / Transport / Delivery Protocol
The protocol that **carries** the tunnel across the network. Typically IPv4 or IPv6.

### Tunnel Endpoint
The router (or host) that **performs encapsulation** (tunnel source) or **decapsulation** (tunnel destination).

### Tunnel Source
The IP address on the **local router** that is the "from" address in the outer IP header.

### Tunnel Destination
The IP address on the **remote router** that is the "to" address in the outer IP header.

### Tunnel Interface
A **virtual (logical) interface** on the router that represents the GRE tunnel. It has its own IP address in a separate subnet, used for routing decisions inside the tunnel.

### Outer Header
The **encapsulating header** — added by GRE. This is what the intermediate network sees.

### Inner Header
The **original passenger packet's header** — hidden inside the GRE tunnel.

### Point-to-Point Tunnel
A tunnel with **one source and one fixed destination**. Standard GRE is point-to-point.

### Multipoint Tunnel (mGRE)
A tunnel with **one source but many possible destinations**. Used in DMVPN.

### Key Field
An optional 32-bit field in the GRE header used to **identify** a specific tunnel when multiple GRE tunnels share the same source/destination pair.

### Sequence Number
An optional 32-bit field for **ordering packets**, enabling detection of out-of-order delivery.

### NHRP (Next Hop Resolution Protocol)
Used with mGRE/DMVPN to **dynamically resolve** the physical (NBMA) address of a tunnel endpoint from its tunnel IP address.

### NBMA (Non-Broadcast Multi-Access)
A network type where many nodes share a medium but **cannot broadcast** — like Frame Relay or the Internet itself. mGRE tunnels exist over NBMA networks.

---

## 3. The OSI Model Context

```
OSI Layer    | Role in GRE
-------------+----------------------------------------------------------
Layer 7      | Application  (HTTP, FTP, SSH...)
Layer 6      | Presentation
Layer 5      | Session
Layer 4      | Transport    (TCP/UDP — these are INSIDE the tunnel)
Layer 3      | Network      <-- GRE operates here
             |              Passenger: IPv6/IPv4/IPX (inner Layer 3)
             |              GRE Header: sits between inner and outer L3
             |              Carrier: IPv4/IPv6 (outer Layer 3)
Layer 2      | Data Link    (Ethernet, PPP — unchanged, carries outer IP)
Layer 1      | Physical     (Fiber, copper, radio)
```

GRE is a **Layer 3 tunneling protocol** — it encapsulates network-layer protocols. This is different from Layer 2 tunnels (like L2TP, VXLAN) that carry Ethernet frames.

---

## 4. GRE Packet Structure — Every Bit Explained

### 4.1 Complete Packet Layout

When a GRE tunnel carries an IPv4 passenger over an IPv4 carrier:

```
+---------------------------+---------------------------+---------------------------+
|   OUTER IPv4 HEADER       |   GRE HEADER              |   INNER IPv4 HEADER       |
|   (Delivery Header)       |   (4 to 20 bytes)         |   (Passenger Header)      |
|   20 bytes                |                           |   20 bytes                |
+---------------------------+---------------------------+---------------------------+
                                                         |   INNER PAYLOAD           |
                                                         |   (TCP/UDP/ICMP...)       |
                                                         +---------------------------+
```

Full wire layout:

```
Byte:  0         1         2         3         4         5         6         7
       01234567  89012345  67890123  45678901  01234567  89012345  67890123  45678901
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |Version |  IHL   |   DSCP   | ECN   |         Total Length            |
      |  4     |  5     |  (TOS)          |                                  |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |         Identification          |Flags|    Fragment Offset            |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |   TTL  | Proto=47|        Header Checksum              |              |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |              Source IP (Tunnel Source = Outer Src)                    |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |              Destination IP (Tunnel Dest = Outer Dst)                 |
      +=======================================================================+
      |||||||||||||||||||  GRE HEADER BEGINS HERE  |||||||||||||||||||||||||||
      +=======================================================================+
      |C|R|K|S|s|Recur|  Flags  |           Protocol Type                   |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |                  Checksum (if C=1)         |       Reserved          |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |                    Key (if K=1, 32 bits)                              |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |                 Sequence Number (if S=1, 32 bits)                     |
      +=======================================================================+
      |||||||||||||||||||  INNER PACKET BEGINS HERE  |||||||||||||||||||||||||
      +=======================================================================+
      |   Inner IP Header (Version, TTL, Src, Dst of REAL traffic)           |
      +--------+--------+--------+--------+--------+--------+--------+--------+
      |   Inner Payload (TCP/UDP/ICMP/etc.)                                   |
      +--------+--------+--------+--------+--------+--------+--------+--------+
```

### 4.2 Outer IPv4 Header Fields (Delivery Header)

The outer IPv4 header is a **standard IPv4 header** with one critical field:

| Field                | Value / Meaning                                                  |
|----------------------|------------------------------------------------------------------|
| **Version**          | 4 (IPv4)                                                         |
| **IHL**              | 5 (20 bytes, no options typically)                               |
| **Protocol**         | **47** — this is GRE's IP protocol number (IANA assigned)        |
| **Source IP**        | IP address of the local router's physical/loopback interface     |
| **Destination IP**   | IP address of the remote router's physical/loopback interface    |
| **TTL**              | Set by the encapsulating router (typically 255)                  |
| **DF Bit**           | Critical for MTU — often set to 0 in GRE (fragmentation allowed)|

**Protocol 47** is how intermediate routers know this is a GRE packet. They do not look inside — they just route based on the outer destination IP.

### 4.3 GRE Header — Detailed Bit-by-Bit

```
GRE Header (RFC 2784 — minimum 4 bytes, flags extend it):

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |C| |K|S| Reserved0       | Ver |         Protocol Type         |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |      Checksum (optional)      |       Reserved1               |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |                         Key (optional)                        |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |                  Sequence Number (optional)                   |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### Bit 0: C — Checksum Present

- **0** = No checksum field in the GRE header (default in RFC 2784)
- **1** = A 16-bit checksum is included immediately after the flags/protocol word
- If C=1, the Checksum field (16 bits) and Reserved1 (16 bits) are present
- The checksum covers the **GRE header only**, not the inner packet
- **Modern usage**: Almost always 0. Checksumming is expensive and rarely needed since lower layers (Ethernet CRC, inner TCP checksum) already provide integrity

#### Bit 1: Reserved (was "Routing Present" in RFC 1701)

- RFC 2784 **deprecated** the routing functionality of RFC 1701
- Must be **0** (zero) in RFC 2784-compliant implementations
- If set to 1 in old RFC 1701 packets, it indicated a Source Route Entry (SRE) was present

#### Bit 2: K — Key Present

- **0** = No Key field (default)
- **1** = A 32-bit Key field is present
- The Key is used to **identify** a specific GRE tunnel or flow
- When multiple GRE tunnels exist between the same two endpoints, the Key differentiates them
- Both ends MUST use the same key; mismatched keys → packets dropped
- **Use case**: Virtual networks, tenant isolation (like AWS VPC uses GRE with keys)

#### Bit 3: S — Sequence Number Present

- **0** = No Sequence Number field (default)
- **1** = A 32-bit Sequence Number field is present
- Sequence numbers allow detection of **out-of-order** or **dropped** packets
- The sender increments the sequence number for each packet
- The receiver can reorder packets or detect loss
- **Rarely used** because it adds overhead and GRE is typically used over reliable paths

#### Bits 4: Reserved (was "Strict Source Route" in RFC 1701)

- Must be **0** in RFC 2784

#### Bits 5-7: Recur (Recursion Control — RFC 1701)

- Indicated the number of additional encapsulations permitted
- **Deprecated** in RFC 2784, must be **0**

#### Bits 8-12: Flags

- All must be **0** in RFC 2784
- Were used in RFC 1701 for various purposes

#### Bits 13-15: Ver (Version)

- Must be **0** (indicates GRE version 0)
- Version 1 was used for PPTP (Point-to-Point Tunneling Protocol) — a completely different beast

#### Bits 16-31: Protocol Type

- A **16-bit EtherType value** identifying the passenger protocol
- This is the same EtherType used in Ethernet frames!

| Protocol Type Value | Passenger Protocol |
|---------------------|-------------------|
| 0x0800              | IPv4              |
| 0x86DD              | IPv6              |
| 0x0806              | ARP               |
| 0x8100              | 802.1Q (VLAN)     |
| 0x8847              | MPLS Unicast      |
| 0x8848              | MPLS Multicast    |
| 0x0BAD              | Novell IPX        |
| 0x6558              | Transparent Ethernet Bridging (L2 over GRE) |
| 0x9000              | Loopback          |
| 0x0060              | XNS               |
| 0x0200              | PUP               |
| 0x0805              | X.25 Level 3      |
| 0x8035              | RARP              |
| 0x809B              | AppleTalk         |

#### Optional Field: Checksum (16 bits, present if C=1)

- A 16-bit one's complement checksum over the entire GRE header
- Followed by 16 bits of Reserved1 (must be zero)
- Adding C=1 increases the GRE header size by 4 bytes

#### Optional Field: Key (32 bits, present if K=1)

- An opaque 32-bit value
- Has no meaning defined by GRE itself — it's up to the implementation
- Can be split into two 16-bit halves (some implementations use this for virtual circuit IDs)
- Adding K=1 increases the GRE header size by 4 bytes

#### Optional Field: Sequence Number (32 bits, present if S=1)

- Unsigned 32-bit integer, starts at 0, increments by 1 per packet
- The receiver tracks the highest sequence number seen
- Adding S=1 increases the GRE header size by 4 bytes

### 4.4 GRE Header Size Summary

| Flags Set          | Header Size |
|--------------------|-------------|
| None (bare minimum)| 4 bytes     |
| C=1 only           | 8 bytes     |
| K=1 only           | 8 bytes     |
| S=1 only           | 8 bytes     |
| C=1, K=1           | 12 bytes    |
| C=1, K=1, S=1      | 16 bytes    |
| All three          | 16 bytes    |

> **Maximum GRE overhead** = 4 (GRE) + 16 (optional fields) = **20 bytes** of GRE header.
> Plus 20 bytes outer IPv4 = **40 bytes total overhead** in the worst case.

---

## 5. How GRE Encapsulation Works — Step by Step

### 5.1 The Journey of a Packet Through a GRE Tunnel

Let's trace a real packet from a host in Site A (10.1.1.10) to a host in Site B (10.2.2.20), through a GRE tunnel between Router A (physical IP: 203.0.113.1) and Router B (physical IP: 198.51.100.1). The tunnel interface IPs are: Router A tunnel = 172.16.0.1, Router B tunnel = 172.16.0.2.

```
NETWORK TOPOLOGY:
=================

Host A             Router A                   Internet              Router B             Host B
10.1.1.10 -----> 10.1.1.1 [Physical: 203.0.113.1] ============ [Physical: 198.51.100.1] 10.2.2.1 ----> 10.2.2.20
                           [Tunnel0: 172.16.0.1]                [Tunnel0: 172.16.0.2]

STEP 1: Host A sends a normal packet
=====================================
Host A creates:
+------------------------------------------+
| Src: 10.1.1.10  | Dst: 10.2.2.20        |  <- Inner IP Header
| Proto: TCP       | TTL: 64               |
+------------------------------------------+
| TCP Header: Src Port 12345, Dst Port 80   |
+------------------------------------------+
| HTTP Data: "GET / HTTP/1.1"               |
+------------------------------------------+
Host A sends this to its gateway: Router A (10.1.1.1)

STEP 2: Router A receives packet, checks routing table
=======================================================
Router A looks at Destination: 10.2.2.20
Routing table says: "10.2.2.0/24 is reachable via Tunnel0 interface"
Router A decides: "This packet must go through the GRE tunnel."

STEP 3: Router A ENCAPSULATES the packet
==========================================
Router A builds a GRE header and a new outer IPv4 header:

+------------------------------------------+
| Outer IPv4 Header:                        |
| Src: 203.0.113.1 (my physical IP)        |
| Dst: 198.51.100.1 (remote router phys IP)|
| Protocol: 47 (GRE)                        |
| TTL: 255                                  |
+------------------------------------------+
| GRE Header:                               |
| Flags: 0x0000 (no checksum/key/seq)       |
| Protocol Type: 0x0800 (IPv4 passenger)    |
+------------------------------------------+
| ORIGINAL PACKET (now the inner payload):  |
| Inner IPv4: Src 10.1.1.10, Dst 10.2.2.20 |
| TCP + HTTP data                           |
+------------------------------------------+

STEP 4: Outer packet traverses the Internet
============================================
The Internet sees ONLY the outer header:
  Src: 203.0.113.1
  Dst: 198.51.100.1
  Protocol: 47

Every router along the path routes based on 198.51.100.1.
They have NO IDEA what's inside. They never look past the outer IP header.
The inner packet (10.1.1.10 -> 10.2.2.20) is invisible to them.

STEP 5: Router B receives the packet
======================================
Router B sees:
  Outer Dst: 198.51.100.1 (that's ME!)
  Protocol: 47 (that's GRE — I know how to handle this)

Router B DECAPSULATES:
  1. Strip outer IPv4 header
  2. Read GRE header: Protocol Type = 0x0800 (inner is IPv4)
  3. Strip GRE header
  4. Now Router B has the original packet: Src 10.1.1.10, Dst 10.2.2.20

STEP 6: Router B forwards the inner packet normally
=====================================================
Router B looks up 10.2.2.20 in its routing table.
10.2.2.0/24 is on its local interface.
Router B forwards to Host B: 10.2.2.20

STEP 7: Host B receives the packet
====================================
Host B receives a normal TCP packet: Src 10.1.1.10, Dst 10.2.2.20
Host B has NO IDEA this packet went through a GRE tunnel.
This is TRANSPARENT tunneling.
```

### 5.2 ASCII Flow Diagram — Encapsulation/Decapsulation

```
ENCAPSULATION (at Router A):
==============================

  [Original Packet]
  +-------------------+
  | Inner IP Header   |
  | (real src/dst)    |
  +-------------------+  -----+
  | TCP/UDP/ICMP...   |       |
  +-------------------+       |
                              |  GRE Encapsulation
                              v
  +-------------------+  <-- Added by GRE tunnel
  | Outer IP Header   |       ^
  | Src: tunnel_src   |       |
  | Dst: tunnel_dst   |       |
  | Proto: 47 (GRE)   |  -----+
  +-------------------+
  | GRE Header        |  <-- Added (4-20 bytes)
  | Protocol: 0x0800  |
  +-------------------+
  | Inner IP Header   |  <-- Original packet (unchanged)
  | (real src/dst)    |
  +-------------------+
  | TCP/UDP/ICMP...   |
  +-------------------+

DECAPSULATION (at Router B):
==============================

  [GRE Encapsulated Packet]
  +-------------------+
  | Outer IP Header   |  --> Read Dst IP = me, Proto = 47 (GRE)
  | Proto: 47 (GRE)   |  --> STRIP this header
  +-------------------+
  | GRE Header        |  --> Read Protocol Type = 0x0800 (IPv4)
  | Protocol: 0x0800  |  --> STRIP this header
  +-------------------+
  | Inner IP Header   |  --> This is the real packet
  | (real src/dst)    |  --> Route it normally
  +-------------------+
  | TCP/UDP/ICMP...   |
  +-------------------+
          |
          v
  [Recovered Original Packet]
  +-------------------+
  | Inner IP Header   |
  | (real src/dst)    |
  +-------------------+
  | TCP/UDP/ICMP...   |
  +-------------------+
```

---

## 6. GRE Tunnel Establishment

### 6.1 No Handshake — GRE is Stateless

Unlike TCP (which has a 3-way handshake) or IKE (which negotiates security associations), **GRE has NO establishment handshake**. There is no "tunnel setup" phase. A GRE tunnel is purely a **configuration artifact** — both routers must be manually configured (or dynamically provisioned) with matching parameters.

When Router A sends a GRE-encapsulated packet toward Router B's tunnel destination IP, the tunnel is "up" if Router B:
1. Receives the packet
2. Has GRE configured with the matching source/destination
3. Decapsulates and processes it

### 6.2 Tunnel "Up/Down" State

Because GRE is stateless, how does a router know if the tunnel is "up"?

- **Line Protocol**: The tunnel interface is considered "up" as long as the **tunnel destination is reachable** in the routing table (the underlying path exists)
- **Keepalives** (optional): GRE supports keepalive messages that probe whether the remote end is responding. Without keepalives, a GRE tunnel interface can show "up/up" even if the remote router is down!

```
TUNNEL STATE DETERMINATION (without keepalives):
=================================================

Router A checks:
  "Can I reach 198.51.100.1 (tunnel destination)?"
  If YES -> Tunnel0 is UP/UP (line protocol up)
  If NO  -> Tunnel0 is UP/DOWN (line protocol down)

PROBLEM: Router B could be running but have its GRE
config removed. Router A would still show UP/UP
because 198.51.100.1 is still reachable via IP.
GRE itself has no way to know the remote end is broken.

SOLUTION: GRE Keepalives (discussed in section 8)
```

### 6.3 Cisco IOS Configuration — Understanding the Syntax

```
! Router A Configuration
interface Tunnel0
  ip address 172.16.0.1 255.255.255.252
  tunnel source 203.0.113.1          ! or: tunnel source GigabitEthernet0/0
  tunnel destination 198.51.100.1
  tunnel mode gre ip                 ! default — GRE over IPv4

! Router A routing: send 10.2.2.0/24 through the tunnel
ip route 10.2.2.0 255.255.255.0 Tunnel0
! or via next-hop: ip route 10.2.2.0 255.255.255.0 172.16.0.2

! Router B Configuration (mirror image)
interface Tunnel0
  ip address 172.16.0.2 255.255.255.252
  tunnel source 198.51.100.1
  tunnel destination 203.0.113.1
  tunnel mode gre ip

ip route 10.1.1.0 255.255.255.0 Tunnel0
```

### 6.4 Linux ip Command Configuration

```bash
# Create GRE tunnel interface
ip tunnel add gre1 mode gre \
  local 203.0.113.1 \       # tunnel source
  remote 198.51.100.1 \     # tunnel destination
  ttl 255

# Bring tunnel interface up
ip link set gre1 up

# Assign IP address to tunnel interface
ip addr add 172.16.0.1/30 dev gre1

# Add route through tunnel
ip route add 10.2.2.0/24 dev gre1

# Verify tunnel
ip tunnel show gre1
ip addr show gre1
```

---

## 7. GRE Routing — How Packets Are Forwarded

### 7.1 Two Routing Tables Are Active Simultaneously

This is a concept that confuses many people. When GRE is running, a router consults **two separate routing processes**:

1. **Passenger routing** (inner): Decides whether a packet should enter the tunnel
2. **Delivery routing** (outer): Decides how to route the encapsulated GRE packet to the tunnel endpoint

```
DUAL ROUTING TABLE LOOKUP:
===========================

Packet arrives: Dst = 10.2.2.20

Step 1: PASSENGER ROUTING TABLE LOOKUP
  Router checks: Where does 10.2.2.20 go?
  Answer: "10.2.2.0/24 → via Tunnel0"
  Decision: Encapsulate this packet in GRE, send out Tunnel0

Step 2: GRE ENCAPSULATION
  Add outer header: Dst = 198.51.100.1 (tunnel destination)
  Add GRE header: Protocol = 0x0800

Step 3: DELIVERY ROUTING TABLE LOOKUP
  Router checks: Where does 198.51.100.1 go?
  Answer: "198.51.100.0/24 → via GigabitEthernet0/0, next hop: 203.0.113.254"
  Decision: Send GRE packet out Gig0/0 toward 198.51.100.1
```

### 7.2 Recursive Routing — The Deadly Pitfall

**Recursive routing** (also called a **routing loop** in the GRE context) occurs when the delivery route to the tunnel destination goes **through the tunnel itself**. This creates an infinite loop:

```
RECURSIVE ROUTING LOOP:
========================

Packet arrives: Dst = 10.2.2.20

Step 1: Passenger lookup → "10.2.2.0/24 via Tunnel0"
Step 2: GRE encapsulates → Outer Dst = 198.51.100.1
Step 3: Delivery lookup → "198.51.100.1 via Tunnel0"  <-- PROBLEM!
Step 4: GRE encapsulates AGAIN → outer Dst = 198.51.100.1
Step 5: Delivery lookup → "via Tunnel0" <-- INFINITE LOOP!

The router wraps the packet in GRE again and again until
the TTL expires or the stack overflows.

SYMPTOMS:
- CPU spikes to 100%
- Interface shows "tunnel encapsulation limit exceeded"
- Traceroute shows repeated hops to the same IP

HOW TO PREVENT:
Option 1: Use a specific host route for the tunnel destination
  ip route 198.51.100.1 255.255.255.255 192.0.2.1  (via physical next hop)

Option 2: Route tunnel destination via physical interface, NOT default route
  Ensure the static route for tunnel destination exits via physical interface

Option 3: Use routing protocols with proper administrative distances
  Ensure IGP/static routes for physical paths have lower metric than tunnel routes
```

### 7.3 Split Tunneling

**Split tunneling** means some traffic goes through the GRE tunnel and some goes directly out to the internet:

```
WITH SPLIT TUNNELING:
======================
Traffic to 10.2.2.0/24 → GRE Tunnel (encrypted via IPsec)
Traffic to 0.0.0.0/0   → Direct Internet (not through tunnel)

WITHOUT SPLIT TUNNELING (full tunnel):
========================================
ALL traffic (including internet) → GRE Tunnel
(Router B then forwards it to the internet from its side)
```

---

## 8. GRE Keepalives

### 8.1 The Problem — False "Up" State

Without keepalives, a GRE tunnel shows as UP if the tunnel destination's IP is reachable — even if:
- The remote router crashed
- The remote router's GRE config was deleted
- The remote router is behind a NAT that stopped working

This causes **black holes**: packets go into the tunnel and disappear.

### 8.2 How GRE Keepalives Work

GRE keepalives are a **Cisco proprietary extension** — not part of the RFC. They work through a clever mechanism:

```
GRE KEEPALIVE MECHANISM:
=========================

Router A sends a KEEPALIVE packet:
  Outer Header: Src=203.0.113.1, Dst=198.51.100.1, Proto=47
  GRE Header: Protocol=0x0800 (IPv4)
  Inner Packet: Dst=203.0.113.1 (Router A's OWN address!)
                 Src=172.16.0.1 (tunnel IP)
                 Protocol: GRE (47)
                 [This inner packet is a GRE-encapsulated IP packet pointing BACK to Router A]

What happens at Router B:
  Router B receives the outer GRE packet.
  Router B decapsulates the GRE header.
  Router B now has the inner packet: Dst=203.0.113.1
  Router B sees this as a normal IPv4 packet destined for 203.0.113.1.
  Router B routes it! It goes back to Router A.
  The inner packet, when it arrives at Router A, looks like a GRE keepalive response.

The GENIUS of this design:
  Router B doesn't need to KNOW about keepalives!
  It just decapsulates and re-routes. The keepalive loop works automatically.
  Router A sends keepalives → B decapsulates → B routes inner packet back → A receives response.

If Router B is down: Router A never receives a response.
After N missed keepalives → Router A marks Tunnel0 as DOWN.
```

### 8.3 Keepalive Configuration

```
! Cisco IOS
interface Tunnel0
  keepalive 10 3    ! Send keepalive every 10 seconds
                    ! After 3 missed keepalives (30 sec), mark tunnel DOWN

! Default: no keepalive (tunnel stays "up" regardless of remote status)
```

### 8.4 Keepalive Packet Structure

```
KEEPALIVE PACKET (what Router A sends):

Outer GRE Packet:
  [Outer IPv4: Src=203.0.113.1, Dst=198.51.100.1, Proto=47]
  [GRE Header: Protocol=0x0800]
  [Inner IPv4: Src=172.16.0.1, Dst=203.0.113.1, Proto=47]
  [Inner GRE: Protocol=0x0800]
  [Payload: zeros or small data]

When Router B receives this and decapsulates the OUTER GRE:
  It gets: [IPv4: Src=172.16.0.1, Dst=203.0.113.1, Proto=47][GRE][zeros]
  Router B routes this to 203.0.113.1 (Router A)
  Router A receives it → keepalive acknowledged → tunnel is UP
```

---

## 9. GRE and MTU — The Hidden Complexity

### 9.1 The MTU Problem

**MTU (Maximum Transmission Unit)** is the largest packet size a network link can carry without fragmentation. Standard Ethernet MTU is **1500 bytes**.

GRE adds overhead:
- 20 bytes outer IPv4 header
- 4 bytes minimum GRE header
- **= 24 bytes overhead (minimum)**

So if the path MTU is 1500 bytes, the maximum **inner** packet size is:
```
1500 - 24 = 1476 bytes
```

If the inner packet is larger than 1476 bytes, something must happen.

### 9.2 What Happens With Oversized Packets

```
SCENARIO:
=========
Host A sends a 1500-byte IP packet through the GRE tunnel.

At Router A:
  Inner packet: 1500 bytes
  After GRE encapsulation: 1500 + 24 = 1524 bytes
  Outgoing interface MTU: 1500 bytes
  1524 > 1500 → PROBLEM!

Option 1: Fragment the OUTER packet
  Router A breaks the 1524-byte outer packet into:
  Fragment 1: 1500 bytes (first 1480 bytes of GRE+inner data)
  Fragment 2: 44 bytes (remaining 24 bytes + fragment overhead)
  
  DRAWBACK: Fragmentation is expensive (CPU overhead)
  Fragments must be reassembled at Router B (memory overhead)
  If one fragment is lost, entire packet must be retransmitted
  Some firewalls BLOCK fragments (security policy)

Option 2: The inner packet has DF (Don't Fragment) bit set
  Router A tries to encapsulate 1500-byte packet.
  Result would be 1524 bytes > 1500 MTU.
  DF bit says "do not fragment."
  Router A DROPS the packet and sends an ICMP Type 3, Code 4 message
  back to Host A: "Fragmentation needed and DF set"
  The ICMP message includes the MTU of the bottleneck link (1476 bytes).
  Host A reduces its packet size (PMTUD — Path MTU Discovery).
  Host A retransmits with 1476-byte packets.
  These fit inside the GRE tunnel correctly.

Option 3: Reduce the tunnel interface MTU proactively
  Configure the GRE tunnel interface with MTU 1476.
  The router will force fragmentation of inner packets > 1476 bytes
  BEFORE encapsulation, avoiding the outer fragmentation problem.
  
  Linux:  ip link set gre1 mtu 1476
  Cisco:  interface Tunnel0
            ip mtu 1476
```

### 9.3 TCP MSS Clamping

For TCP traffic, there is an elegant fix: **TCP MSS (Maximum Segment Size) Clamping**.

TCP negotiates MSS during the 3-way handshake. If we intercept the SYN packets and reduce the MSS to fit within the tunnel MTU, TCP will never send oversized segments.

```
NORMAL TCP MSS NEGOTIATION:
============================
Host A SYN: "I can receive segments up to 1460 bytes"
Host B SYN-ACK: "I can receive segments up to 1460 bytes"
Result: TCP uses 1460-byte segments

These become 1500-byte IP packets (1460 + 20 TCP + 20 IP).
Inside GRE: 1500 + 24 = 1524 bytes → PROBLEM!

WITH MSS CLAMPING ON ROUTER A:
================================
Router A intercepts the SYN packet.
Router A modifies the MSS field: changes 1460 → 1436
  (Why 1436? 1500 MTU - 20 outer IP - 4 GRE - 20 inner IP - 20 TCP = 1436)
Host B sees MSS = 1436, agrees to use 1436-byte segments.
TCP segments become 1476-byte IP packets (1436 + 20 TCP + 20 IP).
Inside GRE: 1476 + 24 = 1500 bytes → PERFECT FIT!

Configuration:
  Linux:   iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
            -j TCPMSS --clamp-mss-to-pmtu
  Cisco:   interface Tunnel0
             ip tcp adjust-mss 1436
```

### 9.4 MTU Calculation Summary

```
For GRE over IPv4 (no IPsec):
  Tunnel MTU = Physical MTU - 20 (outer IPv4) - 4 (GRE min)
             = 1500 - 20 - 4
             = 1476 bytes

For GRE over IPv6:
  Tunnel MTU = Physical MTU - 40 (outer IPv6) - 4 (GRE min)
             = 1500 - 40 - 4
             = 1456 bytes

For GRE over IPv4 with IPsec (ESP in tunnel mode, AES-256-CBC, SHA-1 HMAC):
  Tunnel MTU = 1500 - 20 (outer IP) - 4 (GRE) - 20 (ESP hdr) - 16 (IV)
               - 16 (pad+length+next-hdr) - 20 (HMAC-SHA1)
             ≈ 1404 bytes (varies by cipher/hash algorithm)

For GRE over IPv4 with IPsec (ESP in transport mode, AES-GCM-256):
  Tunnel MTU = 1500 - 20 (outer IP) - 4 (GRE) - 8 (ESP hdr) - 8 (IV/nonce)
               - 16 (GCM auth tag)
             ≈ 1444 bytes
```

---

## 10. mGRE — Multipoint GRE

### 10.1 The Limitation of Point-to-Point GRE

In a standard GRE tunnel, the `tunnel destination` is a **fixed IP address** (one remote endpoint). If you have 10 remote sites, you need **10 separate GRE tunnel interfaces**. This does not scale.

```
STANDARD GRE — Hub-and-Spoke (10 spokes):
==========================================
Hub Router:
  Tunnel0: destination = Spoke1_IP
  Tunnel1: destination = Spoke2_IP
  Tunnel2: destination = Spoke3_IP
  ...
  Tunnel9: destination = Spoke10_IP

10 tunnel interfaces, 10 routing entries, exponential growth!
N spokes = N tunnel interfaces on hub. Doesn't scale.

And spoke-to-spoke traffic must go:
  Spoke1 → Hub → Spoke2 (hairpinning through hub — inefficient)
```

### 10.2 mGRE — One Interface, Many Destinations

mGRE replaces the fixed `tunnel destination` with **no fixed destination**. Instead, the destination is determined **dynamically** using NHRP (Next Hop Resolution Protocol).

```
mGRE TUNNEL CONFIGURATION:
===========================
interface Tunnel0
  ip address 172.16.0.1 255.255.0.0
  tunnel source 203.0.113.1
  tunnel mode gre multipoint          ! <-- NO tunnel destination!
  ip nhrp network-id 1
  ip nhrp map multicast dynamic       ! allow dynamic multicast mappings
```

### 10.3 How mGRE Works With NHRP

```
mGRE + NHRP RESOLUTION PROCESS:
=================================

Actors:
  Hub:    Tunnel IP = 172.16.0.1, Physical IP = 203.0.113.1
  Spoke1: Tunnel IP = 172.16.1.1, Physical IP = 198.51.100.1
  Spoke2: Tunnel IP = 172.16.2.1, Physical IP = 192.0.2.1

STEP 1: Registration (Spokes register with Hub)
  Spoke1 sends NHRP Registration Request to Hub:
    "My tunnel IP is 172.16.1.1, my physical IP is 198.51.100.1"
  Hub records this in its NHRP cache.
  Spoke2 does the same: "172.16.2.1 → 192.0.2.1"
  Hub records this too.

STEP 2: Resolution (Spoke1 wants to talk to Spoke2 directly)
  Spoke1 has traffic for 10.2.2.20 (behind Spoke2)
  Spoke1 doesn't know Spoke2's physical IP
  Spoke1 sends NHRP Resolution Request to Hub:
    "What is the physical IP of 172.16.2.1?"
  Hub looks up its NHRP cache: "172.16.2.1 → 192.0.2.1"
  Hub sends NHRP Resolution Reply to Spoke1:
    "Physical IP of 172.16.2.1 is 192.0.2.1"

STEP 3: Direct Spoke-to-Spoke Tunnel
  Spoke1 now knows: Spoke2's physical IP = 192.0.2.1
  Spoke1 creates a DYNAMIC GRE encapsulation directly to 192.0.2.1
  Traffic flows directly: Spoke1 ↔ Spoke2 (NO hairpinning through Hub!)

NHRP CACHE on Hub:
  +------------------+-----------------------+-------------+
  | Tunnel IP        | Physical IP           | Type        |
  +------------------+-----------------------+-------------+
  | 172.16.1.1       | 198.51.100.1          | Dynamic     |
  | 172.16.2.1       | 192.0.2.1             | Dynamic     |
  +------------------+-----------------------+-------------+
```

### 10.4 mGRE Packet Flow

```
INITIAL TRAFFIC (before NHRP resolution):
==========================================
Spoke1 → Hub → Spoke2 (traffic takes the hub path initially)

AFTER NHRP RESOLUTION:
========================
Spoke1 --------------------------> Spoke2 (DIRECT!)
          GRE tunnel, dst=192.0.2.1

TOPOLOGY:
==========

            +---------+
Spoke3 -----+         +------ Spoke4
            |   HUB   |
Spoke1 -----+         +------ Spoke2
            +---------+
                |
              Internet (NBMA cloud)

After NHRP resolution:
Spoke1 <===========================================> Spoke2 (direct GRE)
Spoke1 <===========================================> Spoke3 (direct GRE)
(Hub is bypassed for spoke-to-spoke traffic)
```

---

## 11. DMVPN — Dynamic Multipoint VPN (Built on mGRE)

### 11.1 What is DMVPN?

DMVPN (Dynamic Multipoint VPN) is a **Cisco technology** that combines:
- **mGRE** — for dynamic, multipoint tunneling
- **NHRP** — for dynamic mapping of tunnel IP → physical IP
- **IPsec** — for encryption (optional but standard in production)
- **Routing Protocol** — OSPF, EIGRP, or BGP for dynamic routing within the VPN

DMVPN creates a **scalable hub-and-spoke VPN** where spokes can communicate directly with each other without pre-configuring every possible tunnel.

### 11.2 DMVPN Phases

```
DMVPN PHASE 1 — Hub-and-Spoke Only:
=====================================
All spoke-to-spoke traffic goes through the hub.
Spokes have "spoke" tunnel configurations pointing to hub.
No direct spoke-to-spoke communication.
Use case: When spoke-to-spoke traffic is minimal.

  Spoke1 --[tunnel]--> Hub --[tunnel]--> Spoke2

DMVPN PHASE 2 — Dynamic Spoke-to-Spoke:
==========================================
Spokes can establish DIRECT tunnels to other spokes.
Hub provides the NHRP resolution.
After resolution, traffic flows directly spoke-to-spoke.
Routing: Next-hop must be PRESERVED (not changed at hub).
  This means EIGRP works naturally; OSPF requires next-hop unchanged.

  Spoke1 --[direct tunnel]--> Spoke2 (after NHRP resolution)

DMVPN PHASE 3 — Route Summarization at Hub + NHRP Shortcuts:
=============================================================
Hub summarizes routes, reducing routing table size at spokes.
Spokes use "NHRP shortcuts" — when traffic arrives at hub destined
for another spoke, hub sends NHRP Redirect to sender.
Sender then builds direct tunnel using NHRP resolution.
MORE scalable than Phase 2 (better route summarization support).

  Step 1: Spoke1 --> Hub (traffic, hub hasn't resolved path yet)
  Step 2: Hub sends NHRP Redirect to Spoke1: "Go directly to Spoke2"
  Step 3: Spoke1 sends NHRP Resolution Request to find Spoke2's physical IP
  Step 4: Direct tunnel established: Spoke1 <--> Spoke2
```

### 11.3 DMVPN + IPsec Architecture

```
DMVPN WITH IPSEC PROTECTION:
==============================

Physical Transport (Internet):
  All GRE packets are encrypted with IPsec ESP
  IPsec uses IKE to negotiate security associations dynamically
  Hub has a "profile" that spokes match — no per-spoke IPsec config needed!

CONFIGURATION MODEL:
  Hub:    1 tunnel interface, 1 IPsec profile → serves ALL spokes
  Spokes: 1 tunnel interface, 1 IPsec profile → connects to hub + dynamic spokes

PACKET FORMAT WITH DMVPN + IPSEC (transport mode):
  [Outer IP] [ESP Header] [GRE Header] [Inner IP] [Payload] [ESP Trailer] [ESP Auth]

OR with IPsec tunnel mode:
  [Outer IP] [ESP Header] [GRE-encrypted-inner-IP-payload] [ESP Trailer] [ESP Auth]
```

---

## 12. GRE over IPsec

### 12.1 Why Combine GRE and IPsec?

| Feature        | GRE Alone | IPsec Alone | GRE + IPsec |
|----------------|-----------|-------------|-------------|
| Encryption     | ❌ No     | ✅ Yes      | ✅ Yes      |
| Multicast      | ✅ Yes    | ❌ No       | ✅ Yes      |
| Dynamic Routing| ✅ Yes    | ❌ No*      | ✅ Yes      |
| Any Protocol   | ✅ Yes    | ❌ IP only  | ✅ Yes      |
| Authentication | ❌ No     | ✅ Yes      | ✅ Yes      |
| Overhead       | Low       | Medium      | High        |

*IPsec in tunnel mode only carries unicast IP packets. No multicast = no OSPF hello packets = no dynamic routing.

**GRE over IPsec** gives you: GRE's protocol flexibility + IPsec's security.

### 12.2 Two Approaches

#### Approach 1: GRE inside IPsec Tunnel Mode

```
PACKET STRUCTURE:
==================
[Outer IP: Src=phys_A, Dst=phys_B, Proto=50 (ESP)]
[ESP Header: SPI, Sequence Number]
[ENCRYPTED BLOCK BEGIN]
  [GRE Header: Protocol=0x0800]
  [Inner IP: Src=host_A, Dst=host_B]
  [Payload]
[ENCRYPTED BLOCK END]
[ESP Auth Tag (HMAC)]

How it works:
1. GRE encapsulates the inner packet
2. IPsec ESP encrypts the entire GRE packet (GRE header + inner packet)
3. IPsec adds outer IP header with ESP protocol (50)

The intermediate network sees: IP/ESP (Protocol 50)
The GRE header is HIDDEN inside the encrypted payload
```

#### Approach 2: GRE outside IPsec Transport Mode

```
PACKET STRUCTURE:
==================
[Outer IP: Src=phys_A, Dst=phys_B, Proto=47 (GRE)]
[GRE Header: Protocol=0x0800]
[ESP Header: SPI, Sequence Number]
[ENCRYPTED BLOCK BEGIN]
  [Inner IP: Src=host_A, Dst=host_B]
  [Payload]
[ENCRYPTED BLOCK END]
[ESP Auth Tag (HMAC)]

How it works:
1. IPsec ESP encrypts the inner packet (transport mode — ESP applied to inner IP)
2. GRE encapsulates the ESP-protected packet
3. Outer IP header carries GRE (Protocol 47)

The intermediate network sees: IP/GRE/ESP
The GRE header is VISIBLE (not encrypted)
```

### 12.3 Standard Deployment: GRE inside IPsec Tunnel Mode

The most common deployment is **GRE tunnel interface + IPsec crypto map** or **IPsec Virtual Tunnel Interface (VTI)**.

```
CONFIGURATION FLOW (Cisco):
=============================

1. Define IKE Phase 1 (ISAKMP Policy — negotiate encryption for key exchange):
   crypto isakmp policy 10
     encryption aes 256
     hash sha256
     authentication pre-share
     group 14           ! Diffie-Hellman group 14 (2048-bit)
     lifetime 86400

2. Define pre-shared key:
   crypto isakmp key MY_SECRET_KEY address 198.51.100.1

3. Define IPsec Transform Set (Phase 2 — data encryption):
   crypto ipsec transform-set GRE_IPSEC esp-aes 256 esp-sha256-hmac
     mode transport     ! Transport mode: IPsec encrypts inner IP payload
                        ! (Used when GRE is the outer wrapper)

4. Define Crypto Map (ties IPsec to GRE traffic):
   crypto map GRE_MAP 10 ipsec-isakmp
     set peer 198.51.100.1
     set transform-set GRE_IPSEC
     match address GRE_ACL          ! Match GRE traffic between endpoints

5. ACL to match GRE traffic:
   ip access-list extended GRE_ACL
     permit gre host 203.0.113.1 host 198.51.100.1

6. Apply crypto map to physical interface:
   interface GigabitEthernet0/0
     crypto map GRE_MAP

7. GRE tunnel interface (same as before):
   interface Tunnel0
     ip address 172.16.0.1 255.255.255.252
     tunnel source 203.0.113.1
     tunnel destination 198.51.100.1
     tunnel mode gre ip

RESULT:
  Any GRE traffic between 203.0.113.1 and 198.51.100.1
  is automatically encrypted by IPsec ESP before transmission.
```

### 12.4 Modern Approach: IPsec VTI (Virtual Tunnel Interface)

IPsec VTI eliminates the need for GRE when only IPv4/IPv6 is needed:

```
crypto ipsec profile IPSEC_PROFILE
  set transform-set MY_TRANSFORM

interface Tunnel0
  ip address 172.16.0.1 255.255.255.252
  tunnel source 203.0.113.1
  tunnel destination 198.51.100.1
  tunnel mode ipsec ipv4          ! IPsec tunnel mode (no GRE!)
  tunnel protection ipsec profile IPSEC_PROFILE
```

**When to use GRE + IPsec vs IPsec VTI:**
- Use **GRE + IPsec** when you need to carry multicast, IPv6, or non-IP protocols
- Use **IPsec VTI** when you only carry IPv4/IPv6 unicast (simpler, less overhead)

---

## 13. GRE over IPv6 (GRE6)

GRE6 carries passenger traffic **inside IPv6** (instead of IPv4 as the carrier).

```
GRE6 PACKET STRUCTURE:
========================
[Outer IPv6 Header: 40 bytes]
  Next Header: 47 (GRE)
  Src: 2001:db8::1 (Router A's IPv6 address)
  Dst: 2001:db8::2 (Router B's IPv6 address)
[GRE Header: 4+ bytes]
  Protocol: 0x0800 (if carrying IPv4)
         or 0x86DD (if carrying IPv6)
[Inner Packet: IPv4 or IPv6]

LINUX CONFIGURATION:
======================
# Create GRE over IPv6 tunnel
ip tunnel add gre6tun1 mode ip6gre \
  local 2001:db8::1 \
  remote 2001:db8::2

ip link set gre6tun1 up
ip addr add 172.16.0.1/30 dev gre6tun1
ip route add 10.2.2.0/24 dev gre6tun1

USE CASES:
  - Connecting IPv4 islands over an IPv6-only backbone
  - Running MPLS or other protocols over an IPv6 infrastructure
  - Future-proofing: IPv6 carrier networks carrying legacy IPv4

OVERHEAD:
  Outer IPv6 header: 40 bytes (vs 20 bytes for IPv4)
  GRE header: 4 bytes
  Total: 44 bytes overhead (vs 24 bytes for GRE over IPv4)
  Effective inner MTU: 1500 - 44 = 1456 bytes
```

---

## 14. IPv6 over GRE (6in4)

While similar in concept, **6in4** specifically carries IPv6 inside IPv4. It's technically a form of GRE (or can be done without GRE header using IP Protocol 41).

```
PURE 6IN4 (Protocol 41 — no GRE header):
==========================================
[Outer IPv4 Header: Protocol=41]
[Inner IPv6 Packet]

This is NOT GRE (no GRE header). It's a simpler form of tunneling.
Often called "IPv6-in-IPv4" or "6in4 tunnel."
Used by Hurricane Electric (he.net) for IPv6 tunnel brokers.

GRE-BASED IPv6 TUNNEL (Protocol 47):
======================================
[Outer IPv4 Header: Protocol=47 (GRE)]
[GRE Header: Protocol=0x86DD (IPv6)]
[Inner IPv6 Packet]

This IS GRE, carrying IPv6 as the passenger.

LINUX 6IN4 (not GRE):
=======================
ip tunnel add sit1 mode sit \      # SIT = Simple Internet Transition
  local 203.0.113.1 \
  remote 198.51.100.1
ip link set sit1 up
ip addr add 2001:db8::1/64 dev sit1
ip -6 route add ::/0 dev sit1

LINUX GRE CARRYING IPv6:
==========================
ip tunnel add gre1 mode gre \
  local 203.0.113.1 \
  remote 198.51.100.1
ip link set gre1 up
ip addr add 172.16.0.1/30 dev gre1    # tunnel management IP (IPv4)
ip -6 addr add 2001:db8::1/64 dev gre1  # tunnel IPv6 address
ip -6 route add 2001:db8:1::/48 dev gre1
```

---

## 15. GRE Security — Threats and Mitigations

### 15.1 GRE Has No Built-in Security

GRE provides **zero security** by itself:
- No authentication (anyone can send GRE packets to your tunnel endpoint)
- No encryption (inner packets are visible in plaintext)
- No integrity protection (packets can be tampered with)

### 15.2 Threat Model

```
THREAT 1: GRE Injection Attack
================================
An attacker on the Internet can craft GRE packets with:
  - Outer Src IP: spoofed (doesn't matter to the victim)
  - Outer Dst IP: Your tunnel endpoint IP
  - Protocol: 47 (GRE)
  - GRE header: any Protocol Type
  - Inner packet: any crafted packet

When your router receives and decapsulates this:
  - The inner packet enters your trusted internal network
  - As if it came from a trusted source
  - This BYPASSES your perimeter firewall!

ATTACK VECTOR:
  Attacker → [Spoofed GRE packet] → Router A → Decapsulate → Inner LAN
  Inner packet could be: spoofed ARP, DNS, ICMP, or even bypass ACLs

MITIGATION:
  1. Only allow GRE (Protocol 47) from specific trusted source IPs
  2. Deploy IPsec on top of GRE (encrypts and authenticates)
  3. Apply ACLs on physical interfaces: permit gre host TRUSTED_IP any
  4. Use GRE Key field for a lightweight (but not cryptographic) check

THREAT 2: GRE Snooping / Wiretapping
======================================
Anyone with access to the path between tunnel endpoints can:
  - Capture all GRE packets
  - See the outer headers (who's tunneling to whom)
  - See ALL inner packets in plaintext (since GRE has no encryption)
  - Reconstruct the complete communication

MITIGATION:
  Use IPsec (ESP) to encrypt GRE traffic.

THREAT 3: Tunnel Hijacking
===========================
An attacker who knows your tunnel source and destination IPs can:
  - Inject traffic into the tunnel from a spoofed source IP
  - Disrupt the tunnel by sending malformed GRE packets
  - Cause routing loops through crafted inner packets

MITIGATION:
  IPsec with pre-shared keys or certificates prevents this completely.
  IKE authentication ensures only legitimate endpoints can establish IPsec SAs.

THREAT 4: Reconnaissance via ICMP TTL Exceeded
================================================
GRE tunnels can leak information. If a packet inside the tunnel
has its inner TTL expire, the router may send ICMP TTL Exceeded
revealing internal topology (inner IP addresses, routing structure).

MITIGATION:
  no ip unreachables on tunnel interfaces (Cisco)
  iptables -A OUTPUT -p icmp --icmp-type time-exceeded -j DROP (carefully!)
```

### 15.3 Security Best Practices

```
SECURITY CHECKLIST FOR GRE DEPLOYMENTS:
=========================================

[ ] Always use GRE + IPsec in production (never bare GRE over untrusted networks)
[ ] Apply ingress ACL: permit gre host TUNNEL_SRC host TUNNEL_DST only
[ ] Apply uRPF (Unicast Reverse Path Forwarding) to prevent IP spoofing
[ ] Use strong IKE Phase 1: AES-256, SHA-256, DH Group 14+
[ ] Use strong IPsec Phase 2: AES-256-GCM (authenticated encryption)
[ ] Use certificates (PKI) instead of pre-shared keys for large deployments
[ ] Implement GRE keepalives to detect tunnel failures quickly
[ ] Monitor for unusual GRE traffic from unexpected source IPs
[ ] Set appropriate TTL on tunnel interfaces to prevent routing loops
[ ] Disable IP redirects on tunnel interfaces
[ ] Use "no ip proxy-arp" on tunnel interfaces
[ ] Regularly rotate IPsec pre-shared keys or use certificate-based auth
```

---

## 16. GRE vs Other Tunneling Protocols

### 16.1 Comprehensive Comparison Table

| Feature                 | GRE       | IPsec VTI | L2TP      | VXLAN     | WireGuard | OpenVPN   |
|-------------------------|-----------|-----------|-----------|-----------|-----------|-----------|
| Layer                   | L3        | L3        | L2        | L2        | L3        | L3/L2     |
| Encryption              | ❌ No     | ✅ Yes    | ❌ No*    | ❌ No*    | ✅ Yes    | ✅ Yes    |
| Authentication          | ❌ No     | ✅ Yes    | ✅ Yes    | ❌ No     | ✅ Yes    | ✅ Yes    |
| Multicast               | ✅ Yes    | ❌ No     | ❌ No     | ✅ Yes    | ❌ No     | ❌ No     |
| Any Protocol            | ✅ Yes    | IPv4/6    | ✅ Yes    | Ethernet  | IPv4/6    | IPv4/6    |
| Dynamic Routing         | ✅ Yes    | ✅ Yes    | ✅ Yes    | ✅ Yes    | Limited   | Limited   |
| Overhead (min)          | 24 bytes  | 36 bytes  | 32 bytes  | 50 bytes  | 32 bytes  | 38 bytes  |
| Stateful                | ❌ No     | ✅ Yes    | ✅ Yes    | ❌ No     | ✅ Yes    | ✅ Yes    |
| NAT Traversal           | Difficult | ✅ NAT-T  | ✅ Yes    | ✅ Yes    | ✅ Yes    | ✅ Yes    |
| Performance             | High      | High      | Medium    | High      | Very High | Medium    |
| Complexity              | Low       | Medium    | Medium    | Low       | Low       | Medium    |

*L2TP uses IPsec for security (L2TP/IPsec); VXLAN can use IPsec separately.

### 16.2 GRE vs VXLAN — Data Center Context

```
GRE:
  - Point-to-point or multipoint (mGRE)
  - Carries Layer 3 (IP) primarily, but can carry L2 with ERSPAN
  - Used in WAN, VPN, and routing environments
  - IP Protocol 47

VXLAN (Virtual eXtensible LAN):
  - Designed for DATA CENTER overlay networks
  - Carries Ethernet FRAMES (Layer 2 over Layer 3)
  - Uses UDP port 4789 (works easily through NAT)
  - 24-bit VNI (VXLAN Network Identifier) = 16 million segments
  - Used by OpenStack, VMware NSX, Docker networks, Kubernetes CNI

WHEN TO USE EACH:
  GRE:    WAN connectivity, branch offices, carrier networks, routing-based VPN
  VXLAN:  Data center VM mobility, multi-tenant cloud, software-defined networking
```

### 16.3 GRE vs WireGuard

```
GRE:                          WireGuard:
  No crypto (need IPsec)        Built-in state-of-the-art crypto
  Works at Layer 3              Works at Layer 3
  Supports any passenger        IPv4/IPv6 only
  Very low overhead (4 bytes)   ~32 bytes overhead
  Widely supported (Cisco, etc) Linux kernel (widely available)
  Stateless by default          Stateful (crypto state)
  Complex to secure             Simple to configure and secure
  Decades of proven operation   Newer (2016) but very clean design

USE GRE WHEN:
  - Carrying non-IP protocols (IPX, MPLS, bridged Ethernet)
  - Need multicast support through tunnel
  - Working with existing Cisco/network infrastructure
  - Building DMVPN architectures

USE WIREGUARD WHEN:
  - Linux-centric environment
  - Need simplest possible secure tunnel
  - Performance is critical (WireGuard has excellent throughput)
  - Remote access VPN for users
```

---

## 17. GRE in Linux — Implementation Deep Dive

### 17.1 Linux GRE Kernel Module

Linux implements GRE in the kernel via the `ip_gre` module. When you create a GRE tunnel, the kernel creates a virtual network device that handles encapsulation/decapsulation automatically.

```bash
# Check if ip_gre module is loaded
lsmod | grep gre
# ip_gre                 24576  0
# gre                    16384  1 ip_gre

# Load if not present
modprobe ip_gre

# View all tunnel interfaces
ip tunnel show

# View GRE-specific information
cat /proc/net/dev | grep gre
```

### 17.2 Creating Different GRE Tunnel Types in Linux

```bash
# ============================================================
# Type 1: Standard GRE Tunnel (IPv4 passenger over IPv4 carrier)
# ============================================================
ip tunnel add gre0 mode gre \
  local 203.0.113.1 \        # Local physical IP (tunnel source)
  remote 198.51.100.1 \      # Remote physical IP (tunnel destination)
  ttl 64 \                   # TTL for outer IP header
  dev eth0                   # Bind to this physical interface

ip link set gre0 up
ip addr add 172.16.0.1/30 dev gre0
ip route add 10.2.2.0/24 via 172.16.0.2  # Route via tunnel

# ============================================================
# Type 2: GRE with Key
# ============================================================
ip tunnel add gre1 mode gre \
  local 203.0.113.1 \
  remote 198.51.100.1 \
  key 12345 \                # 32-bit key value
  ttl 64

# ============================================================
# Type 3: GRE with Checksum
# ============================================================
ip tunnel add gre2 mode gre \
  local 203.0.113.1 \
  remote 198.51.100.1 \
  csum \                     # Enable GRE checksum
  ttl 64

# ============================================================
# Type 4: GRE over IPv6 (ip6gre)
# ============================================================
ip tunnel add gre3 mode ip6gre \
  local 2001:db8::1 \
  remote 2001:db8::2 \
  ttl 64

# ============================================================
# Type 5: mGRE-like: GRE with no fixed remote (gretap for L2)
# ============================================================
ip link add gretap0 type gretap \
  local 203.0.113.1 \
  remote 198.51.100.1
# gretap carries Ethernet frames (L2) not IP (L3)

# ============================================================
# MTU Management
# ============================================================
ip link set gre0 mtu 1476   # Standard GRE MTU (1500 - 24)

# ============================================================
# TCP MSS Clamping with iptables
# ============================================================
# Clamp MSS for traffic going INTO the tunnel
iptables -t mangle -A FORWARD -o gre0 -p tcp \
  --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1436

# ============================================================
# Verify and Monitor
# ============================================================
ip tunnel show gre0
ip -s link show gre0          # Show statistics
tcpdump -i eth0 proto 47      # Capture GRE packets
tcpdump -i gre0               # Capture inner traffic
```

### 17.3 Implementing GRE Manually in C (Conceptual Reference)

This shows the raw socket approach to understand GRE at the byte level.

```c
/*
 * gre_encap.c — Manual GRE Encapsulation (Conceptual)
 * Demonstrates the binary structure of GRE headers.
 * NOT a production implementation.
 *
 * Compile: gcc -o gre_encap gre_encap.c
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>   // htons, htonl

/* GRE Header structure (RFC 2784) */
struct gre_header {
    uint16_t flags_and_version;   /* Bits: C|R|K|S|s|Recur|Flags|Ver */
    uint16_t protocol_type;       /* EtherType of passenger protocol */
    /* Optional fields follow based on flags */
};

/* Extended GRE Header (with optional fields) */
struct gre_header_full {
    uint16_t flags_and_version;
    uint16_t protocol_type;
    uint32_t checksum_and_reserved;  /* Only if C=1 */
    uint32_t key;                    /* Only if K=1 */
    uint32_t sequence_number;        /* Only if S=1 */
};

/* GRE flag bit positions (in the 16-bit flags_and_version field) */
#define GRE_FLAG_CHECKSUM  (1 << 15)   /* Bit 0 — C bit */
#define GRE_FLAG_KEY       (1 << 13)   /* Bit 2 — K bit */
#define GRE_FLAG_SEQNUM    (1 << 12)   /* Bit 3 — S bit */
#define GRE_VERSION_0      0x0000      /* Version = 0 */

/* EtherType values for Protocol Type field */
#define ETHERTYPE_IPV4     0x0800
#define ETHERTYPE_IPV6     0x86DD
#define ETHERTYPE_MPLS     0x8847

/*
 * Build a minimal GRE header (4 bytes — no optional fields)
 *
 * @param buf         Output buffer (must be >= 4 bytes)
 * @param proto_type  EtherType of passenger protocol (e.g., 0x0800 for IPv4)
 * @return            Number of bytes written
 */
int gre_build_minimal_header(uint8_t *buf, uint16_t proto_type) {
    struct gre_header *hdr = (struct gre_header *)buf;

    /* Flags = 0 (no checksum, no key, no sequence number) */
    /* Version = 0 */
    hdr->flags_and_version = htons(GRE_VERSION_0);

    /* Protocol type (network byte order — big endian) */
    hdr->protocol_type = htons(proto_type);

    return sizeof(struct gre_header);  /* 4 bytes */
}

/*
 * Build a GRE header with Key field
 *
 * @param buf         Output buffer (must be >= 8 bytes)
 * @param proto_type  EtherType of passenger protocol
 * @param key         32-bit GRE key value
 * @return            Number of bytes written
 */
int gre_build_keyed_header(uint8_t *buf, uint16_t proto_type, uint32_t key) {
    uint8_t *ptr = buf;

    /* Flags: set K bit (bit 2 of high byte) */
    uint16_t flags = GRE_FLAG_KEY | GRE_VERSION_0;
    *(uint16_t *)ptr = htons(flags);
    ptr += 2;

    /* Protocol type */
    *(uint16_t *)ptr = htons(proto_type);
    ptr += 2;

    /* Key field (32 bits) */
    *(uint32_t *)ptr = htonl(key);
    ptr += 4;

    return (int)(ptr - buf);  /* 8 bytes */
}

/*
 * Parse a received GRE header
 *
 * @param buf     Input buffer containing GRE header
 * @param len     Length of buffer
 * @return        Offset to start of passenger payload (past GRE header)
 *                or -1 on error
 */
int gre_parse_header(const uint8_t *buf, int len,
                     uint16_t *proto_out, uint32_t *key_out) {
    if (len < 4) return -1;  /* Minimum GRE header is 4 bytes */

    const struct gre_header *hdr = (const struct gre_header *)buf;
    uint16_t flags = ntohs(hdr->flags_and_version);
    uint16_t version = flags & 0x0007;  /* Low 3 bits = version */

    if (version != 0) {
        fprintf(stderr, "Unsupported GRE version: %d\n", version);
        return -1;
    }

    *proto_out = ntohs(hdr->protocol_type);

    int offset = 4;  /* Minimum header consumed */

    /* If Checksum bit (C) is set, skip 4 bytes (checksum + reserved) */
    if (flags & GRE_FLAG_CHECKSUM) {
        if (len < offset + 4) return -1;
        offset += 4;
    }

    /* If Key bit (K) is set, read 4-byte key */
    if (flags & GRE_FLAG_KEY) {
        if (len < offset + 4) return -1;
        if (key_out) {
            *key_out = ntohl(*(const uint32_t *)(buf + offset));
        }
        offset += 4;
    }

    /* If Sequence Number bit (S) is set, skip 4 bytes */
    if (flags & GRE_FLAG_SEQNUM) {
        if (len < offset + 4) return -1;
        offset += 4;
    }

    return offset;  /* Offset to start of passenger payload */
}

/*
 * Print GRE header fields for debugging
 */
void gre_print_header(const uint8_t *buf, int len) {
    if (len < 4) {
        printf("Buffer too short for GRE header\n");
        return;
    }

    const struct gre_header *hdr = (const struct gre_header *)buf;
    uint16_t flags = ntohs(hdr->flags_and_version);

    printf("=== GRE Header ===\n");
    printf("  Flags raw: 0x%04X\n", flags);
    printf("  C (Checksum): %d\n", (flags >> 15) & 1);
    printf("  K (Key):      %d\n", (flags >> 13) & 1);
    printf("  S (Sequence): %d\n", (flags >> 12) & 1);
    printf("  Version:      %d\n", flags & 0x7);
    printf("  Protocol:     0x%04X", ntohs(hdr->protocol_type));
    switch (ntohs(hdr->protocol_type)) {
        case 0x0800: printf(" (IPv4)\n"); break;
        case 0x86DD: printf(" (IPv6)\n"); break;
        case 0x8847: printf(" (MPLS)\n"); break;
        default:     printf(" (Unknown)\n"); break;
    }

    int offset = 4;
    if (flags & GRE_FLAG_CHECKSUM) {
        uint16_t cksum = ntohs(*(const uint16_t *)(buf + offset));
        printf("  Checksum: 0x%04X\n", cksum);
        offset += 4;
    }
    if (flags & GRE_FLAG_KEY) {
        uint32_t key = ntohl(*(const uint32_t *)(buf + offset));
        printf("  Key: %u (0x%08X)\n", key, key);
        offset += 4;
    }
    if (flags & GRE_FLAG_SEQNUM) {
        uint32_t seq = ntohl(*(const uint32_t *)(buf + offset));
        printf("  Sequence: %u\n", seq);
        offset += 4;
    }
    printf("  Header size: %d bytes\n", offset);
    printf("  Passenger starts at byte: %d\n", offset);
    printf("==================\n");
}

/* Example usage */
int main(void) {
    uint8_t buf[32];
    int len;

    printf("--- Building minimal GRE header (IPv4 passenger) ---\n");
    len = gre_build_minimal_header(buf, ETHERTYPE_IPV4);
    gre_print_header(buf, len);

    printf("\n--- Building keyed GRE header (IPv6 passenger, key=0xDEADBEEF) ---\n");
    len = gre_build_keyed_header(buf, ETHERTYPE_IPV6, 0xDEADBEEF);
    gre_print_header(buf, len);

    printf("\n--- Parsing the keyed header ---\n");
    uint16_t proto;
    uint32_t key;
    int payload_offset = gre_parse_header(buf, len, &proto, &key);
    printf("Passenger protocol: 0x%04X\n", proto);
    printf("Key: 0x%08X (%u)\n", key, key);
    printf("Payload offset: %d bytes\n", payload_offset);

    return 0;
}
```

### 17.4 Implementing GRE in Go (Raw Socket Conceptual)

```go
// gre_packet.go — GRE packet building and parsing in Go
// Demonstrates GRE header manipulation.
// NOTE: Sending raw IP packets requires root privileges and raw sockets.

package main

import (
	"encoding/binary"
	"fmt"
)

// Protocol type constants (EtherType values used in GRE Protocol Type field)
const (
	ProtoTypeIPv4 = 0x0800
	ProtoTypeIPv6 = 0x86DD
	ProtoTypeMPLS = 0x8847
	ProtoTypeARP  = 0x0806
)

// GRE flag bit masks (applied to the first 16-bit word)
const (
	GREFlagChecksum = uint16(1 << 15) // C bit — checksum present
	GREFlagKey      = uint16(1 << 13) // K bit — key present
	GREFlagSeqNum   = uint16(1 << 12) // S bit — sequence number present
)

// GREHeader represents a parsed GRE header.
type GREHeader struct {
	ChecksumPresent  bool
	KeyPresent       bool
	SeqNumPresent    bool
	ProtocolType     uint16
	Checksum         uint16 // Only valid if ChecksumPresent == true
	Key              uint32 // Only valid if KeyPresent == true
	SequenceNumber   uint32 // Only valid if SeqNumPresent == true
	HeaderLength     int    // Total GRE header length in bytes
	PayloadOffset    int    // Offset to passenger payload in original buffer
}

// ParseGREHeader parses a GRE header from raw bytes.
// Returns parsed header and error.
// buf should start at the GRE header (after outer IP header).
func ParseGREHeader(buf []byte) (*GREHeader, error) {
	if len(buf) < 4 {
		return nil, fmt.Errorf("buffer too short: need 4 bytes, got %d", len(buf))
	}

	hdr := &GREHeader{}

	// Read the first 16-bit word (flags + version)
	flagsAndVersion := binary.BigEndian.Uint16(buf[0:2])

	// Parse flag bits
	hdr.ChecksumPresent = (flagsAndVersion & GREFlagChecksum) != 0
	hdr.KeyPresent = (flagsAndVersion & GREFlagKey) != 0
	hdr.SeqNumPresent = (flagsAndVersion & GREFlagSeqNum) != 0

	// Verify version = 0
	version := flagsAndVersion & 0x0007
	if version != 0 {
		return nil, fmt.Errorf("unsupported GRE version: %d", version)
	}

	// Read Protocol Type (second 16-bit word)
	hdr.ProtocolType = binary.BigEndian.Uint16(buf[2:4])

	// Parse optional fields
	offset := 4 // After mandatory 4-byte GRE header

	if hdr.ChecksumPresent {
		if len(buf) < offset+4 {
			return nil, fmt.Errorf("buffer too short for checksum field")
		}
		hdr.Checksum = binary.BigEndian.Uint16(buf[offset : offset+2])
		// Skip checksum (2 bytes) + reserved1 (2 bytes)
		offset += 4
	}

	if hdr.KeyPresent {
		if len(buf) < offset+4 {
			return nil, fmt.Errorf("buffer too short for key field")
		}
		hdr.Key = binary.BigEndian.Uint32(buf[offset : offset+4])
		offset += 4
	}

	if hdr.SeqNumPresent {
		if len(buf) < offset+4 {
			return nil, fmt.Errorf("buffer too short for sequence number field")
		}
		hdr.SequenceNumber = binary.BigEndian.Uint32(buf[offset : offset+4])
		offset += 4
	}

	hdr.HeaderLength = offset
	hdr.PayloadOffset = offset

	return hdr, nil
}

// BuildGREHeader serializes a GREHeader into bytes.
// Returns the bytes representing the GRE header.
func BuildGREHeader(hdr *GREHeader) ([]byte, error) {
	// Calculate required buffer size
	size := 4 // Mandatory fields
	if hdr.ChecksumPresent {
		size += 4
	}
	if hdr.KeyPresent {
		size += 4
	}
	if hdr.SeqNumPresent {
		size += 4
	}

	buf := make([]byte, size)

	// Build flags + version word
	var flagsAndVersion uint16
	if hdr.ChecksumPresent {
		flagsAndVersion |= GREFlagChecksum
	}
	if hdr.KeyPresent {
		flagsAndVersion |= GREFlagKey
	}
	if hdr.SeqNumPresent {
		flagsAndVersion |= GREFlagSeqNum
	}
	// Version = 0, already set (zero bits)

	binary.BigEndian.PutUint16(buf[0:2], flagsAndVersion)
	binary.BigEndian.PutUint16(buf[2:4], hdr.ProtocolType)

	offset := 4

	if hdr.ChecksumPresent {
		// Write checksum (and reserved = 0)
		binary.BigEndian.PutUint16(buf[offset:offset+2], hdr.Checksum)
		binary.BigEndian.PutUint16(buf[offset+2:offset+4], 0) // reserved1
		offset += 4
	}

	if hdr.KeyPresent {
		binary.BigEndian.PutUint32(buf[offset:offset+4], hdr.Key)
		offset += 4
	}

	if hdr.SeqNumPresent {
		binary.BigEndian.PutUint32(buf[offset:offset+4], hdr.SequenceNumber)
		offset += 4
	}

	return buf, nil
}

// ProtocolTypeName returns a human-readable name for the protocol type.
func ProtocolTypeName(pt uint16) string {
	switch pt {
	case ProtoTypeIPv4:
		return "IPv4"
	case ProtoTypeIPv6:
		return "IPv6"
	case ProtoTypeMPLS:
		return "MPLS"
	case ProtoTypeARP:
		return "ARP"
	case 0x6558:
		return "Ethernet (L2 over GRE)"
	default:
		return "Unknown"
	}
}

func (h *GREHeader) String() string {
	s := fmt.Sprintf("GRE Header {\n")
	s += fmt.Sprintf("  Protocol Type: 0x%04X (%s)\n", h.ProtocolType, ProtocolTypeName(h.ProtocolType))
	s += fmt.Sprintf("  Checksum Present: %v", h.ChecksumPresent)
	if h.ChecksumPresent {
		s += fmt.Sprintf(" (value: 0x%04X)", h.Checksum)
	}
	s += "\n"
	s += fmt.Sprintf("  Key Present: %v", h.KeyPresent)
	if h.KeyPresent {
		s += fmt.Sprintf(" (value: 0x%08X = %d)", h.Key, h.Key)
	}
	s += "\n"
	s += fmt.Sprintf("  Sequence Number Present: %v", h.SeqNumPresent)
	if h.SeqNumPresent {
		s += fmt.Sprintf(" (value: %d)", h.SequenceNumber)
	}
	s += "\n"
	s += fmt.Sprintf("  Total Header Length: %d bytes\n", h.HeaderLength)
	s += fmt.Sprintf("  Passenger Payload Offset: %d bytes\n", h.PayloadOffset)
	s += "}"
	return s
}

func main() {
	fmt.Println("=== GRE Header Building ===")

	// Build a minimal GRE header (IPv4 passenger)
	minimal := &GREHeader{
		ProtocolType: ProtoTypeIPv4,
	}
	minBytes, err := BuildGREHeader(minimal)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Minimal GRE (IPv4): %d bytes → % X\n", len(minBytes), minBytes)

	// Build a GRE header with Key (IPv6 passenger)
	keyed := &GREHeader{
		ProtocolType: ProtoTypeIPv6,
		KeyPresent:   true,
		Key:          0xDEADBEEF,
	}
	keyedBytes, _ := BuildGREHeader(keyed)
	fmt.Printf("Keyed GRE (IPv6):   %d bytes → % X\n", len(keyedBytes), keyedBytes)

	// Build a GRE header with all optional fields
	full := &GREHeader{
		ProtocolType:     ProtoTypeIPv4,
		ChecksumPresent:  true,
		Checksum:         0x1A2B,
		KeyPresent:       true,
		Key:              42,
		SeqNumPresent:    true,
		SequenceNumber:   1000,
	}
	fullBytes, _ := BuildGREHeader(full)
	fmt.Printf("Full GRE (all opts): %d bytes → % X\n", len(fullBytes), fullBytes)

	fmt.Println("\n=== GRE Header Parsing ===")

	// Parse the keyed header back
	parsed, err := ParseGREHeader(keyedBytes)
	if err != nil {
		panic(err)
	}
	fmt.Println(parsed)

	// Parse the full header
	parsedFull, err := ParseGREHeader(fullBytes)
	if err != nil {
		panic(err)
	}
	fmt.Println("\nFull header parsed:")
	fmt.Println(parsedFull)
}
```

### 17.5 GRE in Rust (Byte-Level Manipulation)

```rust
// gre.rs — GRE header parsing and building in Rust
// Demonstrates idiomatic Rust for network protocol handling.

/// GRE Protocol Type constants (EtherType values)
#[allow(dead_code)]
pub mod protocol_type {
    pub const IPV4: u16 = 0x0800;
    pub const IPV6: u16 = 0x86DD;
    pub const MPLS: u16 = 0x8847;
    pub const ARP:  u16 = 0x0806;
    pub const ETH_BRIDGING: u16 = 0x6558; // Transparent Ethernet Bridging
}

/// GRE flag bit masks (in the first 16-bit word)
const FLAG_CHECKSUM: u16 = 1 << 15; // C bit
const FLAG_KEY:      u16 = 1 << 13; // K bit
const FLAG_SEQNUM:   u16 = 1 << 12; // S bit
const VERSION_MASK:  u16 = 0x0007;  // Low 3 bits

/// A parsed GRE header.
#[derive(Debug, Clone, PartialEq)]
pub struct GREHeader {
    pub protocol_type: u16,
    pub checksum:      Option<u16>,
    pub key:           Option<u32>,
    pub sequence_num:  Option<u32>,
}

#[derive(Debug)]
pub enum GREError {
    BufferTooShort { needed: usize, got: usize },
    UnsupportedVersion(u16),
}

impl std::fmt::Display for GREError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GREError::BufferTooShort { needed, got } =>
                write!(f, "Buffer too short: needed {} bytes, got {}", needed, got),
            GREError::UnsupportedVersion(v) =>
                write!(f, "Unsupported GRE version: {} (expected 0)", v),
        }
    }
}

impl GREHeader {
    /// Parse a GRE header from raw bytes.
    /// Returns (header, payload_offset) on success.
    pub fn parse(buf: &[u8]) -> Result<(Self, usize), GREError> {
        if buf.len() < 4 {
            return Err(GREError::BufferTooShort { needed: 4, got: buf.len() });
        }

        // Read first two bytes as big-endian u16 (flags + version)
        let flags_and_version = u16::from_be_bytes([buf[0], buf[1]]);
        let protocol_type     = u16::from_be_bytes([buf[2], buf[3]]);

        // Validate version
        let version = flags_and_version & VERSION_MASK;
        if version != 0 {
            return Err(GREError::UnsupportedVersion(version));
        }

        let checksum_present = (flags_and_version & FLAG_CHECKSUM) != 0;
        let key_present      = (flags_and_version & FLAG_KEY)      != 0;
        let seqnum_present   = (flags_and_version & FLAG_SEQNUM)   != 0;

        let mut offset = 4usize; // After mandatory 4-byte header

        // Parse optional Checksum field
        let checksum = if checksum_present {
            if buf.len() < offset + 4 {
                return Err(GREError::BufferTooShort { needed: offset + 4, got: buf.len() });
            }
            let cksum = u16::from_be_bytes([buf[offset], buf[offset + 1]]);
            offset += 4; // Skip checksum (2) + reserved (2)
            Some(cksum)
        } else {
            None
        };

        // Parse optional Key field
        let key = if key_present {
            if buf.len() < offset + 4 {
                return Err(GREError::BufferTooShort { needed: offset + 4, got: buf.len() });
            }
            let k = u32::from_be_bytes([buf[offset], buf[offset+1], buf[offset+2], buf[offset+3]]);
            offset += 4;
            Some(k)
        } else {
            None
        };

        // Parse optional Sequence Number field
        let sequence_num = if seqnum_present {
            if buf.len() < offset + 4 {
                return Err(GREError::BufferTooShort { needed: offset + 4, got: buf.len() });
            }
            let s = u32::from_be_bytes([buf[offset], buf[offset+1], buf[offset+2], buf[offset+3]]);
            offset += 4;
            Some(s)
        } else {
            None
        };

        Ok((
            GREHeader { protocol_type, checksum, key, sequence_num },
            offset, // offset = start of passenger payload
        ))
    }

    /// Serialize the GRE header to bytes.
    pub fn serialize(&self) -> Vec<u8> {
        let size = self.header_len();
        let mut buf = vec![0u8; size];

        // Build flags + version word
        let mut flags: u16 = 0;
        if self.checksum.is_some() { flags |= FLAG_CHECKSUM; }
        if self.key.is_some()      { flags |= FLAG_KEY; }
        if self.sequence_num.is_some() { flags |= FLAG_SEQNUM; }

        buf[0..2].copy_from_slice(&flags.to_be_bytes());
        buf[2..4].copy_from_slice(&self.protocol_type.to_be_bytes());

        let mut offset = 4usize;

        if let Some(cksum) = self.checksum {
            buf[offset..offset+2].copy_from_slice(&cksum.to_be_bytes());
            // buf[offset+2..offset+4] is already 0 (reserved1)
            offset += 4;
        }

        if let Some(key) = self.key {
            buf[offset..offset+4].copy_from_slice(&key.to_be_bytes());
            offset += 4;
        }

        if let Some(seq) = self.sequence_num {
            buf[offset..offset+4].copy_from_slice(&seq.to_be_bytes());
            // offset += 4; // not needed (last field)
        }

        buf
    }

    /// Calculate the total GRE header length in bytes.
    pub fn header_len(&self) -> usize {
        4 // mandatory
        + if self.checksum.is_some() { 4 } else { 0 }
        + if self.key.is_some() { 4 } else { 0 }
        + if self.sequence_num.is_some() { 4 } else { 0 }
    }

    /// Return a human-readable protocol type name.
    pub fn protocol_name(&self) -> &'static str {
        match self.protocol_type {
            protocol_type::IPV4        => "IPv4",
            protocol_type::IPV6        => "IPv6",
            protocol_type::MPLS        => "MPLS",
            protocol_type::ARP         => "ARP",
            protocol_type::ETH_BRIDGING => "Ethernet Bridging",
            _                           => "Unknown",
        }
    }
}

impl std::fmt::Display for GREHeader {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "GRE Header {{")?;
        writeln!(f, "  Protocol Type:   0x{:04X} ({})", self.protocol_type, self.protocol_name())?;
        match self.checksum {
            Some(c) => writeln!(f, "  Checksum:        0x{:04X}", c)?,
            None    => writeln!(f, "  Checksum:        absent")?,
        }
        match self.key {
            Some(k) => writeln!(f, "  Key:             0x{:08X} ({})", k, k)?,
            None    => writeln!(f, "  Key:             absent")?,
        }
        match self.sequence_num {
            Some(s) => writeln!(f, "  Sequence Number: {}", s)?,
            None    => writeln!(f, "  Sequence Number: absent")?,
        }
        writeln!(f, "  Header Length:   {} bytes", self.header_len())?;
        write!(f, "}}")
    }
}

fn main() {
    println!("=== Building GRE Headers ===\n");

    // Minimal GRE header: IPv4 passenger, no optional fields
    let minimal = GREHeader {
        protocol_type: protocol_type::IPV4,
        checksum:      None,
        key:           None,
        sequence_num:  None,
    };
    let bytes = minimal.serialize();
    println!("Minimal (IPv4):\n{}", minimal);
    println!("Wire bytes ({} bytes): {:02X?}\n", bytes.len(), bytes);

    // GRE with key: IPv6 passenger, key=0xCAFEBABE
    let keyed = GREHeader {
        protocol_type: protocol_type::IPV6,
        checksum:      None,
        key:           Some(0xCAFEBABE),
        sequence_num:  None,
    };
    let keyed_bytes = keyed.serialize();
    println!("Keyed (IPv6, key=0xCAFEBABE):\n{}", keyed);
    println!("Wire bytes ({} bytes): {:02X?}\n", keyed_bytes.len(), keyed_bytes);

    // Full GRE: all optional fields
    let full = GREHeader {
        protocol_type: protocol_type::IPV4,
        checksum:      Some(0xABCD),
        key:           Some(12345),
        sequence_num:  Some(999),
    };
    let full_bytes = full.serialize();
    println!("Full (all options):\n{}", full);
    println!("Wire bytes ({} bytes): {:02X?}\n", full_bytes.len(), full_bytes);

    println!("=== Parsing GRE Headers ===\n");

    // Round-trip: serialize then parse
    match GREHeader::parse(&full_bytes) {
        Ok((parsed, payload_offset)) => {
            println!("Parsed from full_bytes:\n{}", parsed);
            println!("Passenger payload starts at byte: {}", payload_offset);
            assert_eq!(parsed, full, "Round-trip failed!");
            println!("Round-trip OK ✓");
        }
        Err(e) => eprintln!("Parse error: {}", e),
    }

    // Test error: buffer too short
    let short = [0x20u8, 0x00]; // Only 2 bytes — too short
    match GREHeader::parse(&short) {
        Err(e) => println!("\nExpected error: {}", e),
        Ok(_)  => println!("ERROR: should have failed!"),
    }
}
```

---

## 18. Troubleshooting GRE — Expert Methodology

### 18.1 Systematic Troubleshooting Framework

```
GRE TROUBLESHOOTING DECISION TREE:
====================================

START: "GRE tunnel is not working"
            |
            v
    Is tunnel interface UP/UP?
    (show interface Tunnel0)
         /        \
       YES          NO (UP/DOWN or DOWN/DOWN)
        |                    |
        v                    v
  Can ping tunnel        Check physical connectivity:
  destination IP?        ping tunnel destination IP
  (172.16.0.2)          from physical interface
       /    \                 /         \
     YES      NO           YES           NO
      |        |             |             |
      v        v             v             v
  Traffic   Routing       Check:          Fix physical
  flowing?  issue        - ACL blocking  routing first
            (see §18.2)  - Firewall      (BGP/OSPF/static)
                         - NAT issue
                         - Proto 47 blocked
```

### 18.2 Common Issues and Diagnostics

```
ISSUE 1: Tunnel is UP/DOWN (line protocol down)
================================================
CAUSE:    Tunnel destination IP is NOT reachable.
DIAGNOSE:
  Cisco:  ping 198.51.100.1 source 203.0.113.1
          show ip route 198.51.100.1
  Linux:  ping -I eth0 198.51.100.1
          ip route get 198.51.100.1
FIX:      Fix the underlying routing to reach tunnel destination.

ISSUE 2: Tunnel is UP/UP but no traffic flows
==============================================
CAUSE A:  Protocol 47 (GRE) is blocked by firewall.
DIAGNOSE: 
  Wireshark/tcpdump: tcpdump -i eth0 proto 47
  If you see GRE packets leaving but not arriving → BLOCKED.
FIX:      Allow IP Protocol 47 in firewall rules.

CAUSE B:  Routing loop (recursive routing).
DIAGNOSE:
  traceroute to tunnel destination → loops back through tunnel?
  show ip route 198.51.100.1 → exits via Tunnel0? (BAD)
FIX:      Add specific static route for tunnel destination via physical interface.

CAUSE C:  MTU issue causing silent packet drops.
DIAGNOSE:
  ping with large packets: ping -s 1472 -M do 10.2.2.20 (Linux)
  If small pings work (< 1000 bytes) but large fail → MTU problem.
FIX:      Set tunnel MTU to 1476.
          Apply TCP MSS clamping.

ISSUE 3: Tunnel flaps (goes up and down repeatedly)
=====================================================
CAUSE A:  Keepalive misconfiguration.
DIAGNOSE: show interface Tunnel0 → "Line protocol is down (keepalive timeout)"
FIX:      Increase keepalive timer or disable keepalives.

CAUSE B:  Routing table instability.
DIAGNOSE: debug ip routing → frequent route adds/removes for tunnel destination.
FIX:      Stabilize underlying routing.

CAUSE C:  Recursive routing loop (self-referential routing).
DIAGNOSE: As above.

ISSUE 4: One-way traffic (pings get through one way but not the other)
=======================================================================
CAUSE A:  Asymmetric routing — return path uses different path.
DIAGNOSE: traceroute from BOTH sides.
FIX:      Ensure symmetric routing or GRE is configured on both sides.

CAUSE B:  Firewall allowing outbound GRE but blocking inbound.
DIAGNOSE: Capture on both physical interfaces.
FIX:      Allow bidirectional GRE (Protocol 47).

ISSUE 5: GRE tunnel works but performance is poor
===================================================
CAUSE A:  MTU causing fragmentation.
DIAGNOSE: ping -s 1472 -M do → failures indicate fragmentation.
FIX:      Set ip mtu 1476 on tunnel interface, apply MSS clamping.

CAUSE B:  CPU overload from fragmentation/reassembly.
DIAGNOSE: show processes cpu (Cisco), top/mpstat (Linux).
FIX:      Fix MTU, enable hardware offloading if available.
```

### 18.3 Key Show Commands and Their Meaning

```
Cisco IOS Diagnostic Commands:
================================

show interface Tunnel0
  → Shows UP/UP status, encapsulation type, tunnel parameters, packet counts

show ip interface Tunnel0
  → Shows IP configuration, ACLs applied, helper addresses

show ip route
  → Verify routes exist for both:
    1. Tunnel destination (via physical interface)
    2. Remote subnets (via tunnel interface or tunnel next-hop)

show tunnel endpoints
  → Lists all active tunnel endpoints and their state

debug ip packet detail
  → Shows packet-level decisions (enable briefly, creates CPU load!)

debug tunnel
  → Shows tunnel-specific events (encapsulation, decapsulation, keepalives)

ping 172.16.0.2 source 172.16.0.1
  → Test tunnel end-to-end connectivity

ping 172.16.0.2 source 172.16.0.1 size 1500 df-bit
  → Test MTU — will fail if MTU is a problem

traceroute 10.2.2.20 source 10.1.1.1
  → Trace path through tunnel

Linux Diagnostic Commands:
===========================

ip tunnel show gre0
  → Shows tunnel parameters

ip -s link show gre0
  → Shows statistics (rx/tx packets, errors, drops)

tcpdump -i eth0 proto 47
  → Capture GRE packets on physical interface

tcpdump -i gre0
  → Capture inner traffic inside the tunnel

ping -I gre0 172.16.0.2
  → Ping through the tunnel interface

ping -c 3 -s 1472 -M do 172.16.0.2
  → Test MTU with large packets and DF bit set

ip route get 198.51.100.1
  → Check how tunnel destination is reached

cat /proc/net/dev | grep gre
  → Quick statistics
```

---

## 19. Real-World Use Cases

### 19.1 Enterprise WAN Connectivity

```
USE CASE: Connect two office sites over the Internet.

+------------+              Internet              +------------+
| Office A   |                                    | Office B   |
| 10.1.0.0/16|--[GRE+IPsec Tunnel]---------------|10.2.0.0/16 |
+------------+                                    +------------+

Why GRE instead of pure IPsec?
  - Need to run OSPF/EIGRP across the tunnel (multicast needed)
  - Single tunnel interface simplifies routing configuration
  - Can carry non-IP protocols if needed (legacy apps)
```

### 19.2 ISP 6in4 Tunnels — IPv6 Transition

```
USE CASE: ISP provides IPv6 access over IPv4-only infrastructure.

End User (has only IPv4)          ISP Tunnel Broker (has IPv6 backbone)
  IPv6 traffic                        IPv6 traffic
     ↓                                      ↓
[GRE/6in4 encapsulation]           [GRE/6in4 decapsulation]
     ↓                                      ↓
  IPv4 to ISP ←[GRE tunnel]→ IPv4 backbone → Global IPv6 Internet

Real-world example: Hurricane Electric (he.net) tunnel broker
  - Free IPv6 tunnels for anyone with an IPv4 address
  - Uses Protocol 41 (6in4), not GRE, but same concept
```

### 19.3 Cloud Provider Virtual Networks

```
USE CASE: AWS VPC uses GRE (with GENEVE, a GRE evolution) for:
  - Isolating customer virtual networks
  - VPC peering connections
  - Transit Gateway routing

Each VPC gets a unique VNI (Virtual Network Identifier)
Equivalent to GRE Key — identifies which virtual network the packet belongs to.

Physical server: multiple VMs from different customers
  VM1 (Customer A, VNI=100) ──→ encapsulate in GRE, key=100 ──→ underlay
  VM2 (Customer B, VNI=200) ──→ encapsulate in GRE, key=200 ──→ underlay

Underlay sees: all traffic as IP/GRE
No customer can see another's traffic
```

### 19.4 MPLS over GRE

```
USE CASE: Carry MPLS labeled packets over an IP backbone that doesn't support MPLS.

MPLS enables:
  - Traffic engineering
  - VPN services (MPLS L3VPN, L2VPN)
  - Quality of Service (QoS) based on labels

But the path between two MPLS clouds may be an IP-only Internet link.
Solution: Encapsulate MPLS in GRE.

+[MPLS Cloud A]+                              +[MPLS Cloud B]+
|  MPLS router  |---[GRE tunnel, Protocol    |  MPLS router  |
|               |    Type=0x8847 (MPLS)]-----|               |
+---------------+                            +---------------+

Packet structure:
  [Outer IPv4] [GRE: Protocol=0x8847] [MPLS Label Stack] [IPv4/IPv6 Payload]
```

### 19.5 SD-WAN

Software-Defined WAN products (Cisco Viptela, VMware SD-WAN, Versa) use GRE (or GRE-like protocols) as the transport layer for their overlay networks:

```
SD-WAN OVERLAY ARCHITECTURE:
==============================

+----------+    +----------+    +----------+
| Branch 1 |    | Branch 2 |    | Branch 3 |
|  vEdge   |    |  vEdge   |    |  vEdge   |
+----+-----+    +----+-----+    +----+-----+
     |               |               |
     +-------+-------+-------+-------+
             |               |
         Internet           MPLS
             |               |
     +-------+-------+-------+-------+
             |
        +----+----+
        |  vSmart |  (Controller — NHRP-like resolution)
        +---------+

Each branch connects to the overlay via GRE tunnels.
The controller tells each branch where other branches are (like NHRP).
Traffic flows directly branch-to-branch (like DMVPN Phase 3).
All tunnels encrypted with IPsec.
```

---

## 20. Mental Models and Summary

### 20.1 The Five Core Mental Models for GRE

```
MENTAL MODEL 1: The Postal Envelope
=====================================
Inner packet = the letter you want to send
GRE header   = the glue between envelopes
Outer packet = the envelope the postal system sees
Tunnel        = the postal route
Decapsulation = the recipient opening the envelope

MENTAL MODEL 2: The Trojan Horse
==================================
The inner packet (which the intermediate network can't handle)
is hidden inside an outer packet (which the network CAN handle).
The intermediate network "trusts" the outer packet and routes it.
At the destination, the true content is revealed.

MENTAL MODEL 3: The Virtual Wire
==================================
Despite packets traveling across complex networks, GRE creates
an ILLUSION of a direct wire between two routers.
Routing protocols don't know the difference — they see what
looks like a directly connected link.

MENTAL MODEL 4: The Sandwich
==============================
A GRE packet is literally a sandwich:
  TOP BUN:     Outer IP header (the carrier)
  FILLING 1:   GRE header (the protocol indicator)
  FILLING 2:   Inner IP header (the real destination info)
  BOTTOM BUN:  Inner payload (TCP/UDP/application data)

MENTAL MODEL 5: Protocol Agnosticism
======================================
GRE doesn't care WHAT it carries. It's a universal transport.
As long as there's an EtherType assigned to your protocol,
GRE can carry it. This is why it outlasted many alternatives.
```

### 20.2 Complete GRE Reference Card

```
+==============================================================================+
|                          GRE COMPLETE REFERENCE                              |
+==============================================================================+
| RFC:              2784 (base), 2890 (key/seqnum extensions)                  |
| IP Protocol:      47                                                         |
| Header Size:      4 bytes (min) to 20 bytes (max, all optional fields)       |
| Total Overhead:   24 bytes min (4 GRE + 20 outer IPv4) over IPv4             |
|                   44 bytes min (4 GRE + 40 outer IPv6) over IPv6             |
| Encryption:       None (use IPsec: add ~40-60 bytes more)                    |
| Authentication:   None (use IPsec)                                           |
| Stateful:         No (stateless — no connection establishment)               |
| Multicast:        YES (key advantage)                                        |
| Passenger Proto:  Any (identified by 16-bit EtherType in GRE header)        |
| Carrier Proto:    Any (typically IPv4 or IPv6)                               |
+------------------------------------------------------------------------------+
|                         HEADER FLAGS SUMMARY                                 |
+------+---+------------------------------------------------------------------+
| Bit  | # | Meaning                                                          |
+------+---+------------------------------------------------------------------+
|  0   | C | Checksum Present (adds 4 bytes: 2 checksum + 2 reserved)         |
|  1   | - | Reserved (must be 0 in RFC 2784)                                 |
|  2   | K | Key Present (adds 4 bytes: 32-bit key value)                     |
|  3   | S | Sequence Number Present (adds 4 bytes: 32-bit seq num)           |
| 4-7  | - | Reserved (must be 0)                                             |
| 8-12 | - | Flags (must be 0 in RFC 2784)                                    |
|13-15 |Ver| Version = 0 (always)                                             |
+------+---+------------------------------------------------------------------+
|                    COMMON PROTOCOL TYPE VALUES                               |
+----------+------------------------------------------------------------------+
| 0x0800   | IPv4                                                             |
| 0x86DD   | IPv6                                                             |
| 0x8847   | MPLS Unicast                                                     |
| 0x0806   | ARP                                                              |
| 0x6558   | Transparent Ethernet Bridging (L2 over GRE)                     |
+----------+------------------------------------------------------------------+
|                         MTU CALCULATIONS                                     |
+----------------------------------+------------------------------------------+
| GRE over IPv4                    | 1500 - 20 - 4 = 1476 bytes               |
| GRE over IPv6                    | 1500 - 40 - 4 = 1456 bytes               |
| GRE+IPsec (ESP tunnel, AES-CBC)  | ~1418 bytes (varies by cipher)           |
| TCP MSS for GRE over IPv4        | 1476 - 20 (IP) - 20 (TCP) = 1436 bytes  |
+----------------------------------+------------------------------------------+
|                        KEY DESIGN DECISIONS                                  |
+==============================================================================+
| Use GRE when:                                                                |
|  - Need to carry multicast through tunnel (OSPF, EIGRP, PIM)                |
|  - Need to carry non-IP protocols (MPLS, IPX, Ethernet frames)              |
|  - Building DMVPN architecture                                               |
|  - Existing infrastructure requires GRE-compatible tunneling                 |
|                                                                              |
| Use GRE + IPsec when:                                                        |
|  - Running over untrusted networks (Internet)                                |
|  - Need encryption AND multicast support                                     |
|                                                                              |
| Use IPsec VTI instead of GRE when:                                           |
|  - Carrying IPv4/IPv6 unicast ONLY (no multicast, no non-IP)                |
|  - Want less overhead (no GRE header)                                        |
|                                                                              |
| Use mGRE + NHRP (DMVPN) when:                                               |
|  - Hub-and-spoke topology with many spokes                                   |
|  - Spokes have dynamic IP addresses (DHCP)                                   |
|  - Want direct spoke-to-spoke communication without pre-configuration        |
+==============================================================================+
```

### 20.3 Chronological Evolution of GRE

```
TIMELINE:
==========
1994 ── RFC 1701: Original GRE (Cisco)
           Full-featured: checksum, routing, key, sequence number
           Allowed recursive encapsulation (Recur field)

1994 ── RFC 1702: GRE over IPv4
           Specified how GRE runs over IPv4 specifically

1996 ── Cisco introduces mGRE for DMVPN
           Not an RFC — Cisco proprietary at first

1999 ── GRE Keepalives added (Cisco proprietary)

2000 ── RFC 2784: Revised GRE (simplified)
           Deprecated: Routing (source routing), Recur field
           Simplified: Checksum field changed, reserved bits clarified
           This is the CURRENT standard

2000 ── RFC 2890: GRE Key and Sequence Number Extensions
           Formally specified K bit and S bit usage
           Separated from RFC 2784 for modularity

2006 ── DMVPN Phase 2, 3 developed
           mGRE + NHRP + IPsec becomes industry standard

2014 ── GENEVE (Generic Network Virtualization Encapsulation)
           RFC 8926 (2020)
           Evolution of GRE for data center use (like VXLAN + GRE)
           Uses UDP transport (NAT-friendly)
           Variable-length options (like GRE but with TLV extensions)
           Used by AWS, Azure, Google Cloud for VPC networking
```

### 20.4 Protocol Number 47 — Why It Matters

```
IP PROTOCOL NUMBERS (partial list):
=====================================
Protocol 1  — ICMP (ping)
Protocol 6  — TCP
Protocol 17 — UDP
Protocol 41 — IPv6-in-IPv4 (6in4, no GRE header)
Protocol 47 — GRE ← OUR SUBJECT
Protocol 50 — ESP (IPsec Encapsulating Security Payload)
Protocol 51 — AH (IPsec Authentication Header)
Protocol 89 — OSPF
Protocol 103 — PIM (Protocol Independent Multicast)
Protocol 132 — SCTP

When a router receives an IP packet with Protocol=47:
  1. It looks up its protocol demultiplexer
  2. Passes the payload to the GRE handler
  3. GRE handler strips the GRE header
  4. Reads Protocol Type field to identify passenger
  5. Passes inner packet to appropriate handler (IPv4, IPv6, etc.)

Firewalls that "block all non-TCP/UDP" will block GRE.
You must explicitly allow Protocol 47 for GRE tunnels.
```

---

*End of GRE Protocol Complete Guide*

---

> **Reference RFCs:**
> - RFC 1701 — Generic Routing Encapsulation (original, 1994)
> - RFC 1702 — Generic Routing Encapsulation over IPv4 (1994)
> - RFC 2784 — Generic Routing Encapsulation (revised standard, 2000)
> - RFC 2890 — Key and Sequence Number Extensions to GRE (2000)
> - RFC 8926 — GENEVE (successor for data center use, 2020)

> **Related RFCs:**
> - RFC 3948 — UDP Encapsulation of IPsec ESP (NAT-T for GRE+IPsec deployments)
> - RFC 2332 — NBMA Next Hop Resolution Protocol (NHRP — used with mGRE/DMVPN)
> - RFC 7348 — VXLAN (comparison: L2 tunneling, UDP-based)

Here is your complete GRE protocol guide. Here's a map of everything covered:

**Foundations** — What GRE is, what problem it solves (the "envelope" mental model), core vocabulary (tunnel, encapsulation, passenger protocol, carrier protocol, NBMA, NHRP, etc.), and where GRE sits in the OSI stack.

**Packet Anatomy** — Every single bit of the GRE header dissected: the C/K/S flags, what each optional field (Checksum, Key, Sequence Number) is, when to use each, header size calculation for every flag combination, and all EtherType Protocol Type values.

**Mechanics** — Step-by-step packet walk-through with ASCII wire diagrams showing exactly what the packet looks like at each stage (encapsulation → transit → decapsulation). The dual routing table lookup problem is explained precisely.

**Tunnel Behavior** — Why GRE is stateless (no handshake), how tunnel UP/DOWN state is determined, the recursive routing pitfall and how to kill it, and split tunneling vs full tunnel.

**Keepalives** — The clever self-addressing trick that makes GRE keepalives work without requiring the remote end to know anything about them.

**MTU** — The hidden complexity that breaks real deployments: fragmentation, PMTUD, DF-bit behavior, TCP MSS clamping with exact byte calculations for every tunnel type combination.

**mGRE + DMVPN** — How Multipoint GRE solves hub-and-spoke scaling, NHRP resolution flow, DMVPN Phases 1/2/3 with their trade-offs.

**GRE + IPsec** — Why they're combined, two structural approaches, configuration model, and when to use IPsec VTI instead.

**Security** — GRE injection attacks, snooping, hijacking — all with mitigations.

**Code** — GRE header building and parsing implemented in C, Go, and Rust at the byte level — giving you a concrete mental model of the wire format.

**Troubleshooting** — Decision tree, all common failure modes with diagnosis and fix commands for both Cisco IOS and Linux.