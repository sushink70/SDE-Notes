# Classful vs Classless IP Routing — A Complete In-Depth Guide

> *"To master routing, you must first master the language of addresses — every bit tells a story."*

---

## Table of Contents

1. [Prerequisites — Binary Fundamentals for Networking](#1-prerequisites--binary-fundamentals-for-networking)
2. [What is an IP Address?](#2-what-is-an-ip-address)
3. [The Network/Host Divide — The Core Mental Model](#3-the-networkhost-divide--the-core-mental-model)
4. [Classful IP Addressing (1981–1993)](#4-classful-ip-addressing-19811993)
5. [Problems with Classful Addressing](#5-problems-with-classful-addressing)
6. [Subnet Mask — The Boundary Marker](#6-subnet-mask--the-boundary-marker)
7. [Classless IP Routing — CIDR (1993–Present)](#7-classless-ip-routing--cidr-1993present)
8. [Variable Length Subnet Masking (VLSM)](#8-variable-length-subnet-masking-vlsm)
9. [Subnetting — Dividing Networks](#9-subnetting--dividing-networks)
10. [Supernetting — Route Aggregation](#10-supernetting--route-aggregation)
11. [Longest Prefix Match — How Routers Decide](#11-longest-prefix-match--how-routers-decide)
12. [The Routing Table — Anatomy and Lookup](#12-the-routing-table--anatomy-and-lookup)
13. [Real Routing Protocols — Classful Era](#13-real-routing-protocols--classful-era)
14. [Real Routing Protocols — Classless Era](#14-real-routing-protocols--classless-era)
15. [RIP v1 vs v2 — Protocol Packets in ASCII](#15-rip-v1-vs-v2--protocol-packets-in-ascii)
16. [OSPF — Protocol Packets in ASCII](#16-ospf--protocol-packets-in-ascii)
17. [BGP — Protocol Packets in ASCII](#17-bgp--protocol-packets-in-ascii)
18. [Special and Reserved IP Ranges](#18-special-and-reserved-ip-ranges)
19. [Private vs Public IP Space](#19-private-vs-public-ip-space)
20. [C Implementation — Complete Router Engine](#20-c-implementation--complete-router-engine)
21. [Rust Implementation — Complete Router Engine](#21-rust-implementation--complete-router-engine)
22. [Mental Models and Decision Trees](#22-mental-models-and-decision-trees)
23. [Comparison Summary Table](#23-comparison-summary-table)

---

## 1. Prerequisites — Binary Fundamentals for Networking

Before understanding IP routing, you must be fluent in reading IP addresses in binary. Every routing decision is ultimately a **bitwise operation**.

### What is a Bit?

A **bit** is the smallest unit of information — it is either `0` or `1`. Eight bits make a **byte** (also called an **octet** in networking).

### Decimal to Binary Conversion

An IPv4 address is 32 bits, written as 4 groups of 8 bits (octets), separated by dots.

Each bit position in an octet represents a power of 2:

```
Bit Position:  7    6    5    4    3    2    1    0
Power of 2:   128   64   32   16    8    4    2    1
```

**Example: Convert 192 to binary**

```
192 ÷ 2 = 96  remainder 0
 96 ÷ 2 = 48  remainder 0
 48 ÷ 2 = 24  remainder 0
 24 ÷ 2 = 12  remainder 0
 12 ÷ 2 =  6  remainder 0
  6 ÷ 2 =  3  remainder 0
  3 ÷ 2 =  1  remainder 1
  1 ÷ 2 =  0  remainder 1
  
Read remainders bottom-up: 11000000 = 192
```

Or use the power table:
```
128 + 64 = 192
  1   1   0   0   0   0   0   0
```

### Key Binary Operations Used in Routing

#### Bitwise AND (`&`)

Used to extract the **network address** from an IP address using a mask:

```
IP Address:   192.168.10.5   = 11000000.10101000.00001010.00000101
Subnet Mask:  255.255.255.0  = 11111111.11111111.11111111.00000000
              AND operation  = (&) each bit
Network:      192.168.10.0   = 11000000.10101000.00001010.00000000
```

**Rule:** `1 AND 1 = 1`, `1 AND 0 = 0`, `0 AND 0 = 0`

#### Bitwise NOT (`~`)

Used to compute the **wildcard mask** (inverse of subnet mask):

```
Subnet Mask: 255.255.255.0  = 11111111.11111111.11111111.00000000
NOT:         0.0.0.255      = 00000000.00000000.00000000.11111111
```

#### Bitwise OR (`|`)

Used to compute **broadcast address** (network address OR wildcard mask):

```
Network:      192.168.10.0  = 11000000.10101000.00001010.00000000
Wildcard:     0.0.0.255     = 00000000.00000000.00000000.11111111
OR:           192.168.10.255= 11000000.10101000.00001010.11111111
```

---

## 2. What is an IP Address?

An **IP address** (Internet Protocol Address) is a unique numerical label assigned to every device on a network that uses the Internet Protocol for communication.

Think of it like a **postal address** for your device — it tells the network exactly where to deliver data.

### IPv4 Structure

IPv4 addresses are **32-bit numbers**, written in **dotted-decimal notation**:

```
 Dotted-Decimal:   192     .   168    .    10    .    1
 In Binary:      11000000  . 10101000 . 00001010 . 00000001
 As single 32-bit: 11000000101010000000101000000001
 As hex:           C0      .  A8      .   0A     .   01
```

**Full 32-bit breakdown:**

```
Bit:   31 30 29 28 27 26 25 24 | 23 22 21 20 19 18 17 16 | 15 14 13 12 11 10 9 8 | 7 6 5 4 3 2 1 0
Value:  1  1  0  0  0  0  0  0 |  1  0  1  0  1  0  0  0 |  0  0  0  0  1  0 1 0 | 0 0 0 0 0 0 0 1
        <------Octet 1------->   <------Octet 2------->    <------Octet 3------->   <--Octet 4--->
              192                       168                        10                      1
```

### Address Space

With 32 bits, IPv4 can represent **2^32 = 4,294,967,296** unique addresses (~4.3 billion).

---

## 3. The Network/Host Divide — The Core Mental Model

Every IPv4 address has **two logical parts**:

```
+----------------------------------+------------------+
|         NETWORK PORTION          |   HOST PORTION   |
|    (Identifies the network)      | (Identifies the  |
|    Like a street name            |  device on that  |
|                                  |  network)        |
|                                  |  Like a house    |
|                                  |  number          |
+----------------------------------+------------------+
```

**Mental Model:**
- The **Network** portion = the neighborhood / street
- The **Host** portion = specific house number
- A **router** uses the network portion to forward packets
- A **switch/host** uses the host portion to identify devices locally

**Example:**

```
IP Address: 192.168.1.100

If network is first 3 octets:
  Network: 192.168.1  (the street "192.168.1")
  Host:    .100       (house number 100 on that street)

All devices on 192.168.1.x share the same "street"
They can communicate directly without a router.
```

---

## 4. Classful IP Addressing (1981–1993)

Classful addressing was defined in **RFC 791 (1981)**. The idea was simple and elegant: **look at the first few bits of the IP address to determine the class**, and the class determines where the network/host boundary sits.

No extra information needed — the class is **self-identifying** from the high-order bits.

### The 5 IP Classes

```
CLASS A:
First bit = 0
+--+--------+------------------------+
|0 | 7 bits |       24 bits          |
|  | NETWORK|         HOST           |
+--+--------+------------------------+
Range: 0.0.0.0 to 127.255.255.255
Networks: 2^7  = 128 (minus reserved = 126 usable)
Hosts:    2^24 - 2 = 16,777,214 per network
Default mask: 255.0.0.0 (/8)

CLASS B:
First two bits = 10
+--+--+------+--------------------+
|1 |0 |14bits|      16 bits       |
|  |  |NET   |       HOST         |
+--+--+------+--------------------+
Range: 128.0.0.0 to 191.255.255.255
Networks: 2^14 = 16,384
Hosts:    2^16 - 2 = 65,534 per network
Default mask: 255.255.0.0 (/16)

CLASS C:
First three bits = 110
+--+--+--+-----+---------+
|1 |1 |0 |21bits| 8 bits  |
|  |  |  |NET   |  HOST   |
+--+--+--+-----+---------+
Range: 192.0.0.0 to 223.255.255.255
Networks: 2^21 = 2,097,152
Hosts:    2^8 - 2 = 254 per network
Default mask: 255.255.255.0 (/24)

CLASS D (Multicast):
First four bits = 1110
+--+--+--+--+---------------------------+
|1 |1 |1 |0 |       28 bits             |
|  |  |  |  |   MULTICAST GROUP ID      |
+--+--+--+--+---------------------------+
Range: 224.0.0.0 to 239.255.255.255
Not for regular host addressing
Used for: OSPF (224.0.0.5), RIP (224.0.0.9), DVMRP

CLASS E (Reserved/Experimental):
First four bits = 1111
+--+--+--+--+---------------------------+
|1 |1 |1 |1 |       28 bits             |
|  |  |  |  |       RESERVED            |
+--+--+--+--+---------------------------+
Range: 240.0.0.0 to 255.255.255.255
Reserved for research/future use
255.255.255.255 = limited broadcast
```

### Classful Address Identification Flowchart

```
                    [Look at IP Address]
                           |
                    [Read First Octet]
                           |
              +------------+------------+
              |                         |
         [0-127?]                 [128-255?]
              |                         |
           CLASS A              [Read First 2 bits]
    (First bit = 0)                     |
                             +----------+----------+
                             |                     |
                        [10xxxxxx]           [11xxxxxx]
                        128-191               |
                         CLASS B         [Read first 3 bits]
                                              |
                                   +----------+----------+
                                   |                     |
                              [110xxxxx]           [111xxxxx]
                              192-223                    |
                               CLASS C        +----------+------+
                                              |                 |
                                        [1110xxxx]        [1111xxxx]
                                         224-239           240-255
                                          CLASS D           CLASS E
                                         (Multicast)      (Reserved)
```

### Memory Aid — Classful Ranges

```
+-------+------------+--------------------+---------------+------------+
| Class | First Bits | Range              | Default Mask  | Hosts/Net  |
+-------+------------+--------------------+---------------+------------+
|   A   |     0      | 1.0.0.0-127.x.x.x  | /8  (255.0.0.0)| 16,777,214|
|   B   |    10      | 128.x.x.x-191.x.x.x| /16 (255.255.0)| 65,534    |
|   C   |   110      | 192.x.x.x-223.x.x.x| /24 (255.255.255.0)| 254  |
|   D   |  1110      | 224.x.x.x-239.x.x.x| N/A (Multicast)| N/A      |
|   E   |  1111      | 240.x.x.x-255.x.x.x| N/A (Reserved) | N/A      |
+-------+------------+--------------------+---------------+------------+
```

### How a Classful Router Determines Network Boundary

In classful routing, a router receiving an IP address **needs no additional information** to find the network:

```
Step 1: Read first octet of IP
Step 2: Determine class by inspecting high-order bits
Step 3: Apply default mask based on class

Example: Packet arrives for 172.16.50.4

First octet = 172
172 in binary = 10101100
First two bits = 10 → CLASS B
Default mask for B = /16 = 255.255.0.0

Network = 172.16.0.0
Host = 50.4
```

### Classful Routing in Action — Full Example

```
TOPOLOGY:
                                    [Router R1]
                                   /            \
                          [Net A]               [Net B]
                      10.0.0.0/8             172.16.0.0/16

Packet: dst = 10.5.3.2

R1's Classful Routing Table:
+------------------+-------------+-----------+
| Destination Net  | Class       | Next Hop  |
+------------------+-------------+-----------+
| 10.0.0.0         | A (/8)      | eth0      |
| 172.16.0.0       | B (/16)     | eth1      |
+------------------+-------------+-----------+

Lookup Process:
1. Read first octet of 10.5.3.2 → 10
2. 10 is 00001010 in binary → starts with 0 → Class A
3. Apply /8 mask: network = 10.0.0.0
4. Match found! Forward to eth0.
```

---

## 5. Problems with Classful Addressing

By the early 1990s, the internet faced a serious **address exhaustion crisis**. Classful addressing had three major problems:

### Problem 1 — Address Waste (The All-or-Nothing Problem)

```
Scenario: A company needs 300 IP addresses.

CLASS C gives: 254 hosts  ← NOT ENOUGH
CLASS B gives: 65,534 hosts ← MASSIVE OVERKILL

The company must take a CLASS B block.
They use 300 addresses, WASTE 65,234 addresses.
Those wasted addresses cannot be given to anyone else.

The internet cannot afford this waste.
```

**Visualization of Waste:**

```
CLASS B Block (65,534 usable addresses):
+----+----+----+----+----+----+----+----+----+----+...
|USED|USED|USED|USED|USED|USED|USED|USED|USED|USED|...
+----+----+----+----+----+----+----+----+----+----+...
 300 addresses used out of 65,534

##############################################
#                                            #
#  WASTED: 65,234 addresses (99.5% waste!)   #
#                                            #
##############################################
```

### Problem 2 — Routing Table Explosion

```
With classful addressing, every Class C network is a SEPARATE entry.
If ISPs assign individual /24 blocks to thousands of customers:

Routing Table Explosion:
+------------------+
| 192.168.0.0      |
| 192.168.1.0      |
| 192.168.2.0      |
| ...              |
| 192.168.255.0    |  ← 256 entries for one company!
| 193.0.0.0        |
| ...              |
| (millions more)  |
+------------------+

Routers in the 1990s had limited memory and CPU.
Routing tables growing to millions of entries was
causing router crashes and network instability.
```

### Problem 3 — Supernet Aggregation Impossible

```
Without CIDR, you cannot summarize routes.

These 4 networks SHOULD be summarized as one:
  192.168.0.0/24
  192.168.1.0/24
  192.168.2.0/24
  192.168.3.0/24

In classful routing, each is a SEPARATE Class C.
No way to tell routers "all 4 are in same direction."
Every router in the world must know all 4 separately.
```

---

## 6. Subnet Mask — The Boundary Marker

A **subnet mask** is a 32-bit number that tells you where the **network portion** ends and the **host portion** begins. It uses a contiguous sequence of 1s followed by a contiguous sequence of 0s.

### Anatomy of a Subnet Mask

```
Subnet Mask: 255.255.255.0

In binary:
11111111 . 11111111 . 11111111 . 00000000
|<---- network bits ---->|  |<- host bits ->|
        24 ones                  8 zeros

The 1s "mask" the network portion.
The 0s expose the host portion.
```

### Prefix Notation (CIDR Notation)

Instead of writing `255.255.255.0`, we write **/24** — meaning **24 ones** in the mask.

```
/8   = 11111111.00000000.00000000.00000000 = 255.0.0.0
/16  = 11111111.11111111.00000000.00000000 = 255.255.0.0
/24  = 11111111.11111111.11111111.00000000 = 255.255.255.0
/25  = 11111111.11111111.11111111.10000000 = 255.255.255.128
/26  = 11111111.11111111.11111111.11000000 = 255.255.255.192
/27  = 11111111.11111111.11111111.11100000 = 255.255.255.224
/28  = 11111111.11111111.11111111.11110000 = 255.255.255.240
/29  = 11111111.11111111.11111111.11111000 = 255.255.255.248
/30  = 11111111.11111111.11111111.11111100 = 255.255.255.252
/31  = 11111111.11111111.11111111.11111110 = 255.255.255.254
/32  = 11111111.11111111.11111111.11111111 = 255.255.255.255
```

### Computing Key Addresses

Given any IP + mask, you can derive 4 critical values:

```
Given: 192.168.10.100 / 255.255.255.0

Step 1 — Network Address (IP AND Mask):
  11000000.10101000.00001010.01100100   (192.168.10.100)
& 11111111.11111111.11111111.00000000   (255.255.255.0)
= 11000000.10101000.00001010.00000000   (192.168.10.0)  ← NETWORK

Step 2 — Broadcast Address (Network OR ~Mask):
  ~Mask = 00000000.00000000.00000000.11111111
  11000000.10101000.00001010.00000000   (192.168.10.0)
| 00000000.00000000.00000000.11111111   (~Mask)
= 11000000.10101000.00001010.11111111   (192.168.10.255) ← BROADCAST

Step 3 — Host Range:
  First usable: Network + 1 = 192.168.10.1
  Last usable:  Broadcast - 1 = 192.168.10.254

Step 4 — Number of Hosts:
  Host bits = 8 (the 0s in mask)
  Total hosts = 2^8 = 256
  Usable hosts = 256 - 2 = 254  (subtract network + broadcast)
```

### Why Subtract 2?

```
Network address (192.168.10.0):
  - Used to IDENTIFY the network
  - Cannot be assigned to a host

Broadcast address (192.168.10.255):
  - Sending to this address reaches ALL hosts on the network
  - Cannot be assigned to a host
  
Therefore: usable hosts = 2^(host_bits) - 2
```

---

## 7. Classless IP Routing — CIDR (1993–Present)

**CIDR** = **C**lassless **I**nter-**D**omain **R**outing

Defined in **RFC 1517, 1518, 1519, 1520 (1993)**.

The revolutionary idea: **throw away the concept of classes**. The subnet mask is **always explicitly specified** alongside the IP address. No implicit rules based on the first octet.

### The CIDR Principle

```
CLASSFUL (implicit mask based on class):
  Address:   172.16.5.0      → Router ASSUMES /16 because 172.x is Class B
  Mask:      (implied /16)

CLASSLESS (explicit mask always provided):
  Address:   172.16.5.0/24   → Router uses /24 EXACTLY as specified
  Mask:      255.255.255.0   (explicitly provided)

The "address + prefix-length" pair is called a PREFIX.
```

### CIDR Enables Route Aggregation (Supernetting)

The most powerful feature of CIDR: **multiple networks can be represented as one routing entry**.

```
Before CIDR (4 separate routes):
  192.168.0.0/24  → via 10.0.0.1
  192.168.1.0/24  → via 10.0.0.1
  192.168.2.0/24  → via 10.0.0.1
  192.168.3.0/24  → via 10.0.0.1

After CIDR (1 aggregated route):
  192.168.0.0/22  → via 10.0.0.1

Why does this work? Let's look at binary:

  192.168.0.0   = 11000000.10101000.00000000.00000000
  192.168.1.0   = 11000000.10101000.00000001.00000000
  192.168.2.0   = 11000000.10101000.00000010.00000000
  192.168.3.0   = 11000000.10101000.00000011.00000000
                  |<------------ 22 bits match ------>|

All 4 share the same 22 leftmost bits!
So /22 covers all four with ONE entry.
```

### CIDR Block Sizes — Powers of 2

```
Prefix  | # Addresses | # Usable Hosts | Typical Use
--------+-------------+----------------+---------------------------
/8      | 16,777,216  | 16,777,214     | Large ISP allocation
/16     | 65,536      | 65,534         | Large organization
/20     | 4,096       | 4,094          | Medium organization
/22     | 1,024       | 1,022          | Small ISP customers
/24     | 256         | 254            | Common LAN
/25     | 128         | 126            | Half of /24
/26     | 64          | 62             | Small department
/27     | 32          | 30             | Small network
/28     | 16          | 14             | Tiny network
/29     | 8           | 6              | Small WAN link
/30     | 4           | 2              | Point-to-point WAN link
/31     | 2           | 2              | Point-to-point (RFC 3021)
/32     | 1           | 1              | Single host route, loopback
```

### CIDR Notation Explained

```
  192.168.10.0 / 24
  |             |
  |             +-- Prefix Length: number of 1s in the subnet mask
  |                 (how many bits identify the network)
  +---------------- Network Address: the base address of this block

Reading it: "The network 192.168.10.0, with 24 bits for the network
             and 8 bits for hosts"
```

---

## 8. Variable Length Subnet Masking (VLSM)

**VLSM** is the ability to use **different subnet masks within the same network**. This is only possible with classless routing.

### The Problem VLSM Solves

```
Company has been assigned 192.168.1.0/24 (254 hosts).

Requirements:
  Department A: 100 hosts
  Department B: 50 hosts
  Department C: 25 hosts
  WAN Link 1:   2 hosts (router-to-router)
  WAN Link 2:   2 hosts (router-to-router)

CLASSFUL: You'd need separate networks for each.
VLSM: You can carve up ONE network into different-sized pieces.
```

### VLSM Allocation Example

```
Starting pool: 192.168.1.0/24 (256 addresses)

Step 1: Allocate largest first (best practice)

Department A (needs 100 hosts, min block = /25 = 126 hosts):
  192.168.1.0/25   → hosts: 192.168.1.1 - 192.168.1.126
  Used: 128 addresses. Remaining pool: 192.168.1.128/25

Department B (needs 50 hosts, min block = /26 = 62 hosts):
  192.168.1.128/26 → hosts: 192.168.1.129 - 192.168.1.190
  Used: 64 addresses. Remaining pool: 192.168.1.192/26

Department C (needs 25 hosts, min block = /27 = 30 hosts):
  192.168.1.192/27 → hosts: 192.168.1.193 - 192.168.1.222
  Used: 32 addresses. Remaining pool: 192.168.1.224/27

WAN Link 1 (needs 2 hosts, min block = /30 = 2 hosts):
  192.168.1.224/30 → hosts: 192.168.1.225 - 192.168.1.226
  Used: 4 addresses. Remaining pool: 192.168.1.228/30

WAN Link 2 (needs 2 hosts, min block = /30):
  192.168.1.228/30 → hosts: 192.168.1.229 - 192.168.1.230
  Used: 4 addresses. Remaining pool: 192.168.1.232/...

Visual Layout:
+-----------------------------------+
| 192.168.1.0/24 (256 addresses)    |
+------------------+----------------+
| 192.168.1.0/25   | 192.168.1.128  |
| (Dept A, 128)    | /25 (128)      |
+------------------+--------+-------+
                   |128/26  |192/26 |
                   |(Dept B)|       |
                   +--------+---+---+
                            |192| 224/27 (remaining)
                            |/27|
                            |(C)|
                            +---+
```

---

## 9. Subnetting — Dividing Networks

**Subnetting** is the process of dividing a larger network into smaller sub-networks (subnets).

### Subnetting Mental Model

```
Imagine you're given one large building (the network).
Subnetting = installing internal walls to create rooms (subnets).

Each room has its own:
- Room number (network address)
- Range of seats (host addresses)
- Emergency exit routing (default gateway)

Rooms cannot communicate directly — they need
to go through the building's reception (router).
```

### Subnetting Process — Step by Step

**Problem:** Subnet `10.0.0.0/8` into multiple `/16` subnets.

```
Original: 10.0.0.0/8
Binary:   00001010.00000000.00000000.00000000
Mask /8:  11111111.00000000.00000000.00000000
          |NET-BITS|<----- host bits -------->|

We want /16 subnets (borrow 8 more bits from host):
New mask: 11111111.11111111.00000000.00000000
          |<-- original -->|<borrowed>|<host>|

Number of new subnets = 2^(borrowed bits) = 2^8 = 256 subnets

Subnet 0:  10.0.0.0/16    hosts: 10.0.0.1  - 10.0.255.254
Subnet 1:  10.1.0.0/16    hosts: 10.1.0.1  - 10.1.255.254
Subnet 2:  10.2.0.0/16    hosts: 10.2.0.1  - 10.2.255.254
...
Subnet 255: 10.255.0.0/16 hosts: 10.255.0.1 - 10.255.255.254
```

### Subnet Calculation Formula

```
Given: IP/prefix, want to create subnets of size /new_prefix

Additional bits borrowed = new_prefix - original_prefix
Number of subnets = 2^(additional bits borrowed)
Hosts per subnet = 2^(32 - new_prefix) - 2

Example: 192.168.0.0/24 → subdivide into /26 subnets
  Borrowed bits = 26 - 24 = 2
  Number of /26 subnets = 2^2 = 4
  Hosts per /26 = 2^(32-26) - 2 = 2^6 - 2 = 64 - 2 = 62

  Subnet 1: 192.168.0.0/26   (hosts: .1   to .62,   broadcast .63)
  Subnet 2: 192.168.0.64/26  (hosts: .65  to .126,  broadcast .127)
  Subnet 3: 192.168.0.128/26 (hosts: .129 to .190,  broadcast .191)
  Subnet 4: 192.168.0.192/26 (hosts: .193 to .254,  broadcast .255)
```

### Subnet Block Size Trick

The **block size** (increment between subnets) = `256 - last non-zero octet of mask`.

```
Mask 255.255.255.192 (/26): last octet = 192
  Block size = 256 - 192 = 64

Subnets start at: 0, 64, 128, 192 → exactly /26 subnets!

Mask 255.255.255.224 (/27): last octet = 224
  Block size = 256 - 224 = 32

Subnets start at: 0, 32, 64, 96, 128, 160, 192, 224
```

---

## 10. Supernetting — Route Aggregation

**Supernetting** is the opposite of subnetting — combining multiple smaller networks into one larger routing entry. This is also called **route summarization** or **route aggregation**.

### Why Supernet?

```
WITHOUT SUPERNETTING (1000 routes in table):
  ISP announces 1000 individual /24 routes to internet.
  Every router in the world stores 1000 entries.
  
WITH SUPERNETTING (1 route):
  ISP announces 1 supernet covering all 1000 networks.
  Every router stores 1 entry.
  
RESULT: Routing tables shrink dramatically.
        Routers use less memory and CPU.
        Convergence is faster.
```

### Supernetting Algorithm

**Find the common prefix** of all networks you want to aggregate.

```
Networks to aggregate:
  10.16.0.0/24
  10.17.0.0/24
  10.18.0.0/24
  10.19.0.0/24

Step 1: Write in binary:
  10.16.0.0  = 00001010.00010000.00000000.00000000
  10.17.0.0  = 00001010.00010001.00000000.00000000
  10.18.0.0  = 00001010.00010010.00000000.00000000
  10.19.0.0  = 00001010.00010011.00000000.00000000

Step 2: Find common prefix (matching bits from left):
  00001010.00010000
  00001010.00010001
  00001010.00010010
  00001010.00010011
               ^^
               These 2 bits differ (00, 01, 10, 11)
  
  Common prefix length = 22 bits

Step 3: Supernet = 10.16.0.0/22

Verification: Does 10.16.0.0/22 cover all four?
  10.16.0.0/22 means bits 1-22 are fixed.
  Bits 23-32 can vary = 2^10 = 1024 addresses
  10.16.0.0 to 10.19.255.255 ✓ (covers all four /24s)
```

### Supernetting Constraints

```
CRITICAL RULE: Networks must be CONTIGUOUS and start on a 
               NATURAL BOUNDARY for the new prefix.

Example of INVALID supernet:
  10.16.0.0/24
  10.18.0.0/24
  (these two are not contiguous — 10.17 is missing)

Example of VALID but POORLY BOUNDED supernet:
  10.17.0.0/24
  10.18.0.0/24
  Common prefix = 22? Let's check:
  10.17.0.0 = 00001010.00010001.00000000.00000000
  10.18.0.0 = 00001010.00010010.00000000.00000000
                              ^^
  Bit 21-22: 01 vs 10 — different at bit 21
  Common prefix = 20 bits (10.16.0.0/20)
  
  But 10.16.0.0/20 covers 10.16.0.0 through 10.31.255.255!
  This is over-aggregation — includes addresses you don't own!
```

---

## 11. Longest Prefix Match — How Routers Decide

**Longest Prefix Match (LPM)** is the algorithm routers use to decide which routing table entry to use when multiple entries could match a destination.

### The Concept of "More Specific"

```
In routing, a MORE SPECIFIC route is PREFERRED.

More specific = longer prefix = smaller network = more precise match.

Example routing table:
  0.0.0.0/0       → via 10.0.0.1  (default route, matches EVERYTHING)
  10.0.0.0/8      → via 10.0.0.2  (matches 10.x.x.x)
  10.20.0.0/16    → via 10.0.0.3  (matches 10.20.x.x)
  10.20.50.0/24   → via 10.0.0.4  (matches 10.20.50.x)
  10.20.50.128/25 → via 10.0.0.5  (matches 10.20.50.128-255)

Destination: 10.20.50.200

Matches:
  0.0.0.0/0       → YES (matches everything)   prefix length = 0
  10.0.0.0/8      → YES (10.x.x.x)             prefix length = 8
  10.20.0.0/16    → YES (10.20.x.x)            prefix length = 16
  10.20.50.0/24   → YES (10.20.50.x)           prefix length = 24
  10.20.50.128/25 → YES (10.20.50.128-255)     prefix length = 25 ← WINNER

Router sends to 10.0.0.5 (the LONGEST prefix match = most specific)
```

### LPM Flowchart

```
[Packet arrives with destination IP: D]
                |
                v
[Scan all routing table entries]
                |
                v
[For each entry (Network N, mask M):]
    [Compute: D AND M]
    [If result == N: this entry MATCHES]
                |
                v
[Among ALL matching entries:]
    [Select the one with LARGEST prefix length]
                |
                v
[Forward packet to that entry's next-hop]
```

### LPM Implementation Concept — Trie (Prefix Tree)

```
A Trie stores routes bit by bit.
Each node = one bit of the IP address.
Leaf = routing entry.

Example trie for:
  0.0.0.0/0  → A
  10.0.0.0/8 → B

Root
 |
 +-- 0 (bit 0 = 0)
 |    |
 |    +-- any further bits... (matches 0.0.0.0/0 = A)
 |
 +-- 1 (bit 0 = 1)
      |
      +-- 0 (bit 1 = 0 → 10.x.x.x)
           |
           +-- 0 (bit 2 = 0 → 10.0-63.x.x)
                |
                +-- 0 (bit 3 = 0 → 10.0-31.x.x)
                     ...
                     [after 8 bits → Node B: 10.0.0.0/8]

Router traverses trie bit-by-bit from most significant bit.
Records the LAST matching node = longest prefix match.
```

---

## 12. The Routing Table — Anatomy and Lookup

A **routing table** is the database a router uses to decide where to forward packets.

### Routing Table Entry Fields

```
+------------------+----------+----------+--------+------+---------+
| DESTINATION      | PREFIX   | NEXT HOP | IFACE  | MET  | ADMIN   |
| NETWORK          | LENGTH   |          |        | RIC  | DIST    |
+------------------+----------+----------+--------+------+---------+
| 192.168.1.0      | /24      | 10.0.0.2 | eth0   | 1    | 0       |
| 10.0.0.0         | /8       | 10.0.0.1 | eth1   | 110  | 110     |
| 0.0.0.0          | /0       | 172.16.0.1| eth2  | 1    | 1       |
+------------------+----------+----------+--------+------+---------+

Fields explained:
  Destination Network: The network this route reaches
  Prefix Length:       The subnet mask (how specific the route is)
  Next Hop:           IP of the NEXT router to send the packet to
  Interface:          Which physical port to send it out
  Metric:             Cost (lower = preferred)
  Administrative Dist: Trustworthiness of routing source (lower = more trusted)
```

### Administrative Distance — Routing Source Trust

```
+-----------------------+------------------+
| Routing Source        | Admin Distance   |
+-----------------------+------------------+
| Directly Connected    | 0 (most trusted) |
| Static Route          | 1                |
| EIGRP Summary         | 5                |
| BGP (external)        | 20               |
| EIGRP (internal)      | 90               |
| OSPF                  | 110              |
| IS-IS                 | 115              |
| RIP                   | 120              |
| BGP (internal)        | 200              |
| Unknown/Unreachable   | 255 (never used) |
+-----------------------+------------------+

Lower admin distance = more trusted source.
If two routing protocols provide a route to same destination,
the one with LOWER admin distance wins.
```

### Types of Routes in a Routing Table

```
1. CONNECTED ROUTE (C):
   Created automatically when an interface is configured with an IP.
   The router is directly attached to that network.
   Admin distance = 0.

2. STATIC ROUTE (S):
   Manually configured by an administrator.
   S* means it's a static DEFAULT route.
   Admin distance = 1.

3. DYNAMIC ROUTE:
   Learned from a routing protocol (RIP, OSPF, BGP, EIGRP).
   Admin distances vary by protocol.

4. DEFAULT ROUTE (0.0.0.0/0):
   The "route of last resort."
   Catches ALL traffic that doesn't match a more specific route.
   The "if all else fails, send here" rule.
```

---

## 13. Real Routing Protocols — Classful Era

### What is a Routing Protocol?

A **routing protocol** is a set of rules routers use to **discover**, **communicate**, and **maintain** information about network paths. It lets routers automatically build and update their routing tables.

**Key Terms:**
- **Convergence**: The state where all routers agree on the network topology
- **Metric**: The "cost" of a path (hops, bandwidth, delay, reliability)
- **Autonomous System (AS)**: A collection of networks under a single administrative domain

### RIP Version 1 (RFC 1058, 1988) — Classful

**Type:** Distance Vector (each router shares its full table with neighbors)
**Metric:** Hop count (max 15; 16 = unreachable — **infinity**)
**Update:** Broadcast (255.255.255.255) every 30 seconds
**Classful:** Does NOT send subnet mask with updates

```
RIP v1 Behavior:
  Router A has: 10.1.0.0/24 (directly connected)
  Router A tells neighbor B: "I can reach 10.1.0.0, cost 1"
  
  ❌ Router A does NOT say "/24" — the mask is implicit!
  
  Router B assumes:
    10.x.x.x is Class A → apply /8 mask → 10.0.0.0/8
  
  This is CLASSFUL BEHAVIOR — the mask is inferred from the class.
```

**Problems with RIP v1:**
```
1. No subnet mask in updates (classful only)
2. No authentication (anyone can send false routes)
3. Maximum 15 hops (small networks only)
4. Slow convergence (30-second updates + hold-down timers)
5. Count-to-infinity problem (loops can form)
6. Broadcasts cause load on all hosts on segment
```

### IGRP (Interior Gateway Routing Protocol) — Cisco Proprietary, Classful

**Type:** Distance Vector
**Metric:** Composite (bandwidth, delay, reliability, load, MTU)
**Update:** Broadcast every 90 seconds
**Classful:** No mask in updates

```
IGRP Metric = [K1*BW + (K2*BW)/(256-load) + K3*delay] * [K5/(reliability+K4)]

Default: K1=1, K2=0, K3=1, K4=0, K5=0
Simplified: Metric = BW_term + Delay_term
```

IGRP was deprecated — replaced by EIGRP (classless).

---

## 14. Real Routing Protocols — Classless Era

### RIP Version 2 (RFC 2453, 1998) — Classless

Same basic mechanism as RIP v1 but with critical additions:
- Sends **subnet mask** with each route (classless!)
- Uses **multicast** 224.0.0.9 (not broadcast)
- Supports **authentication** (MD5)
- Supports **VLSM** and **CIDR**

### OSPF (Open Shortest Path First — RFC 2328)

**Type:** Link-State (each router knows the ENTIRE topology)
**Metric:** Cost (based on bandwidth: cost = 10^8 / bandwidth_bps)
**Algorithm:** Dijkstra's Shortest Path First (SPF)
**Classless:** YES — carries subnet masks in LSAs
**Authentication:** YES (MD5)
**Area concept:** Scales through hierarchical area design

```
OSPF Concepts:

AREA: A logical group of routers sharing topology info.
      Area 0 = backbone area (all areas must connect to it).

LSA: Link State Advertisement — topology info flooded to all routers.
LSDB: Link State Database — each router's map of the entire network.
SPF: Dijkstra runs on LSDB to compute shortest paths.

OSPF Router Types:
  DR  = Designated Router (elected per segment)
  BDR = Backup Designated Router
  ABR = Area Border Router (connects areas)
  ASBR= AS Boundary Router (connects to external AS)

OSPF Neighbor States:
  Down → Init → 2-Way → Exstart → Exchange → Loading → Full
```

### BGP (Border Gateway Protocol — RFC 4271)

**Type:** Path Vector (carries full AS-PATH to detect loops)
**Used for:** Inter-AS routing (the internet's routing protocol)
**Port:** TCP 179 (reliable transport)
**Classless:** YES
**Scale:** BGP runs the entire internet (~950,000+ prefixes as of 2024)

```
BGP Concepts:

eBGP = External BGP (between different ASes)
iBGP = Internal BGP (within same AS)

AS-PATH: List of AS numbers the route has traversed.
         Used for loop prevention.
         Shorter AS-PATH generally preferred.

BGP Attributes (used for path selection):
  WEIGHT (Cisco-specific) — higher preferred
  LOCAL_PREF — higher preferred (iBGP)
  AS-PATH length — shorter preferred
  ORIGIN — IGP > EGP > Incomplete
  MED (Multi-Exit Discriminator) — lower preferred
  eBGP vs iBGP — eBGP preferred
  IGP metric to next-hop — lower preferred
  Router-ID — lower preferred (tiebreaker)

Memory aid: "We Love Oranges As Oranges Mean Pure Refreshment"
  W-eight, L-ocal_pref, O-rigin, AS-path, O-rigin(med), 
  M-ulti-exit, P-eers, R-outer-ID
```

### EIGRP (Enhanced IGRP) — Cisco, Classless

**Type:** Advanced Distance Vector (Diffusing Update Algorithm - DUAL)
**Metric:** Composite (like IGRP but extended)
**Classless:** YES — sends subnet masks
**Key feature:** Fast convergence without SPF recalculation
**DUAL:** Guarantees loop-free paths using feasibility condition

---

## 15. RIP v1 vs v2 — Protocol Packets in ASCII

### RIP Packet Header (Both v1 and v2)

```
RIP is carried over UDP, port 520.

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Command (1)  |  Version (1)  |       Must Be Zero (2)        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Route Entry 1 (20 bytes)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Route Entry 2 (20 bytes)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    ... (up to 25 route entries per packet)     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Command: 1 = Request, 2 = Response
Version: 1 = RIPv1, 2 = RIPv2
```

### RIP v1 Route Entry (20 bytes per route)

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Address Family Identifier (2)|         Must Be Zero (2)      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     IP Address (4 bytes)                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     Must Be Zero (4 bytes)                     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     Must Be Zero (4 bytes)                     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Metric (4 bytes)                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

NOTE: No subnet mask field! Classful only.
Address Family: 2 = IP (AF_INET)
Metric: 1-15 (16 = infinity/unreachable)
```

### RIP v2 Route Entry (20 bytes per route — same size, different fields)

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Address Family Identifier (2)|         Route Tag (2)         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     IP Address (4 bytes)                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     Subnet Mask (4 bytes)  ← NEW IN v2!       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     Next Hop (4 bytes)     ← NEW IN v2!       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Metric (4 bytes)                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Route Tag: Used to distinguish internal vs redistributed routes
Subnet Mask: Explicit mask! This is what makes v2 CLASSLESS.
Next Hop: Allows route to specify a different next-hop router
```

### RIP v2 Authentication Packet (Special First Entry)

```
When Authentication is enabled, the FIRST route entry is replaced
by an authentication entry (AFI = 0xFFFF signals auth):

   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |       0xFFFF (Auth marker)    |  Auth Type (2=MD5, 1=plain)   |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 Authentication Data (16 bytes)                 |
   |                     (password or MD5 hash)                     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### RIP Update Exchange — Full Protocol Flow

```
ROUTER A                                              ROUTER B
(192.168.1.1)                                    (192.168.1.2)

    |                  [Initial State]                   |
    |   Both routers start, interfaces come up           |
    |                                                    |
    |------------ RIP REQUEST (broadcast) ------------->|
    |  Command=1, Version=2                              |
    |  AFI=0, Metric=16 (request for full table)        |
    |                                                    |
    |<----------- RIP RESPONSE (unicast) ---------------|
    |  Command=2, Version=2                              |
    |  Route: 10.0.0.0/8, Next-hop=0.0.0.0, Metric=1   |
    |  Route: 172.16.0.0/16, Next-hop=0.0.0.0, Metric=2|
    |                                                    |
    |   [After 30 seconds — periodic update]            |
    |                                                    |
    |<----------- RIP RESPONSE (multicast 224.0.0.9) ---|
    |  Command=2, Version=2                              |
    |  Route: 10.0.0.0/8, Metric=1                      |
    |  Route: 172.16.0.0/16, Metric=2                   |
    |                                                    |
    |   [Route ages: if no update in 180s → invalid]    |
    |   [Hold-down timer: 180s before removing route]   |
    |   [Flush timer: 240s → delete route]              |
    |                                                    |
    |   [If Router A detects route failure:]             |
    |                                                    |
    |------------ TRIGGERED UPDATE (immediate) -------->|
    |  Command=2, Version=2                              |
    |  Route: 10.0.0.0/8, Metric=16 (POISONED!)        |
    |  (Metric=16 means "unreachable/infinity")          |
    |                                                    |
```

---

## 16. OSPF — Protocol Packets in ASCII

OSPF runs directly over IP (protocol number 89), NOT over TCP/UDP.

### OSPF Common Packet Header (24 bytes)

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |   Version (1) |     Type (1)  |         Packet Length (2)     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Router ID (4 bytes)                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Area ID (4 bytes)                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum (2)        |  AuType (2)   |  Auth (8 bytes)|
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Version: 2 (OSPFv2 for IPv4), 3 (OSPFv3 for IPv6)
Type:    1=Hello, 2=DBD, 3=LSR, 4=LSU, 5=LSAck
Router ID: 32-bit unique identifier (usually highest IP on router)
Area ID: Which OSPF area this packet belongs to (0.0.0.0 = backbone)
```

### OSPF Type 1 — Hello Packet

```
OSPF Hello is sent every 10 seconds (or 30s on NBMA networks).
Used to discover neighbors and elect DR/BDR.
Multicast to 224.0.0.5 (all OSPF routers).

   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                     [OSPF Common Header - 24 bytes]            |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Network Mask (4)                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Hello Interval (2)    |      Options (1) | Rtr Pri (1)|
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                      Router Dead Interval (4)                  |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Designated Router (4)                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 Backup Designated Router (4)                   |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Neighbor (Router ID) (4)                    |
   |                    (repeated for each neighbor)                |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Network Mask: Subnet mask of the sending interface
Hello Interval: How often hellos are sent (default 10s)
Router Dead Interval: How long before router declared down (40s)
Designated Router: IP of elected DR (0.0.0.0 if unknown yet)
Backup DR: IP of BDR
Neighbor: List of all neighbors this router has heard from
```

### OSPF Type 4 — Link State Update (Contains LSAs)

```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    [OSPF Common Header]                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Number of LSAs (4)                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       LSA 1 Header (20 bytes)                  |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       LSA 1 Data (variable)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   ...

LSA Header (20 bytes):
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          LS Age (2)           | Options (1)   |  LS Type (1)  |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Link State ID (4)                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                      Advertising Router (4)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                      LS Sequence Number (4)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           LS Checksum (2)     |             Length (2)        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

LS Age: Time in seconds since LSA was originated (max age = 3600s)
LS Type: 1=Router, 2=Network, 3=Summary, 4=ASBR-Summary, 5=AS-External
LS Sequence Number: Monotonically increasing; newer = larger number
```

### OSPF Neighbor State Machine

```
[Down]
  |
  | Receive Hello from neighbor
  v
[Init]  ← We heard from neighbor, but they haven't heard from us
  |
  | Neighbor's Hello contains OUR Router-ID
  v
[2-Way]  ← Bidirectional communication established
  |        (DR/BDR election happens here)
  | (Only continue to Full with DR/BDR, or on point-to-point)
  v
[Exstart]  ← Determine master/slave, initial sequence numbers
  |
  v
[Exchange]  ← Exchange DBD (Database Description) packets
  |           (Summaries of LSDB contents)
  v
[Loading]   ← Request missing LSAs via LSR, receive via LSU
  |
  v
[Full]  ← LSDBs are synchronized! Adjacency is complete.
```

### OSPF Full Session — Protocol Flow

```
ROUTER A (1.1.1.1)                              ROUTER B (2.2.2.2)
Area 0                                           Area 0

    |    [Both interfaces come up on same segment]    |
    |                                                 |
    |------ Hello (224.0.0.5) ---------------------->|
    |  RouterID=1.1.1.1, DR=0.0.0.0, BDR=0.0.0.0   |
    |  Neighbor list: (empty — just started)          |
    |                                                 |
    |<----- Hello (224.0.0.5) ------------------------|
    |  RouterID=2.2.2.2, DR=0.0.0.0, BDR=0.0.0.0   |
    |  Neighbor list: (empty)                         |
    |                                                 |
    |   [A sees B's Hello, enters INIT state for B]   |
    |                                                 |
    |------ Hello (224.0.0.5) ---------------------->|
    |  Neighbor list: [2.2.2.2] ← A has heard B      |
    |                                                 |
    |   [B sees A's RouterID in B's neighbor list]    |
    |   [B enters 2-WAY state for A]                  |
    |   [Both in 2-WAY: DR/BDR election starts]       |
    |   [Assume: A=DR, B=BDR based on priority/RID]  |
    |                                                 |
    |------ DBD (master probe, seq=X) -------------->|
    |  I=1 (init), M=1 (more), MS=1 (master claim)   |
    |                                                 |
    |<----- DBD (slave accept, seq=X) ---------------|
    |  I=1, M=1, MS=0 (slave), seq=X (echoes master) |
    |   [EXSTART complete: A=Master, B=Slave]         |
    |                                                 |
    |------ DBD (seq=X, LSDB summary) ------------->|
    |  Lists all LSA headers A has in its LSDB        |
    |                                                 |
    |<----- DBD (seq=X+1, LSDB summary) ------------|
    |  Lists all LSA headers B has in its LSDB        |
    |   [EXCHANGE: both know what the other has]      |
    |                                                 |
    |<----- LSR (requesting missing LSAs) ------------|
    |  "Please send me LSAs: X, Y, Z"                |
    |                                                 |
    |------ LSU (sending requested LSAs) ----------->|
    |  Actual LSA data for X, Y, Z                    |
    |                                                 |
    |<----- LSAck (acknowledgement) -----------------|
    |   [LOADING complete]                            |
    |                                                 |
    |   [FULL STATE — adjacency established!]          |
    |   [Both routers run SPF on synchronized LSDB]  |
    |   [Compute shortest paths to all destinations]  |
```

---

## 17. BGP — Protocol Packets in ASCII

BGP runs over **TCP port 179**. It is a **path vector** protocol.

### BGP Message Header (19 bytes — fixed)

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   |                  Marker (16 bytes = all 1s)                   |
   |                  0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF           |
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Total Length (2)     |    Type (1)   |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Marker: 16 bytes of all-ones (0xFF * 16) — synchronization marker
Total Length: includes header + message body (min 19, max 4096 bytes)
Type: 1=OPEN, 2=UPDATE, 3=NOTIFICATION, 4=KEEPALIVE
```

### BGP OPEN Message (establishes BGP session)

```
   +----------------------------------------+
   |         BGP Header (19 bytes)           |
   +----------------------------------------+
   |  Version (1) |  My Autonomous System (2)|
   +----------------------------------------+
   |          Hold Time (2)                  |
   +----------------------------------------+
   |          BGP Identifier (4)             |
   +----------------------------------------+
   | Opt Parm Len (1) | Optional Params...  |
   +----------------------------------------+

Version: 4 (BGP-4)
My AS: The sender's AS number (16-bit for legacy, 32-bit via capability)
Hold Time: Proposed hold time in seconds (usually 90 or 180)
BGP Identifier: Router ID (must be unique in AS)
Optional Parameters: Capabilities (4-byte ASN, multiprotocol, etc.)
```

### BGP UPDATE Message (carries routing info)

```
   +----------------------------------------+
   |         BGP Header (19 bytes)           |
   +----------------------------------------+
   | Withdrawn Routes Length (2 bytes)       |
   +----------------------------------------+
   | Withdrawn Routes (variable)             |
   |   [Prefix Length (1)] [Prefix (0-4)]   |
   +----------------------------------------+
   | Total Path Attribute Length (2 bytes)   |
   +----------------------------------------+
   | Path Attributes (variable):            |
   |   ORIGIN (type=1, 1 byte):             |
   |     0=IGP, 1=EGP, 2=INCOMPLETE         |
   |   AS_PATH (type=2, variable):          |
   |     AS_SEQUENCE: [64512, 65001, 65002] |
   |   NEXT_HOP (type=3, 4 bytes):          |
   |     IP address of next hop             |
   |   LOCAL_PREF (type=5, 4 bytes):        |
   |     Preference (higher=better)         |
   |   COMMUNITY (type=8, variable):        |
   |     32-bit tags for policy             |
   +----------------------------------------+
   | Network Layer Reachability Info (NLRI)  |
   |   [Prefix Length (1)] [Prefix (0-4)]   |
   |   Example: 24, 192.168.1   (192.168.1.0/24)|
   +----------------------------------------+

Withdrawn Routes: Prefixes being withdrawn (no longer reachable)
Path Attributes: Metadata about the announced routes
NLRI: The actual prefixes being announced
```

### BGP Session — Full State Machine and Protocol Flow

```
STATE MACHINE:

[Idle]
  |-- TCP connect initiated
  v
[Connect]
  |-- TCP SYN sent
  |-- If TCP success:
  v
[OpenSent]
  |-- BGP OPEN sent
  |-- Waiting for OPEN from peer
  v
[OpenConfirm]
  |-- OPEN received and accepted
  |-- KEEPALIVE sent
  v
[Established]  ← BGP peering is UP
  |-- Can now exchange UPDATE messages


FULL BGP SESSION FLOW:

ROUTER A (AS 65001)                          ROUTER B (AS 65002)
10.0.0.1                                      10.0.0.2

    |        [TCP 3-Way Handshake]                |
    |------ TCP SYN (port 179) ----------------->|
    |<----- TCP SYN-ACK --------------------------|
    |------ TCP ACK ------------------------------>|
    |         [TCP session established]           |
    |                                             |
    |------ BGP OPEN --------------------------->|
    |  Version=4, My-AS=65001                     |
    |  Hold-Time=180, BGP-ID=10.0.0.1             |
    |                                             |
    |<----- BGP OPEN -----------------------------|
    |  Version=4, My-AS=65002                     |
    |  Hold-Time=180, BGP-ID=10.0.0.2             |
    |                                             |
    |<----- BGP KEEPALIVE ------------------------|
    |  (OPEN accepted, session confirmed)         |
    |------ BGP KEEPALIVE ----------------------->|
    |                                             |
    |   [BGP ESTABLISHED STATE]                   |
    |                                             |
    |------ BGP UPDATE -------------------------->|
    |  NLRI: 192.168.0.0/16                       |
    |  AS-PATH: [65001]                           |
    |  NEXT_HOP: 10.0.0.1                         |
    |  ORIGIN: IGP                                |
    |                                             |
    |<----- BGP UPDATE ---------------------------|
    |  NLRI: 203.0.113.0/24                       |
    |  AS-PATH: [65002]                           |
    |  NEXT_HOP: 10.0.0.2                         |
    |                                             |
    |   [Every ~60s — KEEPALIVE exchange]          |
    |<----- BGP KEEPALIVE ----------------------->|
    |------ BGP KEEPALIVE ----------------------->|
    |                                             |
    |   [If route is withdrawn:]                  |
    |------ BGP UPDATE (withdrawal) ------------>|
    |  Withdrawn: 192.168.0.0/16                  |
    |  NLRI: (empty)                              |
    |                                             |
    |   [If error occurs:]                        |
    |------ BGP NOTIFICATION ------------------->|
    |  Error Code + Subcode + Data               |
    |   [TCP session closed after NOTIFICATION]   |
```

---

## 18. Special and Reserved IP Ranges

### Well-Known Special Addresses

```
+---------------------+------------------+-----------------------------------+
| Range               | Purpose          | Notes                             |
+---------------------+------------------+-----------------------------------+
| 0.0.0.0/8           | "This" network   | Source in DHCP discovery          |
| 10.0.0.0/8          | Private (Class A)| RFC 1918                          |
| 100.64.0.0/10       | Shared Address   | RFC 6598 — ISP CGN                |
| 127.0.0.0/8         | Loopback         | Never leaves the host             |
| 127.0.0.1           | Localhost        | The classic loopback address      |
| 169.254.0.0/16      | Link-Local       | APIPA (auto-assigned if no DHCP)  |
| 172.16.0.0/12       | Private (Class B)| RFC 1918 (172.16.0.0-172.31.x.x) |
| 192.0.0.0/24        | IETF Protocol    | Reserved for IETF                 |
| 192.0.2.0/24        | TEST-NET-1       | Documentation examples            |
| 192.168.0.0/16      | Private (Class C)| RFC 1918                          |
| 198.18.0.0/15       | Benchmarking     | RFC 2544 network testing          |
| 198.51.100.0/24     | TEST-NET-2       | Documentation examples            |
| 203.0.113.0/24      | TEST-NET-3       | Documentation examples            |
| 224.0.0.0/4         | Multicast        | Class D                           |
| 224.0.0.1           | All-hosts mcast  | All devices on segment            |
| 224.0.0.2           | All-routers mcast| All routers on segment            |
| 224.0.0.5           | OSPF all-routers | All OSPF routers                  |
| 224.0.0.6           | OSPF DR/BDR      | OSPF Designated Routers           |
| 224.0.0.9           | RIPv2            | RIP v2 routers                    |
| 224.0.0.10          | EIGRP routers    | All EIGRP routers                 |
| 240.0.0.0/4         | Reserved/Class E | Future use                        |
| 255.255.255.255      | Broadcast        | Limited broadcast (all subnets)   |
+---------------------+------------------+-----------------------------------+
```

---

## 19. Private vs Public IP Space

### Private IP Ranges (RFC 1918)

```
These addresses are NOT routable on the public internet.
They are free to use internally in any organization.
NAT (Network Address Translation) is used to convert
private IPs to public IPs for internet access.

+------------------+--------------+-----------------+
| RFC 1918 Range   | CIDR Block   | # Addresses     |
+------------------+--------------+-----------------+
| 10.0.0.0         | /8           | 16,777,216      |
| 172.16.0.0       | /12          | 1,048,576       |
| 192.168.0.0      | /16          | 65,536          |
+------------------+--------------+-----------------+
Total private space: ~17.9 million addresses

NAT Topology:
┌─────────────────────────────────────┐
│         PRIVATE NETWORK             │
│                                     │
│  PC1: 192.168.1.100                 │
│  PC2: 192.168.1.101  ─────────────→ │ [ROUTER/NAT]
│  PC3: 192.168.1.102                 │ Public IP: 203.0.113.5
│                                     │
└─────────────────────────────────────┘
                                            │
                                            ↓
                                    [Public Internet]
                                  (Sees only 203.0.113.5)
```

---

## 20. C Implementation — Complete Router Engine

```c
/**
 * ip_router.c
 *
 * Complete Classful and Classless IP Router Engine in C.
 *
 * Demonstrates:
 * - IP address parsing and binary operations
 * - Classful routing (class detection + implicit masks)
 * - CIDR/Classless routing (explicit prefix + longest prefix match)
 * - Routing table management
 * - Subnet calculations
 * - Route aggregation detection
 *
 * Compile: gcc -O2 -Wall -Wextra -o ip_router ip_router.c
 * Run:     ./ip_router
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* ========================================================================
 * SECTION 1: FUNDAMENTAL IP ADDRESS TYPES AND UTILITIES
 * ======================================================================== */

/* IPv4 address is simply a 32-bit unsigned integer.
 * We use network byte order (big-endian) throughout.
 * uint32_t allows direct bitwise operations on the entire address. */
typedef uint32_t ipv4_t;

/* A route entry in the routing table */
typedef struct {
    ipv4_t  network;       /* Network address (host byte order) */
    ipv4_t  mask;          /* Subnet mask (host byte order) */
    uint8_t prefix_len;    /* Prefix length (0-32) */
    ipv4_t  next_hop;      /* Next-hop IP address */
    char    iface[16];     /* Outgoing interface name */
    uint32_t metric;       /* Route cost */
    uint8_t  admin_dist;   /* Administrative distance */
    char     source[8];    /* Route source: "C","S","R","O","B" */
} route_entry_t;

/* A routing table: array of route entries */
typedef struct {
    route_entry_t *entries;
    int            count;
    int            capacity;
} routing_table_t;

/* IP Class identification */
typedef enum {
    IP_CLASS_A,
    IP_CLASS_B,
    IP_CLASS_C,
    IP_CLASS_D,  /* Multicast */
    IP_CLASS_E,  /* Reserved */
    IP_CLASS_UNKNOWN
} ip_class_t;

/* -----------------------------------------------------------------------
 * Parse a dotted-decimal IP address string into uint32_t
 * Example: "192.168.1.1" → 0xC0A80101
 * ----------------------------------------------------------------------- */
ipv4_t ip_parse(const char *str) {
    unsigned int a, b, c, d;
    if (sscanf(str, "%u.%u.%u.%u", &a, &b, &c, &d) != 4) {
        fprintf(stderr, "Invalid IP address: %s\n", str);
        return 0;
    }
    /* Validate each octet is 0-255 */
    if (a > 255 || b > 255 || c > 255 || d > 255) {
        fprintf(stderr, "Octet out of range in: %s\n", str);
        return 0;
    }
    /* Combine 4 octets into single 32-bit value:
     * a occupies bits 31-24, b bits 23-16, c bits 15-8, d bits 7-0 */
    return (a << 24) | (b << 16) | (c << 8) | d;
}

/* -----------------------------------------------------------------------
 * Convert uint32_t IP back to dotted-decimal string
 * Result written to caller-provided buffer (at least 16 bytes)
 * ----------------------------------------------------------------------- */
void ip_to_str(ipv4_t ip, char *buf, size_t buf_size) {
    /* Extract each octet using bitmasks and shifts */
    snprintf(buf, buf_size, "%u.%u.%u.%u",
             (ip >> 24) & 0xFF,   /* Bits 31-24 → first octet */
             (ip >> 16) & 0xFF,   /* Bits 23-16 → second octet */
             (ip >>  8) & 0xFF,   /* Bits 15-8  → third octet */
             (ip      ) & 0xFF);  /* Bits 7-0   → fourth octet */
}

/* -----------------------------------------------------------------------
 * Convert prefix length to subnet mask
 * prefix_len=24 → 0xFFFFFF00 (255.255.255.0)
 *
 * Method: start with all-ones (0xFFFFFFFF),
 *         right-shift by (32 - prefix_len) bits
 * ----------------------------------------------------------------------- */
ipv4_t prefix_to_mask(uint8_t prefix_len) {
    if (prefix_len == 0)  return 0x00000000;
    if (prefix_len >= 32) return 0xFFFFFFFF;
    /* 0xFFFFFFFF << (32 - prefix_len) shifts zeros into the low bits */
    return (uint32_t)(0xFFFFFFFF << (32 - prefix_len));
}

/* -----------------------------------------------------------------------
 * Convert subnet mask to prefix length
 * 255.255.255.0 → 24
 *
 * Method: count the leading 1-bits (population count of leading ones)
 * ----------------------------------------------------------------------- */
uint8_t mask_to_prefix(ipv4_t mask) {
    uint8_t len = 0;
    /* Walk from bit 31 down to bit 0, count consecutive 1s from top */
    for (int i = 31; i >= 0; i--) {
        if (mask & (1u << i)) {
            len++;
        } else {
            break; /* First 0 bit — stop (masks must be contiguous) */
        }
    }
    return len;
}

/* -----------------------------------------------------------------------
 * Validate that a mask is a valid contiguous prefix mask
 * Returns true if mask is a run of 1s followed by run of 0s
 * ----------------------------------------------------------------------- */
bool mask_is_valid(ipv4_t mask) {
    /* Add 1 to host portion: valid mask+1 must be power of 2 */
    /* Equivalent: ~mask must have no transitions from 0 to 1 */
    ipv4_t inverted = ~mask;
    /* (inverted & (inverted + 1)) == 0 means inverted is all 1s
     * i.e., mask is a valid prefix mask */
    return (inverted & (inverted + 1)) == 0;
}

/* -----------------------------------------------------------------------
 * Compute network address: IP AND mask
 * ----------------------------------------------------------------------- */
ipv4_t ip_network(ipv4_t ip, ipv4_t mask) {
    return ip & mask;
}

/* -----------------------------------------------------------------------
 * Compute broadcast address: network OR (~mask)
 * ----------------------------------------------------------------------- */
ipv4_t ip_broadcast(ipv4_t network, ipv4_t mask) {
    return network | (~mask);
}

/* -----------------------------------------------------------------------
 * Count usable hosts: 2^(host_bits) - 2
 * (subtract network address and broadcast address)
 * ----------------------------------------------------------------------- */
uint32_t ip_host_count(uint8_t prefix_len) {
    if (prefix_len >= 32) return 0;   /* /32: single host */
    if (prefix_len == 31) return 2;   /* /31: RFC 3021 P2P links */
    uint32_t host_bits = 32 - prefix_len;
    /* 2^host_bits could overflow uint32 for prefix_len=0 */
    if (host_bits >= 32) return 0xFFFFFFFE; /* Special case /0 */
    return (1u << host_bits) - 2;
}

/* -----------------------------------------------------------------------
 * Print IP address details for educational output
 * ----------------------------------------------------------------------- */
void ip_print_details(ipv4_t ip, uint8_t prefix_len) {
    char buf[20];
    ipv4_t mask      = prefix_to_mask(prefix_len);
    ipv4_t network   = ip_network(ip, mask);
    ipv4_t broadcast = ip_broadcast(network, mask);
    ipv4_t first     = network + 1;
    ipv4_t last      = broadcast - 1;

    ip_to_str(ip,        buf, sizeof(buf)); printf("  IP Address:      %s\n", buf);
    ip_to_str(mask,      buf, sizeof(buf)); printf("  Subnet Mask:     %s (/%u)\n", buf, prefix_len);
    ip_to_str(network,   buf, sizeof(buf)); printf("  Network:         %s\n", buf);
    ip_to_str(broadcast, buf, sizeof(buf)); printf("  Broadcast:       %s\n", buf);
    ip_to_str(first,     buf, sizeof(buf)); printf("  First Host:      %s\n", buf);
    ip_to_str(last,      buf, sizeof(buf)); printf("  Last Host:       %s\n", buf);
    printf("  Usable Hosts:    %u\n", ip_host_count(prefix_len));
}

/* ========================================================================
 * SECTION 2: CLASSFUL ROUTING
 * ======================================================================== */

/* -----------------------------------------------------------------------
 * Determine IP class by examining high-order bits of the address.
 * This is exactly what a classful router does automatically.
 * ----------------------------------------------------------------------- */
ip_class_t ip_get_class(ipv4_t ip) {
    uint8_t first_octet = (ip >> 24) & 0xFF;

    /* Class A: first bit is 0  → range 0-127 */
    if ((first_octet & 0x80) == 0x00) return IP_CLASS_A;

    /* Class B: first two bits are 10 → range 128-191 */
    if ((first_octet & 0xC0) == 0x80) return IP_CLASS_B;

    /* Class C: first three bits are 110 → range 192-223 */
    if ((first_octet & 0xE0) == 0xC0) return IP_CLASS_C;

    /* Class D: first four bits are 1110 → range 224-239 */
    if ((first_octet & 0xF0) == 0xE0) return IP_CLASS_D;

    /* Class E: first four bits are 1111 → range 240-255 */
    return IP_CLASS_E;
}

/* -----------------------------------------------------------------------
 * Get classful default mask for an IP address.
 * This is what RIPv1 and other classful protocols use.
 * ----------------------------------------------------------------------- */
ipv4_t ip_classful_mask(ipv4_t ip) {
    switch (ip_get_class(ip)) {
        case IP_CLASS_A: return 0xFF000000;       /* /8  = 255.0.0.0     */
        case IP_CLASS_B: return 0xFFFF0000;       /* /16 = 255.255.0.0   */
        case IP_CLASS_C: return 0xFFFFFF00;       /* /24 = 255.255.255.0 */
        default:         return 0x00000000;       /* D/E: no classful mask */
    }
}

/* -----------------------------------------------------------------------
 * Get classful network address for an IP (as classful router would compute)
 * ----------------------------------------------------------------------- */
ipv4_t ip_classful_network(ipv4_t ip) {
    return ip & ip_classful_mask(ip);
}

const char *ip_class_name(ip_class_t cls) {
    switch (cls) {
        case IP_CLASS_A: return "Class A (/8)";
        case IP_CLASS_B: return "Class B (/16)";
        case IP_CLASS_C: return "Class C (/24)";
        case IP_CLASS_D: return "Class D (Multicast)";
        case IP_CLASS_E: return "Class E (Reserved)";
        default:         return "Unknown";
    }
}

/* -----------------------------------------------------------------------
 * Classful routing lookup.
 * Router ignores prefix in routing table, uses classful mask instead.
 * ----------------------------------------------------------------------- */
const route_entry_t *classful_lookup(
    const routing_table_t *table,
    ipv4_t dst_ip)
{
    /* In classful routing: derive network from IP's class, then match */
    ipv4_t classful_net = ip_classful_network(dst_ip);

    for (int i = 0; i < table->count; i++) {
        const route_entry_t *r = &table->entries[i];
        /* Apply classful mask of the route's network to destination */
        ipv4_t classful_dst_net = ip_classful_network(dst_ip);
        ipv4_t route_classful_net = ip_classful_network(r->network);

        if (classful_dst_net == route_classful_net) {
            return r;
        }
    }
    return NULL; /* No classful match found */
}

/* ========================================================================
 * SECTION 3: CLASSLESS ROUTING — LONGEST PREFIX MATCH
 * ======================================================================== */

/* -----------------------------------------------------------------------
 * Initialize a routing table
 * ----------------------------------------------------------------------- */
void rt_init(routing_table_t *rt) {
    rt->capacity = 64;
    rt->count    = 0;
    rt->entries  = calloc(rt->capacity, sizeof(route_entry_t));
    if (!rt->entries) {
        perror("rt_init calloc");
        exit(EXIT_FAILURE);
    }
}

/* -----------------------------------------------------------------------
 * Add a route entry to the routing table
 * ----------------------------------------------------------------------- */
void rt_add(routing_table_t *rt,
            const char *network_str,
            uint8_t     prefix_len,
            const char *next_hop_str,
            const char *iface,
            uint32_t    metric,
            uint8_t     admin_dist,
            const char *source)
{
    if (rt->count >= rt->capacity) {
        rt->capacity *= 2;
        rt->entries = realloc(rt->entries,
                              rt->capacity * sizeof(route_entry_t));
        if (!rt->entries) { perror("rt_add realloc"); exit(EXIT_FAILURE); }
    }

    route_entry_t *e = &rt->entries[rt->count++];
    ipv4_t raw_ip  = ip_parse(network_str);
    ipv4_t mask    = prefix_to_mask(prefix_len);

    e->network    = ip_network(raw_ip, mask); /* Ensure clean network addr */
    e->mask       = mask;
    e->prefix_len = prefix_len;
    e->next_hop   = next_hop_str ? ip_parse(next_hop_str) : 0;
    e->metric     = metric;
    e->admin_dist = admin_dist;

    strncpy(e->iface,  iface  ? iface  : "lo",  sizeof(e->iface) - 1);
    strncpy(e->source, source ? source : "?",   sizeof(e->source) - 1);
    e->iface[sizeof(e->iface)-1]   = '\0';
    e->source[sizeof(e->source)-1] = '\0';
}

/* -----------------------------------------------------------------------
 * Classless Longest Prefix Match (LPM) lookup
 *
 * Algorithm:
 * 1. For each route entry, check: (dst_ip AND route.mask) == route.network
 * 2. Among all matching entries, pick the one with LARGEST prefix_len
 * 3. Ties broken by lowest admin_distance, then lowest metric
 *
 * Time complexity: O(n) for linear scan
 * Production systems use a Trie: O(32) worst case for IPv4
 * ----------------------------------------------------------------------- */
const route_entry_t *lpm_lookup(
    const routing_table_t *rt,
    ipv4_t dst_ip)
{
    const route_entry_t *best = NULL;
    int best_prefix = -1;

    for (int i = 0; i < rt->count; i++) {
        const route_entry_t *r = &rt->entries[i];

        /* Core LPM check: does this route cover the destination? */
        /* Apply route's mask to destination, compare to route's network */
        ipv4_t masked = dst_ip & r->mask;
        if (masked == r->network) {
            /* This route MATCHES. Is it more specific than current best? */
            if (r->prefix_len > best_prefix ||
                (r->prefix_len == best_prefix && best != NULL &&
                 r->admin_dist < best->admin_dist) ||
                (r->prefix_len == best_prefix && best != NULL &&
                 r->admin_dist == best->admin_dist &&
                 r->metric < best->metric))
            {
                best = r;
                best_prefix = r->prefix_len;
            }
        }
    }

    return best;
}

/* -----------------------------------------------------------------------
 * Print routing table in a formatted view
 * ----------------------------------------------------------------------- */
void rt_print(const routing_table_t *rt) {
    char net_buf[20], mask_buf[20], nh_buf[20];

    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════════════════╗\n");
    printf("║                          ROUTING TABLE                                  ║\n");
    printf("╠══════════════╦════════╦═════════════════╦══════════╦════════╦══════════╣\n");
    printf("║ Source       ║ Prefix ║ Network          ║ Next Hop ║ Iface  ║ Metric   ║\n");
    printf("╠══════════════╬════════╬═════════════════╬══════════╬════════╬══════════╣\n");

    for (int i = 0; i < rt->count; i++) {
        const route_entry_t *r = &rt->entries[i];
        ip_to_str(r->network,  net_buf,  sizeof(net_buf));
        ip_to_str(r->next_hop, nh_buf,   sizeof(nh_buf));

        printf("║ %-12s ║ /%-6u ║ %-15s   ║ %-8s ║ %-6s ║ %-8u ║\n",
               r->source, r->prefix_len, net_buf,
               r->next_hop ? nh_buf : "directly",
               r->iface, r->metric);
    }
    printf("╚══════════════╩════════╩═════════════════╩══════════╩════════╩══════════╝\n");
}

/* ========================================================================
 * SECTION 4: SUBNET CALCULATION ENGINE
 * ======================================================================== */

/* -----------------------------------------------------------------------
 * Subnet a given network into smaller subnets
 *
 * Parameters:
 *   network      - base network address
 *   orig_prefix  - original prefix length
 *   new_prefix   - desired prefix length for subnets (must be > orig_prefix)
 *
 * Prints all resulting subnets
 * ----------------------------------------------------------------------- */
void subnet_enumerate(ipv4_t network, uint8_t orig_prefix, uint8_t new_prefix) {
    if (new_prefix <= orig_prefix) {
        fprintf(stderr, "New prefix must be longer than original\n");
        return;
    }
    if (new_prefix > 32) {
        fprintf(stderr, "Prefix length cannot exceed 32\n");
        return;
    }

    uint8_t  borrowed_bits  = new_prefix - orig_prefix;
    uint32_t num_subnets    = 1u << borrowed_bits;  /* 2^borrowed_bits */
    ipv4_t   new_mask       = prefix_to_mask(new_prefix);
    ipv4_t   old_mask       = prefix_to_mask(orig_prefix);
    /* Block size = distance between consecutive subnets */
    uint32_t block_size     = 1u << (32 - new_prefix);
    /* Clean network: apply original mask to ensure clean start */
    ipv4_t   base_network   = network & old_mask;

    char buf[20];
    printf("\nSubnetting "); ip_to_str(base_network, buf, sizeof(buf));
    printf("%s/%u into /%u subnets:\n", buf, orig_prefix, new_prefix);
    printf("  Borrowed bits: %u, Subnets: %u, Hosts/subnet: %u\n\n",
           borrowed_bits, num_subnets, ip_host_count(new_prefix));

    printf("  %-5s %-20s %-18s %-18s %-18s\n",
           "No.", "Subnet", "First Host", "Last Host", "Broadcast");
    printf("  %s\n", "----------------------------------------------------------------");

    for (uint32_t i = 0; i < num_subnets; i++) {
        ipv4_t subnet_net  = base_network + (i * block_size);
        ipv4_t subnet_bc   = ip_broadcast(subnet_net, new_mask);
        ipv4_t first_host  = subnet_net + 1;
        ipv4_t last_host   = subnet_bc - 1;

        char sn[20], fh[20], lh[20], bc[20];
        ip_to_str(subnet_net, sn, sizeof(sn));
        ip_to_str(first_host, fh, sizeof(fh));
        ip_to_str(last_host,  lh, sizeof(lh));
        ip_to_str(subnet_bc,  bc, sizeof(bc));

        printf("  %-5u %-15s/%-3u %-18s %-18s %-18s\n",
               i, sn, new_prefix, fh, lh, bc);
    }
}

/* -----------------------------------------------------------------------
 * Check if a set of networks can be aggregated into a single supernet
 * and find the common prefix
 * ----------------------------------------------------------------------- */
uint8_t find_common_prefix(ipv4_t *networks, int count) {
    if (count == 0) return 0;
    if (count == 1) return 32;

    /* XOR all networks together — bits that differ will be 1 */
    /* Find the highest bit that differs across any pair */
    uint32_t differing_bits = 0;
    for (int i = 1; i < count; i++) {
        differing_bits |= (networks[i] ^ networks[0]);
    }
    for (int i = 1; i < count; i++) {
        for (int j = i + 1; j < count; j++) {
            differing_bits |= (networks[i] ^ networks[j]);
        }
    }

    /* Count leading zeros in differing_bits = common prefix length */
    if (differing_bits == 0) return 32; /* All identical */

    uint8_t common = 0;
    for (int bit = 31; bit >= 0; bit--) {
        if (differing_bits & (1u << bit)) break;
        common++;
    }
    return common;
}

/* ========================================================================
 * SECTION 5: UTILITY — BINARY REPRESENTATION
 * ======================================================================== */

/* Print an IP address in binary, with separator at byte boundaries */
void ip_print_binary(ipv4_t ip) {
    for (int i = 31; i >= 0; i--) {
        printf("%c", (ip & (1u << i)) ? '1' : '0');
        if (i > 0 && i % 8 == 0) printf(".");
    }
}

/* Print IP with mask showing network/host boundary */
void ip_print_with_boundary(ipv4_t ip, uint8_t prefix_len) {
    printf("  Binary: ");
    for (int i = 31; i >= 0; i--) {
        if (i == (31 - prefix_len)) printf("|");
        printf("%c", (ip & (1u << i)) ? '1' : '0');
        if (i > 0 && i % 8 == 0 && i != (32 - prefix_len)) printf(".");
    }
    printf("\n");
    printf("          ");
    for (int i = 0; i < prefix_len; i++) printf("N");
    printf("|");
    for (int i = prefix_len; i < 32; i++) printf("H");
    printf("  (N=network, H=host)\n");
}

/* Check if IP is in a given network */
bool ip_in_network(ipv4_t ip, ipv4_t network, uint8_t prefix_len) {
    ipv4_t mask = prefix_to_mask(prefix_len);
    return (ip & mask) == (network & mask);
}

/* ========================================================================
 * SECTION 6: MAIN DEMONSTRATION
 * ======================================================================== */

int main(void) {
    char buf[20], buf2[20], buf3[20];

    printf("╔══════════════════════════════════════════════════════════════════════════╗\n");
    printf("║         CLASSFUL vs CLASSLESS IP ROUTING — C DEMONSTRATION              ║\n");
    printf("╚══════════════════════════════════════════════════════════════════════════╝\n\n");

    /* ------------------------------------------------------------------ */
    printf("══════════════════════════════════════════════════════════════════\n");
    printf("PART 1: IP ADDRESS ANALYSIS — CLASSFUL CLASS DETECTION\n");
    printf("══════════════════════════════════════════════════════════════════\n\n");

    const char *test_ips[] = {
        "10.5.3.2",
        "172.16.50.4",
        "192.168.1.100",
        "224.0.0.5",
        "240.0.0.1"
    };

    for (int i = 0; i < 5; i++) {
        ipv4_t ip = ip_parse(test_ips[i]);
        ip_class_t cls = ip_get_class(ip);
        ipv4_t classful_net = ip_classful_network(ip);

        ip_to_str(ip, buf, sizeof(buf));
        ip_to_str(classful_net, buf2, sizeof(buf2));

        printf("IP: %-18s → %s → Classful Network: %s\n",
               buf, ip_class_name(cls), buf2);
        ip_print_binary(ip); printf("  (binary)\n");
    }

    /* ------------------------------------------------------------------ */
    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("PART 2: SUBNET CALCULATIONS (CIDR)\n");
    printf("══════════════════════════════════════════════════════════════════\n\n");

    ipv4_t test_ip = ip_parse("192.168.10.100");
    printf("Detailed analysis of 192.168.10.100/24:\n");
    ip_print_details(test_ip, 24);
    printf("\nBinary with network/host boundary:\n");
    ip_print_with_boundary(test_ip, 24);

    printf("\nDetailed analysis of 10.128.64.200/18:\n");
    ip_print_details(ip_parse("10.128.64.200"), 18);

    /* ------------------------------------------------------------------ */
    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("PART 3: SUBNETTING — 192.168.1.0/24 into /26 subnets\n");
    printf("══════════════════════════════════════════════════════════════════\n");
    subnet_enumerate(ip_parse("192.168.1.0"), 24, 26);

    /* ------------------------------------------------------------------ */
    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("PART 4: ROUTE AGGREGATION (SUPERNETTING)\n");
    printf("══════════════════════════════════════════════════════════════════\n\n");

    ipv4_t nets_to_agg[] = {
        ip_parse("192.168.0.0"),
        ip_parse("192.168.1.0"),
        ip_parse("192.168.2.0"),
        ip_parse("192.168.3.0"),
    };

    printf("Networks to aggregate:\n");
    for (int i = 0; i < 4; i++) {
        ip_to_str(nets_to_agg[i], buf, sizeof(buf));
        printf("  %s/24  binary: ", buf);
        ip_print_binary(nets_to_agg[i]);
        printf("\n");
    }

    uint8_t common = find_common_prefix(nets_to_agg, 4);
    ipv4_t supernet = nets_to_agg[0] & prefix_to_mask(common);
    ip_to_str(supernet, buf, sizeof(buf));
    printf("\nCommon prefix: %u bits → Supernet: %s/%u\n", common, buf, common);
    printf("Savings: 4 entries → 1 entry (%u%% reduction)\n", 75);

    /* ------------------------------------------------------------------ */
    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("PART 5: CLASSLESS ROUTING TABLE + LONGEST PREFIX MATCH\n");
    printf("══════════════════════════════════════════════════════════════════\n");

    routing_table_t rt;
    rt_init(&rt);

    /* Build routing table with various prefix lengths */
    rt_add(&rt, "0.0.0.0",      0,  "172.16.0.1", "eth2", 1,  1,   "S*");  /* default */
    rt_add(&rt, "10.0.0.0",     8,  "10.0.0.2",   "eth1", 110, 110, "O");  /* OSPF */
    rt_add(&rt, "10.20.0.0",    16, "10.0.0.3",   "eth1", 20, 110, "O");   /* more specific */
    rt_add(&rt, "10.20.50.0",   24, "10.0.0.4",   "eth0", 10, 110, "O");   /* even more specific */
    rt_add(&rt, "10.20.50.128", 25, "10.0.0.5",   "eth0", 5,  110, "O");   /* most specific */
    rt_add(&rt, "192.168.0.0",  22, "10.0.0.6",   "eth1", 1,  1,   "S");   /* supernet */
    rt_add(&rt, "192.168.1.0",  24, "10.0.0.7",   "eth0", 1,  0,   "C");   /* connected */

    rt_print(&rt);

    /* Test LPM lookups */
    printf("\nLongest Prefix Match Lookups:\n");
    const char *lookup_targets[] = {
        "10.20.50.200",   /* Should match /25 */
        "10.20.50.100",   /* Should match /24 (not /25) */
        "10.20.1.1",      /* Should match /16 */
        "10.5.0.1",       /* Should match /8 */
        "192.168.1.50",   /* Should match connected /24 */
        "192.168.2.50",   /* Should match supernet /22 */
        "8.8.8.8",        /* Should match default /0 */
    };

    printf("\n  %-20s %-12s %-15s %s\n",
           "Destination", "Match (/X)", "Next Hop", "Interface");
    printf("  %s\n", "--------------------------------------------------------------");

    for (int i = 0; i < 7; i++) {
        ipv4_t dst = ip_parse(lookup_targets[i]);
        const route_entry_t *match = lpm_lookup(&rt, dst);

        if (match) {
            ip_to_str(match->next_hop, buf2, sizeof(buf2));
            printf("  %-20s → /%2u %-10s %-15s %s\n",
                   lookup_targets[i],
                   match->prefix_len,
                   match->source,
                   match->next_hop ? buf2 : "directly",
                   match->iface);
        } else {
            printf("  %-20s → NO ROUTE (unreachable)\n", lookup_targets[i]);
        }
    }

    /* ------------------------------------------------------------------ */
    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("PART 6: CLASSFUL vs CLASSLESS COMPARISON\n");
    printf("══════════════════════════════════════════════════════════════════\n\n");

    ipv4_t demo_ip = ip_parse("10.20.50.200");
    ip_to_str(demo_ip, buf, sizeof(buf));
    printf("Destination IP: %s\n\n", buf);

    /* Classful lookup (ignores subnet boundaries) */
    const route_entry_t *cl_match = classful_lookup(&rt, demo_ip);
    printf("CLASSFUL router decision:\n");
    printf("  First octet = 10 → Class A → apply /8 mask\n");
    if (cl_match) {
        ip_to_str(cl_match->network, buf2, sizeof(buf2));
        ip_to_str(cl_match->next_hop, buf3, sizeof(buf3));
        printf("  Matched: %s/%u → next-hop: %s via %s\n",
               buf2, cl_match->prefix_len, buf3, cl_match->iface);
    } else {
        printf("  No match — routing failure!\n");
    }

    /* Classless (LPM) lookup */
    const route_entry_t *lpm_match = lpm_lookup(&rt, demo_ip);
    printf("\nCLASSLESS router decision (LPM):\n");
    if (lpm_match) {
        ip_to_str(lpm_match->network, buf2, sizeof(buf2));
        ip_to_str(lpm_match->next_hop, buf3, sizeof(buf3));
        printf("  Best match: %s/%u → next-hop: %s via %s\n",
               buf2, lpm_match->prefix_len, buf3, lpm_match->iface);
        printf("  ✓ More specific! VLSM and CIDR working correctly.\n");
    }

    /* Cleanup */
    free(rt.entries);

    printf("\n══════════════════════════════════════════════════════════════════\n");
    printf("DEMO COMPLETE\n");
    printf("══════════════════════════════════════════════════════════════════\n");

    return EXIT_SUCCESS;
}
```

---

## 21. Rust Implementation — Complete Router Engine

```rust
//! ip_router.rs — Classful and Classless IP Routing Engine in Rust
//!
//! Demonstrates:
//! - Zero-cost abstractions for IP operations
//! - Type-safe routing with newtype patterns
//! - Classful class detection and implicit masking
//! - CIDR prefix matching and longest prefix match
//! - Routing table management with iterators
//! - Subnet and supernet calculations
//!
//! Compile: rustc -O ip_router.rs -o ip_router
//! Run:     ./ip_router
//!
//! Or with Cargo:
//!   cargo new ip_router && copy to src/main.rs
//!   cargo run --release

use std::fmt;
use std::str::FromStr;

// =============================================================================
// SECTION 1: CORE IP ADDRESS TYPE
// =============================================================================

/// IPv4 address stored as a 32-bit unsigned integer (host byte order).
/// Newtype wrapper provides type safety — prevents mixing raw u32 with IPs.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Ipv4Addr(u32);

impl Ipv4Addr {
    /// Create from raw 32-bit value
    pub const fn from_u32(val: u32) -> Self {
        Self(val)
    }

    /// Create from four octets
    pub const fn new(a: u8, b: u8, c: u8, d: u8) -> Self {
        Self(((a as u32) << 24) | ((b as u32) << 16) | ((c as u32) << 8) | (d as u32))
    }

    /// Get raw u32 value
    pub const fn as_u32(self) -> u32 {
        self.0
    }

    /// Extract individual octets
    pub fn octets(self) -> [u8; 4] {
        [
            ((self.0 >> 24) & 0xFF) as u8,
            ((self.0 >> 16) & 0xFF) as u8,
            ((self.0 >>  8) & 0xFF) as u8,
            ((self.0      ) & 0xFF) as u8,
        ]
    }

    /// Bitwise AND (used for computing network address)
    pub fn bitand(self, other: Ipv4Addr) -> Ipv4Addr {
        Ipv4Addr(self.0 & other.0)
    }

    /// Bitwise OR (used for computing broadcast address)
    pub fn bitor(self, other: Ipv4Addr) -> Ipv4Addr {
        Ipv4Addr(self.0 | other.0)
    }

    /// Bitwise NOT (used for computing wildcard/inverse mask)
    pub fn bitnot(self) -> Ipv4Addr {
        Ipv4Addr(!self.0)
    }
}

/// Implement Display so we can use format!("{}", ip)
impl fmt::Display for Ipv4Addr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let o = self.octets();
        write!(f, "{}.{}.{}.{}", o[0], o[1], o[2], o[3])
    }
}

/// Debug output shows both decimal and binary
impl fmt::Debug for Ipv4Addr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let o = self.octets();
        write!(f, "{}.{}.{}.{} ({:08b}.{:08b}.{:08b}.{:08b})",
               o[0], o[1], o[2], o[3],
               o[0], o[1], o[2], o[3])
    }
}

/// Parse "192.168.1.1" → Ipv4Addr
impl FromStr for Ipv4Addr {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let parts: Vec<&str> = s.split('.').collect();
        if parts.len() != 4 {
            return Err(format!("Expected 4 octets, got {}", parts.len()));
        }
        let mut octets = [0u8; 4];
        for (i, part) in parts.iter().enumerate() {
            octets[i] = part.parse::<u8>()
                .map_err(|e| format!("Invalid octet '{}': {}", part, e))?;
        }
        Ok(Ipv4Addr::new(octets[0], octets[1], octets[2], octets[3]))
    }
}

// =============================================================================
// SECTION 2: SUBNET MASK AND PREFIX
// =============================================================================

/// A CIDR prefix: IP address + prefix length
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct IpPrefix {
    pub network:    Ipv4Addr,  // Network address (host bits zeroed)
    pub prefix_len: u8,        // Prefix length (0..=32)
}

impl IpPrefix {
    /// Create a new IpPrefix, automatically zeroing host bits
    pub fn new(ip: Ipv4Addr, prefix_len: u8) -> Self {
        assert!(prefix_len <= 32, "Prefix length must be 0-32");
        let mask    = SubnetMask::from_prefix_len(prefix_len);
        let network = ip.bitand(mask.as_ip());
        Self { network, prefix_len }
    }

    /// Parse CIDR notation: "192.168.1.0/24"
    pub fn parse(s: &str) -> Result<Self, String> {
        let parts: Vec<&str> = s.split('/').collect();
        if parts.len() != 2 {
            return Err(format!("Expected CIDR notation (x.x.x.x/n), got: {}", s));
        }
        let ip: Ipv4Addr = parts[0].parse()?;
        let prefix_len: u8 = parts[1].parse::<u8>()
            .map_err(|e| format!("Invalid prefix length: {}", e))?;
        Ok(Self::new(ip, prefix_len))
    }

    /// Get the subnet mask
    pub fn mask(self) -> SubnetMask {
        SubnetMask::from_prefix_len(self.prefix_len)
    }

    /// Get broadcast address
    pub fn broadcast(self) -> Ipv4Addr {
        let wildcard = self.mask().as_ip().bitnot();
        self.network.bitor(wildcard)
    }

    /// Get first usable host address
    pub fn first_host(self) -> Ipv4Addr {
        if self.prefix_len >= 31 {
            return self.network; // /31 and /32: no traditional host calc
        }
        Ipv4Addr(self.network.0 + 1)
    }

    /// Get last usable host address
    pub fn last_host(self) -> Ipv4Addr {
        if self.prefix_len >= 31 {
            return self.broadcast();
        }
        Ipv4Addr(self.broadcast().0 - 1)
    }

    /// Number of usable hosts
    pub fn host_count(self) -> u64 {
        match self.prefix_len {
            32 => 1,
            31 => 2,  // RFC 3021
            n  => (1u64 << (32 - n)) - 2,
        }
    }

    /// Check if an IP address belongs to this prefix
    pub fn contains(self, ip: Ipv4Addr) -> bool {
        let mask = self.mask().as_ip();
        ip.bitand(mask) == self.network
    }

    /// Check if this prefix is a supernet of another prefix
    pub fn is_supernet_of(self, other: IpPrefix) -> bool {
        self.prefix_len < other.prefix_len && self.contains(other.network)
    }
}

impl fmt::Display for IpPrefix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}/{}", self.network, self.prefix_len)
    }
}

impl fmt::Debug for IpPrefix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}/{}", self.network, self.prefix_len)
    }
}

/// Subnet mask wrapper
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct SubnetMask(u32);

impl SubnetMask {
    /// Build mask from prefix length: /24 → 0xFFFFFF00
    pub fn from_prefix_len(len: u8) -> Self {
        if len == 0  { return Self(0x00000000); }
        if len >= 32 { return Self(0xFFFFFFFF); }
        // Shift all-ones right by (32-len) to create mask
        Self(0xFFFFFFFF_u32 << (32 - len))
    }

    /// Convert to Ipv4Addr for bitwise operations
    pub fn as_ip(self) -> Ipv4Addr {
        Ipv4Addr(self.0)
    }

    /// Convert mask to prefix length
    pub fn to_prefix_len(self) -> u8 {
        // Count leading ones = prefix length
        self.0.leading_ones() as u8
    }

    /// Validate that mask is a valid contiguous prefix mask
    /// A valid mask has form: 1...10...0
    pub fn is_valid(self) -> bool {
        let inv = !self.0;
        // Wildcard (inverse of mask) must be of form 0...01...1
        // i.e., (inv & (inv + 1)) == 0
        inv.wrapping_add(1) & inv == 0
    }
}

impl fmt::Display for SubnetMask {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", Ipv4Addr(self.0))
    }
}

// =============================================================================
// SECTION 3: CLASSFUL IP ADDRESSING
// =============================================================================

/// IP address class as per RFC 791 (1981)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IpClass {
    A,  // First bit: 0    → 0.x.x.x   to 127.x.x.x
    B,  // First bits: 10  → 128.x.x.x to 191.x.x.x
    C,  // First bits: 110 → 192.x.x.x to 223.x.x.x
    D,  // Multicast  → 224.x.x.x to 239.x.x.x
    E,  // Reserved   → 240.x.x.x to 255.x.x.x
}

impl IpClass {
    /// Determine the class of an IP address by examining high-order bits.
    /// This is the core classful routing algorithm.
    pub fn of(ip: Ipv4Addr) -> Self {
        let first = ((ip.as_u32() >> 24) & 0xFF) as u8;
        match first {
            // 0xxx xxxx — bit 7 is 0 → Class A
            0..=127 if first & 0x80 == 0x00 => IpClass::A,
            // 10xx xxxx — bits 7-6 are 10 → Class B
            128..=191 if first & 0xC0 == 0x80 => IpClass::B,
            // 110x xxxx — bits 7-5 are 110 → Class C
            192..=223 if first & 0xE0 == 0xC0 => IpClass::C,
            // 1110 xxxx — bits 7-4 are 1110 → Class D
            224..=239 if first & 0xF0 == 0xE0 => IpClass::D,
            // 1111 xxxx — anything else → Class E
            _ => IpClass::E,
        }
    }

    /// Default subnet mask for classful routing
    pub fn default_mask(self) -> Option<SubnetMask> {
        match self {
            IpClass::A => Some(SubnetMask::from_prefix_len(8)),   // /8
            IpClass::B => Some(SubnetMask::from_prefix_len(16)),  // /16
            IpClass::C => Some(SubnetMask::from_prefix_len(24)),  // /24
            IpClass::D | IpClass::E => None,  // No classful mask for multicast/reserved
        }
    }

    /// Default prefix length for classful routing
    pub fn default_prefix_len(self) -> Option<u8> {
        match self {
            IpClass::A => Some(8),
            IpClass::B => Some(16),
            IpClass::C => Some(24),
            _          => None,
        }
    }

    /// Get classful network for an IP (as a classful router would)
    pub fn classful_network(ip: Ipv4Addr) -> Option<IpPrefix> {
        let cls = IpClass::of(ip);
        cls.default_prefix_len()
           .map(|len| IpPrefix::new(ip, len))
    }

    pub fn description(self) -> &'static str {
        match self {
            IpClass::A => "Class A (/8)  — first bit 0",
            IpClass::B => "Class B (/16) — first two bits 10",
            IpClass::C => "Class C (/24) — first three bits 110",
            IpClass::D => "Class D       — Multicast (1110xxxx)",
            IpClass::E => "Class E       — Reserved (1111xxxx)",
        }
    }
}

impl fmt::Display for IpClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.description())
    }
}

// =============================================================================
// SECTION 4: ROUTING TABLE AND LONGEST PREFIX MATCH
// =============================================================================

/// Source of a routing table entry
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RouteSource {
    Connected,   // Directly connected (admin distance 0)
    Static,      // Manually configured (admin distance 1)
    Rip,         // Learned from RIP (admin distance 120)
    Ospf,        // Learned from OSPF (admin distance 110)
    Bgp,         // Learned from BGP (admin distance 20/200)
    Eigrp,       // Learned from EIGRP (admin distance 90)
    Default,     // Default static route (S*)
}

impl RouteSource {
    pub fn admin_distance(self) -> u8 {
        match self {
            RouteSource::Connected => 0,
            RouteSource::Static | RouteSource::Default => 1,
            RouteSource::Bgp    => 20,
            RouteSource::Eigrp  => 90,
            RouteSource::Ospf   => 110,
            RouteSource::Rip    => 120,
        }
    }

    pub fn symbol(self) -> &'static str {
        match self {
            RouteSource::Connected => "C",
            RouteSource::Static    => "S",
            RouteSource::Default   => "S*",
            RouteSource::Rip       => "R",
            RouteSource::Ospf      => "O",
            RouteSource::Bgp       => "B",
            RouteSource::Eigrp     => "D",
        }
    }
}

/// A single entry in the routing table
#[derive(Debug, Clone)]
pub struct RouteEntry {
    pub prefix:    IpPrefix,           // Destination network + mask
    pub next_hop:  Option<Ipv4Addr>,   // None = directly connected
    pub interface: String,             // Output interface
    pub metric:    u32,                // Route cost
    pub source:    RouteSource,        // How route was learned
}

impl RouteEntry {
    pub fn new(
        prefix: IpPrefix,
        next_hop: Option<Ipv4Addr>,
        interface: &str,
        metric: u32,
        source: RouteSource,
    ) -> Self {
        Self {
            prefix,
            next_hop,
            interface: interface.to_owned(),
            metric,
            source,
        }
    }
}

/// The routing table: a collection of route entries
pub struct RoutingTable {
    entries: Vec<RouteEntry>,
}

impl RoutingTable {
    pub fn new() -> Self {
        Self { entries: Vec::new() }
    }

    /// Add a route entry
    pub fn add(&mut self, entry: RouteEntry) {
        self.entries.push(entry);
    }

    /// Convenience: add from CIDR string
    pub fn add_route(
        &mut self,
        cidr: &str,
        next_hop: Option<&str>,
        interface: &str,
        metric: u32,
        source: RouteSource,
    ) {
        let prefix   = IpPrefix::parse(cidr).expect("Invalid CIDR");
        let next_hop = next_hop.map(|s| s.parse().expect("Invalid next-hop IP"));
        self.add(RouteEntry::new(prefix, next_hop, interface, metric, source));
    }

    /// Longest Prefix Match lookup — the heart of classless routing.
    ///
    /// Algorithm:
    /// 1. Filter entries where (dst AND mask) == network (route matches dst)
    /// 2. Among matches, find maximum prefix_len (most specific)
    /// 3. Ties: prefer lower admin_distance, then lower metric
    ///
    /// Returns None if no match (including default route /0).
    pub fn lpm_lookup(&self, dst: Ipv4Addr) -> Option<&RouteEntry> {
        self.entries
            .iter()
            .filter(|r| r.prefix.contains(dst))
            .max_by(|a, b| {
                // Primary: longer prefix wins (more specific)
                a.prefix.prefix_len.cmp(&b.prefix.prefix_len)
                    // Secondary: lower admin distance wins
                    .then_with(|| {
                        b.source.admin_distance()
                         .cmp(&a.source.admin_distance())
                    })
                    // Tertiary: lower metric wins
                    .then_with(|| b.metric.cmp(&a.metric))
            })
    }

    /// Classful lookup: derive network from IP's class, match that
    pub fn classful_lookup(&self, dst: Ipv4Addr) -> Option<&RouteEntry> {
        let classful_net = IpClass::classful_network(dst)?;
        self.entries.iter().find(|r| {
            // In classful routing, we match the classful network boundary
            IpClass::classful_network(r.prefix.network)
                .map(|rn| rn.network == classful_net.network)
                .unwrap_or(false)
        })
    }

    /// Find all routes to a destination (all matching prefixes)
    pub fn all_matching(&self, dst: Ipv4Addr) -> Vec<&RouteEntry> {
        let mut matches: Vec<&RouteEntry> = self.entries
            .iter()
            .filter(|r| r.prefix.contains(dst))
            .collect();
        // Sort by prefix length descending (most specific first)
        matches.sort_by(|a, b| b.prefix.prefix_len.cmp(&a.prefix.prefix_len));
        matches
    }

    /// Print the routing table
    pub fn print(&self) {
        println!("\n╔══════════════════════════════════════════════════════════════════════╗");
        println!("║                        ROUTING TABLE                                ║");
        println!("╠════╦══════════════════╦════════════╦════════╦════════╦════════════╣");
        println!("║ Src║ Prefix           ║ Next Hop   ║ Iface  ║ Metric ║ Admin Dist ║");
        println!("╠════╬══════════════════╬════════════╬════════╬════════╬════════════╣");

        for r in &self.entries {
            let nh_str = match r.next_hop {
                Some(ip) => ip.to_string(),
                None     => "connected".to_string(),
            };
            println!("║ {:2} ║ {:16} ║ {:10} ║ {:6} ║ {:6} ║ {:10} ║",
                     r.source.symbol(),
                     format!("{}", r.prefix),
                     nh_str,
                     r.interface,
                     r.metric,
                     r.source.admin_distance());
        }
        println!("╚════╩══════════════════╩════════════╩════════╩════════╩════════════╝");
    }
}

// =============================================================================
// SECTION 5: SUBNET CALCULATOR
// =============================================================================

/// Subnet calculation results
#[derive(Debug)]
pub struct SubnetInfo {
    pub prefix:    IpPrefix,
    pub broadcast: Ipv4Addr,
    pub first:     Ipv4Addr,
    pub last:      Ipv4Addr,
    pub hosts:     u64,
}

impl SubnetInfo {
    pub fn new(ip: Ipv4Addr, prefix_len: u8) -> Self {
        let prefix = IpPrefix::new(ip, prefix_len);
        Self {
            broadcast: prefix.broadcast(),
            first:     prefix.first_host(),
            last:      prefix.last_host(),
            hosts:     prefix.host_count(),
            prefix,
        }
    }

    pub fn print(&self) {
        println!("  Network:      {}", self.prefix);
        println!("  Mask:         {} (/{}) ", self.prefix.mask(), self.prefix.prefix_len);
        println!("  Broadcast:    {}", self.broadcast);
        println!("  First Host:   {}", self.first);
        println!("  Last Host:    {}", self.last);
        println!("  Usable Hosts: {}", self.hosts);
    }
}

/// Enumerate all subnets when dividing a network with new prefix
pub fn enumerate_subnets(base: IpPrefix, new_prefix_len: u8) {
    assert!(new_prefix_len > base.prefix_len, "New prefix must be longer");
    assert!(new_prefix_len <= 32, "Prefix too long");

    let borrowed    = new_prefix_len - base.prefix_len;
    let num_subnets = 1u64 << borrowed;
    let block_size  = 1u64 << (32 - new_prefix_len);

    println!("\nSubnetting {} into /{} subnets:", base, new_prefix_len);
    println!("  Borrowed bits: {}, Subnets: {}, Hosts/subnet: {}",
             borrowed, num_subnets,
             IpPrefix::new(base.network, new_prefix_len).host_count());
    println!();
    println!("  {:<4} {:<22} {:<18} {:<18} {:<18}",
             "No.", "Subnet", "First Host", "Last Host", "Broadcast");
    println!("  {}", "-".repeat(82));

    for i in 0..num_subnets {
        let subnet_base = Ipv4Addr::from_u32(base.network.as_u32() + (i * block_size) as u32);
        let subnet      = IpPrefix::new(subnet_base, new_prefix_len);
        println!("  {:<4} {:<22} {:<18} {:<18} {:<18}",
                 i,
                 format!("{}", subnet),
                 subnet.first_host(),
                 subnet.last_host(),
                 subnet.broadcast());
    }
}

// =============================================================================
// SECTION 6: SUPERNET (ROUTE AGGREGATION) CALCULATOR
// =============================================================================

/// Find the smallest supernet that covers all given prefixes
pub fn find_supernet(prefixes: &[IpPrefix]) -> Option<IpPrefix> {
    if prefixes.is_empty() { return None; }

    // XOR all network addresses to find differing bits
    let differing: u32 = prefixes.iter()
        .skip(1)
        .fold(0, |acc, p| acc | (p.network.as_u32() ^ prefixes[0].network.as_u32()));

    // leading_zeros of differing tells us the common prefix length
    let common_len = if differing == 0 {
        32u8 // All addresses are identical
    } else {
        differing.leading_zeros() as u8
    };

    Some(IpPrefix::new(prefixes[0].network, common_len))
}

// =============================================================================
// SECTION 7: BINARY DISPLAY UTILITIES
// =============================================================================

/// Print an IP address in binary with octet separators
pub fn print_binary(ip: Ipv4Addr) {
    let val = ip.as_u32();
    for i in (0..32).rev() {
        if i < 31 && i % 8 == 7 { print!("."); }
        print!("{}", if val & (1 << i) != 0 { '1' } else { '0' });
    }
}

/// Print IP with network/host boundary marker
pub fn print_with_boundary(ip: Ipv4Addr, prefix_len: u8) {
    let val = ip.as_u32();
    print!("  Binary: ");
    for i in (0..32).rev() {
        let bit_pos = 31 - i; // bit position from left
        if bit_pos == prefix_len as usize { print!("|"); }
        else if i < 31 && i % 8 == 7 { print!("."); }
        print!("{}", if val & (1 << i) != 0 { '1' } else { '0' });
    }
    println!();

    print!("          ");
    for i in 0..32usize {
        if i == prefix_len as usize { print!("|"); }
        print!("{}", if i < prefix_len as usize { 'N' } else { 'H' });
    }
    println!("  (N=network, H=host)");
}

// =============================================================================
// SECTION 8: SPECIAL ADDRESS DETECTION
// =============================================================================

/// Check if an IP is a private RFC 1918 address
pub fn is_private(ip: Ipv4Addr) -> bool {
    ip_in(ip, "10.0.0.0/8")
        || ip_in(ip, "172.16.0.0/12")
        || ip_in(ip, "192.168.0.0/16")
}

/// Check if IP is in a CIDR range
fn ip_in(ip: Ipv4Addr, cidr: &str) -> bool {
    IpPrefix::parse(cidr).map(|p| p.contains(ip)).unwrap_or(false)
}

/// Check if IP is loopback (127.0.0.0/8)
pub fn is_loopback(ip: Ipv4Addr) -> bool {
    ip_in(ip, "127.0.0.0/8")
}

/// Check if IP is multicast (224.0.0.0/4)
pub fn is_multicast(ip: Ipv4Addr) -> bool {
    ip_in(ip, "224.0.0.0/4")
}

/// Check if IP is link-local APIPA (169.254.0.0/16)
pub fn is_link_local(ip: Ipv4Addr) -> bool {
    ip_in(ip, "169.254.0.0/16")
}

pub fn ip_category(ip: Ipv4Addr) -> &'static str {
    if is_loopback(ip)   { return "Loopback"; }
    if is_multicast(ip)  { return "Multicast"; }
    if is_link_local(ip) { return "Link-local (APIPA)"; }
    if is_private(ip)    { return "Private (RFC 1918)"; }
    "Public (Internet-routable)"
}

// =============================================================================
// SECTION 9: MAIN DEMONSTRATION
// =============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════════════════════════════════╗");
    println!("║       CLASSFUL vs CLASSLESS IP ROUTING — RUST DEMONSTRATION             ║");
    println!("╚══════════════════════════════════════════════════════════════════════════╝\n");

    // -------------------------------------------------------------------------
    println!("══════════════════════════════════════════════════════════════════");
    println!("PART 1: IP CLASS DETECTION (CLASSFUL ROUTING)");
    println!("══════════════════════════════════════════════════════════════════\n");

    let test_ips = [
        "10.5.3.2",
        "128.0.0.1",
        "172.16.50.4",
        "192.168.1.100",
        "224.0.0.5",
        "240.0.0.1",
    ];

    for ip_str in &test_ips {
        let ip: Ipv4Addr = ip_str.parse().unwrap();
        let cls          = IpClass::of(ip);
        let category     = ip_category(ip);

        println!("IP: {:<20} → {}  [{}]", ip, cls.description(), category);
        print!("  Binary: ");
        print_binary(ip);
        println!();

        if let Some(classful_net) = IpClass::classful_network(ip) {
            println!("  Classful Network: {}", classful_net);
        }
        println!();
    }

    // -------------------------------------------------------------------------
    println!("══════════════════════════════════════════════════════════════════");
    println!("PART 2: SUBNET CALCULATIONS (CIDR)");
    println!("══════════════════════════════════════════════════════════════════\n");

    let test_cases = [
        ("192.168.10.100/24", "Standard /24 LAN"),
        ("10.128.64.200/18",  "Non-standard prefix"),
        ("172.16.5.0/20",     "RFC 1918 Class B subnet"),
    ];

    for (cidr, label) in &test_cases {
        let prefix = IpPrefix::parse(cidr).unwrap();
        let info   = SubnetInfo::new(prefix.network, prefix.prefix_len);
        println!("--- {} : {} ---", cidr, label);
        info.print();
        println!("  Binary layout:");
        print_with_boundary(prefix.network, prefix.prefix_len);
        println!();
    }

    // -------------------------------------------------------------------------
    println!("══════════════════════════════════════════════════════════════════");
    println!("PART 3: VLSM SUBNETTING — 192.168.1.0/24 into /26 blocks");
    println!("══════════════════════════════════════════════════════════════════");

    let base = IpPrefix::parse("192.168.1.0/24").unwrap();
    enumerate_subnets(base, 26);

    // -------------------------------------------------------------------------
    println!("\n══════════════════════════════════════════════════════════════════");
    println!("PART 4: SUPERNETTING — ROUTE AGGREGATION");
    println!("══════════════════════════════════════════════════════════════════\n");

    let prefixes_to_aggregate = [
        IpPrefix::parse("192.168.0.0/24").unwrap(),
        IpPrefix::parse("192.168.1.0/24").unwrap(),
        IpPrefix::parse("192.168.2.0/24").unwrap(),
        IpPrefix::parse("192.168.3.0/24").unwrap(),
    ];

    println!("Networks to aggregate:");
    for p in &prefixes_to_aggregate {
        print!("  {:20} binary: ", format!("{}", p));
        print_binary(p.network);
        println!();
    }

    if let Some(supernet) = find_supernet(&prefixes_to_aggregate) {
        println!("\nSupernet: {} — covers all {} networks with ONE entry",
                 supernet, prefixes_to_aggregate.len());

        // Verify coverage
        println!("Verification:");
        for p in &prefixes_to_aggregate {
            let covered = supernet.is_supernet_of(*p);
            println!("  {} is{} covered by {}",
                     p,
                     if covered { "" } else { " NOT" },
                     supernet);
        }
    }

    // -------------------------------------------------------------------------
    println!("\n══════════════════════════════════════════════════════════════════");
    println!("PART 5: ROUTING TABLE + LONGEST PREFIX MATCH");
    println!("══════════════════════════════════════════════════════════════════");

    let mut rt = RoutingTable::new();

    // Build a realistic routing table
    rt.add_route("0.0.0.0/0",       Some("172.16.0.1"),  "eth2", 1,   RouteSource::Default);
    rt.add_route("10.0.0.0/8",      Some("10.0.0.2"),   "eth1", 110, RouteSource::Ospf);
    rt.add_route("10.20.0.0/16",    Some("10.0.0.3"),   "eth1", 20,  RouteSource::Ospf);
    rt.add_route("10.20.50.0/24",   Some("10.0.0.4"),   "eth0", 10,  RouteSource::Ospf);
    rt.add_route("10.20.50.128/25", Some("10.0.0.5"),   "eth0", 5,   RouteSource::Ospf);
    rt.add_route("192.168.0.0/22",  Some("10.0.0.6"),   "eth1", 1,   RouteSource::Static);
    rt.add_route("192.168.1.0/24",  None,               "eth0", 0,   RouteSource::Connected);
    rt.add_route("10.99.0.0/16",    Some("10.0.0.9"),   "eth3", 120, RouteSource::Rip);

    rt.print();

    println!("\n--- Longest Prefix Match Lookups ---\n");

    let lookups = [
        ("10.20.50.200",   "Should hit /25 — most specific"),
        ("10.20.50.100",   "Should hit /24 — /25 doesn't cover this"),
        ("10.20.1.1",      "Should hit /16"),
        ("10.5.0.1",       "Should hit /8"),
        ("10.99.5.5",      "Should hit /16 via RIP"),
        ("192.168.1.50",   "Should hit connected /24"),
        ("192.168.2.50",   "Should hit static supernet /22"),
        ("8.8.8.8",        "Should hit default route /0"),
    ];

    for (dst_str, desc) in &lookups {
        let dst: Ipv4Addr = dst_str.parse().unwrap();
        match rt.lpm_lookup(dst) {
            Some(r) => {
                let nh = r.next_hop.map(|ip| ip.to_string())
                           .unwrap_or_else(|| "connected".to_string());
                println!("  {:<18} → {:<20} via {:<12} [{}: {}]",
                         dst_str, format!("{}", r.prefix), nh, r.source.symbol(), desc);
            }
            None => {
                println!("  {:<18} → NO ROUTE — unreachable! [{}]", dst_str, desc);
            }
        }
    }

    // -------------------------------------------------------------------------
    println!("\n══════════════════════════════════════════════════════════════════");
    println!("PART 6: CLASSFUL vs CLASSLESS — SIDE-BY-SIDE COMPARISON");
    println!("══════════════════════════════════════════════════════════════════\n");

    let demo_dst: Ipv4Addr = "10.20.50.200".parse().unwrap();
    println!("Destination: {}\n", demo_dst);

    println!("CLASSFUL ROUTER:");
    println!("  Step 1: First octet = 10 → Class A → apply /8 mask");
    match rt.classful_lookup(demo_dst) {
        Some(r) => {
            let nh = r.next_hop.map(|ip| ip.to_string()).unwrap_or("connected".to_string());
            println!("  Result: Matched {} → next-hop: {} via {}",
                     r.prefix, nh, r.interface);
            println!("  ⚠ Uses /8 — ignores the more specific /25 route!");
        }
        None => println!("  Result: NO MATCH — routing black hole!"),
    }

    println!("\nCLASSLESS ROUTER (LPM):");
    println!("  Step 1: Check all routes where (dst AND mask) == network");
    println!("  Step 2: Pick longest matching prefix");
    let all = rt.all_matching(demo_dst);
    println!("  Matching prefixes (most specific first):");
    for r in &all {
        let nh = r.next_hop.map(|ip| ip.to_string()).unwrap_or("connected".to_string());
        println!("    {:<20} via {:<12} [{}{}]",
                 format!("{}", r.prefix),
                 nh,
                 r.source.symbol(),
                 if r.prefix == all[0].prefix { " ← WINNER" } else { "" });
    }

    println!("\n══════════════════════════════════════════════════════════════════");
    println!("PART 7: MASK VALIDATION AND SPECIAL CHECKS");
    println!("══════════════════════════════════════════════════════════════════\n");

    let masks = [
        (0xFFFFFF00u32, "255.255.255.0 (/24)"),
        (0xFFFFFFC0u32, "255.255.255.192 (/26)"),
        (0xFFFFFF01u32, "255.255.255.1 (INVALID — non-contiguous)"),
        (0xFFFF00FFu32, "255.255.0.255 (INVALID — non-contiguous)"),
    ];

    for (raw, label) in &masks {
        let mask = SubnetMask(*raw);
        println!("  Mask: {:40} valid: {}", label, mask.is_valid());
    }

    println!("\n══════════════════════════════════════════════════════════════════");
    println!("RUST DEMO COMPLETE");
    println!("══════════════════════════════════════════════════════════════════");
}
```

---

## 22. Mental Models and Decision Trees

### The "Building" Mental Model for Routing

```
Think of the internet as a CITY:

  CONTINENT = Autonomous System (AS)
  CITY      = Major network block (e.g., 10.0.0.0/8)
  DISTRICT  = Subnet (e.g., 10.20.0.0/16)
  STREET    = Sub-subnet (e.g., 10.20.50.0/24)
  HOUSE     = Individual host (/32)

ROUTING = The postal system:
  - Between cities: BGP (inter-AS, policy-based)
  - Within city:    OSPF/EIGRP (intra-AS, metric-based)
  - Local delivery: ARP + switch (finds the exact house)

KEY INSIGHT: Routing only cares about the STREET LEVEL and above.
             ARP (not routing) handles the final delivery to the house.
```

### The Classful vs Classless Decision Tree

```
WHEN TO USE WHICH APPROACH?

[Do you need subnet masks smaller or larger
 than the classful defaults (A=/8, B=/16, C=/24)?]
         |
    YES  |  NO
         |
    [Use CLASSLESS]   [Classful MIGHT work but
    CIDR + VLSM        classless is always better]
         |
    [Do you have        
     variable-sized    
     subnets?]         
         |
    YES  |  NO        
         |             
    [Use VLSM]    [Use fixed-length subnetting]
    (different    (simpler management)
    mask per
    subnet)
```

### Subnetting Quick-Reference Decision Tree

```
[Given: X hosts needed in a subnet]
         |
         v
[Find smallest power of 2 > X+2]
(+2 for network and broadcast addresses)
         |
         v
[That power of 2 = block size]
[32 - log2(block_size) = prefix_len]
         |
         v
[Verify: 2^(32-prefix_len) - 2 >= X]
         |
   YES   |   NO
         |
[Use this /prefix]  [Go to next larger block]
```

### The LPM Mental Model — "Most Specific Address Wins"

```
Routing Specificity Ladder (most → least):

/32  ████████████████████████████████  Single host route
/30  ████████████████████████████████  WAN point-to-point
/24  ████████████████████████████░░░░  Standard LAN
/16  ████████████████████░░░░░░░░░░░░  Large organization
/8   ████████░░░░░░░░░░░░░░░░░░░░░░░░  Class A network
/0   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  Default (catches all)

More filled bars = more specific = preferred in LPM lookup.
```

### Cognitive Framework — How Experts Think About Routing

```
Expert's 4-Step Mental Process for Any IP Routing Question:

Step 1: DECOMPOSE
  → What is the source IP?
  → What is the destination IP?
  → In binary, how many leading bits are SHARED?

Step 2: CLASSIFY
  → Are these in the same network? (no router needed)
  → Are these in different networks? (routing needed)
  → Is this between ASes? (BGP domain)
  → Is this within an AS? (IGP domain)

Step 3: MATCH
  → What routes exist in the table?
  → Which route has the LONGEST prefix that covers the destination?
  → What is the next hop for that route?

Step 4: VERIFY
  → Does the next hop make sense topologically?
  → Are there any more specific routes being overlooked?
  → Is there a routing loop risk?
```

---

## 23. Comparison Summary Table

```
┌─────────────────────────────┬──────────────────────────────┬──────────────────────────────────┐
│ Characteristic              │ Classful                     │ Classless (CIDR)                 │
├─────────────────────────────┼──────────────────────────────┼──────────────────────────────────┤
│ Era                         │ 1981–1993                    │ 1993–present                     │
│ RFC                         │ RFC 791                      │ RFC 1517–1520, 4632              │
│ Subnet mask in routes       │ NO (implicit from class)     │ YES (always explicit)            │
│ Address boundary            │ Fixed (A=/8, B=/16, C=/24)  │ Variable (any /0 to /32)         │
│ VLSM support                │ NO                           │ YES                              │
│ Route aggregation           │ NO                           │ YES (supernetting)               │
│ Routing table efficiency    │ Poor (many entries)          │ Excellent (aggregation)          │
│ Address utilization         │ Poor (class-forced waste)    │ Excellent (exact allocation)     │
│ Lookup algorithm            │ Class detection → fixed mask │ Longest Prefix Match             │
│ Routing protocols           │ RIPv1, IGRP                  │ RIPv2, OSPF, BGP, EIGRP         │
│ Update mechanism            │ Broadcast (255.255.255.255)  │ Multicast (224.0.0.x)           │
│ Mask in protocol updates    │ Not sent                     │ Sent with every update           │
│ Discontiguous subnets       │ Problematic/unsupported      │ Fully supported                  │
│ Default route               │ 0.0.0.0 (all-zeros network) │ 0.0.0.0/0 (explicit /0)         │
│ Internet scalability        │ Not scalable                 │ Scales to billions of routes     │
│ Authentication support      │ None (e.g., RIPv1)           │ MD5/SHA (RIPv2, OSPF, BGP)      │
│ Route type discrimination   │ By class boundary only       │ By prefix length (LPM)           │
│ Private addressing support  │ Limited                      │ Full (RFC 1918 + NAT)            │
│ Still in use?               │ NO (legacy only)             │ YES (universal)                  │
└─────────────────────────────┴──────────────────────────────┴──────────────────────────────────┘
```

---

## Epilogue — The Mastery Mindset

Understanding classful vs classless routing is not just about memorizing rules. It is about building a **mental model of how information flows through networks at the bit level**.

The journey from classful to classless mirrors a universal pattern in computer science:
- **Rigidity** (fixed classes, implicit rules) gives way to **flexibility** (explicit masks, variable boundaries)
- **Simplicity** (class detection) gives way to **power** (LPM, VLSM, aggregation)
- **Scale limitation** (4 billion addresses, poor utilization) drives **innovation** (CIDR, NAT, then IPv6)

Every time you see an IP address, train yourself to:
1. Immediately think in binary
2. Identify the prefix boundary
3. Compute the network and broadcast mentally
4. Ask: "What is the most specific route that covers this destination?"

This binary fluency is the foundation of network engineering mastery.

---

*End of Guide — Classful vs Classless IP Routing*