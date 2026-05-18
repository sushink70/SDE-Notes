# IPIP Protocol — Complete, In-Depth Guide
> *"To master a protocol is to think like the network itself."*

---

## Table of Contents

1. [Foundational Mental Model — What Is a Protocol?](#1-foundational-mental-model)
2. [What Is Tunneling?](#2-what-is-tunneling)
3. [What Is IPIP?](#3-what-is-ipip)
4. [History and RFC Standards](#4-history-and-rfc-standards)
5. [The IP Header — Deep Understanding](#5-the-ip-header)
6. [IPIP Packet Structure — Anatomy](#6-ipip-packet-structure)
7. [Encapsulation — Step-by-Step](#7-encapsulation)
8. [Decapsulation — Step-by-Step](#8-decapsulation)
9. [TTL Handling](#9-ttl-handling)
10. [MTU and Fragmentation](#10-mtu-and-fragmentation)
11. [Checksum Behavior](#11-checksum-behavior)
12. [Protocol Number and Identification](#12-protocol-number-and-identification)
13. [IPIP vs Other Tunneling Protocols](#13-ipip-vs-other-tunneling-protocols)
14. [Use Cases and Real-World Applications](#14-use-cases)
15. [IPIP in the Linux Kernel](#15-ipip-in-linux-kernel)
16. [ASCII Network Diagrams — Real Protocol Flow](#16-ascii-network-diagrams)
17. [Decision Trees and Flowcharts](#17-decision-trees-and-flowcharts)
18. [C Implementation — Raw Sockets](#18-c-implementation)
19. [Rust Implementation](#19-rust-implementation)
20. [Security Considerations](#20-security-considerations)
21. [Debugging and Observability](#21-debugging-and-observability)
22. [Mental Models and Cognitive Frameworks](#22-mental-models)

---

## 1. Foundational Mental Model

### What Is a Protocol?

A **protocol** is a formal, agreed-upon set of rules that governs how data is
formatted, transmitted, received, and interpreted between two or more systems.

Think of it like a contract between machines:
- "I will send you data in this exact format."
- "You will interpret the first 20 bytes as a header."
- "The header will tell you how to handle the rest."

Every protocol defines:

```
+------------------+------------------------------------------+
| Component        | What it means                            |
+------------------+------------------------------------------+
| Header           | Metadata about the data (addresses, etc) |
| Payload          | The actual content being carried         |
| Encapsulation    | Wrapping data inside another protocol    |
| Protocol Number  | ID used to identify which protocol       |
| RFC              | Request For Comments — official standard |
+------------------+------------------------------------------+
```

### The OSI Model — Where IPIP Lives

```
+-----+------------------+------------------------------------------+
| OSI | Layer Name       | Examples                                 |
+-----+------------------+------------------------------------------+
|  7  | Application      | HTTP, DNS, FTP, SMTP                     |
|  6  | Presentation     | TLS/SSL, encoding                        |
|  5  | Session          | sockets, session management              |
|  4  | Transport        | TCP, UDP, SCTP                           |
|  3  | Network          | IP, ICMP, OSPF  <-- IPIP lives HERE      |
|  2  | Data Link        | Ethernet, Wi-Fi (MAC frames)             |
|  1  | Physical         | Cables, radio, fiber optics              |
+-----+------------------+------------------------------------------+
```

IPIP operates entirely at **Layer 3 (Network Layer)**. It wraps one IP packet
inside another IP packet. No TCP, no UDP is involved in the tunnel header itself.

---

## 2. What Is Tunneling?

### The Core Concept

Imagine you want to send a letter from City A to City C, but the postal route
only goes through City B, and City B does not understand your letter's addressing.

**Solution:** Put your letter inside another envelope addressed to City B. City B
opens the outer envelope, reads the inner envelope's address, and delivers it.

That is **tunneling**.

```
WITHOUT TUNNELING:
  [Sender] ---> [Router1] ---> [Router2] ---> [Receiver]
                  Understands    Understands
                  the address    the address

WITH TUNNELING (different address space in the middle):
  [Sender] ---outer-IP-to--> [TunnelEndpoint] ---inner-IP-to--> [Receiver]
              "wrap it"          "unwrap it"
```

### Why Do We Need Tunneling?

| Problem                                | Tunneling Solution                          |
|----------------------------------------|---------------------------------------------|
| Private IP over public Internet        | Wrap private IP inside public IP            |
| IPv6 over IPv4 infrastructure          | Wrap IPv6 packet inside IPv4 packet         |
| Connect two remote private networks    | VPN tunnel between two gateways             |
| Route around broken network path       | Tunnel through a working alternate path     |
| Mobile IP — keep address while moving  | Home agent tunnels packets to mobile node   |

### The Tunnel Abstraction

```
  Real Network (physical path):
  [HostA] === [RouterX] === [RouterY] === [HostB]

  Logical Tunnel (virtual path):
  [HostA] ============================== [HostB]
          (tunnel hides all middle hops)
```

A **tunnel endpoint** is a machine that:
1. **Encapsulates** — wraps outgoing packets with an outer header.
2. **Decapsulates** — strips the outer header from incoming tunneled packets.

---

## 3. What Is IPIP?

### Definition

**IPIP** stands for **IP-in-IP tunneling**. It is the simplest possible
tunneling protocol at the network layer. It takes an entire IP packet
(header + payload) and wraps it as the **payload** of another IP packet.

```
IPIP Packet:
+------------------+------------------+-----------------------------+
| Outer IP Header  | Inner IP Header  |  Original Payload (data)    |
| (tunnel header)  | (original header)|  (TCP/UDP/ICMP/etc.)        |
+------------------+------------------+-----------------------------+
 <--- added by      <--- original --->  <--- original ------------>
      the tunnel
      endpoint
```

### Key Characteristics

| Property          | Value                                               |
|-------------------|-----------------------------------------------------|
| RFC               | RFC 2003 (IPv4), RFC 2473 (IPv6)                    |
| Protocol Number   | 4 (IP protocol number for "IP within IP")           |
| Header Overhead   | 20 bytes (minimal — just another IP header)         |
| Encryption        | None (IPIP is plain — not encrypted)                |
| Authentication    | None                                                |
| Multicast support | No (basic IPIP does not support multicast)          |
| Complexity        | Very low — simplest tunnel protocol                 |
| Performance       | Very high — minimal overhead                        |

### The Protocol Number Concept

**What is a protocol number?**
When an IP packet arrives at a machine, the IP header contains a field called
**Protocol** (1 byte). This tells the OS what is inside the IP payload.

```
+--------+--------+
| Field  | Value  |   Meaning
+--------+--------+
| Proto  |   1    |   ICMP (ping)
| Proto  |   6    |   TCP
| Proto  |  17    |   UDP
| Proto  |   4    |   IP (IPIP tunnel!)  <--- this is IPIP
| Proto  |  41    |   IPv6 (6in4 tunnel)
| Proto  |  47    |   GRE (Generic Routing Encapsulation)
+--------+--------+
```

When the outer IP header has **Protocol = 4**, it means: "The payload of this
IP packet is itself another IP packet." This is the IPIP signal.

---

## 4. History and RFC Standards

### Timeline

```
1996  RFC 1853 — "IP in IP Tunneling" (early draft, informational)
      |
      v
1996  RFC 2003 — "IP Encapsulation within IP" (the canonical IPIP standard)
      |           Authored by C. Perkins
      v
1998  RFC 2473 — "Generic Packet Tunneling in IPv6 Specification"
      |           Extends the concept to IPv6
      v
2002  RFC 3344 — "IP Mobility Support for IPv4" (Mobile IP uses IPIP heavily)
      |
      v
Today — IPIP still widely used in:
         Linux kernel (ipip.ko module)
         Kubernetes pod networking (Calico CNI)
         Mobile IP deployments
         ISP backbone tunnels
```

### RFC 2003 — The Core Standard

RFC 2003 defines the minimal rules:
1. The **outer IP header** carries the tunnel endpoint addresses.
2. The **inner IP packet** is placed verbatim as the outer IP payload.
3. The outer IP protocol field is set to **4**.
4. TTL, checksum, and fragmentation rules are specified.

The RFC is intentionally minimal. IPIP does NOT define:
- Encryption
- Authentication
- Key exchange
- Compression

For those, you add IPSec on top of IPIP, or use a different protocol (GRE+IPSec, WireGuard, etc.).

---

## 5. The IP Header — Deep Understanding

Before IPIP makes sense, you must master the IP header because IPIP stacks two
of them together.

### IPv4 Header Structure (20 bytes minimum)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |  Row 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |  Row 2
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |  Row 3
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |  Row 4
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |  Row 5
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |  Row 6 (optional)
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field-by-Field Explanation

```
+------------------+------+---+------------------------------------------------+
| Field            | Bits | # | Meaning                                        |
+------------------+------+---+------------------------------------------------+
| Version          |   4  | 4 | IP version: 4 for IPv4                         |
| IHL              |   4  | 4 | Internet Header Length in 32-bit words         |
|                  |      |   | Minimum = 5 (5 x 4 = 20 bytes, no options)     |
| Type of Service  |   8  | 1 | QoS/DSCP — priority hints for routers          |
| Total Length     |  16  | 2 | Total size of packet (header + payload) bytes  |
| Identification   |  16  | 2 | ID used to reassemble fragmented packets       |
| Flags            |   3  | - | Bit 0: Reserved. Bit 1: DF (Don't Fragment).   |
|                  |      |   | Bit 2: MF (More Fragments)                     |
| Fragment Offset  |  13  | - | Where this fragment fits in original packet    |
| Time to Live     |   8  | 1 | Hop count. Decremented by each router.         |
|                  |      |   | Packet dropped when TTL reaches 0.             |
| Protocol         |   8  | 1 | Next-level protocol (4=IPIP, 6=TCP, 17=UDP)    |
| Header Checksum  |  16  | 2 | Checksum of header only (not payload)          |
| Source Address   |  32  | 4 | Sender's IP address (4 bytes)                  |
| Destination Addr |  32  | 4 | Receiver's IP address (4 bytes)                |
| Options          | var  | - | Rarely used. Padding to 32-bit boundary.       |
+------------------+------+---+------------------------------------------------+
```

---

## 6. IPIP Packet Structure — Anatomy

### Full Packet Layout on the Wire

```
+=====================================================================+
|                    ETHERNET FRAME (Layer 2)                         |
|  +---------------------------------------------------------------+  |
|  | Eth Dst MAC | Eth Src MAC | EtherType=0x0800 |                |  |
|  +---------------------------------------------------------------+  |
|  |                  OUTER IP HEADER (Layer 3)                    |  |
|  |  Version=4 | IHL=5 | TOS | Total Length                       |  |
|  |  Identification | Flags | Fragment Offset                     |  |
|  |  TTL | Protocol=4 | Header Checksum                           |  |
|  |  Src=TunnelEntry_IP (e.g. 203.0.113.1)                        |  |
|  |  Dst=TunnelExit_IP  (e.g. 198.51.100.1)                       |  |
|  +---------------------------------------------------------------+  |
|  |                  INNER IP HEADER (original)                   |  |
|  |  Version=4 | IHL=5 | TOS | Total Length                       |  |
|  |  Identification | Flags | Fragment Offset                     |  |
|  |  TTL | Protocol=6 (TCP) | Header Checksum                     |  |
|  |  Src=10.0.0.1  (private sender)                               |  |
|  |  Dst=10.0.0.2  (private receiver)                             |  |
|  +---------------------------------------------------------------+  |
|  |                ORIGINAL PAYLOAD                               |  |
|  |  TCP Header + Application Data (HTTP, SSH, etc.)              |  |
|  +---------------------------------------------------------------+  |
+=====================================================================+
```

### Byte-Level Size Calculation

```
Ethernet Header    :  14 bytes
Outer IP Header    :  20 bytes   <-- added by IPIP encapsulation
Inner IP Header    :  20 bytes   <-- original packet header
TCP Header         :  20 bytes   (typical)
Application Data   :  N bytes

Total overhead added by IPIP = 20 bytes (outer IP header only)
```

### Visual Comparison: Normal vs IPIP Packet

```
NORMAL IP PACKET:
+----------------+-------------------+------------------+
| IP Header (20) | TCP Header (20)   | Application Data |
| Src: 10.0.0.1  |                   |                  |
| Dst: 10.0.0.2  |                   |                  |
+----------------+-------------------+------------------+

IPIP ENCAPSULATED PACKET:
+------------------+----------------+-------------------+------------------+
| Outer IP Hdr(20) | Inner IP Hdr   | TCP Header (20)   | Application Data |
| Src: 203.0.113.1 | Src: 10.0.0.1  |                   |                  |
| Dst: 198.51.100.1| Dst: 10.0.0.2  |                   |                  |
| Proto: 4 (IPIP)  | Proto: 6 (TCP) |                   |                  |
+------------------+----------------+-------------------+------------------+
 ^^^^^^^^^^^^^^^^^^ added by tunnel  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                     original packet (untouched)
```

---

## 7. Encapsulation — Step-by-Step

### What Is Encapsulation?

**Encapsulation** (from "capsule") means to enclose something within a container.
In networking, it means wrapping one packet's complete bytes inside another packet's
payload area.

The machine that performs encapsulation is called the **tunnel ingress** (entry point).

### Step-by-Step Encapsulation Process

```
STEP 1: Original Packet Arrives
===================================

  Application on Host A sends data to 10.0.0.2
  Kernel creates an IP packet:

  +-----------------------------+
  | IP Header                   |
  | Src: 10.0.0.1               |
  | Dst: 10.0.0.2               |
  | Proto: 6 (TCP)              |
  | TTL: 64                     |
  | Total Length: 60            |
  +-----------------------------+
  | TCP + Application Data      |
  +-----------------------------+


STEP 2: Routing Decision — Use Tunnel
=========================================

  Routing table says:
  "To reach 10.0.0.2, send via tunnel interface ipip0"
  
  The IPIP module intercepts the packet.
  It knows the tunnel endpoint: remote = 198.51.100.1


STEP 3: Create Outer IP Header
========================================

  New outer IP header is constructed:

  +-----------------------------+
  | Outer IP Header             |
  | Src: 203.0.113.1            |  <-- local tunnel endpoint IP
  | Dst: 198.51.100.1           |  <-- remote tunnel endpoint IP
  | Proto: 4  (IPIP signal!)    |  <-- critical: tells receiver this is IPIP
  | TTL: 64                     |  <-- independent TTL for the tunnel
  | Total Length: 60 + 20 = 80  |  <-- inner packet + outer header
  +-----------------------------+


STEP 4: Concatenate Headers + Payload
===========================================

  [Outer IP Header (20)] + [Inner IP Header (20)] + [TCP + Data (40)]
         |                        |                       |
  tunnel metadata           original packet           original data
  (public addresses)        (private addresses)


STEP 5: Send to Physical Network
=====================================

  The concatenated packet is sent to the local gateway.
  Routers on the internet see ONLY the outer IP header.
  They route based on Dst: 198.51.100.1 (public IP).
  They are completely unaware of the inner packet.
```

### Encapsulation Algorithm (Pseudocode)

```
function encapsulate(inner_packet, tunnel_src_ip, tunnel_dst_ip):
    
    // Step 1: Compute new total length
    outer_total_length = len(inner_packet) + 20  // 20 = outer IP header size
    
    // Step 2: Build outer IP header
    outer_header = IPHeader {
        version        = 4,
        ihl            = 5,        // 5 * 4 = 20 bytes, no options
        tos            = 0,        // or copy from inner header
        total_length   = outer_total_length,
        identification = generate_id(),
        flags          = 0,
        frag_offset    = 0,
        ttl            = 64,       // independent TTL
        protocol       = 4,        // 4 = IPIP protocol number
        checksum       = 0,        // compute after filling fields
        src_addr       = tunnel_src_ip,
        dst_addr       = tunnel_dst_ip,
    }
    
    // Step 3: Compute checksum over outer header
    outer_header.checksum = compute_ip_checksum(outer_header)
    
    // Step 4: Concatenate
    encapsulated_packet = outer_header + inner_packet
    
    // Step 5: Transmit via physical interface
    send_to_network(encapsulated_packet)
```

---

## 8. Decapsulation — Step-by-Step

### What Is Decapsulation?

**Decapsulation** is the reverse: stripping the outer wrapper to reveal the inner
packet. The machine performing this is the **tunnel egress** (exit point).

### Step-by-Step Decapsulation Process

```
STEP 1: Outer Packet Arrives at Tunnel Endpoint
=================================================

  Network interface receives packet:

  +-----------------------------+
  | Outer IP Header             |
  | Dst: 198.51.100.1  (ME!)   |  <-- matches local IP, so it's for me
  | Proto: 4           (IPIP!) |  <-- tells kernel: inner content is IP
  +-----------------------------+
  | [Inner IP Header + Data]    |
  +-----------------------------+


STEP 2: Kernel Checks Protocol Field
======================================

  OS reads Protocol field of outer header = 4
  OS dispatches packet to IPIP handler module.
  
  Protocol demultiplexing table:
  +----------+---------------------------+
  | Proto=1  | --> ICMP handler          |
  | Proto=4  | --> IPIP handler  (HERE!) |
  | Proto=6  | --> TCP handler           |
  | Proto=17 | --> UDP handler           |
  +----------+---------------------------+


STEP 3: Validate Outer Header
================================

  - Is this packet addressed to a valid tunnel endpoint?
  - Is the source IP from a trusted tunnel peer?  (optional check)
  - Is the packet not malformed?


STEP 4: Strip Outer IP Header
================================

  Remove the first 20 bytes (outer IP header).
  What remains is the complete original inner IP packet:

  +-----------------------------+
  | Inner IP Header             |
  | Src: 10.0.0.1               |
  | Dst: 10.0.0.2               |
  | Proto: 6 (TCP)              |
  +-----------------------------+
  | TCP + Application Data      |
  +-----------------------------+


STEP 5: Re-inject into Network Stack
======================================

  The inner packet is injected into the local routing/forwarding engine
  as if it arrived on a normal interface.

  Routing table consulted:
  "10.0.0.2 is reachable via eth0" --> forwarded to LAN.


STEP 6: Inner Packet Delivered
=================================

  Host at 10.0.0.2 receives a perfectly normal TCP/IP packet.
  It has no knowledge that tunneling occurred.
```

### Decapsulation Algorithm (Pseudocode)

```
function decapsulate(received_packet):

    // Step 1: Parse outer IP header
    outer_header = parse_ip_header(received_packet[0:20])
    
    // Step 2: Verify it's IPIP
    if outer_header.protocol != 4:
        return ERROR("Not an IPIP packet")
    
    // Step 3: Optional source validation
    if outer_header.src_addr not in trusted_peers:
        return ERROR("Untrusted tunnel source")
    
    // Step 4: Strip outer header
    inner_packet = received_packet[20:]    // skip 20 bytes outer header
    
    // Step 5: Validate inner IP header
    inner_header = parse_ip_header(inner_packet[0:20])
    if inner_header.version != 4:
        return ERROR("Invalid inner IP version")
    
    // Step 6: Re-inject inner packet into routing
    inject_into_ip_stack(inner_packet)
```

---

## 9. TTL Handling

### What Is TTL?

**TTL (Time To Live)** is a counter in every IP header. Each router that forwards
a packet decrements TTL by 1. When TTL reaches 0, the router drops the packet
and sends an ICMP "Time Exceeded" message back. This prevents infinite routing loops.

### TTL in IPIP — Two Independent TTLs

IPIP has TWO IP headers, and they have two INDEPENDENT TTL values:

```
                 OUTER IP HEADER                INNER IP HEADER
                 TTL=64 (tunnel hop count)      TTL=64 (end-to-end hop count)

  [HostA]  ---  [TunnelEntry]  ===tunnel===  [TunnelExit]  ---  [HostB]
                     ^                             ^
                     | outer TTL decremented       |
                     | by each internet router     |
                     |                             |
                     | when tunnel exits here,     |
                     | inner TTL is decremented    |
                     | as it crosses internal hops |
```

### TTL Decrement Path

```
Step 1: HostA sends inner packet with TTL=64

Step 2: TunnelEntry encapsulates, adds outer header with TTL=64
        Both TTLs are currently 64.

Step 3: Outer packet traverses 5 internet routers:
        Each router decrements OUTER TTL.
        Outer TTL: 64 -> 63 -> 62 -> 61 -> 60 -> 59
        Inner TTL: still 64 (nobody touches it during transit)

Step 4: TunnelExit receives packet, decapsulates:
        Outer header discarded (outer TTL irrelevant now)
        Inner packet has TTL=64

Step 5: Inner packet forwarded through internal network (3 hops):
        Inner TTL: 64 -> 63 -> 62 -> 61
        Delivered to HostB.

Final TTL seen by HostB application = 61
```

### RFC 2003 TTL Recommendations

RFC 2003 allows two modes for outer TTL:

```
MODE 1 — Uniform model (RFC recommendation):
  outer_ttl = inner_ttl
  Outer and inner start with same TTL.
  Traceroute sees all hops (tunnel hops + end hops).

MODE 2 — Pipe model:
  outer_ttl = fixed value (e.g., 255)
  Traceroute cannot see inside the tunnel (tunnel is opaque).
  Used when tunnel internals should be hidden.
```

---

## 10. MTU and Fragmentation

### What Is MTU?

**MTU (Maximum Transmission Unit)** is the largest packet size (in bytes) that
a network link can carry without splitting (fragmenting) the packet.

```
Ethernet standard MTU = 1500 bytes
  (includes IP header + payload, does NOT include Ethernet frame header)
```

### The IPIP MTU Problem

IPIP adds **20 bytes** of outer IP header overhead. This reduces the effective
MTU for inner packets:

```
Physical link MTU   = 1500 bytes
IPIP outer header   =   20 bytes overhead
                    --------
Inner packet MTU    = 1480 bytes

So inner IP packets must be at most 1480 bytes, or they will be fragmented.
```

### Fragmentation Decision Tree

```
                    [Inner packet arrives at tunnel entry]
                                |
                        [Size > 1480?]
                       /              \
                     YES               NO
                      |                |
           [Inner DF flag set?]    [Encapsulate and send]
           /              \
         YES               NO
          |                 |
  [Drop packet +       [Fragment inner packet]
   Send ICMP            [Encapsulate each fragment]
   Frag Needed          [Send fragments]
   back to sender]
```

### PMTUD — Path MTU Discovery

**PMTUD (Path MTU Discovery)** is a mechanism where:
1. Sender sets DF (Don't Fragment) flag.
2. If a router needs to fragment but DF is set, it drops and sends ICMP.
3. Sender learns the MTU and reduces packet size.

IPIP can break PMTUD because:
- The ICMP message references the outer packet.
- The inner packet sender doesn't see the ICMP.
- Solution: **Tunnel endpoints must translate ICMP messages** or **clamp TCP MSS**.

### TCP MSS Clamping

**MSS (Maximum Segment Size)** is negotiated during TCP handshake. By setting it
to account for IPIP overhead:

```
TCP MSS = Physical MTU - IP header - TCP header - IPIP overhead
        = 1500         - 20        - 20          - 20
        = 1440 bytes

Configure this on the tunnel interface to prevent fragmentation issues.
```

---

## 11. Checksum Behavior

### IP Header Checksum Rules

IPv4 headers include a **header checksum** (not payload checksum). The checksum
covers only the IP header fields.

### IPIP Checksum — TWO Checksums

```
+------------------+------------------+-----------------------------+
| Outer IP Header  | Inner IP Header  |  Payload (TCP/UDP/etc.)     |
| checksum = XYZ   | checksum = ABC   |                             |
+------------------+------------------+-----------------------------+
        ^                  ^
        |                  |
  Computed when      Already computed
  outer header       when original
  is built           packet was created.
  (new each time)    NOT recomputed by IPIP.
```

**Key insight:** IPIP does NOT recompute the inner IP checksum. The inner packet
is treated as an opaque blob of bytes. Only the outer IP header gets a newly
computed checksum.

When the outer header is stripped at the tunnel exit:
- The inner checksum is verified by the receiving host, not the tunnel exit.
- The inner checksum remains valid because the inner packet bytes were not modified.

---

## 12. Protocol Number and Identification

### IANA Protocol Numbers (Relevant to Tunneling)

```
+--------+----------------------+---------------------------------------+
| Number | Protocol             | RFC / Standard                        |
+--------+----------------------+---------------------------------------+
|   0    | HOPOPT               | IPv6 Hop-by-Hop Option                |
|   1    | ICMP                 | RFC 792 — Ping, unreachable msgs      |
|   2    | IGMP                 | Multicast group management            |
|   4    | IP-in-IP (IPIP)      | RFC 2003 — THIS IS OUR PROTOCOL       |
|   6    | TCP                  | RFC 793 — Reliable stream             |
|  17    | UDP                  | RFC 768 — Unreliable datagram         |
|  41    | IPv6                 | RFC 2473 — IPv6 tunneled in IPv4      |
|  47    | GRE                  | RFC 2784 — Generic routing encap      |
|  50    | ESP                  | RFC 4303 — IPSec Encap Security Pay.  |
|  51    | AH                   | RFC 4302 — IPSec Auth Header          |
|  94    | IPIP (alternate)     | Sometimes used for IPIP as well       |
| 115    | L2TP                 | RFC 2661 — Layer 2 Tunneling          |
+--------+----------------------+---------------------------------------+
```

**Protocol Number 4 is the definitive IPIP identifier.** When a router or
firewall sees Protocol=4 in an IP header, it knows the payload is another IP packet.

---

## 13. IPIP vs Other Tunneling Protocols

### Comparison Table

```
+----------+---------+-------+----------+-----------+----------+-------------+
| Protocol | Overhead| Proto | Encryptd | Auth      | Multi-   | Complexity  |
|          | (bytes) | Num   |          |           | cast     |             |
+----------+---------+-------+----------+-----------+----------+-------------+
| IPIP     |   20    |   4   |   No     |   No      |  No      | Very Low    |
| 6in4     |   20    |  41   |   No     |   No      |  No      | Very Low    |
| GRE      |   24+   |  47   |   No     |   No      |  Yes     | Low         |
| GRE+IPSec|   24+   |  47   |   Yes    |   Yes     |  Yes     | Medium      |
| VXLAN    |   50    |  17   |   No     |   No      |  Yes     | Medium      |
| WireGuard|   60+   |  17   |   Yes    |   Yes     |  No      | Low-Medium  |
| OpenVPN  |   100+  |  17   |   Yes    |   Yes     |  Yes     | High        |
| IPSec/AH |   20+   |  51   |   No     |   Yes     |  No      | High        |
| IPSec/ESP|   36+   |  50   |   Yes    |   Yes     |  No      | High        |
| L2TP/IPSec  | 50+  |varied |   Yes    |   Yes     |  No      | High        |
+----------+---------+-------+----------+-----------+----------+-------------+
```

### IPIP vs GRE

```
IPIP:
  [Outer IP] [Inner IP] [Payload]
  Simple. Fixed overhead. Only carries IP.

GRE:
  [Outer IP] [GRE Header (4-16 bytes)] [Inner Protocol] [Payload]
  More flexible. Can carry any Layer 3 protocol (IP, IPX, MPLS, etc.)
  Supports optional sequence numbers, keys, checksums.
  GRE Header adds 4 bytes minimum.

Choose IPIP when:  pure simplicity, maximum performance, IPv4-only
Choose GRE when:   need to carry non-IP protocols, need key fields
```

### IPIP vs VXLAN

```
VXLAN (Virtual eXtensible LAN):
  [Outer IP] [UDP] [VXLAN Header] [Inner Ethernet Frame] [Inner IP] [Payload]
  Operates at Layer 2 (carries Ethernet frames, not just IP).
  Used in cloud datacenters (Kubernetes, OpenStack).
  Much more overhead.
  Supports multicast for MAC learning.

IPIP: Layer 3 only, minimal overhead, no Layer 2 capability.
VXLAN: Layer 2 + 3, high overhead, datacenter scale.
```

### Decision Tree: Which Tunnel to Use?

```
                    [Need a tunnel?]
                          |
               [Need encryption?]
              /                    \
            YES                    NO
             |                      |
    [Need simplicity?]         [Need to carry non-IP?]
    /              \           /                \
  YES              NO        YES                NO
   |                |         |                  |
[WireGuard]  [OpenVPN/    [GRE]              [IPIP]
              IPSec]        |                  <-- simplest,
                     [Need encryption?]           fastest
                     /              \
                   YES              NO
                    |                |
               [GRE+IPSec]         [GRE]
```

---

## 14. Use Cases and Real-World Applications

### Use Case 1: Connecting Two Private Networks Over the Internet

```
Network A: 10.0.0.0/24          Network B: 192.168.1.0/24
GatewayA: 10.0.0.1 / 203.0.113.1   GatewayB: 192.168.1.1 / 198.51.100.1

  [10.0.0.5] --> [GatewayA] ===IPIP tunnel=== [GatewayB] --> [192.168.1.5]
               encapsulates                 decapsulates
               inner 10.x/192.x            extracts inner
               inside outer 203.x/198.x    packet, forwards

Traffic flow:
  HostA (10.0.0.5)     sends to     HostB (192.168.1.5)
  GatewayA sees:       inner dst = 192.168.1.5, use tunnel
  GatewayA builds:     outer dst = 198.51.100.1 (GatewayB's public IP)
  Internet sees only:  outer src=203.0.113.1, outer dst=198.51.100.1
  GatewayB receives:   strips outer, sees inner dst=192.168.1.5
  GatewayB routes:     inner packet to local LAN
```

### Use Case 2: Mobile IP (RFC 3344)

Mobile IP uses IPIP to keep a mobile device's IP address stable while it moves
across networks.

```
Concepts:
  Home Agent (HA):     server at home network, knows mobile's location
  Mobile Node (MN):    device (phone/laptop) that moves around
  Care-of Address:     temporary IP at current location

Flow when mobile is away from home:

  [Correspondent] --sends to--> [MN home addr 10.1.1.5]
        |
        v
  [Home Agent] sees packet for 10.1.1.5
        |
        | IPIP encapsulates:
        |   outer dst = MN's care-of addr (current IP: 203.0.113.50)
        v
  [Foreign Network] receives IPIP packet
        |
        v
  [Mobile Node] decapsulates, sees original packet destined for 10.1.1.5
  MN processes it as if it received it at home.
```

### Use Case 3: Kubernetes / Calico CNI Pod Networking

Calico (a popular Kubernetes networking plugin) uses IPIP tunnels to route
pod traffic across nodes when nodes are on different subnets.

```
Node1 (192.168.1.10):     Pod subnet 10.244.1.0/24
Node2 (192.168.1.20):     Pod subnet 10.244.2.0/24

Pod A (10.244.1.5) --> Pod B (10.244.2.7):

  1. Pod A sends to 10.244.2.7
  2. Node1's kernel: route says send via ipip0 tunnel to Node2
  3. Node1 encapsulates:
       Outer Src: 192.168.1.10
       Outer Dst: 192.168.1.20
       Inner Src: 10.244.1.5
       Inner Dst: 10.244.2.7
  4. Physical network carries outer packet (nodes are on same LAN)
  5. Node2 decapsulates:
       Outer stripped, sees inner dst=10.244.2.7
       Forwards to Pod B's veth interface

Node1 ======IPIP====== Node2
             |
     single physical hop
     (same datacenter LAN)
```

### Use Case 4: ISP and Carrier Networks

```
ISP backbone may use IPIP to:
- Route customer traffic through specific paths
- Implement traffic engineering
- Support MPLS-like behavior without MPLS hardware
- Connect data centers across geographically separate locations
```

---

## 15. IPIP in the Linux Kernel

### Kernel Module: ipip.ko

Linux implements IPIP through a kernel module:

```bash
# Load the IPIP kernel module
modprobe ipip

# View loaded modules
lsmod | grep ipip

# The module registers protocol handler for proto=4
# in the ip_proto_table kernel structure
```

### Creating an IPIP Tunnel Interface

```bash
# Method 1: Using 'ip' command (iproute2)

# Create tunnel interface named ipip0
ip tunnel add ipip0 mode ipip \
    local 203.0.113.1 \          # our public IP (tunnel src)
    remote 198.51.100.1 \        # peer's public IP (tunnel dst)
    ttl 64                       # outer TTL

# Assign IP address to the tunnel interface (inner network)
ip addr add 10.0.0.1/30 dev ipip0

# Bring the interface up
ip link set ipip0 up

# Add route through the tunnel
ip route add 192.168.1.0/24 dev ipip0

# Method 2: Using legacy 'iptunnel' command
iptunnel add ipip0 mode ipip remote 198.51.100.1 local 203.0.113.1
```

### Kernel Data Structures (Conceptual)

```
Linux Kernel Network Stack (simplified):

  Packet arrives on eth0
        |
        v
  ip_rcv()          <-- main IP receive function
        |
        v
  ip_local_deliver()  <-- packet is for this machine
        |
        v
  ip_local_deliver_finish()
        |
        v
  [Read protocol field from IP header]
        |
      proto=4?
        |
        v
  ipip_rcv()        <-- IPIP handler registered for proto 4
        |
        v
  [Validate outer header]
  [Strip 20 bytes]
  [Find tunnel struct for src/dst pair]
        |
        v
  netif_rx(inner_skb)  <-- re-inject inner packet
        |
        v
  ip_rcv() again    <-- inner packet now processed normally
```

### Key Kernel Files (for Reference)

```
net/ipv4/ipip.c         -- Main IPIP implementation
net/ipv4/ip_tunnel.c    -- Generic IP tunnel base code
include/net/ipip.h      -- IPIP-specific structures
include/net/ip_tunnels.h -- Shared tunnel structures

Key structures:
  struct ip_tunnel       -- Represents one IPIP tunnel
  struct ip_tunnel_net   -- Per-netns IPIP state
  struct iphdr           -- IPv4 header structure (linux/ip.h)
```

---

## 16. ASCII Network Diagrams — Real Protocol Flow

### Complete End-to-End Packet Journey

```
  SENDER SIDE                    INTERNET                    RECEIVER SIDE
  ===========                   =========                   ==============

  Application
  generates data
       |
       v
  TCP Layer
  adds TCP header
       |
       v                                                    Application
  IP Layer                                                      ^
  adds inner IP hdr         +---------+    +---------+          |
  Src=10.0.0.1              | Router1 |    | Router2 |      TCP Layer
  Dst=10.0.0.2              |         |    |         |          ^
       |                    +---------+    +---------+          |
       v                         |              |           IP Layer
  IPIP Module             +------+------+  +---+--------+       ^
  adds outer IP hdr       |             |  |            |       |
  Src=203.0.113.1         | Route based |  | Route based|   IPIP Module
  Dst=198.51.100.1        | on outer IP |  | on outer IP|   strips outer
  Proto=4                 |             |  |            |   re-injects
       |                  +------+------+  +---+--------+   inner packet
       v                         |              |               ^
  eth0 ==========================|==============|===============
  Physical Network               |              |
       |                         |              |
  [FRAME ON THE WIRE]:           |              |
  +--------+--------+---------+--+--+---------+-+--+------- --+
  | EthHdr | OuterIP| InnerIP |TCP  |AppData  |               |
  | 14B    | 20B    | 20B     |20B  | var     |               |
  +--------+--------+---------+-----+---------+---------------+
                                                               |
                                                          GatewayB's eth0
                                                               |
                                                          IPIP decap
                                                               |
                                                     Forwards inner packet
                                                        to 10.0.0.2
```

### Network Topology: Site-to-Site IPIP VPN

```
  SITE A                          INTERNET                    SITE B
  ======                          ========                    ======

  +----------+                  +---------+                +-------- --+
  | 10.0.0.5 |                  |         |                |192.168.1.5|
  +----+-----+                  | Router  |                +-----+--- -+
       |                        |  Cloud  |                      |
       | LAN                    +---------+                      | LAN
       |                             |                           |
  +----+--------+                    |                  +--------+---+
  |  GatewayA   |<---IPIP Tunnel---->|<---IPIP Tunnel-->| GatewayB   |
  | 10.0.0.1    |  203.0.113.1   198.51.100.1           |192.168.1.1 |
  | 203.0.113.1 |                                       |198.51.100.1|
  +-------------+                                       +------------+
  
  Routing Tables:
  GatewayA:  192.168.1.0/24 via ipip0 (tunnel to GatewayB)
  GatewayB:  10.0.0.0/24 via ipip0 (tunnel to GatewayA)
  
  Tunnel Config:
  GatewayA:  local=203.0.113.1  remote=198.51.100.1
  GatewayB:  local=198.51.100.1 remote=203.0.113.1
```

### Packet Transformation at Each Hop

```
  HOP 1: Inside Site A (raw inner packet)
  +-----------+-------+------------------+
  | Inner IP  |  TCP  |   App Data       |
  | 10.0.0.5  | dport |   "Hello!"       |
  |->192.168.1.5      |                  |
  +-----------+-------+------------------+

  HOP 2: After GatewayA encapsulates (IPIP packet)
  +-----------+-----------+-------+------------------+
  | Outer IP  | Inner IP  |  TCP  |   App Data       |
  |203.0.113.1| 10.0.0.5  | dport |   "Hello!"       |
  |->198.51.100.1 |->192.168.1.5  |                  |
  | Proto=4   | Proto=6   |       |                  |
  +-----------+-----------+-------+------------------+
   [Routers only see this part]

  HOP 3: After GatewayB decapsulates (back to inner packet)
  +-----------+-------+------------------+
  | Inner IP  |  TCP  |   App Data       |
  | 10.0.0.5  | dport |   "Hello!"       |
  |->192.168.1.5      |   "Hello!"       |
  +-----------+-------+------------------+

  HOP 4: Inside Site B (delivered to destination)
  Application receives: "Hello!"
```

---

## 17. Decision Trees and Flowcharts

### Packet Processing Flowchart at Tunnel Entry

```
  [Packet arrives at routing decision point]
                    |
                    v
         [Destination is local?]
        /                       \
      YES                       NO
       |                         |
  [Deliver locally]    [Lookup in routing table]
                                  |
                      [Route via tunnel interface?]
                       /                         \
                     YES                         NO
                      |                           |
              [Get tunnel config]         [Forward normally
              [src, dst, mode]             via physical interface]
                      |
                      v
             [Inner packet > MTU?]
            /                     \
          YES                     NO
           |                       |
  [Inner DF flag set?]    [Build outer IP header]
  /              \         [Src = tunnel local IP]
YES              NO        [Dst = tunnel remote IP]
 |                |         [Proto = 4]
[Drop +       [Fragment    [TTL = configured value]
 ICMP          inner           |
 back]         packet]    [Compute outer checksum]
                  |             |
              [Encapsulate      v
               each fragment] [Transmit on physical interface]
                  |
              [Transmit each
               encapsulated
               fragment]
```

### Packet Processing Flowchart at Tunnel Exit

```
  [Packet arrives on physical interface]
                    |
                    v
         [Parse outer IP header]
                    |
                    v
         [Dst == my IP address?]
        /                        \
      YES                        NO
       |                          |
  [Read Protocol field]      [Forward/drop packet]
       |
  [Proto == 4?]
  /           \
YES            NO
 |              |
[IPIP!]    [Handle normally:
            TCP/UDP/ICMP/etc.]
 |
 v
[Is source IP a trusted tunnel peer?]
 /                  \
YES (or any)        NO (if strict mode)
 |                   |
 |               [Drop packet + log]
 v
[Strip outer 20 bytes]
 |
 v
[Validate inner IP header]
[Check version, length, checksum]
 |
 v
[Inner packet valid?]
/               \
YES             NO
 |               |
[Re-inject      [Drop + log error]
 inner packet
 into IP stack]
 |
 v
[Inner packet routed normally to destination]
```

### Tunnel Configuration Decision Tree

```
  [Setting up IPIP tunnel]
              |
   [Static or dynamic endpoints?]
   /                            \
STATIC                        DYNAMIC
(fixed IPs on both sides)     (one side has changing IP)
   |                               |
[Use simple IPIP]             [Use Mobile IP
[ip tunnel add mode ipip]      or dynamic tunnel
[specify local + remote]       update mechanism]
   |
   v
[MTU adjustment needed?]
/                       \
YES                     NO (same LAN, jumbo frames)
 |                       |
[Set MTU on               [Default MTU is fine]
 tunnel interface:
 ip link set ipip0 mtu 1480]
 |
 v
[TCP MSS clamping needed?]
YES (if hosts behind tunnel do TCP)
 |
[iptables -t mangle -A FORWARD -p tcp
 --tcp-flags SYN,RST SYN
 -j TCPMSS --set-mss 1440]
```

---

## 18. C Implementation — Raw Sockets

### Concept: What Are Raw Sockets?

**Raw sockets** allow a program to directly construct and read IP packets,
bypassing the OS TCP/UDP layers. This is how we build IPIP in userspace for
learning purposes.

- `SOCK_RAW` — socket type for raw IP access
- `IPPROTO_RAW` — tells kernel we will build our own IP headers
- `IP_HDRINCL` — socket option: we include our own IP header

### C Header Structures

The `linux/ip.h` header defines the `iphdr` structure that maps exactly to the
IP header bytes on the wire.

### Full C Implementation

```c
/*
 * IPIP Tunnel Implementation in C
 * Demonstrates encapsulation and decapsulation using raw sockets.
 *
 * RFC 2003 — IP Encapsulation within IP
 *
 * Compile:
 *   gcc -o ipip_tunnel ipip_tunnel.c -Wall -Wextra
 *
 * Run (requires root):
 *   sudo ./ipip_tunnel encap <inner_src> <inner_dst> <outer_src> <outer_dst>
 *   sudo ./ipip_tunnel decap
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netinet/ip.h>      /* struct iphdr */
#include <arpa/inet.h>
#include <linux/if_packet.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <signal.h>

/* ============================================================
 * CONSTANTS
 * ============================================================ */
#define IPIP_PROTO          4       /* IP protocol number for IPIP */
#define IP_VERSION          4       /* IPv4 */
#define IP_HEADER_LEN       5       /* 5 * 4 = 20 bytes, no options */
#define DEFAULT_TTL         64      /* Standard initial TTL */
#define MAX_PACKET_SIZE     65535   /* Maximum IP packet size */
#define TUNNEL_MTU          1480    /* 1500 - 20 bytes IPIP overhead */

/* ============================================================
 * UTILITY: PRINT IP HEADER FIELDS
 * This helps us understand what's in each header.
 * ============================================================ */
void print_ip_header(const struct iphdr *hdr, const char *label) {
    char src_str[INET_ADDRSTRLEN];
    char dst_str[INET_ADDRSTRLEN];

    struct in_addr src_addr = { .s_addr = hdr->saddr };
    struct in_addr dst_addr = { .s_addr = hdr->daddr };

    inet_ntop(AF_INET, &src_addr, src_str, sizeof(src_str));
    inet_ntop(AF_INET, &dst_addr, dst_str, sizeof(dst_str));

    printf("  [%s IP Header]\n", label);
    printf("    Version   : %d\n",    hdr->version);
    printf("    IHL       : %d (%d bytes)\n", hdr->ihl, hdr->ihl * 4);
    printf("    TOS       : 0x%02x\n", hdr->tos);
    printf("    Tot Len   : %d\n",    ntohs(hdr->tot_len));
    printf("    ID        : 0x%04x\n", ntohs(hdr->id));
    printf("    Frag Off  : %d\n",    ntohs(hdr->frag_off) & 0x1FFF);
    printf("    TTL       : %d\n",    hdr->ttl);
    printf("    Protocol  : %d (%s)\n", hdr->protocol,
           hdr->protocol == 4  ? "IPIP" :
           hdr->protocol == 6  ? "TCP"  :
           hdr->protocol == 17 ? "UDP"  :
           hdr->protocol == 1  ? "ICMP" : "Unknown");
    printf("    Checksum  : 0x%04x\n", ntohs(hdr->check));
    printf("    Src       : %s\n",    src_str);
    printf("    Dst       : %s\n",    dst_str);
    printf("\n");
}

/* ============================================================
 * IP HEADER CHECKSUM COMPUTATION
 *
 * Algorithm: One's complement sum of all 16-bit words in header.
 * Defined in RFC 791.
 *
 * One's complement: invert all bits (NOT operation in binary).
 * The checksum ensures header integrity.
 * ============================================================ */
uint16_t compute_ip_checksum(const void *data, size_t length) {
    const uint16_t *ptr = (const uint16_t *)data;
    uint32_t sum = 0;

    /* Sum all 16-bit words */
    while (length > 1) {
        sum += *ptr++;
        length -= 2;
    }

    /* Handle odd byte (if header length is odd — rare with IP) */
    if (length == 1) {
        sum += *(const uint8_t *)ptr;
    }

    /* Fold 32-bit sum into 16 bits by adding carry bits */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    /* One's complement: invert all bits */
    return (uint16_t)(~sum);
}

/* ============================================================
 * BUILD OUTER IP HEADER
 *
 * This is the core of IPIP encapsulation:
 * we craft a new IP header that wraps the entire inner packet.
 *
 * Parameters:
 *   out_hdr     : pointer to buffer where header will be written
 *   src_ip      : tunnel source (our public IP, in network byte order)
 *   dst_ip      : tunnel dest  (peer public IP, in network byte order)
 *   inner_len   : length of the inner packet (bytes)
 *   ttl         : outer packet TTL
 * ============================================================ */
void build_outer_header(struct iphdr *out_hdr,
                        uint32_t src_ip,
                        uint32_t dst_ip,
                        uint16_t inner_len,
                        uint8_t  ttl) {
    memset(out_hdr, 0, sizeof(struct iphdr));

    out_hdr->version  = IP_VERSION;            /* IPv4 */
    out_hdr->ihl      = IP_HEADER_LEN;         /* 20 bytes, no options */
    out_hdr->tos      = 0;                     /* Best effort */
    out_hdr->tot_len  = htons(sizeof(struct iphdr) + inner_len);
                                               /* outer header + inner packet */
    out_hdr->id       = htons((uint16_t)rand()); /* Random ID */
    out_hdr->frag_off = htons(IP_DF);          /* Don't Fragment */
    out_hdr->ttl      = ttl;
    out_hdr->protocol = IPIP_PROTO;            /* CRITICAL: 4 = IPIP */
    out_hdr->check    = 0;                     /* Zero before checksum */
    out_hdr->saddr    = src_ip;
    out_hdr->daddr    = dst_ip;

    /* Compute checksum over the outer header only */
    out_hdr->check = compute_ip_checksum(out_hdr, sizeof(struct iphdr));
}

/* ============================================================
 * ENCAPSULATE: WRAP INNER PACKET WITH OUTER IP HEADER
 *
 * Returns length of the encapsulated packet, or -1 on error.
 *
 * encap_buf   : output buffer (must be >= inner_len + 20)
 * inner_pkt   : the complete inner IP packet (header + payload)
 * inner_len   : length of inner_pkt
 * outer_src   : tunnel entry IP (our public IP, dotted-decimal string)
 * outer_dst   : tunnel exit IP  (peer public IP, dotted-decimal string)
 * ============================================================ */
ssize_t ipip_encapsulate(uint8_t *encap_buf,
                         const uint8_t *inner_pkt,
                         size_t inner_len,
                         const char *outer_src,
                         const char *outer_dst) {
    struct iphdr *outer_hdr = (struct iphdr *)encap_buf;
    uint32_t src_ip, dst_ip;

    /* Validate inner packet minimum size */
    if (inner_len < sizeof(struct iphdr)) {
        fprintf(stderr, "Error: inner packet too small\n");
        return -1;
    }

    /* Check MTU constraint: inner packet + outer header must fit */
    if (inner_len + sizeof(struct iphdr) > TUNNEL_MTU + sizeof(struct iphdr)) {
        fprintf(stderr, "Warning: packet may need fragmentation "
                "(inner_len=%zu, tunnel MTU=%d)\n", inner_len, TUNNEL_MTU);
    }

    /* Convert IP addresses from string to network byte order */
    if (inet_pton(AF_INET, outer_src, &src_ip) != 1) {
        fprintf(stderr, "Error: invalid outer src IP: %s\n", outer_src);
        return -1;
    }
    if (inet_pton(AF_INET, outer_dst, &dst_ip) != 1) {
        fprintf(stderr, "Error: invalid outer dst IP: %s\n", outer_dst);
        return -1;
    }

    /* Build the outer IP header (first 20 bytes of encap_buf) */
    build_outer_header(outer_hdr, src_ip, dst_ip,
                       (uint16_t)inner_len, DEFAULT_TTL);

    /* Copy inner packet immediately after outer header */
    memcpy(encap_buf + sizeof(struct iphdr), inner_pkt, inner_len);

    printf("=== ENCAPSULATION ===\n");
    print_ip_header(outer_hdr, "Outer");
    print_ip_header((struct iphdr *)(inner_pkt), "Inner");

    return (ssize_t)(sizeof(struct iphdr) + inner_len);
}

/* ============================================================
 * DECAPSULATE: STRIP OUTER HEADER, RECOVER INNER PACKET
 *
 * Returns length of inner packet on success, -1 on error.
 *
 * inner_buf   : output buffer for the recovered inner packet
 * recv_pkt    : received raw packet bytes
 * recv_len    : length of recv_pkt
 * ============================================================ */
ssize_t ipip_decapsulate(uint8_t *inner_buf,
                         const uint8_t *recv_pkt,
                         size_t recv_len) {
    const struct iphdr *outer_hdr = (const struct iphdr *)recv_pkt;
    size_t outer_hdr_len;
    size_t inner_len;

    /* Minimum size check */
    if (recv_len < sizeof(struct iphdr) * 2) {
        fprintf(stderr, "Error: packet too small for IPIP\n");
        return -1;
    }

    /* Verify this is an IPIP packet */
    if (outer_hdr->protocol != IPIP_PROTO) {
        fprintf(stderr, "Error: not an IPIP packet (proto=%d)\n",
                outer_hdr->protocol);
        return -1;
    }

    /* IHL field is in 32-bit words. Multiply by 4 to get bytes. */
    outer_hdr_len = (size_t)(outer_hdr->ihl) * 4;

    if (outer_hdr_len < 20 || outer_hdr_len > recv_len) {
        fprintf(stderr, "Error: invalid outer IHL=%zu\n", outer_hdr_len);
        return -1;
    }

    /* Inner packet starts right after outer header */
    inner_len = recv_len - outer_hdr_len;
    const uint8_t *inner_start = recv_pkt + outer_hdr_len;

    /* Validate inner IP header */
    const struct iphdr *inner_hdr = (const struct iphdr *)inner_start;
    if (inner_hdr->version != 4) {
        fprintf(stderr, "Error: inner packet is not IPv4 (version=%d)\n",
                inner_hdr->version);
        return -1;
    }

    printf("=== DECAPSULATION ===\n");
    print_ip_header(outer_hdr, "Outer (being stripped)");
    print_ip_header(inner_hdr, "Inner (recovered)");

    /* Copy inner packet to output buffer */
    memcpy(inner_buf, inner_start, inner_len);

    return (ssize_t)inner_len;
}

/* ============================================================
 * SEND ENCAPSULATED PACKET VIA RAW SOCKET
 *
 * Raw socket with IPPROTO_RAW and IP_HDRINCL means we provide
 * our own IP header — kernel won't add one.
 * ============================================================ */
int send_ipip_packet(const uint8_t *encap_pkt, size_t encap_len,
                     const char *dst_ip_str) {
    int sockfd;
    struct sockaddr_in dst_addr;
    int one = 1;

    /* Create raw socket (requires root/CAP_NET_RAW capability) */
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sockfd < 0) {
        perror("socket(SOCK_RAW)");
        return -1;
    }

    /* Tell kernel we're providing our own IP header */
    if (setsockopt(sockfd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        perror("setsockopt(IP_HDRINCL)");
        close(sockfd);
        return -1;
    }

    /* Set destination address (kernel uses this for routing) */
    memset(&dst_addr, 0, sizeof(dst_addr));
    dst_addr.sin_family = AF_INET;
    if (inet_pton(AF_INET, dst_ip_str, &dst_addr.sin_addr) != 1) {
        fprintf(stderr, "Invalid dst IP: %s\n", dst_ip_str);
        close(sockfd);
        return -1;
    }

    /* Send the packet */
    ssize_t sent = sendto(sockfd, encap_pkt, encap_len, 0,
                          (struct sockaddr *)&dst_addr, sizeof(dst_addr));
    if (sent < 0) {
        perror("sendto");
        close(sockfd);
        return -1;
    }

    printf("Sent %zd bytes of IPIP-encapsulated packet to %s\n",
           sent, dst_ip_str);

    close(sockfd);
    return 0;
}

/* ============================================================
 * RECEIVE AND DECAPSULATE INCOMING IPIP PACKETS
 *
 * Binds a raw socket to capture all incoming IP packets,
 * filters for IPIP (proto=4), and decapsulates them.
 * ============================================================ */
static volatile int keep_running = 1;

void signal_handler(int sig) {
    (void)sig;
    keep_running = 0;
}

int receive_ipip_packets(void) {
    int sockfd;
    uint8_t recv_buf[MAX_PACKET_SIZE];
    uint8_t inner_buf[MAX_PACKET_SIZE];

    signal(SIGINT, signal_handler);

    /* IPPROTO_IP captures all IP packets */
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_IP);
    if (sockfd < 0) {
        perror("socket");
        return -1;
    }

    printf("Listening for IPIP packets (proto=4)... Press Ctrl+C to stop.\n\n");

    while (keep_running) {
        struct sockaddr_in src_addr;
        socklen_t addrlen = sizeof(src_addr);

        ssize_t recv_len = recvfrom(sockfd, recv_buf, sizeof(recv_buf), 0,
                                    (struct sockaddr *)&src_addr, &addrlen);
        if (recv_len < 0) {
            if (errno == EINTR) break;
            perror("recvfrom");
            continue;
        }

        /* Check outer IP protocol field */
        struct iphdr *hdr = (struct iphdr *)recv_buf;
        if (hdr->protocol != IPIP_PROTO) {
            continue; /* Not IPIP, skip */
        }

        printf("--- IPIP packet received from %s ---\n",
               inet_ntoa(src_addr.sin_addr));

        ssize_t inner_len = ipip_decapsulate(inner_buf, recv_buf,
                                             (size_t)recv_len);
        if (inner_len > 0) {
            printf("Decapsulated %zd bytes of inner packet.\n\n", inner_len);
            /*
             * Here you would inject inner_buf into the OS IP stack,
             * or forward it to the appropriate destination.
             * In a real kernel tunnel, this is done via netif_rx().
             */
        }
    }

    close(sockfd);
    return 0;
}

/* ============================================================
 * DEMO: Build a synthetic inner packet and encapsulate it
 * ============================================================ */
void demo_encapsulation(void) {
    /* Build a minimal inner IP packet (ICMP echo-like) */
    uint8_t inner_packet[64];
    struct iphdr *inner_hdr = (struct iphdr *)inner_packet;
    uint8_t *inner_payload = inner_packet + sizeof(struct iphdr);
    size_t payload_size = 8; /* 8 bytes of dummy ICMP-like payload */

    memset(inner_packet, 0, sizeof(inner_packet));

    /* Fill inner header */
    inner_hdr->version  = 4;
    inner_hdr->ihl      = 5;
    inner_hdr->tos      = 0;
    inner_hdr->tot_len  = htons(sizeof(struct iphdr) + payload_size);
    inner_hdr->id       = htons(0x1234);
    inner_hdr->frag_off = 0;
    inner_hdr->ttl      = 64;
    inner_hdr->protocol = 1; /* ICMP */
    inner_hdr->check    = 0;
    inet_pton(AF_INET, "10.0.0.1", &inner_hdr->saddr);
    inet_pton(AF_INET, "10.0.0.2", &inner_hdr->daddr);
    inner_hdr->check    = compute_ip_checksum(inner_hdr, sizeof(struct iphdr));

    /* Dummy payload */
    memset(inner_payload, 0xAB, payload_size);

    size_t inner_len = sizeof(struct iphdr) + payload_size;

    /* Encapsulate */
    uint8_t encap_buf[MAX_PACKET_SIZE];
    ssize_t encap_len = ipip_encapsulate(
        encap_buf,
        inner_packet,
        inner_len,
        "203.0.113.1",    /* outer source (our public IP) */
        "198.51.100.1"    /* outer dest (peer's public IP) */
    );

    if (encap_len > 0) {
        printf("Encapsulated packet ready: %zd bytes\n", encap_len);
        printf("Outer+Inner header total: %zu bytes\n",
               sizeof(struct iphdr) * 2);
        printf("IPIP overhead: %zu bytes\n\n", sizeof(struct iphdr));

        /* Now decapsulate to verify correctness */
        uint8_t recovered[MAX_PACKET_SIZE];
        ssize_t recovered_len = ipip_decapsulate(recovered, encap_buf,
                                                  (size_t)encap_len);
        if (recovered_len > 0) {
            printf("Round-trip verification successful.\n");
            printf("Recovered %zd bytes match original %zu bytes: %s\n",
                   recovered_len, inner_len,
                   (recovered_len == (ssize_t)inner_len &&
                    memcmp(recovered, inner_packet, inner_len) == 0)
                   ? "PASS" : "FAIL");
        }
    }
}

/* ============================================================
 * MAIN
 * ============================================================ */
int main(int argc, char *argv[]) {
    printf("=================================================\n");
    printf("  IPIP (IP-in-IP) Tunnel Implementation — RFC 2003\n");
    printf("=================================================\n\n");

    if (argc < 2) {
        printf("Usage:\n");
        printf("  %s demo              -- Run encap/decap demonstration\n", argv[0]);
        printf("  %s listen            -- Listen for incoming IPIP packets\n", argv[0]);
        printf("  %s send <outer_dst>  -- Send a demo IPIP packet\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "demo") == 0) {
        demo_encapsulation();
    } else if (strcmp(argv[1], "listen") == 0) {
        return receive_ipip_packets();
    } else if (strcmp(argv[1], "send") == 0 && argc >= 3) {
        uint8_t inner_packet[64];
        struct iphdr *inner_hdr = (struct iphdr *)inner_packet;
        uint8_t *payload = inner_packet + sizeof(struct iphdr);
        size_t pl_size = 8;

        memset(inner_packet, 0, sizeof(inner_packet));
        inner_hdr->version  = 4;
        inner_hdr->ihl      = 5;
        inner_hdr->tot_len  = htons(sizeof(struct iphdr) + pl_size);
        inner_hdr->ttl      = 64;
        inner_hdr->protocol = 1;
        inet_pton(AF_INET, "10.0.0.1", &inner_hdr->saddr);
        inet_pton(AF_INET, "10.0.0.2", &inner_hdr->daddr);
        inner_hdr->check    = compute_ip_checksum(inner_hdr, sizeof(struct iphdr));
        memset(payload, 0xFF, pl_size);

        uint8_t encap_buf[MAX_PACKET_SIZE];
        ssize_t encap_len = ipip_encapsulate(
            encap_buf, inner_packet,
            sizeof(struct iphdr) + pl_size,
            "203.0.113.1", argv[2]);

        if (encap_len > 0) {
            send_ipip_packet(encap_buf, (size_t)encap_len, argv[2]);
        }
    } else {
        fprintf(stderr, "Unknown command: %s\n", argv[1]);
        return 1;
    }

    return 0;
}
```

---

## 19. Rust Implementation

### Rust Concepts Used

| Concept           | What it is                                                    |
|-------------------|---------------------------------------------------------------|
| `[u8; N]`         | Fixed-size byte array — used for packet buffers               |
| `Vec<u8>`         | Dynamic byte buffer — used for variable-length packets        |
| `byteorder`       | Crate for reading/writing network byte order (big-endian)     |
| `std::net::Ipv4Addr` | Type-safe IP address                                       |
| `unsafe`          | Needed for raw pointer casting to C-style structs             |
| `Result<T, E>`    | Rust's error handling idiom — no exceptions, explicit errors  |
| `socket2`         | Crate for raw socket creation (mirrors POSIX socket API)      |

### Rust Implementation

```rust
//! IPIP (IP-in-IP) Tunnel Implementation
//!
//! RFC 2003: IP Encapsulation within IP
//!
//! This implementation demonstrates:
//! - IPv4 header construction
//! - IPIP encapsulation (wrapping inner packet in outer IP header)
//! - IPIP decapsulation (stripping outer header to recover inner packet)
//! - IP checksum computation
//!
//! Cargo.toml dependencies:
//! [dependencies]
//! # No external dependencies needed for core logic
//! # For raw socket send/receive, add:
//! # socket2 = "0.5"

use std::net::Ipv4Addr;

// ============================================================
// CONSTANTS
// ============================================================

/// IANA IP protocol number for IPIP (IP-in-IP encapsulation)
const IPIP_PROTOCOL: u8 = 4;

/// IPv4 version field value
const IPV4_VERSION: u8 = 4;

/// Default IHL (Internet Header Length) in 32-bit words.
/// 5 * 4 = 20 bytes — minimum IP header with no options.
const IPV4_IHL_NO_OPTIONS: u8 = 5;

/// Standard initial TTL value
const DEFAULT_TTL: u8 = 64;

/// Size of IPv4 header in bytes (with no options)
const IPV4_HEADER_SIZE: usize = 20;

/// Maximum inner packet size when IPIP overhead is accounted for.
/// Physical MTU (1500) - IPIP outer header (20) = 1480
const TUNNEL_MTU: usize = 1480;

// ============================================================
// IPv4 HEADER REPRESENTATION
//
// This struct mirrors the on-wire IPv4 header format exactly.
// Network byte order (big-endian) is used for multi-byte fields.
//
// In C, you cast a raw byte pointer to (struct iphdr *).
// In Rust, we use explicit byte-level parsing/serialization.
// This is safer and avoids undefined behavior from raw casts.
// ============================================================

/// Represents a parsed IPv4 header.
/// All multi-byte fields are stored in HOST byte order internally;
/// serialization converts to network byte order (big-endian).
#[derive(Debug, Clone, PartialEq)]
pub struct Ipv4Header {
    pub version:     u8,           // 4 bits — should be 4 for IPv4
    pub ihl:         u8,           // 4 bits — header length in 32-bit words
    pub tos:         u8,           // Type of Service / DSCP
    pub total_length: u16,         // Total packet size (header + payload)
    pub identification: u16,       // Used for fragmentation reassembly
    pub flags:       u8,           // 3 bits: DF, MF flags
    pub frag_offset: u16,          // 13 bits: fragment position
    pub ttl:         u8,           // Time to Live (hop count)
    pub protocol:    u8,           // Next protocol (4=IPIP, 6=TCP, 17=UDP)
    pub checksum:    u16,          // One's complement checksum of header
    pub src_addr:    Ipv4Addr,     // Source IP address
    pub dst_addr:    Ipv4Addr,     // Destination IP address
}

impl Ipv4Header {
    /// Create a new IP header with sensible defaults.
    /// Caller sets src/dst/protocol/total_length for specific use.
    pub fn new(
        src: Ipv4Addr,
        dst: Ipv4Addr,
        protocol: u8,
        total_length: u16,
        ttl: u8,
    ) -> Self {
        Ipv4Header {
            version:        IPV4_VERSION,
            ihl:            IPV4_IHL_NO_OPTIONS,
            tos:            0,
            total_length,
            identification: rand_u16(),  // pseudo-random ID
            flags:          0b010,       // DF bit set (don't fragment)
            frag_offset:    0,
            ttl,
            protocol,
            checksum:       0,           // computed separately
            src_addr:       src,
            dst_addr:       dst,
        }
    }

    /// Serialize the header to 20 bytes in network byte order.
    /// This is what actually goes on the wire.
    ///
    /// Byte layout (RFC 791):
    ///  Byte 0: [version(4)] [ihl(4)]
    ///  Byte 1: tos
    ///  Bytes 2-3: total_length (big-endian)
    ///  Bytes 4-5: identification (big-endian)
    ///  Bytes 6-7: [flags(3)] [frag_offset(13)] (big-endian)
    ///  Byte 8: ttl
    ///  Byte 9: protocol
    ///  Bytes 10-11: checksum (big-endian)
    ///  Bytes 12-15: src_addr
    ///  Bytes 16-19: dst_addr
    pub fn to_bytes(&self) -> [u8; IPV4_HEADER_SIZE] {
        let mut buf = [0u8; IPV4_HEADER_SIZE];

        // Byte 0: pack version (upper 4 bits) and ihl (lower 4 bits)
        buf[0] = (self.version << 4) | (self.ihl & 0x0F);

        // Byte 1: TOS
        buf[1] = self.tos;

        // Bytes 2-3: Total length, big-endian
        let tl = self.total_length.to_be_bytes();
        buf[2] = tl[0];
        buf[3] = tl[1];

        // Bytes 4-5: Identification, big-endian
        let id = self.identification.to_be_bytes();
        buf[4] = id[0];
        buf[5] = id[1];

        // Bytes 6-7: Flags (3 bits) + Fragment Offset (13 bits), big-endian
        // flags occupy the top 3 bits of the 16-bit field
        let flags_and_offset: u16 = ((self.flags as u16) << 13) | (self.frag_offset & 0x1FFF);
        let fo = flags_and_offset.to_be_bytes();
        buf[6] = fo[0];
        buf[7] = fo[1];

        // Byte 8: TTL
        buf[8] = self.ttl;

        // Byte 9: Protocol
        buf[9] = self.protocol;

        // Bytes 10-11: Checksum, big-endian
        let cs = self.checksum.to_be_bytes();
        buf[10] = cs[0];
        buf[11] = cs[1];

        // Bytes 12-15: Source IP (already in network order via octets())
        let src = self.src_addr.octets();
        buf[12..16].copy_from_slice(&src);

        // Bytes 16-19: Destination IP
        let dst = self.dst_addr.octets();
        buf[16..20].copy_from_slice(&dst);

        buf
    }

    /// Parse an IPv4 header from raw bytes.
    /// Returns an error if the bytes are too short or malformed.
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, IpipError> {
        if bytes.len() < IPV4_HEADER_SIZE {
            return Err(IpipError::PacketTooSmall {
                got: bytes.len(),
                need: IPV4_HEADER_SIZE,
            });
        }

        let version = bytes[0] >> 4;
        let ihl     = bytes[0] & 0x0F;

        if version != 4 {
            return Err(IpipError::InvalidVersion(version));
        }

        let ihl_bytes = (ihl as usize) * 4;
        if ihl_bytes < IPV4_HEADER_SIZE || ihl_bytes > bytes.len() {
            return Err(IpipError::InvalidIhl(ihl));
        }

        let tos          = bytes[1];
        let total_length = u16::from_be_bytes([bytes[2], bytes[3]]);
        let identification = u16::from_be_bytes([bytes[4], bytes[5]]);
        let flags_frag   = u16::from_be_bytes([bytes[6], bytes[7]]);
        let flags        = (flags_frag >> 13) as u8;
        let frag_offset  = flags_frag & 0x1FFF;
        let ttl          = bytes[8];
        let protocol     = bytes[9];
        let checksum     = u16::from_be_bytes([bytes[10], bytes[11]]);
        let src_addr     = Ipv4Addr::new(bytes[12], bytes[13], bytes[14], bytes[15]);
        let dst_addr     = Ipv4Addr::new(bytes[16], bytes[17], bytes[18], bytes[19]);

        Ok(Ipv4Header {
            version,
            ihl,
            tos,
            total_length,
            identification,
            flags,
            frag_offset,
            ttl,
            protocol,
            checksum,
            src_addr,
            dst_addr,
        })
    }

    /// Compute and set the IP header checksum.
    /// Must be called AFTER all other fields are set.
    pub fn compute_and_set_checksum(&mut self) {
        self.checksum = 0; // zero out before computing
        let bytes = self.to_bytes();
        self.checksum = ip_checksum(&bytes);
    }

    /// Verify the IP header checksum.
    /// Returns true if checksum is valid.
    pub fn verify_checksum(&self) -> bool {
        let bytes = self.to_bytes();
        ip_checksum(&bytes) == 0 // valid if result is 0
    }
}

impl std::fmt::Display for Ipv4Header {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let proto_name = match self.protocol {
            1  => "ICMP",
            4  => "IPIP",
            6  => "TCP",
            17 => "UDP",
            41 => "IPv6",
            47 => "GRE",
            _  => "Unknown",
        };
        writeln!(f, "  Version  : {}", self.version)?;
        writeln!(f, "  IHL      : {} ({} bytes)", self.ihl, self.ihl * 4)?;
        writeln!(f, "  TOS      : 0x{:02x}", self.tos)?;
        writeln!(f, "  Tot Len  : {}", self.total_length)?;
        writeln!(f, "  ID       : 0x{:04x}", self.identification)?;
        writeln!(f, "  Flags    : {:03b}", self.flags)?;
        writeln!(f, "  Frag Off : {}", self.frag_offset)?;
        writeln!(f, "  TTL      : {}", self.ttl)?;
        writeln!(f, "  Protocol : {} ({})", self.protocol, proto_name)?;
        writeln!(f, "  Checksum : 0x{:04x}", self.checksum)?;
        writeln!(f, "  Src      : {}", self.src_addr)?;
        write!(f,   "  Dst      : {}", self.dst_addr)
    }
}

// ============================================================
// IP CHECKSUM
//
// RFC 791 defines the checksum as:
// "The checksum field is the 16-bit one's complement of the
//  one's complement sum of all 16-bit words in the header."
//
// One's complement addition: add with carry wrapping around.
// One's complement of result: flip all bits (~).
// ============================================================

/// Compute the IPv4 one's complement header checksum.
///
/// Input: raw bytes of the IP header (with checksum field zeroed).
/// Output: 16-bit checksum value to place in the checksum field.
pub fn ip_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;

    // Process 16-bit words
    while i + 1 < data.len() {
        let word = u16::from_be_bytes([data[i], data[i + 1]]) as u32;
        sum += word;
        i += 2;
    }

    // Handle odd byte if present
    if i < data.len() {
        sum += (data[i] as u32) << 8;
    }

    // Fold 32-bit sum to 16 bits by adding carry repeatedly
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    // One's complement: flip all bits
    !(sum as u16)
}

// ============================================================
// ERROR TYPES
// ============================================================

/// Errors that can occur during IPIP operations
#[derive(Debug)]
pub enum IpipError {
    /// Packet is too short to contain a valid IP header
    PacketTooSmall { got: usize, need: usize },
    /// IP version field is not 4
    InvalidVersion(u8),
    /// IHL field is invalid (too small or exceeds packet)
    InvalidIhl(u8),
    /// Outer IP protocol field is not 4 (not IPIP)
    NotIpip { found: u8 },
    /// Inner IP header is invalid after decapsulation
    InvalidInnerPacket(String),
}

impl std::fmt::Display for IpipError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::PacketTooSmall { got, need } =>
                write!(f, "Packet too small: got {} bytes, need {}", got, need),
            Self::InvalidVersion(v) =>
                write!(f, "Invalid IP version: {} (expected 4)", v),
            Self::InvalidIhl(ihl) =>
                write!(f, "Invalid IHL: {}", ihl),
            Self::NotIpip { found } =>
                write!(f, "Not an IPIP packet: protocol={} (expected 4)", found),
            Self::InvalidInnerPacket(msg) =>
                write!(f, "Invalid inner packet: {}", msg),
        }
    }
}

impl std::error::Error for IpipError {}

// ============================================================
// IPIP ENCAPSULATION
// ============================================================

/// Result of IPIP encapsulation
pub struct EncapsulatedPacket {
    /// Complete encapsulated packet bytes (outer header + inner packet)
    pub bytes: Vec<u8>,
    /// Length of the outer IP header (always 20 for no-options)
    pub outer_header_len: usize,
    /// Length of the inner packet (original packet, unchanged)
    pub inner_len: usize,
}

impl EncapsulatedPacket {
    /// Display a summary of the encapsulated packet
    pub fn display_summary(&self) {
        println!("=== ENCAPSULATION SUMMARY ===");
        println!("Total packet size  : {} bytes", self.bytes.len());
        println!("Outer IP header    : {} bytes", self.outer_header_len);
        println!("Inner packet       : {} bytes", self.inner_len);
        println!("IPIP overhead      : {} bytes", self.outer_header_len);
        println!();

        if let Ok(outer) = Ipv4Header::from_bytes(&self.bytes[..IPV4_HEADER_SIZE]) {
            println!("[Outer IP Header]");
            println!("{}", outer);
            println!();
        }
        if let Ok(inner) = Ipv4Header::from_bytes(&self.bytes[IPV4_HEADER_SIZE..]) {
            println!("[Inner IP Header]");
            println!("{}", inner);
            println!();
        }
    }
}

/// Encapsulate an inner IP packet within an outer IP packet (IPIP).
///
/// # Parameters
/// - `inner_packet`: Complete inner IP packet bytes (header + payload)
/// - `outer_src`: Public IP of the tunnel entry point (our side)
/// - `outer_dst`: Public IP of the tunnel exit point (peer side)
/// - `outer_ttl`: TTL for the outer IP header
///
/// # Returns
/// On success: `EncapsulatedPacket` with the full encapsulated packet bytes.
/// On failure: `IpipError` describing what went wrong.
pub fn ipip_encapsulate(
    inner_packet: &[u8],
    outer_src: Ipv4Addr,
    outer_dst: Ipv4Addr,
    outer_ttl: u8,
) -> Result<EncapsulatedPacket, IpipError> {

    // Step 1: Validate inner packet has a valid IP header
    if inner_packet.len() < IPV4_HEADER_SIZE {
        return Err(IpipError::PacketTooSmall {
            got: inner_packet.len(),
            need: IPV4_HEADER_SIZE,
        });
    }

    // Step 2: Check MTU (warn but don't fail — caller decides on fragmentation)
    if inner_packet.len() > TUNNEL_MTU {
        eprintln!(
            "Warning: inner packet ({} bytes) exceeds tunnel MTU ({} bytes). \
             Consider fragmentation or MSS clamping.",
            inner_packet.len(), TUNNEL_MTU
        );
    }

    // Step 3: Compute outer packet total length
    // outer_total_length = size of outer header + size of inner packet
    let outer_total_length = (IPV4_HEADER_SIZE + inner_packet.len()) as u16;

    // Step 4: Build outer IP header
    let mut outer_header = Ipv4Header::new(
        outer_src,
        outer_dst,
        IPIP_PROTOCOL,        // Protocol = 4 (IPIP) — the key identifier
        outer_total_length,
        outer_ttl,
    );

    // Step 5: Compute outer header checksum
    // Important: checksum is computed AFTER all fields are set
    outer_header.compute_and_set_checksum();

    // Step 6: Serialize outer header to bytes
    let outer_bytes = outer_header.to_bytes();

    // Step 7: Concatenate outer header + inner packet
    // This is the complete encapsulated packet as it travels over the internet
    let mut encapsulated = Vec::with_capacity(IPV4_HEADER_SIZE + inner_packet.len());
    encapsulated.extend_from_slice(&outer_bytes);
    encapsulated.extend_from_slice(inner_packet);

    Ok(EncapsulatedPacket {
        bytes: encapsulated,
        outer_header_len: IPV4_HEADER_SIZE,
        inner_len: inner_packet.len(),
    })
}

// ============================================================
// IPIP DECAPSULATION
// ============================================================

/// Result of IPIP decapsulation
pub struct DecapsulatedPacket {
    /// The recovered inner IP packet bytes
    pub inner_bytes: Vec<u8>,
    /// Parsed outer IP header (already stripped)
    pub outer_header: Ipv4Header,
}

impl DecapsulatedPacket {
    /// Display a summary of the decapsulated packet
    pub fn display_summary(&self) {
        println!("=== DECAPSULATION SUMMARY ===");
        println!("[Outer IP Header (stripped)]");
        println!("{}", self.outer_header);
        println!();
        if let Ok(inner_hdr) = Ipv4Header::from_bytes(&self.inner_bytes) {
            println!("[Inner IP Header (recovered)]");
            println!("{}", inner_hdr);
            println!();
        }
        println!("Inner packet size: {} bytes", self.inner_bytes.len());
    }
}

/// Decapsulate an IPIP packet, recovering the inner IP packet.
///
/// # Parameters
/// - `received_packet`: Raw bytes of the received packet (outer header + inner packet)
///
/// # Returns
/// On success: `DecapsulatedPacket` with inner packet bytes and outer header info.
/// On failure: `IpipError` describing what went wrong.
pub fn ipip_decapsulate(
    received_packet: &[u8],
) -> Result<DecapsulatedPacket, IpipError> {

    // Step 1: Minimum size check — must have at least two IP headers
    if received_packet.len() < IPV4_HEADER_SIZE * 2 {
        return Err(IpipError::PacketTooSmall {
            got: received_packet.len(),
            need: IPV4_HEADER_SIZE * 2,
        });
    }

    // Step 2: Parse and validate outer IP header
    let outer_header = Ipv4Header::from_bytes(&received_packet[..IPV4_HEADER_SIZE])?;

    // Step 3: Verify this is an IPIP packet
    // The Protocol field in the outer header must be 4 (IPIP_PROTOCOL)
    if outer_header.protocol != IPIP_PROTOCOL {
        return Err(IpipError::NotIpip { found: outer_header.protocol });
    }

    // Step 4: Determine outer header length (IHL field * 4)
    // This handles cases where outer header has options (IHL > 5)
    let outer_hdr_len = (outer_header.ihl as usize) * 4;

    if outer_hdr_len > received_packet.len() {
        return Err(IpipError::InvalidIhl(outer_header.ihl));
    }

    // Step 5: Extract inner packet (everything after the outer header)
    let inner_bytes = received_packet[outer_hdr_len..].to_vec();

    // Step 6: Validate inner packet has a valid IP header
    if inner_bytes.len() < IPV4_HEADER_SIZE {
        return Err(IpipError::InvalidInnerPacket(format!(
            "Inner packet too small: {} bytes", inner_bytes.len()
        )));
    }

    let inner_header = Ipv4Header::from_bytes(&inner_bytes)?;
    if inner_header.version != 4 {
        return Err(IpipError::InvalidInnerPacket(format!(
            "Inner IP version is {} (expected 4)", inner_header.version
        )));
    }

    Ok(DecapsulatedPacket {
        inner_bytes,
        outer_header,
    })
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

/// Build a minimal synthetic inner IP packet for demonstration.
/// In real usage, this packet would come from the OS kernel.
pub fn build_demo_inner_packet(
    src: Ipv4Addr,
    dst: Ipv4Addr,
    payload: &[u8],
) -> Vec<u8> {
    let total_len = (IPV4_HEADER_SIZE + payload.len()) as u16;

    let mut header = Ipv4Header::new(
        src,
        dst,
        1,        // Protocol 1 = ICMP (demo)
        total_len,
        DEFAULT_TTL,
    );
    header.compute_and_set_checksum();

    let mut packet = Vec::with_capacity(IPV4_HEADER_SIZE + payload.len());
    packet.extend_from_slice(&header.to_bytes());
    packet.extend_from_slice(payload);
    packet
}

/// Naive pseudo-random u16 for packet ID (demo purposes only).
/// In production, use the OS's random number generator.
fn rand_u16() -> u16 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .subsec_nanos();
    (nanos & 0xFFFF) as u16
}

// ============================================================
// MAIN — DEMONSTRATION
// ============================================================

fn main() {
    println!("╔══════════════════════════════════════════════════════╗");
    println!("║   IPIP (IP-in-IP) Tunnel — RFC 2003 Implementation   ║");
    println!("╚══════════════════════════════════════════════════════╝");
    println!();

    // --- SETUP ---
    let inner_src = Ipv4Addr::new(10, 0, 0, 1);     // Private network src
    let inner_dst = Ipv4Addr::new(10, 0, 0, 2);     // Private network dst
    let outer_src = Ipv4Addr::new(203, 0, 113, 1);  // Tunnel entry (our public IP)
    let outer_dst = Ipv4Addr::new(198, 51, 100, 1); // Tunnel exit (peer public IP)

    let payload = b"Hello from IPIP tunnel!"; // Original application data

    // --- BUILD INNER PACKET ---
    println!("Step 1: Building inner packet (simulates OS kernel output)");
    println!("  Src: {} -> Dst: {}", inner_src, inner_dst);
    println!("  Payload: {:?}", std::str::from_utf8(payload).unwrap());
    println!();

    let inner_packet = build_demo_inner_packet(inner_src, inner_dst, payload);
    println!("  Inner packet size: {} bytes", inner_packet.len());
    if let Ok(hdr) = Ipv4Header::from_bytes(&inner_packet) {
        println!("  Checksum valid: {}", hdr.verify_checksum());
    }
    println!();

    // --- ENCAPSULATION ---
    println!("Step 2: IPIP Encapsulation");
    println!("  Outer Src: {} -> Outer Dst: {}", outer_src, outer_dst);
    println!("  This wraps the entire inner packet as payload of outer IP.");
    println!();

    match ipip_encapsulate(&inner_packet, outer_src, outer_dst, DEFAULT_TTL) {
        Ok(encapsulated) => {
            encapsulated.display_summary();

            // Verify outer checksum
            if let Ok(outer_hdr) = Ipv4Header::from_bytes(&encapsulated.bytes) {
                println!("Outer checksum valid: {}", outer_hdr.verify_checksum());
            }

            // --- DECAPSULATION ---
            println!();
            println!("Step 3: IPIP Decapsulation");
            println!("  (Simulates tunnel exit point receiving the packet)");
            println!();

            match ipip_decapsulate(&encapsulated.bytes) {
                Ok(decapsulated) => {
                    decapsulated.display_summary();

                    // Verify round-trip integrity
                    let matches = decapsulated.inner_bytes == inner_packet;
                    println!("Round-trip integrity check: {}",
                             if matches { "PASS ✓" } else { "FAIL ✗" });

                    // Recover original payload
                    let recovered_payload = &decapsulated.inner_bytes[IPV4_HEADER_SIZE..];
                    println!("Recovered payload: {:?}",
                             std::str::from_utf8(recovered_payload).unwrap_or("<non-utf8>"));
                }
                Err(e) => eprintln!("Decapsulation failed: {}", e),
            }
        }
        Err(e) => eprintln!("Encapsulation failed: {}", e),
    }

    // --- CHECKSUM DEMONSTRATION ---
    println!();
    println!("Step 4: IP Checksum Verification");
    let test_bytes = [
        0x45, 0x00, 0x00, 0x3c, // version, ihl, tos, total_len
        0x1c, 0x46, 0x40, 0x00, // id, flags, frag_offset
        0x40, 0x06, 0x00, 0x00, // ttl, protocol, checksum=0
        0xac, 0x10, 0x0a, 0x63, // src: 172.16.10.99
        0xac, 0x10, 0x0a, 0x0c, // dst: 172.16.10.12
    ];
    let checksum = ip_checksum(&test_bytes);
    println!("Computed checksum for test header: 0x{:04x}", checksum);
    println!("(Insert this value into bytes 10-11, then verify = 0x0000)");

    println!();
    println!("=== IPIP Protocol Key Facts ===");
    println!("  Protocol Number  : 4 (in outer IP header's Protocol field)");
    println!("  Overhead         : 20 bytes (one additional IP header)");
    println!("  Effective MTU    : 1480 bytes (1500 - 20 overhead)");
    println!("  Encryption       : None (add IPSec for security)");
    println!("  RFC              : RFC 2003");
    println!("  Linux module     : ipip.ko");
}
```

---

## 20. Security Considerations

### IPIP Has No Built-In Security

IPIP is a **bare, unprotected protocol**. It provides:
- ❌ No encryption
- ❌ No authentication
- ❌ No integrity checking
- ❌ No replay protection

This means:

```
ATTACK 1: Packet Injection
  Attacker forges an IPIP packet with crafted inner packet.
  If tunnel endpoint accepts any source, attacker can inject traffic
  into the private network hidden inside the tunnel.

  Attacker --> [Tunnel Exit] --> Private Network
  (Sends IPIP packet with forged outer src, inner dst = victim)

ATTACK 2: Traffic Eavesdropping
  Anyone on the path between tunnel endpoints can:
  - See the outer packet headers (who is tunneling to whom)
  - See the inner packet headers (actual src/dst)
  - See the inner payload (application data, unencrypted)
  IPIP provides no confidentiality.

ATTACK 3: Spoofed Source
  Attacker spoofs the outer src IP to appear as a trusted tunnel peer.
  Tunnel endpoint may accept and decapsulate the packet.
  This is a form of IP spoofing amplified by tunneling.
```

### Mitigations

```
MITIGATION 1: Source IP Filtering (Basic)
  Configure tunnel endpoints to only accept IPIP packets from
  known peer IPs. Use iptables or routing policy:

  iptables -A INPUT -p 4 ! --source 198.51.100.1 -j DROP
  (Only accept IPIP from our known tunnel peer)

MITIGATION 2: IPSec + IPIP (Standard Practice)
  Layer IPSec (ESP mode) over IPIP to add:
  - Encryption (ESP)
  - Authentication (AH or ESP with auth)
  - Replay protection
  This is a common combination in enterprise VPNs.

MITIGATION 3: Use WireGuard or IPSec Natively
  If security is critical, consider WireGuard or IPSec directly
  instead of raw IPIP. These include encryption by design.

MITIGATION 4: Network Policy / Firewall
  Strict ingress/egress filtering at borders:
  - Block protocol 4 traffic except from trusted peers
  - Rate limit IPIP to prevent abuse
  - Monitor for unexpected IPIP traffic
```

### Firewall Rules for IPIP

```bash
# Allow IPIP only from trusted tunnel peer
iptables -A INPUT  -p 4 -s 198.51.100.1 -j ACCEPT
iptables -A INPUT  -p 4 -j DROP          # Drop all other IPIP
iptables -A OUTPUT -p 4 -d 198.51.100.1 -j ACCEPT
iptables -A OUTPUT -p 4 -j DROP

# Allow traffic on the tunnel interface
iptables -A FORWARD -i ipip0 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0  -o ipip0 -j ACCEPT
```

---

## 21. Debugging and Observability

### Tool 1: tcpdump — Packet Capture

```bash
# Capture all IPIP packets (proto 4) on eth0
tcpdump -i eth0 -n proto 4

# Capture IPIP and show inner packet details
tcpdump -i eth0 -n proto 4 -v

# Decode IPIP and show inner headers
tcpdump -i eth0 -n proto 4 -vvv

# Example output:
# 14:23:01.123456 IP 203.0.113.1 > 198.51.100.1: IP 10.0.0.1 > 10.0.0.2: TCP ...
#                  ^^^outer src    ^^^outer dst    ^^^inner packet shown here
```

### Tool 2: ip — Tunnel Interface Management

```bash
# Show tunnel info
ip tunnel show

# Show tunnel interface statistics
ip -s link show ipip0

# Monitor tunnel traffic in real time
watch -n 1 ip -s link show ipip0
```

### Tool 3: ping — Tunnel Health Check

```bash
# Ping through the tunnel (inner network)
ping -I ipip0 10.0.0.2

# Ping with specific packet size (to test MTU)
ping -I ipip0 -s 1452 10.0.0.2   # 1452 + 28 = 1480 (tunnel MTU)
ping -I ipip0 -s 1453 10.0.0.2   # Should fragment or fail if DF set
```

### Tool 4: traceroute — Path Analysis

```bash
# Trace through the tunnel
traceroute -i ipip0 10.0.0.2

# With IPIP in pipe mode (tunnel hidden), hops inside tunnel are masked
```

### Tool 5: ss / netstat — Socket State

```bash
# View raw sockets (used by IPIP implementation)
ss -n --raw

# System call tracing for IPIP operations
strace -e socket,sendto,recvfrom,setsockopt ./ipip_program
```

### Diagnostic Checklist

```
IPIP Tunnel Not Working — Diagnostic Steps:

  1. [ ] Is the ipip kernel module loaded?
         lsmod | grep ipip

  2. [ ] Is the tunnel interface up?
         ip link show ipip0

  3. [ ] Is the tunnel interface configured correctly?
         ip tunnel show ipip0
         (check local/remote IPs match expected values)

  4. [ ] Are IPIP packets being blocked by firewall?
         iptables -L -n | grep proto 4
         (proto 4 = IPIP)

  5. [ ] Can outer endpoints reach each other?
         ping 198.51.100.1  (from 203.0.113.1)

  6. [ ] Is MTU causing fragmentation/drops?
         ping -M do -s 1480 -I ipip0 10.0.0.2
         (do = DF set; fail if MTU problem)

  7. [ ] Are routing rules correct?
         ip route show
         ip route get 10.0.0.2

  8. [ ] Is rp_filter blocking tunnel traffic?
         sysctl net.ipv4.conf.ipip0.rp_filter
         (set to 0 or 2 for tunnel interfaces)
         sysctl -w net.ipv4.conf.ipip0.rp_filter=0
```

---

## 22. Mental Models and Cognitive Frameworks

### Mental Model 1: The Russian Doll

IPIP is like a Russian matryoshka doll:
- Outer doll = outer IP header (public addressing)
- Inner doll = inner IP header (private addressing)
- Innermost content = actual application data

You can only see the outer doll as it travels. The inner structure is hidden
until you open (decapsulate) the outer shell.

### Mental Model 2: The Postal Envelope Metaphor

```
Inner packet = A letter with address: 10.0.0.1 -> 10.0.0.2
IPIP packet  = Letter stuffed inside another envelope: 203.0.113.1 -> 198.51.100.1

Post office (internet routers) only reads the outer envelope.
At the destination post office (tunnel exit), the outer envelope is opened,
and the inner letter is delivered to its final destination.
```

### Mental Model 3: The Protocol as a Stack of Decisions

Each protocol layer answers one question:

```
Layer | Protocol | Question answered
------+----------+------------------------------------------
  L2  | Ethernet | Who is the next-hop MAC on this LAN?
  L3  | IP       | Who is the final destination IP?
  L3  | IPIP     | Is this packet tunneled? If so, which inner IP?
  L4  | TCP      | Which application port? Is it reliable?
  L7  | HTTP     | What is the request/response?
```

### Mental Model 4: Abstraction Layers in Tunneling

```
Physical Reality:          Logical Abstraction:
==================         ====================

[203.0.113.1]              [10.0.0.1]
     |                          |
  [Internet]             [Virtual direct link]
     |                          |
[198.51.100.1]             [10.0.0.2]

IPIP makes the physical internet invisible.
The two private networks behave as if directly connected.
```

### Cognitive Strategies for Protocol Mastery

**1. Packet Walking (Deliberate Practice)**
Take any packet you're studying and manually trace it through each layer.
Ask: "What does each router see? What does each endpoint do?"

**2. The Protocol Triangle**
Every protocol balances: Simplicity ↔ Security ↔ Features.
IPIP maximizes simplicity (minimal overhead, no features, no security).
IPSec maximizes security at cost of complexity.
GRE balances features vs simplicity.

**3. The Byte Map Technique**
Draw a 20-byte grid. Fill in each field of the IP header manually.
Do this for both outer and inner headers in an IPIP packet.
This builds the low-level intuition needed to read hex dumps.

```
IPIP Byte Map (40 bytes = outer + inner header):

Byte:  0    1    2    3    4    5    6    7
       45   00   00   50   1c   46   40   00
       [V+IHL][TOS][Total Len][ID  ][Flags+Frag]

Byte:  8    9    10   11   12   13   14   15
       40   04   XX   XX   CB   00   71   01
       [TTL][Pro][Checksum ][Src IP: 203.0.113.1]

Byte:  16   17   18   19
       C6   33   64   01
       [Dst IP: 198.51.100.1]

Byte:  20-39: (inner IP header, same structure, different addresses)
```

**4. Chunking Protocol Knowledge**
Group related concepts together for faster recall:
- Chunk 1: Header fields (version, IHL, TTL, protocol, checksum, src, dst)
- Chunk 2: IPIP mechanics (proto=4, outer+inner, encap/decap)
- Chunk 3: Problems (MTU, TTL, security, fragmentation)
- Chunk 4: Solutions (PMTUD, MSS clamp, IPSec, rp_filter)

**5. Comparative Analysis**
Always understand a protocol by comparing it to its neighbors:
- IPIP is simpler than GRE, but less capable.
- IPIP is faster than OpenVPN, but less secure.
- IPIP is older than VXLAN, but more efficient for pure L3.

---

## Summary — Key Takeaways

```
+-----------------------------------------------------------------------+
|                    IPIP Protocol — Master Summary                     |
+-----------------------------------------------------------------------+
|  WHAT IT IS  | IP-in-IP tunneling. One IP packet inside another.      |
|              | Protocol number = 4 in outer IP header.                |
+-----------------------------------------------------------------------+
|  RFC         | RFC 2003 (IPv4), RFC 2473 (IPv6 generalization)        |
+-----------------------------------------------------------------------+
|  OVERHEAD    | Exactly 20 bytes (one additional IPv4 header)          |
|  EFFECTIVE   | 1500 - 20 = 1480 bytes effective MTU                   |
|  MTU         |                                                        |
+-----------------------------------------------------------------------+
|  ENCAP       | Outer IP: src=tunnel_entry, dst=tunnel_exit, proto=4   |
|  HEADER      | Inner IP: original packet, completely untouched        |
+-----------------------------------------------------------------------+
|  DECAP       | Read proto=4, strip 20 bytes, re-inject inner packet   |
+-----------------------------------------------------------------------+
|  SECURITY    | NONE built-in. Add IPSec for encryption/auth.          |
+-----------------------------------------------------------------------+
|  LINUX       | ipip.ko kernel module. `ip tunnel add mode ipip`       |
+-----------------------------------------------------------------------+
|  USE CASES   | Site-to-site VPN, Mobile IP, Kubernetes CNI,           |
|              | ISP backbone tunnels, L3 overlay networks              |
+-----------------------------------------------------------------------+
|  STRENGTHS   | Minimal overhead, simplicity, high performance         |
|  WEAKNESSES  | No security, no multicast, IPv4-only (RFC 2003)        |
+-----------------------------------------------------------------------+
|  KEY CMD     | ip tunnel add ipip0 mode ipip local X.X.X.X            |
|              |   remote Y.Y.Y.Y ttl 64                                |
+-----------------------------------------------------------------------+
```

---

*End of IPIP Protocol Complete Guide.*
*Study deliberately. Think in layers. Master the fundamentals.*

## How ICMP Works in PMTUD — Router & Kernel Deep Dive

You're right that ICMP is a separate protocol, but it has a special role: **it's the error-reporting layer for IP itself**. Think of it as IP's built-in "complaint system."

---

### 1. Why ICMP Gets Involved At All

When a router can't forward a packet as-is, it can't just silently drop it (well, it can, but PMTUD depends on it *not* doing that). The contract is:

```
IP has no error reporting of its own.
ICMP is the designated error channel FOR IP.
```

ICMP Type 3, Code 4 = **"Destination Unreachable — Fragmentation Needed and DF Set"**
This is the specific ICMP message used in PMTUD.

---

### 2. What the ICMP Packet Actually Looks Like

This is the crucial part people miss. The ICMP error is **not just a signal** — it contains a **copy of the offending packet's header**:

```
┌─────────────────────────────────────────────┐
│  Outer IP Header                            │
│  (src = router's IP, dst = original sender) │
├─────────────────────────────────────────────┤
│  ICMP Header                                │
│  Type=3, Code=4                             │
│  Next-Hop MTU = 1400  (the bottleneck MTU)  │
├─────────────────────────────────────────────┤
│  Original IP Header  ← copy of YOUR packet  │
│  (src = sender, dst = destination)          │
├─────────────────────────────────────────────┤
│  First 8 bytes of original payload          │
│  (TCP/UDP header — enough to get port nums) │
└─────────────────────────────────────────────┘
```

The **first 8 bytes of original payload** is what lets the kernel match this ICMP back to a specific socket/connection.

---

### 3. Kernel-Level Handling (Linux)

#### Step 1 — Router side (sending the ICMP)
```
Router receives packet:
  → checks output interface MTU (e.g. 1400)
  → packet size > 1400, DF=1
  → calls icmp_send() in kernel
  → builds ICMP Type3/Code4, copies original IP header + 8 bytes
  → sends back to original source IP
  → drops original packet
```

#### Step 2 — Sender's kernel receives the ICMP

The kernel's IP stack intercepts ICMP errors **before** they reach userspace:

```
icmp_rcv()                    ← ICMP dispatch
  └─ icmp_unreach()           ← handles Type 3
       └─ reads Next-Hop MTU from ICMP payload
       └─ reads original IP header → gets proto (TCP=6?)
       └─ reads first 8 bytes → gets src/dst ports
       └─ looks up socket in socket table using
          (src_ip, src_port, dst_ip, dst_port)
       └─ updates socket's PMTU cache:
             ip_rt_update_pmtu() → updates routing cache
       └─ notifies transport layer:
             tcp_v4_err()  ← for TCP sockets
```

#### Step 3 — TCP reacts
```
tcp_v4_err():
  → finds the TCP socket
  → reduces tcp_sock.mss_cache to fit new PMTU
  → re-queues packets that were too large
  → retransmits with smaller size
```

No userspace app involvement. **The kernel handles it transparently.**

---

### 4. The IPIP Tunnel Break — Exactly Why It Fails

```
Inner packet:  src=10.0.0.1  dst=10.0.0.2  DF=1  size=1500
Outer packet:  src=1.1.1.1   dst=2.2.2.2   DF=1  size=1520
                                                   (adds 20B IP header)
```

A router with MTU=1500 sees the **outer** packet at 1520 bytes → sends ICMP back to `1.1.1.1` (the **tunnel entry point**), referencing the **outer** packet.

```
ICMP arrives at tunnel entry point (1.1.1.1):
  → kernel looks up socket by outer header
  → outer header is the TUNNEL, not a real TCP socket
  → no matching socket found for inner 10.0.0.1
  → ICMP is SILENTLY DROPPED  ← black hole
```

`10.0.0.1` (the real sender) **never learns** about the MTU limit. It keeps sending 1500B packets. They keep getting dropped. **PMTUD black hole.**

---

### 5. The Fixes — Kernel Mechanism

**Fix A: ICMP Translation at Tunnel Endpoint**
The tunnel endpoint kernel code must intercept the ICMP, **unwrap** it, look at the **inner** original header, and synthesize a *new* ICMP back to the inner sender:

```
ipip_err() in kernel (net/ipv4/ipip.c):
  → receives ICMP about outer packet
  → strips outer header from the embedded copy
  → finds inner IP header (10.0.0.1 → 10.0.0.2)
  → subtracts tunnel overhead from reported MTU
        new_mtu = icmp_mtu - sizeof(outer_ip_header)
  → calls tcp_v4_err() as if ICMP came for inner packet
  → inner sender 10.0.0.1 now gets the right MTU
```

**Fix B: MSS Clamping (TCP only)**
```
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
         -j TCPMSS --clamp-mss-to-pmtu
```
The tunnel endpoint **rewrites the TCP MSS option** in SYN packets during handshake. This is a blunt workaround — it doesn't use ICMP at all, just proactively limits segment size before any packet is sent.

---

### Summary Table

| Layer | Role |
|---|---|
| IP | Carries packets, sets DF bit |
| ICMP | Error signaling for IP — embeds original header so errors are traceable |
| Router kernel | Generates ICMP on drop, embeds offending header |
| Sender kernel (`icmp_rcv → tcp_v4_err`) | Matches ICMP to socket via embedded header, updates MTU cache |
| IPIP tunnel | Breaks the match because ICMP references outer header, not inner socket |
| Fix (`ipip_err`) | Re-derives inner socket from embedded outer+inner headers, synthesizes correct ICMP |

The core insight is: **ICMP is not just a signal — it's a carrier of enough of the original packet to trace back to the exact socket that caused it.** IPIP breaks that traceability by adding an extra layer the ICMP doesn't know to unwrap.