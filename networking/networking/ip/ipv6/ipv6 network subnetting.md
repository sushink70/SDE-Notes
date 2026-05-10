# IPv6 Network Subnetting — Complete In-Depth Guide

> **Audience:** Senior systems/security engineers. Math-first, first-principles, production-grade.
> **Scope:** Address structure → subnetting algebra → allocation strategy → cloud → security → transition.

---

## Table of Contents

1. [Why IPv6 Exists — The Math Problem with IPv4](#1-why-ipv6-exists)
2. [IPv6 Address Architecture — Bit-Level Anatomy](#2-ipv6-address-architecture)
3. [Address Notation and Compression Rules](#3-address-notation-and-compression-rules)
4. [IPv6 Address Space — The Full 128-bit Map](#4-ipv6-address-space)
5. [Address Types — Unicast, Multicast, Anycast](#5-address-types)
6. [Scope — Link-Local, Site-Local, Global](#6-address-scope)
7. [Special and Reserved Addresses](#7-special-and-reserved-addresses)
8. [Prefix Notation and CIDR in IPv6](#8-prefix-notation-and-cidr)
9. [Subnetting Mathematics — First Principles](#9-subnetting-mathematics)
10. [The /64 Boundary — Why It Is Sacred](#10-the-64-boundary)
11. [Standard Allocation Hierarchy (/32 → /48 → /56 → /64)](#11-standard-allocation-hierarchy)
12. [Variable-Length Subnet Masking (VLSM) in IPv6](#12-vlsm-in-ipv6)
13. [EUI-64 Interface Identifier Generation](#13-eui-64-interface-identifier-generation)
14. [SLAAC — Stateless Address Autoconfiguration](#14-slaac)
15. [DHCPv6 — Stateful and Stateless Modes](#15-dhcpv6)
16. [Neighbor Discovery Protocol (NDP)](#16-neighbor-discovery-protocol)
17. [Multicast Address Structure and Solicited-Node Multicast](#17-multicast-address-structure)
18. [Route Aggregation and Summarization](#18-route-aggregation-and-summarization)
19. [IPv6 Subnetting in Cloud Environments](#19-ipv6-in-cloud-environments)
20. [IPv6 Subnetting for Kubernetes and Container Networking](#20-ipv6-in-kubernetes)
21. [Transition Mechanisms — Dual-Stack, Tunneling, NAT64/DNS64](#21-transition-mechanisms)
22. [Security Threat Model for IPv6 Subnets](#22-security-threat-model)
23. [Practical Subnetting Worked Examples](#23-practical-worked-examples)
24. [Quick Reference Tables](#24-quick-reference-tables)
25. [Next 3 Steps](#25-next-3-steps)
26. [References](#26-references)

---

## 1. Why IPv6 Exists

### The IPv4 Exhaustion Problem

IPv4 uses 32 bits → **2^32 = 4,294,967,296** total addresses (~4.3 billion).

```
IPv4 exhaustion math:
  Total addresses  : 2^32  = 4,294,967,296
  Reserved/private : ~18%  = ~590,000,000
  Usable public    : ~3.7 billion
  World population : 8+ billion (each person owns 3-10 devices)
  Deficit          : IANA exhausted Feb 2011, APNIC Apr 2011
```

### IPv6 Solves This With 128 Bits

```
IPv6 total addresses = 2^128
                     = 340,282,366,920,938,463,463,374,607,431,768,211,456
                     ≈ 3.4 × 10^38

Comparison:
  IPv4  : 4.3  × 10^9  addresses
  IPv6  : 3.4  × 10^38 addresses
  Ratio : 7.9  × 10^28 times larger

If Earth surface = 5.1 × 10^14 m²
Then IPv6 gives  : 6.7 × 10^23 addresses per m² of Earth's surface
```

IPv6 also removes NAT as a necessity, enables end-to-end connectivity, and has security (IPsec) designed in from the start.

---

## 2. IPv6 Address Architecture

### Bit Layout of a 128-bit IPv6 Address

```
128 bits total
|<---------------------- 128 bits ----------------------->|

+--------+--------+--------+--------+--------+--------+--------+--------+
| 16 bit | 16 bit | 16 bit | 16 bit | 16 bit | 16 bit | 16 bit | 16 bit |
| group1 | group2 | group3 | group4 | group5 | group6 | group7 | group8 |
+--------+--------+--------+--------+--------+--------+--------+--------+
  hhhh  :  hhhh  :  hhhh  :  hhhh  :  hhhh  :  hhhh  :  hhhh  :  hhhh

Each group (called a "hextet" or "group") = 16 bits = 4 hex digits
Total: 8 groups × 16 bits = 128 bits
Written: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx
```

### Full Bit Breakdown of a Global Unicast Address

```
Global Unicast Address (most common, starts 2000::/3)

Bit position:
 0          3  7                                 63 64                           127
 |<--3 bits-->|<------------- 45 bits ----------->|<---------- 64 bits ---------->|

 +-----------+-----------+-------+---------+------+------------------------------+
 | 001       | Global    | Subnet| Subnet  | Sub- |  Interface Identifier (IID)  |
 | (fixed)   | Routing   | (ISP) | (Site)  | net  |  (host part)                 |
 | 3 bits    | Prefix    | /48   | /56     | /64  |  64 bits                     |
 +-----------+-----------+-------+---------+------+------------------------------+
             |<------ Network Portion ------->|    |<------- Host Portion ------>|

In practice, the standard allocation model:

  /32  = ISP / Regional allocation (from RIR)
  /48  = Single site (organization gets this from ISP)
  /56  = Smaller site or residential
  /64  = Single subnet (one L2 domain, one broadcast domain equivalent)
  /128 = Single host (loopback, specific host assignment)
```

### Anatomy With Real Address

```
Address: 2001:0db8:85a3:0042:0000:8a2e:0370:7334

Split into 8 hextets of 16 bits each:

  Hextet 1 : 2001 = 0010 0000 0000 0001
  Hextet 2 : 0db8 = 0000 1101 1011 1000
  Hextet 3 : 85a3 = 1000 0101 1010 0011
  Hextet 4 : 0042 = 0000 0000 0100 0010
  Hextet 5 : 0000 = 0000 0000 0000 0000
  Hextet 6 : 8a2e = 1000 1010 0010 1110
  Hextet 7 : 0370 = 0000 0011 0111 0000
  Hextet 8 : 7334 = 0111 0011 0011 0100
             ^^^^ ^^^^ = last 32 bits often called IPv4-mapped region in special addresses

  If this is a /64 subnet:
    Network  = 2001:0db8:85a3:0042  (first 64 bits, hextets 1-4)
    Host IID = 0000:8a2e:0370:7334  (last  64 bits, hextets 5-8)
```

---

## 3. Address Notation and Compression Rules

### Full Notation

Every address in full: `2001:0db8:0000:0000:0000:0000:0000:0001`

### Rule 1 — Drop Leading Zeros in Each Group

```
Before: 2001:0db8:0000:0000:0000:0000:0000:0001
After:  2001: db8:   0:   0:   0:   0:   0:   1

Leading zeros only — trailing zeros are significant.
0db8 → db8    (leading 0 dropped)
0042 → 42     (leading 0 dropped)
0001 → 1      (leading zeros dropped)
0000 → 0      (all zeros → single 0)
```

### Rule 2 — Double Colon (::) for Consecutive All-Zero Groups

```
One and ONLY one :: allowed per address.
:: represents one or more consecutive groups of 0000.

2001:db8:0:0:0:0:0:1   →   2001:db8::1
                               ^^
                               replaces five :0: groups

ff02:0:0:0:0:0:0:1     →   ff02::1
::1                        →   loopback (127 groups of 0 + 1)
::                         →   all zeros (unspecified address)
```

### Rule 3 — Expanding :: Back to Full Form

```
To expand ::, count the existing groups, then fill the gap.

Example: 2001:db8::1
  Groups present: 2001, db8, 1  →  3 groups
  Missing: 8 - 3 = 5 groups → insert five :0000:
  Result: 2001:0db8:0000:0000:0000:0000:0000:0001
```

### Prefix Notation

```
Address + / + prefix-length

Example: 2001:db8:85a3::/48
                       ^^^ prefix length in bits

This means:
  Network bits = first 48 bits = 2001:0db8:85a3
  Host bits    = remaining 80 bits = anything
```

### URL Notation (Brackets Required)

```
IPv6 in URLs MUST be enclosed in brackets to avoid ambiguity with colon:
  http://[2001:db8::1]:8080/path
  https://[fe80::1%eth0]:443/     (with zone ID for link-local)
```

---

## 4. IPv6 Address Space

### Top-Level Space Map (First 3-4 Bits)

```
Binary prefix  | Hex range             | Assignment
---------------+-----------------------+--------------------------------------------
0000 0000      | ::/8                  | Reserved (loopback ::1, unspecified ::)
0000 0001      | 100::/8               | Reserved
0000 001x      | 200::/7               | Reserved (was OSI NSAP, now unallocated)
0000 010x      | 400::/7               | Reserved
...            | ...                   | Reserved (large swathes unused)
001x xxxx      | 2000::/3              | Global Unicast Addresses (GUA) ← most used
1111 1110 10   | fe80::/10             | Link-Local Unicast
1111 1110 11   | fec0::/10             | Site-Local (deprecated RFC 3879)
1111 1111      | ff00::/8              | Multicast
...            | fc00::/7              | Unique Local Addresses (ULA, RFC 4193)
```

### Global Unicast Space Breakdown

```
2000::/3 = all addresses starting with binary 001
         = 2000:: to 3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff

Total size: 2^125 addresses (3/8 of total IPv6 space)

Current IANA Allocations within GUA:
  2001::/16  → IETF Protocol Assignments
    2001:db8::/32  → Documentation (RFC 5737-equivalent, NEVER routed)
    2001::/23      → IETF Protocol
    2001:20::/28   → ORCHIDv2
  2002::/16  → 6to4 relay (deprecated)
  2400::/12  → APNIC region
  2600::/12  → ARIN region (North America)
  2800::/12  → LACNIC region (Latin America)
  2a00::/12  → RIPE NCC region (Europe/Middle East)
  2c00::/12  → AFRINIC region (Africa)
```

### Unique Local Addresses (ULA) — The Private Space Equivalent

```
Range: fc00::/7   →   covers fc00:: to fdff::

  Split:
    fc00::/8  → Not assigned (L bit = 0, centrally assigned, not implemented)
    fd00::/8  → Locally assigned (L bit = 1) ← USE THIS for private addressing

Structure of ULA fd00::/8:
  |  8 bits  | 40 bits random  | 16 bits subnet | 64 bits IID |
  +----------+-----------------+----------------+-------------+
  | 1111 1101| Global ID       | Subnet ID      | Interface   |
  | (fd)     | (pseudo-random) |                | Identifier  |
  +----------+-----------------+----------------+-------------+

  The 40-bit Global ID MUST be randomly generated to avoid conflicts
  when merging networks.

  Generation: SHA-1 hash of current time + EUI-64 → take low 40 bits
  Example ULA: fd12:3456:789a::/48

Comparison to IPv4 Private:
  IPv4 RFC1918  ↔  IPv6 ULA
  10.0.0.0/8    ↔  fd00::/8 (huge space)
  172.16.0.0/12 ↔  fd00::/8
  192.168.0.0/16↔  fd00::/8

Note: ULA does NOT need NAT. Hosts have globally unique ULA addresses
and can communicate directly (within organization).
```

---

## 5. Address Types

### Unicast — One-to-One

```
One sender → one specific receiver

Types:
  Global Unicast (GUA)  : 2000::/3       - Internet routable
  Link-Local            : fe80::/10      - Single link only, never routed
  Loopback              : ::1/128        - Self
  Unspecified           : ::/128         - "No address" (source before config)
  Unique Local (ULA)    : fc00::/7       - Organization-internal
  IPv4-mapped           : ::ffff:x.x.x.x - IPv6 representation of IPv4
  IPv4-compatible       : ::x.x.x.x      - Deprecated
```

### Multicast — One-to-Many

```
One sender → all subscribed receivers (group)

Prefix: ff00::/8
Format: ffXY::/... where X = flags, Y = scope

NO broadcast in IPv6! Multicast replaces all broadcast use cases.

Key reserved multicast addresses:
  ff02::1  = All nodes (link-local)       → replaces 255.255.255.255 broadcast
  ff02::2  = All routers (link-local)
  ff02::5  = OSPFv3 all routers
  ff02::6  = OSPFv3 DR routers
  ff02::9  = RIPng routers
  ff02::a  = EIGRP routers
  ff02::d  = PIM routers
  ff02::16 = MLDv2 capable routers
  ff02::1:2 = All DHCP servers/relay agents (link-local)
  ff05::1:3 = All DHCP servers (site-local)
  ff02::1:ffXX:XXXX = Solicited-Node Multicast (per-host, NDP)
```

### Anycast — One-to-Nearest

```
One sender → nearest member of a group (routing metric determines "nearest")

Key use cases:
  - DNS root servers (anycast across global PoPs)
  - CDN entry points
  - Load balancing at network layer

Anycast addresses look identical to unicast.
No special prefix — identified by configuration only.
Subnet-Router Anycast: automatically formed from any /64 prefix (all-zeros host).

Example:
  Subnet:  2001:db8:1::/64
  Anycast: 2001:db8:1::   (host part = all zeros)
  This is routed to the nearest router on that subnet.
```

---

## 6. Address Scope

### Scope Hierarchy

```
Scope defines where a packet can travel.

+-------------------+-------+------------------------------------------+
| Scope Name        | Value | Range                                    |
+-------------------+-------+------------------------------------------+
| Interface-Local   |  0x1  | Single NIC/loopback only                 |
| Link-Local        |  0x2  | Single L2 segment, never forwarded      |
| Realm-Local       |  0x3  | Application-defined (mesh)               |
| Admin-Local        |  0x4  | Smallest admin-configured domain        |
| Site-Local        |  0x5  | Site/campus (deprecated for unicast)    |
| Organization-Local|  0x8  | Org-wide                                 |
| Global            |  0xe  | Internet-wide                            |
+-------------------+-------+------------------------------------------+

Scope appears in multicast prefix: ffXY where Y = scope nibble
  ff02:: = link-local multicast  (Y=2)
  ff05:: = site-local multicast  (Y=5)
  ff0e:: = global multicast      (Y=e)
```

### Link-Local Deep Dive

```
Prefix: fe80::/10
Full range: fe80:: to febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff
            (but in practice only fe80::/64 is used — upper 54 bits after prefix = 0)

Properties:
  - Automatically configured on every IPv6 interface at boot
  - NEVER forwarded by routers
  - Used for: NDP, router discovery, DHCPv6 relay, OSPFv3 next-hops
  - Requires zone ID (%interface) when used as destination from multi-homed hosts

Zone ID syntax:
  fe80::1%eth0    (Linux)
  fe80::1%3       (Windows interface index)
  fe80::1%en0     (macOS)

Why zone ID is needed:
  Every interface has fe80::/10 addresses.
  Without zone ID, OS cannot determine which interface to send out.
  Zone ID is LOCAL and has no meaning outside the host.

Link-local address formation:
  Prefix: fe80::/64  (upper 64 bits fixed)
  IID:    EUI-64 derived from MAC, or random (privacy extensions)
```

---

## 7. Special and Reserved Addresses

```
Address              | Prefix Length | Description
---------------------+---------------+------------------------------------------
::                   | /128          | Unspecified — source before IP assignment
::1                  | /128          | Loopback — equivalent to 127.0.0.1
::ffff:0:0/96        | /96           | IPv4-mapped (::ffff:192.0.2.1)
::ffff:0:0:0/96      | /96           | IPv4-translated (NAT64 side)
64:ff9b::/96         | /96           | IPv4/IPv6 translation (Well-known NAT64 prefix)
64:ff9b:1::/48       | /48           | IPv4/IPv6 translation (local use)
100::/64             | /64           | Discard-Only (RFC 6666)
2001::/23            | /23           | IETF Protocol Assignments
2001:db8::/32        | /32           | Documentation (NEVER route this!)
2001:10::/28         | /28           | ORCHIDv1 (deprecated)
2001:20::/28         | /28           | ORCHIDv2
2002::/16            | /16           | 6to4 (deprecated)
fc00::/7             | /7            | Unique Local
fe80::/10            | /10           | Link-Local Unicast
ff00::/8             | /8            | Multicast

Security note: Filter 2001:db8::/32 at all border routers.
               Filter ::/128 and ::1/128 as sources at borders.
               Filter fc00::/7 at Internet boundaries.
               Filter fe80::/10 at routed interfaces (not link boundary).
```

---

## 8. Prefix Notation and CIDR

### How IPv6 CIDR Works

```
IPv6 uses CIDR (Classless Inter-Domain Routing) exclusively.
There are NO "classes" (no Class A/B/C equivalent).

Notation:  address/prefix-length
  address        = any valid IPv6 address
  prefix-length  = integer 0 to 128

The prefix-length means: the first N bits are the NETWORK portion.
The remaining (128 - N) bits are the HOST portion.
```

### Prefix Math

```
Given prefix length N:
  Network bits  = N
  Host bits     = 128 - N
  Total hosts   = 2^(128-N)    (including network address and subnet-router anycast)
  Usable hosts  = 2^(128-N)    (IPv6 has no "broadcast" to reserve)
                               (but ::0 is subnet-router anycast, ::1 often used for gateway)

Examples:
  /32  → 128-32  = 96 host bits → 2^96  ≈ 7.9 × 10^28 addresses
  /48  → 128-48  = 80 host bits → 2^80  ≈ 1.2 × 10^24 addresses
  /56  → 128-56  = 72 host bits → 2^72  ≈ 4.7 × 10^21 addresses
  /64  → 128-64  = 64 host bits → 2^64  ≈ 1.8 × 10^19 addresses
  /96  → 128-96  = 32 host bits → 2^32  ≈ 4.3 × 10^9  addresses (IPv4-sized)
  /128 → 128-128 = 0  host bits → 2^0   = 1 address    (single host)
```

### Network Address (Prefix)

```
To find the network address from an address+prefix:
  1. Convert address to 128-bit binary
  2. Zero out all bits after position N
  3. That is the network address (prefix)

Example: 2001:db8:85a3::8a2e:370:7334/48

  Full binary (first 64 bits shown for brevity):
    2001 = 0010 0000 0000 0001
    0db8 = 0000 1101 1011 1000
    85a3 = 1000 0101 1010 0011  ← bit 48 is the last bit of hextet 3
    0042 = 0000 0000 0100 0010  ← these bits zeroed for /48 prefix

  Network prefix = 2001:0db8:85a3::/48  (zero everything after bit 48)
```

---

## 9. Subnetting Mathematics

### Core Formula

```
Given a block of size /N that you want to split into subnets of size /M
  (where M > N, i.e., longer prefix = smaller subnet):

  Number of subnets = 2^(M - N)
  Addresses per subnet = 2^(128 - M)
  Total addresses = 2^(128 - N)  [unchanged, just subdivided]

Example: Divide a /48 into /64 subnets
  N = 48, M = 64
  Number of subnets = 2^(64-48) = 2^16 = 65,536 subnets
  Addresses per /64  = 2^(128-64) = 2^64 ≈ 1.8 × 10^19
```

### Subnet Enumeration

```
To enumerate subnets when splitting /N into /M subnets:

  Subnet increment = 2^(128 - M)  in terms of address values
  But easier: work in the relevant hextet

Example: Divide 2001:db8:1::/48 into /64 subnets

  The subnet bits are bits 48 to 63 = hextet 4 (0000 to ffff)
  
  Subnet 0:     2001:db8:1:0000::/64  →  2001:db8:1:0::/64
  Subnet 1:     2001:db8:1:0001::/64  →  2001:db8:1:1::/64
  Subnet 2:     2001:db8:1:0002::/64  →  2001:db8:1:2::/64
  ...
  Subnet 255:   2001:db8:1:00ff::/64  →  2001:db8:1:ff::/64
  Subnet 256:   2001:db8:1:0100::/64  →  2001:db8:1:100::/64
  ...
  Subnet 65535: 2001:db8:1:ffff::/64  →  2001:db8:1:ffff::/64

  Total: 65,536 /64 subnets from one /48
```

### Splitting Across Hextet Boundaries

```
When prefix falls in the MIDDLE of a hextet, math gets bit-level.

Example: Divide 2001:db8::/32 into /36 subnets
  N=32, M=36
  Subnet bits: bits 32-35 = top 4 bits of hextet 3
  Number of subnets: 2^(36-32) = 2^4 = 16

  Hextet 3 top 4 bits iterate 0000 to 1111:
  Subnet 0:  2001:db8:0000::/36  → network part of h3 = 0x0000 to 0x0fff
  Subnet 1:  2001:db8:1000::/36  → network part of h3 = 0x1000 to 0x1fff
  Subnet 2:  2001:db8:2000::/36
  ...
  Subnet 15: 2001:db8:f000::/36

  Increment per /36 subnet = 2^(128-36) = 2^92 addresses
  In hex, the 3rd hextet increments by 0x1000 each time.

General increment rule:
  Find which hextet contains the boundary bit position B (= M).
  Hextet index k = floor((M-1) / 16)   [0-indexed]
  Bit position within hextet = M - (k * 16)
  Increment = 2^(16 - (M mod 16)) in that hextet
              (if M is multiple of 16, increment is in hextet k-1 by 1)
```

### Boundary Alignment

```
IPv6 subnets MUST be aligned to their size.
A /64 subnet must start on a /64 boundary (host bits = all zero).

Valid   /64: 2001:db8:1:0::/64    (last 64 bits = 0)
Valid   /64: 2001:db8:1:1::/64
Invalid /64: 2001:db8:1:0::1/64   (host bit is set in network address → invalid)

Check alignment:
  Extract host portion (128 - prefix-length bits from the right)
  If any bit is 1 → misaligned → invalid subnet

This is exactly the same rule as IPv4 subnetting alignment.
```

### Powers of 2 Quick Reference

```
2^0  = 1
2^1  = 2
2^2  = 4
2^4  = 16
2^8  = 256
2^10 = 1,024
2^12 = 4,096
2^16 = 65,536                    ← /64 subnets in a /48
2^20 = 1,048,576
2^24 = 16,777,216
2^32 = 4,294,967,296             ← total IPv4 space
2^40 = 1,099,511,627,776
2^48 = 281,474,976,710,656
2^64 = 18,446,744,073,709,551,616  ← hosts in a /64 subnet
2^80 = 1,208,925,819,614,629,174,706,176
2^96 = 79,228,162,514,264,337,593,543,950,336
2^128= 340,282,366,920,938,463,463,374,607,431,768,211,456
```

---

## 10. The /64 Boundary — Why It Is Sacred

### The Rule

```
The interface identifier (IID) in IPv6 is ALWAYS 64 bits.
Therefore the subnet prefix is ALWAYS /64 for any subnet with hosts.

This is not optional. It is mandated by:
  - RFC 4291 (IPv6 Addressing Architecture)
  - RFC 4862 (SLAAC — requires /64)
  - EUI-64 (requires /64 subnet)
  - NDP Neighbor Discovery (assumes /64)
  - Many router implementations

/64 is the atomic unit of IPv6 subnetting for end-host subnets.
```

### When /64 CAN Be Violated

```
/64 is required for:
  - Any subnet where SLAAC is used
  - Any subnet where EUI-64 IID is used
  - Any standard LAN segment

/64 can technically be broken for:
  /126  → Point-to-point links (like IPv4 /30) — 4 addresses, 2 usable
          RFC 6164 officially allows /127 for P2P links
  /127  → Point-to-point links RFC 6164 — 2 addresses exactly
          Preferred over /126 for P2P to avoid subnet-router anycast issues
  /128  → Loopback, single host assignment, management addresses
          No host bits → no IID, no SLAAC possible

Security implication of /127 on P2P links:
  Prevents subnet-router anycast attack (where attacker claims ::0 of /126)
```

### The /64 Address Space Problem vs. Waste

```
A /64 has 2^64 = 18 quintillion addresses for ONE subnet.
This feels "wasteful" compared to IPv4 thinking.

WHY this is intentional:
  1. SLAAC needs 64-bit IID space
  2. Privacy extensions need large IID space (random addresses)
  3. Scanning a /64 at 1 million probes/sec takes 580,000 years → anti-scan
  4. Subnetting below /64 breaks SLAAC, NDP, many protocols
  5. The total IPv6 space is so vast that /64 waste is irrelevant

The "waste" is a feature: it makes host enumeration via scanning infeasible.
```

---

## 11. Standard Allocation Hierarchy

### The RIR → ISP → Site → Subnet Model

```
+-----------------------------------------------------------------------+
|                     IANA  (manages entire space)                      |
|                     Allocates /12 blocks to RIRs                      |
+-----------------------------------+-----------------------------------+
                                    |
          +-------------------------+-------------------------+
          |           |             |             |           |
       ARIN        RIPE NCC      APNIC        LACNIC      AFRINIC
       /12          /12           /12           /12          /12
       North Am.   Europe/ME     Asia-Pac      Latin Am.   Africa
          |
          | Allocates /32 (sometimes /28, /24) to ISPs/LIRs
          |
     +----+----+
     |         |
  ISP/LIR   ISP/LIR
   /32        /32
     |
     | Assigns /48 per customer site (RFC 6177)
     | (or /56 for residential, /60 for very small)
     |
  Customer Site
    /48
     |
     | Subnets into /64 per L2 segment
     |
  +--+--+--+--+
  /64  /64  /64  /64   (each is one LAN segment)
```

### Allocation Sizes and Rationale

```
Prefix | Size       | Typical Assignment              | Rationale
-------+------------+---------------------------------+-------------------------------
/23    | Large block| RIR to very large ISP           | ~512 /32s
/24    | 256 /32s   | RIR to large ISP                |
/28    | 16 /32s    | RIR to medium ISP               |
/32    | Standard   | ISP allocation from RIR         | 65536 /48s per ISP
/36    |            | ISP internal infrastructure     | 4096 /48s
/48    | Standard   | One site/organization           | 65536 /64 subnets
/52    |            | Large enterprise floor/building |
/56    | Smaller    | Residential / small office      | 256 /64 subnets
/60    | Tiny       | Very small site (4 /64 subnets) | 16 /64 subnets
/64    | Subnet     | ONE network segment             | Single L2 domain
/128   | Host       | Loopback / specific host        | Single interface
```

### /48 Site Internal Subnetting Strategy

```
Your organization received: 2001:db8:abcd::/48

Bits available for subnetting: 48 to 64 = 16 bits
Maximum /64 subnets: 2^16 = 65,536

Structured allocation example:

Bits 48-51 (4 bits) = Region/DC
Bits 52-55 (4 bits) = Building/Zone  
Bits 56-59 (4 bits) = VLAN/Purpose
Bits 60-63 (4 bits) = Sub-segment

         |<-- 48 bits prefix -->|<4>|<4>|<4>|<4>|<--- 64 bits IID --->|
         | 2001:0db8:abcd       | RR| BB| PP| SS|  interface ID        |

Where:
  RR = Region (0-15): e.g., 0=us-east, 1=us-west, 2=eu-west, 3=ap-southeast
  BB = Building/Zone: 0=dmz, 1=prod, 2=staging, 3=mgmt, 4=infra
  PP = Purpose:       0=servers, 1=pods, 2=network, 3=storage, 4=iot
  SS = Sub-segment:   0-15 for further division

Example subnets:
  2001:db8:abcd:0000::/64  → Region 0, Zone 0, Purpose 0, Sub 0
                             (us-east, dmz, servers, segment 0)
  2001:db8:abcd:0011::/64  → Region 0, Zone 0, Purpose 1, Sub 1
  2001:db8:abcd:1234::/64  → Region 1, Zone 2, Purpose 3, Sub 4
  2001:db8:abcd:ffff::/64  → Last segment
```

---

## 12. VLSM in IPv6

### Variable-Length Subnet Masking Concept

```
VLSM = using different prefix lengths for different subnets
       (not all subnets need to be the same size)

IPv6 makes VLSM simpler conceptually:
  - End-host subnets are ALWAYS /64 (no VLSM needed here)
  - VLSM applies to infrastructure/interconnects:
      /64  = LAN segments (standard)
      /96  = Large P2P-ish (rare)
      /126 = P2P transit links (4 addresses)
      /127 = P2P loopback-style links (RFC 6164)
      /128 = Single host, loopback

The "subnetting hierarchy" above IS VLSM in practice:
  /32 → ISP block
  /48 → Site
  /56 → Building
  /64 → Segment
```

### VLSM Worked Example

```
Allocation: fd00::/48 (ULA, internal org)

Requirements:
  - 3 large production VLANs
  - 1 management network (small)
  - 2 P2P router interconnects
  - 1 loopback per router (×4 routers)

Assignment:
  fd00:0:0:0001::/64  → Production VLAN 1   (2^64 hosts)
  fd00:0:0:0002::/64  → Production VLAN 2
  fd00:0:0:0003::/64  → Production VLAN 3
  fd00:0:0:0010::/64  → Management VLAN     (logically small, /64 required for SLAAC)
  fd00:0:0:0f00::/127 → P2P link 1 (router A ↔ router B)
                           ::0 = Router A interface
                           ::1 = Router B interface
  fd00:0:0:0f01::/127 → P2P link 2 (router B ↔ router C)
  fd00:0:0:0ff0::1/128 → Router A loopback
  fd00:0:0:0ff0::2/128 → Router B loopback
  fd00:0:0:0ff0::3/128 → Router C loopback
  fd00:0:0:0ff0::4/128 → Router D loopback

Remaining space:
  fd00:0:0:0004:: through fd00:0:0:0eff:: and more → free for future use
```

---

## 13. EUI-64 Interface Identifier Generation

### What EUI-64 Is

```
EUI-64 = Extended Unique Identifier (64-bit)
         A method to generate a 64-bit Interface Identifier from a 48-bit MAC address

This IID is then appended to the /64 prefix to form a full IPv6 address.
```

### EUI-64 Algorithm Step by Step

```
Input: 48-bit MAC address (e.g., 00:1A:2B:3C:4D:5E)

Step 1: Split MAC into two 24-bit halves
  OUI (Org Unique Identifier): 00:1A:2B
  Device identifier:           3C:4D:5E

Step 2: Insert FF:FE in the middle (making it 64 bits)
  00:1A:2B : FF:FE : 3C:4D:5E

Step 3: Flip the 7th bit (Universal/Local bit) of the first octet
  First octet = 0x00 = 0000 0000
  7th bit (from left, 0-indexed) = bit index 6 = U/L bit
  
  MAC bit 6 = 0 (universally administered)  → flip to 1
  0000 0000 → 0000 0010 = 0x02

  Result: 02:1A:2B:FF:FE:3C:4D:5E

Step 4: Write as IPv6 IID (group in pairs of octets):
  02:1A = 021A
  2B:FF = 2BFF
  FE:3C = FE3C
  4D:5E = 4D5E
  IID = 021A:2BFF:FE3C:4D5E

Step 5: Append to /64 prefix:
  Prefix: 2001:db8:1::/64
  Address: 2001:db8:1::21a:2bff:fe3c:4d5e  (with compression)
           2001:0db8:0001:0000:021a:2bff:fe3c:4d5e (full)
```

### The U/L Bit Rule Explained

```
In MAC addresses, bit 6 of octet 1 (0-indexed) is the Universal/Local bit:
  0 = Universally administered (assigned by IEEE/manufacturer)
  1 = Locally administered (manually assigned, VMware MAC, VPN, etc.)

EUI-64 INVERTS this bit. Why?
  In IEEE EUI-64, the bit means "globally unique"
  The inversion maps MAC's "universal=0" → EUI-64 "globally unique=1"

Practical impact:
  Real MAC  00:1A:2B:3C:4D:5E → IID has 02:... (bit flipped from 00 to 02)
  Local MAC 02:1A:2B:3C:4D:5E → IID has 00:... (bit flipped from 02 to 00)
```

### EUI-64 Privacy Concern

```
EUI-64-derived addresses EMBED YOUR MAC ADDRESS.
This enables:
  - Cross-site tracking (your MAC is visible in your IPv6 address)
  - Vendor identification (OUI reveals manufacturer)
  - Long-term tracking even across networks (MAC persists)

Mitigation: IPv6 Privacy Extensions (RFC 4941)
  Generates random temporary IID instead of EUI-64.
  Address changes over time (default ~1-7 days for outbound connections).
  Stable IID for inbound (RFC 7217 — cryptographically stable but opaque).
```

---

## 14. SLAAC — Stateless Address Autoconfiguration

### Overview

```
SLAAC = host configures its own IPv6 address WITHOUT a DHCP server
        (stateless = no server maintains binding state)

Standards: RFC 4862
Requires:  /64 subnet prefix (hard requirement)
```

### SLAAC Process Step by Step

```
+--------+                                          +--------+
|  Host  |                                          | Router |
+--------+                                          +--------+
    |                                                   |
    | 1. Interface comes up                             |
    |    Generates link-local: fe80::IID/64             |
    |    (IID from EUI-64 or random)                    |
    |                                                   |
    | 2. DAD: Neighbor Solicitation to ff02::1:ff.../   |
    |    "Is anyone using fe80::IID ?"                  |
    |---------------------------------------------->    |
    |    (wait 1 second for Neighbor Advertisement)     |
    |                                                   |
    | 3. Send Router Solicitation (RS)                  |
    |    Source: fe80::IID                              |
    |    Dest: ff02::2 (all-routers multicast)         |
    |---------------------------------------------->    |
    |                                                   |
    |                      4. Router Advertisement (RA)|
    |                         Source: fe80::router     |
    |                         Dest: ff02::1 (all nodes)|
    |                         Contains:                |
    |                           - Prefix: 2001:db8::/64|
    |                           - Prefix valid lifetime|
    |                           - Preferred lifetime   |
    |                           - M flag (Managed)     |
    |                           - O flag (Other config)|
    |                           - Router lifetime      |
    |    <----------------------------------------------+
    |                                                   |
    | 5. Host forms GUA:                                |
    |    Prefix + IID = 2001:db8::IID/64               |
    |                                                   |
    | 6. DAD on new GUA                                 |
    |    NS to ff02::1:ffXX:XXXX (solicited-node)      |
    |    Wait ~1 second for NA reply                    |
    |    If no reply → address is UNIQUE, use it        |
    +                                                   +
```

### RA Flags and Their Meaning

```
Router Advertisement flags:

M flag (Managed Address Configuration):
  0 = Use SLAAC (default)
  1 = Use DHCPv6 for addresses (stateful DHCPv6)
  Note: when M=1, host ALSO uses SLAAC unless A flag in PIO is 0

O flag (Other Configuration):
  0 = No additional config needed
  1 = Use DHCPv6 for other info (DNS, NTP) but NOT addresses
      This is "stateless DHCPv6"

A flag (in Prefix Information Option, PIO):
  1 = Use this prefix for SLAAC address formation
  0 = Do NOT use this prefix for SLAAC

L flag (On-Link, in PIO):
  1 = Prefix is on this link (hosts can talk directly)
  0 = Prefix is NOT on-link (must route even for same-prefix hosts)

Common combinations:
  M=0, O=0  → Pure SLAAC, no DHCPv6 at all
  M=0, O=1  → SLAAC for addresses, stateless DHCPv6 for DNS/NTP
  M=1, O=1  → Stateful DHCPv6 for addresses AND options
  M=1, O=0  → Stateful DHCPv6 for addresses only
```

### Address Lifetimes

```
Each SLAAC address has two lifetimes:

Preferred Lifetime:
  Address is valid and preferred for new connections.
  Default: 604800 seconds (7 days)

Valid Lifetime:
  Address is valid but may be "deprecated" (not preferred for new connections).
  Old connections continue using deprecated address.
  Default: 2592000 seconds (30 days)

After Valid Lifetime expires → address is removed.

States:
  Tentative → (DAD pending, not yet in use)
  Preferred → (valid, use for new connections)
  Deprecated → (valid, keep existing connections, don't start new)
  Invalid → (removed)

Timeline:
  t=0                  preferred expires           valid expires
  |----Preferred---------|-------Deprecated---------|---Invalid-->
  |<-- preferred lifetime (7 days) -->|
  |<---------- valid lifetime (30 days) ---------->|
```

---

## 15. DHCPv6

### DHCPv6 vs. SLAAC

```
+----------------------+-----------------------------+---------------------------+
| Feature              | SLAAC                       | DHCPv6                    |
+----------------------+-----------------------------+---------------------------+
| Address assignment   | Host auto-generates         | Server assigns            |
| Server state         | Stateless                   | Stateful (bindings)       |
| Address tracking     | No (hard to track)          | Yes (lease database)      |
| DNS config           | Via RA (RDNSS option)       | Via DHCPv6 options        |
| Prefix length req.   | /64 mandatory               | /64 for prefix, any for host|
| Default gateway      | From RA                     | NOT from DHCPv6 (still RA)|
| Requires RA          | Yes (for gateway + prefix)  | Yes (for gateway always)  |
+----------------------+-----------------------------+---------------------------+

Critical: DHCPv6 NEVER sends the default gateway. The gateway always
comes from Router Advertisements. Even with full DHCPv6, RA must work.
```

### DHCPv6 Message Exchange

```
Stateful DHCPv6 (M=1):

Client                                    Server
  |                                          |
  |--- Solicit (ff02::1:2, all-DHCP) ------> |  "Who are DHCP servers?"
  |                                          |
  | <-- Advertise -------------------------  |  "I am, here's what I offer"
  |                                          |
  |--- Request --------------------------->  |  "I want that address"
  |                                          |
  | <-- Reply -----------------------------  |  "Confirmed, here's your lease"
  |                                          |

  Renew/Rebind cycle same as DHCPv4 (T1/T2 timers)

Rapid Commit (2-message exchange, when configured):
  Client                Server
    |--- Solicit -------> |  (with Rapid Commit option)
    | <-- Reply --------  |  (server skips Advertise, goes direct to Reply)
```

### DHCPv6 Prefix Delegation (PD) — Critical for ISP/Edge

```
DHCPv6-PD (RFC 3633) allows a router to request a PREFIX (not just an address)
from an upstream DHCP server. This is how ISPs give /48 or /56 to CPE routers.

Home router / CPE router:
  1. Sends DHCPv6-PD Solicit requesting a prefix (IA_PD option)
  2. ISP DHCP server assigns: fd00::/56 (or 2001:db8:x::/48)
  3. CPE router uses that prefix to address its internal subnets

Example:
  ISP gives CPE: 2001:db8:abcd::/56
  CPE assigns subnets:
    LAN1: 2001:db8:abcd:00::/64
    LAN2: 2001:db8:abcd:01::/64
    WiFi: 2001:db8:abcd:02::/64
    IoT:  2001:db8:abcd:03::/64
    ...up to 2001:db8:abcd:ff::/64 (256 subnets from /56)

Kubernetes use of PD:
  Similar mechanism used by cluster IPAM controllers to request pod CIDRs
  from a delegating router or IPAM service.
```

---

## 16. Neighbor Discovery Protocol (NDP)

### NDP Replaces ARP in IPv6

```
ARP (IPv4) → NDP (IPv6)

NDP uses ICMPv6 messages (RFC 4861):

  Type 133 = Router Solicitation (RS)     - host → router
  Type 134 = Router Advertisement (RA)    - router → hosts
  Type 135 = Neighbor Solicitation (NS)   - ARP Request equivalent
  Type 136 = Neighbor Advertisement (NA)  - ARP Reply equivalent
  Type 137 = Redirect                     - ICMP Redirect equivalent

Security advantage over ARP:
  NDP can use SEND (Secure Neighbor Discovery, RFC 3971)
  with Cryptographically Generated Addresses (CGA) for verification.
```

### Solicited-Node Multicast Address

```
Key optimization: NDP uses per-host MULTICAST instead of broadcast.

For any unicast address, the solicited-node multicast address is:
  ff02::1:ff + last 24 bits of unicast address

Example:
  Host address: 2001:db8::1234:5678
  Last 24 bits: 34:56:78
  Solicited-node multicast: ff02::1:ff34:5678

  Host joins this multicast group at L2.
  NDP NS messages target this multicast → only the target host responds.
  
  Compare to ARP: broadcasts to all hosts on the segment.
  NDP: targets a small multicast group (low chance of collision).
  In a /64 with 2^64 possible addresses, solicited-node has 2^24 = 16M
  possible members, but a real subnet might have 100s of hosts.
  Collision probability: ~100 / 16,777,216 ≈ 0.0006% per address lookup.
```

### NDP Cache (Neighbor Cache)

```
Equivalent to ARP cache in IPv4.

States:
  INCOMPLETE  → NS sent, waiting for NA
  REACHABLE   → Recently confirmed reachable (30 seconds default)
  STALE       → Not confirmed recently, but may still work
  DELAY       → In STALE, waiting before probing
  PROBE       → Actively sending unicast NS to verify
  FAILED      → No response after probing → unreachable

Linux NDP cache:
  ip -6 neigh show
  ip -6 neigh flush dev eth0

  Example output:
  2001:db8::1 dev eth0 lladdr 00:1a:2b:3c:4d:5e REACHABLE
  fe80::1     dev eth0 lladdr 00:0c:29:ab:cd:ef STALE
```

### NDP Security Issues

```
NDP is susceptible to spoofing attacks (like ARP poisoning):

Attack: Neighbor Advertisement Spoofing
  Attacker sends unsolicited NA claiming to be the router.
  All traffic gets redirected to attacker.

Attack: Router Advertisement (RA) Spoofing
  Attacker sends fake RA with:
    - Malicious default gateway
    - Malicious prefix (SLAAC poisoning)
    - Short prefix lifetime (DoS by renewing fake prefix)
    - M=1 flag pointing to rogue DHCPv6 server

Defenses:
  1. RA Guard (RFC 6105): Switch drops RA from non-router ports
  2. DHCPv6 Shield: Switch drops DHCPv6 server messages from non-trusted ports
  3. SEND (RFC 3971): Cryptographic signing of NDP messages (complex, rarely deployed)
  4. SeND with CGA: Cryptographically Generated Addresses prove ownership
  5. Port security + IPv6 FHS (First Hop Security)
  6. Kernel sysctl: net.ipv6.conf.all.accept_ra = 0 (disable RA on servers)
```

---

## 17. Multicast Address Structure

### Full Multicast Format

```
ff | flags | scope | group-id (112 bits)

ff = 1111 1111 (0xff) — identifies multicast

flags (4 bits):
  bit 0 (R): Embedded Rendezvous Point (RFC 3956)
  bit 1 (P): Prefix-based (RFC 3306)
  bit 2 (T): 0=well-known (IANA assigned), 1=transient (dynamically assigned)
  bit 3:     Reserved (must be 0)

scope (4 bits):
  0x1 = Interface-local
  0x2 = Link-local
  0x4 = Admin-local
  0x5 = Site-local
  0x8 = Organization-local
  0xe = Global

group-id (112 bits): Identifies the multicast group

Full structure:
  |  8 bits  | 4 bits | 4 bits |         112 bits         |
  +----------+--------+--------+--------------------------+
  | 11111111 | flags  | scope  |        Group ID          |
  +----------+--------+--------+--------------------------+
```

### Solicited-Node Multicast (Recap with Full Format)

```
ff02::1:ffXX:XXXX

Breakdown:
  ff = multicast
  02 = flags=0000, scope=2 (link-local)
  00:00:00:00:00:00:00:00:00:01:ff = group prefix
  XX:XXXX = last 24 bits of unicast address

This is in the well-known (T=0) space, IANA-reserved range.
Every NDP-capable node MUST join the solicited-node multicast group
for each of its unicast and anycast addresses.
```

### Multicast Routing Protocols

```
MLD (Multicast Listener Discovery) = IPv6 equivalent of IGMP

  MLDv1 (RFC 2710) ↔ IGMPv2
  MLDv2 (RFC 3810) ↔ IGMPv3 (source-specific multicast)

MLD uses ICMPv6 messages:
  Type 130 = Multicast Listener Query
  Type 131 = Multicast Listener Report (v1)
  Type 132 = Multicast Listener Done (v1)
  Type 143 = Multicast Listener Report (v2)

Multicast routing protocols:
  PIM-SM (Protocol Independent Multicast - Sparse Mode)
  PIM-SSM (Source-Specific Multicast) — maps to ff3x::/32 addresses
  MLDP (Multicast in MPLS)
```

---

## 18. Route Aggregation and Summarization

### Aggregation Fundamentals

```
Aggregation = combining multiple prefixes into one larger prefix to reduce
              routing table size. Same as "supernetting" in IPv4.

Rule: Multiple prefixes can be aggregated if they share a common bit prefix.

Example:
  2001:db8:0:0::/64
  2001:db8:0:1::/64
  2001:db8:0:2::/64
  2001:db8:0:3::/64

  All share: 2001:db8:0: and the first 2 bits of hextet 4 (00xx)
  Aggregate: 2001:db8:0::/62   (covers ::0 through ::3)
  
  Verify: 2001:db8:0:0::/62 covers addresses:
    From 2001:db8:0:0:: to 2001:db8:0:3:ffff:ffff:ffff:ffff ✓

Another example:
  2001:db8:0::/64
  2001:db8:1::/64
  → Aggregate: 2001:db8::/63  (covers both /64s)
  
  But only valid if you own BOTH. Don't aggregate what you don't own.
```

### Aggregation Algorithm

```
To find the aggregate of two prefixes:

1. Both must be the same size (/N)
2. They must be "buddies" — differ only in the last bit of the prefix

Given /N prefixes A and B:
  Convert both network addresses to binary
  Find the longest common prefix
  Aggregate = common prefix + length of common prefix

Example:
  2001:db8:0:4::/64  = ...0000 0100 (hextet 4 in binary)
  2001:db8:0:5::/64  = ...0000 0101

  Common bits: ...0000 010?  (differ only in last bit)
  Last common bit at position 63 → aggregate is /63
  Aggregate: 2001:db8:0:4::/63

  2001:db8:0:4::/63 covers:
    2001:db8:0:4::/64 and 2001:db8:0:5::/64 ✓

Non-aggregable example:
  2001:db8:0:1::/64
  2001:db8:0:3::/64
  Bit patterns: ...0001 and ...0011 → differ in bit 62 AND 63
  Cannot be aggregated cleanly (would include 2001:db8:0:0:: and 2001:db8:0:2:: too)
```

### Longest Prefix Match (LPM)

```
Routers always use the MOST SPECIFIC (longest prefix) matching route.

Routing table:
  2001:db8::/32      via ISP upstream
  2001:db8:1::/48    via Site A router
  2001:db8:1:2::/64  via VLAN 2 gateway

Packet destined to 2001:db8:1:2::100:

  Matches 2001:db8::/32    (prefix length 32)  ← less specific
  Matches 2001:db8:1::/48  (prefix length 48)  ← more specific
  Matches 2001:db8:1:2::/64(prefix length 64)  ← MOST specific → USED

The /64 route wins. LPM is used in all IPv6 routing.

This is identical to IPv4 behavior.
```

---

## 19. IPv6 in Cloud Environments

### AWS IPv6 Subnetting

```
AWS VPC IPv6 Architecture:

  1. AWS assigns a /56 IPv6 CIDR to each VPC
     (you cannot choose the prefix — AWS assigns from 2600::/12)
  2. Each subnet gets a /64 from the VPC's /56
  3. A /56 gives 2^(64-56) = 2^8 = 256 subnets (/64 each) per VPC

  +---------------------------+
  |   VPC IPv6: /56           |  e.g., 2600:1f18:abcd:ef00::/56
  +---------------------------+
       |         |        |
  +----+    +----+    +---+
  |/64 |    |/64 |    |/64|    (subnet-a, subnet-b, subnet-c)
  +----+    +----+    +---+

  Subnet CIDR example:
    VPC CIDR:    2600:1f18:1234:5600::/56
    Subnet 1:    2600:1f18:1234:5600::/64   (bits 57-64 = 00000000)
    Subnet 2:    2600:1f18:1234:5601::/64   (bits 57-64 = 00000001)
    ...
    Subnet 256:  2600:1f18:1234:56ff::/64   (bits 57-64 = 11111111)

  EC2 instances get:
    - EUI-64 derived GUA from subnet prefix
    - Link-local fe80::/64 (auto)
    - No NAT needed for IPv6 (unless using Egress-Only IGW)

  Egress-Only Internet Gateway:
    IPv6 equivalent of NAT Gateway for outbound-only (IPv6 is globally routable
    but you may want outbound-only for security — like private subnets in IPv4)
```

### GCP IPv6 Subnetting

```
GCP VPC IPv6 (as of 2022+):

  Two modes:
    1. External IPv6 subnets: publicly routable (GUA from Google's space)
    2. Internal IPv6 subnets: ULA (fd20::/20 from GCP's ULA allocation)

  GCP assigns a /48 per VPC region (for external) or /48 ULA (for internal)
  Subnets get /64 from the VPC /48.

  +-------------------------------+
  |  VPC External /48             |  e.g., 2600:1900:4000:abcd::/48
  +-------------------------------+
         |          |
    +----+      +----+
    |/64 |      |/64 |       (one per subnet)
    +----+      +----+

  Unlike AWS:
    - GCP gives /48 (AWS gives /56) → 65536 subnets vs 256 subnets per VPC
    - GCP allows you to request specific ULA prefixes
    - Internal IPv6 uses fd20::/20 (Google's ULA range for internal VPC traffic)
```

### Azure IPv6 Subnetting

```
Azure VNet IPv6:

  Azure requires DUAL-STACK (you must have both IPv4 and IPv6 CIDRs)
  Azure does NOT support IPv6-only VNets (as of 2024)

  IPv6 address space: /48 from Microsoft's GUA space
  Subnets: /64 each (mandatory)
  
  +----------------------------------+
  |  VNet IPv4: 10.0.0.0/16          |
  |  VNet IPv6: 2603:10b6:408::/48   |
  +----------------------------------+
        |                |
   +----+----+      +----+----+
   | IPv4/28 |      | IPv4/28 |
   | IPv6/64 |      | IPv6/64 |
   +---------+      +---------+

  Azure Load Balancer, NSG, and most features support dual-stack.
  AKS supports IPv6 (dual-stack cluster as of 1.21+).
```

### Cloud Security Considerations for IPv6

```
1. Security Groups / NSGs — must explicitly allow IPv6 rules
   Many organizations add IPv4 rules but forget IPv6 → unexpected exposure

2. No implicit NAT hiding — IPv6 addresses are publicly routable
   Every instance has a public address unless you use ULA/internal-only

3. Egress filtering — critical in cloud
   Without explicit egress rules, IPv6 traffic may bypass IPv4-only firewalls

4. Logging — ensure flow logs capture IPv6
   AWS VPC Flow Logs: include IPv6 by default if enabled
   GCP: VPC Flow Logs capture both
   Azure: NSG Flow Logs include IPv6

5. BGP hijacking risk — cloud provider assigns prefixes
   You cannot choose IPv6 prefixes in most clouds → provider-dependent security posture
```

---

## 20. IPv6 in Kubernetes

### Pod CIDR and Node CIDR for IPv6

```
Kubernetes dual-stack (IPv4+IPv6) or IPv6-only clusters:

  IPv4 cluster: --pod-network-cidr=10.244.0.0/16
  IPv6 cluster: --pod-network-cidr=fd00:10:244::/48

  Node gets a /64 from the cluster /48 (or /56 from CNI IPAM):
    Node 1: fd00:10:244:1::/64
    Node 2: fd00:10:244:2::/64
    ...

  Pod on Node 1: fd00:10:244:1::pod-id/128 (typically /128 per pod)

  Service CIDR (IPv6):
    --service-cluster-ip-range=fd00:10:96::/112
    (a /112 gives 2^16 = 65536 service IPs)

Dual-stack kubeadm example:
  kubeadm init \
    --pod-network-cidr=10.244.0.0/16,fd00:10:244::/48 \
    --service-cidr=10.96.0.0/12,fd00:10:96::/112

CNI plugins with IPv6 support:
  Calico  : Full dual-stack, BGP for IPv6 routing
  Cilium  : Full IPv6, eBPF-based, excellent for IPv6-only
  Flannel : Basic dual-stack (VXLAN mode)
  Weave   : Dual-stack support
```

### IPv6 Service Addressing in Kubernetes

```
Services get a virtual IP (ClusterIP) from service CIDR:
  IPv4: 10.96.0.1    (kubernetes default service)
  IPv6: fd00:10:96::1

DNS (CoreDNS) resolves service names to ClusterIPs.
For dual-stack services, CoreDNS returns both A (IPv4) and AAAA (IPv6) records.

NodePort services:
  IPv4: <node-ipv4>:<port>
  IPv6: [<node-ipv6>]:<port>  (bracket notation)

NetworkPolicy for IPv6:
  spec:
    ingress:
    - from:
      - ipBlock:
          cidr: "fd00:10:244::/48"  # Allow from pod CIDR
```

---

## 21. Transition Mechanisms

### Dual-Stack

```
Both IPv4 and IPv6 configured on the same interface/host.

+------------------+
|    Host / Node   |
|  IPv4: 10.0.0.1  |
|  IPv6: 2001::1   |
+------------------+
        |
+-------+-------+
|               |
IPv4 network   IPv6 network
(backward compat)  (forward path)

Applications choose based on DNS resolution:
  - If AAAA record exists, prefer IPv6 (RFC 6724 happy eyeballs)
  - Fall back to IPv4 if IPv6 fails

This is the recommended transition strategy.
Cost: doubles routing complexity and address management.
```

### 6to4 (Deprecated)

```
Encapsulates IPv6 in IPv4 packets (protocol 41).
Prefix: 2002::/16

  IPv6 address formed from IPv4:
    2002 : AABB : CCDD :: where AA.BB.CC.DD is the IPv4 address

  Deprecated: RFC 7526 (2015) — do not use.
  Reason: relay routers unreliable, security issues.
```

### 6in4 (Manual Tunnels)

```
Manually configured IPv6-in-IPv4 tunnel.
Protocol 41 encapsulation.
Requires static endpoints.

Used in:
  - Hurricane Electric (HE.net) tunnel broker
  - ISP interconnects where IPv6 not natively available
  - Lab/testing environments

Config (Linux):
  ip tunnel add tun0 mode sit remote 192.0.2.1 local 192.0.2.2 ttl 255
  ip link set tun0 up
  ip addr add 2001:db8::2/64 dev tun0
  ip route add ::/0 via 2001:db8::1 dev tun0
```

### NAT64 and DNS64

```
NAT64 (RFC 6146): Translates IPv6 packets to IPv4 packets at a gateway.
Allows IPv6-only hosts to reach IPv4-only servers.

Well-known prefix: 64:ff9b::/96  (RFC 6052)
  The last 32 bits hold the IPv4 address.
  64:ff9b::192.0.2.1 = represents 192.0.2.1

How it works:
  IPv6-only host → DNS64 server
    Host asks for www.example.com AAAA record
    DNS64: No AAAA exists, synthesize one:
      A record: 93.184.216.34
      Synthesized AAAA: 64:ff9b::5db8:d822  (64:ff9b:: + 93.184.216.34)
    Returns synthesized AAAA to host

  Host sends packet to 64:ff9b::5db8:d822
  NAT64 gateway intercepts, translates to IPv4 93.184.216.34
  Returns IPv4 response, translates back to IPv6

Architecture:
  IPv6 Host → [DNS64 Server] → [NAT64 Gateway] → IPv4 Internet

+----------+        +---------+       +--------+       +--------------+
| IPv6-only|---AAAA→|  DNS64  |       | NAT64  |       | IPv4 Server  |
|  client  |←synthAAA---------+       | Gateway|       | 93.184.x.x   |
+----------+                          +--------+       +--------------+
     |                                    |                    |
     |--- IPv6 pkt to 64:ff9b::IPv4 ---→ |--- IPv4 pkt ----→ |
     |                                    |← IPv4 reply ------+
     |←---- IPv6 response ---------------+

Used in:
  - iOS/Apple private relay (all Apple devices use NAT64/DNS64)
  - Mobile carrier IPv6-only networks
  - Cloud-native IPv6-only pods needing to reach legacy IPv4
```

### CLAT/PLAT (464XLAT)

```
464XLAT (RFC 6877): Stateless IPv4-in-IPv6 for mobile networks.

PLAT (Provider-side): NAT64 gateway at provider
CLAT (Customer-side): Stateless translator on device that converts IPv4→IPv6

Allows apps that use IPv4 literally (hardcoded IPs) to work on IPv6-only networks.

Device has:
  IPv4: 127.0.0.2 (loopback - CLAT synthetic)
  IPv6: Real IPv6 address

When app sends to 8.8.8.8:
  CLAT converts IPv4→IPv6 (64:ff9b::808:808)
  Network sends as pure IPv6
  PLAT (NAT64) converts back to IPv4 at edge
```

---

## 22. Security Threat Model for IPv6 Subnets

### Threat Overview

```
+----------------------+----------------------------------+-----------------------------+
| Threat               | Attack Vector                    | Mitigation                  |
+----------------------+----------------------------------+-----------------------------+
| RA Flooding/Spoofing | Fake Router Advertisements       | RA Guard (RFC 6105)         |
| DHCPv6 Rogue Server  | Fake DHCPv6 Advertise            | DHCPv6 Shield               |
| NDP Spoofing         | Fake Neighbor Advertisements     | SEND / SeND CGA             |
| NDP Cache Exhaustion | 10s of thousands of NS probes    | NDP rate limiting on router |
| ICMPv6 Amplification | Multicast-based amplification    | Ingress multicast filtering |
| Address Scanning     | Sequential scan of /64 subnet    | Near-impossible (2^64)      |
| Covert Channels      | Large IID space for steganography| DPI / flow analysis         |
| Privacy Leak via IID | EUI-64 tracks MAC address        | Privacy Extensions (RFC 4941)|
| Transition Attacks   | 6to4/Teredo bypass firewall      | Block 6to4/Teredo at border |
| Extension Header DoS | Long/malformed extension headers | Filter at edge, HW offload  |
| Fragmentation Attack | Atomic fragment attack           | Filter frag ID=0 (RFC 6946) |
| BGP IPv6 Hijack      | Announce more-specific prefix    | RPKI ROA validation         |
+----------------------+----------------------------------+-----------------------------+
```

### RA Guard Configuration

```
Cisco IOS-XE:
  ipv6 nd raguard policy RA_GUARD_POLICY
    device-role host           ! Drop RA from host ports
  !
  interface GigabitEthernet1/0/1
    ipv6 nd raguard attach-policy RA_GUARD_POLICY

Linux iptables/ip6tables:
  # Block RA on host interfaces (not from your real router)
  ip6tables -A INPUT -p icmpv6 --icmpv6-type router-advertisement -j DROP
  
  # Block on all interfaces except trusted:
  ip6tables -A INPUT -i eth0 -p icmpv6 --icmpv6-type router-advertisement \
            -s fe80::router_mac_derived_addr -j ACCEPT
  ip6tables -A INPUT -p icmpv6 --icmpv6-type router-advertisement -j DROP

Kernel sysctl (server hardening):
  # Disable RA acceptance on non-router hosts
  sysctl -w net.ipv6.conf.all.accept_ra=0
  sysctl -w net.ipv6.conf.default.accept_ra=0
  # Per-interface:
  sysctl -w net.ipv6.conf.eth0.accept_ra=0
```

### IPv6 Firewall Rules (ip6tables)

```
# Baseline IPv6 firewall for a server

ip6tables -F
ip6tables -X
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT ACCEPT

# Allow established/related
ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
ip6tables -A INPUT -i lo -j ACCEPT

# ICMPv6 — MUST allow specific types (RFC 4890)
# Allow for NDP, PMTUD, etc.
ip6tables -A INPUT -p icmpv6 --icmpv6-type 1   -j ACCEPT  # Destination Unreachable
ip6tables -A INPUT -p icmpv6 --icmpv6-type 2   -j ACCEPT  # Packet Too Big (PMTUD critical!)
ip6tables -A INPUT -p icmpv6 --icmpv6-type 3   -j ACCEPT  # Time Exceeded
ip6tables -A INPUT -p icmpv6 --icmpv6-type 4   -j ACCEPT  # Parameter Problem
ip6tables -A INPUT -p icmpv6 --icmpv6-type 133 -j ACCEPT  # RS
ip6tables -A INPUT -p icmpv6 --icmpv6-type 134 -j ACCEPT  # RA
ip6tables -A INPUT -p icmpv6 --icmpv6-type 135 -j ACCEPT  # NS
ip6tables -A INPUT -p icmpv6 --icmpv6-type 136 -j ACCEPT  # NA
ip6tables -A INPUT -p icmpv6 --icmpv6-type 143 -j ACCEPT  # MLD
# Block all other ICMPv6 (echo optional):
ip6tables -A INPUT -p icmpv6 --icmpv6-type echo-request -j ACCEPT  # optional
ip6tables -A INPUT -p icmpv6 -j DROP

# Block martian sources
ip6tables -A INPUT -s ::1 -j DROP                  # loopback as source
ip6tables -A INPUT -s 2001:db8::/32 -j DROP        # documentation
ip6tables -A INPUT -s fc00::/7 -j DROP             # ULA from internet (if at border)
ip6tables -A INPUT -s ff00::/8 -j DROP             # multicast as source

# WARNING: NEVER block ICMPv6 Type 2 (Packet Too Big) — breaks PMTUD → black-hole!
```

### IPv6 Privacy Extensions

```
RFC 4941 — Privacy Extensions for SLAAC
RFC 7217 — Semantically Opaque IID

Without privacy extensions:
  Address = prefix + EUI-64(MAC)
  → MAC visible, stable, trackable across networks

With RFC 4941 temporary addresses:
  IID = SHA-1(stable-secret + last-random + interface-id + counter)
  Rotates every ~1 day (prefer) / ~7 days (valid)
  Different address on every network, every day

With RFC 7217 stable opaque IID:
  IID = F(prefix, interface, network-id, DAD-counter, secret-key)
  Same address on same network always (good for servers)
  Different address on different networks (good for privacy)
  Not trackable across networks

Linux configuration:
  # Enable privacy extensions (temporary addresses)
  sysctl -w net.ipv6.conf.all.use_tempaddr=2
  sysctl -w net.ipv6.conf.default.use_tempaddr=2
  # 0 = disabled, 1 = generate but don't prefer, 2 = generate and prefer

  # Stable opaque IIDs (modern kernels, RFC 7217)
  # NetworkManager enables this by default in modern distros
  # Check: ip addr show | grep "scope global"
  # Look for "stable-privacy" in address flags
```

### Path MTU Discovery in IPv6

```
IPv6 DOES NOT allow fragmentation by intermediate routers.
Only the SOURCE can fragment.
Fragment header (extension header type 44) required for fragmented packets.

Minimum MTU: 1280 bytes (IPv6 requires this minimum on all links)
Ethernet: 1500 bytes (standard) or 9000 bytes (jumbo frames)
IPv6 header: 40 bytes fixed (vs IPv4 20 bytes)
Available payload: 1500 - 40 = 1460 bytes (no options in base header)

PMTUD process:
  Source sends large packet (e.g., 1500 bytes)
  Intermediate link has MTU 1400 bytes
  Router drops packet, sends back ICMPv6 Type 2 (Packet Too Big)
    with Next-Hop MTU = 1400
  Source retransmits at 1400 bytes
  
CRITICAL: If ICMPv6 Type 2 is blocked → PMTUD black-hole!
  Connections hang silently for large transfers.
  NEVER block ICMPv6 Type 2 at any firewall.

Black-hole detection: TCP MSS clamping as backup
  iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
           -m tcpmss --mss 1281:65535 \
           -j TCPMSS --clamp-mss-to-pmtu
```

---

## 23. Practical Worked Examples

### Example 1: Enterprise /48 Allocation Plan

```
Organization: Acme Corp
Allocation: 2001:db8:acme::/48  (fictional, using documentation prefix)
Sites: HQ, Branch-A, Branch-B, DC-East, DC-West

Plan:

Bits 48-51 (nibble 1 of hextet 4) = Site ID (0-15 max)
Bits 52-55 (nibble 2 of hextet 4) = Zone ID (0-15)
Bits 56-59 (nibble 3 of hextet 4) = VLAN class (0-15)
Bits 60-63 (nibble 4 of hextet 4) = Subnet (0-15)

       Site    Zone   Class  Sub
       ----    ----   -----  ---
HQ:     0      ...    ...    ...  → 2001:db8:acme:0xxx::/64
Branch-A: 1    ...    ...    ...  → 2001:db8:acme:1xxx::/64
Branch-B: 2    ...    ...    ...  → 2001:db8:acme:2xxx::/64
DC-East:  3    ...    ...    ...  → 2001:db8:acme:3xxx::/64
DC-West:  4    ...    ...    ...  → 2001:db8:acme:4xxx::/64

Zone IDs:
  0 = DMZ
  1 = Production
  2 = Staging/Dev
  3 = Management
  4 = Infrastructure (routers, switches)
  5 = Storage
  f = Interconnects/P2P

Class IDs:
  0 = Servers
  1 = VMs/Containers
  2 = Workstations
  3 = IoT/OT
  f = Network devices

Specific subnets:
  2001:db8:acme:0010::/64  → HQ(0) DMZ(0) Servers(1) Sub0 = HQ DMZ Server subnet 0
  2001:db8:acme:0011::/64  → HQ(0) DMZ(0) Servers(1) Sub1 = HQ DMZ Server subnet 1
  2001:db8:acme:0110::/64  → HQ(0) Prod(1) Servers(1) Sub0 = HQ Prod Servers
  2001:db8:acme:3111::/64  → DC-East(3) Prod(1) VMs(1) Sub1 = DC-East Prod VMs
  2001:db8:acme:3f4f::/127 → DC-East(3) Interconnect(f) Infra(4) P2P sub = P2P link

P2P router link:
  2001:db8:acme:3f4f::/127
    Router-A: 2001:db8:acme:3f4f::0  (/127)
    Router-B: 2001:db8:acme:3f4f::1  (/127)
```

### Example 2: Calculate Subnets from a /48

```
Given: fd12:3456:7890::/48

Q1: How many /64 subnets can you create?
A: 2^(64-48) = 2^16 = 65,536 subnets

Q2: What is the 100th /64 subnet?
A: Start at fd12:3456:7890:0000::/64
   100 decimal = 0x0064
   100th subnet (0-indexed at 0): fd12:3456:7890:0063::/64
   100th subnet (1-indexed at 1): fd12:3456:7890:0064::/64
   (clarify indexing — usually 0-indexed)

Q3: What is the last /64 subnet?
A: fd12:3456:7890:ffff::/64

Q4: Split fd12:3456:7890::/48 into /52 subnets. How many?
A: 2^(52-48) = 2^4 = 16 /52 subnets
   Each /52 contains 2^(64-52) = 2^12 = 4096 /64 subnets

   Subnet list:
   fd12:3456:7890:0000::/52  (covers :0000 to :0fff)
   fd12:3456:7890:1000::/52  (covers :1000 to :1fff)
   fd12:3456:7890:2000::/52
   ...
   fd12:3456:7890:f000::/52  (covers :f000 to :ffff)

Q5: Is 2001:db8:1:2:3:4:5:6 in the subnet 2001:db8:1::/48?
A: Network prefix of address: take first 48 bits = 2001:0db8:0001
   Subnet network prefix: 2001:0db8:0001
   Equal → YES, the address is in the subnet.

Q6: Is 2001:db8:1::1 in 2001:db8:1:0::/64?
A: Network prefix of address (64 bits): 2001:0db8:0001:0000
   Subnet network prefix: 2001:0db8:0001:0000
   Equal → YES.

Q7: Is 2001:db8:1::1 in 2001:db8:1:1::/64?
A: Network prefix of address (64 bits): 2001:0db8:0001:0000
   Subnet network prefix: 2001:0db8:0001:0001
   NOT equal (hextet 4: 0000 ≠ 0001) → NO.
```

### Example 3: EUI-64 Calculation

```
MAC: AA:BB:CC:DD:EE:FF

Step 1: Insert FF:FE in middle
  AA:BB:CC : FF:FE : DD:EE:FF

Step 2: Flip U/L bit (bit 6 of first octet, 0-indexed from MSB)
  0xAA = 1010 1010
  Bit 6 from MSB = bit index 1 from LSB = ...0
  Actually: U/L bit is bit 6 counting from bit 7 (MSB) = bit 1 from LSB
  
  Let me be precise:
  Octet = ABCDEFGH (A=MSB=bit7, G=bit1, H=LSB=bit0)
  U/L bit = bit 1 (second from LSB, G position) in IEEE 802
  Wait — let me use standard definition:
  
  IEEE 802 defines: bit 6 of first octet (counting bit 0 as LSB)
  = bit position 1 in standard transmission order (counting from 0 at MSB-first)
  
  0xAA = 1010 1010
  Bit numbering (MSB=7 to LSB=0): 1(7) 0(6) 1(5) 0(4) 1(3) 0(2) 1(1) 0(0)
  U/L bit = bit 1 = 1 (locally administered)
  Flip bit 1: 1010 1010 → 1010 1000 = 0xA8

Step 3: Form IID
  A8:BB:CC:FF:FE:DD:EE:FF
  Group as 16-bit pairs:
  A8BB : CCFF : FEDD : EEFF

Step 4: Full address with prefix 2001:db8:1::/64
  2001:db8:1::a8bb:ccff:fedd:eeff

Verification:
  Original MAC: AA:BB:CC:DD:EE:FF
    0xAA = 1010 1010 → U/L=1 (locally administered)
  After flip: 0xA8 = 1010 1000 → U/L=0 (universally administered in EUI-64 terms)
```

### Example 4: Supernetting / Aggregation

```
Given four /64 subnets to aggregate:
  2001:db8:0:10::/64
  2001:db8:0:11::/64
  2001:db8:0:12::/64
  2001:db8:0:13::/64

Hextet 4 values: 0x0010, 0x0011, 0x0012, 0x0013

Binary:
  0x0010 = 0000 0000 0001 0000
  0x0011 = 0000 0000 0001 0001
  0x0012 = 0000 0000 0001 0010
  0x0013 = 0000 0000 0001 0011

Common prefix: 0000 0000 0001 00xx (first 14 bits of hextet 4)
Position of first differing bit: bit 15 and 16 of hextet 4 (from left, 1-indexed)
= bit position 62 and 63 in full 128-bit address (if hextet 4 is bits 49-64)

Wait, let me count properly:
  Hextet 4 = bits 49 to 64 (1-indexed)
  Common prefix within hextet 4 = first 14 bits
  So total prefix length = 48 (hextets 1-3) + 14 = 62

  Aggregate: 2001:db8:0:10::/62

Verify: 2001:db8:0:10::/62 covers
  2001:db8:0:0010:: to 2001:db8:0:0013::ffff:ffff:ffff:ffff
  = all four /64s ✓

Double-check: does it include anything extra?
  /62 in hextet 4 means last 2 bits of hextet 4 are free → covers 0x10,0x11,0x12,0x13
  That's exactly our 4 subnets ✓
```

---

## 24. Quick Reference Tables

### Prefix Length to Subnet Count (from /48)

```
Desired   | Prefix  | # Subnets  | Addresses
Sub-Size  | Length  | from /48   | per Subnet
----------+---------+------------+------------------------------
/48       |  /48    |          1 | 2^80 ≈ 1.2 × 10^24
/52       |  /52    |         16 | 2^76 ≈ 7.5 × 10^22
/56       |  /56    |        256 | 2^72 ≈ 4.7 × 10^21
/60       |  /60    |      4,096 | 2^68 ≈ 2.9 × 10^20
/64       |  /64    |     65,536 | 2^64 ≈ 1.8 × 10^19
/68       |  /68    |  1,048,576 | 2^60 ≈ 1.2 × 10^18
/96       |  /96    | 2^48 ≈ 2.8×10^14 | 2^32 ≈ 4.3 billion
/127      |  /127   | 2^79       | 2
/128      |  /128   | 2^80       | 1
```

### Key Multicast Addresses

```
Address        | Name                          | Use
---------------+-------------------------------+------------------------------
ff02::1        | All nodes (link-local)        | Like broadcast
ff02::2        | All routers (link-local)      | RS destination
ff02::5        | OSPFv3 all SPF routers        | OSPF hello
ff02::6        | OSPFv3 DR/BDR                 | OSPF DR election
ff02::9        | RIPng                         | RIP updates
ff02::a        | EIGRP                         | EIGRP hello
ff02::d        | PIM routers                   | PIM hello
ff02::16       | MLDv2 routers                 | MLD queries
ff02::1:2      | All DHCP relay agents/servers | DHCPv6 client→server
ff05::1:3      | All DHCP servers (site)       | DHCPv6 server discovery
ff02::1:ffXX:X | Solicited-node multicast      | NDP (per host)
```

### ICMPv6 Types to Never Block

```
Type | Name                  | Why Critical
-----+-----------------------+-----------------------------------------------
1    | Destination Unreachable| Path failure signaling
2    | Packet Too Big        | PMTUD — MUST NOT BLOCK or black-holes occur
3    | Time Exceeded         | Traceroute, loop detection
4    | Parameter Problem     | Protocol error feedback
133  | Router Solicitation   | SLAAC
134  | Router Advertisement  | SLAAC, gateway discovery
135  | Neighbor Solicitation | NDP (ARP replacement)
136  | Neighbor Advertisement| NDP (ARP reply replacement)
143  | MLDv2 Report          | Multicast group management
```

### Common Address Types at a Glance

```
Address/Prefix    | Type                  | Routable?  | Scope
------------------+-----------------------+------------+------------------
::1/128           | Loopback              | No         | Host
::/128            | Unspecified           | No         | None
fe80::/10         | Link-local unicast    | No         | Link
fc00::/7          | Unique Local (ULA)    | Org-only   | Organization
2000::/3          | Global Unicast (GUA)  | Yes        | Global
ff02::/16         | Link-local multicast  | No         | Link
ff05::/16         | Site-local multicast  | No         | Site
ff0e::/16         | Global multicast      | Yes        | Global
2001:db8::/32     | Documentation         | No (filter)| N/A
64:ff9b::/96      | NAT64 well-known      | Special    | Translation
::ffff:0:0/96     | IPv4-mapped           | No         | Host
```

---

## 25. Next 3 Steps

### Step 1 — Build a Lab IPv6 Network

```bash
# On Linux — enable IPv6 routing
sysctl -w net.ipv6.conf.all.forwarding=1

# Assign ULA addresses to interfaces
ip addr add fd00:1:2:3::1/64 dev eth0
ip addr add fd00:1:2:4::1/64 dev eth1

# Add routes
ip -6 route add fd00:1:2::/48 via fd00:1:2:3::2

# Test NDP
ip -6 neigh show
ping6 -c 3 fd00:1:2:3::2

# Analyze with tcpdump (ICMPv6 NDP traffic)
tcpdump -i eth0 -n icmp6

# Verify SLAAC is working
radvd (install radvd, configure /etc/radvd.conf)
# Minimal radvd.conf:
# interface eth0 {
#   AdvSendAdvert on;
#   prefix fd00:1:2:3::/64 {
#     AdvOnLink on;
#     AdvAutonomous on;
#   };
# };
```

### Step 2 — Practice Subnetting Calculations

```
Work through these manually, then verify with tools:

1. Subnet 2001:db8:1::/48 into 8 equal blocks. What prefix? List them.
   Answer: /51 (48+3=51), 2^3=8 blocks
   
2. Is 2001:db8:1:abc0::1 in 2001:db8:1:abc0::/64? In 2001:db8:1:abc::/60?
   
3. Calculate EUI-64 IID for MAC 08:00:27:ab:cd:ef

4. Aggregate: 2001:db8:ff:10::/64, :11:, :12:, :13:, :14:, :15:, :16:, :17::
   (8 consecutive /64s → one summary)

Verification tools:
  ipcalc  -6 (many distros)
  python3 -c "import ipaddress; n=ipaddress.IPv6Network('2001:db8::/48'); list(n.subnets(prefixlen_diff=16))"
  sipcalc (apt install sipcalc)
```

### Step 3 — Harden IPv6 in Production

```bash
# 1. Disable RA on all server interfaces (they are not routers)
cat >> /etc/sysctl.d/99-ipv6-hardening.conf << 'EOF'
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
net.ipv6.conf.all.forwarding = 0
EOF
sysctl --system

# 2. Configure ip6tables baseline (see Section 22)

# 3. Enable IPv6 flow logs in your cloud
# AWS:
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs

# 4. Audit for IPv6 exposure
nmap -6 -sV fd00::/64           # Scan your own subnet
nmap -6 --script ipv6-ra-flood  # Test RA guard effectiveness
```

---

## 26. References

```
RFCs (Authoritative):
  RFC 4291  — IPv6 Addressing Architecture (core)
  RFC 4862  — Stateless Address Autoconfiguration (SLAAC)
  RFC 4861  — Neighbor Discovery Protocol (NDP)
  RFC 4193  — Unique Local IPv6 Unicast Addresses (ULA)
  RFC 3513  — IPv6 Addressing (superseded by 4291, historical)
  RFC 6177  — IPv6 Address Assignment to End Sites (/48, /56, /60)
  RFC 6164  — /127 Prefix for IPv6 Point-to-Point Links
  RFC 6106  — IPv6 RA for DNS (RDNSS, DNSSL)
  RFC 4941  — Privacy Extensions for SLAAC
  RFC 7217  — Semantically Opaque Interface Identifiers (stable privacy)
  RFC 4443  — ICMPv6
  RFC 4890  — Recommendations for Filtering ICMPv6
  RFC 3971  — Secure Neighbor Discovery (SEND)
  RFC 6146  — Stateful NAT64
  RFC 6147  — DNS64
  RFC 6052  — IPv6 Addressing of IPv4/IPv6 Translators
  RFC 6877  — 464XLAT (CLAT/PLAT)
  RFC 7526  — Deprecating 6to4
  RFC 3633  — IPv6 Prefix Options for DHCPv6 (PD)
  RFC 8200  — IPv6 Specification (obsoletes RFC 2460)

IETF Working Groups:
  6man  — IPv6 Maintenance
  v6ops — IPv6 Operations
  dhc   — DHC (DHCPv6)

Tools:
  ipcalc, sipcalc, ipv6calc — subnet calculation
  tcpdump, wireshark         — packet analysis
  radvd                      — RA daemon (Linux)
  dibbler, dhcpcd            — DHCPv6 client/server
  nmap -6                    — IPv6 scanning
  ping6 / ping -6            — connectivity test
  traceroute6 / tracepath6   — path analysis
  ip -6 addr/route/neigh     — Linux IPv6 config/state
```

---

*End of Guide — IPv6 Network Subnetting Complete Reference*
*Version: 1.0 | April 2026*

**~3,800 lines, 26 sections, fully self-contained.** Here's a structural summary of what's covered and a few things worth calling out explicitly:

---

**Key non-obvious things engineered into the guide:**

**The /64 sacredness** (§10) — not just a convention. SLAAC's EUI-64, NDP solicited-node multicast, privacy extensions, and most kernel implementations hard-code assumptions around it. Breaking /64 silently breaks SLAAC, and often NDP too. Use /127 for P2P (RFC 6164) and /128 for loopbacks — those are the only valid exceptions.

**The U/L bit flip in EUI-64** (§13) — frequently misunderstood. The inversion is not a bug; it maps IEEE's "universal=0" to IETF EUI-64's "globally unique=1". VMs with locally-administered MACs (bit already = 1) will have the flip produce a 0, which looks odd until you understand the semantics.

**ICMPv6 Type 2 = never block** (§22) — this is the single most common IPv6 misconfiguration in production. Blocking Packet Too Big breaks PMTUD silently. TCP connections work fine for small transfers and hang permanently for large ones. This bites people in Kubernetes `NetworkPolicy` and cloud `SecurityGroup` rules constantly.

**DHCPv6 never delivers the default gateway** (§15) — this catches people migrating from IPv4 DHCP. The gateway always comes from RA, even in a fully stateful DHCPv6 environment. If RA is broken, hosts get addresses but no gateway.

**RA spoofing attack surface** (§16/§22) — in any environment where you don't control the L2 (shared cloud, co-lo, container networking), a rogue RA can silently reroute all traffic on a /64 before any firewall sees it. `accept_ra=0` sysctl on all non-router hosts is mandatory hardening.

---

**Next 3 steps** (also in §25):
1. Stand up `radvd` on a Linux box, capture the RA/NS/NA exchange in `tcpdump`, and manually expand the EUI-64 from the captured IID back to the MAC.
2. Write a subnet calculator in Go/Rust that: parses CIDR, enumerates subnets, checks containment — forces you to internalize the bit math.
3. Audit every security group / firewall rule set you own for: missing IPv6 rules, blocked ICMPv6 Type 2, and `accept_ra` state on production servers.