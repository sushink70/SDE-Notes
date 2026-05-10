# IPv4 Network Subnetting — Complete & Comprehensive Guide

---

## Table of Contents

1. [Binary & Decimal Foundations](#1-binary--decimal-foundations)
2. [IPv4 Address Structure](#2-ipv4-address-structure)
3. [Address Classes (Classful Addressing)](#3-address-classes-classful-addressing)
4. [Subnet Mask — Deep Dive](#4-subnet-mask--deep-dive)
5. [CIDR — Classless Inter-Domain Routing](#5-cidr--classless-inter-domain-routing)
6. [Network Address, Broadcast, Host Range](#6-network-address-broadcast-host-range)
7. [Subnetting Mathematics — The Core Engine](#7-subnetting-mathematics--the-core-engine)
8. [Subnetting a Network — Step-by-Step](#8-subnetting-a-network--step-by-step)
9. [VLSM — Variable Length Subnet Masking](#9-vlsm--variable-length-subnet-masking)
10. [Supernetting / Route Aggregation / CIDR Summarization](#10-supernetting--route-aggregation--cidr-summarization)
11. [Special & Reserved IPv4 Addresses](#11-special--reserved-ipv4-addresses)
12. [Private Address Ranges & NAT Context](#12-private-address-ranges--nat-context)
13. [Subnet Design Methodology](#13-subnet-design-methodology)
14. [Subnetting Shortcuts & Mental Math Tricks](#14-subnetting-shortcuts--mental-math-tricks)
15. [IP Routing & Subnet Interaction](#15-ip-routing--subnet-interaction)
16. [Practical Examples & Worked Problems](#16-practical-examples--worked-problems)
17. [Linux Kernel & Networking Stack Context](#17-linux-kernel--networking-stack-context)
18. [Quick Reference Tables](#18-quick-reference-tables)

---

## 1. Binary & Decimal Foundations

### 1.1 Why Binary Matters

IPv4 addressing is **entirely binary** at the hardware and kernel level. All subnet operations — masking, AND, OR, XOR — are bitwise operations on 32-bit unsigned integers. Understanding binary is not optional; it IS subnetting.

### 1.2 Positional Value of a Byte (Octet)

Each IPv4 address is 4 octets (bytes = 8 bits each = 32 bits total).

```
Bit Position:   7     6     5     4     3     2     1     0
Power of 2:    2^7   2^6   2^5   2^4   2^3   2^2   2^1   2^0
Decimal Value: 128    64    32    16     8     4     2     1
```

**Sum of all bits set = 128 + 64 + 32 + 16 + 8 + 4 + 2 + 1 = 255**

```
  One Octet (8 bits):
  +-----+-----+-----+-----+-----+-----+-----+-----+
  | 128 |  64 |  32 |  16 |   8 |   4 |   2 |   1 |
  +-----+-----+-----+-----+-----+-----+-----+-----+
     ^                                           ^
   MSB (Most Significant Bit)         LSB (Least Significant Bit)
```

### 1.3 Binary ↔ Decimal Conversion

**Decimal to Binary:**  
Repeatedly divide by 2, collect remainders from bottom to top.

```
Example: 192 → Binary

192 ÷ 2 = 96  remainder 0   ← LSB
 96 ÷ 2 = 48  remainder 0
 48 ÷ 2 = 24  remainder 0
 24 ÷ 2 = 12  remainder 0
 12 ÷ 2 =  6  remainder 0
  6 ÷ 2 =  3  remainder 0
  3 ÷ 2 =  1  remainder 1
  1 ÷ 2 =  0  remainder 1   ← MSB

Read bottom to top: 11000000 = 192  ✓
```

**Faster method — subtract powers of 2:**
```
192:
  192 >= 128? YES → bit 7 = 1, remainder = 64
   64 >= 64?  YES → bit 6 = 1, remainder = 0
    0 >= 32?  NO  → bit 5 = 0
    0 >= 16?  NO  → bit 4 = 0
    0 >= 8?   NO  → bit 3 = 0
    0 >= 4?   NO  → bit 2 = 0
    0 >= 2?   NO  → bit 1 = 0
    0 >= 1?   NO  → bit 0 = 0

Result: 11000000 = 192  ✓
```

**Binary to Decimal:**  
Multiply each bit by its positional value, sum them.

```
11000000 =
  1×128 + 1×64 + 0×32 + 0×16 + 0×8 + 0×4 + 0×2 + 0×1
= 128 + 64
= 192
```

### 1.4 Critical Octet Values to Memorize

```
Binary        Decimal   Common Usage
---------     -------   -------------------------
00000000  =     0       All bits off
10000000  =   128       
11000000  =   192       Class C / /26 block start
11100000  =   224       Class D multicast
11110000  =   240       /28 subnet mask octet
11111000  =   248       /29 subnet mask octet
11111100  =   252       /30 subnet mask octet
11111110  =   254       /31 subnet mask octet
11111111  =   255       All bits on (broadcast / mask)
```

### 1.5 Bitwise AND — The Subnet Operation

The entire concept of "is this host in my subnet?" is a **bitwise AND** between an IP and the subnet mask.

```
Operation: IP_address AND Subnet_mask = Network_address

Example:
  IP:   192.168.10.130  →  11000000.10101000.00001010.10000010
  MASK: 255.255.255.192 →  11111111.11111111.11111111.11000000
  AND:                  →  11000000.10101000.00001010.10000000
                                                       = 192.168.10.128  (network address)

Bitwise AND truth table:
  1 AND 1 = 1
  1 AND 0 = 0
  0 AND 1 = 0
  0 AND 0 = 0
```

---

## 2. IPv4 Address Structure

### 2.1 The 32-Bit Address

```
IPv4 Address = 32 bits = 4 octets, written in dotted-decimal notation

  Octet 1    Octet 2    Octet 3    Octet 4
 [8 bits]   [8 bits]   [8 bits]   [8 bits]
     |          |          |          |
     v          v          v          v
   192    .   168    .    10    .    1
     |          |          |          |
  11000000  10101000  00001010  00000001

Total = 32 bits → 2^32 = 4,294,967,296 possible addresses
```

### 2.2 Two Logical Parts: Network + Host

Every IPv4 address has two conceptual parts divided by the subnet mask:

```
  32 bits total
  <----- n bits ------><---- (32-n) bits ---->
  [  Network Portion  ][    Host Portion     ]
         |                      |
   Identifies the          Identifies the
   network/subnet           specific host

Example with /24:
  192  .  168  .   10  .    1
  [      Network: 24 bits      ][Host: 8 bits]
  192.168.10                .1
```

### 2.3 The Total Address Space

```
Total IPv4 addresses = 2^32 = 4,294,967,296 ≈ 4.3 billion

Address range: 0.0.0.0  →  255.255.255.255

  0.0.0.0         = 00000000.00000000.00000000.00000000
  255.255.255.255 = 11111111.11111111.11111111.11111111
```

---

## 3. Address Classes (Classful Addressing)

Before CIDR (pre-1993), address space was divided into fixed classes. Understanding this is essential because:
1. Many legacy systems still reference classes
2. The kernel's routing code evolved from classful understanding
3. Private ranges are class-based

### 3.1 Class Structure

```
Class  First Octet   First Bits  Network Bits  Host Bits  Default Mask    # Networks      Hosts/Network
-----  -----------   ----------  ------------  ---------  ------------    ----------      -------------
  A      1 - 126       0xxx        8             24        255.0.0.0       126             16,777,214
  B    128 - 191      10xx        16             16        255.255.0.0     16,384          65,534
  C    192 - 223      110x        24              8        255.255.255.0   2,097,152        254
  D    224 - 239      1110        Multicast group addresses (not host assignments)
  E    240 - 255      1111        Experimental / reserved

Notes:
  127.x.x.x  = Loopback (Class A space, but reserved)
  0.x.x.x    = "This" network (reserved, not assigned)
```

### 3.2 Class A Address Space

```
Range: 1.0.0.0 — 126.255.255.255

  First octet always starts with bit 0:  0xxxxxxx

  Network.Host.Host.Host
  [8 bits][      24 bits      ]

  Networks:  2^7 - 2 = 126  (subtract 0.x.x.x and 127.x.x.x)
  Hosts:     2^24 - 2 = 16,777,214 per network

Example: 10.0.0.1/8
  Network:   10.0.0.0
  Broadcast: 10.255.255.255
  Hosts:     10.0.0.1 — 10.0.255.254
```

### 3.3 Class B Address Space

```
Range: 128.0.0.0 — 191.255.255.255

  First octet always starts with bits 10: 10xxxxxx

  Network.Network.Host.Host
  [     16 bits     ][  16 bits  ]

  Networks:  2^14 = 16,384
  Hosts:     2^16 - 2 = 65,534 per network

Example: 172.16.0.1/16
  Network:   172.16.0.0
  Broadcast: 172.16.255.255
  Hosts:     172.16.0.1 — 172.16.255.254
```

### 3.4 Class C Address Space

```
Range: 192.0.0.0 — 223.255.255.255

  First octet always starts with bits 110: 110xxxxx

  Network.Network.Network.Host
  [          24 bits        ][8 bits]

  Networks:  2^21 = 2,097,152
  Hosts:     2^8 - 2 = 254 per network

Example: 192.168.1.1/24
  Network:   192.168.1.0
  Broadcast: 192.168.1.255
  Hosts:     192.168.1.1 — 192.168.1.254
```

### 3.5 Why Classes Became Obsolete

```
Problem: Wasteful allocation

  Company needs 300 hosts:
  ┌─────────────────────────────────────────────────────┐
  │  Class B assigned → 65,534 host capacity            │
  │  Used: 300                                          │
  │  WASTED: 65,234 addresses (99.5% waste!)            │
  └─────────────────────────────────────────────────────┘

  Company needs 300 hosts with Class C:
  ┌─────────────────────────────────────────────────────┐
  │  One /24 = 254 hosts → not enough                   │
  │  Two /24s = 508 hosts → two routing table entries   │
  └─────────────────────────────────────────────────────┘

Solution: CIDR (1993, RFC 1519) — arbitrary prefix lengths
```

---

## 4. Subnet Mask — Deep Dive

### 4.1 What is a Subnet Mask?

A subnet mask is a **32-bit number** where:
- All **1-bits** are contiguous and mark the **network portion**
- All **0-bits** mark the **host portion**
- The transition from 1→0 is always a single boundary (no interleaving)

```
VALID subnet mask:
  11111111.11111111.11111100.00000000  (255.255.252.0)
  ^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^
     contiguous 1s (22)     all 0s (10) ✓

INVALID subnet mask (interleaved — never valid in classful/CIDR):
  11111111.11111111.10101010.00000000
                    ^^^^^^^^
                  alternating — INVALID ✗
```

### 4.2 Subnet Mask Representations

Three equivalent ways to express the same mask:

```
1. Dotted-decimal:  255.255.255.0
2. CIDR prefix:     /24
3. Hex (kernel):    0xFFFFFF00

All three mean: "top 24 bits are network, bottom 8 bits are host"

Conversion:
  255   = 11111111  (8 ones)
  255   = 11111111  (8 ones)
  255   = 11111111  (8 ones)
    0   = 00000000  (8 zeros)
  Total: 24 ones → /24
```

### 4.3 All Valid Subnet Masks

Because bits must be contiguous, only these decimal values can appear in a mask octet:

```
Binary        Decimal   Bits contributed
---------     -------   ----------------
00000000  =     0            0
10000000  =   128            1
11000000  =   192            2
11100000  =   224            3
11110000  =   240            4
11111000  =   248            5
11111100  =   252            6
11111110  =   254            7
11111111  =   255            8
```

Any other value in a subnet mask octet is **invalid** (e.g., 253, 251, 200).

### 4.4 Subnet Mask vs. Wildcard Mask

The **wildcard mask** is the bitwise complement (inversion) of the subnet mask. Used heavily in ACLs (Cisco IOS) and iptables/nftables.

```
Subnet mask:    255.255.255.0   →  11111111.11111111.11111111.00000000
Wildcard mask:    0.0.0.255     →  00000000.00000000.00000000.11111111

Formula: Wildcard = 255.255.255.255 - Subnet_Mask

Example:
  Subnet:   255.255.252.0
  Wildcard: 255.255.255.255
           -255.255.252.0
           = 0.0.3.255

Wildcard mask logic:
  0 bit = must match (fixed)
  1 bit = can be anything (wildcard/don't care)
```

---

## 5. CIDR — Classless Inter-Domain Routing

### 5.1 CIDR Notation

CIDR (RFC 1519, 1993; refined in RFC 4632) expresses a network as:

```
  address / prefix-length

  192.168.10.0/24
  ^           ^
  |           |
  IP address  Prefix length (number of network bits)

The prefix length can be 0 to 32.
```

### 5.2 CIDR Block Sizes

```
Prefix  Mask              Network Bits  Host Bits  Total Addresses  Usable Hosts
------  ----------------  ------------  ---------  ---------------  ------------
  /0    0.0.0.0                0           32      4,294,967,296    4,294,967,294
  /1    128.0.0.0              1           31      2,147,483,648    2,147,483,646
  /2    192.0.0.0              2           30      1,073,741,824    1,073,741,822
  /8    255.0.0.0              8           24         16,777,216      16,777,214
  /16   255.255.0.0           16           16             65,536          65,534
  /17   255.255.128.0         17           15             32,768          32,766
  /18   255.255.192.0         18           14             16,384          16,382
  /19   255.255.224.0         19           13              8,192           8,190
  /20   255.255.240.0         20           12              4,096           4,094
  /21   255.255.248.0         21           11              2,048           2,046
  /22   255.255.252.0         22           10              1,024           1,022
  /23   255.255.254.0         23            9                512             510
  /24   255.255.255.0         24            8                256             254
  /25   255.255.255.128       25            7                128             126
  /26   255.255.255.192       26            6                 64              62
  /27   255.255.255.224       27            5                 32              30
  /28   255.255.255.240       28            4                 16              14
  /29   255.255.255.248       29            3                  8               6
  /30   255.255.255.252       30            2                  4               2
  /31   255.255.255.254       31            1                  2               2*
  /32   255.255.255.255       32            0                  1               1**

* /31: RFC 3021 — point-to-point links, no network/broadcast reserved
** /32: Host route — single IP (loopback, VIP, null route)

Formula:
  Total addresses  = 2^(32 - prefix)
  Usable hosts     = 2^(32 - prefix) - 2   (subtract network + broadcast)
```

### 5.3 The /31 Special Case (RFC 3021)

```
For point-to-point links (e.g., router-to-router):
  /31 gives exactly 2 addresses — both usable as host addresses
  No network address. No broadcast address.

  10.0.0.0/31:
    10.0.0.0  → Router A interface
    10.0.0.1  → Router B interface

Supported in Linux kernel: yes
  ip addr add 10.0.0.0/31 dev eth0   # works
```

### 5.4 The /32 Host Route

```
Represents a single IP address — used for:
  - Loopback (127.0.0.1/32 internally)
  - Null routes (blackhole)
  - VIP (Virtual IP on load balancer)
  - BGP next-hop specification
  - iptables -d 1.2.3.4/32

  ip route add blackhole 10.0.0.5/32
```

---

## 6. Network Address, Broadcast, Host Range

### 6.1 The Three Critical Addresses in a Subnet

```
Given a subnet, you can always derive:

  ┌──────────────────────────────────────────────────────────┐
  │  NETWORK ADDRESS  = IP AND Mask  (all host bits = 0)     │
  │  BROADCAST        = IP OR ~Mask  (all host bits = 1)     │
  │  HOST RANGE       = (Network+1) to (Broadcast-1)         │
  └──────────────────────────────────────────────────────────┘

Example: 192.168.1.100/26

Step 1 — Convert to binary:
  IP:   11000000.10101000.00000001.01100100
  MASK: 11111111.11111111.11111111.11000000

Step 2 — Network Address (IP AND Mask):
  11000000.10101000.00000001.01000000 = 192.168.1.64

Step 3 — Broadcast (set all host bits to 1):
  11000000.10101000.00000001.01111111 = 192.168.1.127

Step 4 — Host Range:
  First: 192.168.1.65
  Last:  192.168.1.126
  Count: 62 hosts (2^6 - 2)
```

### 6.2 Visual Block Diagram

```
192.168.1.0/24 space divided into four /26 subnets:

  192.168.1.0
  |
  +-- [Subnet 1: 192.168.1.0/26]
  |     Network:   192.168.1.0
  |     Hosts:     192.168.1.1  —  192.168.1.62  (62 hosts)
  |     Broadcast: 192.168.1.63
  |
  +-- [Subnet 2: 192.168.1.64/26]
  |     Network:   192.168.1.64
  |     Hosts:     192.168.1.65  —  192.168.1.126 (62 hosts)
  |     Broadcast: 192.168.1.127
  |
  +-- [Subnet 3: 192.168.1.128/26]
  |     Network:   192.168.1.128
  |     Hosts:     192.168.1.129 —  192.168.1.190 (62 hosts)
  |     Broadcast: 192.168.1.191
  |
  +-- [Subnet 4: 192.168.1.192/26]
        Network:   192.168.1.192
        Hosts:     192.168.1.193 —  192.168.1.254 (62 hosts)
        Broadcast: 192.168.1.255
```

### 6.3 Why Network and Broadcast Are Reserved

```
Network address (all host bits = 0):
  → Identifies the subnet itself in routing tables
  → Packets destined to it are invalid host packets
  → ip route show will show this as the route prefix

Broadcast address (all host bits = 1):
  → Directed broadcast: sent to ALL hosts in the subnet
  → Kernel processes at: net/ipv4/ip_input.c
  → ip_route_input_slow() checks RTF_BROADCAST flag
  → Linux drops directed broadcasts by default
     (net.ipv4.ip_forward_broadcast = 0)
```

---

## 7. Subnetting Mathematics — The Core Engine

### 7.1 Fundamental Formulas

```
Given prefix length n:

  Host bits            h = 32 - n
  Total addresses      T = 2^h
  Usable hosts         U = 2^h - 2
  Block size           B = 2^h        (same as T)
  Subnet increment     I = 256 - (interesting octet of mask)

Interesting octet:
  The octet in the mask that is neither 0 nor 255.
  For /24 to /32, it's the 4th octet.
  For /16 to /23, it's the 3rd octet.
  For /8 to /15, it's the 2nd octet.
  For /1 to /7, it's the 1st octet.
```

### 7.2 Block Size and Subnet Increment

The **block size** (also called **subnet increment**) is the most powerful shortcut in subnetting:

```
Block size = 2^(host bits) = 256 - (mask value in interesting octet)

Examples:
  /25 → mask = 255.255.255.128 → interesting = 128 → block = 256-128 = 128
  /26 → mask = 255.255.255.192 → interesting = 192 → block = 256-192 =  64
  /27 → mask = 255.255.255.224 → interesting = 224 → block = 256-224 =  32
  /28 → mask = 255.255.255.240 → interesting = 240 → block = 256-240 =  16
  /29 → mask = 255.255.255.248 → interesting = 248 → block = 256-248 =   8
  /30 → mask = 255.255.255.252 → interesting = 252 → block = 256-252 =   4
  /22 → mask = 255.255.252.0   → interesting = 252 → block = 256-252 =   4 (in 3rd octet)
  /23 → mask = 255.255.254.0   → interesting = 254 → block = 256-254 =   2 (in 3rd octet)

Subnet boundaries are ALWAYS multiples of the block size:
  /26 (block=64): subnets start at 0, 64, 128, 192 (in the relevant octet)
  /27 (block=32): subnets start at 0, 32, 64, 96, 128, 160, 192, 224
  /28 (block=16): subnets start at 0, 16, 32, 48, 64, 80, 96 ...
```

### 7.3 Number of Subnets When Borrowing Bits

When you subnet a network by borrowing **s** bits from the host portion:

```
Number of subnets = 2^s

Examples, starting from 192.168.1.0/24:
  Borrow 1 bit → 2^1 = 2 subnets  → /25
  Borrow 2 bits → 2^2 = 4 subnets → /26
  Borrow 3 bits → 2^3 = 8 subnets → /27
  Borrow 4 bits → 2^4 = 16 subnets → /28
  Borrow 5 bits → 2^5 = 32 subnets → /29
  Borrow 6 bits → 2^6 = 64 subnets → /30
  Borrow 7 bits → 2^7 = 128 subnets → /31

Trade-off:
  More subnets → fewer hosts per subnet
  Fewer subnets → more hosts per subnet

  s = borrowed bits,  h = remaining host bits = original_host_bits - s
  Subnets × Hosts_per_subnet ≈ constant = 2^original_host_bits
```

### 7.4 The Subnet Bit-Borrowing Visualization

```
Original: 192.168.1.0/24
  11000000.10101000.00000001 | 00000000
  [------network: 24 bits---] [host: 8]

Borrow 2 bits (/26):
  11000000.10101000.00000001 | xx | 000000
  [------network: 24 bits---][sub][host:6]
                              ^^
                              00 → Subnet 0 (192.168.1.0)
                              01 → Subnet 1 (192.168.1.64)
                              10 → Subnet 2 (192.168.1.128)
                              11 → Subnet 3 (192.168.1.192)

Each subnet has 6 host bits → 2^6 = 64 addresses → 62 usable hosts
```

### 7.5 Finding Which Subnet an IP Belongs To

```
Method: IP AND Mask = Network Address

Quick method using block size:
  IP: 192.168.1.100, Mask: /26 (block = 64)

  Divide host octet by block size:
    100 ÷ 64 = 1 remainder 36
    Subnet number: 1
    Network start: 1 × 64 = 64
    Network address: 192.168.1.64

  Verify: 100 is between 64 and 127 ✓
  Broadcast: 64 + 64 - 1 = 127
```

---

## 8. Subnetting a Network — Step-by-Step

### 8.1 Procedure A: Given prefix, find all subnets

**Problem:** Subnet 10.0.0.0/8 into /11 subnets. List the first 4.

```
Step 1: Identify host bits and block size
  Original prefix: /8
  New prefix: /11
  Borrowed bits: 11 - 8 = 3
  Subnets created: 2^3 = 8

  Host bits remaining: 32 - 11 = 21
  Hosts per subnet: 2^21 - 2 = 2,097,150

Step 2: Find interesting octet
  /11 mask: 11111111.11100000.00000000.00000000
             255  .  224 .  0  .  0
  Interesting octet: 2nd octet (224)
  Block size: 256 - 224 = 32  (in 2nd octet)

Step 3: List subnets (increment 2nd octet by 32)
  Subnet 0:  10.0.0.0/11    Broadcast: 10.31.255.255
  Subnet 1:  10.32.0.0/11   Broadcast: 10.63.255.255
  Subnet 2:  10.64.0.0/11   Broadcast: 10.95.255.255
  Subnet 3:  10.96.0.0/11   Broadcast: 10.127.255.255
  Subnet 4:  10.128.0.0/11  Broadcast: 10.159.255.255
  Subnet 5:  10.160.0.0/11  Broadcast: 10.191.255.255
  Subnet 6:  10.192.0.0/11  Broadcast: 10.223.255.255
  Subnet 7:  10.224.0.0/11  Broadcast: 10.255.255.255
```

### 8.2 Procedure B: Given number of hosts needed, find prefix

**Problem:** Need subnets with at least 50 hosts each from 172.16.0.0/16.

```
Step 1: Find required host bits
  Need: 50 hosts
  2^h - 2 ≥ 50
  2^h ≥ 52
  2^5 = 32  → too small (30 hosts)
  2^6 = 64  → sufficient (62 hosts) ✓

  Host bits needed: 6
  Prefix: /32 - 6 = /26

Step 2: Find block size
  /26 mask: 255.255.255.192  (192 in 4th octet)
  Block size: 256 - 192 = 64

Step 3: Count subnets
  From /16, borrowing 16-6=10 bits... wait.
  Actually: from /16 we have 16 host bits.
  New prefix /26 means 26-16 = 10 bits borrowed.
  Subnets: 2^10 = 1024 subnets, each with 62 hosts.

Step 4: First few subnets
  172.16.0.0/26    hosts: 172.16.0.1 — 172.16.0.62
  172.16.0.64/26   hosts: 172.16.0.65 — 172.16.0.126
  172.16.0.128/26  hosts: 172.16.0.129 — 172.16.0.190
  172.16.0.192/26  hosts: 172.16.0.193 — 172.16.0.254
  172.16.1.0/26    hosts: 172.16.1.1 — 172.16.1.62
  ...
```

### 8.3 Procedure C: Given number of subnets needed, find prefix

**Problem:** Need at least 30 subnets from 192.168.5.0/24.

```
Step 1: Find required subnet bits
  Need: 30 subnets
  2^s ≥ 30
  2^4 = 16  → too few
  2^5 = 32  → sufficient ✓

  Subnet bits: 5
  New prefix: /24 + 5 = /29

Step 2: Verify host capacity
  Host bits: 32 - 29 = 3
  Hosts per subnet: 2^3 - 2 = 6

Step 3: Block size
  /29 mask: 255.255.255.248 (248 in 4th octet)
  Block size: 256 - 248 = 8

Step 4: List all 32 subnets
  192.168.5.0/29    hosts: .1 — .6
  192.168.5.8/29    hosts: .9 — .14
  192.168.5.16/29   hosts: .17 — .22
  192.168.5.24/29   hosts: .25 — .30
  192.168.5.32/29   hosts: .33 — .38
  ...
  192.168.5.248/29  hosts: .249 — .254
  (32 subnets × 8 addresses = 256 = 2^8 ✓)
```

### 8.4 Complete Step-by-Step Worksheet Template

```
Given: [IP Address] / [Prefix]

1. Subnet mask (dotted-decimal): ___________________
2. Binary representation:
   IP:   __.__.__.__ = ________.________.________.________
   Mask: __.__.__.__ = ________.________.________.________

3. Network address (AND result): __________________
4. Broadcast address (all host bits = 1): __________________
5. First usable host: __________________
6. Last usable host: __________________
7. Number of usable hosts: 2^__ - 2 = __________________
8. Block size: __________________
9. Next subnet starts at: __________________
```

---

## 9. VLSM — Variable Length Subnet Masking

### 9.1 What is VLSM?

VLSM allows different subnets within the same network to have **different prefix lengths** — allocating exactly the right amount of address space to each segment. This is classless subnetting taken to its natural conclusion.

```
Without VLSM (fixed subnetting):
  All subnets same size — wastes addresses in small segments

With VLSM:
  Large dept  → big subnet  → /24 (254 hosts)
  Small dept  → small subnet → /27 (30 hosts)
  Point-to-point link → /30 (2 hosts)
  Single host → /32 (1 host)
```

### 9.2 VLSM Requirements

- Routing protocol must support CIDR (RIPv2, OSPF, EIGRP, BGP — NOT RIPv1)
- All routers must understand classless routing
- Careful address planning required (no overlaps)

### 9.3 VLSM Design Process

**Golden Rule: Allocate largest subnets first, smallest last.**

```
Address Space: 192.168.1.0/24

Requirements:
  Dept A: 100 hosts
  Dept B: 50 hosts
  Dept C: 20 hosts
  Dept D: 10 hosts
  WAN Link 1: 2 hosts (point-to-point)
  WAN Link 2: 2 hosts (point-to-point)

Sort by size (largest first):
  1. Dept A: 100 hosts → need /25 (126 hosts)
  2. Dept B:  50 hosts → need /26 (62 hosts)
  3. Dept C:  20 hosts → need /27 (30 hosts)
  4. Dept D:  10 hosts → need /28 (14 hosts)
  5. WAN 1:    2 hosts → need /30 (2 hosts)
  6. WAN 2:    2 hosts → need /30 (2 hosts)

Allocation:
  Dept A: 192.168.1.0/25
    Network: 192.168.1.0
    Hosts: 192.168.1.1 — 192.168.1.126
    Broadcast: 192.168.1.127
    Used: 128 addresses, 126 hosts

  Dept B: 192.168.1.128/26
    Network: 192.168.1.128
    Hosts: 192.168.1.129 — 192.168.1.190
    Broadcast: 192.168.1.191
    Used: 64 addresses, 62 hosts

  Dept C: 192.168.1.192/27
    Network: 192.168.1.192
    Hosts: 192.168.1.193 — 192.168.1.222
    Broadcast: 192.168.1.223
    Used: 32 addresses, 30 hosts

  Dept D: 192.168.1.224/28
    Network: 192.168.1.224
    Hosts: 192.168.1.225 — 192.168.1.238
    Broadcast: 192.168.1.239
    Used: 16 addresses, 14 hosts

  WAN Link 1: 192.168.1.240/30
    Network: 192.168.1.240
    Hosts: 192.168.1.241 — 192.168.1.242
    Broadcast: 192.168.1.243
    Used: 4 addresses, 2 hosts

  WAN Link 2: 192.168.1.244/30
    Network: 192.168.1.244
    Hosts: 192.168.1.245 — 192.168.1.246
    Broadcast: 192.168.1.247
    Used: 4 addresses, 2 hosts

  Remaining: 192.168.1.248 — 192.168.1.255 (8 addresses free)

Total addresses used: 128 + 64 + 32 + 16 + 4 + 4 = 248
Total addresses free: 8
Efficiency: 248/256 = 96.9% vs fixed-size /25 = 50% efficiency
```

### 9.4 VLSM Tree Visualization

```
                    192.168.1.0/24
                    [256 addresses]
                          |
          ┌───────────────┴────────────────┐
          |                                |
    192.168.1.0/25                  192.168.1.128/25
    [128 addr]                      [128 addr]
    [Dept A]                              |
                              ┌───────────┴──────────┐
                              |                      |
                    192.168.1.128/26          192.168.1.192/26
                    [64 addr]                 [64 addr]
                    [Dept B]                       |
                                        ┌──────────┴──────────┐
                                        |                     |
                              192.168.1.192/27       192.168.1.224/27
                              [32 addr]              [32 addr]
                              [Dept C]                    |
                                                 ┌────────┴────────┐
                                                 |                 |
                                       192.168.1.224/28    192.168.1.240/28
                                       [16 addr]           [16 addr]
                                       [Dept D]                 |
                                                       ┌────────┴────────┐
                                                       |                 |
                                               .240/30 [WAN1]   .244/30 [WAN2]
                                               [4 addr]         [4 addr]
                                               .248-.255 FREE (8 addr)
```

### 9.5 VLSM Overlap Detection

Two subnets overlap if one is a subset of the other. Check:

```
Do 10.0.0.0/22 and 10.0.2.0/24 overlap?

  10.0.0.0/22:   10.0.0.0 — 10.0.3.255
  10.0.2.0/24:   10.0.2.0 — 10.0.2.255

  10.0.2.0 is within 10.0.0.0—10.0.3.255 → OVERLAP! Conflict!

Fix: Either use a subnet outside /22, or re-plan.

Linux check (ip route will refuse duplicate/overlapping routes):
  ip route add 10.0.0.0/22 dev eth0
  ip route add 10.0.2.0/24 dev eth1  # RTNETLINK: File exists
```

---

## 10. Supernetting / Route Aggregation / CIDR Summarization

### 10.1 What is Supernetting?

The **inverse** of subnetting — combining multiple smaller networks into one larger summary route. Used to reduce routing table size (route aggregation).

```
Subnetting:  one big network → many small subnets   (divide)
Supernetting: many small networks → one summary route (combine)
```

### 10.2 Rules for Valid Summarization

For a group of networks to be summarized into one prefix:

1. **They must be contiguous** (no gaps)
2. **Their count must be a power of 2** (1, 2, 4, 8, 16...)
3. **The first network address must be aligned** to the block size of the summary

### 10.3 Summarization Algorithm

**Problem:** Summarize these routes:
```
192.168.8.0/24
192.168.9.0/24
192.168.10.0/24
192.168.11.0/24
```

**Step 1: Write third octets in binary:**
```
  8  = 00001000
  9  = 00001001
  10 = 00001010
  11 = 00001011
       ^^^^^^
       000010  ← common prefix (6 bits of 3rd octet)
             ^^
             varying bits
```

**Step 2: Count common bits in the interesting area:**
```
192.168.  8.0 = 192.168. 00001000 .0
192.168.  9.0 = 192.168. 00001001 .0
192.168. 10.0 = 192.168. 00001010 .0
192.168. 11.0 = 192.168. 00001011 .0
                          ^^^^^^
                          6 bits common in 3rd octet
```

**Step 3: Total prefix = first two octets (16 bits) + 6 bits = /22**
```
Summary: 192.168.8.0/22
  Network: 192.168.8.0
  Range:   192.168.8.0 — 192.168.11.255
  Covers all 4 /24 networks ✓
```

### 10.4 Finding Summary Route Mathematically

```
Algorithm:
  1. Convert all network addresses to 32-bit integers
  2. XOR first and last → find differing bits
  3. Count leading common bits → that's the new prefix

Example:
  172.16.0.0   = 10101100.00010000.00000000.00000000
  172.16.3.255 = 10101100.00010000.00000011.11111111

  XOR result:   00000000.00000000.00000011.11111111
  Leading zeros in XOR: 22
  Summary prefix: /22

  Summary: 172.16.0.0/22 ✓
```

### 10.5 Hierarchy of Summarization

```
ISP Level:
  AS1 advertises: 10.0.0.0/8     (aggregates all internal)

Regional Level:
  Region A: 10.0.0.0/12
  Region B: 10.16.0.0/12

Site Level:
  Site 1: 10.0.0.0/16
  Site 2: 10.1.0.0/16
  ...

Building Level:
  Floor 1: 10.0.1.0/24
  Floor 2: 10.0.2.0/24
  ...

                BGP Table
                    |
           [10.0.0.0/8 summary]
                    |
           ┌────────┴────────┐
  [10.0.0.0/12]        [10.16.0.0/12]
       |                    |
  [10.0.0.0/16]        [10.16.0.0/16]
       |                    |
  [10.0.1.0/24 ...]    [10.16.1.0/24 ...]

Each level only sees one route for the level below it.
```

---

## 11. Special & Reserved IPv4 Addresses

### 11.1 IANA Special-Purpose Registry (RFC 5735, RFC 6890)

```
Address Block       Purpose                      Reference
------------------  ---------------------------  ---------
0.0.0.0/8           "This" network (source only) RFC 1122
10.0.0.0/8          Private use                  RFC 1918
100.64.0.0/10       Shared address (CGN)         RFC 6598
127.0.0.0/8         Loopback                     RFC 1122
169.254.0.0/16      Link-local (APIPA)           RFC 3927
172.16.0.0/12       Private use                  RFC 1918
192.0.0.0/24        IETF Protocol assignments    RFC 6890
192.0.2.0/24        TEST-NET-1 (documentation)   RFC 5737
192.88.99.0/24      6to4 relay (deprecated)      RFC 7526
192.168.0.0/16      Private use                  RFC 1918
198.18.0.0/15       Benchmarking                 RFC 2544
198.51.100.0/24     TEST-NET-2 (documentation)   RFC 5737
203.0.113.0/24      TEST-NET-3 (documentation)   RFC 5737
224.0.0.0/4         Multicast                    RFC 1112
240.0.0.0/4         Reserved (future)            RFC 1112
255.255.255.255/32  Limited broadcast            RFC 919
```

### 11.2 Loopback (127.0.0.0/8)

```
127.0.0.0/8 = 16,777,216 addresses
  Most commonly used: 127.0.0.1

In Linux kernel:
  - Handled by lo (loopback) interface
  - Never leaves the host — processed entirely in kernel
  - net/ipv4/ip_input.c: ip_rcv() → ip_local_deliver()
  - struct net_device *lo defined in drivers/net/loopback.c

  127.0.0.1 → loopback (lo)
  127.x.x.x → also loopback (entire /8)
```

### 11.3 Link-Local (169.254.0.0/16)

```
169.254.0.0/16 (APIPA — Automatic Private IP Addressing)

  Assigned automatically when DHCP fails
  NOT routable — only valid on local segment
  Used in:
    - Windows APIPA
    - AWS instance metadata: 169.254.169.254
    - Kubernetes pod networking internal
    - Link-local multicast: 224.0.0.0/4

Linux behavior:
  ip route show table local
  (link-local routes appear here)
```

### 11.4 Multicast (224.0.0.0/4)

```
224.0.0.0/4 = 224.0.0.0 — 239.255.255.255

Subranges:
  224.0.0.0/24    Local network control (TTL=1, never routed)
                    224.0.0.1  = All hosts on subnet
                    224.0.0.2  = All routers on subnet
                    224.0.0.5  = OSPF all routers
                    224.0.0.6  = OSPF DR/BDR
                    224.0.0.9  = RIPv2
                    224.0.0.10 = EIGRP
  224.0.1.0/24    Internetwork control
  232.0.0.0/8     Source-Specific Multicast (SSM)
  233.0.0.0/8     GLOP (AS-based multicast)
  239.0.0.0/8     Administratively scoped (private multicast)

Linux: ip maddr show
       ip mroute show  (multicast routing table)
```

### 11.5 Broadcast Types

```
Type                 Address               Scope
----                 -------               -----
Limited broadcast    255.255.255.255       Current network only
                                           Never forwarded by routers

Directed broadcast   Network_broadcast     Specific subnet
                     e.g., 192.168.1.255   Routers may forward
                                           Linux drops by default

Subnet broadcast     Same as directed      
(RFC 919)

All-subnets         Network_broadcast     Deprecated
broadcast           (old classful)        (RFC 1812)
```

---

## 12. Private Address Ranges & NAT Context

### 12.1 RFC 1918 Private Ranges

```
Class  Range                    CIDR          Total Addresses
-----  ----------------------   -----------   ---------------
  A    10.0.0.0 — 10.255.255.255  10.0.0.0/8    16,777,216
  B    172.16.0.0 — 172.31.255.255 172.16.0.0/12  1,048,576
  C    192.168.0.0 — 192.168.255.255 192.168.0.0/16  65,536

These are:
  - NOT globally routable
  - Reusable across organizations
  - Require NAT to reach internet
  - Cannot be source-routed across the public internet

172.16.0.0/12 decoded:
  172.16.0.0  = 10101100.00010000.00000000.00000000
  /12 means:    11111111.11110000.00000000.00000000
  Range start:  172.16.0.0
  Range end:    172.31.255.255
  (4th bit of 2nd octet through end varies)
```

### 12.2 NAT and Subnetting Interaction

```
                       [Internet]
                           |
                    [Public IP: 203.0.113.1]
                           |
                       [Router/NAT]
                           |
              ┌────────────┴───────────────┐
              |                            |
       10.0.1.0/24                  10.0.2.0/24
       [LAN 1: 254 hosts]           [LAN 2: 254 hosts]

NAT Translation Table (in Linux: nf_conntrack):
  Internal IP:Port      External IP:Port
  10.0.1.100:34521  →   203.0.113.1:40001
  10.0.1.101:55231  →   203.0.113.1:40002
  10.0.2.50:12345   →   203.0.113.1:40003

Linux NAT kernel path:
  net/netfilter/nf_nat_core.c
  include/net/netfilter/nf_nat.h
  nf_nat_packet() → nf_nat_manip_pkt()

iptables MASQUERADE (dynamic SNAT):
  iptables -t nat -A POSTROUTING -s 10.0.0.0/8 -o eth0 -j MASQUERADE
```

### 12.3 Carrier-Grade NAT (CGN) — RFC 6598

```
100.64.0.0/10 = Shared Address Space
  Range: 100.64.0.0 — 100.127.255.255
  4,194,304 addresses

Used by ISPs for CGN (also called LSN — Large-Scale NAT):
  Customer ← 100.64.x.x → ISP CGN device ← Public IP → Internet

  This is a second layer of NAT for ISPs exhausted of public IPs.
  NOT RFC 1918, but similarly not globally routed.
```

---

## 13. Subnet Design Methodology

### 13.1 Top-Down Design Process

```
Step 1: Requirements Gathering
  - How many segments/VLANs are needed?
  - How many hosts per segment?
  - What is the growth factor? (multiply by 1.5x-2x)
  - Point-to-point links? (use /30 or /31)
  - Loopback interfaces? (use /32)
  - Which address range is available?

Step 2: Choose Address Space
  - Small org: 192.168.0.0/16 or subset
  - Medium org: 172.16.0.0/12 or subset
  - Large org: 10.0.0.0/8

Step 3: Choose Hierarchy Level
  - Site/Region allocation: /16 per site
  - Building/zone: /20 or /22 per zone
  - Department/VLAN: /24 or /25 per dept
  - Point-to-point: /30 or /31

Step 4: Apply VLSM Bottom-Up
  - Plan smallest components first (count and size)
  - Allocate from the address space using VLSM

Step 5: Document and Verify
  - No overlapping ranges
  - All summary routes valid
  - Growth space reserved
```

### 13.2 Enterprise Hierarchical Design Example

```
Enterprise: 10.0.0.0/8

Level 1 — Region allocation:
  Americas:    10.0.0.0/10   (10.0.0.0  — 10.63.255.255)
  EMEA:        10.64.0.0/10  (10.64.0.0 — 10.127.255.255)
  APAC:        10.128.0.0/10 (10.128.0.0 — 10.191.255.255)
  Reserved:    10.192.0.0/10 (future growth)

Level 2 — Site allocation (within Americas /10):
  NYC HQ:      10.0.0.0/16   (65,536 addr)
  LA Office:   10.1.0.0/16
  Chicago:     10.2.0.0/16
  ...

Level 3 — VLAN/Segment (within NYC /16):
  Server VLAN: 10.0.1.0/24   (254 hosts)
  HR dept:     10.0.2.0/24
  Engineering: 10.0.3.0/24
  Management:  10.0.4.0/27   (30 hosts — small team)
  Printers:    10.0.4.32/27
  WAN links:   10.0.255.0/24  (64 × /30 links)

Route Summary advertised by NYC router:
  10.0.0.0/16  (one route covers all NYC subnets)
```

### 13.3 Alignment and "Block Boundary" Rule

Subnet addresses MUST be aligned to their block size. A /26 (block=64) must start at a multiple of 64: 0, 64, 128, 192 only.

```
Valid /26 addresses:
  10.0.0.0/26    ✓ (0 mod 64 = 0)
  10.0.0.64/26   ✓ (64 mod 64 = 0)
  10.0.0.128/26  ✓ (128 mod 64 = 0)
  10.0.0.192/26  ✓ (192 mod 64 = 0)

Invalid:
  10.0.0.50/26   ✗ (50 mod 64 ≠ 0)
  10.0.0.100/26  ✗ (100 mod 64 ≠ 0)

Why? The AND operation with the mask must yield the network address:
  10.0.0.50 AND 255.255.255.192:
    00110010 AND 11000000 = 00000000 = 0
    → Network = 10.0.0.0, not 10.0.0.50
  So 10.0.0.50/26 is actually in the 10.0.0.0/26 subnet.
```

---

## 14. Subnetting Shortcuts & Mental Math Tricks

### 14.1 The Magic Number Method

```
Magic Number = 256 - (subnet mask interesting octet)

Steps:
  1. Find mask value in the "interesting" octet
  2. Magic = 256 - mask_value
  3. List multiples of Magic in that octet → subnet starts
  4. Broadcast = next subnet start - 1

Example: What subnet is 172.16.45.200/22 in?

  /22 mask = 255.255.252.0
  Interesting octet = 3rd (252)
  Magic = 256 - 252 = 4

  Multiples of 4 in 3rd octet: 0,4,8,12,...,44,48,...
    44 × 4 = 44? No, think: 44 / 4 = 11, so 44 is a multiple (11×4=44)
    Next: 48

  172.16.44.0/22  ← 200 is not involved, it's the 3rd octet (45) we check:
    45 ÷ 4 = 11.25 → floor = 11 → 11 × 4 = 44
    Subnet: 172.16.44.0/22
    Broadcast: 172.16.47.255
    Host range: 172.16.44.1 — 172.16.47.254
    ✓ 172.16.45.200 is within this range.
```

### 14.2 Powers of 2 — Must Memorize

```
2^1  = 2        2^9  = 512
2^2  = 4        2^10 = 1,024
2^3  = 8        2^11 = 2,048
2^4  = 16       2^12 = 4,096
2^5  = 32       2^13 = 8,192
2^6  = 64       2^14 = 16,384
2^7  = 128      2^15 = 32,768
2^8  = 256      2^16 = 65,536
```

### 14.3 Prefix-to-Mask Quick Lookup

```
Last octet of mask (for /24 to /32):
  /24 = .0    /28 = .240
  /25 = .128  /29 = .248
  /26 = .192  /30 = .252
  /27 = .224  /31 = .254
               /32 = .255

Third octet of mask (for /16 to /23):
  /16 = 255.255.0.0    /20 = 255.255.240.0
  /17 = 255.255.128.0  /21 = 255.255.248.0
  /18 = 255.255.192.0  /22 = 255.255.252.0
  /19 = 255.255.224.0  /23 = 255.255.254.0
```

### 14.4 Converting Between CIDR and Mask (Fast Method)

```
To get mask from /n:
  1. Fill n bits from left with 1s
  2. Fill remaining (32-n) bits with 0s
  3. Convert each 8-bit group to decimal

Example: /21
  11111111.11111111.11111000.00000000
  255      .255     .248     .0
  → 255.255.248.0 ✓

To get /n from mask:
  Count the 1-bits.
  Or: for each octet, use: 255→8, 254→7, 252→6, 248→5,
                           240→4, 224→3, 192→2, 128→1, 0→0
  Sum them.

Example: 255.255.240.0
  255→8, 255→8, 240→4, 0→0
  8+8+4+0 = 20 → /20 ✓
```

### 14.5 Determining if Two IPs are in the Same Subnet

```
Method: Apply the mask to both IPs. If results are equal → same subnet.

Quick mental check:
  IPs: 10.1.2.100 and 10.1.2.200, mask /25

  /25 block = 128
  100 < 128 → first block (10.1.2.0/25)
  200 ≥ 128 → second block (10.1.2.128/25)
  
  Different subnets! ✗

  IPs: 10.1.2.100 and 10.1.2.120, mask /25
  Both < 128 → both in 10.1.2.0/25 ✓
```

---

## 15. IP Routing & Subnet Interaction

### 15.1 How Routers Use Subnets

```
                       [Router]
                      Routing Table:
                    +------------------+------------------+
                    | Destination      | Next Hop / If    |
                    +------------------+------------------+
                    | 192.168.1.0/24   | eth0 (directly)  |
                    | 192.168.2.0/24   | eth1 (directly)  |
                    | 10.0.0.0/8       | 192.168.2.1      |
                    | 0.0.0.0/0        | 203.0.113.1      |
                    +------------------+------------------+
                           |               |
                  [192.168.1.0/24]  [192.168.2.0/24]
                   eth0 network      eth1 network

Packet routing algorithm:
  For each packet, find the LONGEST PREFIX MATCH in routing table:
    - More specific route (longer prefix) wins
    - 192.168.1.50 → matches 192.168.1.0/24 (length 24) 
                     AND 0.0.0.0/0 (length 0)
                   → /24 wins (longer match)
    - 8.8.8.8     → matches only 0.0.0.0/0 → default gateway
```

### 15.2 Longest Prefix Match (LPM)

```
This is THE fundamental routing operation.

Routing table:
  10.0.0.0/8      → via gw1
  10.1.0.0/16     → via gw2
  10.1.1.0/24     → via gw3
  10.1.1.128/25   → via gw4
  0.0.0.0/0       → via gw5 (default)

Destination: 10.1.1.200

Matches:
  10.0.0.0/8      ✓ (prefix len 8)
  10.1.0.0/16     ✓ (prefix len 16)
  10.1.1.0/24     ✓ (prefix len 24)
  10.1.1.128/25   ✓ (prefix len 25) ← WINNER (longest)
  0.0.0.0/0       ✓ (prefix len 0)

→ Packet forwarded via gw4

Linux kernel implementation:
  net/ipv4/fib_trie.c  (LC-trie / FIB trie)
  fib_lookup() → fib_table_lookup() → trie_lookup_key()
  struct fib_table (include/net/ip_fib.h)
```

### 15.3 Linux Routing Table

```
Commands:
  ip route show                    # main table
  ip route show table all          # all tables (local, main, default)
  ip route show table local        # interface-attached routes, broadcast, loopback
  ip route get 8.8.8.8             # which route would be used?

Example output:
  default via 192.168.1.1 dev eth0
  192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
  10.0.0.0/8 via 192.168.1.254 dev eth0

Tables:
  local (255): managed by kernel, not user-editable
  main (254):  default routing table
  default (253): fallback

Policy Routing: ip rule show
  Rules evaluated in priority order:
  0:    lookup local
  32766: lookup main
  32767: lookup default
```

### 15.4 Connected vs. Static vs. Dynamic Routes

```
Connected route:
  Automatically added when IP assigned to interface:
    ip addr add 192.168.1.100/24 dev eth0
    → kernel adds: 192.168.1.0/24 dev eth0 scope link
  Source: net/ipv4/fib_frontend.c: fib_add_ifaddr()

Static route:
  Manually added by admin:
    ip route add 10.0.0.0/8 via 192.168.1.1
  Source: iproute2 → rtnetlink → fib_nl_newroute()

Dynamic route:
  Added by routing daemon (OSPF, BGP, RIP):
    - OSPF: ospfd (FRRouting) → netlink → kernel RIB
    - BGP: bgpd (FRRouting) → best-path selection → kernel
```

### 15.5 ARP and Subnetting

```
ARP (Address Resolution Protocol) operates WITHIN a subnet:

  Host A (192.168.1.10) wants to reach 192.168.1.50:
    1. Is 192.168.1.50 in my subnet?
       192.168.1.50 AND 255.255.255.0 = 192.168.1.0 ← my network ✓
    2. Send ARP request: "Who has 192.168.1.50?"
    3. 192.168.1.50 replies with MAC address
    4. Direct frame delivery

  Host A wants to reach 8.8.8.8:
    1. Is 8.8.8.8 in my subnet?
       8.8.8.8 AND 255.255.255.0 = 8.8.8.0 ≠ 192.168.1.0 ✗
    2. Send ARP for DEFAULT GATEWAY (192.168.1.1)
    3. Router forwards packet

Linux ARP:
  net/ipv4/arp.c
  arp_rcv() → arp_process()
  arp cache: ip neigh show
  struct neighbour (include/net/neighbour.h)
```

---

## 16. Practical Examples & Worked Problems

### 16.1 Problem Set 1: Basic Subnetting

**Problem 1:** For `172.20.100.68/27`, find all subnet parameters.

```
Step 1: Mask
  /27 → 255.255.255.224
  Binary: 11111111.11111111.11111111.11100000

Step 2: Binary representation
  IP:   172.20.100.68
      = 10101100.00010100.01100100.01000100
  Mask= 11111111.11111111.11111111.11100000

Step 3: Network (AND)
  10101100.00010100.01100100.01000000
= 172.20.100.64

Step 4: Broadcast (all host bits = 1)
  10101100.00010100.01100100.01011111
= 172.20.100.95

Step 5: Hosts
  First: 172.20.100.65
  Last:  172.20.100.94
  Count: 2^5 - 2 = 30

Step 6: Next subnet
  172.20.100.96/27

Answer:
  Network:    172.20.100.64/27
  Mask:       255.255.255.224
  Broadcast:  172.20.100.95
  Host range: 172.20.100.65 — 172.20.100.94
  Hosts:      30
  Next subnet: 172.20.100.96/27
```

**Problem 2:** How many /28 subnets can you get from 10.10.0.0/20?

```
/20 has (32-20) = 12 host bits → 2^12 = 4096 addresses
/28 has (32-28) = 4 host bits  → 2^4  = 16 addresses each

Subnets = 4096 / 16 = 256 subnets
        = 2^(28-20) = 2^8 = 256 ✓
```

**Problem 3:** Is 10.10.5.200 in the subnet 10.10.4.0/22?

```
10.10.4.0/22:
  Block size: 2^(32-22) = 2^10 = 1024 addresses
  Range: 10.10.4.0 — 10.10.7.255

Check: Is 10.10.5.200 within 10.10.4.0 to 10.10.7.255?

Convert to comparable form:
  10.10.4.0   = ...00000100.00000000 (last two octets)
  10.10.7.255 = ...00000111.11111111
  10.10.5.200 = ...00000101.11001000

  5 is between 4 and 7 ✓
  → YES, 10.10.5.200 is in 10.10.4.0/22

Formal AND verification:
  10.10.5.200 AND 255.255.252.0:
    5 AND 252: 00000101 AND 11111100 = 00000100 = 4
  → Network = 10.10.4.0 ✓
```

### 16.2 Problem Set 2: VLSM Design

**Problem:** Given 192.168.0.0/24, design for:
- Network A: 100 hosts
- Network B: 60 hosts
- Network C: 30 hosts
- Network D: 2 hosts (WAN link)

```
Sort by size:
  A: 100 → /25 (126 hosts, block=128)
  B:  60 → /26 (62 hosts, block=64)
  C:  30 → /27 (30 hosts, block=32)
  D:   2 → /30 (2 hosts, block=4)

Address Map:
  ┌────────────────────────────────────────────────────┐
  │ 192.168.0.0    Network A /25                       │
  │ .0 — .127      (128 addresses, 126 usable)         │
  ├────────────────────────────────────────────────────┤
  │ 192.168.0.128  Network B /26                       │
  │ .128 — .191    (64 addresses, 62 usable)           │
  ├────────────────────────────────────────────────────┤
  │ 192.168.0.192  Network C /27                       │
  │ .192 — .223    (32 addresses, 30 usable)           │
  ├────────────────────────────────────────────────────┤
  │ 192.168.0.224  Network D /30                       │
  │ .224 — .227    (4 addresses, 2 usable)             │
  ├────────────────────────────────────────────────────┤
  │ 192.168.0.228 — .255  FREE (28 addresses)          │
  └────────────────────────────────────────────────────┘

Total used:  128 + 64 + 32 + 4 = 228 addresses
Total free:  28 addresses
Efficiency:  228/256 = 89%
```

### 16.3 Problem Set 3: Summarization

**Problem:** Summarize 10.4.0.0/24 through 10.7.255.0/24.

```
Actually let's summarize these four:
  10.4.0.0/16
  10.5.0.0/16
  10.6.0.0/16
  10.7.0.0/16

Binary second octets:
  4 = 00000100
  5 = 00000101
  6 = 00000110
  7 = 00000111
      000001    ← 6 common bits

Fixed: first 8 bits (10.) + 6 common bits in 2nd octet = 14 bits
Summary: 10.4.0.0/14

Verify:
  10.4.0.0/14: Range = 10.4.0.0 — 10.7.255.255
  Covers all four /16 networks ✓

  Mask: /14 = 11111111.11111100.00000000.00000000
            = 255.252.0.0
```

### 16.4 Problem Set 4: Linux Shell — Subnet Calculator

```bash
#!/bin/bash
# subnet_calc.sh — IPv4 subnet calculator
# Usage: ./subnet_calc.sh 192.168.1.100 24

ip_to_int() {
    local ip=$1
    local a b c d
    IFS='.' read -r a b c d <<< "$ip"
    echo $(( (a << 24) | (b << 16) | (c << 8) | d ))
}

int_to_ip() {
    local n=$1
    echo "$(( (n >> 24) & 255 )).$(( (n >> 16) & 255 )).$(( (n >> 8) & 255 )).$(( n & 255 ))"
}

IP=$1
PREFIX=$2

IP_INT=$(ip_to_int "$IP")
MASK_INT=$(( 0xFFFFFFFF << (32 - PREFIX) & 0xFFFFFFFF ))
NETWORK_INT=$(( IP_INT & MASK_INT ))
BROADCAST_INT=$(( NETWORK_INT | (~MASK_INT & 0xFFFFFFFF) ))
FIRST_HOST=$(( NETWORK_INT + 1 ))
LAST_HOST=$(( BROADCAST_INT - 1 ))
HOST_BITS=$(( 32 - PREFIX ))
TOTAL=$(( 1 << HOST_BITS ))
USABLE=$(( TOTAL - 2 ))

echo "==================================="
echo "  IPv4 Subnet Calculator"
echo "==================================="
echo "  IP Address:    $IP/$PREFIX"
echo "  Subnet Mask:   $(int_to_ip $MASK_INT)"
echo "  Network:       $(int_to_ip $NETWORK_INT)/$PREFIX"
echo "  Broadcast:     $(int_to_ip $BROADCAST_INT)"
echo "  First Host:    $(int_to_ip $FIRST_HOST)"
echo "  Last Host:     $(int_to_ip $LAST_HOST)"
echo "  Total Hosts:   $TOTAL"
echo "  Usable Hosts:  $USABLE"
echo "  Block Size:    $TOTAL"
echo "==================================="
```

### 16.5 Python Subnet Calculator

```python
#!/usr/bin/env python3
"""IPv4 Subnet Calculator — no stdlib ipaddress module, pure math"""

def ip_to_int(ip: str) -> int:
    octets = list(map(int, ip.split('.')))
    return (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]

def int_to_ip(n: int) -> str:
    return '.'.join([str((n >> s) & 0xFF) for s in (24, 16, 8, 0)])

def subnet_info(ip: str, prefix: int) -> dict:
    ip_int     = ip_to_int(ip)
    mask_int   = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    net_int    = ip_int & mask_int
    bcast_int  = net_int | (~mask_int & 0xFFFFFFFF)
    host_bits  = 32 - prefix
    total      = 1 << host_bits
    usable     = max(0, total - 2)

    return {
        'ip':           ip,
        'prefix':       prefix,
        'mask':         int_to_ip(mask_int),
        'wildcard':     int_to_ip(~mask_int & 0xFFFFFFFF),
        'network':      int_to_ip(net_int),
        'broadcast':    int_to_ip(bcast_int),
        'first_host':   int_to_ip(net_int + 1) if usable > 0 else 'N/A',
        'last_host':    int_to_ip(bcast_int - 1) if usable > 0 else 'N/A',
        'total_addrs':  total,
        'usable_hosts': usable,
        'host_bits':    host_bits,
        'net_bits':     prefix,
    }

def is_same_subnet(ip1: str, ip2: str, prefix: int) -> bool:
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return (ip_to_int(ip1) & mask) == (ip_to_int(ip2) & mask)

def summarize(networks: list) -> tuple:
    """Find summary route for a list of (ip, prefix) tuples"""
    ints = [ip_to_int(ip) for ip, _ in networks]
    xor_result = ints[0]
    for i in ints[1:]:
        xor_result |= (ints[0] ^ i)
    # Count leading zeros of xor_result
    prefix = 0
    for bit in range(31, -1, -1):
        if xor_result & (1 << bit):
            break
        prefix += 1
    # Align network address
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    net = ints[0] & mask
    return int_to_ip(net), prefix

# Example usage
if __name__ == '__main__':
    info = subnet_info('192.168.1.100', 26)
    for k, v in info.items():
        print(f"  {k:<15}: {v}")

    print()
    print(f"Same subnet? 10.0.0.1 and 10.0.0.200 /25: "
          f"{is_same_subnet('10.0.0.1','10.0.0.200',25)}")

    nets = [('192.168.8.0', 24), ('192.168.9.0', 24),
            ('192.168.10.0', 24), ('192.168.11.0', 24)]
    net, prefix = summarize(nets)
    print(f"\nSummary of 4 /24s: {net}/{prefix}")
```

---

## 17. Linux Kernel & Networking Stack Context

### 17.1 How the Kernel Stores and Processes Subnets

```
Key data structures (include/linux/inetdevice.h, include/net/ip_fib.h):

struct in_ifaddr {              /* per-interface IPv4 address */
    struct in_ifaddr  *ifa_next;
    struct in_device  *ifa_dev;
    __be32             ifa_local;     /* local IP address */
    __be32             ifa_address;   /* peer address (P2P) or local */
    __be32             ifa_mask;      /* subnet mask */
    __be32             ifa_broadcast; /* broadcast address */
    unsigned char      ifa_prefixlen; /* prefix length / CIDR */
    char               ifa_label[IFNAMSIZ];
    ...
};

struct fib_info {               /* route attributes (net/ipv4/fib_semantics.c) */
    struct net        *fib_net;
    int                fib_treeref;
    unsigned int       fib_flags;
    unsigned char      fib_protocol;  /* routing protocol */
    unsigned char      fib_scope;
    unsigned char      fib_type;
    ...
};

Routing table lookup:
  net/ipv4/fib_trie.c  — LC-trie (Level Compressed trie)
    fib_table_lookup()
      → tnode_get_child_rcu()
      → check_leaf()
      → fib_semantic_match()

The trie is keyed on the destination address, and provides O(W)
lookup where W is the address width (32 bits).
```

### 17.2 Packet Reception and Subnet Decisions

```
NIC receives packet
  │
  ▼
net/core/dev.c: netif_receive_skb()
  │
  ▼
net/ipv4/ip_input.c: ip_rcv()
  │ Verifies IP header checksum, length
  ▼
ip_rcv_finish() → ip_route_input_noref()
  │
  ▼
net/ipv4/route.c: ip_route_input_slow()
  │ Calls fib_lookup() — uses subnet routing table
  │ Determines: LOCAL, BROADCAST, UNICAST, MULTICAST
  ▼
  ├─ RTN_LOCAL      → ip_local_deliver()    (for this host)
  ├─ RTN_BROADCAST  → ip_local_deliver()    (broadcast, handled locally)
  ├─ RTN_MULTICAST  → ip_mr_input()         (multicast routing)
  └─ RTN_UNICAST    → ip_forward()          (forward to next hop)
```

### 17.3 Key Files for Subnet/Routing in Kernel Source

```
File                               Purpose
---------------------------------  -------------------------------------------
net/ipv4/ip_input.c                IP packet reception, subnet decision
net/ipv4/ip_output.c               IP packet transmission, source routing
net/ipv4/route.c                   Route cache, route lookup, PMTU
net/ipv4/fib_trie.c                FIB trie (routing table data structure)
net/ipv4/fib_semantics.c           Route attributes and policy
net/ipv4/fib_frontend.c            Netlink interface for route management
net/ipv4/devinet.c                 Per-interface address management
include/linux/inetdevice.h         struct in_ifaddr, in_device
include/net/ip_fib.h               struct fib_table, fib_result
include/uapi/linux/rtnetlink.h     Netlink route types (userspace interface)
net/ipv4/arp.c                     ARP (address resolution within subnet)
net/netfilter/nf_nat_core.c        NAT (masquerades private subnets)
```

### 17.4 Kernel Subnet-Related sysctl Parameters

```bash
# View all IPv4 routing/forwarding sysctls
sysctl -a | grep net.ipv4

# IP forwarding (router function — routes between subnets)
sysctl net.ipv4.ip_forward              # 0=host, 1=router

# Accept/send redirects (ICMP redirect for better routes)
sysctl net.ipv4.conf.all.accept_redirects
sysctl net.ipv4.conf.all.send_redirects

# Reverse path filtering (anti-spoofing, checks if source subnet is reachable)
sysctl net.ipv4.conf.all.rp_filter     # 0=off, 1=strict, 2=loose

# ARP behavior
sysctl net.ipv4.conf.all.arp_announce  # How to choose src IP for ARP
sysctl net.ipv4.conf.all.arp_ignore    # How to respond to ARP requests

# Route cache (removed in 3.6+, now uses nexthop cache)
# /proc/net/rt_cache  — route cache (older kernels)
# /proc/net/fib_trie  — current FIB trie contents
# /proc/net/fib_triestat — trie statistics
```

### 17.5 eBPF and XDP Subnet Operations

```c
/* BPF program: drop packets not in allowed subnet */
/* Subnet: 10.0.0.0/8 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <arpa/inet.h>

#define ALLOWED_NET   0x0A000000   /* 10.0.0.0 in host byte order */
#define ALLOWED_MASK  0xFF000000   /* /8 mask */

SEC("xdp")
int subnet_filter(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_DROP;

    /* Bitwise AND for subnet check — same as subnetting math */
    __u32 src = ntohl(iph->saddr);
    if ((src & ALLOWED_MASK) != ALLOWED_NET)
        return XDP_DROP;   /* not in 10.0.0.0/8 — drop */

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

/* Load with:
   ip link set dev eth0 xdp obj subnet_filter.o sec xdp
   bpftool prog load subnet_filter.o /sys/fs/bpf/subnet_filter
*/
```

---

## 18. Quick Reference Tables

### 18.1 Complete /1 to /32 Reference

```
CIDR  Mask              Hosts    Block   Subnets   Addresses
      (last 2 octets)   Usable   Size    from /24  Total
----  ----------------  -------  ------  --------  ----------
/1    128.0.0.0              —      —        —      2147483648
/2    192.0.0.0              —      —        —      1073741824
/3    224.0.0.0              —      —        —       536870912
/4    240.0.0.0              —      —        —       268435456
/5    248.0.0.0              —      —        —       134217728
/6    252.0.0.0              —      —        —        67108864
/7    254.0.0.0              —      —        —        33554432
/8    255.0.0.0        16777214   16M       —        16777216
/9    255.128.0.0       8388606    8M       —         8388608
/10   255.192.0.0       4194302    4M       —         4194304
/11   255.224.0.0       2097150    2M       —         2097152
/12   255.240.0.0       1048574    1M       —         1048576
/13   255.248.0.0        524286  512K       —          524288
/14   255.252.0.0        262142  256K       —          262144
/15   255.254.0.0        131070  128K       —          131072
/16   255.255.0.0         65534   64K       —           65536
/17   255.255.128.0       32766   32K       —           32768
/18   255.255.192.0       16382   16K       —           16384
/19   255.255.224.0        8190    8K       —            8192
/20   255.255.240.0        4094    4K       —            4096
/21   255.255.248.0        2046    2K       —            2048
/22   255.255.252.0        1022    1K       —            1024
/23   255.255.254.0         510  512        —             512
/24   255.255.255.0         254  256         1            256
/25   255.255.255.128       126  128         2            128
/26   255.255.255.192        62   64         4             64
/27   255.255.255.224        30   32         8             32
/28   255.255.255.240        14   16        16             16
/29   255.255.255.248         6    8        32              8
/30   255.255.255.252         2    4        64              4
/31   255.255.255.254         2*   2       128              2
/32   255.255.255.255         1**  1       256              1
```

### 18.2 Common Subnet Boundaries

```
/25 boundaries (block=128):  0, 128
/26 boundaries (block=64):   0, 64, 128, 192
/27 boundaries (block=32):   0, 32, 64, 96, 128, 160, 192, 224
/28 boundaries (block=16):   0, 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240
/29 boundaries (block=8):    0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, ...
/30 boundaries (block=4):    0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, ...
```

### 18.3 Private Address Summary

```
Range               CIDR            Addresses   Typical Use
------------------  --------------  ----------  -------------------------
10.0.0.0–10.x.x.x  10.0.0.0/8      16,777,216  Large enterprise
172.16–31.x.x       172.16.0.0/12   1,048,576   Medium enterprise
192.168.x.x         192.168.0.0/16  65,536      SOHO, home, small office
100.64–127.x.x.x    100.64.0.0/10   4,194,304   ISP CGN (RFC 6598)
169.254.x.x         169.254.0.0/16  65,536      APIPA/link-local
127.x.x.x           127.0.0.0/8     16,777,216  Loopback
```

### 18.4 Subnet Math Cheat Sheet

```
Given IP/prefix:

  Network address  =  IP  AND  Mask
  Broadcast        =  IP  OR   (~Mask)
                   = Network  OR  (~Mask & 0xFFFFFFFF)
  Wildcard mask    = ~Mask & 0xFFFFFFFF
                   = 255.255.255.255 - Mask
  Block size       = 2^(32 - prefix) = Total addresses per subnet
  Usable hosts     = Block size - 2  (subtract net + broadcast)
  Num subnets      = 2^(new_prefix - original_prefix)
  First host       = Network + 1
  Last host        = Broadcast - 1
  Next subnet      = Network + Block_size
  Interesting octet= the octet in mask that is not 0 or 255
  Magic number     = 256 - interesting_octet_value

  Is X in subnet?  → (X AND Mask) == Network_address
```

---

## Appendix A: RFC References

```
RFC 791  — Internet Protocol (IPv4 specification, 1981)
RFC 919  — Broadcasting Internet Datagrams (1984)
RFC 922  — Broadcasting Internet Datagrams in the Presence of Subnets (1984)
RFC 950  — Internet Standard Subnetting Procedure (1985)
RFC 1112 — Host Extensions for IP Multicasting (Class D)
RFC 1122 — Requirements for Internet Hosts (0.0.0.0/8, 127/8)
RFC 1518 — CIDR Architecture for IP Address Allocation (1993)
RFC 1519 — CIDR: an Address Assignment and Aggregation Strategy (1993)
RFC 1812 — Requirements for IP Version 4 Routers (1995)
RFC 1918 — Address Allocation for Private Internets (10/8, 172.16/12, 192.168/16)
RFC 2544 — Benchmarking Methodology (198.18.0.0/15)
RFC 3021 — Using 31-Bit Prefixes on IPv4 Point-to-Point Links (/31)
RFC 3927 — Dynamic Configuration of IPv4 Link-Local Addresses (169.254/16)
RFC 4632 — Classless Inter-domain Routing (CIDR): The Internet Address Assignment and Aggregation Plan
RFC 5735 — Special Use IPv4 Addresses (superseded by RFC 6890)
RFC 5737 — IPv4 Address Blocks Reserved for Documentation (192.0.2/24, 198.51.100/24, 203.0.113/24)
RFC 6598 — IANA-Reserved IPv4 Prefix for Shared Address Space (100.64/10)
RFC 6890 — Special-Purpose IP Address Registries (current reference)
```

## Appendix B: Linux Commands for Subnetting & Routing

```bash
# Add IP with subnet
ip addr add 192.168.1.10/24 dev eth0

# Show all interfaces with subnets
ip addr show
ip -4 addr show

# Show routing table
ip route show
ip route show table all

# Find which route handles a destination
ip route get 8.8.8.8
ip route get 192.168.1.50 from 192.168.1.10

# Add/delete static routes
ip route add 10.0.0.0/8 via 192.168.1.1
ip route del 10.0.0.0/8

# Add default gateway
ip route add default via 192.168.1.1

# Add blackhole (null route)
ip route add blackhole 192.0.2.0/24

# Show ARP cache (MAC resolution within subnet)
ip neigh show
ip neigh flush dev eth0

# Policy routing
ip rule show
ip rule add from 10.0.0.0/8 table 100

# Network namespace (isolated subnet testing)
ip netns add test_ns
ip netns exec test_ns ip addr show

# Subnet-level firewall with iptables
iptables -A FORWARD -s 192.168.1.0/24 -d 192.168.2.0/24 -j ACCEPT
iptables -t nat -A POSTROUTING -s 10.0.0.0/8 -o eth0 -j MASQUERADE

# nftables equivalent
nft add rule ip filter forward ip saddr 192.168.1.0/24 ip daddr 192.168.2.0/24 accept

# Probe subnet connectivity
ping -I eth0 192.168.1.255   # ping broadcast
arping -I eth0 192.168.1.1   # ARP ping (layer 2)
nmap -sn 192.168.1.0/24      # subnet host discovery

# View kernel FIB trie (routing data structure)
cat /proc/net/fib_trie
cat /proc/net/fib_triestat

# View interface-specific addresses (kernel internal table)
cat /proc/net/if_inet6         # IPv6 (for reference)
cat /proc/net/arp              # ARP cache
cat /proc/net/rt_cache         # route cache (older kernels)
```

---

*Guide version: April 2026 | Kernel reference: v6.x mainline | RFC references current as of 2024*

Here's everything packed into the guide. Here's a summary of what's covered and why each section matters:

**Foundations (§1–2)** — The entire guide is grounded in binary/bitwise math because that's what the kernel actually does. Every subnet operation — `fib_lookup()`, XDP filtering, NAT — is ultimately an AND/OR on a 32-bit integer.

**Classful → CIDR progression (§3–5)** — Classful is legacy but you'll hit it in RFCs, kernel history, and private range explanations. CIDR is what everything runs on now.

**Core math engine (§7)** — The block size / magic number method is the fastest mental shortcut. `Block = 256 - mask_octet`. Every subnet boundary is a multiple of the block size. That's it.

**VLSM (§9)** — The real-world design tool. Always allocate largest first. The tree diagram shows how the address space gets carved hierarchically.

**Supernetting (§10)** — The inverse operation: XOR the network addresses, count leading common bits. Critical for understanding BGP route aggregation and ISP prefix announcements.

**Linux kernel context (§17)** — Ties everything back to actual kernel code paths: `fib_trie.c` for LPM lookups, `ip_input.c` for subnet classification decisions, `devinet.c` for `struct in_ifaddr` (which holds `ifa_mask`/`ifa_prefixlen`), and an XDP program showing how subnet checks are literally just `src & mask == net` in BPF.

**Appendix B** — Every `ip`/`iptables`/`nft`/`proc` command you'll need for subnet work on your Kali dev machine and KVM VMs.