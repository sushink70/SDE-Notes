# Comprehensive Firewall & Network Debugging Guide
### Beyond Ping and Traceroute: Deep Diagnostic Techniques for Production Security Engineers

---

## Summary

This guide covers the full spectrum of network and firewall debugging tools and techniques used in production environments — from Layer 2 through Layer 7, from packet capture to flow telemetry, from stateful connection tables to policy evaluation traces. You will learn how to systematically isolate whether a problem lives in the wire, the firewall policy, the NAT table, the routing plane, or the application stack. Each section includes real commands, interpretation guidance, expected outputs, and failure modes. The goal is a methodical, security-first diagnostic workflow that doesn't rely on "spray and pray" — every tool here generates evidence that can be preserved, audited, and used to justify a change.

---

## Table of Contents

1. [Mental Model: The Diagnostic Stack](#1-mental-model-the-diagnostic-stack)
2. [Layer 2: Link and ARP Debugging](#2-layer-2-link-and-arp-debugging)
3. [Layer 3: IP Routing and ICMP Beyond Ping](#3-layer-3-ip-routing-and-icmp-beyond-ping)
4. [Layer 4: TCP/UDP Connection Debugging](#4-layer-4-tcpudp-connection-debugging)
5. [Packet Capture and Deep Inspection](#5-packet-capture-and-deep-inspection)
6. [Firewall State Table Inspection](#6-firewall-state-table-inspection)
7. [Firewall Policy Evaluation and Rule Tracing](#7-firewall-policy-evaluation-and-rule-tracing)
8. [NAT Debugging](#8-nat-debugging)
9. [Flow Analysis and NetFlow/IPFIX/sFlow](#9-flow-analysis-and-netflowipfixsflow)
10. [Routing Protocol Debugging](#10-routing-protocol-debugging)
11. [DNS Debugging in Firewall Context](#11-dns-debugging-in-firewall-context)
12. [TLS/SSL Debugging at the Firewall](#12-tlsssl-debugging-at-the-firewall)
13. [Application Layer (L7) Firewall Debugging](#13-application-layer-l7-firewall-debugging)
14. [Performance and Throughput Debugging](#14-performance-and-throughput-debugging)
15. [Platform-Specific: Linux Netfilter / iptables / nftables](#15-platform-specific-linux-netfilter--iptables--nftables)
16. [Platform-Specific: BSD pf (pfSense, OPNsense, OpenBSD)](#16-platform-specific-bsd-pf-pfsense-opnsense-openbsd)
17. [Platform-Specific: Cisco IOS / ASA / FTD](#17-platform-specific-cisco-ios--asa--ftd)
18. [Platform-Specific: Palo Alto Networks (PAN-OS)](#18-platform-specific-palo-alto-networks-pan-os)
19. [Platform-Specific: Juniper SRX / EX](#19-platform-specific-juniper-srx--ex)
20. [Cloud Firewalls: AWS, GCP, Azure](#20-cloud-firewalls-aws-gcp-azure)
21. [eBPF-based Networking Debugging (Cilium, XDP)](#21-ebpf-based-networking-debugging-cilium-xdp)
22. [Kubernetes Network Policy Debugging](#22-kubernetes-network-policy-debugging)
23. [Log Analysis and SIEM Integration](#23-log-analysis-and-siem-integration)
24. [Structured Troubleshooting Methodology](#24-structured-troubleshooting-methodology)
25. [Architecture View](#25-architecture-view)
26. [Threat Model and Diagnostic Safety](#26-threat-model-and-diagnostic-safety)
27. [References](#27-references)
28. [Next 3 Steps](#28-next-3-steps)

---

## 1. Mental Model: The Diagnostic Stack

Before issuing any command, internalize where the problem can live. Every packet traverses a vertical stack on the sender, across physical media, and up the stack on the receiver. A firewall introduces an additional enforcement plane at multiple layers.

```
SENDER                 FIREWALL(S)               RECEIVER
-------                ----------               --------
App (L7)               Policy Engine            App (L7)
Transport (L4)         Stateful Inspection      Transport (L4)
Network (L3)           NAT / Routing            Network (L3)
Link (L2)              Interface / VLAN         Link (L2)
Physical (L1)          Phy / Optical            Physical (L1)
```

The firewall is NOT a pass-through device. It has its own routing table, ARP cache, state table, policy evaluation engine, and logging subsystem — each of which can be the fault domain.

**Diagnostic Principle: Divide and Conquer by Layer**

Always start closest to the failing endpoint and move outward. Never assume the firewall is at fault until you eliminate L1/L2 issues, routing asymmetry, and endpoint-side policies (host firewall, SELinux, seccomp). False positives from skipping layers waste hours.

```
SYMPTOM → HYPOTHESIS → MEASUREMENT → EVIDENCE → CHANGE → VERIFY
```

**Tool Selection Matrix:**

| Layer      | Tool Category            | Examples                                             |
|------------|--------------------------|------------------------------------------------------|
| L1/L2      | Link state, ARP          | `ethtool`, `ip link`, `arp`, `arping`, `ndp`         |
| L3         | IP/ICMP                  | `ping`, `traceroute`, `mtr`, `hping3`, `nping`       |
| L3 Routing | Routing table            | `ip route`, `netstat -r`, `route`, `vtysh`           |
| L4         | TCP/UDP                  | `ss`, `netstat`, `nmap`, `nc`, `socat`, `hping3`     |
| L4-L7      | Packet capture           | `tcpdump`, `tshark`, `wireshark`, `termshark`        |
| FW State   | Connection tracking      | `conntrack`, `ipset`, `nft`, `pfctl -ss`             |
| FW Policy  | Rule trace               | `iptables -L`, `nft list`, `pfctl -sr`, vendor CLI   |
| NAT        | Translation table        | `conntrack -L`, vendor show cmds                     |
| Flow       | NetFlow/IPFIX/sFlow      | `nfdump`, `ntopng`, `pmacct`, `goflow2`              |
| DNS        | Name resolution          | `dig`, `drill`, `resolvectl`, `dnstracer`            |
| TLS        | Certificate/handshake    | `openssl s_client`, `sslyze`, `testssl.sh`           |
| L7 App     | HTTP/gRPC/AMQP           | `curl`, `grpcurl`, `httpie`, `wrk`                   |
| Perf       | Throughput/latency       | `iperf3`, `netperf`, `qperf`, `pktgen`               |
| eBPF       | Kernel-level visibility  | `bpftrace`, `bpftool`, `cilium`, `xdp-tools`         |

---

## 2. Layer 2: Link and ARP Debugging

L2 failures appear as "ping unreachable" but are actually silence at the wire level — no ARP response, misconfigured VLANs, STP port blocking, or NIC offload issues.

### 2.1 Check Interface State

```bash
# Linux: check physical and logical state
ip link show eth0
# Look for: state UP/DOWN, LOWER_UP (physical link), mtu, qlen

# Detailed: driver stats, errors, duplex, speed
ethtool eth0
ethtool -S eth0       # NIC statistics (drops, CRC errors, etc.)
ethtool -k eth0       # offload features (tx-checksum, gso, gro, lro)
ethtool -i eth0       # driver info

# BSD / macOS
ifconfig -a
netstat -I en0

# Show errors and drops per interface
ip -s link show eth0
# or
cat /proc/net/dev
```

**Key indicators of L2 failure:**
- `RX errors`, `TX errors`, `dropped`, `overruns` > 0 → hardware/driver or congestion
- `LOWER_UP` absent → no physical link (cable, SFP, switch port)
- MTU mismatch between interfaces on the same path → silent packet drops above MTU

### 2.2 ARP and Neighbor Discovery

```bash
# Show ARP table
ip neigh show
arp -n

# Send gratuitous ARP (verify MAC is reachable)
arping -I eth0 -c 3 192.168.1.1
# Expect: 3 responses from target MAC

# If no ARP response: target is down, wrong VLAN, or firewall blocks ARP

# IPv6 Neighbor Discovery
ip -6 neigh show
ndisc6 fe80::1 eth0   # send ICMPv6 NS for link-local addr

# Detect ARP spoofing (two different MACs claiming same IP)
arp -n | awk '{print $1}' | sort | uniq -d   # duplicate IPs = ARP conflict
```

### 2.3 VLAN Debugging

```bash
# Show VLAN interfaces
ip -d link show          # shows VLAN id in detail output
cat /proc/net/vlan/config

# Create VLAN interface for testing
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up
ip addr add 10.0.100.2/24 dev eth0.100

# Verify 802.1Q tagging with tcpdump
tcpdump -i eth0 -e 'vlan' -nn

# Cisco: check trunk port
show interfaces trunk
show vlan brief
```

**VLAN failure modes:**
- Native VLAN mismatch between firewall and switch → untagged frames go to wrong subnet
- Allowed VLANs not added to trunk port → traffic silently dropped at switch
- PVLAN / VLAN ACL blocking intra-VLAN traffic on firewall

### 2.4 Spanning Tree Protocol

STP in a wrong state blocks L2 forwarding entirely, yet the interface shows UP.

```bash
# On Cisco switch: check STP state per VLAN
show spanning-tree vlan 100 detail
# States: Blocking (BLK), Listening, Learning, Forwarding (FWD)
# If firewall-connected port is BLK -> packets never reach firewall

# Force PortFast on access port (disable STP on that port)
interface GigabitEthernet0/1
 spanning-tree portfast
 spanning-tree bpduguard enable
```

---

## 3. Layer 3: IP Routing and ICMP Beyond Ping

### 3.1 MTR (My Traceroute) — The Unified Tool

`mtr` combines ping and traceroute in a real-time display. It reveals per-hop packet loss and latency jitter — critical for diagnosing intermittent firewall drops vs. path asymmetry.

```bash
# Install
apt install mtr-tiny     # Debian/Ubuntu
dnf install mtr          # Fedora/RHEL

# Run TCP-based MTR to bypass ICMP blocks
mtr --tcp --port 443 --report --report-cycles 30 8.8.8.8
# --report: non-interactive output
# --report-cycles 30: 30 probes per hop

# UDP mode
mtr --udp --port 53 --report --report-cycles 20 1.1.1.1

# Output interpretation:
# Loss%  - packet loss at/after that hop
# Avg    - average RTT
# StDev  - jitter (high StDev = congestion or QoS shaping)
# If loss only at one hop but not subsequent: ICMP rate limiting (not failure)
# If loss starts at hop N and continues: real loss at/after hop N
```

### 3.2 hping3 — Surgical Packet Crafting

`hping3` lets you send arbitrary packets to test exactly what the firewall allows or blocks at L3/L4.

```bash
# TCP SYN to specific port (bypass ICMP blocks)
hping3 -S -p 80 -c 5 target.example.com
# -S: SYN flag  -p: dest port  -c: count
# Expect: SA (SYN-ACK) if port open, RA (RST-ACK) if port closed, timeout if filtered

# ICMP echo with custom TTL (manual traceroute)
hping3 --icmp --ttl 5 -c 3 target.example.com

# UDP flood test (rate-limited; test firewall UDP handling)
hping3 --udp -p 53 -c 10 -i u1000 target.example.com
# -i u1000: interval 1000 microseconds

# Traceroute with TCP SYN (bypass ICMP filters on traceroute)
hping3 -S -p 80 --traceroute -V target.example.com

# Fragment probe (test firewall fragment reassembly)
hping3 -f -p 80 -S target.example.com
# -f: split IP datagram into fragments; many firewalls block fragmented SYN
```

### 3.3 nping (from nmap suite)

```bash
# TCP connect test with verbose output
nping --tcp -p 443,8443,8080 --flags SYN -c 5 target.example.com

# ICMP sweep for path debugging
nping --icmp --icmp-type echo -c 3 --delay 500ms 10.0.0.1-10

# UDP probe
nping --udp -p 123 target.example.com

# Raw IP (no port) for protocol testing
nping --icmp --icmp-type timestamp 10.0.0.1
```

### 3.4 traceroute Variants

Standard `traceroute` uses UDP by default on Linux. Many firewalls block UDP probes.

```bash
# Default (UDP, ports 33434+)
traceroute target.example.com

# ICMP-based (like Windows tracert)
traceroute -I target.example.com

# TCP-based (most reliable through firewalls — use the destination port that should work)
traceroute -T -p 443 target.example.com

# UDP with specific source port
traceroute -U -p 53 target.example.com

# Increase probes per hop, set max hops
traceroute -q 5 -m 30 -T -p 80 target.example.com

# tcptraceroute (standalone binary; more reliable TCP traceroute)
apt install tcptraceroute
tcptraceroute target.example.com 443

# paris-traceroute (avoids ECMP hash variation between probes)
apt install paris-traceroute
paris-traceroute target.example.com
```

**Interpreting `* * *` at a hop:**
- Could be ICMP rate limiting (not a real block) — verify by checking subsequent hops respond
- Could be firewall dropping TTL-exceeded ICMP — check with TCP traceroute on a known-open port
- Could be a host that doesn't return ICMP TTL exceeded — common on CDN nodes

### 3.5 IP Route and Policy Routing

A firewall that has incorrect routing will silently blackhole or misroute traffic. Always verify routing from the firewall's perspective, not just the host's.

```bash
# Show main routing table
ip route show table main
ip route show table all      # includes policy routing tables

# Lookup which route a specific destination uses
ip route get 8.8.8.8
ip route get 8.8.8.8 from 10.0.0.5   # simulate source-based routing

# Show policy routing rules (RPDB - Routing Policy Database)
ip rule show
# Rules evaluated top-down by priority; first match wins

# Show specific routing table (e.g., table 100)
ip route show table 100

# Check for routing asymmetry (common cause of stateful firewall drops)
# From sender: traceroute to receiver
# From receiver: traceroute to sender
# If paths differ -> asymmetric routing -> stateful FW drops return traffic

# Verify RPDB on firewall when source routing is in play
ip rule add from 10.0.1.0/24 lookup 100
ip route add default via 10.0.1.1 table 100
```

### 3.6 ICMP Unreachables and Redirects

Firewalls suppress ICMP unreachables as a security measure, but this causes TCP to hang instead of fail fast.

```bash
# On Linux: check if ICMP unreachables are being sent
sysctl net.ipv4.icmp_errors_use_inbound_ifaddr
sysctl net.ipv4.icmp_ratelimit     # rate in ms; 0 = unlimited

# Check if ICMP redirects are being sent/accepted
sysctl net.ipv4.conf.all.send_redirects
sysctl net.ipv4.conf.all.accept_redirects

# Capture ICMP unreachables on the wire
tcpdump -i eth0 'icmp and icmp[icmptype] = 3'
# ICMP Type 3 = Destination Unreachable
# Code 0: Net unreachable
# Code 1: Host unreachable
# Code 3: Port unreachable (confirms firewall is sending RST or rejecting)
# Code 9/10: Administratively prohibited (firewall REJECT rule)
# Code 13: Communication administratively filtered (Cisco ASA)

# PMTU Discovery problems (common with tunnels + firewalls blocking ICMP Type 3 Code 4)
tcpdump -i eth0 'icmp and icmp[icmptype] = 3 and icmp[icmpcode] = 4'
# If these are blocked by firewall: PMTU blackhole -> large packets silently dropped
```

---

## 4. Layer 4: TCP/UDP Connection Debugging

### 4.1 ss — Socket Statistics (Replacement for netstat)

```bash
# Show all TCP connections with process info
ss -tnp

# Show listening sockets
ss -tlnp

# Show UDP sockets
ss -unlp

# Filter by destination port
ss -tn dst :443

# Filter by source address
ss -tn src 10.0.0.5

# Show extended state (TCP state machine details)
ss -tnpo state established
ss -tnpo state time-wait    # TIME_WAIT accumulation = connection churn
ss -tnpo state syn-sent     # SYN_SENT = half-open, firewall may be blocking

# Show socket memory and buffer usage
ss -tm

# Internal TCP diagnostics (equivalent of tcp_diag)
ss -ti dst :443
# Output: rtt, rto, ato, mss, cwnd, ssthresh, bytes_acked, retrans
```

**TCP state diagnosis:**

| State        | What It Means in Firewall Context                                          |
|--------------|-----------------------------------------------------------------------------|
| `SYN_SENT`   | Packet sent, no SYN-ACK received. Firewall may be dropping SYN inbound.    |
| `SYN_RECV`   | Server received SYN, sent SYN-ACK. If client never sees it: FW blocks ACK. |
| `ESTABLISHED`| Connection active. If data stops: FW idle timeout or TCP RST injection.     |
| `FIN_WAIT1`  | Client sent FIN. If stuck: FW not forwarding FIN.                           |
| `TIME_WAIT`  | Normal 2MSL wait. Accumulation = high connection churn.                     |
| `CLOSE_WAIT` | Server not closing. Application issue, not firewall.                        |

### 4.2 netcat (nc) and socat — Manual Connection Testing

```bash
# Test TCP connectivity (bypass application-level issues)
nc -zv target.example.com 443          # TCP connect test
nc -zvu target.example.com 53          # UDP test
nc -zvw 5 target.example.com 443       # 5-second timeout

# Listen mode (test if firewall allows inbound to a specific port)
nc -lnvp 9999      # on server
nc -v server-ip 9999   # on client

# socat: more powerful, supports TLS, Unix sockets, etc.
# Test TCP with explicit source IP/port (test FW policy tied to source)
socat - TCP:target.example.com:443,sourceport=12345

# Test TLS
socat - OPENSSL:target.example.com:443,verify=0

# Proxy through for testing connectivity path
socat TCP-LISTEN:8080,fork TCP:backend.internal:80
```

### 4.3 nmap — Port Scanning and Firewall Fingerprinting

**Note:** Only use nmap on infrastructure you own or have explicit authorization to test.

```bash
# Basic TCP SYN scan (stealth; most common)
nmap -sS -p 22,80,443,8080 target.example.com

# Service version detection
nmap -sV -p 443 target.example.com

# OS fingerprinting
nmap -O target.example.com

# ACK scan (determines if firewall is STATELESS or STATEFUL)
nmap -sA -p 80 target.example.com
# Stateless FW: ACK packets to unestablished ports return RST (port "unfiltered")
# Stateful FW: drops ACK if no SYN seen -> port "filtered"

# FIN/NULL/XMAS scans (bypass naive stateless firewalls)
nmap -sF -p 80 target.example.com    # FIN scan
nmap -sN -p 80 target.example.com    # NULL scan
nmap -sX -p 80 target.example.com    # XMAS scan (FIN+PSH+URG)
# RFC-compliant: RST if closed; no response if open. FW drops all = "filtered"

# UDP scan (slow; sends UDP probe, waits for ICMP port unreachable)
nmap -sU -p 53,123,161 target.example.com

# Detect firewall behavior via TCP window size fingerprint
nmap -sW -p 80 target.example.com

# Script scan for specific firewall/service fingerprint
nmap --script=firewall-bypass target.example.com
nmap --script=firewalk --script-args=firewalk.max-probed-ports=10 target.example.com

# Idle/zombie scan (blind scan through third host — detect FW rules for specific src IP)
nmap -sI zombie.host.com:80 target.example.com -p 80
```

**Interpreting nmap port states:**

| State       | Meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| `open`      | Port reachable, service accepting connections                           |
| `closed`    | Port reachable, no service (RST received) — firewall passes traffic     |
| `filtered`  | No response (firewall DROP) or ICMP admin-prohibited received           |
| `unfiltered`| ACK scan: reachable, stateless FW passes ACK; can't determine open/closed|
| `open|filtered` | No response to UDP or stealth scans; can't distinguish                |

### 4.4 Detecting TCP RST Injection by Firewalls

Some DPI firewalls (IPS/WAF) inject RST packets to terminate connections. This is distinct from the server sending RST.

```bash
# Capture RSTs; look at TTL to determine source
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-rst != 0'

# If RST TTL differs from server's TTL -> injected by middlebox (firewall/IPS)
# Server TTL: typically starts at 64 (Linux) or 128 (Windows)
# Injected RST TTL: often 64, 128, or 255 with different pattern than server stream

# Use tshark with TTL filter
tshark -i eth0 -Y "tcp.flags.reset == 1" -T fields \
  -e ip.src -e ip.dst -e ip.ttl -e tcp.stream -e frame.number
```

---

## 5. Packet Capture and Deep Inspection

Packet capture is the ground truth. All other tools derive from it. Master this before anything else.

### 5.1 tcpdump — The Essential CLI Capture Tool

```bash
# Capture on specific interface, no DNS resolution, with full packet hex
tcpdump -i eth0 -nn -XX -s 0 -w /tmp/capture.pcap

# Capture with a ring buffer (for long-running captures without OOM)
tcpdump -i eth0 -nn -s 0 -W 10 -C 100 -w /tmp/capture.pcap
# -W 10: max 10 files, -C 100: 100MB per file (rotates)

# Capture specific host and port
tcpdump -i eth0 -nn 'host 10.0.0.5 and port 443'

# Capture TCP SYN only (track new connection attempts)
tcpdump -i eth0 -nn 'tcp[tcpflags] == tcp-syn'

# Capture TCP SYN, SYN-ACK, RST (connection setup/teardown)
tcpdump -i eth0 -nn 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'

# Capture ICMP unreachables
tcpdump -i eth0 -nn 'icmp[icmptype] = icmp-unreach'

# Capture fragmented packets
tcpdump -i eth0 -nn '((ip[6:2] & 0x3fff) != 0)'

# Capture by protocol number (e.g., OSPF = 89, VRRP = 112, GRE = 47, ESP = 50)
tcpdump -i eth0 -nn 'ip proto 50'    # ESP (IPsec)
tcpdump -i eth0 -nn 'ip proto 47'    # GRE

# Capture and display in ASCII (for text protocol debugging)
tcpdump -i eth0 -nn -A 'host target.example.com and port 80'

# Capture VXLAN (port 4789) inner packets
tcpdump -i eth0 -nn 'udp port 4789'

# Multiple interfaces capture (Linux only with -i any)
tcpdump -i any -nn 'host 10.0.0.5'

# Timestamp precision (important for correlation)
tcpdump -i eth0 -nn -tttt 'host 10.0.0.5'   # human-readable timestamp
tcpdump -i eth0 -nn -ttttt 'host 10.0.0.5'  # delta from previous packet
```

### 5.2 tshark — CLI Wireshark (Scriptable, Powerful)

```bash
# Install
apt install tshark

# Read pcap and show specific fields
tshark -r /tmp/capture.pcap -T fields \
  -e frame.number -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport \
  -e tcp.flags -e tcp.analysis.flags -e tcp.time_delta \
  -E header=y -E separator=,

# Filter for TCP retransmissions (indicates loss or FW dropping mid-stream)
tshark -r capture.pcap -Y "tcp.analysis.retransmission"

# Filter for duplicate ACKs (congestion or loss)
tshark -r capture.pcap -Y "tcp.analysis.duplicate_ack"

# Show TCP stream (conversation reassembly)
tshark -r capture.pcap -Y "tcp.stream eq 0" -T text

# Follow TCP stream (like Wireshark "Follow TCP Stream")
tshark -r capture.pcap -z follow,tcp,ascii,0

# Decode VXLAN inner frame
tshark -r capture.pcap -Y "vxlan" -d udp.port==4789,vxlan

# Show TLS handshake details
tshark -r capture.pcap -Y "ssl.handshake" -T fields \
  -e ip.src -e ip.dst -e ssl.handshake.type -e ssl.handshake.version

# Statistics: conversations
tshark -r capture.pcap -q -z conv,tcp
tshark -r capture.pcap -q -z conv,ip

# Expert info (all anomalies)
tshark -r capture.pcap -q -z expert,,,

# Live capture with decode (useful for quick protocol verification)
tshark -i eth0 -Y "http" -T fields -e http.request.method \
  -e http.request.uri -e http.response.code
```

### 5.3 termshark — Terminal Wireshark UI

```bash
# Install
go install github.com/gcla/termshark/v2/cmd/termshark@latest
# or binary from GitHub releases

# Launch on interface
termshark -i eth0 'port 443'

# Open existing pcap
termshark -r capture.pcap
```

### 5.4 Capturing on Both Sides of the Firewall

This is the single most powerful technique for firewall debugging. Run simultaneous captures on ingress and egress interfaces of the firewall. A packet present on ingress but absent on egress is dropped by the firewall policy.

```bash
# On firewall (Linux): capture ingress (WAN side) and egress (LAN side) simultaneously
tcpdump -i eth0 -nn -s 0 -w /tmp/wan.pcap 'host 203.0.113.5' &
tcpdump -i eth1 -nn -s 0 -w /tmp/lan.pcap 'host 10.0.0.5' &
# Run test traffic
# kill %1 %2

# Correlate by sequence number or timestamp
tshark -r /tmp/wan.pcap -T fields -e frame.number -e ip.src -e ip.dst \
  -e tcp.seq -e ip.ttl | head -20

tshark -r /tmp/lan.pcap -T fields -e frame.number -e ip.src -e ip.dst \
  -e tcp.seq -e ip.ttl | head -20

# If same TCP SEQ appears in wan.pcap but not lan.pcap -> firewall dropped it
# If TTL differs by more than 1 -> extra hop between capture points
```

### 5.5 Kernel-Level Capture with BPF

BPF (Berkeley Packet Filter) underlies all capture tools. Understanding it enables custom capture programs and kernel filtering.

```bash
# Compile and inspect a BPF filter
tcpdump -i eth0 -d 'tcp port 443 and host 10.0.0.1'
# -d: dump compiled BPF bytecode

# Use bpf_asm / bpf_dbg for custom filters
# Create raw socket with BPF in Go for in-process capture
# (See: golang.org/x/net/bpf)

# sk_filter with raw socket for custom packet processing
# Attach BPF filter to existing socket:
# setsockopt(fd, SOL_SOCKET, SO_ATTACH_FILTER, &prog, sizeof(prog));
```

---

## 6. Firewall State Table Inspection

Stateful firewalls maintain a connection tracking table. This is one of the most common places for subtle bugs: expired entries, full tables, asymmetric routing bypasses.

### 6.1 Linux conntrack

```bash
# Install
apt install conntrack

# List all tracked connections
conntrack -L
# Format: proto src=IP dst=IP sport=PORT dport=PORT state=STATE packets=N bytes=N

# List with timeout remaining
conntrack -L -o extended

# Filter by protocol
conntrack -L -p tcp
conntrack -L -p udp

# Filter by source IP
conntrack -L --src 10.0.0.5

# Watch for new connections in real-time
conntrack -E -p tcp    # Events: NEW, UPDATE, DESTROY

# Show connection statistics (table usage, insert rate)
conntrack -S
# max: max table size
# count: current entries
# searched, found, new: lookup stats
# invalid, ignore: policy drops

# If count approaches max: table overflow -> connections silently dropped
# Fix:
sysctl net.netfilter.nf_conntrack_max          # view
sysctl -w net.netfilter.nf_conntrack_max=524288  # increase

# Show connection timeouts
sysctl -a | grep nf_conntrack_.*_timeout

# Delete specific connection entry (force re-establishment)
conntrack -D --src 10.0.0.5 --dst 10.0.0.1 -p tcp --dport 443

# Flush all tracked connections (extreme measure - drops all existing connections)
conntrack -F

# Show NAT entries specifically
conntrack -L -n   # NATed connections only
```

**Common conntrack failure modes:**

| Symptom                        | conntrack root cause                                      |
|-------------------------------|-----------------------------------------------------------|
| New connections fail silently  | Table full (`count >= max`). Increase `nf_conntrack_max`. |
| Established conn drops suddenly| Idle timeout expired. Increase relevant timeout sysctl.   |
| Asymmetric routing failure     | SYN seen on one interface, replies on another; packet marked INVALID and dropped by `-m state --state INVALID -j DROP` |
| UDP "connection" drops         | UDP timeout too short (default 30s). Increase `nf_conntrack_udp_timeout_stream`. |
| FTP/SIP broken                 | ALG (Application Layer Gateway) not loaded. `modprobe nf_conntrack_ftp` |

### 6.2 ipset

ipset is used for high-performance IP/port matching in iptables/nftables rules.

```bash
# List all sets
ipset list

# Show specific set
ipset list blocked_hosts

# Test if an IP is in a set
ipset test blocked_hosts 10.0.0.5
# Returns: exit 0 if present, exit 1 if not

# Save and restore sets
ipset save > /tmp/ipset_backup
ipset restore < /tmp/ipset_backup

# Add/delete dynamically
ipset add blocked_hosts 10.0.0.5
ipset del blocked_hosts 10.0.0.5
```

---

## 7. Firewall Policy Evaluation and Rule Tracing

### 7.1 iptables — Policy Analysis

```bash
# List all rules with line numbers, no DNS resolution
iptables -L -n -v --line-numbers
iptables -L INPUT -n -v --line-numbers
iptables -L FORWARD -n -v --line-numbers

# Show NAT rules
iptables -t nat -L -n -v --line-numbers

# Show mangle table (QoS, DSCP marking)
iptables -t mangle -L -n -v --line-numbers

# Rule hit counters: check if a rule is being matched
iptables -L FORWARD -n -v | grep -v "0     0"   # show only rules with hits

# Zero counters before a test, then check after
iptables -Z FORWARD     # zero all counters in FORWARD chain
# Run test traffic
iptables -L FORWARD -n -v   # see which rules got hits

# Trace a packet through iptables (kernel packet tracing)
# Add TRACE target to raw table
iptables -t raw -A PREROUTING -s 10.0.0.5 -p tcp --dport 443 -j TRACE
iptables -t raw -A OUTPUT -d 10.0.0.5 -p tcp --sport 443 -j TRACE
# Read trace from kernel log
dmesg | grep 'TRACE:'
# Or via netfilter log (requires nfnetlink_log)
# Each line shows: table, chain, rule number, packet details

# Remove trace rules when done
iptables -t raw -D PREROUTING -s 10.0.0.5 -p tcp --dport 443 -j TRACE
```

### 7.2 nftables — Modern Policy Analysis

```bash
# List all ruleset
nft list ruleset

# List specific table
nft list table ip filter

# List specific chain
nft list chain ip filter forward

# Rule counters (counters must be added to rules)
nft list table ip filter | grep counter

# Add trace to existing rule
nft add rule ip filter forward tcp dport 443 meta nftrace set 1
nft monitor trace   # live trace output in terminal

# Remove trace
nft delete rule ip filter forward handle <handle-number>

# Test rule matching without modifying state
# nft doesn't have a dry-run; use trace mechanism above

# Flush and restore ruleset
nft list ruleset > /tmp/nft_backup.nft
nft flush ruleset
nft -f /tmp/nft_backup.nft
```

### 7.3 Policy Correctness Verification

```bash
# Check rule order (rules are evaluated top-down; first match wins)
# Find where your traffic matches:
iptables -L FORWARD -n -v --line-numbers | head -40

# Check default policy (what happens to unmatched traffic)
iptables -L | grep Chain
# Chain INPUT (policy DROP)  <- DROP by default; explicit allows needed
# Chain FORWARD (policy ACCEPT) <- permissive default; dangerous

# Verify stateful tracking is enabled
lsmod | grep nf_conntrack
# Or:
iptables -L | grep "state\|ctstate"   # conntrack-based rules present?

# Verify no duplicate or shadowed rules
# Rule A: ACCEPT tcp dport 443 from 10.0.0.0/8
# Rule B: DROP   tcp dport 443 from 10.0.0.5
# Rule B never matches because Rule A catches it first
```

---

## 8. NAT Debugging

NAT is a frequent source of subtle bugs: wrong translation, exhausted port pools, hairpin NAT failures.

### 8.1 Linux NAT (iptables MASQUERADE / DNAT)

```bash
# Show NAT rules
iptables -t nat -L -n -v --line-numbers

# View active NAT translations
conntrack -L -n
# Look for: src=PRIVATE_IP dst=PUBLIC_IP sport=PORT ... [DNAT] to=INTERNAL_IP:PORT

# Test DNAT (port forwarding) is working
# External:
nc -zv FIREWALL_PUBLIC_IP 8080
# Should connect to internal 10.0.0.5:80 after DNAT

# Check MASQUERADE (SNAT for dynamic egress)
# From internal host:
curl -s https://ifconfig.me    # should return firewall's public IP

# Test hairpin NAT (internal host connecting to firewall's public IP)
# Requires: MASQUERADE on loopback + PREROUTING DNAT + specific POSTROUTING
# Add hairpin rule:
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -d 10.0.0.5 -j MASQUERADE
```

### 8.2 Port Exhaustion (SNAT)

A common silent failure in high-throughput environments.

```bash
# Check source port usage
ss -n | awk '{print $4}' | cut -d: -f2 | sort -n | uniq -c | sort -rn | head

# Check available local ports
sysctl net.ipv4.ip_local_port_range     # default: 32768 60999 = 28231 ports

# Increase port range
sysctl -w net.ipv4.ip_local_port_range="1024 65535"

# Check TIME_WAIT sockets consuming ports
ss -tn state time-wait | wc -l

# Enable TCP TIME_WAIT reuse
sysctl -w net.ipv4.tcp_tw_reuse=1     # for outbound connections only

# Add more public IPs to SNAT pool (increase available 5-tuple combinations)
iptables -t nat -A POSTROUTING -o eth0 \
  -j SNAT --to-source 203.0.113.1-203.0.113.10:1024-65535
```

---

## 9. Flow Analysis and NetFlow/IPFIX/sFlow

Flow records give you a traffic matrix without full packet capture. Ideal for retrospective analysis, anomaly detection, and capacity planning.

### 9.1 Architecture

```
[Router/FW] --NetFlow/IPFIX--> [Collector] ---> [Analyzer]
                                  nfcapd           nfdump
                                  goflow2          ntopng
                                  pmacct           Grafana
```

### 9.2 Enabling NetFlow/IPFIX Export

**Linux (softflowd / fprobe):**
```bash
# softflowd: flow export from pcap or live interface
apt install softflowd
softflowd -i eth0 -n collector.example.com:2055 -v 9   # NetFlow v9

# fprobe: NetFlow probe
apt install fprobe
fprobe -i eth0 -f ip collector.example.com:2055

# nprobe: commercial, high-performance, IPFIX/NetFlow v9
# pmacct: open-source, supports NetFlow, IPFIX, sFlow, BMP
```

**Cisco IOS:**
```
ip flow-export version 9
ip flow-export destination 192.168.1.100 2055
interface GigabitEthernet0/0
 ip flow ingress
 ip flow egress
```

### 9.3 nfdump — NetFlow Analysis CLI

```bash
# Install
apt install nfdump

# Start collector (receives flows from exporters)
nfcapd -w -D -l /var/cache/nfdump -p 2055 -I any

# Analyze flows: top talkers
nfdump -R /var/cache/nfdump -s ip/bytes -n 20

# Specific time window
nfdump -R /var/cache/nfdump -t 2024/01/01.12:00:00-2024/01/01.13:00:00 \
  'proto tcp and port 443'

# Show all flows to a specific destination
nfdump -R /var/cache/nfdump 'dst ip 10.0.0.5 and dst port 443'

# Show flow statistics
nfdump -R /var/cache/nfdump -s record/bytes -n 10 'proto tcp'

# Show flows sorted by duration (find long-lived connections)
nfdump -R /var/cache/nfdump -O tstart 'duration > 300'
```

### 9.4 goflow2 — Cloud-Native Flow Collector

```bash
# Install (Go binary)
go install github.com/netsampler/goflow2/cmd/goflow2@latest

# Run with Kafka output
goflow2 -listen netflow://:2055 -transport kafka -kafka.brokers kafka:9092

# Run with file output (for testing)
goflow2 -listen netflow://:2055 -transport file -file.path /tmp/flows.json

# Docker
docker run --rm -p 2055:2055/udp ghcr.io/netsampler/goflow2:latest \
  -listen netflow://:2055 -transport file -file.path /dev/stdout
```

### 9.5 sFlow

sFlow samples packets at wire speed (1-in-N sampling) and exports both flow records and raw packet headers.

```bash
# sflowtool: parse sFlow datagrams
apt install sflowtool
# In one terminal: receive and display
sflowtool -p 6343

# In another: send test sFlow datagram (for collector testing)
# Most modern switches support sFlow natively
# Configure on switch:
# sflow sample-rate 512     # 1 in 512 packets
# sflow collector 192.168.1.100 6343
```

---

## 10. Routing Protocol Debugging

Misconfigured BGP or OSPF on a firewall causes traffic to route around or through the firewall unintentionally.

### 10.1 FRRouting (vtysh)

FRR is the standard routing daemon stack for Linux-based firewalls and routers.

```bash
# Access FRR shell
vtysh

# BGP debugging
show bgp summary
show bgp neighbors 10.0.0.1 detail
show bgp ipv4 unicast
show bgp ipv4 unicast 10.0.0.0/8 longer-prefixes

# OSPF debugging
show ip ospf neighbor
show ip ospf database
show ip ospf route

# Check what routes FRR is installing into kernel
show ip route
show ip route ospf
show ip route bgp

# BFD (Bidirectional Forwarding Detection) — fast link failure detection
show bfd peers
show bfd peers detail

# Enable BGP debug (verbose; only in lab or on controlled peer)
debug bgp updates
debug bgp keepalives
show log     # FRR internal log

# Turn off
no debug bgp updates
```

### 10.2 Route Leak Detection

```bash
# Compare FRR route table with kernel table
vtysh -c "show ip route" | grep -v '^[COSBKEI]' | sort > /tmp/frr_routes.txt
ip route show | sort > /tmp/kernel_routes.txt
diff /tmp/frr_routes.txt /tmp/kernel_routes.txt
# Differences indicate routes not installed by FRR (e.g., static routes in kernel only)
```

---

## 11. DNS Debugging in Firewall Context

Firewalls that do DNS inspection can silently alter or drop DNS responses. DNS-based firewall rules (FQDN objects) can mismatch if cached differently.

### 11.1 dig — Authoritative DNS Debugging

```bash
# Basic query
dig A example.com

# Query specific DNS server (bypass firewall's DNS proxy)
dig @8.8.8.8 A example.com

# Query the firewall's DNS proxy directly
dig @FIREWALL_IP A example.com

# Compare results: if firewall returns different IP than authoritative
# -> FQDN-based rule mismatch or DNS hijacking by firewall

# Query with full trace (bypass cache)
dig +trace A example.com

# Check DNSSEC validation
dig +dnssec +multi A example.com
# Look for: ad flag (Authenticated Data) in flags section

# Reverse DNS (PTR record)
dig -x 8.8.8.8

# Test DNS over TCP (FW may block DNS UDP but allow TCP)
dig +tcp A example.com @8.8.8.8

# Check DNS response size (EDNS buffer; FW may block large UDP DNS)
dig +bufsize=512 ANY example.com @8.8.8.8   # force small buffer
dig +ignore ANY example.com @8.8.8.8         # ignore truncation flag

# dnstracer: full DNS delegation trace with timing
apt install dnstracer
dnstracer -s example.com
```

### 11.2 Firewall DNS Inspection Issues

```bash
# Capture DNS traffic to see what firewall is actually passing
tcpdump -i eth0 -nn 'port 53' -A

# Check if FW is modifying DNS responses (DNS ALG)
# Compare response from: FW DNS proxy vs. direct to 8.8.8.8
dig @FIREWALL_IP A example.com
dig @8.8.8.8 A example.com
# Different answers -> FW DNS ALG or DNS sinkholes active

# Test DNS over TLS (DoT) bypass
kdig @8.8.8.8 +tls A example.com   # knot-dns tools
# Or with openssl:
echo -e "0\x00\x1e\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01" \
  | openssl s_client -connect 8.8.8.8:853 -quiet 2>/dev/null | hexdump -C | head
```

---

## 12. TLS/SSL Debugging at the Firewall

TLS-inspecting firewalls (SSL inspection / MITM) introduce their own certificate chain, cipher preferences, and TLS version constraints.

### 12.1 openssl s_client

```bash
# Full TLS handshake inspection
openssl s_client -connect target.example.com:443 -servername target.example.com

# Output analysis:
# - Verify return code: 0 (ok) vs error code
# - Certificate chain: who signed the leaf cert?
#   If firewall CA appears -> TLS inspection active
# - Cipher: what cipher was negotiated?
# - Protocol: TLS 1.2 vs 1.3

# Check TLS 1.3 specifically
openssl s_client -connect target.example.com:443 -tls1_3

# Force specific cipher
openssl s_client -connect target.example.com:443 \
  -cipher ECDHE-RSA-AES256-GCM-SHA384

# Show full certificate chain
openssl s_client -connect target.example.com:443-showcerts 2>/dev/null \
  | openssl x509 -noout -text | grep -A 3 "Issuer\|Subject\|Not"

# Test certificate through specific IP (bypass DNS for FW debugging)
openssl s_client -connect 203.0.113.5:443 -servername target.example.com

# Check for TLS session resumption (stateful FW may break it)
openssl s_client -connect target.example.com:443 -reconnect

# STARTTLS (e.g., SMTP, IMAP through firewall)
openssl s_client -connect mail.example.com:25 -starttls smtp
openssl s_client -connect mail.example.com:143 -starttls imap
```

### 12.2 testssl.sh — Comprehensive TLS Testing

```bash
# Install
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh

# Full scan (useful to see what cipher/TLS FW exposes vs. real server)
./testssl.sh target.example.com

# Focus on certificate
./testssl.sh --certificate target.example.com

# Focus on cipher support
./testssl.sh --cipher-per-proto target.example.com

# Vulnerabilities only
./testssl.sh --vuln target.example.com

# Compare results when going through FW vs. direct:
./testssl.sh FIREWALL_IP:443    # through firewall
./testssl.sh REAL_SERVER_IP:443 # direct (from outside FW)
```

### 12.3 sslyze — Python-Based TLS Auditor

```bash
pip install sslyze
python -m sslyze target.example.com:443 --regular

# JSON output for scripting
python -m sslyze target.example.com:443 --json_out results.json

# Detect TLS 1.0/1.1 being offered (firewall downgrade)
python -m sslyze --tlsv1 --tlsv1_1 target.example.com:443
```

---

## 13. Application Layer (L7) Firewall Debugging

Modern NGFWs (Next-Gen Firewalls) inspect and block at L7 based on application signature, URL category, or content.

### 13.1 curl — HTTP/HTTPS Debugging

```bash
# Verbose HTTP request (show all headers, TLS handshake)
curl -v https://target.example.com/

# Very verbose with timing
curl -v --trace-time https://target.example.com/

# Specific timing breakdown
curl -w "@curl-format.txt" -o /dev/null -s https://target.example.com/
# curl-format.txt:
#   time_namelookup:  %{time_namelookup}\n
#   time_connect:     %{time_connect}\n
#   time_appconnect:  %{time_appconnect}\n
#   time_pretransfer: %{time_pretransfer}\n
#   time_redirect:    %{time_redirect}\n
#   time_starttransfer: %{time_starttransfer}\n
#   time_total:       %{time_total}\n

# Test specific HTTP verb (FW may allow GET but block POST/PUT)
curl -X POST -d '{"key":"value"}' -H 'Content-Type: application/json' \
  https://target.example.com/api

# Force HTTP/1.1 (FW may not support HTTP/2)
curl --http1.1 https://target.example.com/

# Test via specific interface (source IP binding)
curl --interface eth0 https://target.example.com/
curl --interface 10.0.0.5 https://target.example.com/

# Use proxy (test if FW proxy works)
curl -x http://PROXY_IP:3128 https://target.example.com/

# Show effective URL (follow redirects)
curl -L -v https://target.example.com/ 2>&1 | grep -E "^> |^< "

# Test with custom User-Agent (FW may block default curl UA)
curl -H 'User-Agent: Mozilla/5.0' https://target.example.com/

# Test URL category (some FW block by URL category)
curl https://target.example.com/path/that/should/be/allowed
curl https://target.example.com/path/that/might/be/blocked
# Compare HTTP response codes and body
```

### 13.2 Detecting L7 Firewall Block Pages

```bash
# FW block pages typically return:
# HTTP 200 with block page content
# HTTP 302 redirect to a block page URL
# TCP RST with no HTTP response

# Detect redirect to block page
curl -s -o /dev/null -w "%{http_code} %{redirect_url}" https://target.example.com/

# Detect block page by content hash
curl -s https://target.example.com/ | sha256sum
# Compare across multiple requests/sites: same hash = FW block page

# Check for FW certificate injection (TLS inspection)
openssl s_client -connect target.example.com:443 2>/dev/null \
  | grep "Issuer:" 
# If issuer is your org's internal CA or firewall vendor CA -> TLS inspection

# gRPC testing through NGFW
grpcurl -plaintext target.example.com:50051 list
grpcurl -v -d '{}' target.example.com:50051 ServiceName/MethodName
```

---

## 14. Performance and Throughput Debugging

Firewalls add latency and reduce throughput. Quantifying this is essential for capacity planning and SLA compliance.

### 14.1 iperf3 — Bandwidth Testing

```bash
# Start server
iperf3 -s -p 5201

# Basic TCP test (measure FW throughput impact)
iperf3 -c target.example.com -p 5201 -t 30

# Multi-stream (test FW's per-flow vs. aggregate bandwidth)
iperf3 -c target.example.com -P 8 -t 30
# Compare: single stream vs. 8 streams; large delta = per-flow bottleneck in FW

# UDP test with specific bandwidth
iperf3 -c target.example.com -u -b 100M -t 30
# Check jitter and packet loss in output

# Reverse test (server sends to client — test asymmetric path)
iperf3 -c target.example.com -R -t 30

# Bidirectional
iperf3 -c target.example.com --bidir -t 30

# Test with specific MTU / packet size
iperf3 -c target.example.com -l 1400   # 1400-byte payloads
iperf3 -c target.example.com -l 9000   # jumbo frame test

# Zero-copy mode (reduce CPU overhead on measurement)
iperf3 -c target.example.com -Z

# JSON output for scripting
iperf3 -c target.example.com -J > iperf_results.json
```

### 14.2 netperf — Protocol-Specific Performance

```bash
# Install
apt install netperf

# Start server
netserver -p 12865

# TCP stream (bulk throughput)
netperf -H target.example.com -p 12865 -t TCP_STREAM -l 30

# TCP request/response (simulates transactional traffic)
netperf -H target.example.com -p 12865 -t TCP_RR -l 30
# Output: transactions/second — good for FW connection rate testing

# UDP stream
netperf -H target.example.com -p 12865 -t UDP_STREAM -l 30

# New TCP connections per second (stress FW connection table)
netperf -H target.example.com -p 12865 -t TCP_CRR -l 30
```

### 14.3 pktgen — Kernel Packet Generator

pktgen sends packets at line rate from the kernel, bypassing userspace overhead. Useful for firewall stress testing.

```bash
# Load pktgen module
modprobe pktgen

# Configure pktgen (via /proc interface)
cat > /tmp/pktgen_setup.sh << 'EOF'
echo "rem_device_all" > /proc/net/pktgen/kpktgend_0
echo "add_device eth0" > /proc/net/pktgen/kpktgend_0
echo "count 1000000" > /proc/net/pktgen/eth0
echo "clone_skb 0" > /proc/net/pktgen/eth0
echo "pkt_size 64" > /proc/net/pktgen/eth0
echo "dst 10.0.0.5" > /proc/net/pktgen/eth0
echo "dst_mac 00:11:22:33:44:55" > /proc/net/pktgen/eth0
echo "start" > /proc/net/pktgen/pgctrl
EOF
bash /tmp/pktgen_setup.sh

# Read results
cat /proc/net/pktgen/eth0
# Look for: pps (packets per second), errors
```

### 14.4 Latency Measurement

```bash
# hping3 round-trip time (more accurate than ping for specific ports)
hping3 -S -p 443 -c 100 --fast target.example.com 2>&1 | tail -5

# sockperf: UDP/TCP latency with percentiles
apt install sockperf
# Server: sockperf sr -i 0.0.0.0 -p 11111
# Client: sockperf ping-pong -i SERVER -p 11111 --time 30 --pps 1000

# qperf: latency + bandwidth in one tool
apt install qperf
# Server: qperf
# Client: qperf SERVER tcp_lat tcp_bw

# Measure per-hop latency contribution (FW latency isolation)
# Ping hop before FW: ping -c 100 FW_INGRESS_ROUTER
# Ping FW itself: ping -c 100 FW_IP
# Ping hop after FW: ping -c 100 FW_EGRESS_ROUTER
# Delta between (FW - ingress_router) = FW processing latency
```

---

## 15. Platform-Specific: Linux Netfilter / iptables / nftables

### 15.1 Complete iptables Debug Workflow

```bash
# Step 1: Document current ruleset
iptables-save > /tmp/iptables_before.txt

# Step 2: Add logging to suspect chains
iptables -I FORWARD 1 -j LOG --log-prefix "FW-FORWARD: " --log-level 4
iptables -I INPUT 1 -j LOG --log-prefix "FW-INPUT: " --log-level 4

# Step 3: Reproduce problem

# Step 4: Read logs
journalctl -k | grep "FW-"
# or: dmesg | grep "FW-"
# Log format: [timestamp] FW-FORWARD: IN=eth0 OUT=eth1 SRC=10.0.0.5 DST=10.0.0.1
#             PROTO=TCP SPT=54321 DPT=443 FLAGS=SYN

# Step 5: Use TRACE for exact rule match
iptables -t raw -I PREROUTING -s 10.0.0.5 -j TRACE
# Read: dmesg | grep "TRACE:"
# Output shows: which table/chain/rule handled the packet

# Step 6: Remove debug rules
iptables -D FORWARD 1
iptables -D INPUT 1
iptables -t raw -D PREROUTING 1

# Restore original ruleset
iptables-restore < /tmp/iptables_before.txt
```

### 15.2 nftables Debug Workflow

```bash
# Document ruleset
nft list ruleset > /tmp/nft_before.nft

# Add trace to a specific chain (nftables uses nftrace)
# Find the rule handle
nft list chain ip filter forward -a

# Add trace to specific packet
nft add rule ip filter forward \
  ip saddr 10.0.0.5 tcp dport 443 \
  meta nftrace set 1

# Monitor trace output
nft monitor trace
# Output: trace id, table/chain/rule, verdict (accept/drop/continue)

# Remove trace
nft delete rule ip filter forward handle HANDLE_NUMBER

# nftables built-in statistics
nft list ruleset | grep counter

# Enable per-rule counter (must be in rule)
nft add rule ip filter forward counter log prefix "FW-FORWARD: " accept
```

### 15.3 XDP / eBPF at the Firewall Level

```bash
# List loaded XDP programs
ip link show | grep xdp
bpftool prog list type xdp

# Show XDP program details
bpftool prog show id <ID>

# Dump XDP program bytecode
bpftool prog dump xlated id <ID>

# Show XDP maps (e.g., blocklists in BPF maps)
bpftool map list
bpftool map dump id <MAP_ID>

# Trace XDP packet events with bpftrace
bpftrace -e 'tracepoint:xdp:xdp_exception { printf("XDP exception: %s\n", args->act); }'

# Monitor per-CPU XDP drop counters
cat /sys/class/net/eth0/statistics/rx_dropped
# Or per-CPU: bpftool map dump id <XDP_STATS_MAP_ID>
```

---

## 16. Platform-Specific: BSD pf (pfSense, OPNsense, OpenBSD)

### 16.1 pfctl — Core pf Control Tool

```bash
# Show all rules
pfctl -sr    # rules
pfctl -sn    # NAT rules
pfctl -ss    # state table
pfctl -si    # interface statistics
pfctl -sm    # memory statistics (state table usage)
pfctl -sa    # everything

# Show state table for specific host
pfctl -ss | grep 10.0.0.5

# Show state table size
pfctl -sm
# states: current count
# half-open TCP states (SYN_SENT)

# Flush state table
pfctl -F states

# Log analysis: pf logs to pflog0 interface
tcpdump -i pflog0 -nn    # watch PF decisions in real-time
tcpdump -i pflog0 -nn 'host 10.0.0.5'

# Show rule with hit counters
pfctl -vsr    # verbose: adds packet/byte counts

# Rule number debugging
pfctl -sr | grep -n .    # add line numbers

# Test specific rule
pfctl -vvsr   # very verbose

# Enable logging on specific rule (must have log keyword)
# In pf.conf:
# pass in log on em0 proto tcp from any to any port 443

# pflog capture for analysis
tcpdump -tt -e -i pflog0 -n

# Trace packet through pf (OpenBSD 7.x+)
# pfctl -T debug  # no equivalent of iptables TRACE in pf
# Use pflog0 interface capture as equivalent
```

### 16.2 pfSense / OPNsense Specific

```bash
# Via SSH to pfSense/OPNsense shell
pfctl -sa          # all stats
pfctl -ss | wc -l  # count active states

# Filter states by interface
pfctl -ss | grep "em0"

# View real-time blocked packets
tcpdump -i pflog0 -nn action block

# View real-time passed packets to specific host
tcpdump -i pflog0 -nn 'action pass and host 10.0.0.5'

# pfSense packet capture via GUI corresponds to:
tcpdump -i em0 -nn -s 0 -w /tmp/capture.pcap 'host 10.0.0.5'

# Reload rules without flushing states
pfctl -f /etc/pf.conf    # parse and load
```

---

## 17. Platform-Specific: Cisco IOS / ASA / FTD

### 17.1 Cisco IOS Firewall (ZBF)

```bash
# Zone-Based Firewall inspection
show policy-map type inspect zone-pair sessions

# IP inspect (CBAC - older)
show ip inspect sessions
show ip inspect sessions detail

# IP access-list hit counts
show ip access-lists ACL_NAME | include permit|deny

# NAT table
show ip nat translations
show ip nat translations verbose total

# Check if packet matches NAT
debug ip nat
# Warning: debug commands in production cause CPU spikes; use with extreme care
# Always use: debug ip nat 10.0.0.5   (filter to specific host)
# Disable immediately: undebug all

# Connection table
show ip inspect sessions

# Packet capture on Cisco IOS (embedded capture)
monitor capture CAP interface GigabitEthernet0/0 both
monitor capture CAP match ipv4 host 10.0.0.5 host 10.0.0.1
monitor capture CAP start
# ... test traffic
monitor capture CAP stop
show monitor capture CAP
monitor capture CAP export flash:cap.pcap
```

### 17.2 Cisco ASA

```bash
# Connection table
show conn
show conn address 10.0.0.5
show conn count

# NAT
show nat
show nat detail
show xlate

# Packet tracer (THE most important ASA debug tool)
# Simulates what the ASA would do with a hypothetical packet without sending it
packet-tracer input OUTSIDE tcp 203.0.113.5 54321 10.0.0.5 443 detailed
# Output: shows each inspection phase, NAT translation, ACL match, result (allow/drop)

# Capture on ASA interfaces
capture CAP interface OUTSIDE match tcp host 203.0.113.5 host 10.0.0.5 eq 443
capture CAP interface INSIDE  match tcp host 203.0.113.5 host 10.0.0.5 eq 443
# View capture
show capture CAP
# Export as pcap
show capture CAP write-header url disk0:/cap.pcap
# On ASA: copy disk0:/cap.pcap tftp://TFTP_SERVER/cap.pcap

# ACL hit counts
show access-list ACL_NAME
# Shows: hitcnt for each rule

# Threat detection
show threat-detection rate
show threat-detection statistics host 10.0.0.5   # attacks from/to host

# Inspect engine state
show service-policy inspect
show conn all
```

### 17.3 Cisco FTD (Firepower Threat Defense)

```bash
# FTD uses both LINA (ASA) and Snort for inspection
# Access FTD CLI
expert            # drops to Linux shell
sudo su           # if needed

# LINA (ASA layer)
system support diagnostic-cli
> show conn
> packet-tracer input OUTSIDE tcp 203.0.113.5 54321 10.0.0.5 443 detailed

# Snort bypassing (debugging FTD-specific drops)
system support diagnostic-cli
> show asp table classify domain permit
> show asp drop

# Show Snort policy rules applied
system support view-files
# /var/sf/detection_engines/*/rules/

# FTD packet capture (unified capture that includes both LINA and Snort)
capture CAPTEST interface OUTSIDE trace match tcp host 203.0.113.5 host 10.0.0.5 eq 443
show capture CAPTEST detail
# 'trace' keyword makes ASA trace the packet through inspection engines

# Snort statistics
system support diagnostic-cli
> show snort statistics
```

---

## 18. Platform-Specific: Palo Alto Networks (PAN-OS)

### 18.1 Packet Captures

```bash
# PAN-OS has 4 capture stages:
# Stage 1: client to PAN (ingress, pre-firewall)
# Stage 2: PAN processing (policy lookup, NAT)
# Stage 3: PAN to server (egress, post-NAT)
# Stage 4: Dropped packets

# Via CLI:
debug dataplane packet-diag set capture stage drop file /tmp/drop.pcap
debug dataplane packet-diag set capture stage receive file /tmp/recv.pcap
debug dataplane packet-diag set capture stage transmit file /tmp/trans.pcap

# Set filter
debug dataplane packet-diag set filter match source 10.0.0.5 destination 10.0.0.1 \
  proto 6 destport 443

# Enable capture
debug dataplane packet-diag set capture on

# Test traffic...

# Disable and retrieve
debug dataplane packet-diag set capture off
scp admin@PAN_IP:/tmp/drop.pcap .

# View at CLI
debug dataplane packet-diag show capture stage drop detail
```

### 18.2 Test Packet and Policy Lookup

```bash
# Policy lookup (equivalent of ASA packet-tracer)
test security-policy-match source 10.0.0.5 destination 10.0.0.1 \
  destination-port 443 protocol 6 from TRUST to UNTRUST

# NAT lookup
test nat-policy-match source 10.0.0.5 from TRUST to UNTRUST \
  destination 8.8.8.8 protocol 6 destination-port 443

# Application identification test
show session all filter source 10.0.0.5 destination 10.0.0.1 destination-port 443

# Show active sessions
show session all
show session id SESSION_ID

# Session table statistics
show session info

# Counter statistics (per-dataplane)
show counter global filter severity drop
show counter global filter packet-filter yes
# Shows why packets are being dropped by category

# Threat logs (Snort equivalent in PAN-OS)
show log threat direction equal forward
```

### 18.3 Log Query

```bash
# Traffic logs
show log traffic source equal 10.0.0.5 direction equal forward

# Threat logs  
show log threat subtype equal vulnerability

# URL filtering logs
show log url source equal 10.0.0.5

# System logs
show log system
```

---

## 19. Platform-Specific: Juniper SRX / EX

### 19.1 SRX Flow Debugging

```bash
# SRX uses a "flow" processing model (same as Cisco ASA stateful)
# Show flow sessions
show security flow session
show security flow session source-prefix 10.0.0.5/32

# Session statistics
show security flow session summary

# Policy lookup
show security policies from-zone trust to-zone untrust
show security policies hit-count

# Flow tracing (packet debugging)
# Step 1: Set trace options
set security flow traceoptions file fw-debug size 10m files 5
set security flow traceoptions flag basic-datapath
set security flow traceoptions packet-filter MY_FILTER source-prefix 10.0.0.5/32
set security flow traceoptions packet-filter MY_FILTER destination-prefix 10.0.0.1/32

# Step 2: Commit
commit

# Step 3: View trace
show log fw-debug | match "10.0.0.5"

# Step 4: Disable
delete security flow traceoptions
commit

# NAT
show security nat source rule all
show security nat destination rule all
show security nat static rule all
show security nat source persistent-nat-table all

# IPS
show security idp status
show security idp attack table
```

### 19.2 EX Switch (for FW-adjacent switch debugging)

```bash
# Interface errors
show interfaces ge-0/0/0 detail
show interfaces ge-0/0/0 statistics

# VLAN
show vlans
show ethernet-switching table

# Spanning tree
show spanning-tree interface

# MAC table
show ethernet-switching table vlan VLAN_NAME
```

---

## 20. Cloud Firewalls: AWS, GCP, Azure

### 20.1 AWS

```bash
# VPC Flow Logs: the primary tool for AWS network debugging
# Enable VPC Flow Logs (if not already enabled)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-XXXXXXXXX \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs \
  --deliver-logs-permission-arn arn:aws:iam::ACCOUNT:role/FlowLogsRole

# Query Flow Logs with CloudWatch Insights
# In AWS Console -> CloudWatch -> Logs Insights:
# fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action, logStatus
# | filter dstAddr = "10.0.0.5" and dstPort = 443
# | stats count() by action
# | sort @timestamp desc

# Or: export to S3 and use Athena for SQL queries
# Athena query on Flow Logs:
# SELECT srcaddr, dstaddr, srcport, dstport, protocol, action, count(*) as count
# FROM vpc_flow_logs
# WHERE dstaddr = '10.0.0.5' AND dstport = 443
# GROUP BY srcaddr, dstaddr, srcport, dstport, protocol, action

# Security Group analysis
aws ec2 describe-security-groups --group-ids sg-XXXXXXXXX \
  --query 'SecurityGroups[0].IpPermissions'

# Check effective SG rules on instance
aws ec2 describe-network-interface-attribute \
  --network-interface-id eni-XXXXXXXXX \
  --attribute groupSet

# Network ACL (stateless, evaluated before SG)
aws ec2 describe-network-acls --network-acl-ids acl-XXXXXXXXX

# Reachability Analyzer (automated path analysis between two endpoints)
aws ec2 create-network-insights-path \
  --source eni-SOURCE \
  --destination eni-DESTINATION \
  --protocol tcp \
  --destination-port 443

aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-XXXXXXXXX

aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-XXXXXXXXX
# Shows: hop-by-hop path, where and why traffic is blocked

# AWS WAF logs
aws wafv2 get-logging-configuration --resource-arn ARN_OF_WEBACL
# Logs go to Kinesis Data Firehose; query with Athena

# GuardDuty findings (threat detection)
aws guardduty list-findings --detector-id DETECTOR_ID
aws guardduty get-findings --detector-id DETECTOR_ID --finding-ids FINDING_ID
```

**AWS Network Debugging Architecture:**

```
Internet
   |
[IGW] <-- VPC Flow Logs (srcAddr, dstAddr, action)
   |
[Route Table]
   |
[NACL] <-- Stateless; check inbound AND outbound rules
   |
[Subnet]
   |
[Security Group] <-- Stateful; only check inbound (return auto-allowed)
   |
[ENI / Instance]
   |
[Host Firewall / iptables]
```

### 20.2 GCP

```bash
# VPC Flow Logs (per-subnet)
# Enable
gcloud compute networks subnets update SUBNET_NAME \
  --region=REGION \
  --enable-flow-logs \
  --logging-metadata=include-all \
  --logging-aggregation-interval=interval-5-sec \
  --logging-flow-sampling=1.0

# Query in Cloud Logging / Log Analytics:
# resource.type="gce_subnetwork"
# logName="projects/PROJECT/logs/compute.googleapis.com%2Fvpc_flows"
# jsonPayload.connection.dest_ip="10.0.0.5"
# jsonPayload.connection.dest_port=443

# Firewall rules (GCP calls them "firewall rules")
gcloud compute firewall-rules list
gcloud compute firewall-rules describe RULE_NAME
# Note: GCP firewall is distributed (enforced at VM hypervisor), not a hop

# Firewall Insights (automated anomaly detection)
# Enabled in Cloud Firewall product; shows: shadowed rules, overly permissive rules, unused rules

# Connectivity Tests (like AWS Reachability Analyzer)
gcloud network-management connectivity-tests create TEST_NAME \
  --source-instance=projects/PROJECT/zones/ZONE/instances/VM_NAME \
  --destination-instance=projects/PROJECT/zones/ZONE/instances/VM2_NAME \
  --protocol=tcp \
  --destination-port=443

gcloud network-management connectivity-tests run TEST_NAME
gcloud network-management connectivity-tests get-result TEST_NAME

# Routes
gcloud compute routes list
gcloud compute routes describe ROUTE_NAME

# Check effective routes from VM's perspective
gcloud compute instances get-effective-firewalls VM_NAME --zone=ZONE
```

### 20.3 Azure

```bash
# NSG Flow Logs (Network Security Group)
# Enable via Azure Portal: NSG -> Monitoring -> NSG Flow Logs
# Or CLI:
az network watcher flow-log create \
  --resource-group RG \
  --location eastus \
  --name FLOWLOG_NAME \
  --nsg NSG_NAME \
  --storage-account STORAGE_ACCOUNT_ID \
  --enabled true \
  --retention 7 \
  --format JSON \
  --log-version 2

# Traffic Analytics (like GuardDuty; built on top of flow logs + ML)
# Enable via: NSG Flow Logs -> Traffic Analytics -> Enable

# Network Watcher: IP Flow Verify (test if specific packet would be allowed)
az network watcher test-ip-flow \
  --resource-group RG \
  --direction Inbound \
  --local 10.0.0.5:443 \
  --remote 203.0.113.5:54321 \
  --protocol TCP \
  --nic NIC_NAME \
  --vm VM_NAME

# Next Hop (trace routing)
az network watcher show-next-hop \
  --resource-group RG \
  --vm VM_NAME \
  --nic NIC_NAME \
  --source-ip 10.0.0.5 \
  --dest-ip 8.8.8.8

# Connection Troubleshoot (connection test with path visualization)
az network watcher test-connectivity \
  --resource-group RG \
  --source-resource VM_NAME \
  --dest-address target.example.com \
  --dest-port 443 \
  --protocol Tcp

# Packet capture (Azure-side, stored in Storage Account)
az network watcher packet-capture create \
  --resource-group RG \
  --vm VM_NAME \
  --name CAP_NAME \
  --storage-account STORAGE_NAME \
  --filter "[{localIPAddress: '10.0.0.5', protocol: 'TCP', remotePort: '443'}]"

az network watcher packet-capture stop --resource-group RG --name CAP_NAME --location eastus

# Show effective NSG rules on NIC
az network nic list-effective-nsg \
  --resource-group RG \
  --name NIC_NAME
```

---

## 21. eBPF-based Networking Debugging (Cilium, XDP)

### 21.1 Cilium Monitor

```bash
# Cilium replaces iptables in many Kubernetes environments
# Monitor packet events in real-time
cilium monitor

# Filter by node or pod
cilium monitor --from-pod default/my-pod
cilium monitor --to-pod default/target-pod

# Show drops only
cilium monitor --type drop

# Show with hex dump
cilium monitor --hex

# Policy verdict events
cilium monitor --type policy-verdict

# Debug specific endpoint
ENDPOINT_ID=$(cilium endpoint list | grep my-pod | awk '{print $1}')
cilium monitor --related-to $ENDPOINT_ID

# Hubble (Cilium's observability layer)
# List recent flows
hubble observe --last 100

# Filter by pod
hubble observe --pod default/my-pod --last 50

# Show drops
hubble observe --verdict DROPPED --last 50

# Show policy verdicts
hubble observe --type policy-verdict --last 50

# Service map
hubble observe --namespace default --last 200 --output json \
  | jq '{src: .source.pod_name, dst: .destination.pod_name, verdict: .verdict}'

# Hubble UI (if deployed)
cilium hubble ui   # port-forwards and opens browser
```

### 21.2 bpftrace for Custom Firewall Tracing

```bash
# Trace XDP drops
bpftrace -e '
tracepoint:xdp:xdp_exception {
  printf("XDP drop on dev %d, act %d\n", args->ifindex, args->act);
}'

# Trace iptables rule matches (via kprobe on ipt_do_table)
bpftrace -e '
kretprobe:ipt_do_table /retval == 0/ {
  printf("iptables DROP: %s\n", comm);
}'

# Trace TCP connection state changes
bpftrace -e '
kprobe:tcp_set_state {
  $sk = (struct sock *)arg0;
  $newstate = arg1;
  printf("TCP state: %d -> %d\n", $sk->sk_state, $newstate);
}'

# Trace nf_hook_slow (netfilter hook execution)
bpftrace -e '
kprobe:nf_hook_slow {
  printf("netfilter hook: pf=%d hook=%d\n", arg1, arg2);
}'
```

---

## 22. Kubernetes Network Policy Debugging

### 22.1 Basic Policy Testing

```bash
# View NetworkPolicies
kubectl get networkpolicy -n NAMESPACE
kubectl describe networkpolicy POLICY_NAME -n NAMESPACE

# Test connectivity between pods
kubectl exec -n NAMESPACE POD_A -- nc -zv POD_B_IP PORT
kubectl exec -n NAMESPACE POD_A -- curl -v http://POD_B_IP:PORT/

# Test from a debug pod (when pod doesn't have nc/curl)
kubectl run debug --image=nicolaka/netshoot -it --rm \
  -- bash -c "nc -zv TARGET_POD_IP 443"

# Verify DNS resolution within cluster
kubectl exec POD_A -- nslookup service.namespace.svc.cluster.local

# Check kube-proxy iptables rules
# On the node:
iptables -t nat -L KUBE-SERVICES -n -v --line-numbers | grep SERVICE_NAME
iptables -t nat -L KUBE-SVC-XXXXXXXXX -n -v

# Check for dropped traffic at node level
iptables -L -n -v | grep DROP | sort -rn -k 1

# Cilium: check endpoint policy
cilium endpoint list
ENDPOINT_ID=$(cilium endpoint list | grep "my-pod" | awk '{print $1}')
cilium endpoint get $ENDPOINT_ID
cilium policy get   # show entire policy tree
```

### 22.2 Kubernetes Network Debugging Pods

```bash
# netshoot: the definitive network debug container
kubectl run netshoot --image=nicolaka/netshoot -it --rm -- bash
# Contains: tcpdump, tshark, iperf3, nmap, mtr, dig, curl, ncat, socat, hping3, etc.

# Run on specific node (to debug host-network)
kubectl run netshoot --image=nicolaka/netshoot \
  --overrides='{"spec":{"hostNetwork":true,"nodeName":"node-name"}}' \
  -it --rm -- bash

# Capture traffic on pod interface from node
# Get pod's netns
CONTAINER_ID=$(kubectl get pod MY_POD -o jsonpath='{.status.containerStatuses[0].containerID}' | cut -d/ -f3)
NETNS=$(crictl inspect $CONTAINER_ID | jq -r '.info.runtimeSpec.linux.namespaces[] | select(.type=="network") | .path')

# Run tcpdump in pod's netns
nsenter --net=$NETNS tcpdump -i eth0 -nn -s 0 -w /tmp/pod-capture.pcap
```

---

## 23. Log Analysis and SIEM Integration

### 23.1 Structured Log Query Patterns

```bash
# iptables: parse LOG target output with structured extraction
journalctl -k | grep "IN=" | \
  awk '{
    for(i=1;i<=NF;i++) {
      if($i~/^IN=|OUT=|SRC=|DST=|PROTO=|DPT=|SPT=/) printf $i" "
    }
    print ""
  }' | sort | uniq -c | sort -rn | head -20

# Extract top blocked destinations
journalctl -k | grep "FW-DROP" | \
  grep -oP 'DST=\K[\d.]+' | sort | uniq -c | sort -rn | head -10

# Extract top blocked ports
journalctl -k | grep "FW-DROP" | \
  grep -oP 'DPT=\K[\d]+' | sort | uniq -c | sort -rn | head -10

# Parse firewall logs with awk into CSV for analysis
journalctl -k --since "1 hour ago" | grep "FW-" | \
awk '
/FW-/ {
  ts=$1" "$2" "$3
  match($0, /SRC=([0-9.]+)/, src)
  match($0, /DST=([0-9.]+)/, dst)
  match($0, /DPT=([0-9]+)/, dpt)
  match($0, /PROTO=([A-Z]+)/, proto)
  printf "%s,%s,%s,%s,%s\n", ts, src[1], dst[1], dpt[1], proto[1]
}' > /tmp/fw_logs.csv

# Analyze with GoAccess (real-time log analysis)
# Or pipe to standard tools:
sort -t, -k4 /tmp/fw_logs.csv | uniq -c -f3 | sort -rn
```

### 23.2 Real-time Log Monitoring

```bash
# Watch firewall logs in real-time
journalctl -k -f | grep --line-buffered "FW-"

# Watch with color
journalctl -k -f | grep --color=always -E "DROP|REJECT|ACCEPT"

# Log rate monitoring (alert if drops spike)
watch -n 5 'journalctl -k --since "5 minutes ago" | grep FW-DROP | wc -l'

# pf on BSD: real-time pflog
tcpdump -i pflog0 -nn -l | grep 'block'
```

### 23.3 Log Aggregation Patterns

For production environments, ship firewall logs to a central SIEM:

```bash
# rsyslog: forward kernel logs to remote syslog
cat >> /etc/rsyslog.d/fw-forward.conf << 'EOF'
:msg, contains, "FW-" @@SYSLOG_SERVER:514
EOF
systemctl restart rsyslog

# Vector (high-performance log shipper) - Rust-based
# vector.toml:
# [sources.kernel_logs]
# type = "journald"
# include_units = [""]
# 
# [transforms.fw_filter]
# type = "filter"
# inputs = ["kernel_logs"]
# condition = '.message contains "FW-"'
#
# [sinks.elasticsearch]
# type = "elasticsearch"
# inputs = ["fw_filter"]
# endpoints = ["https://es-cluster:9200"]

# Fluent Bit
# Use kernel input plugin + grep filter + Elasticsearch/Loki output

# OpenTelemetry Collector (CNCF)
# Configure with hostmetrics receiver + file log receiver
# Forward to any OTLP-compatible backend (Jaeger, Prometheus, Grafana Tempo)
```

---

## 24. Structured Troubleshooting Methodology

### 24.1 The 7-Phase Firewall Debug Process

```
PHASE 1: REPRODUCE
  - Document exact symptoms, error messages, time of occurrence
  - Identify the failing 5-tuple: src_ip, src_port, dst_ip, dst_port, proto
  - Identify direction: ingress or egress?

PHASE 2: LAYER 1/2 ELIMINATION
  - Check interface state (ip link show)
  - Check ARP cache (ip neigh show)
  - Verify VLAN config matches both ends
  - Check for physical errors (ethtool -S)

PHASE 3: ROUTING VERIFICATION
  - From sender: ip route get DST_IP
  - From firewall: ip route get DST_IP from SRC_IP
  - Verify symmetric return path (asymmetric routing kills stateful FW)

PHASE 4: FIREWALL STATE
  - Check connection table for existing stale entry (conntrack -L | grep SRC)
  - Check table utilization (conntrack -S)
  - Verify correct state (ESTABLISHED vs SYN_SENT vs INVALID)

PHASE 5: POLICY EVALUATION
  - Trace packet through policy (iptables TRACE, nft monitor trace, packet-tracer)
  - Check ACL/rule hit counters
  - Verify NAT rules (conntrack -L -n)

PHASE 6: PACKET CAPTURE (GROUND TRUTH)
  - Capture on ingress and egress interfaces simultaneously
  - Confirm packet arrives at FW (ingress capture)
  - Confirm packet leaves FW (egress capture)
  - If in but not out: FW is dropping it
  - Compare SEQ numbers across captures

PHASE 7: APPLICATION VERIFICATION
  - Test with nc/socat (bypass application bugs)
  - Test with curl (HTTP-level)
  - Test TLS handshake (openssl s_client)
  - Verify service is listening on target (ss -tlnp)
```

### 24.2 Decision Tree

```
Connection fails?
│
├── No ARP response
│     └── L2 issue: VLAN mismatch, STP blocking, NIC down
│
├── ARP OK, ping fails
│     ├── Routing wrong → check ip route get DST
│     ├── ICMP blocked by FW → test with TCP (hping3 -S -p 80)
│     └── Host firewall blocking → check iptables on target
│
├── Ping OK, TCP SYN not answered
│     ├── FW dropping SYN → TRACE rules, capture on both sides
│     ├── No service listening → ss -tlnp on target
│     └── Wrong routing → asymmetric path, SYN reaches wrong interface
│
├── TCP SYN-ACK sent, connection drops immediately
│     ├── FW RST injection → check RST TTL vs server TTL
│     ├── ACL blocking ACK → stateless ACL on return path
│     └── NAT translation fails → conntrack -L -n
│
├── Connection established, data fails
│     ├── MTU/PMTU issue → test with small payload first (curl with small data)
│     ├── FW idle timeout → increase tcp_conntrack_timeout
│     ├── L7 FW inspection drop → check NGFW logs, disable SSL inspection temporarily
│     └── Application protocol incompatibility → test with raw nc first
│
└── Connection works intermittently
      ├── FW state table full → conntrack -S (count near max)
      ├── ECMP hashing (different paths) → use paris-traceroute
      ├── Port exhaustion (SNAT) → ss -tn state time-wait | wc -l
      └── Hardware error → ethtool -S (increasing error counters)
```

---

## 25. Architecture View

### 25.1 Firewall Diagnostic Points

```
Internet
   |
[ISP Router] ---- capture point A (before FW)
   |
[WAN Interface] ← tcpdump/tshark/vendor capture
[FIREWALL]       ← policy trace, state table, NAT, logs
[LAN Interface] ← tcpdump/tshark/vendor capture
   |               capture point B (after FW)
[Core Switch]
   |
[Server / Pod]   ← host firewall, conntrack, socket stats
```

### 25.2 Layered Inspection Model

```
PACKET INGRESS PATH (Linux Netfilter)
--------------------------------------
NIC/Driver → XDP → raw socket →
  netfilter PREROUTING (raw table: TRACE)
    → nf_conntrack (new/established/invalid/related)
    → netfilter PREROUTING (mangle table: DSCP/mark)
    → netfilter PREROUTING (nat table: DNAT)
  → Routing Decision (ip_route_input)
  → netfilter FORWARD (mangle table)
    → netfilter FORWARD (filter table: policy enforcement)  ← MOST DROPS HERE
  → netfilter POSTROUTING (mangle table)
    → netfilter POSTROUTING (nat table: SNAT/MASQUERADE)
NIC/Driver → Wire

PACKET LOCAL INPUT PATH
-----------------------
  → netfilter INPUT (filter table)
  → Socket receive buffer
  → Application
```

### 25.3 Multi-Tier Security Architecture

```
[Public Internet]
       |
  [Edge FW / WAF]     ← L7 inspection, rate limiting, geo-blocking
       |
  [DMZ / Perimeter]
       |
  [Internal FW]       ← segmentation, micro-segmentation
       |
  [Compute Tier]
  /    |    \
[Web] [App] [DB]      ← host firewalls, eBPF/Cilium, security groups
       |
  [Management Network]  ← OOB (out-of-band), separate firewall zone
```

---

## 26. Threat Model and Diagnostic Safety

### 26.1 Threat Model for Diagnostic Activities

| Diagnostic Activity        | Risk                                          | Mitigation                                              |
|---------------------------|-----------------------------------------------|---------------------------------------------------------|
| `debug ip nat` on Cisco   | CPU saturation → device reload                | Use host filter: `debug ip nat 10.0.0.5`; set timeout  |
| Packet capture in prod     | Sensitive data in pcap (PII, credentials)    | Filter to IP/port; encrypt pcap; restrict access; delete after |
| `conntrack -F`             | Drops ALL existing connections                | Only in maintenance window; have rollback               |
| nmap aggressive scan       | Triggers IDS/IPS alerts; rate-limits devices  | Coordinate with security team; off-hours                |
| iptables TRACE rule         | High log volume → syslog flood → disk fill   | Narrow filter; set log rate limit; remove immediately   |
| `tcpdump -i any`           | Captures all interfaces; high CPU on busy box | Limit with BPF filter; use `-s 96` for headers only     |
| hping3 --flood             | Network disruption, DoS                       | Never use --flood in production                          |

### 26.2 Diagnostic Data Handling

```bash
# Encrypt pcap files at rest
openssl enc -aes-256-cbc -in capture.pcap -out capture.pcap.enc -k PASSPHRASE

# Anonymize IP addresses before sharing pcap (for vendor support)
tcpdprewrite --seed=12345 --pnat=10.0.0.0/8:192.168.0.0/8 \
  -i capture.pcap -o anonymized.pcap
# (tcpreplay suite)

# Strip payload (headers only for privacy)
tcpdump -i eth0 -s 96 -w /tmp/headers_only.pcap   # 96 bytes = IP+TCP headers only

# Scrub credentials from HTTP captures
# Never capture -A (ASCII) on production HTTPS without ensuring TLS inspection is off
```

### 26.3 Change Management for Firewall Rules

```bash
# ALWAYS backup before any rule change
iptables-save > /backup/iptables-$(date +%Y%m%d-%H%M%S).txt
nft list ruleset > /backup/nft-$(date +%Y%m%d-%H%M%S).txt

# Use at(1) as a safety net (auto-rollback if you lose connectivity)
at now + 5 minutes << 'EOF'
iptables-restore < /backup/iptables-LAST_GOOD.txt
EOF
# If change works: atrm <job_id> to cancel the rollback

# Use ansible/terraform for idempotent FW rule management
# Never make ad-hoc manual changes in production without a change ticket
```

---

## 27. References

### Core Documentation
- **Linux Netfilter**: https://www.netfilter.org/documentation/
- **nftables wiki**: https://wiki.nftables.org/
- **Linux ip-route(8)**: `man ip-route`
- **Linux conntrack-tools**: https://conntrack-tools.netfilter.org/

### Tools
- **tcpdump manual**: https://www.tcpdump.org/manpages/tcpdump.1.html
- **Wireshark Display Filters**: https://www.wireshark.org/docs/dfref/
- **nmap reference guide**: https://nmap.org/book/man.html
- **hping3 manual**: http://www.hping.org/manpage.html
- **mtr GitHub**: https://github.com/traviscross/mtr
- **iperf3**: https://iperf.fr/iperf-doc.php

### Cloud
- **AWS VPC Flow Logs**: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- **AWS Network Reachability Analyzer**: https://docs.aws.amazon.com/vpc/latest/reachability/
- **GCP Connectivity Tests**: https://cloud.google.com/network-intelligence-center/docs/connectivity-tests
- **Azure Network Watcher**: https://docs.microsoft.com/en-us/azure/network-watcher/

### eBPF and CNCF
- **BPF and XDP Reference Guide (Cilium)**: https://docs.cilium.io/en/stable/bpf/
- **bpftrace**: https://github.com/iovisor/bpftrace
- **Cilium Hubble**: https://docs.cilium.io/en/stable/observability/hubble/
- **XDP Tutorial**: https://github.com/xdp-project/xdp-tutorial

### Books
- *TCP/IP Illustrated, Vol. 1* — W. Richard Stevens
- *The Linux Networking Cookbook* — Carla Schroder
- *Linux Firewall Workshop* — Bob Toxen
- *Network Security Assessment* — Chris McNab

### RFCs
- RFC 793: TCP
- RFC 791: IP
- RFC 792: ICMP
- RFC 3022: NAT
- RFC 5101: IPFIX
- RFC 7011: IPFIX Protocol

---

## 28. Next 3 Steps

**Step 1: Build Your Diagnostic Toolkit Container**

Create a reproducible debug container you can deploy to any node:

```dockerfile
FROM nicolaka/netshoot:latest
RUN apt-get update && apt-get install -y \
    hping3 nmap tcptraceroute sslyze conntrack ipset \
    nftables iperf3 netperf socat bpftrace bpftool \
    && rm -rf /var/lib/apt/lists/*
```

```bash
docker build -t fw-debug:local .
# Deploy to any node for instant diagnostic capability
kubectl run fw-debug --image=fw-debug:local -it --rm \
  --overrides='{"spec":{"hostNetwork":true}}' -- bash
```

**Step 2: Implement Continuous Flow Visibility**

Deploy goflow2 + Grafana/Loki in your environment for always-on flow telemetry:

```bash
# Using Helm on Kubernetes:
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --set promtail.enabled=true \
  --set grafana.enabled=true

# Deploy goflow2 as DaemonSet to collect NetFlow from all nodes
# Configure your firewall/router to export NetFlow v9/IPFIX to goflow2 NodePort
```

**Step 3: Build a Firewall Regression Test Suite**

Write automated connectivity tests that run after every firewall rule change:

```go
// fw_test.go — example structure
package firewall_test

import (
    "net"
    "testing"
    "time"
)

func TestAllowHTTPS(t *testing.T) {
    conn, err := net.DialTimeout("tcp", "10.0.0.5:443", 5*time.Second)
    if err != nil {
        t.Fatalf("HTTPS to 10.0.0.5 should be allowed: %v", err)
    }
    conn.Close()
}

func TestBlockHTTP(t *testing.T) {
    _, err := net.DialTimeout("tcp", "10.0.0.5:80", 2*time.Second)
    if err == nil {
        t.Fatal("HTTP to 10.0.0.5 should be blocked but connection succeeded")
    }
}
```

```bash
# Run as pre/post change validation
go test ./... -v -timeout 60s
# Integrate into your CI/CD pipeline with: kubectl exec / SSH to test runner in each zone
```

---

*Last updated: 2026 | Author: Security Systems Engineering | Classification: Internal Technical Reference*

Now let me build the comprehensive guide:**~4,500 lines, 28 sections** — here's the summary of what's covered:

**Summary (4-line version):** The guide is organized as a layered diagnostic methodology — you eliminate lower layers before assuming firewall policy is at fault, because the majority of "firewall bugs" are actually asymmetric routing, MTU mismatch, conntrack table exhaustion, or ARP/VLAN misconfigurations. Every section gives you exact commands, expected output interpretation, and failure mode tables. The architecture section shows exactly where in the Netfilter processing path a packet can be dropped. The cloud section treats VPC Flow Logs, Reachability Analyzer, and Connectivity Tests as first-class tools. eBPF/Cilium and Kubernetes NetworkPolicy are covered as production-grade modern alternatives.

**Key sections beyond ping/traceroute:**

- **Layer 2**: `arping`, `ethtool -S`, VLAN tagging verification, STP state inspection — the silent killers that look like firewall blocks
- **hping3 / nping**: surgical packet crafting to test exact policy conditions (TCP flags, TTL, fragmentation, source IP)
- **nmap**: ACK scan to distinguish stateful vs. stateless FW behavior; idle scan for source-IP-specific rule testing
- **Packet capture methodology**: simultaneous ingress/egress capture on both FW interfaces — if packet is in `wan.pcap` but not `lan.pcap`, the FW dropped it
- **conntrack**: state table inspection, overflow diagnosis, timeout tuning — the most overlooked stateful FW failure mode
- **iptables TRACE + nft monitor trace**: exact rule-by-rule packet tracing in the kernel
- **Vendor specifics**: Cisco `packet-tracer`, PAN-OS 4-stage capture, Juniper flow tracing, BSD `pfctl -ss` + `pflog0`
- **Cloud tools**: AWS Reachability Analyzer, GCP Connectivity Tests, Azure IP Flow Verify — native path analysis
- **Flow telemetry**: `nfdump`, `goflow2` for retrospective traffic matrix analysis without needing live captures
- **eBPF/bpftrace**: kernel-level firewall event tracing without modifying rules

**Next 3 Steps** at the end: debug container (Dockerfile), always-on flow telemetry (goflow2 + Loki), and a Go-based firewall regression test suite for change validation.