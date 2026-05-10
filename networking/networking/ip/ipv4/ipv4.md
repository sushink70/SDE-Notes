# IPv4 — Complete Comprehensive Guide

> **Scope:** Every concept in IPv4 — addressing, math, headers, fragmentation, ARP, ICMP,
> routing, NAT, DHCP, subnetting, VLSM, CIDR, exhaustion, Linux kernel internals, socket layer,
> Netfilter — with ASCII diagrams, math, and kernel source references.

---

## Table of Contents

1. [What Is IPv4?](#1-what-is-ipv4)
2. [IPv4 Address Structure](#2-ipv4-address-structure)
3. [Binary & Decimal Arithmetic](#3-binary--decimal-arithmetic)
4. [Address Classes (Classful Addressing)](#4-address-classes-classful-addressing)
5. [Special & Reserved Addresses](#5-special--reserved-addresses)
6. [Subnet Masks & CIDR Notation](#6-subnet-masks--cidr-notation)
7. [Subnetting — Step-by-Step Math](#7-subnetting--step-by-step-math)
8. [VLSM — Variable Length Subnet Masking](#8-vlsm--variable-length-subnet-masking)
9. [Supernetting & Route Aggregation](#9-supernetting--route-aggregation)
10. [IPv4 Packet Header](#10-ipv4-packet-header)
11. [IP Fragmentation & Reassembly](#11-ip-fragmentation--reassembly)
12. [ARP — Address Resolution Protocol](#12-arp--address-resolution-protocol)
13. [ICMP — Internet Control Message Protocol](#13-icmp--internet-control-message-protocol)
14. [IPv4 Routing](#14-ipv4-routing)
15. [NAT — Network Address Translation](#15-nat--network-address-translation)
16. [DHCP — Dynamic Host Configuration Protocol](#16-dhcp--dynamic-host-configuration-protocol)
17. [IPv4 in the Linux Kernel](#17-ipv4-in-the-linux-kernel)
18. [Socket Layer & IPv4](#18-socket-layer--ipv4)
19. [Netfilter & iptables with IPv4](#19-netfilter--iptables-with-ipv4)
20. [IPv4 Address Exhaustion & IPv6 Transition](#20-ipv4-address-exhaustion--ipv6-transition)
21. [Debugging IPv4 on Linux](#21-debugging-ipv4-on-linux)

---

## 1. What Is IPv4?

IPv4 (Internet Protocol version 4) is a **connectionless, best-effort, unreliable** Layer 3
(Network Layer) protocol defined in **RFC 791** (September 1981).

- **Connectionless** — no handshake before sending packets.
- **Best-effort** — no delivery guarantee; packets can be lost, duplicated, or reordered.
- **Unreliable** — error detection (header checksum) but no error correction or retransmission.

Higher layers (TCP, SCTP) provide reliability on top of IPv4.

### OSI / TCP-IP Stack Position

```
  OSI Model          TCP/IP Model         Protocol
+-------------+    +-------------+
| Application |    | Application |   HTTP, FTP, DNS, SSH
+-------------+    +-------------+
| Presentation|    |             |
+-------------+    +-------------+
| Session     |    |             |
+-------------+    +-------------+
| Transport   |    | Transport   |   TCP, UDP, SCTP
+-------------+    +-------------+
| Network     |    | Internet    |   IPv4 ← HERE
+-------------+    +-------------+
| Data Link   |    | Link        |   Ethernet, Wi-Fi, PPP
+-------------+    +-------------+
| Physical    |    |             |   Cables, Radio
+-------------+    +-------------+
```

### IPv4 vs IPv6 Quick Comparison

| Feature        | IPv4              | IPv6                     |
|----------------|-------------------|--------------------------|
| Address length | 32 bits           | 128 bits                 |
| Notation       | Dotted decimal    | Colon-hex                |
| Address space  | ~4.3 billion      | ~3.4 × 10^38             |
| Header size    | 20–60 bytes       | 40 bytes (fixed)         |
| Fragmentation  | Routers & hosts   | Hosts only               |
| Checksum       | Header checksum   | None (moved to transport)|
| ARP            | Yes (IPv4)        | NDP (Neighbor Discovery) |

---

## 2. IPv4 Address Structure

An IPv4 address is a **32-bit unsigned integer**, typically written in
**dotted-decimal notation**: four octets separated by dots.

```
  32-bit binary address:
  ┌────────────┬────────────┬────────────┬────────────┐
  │   Octet 1  │   Octet 2  │   Octet 3  │   Octet 4  │
  │  8 bits    │  8 bits    │  8 bits    │  8 bits    │
  └────────────┴────────────┴────────────┴────────────┘
     Bit 31                                    Bit 0

  Example:  192.168.1.100
  Binary:   11000000.10101000.00000001.01100100
            ^^^^^^^^ ^^^^^^^^ ^^^^^^^^ ^^^^^^^^
              192      168       1       100
```

### Binary Bit Weights Per Octet

Each octet is 8 bits. Bit positions and their decimal values:

```
  Bit position:  7    6    5    4    3    2    1    0
  Bit weight:   128   64   32   16    8    4    2    1
                2^7  2^6  2^5  2^4  2^3  2^2  2^1  2^0
```

So 192 = 128 + 64 = 11000000₂

### Math: Total Address Space

```
  Total IPv4 addresses = 2^32 = 4,294,967,296 ≈ 4.3 billion

  Usable addresses per network = 2^(host bits) - 2
    (subtract network address and broadcast address)
```

### Notation Forms

| Form            | Example                   |
|-----------------|---------------------------|
| Dotted decimal  | 192.168.1.100             |
| Binary          | 11000000.10101000.00000001.01100100 |
| Hexadecimal     | C0.A8.01.64               |
| 32-bit integer  | 3232235876                |

In the Linux kernel, IPv4 addresses are stored as `__be32` (big-endian 32-bit),
defined in `include/uapi/linux/types.h`. See `include/linux/ip.h` and
`include/uapi/linux/in.h` (struct `in_addr`).

---

## 3. Binary & Decimal Arithmetic

### Decimal → Binary Conversion

Use repeated division by 2 or the subtraction method.

**Example: Convert 172 to binary**

```
  172 ÷ 2 = 86  remainder 0   (LSB)
   86 ÷ 2 = 43  remainder 0
   43 ÷ 2 = 21  remainder 1
   21 ÷ 2 = 10  remainder 1
   10 ÷ 2 =  5  remainder 0
    5 ÷ 2 =  2  remainder 1
    2 ÷ 2 =  1  remainder 0
    1 ÷ 2 =  0  remainder 1   (MSB)

  Read remainders bottom-to-top: 10101100 = 172
```

### Binary → Decimal Conversion

**Example: 10101100₂ → decimal**

```
  Bit:    1    0    1    0    1    1    0    0
  Weight: 128  64   32   16   8    4    2    1

  = 128×1 + 64×0 + 32×1 + 16×0 + 8×1 + 4×1 + 2×0 + 1×0
  = 128   +  0   +  32  +  0   +  8  +  4  +  0  +  0
  = 172
```

### Bitwise AND — Subnet Calculation

The network address is computed by ANDing the IP with the subnet mask:

```
  IP:      192.168.10.52  = 11000000.10101000.00001010.00110100
  Mask:    255.255.255.0  = 11111111.11111111.11111111.00000000
  AND:     ─────────────────────────────────────────────────────
  Network: 192.168.10.0   = 11000000.10101000.00001010.00000000

  Rule: 0 AND anything = 0
        1 AND x = x
```

### Bitwise NOT — Wildcard / Inverse Mask

Wildcard mask = bitwise NOT of subnet mask:

```
  Mask:     255.255.255.0  = 11111111.11111111.11111111.00000000
  Wildcard: 0.0.0.255      = 00000000.00000000.00000000.11111111
            (used in ACLs, OSPF, etc.)
```

### Bitwise OR — Broadcast Address

Broadcast = network address OR wildcard mask:

```
  Network:   192.168.10.0   = 11000000.10101000.00001010.00000000
  Wildcard:  0.0.0.255      = 00000000.00000000.00000000.11111111
  OR:        ─────────────────────────────────────────────────────
  Broadcast: 192.168.10.255 = 11000000.10101000.00001010.11111111
```

---

## 4. Address Classes (Classful Addressing)

Before CIDR (1993), the IPv4 space was divided into **classes** determined by the
leading bits of the address. RFC 791 and RFC 1700.

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                    IPv4 Address Class Map                            │
  │                                                                      │
  │   0.0.0.0                                              255.255.255.255
  │   │                                                               │
  │   ├───────────── Class A ───────────┤                             │
  │   │   0.x.x.x          127.x.x.x   │                             │
  │   │   0xxxxxxx (first bit = 0)      │                             │
  │   │                                 │                             │
  │                 ├────────── Class B ──────────┤                   │
  │                 │  128.x.x.x     191.x.x.x   │                   │
  │                 │  10xxxxxx (first 2 bits)    │                   │
  │                                               │                   │
  │                            ├─── Class C ────┤ │                   │
  │                            │  192   223     │ │                   │
  │                            │  110xxxxx      │ │                   │
  │                                             │ ├─ D ─┤ ├─── E ───┤
  │                                             │ │224  │ │240  255 │
  │                                             │ │1110 │ │1111     │
  └──────────────────────────────────────────────────────────────────────┘
```

### Class Breakdown Table

| Class | First Bits | Range             | Default Mask    | Networks    | Hosts/Net         | Purpose        |
|-------|------------|-------------------|-----------------|-------------|-------------------|----------------|
| A     | 0xxx       | 0.0.0.0–127.255.255.255 | /8 (255.0.0.0) | 128 | 16,777,214 | Large orgs |
| B     | 10xx       | 128.0.0.0–191.255.255.255 | /16 (255.255.0.0) | 16,384 | 65,534 | Medium orgs |
| C     | 110x       | 192.0.0.0–223.255.255.255 | /24 (255.255.255.0) | 2,097,152 | 254 | Small nets |
| D     | 1110       | 224.0.0.0–239.255.255.255 | N/A | N/A | N/A | Multicast |
| E     | 1111       | 240.0.0.0–255.255.255.255 | N/A | N/A | N/A | Experimental |

### Class A Deep Dive

```
  Class A address format (32 bits):
  ┌──────────┬──────────────────────────────────┐
  │  Network │          Host part               │
  │  8 bits  │          24 bits                 │
  └──────────┴──────────────────────────────────┘
  bit 31                                    bit 0
       │
       └─ always 0

  First octet range: 0–127 (but 0 and 127 are reserved)
  Usable Class A: 1.0.0.0 – 126.255.255.255

  Number of Class A networks: 2^7 - 2 = 126
  Hosts per Class A network:  2^24 - 2 = 16,777,214
```

### Class B Deep Dive

```
  Class B address format:
  ┌─────────────────┬────────────────────────┐
  │   Network part  │       Host part        │
  │    16 bits      │       16 bits          │
  └─────────────────┴────────────────────────┘
  Bits 31-30 = 10

  Number of Class B networks: 2^14 = 16,384
  Hosts per Class B network:  2^16 - 2 = 65,534
```

### Class C Deep Dive

```
  Class C address format:
  ┌──────────────────────────┬─────────────┐
  │       Network part       │  Host part  │
  │        24 bits           │   8 bits    │
  └──────────────────────────┴─────────────┘
  Bits 31-29 = 110

  Number of Class C networks: 2^21 = 2,097,152
  Hosts per Class C network:  2^8 - 2 = 254
```

### Why Classful Was Abandoned

- **Inflexible**: A company needing 300 hosts got a Class B (65,534 hosts) → wasteful.
- **Route table explosion**: Millions of Class C networks inflated routing tables.
- **No efficient aggregation**.

CIDR (RFC 1519, 1993) replaced classful addressing.

---

## 5. Special & Reserved Addresses

### RFC 5735 / RFC 6890 Reserved Ranges

```
  ┌────────────────────────────────────────────────────────────────────┐
  │                   Special IPv4 Address Space                       │
  ├──────────────────────┬─────────────────────────────────────────────┤
  │ 0.0.0.0/8            │ "This" network. Used as source when no IP   │
  │                      │ assigned (DHCP request). Not routable.       │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 10.0.0.0/8           │ Private (RFC 1918). 16.7M addresses.        │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 100.64.0.0/10        │ Shared address space (RFC 6598). ISP CGN.   │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 127.0.0.0/8          │ Loopback. 127.0.0.1 most common.            │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 169.254.0.0/16       │ Link-local (APIPA). Auto-assigned when      │
  │                      │ DHCP fails. Not routable beyond link.        │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 172.16.0.0/12        │ Private (RFC 1918). 172.16–172.31.          │
  │ (172.16–172.31/16)   │ 1,048,576 addresses.                        │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 192.0.0.0/24         │ IETF Protocol Assignments.                  │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 192.0.2.0/24         │ TEST-NET-1 (RFC 5737). Documentation only.  │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 192.88.99.0/24       │ 6to4 Relay Anycast (deprecated RFC 7526).   │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 192.168.0.0/16       │ Private (RFC 1918). 65,536 addresses.       │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 198.18.0.0/15        │ Benchmarking (RFC 2544).                    │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 198.51.100.0/24      │ TEST-NET-2 (RFC 5737). Documentation.       │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 203.0.113.0/24       │ TEST-NET-3 (RFC 5737). Documentation.       │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 224.0.0.0/4          │ Multicast (Class D). 224.0.0.0–239.255.255  │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 240.0.0.0/4          │ Reserved (Class E). Experimental.           │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │ 255.255.255.255/32   │ Limited broadcast (all-ones). Non-routable.  │
  └──────────────────────┴─────────────────────────────────────────────┘
```

### RFC 1918 Private Ranges (Used in NAT environments)

```
  ┌──────────────────┬──────────────────┬────────────────────────────┐
  │ Range            │ CIDR             │ Total Addresses             │
  ├──────────────────┼──────────────────┼────────────────────────────┤
  │ 10.0.0.0 –       │ 10.0.0.0/8       │ 2^24 = 16,777,216           │
  │   10.255.255.255 │                  │                             │
  ├──────────────────┼──────────────────┼────────────────────────────┤
  │ 172.16.0.0 –     │ 172.16.0.0/12    │ 2^20 = 1,048,576            │
  │   172.31.255.255 │                  │                             │
  ├──────────────────┼──────────────────┼────────────────────────────┤
  │ 192.168.0.0 –    │ 192.168.0.0/16   │ 2^16 = 65,536               │
  │   192.168.255.255│                  │                             │
  └──────────────────┴──────────────────┴────────────────────────────┘
```

### Loopback (127.0.0.0/8)

```
  127.0.0.1 ──► kernel IP stack ──► delivered back to socket
       │                                        ▲
       └────────────────────────────────────────┘
           No NIC traversal; purely in-kernel

  Linux kernel: net/ipv4/lo.c, net/ipv4/ip_input.c
  ip_route_input_noref() identifies loopback via RTN_LOCAL.
```

### Multicast Addresses (224.0.0.0/4)

```
  ┌─────────────────────────────────────────────────────────┐
  │ 224.0.0.0/24   Link-local multicast (TTL=1, no routing) │
  │   224.0.0.1    All hosts on subnet                       │
  │   224.0.0.2    All routers on subnet                     │
  │   224.0.0.5    OSPF routers                              │
  │   224.0.0.6    OSPF DR/BDR routers                       │
  │   224.0.0.9    RIPv2                                     │
  │   224.0.0.18   VRRP                                      │
  │                                                          │
  │ 224.0.1.0/24   Internetwork multicast (globally routed) │
  │   224.0.1.1    NTP                                       │
  │                                                          │
  │ 239.0.0.0/8    Admin-scoped (RFC 2365), site-local       │
  └─────────────────────────────────────────────────────────┘
```

### Network & Broadcast Addresses

For any subnet:
- **Network address**: all host bits = 0 (e.g., 192.168.1.0)
- **Broadcast address**: all host bits = 1 (e.g., 192.168.1.255)
- These are **not assignable** to hosts.

---

## 6. Subnet Masks & CIDR Notation

### What Is a Subnet Mask?

A 32-bit value where the **leading 1-bits** identify the **network portion**
and the **trailing 0-bits** identify the **host portion**.

```
  /24 subnet mask:
  11111111.11111111.11111111.00000000
  ─────────────────────────────────────
  255      .255      .255      .0

  Network  │─────────────────│  Host │─│
  bits:           24                8
```

### CIDR (Classless Inter-Domain Routing) — RFC 1519 / RFC 4632

CIDR notation appends a **prefix length** after a `/`:

```
  192.168.1.0/24
              ^^
              Prefix length = 24 network bits

  This means subnet mask = 255.255.255.0
```

### Prefix Length ↔ Subnet Mask Conversion Table

```
  /Prefix │ Subnet Mask       │ Wildcard Mask     │ # Hosts  │ # Subnets*
  ────────┼───────────────────┼───────────────────┼──────────┼──────────
  /8      │ 255.0.0.0         │ 0.255.255.255     │ 16777214 │
  /9      │ 255.128.0.0       │ 0.127.255.255     │ 8388606  │
  /10     │ 255.192.0.0       │ 0.63.255.255      │ 4194302  │
  /11     │ 255.224.0.0       │ 0.31.255.255      │ 2097150  │
  /12     │ 255.240.0.0       │ 0.15.255.255      │ 1048574  │
  /13     │ 255.248.0.0       │ 0.7.255.255       │ 524286   │
  /14     │ 255.252.0.0       │ 0.3.255.255       │ 262142   │
  /15     │ 255.254.0.0       │ 0.1.255.255       │ 131070   │
  /16     │ 255.255.0.0       │ 0.0.255.255       │ 65534    │
  /17     │ 255.255.128.0     │ 0.0.127.255       │ 32766    │
  /18     │ 255.255.192.0     │ 0.0.63.255        │ 16382    │
  /19     │ 255.255.224.0     │ 0.0.31.255        │ 8190     │
  /20     │ 255.255.240.0     │ 0.0.15.255        │ 4094     │
  /21     │ 255.255.248.0     │ 0.0.7.255         │ 2046     │
  /22     │ 255.255.252.0     │ 0.0.3.255         │ 1022     │
  /23     │ 255.255.254.0     │ 0.0.1.255         │ 510      │
  /24     │ 255.255.255.0     │ 0.0.0.255         │ 254      │
  /25     │ 255.255.255.128   │ 0.0.0.127         │ 126      │
  /26     │ 255.255.255.192   │ 0.0.0.63          │ 62       │
  /27     │ 255.255.255.224   │ 0.0.0.31          │ 30       │
  /28     │ 255.255.255.240   │ 0.0.0.15          │ 14       │
  /29     │ 255.255.255.248   │ 0.0.0.7           │ 6        │
  /30     │ 255.255.255.252   │ 0.0.0.3           │ 2        │
  /31     │ 255.255.255.254   │ 0.0.0.1           │ 2*       │ RFC 3021 p2p
  /32     │ 255.255.255.255   │ 0.0.0.0           │ 1        │ Host route
  ────────┴───────────────────┴───────────────────┴──────────┴──────────
  * Hosts = 2^(32 - prefix) - 2  (except /31: both usable per RFC 3021)
```

### /31 Special Case (RFC 3021)

Point-to-point links often use /31 to save addresses:

```
  /31 network: 10.0.0.0/31
  Address 10.0.0.0 → Router A interface
  Address 10.0.0.1 → Router B interface
  No broadcast, no network address wasted.
```

### /32 Host Route

```
  192.168.1.1/32 — refers to exactly ONE host.
  Used in:
    - Static routes for individual hosts
    - Loopback interfaces
    - BGP next-hop specifications
    - Blackhole/null routes
```

---

## 7. Subnetting — Step-by-Step Math

### The Core Formula

Given a network block, dividing it into subnets:

```
  Borrowed bits (b) = bits stolen from host portion for subnet IDs

  New prefix length  = original prefix + b
  Number of subnets  = 2^b
  Hosts per subnet   = 2^(original_host_bits - b) - 2
  Subnet size        = 2^(32 - new_prefix)
  Block size         = subnet size (jump between subnet addresses)
```

### Example 1: Subnet 192.168.1.0/24 into 4 equal subnets

**Step 1:** Determine bits needed for 4 subnets:
```
  2^b ≥ 4  →  b = 2  (2^2 = 4)
```

**Step 2:** New prefix = 24 + 2 = /26

**Step 3:** Block size = 2^(32-26) = 2^6 = 64

**Step 4:** Enumerate subnets:
```
  ┌────────────────────────────────────────────────────────────┐
  │ Subnet│ Network Addr  │ First Host    │ Last Host     │ Broadcast     │
  ├───────┼───────────────┼───────────────┼───────────────┼───────────────┤
  │  1    │ 192.168.1.0   │ 192.168.1.1   │ 192.168.1.62  │ 192.168.1.63  │
  │  2    │ 192.168.1.64  │ 192.168.1.65  │ 192.168.1.126 │ 192.168.1.127 │
  │  3    │ 192.168.1.128 │ 192.168.1.129 │ 192.168.1.190 │ 192.168.1.191 │
  │  4    │ 192.168.1.192 │ 192.168.1.193 │ 192.168.1.254 │ 192.168.1.255 │
  └────────────────────────────────────────────────────────────────────────┘
  Each subnet: 64 addresses, 62 usable hosts
```

### Example 2: Subnet 10.0.0.0/8 into /16 subnets

```
  b = 16 - 8 = 8 bits borrowed
  Number of /16 subnets = 2^8 = 256
  Hosts per subnet = 2^16 - 2 = 65,534
  Block size = 65,536

  Subnets: 10.0.0.0/16, 10.1.0.0/16, 10.2.0.0/16, ..., 10.255.0.0/16
```

### Quick Subnetting Cheat — The "Magic Number" Method

```
  For a given mask octet value x:
  Block size (magic number) = 256 - x

  Examples:
    Mask octet = 192 → block = 256 - 192 = 64
    Mask octet = 224 → block = 256 - 224 = 32
    Mask octet = 240 → block = 256 - 240 = 16
    Mask octet = 248 → block = 256 - 248 = 8
    Mask octet = 252 → block = 256 - 252 = 4

  Then subnets increment by the block size in the "interesting octet":
    Interesting octet = octet where the mask is neither 255 nor 0
```

### Example 3: Find subnet for 172.16.35.100/20

**Step 1:** Mask = 255.255.240.0 → interesting octet = 3rd (240)

**Step 2:** Block size = 256 - 240 = 16

**Step 3:** 3rd octet multiples of 16: 0, 16, 32, 48, 64, ...

**Step 4:** 35 falls in [32, 48) → subnet is 172.16.**32**.0

```
  Network:   172.16.32.0/20
  Broadcast: 172.16.47.255
  First host: 172.16.32.1
  Last host:  172.16.47.254
  Hosts: 2^12 - 2 = 4094
```

### Verification via Binary

```
  IP:     172.16.35.100  = 10101100.00010000.00100011.01100100
  Mask:   255.255.240.0  = 11111111.11111111.11110000.00000000
                           ─────────────────────────────────────
  AND:    172.16.32.0    = 10101100.00010000.00100000.00000000
                                              ^^^^
                                         35 AND 240 = 32
```

---

## 8. VLSM — Variable Length Subnet Masking

VLSM allows **different-sized subnets** from a single address block,
assigning the right size to each segment. Requires classless routing protocols
(OSPF, EIGRP, BGP, RIPv2).

### VLSM Design Strategy

1. Sort requirements from **largest to smallest**.
2. Allocate the smallest subnet that fits each requirement.
3. Work sequentially through the address space.

### VLSM Example

**Given:** 192.168.1.0/24  
**Requirements:**
- Dept A: 100 hosts
- Dept B: 50 hosts
- Dept C: 20 hosts
- Dept D: 10 hosts
- WAN Link 1: 2 hosts
- WAN Link 2: 2 hosts

**Step 1: Sort largest → smallest**

```
  Dept A: 100 hosts → need 2^n - 2 ≥ 100 → n=7 → /25 (126 hosts)
  Dept B:  50 hosts → need 2^n - 2 ≥  50 → n=6 → /26 ( 62 hosts)
  Dept C:  20 hosts → need 2^n - 2 ≥  20 → n=5 → /27 ( 30 hosts)
  Dept D:  10 hosts → need 2^n - 2 ≥  10 → n=4 → /28 ( 14 hosts)
  WAN 1:    2 hosts → need 2^n - 2 ≥   2 → n=2 → /30 (  2 hosts)
  WAN 2:    2 hosts → same as above      → /30 (  2 hosts)
```

**Step 2: Allocate sequentially**

```
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ Subnet  │ Network Addr      │ Mask │ Hosts │ Range                        │
  ├─────────┼───────────────────┼──────┼───────┼──────────────────────────────┤
  │ Dept A  │ 192.168.1.0       │ /25  │  126  │ .1   – .126 (broadcast .127) │
  │ Dept B  │ 192.168.1.128     │ /26  │   62  │ .129 – .190 (broadcast .191) │
  │ Dept C  │ 192.168.1.192     │ /27  │   30  │ .193 – .222 (broadcast .223) │
  │ Dept D  │ 192.168.1.224     │ /28  │   14  │ .225 – .238 (broadcast .239) │
  │ WAN 1   │ 192.168.1.240     │ /30  │    2  │ .241 – .242 (broadcast .243) │
  │ WAN 2   │ 192.168.1.244     │ /30  │    2  │ .245 – .246 (broadcast .247) │
  │ (free)  │ 192.168.1.248     │ /29  │    6  │ Remaining for future use     │
  └───────────────────────────────────────────────────────────────────────────┘

  Total used: 128+64+32+16+4+4 = 248 addresses
  Remaining:  256 - 248 = 8 addresses (192.168.1.248/29)
```

### VLSM Address Space Visual

```
  192.168.1.0/24 = 256 addresses
  ┌────────────────────────────────────────────────────────────────┐
  │[──────── Dept A /25 (128) ───────────][── Dept B /26 (64) ──]  │
  │[─── Dept C /27 (32) ──][─ Dept D /28 (16) ─][W1/30][W2/30]..  │
  └────────────────────────────────────────────────────────────────┘
  0                                                              255
```

---

## 9. Supernetting & Route Aggregation

**Supernetting** (route summarization) combines multiple contiguous subnets
into one larger prefix — the **inverse of subnetting**.

### Conditions for Aggregation

1. Networks must be **contiguous** (adjacent in address space).
2. The resulting prefix must be a **power-of-two** aligned block.
3. All subnets must share the same **bits** up to the summary prefix.

### Example: Aggregate four /24s into one /22

```
  192.168.0.0/24   = 11000000.10101000.00000000.xxxxxxxx
  192.168.1.0/24   = 11000000.10101000.00000001.xxxxxxxx
  192.168.2.0/24   = 11000000.10101000.00000010.xxxxxxxx
  192.168.3.0/24   = 11000000.10101000.00000011.xxxxxxxx
                                                ^^
                                    These 2 bits vary (00,01,10,11)
  Common prefix:    11000000.10101000.000000── (22 bits)

  Summary route: 192.168.0.0/22

  Verification:
    Number of subnets aggregated = 4 = 2^2 → borrowed back 2 bits
    New prefix = 24 - 2 = 22 ✓
```

### Longest Prefix Match (LPM)

Routers use LPM when multiple routes match a destination:

```
  Routing table:
    10.0.0.0/8    via 1.1.1.1
    10.1.0.0/16   via 2.2.2.2
    10.1.2.0/24   via 3.3.3.3

  Destination: 10.1.2.50
    Matches /8:  10.0.0.0/8     ✓ (24 bits match for 10.1.2.50?)
                  → 10.x (8 bits match)
    Matches /16: 10.1.0.0/16    ✓ (16 bits match)
    Matches /24: 10.1.2.0/24    ✓ (24 bits match)

  LPM → /24 wins → forward via 3.3.3.3

  Rule: More specific (longer prefix) ALWAYS wins.
```

Linux kernel implements LPM via FIB trie: `net/ipv4/fib_trie.c`

---

## 10. IPv4 Packet Header

Defined in **RFC 791**, `include/uapi/linux/ip.h`, struct `iphdr`.

### Header Layout (Minimum 20 bytes, maximum 60 bytes)

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  ├─────┬─────┬────────────────┬────────────────────────────────────┤
  │ VER │ IHL │  DSCP  │  ECN  │         Total Length               │ 0-3
  │  4  │ 4b  │   6b   │  2b   │           16 bits                  │
  ├─────┴─────┴────────────────┼──────┬──┬────────────────────────┤
  │       Identification       │Flags │  │   Fragment Offset       │ 4-7
  │          16 bits           │  3b  │  │      13 bits            │
  ├────────────────────────────┼──────┴──┴────────────────────────┤
  │    TTL     │  Protocol     │        Header Checksum             │ 8-11
  │   8 bits   │   8 bits      │           16 bits                  │
  ├────────────┴───────────────┴────────────────────────────────────┤
  │                    Source IP Address (32 bits)                   │ 12-15
  ├─────────────────────────────────────────────────────────────────┤
  │                  Destination IP Address (32 bits)               │ 16-19
  ├─────────────────────────────────────────────────────────────────┤
  │                  Options (if IHL > 5) + Padding                 │ 20-59
  └─────────────────────────────────────────────────────────────────┘
```

### Field-by-Field Explanation

#### Version (4 bits)
```
  Always = 4 for IPv4 (binary: 0100)
  6 = IPv6
  kernel: iph->version (upper 4 bits of first byte)
```

#### IHL — Internet Header Length (4 bits)
```
  Length of header in 32-bit words (4-byte units).
  Minimum value = 5 (5 × 4 = 20 bytes, no options)
  Maximum value = 15 (15 × 4 = 60 bytes)

  Actual header bytes = IHL × 4

  kernel: iph->ihl (lower 4 bits of first byte)
  Access: ip_hdrlen(skb) = iph->ihl * 4
          Source: include/linux/ip.h
```

#### DSCP — Differentiated Services Code Point (6 bits, was ToS)
```
  Originally: Type of Service (ToS), RFC 791
  Now:        DSCP + ECN (RFC 2474, RFC 3168)

  ToS field layout (old):
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ P2 │ P1 │ P0 │ D  │ T  │ R  │ C  │ 0  │
  └────┴────┴────┴────┴────┴────┴────┴────┘
   Precedence (3b)  │ Delay│Thru│Reli│Cost│

  DSCP layout (RFC 2474):
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ D5 │ D4 │ D3 │ D2 │ D1 │ D0 │ E1 │ E0 │
  └────┴────┴────┴────┴────┴────┴────┴────┘
   ─────────── DSCP (6 bits) ────────│ECN─┤

  Common DSCP values:
    CS0  (000000) = best effort
    CS1  (001000) = scavenger
    AF11 (001010) = low drop assured forwarding
    AF41 (100010) = video
    EF   (101110) = expedited forwarding (voice)
    CS6  (110000) = network control
    CS7  (111000) = highest
```

#### ECN — Explicit Congestion Notification (2 bits, RFC 3168)
```
  00 = Non-ECN-Capable Transport (Non-ECT)
  01 = ECN Capable Transport (ECT(1))
  10 = ECN Capable Transport (ECT(0))
  11 = Congestion Experienced (CE) — set by router when congested

  ECN avoids packet drops by signaling congestion.
  TCP endpoint sees CE → reduces cwnd.
  kernel: net/ipv4/tcp_input.c, net/ipv4/ip_forward.c
```

#### Total Length (16 bits)
```
  Total size of IP packet in bytes (header + data).
  Minimum = 20 (header only)
  Maximum = 65,535 bytes

  Jumbo frames (Jumbograms, RFC 2675) use IPv6 Hop-by-Hop option;
  IPv4 doesn't support > 65,535 natively.

  For fragmented packets: each fragment has its own Total Length.
  kernel: iph->tot_len (network byte order, use ntohs())
```

#### Identification (16 bits)
```
  A 16-bit identifier assigned to each original datagram.
  All fragments of the same datagram share this ID.
  Used during reassembly to group fragments.

  Modern practice: randomized per packet for security (prevents
  idle scan attacks — Nmap -sI).
  kernel: __ip_select_ident() in net/ipv4/ip_output.c
          Uses per-CPU counters + hash for randomization (v4.1+)
```

#### Flags (3 bits)
```
  Bit 0: Reserved, must be 0 (evil bit — RFC 3514, April Fools)
  Bit 1: DF — Don't Fragment
           0 = may fragment
           1 = do NOT fragment (drop and send ICMP Type 3 Code 4 if needed)
  Bit 2: MF — More Fragments
           0 = last fragment (or not fragmented)
           1 = more fragments follow

  ┌───┬────┬────┐
  │ R │ DF │ MF │
  └───┴────┴────┘
```

#### Fragment Offset (13 bits)
```
  Offset of this fragment from start of original datagram.
  Unit = 8 bytes (64-bit granularity).

  Fragment offset (bytes) = field_value × 8

  Maximum offset = (2^13 - 1) × 8 = 65,528 bytes

  First fragment: offset = 0
  Example: datagram split into 3 fragments of 1480 bytes each:
    Fragment 1: offset=0,    len=1480, MF=1
    Fragment 2: offset=185,  len=1480, MF=1  (185 × 8 = 1480)
    Fragment 3: offset=370,  len=rest, MF=0
```

#### TTL — Time to Live (8 bits)
```
  Originally: seconds. In practice: hop count.
  Decremented by 1 at each router.
  When TTL reaches 0 → router drops packet + sends ICMP Time Exceeded.

  Default TTL values by OS:
    Linux:   64
    Windows: 128
    Cisco:   255
    macOS:   64

  TTL is used by:
    - traceroute: sends packets with TTL=1,2,3,...
    - Loop prevention in routing
    - Security: estimating OS type (TTL fingerprinting)

  kernel: iph->ttl, decremented in ip_forward() → net/ipv4/ip_forward.c
          ip_decrease_ttl() macro in include/net/ip.h
```

#### Protocol (8 bits)
```
  Identifies the upper-layer protocol encapsulated in the IP payload.

  Common values (IANA Protocol Numbers):
  ┌──────┬───────────────────────────────────────────┐
  │   1  │ ICMP                                       │
  │   2  │ IGMP (Internet Group Management Protocol)  │
  │   4  │ IP-in-IP encapsulation (IPv4 tunneling)    │
  │   6  │ TCP                                         │
  │  17  │ UDP                                         │
  │  41  │ IPv6 (6in4 tunneling)                       │
  │  47  │ GRE (Generic Routing Encapsulation)         │
  │  50  │ ESP (IPsec Encapsulating Security Payload)  │
  │  51  │ AH (IPsec Authentication Header)            │
  │  58  │ ICMPv6                                      │
  │  89  │ OSPF                                        │
  │ 132  │ SCTP                                        │
  └──────┴───────────────────────────────────────────┘

  kernel: iph->protocol
          Dispatch table: inet_protos[] in net/ipv4/protocol.c
          Registered via inet_add_protocol()
```

#### Header Checksum (16 bits)
```
  One's complement checksum of the IP header only (not payload).
  Recomputed at every router (TTL changes → checksum changes).

  Algorithm (RFC 791):
    1. Set checksum field to 0.
    2. Sum all 16-bit words in header.
    3. Add carry bits (ones' complement addition).
    4. Take bitwise complement (NOT) of the sum.

  Example calculation for a 20-byte header:
    Sum all 10 × 16-bit words.
    Carry any overflow back into low 16 bits.
    Invert.

  kernel: ip_fast_csum() in include/asm/checksum.h
          (architecture-specific: x86 uses optimized assembly)
          ip_send_check() recalculates before transmit.
```

#### Source IP Address (32 bits)
```
  IPv4 address of the sending host.
  Can be spoofed! IP has no source authentication (IPsec adds this).
  kernel: iph->saddr (__be32, big-endian)
```

#### Destination IP Address (32 bits)
```
  IPv4 address of intended recipient (unicast, multicast, or broadcast).
  kernel: iph->daddr (__be32, big-endian)
```

### IPv4 Options

When IHL > 5, options follow the fixed header. Options are rarely used in modern networks.

```
  Option format:
  ┌──────────┬──────────┬────────────────────────────────┐
  │   Type   │  Length  │           Data                  │
  │  1 byte  │  1 byte  │      (Length - 2) bytes         │
  └──────────┴──────────┴────────────────────────────────┘

  Type byte:
  ┌───┬────┬────────┐
  │ C │ CL │ Number │
  │1b │ 2b │  5b    │
  └───┴────┴────────┘
    C  = copied into fragments (1) or not (0)
    CL = class (0=control, 2=debugging)
    Number = option number

  Common Options:
  ┌──────────┬────────────────────────────────────────────┐
  │ Type 0   │ End of Option List                          │
  │ Type 1   │ No Operation (padding)                      │
  │ Type 7   │ Record Route (tracks path, max 9 hops)      │
  │ Type 68  │ Timestamp (records timestamps at each hop)  │
  │ Type 131 │ Loose Source Routing (specify some hops)    │
  │ Type 137 │ Strict Source Routing (specify all hops)    │
  └──────────┴────────────────────────────────────────────┘

  Note: Source routing is disabled on most modern routers
        (security risk — CVE exploits used it extensively).
  kernel: ip_options_compile() in net/ipv4/ip_options.c
```

### Linux Kernel iphdr Structure

```c
/* include/uapi/linux/ip.h */
struct iphdr {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u8    ihl:4,
            version:4;
#elif defined(__BIG_ENDIAN_BITFIELD)
    __u8    version:4,
            ihl:4;
#endif
    __u8    tos;
    __be16  tot_len;
    __be16  id;
    __be16  frag_off;   /* includes flags (top 3 bits) + offset (13 bits) */
    __u8    ttl;
    __u8    protocol;
    __sum16 check;
    __be32  saddr;
    __be32  daddr;
    /* options follow if ihl > 5 */
};
```

---

## 11. IP Fragmentation & Reassembly

When a datagram is larger than the **MTU (Maximum Transmission Unit)**
of a link, it must be fragmented.

### MTU Values

```
  ┌─────────────────────────────┬──────────┐
  │ Link Type                   │ MTU      │
  ├─────────────────────────────┼──────────┤
  │ Ethernet                    │ 1500 B   │
  │ Wi-Fi (802.11)              │ 2304 B   │
  │ PPPoE                       │ 1492 B   │
  │ FDDI                        │ 4352 B   │
  │ Token Ring                  │ 4464 B   │
  │ ATM (AAL5)                  │ 9180 B   │
  │ Jumbo Frames (Ethernet)     │ 9000 B   │
  │ Loopback (Linux default)    │ 65,536 B │
  │ IPv4 minimum required MTU   │ 68 B     │
  └─────────────────────────────┴──────────┘
```

### Path MTU Discovery (PMTUD) — RFC 1191

```
  Host A                   Router R               Host B
    │                          │                      │
    │──── IP packet (1500B) ───►│                      │
    │      DF bit = 1           │                      │
    │                      MTU=576                     │
    │                      Can't forward, DF=1         │
    │◄── ICMP Type=3 Code=4 ───│                      │
    │    "Frag needed, MTU=576" │                      │
    │                           │                      │
    │──── IP packet (576B) ────►│──── forward ────────►│
    │                           │                      │

  This allows hosts to discover the minimum MTU along the path
  and avoid fragmentation entirely.

  Linux default: PMTUD enabled
  sysctl: net.ipv4.ip_no_pmtu_disc
  kernel: ip_rt_frag_needed() in net/ipv4/route.c
```

### Fragmentation Process

Original datagram: 4000 bytes data + 20 bytes IP header = 4020 bytes
MTU of outgoing link: 1500 bytes

```
  Payload per fragment = MTU - IP_header_size = 1500 - 20 = 1480 bytes
  (Must be multiple of 8 for fragment offset field)

  Fragment 1:
    Total length = 1500 (20 header + 1480 data)
    Offset = 0
    MF = 1 (more fragments follow)
    ID = 12345

  Fragment 2:
    Total length = 1500 (20 header + 1480 data)
    Offset = 1480/8 = 185
    MF = 1
    ID = 12345

  Fragment 3:
    Total length = 20 + (4000 - 2960) = 20 + 1040 = 1060
    Offset = 2960/8 = 370
    MF = 0 (last fragment)
    ID = 12345
```

```
  Original:  [IP HDR|────────────────────── 4000 bytes ──────────────────────]
  After frag:
  Frag 1:    [IP HDR|────────── 1480 bytes ──────────] ID=X, Off=0,   MF=1
  Frag 2:    [IP HDR|────────── 1480 bytes ──────────] ID=X, Off=185, MF=1
  Frag 3:    [IP HDR|──── 1040 bytes ────]             ID=X, Off=370, MF=0
```

### Reassembly

```
  At the destination host:
  ┌────────────────────────────────────────────────────────────┐
  │ Fragment table (keyed by: src, dst, protocol, ID)          │
  │                                                            │
  │ On receipt of fragment:                                    │
  │   1. Look up reassembly buffer by (src, dst, proto, ID)    │
  │   2. Store fragment at its offset                          │
  │   3. Check if all fragments received                       │
  │      (MF=0 fragment seen AND no gaps in offset chain)      │
  │   4. Reassemble → pass to upper layer                      │
  │   5. Reassembly timer: 30s default (then ICMP Time Exc.)   │
  └────────────────────────────────────────────────────────────┘

  kernel: net/ipv4/ip_fragment.c
  Main function: ip_defrag() → ip_frag_reasm()
  Fragment queue: struct ipq (ipfrag_queue)
  Timeout: sysctl net.ipv4.ipfrag_time (default 30s)
  Max memory: net.ipv4.ipfrag_high_thresh
```

### Fragmentation Attacks

```
  Teardrop Attack: overlapping fragments with malformed offsets
    → kernel crash (pre-2.0.32 Linux, patched)

  Fragment flooding: fill reassembly buffer → OOM
    → mitigated by ipfrag_high_thresh limit

  Tiny Fragment Attack: TCP header split across fragments
    → first fragment too small to contain TCP flags
    → firewall bypass
    → mitigated in modern kernels by minimum fragment size check
```

---

## 12. ARP — Address Resolution Protocol

ARP (RFC 826, 1982) maps **IPv4 addresses → MAC addresses** on a local network.
It operates at the boundary between Layer 2 and Layer 3.

### Why ARP?

```
  IP routing gives us the next-hop IP address.
  Ethernet transmission requires the MAC address.

  "I know I need to send to 192.168.1.50, but what's its MAC?"
                                          ↓
                                   ARP resolves this
```

### ARP Packet Format

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  ┌─────────────────────────────────────────────────────────────────┐
  │      Hardware Type (HTYPE)      │     Protocol Type (PTYPE)    │
  │       2 bytes (1=Ethernet)      │      2 bytes (0x0800=IPv4)    │
  ├─────────────────┬───────────────┼─────────────────────────────┤
  │   HLEN (1 byte) │  PLEN (1 byte)│     Operation (2 bytes)      │
  │ HW addr length  │ Proto addr len│  1=request, 2=reply          │
  ├─────────────────┴───────────────┴─────────────────────────────┤
  │               Sender Hardware Address (SHA) — 6 bytes          │
  ├─────────────────────────────────────────────────────────────────┤
  │               Sender Protocol Address (SPA) — 4 bytes          │
  ├─────────────────────────────────────────────────────────────────┤
  │               Target Hardware Address (THA) — 6 bytes          │
  ├─────────────────────────────────────────────────────────────────┤
  │               Target Protocol Address (TPA) — 4 bytes          │
  └─────────────────────────────────────────────────────────────────┘
  Total: 28 bytes for Ethernet/IPv4 ARP
```

### ARP Request/Reply Exchange

```
  Host A (192.168.1.1)                    Host B (192.168.1.2)
  MAC: AA:BB:CC:11:22:33                  MAC: DD:EE:FF:44:55:66

  [A wants to send to 192.168.1.2]

  ARP Request (broadcast):
  ┌───────────────────────────────────────────────────┐
  │ Ethernet: Dst=FF:FF:FF:FF:FF:FF (BROADCAST)        │
  │ Src=AA:BB:CC:11:22:33                              │
  │ Type=0x0806 (ARP)                                  │
  │ ARP: "Who has 192.168.1.2? Tell 192.168.1.1"       │
  │   SHA=AA:BB:CC:11:22:33  SPA=192.168.1.1           │
  │   THA=00:00:00:00:00:00  TPA=192.168.1.2           │
  └───────────────────────────────────────────────────┘
  A ─────────────────────────────────────────────────► ALL hosts

  ARP Reply (unicast, only B replies):
  ┌───────────────────────────────────────────────────┐
  │ Ethernet: Dst=AA:BB:CC:11:22:33                    │
  │ Src=DD:EE:FF:44:55:66                              │
  │ Type=0x0806 (ARP)                                  │
  │ ARP: "192.168.1.2 is at DD:EE:FF:44:55:66"        │
  │   SHA=DD:EE:FF:44:55:66  SPA=192.168.1.2           │
  │   THA=AA:BB:CC:11:22:33  TPA=192.168.1.1           │
  └───────────────────────────────────────────────────┘
  B ─────────────────────────────────────────────────► A

  A stores B's MAC in ARP cache:
    192.168.1.2 → DD:EE:FF:44:55:66  (expires ~20 min)
```

### ARP Cache

```
  Linux ARP cache (neighbour table):
  $ ip neigh show
  192.168.1.1 dev eth0 lladdr aa:bb:cc:11:22:33 REACHABLE
  192.168.1.2 dev eth0 lladdr dd:ee:ff:44:55:66 STALE
  192.168.1.3 dev eth0 FAILED

  States:
    INCOMPLETE  → ARP sent, no reply yet
    REACHABLE   → recently verified
    STALE       → timeout, unverified but usable
    DELAY       → sending probe before STALE→PROBE
    PROBE       → unicast ARP probe sent
    FAILED      → no response
    NOARP       → ARP not needed (e.g., point-to-point)
    PERMANENT   → static entry, never expires

  kernel: net/core/neighbour.c, net/ipv4/arp.c
          struct neighbour in include/net/neighbour.h
  Sysctl: net.ipv4.neigh.eth0.base_reachable_time_ms
          net.ipv4.neigh.eth0.gc_stale_time
```

### Gratuitous ARP (GARP)

```
  A host ARPs for its own IP address.
  Uses:
    1. Duplicate IP detection: if anyone replies → conflict
    2. Cache update: after IP change, IP failover (VRRP/HSRP)
    3. Interface bring-up: update switches' MAC tables

  GARP format: ARP request where SPA == TPA (both = own IP)
  kernel: arp_send() with target = own IP
```

### Proxy ARP

```
  A router answers ARP requests on behalf of hosts on other segments.

  Network A (192.168.1.x) ──── Router ──── Network B (192.168.2.x)
                                  │
                        Proxy ARP enabled

  Host A asks "Who has 192.168.2.5?"
  Router replies with its own MAC → Host A sends to router.
  Router forwards to Network B.

  sysctl: net.ipv4.conf.eth0.proxy_arp = 1
```

### ARP Spoofing / Poisoning

```
  Attacker poisons ARP caches:
  ┌──────────────────────────────────────────────────────┐
  │  Attacker sends gratuitous ARP:                      │
  │  "192.168.1.1 (gateway) is at <attacker MAC>"       │
  │                                                      │
  │  Victims update ARP cache → send traffic to attacker│
  │                                                      │
  │  Attack: MITM, eavesdropping, session hijack         │
  │                                                      │
  │  Defense: Dynamic ARP Inspection (DAI) on switches  │
  │           arpwatch daemon on Linux                   │
  │           Static ARP entries                         │
  └──────────────────────────────────────────────────────┘
```

---

## 13. ICMP — Internet Control Message Protocol

ICMP (RFC 792) is a **helper protocol** for IPv4 — it carries error messages
and operational information. ICMP messages are encapsulated in IP packets
(Protocol = 1).

### ICMP Header

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  ┌─────────────────────┬─────────────────────┬────────────────────┐
  │        Type         │        Code         │      Checksum      │
  │       8 bits        │       8 bits        │      16 bits       │
  ├─────────────────────┴─────────────────────┴────────────────────┤
  │                 Rest of Header (4 bytes, type-dependent)        │
  ├─────────────────────────────────────────────────────────────────┤
  │        Data (variable, often original IP header + 8 bytes)      │
  └─────────────────────────────────────────────────────────────────┘
```

### ICMP Message Types

```
  Error Messages:
  ┌──────┬──────┬─────────────────────────────────────────────────┐
  │ Type │ Code │ Meaning                                         │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │  3   │  0   │ Destination Unreachable: Network unreachable    │
  │  3   │  1   │ Destination Unreachable: Host unreachable       │
  │  3   │  2   │ Destination Unreachable: Protocol unreachable   │
  │  3   │  3   │ Destination Unreachable: Port unreachable       │
  │  3   │  4   │ Destination Unreachable: Frag needed (PMTUD)    │
  │  3   │  5   │ Destination Unreachable: Source route failed    │
  │  3   │  6   │ Destination Unreachable: Network unknown        │
  │  3   │  9   │ Destination Unreachable: Network admin prohibit │
  │  3   │ 10   │ Destination Unreachable: Host admin prohibited  │
  │  3   │ 13   │ Destination Unreachable: Comm admin prohibited  │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │  4   │  0   │ Source Quench (deprecated, RFC 6633)            │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │  5   │  0   │ Redirect: Redirect for network                  │
  │  5   │  1   │ Redirect: Redirect for host                     │
  │  5   │  2   │ Redirect: Redirect for ToS and network          │
  │  5   │  3   │ Redirect: Redirect for ToS and host             │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │ 11   │  0   │ Time Exceeded: TTL exceeded in transit          │
  │ 11   │  1   │ Time Exceeded: Fragment reassembly exceeded     │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │ 12   │  0   │ Parameter Problem: Pointer to error             │
  └──────┴──────┴─────────────────────────────────────────────────┘

  Query/Informational Messages:
  ┌──────┬──────┬─────────────────────────────────────────────────┐
  │  0   │  0   │ Echo Reply (ping response)                      │
  │  8   │  0   │ Echo Request (ping)                             │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │  9   │  0   │ Router Advertisement                            │
  │ 10   │  0   │ Router Solicitation                             │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │ 13   │  0   │ Timestamp Request                               │
  │ 14   │  0   │ Timestamp Reply                                 │
  ├──────┼──────┼─────────────────────────────────────────────────┤
  │ 17   │  0   │ Address Mask Request                            │
  │ 18   │  0   │ Address Mask Reply                              │
  └──────┴──────┴─────────────────────────────────────────────────┘
```

### ICMP Echo (Ping) in Detail

```
  ICMP Type 8 (Request):
  ┌──────────┬──────────┬────────────────────┐
  │ Type = 8 │ Code = 0 │    Checksum        │
  ├──────────┴──────────┴────────────────────┤
  │ Identifier (16b)    │  Sequence (16b)    │
  ├────────────────────────────────────────────┤
  │            Data (timestamp, padding)       │
  └────────────────────────────────────────────┘

  Identifier: process ID (allows multiple pings simultaneously)
  Sequence:   incremented per echo request

  RTT = T_reply_received - T_request_sent

  kernel: net/ipv4/icmp.c → icmp_echo()
          ping socket: net/ipv4/ping.c (v3.0+, non-root ping)
```

### traceroute — Using TTL + ICMP

```
  traceroute exploits TTL decrement + ICMP Type 11:

  Probe 1: TTL=1
    A ──TTL=1──► Router1 → drops (TTL=0) → ICMP "TTL Exceeded" back to A
    A records Router1's IP and RTT

  Probe 2: TTL=2
    A ──TTL=2──► Router1 ──TTL=1──► Router2 → drops → ICMP back
    A records Router2's IP and RTT

  Continue until destination reached (ICMP Port Unreachable or Echo Reply)

  Linux traceroute uses UDP by default (to random high port)
  Windows tracert uses ICMP Echo
  Modern traceroute can use TCP (-T flag)
```

### ICMP Rate Limiting (Linux)

```
  Linux limits ICMP error generation to prevent flooding:
  sysctl net.ipv4.icmp_ratelimit       = 1000 (microseconds between)
  sysctl net.ipv4.icmp_ratemask        = 6168 (which types are rate-limited)
  kernel: icmp_global_allow() in net/ipv4/icmp.c
```

---

## 14. IPv4 Routing

### Routing Concepts

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                   IP Routing Decision Flow                       │
  │                                                                  │
  │  Incoming packet                                                 │
  │        │                                                         │
  │        ▼                                                         │
  │  [Is dest == my IP?] ──Yes──► Deliver to local process          │
  │        │                                                         │
  │        No                                                        │
  │        ▼                                                         │
  │  [ip_forward enabled?] ──No──► Drop (send ICMP Unreachable)     │
  │        │                                                         │
  │        Yes                                                       │
  │        ▼                                                         │
  │  [Lookup in FIB] ──────────────────────────────────────────┐    │
  │        │                                                    │    │
  │        ▼                                                    ▼    │
  │  [Match found?] ──Yes──► Decrement TTL ──► Rewrite headers      │
  │        │                     │                  │                │
  │        No                    │                  ▼               │
  │        ▼                     │             Forward to next-hop  │
  │  [Default route?] ──Yes──────┘                                  │
  │        │                                                         │
  │        No                                                         │
  │        ▼                                                         │
  │  Drop + ICMP Network Unreachable                                 │
  └─────────────────────────────────────────────────────────────────┘
```

### Routing Table Structure

```
  Linux routing table (ip route show):
  default via 192.168.1.1 dev eth0 proto dhcp metric 100
  192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.50
  10.0.0.0/8 via 192.168.1.254 dev eth0 metric 200

  Fields:
  ┌─────────────────────────────────────────────────────────────────┐
  │ Destination prefix │ Next-hop (gateway) │ Interface │ Metric    │
  │ 192.168.1.0/24     │ (direct, on-link)  │ eth0      │ 0        │
  │ 10.0.0.0/8         │ 192.168.1.254      │ eth0      │ 200      │
  │ 0.0.0.0/0          │ 192.168.1.1        │ eth0      │ 100      │
  └─────────────────────────────────────────────────────────────────┘

  kernel: struct fib_table, struct fib_info in include/net/ip_fib.h
          FIB (Forwarding Information Base) trie: net/ipv4/fib_trie.c
          Route cache removed in v3.6 (replaced by dst_entry per-flow)
```

### Multiple Routing Tables (iproute2 / Policy Routing)

```
  Linux supports up to 252 routing tables (+ 3 special):

  Table IDs:
    0   = unspecified
    253 = default (ip route show table default)
    254 = main    (ip route show — this is the one normally shown)
    255 = local   (kernel-managed: loopback, broadcast, local)

  Policy routing (ip rule):
  $ ip rule show
  0:      from all lookup local
  32766:  from all lookup main
  32767:  from all lookup default

  Custom policy:
  $ ip rule add from 192.168.2.0/24 table 200 priority 100
  $ ip route add default via 10.0.0.1 table 200

  Use case: multi-homing (multiple ISPs), VPN, VRF

  kernel: net/ipv4/fib_rules.c
          struct fib_rule in include/net/fib_rules.h
```

### Linux FIB (Forwarding Information Base) Architecture

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                  Linux IPv4 FIB Architecture                     │
  │                                                                  │
  │  Route lookup entry point: fib_lookup()                         │
  │  Source: net/ipv4/ip_input.c, net/ipv4/route.c                  │
  │                                                                  │
  │  fib_lookup()                                                    │
  │      │                                                           │
  │      ▼                                                           │
  │  fib_rules_lookup()   ← policy routing rules                    │
  │      │                                                           │
  │      ▼                                                           │
  │  fib_table_lookup()   ← per-table LPM trie lookup               │
  │      │                                                           │
  │      ▼                                                           │
  │  LC-trie (Level-Compressed trie)                                 │
  │      │                                                           │
  │      ▼                                                           │
  │  fib_result (outgoing interface, nexthop, scope, type, etc.)    │
  │      │                                                           │
  │      ▼                                                           │
  │  ip_mkroute_input() / ip_mkroute_output()                        │
  │  → creates dst_entry (struct rtable) for sk_buff                 │
  └──────────────────────────────────────────────────────────────────┘
```

### Static vs Dynamic Routing

#### Static Routing

```
  Manually configured routes. Simple, predictable, no overhead.
  No automatic failover.

  $ ip route add 10.0.0.0/8 via 192.168.1.254
  $ ip route add 0.0.0.0/0 via 192.168.1.1   # default route
  $ ip route add blackhole 192.168.100.0/24   # drop route
  $ ip route add unreachable 10.99.0.0/16     # ICMP unreachable
  $ ip route add prohibit 172.16.0.0/12       # ICMP prohibited
```

#### Dynamic Routing Protocols

```
  ┌────────────────────────────────────────────────────────────┐
  │ Protocol │ Type        │ Metric        │ Scope            │
  ├──────────┼─────────────┼───────────────┼──────────────────┤
  │ RIPv2    │ Distance-   │ Hop count     │ Small networks   │
  │          │ Vector      │ (max 15)      │ RFC 2453         │
  ├──────────┼─────────────┼───────────────┼──────────────────┤
  │ OSPF     │ Link-State  │ Cost (BW)     │ Enterprise IGP   │
  │          │             │               │ RFC 2328         │
  ├──────────┼─────────────┼───────────────┼──────────────────┤
  │ IS-IS    │ Link-State  │ Cost          │ ISP backbone     │
  │          │             │               │ ISO 10589        │
  ├──────────┼─────────────┼───────────────┼──────────────────┤
  │ EIGRP    │ Hybrid      │ Composite     │ Cisco networks   │
  │          │             │ (BW+delay)    │                  │
  ├──────────┼─────────────┼───────────────┼──────────────────┤
  │ BGP-4    │ Path-Vector │ AS path +     │ Internet EGP     │
  │          │             │ attributes    │ RFC 4271         │
  └──────────┴─────────────┴───────────────┴──────────────────┘

  Linux routing daemons: BIRD, FRR (Free Range Routing, formerly Quagga)
  FRR source: https://github.com/FRRouting/frr
```

### OSPF Area Hierarchy

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                       OSPF Domain                               │
  │                                                                  │
  │   ┌─────────────┐        ┌──────────────────────────────────┐  │
  │   │  Area 0     │        │          Area 1                  │  │
  │   │ (Backbone)  │        │                                  │  │
  │   │  ┌───┐ ┌───┐│        │ ┌───┐ ┌───┐ ┌───┐               │  │
  │   │  │ R1│─│ R2││───ABR──│ │ R4│─│ R5│─│ R6│               │  │
  │   │  └───┘ └───┘│        │ └───┘ └───┘ └───┘               │  │
  │   │      │      │        └──────────────────────────────────┘  │
  │   │    ┌─┴─┐   │        ┌──────────────────────────────────┐  │
  │   │    │ R3│───┼───ABR──│          Area 2                  │  │
  │   │    └───┘   │        └──────────────────────────────────┘  │
  │   └─────────────┘                                               │
  │                                                                  │
  │  ABR = Area Border Router (connects to Area 0)                  │
  │  ASBR = Autonomous System Boundary Router (external routes)     │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 15. NAT — Network Address Translation

NAT (RFC 3022) translates IP addresses (and optionally ports) as packets
pass through a router, allowing private RFC 1918 addresses to communicate
with the public internet.

### Types of NAT

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  Type           │ Description                                    │
  ├─────────────────┼────────────────────────────────────────────────┤
  │ Static NAT      │ 1:1 mapping, private↔public                   │
  │ Dynamic NAT     │ Pool of public IPs, first-come-first-served    │
  │ PAT / NAT-T /   │ Many:1 — many private IPs share one public IP │
  │ Masquerade /    │ differentiated by port numbers                 │
  │ NAPT / Overload │                                                │
  └─────────────────┴────────────────────────────────────────────────┘
```

### PAT (Port Address Translation) — Most Common

```
  Private network: 192.168.1.0/24
  Public IP: 203.0.113.1 (one IP)

  ┌──────────────────────────────────────────────────────────────────┐
  │ NAT Translation Table                                            │
  ├──────────────────────┬───────────────────────────────────────────┤
  │ Internal             │ External (translated)                     │
  │ Src:Port             │ Src:Port                                  │
  ├──────────────────────┼───────────────────────────────────────────┤
  │ 192.168.1.10:1234    │ 203.0.113.1:40001                        │
  │ 192.168.1.11:1234    │ 203.0.113.1:40002                        │
  │ 192.168.1.10:5678    │ 203.0.113.1:40003                        │
  └──────────────────────┴───────────────────────────────────────────┘

  Outbound (192.168.1.10:1234 → 8.8.8.8:53):
    Replace src IP+port → 203.0.113.1:40001
    Add to NAT table

  Inbound (8.8.8.8:53 → 203.0.113.1:40001):
    Lookup NAT table → found → replace dst to 192.168.1.10:1234
    Forward to internal host
```

### NAT Traversal Problem

```
  NAT breaks end-to-end connectivity:
  ┌────────────────────────────────────────────────────────────────┐
  │ Problem: External host cannot initiate connection to           │
  │          192.168.1.10 because:                                 │
  │          - No NAT entry exists for inbound                     │
  │          - Router doesn't know which internal host to forward to│
  │                                                                 │
  │ Solutions:                                                      │
  │  1. Port Forwarding: static entry in NAT table                 │
  │     iptables -t nat -A PREROUTING -d 203.0.113.1 -p tcp       │
  │         --dport 80 -j DNAT --to-destination 192.168.1.10:80   │
  │                                                                 │
  │  2. STUN (RFC 5389): discover public IP:port                   │
  │  3. TURN (RFC 5766): relay server                              │
  │  4. ICE (RFC 8445): combined STUN+TURN                        │
  │  5. UPnP / NAT-PMP: automatic port mapping                     │
  │  6. VPN/tunnel: bypass NAT entirely                            │
  └────────────────────────────────────────────────────────────────┘
```

### NAT in Linux — Netfilter / iptables

```
  Linux NAT uses Netfilter connection tracking (conntrack).

  Masquerade (dynamic PAT for dynamic IPs):
  $ iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

  SNAT (static public IP):
  $ iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to-source 203.0.113.1

  DNAT (port forwarding):
  $ iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
        -j DNAT --to-destination 192.168.1.10:80

  View conntrack table:
  $ conntrack -L
  tcp  6 431999 ESTABLISHED src=192.168.1.10 dst=8.8.8.8 sport=1234 dport=53 \
       src=8.8.8.8 dst=203.0.113.1 sport=53 dport=40001 [ASSURED]

  kernel: net/netfilter/nf_nat_core.c
          net/netfilter/nf_conntrack_core.c
          struct nf_conn in include/net/netfilter/nf_conntrack.h
```

### NAT and IP Checksum Recalculation

```
  When NAT modifies src/dst IP:
  1. IP header checksum must be recalculated (IP checksum covers header only)
  2. TCP/UDP checksum must be recalculated (includes pseudo-header with IPs)

  TCP/UDP pseudo-header for checksum:
  ┌────────────────────────────────────┐
  │    Source IP Address (4 bytes)     │
  ├────────────────────────────────────┤
  │  Destination IP Address (4 bytes)  │
  ├──────────┬─────────┬───────────────┤
  │  Zero    │Protocol │  TCP Length   │
  │  1 byte  │ 1 byte  │   2 bytes     │
  └──────────┴─────────┴───────────────┘

  kernel: nf_nat_ipv4_manip_pkt() handles this in net/ipv4/netfilter/nf_nat_l3proto_ipv4.c
  Checksum helpers: include/net/checksum.h, csum_tcpudp_magic()
```

---

## 16. DHCP — Dynamic Host Configuration Protocol

DHCP (RFC 2131, RFC 2132) automatically assigns IP addresses and network
configuration to clients. It operates over UDP (client: port 68, server: port 67).

### DHCP Message Flow (DORA)

```
  Client                              DHCP Server
  (no IP yet)                         (192.168.1.1)

  1. DISCOVER (broadcast)
  ─────────────────────────────────────────────────►
  Src: 0.0.0.0:68    Dst: 255.255.255.255:67
  "I need an IP address! I'm MAC aa:bb:cc:dd:ee:ff"

  2. OFFER (broadcast or unicast)
  ◄─────────────────────────────────────────────────
  Src: 192.168.1.1:67   Dst: 255.255.255.255:68
  "I offer you 192.168.1.50, lease=24h, GW=192.168.1.1"

  3. REQUEST (broadcast)
  ─────────────────────────────────────────────────►
  Src: 0.0.0.0:68    Dst: 255.255.255.255:67
  "I'll take 192.168.1.50 from server 192.168.1.1"
  (broadcast so OTHER servers see the decision)

  4. ACK (broadcast or unicast)
  ◄─────────────────────────────────────────────────
  Src: 192.168.1.1:67   Dst: 255.255.255.255:68
  "Confirmed. 192.168.1.50 is yours for 86400 seconds"

  Client now configures:
    IP: 192.168.1.50/24
    Gateway: 192.168.1.1
    DNS: 8.8.8.8
    Lease: 86400s
```

### DHCP Packet Format

```
  ┌────────────────────────────────────────────────────────┐
  │ op (1B) │ htype(1B) │ hlen(1B) │ hops(1B)             │
  ├─────────┴───────────┴──────────┴──────────────────────┤
  │                   xid (4 bytes) — transaction ID       │
  ├─────────────────────────────────────────────────────────┤
  │    secs (2B)    │            flags (2B)                 │
  ├─────────────────┴─────────────────────────────────────┤
  │              ciaddr (4B) — client IP (if known)        │
  ├─────────────────────────────────────────────────────────┤
  │              yiaddr (4B) — your IP (offered IP)        │
  ├─────────────────────────────────────────────────────────┤
  │              siaddr (4B) — server IP                   │
  ├─────────────────────────────────────────────────────────┤
  │              giaddr (4B) — relay agent IP              │
  ├─────────────────────────────────────────────────────────┤
  │        chaddr (16B) — client MAC + padding              │
  ├─────────────────────────────────────────────────────────┤
  │              sname (64B) — server hostname              │
  ├─────────────────────────────────────────────────────────┤
  │              file (128B) — boot filename               │
  ├─────────────────────────────────────────────────────────┤
  │              options (variable) — "magic cookie" first  │
  │              = 99.130.83.99 (0x63825363)                │
  └─────────────────────────────────────────────────────────┘

  op: 1=BOOTREQUEST (client→server), 2=BOOTREPLY (server→client)
  htype: 1=Ethernet
  hlen: 6 (MAC address length)
```

### DHCP Options (RFC 2132)

```
  Option format:
  ┌──────────┬──────────┬────────────────────────┐
  │  Code    │  Length  │         Value          │
  │  1 byte  │  1 byte  │     Length bytes       │
  └──────────┴──────────┴────────────────────────┘

  Key options:
  ┌──────┬────────────────────────────────────────┐
  │   1  │ Subnet Mask                             │
  │   3  │ Router (Default Gateway)                │
  │   6  │ Domain Name Servers (DNS)               │
  │  12  │ Hostname                                │
  │  15  │ Domain Name                             │
  │  28  │ Broadcast Address                       │
  │  42  │ NTP Servers                             │
  │  43  │ Vendor-Specific Info                    │
  │  50  │ Requested IP Address (in DISCOVER/REQ)  │
  │  51  │ Lease Time (seconds)                    │
  │  53  │ DHCP Message Type                       │
  │      │  1=DISCOVER,2=OFFER,3=REQUEST,4=DECLINE │
  │      │  5=ACK,6=NAK,7=RELEASE,8=INFORM         │
  │  54  │ Server Identifier (server's IP)         │
  │  55  │ Parameter Request List (from client)    │
  │  58  │ Renewal Time (T1, default 50% of lease) │
  │  59  │ Rebinding Time (T2, default 87.5%)      │
  │  60  │ Vendor Class Identifier                 │
  │  61  │ Client Identifier                       │
  │  66  │ TFTP Server Name                        │
  │  67  │ Bootfile Name (PXE)                     │
  │  82  │ Relay Agent Information                 │
  │ 255  │ End                                     │
  └──────┴────────────────────────────────────────┘
```

### DHCP Lease Renewal

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                      DHCP Lease Lifecycle                        │
  │                                                                  │
  │  0%        50%       87.5%              100%                     │
  │  │          │          │                  │                      │
  │  ├──────────┼──────────┼──────────────────┤                     │
  │  │  BOUND   │ RENEWING │  REBINDING       │ EXPIRED              │
  │                                                                  │
  │  T1 (50%)  → Unicast renewal request to original server         │
  │  T2 (87.5%)→ Broadcast request to ANY server (rebinding)        │
  │  T3 (100%) → Lease expired → restart DORA                       │
  └──────────────────────────────────────────────────────────────────┘
```

### DHCP Relay Agent

```
  DHCP is broadcast-based. Routers don't forward broadcasts.
  Relay agents (DHCP helper) solve this for multi-subnet scenarios.

  Client          Relay (Router)          DHCP Server
    │                    │                     │
    │──DISCOVER─────────►│                     │
    │ broadcast          │                     │
    │                    │──DISCOVER──────────►│
    │                    │ unicast to DHCP server
    │                    │ giaddr = relay's IP  │
    │                    │                     │
    │                    │◄──OFFER─────────────│
    │◄──OFFER────────────│                     │

  giaddr field used by server to determine correct subnet/pool.
  Router config: ip helper-address <dhcp-server-ip>
```

---

## 17. IPv4 in the Linux Kernel

### Source Tree Layout

```
  linux/
  ├── net/
  │   └── ipv4/
  │       ├── af_inet.c         ← inet socket creation, bind, connect
  │       ├── ip_input.c        ← ip_rcv(), ip_local_deliver()
  │       ├── ip_output.c       ← ip_output(), ip_xmit()
  │       ├── ip_forward.c      ← ip_forward(), TTL handling
  │       ├── ip_fragment.c     ← fragmentation & reassembly
  │       ├── ip_options.c      ← IP options parsing
  │       ├── route.c           ← routing cache, dst_entry
  │       ├── fib_trie.c        ← FIB LC-trie implementation
  │       ├── fib_rules.c       ← policy routing rules
  │       ├── fib_frontend.c    ← FIB management interface
  │       ├── arp.c             ← ARP protocol
  │       ├── icmp.c            ← ICMP implementation
  │       ├── tcp.c             ← TCP main (part of TCP stack)
  │       ├── tcp_input.c       ← TCP receive path
  │       ├── tcp_output.c      ← TCP transmit path
  │       ├── udp.c             ← UDP implementation
  │       ├── igmp.c            ← IGMP (multicast group management)
  │       ├── inet_hashtables.c ← socket lookup tables
  │       ├── raw.c             ← raw sockets
  │       ├── devinet.c         ← per-device IPv4 settings
  │       ├── ipmr.c            ← multicast routing
  │       ├── sysctl_net_ipv4.c ← /proc/sys/net/ipv4/ knobs
  │       └── netfilter/
  │           ├── iptable_filter.c
  │           ├── iptable_nat.c
  │           └── nf_nat_l3proto_ipv4.c
  │
  ├── include/
  │   ├── linux/
  │   │   ├── ip.h              ← struct iphdr
  │   │   ├── icmp.h            ← struct icmphdr
  │   │   └── in.h              ← struct in_addr, IPPROTO_*, IN_*
  │   ├── uapi/linux/
  │   │   ├── ip.h              ← iphdr (userspace-visible)
  │   │   ├── in.h              ← INADDR_*, sockaddr_in
  │   │   └── route.h           ← RTN_*, routing flags
  │   └── net/
  │       ├── ip.h              ← ip_options, ip_local_out() etc.
  │       ├── route.h           ← struct rtable, dst_entry
  │       ├── ip_fib.h          ← FIB structures
  │       └── neighbour.h       ← ARP/neighbour cache
  └── Documentation/
      └── networking/
          ├── ip-sysctl.rst     ← all net.ipv4.* sysctls
          ├── fib_trie.txt
          └── multiqueue.rst
```

### IP Receive Path (ip_rcv)

```
  NIC DMA ──► sk_buff allocated ──► netif_receive_skb()
                                         │
                                         ▼
                              __netif_receive_skb_core()
                                         │
                              Protocol dispatch (ETH_P_IP)
                                         │
                                         ▼
                                     ip_rcv()           ← net/ipv4/ip_input.c
                                         │
                              ┌──────────┴──────────┐
                              │ Sanity checks:       │
                              │  - version == 4      │
                              │  - ihl >= 5          │
                              │  - tot_len valid     │
                              │  - header checksum   │
                              └──────────┬──────────┘
                                         │
                              NF_HOOK(PREROUTING)    ← Netfilter hook
                                         │
                                         ▼
                               ip_rcv_finish()
                                         │
                              ┌──────────┴──────────┐
                              │  ip_route_input()    │  ← FIB lookup
                              │  determine:          │
                              │   - local delivery   │
                              │   - forward          │
                              │   - drop             │
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┼──────────────────┐
                         ▼               ▼                   ▼
                  LOCAL INPUT       ip_forward()         drop
                  ip_local_deliver()      │
                         │          NF_HOOK(FORWARD)
                         │               │
                  NF_HOOK(INPUT)     ip_output()
                         │               │
                  deliver to        NF_HOOK(POSTROUTING)
                  socket/protocol        │
                                    dev_queue_xmit()
```

### IP Transmit Path

```
  User space write()
        │
        ▼
  sock_sendmsg() → inet_sendmsg() → tcp_sendmsg()/udp_sendmsg()
        │
        ▼
  ip_queue_xmit() / ip_send_skb()
        │
        ▼
  ip_local_out()
        │
  NF_HOOK(OUTPUT)
        │
        ▼
  ip_output()
        │
  NF_HOOK(POSTROUTING)
        │
        ▼
  ip_finish_output()
        │
        ├─── MTU check → ip_fragment() if needed
        │
        ▼
  ip_finish_output2()
        │
  neigh_output() → ARP lookup → Ethernet header
        │
        ▼
  dev_queue_xmit() → NIC driver → wire
```

### sk_buff and IPv4

```c
/* core data structure for network packets */
/* include/linux/skbuff.h */
struct sk_buff {
    /* ... */
    struct net_device   *dev;      /* incoming/outgoing device */
    sk_buff_data_t      transport_header;  /* TCP/UDP header offset */
    sk_buff_data_t      network_header;    /* IP header offset */
    sk_buff_data_t      mac_header;        /* Ethernet header offset */
    /* ... */
    __be16              protocol;  /* ETH_P_IP = 0x0800 */
    /* ... */
};

/* Accessing IP header from skb: */
struct iphdr *iph = ip_hdr(skb);   /* uses skb->network_header */

/* net/ipv4/ip_input.c - key call: */
static int ip_rcv_finish(struct net *net, struct sock *sk,
                          struct sk_buff *skb) {
    const struct iphdr *iph = ip_hdr(skb);
    /* route lookup fills in skb_dst(skb) */
    if (!skb_valid_dst(skb)) {
        ret = ip_route_input_noref(skb, iph->daddr, iph->saddr,
                                   iph->tos, skb->dev);
    }
    return dst_input(skb);  /* calls input handler from dst_entry */
}
```

### Important sysctl Parameters (net.ipv4.*)

```
  Forwarding:
    net.ipv4.ip_forward = 0|1
    net.ipv4.conf.all.forwarding = 0|1
    net.ipv4.conf.eth0.forwarding = 0|1

  ICMP:
    net.ipv4.icmp_echo_ignore_all = 0|1
    net.ipv4.icmp_echo_ignore_broadcasts = 1
    net.ipv4.icmp_ratelimit = 1000  (µs between error ICMP)
    net.ipv4.icmp_ratemask = 6168

  Security:
    net.ipv4.conf.all.rp_filter = 1   (reverse path filter — drop spoofed)
    net.ipv4.conf.all.accept_redirects = 0
    net.ipv4.conf.all.send_redirects = 0
    net.ipv4.conf.all.accept_source_route = 0
    net.ipv4.tcp_syncookies = 1       (SYN flood protection)

  ARP:
    net.ipv4.conf.all.arp_announce = 2
    net.ipv4.conf.all.arp_ignore = 1
    net.ipv4.neigh.eth0.gc_stale_time = 60

  Fragmentation:
    net.ipv4.ipfrag_time = 30
    net.ipv4.ipfrag_high_thresh = 4194304  (bytes, 4MB)
    net.ipv4.ipfrag_low_thresh = 3145728

  TCP:
    net.ipv4.tcp_rmem = 4096 87380 6291456
    net.ipv4.tcp_wmem = 4096 16384 4194304
    net.ipv4.tcp_timestamps = 1
    net.ipv4.tcp_window_scaling = 1
    net.ipv4.tcp_sack = 1

  Source: Documentation/networking/ip-sysctl.rst
```

---

## 18. Socket Layer & IPv4

### IPv4 Socket Address Structure

```c
/* include/uapi/linux/in.h */
struct sockaddr_in {
    __kernel_sa_family_t  sin_family;   /* AF_INET */
    __be16                sin_port;     /* port in network byte order */
    struct in_addr        sin_addr;     /* IPv4 address */
    unsigned char         __pad[8];    /* padding to sockaddr size */
};

struct in_addr {
    __be32 s_addr;  /* 32-bit IPv4 address, network byte order */
};
```

### Byte Order Macros

```c
/* include/uapi/linux/byteorder/little_endian.h */
/* htonl = host-to-network long (32-bit) */
/* htons = host-to-network short (16-bit) */
/* ntohl = network-to-host long */
/* ntohs = network-to-host short */

/* On little-endian (x86): htonl() swaps bytes */
/* On big-endian (MIPS, SPARC): htonl() is no-op */

uint32_t ip  = htonl(0xC0A80101);  /* 192.168.1.1 in network order */
uint16_t port = htons(80);
```

### Raw Socket — Send IPv4 Packet

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/ip.h>

/* Create raw socket (requires CAP_NET_RAW) */
int fd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);

/* IP_HDRINCL = we supply the IP header ourselves */
int one = 1;
setsockopt(fd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));

/* Build IP header */
struct iphdr iph = {
    .version  = 4,
    .ihl      = 5,
    .tos      = 0,
    .tot_len  = htons(sizeof(struct iphdr) + payload_len),
    .id       = htons(0x1234),
    .frag_off = htons(IP_DF),         /* Don't Fragment */
    .ttl      = 64,
    .protocol = IPPROTO_TCP,
    .check    = 0,                    /* kernel fills if 0 with IP_HDRINCL */
    .saddr    = inet_addr("192.168.1.10"),
    .daddr    = inet_addr("8.8.8.8"),
};
```

### Socket Options for IPv4

```c
/* Level: IPPROTO_IP */
IP_TTL            /* get/set TTL for outgoing packets */
IP_TOS            /* get/set ToS/DSCP byte */
IP_HDRINCL        /* include IP header in send data */
IP_OPTIONS        /* set IP options */
IP_RECVOPTS       /* receive IP options */
IP_PKTINFO        /* receive pktinfo (src addr, interface) */
IP_RECVTTL        /* receive TTL of incoming packet */
IP_RECVTOS        /* receive ToS of incoming packet */
IP_MTU            /* get current PMTU */
IP_MTU_DISCOVER   /* PMTUD behavior */
IP_MULTICAST_TTL  /* TTL for multicast packets */
IP_MULTICAST_LOOP /* loopback multicast to sender */
IP_ADD_MEMBERSHIP /* join multicast group */
IP_DROP_MEMBERSHIP/* leave multicast group */
IP_BIND_ADDRESS_NO_PORT  /* bind addr without port (v4.2+) */
IP_TRANSPARENT    /* transparent proxy */
IP_FREEBIND       /* bind to non-local address */
```

---

## 19. Netfilter & iptables with IPv4

### Netfilter Hook Points

```
  ┌──────────────────────────────────────────────────────────────────┐
  │              Netfilter IPv4 Hook Architecture                    │
  │                                                                  │
  │     NIC RX                                               NIC TX  │
  │       │                                                    ▲     │
  │       ▼                                                    │     │
  │  ┌─────────┐                                         ┌─────────┐│
  │  │PREROUTING│                                        │POSTROUTING│
  │  │(NF_IP_  │                                        │(NF_IP_  │ │
  │  │PRE_ROUT)│                                        │POST_ROUT)│ │
  │  └────┬────┘                                        └────▲────┘ │
  │       │                                                   │     │
  │       ├──── local? ──────────────────────────────────────┤     │
  │       │                                                   │     │
  │       │   ┌──────┐                               ┌──────┐│     │
  │       └──►│INPUT │                               │OUTPUT ││     │
  │           │(NF_IP│                               │(NF_IP ││     │
  │           │_LOCAL│                               │_LOCAL ││     │
  │           │_IN)  │                               │_OUT)  ││     │
  │           └──┬───┘                               └───▲───┘│     │
  │              │                                       │     │     │
  │              ▼                                       │     │     │
  │         Local process                         Local process│     │
  │                                                             │     │
  │       │ (forward)                                          │     │
  │       ▼                                                    │     │
  │  ┌──────────┐                                              │     │
  │  │ FORWARD  │ ────────────────────────────────────────────►│     │
  │  │(NF_IP_   │                                              │     │
  │  │ FORWARD) │                                              │     │
  │  └──────────┘                                              │     │
  └──────────────────────────────────────────────────────────────────┘
```

### iptables Tables and Chains

```
  iptables has 5 tables, each with specific chains:

  ┌──────────┬───────────────────────────────────────────────────────┐
  │ Table    │ Chains (built-in)       │ Purpose                    │
  ├──────────┼─────────────────────────┼────────────────────────────┤
  │ raw      │ PREROUTING, OUTPUT      │ Connection tracking bypass  │
  ├──────────┼─────────────────────────┼────────────────────────────┤
  │ mangle   │ PREROUTING, INPUT,      │ Packet modification        │
  │          │ FORWARD, OUTPUT,        │ (TTL, ToS, MARK)          │
  │          │ POSTROUTING             │                            │
  ├──────────┼─────────────────────────┼────────────────────────────┤
  │ nat      │ PREROUTING,             │ Address translation        │
  │          │ INPUT (v3.7+),          │                            │
  │          │ OUTPUT,                 │                            │
  │          │ POSTROUTING             │                            │
  ├──────────┼─────────────────────────┼────────────────────────────┤
  │ filter   │ INPUT, FORWARD, OUTPUT  │ Packet filtering (default) │
  ├──────────┼─────────────────────────┼────────────────────────────┤
  │ security │ INPUT, FORWARD, OUTPUT  │ SELinux/MAC labeling       │
  └──────────┴─────────────────────────┴────────────────────────────┘

  Processing order at each hook:
  raw → mangle → nat → filter → security
```

### Packet Flow Through Tables

```
  Incoming packet for LOCAL PROCESS:
  NIC → raw:PREROUTING → mangle:PREROUTING → nat:PREROUTING
     → [routing decision: local]
     → mangle:INPUT → nat:INPUT → filter:INPUT → security:INPUT
     → socket

  Outgoing packet from LOCAL PROCESS:
  socket → raw:OUTPUT → mangle:OUTPUT → nat:OUTPUT → filter:OUTPUT
         → security:OUTPUT
         → [routing decision]
         → mangle:POSTROUTING → nat:POSTROUTING
         → NIC

  FORWARDED packet:
  NIC → raw:PREROUTING → mangle:PREROUTING → nat:PREROUTING
      → [routing decision: forward]
      → mangle:FORWARD → filter:FORWARD → security:FORWARD
      → mangle:POSTROUTING → nat:POSTROUTING
      → NIC
```

### Common iptables Rules

```bash
# View rules
iptables -L -n -v --line-numbers
iptables -t nat -L -n -v

# Default policies (DROP everything unless allowed)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow established/related (stateful)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# Block specific IP
iptables -A INPUT -s 192.168.100.5 -j DROP

# Rate limit ICMP (anti-ping-flood)
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m limit --limit 1/s --limit-burst 5 -j ACCEPT

# SNAT (NAT with static public IP)
iptables -t nat -A POSTROUTING -o eth0 \
    -s 192.168.1.0/24 -j SNAT --to-source 203.0.113.1

# Port forwarding
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j DNAT --to-destination 192.168.1.10:8080

# Mark packet (for policy routing)
iptables -t mangle -A PREROUTING -p tcp --dport 443 -j MARK --set-mark 100

# Log and drop
iptables -A INPUT -j LOG --log-prefix "DROPPED: " --log-level 4
iptables -A INPUT -j DROP
```

### nftables (Modern Replacement for iptables)

```
  nftables (kernel >= 3.13) replaces iptables/ip6tables/arptables/ebtables.

  # Create a basic nftables firewall:
  nft add table inet filter
  nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
  nft add rule inet filter input ct state established,related accept
  nft add rule inet filter input iif lo accept
  nft add rule inet filter input tcp dport 22 accept
  nft add rule inet filter input tcp dport { 80, 443 } accept

  # View rules
  nft list ruleset

  kernel: net/netfilter/nf_tables_core.c
          net/netfilter/nft_*.c
```

---

## 20. IPv4 Address Exhaustion & IPv6 Transition

### Address Exhaustion Timeline

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                  IPv4 Exhaustion Timeline                        │
  │                                                                  │
  │  1981  RFC 791 defines IPv4 — 4.3B addresses seemed "enough"    │
  │  1993  CIDR introduced — slows exhaustion                        │
  │  1994  RFC 1918 private addresses + NAT — major mitigation       │
  │  1996  IPv6 spec (RFC 1884/2460) published                       │
  │  2011  IANA central pool exhausted (Feb 3, 2011)                 │
  │  2011  APNIC (Asia-Pacific) exhausted (Apr 15, 2011)             │
  │  2012  RIPE NCC (Europe) enters last /8 policy                   │
  │  2014  LACNIC (Latin America) exhausted                          │
  │  2015  ARIN (North America) exhausted (Sep 24, 2015)             │
  │  2017  AFRINIC runs out of large blocks                          │
  │  2019  RIPE NCC fully exhausted (Nov 25, 2019)                   │
  │  Now   IPv4 addresses only available via transfer market          │
  └─────────────────────────────────────────────────────────────────┘
```

### Mitigation Technologies

```
  1. RFC 1918 + NAT: ~1M private networks share each public IP
  2. CIDR: efficient allocation, no classful waste
  3. CGN/LSN (Carrier-Grade NAT, RFC 6888): ISPs NAT multiple customers
     behind one public IP — "double NAT"
     Uses 100.64.0.0/10 (RFC 6598) shared address space
  4. IPv4 address markets: addresses are bought/sold
     e.g., Microsoft bought Nokia's /8 for $7.5M (2011)
```

### IPv4-IPv6 Transition Mechanisms

```
  ┌────────────────────────────────────────────────────────────────┐
  │ Mechanism      │ Description                                   │
  ├────────────────┼───────────────────────────────────────────────┤
  │ Dual-Stack     │ Run IPv4 and IPv6 simultaneously               │
  │ (RFC 4213)     │ Host/router has both addresses                 │
  │                │ Most common today                              │
  ├────────────────┼───────────────────────────────────────────────┤
  │ 6in4 (RFC 4213)│ IPv6 packets tunneled in IPv4 (proto 41)      │
  │                │ Static tunnels between dual-stack nodes        │
  ├────────────────┼───────────────────────────────────────────────┤
  │ 6to4 (RFC 3056)│ Auto-tunneling using 2002::/16 prefix         │
  │                │ Deprecated (RFC 7526) — performance issues     │
  ├────────────────┼───────────────────────────────────────────────┤
  │ Teredo         │ IPv6 over UDP/IPv4 through NAT                 │
  │ (RFC 4380)     │ Uses 2001::/32 prefix                         │
  ├────────────────┼───────────────────────────────────────────────┤
  │ DS-Lite        │ IPv4 in IPv6 tunnel (for ISPs)                 │
  │ (RFC 6333)     │ Customer gets IPv6; ISP does IPv4 NAT          │
  ├────────────────┼───────────────────────────────────────────────┤
  │ MAP-E          │ Mapping of Address and Port Encapsulation       │
  │ (RFC 7597)     │ Stateless NAT64 variant                        │
  ├────────────────┼───────────────────────────────────────────────┤
  │ NAT64 (RFC6146)│ IPv6-only clients talk to IPv4 servers         │
  │ + DNS64        │ DNS64 synthesizes AAAA from A records          │
  │ (RFC 6147)     │ NAT64 translates IPv6↔IPv4 packets             │
  └────────────────┴───────────────────────────────────────────────┘
```

### Happy Eyeballs (RFC 8305)

```
  Modern clients use "Happy Eyeballs" to choose IPv4 or IPv6:

  Client → DNS: query A and AAAA simultaneously
  If AAAA arrives first:
    Try IPv6 connection
    If no response in 250ms: try IPv4 in parallel
    Use whichever connects first

  This ensures fast fallback when IPv6 is broken.
  Linux: getaddrinfo() with AI_ADDRCONFIG
```

---

## 21. Debugging IPv4 on Linux

### Essential Tools

```bash
# ── Address & Interface ──────────────────────────────────────────
ip addr show                # show all addresses
ip addr show dev eth0       # show eth0 addresses
ip link show                # link layer state

# ── Routing ──────────────────────────────────────────────────────
ip route show               # main routing table
ip route show table all     # all routing tables
ip route get 8.8.8.8        # which route matches destination
ip rule show                # policy routing rules

# ── ARP / Neighbours ─────────────────────────────────────────────
ip neigh show               # ARP table
arp -n                      # legacy ARP table
arping -I eth0 192.168.1.1  # ARP request for specific IP

# ── Connectivity ─────────────────────────────────────────────────
ping -c 4 8.8.8.8           # ICMP echo test
ping -s 1472 -M do 8.8.8.8  # MTU test (1472 + 28 = 1500)
traceroute 8.8.8.8          # trace path (UDP)
traceroute -I 8.8.8.8       # trace path (ICMP)
traceroute -T -p 80 8.8.8.8 # trace path (TCP)
mtr 8.8.8.8                 # live traceroute

# ── Socket / Connection state ────────────────────────────────────
ss -tunapw                  # all sockets
ss -tnp state established   # established TCP
ss -s                       # summary

# ── Packet Capture ───────────────────────────────────────────────
tcpdump -i eth0 -n ip                       # capture all IPv4
tcpdump -i eth0 host 192.168.1.1            # capture for specific host
tcpdump -i eth0 'icmp'                      # ICMP only
tcpdump -i eth0 'tcp port 80'               # HTTP traffic
tcpdump -i eth0 -w /tmp/cap.pcap            # save to file

# ── NAT / Conntrack ──────────────────────────────────────────────
conntrack -L                # active connection table
conntrack -E                # live events
conntrack -S                # statistics

# ── Netfilter ────────────────────────────────────────────────────
iptables -L -n -v           # filter rules
iptables -t nat -L -n -v    # NAT rules
nft list ruleset            # nftables rules

# ── Network Statistics ───────────────────────────────────────────
ip -s link show eth0        # interface stats
netstat -s                  # protocol statistics (legacy)
ss -s                       # socket summary
cat /proc/net/snmp          # SNMP-style stats
cat /proc/net/netstat       # extended stats
```

### Kernel Tracing — ftrace for IPv4

```bash
# Trace ip_rcv function calls
echo ip_rcv > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace_pipe

# Trace entire IP receive path with function_graph
echo ip_rcv > /sys/kernel/debug/tracing/set_graph_function
echo function_graph > /sys/kernel/debug/tracing/current_tracer
cat /sys/kernel/debug/tracing/trace_pipe
```

### eBPF / bpftrace for IPv4 Debugging

```bash
# Trace every IP packet with src/dst
bpftrace -e '
kprobe:ip_rcv {
    $skb = (struct sk_buff *)arg1;
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    printf("src=%u.%u.%u.%u dst=%u.%u.%u.%u proto=%d\n",
        ($iph->saddr >> 0) & 0xFF,
        ($iph->saddr >> 8) & 0xFF,
        ($iph->saddr >> 16) & 0xFF,
        ($iph->saddr >> 24) & 0xFF,
        ($iph->daddr >> 0) & 0xFF,
        ($iph->daddr >> 8) & 0xFF,
        ($iph->daddr >> 16) & 0xFF,
        ($iph->daddr >> 24) & 0xFF,
        $iph->protocol);
}'

# Count packets by destination IP
bpftrace -e '
kprobe:ip_rcv {
    $skb = (struct sk_buff *)arg1;
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    @[ntop(AF_INET, &$iph->daddr)] = count();
}
interval:s:5 { print(@); clear(@); }'

# Monitor ARP requests
bpftrace -e '
kprobe:arp_rcv {
    printf("ARP packet received on pid=%d\n", pid);
}'
```

### /proc/net Virtual Files

```
  /proc/net/
  ├── arp              ← ARP cache (same as ip neigh show)
  ├── dev              ← interface stats (RX/TX bytes, errors)
  ├── fib_trie         ← FIB trie dump (routing table internals)
  ├── fib_triestat     ← FIB trie statistics
  ├── if_inet6         ← IPv6 addresses (not IPv4, for reference)
  ├── igmp             ← IGMP group memberships
  ├── ip_conntrack     ← conntrack table (legacy, use conntrack -L)
  ├── netstat          ← extended TCP stats
  ├── route            ← routing table (legacy, use ip route)
  ├── rt_cache         ← route cache (informational, v3.6+)
  ├── snmp             ← IP/ICMP/TCP/UDP MIB counters
  ├── sockstat         ← socket usage summary
  ├── tcp              ← active TCP sockets
  ├── udp              ← active UDP sockets
  └── raw              ← raw sockets
```

### MTU Debugging

```bash
# Find path MTU to a destination
# Method 1: ping with DF bit set, incrementing sizes
ping -c 1 -s 1472 -M do 8.8.8.8   # 1472+28=1500 (Ethernet)
ping -c 1 -s 1464 -M do 8.8.8.8   # 1464+28=1492 (PPPoE)
# If "Frag needed" ICMP comes back → reduce size

# Method 2: tracepath (does PMTUD automatically)
tracepath 8.8.8.8

# Method 3: ip route show with pmtu
ip route get 8.8.8.8
# Shows: cache expires ... mtu 1500

# Force MTU on interface
ip link set eth0 mtu 1400

# TCP MSS clamping (for PPPoE/VPN)
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
    -j TCPMSS --clamp-mss-to-pmtu
```

---

## Summary: IPv4 Concept Map

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    IPv4 Complete Concept Map                        │
  │                                                                     │
  │  ADDRESSING                                                         │
  │  ┌──────────────────────────────────────────┐                      │
  │  │ 32-bit, dotted decimal, 4.3B total        │                      │
  │  │ Classes A/B/C (historic) → CIDR (modern)  │                      │
  │  │ Subnetting: borrow bits, block size=2^n   │                      │
  │  │ VLSM: right-size each subnet              │                      │
  │  │ Special: private, loopback, multicast...  │                      │
  │  └──────────────────────────────────────────┘                      │
  │                                                                     │
  │  PACKET HEADER                                                      │
  │  ┌──────────────────────────────────────────┐                      │
  │  │ Ver│IHL│DSCP/ECN│TotLen│ID│Flags│FragOff│                      │
  │  │ TTL│Proto│Checksum│SrcIP│DstIP│Options   │                      │
  │  └──────────────────────────────────────────┘                      │
  │                                                                     │
  │  SUPPORTING PROTOCOLS                                               │
  │  ARP: IP→MAC resolution  │ ICMP: errors & diagnostics              │
  │  DHCP: auto-config        │ IGMP: multicast group mgmt             │
  │                                                                     │
  │  ROUTING                                                            │
  │  FIB trie (LPM) → next-hop → ARP → Ethernet frame                  │
  │  Static | RIP | OSPF | IS-IS | EIGRP | BGP                         │
  │                                                                     │
  │  SERVICES                                                           │
  │  NAT/PAT: share public IPs (RFC 1918 + conntrack)                  │
  │  Fragmentation: split at MTU, reassemble at destination             │
  │  PMTUD: discover path MTU with DF bit + ICMP Type3/Code4           │
  │                                                                     │
  │  LINUX KERNEL PATHS                                                 │
  │  RX: ip_rcv→Netfilter→fib_lookup→ip_local_deliver/ip_forward      │
  │  TX: tcp/udp→ip_queue_xmit→Netfilter→ip_output→dev_queue_xmit     │
  │  Files: net/ipv4/, include/linux/ip.h, include/uapi/linux/ip.h     │
  │                                                                     │
  │  EXHAUSTION                                                         │
  │  IANA pool gone 2011 → NAT/CGN buys time → IPv6 is the future      │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## References

| Resource | Description |
|----------|-------------|
| RFC 791  | IPv4 Specification (September 1981) |
| RFC 826  | ARP |
| RFC 792  | ICMP |
| RFC 1918 | Private Address Space |
| RFC 1519 | CIDR |
| RFC 2131 | DHCP |
| RFC 3021 | Using /31 Prefixes on P2P Links |
| RFC 3022 | NAT |
| RFC 3168 | ECN |
| RFC 4632 | CIDR (updated) |
| RFC 5735 | Special Use IPv4 Addresses |
| RFC 6890 | Special-Purpose IP Address Registries |
| `net/ipv4/ip_input.c`  | Receive path |
| `net/ipv4/ip_output.c` | Transmit path |
| `net/ipv4/fib_trie.c`  | FIB trie |
| `net/ipv4/arp.c`       | ARP |
| `net/ipv4/icmp.c`      | ICMP |
| `include/uapi/linux/ip.h` | iphdr struct |
| `Documentation/networking/ip-sysctl.rst` | All IPv4 sysctls |

---
*Last updated against Linux kernel v6.x mainline. Verify kernel-version-specific behaviour
using `git log --follow net/ipv4/ip_input.c` at kernel.org.*

Now let me write the comprehensive IPv4 guide as a `.md` file:Here's your complete IPv4 guide. Here's what's covered across 21 sections:

**Addressing & Math** — 32-bit structure, binary↔decimal conversion, bitwise AND/OR/NOT for subnet/broadcast/wildcard calculations, all with worked examples.

**Classful → CIDR evolution** — Class A/B/C/D/E breakdown with bit-level structure, why classful failed, the full /8–/32 prefix table with host counts.

**Subnetting & VLSM** — step-by-step math with the magic-number method, binary verification, VLSM allocation with a real worked 6-subnet example showing address-space layout.

**IPv4 Header** — every field dissected: IHL, DSCP/ECN, ID, Flags (DF/MF), Fragment Offset, TTL, Protocol number table, Checksum algorithm, the `struct iphdr` from `include/uapi/linux/ip.h`.

**Fragmentation** — MTU table, fragment math, teardrop/fragment flooding attacks, kernel path through `net/ipv4/ip_fragment.c`.

**ARP** — packet format, DORA exchange, all neighbour states, GARP, Proxy ARP, ARP spoofing defence. Kernel: `net/ipv4/arp.c`, `struct neighbour`.

**ICMP** — full type/code table, ping internals (Identifier/Sequence/RTT), traceroute TTL trick, rate limiting via `icmp_global_allow()`.

**Routing** — FIB trie architecture, LPM, policy routing (multiple tables), static vs dynamic (RIP/OSPF/BGP comparison), OSPF area diagram. Kernel: `net/ipv4/fib_trie.c`.

**NAT/DHCP** — PAT translation table math, conntrack internals, DORA packet flow, DHCP option table, lease renewal T1/T2/T3 lifecycle.

**Linux Kernel** — full `net/ipv4/` source tree map, complete RX/TX call chain (`ip_rcv` → `fib_lookup` → `dev_queue_xmit`), sk_buff access patterns, all important `net.ipv4.*` sysctls.

**Netfilter** — 5-table/chain architecture, packet flow diagrams through PREROUTING/INPUT/FORWARD/OUTPUT/POSTROUTING, practical iptables + nftables examples.