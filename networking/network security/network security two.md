# Network Security: A Comprehensive Engineering Reference

> **Summary (4–8 lines):** This guide provides a first-principles, production-grade treatment of network security across the full stack — from Linux kernel internals and hardware offload through protocol stacks (L2–L7), routing, switching, overlays, cloud networking (AWS/GCP/Azure), zero-trust, eBPF-based enforcement, TLS/mTLS, and threat modeling. Every concept is backed by C or Rust implementation fragments, kernel data-structure references, and battle-tested operational patterns. The threat model is woven throughout, not bolted on. Aimed at systems engineers who need to reason about isolation boundaries, trust domains, packet fate, and cryptographic identity at every layer. References point to kernel source, RFCs, and production tooling. Where trade-offs exist they are made explicit with failure modes. Use this as a living reference alongside kernel source and protocol RFCs.

---

## Table of Contents

1. [Mental Model: The Attacker's View of a Network](#1-mental-model)
2. [Linux Kernel Networking Architecture](#2-linux-kernel-networking)
3. [Protocol Stack Deep-Dive (L2–L7)](#3-protocol-stack)
4. [Packet Lifecycle: Kernel to Wire](#4-packet-lifecycle)
5. [Netfilter, iptables, nftables](#5-netfilter)
6. [eBPF / XDP for Network Security](#6-ebpf-xdp)
7. [Routing Security](#7-routing-security)
8. [Switching Security (L2)](#8-switching-security)
9. [TLS/mTLS and PKI](#9-tls-mtls)
10. [Network Segmentation: VLANs, VXLANs, Geneve](#10-segmentation)
11. [Firewalls — Architecture and Implementation](#11-firewalls)
12. [Intrusion Detection and Prevention (IDS/IPS)](#12-ids-ips)
13. [DDoS — Taxonomy, Defense, Implementation](#13-ddos)
14. [Cloud Network Security — AWS, GCP, Azure](#14-cloud-security)
15. [Zero Trust Network Architecture](#15-zero-trust)
16. [Kubernetes Network Security](#16-kubernetes)
17. [Cryptographic Primitives in Network Security](#17-crypto)
18. [Threat Model Reference](#18-threat-model)
19. [Benchmarking, Fuzzing, Testing](#19-testing)
20. [Roll-out / Rollback Patterns](#20-rollout)
21. [References](#21-references)

---

## 1. Mental Model: The Attacker's View of a Network

Before any implementation, internalize the attacker's perspective. Every security control maps to an attacker capability it neutralizes.

```
ATTACKER CAPABILITIES vs. DEFENDER CONTROLS
─────────────────────────────────────────────────────────────────────────
Capability                    | Attack                | Control
──────────────────────────────┼───────────────────────┼──────────────────
Passive observation           | Traffic analysis,     | Encryption (TLS),
                              | credential theft      | traffic shaping
L2 access (same segment)      | ARP poison, MITM,     | DHCP snooping,
                              | MAC flood             | DAI, port security
L3 adjacency (routing)        | BGP hijack, route     | RPKI, route filters,
                              | injection, TTL attack | BFD, MD5
L4 access                     | SYN flood, RST inject,| SYN cookies,
                              | port scan             | stateful tracking
Application layer             | SQLi, SSRF, smuggling | WAF, input validation
Physical access               | Cable tap, hardware   | MACsec, fiber tap
                              | implant               | detection, HSM
Supply chain                  | Compromised image,    | SBOM, sigstore,
                              | malicious dep         | reproducible builds
Insider / credential          | Lateral movement      | mTLS, RBAC, 0trust
─────────────────────────────────────────────────────────────────────────
```

**Core security properties to enforce at each layer:**
- **Confidentiality** — encryption in transit and at rest
- **Integrity** — MACs, signatures, HMAC on protocol headers
- **Authenticity** — mutual authentication (mTLS, RPKI, DNSSEC)
- **Availability** — rate limiting, BFD fast-fail, anycast
- **Non-repudiation** — signed audit logs, certificate transparency

---

## 2. Linux Kernel Networking Architecture

### 2.1 Kernel Network Stack Overview

```
User Space
  └── socket() syscall → VFS → socket layer
           │
    ┌──────▼──────────────────────────────────────┐
    │           Socket Buffer (sk_buff)            │
    │   Protocol Families: AF_INET, AF_INET6,      │
    │   AF_PACKET, AF_UNIX, AF_NETLINK             │
    └──────┬──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │        L4: TCP / UDP / SCTP / DCCP           │
    │  tcp_sendmsg → tcp_write_xmit → ip_queue_xmit│
    └──────┬──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │        L3: IPv4 / IPv6 / MPLS                │
    │  ip_rcv → netfilter PRE_ROUTING              │
    │  ip_forward → netfilter FORWARD              │
    │  ip_local_deliver → netfilter POST_ROUTING   │
    └──────┬──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │      Netfilter / nftables / eBPF hooks       │
    │   XDP (driver/generic), TC ingress/egress    │
    └──────┬──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │           Network Device Layer               │
    │   struct net_device, NAPI poll, GRO/GSO      │
    │   ethtool, ring buffers, DMA                 │
    └──────┬──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │         Driver / Hardware / NIC              │
    │   SR-IOV, DPDK, AF_XDP, offload engines      │
    └─────────────────────────────────────────────┘
```

### 2.2 sk_buff — The Kernel's Packet Representation

`sk_buff` (`include/linux/skbuff.h`) is the central data structure. Understanding it is mandatory for any kernel-level network security work.

```c
// Simplified sk_buff — key security-relevant fields
// Source: include/linux/skbuff.h (Linux 6.x)
struct sk_buff {
    /* --- Connectivity --- */
    struct sk_buff      *next;
    struct sk_buff      *prev;
    struct sock         *sk;          // owning socket (NULL for forwarded pkts)
    struct net_device   *dev;         // ingress device

    /* --- Timestamps --- */
    ktime_t             tstamp;       // hardware or software timestamp

    /* --- Data pointers (critical for bounds checking) --- */
    unsigned char       *head;        // start of allocated buffer
    unsigned char       *data;        // start of packet data (moves on pull/push)
    unsigned char       *tail;        // end of packet data
    unsigned char       *end;         // end of allocated buffer
    unsigned int        len;          // total length
    unsigned int        data_len;     // length of paged data (frags)
    __u16               mac_len;      // length of MAC header
    __u16               hdr_len;      // writable header length of cloned skb

    /* --- Offload / checksum info --- */
    __u8                ip_summed:2;  // CHECKSUM_NONE/UNNECESSARY/COMPLETE/PARTIAL
    __u8                csum_valid:1;
    __wsum              csum;

    /* --- Marks and metadata --- */
    __u32               mark;         // used by netfilter, routing, tc
    __u32               priority;     // packet priority (maps to 802.1p / DSCP)
    __u16               queue_mapping;

    /* --- Security / conntrack --- */
    // nf_conntrack attached via skb->_nfct
    // secmark set by SELinux/iptables SECMARK target

    /* --- Netfilter state --- */
    __u8                nf_trace:1;
    __u8                ip_defrag_offset;

    /* --- GSO/GRO segmentation --- */
    struct skb_shared_info  *shinfo;  // at skb->end — frags, GSO size, etc.
};

// Header access macros — always use these, never cast data directly
// ip_hdr(skb)  → struct iphdr*   (after skb_reset_network_header)
// tcp_hdr(skb) → struct tcphdr*  (after skb_reset_transport_header)
// eth_hdr(skb) → struct ethhdr*  (after skb_reset_mac_header)
```

**Security implication:** Any kernel module or eBPF program that manipulates `skb->data` without proper bounds checks is a CVE waiting to happen. Always use `skb_pull()`, `skb_push()`, `pskb_may_pull()` — never raw pointer arithmetic.

### 2.3 NAPI and the Receive Path

```c
// Simplified NAPI poll — where packets enter the kernel
// net/core/dev.c
static int process_backlog(struct napi_struct *napi, int quota)
{
    struct net_device *backlog_dev = container_of(napi,
                                     struct softnet_data, backlog)->dev;
    struct softnet_data *sd;
    unsigned long start_time = jiffies + 1;
    int work = 0;

    // Pull packets off per-CPU queue (softirq context)
    while (again) {
        struct sk_buff *skb;
        // skb dequeued from sd->input_pkt_queue
        // → __netif_receive_skb() → delivers to protocol handlers
        // → calls into XDP/eBPF hooks at this point
    }
    return work;
}
```

**Security implication:** Buffer bloat and ring exhaustion are DoS vectors. Tune `net.core.netdev_max_backlog`, `net.core.rmem_max`, and use hardware rate limiting / RED on the NIC.

### 2.4 Network Namespaces

Network namespaces (`net/core/net_namespace.c`) provide the isolation primitive used by containers. Each namespace has its own:
- Routing tables (FIB)
- Interface set
- iptables/nftables rulesets
- conntrack table
- Unix socket namespace
- `/proc/net/` view

```c
// Creating a net namespace (simplified from net/core/net_namespace.c)
struct net *copy_net_ns(unsigned long flags,
                        struct user_namespace *user_ns,
                        struct net *old_net)
{
    struct net *net;
    int rv;

    net = net_alloc();          // allocate + zero struct net
    rv = setup_net(net, user_ns); // initialize FIB, loopback, etc.
    // Each subsystem registers via register_pernet_subsys()
    // and gets called here to init its per-ns state
    return net;
}
```

**Security implications:**
- Container breakouts that gain `CAP_NET_ADMIN` in the host namespace can reconfigure all network security controls
- veth pairs cross namespace boundaries — packets traverse netfilter twice (once per namespace)
- Always validate that your firewall rules apply in the correct namespace

```bash
# Enumerate all network namespaces on a host
ip netns list
ls -la /proc/*/net/dev | grep -v "^l" | sort -u

# Inspect rules in a container's namespace
nsenter --net=/proc/<pid>/ns/net ip route
nsenter --net=/proc/<pid>/ns/net nft list ruleset

# Verify isolation — can namespace A reach namespace B's lo?
ip netns exec ns-a ping 127.0.0.1  # must stay within ns-a
```

---

## 3. Protocol Stack Deep-Dive (L2–L7)

### 3.1 Layer 2 — Ethernet / MAC

```
Frame structure (802.3):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌──────────────────────────────────────────────────────────────────┐
│                    Destination MAC (6 bytes)                     │
│                                                ├─────────────────┤
│                    Source MAC (6 bytes)         │
├─────────────────────────────────────────────────┤
│  (Optional) 802.1Q VLAN Tag (4 bytes)           │
│  TPID=0x8100 | PCP(3) | DEI(1) | VLAN ID(12)   │
├──────────────────────────────────────────────────────────────────┤
│             EtherType / Length (2 bytes)                         │
├──────────────────────────────────────────────────────────────────┤
│             Payload (46–1500 bytes)                              │
├──────────────────────────────────────────────────────────────────┤
│             FCS / CRC32 (4 bytes)                                │
└──────────────────────────────────────────────────────────────────┘
```

**L2 attack surface:**
- **ARP spoofing** — gratuitous ARP poisons neighbor cache → MITM
- **MAC flooding** — exhaust CAM table → switch degrades to hub
- **VLAN hopping** — double-tagging 802.1Q frames to escape VLAN boundary
- **STP manipulation** — force topology changes to intercept traffic

**Rust: ARP packet parser with security validation**

```rust
// arp_parser.rs — parse and validate ARP packets
// Dependency: none (raw byte parsing)

use std::net::Ipv4Addr;

#[derive(Debug, Clone, PartialEq)]
pub enum ArpOpcode {
    Request,
    Reply,
    Unknown(u16),
}

#[derive(Debug, Clone)]
pub struct ArpPacket {
    pub htype: u16,        // hardware type (1 = Ethernet)
    pub ptype: u16,        // protocol type (0x0800 = IPv4)
    pub hlen: u8,          // hardware address length (6 for MAC)
    pub plen: u8,          // protocol address length (4 for IPv4)
    pub opcode: ArpOpcode,
    pub sha: [u8; 6],      // sender hardware address
    pub spa: Ipv4Addr,     // sender protocol address
    pub tha: [u8; 6],      // target hardware address
    pub tpa: Ipv4Addr,     // target protocol address
}

#[derive(Debug, thiserror::Error)]
pub enum ArpError {
    #[error("packet too short: got {got}, need {need}")]
    TooShort { got: usize, need: usize },
    #[error("invalid hardware type: {0}")]
    InvalidHType(u16),
    #[error("invalid protocol type: {0:#06x}")]
    InvalidPType(u16),
    #[error("invalid field lengths: hlen={hlen} plen={plen}")]
    InvalidLengths { hlen: u8, plen: u8 },
    #[error("gratuitous ARP from broadcast MAC — likely spoofing")]
    GratuitousBroadcast,
}

const ARP_MIN_LEN: usize = 28; // for Ethernet/IPv4

impl ArpPacket {
    pub fn parse(buf: &[u8]) -> Result<Self, ArpError> {
        if buf.len() < ARP_MIN_LEN {
            return Err(ArpError::TooShort {
                got: buf.len(),
                need: ARP_MIN_LEN,
            });
        }

        let htype = u16::from_be_bytes([buf[0], buf[1]]);
        let ptype = u16::from_be_bytes([buf[2], buf[3]]);
        let hlen = buf[4];
        let plen = buf[5];
        let op   = u16::from_be_bytes([buf[6], buf[7]]);

        // Strict validation — reject malformed/unexpected values
        if htype != 1 {
            return Err(ArpError::InvalidHType(htype));
        }
        if ptype != 0x0800 {
            return Err(ArpError::InvalidPType(ptype));
        }
        if hlen != 6 || plen != 4 {
            return Err(ArpError::InvalidLengths { hlen, plen });
        }

        let sha: [u8; 6] = buf[8..14].try_into().unwrap();
        let spa = Ipv4Addr::new(buf[14], buf[15], buf[16], buf[17]);
        let tha: [u8; 6] = buf[18..24].try_into().unwrap();
        let tpa = Ipv4Addr::new(buf[24], buf[25], buf[26], buf[27]);

        let opcode = match op {
            1 => ArpOpcode::Request,
            2 => ArpOpcode::Reply,
            n => ArpOpcode::Unknown(n),
        };

        // Security check: gratuitous ARP from broadcast = anomaly
        let broadcast = [0xff_u8; 6];
        if sha == broadcast && spa == tpa {
            return Err(ArpError::GratuitousBroadcast);
        }

        Ok(ArpPacket { htype, ptype, hlen, plen, opcode, sha, spa, tha, tpa })
    }

    /// Detect potential ARP spoofing: reply SHA differs from expected mapping
    pub fn is_suspicious_reply(
        &self,
        expected_mac: Option<&[u8; 6]>,
    ) -> bool {
        if self.opcode != ArpOpcode::Reply {
            return false;
        }
        // If we have a known mapping and the reply contradicts it
        expected_mac.map_or(false, |mac| &self.sha != mac)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn arp_reply(sha: [u8;6], spa: [u8;4], tha: [u8;6], tpa: [u8;4]) -> Vec<u8> {
        let mut p = vec![
            0x00, 0x01,  // htype = Ethernet
            0x08, 0x00,  // ptype = IPv4
            0x06,        // hlen
            0x04,        // plen
            0x00, 0x02,  // opcode = reply
        ];
        p.extend_from_slice(&sha);
        p.extend_from_slice(&spa);
        p.extend_from_slice(&tha);
        p.extend_from_slice(&tpa);
        p
    }

    #[test]
    fn test_valid_reply() {
        let pkt = arp_reply(
            [0xaa,0xbb,0xcc,0xdd,0xee,0xff],
            [192,168,1,1],
            [0x11,0x22,0x33,0x44,0x55,0x66],
            [192,168,1,2],
        );
        let arp = ArpPacket::parse(&pkt).unwrap();
        assert_eq!(arp.opcode, ArpOpcode::Reply);
    }

    #[test]
    fn test_spoof_detection() {
        let pkt = arp_reply(
            [0xde,0xad,0xbe,0xef,0x00,0x01], // attacker MAC
            [192,168,1,1],
            [0x11,0x22,0x33,0x44,0x55,0x66],
            [192,168,1,2],
        );
        let arp = ArpPacket::parse(&pkt).unwrap();
        let known_mac = [0xaa,0xbb,0xcc,0xdd,0xee,0xff]; // legit MAC
        assert!(arp.is_suspicious_reply(Some(&known_mac)));
    }
}
```

### 3.2 Layer 3 — IP (v4 and v6)

```
IPv4 Header (RFC 791):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─────┬──────┬──────────────────────────────────────────────────────┤
│ Ver │ IHL  │ DSCP/ECN  │           Total Length                  │
├─────┴──────┴───────────────────┬────────────────────────────────┤
│         Identification         │ Flags │    Fragment Offset      │
├────────────────────────────────┼────────────────────────────────┤
│    TTL    │    Protocol        │        Header Checksum          │
├────────────────────────────────────────────────────────────────┤
│                     Source IP Address                           │
├────────────────────────────────────────────────────────────────┤
│                  Destination IP Address                         │
├────────────────────────────────────────────────────────────────┤
│                    Options (if IHL > 5)                         │
└────────────────────────────────────────────────────────────────┘
```

**L3 Security Issues:**

| Attack | Mechanism | Mitigation |
|--------|-----------|------------|
| IP spoofing | Forge source IP | BCP38 ingress filtering, uRPF |
| Fragment attacks | Overlapping/tiny fragments | Reassembly in kernel, `net.ipv4.ipfrag_*` |
| IP options abuse | RR, LSRR, SSRR for source routing | `net.ipv4.conf.all.accept_source_route=0` |
| Smurf/amplification | Broadcast ICMP with spoofed src | `net.ipv4.icmp_echo_ignore_broadcasts=1` |
| TTL expiry DoS | Craft low-TTL packets to exhaust ICMP rate | `net.ipv4.icmp_ratelimit` |

**C: IP header parser with security checks**

```c
/* ip_validate.c — minimal, security-focused IP header validation
 * Compile: gcc -O2 -Wall -Wextra -o ip_validate ip_validate.c
 */
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <arpa/inet.h>
#include <stdio.h>

// RFC 791 IPv4 header — packed to match wire format
struct __attribute__((packed)) ipv4hdr {
    uint8_t  ihl_ver;       // version (4 bits) + IHL (4 bits)
    uint8_t  dscp_ecn;
    uint16_t tot_len;       // network byte order
    uint16_t id;
    uint16_t frag_off;      // flags (3 bits) + fragment offset (13 bits)
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t check;
    uint32_t saddr;         // network byte order
    uint32_t daddr;
};

#define IPV4_MIN_HDR   20   // bytes (IHL=5)
#define IPV4_MAX_HDR   60   // bytes (IHL=15)
#define IP_RF          0x8000   // reserved flag (must be 0, RFC 791)
#define IP_DF          0x4000   // don't fragment
#define IP_MF          0x2000   // more fragments
#define IP_OFFSET      0x1FFF   // fragment offset mask

typedef enum {
    IP_OK = 0,
    IP_ERR_TOO_SHORT,
    IP_ERR_BAD_VERSION,
    IP_ERR_BAD_IHL,
    IP_ERR_TOT_LEN_MISMATCH,
    IP_ERR_RESERVED_FLAG,
    IP_ERR_ZERO_TTL,
    IP_ERR_SOURCE_ROUTE,       // security: reject LSRR/SSRR
    IP_ERR_MARTIAN_SRC,        // BCP38: non-routable source
    IP_ERR_BAD_CHECKSUM,
} ip_verdict_t;

static uint16_t ip_checksum(const void *data, size_t len)
{
    const uint16_t *p = data;
    uint32_t sum = 0;
    while (len > 1) {
        sum += *p++;
        len -= 2;
    }
    if (len)
        sum += *(const uint8_t *)p;
    while (sum >> 16)
        sum = (sum & 0xffff) + (sum >> 16);
    return (uint16_t)~sum;
}

// BCP38 — check for non-routable (martian) source addresses
static bool is_martian(uint32_t addr_ne)
{
    uint32_t addr = ntohl(addr_ne);
    // 0.0.0.0/8
    if ((addr >> 24) == 0)          return true;
    // 127.0.0.0/8 — loopback
    if ((addr >> 24) == 127)        return true;
    // 169.254.0.0/16 — link-local
    if ((addr >> 16) == 0xa9fe)     return true;
    // 224.0.0.0/4 — multicast (not a valid source)
    if ((addr >> 28) == 0xe)        return true;
    // 240.0.0.0/4 — reserved
    if ((addr >> 28) == 0xf)        return true;
    return false;
}

ip_verdict_t validate_ipv4(const uint8_t *pkt, size_t pkt_len)
{
    if (pkt_len < IPV4_MIN_HDR)
        return IP_ERR_TOO_SHORT;

    const struct ipv4hdr *ip = (const struct ipv4hdr *)pkt;

    uint8_t version = (ip->ihl_ver >> 4) & 0xf;
    uint8_t ihl     = (ip->ihl_ver)      & 0xf;

    if (version != 4)
        return IP_ERR_BAD_VERSION;

    size_t hdr_bytes = (size_t)ihl * 4;
    if (ihl < 5 || hdr_bytes > pkt_len || hdr_bytes > IPV4_MAX_HDR)
        return IP_ERR_BAD_IHL;

    uint16_t tot_len = ntohs(ip->tot_len);
    if (tot_len < hdr_bytes || tot_len > pkt_len)
        return IP_ERR_TOT_LEN_MISMATCH;

    uint16_t flags_frag = ntohs(ip->frag_off);
    if (flags_frag & IP_RF)          // reserved bit set
        return IP_ERR_RESERVED_FLAG;

    if (ip->ttl == 0)
        return IP_ERR_ZERO_TTL;

    if (is_martian(ip->saddr))
        return IP_ERR_MARTIAN_SRC;

    // Checksum verification
    uint16_t orig_check = ip->check;
    // Cast-away const for checksum calc (common pattern)
    uint16_t calc;
    {
        struct ipv4hdr tmp;
        memcpy(&tmp, ip, hdr_bytes);
        tmp.check = 0;
        calc = ip_checksum(&tmp, hdr_bytes);
    }
    if (orig_check != calc)
        return IP_ERR_BAD_CHECKSUM;

    // Security: reject IP source routing options (LSRR=0x83, SSRR=0x89)
    if (ihl > 5) {
        const uint8_t *opt = pkt + IPV4_MIN_HDR;
        size_t opt_len = hdr_bytes - IPV4_MIN_HDR;
        size_t i = 0;
        while (i < opt_len) {
            uint8_t opt_type = opt[i];
            if (opt_type == 0x00) break;  // End of options
            if (opt_type == 0x01) { i++; continue; } // NOP
            if (opt_type == 0x83 || opt_type == 0x89)  // LSRR / SSRR
                return IP_ERR_SOURCE_ROUTE;
            if (i + 1 >= opt_len) break;
            uint8_t opt_len_field = opt[i + 1];
            if (opt_len_field < 2) break;  // malformed
            i += opt_len_field;
        }
    }

    return IP_OK;
}

int main(void)
{
    // Test: minimal valid IPv4 header (ICMP echo request, no options)
    uint8_t pkt[] = {
        0x45,             // ver=4, IHL=5
        0x00,             // DSCP/ECN
        0x00, 0x1c,       // total length = 28
        0x00, 0x00,       // id
        0x40, 0x00,       // DF set, no fragment
        0x40,             // TTL=64
        0x01,             // protocol=ICMP
        0x00, 0x00,       // checksum (fill below)
        0x0a, 0x00, 0x00, 0x01,  // src 10.0.0.1
        0x0a, 0x00, 0x00, 0x02,  // dst 10.0.0.2
        // ICMP echo (8 bytes)
        0x08, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01,
    };
    // Fill checksum
    struct ipv4hdr *ip = (struct ipv4hdr *)pkt;
    ip->check = ip_checksum(pkt, 20);

    ip_verdict_t v = validate_ipv4(pkt, sizeof(pkt));
    printf("Verdict: %d (0=OK)\n", v);

    // Test: martian source
    ip->saddr = htonl(0x7f000001); // 127.0.0.1
    ip->check = 0;
    ip->check = ip_checksum(pkt, 20);
    v = validate_ipv4(pkt, sizeof(pkt));
    printf("Martian verdict: %d (expected %d)\n", v, IP_ERR_MARTIAN_SRC);

    return 0;
}
```

### 3.3 Layer 3 — IPv6 Security Considerations

IPv6 introduces new attack surfaces often overlooked in security reviews:

```
┌──────────────────────────────────────────────────────────────────┐
│ IPv6 Attack Surface                                              │
├──────────────────────┬───────────────────────────────────────────┤
│ NDP (replaces ARP)   │ Neighbor spoofing, RA spoofing,           │
│                      │ SLAAC poisoning, router flooding          │
├──────────────────────┼───────────────────────────────────────────┤
│ Extension headers    │ Header chain DoS, firewall evasion        │
│                      │ (hop-by-hop processed by all nodes)       │
├──────────────────────┼───────────────────────────────────────────┤
│ Multicast            │ MLD flooding, multicast listener spoofing │
├──────────────────────┼───────────────────────────────────────────┤
│ Transition mechs     │ Teredo, ISATAP, 6to4 bypass firewalls     │
├──────────────────────┼───────────────────────────────────────────┤
│ Address privacy      │ EUI-64 leaks hardware MAC → tracking      │
└──────────────────────┴───────────────────────────────────────────┘
```

**Kernel hardening for IPv6:**

```bash
# Disable IPv6 router advertisements acceptance (unless you need SLAAC)
sysctl -w net.ipv6.conf.all.accept_ra=0
sysctl -w net.ipv6.conf.all.accept_redirects=0
sysctl -w net.ipv6.conf.all.forwarding=0  # unless this is a router

# Enable RFC 7217 privacy addresses (opaque IIDs)
sysctl -w net.ipv6.conf.all.use_tempaddr=2
sysctl -w net.ipv6.conf.all.temp_prefered_lft=86400

# Disable transition mechanisms unless needed
# (these can bypass IPv4 firewall rules)
modprobe -r sit        # 6in4
modprobe -r ip6_tunnel
modprobe -r tunnel6

# Verify no Teredo/6to4 relays
ip -6 route | grep -E '2002::|::/96'
```

### 3.4 Layer 4 — TCP Security

TCP's stateful design creates both opportunities (stateful firewalling) and vulnerabilities.

```
TCP State Machine — Security-relevant transitions:
                              
  CLOSED ─SYN─→ SYN_RCVD ─SYN/ACK─→ (server sends SYN/ACK)
                     │                        │
           SYN queue (backlog)         ACK expected
           [SYN flood target]          within timeout
                     │
               ESTABLISHED ←─────────────────┘
                     │
         RST injection ←── attacker can inject RST if
                           sequence number within window
```

**TCP Hardening:**

```bash
# SYN cookies — critical for SYN flood defense
sysctl -w net.ipv4.tcp_syncookies=1

# SYN backlog
sysctl -w net.ipv4.tcp_max_syn_backlog=4096
sysctl -w net.core.somaxconn=4096

# TIME_WAIT recycling (careful: breaks NAT in some cases)
sysctl -w net.ipv4.tcp_tw_reuse=1       # safe: only for outgoing
# net.ipv4.tcp_tw_recycle is REMOVED in kernel >= 4.12 (was dangerous)

# RFC 5961 — blind RST/data injection defense
sysctl -w net.ipv4.tcp_challenge_ack_limit=1000

# Disable TCP timestamps (leaks uptime, aids off-path attacks)
# Trade-off: timestamps improve RTT estimation. Disable on edge only.
sysctl -w net.ipv4.tcp_timestamps=0

# TCP keepalive (detect dead connections)
sysctl -w net.ipv4.tcp_keepalive_time=600
sysctl -w net.ipv4.tcp_keepalive_intvl=60
sysctl -w net.ipv4.tcp_keepalive_probes=9

# Protect against RST floods from off-path attackers
# RFC 5961 challenge ACK
sysctl -w net.ipv4.tcp_challenge_ack_limit=100

# Disable ICMP redirects
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.secure_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
```

**Rust: Minimal TCP SYN cookie implementation (concept)**

```rust
// syn_cookie.rs — SYN cookie generation and validation
// Real kernel implementation: net/ipv4/syncookies.c
// This illustrates the algorithm at the application level.

use std::net::Ipv4Addr;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::time::{SystemTime, UNIX_EPOCH};

type HmacSha256 = Hmac<Sha256>;

/// SYN cookie encodes: MSS index + timestamp in the ISN (Initial Sequence Number)
/// Real kernel uses a 32-bit ISN with:
///   bits 31..24 = count (5-min rolling window, 3 bits used)
///   bits 23..0  = HMAC truncated to 24 bits
///
/// The MSS is encoded in high bits, allowing recovery without state.

const MSS_TABLE: [u16; 4] = [512, 1024, 1460, 9000]; // simplified

#[derive(Debug)]
pub struct SynCookieParams {
    pub src_ip:   Ipv4Addr,
    pub dst_ip:   Ipv4Addr,
    pub src_port: u16,
    pub dst_port: u16,
    pub mss:      u16,
}

fn current_5min_count() -> u32 {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    (secs / 300) as u32 & 0x3  // 2-bit count (rotates every ~20 min)
}

fn mss_to_index(mss: u16) -> u8 {
    MSS_TABLE.iter()
        .enumerate()
        .min_by_key(|(_, &m)| (m as i32 - mss as i32).abs())
        .map(|(i, _)| i as u8)
        .unwrap_or(2)
}

pub fn generate_cookie(params: &SynCookieParams, secret: &[u8; 32]) -> u32 {
    let count = current_5min_count();
    let mss_idx = mss_to_index(params.mss);

    // Compute HMAC over the 5-tuple + count
    let mut mac = HmacSha256::new_from_slice(secret).unwrap();
    mac.update(&params.src_ip.octets());
    mac.update(&params.dst_ip.octets());
    mac.update(&params.src_port.to_be_bytes());
    mac.update(&params.dst_port.to_be_bytes());
    mac.update(&count.to_be_bytes());

    let result = mac.finalize().into_bytes();
    // Take low 24 bits of HMAC
    let hmac24 = u32::from_be_bytes([0, result[0], result[1], result[2]]);

    // Pack: [mss_idx:2][count:2][hmac:24] = 28 bits (leave top 4 for seq)
    (((mss_idx as u32) << 26) | ((count & 0x3) << 24) | hmac24)
}

pub fn validate_cookie(
    cookie: u32,
    params: &SynCookieParams,
    secret: &[u8; 32],
) -> Option<u16> {
    let count_from_cookie = (cookie >> 24) & 0x3;
    let mss_idx = ((cookie >> 26) & 0x3) as usize;
    let current_count = current_5min_count();

    // Allow current and previous window
    if count_from_cookie != (current_count & 0x3)
        && count_from_cookie != ((current_count - 1) & 0x3)
    {
        return None;
    }

    let mut mac = HmacSha256::new_from_slice(secret).unwrap();
    mac.update(&params.src_ip.octets());
    mac.update(&params.dst_ip.octets());
    mac.update(&params.src_port.to_be_bytes());
    mac.update(&params.dst_port.to_be_bytes());
    mac.update(&count_from_cookie.to_be_bytes());

    let result = mac.finalize().into_bytes();
    let expected_hmac24 = u32::from_be_bytes([0, result[0], result[1], result[2]]);

    let cookie_hmac24 = cookie & 0x00FF_FFFF;
    if cookie_hmac24 != expected_hmac24 {
        return None;  // HMAC mismatch — forged or expired cookie
    }

    MSS_TABLE.get(mss_idx).copied()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        let secret = [0x42u8; 32];
        let params = SynCookieParams {
            src_ip:   Ipv4Addr::new(10, 0, 0, 1),
            dst_ip:   Ipv4Addr::new(10, 0, 0, 2),
            src_port: 54321,
            dst_port: 443,
            mss:      1460,
        };
        let cookie = generate_cookie(&params, &secret);
        let mss = validate_cookie(cookie, &params, &secret);
        assert_eq!(mss, Some(1460));
    }

    #[test]
    fn tampered_cookie_rejected() {
        let secret = [0x42u8; 32];
        let params = SynCookieParams {
            src_ip:   Ipv4Addr::new(10,0,0,1),
            dst_ip:   Ipv4Addr::new(10,0,0,2),
            src_port: 12345,
            dst_port: 80,
            mss:      1460,
        };
        let cookie = generate_cookie(&params, &secret);
        let bad = validate_cookie(cookie ^ 0xdead, &params, &secret);
        assert!(bad.is_none());
    }
}
```

### 3.5 Layer 4 — UDP Security

UDP's stateless nature makes it particularly susceptible to amplification attacks.

```
Amplification Attack Vectors (UDP):
─────────────────────────────────────────────────────
Protocol    | Port  | Amplification Factor
────────────┼───────┼────────────────────
DNS         | 53    | up to 50x (ANY query)
NTP         | 123   | up to 4000x (monlist)
SSDP        | 1900  | up to 30x
Memcached   | 11211 | up to 51,000x (!)
CLDAP       | 389   | up to 70x
CharGEN     | 19    | up to 360x
─────────────────────────────────────────────────────

Defense: BCP38 source filtering + rate limiting per source
         + response rate limiting (RRL) on resolvers
         + disable unnecessary UDP services
```

### 3.6 Layer 7 — Application Security (HTTP/2, gRPC, DNS)

```
HTTP/2 Security Considerations:
- HPACK header compression → CRIME-like attacks on shared connections
- Stream multiplexing → RST stream flood (CVE-2023-44487 — "Rapid Reset")
- SETTINGS flood → memory exhaustion
- Header injection via pseudo-headers (:method, :path, :authority)

gRPC specific:
- Protobuf deserialization of untrusted input → type confusion
- Streaming RPCs → goroutine leak if server doesn't bound stream lifetime
- Interceptors as security middleware (enforce authz, rate limit)

DNS Security:
- Cache poisoning (Kaminsky attack) → DNSSEC validation required
- DNS rebinding → Same-Origin Policy bypass → bind to 127.0.0.1
- DNS tunneling for C2 → monitor for high entropy labels, long TTL=0 queries
- NXDOMAIN hijacking by ISPs/resolvers
```

---

## 4. Packet Lifecycle: Kernel to Wire

Understanding the exact journey of a packet is essential for placing security controls correctly.

```
INGRESS PATH (incoming packet):
─────────────────────────────────────────────────────────────────
NIC hardware interrupt / NAPI poll
    │
    ├─→ [XDP_HOOK: XDP_DRIVER or XDP_GENERIC]  ← earliest drop point
    │     XDP_DROP, XDP_PASS, XDP_TX, XDP_REDIRECT
    │
    ├─→ GRO (Generic Receive Offload) — reassemble segments
    │
    ├─→ TC ingress (Traffic Control)  ← eBPF classifiers/actions
    │     cls_bpf, act_bpf — can drop, redirect, modify
    │
    ├─→ netfilter: NF_INET_PRE_ROUTING
    │     iptables PREROUTING chain / nft prerouting
    │     Conntrack: nf_conntrack_in() — classify as NEW/ESTABLISHED/RELATED/INVALID
    │     DNAT: destination rewrite (load balancers, NAT)
    │
    ├─→ Routing decision: ip_rcv_finish() → ip_route_input()
    │     Is packet for local delivery or forwarding?
    │
    ├─→ [If FORWARD]:
    │     NF_INET_FORWARD → iptables FORWARD / nft forward
    │     ip_forward() → TTL check → ip_output()
    │
    └─→ [If LOCAL DELIVERY]:
          NF_INET_LOCAL_IN → iptables INPUT / nft input
          ip_local_deliver_finish()
          Protocol dispatch: tcp_v4_rcv / udp_rcv / icmp_rcv
          Socket lookup → sk_buff delivered to socket receive queue

EGRESS PATH (outgoing packet):
─────────────────────────────────────────────────────────────────
Application: send() / write() syscall
    │
    ├─→ Socket buffer allocation (sk_buff)
    ├─→ Protocol processing: tcp_sendmsg → ip_queue_xmit
    ├─→ Routing: ip_route_output() → RTN_UNICAST/BROADCAST/MULTICAST
    ├─→ NF_INET_LOCAL_OUT → iptables OUTPUT / nft output
    ├─→ SNAT/masquerade rewrite
    ├─→ NF_INET_POST_ROUTING → iptables POSTROUTING
    ├─→ GSO (Generic Segmentation Offload) — segment for wire
    ├─→ TC egress — final eBPF/classifier hook
    ├─→ dev_queue_xmit() → qdisc (traffic shaper/scheduler)
    └─→ driver: ndo_start_xmit() → DMA to NIC ring buffer → wire
```

**Implication:** Security controls at XDP/TC-ingress execute before conntrack and can drop packets with single-digit microsecond latency. netfilter/nftables rules execute after conntrack lookup, giving stateful context. Place rate-limiting/DDoS defenses at XDP; stateful ACL at netfilter.

---

## 5. Netfilter, iptables, nftables

### 5.1 Netfilter Hook Architecture

```c
// Registering a Netfilter hook (kernel module pattern)
// include/linux/netfilter.h

#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/module.h>

static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct tcphdr *tcph;

    if (!skb) return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (!iph) return NF_ACCEPT;

    // Block any packet with IP options (common attack vector)
    if (iph->ihl > 5) {
        pr_warn("Dropping packet with IP options from %pI4\n", &iph->saddr);
        return NF_DROP;
    }

    // Example: block TCP port 23 (telnet) on INPUT
    if (iph->protocol == IPPROTO_TCP) {
        if (!pskb_may_pull(skb, ip_hdrlen(skb) + sizeof(*tcph)))
            return NF_DROP;
        tcph = (struct tcphdr *)((uint8_t *)iph + ip_hdrlen(skb));
        if (ntohs(tcph->dest) == 23)
            return NF_DROP;
    }

    return NF_ACCEPT;
}

static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_LOCAL_IN,   // or PRE_ROUTING, FORWARD, etc.
    .priority = NF_IP_PRI_FIRST,    // run before other hooks
};
```

### 5.2 nftables — Production Ruleset

nftables is the successor to iptables. It offers atomic rule updates, sets (data structures for O(1) lookups), and a clean expression language.

```
# /etc/nftables/main.nft — production server ruleset
# Apply: nft -f /etc/nftables/main.nft

flush ruleset

# ──────────────────────────────────────────
# Tables and chain definitions
# ──────────────────────────────────────────
table inet filter {

    # Dynamic block set — populated by IDS/fail2ban/eBPF
    set blocklist_v4 {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
        size 65536
    }

    set blocklist_v6 {
        type ipv6_addr
        flags dynamic, timeout
        timeout 1h
        size 65536
    }

    # Rate-limit per-source counters
    set syn_ratelimit {
        type ipv4_addr
        flags dynamic, timeout
        timeout 60s
        size 65536
    }

    # Allowed administrative IPs (jumbo set — O(1) lookup via hash)
    set admin_nets {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 }
    }

    chain ingress_raw {
        type filter hook prerouting priority raw; policy accept;

        # Drop invalid conntrack state early (before full processing)
        ct state invalid counter drop

        # Drop fragmented packets to services (reassembly DoS)
        # Exception: allow fragmented ICMP
        ip frag-off & 0x1fff != 0 ip protocol != icmp counter drop
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Loopback — always allow
        iif lo accept

        # Dynamic blocklist check — O(1) hash lookup
        ip saddr @blocklist_v4 counter drop
        ip6 saddr @blocklist_v6 counter drop

        # Established/related — stateful allow
        ct state established,related accept

        # ICMP — rate-limited
        ip protocol icmp limit rate 10/second burst 20 packets accept
        ip protocol icmp drop

        # ICMPv6 — required for IPv6 to function (NDP, etc.)
        ip6 nexthdr icmpv6 icmpv6 type {
            destination-unreachable, packet-too-big,
            time-exceeded, parameter-problem,
            nd-router-advert, nd-neighbor-solicit, nd-neighbor-advert
        } accept
        ip6 nexthdr icmpv6 limit rate 10/second accept

        # SSH — restricted to admin nets + rate limited
        tcp dport 22 ip saddr @admin_nets accept
        tcp dport 22 counter drop

        # Application ports
        tcp dport { 80, 443 } accept
        udp dport 443 accept   # QUIC / HTTP3

        # SYN flood mitigation — rate limit new TCP connections per source
        tcp flags syn tcp dport 443 \
            add @syn_ratelimit { ip saddr timeout 10s limit rate over 20/second } \
            add @blocklist_v4 { ip saddr } \
            drop

        # Log and drop everything else
        limit rate 5/minute log prefix "nft-drop: " flags all counter drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        # Only enable if this machine routes between networks
        # Add explicit rules for allowed forwarding paths
        ct state established,related accept
        ct state invalid drop
    }

    chain output {
        type filter hook output priority filter; policy accept;
        # Egress filtering — prevent exfiltration / C2 beaconing
        oif lo accept
        # Deny outbound to RFC 1918 from DMZ hosts (stop SSRF pivoting)
        # Customize per zone
    }
}

# ──────────────────────────────────────────
# NAT table (if needed)
# ──────────────────────────────────────────
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;
        # DNAT rules here
    }
    chain postrouting {
        type nat hook postrouting priority srcnat;
        # SNAT / masquerade
        # oif eth0 masquerade
    }
}
```

### 5.3 Conntrack — Stateful Tracking Engine

```bash
# View conntrack table
conntrack -L
conntrack -L -p tcp --state ESTABLISHED

# Conntrack performance tuning
sysctl -w net.netfilter.nf_conntrack_max=2000000
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=300
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=60
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close_wait=60

# Conntrack hash table size (set BEFORE loading nf_conntrack module)
# /sys/module/nf_conntrack/parameters/hashsize
echo 262144 > /sys/module/nf_conntrack/parameters/hashsize

# Monitor conntrack overflow (conntrack full = new connections dropped)
watch -n1 'cat /proc/sys/net/netfilter/nf_conntrack_count && \
            cat /proc/sys/net/netfilter/nf_conntrack_max'
```

**Conntrack failure modes:**
- Table exhaustion → all new connections dropped (DDoS vector)
- Helper modules (FTP, SIP) expand attack surface — disable unless needed
- NAT + conntrack interaction: asymmetric routing breaks stateful tracking

---

## 6. eBPF / XDP for Network Security

### 6.1 eBPF Architecture for Network

```
eBPF Network Hook Points:
─────────────────────────────────────────────────────────────────
XDP (eXpress Data Path):
  - BPF_PROG_TYPE_XDP
  - Runs in NIC driver NAPI poll context (before sk_buff allocation)
  - Return: XDP_DROP / XDP_PASS / XDP_TX / XDP_REDIRECT
  - Latency: ~100ns (driver mode) — fastest possible drop
  - Limitation: no sk_buff; limited to packet bytes

TC (Traffic Control):
  - BPF_PROG_TYPE_SCHED_CLS (classifier) / SCHED_ACT (action)
  - Runs on tc ingress/egress qdisc
  - Full sk_buff access — can read/modify headers
  - Can redirect to interfaces, encap/decap (for overlays)

Socket filter:
  - BPF_PROG_TYPE_SOCKET_FILTER — filter per-socket (like BPF in tcpdump)
  - SO_ATTACH_BPF

Socket operations:
  - BPF_PROG_TYPE_SOCK_OPS — intercept TCP events
  - TCP fast-open, RTT measurement, policy per-connection

cgroup-bpf:
  - BPF_PROG_TYPE_CGROUP_SKB — per-cgroup egress/ingress filter
  - Kubernetes: apply network policy at cgroup boundary (Cilium)

kprobe/tracepoint:
  - Monitor kernel functions (kretprobe on tcp_connect, etc.)
  - Observability without modifying kernel
─────────────────────────────────────────────────────────────────
```

### 6.2 XDP DDoS Mitigation — C Implementation

```c
// xdp_ddos.bpf.c — XDP program for SYN flood and IP blocklist enforcement
// Build: clang -O2 -target bpf -c xdp_ddos.bpf.c -o xdp_ddos.bpf.o
// Load:  ip link set dev eth0 xdp obj xdp_ddos.bpf.o sec xdp_ingress

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// ─── Maps ─────────────────────────────────────────────────────────────

// Blocklist: IP → expiry timestamp (nanoseconds)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 1 << 20);  // 1M entries
    __type(key,   __u32);          // IPv4 source address
    __type(value, __u64);          // expiry time (bpf_ktime_get_ns)
} blocklist SEC(".maps");

// Per-source SYN rate counter: IP → [count, window_start_ns]
struct rate_entry {
    __u64 count;
    __u64 window_start;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_PERCPU_HASH);
    __uint(max_entries, 1 << 16);
    __type(key,   __u32);
    __type(value, struct rate_entry);
} syn_rate SEC(".maps");

// Stats counters
struct stats {
    __u64 total;
    __u64 dropped_blocklist;
    __u64 dropped_syn_flood;
    __u64 dropped_invalid;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key,   __u32);
    __type(value, struct stats);
} xdp_stats SEC(".maps");

// ─── Config (written by userspace) ────────────────────────────────────
#define SYN_RATE_LIMIT     100      // max SYN/s per source
#define SYN_WINDOW_NS      1000000000ULL  // 1 second in nanoseconds
#define BLOCK_DURATION_NS  (60ULL * 1000000000ULL)  // 60s block

// ─── Helper: parse Ethernet + IP + TCP headers with bounds checks ──────
static __always_inline int
parse_pkt(struct xdp_md *ctx,
          struct ethhdr **eth_out,
          struct iphdr  **ip_out,
          struct tcphdr **tcp_out)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return -1;

    // Only handle IPv4
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return -2;

    struct iphdr *ip = (struct iphdr *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return -1;
    if (ip->version != 4)
        return -1;

    // IHL bounds check
    __u32 ihl = ip->ihl * 4;
    if (ihl < 20 || (void *)ip + ihl > data_end)
        return -1;

    *eth_out = eth;
    *ip_out  = ip;

    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr *)((void *)ip + ihl);
        if ((void *)(tcp + 1) > data_end)
            return -1;
        *tcp_out = tcp;
    } else {
        *tcp_out = NULL;
    }

    return 0;
}

// ─── Main XDP program ─────────────────────────────────────────────────
SEC("xdp_ingress")
int xdp_ddos_fn(struct xdp_md *ctx)
{
    struct ethhdr *eth;
    struct iphdr  *ip;
    struct tcphdr *tcp;
    __u32 zero = 0;
    struct stats *st;

    st = bpf_map_lookup_elem(&xdp_stats, &zero);
    if (st) __sync_fetch_and_add(&st->total, 1);

    // Parse packet — drop on parse failure
    if (parse_pkt(ctx, &eth, &ip, &tcp) < 0) {
        if (st) __sync_fetch_and_add(&st->dropped_invalid, 1);
        return XDP_DROP;
    }

    __u32 src_ip = ip->saddr;

    // ── Blocklist check (O(1) hash lookup) ───────────────────────────
    __u64 now = bpf_ktime_get_ns();
    __u64 *expiry = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (expiry && *expiry > now) {
        if (st) __sync_fetch_and_add(&st->dropped_blocklist, 1);
        return XDP_DROP;
    }

    // ── TCP SYN flood detection ───────────────────────────────────────
    if (tcp && (tcp->syn && !tcp->ack)) {
        struct rate_entry *re = bpf_map_lookup_elem(&syn_rate, &src_ip);
        if (re) {
            // Within the same 1s window?
            if (now - re->window_start < SYN_WINDOW_NS) {
                re->count++;
                if (re->count > SYN_RATE_LIMIT) {
                    // Add to blocklist
                    __u64 block_until = now + BLOCK_DURATION_NS;
                    bpf_map_update_elem(&blocklist, &src_ip,
                                        &block_until, BPF_ANY);
                    if (st) __sync_fetch_and_add(&st->dropped_syn_flood, 1);
                    return XDP_DROP;
                }
            } else {
                // New window — reset
                re->window_start = now;
                re->count = 1;
            }
        } else {
            // First SYN from this source
            struct rate_entry new_entry = { .count = 1, .window_start = now };
            bpf_map_update_elem(&syn_rate, &src_ip, &new_entry, BPF_ANY);
        }
    }

    return XDP_PASS;
}

// ─── Userspace management example (read stats) ────────────────────────
// $ bpftool map dump name xdp_stats
// $ bpftool map lookup name blocklist key hex <ip-hex>

char _license[] SEC("license") = "GPL";
```

**Load and operate:**

```bash
# Compile
clang -O2 -g -Wall -target bpf -D__TARGET_ARCH_x86 \
    -I/usr/include/bpf \
    -c xdp_ddos.bpf.c -o xdp_ddos.bpf.o

# Load in driver mode (fastest)
ip link set dev eth0 xdp obj xdp_ddos.bpf.o sec xdp_ingress

# Or generic mode (works without driver support, but slower)
ip link set dev eth0 xdpgeneric obj xdp_ddos.bpf.o sec xdp_ingress

# Monitor drop stats
bpftool map dump pinned /sys/fs/bpf/xdp_stats

# Manually block an IP (userspace)
bpftool map update pinned /sys/fs/bpf/blocklist \
    key 0x01 0x02 0x03 0x04 \
    value 0xff 0xff 0xff 0xff 0xff 0xff 0xff 0x7f  # far future

# Remove XDP program
ip link set dev eth0 xdp off

# Performance benchmark
pktgen (kernel) or MoonGen or T-Rex for traffic generation
# Expect 10-25 Mpps on a single core with driver-mode XDP
```

### 6.3 eBPF for Network Observability (Security Monitoring)

```c
// trace_connect.bpf.c — trace all outgoing TCP connections
// Useful for detecting C2 beaconing, lateral movement
#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/socket.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct connect_event {
    __u32 pid;
    __u32 uid;
    __u8  comm[16];
    __u32 daddr;    // destination IPv4
    __u16 dport;    // destination port
    __u64 ts;       // timestamp ns
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} events SEC(".maps");

SEC("kretprobe/tcp_v4_connect")
int BPF_KRETPROBE(trace_tcp_connect, int ret)
{
    if (ret != 0) return 0;  // only successful connects

    struct connect_event e = {};
    e.pid   = bpf_get_current_pid_tgid() >> 32;
    e.uid   = bpf_get_current_uid_gid() & 0xffffffff;
    e.ts    = bpf_ktime_get_ns();
    bpf_get_current_comm(&e.comm, sizeof(e.comm));

    // Note: getting daddr/dport requires reading struct sock
    // (omitted here for brevity — see bcc/libbpf examples)

    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                           &e, sizeof(e));
    return 0;
}

char _license[] SEC("license") = "GPL";
```

---

## 7. Routing Security

### 7.1 BGP Security

BGP is the routing protocol of the Internet — and its security model is fundamentally broken without explicit controls.

```
BGP Attack Taxonomy:
─────────────────────────────────────────────────────────────────
Attack               | Impact                | Defense
─────────────────────┼───────────────────────┼──────────────────
Prefix hijacking     | Traffic interception, | RPKI (ROA/ROV),
                     | blackholing           | IRR filtering
Sub-prefix hijacking | More-specific wins    | RPKI max-length
Route leak           | Traffic attraction    | BGP communities,
                     | without authorization | RPKI, peer filters
AS path manipulation | Bypass path policy    | AS path filtering,
                     | loop creation         | max-as-path length
BGP session attack   | Session reset,        | MD5/TCP-AO auth,
                     | route table wipe      | GTSM (TTL=255)
─────────────────────────────────────────────────────────────────
```

**RPKI (Resource Public Key Infrastructure):**

```bash
# RPKI validation state on Linux with Bird2 or FRR

# FRR BGP configuration for RPKI ROV (Route Origin Validation)
# /etc/frr/bgpd.conf

router bgp 65001
  bgp router-id 10.0.0.1

  # RPKI RTR connection to a local validator (Routinator, OctoRPKI, etc.)
  rpki
    rpki cache 127.0.0.1 3323 preference 1
    exit

  neighbor 192.0.2.1 remote-as 65002
  neighbor 192.0.2.1 password <strong-secret>   # MD5 auth (legacy)
  # Better: use TCP-AO (Authentication Option) if supported

  address-family ipv4 unicast
    neighbor 192.0.2.1 activate

    # Apply RPKI-based route map
    neighbor 192.0.2.1 route-map RPKI_CHECK in

    # Maximum prefix limit — prevent route table overflow
    neighbor 192.0.2.1 maximum-prefix 100000 80  # warn at 80%

    # Prefix list: only accept prefixes you expect (IRR filter)
    neighbor 192.0.2.1 prefix-list PEER_PREFIXES in
  exit-address-family

# Route map: drop INVALID, prefer VALID
route-map RPKI_CHECK permit 10
  match rpki valid
  set local-preference 200

route-map RPKI_CHECK permit 20
  match rpki notfound
  set local-preference 100

route-map RPKI_CHECK deny 30
  match rpki invalid
  # Drop RPKI-invalid routes — they are hijacked or misconfigured

# GTSM — Generalized TTL Security Mechanism (RFC 5082)
# Requires BGP peer to set TTL=255; routers decrement; expect >= 254
neighbor 192.0.2.1 ttl-security hops 1
```

```bash
# Run Routinator (RPKI validator) locally
docker run -d --name routinator \
    -p 3323:3323 -p 8323:8323 \
    nlnetlabs/routinator \
    routinator server --rtr 0.0.0.0:3323 --http 0.0.0.0:8323

# Check validation status
curl http://localhost:8323/api/v1/validity/AS65001/203.0.113.0/24

# Verify RPKI state in FRR
vtysh -c "show bgp ipv4 rpki validation"
vtysh -c "show rpki prefix-table"
```

### 7.2 OSPF / IS-IS Security

Interior routing protocols (IGP) are critical — a compromised IGP session can redirect all internal traffic.

```
# OSPF authentication — always enable in production
# MD5 is deprecated; use SHA-512 cryptographic authentication (RFC 7166)

# Cisco IOS / FRR style:
interface eth0
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 <secret>
  # Better: use key-chain with SHA-256
  ip ospf authentication key-chain OSPF_KEYS

key chain OSPF_KEYS
  key 1
    key-string <strong-secret>
    cryptographic-algorithm hmac-sha-256
    send-lifetime 00:00:00 Jan 1 2024 infinite
    accept-lifetime 00:00:00 Jan 1 2024 infinite

# FRR ospfd.conf
router ospf
  ospf router-id 10.0.0.1
  area 0.0.0.0 authentication message-digest

interface eth0
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 "strongpassword"
  # Passive on interfaces with no OSPF neighbors (prevents rogue adjacency)
  ip ospf passive  # on stub interfaces
```

### 7.3 uRPF — Unicast Reverse Path Forwarding

uRPF enforces source address validity — the primary BCP38 mechanism.

```bash
# Enable strict uRPF on ingress interfaces (FRR / Linux)
# Strict mode: source IP must be reachable via the same interface it arrived on
# Loose mode: source IP must exist in routing table (any interface)

# Linux iproute2:
# Strict mode via rp_filter
sysctl -w net.ipv4.conf.eth0.rp_filter=1      # strict
sysctl -w net.ipv4.conf.all.rp_filter=1
# Loose mode
sysctl -w net.ipv4.conf.eth0.rp_filter=2

# Verify
sysctl net.ipv4.conf.eth0.rp_filter

# On a router, strict uRPF may break asymmetric routing
# Use loose mode on transit links, strict on edge (customer-facing) interfaces

# FRR / Quagga: uRPF configured per interface in kernel via sysctl
# Bird2: route check in import filter
protocol static {
    route 0.0.0.0/0 blackhole;  # default for loose uRPF
    # Check source in route table via filter
}
```

---

## 8. Switching Security (L2)

### 8.1 VLAN Security

```
802.1Q VLAN Security Controls:
─────────────────────────────────────────────────────────────────
Threat                  | Control
────────────────────────┼────────────────────────────────────────
VLAN hopping            | Disable DTP (auto-trunk negotiation),
(double-tagging)        | set native VLAN to unused VLAN,
                        | always use tagged trunk links
MAC flooding            | Port security: max-mac-addresses 1-5,
(CAM table exhaustion)  | 802.1X authentication per port
Rogue DHCP server       | DHCP snooping: trusted/untrusted ports,
                        | rate-limit DHCP on untrusted
ARP poisoning           | Dynamic ARP Inspection (DAI):
                        | validate ARP against DHCP snooping DB
STP manipulation        | BPDU Guard: disable port if BPDU rcvd
(root bridge attack)    | Root Guard: prevent superior BPDUs
                        | PortFast: access ports skip STP states
─────────────────────────────────────────────────────────────────
```

```bash
# Linux bridge security configuration
# Applicable to hypervisors, container hosts, bare-metal switches

# Enable ebtables (L2 netfilter) on Linux bridge
# Prevent ARP spoofing on a bridge
ebtables -t filter -A FORWARD --protocol ARP \
    --arp-ip-src ! 10.0.1.0/24 \
    --in-interface veth+ -j DROP

# VLAN filtering on Linux bridge
ip link add name br0 type bridge
ip link set br0 type bridge vlan_filtering 1

# Assign VLANs to bridge ports
bridge vlan add vid 100 dev eth0 pvid untagged    # access port
bridge vlan add vid 100 dev eth1 pvid untagged
bridge vlan add vid 100 vid 200 dev eth2           # trunk port (tagged)

# Block inter-VLAN traffic at the bridge (requires vlan_filtering)
bridge vlan show
bridge fdb show

# MACsec — Layer 2 encryption (IEEE 802.1AE)
# Provides per-frame authentication and encryption between switches
ip link add link eth0 macsec0 type macsec cipher gcm-aes-128 encrypt on
ip macsec add macsec0 tx sa 0 pn 1 on key 01 <hex-key>
ip macsec add macsec0 rx port 1 address <peer-mac>
ip macsec add macsec0 rx port 1 address <peer-mac> sa 0 pn 1 on key 01 <hex-key>
ip link set macsec0 up

# Verify MACsec
ip macsec show
```

### 8.2 DHCP Snooping Equivalent on Linux (with nftables)

```
# DHCP snooping: only allow DHCP responses from trusted servers
# Implemented via nftables on a Linux bridge host

table bridge filter {

    # Trusted DHCP server IPs (configure per environment)
    set trusted_dhcp_servers {
        type ipv4_addr
        elements = { 10.0.0.1, 10.0.0.2 }
    }

    chain forward {
        type filter hook forward priority filter; policy accept;

        # Block DHCP OFFER/ACK from untrusted sources
        # DHCP server → client: UDP src=67, dst=68
        udp sport 67 udp dport 68 \
            ip saddr != @trusted_dhcp_servers \
            counter drop

        # Rate-limit DHCP requests from any single MAC
        # (prevents DHCP starvation attacks)
        udp sport 68 udp dport 67 \
            ether saddr limit rate over 5/second \
            counter drop
    }
}
```

---

## 9. TLS/mTLS and PKI

### 9.1 TLS 1.3 — Security Properties

```
TLS 1.3 Handshake (RFC 8446):
─────────────────────────────────────────────────────────────────
Client                              Server
  │                                    │
  ├──── ClientHello ──────────────────→│
  │     (supported_versions=TLS1.3,    │
  │      key_share=X25519,             │
  │      signature_algos,              │
  │      PSK if resuming)              │
  │                                    │
  │←─── ServerHello ──────────────────┤
  │     (chosen cipher, key_share)     │
  │←─── {EncryptedExtensions} ────────┤
  │←─── {CertificateRequest} ─────────┤  (mTLS: server requests client cert)
  │←─── {Certificate} ────────────────┤
  │←─── {CertificateVerify} ──────────┤
  │←─── {Finished} ───────────────────┤
  │                                    │
  ├──── {Certificate} ────────────────→│  (mTLS: client cert)
  ├──── {CertificateVerify} ──────────→│
  ├──── {Finished} ───────────────────→│
  │                                    │
  ├════ [Application Data] ═══════════→│  (encrypted, authenticated)
  │←═══ [Application Data] ═══════════┤

Key properties:
- Forward Secrecy: ephemeral ECDHE key exchange (X25519 preferred)
- 1-RTT for new sessions, 0-RTT for resumption (careful: replay risk)
- AEAD only: AES-256-GCM, ChaCha20-Poly1305
- No RSA key exchange, no static DH, no CBC, no RC4, no MD5/SHA-1
─────────────────────────────────────────────────────────────────
```

**Rust: TLS 1.3 client with certificate pinning**

```rust
// tls_client.rs — mTLS client with cert pinning using rustls
// Cargo.toml:
//   rustls = "0.23"
//   rustls-pemfile = "2"
//   tokio = { version = "1", features = ["full"] }
//   tokio-rustls = "0.26"
//   webpki-roots = "0.26"

use std::fs::File;
use std::io::BufReader;
use std::sync::Arc;
use rustls::{ClientConfig, RootCertStore, Certificate, PrivateKey};
use rustls::client::ServerCertVerifier;
use rustls::client::ServerCertVerified;
use tokio_rustls::TlsConnector;
use tokio::net::TcpStream;

/// Certificate pinning verifier — accepts only a specific leaf cert
struct PinnedCertVerifier {
    /// SHA-256 digest of the expected DER-encoded leaf certificate
    expected_spki_hash: [u8; 32],
}

impl ServerCertVerifier for PinnedCertVerifier {
    fn verify_server_cert(
        &self,
        end_entity: &Certificate,
        _intermediates: &[Certificate],
        _server_name: &rustls::ServerName,
        _scts: &mut dyn Iterator<Item = &[u8]>,
        _ocsp_response: &[u8],
        _now: std::time::SystemTime,
    ) -> Result<ServerCertVerified, rustls::Error> {
        // Hash the SubjectPublicKeyInfo from the DER cert
        // (Real implementation: parse ASN.1 to extract SPKI)
        let hash = sha256_of_spki(&end_entity.0)?;

        if hash != self.expected_spki_hash {
            return Err(rustls::Error::General(
                "Certificate pin mismatch".into()
            ));
        }

        Ok(ServerCertVerified::assertion())
    }
}

fn sha256_of_spki(cert_der: &[u8]) -> Result<[u8; 32], rustls::Error> {
    // In production: parse X.509 DER, extract SPKI field, SHA-256 it
    // Using x509-parser crate or ring::digest
    use ring::digest;
    // Simplified: hash the whole cert (use SPKI extraction in prod)
    let hash = digest::digest(&digest::SHA256, cert_der);
    let mut out = [0u8; 32];
    out.copy_from_slice(hash.as_ref());
    Ok(out)
}

async fn connect_mtls(
    host: &str,
    port: u16,
    client_cert_path: &str,
    client_key_path:  &str,
    pinned_spki_hash: [u8; 32],
) -> anyhow::Result<tokio_rustls::client::TlsStream<TcpStream>> {

    // Load client certificate and private key (mTLS)
    let cert_file = File::open(client_cert_path)?;
    let mut cert_reader = BufReader::new(cert_file);
    let client_certs: Vec<Certificate> =
        rustls_pemfile::certs(&mut cert_reader)?
            .into_iter().map(Certificate).collect();

    let key_file = File::open(client_key_path)?;
    let mut key_reader = BufReader::new(key_file);
    let client_key = rustls_pemfile::pkcs8_private_keys(&mut key_reader)?
        .into_iter().next()
        .map(PrivateKey)
        .ok_or_else(|| anyhow::anyhow!("no private key found"))?;

    // Build TLS config with cert pinning
    let config = ClientConfig::builder()
        .with_safe_defaults()
        .with_custom_certificate_verifier(Arc::new(PinnedCertVerifier {
            expected_spki_hash: pinned_spki_hash,
        }))
        .with_client_auth_cert(client_certs, client_key)?;

    let connector = TlsConnector::from(Arc::new(config));
    let tcp = TcpStream::connect((host, port)).await?;
    let domain = rustls::ServerName::try_from(host)?;
    let tls = connector.connect(domain, tcp).await?;

    Ok(tls)
}
```

### 9.2 PKI Architecture for Production

```
Production PKI Hierarchy:
─────────────────────────────────────────────────────────────────
Root CA (offline, air-gapped, HSM-backed)
    │  Validity: 20 years
    │  Key: RSA 4096 or P-384 ECDSA
    │  Stored: HSM + 3 encrypted USB + locked safe
    │
    ├── Intermediate CA — Infrastructure (online, HSM)
    │       Validity: 5 years
    │       Signs: service mesh certs, k8s API server
    │       CRL/OCSP: published every 24h
    │
    ├── Intermediate CA — mTLS Services (online)
    │       Validity: 5 years
    │       Signs: short-lived service identity certs (24h or less)
    │       Automation: SPIFFE/SPIRE, cert-manager, Vault PKI
    │
    └── Intermediate CA — Code Signing (HSM)
            Validity: 3 years
            Signs: container images, binaries, configs
            Integration: Cosign/Sigstore, Notary
─────────────────────────────────────────────────────────────────
```

```bash
# Generate Root CA with HSM (SoftHSM for dev, real HSM for prod)
# Using cfssl (Cloud Foundry SSL) — production-grade PKI tooling

# Root CA config
cat > root-ca-csr.json << 'EOF'
{
  "CN": "My Org Root CA",
  "key": { "algo": "ecdsa", "size": 384 },
  "ca": { "expiry": "175200h" },
  "names": [{"O": "My Org", "C": "US"}]
}
EOF

cfssl gencert -initca root-ca-csr.json | cfssljson -bare root-ca

# Intermediate CA
cat > intermediate-ca-csr.json << 'EOF'
{
  "CN": "Infrastructure Intermediate CA",
  "key": { "algo": "ecdsa", "size": 256 },
  "ca": { "expiry": "43800h" },
  "names": [{"O": "My Org", "C": "US"}]
}
EOF

cfssl gencert \
    -ca root-ca.pem -ca-key root-ca-key.pem \
    -config ca-config.json -profile intermediate \
    intermediate-ca-csr.json | cfssljson -bare intermediate-ca

# Issue a short-lived service cert (24h — typical for mTLS service mesh)
cat > service-csr.json << 'EOF'
{
  "CN": "payment-service.prod.svc.cluster.local",
  "key": { "algo": "ecdsa", "size": 256 },
  "names": [{"O": "My Org"}],
  "hosts": [
    "payment-service",
    "payment-service.prod",
    "payment-service.prod.svc.cluster.local",
    "spiffe://prod.cluster.local/ns/prod/sa/payment-service"
  ]
}
EOF

cfssl gencert \
    -ca intermediate-ca.pem -ca-key intermediate-ca-key.pem \
    -config ca-config.json -profile server \
    service-csr.json | cfssljson -bare payment-service

# Verify cert chain
openssl verify -CAfile root-ca.pem -untrusted intermediate-ca.pem payment-service.pem
openssl x509 -in payment-service.pem -noout -text | grep -A5 "Subject Alternative Name"
```

### 9.3 TLS Configuration Hardening

```bash
# Nginx — production TLS hardening
# Test at: https://www.ssllabs.com/ssltest/

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/ssl/certs/example.pem;
    ssl_certificate_key /etc/ssl/private/example-key.pem;

    # TLS 1.3 only (drop 1.2 if clients support it)
    ssl_protocols TLSv1.3;
    # If you must support 1.2:
    # ssl_protocols TLSv1.2 TLSv1.3;
    # ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    # ssl_prefer_server_ciphers on;

    # OCSP stapling — reduces handshake latency + privacy
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/chain.pem;

    # HSTS — force HTTPS for 1 year, include subdomains
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Disable session tickets (breaks forward secrecy if ticket key compromised)
    ssl_session_tickets off;

    # Session cache (if enabling tickets, rotate key every few hours)
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # HPKP is deprecated — use Certificate Transparency instead
    # Ensure CT log submission (Let's Encrypt does this automatically)
}
```

---

## 10. Network Segmentation: VLANs, VXLANs, Geneve

### 10.1 Overlay Network Architecture

```
Physical Underlay vs. Virtual Overlay:
─────────────────────────────────────────────────────────────────
Overlay (tenant/workload traffic):
  VM1 (10.0.1.1) ←→ VXLAN/Geneve tunnel ←→ VM2 (10.0.2.1)
        │                                          │
        │ encapsulated in UDP                      │
        │                                          │
Underlay (physical switching/routing):
  Server1 (192.168.1.1) ←→ ToR Switch ←→ Server2 (192.168.1.2)
                                 ↕
                           Spine Switches
                                 ↕
                         Core / WAN Routers

VXLAN Frame structure:
[Outer Ethernet][Outer IP][Outer UDP(dport=4789)][VXLAN Header][Inner Ethernet Frame]

VXLAN Header (8 bytes):
  ├── Flags (8 bits): I flag = 1 (VNI valid)
  ├── Reserved (24 bits)
  ├── VNI (24 bits): Virtual Network Identifier (16M segments)
  └── Reserved (8 bits)

Geneve (RFC 8926) — more extensible than VXLAN:
[Outer Ethernet][Outer IP][Outer UDP(dport=6081)][Geneve Header][Inner Frame]
  Geneve supports TLV metadata options — used by OVN/OVS for policy metadata
─────────────────────────────────────────────────────────────────
```

**VXLAN Security Considerations:**

```bash
# VXLAN has NO built-in security — it's a tunneling protocol only
# Security must be added via:
# 1. IPsec encryption of the UDP tunnel (underlay IPsec)
# 2. WireGuard for underlay encryption
# 3. MACsec on the physical links
# 4. Proper network segmentation preventing cross-VNI traffic

# Create VXLAN tunnel (basic — no encryption!)
ip link add vxlan100 type vxlan \
    id 100 \
    dstport 4789 \
    local 192.168.1.1 \
    remote 192.168.1.2 \
    dev eth0

ip addr add 10.0.1.1/24 dev vxlan100
ip link set vxlan100 up

# Secure VXLAN with WireGuard underlay:
# 1. Establish WireGuard tunnel between hosts (wg0)
# 2. Run VXLAN traffic over WireGuard interface
ip link add vxlan100 type vxlan \
    id 100 \
    dstport 4789 \
    local 172.16.0.1 \   # WireGuard IP
    remote 172.16.0.2 \
    dev wg0              # WireGuard interface

# Secure VXLAN with IPsec (strongSwan/Libreswan)
# See Section 17 — Cryptographic Primitives
```

### 10.2 WireGuard — Modern Encrypted Overlay

WireGuard is the preferred secure tunnel for overlay networks in modern systems.

```bash
# WireGuard setup — minimal, secure configuration
# Server: 192.168.1.1, WG address: 10.100.0.1/24

# Generate keys
wg genkey | tee server-private.key | wg pubkey > server-public.key
wg genkey | tee client-private.key | wg pubkey > client-public.key

# Server config: /etc/wireguard/wg0.conf
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.100.0.1/24
ListenPort = 51820
PrivateKey = $(cat server-private.key)

# PostUp/Down: extend nftables firewall to WireGuard
PostUp   = nft add rule inet filter forward iif wg0 oif eth0 accept
PostDown = nft delete rule inet filter forward iif wg0 oif eth0 handle <handle>

[Peer]
PublicKey = $(cat client-public.key)
AllowedIPs = 10.100.0.2/32   # restrict: this peer can only use this IP
# PresharedKey = <psk>        # optional: adds PQ-resistance (symmetric key)
EOF

chmod 600 /etc/wireguard/wg0.conf
wg-quick up wg0

# Client config: /etc/wireguard/wg0.conf
cat > /etc/wireguard/wg0-client.conf << EOF
[Interface]
Address = 10.100.0.2/24
PrivateKey = $(cat client-private.key)
DNS = 10.100.0.1   # use server's DNS (prevents DNS leaks)

[Peer]
PublicKey = $(cat server-public.key)
Endpoint = <server-public-ip>:51820
AllowedIPs = 10.100.0.0/24   # only route overlay traffic through WG
PersistentKeepalive = 25      # keep NAT hole open
EOF

# Verify
wg show
```

---

## 11. Firewalls — Architecture and Implementation

### 11.1 Stateful vs. Stateless Firewall

```
Stateless Firewall:
  - Evaluates each packet independently
  - No memory of connections
  - Fast: O(n) rule lookup (or O(1) with hash/bitmap)
  - Limitation: cannot distinguish established traffic from new attacks
  - Use: edge ACLs, rate limiting, blocklists
  - Implementation: iptables with -m conntrack NOT used, simple rules
  - XDP for >10Mpps packet filtering

Stateful Firewall:
  - Tracks connection state (NEW/ESTABLISHED/RELATED/INVALID)
  - Allows return traffic automatically for established sessions
  - Handles FTP/SIP/H.323 ALG (Application Layer Gateway)
  - Cost: memory for conntrack table, CPU for state lookup
  - Implementation: nftables with ct state, Linux conntrack
  - Linux conntrack throughput: ~3-5 Mpps per core (varies)

Next-Generation Firewall (NGFW):
  - L7 application identification (DPI)
  - User identity awareness (integration with AD/LDAP)
  - SSL/TLS inspection (decrypt + inspect + re-encrypt)
  - Threat intelligence feeds
  - Implementation: Suricata (IDS/IPS + DPI), commercial NGFWs
```

### 11.2 Zone-Based Firewall Design

```
Production Zone Architecture:
─────────────────────────────────────────────────────────────────
[Internet] → [DMZ] → [Application Zone] → [Data Zone]
                ↑              ↑                 ↑
             WAF/LB       App Firewall       DB Firewall
           (L7 filter)  (L4 stateful)       (L4 strict)

Traffic policy matrix:
─────────────────┬──────────┬──────────┬──────────┬──────────
Zone             │ Internet │   DMZ    │  AppZone │ DataZone
─────────────────┼──────────┼──────────┼──────────┼──────────
Internet         │    -     │ 80,443   │  DENY    │  DENY
DMZ              │ estab.   │    -     │ 8080     │  DENY
AppZone          │  DENY    │ estab.   │    -     │ 5432,3306
DataZone         │  DENY    │  DENY    │ estab.   │    -
Admin (VPN only) │ 51820/udp│ 22       │ 22       │ 22
─────────────────┴──────────┴──────────┴──────────┴──────────
```

### 11.3 C: Minimal Packet Filter (BPF Socket Filter)

```c
/* socket_filter.c — attach a BPF filter to a raw socket
 * Blocks all traffic except TCP port 443 from 10.0.0.0/8
 * Compile: gcc -O2 -Wall -o socket_filter socket_filter.c
 */
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/filter.h>
#include <linux/if_ether.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

/*
 * BPF filter in classic BPF (cBPF) notation.
 * Equivalent to: tcpdump "tcp dst port 443 and src net 10.0.0.0/8"
 *
 * Generated with:
 *   tcpdump -dd "tcp dst port 443 and src net 10.0.0.0/8"
 *
 * In production: use libpcap or seccomp-tools to generate, don't hand-write.
 */
static struct sock_filter filter_code[] = {
    /* Load EtherType */
    { BPF_LD  | BPF_H   | BPF_ABS, 0, 0, 12 },
    /* Jump if not IPv4 (0x0800) */
    { BPF_JMP | BPF_JEQ | BPF_K,   0, 8, 0x0800 },
    /* Load IP protocol */
    { BPF_LD  | BPF_B   | BPF_ABS, 0, 0, 23 },
    /* Jump if not TCP (6) */
    { BPF_JMP | BPF_JEQ | BPF_K,   0, 6, 6 },
    /* Check no IP fragments */
    { BPF_LD  | BPF_H   | BPF_ABS, 0, 0, 20 },
    { BPF_JMP | BPF_JSET | BPF_K,  4, 0, 0x1fff },
    /* Load TCP destination port */
    { BPF_LDX | BPF_B   | BPF_MSH, 0, 0, 14 },
    { BPF_LD  | BPF_H   | BPF_IND, 0, 0, 16 },
    /* Jump if not port 443 */
    { BPF_JMP | BPF_JEQ | BPF_K,   0, 2, 443 },
    /* Check source IP is in 10.0.0.0/8 */
    { BPF_LD  | BPF_W   | BPF_ABS, 0, 0, 26 },
    { BPF_JMP | BPF_JEQ | BPF_K,   1, 0, 0x0a000000 }, // masked check
    /* Return 0 (drop) */
    { BPF_RET | BPF_K,              0, 0, 0 },
    /* Return 65535 (pass all bytes) */
    { BPF_RET | BPF_K,              0, 0, 65535 },
};

int main(void)
{
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sock < 0) { perror("socket"); return 1; }

    struct sock_fprog prog = {
        .len    = sizeof(filter_code) / sizeof(struct sock_filter),
        .filter = filter_code,
    };

    if (setsockopt(sock, SOL_SOCKET, SO_ATTACH_FILTER,
                   &prog, sizeof(prog)) < 0) {
        perror("SO_ATTACH_FILTER");
        close(sock);
        return 1;
    }

    printf("Filter attached. Receiving filtered packets...\n");

    uint8_t buf[65536];
    ssize_t n;
    while ((n = recv(sock, buf, sizeof(buf), 0)) > 0) {
        printf("Received %zd bytes (matched filter)\n", n);
    }

    close(sock);
    return 0;
}
```

---

## 12. Intrusion Detection and Prevention (IDS/IPS)

### 12.1 Detection Approaches

```
Detection Strategy Matrix:
─────────────────────────────────────────────────────────────────
Approach            | How               | Strengths/Weaknesses
────────────────────┼───────────────────┼──────────────────────
Signature-based     | Match known       | Low FP on known threats;
                    | byte patterns,    | blind to 0-day;
                    | regexes           | fast with PCRE/Hyperscan
────────────────────┼───────────────────┼──────────────────────
Anomaly-based       | Statistical       | Detects novel attacks;
                    | deviation from    | high FP rate;
                    | baseline          | needs training period
────────────────────┼───────────────────┼──────────────────────
Protocol analysis   | State-machine     | Detects malformed PDUs,
                    | validation of     | evasion via malformed pkts;
                    | protocol fields   | high coverage, lower FP
────────────────────┼───────────────────┼──────────────────────
Behavioral          | ML on netflow,    | Lateral movement, exfil;
                    | DNS, TLS metadata | No decrypt needed;
                    | (without decrypt) | Model accuracy depends on data
─────────────────────────────────────────────────────────────────
```

### 12.2 Suricata — Production IDS/IPS Configuration

```yaml
# /etc/suricata/suricata.yaml — key security settings

vars:
  address-groups:
    HOME_NET: "[10.0.0.0/8,172.16.0.0/12,192.168.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    DNS_SERVERS: "[10.0.0.53,10.0.0.54]"

# Run as IPS (inline) using NFQueue or AF_PACKET
af-packet:
  - interface: eth0
    threads: auto
    cluster-type: cluster_flow       # per-flow load balancing (maintains state)
    cluster-id: 99
    copy-mode: ips                   # IPS mode: forward or drop
    copy-iface: eth1                 # forward to this interface
    buffer-size: 128000
    use-mmap: yes
    tpacket-v3: yes
    ring-size: 200000                # packet ring buffer size
    block-size: 32768

# Threading
threading:
  set-cpu-affinity: yes
  cpu-affinity:
    - management-cpu-set:
        cpu: [ 0 ]
    - worker-cpu-set:
        cpu: [ 1, 2, 3, 4 ]

# Detection engine tuning
detect:
  profile: high                      # high: more rules, more CPU
  sgh-mpm-context: auto
  inspection-recursion-limit: 3000

# Output
outputs:
  - eve-log:
      enabled: yes
      filetype: unix_stream           # stream to logstash/vector
      filename: /var/run/suricata/suricata.socket
      types:
        - alert:
            payload: yes              # include packet payload (careful: PII)
            http-body: yes
            metadata: yes
        - flow
        - tls:
            extended: yes            # JA3/JA3S fingerprints
        - dns
        - http
        - files:
            force-magic: yes

# Threat feeds and rules
rule-files:
  - /var/lib/suricata/rules/suricata.rules  # ET Open or ET Pro
  - /etc/suricata/rules/local.rules          # custom org rules

# IPS action policy
action-order:
  - pass
  - drop
  - reject
  - alert
```

```bash
# Custom Suricata rule: detect DNS tunneling (high entropy, long labels)
# /etc/suricata/rules/local.rules

alert dns any any -> any 53 ( \
    msg:"DNS Tunneling - Excessive label length"; \
    dns.query; \
    content:"."; \
    byte_test:1,>,50,0,string,dec;  \  # label longer than 50 chars
    threshold: type limit, track by_src, count 5, seconds 60; \
    classtype:policy-violation; \
    sid:9000001; rev:1; \
)

alert tls any any -> any any ( \
    msg:"TLS - Suspicious JA3 fingerprint (Cobalt Strike default)"; \
    ja3.hash; \
    content:"72a589da586844d7f0818ce684948eea"; \   # CS default JA3
    classtype:trojan-activity; \
    sid:9000002; rev:1; \
)

alert http $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"Outbound HTTP to non-standard port - potential C2"; \
    flow:established,to_server; \
    http.method; content:"POST"; \
    not (content:":80|:8080|:8443|:443" within 50); \
    detection_filter:track by_src, count 5, seconds 300; \
    classtype:trojan-activity; \
    sid:9000003; rev:1; \
)
```

### 12.3 Network Detection with eBPF (without packet copies)

```c
// dns_monitor.bpf.c — monitor DNS queries via socket filter eBPF
// Attach to UDP port 53 without copying packets to userspace
// Returns: DNS query name and type for threat detection

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define DNS_HDR_SIZE 12  // fixed DNS header

struct dns_event {
    __u32 src_ip;
    __u8  qname[128];    // query name (label-encoded)
    __u16 qtype;
    __u32 pid;
    __u64 timestamp;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size,   sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} dns_events SEC(".maps");

SEC("socket_filter")
int monitor_dns(struct __sk_buff *skb)
{
    // Offset calculation: Eth(14) + IP(20) + UDP(8) + DNS_HDR(12) = 54
    __u32 dns_payload_offset = 14 + 20 + 8 + DNS_HDR_SIZE;

    struct dns_event ev = {};
    ev.timestamp = bpf_ktime_get_ns();
    ev.pid       = bpf_get_current_pid_tgid() >> 32;

    // Source IP
    if (bpf_skb_load_bytes(skb, 26, &ev.src_ip, 4) < 0)
        return 0;

    // DNS QNAME (label-encoded, up to 128 bytes)
    if (bpf_skb_load_bytes(skb, dns_payload_offset,
                            ev.qname, sizeof(ev.qname)) < 0)
        return 0;

    // QTYPE (immediately after QNAME — requires name length calculation)
    // Simplified: send raw qname to userspace for parsing

    bpf_perf_event_output(skb, &dns_events,
                           BPF_F_CURRENT_CPU, &ev, sizeof(ev));
    return 0;  // 0 = pass; -1 = drop
}

char _license[] SEC("license") = "GPL";
```

---

## 13. DDoS — Taxonomy, Defense, Implementation

### 13.1 DDoS Attack Taxonomy

```
DDoS Attack Tree:
─────────────────────────────────────────────────────────────────
Volume-based:
  ├── UDP flood (random dest ports)
  ├── ICMP flood (Smurf, ping flood)
  ├── Amplification: DNS/NTP/Memcached/CLDAP
  │   Source IP spoofed → victim receives amplified response
  └── BitTorrent reflection

Protocol-based (exhaust state machines):
  ├── SYN flood (half-open connections)
  ├── ACK flood (challenge state machines)
  ├── RST flood
  ├── Fragmented packet flood
  └── SSL exhaustion (handshake CPU cost)

Application-layer (L7):
  ├── HTTP GET flood (low-and-slow)
  ├── HTTP POST flood
  ├── Slowloris (keep connections open with slow headers)
  ├── RUDY (slow POST body)
  ├── HTTP/2 Rapid Reset (CVE-2023-44487)
  └── DNS NXDOMAIN flood
─────────────────────────────────────────────────────────────────

Defense Layers:
1. Upstream scrubbing (BGP blackhole, CDN, Cloudflare Magic Transit)
2. Anycast for traffic distribution
3. XDP/eBPF packet drop at line rate
4. nftables rate limiting
5. SYN cookies
6. Application-layer rate limiting (nginx limit_req, envoy)
7. Challenge-response (CAPTCHAs, JS challenges)
```

### 13.2 BGP Blackhole (RTBH) for DDoS Mitigation

```bash
# Remote Triggered Black Hole (RTBH) routing
# When under attack, announce victim IP with community 666 to upstream
# Upstream drops all traffic to that IP at their edge → scrubs DDoS

# FRR BGP config:
router bgp 65001
  # Blackhole community action
  address-family ipv4 unicast
    neighbor <upstream-peer> route-map BLACKHOLE out

route-map BLACKHOLE permit 10
  match ip address prefix-list BLACKHOLE_PREFIXES
  set community 65000:666 additive      # RFC 7999 community
  set ip next-hop 192.0.2.1            # blackhole next-hop

# Trigger blackhole for specific attacked IP
ip route 203.0.113.42/32 blackhole     # static blackhole route
# Redistribute into BGP
redistribute static

# For source-based RTBH (uRPF-based): blackhole source IPs, not destinations
# More complex — requires uRPF enforcement on upstream
```

### 13.3 Rust: Token Bucket Rate Limiter

```rust
// rate_limiter.rs — thread-safe token bucket per IP address
// Used in application-layer DDoS defense

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::net::IpAddr;
use std::time::{Instant, Duration};

#[derive(Debug)]
struct TokenBucket {
    tokens:          f64,
    capacity:        f64,       // max burst
    refill_rate:     f64,       // tokens per second
    last_refill:     Instant,
}

impl TokenBucket {
    fn new(capacity: f64, rate_per_sec: f64) -> Self {
        TokenBucket {
            tokens:      capacity,
            capacity,
            refill_rate: rate_per_sec,
            last_refill: Instant::now(),
        }
    }

    /// Try to consume `n` tokens. Returns true if allowed.
    fn try_consume(&mut self, n: f64) -> bool {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();

        // Refill tokens based on elapsed time
        self.tokens = (self.tokens + elapsed * self.refill_rate)
            .min(self.capacity);
        self.last_refill = now;

        if self.tokens >= n {
            self.tokens -= n;
            true
        } else {
            false
        }
    }
}

pub struct IpRateLimiter {
    buckets:      Mutex<HashMap<IpAddr, TokenBucket>>,
    capacity:     f64,
    rate_per_sec: f64,
    cleanup_interval: Duration,
    last_cleanup: Mutex<Instant>,
}

impl IpRateLimiter {
    pub fn new(capacity: f64, rate_per_sec: f64) -> Arc<Self> {
        Arc::new(IpRateLimiter {
            buckets: Mutex::new(HashMap::new()),
            capacity,
            rate_per_sec,
            cleanup_interval: Duration::from_secs(60),
            last_cleanup: Mutex::new(Instant::now()),
        })
    }

    pub fn is_allowed(&self, ip: IpAddr) -> bool {
        let mut buckets = self.buckets.lock().unwrap();

        // Periodic cleanup of idle buckets (prevent memory leak)
        {
            let mut lc = self.last_cleanup.lock().unwrap();
            if lc.elapsed() > self.cleanup_interval {
                let cap = self.capacity;
                buckets.retain(|_, b| b.tokens < cap); // remove full buckets
                *lc = Instant::now();
            }
        }

        let bucket = buckets.entry(ip).or_insert_with(|| {
            TokenBucket::new(self.capacity, self.rate_per_sec)
        });

        bucket.try_consume(1.0)
    }

    pub fn current_tokens(&self, ip: &IpAddr) -> Option<f64> {
        let buckets = self.buckets.lock().unwrap();
        buckets.get(ip).map(|b| b.tokens)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Ipv4Addr;

    #[test]
    fn allows_within_rate() {
        let rl = IpRateLimiter::new(10.0, 10.0);
        let ip = IpAddr::V4(Ipv4Addr::new(1,2,3,4));
        // First 10 requests should pass (burst capacity)
        for _ in 0..10 {
            assert!(rl.is_allowed(ip));
        }
        // 11th should be denied
        assert!(!rl.is_allowed(ip));
    }

    #[test]
    fn different_ips_independent() {
        let rl = IpRateLimiter::new(2.0, 1.0);
        let ip1 = IpAddr::V4(Ipv4Addr::new(1,1,1,1));
        let ip2 = IpAddr::V4(Ipv4Addr::new(2,2,2,2));
        rl.is_allowed(ip1); rl.is_allowed(ip1); // exhaust ip1
        // ip2 should still be allowed
        assert!(rl.is_allowed(ip2));
        assert!(!rl.is_allowed(ip1));
    }
}
```

---

## 14. Cloud Network Security — AWS, GCP, Azure

### 14.1 AWS Network Security

```
AWS Network Security Layers:
─────────────────────────────────────────────────────────────────
Layer               | Service/Feature          | Notes
────────────────────┼──────────────────────────┼──────────────
Physical/hypervisor | AWS Nitro System         | Custom ASIC,
                    |                          | no shared kernel
────────────────────┼──────────────────────────┼──────────────
Network perimeter   | AWS Shield Standard/Adv  | DDoS protection
                    | AWS WAF                  | L7 filtering
                    | CloudFront               | CDN + edge security
────────────────────┼──────────────────────────┼──────────────
VPC perimeter       | Internet Gateway         | Stateful NAT
                    | NAT Gateway              | Egress only
                    | Network Firewall         | Suricata-based NGFW
                    | Transit Gateway          | Hub-and-spoke routing
────────────────────┼──────────────────────────┼──────────────
Subnet / Instance   | Security Groups (SG)     | Stateful, per-ENI
                    | Network ACLs (NACL)      | Stateless, per-subnet
                    | VPC Flow Logs            | Sampled metadata
────────────────────┼──────────────────────────┼──────────────
DNS                 | Route 53 Resolver        | Private DNS
                    | Route 53 Resolver FW     | DNS egress filtering
────────────────────┼──────────────────────────┼──────────────
Connectivity        | VPN (Site-to-Site)       | IKEv2/IPsec
                    | Direct Connect           | Private fiber
                    | PrivateLink              | Service endpoint
                    |                          | isolation
─────────────────────────────────────────────────────────────────
```

**AWS Security Group vs. NACL:**

```
Security Groups:                    Network ACLs:
- Stateful (return traffic auto)    - Stateless (must allow both directions)
- Attached to ENI (per instance)    - Attached to subnet (all instances)
- Default: deny all inbound,        - Default: allow all (numbered rules)
  allow all outbound                - Evaluated in order (lowest # first)
- No explicit deny (only allow)     - Supports explicit DENY rules
- Reference other SGs               - CIDR ranges only
- Applied after NACL                - Applied before SG (traffic hits NACL first)

Use SGs for: per-instance rules, zero-trust service-to-service
Use NACLs for: subnet-wide egress restrictions, blocking specific IPs quickly
```

```hcl
# Terraform: Production VPC with security best practices

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "prod-vpc" }
}

# Flow logs — critical for forensics and compliance
resource "aws_flow_log" "vpc_flow_log" {
  vpc_id          = aws_vpc.main.id
  traffic_type    = "ALL"   # ACCEPT, REJECT, ALL
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.flow_log.arn

  # Enhanced flow log fields (v5 format)
  log_format = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${windowsize} $${tcp-flags} $${type} $${pkt-srcaddr} $${pkt-dstaddr} $${action} $${log-status} $${vpc-id} $${subnet-id} $${instance-id} $${pkt-src-aws-service} $${pkt-dst-aws-service} $${flow-direction} $${traffic-path}"
}

# Security Group: Web tier — minimal exposure
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from Internet"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for redirect only"
  }

  egress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "To app tier only"
  }

  # NO egress to 0.0.0.0/0 — explicit deny by omission
}

# Security Group: App tier — only accessible from web tier
resource "aws_security_group" "app" {
  name   = "app-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
    description     = "From web tier only"
  }

  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.db.id]
    description     = "PostgreSQL to data tier"
  }
}

# Network ACL for data subnet — belt and suspenders
resource "aws_network_acl" "data" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = [aws_subnet.data.id]

  # Allow PostgreSQL from app subnet
  ingress {
    rule_no    = 100
    protocol   = "tcp"
    from_port  = 5432
    to_port    = 5432
    cidr_block = aws_subnet.app.cidr_block
    action     = "allow"
  }

  # Allow return traffic (ephemeral ports)
  egress {
    rule_no    = 100
    protocol   = "tcp"
    from_port  = 1024
    to_port    = 65535
    cidr_block = aws_subnet.app.cidr_block
    action     = "allow"
  }

  # Deny everything else
  ingress {
    rule_no    = 32766
    protocol   = "-1"
    from_port  = 0
    to_port    = 0
    cidr_block = "0.0.0.0/0"
    action     = "deny"
  }

  egress {
    rule_no    = 32766
    protocol   = "-1"
    from_port  = 0
    to_port    = 0
    cidr_block = "0.0.0.0/0"
    action     = "deny"
  }
}

# AWS Network Firewall for deep packet inspection
resource "aws_networkfirewall_rule_group" "stateful_rules" {
  capacity = 100
  name     = "prod-stateful-rules"
  type     = "STATEFUL"

  rule_group {
    rules_source {
      stateful_rule {
        action = "DROP"
        header {
          destination      = "ANY"
          destination_port = "ANY"
          direction        = "FORWARD"
          protocol         = "TCP"
          source           = "ANY"
          source_port      = "ANY"
        }
        rule_option {
          keyword  = "sid"
          settings = ["1"]
        }
        rule_option {
          keyword  = "msg"
          settings = ["\"Block Telnet\""]
        }
        rule_option {
          keyword  = "content"
          settings = ["\"|ff f9|\", depth 2"]  # Telnet WILL command
        }
      }
    }
  }
}
```

### 14.2 GCP Network Security

```
GCP Network Security Architecture:
─────────────────────────────────────────────────────────────────
- VPC is global (spans all regions, unlike AWS per-region VPC)
- Firewall rules are attached to VPC network, applied per-instance
  via network tags or service accounts
- No implied allow-outbound: default deny egress in newer projects
- Shared VPC: host project owns the network, service projects attach
- VPC Service Controls: limit API access by perimeter (DLP, BigQuery)
- Private Google Access: reach Google APIs without public IPs
- Cloud Armor: WAF + DDoS at global load balancer level
─────────────────────────────────────────────────────────────────

# GCP Firewall rule: service account-based (preferred over tag-based)
gcloud compute firewall-rules create allow-app-to-db \
    --network=prod-vpc \
    --direction=INGRESS \
    --priority=1000 \
    --action=ALLOW \
    --rules=tcp:5432 \
    --source-service-accounts=app-sa@project.iam.gserviceaccount.com \
    --target-service-accounts=db-sa@project.iam.gserviceaccount.com \
    --description="App SA can reach DB on PostgreSQL"

# Deny all ingress (explicit default deny)
gcloud compute firewall-rules create deny-all-ingress \
    --network=prod-vpc \
    --direction=INGRESS \
    --priority=65534 \
    --action=DENY \
    --rules=all

# VPC Flow Logs
gcloud compute networks subnets update prod-subnet \
    --region=us-central1 \
    --enable-flow-logs \
    --logging-aggregation-interval=interval-5-sec \
    --logging-flow-sampling=0.5 \
    --logging-metadata=include-all

# Cloud Armor security policy (WAF + rate limiting)
gcloud compute security-policies create prod-waf-policy \
    --description="Production WAF policy"

# Add OWASP CRS (preconfigured rules)
gcloud compute security-policies rules create 1000 \
    --security-policy=prod-waf-policy \
    --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
    --action=deny-403 \
    --description="Block SQLi"

# Rate limiting rule
gcloud compute security-policies rules create 2000 \
    --security-policy=prod-waf-policy \
    --expression="true" \
    --action=rate-based-ban \
    --rate-limit-threshold-count=1000 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=300 \
    --conform-action=allow \
    --exceed-action=deny-429 \
    --enforce-on-key=IP
```

### 14.3 Azure Network Security

```
Azure Network Security:
─────────────────────────────────────────────────────────────────
- NSG (Network Security Group): stateful, applied to subnet or NIC
- ASG (Application Security Group): group VMs by function, ref in NSG
- Azure Firewall: managed NGFW with FQDN filtering, threat intel
- DDoS Protection Standard: per-VNet, adaptive tuning
- Private Endpoint / Private Link: private IP for PaaS services
- Azure Bastion: SSH/RDP broker (no public IP on VMs)
- ExpressRoute: private fiber to Azure
- VNet Service Endpoints: route PaaS traffic over Azure backbone
─────────────────────────────────────────────────────────────────

# Azure CLI: NSG with ASG-based rules
az network asg create -g prod-rg -n app-asg
az network asg create -g prod-rg -n db-asg

az network nsg create -g prod-rg -n prod-nsg

# Allow app to db on 5432 using ASGs
az network nsg rule create -g prod-rg \
    --nsg-name prod-nsg \
    -n allow-app-to-db \
    --priority 100 \
    --source-asgs app-asg \
    --destination-asgs db-asg \
    --destination-port-ranges 5432 \
    --access Allow \
    --protocol Tcp

# Deny all other inbound
az network nsg rule create -g prod-rg \
    --nsg-name prod-nsg \
    -n deny-all-inbound \
    --priority 4096 \
    --source-address-prefixes '*' \
    --destination-address-prefixes '*' \
    --destination-port-ranges '*' \
    --access Deny \
    --protocol '*'
```

### 14.4 Multi-Cloud Security Consistency

```
Multi-Cloud Security Parity Checklist:
─────────────────────────────────────────────────────────────────
Control                    | AWS           | GCP           | Azure
───────────────────────────┼───────────────┼───────────────┼────────────
Perimeter Firewall         | SG + NACL     | VPC FW Rules  | NSG
Stateful Inspection        | SG            | VPC FW        | NSG
DDoS Protection            | Shield        | Cloud Armor   | DDoS Std
WAF                        | AWS WAF       | Cloud Armor   | App GW WAF
Private Service Access     | PrivateLink   | PSC           | Priv. Link
Flow Logging               | VPC Flow Logs | VPC Flow Logs | NSG Flow Logs
DNS Security               | Route53 FW    | Cloud DNS     | Private DNS
Encryption in Transit      | ACM + TLS     | GCP managed   | App GW TLS
Network IDS                | GuardDuty     | SCC + ETD     | Defender
CSPM                       | Security Hub  | SCC           | Defender CSPM
─────────────────────────────────────────────────────────────────

For unified control: Terraform + custom policy enforcement (OPA/Rego)
covering all three clouds with consistent naming, tagging, and rule logic.
```

---

## 15. Zero Trust Network Architecture

### 15.1 Zero Trust Principles

```
Traditional perimeter model:            Zero Trust model:
─────────────────────────────           ──────────────────────────────
"Trust but verify"                      "Never trust, always verify"

Internet │ Firewall │ Corp Net           Every request evaluated:
  (evil) │ (trust   │ (trusted)          - Who is the caller? (identity)
         │  check)  │                    - What is the device? (posture)
         │          │                    - What resource?      (policy)
                                         - What context?       (time, location)
                                         - Least privilege     (min access)

SPIFFE/SPIRE: Identity for Workloads
  SVID = SPIFFE Verifiable Identity Document
  Format: X.509 cert with SAN URI = spiffe://<trust-domain>/path/to/workload
  Issued by SPIRE Agent (attested via node/workload selectors)
  Short-lived (minutes to hours) — no long-lived credentials

Envoy + mTLS:
  All service-to-service communication encrypted + authenticated
  No plaintext internal traffic
  Policy enforced at sidecar, not at app code
```

### 15.2 SPIFFE/SPIRE + Envoy mTLS

```bash
# SPIRE server setup (single-node for dev)
spire-server run -config /etc/spire/server.conf

# /etc/spire/server.conf
server {
    bind_address = "0.0.0.0"
    bind_port    = 8081
    trust_domain = "prod.example.com"
    data_dir     = "/var/lib/spire/data"
    log_level    = "INFO"
    ca_subject {
        country       = ["US"]
        organization  = ["My Org"]
        common_name   = "SPIRE Server CA"
    }
    # Rotate SVIDs every 1 hour, refresh at 30m
    default_svid_ttl = "1h"
}

plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "sqlite3"
            connection_string = "/var/lib/spire/datastore.sqlite3"
        }
    }
    KeyManager "disk" {
        plugin_data { keys_path = "/var/lib/spire/keys.json" }
    }
    NodeAttestor "join_token" {
        plugin_data {}
    }
}

# Register a workload
spire-server entry create \
    -spiffeID spiffe://prod.example.com/ns/prod/sa/payment-service \
    -parentID spiffe://prod.example.com/spire/agent/join_token/... \
    -selector k8s:ns:prod \
    -selector k8s:sa:payment-service \
    -ttl 3600

# SPIRE agent retrieves X.509 SVID → mounts to workload via Unix socket
# Envoy sidecar reads SVID via SDS (Secret Discovery Service) from SPIRE agent

# Envoy: static mTLS cluster config (simplified)
# static_resources:
#   clusters:
#   - name: upstream_service
#     transport_socket:
#       name: envoy.transport_sockets.tls
#       typed_config:
#         "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
#         common_tls_context:
#           tls_certificate_sds_secret_configs:
#           - name: "spiffe://prod.example.com/ns/prod/sa/payment-service"
#             sds_config:
#               api_config_source:
#                 api_type: GRPC
#                 grpc_services:
#                 - envoy_grpc:
#                     cluster_name: spire_agent
```

---

## 16. Kubernetes Network Security

### 16.1 Kubernetes Network Model

```
Kubernetes Networking Assumptions:
- Every Pod gets a unique IP (no NAT between pods by default)
- All pods can communicate with all other pods (by default)
- Nodes can communicate with all pods
- Pod IP is consistent from Pod's own perspective

Security problem: default allow-all is a flat network!
Solution: NetworkPolicy (L4) + service mesh mTLS (L7)

NetworkPolicy limitations:
- Only L3/L4 (IP + port)
- No L7 (HTTP path, headers, methods)
- CNI must support it (Calico, Cilium, Weave — NOT flannel)
- Default: select all pods in namespace → all denied if policy exists

For L7: use Istio AuthorizationPolicy or Cilium NetworkPolicy (L7)
```

### 16.2 Kubernetes NetworkPolicy — Production Patterns

```yaml
# Default deny-all (apply first in every namespace)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: prod
spec:
  podSelector: {}    # selects ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress
  # No rules = deny all ingress AND egress

---
# Allow specific service communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payment-service-policy
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: payment-service

  policyTypes:
  - Ingress
  - Egress

  ingress:
  # Only accept traffic from API gateway pods
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080

  egress:
  # Can reach database
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432

  # Can reach DNS (required for service resolution)
  - ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53

  # Can reach external payment processor (egress to specific CIDR)
  - to:
    - ipBlock:
        cidr: 203.0.113.0/24  # payment processor IP range
    ports:
    - protocol: TCP
      port: 443

---
# Cilium L7 NetworkPolicy (requires Cilium CNI)
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: payment-l7-policy
  namespace: prod
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: api-gateway
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: POST
          path: /api/v1/payment/.*
        - method: GET
          path: /api/v1/payment/status/.*
        # Block everything else (PUT, DELETE, admin paths)
```

### 16.3 Kubernetes API Server Security

```bash
# Audit all API requests — critical for forensics
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all exec/attach (lateral movement detection)
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach", "pods/portforward"]

# Log secret access
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]

# Log RBAC changes
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]

# Don't log noisy read-only operations
- level: None
  verbs: ["get", "list", "watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services", "configmaps"]
  users: ["system:kube-proxy"]

# Default: log metadata for everything else
- level: Metadata
```

```bash
# kube-apiserver hardening flags
--anonymous-auth=false
--audit-log-path=/var/log/kubernetes/audit.log
--audit-log-maxage=90
--audit-log-maxbackup=10
--audit-log-maxsize=100
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--authorization-mode=Node,RBAC        # never AlwaysAllow
--enable-admission-plugins=NodeRestriction,PodSecurity,ResourceQuota
--encryption-provider-config=/etc/kubernetes/encryption.yaml  # encrypt secrets at rest
--tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,...
--tls-min-version=VersionTLS12

# Encrypt secrets at rest (etcd)
# /etc/kubernetes/encryption.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources: ["secrets", "configmaps"]
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-32-byte-random-key>
  - identity: {}  # fallback for decryption of old values
```

---

## 17. Cryptographic Primitives in Network Security

### 17.1 Cipher Suite Selection

```
Recommended Cipher Suites (2024+):
─────────────────────────────────────────────────────────────────
TLS 1.3 (only these exist — automatically selected):
  TLS_AES_256_GCM_SHA384
  TLS_CHACHA20_POLY1305_SHA256
  TLS_AES_128_GCM_SHA256  (acceptable, but prefer 256)

TLS 1.2 (if still needed — strict subset):
  ECDHE-ECDSA-AES256-GCM-SHA384  (prefer ECDSA for perf)
  ECDHE-RSA-AES256-GCM-SHA384
  ECDHE-ECDSA-CHACHA20-POLY1305
  ECDHE-RSA-CHACHA20-POLY1305

Key Exchange:
  X25519 (preferred — constant-time, no timing attacks, fast)
  P-256 / P-384 (FIPS compliance)
  Never: RSA key exchange (no FS), static DH

Authentication:
  ECDSA with P-256 or P-384 (smaller certs, faster)
  Ed25519 (TLS 1.3 only — fastest, safest)
  RSA-2048+ with PSS padding (legacy compat)
  Never: RSA PKCS1v1.5 (Bleichenbacher attacks)

NEVER use:
  RC4, DES, 3DES, EXPORT ciphers, NULL, MD5, SHA-1
  CBC mode ciphers in TLS 1.2 (BEAST, POODLE)
  RSA key exchange (no forward secrecy)
─────────────────────────────────────────────────────────────────
```

### 17.2 IPsec — Architecture and Configuration

```
IPsec Modes:
─────────────────────────────────────────────────────────────────
Transport mode: encrypts payload only; IP header intact
  [IP header][ESP header][TCP/UDP payload (encrypted)][ESP trailer/auth]
  Use: host-to-host, end-to-end

Tunnel mode: encrypts entire inner IP packet
  [Outer IP][ESP header][Inner IP header + payload (encrypted)][ESP auth]
  Use: gateway-to-gateway, VPN tunnels, site-to-site

IKEv2 phases:
  Phase 1 (IKE SA): authenticate endpoints, establish secure channel
    - DH key exchange (prefer DH group 20/21 = P-384/P-521)
    - Authentication: PSK or X.509 certificates
    - Creates ISAKMP SA for Phase 2 negotiation

  Phase 2 (Child SA): negotiate ESP parameters for data traffic
    - AES-256-GCM (combined mode, no separate HMAC needed)
    - Perfect Forward Secrecy (PFS): ephemeral DH in Phase 2
─────────────────────────────────────────────────────────────────
```

```bash
# strongSwan IKEv2 configuration — site-to-site IPsec VPN
# /etc/swanctl/swanctl.conf

connections {
    site-to-site {
        version = 2         # IKEv2
        proposals = aes256gcm128-prfsha384-ecp384   # strong ciphers

        local {
            auth    = pubkey      # certificate-based auth
            certs   = site-a.pem
            id      = "site-a.example.com"
        }
        remote {
            auth    = pubkey
            certs   = site-b.pem
            id      = "site-b.example.com"
        }
        children {
            tunnel {
                local_ts  = 10.0.1.0/24   # protected traffic from site A
                remote_ts = 10.0.2.0/24   # protected traffic at site B
                esp_proposals = aes256gcm128-ecp384   # ESP with PFS
                mode      = tunnel
                dpd_action = restart   # Dead Peer Detection: auto-reconnect
            }
        }
    }
}

secrets {
    private {
        file = site-a-key.pem
    }
}
```

### 17.3 Rust: HKDF for Deriving Session Keys

```rust
// hkdf_keys.rs — derive network session keys using HKDF-SHA256
// Used in custom protocol key derivation (WireGuard-inspired)
// Cargo.toml: hkdf = "0.12", sha2 = "0.10", rand = "0.8"

use hkdf::Hkdf;
use sha2::Sha256;
use rand::RngCore;

#[derive(Debug)]
pub struct SessionKeys {
    pub send_key:    [u8; 32],   // AES-256-GCM sending key
    pub recv_key:    [u8; 32],   // AES-256-GCM receiving key
    pub send_nonce:  [u8; 12],   // initial nonce (increment per packet)
    pub recv_nonce:  [u8; 12],
}

/// Derive symmetric session keys from a shared secret (e.g., DH output)
/// and a handshake hash (transcript of all handshake messages).
///
/// Mirrors the WireGuard/Noise Protocol key derivation pattern.
pub fn derive_session_keys(
    shared_secret:   &[u8],  // 32 bytes from X25519 DH
    handshake_hash:  &[u8],  // 32 bytes: hash of all handshake messages
    info_initiator:  &[u8],  // e.g., b"initiator_key"
    info_responder:  &[u8],  // e.g., b"responder_key"
) -> SessionKeys {
    // Extract: derive a pseudorandom key from shared_secret
    // using handshake_hash as salt
    let hk = Hkdf::<Sha256>::new(Some(handshake_hash), shared_secret);

    let mut send_key   = [0u8; 32];
    let mut recv_key   = [0u8; 32];
    let mut send_nonce = [0u8; 12];
    let mut recv_nonce = [0u8; 12];

    // Expand with context-specific info strings
    hk.expand(info_initiator, &mut send_key)
        .expect("HKDF expand failed — info too long");
    hk.expand(info_responder, &mut recv_key)
        .expect("HKDF expand failed");

    // Derive nonces separately
    let nonce_info = b"nonce_material";
    let mut nonce_buf = [0u8; 24];
    hk.expand(nonce_info, &mut nonce_buf)
        .expect("HKDF expand failed");
    send_nonce.copy_from_slice(&nonce_buf[..12]);
    recv_nonce.copy_from_slice(&nonce_buf[12..]);

    SessionKeys { send_key, recv_key, send_nonce, recv_nonce }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keys_are_deterministic() {
        let secret = [0x42u8; 32];
        let hash   = [0xdeu8; 32];
        let k1 = derive_session_keys(&secret, &hash, b"send", b"recv");
        let k2 = derive_session_keys(&secret, &hash, b"send", b"recv");
        assert_eq!(k1.send_key, k2.send_key);
        assert_eq!(k1.recv_key, k2.recv_key);
    }

    #[test]
    fn different_direction_keys() {
        let secret = [0x42u8; 32];
        let hash   = [0xdeu8; 32];
        let k = derive_session_keys(&secret, &hash, b"send", b"recv");
        // Send and receive keys must be different
        assert_ne!(k.send_key, k.recv_key);
    }
}
```

---

## 18. Threat Model Reference

### 18.1 STRIDE Applied to Network Security

```
STRIDE Threat Model for Network Infrastructure:
─────────────────────────────────────────────────────────────────
Threat          | Network Example              | Control
────────────────┼──────────────────────────────┼──────────────────
Spoofing        | IP/ARP/MAC spoofing,         | mTLS, SPIFFE SVIDs,
(Identity)      | BGP origin AS spoofing       | RPKI, BCP38, DAI
────────────────┼──────────────────────────────┼──────────────────
Tampering       | MITM packet modification,    | HMAC/AEAD encryption,
(Integrity)     | BGP route modification       | MACsec, TLS, IPsec
────────────────┼──────────────────────────────┼──────────────────
Repudiation     | No audit trail for           | Signed flows logs,
(Audit)         | network access               | SIEM, NetFlow v9
────────────────┼──────────────────────────────┼──────────────────
Information     | Traffic sniffing, metadata   | Encryption all paths,
Disclosure      | analysis, side channels      | traffic shaping
────────────────┼──────────────────────────────┼──────────────────
Denial of       | SYN flood, amplification,    | SYN cookies, BH routing,
Service         | BGP session reset, L7 flood  | rate limiting, Shield
────────────────┼──────────────────────────────┼──────────────────
Elevation of    | Container escape via         | Network namespaces,
Privilege       | network namespace, SSRF      | egress filtering,
                | to metadata API              | IMDS v2 enforcement
─────────────────────────────────────────────────────────────────
```

### 18.2 Attack Paths and Mitigations

```
Attack Chain: External Attacker → Data Exfiltration
─────────────────────────────────────────────────────────────────
Step 1: Recon
  → DNS enumeration, port scanning, banner grabbing
  Mitigate: Response rate limiting DNS, no banner disclosure,
            scan detection (psad, Suricata), nmap fingerprint evasion

Step 2: Initial access
  → Exploit public-facing service (RCE, SQLi, SSRF)
  Mitigate: WAF, input validation, least-privilege service accounts,
            no unneeded ports open (strict SG/NACL)

Step 3: Lateral movement
  → Pivot from compromised host to internal services
  Mitigate: Zero-trust (mTLS required for all service-to-service),
            NetworkPolicy default-deny, no flat L3 network

Step 4: Privilege escalation
  → Reach metadata API (169.254.169.254), steal IAM credentials
  Mitigate: IMDSv2 (token-required), block 169.254.169.254 in
            NetworkPolicy egress, instance profile scoping

Step 5: Exfiltration
  → DNS tunneling, HTTPS to C2, large data transfers
  Mitigate: DNS egress filtering (Route53 Resolver FW, Pi-hole),
            JA3 fingerprinting of TLS, NetFlow anomaly detection,
            data transfer volume alerts
─────────────────────────────────────────────────────────────────
```

### 18.3 Security Hardening Checklist

```bash
# ── Host network hardening (apply via Ansible/Chef/Terraform) ──────────

# /etc/sysctl.d/99-network-security.conf
cat > /etc/sysctl.d/99-network-security.conf << 'EOF'
# === IP Spoofing protection (BCP38 equivalent) ===
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# === Disable IP source routing ===
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# === Disable ICMP redirects ===
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# === IPv6 router advertisements ===
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# === TCP hardening ===
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_timestamps = 0              # disable for privacy (uptime leak)
net.ipv4.tcp_challenge_ack_limit = 1000
net.ipv4.tcp_rfc1337 = 1                 # RFC 1337: prevent TIME_WAIT assassination

# === ICMP broadcast ignore ===
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# === Log martian packets ===
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# === Disable IPv4 forwarding (non-router hosts) ===
# net.ipv4.ip_forward = 0  (enable only on routers/NAT hosts)

# === ARP behavior ===
net.ipv4.conf.all.arp_announce = 2  # only use best IP for ARP
net.ipv4.conf.all.arp_ignore = 1    # only ARP for own IPs
EOF

sysctl --system

# Disable unused network modules
cat > /etc/modprobe.d/network-blacklist.conf << 'EOF'
# Disable DCCP (rarely used, had kernel CVEs)
install dccp /bin/true
# Disable SCTP (rarely used externally)
install sctp /bin/true
# Disable RDS (Reliable Datagram Sockets — had CVEs)
install rds /bin/true
# Disable TIPC (Transparent Inter-Process Communication)
install tipc /bin/true
# Disable IPv6 if not used
# install ipv6 /bin/true  (careful — breaks many things)
EOF
```

---

## 19. Benchmarking, Fuzzing, Testing

### 19.1 Network Performance Benchmarking

```bash
# ── Packet throughput testing ──────────────────────────────────────────

# iperf3: TCP/UDP throughput
iperf3 -s -p 5201                           # server
iperf3 -c <server> -P 4 -t 30 -b 10G       # client: 4 parallel streams, 10Gbps

# netperf: latency + throughput
netserver                                    # server
netperf -H <server> -t TCP_RR -l 30         # TCP request-response latency
netperf -H <server> -t TCP_STREAM -l 30     # TCP stream throughput
netperf -H <server> -t UDP_RR -l 30         # UDP request-response

# pktgen: kernel packet generator (line-rate)
modprobe pktgen
echo "add_device eth0@0" > /proc/net/pktgen/kpktgend_0
pgset "pkt_size 64"
pgset "count 10000000"
pgset "dst_mac 00:11:22:33:44:55"
pgset "dst 10.0.0.2"
pgset "start"

# XDP benchmark
# Use xdp-bench from xdp-tools package
xdp-bench drop eth0    # measure max drop rate at XDP

# nftables rule performance
nft add rule inet filter input counter   # count matched packets
watch -n1 'nft list ruleset | grep packets'

# Conntrack table pressure
conntrack -C   # count of current entries
watch -n1 'conntrack -C; echo "max:"; cat /proc/sys/net/netfilter/nf_conntrack_max'
```

### 19.2 Network Security Fuzzing

```bash
# ── Fuzzing network protocols ──────────────────────────────────────────

# Boofuzz: Python-based network fuzzer (successor to Sulley)
pip install boofuzz

# Simple TCP service fuzzer
python3 << 'EOF'
from boofuzz import *

def main():
    session = Session(
        target=Target(
            connection=TCPSocketConnection("127.0.0.1", 8080)
        ),
        sleep_time=0.1,
    )

    s_initialize("HTTP GET")
    s_static("GET ")
    s_string("/", name="path")   # fuzz point
    s_static(" HTTP/1.1\r\nHost: ")
    s_string("localhost", name="host")
    s_static("\r\nConnection: close\r\n\r\n")

    session.connect(s_get("HTTP GET"))
    session.fuzz()

main()
EOF

# AFL++ for fuzzing C network parsers
# Compile target with AFL instrumentation
AFL_USE_ASAN=1 afl-clang-fast -o ip_validate_fuzz ip_validate.c fuzz_main.c

# Fuzz entry point
cat > fuzz_main.c << 'EOF'
#include <stdint.h>
#include <stddef.h>

// AFL++ persistent mode
__AFL_FUZZ_INIT();

int main(void) {
    __AFL_INIT();
    uint8_t *buf = __AFL_FUZZ_TESTCASE_BUF;
    while (__AFL_LOOP(10000)) {
        uint32_t len = __AFL_FUZZ_TESTCASE_LEN;
        validate_ipv4(buf, len);   // call your parser
    }
    return 0;
}
EOF

afl-fuzz -i seeds/ -o findings/ -m none ./ip_validate_fuzz

# cargo-fuzz for Rust
cargo install cargo-fuzz
cargo fuzz add arp_parser_fuzz
# fuzz/fuzz_targets/arp_parser_fuzz.rs:
# #![no_main]
# use libfuzzer_sys::fuzz_target;
# fuzz_target!(|data: &[u8]| { let _ = ArpPacket::parse(data); });

cargo fuzz run arp_parser_fuzz -- -max_len=200
```

### 19.3 Security Testing Tools

```bash
# ── Network security test toolkit ─────────────────────────────────────

# nmap: host discovery + service fingerprinting + scripting
nmap -sV -sC -p- --script vuln <target>        # full scan + vuln scripts
nmap --script ssl-enum-ciphers -p 443 <target>  # enumerate TLS ciphers
nmap --script dns-zone-transfer <target>         # DNS zone transfer test

# testssl.sh: comprehensive TLS testing
testssl.sh --full --jsonfile results.json https://example.com
testssl.sh --cipher-per-proto example.com:443

# sslyze: TLS config auditing
sslyze --certinfo --reneg --robot --heartbleed --sslv2 --sslv3 example.com

# Scapy: packet crafting + testing
python3 << 'EOF'
from scapy.all import *

# Test firewall blocks ICMP redirects
pkt = IP(src="10.0.0.1", dst="10.0.0.2") / \
      ICMP(type=5, code=1) / \
      IP(dst="8.8.8.8") / TCP(dport=80)
send(pkt, iface="eth0")

# Test SYN cookie behavior
for i in range(1000):
    pkt = IP(dst="<server>") / TCP(sport=RandShort(), dport=443, flags="S")
    send(pkt, iface="eth0", verbose=0)
EOF

# hping3: manual packet crafting
hping3 -S --flood -V -p 443 <target>            # SYN flood test
hping3 -A -p 80 <target> --count 1000            # ACK flood test

# tcpdump: packet capture for validation
tcpdump -i eth0 -w capture.pcap \
    '(tcp and port 443) or (udp and port 53)' &

# tshark: dissect capture
tshark -r capture.pcap -Y 'tls.handshake.type == 1' \
    -T fields -e ip.src -e tls.handshake.extensions.sni.name

# Zeek (Bro): network analysis framework
zeek -r capture.pcap local   # analyze pcap
cat conn.log | zeek-cut id.orig_h id.resp_h proto duration

# Verify BCP38 (anti-spoofing) from your host
# Source spoofed packet and verify it doesn't leave your network
hping3 -a 1.2.3.4 -S -p 80 <external-target>    # if blocked: BCP38 works
```

---

## 20. Roll-out / Rollback Plan

### 20.1 Network Security Change Process

```
Change Risk Matrix:
─────────────────────────────────────────────────────────────────
Change                      | Risk  | Validation                 
────────────────────────────┼───────┼──────────────────────────
New nftables DENY rule      | High  | Test in staging exact copy
                            |       | Use nft -c (dry-run check)
BGP route policy change     | High  | Test with peer in lab,
                            |       | have rollback in 30s
TLS cipher suite change     | Med   | Test all client TLS versions
                            |       | Canary 1% traffic first
New XDP program             | High  | Verify in VM/QEMU first,
                            |       | test with pktgen
IPsec tunnel change         | High  | Keep old SA until new validated
Adding RPKI enforcement     | High  | Monitor mode first (log only),
                            |       | then enforce after 72h clean
NetworkPolicy addition      | Med   | Test connectivity post-apply,
                            |       | have kubectl delete ready
─────────────────────────────────────────────────────────────────
```

```bash
# Safe nftables rule deployment
# 1. Test syntax without applying
nft -c -f /etc/nftables/new-rules.nft

# 2. Apply atomically (single transaction)
nft -f /etc/nftables/new-rules.nft

# 3. Auto-rollback if connectivity lost (e.g., bastion disconnected)
# Run in background: restore original rules after 60s unless cancelled
(sleep 60 && nft -f /etc/nftables/backup-rules.nft \
    && logger "nftables: auto-rollback applied") &
ROLLBACK_PID=$!

# Test connectivity in another terminal
ping -c 3 gateway && curl -s https://health-check-endpoint/

# If all good: cancel rollback
kill $ROLLBACK_PID
echo "New rules validated and committed"

# Safe XDP deployment
# 1. Test in generic mode first (no driver modification)
ip link set dev eth0 xdpgeneric obj xdp_ddos.bpf.o sec xdp_ingress

# 2. Verify with traffic
curl -v --max-time 5 https://service/health

# 3. Switch to driver mode for performance
ip link set dev eth0 xdp off
ip link set dev eth0 xdp obj xdp_ddos.bpf.o sec xdp_ingress

# 4. Rollback
ip link set dev eth0 xdp off
```

### 20.2 Canary Deployment for Security Controls

```bash
# Canary BGP policy change
# Step 1: Apply new policy to 1 peer only
vtysh << 'EOF'
configure terminal
router bgp 65001
  neighbor 192.0.2.1 route-map NEW_POLICY in
  no neighbor 192.0.2.2 route-map NEW_POLICY in   # other peers: old policy
end
write
EOF

# Monitor: watch route counts, traffic, alerts
watch -n5 'vtysh -c "show bgp summary" | grep -E "Prefixes|MsgRcvd"'

# If stable after 30 min: apply to all peers
# If issues: revert single peer
vtysh -c "configure terminal" \
      -c "router bgp 65001" \
      -c "neighbor 192.0.2.1 route-map OLD_POLICY in"
```

---

## 21. References

### RFCs (Essential Reading)

```
RFC 791  — Internet Protocol (IPv4)
RFC 793  — Transmission Control Protocol
RFC 826  — Ethernet Address Resolution Protocol (ARP)
RFC 1918 — Private Address Space
RFC 2131 — DHCP
RFC 2460 — Internet Protocol Version 6
RFC 2827 — Network Ingress Filtering: BCP38
RFC 3704 — Ingress Filtering for Multihomed Networks: BCP84
RFC 4271 — BGP-4
RFC 4301 — Security Architecture for IPsec
RFC 5246 — TLS 1.2
RFC 5280 — X.509 PKI
RFC 5682 — Forward Acknowledged (FACKed) TCP
RFC 5961 — Improving TCP's Robustness to Blind In-Window Attacks
RFC 6146 — Stateful NAT64
RFC 6520 — TLS Heartbeat Extension (Heartbleed was here)
RFC 7217 — A Method for Generating Semantically Opaque IIDs
RFC 7539 — ChaCha20-Poly1305
RFC 7858 — DNS over TLS
RFC 7999 — BLACKHOLE Community (RTBH)
RFC 8446 — TLS 1.3
RFC 8656 — TURN (Traversal Using Relays around NAT)
RFC 8726 — RPKI
RFC 8926 — Geneve Encapsulation
```

### Linux Kernel Sources (Essential)

```
net/ipv4/tcp.c                  — TCP implementation
net/ipv4/tcp_input.c            — TCP receive path, SYN cookies
net/ipv4/ip_input.c             — IP receive path
net/netfilter/nf_conntrack_core.c — Connection tracking
net/core/dev.c                  — Network device layer, NAPI
net/core/filter.c               — BPF/socket filter engine
kernel/bpf/                     — eBPF verifier, maps, helpers
include/linux/skbuff.h          — sk_buff definition
include/linux/netfilter.h       — Netfilter hooks
include/net/tcp.h               — TCP socket structures
```

### Tools and Projects

```
XDP / eBPF:
  github.com/xdp-project/xdp-tools         — xdp-bench, xdp-filter
  github.com/libbpf/libbpf                 — eBPF userspace library
  github.com/iovisor/bcc                   — BCC tools (tcptop, tcptracer)
  github.com/cilium/ebpf                   — Go eBPF library (Cilium)
  github.com/cilium/cilium                 — eBPF CNI / service mesh

Firewalling:
  netfilter.org                             — nftables, iptables
  github.com/google/nftables                — Go nftables library

IDS/IPS:
  suricata.io                               — Suricata IDS/IPS
  zeek.org                                  — Zeek network analysis
  github.com/OISF/suricata                  — Suricata source

PKI and TLS:
  github.com/cloudflare/cfssl               — Production PKI tooling
  github.com/smallstep/certificates         — step-ca: ACME + SPIFFE
  github.com/spiffe/spire                   — SPIFFE/SPIRE runtime
  letsencrypt.org                           — ACME protocol

BGP / Routing:
  frrouting.org                             — FRR (BGP, OSPF, IS-IS)
  bird.network.cz                           — BIRD Internet Routing Daemon
  github.com/NLnetLabs/routinator           — RPKI validator

VPN / Encryption:
  wireguard.com                             — WireGuard VPN
  strongswan.org                            — IKEv2/IPsec

Kubernetes Networking:
  github.com/projectcalico/calico           — Calico CNI + NetworkPolicy
  github.com/cilium/cilium                  — Cilium eBPF CNI
  github.com/istio/istio                    — Istio service mesh
```

### Next 3 Steps

```
1. IMPLEMENT: Deploy the XDP SYN-flood mitigation (Section 6.2)
   on a staging host with pktgen generating >1Mpps synthetic SYN
   traffic. Measure drop rate with `bpftool map` stats and validate
   that legitimate traffic (from known IPs) still passes through.
   Then layer nftables rate-limiting (Section 5.2) on top.

2. HARDEN: Apply the sysctl hardening from Section 18.3 via an
   Ansible role. Write a Testinfra or ServerSpec test suite that
   verifies every sysctl value after provisioning. Add it to your
   CI pipeline so a drift detection job runs daily and alerts on
   deviations. Also enable VPC Flow Logs (Section 14) and ship
   to your SIEM.

3. IDENTITY: Stand up SPIRE (Section 15.2) in your Kubernetes dev
   cluster. Register workload entries for two services, verify
   that SVID X.509 certs are issued with TTL < 1h, and confirm
   mTLS between them using `openssl s_client` pointing at the
   SPIFFE SDS socket. Then write a Cilium CiliumNetworkPolicy
   (Section 16.2) that denies all inter-service traffic except
   via the authenticated mTLS path.
```

