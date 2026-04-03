# Application Layer Gateways in Linux: Complete Reference Guide

> **Audience**: Senior systems/security engineers  
> **Scope**: Deep-dive into every ALG available in Linux — kernel internals, nf_conntrack helper framework, netfilter hooks, iptables/nftables integration, protocol-specific mechanics, C and Rust implementations, threat modeling, fuzzing, benchmarking, and production operation.  
> **Kernel version baseline**: Linux 6.x (noted where behavior differs in 4.x/5.x)

---

## Table of Contents

1. [What Is an Application Layer Gateway?](#1-what-is-an-application-layer-gateway)
2. [The Problem ALGs Solve — Deep Protocol Analysis](#2-the-problem-algs-solve)
3. [Linux Kernel Packet Path — Complete Stack](#3-linux-kernel-packet-path)
4. [Netfilter Architecture — Hooks, Tables, and Chains](#4-netfilter-architecture)
5. [Connection Tracking Subsystem (nf_conntrack)](#5-connection-tracking-subsystem)
6. [The nf_conntrack Helper Framework](#6-the-nf_conntrack-helper-framework)
7. [NAT and ALG Interaction](#7-nat-and-alg-interaction)
8. [Every ALG in Linux — Exhaustive Coverage](#8-every-alg-in-linux)
   - 8.1 [FTP ALG](#81-ftp-alg)
   - 8.2 [SIP ALG](#82-sip-alg)
   - 8.3 [H.323 ALG](#83-h323-alg)
   - 8.4 [PPTP ALG](#84-pptp-alg)
   - 8.5 [IRC ALG](#85-irc-alg)
   - 8.6 [TFTP ALG](#86-tftp-alg)
   - 8.7 [SNMP ALG](#87-snmp-alg)
   - 8.8 [Amanda ALG](#88-amanda-alg)
   - 8.9 [NetBIOS ALG](#89-netbios-alg)
   - 8.10 [RTSP ALG](#810-rtsp-alg)
   - 8.11 [DNS ALG](#811-dns-alg)
   - 8.12 [DCCP ALG](#812-dccp-alg)
   - 8.13 [SCTP ALG](#813-sctp-alg)
   - 8.14 [RPC ALG (Sun RPC / ONC RPC)](#814-rpc-alg)
   - 8.15 [MGCP ALG](#815-mgcp-alg)
   - 8.16 [GRE/PPTP helper](#816-grepptp-helper)
   - 8.17 [SANE ALG](#817-sane-alg)
   - 8.18 [Netlink-based Helpers (CT Helpers via userspace)](#818-netlink-based-helpers)
9. [Userspace ALG Frameworks](#9-userspace-alg-frameworks)
   - 9.1 [nf_queue + libnetfilter_queue](#91-nf_queue--libnetfilter_queue)
   - 9.2 [conntrack-tools (conntrackd)](#92-conntrack-tools)
   - 9.3 [nftables ct helper](#93-nftables-ct-helper)
   - 9.4 [Suricata as ALG](#94-suricata-as-alg)
   - 9.5 [Zeek / Bro](#95-zeek--bro)
10. [Other Linux ALG Implementations Beyond Netfilter](#10-other-linux-alg-implementations-beyond-netfilter)
    - 10.1 [squid proxy ALG behavior](#101-squid-proxy-alg-behavior)
    - 10.2 [HAProxy L7 inspection](#102-haproxy-l7-inspection)
    - 10.3 [Envoy proxy ALG](#103-envoy-proxy-alg)
    - 10.4 [eBPF-based ALG (sk_msg, sk_skb)](#104-ebpf-based-alg)
    - 10.5 [XDP ALG patterns](#105-xdp-alg-patterns)
    - 10.6 [DPDK-based ALGs](#106-dpdk-based-algs)
    - 10.7 [strongSwan / libreswan IKE ALG](#107-strongswan--libreswan-ike-alg)
    - 10.8 [OpenVPN ALG behavior](#108-openvpn-alg-behavior)
11. [C Implementation — Full ALG Framework](#11-c-implementation)
12. [Rust Implementation — Full ALG Framework](#12-rust-implementation)
13. [iptables/nftables Configuration — Complete Reference](#13-iptablesnftables-configuration)
14. [Threat Model + Attack Surface Analysis](#14-threat-model)
15. [Security Hardening](#15-security-hardening)
16. [Performance Analysis, Benchmarking, and Tuning](#16-performance-analysis)
17. [Fuzzing ALG Parsers](#17-fuzzing-alg-parsers)
18. [Production Operations — Observability, Rollout, Rollback](#18-production-operations)
19. [Architecture Views](#19-architecture-views)
20. [References and Further Reading](#20-references)

---

## 1. What Is an Application Layer Gateway?

### 1.1 Definition

An **Application Layer Gateway (ALG)** — also called an **Application Level Gateway** — is a software component that operates at OSI Layer 7 (Application layer) and performs **stateful protocol inspection and transformation** on traffic passing through a network boundary device such as a firewall, NAT gateway, or proxy.

Unlike a simple packet filter (L3/L4) that only examines IP addresses, ports, and transport flags, an ALG:

1. **Parses application-layer protocol messages** (e.g., SIP INVITE, FTP PORT command, H.225 Setup)
2. **Extracts embedded addressing information** — IP addresses and ports that are encoded inside the payload
3. **Rewrites those embedded addresses** when NAT is active
4. **Creates expectation entries** (conntrack expectations) so that secondary/data connections are permitted through the firewall automatically
5. **Maintains protocol state machines** to correlate requests with responses

The critical insight is that many protocols were designed in an era when NAT did not exist (IETF RFC 793 TCP dates to 1981, FTP RFC 959 to 1985). These protocols embed transport-layer addressing (IP:port tuples) inside their application payload. When a NAT device rewrites the IP header, those embedded addresses become stale, breaking the protocol. ALGs fix this.

### 1.2 The Three Core ALG Functions

```
Function 1: Protocol State Tracking
  - Follow the protocol state machine
  - Correlate control connection with data connections
  - Maintain session context across multiple packets

Function 2: Payload Inspection and Address Extraction
  - Deep-parse protocol messages
  - Extract embedded IP:port tuples from payload
  - Understand protocol encoding (ASCII, BER/DER, binary)

Function 3: NAT Fixup and Expectation Creation
  - Rewrite embedded addresses to match post-NAT reality
  - Register conntrack expectations for secondary flows
  - Handle IP checksum recalculation after payload modification
```

### 1.3 ALG vs. Proxy vs. Deep Packet Inspection

These terms are often confused. Here is the precise distinction:

| Concept | Terminates connection? | Rewrites payload? | Creates expectations? | Protocol-aware? |
|---------|------------------------|-------------------|----------------------|----------------|
| Packet filter | No | No | No | No |
| Stateful firewall | No | No | No | L4 only |
| ALG (in-kernel) | No | Yes (NAT fixup) | Yes | Yes |
| Application proxy | Yes (full MITM) | Yes | N/A | Yes |
| DPI engine | No | Optional | Optional | Yes |
| IDS/IPS | No | Drop/reject only | No | Yes |

An ALG is **transparent** — the endpoints do not know it exists. A proxy is **non-transparent** — the connection terminates at the proxy and is re-originated.

### 1.4 Why ALGs Are Security-Critical Components

ALGs are at the intersection of several critical security properties:

- **Firewall policy enforcement**: If the FTP ALG creates a conntrack expectation on the wrong port, it effectively opens a hole in the firewall for arbitrary traffic
- **NAT correctness**: A buggy SIP ALG that mis-rewrites a Contact header breaks VoIP and may route calls to the wrong endpoint
- **DoS surface**: ALG parsers process attacker-controlled data; buffer overflows, state machine confusion, and resource exhaustion are all realistic attack vectors
- **Information leakage**: An ALG that logs protocol messages may expose credentials (FTP USER/PASS in cleartext, SIP authentication digests)
- **Evasion**: Fragmented packets, encoding tricks, and protocol violations can confuse ALG state machines and allow bypasses

---

## 2. The Problem ALGs Solve

### 2.1 The NAT Problem with Embedded Addresses

Consider FTP Active Mode without an ALG:

```
Client: 192.168.1.100    NAT Gateway: 203.0.113.1    Server: 198.51.100.5

Step 1: Client connects to server port 21 (control connection)
  TCP SYN: 192.168.1.100:54321 --> 198.51.100.5:21
  NAT rewrites src: 203.0.113.1:54321 --> 198.51.100.5:21  [CORRECT]

Step 2: Client sends PORT command to tell server where to send data
  FTP payload: "PORT 192,168,1,100,195,149\r\n"
             (meaning: connect back to 192.168.1.100 port 50069)

  NAT does NOT rewrite the FTP payload payload!
  Server receives: "PORT 192,168,1,100,195,149"
  Server tries to connect to 192.168.1.100:50069
  192.168.1.100 is a PRIVATE address -- connection FAILS
```

With an FTP ALG:

```
Step 2 (with ALG): Client sends PORT command
  FTP payload before ALG: "PORT 192,168,1,100,195,149\r\n"
  ALG intercepts, rewrites:  "PORT 203,0,113,1,195,149\r\n"
  (replaces private IP with NAT public IP)
  
  ALG also registers a conntrack EXPECTATION:
  "Expect a connection from 198.51.100.5:20 to 203.0.113.1:50069"
  
Step 3: Server connects to 203.0.113.1:50069 (data connection)
  NAT sees this matches the expectation
  NAT rewrites dst: 203.0.113.1:50069 --> 192.168.1.100:50069
  Data connection succeeds!
```

### 2.2 The Firewall Problem

Even without NAT, a stateful firewall with strict policy faces a problem with protocols that negotiate secondary connections on dynamic ports.

Without an ALG, you must either:
- Open all high ports (DANGEROUS: massive attack surface)
- Open specific static ports (WRONG: dynamic protocols don't use fixed ports)
- Use the ALG to dynamically open only the specific negotiated port (CORRECT)

The ALG creates a **temporary, narrow, directional firewall hole** for exactly the negotiated port, from exactly the expected source, for exactly the duration of the session. This is the principle of **least privilege applied to network sessions**.

### 2.3 Protocol Categories Requiring ALGs

```
Category A: Protocols with embedded address in control channel
  - FTP (PORT/PASV commands embed IP:port)
  - SIP (Contact/Via headers embed IP:port)
  - H.323 (Q.931/H.245 embed IP:port in ASN.1)
  - RTSP (Transport header embeds IP:port)
  - MGCP (SDP body embeds IP:port)

Category B: Protocols that open back-channels from server to client
  - FTP Active Mode (server connects back to client)
  - IRC DCC (direct client-to-client file transfer)
  - Legacy protocols (finger, talk, etc.)

Category C: Protocols with complex multiplexed sessions
  - H.323 (uses multiple TCP and UDP sub-sessions)
  - SCTP multi-homing (multiple IP addresses per association)
  - PPTP (GRE data channel keyed by control channel)

Category D: Protocols with dynamic port negotiation
  - Sun RPC (portmapper maps service names to ephemeral ports)
  - NFS (uses RPC portmapper)
  - SNMP traps (agent calls back to manager)
```

### 2.4 Modern Relevance — Are ALGs Still Needed?

ALGs are frequently criticized as:
- Security vulnerabilities (the SIP ALG is notoriously buggy)
- Performance bottlenecks (payload inspection is expensive)
- Complexity sources (state machines are hard to get right)

Modern alternatives that reduce ALG dependency:
- **STUN/TURN/ICE** (RFC 5389/5766/8445): Protocols negotiate around NAT without ALG
- **QUIC** (RFC 9000): Avoids embedding addresses, uses connection IDs
- **SIP over TLS/SRTP**: Encrypted payload that ALG cannot inspect (this breaks naive ALGs)
- **WebRTC**: Uses ICE, so browser-based VoIP works without SIP ALG
- **IPv6**: Eliminates NAT, removes the payload-rewrite requirement (though firewall expectation creation is still useful)

However, ALGs remain essential for:
- Legacy enterprise VoIP infrastructure (H.323, SIP with NAT)
- Legacy file transfer systems (FTP)
- Network monitoring and compliance (need protocol awareness)
- Attack detection that requires understanding protocol semantics

---

## 3. Linux Kernel Packet Path — Complete Stack

### 3.1 Overview

To understand where ALGs operate, you must understand the complete Linux kernel packet path from NIC to socket.

```
                        INGRESS PATH
NIC Hardware
    |
    v
[DMA ring buffer / XDP hook (XDP_PASS/XDP_DROP/XDP_TX/XDP_REDIRECT)]
    |
    v
[__netif_receive_skb] -- tc ingress (sch_ingress) -- eBPF tc hook
    |
    v
[ip_rcv] / [ip6_rcv]
    |
    v
[NETFILTER: NF_INET_PRE_ROUTING]   <-- iptables PREROUTING / nftables prerouting
    |                                   nf_conntrack (conntrack lookup & new entry)
    |                                   DNAT (destination NAT happens here)
    |                                   ALG helpers run in conntrack on this hook
    v
[ip_route_input] -- routing decision
    |
    +-- LOCAL DELIVERY --> [ip_local_deliver]
    |                          |
    |                          v
    |                      [NETFILTER: NF_INET_LOCAL_IN]  <-- INPUT chain
    |                          |
    |                          v
    |                      [TCP/UDP/ICMP protocol handlers]
    |                          |
    |                          v
    |                      [socket receive buffer]
    |
    +-- FORWARD ----------> [ip_forward]
                                |
                                v
                            [NETFILTER: NF_INET_FORWARD]  <-- FORWARD chain
                                |
                                v
                            [ip_output] / [ip6_output]
                                |
                                v
                            [NETFILTER: NF_INET_POST_ROUTING] <-- POSTROUTING
                                |                                   SNAT happens here
                                v
                            [dev_queue_xmit]

                        EGRESS PATH
Socket
    |
    v
[NETFILTER: NF_INET_LOCAL_OUT]  <-- OUTPUT chain
    |
    v
[ip_output]
    |
    v
[NETFILTER: NF_INET_POST_ROUTING]  <-- POSTROUTING chain
    |
    v
[dev_queue_xmit]
    |
    v
[tc egress hook] / [XDP_TX redirect]
    |
    v
NIC Hardware
```

### 3.2 The sk_buff (Socket Buffer) — The Core Data Structure

Every packet in the Linux kernel is represented by a `struct sk_buff`. ALGs manipulate sk_buffs directly.

```c
// Simplified from include/linux/skbuff.h
struct sk_buff {
    // Pointers into the packet data
    unsigned char   *head;      // start of allocated buffer
    unsigned char   *data;      // start of payload (moves with push/pull)
    unsigned char   *tail;      // end of payload
    unsigned char   *end;       // end of allocated buffer

    // Network layer (L3)
    __be16          protocol;   // ETH_P_IP, ETH_P_IPV6, etc.
    union {
        __be32      iph;        // IPv4 header offset
        // ...
    } network_header;
    
    // Transport layer (L4)
    union {
        __be32      th;         // TCP header
        __be32      uh;         // UDP header
        // ...
    } transport_header;

    // Connection tracking
    struct nf_conntrack *nfct;  // pointer to conntrack entry

    // NAT
    unsigned long   nf_trace;

    // Length information
    unsigned int    len;        // total packet length
    unsigned int    data_len;   // length of page fragments (non-linear data)
    
    // Timestamps, marks, etc.
    __u32           mark;       // fwmark (used for policy routing)
    __u32           priority;   // QoS priority
    
    // GSO/GRO (segmentation offload)
    __u16           gso_size;
    __u16           gso_segs;
    __u8            gso_type;
};
```

Key ALG operations on sk_buff:
- `skb_header_pointer()` — safely access header bytes, handling non-linear data
- `skb_make_writable()` — ensure the packet data is writable (copy-on-write)
- `skb_store_bits()` — modify bytes at a given offset
- `skb_push()` / `skb_pull()` — add/remove data at front
- `skb_put()` — add data at end
- `skb_linearize()` — convert paged/fragmented skb to linear (expensive)

### 3.3 Netfilter Hook Registration

ALGs register callbacks at netfilter hook points:

```c
// From include/linux/netfilter.h
struct nf_hook_ops {
    nf_hookfn       *hook;          // the callback function
    struct net_device *dev;         // device (for NETDEV hooks)
    void            *priv;          // private data
    u_int8_t        pf;            // protocol family: PF_INET, PF_INET6
    enum nf_hook_ops_type hook_ops_type;
    unsigned int    hooknum;        // which hook point (PRE_ROUTING etc.)
    int             priority;       // lower = earlier in chain
};

// Hook return values
#define NF_DROP   0     // drop the packet
#define NF_ACCEPT 1     // accept and continue processing
#define NF_STOLEN 2     // packet consumed by hook (no further processing)
#define NF_QUEUE  3     // enqueue for userspace
#define NF_REPEAT 4     // call this hook again
#define NF_STOP   5     // like ACCEPT but stop further hooks (deprecated)

// Hook priorities (from include/uapi/linux/netfilter_ipv4.h)
enum nf_ip_hook_priorities {
    NF_IP_PRI_FIRST         = INT_MIN,
    NF_IP_PRI_RAW_BEFORE_DEFRAG = -450,
    NF_IP_PRI_CONNTRACK_DEFRAG  = -400,
    NF_IP_PRI_RAW               = -300,
    NF_IP_PRI_SELINUX_FIRST     = -225,
    NF_IP_PRI_CONNTRACK         = -200,  // conntrack runs here
    NF_IP_PRI_MANGLE            = -150,
    NF_IP_PRI_NAT_DST           = -100,  // DNAT
    NF_IP_PRI_FILTER            =     0,  // packet filter
    NF_IP_PRI_SECURITY          =    50,
    NF_IP_PRI_NAT_SRC           =   100,  // SNAT
    NF_IP_PRI_SELINUX_LAST      =   225,
    NF_IP_PRI_CONNTRACK_CONFIRM =   INT_MAX, // conntrack confirm
    NF_IP_PRI_LAST              =   INT_MAX,
};
```

---

## 4. Netfilter Architecture — Hooks, Tables, and Chains

### 4.1 The Five Hook Points

```
PREROUTING      -- Before routing decision (DNAT, conntrack)
INPUT           -- For packets destined to local machine
FORWARD         -- For packets being routed through
OUTPUT          -- For packets generated locally
POSTROUTING     -- After routing decision (SNAT)
```

### 4.2 Tables and Chain Priority

iptables has multiple tables, each operating at specific hook points:

```
Table: raw       (priority: -300)
  PREROUTING, OUTPUT
  Purpose: NOTRACK (bypass conntrack), CT target configuration

Table: mangle    (priority: -150)
  PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING
  Purpose: packet modification (TTL, TOS, mark)

Table: nat       (priority: -100 for DNAT, +100 for SNAT)
  PREROUTING (DNAT), INPUT (local DNAT), OUTPUT (local DNAT), POSTROUTING (SNAT)
  Purpose: network address translation

Table: filter    (priority: 0)
  INPUT, FORWARD, OUTPUT
  Purpose: packet filtering (ACCEPT/DROP/REJECT)

Table: security  (priority: +50)
  INPUT, FORWARD, OUTPUT
  Purpose: SELinux/secmark labels
```

### 4.3 How Conntrack Integrates

```
Packet arrives at NF_INET_PRE_ROUTING:

1. nf_conntrack (priority -200) runs FIRST
   - Looks up packet in conntrack table
   - If found: associates packet with existing connection (CT_INFO_ESTABLISHED)
   - If not found: creates NEW conntrack entry (CT_INFO_NEW)
   - Calls conntrack helpers (ALGs) for existing connections

2. DNAT (priority -100) runs SECOND
   - Checks if NAT rules apply
   - If DNAT: rewrites destination IP/port in IP header

3. Filter (priority 0) runs THIRD
   - Checks against iptables FORWARD/INPUT rules
   - Can match on conntrack state (-m conntrack --ctstate NEW,ESTABLISHED)
```

### 4.4 nftables vs. iptables — ALG Differences

nftables (kernel 3.13+, preferred since kernel 5.x) differs from iptables in ALG handling:

```
iptables: ALG helpers are auto-assigned based on port number
  - nf_conntrack_ftp automatically activates for port 21
  - This is INSECURE: any traffic on port 21 gets FTP ALG treatment

nftables: ALG helpers must be EXPLICITLY assigned using ct helper
  - You define: ct helper ftp_helper { type "ftp" protocol tcp; }
  - You apply:  ct helper set "ftp_helper" in a rule
  - This is SECURE: only traffic you explicitly mark gets ALG treatment
```

This is a major security difference. We will cover both approaches in depth.

---

## 5. Connection Tracking Subsystem (nf_conntrack)

### 5.1 The conntrack Entry

Every network flow tracked by conntrack has a `struct nf_conn` entry:

```c
// Simplified from include/net/netfilter/nf_conntrack.h
struct nf_conn {
    // Reference counting
    struct nf_conntrack ct_general;

    // Spinlock for this entry
    spinlock_t lock;

    // The 5-tuple that identifies this connection
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];
    // tuplehash[IP_CT_DIR_ORIGINAL]: original direction (client->server)
    // tuplehash[IP_CT_DIR_REPLY]:    reply direction (server->client)

    // Connection state
    u_int8_t  proto;          // IPPROTO_TCP, IPPROTO_UDP, etc.
    u8        tcp_state;      // TCP state machine

    // Protocol-specific data
    union nf_conntrack_proto proto_data;

    // Expiry timer
    struct timer_list timeout;
    unsigned long    last_used;

    // NAT binding
    struct nf_conn_nat *nat;

    // ALG helper private data
    struct nf_ct_helper_info *helper_info;
    
    // Extension area (for helper data, labels, timestamps, etc.)
    struct nf_ct_ext *ext;

    // Status flags
    unsigned long status;
    // IPS_CONFIRMED_BIT: entry has been seen in both directions
    // IPS_SRC_NAT_BIT: source NAT applied
    // IPS_DST_NAT_BIT: destination NAT applied
    // IPS_DYING_BIT: being deleted
    // IPS_FIXED_TIMEOUT_BIT: timeout not auto-updated
    // IPS_EXPECTED_BIT: this is an expected connection (child of another)
    // IPS_SEQ_ADJUST_BIT: TCP sequence adjustment needed (after payload mod)
    // IPS_OFFLOAD_BIT: offloaded to hardware

    // Marks for policy routing and QoS
    u_int32_t mark;
    u32       secmark;

    // Network namespace
    struct net *ct_net;
};
```

### 5.2 The Tuple — Connection Identity

```c
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;     // source (mangled by SNAT)
    struct {
        union nf_inet_addr u3;       // destination IP
        union {
            __be16 all;
            struct { __be16 port; } tcp;
            struct { __be16 port; } udp;
            struct { u_int8_t type, code; } icmp;
            struct { __be16 port; } dccp;
            struct { __be16 port; } sctp;
            struct { __be16 key; } gre;
        } u;
        u_int8_t protonum;           // IP protocol number
        u_int8_t dir;                // direction
    } dst;
};

struct nf_conntrack_man {
    union nf_inet_addr u3;           // source IP
    union nf_conntrack_man_proto u;  // source port (TCP/UDP) or ICMP id
    u_int16_t l3num;                 // address family: AF_INET, AF_INET6
};
```

The conntrack table stores two tuples per connection:
- `ORIGINAL`: the tuple as seen in the original direction (before any NAT)
- `REPLY`: the tuple as seen in the reply direction (after NAT, reversed)

This is what enables NAT: the conntrack knows both the original and translated tuples.

### 5.3 Conntrack States

```
NEW         - First packet seen (SYN for TCP, first packet for UDP)
ESTABLISHED - Reply seen (SYN-ACK for TCP, reply packet for UDP)
RELATED     - This connection was expected by a helper (data channel)
INVALID     - Does not match any valid state
UNTRACKED   - Deliberately excluded from tracking (NOTRACK rule)

For TCP specifically:
  SYN_SENT    - SYN seen
  SYN_RECV    - SYN+SYN-ACK seen
  ESTABLISHED - Full 3-way handshake complete
  FIN_WAIT    - FIN seen
  CLOSE_WAIT  - FIN+ACK seen
  LAST_ACK    - FIN in both directions
  TIME_WAIT   - 2*MSL wait after close
  CLOSE       - Connection closed
```

### 5.4 Conntrack Expectations

An **expectation** is a record that says: "I expect a future connection with these characteristics. When it arrives, treat it as RELATED to this existing connection."

```c
// From include/net/netfilter/nf_conntrack_expect.h
struct nf_conntrack_expect {
    // List linkage
    struct hlist_node lnode;
    struct hlist_node dnode;

    // Back-pointer to master connection
    struct nf_conn *master;

    // The helper that created this expectation
    struct nf_conntrack_helper *helper;

    // Expected tuple (what we expect to see)
    struct nf_conntrack_tuple tuple;

    // Mask (which fields of the tuple must match)
    struct nf_conntrack_tuple_mask mask;

    // What NAT to apply to the expected connection
    nf_nat_expect_fn *expectfn;

    // Flags
    unsigned int flags;
    // NF_CT_EXPECT_PERMANENT: don't delete after first match
    // NF_CT_EXPECT_INACTIVE: disabled
    // NF_CT_EXPECT_USERSPACE: created by userspace

    // Timeout
    unsigned long timeout;
    
    // Class (used for expectation matching priority)
    unsigned int class;
};
```

When a new packet arrives and matches an expectation:
1. The packet is assigned CT state = `RELATED`
2. A new `nf_conn` is created for the data connection
3. The data connection's `master` pointer is set to the control connection
4. The expectation is deleted (unless `NF_CT_EXPECT_PERMANENT`)
5. NAT is applied to the data connection based on the `expectfn`

### 5.5 TCP Sequence Number Adjustment

When an ALG modifies the payload (e.g., rewrites an IP address string), the TCP payload size may change. This breaks TCP sequence numbers for all subsequent packets in the connection.

The kernel handles this via `nf_ct_seqadj`:

```c
// From include/net/netfilter/nf_conntrack_seqadj.h
struct nf_ct_seqadj {
    u32     correction_pos;   // sequence number where correction applies
    s32     offset_before;    // offset before this position
    s32     offset_after;     // offset after this position
};
```

When the ALG modifies a payload that grows or shrinks:
```c
// ALG calls this to register a sequence adjustment
nf_ct_seqadj_set(ct, ctinfo, seq, off);
// 'off' is the signed size change (positive = grew, negative = shrank)

// Subsequent packets in this connection are adjusted:
// new_seq = old_seq + offset_after (or offset_before depending on position)
```

This is why payload modification is so complex: a single character change in an FTP PORT command can affect sequence numbers for the entire rest of the TCP connection.

### 5.6 Conntrack Sysctl Tuning

```bash
# Maximum number of conntrack entries (critical for high-throughput systems)
sysctl net.netfilter.nf_conntrack_max=2000000

# Hash table size (should be ~1/4 to 1/8 of max)
# Set in modprobe.conf or at module load:
# options nf_conntrack hashsize=524288

# Timeouts for each protocol/state (seconds)
sysctl net.netfilter.nf_conntrack_tcp_timeout_established=86400
sysctl net.netfilter.nf_conntrack_tcp_timeout_syn_sent=120
sysctl net.netfilter.nf_conntrack_tcp_timeout_syn_recv=60
sysctl net.netfilter.nf_conntrack_tcp_timeout_fin_wait=120
sysctl net.netfilter.nf_conntrack_tcp_timeout_time_wait=120
sysctl net.netfilter.nf_conntrack_tcp_timeout_close=10
sysctl net.netfilter.nf_conntrack_udp_timeout=30
sysctl net.netfilter.nf_conntrack_udp_timeout_stream=180
sysctl net.netfilter.nf_conntrack_icmp_timeout=30

# Maximum expectations per connection
sysctl net.netfilter.nf_conntrack_expect_max=4096

# Enable/disable conntrack accounting
sysctl net.netfilter.nf_conntrack_acct=1

# Enable/disable conntrack timestamp
sysctl net.netfilter.nf_conntrack_timestamp=1

# Loose mode for UDP (set to 0 for strict checking)
sysctl net.netfilter.nf_conntrack_udp_loose=0
```

---

## 6. The nf_conntrack Helper Framework

### 6.1 The nf_conntrack_helper Structure

Every in-kernel ALG registers itself as a `nf_conntrack_helper`:

```c
// From include/net/netfilter/nf_conntrack_helper.h
struct nf_conntrack_helper {
    // Name (e.g., "ftp", "sip", "h323")
    char name[NF_CT_HELPER_NAME_LEN];

    // The module that owns this helper
    struct module *me;

    // Protocol and port this helper handles
    const struct nf_conntrack_expect_policy *expect_policy;
    unsigned int expect_class_max;

    // The tuple describing what traffic triggers this helper
    struct nf_conntrack_tuple tuple;

    // MAIN CALLBACK: called for each packet on a connection using this helper
    int (*help)(struct sk_buff *skb,
                unsigned int protoff,
                struct nf_conn *ct,
                enum ip_conntrack_info ctinfo);
    // Returns: NF_ACCEPT, NF_DROP, or NF_QUEUE

    // Called when a connection using this helper is destroyed
    void (*destroy)(struct nf_conn *ct);

    // Called when a new connection matches this helper's tuple
    // Returns: 0 if helper should be assigned, non-zero to reject
    int (*from_nlattr)(struct nlattr *attr, struct nf_conn *ct);

    // Size of per-connection private data
    unsigned int data_len;

    // Flags
    unsigned int flags;
    // NF_CT_HELPER_F_USERSPACE: userspace helper
    // NF_CT_HELPER_F_NAT_MASQUERADE: NAT masquerade helper
};

// Expectation policy (limits on how many expectations this helper can create)
struct nf_conntrack_expect_policy {
    unsigned int    max_expected;   // max concurrent expectations
    unsigned int    timeout;        // expectation timeout in seconds
    char            name[NF_CT_HELPER_NAME_LEN];
};
```

### 6.2 The help() Callback — Core ALG Logic

The `help()` callback is the heart of every ALG. It is called:
- For every packet on a TRACKED connection (not NEW, usually ESTABLISHED or RELATED)
- In the NF_INET_PRE_ROUTING hook for incoming packets
- In the NF_INET_POST_ROUTING hook for outgoing packets (after NAT)

```c
// Typical structure of a help() callback
static int alg_help(struct sk_buff *skb,
                    unsigned int protoff,
                    struct nf_conn *ct,
                    enum ip_conntrack_info ctinfo)
{
    // 1. Get pointer to transport header
    const struct tcphdr *th;
    unsigned int dataoff, datalen;
    
    th = skb_header_pointer(skb, protoff, sizeof(struct tcphdr), &_tcph);
    if (!th) return NF_ACCEPT;
    
    // 2. Skip retransmits (already processed)
    if (ctinfo != IP_CT_ESTABLISHED && 
        ctinfo != IP_CT_ESTABLISHED_REPLY)
        return NF_ACCEPT;
    
    // 3. Get payload pointer
    dataoff = protoff + th->doff * 4;
    datalen = skb->len - dataoff;
    if (datalen == 0) return NF_ACCEPT;
    
    // 4. Lock conntrack for modification
    spin_lock_bh(&ct->lock);
    
    // 5. Parse the protocol payload
    ret = parse_protocol_payload(skb, dataoff, datalen, &parsed_data);
    if (ret < 0) {
        spin_unlock_bh(&ct->lock);
        return NF_ACCEPT;  // or NF_DROP if strict
    }
    
    // 6. Create expectation if needed
    if (parsed_data.has_embedded_address) {
        struct nf_conntrack_expect *exp;
        exp = nf_ct_expect_alloc(ct);
        if (exp) {
            nf_ct_expect_init(exp, NF_CT_EXPECT_CLASS_DEFAULT,
                              nf_ct_l3num(ct),
                              &parsed_data.src_addr,
                              &parsed_data.dst_addr,
                              IPPROTO_TCP,
                              NULL, &parsed_data.port);
            nf_ct_expect_related(exp);
            nf_ct_expect_put(exp);
        }
    }
    
    // 7. NAT fixup (if NAT is active)
    if (nf_nat_alg_hook) {
        ret = nf_nat_alg_hook(skb, protoff, ct, ctinfo, &parsed_data);
    }
    
    spin_unlock_bh(&ct->lock);
    return NF_ACCEPT;
}
```

### 6.3 Helper Registration and Module Loading

```c
// From a typical ALG module
static struct nf_conntrack_helper ftp_helper[2] __read_mostly = {
    {   // IPv4 FTP helper
        .name           = "ftp",
        .me             = THIS_MODULE,
        .data_len       = sizeof(struct ftp_ct_data),
        .tuple.src.l3num = AF_INET,
        .tuple.src.u.tcp.port = cpu_to_be16(FTP_PORT),
        .tuple.dst.protonum    = IPPROTO_TCP,
        .help           = help,
        .destroy        = destroy,
        .expect_policy  = &ftp_exp_policy,
    },
    {   // IPv6 FTP helper
        .name           = "ftp",
        .me             = THIS_MODULE,
        .data_len       = sizeof(struct ftp_ct_data),
        .tuple.src.l3num = AF_INET6,
        .tuple.src.u.tcp.port = cpu_to_be16(FTP_PORT),
        .tuple.dst.protonum    = IPPROTO_TCP,
        .help           = help,
        .destroy        = destroy,
        .expect_policy  = &ftp_exp_policy,
    },
};

static int __init nf_conntrack_ftp_init(void)
{
    return nf_conntrack_helpers_register(ftp_helper, ARRAY_SIZE(ftp_helper));
}

static void __exit nf_conntrack_ftp_fini(void)
{
    nf_conntrack_helpers_unregister(ftp_helper, ARRAY_SIZE(ftp_helper));
}

module_init(nf_conntrack_ftp_init);
module_exit(nf_conntrack_ftp_fini);
```

### 6.4 Automatic vs. Explicit Helper Assignment

**Automatic (iptables legacy mode — INSECURE)**:

When `nf_conntrack_ftp` is loaded, it registers its tuple `{AF_INET, IPPROTO_TCP, port=21}`. Any new connection to port 21 automatically gets the FTP helper assigned. This means:
- An SSH server on port 21 would get FTP helper treatment
- A non-FTP server on port 21 could be confused by the FTP parser trying to interpret its data
- A malicious server could craft FTP-like responses to open arbitrary firewall holes

**Explicit (nftables ct helper — SECURE)**:

```
nft add table ip filter
nft add ct helper ip filter ftp_ct { type "ftp" protocol tcp \; }
nft add chain ip filter forward { type filter hook forward priority 0 \; }
nft add rule ip filter forward tcp dport 21 ct helper set "ftp_ct"
```

Now ONLY traffic on port 21 that matches explicit rules gets the FTP helper. This is the correct approach.

The kernel sysctl to disable automatic helper assignment:
```bash
# Disable automatic helper assignment (RECOMMENDED for security)
sysctl net.netfilter.nf_conntrack_helper=0
```

---

## 7. NAT and ALG Interaction

### 7.1 The NAT Hooks

NAT is implemented as a netfilter extension that uses the conntrack framework. NAT hooks run AFTER conntrack:

```
Packet direction: Client -> Server (through NAT/firewall)

At NF_INET_PRE_ROUTING (DNAT):
  1. Conntrack runs (prio -200): creates new conn, assigns helper
  2. DNAT runs (prio -100): rewrites dst IP in IP header
  
At NF_INET_POST_ROUTING (SNAT / Masquerade):
  3. SNAT runs (prio +100): rewrites src IP in IP header
  4. Conntrack confirm runs (prio INT_MAX): inserts conn into table
  5. ALG help() is called HERE for the payload inspection
```

Wait — step 5 seems late. Let me clarify the exact sequence:

```
For ESTABLISHED connections (not NEW):
  At NF_INET_PRE_ROUTING:
    1. Conntrack lookup: finds existing entry
    2. ct->helper->help() IS CALLED HERE for TCP/UDP ESTABLISHED
    3. NAT rewrites IP header

For NEW connections:
  At NF_INET_PRE_ROUTING:
    1. Conntrack creates new entry, assigns helper
    2. help() is NOT called for NEW (first packet)
    3. NAT may do DNAT
  
  At NF_INET_POST_ROUTING (confirm):
    4. Conntrack confirm: entry goes from unconfirmed to confirmed
    5. First packet does not get help() called

  On SECOND packet (ESTABLISHED state):
    6. help() IS CALLED
```

This means the FTP control connection must send PORT before the server responds — the ALG sees the PORT command when the connection is ESTABLISHED, which is correct.

### 7.2 NAT Expectation Functions

When a helper creates an expectation, it can also specify a NAT function to apply to the expected (data) connection:

```c
// FTP example: when data connection arrives, apply DNAT
static void nf_nat_ftp_expected(struct nf_conn *ct,
                                 struct nf_conntrack_expect *exp)
{
    struct nf_nat_range2 range = {
        .flags = NF_NAT_RANGE_MAP_IPS,
        .min_addr = ct->tuplehash[IP_CT_DIR_REPLY].tuple.dst.u3,
        .max_addr = ct->tuplehash[IP_CT_DIR_REPLY].tuple.dst.u3,
    };
    // Apply the NAT transformation to the data connection
    nf_nat_setup_info(ct, &range, NF_NAT_MANIP_DST);
}
```

### 7.3 The ALG-NAT Payload Rewrite Process

When an ALG must rewrite the payload (e.g., FTP PORT command with private IP → public IP):

```c
// Step-by-step payload rewrite
static int nf_nat_ftp(struct sk_buff *skb,
                       enum ip_conntrack_info ctinfo,
                       enum nf_ct_ftp_type type,
                       unsigned int matchoff,
                       unsigned int matchlen,
                       struct nf_conntrack_expect *exp)
{
    union nf_inet_addr newip;
    u_int16_t port;
    int dir = CTINFO2DIR(ctinfo);
    struct nf_conn *ct = nf_ct_get(skb, &ctinfo);
    char buffer[sizeof("nnn.nnn.nnn.nnn,ppp,ppp")];
    unsigned buflen;

    // Get the post-NAT IP address
    newip = ct->tuplehash[!dir].tuple.dst.u3;
    
    // Get the post-NAT port (from the expectation)
    exp->saved_addr = exp->tuple.dst.u3;
    exp->tuple.dst.u3 = newip;
    exp->saved_proto.tcp.port = exp->tuple.dst.u.tcp.port;

    // Format the new PORT command payload
    if (type == NF_CT_FTP_PORT || type == NF_CT_FTP_PASV) {
        port = ntohs(exp->tuple.dst.u.tcp.port);
        buflen = sprintf(buffer, "%u,%u,%u,%u,%u,%u",
                         ((unsigned char *)&newip.ip)[0],
                         ((unsigned char *)&newip.ip)[1],
                         ((unsigned char *)&newip.ip)[2],
                         ((unsigned char *)&newip.ip)[3],
                         port >> 8, port & 0xFF);
    }
    
    // Perform the actual payload substitution
    // This may change the packet size, requiring TCP seq adjustment
    return nf_nat_mangle_tcp_packet(skb, ct, ctinfo,
                                     protoff, matchoff, matchlen,
                                     buffer, buflen);
}

// nf_nat_mangle_tcp_packet implementation concept:
int nf_nat_mangle_tcp_packet(struct sk_buff *skb,
                               struct nf_conn *ct,
                               enum ip_conntrack_info ctinfo,
                               unsigned int protoff,
                               unsigned int match_offset,
                               unsigned int match_len,
                               const char *rep_buffer,
                               unsigned int rep_len)
{
    // 1. Make packet writable
    if (!skb_make_writable(skb, skb->len))
        return 0;
    
    // 2. Calculate size difference
    int diff = (int)rep_len - (int)match_len;
    
    // 3. If the replacement is larger, grow the skb
    if (rep_len > match_len) {
        if (skb_tailroom(skb) < diff) {
            // Need to allocate more space
            if (pskb_expand_head(skb, 0, diff, GFP_ATOMIC))
                return 0;
        }
        // Move tail of packet forward
        memmove(skb->data + match_offset + rep_len,
                skb->data + match_offset + match_len,
                skb->len - match_offset - match_len);
        skb->len += diff;
    } else if (rep_len < match_len) {
        // Shrink: move tail of packet backward
        memmove(skb->data + match_offset + rep_len,
                skb->data + match_offset + match_len,
                skb->len - match_offset - match_len);
        skb->len -= (match_len - rep_len);
    }
    
    // 4. Copy new data
    memcpy(skb->data + match_offset, rep_buffer, rep_len);
    
    // 5. Update IP total length
    ip_hdr(skb)->tot_len = htons(skb->len);
    
    // 6. Register TCP sequence adjustment
    if (diff != 0) {
        nf_ct_seqadj_set(ct, ctinfo, 
                         ntohl(tcp_hdr(skb)->seq) + match_offset,
                         diff);
    }
    
    // 7. Recalculate checksums
    // (done by hardware offload or kernel at dev_queue_xmit)
    
    return 1;
}
```

---

## 8. Every ALG in Linux — Exhaustive Coverage

### 8.1 FTP ALG

#### Protocol Overview

FTP (File Transfer Protocol, RFC 959, 1985) uses two separate TCP connections:
- **Control connection**: TCP port 21, client to server, carries commands and responses
- **Data connection**: for actual file transfer, opened dynamically

FTP has TWO data transfer modes:

**Active Mode (PORT)**:
```
Client (192.168.1.10)          NAT Gateway              Server (198.51.100.5)
        |                           |                           |
        |-- TCP SYN port 21 ------->|-- TCP SYN port 21 ------->|  Control conn
        |<- TCP SYN-ACK ------------|<- TCP SYN-ACK ------------|
        |-- TCP ACK --------------->|-- TCP ACK --------------->|
        |                           |                           |
        |-- "PORT 192,168,1,10,     |                           |
        |    195,149\r\n" --------->|  FTP ALG intercepts here  |
        |                           |-- "PORT 203,0,113,1,      |
        |                           |    195,149\r\n" --------->|
        |                           |                           |
        |                           |<-- TCP SYN (port 50069) --|  Data conn
        |<-- TCP SYN (port 50069) --|                           |  ALG created expect
```

**Passive Mode (PASV)**:
```
Client (192.168.1.10)          NAT Gateway              Server (198.51.100.5)
        |                           |                           |
        |-- "PASV\r\n" ------------>|-- "PASV\r\n" ------------>|
        |                           |<-- "227 Entering Passive   |
        |                           |    Mode (198,51,100,5,    |
        |                           |    195,149)\r\n" ---------|
        |<-- "227 Entering Passive  |                           |
        |    Mode (198,51,100,5,    |  ALG rewrites response    |
        |    195,149)\r\n" ---------|  (server-side address,    |
        |                           |  no rewrite needed here)  |
        |-- TCP SYN port 50069 ---->|-- TCP SYN port 50069 ---->|  Data conn
```

Note: In PASV, the server embeds ITS OWN address, which is publicly routable — no NAT rewrite needed. But for clients behind NAT reaching a server also behind NAT, Extended Passive (EPSV) is used.

**Extended Modes (EPSV/EPRT for IPv6)**:

EPSV response format: `229 Entering Extended Passive Mode (|||port|)`
EPRT command format: `EPRT |2|2001:db8::1|50069|` (for IPv6)

#### Kernel Module: nf_conntrack_ftp

```bash
# Module name
modprobe nf_conntrack_ftp

# Parameters
modprobe nf_conntrack_ftp ports=21       # which ports to handle (default: 21)
modprobe nf_conntrack_ftp loose=0        # strict: PORT must match src IP
# loose=1 (default): allow PORT with any IP (needed for multi-homed servers)
# loose=0: PORT IP must match connection source (more secure)

# For NAT support:
modprobe nf_nat_ftp
```

#### FTP ALG Source Code Location (Linux Kernel)

```
net/netfilter/nf_conntrack_ftp.c     -- Protocol parser + helper registration
net/netfilter/nf_nat_ftp.c           -- NAT payload rewrite
net/ipv4/netfilter/ip_nat_ftp.c      -- Legacy IPv4-specific (older kernels)
include/linux/netfilter/nf_conntrack_ftp.h -- Types and definitions
```

#### FTP ALG State Machine

```
Control Connection States:
  IDLE          -> (client sends USER) -> AUTHENTICATED_REQUEST
  AUTHENTICATED -> (client sends PORT) -> PORT_SEEN
  PORT_SEEN     -> (server sends 200)  -> READY
  READY         -> (client sends RETR/STOR/LIST) -> TRANSFER
  TRANSFER      -> (transfer complete) -> IDLE

  AUTHENTICATED -> (client sends PASV) -> PASV_REQUESTED
  PASV_REQUESTED-> (server sends 227)  -> PASV_SEEN (expectation created)
  PASV_SEEN     -> (client connects)   -> TRANSFER

FTP Commands Parsed by ALG:
  PORT xxx,xxx,xxx,xxx,ppp,ppp  -- Active mode: client announces data addr
  PASV                          -- Passive mode request
  227 Entering Passive Mode(x,x,x,x,p,p) -- Server announces data addr
  EPRT |family|addr|port|       -- Extended active (IPv6)
  229 Entering Extended Passive Mode (|||port|) -- Extended passive

Parsed by ALG but NOT requiring fixup:
  USER, PASS, QUIT, ABOR, TYPE, MODE, STRU, NLST, LIST, RETR, STOR, etc.
```

#### FTP ALG Kernel Data Structures

```c
// Per-connection FTP state (stored in nf_conn extension)
struct nf_ct_ftp_master {
    /* 1 means seq_aft_nl is valid. */
    int seq_aft_nl_num[IP_CT_DIR_MAX];
    /* If this is set, I've seen a newline after this number. */
    u32 seq_aft_nl[IP_CT_DIR_MAX][2];
};

// Parsed FTP data (from payload)
enum nf_ct_ftp_type {
    /* PORT command from client */
    NF_CT_FTP_PORT,
    /* PASV response from server */
    NF_CT_FTP_PASV,
    /* EPRT command from client */
    NF_CT_FTP_EPRT,
    /* EPSV response from server */
    NF_CT_FTP_EPSV,
};
```

#### Security Issues with FTP ALG

1. **Bounce attack (RFC 2577)**: Attacker can use PORT command to direct server to connect to arbitrary third-party host:port. Solution: `loose=0` and validate that PORT IP matches connection source.

2. **PORT range abuse**: Server connecting to privileged ports (<1024). Some implementations restrict expectations to high ports only.

3. **FTP over TLS (FTPS/FTPES)**: ALG cannot inspect encrypted sessions. AUTH TLS upgrades the control connection to TLS, making all subsequent commands opaque. The ALG must track `AUTH TLS` command and stop trying to parse afterward.

4. **Fragment reassembly attacks**: Send PORT command split across TCP segments. ALG must handle multi-packet payload.

5. **Evasion via CRLF variants**: Some implementations fail on `\r\r\n` or `\n` alone instead of `\r\n`.

#### iptables/nftables Configuration for FTP

```bash
# iptables approach (legacy, auto-helper)
# Load modules
modprobe nf_conntrack_ftp
modprobe nf_nat_ftp

# Allow FTP control and related data
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -p tcp --dport 21 -m conntrack --ctstate NEW -j ACCEPT

# nftables approach (explicit helper - RECOMMENDED)
nft add table ip nat
nft add chain ip nat prerouting { type nat hook prerouting priority -100 \; }
nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }

nft add table ip filter  
nft add chain ip filter forward { type filter hook forward priority 0 \; policy drop \; }

# Define the FTP helper
nft add ct helper ip filter ftp_helper { type "ftp" protocol tcp \; }

# Assign helper to FTP control connections
nft add rule ip filter forward ip saddr 192.168.0.0/16 tcp dport 21 \
    ct state new ct helper set "ftp_helper"

# Allow established and related
nft add rule ip filter forward ct state established,related accept

# SNAT / masquerade for outbound
nft add rule ip nat postrouting ip saddr 192.168.0.0/16 oifname "eth0" masquerade
```

---

### 8.2 SIP ALG

#### Protocol Overview

SIP (Session Initiation Protocol, RFC 3261, 2002) is the dominant VoIP signaling protocol. It uses:
- **Control**: UDP/TCP port 5060, TLS on 5061
- **Media**: RTP/RTCP on dynamic UDP ports negotiated via SDP

SIP is a text-based protocol, similar to HTTP. A SIP session involves:

```
                   REGISTRAR/PROXY (public IP: 203.0.113.10)
                           |
                   SIP INVITE message
                           |
Client (192.168.1.10:5060) --- NAT (203.0.113.1) --- Internet
                           |
                   The INVITE contains:
                   Via: SIP/2.0/UDP 192.168.1.10:5060  <-- WRONG after NAT
                   Contact: <sip:alice@192.168.1.10>   <-- WRONG after NAT
                   SDP body:
                     o=alice 12345 12345 IN IP4 192.168.1.10  <-- WRONG
                     c=IN IP4 192.168.1.10                    <-- WRONG
                     m=audio 49170 RTP/AVP 0                  <-- port to rewrite
```

The SIP ALG must rewrite all these embedded addresses and create expectations for the RTP/RTCP media flows.

#### SDP (Session Description Protocol, RFC 4566)

SDP is embedded in the SIP message body. Key fields:

```
v=0                                    -- version
o=alice 12345 67890 IN IP4 192.168.1.10  -- origin, includes IP
s=Call                                 -- session name
c=IN IP4 192.168.1.10                  -- connection address (media goes here)
t=0 0                                  -- timing
m=audio 49170 RTP/AVP 0 8 97          -- media: audio, port 49170, codecs
a=rtpmap:0 PCMU/8000                  -- codec attributes
m=video 51372 RTP/AVP 31 32           -- media: video, port 51372
```

The ALG must rewrite `o=`, `c=`, and each `m=` line, and create expectations for each media port (and the RTCP port which is typically media_port+1).

#### SIP Dialog State Machine

```
States for each SIP dialog:
  NULL      --> (INVITE sent/received) --> CALLING
  CALLING   --> (1xx response) --> PROCEEDING  
  CALLING   --> (2xx response) --> CONFIRMED (call established)
  CALLING   --> (3xx-6xx response) --> TERMINATED
  PROCEEDING--> (2xx response) --> CONFIRMED
  CONFIRMED --> (BYE sent/received) --> TERMINATED
  
  REGISTER transactions:
  NULL --> (REGISTER) --> REGISTERING --> (200 OK) --> REGISTERED
  
  SUBSCRIBE/NOTIFY:
  NULL --> (SUBSCRIBE) --> SUBSCRIBING --> (200 OK / NOTIFY) --> ACTIVE
```

#### Kernel Module: nf_conntrack_sip

```bash
# Load modules
modprobe nf_conntrack_sip
modprobe nf_nat_sip

# Parameters:
# ports: SIP UDP/TCP ports (default: 5060)
# sip_timeout: dialog timeout (default: 3600 seconds)
modprobe nf_conntrack_sip ports=5060,5061 sip_timeout=3600
```

#### SIP ALG Source Files

```
net/netfilter/nf_conntrack_sip.c     -- Parser + helper
net/netfilter/nf_nat_sip.c           -- NAT payload rewrite
```

#### SIP Header Rewriting — All Headers That May Contain Addresses

The SIP ALG must rewrite these headers when they contain the client's private IP:

```
Via:         -- Each proxy adds a Via header; client's is innermost
Contact:     -- Where to reach the UA directly
Route:       -- Preloaded routes
Record-Route:-- Route that should be added by proxies
From:        -- Source identity (may contain IP in URI)
To:          -- Destination (rarely an IP)
m=           -- SDP connection address
c=           -- SDP media connection address
o=           -- SDP origin (may contain IP)
```

The ALG also rewrites the SDP `m=` port lines and creates conntrack expectations for each media stream.

#### SIP ALG — Known Security Issues

The SIP ALG is notoriously problematic:

1. **Re-INVITE storms**: A misbehaving UAC can send many re-INVITEs with different SDP, each causing new expectations to be created, exhausting the expectation table.

2. **SIP REGISTER hijacking**: The ALG modifies Contact headers; if the rewrite is wrong, all incoming calls are directed to the wrong destination.

3. **Encrypted SIP (SIP/TLS + SRTP)**: ALG cannot read encrypted SIP. The Contact header rewrite fails, causing registration to fail. Most modern deployments use ICE/STUN instead of ALG.

4. **SIP over WebSocket**: RFC 7118 — SIP over WebSocket is becoming standard for WebRTC. Traditional SIP ALG does not handle WS framing.

5. **Denial of Service via malformed SIP**: Deeply nested Via headers, excessively long headers, invalid encoding can crash the ALG parser.

6. **Call flow attacks**: Attacker sends a BYE message to tear down a legitimate call by injecting into an established SIP dialog the ALG is tracking.

#### Why You Should Often Disable the SIP ALG

For modern VoIP deployments:
```bash
# Check if SIP ALG is active
lsmod | grep nf_conntrack_sip

# Remove SIP ALG modules
modprobe -r nf_nat_sip
modprobe -r nf_conntrack_sip

# Add to /etc/modprobe.d/blacklist.conf:
blacklist nf_conntrack_sip
blacklist nf_nat_sip

# Instead, use STUN/TURN (RFC 5766) or Session Border Controller (SBC)
# For enterprise VoIP, use a proper SBC like Kamailio or FreeSWITCH
# as a back-to-back user agent (B2BUA)
```

Modern VoIP alternatives to SIP ALG:
- **ICE (RFC 8445)**: Endpoints discover their public IP/port using STUN
- **TURN (RFC 5766)**: Media relay when direct connection is impossible
- **Session Border Controller (SBC)**: Proper application proxy for SIP
- **WebRTC**: Built-in ICE/STUN/TURN, no ALG needed

---

### 8.3 H.323 ALG

#### Protocol Overview

H.323 is an ITU-T standard for multimedia communication. It is older than SIP and significantly more complex, using a binary ASN.1 encoding (PER — Packed Encoding Rules) rather than text. This makes the ALG much harder to implement correctly.

H.323 sub-protocols:
- **Q.931** (H.225.0): Call setup and teardown over TCP port 1720
- **H.245**: Media capability negotiation (TCP, dynamic port negotiated in Q.931)
- **RAS** (Registration, Admission, Status): UDP port 1719 (with gatekeepers)
- **RTP/RTCP**: Media streams (UDP, dynamic ports from H.245)
- **T.120**: Data conferencing (optional)

```
H.323 Call Setup Flow (simplified):
  
  Caller                    H.323 GK/Gateway            Callee
    |                              |                       |
    |-- Q.931 SETUP (TCP 1720) --->|                       |
    |  (H.245 addr embedded        |                       |
    |   in SETUP using ASN.1)      |                       |
    |                              |-- Q.931 SETUP ------->|
    |<-- Q.931 CALL PROCEEDING ----|<-- Q.931 ALERTING ----|
    |<-- Q.931 ALERTING -----------|                       |
    |<-- Q.931 CONNECT ------------|                       |
    |                              |                       |
    |-- TCP to H.245 addr ----------|-- TCP to H.245 ------>|
    |<- H.245 TerminalCapabilitySet>|<- H.245 capability ---|
    |-- H.245 OpenLogicalChannel -->|                       |
    |  (RTP ports negotiated)       |-- H.245 OLC --------->|
    |<- H.245 OpenLogicalChannelAck-|<- H.245 OLC Ack ------|
    |                              |                       |
    |<============================ RTP Media =============>|
```

#### The ASN.1 Challenge

H.323 messages are encoded in ASN.1 PER (Packed Encoding Rules). This is a binary format:
- Variable-length fields with no separator
- Fields may be absent or present based on bitmask flags
- Nested structures within structures
- Version-dependent encoding (H.323 v1 through v7)

Writing a correct H.323 ALG requires a full ASN.1 PER decoder — this is extremely complex and is one reason H.323 is being replaced by SIP.

#### Kernel Module: nf_conntrack_h323

```bash
# Module loading
modprobe nf_conntrack_h323
modprobe nf_nat_h323

# Parameters:
modprobe nf_conntrack_h323 \
    gkrouted_only=0 \    # 0 = also handle direct calls (not via gatekeeper)
    callforward_filter=1  # filter call forwarding (security)
```

#### H.323 ALG Source Files

```
net/netfilter/nf_conntrack_h323_asn1.c  -- ASN.1 decoder (auto-generated)
net/netfilter/nf_conntrack_h323_main.c  -- Main helper logic
net/netfilter/nf_nat_h323.c             -- NAT payload rewrite
include/linux/netfilter/nf_conntrack_h323_asn1.h
include/linux/netfilter/nf_conntrack_h323_types.h
```

#### H.323 ALG — What It Tracks

```
Q.931 messages parsed:
  Setup          -- contains calledPartyNumber, H.245 address
  CallProceeding -- may contain H.245 address
  Alerting       -- may contain H.245 address
  Connect        -- contains H.245 address
  ReleaseComplete -- call teardown

H.245 messages parsed:
  OpenLogicalChannel     -- contains RTP address and port
  OpenLogicalChannelAck  -- confirms OLC with remote RTP address
  CloseLogicalChannel    -- close a media channel

H.225/RAS messages parsed (UDP):
  GatekeeperRequest/Confirm/Reject
  RegistrationRequest/Confirm/Reject
  AdmissionRequest/Confirm/Reject
  UnregistrationRequest/Confirm

Expectations created:
  - H.245 TCP connection (from Q.931 H.245 address field)
  - RTP UDP connections (from H.245 OLC)
  - RTCP UDP connections (RTP port + 1)
  - T.120 TCP connections (optional data channel)
```

#### Security Issues with H.323 ALG

1. **ASN.1 parser complexity**: The ASN.1 PER decoder is complex and has historically had buffer overflows. CVE-2004-0218 (Cisco IOS), CVE-2004-1027 (various) were H.323 parsing bugs.

2. **Gatekeeper traversal**: H.323 with gatekeepers involves multiple hops; ALG must track all hops correctly.

3. **Encrypted H.235**: H.235 adds security to H.323 with media encryption. Like SIP/TLS, this makes the ALG blind.

4. **H.245 tunneling in H.225**: H.245 messages can be tunneled inside H.225 Q.931 messages, requiring the ALG to parse one protocol to find another.

---

### 8.4 PPTP ALG

#### Protocol Overview

PPTP (Point-to-Point Tunneling Protocol, RFC 2637, 1999) creates VPN tunnels. It uses:
- **Control**: TCP port 1723 (the PPTP control protocol)
- **Data**: GRE (Generic Routing Encapsulation, IP protocol 47) with call IDs

The problem for NAT: GRE packets don't have port numbers. NAT doesn't know how to multiplex multiple GRE connections from different clients to the same PPTP server. The PPTP ALG solves this by:
1. Watching the TCP control connection for the Call-ID
2. Creating a special GRE-aware expectation using the Call-ID as the discriminator

#### GRE and NAT

Standard GRE (RFC 2784) is a tunneling protocol with:
- IP protocol number 47 (not TCP/UDP)
- Key field (optional): Can be used as a session discriminator
- Sequence number (optional)
- Checksum (optional)

For PPTP, GRE uses the "Key" field as a Call-ID. The NAT must track Call-IDs rather than ports.

#### Kernel Module: nf_conntrack_pptp

```bash
modprobe nf_conntrack_pptp    # PPTP control connection tracker
modprobe nf_conntrack_proto_gre  # GRE protocol tracker
modprobe nf_nat_pptp          # PPTP NAT support
modprobe nf_nat_proto_gre     # GRE NAT support
```

#### PPTP ALG Source Files

```
net/netfilter/nf_conntrack_pptp.c        -- Control connection parser
net/netfilter/nf_conntrack_proto_gre.c   -- GRE protocol tracker
net/netfilter/nf_nat_pptp.c             -- PPTP NAT fixup
net/netfilter/nf_nat_proto_gre.c        -- GRE NAT (Call-ID rewriting)
```

#### PPTP Control Protocol Messages Parsed

```
PPTP Message Types (TCP port 1723):
  Start-Control-Connection-Request (SCCRQ)    -- type 1
  Start-Control-Connection-Reply (SCCRP)      -- type 2
  Stop-Control-Connection-Request (StopCCRQ)  -- type 3
  Echo-Request                                -- type 5
  Echo-Reply                                  -- type 6
  Outgoing-Call-Request (OCRQ)               -- type 7  [client -> server]
  Outgoing-Call-Reply (OCRP)                 -- type 8  [server -> client]
  Incoming-Call-Request (ICRQ)               -- type 9
  Incoming-Call-Reply (ICRP)                 -- type 10
  Incoming-Call-Connected (ICCN)             -- type 11
  Call-Clear-Request                         -- type 12
  Call-Disconnect-Notify                     -- type 13
  
Key fields parsed:
  Call-ID (client assigns for outgoing calls)
  Peer-Call-ID (server assigns)
  These IDs are embedded in GRE packets as the "Key" field
```

#### PPTP NAT Operation

```
Normal PPTP without NAT:
  Client (192.168.1.10) --> Server (203.0.113.5)
  TCP OCRQ: Call-ID = 1000
  TCP OCRP: Peer-Call-ID = 2000
  GRE packets from client: Key = 2000 (server's ID)
  GRE packets from server: Key = 1000 (client's ID)

PPTP with two clients behind NAT:
  Client A (192.168.1.10) --> NAT --> Server, Call-ID = 1000
  Client B (192.168.1.20) --> NAT --> Server, Call-ID = 1000  [CONFLICT!]

PPTP ALG solution:
  ALG rewrites Call-IDs to be unique across NAT clients
  Client A: Call-ID 1000 --> rewritten to 5000 (NAT allocates unique ID)
  Client B: Call-ID 1000 --> rewritten to 5001 (NAT allocates different ID)
  NAT tracks: GRE Key 5000 --> Client A, GRE Key 5001 --> Client B
```

#### Security Considerations for PPTP

PPTP itself is cryptographically broken (MS-CHAPv2 authentication is trivially crackable). The PPTP ALG enables broken VPN traffic. Modern deployments should use IPsec/IKEv2, OpenVPN, or WireGuard instead.

---

### 8.5 IRC ALG

#### Protocol Overview

IRC (Internet Relay Chat, RFC 1459, 1993) supports DCC (Direct Client-to-Client) transfers that bypass the IRC server. DCC opens a direct TCP connection between two IRC clients for:
- DCC SEND: file transfer
- DCC CHAT: direct peer chat
- DCC VOICE: audio (rare)

DCC requires one client to listen and the other to connect. When the listener is behind NAT, the ALG must:
1. Parse the DCC SEND/CHAT command
2. Extract the embedded IP:port
3. Rewrite the IP:port to the NAT public address
4. Create an expectation for the incoming DCC connection

#### DCC Message Format

```
DCC message format (sent via IRC PRIVMSG or CTCP):
  PRIVMSG target :\001DCC SEND filename ipaddr port filesize\001
  PRIVMSG target :\001DCC CHAT chat ipaddr port\001

The ipaddr is encoded as a 32-bit integer in decimal:
  192.168.1.100 = (192 * 16777216) + (168 * 65536) + (1 * 256) + 100
                = 3232235876

Example:
  \001DCC SEND mypicture.jpg 3232235876 49152 102400\001
  Means: "Connect to 192.168.1.100:49152 to receive mypicture.jpg (100KB)"
```

#### Kernel Module: nf_conntrack_irc

```bash
modprobe nf_conntrack_irc
modprobe nf_nat_irc

# Parameters:
modprobe nf_conntrack_irc ports=6667  # default IRC port
```

#### IRC ALG Source Files

```
net/netfilter/nf_conntrack_irc.c     -- Parser + helper
net/netfilter/nf_nat_irc.c           -- NAT fixup
```

#### Security Issues

1. **DCC as malware C&C**: DCC connections bypass the IRC server and can be used by malware. The ALG facilitates this.
2. **Integer IP encoding**: The ALG must correctly parse the decimal-encoded IP. Off-by-one errors can map to wrong addresses.
3. **DCC RESUME**: File resume sends a port number that the ALG must also track.
4. **SSL/TLS IRC (IRC over TLS, port 6697)**: ALG cannot see DCC messages if TLS is in use.

---

### 8.6 TFTP ALG

#### Protocol Overview

TFTP (Trivial File Transfer Protocol, RFC 1350, 1992) is a simple UDP-based file transfer protocol. It is used for:
- Network booting (PXE boot)
- Router configuration download
- IP phone firmware updates
- Simple embedded device updates

TFTP uniquely assigns a new UDP port for each data transfer:

```
TFTP Flow:
Client (192.168.1.10:random)    Server (198.51.100.5:69)

Client sends Read Request (RRQ) to port 69:
  UDP src=192.168.1.10:54321, dst=198.51.100.5:69
  
Server responds from a NEW random port:
  UDP src=198.51.100.5:49152, dst=192.168.1.10:54321
  
All subsequent packets use this server port 49152, NOT port 69!
```

The problem: The firewall sees traffic from port 49152 (not 69) and drops it. The ALG creates an expectation for the response from the server's ephemeral port.

#### Kernel Module: nf_conntrack_tftp

```bash
modprobe nf_conntrack_tftp
modprobe nf_nat_tftp

# Note: TFTP uses UDP. The conntrack TFTP helper creates UDP expectations.
# Parameters:
modprobe nf_conntrack_tftp ports=69
```

#### TFTP ALG Source Files

```
net/netfilter/nf_conntrack_tftp.c    -- UDP helper
net/netfilter/nf_nat_tftp.c          -- NAT fixup
```

#### TFTP ALG Operation

```
At NF_INET_PRE_ROUTING for the client RRQ/WRQ packet:
  1. ALG sees UDP packet to port 69 with TFTP opcode 1 (RRQ) or 2 (WRQ)
  2. ALG records the client address (src IP:port)
  3. ALG creates expectation: expect any UDP from server to this client port
     Expectation tuple: {src=server_IP/any, dst=client_IP:client_port}
  4. When server's DATA packet arrives from ephemeral port:
     - Matches expectation
     - Marked as RELATED
     - DNAT applied if needed (for NATed clients)
```

#### Security Notes

TFTP has no authentication. The ALG enabling TFTP creates a window where any packet from the server's IP can reach the client. PXE boot environments should use TFTP in isolated VLANs.

---

### 8.7 SNMP ALG

#### Protocol Overview

SNMP (Simple Network Management Protocol) uses:
- UDP port 161: SNMP queries (manager to agent)
- UDP port 162: SNMP traps (agent to manager, i.e., server-initiated)

The problem: SNMP traps contain embedded IP addresses in OID values. When an SNMP agent behind NAT sends a trap to a manager, the trap may contain the agent's private IP address in the SNMP variable bindings (e.g., in the sysContact or agent address field).

More critically, SNMPv1 traps have an "Enterprise" specific format that embeds the agent address:

```
SNMPv1 Trap PDU:
  enterprise (OID)
  agent-addr (IP address of agent -- embedded private IP!)
  generic-trap (integer)
  specific-trap (integer)
  time-stamp
  variable-bindings (list of OID/value pairs, may contain IPs)
```

#### Kernel Module: nf_conntrack_snmp

```bash
modprobe nf_conntrack_snmp
modprobe nf_nat_snmp_basic

# The SNMP ALG uses BER (Basic Encoding Rules) ASN.1 parsing
# It is quite complex for a kernel module
```

#### SNMP ALG Source Files

```
net/netfilter/nf_nat_snmp_basic.c    -- NAT fixup for SNMP
# Note: The SNMP conntrack helper is relatively minimal; much of the
# intelligence is in the NAT module.
```

#### SNMP BER Parsing

SNMP v1/v2c uses BER encoding. The ALG must parse:
```
TLV (Tag-Length-Value) structure:
  30 82 00 45  -- SEQUENCE, length 0x45 (69 bytes)
    02 01 00   -- INTEGER, length 1, value 0 (version: SNMPv1)
    04 06 70 75 62 6c 69 63  -- OCTET STRING "public" (community)
    A4 ...     -- Trap PDU (tag 0xA4 = context[4])
      06 ...   -- enterprise OID
      40 04 C0 A8 01 0A  -- IpAddress (tag 0x40) = 192.168.1.10 <-- REWRITE
      02 01 06 -- generic-trap
      02 01 00 -- specific-trap
      43 01 00 -- time-stamp
      30 ...   -- variable bindings
```

The `40` tag (IpAddress) is what the ALG rewrites.

#### Security Issues

1. **SNMPv1/v2c community strings in cleartext**: The community string (password) is visible to the ALG and any observer. This is a fundamental SNMP design weakness.
2. **SNMP v3 encryption**: SNMPv3 with authPriv encrypts the PDU, making the ALG blind.
3. **BER malformed input**: The BER parser can be confused by crafted TLV lengths. Length = 0xFF, indefinite length encoding, etc.
4. **Trap flood**: Attacker triggers many traps to exhaust conntrack table.

---

### 8.8 Amanda ALG

#### Protocol Overview

Amanda (Advanced Maryland Automatic Network Disk Archiver) is a backup system. It uses:
- **Control**: UDP port 10080 (amandad)
- **Data**: Multiple dynamic TCP/UDP ports for data channels

Amanda's network protocol requires the backup server to connect BACK to the client (backup client sends request, server initiates data connections). This back-channel creation requires the ALG.

#### Kernel Module: nf_conntrack_amanda

```bash
modprobe nf_conntrack_amanda
modprobe nf_nat_amanda

# Parameters:
modprobe nf_conntrack_amanda ts_algo=0  # timestamp algorithm
```

#### Amanda ALG Source Files

```
net/netfilter/nf_conntrack_amanda.c    -- Helper
net/netfilter/nf_nat_amanda.c          -- NAT fixup
```

#### Amanda Protocol Details

The Amanda server sends a REQUEST via UDP to the client's `amandad` port. The client responds with a REPLY that includes:
- Port numbers for data service connections
- These ports are embedded in the UDP payload as ASCII text

The ALG parses:
```
Amanda SERVICE line format:
  SERVICE servicename port
  
Example reply:
  CONNECT DATA 40000 MESG 40001 INDEX 40002
```

The ALG creates TCP expectations for each announced port (DATA, MESG, INDEX) allowing the server to connect back on those ports.

---

### 8.9 NetBIOS ALG

#### Protocol Overview

NetBIOS (Network Basic Input/Output System) is used by Windows file sharing (SMB). Relevant to ALGs:

- **NetBIOS Name Service (NBNS)**: UDP port 137 — name registration and resolution
- **NetBIOS Datagram Service**: UDP port 138 — connectionless data
- **NetBIOS Session Service**: TCP port 139 — connection-oriented (SMB)

The NetBIOS ALG handles the fact that NetBIOS datagrams embed IP addresses in the data section, similar to how DNS responds with addresses.

#### Kernel Module: nf_conntrack_netbios_ns

```bash
modprobe nf_conntrack_netbios_ns
```

#### Source Files

```
net/netfilter/nf_conntrack_netbios_ns.c
```

#### NetBIOS Name Service Packet Structure

```
NetBIOS Name Query Request (UDP):
  Transaction ID: 2 bytes
  Flags: 2 bytes
  Questions: 1 entry (NetBIOS encoded name)
  
NetBIOS Name Query Response:
  Transaction ID: 2 bytes
  Flags: 2 bytes
  Answers: NetBIOS encoded name + IP address (embedded!)

The ALG must:
  1. See the query (track transaction ID)
  2. Intercept the response
  3. Rewrite the embedded IP address if client is behind NAT
  4. Create expectation for the return unicast response
```

---

### 8.10 RTSP ALG

#### Protocol Overview

RTSP (Real Time Streaming Protocol, RFC 2326/7826) controls streaming media delivery. It uses:
- **Control**: TCP port 554 (or UDP)
- **Media**: RTP/RTCP on dynamic UDP ports (negotiated in SETUP request)

RTSP is text-based, similar to HTTP. The `SETUP` request and `200 OK` response negotiate the transport parameters including ports.

```
RTSP SETUP request:
  SETUP rtsp://198.51.100.5/video.mp4/trackID=1 RTSP/1.0
  CSeq: 3
  Transport: RTP/AVP;unicast;client_port=49170-49171
  
  (client_port=49170 for RTP, 49171 for RTCP)
  
RTSP 200 OK response:
  RTSP/1.0 200 OK
  CSeq: 3
  Transport: RTP/AVP;unicast;client_port=49170-49171;server_port=6970-6971
  Session: 12345678
  
  (server will send RTP from port 6970, RTCP from 6971)
```

#### Kernel Module: nf_conntrack_h323

Note: The kernel's RTSP helper is part of the H.323 module in some configurations, or separate:

```bash
# RTSP support in conntrack
# In some distributions this is compiled in or part of nf_conntrack_h323
# Check:
ls /lib/modules/$(uname -r)/kernel/net/netfilter/ | grep rtsp
# If nf_conntrack_rtsp.ko exists:
modprobe nf_conntrack_rtsp
modprobe nf_nat_rtsp
```

Note: The in-kernel RTSP conntrack helper was actually removed from mainline kernel around 3.x due to maintenance burden. The out-of-tree module `nf_conntrack_rtsp` (from various third-party sources) can be compiled against the running kernel.

For modern systems, RTSP firewall support is often handled via:
- `nfqueue` + userspace RTSP-aware daemon
- Squid proxy with RTSP support
- VLC's built-in NAT traversal

#### RTSP ALG Operation

```
Client SETUP --> ALG parses client_port from Transport header
ALG creates expectation for RTP UDP from server to client_port
ALG creates expectation for RTCP UDP from server to client_port+1

Server 200 OK --> ALG parses server_port from Transport header  
ALG creates additional expectation for server's RTP/RTCP
```

---

### 8.11 DNS ALG

#### Protocol Overview

DNS (Domain Name System) primarily uses UDP port 53. The DNS "ALG" is not a traditional ALG in the sense of managing secondary connections. Instead, it handles:

1. **DNS response rewriting**: In certain NAT64/DNS64 scenarios, DNS AAAA responses are synthesized from A records
2. **DNS expectation tracking**: DNS queries use random source ports (since EDNS0 + randomization); tracking ensures the reply from the resolver is permitted back through the firewall
3. **Split DNS**: Some firewalls rewrite DNS responses to return internal IPs for internal clients

#### Kernel DNS Conntrack

The DNS ALG in the kernel is minimal — primarily it ensures UDP DNS replies from port 53 are tracked and permitted:

```bash
# DNS is primarily tracked as stateful UDP
# The conntrack tracks DNS as bidirectional UDP streams
# Modern kernels (5.6+) have improved DNS tracking via:
sysctl net.netfilter.nf_conntrack_udp_timeout_stream=120
```

#### DNS64 / NAT64

For IPv6-only networks accessing IPv4 servers (RFC 6146 NAT64 + RFC 6147 DNS64):

```
IPv6-only Client          DNS64 Resolver         IPv4 Server
     |                         |                      |
     |-- AAAA query for A.B -->|                       |
     |                         |-- A query for A.B -->|
     |                         |<-- 198.51.100.5 ------|
     |                         |  Synthesizes AAAA:    |
     |                         |  64:ff9b::c633:6405   |
     |<-- AAAA = 64:ff9b::... -|                       |
     |                         |                       |
     |-- IPv6 to 64:ff9b::... --------> NAT64 box --> IPv4 to 198.51.100.5

NAT64 prefix: 64:ff9b::/96
IPv4 address embeds in last 32 bits: 64:ff9b::c633:6405 = 64:ff9b::198.51.100.5
```

This is an "ALG" in the DNS domain — the DNS64 resolver rewrites DNS responses.

Tools: Tayga (userspace NAT64), Jool (kernel NAT64), named with dns64 plugin.

---

### 8.12 DCCP ALG

#### Protocol Overview

DCCP (Datagram Congestion Control Protocol, RFC 4340) is a transport protocol with:
- Congestion control (unlike UDP)
- Unreliable delivery (unlike TCP)
- Variable flow types

DCCP conntrack is implemented in:
```
net/netfilter/nf_conntrack_proto_dccp.c
```

DCCP has its own connection states:
```
NONE -> (DCCP_REQUEST) -> REQUEST
REQUEST -> (DCCP_RESPONSE) -> RESPOND
RESPOND -> (DCCP_ACK) -> PARTOPEN
PARTOPEN -> (DATA) -> OPEN
OPEN -> (DCCP_CLOSE) -> CLOSEREQ
CLOSEREQ -> (DCCP_CLOSE) -> CLOSING
CLOSING -> (DCCP_RESET) -> TIMEWAIT
```

DCCP ALG functionality is mainly about tracking the state machine correctly for stateful firewall purposes. There is no payload inspection requirement for DCCP itself (applications on DCCP don't typically embed addresses).

---

### 8.13 SCTP ALG

#### Protocol Overview

SCTP (Stream Control Transmission Protocol, RFC 4960) is a transport protocol that supports:
- **Multi-homing**: An SCTP association can use multiple IP addresses on each side
- **Multi-streaming**: Multiple independent streams within one association
- **Message-oriented**: Preserves message boundaries (unlike TCP)

SCTP is the transport for SS7-over-IP (Diameter, SIGTRAN) and other telecom protocols.

#### The NAT Problem with SCTP

SCTP multi-homing means a single SCTP association can use multiple source IP addresses. NAT must track ALL of these IP addresses as part of the same association.

The SCTP `INIT` chunk embeds all the sender's IP addresses:
```
SCTP INIT chunk:
  Chunk Type: 1 (INIT)
  Initiate Tag: 0x12345678
  Advertised Receiver Window Credit: 65536
  Number of Outbound Streams: 10
  Number of Inbound Streams: 2048
  Initial TSN: 0x87654321
  Parameters:
    IPv4 Address Parameter (type 5):
      Address: 192.168.1.10      <-- MUST BE REWRITTEN FOR NAT
    IPv4 Address Parameter (type 5):
      Address: 192.168.2.10      <-- second local address (multi-homed)
    Supported Address Types
    ECN Capable
    Forward TSN Supported
```

The ALG must rewrite all embedded IP addresses in INIT and INIT-ACK chunks.

#### Kernel Module: nf_conntrack_proto_sctp

```bash
# SCTP conntrack
modprobe nf_conntrack_proto_sctp

# SCTP NAT (handles multi-homing address rewriting)
modprobe nf_nat_proto_sctp  # if available

# Parameters/sysctls for SCTP conntrack:
sysctl net.netfilter.nf_conntrack_sctp_timeout_closed=10
sysctl net.netfilter.nf_conntrack_sctp_timeout_cookie_wait=3
sysctl net.netfilter.nf_conntrack_sctp_timeout_cookie_echoed=3
sysctl net.netfilter.nf_conntrack_sctp_timeout_established=210
sysctl net.netfilter.nf_conntrack_sctp_timeout_shutdown_sent=0
sysctl net.netfilter.nf_conntrack_sctp_timeout_shutdown_recd=0
sysctl net.netfilter.nf_conntrack_sctp_timeout_shutdown_ack_sent=3
sysctl net.netfilter.nf_conntrack_sctp_timeout_heartbeat_sent=30
sysctl net.netfilter.nf_conntrack_sctp_timeout_heartbeat_acked=210
```

#### SCTP State Machine in Conntrack

```c
// SCTP states tracked (from net/netfilter/nf_conntrack_proto_sctp.c)
enum sctp_conntrack {
    SCTP_CONNTRACK_NONE,
    SCTP_CONNTRACK_CLOSED,
    SCTP_CONNTRACK_COOKIE_WAIT,
    SCTP_CONNTRACK_COOKIE_ECHOED,
    SCTP_CONNTRACK_ESTABLISHED,
    SCTP_CONNTRACK_SHUTDOWN_SENT,
    SCTP_CONNTRACK_SHUTDOWN_RECD,
    SCTP_CONNTRACK_SHUTDOWN_ACK_SENT,
    SCTP_CONNTRACK_HEARTBEAT_SENT,
    SCTP_CONNTRACK_HEARTBEAT_ACKED,
    SCTP_CONNTRACK_MAX
};
```

---

### 8.14 RPC ALG

#### Protocol Overview

Sun RPC (Remote Procedure Call, RFC 1831) / ONC RPC is used by:
- **NFS** (Network File System)
- **NIS** (Network Information Service / YP)
- **rstatd** (remote statistics daemon)
- **lockd** (NFS file locking)
- **mountd** (NFS mount daemon)
- **rquotad** (disk quota service)

The problem: RPC services run on dynamically assigned ports. A **portmapper** (or **rpcbind**) daemon runs on well-known port 111 (TCP/UDP) and maps program numbers to actual ports.

```
RPC Port Discovery Flow:
  Client --> portmapper:111 (GETPORT request for NFS program 100003)
  portmapper --> Client (reply: NFS is on port 2049)
  Client --> NFS server:2049 (actual NFS requests)
  
  The portmapper reply embeds the dynamic port number.
  The ALG must watch the portmapper exchange and create
  expectations for the dynamic ports announced.
```

#### Kernel Module: nf_conntrack_rpc

Note: The RPC conntrack helper is not in mainline kernel by default in recent versions. It was present in older kernels as `nf_conntrack_netlink` functionality or via out-of-tree modules.

For modern systems:
```bash
# Check for RPC conntrack helper
find /lib/modules/$(uname -r) -name "*rpc*"

# If present:
modprobe nf_conntrack_rpc
```

Alternative approach for NFS firewall:
```bash
# On the NFS server, pin RPC services to static ports
# /etc/sysconfig/nfs or /etc/default/nfs-kernel-server:
MOUNTD_PORT=892
STATD_PORT=662
LOCKD_TCPPORT=32803
LOCKD_UDPPORT=32769
RQUOTAD_PORT=875

# Then allow these specific ports in the firewall:
nft add rule ip filter forward tcp dport { 111, 2049, 892, 662, 32803, 875 } accept
nft add rule ip filter forward udp dport { 111, 2049, 892, 662, 32769, 875 } accept
```

#### ONC RPC Message Format

```
RPC Call Message (XDR encoded):
  xid: 0x12345678 (transaction ID)
  msg_type: 0 (CALL)
  rpcvers: 2
  prog: 100003 (NFS)
  vers: 3
  proc: 0 (NULL/ping)
  cred: AUTH_NONE or AUTH_UNIX or AUTH_GSS
  verf: AUTH_NONE
  
RPC Portmap GETPORT request (prog 100000):
  prog: 100003 (NFS)
  vers: 3
  proto: TCP (6)
  port: 0 (asking: what port?)
  
RPC Portmap GETPORT reply:
  port: 2049 (or dynamic port)  <-- ALG must watch this
```

---

### 8.15 MGCP ALG

#### Protocol Overview

MGCP (Media Gateway Control Protocol, RFC 3435) is a VoIP protocol used in carrier networks (not end-user phones). It uses a master/slave model:
- **Call Agent** (master): Controls the gateway, TCP/UDP port 2427
- **Media Gateway** (slave): Executes commands, announces events, UDP port 2427

MGCP uses SDP for media negotiation (same as SIP). The ALG must:
1. Parse MGCP commands (CRCX, MDCX, DLCX)
2. Extract SDP bodies from MGCP messages
3. Rewrite embedded IP addresses in SDP
4. Create RTP/RTCP expectations

#### Kernel Module: nf_conntrack_mgcp

Note: The MGCP helper is not in mainline kernel. Third-party implementations exist.

#### MGCP Message Format

```
MGCP CRCX (Create Connection) command:
  CRCX 1234 aaln/1@gateway.example.com MGCP 1.0
  C: a3e4b3d6
  L: p:10, a:PCMU
  M: recvonly
  
  v=0
  o=- 25678 753849 IN IP4 192.168.1.10    <-- private IP, needs rewrite
  s=-
  c=IN IP4 192.168.1.10                   <-- private IP, needs rewrite
  t=0 0
  m=audio 3456 RTP/AVP 0                  <-- RTP port
  a=rtpmap:0 PCMU/8000
```

---

### 8.16 GRE/PPTP Helper

Already covered in 8.4 PPTP. The GRE protocol helper (`nf_conntrack_proto_gre`) handles the GRE protocol (IP protocol 47) tracking for NAT purposes, specifically using the GRE key/call-ID as the session discriminator.

```bash
# GRE tracking:
modprobe nf_conntrack_proto_gre
# GRE NAT:
modprobe nf_nat_proto_gre
```

Note: Without these modules, a router can only support ONE PPTP client behind NAT. With them, multiple simultaneous PPTP tunnels are supported.

---

### 8.17 SANE ALG

#### Protocol Overview

SANE (Scanner Access Now Easy) is a Linux scanning framework that supports network scanning. The SANE network protocol uses:
- TCP port 6566 for the control/discovery connection
- Additional dynamic connections for image data

#### Kernel Module: nf_conntrack_sane

```bash
modprobe nf_conntrack_sane

# Source:
# net/netfilter/nf_conntrack_sane.c
```

The SANE ALG watches the control connection for DATA_PORT announcements and creates expectations for the image data connections.

---

### 8.18 Netlink-based Helpers (CT Helpers via Userspace)

Starting with Linux 3.x, conntrack helpers can be implemented in **userspace** via the `nf_ct_helper` netlink interface. This is a major improvement for:
- Easier development (no kernel module needed)
- Isolation (bugs don't crash the kernel)
- Complex protocol parsing (use userspace libraries)

The framework:
1. In-kernel nf_conntrack marks packets matching a helper rule for userspace processing
2. Packets are sent to userspace via nfqueue or nfnetlink_cttimeout
3. Userspace daemon parses the protocol and creates expectations via `libnetfilter_conntrack`
4. The kernel receives the expectation and applies it

```bash
# Userspace helper framework:
# conntrack-tools provides nfct command and helper framework
apt-get install conntrack

# List available userspace helpers:
nfct helper list

# Create a userspace FTP helper binding:
nfct helper add ftp inet tcp
```

---

## 9. Userspace ALG Frameworks

### 9.1 nf_queue + libnetfilter_queue

The most flexible approach: intercept packets in userspace and make ALG decisions.

```
Kernel                                    Userspace
  |                                           |
  | NF_QUEUE target in iptables/nftables      |
  |    rule sends packet to queue #N          |
  |                                           |
  | Packet placed in NFQUEUE                  |
  |    (up to queue depth, default 1024)      |
  |                                           |
  | nfnetlink socket                          |
  |    <----- userspace reads packet ---------|
  |    <----- userspace sends verdict --------|
  |                                           |
  | Apply verdict (ACCEPT/DROP/MODIFY)        |
  | Inject modified packet back               |
```

#### libnetfilter_queue API

```c
#include <libnetfilter_queue/libnetfilter_queue.h>

struct nfq_handle *h;        // library handle
struct nfq_q_handle *qh;     // queue handle

// Callback function type:
typedef int (*nfq_callback)(struct nfq_q_handle *qh,
                             struct nfgenmsg *nfmsg,
                             struct nfq_data *nfa,
                             void *data);

// Key functions:
h   = nfq_open();
qh  = nfq_create_queue(h, queue_num, &callback, user_data);
     nfq_set_mode(qh, NFQNL_COPY_PACKET, 65535); // copy full packet
fd  = nfq_fd(h);
// ... select/epoll on fd ...
     nfq_handle_packet(h, buf, rv);               // in callback handler
     nfq_set_verdict(qh, packet_id, NF_ACCEPT, 0, NULL); // accept
     nfq_set_verdict2(qh, packet_id, NF_ACCEPT, mark, len, data); // modify
     nfq_destroy_queue(qh);
     nfq_close(h);
```

### 9.2 conntrack-tools (conntrackd)

`conntrackd` is the userspace daemon for conntrack management:
- High-availability (synchronize conntrack tables between firewalls)
- Userspace conntrack helpers
- Connection event logging

```bash
# Install
apt-get install conntrack conntrackd

# Key commands:
conntrack -L                              # list all conntrack entries
conntrack -L -p tcp --dport 21           # filter by protocol/port
conntrack -D -p tcp --dport 21           # delete entries
conntrack -E                             # event monitoring
conntrack -G -p tcp -s 192.168.1.10     # get specific entry
conntrack --stats                        # per-CPU statistics

# Count active connections:
conntrack -L | wc -l

# Watch new connections in real-time:
conntrack -E -e NEW
```

### 9.3 nftables ct helper

nftables has native support for assigning conntrack helpers explicitly:

```
# Complete nftables configuration with explicit CT helpers
#!/usr/sbin/nft -f

flush ruleset

# Define address family and table
table ip firewall {
    
    # Define conntrack helpers
    ct helper ftp-standard {
        type "ftp" protocol tcp
        l3proto ip
    }
    
    ct helper sip-voip {
        type "sip" protocol udp
        l3proto ip
    }
    
    ct helper tftp-boot {
        type "tftp" protocol udp
        l3proto ip
    }

    # Define chains
    chain prerouting {
        type nat hook prerouting priority -100
        
        # DNAT example
        tcp dport 80 dnat to 192.168.1.100:8080
    }

    chain postrouting {
        type nat hook postrouting priority 100
        
        # Masquerade outbound
        oifname "eth0" masquerade
    }

    chain forward {
        type filter hook forward priority 0
        policy drop
        
        # Allow established and related (including ALG expectations)
        ct state established,related accept
        
        # FTP: assign helper to control connections
        tcp dport 21 ct state new ct helper set "ftp-standard"
        tcp dport 21 ct state new accept
        
        # SIP: assign helper to SIP traffic
        udp dport 5060 ct state new ct helper set "sip-voip"
        udp dport 5060 ct state new accept
        
        # TFTP: assign helper
        udp dport 69 ct state new ct helper set "tftp-boot"
        udp dport 69 ct state new accept
        
        # Drop everything else
        log prefix "FORWARD-DROP: " drop
    }

    chain input {
        type filter hook input priority 0
        policy drop
        
        # Allow loopback
        iifname "lo" accept
        
        # Allow established
        ct state established,related accept
        
        # Allow SSH
        tcp dport 22 ct state new accept
        
        # ICMP
        ip protocol icmp accept
        
        log prefix "INPUT-DROP: " drop
    }
}
```

### 9.4 Suricata as ALG

Suricata (network IDS/IPS) can operate as an in-line ALG via NFQUEUE:

```yaml
# /etc/suricata/suricata.yaml (relevant sections)

# Inline IPS mode via nfqueue
nfqueue:
  mode: repeat
  repeat-mark: 1
  repeat-mask: 1
  bypass-mark: 1
  bypass-mask: 1
  route-queue: 2
  batchcount: 20
  fail-open: yes

# Protocol-specific settings
app-layer:
  protocols:
    ftp:
      enabled: yes
      detection-ports:
        dp: 21
    sip:
      enabled: yes
    tftp:
      enabled: yes
    dns:
      enabled: yes
      detection-ports:
        dp: 53
    http:
      enabled: yes
    tls:
      enabled: yes
    smtp:
      enabled: yes
```

Suricata as ALG:
```bash
# Run Suricata in IPS mode
suricata -c /etc/suricata/suricata.yaml -q 0 --pidfile /run/suricata.pid

# iptables rules to send traffic through Suricata
iptables -I FORWARD -j NFQUEUE --queue-num 0

# Suricata can drop FTP connections that violate policy:
# alert ftp any any -> any any (msg:"FTP Bounce Attack"; \
#   flow:to_server,established; content:"PORT"; \
#   pcre:"/^PORT\s+(?!192\.168\.\d+\.\d+)/"; \
#   sid:1000001; rev:1;)
```

### 9.5 Zeek / Bro

Zeek (formerly Bro) is a network analysis framework that performs passive ALG-like analysis:

```zeek
# Example Zeek script for FTP analysis
# /usr/share/zeek/site/ftp_alg_monitor.zeek

event ftp_request(c: connection, command: string, arg: string)
{
    if (command == "PORT") {
        local parts = split_string(arg, /,/);
        if (|parts| == 6) {
            local ip = fmt("%s.%s.%s.%s", parts[0], parts[1], parts[2], parts[3]);
            local port = (to_int(parts[4]) * 256) + to_int(parts[5]);
            
            if (ip != cat(c$id$orig_h)) {
                # Potential FTP bounce attack
                NOTICE([$note=FTP::Bounce_Attack,
                        $conn=c,
                        $msg=fmt("FTP PORT to non-source IP: %s:%s", ip, port)]);
            }
        }
    }
}

event ftp_reply(c: connection, code: count, msg: string, cont_resp: bool)
{
    if (code == 227) {  # PASV response
        # Parse PASV response
        local m = match_pattern(msg, /([0-9]+,){5}[0-9]+/);
        if (m$matched) {
            print fmt("PASV data channel: %s", m$str);
        }
    }
}
```

---

## 10. Other Linux ALG Implementations Beyond Netfilter

### 10.1 Squid Proxy ALG Behavior

Squid operates as a forward or reverse proxy and provides application-layer inspection:

```
squid.conf relevant directives:

# FTP through HTTP proxy (squid translates FTP to HTTP)
ftp_user anonymous@squid.proxy
ftp_passive on        # Use PASV mode (squid handles this)
ftp_epsv_all off      # Don't require EPSV

# URI access control (Layer 7 ALG)
acl ftp_bounce_check dstdomain !.example.com
# Prevent FTP bounce by checking destination

# SIP: Squid can proxy SIP (experimental)
# cache_peer sip_server parent 5060 0 no-query

# SSL bump (MITM) for HTTPS inspection
ssl_bump splice all   # or peek-and-splice
sslcrtd_program /usr/lib/squid/security_file_certgen -s /var/lib/ssl_db -M 4MB
```

Squid is a full application-layer proxy (not a transparent ALG), but it performs similar functions: protocol inspection, embedded address handling, and connection multiplexing.

### 10.2 HAProxy L7 Inspection

HAProxy performs L7 load balancing with protocol awareness:

```
frontend ftp_in
    bind *:21
    mode tcp
    option tcplog
    
    # L7 inspection via ACL on FTP commands
    tcp-request inspect-delay 5s
    tcp-request content accept if { req.payload(0,4) -m str "USER" }
    
    # FTP stick table for session tracking
    stick-table type ip size 100k expire 30m track-sc0 src
    
    default_backend ftp_servers

backend ftp_servers
    mode tcp
    server ftp1 192.168.1.10:21 check
    server ftp2 192.168.1.11:21 check backup
```

For HTTP, HAProxy performs full L7 inspection:

```
frontend http_in
    bind *:80
    mode http
    
    # ACLs on HTTP content (ALG-like inspection)
    acl is_ftp_over_http path_beg /ftp/
    acl bad_user_agent hdr_sub(user-agent) -i badbot
    
    # Block certain HTTP methods (security ALG)
    acl dangerous_methods method DELETE TRACE OPTIONS
    http-request deny if dangerous_methods
    
    # Inspect and rewrite HTTP headers (ALG function)
    http-request set-header X-Forwarded-For %[src]
    http-request del-header X-Forwarded-Proto
```

### 10.3 Envoy Proxy ALG

Envoy is the data plane for Istio service mesh and operates as a sophisticated L7 ALG:

```yaml
# envoy.yaml - L7 filtering with ALG-like capabilities

static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 10000
    filter_chains:
    - filters:
      # TCP proxy (L4 passthrough)
      - name: envoy.filters.network.tcp_proxy
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.tcp_proxy.v3.TcpProxy
          stat_prefix: ingress_tcp
          cluster: target_cluster

      # OR: HTTP connection manager (L7 ALG)
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          http_filters:
          
          # RBAC filter (security ALG)
          - name: envoy.filters.http.rbac
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.rbac.v3.RBAC
              rules:
                action: ALLOW
                policies:
                  "health-check":
                    permissions:
                    - header:
                        name: ":path"
                        exact_match: "/healthz"
                    principals:
                    - any: true
          
          # JWT authentication (L7 ALG function)
          - name: envoy.filters.http.jwt_authn
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.jwt_authn.v3.JwtAuthentication
              providers:
                provider1:
                  issuer: https://example.com
                  audiences:
                  - my-service
          
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
```

### 10.4 eBPF-based ALG

eBPF enables ALG functionality with:
- Near-zero overhead for packet inspection
- Safe userspace-like programming model in kernel context
- Access to socket-level data (sk_msg, sk_skb programs)

#### eBPF sk_skb for Stream Inspection

```c
// eBPF program type: BPF_PROG_TYPE_SK_SKB
// Attached to: sockmap (BPF_MAP_TYPE_SOCKMAP)
// Used for: stream parsing and redirection

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_SOCKMAP);
    __uint(max_entries, 65536);
    __type(key, int);
    __type(value, int);
} sock_map SEC(".maps");

// Parse stream data and redirect to appropriate backend
SEC("sk_skb/stream_parser")
int bpf_stream_parser(struct __sk_buff *skb)
{
    // Return the length of the "message" found in the stream
    // This implements message framing for protocols like Redis, HTTP, etc.
    
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    
    // Example: look for HTTP request end (\r\n\r\n)
    // ALG: parse HTTP, extract Host header, make routing decision
    
    return skb->len;  // consume entire buffer as one message
}

SEC("sk_skb/stream_verdict")
int bpf_stream_verdict(struct __sk_buff *skb)
{
    // Redirect this stream to the appropriate socket
    __u32 key = 0;
    return bpf_sk_redirect_map(skb, &sock_map, key, 0);
}
```

#### eBPF TC (Traffic Control) for ALG

```c
// BPF_PROG_TYPE_SCHED_CLS attached to tc ingress/egress
// Can perform packet inspection and modification

#include <linux/bpf.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// ALG-like: DNS response inspection and logging
SEC("tc")
int dns_inspector(struct __sk_buff *skb)
{
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    
    struct iphdr *ip = data + sizeof(struct ethhdr);
    if ((void *)(ip + 1) > data_end) return TC_ACT_OK;
    
    if (ip->protocol != IPPROTO_UDP) return TC_ACT_OK;
    
    struct udphdr *udp = (void *)ip + (ip->ihl * 4);
    if ((void *)(udp + 1) > data_end) return TC_ACT_OK;
    
    // DNS responses from port 53
    if (bpf_ntohs(udp->source) != 53) return TC_ACT_OK;
    
    // Parse DNS header
    __u8 *dns = (void *)udp + sizeof(struct udphdr);
    if ((void *)(dns + 12) > data_end) return TC_ACT_OK;
    
    // DNS Flags: [QR(1) OPCODE(4) AA TC RD RA Z RCODE(4)]
    __u16 flags = (dns[2] << 8) | dns[3];
    
    if ((flags & 0x8000) == 0) return TC_ACT_OK; // Query, not response
    
    // Log the DNS response (ALG monitoring)
    bpf_printk("DNS response: txid=0x%x flags=0x%x\n",
               (dns[0] << 8) | dns[1], flags);
    
    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
```

#### eBPF XDP for High-Performance ALG

```c
// BPF_PROG_TYPE_XDP: earliest possible hook, before SKB allocation
// Used for: very high-speed packet classification and forwarding

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// Connection tracking map (simple version)
struct flow_key {
    __be32 src_ip;
    __be32 dst_ip;
    __be16 src_port;
    __be16 dst_port;
    __u8   protocol;
};

struct flow_val {
    __u64 packets;
    __u64 bytes;
    __u8  state;   // connection state
    __u8  flags;   // ALG flags
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1 << 20);  // 1M entries
    __type(key, struct flow_key);
    __type(value, struct flow_val);
} flow_table SEC(".maps");

SEC("xdp")
int xdp_alg_pass(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP) return XDP_PASS;
    
    struct iphdr *ip = (void *)eth + sizeof(*eth);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;
    
    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end) return XDP_PASS;
    
    struct flow_key key = {
        .src_ip   = ip->saddr,
        .dst_ip   = ip->daddr,
        .src_port = tcp->source,
        .dst_port = tcp->dest,
        .protocol = IPPROTO_TCP,
    };
    
    struct flow_val *val = bpf_map_lookup_elem(&flow_table, &key);
    if (!val) {
        struct flow_val new_val = {.packets = 1, .bytes = bpf_ntohs(ip->tot_len)};
        bpf_map_update_elem(&flow_table, &key, &new_val, BPF_NOEXIST);
    } else {
        __sync_fetch_and_add(&val->packets, 1);
        __sync_fetch_and_add(&val->bytes, bpf_ntohs(ip->tot_len));
    }
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### 10.5 XDP ALG Patterns

For true in-line ALG at XDP speed:

```
XDP ALG Architecture:
  NIC receives packet
    |
    v
  XDP hook (runs before SKB allocation — ~1-2 μs latency)
    |
    +-- XDP_DROP: early drop (DDoS mitigation)
    |
    +-- XDP_PASS: hand off to kernel network stack (normal path)
    |
    +-- XDP_TX: hairpin — retransmit on same interface
    |
    +-- XDP_REDIRECT: send to different interface or CPU
    |
    +-- XDP_ABORTED: error (treated as drop)
  
  XDP can:
    - Parse L2-L7 headers
    - Modify packet bytes (NAT rewrite)
    - Maintain maps (flow tables, ACLs, rate limits)
    - NOT create conntrack expectations (must pass to kernel for that)
    - NOT perform TCP state tracking (must use helper maps)
```

XDP ALGs work best for:
- Load balancing (L4 direct server return, XDP LB pattern)
- DDoS mitigation (SYN cookies, rate limiting)
- Fast-path packet forwarding (bypass expensive netfilter)
- Protocol classification (mark packets for further processing)

For complex ALG functions (expectation creation, payload rewrite, TCP seq adjustment), XDP must pass packets to the kernel stack (XDP_PASS + eBPF tc + netfilter).

### 10.6 DPDK-based ALGs

DPDK (Data Plane Development Kit) provides near-hardware-speed packet processing in userspace:

```c
// DPDK ALG example structure

#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_mbuf.h>
#include <rte_hash.h>
#include <rte_jhash.h>
#include <rte_tcp.h>
#include <rte_ip.h>

// Flow table for ALG state
struct alg_flow {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t  proto;
    uint8_t  alg_type;      // which ALG handles this
    uint8_t  alg_state;     // ALG state machine state
    uint32_t seq_offset;    // TCP sequence adjustment
    void    *alg_data;      // protocol-specific data
};

// DPDK burst processing loop
static int alg_process_pkts(uint16_t port, struct rte_hash *flow_table)
{
    struct rte_mbuf *pkts[BURST_SIZE];
    uint16_t nb_rx;
    
    // Receive burst of packets
    nb_rx = rte_eth_rx_burst(port, 0, pkts, BURST_SIZE);
    
    for (uint16_t i = 0; i < nb_rx; i++) {
        struct rte_mbuf *m = pkts[i];
        
        // Parse packet
        struct rte_ether_hdr *eth = rte_pktmbuf_mtod(m, struct rte_ether_hdr *);
        struct rte_ipv4_hdr  *ip  = (void *)(eth + 1);
        struct rte_tcp_hdr   *tcp = (void *)ip + ((ip->version_ihl & 0x0f) * 4);
        
        // Flow lookup
        struct flow_key key = {
            .src_ip   = ip->src_addr,
            .dst_ip   = ip->dst_addr,
            .src_port = tcp->src_port,
            .dst_port = tcp->dst_port,
        };
        
        int64_t pos = rte_hash_lookup(flow_table, &key);
        
        if (pos >= 0) {
            // Existing flow: call appropriate ALG
            struct alg_flow *flow = /* get flow data */ NULL;
            
            switch (flow->alg_type) {
            case ALG_FTP:
                alg_ftp_process(m, ip, tcp, flow);
                break;
            case ALG_SIP:
                alg_sip_process(m, ip, tcp, flow);
                break;
            }
        } else {
            // New flow: classify and assign ALG
            if (rte_be_to_cpu_16(tcp->dst_port) == 21) {
                // FTP control connection
                alg_ftp_new_flow(flow_table, &key, m);
            }
        }
        
        // Forward packet
        rte_eth_tx_burst(port ^ 1, 0, &m, 1);
    }
    
    return 0;
}
```

DPDK ALGs are used in:
- Carrier-grade NAT (CGNAT) devices
- Virtual network functions (VNF)
- Cloud provider NAT gateways (AWS VPC NAT, GCP Cloud NAT internals)
- High-performance firewalls (Palo Alto, Fortinet data plane)

### 10.7 strongSwan / libreswan IKE ALG

IKE (Internet Key Exchange) v1/v2 for IPsec uses:
- UDP port 500: IKE negotiation
- UDP port 4500: NAT-T (NAT Traversal)
- IP protocol 50: ESP (Encapsulating Security Payload) — actual data

The IKE ALG must handle:
- IKE NAT-T encapsulation (wrapping ESP in UDP for NAT traversal)
- IKE port 4500 expectation creation for ESP traffic
- XAUTH / EAP authentication protocol tracking

strongSwan's kernel-netlink interface:

```bash
# strongSwan uses the kernel's xfrm subsystem (not conntrack)
# xfrm (transform) is the kernel's IPsec framework

# View active SA (Security Associations):
ip xfrm state
ip xfrm policy

# strongSwan swanctl configuration:
# /etc/swanctl/swanctl.conf

connections {
    ikev2-rsa {
        remote_addrs = %any
        local {
            auth = pubkey
            certs = server-cert.pem
        }
        remote {
            auth = pubkey
        }
        children {
            net-net {
                local_ts = 10.0.0.0/8
                remote_ts = 0.0.0.0/0
                esp_proposals = aes256gcm16-prfsha384-ecp384
                mode = tunnel
            }
        }
        proposals = aes256-sha384-ecp384
    }
}
```

The xfrm framework in the kernel is separate from netfilter/conntrack but interfaces with it:
```
Netfilter hooks for xfrm:
  NF_INET_LOCAL_OUT -> XFRM policy lookup -> encrypt -> POSTROUTING
  PREROUTING -> decrypt -> NF_INET_LOCAL_IN -> deliver to socket
```

### 10.8 OpenVPN ALG Behavior

OpenVPN uses UDP or TCP as transport. When TCP is used:
- All OpenVPN traffic looks like a single TCP connection
- No secondary channels needed
- No conntrack expectation creation required
- ALG function: classify OpenVPN traffic vs. other TCP traffic on the same port

For UDP OpenVPN:
- OpenVPN uses a session multiplexing approach with session IDs
- No conntrack helper needed
- NAT works naturally because OpenVPN embeds session IDs, not IP addresses

OpenVPN traffic classification (for firewall or QoS ALG):
```
OpenVPN TLS control packet:
  Byte 0: Opcode (upper 5 bits) + Key-ID (lower 3 bits)
  Opcode values:
    0x01: P_CONTROL_HARD_RESET_CLIENT_V1
    0x02: P_CONTROL_HARD_RESET_SERVER_V1
    0x04: P_CONTROL_V1
    0x05: P_ACK_V1
    0x06: P_DATA_V1
    0x07: P_CONTROL_HARD_RESET_CLIENT_V2
    0x08: P_CONTROL_HARD_RESET_SERVER_V2
```

---

## 11. C Implementation — Full ALG Framework

This section builds a complete, production-grade, userspace ALG framework in C using libnetfilter_queue. We implement FTP, SIP, and TFTP ALGs with full error handling, logging, and connection tracking.

### 11.1 Project Structure

```
alg-framework/
├── Makefile
├── include/
│   ├── alg_core.h          -- Core data structures and interfaces
│   ├── alg_conntrack.h     -- Connection tracking
│   ├── alg_ftp.h           -- FTP ALG
│   ├── alg_sip.h           -- SIP ALG
│   ├── alg_tftp.h          -- TFTP ALG
│   └── alg_log.h           -- Logging
├── src/
│   ├── main.c              -- Entry point, queue setup
│   ├── alg_core.c          -- Core packet handling
│   ├── alg_conntrack.c     -- Connection state tracking
│   ├── alg_ftp.c           -- FTP protocol parser
│   ├── alg_sip.c           -- SIP protocol parser
│   ├── alg_tftp.c          -- TFTP protocol parser
│   └── alg_log.c           -- Structured logging
└── tests/
    ├── test_ftp_parser.c
    ├── test_sip_parser.c
    └── corpus/             -- Fuzz corpus
```

### 11.2 Makefile

```makefile
# Makefile for ALG Framework

CC      = gcc
CFLAGS  = -Wall -Wextra -Werror -Wshadow -Wformat=2 \
          -D_FORTIFY_SOURCE=2 -fstack-protector-strong \
          -fPIE -O2 -g -ggdb3 \
          -Iinclude \
          $(shell pkg-config --cflags libnetfilter_queue) \
          $(shell pkg-config --cflags libnetfilter_conntrack)

LDFLAGS = -Wl,-z,relro -Wl,-z,now -pie \
          $(shell pkg-config --libs libnetfilter_queue) \
          $(shell pkg-config --libs libnetfilter_conntrack) \
          -lpthread

SRCS    = src/main.c \
          src/alg_core.c \
          src/alg_conntrack.c \
          src/alg_ftp.c \
          src/alg_sip.c \
          src/alg_tftp.c \
          src/alg_log.c

OBJS    = $(SRCS:.c=.o)
TARGET  = alg-framework

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Address Sanitizer build
asan: CFLAGS += -fsanitize=address,undefined -fno-omit-frame-pointer
asan: LDFLAGS += -fsanitize=address,undefined
asan: $(TARGET)-asan

$(TARGET)-asan: $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Fuzz build (libFuzzer)
fuzz_ftp: tests/fuzz_ftp_parser.c src/alg_ftp.c src/alg_log.c
	clang -fsanitize=fuzzer,address -g -Iinclude -o fuzz_ftp $^

fuzz_sip: tests/fuzz_sip_parser.c src/alg_sip.c src/alg_log.c
	clang -fsanitize=fuzzer,address -g -Iinclude -o fuzz_sip $^

# Unit tests
test: tests/test_ftp_parser.c src/alg_ftp.c src/alg_log.c
	$(CC) $(CFLAGS) -o test_ftp $^ $(LDFLAGS)
	./test_ftp

clean:
	rm -f $(OBJS) $(TARGET) $(TARGET)-asan fuzz_ftp fuzz_sip test_ftp

install: $(TARGET)
	install -m 0755 -o root -g root $(TARGET) /usr/local/sbin/
	install -m 0644 etc/alg-framework.service /etc/systemd/system/

.PHONY: all asan fuzz_ftp fuzz_sip test clean install
```

### 11.3 Core Header — alg_core.h

```c
// include/alg_core.h
// Core data structures for the ALG framework

#ifndef ALG_CORE_H
#define ALG_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <netinet/in.h>
#include <linux/netfilter.h>
#include <libnetfilter_queue/libnetfilter_queue.h>
#include <libnetfilter_conntrack/libnetfilter_conntrack.h>

// ============================================================
// Constants
// ============================================================

#define ALG_MAX_PACKET_SIZE     65536
#define ALG_MAX_PAYLOAD_SIZE    16384
#define ALG_MAX_CONN_ENTRIES    (1 << 17)   // 131072
#define ALG_MAX_EXPECT_ENTRIES  4096
#define ALG_HASH_SIZE           (1 << 16)   // 65536
#define ALG_VERSION             "1.0.0"

// ALG types
typedef enum {
    ALG_TYPE_NONE   = 0,
    ALG_TYPE_FTP    = 1,
    ALG_TYPE_SIP    = 2,
    ALG_TYPE_TFTP   = 3,
    ALG_TYPE_H323   = 4,
    ALG_TYPE_IRC    = 5,
    ALG_TYPE_SNMP   = 6,
    ALG_TYPE_MAX
} alg_type_t;

// ALG verdicts (what to do with the packet)
typedef enum {
    ALG_VERDICT_ACCEPT  = NF_ACCEPT,
    ALG_VERDICT_DROP    = NF_DROP,
    ALG_VERDICT_QUEUE   = NF_QUEUE,
    ALG_VERDICT_STOLEN  = NF_STOLEN,
} alg_verdict_t;

// Connection direction
typedef enum {
    CONN_DIR_ORIGINAL = 0,  // client -> server
    CONN_DIR_REPLY    = 1,  // server -> client
} conn_dir_t;

// Connection state (mirrors conntrack states)
typedef enum {
    CONN_STATE_NEW         = 0,
    CONN_STATE_ESTABLISHED = 1,
    CONN_STATE_RELATED     = 2,
    CONN_STATE_INVALID     = 3,
} conn_state_t;

// ============================================================
// Network address types
// ============================================================

typedef struct {
    int       family;       // AF_INET or AF_INET6
    union {
        struct in_addr  v4;
        struct in6_addr v6;
    } addr;
} alg_addr_t;

typedef struct {
    alg_addr_t addr;
    uint16_t   port;
} alg_endpoint_t;

typedef struct {
    alg_endpoint_t src;
    alg_endpoint_t dst;
    uint8_t        proto;   // IPPROTO_TCP, IPPROTO_UDP
} alg_tuple_t;

// ============================================================
// Expectation (for secondary/data connections)
// ============================================================

typedef void (*alg_expect_fn_t)(struct nf_expect *exp, void *data);

typedef struct alg_expectation {
    alg_tuple_t         tuple;      // expected connection tuple
    alg_tuple_t         mask;       // which fields must match
    alg_type_t          alg_type;
    uint32_t            timeout;    // seconds
    bool                permanent;  // don't delete after first match
    alg_expect_fn_t     nat_fn;     // NAT to apply when matched
    void               *nat_data;
    
    // List linkage
    struct alg_expectation *next;
    struct alg_expectation *prev;
} alg_expectation_t;

// ============================================================
// Connection entry (our userspace connection tracking)
// ============================================================

typedef struct alg_conn {
    alg_tuple_t         tuple;          // connection 5-tuple
    alg_type_t          alg_type;       // which ALG handles this
    conn_state_t        state;          // connection state
    
    // ALG-specific state (union for type safety)
    union {
        void *ftp_state;    // struct alg_ftp_state *
        void *sip_state;    // struct alg_sip_state *
        void *tftp_state;   // struct alg_tftp_state *
    } alg_data;
    
    // TCP sequence tracking (for payload modification)
    int32_t             seq_offset[2];  // per-direction sequence offsets
    
    // Timestamps
    uint64_t            created_ns;
    uint64_t            last_seen_ns;
    
    // Statistics
    uint64_t            pkts[2];
    uint64_t            bytes[2];
    
    // Linked expectations
    alg_expectation_t  *expectations;
    
    // Hash table linkage
    struct alg_conn    *hash_next;
} alg_conn_t;

// ============================================================
// Packet context (passed through processing pipeline)
// ============================================================

typedef struct {
    // Raw packet data
    unsigned char      *raw;
    uint32_t            raw_len;
    
    // Parsed headers (pointers into raw data)
    struct iphdr       *ip;
    struct ipv6hdr     *ip6;
    struct tcphdr      *tcp;
    struct udphdr      *udp;
    
    // Payload (application data)
    unsigned char      *payload;
    uint32_t            payload_len;
    
    // Connection info
    alg_tuple_t         tuple;
    conn_dir_t          direction;
    conn_state_t        ct_state;    // from conntrack
    
    // Associated connection (our tracking)
    alg_conn_t         *conn;
    
    // Nfqueue packet ID (for verdict)
    uint32_t            packet_id;
    
    // Modification tracking
    bool                modified;
    unsigned char      *new_payload;
    uint32_t            new_payload_len;
    int32_t             payload_delta;  // growth/shrinkage
} alg_pkt_t;

// ============================================================
// ALG plugin interface
// ============================================================

typedef struct alg_plugin {
    const char  *name;
    alg_type_t   type;
    uint16_t     port;          // well-known port (or 0 for multi-port)
    uint8_t      proto;         // IPPROTO_TCP or IPPROTO_UDP
    
    // Callbacks
    int (*init)(void);
    void (*fini)(void);
    
    // Called when a new connection matching this ALG is seen
    alg_conn_t *(*new_conn)(alg_pkt_t *pkt);
    
    // Called for each packet on a tracked connection
    alg_verdict_t (*process)(alg_pkt_t *pkt, alg_conn_t *conn);
    
    // Called when connection is destroyed
    void (*destroy_conn)(alg_conn_t *conn);
    
    // Called when an expectation fires (child connection)
    alg_conn_t *(*new_expect)(alg_pkt_t *pkt, alg_expectation_t *exp);
    
    // Plugin linkage
    struct alg_plugin *next;
} alg_plugin_t;

// ============================================================
// ALG framework context
// ============================================================

typedef struct {
    // Nfqueue handles
    struct nfq_handle   *nfq_h;
    struct nfq_q_handle *nfq_qh;
    int                  nfq_fd;
    uint16_t             queue_num;
    
    // Conntrack handle
    struct nfct_handle  *nfct_h;
    
    // Connection table (hash map)
    alg_conn_t         **conn_table;    // array of buckets
    uint32_t             conn_count;
    
    // Expectation table
    alg_expectation_t  **expect_table;
    uint32_t             expect_count;
    
    // Registered plugins
    alg_plugin_t        *plugins;
    
    // Configuration
    bool                 nat_enabled;
    bool                 strict_mode;   // drop on parse errors
    bool                 log_payloads;  // log decrypted payloads (WARNING)
    
    // Statistics
    uint64_t             total_pkts;
    uint64_t             dropped_pkts;
    uint64_t             modified_pkts;
    uint64_t             expect_created;
    uint64_t             expect_matched;
} alg_ctx_t;

// ============================================================
// Function declarations
// ============================================================

// Framework initialization
alg_ctx_t *alg_ctx_create(uint16_t queue_num);
void alg_ctx_destroy(alg_ctx_t *ctx);

// Plugin registration
int alg_register_plugin(alg_ctx_t *ctx, alg_plugin_t *plugin);

// Main processing loop
int alg_run(alg_ctx_t *ctx);

// Connection tracking
alg_conn_t *alg_conn_lookup(alg_ctx_t *ctx, const alg_tuple_t *tuple);
alg_conn_t *alg_conn_create(alg_ctx_t *ctx, const alg_tuple_t *tuple);
void alg_conn_destroy(alg_ctx_t *ctx, alg_conn_t *conn);

// Expectation management
alg_expectation_t *alg_expect_create(alg_ctx_t *ctx,
                                      alg_conn_t *master,
                                      const alg_tuple_t *tuple,
                                      const alg_tuple_t *mask,
                                      uint32_t timeout);
void alg_expect_destroy(alg_ctx_t *ctx, alg_expectation_t *exp);
alg_expectation_t *alg_expect_lookup(alg_ctx_t *ctx, const alg_tuple_t *tuple);

// Packet modification
int alg_pkt_replace_payload(alg_pkt_t *pkt,
                              uint32_t offset,
                              uint32_t old_len,
                              const unsigned char *new_data,
                              uint32_t new_len);

// Conntrack interaction
int alg_create_kernel_expectation(alg_ctx_t *ctx,
                                   const alg_tuple_t *master,
                                   const alg_tuple_t *expect,
                                   const alg_tuple_t *mask,
                                   uint32_t timeout);

// Utilities
uint32_t alg_tuple_hash(const alg_tuple_t *tuple);
bool alg_tuple_matches(const alg_tuple_t *t1, 
                       const alg_tuple_t *t2,
                       const alg_tuple_t *mask);
uint64_t alg_now_ns(void);
const char *alg_type_name(alg_type_t type);

#endif // ALG_CORE_H
```

### 11.4 Core Implementation — alg_core.c

```c
// src/alg_core.c
// Core packet processing and connection tracking

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/ip6.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <linux/netfilter.h>
#include <libnetfilter_queue/libnetfilter_queue.h>
#include <libnetfilter_conntrack/libnetfilter_conntrack.h>

#include "alg_core.h"
#include "alg_log.h"

// ============================================================
// Hash function (FNV-1a)
// ============================================================

#define FNV_OFFSET_BASIS_32  2166136261U
#define FNV_PRIME_32         16777619U

static uint32_t fnv1a_hash(const void *data, size_t len)
{
    const uint8_t *bytes = data;
    uint32_t hash = FNV_OFFSET_BASIS_32;
    
    for (size_t i = 0; i < len; i++) {
        hash ^= bytes[i];
        hash *= FNV_PRIME_32;
    }
    
    return hash;
}

uint32_t alg_tuple_hash(const alg_tuple_t *tuple)
{
    // Hash canonical form: always smaller IP first
    // This handles bidirectional lookup
    struct {
        uint32_t ip1, ip2;
        uint16_t port1, port2;
        uint8_t  proto;
    } key;
    
    memset(&key, 0, sizeof(key));
    key.proto = tuple->proto;
    
    // For IPv4 only (extend for IPv6)
    uint32_t src = tuple->src.addr.addr.v4.s_addr;
    uint32_t dst = tuple->dst.addr.addr.v4.s_addr;
    
    if (src <= dst) {
        key.ip1   = src;    key.ip2   = dst;
        key.port1 = tuple->src.port;
        key.port2 = tuple->dst.port;
    } else {
        key.ip1   = dst;    key.ip2   = src;
        key.port1 = tuple->dst.port;
        key.port2 = tuple->src.port;
    }
    
    return fnv1a_hash(&key, sizeof(key)) & (ALG_HASH_SIZE - 1);
}

// ============================================================
// Context lifecycle
// ============================================================

alg_ctx_t *alg_ctx_create(uint16_t queue_num)
{
    alg_ctx_t *ctx = calloc(1, sizeof(*ctx));
    if (!ctx) {
        ALG_LOG_ERROR("Failed to allocate context: %s", strerror(errno));
        return NULL;
    }
    
    ctx->queue_num = queue_num;
    
    // Allocate connection hash table
    ctx->conn_table = calloc(ALG_HASH_SIZE, sizeof(alg_conn_t *));
    if (!ctx->conn_table) {
        ALG_LOG_ERROR("Failed to allocate connection table");
        free(ctx);
        return NULL;
    }
    
    // Allocate expectation hash table
    ctx->expect_table = calloc(ALG_HASH_SIZE, sizeof(alg_expectation_t *));
    if (!ctx->expect_table) {
        ALG_LOG_ERROR("Failed to allocate expectation table");
        free(ctx->conn_table);
        free(ctx);
        return NULL;
    }
    
    // Open nfqueue handle
    ctx->nfq_h = nfq_open();
    if (!ctx->nfq_h) {
        ALG_LOG_ERROR("nfq_open() failed: %s", strerror(errno));
        goto err_free;
    }
    
    // Unbind existing handler for AF_INET (ignore errors)
    nfq_unbind_pf(ctx->nfq_h, AF_INET);
    nfq_unbind_pf(ctx->nfq_h, AF_INET6);
    
    // Bind to AF_INET and AF_INET6
    if (nfq_bind_pf(ctx->nfq_h, AF_INET) < 0) {
        ALG_LOG_ERROR("nfq_bind_pf(AF_INET) failed: %s", strerror(errno));
        goto err_nfq;
    }
    if (nfq_bind_pf(ctx->nfq_h, AF_INET6) < 0) {
        ALG_LOG_WARN("nfq_bind_pf(AF_INET6) failed (IPv6 unavailable?)");
    }
    
    // Create queue
    ctx->nfq_qh = nfq_create_queue(ctx->nfq_h, queue_num,
                                    alg_nfq_callback, ctx);
    if (!ctx->nfq_qh) {
        ALG_LOG_ERROR("nfq_create_queue(%u) failed", queue_num);
        goto err_nfq;
    }
    
    // Set copy mode: copy entire packet
    if (nfq_set_mode(ctx->nfq_qh, NFQNL_COPY_PACKET,
                     ALG_MAX_PACKET_SIZE) < 0) {
        ALG_LOG_ERROR("nfq_set_mode() failed");
        goto err_queue;
    }
    
    // Set queue max length (backlog)
    if (nfq_set_queue_maxlen(ctx->nfq_qh, 10240) < 0) {
        ALG_LOG_WARN("nfq_set_queue_maxlen() failed (non-fatal)");
    }
    
    // Enable conntrack information in nfqueue messages
    if (nfq_set_queue_flags(ctx->nfq_qh,
                             NFQA_CFG_F_CONNTRACK,
                             NFQA_CFG_F_CONNTRACK) < 0) {
        ALG_LOG_WARN("Failed to enable conntrack info in nfqueue");
    }
    
    ctx->nfq_fd = nfq_fd(ctx->nfq_h);
    
    // Open conntrack handle for expectation creation
    ctx->nfct_h = nfct_open(CONNTRACK, 0);
    if (!ctx->nfct_h) {
        ALG_LOG_WARN("nfct_open() failed: expectations via kernel disabled");
    }
    
    ALG_LOG_INFO("ALG context created, queue %u, fd %d",
                 queue_num, ctx->nfq_fd);
    return ctx;

err_queue:
    nfq_destroy_queue(ctx->nfq_qh);
err_nfq:
    nfq_close(ctx->nfq_h);
err_free:
    free(ctx->expect_table);
    free(ctx->conn_table);
    free(ctx);
    return NULL;
}

void alg_ctx_destroy(alg_ctx_t *ctx)
{
    if (!ctx) return;
    
    if (ctx->nfq_qh) nfq_destroy_queue(ctx->nfq_qh);
    if (ctx->nfq_h)  nfq_close(ctx->nfq_h);
    if (ctx->nfct_h) nfct_close(ctx->nfct_h);
    
    // TODO: free all connections and expectations
    
    free(ctx->conn_table);
    free(ctx->expect_table);
    free(ctx);
}

// ============================================================
// Nfqueue callback — main packet entry point
// ============================================================

static int alg_nfq_callback(struct nfq_q_handle *qh,
                              struct nfgenmsg *nfmsg __attribute__((unused)),
                              struct nfq_data *nfa,
                              void *data)
{
    alg_ctx_t *ctx = (alg_ctx_t *)data;
    alg_pkt_t   pkt = {0};
    alg_verdict_t verdict = ALG_VERDICT_ACCEPT;
    
    ctx->total_pkts++;
    
    // Get packet ID
    struct nfqnl_msg_packet_hdr *ph = nfq_get_msg_packet_hdr(nfa);
    if (!ph) {
        ALG_LOG_ERROR("No packet header");
        return nfq_set_verdict(qh, 0, NF_ACCEPT, 0, NULL);
    }
    pkt.packet_id = ntohl(ph->packet_id);
    
    // Get raw packet data
    pkt.raw_len = nfq_get_payload(nfa, &pkt.raw);
    if (pkt.raw_len < 0) {
        ALG_LOG_ERROR("nfq_get_payload failed");
        return nfq_set_verdict(qh, pkt.packet_id, NF_ACCEPT, 0, NULL);
    }
    
    // Parse the packet
    if (alg_parse_packet(&pkt) < 0) {
        // Malformed packet — accept but don't process
        return nfq_set_verdict(qh, pkt.packet_id, NF_ACCEPT, 0, NULL);
    }
    
    // Lookup or create connection
    pkt.conn = alg_conn_lookup(ctx, &pkt.tuple);
    
    if (!pkt.conn) {
        // New connection: check if any plugin handles this
        alg_plugin_t *plugin = alg_find_plugin(ctx, &pkt.tuple);
        if (plugin) {
            pkt.conn = plugin->new_conn(&pkt);
            if (pkt.conn) {
                alg_conn_insert(ctx, pkt.conn);
            }
        }
    }
    
    // Check expectations (for RELATED connections)
    if (!pkt.conn) {
        alg_expectation_t *exp = alg_expect_lookup(ctx, &pkt.tuple);
        if (exp) {
            // This is an expected secondary connection
            alg_plugin_t *plugin = alg_find_plugin_by_type(ctx, exp->alg_type);
            if (plugin && plugin->new_expect) {
                pkt.conn = plugin->new_expect(&pkt, exp);
            }
            alg_expect_destroy(ctx, exp);
        }
    }
    
    // Process the packet through the ALG
    if (pkt.conn) {
        alg_plugin_t *plugin = alg_find_plugin_by_type(ctx, pkt.conn->alg_type);
        if (plugin && plugin->process) {
            verdict = plugin->process(&pkt, pkt.conn);
            pkt.conn->last_seen_ns = alg_now_ns();
            pkt.conn->pkts[pkt.direction]++;
            pkt.conn->bytes[pkt.direction] += pkt.raw_len;
        }
    }
    
    // Apply verdict with possible modification
    if (verdict == ALG_VERDICT_DROP) {
        ctx->dropped_pkts++;
        return nfq_set_verdict(qh, pkt.packet_id, NF_DROP, 0, NULL);
    }
    
    if (pkt.modified && pkt.new_payload) {
        ctx->modified_pkts++;
        // Send modified packet
        // Note: we must reconstruct the full packet with new payload
        unsigned char *new_pkt = NULL;
        uint32_t new_pkt_len = 0;
        
        if (alg_rebuild_packet(&pkt, &new_pkt, &new_pkt_len) == 0) {
            int ret = nfq_set_verdict(qh, pkt.packet_id, NF_ACCEPT,
                                       new_pkt_len, new_pkt);
            free(new_pkt);
            free(pkt.new_payload);
            return ret;
        }
    }
    
    free(pkt.new_payload);
    return nfq_set_verdict(qh, pkt.packet_id, NF_ACCEPT, 0, NULL);
}

// ============================================================
// Packet parsing
// ============================================================

int alg_parse_packet(alg_pkt_t *pkt)
{
    if (pkt->raw_len < sizeof(struct iphdr)) {
        return -1;
    }
    
    struct iphdr *ip = (struct iphdr *)pkt->raw;
    
    if (ip->version == 4) {
        pkt->ip = ip;
        uint32_t ip_hlen = ip->ihl * 4;
        
        if (pkt->raw_len < ip_hlen) return -1;
        
        pkt->tuple.src.addr.family = AF_INET;
        pkt->tuple.dst.addr.family = AF_INET;
        pkt->tuple.src.addr.addr.v4.s_addr = ip->saddr;
        pkt->tuple.dst.addr.addr.v4.s_addr = ip->daddr;
        pkt->tuple.proto = ip->protocol;
        
        if (ip->protocol == IPPROTO_TCP) {
            if (pkt->raw_len < ip_hlen + sizeof(struct tcphdr)) return -1;
            pkt->tcp = (struct tcphdr *)(pkt->raw + ip_hlen);
            uint32_t tcp_hlen = pkt->tcp->doff * 4;
            
            pkt->tuple.src.port = ntohs(pkt->tcp->source);
            pkt->tuple.dst.port = ntohs(pkt->tcp->dest);
            
            pkt->payload = pkt->raw + ip_hlen + tcp_hlen;
            pkt->payload_len = pkt->raw_len - ip_hlen - tcp_hlen;
            
        } else if (ip->protocol == IPPROTO_UDP) {
            if (pkt->raw_len < ip_hlen + sizeof(struct udphdr)) return -1;
            pkt->udp = (struct udphdr *)(pkt->raw + ip_hlen);
            
            pkt->tuple.src.port = ntohs(pkt->udp->source);
            pkt->tuple.dst.port = ntohs(pkt->udp->dest);
            
            pkt->payload = pkt->raw + ip_hlen + sizeof(struct udphdr);
            pkt->payload_len = pkt->raw_len - ip_hlen - sizeof(struct udphdr);
        }
        
    } else if (ip->version == 6) {
        // IPv6 parsing
        if (pkt->raw_len < sizeof(struct ipv6hdr)) return -1;
        pkt->ip6 = (struct ipv6hdr *)pkt->raw;
        // ... (similar to IPv4, extended)
    } else {
        return -1;
    }
    
    return 0;
}

// ============================================================
// Main event loop
// ============================================================

int alg_run(alg_ctx_t *ctx)
{
    unsigned char buf[ALG_MAX_PACKET_SIZE + 256]; // extra for netlink headers
    int rv;
    
    ALG_LOG_INFO("ALG starting on queue %u", ctx->queue_num);
    
    // Set socket buffer size for high throughput
    int sock_buf_size = 64 * 1024 * 1024; // 64MB
    setsockopt(ctx->nfq_fd, SOL_SOCKET, SO_RCVBUFFORCE,
               &sock_buf_size, sizeof(sock_buf_size));
    
    while (1) {
        rv = recv(ctx->nfq_fd, buf, sizeof(buf), 0);
        if (rv < 0) {
            if (errno == EINTR) continue;
            if (errno == ENOBUFS) {
                // Queue overflow — packets were dropped
                ALG_LOG_WARN("NFQUEUE overflow — increase queue size or reduce load");
                ctx->dropped_pkts++;
                continue;
            }
            ALG_LOG_ERROR("recv() failed: %s", strerror(errno));
            return -1;
        }
        
        nfq_handle_packet(ctx->nfq_h, (char *)buf, rv);
    }
    
    return 0;
}

// ============================================================
// Timestamp utility
// ============================================================

uint64_t alg_now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}
```

### 11.5 FTP ALG Implementation — alg_ftp.c

```c
// src/alg_ftp.c
// FTP Application Layer Gateway implementation

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include "alg_core.h"
#include "alg_ftp.h"
#include "alg_log.h"

// ============================================================
// FTP State Machine
// ============================================================

typedef enum {
    FTP_STATE_IDLE         = 0,
    FTP_STATE_USER_SENT    = 1,
    FTP_STATE_PASS_SENT    = 2,
    FTP_STATE_AUTHENTICATED= 3,
    FTP_STATE_PORT_SEEN    = 4,
    FTP_STATE_PASV_REQUESTED = 5,
    FTP_STATE_PASV_CONFIRMED = 6,
    FTP_STATE_TRANSFER     = 7,
    FTP_STATE_AUTH_TLS     = 8,  // AUTH TLS seen: stop parsing
} ftp_state_t;

typedef struct {
    ftp_state_t state;
    
    // Data channel info
    struct in_addr  data_addr;      // address for data connection
    uint16_t        data_port;      // port for data connection
    bool            is_passive;     // true if PASV mode
    
    // Parser state
    uint32_t        last_seq[2];    // last sequence numbers (per direction)
    bool            partial[2];     // incomplete line buffered
    char            linebuf[2][512];// partial line buffer
    uint32_t        linebuf_len[2];
    
    // Extended modes
    bool            use_epsv;       // using EPSV/EPRT
    struct in6_addr eprt_addr;
    
    // Security
    bool            tls_active;     // AUTH TLS accepted: stop inspection
    bool            bounce_detected;// FTP bounce detected
} ftp_state_t;

// ============================================================
// FTP command detection helpers
// ============================================================

// Case-insensitive prefix match for FTP commands
static bool ftp_cmd_match(const char *line, size_t linelen,
                           const char *cmd, size_t *args_offset)
{
    size_t cmdlen = strlen(cmd);
    if (linelen < cmdlen) return false;
    
    for (size_t i = 0; i < cmdlen; i++) {
        if (toupper((unsigned char)line[i]) != toupper((unsigned char)cmd[i]))
            return false;
    }
    
    if (linelen == cmdlen || line[cmdlen] == ' ' || line[cmdlen] == '\r') {
        if (args_offset) {
            *args_offset = (linelen > cmdlen && line[cmdlen] == ' ')
                         ? cmdlen + 1 : cmdlen;
        }
        return true;
    }
    return false;
}

// Parse PORT h1,h2,h3,h4,p1,p2 command
// Returns 0 on success, -1 on failure
static int ftp_parse_port(const char *args, size_t argslen,
                            struct in_addr *addr, uint16_t *port)
{
    unsigned int h[4], p[2];
    char buf[64];
    
    if (argslen >= sizeof(buf)) return -1;
    memcpy(buf, args, argslen);
    buf[argslen] = '\0';
    
    // Strip trailing \r\n
    for (size_t i = argslen; i > 0; i--) {
        if (buf[i-1] == '\r' || buf[i-1] == '\n') buf[i-1] = '\0';
    }
    
    if (sscanf(buf, "%u,%u,%u,%u,%u,%u",
               &h[0], &h[1], &h[2], &h[3], &p[0], &p[1]) != 6) {
        return -1;
    }
    
    // Validate ranges
    for (int i = 0; i < 4; i++) {
        if (h[i] > 255) return -1;
    }
    for (int i = 0; i < 2; i++) {
        if (p[i] > 255) return -1;
    }
    
    addr->s_addr = htonl((h[0] << 24) | (h[1] << 16) | (h[2] << 8) | h[3]);
    *port = (uint16_t)(p[0] * 256 + p[1]);
    
    // Reject port 0 and ports < 1024 (security)
    if (*port == 0 || *port < 1024) {
        ALG_LOG_WARN("FTP PORT: rejected privileged port %u", *port);
        return -1;
    }
    
    return 0;
}

// Parse "227 Entering Passive Mode (h1,h2,h3,h4,p1,p2)"
// Returns 0 on success, -1 on failure
static int ftp_parse_pasv(const char *line, size_t linelen,
                            struct in_addr *addr, uint16_t *port)
{
    // Find the opening parenthesis
    const char *paren = memchr(line, '(', linelen);
    if (!paren) return -1;
    
    size_t remaining = linelen - (paren - line) - 1;
    return ftp_parse_port(paren + 1, remaining, addr, port);
}

// ============================================================
// FTP line processor — called for each complete FTP line
// ============================================================

static alg_verdict_t ftp_process_line(alg_pkt_t *pkt,
                                       alg_conn_t *conn,
                                       ftp_state_t *state,
                                       const char *line,
                                       size_t linelen,
                                       conn_dir_t dir,
                                       alg_ctx_t *ctx)
{
    // If TLS is active, we cannot read the content
    if (state->tls_active) return ALG_VERDICT_ACCEPT;
    
    size_t args_offset;
    
    // Client -> Server commands
    if (dir == CONN_DIR_ORIGINAL) {
        
        // USER command (track for logging, don't log password)
        if (ftp_cmd_match(line, linelen, "USER", &args_offset)) {
            state->state = FTP_STATE_USER_SENT;
            // Don't log credentials
            return ALG_VERDICT_ACCEPT;
        }
        
        // AUTH TLS: once this is sent, encryption begins on next reply
        if (ftp_cmd_match(line, linelen, "AUTH", &args_offset)) {
            const char *auth_args = line + args_offset;
            size_t auth_argslen = linelen - args_offset;
            if (auth_argslen >= 3 &&
                (strncasecmp(auth_args, "TLS", 3) == 0 ||
                 strncasecmp(auth_args, "SSL", 3) == 0)) {
                ALG_LOG_INFO("FTP: AUTH TLS detected, stopping payload inspection");
                // Don't set tls_active yet — wait for 234 response
            }
        }
        
        // PORT command (Active mode, client announces data addr)
        if (ftp_cmd_match(line, linelen, "PORT", &args_offset)) {
            struct in_addr port_addr;
            uint16_t port_port;
            
            if (ftp_parse_port(line + args_offset, linelen - args_offset,
                               &port_addr, &port_port) < 0) {
                ALG_LOG_WARN("FTP: Invalid PORT command");
                if (ctx->strict_mode) return ALG_VERDICT_DROP;
                return ALG_VERDICT_ACCEPT;
            }
            
            // Security check: PORT addr should match connection source
            // (prevent FTP bounce attacks)
            uint32_t src_ip = pkt->tuple.src.addr.addr.v4.s_addr;
            if (port_addr.s_addr != src_ip) {
                ALG_LOG_WARN("FTP: PORT bounce detected! "
                             "PORT addr=%s != src=%s",
                             inet_ntoa(port_addr),
                             inet_ntoa(*(struct in_addr*)&src_ip));
                state->bounce_detected = true;
                if (ctx->strict_mode) return ALG_VERDICT_DROP;
                // Even in non-strict mode, don't create expectation
                return ALG_VERDICT_ACCEPT;
            }
            
            state->data_addr = port_addr;
            state->data_port = port_port;
            state->is_passive = false;
            state->state = FTP_STATE_PORT_SEEN;
            
            // Create expectation for the data connection
            // Server (port 20) will connect to client's data addr:port
            alg_tuple_t exp_tuple = {
                .src = {
                    .addr = pkt->tuple.dst.addr,  // from server
                    .port = 20,                    // FTP data port
                },
                .dst = {
                    .addr = pkt->tuple.src.addr,  // to client
                    .port = port_port,
                },
                .proto = IPPROTO_TCP,
            };
            
            // Mask: match any source port from server (some servers use ephemeral)
            alg_tuple_t exp_mask = {
                .src = {
                    .addr.addr.v4.s_addr = 0xFFFFFFFF,  // exact server IP
                    .port = 0,                            // any port
                },
                .dst = {
                    .addr.addr.v4.s_addr = 0xFFFFFFFF,  // exact client IP
                    .port = 0xFFFF,                       // exact port
                },
                .proto = 0xFF,
            };
            
            alg_expect_create(ctx, conn, &exp_tuple, &exp_mask, 60);
            
            // If NAT is active, we need to rewrite the PORT command
            // to use the NAT public IP instead of the private IP
            // This is done in the NAT fixup (below)
            
            ALG_LOG_INFO("FTP: PORT %s:%u, expectation created",
                         inet_ntoa(port_addr), port_port);
            
            return ALG_VERDICT_ACCEPT;
        }
        
        // PASV command (Passive mode request)
        if (ftp_cmd_match(line, linelen, "PASV", NULL)) {
            state->is_passive = true;
            state->state = FTP_STATE_PASV_REQUESTED;
            return ALG_VERDICT_ACCEPT;
        }
        
        // EPSV command (Extended Passive)
        if (ftp_cmd_match(line, linelen, "EPSV", NULL)) {
            state->use_epsv = true;
            state->is_passive = true;
            state->state = FTP_STATE_PASV_REQUESTED;
            return ALG_VERDICT_ACCEPT;
        }
        
    // Server -> Client responses
    } else {
        // Parse response code
        if (linelen < 4) return ALG_VERDICT_ACCEPT;
        
        int code = 0;
        if (isdigit((unsigned char)line[0]) &&
            isdigit((unsigned char)line[1]) &&
            isdigit((unsigned char)line[2])) {
            code = ((line[0] - '0') * 100) +
                   ((line[1] - '0') * 10)  +
                   ((line[2] - '0'));
        }
        
        // 227 Entering Passive Mode
        if (code == 227 && state->state == FTP_STATE_PASV_REQUESTED) {
            struct in_addr pasv_addr;
            uint16_t pasv_port;
            
            if (ftp_parse_pasv(line, linelen, &pasv_addr, &pasv_port) < 0) {
                ALG_LOG_WARN("FTP: Invalid PASV response");
                return ALG_VERDICT_ACCEPT;
            }
            
            state->data_addr = pasv_addr;
            state->data_port = pasv_port;
            state->state = FTP_STATE_PASV_CONFIRMED;
            
            // Create expectation for client connecting to server's data port
            alg_tuple_t exp_tuple = {
                .src = pkt->tuple.dst,  // from client (any port)
                .dst = {
                    .addr = pkt->tuple.src.addr,  // to server
                    .port = pasv_port,
                },
                .proto = IPPROTO_TCP,
            };
            
            alg_tuple_t exp_mask = {
                .src = {
                    .addr.addr.v4.s_addr = 0xFFFFFFFF,
                    .port = 0,    // any client port
                },
                .dst = {
                    .addr.addr.v4.s_addr = 0xFFFFFFFF,
                    .port = 0xFFFF,
                },
                .proto = 0xFF,
            };
            
            alg_expect_create(ctx, conn, &exp_tuple, &exp_mask, 60);
            
            ALG_LOG_INFO("FTP: PASV %s:%u, expectation created",
                         inet_ntoa(pasv_addr), pasv_port);
            
            return ALG_VERDICT_ACCEPT;
        }
        
        // 229 Entering Extended Passive Mode
        if (code == 229 && state->use_epsv) {
            // Parse (|||port|)
            const char *pipe1 = memchr(line, '|', linelen);
            if (!pipe1) return ALG_VERDICT_ACCEPT;
            const char *pipe2 = memchr(pipe1 + 1, '|', linelen - (pipe1 - line) - 1);
            if (!pipe2) return ALG_VERDICT_ACCEPT;
            const char *pipe3 = memchr(pipe2 + 1, '|', linelen - (pipe2 - line) - 1);
            if (!pipe3) return ALG_VERDICT_ACCEPT;
            const char *pipe4 = memchr(pipe3 + 1, '|', linelen - (pipe3 - line) - 1);
            if (!pipe4) return ALG_VERDICT_ACCEPT;
            
            unsigned int epsv_port;
            if (sscanf(pipe3 + 1, "%u", &epsv_port) != 1) return ALG_VERDICT_ACCEPT;
            if (epsv_port == 0 || epsv_port > 65535) return ALG_VERDICT_ACCEPT;
            
            state->data_port = (uint16_t)epsv_port;
            state->state = FTP_STATE_PASV_CONFIRMED;
            
            // Create expectation (similar to PASV)
            ALG_LOG_INFO("FTP: EPSV port %u, expectation created", epsv_port);
        }
        
        // 234 Security Exchange Complete (AUTH TLS accepted)
        if (code == 234) {
            state->tls_active = true;
            ALG_LOG_INFO("FTP: TLS negotiation started, ALG disabling payload inspection");
        }
        
        // 426/550 Transfer aborted/failed: cleanup
        if (code == 426 || code == 550) {
            state->state = FTP_STATE_AUTHENTICATED;
        }
    }
    
    return ALG_VERDICT_ACCEPT;
}

// ============================================================
// FTP ALG Plugin callbacks
// ============================================================

static alg_conn_t *ftp_new_conn(alg_pkt_t *pkt)
{
    alg_conn_t *conn = calloc(1, sizeof(*conn));
    if (!conn) return NULL;
    
    conn->alg_type = ALG_TYPE_FTP;
    conn->tuple    = pkt->tuple;
    conn->state    = CONN_STATE_NEW;
    conn->created_ns = alg_now_ns();
    
    ftp_state_t *state = calloc(1, sizeof(*state));
    if (!state) { free(conn); return NULL; }
    
    state->state = FTP_STATE_IDLE;
    conn->alg_data.ftp_state = state;
    
    ALG_LOG_DEBUG("FTP: new connection %s:%u -> %s:%u",
                  inet_ntoa(pkt->tuple.src.addr.addr.v4),
                  pkt->tuple.src.port,
                  inet_ntoa(pkt->tuple.dst.addr.addr.v4),
                  pkt->tuple.dst.port);
    
    return conn;
}

static alg_verdict_t ftp_process(alg_pkt_t *pkt, alg_conn_t *conn)
{
    ftp_state_t *state = (ftp_state_t *)conn->alg_data.ftp_state;
    alg_verdict_t verdict = ALG_VERDICT_ACCEPT;
    
    if (!pkt->payload || pkt->payload_len == 0) return ALG_VERDICT_ACCEPT;
    
    // We need to process line by line
    // Handle TCP reassembly: lines may span packet boundaries
    const char *payload = (const char *)pkt->payload;
    uint32_t payload_len = pkt->payload_len;
    conn_dir_t dir = pkt->direction;
    
    uint32_t pos = 0;
    while (pos < payload_len) {
        // Find end of line (\r\n or just \n)
        uint32_t line_start = pos;
        uint32_t line_end = pos;
        
        while (line_end < payload_len &&
               payload[line_end] != '\n') {
            line_end++;
        }
        
        if (line_end >= payload_len) {
            // Partial line: buffer it
            uint32_t available = sizeof(state->linebuf[dir])
                               - state->linebuf_len[dir] - 1;
            uint32_t copy = payload_len - line_start;
            if (copy > available) {
                // Buffer overflow: discard
                state->linebuf_len[dir] = 0;
                ALG_LOG_WARN("FTP: Line too long, discarding");
            } else {
                memcpy(state->linebuf[dir] + state->linebuf_len[dir],
                       payload + line_start, copy);
                state->linebuf_len[dir] += copy;
            }
            break;
        }
        
        line_end++; // include the \n
        
        // Construct the full line (prepend any buffered data)
        char full_line[1024];
        uint32_t full_len = 0;
        
        if (state->linebuf_len[dir] > 0) {
            uint32_t copy = state->linebuf_len[dir];
            if (copy > sizeof(full_line) - 1) copy = sizeof(full_line) - 1;
            memcpy(full_line, state->linebuf[dir], copy);
            full_len = copy;
            state->linebuf_len[dir] = 0;
        }
        
        uint32_t line_len = line_end - line_start;
        if (full_len + line_len < sizeof(full_line)) {
            memcpy(full_line + full_len, payload + line_start, line_len);
            full_len += line_len;
        }
        
        // Process this complete line
        alg_ctx_t *ctx = /* get from thread-local or pkt */ NULL;
        verdict = ftp_process_line(pkt, conn, state,
                                   full_line, full_len, dir, ctx);
        
        if (verdict == ALG_VERDICT_DROP) return verdict;
        
        pos = line_end;
    }
    
    return verdict;
}

static void ftp_destroy_conn(alg_conn_t *conn)
{
    if (conn && conn->alg_data.ftp_state) {
        free(conn->alg_data.ftp_state);
        conn->alg_data.ftp_state = NULL;
    }
}

// FTP plugin definition
alg_plugin_t alg_ftp_plugin = {
    .name        = "ftp",
    .type        = ALG_TYPE_FTP,
    .port        = 21,
    .proto       = IPPROTO_TCP,
    .new_conn    = ftp_new_conn,
    .process     = ftp_process,
    .destroy_conn= ftp_destroy_conn,
};
```

### 11.6 SIP ALG Implementation — alg_sip.c

```c
// src/alg_sip.c
// SIP ALG implementation with SDP body parsing

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <arpa/inet.h>

#include "alg_core.h"
#include "alg_sip.h"
#include "alg_log.h"

// SIP methods
typedef enum {
    SIP_METHOD_UNKNOWN  = 0,
    SIP_METHOD_INVITE   = 1,
    SIP_METHOD_ACK      = 2,
    SIP_METHOD_BYE      = 3,
    SIP_METHOD_CANCEL   = 4,
    SIP_METHOD_REGISTER = 5,
    SIP_METHOD_OPTIONS  = 6,
    SIP_METHOD_INFO     = 7,
    SIP_METHOD_SUBSCRIBE= 8,
    SIP_METHOD_NOTIFY   = 9,
    SIP_METHOD_REFER    = 10,
    SIP_METHOD_UPDATE   = 11,
} sip_method_t;

// SIP dialog state
typedef enum {
    SIP_STATE_IDLE       = 0,
    SIP_STATE_CALLING    = 1,
    SIP_STATE_PROCEEDING = 2,
    SIP_STATE_CONFIRMED  = 3,
    SIP_STATE_TERMINATED = 4,
} sip_dialog_state_t;

// Media stream info (from SDP m= line)
#define SIP_MAX_MEDIA_STREAMS 8

typedef struct {
    char    media_type[32];   // "audio", "video", "application"
    uint16_t port;
    char    proto[32];        // "RTP/AVP", "RTP/SAVP"
    bool    active;
} sip_media_t;

// Per-connection SIP state
typedef struct {
    sip_dialog_state_t dialog_state;
    sip_method_t       last_method;
    
    // Call-ID for this dialog
    char   call_id[256];
    
    // SDP media streams
    sip_media_t media[SIP_MAX_MEDIA_STREAMS];
    int         media_count;
    
    // Connection address from SDP (c= line)
    struct in_addr sdp_conn_addr;
    bool           has_sdp_conn;
    
    // Origin address from SDP (o= line)
    struct in_addr sdp_orig_addr;
    bool           has_sdp_orig;
} sip_state_t;

// ============================================================
// SIP header parsing utilities
// ============================================================

// Find a header in a SIP message
// Returns pointer to header value (after colon+space), or NULL
static const char *sip_find_header(const char *msg, size_t msglen,
                                    const char *header)
{
    size_t hdrlen = strlen(header);
    const char *p = msg;
    const char *end = msg + msglen;
    
    while (p < end) {
        // Find end of this line
        const char *eol = p;
        while (eol < end && *eol != '\r' && *eol != '\n') eol++;
        
        size_t linelen = eol - p;
        
        // Check if this line starts with our header
        if (linelen > hdrlen + 1 &&
            strncasecmp(p, header, hdrlen) == 0 &&
            (p[hdrlen] == ':' || p[hdrlen] == ' ')) {
            
            // Skip ': ' after header name
            const char *val = p + hdrlen;
            while (val < eol && (*val == ':' || *val == ' ')) val++;
            return val;  // points to header value
        }
        
        // Move to next line
        p = eol;
        if (p < end && *p == '\r') p++;
        if (p < end && *p == '\n') p++;
        
        // Blank line = end of headers
        if (p < end && (*p == '\r' || *p == '\n')) break;
    }
    
    return NULL;
}

// ============================================================
// SDP parsing
// ============================================================

static int sip_parse_sdp(const char *sdp, size_t sdplen,
                           sip_state_t *state, alg_pkt_t *pkt,
                           alg_conn_t *conn, alg_ctx_t *ctx)
{
    const char *p = sdp;
    const char *end = sdp + sdplen;
    
    state->media_count = 0;
    state->has_sdp_conn = false;
    state->has_sdp_orig = false;
    
    while (p < end) {
        const char *eol = p;
        while (eol < end && *eol != '\r' && *eol != '\n') eol++;
        
        size_t linelen = eol - p;
        if (linelen == 0) { p = eol + 1; continue; }
        
        char type = p[0];
        
        if (linelen < 2 || p[1] != '=') {
            p = eol;
            while (p < end && (*p == '\r' || *p == '\n')) p++;
            continue;
        }
        
        const char *value = p + 2;
        size_t valuelen = eol - value;
        
        switch (type) {
        
        // o= (origin): o=username sess-id sess-ver nettype addrtype addr
        case 'o': {
            // Parse: "- 12345 12345 IN IP4 192.168.1.10"
            char username[64], nettype[16], addrtype[16], addr[64];
            unsigned long long sess_id, sess_ver;
            char buf[256];
            if (valuelen >= sizeof(buf)) break;
            memcpy(buf, value, valuelen);
            buf[valuelen] = '\0';
            
            if (sscanf(buf, "%63s %llu %llu %15s %15s %63s",
                       username, &sess_id, &sess_ver,
                       nettype, addrtype, addr) == 6) {
                if (strcmp(addrtype, "IP4") == 0) {
                    if (inet_pton(AF_INET, addr, &state->sdp_orig_addr) == 1) {
                        state->has_sdp_orig = true;
                        // NAT rewrite: replace addr with public IP
                        // (implementation would patch the payload here)
                    }
                }
            }
            break;
        }
        
        // c= (connection): c=IN IP4 192.168.1.10
        case 'c': {
            char nettype[16], addrtype[16], addr[64];
            char buf[128];
            if (valuelen >= sizeof(buf)) break;
            memcpy(buf, value, valuelen);
            buf[valuelen] = '\0';
            
            if (sscanf(buf, "%15s %15s %63s", nettype, addrtype, addr) == 3) {
                if (strcmp(addrtype, "IP4") == 0) {
                    if (inet_pton(AF_INET, addr, &state->sdp_conn_addr) == 1) {
                        state->has_sdp_conn = true;
                        // NAT rewrite would happen here
                    }
                }
            }
            break;
        }
        
        // m= (media): m=audio 49170 RTP/AVP 0 8
        case 'm': {
            if (state->media_count >= SIP_MAX_MEDIA_STREAMS) break;
            
            sip_media_t *media = &state->media[state->media_count];
            char buf[256];
            if (valuelen >= sizeof(buf)) break;
            memcpy(buf, value, valuelen);
            buf[valuelen] = '\0';
            
            unsigned int port;
            if (sscanf(buf, "%31s %u %31s",
                       media->media_type, &port,
                       media->proto) >= 2) {
                
                if (port > 0 && port <= 65535) {
                    media->port = (uint16_t)port;
                    media->active = true;
                    state->media_count++;
                    
                    // Determine media address (from c= line)
                    struct in_addr media_addr = state->has_sdp_conn
                        ? state->sdp_conn_addr
                        : pkt->tuple.src.addr.addr.v4;
                    
                    // Create expectation for RTP
                    alg_tuple_t exp_rtp = {
                        .src = pkt->tuple.dst,      // from remote party
                        .dst = {
                            .addr.family = AF_INET,
                            .addr.addr.v4 = media_addr,
                            .port = port,
                        },
                        .proto = IPPROTO_UDP,
                    };
                    
                    alg_tuple_t exp_mask_rtp = {
                        .src = {
                            .addr.addr.v4.s_addr = 0xFFFFFFFF,
                            .port = 0,          // any source port
                        },
                        .dst = {
                            .addr.addr.v4.s_addr = 0xFFFFFFFF,
                            .port = 0xFFFF,
                        },
                        .proto = 0xFF,
                    };
                    
                    alg_expect_create(ctx, conn, &exp_rtp, &exp_mask_rtp,
                                      conn->alg_data.sip_state
                                      ? 3600 : 60);
                    
                    // Create expectation for RTCP (port + 1)
                    if (port < 65535) {
                        alg_tuple_t exp_rtcp = exp_rtp;
                        exp_rtcp.dst.port = port + 1;
                        alg_expect_create(ctx, conn, &exp_rtcp,
                                          &exp_mask_rtp, 3600);
                    }
                    
                    ALG_LOG_INFO("SIP: SDP media %s port %u, expectations created",
                                 media->media_type, port);
                }
            }
            break;
        }
        }
        
        p = eol;
        while (p < end && (*p == '\r' || *p == '\n')) p++;
    }
    
    return 0;
}

// ============================================================
// SIP message processing
// ============================================================

static alg_verdict_t sip_process(alg_pkt_t *pkt, alg_conn_t *conn)
{
    sip_state_t *state = (sip_state_t *)conn->alg_data.sip_state;
    
    if (!pkt->payload || pkt->payload_len < 7) return ALG_VERDICT_ACCEPT;
    
    const char *payload = (const char *)pkt->payload;
    size_t payload_len = pkt->payload_len;
    
    // Determine if this is a request or response
    bool is_request = (strncmp(payload, "SIP/2.0", 7) != 0);
    
    if (is_request) {
        // Parse method
        const char *sp = memchr(payload, ' ', payload_len < 20 ? payload_len : 20);
        if (!sp) return ALG_VERDICT_ACCEPT;
        
        size_t method_len = sp - payload;
        
        if (method_len == 6 && strncasecmp(payload, "INVITE", 6) == 0) {
            state->last_method = SIP_METHOD_INVITE;
            state->dialog_state = SIP_STATE_CALLING;
        } else if (method_len == 3 && strncasecmp(payload, "BYE", 3) == 0) {
            state->last_method = SIP_METHOD_BYE;
            state->dialog_state = SIP_STATE_TERMINATED;
        }
    } else {
        // Parse response code
        if (payload_len < 12) return ALG_VERDICT_ACCEPT;
        
        int code = 0;
        if (isdigit((unsigned char)payload[8]) &&
            isdigit((unsigned char)payload[9]) &&
            isdigit((unsigned char)payload[10])) {
            code = ((payload[8] - '0') * 100) +
                   ((payload[9] - '0') * 10)  +
                   ((payload[10] - '0'));
        }
        
        if (code >= 200 && code < 300 &&
            state->last_method == SIP_METHOD_INVITE) {
            state->dialog_state = SIP_STATE_CONFIRMED;
        }
    }
    
    // Find and parse SDP body
    // The SDP body starts after the blank line (\r\n\r\n)
    const char *blank_line = NULL;
    for (size_t i = 0; i + 3 < payload_len; i++) {
        if (payload[i] == '\r' && payload[i+1] == '\n' &&
            payload[i+2] == '\r' && payload[i+3] == '\n') {
            blank_line = payload + i + 4;
            break;
        }
    }
    
    if (blank_line && blank_line < payload + payload_len) {
        size_t sdp_len = (payload + payload_len) - blank_line;
        
        // Verify Content-Type is SDP
        const char *ct = sip_find_header(payload, payload_len, "Content-Type");
        if (ct && strncasecmp(ct, "application/sdp", 15) == 0) {
            alg_ctx_t *ctx = NULL; // thread-local
            sip_parse_sdp(blank_line, sdp_len, state, pkt, conn, ctx);
        }
    }
    
    return ALG_VERDICT_ACCEPT;
}

static alg_conn_t *sip_new_conn(alg_pkt_t *pkt)
{
    alg_conn_t *conn = calloc(1, sizeof(*conn));
    if (!conn) return NULL;
    
    conn->alg_type = ALG_TYPE_SIP;
    conn->tuple    = pkt->tuple;
    conn->state    = CONN_STATE_NEW;
    conn->created_ns = alg_now_ns();
    
    sip_state_t *state = calloc(1, sizeof(*state));
    if (!state) { free(conn); return NULL; }
    
    state->dialog_state = SIP_STATE_IDLE;
    conn->alg_data.sip_state = state;
    
    return conn;
}

static void sip_destroy_conn(alg_conn_t *conn)
{
    if (conn && conn->alg_data.sip_state) {
        free(conn->alg_data.sip_state);
        conn->alg_data.sip_state = NULL;
    }
}

alg_plugin_t alg_sip_plugin = {
    .name        = "sip",
    .type        = ALG_TYPE_SIP,
    .port        = 5060,
    .proto       = IPPROTO_UDP,
    .new_conn    = sip_new_conn,
    .process     = sip_process,
    .destroy_conn= sip_destroy_conn,
};
```

### 11.7 Kernel Expectation Creation via libnetfilter_conntrack

```c
// src/alg_kernel_expect.c
// Create kernel-level conntrack expectations for proper RELATED tracking

#include <libnetfilter_conntrack/libnetfilter_conntrack.h>
#include <libnetfilter_conntrack/libnetfilter_conntrack_tcp.h>
#include "alg_core.h"
#include "alg_log.h"

int alg_create_kernel_expectation(alg_ctx_t *ctx,
                                   const alg_tuple_t *master,
                                   const alg_tuple_t *expect,
                                   const alg_tuple_t *mask,
                                   uint32_t timeout)
{
    if (!ctx->nfct_h) {
        ALG_LOG_WARN("No conntrack handle: kernel expectation not created");
        return -1;
    }
    
    struct nf_expect *exp = nfexp_new();
    if (!exp) {
        ALG_LOG_ERROR("nfexp_new() failed");
        return -1;
    }
    
    // Build master tuple
    struct nf_conntrack *master_ct = nfct_new();
    if (!master_ct) goto err;
    
    nfct_set_attr_u8(master_ct, ATTR_L3PROTO, AF_INET);
    nfct_set_attr_u8(master_ct, ATTR_L4PROTO, master->proto);
    nfct_set_attr_u32(master_ct, ATTR_IPV4_SRC,
                      master->src.addr.addr.v4.s_addr);
    nfct_set_attr_u32(master_ct, ATTR_IPV4_DST,
                      master->dst.addr.addr.v4.s_addr);
    nfct_set_attr_u16(master_ct, ATTR_PORT_SRC, htons(master->src.port));
    nfct_set_attr_u16(master_ct, ATTR_PORT_DST, htons(master->dst.port));
    
    // Build expected tuple
    struct nf_conntrack *exp_ct = nfct_new();
    if (!exp_ct) goto err;
    
    nfct_set_attr_u8(exp_ct, ATTR_L3PROTO, AF_INET);
    nfct_set_attr_u8(exp_ct, ATTR_L4PROTO, expect->proto);
    nfct_set_attr_u32(exp_ct, ATTR_IPV4_SRC,
                      expect->src.addr.addr.v4.s_addr);
    nfct_set_attr_u32(exp_ct, ATTR_IPV4_DST,
                      expect->dst.addr.addr.v4.s_addr);
    nfct_set_attr_u16(exp_ct, ATTR_PORT_SRC, htons(expect->src.port));
    nfct_set_attr_u16(exp_ct, ATTR_PORT_DST, htons(expect->dst.port));
    
    // Build mask tuple
    struct nf_conntrack *mask_ct = nfct_new();
    if (!mask_ct) goto err;
    
    nfct_set_attr_u8(mask_ct, ATTR_L3PROTO, AF_INET);
    nfct_set_attr_u8(mask_ct, ATTR_L4PROTO, 0xFF);
    nfct_set_attr_u32(mask_ct, ATTR_IPV4_SRC,
                      mask->src.addr.addr.v4.s_addr);
    nfct_set_attr_u32(mask_ct, ATTR_IPV4_DST,
                      mask->dst.addr.addr.v4.s_addr);
    nfct_set_attr_u16(mask_ct, ATTR_PORT_SRC, htons(mask->src.port));
    nfct_set_attr_u16(mask_ct, ATTR_PORT_DST, htons(mask->dst.port));
    
    // Assemble the expectation
    nfexp_set_attr(exp, ATTR_EXP_MASTER, master_ct);
    nfexp_set_attr(exp, ATTR_EXP_TUPLE,  exp_ct);
    nfexp_set_attr(exp, ATTR_EXP_MASK,   mask_ct);
    nfexp_set_attr_u32(exp, ATTR_EXP_TIMEOUT, timeout);
    
    // Send to kernel
    int ret = nfexp_query(ctx->nfct_h, NFCT_Q_CREATE, exp);
    if (ret < 0) {
        ALG_LOG_ERROR("nfexp_query(CREATE) failed: %s", strerror(errno));
    } else {
        ALG_LOG_DEBUG("Kernel expectation created for proto=%u dst_port=%u",
                      expect->proto, expect->dst.port);
    }
    
    nfct_destroy(master_ct);
    nfct_destroy(exp_ct);
    nfct_destroy(mask_ct);
    nfexp_destroy(exp);
    return ret;

err:
    if (master_ct) nfct_destroy(master_ct);
    if (exp_ct) nfct_destroy(exp_ct);
    if (mask_ct) nfct_destroy(mask_ct);
    nfexp_destroy(exp);
    return -1;
}
```

---

## 12. Rust Implementation — Full ALG Framework

### 12.1 Project Setup

```toml
# Cargo.toml
[package]
name = "alg-framework"
version = "1.0.0"
edition = "2021"
authors = ["Security Team"]
description = "Application Layer Gateway Framework in Rust"

[dependencies]
# Netfilter queue binding
nfq = "0.5"
# Network packet parsing
pnet = "0.34"
pnet_base = "0.34"
# Async runtime
tokio = { version = "1", features = ["full"] }
# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
# Error handling
thiserror = "1"
anyhow = "1"
# Byte manipulation
bytes = "1"
# IP address types
ipnetwork = "0.20"
# Configuration
serde = { version = "1", features = ["derive"] }
serde_json = "1"
# Metrics
prometheus = "0.13"
# Hash maps
dashmap = "5"
# Atomic types
crossbeam = "0.8"

[dev-dependencies]
criterion = "0.5"
arbitrary = { version = "1", features = ["derive"] }
# For fuzzing
afl = "0.12"

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"

[[bin]]
name = "alg"
path = "src/main.rs"

[[bench]]
name = "ftp_parser"
harness = false
```

### 12.2 Core Types — src/types.rs

```rust
// src/types.rs
// Core type definitions for the ALG framework

use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};
use thiserror::Error;

/// ALG processing errors
#[derive(Debug, Error)]
pub enum AlgError {
    #[error("Packet parse error: {0}")]
    ParseError(String),
    
    #[error("Protocol violation: {0}")]
    ProtocolViolation(String),
    
    #[error("Expectation table full")]
    ExpectTableFull,
    
    #[error("Connection table full")]
    ConnTableFull,
    
    #[error("Buffer too small: need {needed}, have {have}")]
    BufferTooSmall { needed: usize, have: usize },
    
    #[error("Invalid port: {0}")]
    InvalidPort(u16),
    
    #[error("Bounce attack detected: src={src} != port_addr={port_addr}")]
    BounceAttack {
        src: IpAddr,
        port_addr: IpAddr,
    },
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("NFQ error: {0}")]
    Nfq(String),
}

pub type AlgResult<T> = Result<T, AlgError>;

/// L3/L4 protocol identifier
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Protocol {
    Tcp,
    Udp,
    Gre,
    Sctp,
    Other(u8),
}

impl Protocol {
    pub fn from_u8(proto: u8) -> Self {
        match proto {
            6  => Protocol::Tcp,
            17 => Protocol::Udp,
            47 => Protocol::Gre,
            132 => Protocol::Sctp,
            p  => Protocol::Other(p),
        }
    }
    
    pub fn to_u8(self) -> u8 {
        match self {
            Protocol::Tcp  => 6,
            Protocol::Udp  => 17,
            Protocol::Gre  => 47,
            Protocol::Sctp => 132,
            Protocol::Other(p) => p,
        }
    }
}

/// Network endpoint (IP address + port)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Endpoint {
    pub addr: IpAddr,
    pub port: u16,
}

impl Endpoint {
    pub fn new(addr: IpAddr, port: u16) -> Self {
        Self { addr, port }
    }
    
    pub fn new_v4(a: u8, b: u8, c: u8, d: u8, port: u16) -> Self {
        Self {
            addr: IpAddr::V4(Ipv4Addr::new(a, b, c, d)),
            port,
        }
    }
}

impl std::fmt::Display for Endpoint {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self.addr {
            IpAddr::V4(v4) => write!(f, "{}:{}", v4, self.port),
            IpAddr::V6(v6) => write!(f, "[{}]:{}", v6, self.port),
        }
    }
}

/// 5-tuple connection identifier
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Tuple {
    pub src:   Endpoint,
    pub dst:   Endpoint,
    pub proto: Protocol,
}

impl Tuple {
    /// Get the reverse tuple (swap src and dst)
    pub fn reverse(&self) -> Self {
        Self {
            src:   self.dst,
            dst:   self.src,
            proto: self.proto,
        }
    }
    
    /// Canonical form (smaller IP first) for symmetric lookup
    pub fn canonical(&self) -> Self {
        let src_bytes = match self.src.addr {
            IpAddr::V4(v) => u128::from(v.to_bits() as u128),
            IpAddr::V6(v) => u128::from_be_bytes(v.octets()),
        };
        let dst_bytes = match self.dst.addr {
            IpAddr::V4(v) => u128::from(v.to_bits() as u128),
            IpAddr::V6(v) => u128::from_be_bytes(v.octets()),
        };
        
        if src_bytes <= dst_bytes {
            *self
        } else {
            self.reverse()
        }
    }
}

impl std::fmt::Display for Tuple {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{} -> {} ({:?})", self.src, self.dst, self.proto)
    }
}

/// Connection direction
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Original, // Client -> Server
    Reply,    // Server -> Client
}

/// ALG verdict for a packet
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    Accept,
    Drop,
    Modified(usize), // payload was modified, new length
}

/// ALG type identifier
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AlgType {
    Ftp,
    Sip,
    Tftp,
    H323,
    Irc,
    Snmp,
    Custom(u32),
}

/// Parsed packet context
#[derive(Debug)]
pub struct PacketCtx<'a> {
    /// Raw packet bytes
    pub raw: &'a [u8],
    
    /// IPv4/IPv6 header
    pub ip_header_len: usize,
    
    /// Transport header (TCP/UDP)
    pub transport_header_len: usize,
    
    /// Application payload
    pub payload: &'a [u8],
    
    /// Parsed tuple
    pub tuple: Tuple,
    
    /// Packet direction (relative to tracked connection)
    pub direction: Direction,
}

impl<'a> PacketCtx<'a> {
    /// Return the payload as a string slice (if valid UTF-8/ASCII)
    pub fn payload_str(&self) -> Option<&str> {
        std::str::from_utf8(self.payload).ok()
    }
}

/// An expectation: expected future connection
#[derive(Debug, Clone)]
pub struct Expectation {
    pub tuple:    Tuple,
    pub mask:     TupleMask,
    pub alg_type: AlgType,
    pub timeout:  std::time::Duration,
    pub master_tuple: Tuple,
}

/// Mask for expectation matching (which fields must match)
#[derive(Debug, Clone)]
pub struct TupleMask {
    pub src_addr_exact: bool,
    pub src_port_exact: bool,
    pub dst_addr_exact: bool,
    pub dst_port_exact: bool,
    pub proto_exact:    bool,
}

impl TupleMask {
    /// Match only destination IP and port, any source
    pub fn dst_only() -> Self {
        Self {
            src_addr_exact: false,
            src_port_exact: false,
            dst_addr_exact: true,
            dst_port_exact: true,
            proto_exact: true,
        }
    }
    
    /// Match source IP, destination IP and port (any source port)
    pub fn src_ip_dst() -> Self {
        Self {
            src_addr_exact: true,
            src_port_exact: false,
            dst_addr_exact: true,
            dst_port_exact: true,
            proto_exact: true,
        }
    }
}
```

### 12.3 FTP Parser — src/alg/ftp.rs

```rust
// src/alg/ftp.rs
// FTP Application Layer Gateway — pure parser (no unsafe code)

use std::net::{IpAddr, Ipv4Addr};
use tracing::{debug, warn, info, error};

use crate::types::*;

/// FTP state machine states
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FtpState {
    Idle,
    UserSent,
    Authenticated,
    PortSeen { addr: Ipv4Addr, port: u16 },
    PasvRequested,
    PasvConfirmed { addr: Ipv4Addr, port: u16 },
    Transfer,
    AuthTls,    // TLS negotiation started — stop inspecting
}

/// FTP connection state
#[derive(Debug)]
pub struct FtpConnState {
    pub state:         FtpState,
    pub tls_active:    bool,
    pub use_epsv:      bool,
    
    // Line buffer for split-packet handling
    // TCP can split a single FTP line across multiple packets
    line_buf: [Vec<u8>; 2],  // indexed by Direction
    
    // Sequence tracking for payload modification
    pub seq_offset: [i32; 2],
}

impl FtpConnState {
    pub fn new() -> Self {
        Self {
            state: FtpState::Idle,
            tls_active: false,
            use_epsv: false,
            line_buf: [Vec::new(), Vec::new()],
            seq_offset: [0, 0],
        }
    }
    
    fn dir_idx(dir: Direction) -> usize {
        match dir { Direction::Original => 0, Direction::Reply => 1 }
    }
}

/// FTP command parsed from a line
#[derive(Debug, Clone, PartialEq)]
pub enum FtpCommand {
    Port { addr: Ipv4Addr, port: u16 },
    Pasv,
    Eprt { family: u8, addr: IpAddr, port: u16 },
    Epsv,
    AuthTls,
    Other(String),
}

/// FTP response parsed from a line
#[derive(Debug, Clone, PartialEq)]
pub enum FtpResponse {
    EnteringPassive { addr: Ipv4Addr, port: u16 },   // 227
    EnteringExtendedPassive { port: u16 },             // 229
    SecurityExchangeComplete,                           // 234 (AUTH TLS)
    TransferComplete,                                   // 226
    Other { code: u16 },
}

/// Parse an FTP PORT command argument: "h1,h2,h3,h4,p1,p2"
/// Returns (Ipv4Addr, port) on success
pub fn parse_port_arg(args: &str) -> AlgResult<(Ipv4Addr, u16)> {
    let args = args.trim();
    let parts: Vec<&str> = args.split(',').collect();
    
    if parts.len() != 6 {
        return Err(AlgError::ParseError(
            format!("PORT: expected 6 comma-separated parts, got {}", parts.len())
        ));
    }
    
    let mut octets = [0u8; 4];
    for (i, part) in parts[..4].iter().enumerate() {
        let n: u32 = part.trim().parse()
            .map_err(|_| AlgError::ParseError(
                format!("PORT: invalid octet '{}'", part)
            ))?;
        if n > 255 {
            return Err(AlgError::ParseError(
                format!("PORT: octet {} out of range", n)
            ));
        }
        octets[i] = n as u8;
    }
    
    let p1: u32 = parts[4].trim().parse()
        .map_err(|_| AlgError::ParseError("PORT: invalid p1".to_string()))?;
    let p2: u32 = parts[5].trim().parse()
        .map_err(|_| AlgError::ParseError("PORT: invalid p2".to_string()))?;
    
    if p1 > 255 || p2 > 255 {
        return Err(AlgError::ParseError("PORT: port components out of range".to_string()));
    }
    
    let port = (p1 * 256 + p2) as u16;
    
    // Security: reject privileged ports
    if port < 1024 {
        return Err(AlgError::InvalidPort(port));
    }
    
    let addr = Ipv4Addr::new(octets[0], octets[1], octets[2], octets[3]);
    Ok((addr, port))
}

/// Parse "227 Entering Passive Mode (h1,h2,h3,h4,p1,p2)"
pub fn parse_pasv_response(line: &str) -> AlgResult<(Ipv4Addr, u16)> {
    let open_paren = line.find('(')
        .ok_or_else(|| AlgError::ParseError("PASV: no opening paren".to_string()))?;
    let close_paren = line[open_paren..].find(')')
        .ok_or_else(|| AlgError::ParseError("PASV: no closing paren".to_string()))?;
    
    let inner = &line[open_paren + 1 .. open_paren + close_paren];
    parse_port_arg(inner)
}

/// Parse "229 Entering Extended Passive Mode (|||port|)"
pub fn parse_epsv_response(line: &str) -> AlgResult<u16> {
    // Find (|||port|)
    let open_paren = line.find('(')
        .ok_or_else(|| AlgError::ParseError("EPSV: no opening paren".to_string()))?;
    let close_paren = line[open_paren..].find(')')
        .ok_or_else(|| AlgError::ParseError("EPSV: no closing paren".to_string()))?;
    
    let inner = &line[open_paren + 1 .. open_paren + close_paren];
    
    // Format: |delim|delim|port|  where delim is typically '|'
    if inner.len() < 4 {
        return Err(AlgError::ParseError("EPSV: response too short".to_string()));
    }
    
    let delim = inner.chars().next().unwrap();
    let parts: Vec<&str> = inner.split(delim).collect();
    
    if parts.len() < 4 {
        return Err(AlgError::ParseError("EPSV: invalid format".to_string()));
    }
    
    let port: u16 = parts[3].trim().parse()
        .map_err(|_| AlgError::ParseError("EPSV: invalid port".to_string()))?;
    
    if port < 1024 {
        return Err(AlgError::InvalidPort(port));
    }
    
    Ok(port)
}

/// Parse an FTP command line (client -> server)
pub fn parse_command(line: &str) -> FtpCommand {
    let line = line.trim_end_matches(|c| c == '\r' || c == '\n');
    
    if line.len() < 4 { return FtpCommand::Other(line.to_string()); }
    
    let (cmd, rest) = if let Some(pos) = line.find(' ') {
        (&line[..pos], line[pos+1..].trim())
    } else {
        (line, "")
    };
    
    let cmd_upper = cmd.to_uppercase();
    
    match cmd_upper.as_str() {
        "PORT" => {
            match parse_port_arg(rest) {
                Ok((addr, port)) => FtpCommand::Port { addr, port },
                Err(e) => {
                    warn!("FTP: Failed to parse PORT: {}", e);
                    FtpCommand::Other(line.to_string())
                }
            }
        }
        "PASV" => FtpCommand::Pasv,
        "EPSV" => FtpCommand::Epsv,
        "EPRT" => {
            // EPRT |family|address|port|
            // e.g., EPRT |1|192.168.1.10|49170|  (IPv4)
            //       EPRT |2|2001:db8::1|49170|    (IPv6)
            match parse_eprt(rest) {
                Ok((family, addr, port)) => FtpCommand::Eprt { family, addr, port },
                Err(e) => {
                    warn!("FTP: Failed to parse EPRT: {}", e);
                    FtpCommand::Other(line.to_string())
                }
            }
        }
        "AUTH" => {
            let rest_upper = rest.to_uppercase();
            if rest_upper.starts_with("TLS") || rest_upper.starts_with("SSL") {
                FtpCommand::AuthTls
            } else {
                FtpCommand::Other(line.to_string())
            }
        }
        _ => FtpCommand::Other(line.to_string()),
    }
}

/// Parse EPRT |family|address|port|
fn parse_eprt(args: &str) -> AlgResult<(u8, IpAddr, u16)> {
    if args.len() < 7 {
        return Err(AlgError::ParseError("EPRT: too short".to_string()));
    }
    
    let delim = args.chars().next().unwrap();
    let parts: Vec<&str> = args.split(delim).collect();
    
    if parts.len() < 5 {
        return Err(AlgError::ParseError("EPRT: insufficient parts".to_string()));
    }
    
    let family: u8 = parts[1].parse()
        .map_err(|_| AlgError::ParseError("EPRT: invalid family".to_string()))?;
    
    let addr: IpAddr = parts[2].parse()
        .map_err(|_| AlgError::ParseError(
            format!("EPRT: invalid address '{}'", parts[2])
        ))?;
    
    let port: u16 = parts[3].parse()
        .map_err(|_| AlgError::ParseError("EPRT: invalid port".to_string()))?;
    
    if port < 1024 {
        return Err(AlgError::InvalidPort(port));
    }
    
    Ok((family, addr, port))
}

/// Parse an FTP response line (server -> client)
pub fn parse_response(line: &str) -> Option<FtpResponse> {
    let line = line.trim_end_matches(|c| c == '\r' || c == '\n');
    
    if line.len() < 3 { return None; }
    
    let code_str = &line[..3];
    let code: u16 = code_str.parse().ok()?;
    
    // Continuation line (e.g., "220-Welcome")
    if line.len() > 3 && line.as_bytes()[3] == b'-' {
        return Some(FtpResponse::Other { code });
    }
    
    match code {
        227 => {
            match parse_pasv_response(line) {
                Ok((addr, port)) => Some(FtpResponse::EnteringPassive { addr, port }),
                Err(e) => {
                    warn!("FTP: Failed to parse PASV response: {}", e);
                    None
                }
            }
        }
        229 => {
            match parse_epsv_response(line) {
                Ok(port) => Some(FtpResponse::EnteringExtendedPassive { port }),
                Err(e) => {
                    warn!("FTP: Failed to parse EPSV response: {}", e);
                    None
                }
            }
        }
        234 => Some(FtpResponse::SecurityExchangeComplete),
        226 => Some(FtpResponse::TransferComplete),
        _ => Some(FtpResponse::Other { code }),
    }
}

/// FTP ALG processor: process a single FTP payload
/// Returns a list of expectations to create and optional verdict
pub struct FtpProcessor;

pub struct FtpProcessResult {
    pub expectations: Vec<ExpectationRequest>,
    pub verdict:      Verdict,
    pub state_change: Option<FtpState>,
}

/// Request to create an expectation
pub struct ExpectationRequest {
    pub tuple:      Tuple,
    pub mask:       TupleMask,
    pub alg_type:   AlgType,
    pub timeout_s:  u32,
}

impl FtpProcessor {
    pub fn process(
        pkt: &PacketCtx,
        conn_state: &mut FtpConnState,
        src_ip: Ipv4Addr,        // connection source IP (for bounce detection)
        strict_mode: bool,
    ) -> AlgResult<FtpProcessResult> {
        
        if conn_state.tls_active {
            return Ok(FtpProcessResult {
                expectations: vec![],
                verdict: Verdict::Accept,
                state_change: None,
            });
        }
        
        let dir_idx = FtpConnState::dir_idx(pkt.direction);
        let mut expectations = Vec::new();
        let mut verdict = Verdict::Accept;
        let mut state_change = None;
        
        // Append to line buffer
        let payload = pkt.payload;
        conn_state.line_buf[dir_idx].extend_from_slice(payload);
        
        // Process complete lines
        loop {
            let buf = &conn_state.line_buf[dir_idx];
            
            // Find \n (end of FTP line)
            let newline_pos = match buf.iter().position(|&b| b == b'\n') {
                Some(p) => p,
                None => break,  // no complete line yet
            };
            
            // Extract the complete line
            let line_bytes = buf[..=newline_pos].to_vec();
            let line = String::from_utf8_lossy(&line_bytes);
            
            // Remove consumed bytes from buffer
            conn_state.line_buf[dir_idx].drain(..=newline_pos);
            
            // Process this line based on direction
            match pkt.direction {
                Direction::Original => {
                    // Client -> Server: parse command
                    let cmd = parse_command(&line);
                    
                    match &cmd {
                        FtpCommand::Port { addr, port } => {
                            // Bounce attack detection
                            if IpAddr::V4(*addr) != IpAddr::V4(src_ip) {
                                warn!(
                                    "FTP: BOUNCE ATTACK DETECTED: PORT addr={} != src={}",
                                    addr, src_ip
                                );
                                if strict_mode {
                                    verdict = Verdict::Drop;
                                    break;
                                }
                                // Don't create expectation for bounce
                                continue;
                            }
                            
                            // Create expectation: server (port 20) -> client data port
                            let exp = ExpectationRequest {
                                tuple: Tuple {
                                    src: Endpoint::new(pkt.tuple.dst.addr, 20),
                                    dst: Endpoint::new(IpAddr::V4(*addr), *port),
                                    proto: Protocol::Tcp,
                                },
                                mask: TupleMask {
                                    src_addr_exact: true,
                                    src_port_exact: false, // any server port (not just 20)
                                    dst_addr_exact: true,
                                    dst_port_exact: true,
                                    proto_exact: true,
                                },
                                alg_type: AlgType::Ftp,
                                timeout_s: 60,
                            };
                            
                            expectations.push(exp);
                            state_change = Some(FtpState::PortSeen {
                                addr: *addr,
                                port: *port,
                            });
                            
                            info!("FTP: PORT {}:{} - expectation created", addr, port);
                        }
                        
                        FtpCommand::Pasv => {
                            state_change = Some(FtpState::PasvRequested);
                            debug!("FTP: PASV requested");
                        }
                        
                        FtpCommand::Epsv => {
                            conn_state.use_epsv = true;
                            state_change = Some(FtpState::PasvRequested);
                            debug!("FTP: EPSV requested");
                        }
                        
                        FtpCommand::Eprt { addr, port, .. } => {
                            // Similar to PORT but extended (IPv6 capable)
                            let exp = ExpectationRequest {
                                tuple: Tuple {
                                    src: Endpoint::new(pkt.tuple.dst.addr, 20),
                                    dst: Endpoint::new(*addr, *port),
                                    proto: Protocol::Tcp,
                                },
                                mask: TupleMask::src_ip_dst(),
                                alg_type: AlgType::Ftp,
                                timeout_s: 60,
                            };
                            expectations.push(exp);
                            info!("FTP: EPRT {}:{} - expectation created", addr, port);
                        }
                        
                        FtpCommand::AuthTls => {
                            // Wait for 234 response before disabling inspection
                            debug!("FTP: AUTH TLS requested");
                        }
                        
                        FtpCommand::Other(s) => {
                            debug!("FTP: command: {}", s.lines().next().unwrap_or(""));
                        }
                    }
                }
                
                Direction::Reply => {
                    // Server -> Client: parse response
                    if let Some(resp) = parse_response(&line) {
                        match resp {
                            FtpResponse::EnteringPassive { addr, port } => {
                                // Create expectation: client -> server data port
                                let exp = ExpectationRequest {
                                    tuple: Tuple {
                                        src: Endpoint::new(pkt.tuple.dst.addr, 0), // any client port
                                        dst: Endpoint::new(IpAddr::V4(addr), port),
                                        proto: Protocol::Tcp,
                                    },
                                    mask: TupleMask {
                                        src_addr_exact: true,
                                        src_port_exact: false,
                                        dst_addr_exact: true,
                                        dst_port_exact: true,
                                        proto_exact: true,
                                    },
                                    alg_type: AlgType::Ftp,
                                    timeout_s: 60,
                                };
                                expectations.push(exp);
                                state_change = Some(FtpState::PasvConfirmed { addr, port });
                                info!("FTP: PASV {}:{} - expectation created", addr, port);
                            }
                            
                            FtpResponse::EnteringExtendedPassive { port } => {
                                // Use server's IP from connection tuple
                                let server_ip = pkt.tuple.src.addr;
                                let exp = ExpectationRequest {
                                    tuple: Tuple {
                                        src: Endpoint::new(pkt.tuple.dst.addr, 0),
                                        dst: Endpoint::new(server_ip, port),
                                        proto: Protocol::Tcp,
                                    },
                                    mask: TupleMask::src_ip_dst(),
                                    alg_type: AlgType::Ftp,
                                    timeout_s: 60,
                                };
                                expectations.push(exp);
                                info!("FTP: EPSV port {} - expectation created", port);
                            }
                            
                            FtpResponse::SecurityExchangeComplete => {
                                conn_state.tls_active = true;
                                info!("FTP: TLS active - payload inspection disabled");
                            }
                            
                            _ => {}
                        }
                    }
                }
            }
        }
        
        // Apply state change
        if let Some(new_state) = &state_change {
            conn_state.state = new_state.clone();
        }
        
        Ok(FtpProcessResult {
            expectations,
            verdict,
            state_change,
        })
    }
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Ipv4Addr;
    
    #[test]
    fn test_parse_port_valid() {
        let (addr, port) = parse_port_arg("192,168,1,100,195,149").unwrap();
        assert_eq!(addr, Ipv4Addr::new(192, 168, 1, 100));
        assert_eq!(port, 195 * 256 + 149);  // 50069
    }
    
    #[test]
    fn test_parse_port_privileged() {
        // Port 80 = 0*256 + 80
        let result = parse_port_arg("192,168,1,100,0,80");
        assert!(matches!(result, Err(AlgError::InvalidPort(80))));
    }
    
    #[test]
    fn test_parse_port_out_of_range() {
        let result = parse_port_arg("192,168,1,100,256,0");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_parse_pasv_response() {
        let (addr, port) = parse_pasv_response(
            "227 Entering Passive Mode (192,168,1,100,195,149)"
        ).unwrap();
        assert_eq!(addr, Ipv4Addr::new(192, 168, 1, 100));
        assert_eq!(port, 50069);
    }
    
    #[test]
    fn test_parse_epsv_response() {
        let port = parse_epsv_response(
            "229 Entering Extended Passive Mode (|||50069|)"
        ).unwrap();
        assert_eq!(port, 50069);
    }
    
    #[test]
    fn test_parse_command_port() {
        let cmd = parse_command("PORT 192,168,1,100,195,149\r\n");
        assert!(matches!(cmd, FtpCommand::Port { addr, port }
            if addr == Ipv4Addr::new(192, 168, 1, 100) && port == 50069));
    }
    
    #[test]
    fn test_parse_command_pasv() {
        assert_eq!(parse_command("PASV\r\n"), FtpCommand::Pasv);
    }
    
    #[test]
    fn test_parse_command_auth_tls() {
        assert_eq!(parse_command("AUTH TLS\r\n"), FtpCommand::AuthTls);
        assert_eq!(parse_command("auth tls\r\n"), FtpCommand::AuthTls);
        assert_eq!(parse_command("AUTH SSL\r\n"), FtpCommand::AuthTls);
    }
    
    #[test]
    fn test_parse_eprt() {
        let cmd = parse_command("EPRT |1|192.168.1.10|49170|\r\n");
        assert!(matches!(cmd, FtpCommand::Eprt { family: 1, .. }));
    }
    
    #[test]
    fn test_parse_eprt_ipv6() {
        let cmd = parse_command("EPRT |2|2001:db8::1|49170|\r\n");
        assert!(matches!(cmd, FtpCommand::Eprt { family: 2, .. }));
    }
    
    #[test]
    fn test_bounce_detection() {
        // The FtpProcessor should detect bounce when PORT addr != connection src
        let src_ip = Ipv4Addr::new(192, 168, 1, 10);
        
        // Simulate a PORT command with different address (bounce attempt)
        let (port_addr, port) = parse_port_arg("10,0,0,1,195,149").unwrap();
        assert_ne!(IpAddr::V4(port_addr), IpAddr::V4(src_ip));
        // In strict mode, this would result in Verdict::Drop
    }
    
    // Test FTP multi-packet line handling
    #[test]
    fn test_split_packet_reassembly() {
        let mut state = FtpConnState::new();
        
        // First "packet" has incomplete line
        state.line_buf[0].extend_from_slice(b"PORT 192,168,1,100");
        
        // No complete line yet
        let buf = &state.line_buf[0];
        assert!(buf.iter().position(|&b| b == b'\n').is_none());
        
        // Second "packet" completes the line
        state.line_buf[0].extend_from_slice(b",195,149\r\n");
        
        let buf = &state.line_buf[0];
        let newline = buf.iter().position(|&b| b == b'\n');
        assert!(newline.is_some());
        
        let line_bytes = buf[..=newline.unwrap()].to_vec();
        let line = String::from_utf8_lossy(&line_bytes);
        
        let cmd = parse_command(&line);
        assert!(matches!(cmd, FtpCommand::Port { .. }));
    }
    
    // Fuzz-like: test many random inputs don't panic
    #[test]
    fn test_parse_port_fuzzing_samples() {
        let inputs = vec![
            "",
            "a",
            ",,,,,,",
            "999,999,999,999,999,999",
            "0,0,0,0,0,0",
            "256,0,0,0,0,0",
            "192,168,1,1,0,0",
            &"1,".repeat(1000),
        ];
        
        for input in inputs {
            // Must not panic
            let _ = parse_port_arg(input);
        }
    }
}
```

### 12.4 SIP Parser — src/alg/sip.rs

```rust
// src/alg/sip.rs
// SIP ALG with SDP parsing

use std::net::{IpAddr, Ipv4Addr};
use tracing::{debug, info, warn};
use crate::types::*;

/// SIP message type
#[derive(Debug, Clone, PartialEq)]
pub enum SipMessage {
    Request { method: SipMethod, uri: String },
    Response { code: u16, reason: String },
}

/// SIP methods
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum SipMethod {
    Invite,
    Ack,
    Bye,
    Cancel,
    Register,
    Options,
    Info,
    Subscribe,
    Notify,
    Refer,
    Update,
    Prack,
    Message,
    Other(String),
}

impl SipMethod {
    pub fn from_str(s: &str) -> Self {
        match s {
            "INVITE"    => SipMethod::Invite,
            "ACK"       => SipMethod::Ack,
            "BYE"       => SipMethod::Bye,
            "CANCEL"    => SipMethod::Cancel,
            "REGISTER"  => SipMethod::Register,
            "OPTIONS"   => SipMethod::Options,
            "INFO"      => SipMethod::Info,
            "SUBSCRIBE" => SipMethod::Subscribe,
            "NOTIFY"    => SipMethod::Notify,
            "REFER"     => SipMethod::Refer,
            "UPDATE"    => SipMethod::Update,
            "PRACK"     => SipMethod::Prack,
            "MESSAGE"   => SipMethod::Message,
            other       => SipMethod::Other(other.to_string()),
        }
    }
}

/// Parsed SDP media stream
#[derive(Debug, Clone)]
pub struct SdpMedia {
    pub media_type: String,     // audio, video, application
    pub port: u16,
    pub rtcp_port: u16,         // usually port + 1
    pub transport: String,      // RTP/AVP, RTP/SAVP, UDPTL
    pub direction: SdpDirection,
    pub connection: Option<IpAddr>, // override c= for this media
}

#[derive(Debug, Clone, PartialEq)]
pub enum SdpDirection {
    SendRecv,
    SendOnly,
    RecvOnly,
    Inactive,
}

/// Parsed SDP body
#[derive(Debug, Clone, Default)]
pub struct SdpBody {
    pub origin_addr: Option<IpAddr>,    // from o= line
    pub connection_addr: Option<IpAddr>, // from session-level c= line
    pub media: Vec<SdpMedia>,
}

/// Parse SDP body, returning extracted addresses and media streams
pub fn parse_sdp(sdp: &str) -> AlgResult<SdpBody> {
    let mut body = SdpBody::default();
    let mut current_media: Option<SdpMedia> = None;
    let mut current_direction = SdpDirection::SendRecv;
    
    for line in sdp.lines() {
        if line.len() < 2 || line.as_bytes()[1] != b'=' {
            continue;
        }
        
        let field_type = line.as_bytes()[0] as char;
        let value = &line[2..];
        
        match field_type {
            'o' => {
                // o=<username> <sess-id> <sess-ver> <nettype> <addrtype> <addr>
                let parts: Vec<&str> = value.splitn(6, ' ').collect();
                if parts.len() >= 6 {
                    if let Ok(addr) = parts[5].parse::<IpAddr>() {
                        body.origin_addr = Some(addr);
                        debug!("SDP o= addr: {}", addr);
                    }
                }
            }
            
            'c' => {
                // c=IN IP4 <addr>  or  c=IN IP6 <addr>
                let parts: Vec<&str> = value.splitn(3, ' ').collect();
                if parts.len() >= 3 {
                    if let Ok(addr) = parts[2].parse::<IpAddr>() {
                        if let Some(ref mut media) = current_media {
                            media.connection = Some(addr);
                        } else {
                            body.connection_addr = Some(addr);
                        }
                        debug!("SDP c= addr: {}", addr);
                    }
                }
            }
            
            'm' => {
                // m=<media> <port> <proto> <fmt> ...
                let parts: Vec<&str> = value.splitn(4, ' ').collect();
                if parts.len() >= 4 {
                    let media_type = parts[0].to_string();
                    if let Ok(port) = parts[1].parse::<u16>() {
                        let transport = parts[2].to_string();
                        let media = SdpMedia {
                            media_type,
                            port,
                            rtcp_port: port + 1,
                            transport,
                            direction: current_direction.clone(),
                            connection: None,
                        };
                        body.media.push(media);
                        current_media = Some(body.media.last().unwrap().clone());
                        debug!("SDP m= media: {}, port: {}", media.media_type, media.port);
                    }
                }
            }
```