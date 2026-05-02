# NAT, SNAT, DNAT, and PAT — Complete In-Depth Guide

> **Mental Model Philosophy:** Networking is about *transforming* and *routing* identity across boundaries.  
> NAT is fundamentally the science of **identity translation** — changing who a packet claims to be, or who it is addressed to, as it crosses a network boundary.

---

## Table of Contents

1. [The Problem NAT Solves — IPv4 Exhaustion](#1-the-problem-nat-solves)
2. [Foundational Vocabulary — Every Term Explained](#2-foundational-vocabulary)
3. [How IP Packets Work (The Physics of the Problem)](#3-how-ip-packets-work)
4. [What is NAT? The Core Mental Model](#4-what-is-nat)
5. [NAT Translation Table — The Heart of NAT](#5-nat-translation-table)
6. [SNAT — Source Network Address Translation](#6-snat)
7. [DNAT — Destination Network Address Translation](#7-dnat)
8. [PAT — Port Address Translation (NAT Overload)](#8-pat)
9. [NAT State Machine — Lifecycle of a Connection](#9-nat-state-machine)
10. [NAT Traversal — The Hard Problem](#10-nat-traversal)
11. [NAT in Real Protocols — TCP, UDP, ICMP](#11-nat-in-real-protocols)
12. [Linux Netfilter / iptables — NAT Under the Hood](#12-linux-netfilter-iptables)
13. [NAT vs Proxy vs Firewall — Precise Distinctions](#13-nat-vs-proxy-vs-firewall)
14. [Common NAT Topologies (Enterprise, Home, Cloud)](#14-common-nat-topologies)
15. [NAT Problems and Failure Modes](#15-nat-problems-and-failure-modes)
16. [Full Protocol Walkthrough — Packet by Packet](#16-full-protocol-walkthrough)
17. [Mental Models and Summary Cheatsheet](#17-mental-models-and-summary)

---

## 1. The Problem NAT Solves

### IPv4 Address Space — A Finite Resource

IPv4 uses **32-bit addresses**. That means the total possible addresses are:

```
2^32 = 4,294,967,296  (~4.3 billion unique addresses)
```

In 1981, this seemed infinite. By the late 1990s, the internet was growing exponentially and it became clear we would run out.

**The IANA (Internet Assigned Numbers Authority)** officially exhausted the IPv4 free pool on **February 3, 2011**.

### Why We Did Not Switch to IPv6 Immediately

IPv6 (128-bit addresses = 340 undecillion addresses) was standardized in 1998. But:

- Billions of devices already existed using IPv4.
- Infrastructure upgrades cost enormous time and money.
- The internet needed a **bridge** — a solution that could stretch IPv4 further while IPv6 adoption grew.

**NAT was that bridge.**

### RFC 1918 — Private Address Space

The IETF (Internet Engineering Task Force) defined **RFC 1918** (published 1996) which reserved three blocks of IP addresses for *private use* — these addresses are **not routable on the public internet**:

```
+-------------------------+-------------------+------------------+
| Range                   | CIDR Notation     | Total Addresses  |
+-------------------------+-------------------+------------------+
| 10.0.0.0 - 10.255.255.255   | 10.0.0.0/8    | 16,777,216       |
| 172.16.0.0 - 172.31.255.255 | 172.16.0.0/12 | 1,048,576        |
| 192.168.0.0 - 192.168.255.255| 192.168.0.0/16| 65,536           |
+-------------------------+-------------------+------------------+
```

**Key Insight:** Millions of home networks can all use `192.168.1.x` simultaneously, because those addresses never appear on the public internet. NAT is the mechanism that translates between this private world and the public one.

---

## 2. Foundational Vocabulary

Before we proceed, every term that will be used throughout this guide is defined precisely here. Read this section carefully — understanding these terms is the foundation.

### Network Addresses and Ports

| Term | Precise Definition |
|------|-------------------|
| **IP Address** | A 32-bit (IPv4) or 128-bit (IPv6) number that uniquely identifies a network interface. Written as dotted-decimal: `192.168.1.5` |
| **Port Number** | A 16-bit number (0–65535) used by transport protocols (TCP/UDP) to identify a specific application/service on a host |
| **Socket** | The combination of an IP address + port + protocol. E.g., `192.168.1.5:8080/TCP`. Uniquely identifies an endpoint of communication |
| **5-tuple** | The complete identifier for a network flow: `{src_ip, src_port, dst_ip, dst_port, protocol}` |
| **Public IP** | An IP address routable on the global internet. Assigned by ISPs. Example: `203.0.113.45` |
| **Private IP** | An RFC 1918 address. Not routable on the public internet. Example: `192.168.1.100` |
| **Loopback** | `127.0.0.1` — a special address that routes back to the same machine |

### NAT-Specific Terms

| Term | Precise Definition |
|------|-------------------|
| **NAT** | Network Address Translation — modifying IP address information in packet headers as they traverse a router |
| **SNAT** | Source NAT — rewriting the *source* IP (and optionally port) of a packet |
| **DNAT** | Destination NAT — rewriting the *destination* IP (and optionally port) of a packet |
| **PAT** | Port Address Translation — a form of SNAT that also translates ports, allowing many private IPs to share one public IP |
| **Masquerade** | A special case of SNAT where the public IP is dynamically learned (used when the WAN interface has a dynamic IP from DHCP) |
| **NAT Gateway** | The router/device that performs NAT translation |
| **Translation Table** | A stateful database maintained by the NAT gateway mapping internal sockets to external sockets |
| **Hairpin NAT** | When an internal host tries to reach an internal server using the server's *public* IP. Also called NAT Loopback |
| **WAN** | Wide Area Network — the "outside" / public internet side |
| **LAN** | Local Area Network — the "inside" / private network side |

### Protocol Layers (Crucial for Understanding NAT)

```
+------------------+
|  Application     |  HTTP, DNS, FTP, SSH — actual user data
+------------------+
|  Transport       |  TCP, UDP — manages src/dst PORTS
+------------------+
|  Network (IP)    |  IPv4, IPv6 — manages src/dst IP ADDRESSES  <-- NAT operates here
+------------------+
|  Data Link       |  Ethernet, Wi-Fi — MAC addresses
+------------------+
|  Physical        |  Cables, radio waves
+------------------+
```

**NAT operates primarily at Layer 3 (Network), but PAT also touches Layer 4 (Transport) because it modifies port numbers.**

### Packet Anatomy

```
+-----------------------------------------------------------+
|   Ethernet Header   |  IP Header   |  TCP Header  | Data  |
+-----------------------------------------------------------+
                             ^               ^
                             |               |
                       NAT modifies    PAT modifies
                       src/dst IP      src/dst port
```

---

## 3. How IP Packets Work

### The IP Header — Fields That Matter for NAT

Every IPv4 packet has a header. The fields NAT cares about:

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
|                       Source Address          <-- NAT MODIFIES |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address        <-- NAT MODIFIES |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

After the IP header comes the TCP header (or UDP):

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     ^-- PAT MODIFIES                  ^-- PAT MODIFIES
```

### The Checksum Problem

**Critical Detail:** When NAT modifies an IP address or port, it **must recalculate checksums**. Both the IP header checksum and the TCP/UDP checksum cover the addresses and ports. If NAT changes these values without updating checksums, the receiving host will detect corruption and drop the packet.

Modern NAT hardware does this automatically and in hardware (nanosecond speed). But this is why NAT is not "free" — every packet requires computation.

### How Routing Works Without NAT

```
Host A (192.168.1.10)  wants to talk to  Server (203.0.113.100)

Host A sends:
  src_ip  = 192.168.1.10   (private — NOT routable on internet)
  dst_ip  = 203.0.113.100
  src_port= 54321
  dst_port= 80

Internet routers receive this packet.
They look at src_ip = 192.168.1.10
They have no route for 192.168.1.10 (it's private).
PACKET DROPPED. Communication fails.
```

This is exactly the problem NAT solves.

---

## 4. What is NAT?

### The Core Mental Model

Think of NAT as a **post office** at the border between a private community (LAN) and the public world (WAN).

- Every house inside the community has an **internal address** (private IP).
- The post office has one or more **public addresses** (public IPs) known to the outside world.
- When a letter (packet) leaves the community, the post office **stamps its own return address** over the sender's internal address.
- When a reply comes back to the post office, it **looks up who the letter was really for** and delivers it to the correct house.

The post office maintains a **logbook** (translation table) of every ongoing correspondence.

### NAT is NOT a Security Feature (Common Misconception)

Many people believe NAT provides security because external hosts cannot directly address internal hosts. This is a **side effect**, not the purpose. NAT was designed to **conserve IP addresses**. The "security" it provides is called **security through obscurity** — a weak and unreliable model. Real security comes from firewalls, which operate on explicit rules.

### The Three Types of NAT

```
+------------------------------------------------------+
|                   NAT TYPES                          |
+------------------------------------------------------+
|                                                      |
|  SNAT:  Modifies SOURCE IP       (outbound traffic)  |
|  DNAT:  Modifies DESTINATION IP  (inbound traffic)   |
|  PAT:   Modifies SOURCE IP+PORT  (many-to-one)       |
|                                                      |
+------------------------------------------------------+
```

---

## 5. NAT Translation Table

### What is a Translation Table?

The **NAT translation table** (also called NAT table, connection table, or state table) is the **most critical component** of any NAT system. It is an in-memory database that maps:

```
INTERNAL socket  <-->  EXTERNAL socket  <-->  REMOTE socket
```

Without this table, NAT cannot function. When a reply packet arrives from the internet, the NAT device uses this table to figure out which internal host to forward it to.

### Table Schema — What Each Entry Contains

```
+----------+----------+----------+----------+----------+----------+----------+
| Protocol | Int. IP  | Int.Port | Ext. IP  | Ext.Port | Rem. IP  | Rem.Port |
+----------+----------+----------+----------+----------+----------+----------+
| TCP      |192.168.1.10| 54321  |203.0.113.45| 54321  |8.8.8.8   |  80      |
| TCP      |192.168.1.11| 44123  |203.0.113.45| 44123  |1.1.1.1   |  443     |
| UDP      |192.168.1.10| 5353   |203.0.113.45| 5353   |8.8.4.4   |  53      |
+----------+----------+----------+----------+----------+----------+----------+

  ^Internal side^                ^External side^          ^Remote (server)^
```

- **Int. IP / Int. Port** — the real private IP and port of the internal host
- **Ext. IP / Ext. Port** — the public IP and (possibly remapped) port as seen from the internet
- **Rem. IP / Rem. Port** — the destination server on the internet

### Entry Lifecycle — Timeouts

NAT entries cannot live forever or the table would fill up:

| Protocol | Default Timeout | Reason |
|----------|----------------|--------|
| TCP established | 86400s (24h) | Long-lived connections |
| TCP TIME_WAIT | 120s | TCP closing handshake |
| TCP SYN_SENT | 120s | Incomplete connection |
| UDP | 30–300s | UDP is stateless, shorter timeout |
| ICMP | 60s | Short-lived pings |

### Port Collision and Remapping

**What happens if two internal hosts use the same source port?**

```
Host A: 192.168.1.10:54321  --> Server:80
Host B: 192.168.1.11:54321  --> Server:80
```

Both packets, after SNAT, would have:

```
PublicIP:54321 --> Server:80   (Host A)
PublicIP:54321 --> Server:80   (Host B)  COLLISION!
```

The NAT device resolves this by **remapping the port** for one of them:

```
PublicIP:54321 --> Server:80   (Host A, unchanged)
PublicIP:54322 --> Server:80   (Host B, port remapped)
```

The table records the mapping so replies can be correctly routed back.

---

## 6. SNAT — Source Network Address Translation

### Definition

**SNAT rewrites the source IP address** (and optionally source port) of packets leaving the internal network toward the internet. It is used for **outbound traffic** — when internal hosts initiate connections to external servers.

### The SNAT Process — Step by Step

```
BEFORE SNAT (Inside NAT Device, entering from LAN):

  [Internal Host: 192.168.1.10]
        |
        | Packet:
        |   src_ip   = 192.168.1.10   (private)
        |   src_port = 54321
        |   dst_ip   = 8.8.8.8
        |   dst_port = 53
        v
  [NAT DEVICE — applies SNAT rule]
        |
        | Translation Table Entry Created:
        |   TCP | 192.168.1.10:54321 <-> PublicIP:54321 | 8.8.8.8:53
        |
        | Packet (AFTER SNAT):
        |   src_ip   = 203.0.113.45   (PUBLIC IP -- replaced!)
        |   src_port = 54321          (may be remapped if collision)
        |   dst_ip   = 8.8.8.8        (unchanged)
        |   dst_port = 53             (unchanged)
        v
  [Internet]
        |
        | Reply from DNS Server:
        |   src_ip   = 8.8.8.8
        |   src_port = 53
        |   dst_ip   = 203.0.113.45   (goes to NAT device)
        |   dst_port = 54321
        v
  [NAT DEVICE — looks up translation table]
        |
        | Finds entry: PublicIP:54321 from 8.8.8.8:53
        |              => maps to 192.168.1.10:54321
        |
        | Packet (AFTER REVERSE SNAT):
        |   src_ip   = 8.8.8.8
        |   src_port = 53
        |   dst_ip   = 192.168.1.10   (restored to private IP)
        |   dst_port = 54321
        v
  [Internal Host: 192.168.1.10]
```

### SNAT Architecture Diagram

```
                         INTERNET
                            |
                     +------+------+
                     |   Router    |
                     |  (NAT GW)   |
                     |             |
                     | Public IP:  |
                     |203.0.113.45 |
                     +------+------+
                            |
              +-------------+-------------+
              |                           |
     +--------+--------+        +--------+--------+
     | Host A           |        | Host B           |
     | 192.168.1.10     |        | 192.168.1.11     |
     | (Client)         |        | (Client)         |
     +------------------+        +------------------+

OUTBOUND FLOW (SNAT Applied):

Host A           NAT Gateway              Server (8.8.8.8)
  |                   |                        |
  |-- Packet -------->|                        |
  |  src:192.168.1.10 |                        |
  |  dst:8.8.8.8      |                        |
  |                   |--[SNAT]--> Packet ----->|
  |                   |  src:203.0.113.45       |
  |                   |  dst:8.8.8.8            |
  |                   |                        |
  |                   |<------- Reply ----------|
  |                   |  src:8.8.8.8            |
  |                   |  dst:203.0.113.45       |
  |                   |                        |
  |<-- [UNSNAT]-------|                        |
  |  src:8.8.8.8      |                        |
  |  dst:192.168.1.10 |                        |
```

### SNAT Rule Syntax (Linux iptables)

```bash
# Classic SNAT — use when public IP is static
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j SNAT \
    --to-source 203.0.113.45

# Masquerade — use when public IP is dynamic (DHCP from ISP)
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE
```

**Difference between SNAT and MASQUERADE:**
- `SNAT --to-source`: The public IP is hardcoded. Faster (IP looked up once at rule creation).
- `MASQUERADE`: The public IP is dynamically read from the interface at packet time. Slightly slower. Essential when ISP assigns IP via DHCP.

### SNAT with Port Range Control

```bash
# SNAT with specific port range for translated source ports
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -p tcp \
    -j SNAT \
    --to-source 203.0.113.45:1024-65535
```

---

## 7. DNAT — Destination Network Address Translation

### Definition

**DNAT rewrites the destination IP address** (and optionally destination port) of incoming packets. It is used for **inbound traffic** — directing external requests to specific internal servers.

### Why DNAT Exists

After SNAT/PAT, internal hosts cannot be directly addressed from the internet. If you run a web server at `192.168.1.50:80`, external users cannot connect because:

1. `192.168.1.50` is a private address — not routable on the internet.
2. Even if they try to connect to `192.168.1.50`, their packet would never arrive.

The solution: **Port Forwarding / DNAT**. External users connect to `PublicIP:80`, and DNAT rewrites the destination to `192.168.1.50:80`.

### The DNAT Process — Step by Step

```
BEFORE DNAT (Packet arriving from Internet):

  [External Client: 5.5.5.5]
        |
        | Packet:
        |   src_ip   = 5.5.5.5
        |   src_port = 43210
        |   dst_ip   = 203.0.113.45   (public IP of NAT gateway)
        |   dst_port = 80             (port-forward rule matches this)
        v
  [NAT DEVICE — applies DNAT rule]
        |
        | Rule: "Port 80 incoming => forward to 192.168.1.50:80"
        |
        | Packet (AFTER DNAT):
        |   src_ip   = 5.5.5.5        (unchanged)
        |   src_port = 43210          (unchanged)
        |   dst_ip   = 192.168.1.50   (REPLACED — now points to internal server)
        |   dst_port = 80             (unchanged, but can also be remapped)
        v
  [Internal Web Server: 192.168.1.50:80]
        |
        | Reply:
        |   src_ip   = 192.168.1.50   (needs to be un-DNATed)
        |   src_port = 80
        |   dst_ip   = 5.5.5.5
        |   dst_port = 43210
        v
  [NAT DEVICE — reverse DNAT / SNAT applied]
        |
        | Packet (outgoing reply):
        |   src_ip   = 203.0.113.45   (replaced back to public IP)
        |   src_port = 80
        |   dst_ip   = 5.5.5.5
        |   dst_port = 43210
        v
  [External Client: 5.5.5.5]
```

### DNAT Architecture Diagram

```
         INTERNET
            |
     +------+------+          +------------------+
     |   Router    |  DNAT    | Web Server        |
     |  (NAT GW)   |--------->| 192.168.1.50:80   |
     |             |          +------------------+
     | Public IP:  |
     |203.0.113.45 |          +------------------+
     |             |  DNAT    | SSH Server        |
     |             |--------->| 192.168.1.51:22   |
     +------+------+          +------------------+
            |
         Internet

INBOUND FLOW (DNAT Applied):

External Client (5.5.5.5)   NAT Gateway         Web Server (192.168.1.50)
        |                        |                        |
        |--- TCP SYN ----------->|                        |
        |   dst:203.0.113.45:80  |                        |
        |                        |--[DNAT]--------------->|
        |                        |   dst:192.168.1.50:80  |
        |                        |                        |
        |                        |<------- TCP SYN-ACK ---|
        |                        |   src:192.168.1.50:80  |
        |<-- TCP SYN-ACK --------|                        |
        |   src:203.0.113.45:80  |                        |
```

### DNAT Use Cases

| Use Case | DNAT Configuration |
|----------|-------------------|
| Public web server on LAN | Port 80 → 192.168.1.50:80 |
| Public HTTPS server | Port 443 → 192.168.1.50:443 |
| SSH access to internal host | Port 2222 → 192.168.1.51:22 |
| Gaming server | Port 27015 → 192.168.1.52:27015 |
| Port remapping | External port 8080 → Internal port 80 |

### DNAT Rule Syntax (Linux iptables)

```bash
# DNAT — forward external port 80 to internal web server
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -j DNAT \
    --to-destination 192.168.1.50:80

# DNAT with port remapping — external 2222 to internal 22
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 2222 \
    -j DNAT \
    --to-destination 192.168.1.51:22

# Allow the forwarded traffic through (required with DNAT)
iptables -A FORWARD \
    -p tcp \
    -d 192.168.1.50 \
    --dport 80 \
    -j ACCEPT
```

### DNAT and Hairpin NAT (NAT Loopback)

**Problem:** Internal host `192.168.1.100` wants to reach the web server `192.168.1.50:80` using the *public* address `203.0.113.45:80`.

```
Internal Client                NAT Gateway                 Internal Server
192.168.1.100                  203.0.113.45                192.168.1.50

  |-- dst:203.0.113.45:80 ---> |                               |
  |                             |--[DNAT]--> dst:192.168.1.50:80|
  |                             |                               |
  |                             | <------- reply ---------------| 
  |                             |   src:192.168.1.50            |
  |                             |                               |
  | Problem: reply src is       |                               |
  | 192.168.1.50, but client    |                               |
  | expected 203.0.113.45!      |                               |
```

**Solution — Hairpin NAT:** The gateway also applies SNAT to the internal client's IP when hairpin traffic is detected, so the reply appears to come from the public IP.

```bash
# Hairpin NAT rule
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 \
    -d 192.168.1.50 \
    -p tcp \
    --dport 80 \
    -j MASQUERADE
```

---

## 8. PAT — Port Address Translation

### Definition

**PAT (Port Address Translation)** — also called **NAT Overload** or **IP Masquerading** — is the mechanism that allows **many internal hosts to share a single public IP address simultaneously**.

PAT extends SNAT by also translating **port numbers**, using the port as an additional dimension to distinguish connections.

### The Mathematical Insight

Without PAT: 1 public IP = 1 internal host (pure SNAT mapping)

With PAT: 1 public IP = up to ~65,535 simultaneous connections from many internal hosts

```
Port range: 0–65535 = 65,536 possible ports
Reserved: 0–1023 (well-known ports, usually not used for PAT)
Available for PAT: 1024–65535 = 64,512 ports per public IP
```

This is why one home router can serve 50+ devices simultaneously.

### PAT Architecture — Many to One

```
INTERNAL NETWORK (192.168.1.0/24)       PUBLIC INTERNET

+------------------+
| Host A            |  192.168.1.10:54321 ──┐
+------------------+                        │
+------------------+                        │    PAT Device       Server
| Host B            |  192.168.1.11:44000 ──┤    203.0.113.45     8.8.8.8
+------------------+                        │
+------------------+                        ├──> :54321 ──────────> :80
| Host C            |  192.168.1.12:33100 ──┤──> :44000 ──────────> :443
+------------------+                        └──> :33100 ──────────> :53
+------------------+
| Host D            |  192.168.1.13:54321 ──┐
+------------------+                        │    PORT COLLISION!
                                            │    Both A and D use :54321
                                            │    PAT remaps D to :54322
                                            └──> :54322 ──────────> :80
```

### PAT Translation Table — Complete Example

```
+-----+----------------+-------+---------------+-------+----------+-------+
|Proto| Internal IP    | I.Port| External IP   | E.Port| Remote IP|R.Port |
+-----+----------------+-------+---------------+-------+----------+-------+
| TCP | 192.168.1.10   | 54321 | 203.0.113.45  | 54321 | 8.8.8.8  |  80   |
| TCP | 192.168.1.11   | 44000 | 203.0.113.45  | 44000 | 1.1.1.1  | 443   |
| TCP | 192.168.1.12   | 33100 | 203.0.113.45  | 33100 | 8.8.4.4  |  53   |
| TCP | 192.168.1.13   | 54321 | 203.0.113.45  | 54322 | 8.8.8.8  |  80   |
|     |                |       |               | ^^^^^                      |
|     |                |       |               | PORT REMAPPED (collision)  |
| UDP | 192.168.1.10   | 5353  | 203.0.113.45  |  5353 | 8.8.4.4  |  53   |
+-----+----------------+-------+---------------+-------+----------+-------+
```

### PAT Packet Transformation — Detailed

```
=== OUTBOUND (Host A → Google DNS) ===

Original packet from Host A (192.168.1.10):
+----------------------------------------------+
| IP Header                                    |
|   src_ip:  192.168.1.10   <-- PRIVATE        |
|   dst_ip:  8.8.8.8                           |
|   protocol: TCP                              |
+----------------------------------------------+
| TCP Header                                   |
|   src_port: 54321                            |
|   dst_port: 80                               |
+----------------------------------------------+
| Data: "GET / HTTP/1.1..."                    |
+----------------------------------------------+

After PAT (leaving NAT device toward internet):
+----------------------------------------------+
| IP Header                                    |
|   src_ip:  203.0.113.45  <-- PUBLIC (changed)|
|   dst_ip:  8.8.8.8                           |
|   protocol: TCP                              |
|   checksum: <recalculated>                   |
+----------------------------------------------+
| TCP Header                                   |
|   src_port: 54321        <-- (unchanged here)|
|   dst_port: 80                               |
|   checksum: <recalculated>                   |
+----------------------------------------------+
| Data: "GET / HTTP/1.1..."  (unchanged)       |
+----------------------------------------------+

=== INBOUND (Reply from Google DNS → Host A) ===

Reply arriving at NAT device:
+----------------------------------------------+
| IP Header                                    |
|   src_ip:  8.8.8.8                           |
|   dst_ip:  203.0.113.45  <-- NAT device's IP |
|   protocol: TCP                              |
+----------------------------------------------+
| TCP Header                                   |
|   src_port: 80                               |
|   dst_port: 54321        <-- lookup key      |
+----------------------------------------------+

NAT device lookup:
  dst_ip:203.0.113.45 + dst_port:54321 + src_ip:8.8.8.8 + protocol:TCP
  => maps to internal: 192.168.1.10:54321

After Un-PAT (forwarded to internal network):
+----------------------------------------------+
| IP Header                                    |
|   src_ip:  8.8.8.8                           |
|   dst_ip:  192.168.1.10  <-- RESTORED        |
|   protocol: TCP                              |
|   checksum: <recalculated>                   |
+----------------------------------------------+
| TCP Header                                   |
|   src_port: 80                               |
|   dst_port: 54321        <-- RESTORED        |
|   checksum: <recalculated>                   |
+----------------------------------------------+
```

### PAT Port Selection Algorithm

When a new outbound connection is created, PAT chooses the external port using this logic:

```
1. Try to preserve the original source port (if no collision exists)
2. If collision:
   a. For ports < 512:  search in range 1-511
   b. For ports < 1024: search in range 512-1023
   c. For ports >= 1024: search in range 1024-65535
3. If all ports in range are exhausted: DROP the connection
```

This is why under extreme load (e.g., a large office with one small public IP range), PAT can fail — the port space is exhausted.

---

## 9. NAT State Machine

### Connection States Tracked by NAT

NAT is **stateful** — it tracks the lifecycle of every connection. Understanding these states is critical for understanding why certain connections succeed or fail through NAT.

### TCP State Machine Through NAT

```
                         CONNECTION STATES

Client                  NAT Device                  Server
  |                         |                          |
  |--- SYN --------------->|                          |
  |                         | State: SYN_SENT          |
  |                         | (entry created, timeout ~120s)
  |                         |--- SYN ----------------->|
  |                         |                          |
  |                         |<-- SYN-ACK --------------|
  |                         | State: SYN_RECV          |
  |<-- SYN-ACK ------------|                          |
  |                         |                          |
  |--- ACK --------------->|                          |
  |                         |--- ACK ----------------->|
  |                         | State: ESTABLISHED       |
  |                         | (timeout ~86400s)        |
  |                        ...                        ...
  |--- FIN --------------->|                          |
  |                         |--- FIN ----------------->|
  |                         | State: FIN_WAIT          |
  |                         |<-- FIN-ACK --------------|
  |<-- FIN-ACK ------------|                          |
  |                         | State: TIME_WAIT         |
  |                         | (timeout ~120s)          |
  |                         | Entry DELETED after timeout
```

### UDP — Pseudo-State Tracking

UDP is connectionless — there is no handshake. NAT creates a "pseudo-connection" entry on the first outbound UDP packet and keeps it alive for a short time (30–300 seconds).

```
Client                  NAT Device                  Server
  |                         |                          |
  |--- UDP packet -------->|                          |
  |                         | Entry Created            |
  |                         | Timeout timer starts     |
  |                         |--- UDP packet ---------->|
  |                         |                          |
  |                         |<-- UDP reply ------------|
  |                         | Timeout timer RESET      |
  |<-- UDP reply -----------|                          |
  |                         |                          |
  |  (no more packets)      |                          |
  |                         | Timeout expires          |
  |                         | Entry DELETED            |
```

**Critical Insight:** If the UDP timeout expires and you send another packet, NAT creates a **new** entry. This is why UDP-based protocols like VoIP can have issues through NAT — the entry may expire between call setup and call media.

### ICMP — Type/Code Based Tracking

ICMP has no ports. NAT uses the **ICMP identifier** field (present in Echo Request/Reply) to track state.

```
Echo Request (ping):
  ICMP Type: 8 (Echo Request)
  ICMP Identifier: 1234        <-- NAT uses this like a "port"
  ICMP Sequence: 1

Echo Reply:
  ICMP Type: 0 (Echo Reply)
  ICMP Identifier: 1234        <-- matched back to same entry
```

---

## 10. NAT Traversal

### The Problem — Why P2P Through NAT is Hard

When two hosts behind separate NAT devices want to communicate **directly** (peer-to-peer), neither can initiate the connection to the other because:

- Neither's private IP is reachable from the outside.
- The NAT device only creates entries for **outbound** connections.
- An inbound packet with no matching NAT entry is **dropped**.

```
Host A (192.168.1.10)              Host B (192.168.2.10)
Behind NAT-A (pub: 1.1.1.1)        Behind NAT-B (pub: 2.2.2.2)

Host A tries: connect to 2.2.2.2 (NAT-B's public IP)
NAT-B receives: "who is this? no entry for A" => DROP

Host B tries: connect to 1.1.1.1 (NAT-A's public IP)
NAT-A receives: "who is this? no entry for B" => DROP

DEADLOCK — neither can reach the other!
```

### NAT Traversal Techniques

#### Technique 1: STUN (Session Traversal Utilities for NAT)

**RFC 5389.** A client contacts a **STUN server** on the public internet to discover its own public IP and port as seen from outside its NAT.

```
Host A (192.168.1.10)            STUN Server (5.5.5.5:3478)
  |                                     |
  |--- UDP request ------------------>  |
  | src: 192.168.1.10:54321            |
  | (NAT translates to 1.1.1.1:54321) |
  |                                     |
  |<-- Response -----------------------|
  | "Your public IP:port = 1.1.1.1:54321"
  |
  Now Host A knows its public address.
  It can share this with Host B via a signaling server.
  Host B connects to 1.1.1.1:54321
  NAT-A recognizes it as reply traffic for the connection
  => SUCCESS (if NAT-A is a "Full Cone" or "Address Restricted" type)
```

#### Technique 2: TURN (Traversal Using Relays around NAT)

**RFC 5766.** When direct P2P fails (strict NAT), use a **relay server** that both peers can connect to.

```
Host A <---> TURN Server (public) <---> Host B
              (relay all traffic)
```

This always works but adds latency and relay server cost.

#### Technique 3: ICE (Interactive Connectivity Establishment)

**RFC 8445.** Used by WebRTC. ICE combines STUN and TURN:

1. Gather all possible "candidates" (direct IP, STUN-discovered public IP, TURN relay)
2. Try all pairs between the two peers
3. Use the best one that works

#### Technique 4: UDP Hole Punching

Both NAT devices have symmetric or predictable port allocation. Both clients send UDP packets to each other simultaneously. The outbound packet "punches a hole" in the NAT table. The other side's packet arrives just as the hole is open.

```
Host A                 NAT-A              NAT-B              Host B
  |                     |                  |                    |
  |--- UDP to B's ------>|                 |                    |
  |    public addr       |                 |                    |
  |    (opens hole)      |--- UDP -------->|                    |
  |                      |                 |--- (hole punch) -->|
  |                      |                 |                    |
  |                      |                 |<-- UDP ------------|
  |                      |<-- UDP ---------|                    |
  |<-- UDP --------------|                 |                    |
  |   (succeeds! entry   |                 |                    |
  |    exists from A's   |                 |                    |
  |    first packet)     |                 |                    |
```

### Types of NAT — Affects Traversal Difficulty

NAT implementations differ in how strictly they filter inbound packets. This is classified by the "cone" model (RFC 3489, now superseded but the terminology persists):

| NAT Type | Inbound Rule | Traversal Difficulty |
|----------|-------------|---------------------|
| **Full Cone** | Any external host can send to the mapped port | Easiest |
| **Address Restricted Cone** | Only the specific IP the client talked to | Moderate |
| **Port Restricted Cone** | Only the specific IP:Port the client talked to | Harder |
| **Symmetric** | Different external port for each remote endpoint; inbound only from same | Hardest |

```
FULL CONE:
  Client at NAT:1.1.1.1:5000
  ANY external host can send to 1.1.1.1:5000
  => Mapped port is truly "open"

SYMMETRIC:
  Client → Server-A:  NAT uses 1.1.1.1:5000
  Client → Server-B:  NAT uses 1.1.1.1:5001  (different port!)
  Only Server-A can reach 1.1.1.1:5000
  Only Server-B can reach 1.1.1.1:5001
  => Hole punching fails. Must use TURN relay.
```

---

## 11. NAT in Real Protocols

### TCP — Most Well-Behaved with NAT

TCP's 3-way handshake and explicit connection states make NAT tracking straightforward:

```
SYN     → NAT creates entry (state: SYN_SENT)
SYN-ACK → NAT confirms entry (state: ESTABLISHED)
FIN     → NAT begins cleanup (state: FIN_WAIT)
RST     → NAT immediately deletes entry
```

**Special Case: FTP (Active Mode)**

FTP uses two TCP connections:
- **Control connection**: Client → Server:21 (standard, NAT handles fine)
- **Data connection**: Server initiates back to Client (PROBLEM — NAT blocks it)

```
Control: Client:54321 --> Server:21     (client initiates, SNAT works)
Data:    Server:20 --> Client:PUBLIC_IP:SOME_PORT
         (server tries to connect back — NAT blocks this!)
```

**Solution:** FTP passive mode (PASV), or Application Layer Gateway (ALG) for FTP. An ALG inspects the FTP control channel, reads the PORT command, and creates a NAT pre-entry for the incoming data connection.

### UDP — Requires Keep-Alive

UDP has no connection concept. For long-lived UDP sessions (VoIP, game UDP), keep-alive packets must be sent frequently to prevent NAT entry expiration.

```
VoIP Call (SIP/RTP):
  SIP Signaling: UDP 5060    (setup call)
  RTP Media:     UDP 5004+   (audio/video stream)

Problem: If call goes silent (e.g., hold), no RTP packets.
         NAT entry expires (30s default).
         When call resumes, NAT drops RTP packets.

Solution: RTCP keep-alive every 15-20s, or NAT keep-alive in SIP stack.
```

### ICMP — Limited but Supported

ICMP types supported by NAT:

```
Type 0: Echo Reply      ← response to Type 8, tracked by ICMP ID
Type 8: Echo Request    ← ping, NAT translates and tracks
Type 3: Dest. Unreachable ← NAT passes through (informational)
Type 11: Time Exceeded  ← TTL expired (traceroute), passed through

Traceroute through NAT:
  Traceroute sends UDP packets with incrementing TTL.
  Routers return ICMP Type 11 when TTL hits 0.
  NAT must pass these ICMP responses through to the correct internal host.
  NAT matches the embedded original IP header inside the ICMP error.
```

### DNS — Special Considerations

DNS uses UDP port 53 (and TCP for large responses). NAT handles DNS well, but two issues arise:

1. **DNS64**: In IPv6-only networks behind NAT64, DNS64 synthesizes AAAA records from A records.
2. **DNSSEC**: DNSSEC signatures bind to the source IP. If SNAT changes the IP, DNSSEC validation at recursive resolvers may fail (mostly non-issue at client side).

### SIP (VoIP) — Most Problematic Protocol with NAT

SIP (Session Initiation Protocol) embeds IP addresses in the application payload:

```
INVITE sip:bob@biloxi.com SIP/2.0
Via: SIP/2.0/UDP 192.168.1.10:5060   <-- PRIVATE IP EMBEDDED IN PAYLOAD
Contact: <sip:alice@192.168.1.10>     <-- PRIVATE IP EMBEDDED IN PAYLOAD
Content-Type: application/sdp
...
o=alice 2890844526 2890844526 IN IP4 192.168.1.10  <-- IN SDP BODY
c=IN IP4 192.168.1.10
```

NAT translates the IP header, but **the private IPs inside the payload remain unchanged**. The remote SIP server sees `192.168.1.10` in the SIP headers and tries to send replies to that — which fails because it's a private address.

**Solutions:**
- **STUN/ICE** in the SIP client: client discovers its public IP and puts that in SIP headers.
- **SIP ALG (Application Layer Gateway)**: NAT device performs deep packet inspection and rewrites the SIP headers. (Often buggy — recommended to disable and use STUN instead.)
- **SIP proxy on public internet**: All SIP goes through a public proxy that handles the addressing.

---

## 12. Linux Netfilter / iptables

### Netfilter — The Kernel Framework

Linux's NAT is implemented by the **Netfilter** framework in the kernel. `iptables` is the userspace tool to configure it.

### The Five Hooks (Chains)

Netfilter intercepts packets at five points in the kernel's network stack:

```
Incoming Packet
      |
      v
  PREROUTING  <-- Hook 1: Before routing decision (DNAT happens here)
      |
      +---> Is it for this machine?
      |          |                |
      |         YES               NO
      |          |                |
      |          v                v
      |       INPUT            FORWARD  <-- Hook 3: For forwarded packets
      |    <-- Hook 2          Hook 4 -->
      |     (local apps)       (routing)
      |                            |
      |                            v
      +----------------------> POSTROUTING  <-- Hook 5: After routing (SNAT here)
                                    |
                              Outgoing Packet
```

### The nat Table

Within Netfilter, the `nat` table handles NAT rules:

```
Table: nat
  Chains:
    PREROUTING   — for DNAT (inbound packets, before routing)
    POSTROUTING  — for SNAT/Masquerade (outbound packets, after routing)
    OUTPUT       — for DNAT on locally-generated packets
```

### Complete NAT Setup (Home Router Example)

```bash
#!/bin/bash
# Complete NAT setup for a Linux router
# LAN interface: eth1 (192.168.1.0/24)
# WAN interface: eth0 (gets public IP from ISP)

# 1. Enable IP forwarding (kernel must forward packets between interfaces)
echo 1 > /proc/sys/net/ipv4/ip_forward
# Persist across reboots:
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf

# 2. Flush existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F

# 3. SNAT/Masquerade — all LAN traffic going out WAN gets NATted
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE

# 4. Allow established/related connections back in (stateful firewall)
iptables -A FORWARD \
    -m state \
    --state ESTABLISHED,RELATED \
    -j ACCEPT

# 5. Allow new connections from LAN to WAN
iptables -A FORWARD \
    -i eth1 \
    -o eth0 \
    -j ACCEPT

# 6. DNAT — port forward HTTP to internal web server
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 80 \
    -j DNAT \
    --to-destination 192.168.1.50:80

# Allow the forwarded HTTP traffic
iptables -A FORWARD \
    -p tcp \
    -d 192.168.1.50 \
    --dport 80 \
    -m state \
    --state NEW,ESTABLISHED,RELATED \
    -j ACCEPT

# 7. DNAT — SSH on port 2222 to internal host port 22
iptables -t nat -A PREROUTING \
    -i eth0 \
    -p tcp \
    --dport 2222 \
    -j DNAT \
    --to-destination 192.168.1.51:22

# 8. Hairpin NAT — allow internal hosts to reach internal servers via public IP
iptables -t nat -A POSTROUTING \
    -s 192.168.1.0/24 \
    -d 192.168.1.50 \
    -p tcp \
    --dport 80 \
    -j MASQUERADE
```

### nftables (Modern Replacement for iptables)

`nftables` is the modern Linux NAT framework. `iptables` is legacy but still widely used.

```
#!/usr/sbin/nft -f

# nftables equivalent of the above iptables setup

table ip nat {

    chain PREROUTING {
        type nat hook prerouting priority dstnat;

        # DNAT: forward HTTP to internal web server
        iif "eth0" tcp dport 80 \
            dnat to 192.168.1.50:80

        # DNAT: SSH port forward
        iif "eth0" tcp dport 2222 \
            dnat to 192.168.1.51:22
    }

    chain POSTROUTING {
        type nat hook postrouting priority srcnat;

        # Masquerade: all LAN traffic going out WAN
        oif "eth0" masquerade
    }
}

table ip filter {
    chain FORWARD {
        type filter hook forward priority filter;

        # Allow established/related
        ct state established,related accept

        # Allow LAN to WAN
        iif "eth1" oif "eth0" accept
    }
}
```

### Connection Tracking (conntrack)

Linux's connection tracking module (`nf_conntrack`) is the subsystem that maintains the NAT state table. You can inspect it:

```bash
# View all current NAT/conntrack entries
cat /proc/net/nf_conntrack
# Or:
conntrack -L

# Example output:
# ipv4     2 tcp      6 86395 ESTABLISHED
#   src=192.168.1.10 dst=8.8.8.8 sport=54321 dport=80
#   src=8.8.8.8 dst=203.0.113.45 sport=80 dport=54321
#   [ASSURED] mark=0 use=1

# Show statistics
conntrack -S

# Delete a specific entry (force reconnect)
conntrack -D -s 192.168.1.10 -d 8.8.8.8

# Monitor new connections in real time
conntrack -E
```

---

## 13. NAT vs Proxy vs Firewall

These three concepts are often confused. Precise distinctions:

### Comparison Table

| Feature | NAT | Proxy | Firewall |
|---------|-----|-------|----------|
| **Layer** | Layer 3/4 (IP + Port) | Layer 7 (Application) | Layer 3/4 (or L7 for NGFW) |
| **Transparency** | Transparent to apps | Apps must use it | Transparent |
| **Modifies packets** | IP header, port | Entire new connection | Drops/allows only |
| **State kept** | Connection 5-tuple | Full HTTP/etc session | Connection state |
| **Purpose** | Address translation | Caching, content filter, anonymity | Access control |
| **Client awareness** | No | Yes (or transparent proxy) | No |

### NAT vs Proxy — The Critical Difference

```
NAT:
  Client <-> [NAT rewrites headers] <-> Server
  The SERVER sees a connection from the NAT's public IP.
  But it is the same TCP connection end-to-end.
  NAT only modifies the IP/port fields.

Proxy:
  Client <-> [Proxy terminates connection] <-> [Proxy opens new connection] <-> Server
  There are TWO separate TCP connections.
  The proxy fully handles the application protocol (HTTP, etc.).
  Client and server do not have a direct connection.
```

---

## 14. Common NAT Topologies

### Topology 1 — Home Network (Single Public IP)

```
                    ISP
                     |
              [DSL/Cable Modem]
                     |
          [Home Router / NAT Gateway]
          Public IP: 203.0.113.45 (dynamic, from ISP DHCP)
          LAN: 192.168.1.0/24
                     |
         +-----------+-----------+
         |           |           |
    [Laptop]     [Phone]     [Smart TV]
    .1.100       .1.101       .1.102
```

- **NAT Type:** PAT / Masquerade (many internal hosts, one dynamic public IP)
- **SNAT:** Masquerade (dynamic public IP)
- **DNAT:** Manual port forwarding for any self-hosted services
- **Port range for PAT:** 1024–65535

### Topology 2 — Enterprise Network (Multiple Public IPs)

```
                    ISP
                     |
              [Border Router]
              Public IPs: 203.0.113.0/29 (8 usable IPs)
                     |
              [Firewall / NAT]
                     |
         +-----------+-----------+
         |           |           |
    [Office LAN]  [DMZ]      [Servers]
    10.0.0.0/16   172.16.1.0/24  172.16.2.0/24
```

- **LAN clients:** SNAT to 203.0.113.1 (one IP for all outbound)
- **DMZ web server:** DNAT from 203.0.113.2:80 → 172.16.1.10:80
- **DMZ mail server:** DNAT from 203.0.113.3:25 → 172.16.1.20:25
- **One IP per public service** (no port sharing on inbound)

### Topology 3 — Cloud / AWS VPC NAT Gateway

```
+----------------------------------------------------------+
|  AWS VPC (10.0.0.0/16)                                   |
|                                                          |
|  +---------------------+    +------------------------+  |
|  | Public Subnet        |    | Private Subnet          |  |
|  | 10.0.1.0/24          |    | 10.0.2.0/24             |  |
|  |                      |    |                        |  |
|  | [NAT Gateway]        |    | [App Servers]          |  |
|  | Elastic IP: X.X.X.X  |    | 10.0.2.10-50           |  |
|  |                      |    |     |                  |  |
|  +----------+-----------+    +-----|------------------+  |
|             |                      |                     |
|             +<----- SNAT ----------+                     |
|             |                                            |
+-------------|--------------------------------------------+
              |
          [Internet Gateway]
              |
         [Internet]
```

AWS NAT Gateway:
- Managed SNAT service for private subnet instances to reach internet.
- Highly available, scales automatically.
- Does **not** support DNAT — for inbound, use ALB/ELB or Elastic IPs.

### Topology 4 — Carrier-Grade NAT (CGNAT)

CGNAT (RFC 6598) is NAT performed by the ISP itself. Your home router's "public" IP is actually also private (in the `100.64.0.0/10` range).

```
Your Device          Home Router          ISP CGNAT            Internet
192.168.1.5  ------> 192.168.1.1  ------> 100.64.x.x  ------> 203.x.x.x
              SNAT1 (your router)   SNAT2 (ISP NAT)
```

This is **double NAT** (NAT444). Problems:
- Port forwarding impossible (you can't port forward through ISP's NAT).
- P2P and gaming severely affected.
- Requires IPv6 or a tunnel (VPN) for public accessibility.

---

## 15. NAT Problems and Failure Modes

### 1. Port Exhaustion

With PAT, when all 64,512 available ports are in use, new connections are dropped.

```
Condition: Large office, single public IP
65,000 concurrent TCP connections active
New connection attempt → NAT: no ports available → DROP

Detection:
  netstat -n | wc -l   (count connections)
  conntrack -C          (count conntrack entries)
  sysctl net.netfilter.nf_conntrack_max   (check limit)

Solution:
  Add more public IPs (IP pool NAT)
  Reduce conntrack timeout values
  Increase nf_conntrack_max
```

### 2. Conntrack Table Full

```
# Default max entries (varies by distro, RAM)
sysctl net.netfilter.nf_conntrack_max
# Default: often 65536 or 131072

# Increase limit:
sysctl -w net.netfilter.nf_conntrack_max=1048576

# Symptoms when full:
#   "nf_conntrack: table full, dropping packet" in dmesg
#   New connections fail while existing ones work
```

### 3. NAT Breaking Protocols with Embedded IPs

Protocols that embed IP addresses in their application payload:

| Protocol | Problem | Solution |
|----------|---------|----------|
| FTP (active) | Server connects back to client's private IP | Use passive FTP, or FTP ALG |
| SIP/VoIP | Private IP in SIP headers/SDP body | STUN in client, or disable SIP ALG |
| H.323 | Private IP in call signaling | H.323 ALG, or use SBC |
| PPTP VPN | GRE protocol has no ports | NAT-T for GRE, or use OpenVPN/WireGuard |

### 4. Asymmetric Routing Breaking NAT

```
Packet goes:    Client → Router-A (NAT) → Internet → Server
Reply comes:    Server → Router-B (no NAT entry!) → DROP

Solution: Ensure all traffic for a flow passes through the same NAT device.
```

### 5. ICMP Error Message Tracking

ICMP error messages embed the original packet's IP header. NAT must inspect this embedded header to correlate the error to the correct internal host:

```
Client sends: src=PublicIP:54321 → dst=Server
Server responds with ICMP Unreachable, embedding original packet header
NAT receives ICMP, must look inside, see PublicIP:54321, map to 192.168.1.10:54321
Deliver ICMP to correct internal host
```

If NAT doesn't handle this (buggy implementation), ICMP errors are silently dropped — path MTU discovery fails, connections mysteriously stall.

---

## 16. Full Protocol Walkthrough — Packet by Packet

This is a complete trace of a web browser on an internal host making an HTTPS request through a NAT router to a public web server. Every packet, every header change, every table lookup — nothing omitted.

### Setup

```
Internal Host:  192.168.1.10  (Chrome browser)
NAT Router:     LAN: 192.168.1.1  |  WAN: 203.0.113.45
Web Server:     93.184.216.34     (example.com)
Protocol:       TCP (HTTPS, port 443)
```

### Step 1 — TCP SYN (Client → Server)

```
Chrome generates TCP SYN:
  Src IP:   192.168.1.10
  Src Port: 54321           (random ephemeral port chosen by OS)
  Dst IP:   93.184.216.34
  Dst Port: 443
  Flags:    SYN
  IP Checksum: 0xA1B2       (covers IP header)
  TCP Checksum: 0xC3D4      (covers TCP header + pseudo-header with src/dst IP)

Packet arrives at NAT Router (192.168.1.1) on LAN interface (eth1)
Routing decision: dst is 93.184.216.34 → route out WAN interface (eth0)

SNAT/PAT rule applies (POSTROUTING chain):
  New connection → create translation table entry:
    Protocol: TCP
    Int: 192.168.1.10:54321
    Ext: 203.0.113.45:54321  (port preserved, no collision)
    Remote: 93.184.216.34:443

  Modify packet:
    Src IP:  192.168.1.10 → 203.0.113.45  (CHANGED)
    Recalculate IP checksum:  0xA1B2 → 0xE5F6  (NEW)
    Recalculate TCP checksum: 0xC3D4 → 0x1A2B  (NEW — includes src IP in pseudo-header)

Packet sent out WAN interface (eth0):
  Src IP:   203.0.113.45   ← server sees this
  Src Port: 54321
  Dst IP:   93.184.216.34
  Dst Port: 443
  Flags:    SYN
```

### Step 2 — TCP SYN-ACK (Server → Client)

```
Server (93.184.216.34) receives SYN, responds:
  Src IP:   93.184.216.34
  Src Port: 443
  Dst IP:   203.0.113.45  ← sent to NAT router's public IP
  Dst Port: 54321
  Flags:    SYN, ACK

Arrives at NAT Router on WAN interface (eth0)
Lookup in translation table:
  Key: dst=203.0.113.45:54321, src=93.184.216.34:443, proto=TCP
  Found: Int=192.168.1.10:54321

DNAT (reverse SNAT) applies:
  Dst IP: 203.0.113.45 → 192.168.1.10   (CHANGED)
  Recalculate IP checksum
  Recalculate TCP checksum

Packet forwarded to LAN:
  Src IP:   93.184.216.34
  Src Port: 443
  Dst IP:   192.168.1.10   ← correct internal host
  Dst Port: 54321
  Flags:    SYN, ACK

Chrome receives SYN-ACK, sends ACK — same translation process repeats.
Connection state in NAT table: ESTABLISHED
```

### Step 3 — HTTP Data Transfer

```
Chrome sends: "GET / HTTP/1.1\r\nHost: example.com\r\n..."

This data goes through the same SNAT translation.
The web server sends back HTML — same reverse translation.

NAT is TRANSPARENT to both Chrome and the web server.
Chrome thinks it's talking directly to 93.184.216.34.
Server thinks it's talking to 203.0.113.45 (the NAT's public IP).
```

### Step 4 — TCP FIN (Connection Close)

```
Chrome closes: sends FIN
  → SNAT → NAT table state: FIN_WAIT

Server responds: FIN-ACK
  → reverse SNAT → Chrome receives FIN-ACK

Chrome sends: ACK
  → SNAT → NAT table state: TIME_WAIT → (120s later) → DELETED

Translation table entry is removed.
Port 54321 is now available for reuse.
```

### Full Flow ASCII Diagram

```
CHROME (192.168.1.10)         NAT ROUTER                   SERVER (93.184.216.34)
        |                  LAN:192.168.1.1                         |
        |                  WAN:203.0.113.45                        |
        |                         |                                |
        |--- SYN --------------->|                                |
        |  src:192.168.1.10:54321 |                                |
        |  dst:93.184.216.34:443  |                                |
        |                         |--[SNAT: src→203.0.113.45]---->|
        |                         |  src:203.0.113.45:54321        |
        |                         |  dst:93.184.216.34:443         |
        |                         |                                |
        |                         |<---------- SYN-ACK ------------|
        |                         |  src:93.184.216.34:443         |
        |                         |  dst:203.0.113.45:54321        |
        |<--[UNSNAT: dst→192.168.1.10]---|                        |
        |  src:93.184.216.34:443  |                                |
        |  dst:192.168.1.10:54321 |                                |
        |                         |                                |
        |--- ACK ---------------->|--[SNAT]----------------------->|
        |      (connection ESTABLISHED)                           |
        |                         |                                |
        |--- GET / HTTP/1.1 ----->|--[SNAT]----------------------->|
        |                         |                                |
        |                         |<---------- 200 OK -------------|
        |<--- 200 OK ------------|                                |
        |                         |                                |
        |--- FIN ---------------->|--[SNAT]----------------------->|
        |                         |<---------- FIN-ACK ------------|
        |<--- FIN-ACK ------------|                                |
        |--- ACK ---------------->|--[SNAT]----------------------->|
        |                         |                                |
        |         (NAT table entry deleted after TIME_WAIT)        |
```

---

## 17. Mental Models and Summary Cheatsheet

### The Three Core Mental Models

**Mental Model 1 — The Post Office (SNAT)**
> NAT is a post office at the border of a private community. Internal mail goes out with the post office's return address. Replies come back to the post office, which looks up the original sender and delivers it. The post office keeps a logbook (translation table) of all ongoing correspondence.

**Mental Model 2 — The Hotel Receptionist (DNAT)**
> DNAT is a hotel receptionist. External callers dial the hotel's main number (public IP) and ask for "room 80" (port). The receptionist connects them to the actual guest (internal server). The hotel's main number is what the outside world knows; the room number is internal.

**Mental Model 3 — The Shared Phone System (PAT)**
> PAT is an office with one external phone number (public IP) but many employees (internal hosts). When an employee makes a call, the switchboard (NAT router) assigns that call an extension number (port). When a call comes back to the main number + extension, the switchboard knows exactly which employee it's for. The office can have hundreds of concurrent external calls using just one external number.

### Quick Reference Cheatsheet

```
+==============================================================================+
|                        NAT / SNAT / DNAT / PAT CHEATSHEET                   |
+==============================================================================+

SNAT (Source NAT):
  Direction:  Outbound (LAN → Internet)
  What:       Rewrites SOURCE IP (private → public)
  When:       Internal hosts initiate connections to internet
  iptables:   -t nat -A POSTROUTING -o eth0 -j SNAT --to-source PUBLIC_IP
  Masquerade: -t nat -A POSTROUTING -o eth0 -j MASQUERADE  (dynamic IP)

DNAT (Destination NAT):
  Direction:  Inbound (Internet → LAN)
  What:       Rewrites DESTINATION IP (public → private)
  When:       Port forwarding, exposing internal servers
  iptables:   -t nat -A PREROUTING -i eth0 -p tcp --dport 80
                    -j DNAT --to-destination INTERNAL_IP:PORT

PAT (Port Address Translation):
  Type:       Special case of SNAT
  Also called: NAT Overload, IP Masquerading
  What:       Rewrites SOURCE IP + SOURCE PORT
  Why:        Allows many:1 mapping (many private hosts → one public IP)
  Key insight: Port number (16-bit) = up to 64K concurrent sessions per IP

HOOKS (where rules apply):
  PREROUTING  → DNAT (before routing decision)
  POSTROUTING → SNAT/Masquerade (after routing decision)

TIMEOUTS (default Linux):
  TCP established: 432000s (5 days)
  TCP time_wait:   120s
  UDP:             30s
  ICMP:            30s

+==============================================================================+
```

### Protocol + NAT Compatibility Matrix

```
+------------------+--------+---------+----------------------------------+
| Protocol         | TCP/IP | NAT OK? | Notes                            |
+------------------+--------+---------+----------------------------------+
| HTTP/HTTPS       | TCP    |   YES   | Works perfectly                  |
| DNS (standard)   | UDP    |   YES   | Short UDP, works fine            |
| SSH              | TCP    |   YES   | Works perfectly                  |
| FTP (active)     | TCP    |   NO    | Needs ALG or use passive FTP     |
| FTP (passive)    | TCP    |   YES   | Client initiates data channel    |
| SIP/VoIP         | UDP    | PARTIAL | Needs STUN or good SIP stack     |
| RTP (VoIP media) | UDP    | PARTIAL | Keep-alive required              |
| IPSec (ESP/AH)   | IP     |   NO    | No ports; needs NAT-T (UDP 4500) |
| PPTP VPN         | GRE    | PARTIAL | GRE has no ports, special ALG    |
| WebRTC           | UDP    |   YES   | Built-in ICE/STUN/TURN           |
| BitTorrent       | TCP/UDP| PARTIAL | Needs port forwarding for seeding|
| QUIC             | UDP    |   YES   | Self-manages NAT traversal       |
| ICMP ping        | ICMP   |   YES   | Uses ICMP identifier field       |
| Traceroute       | UDP/ICMP|  YES   | ICMP error passthrough required  |
+------------------+--------+---------+----------------------------------+
```

### The Deep Insight — NAT's True Nature

NAT is fundamentally a **stateful rewriting system** operating at the intersection of the Network and Transport layers. Every packet that passes through NAT is:

1. **Inspected** (read source/destination)
2. **Looked up** (translation table query — O(1) hash lookup)
3. **Modified** (IP address and/or port rewritten)
4. **Revalidated** (checksums recalculated)
5. **Forwarded** (sent on its way)

The translation table is the memory of all active connections. Lose the table (router reboot), and all connections are severed — because replies will arrive with no matching entry and be dropped.

This is also why **NAT is not just an IP concept** — it requires deep understanding of TCP state, UDP behavior, ICMP mechanics, and application-layer protocols. The protocols that break under NAT are precisely those that forgot they might be translated, embedding private addresses where only the application — not the network — can see them.

---

*Guide complete. Every concept in this guide is operational knowledge — understanding these mechanics gives you the mental model to debug any NAT-related network issue, design any NAT topology, and reason precisely about why P2P, VoIP, and VPN protocols require special handling.*