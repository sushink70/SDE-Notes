# Network Security: Complete Engineering Reference

> **Audience:** Senior security/systems engineers. Assumes kernel internals, cloud architecture, and protocol RFC familiarity.  
> **Scope:** Linux kernel networking stack → protocol internals → routing/switching → cloud networking → threat modeling → defense-in-depth.  
> **Philosophy:** Security-by-default, least-privilege, defense-in-depth, zero-trust posture at every layer.

---

## Table of Contents

1. [Foundational Models: OSI & TCP/IP](#1-foundational-models-osi--tcpip)
2. [Linux Kernel Networking Stack](#2-linux-kernel-networking-stack)
3. [Netfilter, iptables, nftables](#3-netfilter-iptables-nftables)
4. [eBPF & XDP — Kernel-Bypass Security](#4-ebpf--xdp--kernel-bypass-security)
5. [Network Namespaces, cgroups, veth, bridge](#5-network-namespaces-cgroups-veth-bridge)
6. [Protocol Deep Dives](#6-protocol-deep-dives)
   - 6.1 Ethernet & L2
   - 6.2 ARP / NDP
   - 6.3 IP (v4 & v6)
   - 6.4 ICMP / ICMPv6
   - 6.5 TCP
   - 6.6 UDP
   - 6.7 DNS
   - 6.8 TLS 1.3
   - 6.9 QUIC
7. [Routing — L3 Control & Data Plane](#7-routing--l3-control--data-plane)
8. [BGP Deep Dive & Security](#8-bgp-deep-dive--security)
9. [Switching — L2 Control & Data Plane](#9-switching--l2-control--data-plane)
10. [IPsec & WireGuard](#10-ipsec--wireguard)
11. [Network Segmentation & Microsegmentation](#11-network-segmentation--microsegmentation)
12. [Cloud Networking](#12-cloud-networking)
    - 12.1 AWS VPC
    - 12.2 Azure VNet
    - 12.3 GCP VPC
    - 12.4 Overlay Networking (VXLAN, Geneve)
13. [Zero Trust Networking](#13-zero-trust-networking)
14. [Kubernetes & CNCF Network Security](#14-kubernetes--cncf-network-security)
15. [Service Mesh Security (Cilium, Istio)](#15-service-mesh-security-cilium-istio)
16. [DDoS — Taxonomy, Attack Vectors, Mitigations](#16-ddos--taxonomy-attack-vectors-mitigations)
17. [Network Intrusion Detection & Prevention](#17-network-intrusion-detection--prevention)
18. [Attack Techniques & TTPs](#18-attack-techniques--ttps)
19. [Threat Model: Network Security](#19-threat-model-network-security)
20. [Observability & Forensics](#20-observability--forensics)
21. [Compliance & Standards](#21-compliance--standards)
22. [Next 3 Steps & References](#22-next-3-steps--references)

---

## 1. Foundational Models: OSI & TCP/IP

### 1.1 Why Models Matter for Security

Models define **trust boundaries**, **protocol transitions**, and **attack surfaces**. Every layer introduces new protocols, parsers, and state machines — each a potential vulnerability surface. A security engineer must know precisely which kernel subsystem, userspace daemon, or hardware component owns each layer, because that determines where controls are enforced and where they can be bypassed.

### 1.2 OSI Model — Security-Annotated

```
Layer 7  Application    HTTP/2, gRPC, WebSocket, DNS     — Input validation, auth, AuthZ
Layer 6  Presentation   TLS, compression, encoding        — Cipher suite, cert validation
Layer 5  Session        TLS handshake, RPC sessions       — Session fixation, replay
Layer 4  Transport      TCP, UDP, SCTP, QUIC              — SYN flood, port scanning, RST injection
Layer 3  Network        IPv4, IPv6, ICMP, IPsec           — IP spoofing, fragmentation attacks
Layer 2  Data Link      Ethernet, 802.1Q, STP, ARP        — ARP poisoning, VLAN hopping, MAC flood
Layer 1  Physical       Cable, optical, RF, NIC           — Tap, side-channel, physical access
```

**Key insight:** Upper layers trust lower layers implicitly unless explicitly validated. A forged IP packet at L3 (IP spoofing) can bypass application-layer controls that rely solely on `REMOTE_ADDR`. Defense must be **layered** — no single layer's controls are sufficient.

### 1.3 TCP/IP Model vs. OSI

```
TCP/IP Model          OSI Equivalent         Key Protocols
──────────────────────────────────────────────────────────
Application           5, 6, 7                HTTP, DNS, TLS, SSH, SMTP
Transport             4                      TCP, UDP, QUIC, SCTP
Internet              3                      IPv4, IPv6, ICMP, IPsec, OSPF, BGP
Link                  1, 2                   Ethernet, Wi-Fi, ARP, NDP
```

The TCP/IP model is what the Linux kernel actually implements. Understanding its socket API, sk_buff (socket buffer), and the kernel's protocol dispatch is foundational for writing kernel-space security tools.

### 1.4 Encapsulation & Decapsulation Attack Surface

Each encapsulation step is a trust boundary crossing:

```
[Ethernet Frame]
  └─ [IP Packet]
       └─ [TCP Segment]
            └─ [TLS Record]
                 └─ [HTTP/2 Frame]
                      └─ [Application Data]
```

Every layer **parses** the next layer. Parsing is where vulnerabilities live (buffer overflows, integer overflows, state machine confusion, protocol confusion attacks). Each parser must:
- Validate length fields before use
- Handle malformed/truncated input
- Enforce maximum nesting depth
- Be immune to confused-deputy attacks (e.g., HTTP request smuggling exploiting ambiguity between Content-Length and Transfer-Encoding)

---

## 2. Linux Kernel Networking Stack

### 2.1 Architecture Overview

```
User Space
  ├── Socket API (sys_send, sys_recv, sys_connect, sys_bind)
  │       ↕  syscall boundary
Kernel Space
  ├── Socket Layer (SOCK_STREAM, SOCK_DGRAM, SOCK_RAW)
  ├── Protocol Families (AF_INET, AF_INET6, AF_UNIX, AF_PACKET)
  ├── Transport Layer (TCP, UDP, SCTP, DCCP)
  ├── Network Layer (IPv4/IPv6, routing, forwarding)
  ├── Netfilter Hooks (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING)
  ├── Traffic Control (tc/qdisc — shaping, scheduling, policing)
  ├── Network Device Abstraction (struct net_device)
  ├── Driver Layer (NIC driver — e1000, ixgbe, mlx5, virtio-net)
  └── Hardware (NIC, SmartNIC, DPU, SR-IOV VF)
```

### 2.2 sk_buff (Socket Buffer) — The Central Data Structure

`sk_buff` (defined in `include/linux/skbuff.h`) is the kernel's unified packet representation. Understanding it is essential for writing kernel modules, eBPF programs, and understanding performance/security trade-offs.

```c
struct sk_buff {
    /* Packet data pointers */
    unsigned char    *head;      // start of allocated buffer
    unsigned char    *data;      // start of current payload
    unsigned char    *tail;      // end of current payload
    unsigned char    *end;       // end of allocated buffer

    /* Layer header offsets (set during parsing) */
    __u16            transport_header;  // TCP/UDP header offset from head
    __u16            network_header;    // IP header offset
    __u16            mac_header;        // Ethernet header offset

    /* Metadata */
    struct net_device *dev;       // ingress/egress device
    struct sock      *sk;         // owning socket (if local)
    __u32            mark;        // fwmark — used by routing, iptables
    __u8             pkt_type;    // PACKET_HOST, PACKET_BROADCAST, etc.
    __u8             ip_summed;   // checksum state
    
    /* Security metadata */
    __u32            secmark;     // SELinux/secmark label
    struct           nf_conntrack_tuple_hash *nfct; // conntrack entry
};
```

**Security relevance:**
- `mark` / `fwmark` is used for policy-based routing — can be set by iptables/eBPF to route traffic through security middleboxes
- `secmark` integrates with SELinux to label packets for MAC enforcement
- `nfct` links to the conntrack state — the basis of stateful firewalling
- Corrupting sk_buff metadata (via kernel vuln) is a classic privilege escalation vector → always validate in eBPF programs

### 2.3 Packet RX Path (Ingress)

```
NIC Hardware
  ↓  DMA to ring buffer (NAPI poll)
  ↓  netif_receive_skb() / napi_gro_receive()
  ↓  GRO (Generic Receive Offload) — reassemble segments
  ↓  __netif_receive_skb_core()
  ↓  packet_type handlers (ETH_P_IP → ip_rcv)
  ↓  ip_rcv() → ip_rcv_finish()
  ↓  Netfilter NF_INET_PRE_ROUTING hook
  ↓  Routing decision (ip_route_input)
       ├── local delivery → NF_INET_LOCAL_IN → socket delivery
       └── forward → NF_INET_FORWARD → NF_INET_POST_ROUTING → TX
```

**Performance & security note:** GRO can be abused — malformed GRO segments have historically caused kernel panics. `ethtool -K eth0 gro off` disables it, at the cost of CPU overhead. In high-security environments, validate before GRO or use XDP to drop early.

### 2.4 Packet TX Path (Egress)

```
Application (send/write syscall)
  ↓  socket send buffer (sk_wmem_alloc)
  ↓  Transport layer (TCP segmentation, TCP options)
  ↓  NF_INET_LOCAL_OUT hook (iptables OUTPUT chain)
  ↓  Routing (ip_route_output)
  ↓  NF_INET_POST_ROUTING hook (iptables POSTROUTING / MASQUERADE)
  ↓  GSO (Generic Segmentation Offload) — defer segmentation to NIC
  ↓  qdisc (traffic control queue)
  ↓  NIC driver → DMA → wire
```

### 2.5 Kernel Network Sysctl — Security-Critical Parameters

These sysctls are foundational hardening. Every production host should have them set.

```bash
# /etc/sysctl.d/99-network-security.conf

# ── IP Spoofing & Source Validation ──────────────────────────────────────
net.ipv4.conf.all.rp_filter = 1          # Strict reverse-path filtering (RFC 3704)
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0 # Reject IP source routing (can forge path)
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# ── ICMP Hardening ────────────────────────────────────────────────────────
net.ipv4.icmp_echo_ignore_broadcasts = 1  # Smurf amplification defense
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.icmp_ratelimit = 1000            # ICMP rate limit (pps)
net.ipv4.icmp_ratemask = 6168             # Limit: dest-unreach, time-exceeded

# ── TCP Hardening ─────────────────────────────────────────────────────────
net.ipv4.tcp_syncookies = 1               # SYN flood defense (RFC 4987)
net.ipv4.tcp_syn_retries = 2             # Reduce SYN retransmits
net.ipv4.tcp_synack_retries = 2          # Reduce SYNACK retransmits
net.ipv4.tcp_max_syn_backlog = 4096      # Increase SYN queue
net.ipv4.tcp_fin_timeout = 15            # Reduce TIME_WAIT state duration
net.ipv4.tcp_rfc1337 = 1                 # Protect against TIME_WAIT assassination
net.ipv4.tcp_timestamps = 1              # Required for PAWS, but leaks uptime
# net.ipv4.tcp_timestamps = 0            # Disable to hide uptime (trade-off: breaks PAWS)

# ── IP Forwarding (disable on non-routers) ────────────────────────────────
net.ipv4.ip_forward = 0                  # Set to 1 only on routers/K8s nodes
net.ipv6.conf.all.forwarding = 0

# ── IPv6 Hardening ────────────────────────────────────────────────────────
net.ipv6.conf.all.accept_ra = 0          # Disable rogue Router Advertisement acceptance
net.ipv6.conf.default.accept_ra = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.accept_redirects = 0   # Disable ICMP redirect acceptance (MITM vector)
net.ipv4.conf.all.send_redirects = 0

# ── ARP Hardening ────────────────────────────────────────────────────────
net.ipv4.conf.all.arp_ignore = 1         # Reply only for IPs on the receiving interface
net.ipv4.conf.all.arp_announce = 2       # Always use best local address for ARP

# ── Log Martian Packets ───────────────────────────────────────────────────
net.ipv4.conf.all.log_martians = 1       # Log packets with impossible source addresses

# ── TCP Memory Tuning (DDoS resilience) ───────────────────────────────────
net.ipv4.tcp_mem = 786432 1048576 1572864
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 300000

# Apply immediately
sysctl -p /etc/sysctl.d/99-network-security.conf
```

**`rp_filter` deep dive:** Strict mode (=1) checks that the source IP of an incoming packet would be reachable via the same interface it arrived on (using the routing table). This defeats IP spoofing attacks where an attacker sends packets with a forged source IP from a different network. Loose mode (=2) only checks that the source IP is reachable via *any* interface — weaker but needed in asymmetric routing scenarios (e.g., BGP multi-homed environments, ECMP).

### 2.6 SO_REUSEPORT, SO_REUSEADDR — Security Implications

`SO_REUSEPORT` allows multiple sockets to bind to the same port, with the kernel load-balancing across them. This is critical for high-performance servers but introduces a **socket hijacking** risk: an unprivileged process can bind to the same port and steal connections.

Linux 4.5+ added `SO_REUSEPORT` with a filter mechanism using eBPF to restrict which sockets are eligible (EBPF_PROG_TYPE_SK_REUSEPORT). In security-sensitive environments, always pair `SO_REUSEPORT` with seccomp/LSM restrictions on socket syscalls.

```c
// Restrict SO_REUSEPORT with eBPF sk_reuseport program
// The program selects which socket receives the incoming connection
SEC("sk_reuseport")
int select_socket(struct sk_reuseport_md *ctx) {
    // Can inspect packet data, filter by source IP, etc.
    return SK_PASS;
}
```

---

## 3. Netfilter, iptables, nftables

### 3.1 Netfilter Hook Points

Netfilter is the Linux kernel framework providing hooks into the packet processing path. All firewalling, NAT, connection tracking, and packet mangling flows through these hooks.

```
                    ROUTING DECISION
                          │
Packet In   ──► PREROUTING ──► (local?) ──► INPUT ──► Socket
                          │         (no)
                          └──────► FORWARD ──► POSTROUTING ──► Packet Out
                                                    ↑
                                              LOCAL OUTPUT
                                          Socket ──► OUTPUT ──┘
```

**Hook priorities** (lower = earlier):
```
NF_IP_PRI_CONNTRACK_DEFRAG = -400  # IP defragmentation
NF_IP_PRI_RAW              = -300  # iptables raw table
NF_IP_PRI_SELINUX_FIRST    = -225  # SELinux (first pass)
NF_IP_PRI_CONNTRACK        = -200  # Connection tracking
NF_IP_PRI_MANGLE           = -150  # iptables mangle table
NF_IP_PRI_NAT_DST          = -100  # DNAT
NF_IP_PRI_FILTER           =    0  # iptables filter table
NF_IP_PRI_SECURITY         =   50  # Security (SELinux second pass)
NF_IP_PRI_NAT_SRC          =  100  # SNAT/MASQUERADE
NF_IP_PRI_SELINUX_LAST     =  225  # SELinux (last pass)
NF_IP_PRI_CONNTRACK_HELPER = INT_MAX # Conntrack helpers (ALGs)
```

### 3.2 Connection Tracking (conntrack)

Conntrack is the kernel's stateful packet inspection engine. It tracks the state of network connections and is the foundation of stateful firewalling.

**States:**
- `NEW` — first packet of a new connection (no reply seen)
- `ESTABLISHED` — reply seen; bidirectional flow established
- `RELATED` — related connection (e.g., FTP data channel, ICMP error)
- `INVALID` — doesn't match any known connection; should be DROPped
- `UNTRACKED` — explicitly excluded from tracking (raw table `NOTRACK`)

```bash
# View conntrack table
conntrack -L
conntrack -L --proto tcp --state ESTABLISHED

# Conntrack statistics (per-CPU)
conntrack -S

# Conntrack table size — CRITICAL: exhaustion = DoS
cat /proc/sys/net/netfilter/nf_conntrack_max        # default often 65536
cat /proc/sys/net/netfilter/nf_conntrack_count      # current entries

# Tune for high-traffic environments
sysctl -w net.netfilter.nf_conntrack_max=1048576
sysctl -w net.netfilter.nf_conntrack_buckets=262144  # hash table size

# Timeouts — reduce for DDoS resilience
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=300
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=15
sysctl -w net.netfilter.nf_conntrack_udp_timeout=15
```

**Conntrack exhaustion attack:** An attacker floods with half-open TCP connections or UDP datagrams, filling the conntrack table. Legitimate connections then fail with "nf_conntrack: table full, dropping packet." Mitigations:
1. Increase `nf_conntrack_max` proportionally to RAM
2. Reduce timeouts aggressively
3. Rate-limit NEW connections per source IP with `iptables -m hashlimit`
4. Use SYN cookies (bypasses conntrack for SYN packets)
5. Use XDP to drop flood traffic before conntrack is reached

### 3.3 iptables — Tables, Chains, Rules

**Tables and their purposes:**
```
raw      → Earliest hook; use NOTRACK to exempt from conntrack
mangle   → Modify packet headers (TTL, TOS/DSCP, mark)
nat      → Address translation (DNAT, SNAT, MASQUERADE, REDIRECT)
filter   → Accept/Drop/Reject decisions (DEFAULT TABLE)
security → SELinux/secmark integration
```

**Production-grade iptables ruleset structure:**

```bash
#!/bin/bash
# /etc/iptables/rules.sh — Hardened host firewall

IPT="iptables"

# ── Flush & set defaults ──────────────────────────────────────────────────
$IPT -F; $IPT -X; $IPT -Z
$IPT -t nat -F; $IPT -t nat -X
$IPT -t mangle -F; $IPT -t mangle -X
$IPT -t raw -F; $IPT -t raw -X

# DEFAULT POLICY: DROP everything, allow explicitly
$IPT -P INPUT DROP
$IPT -P FORWARD DROP
$IPT -P OUTPUT DROP   # Egress filtering — critical for compromised host detection

# ── Loopback ──────────────────────────────────────────────────────────────
$IPT -A INPUT  -i lo -j ACCEPT
$IPT -A OUTPUT -o lo -j ACCEPT

# ── Drop INVALID state — conntrack invalid packets ────────────────────────
$IPT -A INPUT   -m conntrack --ctstate INVALID -j DROP
$IPT -A FORWARD -m conntrack --ctstate INVALID -j DROP
$IPT -A OUTPUT  -m conntrack --ctstate INVALID -j DROP

# ── Allow ESTABLISHED/RELATED (stateful) ─────────────────────────────────
$IPT -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
$IPT -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ── Anti-spoofing: Drop RFC1918/bogons from public interfaces ─────────────
BOGONS="10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16
        192.0.2.0/24 198.51.100.0/24 203.0.113.0/24 224.0.0.0/4
        240.0.0.0/4 0.0.0.0/8 127.0.0.0/8"
for net in $BOGONS; do
    $IPT -A INPUT -i eth0 -s $net -j DROP   # eth0 = public interface
done

# ── ICMP: Allow only necessary types ─────────────────────────────────────
$IPT -A INPUT  -p icmp --icmp-type echo-request  -m limit --limit 5/s --limit-burst 10 -j ACCEPT
$IPT -A INPUT  -p icmp --icmp-type echo-reply    -j ACCEPT
$IPT -A INPUT  -p icmp --icmp-type destination-unreachable -j ACCEPT
$IPT -A INPUT  -p icmp --icmp-type time-exceeded -j ACCEPT
$IPT -A OUTPUT -p icmp -j ACCEPT

# ── SYN Flood Protection ──────────────────────────────────────────────────
$IPT -A INPUT -p tcp --syn -m limit --limit 50/s --limit-burst 100 -j ACCEPT
$IPT -A INPUT -p tcp --syn -j DROP   # Drop excess SYN

# ── Port Scanning Protection ──────────────────────────────────────────────
$IPT -N PORT_SCAN
$IPT -A PORT_SCAN -p tcp --tcp-flags SYN,ACK,FIN,RST RST \
     -m limit --limit 1/s -j RETURN
$IPT -A PORT_SCAN -j DROP
$IPT -A INPUT -p tcp -m conntrack --ctstate NEW -j PORT_SCAN

# ── Specific Service Rules ────────────────────────────────────────────────
MGMT_NET="10.0.1.0/24"   # Management network CIDR
$IPT -A INPUT -p tcp --dport 22 -s $MGMT_NET -m conntrack --ctstate NEW -j ACCEPT

# ── Log & Drop (at end of INPUT chain) ───────────────────────────────────
$IPT -A INPUT -m limit --limit 5/min -j LOG \
    --log-prefix "[IPT-DROP-IN] " --log-level 7
$IPT -A INPUT -j DROP

# ── Egress filtering ──────────────────────────────────────────────────────
$IPT -A OUTPUT -p tcp  -m conntrack --ctstate NEW -j ACCEPT
$IPT -A OUTPUT -p udp  --dport 53  -j ACCEPT   # DNS
$IPT -A OUTPUT -p udp  --dport 123 -j ACCEPT   # NTP
$IPT -A OUTPUT -m limit --limit 5/min -j LOG \
    --log-prefix "[IPT-DROP-OUT] " --log-level 7
$IPT -A OUTPUT -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

**Why egress filtering matters:** A compromised host will attempt outbound C2 (command and control) connections. Strict OUTPUT chain rules detect and prevent lateral movement, data exfiltration, and botnet participation. This is often skipped in practice — it shouldn't be.

### 3.4 nftables — Modern Replacement

nftables replaces iptables/ip6tables/ebtables/arptables with a single framework. Linux 3.13+, default in Debian 10+, RHEL 8+, Ubuntu 20.04+.

**Advantages over iptables:**
- Atomic rule sets (entire ruleset applied at once — no partial updates)
- Better performance (JIT compilation)
- Native IPv4+IPv6 in one ruleset
- Cleaner syntax, set data structures, maps
- Lower overhead than iptables for large rulesets

```nft
#!/usr/sbin/nft -f
# /etc/nftables.conf — Production hardened ruleset

flush ruleset

# Define sets for dynamic IP management
define MGMT_NETS = { 10.0.1.0/24, 10.0.2.0/24 }

table inet filter {
    # Bogon set — can be updated atomically
    set bogons {
        type ipv4_addr
        flags interval
        elements = {
            0.0.0.0/8, 10.0.0.0/8, 127.0.0.0/8,
            169.254.0.0/16, 172.16.0.0/12, 192.0.2.0/24,
            192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24,
            224.0.0.0/4, 240.0.0.0/4
        }
    }

    # Dynamic blocklist (populated by IDS/fail2ban/eBPF)
    set blocklist {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
        size 65536
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Blocklist — checked first
        ip saddr @blocklist drop

        # Loopback
        iif lo accept

        # Drop invalid conntrack state
        ct state invalid drop

        # Allow established/related
        ct state { established, related } accept

        # Anti-spoofing on public interface
        iif "eth0" ip saddr @bogons drop

        # ICMP — rate limited
        ip protocol icmp icmp type {
            echo-reply, destination-unreachable,
            time-exceeded, parameter-problem
        } accept
        ip protocol icmp icmp type echo-request \
            limit rate 5/second accept
        ip protocol icmp drop

        # ICMPv6 — required for IPv6 operation
        ip6 nexthdr icmpv6 icmpv6 type {
            nd-neighbor-solicitation, nd-neighbor-advertisement,
            nd-router-solicitation, nd-router-advertisement,
            mld-listener-query, echo-request, echo-reply,
            destination-unreachable, time-exceeded
        } accept

        # SSH from management networks only
        tcp dport 22 ip saddr $MGMT_NETS ct state new accept

        # SYN flood protection using connlimit
        tcp flags syn tcp option maxseg size 1-500 drop   # MSS-based syn scan detect
        tcp dport { 80, 443 } ct state new \
            limit rate 1000/second accept

        # Log and drop the rest
        limit rate 10/minute log prefix "[NFT-DROP-IN] " level debug
        drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state { established, related } accept
        ct state invalid drop
    }

    chain output {
        type filter hook output priority filter; policy drop;

        oif lo accept
        ct state { established, related } accept

        # Allow specific outbound
        tcp dport { 80, 443 } ct state new accept
        udp dport 53  accept
        udp dport 123 accept

        limit rate 5/minute log prefix "[NFT-DROP-OUT] " level debug
        drop
    }
}

table inet mangle {
    chain prerouting {
        type filter hook prerouting priority mangle; policy accept;
        # Drop TCP packets with bogus flag combinations
        tcp flags & (fin|syn) == (fin|syn) drop       # FIN+SYN invalid
        tcp flags & (syn|rst) == (syn|rst) drop       # SYN+RST invalid
        tcp flags & (fin|rst) == (fin|rst) drop       # FIN+RST invalid
        tcp flags & (fin|ack) == fin drop             # FIN without ACK
        tcp flags & (ack|urg) == urg drop             # URG without ACK
        tcp flags == 0x0 drop                          # NULL scan
        tcp flags == 0x3f drop                         # XMAS scan (all flags)
    }
}
```

**Atomic updates with nftables:**
```bash
# Test ruleset before applying
nft -c -f /etc/nftables.conf    # dry-run check

# Apply atomically (all or nothing — no partial state)
nft -f /etc/nftables.conf

# Add to blocklist dynamically (from IDS, fail2ban, etc.)
nft add element inet filter blocklist { 203.0.113.5 }

# Flush blocklist
nft flush set inet filter blocklist
```

---

## 4. eBPF & XDP — Kernel-Bypass Security

### 4.1 eBPF Architecture

eBPF (extended Berkeley Packet Filter) is a sandboxed virtual machine in the Linux kernel that allows safe execution of user-defined programs at various kernel hook points. It is the most important technology in modern Linux networking security.

```
User Space
  ├── BPF program source (C, Rust via aya)
  ├── Compile → BPF bytecode (LLVM/clang -target bpf)
  ├── bpf() syscall → load & verify
  └── Attach to hook point

Kernel Verifier
  ├── DAG analysis (no loops unless bounded)
  ├── Register range tracking (bounds checking)
  ├── Stack depth limiting (512 bytes max)
  ├── Pointer validation (no arbitrary memory access)
  └── JIT compilation → native code

Hook Points
  ├── XDP        — Earliest ingress, before sk_buff allocation
  ├── TC (clsact) — Ingress/egress, after sk_buff, bi-directional
  ├── kprobe/tracepoint — Kernel function tracing
  ├── socket filter — Per-socket packet filtering (legacy: BPF)
  ├── cgroup      — Per-cgroup socket/device access control
  ├── sk_msg / sk_skb — Sockmap, TCP socket redirection
  └── LSM         — Linux Security Module hooks (5.7+)
```

### 4.2 XDP (eXpress Data Path)

XDP runs eBPF programs in the NIC driver context (or NAPI poll loop), before the kernel allocates an `sk_buff`. This makes it the earliest possible firewall/filter point — ideal for DDoS mitigation.

**XDP program actions:**
```
XDP_DROP     → Drop packet immediately (fastest possible drop)
XDP_PASS     → Pass to normal kernel networking stack
XDP_TX       → Reflect packet back out the same NIC
XDP_REDIRECT → Redirect to another NIC, CPU, or AF_XDP socket
XDP_ABORTED  → Drop + trace event (debugging)
```

**XDP modes:**
```
Native XDP   → Runs in NIC driver's NAPI poll loop (best perf)
              Supported: mlx5, i40e, ixgbevf, virtio-net, tun
Generic XDP  → Runs after sk_buff allocation (software fallback)
              Lower performance but works on all NICs
Offloaded XDP → Runs on SmartNIC hardware (e.g., Netronome)
              Lowest CPU overhead, highest throughput
```

**Example: XDP-based IP blocklist (Rust/aya):**
```rust
// src/xdp_firewall.rs — using aya (Rust eBPF framework)
use aya_bpf::{bindings::xdp_action, macros::xdp, maps::HashMap, programs::XdpContext};

#[map]
static BLOCKLIST: HashMap<u32, u8> = HashMap::with_max_entries(65536, 0);

#[xdp]
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret) => ret,
        Err(_) => xdp_action::XDP_ABORTED,
    }
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    // Parse Ethernet header
    let eth = ptr_at::<ethhdr>(&ctx, 0)?;
    if unsafe { (*eth).h_proto } != u16::from_be(ETH_P_IP as u16) {
        return Ok(xdp_action::XDP_PASS);
    }

    // Parse IP header
    let ip = ptr_at::<iphdr>(&ctx, ETH_HDR_LEN)?;
    let src = u32::from_be(unsafe { (*ip).saddr });

    // Check blocklist — O(1) hash map lookup
    if BLOCKLIST.get(&src).is_some() {
        return Ok(xdp_action::XDP_DROP);  // Drop before sk_buff, before conntrack
    }

    Ok(xdp_action::XDP_PASS)
}
```

**Performance comparison for packet drop (10GbE, single core):**
```
iptables DROP       :  ~2 Mpps  (sk_buff allocated, conntrack touched)
TC BPF DROP         :  ~5 Mpps  (sk_buff allocated, but conntrack bypassed)
XDP Generic DROP    :  ~8 Mpps  (sk_buff allocated in softirq)
XDP Native DROP     : ~20 Mpps  (before sk_buff, in NAPI poll)
XDP Offload DROP    : ~40+ Mpps (on NIC, zero host CPU)
```

### 4.3 TC BPF (Traffic Control eBPF)

TC BPF runs at the `tc` (traffic control) layer — after `sk_buff` is allocated but still in the kernel's fast path. It is more flexible than XDP (can modify packets, access full sk_buff metadata, handle egress) and is what Cilium uses for its dataplane.

```bash
# Attach BPF program to interface ingress using tc
ip link add dev lo
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf da obj firewall.o sec tc/ingress
tc filter add dev eth0 egress  bpf da obj firewall.o sec tc/egress

# Show attached programs
tc filter show dev eth0 ingress

# BPF return codes for TC programs
# TC_ACT_OK (0)       → pass to next handler
# TC_ACT_SHOT (2)     → drop packet
# TC_ACT_REDIRECT (7) → redirect (used by Cilium for cross-namespace routing)
```

### 4.4 eBPF LSM (BPF-LSM)

Linux 5.7+ allows eBPF programs to be attached to LSM (Linux Security Module) hooks, enabling programmable MAC (Mandatory Access Control) policies without writing kernel modules.

```c
// BPF-LSM: restrict socket creation by cgroup
SEC("lsm/socket_create")
int BPF_PROG(restrict_socket_create, int family, int type,
             int protocol, int kern) {
    // Get cgroup id of current task
    __u64 cgid = bpf_get_current_cgroup_id();
    
    // Look up policy for this cgroup
    struct policy *p = bpf_map_lookup_elem(&cgroup_policy, &cgid);
    if (!p) return 0; // default allow
    
    // Enforce: if policy says no raw sockets, block them
    if (type == SOCK_RAW && !p->allow_raw) {
        return -EPERM;
    }
    return 0;
}
```

### 4.5 eBPF Security Considerations

eBPF itself has a security boundary — the **verifier**. Historical verifier bugs have led to kernel privilege escalation (CVE-2021-3490, CVE-2021-4204, CVE-2022-23222). Mitigations:
- Restrict `bpf()` syscall: `kernel.unprivileged_bpf_disabled = 1`
- Use seccomp to deny `bpf()` in untrusted containers
- Audit eBPF programs loaded on the host (bpftool + Falco)

```bash
# Disable unprivileged eBPF
sysctl -w kernel.unprivileged_bpf_disabled=1

# List all loaded eBPF programs on host
bpftool prog list

# Show program details including BTF type info
bpftool prog dump xlated id <id> linum

# Inspect maps
bpftool map list
bpftool map dump id <id>
```

---

## 5. Network Namespaces, cgroups, veth, bridge

### 5.1 Network Namespaces

Network namespaces provide kernel-level isolation of the network stack. Each namespace has its own:
- Network interfaces
- Routing tables
- iptables/nftables rules
- Conntrack tables
- Sockets
- `/proc/net/*` view

This is the foundation of container networking in Docker, Kubernetes (each Pod), and VM networking in KVM.

```bash
# Create isolated network namespace
ip netns add red
ip netns add blue

# Verify isolation
ip netns exec red ip addr show     # Only sees loopback initially
ip netns exec blue ip addr show

# Create veth pair — virtual Ethernet cable
ip link add veth-red   type veth peer name veth-red-br
ip link add veth-blue  type veth peer name veth-blue-br

# Move one end of each pair into its namespace
ip link set veth-red   netns red
ip link set veth-blue  netns blue

# Bring up interfaces
ip netns exec red  ip link set veth-red  up
ip netns exec blue ip link set veth-blue up
ip netns exec red  ip addr add 192.168.1.1/24 dev veth-red
ip netns exec blue ip addr add 192.168.1.2/24 dev veth-blue

# Create bridge in root namespace to connect them
ip link add name br0 type bridge
ip link set br0 up
ip link set veth-red-br  master br0 up
ip link set veth-blue-br master br0 up

# Now red and blue can communicate via bridge
ip netns exec red ping -c3 192.168.1.2
```

**Security isolation properties:**
- Processes in a namespace cannot see or interfere with sockets/routes in other namespaces
- iptables rules in one namespace don't affect another (except for the root namespace's bridge netfilter — controlled by `br_netfilter` module and `net.bridge.bridge-nf-call-iptables`)
- A process needs `CAP_NET_ADMIN` to create/modify interfaces, or it must be in a user namespace with appropriate mapping

**`br_netfilter` security note:** When the `br_netfilter` kernel module is loaded (required for Kubernetes), bridged traffic passes through the host's iptables/netfilter hooks. This is essential for kube-proxy (iptables mode) but means bridge traffic is NOT isolated from host firewall rules. This must be understood when designing K8s NetworkPolicy enforcement.

### 5.2 veth Pairs — Implementation Detail

veth (virtual Ethernet) pairs are connected at the kernel level — packets written to one end are immediately readable from the other, with no actual network I/O. The kernel skips the full TX/RX path, making veth extremely fast but subject to head-of-line blocking if one end's rx queue fills.

```
Container/Pod namespace                  Root/Node namespace
┌──────────────────────┐                ┌──────────────────────┐
│ eth0 ←──────────────────── veth pair ───────────────────► vethXXXXXX │
│ 10.0.0.2/24          │                │ → bridge cbr0        │
└──────────────────────┘                │ → iptables/eBPF      │
                                        └──────────────────────┘
```

### 5.3 Linux Bridge vs. Open vSwitch

**Linux bridge (`bridge`):** Simple L2 forwarding, MAC learning, STP. Used by Docker's `docker0`, basic K8s CNI plugins.

**Open vSwitch (OVS):** Full-featured virtual switch with OpenFlow support, VXLAN/Geneve tunneling, QoS, and fine-grained flow control. Used in OpenStack, some K8s deployments, and data center SDN.

```bash
# OVS basic setup
ovs-vsctl add-br ovs-br0
ovs-vsctl add-port ovs-br0 eth0    # Uplink to physical network
ovs-vsctl add-port ovs-br0 vnet0   # VM's tap interface

# Add VXLAN tunnel for overlay networking
ovs-vsctl add-port ovs-br0 vxlan0 -- \
    set interface vxlan0 type=vxlan \
    options:remote_ip=10.0.0.2 \
    options:key=100

# Flow table inspection (OpenFlow)
ovs-ofctl dump-flows ovs-br0
ovs-ofctl dump-tables ovs-br0

# Security: restrict flow table modifications
ovs-vsctl set bridge ovs-br0 fail-mode=secure  # Don't fall back to learning switch on disconnect
```

### 5.4 cgroups v2 and Network Control

cgroups v2 integrates with the network stack for:
- Per-cgroup network priority (net_prio)
- Per-cgroup eBPF programs (BPF_PROG_TYPE_CGROUP_SKB, BPF_PROG_TYPE_CGROUP_SOCK)
- Socket-level network policy enforcement

```bash
# Attach eBPF ingress filter to cgroup
bpftool cgroup attach /sys/fs/cgroup/system.slice ingress \
    pinned /sys/fs/bpf/cgroup_ingress

# Verify
bpftool cgroup list /sys/fs/cgroup/system.slice

# Per-cgroup bandwidth limiting using tc + cgroup matching
tc qdisc add dev eth0 root handle 1: htb default 30
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit
tc filter add dev eth0 parent 1: handle 1 cgroup
```

---

## 6. Protocol Deep Dives

### 6.1 Ethernet & L2 (IEEE 802.3, 802.1Q)

**Ethernet frame format:**
```
 6B    6B    2B         46-1500B    4B
┌──────┬──────┬──────────┬──────────┬─────┐
│ DST  │ SRC  │EtherType │ Payload  │ FCS │
│ MAC  │ MAC  │(or VLAN) │          │CRC32│
└──────┴──────┴──────────┴──────────┴─────┘

With 802.1Q VLAN tag (4B inserted):
 6B    6B    4B      2B        46-1500B   4B
┌──────┬──────┬──────┬──────────┬─────────┬─────┐
│ DST  │ SRC  │ 8100 │EtherType │ Payload │ FCS │
│      │      │+VLAN │          │         │     │
└──────┴──────┴──────┴──────────┴─────────┴─────┘
         TPID=0x8100  PCP(3b) DEI(1b) VID(12b)
```

**802.1Q VLAN security:**
- VID=0: priority tagging only (no VLAN isolation)
- VID=1: default VLAN on many switches — never use for production traffic
- VID=4095: reserved
- **VLAN hopping attacks:** If a switch port is configured as a trunk (multiple VLANs), an attacker on an access port may send double-tagged 802.1Q frames to reach other VLANs. Mitigation: set native VLAN to an unused VLAN, explicitly configure trunks, and use MAC-based 802.1X authentication.

**MAC flooding attack:** An attacker sends millions of frames with random source MACs, filling the switch's CAM (Content Addressable Memory) table. The switch then falls back to broadcasting all frames — effectively turning a switch into a hub, enabling passive sniffing. Mitigation: port security (limit MACs per port), dynamic ARP inspection, 802.1X.

```bash
# Linux: view ARP/neighbor cache (equivalent to CAM table on host)
ip neigh show
ip -s neigh show

# Detect ARP flood
watch -n1 "ip neigh show | wc -l"
```

### 6.2 ARP & NDP — The Root of Many L2 Attacks

**ARP (Address Resolution Protocol) — IPv4 only, RFC 826:**
```
ARP Request  (broadcast): "Who has 192.168.1.1? Tell 192.168.1.100"
ARP Reply    (unicast):   "192.168.1.1 is at aa:bb:cc:dd:ee:ff"

Frame format (28 bytes):
HType(2) PType(2) HLen(1) PLen(1) Op(2) SHA(6) SPA(4) THA(6) TPA(4)
```

**ARP has NO authentication.** Any host can send a Gratuitous ARP claiming ownership of any IP, poisoning the ARP cache of all hosts on the segment. This enables MITM attacks.

**ARP poisoning attack:**
```
Attacker sends:
  Gratuitous ARP: 192.168.1.1 is at attacker:mac → poisons all hosts
  Gratuitous ARP: 192.168.1.100 is at attacker:mac → poisons router

Result: All traffic between 192.168.1.1 and .100 flows through attacker
        (only visible at L2 — SSL/TLS still protects L7 content)
```

**Mitigations:**
1. **Dynamic ARP Inspection (DAI)** on managed switches: validates ARP against DHCP snooping binding table
2. **Static ARP entries** for critical hosts (router/gateway):
   ```bash
   ip neigh add 192.168.1.1 lladdr aa:bb:cc:dd:ee:ff dev eth0 nud permanent
   ```
3. **arpwatch** or **XDP/eBPF-based ARP monitor**: alert on unexpected ARP replies
4. **Private VLANs (PVLANs)**: isolate hosts on the same VLAN from directly communicating at L2
5. **IPv6 NDP with SEND (Secure Neighbor Discovery, RFC 3971)**: cryptographic authentication of NDP messages

**NDP (Neighbor Discovery Protocol) — IPv6, RFC 4861:**
Replaces ARP for IPv6, carried over ICMPv6. Uses:
- Neighbor Solicitation (NS, type 135) — like ARP request
- Neighbor Advertisement (NA, type 136) — like ARP reply
- Router Solicitation (RS, type 133)
- Router Advertisement (RA, type 134)
- Redirect (type 137)

**NDP attacks:**
- **Neighbor spoofing**: same as ARP poisoning but at IPv6 level
- **Rogue RA**: attacker sends Router Advertisement claiming to be the default router, potentially with shorter prefix lifetime to cause route thrashing, or claiming smaller MTU to cause fragmentation
- **RA Guard (RFC 6105)**: switch-level enforcement that drops RA messages from non-router ports

```bash
# Disable rogue RA acceptance (host hardening — already in sysctl section)
sysctl -w net.ipv6.conf.all.accept_ra=0

# Monitor for rogue RAs
tcpdump -i eth0 'icmp6 and (ip6[40] == 133 or ip6[40] == 134)'

# NDPmon — NDP monitoring tool
ndpmon -i eth0
```

### 6.3 IP — Internet Protocol (v4 & v6)

**IPv4 Header (20 bytes minimum):**
```
 0               1               2               3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─┬─────┬────────┬───────────────────────────────────────────────┤
│V│ IHL │  DSCP │ECN│           Total Length                     │
├─┴─────┴────────┴───┴───────────────────────────────────────────┤
│          Identification       │Flags│   Fragment Offset         │
├───────────────────────────────┴─────┴───────────────────────────┤
│    TTL        │   Protocol    │         Header Checksum          │
├───────────────┴───────────────┴──────────────────────────────────┤
│                       Source Address                             │
├──────────────────────────────────────────────────────────────────┤
│                    Destination Address                           │
└──────────────────────────────────────────────────────────────────┘
```

**Key security fields:**
- **TTL (Time to Live):** Decremented by each router. TTL=0 → drop + ICMP Time Exceeded. Used for traceroute. Can fingerprint OS (Linux default TTL=64, Windows=128, Cisco=255). Traceroute probes can be used for network topology discovery — block ICMP Time Exceeded at border routers in high-security environments.
- **Protocol:** Next-layer protocol (6=TCP, 17=UDP, 1=ICMP, 89=OSPF, 50=ESP, 51=AH). Always validate; routers and firewalls that don't handle unexpected protocol numbers may pass them to end hosts.
- **Flags/Fragment Offset:** IP fragmentation allows packets to be split across multiple fragments. Reassembly happens at the destination. This creates multiple attack vectors:
  - **Tiny fragment attack:** Force TCP header split across fragments so firewall can't inspect ports
  - **Fragment overlap:** Different fragments with overlapping offsets — OS reassembly behavior is ambiguous (Teardrop vulnerability, CVE-1999-0214 style)
  - **ICMP fragmentation needed + PMTUD blackhole:** Attacker drops ICMP type 3 code 4, preventing PMTUD, causing connection stalls

```bash
# Drop fragmented packets (unless legitimate)
iptables -A INPUT -f -j DROP    # Drop all fragments
# Or, better: let conntrack handle defrag
# net.ipv4.conf.all.ip_default_ttl affects outbound TTL
sysctl net.ipv4.ip_default_ttl
```

**IPv6 Header (40 bytes fixed):**
- No checksum (removed — checksums at transport layer)
- No fragmentation by routers (only by source host) — eliminates router fragmentation overhead
- Extension headers chain: Hop-by-Hop → Routing → Fragment → Destination Options → Upper Layer
- Extension header attacks: crafted extension header chains can confuse parsers, cause DoS on devices doing deep inspection (e.g., atomic fragment attack, RFC 8021)

**IPv6 Security considerations:**
```bash
# Firewall IPv6 properly — many deployments leave IPv6 open
ip6tables -P INPUT   DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT  DROP
ip6tables -A INPUT   -i lo -j ACCEPT
ip6tables -A INPUT   -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Required ICMPv6
ip6tables -A INPUT -p icmpv6 --icmpv6-type 133 -j ACCEPT  # RS
ip6tables -A INPUT -p icmpv6 --icmpv6-type 134 -j ACCEPT  # RA (if client)
ip6tables -A INPUT -p icmpv6 --icmpv6-type 135 -j ACCEPT  # NS
ip6tables -A INPUT -p icmpv6 --icmpv6-type 136 -j ACCEPT  # NA

# Or with nftables (shown earlier)
```

### 6.4 ICMP — Internet Control Message Protocol

ICMP operates at L3 (protocol number 1 for ICMPv4, next-header 58 for ICMPv6). It carries network control messages — errors, reachability, path management. Never filter ALL ICMP — this breaks PMTUD and causes hard-to-debug connectivity issues.

**ICMP types to allow:**
```
Type 0  — Echo Reply           (ping response)
Type 3  — Destination Unreach  (PMTUD critical: code 4 = frag needed)
Type 8  — Echo Request         (ping — rate limit)
Type 11 — Time Exceeded        (traceroute)
Type 12 — Parameter Problem    (malformed packet)
```

**ICMP-based attacks:**
- **Smurf amplification:** Send ICMP echo to broadcast address with spoofed source → all hosts reply to victim. Mitigated by `icmp_echo_ignore_broadcasts=1`.
- **Ping of Death:** Oversized ICMP packet causing buffer overflow on old stacks. Fully patched in modern kernels.
- **ICMP redirect:** Router sends type 5 to host, telling it to use a better next-hop. Can be abused for MITM. Always disable: `accept_redirects=0`.
- **ICMP tunneling:** Encapsulate data in ICMP echo payload. Used for C2/exfiltration. Detect with DPI or rate-limit ICMP payload size.

```bash
# Detect ICMP tunneling (large payload = suspicious)
tcpdump -i eth0 'icmp[icmptype]==icmp-echo and (ip[2:2] > 100)'

# Block ICMP with large payloads
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m length --length 100:65535 -j DROP
```

### 6.5 TCP — Transmission Control Protocol

**TCP Header (20 bytes minimum):**
```
 0               1               2               3
┌───────────────────────────────────────────────────────────────┐
│          Source Port          │       Destination Port         │
├───────────────────────────────────────────────────────────────┤
│                        Sequence Number                         │
├───────────────────────────────────────────────────────────────┤
│                     Acknowledgment Number                      │
├─────────┬─────────┬───────────────────────────────────────────┤
│Data Off.│ Reserved│ CWR│ECE│URG│ACK│PSH│RST│SYN│FIN│ Window  │
├─────────┴─────────┴─────────────────────────────────┬─────────┤
│                    Checksum              │ Urgent Ptr│
└───────────────────────────────────────────────────────────────┘
```

**Three-way handshake and SYN flood:**
```
Client                    Server
  │─────── SYN ──────────►│  Server allocates SYN queue entry
  │◄────── SYN+ACK ────────│  If queue fills → new SYN dropped
  │─────── ACK ──────────►│  Connection ESTABLISHED

SYN Flood: Attacker sends thousands of SYN with spoofed source IPs.
           Server's SYN backlog fills. Legitimate connections dropped.
           
TCP SYN Cookies (net.ipv4.tcp_syncookies=1):
  - Server encodes connection state in SYN+ACK's sequence number
  - No SYN queue entry allocated until ACK received and cookie verified
  - Tradeoff: TCP options (window scaling, SACK) may be lost
```

**TCP state machine attacks:**
- **RST injection:** Attacker in a MITM position sends RST with correct sequence number, tearing down connections. Mitigation: TCP-AO (RFC 5925), TLS.
- **Session hijacking:** Predict sequence numbers, inject data. Randomized ISN (Initial Sequence Number) since Linux 3.x makes this impractical but not impossible across connections.
- **TIME_WAIT assassination:** RST packet during TIME_WAIT state. `net.ipv4.tcp_rfc1337=1` mitigates.
- **TCP ACK storm:** Loop between two hosts due to injected bad sequence. Historical.

**TCP security options:**
```bash
# TCP-AO (Authentication Option, RFC 5925) — replaces TCP MD5
# Authenticates TCP segments using HMAC (SHA1/SHA256)
# Used for BGP peering security (see BGP section)

# View TCP socket statistics
ss -s           # Summary
ss -tnp         # TCP sockets with process info
ss -tnp state established  # Only established

# Detailed socket info
ss -tnpi        # Including TCP internal info (rtt, cwnd, retransmits)

# TCP connection states — useful for detecting attacks
ss -ant | awk '{print $1}' | sort | uniq -c | sort -rn
```

**TCP BBR and security:** BBR (Bottleneck Bandwidth and RTT) congestion control can be exploited — an attacker who can forge ACKs or observe timing can influence TCP's bandwidth estimates. In low-trust environments, prefer TLS + mTLS to protect the transport.

```bash
# Enable BBR (better performance, generally recommended)
sysctl -w net.core.default_qdisc=fq
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

### 6.6 UDP — User Datagram Protocol

UDP is stateless — no connection, no delivery guarantee, no ordering. This makes it fast but also makes it easy to spoof and amplify.

**UDP amplification attacks:** Attacker sends small UDP request with spoofed source IP (victim), gets large response sent to victim. Amplification factor = response_size / request_size.

```
Protocol      Amplification Factor
───────────────────────────────────
DNS           28x–54x
NTP           556x
SSDP          30x
Memcached     50,000x
CharGen       358x
RPC           (variable, high)
```

**Mitigations:**
- BCP 38 (Network Ingress Filtering, RFC 2827): ISPs should filter traffic with spoofed source IPs
- Disable unused UDP services (chargen, daytime, echo)
- Rate-limit UDP responses per destination IP
- DNS: Response Rate Limiting (RRL)
- NTP: Use `restrict` config, disable monlist

```bash
# Detect UDP amplification attempts (victim side)
tcpdump -i eth0 'udp and (greater 500)' -c 1000 | \
    awk '{print $3}' | sort | uniq -c | sort -rn | head -20

# Block UDP flood at XDP level (much more efficient)
# See XDP section above
```

### 6.7 DNS — Domain Name System

DNS is UDP/TCP port 53. It is critical infrastructure and a major attack vector. Every enterprise needs to deeply understand DNS security.

**DNS record types (security-relevant):**
```
A        → IPv4 address
AAAA     → IPv6 address
CNAME    → Canonical name alias
MX       → Mail exchanger
NS       → Name server
PTR      → Reverse lookup
SOA      → Start of Authority
TXT      → Text (SPF, DKIM, verification tokens)
SRV      → Service locator
CAA      → Certification Authority Authorization (restrict cert issuance)
TLSA     → DANE — bind TLS cert to DNS (DNSSEC-protected)
DNSKEY   → DNSSEC public key
DS       → Delegation Signer (chain of trust)
RRSIG    → DNSSEC signature
```

**DNS security attacks:**
1. **DNS Cache Poisoning (Kaminsky attack, 2008):** Attacker races legitimate responses by sending many forged responses with guessed Transaction IDs. Mitigation: source port randomization (16-bit entropy), DNSSEC.

2. **DNS Spoofing/MITM:** On-path attacker intercepts and forges DNS responses. Mitigation: DoT (DNS-over-TLS), DoH (DNS-over-HTTPS), DNSSEC.

3. **DNS Amplification/Reflection:** See UDP section.

4. **NXDOMAIN attacks:** Flood resolver with queries for non-existent domains, filling negative cache.

5. **DNS Tunneling:** Encode data in DNS queries/responses for C2 or exfiltration. High query volume for long hostnames is suspicious.

```bash
# Detect DNS tunneling indicators
tcpdump -i eth0 -w dns.pcap 'port 53'
# Then analyze: long hostnames, high entropy labels, many unique queries

# Use dnsmasq with rate limiting
# /etc/dnsmasq.conf
# dns-rrl-rate=100          # Response rate limiting
# dns-rrl-slip=2            # Slip 1 in every 2 (send truncated response)

# Check DNSSEC validation
dig +dnssec google.com A          # Should show RRSIG records
dig +dnssec example.com DNSKEY    # Check trust anchor
systemd-resolve --status | grep DNSSEC

# DNS-over-TLS with stubby (local resolver)
# /etc/stubby/stubby.yml
# resolution_type: GETDNS_RESOLUTION_STUB
# dns_transport_list: [GETDNS_TRANSPORT_TLS]
# upstream_recursive_servers:
#   - address_data: 1.1.1.1
#     tls_port: 853
#     tls_auth_name: "cloudflare-dns.com"

# CAA record prevents issuance of certs by non-authorized CAs
dig example.com CAA
```

**Split-horizon DNS / internal DNS security:**
- Maintain separate authoritative zones for internal and external names
- Internal DNS servers should not be internet-accessible
- Use TSIG (Transaction Signatures) for zone transfer authentication
- Monitor for zone transfer attempts: `dig @ns.example.com example.com AXFR`

### 6.8 TLS 1.3 — Transport Layer Security

TLS 1.3 (RFC 8446) is the current standard for transport encryption. Understanding its internals is essential for a security engineer.

**TLS 1.3 Handshake (1-RTT):**
```
Client                                   Server
  │                                          │
  │── ClientHello ───────────────────────►  │
  │   (random, supported ciphers,           │
  │    key_share: ephemeral DH pubkey)      │
  │                                          │
  │◄─── ServerHello ────────────────────────│
  │   (random, chosen cipher,              │
  │    key_share: server DH pubkey)        │
  │   [Key derivation happens here]        │
  │◄─── {EncryptedExtensions} ─────────────│
  │◄─── {Certificate} ─────────────────────│
  │◄─── {CertificateVerify} ───────────────│
  │◄─── {Finished} ────────────────────────│
  │                                          │
  │─── {Finished} ───────────────────────►  │
  │                                          │
  │◄══════════ Application Data ═══════════►│
  
  {} = encrypted with handshake key
  0-RTT resumption: client can send data with first flight (replay risk)
```

**TLS 1.3 security improvements over TLS 1.2:**
- Removed weak cipher suites (RC4, 3DES, export ciphers, non-AEAD modes)
- Mandatory ephemeral key exchange (perfect forward secrecy always)
- Encrypted Certificate and ServerHello (only ServerHello's server_random visible to passive observer)
- Removed RSA key exchange (which had no PFS)
- Simplified cipher suite list: TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256, TLS_AES_128_GCM_SHA256

**TLS deployment security checklist:**
```
Certificate:
  [ ] Valid CA chain (no self-signed in production except internal PKI)
  [ ] RSA ≥ 2048 bit or ECDSA P-256/P-384
  [ ] Short validity (≤ 1 year; 90 days preferred — Let's Encrypt)
  [ ] CAA record restricts issuance to approved CAs
  [ ] CT (Certificate Transparency) logged
  [ ] OCSP stapling enabled

Protocol:
  [ ] TLS 1.3 only (TLS 1.2 if legacy required with restricted ciphers)
  [ ] Disable TLS 1.0, 1.1 (deprecated, RFC 8996)
  [ ] Disable SSL 3.0, SSL 2.0
  [ ] Ephemeral DH only (no static RSA/DH)

Cipher suites (TLS 1.2 if needed):
  [ ] ECDHE-ECDSA-AES256-GCM-SHA384
  [ ] ECDHE-RSA-AES256-GCM-SHA384
  [ ] ECDHE-ECDSA-CHACHA20-POLY1305
  [ ] No CBC mode ciphers (BEAST, POODLE)
  [ ] No RC4, DES, 3DES, NULL, EXPORT

HTTP headers:
  [ ] HSTS (Strict-Transport-Security: max-age=31536000; includeSubDomains; preload)
  [ ] Certificate pinning (HPKP deprecated; use CAA instead)
```

```bash
# Test TLS configuration
testssl.sh --severity HIGH https://example.com
openssl s_client -connect example.com:443 -tls1_3

# Check cipher suites offered
nmap --script ssl-enum-ciphers -p 443 example.com

# Verify certificate chain
openssl s_client -connect example.com:443 -showcerts 2>/dev/null | \
    openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not After"
```

**mTLS (Mutual TLS):** Both client AND server authenticate with certificates. Essential for service-to-service communication in microservices / zero-trust architectures. Used by Istio, Linkerd, Consul Connect.

```bash
# Generate self-signed CA + cert for mTLS testing
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 365 \
    -subj "/CN=Internal CA"

openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/CN=server"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -days 90

# Configure nginx for mTLS
# ssl_client_certificate /etc/nginx/ca.crt;
# ssl_verify_client on;  # Require client cert signed by CA
```

### 6.9 QUIC

QUIC (RFC 9000) is the transport used by HTTP/3. It runs over UDP, implements TLS 1.3 natively, and provides:
- 0-RTT or 1-RTT connection establishment
- Multiplexing without head-of-line blocking (stream-level, not connection-level)
- Connection migration (IP/port changes don't break connections — mobile-friendly)
- Built-in encryption (entire payload including headers encrypted)

**QUIC security considerations:**
- Traditional DPI and iptables port-based filtering is ineffective (QUIC uses UDP 443, content is encrypted)
- Firewall by connection ID is possible but complex
- QUIC's 0-RTT has replay attack risks (same as TLS 1.3 0-RTT) — servers must be idempotent for 0-RTT data
- UDP port 443 is required — firewalls that block all UDP will fall back to TCP/TLS (client side)
- QUIC amplification: during handshake, server sends more data than client — built-in anti-amplification (3x limit until address validated)

```bash
# Identify QUIC traffic (Wireshark filter)
# udp.port == 443 and (quic)

# Block QUIC to force TLS/TCP (for DPI environments)
iptables -A OUTPUT -p udp --dport 443 -j REJECT --reject-with icmp-port-unreachable
# Clients will fall back to TCP/443 (TLS 1.3)
```

---

## 7. Routing — L3 Control & Data Plane

### 7.1 Architecture: Control Plane vs. Data Plane

```
Control Plane                        Data Plane
─────────────────────────────────────────────────────────────────
Routing protocols (BGP, OSPF)       Forwarding table (FIB)
Route computation                   Per-packet lookup
RIB (Routing Information Base)      Hardware TCAM (on switches)
Route redistribution                Linux: FIB (ip_fib_main)
Policy (route maps, prefix lists)   XDP/eBPF fast path
                                    Hardware offload (SmartNIC)
```

Separation of control and data plane is a security principle: compromising the control plane (e.g., BGP hijacking) affects routing decisions but the data plane may still forward correctly (and vice versa with hardware faults).

### 7.2 Linux Routing — FIB, Policy Routing, VRF

**Linux FIB (Forwarding Information Base):**
```bash
# View routing table (main table)
ip route show table main
ip route show table all   # All tables (main, local, default)

# Routing tables (0-255, or by name in /etc/iproute2/rt_tables)
cat /etc/iproute2/rt_tables
# 255     local   (kernel-managed: local addresses, broadcast)
# 254     main    (default routing table)
# 253     default (router of last resort)
# 0       unspec

# Policy routing — route based on source IP, mark, TOS, etc.
# Rule: if source is 10.0.0.0/8, use routing table 100
ip rule add from 10.0.0.0/8 table 100 priority 100
ip rule show

# Add route to custom table
ip route add default via 192.168.2.1 table 100

# VRF (Virtual Routing and Forwarding) — kernel 4.3+
# Each VRF is an isolated routing domain
ip link add vrf-red type vrf table 10
ip link set vrf-red up
ip link set eth1 master vrf-red       # Assign interface to VRF
ip route show vrf vrf-red
```

**Policy-based routing (PBR) use cases:**
- Route management traffic via out-of-band interface
- Route traffic through security appliances (IDS/IPS) based on fwmark
- Multi-path routing (ECMP) for load distribution
- Source-based routing for multi-homed servers

```bash
# fwmark-based routing: route marked packets through VPN
iptables -t mangle -A OUTPUT -p tcp --dport 443 -j MARK --set-mark 100
ip rule add fwmark 100 table 100 priority 200
ip route add default via 10.8.0.1 table 100  # VPN gateway
```

### 7.3 OSPF — Open Shortest Path First (RFC 2328)

OSPF is a link-state IGP (Interior Gateway Protocol) that builds a complete topology map (LSDB — Link State Database) and computes shortest paths using Dijkstra's algorithm.

**OSPF packet types:**
```
Type 1: Hello          — neighbor discovery & keepalive
Type 2: Database Desc  — LSDB summary exchange
Type 3: LS Request     — request specific LSAs
Type 4: LS Update      — send LSAs
Type 5: LS Acknowledge — acknowledge LSA receipt
```

**OSPF security:**

OSPF has no built-in authentication in its original form. Unauthenticated OSPF is a major security risk — an attacker on the network can inject false LSAs and redirect traffic.

```
Authentication options:
  Type 0: None (no auth — NEVER use in production)
  Type 1: Plain text password (visible in packet — weak)
  Type 2: MD5 HMAC (RFC 2154) — acceptable minimum
  OSPF with IPsec (RFC 4552) — strongest: encryption + auth
```

```bash
# FRRouting configuration (OSPF with MD5 auth)
# /etc/frr/ospfd.conf

router ospf
  ospf router-id 10.0.0.1
  network 10.0.0.0/8 area 0

interface eth0
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 <strong-key>
  ip ospf hello-interval 10
  ip ospf dead-interval 40

# OSPF-specific attacks:
# 1. MaxAge LSA attack: send LSA with MaxAge=3600s → router removes it from LSDB
# 2. Sequence number wrap: predict/forge sequence numbers
# 3. Phantom router: inject LSA for non-existent router, redirect traffic

# Detection: monitor LSDB changes
# vtysh -c "show ip ospf database" | diff - <previous_snapshot>
```

**OSPF areas and security:**
- Area 0 (backbone) is the most critical — compromise here affects all areas
- Stub areas and NSSA areas limit LSA flooding — reduces attack surface
- ABRs (Area Border Routers) and ASBRs (AS Boundary Routers) are high-value targets

### 7.4 IS-IS

IS-IS is a link-state protocol similar to OSPF but operates at L2 (doesn't use IP for its own packets — uses CLNS). This makes it slightly harder to spoof. Used extensively in large ISP backbones and data centers (Clos fabrics).

IS-IS supports authentication (MD5, SHA1 with RFC 5304/5310) and is used by cloud providers internally.

```
IS-IS security advantages over OSPF:
- Runs below IP → IP spoofing doesn't directly affect IS-IS
- HMAC-MD5/SHA1 authentication supported
- Used in data center fabrics (Clos) for its simplicity and scale
```

---

## 8. BGP Deep Dive & Security

### 8.1 BGP Fundamentals

BGP (Border Gateway Protocol, RFC 4271) is the routing protocol of the internet. It is a path-vector protocol — routes carry the complete AS_PATH, enabling loop detection and policy enforcement based on the sequence of ASes a route traverses.

**BGP session types:**
- **iBGP (internal BGP):** Between routers in the same AS. Requires full mesh or route reflectors. Next-hop unchanged.
- **eBGP (external BGP):** Between routers in different ASes. Next-hop set to advertising router's IP. TTL=1 by default (prevents remote session attacks).

**BGP attributes (key for policy/security):**
```
Well-known mandatory:    ORIGIN, AS_PATH, NEXT_HOP
Well-known discretionary: LOCAL_PREF, ATOMIC_AGGREGATE
Optional transitive:     COMMUNITY, AGGREGATOR, EXTENDED COMMUNITY
Optional non-transitive: MED (Multi-Exit Discriminator), CLUSTER_LIST
```

### 8.2 BGP Attack Taxonomy

**8.2.1 BGP Hijacking**

BGP hijacking occurs when an AS advertises prefixes it doesn't own, causing traffic to be misrouted.

Types:
1. **Exact prefix hijack:** Advertise 1.2.3.0/24 (same as victim) — traffic splits between victim and attacker based on AS_PATH length and policy
2. **Subprefix hijack:** Advertise 1.2.3.0/25 (more specific) — BGP always prefers longer prefix match → all traffic goes to attacker
3. **AS PATH manipulation:** Prepend victim's AS to make route appear to originate from legitimate AS

Famous incidents:
- Pakistan Telecom → YouTube hijack (2008)
- China Telecom US traffic hijack (2010)
- Rostelecom BGP hijack of financial prefixes (2020)
- Amazon Route 53 BGP hijack for crypto theft (2018)

**8.2.2 BGP Route Leak**

A route learned from one peer is incorrectly announced to another, creating traffic loops or unexpected routing. Classic example: a transit customer announces routes learned from ISP A to ISP B.

**8.2.3 BGP Denial of Service**

- **UPDATE message flood:** Send thousands of UPDATE messages, overwhelming router CPU
- **Prefix deaggregation:** Withdraw aggregate, announce thousands of /32s → BGP table explosion (routing table attack)
- **NOTIFICATION message:** Forge BGP NOTIFICATION to tear down session

### 8.3 BGP Security Mechanisms

**8.3.1 RPKI (Resource Public Key Infrastructure)**

RPKI (RFC 6480) provides cryptographic attestation of IP prefix ownership. An ROA (Route Origin Authorization) is a signed object stating which AS is authorized to originate a prefix.

```
ROA: "AS64496 is authorized to originate 192.0.2.0/24 (maxLength: 24)"

BGP route validation states:
  Valid:   Route's origin AS matches an ROA; prefix length ≤ maxLength
  Invalid: Origin AS doesn't match ROA, or prefix is more specific than maxLength
  NotFound: No ROA covering the prefix

Policy (SHOULD implement):
  Valid    → Accept (possibly prefer with LOCAL_PREF bump)
  Invalid  → DROP (the attacker's advertisement)
  NotFound → Accept (without preference change — transitional)
```

```bash
# Check RPKI status for a prefix (using routinator or similar)
curl https://rpki.cloudflare.com/api/v1/validity/AS64496/192.0.2.0/24

# FRRouting RPKI configuration
# /etc/frr/bgpd.conf
rpki
  rpki cache rtr.example.com 3323
  rpki polling-period 300

router bgp 64496
  bgp rpki strict    # Drop INVALID routes

# Verify RPKI validation
vtysh -c "show bgp ipv4 unicast 1.1.1.0/24"
```

**8.3.2 BGPsec (RFC 8205)**

BGPsec provides cryptographic signing of the AS_PATH — each AS in the path signs the route update, preventing AS_PATH manipulation. Operationally complex; RPKI ROV (Route Origin Validation) is widely deployed while BGPsec deployment is minimal.

**8.3.3 TCP-AO (Authentication Option, RFC 5925)**

BGP runs over TCP. TCP-AO provides cryptographic authentication of TCP segments, preventing TCP RST injection and session hijacking against BGP sessions.

```bash
# Linux TCP-AO support (kernel 6.7+)
# Configure with ip tcp_ao subcommand (iproute2 6.7+)
ip tcp_ao add 192.168.1.2 key mykey algo hmac-sha256 send_id 1 recv_id 1

# FRRouting: configure MD5 on BGP session (older, widely supported)
neighbor 192.168.1.2 password <strong-password>

# eBGP: TTL security (Generalized TTL Security Mechanism, RFC 5082)
neighbor 192.168.1.2 ttl-security hops 1
# eBGP session only accepts packets with TTL ≥ 254 (255 - 1)
# Prevents remote attacks (attacker must be directly connected)
```

**8.3.4 BGP Prefix Filtering**

Prefix filtering is the most immediately deployable BGP security control:

```
# FRRouting — prefix-list for eBGP customer
ip prefix-list CUSTOMER-IN seq 5  permit 192.0.2.0/24
ip prefix-list CUSTOMER-IN seq 10 permit 192.0.2.0/24 le 28  # allow subnets up to /28
ip prefix-list CUSTOMER-IN seq 100 deny any  # deny everything else

router bgp 64496
  neighbor 192.168.1.2 prefix-list CUSTOMER-IN in

# Bogon prefix filtering (IANA reserved, RFC 5735)
ip prefix-list BOGONS seq 5   deny 0.0.0.0/8 le 32
ip prefix-list BOGONS seq 10  deny 10.0.0.0/8 le 32
ip prefix-list BOGONS seq 15  deny 127.0.0.0/8 le 32
ip prefix-list BOGONS seq 20  deny 169.254.0.0/16 le 32
ip prefix-list BOGONS seq 25  deny 172.16.0.0/12 le 32
ip prefix-list BOGONS seq 30  deny 192.0.2.0/24 le 32
ip prefix-list BOGONS seq 35  deny 192.168.0.0/16 le 32
ip prefix-list BOGONS seq 40  deny 198.18.0.0/15 le 32
ip prefix-list BOGONS seq 45  deny 198.51.100.0/24 le 32
ip prefix-list BOGONS seq 50  deny 203.0.113.0/24 le 32
ip prefix-list BOGONS seq 55  deny 224.0.0.0/4 le 32
ip prefix-list BOGONS seq 60  deny 240.0.0.0/4 le 32
ip prefix-list BOGONS seq 100 permit any
```

**8.3.5 BGP Community-Based Security**

Communities allow tagging routes with operational metadata:

```
NO_EXPORT (65535:65281)        — Don't export beyond current AS
NO_ADVERTISE (65535:65282)     — Don't advertise to any peer
BLACKHOLE (65535:666)          — RFC 7999: trigger RTBH for this prefix
GRACEFUL_SHUTDOWN (65535:0)    — RFC 8326: planned maintenance
```

**RTBH (Remotely Triggered Blackhole) for DDoS mitigation:**
```
# When under DDoS attack on 192.0.2.100:
# Announce 192.0.2.100/32 with BLACKHOLE community to upstream provider
# Provider drops all traffic to that IP at their edge
# Protects rest of infrastructure at cost of single IP availability

router bgp 64496
  neighbor upstream route-map BLACKHOLE-OUT out

route-map BLACKHOLE-OUT permit 10
  match community BLACKHOLE-TRIGGER
  set community 65535:666 additive
  set local-preference 0

ip community-list standard BLACKHOLE-TRIGGER permit 64496:9999
```

### 8.4 BGP Monitoring

```bash
# Real-time BGP monitoring with RIPE RIS or RouteViews
# Quagga/FRR: export to Kafka/BGP API

# gobgp — modern BGP implementation for monitoring
gobgp global rib -a ipv4

# bgpd log monitoring (FRRouting)
vtysh -c "debug bgp updates"
vtysh -c "debug bgp keepalives"

# RIPE Routing Information Service (RIS) live feed
# Subscribe to BGP updates for your prefixes via https://ris-live.ripe.net

# BGPalerter — alert on BGP hijacks/leaks
# docker run -d -v $(pwd):/config nttgin/bgpalerter:latest
```

---

## 9. Switching — L2 Control & Data Plane

### 9.1 Spanning Tree Protocol (STP, IEEE 802.1D)

STP prevents L2 loops by electing a Root Bridge and blocking redundant paths. All bridges send BPDUs (Bridge Protocol Data Units).

**STP security attacks:**
1. **STP Root Bridge takeover:** Attacker connects a switch claiming superior Bridge ID (lower priority). Becomes Root Bridge. All traffic passes through attacker. Mitigation: **BPDU Guard** on access ports — if BPDU received on non-uplink port, port is err-disabled.

2. **STP topology change attack:** Attacker floods TC (Topology Change) BPDUs, causing all switches to flush their MAC tables every 15 seconds → switches revert to flooding → traffic visible to attacker. Mitigation: **TC Guard**, rate-limit TC BPDUs.

3. **BPDU flooding:** Exhaust STP CPU processing with BPDU floods. Mitigation: **BPDU Storm Control**.

```bash
# Linux bridge STP configuration
brctl stp br0 on
brctl showstp br0

# Enable BPDU guard on Linux bridge ports (using ebtables)
# Drop BPDUs received on non-uplink ports
ebtables -A INPUT -p 802_1Q --8021q-encap STP -j DROP

# Modern alternative: use ip link with guard
ip link set br0 type bridge stp_state 1
```

**RSTP (Rapid STP, 802.1W) and MSTP (Multiple STP, 802.1S):** Modern deployments use RSTP (much faster convergence: ~1s vs 30-50s for STP) or MSTP (maps multiple VLANs to STP instances for efficient load distribution). Same security concerns apply.

### 9.2 VLANs and 802.1Q Security

**VLAN hopping attacks:**

1. **Switch Spoofing:** Attacker negotiates a trunk link using DTP (Dynamic Trunking Protocol) — a Cisco proprietary protocol that automatically forms trunks. Attacker becomes a trunk, receiving all VLAN traffic. Mitigation: Disable DTP (`switchport nonegotiate`), explicitly configure ports as access or trunk.

2. **Double-tagging:** Attacker on native VLAN sends double-tagged frame (outer tag = native VLAN, inner tag = target VLAN). Switch strips outer tag, forwards on trunk with inner tag intact, reaching target VLAN. Only works outbound (attacker → victim). Mitigation: Set native VLAN to a VLAN not used for any host traffic (e.g., VLAN 999), explicitly tag native VLAN on trunks.

```bash
# Linux VLAN configuration
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up
ip addr add 10.100.0.1/24 dev eth0.100

# VLAN-aware bridge (Linux kernel 3.9+)
ip link add name br0 type bridge vlan_filtering 1
ip link set eth0 master br0
bridge vlan add dev eth0 vid 100 pvid untagged  # Access port for VLAN 100
bridge vlan add dev eth1 vid 100               # Trunk port
bridge vlan show
```

### 9.3 802.1X — Port-Based Network Access Control

802.1X provides authentication before a port is allowed to forward traffic. Requires: Supplicant (client), Authenticator (switch), Authentication Server (RADIUS).

```
Client (Supplicant) ──EAP──► Switch (Authenticator) ──RADIUS──► Auth Server
                              [port: unauthorized state]
                              
After auth success:
                              [port: authorized state → normal forwarding]
```

**EAP methods (security ranking):**
```
EAP-MD5      — Weak (MD5, no server auth) — avoid
LEAP         — Vulnerable (Cisco proprietary) — avoid
PEAP         — TLS tunnel, then inner auth (EAP-MSCHAPv2) — common
EAP-TTLS     — TLS tunnel, inner auth flexible — good
EAP-TLS      — Mutual TLS (strongest, requires client certs)
```

```bash
# Linux hostapd / wpa_supplicant for 802.1X
# /etc/wpa_supplicant/wpa_supplicant.conf
network={
    key_mgmt=IEEE8021X
    eap=TLS
    identity="user@example.com"
    ca_cert="/etc/ssl/certs/ca.pem"
    client_cert="/etc/ssl/certs/client.pem"
    private_key="/etc/ssl/private/client.key"
}

# freeRADIUS server (authentication server)
# Users file, TLS certificates, VLAN assignment via RADIUS attributes
```

---

## 10. IPsec & WireGuard

### 10.1 IPsec Architecture

IPsec (RFC 4301) provides security at the IP layer. It can operate in:
- **Transport mode:** Encrypts/authenticates payload only, IP header intact. Used for host-to-host.
- **Tunnel mode:** Encrypts/authenticates entire IP packet, new IP header added. Used for VPN (site-to-site, remote access).

**IPsec protocols:**
- **AH (Authentication Header, protocol 51):** Integrity + authentication only. No encryption. Problematic with NAT (covers original IP header which NAT modifies).
- **ESP (Encapsulating Security Payload, protocol 50):** Confidentiality + integrity + authentication. Supports NAT traversal (NAT-T: UDP port 4500 encapsulation). Use ESP exclusively in modern deployments.

**IKEv2 (Internet Key Exchange v2, RFC 7296):**

IKEv2 negotiates IPsec SAs (Security Associations). Key features:
- EAP support for user authentication
- MOBIKE (RFC 4555) — IP address mobility
- Traffic selectors for fine-grained policy
- Cryptographically strong: DH groups, PRF, cipher suite negotiation

```bash
# strongSwan (IPsec/IKEv2 implementation)
# /etc/swanctl/swanctl.conf

connections {
    site-to-site {
        version = 2
        local_addrs  = 203.0.113.1
        remote_addrs = 203.0.113.2

        local {
            auth = pubkey
            certs = /etc/swanctl/x509/host.crt
            id = host1.example.com
        }
        remote {
            auth = pubkey
            id = host2.example.com
        }

        children {
            net-net {
                local_ts  = 10.1.0.0/16
                remote_ts = 10.2.0.0/16
                esp_proposals = aes256gcm128-x25519
                dpd_action = restart
            }
        }

        proposals = aes256gcm128-prfsha384-x25519
        keyingtries = 0        # Retry indefinitely
        dpd_delay = 30s
    }
}

# Load config
swanctl --load-all

# Status
swanctl --list-sas
swanctl --list-conns

# Verify IPsec SAs in kernel
ip xfrm state
ip xfrm policy
```

**IPsec security checklist:**
```
IKEv2 proposals:
  [ ] Cipher: AES-256-GCM (AEAD preferred, avoids separate MAC)
  [ ] PRF: SHA-384 or SHA-512
  [ ] DH group: 25 (Curve25519) or 20 (P-384) — no DH group 1,2,5
  [ ] Avoid 3DES, DES, MD5, SHA1

Authentication:
  [ ] RSA/ECDSA certificates (avoid PSK — harder to manage at scale)
  [ ] CRL or OCSP checking enabled
  [ ] Certificate expiry monitoring

Operations:
  [ ] DPD (Dead Peer Detection) enabled
  [ ] Perfect Forward Secrecy — IKEv2 always uses PFS
  [ ] Rekeying before lifetime expiry
```

### 10.2 WireGuard

WireGuard (RFC-in-progress, mainlined Linux 5.6) is a modern VPN protocol with a minimal codebase (~4,000 lines), superior performance to OpenVPN/IPsec, and a fixed modern cryptographic stack.

**WireGuard cryptographic stack (no negotiation — fixed):**
```
Key exchange: Noise_IKpsk2 protocol (based on Noise Framework)
DH:           Curve25519
Cipher:       ChaCha20-Poly1305 (AEAD)
Hash:         BLAKE2s
MAC:          HMAC-BLAKE2s
KDF:          HKDF with BLAKE2s
```

**Security properties:**
- **Cryptographic identity:** Each peer has a Curve25519 keypair. No PKI needed (peer's public key IS the identity).
- **Stealth:** No response until valid handshake. Port appears closed to scanners.
- **Perfect Forward Secrecy:** Session keys rotate every few minutes. Past sessions protected even if long-term key compromised.
- **DoS resistance:** Mao Zedong cookie mechanism — rate-limit handshake CPU with challenge-response before allocating state.
- **Minimal attack surface:** ~4,000 LoC vs OpenVPN's ~70,000. Formal verification possible.

```bash
# WireGuard configuration — server (Linux kernel module)
# Generate keypair
wg genkey | tee server.key | wg pubkey > server.pub
wg genkey | tee client.key | wg pubkey > client.pub

# /etc/wireguard/wg0.conf — server
[Interface]
PrivateKey = <server_private_key>
Address = 10.0.0.1/24
ListenPort = 51820
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; \
           iptables -A FORWARD -o wg0 -j ACCEPT; \
           iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; \
           iptables -D FORWARD -o wg0 -j ACCEPT; \
           iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client_public_key>
PresharedKey = <optional_psk_for_post_quantum_resistance>
AllowedIPs = 10.0.0.2/32

# /etc/wireguard/wg0.conf — client
[Interface]
PrivateKey = <client_private_key>
Address = 10.0.0.2/24
DNS = 10.0.0.1

[Peer]
PublicKey = <server_public_key>
PresharedKey = <optional_psk>
Endpoint = 203.0.113.1:51820
AllowedIPs = 0.0.0.0/0, ::/0   # Full tunnel
PersistentKeepalive = 25        # Keep NAT mappings alive

# Bring up interface
wg-quick up wg0
systemctl enable wg-quick@wg0

# Monitor WireGuard state
wg show
wg show wg0 dump   # Machine-readable

# Performance tuning
# WireGuard uses kernel threads (1 per CPU for crypto)
# For high throughput, ensure CPU affinity of IRQs matches WG threads
```

**WireGuard vs IPsec comparison:**

| Aspect | WireGuard | IPsec/IKEv2 |
|--------|-----------|-------------|
| Codebase | ~4,000 LoC | >70,000 LoC |
| Crypto agility | None (fixed — security feature) | Full negotiation |
| Performance | ~4 Gbps (single core) | ~2-3 Gbps (OpenVPN worse) |
| DoS resistance | Built-in cookie mechanism | IKEv2 has cookie mechanism |
| Interoperability | WireGuard implementations only | Broad (Cisco, Juniper, etc.) |
| Enterprise features | Limited (no RADIUS, no XAUTH) | Full (EAP, RADIUS, X.509) |
| NAT traversal | Built-in | NAT-T (UDP 4500) |

---

## 11. Network Segmentation & Microsegmentation

### 11.1 Traditional Segmentation

Traditional network segmentation uses VLANs and firewall zones to create security boundaries:

```
Internet
    │
  [Firewall]
    │
  DMZ  ─── Web servers (reverse proxy)
    │
  [Firewall/ACL]
    │
  App Zone ─── Application servers
    │
  [Firewall/ACL]
    │
  DB Zone  ─── Database servers
    │
  [Firewall/ACL]
    │
  Mgmt Zone ── Management hosts (bastion, monitoring)
```

**Limitations:**
- Flat zones — lateral movement within a zone is unconstrained
- Firewall rules based on IP/port — not identity-aware
- Doesn't scale for microservices (hundreds of services)
- East-west traffic between zones requires hairpin through firewall

### 11.2 Microsegmentation

Microsegmentation enforces security policies at the individual workload level, regardless of network topology. Every workload-to-workload flow is explicitly authorized.

**Implementation options:**

1. **Host-based (iptables/nftables/eBPF):** Rules on each host. Enforced even for intra-host traffic. Used by Kubernetes NetworkPolicy (via CNI plugins).

2. **SDN-based (NSX-T, Calico, Cilium):** Central policy controller pushes rules to distributed enforcement points. Identity-aware (uses labels/tags, not IPs).

3. **Service Mesh (Istio, Linkerd):** mTLS between all services, RBAC authorization policies. L7-aware.

```yaml
# Kubernetes NetworkPolicy — basic microsegmentation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  # Implicit: all other traffic denied
```

```yaml
# Cilium NetworkPolicy — L7-aware (HTTP method/path filtering)
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-get-only
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: /api/.*
  # Deny POST, PUT, DELETE even from frontend
```

### 11.3 Zero-Trust Network Access (ZTNA)

ZTNA replaces VPN with per-application, per-session access control based on identity, device posture, and context.

Principles:
1. Never trust, always verify — no implicit trust based on network location
2. Least-privilege access — minimum required access per request
3. Assume breach — segment and monitor even internal traffic
4. Verify explicitly — authenticate and authorize every request

```
Traditional VPN model:
  User → VPN → FULL internal network access

ZTNA model:
  User → Identity Provider (IdP) → Device posture check → 
  Policy Engine → Application proxy → Specific app only
```

---

## 12. Cloud Networking

### 12.1 AWS VPC (Virtual Private Cloud)

AWS VPC is a software-defined network built on top of AWS's physical infrastructure using VXLAN-based overlay networking.

**VPC components:**
```
VPC (CIDR: 10.0.0.0/16)
├── Subnets (per AZ, per tier)
│   ├── Public subnet  10.0.1.0/24 (AZ1) — has route to IGW
│   ├── Public subnet  10.0.2.0/24 (AZ2)
│   ├── Private subnet 10.0.3.0/24 (AZ1) — route to NAT GW
│   ├── Private subnet 10.0.4.0/24 (AZ2)
│   └── DB subnet      10.0.5.0/24 (AZ1) — no internet route
├── Route Tables (per subnet)
├── Internet Gateway (IGW) — public egress/ingress
├── NAT Gateway (managed, per-AZ) — private subnet egress
├── Security Groups (stateful, per-ENI)
├── Network ACLs (stateless, per-subnet)
├── VPC Endpoints (Gateway/Interface) — private AWS service access
├── VPC Peering / Transit Gateway — inter-VPC connectivity
└── Flow Logs (VPC, subnet, or ENI level → CloudWatch/S3)
```

**Security Groups vs NACLs:**
```
Security Groups:                   Network ACLs:
  Stateful (return allowed auto)     Stateless (must allow both dirs)
  Instance/ENI level                 Subnet level
  Allow rules only (implicit deny)   Allow AND Deny rules
  Evaluated as a unit                Rules evaluated in order (rule number)
  No ordering                        Lower number = higher priority
  Up to 5 SGs per ENI                One NACL per subnet
```

**VPC Security architecture:**
```bash
# Best practice: Security Groups as security boundaries

# Web tier SG — allow HTTP/HTTPS from internet
aws ec2 create-security-group --group-name web-sg \
    --description "Web tier" --vpc-id vpc-xxx

aws ec2 authorize-security-group-ingress --group-id sg-web \
    --protocol tcp --port 443 --cidr 0.0.0.0/0

# App tier SG — allow only from web tier SG (not CIDR)
aws ec2 authorize-security-group-ingress --group-id sg-app \
    --protocol tcp --port 8080 \
    --source-group sg-web    # Reference SG, not IP!

# DB tier SG — allow only from app tier SG
aws ec2 authorize-security-group-ingress --group-id sg-db \
    --protocol tcp --port 5432 \
    --source-group sg-app

# VPC Flow Logs — essential for security monitoring
aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids vpc-xxx \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name /aws/vpc/flowlogs \
    --deliver-logs-permission-arn arn:aws:iam::xxx:role/flow-logs-role

# VPC Endpoint — access S3 without internet (no NAT GW cost, private)
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxx \
    --service-name com.amazonaws.us-east-1.s3 \
    --route-table-ids rtb-xxx \
    --policy-document file://s3-endpoint-policy.json

# PrivateLink (Interface endpoint) — access services privately
aws ec2 create-vpc-endpoint \
    --vpc-endpoint-type Interface \
    --vpc-id vpc-xxx \
    --service-name com.amazonaws.us-east-1.secretsmanager \
    --subnet-ids subnet-xxx \
    --security-group-ids sg-xxx
```

**AWS Network Firewall** (managed, stateful/stateless, Suricata rules):
```bash
# Create Network Firewall policy
aws network-firewall create-firewall-policy \
    --firewall-policy-name prod-fw-policy \
    --firewall-policy '{
        "StatelessDefaultActions": ["aws:forward_to_sfe"],
        "StatelessFragmentDefaultActions": ["aws:drop"],
        "StatefulRuleGroupReferences": [
            {"ResourceArn": "arn:aws:network-firewall:...:stateful-rulegroup/IDS-rules"}
        ]
    }'

# AWS WAF for L7 (attached to ALB, CloudFront, API Gateway)
aws wafv2 create-web-acl \
    --name prod-waf \
    --scope REGIONAL \
    --default-action Block={} \
    --rules file://waf-rules.json \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=prod-waf
```

**AWS Shield** (DDoS protection):
- Shield Standard: automatic, free, L3/L4 protection for all AWS resources
- Shield Advanced: $3,000/month, L7 protection, DRT access, cost protection, Route53 health check integration

### 12.2 Azure Virtual Network (VNet)

```
VNet (10.0.0.0/8)
├── Subnets (span entire region, no AZ restriction)
│   ├── AzureFirewallSubnet (/26 minimum) — Azure Firewall dedicated
│   ├── GatewaySubnet       — VPN/ExpressRoute gateway
│   ├── WebSubnet    10.0.1.0/24
│   ├── AppSubnet    10.0.2.0/24
│   └── DataSubnet   10.0.3.0/24
├── NSG (Network Security Group) — stateful, per-subnet or per-NIC
├── Azure Firewall — managed L3-L7 firewall with IDPS
├── Application Gateway — L7 LB + WAF
├── DDoS Protection Standard — per-VNet, advanced mitigation
├── Private Endpoint — private access to Azure PaaS services
├── Service Endpoint — optimized path to Azure services (not private)
├── VNet Peering — inter-VNet (regional or global)
└── Virtual WAN — managed hub-spoke topology
```

**NSG rules — Azure specifics:**
```bash
# Azure NSG priority: 100-4096 (lower = higher priority)
# Default rules (cannot be deleted, priority 65000-65500):
#   AllowVnetInBound, AllowAzureLoadBalancerInBound, DenyAllInBound

az network nsg rule create \
    --resource-group myRG \
    --nsg-name app-nsg \
    --name allow-web-to-app \
    --priority 100 \
    --source-address-prefixes 10.0.1.0/24 \
    --source-port-ranges '*' \
    --destination-address-prefixes 10.0.2.0/24 \
    --destination-port-ranges 8080 \
    --protocol TCP \
    --access Allow \
    --direction Inbound

# Azure Firewall — FQDN-based filtering (unlike AWS SGs)
az network firewall application-rule create \
    --resource-group myRG \
    --firewall-name prod-fw \
    --collection-name allow-updates \
    --name allow-ubuntu-updates \
    --protocols Http=80 Https=443 \
    --source-addresses 10.0.0.0/8 \
    --fqdn-tags Ubuntu \
    --priority 100 \
    --action Allow

# Private Endpoint for Azure SQL (no public internet)
az network private-endpoint create \
    --resource-group myRG \
    --name sql-pe \
    --vnet-name myVNet \
    --subnet DataSubnet \
    --private-connection-resource-id /subscriptions/.../sqlServers/mySQL \
    --group-ids sqlServer \
    --connection-name sql-connection
```

**Azure Defender for Network:** Integrates with NSG flow logs, Azure Firewall logs, and DDoS protection. Provides behavioral analytics and threat intelligence correlation.

### 12.3 GCP VPC

GCP VPC is uniquely **global** — a single VPC spans all regions. No VPC peering needed between regions.

```
GCP VPC (global)
├── Subnets (regional, per-region CIDR)
│   ├── us-central1 10.0.0.0/20
│   ├── europe-west1 10.0.16.0/20
│   └── asia-east1  10.0.32.0/20
├── Firewall Rules (global, tag/SA-based)
├── Cloud Armor (WAF + DDoS — attached to Backend Services)
├── Cloud NAT (managed SNAT for private instances)
├── Private Service Connect (private access to Google APIs)
├── VPC Service Controls (data exfiltration prevention)
└── Packet Mirroring (tap traffic to IDS/monitoring)
```

**GCP Firewall Rules — tag and Service Account based:**
```bash
# GCP firewall rules use network tags OR service accounts as source/target
# This is more flexible than CIDR-based rules in AWS/Azure

# Allow HTTP from load balancer to web instances (tag-based)
gcloud compute firewall-rules create allow-http \
    --network prod-vpc \
    --direction INGRESS \
    --priority 1000 \
    --source-ranges 130.211.0.0/22,35.191.0.0/16 \  # GCP LB health check ranges
    --target-tags web-server \
    --allow tcp:80,tcp:443

# Allow app tier to DB tier using Service Accounts (identity-based)
gcloud compute firewall-rules create allow-app-to-db \
    --network prod-vpc \
    --direction INGRESS \
    --priority 1000 \
    --source-service-accounts app-sa@project.iam.gserviceaccount.com \
    --target-service-accounts db-sa@project.iam.gserviceaccount.com \
    --allow tcp:5432

# GCP VPC Flow Logs (per subnet)
gcloud compute networks subnets update prod-subnet \
    --region us-central1 \
    --enable-flow-logs \
    --logging-aggregation-interval interval-5-sec \
    --logging-flow-sampling 0.5 \
    --logging-metadata include-all

# VPC Service Controls — prevent data exfiltration from GCP services
gcloud access-context-manager perimeters create prod-perimeter \
    --policy=accessPolicies/xxx \
    --title="Production Perimeter" \
    --resources=projects/my-project \
    --restricted-services=bigquery.googleapis.com,storage.googleapis.com \
    --access-levels=accessPolicies/xxx/accessLevels/trusted-networks
```

**GCP Cloud Armor (WAF + DDoS):**
```bash
# Create security policy
gcloud compute security-policies create prod-armor \
    --description "Production WAF policy"

# Add OWASP top-10 pre-configured rules
gcloud compute security-policies rules create 1000 \
    --security-policy prod-armor \
    --expression "evaluatePreconfiguredExpr('sqli-v33-stable')" \
    --action deny-403

# Rate limiting (DDoS mitigation)
gcloud compute security-policies rules create 2000 \
    --security-policy prod-armor \
    --expression "true" \
    --action rate-based-ban \
    --rate-limit-threshold-count 1000 \
    --rate-limit-threshold-interval-sec 60 \
    --ban-duration-sec 300

# Attach to backend service
gcloud compute backend-services update prod-backend \
    --security-policy prod-armor \
    --global
```

### 12.4 Overlay Networking — VXLAN & Geneve

Cloud providers and container orchestrators use overlay networks to virtualize L2 over L3 infrastructure. The two dominant protocols are VXLAN and Geneve.

**VXLAN (Virtual eXtensible LAN, RFC 7348):**
```
Encapsulation:
Outer: [ Ethernet | IP | UDP (port 4789) | VXLAN Header (8B) | Inner Frame ]
VXLAN Header: VXLAN flags (8b) | Reserved (24b) | VNI (24b) | Reserved (8b)

VNI (VXLAN Network Identifier): 24 bits = 16 million virtual networks
                                 vs VLAN's 12 bits = 4096 VLANs
```

```bash
# Linux VXLAN interface
ip link add vxlan100 type vxlan \
    id 100 \
    remote 192.168.1.2 \        # VTEP peer (unicast tunnel)
    local 192.168.1.1 \
    dstport 4789 \
    dev eth0

ip link set vxlan100 up
ip addr add 10.100.0.1/24 dev vxlan100

# Multicast VXLAN (for flooding/learning)
ip link add vxlan100 type vxlan \
    id 100 \
    group 239.0.0.100 \        # Multicast group for BUM traffic
    dev eth0 \
    dstport 4789

# VXLAN with bridge (connecting multiple containers)
ip link add name br-vxlan type bridge
ip link set vxlan100 master br-vxlan
ip link set veth-container0 master br-vxlan
```

**VXLAN security concerns:**
- No built-in encryption — VXLAN traffic is plaintext UDP
- Any host that can reach UDP 4789 can inject VXLAN frames → impersonate any VNI
- Inner MAC/IP can be spoofed — VTEP should validate source MAC/IP in FDB
- Mitigation: IPsec or WireGuard to encrypt VXLAN underlay; restrict UDP 4789 access

**Geneve (Generic Network Virtualization Encapsulation, RFC 8926):**
Geneve is the next-generation overlay protocol — it's extensible (variable-length options in header) while VXLAN has a fixed header. Used by AWS Nitro, OVN (Open Virtual Network), and increasingly in CNI plugins.

```
Geneve Header:
[ Ver(2) | Opt Len(6) | O(1) | C(1) | Rsvd(6) | Proto Type(16) |
  VNI(24) | Reserved(8) | Options... ]

Options are TLV-encoded, allowing extension for metadata like:
- Security context
- Policy labels
- Tracing/telemetry correlation IDs
```

---

## 13. Zero Trust Networking

### 13.1 Zero Trust Principles

Zero Trust (NIST SP 800-207) asserts that:
1. All resources are accessed in a secure manner regardless of network location
2. Access is granted on a per-session, least-privilege basis
3. Access is determined by dynamic policy (identity + device + context)
4. All traffic is inspected and logged
5. Authentication and authorization are performed before any resource access

```
Traditional perimeter model:
  Internet → Firewall → Internal network (trusted zone)
  Inside the perimeter: implicit trust

Zero Trust model:
  Every request authenticated + authorized + encrypted
  No implicit trust based on network location
  Identity is the new perimeter
```

### 13.2 Zero Trust Architecture Components

```
Identity Plane:
  ├── IdP (Okta, Azure AD, Google Workspace) — SAML, OIDC
  ├── PKI — mutual TLS certificates (SPIFFE/SPIRE for workloads)
  └── Device management (MDM, SCCM) — device posture

Policy Plane:
  ├── Policy Engine (OPA, Styra, proprietary)
  ├── Policy Administrator (translates decisions to enforcement)
  └── Continuous evaluation (real-time context: risk score, behavior)

Data Plane (enforcement):
  ├── PEP (Policy Enforcement Point) — network proxy, agent, gateway
  ├── Encrypted transport (mTLS, TLS 1.3, WireGuard)
  └── Micro-segmentation (per-workload rules)
```

### 13.3 SPIFFE & SPIRE — Workload Identity

SPIFFE (Secure Production Identity Framework for Everyone) provides a standard for cryptographic workload identity in dynamic environments.

```
SPIFFE ID format: spiffe://<trust-domain>/<workload-path>
Example: spiffe://example.com/ns/production/sa/frontend

SVID (SPIFFE Verifiable Identity Document):
  X.509-SVID: X.509 certificate with SPIFFE ID in SAN (SubjectAltName)
  JWT-SVID:   JWT token with SPIFFE ID as subject

SPIRE (SPIFFE Runtime Environment):
  ├── SPIRE Server — CA, identity issuance policy
  ├── SPIRE Agent  — per-node daemon, attests workloads
  └── Workload API — Unix domain socket, issues SVIDs to workloads
```

```yaml
# SPIRE Server registration (register a workload)
spire-server entry create \
    -spiffeID spiffe://example.com/ns/production/sa/frontend \
    -parentID spiffe://example.com/nodes/node1 \
    -selector k8s:ns:production \
    -selector k8s:sa:frontend \
    -ttl 3600

# Workload retrieves SVID via Workload API
# /run/spire/sockets/agent.sock
```

---

## 14. Kubernetes & CNCF Network Security

### 14.1 Kubernetes Networking Model

Kubernetes mandates:
- Every Pod gets a unique IP (no NAT for pod-to-pod within cluster)
- Pods on the same node can communicate directly
- Pods on different nodes communicate without NAT (via CNI plugin)
- Services use iptables/ipvs/eBPF for load balancing and virtual IPs

### 14.2 CNI Security Comparison

| CNI Plugin | Dataplane | NetworkPolicy | L7 Policy | Encryption |
|------------|-----------|---------------|-----------|------------|
| Flannel | VXLAN/host-gw | No (needs Calico) | No | No |
| Calico | eBPF or iptables | Yes | No (with Calico+) | WireGuard |
| Cilium | eBPF | Yes | Yes (HTTP/DNS) | WireGuard |
| Weave | VXLAN | Yes | No | NaCl |
| Canal | Flannel+Calico | Yes | No | No |

**Cilium** is the most security-capable CNCF CNI — eBPF-based, L7-aware, FQDN-based policy, transparent encryption with WireGuard, Hubble for observability.

```yaml
# Cilium L7-aware NetworkPolicy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-security
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8443"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: /api/v1/.*
        - method: POST
          path: /api/v1/orders
          headers:
          - 'Content-Type: application/json'
  egress:
  - toFQDNs:
    - matchName: db.internal.example.com
    toPorts:
    - ports:
      - port: "5432"

---
# Enable WireGuard encryption cluster-wide in Cilium
# cilium-config:
# encryption: wireguard
# encryption-strict-mode: true  # Drop unencrypted pod-to-pod traffic
```

### 14.3 Kubernetes RBAC + NetworkPolicy Security Model

```yaml
# Default deny all — MANDATORY baseline
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}   # Selects ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress

---
# Only allow DNS egress (required for all pods)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

### 14.4 kube-proxy Security

kube-proxy implements Kubernetes Services by programming iptables or ipvs rules. eBPF-based kube-proxy replacement (Cilium kube-proxy free mode) eliminates iptables overhead and provides better performance and observability.

```bash
# View iptables rules created by kube-proxy
iptables -t nat -L KUBE-SERVICES -n --line-numbers
iptables -t nat -L KUBE-SVC-XXXXX -n   # Per-service chain

# kube-proxy uses conntrack for service load balancing
# Monitor conntrack table in K8s cluster
kubectl -n kube-system exec -it $(kubectl get pod -n kube-system \
    -l component=kube-proxy -o name | head -1) -- conntrack -L 2>/dev/null | wc -l

# Cilium kube-proxy replacement
# helm upgrade cilium cilium/cilium \
#   --set kubeProxyReplacement=strict \
#   --set k8sServiceHost=<API_SERVER_IP> \
#   --set k8sServicePort=6443
```

---

## 15. Service Mesh Security (Cilium, Istio)

### 15.1 Service Mesh Security Model

A service mesh provides:
- **mTLS everywhere:** All service-to-service traffic encrypted and mutually authenticated
- **Authorization policies:** Fine-grained RBAC at L7 (which service can call which endpoint)
- **Observability:** Full L7 telemetry (latency, error rates, request traces) without application changes
- **Traffic management:** Circuit breaking, retries, timeouts, canary deployments

### 15.2 Istio Security

```yaml
# Istio: Enforce mTLS cluster-wide (strict mode)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # Global scope
spec:
  mtls:
    mode: STRICT    # No plaintext traffic allowed

---
# Istio: Authorization policy — only frontend can call backend
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/production/sa/frontend"  # SPIFFE identity
    to:
    - operation:
        methods: ["GET"]
        paths: ["/api/*"]

---
# Deny all by default (explicit deny policy)
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}  # No rules = deny all
```

### 15.3 Cilium Hubble — Network Observability

```bash
# Enable Hubble UI
cilium hubble enable --ui

# Real-time flow observation
hubble observe --follow --namespace production

# Filter by specific pod
hubble observe --pod frontend --follow

# Dropped flows (policy violations)
hubble observe --verdict DROPPED --follow

# L7 HTTP flows
hubble observe --protocol http --follow

# Export to Prometheus/Grafana
# hubble-metrics configured in cilium-config:
# hubble-metrics-server: ":9091"
# hubble-metrics: "drop;tcp;flow;icmp;http"
```

---

## 16. DDoS — Taxonomy, Attack Vectors, Mitigations

### 16.1 DDoS Attack Taxonomy

```
Volume-based attacks (saturate bandwidth):
  UDP flood, ICMP flood, DNS amplification, NTP amplification
  Mitigation: upstream scrubbing, RTBH, anycast diffusion

Protocol attacks (exhaust network device state):
  SYN flood, Smurf, fragmented packet flood, Ping of Death
  Mitigation: SYN cookies, rate limiting, stateless ACLs

Application layer attacks (exhaust server resources):
  HTTP flood (GET/POST), Slowloris, RUDY, SSL exhaustion
  Mitigation: WAF, rate limiting, challenge (CAPTCHA, JS challenge)

Reflection/Amplification:
  Attacker → Reflector (with spoofed source=victim) → Victim
  Amplification factor can exceed 50,000x (Memcached)
  Mitigation: BCP38, disable amplifiable services, rate limit responses
```

### 16.2 DDoS Mitigation Architecture

```
Tier 1: Upstream (ISP/Transit provider)
  ├── BGP RTBH (Remotely Triggered Black Hole) — route victim IP to null
  ├── Traffic scrubbing centers (Cogent, Lumen, NTT)
  └── Anycast diffusion (distribute attack across PoPs)

Tier 2: Cloud DDoS mitigation
  ├── AWS Shield Advanced / Azure DDoS Protection / GCP Cloud Armor
  ├── Cloudflare Magic Transit (BGP-based, L3/L4)
  └── Akamai Prolexic / Radware DefensePro

Tier 3: Edge (CDN / Load balancer)
  ├── Rate limiting (per IP, per endpoint)
  ├── WAF rules
  └── Bot detection (JS challenge, fingerprinting)

Tier 4: Host (last line)
  ├── XDP BPF (drop before conntrack — millions pps)
  ├── SYN cookies
  └── Conntrack tuning
```

```bash
# XDP-based SYN flood mitigation
# Rate limit SYN packets per source IP using eBPF LRU hash map
# (conceptual — full implementation is ~200 lines)

# iptables hashlimit — per-IP SYN rate limiting
iptables -A INPUT -p tcp --syn \
    -m hashlimit \
    --hashlimit-mode srcip \
    --hashlimit-upto 10/sec \
    --hashlimit-burst 20 \
    --hashlimit-name syn-limit \
    -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# nftables meter (more efficient)
nft add rule inet filter input \
    tcp flags syn \
    meter syn-flood { ip saddr limit rate 10/second } \
    accept
nft add rule inet filter input tcp flags syn drop
```

---

## 17. Network Intrusion Detection & Prevention

### 17.1 IDS/IPS Architecture

```
Passive IDS (detection only):
  Network TAP or SPAN port → IDS (Suricata, Zeek, Snort)
  Advantage: no latency, no failure mode for traffic
  Disadvantage: can detect but not block

Inline IPS (detection + prevention):
  Traffic passes through IPS engine before forwarding
  Advantage: can drop/block malicious traffic
  Disadvantage: adds latency, single point of failure

Host-based IDS:
  Agent on each host (Falco, OSSEC, Wazuh)
  Monitors system calls, files, network (per-process)
```

### 17.2 Suricata — High-Performance IDS/IPS

```yaml
# /etc/suricata/suricata.yaml (key sections)

vars:
  address-groups:
    HOME_NET: "[10.0.0.0/8,172.16.0.0/12,192.168.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    SQL_SERVERS: "$HOME_NET"
    DNS_SERVERS: "$HOME_NET"

af-packet:
  - interface: eth0
    threads: auto
    cluster-id: 99
    cluster-type: cluster_flow    # Per-flow to same thread
    defrag: yes
    use-mmap: yes
    ring-size: 200000
    block-size: 32768

outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      types:
        - alert:
            payload: yes
            http: yes
            tls: yes
            dnp3: yes
        - http
        - dns
        - tls
        - flow
```

```bash
# Suricata rule syntax
# alert: action | protocol | src | sport | dir | dst | dport | options
alert tcp $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS \
    (msg:"Possible SQL injection"; \
     flow:established,to_server; \
     content:"UNION"; nocase; \
     content:"SELECT"; nocase; distance:0; \
     pcre:"/UNION\s+SELECT/si"; \
     classtype:web-application-attack; \
     sid:1000001; rev:1;)

# Load Emerging Threats ruleset
suricata-update update-sources
suricata-update enable-source et/open
suricata-update
suricata -T -c /etc/suricata/suricata.yaml   # Test config

# Run in IDS mode (inline requires nfqueue or af-xdp)
suricata -c /etc/suricata/suricata.yaml -i eth0

# IPS mode with nfqueue
iptables -I FORWARD -j NFQUEUE --queue-num 0
suricata -c /etc/suricata/suricata.yaml -q 0

# Analyze alerts
jq '. | select(.event_type=="alert")' /var/log/suricata/eve.json | \
    jq '{alert: .alert.signature, src: .src_ip, dst: .dest_ip}' | \
    sort | uniq -c | sort -rn
```

### 17.3 Zeek (formerly Bro) — Network Security Monitor

Zeek is a scriptable network analysis framework — not signature-based but behavioral. Generates rich structured logs and supports custom protocol analysis.

```bash
# Key Zeek log files
# conn.log    — all connections (src, dst, port, bytes, duration)
# dns.log     — all DNS queries/responses
# http.log    — all HTTP requests/responses
# ssl.log     — TLS handshake metadata
# x509.log    — Certificate details
# files.log   — Files transferred (with hash)
# smtp.log    — SMTP sessions

# Start Zeek
zeek -i eth0 local.zeek

# Find DNS tunneling indicators (many unique queries)
cat /var/log/zeek/dns.log | zeek-cut query | sort | uniq -c | sort -rn | head

# Find large HTTP transfers
cat /var/log/zeek/http.log | zeek-cut method uri resp_bytes | \
    awk '$3 > 10000000' | sort -t'\t' -k3 -rn

# Certificate inspection — find short-lived/self-signed certs
cat /var/log/zeek/ssl.log | zeek-cut server_name validation_status | \
    grep -v ok
```

### 17.4 Falco — Runtime Security

Falco uses eBPF to monitor system calls in real-time and detect anomalous behavior (container escapes, privilege escalation, network anomalies).

```yaml
# /etc/falco/falco_rules.yaml — custom network rule
- rule: Unexpected Outbound Connection
  desc: Detect unexpected outbound connections from production pods
  condition: >
    outbound and
    container and
    not fd.sport in (80, 443, 53) and
    not proc.name in (allowed_processes) and
    fd.type = ipv4
  output: >
    Unexpected outbound connection 
    (command=%proc.cmdline connection=%fd.name container=%container.id
     image=%container.image.repository)
  priority: WARNING
  tags: [network, container]

- rule: Network Tool in Container
  desc: Network tools launched in containers (recon indicator)
  condition: >
    spawned_process and
    container and
    proc.name in (network_tools)
  output: >
    Network tool launched in container
    (user=%user.name command=%proc.cmdline container=%container.id)
  priority: NOTICE

- macro: network_tools
  condition: >
    proc.name in (nmap, nc, netcat, ncat, socat, masscan, 
                  tcpdump, tshark, wireshark, ngrep, dsniff,
                  hping, hping3, arp-scan, arpspoof)
```

---

## 18. Attack Techniques & TTPs

### 18.1 MITRE ATT&CK — Network-Relevant TTPs

```
Initial Access:
  T1190 — Exploit Public-Facing Application
  T1133 — External Remote Services (VPN, RDP)
  T1566 — Phishing (email attachment/link → initial foothold)

Discovery:
  T1046 — Network Service Scanning (nmap)
  T1018 — Remote System Discovery
  T1049 — System Network Connections Discovery (netstat, ss)
  T1016 — System Network Configuration Discovery

Lateral Movement:
  T1021 — Remote Services (SSH, RDP, SMB)
  T1210 — Exploitation of Remote Services

Collection:
  T1040 — Network Sniffing (tcpdump, wireshark)
  T1557 — Adversary-in-the-Middle (ARP poisoning, DNS spoofing)

Command & Control:
  T1071 — Application Layer Protocol (HTTP/S, DNS)
  T1090 — Proxy (SOCKS, multi-hop C2)
  T1572 — Protocol Tunneling (DNS tunnel, ICMP tunnel, HTTP tunnel)
  T1573 — Encrypted Channel (custom protocol over TLS)

Exfiltration:
  T1041 — Exfiltration Over C2 Channel
  T1048 — Exfiltration Over Alternative Protocol (DNS, ICMP)
  T1567 — Exfiltration Over Web Service (cloud storage)
```

### 18.2 Protocol-Level Attack Details

**HTTP Request Smuggling:**
```
Attacker sends:
  POST / HTTP/1.1
  Content-Length: 13  (frontend uses this)
  Transfer-Encoding: chunked  (backend uses this)

  0

  GET /admin HTTP/1.1  ← smuggled request (only backend sees this)
```
Frontend (CDN/WAF) parses by Content-Length, passes everything.
Backend parses by Transfer-Encoding/chunked, sees smuggled GET /admin.
The WAF's inspection of the outer request is bypassed.

Mitigation: Normalize all HTTP requests at proxy, reject ambiguous requests, use HTTP/2 end-to-end (no request smuggling in H2), update HTTP libraries.

**SSL Stripping:**
Attacker intercepts HTTP→HTTPS redirect, maintains HTTP connection to victim while maintaining HTTPS to server. Victim sees HTTP, attacker sees plaintext.

Mitigation: HSTS (HTTP Strict Transport Security) — browser refuses HTTP. HSTS Preload list ensures first visit is HTTPS.

**TLS Downgrade (FREAK, POODLE, BEAST, DROWN):**
Attacker forces negotiation of weak cipher suite. All fixed by disabling affected protocol versions and cipher suites (see TLS section).

**BGP Hijacking** — see Section 8.

**DNS Cache Poisoning** — see Section 6.7.

---

## 19. Threat Model: Network Security

### 19.1 STRIDE Analysis

```
Spoofing:
  Threats: IP spoofing, ARP poisoning, BGP hijacking, DNS spoofing
  Mitigations: rp_filter, DAI, RPKI, DNSSEC, BCP38, mTLS (identity verified)

Tampering:
  Threats: TCP RST injection, BGP route manipulation, MITM packet modification
  Mitigations: TLS/mTLS, TCP-AO, IPsec, DNSSEC, TLS certificate pinning

Repudiation:
  Threats: Attacker denies actions, no audit trail of network events
  Mitigations: VPC Flow Logs, Zeek logs, syslog with integrity (WORM storage)

Information Disclosure:
  Threats: Plaintext protocols, side-channel (timing), traffic analysis
  Mitigations: TLS everywhere, QUIC (encrypted headers), WireGuard, onion routing

Denial of Service:
  Threats: SYN flood, UDP amplification, conntrack exhaustion, BGP CPU exhaustion
  Mitigations: SYN cookies, BCP38, XDP-based filtering, conntrack tuning, rate limiting

Elevation of Privilege:
  Threats: VLAN hopping, ARP poisoning → MITM → session hijack → auth bypass
  Mitigations: 802.1X, PVLAN, DAI, TLS (session bound to cert, not network)
```

### 19.2 Defense-in-Depth Map

```
Layer 1 Physical:    Physical access control, tamper-evident hardware
Layer 2 Data Link:   802.1X, DAI, BPDU Guard, PVLAN, MACSec (802.1AE)
Layer 3 Network:     rp_filter, BCP38, RPKI, IPsec/WireGuard, ACLs
Layer 4 Transport:   TCP-AO, SYN cookies, TLS 1.3 (mTLS), rate limiting
Layer 5-7 App:       WAF, input validation, auth/authz, DLP, SAST/DAST
Cross-cutting:       Logging, monitoring, IDS/IPS, threat intelligence
                     Incident response playbooks, red team exercises
```

---

## 20. Observability & Forensics

### 20.1 Packet Capture

```bash
# tcpdump — essential for debugging and forensics
tcpdump -i eth0 -w capture.pcap         # Capture to file
tcpdump -i eth0 -nn -v                   # Verbose, no name resolution
tcpdump -i eth0 'tcp port 443 and host 10.0.0.1'  # Filtered
tcpdump -i eth0 -G 3600 -w capture_%Y%m%d_%H%M%S.pcap  # Rotate hourly

# Capture on all interfaces (monitoring mode)
tcpdump -i any -w all_traffic.pcap

# tshark (Wireshark CLI) — more powerful filtering/decoding
tshark -i eth0 -Y "http.request.method == POST" -T fields \
    -e http.host -e http.request.uri -e http.file_data

# Capture ring buffer (for forensics — always-on, fixed size)
tcpdump -i eth0 -C 100 -W 20 -w /var/capture/ring.pcap
# -C 100: rotate when file reaches 100MB
# -W 20:  keep max 20 files (2GB total)

# af-packet high-performance capture
tshark -i eth0 -b filesize:102400 -b files:10 \
    --compress-type gzip -w /data/capture.pcap
```

### 20.2 Network Flow Analysis

```bash
# nfdump/nfcapd — NetFlow/IPFIX analysis
nfcapd -w -D -l /var/netflow/          # Collect flows
nfdump -r /var/netflow/nfcapd.current \
    -s record/bytes -n 20              # Top talkers by bytes

nfdump -r /var/netflow/ \
    'dst port 53 and packets > 1000'   # High-volume DNS sources

# GoFlow2 — modern flow collector (sFlow, NetFlow, IPFIX)
# docker run -d netsampler/goflow2 \
#   --transport kafka --kafka.brokers kafka:9092

# eBPF-based flow export (no kernel module needed)
# Cilium Hubble flow exporter
hubble export --output json | \
    jq 'select(.verdict=="DROPPED") | {src: .source, dst: .destination}'
```

### 20.3 Security Monitoring Stack

```
Data sources:
  VPC Flow Logs / Azure NSG Flow Logs / GCP VPC Flow Logs
  Suricata EVE JSON
  Zeek logs
  Falco alerts
  iptables LOG
  DNS query logs
  TLS SNI/certificate logs (from proxy)
  BGP route change events

Collection:
  Fluent Bit / Fluentd → Kafka → Elasticsearch / OpenSearch

Analysis:
  OpenSearch Dashboards / Grafana
  Sigma rules → detection correlation
  SIEM (Splunk, Microsoft Sentinel, Chronicle)

Alerting:
  PagerDuty / OpsGenie for critical alerts
  Slack/Teams for informational
  SOAR (Palo Alto XSOAR) for automated response
```

---

## 21. Compliance & Standards

### 21.1 Network Security Standards

```
Framework       Relevant Network Controls
──────────────────────────────────────────────────────────────────
NIST SP 800-53  AC-17 (Remote Access), SC-7 (Boundary Protection),
                SC-8 (Transmission Confidentiality), SI-3 (Malware)
                SC-5 (Denial-of-Service Protection)

CIS Benchmarks  CIS Linux Benchmark (sysctl hardening)
                CIS AWS Foundations, CIS Azure, CIS GCP

PCI DSS v4.0    Req 1: Network Access Controls (firewall)
                Req 4: Encryption in Transit
                Req 10: Network Activity Logging
                Req 11: Network Vulnerability Scanning, Pen Testing

NIST ZTA        NIST SP 800-207 Zero Trust Architecture

SOC 2 Type II   Network monitoring, encryption, access control

ISO 27001       A.13 (Communications Security)
                A.8.22 (Segregation of Networks)
```

### 21.2 Network Encryption Requirements

```
Data in transit requirements:
  PCI DSS:  TLS 1.2 minimum (1.3 strongly preferred after 2024)
  HIPAA:    Encryption required (standard doesn't specify version)
  FedRAMP:  TLS 1.2+ with FIPS 140-2 validated modules
  GDPR:     "Appropriate" technical measures (TLS 1.3 recommended)
  
FIPS 140-2/140-3 compliance:
  Use OpenSSL with FIPS module, or BoringSSL (Google)
  Avoid ChaCha20-Poly1305 if FIPS required (not FIPS-approved until 140-3)
  AES-256-GCM with P-384 is FIPS-compliant and TLS 1.3 compatible
```

---

## 22. Next 3 Steps & References

### Next 3 Steps

**Step 1 — Implement and audit the Linux network hardening baseline:**
```bash
# Apply all sysctls from Section 2.5
sysctl -p /etc/sysctl.d/99-network-security.conf

# Audit current state with Lynis
lynis audit system --tests-from-group networking

# Verify iptables/nftables state matches policy
nft list ruleset | sha256sum   # Baseline hash; detect drift
iptables-save | sha256sum
```

**Step 2 — Deploy Cilium with Hubble and establish default-deny NetworkPolicy:**
```bash
# Install Cilium with strict mTLS and WireGuard
helm install cilium cilium/cilium \
    --namespace kube-system \
    --set encryption.enabled=true \
    --set encryption.type=wireguard \
    --set hubble.enabled=true \
    --set hubble.relay.enabled=true \
    --set kubeProxyReplacement=strict

# Apply default-deny namespace policies (Section 14.3)
kubectl apply -f default-deny-all.yaml

# Observe dropped flows and build allowlist
hubble observe --verdict DROPPED --follow
```

**Step 3 — Deploy Suricata in IDS mode with Emerging Threats ruleset + integrate with SIEM:**
```bash
# Deploy Suricata on edge nodes
suricata-update update-sources && suricata-update enable-source et/open
suricata-update && systemctl restart suricata

# Ship EVE JSON to Elasticsearch
# /etc/filebeat/filebeat.yml
# filebeat.inputs:
#   - type: log
#     paths: [/var/log/suricata/eve.json]
#     json.keys_under_root: true

# Build Kibana/OpenSearch dashboard:
# - Alerts by severity and signature
# - Top source IPs for alerts
# - DNS anomalies (volume, NXDOMAIN rate)
# - TLS validation failures
```

---

### References

**RFCs:**
- RFC 791 — Internet Protocol (IPv4)
- RFC 793 — Transmission Control Protocol
- RFC 2460 — IPv6
- RFC 2328 — OSPF v2
- RFC 4271 — BGP-4
- RFC 4301 — IPsec Architecture
- RFC 4861 — IPv6 Neighbor Discovery
- RFC 5925 — TCP Authentication Option
- RFC 6480 — RPKI
- RFC 7296 — IKEv2
- RFC 7348 — VXLAN
- RFC 7858 — DNS over TLS
- RFC 8446 — TLS 1.3
- RFC 8926 — Geneve
- RFC 9000 — QUIC

**Books:**
- *TCP/IP Illustrated Vol 1 & 2* — Stevens
- *The Linux Kernel Networking* — Rami Rosen
- *Network Security Through Data Analysis* — Collins
- *BGP: Building Reliable Networks* — Halabi
- *The Art of Network Penetration Testing* — Diquet

**Standards & Frameworks:**
- NIST SP 800-207 (Zero Trust Architecture)
- NIST SP 800-53 Rev 5
- CIS Benchmarks (Linux, cloud platforms)
- MITRE ATT&CK Framework (https://attack.mitre.org)
- BCP 38 (RFC 2827) — Network Ingress Filtering
- RPKI Deployment Guide: https://rpki.readthedocs.io

**Tools & Projects:**
- Suricata IDS/IPS: https://suricata.io
- Zeek Network Monitor: https://zeek.org
- Cilium (eBPF CNI): https://cilium.io
- SPIRE (SPIFFE): https://spiffe.io
- FRRouting: https://frrouting.org
- Aya (Rust eBPF): https://aya-rs.dev
- bpftool: https://github.com/libbpf/bpftool
- WireGuard: https://wireguard.com
- strongSwan (IPsec): https://strongswan.org
- BGPalerter: https://github.com/nttgin/BGPalerter
- Falco: https://falco.org

**Research Papers:**
- "The MITRE ATT&CK Framework" — Strom et al.
- "eBPF: Rethinking the Linux Kernel" — Gregg
- "Maglev: A Fast and Reliable Software Network Load Balancer" — Eisenbud et al. (Google)
- "QUIC: A UDP-Based Multiplexed and Secure Transport" — Iyengar, Thomson
- "BGP Security in Partial Deployment" — RFC 7115

I'll build this as a comprehensive `.md` reference — writing it in sections given the depth. This will be a large, production-grade guide.**~3,200 lines / ~120KB** of dense, production-grade reference material. Here's what's covered across 22 sections:

**Linux Kernel Stack** — `sk_buff` internals, the full RX/TX path from NAPI poll to socket delivery, every security-critical sysctl with justification (rp_filter deep dive, SYN cookies, RA suppression), and `SO_REUSEPORT` hijacking risk.

**Netfilter / iptables / nftables** — Hook priority table, conntrack state machine and exhaustion attacks, a full hardened iptables ruleset with egress filtering, and a production nftables ruleset with atomic updates, bogon sets, TCP flag anomaly dropping (XMAS/NULL scan detection).

**eBPF & XDP** — sk_buff vs XDP tradeoffs with exact pps benchmarks (2M→40M pps), Rust/aya XDP blocklist example, TC BPF and BPF-LSM patterns, verifier CVEs and mitigations (`unprivileged_bpf_disabled=1`).

**Network Namespaces** — veth pair mechanics, `br_netfilter` security implications for Kubernetes, OVS fail-mode security.

**Protocol Internals** — ARP/NDP poisoning mechanics with mitigations, IP fragmentation attacks, TCP state machine attacks (RST injection, TIME_WAIT assassination), UDP amplification table (Memcached 50,000x), DNS tunneling detection, TLS 1.3 handshake with deployment checklist, QUIC security model.

**Routing & BGP** — FIB/PBR/VRF, OSPF authentication and MaxAge LSA attack, BGP hijacking taxonomy (Pakistan Telecom/China Telecom cases), RPKI ROV with FRRouting config, BGPsec, TCP-AO, prefix filtering with bogon list, RTBH for DDoS.

**Cloud** — AWS VPC (SG vs NACL comparison, PrivateLink, Shield), Azure VNet (NSG, Azure Firewall FQDN filtering), GCP VPC (global model, SA-based firewall rules, VPC Service Controls, Cloud Armor rate limiting), VXLAN/Geneve internals with security gaps.

**Zero Trust / K8s / Service Mesh** — SPIFFE/SPIRE workload identity, Cilium L7 NetworkPolicy (HTTP method/path), Istio strict mTLS + AuthorizationPolicy, Hubble observability commands.

**Next 3 Steps** are immediately actionable: sysctl hardening audit → Cilium + WireGuard encryption deployment → Suricata with ET ruleset → SIEM integration.