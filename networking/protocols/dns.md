# DNS Protocol: A Complete, Comprehensive Guide

> **Summary (4–8 lines)**
> DNS (Domain Name System) is the distributed, hierarchical, globally-replicated naming system that maps human-readable domain names to network resources. It operates as a loosely-consistent, eventually-convergent distributed database with TTL-based caching, delegation trees, and a trust anchor rooted at IANA's root zone. DNS wire format runs natively over UDP/53 and TCP/53, with modern secured transports via DoT (853), DoH (443), and DoQ (853 QUIC). Its security model has been repeatedly broken — cache poisoning, amplification, NXDOMAIN hijacking, and exfiltration channels — necessitating DNSSEC, response-rate limiting, 0x20 encoding, aggressive NSEC, and encrypted transport. Understanding DNS at the bit level — wire format, label compression, EDNS0, DNSSEC chain-of-trust — is foundational for cloud security, service mesh control planes, zero-trust networking, and any system that names things. This guide covers all layers from the ARPA origins to production-hardened resolver implementations in C and Rust.

---

## Table of Contents

1. [History and Motivation](#1-history-and-motivation)
2. [DNS Namespace and Hierarchy](#2-dns-namespace-and-hierarchy)
3. [DNS Architecture: Components and Roles](#3-dns-architecture-components-and-roles)
4. [DNS Message Wire Format](#4-dns-message-wire-format)
5. [DNS Record Types — Complete Reference](#5-dns-record-types--complete-reference)
6. [Name Resolution: Full Walk-Through](#6-name-resolution-full-walk-through)
7. [DNS Caching, TTL, and Negative Caching](#7-dns-caching-ttl-and-negative-caching)
8. [Zone Files and Zone Transfers (AXFR/IXFR)](#8-zone-files-and-zone-transfers-axfrixfr)
9. [EDNS0 — Extension Mechanisms for DNS](#9-edns0--extension-mechanisms-for-dns)
10. [Transport Layer: UDP, TCP, DoT, DoH, DoQ](#10-transport-layer-udp-tcp-dot-doh-doq)
11. [DNSSEC — DNS Security Extensions](#11-dnssec--dns-security-extensions)
12. [DNS Security Threats and Mitigations](#12-dns-security-threats-and-mitigations)
13. [Split-Horizon DNS, Views, and RPZ](#13-split-horizon-dns-views-and-rpz)
14. [DNS in Kubernetes and Cloud Platforms](#14-dns-in-kubernetes-and-cloud-platforms)
15. [Implementation in C](#15-implementation-in-c)
16. [Implementation in Rust](#16-implementation-in-rust)
17. [Testing, Fuzzing, and Benchmarking](#17-testing-fuzzing-and-benchmarking)
18. [Threat Model](#18-threat-model)
19. [Next 3 Steps](#19-next-3-steps)
20. [References and RFCs](#20-references-and-rfcs)

---

## 1. History and Motivation

### 1.1 The Pre-DNS World (before 1983)

In the ARPANET era, host-to-address mapping was maintained in a single flat file: `HOSTS.TXT`, managed at the Stanford Research Institute Network Information Center (SRI-NIC) and manually distributed to every host. Administrators would periodically FTP the file from `SRI-NIC.ARPA`. Problems were fundamental:

- **Scale**: By 1982, ARPANET had ~400 hosts. Growth made the model untenable. Today there are ~1.9 billion websites.
- **Uniqueness**: No enforcement of name collisions. Multiple administrators would independently pick the same hostname.
- **Update latency**: Changes took days to propagate via batch FTP. A host removal still received traffic.
- **Single point of failure**: One file, one server, one distribution mechanism.
- **No delegation**: No way to let an organization manage its own namespace.

### 1.2 RFC 882/883 and the Birth of DNS (1983)

Paul Mockapetris published **RFC 882** and **RFC 883** in November 1983, introducing the DNS design. The core insight was to model the naming system as a **distributed database** with:

- A hierarchical namespace modeled as an inverted tree
- Delegation of authority to zones, not a monolithic file
- A protocol for querying the distributed database (UDP/TCP port 53)
- Caching with TTLs to reduce load

**RFC 1034** and **RFC 1035** (1987) obsoleted 882/883, remained the base DNS specification for decades. Subsequent RFCs layered DNSSEC, EDNS0, DoT, DoH, and DoQ on top without replacing the core.

### 1.3 Design Principles (and Their Security Implications)


| Principle | Description | Security implication |
|-----------|-------------|---------------------|
| Hierarchical delegation | Zones delegate sub-zones | Compromise of parent breaks child trust without DNSSEC |
| UDP-first | Low overhead queries | Stateless → spoofing, amplification attacks |
| Anycast routing | Multiple root/TLD servers share one IP | Resilient but complicates source validation |
| Caching | Resolvers cache answers per TTL | Cache poisoning if TXID/port prediction succeeds |
| Open recursion | Resolvers accept queries from any IP | Amplification DDoS vector |
| Cleartext | No encryption in original protocol | On-path eavesdropping, manipulation |

---

## 2. DNS Namespace and Hierarchy

### 2.1 The Tree Structure

DNS names form an **inverted tree** rooted at `.` (the root). Each node in the tree is a **label**. The full path from a node to the root is the **Fully Qualified Domain Name (FQDN)**.

```
                            . (root)
                            |
          +-----------------+------------------+
          |                 |                  |
         com               org                net
          |                 |
    +-----+-----+      +---------+
    |           |      |         |
  google     amazon  ietf     linux
    |
  +--+--+
  |     |
 www   mail
```

- **Root zone**: `.` — managed by IANA/ICANN, served by 13 root server clusters (a–m.root-servers.net) using IPv4 anycast (and IPv6 AAAA).
- **Top-Level Domains (TLDs)**: `com`, `org`, `net`, `io`, country-code TLDs (`uk`, `de`, `in`), new gTLDs (`app`, `dev`, `cloud`).
- **Second-Level Domains (SLDs)**: `google`, `amazon`, `ietf` — registered by organizations.
- **Subdomains**: `www`, `mail`, `vpn` — delegated within the SLD.

### 2.2 Labels and Name Encoding

A DNS name is a sequence of **labels** separated by `.`. Wire-format encoding:

```
Each label:  [1-byte length][label bytes]
Terminator:  [0x00]

Example: "www.example.com."
Wire:    03 77 77 77  (3, "www")
         07 65 78 61 6d 70 6c 65  (7, "example")
         03 63 6f 6d  (3, "com")
         00  (root / terminator)
```

Constraints:
- Label length: 1–63 octets
- Total name length (wire): ≤255 octets
- Labels: case-insensitive comparison (uppercase A = lowercase a per RFC 1034 §3.1)
- Internationalized Domain Names (IDN): Punycode-encoded, e.g. `münchen.de` → `xn--mnchen-3ya.de` (IDNA2008, RFC 5891)

### 2.3 Label Compression (Pointer)

DNS messages can use **message compression** to reduce packet size. A pointer replaces a repeated label sequence:

```
Bits: 11xxxxxxxxxxxxxx  (top 2 bits = 11 → pointer)
      ^^^^^^^^^^^^^^^^
      14-bit offset from the start of the DNS message

Example:
  Offset 12: 03 77 77 77 07 65 78 61 6d 70 6c 65 03 63 6f 6d 00
             "www.example.com."
  
  Later in the packet, "mail.example.com." can be encoded as:
  04 6d 61 69 6c  (4, "mail")
  c0 0f           (pointer to offset 15 → ".example.com.")
```

**Security implication**: Malformed pointers (loops, out-of-bounds) are a historic source of parser vulnerabilities. Always track pointer depth and validate offsets.

### 2.4 Zone and Delegation

A **zone** is a contiguous portion of the DNS namespace that a single administrative entity controls. A **zone cut** is where delegation occurs — the parent zone has NS records pointing to the child zone's authoritative servers.

```
parent zone: example.com.
  contains:  NS records for api.example.com. → delegation
  does NOT contain: records inside api.example.com. (that's the child zone)

child zone: api.example.com.
  contains: all records within api.example.com.
  Start of Authority: SOA record
```

---

## 3. DNS Architecture: Components and Roles

### 3.1 Component Overview

```
+------------------+       +-------------------+       +---------------------------+
|   Stub Resolver  |       |  Recursive        |       |  Authoritative Name       |
|  (libc/systemd-  +------>+  Resolver         +------>+  Server                   |
|   resolved/      |UDP/53 | (full-service     |UDP/53 | (BIND/NSD/PowerDNS/       |
|   getaddrinfo)   |       |  resolver, DNSSEC |TCP/53 |  Knot/Route53)            |
+------------------+       |  validation,      |DoT    |                           |
                           |  caching)         |DoH    | Serves zone data from     |
                           +-------------------+       | zone files or DB backend  |
                                    |                  +---------------------------+
                                    | (iterative queries)
                           +--------v---------+
                           |  Root Name Server |
                           |  (a-m.root-       |
                           |   servers.net)    |
                           +--------+---------+
                                    |
                           +--------v---------+
                           |  TLD Name Server  |
                           |  (e.g. Verisign   |
                           |   for .com)       |
                           +--------+---------+
                                    |
                           +--------v---------+
                           |  SLD Authoritative|
                           |  Server           |
                           |  (e.g. ns1.       |
                           |   example.com)    |
                           +------------------+
```

### 3.2 Stub Resolver

The **stub resolver** is the client-side component in the operating system or application runtime. It:

- Reads `/etc/resolv.conf` (Linux) or system DNS settings
- Sends non-recursive queries to a configured recursive resolver
- Has minimal or no cache (glibc has a small, optional nscd)
- Does **not** perform iterative resolution

Key functions: `getaddrinfo()`, `getnameinfo()`, `res_query()` (POSIX). On modern Linux, `systemd-resolved` acts as a local stub resolver at `127.0.0.53:53`.

**`/etc/resolv.conf` format:**
```
nameserver 127.0.0.53       # or 8.8.8.8
search example.com corp.internal
options ndots:5 timeout:2 attempts:3 rotate
```

`ndots:5` means: if the query name has fewer than 5 dots, try appending search domains before treating it as absolute. This is a significant security and reliability concern in Kubernetes.

### 3.3 Recursive Resolver (Full-Service Resolver)

Also called a **recursive nameserver** or **resolver**. It:

- Accepts recursive queries from stub resolvers (`RD=1`)
- Performs the full iterative resolution process on behalf of the client
- Caches all answers per TTL
- Validates DNSSEC if configured
- Examples: Unbound, BIND (named), PowerDNS Recursor, Knot Resolver, CoreDNS

Key distinction: **recursive** vs **iterative**. The resolver iterates through the hierarchy; the stub just asks the resolver to do the full job (`RD` bit = Recursion Desired).

### 3.4 Authoritative Name Server

Holds the **ground truth** for a zone. It:

- Responds with `AA=1` (Authoritative Answer) bit set
- Never follows referrals for its own zone
- Serves SOA, NS, A, AAAA, MX, TXT, CNAME, and all other records
- May be primary (holds the master zone file) or secondary (transfers via AXFR/IXFR from primary)
- Examples: BIND (named), NSD, Knot Authoritative, PowerDNS Authoritative, AWS Route 53, Cloudflare

### 3.5 Root Servers

13 logical root nameservers (A through M), each backed by **hundreds of physical anycast nodes** worldwide:

```
Letter  Operator                    IPv4            IPv6
A       Verisign                    198.41.0.4      2001:503:ba3e::2:30
B       USC-ISI                     199.9.14.201    2001:500:200::b
C       Cogent                      192.33.4.12     2001:500:2::c
D       U Maryland                  199.7.91.13     2001:500:2d::d
E       NASA                        192.203.230.10  2001:500:a8::e
F       ISC                         192.5.5.241     2001:500:2f::f
G       DISA                        192.112.36.4    2001:500:12::d0d
H       ARL                         198.97.190.53   2001:500:1::53
I       Netnod                      192.36.148.17   2001:7fe::53
J       Verisign                    192.58.128.30   2001:503:c27::2:30
K       RIPE NCC                    193.0.14.129    2001:7fd::1
L       ICANN                       199.7.83.42     2001:500:9f::42
M       WIDE Project                202.12.27.33    2001:dc3::35
```

These IPs are embedded in resolvers as the **root hints file** (`named.root` / `root.hints`). Root servers are reached via BGP anycast — the resolver's packet is routed to the nearest instance.

### 3.6 Forwarding vs. Resolving

A **forwarding resolver** passes queries to an upstream resolver instead of iterating from root. Useful for:
- Split-horizon (internal vs external)
- Enforcing DoT/DoH to upstream
- Filtering via RPZ

```
stub → local forwarding resolver → corporate upstream resolver → root → TLD → auth
```

---

## 4. DNS Message Wire Format

This is the most critical section for implementation and security analysis. Every DNS interaction is a binary message. You must understand every bit.

### 4.1 Message Structure Overview

```
+---------------------+
|        Header       |  12 bytes, always present
+---------------------+
|       Question      |  QDCOUNT entries
+---------------------+
|        Answer       |  ANCOUNT RRs
+---------------------+
|      Authority      |  NSCOUNT RRs
+---------------------+
|      Additional     |  ARCOUNT RRs
+---------------------+
```

### 4.2 Header Format (12 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                          ID (16 bits)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|QR|  Opcode   |AA|TC|RD|RA| Z|AD|CD|        RCODE (4 bits)     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       QDCOUNT (16 bits)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       ANCOUNT (16 bits)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       NSCOUNT (16 bits)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       ARCOUNT (16 bits)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Field-by-field:**

| Field | Bits | Description |
|-------|------|-------------|
| **ID** | 16 | Transaction ID. Client sets; server copies. Used to match responses to queries. MUST be random (PRNG) to resist off-path spoofing. |
| **QR** | 1 | 0 = Query, 1 = Response |
| **Opcode** | 4 | 0=QUERY, 1=IQUERY(obsolete), 2=STATUS, 4=NOTIFY, 5=UPDATE(RFC 2136) |
| **AA** | 1 | Authoritative Answer — set by authoritative server |
| **TC** | 1 | TrunCated — response was truncated (UDP limit hit), client should retry over TCP |
| **RD** | 1 | Recursion Desired — client asks resolver to recurse |
| **RA** | 1 | Recursion Available — server sets if it supports recursion |
| **Z** | 1 | Reserved, MUST be zero (RFC 1035). EDNS0 reuses as part of extended RCODE |
| **AD** | 1 | Authentic Data (DNSSEC) — resolver validated the answer chain |
| **CD** | 1 | Checking Disabled (DNSSEC) — client asks resolver NOT to validate |
| **RCODE** | 4 | Response code (see table below) |
| **QDCOUNT** | 16 | Number of entries in Question section (almost always 1) |
| **ANCOUNT** | 16 | Number of Resource Records in Answer section |
| **NSCOUNT** | 16 | Number of RRs in Authority section |
| **ARCOUNT** | 16 | Number of RRs in Additional section |

**RCODE values:**

| Code | Name | Meaning |
|------|------|---------|
| 0 | NOERROR | No error |
| 1 | FORMERR | Format error — server could not interpret query |
| 2 | SERVFAIL | Server failure — recursive resolution failed |
| 3 | NXDOMAIN | Name does not exist |
| 4 | NOTIMP | Not implemented — server does not support this query type |
| 5 | REFUSED | Policy refusal (e.g., zone transfer denied) |
| 6 | YXDOMAIN | Name exists when it should not (RFC 2136 Dynamic DNS) |
| 7 | YXRRSET | RR set exists when it should not |
| 8 | NXRRSET | RR set that should exist does not |
| 9 | NOTAUTH | Server not authoritative for zone |
| 10 | NOTZONE | Name not contained in zone |
| 16 | BADSIG | TSIG signature failure (extended RCODE via EDNS0 OPT) |
| 17 | BADKEY | Key not recognized |
| 18 | BADTIME | Signature out of time window |
| 22 | BADCOOKIE | Bad/missing server cookie (RFC 7873) |

### 4.3 Question Section

Follows the header. Each question entry:

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      QNAME                    |
|           (variable length, encoded name)     |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      QTYPE                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                     QCLASS                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

- **QNAME**: Wire-encoded domain name (labels + length bytes + null terminator)
- **QTYPE**: Record type being queried (A=1, AAAA=28, MX=15, NS=2, SOA=6, TXT=16, ANY=255, etc.)
- **QCLASS**: IN (Internet) = 1; CH (Chaos) = 3 (used for `version.bind` queries); ANY = 255

### 4.4 Resource Record (RR) Format

All sections (Answer, Authority, Additional) contain Resource Records:

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                       NAME                    |
|           (compressed or full domain name)    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                       TYPE         (16 bits)  |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      CLASS         (16 bits)  |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                       TTL          (32 bits)  |
|                                               |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                     RDLENGTH       (16 bits)  |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      RDATA                    |
|             (variable, RDLENGTH bytes)        |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

- **NAME**: Owner name of this RR
- **TYPE**: RR type (numeric)
- **CLASS**: Almost always IN (1)
- **TTL**: 32-bit unsigned integer — seconds this RR may be cached; 0 = do not cache
- **RDLENGTH**: Length in bytes of RDATA
- **RDATA**: Type-specific data

### 4.5 Annotated Wire Example: Query for `www.example.com` A record

```
DNS Query: A record for www.example.com

Bytes (hex):
ab cd  <- Transaction ID = 0xABCD
01 00  <- Flags: QR=0 (query), Opcode=0, RD=1 (recursion desired)
         Binary: 0000 0001 0000 0000
00 01  <- QDCOUNT = 1
00 00  <- ANCOUNT = 0
00 00  <- NSCOUNT = 0
00 00  <- ARCOUNT = 0

Question section:
03     <- label length = 3
77 77 77  <- "www"
07     <- label length = 7
65 78 61 6d 70 6c 65  <- "example"
03     <- label length = 3
63 6f 6d  <- "com"
00     <- end of name (root label)
00 01  <- QTYPE = A (1)
00 01  <- QCLASS = IN (1)

Total: 29 bytes
```

```
DNS Response: A record for www.example.com

ab cd  <- Transaction ID (echoed from query)
81 80  <- Flags: QR=1 (response), AA=0, TC=0, RD=1, RA=1, RCODE=0
         Binary: 1000 0001 1000 0000
00 01  <- QDCOUNT = 1 (question echoed)
00 01  <- ANCOUNT = 1 (one answer)
00 00  <- NSCOUNT = 0
00 00  <- ARCOUNT = 0

Question section (echoed):
[same as query question section]

Answer section:
c0 0c  <- NAME: pointer (0xC0 = pointer indicator, 0x0C = offset 12)
         offset 12 is where the QNAME starts in this message
00 01  <- TYPE = A
00 01  <- CLASS = IN
00 00 0e 10  <- TTL = 3600 seconds
00 04  <- RDLENGTH = 4 bytes
5d b8 d8 22  <- RDATA = 93.184.216.34 (example.com's IP)
```

### 4.6 Flags Byte Detailed Bit Layout

```
Byte offset 2 (first flags byte):
 Bit 7   6   5   4   3   2   1   0
+----+---+---+---+---+---+---+---+
| QR | Opcode    |AA |TC |RD | unused for this octet position
+----+---+---+---+---+---+---+---+
  ^      ^            ^   ^   ^
  |      0=QUERY      |   |   Recursion Desired
  |      2=STATUS     |   TrunCated
  |      4=NOTIFY     Authoritative Answer
  Response/Query

Byte offset 3 (second flags byte):
 Bit 7   6   5   4   3   2   1   0
+----+---+---+---+---+---+---+---+
| RA | Z |AD |CD |    RCODE      |
+----+---+---+---+---+---+---+---+
  ^   ^   ^   ^      ^
  |   |   |   |      0=NOERROR
  |   |   |   |      1=FORMERR
  |   |   |   |      2=SERVFAIL
  |   |   |   |      3=NXDOMAIN
  |   |   |   Checking Disabled (DNSSEC)
  |   |   Authentic Data (DNSSEC validated)
  |   Reserved (MUST be 0; EDNS0 extends)
  Recursion Available
```

---

## 5. DNS Record Types — Complete Reference

### 5.1 Core Record Types (RFC 1035)

#### A — IPv4 Address (Type 1)

```
RDATA: 4 bytes, IPv4 address in network byte order

Example:
www.example.com.  3600  IN  A  93.184.216.34

Wire RDATA: 5d b8 d8 22
```

#### NS — Name Server (Type 2)

```
RDATA: domain name (wire-encoded, compressible)
Points to the authoritative nameserver for the zone.

Example:
example.com.  172800  IN  NS  ns1.example.com.

RDATA wire: encoded name "ns1.example.com."
```

#### CNAME — Canonical Name (Type 5)

```
RDATA: domain name — the canonical (true) name
An alias. Resolver must follow the CNAME chain and re-query for the target.

Example:
www.example.com.  3600  IN  CNAME  lb.example.com.
lb.example.com.   60    IN  A      203.0.113.5

Rules:
- CNAME must be the ONLY record for that name (cannot coexist with A, MX, etc.)
  EXCEPT at zone apex (which is why ALIAS/ANAME pseudo-records exist in some implementations)
- Resolver follows chain; max chain depth implementation-dependent (typically 8–16)
- CNAME chains can cross zones
```

#### SOA — Start of Authority (Type 6)

```
RDATA format:
  MNAME:   primary nameserver for the zone (wire name)
  RNAME:   responsible party email (. replaces @; foo.bar.com = foo@bar.com)
  SERIAL:  32-bit unsigned, zone version. Secondary transfers if SERIAL increases.
  REFRESH: seconds between serial checks by secondaries
  RETRY:   seconds before retry after failed REFRESH
  EXPIRE:  seconds after which secondary stops serving if primary unreachable
  MINIMUM: minimum TTL; also used as negative caching TTL (RFC 2308)

Example:
example.com.  3600  IN  SOA  ns1.example.com. admin.example.com. (
                    2024010101  ; Serial (often YYYYMMDDNN format)
                    3600        ; Refresh
                    900         ; Retry
                    604800      ; Expire (1 week)
                    300 )       ; Minimum TTL / negative cache TTL
```

SOA SERIAL increment conventions:
- `YYYYMMDDNN` (date + 2-digit counter): most common
- Unix timestamp: used by some dynamic DNS implementations
- **Critical**: Serial MUST increase for zone transfer to trigger (secondary compares).

#### MX — Mail Exchange (Type 15)

```
RDATA:
  PREFERENCE: 16-bit priority (lower = preferred)
  EXCHANGE:   domain name of mail server

Example:
example.com.  3600  IN  MX  10  mail1.example.com.
example.com.  3600  IN  MX  20  mail2.example.com.

Wire RDATA:
  00 0a       <- preference = 10
  [encoded "mail1.example.com."]

Security: MX records enable email spoofing research. DMARC/DKIM/SPF records
in TXT complement MX security.
```

#### PTR — Pointer (Type 12)

```
Used for reverse DNS lookups (IP → name).
IPv4 reverse zone: in-addr.arpa.
  93.184.216.34 → 34.216.184.93.in-addr.arpa. PTR www.example.com.
IPv6 reverse zone: ip6.arpa.
  2001:db8::1 → 1.0.0.0...0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa. PTR host.example.com.

RDATA: domain name (the reverse mapping target)
```

#### TXT — Text (Type 16)

```
RDATA: one or more character strings, each prefixed by 1-byte length.
Multiple strings in one TXT record are concatenated by convention.
Max per string: 255 bytes. Total RDATA: up to 65535 bytes (but practical limit ~512 bytes for UDP).

Example:
example.com.  3600  IN  TXT  "v=spf1 include:_spf.example.com ~all"
_dmarc.example.com.  3600  IN  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
_domainkey.example.com.  3600  IN  TXT  "v=DKIM1; k=rsa; p=MIGfMA0GCS..."

Wire RDATA for TXT "hello" "world":
  05 68 65 6c 6c 6f  <- length=5, "hello"
  05 77 6f 72 6c 64  <- length=5, "world"
```

### 5.2 Extended Record Types

#### AAAA — IPv6 Address (Type 28, RFC 3596)

```
RDATA: 16 bytes, IPv6 address in network byte order

Example:
www.example.com.  3600  IN  AAAA  2606:2800:220:1:248:1893:25c8:1946

Wire RDATA: 26 06 28 00 02 20 00 01 02 48 18 93 25 c8 19 46
```

#### SRV — Service Locator (Type 33, RFC 2782)

```
Name format: _service._proto.name.
RDATA:
  PRIORITY: 16-bit (lower = preferred, like MX)
  WEIGHT:   16-bit (relative weight among same-priority records, for load balancing)
  PORT:     16-bit TCP/UDP port
  TARGET:   domain name of the server

Example:
_http._tcp.example.com.  3600  IN  SRV  10 50 80 web1.example.com.
_http._tcp.example.com.  3600  IN  SRV  10 50 80 web2.example.com.
_http._tcp.example.com.  3600  IN  SRV  20 0  80 backup.example.com.

Used by: Kubernetes service discovery (kube-dns), XMPP, SIP, etcd cluster join.
```

#### CAA — Certification Authority Authorization (Type 257, RFC 8659)

```
RDATA:
  FLAGS: 1 byte (bit 0 = critical)
  TAG:   1-byte length + string ("issue", "issuewild", "iodef")
  VALUE: remaining bytes

Example:
example.com.  3600  IN  CAA  0 issue "letsencrypt.org"
example.com.  3600  IN  CAA  0 issuewild ";"
example.com.  3600  IN  CAA  0 iodef "mailto:security@example.com"

CAs MUST check CAA before issuing a certificate. Critical for preventing
unauthorized certificate issuance (MITM attacks).
```

#### NAPTR — Naming Authority Pointer (Type 35, RFC 3403)

```
Used in ENUM (telephone number → URI mapping) and SIP.
RDATA: ORDER, PREFERENCE, FLAGS, SERVICES, REGEXP, REPLACEMENT
```

#### DS — Delegation Signer (Type 43, RFC 4034)

```
Created by parent zone, contains hash of child zone's KSK (Key Signing Key).
RDATA:
  KEY TAG:    16-bit
  ALGORITHM:  8-bit (5=RSA/SHA-1, 8=RSA/SHA-256, 13=ECDSA P-256/SHA-256, 15=Ed25519)
  DIGEST TYPE: 8-bit (1=SHA-1, 2=SHA-256, 4=SHA-384)
  DIGEST:     variable bytes

Central to DNSSEC chain of trust.
```

#### DNSKEY — DNS Public Key (Type 48, RFC 4034)

```
RDATA:
  FLAGS:     16-bit (bit 8 = Zone Key, bit 0 = Secure Entry Point = KSK)
  PROTOCOL:  8-bit (MUST be 3 per RFC)
  ALGORITHM: 8-bit (same as DS)
  PUBLIC KEY: variable bytes

Zone Key Flag (bit 8 set, value 256) = ZSK (Zone Signing Key)
SEP flag (bit 8 + bit 0, value 257) = KSK (Key Signing Key)
```

#### RRSIG — Resource Record Signature (Type 46, RFC 4034)

```
RDATA:
  TYPE COVERED:   16-bit (type of RRset being signed)
  ALGORITHM:      8-bit
  LABELS:         8-bit (number of labels in original name, for wildcard handling)
  ORIGINAL TTL:   32-bit
  SIGNATURE EXPIRATION: 32-bit Unix timestamp
  SIGNATURE INCEPTION:  32-bit Unix timestamp
  KEY TAG:        16-bit (identifies signing key)
  SIGNER NAME:    domain name (zone that holds the DNSKEY)
  SIGNATURE:      variable bytes (RSA/ECDSA/Ed25519 signature)
```

#### NSEC — Next Secure (Type 47, RFC 4034)

```
Used to prove non-existence of names/types in DNSSEC-signed zones.
RDATA:
  NEXT DOMAIN NAME: the next name in canonical order in the zone
  TYPE BITMAP: bit map of existing types at the current name

Problem: NSEC enables zone enumeration (walk the chain of NEXT pointers).
Solution: NSEC3 (Type 50) hashes the names with salt.
```

#### NSEC3 — Next Secure v3 (Type 50, RFC 5155)

```
RDATA:
  HASH ALGORITHM:  8-bit (1=SHA-1 only currently)
  FLAGS:           8-bit (bit 0 = Opt-Out)
  ITERATIONS:      16-bit (hash iteration count — keep low to resist offline attacks)
  SALT LENGTH:     8-bit
  SALT:            variable
  HASH LENGTH:     8-bit
  NEXT HASHED OWNER NAME: variable (base32-encoded SHA-1 hash)
  TYPE BITMAP:     same as NSEC

Opt-Out flag: allows unsigned delegations (for large TLDs with many unsigned delegations)
Security concern: NSEC3 with high iterations (>100) degrades resolver performance.
ICANN recommended max iterations dropped to 0 in RFC 9276.
```

#### TLSA — TLS Authentication (Type 52, RFC 6698) — DANE

```
Name: _port._proto.hostname
RDATA:
  CERT USAGE:      8-bit (0=PKIX-TA, 1=PKIX-EE, 2=DANE-TA, 3=DANE-EE)
  SELECTOR:        8-bit (0=full cert, 1=SubjectPublicKeyInfo)
  MATCHING TYPE:   8-bit (0=exact, 1=SHA-256, 2=SHA-512)
  CERT ASSOCIATION DATA: variable

Example:
_443._tcp.www.example.com.  3600  IN  TLSA  3 1 1 [sha256-of-spki]

Enables certificate pinning via DNS (DANE). Requires DNSSEC for security.
```

#### HTTPS / SVCB — Service Binding (Type 65/64, RFC 9460)

```
Modern replacement for combining A/AAAA + port + ALPN info.
Enables HTTP/3 (QUIC) discovery, ECH (Encrypted Client Hello) key distribution.

Example:
example.com.  3600  IN  HTTPS  1 . alpn="h3,h2" ipv4hint=93.184.216.34

Priority=0: aliasform (like CNAME)
Priority>0: serviceform with params
```

#### DNAME — Delegation Name (Type 39, RFC 6672)

```
Redirects an entire subtree of the DNS namespace. Unlike CNAME (single name),
DNAME redirects all names under it.

Example:
old.example.com.  3600  IN  DNAME  new.example.com.
www.old.example.com → synthesized CNAME → www.new.example.com
```

#### OPT — Option (Type 41, RFC 6891) — EDNS0

```
Pseudo-RR used in Additional section to signal EDNS0 capabilities.
NOT stored in zone data. Only in DNS messages.
See Section 9 for full EDNS0 coverage.
```

#### ANY — All Types (QTYPE 255)

```
Query for all cached records. Heavily abused for amplification attacks.
RFC 8482 allows resolvers to respond with a minimal/synthetic response.
Many authoritative servers now return HINFO or refuse ANY queries.
```

### 5.3 Record Type Number Quick Reference

```
Type  Name      RFC
1     A         1035
2     NS        1035
5     CNAME     1035
6     SOA       1035
12    PTR       1035
15    MX        1035
16    TXT       1035
28    AAAA      3596
29    LOC       1876
33    SRV       2782
35    NAPTR     3403
36    KX        2230
37    CERT      4398
39    DNAME     6672
41    OPT       6891  (EDNS0 pseudo-RR)
43    DS        4034  (DNSSEC)
44    SSHFP     4255
45    IPSECKEY  4025
46    RRSIG     4034  (DNSSEC)
47    NSEC      4034  (DNSSEC)
48    DNSKEY    4034  (DNSSEC)
49    DHCID     4701
50    NSEC3     5155  (DNSSEC)
51    NSEC3PARAM 5155
52    TLSA      6698  (DANE)
53    SMIMEA    8162
55    HIP       5205
59    CDS       7344
60    CDNSKEY   7344
61    OPENPGPKEY 7929
62    CSYNC     7477
63    ZONEMD    8976
64    SVCB      9460
65    HTTPS     9460
99    SPF       4408  (deprecated, use TXT)
108   EUI48     7043
109   EUI64     7043
249   TKEY      2930
250   TSIG      2845
251   IXFR      1995
252   AXFR      1035
253   MAILB     1035  (obsolete)
254   MAILA     1035  (obsolete)
255   ANY       1035
256   URI       7553
257   CAA       8659
32768 TA        (DNSSEC Trust Anchor, experimental)
32769 DLV       4431  (obsolete)
```

---

## 6. Name Resolution: Full Walk-Through

### 6.1 Iterative Resolution from Root

```
Client (stub)                   Recursive Resolver                  Internet
    |                                   |
    |--- Query: A www.example.com? ---->|
    |    (RD=1, random TXID)            |
    |                                   |--- 1. Check cache: miss
    |                                   |
    |                                   |--- 2. Query root servers (priming if needed)
    |                                   |    A www.example.com? (RD=0, iterative)
    |                                   |    --> a.root-servers.net (198.41.0.4)
    |                                   |
    |                                   |<-- REFERRAL: .com NS servers
    |                                   |    RCODE=NOERROR, AA=0, ANCOUNT=0
    |                                   |    NSCOUNT: com. NS a.gtld-servers.net.
    |                                   |    ADDITIONAL: a.gtld-servers.net. A 192.5.6.30
    |                                   |
    |                                   |--- 3. Query .com TLD servers
    |                                   |    A www.example.com?
    |                                   |    --> a.gtld-servers.net (192.5.6.30)
    |                                   |
    |                                   |<-- REFERRAL: example.com NS servers
    |                                   |    NSCOUNT: example.com NS ns1.example.com.
    |                                   |    ADDITIONAL: ns1.example.com. A 205.251.196.1
    |                                   |
    |                                   |--- 4. Query example.com authoritative
    |                                   |    A www.example.com?
    |                                   |    --> ns1.example.com (205.251.196.1)
    |                                   |
    |                                   |<-- ANSWER: AA=1
    |                                   |    www.example.com. 3600 IN A 93.184.216.34
    |                                   |
    |                                   |--- 5. Cache the answer, authority, and glue
    |                                   |
    |<-- Response: 93.184.216.34 -------|
    |    (ANCOUNT=1, RA=1, RCODE=0)     |
```

### 6.2 Cache Priming

The very first query from a resolver cold start requires root server addresses. Resolvers load a **root hints file** containing the 13 root server names and their IPs. They then perform **cache priming**: querying the root servers for the root NS records to populate the root zone's NS and glue records in cache.

```bash
# Check root hints file location
dig . NS @a.root-servers.net +norec

# BIND root hints file
/var/named/named.root   # or /etc/bind/db.root
```

### 6.3 CNAME Chasing

```
Query: A www.example.com

Step 1: www.example.com. CNAME lb.example.com.     <- resolver follows
Step 2: lb.example.com.  CNAME pool-a.cdn.net.     <- resolver follows (cross-zone!)
Step 3: pool-a.cdn.net.  A     203.0.113.5          <- final answer

Response to client includes all three RRs in Answer section.

Security concern: CNAME chains can be used for subdomain takeover if
intermediate CNAMEs point to services that are no longer provisioned.
E.g., www.example.com CNAME something.azurewebsites.net (unclaimed)
```

### 6.4 Negative Responses and NXDOMAIN

Two types of negative responses:
1. **NXDOMAIN** (RCODE=3): The name does not exist at all
2. **NOERROR with empty Answer** (NODATA): The name exists but has no records of the queried type

Both are cached with the **negative cache TTL** taken from the SOA MINIMUM field (RFC 2308).

```
NXDOMAIN response:
  RCODE = 3
  ANCOUNT = 0
  NSCOUNT ≥ 1 (SOA record in Authority section for negative caching TTL)

NODATA response:
  RCODE = 0
  ANCOUNT = 0
  NSCOUNT ≥ 1 (SOA record)
```

### 6.5 Glue Records and Bailiwick

**Glue records** are A/AAAA records for nameservers included in the Additional section of referral responses, necessary to avoid circular dependencies.

```
If ns1.example.com. is the NS for example.com., then to find
ns1.example.com.'s IP, you'd need to query example.com. → circular!

Solution: Parent zone (.com TLD) includes "glue":
  AUTHORITY: example.com. NS ns1.example.com.
  ADDITIONAL: ns1.example.com. A 205.251.196.1   <- glue record
```

**Bailiwick checking**: A resolver must only accept glue records that are within the bailiwick (the zone being delegated). A malicious NS server cannot inject glue for `google.com` when answering for `example.com`. Historically, lack of bailiwick checking led to cache poisoning (Kaminsky attack).

### 6.6 The Kaminsky Attack (2008)

Dan Kaminsky's cache poisoning attack exploited:

1. Resolver queries for `random-subdomain.example.com` (attacker sends 1000s of forged subdomains)
2. Attacker sends spoofed UDP responses with:
   - Source IP: real authoritative server
   - TXID: brute-forced (16 bits = 65536 possibilities)
   - Answer: `example.com NS evil.attacker.com`
3. If one spoofed response arrives before the real one, cache is poisoned

**Why it worked pre-fix**: Source port was predictable (often fixed port 53). Only 16-bit TXID randomness.

**Fix**: Source port randomization (RFC 5452). Each query uses a random ephemeral port (49152–65535 range = ~16,000 extra bits of entropy). Attack now requires ~16,000 × 65,536 = ~10⁹ guesses.

**DNSSEC** is the complete fix — cryptographic signatures make spoofing impossible.

**CVE-2008-1447** — one of the most significant DNS vulnerabilities in history.

---

## 7. DNS Caching, TTL, and Negative Caching

### 7.1 TTL Semantics

TTL is a **32-bit unsigned integer** in seconds. However:
- RFC 2181 clarifies: all RRs in an RRset MUST have the same TTL
- If they differ, use the **lowest TTL** (conservative caching)
- TTL=0 means "do not cache" (still valid for one use)
- Maximum meaningful TTL: ~68 years (but practically capped at 24h–7d)

**TTL strategy trade-offs:**

| TTL | Pros | Cons |
|-----|------|------|
| Low (60–300s) | Fast propagation of changes, failover speed | Higher query load, more resolver latency |
| Medium (3600s) | Balanced | 1-hour propagation delay |
| High (86400s) | Low query load, resilient to authoritative outage | Very slow changes, 24h for failover |

**Best practice**: Keep TTL high normally, lower it before planned changes (TTL pre-lowering), then raise it again afterward.

### 7.2 Negative Caching (RFC 2308)

Negative caching prevents repeated lookups for non-existent names:

```
Negative TTL = MIN(SOA TTL, SOA MINIMUM field)

Example SOA:
example.com.  3600  IN  SOA  ns1 admin (2024010101 3600 900 604800 300)
                                                                       ^^^
                                                                       MINIMUM = 300s

If NXDOMAIN for foo.example.com., cache for min(3600, 300) = 300 seconds
```

### 7.3 TTL Aging and Refresh

When a resolver serves a cached record, it **decrements the TTL** by the elapsed time since it was cached. The client always receives the remaining TTL, not the original.

```
At t=0: cached www.example.com A 93.184.216.34, TTL=3600
At t=1800: client queries → responds with TTL=1800
At t=3600: TTL expired → resolver re-queries authoritative server
```

### 7.4 Prefetching and Serve-Stale

**Prefetching** (Unbound: `prefetch: yes`): When TTL drops below 10% of original, proactively re-query in background. Reduces latency for popular records.

**Serve-stale** (RFC 8767): When authoritative is unreachable, serve expired records with TTL=30 rather than SERVFAIL. Improves resilience.

```
# Unbound config
serve-expired: yes
serve-expired-ttl: 86400
prefetch: yes
prefetch-key: yes
```

### 7.5 DNS Cache Snooping

An attacker can determine if a resolver has cached a record by querying it with `RD=0` (non-recursive). Cache hit → fast response with positive TTL; cache miss → REFUSED or slow referral. Used in threat intelligence and for detecting if a user visited a site.

**Mitigation**: Respond REFUSED to non-recursive queries from untrusted sources.

---

## 8. Zone Files and Zone Transfers (AXFR/IXFR)

### 8.1 Zone File Format (RFC 1035 Master Format)

```
$ORIGIN example.com.
$TTL 3600

; SOA - mandatory first record
@   IN  SOA  ns1.example.com.  admin.example.com. (
            2024010101  ; Serial
            3600        ; Refresh
            900         ; Retry
            604800      ; Expire
            300 )       ; Minimum

; Name servers
@       IN  NS   ns1.example.com.
@       IN  NS   ns2.example.com.

; Glue records (if ns1/ns2 are in this zone)
ns1     IN  A    203.0.113.1
ns2     IN  A    203.0.113.2

; Mail exchanger
@       IN  MX   10  mail1.example.com.
@       IN  MX   20  mail2.example.com.

; A records
@       IN  A    93.184.216.34
www     IN  A    93.184.216.34
mail1   IN  A    203.0.113.10
mail2   IN  A    203.0.113.11
api     IN  A    203.0.113.20

; AAAA records
@       IN  AAAA 2606:2800:220:1:248:1893:25c8:1946
www     IN  AAAA 2606:2800:220:1:248:1893:25c8:1946

; CNAME
ftp     IN  CNAME  www.example.com.
blog    IN  CNAME  www.example.com.

; TXT records
@       IN  TXT  "v=spf1 mx ~all"
_dmarc  IN  TXT  "v=DMARC1; p=quarantine"

; CAA
@       IN  CAA  0 issue "letsencrypt.org"

; SRV
_https._tcp  IN  SRV  10 50 443 www.example.com.
```

**$ORIGIN**: Sets the default domain suffix for relative names.
**@**: Shorthand for the current origin.
**Relative names**: `www` = `www.example.com.` (current origin appended).
**Absolute names**: `www.other.com.` (trailing dot = no origin appended).

### 8.2 AXFR — Full Zone Transfer

AXFR (Authoritative Transfer) transfers the complete zone from primary to secondary:

```
1. Secondary connects to primary TCP/53 (or TSIG-protected)
2. Secondary sends: QTYPE=AXFR, QNAME=example.com.
3. Primary responds with all zone RRs, starting and ending with SOA
4. Secondary replaces its zone data atomically

Wire format:
  [SOA record]
  [all RRs in zone]
  [SOA record again] (marks end of transfer)

Security: AXFR exposes the entire zone. MUST be restricted!
  - BIND: allow-transfer { key tsig-key-name; };
  - Or IP ACLs: allow-transfer { 203.0.113.2; };
  - Best: TSIG authentication (RFC 2845)
```

### 8.3 IXFR — Incremental Zone Transfer (RFC 1995)

IXFR transfers only the differences between zone versions:

```
Secondary sends: QTYPE=IXFR, with SOA of its current version in Authority section
Primary responds:
  - If changes available: [new SOA] [deleted RRs] [new SOA again] [added RRs] [new SOA]
  - If secondary too far behind: full AXFR instead

Significantly reduces bandwidth for large zones with frequent small updates.
```

### 8.4 NOTIFY (RFC 1996)

Instead of waiting for REFRESH interval, primary immediately notifies secondaries of zone changes:

```
Primary sends NOTIFY (Opcode=4) to secondary
Secondary responds with NOTIFY to acknowledge
Secondary then initiates SOA check and transfer if needed
```

### 8.5 TSIG — Transaction SIGnature (RFC 2845)

TSIG authenticates DNS messages (particularly zone transfers and dynamic updates) using shared-secret HMAC:

```
TSIG record in Additional section:
  NAME:    key name (e.g., "transfer-key.example.com.")
  TYPE:    250 (TSIG)
  CLASS:   ANY
  TTL:     0
  RDATA:
    Algorithm Name: hmac-sha256.
    Time Signed:    Unix timestamp (6 bytes)
    Fudge:          300 (seconds of clock skew tolerance)
    MAC Size:       32
    MAC:            32-byte HMAC-SHA256 of (message + TSIG record variables)
    Original ID:    original query ID
    Error:          0 (or TSIG error code)
    Other Data:     variable

Key generation:
  tsig-keygen -a hmac-sha256 transfer-key
```

---

## 9. EDNS0 — Extension Mechanisms for DNS

RFC 6891 (originally RFC 2671) — EDNS0 extends DNS without breaking backward compatibility.

### 9.1 OPT Pseudo-RR Format

Appears in the Additional section. Not stored in zone data. Present in messages only.

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    NAME = 0x00                |  (root label = empty)
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|              TYPE = 41 (OPT)      (16 bits)   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|         UDP PAYLOAD SIZE          (16 bits)   |  (replaces CLASS field)
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
| EXTENDED RCODE (8) | VERSION (8)  (these two) |  (replaces TTL high 16 bits)
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|     Z (DO bit = bit 15)  + reserved (15 bits) |  (replaces TTL low 16 bits)
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                   RDLENGTH        (16 bits)   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                   RDATA (options)             |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

Key fields:
- **UDP PAYLOAD SIZE**: Advertises max UDP response the client can receive (typically 1232 or 4096 bytes)
- **EXTENDED RCODE**: Upper 8 bits of RCODE (combined with header's 4-bit RCODE for 12-bit total)
- **VERSION**: EDNS version (0 only currently; unknown = BADVERS error)
- **DO bit** (DNSSEC OK): Client sets this to request DNSSEC records (RRSIG, NSEC, etc.)

### 9.2 EDNS Options

RDATA contains TLV-encoded options:

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|               OPTION-CODE         (16 bits)   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|               OPTION-LENGTH       (16 bits)   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|               OPTION-DATA         (variable)  |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

**Important EDNS options:**

| Code | Name | RFC | Purpose |
|------|------|-----|---------|
| 3 | NSID | 5001 | Server identity (debugging) |
| 8 | ECS (Client Subnet) | 7871 | Pass client subnet to auth server for geo-DNS |
| 9 | EXPIRE | 7314 | Zone expiry for AXFR-over-TCP-persistent |
| 10 | COOKIE | 7873 | Client+server cookies (anti-spoofing, anti-amplification) |
| 11 | KEEPALIVE | 7828 | TCP keepalive timeout for persistent connections |
| 12 | PADDING | 7830 | Pad responses to resist traffic analysis |
| 13 | CHAIN | 7901 | Request full DNSSEC chain in one query |
| 14 | KEY TAG | 8145 | Signal DNSSEC key tags client trusts |
| 15 | EDE (Extended DNS Errors) | 8914 | Structured error information |
| 65001–65534 | Private use | — | Vendor extensions |

### 9.3 ECS — EDNS Client Subnet (RFC 7871)

Used for CDN/GeoDNS: resolver includes client's IP prefix in query so auth server can return the geographically optimal IP.

```
ECS option RDATA:
  FAMILY:         2 bytes (1=IPv4, 2=IPv6)
  SOURCE PREFIX:  1 byte (bits of client IP included)
  SCOPE PREFIX:   1 byte (bits auth server used in answer; set in response)
  ADDRESS:        variable (source prefix bits, padded to byte boundary)

Example: Client at 203.0.113.45/24 → ECS sends 203.0.113.0/24

Privacy concern: ECS leaks approximate client location to authoritative server.
RFC 7871 §11: resolvers SHOULD anonymize (truncate prefix to /24 or /48).
Opt-out: include ECS with SOURCE PREFIX=0 (signal "no client info")
```

### 9.4 DNS Cookies (RFC 7873)

Lightweight defense against off-path spoofing and amplification:

```
Client cookie: 8 bytes, random, per-server
Server cookie: 8–32 bytes, derived from (client IP, server IP, client cookie, server secret)

First query: Client sends only client cookie
Server responds: Sends server cookie
Subsequent queries: Client sends both; server validates

Benefits:
- Proves client is at the claimed IP (requires routing round-trip)
- Enables stateless challenge-response without state on server
- Servers can give larger responses to cookie-verified clients

RCODE 22 (BADCOOKIE): Server returns this + its cookie to bootstrap the exchange
```

---

## 10. Transport Layer: UDP, TCP, DoT, DoH, DoQ

### 10.1 UDP/53 — The Original Transport

DNS traditionally uses **UDP port 53** for queries. Properties:
- **Stateless**: No connection setup overhead
- **Size limit**: Original limit 512 bytes per RFC 1035. EDNS0 raised this to advertised size (1232 bytes recommended by DNS Flag Day 2020 to fit in one IPv6 fragment; 4096 bytes common).
- **TC bit**: If response exceeds limit, server sets TC=1 and client retries over TCP
- **Fragmentation risk**: Large EDNS0 responses may be fragmented at IP layer. Fragment reassembly vulnerabilities exist.

**Recommended maximum UDP payload**: 1232 bytes (fits in one IPv6 packet without fragmentation: 1280 MTU − 40 IPv6 − 8 UDP = 1232).

### 10.2 TCP/53 — Fallback and Zone Transfer

DNS over TCP is mandatory for:
- Zone transfers (AXFR/IXFR)
- Responses exceeding UDP limit (TC=1 → retry TCP)
- DNSSEC responses (often large due to signatures)
- Reliable transport for dynamic updates (RFC 2136)

TCP DNS message framing: **2-byte length prefix** before each DNS message:
```
[2-byte big-endian message length][DNS message bytes]
[2-byte big-endian message length][DNS message bytes]
...
```
TCP pipelining (RFC 7766): Multiple queries can be sent over one TCP connection without waiting for each response. Responses may arrive out-of-order (matched by TXID).

### 10.3 DNS over TLS (DoT) — RFC 7858, Port 853

DoT wraps DNS-over-TCP in TLS:

```
Client                              Server (port 853)
  |                                    |
  |--- TCP SYN ----------------------->|
  |<-- TCP SYN-ACK --------------------|
  |--- TCP ACK, TLS ClientHello ------>|
  |<-- TLS ServerHello, Certificate ---|
  |--- TLS Finished ------------------>|
  |                                    |
  |--- [2-byte len][DNS query] ------->|  (TLS-encrypted)
  |<-- [2-byte len][DNS response] -----|
  |                                    |
  |--- TCP FIN ----------------------->|

Authentication:
  - Opportunistic: connect to any server at port 853; no cert validation
  - Authenticated: validate server certificate against pinned name or SPKI hash
    (Strict Privacy mode per RFC 8310)

Padding: RFC 7830 EDNS PADDING option; pad to next multiple of 128 bytes
to resist traffic analysis (query length leaks information)
```

**`/etc/systemd/resolved.conf`:**
```ini
[Resolve]
DNS=1.1.1.1#cloudflare-dns.com 8.8.8.8#dns.google
DNSOverTLS=yes
```

### 10.4 DNS over HTTPS (DoH) — RFC 8484, Port 443

DoH encodes DNS messages in HTTP/2 (or HTTP/3) requests over TLS:

```
GET request (wireformat):
  GET /dns-query?dns=<base64url-encoded-dns-message> HTTP/2
  Host: dns.example.com
  Accept: application/dns-message

POST request:
  POST /dns-query HTTP/2
  Host: dns.example.com
  Content-Type: application/dns-message
  Content-Length: <length>
  Accept: application/dns-message
  
  [raw DNS message bytes in body]

Response:
  HTTP/2 200 OK
  Content-Type: application/dns-message
  Cache-Control: max-age=<TTL>
  
  [raw DNS response bytes]
```

DoH advantages:
- Indistinguishable from HTTPS traffic (evades port 53 blocking)
- Benefits from HTTP/2 multiplexing, connection reuse, HTTP caching semantics
- Well-supported in browsers (Firefox, Chrome have built-in DoH)

DoH disadvantages/concerns:
- Centralizes DNS to large operators (Google, Cloudflare)
- Breaks enterprise split-horizon DNS (browsers bypass OS resolver)
- No standard mechanism for enterprise policy enforcement
- HTTP overhead compared to DoT

**Oblivious DoH (ODoH, RFC 9230)**: Adds a proxy tier so the resolver cannot see the client IP:
```
Client → Proxy → Target (resolver)
Proxy sees client IP but not queries.
Target sees queries but not client IP.
Neither sees both.
```

### 10.5 DNS over QUIC (DoQ) — RFC 9250, Port 853

DoQ uses QUIC (UDP+TLS 1.3) as transport:

```
- Eliminates TCP head-of-line blocking
- 0-RTT resumption for repeat connections
- Per-stream flow control
- Connection migration (works across NAT rebinding)
- Each DNS query = one bidirectional QUIC stream
- 2-byte length prefix per DNS message (same as TCP)
- Server QUIC ALPN: "doq"
```

**Transport comparison:**

```
Feature          UDP/53   TCP/53   DoT/853  DoH/443   DoQ/853
-----------------------------------------------------------------
Encryption          No      No       Yes      Yes        Yes
Authentication      No      No       Yes      Yes        Yes  
Latency          Low     Medium    Medium    Medium      Low
HoL blocking      N/A    Yes       Yes       No(H2)      No
Nat traversal     Easy    Easy      Easy      Easy       Easy
Port 53 bypass    No      No        No        Yes        No
OSCP/Revocation   N/A     N/A      Yes       Yes        Yes
0-RTT             N/A     No       No(TLS)  No(TLS)     Yes
Fingerprinting    Hard    Medium    Medium    Hard       Medium
```

---

## 11. DNSSEC — DNS Security Extensions

DNSSEC (RFC 4033/4034/4035) provides **data origin authentication** and **data integrity** for DNS responses using asymmetric cryptography.

### 11.1 What DNSSEC Does and Doesn't Do

**Does:**
- Prove that data comes from the authoritative zone (not spoofed)
- Prove that a name does not exist (authenticated denial of existence)
- Enable DANE (certificate pinning via DNS)

**Does NOT:**
- Encrypt DNS traffic (responses are still cleartext — use DoT/DoH for privacy)
- Protect against SERVFAIL (resolver can't reach authoritative)
- Prevent DoS (amplification attacks are worse with DNSSEC due to larger responses)

### 11.2 Key Types

```
KSK (Key Signing Key):
  DNSKEY flags = 257 (Zone Key + SEP)
  Signs only the DNSKEY RRset
  Longer key (RSA-2048, or ECDSA P-256)
  Updated infrequently (annual or less)
  Published as DS record in parent zone

ZSK (Zone Signing Key):
  DNSKEY flags = 256 (Zone Key only)
  Signs all other RRsets in the zone
  Shorter key acceptable (RSA-1024 or ECDSA P-256)
  Updated frequently (monthly common)
  No DS record in parent; KSK signs the DNSKEY RRset including ZSK

Why two keys:
  - Separates trust anchor operations from operational signing
  - KSK rollover requires parent zone interaction (DS update)
  - ZSK rollover is self-contained within the zone
  - Allows HSM to hold KSK, software to hold ZSK
```

### 11.3 Chain of Trust

```
Root Zone (.) — IANA maintains root trust anchor
  DNSKEY (KSK, alg 8, RSA-2048): published in root zone
  DS in root: self-signed (root is its own trust anchor)
  
  └── .com Zone
        DS record in root zone (hash of .com KSK)
        .com DNSKEY (KSK) verifiable via root DS
        
        └── example.com Zone
              DS record in .com zone (hash of example.com KSK)
              example.com DNSKEY (KSK) verifiable via .com DS
              example.com records signed by ZSK
              DNSKEY RRset (including ZSK) signed by KSK

Validation chain:
  1. Validator knows root KSK (hardcoded trust anchor)
  2. Root zone DNSKEY RRset is signed by root KSK (self-validating)
  3. Root zone DS for .com = hash of .com KSK → validates .com DNSKEY
  4. .com DS for example.com → validates example.com DNSKEY
  5. example.com DNSKEY (ZSK) validates all example.com records
```

```
Trust Anchor
    |
    v
Root KSK  ----signs---->  Root DNSKEY RRset
                                |
                                | contains
                                v
                           Root ZSK  ----signs---->  Root DS RRset
                                                           |
                                                           | DS hash of
                                                           v
                                                    .com KSK  ----signs---->  .com DNSKEY RRset
                                                                                    |
                                                                                    | contains
                                                                                    v
                                                                               .com ZSK  ----signs---->  .com DS RRset
                                                                                                               |
                                                                                                               | DS hash of
                                                                                                               v
                                                                                                        example.com KSK
```

### 11.4 RRSIG Computation

An RRSIG signs an **RRset** (all RRs with the same name, class, and type):

```
Signature Input (canonicalized):
  1. RRSIG RDATA fields (except the signature itself), in wire format
  2. Each RR in the RRset, sorted in canonical DNS name order,
     with TTL replaced by the RRSIG original TTL

Signed data format:
  [Type Covered (2)] [Algorithm (1)] [Labels (1)] [Original TTL (4)]
  [Sig Expiration (4)] [Sig Inception (4)] [Key Tag (2)]
  [Signer's Name (wire-encoded)]
  [RR1 in canonical form]
  [RR2 in canonical form]
  ...

Signature algorithms:
  5:  RSA/SHA-1       (deprecated, must not use)
  7:  RSA/SHA-1 NSEC3 (deprecated)
  8:  RSA/SHA-256     (widely deployed, 2048-bit recommended minimum)
  10: RSA/SHA-512     (large signatures, slower)
  13: ECDSA P-256/SHA-256  (recommended: compact signatures ~64 bytes)
  14: ECDSA P-384/SHA-384  (higher security margin)
  15: Ed25519/SHA-512  (recommended: fast, compact, 64-byte signatures)
  16: Ed448            (highest security margin)
```

### 11.5 Authenticated Denial of Existence: NSEC and NSEC3

**NSEC** (RFC 4034): Proves that no name exists between two adjacent names in canonical order.

```
Zone has: alpha.example.com., gamma.example.com., omega.example.com.

NSEC chain:
  alpha.example.com.  NSEC  gamma.example.com.  A TXT
  gamma.example.com.  NSEC  omega.example.com.  A AAAA MX
  omega.example.com.  NSEC  alpha.example.com.  NS SOA RRSIG NSEC DNSKEY
                             ^-- wraps around to first name

Query for beta.example.com. (doesn't exist):
  Server returns: alpha.example.com. NSEC gamma.example.com.
  This proves: no name between alpha and gamma, so beta doesn't exist

Problem: Zone enumeration! Walk the NSEC chain to list all names.
```

**NSEC3** (RFC 5155): Hashes names before chaining, preventing enumeration.

```
Algorithm: SHA-1 with salt and iteration count
Hash: base32(SHA-1(salt || wire-name || (iterations of SHA-1)))

NSEC3 chain:
  [hash(alpha)] NSEC3  [hash(gamma)]  A TXT
  [hash(gamma)] NSEC3  [hash(omega)]  A AAAA MX

Offline attacks still possible: brute-force common names against hashes.
RFC 9276: Use iterations=0, random salt. High iterations provide false security.

White Lies / Minimal NSEC3 (RFC 7129):
  Return synthetic NSEC3 records covering only the query name.
  Proves non-existence without revealing adjacent names.
  Used by dnsdist, PowerDNS with "NSEC3 minimal" mode.
```

### 11.6 DNSSEC Validation Algorithm (RFC 4035 §5)

```
Validator receives response. For each RRset in Answer/Authority:

1. Find RRSIG(s) covering the RRset
2. Get DNSKEY RRset for the signer (from cache or query)
3. Check RRSIG: 
   a. Algorithm supported?
   b. Signer name = zone name?
   c. Labels count correct (wildcard check)?
   d. Not expired (inception ≤ now ≤ expiration)?
   e. Signature valid over canonicalized RRset?
4. Validate DNSKEY:
   a. Is this DNSKEY trusted? (is it a trust anchor?)
   b. OR: is there a DS record in parent zone matching this DNSKEY?
   c. Is that DS record itself signed and validated?
5. Repeat up the chain to the trust anchor (root KSK)

Outcomes:
  Secure:   Full chain of validated signatures to trust anchor
  Insecure: Zone is unsigned (no DS in parent), chain of unsigned delegations from signed parent
  Bogus:    Signature exists but fails validation → SERVFAIL to client (unless CD=1)
  Indeterminate: Cannot determine (missing data)
```

### 11.7 Key Rollover Procedures

**ZSK Rollover** (no parent interaction needed):

```
Pre-publish method:
  Phase 1 (ZSK1 active):     Publish ZSK2 in DNSKEY RRset (but don't sign with it yet)
                              Wait > max(TTL of DNSKEY RRset)
  Phase 2 (ZSK2 signing):    Start signing with ZSK2, keep ZSK1 in DNSKEY RRset
                              Wait > max(TTL of all signed RRsets + signature validity window)
  Phase 3 (ZSK1 removed):    Remove ZSK1 from DNSKEY RRset

Double-signature method (simpler, more bandwidth):
  Sign with both ZSK1 and ZSK2 during transition period
```

**KSK Rollover** (requires parent DS update — critical operation):

```
Double-KSK method:
  1. Generate new KSK2, publish in DNSKEY RRset alongside KSK1
  2. Submit KSK2's DS hash to parent registrar (out-of-band: web portal/API/EPP)
  3. Wait for parent to publish new DS + TTL propagation
  4. Verify new DS is resolvable from multiple vantage points
  5. Remove old KSK1 from DNSKEY RRset
  6. Ask parent to remove old DS record

Root KSK rollovers (done by IANA):
  RFC 8145: Validators signal which KSK they trust via EDNS KEY TAG option
  2018 root KSK rollover: first root KSK rollover since DNS inception (originally ~3% of resolvers would have broken; IANA delayed due to this)
  Next root KSK is KSK-2024 (alg 13, ECDSA P-256)
```

### 11.8 Algorithm Recommendations (RFC 8624)

```
Algorithm  Sign?        Validate?    Notes
13 (ECDSA P-256/SHA-256)  MUST      MUST     Recommended default
15 (Ed25519)              RECOMMENDED RECOMMENDED  Fastest, smallest signatures
8  (RSA/SHA-256)          MUST NOT   MUST     Widely deployed but MUST NOT use for new zones
5  (RSA/SHA-1)            MUST NOT   NOT RECOMMENDED  Deprecated
14 (ECDSA P-384/SHA-384)  MAY        RECOMMENDED  Higher security margin
16 (Ed448)                MAY        MAY      Experimental
```

---

## 12. DNS Security Threats and Mitigations

### 12.1 Complete Threat Taxonomy

```
THREAT CATEGORY          ATTACK                        MITIGATION
======================== ============================= ===============================
Cache Poisoning          Kaminsky (TXID brute-force)   Source port randomization
                         Birthday paradox attack        DNSSEC
                         Bailiwick violation            Strict bailiwick checking
                         0x20 bypass                    —

Amplification/DDoS       DNS amplification (ANY/DNSKEY) RRL, BCP38, response policy
                         NXNSAttack (RFC 8198 related)  NXNS mitigation patches
                         PRSD (phantom subdomain)        qname-min, QNAME minimization

Eavesdropping            Passive monitoring             DoT, DoH, DoQ
                         Traffic analysis               EDNS PADDING, ODoH

Hijacking                BGP hijack of authoritative    RPKI, multi-path resolution
                         Registrar account compromise   Registrar 2FA, registry lock
                         NXDOMAIN hijacking by ISP      DoH to trusted resolver

Zone Enumeration         NSEC walking                   NSEC3 (with opt-in or white lies)
                         NSEC3 offline brute-force       Random salt, iterations=0 (paradox)

Exfiltration             DNS tunneling                   RPZ, rate limiting, anomaly detection
                         C2 via DNS TXT/CNAME            DNS inspection proxies, ML models

DNSSEC-specific          Signature expiry (key ops fail) Key management automation
                         Algorithm downgrade             Strict algorithm requirement
                         Replay attack                   Signature inception/expiration window
                         Key compromise                  Fast rollover procedures

Resolver-based           SERVFAIL amplification          Negative caching, qname-minimization
                         Resolver cache poisoning        DNSSEC validation
                         Lame delegation loops           Max iteration limits

Application-layer        DNS rebinding                   DNS rebind protection (check A against private)
                         Homograph attacks (IDN)         IDNA2008, visual similarity detection
                         Subdomain takeover              Scan for dangling CNAMEs/NS
```

### 12.2 DNS Amplification Attack

**Mechanism**: Attacker sends UDP queries to open resolvers, spoofing victim's IP as source. Resolver sends large response to victim.

```
Amplification factor examples:
  ANY query to ANY resolver:      up to 73x amplification (512→37,500 bytes)
  DNSKEY query for root zone:     up to 22x (40→880 bytes)
  TXT query for well-known zones: up to 45x

Attack flow:
Attacker (spoofed src=victim) → Open resolver → Large response → Victim
                 small query                     large answer

Mitigations:
1. BCP38 (RFC 2827): ISPs filter packets with spoofed source IPs (ingress filtering)
2. Response Rate Limiting (RRL, RFC 8198 related): Limit response rate per source IP
3. DNS Cookies: Require valid cookie for large responses
4. RFC 8482: Synthesize minimal response for ANY queries
5. Disable open recursion: only serve your own clients
```

**RRL configuration (BIND):**
```
rate-limit {
    responses-per-second 10;
    window 5;
    slip 2;  /* 1 in 2 responses is a truncated answer instead of dropped */
    errors-per-second 5;
    nxdomains-per-second 5;
    min-table-size 500;
    max-table-size 20000;
};
```

### 12.3 DNS Tunneling / Data Exfiltration

Attackers encode data in DNS names and TXT/CNAME responses to bypass firewalls:

```
C2 channel example (iodine, dns2tcp, dnscat2):

Attacker controls: tunnel.attacker.com authoritative server

Victim (inside firewall):
  DNS query: <base64-encoded-data>.tunnel.attacker.com TXT
  → passes through corporate DNS (only port 53 open)
  
Authoritative server:
  Decodes base64 data from QNAME
  Encodes response in TXT RDATA
  
Throughput: ~500–3000 bps (enough for shell commands, slow file exfil)

Detection indicators:
  - High entropy in QNAME labels (base64/base32)
  - Unusually long subdomain labels (>50 chars)
  - High query rate to single second-level domain
  - TXT queries (rare in normal traffic)
  - Long TXT records in responses
  - Domains registered recently (WHOIS age < 30 days)
  - No matching A record for queried domain

Mitigations:
  RPZ (Response Policy Zones): block known C2 domains
  DNS firewall / inspection proxy with ML models
  Anomaly detection: entropy, label length, query rate per domain
  FQDN allowlisting in highly controlled environments
```

### 12.4 DNS Rebinding Attack

Exploits browser same-origin policy using short-TTL records:

```
1. Attacker registers attack.com with NS pointing to attacker-controlled server
2. Victim visits http://attack.com (browser resolves to attacker's server: 203.0.113.1)
3. Attacker's page runs JavaScript with origin "http://attack.com"
4. TTL expires (attacker uses TTL=1)
5. Attacker's NS returns NEW answer: 192.168.1.1 (victim's internal router)
6. Browser makes XHR to http://attack.com/api → resolves to 192.168.1.1
7. Same-origin policy allows this (host:port still "attack.com:80")
8. Attacker's JS now talks to victim's internal router, cloud metadata API, etc.

Attack targets: AWS IMDS (169.254.169.254), internal admin panels, IoT devices

Mitigations:
  - DNS rebind protection in resolvers (reject private IPs for public domain queries)
  - BIND: deny-answer-addresses { 192.168.0.0/16; 10.0.0.0/8; 172.16.0.0/12; };
  - Unbound: private-address directive
  - Application layer: Host header validation, require authentication
  - Network: block 169.254.169.254 on egress for untrusted workloads
  - IMDS v2 (AWS): requires PUT to obtain token (mitigates SSRF-based rebinding)
```

### 12.5 QNAME Minimization (RFC 7816)

Traditional resolvers send the full QNAME to all servers in the chain, leaking the full query to root and TLD servers.

```
Traditional (privacy-leaking):
  Root server receives:     A www.example.com
  .com TLD receives:        A www.example.com
  example.com auth receives: A www.example.com

QNAME minimization:
  Root server receives:     NS com.  (just asks about .com delegation)
  .com TLD receives:        NS example.com.  (just asks about SLD delegation)
  example.com auth receives: A www.example.com  (only final server sees full name)

Reduces privacy leakage. Small performance cost (sometimes one extra round-trip).
Enabled by default in Unbound 1.7+, Knot Resolver.
```

### 12.6 NXNSAttack (CVE-2020-8616)

Exploits DNS delegation mechanism to amplify queries to victim nameservers:

```
Attacker controls: evil.com zone, attacker-ns.evil.com

Attacker sends query for:
  subdomain.evil.com
  
evil.com zone returns: NS ns1.victim.com., ns2.victim.com., ns3.victim.com. ... (many fake NS)

Resolver dutifully queries ALL listed nameservers!
Each query hits victim's nameserver → amplification of 1 query to N queries.

Fix (RFC 8198 / patched resolvers):
  Limit NS referral fan-out
  Validate NS names are within the delegated zone or known to exist
  Rate-limit repeated referral loops
```

---

## 13. Split-Horizon DNS, Views, and RPZ

### 13.1 Split-Horizon DNS

Different responses for same query based on client's source IP. Used for:
- Internal vs external views (intranet vs internet)
- Geographic load balancing
- Regulatory compliance (data sovereignty)

```
BIND named.conf views example:

view "internal" {
    match-clients { 10.0.0.0/8; 172.16.0.0/12; 192.168.0.0/16; };
    recursion yes;
    zone "example.com" {
        type master;
        file "/etc/bind/zones/internal/example.com";
    };
    // Internal view: app.example.com → 10.0.1.5 (private IP)
};

view "external" {
    match-clients { any; };
    recursion no;
    zone "example.com" {
        type master;
        file "/etc/bind/zones/external/example.com";
    };
    // External view: app.example.com → 203.0.113.10 (public IP)
};
```

**EDNS Client Subnet (ECS)** enables split-horizon by IP from recursive resolvers:
The resolver passes client IP prefix; the authoritative server uses it for view selection.

### 13.2 Response Policy Zones (RPZ, RFC draft)

RPZ allows resolvers to intercept and modify DNS responses based on policy zones. Used for:
- Malware domain blocking
- Parental controls
- C2 blocking (threat intel feeds)
- NXDOMAIN injection / sinkholing

```
RPZ rule types:
  QNAME policy:     triggers on queried name
  IP policy:        triggers on returned IP address
  NSDNAME policy:   triggers on delegation NS name
  NSIP policy:      triggers on NS IP address
  CLIENT-IP policy: triggers on querying client's IP

RPZ actions:
  NXDOMAIN (CNAME .)     - return NXDOMAIN (block)
  NODATA (CNAME *.)      - return empty answer
  PASSTHRU (CNAME rpz-passthru.) - bypass policy
  DROP (CNAME rpz-drop.) - drop packet silently
  Local data             - return custom A/TXT/etc.

Example RPZ zone file:
; Block malware domain
malware.example.com.       CNAME  .   ; NXDOMAIN
*.malware.example.com.     CNAME  .   ; block subdomains too

; Redirect phishing
phishing.example.com.      A  198.51.100.1   ; sinkhole IP

BIND named.conf:
response-policy {
    zone "rpz.blocklist.internal" policy nxdomain;
    zone "rpz.allowlist.internal" policy passthru;  /* allowlist checked first? no — order matters */
} qname-wait-recurse no;

Note: RPZ processing order matters. First matching rule wins.
DNS Firewall (ISC) / Cloudflare Gateway / NextDNS use RPZ under the hood.
```

---

## 14. DNS in Kubernetes and Cloud Platforms

### 14.1 Kubernetes DNS (CoreDNS)

Every Kubernetes cluster runs **CoreDNS** as the in-cluster DNS resolver (replaced kube-dns as default since K8s 1.13).

```
Architecture:

Pod
 |
 | /etc/resolv.conf:
 |   nameserver 10.96.0.10  (ClusterIP of kube-dns Service)
 |   search default.svc.cluster.local svc.cluster.local cluster.local
 |   options ndots:5
 |
 v
CoreDNS (Deployment, 2 replicas by default)
 | ClusterIP: 10.96.0.10
 |
 +-- kubernetes plugin: serves in-cluster names
 |     Endpoints -> A records
 |     Services -> A/AAAA/SRV records
 |
 +-- forward plugin: external queries forwarded to /etc/resolv.conf of node
       (or explicit upstream: 8.8.8.8, 1.1.1.1)
```

**In-cluster DNS naming convention:**

```
Service:
  <service-name>.<namespace>.svc.cluster.local.
  → ClusterIP A record

  Example: my-service.default.svc.cluster.local.

Headless Service (clusterIP: None):
  → Returns A records for each Pod IP directly
  → Enables StatefulSet stable DNS names:
    <pod-name>.<service-name>.<namespace>.svc.cluster.local.
    web-0.my-service.default.svc.cluster.local.

External Services (ExternalName):
  → Returns CNAME to external name

SRV records:
  _<port-name>._<protocol>.<service>.<namespace>.svc.cluster.local.
  _http._tcp.my-service.default.svc.cluster.local.
  → PRIORITY=0, WEIGHT=100, PORT=<port>, TARGET=<pod-dns>
```

**ndots:5 security implications:**

```
Pod queries: "redis" (no dots)
  Search domains tried in order:
  1. redis.default.svc.cluster.local
  2. redis.svc.cluster.local
  3. redis.cluster.local
  4. redis.  <- absolute query

With ndots:5, names with fewer than 5 dots try search domains FIRST.
Problem: An attacker who can inject records into cluster.local DNS
can intercept queries for external names.

Example: If pod queries "evil.attacker.com" (2 dots < 5):
  Tries: evil.attacker.com.default.svc.cluster.local. FIRST
  If resolver returns answer for this → used instead of real IP

Mitigation: 
  Use FQDNs (trailing dot): "redis.default.svc.cluster.local."
  Or set ndots:1 in pods that only need in-cluster DNS
  Explicit search domain override per pod:
    dnsConfig:
      options:
        - name: ndots
          value: "1"
```

**CoreDNS Corefile:**
```
.:53 {
    errors
    health {
        lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure         # trust pod IP in request (default; use 'verified' for security)
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153          # metrics endpoint
    forward . /etc/resolv.conf {
        max_concurrent 1000
    }
    cache 30 {
        denial 5              # cache NXDOMAIN for 5s
        success 30
    }
    loop                      # detect loops
    reload                    # hot-reload Corefile
    loadbalance               # round-robin A records
}
```

**Security hardening for CoreDNS:**
```yaml
# Corefile with security improvements
.:53 {
    errors
    health
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods verified   # not insecure — verify pod IP against API server
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    # RPZ-style blocking via rewrite
    rewrite name regex (.*)\.malicious\.com blocked.example.com
    
    # Forward only to specific trusted resolvers over DoT
    forward . tls://1.1.1.1 tls://8.8.8.8 {
        tls_servername cloudflare-dns.com
        health_check 5s
    }
    cache 30
    loop
    reload
    loadbalance
    # Log queries (for audit)
    log . {
        class denial error
    }
}
```

### 14.2 AWS Route 53

Route 53 is AWS's managed DNS service. Key features:

```
Resolver architecture:
  VPC DNS: <VPC CIDR base> + 2 (e.g., 10.0.0.2 in 10.0.0.0/16)
  Also reachable at 169.254.169.253 and fd00:ec2::253

Route 53 Resolver:
  Inbound Endpoint:  External → AWS VPC DNS (hybrid cloud)
  Outbound Endpoint: AWS → External DNS (conditional forwarding)
  
  Forwarding rules:
    example.internal → on-prem DNS 10.0.0.5
    amazonaws.com → Route 53 (default)
    . → 8.8.8.8 (fallback)

Route 53 record types specific to AWS:
  Alias records: Maps to AWS resources (ELB, CloudFront, S3) 
                 No TTL (uses target's TTL)
                 Free queries (unlike CNAME which incurs resolution cost)

Routing policies:
  Simple:          One record set (or weighted if multiple values)
  Weighted:        Distribute traffic by percentage weight
  Latency-based:   Route to lowest-latency region
  Geolocation:     Route by client geography (continent/country)
  Geoproximity:    Route by geographic proximity with bias
  Failover:        Active-passive (health checks required)
  Multivalue:      Return up to 8 healthy records (not a load balancer substitute)
  IP-based:        Route by client CIDR (CIDR → endpoint mapping)

Health checks:
  HTTP/HTTPS/TCP endpoint checks
  CloudWatch alarm state
  Calculated (aggregate of other checks)
  Route 53 withdraws unhealthy records from DNS responses

DNSSEC: Route 53 supports DNSSEC signing for public hosted zones.
Private hosted zones: No DNSSEC (internal network).
```

### 14.3 GCP Cloud DNS

```
Default resolver: 169.254.169.254:53 (metadata server) → routes to 8.8.8.8 by default
Cloud DNS: Fully managed authoritative + private zones
  Private zones: VPC-scoped, peerable across VPCs
  Forwarding zones: Route queries to on-prem or external DNS
  Peering zones: Share zones across VPC networks

GKE node DNS: Uses Cloud DNS or kube-dns depending on cluster config
  Cloud DNS for GKE: Full resolution via Cloud DNS + CoreDNS in-cluster
```

### 14.4 Azure DNS / Private Resolver

```
Default DNS: 168.63.129.16 (platform DNS)
Azure DNS Zones: Authoritative DNS management
Azure Private DNS: Private zones linked to VNets
Azure DNS Private Resolver (2022):
  Inbound Endpoint: External → Azure Private DNS
  Outbound Endpoint: Azure → on-prem/external
  DNS Forwarding Ruleset: Conditional forwarding rules

Hybrid DNS patterns:
  Hub VNet has Private Resolver
  Spoke VNets peer to Hub
  On-prem → Azure via ExpressRoute + Inbound Endpoint
  Azure → On-prem via Outbound Endpoint + Forwarding Rules
```

---

## 15. Implementation in C

### 15.1 DNS Stub Resolver in C

Complete, production-grade DNS stub resolver implementing query building, wire-format parsing, EDNS0, and DNSSEC AD bit checking.

```c
/* dns_resolver.c - Complete DNS stub resolver
 * Implements: RFC 1035 wire format, EDNS0 (RFC 6891), DNSSEC AD bit
 * Build: gcc -O2 -Wall -Wextra -o dns_resolver dns_resolver.c
 * Usage: ./dns_resolver <hostname> [A|AAAA|MX|TXT|NS]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <time.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>

/* ---- Constants ---- */
#define DNS_PORT            53
#define DNS_MAX_UDP_SIZE    512
#define DNS_EDNS_UDP_SIZE   4096
#define DNS_MAX_NAME_LEN    255
#define DNS_MAX_LABEL_LEN   63
#define DNS_HEADER_SIZE     12
#define DNS_TIMEOUT_SEC     5
#define DNS_MAX_RETRIES     3
#define DNS_MAX_CNAME_DEPTH 8
#define DNS_MAX_POINTER_DEPTH 32

/* ---- DNS Record Types ---- */
#define DNS_TYPE_A      1
#define DNS_TYPE_NS     2
#define DNS_TYPE_CNAME  5
#define DNS_TYPE_SOA    6
#define DNS_TYPE_MX     15
#define DNS_TYPE_TXT    16
#define DNS_TYPE_AAAA   28
#define DNS_TYPE_SRV    33
#define DNS_TYPE_OPT    41
#define DNS_TYPE_DS     43
#define DNS_TYPE_RRSIG  46
#define DNS_TYPE_NSEC   47
#define DNS_TYPE_DNSKEY 48
#define DNS_TYPE_ANY    255

#define DNS_CLASS_IN    1
#define DNS_CLASS_ANY   255

/* ---- DNS Opcodes ---- */
#define DNS_OPCODE_QUERY  0
#define DNS_OPCODE_STATUS 2
#define DNS_OPCODE_NOTIFY 4
#define DNS_OPCODE_UPDATE 5

/* ---- DNS RCODEs ---- */
#define DNS_RCODE_NOERROR  0
#define DNS_RCODE_FORMERR  1
#define DNS_RCODE_SERVFAIL 2
#define DNS_RCODE_NXDOMAIN 3
#define DNS_RCODE_NOTIMP   4
#define DNS_RCODE_REFUSED  5

/* ---- Flag bit positions in flags word (network byte order applied) ---- */
#define DNS_FLAG_QR     (1 << 15)  /* 0=query 1=response */
#define DNS_FLAG_AA     (1 << 10)  /* authoritative answer */
#define DNS_FLAG_TC     (1 << 9)   /* truncated */
#define DNS_FLAG_RD     (1 << 8)   /* recursion desired */
#define DNS_FLAG_RA     (1 << 7)   /* recursion available */
#define DNS_FLAG_Z      (1 << 6)   /* reserved */
#define DNS_FLAG_AD     (1 << 5)   /* authentic data (DNSSEC) */
#define DNS_FLAG_CD     (1 << 4)   /* checking disabled (DNSSEC) */
#define DNS_RCODE_MASK  0x000F

/* ---- Wire Format Structures ---- */
/* All fields in network byte order when in struct, 
 * use read_u16/read_u32 to decode from buffer */

typedef struct {
    uint8_t  buf[DNS_EDNS_UDP_SIZE + 512];
    size_t   len;
} dns_buf_t;

typedef struct {
    uint16_t id;
    uint16_t flags;
    uint16_t qdcount;
    uint16_t ancount;
    uint16_t nscount;
    uint16_t arcount;
} dns_header_t;

typedef struct {
    char     name[DNS_MAX_NAME_LEN + 1];
    uint16_t type;
    uint16_t class;
    uint32_t ttl;
    uint16_t rdlength;
    const uint8_t *rdata;  /* pointer into original buffer */
} dns_rr_t;

typedef struct {
    char     qname[DNS_MAX_NAME_LEN + 1];
    uint16_t qtype;
    uint16_t qclass;
} dns_question_t;

typedef struct {
    dns_header_t   header;
    dns_question_t questions[1];
    dns_rr_t       answers[32];
    dns_rr_t       authority[16];
    dns_rr_t       additional[16];
    int            nquestions;
    int            nanswers;
    int            nauthority;
    int            nadditional;
    bool           ad_bit;  /* DNSSEC authenticated */
} dns_message_t;

/* ---- Utility: Safe buffer readers ---- */
static inline uint16_t read_u16(const uint8_t *p) {
    return (uint16_t)((p[0] << 8) | p[1]);
}
static inline uint32_t read_u32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8)  |  (uint32_t)p[3];
}
static inline void write_u16(uint8_t *p, uint16_t v) {
    p[0] = (v >> 8) & 0xFF;
    p[1] = v & 0xFF;
}
static inline void write_u32(uint8_t *p, uint32_t v) {
    p[0] = (v >> 24) & 0xFF;
    p[1] = (v >> 16) & 0xFF;
    p[2] = (v >> 8)  & 0xFF;
    p[3] = v & 0xFF;
}

/* ---- Name encoding: "www.example.com" → wire format ---- */
static int dns_encode_name(const char *name, uint8_t *buf, size_t bufsize) {
    size_t pos = 0;
    const char *p = name;
    
    while (*p) {
        const char *dot = strchr(p, '.');
        size_t label_len = dot ? (size_t)(dot - p) : strlen(p);
        
        if (label_len == 0 || label_len > DNS_MAX_LABEL_LEN) return -1;
        if (pos + 1 + label_len >= bufsize) return -1;
        
        buf[pos++] = (uint8_t)label_len;
        memcpy(buf + pos, p, label_len);
        pos += label_len;
        
        p += label_len;
        if (*p == '.') p++;
    }
    
    if (pos + 1 >= bufsize) return -1;
    buf[pos++] = 0x00;  /* root label */
    return (int)pos;
}

/* ---- Name decoding: wire format → "www.example.com" (with compression) ---- */
/* Returns bytes consumed from *buf_pos (NOT following pointers) */
static int dns_decode_name(
    const uint8_t *msg, size_t msglen,
    size_t *buf_pos,
    char *out, size_t outsize)
{
    size_t pos = *buf_pos;
    size_t out_pos = 0;
    int pointer_count = 0;
    bool jumped = false;
    size_t return_pos = 0;
    
    out[0] = '\0';
    
    while (pos < msglen) {
        uint8_t len = msg[pos];
        
        if ((len & 0xC0) == 0xC0) {
            /* Pointer compression */
            if (pos + 1 >= msglen) return -1;
            if (++pointer_count > DNS_MAX_POINTER_DEPTH) return -1;  /* loop detection */
            
            size_t ptr_offset = ((size_t)(len & 0x3F) << 8) | msg[pos + 1];
            if (ptr_offset >= msglen) return -1;
            
            if (!jumped) {
                return_pos = pos + 2;
                jumped = true;
            }
            pos = ptr_offset;
            continue;
        }
        
        if ((len & 0xC0) != 0x00) return -1;  /* reserved, invalid */
        
        pos++;  /* advance past length byte */
        
        if (len == 0) break;  /* root label = end */
        
        if (pos + len > msglen) return -1;
        if (out_pos + len + 1 >= outsize) return -1;  /* +1 for dot */
        
        if (out_pos > 0) out[out_pos++] = '.';
        memcpy(out + out_pos, msg + pos, len);
        out_pos += len;
        out[out_pos] = '\0';
        pos += len;
    }
    
    *buf_pos = jumped ? return_pos : pos;
    return 0;
}

/* ---- Parse a single RR from message buffer ---- */
static int dns_parse_rr(
    const uint8_t *msg, size_t msglen,
    size_t *pos, dns_rr_t *rr)
{
    /* Parse owner name */
    if (dns_decode_name(msg, msglen, pos, rr->name, sizeof(rr->name)) < 0)
        return -1;
    
    if (*pos + 10 > msglen) return -1;  /* type+class+ttl+rdlength = 10 bytes */
    
    rr->type     = read_u16(msg + *pos);     *pos += 2;
    rr->class    = read_u16(msg + *pos);     *pos += 2;
    rr->ttl      = read_u32(msg + *pos);     *pos += 4;
    rr->rdlength = read_u16(msg + *pos);     *pos += 2;
    
    if (*pos + rr->rdlength > msglen) return -1;
    rr->rdata = msg + *pos;
    *pos += rr->rdlength;
    
    return 0;
}

/* ---- Parse complete DNS message ---- */
static int dns_parse_message(
    const uint8_t *buf, size_t buflen,
    dns_message_t *msg)
{
    if (buflen < DNS_HEADER_SIZE) return -1;
    
    /* Parse header */
    msg->header.id      = read_u16(buf + 0);
    msg->header.flags   = read_u16(buf + 2);
    msg->header.qdcount = read_u16(buf + 4);
    msg->header.ancount = read_u16(buf + 6);
    msg->header.nscount = read_u16(buf + 8);
    msg->header.arcount = read_u16(buf + 10);
    
    msg->ad_bit = (msg->header.flags & DNS_FLAG_AD) != 0;
    
    size_t pos = DNS_HEADER_SIZE;
    
    /* Parse questions */
    msg->nquestions = 0;
    int qdcount = msg->header.qdcount;
    if (qdcount > 1) qdcount = 1;  /* sanity limit */
    
    for (int i = 0; i < qdcount; i++) {
        if (msg->nquestions >= (int)(sizeof(msg->questions)/sizeof(msg->questions[0])))
            break;
        dns_question_t *q = &msg->questions[msg->nquestions];
        if (dns_decode_name(buf, buflen, &pos, q->qname, sizeof(q->qname)) < 0)
            return -1;
        if (pos + 4 > buflen) return -1;
        q->qtype  = read_u16(buf + pos); pos += 2;
        q->qclass = read_u16(buf + pos); pos += 2;
        msg->nquestions++;
    }
    
    /* Parse answers */
    msg->nanswers = 0;
    int ancount = msg->header.ancount;
    if (ancount > 32) ancount = 32;
    for (int i = 0; i < ancount; i++) {
        if (dns_parse_rr(buf, buflen, &pos, &msg->answers[msg->nanswers]) < 0)
            break;
        msg->nanswers++;
    }
    
    /* Parse authority */
    msg->nauthority = 0;
    int nscount = msg->header.nscount;
    if (nscount > 16) nscount = 16;
    for (int i = 0; i < nscount; i++) {
        if (dns_parse_rr(buf, buflen, &pos, &msg->authority[msg->nauthority]) < 0)
            break;
        msg->nauthority++;
    }
    
    /* Parse additional */
    msg->nadditional = 0;
    int arcount = msg->header.arcount;
    if (arcount > 16) arcount = 16;
    for (int i = 0; i < arcount; i++) {
        if (dns_parse_rr(buf, buflen, &pos, &msg->additional[msg->nadditional]) < 0)
            break;
        msg->nadditional++;
    }
    
    return 0;
}

/* ---- Build DNS query with EDNS0 OPT record ---- */
static int dns_build_query(
    uint16_t id, const char *name, uint16_t qtype,
    bool want_dnssec, uint8_t *buf, size_t bufsize)
{
    if (bufsize < DNS_HEADER_SIZE + DNS_MAX_NAME_LEN + 16) return -1;
    
    memset(buf, 0, DNS_HEADER_SIZE);
    
    /* Header */
    write_u16(buf + 0, id);
    write_u16(buf + 2, DNS_FLAG_RD);  /* RD=1, everything else 0 for query */
    write_u16(buf + 4, 1);            /* QDCOUNT=1 */
    write_u16(buf + 6, 0);            /* ANCOUNT=0 */
    write_u16(buf + 8, 0);            /* NSCOUNT=0 */
    write_u16(buf + 10, 1);           /* ARCOUNT=1 (OPT record) */
    
    size_t pos = DNS_HEADER_SIZE;
    
    /* Question QNAME */
    int name_len = dns_encode_name(name, buf + pos, bufsize - pos);
    if (name_len < 0) return -1;
    pos += (size_t)name_len;
    
    if (pos + 4 > bufsize) return -1;
    write_u16(buf + pos, qtype);     pos += 2;  /* QTYPE */
    write_u16(buf + pos, DNS_CLASS_IN); pos += 2; /* QCLASS */
    
    /* EDNS0 OPT record in Additional section */
    /* NAME = 0x00 (root) */
    if (pos + 11 > bufsize) return -1;
    buf[pos++] = 0x00;                            /* NAME = root */
    write_u16(buf + pos, DNS_TYPE_OPT); pos += 2; /* TYPE = OPT */
    write_u16(buf + pos, DNS_EDNS_UDP_SIZE); pos += 2; /* CLASS = requestor's UDP payload size */
    buf[pos++] = 0x00;                            /* EXTENDED RCODE = 0 */
    buf[pos++] = 0x00;                            /* VERSION = 0 */
    
    /* Z field: DO bit (DNSSEC OK) in bit 15 of the 16-bit Z */
    uint16_t z = want_dnssec ? 0x8000 : 0x0000;
    write_u16(buf + pos, z); pos += 2;
    
    write_u16(buf + pos, 0); pos += 2;  /* RDLENGTH = 0 (no options) */
    
    return (int)pos;
}

/* ---- Print RDATA in human-readable form ---- */
static void dns_print_rdata(const dns_rr_t *rr, const uint8_t *msg, size_t msglen) {
    const uint8_t *rd = rr->rdata;
    size_t rdlen = rr->rdlength;
    
    switch (rr->type) {
        case DNS_TYPE_A: {
            if (rdlen < 4) { printf("<invalid A>"); return; }
            printf("%d.%d.%d.%d", rd[0], rd[1], rd[2], rd[3]);
            break;
        }
        case DNS_TYPE_AAAA: {
            if (rdlen < 16) { printf("<invalid AAAA>"); return; }
            char addr[INET6_ADDRSTRLEN];
            inet_ntop(AF_INET6, rd, addr, sizeof(addr));
            printf("%s", addr);
            break;
        }
        case DNS_TYPE_CNAME:
        case DNS_TYPE_NS:
        case DNS_TYPE_PTR: {
            char name[DNS_MAX_NAME_LEN + 1];
            size_t pos = (size_t)(rd - msg);
            dns_decode_name(msg, msglen, &pos, name, sizeof(name));
            printf("%s", name);
            break;
        }
        case DNS_TYPE_MX: {
            if (rdlen < 3) { printf("<invalid MX>"); return; }
            uint16_t pref = read_u16(rd);
            char name[DNS_MAX_NAME_LEN + 1];
            size_t pos = (size_t)(rd - msg) + 2;
            dns_decode_name(msg, msglen, &pos, name, sizeof(name));
            printf("%u %s", pref, name);
            break;
        }
        case DNS_TYPE_TXT: {
            size_t i = 0;
            printf("\"");
            while (i < rdlen) {
                uint8_t slen = rd[i++];
                if (i + slen > rdlen) break;
                for (uint8_t j = 0; j < slen; j++) {
                    unsigned char c = rd[i + j];
                    if (c >= 32 && c < 127 && c != '"' && c != '\\')
                        putchar(c);
                    else
                        printf("\\x%02x", c);
                }
                i += slen;
                if (i < rdlen) printf("\" \"");  /* multiple strings */
            }
            printf("\"");
            break;
        }
        case DNS_TYPE_SOA: {
            char mname[DNS_MAX_NAME_LEN + 1], rname[DNS_MAX_NAME_LEN + 1];
            size_t pos = (size_t)(rd - msg);
            dns_decode_name(msg, msglen, &pos, mname, sizeof(mname));
            dns_decode_name(msg, msglen, &pos, rname, sizeof(rname));
            if (pos + 20 > msglen) { printf("<invalid SOA>"); return; }
            uint32_t serial  = read_u32(msg + pos);     pos += 4;
            uint32_t refresh = read_u32(msg + pos);     pos += 4;
            uint32_t retry   = read_u32(msg + pos);     pos += 4;
            uint32_t expire  = read_u32(msg + pos);     pos += 4;
            uint32_t minimum = read_u32(msg + pos);
            printf("%s %s %u %u %u %u %u",
                   mname, rname, serial, refresh, retry, expire, minimum);
            break;
        }
        case DNS_TYPE_SRV: {
            if (rdlen < 7) { printf("<invalid SRV>"); return; }
            uint16_t prio   = read_u16(rd);
            uint16_t weight = read_u16(rd + 2);
            uint16_t port   = read_u16(rd + 4);
            char target[DNS_MAX_NAME_LEN + 1];
            size_t pos = (size_t)(rd - msg) + 6;
            dns_decode_name(msg, msglen, &pos, target, sizeof(target));
            printf("%u %u %u %s", prio, weight, port, target);
            break;
        }
        default:
            printf("<type=%u rdlen=%u bytes>", rr->type, rr->rdlength);
            /* hex dump first 16 bytes */
            for (size_t i = 0; i < rdlen && i < 16; i++)
                printf(" %02x", rd[i]);
            if (rdlen > 16) printf("...");
    }
}

/* ---- Get type name string ---- */
static const char *dns_type_name(uint16_t type) {
    switch (type) {
        case DNS_TYPE_A:      return "A";
        case DNS_TYPE_NS:     return "NS";
        case DNS_TYPE_CNAME:  return "CNAME";
        case DNS_TYPE_SOA:    return "SOA";
        case DNS_TYPE_MX:     return "MX";
        case DNS_TYPE_TXT:    return "TXT";
        case DNS_TYPE_AAAA:   return "AAAA";
        case DNS_TYPE_SRV:    return "SRV";
        case DNS_TYPE_OPT:    return "OPT";
        case DNS_TYPE_DNSKEY: return "DNSKEY";
        case DNS_TYPE_RRSIG:  return "RRSIG";
        case DNS_TYPE_NSEC:   return "NSEC";
        case DNS_TYPE_DS:     return "DS";
        case DNS_TYPE_ANY:    return "ANY";
        default: {
            static char buf[16];
            snprintf(buf, sizeof(buf), "TYPE%u", type);
            return buf;
        }
    }
}

/* ---- Get RCODE name ---- */
static const char *dns_rcode_name(uint16_t rcode) {
    switch (rcode & DNS_RCODE_MASK) {
        case 0: return "NOERROR";
        case 1: return "FORMERR";
        case 2: return "SERVFAIL";
        case 3: return "NXDOMAIN";
        case 4: return "NOTIMP";
        case 5: return "REFUSED";
        default: return "UNKNOWN";
    }
}

/* ---- Resolve: send query, receive response, parse, print ---- */
static int dns_resolve(
    const char *resolver_ip, uint16_t resolver_port,
    const char *name, uint16_t qtype, bool want_dnssec)
{
    /* Create UDP socket */
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) { perror("socket"); return -1; }
    
    /* Set timeout */
    struct timeval tv = { .tv_sec = DNS_TIMEOUT_SEC, .tv_usec = 0 };
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    
    /* Resolver address */
    struct sockaddr_in resolver_addr;
    memset(&resolver_addr, 0, sizeof(resolver_addr));
    resolver_addr.sin_family = AF_INET;
    resolver_addr.sin_port = htons(resolver_port);
    if (inet_pton(AF_INET, resolver_ip, &resolver_addr.sin_addr) != 1) {
        fprintf(stderr, "Invalid resolver IP: %s\n", resolver_ip);
        close(sock); return -1;
    }
    
    /* Random transaction ID */
    srand((unsigned)time(NULL) ^ (unsigned)getpid());
    uint16_t txid = (uint16_t)rand();
    
    /* Build query */
    uint8_t query_buf[DNS_EDNS_UDP_SIZE];
    int query_len = dns_build_query(txid, name, qtype, want_dnssec,
                                    query_buf, sizeof(query_buf));
    if (query_len < 0) {
        fprintf(stderr, "Failed to build query\n");
        close(sock); return -1;
    }
    
    printf(";; Query: %s %s → %s:%u\n", name, dns_type_name(qtype),
           resolver_ip, resolver_port);
    printf(";; TXID: 0x%04X  EDNS0: yes  DO: %s\n\n",
           txid, want_dnssec ? "yes" : "no");
    
    /* Send query with retries */
    uint8_t resp_buf[DNS_EDNS_UDP_SIZE + 512];
    ssize_t resp_len = -1;
    
    for (int attempt = 0; attempt < DNS_MAX_RETRIES; attempt++) {
        ssize_t sent = sendto(sock, query_buf, (size_t)query_len, 0,
                              (struct sockaddr*)&resolver_addr,
                              sizeof(resolver_addr));
        if (sent < 0) { perror("sendto"); continue; }
        
        struct sockaddr_in from_addr;
        socklen_t from_len = sizeof(from_addr);
        resp_len = recvfrom(sock, resp_buf, sizeof(resp_buf), 0,
                            (struct sockaddr*)&from_addr, &from_len);
        if (resp_len > 0) break;
        
        fprintf(stderr, ";; Timeout/error on attempt %d, retrying...\n", attempt + 1);
    }
    
    close(sock);
    
    if (resp_len <= 0) {
        fprintf(stderr, ";; No response from %s:%u\n", resolver_ip, resolver_port);
        return -1;
    }
    
    /* Validate response TXID matches */
    if (resp_len < 2 || read_u16(resp_buf) != txid) {
        fprintf(stderr, ";; TXID mismatch (possible spoofing attempt)\n");
        return -1;
    }
    
    /* Parse message */
    dns_message_t msg;
    memset(&msg, 0, sizeof(msg));
    if (dns_parse_message(resp_buf, (size_t)resp_len, &msg) < 0) {
        fprintf(stderr, ";; Failed to parse response\n");
        return -1;
    }
    
    /* Check TC bit — should retry over TCP */
    if (msg.header.flags & DNS_FLAG_TC) {
        fprintf(stderr, ";; Response truncated (TC=1). Should retry over TCP.\n");
        /* In production: implement TCP fallback here */
    }
    
    /* Print response header */
    uint16_t flags = msg.header.flags;
    uint16_t rcode = flags & DNS_RCODE_MASK;
    
    printf(";; ->>HEADER<<- opcode: QUERY, status: %s, id: %u\n",
           dns_rcode_name(rcode), msg.header.id);
    printf(";; flags: %s%s%s%s%s%s%s ; QUERY: %d, ANSWER: %d, AUTHORITY: %d, ADDITIONAL: %d\n",
           (flags & DNS_FLAG_QR) ? "qr " : "",
           (flags & DNS_FLAG_AA) ? "aa " : "",
           (flags & DNS_FLAG_TC) ? "tc " : "",
           (flags & DNS_FLAG_RD) ? "rd " : "",
           (flags & DNS_FLAG_RA) ? "ra " : "",
           (flags & DNS_FLAG_AD) ? "ad " : "",  /* DNSSEC validated */
           (flags & DNS_FLAG_CD) ? "cd " : "",
           msg.nquestions, msg.nanswers, msg.nauthority, msg.nadditional);
    
    if (msg.ad_bit) printf(";; DNSSEC: Response is AUTHENTICATED (AD=1)\n");
    
    /* Print question */
    if (msg.nquestions > 0) {
        printf("\n;; QUESTION SECTION:\n");
        printf(";%-30s %-6s %-6s\n",
               msg.questions[0].qname,
               dns_type_name(msg.questions[0].qtype),
               "IN");
    }
    
    /* Print answers */
    if (msg.nanswers > 0) {
        printf("\n;; ANSWER SECTION:\n");
        for (int i = 0; i < msg.nanswers; i++) {
            const dns_rr_t *rr = &msg.answers[i];
            printf("%-30s %-7u %-4s %-8s ",
                   rr->name, rr->ttl, "IN", dns_type_name(rr->type));
            dns_print_rdata(rr, resp_buf, (size_t)resp_len);
            printf("\n");
        }
    }
    
    /* Print authority */
    if (msg.nauthority > 0) {
        printf("\n;; AUTHORITY SECTION:\n");
        for (int i = 0; i < msg.nauthority; i++) {
            const dns_rr_t *rr = &msg.authority[i];
            printf("%-30s %-7u %-4s %-8s ",
                   rr->name, rr->ttl, "IN", dns_type_name(rr->type));
            dns_print_rdata(rr, resp_buf, (size_t)resp_len);
            printf("\n");
        }
    }
    
    /* Print additional (skip OPT records) */
    bool printed_additional_header = false;
    for (int i = 0; i < msg.nadditional; i++) {
        const dns_rr_t *rr = &msg.additional[i];
        if (rr->type == DNS_TYPE_OPT) continue;  /* skip EDNS0 OPT */
        if (!printed_additional_header) {
            printf("\n;; ADDITIONAL SECTION:\n");
            printed_additional_header = true;
        }
        printf("%-30s %-7u %-4s %-8s ",
               rr->name, rr->ttl, "IN", dns_type_name(rr->type));
        dns_print_rdata(rr, resp_buf, (size_t)resp_len);
        printf("\n");
    }
    
    printf("\n;; MSG SIZE rcvd: %zd bytes\n", resp_len);
    
    return (int)rcode;
}

/* ---- Lookup resolver from /etc/resolv.conf ---- */
static int get_system_resolver(char *ip_out, size_t ip_out_size) {
    FILE *f = fopen("/etc/resolv.conf", "r");
    if (!f) return -1;
    
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        char keyword[32], value[128];
        if (sscanf(line, "%31s %127s", keyword, value) == 2) {
            if (strcmp(keyword, "nameserver") == 0) {
                strncpy(ip_out, value, ip_out_size - 1);
                ip_out[ip_out_size - 1] = '\0';
                fclose(f);
                return 0;
            }
        }
    }
    fclose(f);
    return -1;
}

/* ---- main ---- */
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <hostname> [A|AAAA|MX|TXT|NS|SOA|SRV|ANY] [@resolver]\n", argv[0]);
        fprintf(stderr, "  Options:\n");
        fprintf(stderr, "    +dnssec    Request DNSSEC records\n");
        return 1;
    }
    
    const char *name = argv[1];
    uint16_t qtype = DNS_TYPE_A;
    char resolver_ip[64] = "8.8.8.8";
    bool want_dnssec = false;
    
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "A")    == 0)  qtype = DNS_TYPE_A;
        else if (strcmp(argv[i], "AAAA") == 0) qtype = DNS_TYPE_AAAA;
        else if (strcmp(argv[i], "MX")   == 0) qtype = DNS_TYPE_MX;
        else if (strcmp(argv[i], "TXT")  == 0) qtype = DNS_TYPE_TXT;
        else if (strcmp(argv[i], "NS")   == 0) qtype = DNS_TYPE_NS;
        else if (strcmp(argv[i], "SOA")  == 0) qtype = DNS_TYPE_SOA;
        else if (strcmp(argv[i], "SRV")  == 0) qtype = DNS_TYPE_SRV;
        else if (strcmp(argv[i], "ANY")  == 0) qtype = DNS_TYPE_ANY;
        else if (argv[i][0] == '@') strncpy(resolver_ip, argv[i] + 1, sizeof(resolver_ip) - 1);
        else if (strcmp(argv[i], "+dnssec") == 0) want_dnssec = true;
        else if (strcmp(argv[i], "+sys")   == 0) get_system_resolver(resolver_ip, sizeof(resolver_ip));
    }
    
    int rcode = dns_resolve(resolver_ip, DNS_PORT, name, qtype, want_dnssec);
    return (rcode == DNS_RCODE_NOERROR) ? 0 : 1;
}
```

**Build and test:**
```bash
gcc -O2 -Wall -Wextra -Wshadow -fstack-protector-strong \
    -D_FORTIFY_SOURCE=2 -o dns_resolver dns_resolver.c

# Basic A query
./dns_resolver example.com A @8.8.8.8

# DNSSEC-aware query (check AD bit)
./dns_resolver cloudflare.com A @1.1.1.1 +dnssec

# MX lookup
./dns_resolver gmail.com MX @8.8.8.8

# TXT (SPF record)
./dns_resolver gmail.com TXT @8.8.8.8

# SOA
./dns_resolver example.com SOA @8.8.8.8

# AAAA
./dns_resolver ipv6.google.com AAAA @8.8.8.8

# From system resolver
./dns_resolver kubernetes.default.svc.cluster.local A +sys
```

---

## 16. Implementation in Rust

### 16.1 DNS Library in Rust

Complete DNS implementation: wire format encode/decode, query builder, async UDP resolver with timeout, EDNS0.

```toml
# Cargo.toml
[package]
name = "dns-resolver"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
thiserror = "1"
rand = "0.8"
bytes = "1"

[[bin]]
name = "dns-resolver"
path = "src/main.rs"
```

```rust
// src/lib.rs - DNS wire format library
#![deny(clippy::all)]
#![warn(clippy::pedantic)]

use std::fmt;
use thiserror::Error;

// ─────────────────────────────────────────────────────────
// Error Types
// ─────────────────────────────────────────────────────────

#[derive(Error, Debug)]
pub enum DnsError {
    #[error("buffer too short: need {need}, have {have}")]
    BufferTooShort { need: usize, have: usize },

    #[error("invalid label length {0}")]
    InvalidLabelLength(u8),

    #[error("name exceeds 255 bytes")]
    NameTooLong,

    #[error("pointer loop detected at depth {0}")]
    PointerLoop(usize),

    #[error("pointer offset {0} out of bounds (msg len {1})")]
    InvalidPointer(usize, usize),

    #[error("invalid label type byte 0x{0:02x}")]
    InvalidLabelType(u8),

    #[error("malformed RDATA for type {0:?}")]
    MalformedRdata(RecordType),

    #[error("transaction ID mismatch: sent 0x{sent:04x}, got 0x{got:04x}")]
    TxidMismatch { sent: u16, got: u16 },

    #[error("DNS error: {0:?}")]
    DnsServerError(Rcode),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("timeout waiting for DNS response")]
    Timeout,
}

pub type Result<T> = std::result::Result<T, DnsError>;

// ─────────────────────────────────────────────────────────
// DNS Record Types
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[repr(u16)]
pub enum RecordType {
    A      = 1,
    Ns     = 2,
    Cname  = 5,
    Soa    = 6,
    Mx     = 15,
    Txt    = 16,
    Aaaa   = 28,
    Srv    = 33,
    Opt    = 41,
    Ds     = 43,
    Rrsig  = 46,
    Nsec   = 47,
    DnsKey = 48,
    Nsec3  = 50,
    Tlsa   = 52,
    Caa    = 257,
    Unknown(u16),
}

impl RecordType {
    pub fn from_u16(v: u16) -> Self {
        match v {
            1   => Self::A,
            2   => Self::Ns,
            5   => Self::Cname,
            6   => Self::Soa,
            15  => Self::Mx,
            16  => Self::Txt,
            28  => Self::Aaaa,
            33  => Self::Srv,
            41  => Self::Opt,
            43  => Self::Ds,
            46  => Self::Rrsig,
            47  => Self::Nsec,
            48  => Self::DnsKey,
            50  => Self::Nsec3,
            52  => Self::Tlsa,
            257 => Self::Caa,
            n   => Self::Unknown(n),
        }
    }

    pub fn as_u16(self) -> u16 {
        match self {
            Self::Unknown(n) => n,
            _ => unsafe { *<*const _>::cast::<u16>(&self) },
        }
    }
}

impl fmt::Display for RecordType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::A       => write!(f, "A"),
            Self::Ns      => write!(f, "NS"),
            Self::Cname   => write!(f, "CNAME"),
            Self::Soa     => write!(f, "SOA"),
            Self::Mx      => write!(f, "MX"),
            Self::Txt     => write!(f, "TXT"),
            Self::Aaaa    => write!(f, "AAAA"),
            Self::Srv     => write!(f, "SRV"),
            Self::Opt     => write!(f, "OPT"),
            Self::Ds      => write!(f, "DS"),
            Self::Rrsig   => write!(f, "RRSIG"),
            Self::Nsec    => write!(f, "NSEC"),
            Self::DnsKey  => write!(f, "DNSKEY"),
            Self::Nsec3   => write!(f, "NSEC3"),
            Self::Tlsa    => write!(f, "TLSA"),
            Self::Caa     => write!(f, "CAA"),
            Self::Unknown(n) => write!(f, "TYPE{n}"),
        }
    }
}

// ─────────────────────────────────────────────────────────
// DNS Opcodes and RCODEs
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rcode {
    NoError  = 0,
    FormErr  = 1,
    ServFail = 2,
    NxDomain = 3,
    NotImpl  = 4,
    Refused  = 5,
    Unknown(u16),
}

impl Rcode {
    pub fn from_u16(v: u16) -> Self {
        match v & 0x0F {
            0 => Self::NoError,
            1 => Self::FormErr,
            2 => Self::ServFail,
            3 => Self::NxDomain,
            4 => Self::NotImpl,
            5 => Self::Refused,
            n => Self::Unknown(n as u16),
        }
    }
}

impl fmt::Display for Rcode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NoError  => write!(f, "NOERROR"),
            Self::FormErr  => write!(f, "FORMERR"),
            Self::ServFail => write!(f, "SERVFAIL"),
            Self::NxDomain => write!(f, "NXDOMAIN"),
            Self::NotImpl  => write!(f, "NOTIMP"),
            Self::Refused  => write!(f, "REFUSED"),
            Self::Unknown(n) => write!(f, "RCODE{n}"),
        }
    }
}

// ─────────────────────────────────────────────────────────
// DNS Header Flags
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy)]
pub struct Flags(pub u16);

impl Flags {
    pub fn query() -> Self { Self(0x0100) }  // RD=1
    pub fn is_response(self)    -> bool { (self.0 & 0x8000) != 0 }
    pub fn is_authoritative(self) -> bool { (self.0 & 0x0400) != 0 }
    pub fn is_truncated(self)   -> bool { (self.0 & 0x0200) != 0 }
    pub fn recursion_desired(self) -> bool { (self.0 & 0x0100) != 0 }
    pub fn recursion_available(self) -> bool { (self.0 & 0x0080) != 0 }
    pub fn authentic_data(self) -> bool { (self.0 & 0x0020) != 0 }
    pub fn checking_disabled(self) -> bool { (self.0 & 0x0010) != 0 }
    pub fn rcode(self) -> Rcode { Rcode::from_u16(self.0 & 0x000F) }
}

impl fmt::Display for Flags {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut parts = Vec::new();
        if self.is_response()        { parts.push("qr"); }
        if self.is_authoritative()   { parts.push("aa"); }
        if self.is_truncated()       { parts.push("tc"); }
        if self.recursion_desired()  { parts.push("rd"); }
        if self.recursion_available(){ parts.push("ra"); }
        if self.authentic_data()     { parts.push("ad"); }
        if self.checking_disabled()  { parts.push("cd"); }
        write!(f, "{}", parts.join(" "))
    }
}

// ─────────────────────────────────────────────────────────
// DNS Name
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Name(String);

impl Name {
    pub fn new(s: impl Into<String>) -> Self {
        let s = s.into();
        let s = if s.ends_with('.') { s } else { s + "." };
        Self(s)
    }

    pub fn as_str(&self) -> &str { &self.0 }

    /// Encode to DNS wire format (no compression)
    pub fn encode(&self, buf: &mut Vec<u8>) -> Result<()> {
        let name = self.0.trim_end_matches('.');
        if name.is_empty() {
            buf.push(0);  // root label
            return Ok(());
        }
        let mut total = 0usize;
        for label in name.split('.') {
            let label = label.as_bytes();
            if label.len() > 63 {
                return Err(DnsError::InvalidLabelLength(label.len() as u8));
            }
            total += 1 + label.len();
            if total > 255 {
                return Err(DnsError::NameTooLong);
            }
            buf.push(label.len() as u8);
            buf.extend_from_slice(label);
        }
        buf.push(0);  // root terminator
        Ok(())
    }

    /// Decode from DNS wire format with compression support
    /// Returns the name and the number of bytes consumed (NOT following pointers)
    pub fn decode(msg: &[u8], offset: usize) -> Result<(Self, usize)> {
        Self::decode_inner(msg, offset, 0)
    }

    fn decode_inner(msg: &[u8], offset: usize, depth: usize) -> Result<(Self, usize)> {
        const MAX_DEPTH: usize = 32;
        if depth > MAX_DEPTH {
            return Err(DnsError::PointerLoop(depth));
        }

        let mut labels: Vec<String> = Vec::new();
        let mut pos = offset;
        let mut first_return_pos = None;

        loop {
            if pos >= msg.len() {
                return Err(DnsError::BufferTooShort { need: pos + 1, have: msg.len() });
            }

            let byte = msg[pos];

            match byte & 0xC0 {
                0x00 => {
                    // Regular label
                    let len = byte as usize;
                    pos += 1;
                    if len == 0 { break; }  // root label, end
                    if pos + len > msg.len() {
                        return Err(DnsError::BufferTooShort { need: pos + len, have: msg.len() });
                    }
                    let label = std::str::from_utf8(&msg[pos..pos + len])
                        .unwrap_or("<invalid>")
                        .to_ascii_lowercase();
                    labels.push(label);
                    pos += len;
                }
                0xC0 => {
                    // Pointer
                    if pos + 1 >= msg.len() {
                        return Err(DnsError::BufferTooShort { need: pos + 2, have: msg.len() });
                    }
                    let ptr = (((byte & 0x3F) as usize) << 8) | (msg[pos + 1] as usize);
                    if ptr >= msg.len() {
                        return Err(DnsError::InvalidPointer(ptr, msg.len()));
                    }
                    if first_return_pos.is_none() {
                        first_return_pos = Some(pos + 2);
                    }
                    let (suffix, _) = Self::decode_inner(msg, ptr, depth + 1)?;
                    // Merge suffix labels
                    let suffix_str = suffix.0.trim_end_matches('.');
                    if !suffix_str.is_empty() {
                        for label in suffix_str.split('.') {
                            labels.push(label.to_string());
                        }
                    }
                    pos = first_return_pos.unwrap();
                    break;
                }
                _ => return Err(DnsError::InvalidLabelType(byte)),
            }
        }

        let consumed = first_return_pos.unwrap_or(pos);
        let name = if labels.is_empty() {
            ".".to_string()
        } else {
            labels.join(".") + "."
        };
        Ok((Self(name), consumed))
    }
}

impl fmt::Display for Name {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

// ─────────────────────────────────────────────────────────
// Resource Record RDATA
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub enum RData {
    A(std::net::Ipv4Addr),
    Aaaa(std::net::Ipv6Addr),
    Ns(Name),
    Cname(Name),
    Ptr(Name),
    Mx { preference: u16, exchange: Name },
    Txt(Vec<Vec<u8>>),
    Soa {
        mname:   Name,
        rname:   Name,
        serial:  u32,
        refresh: u32,
        retry:   u32,
        expire:  u32,
        minimum: u32,
    },
    Srv {
        priority: u16,
        weight:   u16,
        port:     u16,
        target:   Name,
    },
    Unknown { rtype: u16, data: Vec<u8> },
}

impl RData {
    pub fn parse(rtype: RecordType, msg: &[u8], offset: usize, rdlen: usize) -> Result<Self> {
        if offset + rdlen > msg.len() {
            return Err(DnsError::BufferTooShort { need: offset + rdlen, have: msg.len() });
        }
        let rd = &msg[offset..offset + rdlen];

        match rtype {
            RecordType::A => {
                if rdlen < 4 { return Err(DnsError::MalformedRdata(rtype)); }
                Ok(Self::A(std::net::Ipv4Addr::new(rd[0], rd[1], rd[2], rd[3])))
            }
            RecordType::Aaaa => {
                if rdlen < 16 { return Err(DnsError::MalformedRdata(rtype)); }
                let bytes: [u8; 16] = rd[..16].try_into().unwrap();
                Ok(Self::Aaaa(std::net::Ipv6Addr::from(bytes)))
            }
            RecordType::Ns => {
                let (name, _) = Name::decode(msg, offset)?;
                Ok(Self::Ns(name))
            }
            RecordType::Cname => {
                let (name, _) = Name::decode(msg, offset)?;
                Ok(Self::Cname(name))
            }
            RecordType::Mx => {
                if rdlen < 3 { return Err(DnsError::MalformedRdata(rtype)); }
                let pref = u16::from_be_bytes([rd[0], rd[1]]);
                let (exchange, _) = Name::decode(msg, offset + 2)?;
                Ok(Self::Mx { preference: pref, exchange })
            }
            RecordType::Txt => {
                let mut strings = Vec::new();
                let mut i = 0;
                while i < rdlen {
                    let slen = rd[i] as usize;
                    i += 1;
                    if i + slen > rdlen {
                        return Err(DnsError::MalformedRdata(rtype));
                    }
                    strings.push(rd[i..i + slen].to_vec());
                    i += slen;
                }
                Ok(Self::Txt(strings))
            }
            RecordType::Soa => {
                let (mname, pos1) = Name::decode(msg, offset)?;
                let (rname, pos2) = Name::decode(msg, pos1)?;
                if pos2 + 20 > msg.len() {
                    return Err(DnsError::MalformedRdata(rtype));
                }
                let serial  = u32::from_be_bytes(msg[pos2..pos2+4].try_into().unwrap());
                let refresh = u32::from_be_bytes(msg[pos2+4..pos2+8].try_into().unwrap());
                let retry   = u32::from_be_bytes(msg[pos2+8..pos2+12].try_into().unwrap());
                let expire  = u32::from_be_bytes(msg[pos2+12..pos2+16].try_into().unwrap());
                let minimum = u32::from_be_bytes(msg[pos2+16..pos2+20].try_into().unwrap());
                Ok(Self::Soa { mname, rname, serial, refresh, retry, expire, minimum })
            }
            RecordType::Srv => {
                if rdlen < 7 { return Err(DnsError::MalformedRdata(rtype)); }
                let priority = u16::from_be_bytes([rd[0], rd[1]]);
                let weight   = u16::from_be_bytes([rd[2], rd[3]]);
                let port     = u16::from_be_bytes([rd[4], rd[5]]);
                let (target, _) = Name::decode(msg, offset + 6)?;
                Ok(Self::Srv { priority, weight, port, target })
            }
            _ => {
                Ok(Self::Unknown {
                    rtype: rtype.as_u16(),
                    data: rd.to_vec(),
                })
            }
        }
    }
}

impl fmt::Display for RData {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::A(addr)    => write!(f, "{addr}"),
            Self::Aaaa(addr) => write!(f, "{addr}"),
            Self::Ns(name)   => write!(f, "{name}"),
            Self::Cname(name) => write!(f, "{name}"),
            Self::Ptr(name)  => write!(f, "{name}"),
            Self::Mx { preference, exchange } => write!(f, "{preference} {exchange}"),
            Self::Txt(strings) => {
                for (i, s) in strings.iter().enumerate() {
                    if i > 0 { write!(f, " ")?; }
                    write!(f, "\"")?;
                    for &b in s {
                        if b.is_ascii_graphic() || b == b' ' {
                            write!(f, "{}", b as char)?;
                        } else {
                            write!(f, "\\x{b:02x}")?;
                        }
                    }
                    write!(f, "\"")?;
                }
                Ok(())
            }
            Self::Soa { mname, rname, serial, refresh, retry, expire, minimum } => {
                write!(f, "{mname} {rname} {serial} {refresh} {retry} {expire} {minimum}")
            }
            Self::Srv { priority, weight, port, target } => {
                write!(f, "{priority} {weight} {port} {target}")
            }
            Self::Unknown { rtype, data } => {
                write!(f, "\\# {} ", data.len())?;
                for b in data { write!(f, "{b:02x}")?; }
                write!(f, " (type={rtype})")
            }
        }
    }
}

// ─────────────────────────────────────────────────────────
// Resource Record
// ─────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ResourceRecord {
    pub name:  Name,
    pub rtype: RecordType,
    pub class: u16,
    pub ttl:   u32,
    pub rdata: RData,
}

impl ResourceRecord {
    pub fn parse(msg: &[u8], offset: usize) -> Result<(Self, usize)> {
        let (name, pos) = Name::decode(msg, offset)?;
        if pos + 10 > msg.len() {
            return Err(DnsError::BufferTooShort { need: pos + 10, have: msg.len() });
        }
        let rtype  = RecordType::from_u16(u16::from_be_bytes([msg[pos], msg[pos+1]]));
        let class  = u16::from_be_bytes([msg[pos+2], msg[pos+3]]);
        let ttl    = u32::from_be_bytes([msg[pos+4], msg[pos+5], msg[pos+6], msg[pos+7]]);
        let rdlen  = u16::from_be_bytes([msg[pos+8], msg[pos+9]]) as usize;
        let rdata_start = pos + 10;

        if rdata_start + rdlen > msg.len() {
            return Err(DnsError::BufferTooShort {
                need: rdata_start + rdlen,
                have: msg.len(),
            });
        }

        let rdata = RData::parse(rtype, msg, rdata_start, rdlen)?;

        Ok((Self { name, rtype, class, ttl, rdata }, rdata_start + rdlen))
    }
}

impl fmt::Display for ResourceRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:<30} {:<7} IN  {:<8} {}",
               self.name.as_str(), self.ttl, self.rtype, self.rdata)
    }
}

// ─────────────────────────────────────────────────────────
// DNS Message
// ─────────────────────────────────────────────────────────

#[derive(Debug)]
pub struct DnsMessage {
    pub id:         u16,
    pub flags:      Flags,
    pub questions:  Vec<(Name, RecordType, u16)>,
    pub answers:    Vec<ResourceRecord>,
    pub authority:  Vec<ResourceRecord>,
    pub additional: Vec<ResourceRecord>,
}

impl DnsMessage {
    /// Build a query message with EDNS0 OPT record
    pub fn build_query(
        id: u16,
        name: &Name,
        qtype: RecordType,
        want_dnssec: bool,
    ) -> Result<Vec<u8>> {
        let mut buf = Vec::with_capacity(512);

        // Header: ID, flags (RD=1), QDCOUNT=1, ANCOUNT=0, NSCOUNT=0, ARCOUNT=1
        buf.extend_from_slice(&id.to_be_bytes());
        buf.extend_from_slice(&0x0100u16.to_be_bytes()); // RD=1
        buf.extend_from_slice(&1u16.to_be_bytes()); // QDCOUNT
        buf.extend_from_slice(&0u16.to_be_bytes()); // ANCOUNT
        buf.extend_from_slice(&0u16.to_be_bytes()); // NSCOUNT
        buf.extend_from_slice(&1u16.to_be_bytes()); // ARCOUNT (OPT)

        // Question
        name.encode(&mut buf)?;
        buf.extend_from_slice(&qtype.as_u16().to_be_bytes());
        buf.extend_from_slice(&1u16.to_be_bytes()); // CLASS = IN

        // EDNS0 OPT record
        buf.push(0x00); // NAME = root
        buf.extend_from_slice(&41u16.to_be_bytes()); // TYPE = OPT
        buf.extend_from_slice(&4096u16.to_be_bytes()); // UDP payload size (CLASS field)
        buf.push(0x00); // Extended RCODE = 0
        buf.push(0x00); // EDNS version = 0
        // Z field: DO bit
        let z: u16 = if want_dnssec { 0x8000 } else { 0x0000 };
        buf.extend_from_slice(&z.to_be_bytes());
        buf.extend_from_slice(&0u16.to_be_bytes()); // RDLENGTH = 0

        Ok(buf)
    }

    /// Parse a DNS response message
    pub fn parse(msg: &[u8]) -> Result<Self> {
        if msg.len() < 12 {
            return Err(DnsError::BufferTooShort { need: 12, have: msg.len() });
        }

        let id      = u16::from_be_bytes([msg[0], msg[1]]);
        let flags   = Flags(u16::from_be_bytes([msg[2], msg[3]]));
        let qdcount = u16::from_be_bytes([msg[4], msg[5]]) as usize;
        let ancount = u16::from_be_bytes([msg[6], msg[7]]) as usize;
        let nscount = u16::from_be_bytes([msg[8], msg[9]]) as usize;
        let arcount = u16::from_be_bytes([msg[10], msg[11]]) as usize;

        let mut pos = 12usize;

        // Parse questions
        let mut questions = Vec::with_capacity(qdcount.min(4));
        for _ in 0..qdcount.min(4) {
            let (name, next_pos) = Name::decode(msg, pos)?;
            if next_pos + 4 > msg.len() {
                return Err(DnsError::BufferTooShort { need: next_pos + 4, have: msg.len() });
            }
            let qtype  = RecordType::from_u16(u16::from_be_bytes([msg[next_pos], msg[next_pos+1]]));
            let qclass = u16::from_be_bytes([msg[next_pos+2], msg[next_pos+3]]);
            pos = next_pos + 4;
            questions.push((name, qtype, qclass));
        }

        // Parse RR sections
        let parse_rrs = |count: usize, pos: &mut usize| -> Result<Vec<ResourceRecord>> {
            let mut rrs = Vec::with_capacity(count.min(64));
            for _ in 0..count.min(64) {
                let (rr, next_pos) = ResourceRecord::parse(msg, *pos)?;
                *pos = next_pos;
                // Skip OPT pseudo-RR from display (keep internally)
                if rr.rtype != RecordType::Opt {
                    rrs.push(rr);
                } else {
                    // Could parse EDNS0 options here
                }
            }
            Ok(rrs)
        };

        let answers    = parse_rrs(ancount, &mut pos)?;
        let authority  = parse_rrs(nscount, &mut pos)?;
        let additional = parse_rrs(arcount, &mut pos)?;

        Ok(Self { id, flags, questions, answers, authority, additional })
    }

    pub fn print(&self) {
        println!(";; ->>HEADER<<- opcode: QUERY, status: {}, id: {}",
                 self.flags.rcode(), self.id);
        println!(";; flags: {} ; QUERY: {}, ANSWER: {}, AUTHORITY: {}, ADDITIONAL: {}",
                 self.flags,
                 self.questions.len(),
                 self.answers.len(),
                 self.authority.len(),
                 self.additional.len());
        if self.flags.authentic_data() {
            println!(";; DNSSEC: Response AUTHENTICATED (AD=1)");
        }

        if !self.questions.is_empty() {
            println!("\n;; QUESTION SECTION:");
            for (name, qtype, _class) in &self.questions {
                println!(";{:<30} IN  {}", name.as_str(), qtype);
            }
        }
        if !self.answers.is_empty() {
            println!("\n;; ANSWER SECTION:");
            for rr in &self.answers { println!("{rr}"); }
        }
        if !self.authority.is_empty() {
            println!("\n;; AUTHORITY SECTION:");
            for rr in &self.authority { println!("{rr}"); }
        }
        if !self.additional.is_empty() {
            println!("\n;; ADDITIONAL SECTION:");
            for rr in &self.additional { println!("{rr}"); }
        }
    }
}

// ─────────────────────────────────────────────────────────
// Async UDP Resolver
// ─────────────────────────────────────────────────────────

use std::net::SocketAddr;
use std::time::Duration;
use tokio::net::UdpSocket;
use tokio::time::timeout;
use rand::Rng;

pub const DEFAULT_DNS_PORT: u16 = 53;
pub const DEFAULT_TIMEOUT: Duration = Duration::from_secs(5);
pub const MAX_RETRIES: usize = 3;
pub const MAX_UDP_PAYLOAD: usize = 4096 + 512;

pub struct Resolver {
    server: SocketAddr,
    timeout: Duration,
    retries: usize,
    want_dnssec: bool,
}

impl Resolver {
    pub fn new(server: SocketAddr) -> Self {
        Self {
            server,
            timeout: DEFAULT_TIMEOUT,
            retries: MAX_RETRIES,
            want_dnssec: false,
        }
    }

    pub fn with_timeout(mut self, t: Duration) -> Self { self.timeout = t; self }
    pub fn with_retries(mut self, r: usize) -> Self { self.retries = r; self }
    pub fn with_dnssec(mut self, d: bool) -> Self { self.want_dnssec = d; self }

    pub async fn query(&self, name: &str, qtype: RecordType) -> Result<DnsMessage> {
        let dns_name = Name::new(name);
        let txid: u16 = rand::thread_rng().gen();

        let query = DnsMessage::build_query(txid, &dns_name, qtype, self.want_dnssec)?;

        // Bind to random ephemeral port (source port randomization, RFC 5452)
        let local: SocketAddr = if self.server.is_ipv4() {
            "0.0.0.0:0".parse().unwrap()
        } else {
            "[::]:0".parse().unwrap()
        };

        let mut last_err = DnsError::Timeout;

        for attempt in 0..self.retries {
            let sock = UdpSocket::bind(local).await
                .map_err(DnsError::Io)?;
            sock.connect(self.server).await
                .map_err(DnsError::Io)?;

            // Send query
            sock.send(&query).await.map_err(DnsError::Io)?;

            // Receive response with timeout
            let mut buf = vec![0u8; MAX_UDP_PAYLOAD];
            let recv_result = timeout(self.timeout, sock.recv(&mut buf)).await;

            match recv_result {
                Err(_) => {
                    eprintln!(";; Timeout on attempt {}", attempt + 1);
                    last_err = DnsError::Timeout;
                    continue;
                }
                Ok(Err(e)) => {
                    eprintln!(";; Recv error: {e}");
                    last_err = DnsError::Io(e);
                    continue;
                }
                Ok(Ok(n)) => {
                    buf.truncate(n);

                    // Validate TXID
                    if n < 2 {
                        last_err = DnsError::BufferTooShort { need: 2, have: n };
                        continue;
                    }
                    let resp_id = u16::from_be_bytes([buf[0], buf[1]]);
                    if resp_id != txid {
                        last_err = DnsError::TxidMismatch { sent: txid, got: resp_id };
                        // Don't retry on TXID mismatch — possible spoofing
                        return Err(last_err);
                    }

                    // Parse
                    let msg = DnsMessage::parse(&buf)?;

                    // Check TC bit — should retry over TCP
                    if msg.flags.is_truncated() {
                        eprintln!(";; Response truncated (TC=1). TCP fallback needed for full response.");
                        // Production: implement TCP fallback here
                    }

                    return Ok(msg);
                }
            }
        }

        Err(last_err)
    }

    /// Parse system resolver from /etc/resolv.conf
    pub fn from_system() -> Result<Self> {
        let content = std::fs::read_to_string("/etc/resolv.conf")
            .map_err(DnsError::Io)?;
        for line in content.lines() {
            let mut parts = line.split_whitespace();
            if parts.next() == Some("nameserver") {
                if let Some(ip) = parts.next() {
                    if let Ok(addr) = ip.parse::<std::net::IpAddr>() {
                        let sa = SocketAddr::new(addr, DEFAULT_DNS_PORT);
                        return Ok(Self::new(sa));
                    }
                }
            }
        }
        // Default to Google DNS
        Ok(Self::new("8.8.8.8:53".parse().unwrap()))
    }
}
```

```rust
// src/main.rs - CLI for the DNS resolver
use std::net::SocketAddr;
use tokio;

// Import from lib
mod lib_dns {
    include!("lib.rs");
}
use lib_dns::{DnsMessage, Name, RecordType, Resolver};

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <hostname> [A|AAAA|MX|TXT|NS|SOA|SRV] [@server] [+dnssec]", args[0]);
        std::process::exit(1);
    }

    let name = &args[1];
    let mut qtype = RecordType::A;
    let mut server: SocketAddr = "8.8.8.8:53".parse().unwrap();
    let mut want_dnssec = false;

    for arg in &args[2..] {
        match arg.as_str() {
            "A"       => qtype = RecordType::A,
            "AAAA"    => qtype = RecordType::Aaaa,
            "MX"      => qtype = RecordType::Mx,
            "TXT"     => qtype = RecordType::Txt,
            "NS"      => qtype = RecordType::Ns,
            "SOA"     => qtype = RecordType::Soa,
            "SRV"     => qtype = RecordType::Srv,
            "+dnssec" => want_dnssec = true,
            "+sys"    => {
                if let Ok(r) = Resolver::from_system() {
                    server = r.server; // would need pub field
                }
            }
            s if s.starts_with('@') => {
                let ip = &s[1..];
                server = if ip.contains(':') {
                    ip.parse().unwrap_or(server)
                } else {
                    format!("{ip}:53").parse().unwrap_or(server)
                };
            }
            _ => {}
        }
    }

    println!(";; Querying {name} {qtype} @{server}");
    if want_dnssec { println!(";; DNSSEC requested (DO=1)"); }

    let resolver = Resolver::new(server).with_dnssec(want_dnssec);

    match resolver.query(name, qtype).await {
        Ok(msg) => {
            msg.print();
            if matches!(msg.flags.rcode(), lib_dns::Rcode::NoError) {
                std::process::exit(0);
            } else {
                std::process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(2);
        }
    }
}
```

**Build and run:**
```bash
# Build
cargo build --release

# A record
./target/release/dns-resolver example.com A @8.8.8.8

# AAAA
./target/release/dns-resolver ipv6.google.com AAAA

# MX with DNSSEC
./target/release/dns-resolver gmail.com MX @1.1.1.1 +dnssec

# TXT (SPF)
./target/release/dns-resolver cloudflare.com TXT

# SOA
./target/release/dns-resolver iana.org SOA @8.8.8.8

# Clippy lint
cargo clippy -- -D warnings

# Run tests
cargo test
```

---

## 17. Testing, Fuzzing, and Benchmarking

### 17.1 Unit Tests (Rust)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_name_encode_decode_roundtrip() {
        let name = Name::new("www.example.com");
        let mut buf = Vec::new();
        name.encode(&mut buf).unwrap();

        // Expected wire: 03 77 77 77 07 65 78 61 6d 70 6c 65 03 63 6f 6d 00
        assert_eq!(buf[0], 3);  // "www" length
        assert_eq!(&buf[1..4], b"www");
        assert_eq!(buf[4], 7);  // "example" length
        assert_eq!(buf[12], 3); // "com" length
        assert_eq!(buf[16], 0); // root terminator

        let (decoded, _) = Name::decode(&buf, 0).unwrap();
        assert_eq!(decoded.as_str(), "www.example.com.");
    }

    #[test]
    fn test_name_decode_with_compression() {
        // Simulate compressed message
        // Offset 0: "example.com." (12 bytes)
        // Offset 12: pointer to offset 0 with "www" prefix
        let mut msg: Vec<u8> = Vec::new();

        // "example.com." at offset 0
        msg.push(7); msg.extend_from_slice(b"example");
        msg.push(3); msg.extend_from_slice(b"com");
        msg.push(0);  // root, total = 13 bytes

        // "www.example.com." at offset 13 using compression
        msg.push(3); msg.extend_from_slice(b"www"); // "www" label
        msg.push(0xC0); msg.push(0x00); // pointer to offset 0

        let (name, consumed) = Name::decode(&msg, 13).unwrap();
        assert_eq!(name.as_str(), "www.example.com.");
        assert_eq!(consumed, 19); // 13 + 4 (www label) + 2 (pointer) = 19
    }

    #[test]
    fn test_pointer_loop_detection() {
        // Two pointers pointing at each other
        let msg = vec![
            0xC0, 0x02, // pointer to offset 2
            0xC0, 0x00, // pointer to offset 0
        ];
        let result = Name::decode(&msg, 0);
        assert!(matches!(result, Err(DnsError::PointerLoop(_))));
    }

    #[test]
    fn test_flags_parsing() {
        // Standard response: QR=1 RD=1 RA=1 RCODE=0
        let flags = Flags(0x8180);
        assert!(flags.is_response());
        assert!(flags.recursion_desired());
        assert!(flags.recursion_available());
        assert_eq!(flags.rcode(), Rcode::NoError);
        assert!(!flags.authentic_data());

        // DNSSEC-authenticated response
        let flags_ad = Flags(0x8380);  // QR+AD+RD+RA
        assert!(flags_ad.authentic_data());

        // NXDOMAIN
        let flags_nx = Flags(0x8183);
        assert_eq!(flags_nx.rcode(), Rcode::NxDomain);
    }

    #[test]
    fn test_build_query_wire_format() {
        let name = Name::new("example.com");
        let query = DnsMessage::build_query(0xABCD, &name, RecordType::A, false).unwrap();

        // Check header
        assert_eq!(&query[0..2], &[0xAB, 0xCD]); // ID
        assert_eq!(&query[2..4], &[0x01, 0x00]); // flags: RD=1
        assert_eq!(&query[4..6], &[0x00, 0x01]); // QDCOUNT=1
        assert_eq!(&query[10..12], &[0x00, 0x01]); // ARCOUNT=1 (OPT)

        // Check OPT record is present at end
        let last_bytes = &query[query.len()-4..];
        // RDLENGTH=0 at end of OPT
        assert_eq!(&last_bytes[2..4], &[0x00, 0x00]);
    }

    #[test]
    fn test_build_query_dnssec() {
        let name = Name::new("example.com");
        let query = DnsMessage::build_query(0x1234, &name, RecordType::A, true).unwrap();

        // Find the OPT record Z field (DO bit)
        // OPT starts after question section
        // Header(12) + qname("example.com." = 13 bytes) + qtype(2) + qclass(2) = 29
        // OPT: name(1) + type(2) + class/udpsize(2) + ext-rcode(1) + version(1) + Z(2) + rdlen(2) = 11
        // Z field is at header(12) + qname + qtype + qclass + opt_name + opt_type + opt_class + ext_rcode + version
        let opt_start = 12 + 13 + 4; // rough position of OPT record
        // The DO bit should be set in the Z field
        let do_bit_offset = opt_start + 1 + 2 + 2 + 1 + 1; // skip NAME(1)+TYPE(2)+CLASS(2)+EXTRCODE(1)+VER(1)
        assert_eq!(query[do_bit_offset] & 0x80, 0x80, "DO bit should be set");
    }

    #[test]
    fn test_rdata_a_parsing() {
        let msg = [93u8, 184, 216, 34]; // 93.184.216.34
        let rdata = RData::parse(RecordType::A, &msg, 0, 4).unwrap();
        if let RData::A(addr) = rdata {
            assert_eq!(addr, "93.184.216.34".parse::<std::net::Ipv4Addr>().unwrap());
        } else {
            panic!("Expected A record");
        }
    }

    #[test]
    fn test_rdata_txt_multi_string() {
        // TXT with two strings: "hello" and "world"
        let msg = [5u8, b'h', b'e', b'l', b'l', b'o', 5, b'w', b'o', b'r', b'l', b'd'];
        let rdata = RData::parse(RecordType::Txt, &msg, 0, 12).unwrap();
        if let RData::Txt(strings) = rdata {
            assert_eq!(strings.len(), 2);
            assert_eq!(strings[0], b"hello");
            assert_eq!(strings[1], b"world");
        } else {
            panic!("Expected TXT record");
        }
    }

    #[test]
    fn test_truncated_buffer_returns_error() {
        // Buffer too short for header
        let msg = [0xAB, 0xCD, 0x81]; // only 3 bytes
        let result = DnsMessage::parse(&msg);
        assert!(matches!(result, Err(DnsError::BufferTooShort { .. })));
    }

    #[test]
    fn test_record_type_roundtrip() {
        for (n, expected) in [
            (1u16, RecordType::A),
            (28, RecordType::Aaaa),
            (15, RecordType::Mx),
            (16, RecordType::Txt),
            (999, RecordType::Unknown(999)),
        ] {
            let t = RecordType::from_u16(n);
            assert_eq!(t, expected);
        }
    }
}
```

### 17.2 Fuzzing (C)

```c
/* fuzz_dns_parser.c — libFuzzer target for DNS message parser
 * Build: clang -O1 -fsanitize=fuzzer,address,undefined -o fuzz_dns fuzz_dns_parser.c dns_resolver.c
 * Run:   ./fuzz_dns corpus/ -max_len=65535 -jobs=8
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

/* Forward declarations from dns_resolver.c */
extern int dns_parse_message(const uint8_t *buf, size_t buflen, void *msg);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    /* Allocate a zeroed message struct (must match dns_message_t) */
    uint8_t msg_buf[65536] = {0};
    
    /* The fuzzer provides arbitrary bytes as a "DNS message" */
    /* Our parser must not crash, hang, or corrupt memory */
    dns_parse_message(data, size, msg_buf);
    
    return 0;
}
```

### 17.3 Fuzzing (Rust — cargo-fuzz)

```rust
// fuzz/fuzz_targets/fuzz_dns_parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // Should never panic, only return Err
    let _ = dns_resolver::DnsMessage::parse(data);
    
    // Also test name decoder
    if data.len() >= 2 {
        let _ = dns_resolver::Name::decode(data, 0);
    }
});
```

```bash
# Setup
cargo install cargo-fuzz
cargo fuzz init

# Run
cargo fuzz run fuzz_dns_parse -- -max_len=65535

# With AddressSanitizer + coverage
RUSTFLAGS="-C instrument-coverage" cargo fuzz run fuzz_dns_parse

# Minimize corpus
cargo fuzz cmin fuzz_dns_parse -- fuzz/corpus/fuzz_dns_parse/
```

### 17.4 Integration Testing with dig

```bash
#!/usr/bin/env bash
# test_dns_resolver.sh — Integration test suite

BINARY="./dns_resolver"
RESOLVER="8.8.8.8"
FAILURES=0

run_test() {
    local desc="$1"; local expected_exit="$2"; shift 2
    echo -n "TEST: $desc ... "
    $BINARY "$@" > /dev/null 2>&1
    local actual=$?
    if [ "$actual" -eq "$expected_exit" ]; then
        echo "PASS"
    else
        echo "FAIL (expected exit $expected_exit, got $actual)"
        FAILURES=$((FAILURES + 1))
    fi
}

# Basic resolution tests
run_test "A record for example.com"     0   example.com A  "@$RESOLVER"
run_test "AAAA record for ipv6.google"  0   ipv6.google.com AAAA "@$RESOLVER"
run_test "MX record for gmail.com"      0   gmail.com MX "@$RESOLVER"
run_test "TXT record for gmail.com"     0   gmail.com TXT "@$RESOLVER"
run_test "NS record for example.com"    0   example.com NS "@$RESOLVER"
run_test "SOA record for example.com"   0   example.com SOA "@$RESOLVER"

# NXDOMAIN tests
run_test "NXDOMAIN for nonexistent"     1   thisdoesnotexist12345xyz.com A "@$RESOLVER"

# DNSSEC tests
run_test "DNSSEC A for cloudflare.com"  0   cloudflare.com A "@1.1.1.1" +dnssec

# Edge cases
run_test "Root zone NS"                 0   . NS "@$RESOLVER"

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "All tests PASSED"
else
    echo "$FAILURES test(s) FAILED"
    exit 1
fi
```

### 17.5 Benchmarking

```bash
# Using dnsperf (ISC tool)
# Install: apt-get install dnsperf

# Generate query file
for domain in google.com youtube.com amazon.com; do
    echo "$domain A"
done > queryfile.txt

# Benchmark against resolver
dnsperf -s 8.8.8.8 -d queryfile.txt -l 30 -c 10 -Q 1000

# Expected output format:
# DNS Performance Testing Tool
# Queries sent:         30000
# Queries completed:    29998 (100.0%)
# Average latency:      2.531 ms
# Maximum latency:      45.234 ms
# Queries per second:   999.9

# Rust benchmarks with criterion
# Add to Cargo.toml:
# [dev-dependencies]
# criterion = "0.5"
# [[bench]]
# name = "dns_bench"
# harness = false

# benches/dns_bench.rs:
# use criterion::{black_box, criterion_group, criterion_main, Criterion};
# fn bench_name_encode(c: &mut Criterion) {
#     c.bench_function("name_encode", |b| {
#         let name = Name::new("www.example.com");
#         b.iter(|| {
#             let mut buf = Vec::with_capacity(32);
#             black_box(name.encode(&mut buf).unwrap());
#         })
#     });
# }
```

---

## 18. Threat Model

### 18.1 Architecture View

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    THREAT ZONES                         │
                    └─────────────────────────────────────────────────────────┘

[Attacker]
    │
    ├── Off-path (no routing position)
    │     Threat: TXID/port brute-force spoofing
    │     Mitigation: Port randomization, DNSSEC, Cookies
    │
    ├── On-path (MITM, malicious ISP, BGP hijack)
    │     Threat: Response manipulation, eavesdropping
    │     Mitigation: DNSSEC + DoT/DoH/DoQ
    │
    ├── Local network (same LAN as client/resolver)
    │     Threat: ARP spoofing → intercept resolver traffic
    │     Mitigation: Encrypted transport DoT/DoH, DNSSEC
    │
    ├── Malicious resolver (compromised upstream)
    │     Threat: Return wrong answers, log queries
    │     Mitigation: DNSSEC validation at stub, authenticated DoT
    │
    ├── Authoritative server compromise
    │     Threat: Inject false records
    │     Mitigation: DNSSEC signing, TSIG for zone transfers, registrar lock
    │
    └── Application layer
          Threat: DNS rebinding, SSRF via DNS, subdomain takeover
          Mitigation: Private IP filtering, Host header validation, CNAME monitoring
```

### 18.2 Assets, Threats, Mitigations

| Asset | Threat | STRIDE | Mitigation | Residual Risk |
|-------|--------|--------|------------|---------------|
| DNS cache integrity | Cache poisoning | Tampering | Port randomization + DNSSEC | Low (DNSSEC signed zones) |
| Query privacy | Traffic analysis | Info Disclosure | DoT/DoH + EDNS PADDING | Medium (timing correlation) |
| Zone data | Zone enumeration | Info Disclosure | NSEC3 with random salt | Medium (offline hash attack) |
| Zone data | Unauthorized AXFR | Info Disclosure | TSIG, IP ACL | Low |
| Resolver availability | Amplification DDoS | DoS | RRL, BCP38, Cookies | Medium |
| Name resolution | NXDOMAIN hijacking | Spoofing | DoH to trusted resolver | Low |
| Zone signing keys | Key compromise | Elevation | HSM, key ceremonies, fast rollover | Low |
| Registrar account | Domain hijacking | Elevation | 2FA, registry lock (REGLOCK) | Low |
| Kubernetes DNS | ndots search domain abuse | Spoofing | ndots:1, use FQDNs | Medium |
| Cloud metadata DNS | DNS rebinding → SSRF | Spoofing | IMDSv2, Host header validation | Low (with IMDSv2) |

### 18.3 DNSSEC Deployment Decision Tree

```
Is your zone public and externally resolved?
  YES →
    Do your registrar and TLD support DS records?
      YES → Deploy DNSSEC (algorithm 13 ECDSA P-256 or 15 Ed25519)
      NO → Push registrar/TLD to support it; use DLV (legacy, not recommended)
  NO (internal) →
    Configure trust anchors in internal resolvers manually
    Use TSIG for zone transfer security
    Consider DNSSEC for high-security zones even internally

Do you have HSM capabilities?
  YES → Store KSK in HSM (PKCS#11)
  NO → Minimum: KSK on air-gapped system; ZSK on signer

Automate with:
  - OpenDNSSEC (policy-based signing automation)
  - BIND inline-signing (simpler, less flexible)
  - Cloudflare/Route53 managed DNSSEC (fully automated)
```

---

## 19. Next 3 Steps

1. **Implement TCP fallback in the C/Rust resolver**: Detect `TC=1` in UDP response, reconnect via TCP with 2-byte length framing, re-send same query. Test with zones that return large DNSSEC responses. This makes your resolver RFC 7766-compliant.

2. **Add DNSSEC chain validation**: Extend the Rust resolver to perform full DNSSEC chain validation — fetch DNSKEY and DS records, verify RRSIG signatures using `ring` or `openssl` crate, walk the chain from response up to root trust anchor. Start with algorithm 13 (ECDSA P-256). Test against `dnssec-failed.org` (intentionally broken DNSSEC) and `dnssec-tools.org` (valid).

3. **Deploy a production Unbound recursive resolver with full hardening**: Configure QNAME minimization, DNSSEC validation, aggressive NSEC/NSEC3, serve-stale, prefetching, DNS Cookies, response rate limiting, and RPZ-based blocking. Export metrics to Prometheus via the unbound-exporter, set up alerting on SERVFAIL rate, NXDOMAIN rate, and cache hit ratio. This is the real-world system that all the theory above maps to.

---

## 20. References and RFCs

### Core Protocol

| RFC | Title |
|-----|-------|
| RFC 1034 | Domain Names — Concepts and Facilities |
| RFC 1035 | Domain Names — Implementation and Specification |
| RFC 1123 | Requirements for Internet Hosts |
| RFC 2181 | Clarifications to the DNS Specification |
| RFC 2308 | Negative Caching of DNS Queries |
| RFC 3596 | DNS Extensions to Support IP Version 6 |
| RFC 6891 | Extension Mechanisms for DNS (EDNS(0)) |
| RFC 7766 | DNS Transport over TCP — Implementation Requirements |

### Security

| RFC | Title |
|-----|-------|
| RFC 4033 | DNS Security Introduction and Requirements |
| RFC 4034 | Resource Records for the DNS Security Extensions |
| RFC 4035 | Protocol Modifications for the DNS Security Extensions |
| RFC 5155 | DNS Security (DNSSEC) Hashed Authenticated Denial of Existence |
| RFC 5452 | Measures for Making DNS More Resilient against Forged Answers |
| RFC 7873 | Domain Name System (DNS) Cookies |
| RFC 8624 | Algorithm Implementation Requirements and Usage Guidance for DNSSEC |
| RFC 9276 | Guidance for NSEC3 Parameter Settings |
| RFC 6698 | The DNS-Based Authentication of Named Entities (DANE) |

### Privacy & Transport

| RFC | Title |
|-----|-------|
| RFC 7816 | DNS Query Name Minimisation to Improve Privacy |
| RFC 7858 | Specification for DNS over Transport Layer Security (TLS) |
| RFC 8310 | Usage Profiles for DNS over TLS and DNS over DTLS |
| RFC 8484 | DNS Queries over HTTPS (DoH) |
| RFC 9230 | Oblivious DNS over HTTPS |
| RFC 9250 | DNS over Dedicated QUIC Connections |
| RFC 7830 | The EDNS(0) Padding Option |

### Operations & Extensions

| RFC | Title |
|-----|-------|
| RFC 1995 | Incremental Zone Transfer in DNS |
| RFC 1996 | A Mechanism for Prompt Notification of Zone Changes (DNS NOTIFY) |
| RFC 2136 | Dynamic Updates in the Domain Name System (DNS UPDATE) |
| RFC 2782 | A DNS RR for specifying the location of services (DNS SRV) |
| RFC 2845 | Secret Key Transaction Authentication for DNS (TSIG) |
| RFC 6672 | DNAME Redirection in the DNS |
| RFC 7344 | Automating DNSSEC Delegation Trust Maintenance |
| RFC 7871 | Client Subnet in DNS Queries (ECS) |
| RFC 8659 | DNS Certification Authority Authorization (CAA) Resource Record |
| RFC 8767 | Serving Stale Data to Improve DNS Resiliency |
| RFC 8914 | Extended DNS Errors |
| RFC 9460 | Service Binding and Parameter Specification via the DNS (SVCB and HTTPS) |

### Tools and References

- **BIND 9**: https://bind9.readthedocs.io/
- **Unbound**: https://nlnetlabs.nl/documentation/unbound/
- **Knot DNS/Resolver**: https://www.knot-dns.cz/
- **CoreDNS**: https://coredns.io/
- **PowerDNS**: https://doc.powerdns.com/
- **dnsviz** (DNSSEC visualizer): https://dnsviz.net/
- **IANA Root Zone**: https://www.iana.org/domains/root
- **Root Hints**: https://www.internic.net/domain/named.root
- **DNS Flag Day 2020**: https://dnsflagday.net/2020/
- **Verisign DNSSEC Root Trust Anchor**: https://www.iana.org/dnssec/files
- **RFC 8624 Algorithm Guidance**: https://www.rfc-editor.org/rfc/rfc8624