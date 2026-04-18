# The Complete Network Router Debugging & Troubleshooting Guide

> *"The expert in anything was once a beginner who refused to quit understanding."*

---

## Table of Contents

1. [Foundational Concepts — Read This First](#1-foundational-concepts)
2. [The OSI Model — The Mental Map of Networking](#2-osi-model)
3. [The Diagnostic Mindset — How Experts Think](#3-diagnostic-mindset)
4. [Layer-by-Layer Troubleshooting Framework](#4-layer-by-layer-framework)
5. [Physical Layer Tools & Techniques](#5-physical-layer)
6. [Data Link Layer Debugging](#6-data-link-layer)
7. [Network Layer Debugging](#7-network-layer)
8. [Ping & Traceroute — Deep Internals](#8-ping-and-traceroute)
9. [Advanced CLI Diagnostic Tools](#9-advanced-cli-tools)
10. [Routing Protocol Diagnostics](#10-routing-protocols)
11. [Firewall & ACL Debugging](#11-firewall-acl)
12. [DNS Debugging](#12-dns-debugging)
13. [DHCP Debugging](#13-dhcp-debugging)
14. [NAT Debugging](#14-nat-debugging)
15. [QoS & Bandwidth Debugging](#15-qos-bandwidth)
16. [Packet Capture & Deep Inspection](#16-packet-capture)
17. [Log Analysis & SNMP Monitoring](#17-logs-snmp)
18. [VPN & Tunnel Debugging](#18-vpn-tunnels)
19. [Wireless/WiFi Router Debugging](#19-wireless-wifi)
20. [Common Failure Patterns & Decision Trees](#20-failure-patterns)
21. [Systematic Troubleshooting Checklists](#21-checklists)
22. [Mental Models for Network Mastery](#22-mental-models)

---

## 1. Foundational Concepts

Before any tool makes sense, you must deeply understand what a **router** does and the vocabulary of networking.

### What is a Router?

A **router** is a device that operates at **Layer 3 (Network Layer)** of the OSI model. Its core job is:

```
Receive a packet → Read destination IP → Consult routing table → Forward packet out the correct interface
```

Think of a router as a **post office sorting center**: packages (packets) arrive, the address (IP) is read, and the package is sent toward its destination through the best known path.

### Essential Vocabulary

| Term | Plain English Explanation |
|------|--------------------------|
| **Packet** | A small chunk of data with a source IP, destination IP, and payload |
| **Interface** | A port on the router (eth0, fa0/0, ge-0/0/0) — the "doorways" |
| **Routing Table** | A list: "to reach network X, go through gateway Y via interface Z" |
| **Gateway** | The next router in the path — your packet's next stop |
| **Hop** | Each router a packet passes through is one "hop" |
| **TTL (Time To Live)** | A counter in the packet that decrements at each hop; prevents infinite loops |
| **MTU (Maximum Transmission Unit)** | Largest packet size a link can carry (default Ethernet = 1500 bytes) |
| **Latency** | Time delay for a packet to travel from A to B (measured in milliseconds) |
| **Jitter** | Variation in latency — inconsistency in packet arrival times |
| **Packet Loss** | % of packets that never arrive at the destination |
| **Bandwidth** | Maximum data throughput capacity of a link (e.g., 1 Gbps) |
| **Throughput** | Actual data transferred per second (always ≤ bandwidth) |
| **ARP (Address Resolution Protocol)** | Maps IP address → MAC address on local network |
| **MAC Address** | Hardware address of a network interface card (like a serial number) |
| **Subnet** | A logical division of a network (e.g., 192.168.1.0/24) |
| **CIDR** | Notation for subnets: 192.168.1.0/24 means 24-bit mask, 256 addresses |
| **Default Route** | The "if I don't know where to send it, send it here" rule (0.0.0.0/0) |
| **Next-hop** | The immediate next router IP address a packet is forwarded to |
| **AS (Autonomous System)** | A network under one administrative control (like an ISP) |
| **BGP/OSPF/EIGRP/RIP** | Routing protocols — how routers talk to each other about paths |
| **ACL (Access Control List)** | Rules that permit or deny traffic based on criteria |
| **NAT (Network Address Translation)** | Converts private IPs to public IPs and back |
| **VLAN** | Virtual LAN — logical separation of network segments |
| **Duplex** | Full-duplex = send & receive simultaneously; Half-duplex = one at a time |
| **QoS (Quality of Service)** | Priority system for different types of traffic |

---

## 2. OSI Model — The Mental Map of Networking

The **OSI (Open Systems Interconnection) model** is the single most important mental model in networking. Every problem lives at a specific layer. Master this and you gain a systematic map for debugging.

```
+--------------------------------------------------+
|  Layer 7 — APPLICATION                           |
|  HTTP, FTP, DNS, SMTP, SSH                       |
|  Tools: curl, wget, nslookup, telnet, nc         |
+--------------------------------------------------+
|  Layer 6 — PRESENTATION                         |
|  Encryption, Encoding, Compression              |
|  (SSL/TLS lives here conceptually)              |
+--------------------------------------------------+
|  Layer 5 — SESSION                              |
|  Manages connections/sessions between apps      |
+--------------------------------------------------+
|  Layer 4 — TRANSPORT                            |
|  TCP (reliable), UDP (fast, unreliable)         |
|  Tools: netstat, ss, telnet <port>              |
+--------------------------------------------------+
|  Layer 3 — NETWORK  <-- ROUTER lives here       |
|  IP addressing, routing, subnetting             |
|  Tools: ping, traceroute, route, ip route       |
+--------------------------------------------------+
|  Layer 2 — DATA LINK                            |
|  MAC addresses, Ethernet frames, switches       |
|  Tools: arp, ip neigh, show mac-address-table   |
+--------------------------------------------------+
|  Layer 1 — PHYSICAL                             |
|  Cables, fiber, electrical signals, hardware    |
|  Tools: show interface, cable tester            |
+--------------------------------------------------+
```

### The Golden Rule of Troubleshooting

> **Always start at Layer 1 and work UP.**

A Layer 7 (application) failure can be caused by any layer below it. Starting from physical and moving up eliminates entire categories of problems quickly.

```
PROBLEM: "I can't reach google.com"

Is cable connected?          (Layer 1)
  NO → Fix physical issue
  YES ↓
Is interface up/up?          (Layer 2)
  NO → Check duplex, VLAN
  YES ↓
Can I ping gateway?          (Layer 3)
  NO → Check IP, subnet, routing
  YES ↓
Can I ping 8.8.8.8?          (Layer 3 extended)
  NO → Check default route, NAT
  YES ↓
Does nslookup work?          (Layer 7 - DNS)
  NO → Fix DNS config
  YES ↓
Does curl http://google.com work? (Layer 7 - HTTP)
  NO → Check firewall/ACL/proxy
```

---

## 3. The Diagnostic Mindset — How Experts Think

### The Five-Step Expert Process

```
1. OBSERVE    → Gather all symptoms, error messages, logs
2. HYPOTHESIZE → Form a ranked list of likely causes (Layer 1 first)
3. TEST        → Run ONE targeted test at a time
4. ANALYZE     → What did the result tell you?
5. ITERATE     → Eliminate hypothesis or escalate up the layers
```

### Mental Model: "Divide and Conquer"

Never guess randomly. Instead, **bisect the problem**:

```
                  [Internet unreachable]
                         |
           +-------------+-------------+
           |                           |
    [Can I reach              [Can I reach
     my gateway?]              8.8.8.8?]
           |                           |
       YES/NO                      YES/NO
    (Local issue)             (ISP/routing issue)
```

This is like binary search in algorithms — you eliminate half the problem space with each test.

### Cognitive Principle: **Chunking**

Expert network engineers chunk symptoms into patterns. When you see "high latency + packet loss on one interface only," your brain should immediately chunk that as "likely physical/duplex issue" rather than examining it piece by piece.

Build your **pattern library** by solving many problems deliberately.

---

## 4. Layer-by-Layer Troubleshooting Framework

```
STEP-BY-STEP MASTER FLOW
========================

[Start: Network Problem Reported]
           |
           v
+----------------------+
| LAYER 1: Physical    |
| - Cable connected?   |
| - Interface up/up?   |
| - LED lights OK?     |
+----------------------+
           | PASS
           v
+----------------------+
| LAYER 2: Data Link   |
| - ARP resolving?     |
| - Duplex mismatch?   |
| - VLAN correct?      |
+----------------------+
           | PASS
           v
+----------------------+
| LAYER 3: Network     |
| - IP configured?     |
| - Gateway pingable?  |
| - Routing table OK?  |
| - NAT working?       |
+----------------------+
           | PASS
           v
+----------------------+
| LAYER 4: Transport   |
| - TCP port open?     |
| - Firewall blocking? |
| - Connections estab? |
+----------------------+
           | PASS
           v
+----------------------+
| LAYER 7: Application |
| - DNS resolving?     |
| - App responding?    |
| - Auth working?      |
+----------------------+
```

---

## 5. Physical Layer Tools & Techniques

The physical layer is the most overlooked — and often the most common cause of problems.

### Interface Status Codes

When you run `show interfaces` (Cisco) or `ip link show` (Linux), you'll see status codes:

```
Interface Status Combinations:

FastEthernet0/0 is up, line protocol is up      ← GOOD: Both physical and logical OK
FastEthernet0/0 is up, line protocol is down    ← Layer 2 problem (keepalives, encapsulation)
FastEthernet0/0 is administratively down        ← Manually shut down with "shutdown" command
FastEthernet0/0 is down, line protocol is down  ← Physical problem (cable, remote end off)
```

### Key Commands

```bash
# Cisco/IOS Router
show interfaces                    # Full status of all interfaces
show interfaces fastethernet0/0    # Specific interface
show interfaces fastethernet0/0 counters  # Packet/error counters

# Linux (modern systems use 'ip' command, older use 'ifconfig')
ip link show                       # All interface states
ip link show eth0                  # Specific interface
ip -s link show eth0               # Statistics with counters
ethtool eth0                       # Physical layer details (speed, duplex, link detected)
```

### What to Look for in Interface Output

```
FastEthernet0/0 is up, line protocol is up
  Hardware is Fast Ethernet, address is 0019.aa9b.1234
  Internet address is 192.168.1.1/24
  MTU 1500 bytes, BW 100000 Kbit/sec, DLY 100 usec
  Full-duplex, 100Mb/s, media type is RJ45
  
  5 minute input rate 0 bits/sec, 0 packets/sec
  5 minute output rate 0 bits/sec, 0 packets/sec
  
  Input errors: 0                   ← CRC errors = bad cable/SFP
  CRC: 0                            ← Non-zero = physical layer problem
  Frame: 0                          ← Framing errors = encapsulation mismatch
  Overrun: 0                        ← Buffer overruns = CPU overloaded
  Output drops: 0                   ← Drops = queue full (bandwidth congestion)
  Runts: 0                          ← Packets too small = duplex mismatch!
  Giants: 0                         ← Packets too large = MTU problem
```

### Duplex Mismatch — The Silent Killer

**Concept:** When one side is set to "Full-duplex" and the other is "Half-duplex," communication works but degrades severely under load.

```
Full-duplex end              Half-duplex end
     |                             |
  "I can send and               "I must wait before
   receive at the                sending — am I
   same time"                    interrupting?"
     |                             |
     +-------- COLLISION ----------+
               (Half sees it)
               (Full ignores it)
               
Result: Runts, CRC errors, intermittent slowness
```

**Detection:**
```bash
# Cisco
show interfaces fastethernet0/0 | include duplex
# Look for: "Half-duplex" when the other end is Full

# Linux
ethtool eth0 | grep -i duplex
```

**Fix:** Set both ends to the same duplex (prefer auto-negotiation OR manually set both to Full-duplex 1000Mbps).

---

## 6. Data Link Layer Debugging

The Data Link Layer (Layer 2) handles communication between directly connected devices using **MAC addresses**.

### ARP — Address Resolution Protocol

**Concept:** ARP answers the question: *"I know the IP address of the next-hop, but what is its MAC address so I can build the Ethernet frame?"*

```
Your router wants to send to 192.168.1.10:

1. Router broadcasts: "Who has 192.168.1.10? Tell 192.168.1.1"
2. Device 192.168.1.10 replies: "192.168.1.10 is at aa:bb:cc:dd:ee:ff"
3. Router caches this in ARP table
4. Router sends frame directly to aa:bb:cc:dd:ee:ff

ARP Table (cache):
192.168.1.10   aa:bb:cc:dd:ee:ff   eth0   30sec
192.168.1.1    11:22:33:44:55:66   eth0   permanent
```

**ARP Debugging Commands:**

```bash
# Linux
arp -n                      # Show ARP table (numeric)
ip neigh show               # Modern way to show ARP/neighbor table
ip neigh flush dev eth0     # Clear ARP cache for interface

# Cisco
show arp                    # Full ARP table
show arp 192.168.1.10       # Specific entry
clear arp-cache             # Flush ARP cache

# Windows
arp -a                      # Show ARP table
arp -d *                    # Clear ARP cache
```

### ARP Problems to Watch For

```
Problem 1: INCOMPLETE ARP entry
  192.168.1.10  (incomplete)  eth0
  Cause: Device at that IP is down or unreachable
  
Problem 2: Wrong MAC in ARP table (ARP Poisoning/Spoofing)
  192.168.1.1  aa:bb:cc:dd:ee:ff  ← should be router MAC but shows PC MAC
  Cause: ARP spoofing attack or misconfigured device
  
Problem 3: ARP entry aged out too quickly
  Cause: Short ARP cache timeout causing frequent re-ARP
  
Problem 4: Gratuitous ARP flooding
  Cause: NIC flapping, dual-homed device broadcasting
```

### VLAN Troubleshooting

**Concept:** A VLAN (Virtual LAN) logically separates devices on the same physical switch into different broadcast domains. Devices in VLAN 10 cannot communicate with VLAN 20 without going through a Layer 3 device (router or Layer 3 switch).

```
Physical Switch:
  Port 1 → VLAN 10 (Finance)
  Port 2 → VLAN 10 (Finance)
  Port 3 → VLAN 20 (Engineering)
  Port 4 → VLAN 20 (Engineering)
  Port 5 → TRUNK (carries all VLANs, tagged with 802.1Q)

Trunk Port:
  Frame arrives with VLAN tag: [Ethernet Header | VLAN Tag=10 | IP Packet | ...]
  
Problem: Device in VLAN 10 can't reach VLAN 20
  Root cause: No inter-VLAN routing configured
  OR: VLAN mismatch (port assigned wrong VLAN)
```

**VLAN Debug Commands:**

```bash
# Cisco Switch
show vlan brief                     # All VLANs and their ports
show interfaces trunk               # Trunk ports and allowed VLANs
show interfaces fastethernet0/1 switchport   # Check port VLAN assignment

# Linux (with 802.1Q)
ip link show                        # Look for eth0.10, eth0.20 (VLAN subinterfaces)
bridge vlan show                    # VLAN assignments on bridge interfaces
cat /proc/net/vlan/config           # VLAN configuration
```

---

## 7. Network Layer Debugging

This is the router's primary domain. All IP-level problems live here.

### Understanding the Routing Table

The routing table is the router's "map." It answers: *"Given a destination IP, which way should I forward this packet?"*

```
Linux Routing Table (ip route show):
default via 203.0.113.1 dev eth0         ← Default route: send unknown traffic to ISP gateway
192.168.1.0/24 dev eth1 proto kernel     ← Directly connected: reach this network via eth1
10.0.0.0/8 via 192.168.1.254 dev eth1   ← Static route: reach 10.x.x.x via this gateway
172.16.0.0/12 via 192.168.1.253 dev eth1 proto ospf  ← Learned via OSPF

Cisco Routing Table (show ip route):
C    192.168.1.0/24 is directly connected, FastEthernet0/1    ← C = Connected
S    10.0.0.0/8 [1/0] via 192.168.1.254                       ← S = Static
O    172.16.0.0/12 [110/20] via 192.168.1.253                 ← O = OSPF
B    8.8.0.0/16 [200/0] via 203.0.113.1                       ← B = BGP
```

### Route Lookup: Longest Prefix Match

**Concept:** When multiple routes match a destination, the router picks the **most specific** (longest prefix/highest mask) route.

```
Destination: 10.1.1.5

Routing Table:
  10.0.0.0/8      via gateway A
  10.1.0.0/16     via gateway B
  10.1.1.0/24     via gateway C   ← Winner! Most specific match
  0.0.0.0/0       via default gw

The router forwards to gateway C.
```

### Key Routing Commands

```bash
# Linux — Modern ip command
ip route show                           # Full routing table
ip route show table all                 # All routing tables (including policy routing)
ip route get 8.8.8.8                    # Which route would be used for 8.8.8.8?
ip route add 10.0.0.0/8 via 192.168.1.1 # Add static route
ip route del 10.0.0.0/8                 # Delete route
ip route flush cache                    # Clear route cache
ip rule show                            # Policy routing rules

# Linux — older route command
route -n                                # Routing table (numeric, no DNS resolution)
route add -net 10.0.0.0/8 gw 192.168.1.1

# Cisco
show ip route                           # IPv4 routing table
show ip route 8.8.8.8                   # Specific destination lookup
show ip route summary                   # Summary statistics
show ip interface brief                 # All interfaces and IP assignments
debug ip routing                        # Real-time routing table changes (USE CAREFULLY!)

# Windows
route print                             # Windows routing table
route add 10.0.0.0 mask 255.0.0.0 192.168.1.1   # Add route

# Verify what IP would be used (crucial for debugging)
ip route get 203.0.113.50
# Output: 203.0.113.50 via 192.168.1.1 dev eth0 src 192.168.1.100
```

### IP Address Configuration

```bash
# Linux
ip addr show                    # All interfaces and IPs
ip addr show eth0               # Specific interface
ip addr add 192.168.1.1/24 dev eth0   # Add IP
ip addr del 192.168.1.1/24 dev eth0   # Remove IP

# Check for duplicate IP addresses (common problem!)
arping -D -I eth0 192.168.1.1   # -D = Detect duplicates (exits 0 if duplicate found)

# Cisco
show ip interface brief          # Summary: interface, IP, status
show ip interface fastethernet0/0  # Full IP details

# Windows
ipconfig /all                   # Full IP configuration
ipconfig /release               # Release DHCP lease
ipconfig /renew                 # Renew DHCP lease
```

---

## 8. Ping & Traceroute — Deep Internals

You know these tools. Now let's go deeper into what the results actually mean.

### Ping — Under the Hood

Ping uses **ICMP Echo Request** (type 8) and **ICMP Echo Reply** (type 0).

```
Your machine                    Target machine
    |                                |
    |--- ICMP Echo Request (type 8) ->|
    |<-- ICMP Echo Reply (type 0) ---|
    
Time measured = RTT (Round Trip Time)
```

**Interpreting Ping Output:**

```
$ ping 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=55 time=12.3 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=55 time=12.1 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=55 time=45.8 ms   ← Spike = jitter
Request timeout for icmp_seq 4                            ← Packet lost

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 4 received, 20% packet loss        ← 20% loss = serious problem
round-trip min/avg/max/stddev = 12.1/20.7/45.8/14.8 ms  ← High stddev = jitter

Fields:
  ttl=55     ← Started at 64 (Linux default), passed through 9 hops to reach you
             ← Common starting TTLs: Linux=64, Windows=128, Cisco=255
  time=12.3  ← Round Trip Time in milliseconds
  icmp_seq=1 ← Sequence number (gaps = lost packets)
```

**Advanced Ping Options:**

```bash
# Linux
ping -c 10 8.8.8.8              # Send exactly 10 packets
ping -i 0.2 8.8.8.8             # Send every 0.2 seconds (flood-like)
ping -s 1400 8.8.8.8            # Large 1400-byte packets (test MTU)
ping -M do -s 1472 8.8.8.8      # Don't Fragment flag — MTU path discovery
ping -W 1 8.8.8.8               # 1 second timeout per packet
ping -q -c 100 8.8.8.8          # Quiet, 100 packets (get accurate loss %)
ping -t 10 8.8.8.8              # Set TTL to 10 (simulate distant hop testing)
ping -I eth1 8.8.8.8            # Force ping out specific interface
ping6 ::1                        # IPv6 ping

# Cisco
ping 8.8.8.8                    # Basic ping
ping 8.8.8.8 repeat 1000        # 1000 packets
ping 8.8.8.8 size 1400          # Large packets
ping 8.8.8.8 source loopback0   # Ping from specific source IP
ping 8.8.8.8 df-bit             # Set Don't Fragment bit (MTU testing)
```

**Ping Failure Analysis:**

```
Scenario 1: Destination Host Unreachable
  "Destination Host Unreachable" → Router knows the network but host is down/gone

Scenario 2: No route to host
  "Network Unreachable" → No routing table entry for that destination

Scenario 3: Request timeout
  Silence → Could be: host is down, ICMP blocked by firewall, packet lost in transit

Scenario 4: Ping works but web browsing fails
  → Layer 3 is OK, problem is Layer 4+ (DNS, TCP, firewall blocking port 80/443)

Scenario 5: Ping works one way but not other
  → Asymmetric routing or one-directional ACL/firewall
```

### Traceroute — Deep Dive

Traceroute exploits the **TTL mechanism** to map the path packet takes.

```
How Traceroute Works:
=====================

Step 1: Send packet with TTL=1
  Your PC → Router1 → Router1 decrements TTL to 0
  Router1 sends ICMP "Time Exceeded" back to your PC
  You learn: Router1 is at IP X.X.X.X, latency = Y ms

Step 2: Send packet with TTL=2
  Your PC → Router1 → Router2 → Router2 decrements TTL to 0
  Router2 sends ICMP "Time Exceeded" back to your PC
  You learn: Router2 is at IP A.A.A.A, latency = B ms

Step 3: Continue until destination reached...
  Final hop: ICMP "Echo Reply" (ping reply) = destination reached

Traceroute sends 3 probes per TTL to get 3 latency samples.
```

**Reading Traceroute Output:**

```
$ traceroute 8.8.8.8
traceroute to 8.8.8.8, 30 hops max, 60 byte packets

1  192.168.1.1      1.2 ms   1.1 ms   1.0 ms    ← Your local router (LAN)
2  10.20.30.1       8.5 ms   8.3 ms   8.4 ms    ← ISP first hop
3  203.0.113.1      9.1 ms   9.3 ms   9.2 ms    ← ISP backbone
4  * * *                                         ← Firewall blocking ICMP TTL Exceeded
5  72.14.215.1      11.2 ms  11.1 ms  11.0 ms   ← Google's network
6  8.8.8.8          12.3 ms  12.1 ms  12.2 ms   ← Destination!

Interpreting:
  * * *   → ICMP blocked by firewall (not necessarily a problem — check if final dest reached)
  High latency at hop N → Congestion or long physical distance at that hop
  High latency from hop N onwards → Problem introduced at hop N
  Increasing latency then plateau → Normal (just distance/routing)
  Sudden latency spike that persists → Real bottleneck
```

**Advanced Traceroute:**

```bash
# Linux
traceroute 8.8.8.8                  # UDP-based (default)
traceroute -I 8.8.8.8               # ICMP-based (like Windows tracert)
traceroute -T -p 80 8.8.8.8         # TCP SYN on port 80 (bypasses ICMP firewalls)
traceroute -T -p 443 8.8.8.8        # TCP SYN on port 443 (HTTPS)
traceroute -n 8.8.8.8               # No DNS resolution (faster)
traceroute -q 5 8.8.8.8             # 5 probes per hop instead of 3
traceroute -m 50 8.8.8.8            # Max 50 hops
traceroute -s 192.168.1.100 8.8.8.8 # Source IP address
traceroute6 2001:4860:4860::8888    # IPv6 traceroute

# Better alternatives to traceroute
mtr 8.8.8.8                         # My Traceroute: continuous real-time traceroute
mtr --report 8.8.8.8                # Generate report
mtr --tcp --port 443 8.8.8.8        # TCP mode

# Windows
tracert 8.8.8.8                     # Windows traceroute
```

---

## 9. Advanced CLI Diagnostic Tools

### `mtr` — My Traceroute (Best Tool for Latency Analysis)

MTR combines ping and traceroute into a real-time continuous view. It's the **best single tool** for identifying where latency and packet loss originate.

```
$ mtr --report 8.8.8.8

HOST: mymachine                    Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 192.168.1.1               0.0%    10    1.2   1.1   1.0   1.3   0.1
  2.|-- 10.20.30.1                0.0%    10    8.5   8.4   8.3   8.6   0.1
  3.|-- 203.0.113.1              20.0%    10    9.1   9.5   9.1  12.3   1.0  ← 20% LOSS HERE!
  4.|-- 72.14.215.1               0.0%    10   11.2  11.1  11.0  11.3   0.1
  5.|-- 8.8.8.8                   0.0%    10   12.3  12.2  12.1  12.5   0.1

Analysis:
  - Hop 3 shows 20% packet loss (ISP backbone issue)
  - Hop 4 onwards is fine (0% loss)
  - Conclusion: Problem is at ISP's 203.0.113.1 router — ISP's problem to fix

CRITICAL INSIGHT: Loss at intermediate hops that doesn't persist to final destination
  is often just ICMP deprioritization at that router (not a real problem).
  Only care about loss that persists to the FINAL destination.
```

### `ss` — Socket Statistics (Better than netstat)

**Concept:** Sockets are the endpoints of network connections. `ss` shows all active connections, listening ports, and socket states.

```bash
ss -tuln                   # TCP/UDP, listening, numeric (no DNS lookup)
ss -tunap                  # All connections with process names
ss -s                      # Summary statistics
ss -t state established    # Only established TCP connections
ss -t state time-wait      # TIME_WAIT connections (potential port exhaustion)
ss -ltp                    # Listening TCP with process
ss -o state fin-wait-1     # Connections in FIN-WAIT-1

# Filter by port
ss -tnp sport = :80        # Who is connected to port 80
ss -tnp dport = :443       # Connections TO port 443

# Output example:
# State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port
# ESTAB  0      0       192.168.1.5:52341   8.8.8.8:443     ← Active HTTPS connection
# LISTEN 0      128     0.0.0.0:22          0.0.0.0:*        ← SSH listening
```

**TCP States — Know These:**

```
TCP State Machine:
==================
  LISTEN        → Server waiting for connections
  SYN_SENT      → Client sent SYN, waiting for SYN-ACK
  SYN_RECEIVED  → Server got SYN, sent SYN-ACK, waiting for ACK
  ESTABLISHED   → Active connection (data flowing)
  FIN_WAIT_1    → Sent FIN (closing)
  FIN_WAIT_2    → Received ACK of FIN, waiting for remote FIN
  CLOSE_WAIT    → Received FIN from remote, waiting for app to close
  TIME_WAIT     → Waiting to ensure remote received ACK (lasts 2*MSL = ~2 min)
  CLOSED        → No connection

Debugging Insight:
  Many TIME_WAIT = High connection turnover (normal for HTTP/1.0, fix with keepalive)
  Many CLOSE_WAIT = Application not calling close() (application bug)
  Many SYN_SENT = Destination unreachable or firewall dropping SYN
```

### `netstat` — Network Statistics (Older but Universal)

```bash
netstat -rn               # Routing table (numeric)
netstat -an               # All connections (numeric)
netstat -tulnp            # Listening TCP/UDP with process
netstat -s                # Protocol statistics (errors, dropped packets)
netstat -i                # Interface statistics
netstat -g                # Multicast group memberships
```

### `tcpdump` — Packet Sniffer (Most Powerful Tool)

**Concept:** tcpdump captures actual packets on the wire. It's like a stethoscope for your network — you can hear everything.

```bash
# Basic usage
tcpdump -i eth0                          # Capture on eth0
tcpdump -i any                           # All interfaces
tcpdump -n                               # Don't resolve hostnames (faster)
tcpdump -nn                              # Don't resolve hostnames OR port names
tcpdump -v                               # Verbose
tcpdump -vvv                             # Very verbose
tcpdump -X                               # Show packet contents in hex and ASCII

# Write to file (for later analysis in Wireshark)
tcpdump -i eth0 -w capture.pcap
tcpdump -r capture.pcap                  # Read from file

# Filters (BPF - Berkeley Packet Filter syntax)
tcpdump host 8.8.8.8                     # Traffic to/from 8.8.8.8
tcpdump src 192.168.1.5                  # Traffic FROM 192.168.1.5
tcpdump dst 8.8.8.8                      # Traffic TO 8.8.8.8
tcpdump port 80                          # HTTP traffic
tcpdump tcp port 443                     # HTTPS TCP only
tcpdump udp port 53                      # DNS queries
tcpdump icmp                             # Only ICMP (ping)
tcpdump arp                              # Only ARP
tcpdump -i eth0 not port 22              # Exclude SSH (keep terminal usable!)
tcpdump tcp[tcpflags] & tcp-syn != 0     # Only TCP SYN packets
tcpdump 'tcp[tcpflags] == tcp-syn'       # SYN only (no ACK = new connections)

# Combined filters
tcpdump -i eth0 -nn 'host 8.8.8.8 and port 53'
tcpdump -i eth0 -nn 'src net 192.168.1.0/24 and dst port 80'
tcpdump -i eth0 -nn '(tcp or udp) and port 53'
```

**Reading tcpdump Output:**

```
$ tcpdump -nn -i eth0 port 53

12:34:56.789012 IP 192.168.1.5.52341 > 8.8.8.8.53: UDP, length 35
  ↑timestamp     ↑source IP.port     ↑dest IP.port  ↑protocol  ↑size

12:34:56.801234 IP 8.8.8.8.53 > 192.168.1.5.52341: UDP, length 65
  ↑DNS reply from 8.8.8.8 back to our machine

Good DNS: Request → Reply within milliseconds
Bad DNS: Request → Request → Request → no reply (timeout, firewall blocking UDP 53)
```

### `nmap` — Network Scanner

**Concept:** nmap sends various packets to discover hosts, open ports, services, and OS fingerprints.

```bash
# Host discovery
nmap -sn 192.168.1.0/24             # Ping scan — find live hosts
nmap -sn 192.168.1.0/24 --send-ip  # ARP-based scan (more reliable on LAN)

# Port scanning
nmap 192.168.1.1                    # Default: scan 1000 common ports (TCP)
nmap -p 80,443,22 192.168.1.1      # Specific ports
nmap -p 1-65535 192.168.1.1        # All ports
nmap -sU -p 53,67,161 192.168.1.1  # UDP scan (DNS, DHCP, SNMP)

# Scan types
nmap -sS 192.168.1.1               # SYN scan (stealth — doesn't complete TCP handshake)
nmap -sT 192.168.1.1               # Full TCP connect (noisier)
nmap -sA 192.168.1.1               # ACK scan (detect firewalls/ACLs)

# Service and version detection
nmap -sV 192.168.1.1               # Service version detection
nmap -O 192.168.1.1                # OS detection
nmap -A 192.168.1.1                # Aggressive: OS + version + scripts + traceroute

# Useful for router debugging
nmap -sU -p 161 192.168.1.1        # Test if SNMP is open
nmap -p 22,23,80,443,8080 192.168.1.1  # Common management ports
```

### `curl` / `wget` — HTTP Layer Testing

```bash
# Test HTTP connectivity with full details
curl -v http://192.168.1.1                    # Verbose HTTP request
curl -vk https://192.168.1.1                  # Verbose HTTPS (ignore cert)
curl -o /dev/null -w "%{time_total}" http://google.com  # Measure total time
curl -o /dev/null -w "DNS: %{time_namelookup}\nConnect: %{time_connect}\nTTFB: %{time_starttransfer}\nTotal: %{time_total}\n" https://google.com

# Test specific source IP/interface
curl --interface eth1 http://8.8.8.8

# Test through proxy
curl -x http://proxy:3128 http://google.com

# Follow redirects
curl -L http://google.com
```

### `netcat` (nc) — The "Swiss Army Knife"

**Concept:** nc can open raw TCP/UDP connections to any port. Essential for testing port connectivity.

```bash
# Test if port is open (TCP)
nc -zv 192.168.1.1 80              # -z = don't send data, -v = verbose
nc -zv 8.8.8.8 53                  # Test DNS port
nc -zv 192.168.1.1 22              # Test SSH port

# UDP test
nc -zvu 192.168.1.1 53             # -u = UDP

# Scan range of ports
nc -zv 192.168.1.1 20-25           # Ports 20 through 25

# Test bandwidth (crude)
# On server:
nc -l -p 9999 > /dev/null
# On client:
dd if=/dev/zero bs=1M count=100 | nc 192.168.1.1 9999

Output: "Connection refused"    → Port closed (server rejecting)
Output: "Connection timed out"  → Firewall dropping packets (no response at all)
Output: "Connected"             → Port open!
```

### `iperf3` — Bandwidth Testing

**Concept:** iperf3 is the gold standard for measuring actual bandwidth and throughput between two points.

```bash
# Server side (run on one machine)
iperf3 -s                          # Start iperf server on port 5201
iperf3 -s -p 9999                  # Custom port

# Client side (run on the other machine)
iperf3 -c 192.168.1.1              # Test TCP bandwidth to server
iperf3 -c 192.168.1.1 -u           # UDP test
iperf3 -c 192.168.1.1 -t 30        # Run for 30 seconds
iperf3 -c 192.168.1.1 -P 4         # 4 parallel streams (stress test)
iperf3 -c 192.168.1.1 -b 100M -u   # UDP at 100Mbps
iperf3 -c 192.168.1.1 -R           # Reverse direction (server sends to client)
iperf3 -c 192.168.1.1 --bidir      # Bidirectional simultaneously

# Output interpretation:
# [ 5]  0.00-1.00 sec  112 MBytes  940 Mbits/sec  → ~940 Mbps (near gigabit, good!)
# [ 5]  0.00-1.00 sec   11 MBytes   92 Mbits/sec  → Only 92 Mbps on gigabit link — problem!
```

### `hping3` — Advanced Packet Crafting

```bash
# TCP SYN flood test (careful — only use on your own equipment!)
hping3 -S -p 80 192.168.1.1        # Send TCP SYN to port 80

# Test with specific flags
hping3 -A -p 80 192.168.1.1        # ACK scan (detect stateful firewall)
hping3 --icmp 192.168.1.1          # ICMP ping
hping3 -2 -p 53 192.168.1.1        # UDP to port 53

# Traceroute variant
hping3 --traceroute -V -1 8.8.8.8  # ICMP traceroute with verbose
```

---

## 10. Routing Protocol Diagnostics

### OSPF (Open Shortest Path First)

**Concept:** OSPF is a link-state routing protocol. Each router builds a complete map of the network topology (LSDB — Link State Database) and independently calculates the best path using Dijkstra's algorithm.

```
OSPF Neighbor States (must reach FULL for proper operation):
============================================================

DOWN → Neighbor not heard from
INIT → Hello received from neighbor (one-way)
2-WAY → Both sides see each other's hellos (bidirectional)
EXSTART → Master/Slave negotiation begins
EXCHANGE → Routers exchange DBD (Database Description) packets
LOADING → Requesting and sending LSAs (Link State Advertisements)
FULL → Databases synchronized ← This is the GOAL state

OSPF Timer Defaults:
  Hello interval: 10 seconds (broadcast)
  Dead interval: 40 seconds (4x Hello)
  If dead interval expires without Hello → neighbor declared dead
```

```bash
# Cisco OSPF debugging
show ip ospf neighbor                    # Neighbor states
show ip ospf neighbor detail             # Full neighbor info
show ip ospf database                    # Link State Database
show ip ospf interface                   # OSPF interface details
show ip ospf                             # OSPF process information
debug ip ospf adj                        # Debug adjacency formation
debug ip ospf events                     # OSPF events

# Common OSPF problems:
# 1. Neighbors stuck in INIT: Unicast hello (check ip ospf network type)
# 2. Neighbors stuck in EXSTART: MTU mismatch between neighbors
# 3. Neighbors stuck in 2-WAY: DR/BDR election issue
# 4. Route not in table: Area type mismatch, LSA filtering
```

### BGP (Border Gateway Protocol)

**Concept:** BGP is the routing protocol of the internet. It's a path-vector protocol where routers advertise routes and choose paths based on policies and attributes (AS-PATH, LOCAL_PREF, MED, etc.).

```
BGP Neighbor States:
====================
IDLE        → Not attempting connection
CONNECT     → TCP connection in progress
ACTIVE       → TCP failed, retrying
OPENSENT    → TCP connected, OPEN message sent
OPENCONFIRM → OPEN received, waiting for KEEPALIVE
ESTABLISHED → BGP session up, exchanging routes ← GOAL

BGP vs OSPF:
  OSPF: Intra-domain (within your network) — fast convergence
  BGP: Inter-domain (between ISPs) — policy-driven, slow convergence
```

```bash
# Cisco BGP debugging
show ip bgp summary                      # All BGP neighbors and state
show ip bgp neighbors 203.0.113.1        # Detailed neighbor info
show ip bgp                              # Full BGP table
show ip bgp 8.8.8.0/24                  # Specific prefix
show ip bgp neighbors 203.0.113.1 received-routes  # Routes received
show ip bgp neighbors 203.0.113.1 advertised-routes  # Routes advertised

debug ip bgp 203.0.113.1 events         # BGP events with specific neighbor

# Common BGP problems:
# 1. ACTIVE state: TCP can't connect (firewall blocking port 179, wrong neighbor IP)
# 2. IDLE after reset: Authentication mismatch (MD5 password)
# 3. Routes not installed: BGP NEXT_HOP unreachable (need next-hop-self for iBGP)
# 4. Route flapping: Interface instability underneath
```

### Static Routes

```bash
# Linux — permanent routes (add to /etc/network/interfaces or netplan)
ip route add 10.0.0.0/8 via 192.168.1.1           # Add
ip route add 10.0.0.0/8 via 192.168.1.1 metric 100  # With metric (lower = preferred)
ip route del 10.0.0.0/8                             # Delete

# Cisco
ip route 10.0.0.0 255.0.0.0 192.168.1.1            # Add static route
ip route 10.0.0.0 255.0.0.0 192.168.1.1 100        # With admin distance 100
no ip route 10.0.0.0 255.0.0.0                       # Remove

# Floating static route (backup when primary routing protocol fails)
ip route 0.0.0.0 0.0.0.0 10.0.0.1 200              # AD 200 > OSPF's 110, only used if OSPF fails
```

---

## 11. Firewall & ACL Debugging

### Understanding ACLs

**Concept:** An ACL (Access Control List) is an ordered list of "permit" and "deny" rules. Traffic is checked against rules top-to-bottom. First match wins. If nothing matches, the implicit "deny all" at the end applies.

```
ACL Logic Flow:
===============

Packet arrives at interface
         |
         v
  [Rule 1: permit tcp any host 8.8.8.8 eq 53]
         |
    Matches? → YES → PERMIT (stop processing)
         |
        NO
         v
  [Rule 2: deny icmp any any]
         |
    Matches? → YES → DENY (stop processing)
         |
        NO
         v
  [Implicit deny: deny ip any any]  ← All packets fall here if no match
         |
         v
      DENY (dropped silently)
```

```bash
# Cisco ACL
show ip access-lists                    # All ACLs and hit counters
show ip access-lists INBOUND_ACL        # Specific ACL
show ip interface fastethernet0/0       # Which ACLs applied to interface
debug ip packet detail                  # Watch packets being processed (CAUTION: CPU intensive)

# Linux iptables (older)
iptables -L -n -v                       # List all rules with counters
iptables -L INPUT -n -v                 # Input chain only
iptables -L -n -v --line-numbers        # With line numbers (for deletion)
iptables -Z                             # Zero all counters (then check after traffic)
iptables -I INPUT -p tcp --dport 80 -j LOG --log-prefix "HTTP: "  # Add logging

# Linux nftables (modern replacement for iptables)
nft list ruleset                        # Show all rules
nft list table inet filter             # Specific table

# Linux — check which rule is matching (with logging)
iptables -I INPUT 1 -j LOG --log-prefix "DEBUG-INPUT: "  # Log all INPUT traffic
tail -f /var/log/syslog | grep DEBUG-INPUT               # Watch logs
```

### UFW (Uncomplicated Firewall — Ubuntu/Debian)

```bash
ufw status verbose              # Current status and rules
ufw status numbered             # Rules with numbers
ufw allow 22/tcp                # Allow SSH
ufw deny from 10.0.0.5          # Block specific IP
ufw delete 3                    # Delete rule number 3
ufw reset                       # Reset all rules
ufw logging on                  # Enable logging
```

### Common Firewall Debugging Scenarios

```
Scenario: "Connection timed out" vs "Connection refused"

  TIMED OUT = Firewall is silently DROPPING packets (no response)
    → Stateless firewall with DROP rule
    → Network unreachable

  CONNECTION REFUSED = TCP RST received (port is closed but host reachable)
    → Port not listening
    → Stateless firewall with REJECT rule

To distinguish:
  nc -zv 192.168.1.1 80
  "Connection refused" immediately → Port closed but host reachable
  "Timed out" after 30 seconds   → Firewall dropping SYN packets
```

---

## 12. DNS Debugging

**Concept:** DNS (Domain Name System) translates human-readable names (google.com) into IP addresses. It's hierarchical: your router asks a recursive resolver → root servers → TLD servers → authoritative servers.

```
DNS Resolution Path:
====================

Browser: "What is the IP of google.com?"
         |
         v
[DNS Cache] → Not found
         |
         v
[Local Router DNS] → Not found (or forward to ISP)
         |
         v
[ISP Recursive Resolver (8.8.8.8)]
         |
         v
[Root Nameservers] → "I don't know google.com, ask .com TLD servers"
         |
         v
[.com TLD Servers] → "I don't know, ask Google's nameservers: ns1.google.com"
         |
         v
[ns1.google.com] → "google.com = 142.250.80.78" ← Authoritative answer
         |
         v
[Result cached at ISP resolver, then returned to browser]
```

### DNS Tools

```bash
# nslookup (simple, cross-platform)
nslookup google.com                          # Basic lookup
nslookup google.com 8.8.8.8                  # Use specific DNS server
nslookup -type=MX gmail.com                  # MX records (mail)
nslookup -type=NS google.com                 # Nameservers

# dig (powerful DNS debugging tool)
dig google.com                               # A record (IPv4)
dig google.com AAAA                          # IPv6 address
dig google.com MX                            # Mail servers
dig google.com NS                            # Nameservers
dig google.com TXT                           # TXT records (SPF, verification)
dig @8.8.8.8 google.com                      # Use specific DNS server (8.8.8.8)
dig @192.168.1.1 google.com                  # Query local router DNS
dig +short google.com                        # Just the answer
dig +trace google.com                        # Full DNS resolution trace
dig -x 8.8.8.8                               # Reverse DNS lookup (IP → hostname)
dig google.com +nocmd +noall +answer         # Clean output

# Check DNS propagation
dig @ns1.google.com google.com               # Direct query to authoritative server

# host command
host google.com                              # Simple lookup
host -t MX gmail.com                         # MX records
host 8.8.8.8                                 # Reverse lookup

# systemd-resolved (modern Linux)
resolvectl status                            # DNS configuration
resolvectl query google.com                  # Resolve via systemd-resolved
resolvectl flush-caches                      # Clear DNS cache
```

**DNS Record Types:**

| Type | Purpose | Example |
|------|---------|---------|
| A | IPv4 address | google.com → 142.250.80.78 |
| AAAA | IPv6 address | google.com → 2607:f8b0::4006:803 |
| CNAME | Alias to another name | www.google.com → google.com |
| MX | Mail server | gmail.com → aspmx.l.google.com |
| NS | Nameserver | google.com → ns1.google.com |
| PTR | Reverse DNS | 8.8.8.8 → dns.google |
| TXT | Arbitrary text | SPF, DKIM, domain verification |
| SOA | Start of Authority | Zone admin info |

**DNS Debugging Scenarios:**

```
Problem 1: DNS works for some sites but not others
  → Try: dig @8.8.8.8 failing-domain.com (bypass local DNS)
  → If works → Local DNS/resolver issue (stale cache, split-horizon)
  → If fails → Authoritative server issue or NXDOMAIN (domain doesn't exist)

Problem 2: Intermittent DNS failures
  → mtr to DNS server (check packet loss)
  → Check if UDP 53 is being rate-limited or dropped
  → Try TCP DNS: dig +tcp google.com

Problem 3: DNS slow
  → dig google.com | grep "Query time"
  → High query time → DNS server overloaded or far away
  → Test closer DNS server: dig @1.1.1.1 google.com

Problem 4: DNS resolution different from expected
  → dig +trace google.com to see full resolution chain
  → Check if split-horizon DNS is configured (internal vs external views)
```

---

## 13. DHCP Debugging

**Concept:** DHCP (Dynamic Host Configuration Protocol) automatically assigns IP addresses, subnet masks, gateway, and DNS to devices. It uses a 4-step process called **DORA**.

```
DHCP DORA Process:
==================

Client (new device)              DHCP Server (router)
      |                                |
      |---- DISCOVER (broadcast) ----> |  "Anyone have an IP for me?"
      |                                |  (UDP src:0.0.0.0:68 dst:255.255.255.255:67)
      |                                |
      | <--- OFFER (broadcast) -----   |  "I offer you 192.168.1.100"
      |                                |  (Includes IP, mask, gateway, DNS, lease time)
      |                                |
      |---- REQUEST (broadcast) ----> |  "I accept! I want 192.168.1.100"
      |                                |
      | <--- ACK (broadcast) -------   |  "Confirmed! It's yours for 24 hours."
      |                                |
      Device configures its IP         |

DORA = Discover, Offer, Request, Acknowledge
```

```bash
# View DHCP leases (Linux server running ISC DHCP)
cat /var/lib/dhcp/dhcpd.leases     # All current and expired leases

# Manual DHCP request (Linux client)
dhclient -v eth0                    # Request new lease on eth0 (verbose)
dhclient -r eth0                    # Release current lease
dhclient -v -d eth0                 # Debug mode

# Check DHCP pool exhaustion (ISC DHCP)
dhcp-lease-list                     # Show all leases
grep "binding state active" /var/lib/dhcp/dhcpd.leases | wc -l  # Count active leases

# Cisco router DHCP debugging
show ip dhcp pool                   # DHCP pool configuration
show ip dhcp binding                # All IP assignments (MAC → IP)
show ip dhcp conflict               # IPs with conflicts
show ip dhcp server statistics      # DHCP message counters
debug ip dhcp server events         # Real-time DHCP events

# Wireshark/tcpdump for DHCP
tcpdump -i eth0 port 67 or port 68  # Capture DHCP traffic
```

**DHCP Problems:**

```
Problem 1: Client gets 169.254.x.x (APIPA address)
  → Client didn't get DHCP response
  → DHCP server unreachable (different VLAN, server down, pool exhausted)
  → Fix: Check if ip helper-address configured on router (for routed DHCP)

Problem 2: IP conflict
  → Two devices with same IP (manual config overrides DHCP, or duplicate static)
  → Detection: arping -D -I eth0 192.168.1.x

Problem 3: DHCP pool exhausted
  → All IPs in pool assigned, new devices can't get IP
  → Fix: Increase pool range, decrease lease time, check for stale leases

Problem 4: Wrong gateway/DNS from DHCP
  → Check DHCP server option 3 (router) and option 6 (DNS)
  → Fix DHCP server configuration
  
DHCP Relay (ip helper-address):
  Normally DHCP uses broadcasts (can't cross routers)
  ip helper-address converts broadcast to unicast to DHCP server
  If not configured → devices on remote VLANs can't get DHCP
```

---

## 14. NAT Debugging

**Concept:** NAT (Network Address Translation) allows multiple devices with private IPs to share one public IP when communicating with the internet. The router maintains a **translation table** mapping internal IP:port to external IP:port.

```
NAT Translation Flow:
=====================

Internal Device: 192.168.1.5:54321
                     |
                     v
         [NAT Router with public IP 203.0.113.1]
                     |
                     v
         Translation Table Entry:
         192.168.1.5:54321 → 203.0.113.1:45000

Outgoing packet:
  Before NAT: SRC = 192.168.1.5:54321
  After NAT:  SRC = 203.0.113.1:45000

Return packet:
  Before NAT: DST = 203.0.113.1:45000
  After NAT:  DST = 192.168.1.5:54321 (router translates back)
```

```bash
# Cisco NAT debugging
show ip nat translations             # Current NAT table
show ip nat translations verbose     # Detailed (age, flags)
show ip nat statistics               # Hit counters
debug ip nat                         # Real-time NAT translations (CAUTION: very verbose)
debug ip nat detailed                # Full packet details
clear ip nat translation *           # Clear all NAT translations

# Linux NAT (iptables/nftables)
iptables -t nat -L -n -v             # NAT rules with counters
conntrack -L                         # Connection tracking table (all NAT sessions)
conntrack -L --proto tcp             # TCP only
conntrack -E                         # Watch real-time connection events
conntrack -D -s 192.168.1.5         # Delete entries for specific source

# Check NAT exhaustion
conntrack -C                         # Count total connections
cat /proc/sys/net/netfilter/nf_conntrack_count    # Current connections
cat /proc/sys/net/netfilter/nf_conntrack_max      # Maximum allowed
```

**NAT Problems:**

```
Problem 1: NAT table full (connection tracking exhaustion)
  Symptom: New connections fail, existing ones work
  Check: conntrack -C vs nf_conntrack_max
  Fix: Increase nf_conntrack_max, reduce idle timeouts

Problem 2: Hairpin NAT / NAT loopback
  Symptom: Internal clients can't reach internal server by public IP
  Cause: Router doesn't support NAT loopback
  Fix: Enable NAT loopback, or use split-horizon DNS

Problem 3: Port forwarding not working
  Check: Is NAT rule actually configured?
  Check: Is internal server running and listening on that port?
  Check: Is stateful firewall also allowing the inbound connection?
  Test: nc -zv <public_ip> <port> from outside network

Problem 4: FTP/SIP/H.323 not working through NAT
  Cause: These protocols embed IP addresses in payload (ALG needed)
  Fix: Enable Application Layer Gateway (ip nat service sip, ip nat service ftp)
```

---

## 15. QoS & Bandwidth Debugging

**Concept:** QoS (Quality of Service) prioritizes network traffic so that important traffic (VoIP, video calls) gets bandwidth and low latency, while less important traffic (downloads) gets what's left.

```
Traffic Priority Queue:
=======================

High Priority:   [VoIP] → Always served first
Medium Priority: [Video] → Served after VoIP
Low Priority:    [HTTP] → Served when available
Background:      [P2P]  → Only served when nothing else needs bandwidth

Without QoS:
  All traffic treated equally → VoIP call breaks when someone downloads 4K video

With QoS:
  VoIP gets guaranteed bandwidth → Call stays clear even with heavy downloads
```

```bash
# Linux traffic control (tc command)
tc qdisc show dev eth0              # Current queue discipline
tc class show dev eth0              # Traffic classes
tc filter show dev eth0             # Filters (how traffic is classified)
tc -s qdisc show dev eth0          # Statistics (drops, bytes, packets)
tc -s class show dev eth0          # Class statistics

# Identify bandwidth hogs
iftop -i eth0                       # Real-time bandwidth by connection (install separately)
nethogs eth0                        # Bandwidth by process (install separately)
nload eth0                          # Simple bandwidth graph
bmon                                # Bandwidth monitor

# Cisco QoS debugging
show policy-map interface           # QoS policy statistics
show class-map                      # Traffic classifications
show queue fastethernet0/0          # Queue statistics
show interfaces fastethernet0/0 | include output drops  # Check for drops

# Check interface bandwidth utilization
ifstat 1                            # 1-second updates of bytes/sec
sar -n DEV 1 10                     # 10 samples of network statistics
```

---

## 16. Packet Capture & Deep Inspection

### Wireshark (GUI Packet Analyzer)

While tcpdump is CLI, **Wireshark** is the GUI version with powerful filtering and protocol dissection. You can capture with tcpdump and analyze in Wireshark.

```bash
# Capture for Wireshark analysis
tcpdump -i eth0 -w /tmp/capture.pcap        # Capture to file
tcpdump -i eth0 -w /tmp/capture.pcap -C 100 # Rotate at 100MB
tcpdump -i eth0 -w /tmp/cap%d.pcap -G 60   # New file every 60 seconds

# Transfer to machine with Wireshark
scp user@router:/tmp/capture.pcap ./
```

**Wireshark Display Filters (crucial knowledge):**

```
# IP filters
ip.addr == 8.8.8.8                   # Traffic to or from 8.8.8.8
ip.src == 192.168.1.5                # Only from this source
ip.dst == 8.8.8.8                    # Only to this destination
ip.ttl < 5                           # Low TTL packets (near expiry)

# TCP filters
tcp.port == 80                       # HTTP
tcp.flags.syn == 1                   # SYN packets only
tcp.flags.reset == 1                 # RST packets (connection resets — problem indicator!)
tcp.analysis.retransmission          # All TCP retransmissions ← Look for these
tcp.analysis.duplicate_ack           # Duplicate ACKs ← Packet loss indicator
tcp.analysis.zero_window             # Zero window ← Receiver buffer full (flow control)
tcp.time_delta > 1                   # Gaps > 1 second

# DNS filters
dns.qry.name == "google.com"         # DNS queries for google.com
dns.flags.rcode != 0                 # DNS errors (NXDOMAIN, SERVFAIL, etc.)

# ICMP filters  
icmp.type == 3                       # Destination Unreachable
icmp.type == 11                      # Time Exceeded (traceroute response)
icmp.type == 8                       # Echo Request (ping)
```

**TCP Retransmission Analysis:**

```
TCP Retransmission Causes:
==========================

Retransmission → Packet was sent but ACK not received in time
  → Could mean: packet lost, ACK lost, high latency, receiver slow

Indicators of packet loss:
  1. Multiple retransmissions of same sequence number
  2. Duplicate ACKs (receiver sending same ACK repeatedly saying "I'm missing X")
  3. Fast Retransmit: 3 duplicate ACKs triggers immediate retransmit (before timeout)

Indicators of congestion:
  1. TCP window size decreasing (congestion control kicking in)
  2. Exponential backoff in retransmit timing
  3. Throughput visible decline in Wireshark I/O graph
```

---

## 17. Log Analysis & SNMP Monitoring

### Syslog

**Concept:** Routers and network devices send log messages to a syslog server. These logs tell you about interface changes, routing events, errors, and attacks.

```
Syslog Severity Levels (know these!):
=====================================
0 - EMERGENCY   (emerg)  → System unusable
1 - ALERT        (alert)  → Immediate action needed
2 - CRITICAL     (crit)   → Critical conditions
3 - ERROR        (err)    → Error conditions
4 - WARNING      (warn)   → Warning conditions  ← Often most useful
5 - NOTICE       (notice) → Normal but significant
6 - INFORMATIONAL(info)   → Informational messages ← Most common
7 - DEBUG        (debug)  → Debug messages (very verbose)
```

```bash
# Linux syslog
tail -f /var/log/syslog                     # Live log watching
tail -f /var/log/kern.log                   # Kernel (network driver) messages
journalctl -f                               # systemd journal (modern Linux)
journalctl -u networking                    # Networking service logs
journalctl -k                               # Kernel messages only
grep -i "error\|fail\|down\|unreachable" /var/log/syslog  # Find problems

# Cisco syslog
show logging                                # All buffered logs
show logging | include OSPF                 # Filter for OSPF messages
show logging | include %LINK                # Interface up/down events
terminal monitor                            # See logs in current terminal session

# Important Cisco syslog messages to watch:
# %LINK-3-UPDOWN: Interface FastEthernet0/0, changed state to down
# %OSPF-5-ADJCHG: OSPF neighbor changed state to FULL
# %BGP-5-ADJCHANGE: BGP neighbor 203.0.113.1 Up
# %SEC-6-IPACCESSLOGP: list ACL_NAME denied tcp 1.2.3.4(1234) -> 192.168.1.1(80)
```

### SNMP — Simple Network Management Protocol

**Concept:** SNMP allows centralized monitoring of network devices. A monitoring system (NMS) polls devices periodically, or devices send alerts (traps) when events occur.

```
SNMP Architecture:
==================

[NMS - Network Management System]
  (Nagios, Zabbix, PRTG, LibreNMS)
           |
    SNMP Polls (every 60s)
           |
           v
[Router SNMP Agent]
  Exposes data via MIB (Management Information Base)
  MIB = Database of variables (CPU%, bandwidth, interface counters, etc.)
  Each variable has an OID (Object Identifier)

OID Examples:
  1.3.6.1.2.1.1.1.0       → sysDescr (device description)
  1.3.6.1.2.1.2.2.1.10.1  → ifInOctets for interface 1 (bytes received)
  1.3.6.1.2.1.2.2.1.16.1  → ifOutOctets for interface 1 (bytes sent)
```

```bash
# SNMP tools
snmpwalk -v2c -c public 192.168.1.1 .1.3.6.1.2.1.1    # Walk system info
snmpget -v2c -c public 192.168.1.1 .1.3.6.1.2.1.1.1.0  # Get sysDescr
snmpwalk -v2c -c public 192.168.1.1 .1.3.6.1.2.1.2.2   # All interface data
snmptrapd -f -Le -c /etc/snmp/snmptrapd.conf            # Receive SNMP traps

# Check if SNMP is working
nmap -sU -p 161 192.168.1.1                              # Test SNMP port

# Cisco SNMP configuration check
show snmp                               # SNMP statistics
show snmp community                     # Community strings configured
show snmp host                          # Trap destinations
```

---

## 18. VPN & Tunnel Debugging

### IPsec VPN

**Concept:** IPsec creates an encrypted tunnel between two endpoints. It has two phases: Phase 1 (authenticate and create secure channel) and Phase 2 (create the actual tunnel for data).

```
IPsec IKE Phases:
=================

PHASE 1 (IKE SA / ISAKMP SA):
  Goal: Authenticate peers, establish secure channel for Phase 2
  Exchange: Encryption algo, hash, authentication method, DH group
  Result: IKE SA (Security Association)
  
  State: MM_NO_STATE → MM_SA_SETUP → MM_KEY_EXCH → MM_KEY_AUTH → QM_IDLE (ready)

PHASE 2 (IPsec SA / Quick Mode):
  Goal: Negotiate encryption for actual data tunnel
  Exchange: IPsec encryption algo, hash, lifetime, PFS
  Result: Two unidirectional SAs (one each direction)
  
Common Issues:
  Phase 1 fails: Mismatched crypto proposals, authentication failure, NAT-T needed
  Phase 2 fails: Mismatched proxy IDs (interesting traffic), PFS mismatch
  Tunnel up but no traffic: Routing to tunnel missing, ACL blocking, proxy ID too narrow
```

```bash
# Cisco IPsec debugging
show crypto isa sa                      # IKE Phase 1 SAs
show crypto ipsec sa                    # Phase 2 SAs (with packet counters)
show crypto map                         # Crypto map configuration
debug crypto isakmp                     # Phase 1 negotiations
debug crypto ipsec                      # Phase 2 negotiations

# Key things to check in show crypto ipsec sa:
# #pkts encaps: 12345    ← Packets entering tunnel
# #pkts encrypt: 12345   ← Must equal encaps
# #pkts decaps: 12345    ← Packets from remote end
# #pkts decrypt: 12345   ← Must equal decaps
# #pkts no sa (send): 0  ← Non-zero = traffic not matching crypto ACL
# inbound/outbound errors → Mismatched keys or transforms

# Linux strongSwan/IKEv2
ipsec statusall                         # Full VPN status
ipsec status                            # Summary
journalctl -u strongswan -f             # Live logs
```

### WireGuard VPN

```bash
wg show                                 # All WireGuard interfaces and peers
wg showconf wg0                         # Configuration of wg0
ip link show wg0                        # Interface state
ping 10.0.0.1                           # Ping VPN peer

# Check if packets are flowing
wg show wg0 | grep "latest handshake"   # When was last handshake? (should be recent)
wg show wg0 | grep "transfer"           # Bytes sent/received (should be increasing)

# Common issues:
# Latest handshake: never → Keys not matching, firewall blocking UDP port
# Transfer: 0 bytes received → Route to peer missing or firewall blocking
```

---

## 19. Wireless/WiFi Router Debugging

### WiFi Fundamentals

```
WiFi Frequency Bands:
=====================
2.4 GHz: Channels 1-14 (overlapping — only 1, 6, 11 are non-overlapping)
          Range: Long (penetrates walls well)
          Speed: Lower (up to 600 Mbps for 802.11n)
          Interference: More crowded (microwaves, Bluetooth, neighbors)

5 GHz:   Channels 36-165 (many non-overlapping channels)
          Range: Shorter (absorbed by walls)
          Speed: Higher (up to 9.6 Gbps for 802.11ax/WiFi6)
          Interference: Less crowded

6 GHz:   New with WiFi 6E/WiFi 7
          Cleanest spectrum, shortest range
```

```bash
# Linux WiFi debugging
iwconfig                               # WiFi interface details (older)
iw dev                                 # List WiFi devices (modern)
iw dev wlan0 info                      # Interface info
iw dev wlan0 link                      # Current connection details
iw dev wlan0 station dump              # Connected clients (if AP mode)
iw dev wlan0 survey dump               # Channel survey (noise levels)

# Scan for networks
iw dev wlan0 scan                      # Scan all WiFi networks
nmcli device wifi list                 # NetworkManager scan

# Check signal strength
watch -n 1 'iw dev wlan0 link | grep signal'  # Real-time signal level
iwconfig wlan0 | grep -i quality       # Link quality and signal

# Check for channel interference
iw dev wlan0 scan | grep -E "SSID|freq|signal"   # See all networks and their channels

# hostapd (if router is running as AP)
hostapd_cli status                     # AP status
hostapd_cli all_sta                    # All connected stations

# Signal strength interpretation:
# -30 dBm = Amazing (max signal)
# -50 dBm = Excellent
# -60 dBm = Good
# -70 dBm = Fair (minimum for most applications)
# -80 dBm = Poor (unreliable)
# -90 dBm = Unusable
```

### WiFi Channel Analysis

```bash
# Find crowded channels
iw dev wlan0 scan | grep freq | sort | uniq -c | sort -rn
# High count on one frequency = crowded channel

# Use iwlist for older kernels
iwlist wlan0 scanning | grep -E "Channel|Signal|SSID"
```

---

## 20. Common Failure Patterns & Decision Trees

### Decision Tree 1: "No Internet Access"

```
[No Internet Access]
        |
        v
Can you ping your default gateway (e.g., 192.168.1.1)?
        |
   NO---+---YES
   |            |
   v            v
Is cable    Can you ping an external IP (e.g., 8.8.8.8)?
plugged in?     |
   |       NO---+---YES
   |       |            |
   |       v            v
   |   Is NAT       Can you resolve DNS
   |   configured?  (nslookup google.com)?
   |       |             |
   |  NO---+---YES  NO---+---YES
   |  |        |    |        |
   |  v        v    v        v
   | Configure Check   Fix DNS  Check application
   | NAT       ISP    settings  layer (port 443
   | rules     link   (/etc/   open? proxy? etc.)
   |                  resolv.conf)
   |
   v
Is interface UP?
   |
   NO → Check cable, speed/duplex settings
   YES → Check IP address configuration
         Check ARP for gateway
         Check default route: ip route show
```

### Decision Tree 2: "Intermittent Connectivity"

```
[Intermittent Connectivity]
        |
        v
Is it time-based (same time of day)?
        |
  YES---+---NO
  |          |
  v          v
Likely QoS/ Is it correlated with traffic volume?
cron jobs/      |
scheduled    YES+---NO
tasks         |      |
              v      v
           Bandwidth  Run mtr continuously:
           saturation  mtr --report-wide 8.8.8.8
           (check      Look for packet loss
           iperf3)     at specific hops
                       |
              Loss at intermediate hops only?
                       |
               YES-----+-----NO
               |               |
               v               v
           Likely ICMP     Real loss —
           deprioritize    check physical
           at that router  layer, duplex,
           (usually OK)    cable quality
```

### Decision Tree 3: "Slow Network"

```
[Slow Network]
        |
        v
Is it slow to all destinations or just one?
        |
ONE-----+-----ALL
 |              |
 v              v
Problem at    Is it slow from all devices or just one?
that specific     |
destination    ONE+---ALL
or path         |      |
                v      v
           Device-   Check ISP connection
           specific  (iperf3 to speedtest server)
           issue      |
           (NIC,  Fast+---Slow
           driver, |        |
           TCP     v        v
           tuning) Local   ISP issue
                   network (call ISP,
                   issue   check ONT/modem)
                   (check
                   switch
                   ports)
```

---

## 21. Systematic Troubleshooting Checklists

### Quick 5-Minute Router Health Check

```
PHYSICAL & INTERFACE LAYER
[ ] All expected interfaces show: up/up
[ ] No CRC errors, input errors, or output drops
[ ] No duplex mismatches
[ ] CPU utilization < 70% (show processes cpu)
[ ] Memory utilization < 80% (show processes memory)

ROUTING LAYER
[ ] Default route present in routing table
[ ] All expected prefixes present
[ ] No routes missing that should be there
[ ] Routing protocol neighbors all in expected state (FULL/ESTABLISHED)

CONNECTIVITY TESTS
[ ] Can ping all directly connected interfaces
[ ] Can ping default gateway
[ ] Can ping external IP (8.8.8.8)
[ ] DNS resolution works (nslookup google.com)
[ ] Key applications accessible

LOGS
[ ] No recent interface flaps in logs
[ ] No authentication failures
[ ] No routing protocol neighbor state changes
[ ] No ACL drops for expected traffic
```

### Pre-Change Checklist (Before Making Changes)

```
[ ] Document current state (show running-config, show ip route)
[ ] Take baseline ping/traceroute results
[ ] Identify rollback procedure
[ ] Notify affected users
[ ] Have console access ready (not just SSH — you might lose connectivity)
[ ] Schedule maintenance window if production
[ ] Test changes on lab/staging first
```

### Post-Change Validation Checklist

```
[ ] Interfaces still up/up
[ ] Routing table has all expected routes
[ ] Can ping all critical hosts
[ ] Applications functioning correctly
[ ] No error spikes in interface counters
[ ] Logs clean (no new errors)
[ ] Performance baseline matches pre-change
[ ] Routing protocol neighbors re-established
```

---

## 22. Mental Models for Network Mastery

### Model 1: The "Plumbing" Model

Think of a network as plumbing. IP addresses are addresses on houses, packets are water droplets, routers are water valves/junctions, and firewalls are water shutoffs. When water doesn't flow from A to B, you trace the pipe: is the source flowing? Is there a closed valve? Is there a broken pipe (physical layer)? Is the destination drain open (port listening)?

### Model 2: The "Letter Mail" Model

A packet is like a letter. The IP header is the envelope with destination and return address. The router is the sorting center — it reads the destination and forwards to the next sorting center. TTL is like a "return if not delivered in X days" instruction. NAT is like a PO Box — many letters go out from one address and are redistributed internally.

### Model 3: Layers as Onions

Each OSI layer wraps the one above it. When a packet is sent:
- Application data → wrapped in TCP/UDP (Layer 4 header added)
- TCP/UDP → wrapped in IP packet (Layer 3 header with src/dst IP)
- IP packet → wrapped in Ethernet frame (Layer 2 header with src/dst MAC)
- Ethernet frame → converted to electrical signals (Layer 1 — physical)

At each router, Layer 1/2 is stripped, Layer 3 is read, then new Layer 1/2 headers are added for the next hop.

### Model 4: The "Two-Phase" Mental Check

For any networking problem, always ask two questions:
1. **"Can I reach the next hop?"** (Local/Layer 2-3 question)
2. **"Can the next hop reach the destination?"** (End-to-end/routing question)

Answering question 1 first narrows the problem to local vs. remote.

### The Expert Habit: Keep Baselines

Before problems happen, know what "normal" looks like:
- Save output of `show interfaces` weekly
- Track interface error counters over time
- Know your normal CPU/memory utilization
- Know your normal bandwidth utilization
- Know your normal routing table size

When a problem occurs, **compare to baseline** — the delta tells you everything.

### Cognitive Principle: Deliberate Practice

Each troubleshooting session is a deliberate practice opportunity. After resolving each issue:
1. **Write a post-mortem**: What was the root cause? What led you astray? What would you do faster next time?
2. **Build your pattern library**: File each problem in your mental "case book" — symptoms → root cause → fix
3. **Simulate problems**: Set up lab environments and intentionally break things, then fix them. Break → debug → fix → repeat is the fastest path to expertise.

---

## Quick Reference Card

```
TOOL          | PURPOSE                           | KEY FLAGS
--------------+-----------------------------------+------------------------
ping          | Basic reachability + latency      | -c -s -M do (MTU)
traceroute    | Path + per-hop latency            | -I (ICMP), -T (TCP)
mtr           | Continuous traceroute + loss      | --report --tcp
tcpdump       | Raw packet capture                | -i -nn -w host/port
ss            | Socket & connection state         | -tunap -s
ip route      | Routing table                     | show, get, add, del
ip addr       | Interface IPs                     | show, add, del
ip neigh      | ARP table                         | show, flush
arp           | ARP table (older)                 | -n -d
dig           | DNS deep debugging                | @server, +trace, +short
nmap          | Host/port discovery               | -sn -sS -sU -sV
nc            | TCP/UDP port connectivity test    | -zv (test), -l (listen)
iperf3        | Bandwidth measurement             | -s (server), -c (client)
ethtool       | Physical layer info               | ethX
conntrack     | NAT/connection tracking           | -L -C -E
curl          | HTTP layer testing                | -v -o /dev/null -w
```

---

*"The network never lies — it only speaks in packets. Learn its language, and no problem will remain mysterious for long."*

---

**Document Version:** 1.0 | **Coverage:** Layer 1 through Layer 7 | **Focus:** Router & Network Debugging

Here is your complete, comprehensive guide — **22 sections** covering the entire spectrum of network router debugging, from the physical cable to the application layer.

---

### What's Inside

The guide is structured like a **mentor teaching you to think**, not just to run commands. Here's the arc:

**Foundation First** — Sections 1–4 build your mental model before touching any tool. The OSI layer framework is your permanent debugging compass. Without it, tool usage is just random button pressing.

**Layer-by-Layer Mastery** — Sections 5–11 methodically walk you through Physical → Data Link → Network → Transport → Application. Every layer has its own failure modes, its own tools, and its own language.

**Beyond Ping & Traceroute** — Section 9 introduces the tools experts actually use daily: `mtr` (best latency analysis), `ss` (socket states), `tcpdump` (packet truth), `nmap` (network reconnaissance), `iperf3` (bandwidth ground truth), and `netcat` (the port-testing multi-tool).

**Deep Protocol Debugging** — Sections 10–18 cover OSPF, BGP, NAT, DHCP, DNS, VPN, QoS, and packet capture — each with internal mechanics explained before commands.

**Decision Trees** — Section 20 gives you three branching logic flows for the most common failure scenarios so you develop the expert habit of *bisecting* problems instead of guessing.

---

### The Core Mental Leap

Every expert network engineer operates by one rule: **the network tells the truth — your assumptions lie**. Run the commands. Read the output. Let the evidence build the hypothesis, not the other way around. That discipline separates the top 1% from the rest.