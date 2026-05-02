# ICMP: Internet Control Message Protocol — Complete In-Depth Guide

---

## Table of Contents

1. [Overview & RFC History](#1-overview--rfc-history)
2. [ICMP in the Protocol Stack](#2-icmp-in-the-protocol-stack)
3. [ICMPv4 Packet Format](#3-icmpv4-packet-format)
4. [ICMPv4 Message Types & Codes](#4-icmpv4-message-types--codes)
5. [ICMPv6 — Architecture & Differences](#5-icmpv6--architecture--differences)
6. [Linux Kernel ICMP Implementation](#6-linux-kernel-icmp-implementation)
7. [ICMP RX Path — Kernel Code Walk](#7-icmp-rx-path--kernel-code-walk)
8. [ICMP TX Path — icmp_send()](#8-icmp-tx-path--icmp_send)
9. [ICMP Rate Limiting](#9-icmp-rate-limiting)
10. [Path MTU Discovery (PMTUD)](#10-path-mtu-discovery-pmtud)
11. [ICMP Redirect](#11-icmp-redirect)
12. [ICMP & Routing Interaction](#12-icmp--routing-interaction)
13. [ICMP Security — Attacks & Mitigations](#13-icmp-security--attacks--mitigations)
14. [Kernel Data Structures Deep Dive](#14-kernel-data-structures-deep-dive)
15. [C Implementation — Raw Socket ICMP](#15-c-implementation--raw-socket-icmp)
16. [Rust Implementation](#16-rust-implementation)
17. [Debugging & Tracing with Kernel Tools](#17-debugging--tracing-with-kernel-tools)
18. [sysctl Tunables & /proc Interface](#18-sysctl-tunables--proc-interface)
19. [eBPF / XDP ICMP Filtering](#19-ebpf--xdp-icmp-filtering)
20. [ICMP in Containers & Namespaces](#20-icmp-in-containers--namespaces)

---

## 1. Overview & RFC History

ICMP (Internet Control Message Protocol) is a **Layer 3 support protocol** — it rides
_inside_ IP but it is not a transport protocol. Its sole purpose is to carry network
diagnostic and error feedback messages between IP nodes. Every IP implementation MUST
support ICMP (RFC 1122 §3.2.2).

### RFC Timeline

```
RFC 792  (1981)  — ICMP for IPv4 — Jon Postel
RFC 950  (1985)  — ICMP Subnet Mask Request/Reply
RFC 1016 (1987)  — Source Quench (deprecated in RFC 6633)
RFC 1191 (1990)  — Path MTU Discovery using ICMP Frag-Needed
RFC 1256 (1991)  — ICMP Router Discovery
RFC 1349 (1992)  — TOS in ICMP error messages
RFC 2463 (1998)  — ICMPv6 for IPv6 (obsoleted)
RFC 2521 (1999)  — ICMP Security Failures
RFC 4443 (2006)  — ICMPv6 for IPv6 — current standard
RFC 4884 (2007)  — Extended ICMP (multi-part messages)
RFC 5837 (2010)  — Extending ICMP for Interface/Next-Hop Info
RFC 6633 (2012)  — Deprecation of ICMP Source Quench
RFC 8335 (2018)  — PROBE: A Utility for Probing Interfaces
RFC 8335 (2018)  — ICMP Extended Echo Request/Reply (Type 42/43)
```

### What ICMP Is NOT

- **Not a transport protocol** — no port numbers, no session management
- **Not reliable** — ICMP messages themselves can be lost; no retransmission
- **Not secured by default** — anyone on the path can forge ICMP
- **Not congestion control** — Source Quench (Type 4) is deprecated since 2012

### ICMP Protocol Number

IP carries ICMP using **protocol number 1** (IPv4) and **protocol number 58** (IPv6).

```
/etc/protocols:
    icmp    1   ICMP    # internet control message protocol
    ipv6-icmp 58 IPv6-ICMP
```

---

## 2. ICMP in the Protocol Stack

```
 OSI Model          TCP/IP Model           Actual Headers
 ─────────          ────────────           ──────────────
 Application   ─┐
 Presentation  ─┤  Application             HTTP / DNS / SSH
 Session       ─┘
 Transport        Transport                TCP / UDP
                                              │
 Network          Internet           ┌────────▼────────┐
                                     │   IPv4 Header   │  proto=1
                                     │  (or IPv6 NH=58)│
                                     └────────┬────────┘
                                              │
                                     ┌────────▼────────┐
                                     │  ICMP Header    │  Type/Code/Checksum
                                     │  + ICMP Body    │  (varies by type)
                                     └─────────────────┘
 Data Link        Link                Ethernet Frame
 Physical         Physical            Wire / Fiber
```

ICMP is **encapsulated directly in IP**. The IP header's Protocol field is set to 1.
When an ICMP error message is generated, the original IP header plus first 8 bytes of
the offending packet's payload is included in the ICMP body (the "original datagram"
section). This allows the sender to identify which flow caused the error.

```
ICMP Error Message Encapsulation:
┌─────────────────────────────────────────────────────────┐
│                    Ethernet Frame                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │                  IP Header (proto=1)               │  │
│  │  src=router   dst=original_sender                  │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │              ICMP Header                    │  │  │
│  │  │  Type | Code | Checksum | (type-specific)   │  │  │
│  │  │  ┌─────────────────────────────────────┐    │  │  │
│  │  │  │   Original IP Header (20+ bytes)    │    │  │  │
│  │  │  │   First 8 bytes of original payload │    │  │  │
│  │  │  └─────────────────────────────────────┘    │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

The "first 8 bytes of original payload" is enough to recover the **source port,
destination port** (TCP/UDP) or **type/code** (nested ICMP), enabling the kernel to
demultiplex the error to the correct socket (see `icmp_err()` callbacks).

---

## 3. ICMPv4 Packet Format

### 3.1 General ICMP Header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│     Type      │     Code      │           Checksum            │
├───────────────┴───────────────┼───────────────────────────────┤
│                     Type-Specific Data                        │
├───────────────────────────────────────────────────────────────┤
│              Type-Specific Data (continued)                   │
├───────────────────────────────────────────────────────────────┤
│                   Data (variable length)                      │
└───────────────────────────────────────────────────────────────┘

  Type     (8 bits):  Message category (Echo, Unreach, etc.)
  Code     (8 bits):  Sub-type within the Type
  Checksum (16 bits): One's complement of the entire ICMP message
                      including header + data; computed with checksum=0
```

**Kernel struct** (`include/uapi/linux/icmp.h`):

```c
struct icmphdr {
    __u8  type;
    __u8  code;
    __sum16 checksum;
    union {
        struct {
            __be16 id;
            __be16 sequence;
        } echo;                     /* echo datagram */
        __be32  gateway;            /* gateway address for redirect */
        struct {
            __be16 __unused;
            __be16 mtu;             /* used for frag needed (type 3 code 4) */
        } frag;
        __u8    reserved[4];
    } un;
};
```

### 3.2 Echo Request/Reply (Type 8 / Type 0)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│  Type (8/0)   │   Code (0)    │           Checksum            │
├───────────────────────────────┼───────────────────────────────┤
│         Identifier            │         Sequence Number       │
├───────────────────────────────────────────────────────────────┤
│                        Payload Data                           │
│                   (arbitrary, min 0 bytes)                    │
└───────────────────────────────────────────────────────────────┘

  Identifier:       PID of ping process (or random for socket ping)
  Sequence Number:  Monotonically increasing per echo request sent
  Data:             Arbitrary; ping(8) stuffs timestamps here
```

### 3.3 Destination Unreachable (Type 3)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│    Type (3)   │     Code      │           Checksum            │
├───────────────────────────────┼───────────────────────────────┤
│             Unused            │    Next-Hop MTU (code 4 only) │
├───────────────────────────────────────────────────────────────┤
│         Internet Header + First 8 Bytes of Original Datagram │
│                                                               │
└───────────────────────────────────────────────────────────────┘

  Code 0:  Net Unreachable
  Code 1:  Host Unreachable
  Code 2:  Protocol Unreachable
  Code 3:  Port Unreachable
  Code 4:  Fragmentation Needed and DF Set  ← PMTUD uses this
  Code 5:  Source Route Failed
  Code 6:  Destination Network Unknown
  Code 7:  Destination Host Unknown
  Code 8:  Source Host Isolated
  Code 9:  Communication with Dest Net Administratively Prohibited
  Code 10: Communication with Dest Host Administratively Prohibited
  Code 11: Dest Net Unreachable for TOS
  Code 12: Dest Host Unreachable for TOS
  Code 13: Communication Administratively Prohibited (RFC 1812)
  Code 14: Host Precedence Violation
  Code 15: Precedence Cutoff in Effect
```

### 3.4 Time Exceeded (Type 11)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│    Type (11)  │     Code      │           Checksum            │
├───────────────────────────────────────────────────────────────┤
│                            Unused                             │
├───────────────────────────────────────────────────────────────┤
│         Internet Header + First 8 Bytes of Original Datagram │
└───────────────────────────────────────────────────────────────┘

  Code 0:  Time to Live Exceeded in Transit (TTL=0)  ← traceroute uses this
  Code 1:  Fragment Reassembly Time Exceeded
```

### 3.5 Redirect (Type 5)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│    Type (5)   │     Code      │           Checksum            │
├───────────────────────────────────────────────────────────────┤
│                    Gateway Internet Address                   │
├───────────────────────────────────────────────────────────────┤
│         Internet Header + First 8 Bytes of Original Datagram │
└───────────────────────────────────────────────────────────────┘

  Code 0:  Redirect for Network
  Code 1:  Redirect for Host
  Code 2:  Redirect for Type of Service and Network
  Code 3:  Redirect for Type of Service and Host
```

### 3.6 Parameter Problem (Type 12)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│    Type (12)  │     Code      │           Checksum            │
├───────────────┬───────────────┴───────────────────────────────┤
│    Pointer    │                   Unused                      │
├───────────────────────────────────────────────────────────────┤
│         Internet Header + First 8 Bytes of Original Datagram │
└───────────────────────────────────────────────────────────────┘

  Pointer: Byte offset into original IP header where error was detected
  Code 0:  Pointer indicates the error
  Code 1:  Missing a Required Option
  Code 2:  Bad Length
```

### 3.7 Timestamp Request/Reply (Type 13 / Type 14)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│  Type (13/14) │   Code (0)    │           Checksum            │
├───────────────────────────────┼───────────────────────────────┤
│         Identifier            │         Sequence Number       │
├───────────────────────────────────────────────────────────────┤
│               Originate Timestamp (milliseconds since midnight│
│               UT; 32-bit)                                     │
├───────────────────────────────────────────────────────────────┤
│                         Receive Timestamp                     │
├───────────────────────────────────────────────────────────────┤
│                         Transmit Timestamp                    │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. ICMPv4 Message Types & Codes

### Complete Type Table

```
Type  Code  Name                              RFC     Status
────  ────  ────────────────────────────────  ──────  ───────────
0     0     Echo Reply                        792     Active
3     0-15  Destination Unreachable           792     Active
4     0     Source Quench                     792     Deprecated (RFC 6633)
5     0-3   Redirect                          792     Active (host only)
8     0     Echo Request                      792     Active
9     0     Router Advertisement              1256    Active
10    0     Router Solicitation               1256    Active
11    0-1   Time Exceeded                     792     Active
12    0-2   Parameter Problem                 792     Active
13    0     Timestamp Request                 792     Active (rarely used)
14    0     Timestamp Reply                   792     Active (rarely used)
15    0     Information Request               792     Obsolete
16    0     Information Reply                 792     Obsolete
17    0     Address Mask Request              950     Deprecated
18    0     Address Mask Reply                950     Deprecated
30    0     Traceroute                        1393    Deprecated
40    0     Photuris (Security Failures)      2521    Active
42    0     Extended Echo Request             8335    Active (2018)
43    0-4   Extended Echo Reply               8335    Active (2018)
```

### Type 3: Destination Unreachable — Detailed Code Semantics

```
Code 0  — Net Unreachable
    Router has no route to the destination network.
    Generated by: routers (not end hosts).

Code 1  — Host Unreachable
    Router can reach the network but not the specific host (ARP failed,
    host is down). Generated by: routers.

Code 2  — Protocol Unreachable
    Destination host does not support the IP protocol in the header
    (e.g., protocol field = 42 but host has no handler).
    Generated by: destination host.

Code 3  — Port Unreachable
    Destination host has no listener on the UDP port.
    TCP sends RST instead; UDP sends ICMP Port Unreachable.
    Generated by: destination host.
    *** This is the most common ICMP message in practice ***

Code 4  — Fragmentation Needed, DF Set
    A router needs to fragment a packet but DF bit is set.
    The 16-bit MTU field (RFC 1191) carries the next-hop MTU.
    Generated by: routers.
    *** Critical for PMTUD ***

Code 5  — Source Route Failed
    Strict or loose source route option failed.

Code 9  — Network Administratively Prohibited
Code 10 — Host Administratively Prohibited
Code 13 — Communication Administratively Prohibited
    Firewall reject (vs. drop which sends nothing).
    Firewalls use Code 13 for generic administrative rejection.
```

### Type 11: Time Exceeded — TTL Mechanics

```
Traceroute Mechanism Using ICMP Time Exceeded:

Sender                   R1          R2          R3       Destination
  │                       │           │           │            │
  │ UDP/ICMP, TTL=1       │           │           │            │
  ├──────────────────────>│           │           │            │
  │                       │ TTL=0     │           │            │
  │ ICMP Time Exceeded    │           │           │            │
  │ (Type 11, Code 0)     │           │           │            │
  │<──────────────────────┤           │           │            │
  │                                   │           │            │
  │ UDP/ICMP, TTL=2                   │           │            │
  ├──────────────────────────────────>│           │            │
  │                                   │ TTL=0     │            │
  │ ICMP Time Exceeded                │           │            │
  │<──────────────────────────────────┤           │            │
  │                                               │            │
  │ UDP/ICMP, TTL=3                               │            │
  ├──────────────────────────────────────────────>│            │
  │                                               │ TTL=0      │
  │ ICMP Time Exceeded                            │            │
  │<──────────────────────────────────────────────┤            │
  │                                                            │
  │ UDP/ICMP, TTL=4                                            │
  ├───────────────────────────────────────────────────────────>│
  │ ICMP Port Unreachable (Type 3, Code 3)                     │
  │<───────────────────────────────────────────────────────────┤
  │ (or ICMP Echo Reply if using ICMP mode traceroute)
```

---

## 5. ICMPv6 — Architecture & Differences

ICMPv6 (RFC 4443) is significantly more important than ICMPv4 — it is **mandatory** for
IPv6 and handles functions that were separate protocols in IPv4 (ARP → NDP, IGMP → MLD).

### 5.1 ICMPv6 Header Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│     Type      │     Code      │           Checksum            │
├───────────────────────────────────────────────────────────────┤
│                     Message Body                              │
└───────────────────────────────────────────────────────────────┘
```

**Critical difference**: ICMPv6 checksum includes a **pseudo-header** (src IP, dst IP,
upper-layer length, next-header=58). This is the same as TCP/UDP checksums in IPv6.

```c
/* include/uapi/linux/icmpv6.h */
struct icmp6hdr {
    __u8    icmp6_type;
    __u8    icmp6_code;
    __sum16 icmp6_cksum;
    union {
        __be32          un_data32[1];
        __be16          un_data16[2];
        __u8            un_data8[4];
        struct icmpv6_echo {
            __be16      identifier;
            __be16      sequence;
        } u_echo;
        struct icmpv6_nd_advt {
#if defined(__LITTLE_ENDIAN_BITFIELD)
            __u32       reserved:5,
                        override:1,
                        solicited:1,
                        router:1,
                        reserved2:24;
#elif defined(__BIG_ENDIAN_BITFIELD)
            __u32       router:1,
                        solicited:1,
                        override:1,
                        reserved:29;
#endif
        } u_nd_advt;
        struct icmpv6_nd_ra {
            __u8        hop_limit;
#if defined(__LITTLE_ENDIAN_BITFIELD)
            __u8        reserved:3,
                        router_pref:2,
                        home_agent:1,
                        other:1,
                        managed:1;
#elif defined(__BIG_ENDIAN_BITFIELD)
            __u8        managed:1,
                        other:1,
                        home_agent:1,
                        router_pref:2,
                        reserved:3;
#endif
            __be16      rt_lifetime;
        } u_nd_ra;
    } icmp6_dataun;
};
```

### 5.2 ICMPv6 Type Table

```
Type    Name                            RFC     Notes
──────  ──────────────────────────────  ──────  ─────────────────────────────
1       Destination Unreachable         4443    Codes 0,1,2,3,4,5,6,7
2       Packet Too Big                  4443    Replaces IPv4 Frag-Needed
3       Time Exceeded                   4443    Codes 0,1
4       Parameter Problem               4443    Codes 0,1,2,3
100     Private Experimentation         4443
101     Private Experimentation         4443
127     Reserved for expansion          4443
128     Echo Request                    4443
129     Echo Reply                      4443
130     MLD Query                       3810    Multicast Listener Discovery
131     MLD Report                      3810
132     MLD Done                        3810
133     Router Solicitation (RS)        4861    NDP
134     Router Advertisement (RA)       4861    NDP — carries prefix info
135     Neighbor Solicitation (NS)      4861    NDP — replaces ARP Request
136     Neighbor Advertisement (NA)     4861    NDP — replaces ARP Reply
137     Redirect                        4861    NDP
138     Router Renumbering              2894
139     ICMP Node Info Query            4620
140     ICMP Node Info Response         4620
141     Inverse NS                      3122
142     Inverse NA                      3122
143     MLDv2 Report                    3810
144     Home Agent Address Discovery    3775    Mobile IPv6
145     Home Agent Address Discovery    3775
146     Mobile Prefix Solicitation      3775
147     Mobile Prefix Advertisement     3775
148     Certification Path Solicitation 3971    SEND
149     Certification Path Advertisement 3971   SEND
151     MR Advertisement                4286    Multicast Router Discovery
152     MR Solicitation                 4286
153     MR Termination                  4286
200     Private Experimentation         4443
201     Private Experimentation         4443
255     Reserved for expansion          4443
```

### 5.3 ICMPv6 Type 2: Packet Too Big

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────┬───────────────┼───────────────────────────────┤
│    Type (2)   │   Code (0)    │           Checksum            │
├───────────────────────────────────────────────────────────────┤
│                             MTU                               │
├───────────────────────────────────────────────────────────────┤
│           As much of the invoking packet as possible          │
│        without the ICMPv6 packet exceeding 1280 bytes        │
└───────────────────────────────────────────────────────────────┘

IPv6 NEVER fragments in transit (only at source via PMTUD).
All IPv6 routers MUST support MTU >= 1280 bytes.
The minimum IPv6 MTU is 1280 bytes (RFC 8200).
```

### 5.4 Neighbor Discovery Protocol (NDP) via ICMPv6

NDP replaces IPv4's ARP. It uses ICMPv6 Types 133-137.

```
IPv4 ARP                        IPv6 NDP (ICMPv6)
──────────────────────────────  ──────────────────────────────
ARP Request  (broadcast)    →   Neighbor Solicitation (multicast to
                                 solicited-node multicast address)
ARP Reply    (unicast)      →   Neighbor Advertisement (unicast)
Gratuitous ARP              →   Unsolicited Neighbor Advertisement
RARP                        →   (not needed; SLAAC handles this)
Router Discovery (IRDP)     →   Router Solicitation / Advertisement
Proxy ARP                   →   Proxy Neighbor Advertisement

Solicited-Node Multicast Address:
  ff02::1:ff<last 24 bits of IPv6 addr>

Example: 2001:db8::1
  Solicited-node: ff02::1:ff00:0001
  Ethernet dest:  33:33:ff:00:00:01
```

```
Neighbor Solicitation (Type 135):
┌───────────────────────────────────────────────────────────────┐
│  Type(135) │ Code(0) │ Checksum                               │
├───────────────────────────────────────────────────────────────┤
│  Reserved (32 bits)                                           │
├───────────────────────────────────────────────────────────────┤
│  Target Address (128 bits — the IPv6 addr being resolved)     │
├───────────────────────────────────────────────────────────────┤
│  Options: Source Link-Layer Address (Type=1, Len=1)           │
│           │ Type(1) │ Length(1) │ Source MAC (6 bytes)        │
└───────────────────────────────────────────────────────────────┘

Neighbor Advertisement (Type 136):
┌───────────────────────────────────────────────────────────────┐
│  Type(136) │ Code(0) │ Checksum                               │
├─────┬──────────────────────────────────────────────────────── ┤
│ R|S|O │ Reserved (29 bits)                                    │
├───────────────────────────────────────────────────────────────┤
│  Target Address (128 bits)                                    │
├───────────────────────────────────────────────────────────────┤
│  Options: Target Link-Layer Address (Type=2, Len=1)           │
└───────────────────────────────────────────────────────────────┘
  R=Router, S=Solicited, O=Override
```

---

## 6. Linux Kernel ICMP Implementation

### 6.1 Key Source Files

```
net/ipv4/icmp.c         — ICMPv4 receive/send, all handler functions
net/ipv6/icmp.c         — ICMPv6 receive/send
net/ipv6/ndisc.c        — NDP (NS/NA/RS/RA/Redirect)
net/ipv6/mcast.c        — MLD (ICMPv6 types 130-132, 143)
include/uapi/linux/icmp.h    — UAPI structs (icmphdr)
include/uapi/linux/icmpv6.h  — UAPI structs (icmp6hdr)
include/linux/icmp.h         — Kernel-internal ICMP declarations
include/linux/icmpv6.h       — Kernel-internal ICMPv6 declarations
net/ipv4/ip_input.c     — IP receive dispatch (calls icmp_rcv)
net/ipv4/raw.c          — Raw socket ICMP (SOCK_RAW + IPPROTO_ICMP)
net/ipv4/ping.c         — ICMP Echo via SOCK_DGRAM (ping sockets, v3.11+)
net/ipv4/protocol.c     — inet_protocol registration
```

### 6.2 Protocol Registration

ICMPv4 is registered as a `net_protocol` handler:

```c
/* net/ipv4/icmp.c */
static const struct net_protocol icmp_protocol = {
    .handler     = icmp_rcv,         /* receive handler */
    .err_handler = icmp_err,         /* ICMP-inside-ICMP error */
    .no_policy   = 1,                /* bypass IP policy routing check */
    .netns_ok    = 1,                /* per-namespace safe */
};

void __init icmp_init(void)
{
    /* Register protocol number 1 */
    if (inet_add_protocol(&icmp_protocol, IPPROTO_ICMP) < 0)
        panic("Failed to register ICMP protocol\n");
    /* ... */
}
```

The `inet_add_protocol()` call inserts this into the global `inet_protos[]` hash table
(`net/ipv4/protocol.c`). When `ip_local_deliver_finish()` processes an IP packet with
`protocol=1`, it looks up this table and calls `icmp_rcv()`.

### 6.3 ICMP Handler Dispatch Table

```c
/* net/ipv4/icmp.c — handler function table */
static const struct icmp_control icmp_pointers[NR_ICMP_TYPES + 1] = {
    [ICMP_ECHOREPLY] = {               /* Type 0 */
        .handler = ping_rcv,
    },
    [1] = {
        .handler = icmp_discard,
        .error   = 1,
    },
    [2] = {
        .handler = icmp_discard,
        .error   = 1,
    },
    [ICMP_DEST_UNREACH] = {            /* Type 3 */
        .handler = icmp_unreach,
        .error   = 1,
    },
    [ICMP_SOURCE_QUENCH] = {           /* Type 4 — ignored since 6633 */
        .handler = icmp_unreach,
        .error   = 1,
    },
    [ICMP_REDIRECT] = {                /* Type 5 */
        .handler = icmp_redirect,
        .error   = 1,
    },
    [6] = {
        .handler = icmp_discard,
        .error   = 1,
    },
    [7] = {
        .handler = icmp_discard,
        .error   = 1,
    },
    [ICMP_ECHO] = {                    /* Type 8 */
        .handler = icmp_echo,
    },
    /* ... */
    [ICMP_TIME_EXCEEDED] = {           /* Type 11 */
        .handler = icmp_unreach,
        .error   = 1,
    },
    [ICMP_PARAMETERPROB] = {           /* Type 12 */
        .handler = icmp_unreach,
        .error   = 1,
    },
    [ICMP_TIMESTAMP] = {               /* Type 13 */
        .handler = icmp_timestamp,
    },
    [ICMP_TIMESTAMPREPLY] = {          /* Type 14 */
        .handler = icmp_discard,
    },
    [ICMP_INFO_REQUEST] = {            /* Type 15 */
        .handler = icmp_discard,
    },
    [ICMP_INFO_REPLY] = {              /* Type 16 */
        .handler = icmp_discard,
    },
    [ICMP_ADDRESS] = {                 /* Type 17 */
        .handler = icmp_discard,
    },
    [ICMP_ADDRESSREPLY] = {            /* Type 18 */
        .handler = icmp_discard,
    },
};
```

---

## 7. ICMP RX Path — Kernel Code Walk

### 7.1 Full Receive Path

```
NIC Driver
    │  skb = alloc_skb(...)
    │  napi_gro_receive() / netif_rx()
    ▼
net/core/dev.c: __netif_receive_skb()
    │  Calls registered ptype handlers
    │  For ETH_P_IP:
    ▼
net/ipv4/ip_input.c: ip_rcv()
    │  Validates IP header (checksum, length, version)
    │  NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING, ...)
    ▼
net/ipv4/ip_input.c: ip_rcv_finish()
    │  ip_route_input_noref() — routing decision
    │  If dst is local → ip_local_deliver()
    ▼
net/ipv4/ip_input.c: ip_local_deliver()
    │  Reassemble fragments if needed (ip_defrag())
    │  NF_HOOK(NFPROTO_IPV4, NF_INET_LOCAL_IN, ...)
    ▼
net/ipv4/ip_input.c: ip_local_deliver_finish()
    │  protocol = ip_hdr(skb)->protocol  /* = 1 for ICMP */
    │  ipprot = rcu_dereference(inet_protos[protocol])
    │  ipprot->handler(skb)  /* calls icmp_rcv() */
    ▼
net/ipv4/icmp.c: icmp_rcv()
    │  [See 7.2 below]
    ▼
Handler (icmp_echo, icmp_unreach, icmp_redirect, ...)
```

### 7.2 icmp_rcv() Detailed Walkthrough

```c
/* net/ipv4/icmp.c — simplified and annotated */
int icmp_rcv(struct sk_buff *skb)
{
    struct icmphdr *icmph;
    struct rtable  *rt = skb_rtable(skb);
    struct net     *net = dev_net(skb->dev);
    bool            success;

    /* (1) Ensure ICMP header is in linear skb area */
    if (!pskb_may_pull(skb, sizeof(struct icmphdr)))
        goto error;

    icmph = icmp_hdr(skb);

    /* (2) Verify checksum (over entire ICMP message) */
    if (skb_checksum_simple_validate(skb))
        goto csum_error;

    /* (3) SNMP statistics */
    __ICMP_INC_STATS(net, ICMP_MIB_INMSGS);

    /* (4) Type-specific stats */
    if (icmph->type < NR_ICMP_TYPES)
        __ICMP_INC_STATS(net, icmp_pointers[icmph->type].in_stat);

    /* (5) Is this an error ICMP? (error=1 in icmp_control) */
    if (icmp_pointers[icmph->type].error) {
        /* Must not be too short (need embedded IP header + 8 bytes) */
        if (!pskb_may_pull(skb, sizeof(struct icmphdr) +
                                sizeof(struct iphdr)))
            goto error;

        /* No ICMP errors in response to multicast or broadcast */
        if (rt->rt_flags & (RTCF_BROADCAST | RTCF_MULTICAST))
            goto error;

        /* No ICMP errors in response to ICMP errors */
        /* (checked inside individual handlers using the inner IP header) */
    }

    /* (6) Dispatch to type handler */
    success = icmp_pointers[icmph->type].handler(skb);

    if (success) {
        consume_skb(skb);
        return NET_RX_SUCCESS;
    }

error:
    kfree_skb(skb);
    return NET_RX_DROP;

csum_error:
    __ICMP_INC_STATS(net, ICMP_MIB_CSUMERRORS);
    __ICMP_INC_STATS(net, ICMP_MIB_INERRORS);
    goto error;
}
```

### 7.3 icmp_echo() — Echo Request Handler

```c
/* net/ipv4/icmp.c */
static bool icmp_echo(struct sk_buff *skb)
{
    struct net *net = dev_net(skb->dev);

    /* sysctl: net.ipv4.icmp_echo_ignore_all — drop if set */
    if (net->ipv4.sysctl_icmp_echo_ignore_all)
        return true;

    /* sysctl: net.ipv4.icmp_echo_ignore_broadcasts */
    if (net->ipv4.sysctl_icmp_echo_ignore_broadcasts) {
        if (rt_is_broadcast(skb_rtable(skb)) ||
            ipv4_is_multicast(ip_hdr(skb)->daddr))
            return true;
    }

    /* Try ICMP socket first (ping(4) / SOCK_DGRAM ICMP) */
    if (!icmp_echo_reply_with_pmtu(skb))
        return true;

    /* Build and send ICMP Echo Reply */
    icmp_send_reply(skb, ICMP_ECHOREPLY, 0, 0);
    return true;
}
```

### 7.4 icmp_unreach() — Error Message Handler

```c
/* net/ipv4/icmp.c — handles Type 3, 4, 11, 12 */
static bool icmp_unreach(struct sk_buff *skb)
{
    const struct iphdr *iph;
    struct icmphdr *icmph = icmp_hdr(skb);
    struct net *net = dev_net(skb->dev);
    u32 info = 0;

    /*
     * Pull the inner (original) IP header from the ICMP payload.
     * This is the header of the packet that caused the error.
     */
    iph = (const struct iphdr *)skb->data;

    /* Sanity: inner IP header must be IPv4, valid IHL */
    if (iph->ihl < 5)
        goto out;

    if (icmph->type == ICMP_DEST_UNREACH) {
        switch (icmph->code & 15) {
        case ICMP_NET_UNREACH:
        case ICMP_HOST_UNREACH:
        case ICMP_PORT_UNREACH:
        case ICMP_NET_ANO:
        case ICMP_HOST_ANO:
        case ICMP_PKT_FILTERED:
            /* These will set ECONNREFUSED / EHOSTUNREACH on socket */
            break;
        case ICMP_FRAG_NEEDED:
            /* Path MTU Discovery — extract the MTU from icmph->un.frag.mtu */
            info = ntohs(icmph->un.frag.mtu);
            if (!info) {
                /* Pre-RFC 1191 router; guess MTU from plateau table */
                info = ip_rt_frag_needed(net, iph,
                            ntohs(ip_hdr(skb)->tot_len), skb->dev);
            }
            /* Update route cache with new PMTU */
            if (INET_ECN_is_not_ect(iph->tos))
                ip_update_pmtu(skb, net, info,
                               ip_hdr(skb)->daddr,
                               ip_hdr(skb)->saddr);
            break;
        case ICMP_SR_FAILED:
            /* Source route failed — treat as host unreachable */
            break;
        default:
            break;
        }
    } else if (icmph->type == ICMP_TIME_EXCEEDED &&
               icmph->code == ICMP_EXC_FRAGTIME) {
        /* Fragment reassembly timeout — nothing to do for sockets */
        goto out;
    }

    /*
     * Find the socket that sent the original packet and
     * deliver the error via its error queue / sock_error().
     * Uses the inner IP header's protocol to find the right
     * inet_protocol handler's err_handler.
     */
    raw_icmp_error(skb, iph->protocol, info);  /* raw sockets */
    ipprot = rcu_dereference(inet_protos[iph->protocol]);
    if (ipprot && ipprot->err_handler)
        ipprot->err_handler(skb, info);        /* TCP/UDP err handlers */

out:
    return true;
}
```

---

## 8. ICMP TX Path — icmp_send()

`icmp_send()` is the primary kernel function to generate ICMP error messages. It is
called from throughout the networking stack (IP forwarding, TCP, UDP, etc.).

```
Callers of icmp_send():
  net/ipv4/ip_forward.c  ip_forward()         → TTL exceeded
  net/ipv4/ip_input.c    ip_local_deliver()   → Protocol unreachable
  net/ipv4/ip_output.c   ip_fragment()        → Frag needed (DF set)
  net/ipv4/udp.c         __udp4_lib_rcv()     → Port unreachable
  net/ipv4/route.c       ip_error()           → Net/Host unreachable
  net/ipv4/ip_options.c  ip_options_compile() → Parameter problem
```

### 8.1 icmp_send() Code Walk

```c
/* net/ipv4/icmp.c */
void icmp_send(struct sk_buff *skb_in, int type, int code, __be32 info)
{
    struct iphdr *iph = ip_hdr(skb_in);
    struct icmp_bxm icmp_param;
    struct rtable *rt = skb_rtable(skb_in);
    struct ipcm_cookie ipc;
    struct flowi4 fl4;
    __be32 saddr;
    int room;
    struct net *net = dev_net(skb_in->dev ?: skb_dst(skb_in)->dev);

    /*
     * Rule 1: Never send ICMP errors in response to:
     *   (a) ICMP error messages (prevents infinite loops)
     *   (b) Broadcast/multicast IP packets
     *   (c) Packets with a source address of 0 or 127.*
     *   (d) Fragmented packets (not first fragment)
     */
    if (iph->frag_off & htons(IP_OFFSET))   /* not first fragment */
        return;
    if (iph->daddr == htonl(INADDR_BROADCAST))
        return;
    if (ipv4_is_multicast(iph->daddr))
        return;
    if (iph->saddr == 0 || ipv4_is_loopback(iph->saddr))
        return;
    if (iph->saddr == htonl(INADDR_BROADCAST))
        return;

    /* Rule 2: ICMP errors cannot be sent in response to ICMP errors */
    if (type == ICMP_DEST_UNREACH || type == ICMP_REDIRECT ||
        type == ICMP_TIME_EXCEEDED || type == ICMP_PARAMETERPROB) {
        const struct icmphdr *icmph =
            (const struct icmphdr *)((unsigned char *)iph + iph->ihl * 4);
        if (icmph->type != ICMP_ECHO && icmph->type != ICMP_TIMESTAMP &&
            icmph->type != ICMP_INFO_REQUEST && icmph->type != ICMP_ADDRESS) {
            /* Original was an ICMP error — suppress */
            return;
        }
    }

    /* Rate limiting */
    if (!icmpv4_xrlim_allow(net, rt, &fl4, type, code))
        return;

    /* Build the reply: fill icmp_param */
    icmp_param.data.icmph.type             = type;
    icmp_param.data.icmph.code             = code;
    icmp_param.data.icmph.un.gateway       = info;
    icmp_param.data.icmph.checksum         = 0;
    icmp_param.skb   = skb_in;
    icmp_param.offset = skb_network_offset(skb_in);
    icmp_param.data_len = min_t(int,
                    /* RFC says: IP header + 8 bytes of original */
                    skb_in->len - skb_network_offset(skb_in),
                    /* But try to include more if possible (Extended ICMP) */
                    576 - sizeof(struct iphdr) - sizeof(struct icmphdr));
    icmp_param.head_len = sizeof(struct icmphdr);

    /* Route lookup for the reply */
    saddr = icmp_reply_saddr(net, rt, iph, type);
    /* ... flowi4 setup, ip_route_output_key() ... */

    /* Send via icmp_push_reply() → ip_push_pending_frames() */
    icmp_push_reply(&icmp_param, &fl4, &ipc, &rt);
}
EXPORT_SYMBOL(icmp_send);
```

### 8.2 ICMP Checksum Computation

ICMP checksum covers the entire ICMP message (header + data). It uses one's complement:

```c
/* In icmp_push_reply() → ip_append_data() → ... */
/* The checksum is computed by:
 * 1. Set checksum field to 0
 * 2. Sum all 16-bit words of the ICMP message
 * 3. Fold carries: add high 16 bits to low 16 bits
 * 4. Take one's complement (~)
 */

static __sum16 icmp_checksum(const void *buf, int len)
{
    return csum_fold(csum_partial(buf, len, 0));
}

/* For ICMPv6, must include IPv6 pseudo-header: */
static __sum16 icmpv6_checksum_with_pseudo_header(
    const struct ipv6hdr *ip6h,
    const struct icmp6hdr *icmp6h,
    int len)
{
    __wsum csum = 0;
    /* Pseudo-header: src, dst, length, zero*3, next-header=58 */
    csum = csum_partial(ip6h->saddr.s6_addr, 16, csum);
    csum = csum_partial(ip6h->daddr.s6_addr, 16, csum);
    /* ... add length and next header ... */
    csum = csum_partial(icmp6h, len, csum);
    return csum_fold(csum);
}
```

---

## 9. ICMP Rate Limiting

Rate limiting is **critical** — without it, a single port scan or routing loop can flood
a host with ICMP error messages. Linux implements two mechanisms.

### 9.1 Token Bucket (icmp_ratemask / icmp_ratelimit)

```c
/* net/ipv4/icmp.c — icmpv4_xrlim_allow() */
static bool icmpv4_xrlim_allow(struct net *net, struct rtable *rt,
                                struct flowi4 *fl4, int type, int code)
{
    struct dst_entry *dst = &rt->dst;
    struct net *net = dev_net(dst->dev);
    bool rc = true;

    /* Bypass rate limit for Echo Reply and Timestamp Reply */
    if (type == ICMP_ECHOREPLY || type == ICMP_TIMESTAMPREPLY)
        return true;

    /* Check if this type/code is in the rate-limited mask */
    if (!((1 << type) & net->ipv4.sysctl_icmp_ratemask))
        return true;   /* not rate-limited */

    /* Per-destination rate limiting using the route dst_entry */
    if (dst->dev && (dst->dev->flags & IFF_LOOPBACK))
        goto out;

    rc = icmp_global_allow(net);   /* global token bucket */
out:
    return rc;
}

/* Token bucket state: net->ipv4.icmp_global (struct icmp_mib) */
/* Rate: net.ipv4.icmp_ratelimit (default: 1000 = 1000 tokens/sec,
 *       i.e., max 1000 ICMP error messages/second globally) */
```

### 9.2 Global vs Per-Destination Rate Limiting

```
net.ipv4.icmp_ratelimit    (default: 1000)
    └── Interval in microseconds between ICMP messages
        0 = unlimited, 1000 = 1000/sec max globally

net.ipv4.icmp_ratemask     (default: 0x1818)
    └── Bitmask of ICMP types to rate-limit:
        bit 3  = Type 3  (Dest Unreachable)
        bit 4  = Type 4  (Source Quench)
        bit 11 = Type 11 (Time Exceeded)
        bit 12 = Type 12 (Parameter Problem)
        0x1818 = bits 3,4,11,12
```

```
Token Bucket Algorithm:
  ┌─────────────────────────────────┐
  │  Bucket: max 'burst' tokens     │
  │  Refill: 1 token per 'interval' │
  │                                 │
  │  Per ICMP send attempt:         │
  │    if tokens > 0:               │
  │      tokens--                   │
  │      ALLOW                      │
  │    else:                        │
  │      DISCARD (rate limited)     │
  └─────────────────────────────────┘

struct icmp_mib (per-cpu, in net namespace):
  icmp_global.credit      — current token count
  icmp_global.stamp       — last refill time
  icmp_global.lock        — spinlock
```

---

## 10. Path MTU Discovery (PMTUD)

PMTUD (RFC 1191 for IPv4, RFC 8201 for IPv6) discovers the smallest MTU along a path
without sending probe packets by using ICMP Fragmentation Needed messages.

### 10.1 IPv4 PMTUD Flow

```
Sender (host A, MSS=1460)         Router R1 (MTU=1500)    Router R2 (MTU=576)   Destination
        │                               │                        │                    │
        │ IP pkt, DF=1, len=1500        │                        │                    │
        ├──────────────────────────────>│                        │                    │
        │                               │ Needs to forward:      │                    │
        │                               │ outgoing MTU=576,      │                    │
        │                               │ pkt len=1500 > MTU     │                    │
        │                               │ DF bit is set → cannot │                    │
        │                               │ fragment → send ICMP   │                    │
        │ ICMP Type 3, Code 4           │                        │                    │
        │ Next-Hop MTU = 576            │                        │                    │
        │<──────────────────────────────┤                        │                    │
        │                               │                        │                    │
        │ Update PMTU cache: 576        │                        │                    │
        │ Retransmit with len <= 576    │                        │                    │
        ├──────────────────────────────>│───────────────────────>│──────────────────> │
```

### 10.2 Kernel PMTU Cache

```c
/* net/ipv4/route.c — PMTU update on ICMP Frag Needed */
void ip_update_pmtu(struct sk_buff *skb, struct net *net, u32 mtu,
                    __be32 dest, __be32 nexthop)
{
    struct rtable *rt;
    /* ... */
    rt = ip_route_output(net, dest, nexthop, 0, 0, 0);
    if (!IS_ERR(rt)) {
        dst_metric_set(&rt->dst, RTAX_MTU, mtu);
        /* PMTU is stored per-route in the dst_entry's metrics */
        /* Expires after net.ipv4.route.mtu_expires (default 600s) */
        dst_release(&rt->dst);
    }
}

/* PMTU can be inspected via:
 * ip route show cache
 * ip route get <dst>
 * /proc/net/rt_cache (deprecated)
 */
```

### 10.3 TCP's Interaction with PMTUD

```
TCP sets DF=1 on all segments by default (since Linux 2.2).
When ICMP Frag Needed arrives:
  1. icmp_unreach() → tcp_v4_err() (err_handler for IPPROTO_TCP)
  2. tcp_v4_err() finds the TCP socket by 4-tuple in inner IP header
  3. Updates tp->mss_cache to new PMTU - IP/TCP headers overhead
  4. Re-segments any packets in write queue that exceed new MSS
  5. If socket is in SYN_SENT, remembers PMTU for syn retransmit

/* net/ipv4/tcp_ipv4.c */
void tcp_v4_err(struct sk_buff *skb, u32 info)
{
    /* info = next-hop MTU from ICMP Frag Needed */
    const struct iphdr *iph = (const struct iphdr *)skb->data;
    struct tcphdr *th = (struct tcphdr *)(skb->data + (iph->ihl << 2));
    struct inet_connection_sock *icsk;
    struct tcp_sock *tp;
    struct sock *sk;
    /* ... */
    sk = inet_lookup(net, &tcp_hashinfo, /* 4-tuple from inner header */
                     iph->daddr, th->dest, iph->saddr, th->source,
                     inet_iif(skb));
    /* ... */
    if (sk->sk_state == TCP_SYN_SENT)
        tcp_sync_mss(sk, dst_mtu(dst));
    else
        tcp_update_pmtu(sk, dst);
    /* ... */
}
```

### 10.4 Black Hole Detection

Some firewalls silently drop ICMP Frag Needed messages, breaking PMTUD. Linux detects
this (PMTU Black Holes) and automatically reduces MSS:

```c
/* Controlled by: net.ipv4.tcp_mtu_probing
 *   0 = disabled
 *   1 = enabled only when black hole detected
 *   2 = always use TCP MSS probing (start at tcp_base_mss)
 *
 * net.ipv4.tcp_base_mss (default: 1024) — fallback MSS
 * net.ipv4.tcp_probe_threshold — retransmit threshold before probing
 */
```

---

## 11. ICMP Redirect

ICMP Redirect (Type 5) allows a router to inform a host that a better gateway exists
for a particular destination.

### 11.1 When Redirects Are Sent

```
Network:
  Host A ─── Switch ─── Router R1 ─── Internet
                    │
                    └── Router R2 ─── Network B

Scenario: Host A sends traffic to Network B via its default GW (R1).
          R1 knows R2 is a better next hop on the same subnet.
          R1 sends ICMP Redirect to Host A:
            Type=5, Code=1 (Redirect for Host)
            Gateway=R2's IP
            Data=original IP header + 8 bytes

After redirect:
  Host A updates its routing cache to use R2 for Network B.
```

### 11.2 Kernel Redirect Processing

```c
/* net/ipv4/icmp.c */
static bool icmp_redirect(struct sk_buff *skb)
{
    if (skb->len < sizeof(struct iphdr))
        return false;

    if (!IN_DEV_RX_REDIRECTS(in_dev))  /* net.ipv4.conf.*.accept_redirects */
        return true;

    /* Security: only accept redirects from current gateway for a route */
    ip_rt_redirect(ip_hdr(skb)->saddr, /* router sending redirect */
                   iph->daddr,          /* original destination */
                   icmph->un.gateway,   /* new gateway suggested */
                   iph->saddr,          /* original source (us) */
                   skb->dev);
    return true;
}

/* net/ipv4/route.c — ip_rt_redirect() */
/* Creates a redirect (RTCF_REDIRECTED) entry in the route cache
 * with the new gateway. Expires after ip_rt_redirect_silence.
 */
```

### 11.3 Redirect Security Considerations

```
Redirect attacks allow MITM by redirecting traffic to attacker-controlled GW.
Linux mitigations:
  net.ipv4.conf.all.accept_redirects = 0   (disable on routers/servers)
  net.ipv4.conf.all.secure_redirects = 1   (only accept from known GW)
  net.ipv4.conf.all.send_redirects = 0     (on forwarding hosts)

secure_redirects (default: 1):
  Only accepts redirect from the gateway currently used for that dest.
  Prevents injection of arbitrary redirects from off-path attackers.
```

---

## 12. ICMP & Routing Interaction

### 12.1 ICMP and the dst_entry / rtable

```c
/*
 * Every sk_buff carries a dst_entry (skb_dst(skb)) after routing.
 * For ICMP error replies, the kernel must perform a reverse route lookup
 * to reach the original sender.
 */

/* net/ipv4/icmp.c — icmp_route_lookup() */
static struct rtable *icmp_route_lookup(struct net *net,
                                         struct flowi4 *fl4,
                                         struct sk_buff *skb_in,
                                         const struct iphdr *iph,
                                         __be32 saddr, u8 tos, u32 mark,
                                         int type, int code)
{
    struct rtable *rt, *rt2;

    /* Build flowi4 for reverse lookup */
    flowi4_init_output(fl4, L3MDEV_MASTER_IFINDEX(skb_in->dev),
                       mark, tos,
                       RT_SCOPE_UNIVERSE, IPPROTO_ICMP,
                       inet_sk_flowi_flags(NULL),
                       iph->saddr,    /* dst = original source */
                       saddr,         /* src = our address */
                       0, 0);

    rt = __ip_route_output_key(net, fl4);
    /* ... */
    return rt;
}
```

### 12.2 ICMP and VRF / Network Namespaces

Each network namespace has its own ICMP state:

```c
/* net/ipv4/icmp.c — per-namespace sysctl values */
struct netns_ipv4 {
    /* ... */
    int sysctl_icmp_echo_ignore_all;
    int sysctl_icmp_echo_ignore_broadcasts;
    int sysctl_icmp_ignore_bogus_error_responses;
    int sysctl_icmp_ratelimit;
    int sysctl_icmp_ratemask;
    int sysctl_icmp_errors_use_inbound_ifaddr;
    /* icmp_global: per-net token bucket for rate limiting */
    struct {
        spinlock_t  lock;
        u32         credit;
        u32         stamp;
    } icmp_global;
};
```

---

## 13. ICMP Security — Attacks & Mitigations

### 13.1 Attack Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                     ICMP Attack Taxonomy                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. ICMP Flood (Smurf, Ping of Death, Direct Flood)             │
│     ├── Smurf: src=victim, dst=broadcast → amplification        │
│     ├── Ping of Death: oversized ping (>65535 bytes) — ancient  │
│     └── Direct: high-rate echo requests → CPU exhaustion        │
│                                                                   │
│  2. ICMP-based Information Gathering                             │
│     ├── Ping sweep: host discovery                               │
│     ├── Traceroute: path/topology mapping                        │
│     └── Timestamp: clock skew → device fingerprinting          │
│                                                                   │
│  3. ICMP Injection Attacks (requires on-path or spoofing)       │
│     ├── ICMP Redirect Hijacking: reroute traffic via MITM      │
│     ├── ICMP Frag Needed spoofing: force MSS reduction (DoS)   │
│     ├── ICMP Source Quench: force TCP rate reduction (obsolete)│
│     └── ICMP Hard Error: terminate TCP connections (RST equiv) │
│                                                                   │
│  4. ICMP Tunnel / Covert Channel                                 │
│     └── Carry arbitrary data in Echo Request/Reply payload     │
│         (ptunnel, icmptunnel tools — bypasses firewalls)        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 ICMP Hard Error — TCP Connection Termination

This is a serious and often overlooked attack vector (CVE-2004-0790, CVE-2004-0791):

```
Off-path attacker can terminate TCP connections:
  1. Observe src/dst IP of a TCP session (e.g., from BGP table, DNS)
  2. Forge ICMP Dest Unreachable (Code 1 or 3) with:
     - Outer IP: src=victim_router, dst=client
     - Inner IP: src=client, dst=server, proto=6 (TCP)
     - Inner TCP: sport=<guessed or known>, dport=<server port>
  3. Kernel's tcp_v4_err() receives this error
  4. Sets sk->sk_err = ECONNREFUSED
  5. Application's next recv() gets -ECONNREFUSED

Linux mitigation (RFC 5927 compliant since ~v2.6.12):
  The kernel validates that the Inner TCP SEQ number is within the
  current receive window before killing the connection.
  (ICMP hard error → soft error if SEQ out-of-window)

  net.ipv4.tcp_rfc1337 = 1  (TIME_WAIT assassination prevention)
```

### 13.3 ICMP Frag Needed Spoofing (MSS/PMTU Attack)

```
Attacker forges ICMP Type 3 Code 4 with very small MTU (e.g., 68):
  → tcp_v4_err() → tcp_sync_mss(sk, 68)
  → TCP segments shrink to ~28 bytes
  → Massive overhead, effective DoS

Linux mitigations:
  ip_rt_min_pmtu (default: 552) — minimum accepted PMTU
  ip_rt_mtu_expires (default: 600s) — PMTU cache TTL
  TCP_MIN_MSS (default: 88) — minimum MSS enforced in tcp.h

  Mitigation: net.ipv4.ip_no_pmtu_disc = 0  (keep PMTUD enabled)
              Firewall: only accept ICMP Frag Needed from known routers
```

### 13.4 ICMP Tunnel / Covert Channel

```
ICMP Tunnel Architecture:
  Client ──── ICMP Echo Req (payload=TCP data) ────> ICMP Proxy ──── TCP ──── Server
  Client <─── ICMP Echo Rep (payload=TCP resp) ───── ICMP Proxy

Tools: ptunnel, icmptunnel, hans
Detection: payload entropy, timing patterns, unusual ICMP ID/seq patterns
Prevention: DPI, payload inspection, rate limiting on ICMP data size
```

### 13.5 Kernel Hardening Sysctls

```bash
# Recommended production server ICMP hardening:
sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1
sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.default.accept_redirects=0
sysctl -w net.ipv4.conf.all.secure_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv4.icmp_ratelimit=1000
sysctl -w net.ipv4.icmp_ratemask=6168    # Limit types 3,4,11,12
# Router: keep echo enabled for diagnostics but rate-limit
sysctl -w net.ipv4.icmp_echo_ignore_all=0
# Firewall rule to limit ping rate (not just kernel rate limiting):
# iptables -A INPUT -p icmp --icmp-type echo-request -m limit \
#          --limit 1/s --limit-burst 4 -j ACCEPT
# iptables -A INPUT -p icmp --icmp-type echo-request -j DROP
```

---

## 14. Kernel Data Structures Deep Dive

### 14.1 sk_buff and ICMP

```
sk_buff layout for an incoming ICMP packet:

skb->data ──────────────┐
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ Ethernet Header (14 bytes)                                    │
│   dst_mac | src_mac | ethertype=0x0800                       │
├──────────────────────────────────────────────────────────────┤  ← skb->network_header
│ IP Header (20 bytes)                                          │
│   ver=4 | ihl=5 | tos | tot_len | id | frag | ttl | proto=1  │
│   src_ip | dst_ip                                             │
├──────────────────────────────────────────────────────────────┤  ← skb->transport_header
│ ICMP Header (8 bytes)                                         │
│   type | code | checksum | id | sequence                     │
├──────────────────────────────────────────────────────────────┤
│ ICMP Data / Payload                                           │
│   (for echo: timestamp + padding)                            │
└──────────────────────────────────────────────────────────────┘
                                                               ▲
skb->tail ──────────────────────────────────────────────────────┘

Key macros:
  ip_hdr(skb)    → (struct iphdr *)skb->network_header
  icmp_hdr(skb)  → (struct icmphdr *)skb->transport_header
  skb->data      → points to beginning of current protocol header
```

### 14.2 ICMP MIB Statistics

```c
/* Tracked in /proc/net/snmp and /proc/net/netstat */
/* include/uapi/linux/snmp.h */
enum {
    ICMP_MIB_NUM = 0,
    ICMP_MIB_INMSGS,                 /* InMsgs */
    ICMP_MIB_INERRORS,               /* InErrors */
    ICMP_MIB_INDESTUNREACHS,         /* InDestUnreachs */
    ICMP_MIB_INTIMEEXCDS,            /* InTimeExcds */
    ICMP_MIB_INPARMPROBS,            /* InParmProbs */
    ICMP_MIB_INSRCQUENCHS,           /* InSrcQuenchs */
    ICMP_MIB_INREDIRECTS,            /* InRedirects */
    ICMP_MIB_INECHOS,                /* InEchos */
    ICMP_MIB_INECHOREPS,             /* InEchoReps */
    ICMP_MIB_INTIMESTAMPS,           /* InTimestamps */
    ICMP_MIB_INTIMESTAMPREPS,        /* InTimestampReps */
    ICMP_MIB_INADDRMASKS,            /* InAddrMasks */
    ICMP_MIB_INADDRMASKREPS,         /* InAddrMaskReps */
    ICMP_MIB_OUTMSGS,                /* OutMsgs */
    ICMP_MIB_OUTERRORS,              /* OutErrors */
    ICMP_MIB_OUTDESTUNREACHS,        /* OutDestUnreachs */
    ICMP_MIB_OUTTIMEEXCDS,           /* OutTimeExcds */
    ICMP_MIB_OUTPARMPROBS,           /* OutParmProbs */
    ICMP_MIB_OUTSRCQUENCHS,          /* OutSrcQuenchs */
    ICMP_MIB_OUTREDIRECTS,           /* OutRedirects */
    ICMP_MIB_OUTECHOS,               /* OutEchos */
    ICMP_MIB_OUTECHOREPS,            /* OutEchoReps */
    ICMP_MIB_OUTTIMESTAMPS,          /* OutTimestamps */
    ICMP_MIB_OUTTIMESTAMPREPS,       /* OutTimestampReps */
    ICMP_MIB_OUTADDRMASKS,           /* OutAddrMasks */
    ICMP_MIB_OUTADDRMASKREPS,        /* OutAddrMaskReps */
    ICMP_MIB_CSUMERRORS,             /* InCsumErrors */
    ICMP_MIB_RATELIMITGLOBAL,        /* OutRateLimitGlobal (v5.3+) */
    ICMP_MIB_RATELIMITHOST,          /* OutRateLimitHost   (v5.3+) */
    __ICMP_MIB_MAX
};
```

---

## 15. C Implementation — Raw Socket ICMP

### 15.1 Complete ICMPv4 Ping — Raw Socket

```c
/*
 * icmp_ping.c — ICMPv4 Echo Request/Reply using raw sockets
 * Build: gcc -O2 -Wall -o icmp_ping icmp_ping.c
 * Run:   sudo ./icmp_ping 8.8.8.8   (requires CAP_NET_RAW)
 *
 * Kernel-style: no stdlib beyond syscall wrappers, explicit types.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <arpa/inet.h>
#include <netdb.h>

#define ICMP_DATA_LEN   56      /* same as ping(8) default */
#define ICMP_HDR_LEN    8       /* sizeof(struct icmphdr) */
#define IP_HDR_LEN      20      /* minimum; no options */
#define RECV_BUF_LEN    1500

/* ─── Checksum ─────────────────────────────────────────────── */
/*
 * Standard one's complement checksum.
 * Used for ICMP (and IP header itself).
 * Input must be 16-bit aligned; if len is odd, pad last byte.
 */
static __u16 icmp_checksum(const void *buf, int len)
{
    const __u16 *ptr = (const __u16 *)buf;
    __u32 sum = 0;

    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }
    if (len == 1)
        sum += *(__u8 *)ptr;    /* last odd byte */

    /* Fold 32-bit sum into 16-bit */
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);

    return (__u16)~sum;
}

/* ─── Payload (timeval for RTT measurement) ─────────────────── */
struct icmp_payload {
    struct timeval tv;
    __u8 pad[ICMP_DATA_LEN - sizeof(struct timeval)];
};

/* ─── Build ICMP Echo Request ───────────────────────────────── */
static void icmp_build_echo(__u8 *buf, __u16 id, __u16 seq)
{
    struct icmphdr *hdr = (struct icmphdr *)buf;
    struct icmp_payload *payload =
        (struct icmp_payload *)(buf + ICMP_HDR_LEN);

    hdr->type             = ICMP_ECHO;
    hdr->code             = 0;
    hdr->checksum         = 0;
    hdr->un.echo.id       = htons(id);
    hdr->un.echo.sequence = htons(seq);

    /* Stamp send time into payload for RTT calculation */
    gettimeofday(&payload->tv, NULL);
    memset(payload->pad, 0xAB, sizeof(payload->pad));

    /* Checksum over header + payload */
    hdr->checksum = icmp_checksum(buf, ICMP_HDR_LEN + ICMP_DATA_LEN);
}

/* ─── Parse ICMP Echo Reply ─────────────────────────────────── */
static int icmp_parse_reply(const __u8 *buf, int len,
                             __u16 id, __u16 seq,
                             double *rtt_ms)
{
    const struct iphdr    *iph;
    const struct icmphdr  *icmph;
    const struct icmp_payload *payload;
    int ip_hlen;
    struct timeval tv_recv, tv_sent;

    if (len < IP_HDR_LEN + ICMP_HDR_LEN + (int)sizeof(struct timeval))
        return -EINVAL;

    iph    = (const struct iphdr *)buf;
    ip_hlen = iph->ihl * 4;

    if (len < ip_hlen + ICMP_HDR_LEN)
        return -EINVAL;

    icmph = (const struct icmphdr *)(buf + ip_hlen);

    /* Only interested in Echo Reply to our probes */
    if (icmph->type != ICMP_ECHOREPLY)
        return -EAGAIN;

    if (ntohs(icmph->un.echo.id) != id)
        return -EAGAIN;

    if (ntohs(icmph->un.echo.sequence) != seq)
        return -EAGAIN;

    /* RTT: current time - send timestamp in payload */
    payload = (const struct icmp_payload *)(buf + ip_hlen + ICMP_HDR_LEN);
    gettimeofday(&tv_recv, NULL);
    tv_sent = payload->tv;

    *rtt_ms = (double)(tv_recv.tv_sec  - tv_sent.tv_sec)  * 1000.0 +
              (double)(tv_recv.tv_usec - tv_sent.tv_usec) / 1000.0;

    return 0;
}

/* ─── Main ──────────────────────────────────────────────────── */
int main(int argc, char **argv)
{
    int sockfd;
    struct sockaddr_in dest;
    struct hostent *he;
    __u8 send_buf[ICMP_HDR_LEN + ICMP_DATA_LEN];
    __u8 recv_buf[RECV_BUF_LEN];
    __u16 id  = (__u16)getpid();
    __u16 seq = 0;
    int count = 4;
    struct timeval timeout = { .tv_sec = 1, .tv_usec = 0 };
    int sent = 0, recv = 0;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <host> [count]\n", argv[0]);
        return 1;
    }
    if (argc >= 3)
        count = atoi(argv[2]);

    /* ── Resolve destination ── */
    he = gethostbyname(argv[1]);
    if (!he) {
        fprintf(stderr, "Cannot resolve %s\n", argv[1]);
        return 1;
    }
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    memcpy(&dest.sin_addr, he->h_addr_list[0], he->h_length);

    printf("PING %s (%s): %d data bytes\n",
           argv[1], inet_ntoa(dest.sin_addr), ICMP_DATA_LEN);

    /* ── Create raw socket ──
     * SOCK_RAW + IPPROTO_ICMP: kernel provides IP header in recv,
     * we build only ICMP. Requires CAP_NET_RAW (or root).
     *
     * Alternative (Linux v3.11+, no root needed):
     *   sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_ICMP);
     *   (net/ipv4/ping.c)
     */
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
    if (sockfd < 0) {
        perror("socket(SOCK_RAW, IPPROTO_ICMP)");
        return 1;
    }

    /* Set receive timeout to 1 second */
    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO,
               &timeout, sizeof(timeout));

    /* ── Send/Receive loop ── */
    for (int i = 0; i < count; i++) {
        ssize_t nsent, nrecv;
        double rtt = 0.0;
        struct sockaddr_in from;
        socklen_t fromlen = sizeof(from);
        int found = 0;

        seq++;
        icmp_build_echo(send_buf, id, seq);

        nsent = sendto(sockfd, send_buf, sizeof(send_buf), 0,
                       (struct sockaddr *)&dest, sizeof(dest));
        if (nsent < 0) {
            perror("sendto");
            continue;
        }
        sent++;

        /* Receive loop: discard packets not meant for us */
        do {
            nrecv = recvfrom(sockfd, recv_buf, sizeof(recv_buf), 0,
                             (struct sockaddr *)&from, &fromlen);
            if (nrecv < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK)
                    printf("Request timeout for icmp_seq %u\n", seq);
                else
                    perror("recvfrom");
                break;
            }
            if (icmp_parse_reply(recv_buf, nrecv, id, seq, &rtt) == 0) {
                found = 1;
                recv++;
                printf("%zd bytes from %s: icmp_seq=%u ttl=%u time=%.3f ms\n",
                       nrecv - 20,
                       inet_ntoa(from.sin_addr),
                       seq,
                       ((struct iphdr *)recv_buf)->ttl,
                       rtt);
            }
        } while (!found);

        if (i < count - 1)
            sleep(1);
    }

    close(sockfd);

    printf("\n--- %s ping statistics ---\n", argv[1]);
    printf("%d packets transmitted, %d received, %d%% packet loss\n",
           sent, recv, sent ? (sent - recv) * 100 / sent : 0);

    return (recv == sent) ? 0 : 1;
}
```

### 15.2 ICMPv4 Traceroute — Raw Socket

```c
/*
 * icmp_traceroute.c — UDP/ICMP-based traceroute
 * Sends UDP probes with incrementing TTL, listens for ICMP Time Exceeded.
 * Build: gcc -O2 -Wall -o icmp_traceroute icmp_traceroute.c
 * Run:   sudo ./icmp_traceroute 8.8.8.8
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <netdb.h>

#define MAX_TTL         30
#define PROBES_PER_TTL   3
#define BASE_UDP_PORT   33434   /* traceroute convention */
#define PROBE_DATA_LEN  32

static __u16 checksum_simple(const void *buf, int len)
{
    const __u16 *p = buf;
    __u32 sum = 0;
    while (len > 1) { sum += *p++; len -= 2; }
    if (len) sum += *(__u8 *)p;
    while (sum >> 16) sum = (sum & 0xffff) + (sum >> 16);
    return (__u16)~sum;
}

int main(int argc, char **argv)
{
    int send_sock, recv_sock;
    struct sockaddr_in dest, from;
    socklen_t fromlen;
    struct hostent *he;
    __u8 send_buf[sizeof(struct iphdr) + sizeof(struct udphdr) + PROBE_DATA_LEN];
    __u8 recv_buf[512];
    struct iphdr  *iph  = (struct iphdr *)send_buf;
    struct udphdr *udph = (struct udphdr *)(send_buf + sizeof(struct iphdr));
    struct timeval tv_send, tv_recv, timeout = {1, 0};
    int done = 0;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <host>\n", argv[0]);
        return 1;
    }

    he = gethostbyname(argv[1]);
    if (!he) { perror("gethostbyname"); return 1; }

    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    memcpy(&dest.sin_addr, he->h_addr_list[0], he->h_length);

    /* Raw socket for sending (IP_HDRINCL: we build the IP header) */
    send_sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (send_sock < 0) { perror("send socket"); return 1; }
    {
        int on = 1;
        setsockopt(send_sock, IPPROTO_IP, IP_HDRINCL, &on, sizeof(on));
    }

    /* Raw socket for receiving ICMP Time Exceeded */
    recv_sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
    if (recv_sock < 0) { perror("recv socket"); return 1; }
    setsockopt(recv_sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    printf("traceroute to %s (%s), %d hops max, %d byte packets\n",
           argv[1], inet_ntoa(dest.sin_addr), MAX_TTL,
           (int)(sizeof(struct udphdr) + PROBE_DATA_LEN));

    for (int ttl = 1; ttl <= MAX_TTL && !done; ttl++) {
        struct in_addr last_hop = {0};
        int got_reply = 0;

        printf("%2d  ", ttl);

        for (int probe = 0; probe < PROBES_PER_TTL; probe++) {
            __u16 sport = 40000 + ttl * PROBES_PER_TTL + probe;
            __u16 dport = BASE_UDP_PORT + ttl * PROBES_PER_TTL + probe;
            ssize_t nrecv;

            /* ── Build IP header ── */
            memset(iph, 0, sizeof(*iph));
            iph->ihl      = 5;
            iph->version  = 4;
            iph->tos      = 0;
            iph->tot_len  = htons(sizeof(send_buf));
            iph->id       = htons((__u16)(ttl * 100 + probe));
            iph->frag_off = htons(IP_DF);
            iph->ttl      = ttl;
            iph->protocol = IPPROTO_UDP;
            iph->saddr    = 0;  /* kernel fills this */
            iph->daddr    = dest.sin_addr.s_addr;
            iph->check    = checksum_simple(iph, sizeof(*iph));

            /* ── Build UDP header ── */
            udph->source = htons(sport);
            udph->dest   = htons(dport);
            udph->len    = htons(sizeof(struct udphdr) + PROBE_DATA_LEN);
            udph->check  = 0;   /* optional for UDP/IPv4 */

            /* ── Send probe ── */
            gettimeofday(&tv_send, NULL);
            sendto(send_sock, send_buf, sizeof(send_buf), 0,
                   (struct sockaddr *)&dest, sizeof(dest));

            /* ── Wait for ICMP response ── */
            fromlen = sizeof(from);
            nrecv = recvfrom(recv_sock, recv_buf, sizeof(recv_buf), 0,
                             (struct sockaddr *)&from, &fromlen);

            if (nrecv < 0) {
                printf(" *");
            } else {
                struct iphdr  *r_iph  = (struct iphdr *)recv_buf;
                struct icmphdr *r_icmph = (struct icmphdr *)
                                         (recv_buf + r_iph->ihl * 4);
                gettimeofday(&tv_recv, NULL);
                double rtt = (tv_recv.tv_sec  - tv_send.tv_sec)  * 1000.0
                           + (tv_recv.tv_usec - tv_send.tv_usec) / 1000.0;

                if (r_icmph->type == ICMP_TIME_EXCEEDED) {
                    last_hop = from.sin_addr;
                    got_reply = 1;
                    printf(" %.3f ms", rtt);
                } else if (r_icmph->type == ICMP_DEST_UNREACH) {
                    /* UDP port unreachable = we reached destination */
                    last_hop = from.sin_addr;
                    got_reply = 1;
                    done = 1;
                    printf(" %.3f ms", rtt);
                }
            }
        }

        if (got_reply) {
            char hostname[256] = {0};
            struct hostent *h = gethostbyaddr(&last_hop, sizeof(last_hop), AF_INET);
            if (h) strncpy(hostname, h->h_name, sizeof(hostname)-1);
            printf("  %s (%s)\n",
                   hostname[0] ? hostname : inet_ntoa(last_hop),
                   inet_ntoa(last_hop));
        } else {
            printf("\n");
        }
    }

    close(send_sock);
    close(recv_sock);
    return 0;
}
```

### 15.3 ICMPv6 Raw Socket Ping

```c
/*
 * icmpv6_ping.c — ICMPv6 Echo Request using raw socket
 * Build: gcc -O2 -Wall -o icmpv6_ping icmpv6_ping.c
 * Run:   sudo ./icmpv6_ping ::1
 *
 * Key differences from ICMPv4:
 *   - AF_INET6, IPPROTO_ICMPV6
 *   - Checksum includes IPv6 pseudo-header (kernel computes if IPV6_CHECKSUM)
 *   - Type 128 (Echo Request) / Type 129 (Echo Reply)
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netinet/icmp6.h>
#include <arpa/inet.h>
#include <netdb.h>

#define ICMPV6_DATA_LEN  56

int main(int argc, char **argv)
{
    int sockfd;
    struct sockaddr_in6 dest;
    struct addrinfo hints = {0}, *res;
    __u8 send_buf[sizeof(struct icmp6_hdr) + ICMPV6_DATA_LEN];
    __u8 recv_buf[1500];
    struct icmp6_hdr *hdr = (struct icmp6_hdr *)send_buf;
    __u16 id  = (__u16)getpid();
    __u16 seq = 0;
    struct timeval timeout = {1, 0};
    /* Filter: only receive ICMPv6 Echo Reply (Type 129) */
    struct icmp6_filter filter;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <ipv6_host>\n", argv[0]);
        return 1;
    }

    hints.ai_family   = AF_INET6;
    hints.ai_socktype = SOCK_RAW;
    hints.ai_protocol = IPPROTO_ICMPV6;

    if (getaddrinfo(argv[1], NULL, &hints, &res) != 0) {
        fprintf(stderr, "Cannot resolve %s\n", argv[1]);
        return 1;
    }
    memcpy(&dest, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);

    sockfd = socket(AF_INET6, SOCK_RAW, IPPROTO_ICMPV6);
    if (sockfd < 0) { perror("socket"); return 1; }

    /* ICMPv6 filter: only pass Echo Reply to userspace */
    ICMP6_FILTER_SETBLOCKALL(&filter);
    ICMP6_FILTER_SETPASS(ICMP6_ECHO_REPLY, &filter);
    setsockopt(sockfd, IPPROTO_ICMPV6, ICMP6_FILTER,
               &filter, sizeof(filter));

    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    /*
     * For ICMPv6 raw sockets, the kernel automatically computes the
     * checksum using the IPv6 pseudo-header if we set IPV6_CHECKSUM.
     * The value (2) is the offset of the checksum field in the ICMPv6 header.
     */
    {
        int offset = 2;
        setsockopt(sockfd, IPPROTO_IPV6, IPV6_CHECKSUM,
                   &offset, sizeof(offset));
    }

    {
        char addr_str[INET6_ADDRSTRLEN];
        inet_ntop(AF_INET6, &dest.sin6_addr, addr_str, sizeof(addr_str));
        printf("PING6 %s (%s): %d data bytes\n",
               argv[1], addr_str, ICMPV6_DATA_LEN);
    }

    for (int i = 0; i < 4; i++) {
        ssize_t n;
        struct sockaddr_in6 from;
        socklen_t fromlen = sizeof(from);
        struct timeval tv_send, tv_recv;
        double rtt;

        seq++;

        /* ── Build ICMPv6 Echo Request (Type 128) ── */
        memset(hdr, 0, sizeof(*hdr));
        hdr->icmp6_type  = ICMP6_ECHO_REQUEST;   /* 128 */
        hdr->icmp6_code  = 0;
        hdr->icmp6_id    = htons(id);
        hdr->icmp6_seq   = htons(seq);
        gettimeofday((struct timeval *)(send_buf + sizeof(*hdr)), NULL);
        /* checksum = 0; kernel fills in (IPV6_CHECKSUM socket option) */

        gettimeofday(&tv_send, NULL);
        sendto(sockfd, send_buf, sizeof(send_buf), 0,
               (struct sockaddr *)&dest, sizeof(dest));

        n = recvfrom(sockfd, recv_buf, sizeof(recv_buf), 0,
                     (struct sockaddr *)&from, &fromlen);

        if (n < 0) {
            printf("Request timeout for icmp6_seq %u\n", seq);
        } else {
            struct icmp6_hdr *r = (struct icmp6_hdr *)recv_buf;
            char src_str[INET6_ADDRSTRLEN];
            gettimeofday(&tv_recv, NULL);
            rtt = (tv_recv.tv_sec  - tv_send.tv_sec)  * 1000.0 +
                  (tv_recv.tv_usec - tv_send.tv_usec) / 1000.0;
            if (r->icmp6_type == ICMP6_ECHO_REPLY &&
                ntohs(r->icmp6_id) == id) {
                inet_ntop(AF_INET6, &from.sin6_addr,
                          src_str, sizeof(src_str));
                printf("%zd bytes from %s: icmp6_seq=%u time=%.3f ms\n",
                       n, src_str, seq, rtt);
            }
        }
        if (i < 3) sleep(1);
    }

    close(sockfd);
    return 0;
}
```

---

## 16. Rust Implementation

### 16.1 Dependencies (Cargo.toml)

```toml
[package]
name = "icmp-ping"
version = "0.1.0"
edition = "2021"

[dependencies]
# socket2: portable socket API with raw socket support
socket2 = { version = "0.5", features = ["all"] }
# No std-net for raw sockets — use libc directly
libc = "0.2"

[[bin]]
name = "icmp_ping"
path = "src/main.rs"
```

### 16.2 Complete Rust ICMPv4 Ping

```rust
//! icmp_ping — ICMPv4 Echo using raw sockets in Rust
//! Requires: sudo or CAP_NET_RAW capability
//!
//! Design: no async, no tokio — mimics kernel coding style with
//! explicit error handling and zero unnecessary allocations.

use std::net::{Ipv4Addr, SocketAddrV4};
use std::os::unix::io::AsRawFd;
use std::time::{Duration, Instant};
use std::io;

/// ICMP message types (RFC 792)
#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum IcmpType {
    EchoReply   = 0,
    EchoRequest = 8,
}

/// Minimal ICMP Echo header layout
///
/// Wire format (big-endian):
///   [0]    type
///   [1]    code
///   [2-3]  checksum (one's complement of entire ICMP message)
///   [4-5]  identifier
///   [6-7]  sequence number
#[repr(C, packed)]
#[derive(Debug, Clone, Copy)]
pub struct IcmpEchoHdr {
    pub icmp_type:  u8,
    pub code:       u8,
    pub checksum:   u16,    /* network byte order */
    pub identifier: u16,    /* network byte order */
    pub sequence:   u16,    /* network byte order */
}

impl IcmpEchoHdr {
    pub fn new_request(id: u16, seq: u16) -> Self {
        IcmpEchoHdr {
            icmp_type:  IcmpType::EchoRequest as u8,
            code:       0,
            checksum:   0,
            identifier: id.to_be(),
            sequence:   seq.to_be(),
        }
    }
}

/// One's complement checksum (RFC 1071)
///
/// Same algorithm as used in ip_fast_csum() and icmp_checksum()
/// in the kernel.
pub fn ones_complement_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;

    // Sum 16-bit words
    while i + 1 < data.len() {
        let word = u16::from_be_bytes([data[i], data[i + 1]]) as u32;
        sum = sum.wrapping_add(word);
        i += 2;
    }

    // If odd number of bytes, pad last byte
    if i < data.len() {
        sum = sum.wrapping_add((data[i] as u32) << 8);
    }

    // Fold 32-bit sum to 16 bits (handle carry)
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    !(sum as u16)
}

/// Build complete ICMP Echo Request packet
fn build_icmp_echo(id: u16, seq: u16, timestamp_ns: u64) -> Vec<u8> {
    const PAYLOAD_LEN: usize = 48; // 8 bytes timestamp + 40 bytes padding

    let mut packet = vec![0u8; 8 + PAYLOAD_LEN]; // ICMP hdr + payload

    // Header fields
    packet[0] = IcmpType::EchoRequest as u8;
    packet[1] = 0;                              // code
    packet[2] = 0;                              // checksum (filled later)
    packet[3] = 0;
    packet[4] = (id >> 8) as u8;               // identifier BE
    packet[5] = (id & 0xFF) as u8;
    packet[6] = (seq >> 8) as u8;              // sequence BE
    packet[7] = (seq & 0xFF) as u8;

    // Payload: 8-byte timestamp (nanoseconds since boot)
    let ts_bytes = timestamp_ns.to_be_bytes();
    packet[8..16].copy_from_slice(&ts_bytes);

    // Fill remaining payload with pattern (0xAB like ping)
    for b in &mut packet[16..] {
        *b = 0xAB;
    }

    // Compute and insert checksum
    let csum = ones_complement_checksum(&packet);
    packet[2] = (csum >> 8) as u8;
    packet[3] = (csum & 0xFF) as u8;

    packet
}

/// Parse ICMP Echo Reply from raw socket receive buffer
/// raw socket for IPPROTO_ICMP delivers: IP header + ICMP message
fn parse_echo_reply(buf: &[u8], expected_id: u16, expected_seq: u16)
    -> Option<u64>  /* returns timestamp from payload */
{
    if buf.len() < 28 { return None; }  // 20 IP + 8 ICMP minimum

    // IP header length (IHL field, bits [0:3] of first byte, in 32-bit words)
    let ihl = ((buf[0] & 0x0F) as usize) * 4;
    if buf.len() < ihl + 8 { return None; }

    let icmp = &buf[ihl..];

    // Type must be ICMP Echo Reply (0)
    if icmp[0] != IcmpType::EchoReply as u8 { return None; }

    // Identifier must match
    let id = u16::from_be_bytes([icmp[4], icmp[5]]);
    if id != expected_id { return None; }

    // Sequence must match
    let seq = u16::from_be_bytes([icmp[6], icmp[7]]);
    if seq != expected_seq { return None; }

    // Extract timestamp from payload
    if icmp.len() < 16 { return None; }
    let ts = u64::from_be_bytes(icmp[8..16].try_into().ok()?);

    Some(ts)
}

/// Raw ICMP socket wrapper
pub struct RawIcmpSocket {
    fd: i32,
}

impl RawIcmpSocket {
    /// Create AF_INET SOCK_RAW IPPROTO_ICMP socket
    pub fn new() -> io::Result<Self> {
        let fd = unsafe {
            libc::socket(
                libc::AF_INET,
                libc::SOCK_RAW,
                libc::IPPROTO_ICMP,
            )
        };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(RawIcmpSocket { fd })
    }

    pub fn set_recv_timeout(&self, timeout: Duration) -> io::Result<()> {
        let tv = libc::timeval {
            tv_sec:  timeout.as_secs() as libc::time_t,
            tv_usec: timeout.subsec_micros() as libc::suseconds_t,
        };
        let ret = unsafe {
            libc::setsockopt(
                self.fd,
                libc::SOL_SOCKET,
                libc::SO_RCVTIMEO,
                &tv as *const _ as *const libc::c_void,
                std::mem::size_of::<libc::timeval>() as libc::socklen_t,
            )
        };
        if ret < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }

    pub fn send_to(&self, buf: &[u8], dst: Ipv4Addr) -> io::Result<usize> {
        let addr = libc::sockaddr_in {
            sin_family: libc::AF_INET as u16,
            sin_port:   0,
            sin_addr:   libc::in_addr {
                s_addr: u32::from(dst).to_be(),
            },
            sin_zero:   [0u8; 8],
        };
        let n = unsafe {
            libc::sendto(
                self.fd,
                buf.as_ptr() as *const libc::c_void,
                buf.len(),
                0,
                &addr as *const _ as *const libc::sockaddr,
                std::mem::size_of::<libc::sockaddr_in>() as libc::socklen_t,
            )
        };
        if n < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(n as usize)
    }

    pub fn recv(&self, buf: &mut [u8]) -> io::Result<(usize, Ipv4Addr)> {
        let mut from: libc::sockaddr_in = unsafe { std::mem::zeroed() };
        let mut fromlen = std::mem::size_of::<libc::sockaddr_in>() as libc::socklen_t;
        let n = unsafe {
            libc::recvfrom(
                self.fd,
                buf.as_mut_ptr() as *mut libc::c_void,
                buf.len(),
                0,
                &mut from as *mut _ as *mut libc::sockaddr,
                &mut fromlen,
            )
        };
        if n < 0 {
            return Err(io::Error::last_os_error());
        }
        let src = Ipv4Addr::from(u32::from_be(from.sin_addr.s_addr));
        Ok((n as usize, src))
    }
}

impl Drop for RawIcmpSocket {
    fn drop(&mut self) {
        unsafe { libc::close(self.fd); }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <ipv4_address>", args[0]);
        std::process::exit(1);
    }

    let dest: Ipv4Addr = args[1].parse().unwrap_or_else(|_| {
        // Simple hostname resolution fallback
        eprintln!("Invalid IPv4 address: {}", args[1]);
        std::process::exit(1);
    });

    let id  = std::process::id() as u16;
    let count = 4u16;

    println!("PING {} ({}) 56 data bytes", args[1], dest);

    let sock = RawIcmpSocket::new().expect("Cannot create raw socket (need CAP_NET_RAW)");
    sock.set_recv_timeout(Duration::from_secs(1)).expect("setsockopt failed");

    let mut sent = 0u32;
    let mut received = 0u32;

    for seq in 1..=count {
        let now = Instant::now();
        // Use monotonic clock nanoseconds as payload timestamp
        let ts_ns = {
            let mut ts: libc::timespec = unsafe { std::mem::zeroed() };
            unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts); }
            ts.tv_sec as u64 * 1_000_000_000 + ts.tv_nsec as u64
        };

        let packet = build_icmp_echo(id, seq, ts_ns);

        match sock.send_to(&packet, dest) {
            Ok(_) => sent += 1,
            Err(e) => { eprintln!("sendto error: {}", e); continue; }
        }

        let mut recv_buf = [0u8; 1500];
        let mut found = false;

        loop {
            match sock.recv(&mut recv_buf) {
                Ok((n, src)) => {
                    if let Some(sent_ts) = parse_echo_reply(&recv_buf[..n], id, seq) {
                        // RTT from monotonic clock
                        let now_ns = {
                            let mut ts: libc::timespec = unsafe { std::mem::zeroed() };
                            unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts); }
                            ts.tv_sec as u64 * 1_000_000_000 + ts.tv_nsec as u64
                        };
                        let rtt_ms = (now_ns.saturating_sub(sent_ts)) as f64 / 1_000_000.0;

                        // TTL is at byte 8 of the IP header
                        let ttl = recv_buf[8];
                        println!(
                            "64 bytes from {}: icmp_seq={} ttl={} time={:.3} ms",
                            src, seq, ttl, rtt_ms
                        );
                        received += 1;
                        found = true;
                        break;
                    }
                    // Not our packet; keep waiting
                }
                Err(e) if e.kind() == io::ErrorKind::WouldBlock => {
                    println!("Request timeout for icmp_seq {}", seq);
                    break;
                }
                Err(e) => {
                    eprintln!("recvfrom error: {}", e);
                    break;
                }
            }
        }

        if seq < count {
            std::thread::sleep(Duration::from_secs(1));
        }
    }

    println!();
    println!("--- {} ping statistics ---", args[1]);
    let loss = if sent > 0 { (sent - received) * 100 / sent } else { 0 };
    println!("{} packets transmitted, {} received, {}% packet loss",
             sent, received, loss);
}
```

### 16.3 Rust ICMP Checksum Verification (Unit Tests)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Verify checksum against known ICMP Echo packet bytes
    /// Captured: ping 127.0.0.1, first echo request
    #[test]
    fn test_icmp_checksum_echo_request() {
        // ICMP Echo Request with checksum=0 field
        // type=8, code=0, id=0x1234, seq=1, payload=0xAB * 56
        let mut pkt = vec![0u8; 64];
        pkt[0] = 8;      // type = Echo Request
        pkt[1] = 0;      // code
        pkt[2] = 0;      // checksum MSB (zero for computation)
        pkt[3] = 0;      // checksum LSB
        pkt[4] = 0x12;   // id MSB
        pkt[5] = 0x34;   // id LSB
        pkt[6] = 0x00;   // seq MSB
        pkt[7] = 0x01;   // seq LSB
        for b in &mut pkt[8..] { *b = 0xAB; }

        let csum = ones_complement_checksum(&pkt);
        // Insert checksum
        pkt[2] = (csum >> 8) as u8;
        pkt[3] = (csum & 0xFF) as u8;

        // Verify: checksum over the complete packet with checksum inserted = 0
        let verify = ones_complement_checksum(&pkt);
        assert_eq!(verify, 0, "ICMP checksum verification failed");
    }

    /// Empty data edge case
    #[test]
    fn test_checksum_empty() {
        let csum = ones_complement_checksum(&[]);
        // sum=0, ~0 = 0xFFFF
        assert_eq!(csum, 0xFFFF);
    }

    /// Single byte (odd length padding)
    #[test]
    fn test_checksum_single_byte() {
        let data = [0x45u8];
        let csum = ones_complement_checksum(&data);
        // sum = 0x4500 (padded), ~0x4500 = 0xBAFF
        assert_eq!(csum, 0xBAFF);
    }

    /// Packet construction test
    #[test]
    fn test_build_echo_request() {
        let pkt = build_icmp_echo(0x1234, 1, 12345678901234u64);
        assert_eq!(pkt.len(), 56);
        assert_eq!(pkt[0], 8);  // Echo Request
        assert_eq!(pkt[1], 0);  // Code 0
        // Verify checksum is correct
        let verify = ones_complement_checksum(&pkt);
        assert_eq!(verify, 0, "Built packet checksum invalid");
        // Verify identifier
        let id = u16::from_be_bytes([pkt[4], pkt[5]]);
        assert_eq!(id, 0x1234);
    }
}
```

---

## 17. Debugging & Tracing with Kernel Tools

### 17.1 ftrace — Trace ICMP Receive Path

```bash
# Trace icmp_rcv and icmp_echo function calls
cd /sys/kernel/debug/tracing

# Enable function tracer
echo function > current_tracer

# Filter to ICMP-related functions
echo 'icmp_*' > set_ftrace_filter
echo 'ping_rcv' >> set_ftrace_filter

# Enable tracing
echo 1 > tracing_on

# Generate some ICMP traffic
ping -c 3 8.8.8.8 &

# Read trace
cat trace

# Sample output:
# ping-12345 [001] .... 12345.678: icmp_rcv <-ip_local_deliver_finish
# ping-12345 [001] .... 12345.679: icmp_echo <-icmp_rcv
# ping-12345 [001] .... 12345.680: icmp_reply <-icmp_echo

# Function graph (shows call depth and timing):
echo function_graph > current_tracer
echo 'icmp_rcv' > set_graph_function
cat trace
# 0)               |  icmp_rcv() {
# 0)               |    icmp_echo() {
# 0)               |      icmp_reply() {
# 0)   2.345 us    |        ip_push_pending_frames();
# 0)   5.678 us    |      }
# 0)   8.901 us    |    }
# 0)  12.345 us    |  }

echo 0 > tracing_on
echo nop > current_tracer
echo > set_ftrace_filter
```

### 17.2 perf — ICMP Performance Analysis

```bash
# Count ICMP-related events
perf stat -e 'net:icmp_send,net:icmp_receive' ping -c 100 8.8.8.8

# Record ICMP processing call stack
perf record -g -e 'net:icmp_send' -- ping -c 10 8.8.8.8
perf report --stdio

# Trace ICMP with hardware PMU counters
perf record -e cycles:pp -g -F 99 \
    --filter 'ip >= 0xffffffff81000000' \  # kernel only
    -- ping -c 100 -i 0.001 8.8.8.8

# Check rate limiting drops
perf stat -e 'net:net_dev_xmit_timeout' -- sleep 10
# Or watch /proc/net/snmp:
watch -n1 'grep -i icmp /proc/net/snmp'
```

### 17.3 bpftrace — Dynamic ICMP Tracing

```bash
# Trace all ICMP messages with type/code
bpftrace -e '
kprobe:icmp_rcv {
    $skb = (struct sk_buff *)arg0;
    $icmph = (struct icmphdr *)($skb->head + $skb->transport_header);
    printf("ICMP RX: type=%d code=%d from cpu=%d\n",
           $icmph->type, $icmph->code, cpu);
}
'

# Measure ICMP echo round-trip latency (kernel perspective)
bpftrace -e '
kprobe:icmp_echo { @start[tid] = nsecs; }
kretprobe:icmp_echo /@start[tid]/ {
    $delta = nsecs - @start[tid];
    @icmp_echo_ns = hist($delta);
    delete(@start[tid]);
}
END { print(@icmp_echo_ns); }
'

# Detect ICMP rate limiting (icmpv4_xrlim_allow returns false)
bpftrace -e '
kretprobe:icmpv4_xrlim_allow {
    if (retval == 0) {
        @rate_limited = count();
    }
}
interval:s:1 {
    printf("ICMP rate-limited: %llu/sec\n", @rate_limited);
    clear(@rate_limited);
}
'

# Track ICMP errors sent by type
bpftrace -e '
kprobe:icmp_send {
    @by_type[arg1] = count();   /* arg1 = type */
}
interval:s:5 {
    print(@by_type);
    clear(@by_type);
}
'
```

### 17.4 eBPF Program — ICMP Statistics (BPF_PROG_TYPE_SOCKET_FILTER)

```c
/* icmp_stats.bpf.c — Count ICMP types using socket filter */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 256);        /* one entry per ICMP type */
    __type(key, __u32);
    __type(value, __u64);
} icmp_type_count SEC(".maps");

SEC("socket")
int icmp_filter(struct __sk_buff *skb)
{
    struct ethhdr eth;
    struct iphdr  iph;
    struct icmphdr icmph;
    __u32 type;
    __u64 *cnt;

    /* Load Ethernet header */
    if (bpf_skb_load_bytes(skb, 0, &eth, sizeof(eth)) < 0)
        return 0;

    if (bpf_ntohs(eth.h_proto) != ETH_P_IP)
        return 0;

    /* Load IP header */
    if (bpf_skb_load_bytes(skb, ETH_HLEN, &iph, sizeof(iph)) < 0)
        return 0;

    if (iph.protocol != IPPROTO_ICMP)
        return 0;

    /* Load ICMP header */
    __u32 ip_hlen = iph.ihl * 4;
    if (bpf_skb_load_bytes(skb, ETH_HLEN + ip_hlen,
                            &icmph, sizeof(icmph)) < 0)
        return 0;

    type = icmph.type;
    cnt = bpf_map_lookup_elem(&icmp_type_count, &type);
    if (cnt)
        __sync_fetch_and_add(cnt, 1);

    return 0;    /* pass all packets (socket filter) */
}

char LICENSE[] SEC("license") = "GPL";
```

### 17.5 Wireshark / tcpdump ICMP Filters

```bash
# tcpdump ICMP capture
tcpdump -i eth0 -nn -v 'icmp'
tcpdump -i eth0 -nn 'icmp[icmptype] == icmp-echo'
tcpdump -i eth0 -nn 'icmp[icmptype] == icmp-echoreply'
tcpdump -i eth0 -nn 'icmp[icmptype] == icmp-unreach'
tcpdump -i eth0 -nn 'icmp[icmptype] == icmp-timxceed'

# ICMP fragmentation needed (Type 3, Code 4)
tcpdump -i eth0 -nn 'icmp[icmptype] == 3 and icmp[icmpcode] == 4'

# ICMPv6
tcpdump -i eth0 -nn 'icmp6'
tcpdump -i eth0 -nn 'icmp6[icmp6type] == 128'  # Echo Request
tcpdump -i eth0 -nn 'icmp6[icmp6type] == 135'  # Neighbor Solicitation

# Verbose ICMP with hex dump of payload
tcpdump -i eth0 -nn -X 'icmp'

# Write to pcap for offline analysis
tcpdump -i eth0 -w /tmp/icmp.pcap 'icmp or icmp6'
```

### 17.6 /proc/net/snmp — ICMP Statistics

```bash
cat /proc/net/snmp | grep -i icmp

# Output format:
# Icmp: InMsgs InErrors InCsumErrors InDestUnreachs InTimeExcds ...
# Icmp: 1234   0        0            500            200         ...

# Decode the stats:
awk '/^Icmp:/ {
    if (NR % 2 == 0) {
        split(headers, h); split($0, v);
        for (i=2; i<=length(h); i++) printf "%s = %s\n", h[i], v[i];
    } else {
        headers = $0;
    }
}' /proc/net/snmp

# Watch ICMP rate limiting (OutRateLimitGlobal added in Linux v5.3):
watch -n1 "awk '/^Icmp:/{if(h){split(h,k); split(\$0,v); \
    for(i=2;i<=NF;i++) printf k[i]\" = \"v[i]\"\\n\"} else h=\$0}' \
    /proc/net/snmp | grep -i ratelimit"
```

---

## 18. sysctl Tunables & /proc Interface

### 18.1 Complete ICMP sysctl Reference

```
/proc/sys/net/ipv4/

icmp_echo_ignore_all         (default: 0)
    0 = respond to echo requests
    1 = silently ignore all ICMP echo requests
    Note: does NOT affect ICMP echo replies or errors

icmp_echo_ignore_broadcasts  (default: 1)
    0 = respond to broadcasts/multicast echo requests (Smurf risk!)
    1 = ignore echo requests to broadcast/multicast addresses

icmp_ignore_bogus_error_responses (default: 1)
    Some hosts send ICMP errors in response to broadcasts.
    0 = log these to syslog
    1 = silently ignore

icmp_ratelimit               (default: 1000)
    Limit of ICMP error messages per second (token bucket rate).
    Unit: microseconds between tokens (1000 = 1 per ms = 1000/sec)
    0   = unlimited (dangerous)
    100 = 10,000/sec

icmp_ratemask                (default: 0x1818)
    Bitmask of ICMP types subject to ratelimiting.
    bit N = type N is rate-limited.
    0x1818 = bits 3,4,11,12 = Dest Unreach, Source Quench, Time Exceeded, Param Prob

icmp_errors_use_inbound_ifaddr (default: 0)
    0 = use primary address of outgoing interface as ICMP source
    1 = use address of interface on which triggering packet arrived
    (Useful for multi-homed hosts where you want ICMP from same IF)

/proc/sys/net/ipv4/conf/<iface>/

accept_redirects             (default: 1 for hosts, 0 for routers)
    0 = ignore ICMP redirects
    1 = accept ICMP redirects (update route cache)

secure_redirects             (default: 1)
    0 = accept redirects from any host
    1 = only accept from current gateway (RFC 2827 compliant)

send_redirects               (default: 1)
    0 = do not send ICMP redirects
    1 = send ICMP redirects when forwarding

/proc/sys/net/ipv6/

icmp_echo_ignore_all         (default: 0)
icmp_echo_ignore_multicast   (default: 0)
icmp_ratelimit               (default: 1000)
icmp_ratemask                (default: 0x0000)   # ICMPv6 uses different mask
```

### 18.2 Kernel Compile-Time Limits

```c
/* include/linux/icmp.h */
#define ICMP_FILTER     1           /* socket option: ICMPv4 filter */

/* net/ipv4/icmp.c */
#define IP_MAX_MTU      0xFFF0      /* max ICMP Frag Needed MTU */

/* net/ipv4/route.c */
#define IP_RT_MIN_PMTU  552         /* minimum PMTU accepted (bytes) */
#define IP_RT_MIN_ADVMSS 256        /* minimum advertised MSS */
```

### 18.3 /proc/net Files

```bash
# ICMP/SNMP stats (RFC 1213 MIB-II format)
/proc/net/snmp          — IPv4 ICMP stats (InMsgs, OutMsgs, InErrors, ...)
/proc/net/snmp6         — IPv6 ICMPv6 stats
/proc/net/netstat       — Extended stats including TCP/ICMP

# Per-socket raw ICMP sockets
/proc/net/raw           — shows open raw sockets (IPPROTO_ICMP)
/proc/net/icmp          — (same as raw for ICMP)
/proc/net/icmp6         — ICMPv6 sockets

# Ping sockets (SOCK_DGRAM ICMP, no root needed)
/proc/net/ping          — shows ICMP ping sockets (since Linux 3.11)

# Example /proc/net/raw entry:
#   sl  local_address rem_address   st tx_queue rx_queue ... uid inode
#   0:  00000000:0000 00000000:0000 07 00000000:00000000 ...   0  12345
#   ^                                ^
#   socket slot                      state 7 = listening (raw)
```

---

## 19. eBPF / XDP ICMP Filtering

### 19.1 XDP ICMP Rate Limiter

```c
/* xdp_icmp_ratelimit.bpf.c
 * Drop ICMP Echo Requests exceeding rate_limit pps per source IP.
 * Load with: ip link set dev eth0 xdpdrv obj xdp_icmp_ratelimit.bpf.o
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define RATE_LIMIT_PPS  100   /* max 100 ICMP echo req/sec per source */
#define WINDOW_NS       1000000000ULL  /* 1 second in nanoseconds */

struct rate_entry {
    __u64 timestamp;    /* window start time */
    __u64 count;        /* packets in current window */
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, __u32);             /* source IPv4 address */
    __type(value, struct rate_entry);
} icmp_rate_map SEC(".maps");

SEC("xdp")
int xdp_icmp_ratelimit(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    if (iph->protocol != IPPROTO_ICMP)
        return XDP_PASS;

    /* Calculate IP header length */
    if (iph->ihl < 5)
        return XDP_PASS;
    __u32 iph_len = iph->ihl * 4;

    struct icmphdr *icmph = (void *)iph + iph_len;
    if ((void *)(icmph + 1) > data_end)
        return XDP_PASS;

    /* Only rate-limit Echo Requests */
    if (icmph->type != ICMP_ECHO)
        return XDP_PASS;

    __u32 src_ip = iph->saddr;
    __u64 now    = bpf_ktime_get_ns();

    struct rate_entry *entry = bpf_map_lookup_elem(&icmp_rate_map, &src_ip);
    if (!entry) {
        /* First packet from this source */
        struct rate_entry new_entry = {
            .timestamp = now,
            .count     = 1,
        };
        bpf_map_update_elem(&icmp_rate_map, &src_ip, &new_entry, BPF_ANY);
        return XDP_PASS;
    }

    /* Reset window if expired */
    if (now - entry->timestamp > WINDOW_NS) {
        entry->timestamp = now;
        entry->count     = 1;
        return XDP_PASS;
    }

    /* Check rate */
    entry->count++;
    if (entry->count > RATE_LIMIT_PPS) {
        return XDP_DROP;    /* Rate exceeded — drop at NIC level */
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

### 19.2 tc/BPF ICMP Redirect Detector

```c
/* tc_icmp_redirect_detect.bpf.c
 * Detect ICMP Redirect messages and alert via perf ring buffer.
 * Load: tc filter add dev eth0 ingress bpf obj tc_icmp_redirect_detect.bpf.o
 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <bpf/bpf_helpers.h>

struct redirect_event {
    __u32 src;          /* router sending redirect */
    __u32 new_gw;       /* suggested new gateway */
    __u32 orig_dst;     /* original destination */
    __u8  code;         /* redirect code 0-3 */
    __u8  pad[3];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(int));
} redirect_events SEC(".maps");

SEC("tc")
int detect_icmp_redirect(struct __sk_buff *skb)
{
    struct ethhdr eth;
    struct iphdr  iph;
    struct icmphdr icmph;
    __u32 offset = 0;

    if (bpf_skb_load_bytes(skb, offset, &eth, sizeof(eth)) < 0)
        return TC_ACT_OK;
    offset += sizeof(eth);

    if (bpf_ntohs(eth.h_proto) != ETH_P_IP)
        return TC_ACT_OK;

    if (bpf_skb_load_bytes(skb, offset, &iph, sizeof(iph)) < 0)
        return TC_ACT_OK;

    if (iph.protocol != IPPROTO_ICMP)
        return TC_ACT_OK;

    offset += iph.ihl * 4;
    if (bpf_skb_load_bytes(skb, offset, &icmph, sizeof(icmph)) < 0)
        return TC_ACT_OK;

    if (icmph.type != ICMP_REDIRECT)
        return TC_ACT_OK;

    /* Suspicious: log redirect event to userspace */
    struct redirect_event ev = {
        .src    = iph.saddr,
        .new_gw = icmph.un.gateway,
        .code   = icmph.code,
    };

    /* Extract original destination from embedded IP header */
    __u32 inner_offset = offset + sizeof(icmph);
    struct iphdr inner;
    if (bpf_skb_load_bytes(skb, inner_offset, &inner, sizeof(inner)) == 0)
        ev.orig_dst = inner.daddr;

    bpf_perf_event_output(skb, &redirect_events,
                          BPF_F_CURRENT_CPU, &ev, sizeof(ev));

    return TC_ACT_OK;   /* pass; let kernel decide whether to accept */
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 20. ICMP in Containers & Namespaces

### 20.1 ICMP and Network Namespaces

Each network namespace has its own:
- ICMP sysctl values (icmp_echo_ignore_all, ratelimit, etc.)
- ICMP MIB counters
- ICMP socket state (ping sockets, raw sockets)

```c
/*
 * When an IP packet is received, net = dev_net(skb->dev) gives the
 * namespace associated with the receiving interface.
 * All ICMP processing happens within that namespace.
 *
 * struct net (include/net/net_namespace.h):
 *   struct netns_ipv4 ipv4;    ← per-namespace IPv4 state
 *
 * struct netns_ipv4 (include/net/netns/ipv4.h):
 *   int sysctl_icmp_echo_ignore_all;
 *   int sysctl_icmp_ratelimit;
 *   struct icmp_mib __percpu *icmp_statistics;
 *   ...
 */
```

### 20.2 ICMP in Docker / Container Networking

```
Docker bridge network (default):
                                   Host Network Namespace
                                  ┌──────────────────────┐
Container A Namespace             │         eth0          │
┌───────────────┐                 │           │           │
│    eth0       │                 │      iptables NAT     │
│  172.17.0.2   │                 │           │           │
│       │       │                 │       docker0         │
│     veth0 ───────────────────── │  veth0a  veth0b ...   │
└───────────────┘                 └──────────────────────┘

ICMP flow for "ping 8.8.8.8" from Container A:
  1. Container sends ICMP Echo in its namespace
  2. Exits via veth pair to host's docker0 bridge
  3. iptables MASQUERADE NATTs src to host's eth0 IP
  4. Host sends ICMP Echo to 8.8.8.8
  5. ICMP Reply arrives at host eth0
  6. iptables DNAT/conntrack restores original src
  7. Packet delivered back to container via veth

icmp_echo_ignore_all inside container:
  sudo ip netns exec <container_ns> \
    sysctl net.ipv4.icmp_echo_ignore_all=1
  (only affects that namespace)
```

### 20.3 ICMP Ping Socket (No Root Required — Linux v3.11+)

```c
/*
 * net/ipv4/ping.c — SOCK_DGRAM + IPPROTO_ICMP
 * Allows unprivileged ping without CAP_NET_RAW.
 *
 * Controlled by: net.ipv4.ping_group_range (default: "1 0" = disabled)
 * Enable for all users: sysctl net.ipv4.ping_group_range="0 2147483647"
 *
 * Difference from SOCK_RAW IPPROTO_ICMP:
 *   - kernel handles IP header (no IP_HDRINCL)
 *   - only ICMP Echo Request/Reply allowed (type 8/0)
 *   - kernel automatically fills identifier from socket
 *   - accessible to unprivileged users in ping_group_range
 */

/* Usage from C */
int fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_ICMP);
/* No setsockopt(IP_HDRINCL) needed */
/* sendto/recvfrom work exactly like UDP */
/* kernel prepends IP header and sets identifier */
```

---

## Appendix A: ICMP Type/Code Quick Reference

```
Type  Code  Symbol                          Meaning
────  ────  ──────────────────────────────  ──────────────────────────────────
0     0     ICMP_ECHOREPLY                  Echo Reply
3     0     ICMP_NET_UNREACH                Destination Net Unreachable
3     1     ICMP_HOST_UNREACH               Destination Host Unreachable
3     2     ICMP_PROT_UNREACH               Destination Protocol Unreachable
3     3     ICMP_PORT_UNREACH               Destination Port Unreachable
3     4     ICMP_FRAG_NEEDED                Fragmentation Needed and DF Set
3     5     ICMP_SR_FAILED                  Source Route Failed
3     6     ICMP_NET_UNKNOWN                Destination Network Unknown
3     7     ICMP_HOST_UNKNOWN               Destination Host Unknown
3     9     ICMP_NET_ANO                    Net Administratively Prohibited
3     10    ICMP_HOST_ANO                   Host Administratively Prohibited
3     11    ICMP_NET_UNR_TOS                Net Unreachable for TOS
3     12    ICMP_HOST_UNR_TOS               Host Unreachable for TOS
3     13    ICMP_PKT_FILTERED               Communication Filtered
3     14    ICMP_PREC_VIOLATION             Precedence Violation
3     15    ICMP_PREC_CUTOFF                Precedence Cutoff
4     0     ICMP_SOURCE_QUENCH              Source Quench (DEPRECATED)
5     0     ICMP_REDIR_NET                  Redirect Net
5     1     ICMP_REDIR_HOST                 Redirect Host
5     2     ICMP_REDIR_NETTOS               Redirect Net for TOS
5     3     ICMP_REDIR_HOSTTOS              Redirect Host for TOS
8     0     ICMP_ECHO                       Echo Request
9     0     ICMP_ROUTERADVERT               Router Advertisement
10    0     ICMP_ROUTERSOLICIT              Router Solicitation
11    0     ICMP_EXC_TTL                    TTL Exceeded in Transit
11    1     ICMP_EXC_FRAGTIME               Fragment Reassembly Time Exceeded
12    0     ICMP_PARAMETERPROB              Bad IP Header (pointer)
12    1     —                               Missing Required Option
12    2     —                               Bad Length
13    0     ICMP_TIMESTAMP                  Timestamp Request
14    0     ICMP_TIMESTAMPREPLY             Timestamp Reply
17    0     ICMP_ADDRESS                    Address Mask Request (deprecated)
18    0     ICMP_ADDRESSREPLY               Address Mask Reply (deprecated)
```

## Appendix B: Kernel Symbol Index

```
Function/Symbol             File                        Purpose
──────────────────────────  ──────────────────────────  ────────────────────────────
icmp_rcv()                  net/ipv4/icmp.c             Main ICMP receive entry
icmp_send()                 net/ipv4/icmp.c             Send ICMP error (exported)
icmp_echo()                 net/ipv4/icmp.c             Handle Echo Request (Type 8)
icmp_reply()                net/ipv4/icmp.c             Send Echo Reply (Type 0)
icmp_unreach()              net/ipv4/icmp.c             Handle Type 3,4,11,12
icmp_redirect()             net/ipv4/icmp.c             Handle Redirect (Type 5)
icmp_timestamp()            net/ipv4/icmp.c             Handle Timestamp (Type 13)
icmpv4_xrlim_allow()        net/ipv4/icmp.c             Rate limiting check
icmp_push_reply()           net/ipv4/icmp.c             Transmit ICMP packet
icmp_global_allow()         net/ipv4/icmp.c             Global token bucket
ping_rcv()                  net/ipv4/ping.c             SOCK_DGRAM ICMP handler
icmpv6_rcv()                net/ipv6/icmp.c             ICMPv6 receive entry
icmpv6_send()               net/ipv6/icmp.c             Send ICMPv6 error
ndisc_rcv()                 net/ipv6/ndisc.c            NDP (NS/NA/RS/RA)
ip_icmp_error()             net/ipv4/udp.c              Deliver ICMP to UDP socket
tcp_v4_err()                net/ipv4/tcp_ipv4.c         ICMP → TCP error delivery
ip_update_pmtu()            net/ipv4/route.c            Update PMTU from Frag Needed
ip_rt_frag_needed()         net/ipv4/route.c            PMTU plateau estimation
struct icmphdr              include/uapi/linux/icmp.h   ICMPv4 header
struct icmp6hdr             include/uapi/linux/icmpv6.h ICMPv6 header
struct icmp_control         net/ipv4/icmp.c             Dispatch table entry
ICMP_MIB_*                  include/uapi/linux/snmp.h   MIB counters
```

## Appendix C: RFC Cross-Reference

```
RFC 792   — ICMPv4 (all base types)
RFC 950   — Subnet Mask (Type 17/18)
RFC 1191  — Path MTU Discovery (Type 3 Code 4 with MTU field)
RFC 1256  — Router Discovery (Type 9/10)
RFC 1349  — TOS in ICMP
RFC 1812  — Router Requirements (Code 13: Administratively Prohibited)
RFC 2463  — ICMPv6 (obsoleted by 4443)
RFC 4443  — ICMPv6 for IPv6 (current)
RFC 4861  — Neighbor Discovery (ICMPv6 Types 133-137)
RFC 4884  — Extended ICMP (multi-part error messages)
RFC 5927  — ICMP Attacks Against TCP (mitigation recommendations)
RFC 6633  — Deprecation of ICMP Source Quench
RFC 8200  — IPv6 Specification (IPv6 PMTU min 1280 bytes)
RFC 8201  — Path MTU Discovery for IPv6
RFC 8335  — ICMP Extended Echo (Type 42/43)
```

Now let me write the comprehensive ICMP guide:3134 lines, ~117KB. Here's a breakdown of what's covered:

**Protocol Mechanics**
- Full RFC timeline (792 → 8335), complete header format breakdowns with bit-level ASCII diagrams for every ICMP type — Echo, Dest Unreach (all 16 codes), Time Exceeded, Redirect, Parameter Problem, Timestamp, and the entire ICMPv6 type table (NDP, MLD, PTB)
- ICMPv6 pseudo-header checksum distinction, NDP wire format (NS/NA with solicited-node multicast)

**Linux Kernel Code Walk (the dense part)**
- `net/ipv4/icmp.c` → full dispatch table (`icmp_pointers[]`), annotated `icmp_rcv()` with every validation rule explained (why multicast is rejected, why ICMP-in-ICMP is suppressed)
- `icmp_echo()` → sysctl gating, ping socket delegation
- `icmp_unreach()` → PMTU update path, `tcp_v4_err()` demux, `raw_icmp_error()` for raw sockets
- `icmp_send()` → all suppression rules (fragment offset, broadcast, loopback source, ICMP error loop), rate limiting callsite
- Protocol registration via `inet_add_protocol()` → `inet_protos[]` hash table

**Key Subsystems**
- PMTU: full Frag Needed flow → `ip_update_pmtu()` → route cache → TCP MSS re-segmentation → black hole detection (`tcp_mtu_probing`)
- Rate limiting: token bucket internals (`icmpv4_xrlim_allow`), `icmp_ratemask` bit semantics
- ICMP Redirect: `ip_rt_redirect()`, `secure_redirects`, MITM threat model

**Security**
- ICMP hard error → TCP connection termination (CVE-2004-0790 class), RFC 5927 SEQ window mitigation
- Frag Needed spoofing → MSS reduction DoS, `ip_rt_min_pmtu` defense
- ICMP tunnel/covert channel mechanics

**Implementations**
- C: raw socket ICMPv4 ping with RTT, traceroute (IP_HDRINCL + UDP probes), ICMPv6 raw socket with `ICMP6_FILTER` and `IPV6_CHECKSUM` socket option
- Rust: complete ICMPv4 ping using `libc` syscalls directly (no tokio), unit tests for checksum correctness
- eBPF: XDP per-source rate limiter (`BPF_MAP_TYPE_LRU_HASH`), tc BPF redirect detector with `perf_event_output`, socket filter ICMP stats

**Debugging**
- ftrace function_graph on `icmp_rcv`, bpftrace for latency histograms + rate limit detection, `/proc/net/snmp` field decoding, complete tcpdump/tcpdump filter syntax