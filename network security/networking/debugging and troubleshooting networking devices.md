# Complete Guide to Debugging and Troubleshooting Networking Devices

> *"The network is the computer." — John Gage, Sun Microsystems*  
> Master the tools. Master the layers. Master the thinking.

---

## Table of Contents

1. [Mental Model: The OSI Layered Thinking Framework](#1-mental-model-the-osi-layered-thinking-framework)
2. [Layer 1 — Physical Layer Diagnostics](#2-layer-1--physical-layer-diagnostics)
3. [Layer 2 — Data Link Layer Tools](#3-layer-2--data-link-layer-tools)
4. [Layer 3 — Network Layer Tools (Beyond Ping & Traceroute)](#4-layer-3--network-layer-tools-beyond-ping--traceroute)
5. [Layer 4 — Transport Layer Diagnostics](#5-layer-4--transport-layer-diagnostics)
6. [Layer 7 — Application Layer Diagnostics](#6-layer-7--application-layer-diagnostics)
7. [Packet Capture & Deep Inspection](#7-packet-capture--deep-inspection)
8. [DNS Diagnostics](#8-dns-diagnostics)
9. [Routing & Path Analysis](#9-routing--path-analysis)
10. [Firewall & ACL Diagnostics](#10-firewall--acl-diagnostics)
11. [Interface & Link Statistics](#11-interface--link-statistics)
12. [Network Performance Benchmarking](#12-network-performance-benchmarking)
13. [Wireless Network Diagnostics](#13-wireless-network-diagnostics)
14. [DHCP & ARP Diagnostics](#14-dhcp--arp-diagnostics)
15. [SSL/TLS Diagnostics](#15-ssltls-diagnostics)
16. [Network Monitoring & SNMP](#16-network-monitoring--snmp)
17. [Logs & Syslog Analysis](#17-logs--syslog-analysis)
18. [Vendor-Specific CLI Diagnostics (Cisco, Juniper, Linux)](#18-vendor-specific-cli-diagnostics-cisco-juniper-linux)
19. [Systematic Troubleshooting Methodology](#19-systematic-troubleshooting-methodology)
20. [Advanced Concepts: MTU, Fragmentation, Jitter, QoS](#20-advanced-concepts-mtu-fragmentation-jitter-qos)
21. [Security-Oriented Diagnostics](#21-security-oriented-diagnostics)
22. [Tool Reference Cheat Sheet](#22-tool-reference-cheat-sheet)

---

## 1. Mental Model: The OSI Layered Thinking Framework

Before touching a single tool, you must think architecturally. The single most important meta-skill in network troubleshooting is **knowing which layer to suspect**.

### The OSI Model as a Diagnostic Compass

```
Layer 7 — Application    → HTTP, DNS, FTP, SMTP, SNMP
Layer 6 — Presentation   → SSL/TLS, encoding, compression
Layer 5 — Session        → NetBIOS, RPC sessions
Layer 4 — Transport      → TCP, UDP, ports, flow control
Layer 3 — Network        → IP, ICMP, routing, subnetting
Layer 2 — Data Link      → Ethernet, MAC, ARP, VLANs, STP
Layer 1 — Physical       → Cables, signals, optical fiber, RF
```

### The Divide-and-Conquer Diagnostic Strategy

Two master strategies exist:

**Bottom-Up:** Start at Layer 1 (physical) and verify each layer working before going higher. Best when the fault is unknown.

**Top-Down:** Start at Layer 7 (application). The application sees the problem first; work down until something breaks. Best when symptoms are application-specific.

**Divide in Half (Binary Search):** Suspect Layer 4? Verify Layer 3 works AND Layer 7 fails. Isolates the fault zone quickly.

### The Expert Mindset Before Picking Any Tool

Ask yourself five questions before touching a terminal:

1. **What changed?** — Most outages follow a change (config push, upgrade, cable swap).
2. **What scope?** — One user? One subnet? One site? All sites?
3. **Which direction?** — One-way failure? Bidirectional? Upload or download only?
4. **Intermittent or constant?** — Intermittent faults are the hardest; they point to flapping, collisions, or overload.
5. **When did it start?** — Correlate with maintenance windows, weather (for microwave links), or traffic peaks.

---

## 2. Layer 1 — Physical Layer Diagnostics

Physical layer faults account for roughly **70–80% of real-world network problems**. Most engineers underestimate this layer.

### 2.1 Cable Testing

#### TDR (Time Domain Reflectometer)
A TDR sends a pulse down a cable and measures the reflection. From the reflection delay, it calculates:
- Distance to a break or fault
- Cable length
- Impedance mismatch location

```
Usage (conceptual):
TDR pulse sent → reflects off discontinuity → delay measured
Distance = (Speed of propagation × Time) / 2
```

Commercial tools: Fluke Networks DTX CableAnalyzer, Ideal Networks LanTEK.

#### OTDR (Optical Time Domain Reflectometer)
The fiber-optic equivalent of TDR. Used to:
- Locate fiber breaks
- Measure splice loss
- Find connector degradation
- Test total fiber span length

Key metrics from OTDR traces:
- **dB loss per km** — should be < 0.35 dB/km for single-mode fiber
- **Splice loss** — should be < 0.1 dB per fusion splice
- **Connector loss** — should be < 0.5 dB per connector pair

#### Visual Fault Locator (VFL)
A laser tool that injects visible red light into a fiber to find:
- Tight bends causing light leakage
- Breaks within ~5 km
- Incorrect patch panel routing

#### Copper Cable Verification
- **Continuity tester** — verifies all 8 conductors are connected
- **Wiremap tester** — verifies correct pairing per T568A/T568B
- **Cat rating tester** — measures crosstalk (NEXT, FEXT), return loss, and bandwidth

Common wiring faults:
- **Split pair** — wires from different pairs used together; passes continuity but causes massive crosstalk
- **Reversed pair** — pin 1/2 swapped
- **Crossed pair** — pair connected to wrong pins on one end
- **Short** — two conductors touching
- **Open** — conductor broken

### 2.2 ethtool (Linux)

`ethtool` is the primary Linux tool for physical and data-link layer hardware inspection.

```bash
# Check interface speed, duplex, link status
ethtool eth0

# Output example:
# Settings for eth0:
#   Speed: 1000Mb/s
#   Duplex: Full
#   Auto-negotiation: on
#   Link detected: yes

# Check driver and firmware information
ethtool -i eth0

# Show interface statistics (error counters)
ethtool -S eth0

# Force speed and duplex (disables auto-negotiation)
ethtool -s eth0 speed 1000 duplex full autoneg off

# Test cable via TDR (if NIC supports it)
ethtool --cable-test eth0

# Check pause frames (flow control)
ethtool -a eth0
```

**Critical fields to check:**
- `Link detected: no` → physical layer failure (cable, SFP, port)
- `Speed: Unknown` → negotiation failed
- `rx_errors`, `tx_errors` in `-S` output → hardware or cabling issues
- `rx_missed_errors` → NIC cannot keep up with traffic (buffer overflow)
- `rx_crc_errors` → electromagnetic interference or bad cable

### 2.3 SFP/Transceiver Diagnostics

Modern SFPs support **DOM (Digital Optical Monitoring)**, which exposes real-time optical power levels.

```bash
# Read SFP DOM data (Linux)
ethtool -m eth0

# Or via vendor CLI
show interfaces ethernet 0/1 transceiver detail  # Arista/Cisco-like
```

DOM readings to check:
- **TX Power (dBm)** — the optical power the SFP is transmitting
- **RX Power (dBm)** — the optical power being received
- **Laser Bias Current (mA)** — indicates laser health
- **Temperature (°C)** — overheating SFPs malfunction intermittently
- **Voltage (V)** — power supply to the transceiver

Typical single-mode SFP at 1 km:
- TX: -3 to +3 dBm
- RX: -3 to -20 dBm (depends on distance)
- If RX power is -30 dBm or lower → dirty connector, broken fiber, or wrong fiber type

**Clean connectors first.** Dirty fiber connectors are the #1 cause of intermittent optical link failures. A single fingerprint on an SC connector can cause 10+ dB of loss.

### 2.4 Interface Error Counters

Every managed switch and router exposes interface counters. Understanding them is crucial.

```
Input errors types:
- Runts         → frames < 64 bytes (truncated, usually collision artifacts)
- Giants        → frames > MTU (config mismatch or misconfigured jumbo frames)
- CRC errors    → bad frames detected by checksum (cabling or EMI)
- Frame errors  → framing alignment problems
- Overruns      → input buffer overflow (NIC cannot keep up)
- Ignored       → frames discarded due to no buffer space

Output errors types:
- Collisions    → expected only in half-duplex; on full-duplex = duplex mismatch
- Late collisions → occur after 64 bytes transmitted = duplex mismatch almost certainly
- Deferred      → waited for idle medium (half-duplex only)
- Output drops  → output queue overflow (congestion)
```

**Duplex mismatch** is one of the most common physical/data-link issues:
- One side is half-duplex, other is full-duplex
- The full-duplex side sees constant late collisions and CRC errors
- The half-duplex side sees excessive collisions
- Link "works" but performance is 10–20× degraded

```bash
# On Linux: check for duplex mismatch indicators
ethtool eth0 | grep -E "Speed|Duplex"
ip -s link show eth0   # shows TX/RX error counts
```

---

## 3. Layer 2 — Data Link Layer Tools

### 3.1 ARP (Address Resolution Protocol) Inspection

ARP is the glue between Layer 3 (IP) and Layer 2 (MAC). Almost every network problem eventually involves ARP.

```bash
# View local ARP cache
arp -n                   # Linux, no DNS resolution
ip neigh show            # Modern Linux (iproute2)
arp -a                   # macOS / Windows

# Flush ARP cache (useful when stale entries cause blackholing)
ip neigh flush all       # Linux
arp -d <IP>              # Delete specific entry

# Send gratuitous ARP (announce your own IP/MAC mapping)
arping -I eth0 -c 3 192.168.1.1

# Detect ARP spoofing (multiple MACs for same IP)
arp -n | awk '{print $1}' | sort | uniq -d
```

**ARP table states (Linux `ip neigh`):**
```
REACHABLE   — recently verified
STALE       — not used recently but still cached
DELAY       — timer started to re-verify
PROBE       — actively sending ARP requests
FAILED      — no response received
INCOMPLETE  — ARP request sent, no reply yet (host unreachable or ARP blocked)
PERMANENT   — static entry
NOARP       — interface doesn't use ARP
```

**ARP troubleshooting scenarios:**
- **Entry stays INCOMPLETE** → host is down, or a firewall is blocking ARP
- **Entry oscillates between two MACs** → ARP spoofing or misconfigured HSRP/VRRP
- **Correct IP but wrong MAC** → stale entry; flush and retry
- **ARP works but ping fails** → ICMP blocked by firewall (Layer 3 issue)

### 3.2 Spanning Tree Protocol (STP) Diagnostics

STP prevents Layer 2 loops in switched networks. Misconfigured STP is the cause of catastrophic broadcast storms.

```bash
# Cisco IOS
show spanning-tree
show spanning-tree vlan 100
show spanning-tree detail
show spanning-tree inconsistentports

# Linux (bridge)
bridge link show
bridge stp show
```

STP port states:
```
Blocking    — receives BPDUs, does not forward frames (prevents loops)
Listening   — transitioning, sends/receives BPDUs
Learning    — populates MAC table but doesn't forward
Forwarding  — fully operational
Disabled    — administratively shut down
```

**STP failure indicators:**
- **Broadcast storm** — CPU at 100%, switch overwhelmed, loop formed
  - Cause: STP not running, BPDU filter on wrong port, rogue switch
- **Topology change (TC) events** — excessive TCs flush the MAC table constantly → performance degradation
- **Root bridge in wrong location** — traffic takes suboptimal paths
- **PortFast on trunk ports** — never enable PortFast on inter-switch links

```bash
# Check for TC events (Cisco)
show spanning-tree detail | include change
# High "number of topology changes" = problem
```

### 3.3 MAC Address Table Diagnostics

```bash
# Cisco: view MAC table
show mac address-table
show mac address-table dynamic
show mac address-table count
show mac address-table address <mac>
show mac address-table interface GigabitEthernet0/1

# Linux bridge
bridge fdb show
bridge fdb show dev eth0
```

**What to look for:**
- MAC address appearing on multiple ports → loop or ARP spoofing
- No MAC entries on a port → host isn't sending traffic or port is down
- MAC table full → triggers unknown unicast flooding (broadcasts everything)
- Duplicate MAC addresses → misconfigured VMs or intentional attack

### 3.4 VLAN Diagnostics

```bash
# Cisco: VLAN verification
show vlan brief
show vlan id 100
show interfaces trunk
show interfaces GigabitEthernet0/1 switchport

# Linux: VLAN interfaces
ip link show type vlan
cat /proc/net/vlan/config
vconfig show     # older tool
```

**VLAN mismatch troubleshooting:**
- Host can reach local subnet but not across the network → check VLAN tagging
- Native VLAN mismatch on trunks → Cisco will generate CDP warning
- Trunk port not carrying a VLAN → `show interfaces trunk` doesn't list it under "VLANs allowed and active"

### 3.5 CDP / LLDP (Neighbor Discovery)

```bash
# Cisco CDP
show cdp neighbors
show cdp neighbors detail

# LLDP (standard, works across vendors)
show lldp neighbors
show lldp neighbors detail

# Linux LLDP
lldpctl
lldpctl eth0
```

These protocols reveal:
- Connected device hostname and model
- Port IDs on both ends
- IP address management interfaces
- Capabilities (router, switch, phone)
- VLAN information

CDP/LLDP is invaluable for **mapping unknown network topology**.

---

## 4. Layer 3 — Network Layer Tools (Beyond Ping & Traceroute)

### 4.1 ip / ifconfig — Interface and Route Inspection

```bash
# Modern Linux (iproute2)
ip addr show
ip addr show dev eth0
ip link show
ip route show
ip route show table all    # all routing tables
ip rule show               # policy routing rules
ip neigh show              # ARP/neighbor table

# Check if routing is enabled
sysctl net.ipv4.ip_forward
cat /proc/sys/net/ipv4/ip_forward   # 1 = forwarding enabled

# Show specific route for a destination
ip route get 8.8.8.8
# Output shows exact next-hop and interface used
```

### 4.2 mtr (Matt's Traceroute)

`mtr` combines ping and traceroute into a continuous, real-time display. It is far superior to plain traceroute for identifying **intermittent packet loss** and **jitter** along a path.

```bash
mtr 8.8.8.8
mtr --report --report-cycles 100 8.8.8.8    # 100-packet report
mtr --tcp --port 443 8.8.8.8               # TCP probe (bypasses ICMP blocks)
mtr --udp 8.8.8.8                          # UDP probe
mtr --no-dns 8.8.8.8                       # no DNS lookup (faster)
mtr --interval 0.1 8.8.8.8                 # 100ms interval
```

**Reading mtr output:**
```
                             My traceroute  [v0.95]
Host                        Loss%   Snt   Last   Avg  Best  Wrst StDev
1. 192.168.1.1              0.0%    100    0.4   0.5   0.3   1.2   0.2
2. 10.0.0.1                 0.0%    100    2.1   2.3   1.9   4.1   0.3
3. ???                     100.0%   100    0.0   0.0   0.0   0.0   0.0
4. core1.isp.net            0.0%    100   10.2  10.4   9.8  12.1   0.5
5. 8.8.8.8                  0.0%    100   11.1  11.3  10.9  13.0   0.4
```

**Interpretation rules:**
- Loss at hop N but **not at subsequent hops** → that hop deprioritizes ICMP; NOT a real problem
- Loss at hop N **and all subsequent hops** → real packet loss at hop N
- High `StDev` (standard deviation) → jitter; indicates congestion or unstable link
- `???` with 100% loss but later hops respond → router silently drops TTL-exceeded; normal
- Increasing latency from hop to hop → normal geographic distance
- Sudden 100ms+ jump at a specific hop → congestion or rate limiting at that hop

### 4.3 hping3 — Advanced Packet Crafting

`hping3` is a command-line packet generator. It lets you craft custom packets to test specific behaviors that ping cannot.

```bash
# TCP SYN ping to port 80 (bypasses ICMP firewalls)
hping3 -S -p 80 192.168.1.1

# UDP ping
hping3 --udp -p 53 192.168.1.1

# Traceroute using TCP SYN
hping3 --traceroute -S -p 80 192.168.1.1

# Measure packet loss
hping3 -c 100 -i u1000 192.168.1.1   # 100 packets, 1ms interval

# Fragment packets (test MTU path)
hping3 -f -p 80 192.168.1.1

# Set specific TTL
hping3 --ttl 5 192.168.1.1

# Flood test (dangerous, use responsibly)
hping3 --flood -S -p 80 192.168.1.1
```

### 4.4 nmap — Network Scanning and Port Discovery

```bash
# Host discovery (ping scan, no port scan)
nmap -sn 192.168.1.0/24

# Fast scan top 100 ports
nmap -F 192.168.1.1

# Full TCP SYN scan
nmap -sS 192.168.1.1

# UDP scan (slow but important)
nmap -sU 192.168.1.1

# OS detection and version detection
nmap -O -sV 192.168.1.1

# Comprehensive scan
nmap -A 192.168.1.1

# Scan specific ports
nmap -p 22,80,443,8080 192.168.1.1

# Scan entire subnet, save output
nmap -sn 10.0.0.0/24 -oG sweep.txt

# Test if port is filtered vs closed
nmap --reason -p 22 192.168.1.1
# "filtered" = firewall dropping; "closed" = port unreachable (RST received)
```

**nmap port states:**
- `open` — application actively listening
- `closed` — port reachable but nothing listening (RST received)
- `filtered` — firewall dropping packets; no response
- `unfiltered` — reachable but state unknown
- `open|filtered` — uncertain (common with UDP)

### 4.5 fping — Fast Parallel Ping

```bash
# Ping multiple hosts simultaneously
fping 192.168.1.1 192.168.1.2 192.168.1.3

# Ping entire subnet
fping -g 192.168.1.0/24

# Show only alive hosts
fping -g -a 192.168.1.0/24 2>/dev/null

# Show only unreachable hosts
fping -g -u 192.168.1.0/24 2>/dev/null

# Continuous ping with summary statistics
fping -l -c 100 192.168.1.1
```

### 4.6 pathping (Windows)

Windows-native tool combining ping + traceroute with statistical analysis:

```cmd
pathping 8.8.8.8
pathping /n 8.8.8.8      # no DNS resolution
pathping /q 50 8.8.8.8   # 50 queries per hop
```

---

## 5. Layer 4 — Transport Layer Diagnostics

### 5.1 netstat — Connection and Socket State

```bash
# All listening ports and established connections
netstat -tunapl

# Flags breakdown:
# -t = TCP
# -u = UDP
# -n = numeric (no DNS)
# -a = all states
# -p = show process/PID
# -l = listening only

# Statistics per protocol
netstat -s

# Interface statistics
netstat -i

# Routing table
netstat -r
```

### 5.2 ss — Modern Socket Statistics (Replacement for netstat)

`ss` is faster and more feature-rich than `netstat`. Always prefer `ss` on modern Linux.

```bash
# All TCP sockets
ss -t

# All listening sockets
ss -ltn

# Connections to a specific port
ss -tn dst :443

# Connections from a specific IP
ss -tn src 192.168.1.100

# Show socket memory usage (important for high-traffic servers)
ss -tm

# Filter by state
ss -t state established
ss -t state time-wait
ss -t state syn-recv

# Show timer info (retransmit counts)
ss -to

# Full detail including socket options
ss -ti
```

**TCP States and What They Mean:**
```
LISTEN      → waiting for incoming connection
SYN_SENT    → initiator sent SYN, waiting for SYN-ACK
SYN_RECV    → server received SYN, sent SYN-ACK, waiting for ACK
ESTABLISHED → fully connected session
FIN_WAIT_1  → initiator sent FIN (closing)
FIN_WAIT_2  → received ACK for FIN, waiting for remote FIN
CLOSE_WAIT  → received FIN from remote, waiting for local app to close
LAST_ACK    → sent FIN, waiting for final ACK
TIME_WAIT   → waiting 2×MSL before socket fully closed
CLOSED      → socket fully closed
```

**Too many TIME_WAIT?** High-traffic servers accumulate TIME_WAIT for old connections. This is normal but can exhaust ephemeral ports. Tuning: `net.ipv4.tcp_tw_reuse = 1`.

**Too many SYN_RECV?** Possible SYN flood attack or firewall blocking ACK packets.

### 5.3 tcpflow — TCP Session Reconstruction

```bash
# Capture and reconstruct TCP sessions
tcpflow -i eth0 port 80

# Capture to file
tcpflow -i eth0 -o /tmp/flows/ port 80

# Show header information
tcpflow -c -i eth0 port 80
```

### 5.4 nc (netcat) — The TCP/UDP Swiss Army Knife

`nc` is indispensable for manual protocol testing and port reachability verification.

```bash
# Test if TCP port is open
nc -zv 192.168.1.1 22
nc -zv 192.168.1.1 80
nc -zv 192.168.1.1 443

# Test UDP port reachability
nc -zuv 192.168.1.1 53

# Scan a port range
nc -zv 192.168.1.1 20-100

# Simple TCP chat / relay
nc -l 9999              # Server: listen on port 9999
nc 192.168.1.1 9999     # Client: connect

# Transfer a file over TCP
nc -l 9999 > received_file          # Receiver
nc 192.168.1.1 9999 < file_to_send  # Sender

# Connect to HTTP manually
nc 192.168.1.1 80
GET / HTTP/1.0
Host: 192.168.1.1
[Enter twice]

# Test SMTP manually
nc mail.example.com 25
EHLO myhost
MAIL FROM:<test@test.com>
RCPT TO:<user@example.com>
```

### 5.5 iperf3 — Bandwidth and Performance Testing

`iperf3` measures raw TCP/UDP throughput between two hosts.

```bash
# Server side
iperf3 -s

# Client side: TCP test
iperf3 -c 192.168.1.1

# UDP test with target bandwidth
iperf3 -c 192.168.1.1 -u -b 100M

# Bidirectional test
iperf3 -c 192.168.1.1 --bidir

# Longer duration (60 seconds)
iperf3 -c 192.168.1.1 -t 60

# Multiple parallel streams (saturate bonded links)
iperf3 -c 192.168.1.1 -P 4

# Reverse mode (server sends to client)
iperf3 -c 192.168.1.1 -R

# Adjust TCP window size
iperf3 -c 192.168.1.1 -w 512K

# JSON output for scripting
iperf3 -c 192.168.1.1 -J
```

**Interpreting iperf3 results:**
- **Bandwidth less than expected** → congestion, duplex mismatch, or route asymmetry
- **High jitter in UDP test** → congestion or QoS problem
- **High packet loss in UDP** → firewall, congestion, or bufferbloat
- **TCP bandwidth climbs slowly** → small TCP window or high RTT (BDP problem: Bandwidth-Delay Product)

---

## 6. Layer 7 — Application Layer Diagnostics

### 6.1 curl — HTTP Diagnostics

```bash
# Verbose HTTP request (shows TLS handshake, headers, timing)
curl -v https://example.com

# Show timing breakdown
curl -w "@curl-format.txt" -o /dev/null -s https://example.com

# curl-format.txt:
#     time_namelookup:  %{time_namelookup}\n
#     time_connect:     %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#     time_pretransfer: %{time_pretransfer}\n
#     time_redirect:    %{time_redirect}\n
#     time_starttransfer: %{time_starttransfer}\n
#     time_total:       %{time_total}\n

# Follow redirects
curl -L https://example.com

# Custom headers
curl -H "Authorization: Bearer TOKEN" https://api.example.com

# POST request
curl -X POST -d '{"key":"value"}' -H "Content-Type: application/json" https://api.example.com

# Skip TLS verification (debugging only)
curl -k https://192.168.1.1

# Show only HTTP response code
curl -o /dev/null -s -w "%{http_code}" https://example.com

# Use specific DNS server
curl --dns-servers 8.8.8.8 https://example.com

# Test with specific TLS version
curl --tls-max 1.2 https://example.com
curl --tlsv1.3 https://example.com
```

**Timing interpretation:**
- `time_namelookup` — DNS resolution time
- `time_connect` — TCP handshake time
- `time_appconnect` — TLS handshake time (for HTTPS)
- `time_starttransfer` — time to first byte (TTFB): server processing time
- `time_total` — full download time

### 6.2 wget — Alternative HTTP Testing

```bash
# Download and show debug info
wget -d https://example.com

# Spider mode (check all links)
wget --spider https://example.com

# Check certificate
wget --server-response https://example.com -O /dev/null

# Test with specific interface
wget --bind-address=192.168.1.100 https://example.com
```

### 6.3 telnet — Raw Protocol Testing

Though largely replaced by `nc`, telnet is still universally available:

```bash
telnet 192.168.1.1 80    # Test HTTP port
telnet 192.168.1.1 25    # Test SMTP
telnet 192.168.1.1 23    # Verify telnet access (should be disabled)
```

---

## 7. Packet Capture & Deep Inspection

### 7.1 tcpdump — The Network Microscope

`tcpdump` is the most powerful command-line packet analysis tool. Mastering it separates competent engineers from great ones.

```bash
# Capture on interface, no DNS, show packet content
tcpdump -i eth0 -nn -v

# Capture to file (for Wireshark analysis later)
tcpdump -i eth0 -w capture.pcap

# Read capture file
tcpdump -r capture.pcap

# Capture only 1000 packets
tcpdump -i eth0 -c 1000 -w capture.pcap

# Rotate capture files (100MB max, keep 10 files)
tcpdump -i eth0 -C 100 -W 10 -w capture.pcap

# Increase snapshot length (default 262144 bytes)
tcpdump -i eth0 -s 0 -w capture.pcap
```

**BPF Filters (Berkeley Packet Filter):**

```bash
# Filter by host
tcpdump host 192.168.1.1
tcpdump src host 192.168.1.1
tcpdump dst host 192.168.1.1

# Filter by port
tcpdump port 80
tcpdump port 80 or port 443

# Filter by protocol
tcpdump icmp
tcpdump tcp
tcpdump udp
tcpdump arp

# Filter by network
tcpdump net 192.168.1.0/24
tcpdump src net 10.0.0.0/8

# TCP flag filters
tcpdump 'tcp[tcpflags] == tcp-syn'          # only SYN packets
tcpdump 'tcp[tcpflags] & tcp-rst != 0'     # any RST packets
tcpdump 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'  # SYN or RST

# Filter by packet size
tcpdump 'len > 1400'    # large packets (useful for MTU debugging)
tcpdump 'len < 100'     # small packets

# Combine filters
tcpdump -i eth0 'host 192.168.1.1 and port 443 and tcp'

# NOT a host
tcpdump 'not host 192.168.1.1'

# Capture HTTP traffic (not HTTPS)
tcpdump -i eth0 -A 'tcp port 80'   # -A prints ASCII content

# Capture DNS queries
tcpdump -i eth0 udp port 53

# Capture DHCP
tcpdump -i eth0 port 67 or port 68 -nn

# Detect ARP storms
tcpdump -i eth0 -n arp | head -50
```

**Reading tcpdump output:**

```
14:23:01.123456 IP 192.168.1.100.52341 > 192.168.1.1.80: Flags [S], seq 1234567890, win 65535, options [mss 1460,sackOK,TS val 123 ecr 0,nop,wscale 7], length 0

Explanation:
  14:23:01.123456     → timestamp (microsecond precision)
  192.168.1.100.52341 → source IP and port
  192.168.1.1.80      → destination IP and port
  Flags [S]           → TCP flags (S=SYN, A=ACK, F=FIN, R=RST, P=PUSH, U=URG)
  seq 1234567890      → sequence number
  win 65535           → TCP window size
  length 0            → payload length
```

**TCP flags in `tcpdump`:**
```
[S]   = SYN
[.]   = ACK (just an acknowledgment)
[S.]  = SYN-ACK
[F.]  = FIN-ACK
[R.]  = RST-ACK
[P.]  = PUSH-ACK (data transmission)
[R]   = RST (connection reset)
```

### 7.2 Wireshark / tshark — Deep Packet Inspection

**tshark** is the command-line version of Wireshark, usable on servers.

```bash
# Basic capture
tshark -i eth0

# Capture to file
tshark -i eth0 -w capture.pcap

# Read and display pcap
tshark -r capture.pcap

# Filter (uses Wireshark display filter syntax, different from tcpdump BPF)
tshark -r capture.pcap -Y "http"
tshark -r capture.pcap -Y "tcp.flags.syn == 1 && tcp.flags.ack == 0"
tshark -r capture.pcap -Y "dns"
tshark -r capture.pcap -Y "ip.addr == 192.168.1.1"

# Show specific fields
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e tcp.dstport

# Extract HTTP URLs
tshark -r capture.pcap -Y "http.request" -T fields -e http.host -e http.request.uri

# Show TCP stream reconstruction
tshark -r capture.pcap -q -z "follow,tcp,ascii,0"

# Protocol statistics
tshark -r capture.pcap -q -z io,phs

# Conversation statistics
tshark -r capture.pcap -q -z conv,tcp

# Show retransmissions
tshark -r capture.pcap -Y "tcp.analysis.retransmission"

# Decode as specific protocol
tshark -r capture.pcap -d tcp.port==8080,http
```

**Wireshark Display Filter Examples:**

```
tcp.analysis.retransmission        → TCP retransmissions
tcp.analysis.out_of_order          → Out-of-order segments
tcp.analysis.duplicate_ack         → Duplicate ACKs (congestion/loss indicator)
tcp.analysis.zero_window           → Receiver buffer full (flow control)
tcp.analysis.window_full           → Sender's window exhausted
tcp.analysis.fast_retransmission   → Fast retransmit triggered
icmp.type == 3                     → ICMP Destination Unreachable
icmp.code == 4                     → ICMP Fragmentation Needed (MTU discovery)
dns.flags.rcode != 0               → DNS errors
http.response.code >= 400          → HTTP error responses
ssl.alert_message                  → TLS alerts (handshake failures)
arp.duplicate-address-detected     → Duplicate IP detected
```

### 7.3 ngrep — Network grep

```bash
# Search for string in network traffic
ngrep -d eth0 "HTTP/1" tcp port 80

# Case-insensitive search
ngrep -i "password" -d eth0

# DNS query search
ngrep -d eth0 "" udp port 53
```

---

## 8. DNS Diagnostics

DNS failures cause problems that look like connectivity issues. An expert always checks DNS early.

### 8.1 dig — The DNS Analyst's Tool

```bash
# Basic query (A record)
dig example.com

# Query specific record type
dig example.com A
dig example.com AAAA      # IPv6
dig example.com MX        # Mail exchanger
dig example.com NS        # Name servers
dig example.com TXT       # Text records (SPF, DKIM, etc.)
dig example.com SOA       # Start of Authority
dig example.com CNAME     # Canonical name
dig example.com PTR       # Reverse DNS
dig example.com ANY       # All records (often blocked)

# Reverse DNS lookup
dig -x 8.8.8.8

# Query specific DNS server
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# Short answer only
dig +short example.com

# No additional section
dig +noall +answer example.com

# Trace the full DNS resolution path
dig +trace example.com

# Check DNSSEC
dig +dnssec example.com
dig example.com DNSKEY
dig example.com DS

# Show query time
dig example.com | grep "Query time"

# TCP DNS (useful when UDP is blocked or truncated response)
dig +tcp example.com

# Detailed debugging
dig +all example.com
```

**Reading dig output:**
```
;; ANSWER SECTION:
example.com.    3600    IN    A    93.184.216.34
                ^        ^    ^    ^
                TTL      Class Type Value

;; Query time: 23 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)
```

**DNS flags:**
```
QR  → Query/Response (1 = response)
AA  → Authoritative Answer
TC  → Truncated (response exceeds 512 bytes, retry with TCP)
RD  → Recursion Desired
RA  → Recursion Available
AD  → Authenticated Data (DNSSEC)
CD  → Checking Disabled (DNSSEC)
```

**DNS response codes (RCODE):**
```
NOERROR    (0) → success
FORMERR    (1) → malformed query
SERVFAIL   (2) → server failed to process (often DNSSEC validation failure)
NXDOMAIN   (3) → domain does not exist
NOTIMP     (4) → feature not implemented
REFUSED    (5) → server refused query
NOTAUTH    (9) → server not authoritative for zone
```

### 8.2 nslookup

```bash
nslookup example.com           # Basic lookup
nslookup example.com 8.8.8.8   # Using specific DNS server
nslookup -type=MX example.com  # MX records
nslookup -type=NS example.com  # NS records

# Interactive mode
nslookup
> server 8.8.8.8
> set type=any
> example.com
```

### 8.3 host — Simple DNS Lookup

```bash
host example.com
host -t MX example.com
host -a example.com            # all records
host 8.8.8.8                   # reverse lookup
```

### 8.4 resolvectl / systemd-resolve (Modern Linux)

```bash
resolvectl status
resolvectl dns
resolvectl query example.com
resolvectl statistics
resolvectl flush-caches        # flush DNS cache

# Older equivalent
systemd-resolve --status
systemd-resolve --flush-caches
```

### 8.5 DNS Cache Inspection

```bash
# Linux (systemd-resolved cache)
resolvectl statistics

# Windows: flush DNS cache
ipconfig /flushdns
ipconfig /displaydns

# macOS: flush DNS cache
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

---

## 9. Routing & Path Analysis

### 9.1 ip route — Routing Table Analysis

```bash
# Show main routing table
ip route show

# Show specific table
ip route show table 100

# Look up route for specific destination
ip route get 8.8.8.8
# Returns: 8.8.8.8 via 192.168.1.1 dev eth0 src 192.168.1.100 uid 1000

# Show all routing tables
ip route show table all

# Add static route
ip route add 10.0.0.0/8 via 192.168.1.1 dev eth0

# Delete route
ip route del 10.0.0.0/8

# Add default gateway
ip route add default via 192.168.1.1

# Show policy routing rules
ip rule show
```

### 9.2 route (Legacy but Universal)

```bash
route -n         # show routing table, numeric
route -n -A inet6  # IPv6 routing table
```

### 9.3 BGP Diagnostics (Quagga/FRRouting/Cisco)

```bash
# FRRouting (vtysh)
show bgp summary
show bgp neighbors
show bgp neighbors 10.0.0.1 received-routes
show bgp neighbors 10.0.0.1 advertised-routes
show bgp ipv4 unicast
show bgp ipv4 unicast 192.168.0.0/24 longer-prefixes

# Cisco IOS
show ip bgp summary
show ip bgp neighbors
show ip bgp 192.168.0.0/24
show ip bgp regexp _65001_     # routes containing ASN 65001
```

**BGP troubleshooting checklist:**
- Peer stuck in `Active` state → TCP connection failing (firewall, wrong IP, wrong ASN)
- Peer in `Idle` state → BGP not attempting connection (check `neighbor` config)
- Routes not advertised → check `network` statements, route-maps, prefix-lists
- Routes rejected → check `maximum-prefix` limits, prefix-lists, route-maps
- Flapping sessions → MTU mismatch, TCP MD5 authentication failure, interface instability

### 9.4 OSPF Diagnostics

```bash
# Cisco IOS
show ip ospf neighbor
show ip ospf neighbor detail
show ip ospf interface
show ip ospf database
show ip ospf database summary
show ip route ospf

# FRRouting
show ip ospf neighbor
show ip ospf interface
```

**OSPF neighbor states:**
```
Down         → no Hello received
Attempt      → trying to contact (NBMA networks)
Init         → Hello received but router not seen in Hello
2-Way        → bidirectional communication established (DR/BDR election here)
ExStart      → establishing master/slave relationship for DBD exchange
Exchange     → exchanging DBD (database descriptor) packets
Loading      → requesting LSAs
Full         → fully synchronized
```

### 9.5 tracepath — Path MTU Discovery

```bash
tracepath 8.8.8.8

# Output includes MTU at each hop
# Look for "pmtu X" — this shows path MTU at that hop
# If MTU drops → router is fragmenting or dropping oversized packets
```

---

## 10. Firewall & ACL Diagnostics

### 10.1 iptables — Linux Firewall

```bash
# List all rules with packet/byte counters
iptables -L -n -v

# List specific chain
iptables -L INPUT -n -v
iptables -L OUTPUT -n -v
iptables -L FORWARD -n -v

# List NAT rules
iptables -t nat -L -n -v

# List mangle rules
iptables -t mangle -L -n -v

# Show rule line numbers
iptables -L INPUT -n --line-numbers

# Show connection tracking table
conntrack -L
conntrack -L --src 192.168.1.100

# Monitor connection tracking events in real time
conntrack -E

# Check if conntrack table is full (causes packet drops)
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
```

**iptables chain traversal order:**
```
Incoming packet:
  → PREROUTING (nat) → routing decision → FORWARD → POSTROUTING (nat)
                                        ↓
                                     INPUT → local process → OUTPUT → POSTROUTING
```

**Testing specific rules:**
```bash
# Temporarily allow all traffic (isolate firewall as cause)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -F

# Restore rules
iptables-restore < /etc/iptables/rules.v4
```

### 10.2 nftables — Modern Linux Firewall

```bash
# List all rules
nft list ruleset

# List specific table
nft list table ip filter

# Show counter data
nft list table ip filter -a
```

### 10.3 ufw — UFW Frontend

```bash
ufw status verbose
ufw status numbered
```

### 10.4 Cisco ACL Verification

```bash
# Show ACL hit counts
show ip access-lists
show ip access-lists ACL_NAME

# Show interface ACL assignments
show ip interface GigabitEthernet0/1

# ACL log analysis
show logging | include PERMIT|DENY

# Packet tracer (simulates packet through device)
debug ip packet detail         # CAUTION: high CPU on busy routers
```

---

## 11. Interface & Link Statistics

### 11.1 watch + ip — Real-Time Counter Monitoring

```bash
# Monitor interface stats every second
watch -n 1 'ip -s link show eth0'

# Monitor RX/TX counters
watch -n 1 'cat /proc/net/dev'
```

### 11.2 /proc/net Filesystem

```bash
# Interface statistics
cat /proc/net/dev

# TCP statistics
cat /proc/net/snmp

# UDP statistics  
cat /proc/net/udp

# ARP table
cat /proc/net/arp

# Routing table
cat /proc/net/route

# Connection tracking
cat /proc/net/nf_conntrack

# TCP socket states
cat /proc/net/tcp
cat /proc/net/tcp6
```

### 11.3 sar — System Activity Reporter

```bash
# Network interface statistics
sar -n DEV 1 10    # 10 samples, 1 second interval
sar -n EDEV 1 10   # Error statistics
sar -n TCP 1 10    # TCP statistics
sar -n UDP 1 10    # UDP statistics
sar -n SOCK 1 10   # Socket statistics

# Historical data
sar -n DEV -f /var/log/sa/sa15   # data from 15th of month
```

### 11.4 vnstat — Long-Term Bandwidth Monitoring

```bash
vnstat               # Summary statistics
vnstat -l            # Live mode
vnstat -h            # Hourly statistics
vnstat -d            # Daily statistics
vnstat -m            # Monthly statistics
vnstat -i eth0       # Specific interface
vnstat --exportjson  # Export as JSON for scripting
```

---

## 12. Network Performance Benchmarking

### 12.1 BDP — Bandwidth-Delay Product

Understanding TCP throughput requires understanding BDP:

```
BDP = Bandwidth × RTT

Example:
  1 Gbps link, 100ms RTT:
  BDP = 1,000,000,000 bits/sec × 0.1 sec = 100,000,000 bits = 12.5 MB

The TCP send window must be at LEAST as large as BDP for full throughput.
Default TCP window (65,535 bytes = 64 KB) limits throughput on high-latency links:
  64 KB / 0.1 sec = 655 Kbps — far below 1 Gbps link capacity!

Solution: TCP window scaling (RFC 1323), enabled by default on Linux:
  sysctl net.ipv4.tcp_window_scaling = 1
  sysctl net.ipv4.tcp_rmem
  sysctl net.ipv4.tcp_wmem
```

### 12.2 TCP Tuning Parameters

```bash
# Show current TCP buffer sizes (min, default, max in bytes)
sysctl net.ipv4.tcp_rmem    # receive buffer
sysctl net.ipv4.tcp_wmem    # send buffer

# Enable window scaling
sysctl net.ipv4.tcp_window_scaling

# TCP congestion control algorithm
sysctl net.ipv4.tcp_congestion_control

# Available algorithms
cat /proc/sys/net/ipv4/tcp_available_congestion_control

# Enable BBR (Bottleneck Bandwidth and RTT) — Google's modern CC algorithm
modprobe tcp_bbr
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Check retransmit timeout
sysctl net.ipv4.tcp_retries2

# Keepalive settings
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_intvl
sysctl net.ipv4.tcp_keepalive_probes
```

### 12.3 qperf — Latency and Bandwidth Testing (RDMA-aware)

```bash
qperf 192.168.1.1 tcp_bw tcp_lat udp_bw udp_lat
```

### 12.4 netperf

```bash
# Server
netserver

# Client TCP throughput
netperf -H 192.168.1.1 -t TCP_STREAM

# Client UDP throughput
netperf -H 192.168.1.1 -t UDP_STREAM

# TCP request-response (latency)
netperf -H 192.168.1.1 -t TCP_RR
```

---

## 13. Wireless Network Diagnostics

### 13.1 iwconfig / iwlist (Legacy)

```bash
iwconfig wlan0               # show wireless parameters
iwlist wlan0 scan            # scan for networks
iwlist wlan0 frequency       # show available channels
iwlist wlan0 rate            # show supported bitrates
```

### 13.2 iw — Modern Wireless Tool

```bash
# Interface information
iw dev
iw dev wlan0 info

# Link quality and signal strength
iw dev wlan0 link
# Output: signal -65 dBm, tx bitrate 300.0 MBit/s, rx bitrate 270.0 MBit/s

# Station statistics (associated clients, if AP mode)
iw dev wlan0 station dump

# Scan for networks
iw dev wlan0 scan
iw dev wlan0 scan | grep -E "SSID|signal|channel|freq"

# Monitor mode (for packet capture)
ip link set wlan0 down
iw dev wlan0 set monitor none
ip link set wlan0 up

# Regulatory domain (affects available channels)
iw reg get
iw reg set US
```

### 13.3 Signal Strength Interpretation

```
Signal Strength (dBm):
  > -50 dBm  → Excellent (very close to AP)
  -50 to -60 → Good
  -60 to -70 → Fair (usable)
  -70 to -80 → Weak (degraded performance)
  < -80 dBm  → Very poor (likely drops and disconnections)

Signal-to-Noise Ratio (SNR):
  > 40 dB → Excellent
  25-40   → Very good
  15-25   → Low quality (errors possible)
  < 10 dB → Unusable

Channel Interference Check:
  2.4 GHz: Use channels 1, 6, or 11 (non-overlapping)
  5 GHz: More channels available, less interference
  6 GHz (Wi-Fi 6E): Clean spectrum, minimal legacy interference
```

### 13.4 wavemon — Wireless Monitor

```bash
wavemon -i wlan0    # ncurses-based real-time wireless monitor
```

### 13.5 Wireless Packet Capture

```bash
# Set interface to monitor mode
airmon-ng start wlan0          # creates wlan0mon
tcpdump -i wlan0mon -w wifi.pcap

# Or using iw
iw dev wlan0 interface add wlan0mon type monitor
ip link set wlan0mon up
tcpdump -i wlan0mon
```

---

## 14. DHCP & ARP Diagnostics

### 14.1 DHCP Client Diagnostics

```bash
# Manually request DHCP lease (Linux)
dhclient -v eth0

# Release and renew
dhclient -r eth0    # release
dhclient eth0       # request new lease

# Using dhcpcd
dhcpcd -d eth0      # debug mode

# Using systemd-networkd
networkctl status eth0

# Check DHCP lease file
cat /var/lib/dhclient/dhclient.leases
cat /var/lib/dhcpcd/dhcpcd-eth0.lease

# Capture DHCP exchange
tcpdump -i eth0 -n port 67 or port 68

# DHCP packet types visible in capture:
# 1 = DHCPDISCOVER  (client broadcast, looking for server)
# 2 = DHCPOFFER     (server offers IP)
# 3 = DHCPREQUEST   (client accepts offer)
# 5 = DHCPACK       (server confirms)
# 6 = DHCPNAK       (server rejects — IP conflict or lease expired)
# 7 = DHCPRELEASE   (client releases)
# 8 = DHCPINFORM    (client already has IP, needs config only)
```

### 14.2 DHCP Server Diagnostics

```bash
# ISC DHCP Server
cat /var/lib/dhcpd/dhcpd.leases
journalctl -u isc-dhcp-server -f

# Show active leases
dhcp-lease-list

# dnsmasq
cat /var/lib/misc/dnsmasq.leases
journalctl -u dnsmasq -f
```

### 14.3 ARP Probing & Conflict Detection

```bash
# arping — send ARP requests and receive replies
arping -I eth0 192.168.1.1    # ping via ARP (Layer 2)
arping -I eth0 -c 3 192.168.1.1

# Check for duplicate IP address
arping -D -I eth0 192.168.1.100
# Exit code 0 = no duplicate; exit code 1 = duplicate found

# Gratuitous ARP (announce IP/MAC to network)
arping -I eth0 -B 192.168.1.100   # broadcast gratuitous ARP

# arp-scan — network ARP sweep
arp-scan --interface=eth0 --localnet
arp-scan 192.168.1.0/24
```

---

## 15. SSL/TLS Diagnostics

### 15.1 openssl — TLS Handshake Analysis

```bash
# Full TLS connection test
openssl s_client -connect example.com:443

# Specify TLS version
openssl s_client -tls1_2 -connect example.com:443
openssl s_client -tls1_3 -connect example.com:443

# Show certificate chain
openssl s_client -connect example.com:443 -showcerts

# Check certificate details
openssl s_client -connect example.com:443 | openssl x509 -text -noout

# Check certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates

# Test specific cipher suite
openssl s_client -connect example.com:443 -cipher AES256-SHA

# Test STARTTLS (SMTP, IMAP, FTP)
openssl s_client -starttls smtp -connect mail.example.com:587
openssl s_client -starttls imap -connect mail.example.com:143

# Verify certificate against CA bundle
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt cert.pem

# Decode certificate file
openssl x509 -in cert.pem -text -noout

# Check certificate's Subject Alternative Names
openssl x509 -in cert.pem -text -noout | grep -A 3 "Subject Alternative Name"

# Test SNI (Server Name Indication)
openssl s_client -connect example.com:443 -servername example.com
```

### 15.2 testssl.sh — Comprehensive TLS Scanner

```bash
# Download testssl.sh
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh example.com:443
./testssl.sh --severity HIGH example.com:443   # show only HIGH+ severity issues
./testssl.sh --heartbleed example.com:443       # test specific vulnerability
```

### 15.3 Common TLS Failures

```
SSL_ERROR_RX_RECORD_TOO_LONG  → Usually means HTTP port used for HTTPS
certificate verify failed      → Expired cert, wrong CA, or hostname mismatch
SSL3_GET_SERVER_CERTIFICATE: certificate verify failed → Untrusted CA
sslv3 alert handshake failure → Client/server TLS version mismatch
TLSV1_ALERT_PROTOCOL_VERSION  → Server doesn't support requested TLS version
No shared cipher              → No compatible cipher suites
```

---

## 16. Network Monitoring & SNMP

### 16.1 SNMP — Simple Network Management Protocol

SNMP is the foundation of network device monitoring. Devices expose metrics via a **MIB (Management Information Base)** — a tree-structured database of variables.

```bash
# Query a device (SNMPv2c)
snmpwalk -v2c -c public 192.168.1.1

# Get specific OID
snmpget -v2c -c public 192.168.1.1 sysDescr.0
snmpget -v2c -c public 192.168.1.1 1.3.6.1.2.1.1.1.0

# Walk entire MIB subtree
snmpwalk -v2c -c public 192.168.1.1 interfaces

# Check interface counters via SNMP
snmpwalk -v2c -c public 192.168.1.1 ifTable
snmpwalk -v2c -c public 192.168.1.1 ifInOctets
snmpwalk -v2c -c public 192.168.1.1 ifOutOctets
snmpwalk -v2c -c public 192.168.1.1 ifInErrors
snmpwalk -v2c -c public 192.168.1.1 ifOutErrors

# CPU and memory
snmpget -v2c -c public 192.168.1.1 enterprises.9.2.1.57.0  # Cisco CPU 5min avg

# SNMPv3 (encrypted, authenticated)
snmpwalk -v3 -u admin -l authPriv -a SHA -A authpass -x AES -X privpass 192.168.1.1

# Test SNMP connectivity
snmpstatus -v2c -c public 192.168.1.1
```

**Important SNMP OID categories:**
```
System:     1.3.6.1.2.1.1      → sysDescr, sysUpTime, sysName
Interfaces: 1.3.6.1.2.1.2      → ifTable (speed, counters, errors)
IP:         1.3.6.1.2.1.4      → routing table, IP statistics
TCP:        1.3.6.1.2.1.6      → TCP connections, statistics
UDP:        1.3.6.1.2.1.7      → UDP statistics
ICMP:       1.3.6.1.2.1.5      → ICMP statistics
Entities:   1.3.6.1.2.1.47     → hardware components
```

### 16.2 Monitoring Platforms

Understanding these tools is critical even if you don't administer them:

**Prometheus + Grafana:**
- Prometheus scrapes metrics from exporters (node_exporter, snmp_exporter, etc.)
- Grafana visualizes them
- `node_exporter` exposes Linux system metrics including all network counters

```bash
# Query Prometheus directly
curl "http://localhost:9090/api/v1/query?query=node_network_receive_bytes_total"
curl "http://localhost:9090/api/v1/query?query=rate(node_network_receive_bytes_total[5m])"
```

**Nagios/Zabbix:** Active and passive checks, alerting on thresholds.

**ntopng:** Real-time traffic analysis with protocol breakdown, flow tracking.

**Netflow/sFlow/IPFIX:** Flow-based traffic analysis (not packet capture):
- Routers/switches export summarized flow data
- Tools: nfdump, ntopng, SolarWinds, PRTG
- Shows who is talking to whom, how much, which applications

```bash
# nfdump: analyze netflow captures
nfdump -R /var/flows/ -s ip/bytes -n 20   # top 20 talkers by bytes
nfdump -R /var/flows/ -A srcip,dstip -n 100 'src ip 10.0.0.0/8'
```

---

## 17. Logs & Syslog Analysis

### 17.1 Linux System Logs

```bash
# Real-time kernel messages (network driver events)
dmesg | grep -i eth
dmesg | grep -i link
dmesg | tail -f
journalctl -k -f             # kernel journal, follow

# Network-related systemd logs
journalctl -u NetworkManager -f
journalctl -u systemd-networkd -f

# Firewall logs
journalctl | grep -i 'iptables\|nftables\|firewall'

# DHCP logs
journalctl -u isc-dhcp-server
journalctl -u dnsmasq

# Interface events in dmesg output:
# "eth0: NIC Link is Up" → physical link established
# "eth0: NIC Link is Down" → physical link lost (cable or SFP issue)
# "eth0: renamed from eth1" → udev renaming event
# "ADDRCONF(NETDEV_UP): eth0: link is not ready" → waiting for link
```

### 17.2 Cisco/Juniper Syslog Analysis

```bash
# Cisco IOS
show logging
show logging | include %LINK|%LINEPROTO|%BGP|%OSPF|%STP
debug ip packet
terminal monitor    # show debug to SSH session

# Common syslog messages:
# %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
# %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to down
# %BGP-5-ADJCHANGE: neighbor 10.0.0.1 Down Peer closed the session
# %OSPF-5-ADJCHG: Process 1, Nbr 10.0.0.2 on GigabitEthernet0/1 from FULL to DOWN
# %STP-2-TOPOLOGY_CHANGE: detected topology change
# %SEC-6-IPACCESSLOGP: list ACL_IN denied tcp 10.0.0.1(1234) -> 192.168.1.1(80)
```

### 17.3 Log Aggregation Tools

```bash
# grep with context
grep -A 5 -B 5 "error" /var/log/syslog

# Search compressed logs
zgrep "error" /var/log/syslog.2.gz

# awk for log parsing
awk '/OSPF/ {print $0}' /var/log/syslog

# lnav — advanced log viewer
lnav /var/log/syslog

# journalctl queries
journalctl --since "2024-01-01 00:00:00" --until "2024-01-01 01:00:00"
journalctl -p err -n 100    # last 100 error-level messages
```

---

## 18. Vendor-Specific CLI Diagnostics (Cisco, Juniper, Linux)

### 18.1 Cisco IOS / IOS-XE

```bash
# Basic system info
show version
show inventory
show environment all

# Interface diagnostics
show interfaces
show interfaces GigabitEthernet0/1
show interfaces GigabitEthernet0/1 counters
show interfaces GigabitEthernet0/1 status
show ip interface brief         # summary of all interfaces

# Routing diagnostics
show ip route
show ip route 192.168.1.0
show ip route summary

# Connectivity
ping 8.8.8.8
ping 8.8.8.8 repeat 100 size 1500   # test with large packets
ping 8.8.8.8 source GigabitEthernet0/1

# Traceroute with source selection
traceroute 8.8.8.8 source GigabitEthernet0/1

# CDP / LLDP
show cdp neighbors detail
show lldp neighbors detail

# CPU and memory
show processes cpu sorted
show processes memory sorted

# Packet debugging (CAREFUL on production)
debug ip packet detail
debug ip icmp
undebug all    # always run after debugging

# Access list logging
show ip access-lists
show logging | include denied

# VPN diagnostics
show crypto isakmp sa
show crypto ipsec sa
show crypto map

# STP
show spanning-tree
show spanning-tree detail
show spanning-tree inconsistentports
```

### 18.2 Cisco IOS-XR

```bash
show interfaces brief
show route ipv4
show bgp summary
show ospf neighbor
show platform
show environment temperature
show controllers GigabitEthernet0/0/0/0
show interfaces GigabitEthernet0/0/0/0 accounting
```

### 18.3 Juniper JunOS

```bash
# Interface info
show interfaces
show interfaces ge-0/0/0 detail
show interfaces ge-0/0/0 statistics
show interfaces ge-0/0/0 extensive    # most detailed

# Routing
show route
show route 192.168.1.0/24
show route detail

# BGP
show bgp summary
show bgp neighbor 10.0.0.1
show bgp neighbor 10.0.0.1 routes
show bgp neighbor 10.0.0.1 advertised-routes

# OSPF
show ospf neighbor
show ospf neighbor detail
show ospf database

# Diagnostics
ping 8.8.8.8 count 100 size 1500 rapid
traceroute 8.8.8.8

# STP
show spanning-tree bridge
show spanning-tree interface

# ARP
show arp

# Chassis/hardware
show chassis hardware
show chassis environment
show chassis fpc detail   # line card status
```

### 18.4 Linux Networking (iproute2 Complete Reference)

```bash
# Comprehensive interface dump
ip -details -statistics link show

# IP address management
ip addr
ip addr add 192.168.1.10/24 dev eth0
ip addr del 192.168.1.10/24 dev eth0

# Link management
ip link set eth0 up
ip link set eth0 down
ip link set eth0 mtu 9000         # jumbo frames
ip link set eth0 promisc on       # promiscuous mode

# VLAN interfaces
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up

# Bonding/LAG
ip link add bond0 type bond
ip link set bond0 type bond mode active-backup
ip link set eth0 master bond0

# Route management
ip route add 10.0.0.0/8 via 192.168.1.1
ip route change default via 192.168.1.1 dev eth0

# Network namespaces (for isolation testing)
ip netns add testns
ip netns exec testns ip link show
ip link set eth1 netns testns
```

---

## 19. Systematic Troubleshooting Methodology

### 19.1 The Scientific Method Applied to Networking

1. **Observe** — collect symptoms precisely
2. **Hypothesize** — form a specific hypothesis (not a vague guess)
3. **Predict** — if hypothesis is correct, what should you see?
4. **Test** — run one test that either confirms or refutes
5. **Analyze** — did results match prediction?
6. **Iterate** — refine hypothesis and repeat

The key discipline: **test one variable at a time**. Engineers who change multiple things simultaneously cannot determine what fixed the problem.

### 19.2 The Information Gathering Phase

Before running any command, collect:

```
1. Symptom description:
   - What exactly fails? (no connectivity? slow? intermittent?)
   - What error messages appear?
   - What works vs. what doesn't?

2. Scope analysis:
   - One host? Multiple hosts? All hosts?
   - One direction? Both directions?
   - One protocol? All protocols?
   - One VLAN? All VLANs?
   - One site? Multiple sites?

3. Timeline:
   - When did it start?
   - Is it constant or periodic?
   - Any recent changes? (config, hardware, software, physical plant)

4. Baseline comparison:
   - What is normal for this environment?
   - Do you have monitoring data from before the incident?
```

### 19.3 The Layer-by-Layer Verification Checklist

```
Layer 1 — Physical:
  ✓ Cable plugged in? LED status?
  ✓ Interface shows link up? (ethtool, show interfaces)
  ✓ Speed and duplex correct? No mismatch?
  ✓ SFP DOM readings normal?
  ✓ Error counters clean? (CRC, runts, giants)

Layer 2 — Data Link:
  ✓ MAC address table populated?
  ✓ Correct VLAN configured?
  ✓ Trunk ports passing VLANs?
  ✓ No STP blocking on wrong port?
  ✓ ARP resolving correctly?

Layer 3 — Network:
  ✓ IP address correct?
  ✓ Subnet mask correct?
  ✓ Default gateway reachable? (ping gateway)
  ✓ Route to destination exists?
  ✓ No blackhole routes?

Layer 4 — Transport:
  ✓ Port is open? (nc -zv)
  ✓ Firewall not blocking?
  ✓ Service actually listening? (ss -ltn)
  ✓ Connection states healthy?

Layer 7 — Application:
  ✓ Service running? (systemctl status)
  ✓ Config file correct?
  ✓ Certificate valid?
  ✓ DNS resolving correctly?
  ✓ Authentication working?
```

### 19.4 Common Failure Patterns and Immediate Tests

| Symptom | First Test | Likely Cause |
|---|---|---|
| Cannot ping gateway | `ip route show`, `ip neigh show` | No route, ARP failure, wrong gateway |
| Can ping IP, cannot reach hostname | `dig hostname` | DNS failure |
| Can reach some hosts, not others | `traceroute` to both | Routing asymmetry or ACL |
| Slow in one direction only | `iperf3 -R` vs normal | Asymmetric congestion or rate limit |
| Intermittent drops | `mtr --report -c 200` | Physical instability or congestion |
| High latency to specific hop | `mtr`, `tcpdump` for ICMP | QoS policy rate-limiting ICMP |
| TCP works, UDP doesn't | Port-specific `nc -zu` | Firewall UDP block |
| HTTPS fails, HTTP works | `openssl s_client` | Certificate or TLS config issue |
| New VLAN unreachable | `show interfaces trunk` | VLAN not allowed on trunk |
| Everything down on segment | `tcpdump` for broadcasts | Broadcast storm / loop |

---

## 20. Advanced Concepts: MTU, Fragmentation, Jitter, QoS

### 20.1 MTU and Path MTU Discovery (PMTUD)

MTU (Maximum Transmission Unit) is the largest frame that can be sent without fragmentation.

```
Standard Ethernet MTU:   1500 bytes (Layer 3 payload)
Jumbo frames:            9000 bytes (requires end-to-end support)
PPPoE overhead:          8 bytes (effective MTU becomes 1492)
VXLAN overhead:          50 bytes (effective MTU needs to be ≥1550 for 1500 inner)
IPSec overhead:          50–70 bytes depending on cipher
GRE overhead:            24 bytes
MPLS per-label:          4 bytes per label
```

**Testing effective path MTU:**

```bash
# Ping with Don't Fragment bit and specific size
ping -M do -s 1472 192.168.1.1     # 1472 + 28 (ICMP+IP headers) = 1500
ping -M do -s 1400 192.168.1.1
ping -M do -s 1460 192.168.1.1

# Binary search for exact MTU:
# If 1472 fails but 1400 works → MTU is between 1400 and 1472
# Test 1436 → if works, test 1454 → binary search to find exact limit

# Check MTU on interface
ip link show eth0 | grep mtu

# Set MTU
ip link set eth0 mtu 1400

# tracepath discovers path MTU automatically
tracepath 8.8.8.8
```

**PMTUD failure:** When a router drops an oversized packet and sends back `ICMP Type 3, Code 4` (Fragmentation Needed), but a firewall blocks ICMP → PMTUD breaks → TCP sessions hang after small exchanges (the "black hole" problem).

```bash
# Detect PMTUD black holes
# Symptom: small HTTP requests work, large file transfers hang

# Fix: MSS clamping on Linux
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu

# Or set a fixed MSS
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --set-mss 1452
```

### 20.2 Jitter and Latency Analysis

**Jitter** = variation in packet delay. It destroys real-time communications (VoIP, video conferencing, gaming).

```bash
# Measure jitter with ping
ping -c 100 -i 0.1 192.168.1.1 | tail -1
# Output: rtt min/avg/max/mdev = 1.234/1.456/2.101/0.198 ms
# mdev = mean deviation ≈ jitter

# UDP jitter test with iperf3
iperf3 -c 192.168.1.1 -u -b 10M -t 30
# Shows jitter in milliseconds per UDP stream

# Detailed RTT histogram
ping -c 1000 -i 0.01 192.168.1.1 | grep -oP 'time=\K[0-9.]+' | awk '
  {sum+=$1; sumsq+=$1*$1; n++}
  END {
    avg=sum/n;
    variance=sumsq/n - avg*avg;
    print "avg:", avg, "ms | jitter:", sqrt(variance), "ms"
  }'
```

**Jitter sources:**
- Network congestion (queue buildup)
- CPU load on routers (interrupt coalescing)
- Wireless interference (retransmissions)
- Bufferbloat (oversized router buffers)
- Temperature-related hardware instability

### 20.3 QoS (Quality of Service) Diagnostics

```bash
# Linux Traffic Control (tc)
tc qdisc show dev eth0         # show queuing disciplines
tc class show dev eth0         # show traffic classes
tc filter show dev eth0        # show classification rules
tc -s qdisc show dev eth0      # with statistics (drops, backlog)

# Check DSCP markings in captured traffic
tcpdump -i eth0 -nn -v 'ip' | grep "tos"
# tos 0x10 = DSCP EF (Expedited Forwarding, for VoIP)
# tos 0x00 = Best effort

# Check if packets are being marked/remarked
tshark -r capture.pcap -T fields -e ip.dsfield.dscp

# Common DSCP values:
# EF  (46/0xb8) → Voice (< 1% loss, < 150ms latency, < 30ms jitter)
# AF41 (34)     → Interactive video
# AF31 (26)     → Mission critical data
# CS0 (0)       → Best effort (default)
```

### 20.4 Bufferbloat

Bufferbloat occurs when routers have excessively large buffers that fill up during congestion, causing latency to spike while preventing packet loss.

```bash
# Detect bufferbloat
# Download a file with constant throughput, simultaneously ping
# If ping RTT increases dramatically during download → bufferbloat

# Test using netperf
netperf -H 192.168.1.1 -t TCP_STREAM &    # saturate link
ping -i 0.2 192.168.1.1                   # watch RTT increase

# Use the Bufferbloat.net tool: https://www.waveform.com/tools/bufferbloat

# Mitigation: CoDel / FQ-CoDel / CAKE queuing disciplines
tc qdisc replace dev eth0 root fq_codel
tc qdisc replace dev eth0 root cake bandwidth 100Mbit
```

---

## 21. Security-Oriented Diagnostics

### 21.1 Network Reconnaissance Detection

```bash
# Detect port scans in logs
grep "SCAN\|nmap\|SYN flood" /var/log/syslog

# Detect with iptables logging
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j LOG --log-prefix "NULL_SCAN: "
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j LOG --log-prefix "XMAS_SCAN: "

# Monitor for SYN flood
watch -n 1 'ss -t state syn-recv | wc -l'
netstat -s | grep -i "syn\|cookies"

# Detect ARP spoofing
arpwatch -i eth0                # daemon that monitors ARP changes
arp-scan --localnet | sort -t' ' -k1,1 | uniq -d -f 1    # find duplicate IPs
```

### 21.2 netstat / ss for Security Monitoring

```bash
# Find unexpected listening services
ss -ltnp | grep -v '127.0.0.1\|::1'     # external listeners

# Find connections to suspicious ports
ss -tn | awk '{print $5}' | grep -v 'Local\|Peer' | cut -d: -f2 | sort | uniq -c | sort -rn

# Check for unusual foreign connections
ss -tn state established | grep -v '192.168\|10\.\|172\.'

# Identify process behind a connection
ss -tnp | grep <port>
```

### 21.3 Promiscuous Mode Detection

```bash
# Check if interface is in promiscuous mode (potential sniffer)
ip link show | grep PROMISC
ifconfig | grep PROMISC

# Check all interfaces
for i in $(ip link | grep '^[0-9]' | awk '{print $2}' | tr -d ':'); do
  ip link show $i | grep -q PROMISC && echo "$i is in promiscuous mode"
done
```

### 21.4 Traffic Analysis for Anomalies

```bash
# Top talkers using tcpdump
tcpdump -i eth0 -nn -q -c 10000 2>/dev/null | awk '{print $3}' | \
  cut -d. -f1-4 | sort | uniq -c | sort -rn | head -20

# Check for DNS exfiltration (unusually long DNS names)
tcpdump -i eth0 udp port 53 -l | grep -E '[a-z0-9]{30,}\.'

# Check for ICMP tunneling (large ICMP payloads)
tcpdump -i eth0 icmp and 'len > 100'

# Check for suspicious outbound connections on high ports
ss -tn state established | awk '{print $5}' | grep -E ':[0-9]{4,5}$' | \
  sort | uniq -c | sort -rn
```

---

## 22. Tool Reference Cheat Sheet

### By Layer

| Layer | Tool | Primary Use |
|---|---|---|
| 1 | `ethtool` | Physical link, speed, duplex, error counters |
| 1 | `ethtool -m` | SFP/transceiver DOM (optical power) |
| 1 | TDR/OTDR | Cable fault location |
| 2 | `arp`, `ip neigh` | ARP table inspection |
| 2 | `arping` | Layer 2 reachability, duplicate IP detection |
| 2 | `arp-scan` | Network-wide ARP sweep |
| 2 | `bridge fdb show` | MAC forwarding table (Linux bridge) |
| 2 | `show spanning-tree` | STP state and topology |
| 2 | `show cdp/lldp` | Neighbor discovery |
| 3 | `ping` | ICMP reachability and RTT |
| 3 | `traceroute` | Path tracing |
| 3 | `mtr` | Combined path tracing + packet loss stats |
| 3 | `ip route` | Routing table |
| 3 | `ip route get` | Specific route lookup |
| 3 | `hping3` | Custom packet crafting |
| 3 | `fping` | Fast parallel host sweep |
| 3 | `nmap` | Port scanning, OS detection |
| 3 | `tracepath` | Path MTU discovery |
| 4 | `ss` | Socket and connection state |
| 4 | `netstat` | Legacy socket stats |
| 4 | `nc` | Port testing, raw protocol interaction |
| 4 | `iperf3` | Throughput and jitter benchmarking |
| 4 | `tcpflow` | TCP stream reconstruction |
| 7 | `dig` | DNS queries, DNSSEC |
| 7 | `nslookup` | DNS lookup |
| 7 | `curl` | HTTP with timing breakdown |
| 7 | `openssl s_client` | TLS handshake, certificate inspection |
| All | `tcpdump` | Packet capture and filtering |
| All | `tshark` | Deep packet analysis (Wireshark CLI) |
| All | `wireshark` | GUI packet analysis |

### By Problem Type

| Problem | Primary Tools |
|---|---|
| No connectivity at all | `ethtool`, `ip link`, `ip addr`, `ip route` |
| Can ping IP, not name | `dig`, `nslookup`, `resolvectl` |
| Intermittent packet loss | `mtr`, `iperf3 -u`, `ping` long-term |
| Slow throughput | `iperf3`, `ethtool` (duplex check), `ss -to` (retransmits) |
| High latency | `mtr`, `traceroute`, `ping` statistics |
| Port unreachable | `nc -zv`, `nmap`, `ss -ltn`, `iptables -L -v` |
| TLS/HTTPS failure | `openssl s_client`, `curl -v`, `testssl.sh` |
| DHCP not working | `tcpdump port 67 or 68`, `dhclient -v` |
| VLAN not reachable | `show interfaces trunk`, `ip link show type vlan` |
| STP loop | `tcpdump arp`, `show spanning-tree`, monitoring CPU |
| BGP not establishing | `show bgp summary`, `ping` peer, check ASN, firewall |
| OSPF neighbor not forming | `show ospf neighbor`, verify hello timers, MTU |
| MTU black hole | `ping -M do -s SIZE`, `tracepath`, MSS clamping |
| ARP conflict | `arping -D`, `arpwatch`, `ip neigh show` |

### Quick Command Reference

```bash
# One-liners for rapid triage

# What's listening?
ss -ltnp

# What connections are established?
ss -tnp state established

# Where does traffic go for this IP?
ip route get 8.8.8.8

# Can I reach port 443?
nc -zv 8.8.8.8 443

# What's my DNS server returning?
dig +short example.com

# Which process is using port 80?
ss -ltnp | grep :80

# How full is the connection tracking table?
cat /proc/sys/net/netfilter/nf_conntrack_count

# Are there any ARP conflicts?
arp -n | awk '{print $3}' | sort | uniq -d

# What's the physical link status?
ethtool eth0 | grep -E "Speed|Duplex|Link"

# Is the default route present?
ip route | grep default

# Real-time packet rates per interface
watch -n 1 'cat /proc/net/dev | column -t'

# Count TCP states
ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn

# Quick path analysis
mtr --report --report-cycles 50 8.8.8.8

# Test web server completely
curl -Lvo /dev/null https://example.com 2>&1 | grep -E "Connected|SSL|HTTP|Host"
```

---

## Closing Perspective: The Expert Troubleshooter's Edge

The tools listed here are instruments. The diagnostic mind that wields them is the real asset.

**What separates the top 1%:**

1. **Mental model precision** — they know exactly what each tool measures and what it cannot see. They know the limits of ping, why ICMP is rate-limited, why traceroute lies, why TCP packet loss hides when retransmission happens.

2. **Cross-layer thinking** — they never isolate a layer when debugging. A Layer 1 duplex mismatch shows up as Layer 4 TCP retransmissions, which appears to an application developer as "slow database queries."

3. **Hypothesis discipline** — they form one hypothesis, test it, accept or reject it, then move on. They don't swap random cables hoping something changes.

4. **Pattern recognition** — they've seen enough failures that they recognize "late collisions on full-duplex interface = duplex mismatch" the way a chess grandmaster recognizes an endgame pattern. This comes from deliberate practice with real networks.

5. **Documentation obsession** — they document what they changed, what they observed, and what resolved the issue. Every incident is a case study for the next one.

The OSI model is not just an exam topic. It is the **hierarchical mental taxonomy** you use to decompose every network problem into tractable sub-problems. Internalize it until you think in layers automatically.

---

*Guide compiled for deep study of network engineering and systems programming.*
*Covers Linux (iproute2), Cisco IOS/IOS-XE/IOS-XR, Juniper JunOS, and protocol-level analysis.*

The guide is complete — 22 sections, fully comprehensive. Here's the mental map of what's inside:

**Physical (Layer 1):** `ethtool`, TDR/OTDR, SFP DOM readings, cable faults, interface error counter taxonomy (runts, giants, CRC, late collisions — and what each *means*), duplex mismatch diagnosis.

**Data Link (Layer 2):** ARP states and pathological conditions, STP port states and failure modes (broadcast storms, TC events, wrong root bridge), MAC table analysis, VLAN trunk verification, CDP/LLDP neighbor mapping.

**Network (Layer 3):** `mtr` and how to correctly read it (false loss vs. real loss), `hping3` for crafting custom packets, `nmap` port states (open vs. closed vs. filtered — important distinction), `ip route get` for exact next-hop lookup, BGP/OSPF neighbor state machines.

**Transport (Layer 4):** Full TCP state machine with what each state implies diagnostically, `ss` filters for specific connection patterns, `iperf3` for BDP-aware throughput testing, the Bandwidth-Delay Product concept (why fast links go slow over distance).

**Packet Capture:** `tcpdump` BPF filter mastery, TCP flag notation (`[S.]`, `[R]`, `[P.]`), `tshark` display filters including retransmission and zero-window detection.

**Advanced:** PMTUD black holes and MSS clamping, bufferbloat detection and CoDel mitigation, QoS/DSCP markings, jitter measurement, Netflow analysis, SNMP OID navigation, and security-oriented diagnostics (SYN flood detection, ARP spoofing, promiscuous mode).

Every section follows the same discipline you apply to DSA — understand the *why* behind the tool, not just the syntax.