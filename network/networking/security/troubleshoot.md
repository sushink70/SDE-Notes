# 🛡️ Complete Guide: Debugging & Troubleshooting Network Security Devices

> *"The expert debugger does not panic. They observe, hypothesize, test, and conclude — like a scientist in calm pursuit of truth."*

---

## Table of Contents

1. [Mental Model: The OSI Ladder](#1-mental-model-the-osi-ladder)
2. [The Debugging Philosophy](#2-the-debugging-philosophy)
3. [Foundational Concepts You Must Know First](#3-foundational-concepts-you-must-know-first)
4. [The Master Troubleshooting Framework](#4-the-master-troubleshooting-framework)
5. [Layer 1 — Physical & Link Layer Tools](#5-layer-1--physical--link-layer-tools)
6. [Layer 2 — ARP, MAC, Switching](#6-layer-2--arp-mac-switching)
7. [Layer 3 — IP Routing & Path Analysis](#7-layer-3--ip-routing--path-analysis)
8. [Layer 4 — TCP/UDP Port & Connection Tools](#8-layer-4--tcpudp-port--connection-tools)
9. [Layer 7 — Application Layer Tools](#9-layer-7--application-layer-tools)
10. [Packet Capture & Deep Inspection](#10-packet-capture--deep-inspection)
11. [Firewall Debugging](#11-firewall-debugging)
12. [DNS Debugging](#12-dns-debugging)
13. [TLS/SSL & Certificate Debugging](#13-tlsssl--certificate-debugging)
14. [VPN Debugging](#14-vpn-debugging)
15. [IDS/IPS Debugging](#15-idsips-debugging)
16. [Bandwidth & Performance Testing](#16-bandwidth--performance-testing)
17. [SNMP & Network Monitoring](#17-snmp--network-monitoring)
18. [Log Analysis & Syslog](#18-log-analysis--syslog)
19. [Decision Trees for Common Problems](#19-decision-trees-for-common-problems)
20. [Advanced Mental Models for Expert Debugging](#20-advanced-mental-models-for-expert-debugging)

---

## 1. Mental Model: The OSI Ladder

Before touching a single tool, understand **where** in the network stack your problem lives.

The **OSI Model** (Open Systems Interconnection) is a 7-layer conceptual framework that describes how data moves from one device to another across a network.

Think of it like postal mail:
- Layer 7 = The message content (Application)
- Layer 4 = The envelope with address (Transport)
- Layer 3 = The postal routing system (Network)
- Layer 2 = The local delivery van (Data Link)
- Layer 1 = The road itself (Physical)

```
+--------------------------------------------------+
|   OSI MODEL — THE NETWORK STACK                  |
|                                                  |
|  Layer 7  ██████████  APPLICATION   HTTP,FTP,SSH |
|  Layer 6  ██████████  PRESENTATION  TLS,SSL,Enc  |
|  Layer 5  ██████████  SESSION       Sessions,RPC |
|  Layer 4  ██████████  TRANSPORT     TCP, UDP     |
|  Layer 3  ██████████  NETWORK       IP, ICMP     |
|  Layer 2  ██████████  DATA LINK     ARP, MAC     |
|  Layer 1  ██████████  PHYSICAL      Cables,NIC   |
+--------------------------------------------------+

  DEBUGGING DIRECTION:
  Bottom-Up: Start at Physical, move up
  
  [Physical] → [Link] → [Network] → [Transport] → [Application]
       ↑            ↑         ↑            ↑              ↑
   cables?      ARP ok?   routing?     ports?        app error?
```

**Why this matters:** Every tool you use targets a specific layer. Using a Layer 7 tool (curl) to debug a Layer 3 problem (IP routing) wastes time. Always identify the layer first.

---

## 2. The Debugging Philosophy

### The Scientific Method Applied to Networks

```
+--------------------------------------------------------+
|           THE EXPERT DEBUGGING CYCLE                   |
|                                                        |
|   OBSERVE          HYPOTHESIZE        TEST             |
|  [Symptoms]  -->  [What layer?]  -->  [Tool/Check] --> |
|      ^                                     |           |
|      |           CONCLUDE                  |           |
|      +---------- [Fix or next hypothesis]<-+           |
+--------------------------------------------------------+
```

**Three Cardinal Rules:**
1. **Change one thing at a time** — otherwise you cannot isolate the cause
2. **Document everything** — write what you changed and when
3. **Verify after every fix** — confirm the fix before moving on

---

## 3. Foundational Concepts You Must Know First

### 3.1 What is a Packet?

A **packet** is a small unit of data transmitted over a network. Large messages are broken into packets, sent independently, and reassembled at the destination.

```
  ORIGINAL DATA: "Hello, World!"
  
  +----------------+    Broken into    +--------+ +--------+
  | Hello, World!  | ===============>  | Pkt #1 | | Pkt #2 |
  +----------------+                   +--------+ +--------+
  
  Each packet has:
  +---------------------------------+
  | HEADER | PAYLOAD | TRAILER      |
  |  (IP,  | (data)  | (checksum)   |
  |  TCP)  |         |              |
  +---------------------------------+
```

### 3.2 What is a Port?

A **port** is a numbered endpoint on a device that identifies a specific service or process. Like an apartment number in a building (the building = IP address, apartment = port).

```
  YOUR COMPUTER (192.168.1.5)
  +-----------------------------+
  | Port 22  → SSH service      |
  | Port 80  → HTTP service     |
  | Port 443 → HTTPS service    |
  | Port 3306→ MySQL service    |
  +-----------------------------+
  
  Incoming traffic → IP routes to building → Port routes to apartment
```

**Well-known ports:** 0–1023 (reserved, needs root)
**Registered ports:** 1024–49151
**Ephemeral/Dynamic:** 49152–65535 (client-side temporary)

### 3.3 What is a Socket?

A **socket** = IP address + Port + Protocol. It is the unique endpoint of a network connection.

```
  Socket example:  192.168.1.5:443/TCP
                   └─────────┘ └─┘ └──┘
                    IP Address  Port Protocol
```

### 3.4 What is a Firewall?

A **firewall** is a security device (hardware or software) that monitors and controls incoming/outgoing traffic based on rules (called **ACLs** — Access Control Lists).

```
  INTERNET ──── [FIREWALL] ──── INTERNAL NETWORK
                    │
               RULE ENGINE:
               ┌────────────────────────────────┐
               │ ALLOW TCP 443 from ANY to WEB  │
               │ ALLOW TCP 22 from 10.0.0.0/8   │
               │ DENY ALL others                │
               └────────────────────────────────┘
```

### 3.5 What is a Subnet / CIDR?

A **subnet** is a logical subdivision of an IP network. **CIDR** (Classless Inter-Domain Routing) notation expresses it as `IP/prefix`.

```
  192.168.1.0/24
  └──────────┘└─┘
   Network       Prefix length (24 bits = 256 addresses)
   
  /24 → 256 addresses (192.168.1.0 to 192.168.1.255)
  /16 → 65536 addresses
  /32 → 1 address (a single host)
  /0  → ALL addresses (the entire internet)
```

### 3.6 What is MTU?

**MTU** (Maximum Transmission Unit) is the largest packet size a network link can carry without fragmentation, typically **1500 bytes** on Ethernet.

If a packet is larger than the MTU, it must be **fragmented** (split). This can cause performance issues or silent drops in some security configurations.

### 3.7 What is TTL?

**TTL** (Time To Live) is a counter in each IP packet. Every router that forwards a packet decrements TTL by 1. When TTL reaches 0, the packet is discarded and an ICMP "Time Exceeded" message is sent back. This prevents packets from looping forever.

```
  SOURCE ──[TTL=64]──> Router1 ──[TTL=63]──> Router2 ──[TTL=62]──> ...
                                                        
  If TTL reaches 0: Router sends "ICMP Time Exceeded" back to source
  This is how traceroute works!
```

### 3.8 What is ICMP?

**ICMP** (Internet Control Message Protocol) is a Layer 3 protocol used for network diagnostics. It carries error messages and operational information. Ping uses ICMP Echo Request/Reply.

```
  Types of ICMP messages:
  Type 0  = Echo Reply          (ping response)
  Type 3  = Destination Unreachable
  Type 8  = Echo Request        (ping)
  Type 11 = Time Exceeded       (TTL expired, used by traceroute)
  Type 13 = Timestamp Request
```

---

## 4. The Master Troubleshooting Framework

### The OSI Bottom-Up Approach

```
  START HERE (when network is broken)
       │
       ▼
+──────────────────────────────────────────────────────────────+
│  STEP 1: PHYSICAL LAYER (Layer 1)                            │
│  Q: Is the cable/NIC/interface physically up?                │
│  Tools: ip link, ethtool, dmesg                              │
│  If YES → continue ↓   If NO → Fix cable/driver             │
+──────────────────────────────────────────────────────────────+
       │
       ▼
+──────────────────────────────────────────────────────────────+
│  STEP 2: DATA LINK (Layer 2)                                 │
│  Q: Can we reach the next-hop MAC address?                   │
│  Tools: arp, ip neigh, arping                                │
│  If YES → continue ↓   If NO → Switch/VLAN issue            │
+──────────────────────────────────────────────────────────────+
       │
       ▼
+──────────────────────────────────────────────────────────────+
│  STEP 3: NETWORK (Layer 3)                                   │
│  Q: Can we reach the remote IP? Is routing correct?          │
│  Tools: ping, ip route, mtr, traceroute                      │
│  If YES → continue ↓   If NO → Routing/Firewall/ACL         │
+──────────────────────────────────────────────────────────────+
       │
       ▼
+──────────────────────────────────────────────────────────────+
│  STEP 4: TRANSPORT (Layer 4)                                 │
│  Q: Is the specific port reachable? Any TCP reset?           │
│  Tools: nc, telnet, nmap, ss, netstat                        │
│  If YES → continue ↓   If NO → Firewall blocking port       │
+──────────────────────────────────────────────────────────────+
       │
       ▼
+──────────────────────────────────────────────────────────────+
│  STEP 5: APPLICATION (Layer 7)                               │
│  Q: Is the service responding correctly?                     │
│  Tools: curl, openssl s_client, dig, nslookup               │
│  If YES → DONE   If NO → App config/cert/DNS issue           │
+──────────────────────────────────────────────────────────────+
```

---

## 5. Layer 1 — Physical & Link Layer Tools

### 5.1 `ip link` — Interface Status

**What it does:** Shows all network interfaces and their physical/link state.

```bash
ip link show
ip link show eth0
```

**Sample Output:**
```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
```

**Decode the flags:**
```
  <BROADCAST>  = Supports broadcast
  <MULTICAST>  = Supports multicast
  <UP>         = Interface is administratively enabled
  <LOWER_UP>   = Physical link is up (cable connected, signal detected)
  
  If you see <UP> but NOT <LOWER_UP> → cable is unplugged or bad
  If you don't see <UP> at all → interface is disabled (bring it up with ip link set eth0 up)
```

**Bring interface up/down:**
```bash
ip link set eth0 up
ip link set eth0 down
```

### 5.2 `ethtool` — NIC Deep Inspection

**What it does:** Shows hardware-level details of a NIC — speed, duplex, auto-negotiation.

**Concept — Duplex:** 
- **Half-duplex:** Can send OR receive, not both simultaneously (like a walkie-talkie)
- **Full-duplex:** Can send AND receive simultaneously (like a phone call)
- A mismatch (one side full, other half) causes severe packet loss and collisions!

```bash
ethtool eth0
```

**Sample Output:**
```
Settings for eth0:
   Speed: 1000Mb/s
   Duplex: Full
   Auto-negotiation: on
   Link detected: yes
```

**Diagnostics:**
```bash
ethtool -S eth0    # NIC statistics (errors, drops, missed packets)
ethtool -k eth0    # Offload features (TSO, GRO, etc.)
ethtool -i eth0    # Driver and firmware version
```

**Error counter analysis:**
```
  rx_errors   > 0 → Receiving bad frames (bad cable, EMI noise)
  tx_errors   > 0 → Transmission errors
  rx_dropped  > 0 → Kernel buffer overflow (system too busy)
  collisions  > 0 → Duplex mismatch or overloaded shared medium
```

### 5.3 `dmesg` — Kernel Messages

**What it does:** Shows kernel ring buffer messages — including NIC driver events, link state changes.

```bash
dmesg | grep -i "eth0\|link\|nic\|network"
dmesg --follow    # Live stream of kernel messages
```

**What to look for:**
```
  [  5.123456] eth0: NIC Link is Up 1000 Mbps Full Duplex    ← GOOD
  [ 42.000000] eth0: NIC Link is Down                        ← BAD: cable/switch issue
  [ 99.000000] eth0: reset adapter                           ← Driver/hardware problem
```

---

## 6. Layer 2 — ARP, MAC, Switching

### 6.1 What is ARP?

**ARP** (Address Resolution Protocol) resolves IP addresses to MAC addresses. Before sending a packet to `192.168.1.1`, your computer asks "Who has 192.168.1.1? Tell me your MAC address!" — this is an ARP broadcast.

```
  YOUR PC                              ROUTER (192.168.1.1)
  192.168.1.5                          MAC: AA:BB:CC:DD:EE:FF
      │                                         │
      │ ARP REQUEST (broadcast):                │
      │ "Who has 192.168.1.1?"                  │
      │─────────────────────────────────────────▶
      │                                         │
      │ ARP REPLY (unicast):                    │
      │ "I have it! My MAC is AA:BB:CC:DD:EE:FF"│
      ◀─────────────────────────────────────────│
      │                                         │
      │ Now PC stores this in ARP CACHE         │
      │ and sends future packets directly       │
```

### 6.2 `arp` and `ip neigh` — ARP Cache

```bash
arp -n              # Show ARP cache (no DNS lookup)
ip neigh show       # Modern equivalent (preferred)
ip neigh show dev eth0
```

**Sample Output:**
```
192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
192.168.1.100 dev eth0 lladdr 11:22:33:44:55:66 STALE
192.168.1.200 dev eth0  FAILED
```

**ARP entry states:**
```
  REACHABLE  = Recently verified, actively communicating
  STALE      = Not recently verified, but cached (will re-verify on use)
  FAILED     = ARP request sent, no reply (host unreachable at L2)
  INCOMPLETE = ARP request sent, waiting for reply
  PERMANENT  = Static entry (set manually)
  
  FAILED → host is down, wrong VLAN, or MAC filtering
```

**Add a static ARP entry:**
```bash
ip neigh add 192.168.1.99 lladdr 00:11:22:33:44:55 dev eth0
```

**Clear ARP cache:**
```bash
ip neigh flush dev eth0
```

### 6.3 `arping` — ARP-Level Ping

**What it does:** Sends ARP requests and waits for ARP replies. Unlike ping (ICMP), it works even if ICMP is blocked by a firewall. Proves Layer 2 connectivity.

```bash
arping -I eth0 192.168.1.1
arping -I eth0 -c 4 192.168.1.1    # Send 4 ARP requests
```

**Flow:**
```
  arping ──ARP Broadcast──> network ──ARP Reply──> arping prints MAC + RTT
  
  If no reply: L2 issue (VLAN, switch port, MAC filtering)
  If ICMP ping fails but arping succeeds: Firewall blocking ICMP at L3
```

### 6.4 `bridge` — Switch/Bridge Table

On Linux bridges or network switches with CLI access:

```bash
bridge fdb show         # Forwarding Database (MAC table)
bridge link show        # Bridge port states
```

**Concept — MAC Table (Forwarding Database):**
A switch learns which MAC address is reachable through which port. If a MAC is missing, it floods the frame to all ports. A corrupted/stale MAC table causes traffic to go to the wrong port.

```
  SWITCH MAC TABLE:
  +──────────────────────────────────────────+
  │ MAC Address         Port    Age (secs)   │
  │ AA:BB:CC:DD:EE:FF   eth1    5            │
  │ 11:22:33:44:55:66   eth3    120          │
  │ 00:FF:EE:DD:CC:BB   eth2    300          │
  +──────────────────────────────────────────+
```

---

## 7. Layer 3 — IP Routing & Path Analysis

### 7.1 `ip addr` — IP Address Configuration

```bash
ip addr show
ip addr show eth0
ip addr show dev eth0
```

**Sample Output:**
```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.1.5/24 brd 192.168.1.255 scope global eth0
    inet6 fe80::211:22ff:fe33:4455/64 scope link
```

**What to verify:**
```
  Correct IP assigned?
  Correct subnet mask (/24, /16 etc)?
  No IP conflict with another device?
  IPv6 link-local (fe80::/10) present? → interface working at L2
```

### 7.2 `ip route` — Routing Table

**Concept — Routing Table:** A list of rules that tells the OS where to send packets for different destination networks. A **default route** (0.0.0.0/0) is the "if nothing else matches, send here" rule — typically pointing to your gateway/router.

```bash
ip route show
ip route get 8.8.8.8    # Which route would be used to reach 8.8.8.8?
```

**Sample Output:**
```
default via 192.168.1.1 dev eth0 proto dhcp metric 100
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.5
10.0.0.0/8 via 10.10.0.1 dev tun0
```

**Decode:**
```
  default via 192.168.1.1  → Gateway (default route)
  192.168.1.0/24 dev eth0  → Local network, reachable directly
  10.0.0.0/8 via 10.10.0.1 → VPN tunnel route
  
  ip route get 8.8.8.8 shows:
  8.8.8.8 via 192.168.1.1 dev eth0 src 192.168.1.5
  ← This is the exact path the OS will use for 8.8.8.8
```

**Add/delete routes:**
```bash
ip route add 10.0.0.0/8 via 192.168.1.254 dev eth0
ip route del 10.0.0.0/8
ip route add default via 192.168.1.1    # Set default gateway
```

### 7.3 `mtr` — My TraceRoute (Superior to traceroute)

**What it is:** MTR combines ping + traceroute into a real-time continuous monitor. It shows every hop to a destination, with packet loss and latency statistics per hop — continuously updated.

**Concept — Hops:** Each router a packet passes through is called a "hop." Traceroute/MTR reveals each hop by exploiting TTL.

```bash
mtr google.com
mtr --report --report-cycles 100 google.com    # 100 packet report
mtr -n google.com                               # No DNS (show IPs only)
mtr --tcp --port 443 google.com                 # TCP mode (bypass ICMP blocks)
mtr --udp google.com                            # UDP mode
```

**Sample MTR Output:**
```
                     My TraceRoute
HOST: mypc                      Loss%   Snt   Last   Avg  Best  Wrst StDev
 1. 192.168.1.1                  0.0%   100    1.2   1.3   1.0   2.1   0.3
 2. 10.0.0.1                     0.0%   100    5.4   5.2   4.8   6.1   0.4
 3. 72.14.215.165                 0.0%   100   10.1  10.3   9.8  12.0   0.5
 4. 8.8.8.8                       0.0%   100   11.0  11.1  10.5  13.0   0.6
```

**Interpret packet loss:**
```
  Loss% at hop N, but 0% at hop N+1?
  → That router deprioritizes ICMP (not a real problem)
  
  Loss% at hop N AND all subsequent hops?
  → REAL packet loss at hop N (congestion, bad link, firewall)
  
  Loss% only at the last hop?
  → Destination host filtering ICMP, but TCP/UDP might still work
```

**MTR Visualization:**
```
  Source ──0%──> Hop1 ──0%──> Hop2 ──30%──> Hop3 ──30%──> Dest
                                  ↑
                          PROBLEM IS HERE
                          (30% loss starts at Hop2)
```

### 7.4 `traceroute` / `tracepath` — Path Discovery

**How traceroute works (mechanism):**
```
  1. Send packet with TTL=1 → First router decrements to 0, sends ICMP "Time Exceeded"
     → We learn the IP of Hop 1
  
  2. Send packet with TTL=2 → Second router decrements to 0, sends ICMP "Time Exceeded"
     → We learn the IP of Hop 2
  
  ... repeat until we reach destination (which sends ICMP "Port Unreachable" or Echo Reply)
```

```bash
traceroute google.com                    # Default (UDP mode on Linux)
traceroute -I google.com                 # ICMP mode (like Windows tracert)
traceroute -T -p 443 google.com          # TCP mode on port 443 (bypasses firewall)
traceroute -n google.com                 # No DNS resolution (faster)
tracepath google.com                     # Also discovers MTU along the path
```

**Interpret output:**
```
  traceroute to google.com, 30 hops max
   1  192.168.1.1       1.234 ms   1.212 ms   1.198 ms   ← Your gateway
   2  10.0.0.1          5.432 ms   5.301 ms   5.289 ms   ← ISP router
   3  * * *                                               ← Hop filtered (normal)
   4  72.14.215.165    10.102 ms  10.085 ms  10.091 ms
   5  8.8.8.8          11.203 ms  11.100 ms  11.150 ms   ← Destination reached!
   
   * * * = Router does not respond to ICMP/UDP (firewall), 
           but traffic PASSES THROUGH (not a problem unless all subsequent hops also *)
```

---

## 8. Layer 4 — TCP/UDP Port & Connection Tools

### 8.1 `ss` — Socket Statistics (Modern netstat)

**Concept — Socket States:**
- `LISTEN` = Service waiting for connections
- `ESTABLISHED` = Active connection
- `TIME_WAIT` = Connection closed, waiting for late packets
- `CLOSE_WAIT` = Remote closed, local hasn't yet
- `SYN_SENT` = Connecting...
- `SYN_RECV` = Received SYN, waiting for ACK

```bash
ss -tlnp          # TCP (-t) listening (-l) no-DNS (-n) with process (-p)
ss -ulnp          # UDP listening ports
ss -anp           # All sockets with process info
ss -s             # Summary statistics
ss -tp            # TCP connections with process
ss state ESTABLISHED  # Only established connections
```

**Sample Output:**
```
State    Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN   0       128     0.0.0.0:22          0.0.0.0:*          sshd
LISTEN   0       511     0.0.0.0:80          0.0.0.0:*          nginx
ESTAB    0       0       192.168.1.5:22      10.0.0.5:54321     sshd

  Recv-Q > 0 on LISTEN socket → backlog full, service overwhelmed
  Send-Q > 0 on ESTAB socket  → network congestion or slow receiver
```

**Filter connections:**
```bash
ss -tnp dst 8.8.8.8         # Connections TO 8.8.8.8
ss -tnp sport :443          # Connections FROM port 443
ss -tnp dport :80           # Connections TO port 80
```

### 8.2 `netstat` — Legacy (but still widely available)

```bash
netstat -tlnp         # TCP listening ports with process
netstat -an           # All connections
netstat -rn           # Routing table
netstat -s            # Protocol statistics
netstat -i            # Interface statistics
```

### 8.3 `nc` (netcat) — The Swiss Army Knife

**What it does:** Reads and writes data across TCP/UDP connections. Used for port testing, banner grabbing, file transfer, port scanning.

**Concept — Banner:** When a service starts a TCP connection, it often sends a greeting message called a "banner" (e.g., SSH version, FTP welcome). This reveals service type and version.

```bash
# Test if port is open (TCP connect test)
nc -zv 192.168.1.1 22
nc -zv 192.168.1.1 80

# Test UDP port
nc -zuv 192.168.1.1 53

# Grab banner (connect and see what service says)
nc 192.168.1.1 22
nc 192.168.1.1 21

# Listen on a port (create a simple server for testing)
nc -lvnp 9999

# Send data / test firewall rules
echo "test" | nc 192.168.1.1 9999

# Port scan range
nc -zv 192.168.1.1 20-100
```

**Output interpretation:**
```
  nc -zv 192.168.1.1 22
  Connection to 192.168.1.1 22 port [tcp/ssh] succeeded!  → Port OPEN
  
  nc: connect to 192.168.1.1 port 80 (tcp) failed: Connection refused  → Port CLOSED (host up, no service)
  nc: connect to 192.168.1.1 port 443 (tcp) failed: No route to host   → Firewall DROP (host unreachable)
  
  "Connection refused" = Host is UP, firewall says REJECT (sends TCP RST)
  "No route to host"   = Firewall says DROP (silent discard, timeout)
```

**The Firewall Response Difference:**
```
  ALLOW:   SYN ──────────────────> SYN+ACK (connection established)
  REJECT:  SYN ──────────────────> RST     (immediate refusal, fast)
  DROP:    SYN ──────────────────> (silence, waits for timeout)
  
  DROP is harder to detect than REJECT — it causes long timeouts
```

### 8.4 `nmap` — Network Mapper (Industry Standard)

**What it does:** Comprehensive port scanner, OS detection, service version detection, and vulnerability scanning via scripts.

**Concept — Scan Types:**
- **SYN scan (-sS):** Sends SYN, gets SYN+ACK (open) or RST (closed). Never completes handshake. Stealthy.
- **Connect scan (-sT):** Full TCP handshake. Logged by the target. Less stealthy.
- **UDP scan (-sU):** Probes UDP ports. Slow because UDP has no handshake.
- **Null/FIN/Xmas scans:** Bypass some firewalls by sending unusual flag combinations.

```bash
# Basic scan (top 1000 ports)
nmap 192.168.1.1

# Scan specific ports
nmap -p 22,80,443 192.168.1.1

# Scan all 65535 ports
nmap -p- 192.168.1.1

# Service version detection
nmap -sV 192.168.1.1

# OS detection (requires root)
nmap -O 192.168.1.1

# Aggressive scan (OS + version + scripts + traceroute)
nmap -A 192.168.1.1

# UDP scan
nmap -sU 192.168.1.1

# Scan entire subnet
nmap 192.168.1.0/24

# Scan without ping (skip host discovery)
nmap -Pn 192.168.1.1

# Stealth SYN scan
nmap -sS 192.168.1.1

# NSE script: check for vulnerabilities
nmap --script vuln 192.168.1.1

# Check if port is firewalled vs closed
nmap -sA 192.168.1.1    # ACK scan (reveals firewall rules)

# Firewall evasion - fragment packets
nmap -f 192.168.1.1

# Timing (-T0 slowest/stealthy, -T5 fastest/aggressive)
nmap -T2 192.168.1.1
```

**Nmap port states:**
```
  open         = Service actively accepting connections
  closed       = Port accessible, no service listening (RST received)
  filtered     = Firewall dropping packets (no response or ICMP unreachable)
  unfiltered   = Port accessible, but nmap can't determine open/closed
  open|filtered= Can't tell if open or filtered (common with UDP)
```

**Decision tree for nmap results:**
```
  PORT SHOWS "filtered"?
  │
  ├─ YES → Firewall is blocking
  │        ├─ Check iptables/nftables rules
  │        ├─ Check cloud security groups
  │        └─ Try from different source IP
  │
  └─ NO → Port shows "closed"?
           ├─ YES → No service running on that port
           │        └─ Check: ss -tlnp | grep PORT
           └─ NO → Port shows "open" → Service is running
```

---

## 9. Layer 7 — Application Layer Tools

### 9.1 `curl` — HTTP/HTTPS Swiss Army Knife

**What it does:** Transfers data using various protocols. Essential for testing web servers, APIs, authentication, headers, TLS.

```bash
# Basic GET request
curl http://192.168.1.1

# Include response headers
curl -I http://192.168.1.1            # Headers only (HEAD request)
curl -v http://192.168.1.1            # Verbose: full request/response headers

# Follow redirects
curl -L http://example.com

# POST with JSON data
curl -X POST -H "Content-Type: application/json" \
     -d '{"key":"value"}' http://api.example.com/endpoint

# Test with custom Host header (virtual hosting test)
curl -H "Host: example.com" http://192.168.1.1

# Ignore TLS certificate errors (testing only!)
curl -k https://192.168.1.1

# Specify timeout
curl --connect-timeout 5 --max-time 10 http://example.com

# Test specific interface/source IP
curl --interface eth0 http://example.com

# Show detailed timing (connection, TTFB, total)
curl -w "\n\nDNS: %{time_namelookup}\nConnect: %{time_connect}\nTLS: %{time_appconnect}\nTTFB: %{time_starttransfer}\nTotal: %{time_total}\n" \
     -o /dev/null -s https://example.com

# Test with client certificate (mTLS)
curl --cert client.crt --key client.key https://example.com

# Set custom DNS server
curl --dns-servers 8.8.8.8 http://example.com
```

**curl timing breakdown:**
```
  DNS lookup:     time_namelookup   (DNS resolution delay)
  TCP connect:    time_connect      (network RTT)
  TLS handshake:  time_appconnect   (TLS negotiation)
  TTFB:           time_starttransfer (server processing + first byte)
  Total:          time_total        (everything including download)
  
  Slow DNS?      → DNS server issue
  Slow Connect?  → Network congestion or firewall delay
  Slow TLS?      → Certificate validation, cipher negotiation
  Slow TTFB?     → Server-side processing problem
```

### 9.2 `wget` — File Downloader with Debugging

```bash
wget -d http://example.com         # Debug mode (verbose headers)
wget --server-response http://example.com    # Show server response headers
wget --spider http://example.com   # Check if URL exists (no download)
wget --no-check-certificate https://example.com  # Ignore TLS errors
```

### 9.3 `telnet` — Raw TCP Connection Test

**What it does:** Opens a raw TCP connection to any host:port. Useful for manually testing protocols like HTTP, SMTP, FTP.

```bash
telnet 192.168.1.1 80     # Test HTTP port
telnet 192.168.1.1 25     # Test SMTP port
```

**Manual HTTP request via telnet:**
```
  $ telnet example.com 80
  Trying 93.184.216.34...
  Connected to example.com.
  
  (Type this exactly, press Enter twice):
  GET / HTTP/1.1
  Host: example.com
  [blank line]
  
  HTTP/1.1 200 OK
  Content-Type: text/html
  ...
```

This proves the HTTP service works at raw TCP level, ruling out curl/browser configuration issues.

---

## 10. Packet Capture & Deep Inspection

### 10.1 `tcpdump` — CLI Packet Sniffer

**What it does:** Captures and displays network packets in real time. The most fundamental network debugging tool — it shows you exactly what is on the wire.

**Concept — Promiscuous Mode:** Normally, a NIC only processes packets addressed to it. In promiscuous mode, it captures ALL packets on the segment. tcpdump enables this automatically.

**Concept — BPF Filter:** tcpdump uses Berkeley Packet Filter (BPF) — a powerful expression language to filter captured packets.

```bash
# Capture on specific interface
tcpdump -i eth0

# Capture with verbose output and no DNS
tcpdump -i eth0 -vvv -n

# Save to file for later analysis
tcpdump -i eth0 -w capture.pcap

# Read from saved file
tcpdump -r capture.pcap

# Filter by host
tcpdump -i eth0 host 192.168.1.1

# Filter by port
tcpdump -i eth0 port 443

# Filter by source/destination
tcpdump -i eth0 src 192.168.1.5
tcpdump -i eth0 dst 8.8.8.8

# Capture ONLY TCP SYN packets (connection attempts)
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) == 0'

# Capture HTTP traffic
tcpdump -i eth0 -A -s 0 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# Capture ICMP
tcpdump -i eth0 icmp

# Capture DNS queries
tcpdump -i eth0 -n 'udp port 53'

# Capture ARP
tcpdump -i eth0 arp

# Show packet contents in ASCII
tcpdump -i eth0 -A port 80

# Show packet contents in hex + ASCII
tcpdump -i eth0 -X port 80

# Combine filters with AND/OR/NOT
tcpdump -i eth0 'host 192.168.1.1 and not port 22'
tcpdump -i eth0 'port 80 or port 443'
```

**TCP Flags reference (for BPF filters):**
```
  tcp-syn  = SYN  (S) → Connection initiation
  tcp-ack  = ACK  (.) → Acknowledgment
  tcp-rst  = RST  (R) → Reset (abrupt close)
  tcp-fin  = FIN  (F) → Graceful close
  tcp-push = PSH  (P) → Push data immediately
  tcp-urg  = URG  (U) → Urgent data
  
  SYN only        → New connection attempt
  SYN+ACK         → Server accepting connection
  RST             → Connection forcefully rejected (firewall REJECT or closed port)
  FIN+ACK         → Graceful connection shutdown
```

**The TCP 3-Way Handshake — What to look for:**
```
  CLIENT                    SERVER
    │                          │
    │────── SYN ───────────────▶  "I want to connect"
    │                          │
    │◀────── SYN+ACK ──────────│  "OK, I'm ready"
    │                          │
    │────── ACK ───────────────▶  "Great, let's talk"
    │                          │
    │═══════ DATA TRANSFER ════│
    │                          │
    
  In tcpdump:
  S    = SYN
  S.   = SYN+ACK  (. means ACK bit set)
  .    = ACK
  P.   = PSH+ACK (data push)
  F.   = FIN+ACK (graceful close)
  R    = RST     (problem!)
```

**Reading tcpdump output:**
```
  10:35:42.123456 IP 192.168.1.5.54321 > 8.8.8.8.443: Flags [S], ...
  
  10:35:42.123456  → Timestamp
  IP               → Protocol
  192.168.1.5.54321→ Source IP.Port
  8.8.8.8.443      → Destination IP.Port
  [S]              → TCP Flags (SYN)
```

### 10.2 Wireshark (GUI) — Visual Packet Analysis

**What it does:** GUI-based packet analyzer with protocol dissectors, color coding, statistics, and follow-stream features.

**Key Wireshark Display Filters:**
```
  ip.addr == 192.168.1.1             Filter by IP
  ip.src == 192.168.1.5              Filter by source IP
  tcp.port == 443                    Filter by TCP port
  http                               Show only HTTP
  http.request.method == "POST"      HTTP POST only
  tcp.flags.syn == 1 && tcp.flags.ack == 0  SYN only (new connections)
  tcp.flags.reset == 1               TCP resets (problems!)
  dns                                DNS traffic
  tls                                TLS traffic
  icmp                               ICMP (ping/traceroute)
  !(arp || dns || icmp)              Exclude noise
  
  tcp.analysis.retransmission        Retransmitted packets
  tcp.analysis.zero_window           TCP window full (flow control)
  tcp.analysis.duplicate_ack         Duplicate ACKs (packet loss indicator)
```

**Statistics menu essentials:**
```
  Statistics → IO Graphs          → Throughput over time
  Statistics → TCP Stream Graphs  → RTT, window size, throughput
  Statistics → Protocol Hierarchy → What protocols are in the capture
  Statistics → Conversations      → Top talkers
  Analyze → Follow → TCP Stream  → Reassemble and read entire session
```

---

## 11. Firewall Debugging

### 11.1 `iptables` — Linux Firewall (netfilter)

**Concept — Tables and Chains:**

**Tables** define the purpose:
- `filter` = Accept/drop/reject packets (most common)
- `nat` = Network Address Translation (masquerading, port forwarding)
- `mangle` = Modify packet headers
- `raw` = Pre-connection tracking

**Chains** define when the rule applies:
- `INPUT` = Packets destined for THIS machine
- `OUTPUT` = Packets sent FROM this machine
- `FORWARD` = Packets passing THROUGH this machine (routing)
- `PREROUTING` = Before routing decision (nat DNAT, redirect)
- `POSTROUTING` = After routing decision (nat SNAT, masquerade)

**Packet flow through iptables:**
```
  INCOMING PACKET
       │
       ▼
  [PREROUTING]  ← nat table (DNAT, redirect)
       │
       ├── For this machine? ──────────────────────▶ [INPUT] ──▶ Local process
       │
       └── For another host? ──▶ [FORWARD] ──▶ [POSTROUTING] ──▶ Out
  
  LOCAL PROCESS SENDS PACKET
       │
       ▼
  [OUTPUT] ──▶ [POSTROUTING] ──▶ Out
```

```bash
# List all rules with line numbers
iptables -L -n -v --line-numbers

# List specific chain
iptables -L INPUT -n -v --line-numbers

# List NAT rules
iptables -t nat -L -n -v

# List all tables
iptables -t filter -L -n -v
iptables -t nat -L -n -v
iptables -t mangle -L -n -v

# Add rule: Allow incoming SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Add rule at position 1 (top priority)
iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT

# Drop all traffic from IP
iptables -A INPUT -s 10.0.0.5 -j DROP

# Allow ESTABLISHED/RELATED (stateful firewall)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Delete rule by line number
iptables -D INPUT 3

# Flush all rules (DANGEROUS - removes all rules!)
iptables -F

# Count packets per rule (watch mode)
watch -n 1 'iptables -L -n -v'

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "DROPPED: " --log-level 4
iptables -A INPUT -j DROP

# Test a rule WITHOUT adding it (iptables-legacy only)
# Use: iptables -C INPUT <rule>  → exit 0 = rule exists, exit 1 = doesn't
iptables -C INPUT -p tcp --dport 80 -j ACCEPT
```

**Debug: Which rule is matching?**
```bash
# Reset counters
iptables -Z

# Generate traffic to the host
ping 192.168.1.1

# See which rules have non-zero packet counts
iptables -L INPUT -n -v
```

**iptables rule reading:**
```
  Chain INPUT (policy DROP)    ← Default policy: DROP everything not matched
  target  prot  opt  source        destination
  ACCEPT  tcp   --   0.0.0.0/0    0.0.0.0/0    tcp dpt:22
  ACCEPT  tcp   --   10.0.0.0/8   0.0.0.0/0    tcp dpt:443
  DROP    all   --   0.0.0.0/0    0.0.0.0/0
  
  Read top-to-bottom: First match wins!
```

### 11.2 `nftables` — Modern Linux Firewall

**nftables** is the replacement for iptables in modern Linux systems.

```bash
# List all rules
nft list ruleset

# List specific table
nft list table inet filter

# Add rule
nft add rule inet filter input tcp dport 22 accept

# Monitor rule matches in real time
nft monitor trace
```

**Enable rule tracing (powerful debug feature!):**
```bash
# Mark packets to trace
nft add rule inet filter input meta nftrace set 1

# Start monitor
nft monitor trace

# This shows EVERY rule evaluation for each packet — incredibly powerful
```

### 11.3 `firewall-cmd` — firewalld (RHEL/CentOS/Fedora)

```bash
# Show active zones
firewall-cmd --get-active-zones

# List all rules in zone
firewall-cmd --zone=public --list-all

# Check if port is open
firewall-cmd --zone=public --query-port=80/tcp

# Allow port
firewall-cmd --zone=public --add-port=8080/tcp --permanent
firewall-cmd --reload

# Allow service by name
firewall-cmd --zone=public --add-service=https --permanent

# Block IP address
firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="10.0.0.5" reject'

# List rich rules
firewall-cmd --list-rich-rules

# Test: Where would traffic go?
firewall-cmd --zone=public --query-port=443/tcp
```

### 11.4 `ufw` — Uncomplicated Firewall (Ubuntu/Debian)

```bash
ufw status verbose
ufw status numbered         # With line numbers for deletion
ufw allow 22/tcp
ufw deny 23/tcp
ufw allow from 192.168.1.0/24 to any port 3306
ufw delete 3                # Delete rule number 3
ufw logging on              # Enable logging
ufw logging medium          # Log level
```

### 11.5 Firewall Log Analysis

```bash
# iptables logs go to syslog/kern.log
tail -f /var/log/kern.log | grep "DROPPED:"

# journalctl for systemd systems
journalctl -f -k | grep "DROPPED:"

# UFW logs
tail -f /var/log/ufw.log

# firewalld logs
journalctl -f -u firewalld
```

**Understanding firewall log entries:**
```
  DROPPED: IN=eth0 OUT= MAC=... SRC=10.0.0.5 DST=192.168.1.1 
           LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=12345 DF 
           PROTO=TCP SPT=54321 DPT=22 WINDOW=64240 RES=0x00 SYN
  
  IN=eth0      → Arrived on eth0
  SRC=10.0.0.5 → Source IP
  DST=192.168.1.1 → Destination IP
  PROTO=TCP    → Protocol
  SPT=54321    → Source port
  DPT=22       → Destination port (22 = SSH)
  SYN          → TCP SYN flag (new connection attempt)
```

---

## 12. DNS Debugging

### 12.1 Concepts First

**DNS (Domain Name System)** translates human-readable names (example.com) to IP addresses.

**DNS Record Types:**
```
  A     → IPv4 address           example.com → 93.184.216.34
  AAAA  → IPv6 address           example.com → 2606:2800:220:1::68
  CNAME → Alias to another name  www → example.com
  MX    → Mail server            example.com → mail.example.com
  NS    → Name server            example.com → ns1.example.com
  PTR   → Reverse lookup (IP→name)  34.216.184.93.in-addr.arpa → example.com
  TXT   → Text records           SPF, DKIM, verification
  SOA   → Start of Authority (zone info)
  SRV   → Service locator       _http._tcp.example.com
```

**DNS Resolution Chain:**
```
  Browser asks: "What's the IP for example.com?"
  
  ┌──────────────────────────────────────────────────────────┐
  │  1. Check local /etc/hosts file                          │
  │  2. Check local DNS cache                                │
  │  3. Ask Recursive Resolver (your ISP or 8.8.8.8)        │
  │     4. Resolver asks Root DNS (.)                        │
  │     5. Root says: ".com NS is a.gtld-servers.net"        │
  │     6. Resolver asks .com NS                             │
  │     7. .com NS says: "example.com NS is ns1.example.com" │
  │     8. Resolver asks ns1.example.com                     │
  │     9. Gets answer: example.com A 93.184.216.34          │
  │     10. Resolver caches and returns answer               │
  └──────────────────────────────────────────────────────────┘
```

### 12.2 `dig` — DNS Interrogator (The Best Tool)

**dig** (Domain Information Groper) is the definitive DNS debugging tool.

```bash
# Basic A record lookup
dig example.com

# Specific record type
dig example.com A
dig example.com AAAA
dig example.com MX
dig example.com NS
dig example.com TXT
dig example.com SOA
dig example.com CNAME

# Reverse lookup (IP to name)
dig -x 8.8.8.8

# Use specific DNS server
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com
dig @192.168.1.1 example.com    # Use your local DNS server

# Trace the full resolution path (+trace follows delegation)
dig +trace example.com

# Short output (just the answer)
dig +short example.com

# No recursion (ask the server what IT knows, no forwarding)
dig +norecurse @ns1.example.com example.com

# All DNS records
dig example.com ANY

# Show the query time and server used
dig example.com | grep -E "Query time|SERVER"

# Batch queries from file
dig -f hostnames.txt

# Check for DNSSEC
dig +dnssec example.com
```

**Reading dig output:**
```
  ; <<>> DiG 9.16 <<>> example.com
  ;; QUESTION SECTION:
  ;example.com.    IN A               ← What we asked
  
  ;; ANSWER SECTION:
  example.com. 3600 IN A 93.184.216.34  ← The answer
  │            │       │  └─ IP address
  │            │       └─ Record type (A)
  │            └─ TTL in seconds (3600 = 1 hour)
  └─ Domain name
  
  ;; AUTHORITY SECTION:              ← Which NS servers are authoritative
  ;; ADDITIONAL SECTION:             ← Extra info (glue records)
  
  ;; SERVER: 192.168.1.1#53          ← Which DNS server answered
  ;; Query time: 5 msec              ← How long it took
  
  NXDOMAIN                           ← Domain does not exist
  SERVFAIL                           ← DNS server error
  REFUSED                            ← Server refused to answer
```

### 12.3 `nslookup` — Legacy DNS Tool

```bash
nslookup example.com              # Basic lookup
nslookup example.com 8.8.8.8     # Use specific server
nslookup -type=MX example.com    # MX records
nslookup -type=NS example.com    # NS records
nslookup 8.8.8.8                  # Reverse lookup

# Interactive mode
nslookup
> server 8.8.8.8
> set type=TXT
> example.com
> exit
```

### 12.4 `host` — Simple DNS Lookup

```bash
host example.com
host -t MX example.com
host 8.8.8.8                # Reverse lookup
host -a example.com         # All records
```

### 12.5 Common DNS Problems

**Problem: DNS resolution fails**
```bash
# Step 1: Can we reach the DNS server?
ping 8.8.8.8

# Step 2: Can we reach DNS port?
nc -zuv 8.8.8.8 53

# Step 3: Does dig return an answer?
dig @8.8.8.8 google.com

# Step 4: Check /etc/resolv.conf
cat /etc/resolv.conf
# Should contain: nameserver 8.8.8.8 (or your DNS server)

# Step 5: Check /etc/nsswitch.conf
cat /etc/nsswitch.conf | grep hosts
# Should contain: hosts: files dns
# "files" = /etc/hosts checked first, "dns" = DNS second
```

**Check /etc/hosts for overrides:**
```bash
cat /etc/hosts
# If example.com is in here, it overrides DNS completely!
```

**Flush DNS cache:**
```bash
systemd-resolve --flush-caches    # systemd-resolved
resolvectl flush-caches           # Alternative
nscd -i hosts                     # nscd daemon
```

**DNS Debugging Decision Tree:**
```
  DNS resolution failing?
  │
  ├─ ping 8.8.8.8 works?
  │   ├─ NO  → L3/firewall issue (not DNS)
  │   └─ YES → nc -zuv 8.8.8.8 53 works?
  │             ├─ NO  → UDP port 53 blocked by firewall
  │             └─ YES → dig @8.8.8.8 google.com works?
  │                       ├─ NO  → DNS server issue
  │                       └─ YES → Local resolver issue
  │                                ├─ Check /etc/resolv.conf
  │                                └─ Check systemd-resolved
  │
  └─ dig works but app fails?
      ├─ Check /etc/hosts for overrides
      ├─ Check application's DNS configuration
      └─ Check /etc/nsswitch.conf order
```

---

## 13. TLS/SSL & Certificate Debugging

### 13.1 Concepts First

**TLS** (Transport Layer Security) encrypts network communications. **SSL** is its predecessor (deprecated but name persists).

**Certificate Chain:** TLS uses a chain of trust:
```
  Root CA (self-signed, trusted by OS/browser)
      │
      └─ Intermediate CA (signed by Root CA)
              │
              └─ Server Certificate (signed by Intermediate CA, for example.com)
```

**Concept — Handshake:** Before encrypted data flows, TLS negotiates:
1. Protocol version (TLS 1.2, TLS 1.3)
2. Cipher suite (encryption algorithm)
3. Certificate exchange and verification
4. Key agreement (session keys)

### 13.2 `openssl s_client` — TLS Debugger

**The most powerful TLS debugging tool.**

```bash
# Basic TLS connection test
openssl s_client -connect example.com:443

# Test with SNI (Server Name Indication — for virtual hosting)
openssl s_client -connect example.com:443 -servername example.com

# Show full certificate chain
openssl s_client -connect example.com:443 -showcerts

# Test specific TLS version
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# Test specific cipher
openssl s_client -connect example.com:443 -cipher AES256-SHA

# Test STARTTLS (for SMTP, IMAP, etc.)
openssl s_client -connect mail.example.com:25 -starttls smtp

# Check certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | \
       openssl x509 -noout -dates

# Verify certificate chain
openssl s_client -connect example.com:443 -CAfile /etc/ssl/certs/ca-certificates.crt

# Send HTTP request after TLS connect
echo -e "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n" | \
  openssl s_client -connect example.com:443 -quiet
```

**Reading openssl s_client output:**
```
  CONNECTED(00000003)
  depth=2 C = US, O = DigiCert Inc, CN = DigiCert Global Root CA  ← Root CA
  depth=1 C = US, O = DigiCert Inc, CN = DigiCert TLS RSA...      ← Intermediate CA
  depth=0 CN = example.com                                         ← Server cert
  verify return:1                                                  ← Chain verified OK
  
  Certificate chain:
   0 s:CN = example.com
     i:CN = DigiCert TLS RSA SHA256 2020 CA1
     
  SSL-Session:
    Protocol  : TLSv1.3          ← TLS version negotiated
    Cipher    : TLS_AES_256_GCM_SHA384  ← Cipher suite
    Session-ID: ...
    
  Verify return code: 0 (ok)     ← 0 = success, anything else = problem!
```

**Common verify errors:**
```
  Verify return code: 18 → Certificate is self-signed (not trusted)
  Verify return code: 19 → Self-signed cert in chain
  Verify return code: 20 → Unable to get local issuer certificate
  Verify return code: 21 → Unable to verify first certificate
  Verify return code: 10 → Certificate has expired!
```

### 13.3 `openssl x509` — Certificate Inspector

```bash
# View certificate details from a file
openssl x509 -in cert.pem -text -noout

# Check certificate dates
openssl x509 -in cert.pem -noout -dates

# Check subject (who this cert is for)
openssl x509 -in cert.pem -noout -subject

# Check issuer (who signed it)
openssl x509 -in cert.pem -noout -issuer

# Check SAN (Subject Alternative Names — valid hostnames for this cert)
openssl x509 -in cert.pem -noout -ext subjectAltName

# Verify a cert against a CA
openssl verify -CAfile ca.pem cert.pem

# Convert PEM to DER
openssl x509 -in cert.pem -outform DER -out cert.der

# Check if key matches certificate
openssl x509 -noout -modulus -in cert.pem | md5sum
openssl rsa -noout -modulus -in key.pem | md5sum
# If MD5 hashes match → key and cert are a pair
```

### 13.4 `sslyze` and `testssl.sh` — SSL Auditing

```bash
# sslyze: comprehensive TLS scanner
sslyze example.com:443

# testssl.sh: checks for vulnerabilities
./testssl.sh example.com

# Check for known vulnerabilities:
# HEARTBLEED, BEAST, POODLE, DROWN, ROBOT, LUCKY13, etc.
```

---

## 14. VPN Debugging

### 14.1 WireGuard Debugging

**Concept — WireGuard:** A modern, fast VPN that uses public-key cryptography. Peers exchange public keys and communicate via UDP.

```bash
# Show WireGuard status
wg show
wg show wg0

# Check interface
ip addr show wg0
ip route show dev wg0

# WireGuard handshake log (systemd)
journalctl -u wg-quick@wg0 -f

# Check if handshake happened (last handshake time)
wg show wg0 latest-handshakes
# If "0" → No handshake ever! Check keys, endpoints, firewall

# Check UDP port is open (WireGuard uses UDP, default 51820)
ss -ulnp | grep 51820
nc -zuv remote-host 51820

# Manually trigger handshake
wg set wg0 peer <PEER_PUBKEY> endpoint remote-host:51820
```

**WireGuard debugging checklist:**
```
  No connectivity through WireGuard?
  │
  ├─ wg show: latest-handshake = 0?
  │   ├─ YES → No handshake → Check:
  │   │         ├─ Remote UDP port 51820 open? (nc -zuv)
  │   │         ├─ Public keys correct?
  │   │         ├─ Firewall allowing UDP 51820?
  │   │         └─ Endpoint IP/hostname correct?
  │   │
  │   └─ NO → Handshake happened → Check:
  │             ├─ AllowedIPs correct?
  │             ├─ ip route dev wg0 correct?
  │             └─ Remote peer's routing/firewall?
```

### 14.2 OpenVPN Debugging

```bash
# Run with high verbosity (verb 6+ for deep debug)
openvpn --config client.ovpn --verb 6

# Check OpenVPN log
journalctl -u openvpn@client -f
tail -f /var/log/openvpn.log

# Verify TLS handshake
# In log look for: "TLS handshake failed" → cert issue
# Look for: "AUTH_FAILED" → credentials wrong
# Look for: "VERIFY ERROR" → certificate not trusted

# Check routing after connection
ip route show
ip route show table all | grep -i vpn

# Test DNS through VPN (if VPN should resolve internal names)
dig @<VPN_DNS_SERVER> internal.company.com
```

### 14.3 IPsec Debugging

**Concept — IPsec:** A suite of protocols for securing IP communications through authentication and encryption. Used heavily in enterprise VPNs.

```bash
# strongSwan/Libreswan status
ipsec status
ipsec statusall

# Detailed SA (Security Association) info
ip xfrm state list      # Encryption/auth parameters
ip xfrm policy list     # Traffic selectors (what traffic goes through VPN)

# Show IKE negotiations
ipsec up <connection-name>
journalctl -u strongswan -f

# Test connectivity
ping -I <vpn_interface> remote_host
```

---

## 15. IDS/IPS Debugging

### 15.1 Concepts

**IDS** (Intrusion Detection System) = Monitors traffic and ALERTS on suspicious activity (passive).
**IPS** (Intrusion Prevention System) = Monitors AND BLOCKS suspicious traffic (active).

**Concept — Rule/Signature:** IDS/IPS rules define patterns that indicate attacks (e.g., SQL injection strings, port scan patterns, known malware signatures).

**Concept — False Positive:** IDS alerts on legitimate traffic as if it were malicious. False positives cause alert fatigue.

**Concept — False Negative:** Real attack that the IDS misses entirely. False negatives are dangerous.

### 15.2 Snort / Suricata Debugging

```bash
# Test Snort configuration
snort -T -c /etc/snort/snort.conf

# Run Snort in alert mode on interface
snort -i eth0 -A console -q -c /etc/snort/snort.conf

# Test specific rules
snort -i eth0 -A fast -l /var/log/snort -c /etc/snort/snort.conf

# Suricata: test config
suricata -T -c /etc/suricata/suricata.yaml

# Run Suricata
suricata -i eth0 -c /etc/suricata/suricata.yaml

# Live alerts
tail -f /var/log/suricata/fast.log
tail -f /var/log/suricata/eve.json | python3 -m json.tool

# Check if a specific rule is triggering
grep "1001" /var/log/suricata/fast.log   # Rule SID 1001
```

**Reading Snort/Suricata alert:**
```
  [**] [1:1000001:1] SQL Injection Attempt [**]
  [Classification: Web Application Attack] [Priority: 1]
  03/15-10:30:00.123456 10.0.0.5:54321 -> 192.168.1.10:80
  TCP TTL:64 TOS:0x0 ID:12345 IpLen:20 DgmLen:100
  ***AP*** Seq: 0x1234 Ack: 0x5678 Win: 0x7210 TcpLen: 20
  
  1:1000001:1  → Generator:SID:Revision
  10.0.0.5:54321 → 192.168.1.10:80  → Direction
```

---

## 16. Bandwidth & Performance Testing

### 16.1 `iperf3` — Bandwidth Measurement

**Concept:** iperf3 measures actual throughput between two endpoints. You need iperf3 on both the client and server.

```bash
# Server side (listen for connections)
iperf3 -s

# Client side (connect and test)
iperf3 -c server_ip

# Test for 30 seconds
iperf3 -c server_ip -t 30

# UDP test (instead of TCP)
iperf3 -c server_ip -u -b 100M    # UDP, 100 Mbps target bandwidth

# Bidirectional test (both directions simultaneously)
iperf3 -c server_ip --bidir

# Multiple parallel streams (stress test)
iperf3 -c server_ip -P 4         # 4 parallel TCP streams

# Reverse mode (server sends TO client)
iperf3 -c server_ip -R

# Test with specific port
iperf3 -s -p 5202
iperf3 -c server_ip -p 5202

# JSON output
iperf3 -c server_ip -J | python3 -m json.tool
```

**Reading iperf3 output:**
```
  Interval       Transfer     Bandwidth
  0.00-1.00  sec  112 MBytes  941 Mbits/sec     ← Per-second measurement
  0.00-10.00 sec  1.09 GBytes 937 Mbits/sec     ← Overall summary
  
  Expected bandwidth much lower than link speed?
  → Firewall shaping/throttling
  → MTU mismatch causing fragmentation
  → TCP buffer sizes too small (check net.core.rmem_max)
  → Bad cable/duplex mismatch
```

### 16.2 `hping3` — Custom Packet Generator

**What it does:** Creates custom TCP/UDP/ICMP packets with any parameters. Useful for testing firewall rules precisely.

```bash
# ICMP ping (like regular ping but more control)
hping3 -1 192.168.1.1

# TCP SYN to port 80 (like a connection attempt)
hping3 -S -p 80 192.168.1.1

# TCP SYN flood test (careful — use only on your own systems!)
hping3 -S -p 80 --flood 192.168.1.1

# Traceroute using TCP (bypasses ICMP filters)
hping3 -S -p 80 --traceroute 192.168.1.1

# Send with specific TTL
hping3 --ttl 5 192.168.1.1

# UDP packet to port 53
hping3 -2 -p 53 192.168.1.1

# Fragment packets
hping3 -f -p 80 192.168.1.1

# Set specific source port
hping3 -S -p 80 -s 54321 192.168.1.1
```

### 16.3 `tc` — Traffic Control (QoS and Shaping)

**What it does:** Controls network bandwidth, delay, packet loss, and reordering at the kernel level. Used to test application behavior under poor network conditions.

```bash
# Show current qdisc (queuing discipline)
tc qdisc show dev eth0

# Add 100ms artificial delay (testing latency sensitivity)
tc qdisc add dev eth0 root netem delay 100ms

# Add random delay + packet loss
tc qdisc add dev eth0 root netem delay 100ms 20ms loss 5%

# Limit bandwidth to 1Mbit
tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms

# Remove all tc rules
tc qdisc del dev eth0 root

# Show class statistics
tc -s class show dev eth0
```

---

## 17. SNMP & Network Monitoring

### 17.1 Concepts

**SNMP** (Simple Network Management Protocol) is a protocol for monitoring and managing network devices (routers, switches, firewalls).

**Concept — OID:** Object Identifier — a unique numerical path identifying a specific piece of information (like interface counters, CPU usage) in the **MIB** (Management Information Base — the database of SNMP variables).

**Concept — Community String:** In SNMP v1/v2c, this acts like a password. "public" = read-only, "private" = read-write. SNMPv3 uses proper authentication.

```bash
# Test SNMP connectivity
snmpwalk -v2c -c public 192.168.1.1

# Get specific OID (system description)
snmpget -v2c -c public 192.168.1.1 1.3.6.1.2.1.1.1.0

# Walk interface table
snmpwalk -v2c -c public 192.168.1.1 1.3.6.1.2.1.2.2.1

# Common OIDs:
# sysDescr:   1.3.6.1.2.1.1.1.0   → Device description
# sysUpTime:  1.3.6.1.2.1.1.3.0   → Uptime
# ifTable:    1.3.6.1.2.1.2.2     → Interface table
# ifInErrors: 1.3.6.1.2.1.2.2.1.14 → Inbound errors per interface
# ifOutErrors:1.3.6.1.2.1.2.2.1.20 → Outbound errors

# SNMPv3 (secure)
snmpwalk -v3 -l authPriv -u admin -a SHA -A authpass -x AES -X privpass 192.168.1.1

# Test SNMP trap reception
snmptrapd -f -Le    # Run trap daemon in foreground
```

---

## 18. Log Analysis & Syslog

### 18.1 `journalctl` — systemd Log Viewer

```bash
# Follow logs in real time
journalctl -f

# Filter by service
journalctl -u sshd -f
journalctl -u nginx -f
journalctl -u firewalld -f

# Kernel messages only
journalctl -k
journalctl -k --since "1 hour ago"

# Priority levels (emerg=0, alert=1, crit=2, err=3, warn=4, notice=5, info=6, debug=7)
journalctl -p err    # Only errors and above
journalctl -p warning..crit   # Range

# Time filtering
journalctl --since "2024-01-15 10:00:00"
journalctl --since "1 hour ago"
journalctl --until "2024-01-15 11:00:00"

# Show boot messages
journalctl -b        # Current boot
journalctl -b -1     # Previous boot

# Export to JSON
journalctl -u sshd -o json | python3 -m json.tool

# Search for pattern
journalctl | grep -i "refused\|denied\|failed\|error"
```

### 18.2 Common Log Files

```
  /var/log/syslog          → General system messages (Debian/Ubuntu)
  /var/log/messages        → General system messages (RHEL/CentOS)
  /var/log/kern.log        → Kernel messages (iptables DROP logs here)
  /var/log/auth.log        → Authentication (SSH logins, sudo)
  /var/log/secure          → Authentication (RHEL/CentOS)
  /var/log/nginx/access.log   → Web server access log
  /var/log/nginx/error.log    → Web server errors
  /var/log/apache2/access.log → Apache access log
  /var/log/ufw.log            → UFW firewall log
  /var/log/fail2ban.log       → Fail2ban bans
  /var/log/suricata/fast.log  → Suricata IDS alerts
  /var/log/snort/alert        → Snort IDS alerts
  /var/log/openvpn.log        → OpenVPN connection log
```

### 18.3 Log Analysis Patterns

```bash
# Count failed SSH login attempts by IP
grep "Failed password" /var/log/auth.log | \
  awk '{print $11}' | sort | uniq -c | sort -rn | head -20

# Find IPs causing most firewall drops
grep "DROPPED" /var/log/kern.log | \
  grep -oP 'SRC=\K[0-9.]+' | sort | uniq -c | sort -rn | head -20

# HTTP error codes from nginx
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Real-time connection tracking
watch -n 2 'ss -tn | awk "{print \$5}" | cut -d: -f1 | sort | uniq -c | sort -rn'
```

---

## 19. Decision Trees for Common Problems

### 19.1 "I Can't Reach a Website"

```
  PROBLEM: Cannot access https://example.com
  │
  ├─ STEP 1: Can you ping 8.8.8.8?
  │   ├─ NO  → Layer 3 broken. Check:
  │   │         ├─ ip addr (do you have an IP?)
  │   │         ├─ ip route (do you have a default gateway?)
  │   │         └─ arping gateway (can you reach your gateway at L2?)
  │   │
  │   └─ YES → STEP 2: Can you ping example.com by IP?
  │             ├─ NO  → DNS is broken. Check:
  │             │         ├─ cat /etc/resolv.conf
  │             │         ├─ dig @8.8.8.8 example.com
  │             │         └─ nc -zuv 8.8.8.8 53
  │             │
  │             └─ YES → STEP 3: Can you reach port 443?
  │                       nc -zv example.com 443
  │                       ├─ NO  → Port 443 blocked:
  │                       │         ├─ Local firewall (iptables, ufw)
  │                       │         └─ Upstream firewall/proxy
  │                       │
  │                       └─ YES → STEP 4: TLS issue?
  │                                 openssl s_client -connect example.com:443
  │                                 ├─ Cert expired? → Renew cert
  │                                 ├─ VERIFY ERROR? → Cert chain issue
  │                                 └─ OK → App-level issue (check curl -v)
```

### 19.2 "SSH Connection Refused/Timeout"

```
  PROBLEM: SSH to 192.168.1.10 fails
  │
  ├─ "Connection refused"?
  │   └─ SSH service not running. On target:
  │       systemctl status sshd
  │       ss -tlnp | grep 22
  │
  ├─ "Connection timed out"?
  │   └─ Firewall dropping packets:
  │       ├─ iptables -L -n | grep 22
  │       ├─ ufw status
  │       └─ Check cloud security groups / ACLs
  │
  ├─ "No route to host"?
  │   └─ Routing problem:
  │       ├─ ping 192.168.1.10 (L3 reachable?)
  │       ├─ ip route get 192.168.1.10
  │       └─ mtr 192.168.1.10
  │
  └─ "Permission denied (publickey)"?
      └─ Authentication problem:
          ├─ ssh -v 192.168.1.10 (verbose output)
          ├─ Check ~/.ssh/authorized_keys on server
          ├─ Check permissions: chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys
          └─ Check sshd_config: PubkeyAuthentication yes
```

### 19.3 "Intermittent Packet Loss"

```
  PROBLEM: Packet loss, sometimes works, sometimes doesn't
  │
  ├─ STEP 1: mtr -n 8.8.8.8 for 5 minutes
  │   ├─ Loss at specific hop and all after?
  │   │   └─ Problem is AT that hop (congestion, bad link)
  │   ├─ Loss only at LAST hop?
  │   │   └─ Destination filtering ICMP (not real packet loss)
  │   └─ Loss at ALL hops equally?
  │       └─ Local issue (NIC, driver, cable)
  │
  ├─ STEP 2: Check NIC errors
  │   ethtool -S eth0 | grep -i error
  │   ├─ rx_errors > 0? → Physical layer (cable, SFP, EMI)
  │   └─ rx_dropped > 0? → Kernel buffer overflow (CPU/memory issue)
  │
  ├─ STEP 3: Check duplex mismatch
  │   ethtool eth0 | grep -i duplex
  │   └─ Half-duplex? → Force full-duplex:
  │       ethtool -s eth0 duplex full speed 1000 autoneg off
  │
  └─ STEP 4: MTU issue?
      ping -M do -s 1472 8.8.8.8    # Test with DF bit set, 1472+28=1500 MTU
      ├─ Works with 1472 but not 1473+? → MTU correctly at 1500
      └─ Fails at lower sizes? → MTU black hole (some router drops large packets)
          Solution: Reduce MTU: ip link set eth0 mtu 1400
```

### 19.4 "Firewall Rule Not Working"

```
  PROBLEM: Added a firewall ALLOW rule, but traffic still blocked
  │
  ├─ STEP 1: Verify rule actually exists
  │   iptables -L INPUT -n -v --line-numbers | grep PORT
  │   └─ Not there? → Rule wasn't applied correctly
  │
  ├─ STEP 2: Check rule ORDER (first match wins!)
  │   iptables -L INPUT -n -v --line-numbers
  │   └─ Is there a DROP/REJECT rule BEFORE your ALLOW?
  │       → Insert your rule BEFORE the deny:
  │         iptables -I INPUT 1 -p tcp --dport PORT -j ACCEPT
  │
  ├─ STEP 3: Reset counters, test, check matches
  │   iptables -Z
  │   [generate traffic]
  │   iptables -L INPUT -n -v
  │   └─ Your ALLOW rule has 0 packets? → Traffic not reaching this chain
  │       → Check PREROUTING/FORWARD chains, check routing
  │
  └─ STEP 4: Check if traffic is on correct interface
      tcpdump -i eth0 port PORT
      └─ Traffic arrives on wrong interface? → Rule needs different interface
          iptables -A INPUT -i eth0 -p tcp --dport PORT -j ACCEPT
```

---

## 20. Advanced Mental Models for Expert Debugging

### 20.1 The Bisection Method

When you don't know where in a multi-hop path the problem is, **bisect**:

```
  You know: Source ──> Hop1 ──> Hop2 ──> Hop3 ──> Hop4 ──> Destination
  Problem: Source can't reach Destination
  
  Step 1: Test from Hop2 → Can Hop2 reach Destination?
           YES → Problem is between Source and Hop2
           NO  → Problem is between Hop2 and Destination
  
  Step 2: If between Source and Hop2, test Hop1:
           Can Hop1 reach Destination?
           ...
  
  This is O(log n) instead of O(n) — much faster for long paths!
```

### 20.2 Correlation vs Causation in Logs

```
  Dangerous assumption:
  "I see a firewall DENY log at 10:30:00 and the outage started at 10:30:00
   → The firewall caused the outage!"
  
  Reality check:
  - Was this deny log also happening BEFORE the outage?
  - Is this deny for critical traffic or background noise?
  - Did anything else change at 10:30:00?
  
  Always look at BASELINE behavior (what was normal before?) vs ANOMALY.
```

### 20.3 The Rubber Duck Principle

Explain the problem out loud (even to yourself, a rubber duck, or your notes):
1. "Traffic goes from A to B..."
2. "It passes through firewall F..."
3. "The rule says..."
4. "Wait — the rule says DROP all, but my ALLOW rule is at position 5, AFTER the DROP at position 2..."

**Often, the act of articulating the problem reveals the solution.**

### 20.4 Eliminate Variables Systematically

```
  Unknown: Is it a firewall issue, routing issue, or service issue?
  
  Test 1: bypass the firewall (if possible) → If works → Firewall issue
  Test 2: use different source IP → If works → Source-specific rule
  Test 3: test from the target host itself → If works → Network issue
  Test 4: test a different port → If works → Port-specific rule
  
  Each test eliminates one category. Work methodically.
```

### 20.5 The Three-Layer Mental Model for Security Devices

```
  Every security device has three layers to debug:

  ┌─────────────────────────────────────────────────┐
  │ LAYER 3: POLICY / CONFIGURATION                 │
  │ "Are the rules/policies correctly defined?"     │
  │ Tools: show config, policy review               │
  ├─────────────────────────────────────────────────┤
  │ LAYER 2: OPERATIONAL STATE                      │
  │ "Is the device functioning correctly?"          │
  │ Tools: show status, interfaces, sessions, CPU   │
  ├─────────────────────────────────────────────────┤
  │ LAYER 1: CONNECTIVITY                           │
  │ "Can packets physically reach the device?"      │
  │ Tools: ping, traceroute, arp, tcpdump           │
  └─────────────────────────────────────────────────┘
  
  Debug bottom-up: Connectivity → State → Policy
```

### 20.6 Quick Reference Command Matrix

```
  SYMPTOM                    FIRST COMMAND             FOLLOW-UP
  ─────────────────────────────────────────────────────────────────────
  No network at all          ip link show              ip addr, ip route
  Can't ping gateway         arping -I eth0 gateway    arp -n, ethtool
  Can ping IP, not hostname  dig @8.8.8.8 hostname     cat /etc/resolv.conf
  Port unreachable           nc -zv host port          nmap, iptables -L
  Packet loss                mtr -n destination        tcpdump, ethtool -S
  Slow connection            iperf3 -c server          tc qdisc, mtr
  TLS error                  openssl s_client          openssl x509 -dates
  SSH refuses                nc -zv host 22            systemctl status sshd
  Firewall rule not working  iptables -L -n -v -Z      tcpdump, iptables -L
  VPN not connecting         wg show / ipsec status    journalctl, nmap
  High packet loss at NIC    ethtool -S eth0           dmesg, ip link
  Unknown traffic            tcpdump -i eth0 -n        nmap (source IPs)
  DNS not resolving          dig @8.8.8.8 name         resolvectl, nsswitch
```

---

## Appendix A: Essential `/proc` Files for Network Debugging

```bash
# Network interface statistics
cat /proc/net/dev

# ARP cache
cat /proc/net/arp

# Routing table
cat /proc/net/route        # Hex format
cat /proc/net/fib_trie     # Trie format (detailed)

# TCP connections
cat /proc/net/tcp          # IPv4 TCP sockets (hex)
cat /proc/net/tcp6         # IPv6 TCP sockets

# UDP sockets
cat /proc/net/udp

# Network statistics (ICMP, TCP, UDP counters)
cat /proc/net/netstat
cat /proc/net/snmp

# Conntrack (connection tracking table)
cat /proc/net/nf_conntrack

# Kernel network tuning parameters
sysctl -a | grep net.
```

## Appendix B: Kernel Network Tuning

```bash
# View current value
sysctl net.ipv4.ip_forward

# Enable IP forwarding (required for routing/VPN)
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# TCP buffer sizes
sysctl net.core.rmem_max         # Max receive buffer
sysctl net.core.wmem_max         # Max send buffer

# Connection tracking table size
sysctl net.netfilter.nf_conntrack_max
sysctl net.netfilter.nf_conntrack_count   # Current count

# SYN backlog (for servers under high connection load)
sysctl net.ipv4.tcp_max_syn_backlog

# TIME_WAIT recycling
sysctl net.ipv4.tcp_tw_reuse

# Disable ICMP redirects (security hardening)
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv4.conf.all.accept_redirects=0
```

## Appendix C: The Expert's Minimal Toolkit

When you have access to a minimal system (container, embedded device), here are the most important tools in priority order:

```
  Priority 1 (must have):
  ├─ ip (iproute2)     → interfaces, routes, ARP
  ├─ ping              → ICMP reachability
  ├─ curl/wget         → HTTP testing
  └─ ss/netstat        → Socket inspection

  Priority 2 (very useful):
  ├─ tcpdump           → Packet capture (root required)
  ├─ nc/ncat           → Port testing
  ├─ dig/nslookup      → DNS testing
  └─ openssl           → TLS/cert testing

  Priority 3 (advanced):
  ├─ nmap              → Comprehensive scanning
  ├─ mtr               → Path analysis
  ├─ iperf3            → Throughput testing
  └─ iptables          → Firewall inspection
```

---

*"Mastery in network debugging is not memorizing commands — it's building an internal model of how packets flow through your system. When that model is complete, the right tool to apply at any given moment becomes obvious."*

---
**Guide Version:** 1.0  
**Coverage:** OSI Layers 1-7 | Firewalls | DNS | TLS | VPN | IDS/IPS | Packet Capture | Log Analysis

Here is your complete guide. Here's what's packed inside across **20 major sections**:

**Foundational Concepts (things most guides skip):**
- What packets, ports, sockets, firewalls, subnets, MTU, TTL, and ICMP actually are — explained from first principles with ASCII diagrams.

**Tools Covered (beyond ping and traceroute):**

| Layer | Tools |
|---|---|
| Physical (L1) | `ip link`, `ethtool`, `dmesg` |
| Data Link (L2) | `arp`, `ip neigh`, `arping`, `bridge` |
| Network (L3) | `ip route`, `mtr`, `traceroute`, `tracepath` |
| Transport (L4) | `ss`, `netstat`, `nc`, `nmap` |
| Application (L7) | `curl`, `wget`, `telnet` |
| Packet Capture | `tcpdump`, Wireshark filter reference |
| Firewall | `iptables`, `nftables`, `firewall-cmd`, `ufw` |
| DNS | `dig`, `nslookup`, `host` |
| TLS/SSL | `openssl s_client`, `openssl x509`, `sslyze` |
| VPN | WireGuard `wg`, OpenVPN, IPsec |
| IDS/IPS | Snort, Suricata |
| Performance | `iperf3`, `hping3`, `tc` |
| Monitoring | SNMP, `snmpwalk` |
| Logs | `journalctl`, log file locations, grep patterns |

**Decision Trees for:** website unreachable, SSH failure, packet loss, firewall rule not matching.

**Expert mental models:** bisection method, correlation vs causation, eliminating variables, the three-layer security device model — all principles that a world-class network engineer carries in their head.