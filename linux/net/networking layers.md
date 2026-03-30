# Linux Networking Layers — The Complete, In-Depth Guide

> *"The network stack is not magic — it is a precise, layered machine. Master each layer and you master the internet itself."*

---

## Table of Contents

1. [Mental Model: Why Layers Exist](#1-mental-model-why-layers-exist)
2. [The OSI Model — The Universal Blueprint](#2-the-osi-model--the-universal-blueprint)
3. [The TCP/IP Model — What Linux Actually Uses](#3-the-tcpip-model--what-linux-actually-uses)
4. [The Linux Kernel Network Stack — The Master Architecture](#4-the-linux-kernel-network-stack--the-master-architecture)
5. [Layer 1 — Physical Layer](#5-layer-1--physical-layer)
6. [Layer 2 — Data Link Layer](#6-layer-2--data-link-layer)
7. [Layer 3 — Network Layer (IP)](#7-layer-3--network-layer-ip)
8. [Layer 4 — Transport Layer (TCP/UDP)](#8-layer-4--transport-layer-tcpudp)
9. [The Socket Layer — Bridge Between Userspace and Kernel](#9-the-socket-layer--bridge-between-userspace-and-kernel)
10. [System Calls — How Userspace Talks to the Kernel](#10-system-calls--how-userspace-talks-to-the-kernel)
11. [sk_buff — The Nerve Cell of Linux Networking](#11-sk_buff--the-nerve-cell-of-linux-networking)
12. [Netfilter & iptables/nftables — The Packet Firewall Engine](#12-netfilter--iptablesnftables--the-packet-firewall-engine)
13. [Routing Subsystem — How Linux Decides Where Packets Go](#13-routing-subsystem--how-linux-decides-where-packets-go)
14. [Network Namespaces & Virtual Networking](#14-network-namespaces--virtual-networking)
15. [Traffic Control (tc) — QoS and Shaping](#15-traffic-control-tc--qos-and-shaping)
16. [XDP & eBPF — The Modern Programmable Data Plane](#16-xdp--ebpf--the-modern-programmable-data-plane)
17. [Network Device Drivers — Hardware to Kernel](#17-network-device-drivers--hardware-to-kernel)
18. [Packet Journey: End-to-End Walkthrough](#18-packet-journey-end-to-end-walkthrough)
19. [Performance Tuning & Kernel Parameters](#19-performance-tuning--kernel-parameters)
20. [Debugging & Observability Tools](#20-debugging--observability-tools)
21. [Mental Models & Expert Intuition](#21-mental-models--expert-intuition)

---

## 1. Mental Model: Why Layers Exist

### The Core Problem

Imagine you need to send a letter to someone in another country. You don't think about:
- How the postal truck engine works
- How the airplane navigation system works
- What language the sorting machine reads

You just **write the letter and address it**. Each "layer" (envelope, post office, airline, customs) handles its own concern independently.

Networking layers solve the same problem: **separation of concerns**.

### The Abstraction Ladder

```
HIGH ABSTRACTION (what you think about)
    |
    |  "Send this HTTP request to google.com"
    |       ↓
    |  "Open a TCP stream to 142.250.80.46:443"
    |       ↓
    |  "Route this IP packet via gateway 192.168.1.1"
    |       ↓
    |  "Transmit these bytes over Ethernet frame"
    |       ↓
    |  "Flip these voltage signals on the wire"
    |
LOW ABSTRACTION (hardware reality)
```

Each layer:
- **Only talks to the layers directly above and below it**
- **Encapsulates** its logic so other layers don't need to know internals
- **Adds a header** when sending, **removes a header** when receiving

---

## 2. The OSI Model — The Universal Blueprint

### What is OSI?

**OSI = Open Systems Interconnection**. It is a **theoretical model** created by ISO in 1984 to standardize how different networking systems communicate. It has **7 layers**.

> **Key insight:** OSI is not what Linux implements directly — it is the *reference model*. Think of it as the "grammar textbook" and TCP/IP as the "actual spoken language."

### The 7 Layers

```
+-------+------------------+------------------------------------------+-------------------+
| Layer | Name             | Responsibility                           | Example Protocols |
+-------+------------------+------------------------------------------+-------------------+
|   7   | Application      | Human-facing protocols, data semantics   | HTTP, FTP, DNS    |
|   6   | Presentation     | Encryption, encoding, compression        | TLS/SSL, JPEG     |
|   5   | Session          | Managing sessions/dialogs                | NetBIOS, RPC      |
|   4   | Transport        | End-to-end delivery, segmentation        | TCP, UDP, SCTP    |
|   3   | Network          | Logical addressing, routing              | IP, ICMP, OSPF    |
|   2   | Data Link        | Framing, MAC addressing, error detection | Ethernet, Wi-Fi   |
|   1   | Physical         | Bits on wire, signals, hardware          | Cables, Radio     |
+-------+------------------+------------------------------------------+-------------------+
```

### Encapsulation — The Core Mechanism

Each layer **wraps** the data from the layer above it with its own header (and sometimes a trailer).

```
SENDER SIDE (Going DOWN the stack):

Application data: [ HTTP Request ]

Transport adds TCP header:
[ TCP Header | HTTP Request ]

Network adds IP header:
[ IP Header | TCP Header | HTTP Request ]

Data Link adds Ethernet header + trailer:
[ Eth Header | IP Header | TCP Header | HTTP Request | Eth Trailer ]

Physical: converts to bits/signals on wire
```

```
RECEIVER SIDE (Going UP the stack):

Physical: receives signals, converts to bits

Data Link strips Ethernet header:
[ IP Header | TCP Header | HTTP Request ]

Network strips IP header:
[ TCP Header | HTTP Request ]

Transport strips TCP header:
[ HTTP Request ]

Application: reads HTTP Request
```

> **Technical term — PDU (Protocol Data Unit):** Each layer calls its data by a different name:
> - Application: **Message** or **Data**
> - Transport: **Segment** (TCP) or **Datagram** (UDP)
> - Network: **Packet**
> - Data Link: **Frame**
> - Physical: **Bits**

---

## 3. The TCP/IP Model — What Linux Actually Uses

### Overview

The TCP/IP model (also called the Internet Model or DoD model) is the **practical, deployed model**. It has **4 layers** (some say 5).

```
OSI Model           TCP/IP Model        Linux Kernel Layer
-----------         ------------        ------------------
Application  ─┐
Presentation  ├──►  Application    ──►  Userspace (sockets)
Session      ─┘
Transport    ───►   Transport      ──►  Transport (TCP/UDP)
Network      ───►   Internet       ──►  Network (IP)
Data Link    ─┐
Physical     ─┴──►  Network Access ──►  Device Driver + NIC
```

### Why TCP/IP Collapsed OSI Layers

OSI's Session and Presentation layers (5 and 6) are **rarely implemented as separate layers** in practice. Applications themselves handle encoding (JSON, Protobuf) and sessions (cookies, tokens). This is why TCP/IP merges them all into "Application."

---

## 4. The Linux Kernel Network Stack — The Master Architecture

### The Complete Stack Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                         USERSPACE                                    ║
║                                                                      ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          ║
║   │  Nginx   │  │  curl    │  │  Python  │  │  Redis   │          ║
║   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          ║
║        │             │             │              │                  ║
║        └─────────────┴─────────────┴──────────────┘                 ║
║                              │                                       ║
║                    POSIX Socket API                                  ║
║              (send/recv/connect/bind/listen)                         ║
╚══════════════════════════════════╤═══════════════════════════════════╝
                                   │  syscall boundary
╔══════════════════════════════════╧═══════════════════════════════════╗
║                         KERNEL SPACE                                 ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │                    SOCKET LAYER (VFS)                          │  ║
║  │      sock → sk_buff queue → protocol operations               │  ║
║  └────────────────────┬───────────────────────────────────────────┘  ║
║                       │                                              ║
║  ┌────────────────────▼───────────────────────────────────────────┐  ║
║  │                  TRANSPORT LAYER                               │  ║
║  │           TCP           UDP          SCTP         DCCP        │  ║
║  │    (tcp_v4_rcv)    (udp_rcv)   (sctp_rcv)   (dccp_rcv)       │  ║
║  └────────────────────┬───────────────────────────────────────────┘  ║
║                       │                                              ║
║  ┌────────────────────▼───────────────────────────────────────────┐  ║
║  │               NETWORK LAYER (IPv4/IPv6)                        │  ║
║  │   ip_rcv() → ip_forward() → ip_local_deliver()                │  ║
║  │             Routing Table Lookup (FIB)                        │  ║
║  └──────────┬─────────────────────────────────┬──────────────────┘  ║
║             │                                 │                      ║
║  ┌──────────▼──────────┐           ┌──────────▼──────────────────┐  ║
║  │    NETFILTER        │           │      ARP / ICMP              │  ║
║  │  (iptables/nftables)│           │  (Address Resolution)        │  ║
║  │  PREROUTING         │           └──────────────────────────────┘  ║
║  │  FORWARD            │                                             ║
║  │  POSTROUTING        │                                             ║
║  │  INPUT / OUTPUT     │                                             ║
║  └──────────┬──────────┘                                             ║
║             │                                                        ║
║  ┌──────────▼──────────────────────────────────────────────────────┐  ║
║  │             TRAFFIC CONTROL (tc / qdisc)                       │  ║
║  │    HTB, FIFO, fq_codel, SFQ — shaping and scheduling           │  ║
║  └──────────┬──────────────────────────────────────────────────────┘  ║
║             │                                                        ║
║  ┌──────────▼──────────────────────────────────────────────────────┐  ║
║  │              NETWORK DEVICE LAYER                               │  ║
║  │      net_device struct → NAPI polling → DMA ring buffers       │  ║
║  └──────────┬──────────────────────────────────────────────────────┘  ║
║             │                                                        ║
║  ┌──────────▼──────────────────────────────────────────────────────┐  ║
║  │                  XDP (eXpress Data Path)                        │  ║
║  │         eBPF programs running at driver level                   │  ║
║  └──────────┬──────────────────────────────────────────────────────┘  ║
╚════════════╤═══════════════════════════════════════════════════════════╝
             │  hardware interrupt (IRQ)
╔════════════▼═══════════════════════════════════════════════════════════╗
║                    HARDWARE (NIC)                                      ║
║         Ethernet / Wi-Fi / InfiniBand / lo (loopback)                 ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 5. Layer 1 — Physical Layer

### What is the Physical Layer?

The Physical Layer is **the hardware reality**. It concerns:
- **Cables** (Cat5e, Cat6, fiber optic)
- **Radio waves** (Wi-Fi, 5G)
- **Voltage signals, light pulses, electromagnetic waves**
- **Pin layout, connector types** (RJ45, SFP)
- **Bit rate, bandwidth** (1 Gbps, 10 Gbps, 100 Gbps)
- **Signal encoding** (how a `1` or `0` is physically represented)

### Signal Encoding (Conceptual)

```
Digital data:    1   0   1   1   0   1
                 |       |   |       |
NRZ-L encoding: ─┘   ___┘   └───────┘
(Non-Return    ___                    
to Zero):        └───
```

### Linux's Role at Layer 1

Linux itself **does not manage Layer 1**. The Network Interface Card (NIC) and its driver handle it. However, Linux exposes physical layer information via:

```bash
# Check physical link status
ip link show eth0
# Output: state UP (physical link is connected)
#         state DOWN (cable unplugged or hardware off)

# Detailed NIC info including speed, duplex
ethtool eth0
# Output:
#   Speed: 1000Mb/s
#   Duplex: Full
#   Link detected: yes
```

### Key Terms

| Term | Meaning |
|------|---------|
| **Bandwidth** | Maximum data capacity of the medium (e.g., 1 Gbps) |
| **Latency** | Time for a signal to travel from A to B |
| **Duplex** | Full-duplex = send AND receive simultaneously. Half-duplex = one at a time |
| **MTU** | Maximum Transmission Unit — largest frame size (typically 1500 bytes for Ethernet) |
| **Jumbo Frames** | MTU > 1500 bytes (up to 9000), used in data centers |

---

## 6. Layer 2 — Data Link Layer

### What is the Data Link Layer?

The Data Link Layer provides **node-to-node** communication on the **same physical network** (the same LAN). It handles:
- **Framing**: Wrapping data in a structured Frame
- **MAC Addressing**: Hardware-level addresses (like a permanent serial number)
- **Error Detection**: CRC (Cyclic Redundancy Check)
- **Flow Control**: Preventing a fast sender from overwhelming a slow receiver

> **Key distinction:** Layer 2 only thinks about the **next hop** (the next device on the same network). It does NOT think about the final destination across the internet — that's Layer 3's job.

### The Ethernet Frame Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-------+-------+-------+-------+-------+-------+
|           Destination MAC Address (6 bytes)    |
+-------+-------+-------+-------+-------+-------+
|              Source MAC Address (6 bytes)      |
+-------+-------+-------+-------+-------+-------+
|  EtherType (2 bytes)  |
+-------+-------+-------+---//---+-------+-------+
|         Payload (46 - 1500 bytes)              |
+-------+-------+-------+---//---+-------+-------+
|   Frame Check Sequence / CRC (4 bytes)         |
+-------+-------+-------+-------+
```

#### Field Explanations

| Field | Size | Purpose |
|-------|------|---------|
| **Destination MAC** | 6 bytes | Hardware address of next-hop device |
| **Source MAC** | 6 bytes | Hardware address of sending device |
| **EtherType** | 2 bytes | What protocol is in the payload (0x0800 = IPv4, 0x0806 = ARP, 0x86DD = IPv6) |
| **Payload** | 46–1500 bytes | The IP packet (or other data) |
| **FCS/CRC** | 4 bytes | Error detection checksum |

### MAC Addresses

A **MAC (Media Access Control) address** is a 48-bit (6-byte) hardware identifier assigned to every NIC by the manufacturer. It is (theoretically) globally unique.

```
Format:  XX:XX:XX:XX:XX:XX
Example: 00:1A:2B:3C:4D:5E
         |--------|  |---------|
         OUI              Device ID
   (Manufacturer)       (Unique per device)
```

- **OUI** = Organizationally Unique Identifier (first 3 bytes) — identifies the manufacturer
- **Last 3 bytes** = device-specific serial

```bash
# View MAC address of your interfaces
ip link show

# or
ifconfig -a

# Output includes:
# link/ether 00:1a:2b:3c:4d:5e  ← this is the MAC
```

### ARP — Address Resolution Protocol

> **Problem:** You know someone's IP address (Layer 3), but you need their MAC address (Layer 2) to actually send a frame to them on the same LAN.
>
> **Solution:** ARP.

ARP is a Layer 2/3 bridge protocol.

#### ARP Process Diagram

```
Host A (192.168.1.10)              Host B (192.168.1.20)
         |                                    |
         |  "I need to send to 192.168.1.20"  |
         |  "What is your MAC address?"       |
         |                                    |
         |──── ARP Request (BROADCAST) ──────►|
         |     "Who has 192.168.1.20?"        |
         |     Dest MAC: FF:FF:FF:FF:FF:FF    |
         |     (broadcast to everyone)        |
         |                                    |
         |◄─── ARP Reply (UNICAST) ───────────|
         |     "I have 192.168.1.20"          |
         |     "My MAC is AA:BB:CC:DD:EE:FF"  |
         |                                    |
         |  Host A stores in ARP Cache:       |
         |  192.168.1.20 → AA:BB:CC:DD:EE:FF  |
```

```bash
# View ARP cache
arp -n
# or
ip neigh show

# Output:
# 192.168.1.1 dev eth0 lladdr 00:11:22:33:44:55 REACHABLE
```

### Switches — Layer 2 Devices

A **switch** operates at Layer 2. It learns MAC addresses and **forwards frames only to the correct port**:

```
Switch MAC Table:
  Port 1 → MAC: AA:BB:CC:DD:EE:FF
  Port 2 → MAC: 11:22:33:44:55:66
  Port 3 → MAC: AA:11:BB:22:CC:33

When a frame arrives at Port 1 destined for MAC 11:22:33:44:55:66:
  → Forward ONLY to Port 2 (not broadcast)
```

### VLANs — Virtual LANs (802.1Q Tagging)

A VLAN logically segments a single physical network into multiple isolated broadcast domains.

```
Ethernet Frame with 802.1Q VLAN Tag:

+----+----+----+----+----+----+----+----+----+
| Dst MAC | Src MAC | 0x8100 | VLAN Tag | EtherType | Payload | FCS |
+----+----+----+----+----+----+----+----+----+
                      ↑         ↑
                 "This is a  VLAN ID (12 bits = 4094 VLANs)
                 tagged frame"  + Priority (3 bits)
                                + DEI (1 bit)
```

```bash
# Create VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up
ip addr add 10.0.100.1/24 dev eth0.100
```

### Linux Kernel Data Link Layer Internals

In the kernel, Layer 2 is handled by:
- **`net_device` struct**: Represents a network interface
- **`dev_queue_xmit()`**: Sends an skb (socket buffer) to the device
- **`netif_receive_skb()`**: Receives an skb from the device and passes it up
- **NAPI (New API)**: Polling mechanism to reduce interrupt overhead

---

## 7. Layer 3 — Network Layer (IP)

### What is the Network Layer?

The Network Layer provides **end-to-end delivery** across multiple networks (internetworking). It handles:
- **IP Addressing**: Logical addresses (not hardware-bound)
- **Routing**: Deciding the path from source to destination
- **Fragmentation**: Breaking large packets for smaller MTU links
- **TTL (Time to Live)**: Preventing infinite loops

### IPv4 Header Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### IPv4 Header Field Explanations

| Field | Bits | Meaning |
|-------|------|---------|
| **Version** | 4 | Always `4` for IPv4 |
| **IHL** | 4 | IP Header Length in 32-bit words (minimum = 5 = 20 bytes) |
| **TOS/DSCP** | 8 | Type of Service / Quality of Service markings |
| **Total Length** | 16 | Total size of IP packet (header + payload), max 65535 bytes |
| **Identification** | 16 | Unique ID for reassembling fragments |
| **Flags** | 3 | DF (Don't Fragment), MF (More Fragments) |
| **Fragment Offset** | 13 | Position of this fragment in original datagram |
| **TTL** | 8 | Decremented at each router. Packet dropped at 0. Prevents infinite loops |
| **Protocol** | 8 | What's inside: 6=TCP, 17=UDP, 1=ICMP, 89=OSPF |
| **Checksum** | 16 | Error detection for the header only |
| **Source IP** | 32 | Sender's IP address |
| **Destination IP** | 32 | Receiver's IP address |

### IP Addresses

An IPv4 address is a **32-bit number** written in **dotted decimal**:

```
192.168.1.100

Binary:  11000000 . 10101000 . 00000001 . 01100100
         ──────────────────────────────────────────
         32 bits total
```

#### CIDR Notation and Subnets

> **CIDR** = Classless Inter-Domain Routing. A way to specify network blocks.

```
192.168.1.0/24

                 Network Part         Host Part
                 ┌──────────────┐    ┌────────┐
Binary:  11000000.10101000.00000001 . xxxxxxxx
                                       ↑
                               24 bits = network prefix
                               8 bits left for hosts = 256 addresses (0-255)
                               Usable hosts = 254 (subtract network + broadcast)
```

```
Subnet Mask: /24 = 255.255.255.0 = 11111111.11111111.11111111.00000000

The 1-bits = network part (fixed)
The 0-bits = host part (variable)
```

Common CIDR blocks:

```
/8   = 255.0.0.0       → 16,777,216 addresses (A class)
/16  = 255.255.0.0     → 65,536 addresses     (B class)
/24  = 255.255.255.0   → 256 addresses        (C class)
/30  = 255.255.255.252 → 4 addresses          (point-to-point links)
/32  = 255.255.255.255 → 1 address            (single host)
```

### Private IP Ranges (RFC 1918)

These addresses are **not routable on the internet** — used for internal/private networks:

```
10.0.0.0/8        → 10.x.x.x
172.16.0.0/12     → 172.16.x.x to 172.31.x.x
192.168.0.0/16    → 192.168.x.x
```

### IPv6 Header Structure

IPv6 uses **128-bit addresses** and has a **simplified fixed-size header** (40 bytes):

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|Traffic Class|           Flow Label                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Payload Length        |  Next Header  |   Hop Limit   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                         Source Address                        |
+                         (128 bits)                            +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                      Destination Address                      |
+                         (128 bits)                            +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

IPv6 Address Example:
```
2001:0db8:85a3:0000:0000:8a2e:0370:7334

Shortened: 2001:db8:85a3::8a2e:370:7334
           (consecutive zeros compressed with ::)
```

### ICMP — Internet Control Message Protocol

ICMP is a helper protocol at Layer 3 used for diagnostics and error reporting.

```
ICMP Message Types:
  Type 0: Echo Reply      ← response to ping
  Type 3: Destination Unreachable
  Type 8: Echo Request    ← ping
  Type 11: Time Exceeded  ← TTL expired (used by traceroute)
```

```bash
# ping uses ICMP Echo Request/Reply
ping 8.8.8.8

# traceroute sends packets with TTL=1, 2, 3... forcing ICMP Time Exceeded
traceroute 8.8.8.8
```

### Routing — How Linux Decides Where to Send Packets

#### The Routing Table

Linux maintains a **routing table** (also called FIB — Forwarding Information Base):

```bash
ip route show
# Output:
# default via 192.168.1.1 dev eth0 proto dhcp
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
```

Reading this:
```
default via 192.168.1.1 dev eth0
  │          │              └── use interface eth0
  │          └── send to gateway (router) at 192.168.1.1
  └── If no other route matches, use this (the default route)

192.168.1.0/24 dev eth0 scope link
  │                          └── directly connected (no router needed)
  └── Packets destined for 192.168.1.x go directly via eth0
```

#### Routing Decision Algorithm

```
PACKET ARRIVES → Need to forward it

For each entry in routing table (sorted by prefix length, longest first):

    Does destination IP match this route's network?
    YES → Use this route (LONGEST PREFIX MATCH)
    NO  → Try next route

No route matched? → ICMP Destination Unreachable → Drop packet
```

#### Longest Prefix Match

This is the fundamental routing algorithm:

```
Routing table:
  10.0.0.0/8      via 1.1.1.1
  10.0.1.0/24     via 2.2.2.2
  10.0.1.128/25   via 3.3.3.3
  default          via 4.4.4.4

Packet destined for 10.0.1.200:
  Matches 10.0.0.0/8     (prefix length 8)  ✓
  Matches 10.0.1.0/24    (prefix length 24) ✓ (more specific)
  Matches 10.0.1.128/25  (prefix length 25) ✓ (MOST specific → WINNER)
  → Route via 3.3.3.3
```

#### Linux Routing Policy (Multiple Routing Tables)

Linux supports **multiple routing tables** and **routing rules** (ip rule):

```
Priority 0:   local table    (loopback, local addresses)
Priority 32766: main table   (what you see with 'ip route')
Priority 32767: default table (last resort)
```

```bash
# View routing rules
ip rule show

# Add policy-based routing: traffic from 192.168.2.0/24 uses table 100
ip rule add from 192.168.2.0/24 table 100
ip route add default via 10.0.0.1 table 100
```

### NAT — Network Address Translation

NAT allows multiple private IPs to share one public IP. The most common form is **Masquerade / SNAT (Source NAT)**:

```
Private Network                    Internet
192.168.1.10:5000 ─┐
192.168.1.11:5001 ─┤─► [NAT Router: 1.2.3.4] ─► google.com:443
192.168.1.12:5002 ─┘

The router translates:
192.168.1.10:5000 → 1.2.3.4:40001 (outgoing)
1.2.3.4:40001     → 192.168.1.10:5000 (incoming reply)

The NAT table tracks these mappings.
```

```bash
# Enable masquerade (SNAT) for all traffic from eth0
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Enable IP forwarding (kernel must forward between interfaces)
echo 1 > /proc/sys/net/ipv4/ip_forward
# or
sysctl -w net.ipv4.ip_forward=1
```

---

## 8. Layer 4 — Transport Layer (TCP/UDP)

### Purpose of Transport Layer

The Transport Layer provides:
- **Multiplexing**: Many applications can use the network simultaneously via **port numbers**
- **Reliability** (TCP only): Guaranteed, ordered delivery
- **Flow Control** (TCP): Prevents sender from overwhelming receiver
- **Congestion Control** (TCP): Prevents sender from overwhelming the network

### Port Numbers

A **port** is a 16-bit number (0–65535) that identifies a specific **process or service** on a host.

```
IP Address = the building address
Port = the apartment number

192.168.1.100:80   → Web server
192.168.1.100:443  → HTTPS server
192.168.1.100:22   → SSH server
192.168.1.100:5432 → PostgreSQL
```

Port ranges:
```
0–1023     : Well-known ports (root required to bind)
1024–49151 : Registered ports
49152–65535: Ephemeral/dynamic ports (used by clients)
```

### TCP — Transmission Control Protocol

TCP provides **reliable, ordered, connection-oriented** communication.

#### TCP Segment Header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                               |
| Offset|  Res. |W|C|R|C|S|S|Y|I|            Window            |
|       |       |R|E|G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Key TCP flags:
```
SYN  (S) = Synchronize: initiate connection
ACK  (A) = Acknowledge: confirm receipt
FIN  (F) = Finish: initiate connection close
RST  (R) = Reset: abort connection immediately
PSH  (P) = Push: deliver immediately to application
URG  (U) = Urgent: urgent data present
```

#### TCP Three-Way Handshake (Connection Setup)

```
CLIENT                              SERVER
  |                                   |
  |──── SYN (seq=x) ─────────────────►|  "I want to connect, my seq starts at x"
  |                                   |
  |◄─── SYN-ACK (seq=y, ack=x+1) ────|  "OK, my seq starts at y, I received x"
  |                                   |
  |──── ACK (ack=y+1) ───────────────►|  "Got it, I received y"
  |                                   |
  |          [CONNECTION ESTABLISHED] |
```

> **What is a sequence number?** A number assigned to each byte in the TCP stream, allowing the receiver to reassemble segments in order and detect missing data.

> **What is an acknowledgment number?** It means "I have received everything up to byte N, send me byte N+1 next."

#### TCP Four-Way Handshake (Connection Teardown)

```
CLIENT                              SERVER
  |                                   |
  |──── FIN (seq=x) ─────────────────►|  "I'm done sending"
  |                                   |
  |◄─── ACK (ack=x+1) ────────────── |  "OK, noted"
  |                                   |
  |◄─── FIN (seq=y) ─────────────────|  "I'm also done sending"
  |                                   |
  |──── ACK (ack=y+1) ───────────────►|  "OK, connection fully closed"
  |                                   |
  |     [TIME_WAIT state: wait 2×MSL] |
```

> **TIME_WAIT**: The client waits 2× Maximum Segment Lifetime (~60-120 seconds) to ensure the final ACK was received. This prevents stale packets from a previous connection being mistaken for a new one.

#### TCP State Machine

```
                    ┌─────────┐
              ┌────►│  CLOSED │◄────────────────────┐
              │     └────┬────┘                     │
              │          │ passive open              │ close
              │          ▼                           │
              │     ┌──────────┐  close         ┌───┴────┐
              │     │  LISTEN  │───────────────►│TIME_WAIT│
              │     └────┬─────┘                └────────┘
              │          │ SYN recv                  ▲
              │          ▼                           │ FIN recv + FIN sent
              │     ┌──────────┐                    │
              │     │ SYN_RCVD │                ┌───┴────────┐
              │     └────┬─────┘                │CLOSING     │
              │          │ ACK recv              └───▲────────┘
              │          ▼                           │ FIN recv
   SYN sent   │     ┌──────────┐  FIN recv       ┌──┴──────────┐
       ┌──────┼────►│ESTABLISHED│────────────────►│ CLOSE_WAIT  │
       │      │     └────┬──────┘                 └──────┬──────┘
       │      │          │ close (FIN sent)               │ close
       │      │          ▼                                ▼
  ┌────┴───┐  │     ┌──────────┐                 ┌────────────┐
  │SYN_SENT│  │     │ FIN_WAIT1│                 │  LAST_ACK  │
  └────┬───┘  │     └────┬─────┘                 └──────┬─────┘
       │      │          │ ACK recv                     │ ACK recv
       │      │          ▼                              │
       │      │     ┌──────────┐                       │
       │      └─────│ FIN_WAIT2│                       │
       │            └────┬─────┘                       │
       │                 │ FIN recv                    │
       │                 ▼                             │
       │            ┌──────────┐                      │
       └───────────►│TIME_WAIT │◄────────────────────-┘
                    └──────────┘
```

#### TCP Flow Control — The Sliding Window

Flow control prevents the sender from sending too fast for the **receiver** to process.

```
Sender                         Receiver
  |                               |
  |  Window = 3 segments          |
  |──── Seg 1 ───────────────────►|  [buffer: 1]
  |──── Seg 2 ───────────────────►|  [buffer: 1,2]
  |──── Seg 3 ───────────────────►|  [buffer: 1,2,3]
  |                               |
  |           [Receiver processes segment 1]
  |◄─── ACK 2, Window=2 ─────────|  "Send up to 2 more"
  |──── Seg 4 ───────────────────►|
  |──── Seg 5 ───────────────────►|
  |  (must wait — window full)    |
```

#### TCP Congestion Control

Congestion control prevents the sender from overwhelming the **network** (not the receiver).

Four phases:

```
1. SLOW START
   - Begin with cwnd (congestion window) = 1 MSS
   - Double cwnd every RTT (exponential growth)
   - Until cwnd reaches ssthresh (slow start threshold)

2. CONGESTION AVOIDANCE
   - Increase cwnd by 1 MSS per RTT (linear growth)
   - Continue until packet loss detected

3. FAST RETRANSMIT
   - On 3 duplicate ACKs → retransmit lost segment immediately
   - (Don't wait for timeout)

4. FAST RECOVERY
   - Set ssthresh = cwnd/2
   - Set cwnd = ssthresh + 3
   - Resume congestion avoidance

cwnd growth:
   ^
   |        /
   |      /
 W |    / (congestion avoidance - linear)
 i |  /
 n |/ (slow start - exponential)
 d |___________________________
 o    time →
 w
```

#### Modern TCP Congestion Algorithms in Linux

```bash
# View available congestion control algorithms
cat /proc/sys/net/ipv4/tcp_available_congestion_control
# bbr cubic reno

# View current algorithm
cat /proc/sys/net/ipv4/tcp_congestion_control
# cubic

# Switch to BBR (Google's algorithm, better for high-bandwidth/latency links)
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

| Algorithm | Description |
|-----------|-------------|
| **cubic** | Default in Linux. Uses cubic function for window growth |
| **bbr** | Bottleneck Bandwidth and RTT — models network bandwidth |
| **reno** | Classic algorithm, simple |
| **htcp** | High-speed TCP |

### UDP — User Datagram Protocol

UDP is **connectionless, unreliable, low-overhead**. No handshake, no guarantees.

#### UDP Header

```
 0      7 8     15 16    23 24    31
+--------+--------+--------+--------+
|     Source      |   Destination   |
|      Port       |      Port       |
+--------+--------+--------+--------+
|                 |                 |
|     Length      |    Checksum     |
+--------+--------+--------+--------+
|          data octets ...
+---------------- ...
```

Only 8 bytes. Compare to TCP's minimum 20 bytes.

#### TCP vs UDP Decision Tree

```
Do you need reliability?
├─ YES → Do you need ordering?
│        ├─ YES → TCP
│        └─ NO  → TCP still (or implement yourself over UDP)
│
└─ NO  → Can you tolerate some packet loss?
          ├─ YES → Is latency critical?
          │        ├─ YES → UDP (gaming, VoIP, video streaming)
          │        └─ NO  → TCP is fine
          └─ NO  → TCP
```

Use UDP for: DNS, DHCP, NTP, video streaming, online games, VoIP, QUIC

---

## 9. The Socket Layer — Bridge Between Userspace and Kernel

### What is a Socket?

A **socket** is a **file descriptor** that represents a network communication endpoint. It is the API through which userspace applications interact with the kernel's network stack.

> **Key insight:** In Linux, "everything is a file." A socket is just a special kind of file. You can `read()`, `write()`, `close()` a socket just like a file.

### Socket Types

| Socket Type | Constant | Description |
|-------------|----------|-------------|
| **SOCK_STREAM** | `1` | TCP — reliable, ordered byte stream |
| **SOCK_DGRAM** | `2` | UDP — unreliable datagrams |
| **SOCK_RAW** | `3` | Raw IP — bypasses transport layer |
| **SOCK_SEQPACKET** | `5` | SCTP — reliable, message-based |

### Socket Address Families

| Family | Constant | Description |
|--------|----------|-------------|
| **AF_INET** | `2` | IPv4 |
| **AF_INET6** | `10` | IPv6 |
| **AF_UNIX/AF_LOCAL** | `1` | Unix domain sockets (inter-process on same host) |
| **AF_PACKET** | `17` | Raw packet access (Layer 2) |
| **AF_NETLINK** | `16` | Kernel-userspace communication (routing, netfilter) |

### Socket Lifecycle (TCP Server)

```
SERVER                                 CLIENT
  |                                       |
  | socket()                              | socket()
  | ↓                                     | ↓
  | bind(addr:port)                       |
  | ↓                                     |
  | listen(backlog)                       |
  | ↓                                     |
  | accept()  ◄────────────────────────── | connect(server_addr:port)
  | [blocks]                              | ↓
  | ↓ [returns new connected socket]     | [TCP 3-way handshake happens in kernel]
  | ↓                                     |
  | recv()/read() ◄──────────────────────►| send()/write()
  | send()/write() ──────────────────────►| recv()/read()
  |                                       |
  | close()  ────────────────────────────►| close()
```

### The Kernel Socket Structure (`struct sock`)

In the Linux kernel, every socket is represented by `struct sock` (in `include/net/sock.h`):

```
struct sock {
    struct sock_common  __sk_common;    // protocol-independent fields
    socket_lock_t       sk_lock;        // serialization lock
    struct sk_buff_head sk_receive_queue; // incoming data queue
    struct sk_buff_head sk_write_queue;   // outgoing data queue
    __u32               sk_rcvbuf;     // receive buffer size
    __u32               sk_sndbuf;     // send buffer size
    void               (*sk_data_ready)(struct sock *sk); // callback
    // ... many more fields
};
```

### Socket Buffers in Kernel

When data arrives, it sits in the **receive buffer** (`sk_rcvbuf`). When you call `recv()`, it is copied from kernel space to userspace.

```
NIC receives data
      │
      ▼
kernel: sk_buff allocated
      │
      ▼
TCP processes segment, appends to sk_receive_queue
      │
      ▼
userspace calls recv()
      │
      ▼
kernel copies from sk_receive_queue → userspace buffer
      │
      ▼
sk_buff freed
```

```bash
# View socket buffer sizes
cat /proc/sys/net/core/rmem_default    # default receive buffer
cat /proc/sys/net/core/wmem_default    # default write buffer
cat /proc/sys/net/core/rmem_max        # max receive buffer
cat /proc/sys/net/core/wmem_max        # max write buffer

# View active sockets
ss -tunapl     # t=TCP, u=UDP, n=numeric, a=all, p=process, l=listening
```

---

## 10. System Calls — How Userspace Talks to the Kernel

### The Syscall Boundary

Userspace programs cannot directly access hardware or kernel data structures. They must use **system calls** — controlled entry points into the kernel.

```
Userspace                     Kernel Space
  │                               │
  │  send(sockfd, buf, len, 0)    │
  │                               │
  │──── syscall instruction ─────►│ (CPU switches to ring 0 / kernel mode)
  │                               │
  │                               │  sys_sendmsg()
  │                               │    → sock_sendmsg()
  │                               │      → tcp_sendmsg()
  │                               │        → skb allocated
  │                               │          → TCP header added
  │                               │            → IP routing
  │                               │              → NIC driver
  │                               │
  │◄──── return (bytes sent) ─────│ (CPU switches back to ring 3 / user mode)
  │                               │
```

### Key Network System Calls

```
socket(domain, type, protocol)
    Creates a socket. Returns fd (file descriptor).
    Example: socket(AF_INET, SOCK_STREAM, 0)

bind(sockfd, addr, addrlen)
    Associates socket with a local address:port.

listen(sockfd, backlog)
    Marks socket as passive (server). backlog = connection queue size.

accept(sockfd, addr, addrlen)
    Accepts incoming connection. Returns new connected socket fd.

connect(sockfd, addr, addrlen)
    Initiates TCP connection (client side).

send(sockfd, buf, len, flags)
recv(sockfd, buf, len, flags)
    Send/receive data.

sendmsg(sockfd, msghdr, flags)
recvmsg(sockfd, msghdr, flags)
    Advanced send/receive with scatter-gather, ancillary data.

sendfile(out_fd, in_fd, offset, count)
    Zero-copy: send file directly from kernel, bypassing userspace.

setsockopt / getsockopt
    Set/get socket options (TCP_NODELAY, SO_REUSEADDR, etc.)

epoll_create / epoll_ctl / epoll_wait
    Scalable I/O multiplexing (better than select/poll for many connections).

shutdown(sockfd, how)
close(sockfd)
    Shut down / close a socket.
```

### Zero-Copy I/O

Traditional data path copies data multiple times:

```
Traditional: NIC → kernel buffer → userspace buffer → kernel buffer → NIC
             (4 copies, 2 context switches)

sendfile():  NIC → kernel buffer ──────────────────► NIC
             (2 copies, 1 context switch)

splice():    kernel buffer ────────────────────────► kernel buffer
             (0 copies via kernel pipe)
```

```c
// C example: zero-copy file transfer
int file_fd = open("largefile.bin", O_RDONLY);
int sock_fd = /* connected socket */;
off_t offset = 0;
sendfile(sock_fd, file_fd, &offset, file_size);
```

---

## 11. sk_buff — The Nerve Cell of Linux Networking

### What is sk_buff?

`sk_buff` (socket buffer) is the **most important data structure** in the Linux network stack. Every packet moving through the kernel is represented as an `sk_buff` (or `skb`).

Think of it as a **smart envelope** that holds the packet data and all metadata about it.

### The sk_buff Structure

```
struct sk_buff {
    /* Packet data pointers */
    unsigned char     *head;    // Start of allocated buffer
    unsigned char     *data;    // Start of actual data
    unsigned char     *tail;    // End of actual data
    unsigned char     *end;     // End of allocated buffer

    /* Network layer metadata */
    struct sock       *sk;      // Socket this skb belongs to
    struct net_device *dev;     // Device that received/will send
    __u16             protocol; // EtherType (IPv4, IPv6, ARP...)

    /* IP-layer info */
    struct  dst_entry *dst;     // Routing decision (where to forward)

    /* Transport-layer info */
    struct tcphdr     *h.th;    // Pointer to TCP header
    struct udphdr     *h.uh;    // Pointer to UDP header
    struct iphdr      *nh.iph;  // Pointer to IP header

    /* Checksum info */
    __wsum            csum;     // Checksum value

    /* ... many more fields */
};
```

### Memory Layout of sk_buff

```
    sk_buff structure                  Packet Data Buffer
    ┌─────────────────────┐           ┌───────────────────────────────────┐
    │  head  ─────────────┼──────────►│ [headroom]                        │
    │  data  ─────────────┼──────────►│ [Ethernet Header][IP Hdr][TCP Hdr]│
    │  tail  ─────────────┼──────────►│ [Payload Data]                    │
    │  end   ─────────────┼──────────►│ [tailroom]                        │
    │                     │           └───────────────────────────────────┘
    │  len   = tail-data  │             ↑              ↑
    │  (actual data size) │         data ptr        tail ptr
    └─────────────────────┘
```

### How Headers Are Added/Removed Efficiently

Instead of copying data when adding headers, Linux just **moves the `data` pointer**:

```
Adding a header (skb_push):
    Before: [headroom | IP Header | TCP Header | Payload]
                         ↑ data
    After:  [Eth Hdr | IP Header | TCP Header | Payload]
             ↑ data  (pointer moved backward)

Removing a header (skb_pull):
    Before: [Eth Hdr | IP Header | TCP Header | Payload]
             ↑ data
    After:  [Eth Hdr | IP Header | TCP Header | Payload]
                         ↑ data  (pointer moved forward)
```

This is **O(1) and zero-copy** — no data is ever moved in memory.

### sk_buff Lists

sk_buffs are linked together in queues:

```
sk_buff_head (queue head)
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│  skb 1  │───►│  skb 2  │───►│  skb 3  │──► NULL
│         │◄───│         │◄───│         │
└─────────┘    └─────────┘    └─────────┘
```

---

## 12. Netfilter & iptables/nftables — The Packet Firewall Engine

### What is Netfilter?

**Netfilter** is a kernel-level framework that provides **hooks** at specific points in the packet processing path. Tools like `iptables`, `nftables`, `ipvs`, and even NAT are built on top of Netfilter.

> **Hook:** A point in code where you can insert your own function. Like an event listener in programming.

### The Five Netfilter Hooks

```
                           ┌──────────────┐
                           │   ROUTING    │
                           │   DECISION   │
                           └──────┬───────┘
                                  │
              ┌───────────────────┼──────────────────────┐
              │                   │                      │
   Packet     │                   │                      │
   enters ────► PREROUTING ───────┤               FORWARD ──── exits
   NIC        │  (before routing) │  (routed to    (packet
              │                   │  local process) forwarded)
              │                   ▼                      │
              │              INPUT hook                  ▼
              │           (arrives at local         POSTROUTING
              │             process)              (before leaving)
              │                   │                      │
              │             ┌─────▼──────┐               │
              │             │  LOCAL     │               │
              │             │  PROCESS   │               │
              │             │ (userspace)│               │
              │             └─────┬──────┘               │
              │                   │                      │
              │              OUTPUT hook                 │
              │           (from local process)           │
              │                   │                      │
              └───────────────────┴──────────────────────┘
```

### iptables Tables

`iptables` organizes rules into **tables**, each with a purpose:

| Table | Purpose | Chains |
|-------|---------|--------|
| **filter** | Firewall — allow/drop packets | INPUT, FORWARD, OUTPUT |
| **nat** | Network Address Translation | PREROUTING, OUTPUT, POSTROUTING |
| **mangle** | Modify packet headers (TTL, TOS) | All 5 hooks |
| **raw** | Bypass connection tracking | PREROUTING, OUTPUT |
| **security** | SELinux/AppArmor labels | INPUT, FORWARD, OUTPUT |

### iptables Rule Processing

```
Packet arrives at INPUT chain:

Rule 1: -s 192.168.1.0/24 -j ACCEPT  ← Does packet match? YES → ACCEPT
Rule 2: -p tcp --dport 22 -j ACCEPT   ← (skipped, already matched)
Rule 3: -j DROP                        ← (skipped)

[If no rule matches, use chain policy: ACCEPT or DROP]
```

```bash
# List all rules with line numbers
iptables -L -n -v --line-numbers

# Add rule: accept SSH (port 22) from anywhere
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Add rule: drop all other incoming traffic
iptables -A INPUT -j DROP

# DNAT: redirect incoming port 80 to internal server
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.10:80

# MASQUERADE: NAT for all outgoing traffic
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Connection Tracking (conntrack)

The **connection tracking** module (`nf_conntrack`) maintains a table of all active connections, enabling **stateful** firewall rules.

```
conntrack table entry:
  proto=tcp src=192.168.1.10:54321 dst=8.8.8.8:443 state=ESTABLISHED
  bytes_in=1024 bytes_out=512 timeout=300s
```

Connection states:
```
NEW       → First packet of a new connection
ESTABLISHED → Part of an existing connection
RELATED    → Related to existing connection (e.g., FTP data channel)
INVALID    → Does not match any connection state
```

```bash
# View connection tracking table
conntrack -L

# Count active connections
conntrack -C

# Filter by protocol
conntrack -L -p tcp
```

### nftables — The Modern Replacement

`nftables` replaces `iptables` with a single framework, unified syntax, and better performance:

```
# nftables equivalent of iptables rules
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0\; policy drop\; }
nft add rule inet filter input tcp dport 22 accept
nft add rule inet filter input ct state established,related accept

# List rules
nft list ruleset
```

---

## 13. Routing Subsystem — How Linux Decides Where Packets Go

### The FIB — Forwarding Information Base

The **FIB** is Linux's main routing data structure. It is a **trie** (prefix tree) optimized for longest-prefix match lookups.

```
FIB Trie (simplified for 192.168.x.x):

          root
           │
     ┌─────┴─────┐
    192          10
     │
   168
     │
   ┌─┴─┐
  1    2
  │    │
 /24  /24
```

### Route Lookup Process

```
ip_route_input() called with destination IP

    ↓
Check routing cache (rcu lookup - fast path)
    │
    ├── Cache hit → return cached route (no FIB lookup)
    │
    └── Cache miss → FIB trie lookup
              │
              ├── Match found → create route cache entry → return
              │
              └── No match → return ENETUNREACH error
```

### Policy Routing

Linux supports **multiple routing tables** to make routing decisions based on more than just the destination:

```
Decision factors for policy routing:
  - Source IP address
  - Destination IP address
  - TOS (Type of Service)
  - Interface
  - Firewall mark (fwmark)
  - UID of the process
```

```bash
# View routing policy database
ip rule show
# 0:       lookup local
# 32766:   lookup main
# 32767:   lookup default

# Route-based on source address
ip rule add from 10.0.0.0/8 table 200
ip route add default via 172.16.0.1 table 200
```

### ECMP — Equal-Cost Multi-Path Routing

Linux supports multiple paths with equal cost — traffic is load-balanced:

```bash
# Add two equal-cost routes (ECMP)
ip route add 10.0.0.0/8 \
    nexthop via 192.168.1.1 weight 1 \
    nexthop via 192.168.1.2 weight 1

# Traffic to 10.0.0.x is split between two gateways
```

### Dynamic Routing Protocols

Static routes don't scale. Dynamic routing protocols automatically maintain routing tables:

| Protocol | Type | Use Case |
|----------|------|---------|
| **OSPF** | Link-state | Enterprise LAN |
| **BGP** | Path-vector | Internet routing (ISPs) |
| **RIP** | Distance-vector | Small networks (legacy) |
| **IS-IS** | Link-state | ISP core networks |
| **BABEL** | Distance-vector | Mesh networks |

Linux implements these via **FRRouting (FRR)** or **BIRD**:

```bash
# Install and run FRR (includes OSPF, BGP, etc.)
apt install frr
vtysh  # enter FRR shell (Cisco-like CLI)
```

---

## 14. Network Namespaces & Virtual Networking

### What are Network Namespaces?

A **network namespace** is an isolated copy of the network stack. Each namespace has its own:
- Network interfaces
- Routing tables
- iptables rules
- Connection tracking table
- Sockets

> **Use case:** Container networking (Docker, Kubernetes), VRF (Virtual Routing and Forwarding), network testing.

```bash
# Create a new network namespace
ip netns add myns

# Run a command inside the namespace
ip netns exec myns ip link show

# List namespaces
ip netns list
```

### Virtual Network Devices

Linux provides many types of virtual network devices:

#### veth — Virtual Ethernet Pair

Two virtual interfaces connected back-to-back. A packet sent into one end comes out the other. Used to connect namespaces.

```
Namespace A              Namespace B
┌──────────┐            ┌──────────┐
│  veth0   │────────────│  veth1   │
└──────────┘            └──────────┘
  packets here          appears here
```

```bash
# Create veth pair
ip link add veth0 type veth peer name veth1

# Move one end to another namespace
ip link set veth1 netns myns

# Configure IPs
ip addr add 10.0.0.1/24 dev veth0
ip netns exec myns ip addr add 10.0.0.2/24 dev veth1
```

#### bridge — Layer 2 Switch

A bridge connects multiple interfaces and operates as a software switch:

```
   eth0      veth0      veth1
     │          │          │
     └──────────┴──────────┘
              bridge0
         (software switch)
```

```bash
ip link add br0 type bridge
ip link set eth0 master br0
ip link set veth0 master br0
ip link set br0 up
```

#### tun/tap — Virtual L3/L2 Tunnels

- **tun** (tunnel): Layer 3 device. Works with IP packets. Used by VPNs (OpenVPN, WireGuard).
- **tap**: Layer 2 device. Works with Ethernet frames. Used by VMs (QEMU/KVM).

```
VPN user process              Kernel
        │                        │
        │  read/write /dev/tun0  │
        ├────────────────────────►│ tun0 device
        │                        │    ↓
        │     [encrypted]        │  IP routing
        │◄───────────────────────│    ↓
        │                        │  physical NIC
```

#### vxlan — Virtual Extensible LAN

VXLAN encapsulates Layer 2 frames inside UDP packets, allowing Layer 2 networks to span Layer 3 (IP) networks. Used extensively in cloud networking.

```
Host A                          Host B
┌─────────────────┐             ┌─────────────────┐
│ VM: 10.0.0.1    │             │ VM: 10.0.0.2    │
│       │         │             │       │         │
│    vxlan0       │             │    vxlan0       │
│  [L2 overlay]   │             │  [L2 overlay]   │
│       │         │             │       │         │
│  [UDP 4789]     │─────────────│  [UDP 4789]     │
│       │         │  Physical   │       │         │
│     eth0        │   Network   │     eth0        │
└─────────────────┘             └─────────────────┘
   192.168.1.10                    192.168.1.20
```

#### macvlan / ipvlan

- **macvlan**: Each virtual interface has its own MAC address. Multiple MACs on one physical NIC.
- **ipvlan**: Shares the MAC of parent, but each virtual interface has a unique IP.

```bash
# Create macvlan interface
ip link add macvlan0 link eth0 type macvlan mode bridge
```

#### Wireguard — Kernel-native VPN

WireGuard is built into the Linux kernel (since 5.6). It uses modern cryptography (Curve25519, ChaCha20, Poly1305):

```bash
# Create WireGuard interface
ip link add wg0 type wireguard
ip addr add 10.0.0.1/24 dev wg0

# Configure (using wg tool)
wg set wg0 private-key /etc/wireguard/privatekey \
    listen-port 51820 \
    peer <PUBLIC_KEY> \
    allowed-ips 10.0.0.2/32 \
    endpoint peer.example.com:51820
```

### Container Networking (Docker Model)

```
Docker Container                    Host Network
┌─────────────────────────────┐    ┌─────────────────────────────┐
│ Network Namespace            │    │                             │
│                              │    │                             │
│  eth0 (172.17.0.2)          │    │  docker0 bridge (172.17.0.1)│
│    │                         │    │    │                        │
│    │   veth pair              │    │  veth (host-side)          │
└────┼─────────────────────────┘    └────┼────────────────────────┘
     └────────────── ─────────────────────┘
          tunnel through veth pair
```

---

## 15. Traffic Control (tc) — QoS and Shaping

### What is tc?

`tc` (traffic control) is the Linux subsystem for **Quality of Service (QoS)** — controlling how packets are queued, delayed, prioritized, and limited.

### Key Concepts

| Term | Meaning |
|------|---------|
| **qdisc** | Queuing discipline — algorithm that decides the order/rate of packet transmission |
| **class** | A partition within a classful qdisc |
| **filter** | Rules that classify packets into classes |
| **HTB** | Hierarchical Token Bucket — most common classful qdisc |
| **fq_codel** | Flow Queue CoDel — modern default qdisc (reduces latency) |

### The tc Architecture

```
Packet ready to be sent
        │
        ▼
   ┌──────────┐
   │  qdisc   │
   │ (root)   │
   └─────┬────┘
         │
    ┌────┴────┐
    │  HTB    │
    │ 100Mbps │
    └─┬──┬───┘
      │  │
 ┌────┘  └─────┐
 │             │
┌┴─────┐  ┌───┴────┐
│Class A│  │Class B │
│50Mbps │  │50Mbps  │
│(HTTP) │  │(other) │
└───────┘  └────────┘
```

```bash
# Limit outgoing bandwidth on eth0 to 10Mbit/s
tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms

# More complex: HTB with class hierarchy
# Root qdisc
tc qdisc add dev eth0 root handle 1: htb default 30

# Root class (total bandwidth: 100Mbit)
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit

# High-priority class (SSH, 10Mbit guaranteed)
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 10mbit ceil 100mbit

# Default class (everything else, 90Mbit)
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 90mbit

# Filter: SSH traffic (port 22) → high-priority class
tc filter add dev eth0 parent 1: protocol ip u32 \
    match ip dport 22 0xffff flowid 1:10

# View current qdisc
tc qdisc show dev eth0
tc class show dev eth0
```

### Netem — Network Emulation

Netem simulates bad network conditions (delay, loss, corruption):

```bash
# Add 100ms delay to all packets
tc qdisc add dev eth0 root netem delay 100ms

# Add delay with ±10ms jitter
tc qdisc add dev eth0 root netem delay 100ms 10ms

# Add 5% random packet loss
tc qdisc add dev eth0 root netem loss 5%

# Combine: 50ms delay + 1% loss
tc qdisc add dev eth0 root netem delay 50ms loss 1%

# Remove
tc qdisc del dev eth0 root
```

---

## 16. XDP & eBPF — The Modern Programmable Data Plane

### What is eBPF?

**eBPF** (extended Berkeley Packet Filter) is a **virtual machine** inside the Linux kernel that lets you run sandboxed programs in kernel space without writing a kernel module.

> **Analogy:** eBPF is to the kernel what JavaScript is to a web browser — a safe, sandboxed environment to run custom code inside a larger system.

### What is XDP?

**XDP** (eXpress Data Path) is the **earliest hook point** in the Linux network stack — right inside the NIC driver, before any sk_buff is allocated. XDP programs run with eBPF.

```
NIC receives packet
        │
        ▼
  ┌───────────┐
  │  XDP Hook │  ← eBPF program runs HERE (nanosecond latency)
  │  (driver) │
  └─────┬─────┘
        │
   XDP_DROP  → Packet discarded immediately (DDoS mitigation!)
   XDP_PASS  → Continue to normal stack
   XDP_TX    → Bounce back to NIC (reflection)
   XDP_REDIRECT → Forward to another interface or CPU
        │
        ▼
  Normal kernel network stack
```

### Why XDP/eBPF Matters

| Approach | Performance | Flexibility |
|----------|-------------|-------------|
| Kernel module | Very High | Low (kernel ABI, risk) |
| Userspace DPDK | Very High | High (bypass kernel) |
| **XDP/eBPF** | **Very High** | **High (safe, in-kernel)** |
| iptables | Medium | Medium |

### eBPF Hook Points in Networking

```
XDP           ← packet at NIC driver (earliest possible)
tc (ingress)  ← packet entering kernel stack
tc (egress)   ← packet leaving kernel stack  
socket filter ← filter packets for a specific socket
kprobe        ← hook into any kernel function
tracepoint    ← predefined tracing events
cgroup        ← per-cgroup networking policy (used in containers)
```

### Writing an XDP Program (C)

```c
// xdp_drop_udp.c — Drop all UDP packets using XDP
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_prog(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void*)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != __constant_htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *ip = (void*)(eth + 1);
    if ((void*)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_UDP) return XDP_PASS;

    return XDP_DROP;   // Drop all UDP packets
}

char _license[] SEC("license") = "GPL";
```

```bash
# Compile
clang -O2 -target bpf -c xdp_drop_udp.c -o xdp_drop_udp.o

# Load onto interface
ip link set dev eth0 xdp obj xdp_drop_udp.o sec xdp

# Remove
ip link set dev eth0 xdp off
```

### eBPF Maps

eBPF programs communicate with userspace and share state through **maps** — key-value stores in kernel memory:

```c
// Define a hash map in eBPF
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);   // IP address
    __type(value, __u64); // packet count
} packet_count_map SEC(".maps");

// In eBPF program, update map:
__u32 src_ip = ip->saddr;
__u64 *count = bpf_map_lookup_elem(&packet_count_map, &src_ip);
if (count) (*count)++;
else { __u64 one = 1; bpf_map_update_elem(&packet_count_map, &src_ip, &one, BPF_ANY); }
```

### Popular eBPF Tools

| Tool | Purpose |
|------|---------|
| **bpftrace** | High-level tracing scripting language |
| **bcc** | Python/C framework for eBPF programs |
| **Cilium** | eBPF-based Kubernetes CNI (networking + security) |
| **Katran** | Facebook's XDP-based L4 load balancer |
| **Falco** | Runtime security using eBPF |
| **pixie** | Kubernetes observability |

---

## 17. Network Device Drivers — Hardware to Kernel

### What is a Network Device Driver?

A **NIC driver** is a kernel module that manages the hardware NIC. It:
- Initializes the hardware
- Manages DMA ring buffers for TX and RX
- Handles hardware interrupts
- Implements the `net_device_ops` interface

### The net_device Structure

```c
struct net_device {
    char             name[IFNAMSIZ];    // "eth0", "lo", "wlan0"
    struct net_device_ops *netdev_ops;  // TX, open, stop, etc.
    unsigned int     mtu;               // 1500 for Ethernet
    unsigned char    dev_addr[MAX_ADDR_LEN]; // MAC address
    struct net_device_stats stats;      // TX/RX counters
    // ...
};
```

### TX Path (Sending)

```
Application calls send()
        │
        ▼
TCP/IP Stack creates sk_buff
        │
        ▼
dev_queue_xmit(skb)
        │
        ▼
qdisc (traffic control queue)
        │
        ▼
ndo_start_xmit() ← driver's transmit function
        │
        ▼
DMA: copy skb data to NIC TX ring buffer
        │
        ▼
NIC hardware transmits frames
        │
        ▼
TX completion interrupt → free sk_buff
```

### RX Path (Receiving)

```
Frame arrives at NIC
        │
        ▼
DMA: NIC copies frame to kernel RX ring buffer
        │
        ▼
Hardware interrupt (IRQ) fires
        │
        ▼
Interrupt handler: napi_schedule()
(schedules softirq, disables further interrupts)
        │
        ▼
NET_RX_SOFTIRQ fires (softirq context)
        │
        ▼
NAPI poll: driver's poll() function
    - Reads frames from RX ring
    - Creates sk_buff for each frame
    - Calls netif_receive_skb()
    - Re-enables interrupts when budget exhausted
        │
        ▼
netif_receive_skb() / __netif_receive_skb()
        │
        ▼
Protocol handler (ip_rcv for IPv4)
        │
        ▼
Up through TCP/IP stack → socket → userspace
```

### NAPI — New API

**NAPI** is a hybrid interrupt/polling mechanism:

```
Without NAPI (old):
  Packet 1 → IRQ → process packet 1
  Packet 2 → IRQ → process packet 2
  Packet 3 → IRQ → process packet 3
  [1000 packets/sec = 1000 interrupts/sec → CPU overloaded]

With NAPI:
  Packet 1 → IRQ → disable IRQ → enter poll loop
    poll: process packet 1
    poll: process packet 2
    poll: process packet 3
    ...
    poll budget exhausted → re-enable IRQ → return
  [1000 packets/sec → 1 IRQ + 1 poll loop → much less overhead]
```

### Ring Buffers

NICs use **ring buffers** (circular queues) for DMA:

```
RX Ring Buffer:
  ┌──────────────────────────────────────────────────┐
  │ [desc0] [desc1] [desc2] [desc3] [desc4] [desc5] │
  │   ↑                                    ↑         │
  │  head                                 tail       │
  │ (next to fill)                   (next to read)  │
  └──────────────────────────────────────────────────┘

  desc = descriptor pointing to a DMA buffer
  NIC fills buffers from tail
  Kernel reads from head
  Ring: when tail reaches end, it wraps to start
```

```bash
# View/change RX/TX ring buffer sizes
ethtool -g eth0
ethtool -G eth0 rx 4096 tx 4096
```

---

## 18. Packet Journey: End-to-End Walkthrough

### Scenario: curl https://example.com from your Linux machine

```
Step 1: DNS Resolution
──────────────────────
curl resolves "example.com"
  → glibc resolver reads /etc/resolv.conf
  → UDP socket to 8.8.8.8:53
  → DNS query packet created
  → IP: src=192.168.1.10, dst=8.8.8.8, proto=UDP
  → Routing: default route via 192.168.1.1
  → ARP: resolve 192.168.1.1's MAC
  → Ethernet frame: src=our:mac, dst=router:mac
  → Frame transmitted on wire

Step 2: TCP Handshake (TLS on port 443)
────────────────────────────────────────
  SYN packet created (TCP, src_port=54321, dst_port=443)
  → IP header: src=192.168.1.10, dst=93.184.216.34 (example.com)
  → Routing: default route via 192.168.1.1
  → NAT: router rewrites src to public IP
  → Travels through internet (BGP routers)
  → example.com server: SYN-ACK returned
  → Our machine: sends ACK → connection ESTABLISHED

Step 3: TLS Handshake (Application Layer)
──────────────────────────────────────────
  TLS ClientHello → TCP segment → IP packet → Ethernet frame → wire
  TLS ServerHello + Certificate
  TLS Key exchange (ECDHE)
  TLS Finished → encrypted tunnel established

Step 4: HTTP/2 Request
───────────────────────
  "GET / HTTP/2" written to TLS socket
  → TLS encrypts
  → TCP segments data (if > MSS=1460 bytes)
  → IP packets created
  → Each packet: routing → NAT → wire

Step 5: Response Journey (Inbound)
────────────────────────────────────
  Data arrives at NIC as Ethernet frames
  → NIC DMA → RX ring buffer
  → Hardware interrupt → NAPI poll
  → netif_receive_skb()
  → ip_rcv(): validate IP header, check TTL
  → Netfilter PREROUTING hooks (iptables check)
  → Routing: ip_local_deliver (it's for us)
  → Netfilter INPUT hooks
  → tcp_v4_rcv(): validate TCP, deliver to socket
  → sk_receive_queue: data queued
  → userspace: recv() unblocks, data copied
  → TLS decrypts
  → HTTP/2 parser reads response
  → curl displays HTML
```

### Packet Journey Flowchart (Receive Side)

```
                    ┌──────────────────────────────────────┐
                    │           NIC HARDWARE               │
                    │    Frame received via DMA             │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   Hardware Interrupt (IRQ)            │
                    │   NAPI scheduled                      │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   NET_RX_SOFTIRQ                      │
                    │   netif_receive_skb()                 │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   XDP (if loaded) — very early hook   │
                    │   XDP_DROP / XDP_PASS / XDP_REDIRECT  │
                    └──────────────┬───────────────────────┘
                                   │ XDP_PASS
                    ┌──────────────▼───────────────────────┐
                    │   Traffic Control ingress (tc)        │
                    │   eBPF classifiers / actions          │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │   Netfilter: PREROUTING               │
                    │   (raw → mangle → nat → conntrack)    │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │       ROUTING DECISION                │
                    │   Is this packet for us?              │
                    └──────┬───────────────┬───────────────┘
                           │ YES           │ NO
              ┌────────────▼──┐       ┌────▼───────────────┐
              │  Netfilter:   │       │  Netfilter: FORWARD │
              │    INPUT      │       │   (if routing ON)   │
              └────────┬──────┘       └─────────────────────┘
                       │
              ┌────────▼──────────────────────────┐
              │         Transport Layer            │
              │   tcp_v4_rcv() / udp_rcv()         │
              └────────┬──────────────────────────┘
                       │
              ┌────────▼──────────────────────────┐
              │         Socket Layer               │
              │   sk_receive_queue — data queued   │
              └────────┬──────────────────────────┘
                       │
              ┌────────▼──────────────────────────┐
              │         Userspace                  │
              │   recv() → data copied             │
              └────────────────────────────────────┘
```

---

## 19. Performance Tuning & Kernel Parameters

### Critical sysctl Parameters

#### Receive Buffer Sizes

```bash
# Increase socket receive buffer (important for high-throughput)
sysctl -w net.core.rmem_max=134217728      # 128MB max
sysctl -w net.core.rmem_default=16777216   # 16MB default
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
#                              min default max
```

#### Send Buffer Sizes

```bash
sysctl -w net.core.wmem_max=134217728
sysctl -w net.core.wmem_default=16777216
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
```

#### Backlog and Connection Queues

```bash
# SYN backlog (incomplete connections queue)
sysctl -w net.ipv4.tcp_max_syn_backlog=65536

# Accept queue (completed connections waiting for accept())
sysctl -w net.core.somaxconn=65536

# Increase netdev receive queue
sysctl -w net.core.netdev_max_backlog=250000
```

#### TCP Tuning

```bash
# Enable TCP timestamps (required for PAWS, congestion control)
sysctl -w net.ipv4.tcp_timestamps=1

# TCP keepalive (detect dead connections)
sysctl -w net.ipv4.tcp_keepalive_time=60
sysctl -w net.ipv4.tcp_keepalive_intvl=10
sysctl -w net.ipv4.tcp_keepalive_probes=6

# Reuse TIME_WAIT sockets (for high connection rate servers)
sysctl -w net.ipv4.tcp_tw_reuse=1

# BBR congestion control
sysctl -w net.ipv4.tcp_congestion_control=bbr

# TCP Fast Open (reduce 3-way handshake overhead)
sysctl -w net.ipv4.tcp_fastopen=3
```

#### NIC Offloading

Modern NICs can offload work from the CPU:

```bash
# View offload settings
ethtool -k eth0

# TCP Segmentation Offload: NIC splits large TCP segments
ethtool -K eth0 tso on

# Generic Segmentation Offload: software fallback for TSO
ethtool -K eth0 gso on

# Large Receive Offload: NIC merges small frames
ethtool -K eth0 lro on

# Generic Receive Offload
ethtool -K eth0 gro on

# Receive Side Scaling: spread RX across multiple CPUs
ethtool -K eth0 ntuple on
ethtool -N eth0 rx-flow-hash tcp4 sdfn
```

#### IRQ Affinity — Binding NIC Interrupts to CPUs

```bash
# View IRQ for eth0
cat /proc/interrupts | grep eth0

# Pin IRQ 34 to CPU 0
echo 1 > /proc/irq/34/smp_affinity

# Use irqbalance for automatic balancing
systemctl start irqbalance
```

### The BDP — Bandwidth-Delay Product

> **Key performance insight:** For maximum throughput, TCP buffers must be large enough to fill the pipe.

```
BDP = Bandwidth × RTT

Example:
  Link: 1 Gbps
  RTT:  100ms = 0.1s
  BDP = 1,000,000,000 bits/s × 0.1s = 100,000,000 bits = 12.5 MB

  → You need at least 12.5 MB of TCP buffer to saturate this link!
```

---

## 20. Debugging & Observability Tools

### Network Diagnostics Toolkit

#### ip — Modern replacement for ifconfig/route

```bash
# Interface management
ip link show
ip link set eth0 up/down
ip addr add 10.0.0.1/24 dev eth0

# Routing
ip route show
ip route add 10.0.0.0/8 via 192.168.1.1
ip route get 8.8.8.8    # Show which route would be used

# ARP/neighbor
ip neigh show
ip neigh flush dev eth0

# Network namespaces
ip netns list
ip netns exec <ns> <command>
```

#### ss — Socket Statistics (replaces netstat)

```bash
ss -tulnp                    # All listening TCP/UDP sockets
ss -t state established      # Established TCP connections
ss -o state time-wait        # TIME_WAIT sockets
ss -s                        # Summary statistics
ss 'dst 8.8.8.8'             # Connections to specific host
ss -4 -t -a                  # IPv4 TCP all
```

#### tcpdump — Packet Capture

```bash
# Capture all packets on eth0
tcpdump -i eth0

# Capture TCP on port 80
tcpdump -i eth0 tcp port 80

# Capture and decode verbosely
tcpdump -i eth0 -v -X

# Save to file for Wireshark analysis
tcpdump -i eth0 -w capture.pcap

# Read from file
tcpdump -r capture.pcap

# Complex filters
tcpdump -i eth0 'src 192.168.1.10 and (tcp port 443 or tcp port 80)'
```

#### nmap — Network Scanner

```bash
# Scan open ports on a host
nmap -sS 192.168.1.1         # SYN scan (stealthy)
nmap -sV 192.168.1.1         # Version detection
nmap -O 192.168.1.1          # OS detection
nmap -A 192.168.1.0/24       # Aggressive scan of entire subnet
nmap -p 1-65535 target.com   # Full port scan
```

#### iperf3 — Bandwidth Testing

```bash
# Server side
iperf3 -s

# Client side (test to server)
iperf3 -c server.ip

# UDP test
iperf3 -c server.ip -u -b 100M

# Bidirectional
iperf3 -c server.ip --bidir

# Long test (60 seconds)
iperf3 -c server.ip -t 60
```

#### ethtool — NIC Diagnostics

```bash
ethtool eth0           # Link status, speed, duplex
ethtool -i eth0        # Driver info
ethtool -S eth0        # NIC statistics (RX/TX errors, drops)
ethtool -k eth0        # Offload features
ethtool -g eth0        # Ring buffer sizes
ethtool -c eth0        # Interrupt coalescing settings
```

#### /proc/net — Kernel Network Statistics

```bash
cat /proc/net/dev          # Per-interface RX/TX stats
cat /proc/net/tcp          # All TCP sockets (hex format)
cat /proc/net/snmp         # SNMP counters (TCP, UDP, IP stats)
cat /proc/net/netstat      # Extended stats
cat /proc/net/if_inet6     # IPv6 interfaces
cat /proc/net/arp          # ARP table
cat /proc/net/route        # Routing table (hex format)
```

#### perf — Kernel Performance Profiling

```bash
# Profile network stack CPU usage
perf top -g

# Record and report
perf record -g -a sleep 10
perf report

# Trace specific kernel functions
perf trace -e net:net_dev_xmit
```

#### bpftrace — High-Level eBPF Tracing

```bash
# Count packets per protocol
bpftrace -e 'tracepoint:net:netif_receive_skb { @[args->name] = count(); }'

# Trace TCP state changes
bpftrace -e 'kprobe:tcp_set_state { printf("TCP state: %d\n", arg1); }'

# Measure send() latency
bpftrace -e 'kprobe:tcp_sendmsg { @start[tid] = nsecs; }
             kretprobe:tcp_sendmsg /@start[tid]/ {
               @lat = hist(nsecs - @start[tid]);
               delete(@start[tid]);
             }'
```

#### Debugging Flow Decision Tree

```
Network problem reported
        │
        ▼
Is the interface UP?
  ip link show → state UP?
  └─ NO → ip link set dev eth0 up
  └─ YES ↓

IP address configured?
  ip addr show
  └─ NO → ip addr add ...
  └─ YES ↓

Can ping gateway?
  ping 192.168.1.1
  └─ NO → ARP issue? Check: ip neigh show
  └─ YES ↓

Can ping 8.8.8.8?
  └─ NO → Routing issue? ip route show
         → NAT issue? iptables -t nat -L
         → Firewall? iptables -L
  └─ YES ↓

Can ping google.com (by name)?
  └─ NO → DNS issue: cat /etc/resolv.conf
          dig google.com @8.8.8.8
  └─ YES ↓

Specific port not working?
  ss -tlnp (is service listening?)
  tcpdump (are packets arriving?)
  iptables -L (firewall blocking?)
```

---

## 21. Mental Models & Expert Intuition

### The Plumber's Mental Model

Think of the network stack as plumbing:
- **Pipes** = network cables and virtual links
- **Fittings/joints** = protocol headers (where data transforms)
- **Valves** = iptables/nftables rules
- **Pressure regulators** = tc/traffic control
- **Water** = packets/bytes
- **Meters** = /proc/net/dev counters

When something is broken, you trace the water: where did it stop flowing?

### The Layered Contract Model

Each layer has a **contract**:

```
Layer N provides services TO Layer N+1
Layer N uses services FROM Layer N-1

TCP's contract with application:
  "I will deliver your bytes, in order, without duplicates, or tell you it failed."

IP's contract with TCP:
  "I will make my best effort to deliver your packet to the destination.
   I give no guarantees."

Ethernet's contract with IP:
  "I will deliver your frame to the next hop on this LAN.
   I detect but don't fix errors."
```

If something breaks, ask: "Which layer's contract was violated?"

### The State Machine Model

Almost everything in networking is a **state machine**:
- TCP connection: CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → CLOSED
- ARP entry: INCOMPLETE → REACHABLE → STALE → PROBE → FAILED
- BGP session: IDLE → CONNECT → ACTIVE → OPENSENT → ESTABLISHED

When debugging, always ask: **"What state is this connection/entry in, and why?"**

### Deliberate Practice for Networking Mastery

```
LEVEL 1: Conceptual Understanding
  Read and re-read this guide.
  Draw all diagrams from memory.
  Explain each layer to someone else.

LEVEL 2: Hands-On Exploration
  Set up virtual network topologies with ip netns.
  Capture and analyze your own traffic with tcpdump.
  Write iptables rules for real scenarios.

LEVEL 3: Build From Scratch
  Write a raw socket program (in C/Rust) that sends ARP requests.
  Implement a simple TCP client/server using only syscalls.
  Write an XDP/eBPF program that counts packets per IP.

LEVEL 4: Diagnose Real Problems
  Debug broken network configurations.
  Tune kernel parameters for high-throughput scenarios.
  Trace a slow request end-to-end with perf + bpftrace.

LEVEL 5: Design
  Design container networking for 10,000 pods.
  Design a DDoS mitigation system using XDP.
  Design a zero-downtime load balancer.
```

### Chunking Strategy (Cognitive Science)

Instead of memorizing isolated facts, build **chunks**:

```
Chunk 1: "Ethernet Frame"
  = [ Dst MAC | Src MAC | EtherType | Payload | CRC ]
  = Layer 2, same-LAN delivery, 1500 byte MTU

Chunk 2: "TCP Connection Setup"
  = SYN → SYN-ACK → ACK
  = Establishes sequence numbers
  = Creates ESTABLISHED state on both sides

Chunk 3: "Packet Leaving Machine"
  = Socket write → TCP segment → IP packet → Routing → ARP → Ethernet frame → Wire
  = Each layer adds a header
  = Reversed on the other side
```

Once you have these chunks, complex scenarios become *combinations of simple chunks*.

### Pattern Recognition for Diagnostics

| Symptom | Pattern | Likely Cause |
|---------|---------|-------------|
| Can ping IP but not hostname | DNS pattern | /etc/resolv.conf, DNS server down |
| Can ping gateway, not internet | Routing pattern | Default route missing, NAT broken |
| Connection refused | Port closed | Service not running, firewall DROP |
| Connection timeout | No response | Firewall DROP (vs REJECT), routing loop |
| High packet loss | Buffer pattern | RX ring buffer too small, CPU overloaded |
| Asymmetric latency | Routing pattern | Different paths inbound/outbound |
| Connections reset | RST pattern | Firewall RST, SO_LINGER, bad load balancer |

---

## Summary: The Complete Stack in One View

```
╔══════════════════════════════════════════════════════════════════╗
║  Layer    │  What it does          │  Key Linux Components       ║
╠══════════════════════════════════════════════════════════════════╣
║  7 App    │  User data/protocols   │  nginx, curl, your code     ║
║  ─────────┼────────────────────────┼─────────────────────────────║
║  4 Trans  │  End-to-end delivery   │  TCP, UDP (kernel)          ║
║  ─────────┼────────────────────────┼─────────────────────────────║
║  3 Net    │  Routing, addressing   │  ip, netfilter, FIB         ║
║  ─────────┼────────────────────────┼─────────────────────────────║
║  2 Link   │  LAN delivery, MAC     │  NIC driver, bridge, veth   ║
║  ─────────┼────────────────────────┼─────────────────────────────║
║  1 Phys   │  Bits on wire          │  NIC hardware, cables       ║
╠══════════════════════════════════════════════════════════════════╣
║  Cross-cutting concerns:                                         ║
║    sk_buff      → packet representation throughout stack        ║
║    Netfilter    → hooks at every layer (firewall/NAT)           ║
║    eBPF/XDP     → programmable data plane                       ║
║    tc           → QoS and traffic shaping                       ║
║    net namespaces → isolation (containers, VRF)                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*Guide created for mastery-level study of Linux networking internals.*
*Applicable to kernel versions 5.x and 6.x.*
*Cross-reference with: `man 7 socket`, `man 7 ip`, `man 7 tcp`, `man 8 ip`, `man 8 tc`, `man 8 iptables`*

Here is your complete, in-depth guide to Linux Networking Layers. Here's what's covered across **21 deep sections**:

**Foundations**
- Why layers exist (mental model first, then mechanics)
- OSI 7-layer model with encapsulation/decapsulation diagrams
- TCP/IP model and how it maps to the Linux kernel

**Layer-by-Layer Deep Dives**
- **L1 Physical** — signals, MTU, `ethtool`
- **L2 Data Link** — Ethernet frame anatomy, MAC addresses, ARP (with full diagram), VLANs, NAPI
- **L3 Network** — IPv4/IPv6 headers (bit-level), CIDR/subnetting, ICMP, routing with **Longest Prefix Match**, Policy Routing, NAT
- **L4 Transport** — TCP header, 3-way & 4-way handshake, full **state machine diagram**, sliding window flow control, congestion control (Slow Start → CA → BBR), UDP vs TCP decision tree

**Kernel Internals**
- **Socket layer** — `struct sock`, syscall boundary, zero-copy I/O
- **sk_buff** — the packet's nervous system, efficient pointer-based header add/remove
- **Netfilter/iptables** — all 5 hooks, tables, conntrack, nftables
- **Routing subsystem** — FIB trie, ECMP, policy routing
- **tc/qdisc** — HTB, netem (simulate bad networks), shaping

**Modern Data Plane**
- **XDP + eBPF** — full C example of XDP program, hook points, maps
- **Network device drivers** — TX/RX ring buffer, interrupt → NAPI path

**End-to-End**
- Full `curl https://example.com` packet journey narrated step-by-step
- Complete receive-side flowchart
- Performance tuning (`sysctl` parameters, BDP formula, RSS, offloads)
- Debugging toolkit with a **decision tree** for diagnosing problems

**Expert Mental Models**
- Layered contract model, state machine model, chunking strategy, diagnostic pattern recognition table