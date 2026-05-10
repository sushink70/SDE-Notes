# Network Security: A Complete Engineering Reference

> **Audience**: Senior systems/security engineers  
> **Scope**: Linux kernel networking, protocol stacks, routing/switching, cloud security, C and Rust implementations  
> **Philosophy**: Security-by-design, first-principles, production-grade trade-offs  
> **Last reviewed against**: Linux 6.x kernel, Rust 1.78+, AWS/Azure/GCP 2024–2025

---

## Table of Contents

1. [Mental Model: The Threat Landscape](#1-mental-model-the-threat-landscape)
2. [OSI / TCP-IP Model — Security at Every Layer](#2-osi--tcp-ip-model--security-at-every-layer)
3. [Linux Kernel Networking Stack — Deep Dive](#3-linux-kernel-networking-stack--deep-dive)
4. [Packet Lifecycle: sk_buff to Userspace](#4-packet-lifecycle-sk_buff-to-userspace)
5. [Netfilter, iptables, nftables](#5-netfilter-iptables-nftables)
6. [eBPF / XDP — Kernel-Bypass Security](#6-ebpf--xdp--kernel-bypass-security)
7. [Network Namespaces and VRFs](#7-network-namespaces-and-vrfs)
8. [TCP/IP Security In Depth](#8-tcpip-security-in-depth)
9. [TLS 1.3 — Protocol, Threat Model, Implementation](#9-tls-13--protocol-threat-model-implementation)
10. [mTLS and Zero Trust Identity](#10-mtls-and-zero-trust-identity)
11. [DNS Security (DNSSEC, DoH, DoT)](#11-dns-security-dnssec-doh-dot)
12. [BGP Security (RPKI, Route Filtering)](#12-bgp-security-rpki-route-filtering)
13. [Routing and Switching Security](#13-routing-and-switching-security)
14. [Firewalls: Architecture and Design](#14-firewalls-architecture-and-design)
15. [Network Intrusion Detection and Prevention](#15-network-intrusion-detection-and-prevention)
16. [DDoS: Attack Taxonomy and Mitigation](#16-ddos-attack-taxonomy-and-mitigation)
17. [VPN: IPsec, WireGuard, Architecture](#17-vpn-ipsec-wireguard-architecture)
18. [Zero Trust Network Architecture (ZTNA)](#18-zero-trust-network-architecture-ztna)
19. [Cloud Network Security — AWS](#19-cloud-network-security--aws)
20. [Cloud Network Security — Azure](#20-cloud-network-security--azure)
21. [Cloud Network Security — GCP](#21-cloud-network-security--gcp)
22. [Kubernetes Network Security](#22-kubernetes-network-security)
23. [Service Mesh Security (Envoy/Istio)](#23-service-mesh-security-envoyistio)
24. [C Implementations: Raw Socket Security Tools](#24-c-implementations-raw-socket-security-tools)
25. [Rust Implementations: Network Security Libraries](#25-rust-implementations-network-security-libraries)
26. [Threat Modeling: STRIDE per Layer](#26-threat-modeling-stride-per-layer)
27. [Testing, Fuzzing, Benchmarking](#27-testing-fuzzing-benchmarking)
28. [Production Hardening Checklist](#28-production-hardening-checklist)
29. [References](#29-references)

---

## 1. Mental Model: The Threat Landscape

### 1.1 Attack Surface Decomposition

Network security is not a product — it is a **property of a system**. Every byte that traverses a network boundary is a potential attack vector. The goal is to reason about each boundary, what trust is extended across it, and what happens when that trust is violated.

```
Attack Surface = sum(
    exposed_interfaces,
    protocol_parsers,
    authentication_boundaries,
    encryption_gaps,
    side_channels,
    trust_relationships
)
```

### 1.2 Core Security Properties

| Property | Definition | Network Mechanism |
|---|---|---|
| **Confidentiality** | Data not readable by unauthorized parties | TLS, IPsec, VPN, encryption at rest |
| **Integrity** | Data not tampered with in transit | HMAC, authenticated encryption (AEAD), signatures |
| **Availability** | Service reachable by authorized parties | Rate limiting, DDoS mitigation, redundancy |
| **Authentication** | Proving identity of communicating parties | mTLS, SPIFFE/SPIRE, Kerberos, 802.1X |
| **Authorization** | Enforcing what authenticated parties may do | ACLs, RBAC, NetworkPolicy, firewall rules |
| **Non-repudiation** | Proof of communication occurred | Audit logs, signed certificates, DNSSEC |

### 1.3 Attacker Capability Model

```
Passive Attacker:
  - On-path (MITM position): can read all plaintext, replay, inject
  - Off-path: can send spoofed packets, cannot read responses

Active Attacker (On-path):
  - Intercept, modify, replay, drop, delay any packet
  - Can terminate TLS if no certificate pinning / proper PKI

State-Level Attacker:
  - BGP hijacking capability
  - CA compromise
  - Hardware supply chain
  - Pervasive traffic analysis
```

### 1.4 Defense-in-Depth Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Physical Layer                            │
│  Cable security, optical tap detection, physical access      │
├─────────────────────────────────────────────────────────────┤
│                    Data Link (L2)                            │
│  802.1X port auth, VLAN segmentation, storm control          │
├─────────────────────────────────────────────────────────────┤
│                    Network (L3)                              │
│  ACLs, uRPF, BGP/RPKI, firewall, NAT, IPsec                  │
├─────────────────────────────────────────────────────────────┤
│                    Transport (L4)                            │
│  TCP hardening, stateful inspection, SYN cookies             │
├─────────────────────────────────────────────────────────────┤
│                    Session/TLS (L5-6)                        │
│  TLS 1.3, mTLS, certificate transparency, HSTS               │
├─────────────────────────────────────────────────────────────┤
│                    Application (L7)                          │
│  WAF, input validation, protocol-aware inspection            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. OSI / TCP-IP Model — Security at Every Layer

### 2.1 Layered Protocol Stack

```
OSI Model          TCP/IP Model     PDU          Security Controls
─────────────────────────────────────────────────────────────────
7. Application   ┐                 Data         WAF, AppFW, DLP
6. Presentation  ├─ Application    Data         TLS, encoding checks
5. Session       ┘                 Data         mTLS, session tokens
4. Transport       Transport       Segment      TCP hardening, QUIC
3. Network         Internet        Packet       ACL, BGP/RPKI, IPsec
2. Data Link       Link            Frame        802.1X, MACsec, VLAN
1. Physical        Physical        Bits         Physical security, TEMPEST
```

### 2.2 Security Relevance Per Layer

**Layer 1 (Physical)**
- Fiber taps are passive and undetectable without optical power monitoring
- Hardware keyloggers, rogue network taps
- Mitigation: optical tap detection, physical access control, TEMPEST shielding for classified environments

**Layer 2 (Data Link)**
- ARP spoofing: attacker poisons ARP cache to redirect L2 frames
- MAC flooding: overflows CAM table, switch degrades to hub behavior
- VLAN hopping: double-tagging or switch spoofing to escape VLAN isolation
- STP manipulation: attacker becomes root bridge, intercepts traffic
- Mitigation: Dynamic ARP Inspection (DAI), port security, BPDU guard, private VLANs, MACsec (802.1AE)

**Layer 3 (Network)**
- IP spoofing: forge source IP to bypass ACLs, amplify reflection attacks
- ICMP attacks: redirect, unreachable floods, Smurf amplification
- Fragmentation attacks: overlapping fragments bypass IDS, reassembly bombs
- BGP hijacking: advertise more-specific prefixes to steal/intercept traffic
- Mitigation: uRPF (Unicast Reverse Path Forwarding), RPKI, route filters, BCP38

**Layer 4 (Transport)**
- SYN flood: exhaust connection state table
- TCP session hijacking: predict/observe sequence numbers
- UDP amplification: DNS/NTP/SSDP reflection DDoS
- Port scanning: information gathering
- Mitigation: SYN cookies, TCP authentication option (TCP-AO), stateful firewall, rate limiting

**Layer 7 (Application)**
- Protocol-specific parsing bugs (HTTP smuggling, DNS cache poisoning)
- Injection attacks, deserialization
- Mitigation: WAF, strict protocol validation, content security policies

---

## 3. Linux Kernel Networking Stack — Deep Dive

### 3.1 Architecture Overview

```
User Space
  │  socket(), send(), recv(), etc.
  │  System calls
  ▼
──────────────────────────────────────────────────────────────
Kernel Space

  ┌─────────────────────────────────────────────────────────┐
  │  Socket Layer (SOCK_STREAM, SOCK_DGRAM, SOCK_RAW)        │
  │  struct socket, struct sock, protocol-specific ops       │
  └─────────────────────────┬───────────────────────────────┘
                             │
  ┌─────────────────────────▼───────────────────────────────┐
  │  Protocol Layer (TCP, UDP, ICMP, SCTP, QUIC via UDP)     │
  │  tcp_sendmsg(), udp_sendmsg(), ip_output()               │
  └─────────────────────────┬───────────────────────────────┘
                             │
  ┌─────────────────────────▼───────────────────────────────┐
  │  IP Layer (IPv4/IPv6)                                    │
  │  ip_rcv(), ip_forward(), ip_output(), ip_route_*()       │
  │  Netfilter hooks: PREROUTING, FORWARD, POSTROUTING       │
  │                   INPUT, OUTPUT                          │
  └─────────────────────────┬───────────────────────────────┘
                             │
  ┌─────────────────────────▼───────────────────────────────┐
  │  Routing Subsystem (FIB - Forwarding Information Base)   │
  │  ip_fib_main, ECMP, policy routing (multiple tables)     │
  │  struct rtable, struct fib_result                        │
  └─────────────────────────┬───────────────────────────────┘
                             │
  ┌─────────────────────────▼───────────────────────────────┐
  │  Network Device Layer                                    │
  │  struct net_device, NAPI polling, GRO, GSO, TSO          │
  └─────────────────────────┬───────────────────────────────┘
                             │
  ┌─────────────────────────▼───────────────────────────────┐
  │  XDP (eXpress Data Path)                                 │
  │  Runs at driver level, before sk_buff allocation         │
  │  Actions: XDP_PASS, XDP_DROP, XDP_TX, XDP_REDIRECT       │
  └─────────────────────────┬───────────────────────────────┘
                             │
  NIC Driver (mlx5, ixgbe, virtio-net, etc.)
──────────────────────────────────────────────────────────────
Hardware (NIC, RDMA, SmartNIC/DPU)
```

### 3.2 sk_buff (Socket Buffer) — The Core Data Structure

Every packet in the Linux kernel is represented as an `sk_buff`. Understanding this structure is essential for writing kernel network code and eBPF programs.

```c
struct sk_buff {
    /* Pointers to data */
    unsigned char   *head;      // start of allocated buffer
    unsigned char   *data;      // start of packet data
    unsigned char   *tail;      // end of packet data
    unsigned char   *end;       // end of allocated buffer

    /* Length fields */
    unsigned int    len;        // total packet length
    unsigned int    data_len;   // paged data length
    __u16           mac_len;    // length of MAC header
    __u16           hdr_len;    // writable header length of cloned skb

    /* Transport/network/mac headers (offsets from head) */
    sk_buff_data_t  transport_header;
    sk_buff_data_t  network_header;
    sk_buff_data_t  mac_header;

    /* Checksums */
    __wsum          csum;
    __u8            ip_summed;      // checksum validation status
    __u8            csum_valid;

    /* Routing */
    struct dst_entry *dst;          // routing decision cache

    /* Netfilter */
    __u32           nfmark;
    __u8            pkt_type;       // PACKET_HOST, MULTICAST, etc.

    /* Timestamps, priority, queue */
    ktime_t         tstamp;
    __u32           priority;

    /* Connection tracking */
    struct nf_conntrack *nfct;

    /* Security: secmark, connmark */
    __u32           secmark;
};
```

Key operations:
```c
// Access headers (compile-time safe)
struct iphdr *ip_hdr(const struct sk_buff *skb);
struct tcphdr *tcp_hdr(const struct sk_buff *skb);
struct ethhdr *eth_hdr(const struct sk_buff *skb);

// Push/pull data (for encap/decap)
void *skb_push(struct sk_buff *skb, unsigned int len);
void *skb_pull(struct sk_buff *skb, unsigned int len);
void *skb_put(struct sk_buff *skb, unsigned int len);

// Clone vs copy
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t priority);
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t priority);
```

### 3.3 Netfilter Hook Architecture

Netfilter is the framework underlying iptables, nftables, conntrack, and NAT. It inserts hooks at five points in the packet path:

```
INGRESS (NIC → kernel, after driver, before IP)
  │
  ▼
┌─────────────────────────────────────────────────────┐
│  NF_INET_PRE_ROUTING                                 │
│  iptables: PREROUTING chain                          │
│  Used for: DNAT, connection tracking, raw table      │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Routing Decision  │
         └─────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼ (for-this-host)     ▼ (forward)
┌───────────────┐    ┌────────────────────┐
│ NF_INET_INPUT │    │ NF_INET_FORWARD    │
│ iptables:     │    │ iptables:          │
│ INPUT chain   │    │ FORWARD chain      │
└───────┬───────┘    └──────────┬─────────┘
        │                       │
        ▼                       │
   [Socket/App]                 │
        │                       │
        ▼                       │
┌───────────────┐               │
│NF_INET_OUTPUT │               │
│iptables:      │               │
│OUTPUT chain   │               │
└───────┬───────┘               │
        └───────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │ NF_INET_POST_ROUTING │
         │ iptables:            │
         │ POSTROUTING chain    │
         │ Used for: SNAT/MASQ  │
         └──────────────────────┘
                    │
                    ▼
               [Wire / NIC]
```

Hook registration example (kernel module):
```c
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>

static unsigned int my_nf_hook(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph;
    
    if (!skb) return NF_ACCEPT;
    
    iph = ip_hdr(skb);
    if (!iph) return NF_ACCEPT;
    
    /* Example: drop packets from a specific source */
    if (iph->saddr == htonl(0xC0A80001)) { /* 192.168.0.1 */
        return NF_DROP;
    }
    
    return NF_ACCEPT;
}

static struct nf_hook_ops my_nf_ops = {
    .hook     = my_nf_hook,
    .pf       = PF_INET,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};

static int __init my_nf_init(void) {
    return nf_register_net_hook(&init_net, &my_nf_ops);
}
```

### 3.4 Connection Tracking (conntrack)

Conntrack maintains a state table for every tracked connection. This is how stateful firewalling works in Linux.

```
conntrack states:
  NEW        - first packet of a connection (SYN for TCP)
  ESTABLISHED- reply seen, connection is active
  RELATED    - related connection (FTP data, ICMP errors)
  INVALID    - doesn't match any known connection, bad state
  UNTRACKED  - explicitly excluded from tracking (via raw table NOTRACK)
  SNAT       - source NAT applied
  DNAT       - destination NAT applied
```

```bash
# View conntrack table
conntrack -L
conntrack -L --proto tcp --state ESTABLISHED

# Show conntrack statistics per CPU
conntrack -S

# Conntrack table limits (tune for high-connection servers)
sysctl net.netfilter.nf_conntrack_max          # default 65536 - increase for high-load
sysctl net.netfilter.nf_conntrack_tcp_timeout_established  # default 432000 (5 days!) - reduce
sysctl net.netfilter.nf_conntrack_tcp_timeout_time_wait    # default 120s
sysctl net.netfilter.nf_conntrack_tcp_timeout_close_wait   # default 60s

# Security: conntrack timeout tuning to prevent table exhaustion
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_recv=30
sysctl -w net.netfilter.nf_conntrack_max=2000000
```

Conntrack tuple structure:
```c
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;    /* source: IP + port/id */
    struct {
        union nf_inet_addr u3;      /* dest IP */
        union {
            __be16 all;
            struct { __be16 port; } tcp;
            struct { __be16 port; } udp;
            struct { u_int8_t type, code; } icmp;
        } u;
        u_int8_t protonum;          /* L4 protocol */
        u_int8_t dir;               /* direction */
    } dst;
};
```

### 3.5 NAPI (New API) — Interrupt Mitigation

NAPI is the modern NIC polling mechanism that prevents interrupt storms at high packet rates, critical for security under DDoS conditions:

```
Without NAPI:
  Each packet → hardware interrupt → context switch → process packet
  At 10 Mpps → 10M interrupts/sec → CPU 100% in interrupt handlers

With NAPI:
  First packet → interrupt → disable interrupts → poll in softirq
  Process up to napi_budget packets before re-enabling interrupts
  If budget exhausted → yield, reschedule
  If no more packets → re-enable interrupts

napi_budget default: 64 packets per poll cycle
```

```c
// NAPI poll function (driver implementation pattern)
int my_driver_poll(struct napi_struct *napi, int budget)
{
    int work_done = 0;
    
    while (work_done < budget) {
        struct sk_buff *skb = rx_ring_get_next_packet();
        if (!skb) break;
        
        napi_gro_receive(napi, skb);  // GRO: coalesce before stack
        work_done++;
    }
    
    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        enable_rx_interrupts();
    }
    
    return work_done;
}
```

### 3.6 TCP Security Hardening — Kernel Parameters

```bash
# SYN flood protection
sysctl -w net.ipv4.tcp_syncookies=1          # SYN cookies (MANDATORY)
sysctl -w net.ipv4.tcp_max_syn_backlog=4096  # Increase SYN backlog
sysctl -w net.ipv4.tcp_synack_retries=2      # Reduce SYNACK retries (default 5)
sysctl -w net.ipv4.tcp_syn_retries=3         # Reduce SYN retries

# TIME_WAIT handling
sysctl -w net.ipv4.tcp_tw_reuse=1            # Reuse TIME_WAIT sockets (safe)
# DO NOT set tcp_tw_recycle - broken with NAT, removed in kernel 4.12

# Idle connection cleanup
sysctl -w net.ipv4.tcp_keepalive_time=600    # Start keepalive after 10min (default 7200s)
sysctl -w net.ipv4.tcp_keepalive_intvl=60    # Keepalive interval
sysctl -w net.ipv4.tcp_keepalive_probes=5    # Drop after 5 failed probes

# Fin timeout (prevents FIN_WAIT2 exhaustion)
sysctl -w net.ipv4.tcp_fin_timeout=15        # Default 60s - aggressive reduction

# TCP sequence number randomization (always on in modern kernels)
# Prevents session hijacking
sysctl net.ipv4.tcp_timestamps=1             # REQUIRED for PAWS (anti-replay)

# Reverse path filtering (anti-spoofing)
sysctl -w net.ipv4.conf.all.rp_filter=1      # Strict mode (mode 2 = loose)
sysctl -w net.ipv4.conf.default.rp_filter=1

# ICMP rate limiting
sysctl -w net.ipv4.icmp_ratelimit=1000       # pps limit for ICMP responses
sysctl -w net.ipv4.icmp_ratemask=88089       # bitmask of ICMP types to rate limit

# Disable source routing (CRITICAL - prevent route manipulation)
sysctl -w net.ipv4.conf.all.accept_source_route=0
sysctl -w net.ipv4.conf.default.accept_source_route=0

# Disable ICMP redirects (prevent routing table manipulation)
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv4.conf.default.accept_redirects=0

# Log martians (packets with impossible source IPs)
sysctl -w net.ipv4.conf.all.log_martians=1

# Disable IP forwarding on non-routers
sysctl -w net.ipv4.ip_forward=0  # set to 1 only on routers/containers

# IPv6 equivalents
sysctl -w net.ipv6.conf.all.accept_redirects=0
sysctl -w net.ipv6.conf.all.accept_source_route=0
sysctl -w net.ipv6.conf.all.forwarding=0

# TCP buffer sizes (for high-bandwidth systems)
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
```

Persist in `/etc/sysctl.d/99-network-security.conf`.

---

## 4. Packet Lifecycle: sk_buff to Userspace

### 4.1 RX Path (Receive — NIC to Socket)

```
1. [Hardware]  DMA: NIC writes packet into pre-allocated ring buffer
2. [Hardware]  NIC raises hardware interrupt (or MSI-X)
3. [Kernel]    ixgbe_msix_clean_rings() → napi_schedule()
4. [Kernel]    net_rx_action() softirq fires
5. [Driver]    napi_poll() → receive descriptor ring
6. [Driver]    Allocate sk_buff (or use XDP before this point)
7. [Driver]    skb->data points to packet data in DMA memory
8. [Driver]    netif_receive_skb() → deliver to stack
9. [L3]        ip_rcv() → ip_rcv_finish()
               - Validate IP header (checksum, version, length)
               - Netfilter: NF_INET_PRE_ROUTING
               - Routing lookup: ip_route_input()
10.[L3]        If local: ip_local_deliver() → NF_INET_INPUT
11.[L4]        tcp_v4_rcv() / udp_rcv()
               - TCP: lookup sock by (src_ip, src_port, dst_ip, dst_port)
               - Validate sequence numbers, checksums
               - Deliver to receive queue
12.[Socket]    sock_queue_rcv_skb()
13.[Userspace] read()/recv()/recvmsg() copies data from kernel ring buffer

XDP interception point: between step 6 and 7 (driver) or step 8 (generic XDP)
```

### 4.2 TX Path (Transmit — Socket to NIC)

```
1. [App]       write()/send()/sendmsg() syscall
2. [Socket]    tcp_sendmsg() → tcp_push_one()
3. [TCP]       tcp_transmit_skb() → build TCP header, compute checksum
4. [IP]        ip_queue_xmit() → ip_local_out()
               - Routing: ip_route_output()
               - Netfilter: NF_INET_OUTPUT → NF_INET_POST_ROUTING
               - SNAT if configured (ip_nat_out())
5. [L2]        dev_queue_xmit()
               - QDisc (queuing discipline, tc): handle TC/shaping/policing
               - ARP resolution for next-hop MAC
6. [Driver]    Driver TX ring: build descriptor, map DMA
7. [Hardware]  NIC reads descriptor, DMA from memory, transmits
8. [Hardware]  TX completion interrupt
9. [Driver]    Free sk_buff, unmap DMA
```

### 4.3 Zero-Copy and its Security Implications

```
sendfile():
  File → kernel page cache → NIC
  Bypasses userspace copy
  Security risk: data in page cache accessible to other processes
                 with appropriate capabilities

splice():
  pipe → socket without user-kernel copy
  
io_uring with zero-copy send (kernel 6.0+):
  User provides io_uring_sqe with IORING_OP_SEND_ZC
  Kernel registers userspace buffer, DMA directly
  Security: registered buffers must not be modified during DMA
            (temporal safety issue — document ABI contract)

MSG_ZEROCOPY (sendmsg):
  setsockopt(SO_ZEROCOPY)
  Kernel notifies completion via error queue
  Security: completion notification required — not receiving it
            = bug (memory corruption risk)
```

---

## 5. Netfilter, iptables, nftables

### 5.1 iptables Architecture

iptables organizes rules into **tables** (classify by function) and **chains** (classify by hook point):

```
Tables:
  raw      → Connection tracking bypass (highest priority)
  mangle   → Packet modification (TTL, DSCP, marks)
  nat      → Address translation
  filter   → Packet filtering (default table)
  security → SELinux/security context marking

Chains per table:
  raw:      PREROUTING, OUTPUT
  mangle:   PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING
  nat:      PREROUTING, INPUT, OUTPUT, POSTROUTING
  filter:   INPUT, FORWARD, OUTPUT
  security: INPUT, FORWARD, OUTPUT

Processing order at PREROUTING:
  raw → mangle → nat (DNAT) → routing decision

Processing order at INPUT:
  mangle → nat (rare) → filter → security

Default policies: ACCEPT or DROP (for built-in chains)
```

Critical iptables rules for server hardening:
```bash
#!/bin/bash
# Production-grade iptables baseline

IPT="iptables"

# Flush and reset
$IPT -F; $IPT -X; $IPT -Z
$IPT -t nat -F; $IPT -t nat -X
$IPT -t mangle -F; $IPT -t mangle -X
$IPT -t raw -F; $IPT -t raw -X

# Default policies: DROP everything
$IPT -P INPUT DROP
$IPT -P FORWARD DROP
$IPT -P OUTPUT ACCEPT  # adjust to DROP for strict egress filtering

# Allow loopback
$IPT -A INPUT -i lo -j ACCEPT
$IPT -A OUTPUT -o lo -j ACCEPT

# Allow established/related (stateful)
$IPT -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Drop INVALID state packets (prevents TCP state confusion attacks)
$IPT -A INPUT -m conntrack --ctstate INVALID -j DROP

# SYN flood protection
$IPT -A INPUT -p tcp --syn -m limit --limit 25/s --limit-burst 50 -j ACCEPT
$IPT -A INPUT -p tcp --syn -j DROP

# Protect against null packets
$IPT -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Protect against XMAS packets
$IPT -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Protect against SYN-RST (invalid combination)
$IPT -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP

# ICMP: allow echo only, rate limited
$IPT -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT
$IPT -A INPUT -p icmp -j DROP

# Allow SSH (specific source IP recommended)
$IPT -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent \
    --set --name SSH
$IPT -A INPUT -p tcp --dport 22 -m recent --update --seconds 60 \
    --hitcount 4 --name SSH -j DROP
$IPT -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Log and drop everything else
$IPT -A INPUT -m limit --limit 5/min --limit-burst 10 \
    -j LOG --log-prefix "iptables-drop: " --log-level 7
$IPT -A INPUT -j DROP

# Anti-spoofing: drop packets from loopback IPs coming on physical interface
$IPT -A INPUT -i eth0 -s 127.0.0.0/8 -j DROP
$IPT -A INPUT -i eth0 -s 10.0.0.0/8 -j LOG --log-prefix "SPOOF-RFC1918: "

# Save
iptables-save > /etc/iptables/rules.v4
```

### 5.2 nftables — Modern Replacement

nftables is the kernel ≥ 3.13 successor to iptables. It uses a single table structure, supports set operations natively, has atomic rule updates, and avoids the O(n) linear rule scan through use of hash/rbtree maps.

```bash
# nftables basic structure
nft add table inet filter

# Create base chains with hooks
nft add chain inet filter input \
    '{ type filter hook input priority 0; policy drop; }'
nft add chain inet filter forward \
    '{ type filter hook forward priority 0; policy drop; }'
nft add chain inet filter output \
    '{ type filter hook output priority 0; policy accept; }'

# Allow established/related
nft add rule inet filter input \
    ct state established,related accept

# Drop invalid
nft add rule inet filter input \
    ct state invalid drop

# Loopback
nft add rule inet filter input iif lo accept

# ICMP rate limiting
nft add rule inet filter input \
    ip protocol icmp icmp type echo-request \
    limit rate 5/second accept

# SSH with rate limiting using sets (nftables native feature)
nft add set inet filter ssh_ratelimit \
    '{ type ipv4_addr; flags dynamic; timeout 60s; }'

nft add rule inet filter input \
    tcp dport 22 ct state new \
    add @ssh_ratelimit { ip saddr ct count over 3 } drop

nft add rule inet filter input tcp dport 22 ct state new accept

# Blocklist using nft sets (O(1) lookup vs O(n) for iptables)
nft add set inet filter blocklist \
    '{ type ipv4_addr; flags interval; auto-merge; }'
nft add rule inet filter input \
    ip saddr @blocklist drop

# Add IPs to blocklist atomically
nft add element inet filter blocklist \
    { 192.168.100.1, 10.0.0.0/8 }
```

nftables ruleset file (`/etc/nftables.conf`):
```nft
#!/usr/sbin/nft -f

flush ruleset

table inet firewall {
    # Dynamic blocklist (populated by fail2ban or custom tool)
    set blocklist_v4 {
        type ipv4_addr
        flags dynamic, interval
        timeout 1h
        auto-merge
    }

    set blocklist_v6 {
        type ipv6_addr
        flags dynamic, interval
        timeout 1h
        auto-merge
    }

    # Allowed services (uses named ports for clarity)
    set allowed_tcp_ports {
        type inet_service
        elements = { ssh, https, 8443 }
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Blocklist check (O(1) hash lookup)
        ip saddr @blocklist_v4 counter drop
        ip6 saddr @blocklist_v6 counter drop

        # Loopback
        iif "lo" accept

        # Established/related
        ct state established,related accept

        # Invalid
        ct state invalid counter drop

        # ICMP/ICMPv6 - controlled
        ip protocol icmp icmp type {
            echo-request, destination-unreachable,
            time-exceeded, parameter-problem
        } limit rate 10/second accept

        ip6 nexthdr icmpv6 icmpv6 type {
            echo-request, nd-neighbor-solicit,
            nd-neighbor-advert, nd-router-advert,
            destination-unreachable, packet-too-big,
            time-exceeded, parameter-problem
        } accept

        # TCP services from allowed set
        tcp dport @allowed_tcp_ports ct state new \
            meter ssh_limit { ip saddr timeout 60s limit rate 10/minute } \
            accept

        # Log and drop
        limit rate 1/minute log prefix "nft-drop: " level info
        drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        # For routers/gateways only:
        # ct state established,related accept
    }

    chain output {
        type filter hook output priority filter; policy accept;
        # Egress filtering (strict - only allow expected traffic)
    }
}
```

### 5.3 Comparison: iptables vs nftables

| Feature | iptables | nftables |
|---|---|---|
| Rule lookup | O(n) linear scan | O(1) hash/rbtree maps |
| Atomic updates | No (each rule = separate syscall) | Yes (transactions) |
| IPv4/IPv6 | Separate tools (ip6tables) | Unified (`inet` family) |
| Sets/maps | Via ipset (external) | Native, high-performance |
| Scripting | Shell + iptables-restore | Native nft language |
| Kernel support | < 3.13 (legacy) | ≥ 3.13 (default 5.x+) |
| ARP/bridge | arptables/ebtables | Native (arp/bridge families) |
| Performance | Degrades with rule count | Consistent with sets |

---

## 6. eBPF / XDP — Kernel-Bypass Security

### 6.1 eBPF Architecture

eBPF (extended Berkeley Packet Filter) is the most significant networking security technology in the Linux kernel since Netfilter. It allows safely running sandboxed programs in the kernel without writing kernel modules.

```
eBPF Program Types (security-relevant):
  BPF_PROG_TYPE_XDP              → Pre-stack packet processing (NIC level)
  BPF_PROG_TYPE_SCHED_CLS        → tc classifier (ingress/egress shaping)
  BPF_PROG_TYPE_SOCKET_FILTER    → Socket-level filtering (like classic BPF)
  BPF_PROG_TYPE_SK_MSG           → sockmap message redirection
  BPF_PROG_TYPE_SK_SKB           → Stream parser/verdict
  BPF_PROG_TYPE_CGROUP_SKB       → Per-cgroup packet filtering
  BPF_PROG_TYPE_CGROUP_SOCK      → Per-cgroup socket creation control
  BPF_PROG_TYPE_KPROBE           → Kernel function tracing
  BPF_PROG_TYPE_TRACEPOINT       → Static tracepoints
  BPF_PROG_TYPE_LSM              → Linux Security Module hooks
  BPF_PROG_TYPE_FLOW_DISSECTOR   → Custom protocol dissection

Verifier guarantees:
  - No unbounded loops (provably terminates) [relaxed in 5.3+ with bounded loops]
  - No null pointer dereferences (all pointer accesses verified)
  - No out-of-bounds memory access
  - No use-after-free
  - Stack depth ≤ 512 bytes
  - Max instruction count: 1M (kernel 5.2+, was 4096)
```

### 6.2 XDP Program — DDoS Mitigation (C)

```c
// File: xdp_ddos_filter.c
// Compile: clang -O2 -target bpf -c xdp_ddos_filter.c -o xdp_ddos_filter.o
// Load:    ip link set dev eth0 xdp obj xdp_ddos_filter.o sec xdp_filter

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Rate limiting map: src_ip → packet count per second
struct {
    __uint(type, BPF_MAP_TYPE_LRU_PERCPU_HASH);
    __type(key, __u32);           // source IPv4 address
    __type(value, __u64);         // packet count
    __uint(max_entries, 100000);
} src_rate_map SEC(".maps");

// Blocklist: src_ip → 1 (blocked)
struct {
    __uint(type, BPF_MAP_TYPE_LPM_TRIE);
    __type(key, struct {
        __u32 prefixlen;
        __u32 addr;
    });
    __type(value, __u32);
    __uint(max_entries, 10000);
    __uint(map_flags, BPF_F_NO_PREALLOC);
} blocklist SEC(".maps");

// Stats per action
struct xdp_stats {
    __u64 pass;
    __u64 drop;
    __u64 aborted;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, __u32);
    __type(value, struct xdp_stats);
    __uint(max_entries, 1);
} stats_map SEC(".maps");

#define RATE_LIMIT_PPS 1000  // packets per second per source IP
#define NANOSEC_PER_SEC 1000000000ULL

static __always_inline int parse_ethhdr(void *data, void *data_end,
                                          struct ethhdr **eth)
{
    struct ethhdr *e = data;
    if ((void *)(e + 1) > data_end)
        return -1;
    *eth = e;
    return bpf_ntohs(e->h_proto);
}

SEC("xdp_filter")
int xdp_ddos_filter(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;
    
    struct ethhdr *eth;
    int eth_proto = parse_ethhdr(data, data_end, &eth);
    if (eth_proto < 0)
        return XDP_DROP;
    
    // Only handle IPv4 for now
    if (eth_proto != ETH_P_IP)
        return XDP_PASS;
    
    struct iphdr *iph = (struct iphdr *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_DROP;
    
    // Validate IP header length
    if (iph->ihl < 5)
        return XDP_DROP;
    
    __u32 src_ip = iph->saddr;
    
    // Check blocklist (LPM trie for CIDR blocking)
    struct {
        __u32 prefixlen;
        __u32 addr;
    } key = {
        .prefixlen = 32,
        .addr      = src_ip,
    };
    
    if (bpf_map_lookup_elem(&blocklist, &key))
        return XDP_DROP;
    
    // Rate limiting: per-source-IP pps limit
    __u64 *count = bpf_map_lookup_elem(&src_rate_map, &src_ip);
    if (count) {
        __u64 curr = __sync_fetch_and_add(count, 1);
        if (curr > RATE_LIMIT_PPS)
            return XDP_DROP;
    } else {
        __u64 init = 1;
        bpf_map_update_elem(&src_rate_map, &src_ip, &init, BPF_ANY);
    }
    
    // Drop fragments (can be used to evade IDS)
    if (iph->frag_off & bpf_htons(IP_MF | IP_OFFSET))
        return XDP_DROP;
    
    // TCP-specific checks
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcph = (struct tcphdr *)((void *)iph + (iph->ihl * 4));
        if ((void *)(tcph + 1) > data_end)
            return XDP_DROP;
        
        // Drop TCP packets with invalid flag combinations
        // NULL scan (no flags)
        if (!tcph->syn && !tcph->ack && !tcph->fin && 
            !tcph->rst && !tcph->psh && !tcph->urg)
            return XDP_DROP;
        
        // XMAS scan (FIN+PSH+URG)
        if (tcph->fin && tcph->psh && tcph->urg)
            return XDP_DROP;
        
        // SYN+FIN (invalid)
        if (tcph->syn && tcph->fin)
            return XDP_DROP;
    }
    
    // Update stats
    __u32 stats_key = 0;
    struct xdp_stats *s = bpf_map_lookup_elem(&stats_map, &stats_key);
    if (s)
        __sync_fetch_and_add(&s->pass, 1);
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

Loading and managing:
```bash
# Load XDP program (native mode - fastest, driver support required)
ip link set dev eth0 xdpdrv obj xdp_ddos_filter.o sec xdp_filter

# Generic mode (works on any driver, slower)
ip link set dev eth0 xdpgeneric obj xdp_ddos_filter.o sec xdp_filter

# Verify loaded
ip link show dev eth0 | grep xdp

# Using libbpf / bpftool
bpftool prog load xdp_ddos_filter.o /sys/fs/bpf/xdp_ddos
bpftool net attach xdp id $(bpftool prog show name xdp_ddos_filter | awk '{print $1}' | tr -d ':') dev eth0

# Add to blocklist map
bpftool map update pinned /sys/fs/bpf/blocklist_map \
    key 0x20 0x00 0x00 0x00 0xC0 0xA8 0x64 0x01 \  # prefixlen=32, 192.168.100.1
    value 0x01 0x00 0x00 0x00

# View stats
bpftool map dump pinned /sys/fs/bpf/stats_map

# Detach
ip link set dev eth0 xdp off
```

### 6.3 eBPF TC (Traffic Control) for Egress Filtering

XDP only handles ingress. For egress filtering, use TC (traffic control) classifier:

```c
// File: tc_egress_filter.c
// Load: tc qdisc add dev eth0 clsact
//       tc filter add dev eth0 egress bpf obj tc_egress_filter.o sec tc_egress direct-action

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// Denied destination ports
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u16);    // port (host byte order)
    __type(value, __u8);   // 1 = deny
    __uint(max_entries, 1024);
} denied_ports SEC(".maps");

SEC("tc_egress")
int tc_egress_filter(struct __sk_buff *skb)
{
    void *data_end = (void *)(long)skb->data_end;
    void *data     = (void *)(long)skb->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;
    
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return TC_ACT_OK;
    
    struct iphdr *iph = (struct iphdr *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return TC_ACT_SHOT;
    
    if (iph->protocol != IPPROTO_TCP)
        return TC_ACT_OK;
    
    struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
    if ((void *)(tcph + 1) > data_end)
        return TC_ACT_SHOT;
    
    __u16 dst_port = bpf_ntohs(tcph->dest);
    
    if (bpf_map_lookup_elem(&denied_ports, &dst_port))
        return TC_ACT_SHOT;  // drop egress packet
    
    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
```

### 6.4 eBPF LSM (Linux Security Module)

eBPF LSM hooks allow implementing security policies at the kernel security layer without writing a full LSM:

```c
// File: bpf_lsm_net.c
// Requires: CONFIG_BPF_LSM=y, kernel ≥ 5.7
// Boot param: lsm=bpf (or lsm=lockdown,yama,bpf)

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

// Block network socket creation for specific UIDs
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);   // uid
    __type(value, __u8);  // 1 = blocked
    __uint(max_entries, 1000);
} blocked_uids SEC(".maps");

SEC("lsm/socket_create")
int BPF_PROG(socket_create_check, int family, int type,
              int protocol, int kern)
{
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    
    if (bpf_map_lookup_elem(&blocked_uids, &uid)) {
        // Deny socket creation for this UID
        return -EPERM;
    }
    
    return 0;
}

SEC("lsm/socket_connect")
int BPF_PROG(socket_connect_check, struct socket *sock,
              struct sockaddr *address, int addrlen)
{
    // Could inspect address, enforce egress policy per process
    // e.g., deny connections to external IPs from certain processes
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    // ... policy enforcement
    return 0;
}

char _license[] SEC("license") = "GPL";
```

---

## 7. Network Namespaces and VRFs

### 7.1 Network Namespaces — Isolation Primitive

Network namespaces are the fundamental kernel isolation mechanism underlying containers, Kubernetes pods, and virtual routing.

```
Each network namespace has:
  - Independent set of network interfaces
  - Independent routing tables (FIB)
  - Independent iptables/nftables ruleset
  - Independent conntrack table
  - Independent ARP/NDP tables
  - Independent socket table
  - Independent /proc/sys/net/ tunables

Security properties:
  - Process in namespace A cannot see interfaces in namespace B
  - A bug in namespace A's network stack cannot directly corrupt B
  - Each namespace can have its own firewall policy
  
Limitation:
  - Namespaces share the same kernel code paths
  - Spectre/Meltdown-style attacks across namespaces are possible
  - Kernel CVEs affect all namespaces
```

Namespace operations:
```bash
# Create a network namespace
ip netns add secure-ns

# List namespaces
ip netns list

# Execute in namespace
ip netns exec secure-ns ip addr

# Create veth pair (virtual ethernet - connects two namespaces)
ip link add veth0 type veth peer name veth1

# Move veth1 to secure-ns
ip link set veth1 netns secure-ns

# Configure interfaces
ip addr add 192.168.100.1/24 dev veth0
ip link set veth0 up

ip netns exec secure-ns ip addr add 192.168.100.2/24 dev veth1
ip netns exec secure-ns ip link set veth1 up
ip netns exec secure-ns ip link set lo up

# Add default route in namespace
ip netns exec secure-ns ip route add default via 192.168.100.1

# Enable forwarding on host to allow namespace to reach outside
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -j MASQUERADE

# Delete namespace (and all its interfaces)
ip netns del secure-ns
```

### 7.2 Namespace in Code (Rust)

```rust
// File: src/netns.rs
// Creates isolated network namespace for sandboxing

use std::fs::{self, File};
use std::io;
use std::os::unix::io::AsRawFd;
use nix::sched::{unshare, CloneFlags};
use nix::sys::socket::{socket, AddressFamily, SockType, SockFlag};

/// Create a new isolated network namespace
/// 
/// # Safety
/// Must be called in a single-threaded context before forking,
/// or in a dedicated thread. Calling unshare in a multi-threaded
/// process is generally unsafe.
pub fn isolate_network() -> io::Result<()> {
    // Create new network namespace for this process
    unshare(CloneFlags::CLONE_NEWNET)
        .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
    
    // At this point, process has only the loopback interface
    // No connectivity to external network
    Ok(())
}

/// Bind to a named network namespace
pub fn enter_netns(ns_name: &str) -> io::Result<()> {
    let ns_path = format!("/var/run/netns/{}", ns_name);
    let ns_file = File::open(&ns_path)?;
    
    // setns: join existing namespace via file descriptor
    let ret = unsafe {
        libc::setns(ns_file.as_raw_fd(), libc::CLONE_NEWNET)
    };
    
    if ret != 0 {
        return Err(io::Error::last_os_error());
    }
    
    Ok(())
}
```

### 7.3 VRF (Virtual Routing and Forwarding)

VRFs provide routing table isolation without full network namespace isolation. Multiple routing tables coexist in a single network namespace, allowing traffic separation:

```bash
# Create VRF device
ip link add vrf-blue type vrf table 10
ip link set vrf-blue up

# Assign interface to VRF
ip link set eth1 master vrf-blue

# Routes in VRF table 10 are isolated from main table
ip route add 10.0.0.0/8 via 10.1.1.1 vrf vrf-blue
ip route show vrf vrf-blue

# Socket binding to VRF
# Sockets must explicitly bind to VRF device to use VRF routing
# SO_BINDTODEVICE: bind socket to specific VRF
setsockopt(fd, SOL_SOCKET, SO_BINDTODEVICE, "vrf-blue", 9)

# Kernel VRF strict mode (v6 only by default, tune v4):
sysctl -w net.ipv4.tcp_l3mdev_accept=1    # Allow VRF-bound servers
sysctl -w net.ipv4.udp_l3mdev_accept=1
sysctl -w net.ipv4.raw_l3mdev_accept=1
```

Security use case: Multi-tenant routing isolation — tenant A's traffic cannot reach tenant B's routing table even if there's a routing misconfiguration.

---

## 8. TCP/IP Security In Depth

### 8.1 TCP State Machine and Attack Surface

```
TCP State Machine:

CLOSED ──SYN sent──► SYN_SENT ──SYN-ACK rcvd──► ESTABLISHED
                                                        │
         passive open                               FIN sent
              │                                         │
           LISTEN ──SYN rcvd──► SYN_RECEIVED ──ACK──► ESTABLISHED
                                                        │
                                                    FIN sent
                                                        │
                                                   FIN_WAIT_1 ──FIN rcvd──► CLOSING ──ACK──► TIME_WAIT
                                                        │
                                                    ACK rcvd
                                                        │
                                                   FIN_WAIT_2 ──FIN rcvd──► TIME_WAIT (2MSL) ──► CLOSED

Attack vectors per state:
  LISTEN:      SYN flood → SYN_RECEIVED table overflow
  SYN_SENT:    RST injection (sequence prediction)
  ESTABLISHED: RST injection, data injection, ACK storm
  TIME_WAIT:   TIME_WAIT assassination (RFC 1337 describes the attack)
               Prevented by: net.ipv4.tcp_rfc1337=1
```

### 8.2 TCP Sequence Number Security

Modern kernels use cryptographically random ISNs (Initial Sequence Numbers):

```c
// From Linux kernel: net/ipv4/tcp_ipv4.c
// ISN generation using SipHash (kernel ≥ 4.x)
u32 secure_tcp_seq(__be32 saddr, __be32 daddr,
                   __be16 sport, __be16 dport)
{
    u32 hash;
    net_secret_init();
    hash = siphash_4u32((__force u32)saddr, (__force u32)daddr,
                        (__force u32)sport << 16 | (__force u32)dport,
                        net_secret[1], &net_secret_key);
    return seq_scale(hash);
}
```

The ISN includes a time component (`seq_scale`) and a keyed hash, preventing blind sequence number prediction.

### 8.3 TCP Authentication Option (TCP-AO) — RFC 5925

TCP-AO replaces TCP MD5 signatures, providing per-segment authentication:

```c
// Configure TCP-AO for BGP session authentication
// Using iproute2 / ss tools (requires kernel ≥ 5.14)

// Key configuration structure (from linux/tcp.h)
struct tcp_ao_add {
    struct sockaddr_storage addr;  // peer address
    char     alg_name[64];         // "cmac(aes128)" or "hmac(sha1)"
    __s32    ifindex;
    __u32    set_current  : 1,
             set_rnext    : 1,
             reserved     : 30;
    __u16    reserved2;
    __u8     prefix;               // prefix length for peer address
    __u8     sndid;                // key ID for sent segments
    __u8     rcvid;                // key ID expected on received segments  
    __u8     maclen;               // MAC length (default 12)
    __u8     keyflags;
    __u8     keylen;
    __u8     key[TCP_AO_MAXKEYLEN];
};
```

### 8.4 Raw TCP Implementation (C) — Three-Way Handshake with Security

```c
// File: tcp_raw_secure.c
// Demonstrates raw socket TCP with security validation
// Compile: gcc -O2 -o tcp_raw_secure tcp_raw_secure.c
// Run: sudo ./tcp_raw_secure (requires CAP_NET_RAW)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define TARGET_IP   "192.168.1.1"
#define TARGET_PORT 80
#define SOURCE_IP   "192.168.1.100"
#define SOURCE_PORT 54321

// Pseudo-header for TCP checksum calculation
struct pseudo_header {
    uint32_t source_addr;
    uint32_t dest_addr;
    uint8_t  placeholder;
    uint8_t  protocol;
    uint16_t tcp_length;
};

// Compute Internet checksum (RFC 1071)
static uint16_t checksum(void *buf, int len)
{
    uint16_t *ptr = (uint16_t *)buf;
    uint32_t sum = 0;
    
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }
    
    if (len == 1)
        sum += *(uint8_t *)ptr;
    
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    
    return (uint16_t)(~sum);
}

// Build and compute TCP checksum over pseudo-header
static uint16_t tcp_checksum(struct iphdr *iph, struct tcphdr *tcph,
                               uint8_t *data, int data_len)
{
    int tcp_len = sizeof(struct tcphdr) + data_len;
    
    struct pseudo_header psh = {
        .source_addr = iph->saddr,
        .dest_addr   = iph->daddr,
        .placeholder = 0,
        .protocol    = IPPROTO_TCP,
        .tcp_length  = htons(tcp_len),
    };
    
    int total_len = sizeof(struct pseudo_header) + tcp_len;
    uint8_t *buf = calloc(1, total_len);
    if (!buf) return 0;
    
    memcpy(buf, &psh, sizeof(psh));
    memcpy(buf + sizeof(psh), tcph, sizeof(struct tcphdr));
    if (data && data_len > 0)
        memcpy(buf + sizeof(psh) + sizeof(struct tcphdr), data, data_len);
    
    uint16_t csum = checksum(buf, total_len);
    free(buf);
    return csum;
}

// Forge a TCP SYN packet (demonstration only)
// In production: use proper socket API, never forge packets on live network
static int forge_syn(int raw_sock, const char *src_ip, uint16_t src_port,
                      const char *dst_ip, uint16_t dst_port, uint32_t seq)
{
    uint8_t packet[sizeof(struct iphdr) + sizeof(struct tcphdr)];
    memset(packet, 0, sizeof(packet));
    
    struct iphdr  *iph  = (struct iphdr *)packet;
    struct tcphdr *tcph = (struct tcphdr *)(packet + sizeof(struct iphdr));
    
    // IP header
    iph->ihl      = 5;
    iph->version  = 4;
    iph->tos      = 0;
    iph->tot_len  = htons(sizeof(packet));
    iph->id       = htons(12345);
    iph->frag_off = 0;
    iph->ttl      = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr    = inet_addr(src_ip);
    iph->daddr    = inet_addr(dst_ip);
    iph->check    = 0;
    iph->check    = checksum(iph, sizeof(struct iphdr));
    
    // TCP header
    tcph->source  = htons(src_port);
    tcph->dest    = htons(dst_port);
    tcph->seq     = htonl(seq);
    tcph->ack_seq = 0;
    tcph->doff    = 5;    // header length in 32-bit words
    tcph->syn     = 1;
    tcph->window  = htons(65535);
    tcph->check   = 0;
    tcph->check   = tcp_checksum(iph, tcph, NULL, 0);
    
    struct sockaddr_in dst = {
        .sin_family = AF_INET,
        .sin_port   = tcph->dest,
        .sin_addr.s_addr = iph->daddr,
    };
    
    ssize_t sent = sendto(raw_sock, packet, sizeof(packet), 0,
                           (struct sockaddr *)&dst, sizeof(dst));
    if (sent < 0) {
        perror("sendto");
        return -1;
    }
    
    return 0;
}

int main(void)
{
    // CAP_NET_RAW required
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (sock < 0) {
        perror("socket");
        fprintf(stderr, "Need CAP_NET_RAW capability\n");
        return 1;
    }
    
    // Tell kernel we provide IP header
    int one = 1;
    if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        perror("setsockopt IP_HDRINCL");
        close(sock);
        return 1;
    }
    
    // In real usage, use cryptographically random sequence number
    // arc4random_buf() or getrandom() syscall
    uint32_t isn;
    if (getrandom(&isn, sizeof(isn), GRND_NONBLOCK) != sizeof(isn)) {
        perror("getrandom");
        close(sock);
        return 1;
    }
    
    printf("ISN: 0x%08x\n", isn);
    forge_syn(sock, SOURCE_IP, SOURCE_PORT, TARGET_IP, TARGET_PORT, isn);
    
    close(sock);
    return 0;
}
```

---

## 9. TLS 1.3 — Protocol, Threat Model, Implementation

### 9.1 TLS 1.3 Handshake — One Round Trip

```
Client                                              Server
──────                                              ──────
ClientHello
  - supported versions: [TLS 1.3]
  - random (32 bytes)
  - session_id (legacy compat)
  - cipher_suites: [TLS_AES_256_GCM_SHA384,
                    TLS_CHACHA20_POLY1305_SHA256,
                    TLS_AES_128_GCM_SHA256]
  - extensions:
      supported_groups: [x25519, secp256r1]
      key_share: [x25519 public key]
      signature_algorithms: [ecdsa_secp256r1_sha256, rsa_pss_rsae_sha256]
      server_name: "api.example.com"   (SNI)
      alpn: ["h2", "http/1.1"]
  ──────────────────────────────────────────────────►
                                         ServerHello
                                           - version: TLS 1.3
                                           - random (32 bytes)
                                           - key_share: x25519 public key
                                           - cipher: TLS_AES_256_GCM_SHA384
                                         {EncryptedExtensions}
                                         {CertificateRequest} (if mTLS)
                                         {Certificate}
                                         {CertificateVerify}
                                           - signature over transcript hash
                                         {Finished}
                                           - HMAC over transcript
  ◄──────────────────────────────────────────────────
{Certificate} (if mTLS requested)
{CertificateVerify}
{Finished}
  ──────────────────────────────────────────────────►
[Application Data] (encrypted)  ◄─────────────────► [Application Data]

Key derivation (HKDF):
  early_secret  = HKDF-Extract(0, PSK)  [0 if no PSK]
  ↓ HKDF-Expand-Label
  handshake_secret = HKDF-Extract(ECDHE_shared_secret, Derive(early_secret))
  ↓ HKDF-Expand-Label  
  master_secret = HKDF-Extract(0, Derive(handshake_secret))
  ↓
  client_write_key, server_write_key, client_write_iv, server_write_iv
```

### 9.2 TLS Security Properties

| Property | TLS 1.2 | TLS 1.3 |
|---|---|---|
| Forward Secrecy | Optional (depends on cipher) | Mandatory (ECDHE always) |
| 0-RTT | No | Yes (but has replay risks) |
| Downgrade protection | Limited | Canary values in ServerHello |
| Encrypted handshake | Partially | Certificate/CertVerify encrypted |
| Weak ciphers | RSA key exchange, RC4, DES | All removed |
| Round trips | 2-RTT (1-RTT with session resumption) | 1-RTT (0-RTT with PSK) |
| AEAD only | No (CBC allowed) | Yes (mandatory AEAD) |

### 9.3 TLS 0-RTT — Security Considerations

```
0-RTT (Early Data) Risk: REPLAY ATTACKS

Client sends early data before handshake completes.
A network attacker can record and replay this early data.

0-RTT safe uses:
  - Idempotent GET requests
  - Read-only API calls
  - Fetching public resources

0-RTT UNSAFE uses:
  - Any state-changing operation (POST, PUT, DELETE)
  - Financial transactions
  - Authentication requests

Mitigation:
  - Server anti-replay (at cost of state: deduplication cache)
  - Application-level idempotency keys
  - Mark 0-RTT data separately at application layer
  - Disable 0-RTT for sensitive endpoints

OpenSSL configuration:
  SSL_CTX_set_max_early_data(ctx, 0);  // disable 0-RTT entirely
```

### 9.4 Rust TLS Implementation (rustls)

```toml
# Cargo.toml
[dependencies]
rustls = "0.23"
rustls-pemfile = "2.0"
tokio = { version = "1", features = ["full"] }
tokio-rustls = "0.26"
```

```rust
// File: src/tls_server.rs
// Production TLS 1.3 server with mTLS support

use std::fs::File;
use std::io::{self, BufReader};
use std::net::SocketAddr;
use std::sync::Arc;

use rustls::pki_types::{CertificateDer, PrivateKeyDer};
use rustls::server::{ClientHello, ResolvesServerCert, WebPkiClientVerifier};
use rustls::{RootCertStore, ServerConfig};
use rustls_pemfile::{certs, pkcs8_private_keys};
use tokio::net::TcpListener;
use tokio_rustls::TlsAcceptor;

/// Load certificates from PEM file
fn load_certs(path: &str) -> io::Result<Vec<CertificateDer<'static>>> {
    let certfile = File::open(path)?;
    let mut reader = BufReader::new(certfile);
    certs(&mut reader).collect()
}

/// Load private key from PKCS8 PEM file
fn load_private_key(path: &str) -> io::Result<PrivateKeyDer<'static>> {
    let keyfile = File::open(path)?;
    let mut reader = BufReader::new(keyfile);
    
    pkcs8_private_keys(&mut reader)
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "no private key found"))?
        .map(Into::into)
}

/// Build TLS server config with strict security settings
pub fn build_tls_config(
    cert_path: &str,
    key_path: &str,
    ca_path: Option<&str>,  // CA for client cert verification (mTLS)
) -> Result<Arc<ServerConfig>, Box<dyn std::error::Error>> {
    let certs = load_certs(cert_path)?;
    let key = load_private_key(key_path)?;
    
    let builder = if let Some(ca) = ca_path {
        // mTLS: require client certificate
        let ca_certs = load_certs(ca)?;
        let mut root_store = RootCertStore::empty();
        for cert in ca_certs {
            root_store.add(cert)?;
        }
        
        let client_verifier = WebPkiClientVerifier::builder(Arc::new(root_store))
            .build()?;
        
        ServerConfig::builder()
            .with_client_cert_verifier(client_verifier)
    } else {
        // TLS without client cert
        ServerConfig::builder().with_no_client_auth()
    };
    
    let mut config = builder.with_single_cert(certs, key)?;
    
    // Security hardening
    // TLS 1.3 only (reject 1.2 and below)
    config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];
    
    // Disable session tickets if strict forward secrecy required
    // (session tickets can weaken FS if ticket key is compromised)
    config.session_storage = Arc::new(rustls::server::NoServerSessionStorage {});
    
    // Disable 0-RTT for sensitive services
    config.max_early_data_size = 0;
    
    Ok(Arc::new(config))
}

/// TLS-secured TCP server
pub async fn run_tls_server(
    addr: SocketAddr,
    config: Arc<ServerConfig>,
) -> io::Result<()> {
    let acceptor = TlsAcceptor::from(config);
    let listener = TcpListener::bind(addr).await?;
    
    println!("TLS server listening on {}", addr);
    
    loop {
        let (tcp_stream, peer_addr) = listener.accept().await?;
        let acceptor = acceptor.clone();
        
        tokio::spawn(async move {
            match acceptor.accept(tcp_stream).await {
                Ok(tls_stream) => {
                    let (_, server_conn) = tls_stream.get_ref();
                    
                    // Log cipher suite and protocol version
                    if let Some(proto) = server_conn.alpn_protocol() {
                        println!("ALPN: {}", String::from_utf8_lossy(proto));
                    }
                    
                    // If mTLS: extract and validate client identity
                    if let Some(client_certs) = server_conn.peer_certificates() {
                        println!("Client presented {} cert(s)", client_certs.len());
                        // Parse cert to extract SPIFFE ID or CN
                        // for authorization decisions
                    }
                    
                    println!("TLS connection from {}", peer_addr);
                    // handle_connection(tls_stream).await;
                }
                Err(e) => {
                    // Log but don't panic - could be scanner/probe
                    eprintln!("TLS handshake failed from {}: {}", peer_addr, e);
                }
            }
        });
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Server cert + key
    let config = build_tls_config(
        "/etc/ssl/server.crt",
        "/etc/ssl/server.key",
        Some("/etc/ssl/ca.crt"),  // enable mTLS
    )?;
    
    run_tls_server("0.0.0.0:8443".parse()?, config).await?;
    Ok(())
}
```

Certificate validation checklist:
```rust
// Critical validation steps for peer certificates
// (Beyond what rustls does automatically)

fn validate_certificate_for_service(
    cert: &CertificateDer,
    expected_spiffe_id: &str,
) -> Result<(), CertValidationError> {
    // rustls already validates:
    // 1. Certificate chain to trusted CA
    // 2. Certificate not expired
    // 3. Signature algorithms are acceptable
    // 4. Key usage extensions
    
    // Application MUST additionally validate:
    // 1. Subject Alternative Name matches expected identity
    // 2. SPIFFE URI SAN if using SPIFFE/SPIRE
    // 3. Custom OID extensions if using internal PKI
    // 4. Certificate Transparency (CT) logs for public-facing
    // 5. OCSP/CRL revocation status
    
    let parsed = parse_x509_cert(cert)?;
    
    // Check SPIFFE SVID format
    let spiffe_uri = parsed.subject_alt_names()
        .find(|san| san.starts_with("spiffe://"))
        .ok_or(CertValidationError::MissingSpiffeId)?;
    
    if spiffe_uri != expected_spiffe_id {
        return Err(CertValidationError::SpiffeIdMismatch {
            expected: expected_spiffe_id.to_string(),
            got: spiffe_uri.to_string(),
        });
    }
    
    Ok(())
}
```

---

## 10. mTLS and Zero Trust Identity

### 10.1 mTLS Architecture

```
Without mTLS (standard TLS):
  Client ──cert?─► Server (no)
         ◄─cert── Server presents cert
         ──verified─► [channel open - but CLIENT is anonymous]

With mTLS:
  Client ──ClientHello─────────────────────► Server
         ◄─ServerHello─────────────────────
         ◄─Certificate (server cert)────────
         ◄─CertificateRequest──────────────  ← server demands client cert
         ◄─CertificateVerify──────────────
         ◄─Finished────────────────────────
         ──Certificate (client cert)────────►
         ──CertificateVerify────────────────► ← client proves key ownership
         ──Finished─────────────────────────►
  [Mutual authentication established]

Identity anchored to:
  - X.509 certificate → CN, SAN, OID extensions
  - SPIFFE SVID: spiffe://trust-domain/ns/namespace/sa/service-account
  - Short-lived certificates (SVID TTL: 1 hour default in SPIRE)
```

### 10.2 SPIFFE/SPIRE Integration

```yaml
# SPIRE server configuration (spire-server.conf)
server {
  bind_address = "0.0.0.0"
  bind_port = "8081"
  socket_path = "/tmp/spire-server/private/api.sock"
  trust_domain = "prod.example.com"
  data_dir = "/opt/spire/data/server"
  log_level = "INFO"
  
  # JWT SVID TTL
  jwt_issuer = "https://spire.prod.example.com"
  
  # CA configuration - use hardware HSM in production
  ca_ttl = "24h"
  default_x509_svid_ttl = "1h"    # Short-lived SVIDs
  default_jwt_svid_ttl = "5m"     # Very short for JWT
}

plugins {
  DataStore "sql" {
    plugin_data {
      database_type = "postgres"
      connection_string = "postgresql://spire:${SPIRE_DB_PASS}@localhost/spiredb"
    }
  }

  KeyManager "disk" {
    plugin_data {
      keys_path = "/opt/spire/data/server/keys.json"
      # Production: use "aws_kms" or "hashicorp_vault" plugin
    }
  }

  NodeAttestor "k8s_psat" {
    plugin_data {
      clusters = {
        "prod-cluster" = {
          service_account_allow_list = [
            "spire:spire-agent"
          ]
        }
      }
    }
  }
}
```

---

## 11. DNS Security (DNSSEC, DoH, DoT)

### 11.1 DNS Attack Taxonomy

```
Cache Poisoning (Kaminsky Attack, 2008):
  Attacker floods resolver with forged responses
  Guesses transaction ID (16-bit) + source port
  Birthday paradox: 65536 * 65536 = 4.3B combinations
  Modern resolvers use random source ports → 10M+ combinations
  DNSSEC: cryptographic signatures prevent forgery

DNS Amplification (DDoS):
  Attacker sends DNS queries with spoofed victim source IP
  Open resolver responds with large answer (up to 4096 bytes)
  Amplification factor: up to 100x
  Mitigation: 
    - Close open resolvers (BCP140)
    - Response Rate Limiting (RRL)
    - ACLs on DNS servers

DNS Tunneling (Exfiltration):
  C2 communication encoded in DNS queries/responses
  encoder.malware.c2.example.com TXT "base64payload"
  Detection: long query names, high query rate, uncommon record types
  Mitigation: DNS monitoring, anomaly detection, RPZ (Response Policy Zones)

NXDOMAIN Hijacking:
  ISP/attacker intercepts NXDOMAIN responses, redirects to ad page
  Mitigation: DNS over HTTPS (DoH), DNS over TLS (DoT)

DNS Rebinding:
  Attacker controls DNS, returns valid IP initially
  After TTL expires, returns internal IP (192.168.x.x)
  Browser same-origin policy bypassed
  Mitigation: 
    - DNS rebinding protection in resolvers (reject private IPs for public domains)
    - Bind to specific interface in applications
    - Host header validation
```

### 11.2 DNSSEC Chain of Trust

```
Root Zone (.)
  └── KSK (Key Signing Key) — 4096-bit RSA or Ed25519
       └── ZSK (Zone Signing Key) — 2048-bit RSA
            └── Signs all RRsets in zone

Resolution with DNSSEC:
  1. Resolver queries example.com A
  2. Gets A record + RRSIG (signature over RRset)
  3. Gets DNSKEY record (public ZSK)
  4. Gets DS record from parent (.com) → links to child KSK
  5. Validates: RRSIG(A record, ZSK) → valid?
  6. Validates: DS(KSK hash) from .com → matches DNSKEY?
  7. Chain verified back to trust anchor (root KSK)

Negative responses (NSEC/NSEC3):
  NSEC:  proves non-existence by listing next existing name
         (zone walking attack: enumerate all names)
  NSEC3: hashed names prevent enumeration
         Salt + iterations protect against precomputed rainbow tables
```

```bash
# Verify DNSSEC chain
dig +dnssec example.com A
dig +dnssec example.com DNSKEY
dig DNSKEY . | grep "257"  # root KSK

# Test DNSSEC validation
delv @8.8.8.8 example.com A +rtrace

# Check if domain is DNSSEC-signed
dig example.com DS @8.8.8.8 +short

# DNSSEC debugging
dig +multiline +dnssec +cd example.com  # +cd = checking disabled (bypass DNSSEC)
```

### 11.3 DNS over TLS (DoT) and DNS over HTTPS (DoH)

```
DoT (RFC 7858):
  Port: 853 (dedicated, easy to block)
  Protocol: TLS 1.2+ wrapping DNS wire format
  Authentication: server cert validation (or SPKI pinning)
  
DoH (RFC 8484):
  Port: 443 (HTTP/2, mixed with web traffic - hard to block)
  Format: application/dns-message (binary) or application/dns-json
  Benefit: privacy from ISP, harder to censor
  Concern: centralizes DNS to large providers (Cloudflare, Google)

DNS over QUIC (DoQ, RFC 9250):
  Uses QUIC transport
  Reduces head-of-line blocking vs DoT
  
Implementation in Go/Rust: use getdns, stubby, or Unbound with DoT
```

```bash
# DoT with kdig
kdig -d @1.1.1.1 +tls-ca +tls-hostname=one.one.one.one example.com

# Configure systemd-resolved for DoT
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com
DNSOverTLS=yes
DNSSEC=yes
DNSStubListener=yes

# Unbound with DoT upstream
# /etc/unbound/unbound.conf
server:
    tls-cert-bundle: /etc/ssl/certs/ca-certificates.crt

forward-zone:
    name: "."
    forward-tls-upstream: yes
    forward-addr: 1.1.1.1@853#cloudflare-dns.com
    forward-addr: 9.9.9.9@853#dns.quad9.net
```

---

## 12. BGP Security (RPKI, Route Filtering)

### 12.1 BGP Attack Landscape

BGP (Border Gateway Protocol) is the routing protocol of the Internet. It was designed for trust, not security — any AS (Autonomous System) can announce any prefix.

```
BGP Hijacking types:

1. Exact-prefix hijack:
   Legitimate owner: AS64496 announces 203.0.113.0/24
   Attacker:         AS666 announces 203.0.113.0/24
   Effect: ~50% of traffic goes to attacker (depends on AS path)

2. More-specific hijack (most effective):
   Legitimate: 203.0.113.0/24
   Attacker:   203.0.113.128/25 (more specific → always preferred)
   Effect: all traffic to that /25 hijacked

3. Sub-prefix hijack for interception (man-in-the-middle):
   Attacker announces more-specific, has route to legitimate
   Traffic flows: Client → Attacker → Forward to victim
   Can decrypt HTTPS if combined with valid cert or HPKP bypassed

Real incidents:
  - 2008: Pakistan Telecom hijacked YouTube (AS17557 → /24 more-specific)
  - 2010: China Telecom hijacked 15% of Internet routes for 18 minutes
  - 2018: Amazon Route53 DNS hijack (MyEtherWallet.com BGP + DNS)
  - 2019: Verizon accepted Cloudflare routes from Allegheny Technologies
```

### 12.2 RPKI (Resource Public Key Infrastructure)

```
RPKI creates cryptographically signed Route Origin Authorizations (ROAs):

ROA:
  - Origin ASN: 64496
  - Prefix: 203.0.113.0/24
  - Max length: 24 (no more-specific allowed)
  - Signed by: IP address holder's certificate
  - Certificate chain: IANA → RIR (ARIN/RIPE/APNIC) → ISP → customer

Validation states:
  Valid:   prefix + ASN matches a ROA
  Invalid: prefix matches a ROA but ASN doesn't, or more-specific than maxLength
  NotFound: no ROA exists for this prefix (can still be accepted, but flagged)

RPKI deployment:
  1. Relying Party (RP) software: routinator, OctoRPKI, rpki-client
  2. RTR (RPKI-to-Router) protocol feeds VRPs to routers
  3. Router enforces policy based on validation state

BGP policy with RPKI (Junos example):
  policy-statement RPKI {
    term INVALID {
      from {
        protocol bgp;
        validation-database invalid;
      }
      then reject;  # Drop invalid routes
    }
    term VALID {
      from {
        protocol bgp;
        validation-database valid;
      }
      then {
        local-preference 200;
        accept;
      }
    }
    term NOT-FOUND {
      from {
        protocol bgp;
        validation-database unknown;
      }
      then {
        local-preference 100;
        accept;  # Accept but lower preference
      }
    }
  }
```

```bash
# Install routinator (RPKI relying party)
cargo install routinator

# Initialize (fetches trust anchors)
routinator init --accept-arin-rpa

# Run RTR server (feeds validated prefix list to routers)
routinator server --rtr 0.0.0.0:3323 --http 0.0.0.0:9556

# Query validation state
routinator validate --asn 64496 --prefix 203.0.113.0/24

# Monitor RPKI coverage
routinator --output json vrps > vrps.json

# Check if your prefixes have ROAs
curl -s "https://rpki-validator.ripe.net/api/v1/validity/64496/203.0.113.0/24"
```

### 12.3 BGP Security Hardening

```bash
# GTSM (Generalized TTL Security Mechanism) - RFC 5082
# Prevents BGP sessions from being established with forged source IPs
# Only peers with TTL=255 (1 hop) are accepted

# FRRouting (FRR) configuration
router bgp 64496
  neighbor 192.0.2.1 remote-as 64500
  neighbor 192.0.2.1 ttl-security hops 1   # GTSM: expect TTL≥254
  neighbor 192.0.2.1 password "TCPmd5passphrase"  # TCP MD5 (legacy) or TCP-AO
  
  # Prefix filtering (critical - never accept full BGP table by default)
  neighbor 192.0.2.1 prefix-list INBOUND-FILTER in
  neighbor 192.0.2.1 prefix-list OUTBOUND-FILTER out
  
  # Maximum prefixes (protection against route leaks)
  neighbor 192.0.2.1 maximum-prefix 100 warning-only

# Prefix list filters
ip prefix-list BOGON-FILTER deny 0.0.0.0/8 le 32
ip prefix-list BOGON-FILTER deny 10.0.0.0/8 le 32
ip prefix-list BOGON-FILTER deny 100.64.0.0/10 le 32
ip prefix-list BOGON-FILTER deny 127.0.0.0/8 le 32
ip prefix-list BOGON-FILTER deny 169.254.0.0/16 le 32
ip prefix-list BOGON-FILTER deny 172.16.0.0/12 le 32
ip prefix-list BOGON-FILTER deny 192.0.0.0/24 le 32
ip prefix-list BOGON-FILTER deny 192.0.2.0/24 le 32
ip prefix-list BOGON-FILTER deny 192.168.0.0/16 le 32
ip prefix-list BOGON-FILTER deny 198.18.0.0/15 le 32
ip prefix-list BOGON-FILTER deny 198.51.100.0/24 le 32
ip prefix-list BOGON-FILTER deny 203.0.113.0/24 le 32
ip prefix-list BOGON-FILTER deny 240.0.0.0/4 le 32
ip prefix-list BOGON-FILTER deny 255.255.255.255/32
ip prefix-list BOGON-FILTER deny 0.0.0.0/0           # Deny default route
ip prefix-list BOGON-FILTER deny 0.0.0.0/0 ge 25     # Deny /25 and more specific
ip prefix-list BOGON-FILTER permit 0.0.0.0/0 le 24   # Allow /8 to /24 only
```

---

## 13. Routing and Switching Security

### 13.1 Layer 2 Attacks and Mitigations

**ARP Spoofing / ARP Poisoning**
```
Attack:
  Attacker sends unsolicited ARP replies
  "192.168.1.1 is at AA:BB:CC:DD:EE:FF" (attacker's MAC)
  Hosts update ARP cache, send traffic to attacker

Mitigation: Dynamic ARP Inspection (DAI)
  - DHCP Snooping binding table: {MAC, IP, VLAN, Port}
  - ARP packets validated against binding table
  - Invalid ARP packets dropped
  
Cisco IOS:
  ip dhcp snooping
  ip dhcp snooping vlan 10
  
  interface GigabitEthernet0/1
    ip dhcp snooping trust    ! Only on uplinks to DHCP server
  
  ip arp inspection vlan 10
  ip arp inspection validate src-mac dst-mac ip
```

**VLAN Hopping**
```
Double-tagging attack:
  1. Attacker on VLAN 10 sends frame with two 802.1Q tags:
     Outer tag: native VLAN (e.g., VLAN 1)
     Inner tag: target VLAN (e.g., VLAN 20)
  2. First switch strips outer tag (native VLAN untagged)
  3. Second switch sees inner tag, forwards to VLAN 20
  
Mitigation:
  - Change native VLAN to unused VLAN (not VLAN 1)
  - Explicitly tag the native VLAN
  - Disable DTP (Dynamic Trunking Protocol) on access ports
  
Cisco:
  interface GigabitEthernet0/1
    switchport mode access         ! Disable DTP negotiation
    switchport access vlan 10
    switchport nonegotiate
    spanning-tree portfast
    spanning-tree bpduguard enable  ! STP BPDU guard
```

**MAC Flooding / CAM Table Overflow**
```
Attack:
  Flood switch with frames from random MACs
  CAM table fills up (typically 8K-16K entries)
  Switch enters "fail-open" mode: broadcasts all frames (hub behavior)
  Attacker receives all traffic

Mitigation: Port Security
  interface GigabitEthernet0/1
    switchport port-security
    switchport port-security maximum 2           ! Max 2 MACs
    switchport port-security violation restrict  ! or shutdown
    switchport port-security mac-address sticky  ! Learn current MACs
```

**Spanning Tree Protocol (STP) Attacks**
```
Attack:
  Attacker sends superior BPDU (Bridge Protocol Data Unit)
  Becomes root bridge for VLAN
  All traffic flows through attacker

Mitigation:
  - BPDU Guard on access ports (shutdown if BPDU received)
  - Root Guard on distribution ports (prevents root bridge takeover)
  - PortFast only on access ports (never on trunk ports)
  
  interface GigabitEthernet0/1
    spanning-tree portfast
    spanning-tree bpduguard enable
  
  interface GigabitEthernet0/48  ! Uplink
    spanning-tree guard root
```

**802.1X Port-Based Authentication**
```
EAP/802.1X flow:
  Supplicant (client) ←→ Authenticator (switch) ←→ Authentication Server (RADIUS)
  
  1. Client connects to port
  2. Switch: port in unauthorized state (EAPOL only)
  3. Switch sends EAP-Request/Identity
  4. Client responds with EAP-Response/Identity
  5. Switch relays to RADIUS server (RADIUS Access-Request)
  6. RADIUS responds with challenge (EAP-TLS, PEAP, EAP-TTLS)
  7. Client and RADIUS complete EAP authentication
  8. RADIUS: Access-Accept → switch opens port (authorized state)
  9. RADIUS can return VLAN assignment in Access-Accept

FreeRADIUS with EAP-TLS:
  # /etc/freeradius/3.0/sites-enabled/default
  authenticate {
    Auth-Type EAP {
      eap
    }
  }
  
  # /etc/freeradius/3.0/mods-enabled/eap
  eap {
    default_eap_type = tls
    tls-config tls-common {
      private_key_file = /etc/ssl/private/radius.key
      certificate_file = /etc/ssl/certs/radius.crt
      ca_file = /etc/ssl/certs/ca.crt
      verify_client_cert = yes
      check_crl = yes
    }
  }
```

### 13.2 Layer 3 Routing Security

**Unicast Reverse Path Forwarding (uRPF)**
```
Problem: IP spoofing — source IP doesn't match inbound interface

uRPF strict mode:
  For each inbound packet, check:
  - Is source IP reachable via the same interface it arrived on?
  - If not → DROP (spoof detected)
  
uRPF loose mode:
  - Is source IP reachable via ANY interface?
  - Less effective but works with asymmetric routing

Linux:
  sysctl -w net.ipv4.conf.eth0.rp_filter=1  # strict
  sysctl -w net.ipv4.conf.eth0.rp_filter=2  # loose

Cisco IOS:
  interface GigabitEthernet0/0
    ip verify unicast source reachable-via rx  ! strict
    ! or: ip verify unicast source reachable-via any  (loose)
```

**Route Filtering with Prefix Lists and AS-Path Filters**
```
# FRRouting: AS-path access lists
bgp as-path access-list MY-ASNS permit ^(64496|64497|64498)$

# Route maps with multiple match criteria
route-map INBOUND-POLICY permit 10
  match as-path MY-ASNS
  match ip address prefix-list ALLOWED-PREFIXES
  set local-preference 150
  set community 64496:100

route-map INBOUND-POLICY deny 9999  # Implicit deny with explicit statement
```

---

## 14. Firewalls: Architecture and Design

### 14.1 Firewall Types

```
1. Packet Filter (Stateless)
   - Examines each packet independently
   - Matches on: src/dst IP, src/dst port, protocol, flags
   - No awareness of connection state
   - Fast (no state table) but limited
   - Vulnerable to: IP fragmentation attacks, TCP state confusion
   - Example: ACLs on router interfaces

2. Stateful Inspection (SPI)
   - Tracks connection state table
   - Matches return traffic automatically
   - Connection state: NEW, ESTABLISHED, RELATED, INVALID
   - Linux: iptables/nftables/conntrack
   - Vulnerable to: state table exhaustion (SYN flood)

3. Application-Layer Gateway (ALG) / Deep Packet Inspection (DPI)
   - Inspects L7 payload
   - Can decode HTTP, FTP, SIP, DNS protocols
   - Can block by URL, content type, user agent
   - SSL inspection (MITM): decrypt TLS to inspect payload
   - Performance cost: significant CPU for TLS termination

4. Next-Generation Firewall (NGFW)
   - Stateful + DPI + identity-aware (user/group, not just IP)
   - Application identification (App-ID)
   - Threat intelligence integration
   - Sandboxing for unknown files
   - Examples: Palo Alto PAN-OS, Fortinet FortiGate, Cisco Firepower

5. Web Application Firewall (WAF)
   - L7 only: HTTP/HTTPS focused
   - Signatures for OWASP Top 10 (SQLi, XSS, CSRF, etc.)
   - Rate limiting, bot detection, geo-blocking
   - Examples: ModSecurity, AWS WAF, Cloudflare WAF

6. Software-Defined Perimeter (SDP) / ZTNA
   - No implicit trust based on network position
   - Every connection authenticated before access granted
   - Micro-segmentation per application
```

### 14.2 High-Availability Firewall Design

```
Active-Passive HA:
  ┌────────────────────────────────────────────────────────────────┐
  │ Internet                                                        │
  └──────────────────────┬─────────────────────────────────────────┘
                         │
               ┌─────────▼─────────┐
               │   Border Router   │
               │   (ECMP/VRRP)     │
               └────────┬──────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
   ┌────────▼───────┐   ┌───────────▼──────┐
   │  FW-01 (Active)│   │  FW-02 (Standby) │
   │  VRRP: Master  │   │  VRRP: Backup    │
   │  State sync ◄──┼───┼──► conntrack sync │
   │  HA link       │   │  HA link          │
   └────────┬───────┘   └───────────────────┘
            │
   ┌────────▼────────────────────────────────┐
   │  Internal Switch (L3)                    │
   │  VLAN 10: Servers, VLAN 20: Management   │
   └─────────────────────────────────────────┘

conntrack sync (conntrackd):
  # /etc/conntrackd/conntrackd.conf
  Sync {
    Mode FTFW {
      ResendQueueSize 131072
      ResendTimeout 2
      DisableExternalCache Off
      PurgeTimeout 5
    }
    UDP {
      IPv4_address 192.168.254.1
      IPv4_Destination_Address 192.168.254.2
      Port 3780
      Interface eth2
      SndSocketBuffer 24985600
      RcvSocketBuffer 24985600
      Checksum on
    }
  }
  
  General {
    Systemd off
    LockFile /var/lock/conntrackd.lock
    UNIX { Path /var/run/conntrackd.ctl }
    Filter {
      Protocol Accept { TCP UDP ICMP }
      Address Ignore { IPv4_address 127.0.0.1 }
    }
  }
```

### 14.3 Zero-Downtime Firewall Rule Updates (nftables)

```bash
# Atomic rule replacement (critical for production)
# Old ruleset remains active until new one is fully loaded

# Write new ruleset to file
cat > /tmp/new_rules.nft << 'EOF'
flush ruleset
# ... new rules ...
EOF

# Validate without applying
nft -c -f /tmp/new_rules.nft

# Apply atomically (single syscall transaction)
nft -f /tmp/new_rules.nft

# Rollback if needed (keep backup)
nft -f /etc/nftables.conf.backup
```

---

## 15. Network Intrusion Detection and Prevention

### 15.1 Snort/Suricata Rule Language

Suricata is the production-grade open-source IDS/IPS for CNCF-adjacent security tooling:

```
Rule format:
action proto src_ip src_port direction dst_ip dst_port (options)

Examples:
# Detect SYN flood
alert tcp any any -> $HOME_NET any \
    (flags:S; threshold: type both, track by_src, count 500, seconds 1; \
     msg:"Possible SYN flood"; sid:1000001; rev:1;)

# Detect port scan
alert tcp any any -> $HOME_NET any \
    (flags:S; threshold: type both, track by_src, count 20, seconds 5; \
     msg:"Port scan detected"; sid:1000002; rev:1;)

# Detect SQL injection attempt
alert http any any -> $HTTP_SERVERS $HTTP_PORTS \
    (msg:"SQL Injection attempt"; \
     flow:to_server,established; \
     http.uri; content:"UNION"; nocase; content:"SELECT"; nocase; \
     pcre:"/UNION\s+SELECT/i"; \
     sid:1000003; rev:1;)

# Detect DNS tunneling (long query names)
alert dns any any -> any 53 \
    (msg:"Possible DNS tunneling - long hostname"; \
     dns.query; isdataat:50,relative; \
     threshold: type both, track by_src, count 10, seconds 60; \
     sid:1000004; rev:1;)

# Detect TLS with self-signed cert (no CA in chain)
alert tls any any -> $HOME_NET any \
    (msg:"TLS self-signed certificate"; \
     tls.cert_issuer; content:!"Let's Encrypt"; \
     tls.cert_subject; pcre:"/^CN=[^,]+$/"; \
     sid:1000005; rev:1;)
```

Suricata configuration:
```yaml
# /etc/suricata/suricata.yaml (security-critical settings)

vars:
  address-groups:
    HOME_NET: "[10.0.0.0/8,172.16.0.0/12,192.168.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    DNS_SERVERS: "$HOME_NET"

# Run as IPS (inline) mode via netfilter queue
nfq:
  mode: accept

# Or AF_PACKET for passive monitoring
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow  # symmetric flow assignment
    defrag: yes
    use-mmap: yes
    ring-size: 2048

# Output
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert:
            tagged-packets: yes
        - dns:
            query: yes
            answer: yes
        - tls:
            extended: yes
        - http:
            extended: yes
        - flow

# Detection engine
detect:
  profile: high
  custom-values:
    toclient-groups: 3
    toserver-groups: 25
  sgh-mpm-context: auto
  inspection-recursion-limit: 3000

# Stream engine
stream:
  memcap: 64mb
  checksum-validation: yes
  inline: auto
  reassembly:
    memcap: 256mb
    depth: 1mb
    toserver-chunk-size: 2560
    toclient-chunk-size: 2560
```

### 15.2 eBPF-Based IDS (Falco-style)

```c
// Kernel-space network event capture using eBPF
// Detect unusual network connections from containers

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/socket.h>
#include <linux/in.h>

struct net_event {
    __u32 pid;
    __u32 uid;
    __u32 saddr;
    __u32 daddr;
    __u16 dport;
    __u16 sport;
    __u8  proto;
    char  comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __type(key, int);
    __type(value, int);
} events SEC(".maps");

// Trace tcp_connect kernel function
SEC("kprobe/tcp_connect")
int trace_tcp_connect(struct pt_regs *ctx)
{
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    struct net_event event = {};
    
    event.pid = bpf_get_current_pid_tgid() >> 32;
    event.uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    
    // Read socket addresses
    bpf_probe_read_kernel(&event.saddr,
        sizeof(event.saddr),
        &sk->__sk_common.skc_rcv_saddr);
    bpf_probe_read_kernel(&event.daddr,
        sizeof(event.daddr),
        &sk->__sk_common.skc_daddr);
    bpf_probe_read_kernel(&event.dport,
        sizeof(event.dport),
        &sk->__sk_common.skc_dport);
    
    event.dport = bpf_ntohs(event.dport);
    
    // Send to userspace for policy evaluation
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                           &event, sizeof(event));
    
    return 0;
}

char _license[] SEC("license") = "GPL";
```

---

## 16. DDoS: Attack Taxonomy and Mitigation

### 16.1 DDoS Attack Categories

```
Volumetric (L3/L4):
  Goal: Exhaust bandwidth
  Method: UDP flood, ICMP flood, amplification attacks
  Scale: 1-10 Tbps possible (Mirai botnet, Cloudflare records)
  
  Amplification attacks (UDP):
  ┌──────────────────────────────────────────────────────────────┐
  │ Attack type  │ Req size │ Resp size │ Amplification factor   │
  │──────────────────────────────────────────────────────────────│
  │ DNS          │ 60 bytes │ 4096 bytes│ 68x                    │
  │ NTP (monlist)│ 8 bytes  │ 2650 bytes│ 556x                   │
  │ SSDP         │ 30 bytes │ 3000 bytes│ 100x                   │
  │ memcached    │ 15 bytes │ 1MB       │ 51200x (!!)            │
  │ LDAP (CLDAP) │ 52 bytes │ 70KB      │ 1300x                  │
  └──────────────────────────────────────────────────────────────┘

Protocol exhaustion (L4):
  Goal: Exhaust server state tables
  Method: SYN flood, ACK flood, fragmented packet flood
  Target: Firewall state table, server TCP stack
  Mitigation: SYN cookies, upstream scrubbing

Application layer (L7):
  Goal: Exhaust server resources (CPU, memory, DB)
  Method: HTTP GET/POST flood, Slowloris, slow HTTP body
  Hard to distinguish from legitimate traffic
  Mitigation: rate limiting, challenge-response (CAPTCHAs, JS challenges)
  
Slowloris attack:
  Open many TCP connections, send partial HTTP request
  Never complete (keep connection alive with partial headers)
  Server holds connections waiting for complete request
  Apache mod_reqtimeout / nginx client_body_timeout = mitigation
```

### 16.2 DDoS Mitigation Architecture

```
Tier 1: Upstream Scrubbing Centers
  ┌─────────────────────────────────────────────────────────────┐
  │  Attack traffic flows:                                       │
  │  Internet → BGP Anycast → Scrubbing Center                  │
  │              ↑                                              │
  │              BGP community triggers diversion               │
  │  Clean traffic:                                             │
  │  Scrubbing Center → GRE tunnel → Origin                     │
  └─────────────────────────────────────────────────────────────┘

  Providers: Cloudflare Magic Transit, Akamai Prolexic, AWS Shield Advanced

Tier 2: Transit Provider Filtering (Flowspec, RFC 5575)
  BGP Flowspec allows injecting packet filter rules into transit routers:
  
  type 1: destination-prefix  (filter by dest IP)
  type 2: source-prefix       (filter by source IP)  
  type 3: protocol            (filter by L4 protocol)
  type 5: source-port         (filter by source port)
  
  Actions:
    traffic-rate: 0  → discard (blackhole)
    redirect: VRF   → redirect to scrubbing
    dscp: mark      → mark for QoS

Tier 3: On-Premises Mitigation
  - Linux + XDP: drop at NIC level (multi-Mpps)
  - Hardware firewalls: ASICs for terabit-scale
  - Anycast load balancing: distribute attack across PoPs

Tier 4: Application Layer
  - Rate limiting (token bucket, leaky bucket)
  - Connection queuing (nginx limit_conn)
  - CAPTCHAs / JS challenges for HTTP floods
  - Resource isolation (per-tenant limits)
```

### 16.3 SYN Cookie Implementation (C)

```c
// File: syn_cookie.c
// Demonstrates SYN cookie concept (kernel implements this natively)
// Reference implementation for understanding the mechanism

#include <stdint.h>
#include <string.h>
#include <openssl/hmac.h>
#include <arpa/inet.h>

// SYN cookie: encode MSS, timestamp, and HMAC into ISN
// ISN = t[3 bits] | M[3 bits] | hash[26 bits]
// t = time in 64-second units (prevents replay)
// M = encoded MSS (3 bits = 8 possible MSS values)
// hash = truncated HMAC-SHA1 of (src_ip, dst_ip, src_port, dst_port, t, M, key)

static const uint16_t mss_table[] = {536, 1300, 1460, 1440, 1460, 1440, 1460, 1440};

static uint32_t compute_cookie_hash(
    uint32_t saddr, uint32_t daddr,
    uint16_t sport, uint16_t dport,
    uint32_t t, uint32_t mss_idx,
    const uint8_t *key, size_t key_len)
{
    uint8_t data[18];
    uint32_t idx = 0;
    
    memcpy(data + idx, &saddr,    4); idx += 4;
    memcpy(data + idx, &daddr,    4); idx += 4;
    memcpy(data + idx, &sport,    2); idx += 2;
    memcpy(data + idx, &dport,    2); idx += 2;
    memcpy(data + idx, &t,        4); idx += 4;
    memcpy(data + idx, &mss_idx,  2); idx += 2;
    
    uint8_t digest[20];
    unsigned int digest_len = 20;
    HMAC(EVP_sha1(), key, key_len, data, idx, digest, &digest_len);
    
    uint32_t hash;
    memcpy(&hash, digest, 4);
    return hash & 0x03FFFFFF;  // 26 bits
}

uint32_t generate_syn_cookie(
    uint32_t saddr, uint32_t daddr,
    uint16_t sport, uint16_t dport,
    uint16_t mss_offered,
    uint32_t timestamp_seconds,
    const uint8_t *secret, size_t secret_len)
{
    uint32_t t = (timestamp_seconds >> 6) & 0x7;  // 3 bits, 64-second granularity
    
    // Find best MSS from table
    uint32_t mss_idx = 0;
    for (int i = 7; i >= 0; i--) {
        if (mss_table[i] <= mss_offered) {
            mss_idx = i;
            break;
        }
    }
    
    uint32_t hash = compute_cookie_hash(saddr, daddr, sport, dport,
                                         t, mss_idx, secret, secret_len);
    
    return (t << 29) | (mss_idx << 26) | hash;
}

int validate_syn_cookie(
    uint32_t cookie,
    uint32_t saddr, uint32_t daddr,
    uint16_t sport, uint16_t dport,
    uint32_t timestamp_seconds,
    const uint8_t *secret, size_t secret_len,
    uint16_t *mss_out)
{
    uint32_t t_received = (cookie >> 29) & 0x7;
    uint32_t mss_idx    = (cookie >> 26) & 0x7;
    uint32_t hash_recv  = cookie & 0x03FFFFFF;
    
    // Check timestamp (allow 32-second window for clock skew)
    uint32_t t_now = (timestamp_seconds >> 6) & 0x7;
    if (t_received != t_now && t_received != ((t_now - 1) & 0x7))
        return -1;  // expired
    
    uint32_t hash_expected = compute_cookie_hash(
        saddr, daddr, sport, dport,
        t_received, mss_idx, secret, secret_len);
    
    if (hash_recv != hash_expected)
        return -1;  // invalid (possible spoofed ACK)
    
    if (mss_out)
        *mss_out = mss_table[mss_idx];
    
    return 0;  // valid
}
```

---

## 17. VPN: IPsec, WireGuard, Architecture

### 17.1 IPsec Architecture

```
IPsec provides:
  - Authentication Header (AH): integrity + authentication only (rarely used)
  - Encapsulating Security Payload (ESP): confidentiality + integrity

Modes:
  Transport mode: Encrypts payload only, original IP header intact
                  src → dst (both endpoints are IPsec-capable)
  
  Tunnel mode:   Encrypts entire original IP packet, new IP header added
                 Creates secure tunnel between gateways
                 src_gw → dst_gw (endpoints transparent)

Key Exchange:
  IKEv2 (RFC 7296) — current standard
  
  IKEv2 phases:
    Phase 1 (IKE SA): 
      Negotiate: encryption (AES-256-GCM), PRF (SHA-384), DH group (ECP-384)
      Authenticate: PSK or certificates (recommended: ECDSA/RSA)
      Result: IKE SA (bidirectional, used for control plane)
    
    Phase 2 (Child SA / IPsec SA):
      Negotiate: IPsec transform (ESP with AES-256-GCM)
      Create: two unidirectional SAs (inbound + outbound)
      Install: into SAD (Security Association Database)
      Result: encrypted data channel

Security databases:
  SAD (Security Association Database): 
    Active SAs, keying material, replay windows
  SPD (Security Policy Database):
    Rules: which traffic to protect, how, and to where
  
  SPD rule example:
    src: 10.0.0.0/8, dst: 172.16.0.0/12 → PROTECT via SA to peer 192.0.2.1
    src: any, dst: any → BYPASS (non-tunneled traffic)
```

StrongSwan configuration:
```bash
# /etc/swanctl/swanctl.conf

connections {
  corp-vpn {
    version = 2
    local_addrs = 192.0.2.1
    remote_addrs = 203.0.113.1
    
    proposals = aes256gcm16-prfsha384-ecp384  # Modern, AEAD-only
    
    local {
      auth = pubkey
      certs = server.pem
      id = "CN=vpn.example.com"
    }
    
    remote {
      auth = pubkey
      cacerts = ca.pem
    }
    
    children {
      corp-subnet {
        local_ts  = 10.0.0.0/8
        remote_ts = 172.16.0.0/12
        esp_proposals = aes256gcm16-ecp384
        mode = tunnel
        dpd_action = restart
        # Perfect Forward Secrecy: rekey frequently
        rekey_time = 3600s    # Rekey after 1 hour
        life_time = 7200s     # Max lifetime 2 hours
        rekey_bytes = 1073741824  # Rekey after 1GB
      }
    }
    
    dpd_delay = 30s
    dpd_timeout = 120s
    
    # Anti-replay window
    replay_window = 128
  }
}

secrets {
  private {
    file = server.key
  }
}
```

### 17.2 WireGuard — Architecture and Security Model

```
WireGuard design principles:
  1. Cryptographic agility is a misfeature (no negotiation, fixed algorithms)
  2. Minimize attack surface (4000 LoC vs IPsec/OpenVPN's 100k+)
  3. Silence = no response to invalid packets (no fingerprinting)
  4. Cryptokey routing: identity tied directly to keys

Fixed cryptography (no negotiation):
  - Handshake: Noise_IKpsk2 protocol
  - Key exchange: Curve25519 ECDH
  - Symmetric cipher: ChaCha20-Poly1305 (AEAD)
  - Hash/PRF: BLAKE2s
  - MAC: HMAC-BLAKE2s
  - Key derivation: HKDF

Cryptographic handshake:
  Initiator                              Responder
  ─────────                              ─────────
  Know: responder's public key (config)
  
  msg1 = (type=1, sender_idx,
           ephemeral = E_i encrypted,
           static    = S_i encrypted under (S_r_pub, E_i),
           timestamp = TAI64N encrypted,
           mac1, mac2)
  ─────────────────────────────────────────────────────────►
                                         Validates S_i (is it a peer?)
                                         msg2 = (type=2, sender_idx, receiver_idx,
                                                  ephemeral = E_r encrypted,
                                                  empty = "" encrypted,
                                                  mac1, mac2)
  ◄─────────────────────────────────────────────────────────
  Session keys derived: T_{send}, T_{recv} using HKDF
  [Data packets: encrypted ChaCha20-Poly1305]

Replay protection:
  - 64-bit counter per session
  - Sliding window of 2048 previous counters (out-of-order tolerance)
  - Packets outside window or already-seen counter → silently dropped
```

WireGuard kernel configuration:
```bash
# Install
apt install wireguard-tools

# Generate keys
wg genkey | tee /etc/wireguard/server_private.key | \
    wg pubkey > /etc/wireguard/server_public.key
chmod 600 /etc/wireguard/server_private.key

# Server config: /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <server_private_key>
Address = 10.200.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; \
         iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; \
           iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
# DNS = 10.200.0.1  # if running local DNS

[Peer]
PublicKey = <client_public_key>
PresharedKey = <psk>   # optional: quantum resistance
AllowedIPs = 10.200.0.2/32
# Persistent keepalive not needed on server

# Start
wg-quick up wg0
systemctl enable wg-quick@wg0

# Status
wg show wg0
wg show wg0 transfer
wg show wg0 latest-handshakes
```

WireGuard in Go (userspace, for embedded/containers):
```go
// Using golang.zx2c4.com/wireguard (the reference userspace implementation)
// go get golang.zx2c4.com/wireguard

package main

import (
    "fmt"
    "log"
    "net"
    "os"

    "golang.zx2c4.com/wireguard/conn"
    "golang.zx2c4.com/wireguard/device"
    "golang.zx2c4.com/wireguard/ipc"
    "golang.zx2c4.com/wireguard/tun"
    "golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

func main() {
    // Create TUN interface
    tunDev, err := tun.CreateTUN("wg0", device.DefaultMTU)
    if err != nil {
        log.Fatal(err)
    }

    // Create WireGuard device
    logger := device.NewLogger(device.LogLevelVerbose, "(wg) ")
    dev := device.NewDevice(tunDev, conn.NewDefaultBind(), logger)

    // Configure via UAPI
    uapiFile, err := ipc.UAPIOpen("wg0")
    if err != nil {
        log.Fatal(err)
    }
    defer uapiFile.Close()

    // Generate keys
    privateKey, _ := wgtypes.GeneratePrivateKey()
    fmt.Printf("Public key: %s\n", privateKey.PublicKey())

    // Device is now running
    dev.Up()
    
    // Wait for shutdown signal
    select {}
}
```

---

## 18. Zero Trust Network Architecture (ZTNA)

### 18.1 Zero Trust Principles

```
Traditional perimeter model (BROKEN):
  "Trust but verify" → Trust everything inside the perimeter
  Problem: Lateral movement after initial breach
  Assumption: Internal network = safe
  Reality: Insider threats, compromised endpoints, east-west attacks

Zero Trust Model:
  "Never trust, always verify"
  Core assertions:
    1. No implicit trust based on network location
    2. Authenticate every request (user + device + service)
    3. Authorize every request (least privilege)
    4. Assume breach has already occurred
    5. Verify explicitly, use all available signals

NIST SP 800-207 Seven Tenets:
  1. All data sources and services are resources
  2. All communication secured regardless of network location
  3. Per-session access to individual resources
  4. Access determined by dynamic policy (context-aware)
  5. Monitor integrity of all owned/associated devices
  6. Authenticate and authorize before granting access
  7. Collect data to improve security posture
```

### 18.2 ZTNA Implementation Stack

```
Identity Provider (IdP)
  └── SPIFFE/SPIRE (workload identity)
  └── HashiCorp Vault (secrets, PKI)
  └── Keycloak / Okta (user identity)

Policy Engine
  └── OPA (Open Policy Agent)
  └── Styra DAS (OPA management plane)

Enforcement Points
  └── Envoy (sidecar proxy) — per-service
  └── Cilium (eBPF-based) — per-pod in K8s
  └── Calico (per-pod NetworkPolicy)
  └── Service mesh (Istio/Linkerd)

Visibility
  └── Hubble (Cilium observability)
  └── Jaeger (distributed tracing)
  └── Prometheus + Grafana (metrics)
  └── Loki (log aggregation)
```

OPA network policy example:
```rego
# File: policy/network.rego
package network.authz

import future.keywords.if
import future.keywords.in

default allow = false

# Allow if all conditions met
allow if {
    # Source service has valid SPIFFE identity
    valid_spiffe_id(input.source.spiffe_id)
    
    # Source is authorized to call this destination
    authorized_caller(input.source.service, input.destination.service)
    
    # Connection uses mTLS
    input.connection.mutual_tls == true
    
    # Certificate is not expired (checked by proxy, but defense-in-depth)
    input.connection.cert_expiry_seconds > 0
    
    # Not in blocked list
    not blocked_service(input.source.service)
}

valid_spiffe_id(id) if {
    regex.match(`^spiffe://prod\.example\.com/`, id)
}

authorized_caller(source, dest) if {
    data.service_acl[dest][_] == source
}

blocked_service(service) if {
    service in data.blocked_services
}
```

---

## 19. Cloud Network Security — AWS

### 19.1 AWS Network Architecture

```
AWS Network Isolation Stack:
  
  Account boundary
  └── VPC (Virtual Private Cloud) — logical network isolation
      ├── Subnet (AZ-bound, public or private)
      │   ├── Route Table → Internet Gateway (public) or NAT GW (private)
      │   ├── Network ACL (stateless, subnet-level, L3/L4)
      │   └── Security Group (stateful, instance-level, L3/L4)
      ├── VPC Flow Logs → CloudWatch / S3 / Kinesis
      ├── VPC Endpoints (PrivateLink — no internet traversal)
      ├── Transit Gateway (inter-VPC, inter-account routing hub)
      └── AWS Network Firewall (stateful, L7 capable, Suricata rules)

Physical isolation model:
  Nitro Hypervisor:
    - AWS-designed hypervisor (not Xen/KVM in traditional sense)
    - Dedicated hardware for network/storage I/O (Nitro cards)
    - No host OS — hypervisor is firmware-like
    - Cryptographic attestation of instance identity
    - Memory encryption (AMD SEV on Graviton/EPYC instances)
```

### 19.2 VPC Security Design

```
Best Practice VPC Architecture:

┌─────────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Public Subnets (10.0.0.0/20 each AZ)                    │   │
│  │  Route: 0.0.0.0/0 → Internet Gateway                     │   │
│  │  Resources: NAT Gateway, Load Balancers, Bastion (NACLs) │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ NAT Gateway                             │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  Application Subnets (10.0.16.0/20 each AZ)              │   │
│  │  Route: 0.0.0.0/0 → NAT Gateway                          │   │
│  │  Resources: ECS/EKS tasks, EC2, Lambda (VPC-bound)       │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │ Internal LB                             │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  Data Subnets (10.0.32.0/20 each AZ)                     │   │
│  │  Route: no internet route (fully isolated)               │   │
│  │  Resources: RDS, ElastiCache, Secrets Manager endpoints  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Management Subnet (10.0.48.0/24)                        │   │
│  │  Bastion host (SSM preferred over SSH bastion)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

Network ACL rules (stateless — must allow both directions):
```
Inbound NACL for Application Subnet:
Priority  Protocol  Source              Port    Action
100       TCP       10.0.0.0/20         All     ALLOW  (from public subnet LB)
110       TCP       10.0.32.0/20        All     ALLOW  (from data subnet responses)
120       TCP       0.0.0.0/0           1024-65535 ALLOW  (return traffic for outbound)
32766     All       0.0.0.0/0           All     DENY

Outbound NACL for Application Subnet:
100       TCP       10.0.32.0/20        5432    ALLOW  (PostgreSQL)
110       TCP       0.0.0.0/0           443     ALLOW  (HTTPS egress)
120       TCP       0.0.0.0/0           1024-65535 ALLOW  (return traffic)
32766     All       0.0.0.0/0           All     DENY
```

Security Group for Application Layer (Terraform):
```hcl
resource "aws_security_group" "app" {
  name        = "app-tier"
  description = "Application tier - allow from LB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTPS from load balancer only"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.lb.id]  # SG reference, not CIDR
  }

  egress {
    description = "Allow to data tier PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.data.id]
  }

  egress {
    description = "HTTPS egress for API calls and SSM"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # No SSH ingress - use SSM Session Manager
  
  tags = {
    Name        = "app-tier-sg"
    Environment = "production"
  }
}
```

AWS Network Firewall (Suricata-compatible rules):
```
# Stateful rule group: Block known malicious domains
rule "suricata":
  action: ALERT drop
  protocols: ["TCP", "UDP"]
  direction: FORWARD
  rule_string: |
    pass tls $HOME_NET any -> $EXTERNAL_NET 443 \
      (tls.sni; content:"api.example.com"; \
       nocase; endswith; msg:"Allow known good"; \
       flow:established,to_server; sid:100001;)
    
    drop tls $HOME_NET any -> $EXTERNAL_NET 443 \
      (tls.sni; content:!".example.com"; \
       nocase; endswith; \
       msg:"Block unexpected egress TLS"; \
       flow:established,to_server; sid:100002;)
```

### 19.3 AWS Shield Advanced and WAF

```bash
# AWS WAF rate-based rule (blocks IP after 2000 req/5min)
aws wafv2 create-rule-group \
    --name "RateLimit" \
    --scope "REGIONAL" \
    --capacity 2 \
    --rules '[{
        "Name": "RateLimitRule",
        "Priority": 1,
        "Action": {"Block": {}},
        "Statement": {
            "RateBasedStatement": {
                "Limit": 2000,
                "AggregateKeyType": "IP"
            }
        },
        "VisibilityConfig": {
            "SampledRequestsEnabled": true,
            "CloudWatchMetricsEnabled": true,
            "MetricName": "RateLimitMetric"
        }
    }]' \
    --visibility-config '...'

# Enable Shield Advanced (programmatic)
aws shield create-subscription
aws shield associate-drt-log-bucket --log-bucket my-waf-logs
aws shield associate-drt-role --role-arn arn:aws:iam::123456789:role/AWSShieldDRTAccessRole
```

---

## 20. Cloud Network Security — Azure

### 20.1 Azure Network Security Architecture

```
Azure Network Security Stack:

  ┌─────────────────────────────────────────────────────────────┐
  │  Azure DDoS Protection Standard                              │
  │  (tenant-level, auto-scales, ML-based mitigation)           │
  └──────────────────────────┬──────────────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────────────┐
  │  Azure Firewall Premium (L7, IDPS, TLS inspection)           │
  │  Azure Application Gateway + WAF v2                          │
  └──────────────────────────┬──────────────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────────────┐
  │  Virtual Network (VNet)                                      │
  │  ├── Network Security Groups (NSG) — stateful, L4           │
  │  │   Applied at NIC level or Subnet level                    │
  │  ├── Application Security Groups (ASG) — logical grouping   │
  │  ├── Service Endpoints → PaaS without internet hop          │
  │  ├── Private Endpoints → PaaS with private IP in VNet       │
  │  └── VNet Peering / Virtual WAN (hub-and-spoke)             │
  └─────────────────────────────────────────────────────────────┘

Defender for Cloud (CSPM + CWPP):
  - Network topology visualization
  - Adaptive network hardening (ML-suggested NSG rules)
  - Just-in-time (JIT) VM access (temp NSG rules for management)
```

NSG configuration (ARM/Bicep):
```bicep
resource networkSecurityGroup 'Microsoft.Network/networkSecurityGroups@2023-04-01' = {
  name: 'app-nsg'
  location: resourceGroup().location
  properties: {
    securityRules: [
      {
        name: 'AllowHTTPSFromLoadBalancer'
        properties: {
          priority: 100
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: 'AzureLoadBalancer'  // Service tag
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          protocol: '*'
          access: 'Deny'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'AllowAzureMonitor'
        properties: {
          priority: 110
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Outbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'AzureMonitor'  // Service tag
          destinationPortRange: '443'
        }
      }
    ]
  }
}
```

---

## 21. Cloud Network Security — GCP

### 21.1 GCP Network Model

```
GCP is fundamentally different from AWS/Azure:
  - VPCs are GLOBAL (not regional)
  - Subnets ARE regional
  - No internet gateway concept (external IPs directly on instances)
  - Andromeda — Google's SDN platform (custom ASICs: Jupiter switches, Orion NICs)

GCP Security Stack:
  Cloud Armor (WAF + DDoS) → Load Balancer → VPC
  
  VPC Firewall Rules (global, tag-based OR service-account-based)
    Priority 0-65535 (lower = higher priority)
    Allow/Deny
    Ingress/Egress
    L4: protocol + ports
    Source: CIDR, service account, network tag
  
  Hierarchical Firewall Policies:
    Organization → Folder → Project → VPC → instance
    Evaluated top-down; "goto_next" delegates to lower policy
    
  VPC Service Controls:
    Data exfiltration protection for GCP APIs
    Creates a security perimeter around GCP services
    Blocks API calls from outside perimeter even with valid credentials

Andromeda virtual network:
  - All packet processing in software on host hardware
  - Custom NICs (Orion) handle encap/decap in hardware offload
  - Maglev: consistent hashing load balancer at line rate
  - Jupiter: custom data-center fabric switches (40Tbps per rack)
```

VPC Firewall (gcloud):
```bash
# Create firewall rule using service account identity (not network tags - more secure)
gcloud compute firewall-rules create allow-app-to-db \
    --network=prod-vpc \
    --direction=INGRESS \
    --priority=1000 \
    --action=ALLOW \
    --rules=tcp:5432 \
    --source-service-accounts=app-sa@project.iam.gserviceaccount.com \
    --target-service-accounts=db-sa@project.iam.gserviceaccount.com

# Enable VPC Flow Logs
gcloud compute networks subnets update app-subnet \
    --region=us-central1 \
    --enable-flow-logs \
    --logging-aggregation-interval=interval-5-sec \
    --logging-flow-sampling=0.5 \
    --logging-metadata=include-all

# VPC Service Controls perimeter
gcloud access-context-manager perimeters create prod-perimeter \
    --title="Production Perimeter" \
    --resources=projects/123456789 \
    --restricted-services=storage.googleapis.com,bigquery.googleapis.com \
    --policy=1234567890

# Private Google Access (reach Google APIs without internet)
gcloud compute networks subnets update app-subnet \
    --region=us-central1 \
    --enable-private-ip-google-access
```

---

## 22. Kubernetes Network Security

### 22.1 Kubernetes Network Model

```
K8s networking fundamentals:
  - Every pod gets a unique routable IP
  - Pods can communicate without NAT (within cluster)
  - Nodes can communicate with all pods
  - Default: no network isolation (flat L3 network)

Container Network Interface (CNI):
  Plugin interface between kubelet and network implementation
  Examples: Cilium, Calico, Flannel, WeaveNet, AWS VPC CNI

NetworkPolicy (K8s built-in):
  - Requires CNI that implements it (Calico, Cilium — yes; Flannel — no)
  - Namespace-scoped
  - Selects pods via labels
  - Default: if no NetworkPolicy selects a pod → allow all
  - Once a NetworkPolicy selects a pod → deny all not explicitly allowed

Cilium eBPF enforcement vs iptables:
  iptables approach: O(n) rule scan per packet, kernel path
  Cilium eBPF:       O(1) map lookup, runs at XDP/TC level
                     Can enforce identity-based (SPIFFE, not just IP)
                     Service mesh without sidecar overhead
```

### 22.2 NetworkPolicy — Production Patterns

```yaml
# Default deny-all for namespace (establish baseline)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}   # Selects ALL pods
  policyTypes:
  - Ingress
  - Egress
---
# Allow specific service-to-service traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
      tier: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
      namespaceSelector:
        matchLabels:
          environment: production
    ports:
    - protocol: TCP
      port: 8080
---
# Allow egress to DNS and specific external services only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:  # Allow DNS
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
  - to:  # Allow to database tier
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 22.3 Cilium Network Policy (L7-aware)

```yaml
# Cilium CiliumNetworkPolicy: L7 HTTP filtering
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: http-policy
  namespace: production
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
        - method: "GET"
          path: "^/api/v1/public/.*"
        - method: "POST"
          path: "^/api/v1/orders$"
          headers:
          - "Content-Type: application/json"
  egress:
  - toFQDNs:   # DNS-based policy (Cilium resolves and tracks IPs)
    - matchName: "api.stripe.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

### 22.4 Pod Security — seccomp, AppArmor, Seccomp

```yaml
# Pod security context with network restrictions
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: runtime/default
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10000
    runAsGroup: 10000
    seccompProfile:
      type: RuntimeDefault   # Seccomp: deny unknown syscalls
    sysctls:
    - name: net.ipv4.tcp_syncookies
      value: "1"
  
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL              # Drop ALL capabilities
        add:
        - NET_BIND_SERVICE  # Only if port < 1024 needed
    
    # Don't use host network - isolates in pod's netns
    # hostNetwork: false (default)
    # hostPID: false (default)
    # hostIPC: false (default)
```

---

## 23. Service Mesh Security (Envoy/Istio)

### 23.1 Envoy Proxy Security Architecture

```
Envoy as security enforcement point:

  Inbound path:
  [External] → [Listener] → [Filter Chain] → [HTTP Connection Manager]
                               │
                     ┌─────────▼──────────┐
                     │ Transport Socket:   │
                     │ DownstreamTLSContext│
                     │ mTLS verification   │
                     │ SPIFFE validation   │
                     └─────────┬──────────┘
                               │
                     ┌─────────▼──────────┐
                     │ HTTP Filters:       │
                     │ JWT authentication  │
                     │ Rate limiting       │
                     │ RBAC authorization  │
                     │ External authz (OPA)│
                     └─────────────────────┘

  Outbound path:
  [Service] → [Cluster] → [Transport Socket: UpstreamTLSContext]
                                               (mTLS origination)
```

Envoy xDS configuration (YAML representation):
```yaml
# Listener with mTLS and JWT auth
listeners:
- name: inbound_listener
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 15006
  filter_chains:
  - transport_socket:
      name: envoy.transport_sockets.tls
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
        require_client_certificate: true
        common_tls_context:
          tls_certificate_sds_secret_configs:
          - name: "ROOTCA"
            sds_config:
              api_config_source:
                api_type: GRPC
                grpc_services:
                - envoy_grpc:
                    cluster_name: sds_server  # SPIRE agent SDS endpoint
          validation_context_sds_secret_config:
            name: "ROOTCA"
            sds_config: ...
          # TLS 1.3 only
          tls_params:
            tls_minimum_protocol_version: TLSv1_3
            cipher_suites:
            - TLS_AES_256_GCM_SHA384
            - TLS_CHACHA20_POLY1305_SHA256
    filters:
    - name: envoy.filters.network.http_connection_manager
      typed_config:
        http_filters:
        # JWT Authentication
        - name: envoy.filters.http.jwt_authn
          typed_config:
            providers:
              jwt_provider:
                issuer: "https://auth.example.com"
                audiences: ["api.example.com"]
                remote_jwks:
                  http_uri:
                    uri: "https://auth.example.com/.well-known/jwks.json"
                    cluster: jwks_cluster
                    timeout: 1s
        
        # RBAC Authorization
        - name: envoy.filters.http.rbac
          typed_config:
            rules:
              action: ALLOW
              policies:
                "allow-frontend":
                  principals:
                  - authenticated:
                      principal_name:
                        exact: "spiffe://cluster.local/ns/prod/sa/frontend"
                  permissions:
                  - and_rules:
                      rules:
                      - header:
                          name: ":method"
                          exact_match: "POST"
                      - url_path:
                          path:
                            prefix: "/api/orders"
        
        - name: envoy.filters.http.router
```

---

## 24. C Implementations: Raw Socket Security Tools

### 24.1 Network Packet Analyzer (C)

```c
// File: packet_capture.c
// Minimal libpcap-based packet capture with protocol dissection
// Compile: gcc -O2 -o packet_capture packet_capture.c -lpcap
// Run: sudo ./packet_capture eth0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/ip_icmp.h>
#include <netinet/if_ether.h>
#include <pcap/pcap.h>

#define SNAP_LEN 65535
#define PROMISC  1
#define TIMEOUT_MS 1000

static uint64_t packet_count = 0;
static uint64_t tcp_count = 0;
static uint64_t udp_count = 0;
static uint64_t dropped_count = 0;

static void process_tcp(const struct iphdr *iph, 
                         const uint8_t *packet, int len)
{
    const struct tcphdr *tcph = 
        (const struct tcphdr *)((const uint8_t *)iph + (iph->ihl * 4));
    
    if ((const uint8_t *)(tcph + 1) > packet + len)
        return;
    
    char src[INET_ADDRSTRLEN], dst[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &iph->saddr, src, sizeof(src));
    inet_ntop(AF_INET, &iph->daddr, dst, sizeof(dst));
    
    // Flag analysis
    char flags[16] = "";
    if (tcph->syn) strcat(flags, "S");
    if (tcph->ack) strcat(flags, "A");
    if (tcph->fin) strcat(flags, "F");
    if (tcph->rst) strcat(flags, "R");
    if (tcph->psh) strcat(flags, "P");
    if (tcph->urg) strcat(flags, "U");
    if (!flags[0]) strcpy(flags, "-");
    
    // Detect suspicious flag combinations
    const char *warning = "";
    if (tcph->syn && tcph->fin)  warning = " [SUSPICIOUS:SYN+FIN]";
    if (tcph->syn && tcph->rst)  warning = " [SUSPICIOUS:SYN+RST]";
    if (!tcph->syn && !tcph->ack && !tcph->fin && 
        !tcph->rst && !tcph->psh && !tcph->urg)
        warning = " [SUSPICIOUS:NULL]";
    if (tcph->fin && tcph->psh && tcph->urg) warning = " [SUSPICIOUS:XMAS]";
    
    printf("TCP %s:%d → %s:%d [%s] seq=%u ack=%u win=%u%s\n",
           src, ntohs(tcph->source),
           dst, ntohs(tcph->dest),
           flags,
           ntohl(tcph->seq),
           ntohl(tcph->ack_seq),
           ntohs(tcph->window),
           warning);
    
    tcp_count++;
}

static void process_udp(const struct iphdr *iph,
                         const uint8_t *packet, int len)
{
    const struct udphdr *udph =
        (const struct udphdr *)((const uint8_t *)iph + (iph->ihl * 4));
    
    if ((const uint8_t *)(udph + 1) > packet + len)
        return;
    
    char src[INET_ADDRSTRLEN], dst[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &iph->saddr, src, sizeof(src));
    inet_ntop(AF_INET, &iph->daddr, dst, sizeof(dst));
    
    printf("UDP %s:%d → %s:%d len=%u\n",
           src, ntohs(udph->source),
           dst, ntohs(udph->dest),
           ntohs(udph->len));
    
    udp_count++;
}

static void packet_handler(u_char *user, 
                             const struct pcap_pkthdr *header,
                             const u_char *packet)
{
    (void)user;
    packet_count++;
    
    if (header->caplen < sizeof(struct ethhdr))
        return;
    
    const struct ethhdr *eth = (const struct ethhdr *)packet;
    
    // Only process IPv4
    if (ntohs(eth->h_proto) != ETH_P_IP)
        return;
    
    const struct iphdr *iph = 
        (const struct iphdr *)(packet + sizeof(struct ethhdr));
    
    if ((const uint8_t *)(iph + 1) > packet + header->caplen)
        return;
    
    // Validate IP header
    if (iph->version != 4 || iph->ihl < 5)
        return;
    
    uint16_t ip_total = ntohs(iph->tot_len);
    if (ip_total > header->caplen - sizeof(struct ethhdr))
        return;
    
    switch (iph->protocol) {
        case IPPROTO_TCP:
            process_tcp(iph, packet, header->caplen);
            break;
        case IPPROTO_UDP:
            process_udp(iph, packet, header->caplen);
            break;
        default:
            break;
    }
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <interface> [filter]\n", argv[0]);
        return 1;
    }
    
    char errbuf[PCAP_ERRBUF_SIZE];
    
    pcap_t *handle = pcap_open_live(argv[1], SNAP_LEN, PROMISC,
                                     TIMEOUT_MS, errbuf);
    if (!handle) {
        fprintf(stderr, "pcap_open_live(%s): %s\n", argv[1], errbuf);
        return 1;
    }
    
    // Compile and set BPF filter
    const char *filter_str = argc > 2 ? argv[2] : "ip";
    struct bpf_program fp;
    bpf_u_int32 net = 0, mask = 0;
    
    pcap_lookupnet(argv[1], &net, &mask, errbuf);
    
    if (pcap_compile(handle, &fp, filter_str, 0, net) < 0) {
        fprintf(stderr, "pcap_compile: %s\n", pcap_geterr(handle));
        pcap_close(handle);
        return 1;
    }
    
    if (pcap_setfilter(handle, &fp) < 0) {
        fprintf(stderr, "pcap_setfilter: %s\n", pcap_geterr(handle));
        pcap_freecode(&fp);
        pcap_close(handle);
        return 1;
    }
    
    pcap_freecode(&fp);
    
    printf("Capturing on %s with filter: %s\n", argv[1], filter_str);
    
    // Capture packets
    pcap_loop(handle, 0, packet_handler, NULL);
    
    // Print stats
    struct pcap_stat stats;
    if (pcap_stats(handle, &stats) == 0) {
        printf("\n--- Capture Statistics ---\n");
        printf("Packets received: %u\n", stats.ps_recv);
        printf("Packets dropped (kernel): %u\n", stats.ps_drop);
        printf("Packets dropped (iface): %u\n", stats.ps_ifdrop);
        printf("TCP: %lu, UDP: %lu\n", tcp_count, udp_count);
    }
    
    pcap_close(handle);
    return 0;
}
```

### 24.2 Port Scanner with Rate Limiting (C)

```c
// File: portscan.c  
// SYN scanner for security assessment (use only on authorized systems)
// Compile: gcc -O2 -o portscan portscan.c -lpthread
// Run: sudo ./portscan 192.168.1.1 1 1024

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>

#define MAX_THREADS 128
#define CONNECT_TIMEOUT_MS 500

struct scan_task {
    const char *target_ip;
    int start_port;
    int end_port;
    int *open_ports;
    int open_count;
    pthread_mutex_t *mutex;
};

static int tcp_connect_probe(const char *ip, int port, int timeout_ms)
{
    int sock = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
    if (sock < 0)
        return -1;
    
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons((uint16_t)port),
    };
    inet_pton(AF_INET, ip, &addr.sin_addr);
    
    int result = -1;
    int ret = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
    
    if (ret == 0) {
        result = 1;  // connected immediately (rare)
    } else if (errno == EINPROGRESS) {
        struct pollfd pfd = { .fd = sock, .events = POLLOUT | POLLERR };
        ret = poll(&pfd, 1, timeout_ms);
        
        if (ret == 1) {
            int err = 0;
            socklen_t len = sizeof(err);
            getsockopt(sock, SOL_SOCKET, SO_ERROR, &err, &len);
            result = (err == 0) ? 1 : 0;  // 1=open, 0=refused/filtered
        } else if (ret == 0) {
            result = 0;  // timeout → filtered
        }
    }
    
    close(sock);
    return result;
}

static void *scan_range(void *arg)
{
    struct scan_task *task = (struct scan_task *)arg;
    
    for (int port = task->start_port; port <= task->end_port; port++) {
        int status = tcp_connect_probe(task->target_ip, port, CONNECT_TIMEOUT_MS);
        
        if (status == 1) {
            pthread_mutex_lock(task->mutex);
            task->open_ports[task->open_count++] = port;
            printf("  OPEN: %s:%d\n", task->target_ip, port);
            pthread_mutex_unlock(task->mutex);
        }
    }
    
    return NULL;
}

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <ip> <start_port> <end_port>\n", argv[0]);
        return 1;
    }
    
    const char *target = argv[1];
    int start = atoi(argv[2]);
    int end   = atoi(argv[3]);
    
    if (start < 1 || end > 65535 || start > end) {
        fprintf(stderr, "Invalid port range\n");
        return 1;
    }
    
    int total = end - start + 1;
    int threads = (total < MAX_THREADS) ? total : MAX_THREADS;
    int ports_per_thread = total / threads;
    
    int *open_ports = calloc(total, sizeof(int));
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    struct scan_task *tasks = calloc(threads, sizeof(struct scan_task));
    pthread_t *tids = calloc(threads, sizeof(pthread_t));
    
    printf("Scanning %s ports %d-%d with %d threads\n",
           target, start, end, threads);
    
    struct timeval t0;
    gettimeofday(&t0, NULL);
    
    for (int i = 0; i < threads; i++) {
        tasks[i].target_ip  = target;
        tasks[i].start_port = start + (i * ports_per_thread);
        tasks[i].end_port   = (i == threads - 1) ?
                               end : (start + (i + 1) * ports_per_thread - 1);
        tasks[i].open_ports = open_ports;
        tasks[i].open_count = 0;
        tasks[i].mutex      = &mutex;
        pthread_create(&tids[i], NULL, scan_range, &tasks[i]);
    }
    
    for (int i = 0; i < threads; i++)
        pthread_join(tids[i], NULL);
    
    struct timeval t1;
    gettimeofday(&t1, NULL);
    double elapsed = (t1.tv_sec - t0.tv_sec) + 
                     (t1.tv_usec - t0.tv_usec) / 1e6;
    
    printf("\nScan completed in %.2fs\n", elapsed);
    
    free(open_ports);
    free(tasks);
    free(tids);
    pthread_mutex_destroy(&mutex);
    
    return 0;
}
```

---

## 25. Rust Implementations: Network Security Libraries

### 25.1 Async TCP Proxy with mTLS and Rate Limiting

```rust
// File: src/main.rs
// Secure TLS-terminating proxy with rate limiting and access control
// Build: cargo build --release
// Deps: tokio, tokio-rustls, rustls, dashmap

use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};

use dashmap::DashMap;
use tokio::io::{self, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::Semaphore;
use tokio::time::timeout;
use tokio_rustls::TlsAcceptor;

/// Per-IP rate limiter using token bucket algorithm
#[derive(Debug)]
struct TokenBucket {
    tokens: f64,
    last_refill: Instant,
    capacity: f64,
    refill_rate: f64,  // tokens per second
}

impl TokenBucket {
    fn new(capacity: f64, refill_rate: f64) -> Self {
        Self {
            tokens: capacity,
            last_refill: Instant::now(),
            capacity,
            refill_rate,
        }
    }
    
    fn try_consume(&mut self, amount: f64) -> bool {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        
        // Refill tokens based on elapsed time
        self.tokens = (self.tokens + elapsed * self.refill_rate)
            .min(self.capacity);
        self.last_refill = now;
        
        if self.tokens >= amount {
            self.tokens -= amount;
            true
        } else {
            false
        }
    }
}

/// Rate limiter shared across all connections
struct RateLimiter {
    buckets: DashMap<std::net::IpAddr, TokenBucket>,
    max_ips: usize,
    capacity: f64,
    refill_rate: f64,
}

impl RateLimiter {
    fn new(max_ips: usize, capacity: f64, refill_rate: f64) -> Self {
        Self {
            buckets: DashMap::with_capacity(max_ips),
            max_ips,
            capacity,
            refill_rate,
        }
    }
    
    fn check(&self, ip: std::net::IpAddr) -> bool {
        // Evict if at capacity (simple strategy: just deny)
        if self.buckets.len() >= self.max_ips && !self.buckets.contains_key(&ip) {
            return false;
        }
        
        let mut bucket = self.buckets
            .entry(ip)
            .or_insert_with(|| TokenBucket::new(self.capacity, self.refill_rate));
        
        bucket.try_consume(1.0)
    }
}

/// Connection handler: proxy client to backend with logging
async fn handle_connection(
    client_stream: tokio_rustls::server::TlsStream<TcpStream>,
    peer_addr: SocketAddr,
    backend_addr: SocketAddr,
    semaphore: Arc<Semaphore>,
) -> io::Result<()> {
    let _permit = semaphore.try_acquire().map_err(|_| {
        io::Error::new(io::ErrorKind::ConnectionRefused, "max connections exceeded")
    })?;
    
    // Extract client identity from TLS session
    let (_, server_conn) = client_stream.get_ref();
    let client_identity = server_conn
        .peer_certificates()
        .and_then(|certs| certs.first())
        .map(|cert| format!("{} bytes cert", cert.len()))
        .unwrap_or_else(|| "anonymous".to_string());
    
    tracing::info!(
        peer = %peer_addr,
        identity = %client_identity,
        "connection accepted"
    );
    
    // Connect to backend
    let backend = timeout(
        Duration::from_secs(5),
        TcpStream::connect(backend_addr),
    )
    .await
    .map_err(|_| io::Error::new(io::ErrorKind::TimedOut, "backend connect timeout"))?
    .map_err(|e| {
        tracing::error!(error = %e, "backend connect failed");
        e
    })?;
    
    // Bidirectional copy
    let (mut client_read, mut client_write) = io::split(client_stream);
    let (mut backend_read, mut backend_write) = backend.into_split();
    
    let client_to_backend = io::copy(&mut client_read, &mut backend_write);
    let backend_to_client = io::copy(&mut backend_read, &mut client_write);
    
    let (bytes_up, bytes_down) = tokio::try_join!(client_to_backend, backend_to_client)
        .unwrap_or((0, 0));
    
    tracing::info!(
        peer = %peer_addr,
        bytes_up = bytes_up,
        bytes_down = bytes_down,
        "connection closed"
    );
    
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::init();
    
    let tls_config = build_tls_config(
        "certs/proxy.crt",
        "certs/proxy.key",
        Some("certs/ca.crt"),
    )?;
    
    let acceptor = TlsAcceptor::from(tls_config);
    let listener = TcpListener::bind("0.0.0.0:8443").await?;
    
    let backend_addr: SocketAddr = "127.0.0.1:8080".parse()?;
    let rate_limiter = Arc::new(RateLimiter::new(10_000, 100.0, 10.0));
    let semaphore = Arc::new(Semaphore::new(1000));  // max 1000 concurrent conns
    
    tracing::info!("Proxy listening on 0.0.0.0:8443");
    
    loop {
        let (tcp_stream, peer_addr) = listener.accept().await?;
        
        // Rate limit check before TLS handshake (saves resources)
        if !rate_limiter.check(peer_addr.ip()) {
            tracing::warn!(peer = %peer_addr, "rate limited");
            // Drop connection silently (don't give attacker feedback)
            drop(tcp_stream);
            continue;
        }
        
        let acceptor = acceptor.clone();
        let semaphore = semaphore.clone();
        
        tokio::spawn(async move {
            match timeout(Duration::from_secs(10), acceptor.accept(tcp_stream)).await {
                Ok(Ok(tls_stream)) => {
                    if let Err(e) = handle_connection(
                        tls_stream,
                        peer_addr,
                        backend_addr,
                        semaphore,
                    ).await {
                        tracing::error!(peer = %peer_addr, error = %e);
                    }
                }
                Ok(Err(e)) => {
                    tracing::warn!(peer = %peer_addr, error = %e, "TLS handshake failed");
                }
                Err(_) => {
                    tracing::warn!(peer = %peer_addr, "TLS handshake timeout");
                }
            }
        });
    }
}
```

### 25.2 Network Scanner (Rust, Async)

```rust
// File: src/scanner.rs
// Async TCP port scanner with timeout and CIDR support
// Cargo.toml: tokio = {version="1", features=["full"]}, ipnetwork = "0.20"

use std::net::{IpAddr, SocketAddr};
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::time::timeout;
use tokio::sync::Semaphore;
use std::sync::Arc;
use ipnetwork::IpNetwork;

const CONNECT_TIMEOUT: Duration = Duration::from_millis(500);
const MAX_CONCURRENT: usize = 1000;

#[derive(Debug, Clone)]
pub struct ScanResult {
    pub addr: SocketAddr,
    pub open: bool,
    pub error: Option<String>,
}

/// Probe a single TCP port
async fn probe(addr: SocketAddr) -> ScanResult {
    match timeout(CONNECT_TIMEOUT, TcpStream::connect(addr)).await {
        Ok(Ok(_)) => ScanResult { addr, open: true, error: None },
        Ok(Err(e)) => ScanResult {
            addr,
            open: false,
            error: Some(e.to_string()),
        },
        Err(_) => ScanResult {
            addr,
            open: false,
            error: Some("timeout".to_string()),
        },
    }
}

/// Scan a single host for multiple ports
pub async fn scan_host(ip: IpAddr, ports: &[u16]) -> Vec<ScanResult> {
    let sem = Arc::new(Semaphore::new(MAX_CONCURRENT));
    let mut handles = Vec::with_capacity(ports.len());
    
    for &port in ports {
        let addr = SocketAddr::new(ip, port);
        let sem = sem.clone();
        
        handles.push(tokio::spawn(async move {
            let _permit = sem.acquire().await.expect("semaphore closed");
            probe(addr).await
        }));
    }
    
    let mut results = Vec::with_capacity(ports.len());
    for handle in handles {
        if let Ok(result) = handle.await {
            results.push(result);
        }
    }
    
    results
}

/// Scan a CIDR range
pub async fn scan_network(
    network: &str,
    ports: Vec<u16>,
) -> Result<Vec<ScanResult>, Box<dyn std::error::Error>> {
    let net: IpNetwork = network.parse()?;
    let sem = Arc::new(Semaphore::new(MAX_CONCURRENT));
    let ports = Arc::new(ports);
    let mut handles = Vec::new();
    
    for ip in net.iter() {
        let ports = ports.clone();
        let sem = sem.clone();
        
        handles.push(tokio::spawn(async move {
            let mut host_results = Vec::new();
            for &port in ports.iter() {
                let addr = SocketAddr::new(ip, port);
                let sem = sem.clone();
                let _permit = sem.acquire().await.expect("semaphore closed");
                let result = probe(addr).await;
                if result.open {
                    host_results.push(result);
                }
            }
            host_results
        }));
    }
    
    let mut all_results = Vec::new();
    for handle in handles {
        if let Ok(results) = handle.await {
            all_results.extend(results);
        }
    }
    
    Ok(all_results)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let target_network = "192.168.1.0/24";
    let ports = vec![22, 80, 443, 8080, 8443, 3306, 5432, 6379, 27017];
    
    println!("Scanning {} for ports {:?}", target_network, ports);
    
    let results = scan_network(target_network, ports).await?;
    
    for r in &results {
        println!("OPEN: {}", r.addr);
    }
    
    println!("\n{} open ports found", results.len());
    
    Ok(())
}
```

---

## 26. Threat Modeling: STRIDE per Layer

### 26.1 STRIDE Applied to Network Stack

```
STRIDE: Spoofing, Tampering, Repudiation, Info Disclosure, Denial of Service, Elevation of Privilege

Layer 2 (Data Link):
  S: MAC spoofing, ARP spoofing → Mitigate: 802.1X, DAI
  T: ARP cache poisoning, STP manipulation → Mitigate: DAI, BPDU Guard
  R: No L2 audit trail → Mitigate: sFlow/IPFIX logging
  I: VLAN hopping, monitor mode capture → Mitigate: private VLANs, MACsec
  D: MAC flood (CAM overflow), broadcast storm → Mitigate: port security, storm control
  E: VLAN privilege escalation → Mitigate: strict VLAN access control

Layer 3 (Network):
  S: IP spoofing → Mitigate: uRPF, BCP38 at network edge
  T: ICMP redirect, BGP route injection → Mitigate: disable ICMP redirects, RPKI
  R: No native attribution → Mitigate: NetFlow/IPFIX with authentication
  I: Traffic interception (on-path) → Mitigate: encryption (IPsec, TLS)
  D: Smurf attack, ICMP flood, fragmentation → Mitigate: rate limiting, BCP84
  E: Route manipulation → Mitigate: RPKI, route filtering

Layer 4 (Transport):
  S: TCP session hijacking → Mitigate: cryptographic ISNs, TCP-AO
  T: TCP data injection → Mitigate: TLS/AEAD
  R: No native attribution → Mitigate: audit logging, SIEM
  I: Traffic analysis (patterns, timing) → Mitigate: traffic padding, Tor-style
  D: SYN flood, ACK flood, RESET attack → Mitigate: SYN cookies, stateful FW
  E: Port bypass via fragmentation → Mitigate: reassembly before filtering

Layer 7 (Application):
  S: DNS spoofing, session hijacking → Mitigate: DNSSEC, HSTS, secure cookies
  T: HTTP request smuggling, parameter tampering → Mitigate: WAF, input validation
  R: Insufficient logging → Mitigate: audit logs with HMAC, immutable log storage
  I: Cleartext protocols (HTTP, SMTP no STARTTLS) → Mitigate: TLS everywhere
  D: Slowloris, application flood → Mitigate: timeouts, rate limiting, WAF
  E: SQL injection, RCE via deserialization → Mitigate: WAF, code review, sandboxing
```

### 26.2 Attack Tree: Compromising Network Communications

```
Goal: Read confidential traffic between Service A and Service B

├── Break encryption
│   ├── Compromise private key (key exfiltration)
│   │   ├── Steal from disk (weak file permissions → chmod 600)
│   │   ├── Steal from memory (process dump, core file)
│   │   └── Steal from HSM (requires physical access or HSM bug)
│   ├── Cryptographic weakness
│   │   ├── Weak cipher (e.g., 3DES, RC4) → enforce TLS 1.3 only
│   │   ├── Weak PRF/hash (MD5, SHA1) → enforce SHA-256+
│   │   └── Implementation bug (OpenSSL CVE-2014-0160 Heartbleed)
│   └── CA compromise (MITM with fraudulent cert)
│       ├── Rogue CA issues cert for your domain
│       ├── Mitigation: Certificate Pinning, HPKP, CT logs
│       └── Mitigation: Private PKI (don't trust public CAs internally)
│
├── Position on network path
│   ├── BGP hijack (steal prefix)
│   ├── ARP poisoning (L2 MITM)
│   ├── DNS hijacking (redirect to attacker's IP)
│   ├── Rogue wireless AP
│   └── Compromised intermediate network device (router, switch)
│
└── Traffic analysis (even without decryption)
    ├── Timing analysis (correlate request/response times)
    ├── Size analysis (infer content from packet sizes)
    ├── Flow analysis (communication patterns, graph analysis)
    └── Mitigation: traffic padding, constant-bitrate tunnels (noisy but effective)
```

---

## 27. Testing, Fuzzing, Benchmarking

### 27.1 Network Stack Fuzzing

```bash
# Fuzzing with AFL++ targeting network protocol parsers
apt install afl++

# Write a test harness for your protocol parser
cat > fuzz_http_parser.c << 'EOF'
#include "http_parser.h"
#include <stdlib.h>
#include <string.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    
    // Fuzz target: HTTP request parser
    struct http_request req;
    http_parse_request(data, size, &req);
    
    return 0;
}
EOF

# Compile with AFL++ instrumentation
afl-clang-fast -O2 -o fuzz_http_parser fuzz_http_parser.c http_parser.c

# Create seed corpus
mkdir -p corpus
echo -e "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n" > corpus/get_request.bin
echo -e "POST /api HTTP/1.1\r\nContent-Length: 4\r\n\r\ndata" > corpus/post_request.bin

# Run fuzzer
AFL_SKIP_CPUFREQ=1 afl-fuzz -i corpus -o findings -m none -- ./fuzz_http_parser @@

# Minimize corpus
afl-cmin -i findings/queue -o corpus_min -- ./fuzz_http_parser @@

# Cargo-fuzz for Rust
cargo install cargo-fuzz

# In your Rust project:
cargo fuzz init
cargo fuzz add packet_parser

# fuzz/fuzz_targets/packet_parser.rs:
# #![no_main]
# use libfuzzer_sys::fuzz_target;
# fuzz_target!(|data: &[u8]| {
#     let _ = my_crate::parse_packet(data);
# });

cargo fuzz run packet_parser -- -max_total_time=3600
```

### 27.2 Network Performance Benchmarking

```bash
# iperf3: measure raw throughput and jitter
# Server:
iperf3 -s -p 5201

# Client: TCP throughput
iperf3 -c server_ip -t 30 -P 4  # 4 parallel streams

# UDP throughput (test for packet loss)
iperf3 -c server_ip -u -b 1G -t 30

# Reverse direction (server to client)
iperf3 -c server_ip -R -t 30

# With specific TOS/DSCP marking
iperf3 -c server_ip --tos 0x28

# nping: network probing (from nmap project)
nping --tcp --flags SYN -p 80 --rate 100 target_ip
nping --udp -p 53 --rate 50 target_ip

# pktgen: kernel packet generator (up to line rate)
modprobe pktgen
echo "rem_device_all" > /proc/net/pktgen/pgctrl
echo "add_device eth0@0" > /proc/net/pktgen/pgctrl

cat > /proc/net/pktgen/eth0@0 << 'EOF'
count 10000000
clone_skb 1
pkt_size 64
delay 0
dst 192.168.1.1
dst_mac 00:11:22:33:44:55
src 192.168.1.100
EOF

echo "start" > /proc/net/pktgen/pgctrl
cat /proc/net/pktgen/eth0@0  # view results

# tc netem: simulate network impairments for testing
# Add 100ms delay, 10ms jitter, 1% packet loss
tc qdisc add dev eth0 root netem \
    delay 100ms 10ms 25% \
    loss 1% 25% \
    corrupt 0.1% \
    reorder 5% 50%

# Remove
tc qdisc del dev eth0 root

# Rust network benchmarks (criterion)
# In benches/bench_parser.rs:
# use criterion::{criterion_group, criterion_main, Criterion};
# fn bench_packet_parse(c: &mut Criterion) {
#     let pkt = include_bytes!("fixtures/sample_packet.bin");
#     c.bench_function("parse_packet", |b| b.iter(|| parse_packet(pkt)));
# }
```

### 27.3 Security Testing

```bash
# testssl.sh: comprehensive TLS testing
./testssl.sh --full --vulnerable --long https://your-server:8443

# Key checks:
# - Protocol versions (reject SSLv3, TLS 1.0, TLS 1.1)
# - Cipher suites (reject NULL, EXPORT, DES, RC4, 3DES, ANON)
# - Certificate chain validation
# - HSTS, HPKP, CSP headers
# - BEAST, POODLE, HEARTBLEED, DROWN, LOGJAM, FREAK vulnerabilities

# nmap security scanning
nmap -sV -sC -O --script vuln target_ip
nmap -sS -p- --min-rate 1000 target_ip  # SYN scan all ports
nmap -sU -p 53,161,500 target_ip         # UDP scan
nmap --script ssl-cert,ssl-enum-ciphers -p 443 target_ip

# Trivy: container and IaC security scanning
trivy image --severity HIGH,CRITICAL nginx:latest
trivy k8s --report summary cluster

# Kube-bench: CIS Kubernetes benchmark
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs -l app=kube-bench

# Network policy testing
# kubectl-netpol (validate NetworkPolicy behavior)
kubectl netpol verify --pod frontend --pod backend --namespace production

# Cilium connectivity test
cilium connectivity test
```

---

## 28. Production Hardening Checklist

### 28.1 Linux Host Network Hardening

```bash
#!/bin/bash
# /etc/sysctl.d/99-security.conf — complete network hardening

# ===== Anti-Spoofing =====
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.default.rp_filter=1
net.ipv4.conf.all.log_martians=1
net.ipv4.conf.default.log_martians=1

# ===== Source Routing Disable =====
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.default.accept_source_route=0
net.ipv6.conf.all.accept_source_route=0
net.ipv6.conf.default.accept_source_route=0

# ===== ICMP Redirect Disable =====
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.default.accept_redirects=0
net.ipv4.conf.all.secure_redirects=0
net.ipv4.conf.default.secure_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.default.send_redirects=0
net.ipv6.conf.all.accept_redirects=0
net.ipv6.conf.default.accept_redirects=0

# ===== SYN Flood Protection =====
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_max_syn_backlog=4096
net.ipv4.tcp_synack_retries=2
net.ipv4.tcp_syn_retries=3

# ===== TCP Hardening =====
net.ipv4.tcp_timestamps=1              # Needed for PAWS
net.ipv4.tcp_rfc1337=1                 # TIME_WAIT assassination protection
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_keepalive_time=600
net.ipv4.tcp_keepalive_probes=5
net.ipv4.tcp_keepalive_intvl=15
net.ipv4.tcp_tw_reuse=1

# ===== ICMP Rate Limiting =====
net.ipv4.icmp_ratelimit=100
net.ipv4.icmp_echo_ignore_broadcasts=1
net.ipv4.icmp_ignore_bogus_error_responses=1

# ===== IPv6 =====
net.ipv6.conf.all.use_tempaddr=2       # IPv6 privacy extensions
net.ipv6.conf.default.use_tempaddr=2
net.ipv6.conf.all.accept_ra=0          # Disable router advertisements on servers
net.ipv6.conf.default.accept_ra=0

# ===== Network Performance (for high-traffic servers) =====
net.core.rmem_max=67108864
net.core.wmem_max=67108864
net.ipv4.tcp_rmem=4096 65536 67108864
net.ipv4.tcp_wmem=4096 65536 67108864
net.core.netdev_max_backlog=5000
net.ipv4.tcp_mtu_probing=1

# ===== IP Forwarding (OFF on workloads, ON on gateways) =====
net.ipv4.ip_forward=0
net.ipv6.conf.all.forwarding=0
```

### 28.2 Certificate and PKI Best Practices

```
Private PKI checklist:
  □ Root CA: offline, HSM-protected, 4096-bit RSA or P-384 ECDSA
  □ Intermediate CAs: online, HSM-protected, separate per environment
  □ Leaf certs: 90-day maximum validity (SPIRE: 1 hour for workloads)
  □ Key usage constraints: exactly what each cert is authorized for
  □ Extended key usage: clientAuth AND serverAuth for mTLS
  □ CRL/OCSP: published and reachable (OCSP stapling on servers)
  □ CT logs: for publicly-trusted certs
  □ Certificate rotation: automated (cert-manager, SPIRE, Vault PKI)

TLS configuration:
  □ Protocol: TLS 1.3 only (or 1.2 minimum if legacy required)
  □ Ciphers (TLS 1.3): TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256
  □ Ciphers (TLS 1.2 compat): ECDHE-ECDSA-AES256-GCM-SHA384
  □ Session resumption: session tickets with key rotation (or disable)
  □ 0-RTT: disabled for sensitive endpoints
  □ HSTS: max-age=63072000; includeSubDomains; preload
  □ Certificate transparency: expect-ct header
  □ OCSP stapling: enabled
```

### 28.3 Observability for Network Security

```yaml
# Prometheus alerts for network security events

groups:
- name: network_security
  rules:
  - alert: HighConnectionRefusalRate
    expr: |
      rate(node_netstat_Tcp_AttemptFails[5m]) > 100
    for: 2m
    annotations:
      summary: "High TCP connection failure rate - possible scan/flood"
  
  - alert: SYNFloodDetected
    expr: |
      node_netstat_TcpExt_TCPReqQFullDrop > 0
    for: 30s
    annotations:
      summary: "SYN cookies overflow - SYN flood in progress"
  
  - alert: ConntrackTableNearCapacity
    expr: |
      node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8
    for: 1m
    annotations:
      summary: "conntrack table >80% full - risk of connection drop"
  
  - alert: UnexpectedEgressTraffic
    expr: |
      sum by(destination_cidr) (
        rate(cilium_forward_bytes_total{direction="egress",
          destination_cidr!~"10\\..*|172\\.16\\..*|192\\.168\\..*"}[5m])
      ) > 0
    for: 1m
    annotations:
      summary: "Unexpected egress to public IP detected"
```

VPC Flow Log analysis (AWS):
```bash
# Athena query for suspicious traffic analysis
CREATE EXTERNAL TABLE vpc_flow_logs (
  version int, account string, interfaceid string,
  sourceaddress string, destinationaddress string,
  sourceport int, destinationport int, protocol int,
  numpackets bigint, numbytes bigint,
  starttime bigint, endtime bigint,
  action string, logstatus string
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ' '
LOCATION 's3://your-bucket/AWSLogs/account-id/vpcflowlogs/region/';

-- Find port scans: source hitting many destination ports
SELECT sourceaddress, COUNT(DISTINCT destinationport) as unique_ports
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND from_unixtime(starttime) > current_timestamp - interval '1' hour
GROUP BY sourceaddress
HAVING COUNT(DISTINCT destinationport) > 20
ORDER BY unique_ports DESC;

-- Find large data transfers (potential exfiltration)
SELECT sourceaddress, destinationaddress, SUM(numbytes) as total_bytes
FROM vpc_flow_logs
WHERE action = 'ACCEPT'
  AND from_unixtime(starttime) > current_timestamp - interval '1' hour
GROUP BY sourceaddress, destinationaddress
HAVING SUM(numbytes) > 104857600  -- 100MB
ORDER BY total_bytes DESC;
```

---

## 29. References

### Standards and RFCs
- RFC 791: IPv4
- RFC 793: TCP
- RFC 1122: Host Requirements
- RFC 1337: TIME-WAIT assassination
- RFC 3704: BCP38 - Ingress Filtering (anti-spoofing)
- RFC 4271: BGP-4
- RFC 4301: IPsec Architecture
- RFC 4493: AES-CMAC
- RFC 5280: X.509 PKI Certificate
- RFC 5575: BGP Flowspec
- RFC 5925: TCP-AO
- RFC 6347: DTLS 1.2
- RFC 6520: TLS Heartbeat (Heartbleed affected this)
- RFC 7296: IKEv2
- RFC 7858: DNS over TLS
- RFC 8446: TLS 1.3
- RFC 8484: DNS over HTTPS
- RFC 9110: HTTP Semantics
- RFC 9250: DNS over QUIC

### Security Frameworks and Standards
- NIST SP 800-207: Zero Trust Architecture
- NIST SP 800-77: IPsec Guide
- CIS Benchmarks: Linux, Kubernetes, Cloud Providers
- OWASP Top 10, API Security Top 10

### Linux Kernel References
- Linux kernel source: https://elixir.bootlin.com/linux/latest
- Linux Networking Documentation: Documentation/networking/
- eBPF reference: https://docs.kernel.org/bpf/
- netfilter documentation: https://www.netfilter.org/documentation/

### CNCF Projects
- Cilium: https://cilium.io (eBPF networking)
- Falco: https://falco.org (runtime security)
- SPIFFE/SPIRE: https://spiffe.io (workload identity)
- OPA: https://openpolicyagent.org (policy engine)
- Envoy: https://envoyproxy.io (data plane proxy)
- Istio: https://istio.io (service mesh)

### Books
- "TCP/IP Illustrated Vol 1-3" — Stevens
- "The Linux Networking Architecture" — Olaf Kirch & Terry Dawson
- "Network Security Assessment" — McNab (O'Reilly)
- "The Web Application Hacker's Handbook" — Stuttard & Pinto
- "Hacking: The Art of Exploitation" — Erickson
- "Network Warrior" — Donahue

### Tools
- Wireshark/tshark: https://wireshark.org
- Suricata IDS: https://suricata.io
- FRRouting: https://frrouting.org
- StrongSwan (IPsec): https://strongswan.org
- WireGuard: https://wireguard.com
- Routinator (RPKI): https://nlnetlabs.nl/projects/routinator/
- bcc/bpftrace (eBPF): https://github.com/iovisor/bcc
- libbpf: https://github.com/libbpf/libbpf

---

## Architecture Reference: Full Stack View

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER WORKLOAD                                     │
│  Go/Rust/C service  ←mTLS/SPIFFE→  Peer Service                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ UNIX socket / loopback
┌───────────────────────────────▼─────────────────────────────────────────┐
│                        ENVOY SIDECAR                                     │
│  JWT validation │ RBAC authz │ mTLS termination │ Rate limit │ Tracing  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ Veth pair
┌───────────────────────────────▼─────────────────────────────────────────┐
│                    CILIUM / EBPF (per-pod network)                       │
│  XDP: DDoS drop   │  TC: egress filter  │  L7 NetworkPolicy (Cilium)    │
│  Identity: SPIFFE-based (not IP-based)                                   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ Linux bridge / VXLAN
┌───────────────────────────────▼─────────────────────────────────────────┐
│               NODE KERNEL (Linux 6.x)                                   │
│  netns isolation │ nftables │ conntrack │ ip route │ sysctl hardened     │
│  seccomp │ AppArmor/SELinux │ capabilities dropped                       │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ VPC/VLAN encap (VXLAN, Geneve, GRE)
┌───────────────────────────────▼─────────────────────────────────────────┐
│                    SDN UNDERLAY (Cloud VPC / DC Fabric)                  │
│  AWS Nitro/Azure FPGA/GCP Andromeda                                      │
│  Security Groups/NSG │ Flow Logs │ Network Firewall │ WAF                │
│  DDoS scrubbing │ RPKI-validated BGP │ BFD                               │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ Physical
┌───────────────────────────────▼─────────────────────────────────────────┐
│              PHYSICAL FABRIC (DC or Cloud PoP)                           │
│  MACsec (802.1AE) │ 802.1X port auth │ BPDU Guard │ DAI │ uRPF          │
│  BGP with RPKI │ GTSM │ TCP-AO │ Flowspec DDoS response                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*This document covers production-grade network security from silicon to software. Each section assumes you have operator-level access to the relevant systems. Commands marked `sudo` require appropriate privileges. Always test in a non-production environment first. Security configurations are context-dependent — understand the trade-offs before applying.*