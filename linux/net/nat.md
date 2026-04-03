# The Complete Linux NAT Guide
## NAT · SNAT · DNAT · MASQUERADE · REDIRECT · TPROXY · and Beyond

> "To understand a network is to understand the flow of truth through wires."  
> A world-class systems guide for engineers who think in packets.

---

## Table of Contents

1. [Foundational Concepts — Before NAT Makes Sense](#1-foundational-concepts)
2. [The OSI Model and Where NAT Lives](#2-osi-model)
3. [IP Addressing — Private vs Public Space](#3-ip-addressing)
4. [What Is NAT? (Network Address Translation)](#4-what-is-nat)
5. [The Linux Netfilter Framework — The Engine Behind NAT](#5-netfilter-framework)
6. [Connection Tracking (conntrack) — The Memory of NAT](#6-connection-tracking)
7. [iptables — The Classic NAT Tool](#7-iptables)
8. [nftables — The Modern NAT Tool](#8-nftables)
9. [SNAT — Source NAT](#9-snat)
10. [DNAT — Destination NAT](#10-dnat)
11. [MASQUERADE — Dynamic SNAT](#11-masquerade)
12. [REDIRECT — Local Port Redirect](#12-redirect)
13. [TPROXY — Transparent Proxy](#13-tproxy)
14. [Full Cone NAT, Symmetric NAT, Restricted NAT](#14-nat-types-classification)
15. [Static NAT](#15-static-nat)
16. [Dynamic NAT](#16-dynamic-nat)
17. [PAT — Port Address Translation](#17-pat)
18. [Hairpin NAT / NAT Reflection / Loopback NAT](#18-hairpin-nat)
19. [Double NAT](#19-double-nat)
20. [Carrier-Grade NAT (CGNAT)](#20-cgnat)
21. [NAT64 and DNS64 — IPv6 Transition](#21-nat64)
22. [NAT Traversal Techniques (STUN, TURN, ICE, UPnP)](#22-nat-traversal)
23. [Linux Kernel Internals — How NAT Works at the Code Level](#23-kernel-internals)
24. [The /proc and /sys NAT Interfaces](#24-proc-sys-interfaces)
25. [ip rule and ip route — Policy Routing with NAT](#25-policy-routing)
26. [Network Namespaces and NAT](#26-network-namespaces)
27. [Docker / Kubernetes NAT Internals](#27-container-nat)
28. [eBPF / XDP NAT — The Future](#28-ebpf-nat)
29. [C Implementation — Raw Socket NAT Engine](#29-c-implementation)
30. [Rust Implementation — Safe NAT Engine](#30-rust-implementation)
31. [Performance Tuning NAT](#31-performance-tuning)
32. [NAT Troubleshooting & Debugging](#32-troubleshooting)
33. [Security Implications of NAT](#33-security)
34. [Real-World Architectures](#34-real-world)
35. [Complete Command Reference](#35-command-reference)

---

# 1. Foundational Concepts

> Before we touch a single iptables rule, you must have crystal-clear mental models.
> Every expert shortcut is built on a foundation of deep fundamentals.

## 1.1 What Is a Packet?

A **packet** is the basic unit of data transmitted over a network. Think of it like a letter:

```
+--------------------------------------------------+
|  ENVELOPE (Headers)                              |
|  From:  192.168.1.10:54321  (source IP:port)     |
|  To:    8.8.8.8:53          (destination IP:port)|
|  Protocol: UDP                                   |
+--------------------------------------------------+
|  LETTER CONTENT (Payload)                        |
|  "What is the IP address of google.com?"         |
+--------------------------------------------------+
```

When this packet travels through the internet:
- Routers read the **envelope** (headers)
- Routers forward based on the **destination address**
- The content (payload) is generally not inspected

## 1.2 What Is an IP Address?

An **IP address** (Internet Protocol address) is a unique numerical label assigned to every device on a network.

### IPv4

IPv4 addresses are **32-bit numbers** written as 4 octets (bytes) separated by dots:

```
192  .  168  .   1   .  10
 |        |       |      |
 8 bits  8 bits  8 bits  8 bits
 (0-255) (0-255) (0-255) (0-255)
```

Total IPv4 space: 2^32 = **4,294,967,296 addresses** (~4.3 billion)

### IPv6

IPv6 addresses are **128-bit numbers** written in hexadecimal:

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

Total IPv6 space: 2^128 ≈ **340 undecillion** (practically infinite)

## 1.3 What Is a Port?

A **port** is a 16-bit number (0–65535) that identifies a specific **process or service** on a host.

```
IP Address = Which building (host)
Port       = Which apartment (service/process)
```

Common ports:
| Port | Service |
|------|---------|
| 22   | SSH     |
| 80   | HTTP    |
| 443  | HTTPS   |
| 53   | DNS     |
| 3306 | MySQL   |

### Port Categories:
- **0–1023**: Well-known ports (root required to bind)
- **1024–49151**: Registered ports
- **49152–65535**: Ephemeral ports (used by clients for temporary connections)

## 1.4 What Is a Socket?

A **socket** is the combination of IP address + port + protocol that uniquely identifies a connection endpoint:

```
Socket = IP:Port (e.g., 192.168.1.10:54321)
```

A **connection** (TCP) is defined by a **4-tuple**:

```
(src_ip, src_port, dst_ip, dst_port)
e.g.:
(192.168.1.10, 54321, 8.8.8.8, 53)
```

This 4-tuple is crucial. NAT operates by **rewriting parts of this 4-tuple**.

## 1.5 What Is a Protocol?

The **protocol** field in an IP header tells the OS how to interpret the payload:

| Number | Protocol |
|--------|----------|
| 6      | TCP      |
| 17     | UDP      |
| 1      | ICMP     |
| 47     | GRE      |
| 50     | ESP (IPSec) |

### TCP vs UDP — Why It Matters for NAT

```
TCP (Transmission Control Protocol):
  - Connection-oriented (3-way handshake)
  - Reliable (acknowledgments, retransmission)
  - Ordered delivery
  - Stateful — NAT must track connections

     Client          Server
       |---SYN-------->|   (I want to connect)
       |<--SYN+ACK-----|   (OK, let's connect)
       |---ACK-------->|   (Connected!)
       |                |
       |---DATA------->|
       |<--ACK---------|
       |                |
       |---FIN-------->|   (I'm done)
       |<--FIN+ACK-----|
       |---ACK-------->|

UDP (User Datagram Protocol):
  - Connectionless
  - No reliability guarantee
  - No ordering
  - Fire-and-forget
  - NAT must use timers to track "connections"
```

## 1.6 What Is a Router?

A **router** is a device that forwards packets between different networks. It operates at **Layer 3** (Network layer) of the OSI model.

```
Network A           Router           Network B
192.168.1.0/24 -----|    |------ 10.0.0.0/8
                     |    |
                  Routing
                   Table:
                  192.168.1.0/24 → eth0
                  10.0.0.0/8     → eth1
                  0.0.0.0/0      → ISP
```

Linux can act as a router with:
```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
```

## 1.7 What Is a Subnet?

A **subnet** (subnetwork) is a subdivision of an IP network. Defined using **CIDR notation**:

```
192.168.1.0/24

/24 means 24 bits are the "network" part:
11000000.10101000.00000001.XXXXXXXX
└─────────────────────────┘└───────┘
         Network (fixed)    Host (variable)

Range: 192.168.1.0 to 192.168.1.255
Usable: 192.168.1.1 to 192.168.1.254 (254 hosts)
```

Common subnet sizes:
| CIDR | Hosts  | Example               |
|------|--------|-----------------------|
| /8   | 16M    | 10.0.0.0/8            |
| /16  | 65534  | 172.16.0.0/16         |
| /24  | 254    | 192.168.1.0/24        |
| /30  | 2      | Point-to-point links  |
| /32  | 1      | Single host           |

---

# 2. The OSI Model and Where NAT Lives

## 2.1 The 7-Layer OSI Model

```
Layer 7 — Application   : HTTP, DNS, FTP, SSH
Layer 6 — Presentation  : TLS/SSL, encoding
Layer 5 — Session       : Session management
Layer 4 — Transport     : TCP, UDP (ports)
Layer 3 — Network       : IP addresses, routing  ← NAT operates HERE
Layer 2 — Data Link     : MAC addresses, Ethernet frames
Layer 1 — Physical      : Bits on wire
```

### How a Packet Travels Down the Stack (Sender):

```
Application says: "Send 'Hello' to 8.8.8.8:80"
         ↓
Transport adds:  src_port=54321, dst_port=80, TCP header
         ↓
Network adds:    src_ip=192.168.1.10, dst_ip=8.8.8.8, IP header
         ↓
Data Link adds:  src_mac=AA:BB:..., dst_mac=gateway_mac, Ethernet frame
         ↓
Physical:        01001000 10110010 ... (bits on wire)
```

### How a Packet Travels Up the Stack (Receiver):

```
Physical receives bits
         ↓
Data Link strips Ethernet frame, checks MAC
         ↓
Network strips IP header, checks destination IP
         ↓
Transport strips TCP header, checks destination port
         ↓
Application receives payload: "Hello"
```

## 2.2 Where Exactly Does NAT Operate?

NAT operates at **Layer 3 (Network)** but must read **Layer 4 (Transport)** headers to handle port translation. This is sometimes called **Layer 3.5** or **Layer 4 NAT**.

```
Packet traveling through Linux NAT router:

  Incoming Packet (Wire)
        ↓
  [Layer 2: Ethernet] ← check MAC, strip frame
        ↓
  [Layer 3: IP]       ← check dst IP, routing decision
        ↓
  [Netfilter Hooks]   ← NAT, filtering happens here
        ↓
  [Layer 3: IP]       ← rewrite src/dst IP
  [Layer 4: TCP/UDP]  ← rewrite src/dst port
        ↓
  [Layer 2: Ethernet] ← add new MAC header
        ↓
  Outgoing Packet (Wire)
```

---

# 3. IP Addressing — Private vs Public Space

## 3.1 Public IP Addresses

**Public IPs** are globally routable — any device on the internet can reach them directly.

They are assigned by:
- IANA (Internet Assigned Numbers Authority) globally
- RIRs (Regional Internet Registries): ARIN, RIPE, APNIC, LACNIC, AFRINIC
- ISPs allocate to customers

## 3.2 Private IP Addresses (RFC 1918)

**Private IPs** are reserved for internal use only. They are **NOT routable on the internet**.

| Range                       | CIDR             | Size       |
|-----------------------------|------------------|------------|
| 10.0.0.0 – 10.255.255.255  | 10.0.0.0/8       | 16 million |
| 172.16.0.0 – 172.31.255.255| 172.16.0.0/12    | 1 million  |
| 192.168.0.0 – 192.168.255.255| 192.168.0.0/16 | 65,534     |

### The Core Problem NAT Solves:

```
Problem:
  Your home has 10 devices.
  You only get 1 public IP from your ISP.
  Private IPs can't be routed on the internet.

Before NAT:
  Device A: 192.168.1.10 wants to reach 8.8.8.8
  Router sends packet with src=192.168.1.10
  8.8.8.8 tries to reply to 192.168.1.10
  ❌ FAILS — 192.168.1.10 is not routable on internet!

After NAT:
  Device A: 192.168.1.10 wants to reach 8.8.8.8
  Router REWRITES src=192.168.1.10 to src=203.0.113.1 (public IP)
  8.8.8.8 replies to 203.0.113.1 ✓
  Router REWRITES dst=203.0.113.1 back to dst=192.168.1.10
  Device A receives the reply ✓
```

## 3.3 Other Special IP Ranges

| Range            | Purpose                          |
|------------------|----------------------------------|
| 127.0.0.0/8      | Loopback (localhost)             |
| 169.254.0.0/16   | Link-local (APIPA)               |
| 100.64.0.0/10    | Shared address space (CGNAT)     |
| 0.0.0.0/8        | "This" network                   |
| 255.255.255.255  | Broadcast                        |
| 224.0.0.0/4      | Multicast                        |

---

# 4. What Is NAT? (Network Address Translation)

## 4.1 Core Definition

**NAT (Network Address Translation)** is the process of modifying IP address (and optionally port) information in packet headers while packets are in transit through a routing device.

```
FUNDAMENTAL NAT OPERATION:

Packet BEFORE NAT:                Packet AFTER NAT:
+------------------+              +------------------+
| src: 192.168.1.10|    SNAT      | src: 203.0.113.1 |
| dst: 8.8.8.8     |  ========>  | dst: 8.8.8.8     |
| sport: 54321     |             | sport: 40001     |
| dport: 53        |             | dport: 53        |
+------------------+             +------------------+
    Private host                     Public router
```

## 4.2 The NAT Translation Table

NAT must remember what it changed so it can **reverse the translation** for reply packets:

```
NAT TRANSLATION TABLE (conntrack):

Original                      Translated
(src_ip, src_port)     →     (new_src_ip, new_src_port)
(192.168.1.10, 54321)  →     (203.0.113.1, 40001)
(192.168.1.10, 54322)  →     (203.0.113.1, 40002)
(192.168.1.20, 60000)  →     (203.0.113.1, 40003)
(192.168.1.30, 1024)   →     (203.0.113.1, 40004)
```

When a reply comes back to 203.0.113.1:40001, the NAT engine looks up the table and rewrites it back to 192.168.1.10:54321.

## 4.3 The Complete Flow

```
HOME NETWORK EXAMPLE:

Devices:                        Internet:
192.168.1.10 (PC)    ┐
192.168.1.20 (Phone) ├──→  [Linux Router/NAT] ──→ 8.8.8.8
192.168.1.30 (TV)    ┘     203.0.113.1 (Public)

STEP-BY-STEP FLOW:

① PC (192.168.1.10:54321) sends DNS query to 8.8.8.8:53
   Packet: [src=192.168.1.10:54321 | dst=8.8.8.8:53 | "what is google.com?"]

② Router receives packet on eth0 (LAN side)
   ip_forward is enabled → packet goes to FORWARD chain

③ NAT (POSTROUTING/SNAT) rewrites source:
   [src=203.0.113.1:40001 | dst=8.8.8.8:53 | "what is google.com?"]

④ Router stores in conntrack:
   192.168.1.10:54321 <→> 203.0.113.1:40001

⑤ 8.8.8.8 receives query, sees src=203.0.113.1:40001
   Sends reply: [src=8.8.8.8:53 | dst=203.0.113.1:40001 | "google.com=142.250.80.46"]

⑥ Router receives reply, looks up conntrack:
   203.0.113.1:40001 → 192.168.1.10:54321

⑦ NAT (PREROUTING/DNAT) rewrites destination:
   [src=8.8.8.8:53 | dst=192.168.1.10:54321 | "google.com=142.250.80.46"]

⑧ PC receives the reply ✓
```

## 4.4 Classification of NAT Types

```
NAT
├── By What Gets Changed:
│   ├── SNAT (Source NAT)       — changes source IP/port
│   ├── DNAT (Destination NAT) — changes destination IP/port
│   └── Full NAT               — changes both
│
├── By Translation Method:
│   ├── Static NAT             — 1:1 permanent mapping
│   ├── Dynamic NAT            — pool of IPs, mapping on demand
│   └── PAT/NAPT               — many:1 using ports
│
├── By Behavior (RFC 4787):
│   ├── Full Cone NAT          — most open
│   ├── Address-Restricted Cone NAT
│   ├── Port-Restricted Cone NAT
│   └── Symmetric NAT          — most restrictive
│
└── By Special Feature:
    ├── MASQUERADE             — SNAT with dynamic IP detection
    ├── REDIRECT               — redirect to local port
    ├── TPROXY                 — transparent proxy
    ├── Hairpin NAT            — inside→inside via public IP
    ├── CGNAT                  — carrier-grade (100.64.0.0/10)
    └── NAT64                  — IPv6 to IPv4 translation
```

---

# 5. The Linux Netfilter Framework — The Engine Behind NAT

## 5.1 What Is Netfilter?

**Netfilter** is a framework built into the Linux kernel that provides hooks into the network stack. Every tool you use for NAT (iptables, nftables, ipset, conntrack) is built on top of Netfilter.

```
USER SPACE                         KERNEL SPACE
─────────────────────────────────────────────────
iptables   }                     Netfilter
nftables   }──── communicate ──→ Framework
ipset      }     via syscalls    (kernel hooks)
conntrack  }
```

## 5.2 The 5 Netfilter Hooks

Netfilter defines **5 hook points** where it can intercept packets. Understanding these hooks is CRITICAL to understanding how NAT rules work.

```
                    ┌──────────────────────┐
                    │   Linux Kernel       │
                    │   Network Stack      │
                    └──────────────────────┘

Packet arrives on NIC
         │
         ▼
    ┌────────────┐
    │ PREROUTING │  ← Hook 1: FIRST hook, before routing decision
    │   Hook     │             DNAT happens here (change destination)
    └─────┬──────┘
          │
    ┌─────▼──────────────────────────────────────┐
    │           ROUTING DECISION                  │
    │   "Is this packet for ME or to FORWARD?"    │
    └──────────┬──────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
 ┌────────────┐  ┌────────────┐
 │   INPUT    │  │  FORWARD   │  ← Hook 3: For forwarded packets
 │   Hook 2   │  │   Hook     │
 └─────┬──────┘  └─────┬──────┘
       │               │
  (to local           │
   process)           │
       │               │
       ▼               ▼
  ┌──────────────────────────┐
  │  Local process /         │
  │  ROUTING DECISION        │
  └────────────┬─────────────┘
               │
         ┌─────▼──────┐
         │POSTROUTING │  ← Hook 5: LAST hook, after routing decision
         │   Hook     │             SNAT happens here (change source)
         └─────┬──────┘
               │
               ▼
     Packet leaves on NIC

Hook 4 = OUTPUT (from local process to network)
```

### Complete Flow Diagram:

```
                     INCOMING PACKET
                           │
                           ▼
                    ┌─────────────┐
                    │ PREROUTING  │ (NF_INET_PRE_ROUTING)
                    │ • raw       │  ← Hook 1
                    │ • mangle    │
                    │ • nat(DNAT) │
                    └──────┬──────┘
                           │
              ┌────────────▼───────────────┐
              │      ROUTING DECISION       │
              └──────┬──────────────┬───────┘
                     │              │
              (local dest)    (foreign dest)
                     │              │
              ┌──────▼──────┐ ┌─────▼──────┐
              │    INPUT    │ │  FORWARD   │
              │ • raw       │ │ • mangle   │
              │ • mangle    │ │ • filter   │
              │ • filter    │ └──────┬─────┘
              └──────┬──────┘        │
                     │              │
              (local process)       │
                     │              │
              ┌──────▼──────┐       │
              │   OUTPUT    │       │
              │ • raw       │       │
              │ • mangle    │       │
              │ • nat(DNAT) │       │
              │ • filter    │       │
              └──────┬──────┘       │
                     │              │
              ┌──────▼──────────────▼───────┐
              │        POSTROUTING          │
              │ • mangle                    │
              │ • nat (SNAT/MASQUERADE)     │
              └─────────────────────────────┘
                            │
                     OUTGOING PACKET
```

## 5.3 Netfilter Tables

Each hook can contain rules organized into **tables**. The tables in order of priority:

| Table   | Purpose                                     | Chains                              |
|---------|---------------------------------------------|-------------------------------------|
| raw     | Very early processing, connection tracking bypass | PREROUTING, OUTPUT            |
| mangle  | Packet modification (TTL, TOS, mark)        | All 5 chains                        |
| nat     | Address/port translation                    | PREROUTING, INPUT, OUTPUT, POSTROUTING |
| filter  | Packet filtering (accept/drop)              | INPUT, FORWARD, OUTPUT              |
| security| SELinux/AppArmor security labels            | INPUT, FORWARD, OUTPUT              |

### Priority Order (lower number = higher priority):

```
Priority numbers for hook processing:
NF_IP_PRI_RAW_BEFORE_DEFRAG = -450
NF_IP_PRI_CONNTRACK_DEFRAG  = -400
NF_IP_PRI_RAW               = -300   ← raw table
NF_IP_PRI_SELINUX_FIRST     = -225
NF_IP_PRI_CONNTRACK         = -200   ← conntrack (before NAT!)
NF_IP_PRI_MANGLE            = -150   ← mangle table
NF_IP_PRI_NAT_DST           = -100   ← nat table DNAT
NF_IP_PRI_FILTER            =  0     ← filter table
NF_IP_PRI_SECURITY          =  50    ← security table
NF_IP_PRI_NAT_SRC           =  100   ← nat table SNAT/MASQUERADE
```

### The Verdict System

Each hook returns a **verdict** for each packet:

| Verdict         | Meaning                                    |
|-----------------|--------------------------------------------|
| NF_ACCEPT       | Continue processing                        |
| NF_DROP         | Drop the packet silently                   |
| NF_STOLEN       | Packet taken by the hook, don't process    |
| NF_QUEUE        | Queue to userspace                         |
| NF_REPEAT       | Call the hook again                        |
| NF_STOP         | Stop hook traversal, accept                |

## 5.4 Netfilter Architecture (Kernel Internals Overview)

```
Kernel Module Structure:

┌─────────────────────────────────────────────────────┐
│                   nf_tables.ko                       │ ← nftables
│                   ip_tables.ko                       │ ← iptables
│                   xt_nat.ko                          │ ← NAT target
│                   nf_nat_ipv4.ko                     │ ← IPv4 NAT
│                   nf_nat.ko                          │ ← core NAT
│                   nf_conntrack_ipv4.ko               │ ← IPv4 conntrack
│                   nf_conntrack.ko                    │ ← core conntrack
│                   x_tables.ko                        │ ← iptables framework
└─────────────────────────────────────────────────────┘
              ↕ (all built on)
┌─────────────────────────────────────────────────────┐
│                  netfilter core                      │
│         (net/netfilter/core.c in kernel)             │
└─────────────────────────────────────────────────────┘
```

---

# 6. Connection Tracking (conntrack) — The Memory of NAT

## 6.1 Why Is Connection Tracking Needed?

NAT is **stateful**. When a packet leaves with modified headers, the system must remember:
- What the original headers were
- How to reverse the translation for reply packets

This is the job of **conntrack** (connection tracking), which is a subsystem of Netfilter.

> **Key Insight**: NAT without conntrack is impossible for bi-directional traffic. conntrack is what makes NAT "work" — it's the lookup table in our brain analogy.

## 6.2 Connection States

conntrack tracks packets in **states**:

| State       | Meaning                                              |
|-------------|------------------------------------------------------|
| NEW         | First packet of a connection (SYN for TCP)           |
| ESTABLISHED | Connection is established, packets flowing both ways |
| RELATED     | Related to an established connection (e.g., FTP data)|
| INVALID     | Doesn't match any connection                         |
| UNTRACKED   | Deliberately excluded from tracking (raw table)      |
| SNAT        | Packets being source-NATted                          |
| DNAT        | Packets being destination-NATted                     |

### State Machine for TCP:

```
                          ┌─────────┐
                          │  NONE   │
                          └────┬────┘
                               │ SYN received
                               ▼
                          ┌─────────┐
                          │   NEW   │ ← First SYN
                          └────┬────┘
                               │ SYN-ACK seen
                               ▼
                       ┌───────────────┐
                       │  ESTABLISHED  │ ← SYN+ACK, ACK
                       └───────┬───────┘
                               │ FIN seen
                               ▼
                       ┌───────────────┐
                       │  TIME_WAIT    │
                       └───────┬───────┘
                               │ timeout
                               ▼
                          ┌─────────┐
                          │  NONE   │
                          └─────────┘
```

## 6.3 Conntrack Entry Structure

Each tracked connection has an entry with:

```
conntrack entry:
┌────────────────────────────────────────────────────────┐
│  Original direction:                                   │
│    src: 192.168.1.10:54321  dst: 8.8.8.8:53           │
│    proto: UDP                                          │
│                                                        │
│  Reply direction (what replies should look like):      │
│    src: 8.8.8.8:53         dst: 203.0.113.1:40001     │
│    → NAT will rewrite dst: 203.0.113.1:40001          │
│      back to dst: 192.168.1.10:54321                   │
│                                                        │
│  State:      ESTABLISHED                               │
│  Timeout:    30 seconds (UDP)                          │
│  Status:     SNAT, SEEN_REPLY                          │
└────────────────────────────────────────────────────────┘
```

## 6.4 Viewing conntrack Entries

```bash
# Install conntrack tools
apt install conntrack

# View all connections
conntrack -L

# View only NAT'd connections
conntrack -L | grep SNAT

# Watch connections in real time
conntrack -E

# Count connections by state
conntrack -L | awk '{print $4}' | sort | uniq -c

# View specific protocol
conntrack -L -p tcp

# Delete a specific connection
conntrack -D -s 192.168.1.10 -p tcp --sport 54321

# Example output:
# tcp      6 431999 ESTABLISHED src=192.168.1.10 dst=8.8.8.8 sport=54321 dport=80 
#          src=8.8.8.8 dst=203.0.113.1 sport=80 dport=40001 [ASSURED] mark=0 use=1
```

### Reading conntrack output:

```
tcp      6 431999   ESTABLISHED   src=192.168.1.10 dst=8.8.8.8 sport=54321 dport=80
│        │ │         │             └──────────────── ORIGINAL DIRECTION ─────────────
│        │ │         │
│        │ │         └── Connection state
│        │ └── Timeout remaining (seconds)
│        └── Protocol number (6=TCP)
└── Protocol name

src=8.8.8.8 dst=203.0.113.1 sport=80 dport=40001 [ASSURED] mark=0 use=1
└──────────────── REPLY DIRECTION ─────────────────────────────────────
The reply packets are expected to look like this.
NAT reversal: when dst=203.0.113.1:40001, rewrite to 192.168.1.10:54321
```

## 6.5 conntrack Tuning

```bash
# View current limits
cat /proc/sys/net/netfilter/nf_conntrack_max
cat /proc/sys/net/netfilter/nf_conntrack_count  # current

# Increase limit (important for high-traffic NAT)
echo 1000000 > /proc/sys/net/netfilter/nf_conntrack_max

# Or permanently in /etc/sysctl.conf:
net.netfilter.nf_conntrack_max = 1000000

# View hashsize (bucket count in hash table)
cat /sys/module/nf_conntrack/parameters/hashsize

# Set hashsize (should be ~1/4 of max)
echo 262144 > /sys/module/nf_conntrack/parameters/hashsize

# View timeouts for different protocols
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_established  # 432000s = 5 days!
cat /proc/sys/net/netfilter/nf_conntrack_udp_timeout              # 30s
cat /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream       # 180s

# Reduce TCP established timeout (saves memory on high-traffic servers)
echo 86400 > /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_established
```

## 6.6 conntrack Helpers — RELATED State

Some protocols open secondary connections (like FTP). conntrack **helpers** track these:

```
FTP Example:
  Client: 192.168.1.10
  FTP Server: 203.0.113.2

  Control connection: 192.168.1.10:54321 → 203.0.113.2:21
  Server says "connect to port 35000 for data"

  Without conntrack helper:
    Data connection: 203.0.113.2:20 → 192.168.1.10:35000
    ❌ BLOCKED by firewall (new unsolicited connection)

  With nf_conntrack_ftp helper:
    Helper parses FTP commands, sees PORT/PASV
    Creates EXPECT entry for data connection
    Data connection is marked RELATED → ✓ ALLOWED
```

Available conntrack helpers:
- `nf_conntrack_ftp` — FTP active/passive
- `nf_conntrack_irc` — IRC DCC connections
- `nf_conntrack_h323` — H.323 VoIP
- `nf_conntrack_sip` — SIP VoIP
- `nf_conntrack_tftp` — TFTP
- `nf_conntrack_pptp` — PPTP VPN
- `nf_conntrack_amanda` — Amanda backup

---

# 7. iptables — The Classic NAT Tool

## 7.1 iptables Architecture

**iptables** is the traditional userspace tool for configuring Netfilter. It operates on IPv4. For IPv6, use **ip6tables** (same syntax).

```
iptables COMMAND [TABLE] CHAIN [MATCH_OPTIONS] [TARGET]

Components:
  TABLE   : which table (-t nat, -t filter, -t mangle, -t raw)
  CHAIN   : which chain (PREROUTING, POSTROUTING, INPUT, FORWARD, OUTPUT)
  MATCH   : packet matching criteria (-s, -d, -p, --sport, --dport, -i, -o)
  TARGET  : what to do (-j ACCEPT, -j DROP, -j SNAT, -j DNAT, -j MASQUERADE)
```

## 7.2 iptables Command Reference

```bash
# General syntax
iptables [-t TABLE] COMMAND CHAIN [MATCHES] -j TARGET

# Commands:
-A  : Append rule to end of chain
-I  : Insert rule at position (default: position 1)
-D  : Delete rule
-R  : Replace rule at position
-L  : List rules
-F  : Flush (delete all rules in chain)
-Z  : Zero counters
-N  : New user-defined chain
-X  : Delete user-defined chain
-P  : Set default policy
-n  : Numeric output (don't resolve hostnames)
-v  : Verbose output
--line-numbers : Show rule numbers

# Common matches:
-s SOURCE_IP          : Match source IP (or range with CIDR)
-d DEST_IP            : Match destination IP
-p PROTOCOL           : Match protocol (tcp, udp, icmp)
-i INTERFACE          : Match input interface
-o INTERFACE          : Match output interface
--sport PORT          : Match source port (requires -p)
--dport PORT          : Match destination port (requires -p)
-m state --state      : Match connection state (with xt_state)
-m conntrack --ctstate: Match conntrack state (with xt_conntrack)
```

## 7.3 Listing and Saving Rules

```bash
# List NAT rules with details
iptables -t nat -L -n -v --line-numbers

# List all tables
for table in raw mangle nat filter; do
    echo "=== TABLE: $table ==="
    iptables -t $table -L -n -v
done

# Save rules
iptables-save > /etc/iptables/rules.v4

# Restore rules
iptables-restore < /etc/iptables/rules.v4

# Flush all NAT rules (careful!)
iptables -t nat -F

# View packet/byte counters
iptables -t nat -L -n -v
# Output:
# Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
#  pkts bytes target     prot opt in     out     source               destination
#  1234 567K  MASQUERADE  all  --  *      eth0    192.168.0.0/24       0.0.0.0/0
```

## 7.4 iptables Modules (Extensions)

```bash
# Load a match extension with -m
-m comment --comment "my rule"    # Add human-readable comments
-m multiport --dports 80,443      # Match multiple ports
-m iprange --src-range IP1-IP2    # Match IP range
-m mac --mac-source AA:BB:CC:..   # Match MAC address
-m limit --limit 10/min           # Rate limiting
-m recent                         # Track recent connections
-m string --string "GET /"        # Deep packet inspection
-m connlimit --connlimit-above 10 # Connection count limit
-m owner --uid-owner 1000         # Match by process owner
-m mark --mark 0x1                # Match packet mark
-m addrtype --dst-type LOCAL      # Match address type
-m hashlimit                      # Per-host rate limiting
```

---

# 8. nftables — The Modern NAT Tool

## 8.1 Why nftables?

**nftables** was introduced in Linux 3.13 as the successor to iptables. Key improvements:

| Feature         | iptables          | nftables             |
|-----------------|-------------------|----------------------|
| Performance     | Linear rule scan  | Hash/map lookups     |
| Syntax          | Complex, verbose  | Cleaner, unified     |
| IPv4/IPv6       | Separate tools    | Single ruleset       |
| Tables/chains   | Fixed             | User-defined         |
| Sets            | External (ipset)  | Built-in             |
| Debugging       | Limited           | Packet tracing       |
| Atomicity       | Per-table         | Per-ruleset          |

## 8.2 nftables Concepts

```
nftables HIERARCHY:

Table        : Top-level namespace (you name it)
  └── Chain  : Where rules live (you choose hook/priority)
       └── Rule  : Match + Statement (ACCEPT/DROP/NAT/etc.)
            └── Expression : Specific match or action
```

## 8.3 nftables Basic Syntax

```nft
# Create a table
nft add table ip mynat

# Create chains (you must specify hook, priority, policy)
nft add chain ip mynat prerouting { type nat hook prerouting priority -100\; policy accept\; }
nft add chain ip mynat postrouting { type nat hook postrouting priority 100\; policy accept\; }
nft add chain ip mynat input { type filter hook input priority 0\; policy accept\; }
nft add chain ip mynat forward { type filter hook forward priority 0\; policy accept\; }
nft add chain ip mynat output { type nat hook output priority -100\; policy accept\; }

# Add SNAT rule
nft add rule ip mynat postrouting oifname "eth0" ip saddr 192.168.0.0/24 snat to 203.0.113.1

# Add MASQUERADE
nft add rule ip mynat postrouting oifname "eth0" masquerade

# Add DNAT
nft add rule ip mynat prerouting iifname "eth0" tcp dport 80 dnat to 192.168.0.10:8080

# List rules
nft list ruleset

# Save/restore
nft list ruleset > /etc/nftables.conf
nft -f /etc/nftables.conf

# Delete table
nft delete table ip mynat
```

## 8.4 nftables Sets and Maps (Powerful Features)

```nft
# Create a set of IPs
nft add set ip mynat blocked_ips { type ipv4_addr\; }
nft add element ip mynat blocked_ips { 10.0.0.1, 10.0.0.2 }

# Use set in rule
nft add rule ip mynat forward ip saddr @blocked_ips drop

# Create a map for DNAT (port → server mapping)
nft add map ip mynat port_map { type inet_service : ipv4_addr . inet_service\; }
nft add element ip mynat port_map { 80 : 192.168.0.10 . 8080 }
nft add element ip mynat port_map { 443 : 192.168.0.10 . 8443 }

# Use map for DNAT
nft add rule ip mynat prerouting dnat tcp dport map @port_map
```

## 8.5 Complete nftables Ruleset Example

```nft
#!/usr/sbin/nft -f

# Clear everything
flush ruleset

# IPv4 NAT table
table ip nat {
    # DNAT chain
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        
        # Port forward: external:80 → internal:192.168.0.10:8080
        iifname "eth0" tcp dport 80 dnat to 192.168.0.10:8080
        
        # Port forward: external:443 → internal server
        iifname "eth0" tcp dport 443 dnat to 192.168.0.10:8443
        
        # RDP forwarding
        iifname "eth0" tcp dport 3389 dnat to 192.168.0.20:3389
    }
    
    # SNAT chain
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        
        # Masquerade outgoing from LAN
        oifname "eth0" ip saddr 192.168.0.0/24 masquerade
    }
}

# Filter table
table ip filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iifname "lo" accept
        tcp dport 22 accept
        drop
    }
    
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established,related accept
        iifname "eth1" oifname "eth0" accept  # LAN → WAN
        iifname "eth0" ct state related,established accept
        drop
    }
    
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

---

# 9. SNAT — Source NAT

## 9.1 What Is SNAT?

**SNAT (Source NAT)** rewrites the **source** IP address (and optionally the source port) of outgoing packets.

**When is it needed?**
- Private hosts need to communicate with the internet
- Load balancing from multiple sources through one IP
- Changing the "return" address of outgoing traffic

```
SNAT OPERATION:

Client (private)    Router               Server (internet)
192.168.1.10:54321 ─── SNAT ──→ 203.0.113.1:40001 ──→ 8.8.8.8:53

Step by step:
① Original:  src=192.168.1.10:54321  dst=8.8.8.8:53
② After SNAT: src=203.0.113.1:40001  dst=8.8.8.8:53
③ Reply:      src=8.8.8.8:53         dst=203.0.113.1:40001
④ After DNAT: src=8.8.8.8:53         dst=192.168.1.10:54321
   (automatic reverse DNAT by conntrack)
```

## 9.2 Where Does SNAT Happen?

SNAT happens in the **POSTROUTING** chain (after routing decision) in the **nat** table.

```
Packet flow for SNAT:

  Packet from 192.168.1.10
         │
    PREROUTING (nat) — no DNAT rule matches
         │
   Routing: packet is FORWARDED (not local)
         │
    FORWARD (filter) — if allowed
         │
   POSTROUTING (nat) — ← SNAT HAPPENS HERE
    "Rewrite src from 192.168.1.10:54321 to 203.0.113.1:40001"
         │
   Packet exits on eth0 with src=203.0.113.1:40001
```

## 9.3 SNAT with iptables

```bash
# Basic SNAT: change source to specific IP
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -s 192.168.1.0/24 \
    -j SNAT --to-source 203.0.113.1

# SNAT with specific source port range
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -s 192.168.1.0/24 \
    -j SNAT --to-source 203.0.113.1:1024-65535

# SNAT to one of a pool of IPs (round-robin)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j SNAT --to-source 203.0.113.1-203.0.113.5

# SNAT only for specific protocol
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -p tcp \
    -s 192.168.1.0/24 \
    --dport 80 \
    -j SNAT --to-source 203.0.113.1

# SNAT for specific destination (useful for split routing)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -s 192.168.1.0/24 \
    -d 0.0.0.0/0 \
    -j SNAT --to-source 203.0.113.1
```

## 9.4 SNAT with nftables

```nft
# Basic SNAT
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        
        # Simple SNAT
        oifname "eth0" ip saddr 192.168.1.0/24 snat to 203.0.113.1
        
        # SNAT with port range
        oifname "eth0" ip saddr 192.168.1.0/24 snat to 203.0.113.1:1024-65535
        
        # SNAT to IP range (load distribution)
        oifname "eth0" ip saddr 192.168.1.0/24 snat to 203.0.113.1-203.0.113.5
        
        # Protocol-specific SNAT
        oifname "eth0" ip protocol tcp snat to 203.0.113.1
    }
}
```

## 9.5 SNAT --random and --persistent Flags

```bash
# --random: Randomize source port mapping (helps with NAT predictability attacks)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j SNAT --to-source 203.0.113.1 --random

# --random-fully: Fully randomize source port (stronger randomization)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j SNAT --to-source 203.0.113.1 --random-fully

# --persistent: Same source IP always maps to same translated IP (sticky)
# Useful when SNAT pool has multiple IPs
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j SNAT --to-source 203.0.113.1-203.0.113.5 --persistent
```

## 9.6 SNAT Decision Flow

```
SNAT DECISION FLOWCHART:

Packet arrives at POSTROUTING
         │
         ▼
  Does it match -o eth0?
    NO  → skip SNAT, accept
    YES → continue
         │
         ▼
  Does source IP match 192.168.1.0/24?
    NO  → skip, accept
    YES → continue
         │
         ▼
  Is there already a conntrack entry?
    YES → use existing translation (ESTABLISHED)
    NO  → create new translation
         │
         ▼
  Allocate source port from 1024-65535
         │
         ▼
  Store in conntrack:
    orig:  192.168.1.10:54321 → 203.0.113.1:40001
    reply: 8.8.8.8:53 will come back to 203.0.113.1:40001
         │
         ▼
  Rewrite packet: src = 203.0.113.1:40001
         │
         ▼
  Send packet out eth0
```

---

# 10. DNAT — Destination NAT

## 10.1 What Is DNAT?

**DNAT (Destination NAT)** rewrites the **destination** IP address (and optionally the destination port) of incoming packets.

**When is it needed?**
- Port forwarding (expose a private server to the internet)
- Load balancing (distribute traffic to multiple backends)
- Transparent proxying (redirect traffic without client knowledge)
- Service migration (redirect traffic from old IP to new)

```
DNAT OPERATION (Port Forwarding):

Internet Client    Router               Private Server
1.2.3.4:54321 ──→ 203.0.113.1:80 ──DNAT──→ 192.168.1.10:8080

Step by step:
① Arrives at router: src=1.2.3.4:54321   dst=203.0.113.1:80
② After DNAT:        src=1.2.3.4:54321   dst=192.168.1.10:8080
③ Server replies:    src=192.168.1.10:8080 dst=1.2.3.4:54321
④ Router SNAT reply: src=203.0.113.1:80   dst=1.2.3.4:54321
   (automatic reverse SNAT by conntrack)
```

## 10.2 Where Does DNAT Happen?

DNAT happens in the **PREROUTING** chain (before routing decision) in the **nat** table.

```
CRITICAL INSIGHT: DNAT MUST happen BEFORE routing!

Why? Because the routing decision is based on the DESTINATION IP.
If we DNAT to change dst=1.2.3.4 to dst=192.168.0.10,
the routing table must see 192.168.0.10 to forward correctly.

Packet flow:
  External packet: dst=203.0.113.1:80
         │
    PREROUTING (nat) — ← DNAT HAPPENS HERE
    "Rewrite dst to 192.168.0.10:8080"
    Packet now: dst=192.168.0.10:8080
         │
   Routing: "192.168.0.10 is on my local LAN"
   → FORWARD this packet
         │
    FORWARD (filter) — check if allowed
         │
    POSTROUTING — exits toward 192.168.0.10
```

## 10.3 DNAT with iptables

```bash
# Port forwarding: external port 80 → internal server port 8080
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -j DNAT --to-destination 192.168.1.10:8080

# Port forwarding: SSH (external 2222 → internal 22)
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 2222 \
    -j DNAT --to-destination 192.168.1.20:22

# DNAT only for specific source IP
iptables -t nat -A PREROUTING \
    -i eth0 \
    -s 10.0.0.0/8 \
    -p tcp \
    --dport 443 \
    -j DNAT --to-destination 192.168.1.10:443

# DNAT to IP range (round-robin load balancing)
# Note: Requires statistic module or use ipvs for proper LB
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -m statistic --mode nth --every 3 --packet 0 \
    -j DNAT --to-destination 192.168.1.10:80
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -m statistic --mode nth --every 2 --packet 0 \
    -j DNAT --to-destination 192.168.1.11:80
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -j DNAT --to-destination 192.168.1.12:80

# DNAT port range
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 8000:8100 \
    -j DNAT --to-destination 192.168.1.10

# DNAT without port change (just IP)
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 443 \
    -j DNAT --to-destination 192.168.1.10

# Don't forget: allow forwarding!
iptables -A FORWARD -d 192.168.1.10 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 192.168.1.10 -p tcp --sport 8080 -j ACCEPT
```

## 10.4 DNAT with nftables

```nft
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        
        # Port forward HTTP
        iifname "eth0" tcp dport 80 dnat to 192.168.1.10:8080
        
        # Port forward HTTPS
        iifname "eth0" tcp dport 443 dnat to 192.168.1.10:8443
        
        # Port forward SSH on alternate port
        iifname "eth0" tcp dport 2222 dnat to 192.168.1.20:22
        
        # DNAT with source restriction
        iifname "eth0" ip saddr 10.0.0.0/8 tcp dport 443 dnat to 192.168.1.10
        
        # DNAT range of ports
        iifname "eth0" tcp dport 8000-8100 dnat to 192.168.1.10
        
        # Load balance using nft map
        iifname "eth0" tcp dport 80 dnat to numgen inc mod 3 map {
            0 : 192.168.1.10,
            1 : 192.168.1.11,
            2 : 192.168.1.12
        }
    }
}
```

## 10.5 DNAT Decision Flow

```
DNAT DECISION FLOWCHART:

External packet arrives on eth0
dst=203.0.113.1:80
         │
         ▼
    PREROUTING chain
         │
         ▼
  Rule: -i eth0 -p tcp --dport 80 -j DNAT --to-dest 192.168.1.10:8080
         │
         ▼
  Does packet match?
    -i eth0? YES
    -p tcp?  YES
    --dport 80? YES
         │
         ▼
  Perform DNAT:
    dst: 203.0.113.1:80 → 192.168.1.10:8080
         │
         ▼
  Store in conntrack:
    orig:  1.2.3.4:54321 → 203.0.113.1:80
    DNAT → 192.168.1.10:8080
    reply: 192.168.1.10:8080 → 1.2.3.4:54321
    will be un-DNAT'd to 1.2.3.4:54321 → 203.0.113.1:80 → 1.2.3.4:54321
         │
         ▼
  Routing: dst=192.168.1.10 → forward to eth1 (LAN)
         │
         ▼
  FORWARD chain: check if allowed
         │
         ▼
  Packet reaches 192.168.1.10:8080
```

---

# 11. MASQUERADE — Dynamic SNAT

## 11.1 What Is MASQUERADE?

**MASQUERADE** is a special form of SNAT where the source IP is automatically set to the IP address of the **outgoing interface**. Unlike SNAT, you don't specify the source IP in the rule.

**Why use MASQUERADE instead of SNAT?**
- When the public IP of the interface is **dynamic** (e.g., DHCP from ISP)
- You don't want to hardcode the IP in rules
- Connection is PPP/DSL with changing IPs

```
MASQUERADE vs SNAT:

SNAT (static IP):
  iptables -j SNAT --to-source 203.0.113.1
  → Always uses 203.0.113.1 (must know it in advance)
  → Faster (no interface IP lookup per packet)

MASQUERADE (dynamic IP):
  iptables -j MASQUERADE
  → Automatically uses current IP of outgoing interface
  → Slightly slower (looks up interface IP per packet)
  → Perfect for dynamic IPs (home broadband, cellular)
```

## 11.2 MASQUERADE with iptables

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# MASQUERADE all outgoing traffic from LAN
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -s 192.168.1.0/24 \
    -j MASQUERADE

# MASQUERADE with port range
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE --to-ports 1024-65535

# MASQUERADE with randomization
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE --random

# MASQUERADE for all outgoing (catch-all)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE
```

## 11.3 MASQUERADE with nftables

```nft
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        
        # Simple masquerade
        oifname "eth0" masquerade
        
        # Masquerade with random ports
        oifname "eth0" masquerade random
        
        # Masquerade only LAN traffic
        oifname "eth0" ip saddr 192.168.1.0/24 masquerade
        
        # Masquerade with fully random (stronger)
        oifname "eth0" masquerade fully-random
    }
}
```

## 11.4 Complete Home Router Setup with MASQUERADE

```bash
#!/bin/bash
# Complete home router NAT setup

# Interfaces
LAN_IF="eth1"    # LAN interface (connected to home devices)
WAN_IF="eth0"    # WAN interface (connected to internet)
LAN_NET="192.168.1.0/24"

# 1. Enable IPv4 forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# 2. Make it permanent
cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
EOF

# 3. Flush existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F

# 4. Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 5. Allow established/related
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 6. Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# 7. Allow LAN → WAN forwarding
iptables -A FORWARD \
    -i $LAN_IF \
    -o $WAN_IF \
    -s $LAN_NET \
    -j ACCEPT

# 8. MASQUERADE outgoing traffic
iptables -t nat -A POSTROUTING \
    -o $WAN_IF \
    -s $LAN_NET \
    -j MASQUERADE

# 9. Allow SSH from WAN (optional)
iptables -A INPUT -i $WAN_IF -p tcp --dport 22 -j ACCEPT

# 10. Allow LAN access to router
iptables -A INPUT -i $LAN_IF -j ACCEPT

echo "NAT router configured!"
```

---

# 12. REDIRECT — Local Port Redirect

## 12.1 What Is REDIRECT?

**REDIRECT** is a special form of DNAT that redirects packets to a port on the **local machine** (127.0.0.1). The destination IP is automatically set to the IP of the incoming interface (or 127.0.0.1 for OUTPUT chain).

**Primary use cases:**
- Transparent proxy (intercept HTTP/HTTPS without client configuration)
- Redirecting services to different ports on the same machine
- Traffic interception for monitoring

```
REDIRECT Operation:

Without REDIRECT:
  Client → Router:80 → Web Server (external)

With REDIRECT:
  Client → Router:80 ──REDIRECT──→ Router:3128 (Squid proxy)
  ↑ Client thinks it's talking to external server,
    but actually talking to local proxy!
```

## 12.2 REDIRECT with iptables

```bash
# Redirect incoming HTTP to local proxy (Squid on port 3128)
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -j REDIRECT --to-port 3128

# Redirect for a specific network
iptables -t nat -A PREROUTING \
    -s 192.168.1.0/24 \
    -p tcp \
    --dport 80 \
    -j REDIRECT --to-port 3128

# Redirect locally generated traffic (OUTPUT chain)
iptables -t nat -A OUTPUT \
    -p tcp \
    --dport 80 \
    -j REDIRECT --to-port 3128

# Redirect port range
iptables -t nat -A PREROUTING \
    -p tcp \
    --dport 80:443 \
    -j REDIRECT --to-port 3128

# DNS redirect: all DNS queries to local DNS resolver
iptables -t nat -A PREROUTING \
    -p udp \
    --dport 53 \
    -j REDIRECT --to-port 5353

# Transparent proxy for HTTPS (requires SSL interception by proxy)
iptables -t nat -A PREROUTING \
    -p tcp \
    --dport 443 \
    -j REDIRECT --to-port 3129
```

## 12.3 REDIRECT with nftables

```nft
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        
        # HTTP redirect to proxy
        tcp dport 80 redirect to :3128
        
        # DNS redirect
        udp dport 53 redirect to :5353
        
        # HTTPS redirect
        tcp dport 443 redirect to :3129
        
        # Only from specific interface
        iifname "eth1" tcp dport 80 redirect to :3128
    }
    
    chain output {
        type nat hook output priority -100; policy accept;
        
        # Redirect locally generated traffic
        tcp dport 80 redirect to :3128
    }
}
```

## 12.4 Getting Original Destination with SO_ORIGINAL_DST

When using REDIRECT, the proxy needs to know the **original destination** (where the client actually wanted to go):

```c
// C code: Get original destination after REDIRECT
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/netfilter_ipv4.h>

int get_original_dst(int sockfd, struct sockaddr_in *orig_dst) {
    socklen_t len = sizeof(struct sockaddr_in);
    return getsockopt(sockfd, SOL_IP, SO_ORIGINAL_DST, orig_dst, &len);
}

// Usage in a transparent proxy:
struct sockaddr_in orig_dst;
if (get_original_dst(client_fd, &orig_dst) == 0) {
    printf("Client wanted: %s:%d\n",
           inet_ntoa(orig_dst.sin_addr),
           ntohs(orig_dst.sin_port));
    // Now connect to orig_dst on behalf of the client
}
```

---

# 13. TPROXY — Transparent Proxy

## 13.1 What Is TPROXY?

**TPROXY** (Transparent Proxy) is an advanced redirection mechanism that allows a proxy application to receive traffic that was not originally destined for the local machine, **without modifying the packet** as it passes through.

**Key difference from REDIRECT:**

```
REDIRECT:
  - Changes dst IP to 127.0.0.1
  - Packet headers are modified in kernel
  - Original destination available via SO_ORIGINAL_DST

TPROXY:
  - Does NOT change packet headers
  - Packets delivered to socket with original dst IP:port intact
  - Application sees "as if" it is at original destination
  - Works better with UDP
  - Required for IPv6 transparent proxy
  - More elegant for complex routing scenarios
```

## 13.2 TPROXY Mechanism

```
TPROXY Flow:

1. External client sends: dst=remote_server:80
2. TPROXY mangle rule marks packet + sets mark
3. Policy routing rule: "marked packets → local"
4. Packet delivered to local proxy process listening on 0.0.0.0:80
5. Proxy sees original dst (remote_server:80) in ip header
6. Proxy connects to remote_server:80 on behalf of client

Why policy routing?
  Without it: kernel sees dst=remote_server:80 → routes to internet
  With it: kernel sees mark → routes to local proxy
```

## 13.3 TPROXY Setup

```bash
# Step 1: Mark packets in mangle PREROUTING
iptables -t mangle -A PREROUTING \
    -p tcp \
    --dport 80 \
    -j TPROXY \
    --tproxy-mark 0x1/0x1 \
    --on-port 8080

# Step 2: Policy routing — send marked packets to local
ip rule add fwmark 0x1 lookup 100
ip route add local 0.0.0.0/0 dev lo table 100

# Step 3: Proxy must listen with IP_TRANSPARENT option
# (see C/Rust implementation sections)
```

## 13.4 IP_TRANSPARENT Socket Option

```c
// C: Create a transparent proxy socket
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/socket.h>

int create_tproxy_socket(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    
    // Set IP_TRANSPARENT — allows binding to non-local addresses
    int one = 1;
    setsockopt(fd, SOL_IP, IP_TRANSPARENT, &one, sizeof(one));
    
    // Bind to 0.0.0.0:8080 (or any port TPROXY configured)
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(8080)
    };
    bind(fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(fd, 128);
    
    return fd;
}

// When accepting a connection:
// The accepted socket has dst IP = original destination (remote server)!
// Use getsockname() on the *accepted* socket to get original destination.
struct sockaddr_in orig_dst;
socklen_t len = sizeof(orig_dst);
getsockname(accepted_fd, (struct sockaddr*)&orig_dst, &len);
// orig_dst now contains where the client really wanted to go!
```

---

# 14. Full Cone, Symmetric, and Restricted NAT Types (RFC 4787)

## 14.1 Why This Classification Matters

These NAT behaviors affect **peer-to-peer** applications (VoIP, gaming, WebRTC, BitTorrent). The type of NAT determines if P2P works without special tricks.

```
Terminology:
  Internal: your private device
  External: the public internet side
  Internal IP:Port = (X:x)
  External IP:Port = (Y:y)  ← what the NAT allocates
  Remote host A = (A:a)
  Remote host B = (B:b)
```

## 14.2 Full Cone NAT (Best for P2P)

```
FULL CONE NAT:

① Internal (X:x) sends to (A:a)
   NAT maps (X:x) → (Y:y)

② ANY external host can send to (Y:y)
   and reach (X:x) — even if (X:x) never contacted them!

Analogy: Your front door is UNLOCKED.
Anyone who knows your address can knock.

                    ┌──────────────────┐
(X:x) ──sends──→   │    NAT Router    │  → (A:a)
                    │  X:x ↔ Y:y      │
(B:b) ──sends──→   │  (Y:y is open)   │  → (X:x) ✓
(C:c) ──sends──→   │                  │  → (X:x) ✓
                    └──────────────────┘
Any external IP can reach X:x via Y:y
```

## 14.3 Address-Restricted Cone NAT

```
ADDRESS-RESTRICTED CONE NAT:

① Internal (X:x) sends to (A:a)
   NAT maps (X:x) → (Y:y)

② External host (A:b) can send to (Y:y) → reaches (X:x) ✓
   (Same IP address A, ANY port)

③ External host (B:b) CANNOT send to (Y:y) → BLOCKED ✗
   (Different IP address)

Rule: External packets ACCEPTED only if X:x previously sent to that IP

Analogy: Front door with a guest list.
Only people you've spoken to can visit.

                    ┌──────────────────┐
(X:x) ──sends──→   │    NAT Router    │  → (A:a)
                    │  X:x ↔ Y:y      │
(A:b) ──sends──→   │  Allowed: A.*    │  → (X:x) ✓
(A:9999) ──sends→  │                  │  → (X:x) ✓ (any port of A)
(B:b) ──sends──→   │                  │  → BLOCKED ✗
                    └──────────────────┘
```

## 14.4 Port-Restricted Cone NAT

```
PORT-RESTRICTED CONE NAT:

① Internal (X:x) sends to (A:a)
   NAT maps (X:x) → (Y:y)

② (A:a) can send to (Y:y) → reaches (X:x) ✓
③ (A:b) CANNOT → BLOCKED ✗ (different port)
④ (B:a) CANNOT → BLOCKED ✗ (different IP)

Rule: Packets ACCEPTED only from the EXACT (IP:port) X:x sent to

                    ┌──────────────────┐
(X:x) ──sends──→   │    NAT Router    │  → (A:a)
                    │  X:x ↔ Y:y      │
(A:a) ──sends──→   │  Allowed: A:a    │  → (X:x) ✓
(A:b) ──sends──→   │  only            │  → BLOCKED ✗
(B:a) ──sends──→   │                  │  → BLOCKED ✗
                    └──────────────────┘
```

## 14.5 Symmetric NAT (Worst for P2P)

```
SYMMETRIC NAT (worst for P2P):

① (X:x) sends to (A:a) → NAT maps (X:x) → (Y:y1)
② (X:x) sends to (B:b) → NAT maps (X:x) → (Y:y2)  ← DIFFERENT MAPPING!

Each destination gets a DIFFERENT external port mapping!

AND: Only (A:a) can send back through (Y:y1)
     Only (B:b) can send back through (Y:y2)

WHY THIS BREAKS P2P:
  STUN server tells P2P client: "Your external address is Y:y1"
  P2P peer tries to connect to Y:y1
  But because peer is a NEW destination, NAT creates NEW mapping Y:y3
  Peer doesn't know about y3, tries y1 → FAILS

Analogy: You get a different phone number for every person you call,
and only they can call that number back.

                    ┌──────────────────────┐
(X:x) ──to A:a──→  │    NAT Router        │ --Y:y1-→ (A:a)
(X:x) ──to B:b──→  │  X:x→A:a = Y:y1     │ --Y:y2-→ (B:b)
                    │  X:x→B:b = Y:y2     │
(A:a) ──to Y:y1──→ │  Only A:a may use y1 │ → (X:x) ✓
(B:a) ──to Y:y1──→ │                      │ → BLOCKED ✗
                    └──────────────────────┘
```

## 14.6 Linux NAT Behavior

By default, Linux (Netfilter) implements **Port-Restricted Cone NAT** behavior. This means:
- Same source creates same external mapping to different destinations ✓ (Cone)
- Only the exact remote IP:port can send back ✓ (Port-restricted)

This is good for P2P with STUN but can cause issues with some applications expecting Full Cone.

---

# 15. Static NAT

## 15.1 What Is Static NAT?

**Static NAT** creates a **permanent 1:1 mapping** between a private IP and a public IP. Unlike dynamic NAT, the mapping never changes.

```
Static NAT:
  Private IP      ←→     Public IP
  192.168.1.10   ←→    203.0.113.10  (permanent)
  192.168.1.20   ←→    203.0.113.20  (permanent)
  192.168.1.30   ←→    203.0.113.30  (permanent)

  1 public IP per private IP (1:1 ratio)

Use cases:
  - Public servers that must have a fixed public IP
  - When you have enough public IPs for all hosts
  - Bidirectional access (both inbound and outbound)
```

## 15.2 Static NAT Implementation

```bash
# Static NAT with iptables (bidirectional 1:1)

# Public IP: 203.0.113.10 → Private: 192.168.1.10

# Outbound SNAT (private → public)
iptables -t nat -A POSTROUTING \
    -s 192.168.1.10 \
    -o eth0 \
    -j SNAT --to-source 203.0.113.10

# Inbound DNAT (public → private)
iptables -t nat -A PREROUTING \
    -d 203.0.113.10 \
    -i eth0 \
    -j DNAT --to-destination 192.168.1.10

# Multiple static NAT entries:
for i in 10 20 30; do
    private="192.168.1.$i"
    public="203.0.113.$i"
    
    iptables -t nat -A POSTROUTING -s $private -o eth0 \
        -j SNAT --to-source $public
    
    iptables -t nat -A PREROUTING -d $public -i eth0 \
        -j DNAT --to-destination $private
done
```

---

# 16. Dynamic NAT

## 16.1 What Is Dynamic NAT?

**Dynamic NAT** maps private IPs to a **pool** of public IPs. Unlike static NAT, the mapping is created on demand and released when the connection ends.

```
Dynamic NAT:
  Public IP Pool: 203.0.113.10 - 203.0.113.15 (6 addresses)
  Private Network: 192.168.1.0/24 (254 hosts)

  When private host needs internet:
    192.168.1.10 connects → assigned 203.0.113.10
    192.168.1.20 connects → assigned 203.0.113.11
    192.168.1.30 connects → assigned 203.0.113.12

  When connection ends → public IP returned to pool

  If 7+ hosts connect simultaneously → CONNECTION FAILS
  (pool exhausted — requires PAT/NAPT to solve this)
```

## 16.2 Dynamic NAT with iptables (IP Pool)

```bash
# Dynamic NAT with an IP pool
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -s 192.168.1.0/24 \
    -j SNAT --to-source 203.0.113.10-203.0.113.15

# Note: iptables will automatically manage the pool
# For true dynamic NAT behavior, each src IP gets one public IP
# For NAPT (many private → one public), just use MASQUERADE
```

---

# 17. PAT — Port Address Translation (NAPT)

## 17.1 What Is PAT?

**PAT (Port Address Translation)**, also known as **NAPT (Network Address and Port Translation)** or **IP masquerading**, maps **multiple private IP:port combinations** to a **single public IP** using different port numbers.

This is the most common form of NAT used in home routers and enterprise networks.

```
PAT / NAPT:

Private                     Public (single IP)
192.168.1.10:54321  ──→    203.0.113.1:40001
192.168.1.10:54322  ──→    203.0.113.1:40002
192.168.1.20:60000  ──→    203.0.113.1:40003
192.168.1.30:1024   ──→    203.0.113.1:40004
192.168.1.30:1025   ──→    203.0.113.1:40005
...

Theoretical maximum: 65535 concurrent connections per public IP
(In practice: ~60000 usable ephemeral ports)

This is what MASQUERADE implements!
```

## 17.2 Port Exhaustion Problem

```
PAT Port Exhaustion:

Available ports: ~60000 (1024-65535)
If each user has 10 connections: max ~6000 concurrent users per public IP

Solutions:
1. Multiple public IPs (SNAT pool)
2. Per-destination port tracking (most NAT implementations)
   → 60000 ports per destination IP
   → Much higher effective capacity
3. CGNAT with 100.64.0.0/10 range
```

---

# 18. Hairpin NAT / NAT Reflection / Loopback NAT

## 18.1 What Is Hairpin NAT?

**Hairpin NAT** (also called NAT Reflection or NAT Loopback) solves a specific problem: accessing an internal server using its **public IP/domain** from inside the same network.

```
THE PROBLEM:

Network: 192.168.1.0/24
Router: 192.168.1.1 (public IP: 203.0.113.1)
Web server: 192.168.1.10 (accessible externally as 203.0.113.1:80)

From external client (works fine):
  Client → 203.0.113.1:80 → DNAT → 192.168.1.10:80 ✓

From internal client 192.168.1.20 (BROKEN):
  192.168.1.20 → 203.0.113.1:80 → DNAT → 192.168.1.10:80
  
  But wait! 192.168.1.10 sees src=192.168.1.20
  Replies to 192.168.1.20 DIRECTLY (not through router!)
  192.168.1.20 is confused — it sent to 203.0.113.1 but gets reply from 192.168.1.10!
  → TCP connection FAILS (asymmetric routing)
```

```
HAIRPIN NAT FLOW (With Loopback NAT):

Without hairpin:
  .20 → [Router] → .10
  .10 → [Directly] → .20  ← ASYMMETRIC! BROKEN!

With hairpin:
  .20 → [Router] DNAT+SNAT → .10
  .10 → [Router] un-SNAT+un-DNAT → .20  ← Symmetric! WORKS!
```

## 18.2 Hairpin NAT Implementation

```bash
# Enable hairpin NAT

# DNAT rule (same as normal port forwarding)
iptables -t nat -A PREROUTING \
    -d 203.0.113.1 \
    -p tcp \
    --dport 80 \
    -j DNAT --to-destination 192.168.1.10:80

# SNAT rule for traffic that comes from LAN going to the server via public IP
# This is the KEY hairpin rule:
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 \
    -d 192.168.1.10 \
    -p tcp \
    --dport 80 \
    -j MASQUERADE

# Or with specific SNAT:
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 \
    -d 192.168.1.10 \
    -j SNAT --to-source 192.168.1.1

# Allow forwarding between LAN hosts
iptables -A FORWARD \
    -i eth1 \
    -o eth1 \
    -j ACCEPT
```

---

# 19. Double NAT

## 19.1 What Is Double NAT?

**Double NAT** occurs when there are two NAT devices in the path between client and server. Common in home networks where an ISP provides a NAT router, and the user also has a home router.

```
DOUBLE NAT TOPOLOGY:

Internet Server
     │
  ISP Router (NAT 1)
  Public IP: 1.2.3.4
  "You": 100.64.x.x (CGNAT)
     │
  Home Router (NAT 2)
  WAN: 100.64.x.x
  LAN: 192.168.1.0/24
     │
  Your Device: 192.168.1.10

Packet from your device to 8.8.8.8:
  src=192.168.1.10  → (NAT 2) → src=100.64.x.x → (NAT 1) → src=1.2.3.4
  
TWO levels of NAT!
Problems this causes:
  - Port forwarding broken
  - P2P applications fail
  - UPnP only works for inner NAT
  - VPNs may have issues
  - Gaming consoles show "strict NAT type"
```

## 19.2 Detecting Double NAT

```bash
# Check your public IP from device
curl ifconfig.me

# Check WAN IP of your home router
# (login to router admin page and look at WAN IP)

# If these differ → you have Double NAT
# If WAN IP is in 100.64.0.0/10 → ISP CGNAT (Double NAT)

# Check with traceroute — look for private IPs in path
traceroute 8.8.8.8
# If you see 192.168.x.x then 10.x.x.x, that's double NAT
```

---

# 20. Carrier-Grade NAT (CGNAT)

## 20.1 What Is CGNAT?

**CGNAT (Carrier-Grade NAT)**, also called **Large-Scale NAT (LSN)**, is NAT deployed by ISPs to share a single public IP among many subscribers.

```
CGNAT Address Space (RFC 6598):
  100.64.0.0/10 (100.64.0.0 - 100.127.255.255)
  ~4 million addresses — private between ISP and customers
  
CGNAT Hierarchy:
  Internet (Public IP)
       │
    ISP CGNAT (Shared public IP pool)
    100.64.0.0/10 → subscriber
       │
    Home Router (Private)
    192.168.1.0/24 → home devices
       │
    Your device (192.168.1.10)

Result: Three levels of addressing!
  1.2.3.4 → 100.64.x.y → 192.168.1.10
```

## 20.2 CGNAT Impact and Workarounds

```
Problems with CGNAT:
  ✗ Port forwarding completely broken
  ✗ Hosting servers from home impossible
  ✗ Some VPN protocols fail
  ✗ Gaming NAT type: Strict
  ✗ P2P severely limited

Workarounds:
  1. Request static public IP from ISP (usually paid)
  2. Use VPN service (traffic exits at VPN provider's public IP)
  3. Use reverse tunnels (e.g., frp, ngrok, bore, rathole)
  4. Use IPv6 (no NAT needed!)
```

## 20.3 Linux CGNAT Configuration

```bash
# Configuring a basic CGNAT setup on a Linux carrier system

# Masquerade subscriber traffic to public IP pool
iptables -t nat -A POSTROUTING \
    -s 100.64.0.0/10 \
    -o eth0 \
    -j SNAT --to-source 1.2.3.4-1.2.3.100 --random

# Or with MASQUERADE (auto-detects outgoing interface IP)
iptables -t nat -A POSTROUTING \
    -s 100.64.0.0/10 \
    -o eth0 \
    -j MASQUERADE

# For high-performance CGNAT, consider:
# - nftables with maps for deterministic port allocation
# - IPVS (IP Virtual Server) for scalable NAT
# - eBPF/XDP for kernel bypass NAT
```

---

# 21. NAT64 and DNS64 — IPv6 Transition

## 21.1 What Is NAT64?

**NAT64** allows **IPv6-only clients** to communicate with **IPv4-only servers** by translating between IPv6 and IPv4 addresses.

**Why needed?** As IPv4 addresses run out, ISPs deploy IPv6-only networks. But most of the internet still has IPv4-only content.

```
NAT64 ARCHITECTURE:

IPv6 Client (2001:db8::1)
     │
     ├─→ IPv6 Server: connects directly ✓
     │
     └─→ IPv4 Server:
           DNS64: translates A record to AAAA (64:ff9b::8.8.8.8)
           NAT64: translates IPv6 packet to IPv4 packet
           
Well-known prefix: 64:ff9b::/96
  IPv4 server 8.8.8.8 → appears as 64:ff9b::8.8.8.8 to IPv6 clients
  64:ff9b::0800.0808 = 64:ff9b::8.8.8.8

Flow:
  IPv6 client → DNS64 → "google.com AAAA = 64:ff9b::8.8.8.8"
  IPv6 client → sends to 64:ff9b::8.8.8.8
  NAT64 gateway → strips prefix, sends to 8.8.8.8 as IPv4
  8.8.8.8 → replies to NAT64 (IPv4)
  NAT64 → translates to IPv6, sends to client
```

## 21.2 NAT64 Implementation with Linux

```bash
# Using tayga (userspace NAT64 translator)
apt install tayga

# /etc/tayga.conf:
# tun-device nat64
# ipv4-addr 192.168.255.1
# prefix 64:ff9b::/96
# dynamic-pool 192.168.255.0/24
# data-dir /var/spool/tayga

# Start tayga
tayga --mktun
ip link set nat64 up
ip route add 192.168.255.0/24 dev nat64
ip route add 64:ff9b::/96 dev nat64

# DNS64 with BIND:
# In named.conf:
# dns64 64:ff9b::/96 {
#     clients { any; };
#     mapped { !rfc1918; any; };
#     exclude { 64:ff9b::/96; ::ffff:0:0/96; any; };
# };
```

---

# 22. NAT Traversal Techniques (STUN, TURN, ICE, UPnP)

## 22.1 The NAT Traversal Problem

```
P2P Communication Problem:

Peer A (behind NAT)        Peer B (behind NAT)
192.168.1.10               192.168.2.10
↕ NAT A                    ↕ NAT B
Public: 1.2.3.4:40001      Public: 5.6.7.8:50001

A wants to connect to B:
  A knows B's private IP (192.168.2.10) — not routable ✗
  A needs B's public IP:port (5.6.7.8:50001) — but NAT B may block ✗

Solution techniques:
  1. STUN — discover external address
  2. TURN — relay traffic through server
  3. ICE  — try multiple methods
  4. UPnP — ask router to open port
  5. Hole punching — simultaneous connect
```

## 22.2 STUN (Session Traversal Utilities for NAT)

```
STUN allows a client to discover its external IP:port.

Flow:
  Client → STUN Server: "What is my external address?"
  STUN Server → Client: "You appear as 1.2.3.4:40001"
  Client now knows its external address to share with peers.

Works with:
  - Full Cone NAT ✓
  - Restricted Cone NAT ✓ (with hole punching)
  - Symmetric NAT ✗ (each destination = different mapping)
```

## 22.3 Hole Punching

```
UDP HOLE PUNCHING:

Both peers send to each other SIMULTANEOUSLY:

Peer A (1.2.3.4)    Signal Server    Peer B (5.6.7.8)
     │                   │                   │
     │──"I'm at 1.2.3.4"──→                  │
     │                   │←─"I'm at 5.6.7.8"─│
     │                   │                   │
     │←─"Connect to 5.6.7.8"─────────────────│
     │──"Connect to 1.2.3.4"─────────────────→│
     │                   │                   │
     │─────UDP to 5.6.7.8:50001──────────────→│ (creates hole in NAT A)
     │←────UDP to 1.2.3.4:40001──────────────│ (creates hole in NAT B)
     │                   │                   │
     ◄═══════════════ P2P connection ════════►│
     
Why it works:
  A sends to B → NAT A opens port for (B)
  B sends to A → NAT B opens port for (A)
  Both NATs now have entries → packets flow!
```

## 22.4 TURN (Traversal Using Relays around NAT)

```
TURN = fallback when hole punching fails (Symmetric NAT):

Peer A ──→ TURN Server ──→ Peer B
Peer B ──→ TURN Server ──→ Peer A

Traffic relayed through TURN server (adds latency, bandwidth cost)
Used as last resort when direct P2P impossible.
```

## 22.5 ICE (Interactive Connectivity Establishment)

```
ICE tries candidates in order of preference:
1. Host candidate  : Direct connect (no NAT)
2. Server Reflexive: STUN-discovered external IP (STUN traversal)
3. Relayed         : TURN relay

ICE negotiation:
  Both peers gather all their candidates
  Exchange candidates via signaling (SIP/WebRTC)
  Try all combinations in priority order
  Use best working connection
  
This is used by WebRTC for browser video calls!
```

## 22.6 UPnP / NAT-PMP — Automatic Port Forwarding

```
UPnP (Universal Plug and Play) - IGD profile:
  Application → Router: "Please open port 8080 and forward to me"
  Router → Application: "Done, port 8080 is forwarded to you"

No user configuration needed!

Linux UPnP client:
  upnpc -e "MyApp" -r 8080 TCP   # Request port mapping
  upnpc -l                        # List current mappings

NAT-PMP (NAT Port Mapping Protocol) — simpler UPnP:
  Used by macOS, iOS (before PCP)

PCP (Port Control Protocol) — successor to NAT-PMP:
  More features, IPv6 support
```

---

# 23. Linux Kernel Internals — How NAT Works at the Code Level

## 23.1 Key Kernel Source Files

```
Linux kernel source related to NAT:

net/netfilter/
├── nf_conntrack_core.c      — Core connection tracking
├── nf_conntrack_proto_tcp.c — TCP state machine
├── nf_conntrack_proto_udp.c — UDP tracking
├── nf_nat_core.c            — Core NAT operations
├── nf_nat_proto_tcp.c       — TCP NAT (port mangling)
├── nf_nat_proto_udp.c       — UDP NAT
├── nf_nat_masquerade.c      — MASQUERADE target
├── nf_tables_core.c         — nftables core
└── xt_MASQUERADE.c          — iptables MASQUERADE target

net/ipv4/
├── ip_forward.c             — IP forwarding logic
├── netfilter/
│   ├── nf_nat_l3proto_ipv4.c  — IPv4-specific NAT
│   └── iptable_nat.c          — iptables NAT table
```

## 23.2 The nf_conntrack_tuple Structure

This is the core data structure that represents a connection:

```c
/* From: include/net/netfilter/nf_conntrack_tuple.h */

/* What is a connection? It's defined by its tuple.
 * A tuple uniquely identifies a connection in one direction. */
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;  /* Source side (can be changed by NAT) */
    
    /* Destination: cannot be altered in SNAT */
    struct {
        union nf_inet_addr u3;    /* IP address */
        union {
            /* Protocol-specific destination port/id */
            __be16 all;           /* Port (TCP/UDP) */
            struct { __be16 port; } tcp;
            struct { __be16 port; } udp;
            struct { u_int8_t type, code; } icmp;
        } u;
        u_int8_t protonum;        /* Protocol number (6=TCP, 17=UDP) */
        u_int8_t dir;             /* Direction */
    } dst;
};

/* The source side that NAT can rewrite */
struct nf_conntrack_man {
    union nf_inet_addr u3;        /* IP address */
    union nf_conntrack_man_proto u;  /* Port/ID */
    u_int16_t l3num;             /* Layer 3 protocol */
};
```

## 23.3 The nf_conn Structure (Connection Tracking Entry)

```c
/* From: include/net/netfilter/nf_conntrack.h */

struct nf_conn {
    struct nf_conntrack ct_general;  /* reference count */
    
    /* 2 tuples: original and reply directions */
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];
    
    /* Connection state */
    unsigned long status;  /* IP_CT_STATUS flags */
    
    /* NAT information */
    struct nf_conn_nat *nat;  /* If NULL, no NAT */
    
    /* Timeout */
    struct timer_list timeout;
    
    /* Connection mark (used by iptables -m mark) */
    u_int32_t mark;
    
    /* Extensions (NAT, helpers, etc.) */
    struct nf_ct_ext *ext;
    
    /* Protocol-specific data */
    union nf_conntrack_proto proto;
};
```

## 23.4 NAT Core Operation (nf_nat_packet)

```c
/* Simplified from: net/netfilter/nf_nat_core.c */

unsigned int nf_nat_packet(struct nf_conn *ct,
                            enum ip_conntrack_info ctinfo,
                            unsigned int hooknum,
                            struct sk_buff *skb)
{
    enum nf_nat_manip_type mtype = HOOK2MANIP(hooknum);
    enum ip_conntrack_dir dir = CTINFO2DIR(ctinfo);
    
    /* Get the tuple we need to mangle */
    const struct nf_conntrack_tuple *t = &ct->tuplehash[!dir].tuple;
    
    /* Perform the actual packet mangling:
       - For SNAT: change source IP/port in packet
       - For DNAT: change destination IP/port in packet */
    if (mtype == NF_NAT_MANIP_SRC) {
        /* SNAT: rewrite source */
        nf_nat_ipv4_manip_pkt(skb, 0, &ct->tuplehash[!dir].tuple, mtype);
    } else {
        /* DNAT: rewrite destination */
        nf_nat_ipv4_manip_pkt(skb, 0, &ct->tuplehash[!dir].tuple, mtype);
    }
    
    return NF_ACCEPT;
}
```

## 23.5 The Hash Table — How conntrack Finds Entries Fast

```
conntrack uses a HASH TABLE for O(1) lookup:

Hash function:
  hash = jhash(src_ip, dst_ip, src_port, dst_port, proto, zone)
  bucket = hash % table_size

When a packet arrives:
  1. Compute hash of packet's 5-tuple
  2. Look up hash table bucket
  3. Walk bucket chain (collision resolution)
  4. Compare full tuple for exact match
  5. Found → get existing conntrack entry
  6. Not found → create new entry

  O(1) average case lookup — very fast!

Hash Table:
  ┌─────────────────────────────────────┐
  │ Bucket 0: conn_A → conn_B → null   │
  │ Bucket 1: null                       │
  │ Bucket 2: conn_C → null             │
  │ Bucket 3: conn_D → conn_E → null   │
  │ ...                                  │
  │ Bucket N: ...                        │
  └─────────────────────────────────────┘
```

---

# 24. The /proc and /sys NAT Interfaces

## 24.1 Important /proc Entries

```bash
# ─── Connection Tracking ───

# Current conntrack count
cat /proc/sys/net/netfilter/nf_conntrack_count

# Maximum conntrack entries
cat /proc/sys/net/netfilter/nf_conntrack_max

# View raw conntrack table
cat /proc/net/nf_conntrack

# ─── Protocol Timeouts ───

# TCP timeouts (in seconds)
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_syn_sent
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_syn_recv
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_established  # 432000 = 5 days!
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_fin_wait
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_close_wait
cat /proc/sys/net/netfilter/nf_conntrack_tcp_timeout_time_wait

# UDP timeouts
cat /proc/sys/net/netfilter/nf_conntrack_udp_timeout
cat /proc/sys/net/netfilter/nf_conntrack_udp_timeout_stream

# ICMP timeout
cat /proc/sys/net/netfilter/nf_conntrack_icmp_timeout

# ─── IP Forwarding ───

# Enable/disable IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Per-interface forwarding
cat /proc/sys/net/ipv4/conf/eth0/forwarding

# ─── NAT related ───

# Local port range used for MASQUERADE
cat /proc/sys/net/ipv4/ip_local_port_range
# Default: 32768 60999

# Change to use more ports for MASQUERADE
echo "1024 65535" > /proc/sys/net/ipv4/ip_local_port_range
```

## 24.2 Important /sys Entries

```bash
# Conntrack hash table size
cat /sys/module/nf_conntrack/parameters/hashsize
echo 262144 > /sys/module/nf_conntrack/parameters/hashsize

# Check loaded netfilter modules
ls /sys/module/ | grep nf_

# Conntrack accounting (per-connection packet/byte counters)
cat /sys/module/nf_conntrack/parameters/acct
echo 1 > /sys/module/nf_conntrack/parameters/acct
```

## 24.3 Important sysctl Settings for NAT Optimization

```bash
# /etc/sysctl.d/99-nat-optimization.conf

# Enable IP forwarding
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# Increase conntrack table size
net.netfilter.nf_conntrack_max = 1048576

# Decrease TCP established timeout (saves conntrack memory)
net.netfilter.nf_conntrack_tcp_timeout_established = 600

# Decrease TIME_WAIT timeout
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30

# Extend UDP timeout for DNS
net.netfilter.nf_conntrack_udp_timeout = 30
net.netfilter.nf_conntrack_udp_timeout_stream = 180

# Reverse path filtering (spoofing protection)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# TCP optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Disable ICMP redirects on router
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Don't accept IP source routing
net.ipv4.conf.all.accept_source_route = 0
```

---

# 25. ip rule and ip route — Policy Routing with NAT

## 25.1 What Is Policy Routing?

**Policy routing** allows different routing decisions based on more than just the destination IP. You can route based on source IP, packet mark, ToS, etc.

This is essential for:
- TPROXY setups
- Multiple ISP routing (multi-homing)
- VPN routing

```
Normal routing: based only on DESTINATION IP
Policy routing: based on SOURCE IP, MARK, TOS, INPUT INTERFACE, etc.

Linux routing lookup order:
  1. ip rule: match rules in order of priority
  2. If matched, use specified routing table
  3. ip route: look up route in that table
```

## 25.2 ip rule Command

```bash
# View current routing rules
ip rule list
# Output:
# 0:      from all lookup local      ← always check local table first
# 32766:  from all lookup main       ← default: use main routing table
# 32767:  from all lookup default    ← last resort

# Add rule: traffic from 192.168.1.0/24 uses table 100
ip rule add from 192.168.1.0/24 lookup 100 priority 100

# Add rule: marked packets use table 200
ip rule add fwmark 0x1 lookup 200 priority 200

# Add rule: based on destination
ip rule add to 10.0.0.0/8 lookup 300

# Delete rule
ip rule del from 192.168.1.0/24 lookup 100

# Named routing tables (in /etc/iproute2/rt_tables)
# Add: 100 myroutetable
# Then use: ip rule add from X lookup myroutetable
```

## 25.3 ip route for Policy Routing

```bash
# Add route to specific routing table
ip route add default via 192.168.1.1 table 100
ip route add 192.168.1.0/24 dev eth1 table 100

# For TPROXY: route marked packets to local
ip route add local default dev lo table 200
ip rule add fwmark 0x1 lookup 200

# Multiple ISP setup:
# ISP1: eth0 (192.168.1.1 gateway)
# ISP2: eth1 (10.0.0.1 gateway)
# Default: use ISP1
# Traffic from 192.168.2.0/24: use ISP2

ip route add default via 192.168.1.1     # Main table default
ip route add default via 10.0.0.1 table 200  # ISP2 table
ip rule add from 192.168.2.0/24 lookup 200   # Route LAN2 via ISP2
```

## 25.4 Multi-ISP NAT with Policy Routing

```bash
#!/bin/bash
# Multi-ISP Load Balancing with NAT

# ISP1
ISP1_IF="eth0"
ISP1_GW="203.0.113.1"
ISP1_IP="203.0.113.10"
ISP1_TABLE=100

# ISP2
ISP2_IF="eth1"
ISP2_GW="198.51.100.1"
ISP2_IP="198.51.100.10"
ISP2_TABLE=101

# LAN
LAN_IF="eth2"
LAN_NET="192.168.1.0/24"

# Create routing tables for each ISP
ip route flush table $ISP1_TABLE
ip route flush table $ISP2_TABLE

ip route add default via $ISP1_GW table $ISP1_TABLE
ip route add $LAN_NET dev $LAN_IF table $ISP1_TABLE

ip route add default via $ISP2_GW table $ISP2_TABLE
ip route add $LAN_NET dev $LAN_IF table $ISP2_TABLE

# Rules: mark-based routing
ip rule add fwmark 1 lookup $ISP1_TABLE priority 100
ip rule add fwmark 2 lookup $ISP2_TABLE priority 101

# Mark packets: round-robin between ISPs
iptables -t mangle -A PREROUTING -i $LAN_IF \
    -m statistic --mode nth --every 2 --packet 0 \
    -j MARK --set-mark 1

iptables -t mangle -A PREROUTING -i $LAN_IF \
    -m statistic --mode nth --every 2 --packet 1 \
    -j MARK --set-mark 2

# SNAT for each ISP
iptables -t nat -A POSTROUTING -o $ISP1_IF \
    -j SNAT --to-source $ISP1_IP

iptables -t nat -A POSTROUTING -o $ISP2_IF \
    -j SNAT --to-source $ISP2_IP

echo "Multi-ISP NAT configured!"
```

---

# 26. Network Namespaces and NAT

## 26.1 What Are Network Namespaces?

**Network namespaces** are a Linux kernel feature that creates isolated network stacks. Each namespace has its own:
- Network interfaces
- Routing tables
- iptables/nftables rules
- conntrack table
- Sockets

This is the foundation of **container networking** (Docker, Kubernetes).

```
Network Namespaces:

Default namespace (root):
  eth0 (physical)
  lo
  iptables rules
  routing table

  ┌─────────────────────────────┐
  │   Container namespace 1     │
  │   veth0 (virtual ethernet)  │
  │   lo                        │
  │   routing table             │
  │   iptables rules            │
  └─────────────────────────────┘
        ↕ (veth pair)
  ┌─────────────────────────────┐
  │   Container namespace 2     │
  │   veth0                     │
  │   lo                        │
  └─────────────────────────────┘
```

## 26.2 Creating Namespaces and Testing NAT

```bash
# Create two network namespaces
ip netns add client
ip netns add router
ip netns add server

# Create veth pairs (virtual ethernet cables)
ip link add veth-client type veth peer name veth-router-client
ip link add veth-server type veth peer name veth-router-server

# Assign interfaces to namespaces
ip link set veth-client netns client
ip link set veth-router-client netns router
ip link set veth-server netns server
ip link set veth-router-server netns router

# Configure client namespace
ip netns exec client ip addr add 192.168.1.10/24 dev veth-client
ip netns exec client ip link set veth-client up
ip netns exec client ip link set lo up
ip netns exec client ip route add default via 192.168.1.1

# Configure router namespace
ip netns exec router ip addr add 192.168.1.1/24 dev veth-router-client
ip netns exec router ip addr add 10.0.0.1/24 dev veth-router-server
ip netns exec router ip link set veth-router-client up
ip netns exec router ip link set veth-router-server up
ip netns exec router ip link set lo up
ip netns exec router sysctl -w net.ipv4.ip_forward=1

# Configure server namespace
ip netns exec server ip addr add 10.0.0.10/24 dev veth-server
ip netns exec server ip link set veth-server up
ip netns exec server ip link set lo up
ip netns exec server ip route add default via 10.0.0.1

# Add MASQUERADE in router namespace
ip netns exec router iptables -t nat -A POSTROUTING \
    -o veth-router-server -j MASQUERADE

# Test: ping from client to server (goes through NAT)
ip netns exec client ping 10.0.0.10

# Test: see NAT in action
ip netns exec router conntrack -L

# Clean up
ip netns del client
ip netns del router
ip netns del server
```

---

# 27. Docker / Kubernetes NAT Internals

## 27.1 How Docker Uses NAT

Docker creates its own network namespace for each container and uses **iptables** to handle NAT automatically.

```
DOCKER NAT ARCHITECTURE:

Physical Host:
  eth0: 203.0.113.1 (public IP)
  docker0: 172.17.0.1 (bridge, default)

Container 1: 172.17.0.2
Container 2: 172.17.0.3

Docker iptables rules (auto-created):

POSTROUTING:
  -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
  ← All container traffic going out non-docker interface is MASQUERADE'd

PREROUTING:
  -d 203.0.113.1 -p tcp --dport 8080 -j DNAT --to-dest 172.17.0.2:80
  ← Port publishing (-p 8080:80 in docker run)
```

## 27.2 Viewing Docker NAT Rules

```bash
# See Docker's iptables rules
iptables -t nat -L -n -v

# Docker chains:
# DOCKER-USER    — user-defined rules (docker recommends putting custom rules here)
# DOCKER         — docker's own DNAT rules
# DOCKER-ISOLATION-STAGE-1 — network isolation
# DOCKER-ISOLATION-STAGE-2 — network isolation

# See specific container's port forwarding
docker inspect  | grep -A 20 "Ports"

# See how Docker creates rules when you expose a port
docker run -d -p 8080:80 nginx

# Then:
iptables -t nat -L DOCKER -n -v
# Shows: DNAT tcp -- 0.0.0.0/0 0.0.0.0/0 tcp dpt:8080 to:172.17.0.x:80
```

## 27.3 Kubernetes kube-proxy NAT

```
KUBERNETES NAT:

kube-proxy runs on every node, manages iptables for Services.

Service: ClusterIP (internal)
  iptables DNAT: ClusterIP:Port → random pod IP:port

Service: NodePort
  iptables DNAT: NodeIP:NodePort → ClusterIP:Port → Pod

Service: LoadBalancer  
  External LB → NodeIP:NodePort → DNAT → Pod

kube-proxy iptables rules:
  PREROUTING → KUBE-SERVICES chain
  KUBE-SERVICES → KUBE-SVC-XXXXX (per service)
  KUBE-SVC-XXXXX → KUBE-SEP-XXXXX (per endpoint, round-robin)
  KUBE-SEP-XXXXX → DNAT --to-destination podIP:podPort
```

## 27.4 Inspecting Kubernetes NAT

```bash
# See all kube-proxy NAT rules
iptables -t nat -L -n | grep -E "KUBE|kube"

# See rules for a specific service
iptables -t nat -L KUBE-SERVICES -n

# See endpoints for a service
iptables -t nat -L KUBE-SVC-XXXXXX -n

# In newer Kubernetes: kube-proxy with ipvs mode (no iptables)
ipvsadm -L -n
```

---

# 28. eBPF / XDP NAT — The Future

## 28.1 What Is eBPF?

**eBPF (extended Berkeley Packet Filter)** is a technology that allows running sandboxed programs in the Linux kernel without changing kernel source code. For networking, eBPF can:

- Intercept packets at the earliest possible point
- Run at wire speed
- Replace iptables/nftables for high-performance use cases

```
eBPF vs iptables for NAT:

iptables NAT:
  NIC → Driver → netfilter hooks → NAT → forwarding
  Multiple copies, many hook points, overhead

XDP/eBPF NAT:
  NIC → Driver → XDP hook → eBPF NAT program → transmit
  Zero copy, earliest hook, maximum performance
  
Performance:
  iptables MASQUERADE:  ~2-3 million PPS
  XDP eBPF NAT:         ~10-15 million PPS (5x improvement)
```

## 28.2 Simple eBPF NAT Concept

```c
/* Simplified eBPF XDP NAT (conceptual) */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

/* NAT map: private → public */
struct nat_key {
    __u32 src_ip;
    __u16 src_port;
    __u8  protocol;
};

struct nat_entry {
    __u32 new_src_ip;
    __u16 new_src_port;
};

/* BPF hash map for NAT state */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct nat_key);
    __type(value, struct nat_entry);
    __uint(max_entries, 1000000);
} nat_table SEC(".maps");

SEC("xdp")
int xdp_nat(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if (data + sizeof(*eth) > data_end)
        return XDP_PASS;
    
    /* Only handle IPv4 */
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;
    
    /* Parse IP header */
    struct iphdr *ip = data + sizeof(*eth);
    if ((void*)ip + sizeof(*ip) > data_end)
        return XDP_PASS;
    
    /* Only TCP/UDP */
    if (ip->protocol != IPPROTO_TCP && ip->protocol != IPPROTO_UDP)
        return XDP_PASS;
    
    /* Parse TCP header */
    struct tcphdr *tcp = (void*)ip + (ip->ihl * 4);
    if ((void*)tcp + sizeof(*tcp) > data_end)
        return XDP_PASS;
    
    /* Look up NAT table */
    struct nat_key key = {
        .src_ip = ip->saddr,
        .src_port = tcp->source,
        .protocol = ip->protocol
    };
    
    struct nat_entry *entry = bpf_map_lookup_elem(&nat_table, &key);
    if (!entry)
        return XDP_PASS;  /* Not in NAT table, pass up the stack */
    
    /* Rewrite source IP and port */
    /* (Need to update checksums too!) */
    ip->saddr = entry->new_src_ip;
    tcp->source = entry->new_src_port;
    
    /* Recalculate checksums */
    /* ... (complex, omitted for brevity) ... */
    
    return XDP_TX;  /* Retransmit the modified packet */
}

char LICENSE[] SEC("license") = "GPL";
```

## 28.3 Cilium — Kubernetes CNI using eBPF for NAT

```
Cilium replaces kube-proxy with eBPF programs:
  No iptables at all!
  Direct eBPF maps for service → pod routing
  Order of magnitude better performance
  Better observability

Key concepts:
  - BPF socket-level load balancing (before socket connect())
  - No DNAT needed — kernel routes to pod directly
  - Connection tracking in BPF maps
```

---

# 29. C Implementation — Raw Socket NAT Engine

## 29.1 Overview

We'll build a userspace NAT engine in C using:
- Raw sockets (to capture all IP traffic)
- A hash map for connection tracking
- Manual IP/TCP header manipulation
- Checksum recalculation

## 29.2 Header Files and Data Structures

```c
/* nat_engine.h */
#ifndef NAT_ENGINE_H
#define NAT_ENGINE_H

#include 
#include 
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include 

/* ─── Constants ─── */
#define NAT_TABLE_SIZE      65536
#define NAT_PORT_START      10000
#define NAT_PORT_END        60000
#define NAT_TCP_TIMEOUT     600   /* seconds */
#define NAT_UDP_TIMEOUT     30    /* seconds */
#define MAX_PACKET_SIZE     65536

/* ─── NAT Entry State ─── */
typedef enum {
    NAT_STATE_NEW        = 0,
    NAT_STATE_ESTABLISHED = 1,
    NAT_STATE_CLOSING    = 2,
    NAT_STATE_CLOSED     = 3,
} nat_state_t;

/* ─── 5-Tuple: Unique connection identifier ─── */
/* A 5-tuple identifies a unique connection: protocol + src + dst */
typedef struct {
    uint32_t src_ip;    /* Source IP (network byte order) */
    uint32_t dst_ip;    /* Destination IP */
    uint16_t src_port;  /* Source port */
    uint16_t dst_port;  /* Destination port */
    uint8_t  proto;     /* Protocol (IPPROTO_TCP, IPPROTO_UDP) */
} five_tuple_t;

/* ─── NAT Mapping ─── */
/* Represents a single NAT translation entry */
typedef struct nat_entry {
    /* Original connection (from private host) */
    five_tuple_t original;
    
    /* Translated connection (what the internet sees) */
    uint32_t     nat_ip;       /* Public IP after translation */
    uint16_t     nat_port;     /* Allocated port after translation */
    
    /* State and timing */
    nat_state_t  state;
    time_t       created;      /* Creation timestamp */
    time_t       last_seen;    /* Last packet timestamp */
    uint64_t     pkts_fwd;     /* Forward direction packet count */
    uint64_t     pkts_rev;     /* Reverse direction packet count */
    uint64_t     bytes_fwd;    /* Forward bytes */
    uint64_t     bytes_rev;    /* Reverse bytes */
    
    /* Hash chain */
    struct nat_entry *next;    /* For hash collision chaining */
} nat_entry_t;

/* ─── NAT Configuration ─── */
typedef struct {
    uint32_t private_net;    /* Private network (e.g., 192.168.1.0) */
    uint32_t private_mask;   /* Subnet mask */
    uint32_t public_ip;      /* Public IP to SNAT to */
    uint16_t port_start;     /* Start of ephemeral port range */
    uint16_t port_end;       /* End of ephemeral port range */
    
    /* Interfaces */
    char lan_interface[16];  /* LAN interface name */
    char wan_interface[16];  /* WAN interface name */
    
    /* Timeouts */
    int tcp_timeout;
    int udp_timeout;
} nat_config_t;

/* ─── NAT Table ─── */
typedef struct {
    nat_entry_t *buckets[NAT_TABLE_SIZE];  /* Hash buckets */
    pthread_mutex_t lock;                   /* Thread safety */
    nat_config_t config;                    /* Configuration */
    uint16_t next_port;                     /* Next port to allocate */
    uint64_t total_entries;
    uint64_t total_translations;
} nat_table_t;

/* ─── Packet Buffer ─── */
typedef struct {
    uint8_t  data[MAX_PACKET_SIZE];
    size_t   len;
    int      in_fd;   /* Input socket fd */
    int      out_fd;  /* Output socket fd */
} packet_t;

/* ─── Function Declarations ─── */

/* NAT table operations */
nat_table_t* nat_table_create(const nat_config_t *config);
void         nat_table_destroy(nat_table_t *table);
nat_entry_t* nat_table_lookup_forward(nat_table_t *table,
                                       const five_tuple_t *tuple);
nat_entry_t* nat_table_lookup_reverse(nat_table_t *table,
                                       uint32_t nat_ip, uint16_t nat_port,
                                       uint8_t proto);
nat_entry_t* nat_table_insert(nat_table_t *table,
                               const five_tuple_t *tuple);
void         nat_table_cleanup(nat_table_t *table);

/* Packet processing */
int process_outbound(nat_table_t *table, packet_t *pkt);
int process_inbound(nat_table_t *table, packet_t *pkt);

/* Checksum utilities */
uint16_t ip_checksum(const void *data, size_t len);
uint16_t tcp_checksum(const struct iphdr *ip, const struct tcphdr *tcp,
                       const uint8_t *payload, size_t payload_len);
uint16_t udp_checksum(const struct iphdr *ip, const struct udphdr *udp,
                       const uint8_t *payload, size_t payload_len);

/* Utility */
uint32_t hash_five_tuple(const five_tuple_t *tuple);
const char* ip_to_str(uint32_t ip, char *buf, size_t buflen);
void print_entry(const nat_entry_t *entry);
void print_nat_table(const nat_table_t *table);

#endif /* NAT_ENGINE_H */
```

## 29.3 Core Implementation

```c
/* nat_engine.c */
#include "nat_engine.h"
#include 
#include 
#include 
#include 
#include 
#include 

/* ═══════════════════════════════════════════════════════════
   HASHING
   ═══════════════════════════════════════════════════════════ */

/* Jenkins hash for 5-tuple — fast and good distribution */
uint32_t hash_five_tuple(const five_tuple_t *t) {
    uint32_t hash = 0;
    
    /* Mix all fields */
    hash += t->src_ip;
    hash += (hash << 10);
    hash ^= (hash >> 6);
    
    hash += t->dst_ip;
    hash += (hash << 10);
    hash ^= (hash >> 6);
    
    hash += ((uint32_t)t->src_port << 16) | t->dst_port;
    hash += (hash << 10);
    hash ^= (hash >> 6);
    
    hash += t->proto;
    hash += (hash << 10);
    hash ^= (hash >> 6);
    
    /* Final mix */
    hash += (hash << 3);
    hash ^= (hash >> 11);
    hash += (hash << 15);
    
    return hash % NAT_TABLE_SIZE;
}

/* ═══════════════════════════════════════════════════════════
   NAT TABLE CREATION
   ═══════════════════════════════════════════════════════════ */

nat_table_t* nat_table_create(const nat_config_t *config) {
    nat_table_t *table = calloc(1, sizeof(nat_table_t));
    if (!table) {
        perror("calloc");
        return NULL;
    }
    
    /* Copy configuration */
    memcpy(&table->config, config, sizeof(nat_config_t));
    
    /* Initialize mutex for thread safety */
    if (pthread_mutex_init(&table->lock, NULL) != 0) {
        free(table);
        return NULL;
    }
    
    /* Start port allocation from port_start */
    table->next_port = config->port_start;
    
    fprintf(stderr, "NAT table created:\n");
    fprintf(stderr, "  Public IP: %s\n", 
            inet_ntoa((struct in_addr){config->public_ip}));
    fprintf(stderr, "  Port range: %d-%d\n", 
            config->port_start, config->port_end);
    
    return table;
}

/* ═══════════════════════════════════════════════════════════
   PORT ALLOCATION
   ═══════════════════════════════════════════════════════════ */

/* Allocate next available port in our range */
static uint16_t allocate_port(nat_table_t *table) {
    /* Simple sequential allocation — in production, 
       use a bitmap or circular buffer for O(1) allocation */
    uint16_t start = table->next_port;
    
    do {
        uint16_t port = table->next_port++;
        if (table->next_port > table->config.port_end)
            table->next_port = table->config.port_start;
        
        /* Check if port is in use by scanning reverse lookup */
        /* For simplicity — in production use a separate port bitmap */
        int in_use = 0;
        for (int i = 0; i < NAT_TABLE_SIZE; i++) {
            nat_entry_t *e = table->buckets[i];
            while (e) {
                if (e->nat_port == port && e->original.proto != 0) {
                    in_use = 1;
                    break;
                }
                e = e->next;
            }
            if (in_use) break;
        }
        
        if (!in_use) return port;
        
    } while (table->next_port != start); /* Wrapped around */
    
    return 0; /* Port exhaustion */
}

/* ═══════════════════════════════════════════════════════════
   LOOKUP FUNCTIONS
   ═══════════════════════════════════════════════════════════ */

/* Look up by original 5-tuple (outbound SNAT lookup) */
nat_entry_t* nat_table_lookup_forward(nat_table_t *table,
                                       const five_tuple_t *tuple) {
    uint32_t bucket = hash_five_tuple(tuple);
    nat_entry_t *entry = table->buckets[bucket];
    
    while (entry) {
        if (entry->original.src_ip   == tuple->src_ip   &&
            entry->original.dst_ip   == tuple->dst_ip   &&
            entry->original.src_port == tuple->src_port &&
            entry->original.dst_port == tuple->dst_port &&
            entry->original.proto    == tuple->proto) {
            return entry;  /* Found! */
        }
        entry = entry->next;
    }
    
    return NULL;  /* Not found */
}

/* Look up by NAT IP:port (inbound reverse lookup) */
nat_entry_t* nat_table_lookup_reverse(nat_table_t *table,
                                       uint32_t nat_ip, uint16_t nat_port,
                                       uint8_t proto) {
    /* Scan all buckets for reverse lookup 
       For high performance: use separate hash table keyed by nat_port */
    for (int i = 0; i < NAT_TABLE_SIZE; i++) {
        nat_entry_t *entry = table->buckets[i];
        while (entry) {
            if (entry->nat_ip   == nat_ip   &&
                entry->nat_port == nat_port &&
                entry->original.proto == proto) {
                return entry;
            }
            entry = entry->next;
        }
    }
    return NULL;
}

/* ═══════════════════════════════════════════════════════════
   INSERT NEW NAT ENTRY
   ═══════════════════════════════════════════════════════════ */

nat_entry_t* nat_table_insert(nat_table_t *table,
                               const five_tuple_t *tuple) {
    /* Allocate new port */
    uint16_t port = allocate_port(table);
    if (port == 0) {
        fprintf(stderr, "ERROR: Port exhaustion! All NAT ports in use.\n");
        return NULL;
    }
    
    /* Create entry */
    nat_entry_t *entry = calloc(1, sizeof(nat_entry_t));
    if (!entry) {
        perror("calloc");
        return NULL;
    }
    
    /* Fill in the entry */
    memcpy(&entry->original, tuple, sizeof(five_tuple_t));
    entry->nat_ip   = table->config.public_ip;
    entry->nat_port = htons(port);  /* Store in network byte order */
    entry->state    = NAT_STATE_NEW;
    entry->created  = time(NULL);
    entry->last_seen = entry->created;
    
    /* Insert into hash table */
    uint32_t bucket = hash_five_tuple(tuple);
    entry->next = table->buckets[bucket];
    table->buckets[bucket] = entry;
    
    table->total_entries++;
    table->total_translations++;
    
    return entry;
}

/* ═══════════════════════════════════════════════════════════
   CHECKSUM CALCULATION
   ═══════════════════════════════════════════════════════════ */

/* Internet checksum (RFC 1071) */
uint16_t ip_checksum(const void *data, size_t len) {
    const uint16_t *buf = data;
    uint32_t sum = 0;
    
    /* Sum all 16-bit words */
    while (len > 1) {
        sum += *buf++;
        len -= 2;
    }
    
    /* Handle odd byte */
    if (len == 1) {
        sum += *(const uint8_t*)buf;
    }
    
    /* Fold 32-bit sum to 16 bits */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    
    return ~sum;  /* One's complement */
}

/* Pseudo-header for TCP/UDP checksum computation */
struct pseudo_header {
    uint32_t src_addr;
    uint32_t dst_addr;
    uint8_t  zero;
    uint8_t  protocol;
    uint16_t tcp_length;
};

uint16_t tcp_checksum(const struct iphdr *ip, const struct tcphdr *tcp,
                       const uint8_t *payload, size_t payload_len) {
    struct pseudo_header psh;
    psh.src_addr  = ip->saddr;
    psh.dst_addr  = ip->daddr;
    psh.zero      = 0;
    psh.protocol  = IPPROTO_TCP;
    psh.tcp_length = htons(sizeof(struct tcphdr) + payload_len);
    
    /* Build buffer: pseudo_header + tcp_header + payload */
    size_t total = sizeof(psh) + sizeof(struct tcphdr) + payload_len;
    uint8_t *buf = malloc(total);
    if (!buf) return 0;
    
    memcpy(buf, &psh, sizeof(psh));
    memcpy(buf + sizeof(psh), tcp, sizeof(struct tcphdr));
    if (payload && payload_len > 0)
        memcpy(buf + sizeof(psh) + sizeof(struct tcphdr), payload, payload_len);
    
    uint16_t csum = ip_checksum(buf, total);
    free(buf);
    return csum;
}

/* ═══════════════════════════════════════════════════════════
   OUTBOUND PACKET PROCESSING (SNAT)
   ═══════════════════════════════════════════════════════════ */

/*
 * Process outbound packet: apply SNAT
 * Packet flows: private_host → public_internet
 * We change: src_ip, src_port
 *
 * Returns: 0 on success, -1 if packet should be dropped
 */
int process_outbound(nat_table_t *table, packet_t *pkt) {
    struct iphdr *ip = (struct iphdr*)pkt->data;
    
    /* Verify it's IP packet with valid length */
    if (pkt->len < sizeof(struct iphdr)) return -1;
    size_t ip_hdr_len = ip->ihl * 4;
    if (pkt->len < ip_hdr_len) return -1;
    
    /* Only handle TCP and UDP */
    if (ip->protocol != IPPROTO_TCP && ip->protocol != IPPROTO_UDP)
        return 0;  /* Pass through unchanged */
    
    /* Check if source is in our private network */
    uint32_t src = ntohl(ip->saddr);
    uint32_t net = ntohl(table->config.private_net);
    uint32_t mask = ntohl(table->config.private_mask);
    
    if ((src & mask) != (net & mask)) {
        return 0;  /* Not our private network, pass through */
    }
    
    /* Extract ports from transport header */
    uint16_t src_port = 0, dst_port = 0;
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr*)(pkt->data + ip_hdr_len);
        src_port = tcp->source;
        dst_port = tcp->dest;
    } else {
        struct udphdr *udp = (struct udphdr*)(pkt->data + ip_hdr_len);
        src_port = udp->source;
        dst_port = udp->dest;
    }
    
    /* Build 5-tuple */
    five_tuple_t tuple = {
        .src_ip   = ip->saddr,
        .dst_ip   = ip->daddr,
        .src_port = src_port,
        .dst_port = dst_port,
        .proto    = ip->protocol
    };
    
    pthread_mutex_lock(&table->lock);
    
    /* Look up existing entry */
    nat_entry_t *entry = nat_table_lookup_forward(table, &tuple);
    
    if (!entry) {
        /* New connection — create NAT entry */
        entry = nat_table_insert(table, &tuple);
        if (!entry) {
            pthread_mutex_unlock(&table->lock);
            return -1;  /* Port exhaustion */
        }
        
        char src_str[INET_ADDRSTRLEN], nat_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &ip->saddr, src_str, sizeof(src_str));
        inet_ntop(AF_INET, &entry->nat_ip, nat_str, sizeof(nat_str));
        fprintf(stderr, "[NAT] New: %s:%d → %s:%d (proto=%d)\n",
                src_str, ntohs(src_port),
                nat_str, ntohs(entry->nat_port),
                ip->protocol);
    }
    
    /* Update statistics */
    entry->last_seen = time(NULL);
    entry->pkts_fwd++;
    entry->bytes_fwd += pkt->len;
    entry->state = NAT_STATE_ESTABLISHED;
    
    /* Save old values for checksum delta */
    uint32_t old_src_ip   = ip->saddr;
    uint16_t old_src_port = src_port;
    uint32_t new_src_ip   = entry->nat_ip;
    uint16_t new_src_port = entry->nat_port;
    
    pthread_mutex_unlock(&table->lock);
    
    /* ─── Rewrite source IP ─── */
    ip->saddr = new_src_ip;
    
    /* Recalculate IP checksum */
    ip->check = 0;
    ip->check = ip_checksum(ip, ip_hdr_len);
    
    /* ─── Rewrite source port and transport checksum ─── */
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr*)(pkt->data + ip_hdr_len);
        tcp->source = new_src_port;
        
        /* Recalculate TCP checksum */
        size_t payload_len = pkt->len - ip_hdr_len - (tcp->doff * 4);
        uint8_t *payload = pkt->data + ip_hdr_len + (tcp->doff * 4);
        tcp->check = 0;
        tcp->check = tcp_checksum(ip, tcp, payload, payload_len);
        
    } else if (ip->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (struct udphdr*)(pkt->data + ip_hdr_len);
        udp->source = new_src_port;
        
        /* UDP checksum is optional in IPv4, but good practice */
        if (udp->check != 0) {
            size_t payload_len = ntohs(udp->len) - sizeof(struct udphdr);
            uint8_t *payload = pkt->data + ip_hdr_len + sizeof(struct udphdr);
            udp->check = 0;
            udp->check = udp_checksum(ip, udp, payload, payload_len);
        }
    }
    
    return 0;
}

/* ═══════════════════════════════════════════════════════════
   INBOUND PACKET PROCESSING (Reverse DNAT)
   ═══════════════════════════════════════════════════════════ */

/*
 * Process inbound packet: reverse NAT (DNAT back to original)
 * Packet flows: public_internet → private_host
 * We change: dst_ip, dst_port (back to original private)
 */
int process_inbound(nat_table_t *table, packet_t *pkt) {
    struct iphdr *ip = (struct iphdr*)pkt->data;
    
    if (pkt->len < sizeof(struct iphdr)) return -1;
    size_t ip_hdr_len = ip->ihl * 4;
    
    if (ip->protocol != IPPROTO_TCP && ip->protocol != IPPROTO_UDP)
        return 0;
    
    /* Extract destination port */
    uint16_t dst_port = 0;
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr*)(pkt->data + ip_hdr_len);
        dst_port = tcp->dest;
    } else {
        struct udphdr *udp = (struct udphdr*)(pkt->data + ip_hdr_len);
        dst_port = udp->dest;
    }
    
    pthread_mutex_lock(&table->lock);
    
    /* Reverse lookup: who owns this NAT IP:port? */
    nat_entry_t *entry = nat_table_lookup_reverse(
        table, ip->daddr, dst_port, ip->protocol);
    
    if (!entry) {
        pthread_mutex_unlock(&table->lock);
        return -1;  /* No NAT entry — drop packet */
    }
    
    /* Update statistics */
    entry->last_seen = time(NULL);
    entry->pkts_rev++;
    entry->bytes_rev += pkt->len;
    
    uint32_t new_dst_ip   = entry->original.src_ip;
    uint16_t new_dst_port = entry->original.src_port;
    
    pthread_mutex_unlock(&table->lock);
    
    /* Rewrite destination IP */
    ip->daddr = new_dst_ip;
    
    /* Recalculate IP checksum */
    ip->check = 0;
    ip->check = ip_checksum(ip, ip_hdr_len);
    
    /* Rewrite destination port */
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr*)(pkt->data + ip_hdr_len);
        tcp->dest = new_dst_port;
        
        size_t payload_len = pkt->len - ip_hdr_len - (tcp->doff * 4);
        uint8_t *payload = pkt->data + ip_hdr_len + (tcp->doff * 4);
        tcp->check = 0;
        tcp->check = tcp_checksum(ip, tcp, payload, payload_len);
        
    } else if (ip->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (struct udphdr*)(pkt->data + ip_hdr_len);
        udp->dest = new_dst_port;
        
        if (udp->check != 0) {
            size_t payload_len = ntohs(udp->len) - sizeof(struct udphdr);
            uint8_t *payload = pkt->data + ip_hdr_len + sizeof(struct udphdr);
            udp->check = 0;
            udp->check = udp_checksum(ip, udp, payload, payload_len);
        }
    }
    
    return 0;
}

/* ═══════════════════════════════════════════════════════════
   CLEANUP — Remove expired entries
   ═══════════════════════════════════════════════════════════ */

void nat_table_cleanup(nat_table_t *table) {
    time_t now = time(NULL);
    
    pthread_mutex_lock(&table->lock);
    
    for (int i = 0; i < NAT_TABLE_SIZE; i++) {
        nat_entry_t **pp = &table->buckets[i];
        nat_entry_t *entry = *pp;
        
        while (entry) {
            int timeout;
            if (entry->original.proto == IPPROTO_TCP)
                timeout = table->config.tcp_timeout;
            else
                timeout = table->config.udp_timeout;
            
            if (now - entry->last_seen > timeout) {
                /* Entry expired — remove it */
                nat_entry_t *dead = entry;
                *pp = entry->next;
                entry = entry->next;
                table->total_entries--;
                free(dead);
            } else {
                pp = &entry->next;
                entry = entry->next;
            }
        }
    }
    
    pthread_mutex_unlock(&table->lock);
}

/* ═══════════════════════════════════════════════════════════
   UTILITY FUNCTIONS
   ═══════════════════════════════════════════════════════════ */

void print_nat_table(const nat_table_t *table) {
    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║              NAT TABLE (%lu entries)               ║\n",
           table->total_entries);
    printf("╠══════════════════════════════════════════════════════╣\n");
    printf("║ %-20s %-20s %s ║\n", "ORIGINAL", "NAT", "STATE");
    printf("╠══════════════════════════════════════════════════════╣\n");
    
    char src_str[INET_ADDRSTRLEN], nat_str[INET_ADDRSTRLEN];
    
    for (int i = 0; i < NAT_TABLE_SIZE; i++) {
        nat_entry_t *entry = table->buckets[i];
        while (entry) {
            inet_ntop(AF_INET, &entry->original.src_ip, src_str, sizeof(src_str));
            inet_ntop(AF_INET, &entry->nat_ip, nat_str, sizeof(nat_str));
            
            printf("║ %s:%-5d → %s:%-5d %s ║\n",
                   src_str, ntohs(entry->original.src_port),
                   nat_str, ntohs(entry->nat_port),
                   entry->state == NAT_STATE_ESTABLISHED ? "ESTABLISHED" : "NEW");
            
            entry = entry->next;
        }
    }
    printf("╚══════════════════════════════════════════════════════╝\n");
}

void nat_table_destroy(nat_table_t *table) {
    if (!table) return;
    
    for (int i = 0; i < NAT_TABLE_SIZE; i++) {
        nat_entry_t *entry = table->buckets[i];
        while (entry) {
            nat_entry_t *next = entry->next;
            free(entry);
            entry = next;
        }
    }
    
    pthread_mutex_destroy(&table->lock);
    free(table);
}
```

## 29.4 Main Program — Raw Socket NAT

```c
/* nat_main.c */
#include "nat_engine.h"
#include 
#include 
#include 
#include 
#include 
#include <sys/socket.h>
#include <netinet/in.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include 
#include 

/* Global NAT table */
static nat_table_t *g_nat_table = NULL;
static volatile int g_running = 1;

/* Signal handler */
void signal_handler(int sig) {
    fprintf(stderr, "\nCaught signal %d, shutting down...\n", sig);
    g_running = 0;
}

/* Cleanup thread — runs every 30 seconds */
void* cleanup_thread(void *arg) {
    nat_table_t *table = (nat_table_t*)arg;
    
    while (g_running) {
        sleep(30);
        fprintf(stderr, "[Cleanup] Removing expired NAT entries...\n");
        nat_table_cleanup(table);
    }
    
    return NULL;
}

/* Get interface index and IP */
int get_if_info(const char *ifname, int *idx, uint32_t *ip) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;
    
    struct ifreq req;
    strncpy(req.ifr_name, ifname, IFNAMSIZ);
    
    /* Get interface index */
    if (ioctl(fd, SIOCGIFINDEX, &req) < 0) {
        close(fd);
        return -1;
    }
    *idx = req.ifr_ifindex;
    
    /* Get interface IP */
    if (ioctl(fd, SIOCGIFADDR, &req) < 0) {
        close(fd);
        return -1;
    }
    struct sockaddr_in *sin = (struct sockaddr_in*)&req.ifr_addr;
    *ip = sin->sin_addr.s_addr;
    
    close(fd);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s   <private_net/mask> \n", argv[0]);
        fprintf(stderr, "Example: %s eth1 eth0 192.168.1.0/24 203.0.113.1\n", argv[0]);
        return 1;
    }
    
    char *lan_if = argv[1];
    char *wan_if = argv[2];
    
    /* Parse private network CIDR */
    char net_str[32];
    int prefix_len;
    strncpy(net_str, argv[3], sizeof(net_str));
    char *slash = strchr(net_str, '/');
    if (!slash) {
        fprintf(stderr, "Invalid network format. Use: IP/prefix\n");
        return 1;
    }
    *slash = '\0';
    prefix_len = atoi(slash + 1);
    
    /* Configure NAT */
    nat_config_t config = {0};
    
    inet_aton(net_str, (struct in_addr*)&config.private_net);
    uint32_t mask = prefix_len > 0 ? (0xFFFFFFFF << (32 - prefix_len)) : 0;
    config.private_mask = htonl(mask);
    
    inet_aton(argv[4], (struct in_addr*)&config.public_ip);
    
    strncpy(config.lan_interface, lan_if, sizeof(config.lan_interface));
    strncpy(config.wan_interface, wan_if, sizeof(config.wan_interface));
    config.port_start  = NAT_PORT_START;
    config.port_end    = NAT_PORT_END;
    config.tcp_timeout = NAT_TCP_TIMEOUT;
    config.udp_timeout = NAT_UDP_TIMEOUT;
    
    /* Create NAT table */
    g_nat_table = nat_table_create(&config);
    if (!g_nat_table) {
        fprintf(stderr, "Failed to create NAT table\n");
        return 1;
    }
    
    /* Create raw sockets for packet capture */
    /* Note: In production, use nfqueue or kernel NAT instead */
    int lan_fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_IP));
    int wan_fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_IP));
    
    if (lan_fd < 0 || wan_fd < 0) {
        perror("socket (need root/CAP_NET_RAW)");
        nat_table_destroy(g_nat_table);
        return 1;
    }
    
    /* Signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    /* Start cleanup thread */
    pthread_t cleanup_tid;
    pthread_create(&cleanup_tid, NULL, cleanup_thread, g_nat_table);
    
    fprintf(stderr, "\n[NAT Engine Started]\n");
    fprintf(stderr, "  LAN: %s\n  WAN: %s\n", lan_if, wan_if);
    fprintf(stderr, "  Private net: %s/%d\n", net_str, prefix_len);
    fprintf(stderr, "  Public IP: %s\n\n", argv[4]);
    
    /* Main packet processing loop */
    packet_t pkt;
    
    while (g_running) {
        /* Receive packet from LAN interface */
        pkt.len = recvfrom(lan_fd, pkt.data, sizeof(pkt.data), 
                           MSG_DONTWAIT, NULL, NULL);
        
        if (pkt.len > 0) {
            /* Skip Ethernet header (14 bytes) */
            if (pkt.len > 14) {
                /* Check if it's IP (Ethernet type 0x0800) */
                uint16_t eth_type = ntohs(*(uint16_t*)(pkt.data + 12));
                if (eth_type == ETH_P_IP) {
                    /* Move to IP header */
                    memmove(pkt.data, pkt.data + 14, pkt.len - 14);
                    pkt.len -= 14;
                    
                    /* Apply SNAT */
                    if (process_outbound(g_nat_table, &pkt) == 0) {
                        /* Send out WAN interface (simplified) */
                        /* In production: use raw socket sendto with if_index */
                        fprintf(stderr, "[FWD] Packet forwarded to WAN\n");
                    }
                }
            }
        }
        
        /* In a real implementation, also poll WAN interface for inbound */
        
        usleep(100);  /* Prevent CPU spin */
    }
    
    /* Cleanup */
    fprintf(stderr, "\nShutting down...\n");
    g_running = 0;
    pthread_join(cleanup_tid, NULL);
    
    print_nat_table(g_nat_table);
    
    close(lan_fd);
    close(wan_fd);
    nat_table_destroy(g_nat_table);
    
    return 0;
}
```

## 29.5 NFQUEUE-based NAT (Practical C Implementation)

```c
/* nfqueue_nat.c — NAT using libnetfilter_queue */
/*
 * This is more practical than raw sockets.
 * Works with: iptables -j NFQUEUE --queue-num 0
 */

#include 
#include 
#include 
#include 
#include 
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <linux/netfilter.h>
#include <libnetfilter_queue/libnetfilter_queue.h>

/* Simple NAT entry for demo */
#define MAX_ENTRIES 1024

struct simple_nat_entry {
    uint32_t priv_ip;
    uint16_t priv_port;
    uint16_t nat_port;
    uint8_t  proto;
    int      active;
};

static struct simple_nat_entry nat_table[MAX_ENTRIES];
static uint32_t public_ip;
static uint16_t next_port = 10000;

/* Find or create NAT mapping */
struct simple_nat_entry* get_nat_entry(uint32_t priv_ip, uint16_t priv_port, 
                                        uint8_t proto) {
    /* Find existing */
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (nat_table[i].active &&
            nat_table[i].priv_ip   == priv_ip &&
            nat_table[i].priv_port == priv_port &&
            nat_table[i].proto     == proto) {
            return &nat_table[i];
        }
    }
    
    /* Create new */
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (!nat_table[i].active) {
            nat_table[i].priv_ip   = priv_ip;
            nat_table[i].priv_port = priv_port;
            nat_table[i].proto     = proto;
            nat_table[i].nat_port  = htons(next_port++);
            nat_table[i].active    = 1;
            return &nat_table[i];
        }
    }
    
    return NULL;  /* Table full */
}

/* Update IP checksum using one's complement delta */
static uint16_t update_checksum(uint16_t old_check,
                                  uint32_t old_val, uint32_t new_val) {
    uint32_t sum = ~ntohs(old_check) & 0xFFFF;
    sum += (~old_val >> 16) & 0xFFFF;
    sum += (~old_val) & 0xFFFF;
    sum += (new_val >> 16) & 0xFFFF;
    sum += new_val & 0xFFFF;
    while (sum >> 16) sum = (sum >> 16) + (sum & 0xFFFF);
    return htons(~sum & 0xFFFF);
}

/* Packet callback — called for each packet from nfqueue */
static int packet_callback(struct nfq_q_handle *qh, struct nfgenmsg *nfmsg,
                             struct nfq_data *nfa, void *data) {
    uint8_t *packet_data;
    int len = nfq_get_payload(nfa, &packet_data);
    if (len < 0) return -1;
    
    uint32_t id = ntohl(nfq_get_msg_packet_hdr(nfa)->packet_id);
    
    struct iphdr *ip = (struct iphdr*)packet_data;
    size_t ip_len = ip->ihl * 4;
    
    /* Only SNAT outbound traffic from private net */
    uint32_t src = ntohl(ip->saddr);
    
    /* Check if private 192.168.x.x */
    if ((src & 0xFFFF0000) != 0xC0A80000) {
        /* Not private — accept unchanged */
        return nfq_set_verdict(qh, id, NF_ACCEPT, 0, NULL);
    }
    
    /* Make a mutable copy */
    uint8_t buf[65536];
    memcpy(buf, packet_data, len);
    struct iphdr *new_ip = (struct iphdr*)buf;
    
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr*)(buf + ip_len);
        
        struct simple_nat_entry *entry = get_nat_entry(
            ip->saddr, tcp->source, IPPROTO_TCP);
        
        if (!entry) {
            return nfq_set_verdict(qh, id, NF_DROP, 0, NULL);
        }
        
        /* Update IP */
        uint32_t old_ip = new_ip->saddr;
        new_ip->saddr = public_ip;
        new_ip->check = update_checksum(new_ip->check, 
                                         ntohl(old_ip), ntohl(public_ip));
        
        /* Update TCP */
        uint32_t old_port_ip = (uint32_t)ntohs(tcp->source);
        uint32_t new_port_ip = (uint32_t)ntohs(entry->nat_port);
        tcp->check = update_checksum(tcp->check, 
                                      (ntohl(old_ip) ^ old_port_ip),
                                      (ntohl(public_ip) ^ new_port_ip));
        tcp->source = entry->nat_port;
        
        char src_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &ip->saddr, src_str, sizeof(src_str));
        printf("[SNAT] %s:%d → public:%d\n",
               src_str, ntohs(tcp->source), ntohs(entry->nat_port));
    }
    
    /* Accept modified packet */
    return nfq_set_verdict(qh, id, NF_ACCEPT, len, buf);
}

int main(void) {
    /* Set public IP */
    inet_aton("203.0.113.1", (struct in_addr*)&public_ip);
    
    printf("NFQUEUE NAT starting...\n");
    printf("Setup: iptables -t mangle -A PREROUTING -j NFQUEUE --queue-num 0\n\n");
    
    struct nfq_handle *h = nfq_open();
    if (!h) { perror("nfq_open"); return 1; }
    
    struct nfq_q_handle *qh = nfq_create_queue(h, 0, &packet_callback, NULL);
    if (!qh) { perror("nfq_create_queue"); return 1; }
    
    /* Set copy mode: copy entire packet */
    if (nfq_set_mode(qh, NFQNL_COPY_PACKET, 0xFFFF) < 0) {
        perror("nfq_set_mode");
        return 1;
    }
    
    int fd = nfq_fd(h);
    char buf[65536] __attribute__((aligned));
    
    printf("Listening on NFQUEUE 0...\n");
    
    int rv;
    while ((rv = recv(fd, buf, sizeof(buf), 0)) >= 0) {
        nfq_handle_packet(h, buf, rv);
    }
    
    nfq_destroy_queue(qh);
    nfq_close(h);
    
    return 0;
}

/*
Compile:
  gcc -O2 -Wall -o nfqueue_nat nfqueue_nat.c -lnetfilter_queue

Usage:
  # Setup NFQUEUE rule (packets go to userspace)
  iptables -t mangle -A PREROUTING -s 192.168.0.0/16 -j NFQUEUE --queue-num 0
  
  # Run our NAT engine
  sudo ./nfqueue_nat
*/
```

## 29.6 Transparent Proxy in C (TPROXY)

```c
/* tproxy_server.c — Transparent proxy accepting TCP connections */
#include 
#include 
#include 
#include 
#include 
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <linux/netfilter_ipv4.h>

#define PROXY_PORT 8080
#define BUFFER_SIZE 4096

/* Get the original destination for a TPROXY/REDIRECT socket */
int get_orig_dst(int fd, struct sockaddr_in *orig_dst) {
    socklen_t len = sizeof(struct sockaddr_in);
    
    /* Method 1: SO_ORIGINAL_DST (works with REDIRECT) */
    if (getsockopt(fd, SOL_IP, SO_ORIGINAL_DST, orig_dst, &len) == 0) {
        return 0;
    }
    
    /* Method 2: getsockname (works with TPROXY) */
    if (getsockname(fd, (struct sockaddr*)orig_dst, &len) == 0) {
        return 0;
    }
    
    return -1;
}

/* Create transparent proxy server socket */
int create_tproxy_socket(int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); return -1; }
    
    /* SO_REUSEADDR */
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    
    /* IP_TRANSPARENT: allows binding to non-local addresses
       This is required for TPROXY to work */
    if (setsockopt(fd, SOL_IP, IP_TRANSPARENT, &one, sizeof(one)) < 0) {
        perror("setsockopt IP_TRANSPARENT (need CAP_NET_ADMIN)");
        close(fd);
        return -1;
    }
    
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(port)
    };
    
    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(fd);
        return -1;
    }
    
    if (listen(fd, 128) < 0) {
        perror("listen");
        close(fd);
        return -1;
    }
    
    return fd;
}

/* Handle one client connection */
void handle_client(int client_fd) {
    /* Find out where the client REALLY wanted to go */
    struct sockaddr_in orig_dst;
    if (get_orig_dst(client_fd, &orig_dst) < 0) {
        fprintf(stderr, "Failed to get original destination\n");
        close(client_fd);
        return;
    }
    
    char orig_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &orig_dst.sin_addr, orig_ip, sizeof(orig_ip));
    
    printf("[Proxy] Client intercepted → originally wanted: %s:%d\n",
           orig_ip, ntohs(orig_dst.sin_port));
    
    /* Connect to original destination on behalf of client */
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); close(client_fd); return; }
    
    if (connect(server_fd, (struct sockaddr*)&orig_dst, sizeof(orig_dst)) < 0) {
        fprintf(stderr, "Cannot connect to %s:%d: %s\n",
                orig_ip, ntohs(orig_dst.sin_port), strerror(errno));
        close(server_fd);
        close(client_fd);
        return;
    }
    
    printf("[Proxy] Connected to %s:%d — relaying traffic\n",
           orig_ip, ntohs(orig_dst.sin_port));
    
    /* Relay data between client and server */
    char buf[BUFFER_SIZE];
    fd_set fds;
    
    while (1) {
        FD_ZERO(&fds);
        FD_SET(client_fd, &fds);
        FD_SET(server_fd, &fds);
        
        int max_fd = (client_fd > server_fd ? client_fd : server_fd) + 1;
        
        if (select(max_fd, &fds, NULL, NULL, NULL) < 0) break;
        
        if (FD_ISSET(client_fd, &fds)) {
            ssize_t n = read(client_fd, buf, sizeof(buf));
            if (n <= 0) break;
            write(server_fd, buf, n);
        }
        
        if (FD_ISSET(server_fd, &fds)) {
            ssize_t n = read(server_fd, buf, sizeof(buf));
            if (n <= 0) break;
            write(client_fd, buf, n);
        }
    }
    
    close(server_fd);
    close(client_fd);
}

int main(void) {
    printf("Transparent proxy starting on port %d\n", PROXY_PORT);
    printf("Setup iptables:\n");
    printf("  iptables -t mangle -A PREROUTING -p tcp --dport 80 \\\n");
    printf("    -j TPROXY --tproxy-mark 0x1/0x1 --on-port %d\n", PROXY_PORT);
    printf("  ip rule add fwmark 0x1 lookup 100\n");
    printf("  ip route add local default dev lo table 100\n\n");
    
    int server_fd = create_tproxy_socket(PROXY_PORT);
    if (server_fd < 0) return 1;
    
    while (1) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        
        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) { perror("accept"); continue; }
        
        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, sizeof(client_ip));
        printf("[Proxy] Client from %s:%d\n", 
               client_ip, ntohs(client_addr.sin_port));
        
        /* In production: use fork() or thread pool */
        handle_client(client_fd);
    }
    
    close(server_fd);
    return 0;
}
```

---

# 30. Rust Implementation — Safe NAT Engine

## 30.1 Cargo.toml

```toml
[package]
name = "nat-engine"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "nat-engine"
path = "src/main.rs"

[[bin]]
name = "tproxy"
path = "src/tproxy.rs"

[dependencies]
# Async runtime
tokio = { version = "1", features = ["full"] }

# Network utilities
pnet = "0.34"              # Packet parsing
socket2 = "0.5"            # Advanced socket options

# Data structures
dashmap = "5"              # Concurrent HashMap (no mutex needed)
fnv = "1.0"                # Fast hash for network data

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Serialization
serde = { version = "1.0", features = ["derive"] }

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
```

## 30.2 Core Types (src/types.rs)

```rust
// src/types.rs
//! Core types for the NAT engine.
//! Rust's type system lets us encode invariants at compile time.

use std::net::{Ipv4Addr, SocketAddrV4};
use std::time::{Duration, Instant};
use std::fmt;

/// ─── Protocol ─────────────────────────────────────────────────────────────
/// We model protocol as a type-safe enum instead of a raw u8.
/// This prevents accidentally using invalid protocol numbers.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Protocol {
    Tcp,
    Udp,
    Icmp,
    Other(u8),
}

impl Protocol {
    pub fn from_u8(val: u8) -> Self {
        match val {
            6  => Protocol::Tcp,
            17 => Protocol::Udp,
            1  => Protocol::Icmp,
            n  => Protocol::Other(n),
        }
    }

    pub fn to_u8(self) -> u8 {
        match self {
            Protocol::Tcp      => 6,
            Protocol::Udp      => 17,
            Protocol::Icmp     => 1,
            Protocol::Other(n) => n,
        }
    }

    pub fn default_timeout(self) -> Duration {
        match self {
            Protocol::Tcp   => Duration::from_secs(600),
            Protocol::Udp   => Duration::from_secs(30),
            Protocol::Icmp  => Duration::from_secs(30),
            Protocol::Other(_) => Duration::from_secs(60),
        }
    }
}

impl fmt::Display for Protocol {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Protocol::Tcp      => write!(f, "TCP"),
            Protocol::Udp      => write!(f, "UDP"),
            Protocol::Icmp     => write!(f, "ICMP"),
            Protocol::Other(n) => write!(f, "Proto({})", n),
        }
    }
}

/// ─── FiveTuple ────────────────────────────────────────────────────────────
/// A 5-tuple uniquely identifies a connection in one direction.
/// Think of it as the "key" to identify which stream a packet belongs to.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct FiveTuple {
    pub src_ip:   Ipv4Addr,
    pub dst_ip:   Ipv4Addr,
    pub src_port: u16,
    pub dst_port: u16,
    pub protocol: Protocol,
}

impl FiveTuple {
    pub fn new(
        src_ip: Ipv4Addr,
        dst_ip: Ipv4Addr,
        src_port: u16,
        dst_port: u16,
        protocol: Protocol,
    ) -> Self {
        Self { src_ip, dst_ip, src_port, dst_port, protocol }
    }

    /// Get the reverse 5-tuple (for reply packet matching)
    pub fn reverse(&self) -> Self {
        Self {
            src_ip:   self.dst_ip,
            dst_ip:   self.src_ip,
            src_port: self.dst_port,
            dst_port: self.src_port,
            protocol: self.protocol,
        }
    }
}

impl fmt::Display for FiveTuple {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}:{} → {}:{} ({})",
            self.src_ip, self.src_port,
            self.dst_ip, self.dst_port,
            self.protocol)
    }
}

/// ─── NatKey ───────────────────────────────────────────────────────────────
/// Key for reverse lookup: given nat_ip:nat_port → original tuple

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct NatKey {
    pub nat_ip:   Ipv4Addr,
    pub nat_port: u16,
    pub protocol: Protocol,
}

/// ─── NatState ─────────────────────────────────────────────────────────────
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NatState {
    New,
    Established,
    Closing,
    Closed,
}

impl fmt::Display for NatState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            NatState::New         => write!(f, "NEW"),
            NatState::Established => write!(f, "ESTABLISHED"),
            NatState::Closing     => write!(f, "CLOSING"),
            NatState::Closed      => write!(f, "CLOSED"),
        }
    }
}

/// ─── NatEntry ─────────────────────────────────────────────────────────────
/// One NAT translation entry.
///
/// Original direction: original_tuple
/// Translated source:  nat_socket (public IP:port)

#[derive(Debug, Clone)]
pub struct NatEntry {
    /// The original connection from the private host
    pub original: FiveTuple,

    /// The NAT'd address (public IP:port allocated)
    pub nat_socket: SocketAddrV4,

    /// Current state
    pub state: NatState,

    /// When this entry was created
    pub created_at: Instant,

    /// Last packet time (used for timeout)
    pub last_seen: Instant,

    /// Statistics — forward direction (private → internet)
    pub pkts_fwd:  u64,
    pub bytes_fwd: u64,

    /// Statistics — reverse direction (internet → private)
    pub pkts_rev:  u64,
    pub bytes_rev: u64,
}

impl NatEntry {
    pub fn new(original: FiveTuple, nat_socket: SocketAddrV4) -> Self {
        let now = Instant::now();
        Self {
            original,
            nat_socket,
            state:     NatState::New,
            created_at: now,
            last_seen: now,
            pkts_fwd:  0,
            bytes_fwd: 0,
            pkts_rev:  0,
            bytes_rev: 0,
        }
    }

    /// Check if this entry has expired
    pub fn is_expired(&self) -> bool {
        let timeout = self.original.protocol.default_timeout();
        self.last_seen.elapsed() > timeout
    }

    /// Mark as seen (update timestamp and stats)
    pub fn seen_forward(&mut self, bytes: u64) {
        self.last_seen = Instant::now();
        self.pkts_fwd  += 1;
        self.bytes_fwd += bytes;
        self.state = NatState::Established;
    }

    pub fn seen_reverse(&mut self, bytes: u64) {
        self.last_seen = Instant::now();
        self.pkts_rev  += 1;
        self.bytes_rev += bytes;
    }

    /// Age of this entry
    pub fn age(&self) -> Duration {
        self.created_at.elapsed()
    }
}

impl fmt::Display for NatEntry {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f,
            "[{}] {} → nat={} | state={} | fwd={}pkts/{}B rev={}pkts/{}B | age={:.0}s",
            self.original.protocol,
            self.original,
            self.nat_socket,
            self.state,
            self.pkts_fwd, self.bytes_fwd,
            self.pkts_rev, self.bytes_rev,
            self.age().as_secs_f64()
        )
    }
}

/// ─── Config ───────────────────────────────────────────────────────────────
#[derive(Debug, Clone)]
pub struct NatConfig {
    /// Private network to NAT
    pub private_net:  Ipv4Addr,
    pub private_mask: u32,       // In host byte order (e.g., 0xFFFFFF00 for /24)

    /// Public IP to SNAT to
    pub public_ip:    Ipv4Addr,

    /// Ephemeral port range
    pub port_min: u16,
    pub port_max: u16,

    /// Interface names
    pub lan_if: String,
    pub wan_if: String,
}

impl NatConfig {
    /// Check if an IP is in our private network
    pub fn is_private(&self, ip: Ipv4Addr) -> bool {
        let ip_u32 = u32::from(ip);
        let net_u32 = u32::from(self.private_net);
        (ip_u32 & self.private_mask) == (net_u32 & self.private_mask)
    }
}
```

## 30.3 NAT Table (src/nat_table.rs)

```rust
// src/nat_table.rs
//! The core NAT translation table.
//! Uses DashMap for lock-free concurrent access.

use crate::types::*;
use dashmap::DashMap;
use std::net::{Ipv4Addr, SocketAddrV4};
use std::sync::atomic::{AtomicU16, AtomicU64, Ordering};
use std::sync::Arc;
use tracing::{debug, warn, info};

/// ─── Port Allocator ───────────────────────────────────────────────────────
/// Thread-safe sequential port allocator.
/// In production, use a more sophisticated allocator (bitmap, per-CPU pool).

pub struct PortAllocator {
    next_port: AtomicU16,
    port_min:  u16,
    port_max:  u16,
}

impl PortAllocator {
    pub fn new(min: u16, max: u16) -> Self {
        Self {
            next_port: AtomicU16::new(min),
            port_min: min,
            port_max: max,
        }
    }

    /// Allocate next port. Returns None on exhaustion.
    pub fn allocate(&self) -> Option {
        // Relaxed is fine here — we just need an atomic increment.
        // In the worst case, two threads get the same port,
        // which we'd catch in the duplicate check below.
        let port = self.next_port.fetch_add(1, Ordering::Relaxed);

        if port > self.port_max {
            // Wrap around
            self.next_port.store(self.port_min, Ordering::Relaxed);
            let port = self.next_port.fetch_add(1, Ordering::Relaxed);
            if port > self.port_max {
                return None; // Exhausted
            }
            Some(port)
        } else {
            Some(port)
        }
    }
}

/// ─── NatTable ─────────────────────────────────────────────────────────────
/// The main NAT translation table.
///
/// Two hash maps for O(1) bidirectional lookup:
///   forward_map: FiveTuple → NatEntry
///   reverse_map: NatKey → FiveTuple (points back into forward_map)

pub struct NatTable {
    config: NatConfig,

    /// Forward lookup: original 5-tuple → NAT entry
    forward_map: DashMap,

    /// Reverse lookup: nat_ip:nat_port → original 5-tuple
    reverse_map: DashMap,

    /// Port allocator
    port_alloc: PortAllocator,

    /// Statistics
    total_translations: AtomicU64,
    current_entries:    AtomicU64,
    dropped_port_exhaustion: AtomicU64,
}

impl NatTable {
    pub fn new(config: NatConfig) -> Arc {
        let port_alloc = PortAllocator::new(config.port_min, config.port_max);

        info!(
            public_ip = %config.public_ip,
            port_range = ?config.port_min..=config.port_max,
            "NAT table created"
        );

        Arc::new(Self {
            port_alloc,
            forward_map: DashMap::new(),
            reverse_map: DashMap::new(),
            total_translations: AtomicU64::new(0),
            current_entries: AtomicU64::new(0),
            dropped_port_exhaustion: AtomicU64::new(0),
            config,
        })
    }

    /// ─── FORWARD LOOKUP ───────────────────────────────────────────────────
    /// Called for outbound packets (private → internet).
    /// Returns the NAT mapping (nat_ip, nat_port) if found or newly created.
    pub fn lookup_or_create(&self, tuple: &FiveTuple) -> Option {
        // Fast path: entry already exists
        if let Some(mut entry) = self.forward_map.get_mut(tuple) {
            entry.seen_forward(0); // Update timestamp; bytes updated by caller
            debug!(tuple = %tuple, nat = %entry.nat_socket, "NAT hit");
            return Some(entry.nat_socket);
        }

        // Slow path: create new entry
        self.create_entry(tuple)
    }

    fn create_entry(&self, tuple: &FiveTuple) -> Option {
        // Allocate port
        let port = match self.port_alloc.allocate() {
            Some(p) => p,
            None => {
                warn!("Port exhaustion! Cannot create NAT entry for {}", tuple);
                self.dropped_port_exhaustion.fetch_add(1, Ordering::Relaxed);
                return None;
            }
        };

        let nat_socket = SocketAddrV4::new(self.config.public_ip, port);

        // Create forward entry
        let entry = NatEntry::new(*tuple, nat_socket);

        info!(
            original = %tuple,
            nat = %nat_socket,
            "New NAT translation"
        );

        // Insert into forward map
        self.forward_map.insert(*tuple, entry);

        // Insert into reverse map for O(1) reverse lookup
        let nat_key = NatKey {
            nat_ip:   self.config.public_ip,
            nat_port: port,
            protocol: tuple.protocol,
        };
        self.reverse_map.insert(nat_key, *tuple);

        // Update stats
        self.total_translations.fetch_add(1, Ordering::Relaxed);
        self.current_entries.fetch_add(1, Ordering::Relaxed);

        Some(nat_socket)
    }

    /// ─── REVERSE LOOKUP ───────────────────────────────────────────────────
    /// Called for inbound packets (internet → NAT IP).
    /// Returns the original private address if found.
    pub fn reverse_lookup(&self, nat_ip: Ipv4Addr, nat_port: u16, proto: Protocol)
        -> Option
    {
        let key = NatKey { nat_ip, nat_port, protocol: proto };

        if let Some(original_tuple) = self.reverse_map.get(&key) {
            // Update reverse stats
            if let Some(mut entry) = self.forward_map.get_mut(&*original_tuple) {
                entry.seen_reverse(0);
            }
            Some((original_tuple.src_ip, original_tuple.src_port))
        } else {
            None
        }
    }

    /// ─── CLEANUP ──────────────────────────────────────────────────────────
    /// Remove expired entries. Call this periodically.
    pub fn cleanup_expired(&self) {
        let mut removed = 0usize;

        // Collect expired keys first (can't remove while iterating DashMap)
        let expired: Vec = self.forward_map
            .iter()
            .filter(|r| r.value().is_expired())
            .map(|r| *r.key())
            .collect();

        for tuple in &expired {
            if let Some((_, entry)) = self.forward_map.remove(tuple) {
                // Also remove reverse entry
                let key = NatKey {
                    nat_ip:   *entry.nat_socket.ip(),
                    nat_port: entry.nat_socket.port(),
                    protocol: tuple.protocol,
                };
                self.reverse_map.remove(&key);
                removed += 1;
            }
        }

        if removed > 0 {
            self.current_entries.fetch_sub(removed as u64, Ordering::Relaxed);
            info!(removed, "Cleaned up expired NAT entries");
        }
    }

    /// Statistics
    pub fn stats(&self) -> NatStats {
        NatStats {
            current_entries:         self.current_entries.load(Ordering::Relaxed),
            total_translations:      self.total_translations.load(Ordering::Relaxed),
            dropped_port_exhaustion: self.dropped_port_exhaustion.load(Ordering::Relaxed),
        }
    }

    /// Print all entries (for debugging)
    pub fn dump(&self) {
        println!("\n╔═════════════════════════════════════════════════════════╗");
        println!("║                    NAT TABLE DUMP                      ║");
        println!("╠═════════════════════════════════════════════════════════╣");

        for entry in self.forward_map.iter() {
            println!("║ {}", entry.value());
        }

        let stats = self.stats();
        println!("╠═════════════════════════════════════════════════════════╣");
        println!("║ Total: {} | Current: {} | Dropped: {}",
            stats.total_translations,
            stats.current_entries,
            stats.dropped_port_exhaustion);
        println!("╚═════════════════════════════════════════════════════════╝\n");
    }
}

#[derive(Debug)]
pub struct NatStats {
    pub current_entries:         u64,
    pub total_translations:      u64,
    pub dropped_port_exhaustion: u64,
}
```

## 30.4 Packet Processing (src/packet.rs)

```rust
// src/packet.rs
//! IP packet parsing and header manipulation.
//! We use `pnet` for safe packet parsing.

use crate::types::*;
use anyhow::{anyhow, Result};
use pnet::packet::{
    ip::IpNextHeaderProtocols,
    ipv4::{Ipv4Packet, MutableIpv4Packet},
    tcp::{MutableTcpPacket, TcpPacket},
    udp::{MutableUdpPacket, UdpPacket},
    Packet,
};
use std::net::Ipv4Addr;

/// ─── Parsed Packet ────────────────────────────────────────────────────────
/// A parsed view of a network packet.
#[derive(Debug)]
pub struct ParsedPacket {
    pub ip:       Ipv4Packet,
    pub protocol: Protocol,
    pub src_port: u16,
    pub dst_port: u16,
}

/// Parse raw bytes into a structured packet view.
pub fn parse_packet(data: &[u8]) -> Result<ParsedPacket> {
    let ip = Ipv4Packet::new(data)
        .ok_or_else(|| anyhow!("Not a valid IPv4 packet"))?;

    let protocol = Protocol::from_u8(ip.get_next_level_protocol().0);

    let (src_port, dst_port) = match ip.get_next_level_protocol() {
        IpNextHeaderProtocols::Tcp => {
            let tcp = TcpPacket::new(ip.payload())
                .ok_or_else(|| anyhow!("Invalid TCP header"))?;
            (tcp.get_source(), tcp.get_destination())
        }
        IpNextHeaderProtocols::Udp => {
            let udp = UdpPacket::new(ip.payload())
                .ok_or_else(|| anyhow!("Invalid UDP header"))?;
            (udp.get_source(), udp.get_destination())
        }
        _ => (0, 0), // ICMP etc.
    };

    Ok(ParsedPacket { ip, protocol, src_port, dst_port })
}

/// ─── Checksum Update ──────────────────────────────────────────────────────
/// Efficient incremental checksum update using one's complement arithmetic.
///
/// When you change a field in an IP/TCP header, you don't need to
/// recompute the entire checksum. You can use the delta method:
///
///   new_checksum = old_checksum - old_field + new_field
///   (in one's complement arithmetic)
///
/// This is significantly faster than full recomputation.

pub fn incremental_checksum_update(old_csum: u16, old_val: u32, new_val: u32) -> u16 {
    // Work in 32-bit to handle overflow (carries)
    let mut sum = (!old_csum as u32) & 0xFFFF;
    
    // Subtract old value (add complement = flip bits and add 1)
    sum = sum.wrapping_add((!old_val >> 16) & 0xFFFF);
    sum = sum.wrapping_add((!old_val) & 0xFFFF);
    
    // Add new value
    sum = sum.wrapping_add((new_val >> 16) & 0xFFFF);
    sum = sum.wrapping_add(new_val & 0xFFFF);
    
    // Fold 32-bit → 16-bit
    while sum >> 16 != 0 {
        sum = (sum >> 16) + (sum & 0xFFFF);
    }
    
    !(sum as u16)
}

/// ─── Apply SNAT ───────────────────────────────────────────────────────────
/// Rewrite the source IP and port of a packet.
/// Updates both IP and TCP/UDP checksums efficiently.
///
/// # Arguments
/// * `data` - Mutable packet bytes
/// * `new_src_ip` - New source IP address
/// * `new_src_port` - New source port (0 = don't change port)
///
/// # Returns
/// * `Ok(())` on success
/// * `Err` if packet is invalid
pub fn apply_snat(data: &mut [u8], new_src_ip: Ipv4Addr, new_src_port: u16) -> Result {
    // Get old values before mutation
    let old_src_ip: u32;
    let old_src_port: u16;
    let proto: u8;
    let ip_hdr_len: usize;

    {
        let ip = Ipv4Packet::new(data)
            .ok_or_else(|| anyhow!("Invalid IPv4 packet"))?;
        old_src_ip = u32::from(ip.get_source());
        proto = ip.get_next_level_protocol().0;
        ip_hdr_len = (ip.get_header_length() as usize) * 4;

        let transport = ip.payload();
        old_src_port = match proto {
            6  => TcpPacket::new(transport)
                    .map(|t| t.get_source())
                    .unwrap_or(0),
            17 => UdpPacket::new(transport)
                    .map(|u| u.get_source())
                    .unwrap_or(0),
            _  => 0,
        };
    }

    let new_src_ip_u32 = u32::from(new_src_ip);

    // ── Rewrite IP header ──────────────────────────────────────────────────
    {
        let mut ip_pkt = MutableIpv4Packet::new(data)
            .ok_or_else(|| anyhow!("Cannot create mutable IPv4 packet"))?;

        // Update IP checksum (incremental)
        let old_ip_csum = ip_pkt.get_checksum();
        let new_ip_csum = incremental_checksum_update(
            old_ip_csum,
            old_src_ip,
            new_src_ip_u32
        );
        ip_pkt.set_checksum(new_ip_csum);
        ip_pkt.set_source(new_src_ip);
    }

    // ── Rewrite transport header ───────────────────────────────────────────
    let transport_data = &mut data[ip_hdr_len..];

    match proto {
        6 => {
            // TCP
            let mut tcp = MutableTcpPacket::new(transport_data)
                .ok_or_else(|| anyhow!("Invalid TCP header"))?;

            let old_csum = tcp.get_checksum();

            // Update checksum for IP change
            let csum1 = incremental_checksum_update(old_csum, old_src_ip, new_src_ip_u32);

            // Update checksum for port change
            let csum2 = if new_src_port != 0 {
                incremental_checksum_update(
                    csum1,
                    old_src_port as u32,
                    new_src_port as u32
                )
            } else {
                csum1
            };

            tcp.set_checksum(csum2);
            if new_src_port != 0 {
                tcp.set_source(new_src_port);
            }
        }
        17 => {
            // UDP
            let mut udp = MutableUdpPacket::new(transport_data)
                .ok_or_else(|| anyhow!("Invalid UDP header"))?;

            if udp.get_checksum() != 0 {
                let old_csum = udp.get_checksum();
                let csum1 = incremental_checksum_update(old_csum, old_src_ip, new_src_ip_u32);
                let csum2 = if new_src_port != 0 {
                    incremental_checksum_update(csum1, old_src_port as u32, new_src_port as u32)
                } else {
                    csum1
                };
                udp.set_checksum(csum2);
            }

            if new_src_port != 0 {
                udp.set_source(new_src_port);
            }
        }
        _ => {} // ICMP etc. — no port to update
    }

    Ok(())
}

/// ─── Apply Reverse DNAT ───────────────────────────────────────────────────
/// Rewrite destination IP and port (for inbound reply packets).
pub fn apply_reverse_dnat(data: &mut [u8], new_dst_ip: Ipv4Addr, new_dst_port: u16) -> Result {
    let old_dst_ip: u32;
    let old_dst_port: u16;
    let proto: u8;
    let ip_hdr_len: usize;

    {
        let ip = Ipv4Packet::new(data)
            .ok_or_else(|| anyhow!("Invalid IPv4 packet"))?;
        old_dst_ip = u32::from(ip.get_destination());
        proto = ip.get_next_level_protocol().0;
        ip_hdr_len = (ip.get_header_length() as usize) * 4;

        let transport = ip.payload();
        old_dst_port = match proto {
            6  => TcpPacket::new(transport).map(|t| t.get_destination()).unwrap_or(0),
            17 => UdpPacket::new(transport).map(|u| u.get_destination()).unwrap_or(0),
            _  => 0,
        };
    }

    let new_dst_ip_u32 = u32::from(new_dst_ip);

    {
        let mut ip_pkt = MutableIpv4Packet::new(data).unwrap();
        let old_csum = ip_pkt.get_checksum();
        let new_csum = incremental_checksum_update(old_csum, old_dst_ip, new_dst_ip_u32);
        ip_pkt.set_checksum(new_csum);
        ip_pkt.set_destination(new_dst_ip);
    }

    let transport_data = &mut data[ip_hdr_len..];

    match proto {
        6 => {
            let mut tcp = MutableTcpPacket::new(transport_data).unwrap();
            let csum1 = incremental_checksum_update(
                tcp.get_checksum(), old_dst_ip, new_dst_ip_u32);
            let csum2 = incremental_checksum_update(
                csum1, old_dst_port as u32, new_dst_port as u32);
            tcp.set_checksum(csum2);
            tcp.set_destination(new_dst_port);
        }
        17 => {
            let mut udp = MutableUdpPacket::new(transport_data).unwrap();
            if udp.get_checksum() != 0 {
                let csum1 = incremental_checksum_update(
                    udp.get_checksum(), old_dst_ip, new_dst_ip_u32);
                let csum2 = incremental_checksum_update(
                    csum1, old_dst_port as u32, new_dst_port as u32);
                udp.set_checksum(csum2);
            }
            udp.set_destination(new_dst_port);
        }
        _ => {}
    }

    Ok(())
}
```

## 30.5 Transparent Proxy in Rust (src/tproxy.rs)

```rust
// src/tproxy.rs
//! Transparent proxy implementation in Rust.
//! Intercepts TCP connections via TPROXY or REDIRECT iptables rules.
//!
//! Setup:
//!   iptables -t mangle -A PREROUTING -p tcp --dport 80 \
//!     -j TPROXY --tproxy-mark 0x1/0x1 --on-port 8080
//!   ip rule add fwmark 0x1 lookup 100
//!   ip route add local default dev lo table 100

use anyhow::{Context, Result};
use socket2::{Domain, Protocol, Socket, Type};
use std::net::{SocketAddr, SocketAddrV4, TcpListener, TcpStream};
use std::os::unix::io::FromRawFd;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream as TokioStream;
use tracing::{error, info, warn};

const PROXY_PORT: u16 = 8080;
const BUFFER_SIZE: usize = 8192;

/// SOL_IP = 0 in Linux
const SOL_IP: libc::c_int = 0;
/// IP_TRANSPARENT allows binding to non-local addresses
const IP_TRANSPARENT: libc::c_int = 19;
/// SO_ORIGINAL_DST: get original destination for REDIRECT'd connections
const SO_ORIGINAL_DST: libc::c_int = 80;

/// Get the original destination address for a transparent proxy connection.
///
/// For REDIRECT: the kernel knows original dst via conntrack
/// For TPROXY: getsockname() returns the original dst
fn get_original_dst(fd: i32) -> Result {
    // Try SO_ORIGINAL_DST first (for REDIRECT)
    let mut addr: libc::sockaddr_in = unsafe { std::mem::zeroed() };
    let mut len = std::mem::size_of::() as libc::socklen_t;

    let ret = unsafe {
        libc::getsockopt(
            fd,
            SOL_IP,
            SO_ORIGINAL_DST,
            &mut addr as *mut _ as *mut libc::c_void,
            &mut len,
        )
    };

    if ret == 0 {
        let ip = std::net::Ipv4Addr::from(u32::from_be(addr.sin_addr.s_addr));
        let port = u16::from_be(addr.sin_port);
        return Ok(SocketAddrV4::new(ip, port));
    }

    // Fall back to getsockname (for TPROXY)
    let ret = unsafe {
        libc::getsockname(
            fd,
            &mut addr as *mut _ as *mut libc::sockaddr,
            &mut len,
        )
    };

    if ret == 0 {
        let ip = std::net::Ipv4Addr::from(u32::from_be(addr.sin_addr.s_addr));
        let port = u16::from_be(addr.sin_port);
        Ok(SocketAddrV4::new(ip, port))
    } else {
        Err(anyhow::anyhow!("Cannot get original destination"))
    }
}

/// Create a TCP listener with IP_TRANSPARENT enabled.
///
/// IP_TRANSPARENT is needed to:
/// 1. Accept connections whose original destination is not us (TPROXY)
/// 2. Bind to non-local addresses
fn create_transparent_listener(port: u16) -> Result {
    let socket = Socket::new(Domain::IPV4, Type::STREAM, Some(Protocol::TCP))
        .context("create socket")?;

    socket.set_reuse_address(true)?;

    // Enable IP_TRANSPARENT
    unsafe {
        let one: libc::c_int = 1;
        let ret = libc::setsockopt(
            socket.as_raw_fd(),
            SOL_IP,
            IP_TRANSPARENT,
            &one as *const _ as *const libc::c_void,
            std::mem::size_of::() as libc::socklen_t,
        );
        if ret != 0 {
            return Err(anyhow::anyhow!(
                "setsockopt IP_TRANSPARENT failed: {} (need CAP_NET_ADMIN)",
                std::io::Error::last_os_error()
            ));
        }
    }

    let addr: SocketAddr = format!("0.0.0.0:{}", port).parse()?;
    socket.bind(&addr.into())?;
    socket.listen(128)?;

    // Convert to std::net::TcpListener
    Ok(socket.into())
}

/// Bidirectional relay: copy data between client and server.
async fn relay(client: TokioStream, server: TokioStream) -> Result {
    let (mut client_read, mut client_write) = tokio::io::split(client);
    let (mut server_read, mut server_write) = tokio::io::split(server);

    let client_to_server = async {
        let mut buf = vec![0u8; BUFFER_SIZE];
        loop {
            let n = client_read.read(&mut buf).await?;
            if n == 0 { break; }
            server_write.write_all(&buf[..n]).await?;
        }
        server_write.shutdown().await?;
        Ok::(())
    };

    let server_to_client = async {
        let mut buf = vec![0u8; BUFFER_SIZE];
        loop {
            let n = server_read.read(&mut buf).await?;
            if n == 0 { break; }
            client_write.write_all(&buf[..n]).await?;
        }
        client_write.shutdown().await?;
        Ok::(())
    };

    // Run both directions concurrently
    tokio::try_join!(client_to_server, server_to_client)?;
    Ok(())
}

/// Handle a single intercepted connection.
async fn handle_connection(
    stream: std::net::TcpStream,
    peer_addr: SocketAddr,
) {
    // Get the original destination BEFORE converting to async
    let orig_dst = match get_original_dst(stream.as_raw_fd()) {
        Ok(dst) => dst,
        Err(e) => {
            error!("Failed to get original dst: {}", e);
            return;
        }
    };

    info!(
        client = %peer_addr,
        original_dst = %orig_dst,
        "Intercepted connection"
    );

    // Convert to tokio stream
    stream.set_nonblocking(true).unwrap();
    let client = match TokioStream::from_std(stream) {
        Ok(s) => s,
        Err(e) => { error!("from_std: {}", e); return; }
    };

    // Connect to the original destination
    let server_addr: SocketAddr = orig_dst.into();
    let server = match TokioStream::connect(server_addr).await {
        Ok(s) => s,
        Err(e) => {
            warn!(
                dst = %orig_dst,
                "Cannot connect to original destination: {}",
                e
            );
            return;
        }
    };

    info!(
        client = %peer_addr,
        server = %orig_dst,
        "Relaying traffic"
    );

    if let Err(e) = relay(client, server).await {
        warn!("Relay error: {}", e);
    }

    info!(client = %peer_addr, "Connection closed");
}

#[tokio::main]
async fn main() -> Result {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    info!("Transparent proxy starting on port {}", PROXY_PORT);
    info!("Setup commands:");
    info!("  iptables -t mangle -A PREROUTING -p tcp --dport 80 \\");
    info!("    -j TPROXY --tproxy-mark 0x1/0x1 --on-port {}", PROXY_PORT);
    info!("  ip rule add fwmark 0x1 lookup 100");
    info!("  ip route add local default dev lo table 100");

    let listener = create_transparent_listener(PROXY_PORT)?;
    listener.set_nonblocking(true)?;
    let listener = tokio::net::TcpListener::from_std(listener)?;

    info!("Listening... (waiting for intercepted connections)");

    loop {
        let (stream, peer_addr) = listener.accept().await?;

        // Convert back to std (we need fd for getsockopt)
        let std_stream = stream.into_std()?;

        tokio::spawn(async move {
            handle_connection(std_stream, peer_addr).await;
        });
    }
}
```

## 30.6 Main NAT Engine (src/main.rs)

```rust
// src/main.rs
//! NAT Engine entry point.
//! Uses netlink/nfqueue for packet interception.

mod types;
mod nat_table;
mod packet;

use crate::types::*;
use crate::nat_table::NatTable;
use crate::packet::{apply_snat, apply_reverse_dnat, parse_packet};
use std::net::Ipv4Addr;
use std::sync::Arc;
use std::time::Duration;
use tracing::{error, info, warn};

/// Simulate packet processing (in production, use nfqueue)
fn process_packet(
    nat_table: &Arc,
    config: &NatConfig,
    data: &mut Vec,
    direction: PacketDirection,
) -> ProcessResult {
    let parsed = match parse_packet(data) {
        Ok(p) => p,
        Err(e) => {
            warn!("Cannot parse packet: {}", e);
            return ProcessResult::Accept; // Pass through
        }
    };

    match direction {
        PacketDirection::Outbound => {
            // SNAT: private → internet
            let src_ip = parsed.ip.get_source();

            if !config.is_private(src_ip) {
                return ProcessResult::Accept; // Not our traffic
            }

            let tuple = FiveTuple::new(
                src_ip,
                parsed.ip.get_destination(),
                parsed.src_port,
                parsed.dst_port,
                parsed.protocol,
            );

            // Get or create NAT mapping
            match nat_table.lookup_or_create(&tuple) {
                Some(nat_socket) => {
                    // Apply SNAT
                    if let Err(e) = apply_snat(data, *nat_socket.ip(), nat_socket.port()) {
                        error!("SNAT failed: {}", e);
                        return ProcessResult::Drop;
                    }
                    ProcessResult::Accept
                }
                None => {
                    warn!("Port exhaustion — dropping packet");
                    ProcessResult::Drop
                }
            }
        }

        PacketDirection::Inbound => {
            // Reverse DNAT: internet → private
            let dst_ip = parsed.ip.get_destination();
            let dst_port = parsed.dst_port;

            match nat_table.reverse_lookup(dst_ip, dst_port, parsed.protocol) {
                Some((orig_ip, orig_port)) => {
                    if let Err(e) = apply_reverse_dnat(data, orig_ip, orig_port) {
                        error!("Reverse DNAT failed: {}", e);
                        return ProcessResult::Drop;
                    }
                    ProcessResult::Accept
                }
                None => {
                    // No NAT entry — could be INVALID or untracked
                    ProcessResult::Drop
                }
            }
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum PacketDirection {
    Outbound,
    Inbound,
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum ProcessResult {
    Accept,
    Drop,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_env_filter("info").init();

    info!("NAT Engine starting...");

    let config = NatConfig {
        private_net:  "192.168.1.0".parse().unwrap(),
        private_mask: 0xFFFFFF00, // /24
        public_ip:    "203.0.113.1".parse().unwrap(),
        port_min:     10000,
        port_max:     60000,
        lan_if:       "eth1".to_string(),
        wan_if:       "eth0".to_string(),
    };

    let nat_table = NatTable::new(config.clone());

    // Cleanup task — run every 30 seconds
    let cleanup_table = nat_table.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(30));
        loop {
            interval.tick().await;
            cleanup_table.cleanup_expired();
            let stats = cleanup_table.stats();
            info!(
                current = stats.current_entries,
                total = stats.total_translations,
                dropped = stats.dropped_port_exhaustion,
                "NAT stats"
            );
        }
    });

    // Stats dump task — every 60 seconds
    let dump_table = nat_table.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(60));
        loop {
            interval.tick().await;
            dump_table.dump();
        }
    });

    info!("NAT Engine running. Press Ctrl+C to stop.");
    info!("In production, connect to nfqueue or use kernel NAT.");

    // Simulate some packets for demonstration
    simulate_packets(&nat_table, &config).await;

    // Signal handler
    tokio::signal::ctrl_c().await.expect("Signal handler");
    info!("Shutting down...");
    nat_table.dump();
}

/// Demonstrate NAT processing with simulated packets
async fn simulate_packets(nat_table: &Arc, config: &NatConfig) {
    info!("Simulating NAT translations...");

    // Simulate outbound packets from multiple clients
    let clients = vec![
        ("192.168.1.10", 54321u16, "8.8.8.8", 53u16,  Protocol::Udp),
        ("192.168.1.20", 60000u16, "1.1.1.1", 443u16, Protocol::Tcp),
        ("192.168.1.10", 54322u16, "8.8.4.4", 53u16,  Protocol::Udp),
        ("192.168.1.30", 1024u16,  "9.9.9.9", 80u16,  Protocol::Tcp),
    ];

    for (src, sport, dst, dport, proto) in &clients {
        let src_ip: Ipv4Addr = src.parse().unwrap();
        let dst_ip: Ipv4Addr = dst.parse().unwrap();

        let tuple = FiveTuple::new(src_ip, dst_ip, *sport, *dport, *proto);

        match nat_table.lookup_or_create(&tuple) {
            Some(nat) => info!("  {} → NAT:{}", tuple, nat.port()),
            None      => warn!("  {} → DROPPED (port exhaustion)", tuple),
        }
    }

    // Show the table
    nat_table.dump();
}
```

---

# 31. Performance Tuning NAT

## 31.1 Conntrack Table Sizing

```bash
# Calculate optimal settings based on your traffic:
# Rule of thumb: nf_conntrack_max = (RAM_MB * 1000) / 2
# For 4GB RAM: 4000 * 1000 / 2 = 2,000,000

# Check current count vs max
watch -n1 'echo "Current:"; cat /proc/sys/net/netfilter/nf_conntrack_count; 
           echo "Max:"; cat /proc/sys/net/netfilter/nf_conntrack_max'

# Set max and hashsize (hashsize should be ~1/4 of max)
sysctl -w net.netfilter.nf_conntrack_max=2000000
echo 500000 > /sys/module/nf_conntrack/parameters/hashsize

# Monitor conntrack table drops (important!)
watch -n1 'netstat -s | grep -i conntrack'
# Or:
nstat -az | grep -i conntrack
```

## 31.2 NAT Port Range Optimization

```bash
# Extend ephemeral port range for MASQUERADE
# Default: 32768-60999 (28231 ports)
# Extend to: 1024-65535 (64511 ports) — 2.3x more

sysctl -w net.ipv4.ip_local_port_range="1024 65535"

# Per-destination port reuse (allows more concurrent connections)
# Enable TCP_SYNCOOKIES (reduces half-open connections)
sysctl -w net.ipv4.tcp_syncookies=1

# Enable TCP time wait reuse
sysctl -w net.ipv4.tcp_tw_reuse=1

# Decrease FIN_WAIT2 timeout
sysctl -w net.ipv4.tcp_fin_timeout=15
```

## 31.3 nftables vs iptables Performance

```bash
# nftables with sets is MUCH faster than iptables chains for large rulesets

# iptables: O(N) linear scan of rules
# nftables: O(1) hash set lookup

# Benchmark: 10,000 blocked IPs
# iptables: each packet scans 10,000 rules → very slow!
time for i in $(seq 1 10000); do
    iptables -A FORWARD -s 10.0.$((i/256)).$((i%256)) -j DROP
done

# nftables: same 10,000 IPs in a set → O(1) lookup
nft add set ip filter blocked_ips { type ipv4_addr\; flags interval\; }
# Then bulk load IPs (extremely fast lookup)
nft add rule ip filter forward ip saddr @blocked_ips drop
```

## 31.4 Offloading NAT to Hardware (Flowtable/Fastpath)

```bash
# nftables flowtable: bypass kernel for established flows
# Supported by many NICs with driver support

# Create a flowtable
nft add flowtable ip nat_ft { hook ingress priority -1\; devices = { eth0, eth1 }\; }

# Offload established connections
nft add chain ip filter forward { type filter hook forward priority 0\; }
nft add rule ip filter forward ip protocol { tcp, udp } \
    ct state established flow add @nat_ft

# Benefits:
# - Established flows skip full netfilter processing
# - Orders of magnitude faster for bulk data
# - Can use kernel software fastpath OR NIC hardware offload
```

## 31.5 XPS/RSS for Multi-CPU NAT

```bash
# Receive Side Scaling: distribute NIC packets across CPU cores
# For Intel NICs:
ethtool -N eth0 rx-flow-hash tcp4 sdfn   # Hash by src/dst IP+port
ethtool -N eth0 rx-flow-hash udp4 sdfn

# Set IRQ affinity: spread NIC IRQs across CPUs
for i in /proc/irq/*/smp_affinity; do
    echo ff > $i  # Allow all CPUs
done

# XPS: Transmit Packet Steering
# Map TX queues to CPU cores
for i in /sys/class/net/eth0/queues/tx-*/xps_cpus; do
    echo f > $i
done

# nfqueue with multiple queues (parallel processing)
iptables -t mangle -A PREROUTING -j NFQUEUE --queue-balance 0:3
# → distributes packets across 4 queues (4 worker processes)
```

## 31.6 Kernel Network Optimization

```bash
# /etc/sysctl.d/99-nat-performance.conf

# Increase socket buffers
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 250000

# TCP buffer sizes
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# Disable slow start after idle
net.ipv4.tcp_slow_start_after_idle = 0

# Enable TCP Fast Open
net.ipv4.tcp_fastopen = 3

# Reduce ARP cache pressure
net.ipv4.neigh.default.gc_thresh1 = 4096
net.ipv4.neigh.default.gc_thresh2 = 8192
net.ipv4.neigh.default.gc_thresh3 = 16384

# Increase connection tracking table size
net.netfilter.nf_conntrack_max = 1048576

# Shorter timeouts = smaller table = more room for active connections
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 15
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 15
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 15
net.netfilter.nf_conntrack_tcp_timeout_established = 3600
net.netfilter.nf_conntrack_udp_timeout = 30
net.netfilter.nf_conntrack_udp_timeout_stream = 120

# Disable conntrack for performance-critical traffic
# (use raw table to bypass)
# iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
# iptables -t raw -A OUTPUT -p tcp --sport 80 -j NOTRACK
```

---

# 32. NAT Troubleshooting & Debugging

## 32.1 Systematic Debugging Approach

```
NAT DEBUGGING FLOWCHART:

Problem: Traffic not flowing through NAT

Step 1: Is IP forwarding enabled?
  ├── NO  → echo 1 > /proc/sys/net/ipv4/ip_forward
  └── YES → Step 2

Step 2: Is there a NAT rule?
  ├── iptables -t nat -L -n -v | grep MASQUERADE
  ├── NO  → Add MASQUERADE rule
  └── YES → Step 3

Step 3: Is the packet reaching POSTROUTING?
  ├── Add logging: iptables -t nat -A POSTROUTING -j LOG --log-prefix "POSTROUTING: "
  ├── Check: tail -f /var/log/kern.log | grep POSTROUTING
  ├── NOT ARRIVING → check routing/FORWARD chain
  └── ARRIVING → Step 4

Step 4: Is FORWARD chain allowing it?
  ├── iptables -A FORWARD -j LOG --log-prefix "FORWARD: "
  ├── iptables -L FORWARD -n -v (check default policy)
  └── If DROP → add ACCEPT rule

Step 5: conntrack issue?
  ├── conntrack -L | grep <src_ip>
  ├── dmesg | grep conntrack (look for table full errors)
  └── Check /proc/sys/net/netfilter/nf_conntrack_count vs max
```

## 32.2 Essential Debugging Commands

```bash
# ─── iptables debugging ───────────────────────────────────────────────────

# Add logging to trace packet flow
iptables -t nat -A PREROUTING -j LOG --log-prefix "[NAT-PRE] " --log-level 4
iptables -t nat -A POSTROUTING -j LOG --log-prefix "[NAT-POST] " --log-level 4
iptables -A FORWARD -j LOG --log-prefix "[FORWARD] " --log-level 4

# Watch logs
tail -f /var/log/kern.log | grep NAT

# View all rules with packet counters
iptables -t nat -L -n -v --line-numbers
iptables -L -n -v --line-numbers

# Reset counters
iptables -t nat -Z

# ─── conntrack debugging ─────────────────────────────────────────────────

# Watch new connections
conntrack -E -e NEW

# Watch all events
conntrack -E

# Find specific connection
conntrack -L | grep 192.168.1.10

# Count by state
conntrack -L | awk '{print $4}' | sort | uniq -c | sort -rn

# Check for conntrack table full
dmesg | grep "nf_conntrack: table full"

# ─── tcpdump — see actual packets ────────────────────────────────────────

# Capture on LAN interface (before NAT)
tcpdump -i eth1 -n 'host 192.168.1.10'

# Capture on WAN interface (after NAT)
tcpdump -i eth0 -n 'host 203.0.113.1'

# Capture and show full packet details
tcpdump -i eth0 -nn -vvv -X

# Show only TCP SYN packets (new connections)
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'

# Capture to file for Wireshark analysis
tcpdump -i eth0 -w /tmp/capture.pcap

# ─── ip command debugging ────────────────────────────────────────────────

# Show routing table
ip route show

# Show specific route
ip route get 8.8.8.8

# Show routing rules
ip rule list

# Check interface stats
ip -s link show eth0

# ─── nftables debugging ──────────────────────────────────────────────────

# Enable tracing for specific packets (nftables)
nft add chain ip filter trace_chain { type filter hook prerouting priority -301\; }
nft add rule ip filter trace_chain ip saddr 192.168.1.10 meta nftrace set 1
nft monitor trace  # Watch trace output

# ─── ss and netstat ──────────────────────────────────────────────────────

# Show all connections (fast)
ss -an

# Show TCP connections with process
ss -tnp

# Show UDP
ss -unp

# Show listen ports
ss -lntp

# ─── ping tests ──────────────────────────────────────────────────────────

# Test basic connectivity
ping -I eth1 8.8.8.8  # From LAN interface

# Trace route
traceroute 8.8.8.8

# Test with specific source
ping -S 192.168.1.10 8.8.8.8

# ─── nmap for port forwarding verification ───────────────────────────────

# Test if port forward is working
nmap -p 80 203.0.113.1  # Should connect to internal web server
```

## 32.3 Common Problems and Solutions

```
PROBLEM: "I set up MASQUERADE but internet doesn't work"

CHECK 1: ip_forward
  cat /proc/sys/net/ipv4/ip_forward
  FIX: echo 1 > /proc/sys/net/ipv4/ip_forward

CHECK 2: FORWARD chain policy
  iptables -L FORWARD -n | head -1
  FIX: iptables -P FORWARD ACCEPT (or add explicit ACCEPT rules)

CHECK 3: MASQUERADE rule on correct interface
  iptables -t nat -L POSTROUTING -n -v
  MUST show: -o eth0 (your WAN interface!)
  FIX: Check interface name (ip link show)

CHECK 4: Default route on clients
  ip route show
  Must have: default via 192.168.1.1 (your NAT router)
  FIX: ip route add default via 192.168.1.1

────────────────────────────────────────────────────────────

PROBLEM: "Port forwarding not working"

CHECK 1: DNAT rule exists
  iptables -t nat -L PREROUTING -n -v
  Must show: DNAT tcp dpt:80 to:192.168.1.10:8080

CHECK 2: FORWARD chain allows it
  iptables -L FORWARD -n | grep 192.168.1.10
  FIX: iptables -A FORWARD -d 192.168.1.10 -p tcp --dport 8080 -j ACCEPT

CHECK 3: Internal server is actually listening
  ss -lntp | grep 8080  (on the server)

CHECK 4: Client can reach internal server directly
  curl http://192.168.1.10:8080  (from router)

CHECK 5: Hairpin NAT if testing from inside
  Add: iptables -t nat -A POSTROUTING -d 192.168.1.10 -j MASQUERADE

────────────────────────────────────────────────────────────

PROBLEM: "conntrack table full — connections failing"

SYMPTOMS:
  dmesg: "nf_conntrack: table full, dropping packet"
  
FIXES:
  # Short term: increase max
  sysctl -w net.netfilter.nf_conntrack_max=1048576
  
  # Medium term: decrease timeouts
  sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=3600
  sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=15
  
  # Long term: analyze what's filling the table
  conntrack -L | awk '{print $4}' | sort | uniq -c
  # Many TIME_WAIT → web server needs more aggressive recycling
  # Many ESTABLISHED → check for connection leaks

────────────────────────────────────────────────────────────

PROBLEM: "SNAT not working for specific protocol"

CHECK: Does your rule match the protocol?
  iptables -t nat -A POSTROUTING -o eth0 -p tcp -j MASQUERADE
  iptables -t nat -A POSTROUTING -o eth0 -p udp -j MASQUERADE
  iptables -t nat -A POSTROUTING -o eth0 -p icmp -j MASQUERADE

Or use a single all-protocol rule:
  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
  (no -p = matches all protocols)
```

## 32.4 nflog — Advanced Packet Logging

```bash
# Use NFLOG for structured logging (better than LOG target)
iptables -t nat -A PREROUTING -j NFLOG --nflog-group 1 --nflog-prefix "PREROUTING"
iptables -t nat -A POSTROUTING -j NFLOG --nflog-group 2 --nflog-prefix "POSTROUTING"

# Capture with ulogd or tcpdump
tcpdump -i nflog:1 -n  # Capture nflog group 1

# Or use nflog with tcpdump nflog interface
# Great for seeing packets AT specific hook points
```

---

# 33. Security Implications of NAT

## 33.1 NAT as a (Weak) Security Mechanism

```
MYTH: "NAT is a firewall"
REALITY: NAT provides SOME security, but it is NOT a firewall

NAT Security Properties:
  ✓ External hosts cannot initiate connections to private hosts
    (no inbound mapping without explicit DNAT)
  ✓ Private IP addresses are hidden from the internet
  ✓ Port scanning the NAT IP reveals nothing about private hosts

NAT Security Weaknesses:
  ✗ Any private host can initiate connections to internet
    (no outbound filtering)
  ✗ Malware on private host can phone home freely
  ✗ DNAT rules expose internal servers
  ✗ DNS rebinding attacks can bypass NAT
  ✗ IPv6 may bypass NAT entirely (misconfigured dual-stack)
  
Firewall properties NAT LACKS:
  - Deep packet inspection
  - Application layer filtering
  - Content filtering
  - State-based outbound rules
  - IDS/IPS capabilities
```

## 33.2 Port Prediction Attack

```
SYMMETRIC NAT Port Prediction Attack:

If attacker can observe multiple requests from behind NAT,
they can predict the next allocated port:
  Connection 1: public port 40001
  Connection 2: public port 40002
  Connection 3: (predicted) 40003

Mitigation:
  iptables -t nat -A POSTROUTING -j MASQUERADE --random
  iptables -t nat -A POSTROUTING -j MASQUERADE --random-fully
  
  # Or in nftables:
  masquerade random
  masquerade fully-random
```

## 33.3 NAT Slipstreaming Attack

```
NAT SLIPSTREAMING:
  Malicious website can trick browser into sending specially crafted HTTP
  request that causes NAT to open ports on behalf of the attacker.
  
  Affected protocols: FTP (ALG), SIP (ALG)
  
  Mitigation:
    # Disable ALG (Application Layer Gateway) helpers
    sysctl -w net.netfilter.nf_conntrack_helper=0
    
    # Or selectively disable specific helpers
    modprobe -r nf_conntrack_ftp
    modprobe -r nf_conntrack_sip
```

## 33.4 Proper Defense with NAT + Firewall

```bash
# Complete secure NAT + firewall setup

# 1. Enable NAT
iptables -t nat -A POSTROUTING -o eth0 -s 192.168.1.0/24 -j MASQUERADE

# 2. Set restrictive default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 3. Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 4. Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# 5. Allow LAN → WAN (outbound from private network)
iptables -A FORWARD -i eth1 -o eth0 -m conntrack --ctstate NEW -j ACCEPT

# 6. Block invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
iptables -A FORWARD -m conntrack --ctstate INVALID -j DROP

# 7. Rate limit new connections (anti-DoS)
iptables -A FORWARD -p tcp --syn -m limit --limit 1000/s --limit-burst 2000 -j ACCEPT
iptables -A FORWARD -p tcp --syn -j DROP

# 8. Block RFC1918 from WAN (anti-spoofing)
iptables -A INPUT -i eth0 -s 192.168.0.0/16 -j DROP
iptables -A INPUT -i eth0 -s 172.16.0.0/12  -j DROP
iptables -A INPUT -i eth0 -s 10.0.0.0/8     -j DROP

# 9. Log and drop everything else
iptables -A INPUT   -j LOG --log-prefix "[BLOCKED-IN] "
iptables -A FORWARD -j LOG --log-prefix "[BLOCKED-FWD] "
```

---

# 34. Real-World Architectures

## 34.1 Home Router (NAT + DHCP + DNS)

```
                        ISP
                         │
                    eth0 (WAN)
                  203.0.113.1/30
                  ┌────────────┐
                  │   Linux    │
                  │   Router   │ ← MASQUERADE, DHCP server, DNS resolver
                  └────────────┘
                  192.168.1.1/24
                    eth1 (LAN)
                         │
          ┌──────────────┼──────────────┐
          │              │              │
      PC (.10)    Phone (.20)    TV (.30)
      
Rules:
  MASQUERADE: eth1 → eth0
  DHCP: dnsmasq serving 192.168.1.10-100
  DNS: unbound/dnsmasq on 192.168.1.1:53
  Port forward: :80 → 192.168.1.10:8080 (home server)
```

## 34.2 Enterprise DMZ Architecture

```
                    Internet
                        │
              ┌─────────────────────┐
              │   Edge Firewall/NAT  │
              │   203.0.113.0/30    │
              └───┬─────────────────┘
                  │
         ┌────────┴──────────────┐
         │                       │
    ┌────▼─────┐          ┌──────▼──────┐
    │    DMZ   │          │  Internal   │
    │ 10.0.1.0 │          │ 172.16.0.0  │
    └──────────┘          └─────────────┘
    Web servers           Internal servers
    Mail servers          Databases
    DNS servers           File servers
    
NAT Rules:
  DMZ → Internet: SNAT to 203.0.113.10
  Internal → Internet: SNAT to 203.0.113.20
  Internet → DMZ: DNAT (web/mail/dns)
  Internal → DMZ: Direct routing (no NAT needed)
  DMZ → Internal: BLOCKED (DMZ is untrusted)
```

## 34.3 Cloud Load Balancer (DNAT)

```
                    Internet Client
                         │
                   Load Balancer VIP
                   203.0.113.100:80
                         │
            ┌────────────┼────────────┐
            │ DNAT                    │
            │ (round-robin)           │
            ▼            ▼            ▼
       Web Server 1  Web Server 2  Web Server 3
       10.0.0.10:80  10.0.0.11:80  10.0.0.12:80

iptables implementation:
  iptables -t nat -A PREROUTING -d 203.0.113.100 -p tcp --dport 80 \
    -m statistic --mode nth --every 3 --packet 0 \
    -j DNAT --to-destination 10.0.0.10:80
  iptables -t nat -A PREROUTING -d 203.0.113.100 -p tcp --dport 80 \
    -m statistic --mode nth --every 2 --packet 0 \
    -j DNAT --to-destination 10.0.0.11:80
  iptables -t nat -A PREROUTING -d 203.0.113.100 -p tcp --dport 80 \
    -j DNAT --to-destination 10.0.0.12:80

Better with IPVS:
  ipvsadm -A -t 203.0.113.100:80 -s rr
  ipvsadm -a -t 203.0.113.100:80 -r 10.0.0.10:80 -m
  ipvsadm -a -t 203.0.113.100:80 -r 10.0.0.11:80 -m
  ipvsadm -a -t 203.0.113.100:80 -r 10.0.0.12:80 -m
```