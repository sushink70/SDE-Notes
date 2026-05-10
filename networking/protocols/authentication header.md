# Authentication Header (AH) Protocol — Complete In-Depth Guide

> **Mental Model Goal:** By the end of this guide, you will be able to mentally simulate exactly what happens to every single byte in a network packet when AH protection is applied — from handshake to verification, from sender to receiver.

---

## Table of Contents

1. [The Big Picture — Why AH Exists](#1-the-big-picture--why-ah-exists)
2. [The IPsec Family — Where AH Lives](#2-the-ipsec-family--where-ah-lives)
3. [Core Vocabulary You Must Know](#3-core-vocabulary-you-must-know)
4. [AH Protocol Fundamentals](#4-ah-protocol-fundamentals)
5. [AH Header Structure — Byte by Byte](#5-ah-header-structure--byte-by-byte)
6. [Security Association (SA) — The Contract](#6-security-association-sa--the-contract)
7. [Cryptographic Mechanisms in AH](#7-cryptographic-mechanisms-in-ah)
8. [AH Transport Mode — Deep Dive](#8-ah-transport-mode--deep-dive)
9. [AH Tunnel Mode — Deep Dive](#9-ah-tunnel-mode--deep-dive)
10. [Anti-Replay Mechanism](#10-anti-replay-mechanism)
11. [Packet Processing — Outbound (Sender)](#11-packet-processing--outbound-sender)
12. [Packet Processing — Inbound (Receiver)](#12-packet-processing--inbound-receiver)
13. [Mutable vs Immutable Fields](#13-mutable-vs-immutable-fields)
14. [AH vs ESP — The Critical Difference](#14-ah-vs-esp--the-critical-difference)
15. [AH and NAT — A Fatal Incompatibility](#15-ah-and-nat--a-fatal-incompatibility)
16. [IKE — Key Management for AH](#16-ike--key-management-for-ah)
17. [AH in IPv4 vs IPv6](#17-ah-in-ipv4-vs-ipv6)
18. [Real RFC 4302 Packet Diagrams (ASCII)](#18-real-rfc-4302-packet-diagrams-ascii)
19. [C Implementation — Full Working Code](#19-c-implementation--full-working-code)
20. [Rust Implementation — Full Working Code](#20-rust-implementation--full-working-code)
21. [Security Analysis and Attack Vectors](#21-security-analysis-and-attack-vectors)
22. [Mental Models and Summary](#22-mental-models-and-summary)

---

## 1. The Big Picture — Why AH Exists

### The Problem AH Solves

Imagine you send a letter. Without any protection:

```
SENDER                     NETWORK (Untrusted)               RECEIVER
  |                               |                               |
  |--- "Transfer $100 to Bob" --->|                               |
  |                               |  [Attacker intercepts]        |
  |                               |  [Changes to $10000 to Eve]   |
  |                               |--- "Transfer $10000 to Eve" ->|
  |                               |                               |
```

Three fundamental threats exist in any network:

| Threat                | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Eavesdropping**     | Attacker reads your data (confidentiality breach)                           |
| **Tampering**         | Attacker modifies your data in transit (integrity breach)                   |
| **Impersonation**     | Attacker pretends to be you or the server (authentication breach)           |
| **Replay Attack**     | Attacker re-sends a captured valid packet to trigger the same action again  |

### What AH Specifically Solves

AH (Authentication Header) is a protocol designed to solve **three** of these four threats:

```
AH GUARANTEES:
  [1] DATA INTEGRITY     — The packet was NOT modified in transit
  [2] ORIGIN AUTHENTICATION — The packet genuinely came from who it claims
  [3] ANTI-REPLAY        — This packet was NOT a replayed old packet

AH DOES NOT PROVIDE:
  [X] CONFIDENTIALITY    — AH does NOT encrypt data (anyone can read it)
```

> **Key Mental Model:** AH is like a tamper-evident wax seal on a transparent envelope.
> - You can read the letter (no encryption).
> - But you can PROVE it hasn't been touched (integrity).
> - And you can PROVE who sealed it (authentication).

---

## 2. The IPsec Family — Where AH Lives

### What is IPsec?

**IPsec** stands for **Internet Protocol Security**. It is a *suite* (a collection) of protocols that work at the **Network Layer (Layer 3)** of the OSI model to secure IP communications.

```
OSI MODEL LAYERS:
+---------------------------+
|  Layer 7: Application     |  (HTTP, FTP, SSH...)
+---------------------------+
|  Layer 6: Presentation    |  (TLS, SSL...)
+---------------------------+
|  Layer 5: Session         |
+---------------------------+
|  Layer 4: Transport       |  (TCP, UDP)
+---------------------------+
|  Layer 3: Network         |  <--- IPsec LIVES HERE (AH, ESP)
+---------------------------+
|  Layer 2: Data Link       |  (Ethernet, Wi-Fi)
+---------------------------+
|  Layer 1: Physical        |  (Cables, Radio waves)
+---------------------------+
```

### IPsec Protocol Suite Components

```
IPsec Suite
├── AH  (Authentication Header)        — RFC 4302 — Integrity + Auth
├── ESP (Encapsulating Security Payload) — RFC 4303 — Encrypt + Auth + Integrity
├── IKE (Internet Key Exchange)        — RFC 7296 — Key Management
└── SA  (Security Association)         — The "session" concept tying it together
```

### Why Layer 3?

Operating at Layer 3 means IPsec protects ALL traffic, regardless of the application. No application changes are needed. This is called **transparent security** — apps above (HTTP, FTP, etc.) don't need to know about it.

Compare this to TLS (Layer 6), which requires each application to implement it.

---

## 3. Core Vocabulary You Must Know

Before we go deeper, cement these terms. Every term below will appear repeatedly.

### Datagram / Packet

A **packet** (formally called a datagram in IP) is a unit of data transmitted across a network. It has:

```
+------------------+------------------+
|    HEADER        |    PAYLOAD       |
| (routing info,   | (actual data     |
|  protocol info)  |  being carried)  |
+------------------+------------------+
```

### Protocol Number

Every protocol that rides on top of IP is assigned a unique number called the **IP Protocol Number**. This tells the receiving machine what type of payload follows the IP header.

```
Protocol Number  |  Protocol
-----------------+----------
      1          |  ICMP (ping)
      6          |  TCP
     17          |  UDP
     50          |  ESP (IPsec)
     51          |  AH  (IPsec)  <--- AH's identifier
```

### SPI (Security Parameters Index)

A **32-bit number** that, combined with the destination IP address and the security protocol (AH or ESP), uniquely identifies a **Security Association (SA)** — the set of parameters used to protect a communication.

Think of it as: "Use rule #42 to process this packet."

### ICV (Integrity Check Value)

The **cryptographic hash** appended to the AH header. It is the "digital fingerprint" of the packet. If even one bit changes, the ICV will not match.

### HMAC (Hash-based Message Authentication Code)

A method to produce a **keyed hash**. Unlike a plain hash (SHA-256), HMAC uses a **secret key** combined with the data. This means:
- Only someone with the key can produce a valid HMAC.
- An attacker cannot fake the HMAC without the key, even if they can see the message.

```
HMAC(key, message) = Hash(key XOR opad || Hash(key XOR ipad || message))
```

### Mutable Fields

Fields in the IP header that **change as the packet travels** through the network (e.g., TTL — Time To Live decrements at each router hop). AH must handle these specially, as you'll see.

### Security Association (SA)

A **one-way agreement** between two parties about how to protect traffic. Like a contract that says: "I will use HMAC-SHA256 with key K to authenticate packets going from A to B."

---

## 4. AH Protocol Fundamentals

### RFC Reference

AH is formally defined in **RFC 4302** (published December 2005), which obsoleted the older RFC 2402.

- RFC = Request for Comments = the official specification documents of the Internet.

### What AH Does — Step by Step at a High Level

```
SENDER SIDE:
  1. Take the outgoing IP packet
  2. Insert an AH header between IP header and the original payload
  3. Compute HMAC over: [fixed IP fields + AH header (with ICV=0) + payload]
  4. Place the HMAC result into the ICV field of the AH header
  5. Send the packet

RECEIVER SIDE:
  1. Receive the packet, detect AH (Protocol Number = 51)
  2. Look up the SA using SPI + destination IP
  3. Check Sequence Number (anti-replay)
  4. Zero out the mutable IP fields
  5. Recompute HMAC over same fields
  6. Compare recomputed HMAC with received ICV
  7. If match: packet is authentic and unmodified → ACCEPT
  8. If mismatch: packet was tampered with or wrong key → DROP
```

### AH's Position in an IP Packet

```
TRANSPORT MODE (Host-to-Host):

  Original Packet:
  +----------+---------------------------+
  | IP Header|       TCP/UDP Payload     |
  +----------+---------------------------+

  After AH:
  +----------+-----------+---------------+
  | IP Header| AH Header |TCP/UDP Payload|
  +----------+-----------+---------------+
       |           |             |
  Protocol=51  Contains ICV   Authenticated
               (HMAC result)

TUNNEL MODE (Gateway-to-Gateway):

  Original Packet:
  +----------+---------------------------+
  | IP Header|       TCP/UDP Payload     |
  +----------+---------------------------+

  After AH Tunnel:
  +----------+-----------+----------+---------------------------+
  |New IP Hdr| AH Header |Orig IP   |       TCP/UDP Payload     |
  +----------+-----------+----------+---------------------------+
       |           |          |_____________________________|
  New outer IP  HMAC of all  The entire original packet
                              is authenticated
```

---

## 5. AH Header Structure — Byte by Byte

### The AH Header Format (RFC 4302)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Next Header   |  Payload Len  |          RESERVED             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Security Parameters Index (SPI)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Sequence Number Field                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                Integrity Check Value - ICV                    +
|              (variable length, MUST be 32-bit aligned)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field-by-Field Explanation

#### Field 1: Next Header (8 bits = 1 byte)

```
+---------------+
| Next Header   |
| (8 bits)      |
+---------------+
```

- **What it is:** Identifies the type of payload that comes AFTER the AH header.
- **Why it matters:** The receiver needs to know what to do with the data after AH.
- **Common values:**
  - `6` = TCP (the AH protects a TCP segment)
  - `17` = UDP (the AH protects a UDP datagram)
  - `4` = IP-in-IP (tunnel mode, another IP header follows)
  - `41` = IPv6 header follows
- **In transport mode:** This is the original protocol (TCP=6, UDP=17).
- **In tunnel mode:** This is `4` (IPv4) or `41` (IPv6), indicating another IP header.

```
Example in Transport Mode (protecting TCP):
  IP Header [Protocol=51] → AH Header [Next Header=6] → TCP Segment
                                                            ^
                                              Next Header=6 points here
```

#### Field 2: Payload Length (8 bits = 1 byte)

```
+---------------+
| Payload Len   |
| (8 bits)      |
+---------------+
```

- **What it is:** The length of the AH header itself (not the data payload!).
- **Confusing name warning:** Despite being called "Payload Length," it measures the AH header length.
- **How to compute:** `(AH header length in bytes / 4) - 2`
- **Why the formula?** RFC 4302 uses a specific convention from IPv6 extension headers.

```
Example calculation:
  AH header = 12 bytes (fixed) + 12 bytes (ICV for HMAC-SHA1) = 24 bytes
  Payload Length = (24 / 4) - 2 = 6 - 2 = 4
```

#### Field 3: Reserved (16 bits = 2 bytes)

```
+-----------------+
|    RESERVED     |
|  (16 bits)      |
+-----------------+
```

- **Must be all zeros** when transmitted.
- **Must be ignored** by the receiver (forward compatibility).
- Exists for alignment and future use.

#### Field 4: Security Parameters Index — SPI (32 bits = 4 bytes)

```
+-------------------------------+
|            SPI                |
|         (32 bits)             |
+-------------------------------+
```

- **The most critical field for lookup.**
- A **32-bit unsigned integer** chosen by the **receiver** during SA negotiation (via IKE).
- Combined with destination IP + protocol (AH=51), it uniquely identifies which **Security Association** (set of rules and keys) applies to this packet.
- Values `0x00000001` to `0x000000FF` are reserved by IANA.
- Value `0x00000000` is reserved (means "no SPI" in local use).

```
HOW SPI IS USED:

Receiver gets a packet. It asks:
  "Destination IP = 10.0.0.5"
  "Protocol = AH (51)"
  "SPI = 0x00001234"

It looks up in the SAD (Security Association Database):
  (10.0.0.5, AH, 0x00001234) → SA entry with key K, algorithm HMAC-SHA256

Now it knows how to verify the packet.
```

#### Field 5: Sequence Number (32 bits = 4 bytes)

```
+-------------------------------+
|      Sequence Number          |
|         (32 bits)             |
+-------------------------------+
```

- **Starts at 1** for the first packet in an SA.
- **Increments by 1** for every subsequent packet.
- **Never repeats** — if it reaches `0xFFFFFFFF` (4,294,967,295), the SA MUST be renegotiated.
- **Purpose:** Enable the **anti-replay mechanism** at the receiver.
- **Extended Sequence Number (ESN):** RFC 4302 also supports a 64-bit sequence number to avoid rollover for high-speed links (only 32 bits in the header; the upper 32 bits are virtual).
- The sequence number is **always included** in the ICV computation (it is authenticated).

#### Field 6: Integrity Check Value — ICV (variable length)

```
+-------------------------------+
|            ICV                |
|   (variable, 32-bit aligned)  |
+-------------------------------+
```

- The **cryptographic signature** of the packet — the HMAC output.
- **Length depends on the algorithm:**
  - HMAC-MD5-96: 96 bits = 12 bytes
  - HMAC-SHA1-96: 96 bits = 12 bytes
  - HMAC-SHA256-128: 128 bits = 16 bytes
  - HMAC-SHA384-192: 192 bits = 24 bytes
  - HMAC-SHA512-256: 256 bits = 32 bytes
- **Must be 32-bit aligned** — padding added if needed (padding bits are zeros).
- **During computation:** The ICV field is treated as all zeros.

---

## 6. Security Association (SA) — The Contract

### What is a Security Association?

An SA is a **one-directional, uniquely identified security context**. It's the set of all parameters agreed upon for securing a communication channel.

> **Mental Model:** An SA is like a **pre-agreed cipher book** between two spies.
> "When I send you a message with label #42, use codebook Alpha with key Zebra."

### SA is Unidirectional

This is crucial. A **full duplex** (two-way) protected connection requires **two SAs**:

```
HOST A ────────────────────────────────────────── HOST B

  SA_1: A→B  (SPI=0x1234, key=K1, algo=HMAC-SHA256)
  ─────────────────────────────────────────────────►

  SA_2: B→A  (SPI=0x5678, key=K2, algo=HMAC-SHA256)
  ◄─────────────────────────────────────────────────
```

### What an SA Contains

```
Security Association (SA) Parameters:
┌────────────────────────────────────────────────────┐
│  Identifier:                                        │
│    - SPI (32-bit)                                   │
│    - Destination IP Address                         │
│    - Security Protocol (AH=51 or ESP=50)            │
│                                                     │
│  Cryptographic Material:                            │
│    - Authentication Algorithm (e.g., HMAC-SHA256)   │
│    - Authentication Key (e.g., 256-bit key)         │
│    - Key Length                                     │
│                                                     │
│  Operational Parameters:                            │
│    - Sequence Number Counter (starts at 0)          │
│    - Anti-Replay Window (64 or 128 bits wide)       │
│    - SA Lifetime (bytes or time)                    │
│    - Mode (Transport or Tunnel)                     │
│    - Path MTU (Maximum Transmission Unit)           │
│                                                     │
│  (For AH — no encryption key, AH doesn't encrypt)  │
└────────────────────────────────────────────────────┘
```

### SAD (Security Association Database)

The **SAD** is a local database (on each host) that stores all active SAs. When a packet arrives with AH, the host does a lookup:

```
LOOKUP KEY:  (Destination IP, Protocol=AH, SPI)
RETURNS:     Full SA entry with key, algorithm, replay window, etc.

Example SAD entry:
+-------------+----------+------+---------------+------------------+----------+
| Dest IP     | Protocol | SPI  | Auth Algorithm| Auth Key         | Seq. Num |
+-------------+----------+------+---------------+------------------+----------+
| 192.168.1.5 | AH (51)  | 1234 | HMAC-SHA256   | 0xABCD...EF01    | 1042     |
| 10.0.0.1    | AH (51)  | 5678 | HMAC-SHA1-96  | 0x1234...5678    | 77       |
+-------------+----------+------+---------------+------------------+----------+
```

### SPD (Security Policy Database)

The **SPD** defines the *policy* — what to do with packets matching certain criteria. It comes **before** the SAD.

```
Traffic arrives → SPD lookup → Policy Decision:
  ┌──────────────────────┐
  │  BYPASS  │ Don't apply IPsec (plain traffic OK)    │
  │  DISCARD │ Drop the packet (traffic not allowed)   │
  │  PROTECT │ Apply IPsec (AH or ESP) → then SAD lookup│
  └──────────────────────┘
```

```
Example SPD rules:
  - Traffic from 10.0.0.0/8 to 10.0.0.0/8, TCP port 80 → PROTECT with AH
  - ICMP traffic → BYPASS
  - All other traffic → DISCARD
```

---

## 7. Cryptographic Mechanisms in AH

### HMAC — The Foundation of AH Authentication

**HMAC (Hash-based Message Authentication Code)** combines a **cryptographic hash function** with a **secret key** to produce an authentication code.

#### Why Not Just Use a Hash (SHA-256)?

If AH just used `SHA-256(packet)`, an attacker could:
1. Intercept the packet.
2. Modify the data.
3. Recompute `SHA-256(modified_packet)`.
4. Replace the hash.

The receiver would accept it! Without the key, you cannot produce a valid MAC.

#### HMAC Construction

```
HMAC(K, m) = H((K' XOR opad) || H((K' XOR ipad) || m))

Where:
  K'   = K padded to block size (or hashed if K is too long)
  ipad = 0x36 repeated to block size
  opad = 0x5C repeated to block size
  H    = hash function (SHA-1, SHA-256, etc.)
  ||   = concatenation
```

```
Step-by-step HMAC-SHA256:

  1. K' = K padded to 64 bytes
  2. inner_key = K' XOR ipad  (XOR each byte with 0x36)
  3. inner_hash = SHA256(inner_key || message)
  4. outer_key = K' XOR opad  (XOR each byte with 0x5C)
  5. HMAC = SHA256(outer_key || inner_hash)
```

#### Why HMAC is Secure

- **Cannot forge without key:** Attacker doesn't know K, can't compute valid HMAC.
- **Collision resistance:** Even small changes to message produce completely different HMAC.
- **Length extension attack resistant:** Unlike plain `H(K||m)`, HMAC is immune.

### Mandatory and Recommended Algorithms (RFC 4302, RFC 8221)

```
Algorithm               | Key Size  | ICV Size | Status
------------------------|-----------|----------|------------------
HMAC-SHA1-96            | 160 bits  | 96 bits  | MUST implement
HMAC-SHA256-128         | 256 bits  | 128 bits | SHOULD implement
HMAC-SHA384-192         | 384 bits  | 192 bits | MAY implement
HMAC-SHA512-256         | 512 bits  | 256 bits | MAY implement
AES-XCBC-MAC-96         | 128 bits  | 96 bits  | SHOULD implement
AES-CMAC-96             | 128 bits  | 96 bits  | SHOULD implement
HMAC-MD5-96             | 128 bits  | 96 bits  | MUST NOT (deprecated)
```

> **Note:** MD5 and SHA-1 are cryptographically weak. Modern implementations use SHA-256 or better.

### What Exactly is Authenticated (Covered by ICV)?

```
AH authenticates EVERYTHING EXCEPT mutable fields:

AUTHENTICATED:
  - IP source address (immutable in transit)
  - IP destination address (immutable)
  - AH header fields (Next Header, Payload Len, Reserved, SPI, Seq Num)
  - AH ICV field treated as ZERO during computation
  - Entire payload (TCP/UDP segment, or tunneled IP packet)

NOT AUTHENTICATED (zeroed out before computation):
  - IP TTL (changes at each router hop)
  - IP ToS/DSCP (may change for QoS)
  - IP Flags (DF bit may change)
  - IP Fragment Offset (fragmentation changes this)
  - IP Header Checksum (changes because TTL changes)
  - IPv6 Hop Limit (like TTL)
  - IPv6 Flow Label (may change)
```

---

## 8. AH Transport Mode — Deep Dive

### What is Transport Mode?

Transport mode protects the **payload of the IP packet** but keeps the **original IP header** largely intact. It is used for **host-to-host** communication.

```
BEFORE AH (Original Packet):
┌────────────────────────────────────────────────────────────┐
│ IP Header  │ TCP/UDP Header │         Data                 │
│ Src: A     │                │                              │
│ Dst: B     │                │                              │
│ Proto: 6   │                │                              │
└────────────────────────────────────────────────────────────┘
  |___________________________________________________|
                  Total Packet

AFTER AH Transport Mode:
┌────────────────────────────────────────────────────────────┐
│ IP Header  │ AH Header     │ TCP/UDP Header │    Data      │
│ Src: A     │ Next Hdr: 6   │                │              │
│ Dst: B     │ SPI: 0x1234   │                │              │
│ Proto: 51  │ Seq: 42       │                │              │
│            │ ICV: [HMAC]   │                │              │
└────────────────────────────────────────────────────────────┘
  |___________________________________________________|
  |           |_______________________________________|
  | Original  |     AH inserted here                  |
  | IP Hdr    |     (Protocol changed 6→51)            |
  | modified  |                                        |
```

### How the IP Header Changes in Transport Mode

```
ORIGINAL IP HEADER FIELD      → VALUE AFTER AH INSERTION
─────────────────────────────────────────────────────────
Protocol (was TCP=6)          → 51 (AH protocol number)
Total Length                  → Increased by AH header size
Everything else               → Unchanged
```

### Transport Mode: Full ASCII Packet Diagram

```
Transport Mode AH IPv4 Packet:

Byte:  0        7 8      15 16     23 24     31
       +─────────+─────────+─────────+─────────+
 0     │ Version │   IHL   │   TOS   │ Total Length    │  IPv4 Header
       +─────────+─────────+─────────+─────────+
 4     │    Identification           │Flags│ Frag Off   │
       +─────────────────────────────+─────+─────────+
 8     │    TTL  │ Proto=51│    Header Checksum        │
       +─────────+─────────+───────────────────────────+
12     │              Source IP Address                │
       +───────────────────────────────────────────────+
16     │            Destination IP Address             │
       +───────────────────────────────────────────────+
       ╔═══════════════════════════════════════════════╗
20     ║  Next Header  │  Payload Len│    RESERVED      ║  AH Header
       ╠═══════════════════════════════════════════════╣
24     ║              SPI (32 bits)                    ║
       ╠═══════════════════════════════════════════════╣
28     ║            Sequence Number (32 bits)          ║
       ╠═══════════════════════════════════════════════╣
32     ║                                               ║
       ║              ICV (variable)                   ║
44     ║              (12 bytes for HMAC-SHA1-96)      ║
       ╚═══════════════════════════════════════════════╝
44     ┌───────────────────────────────────────────────┐
       │           TCP/UDP Header + Data               │  Payload
       └───────────────────────────────────────────────┘

Legend:
  [ ] = IPv4 Header (authenticated with mutable fields zeroed)
  [=] = AH Header   (SPI, SeqNum authenticated; ICV zeroed during computation)
  [ ] = Payload     (fully authenticated)
```

---

## 9. AH Tunnel Mode — Deep Dive

### What is Tunnel Mode?

Tunnel mode **encapsulates the entire original IP packet** (including its IP header) inside a new IP packet and then applies AH protection. This creates an IP-within-IP structure.

Used primarily for:
- **VPN gateways** (protecting traffic between two networks)
- **Site-to-site VPNs**
- **Protecting the original IP header** (source/destination hidden from routers)

```
BEFORE (Original Packet from Host A to Host B):
┌──────────────────────────────────────────────┐
│  Inner IP Hdr  │  TCP/UDP  │     Data         │
│  Src: 10.0.0.1 │           │                  │
│  Dst: 10.0.0.5 │           │                  │
└──────────────────────────────────────────────┘

AFTER AH Tunnel Mode (Gateway G1 wraps it to send to Gateway G2):
┌──────────────────────────────────────────────────────────────────┐
│  Outer IP Hdr  │  AH Hdr  │  Inner IP Hdr  │  TCP/UDP  │  Data   │
│  Src: G1       │ Next:4   │  Src: 10.0.0.1 │           │         │
│  Dst: G2       │ SPI:0x99 │  Dst: 10.0.0.5 │           │         │
│  Proto: 51     │ ICV:[MAC]│                │           │         │
└──────────────────────────────────────────────────────────────────┘
  |____________|   |______|  |_____________________________________________|
  New outer IP    AH header  Entire original packet is authenticated
  (G1 to G2)     protects    (including inner IP header!)
                 all this →
```

### Tunnel Mode: Full ASCII Packet Diagram

```
Tunnel Mode AH IPv4 Packet:

       0        7 8      15 16     23 24     31
       +─────────+─────────+─────────+─────────+
 0     │ Ver=4   │   IHL   │   TOS   │   Total Length  │  OUTER IPv4 Header
       +─────────+─────────+─────────+─────────+        (new, added by gateway)
 4     │    Identification           │Flags│ Frag Off   │
       +─────────────────────────────+─────+─────────+
 8     │    TTL  │ Proto=51│    Header Checksum        │
       +─────────+─────────+───────────────────────────+
12     │         Outer Source IP (Gateway 1)            │
       +───────────────────────────────────────────────+
16     │         Outer Dest IP (Gateway 2)              │
       ╔═══════════════════════════════════════════════╗
20     ║  Next Header=4│  Payload Len│    RESERVED      ║  AH Header
       ╠═══════════════════════════════════════════════╣
24     ║              SPI (32 bits)                    ║
       ╠═══════════════════════════════════════════════╣
28     ║            Sequence Number (32 bits)          ║
       ╠═══════════════════════════════════════════════╣
32     ║                                               ║
       ║              ICV (12-32 bytes)                ║
       ╚═══════════════════════════════════════════════╝
       ┌───────────────────────────────────────────────┐
       │ Ver=4  │  IHL   │  TOS   │  Total Length       │  INNER IPv4 Header
       ├───────────────────────────────────────────────┤  (original, authenticated)
       │    Identification          │Flags│  Frag Off   │
       ├───────────────────────────────────────────────┤
       │   TTL  │ Proto=6│    Header Checksum           │
       ├───────────────────────────────────────────────┤
       │         Inner Source IP (Host A)               │
       ├───────────────────────────────────────────────┤
       │         Inner Dest IP (Host B)                 │
       ├───────────────────────────────────────────────┤
       │            TCP Header + Data                   │
       └───────────────────────────────────────────────┘

ICV covers: [Outer IP (mutable zeroed)] + [AH (ICV=0)] + [Inner IP + TCP + Data]
```

### Transport vs Tunnel Mode Comparison

```
Feature              │ Transport Mode          │ Tunnel Mode
─────────────────────┼─────────────────────────┼─────────────────────────
IP Header            │ Original preserved       │ New outer header added
Who uses it          │ End-hosts to end-hosts   │ Gateways (VPN)
Inner IP hidden?     │ No (original IP exposed) │ Yes (inner IP protected)
Authentication scope │ Payload only             │ Entire original packet
Overhead             │ AH header only           │ AH header + new IP header
Suitable for VPN     │ No (host must know SA)   │ Yes (gateway handles it)
```

---

## 10. Anti-Replay Mechanism

### The Replay Attack

Without protection, an attacker can:
1. Capture a valid authenticated packet.
2. Re-send it later.
3. The receiver will accept it as valid (the HMAC is correct!).

```
Replay Attack:
  T=1:  Alice → Bank: "Transfer $100 to Bob"  [HMAC valid]
  T=2:  Attacker captures and saves this packet
  T=5:  Attacker re-sends: "Transfer $100 to Bob"  [HMAC still valid!]
        Bank accepts it and transfers again!
```

### Sliding Window Anti-Replay

AH uses a **sliding window** mechanism to detect and reject replayed packets.

#### How It Works

The receiver maintains:
- **Right edge (N):** The highest sequence number received so far.
- **Window (W):** Typically 64 bits wide (configurable).
- **Bitmap:** A bitmap where bit i=1 means sequence number (N - i) has been received.

```
Window State Example (W=8 for illustration):

    Window (W=8 bits)
    ┌───────────────────────────────┐
    │  N-7  N-6  N-5  N-4  N-3  N-2  N-1  N  │
    │   1    0    1    1    0    1    1   1  │
    └───────────────────────────────┘
    N = 20 (highest received)

    Bit = 1: Seq num was received (duplicate would be rejected)
    Bit = 0: Not yet received (could still arrive)

    If seq = 20 arrives  → Already received → DROP (duplicate)
    If seq = 19 arrives  → bit[1]=1 → Already received → DROP
    If seq = 15 arrives  → bit[5]=0 → Not received → VERIFY HMAC → ACCEPT → set bit[5]=1
    If seq = 12 arrives  → 20-12=8 → Outside window (too old) → DROP
    If seq = 25 arrives  → Advance window → N=25, old bits shifted out
```

#### Detailed State Machine

```
PACKET ARRIVES with Sequence Number S:

                   ┌──────────────┐
                   │ S > N?       │
                   │(ahead of     │
                   │ window edge) │
                   └──────┬───────┘
                    YES   │    NO
           ┌──────────────┘    │
           ▼                   ▼
    ┌─────────────┐    ┌────────────────────┐
    │ Will advance│    │ S within window?   │
    │ window to S │    │ (N-W+1 <= S <= N)  │
    └──────┬──────┘    └────────┬───────────┘
           │               YES  │   NO (too old)
           │            ┌───────┘    │
           │            ▼            ▼
           │     ┌────────────┐  ┌────────┐
           │     │ bit[N-S]=1?│  │ DROP   │
           │     │(duplicate?)│  │(outside│
           │     └─────┬──────┘  │window) │
           │      YES  │  NO     └────────┘
           │       ┌───┘  │
           │       ▼      ▼
           │    ┌─────┐  ┌──────────────────┐
           │    │DROP │  │  VERIFY ICV       │
           │    │(dup)│  │  (compute HMAC)   │
           │    └─────┘  └────────┬─────────┘
           │                  OK  │  FAIL
           │              ┌───────┘    │
           │              ▼            ▼
           │          ┌────────┐   ┌────────┐
           └─────────►│ACCEPT  │   │  DROP  │
                      │update  │   │(tamper)│
                      │window  │   └────────┘
                      └────────┘
```

#### Why Window Instead of Just Rejecting Old Packets?

Networks are not perfectly ordered. Packet B sent after packet A might arrive first (out-of-order delivery). A small window (e.g., 64 packets) tolerates normal network reordering while still rejecting true replays.

---

## 11. Packet Processing — Outbound (Sender)

```
OUTBOUND AH PROCESSING (Sending a protected packet):

Step 1: SPD Lookup
  ┌─────────────────────────────────────────────────────┐
  │ Does traffic (src IP, dst IP, protocol, ports)      │
  │ match a policy requiring AH protection?             │
  └─────────────────────────────────────────────────────┘
                          │ YES
                          ▼
Step 2: SAD Lookup
  ┌─────────────────────────────────────────────────────┐
  │ Is there an active SA for this traffic?             │
  │ If no → trigger IKE to negotiate a new SA           │
  │ If yes → retrieve SA (key, algorithm, seq counter)  │
  └─────────────────────────────────────────────────────┘
                          │ SA found
                          ▼
Step 3: Check Sequence Number
  ┌─────────────────────────────────────────────────────┐
  │ If seq counter would overflow (reach 2^32)?         │
  │ → MUST NOT send → renegotiate SA (or use ESN)       │
  └─────────────────────────────────────────────────────┘
                          │ OK
                          ▼
Step 4: Construct AH Header
  ┌─────────────────────────────────────────────────────┐
  │ Fill: Next Header, Payload Length, Reserved=0       │
  │ Fill: SPI (from SA)                                 │
  │ Fill: Sequence Number (SA.seq_counter + 1)          │
  │ Fill: ICV = all zeros (placeholder)                 │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 5: Insert AH Header
  ┌─────────────────────────────────────────────────────┐
  │ Transport Mode: Insert AH between IP header and     │
  │   payload. Change IP Protocol field to 51.          │
  │ Tunnel Mode: Prepend new outer IP header,           │
  │   then AH header, before entire original packet.   │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 6: Prepare for HMAC Computation
  ┌─────────────────────────────────────────────────────┐
  │ Zero out MUTABLE fields in IP header:               │
  │   TTL, ToS, Flags (DF/MF), Fragment Offset,        │
  │   Header Checksum                                   │
  │ Zero out ICV field in AH header                     │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 7: Compute ICV
  ┌─────────────────────────────────────────────────────┐
  │ ICV = HMAC(auth_key, zeroed_packet)                 │
  │ Place ICV into AH header's ICV field                │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 8: Restore Mutable Fields
  ┌─────────────────────────────────────────────────────┐
  │ Restore IP TTL, ToS, Flags to actual values         │
  │ Recompute IP header checksum                        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 9: Increment Sequence Counter
  ┌─────────────────────────────────────────────────────┐
  │ SA.seq_counter++                                    │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 10: Transmit Packet
```

---

## 12. Packet Processing — Inbound (Receiver)

```
INBOUND AH PROCESSING (Receiving and verifying a protected packet):

Step 1: Detect AH
  ┌─────────────────────────────────────────────────────┐
  │ IP Protocol Number = 51? → This is an AH packet     │
  └─────────────────────────────────────────────────────┘
                          │ YES
                          ▼
Step 2: SA Lookup
  ┌─────────────────────────────────────────────────────┐
  │ Extract: SPI from AH header                         │
  │ Lookup SAD: (Destination IP, AH, SPI)               │
  │ Not found → DROP + log                              │
  └─────────────────────────────────────────────────────┘
                          │ SA found
                          ▼
Step 3: Anti-Replay Check
  ┌─────────────────────────────────────────────────────┐
  │ Extract Sequence Number S                           │
  │ Check against replay window:                        │
  │   - S outside window (too old)? → DROP              │
  │   - S already in window bitmap? → DROP (duplicate)  │
  │   - S valid? → Continue                             │
  └─────────────────────────────────────────────────────┘
                          │ S is valid candidate
                          ▼
Step 4: Save and Zero Mutable Fields
  ┌─────────────────────────────────────────────────────┐
  │ Save original TTL, ToS, Flags, Checksum             │
  │ Zero these mutable fields (same as sender did)      │
  │ Zero ICV field in AH header                         │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 5: Recompute ICV
  ┌─────────────────────────────────────────────────────┐
  │ computed_ICV = HMAC(auth_key, zeroed_packet)        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 6: Compare ICVs (constant-time comparison!)
  ┌─────────────────────────────────────────────────────┐
  │ received_ICV (from AH header) == computed_ICV?      │
  │   NO  → DROP (tampered or wrong key)                │
  │   YES → Continue                                    │
  └─────────────────────────────────────────────────────┘
                          │ Match!
                          ▼
Step 7: Update Anti-Replay Window
  ┌─────────────────────────────────────────────────────┐
  │ Mark sequence number S as received in bitmap        │
  │ If S > N (right edge), advance window: N = S        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
Step 8: Process Packet
  ┌─────────────────────────────────────────────────────┐
  │ Remove AH header                                    │
  │ Restore IP header (fix Protocol from 51 to original)│
  │ Pass packet to upper layer (TCP/UDP stack)          │
  └─────────────────────────────────────────────────────┘

> IMPORTANT: The ICV comparison in Step 6 MUST use constant-time
> comparison to prevent timing side-channel attacks.
```

---

## 13. Mutable vs Immutable Fields

This is one of the most subtle and important aspects of AH. The problem: if AH authenticates every bit of the packet, and some bits legitimately change in transit (TTL at each router), the receiver's HMAC would never match.

### IPv4 Mutable Fields (Zeroed During HMAC)

```
IPv4 Header:
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |Ver| IHL |████████|          Total Length                      |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |        Identification         |█████|      Fragment Offset   |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |███████|   Protocol   |████████████████████████████████████████|
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |                    Source Address                             |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |                 Destination Address                           |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

 ████ = Mutable (zeroed before HMAC computation)

 Mutable fields:
   - DSCP/ToS byte (may be changed for QoS)
   - Flags (DF=may change, MF, Fragment Offset)
   - TTL (decremented at each hop)
   - Header Checksum (changes because TTL changes)
```

### IPv4 Immutable Fields (Authenticated)

```
Immutable fields (included in HMAC computation):
  - Version (4 for IPv4)
  - IHL (Internet Header Length)
  - Total Length
  - Identification (stays same; fragmentation is separate issue)
  - Protocol (51 for AH)
  - Source IP Address
  - Destination IP Address
```

### IPv6 Mutable Fields

```
IPv6 Base Header:
  Version (4 bits)    → Immutable
  Traffic Class (8b)  → MUTABLE (zero it)
  Flow Label (20b)    → MUTABLE (zero it, may change at routers)
  Payload Length (16b)→ Immutable
  Next Header (8b)    → Immutable
  Hop Limit (8b)      → MUTABLE (like TTL, zero it)
  Source Address      → Immutable
  Destination Address → Immutable (unless routing header changes it)
```

### The Routing Header Special Case

In IPv6, if there's a Type 0 Routing Header, the **final destination** is the ultimate destination. AH must authenticate using the **final destination**, not the intermediate ones.

---

## 14. AH vs ESP — The Critical Difference

```
                AH                          ESP
         (Auth Header)            (Encapsulating Security Payload)
         Protocol: 51                  Protocol: 50
         RFC 4302                      RFC 4303

┌─────────────────────────────────────────────────────────────┐
│ SECURITY SERVICES:                                          │
│                                                             │
│ Confidentiality (encryption)  ✗ NO         ✓ YES           │
│ Data Origin Authentication    ✓ YES        ✓ YES           │
│ Connectionless Integrity      ✓ YES        ✓ YES           │
│ Anti-Replay                   ✓ YES        ✓ YES           │
│ Traffic Flow Confidentiality  ✗ NO (partial)✓ YES (tunnel) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WHAT IS AUTHENTICATED:                                      │
│                                                             │
│ AH: Outer IP header + AH header + Payload                  │
│     (MORE of the packet is authenticated, including IP hdr) │
│                                                             │
│ ESP: Only the payload (inner data), NOT the outer IP header │
│      (IP header can be modified without detection!)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PACKET STRUCTURE:                                           │
│                                                             │
│ AH:                                                         │
│   [IP Hdr][AH Hdr][TCP/UDP Data]                           │
│    ^auth^   ^auth^  ^auth^                                  │
│                                                             │
│ ESP:                                                        │
│   [IP Hdr][ESP Hdr][Encrypted: TCP/UDP Data][ESP Trailer]  │
│    NOT auth  ^auth^ ^protected^               ^auth^        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PRACTICAL CHOICE:                                           │
│                                                             │
│ Use AH when: You need to authenticate IP header too,        │
│              no encryption needed (rare scenario).          │
│                                                             │
│ Use ESP when: You need encryption (most real-world cases).  │
│              ESP with authentication is generally preferred. │
│                                                             │
│ Use AH+ESP: Both can be combined for maximum protection.   │
│             Uncommon. Adds overhead.                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 15. AH and NAT — A Fatal Incompatibility

### What is NAT?

**NAT (Network Address Translation)** is a mechanism where a router **modifies the IP addresses** (and sometimes ports) in packets as they traverse it. It allows multiple devices to share a single public IP address.

```
Home Network:
  192.168.1.10 ──┐
  192.168.1.11 ──┤── NAT Router (public IP: 203.0.113.5) ── Internet
  192.168.1.12 ──┘

  When 192.168.1.10 sends to 8.8.8.8:
    Source becomes 203.0.113.5 (NAT modifies the IP header!)
```

### Why AH and NAT Cannot Coexist

```
AH authenticates the SOURCE IP ADDRESS.

When NAT rewrites the source IP:
  Original: Src=192.168.1.10 → AH computed over this IP
  After NAT: Src=203.0.113.5 → IP address has CHANGED

At the receiver:
  Receives packet with Src=203.0.113.5
  Recomputes HMAC using 203.0.113.5
  But original HMAC was computed with 192.168.1.10
  Result: HMAC mismatch → PACKET DROPPED!

AH is fundamentally incompatible with NAT.
```

### The Solution: ESP with NAT-T

**NAT-Traversal (NAT-T)** is defined in RFC 3948. It solves this by encapsulating ESP packets inside **UDP** (port 4500), which NAT can handle. But:

- **AH has no NAT-T solution** — the IP address is authenticated, period.
- **ESP** (not AH) is what modern VPNs use, often with NAT-T.

This is the primary reason **AH is rarely used in practice today** for internet-facing connections.

---

## 16. IKE — Key Management for AH

### The Bootstrap Problem

For AH to work, both parties need the **same authentication key**. But how do you securely exchange a key over an insecure network?

This is the **key distribution problem**, and **IKE (Internet Key Exchange)** solves it.

### IKEv2 Overview (RFC 7296)

IKE uses **Diffie-Hellman (DH) key exchange** — a mathematical method to agree on a shared secret without ever transmitting the secret.

```
DIFFIE-HELLMAN KEY EXCHANGE (Simplified):

  Public params: prime p, generator g (known to everyone)

  Alice:
    chooses secret a
    computes A = g^a mod p
    sends A to Bob

  Bob:
    chooses secret b
    computes B = g^b mod p
    sends B to Alice

  Alice computes: shared_secret = B^a mod p = g^(ab) mod p
  Bob computes:   shared_secret = A^b mod p = g^(ab) mod p

  Both arrive at same secret!
  Attacker sees: p, g, A, B — cannot compute g^(ab) efficiently
  (This is the Discrete Logarithm Problem)
```

### IKEv2 Phases for AH SA Establishment

```
PHASE 1 — IKE_SA_INIT (Establish IKE SA):

  Initiator                                   Responder
      │                                            │
      │ ── IKE_SA_INIT Request ───────────────────►│
      │    [DH Key Share, Nonce, Supported Algorithms]
      │                                            │
      │ ◄─ IKE_SA_INIT Response ──────────────────│
      │    [DH Key Share, Nonce, Chosen Algorithm] │
      │                                            │
      Both now compute: shared secret → IKE keys

PHASE 2 — IKE_AUTH (Authenticate and Create Child SA):

      │ ── IKE_AUTH Request ──────────────────────►│
      │    [Identity, Auth Payload, SA Proposals,  │
      │     Traffic Selectors]                     │
      │                                            │
      │ ◄─ IKE_AUTH Response ─────────────────────│
      │    [Identity, Auth Payload, SA Selection,  │
      │     Traffic Selectors]                     │
      │                                            │
      AH SA is now established!
      Both sides have:
        - Authentication key
        - SPI values
        - Sequence counters (both start at 0)
```

---

## 17. AH in IPv4 vs IPv6

### IPv4 Differences

- AH header inserted after IPv4 header (and after any options).
- Protocol field in IPv4 header changes to 51.
- IPv4 header checksum must be recalculated after adding AH.
- IPv4 does not guarantee no fragmentation — fragments must be reassembled before AH verification.

### IPv6 Differences

- AH is an **Extension Header** in IPv6 — it fits naturally into IPv6's extension header chain.
- AH is placed after all "hop-by-hop" extension headers but before destination extension headers.
- No separate checksum issue (IPv6 doesn't have a header checksum).
- Next Header field chain:

```
IPv6 Header Chain with AH:

  [IPv6 Base Header]──►[Hop-by-Hop Options]──►[AH Header]──►[TCP/UDP]
        │                      │                    │             │
  Next Hdr=0              Next Hdr=51          Next Hdr=6    (payload)

  Without extension headers:
  [IPv6 Base Header]──►[AH Header]──►[TCP/UDP]
        │                   │
  Next Hdr=51          Next Hdr=6
```

### RFC 4302 IPv6 AH Extension Header

```
IPv6 AH as Extension Header:

  ┌───────────────┬───────────────┬───────────────────────────────┐
  │ Next Header   │ Payload Len   │           RESERVED             │
  ├───────────────┴───────────────┴───────────────────────────────┤
  │                         SPI (32 bits)                         │
  ├───────────────────────────────────────────────────────────────┤
  │                  Sequence Number (32 bits)                    │
  ├───────────────────────────────────────────────────────────────┤
  │                    ICV (variable length)                      │
  └───────────────────────────────────────────────────────────────┘

  In IPv6, AH uses 64-bit alignment (not 32-bit as in IPv4).
```

---

## 18. Real RFC 4302 Packet Diagrams (ASCII)

### Complete IPv4 AH Transport Mode Packet (with HMAC-SHA256-128)

```
COMPLETE PACKET LAYOUT (bytes from left to right, top to bottom):

Offset  Size    Field
──────  ──────  ──────────────────────────────────────────────────
 [IPv4 Header - 20 bytes]
 0       1      Version=4, IHL=5
 1       1      DSCP/ToS   [ZEROED in HMAC computation]
 2       2      Total Length
 4       2      Identification
 6       2      Flags + Fragment Offset  [Flags zeroed in HMAC]
 8       1      TTL        [ZEROED in HMAC computation]
 9       1      Protocol = 51  (AH)
10       2      Header Checksum  [ZEROED in HMAC computation]
12       4      Source IP Address
16       4      Destination IP Address

 [AH Header - 12 bytes fixed + 16 bytes ICV = 28 bytes total]
20       1      Next Header = 6  (TCP)
21       1      Payload Length = (28/4) - 2 = 5
22       2      Reserved = 0x0000  [Must be zero, included in HMAC]
24       4      SPI = 0x00001234  (example)
28       4      Sequence Number = 0x00000001  (first packet)
32      16      ICV (HMAC-SHA256-128 output = 128 bits)
                [Set to 0 during computation, filled after]

 [TCP Segment - variable]
48       2      TCP Source Port
50       2      TCP Destination Port
52       4      Sequence Number (TCP)
56       4      Acknowledgment Number
60       2      Data Offset + Flags
62       2      Window Size
64       2      TCP Checksum
66       2      Urgent Pointer
68+      N      Application Data

Total packet = 20 (IPv4) + 28 (AH) + TCP = 48 + TCP bytes
```

### Complete IPv4 AH Tunnel Mode Packet Diagram

```
TUNNEL MODE — Two full IP headers stacked:

Byte 0                                              Byte 63+
┌─────────────────────────────────────────────────────────────────┐
│                    OUTER IPv4 Header (20 bytes)                 │
│  [4][5][ToS*][   TotalLen  ][   Ident  ][Flags*][ FragOff*]    │
│  [    TTL*   ][Protocol=51 ][  HdrCsum* ][  SrcIP (Gateway1)  ]│
│  [                   DstIP (Gateway2)                         ] │
├─────────────────────────────────────────────────────────────────┤
│                      AH Header (28 bytes)                       │
│  [NextHdr=4 ][PayLen=5][     Reserved=0x0000                  ] │
│  [                      SPI = 0x00005678                      ] │
│  [                   Sequence Number = 42                     ] │
│  [                                                            ] │
│  [              ICV (16 bytes - HMAC-SHA256-128)              ] │
│  [                                                            ] │
├─────────────────────────────────────────────────────────────────┤
│                    INNER IPv4 Header (20 bytes)                 │
│  [4][5][ToS ][   TotalLen  ][   Ident  ][ Flags ][ FragOff  ] │
│  [    TTL   ][Protocol=6   ][  HdrCsum  ][ SrcIP (Host A)   ] │
│  [                    DstIP (Host B)                         ] │
├─────────────────────────────────────────────────────────────────┤
│                     TCP Header + Data                           │
│  [SrcPort][DstPort][  SeqNum  ][  AckNum  ][Offset+Flags]      │
│  [Window][Checksum][UrgPtr][                Data...           ] │
└─────────────────────────────────────────────────────────────────┘

* = Mutable fields (zeroed during HMAC computation)

ICV covers:
  - Outer IP header (mutable fields zeroed)
  - AH header (ICV field zeroed)
  - Inner IP header (fully authenticated - mutable fields NOT zeroed here)
  - TCP header + Data (fully authenticated)
```

### Sequence Number Rollover Prevention

```
Sequence Number Space:

  0x00000000  0x00000001                    0xFFFFFFFF
  ─────────────────────────────────────────────────────
  │ RESERVED │ First packet │ ... │ Last packet │ STOP │
                                                   ^
                              SA must be renegotiated before reaching this
                              (IKE should create new SA around 0xC0000000)
```

---

## 19. C Implementation — Full Working Code

```c
/*
 * AH Protocol Implementation in C
 * RFC 4302 — Authentication Header
 *
 * This implements:
 *   - AH header structure
 *   - HMAC-SHA256 computation (manual implementation for learning)
 *   - Outbound packet processing
 *   - Inbound packet processing
 *   - Anti-replay window
 *   - Constant-time ICV comparison
 *
 * Compile: gcc -O2 -Wall -o ah_demo ah_protocol.c -lcrypto
 *          (requires OpenSSL for HMAC, or use our manual HMAC below)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <arpa/inet.h>    /* htonl, ntohl, htons */

/* ─────────────────────────────────────────────────────────────────
   SECTION 1: CONSTANTS AND CONFIGURATION
   ───────────────────────────────────────────────────────────────── */

#define AH_PROTOCOL_NUMBER    51
#define AH_ICV_SIZE_SHA256    16   /* 128-bit ICV for HMAC-SHA256-128 */
#define AH_ICV_SIZE_SHA1      12   /* 96-bit ICV for HMAC-SHA1-96     */
#define AH_FIXED_HEADER_SIZE  12   /* Next Header + PayLen + Reserved + SPI + SeqNum */
#define ANTI_REPLAY_WINDOW    64   /* Standard 64-packet window */

/* SHA-256 constants */
#define SHA256_BLOCK_SIZE     64
#define SHA256_DIGEST_SIZE    32

/* ─────────────────────────────────────────────────────────────────
   SECTION 2: DATA STRUCTURES
   ───────────────────────────────────────────────────────────────── */

/*
 * AH Header (RFC 4302)
 * All fields in network byte order (big-endian)
 */
typedef struct __attribute__((packed)) {
    uint8_t  next_header;    /* Protocol of data following AH (e.g., TCP=6) */
    uint8_t  payload_len;    /* AH length in 4-byte words, minus 2           */
    uint16_t reserved;       /* Must be zero                                 */
    uint32_t spi;            /* Security Parameters Index                    */
    uint32_t seq_number;     /* Monotonically increasing sequence number     */
    uint8_t  icv[AH_ICV_SIZE_SHA256]; /* Integrity Check Value (HMAC output)*/
} ah_header_t;

/*
 * Minimal IPv4 Header structure
 * Used to demonstrate mutable field handling
 */
typedef struct __attribute__((packed)) {
    uint8_t  version_ihl;    /* Version (4 bits) + IHL (4 bits)              */
    uint8_t  dscp_ecn;       /* DSCP + ECN (MUTABLE — zeroed for HMAC)       */
    uint16_t total_length;   /* Total packet length                          */
    uint16_t identification; /* For fragmentation                            */
    uint16_t flags_frag;     /* Flags (partially mutable) + Fragment offset  */
    uint8_t  ttl;            /* Time To Live (MUTABLE — zeroed for HMAC)     */
    uint8_t  protocol;       /* Protocol (will be 51 for AH)                 */
    uint16_t checksum;       /* Header checksum (MUTABLE — zeroed for HMAC)  */
    uint32_t src_addr;       /* Source IP address (immutable)                */
    uint32_t dst_addr;       /* Destination IP address (immutable)           */
} ipv4_header_t;

/*
 * Security Association (SA)
 * Represents one direction of an IPsec connection
 */
typedef struct {
    uint32_t spi;                          /* Security Parameters Index         */
    uint32_t dst_addr;                     /* Destination IP                    */
    uint8_t  auth_key[64];                 /* Authentication key (up to 512-bit)*/
    size_t   auth_key_len;                 /* Key length in bytes               */
    uint32_t seq_counter;                  /* Outbound: last seq sent           */
    uint32_t replay_window_right;          /* Inbound: highest seq received     */
    uint64_t replay_bitmap;               /* Inbound: 64-bit sliding window     */
    bool     anti_replay_enabled;          /* Whether to check anti-replay      */
} security_association_t;

/* ─────────────────────────────────────────────────────────────────
   SECTION 3: SHA-256 IMPLEMENTATION
   (Manual implementation to understand the internals)
   ───────────────────────────────────────────────────────────────── */

typedef struct {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t  buffer[SHA256_BLOCK_SIZE];
    size_t   buffer_len;
} sha256_ctx_t;

/* SHA-256 constants (first 32 bits of fractional parts of cube roots of primes) */
static const uint32_t K256[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};

#define ROTR32(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(e,f,g)    (((e) & (f)) ^ (~(e) & (g)))
#define MAJ(a,b,c)   (((a) & (b)) ^ ((a) & (c)) ^ ((b) & (c)))
#define EP0(a)       (ROTR32(a,2)  ^ ROTR32(a,13) ^ ROTR32(a,22))
#define EP1(e)       (ROTR32(e,6)  ^ ROTR32(e,11) ^ ROTR32(e,25))
#define SIG0(x)      (ROTR32(x,7)  ^ ROTR32(x,18) ^ ((x) >> 3))
#define SIG1(x)      (ROTR32(x,17) ^ ROTR32(x,19) ^ ((x) >> 10))

static void sha256_init(sha256_ctx_t *ctx) {
    /* Initial hash values: first 32 bits of fractional parts of square roots */
    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
    ctx->bit_count  = 0;
    ctx->buffer_len = 0;
}

static void sha256_process_block(sha256_ctx_t *ctx, const uint8_t *block) {
    uint32_t w[64];
    uint32_t a, b, c, d, e, f, g, h;
    uint32_t t1, t2;

    /* Prepare message schedule */
    for (int i = 0; i < 16; i++) {
        w[i] = ((uint32_t)block[i*4]     << 24) |
               ((uint32_t)block[i*4 + 1] << 16) |
               ((uint32_t)block[i*4 + 2] <<  8) |
               ((uint32_t)block[i*4 + 3]);
    }
    for (int i = 16; i < 64; i++) {
        w[i] = SIG1(w[i-2]) + w[i-7] + SIG0(w[i-15]) + w[i-16];
    }

    /* Initialize working variables */
    a = ctx->state[0]; b = ctx->state[1];
    c = ctx->state[2]; d = ctx->state[3];
    e = ctx->state[4]; f = ctx->state[5];
    g = ctx->state[6]; h = ctx->state[7];

    /* 64 rounds of compression */
    for (int i = 0; i < 64; i++) {
        t1 = h + EP1(e) + CH(e,f,g) + K256[i] + w[i];
        t2 = EP0(a) + MAJ(a,b,c);
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }

    /* Add compressed chunk to current hash */
    ctx->state[0] += a; ctx->state[1] += b;
    ctx->state[2] += c; ctx->state[3] += d;
    ctx->state[4] += e; ctx->state[5] += f;
    ctx->state[6] += g; ctx->state[7] += h;
}

static void sha256_update(sha256_ctx_t *ctx, const uint8_t *data, size_t len) {
    ctx->bit_count += (uint64_t)len * 8;
    while (len > 0) {
        size_t space = SHA256_BLOCK_SIZE - ctx->buffer_len;
        size_t copy  = (len < space) ? len : space;
        memcpy(ctx->buffer + ctx->buffer_len, data, copy);
        ctx->buffer_len += copy;
        data += copy;
        len  -= copy;
        if (ctx->buffer_len == SHA256_BLOCK_SIZE) {
            sha256_process_block(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

static void sha256_final(sha256_ctx_t *ctx, uint8_t digest[SHA256_DIGEST_SIZE]) {
    /* Padding: append 0x80, then zeros, then 64-bit bit count */
    uint8_t pad[SHA256_BLOCK_SIZE] = {0};
    uint64_t bit_count = ctx->bit_count;
    pad[0] = 0x80;

    size_t pad_len = (ctx->buffer_len < 56)
                   ? (56 - ctx->buffer_len)
                   : (SHA256_BLOCK_SIZE + 56 - ctx->buffer_len);

    sha256_update(ctx, pad, pad_len);

    uint8_t length_bytes[8];
    for (int i = 7; i >= 0; i--) {
        length_bytes[i] = bit_count & 0xFF;
        bit_count >>= 8;
    }
    sha256_update(ctx, length_bytes, 8);

    /* Output final hash */
    for (int i = 0; i < 8; i++) {
        digest[i*4]     = (ctx->state[i] >> 24) & 0xFF;
        digest[i*4 + 1] = (ctx->state[i] >> 16) & 0xFF;
        digest[i*4 + 2] = (ctx->state[i] >>  8) & 0xFF;
        digest[i*4 + 3] = (ctx->state[i]      ) & 0xFF;
    }
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 4: HMAC-SHA256 IMPLEMENTATION
   ───────────────────────────────────────────────────────────────── */

/*
 * hmac_sha256 — Compute HMAC-SHA256
 *
 * HMAC(K, m) = H((K' XOR opad) || H((K' XOR ipad) || m))
 *
 * @key      : Secret authentication key
 * @key_len  : Key length in bytes
 * @data     : Data to authenticate
 * @data_len : Data length in bytes
 * @output   : Output buffer (must be SHA256_DIGEST_SIZE = 32 bytes)
 */
void hmac_sha256(
    const uint8_t *key, size_t key_len,
    const uint8_t *data, size_t data_len,
    uint8_t output[SHA256_DIGEST_SIZE])
{
    uint8_t k_prime[SHA256_BLOCK_SIZE] = {0};  /* Key padded to block size */
    uint8_t ipad[SHA256_BLOCK_SIZE];
    uint8_t opad[SHA256_BLOCK_SIZE];
    sha256_ctx_t ctx;
    uint8_t inner_hash[SHA256_DIGEST_SIZE];

    /* Step 1: Derive K' */
    if (key_len > SHA256_BLOCK_SIZE) {
        /* If key is too long, hash it */
        sha256_init(&ctx);
        sha256_update(&ctx, key, key_len);
        sha256_final(&ctx, k_prime);
    } else {
        memcpy(k_prime, key, key_len);
        /* Rest is already zero from initialization */
    }

    /* Step 2: Compute ipad and opad */
    for (int i = 0; i < SHA256_BLOCK_SIZE; i++) {
        ipad[i] = k_prime[i] ^ 0x36;  /* XOR with ipad byte */
        opad[i] = k_prime[i] ^ 0x5C;  /* XOR with opad byte */
    }

    /* Step 3: Inner hash = H(K' XOR ipad || message) */
    sha256_init(&ctx);
    sha256_update(&ctx, ipad, SHA256_BLOCK_SIZE);
    sha256_update(&ctx, data, data_len);
    sha256_final(&ctx, inner_hash);

    /* Step 4: Outer hash = H(K' XOR opad || inner_hash) */
    sha256_init(&ctx);
    sha256_update(&ctx, opad, SHA256_BLOCK_SIZE);
    sha256_update(&ctx, inner_hash, SHA256_DIGEST_SIZE);
    sha256_final(&ctx, output);
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 5: ANTI-REPLAY WINDOW
   ───────────────────────────────────────────────────────────────── */

typedef enum {
    REPLAY_OK       = 0,  /* Packet is valid, update window             */
    REPLAY_DUPLICATE = 1,  /* Already received this sequence number       */
    REPLAY_TOO_OLD   = 2,  /* Outside window (too old to accept)          */
} replay_status_t;

/*
 * anti_replay_check — Check if a sequence number is valid
 *
 * Returns REPLAY_OK if packet should proceed to ICV verification.
 * IMPORTANT: Update the window only AFTER ICV verification succeeds.
 *
 * Window layout:
 *   [N-63][N-62]...[N-1][N]
 *   bit 63      bit 1  bit 0
 */
replay_status_t anti_replay_check(security_association_t *sa, uint32_t seq)
{
    uint32_t N = sa->replay_window_right;  /* Right edge (highest received) */

    if (seq == 0) {
        /*
         * Sequence number 0 is never valid.
         * Sequence numbers start at 1 per RFC 4302.
         */
        return REPLAY_DUPLICATE;
    }

    if (seq > N) {
        /* Packet is ahead of window — it's a candidate (not yet received) */
        return REPLAY_OK;
    }

    if (N - seq >= ANTI_REPLAY_WINDOW) {
        /* Packet is too old — outside the left edge of the window */
        return REPLAY_TOO_OLD;
    }

    /* Packet is within the window — check if already received */
    uint32_t bit_pos = N - seq;  /* 0 = right edge, 63 = left edge */
    if (sa->replay_bitmap & ((uint64_t)1 << bit_pos)) {
        return REPLAY_DUPLICATE;
    }

    return REPLAY_OK;
}

/*
 * anti_replay_update — Update the window after successful ICV verification
 * Call this ONLY after HMAC verification passes.
 */
void anti_replay_update(security_association_t *sa, uint32_t seq)
{
    uint32_t N = sa->replay_window_right;

    if (seq > N) {
        /*
         * Advance the window right edge.
         * Shift bitmap left by (seq - N) positions.
         * New right edge bit gets set to 1 (received).
         */
        uint32_t advance = seq - N;
        if (advance >= ANTI_REPLAY_WINDOW) {
            sa->replay_bitmap = 0;  /* Window jumped entirely */
        } else {
            sa->replay_bitmap <<= advance;
        }
        sa->replay_bitmap |= 1;  /* Mark current packet (bit 0) as received */
        sa->replay_window_right = seq;
    } else {
        /* Packet within window — set its bit */
        uint32_t bit_pos = N - seq;
        sa->replay_bitmap |= ((uint64_t)1 << bit_pos);
    }
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 6: CONSTANT-TIME COMPARISON
   ───────────────────────────────────────────────────────────────── */

/*
 * icv_compare_ct — Constant-time byte comparison
 *
 * WHY CONSTANT-TIME?
 * A naive memcmp() returns early on the first mismatch.
 * An attacker measuring response time can determine HOW MANY bytes
 * match, enabling byte-by-byte brute force. Constant-time comparison
 * always takes the same time regardless of where mismatch occurs.
 *
 * Returns: 0 if equal, non-zero if different
 */
int icv_compare_ct(const uint8_t *a, const uint8_t *b, size_t len)
{
    uint8_t result = 0;
    for (size_t i = 0; i < len; i++) {
        result |= a[i] ^ b[i];  /* OR accumulates any difference */
    }
    return (int)result;  /* 0 = equal, non-zero = different */
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 7: OUTBOUND PACKET PROCESSING
   ───────────────────────────────────────────────────────────────── */

/*
 * ah_outbound_process — Apply AH protection to an outgoing packet
 *
 * This function:
 *   1. Inserts AH header into the packet buffer
 *   2. Computes HMAC over the (mutable-zeroed) packet
 *   3. Fills in the ICV
 *
 * @sa       : Security Association to use
 * @packet   : Buffer containing the original IP packet
 * @pkt_len  : Length of the original packet
 * @out_buf  : Output buffer (must be large enough: pkt_len + AH header size)
 * @out_len  : Will be set to the output packet length
 *
 * Returns: 0 on success, -1 on error
 */
int ah_outbound_process(
    security_association_t *sa,
    const uint8_t *packet, size_t pkt_len,
    uint8_t *out_buf, size_t *out_len)
{
    if (!sa || !packet || !out_buf || !out_len) return -1;
    if (pkt_len < sizeof(ipv4_header_t)) return -1;

    /* Check sequence number overflow */
    if (sa->seq_counter == UINT32_MAX) {
        fprintf(stderr, "[AH] ERROR: Sequence number overflow — SA must be renegotiated!\n");
        return -1;
    }

    /* Sizes */
    size_t ah_total_size = AH_FIXED_HEADER_SIZE + AH_ICV_SIZE_SHA256;
    *out_len = pkt_len + ah_total_size;

    /* ── Step 1: Copy and modify IP header ── */
    memcpy(out_buf, packet, sizeof(ipv4_header_t));
    ipv4_header_t *ip = (ipv4_header_t *)out_buf;

    /* Save the original protocol, then set to AH */
    uint8_t original_proto = ip->protocol;
    ip->protocol = AH_PROTOCOL_NUMBER;

    /* Update total length */
    ip->total_length = htons((uint16_t)*out_len);

    /* ── Step 2: Insert AH header ── */
    ah_header_t *ah = (ah_header_t *)(out_buf + sizeof(ipv4_header_t));

    sa->seq_counter++;  /* Increment before use */

    ah->next_header = original_proto;
    ah->payload_len = (uint8_t)((ah_total_size / 4) - 2);
    ah->reserved    = 0;
    ah->spi         = htonl(sa->spi);
    ah->seq_number  = htonl(sa->seq_counter);
    memset(ah->icv, 0, AH_ICV_SIZE_SHA256);  /* ICV = 0 for computation */

    /* ── Step 3: Copy original payload after AH header ── */
    memcpy(out_buf + sizeof(ipv4_header_t) + ah_total_size,
           packet  + sizeof(ipv4_header_t),
           pkt_len - sizeof(ipv4_header_t));

    /* ── Step 4: Zero mutable fields for HMAC computation ── */
    /* Create a copy for HMAC (we need to zero mutable fields) */
    uint8_t *hmac_buf = (uint8_t *)malloc(*out_len);
    if (!hmac_buf) return -1;
    memcpy(hmac_buf, out_buf, *out_len);

    ipv4_header_t *hmac_ip = (ipv4_header_t *)hmac_buf;
    hmac_ip->dscp_ecn   = 0;   /* MUTABLE: zero ToS/DSCP */
    hmac_ip->flags_frag = htons(ntohs(hmac_ip->flags_frag) & 0x4000);
                                /* Keep DF bit, zero MF and fragment offset */
    hmac_ip->ttl        = 0;   /* MUTABLE: zero TTL */
    hmac_ip->checksum   = 0;   /* MUTABLE: zero checksum */

    /* ICV field is already zero in hmac_buf (we set it above) */

    /* ── Step 5: Compute HMAC-SHA256 over zeroed packet ── */
    uint8_t full_hmac[SHA256_DIGEST_SIZE];
    hmac_sha256(sa->auth_key, sa->auth_key_len,
                hmac_buf, *out_len,
                full_hmac);

    free(hmac_buf);

    /* Truncate to ICV_SIZE (use first 128 bits for HMAC-SHA256-128) */
    memcpy(ah->icv, full_hmac, AH_ICV_SIZE_SHA256);

    /* ── Step 6: Recompute IP checksum ── */
    /* Simple IP header checksum computation */
    ip->checksum = 0;
    uint32_t sum = 0;
    uint16_t *words = (uint16_t *)out_buf;
    for (size_t i = 0; i < sizeof(ipv4_header_t) / 2; i++) {
        sum += ntohs(words[i]);
    }
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    ip->checksum = htons((uint16_t)~sum);

    printf("[AH OUTBOUND] Packet protected:\n");
    printf("  SPI:      0x%08X\n", sa->spi);
    printf("  Seq Num:  %u\n", sa->seq_counter);
    printf("  ICV:      ");
    for (int i = 0; i < AH_ICV_SIZE_SHA256; i++) printf("%02X", ah->icv[i]);
    printf("\n  Out size: %zu bytes\n", *out_len);

    return 0;
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 8: INBOUND PACKET PROCESSING
   ───────────────────────────────────────────────────────────────── */

/*
 * ah_inbound_process — Verify and strip AH from an incoming packet
 *
 * Returns: 0 on success (packet is authentic), -1 on failure
 */
int ah_inbound_process(
    security_association_t *sa,
    const uint8_t *packet, size_t pkt_len,
    uint8_t *out_buf, size_t *out_len)
{
    if (!sa || !packet || !out_buf || !out_len) return -1;
    if (pkt_len < sizeof(ipv4_header_t) + AH_FIXED_HEADER_SIZE + AH_ICV_SIZE_SHA256)
        return -1;

    const ipv4_header_t *ip = (const ipv4_header_t *)packet;
    if (ip->protocol != AH_PROTOCOL_NUMBER) {
        fprintf(stderr, "[AH] Not an AH packet (proto=%d)\n", ip->protocol);
        return -1;
    }

    const ah_header_t *ah = (const ah_header_t *)(packet + sizeof(ipv4_header_t));

    /* ── Step 1: Look up SA by SPI ── */
    uint32_t recv_spi = ntohl(ah->spi);
    if (recv_spi != sa->spi) {
        fprintf(stderr, "[AH] SPI mismatch: got 0x%X, expected 0x%X\n",
                recv_spi, sa->spi);
        return -1;
    }

    /* ── Step 2: Anti-replay check ── */
    uint32_t seq = ntohl(ah->seq_number);
    if (sa->anti_replay_enabled) {
        replay_status_t rs = anti_replay_check(sa, seq);
        if (rs == REPLAY_TOO_OLD) {
            fprintf(stderr, "[AH] DROPPED: Packet too old (seq=%u, window right=%u)\n",
                    seq, sa->replay_window_right);
            return -1;
        }
        if (rs == REPLAY_DUPLICATE) {
            fprintf(stderr, "[AH] DROPPED: Duplicate packet (seq=%u)\n", seq);
            return -1;
        }
    }

    /* ── Step 3: Prepare packet for HMAC computation ── */
    uint8_t *hmac_buf = (uint8_t *)malloc(pkt_len);
    if (!hmac_buf) return -1;
    memcpy(hmac_buf, packet, pkt_len);

    /* Zero mutable IP fields */
    ipv4_header_t *hmac_ip = (ipv4_header_t *)hmac_buf;
    hmac_ip->dscp_ecn   = 0;
    hmac_ip->flags_frag = htons(ntohs(hmac_ip->flags_frag) & 0x4000);
    hmac_ip->ttl        = 0;
    hmac_ip->checksum   = 0;

    /* Zero ICV field in the working copy */
    ah_header_t *hmac_ah = (ah_header_t *)(hmac_buf + sizeof(ipv4_header_t));
    memset(hmac_ah->icv, 0, AH_ICV_SIZE_SHA256);

    /* ── Step 4: Recompute HMAC ── */
    uint8_t computed_hmac[SHA256_DIGEST_SIZE];
    hmac_sha256(sa->auth_key, sa->auth_key_len,
                hmac_buf, pkt_len,
                computed_hmac);

    free(hmac_buf);

    /* ── Step 5: Constant-time ICV comparison ── */
    if (icv_compare_ct(ah->icv, computed_hmac, AH_ICV_SIZE_SHA256) != 0) {
        fprintf(stderr, "[AH] ICV MISMATCH — packet tampered or wrong key!\n");
        fprintf(stderr, "  Received ICV:  ");
        for (int i = 0; i < AH_ICV_SIZE_SHA256; i++) printf("%02X", ah->icv[i]);
        fprintf(stderr, "\n  Computed ICV:  ");
        for (int i = 0; i < AH_ICV_SIZE_SHA256; i++) printf("%02X", computed_hmac[i]);
        fprintf(stderr, "\n");
        return -1;
    }

    /* ── Step 6: Update anti-replay window ── */
    if (sa->anti_replay_enabled) {
        anti_replay_update(sa, seq);
    }

    /* ── Step 7: Strip AH header — reconstruct original packet ── */
    size_t ah_total = AH_FIXED_HEADER_SIZE + AH_ICV_SIZE_SHA256;
    *out_len = pkt_len - ah_total;

    memcpy(out_buf, packet, sizeof(ipv4_header_t));

    ipv4_header_t *out_ip = (ipv4_header_t *)out_buf;
    out_ip->protocol     = ah->next_header;  /* Restore original protocol */
    out_ip->total_length = htons((uint16_t)*out_len);

    memcpy(out_buf + sizeof(ipv4_header_t),
           packet  + sizeof(ipv4_header_t) + ah_total,
           *out_len - sizeof(ipv4_header_t));

    /* Recompute checksum */
    out_ip->checksum = 0;
    uint32_t sum = 0;
    uint16_t *words = (uint16_t *)out_buf;
    for (size_t i = 0; i < sizeof(ipv4_header_t) / 2; i++) {
        sum += ntohs(words[i]);
    }
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    out_ip->checksum = htons((uint16_t)~sum);

    printf("[AH INBOUND] Packet verified and accepted:\n");
    printf("  SPI:      0x%08X\n", recv_spi);
    printf("  Seq Num:  %u\n", seq);
    printf("  ICV:      VALID\n");
    printf("  Out size: %zu bytes\n", *out_len);

    return 0;
}

/* ─────────────────────────────────────────────────────────────────
   SECTION 9: DEMONSTRATION MAIN
   ───────────────────────────────────────────────────────────────── */

int main(void)
{
    printf("═══════════════════════════════════════════════════════\n");
    printf("   AH Protocol (RFC 4302) — C Implementation Demo\n");
    printf("═══════════════════════════════════════════════════════\n\n");

    /* ── Initialize Security Association ── */
    security_association_t sa;
    memset(&sa, 0, sizeof(sa));

    sa.spi         = 0x00001234;
    sa.seq_counter = 0;
    sa.anti_replay_enabled = true;
    sa.replay_window_right = 0;
    sa.replay_bitmap       = 0;

    /* 256-bit authentication key (in practice, from IKE) */
    const char *key_str = "MySuperSecretKey1MySuperSecretKey1";
    sa.auth_key_len = 32;
    memcpy(sa.auth_key, key_str, sa.auth_key_len);

    printf("Security Association Initialized:\n");
    printf("  SPI:       0x%08X\n", sa.spi);
    printf("  Key length: %zu bytes (%zu bits)\n\n",
           sa.auth_key_len, sa.auth_key_len * 8);

    /* ── Build a fake IPv4+TCP packet ── */
    #define PAYLOAD_SIZE 20  /* Simulated TCP header + tiny data */

    size_t orig_len = sizeof(ipv4_header_t) + PAYLOAD_SIZE;
    uint8_t original_packet[sizeof(ipv4_header_t) + PAYLOAD_SIZE];
    memset(original_packet, 0, sizeof(original_packet));

    ipv4_header_t *ip = (ipv4_header_t *)original_packet;
    ip->version_ihl  = 0x45;  /* Version=4, IHL=5 (20 bytes) */
    ip->dscp_ecn     = 0;
    ip->total_length = htons((uint16_t)orig_len);
    ip->identification = htons(0x1234);
    ip->flags_frag   = htons(0x4000);  /* DF=1, MF=0, offset=0 */
    ip->ttl          = 64;
    ip->protocol     = 6;  /* TCP */
    ip->checksum     = 0;
    ip->src_addr     = inet_addr("192.168.1.10");
    ip->dst_addr     = inet_addr("192.168.1.20");

    /* Fake TCP payload */
    uint8_t *payload = original_packet + sizeof(ipv4_header_t);
    memcpy(payload, "Hello, AH Protocol!", 19);
    payload[19] = 0;

    printf("Original Packet:\n");
    printf("  Src IP:   192.168.1.10\n");
    printf("  Dst IP:   192.168.1.20\n");
    printf("  Protocol: TCP (6)\n");
    printf("  Payload:  \"%s\"\n", payload);
    printf("  Size:     %zu bytes\n\n", orig_len);

    /* ── OUTBOUND: Apply AH ── */
    printf("── OUTBOUND PROCESSING ──\n");
    size_t ah_pkt_size = orig_len + AH_FIXED_HEADER_SIZE + AH_ICV_SIZE_SHA256 + 16;
    uint8_t ah_packet[512];
    size_t ah_packet_len = 0;

    if (ah_outbound_process(&sa, original_packet, orig_len,
                            ah_packet, &ah_packet_len) != 0) {
        fprintf(stderr, "Outbound processing failed!\n");
        return 1;
    }
    (void)ah_pkt_size;

    printf("\nAH-Protected Packet (hex dump):\n");
    for (size_t i = 0; i < ah_packet_len; i++) {
        printf("%02X ", ah_packet[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n\n");

    /* ── INBOUND: Verify AH ── */
    printf("── INBOUND PROCESSING ──\n");
    /* Reset SA for receiver side (same key, seq starts at 0) */
    security_association_t sa_recv;
    memcpy(&sa_recv, &sa, sizeof(sa));
    sa_recv.seq_counter        = 0;
    sa_recv.replay_window_right = 0;
    sa_recv.replay_bitmap       = 0;

    uint8_t recovered_packet[512];
    size_t  recovered_len = 0;

    if (ah_inbound_process(&sa_recv, ah_packet, ah_packet_len,
                           recovered_packet, &recovered_len) != 0) {
        fprintf(stderr, "Inbound processing FAILED — packet rejected!\n");
        return 1;
    }

    uint8_t *recv_payload = recovered_packet + sizeof(ipv4_header_t);
    printf("\nRecovered Payload: \"%s\"\n", recv_payload);

    /* ── Test Tamper Detection ── */
    printf("\n── TAMPER DETECTION TEST ──\n");
    uint8_t tampered[512];
    memcpy(tampered, ah_packet, ah_packet_len);
    tampered[ah_packet_len - 5] ^= 0xFF;  /* Flip some bits in payload */

    uint8_t junk[512];
    size_t junk_len = 0;
    int result = ah_inbound_process(&sa_recv, tampered, ah_packet_len,
                                    junk, &junk_len);
    if (result != 0) {
        printf("[AH] Tampered packet correctly REJECTED!\n");
    } else {
        printf("[AH] ERROR: Tampered packet was ACCEPTED (bug!)\n");
    }

    /* ── Test Replay Attack ── */
    printf("\n── REPLAY ATTACK TEST ──\n");
    /* Re-send the same (valid) packet — should be rejected */
    result = ah_inbound_process(&sa_recv, ah_packet, ah_packet_len,
                                junk, &junk_len);
    if (result != 0) {
        printf("[AH] Replayed packet correctly REJECTED!\n");
    } else {
        printf("[AH] ERROR: Replayed packet was ACCEPTED (anti-replay bug!)\n");
    }

    printf("\n═══════════════════════════════════════════════════════\n");
    printf("   All tests completed.\n");
    printf("═══════════════════════════════════════════════════════\n");

    return 0;
}
```

---

## 20. Rust Implementation — Full Working Code

```rust
//! AH Protocol Implementation in Rust
//! RFC 4302 — Authentication Header
//!
//! This demonstrates:
//!   - AH header structure with `#[repr(C, packed)]`
//!   - HMAC-SHA256 (pure Rust, no external crypto crates)
//!   - Outbound packet processing
//!   - Inbound packet processing
//!   - Anti-replay sliding window
//!   - Constant-time ICV comparison
//!
//! Run: cargo run
//!
//! Cargo.toml dependencies: none (pure std)

use std::fmt;

// ─────────────────────────────────────────────────────────────────
// SECTION 1: CONSTANTS
// ─────────────────────────────────────────────────────────────────

const AH_PROTOCOL_NUMBER: u8 = 51;
const AH_ICV_SIZE_SHA256: usize = 16;          // 128-bit ICV
const AH_FIXED_HEADER_SIZE: usize = 12;        // Fixed part of AH header
const ANTI_REPLAY_WINDOW: u32 = 64;
const SHA256_BLOCK_SIZE: usize = 64;
const SHA256_DIGEST_SIZE: usize = 32;

// ─────────────────────────────────────────────────────────────────
// SECTION 2: SHA-256 IMPLEMENTATION
// ─────────────────────────────────────────────────────────────────

/// SHA-256 context holding intermediate state
struct Sha256 {
    state: [u32; 8],
    bit_count: u64,
    buffer: [u8; SHA256_BLOCK_SIZE],
    buffer_len: usize,
}

/// SHA-256 round constants
const K256: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

impl Sha256 {
    fn new() -> Self {
        Self {
            // Initial hash values (fractional parts of sqrt of first 8 primes)
            state: [
                0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
            ],
            bit_count: 0,
            buffer: [0u8; SHA256_BLOCK_SIZE],
            buffer_len: 0,
        }
    }

    fn process_block(&mut self, block: &[u8; SHA256_BLOCK_SIZE]) {
        let mut w = [0u32; 64];

        // Prepare message schedule
        for i in 0..16 {
            w[i] = u32::from_be_bytes([
                block[i*4], block[i*4+1], block[i*4+2], block[i*4+3]
            ]);
        }
        for i in 16..64 {
            let s0 = w[i-15].rotate_right(7) ^ w[i-15].rotate_right(18) ^ (w[i-15] >> 3);
            let s1 = w[i-2].rotate_right(17) ^ w[i-2].rotate_right(19) ^ (w[i-2] >> 10);
            w[i] = w[i-16].wrapping_add(s0).wrapping_add(w[i-7]).wrapping_add(s1);
        }

        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = self.state;

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ (!e & g);
            let temp1 = h.wrapping_add(s1).wrapping_add(ch)
                         .wrapping_add(K256[i]).wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            h = g; g = f; f = e;
            e = d.wrapping_add(temp1);
            d = c; c = b; b = a;
            a = temp1.wrapping_add(temp2);
        }

        self.state[0] = self.state[0].wrapping_add(a);
        self.state[1] = self.state[1].wrapping_add(b);
        self.state[2] = self.state[2].wrapping_add(c);
        self.state[3] = self.state[3].wrapping_add(d);
        self.state[4] = self.state[4].wrapping_add(e);
        self.state[5] = self.state[5].wrapping_add(f);
        self.state[6] = self.state[6].wrapping_add(g);
        self.state[7] = self.state[7].wrapping_add(h);
    }

    fn update(&mut self, data: &[u8]) {
        self.bit_count += (data.len() as u64) * 8;
        let mut offset = 0;
        while offset < data.len() {
            let space = SHA256_BLOCK_SIZE - self.buffer_len;
            let copy  = (data.len() - offset).min(space);
            self.buffer[self.buffer_len..self.buffer_len + copy]
                .copy_from_slice(&data[offset..offset + copy]);
            self.buffer_len += copy;
            offset += copy;
            if self.buffer_len == SHA256_BLOCK_SIZE {
                let block = self.buffer;
                self.process_block(&block);
                self.buffer_len = 0;
            }
        }
    }

    fn finalize(mut self) -> [u8; SHA256_DIGEST_SIZE] {
        // Padding
        let bit_count = self.bit_count;
        let pad_byte = [0x80u8];
        self.update(&pad_byte);

        // Pad with zeros until 56 bytes remain in current block
        while self.buffer_len != 56 {
            self.update(&[0u8]);
        }

        // Append 64-bit big-endian bit count
        self.update(&bit_count.to_be_bytes());

        // Extract digest
        let mut digest = [0u8; SHA256_DIGEST_SIZE];
        for (i, word) in self.state.iter().enumerate() {
            digest[i*4..(i+1)*4].copy_from_slice(&word.to_be_bytes());
        }
        digest
    }
}

// ─────────────────────────────────────────────────────────────────
// SECTION 3: HMAC-SHA256
// ─────────────────────────────────────────────────────────────────

/// Compute HMAC-SHA256
///
/// HMAC(K, m) = H((K' XOR opad) || H((K' XOR ipad) || m))
///
/// Returns the full 32-byte digest. Truncate to ICV_SIZE for AH.
fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; SHA256_DIGEST_SIZE] {
    // Derive K': pad or hash key to block size
    let mut k_prime = [0u8; SHA256_BLOCK_SIZE];
    if key.len() > SHA256_BLOCK_SIZE {
        let h = Sha256::new();
        // If key is too long, hash it
        let mut ctx = Sha256::new();
        ctx.update(key);
        k_prime[..SHA256_DIGEST_SIZE].copy_from_slice(&ctx.finalize());
    } else {
        k_prime[..key.len()].copy_from_slice(key);
    }

    // ipad and opad
    let ipad: Vec<u8> = k_prime.iter().map(|&b| b ^ 0x36).collect();
    let opad: Vec<u8> = k_prime.iter().map(|&b| b ^ 0x5C).collect();

    // Inner hash: H(ipad || message)
    let mut inner_ctx = Sha256::new();
    inner_ctx.update(&ipad);
    inner_ctx.update(message);
    let inner_hash = inner_ctx.finalize();

    // Outer hash: H(opad || inner_hash)
    let mut outer_ctx = Sha256::new();
    outer_ctx.update(&opad);
    outer_ctx.update(&inner_hash);
    outer_ctx.finalize()
}

// ─────────────────────────────────────────────────────────────────
// SECTION 4: ANTI-REPLAY WINDOW
// ─────────────────────────────────────────────────────────────────

#[derive(Debug, PartialEq)]
enum ReplayStatus {
    Ok,
    Duplicate,
    TooOld,
}

/// Anti-replay sliding window state
struct ReplayWindow {
    right_edge: u32,  // Highest sequence number received
    bitmap: u64,      // Bit i=1 means (right_edge - i) was received
}

impl ReplayWindow {
    fn new() -> Self {
        Self { right_edge: 0, bitmap: 0 }
    }

    /// Check if a sequence number should be accepted
    ///
    /// Call this BEFORE ICV verification (don't update window yet).
    fn check(&self, seq: u32) -> ReplayStatus {
        if seq == 0 {
            return ReplayStatus::Duplicate; // Seq 0 is never valid
        }

        if seq > self.right_edge {
            // Ahead of window — valid candidate
            return ReplayStatus::Ok;
        }

        let age = self.right_edge - seq;
        if age >= ANTI_REPLAY_WINDOW {
            // Too old — outside the window
            return ReplayStatus::TooOld;
        }

        // Within window — check bitmap
        if self.bitmap & (1u64 << age) != 0 {
            ReplayStatus::Duplicate
        } else {
            ReplayStatus::Ok
        }
    }

    /// Update window after successful ICV verification
    fn update(&mut self, seq: u32) {
        if seq > self.right_edge {
            let advance = seq - self.right_edge;
            if advance >= ANTI_REPLAY_WINDOW {
                self.bitmap = 0;
            } else {
                self.bitmap <<= advance;
            }
            self.bitmap |= 1; // Mark bit 0 (new right edge) as received
            self.right_edge = seq;
        } else {
            let age = self.right_edge - seq;
            self.bitmap |= 1u64 << age;
        }
    }
}

// ─────────────────────────────────────────────────────────────────
// SECTION 5: AH HEADER
// ─────────────────────────────────────────────────────────────────

/// AH Header as per RFC 4302
///
/// All fields must be stored in network byte order (big-endian).
/// We use explicit `to_be_bytes()` / `from_be_bytes()` for conversion.
#[derive(Debug, Clone)]
struct AhHeader {
    next_header: u8,
    payload_len: u8,
    reserved: u16,
    spi: u32,
    seq_number: u32,
    icv: [u8; AH_ICV_SIZE_SHA256],
}

impl AhHeader {
    fn total_size() -> usize {
        AH_FIXED_HEADER_SIZE + AH_ICV_SIZE_SHA256
    }

    /// Serialize to bytes (network byte order)
    fn to_bytes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(Self::total_size());
        out.push(self.next_header);
        out.push(self.payload_len);
        out.extend_from_slice(&self.reserved.to_be_bytes());
        out.extend_from_slice(&self.spi.to_be_bytes());
        out.extend_from_slice(&self.seq_number.to_be_bytes());
        out.extend_from_slice(&self.icv);
        out
    }

    /// Deserialize from bytes
    fn from_bytes(data: &[u8]) -> Option<Self> {
        if data.len() < Self::total_size() {
            return None;
        }
        let mut icv = [0u8; AH_ICV_SIZE_SHA256];
        icv.copy_from_slice(&data[12..12 + AH_ICV_SIZE_SHA256]);
        Some(Self {
            next_header: data[0],
            payload_len: data[1],
            reserved:    u16::from_be_bytes([data[2], data[3]]),
            spi:         u32::from_be_bytes([data[4], data[5], data[6], data[7]]),
            seq_number:  u32::from_be_bytes([data[8], data[9], data[10], data[11]]),
            icv,
        })
    }
}

// ─────────────────────────────────────────────────────────────────
// SECTION 6: SECURITY ASSOCIATION
// ─────────────────────────────────────────────────────────────────

/// Security Association — one-directional IPsec context
struct SecurityAssociation {
    spi: u32,
    auth_key: Vec<u8>,
    seq_counter: u32,       // For outbound: last sequence number sent
    replay_window: ReplayWindow,
    anti_replay_enabled: bool,
}

impl SecurityAssociation {
    fn new(spi: u32, auth_key: Vec<u8>) -> Self {
        Self {
            spi,
            auth_key,
            seq_counter: 0,
            replay_window: ReplayWindow::new(),
            anti_replay_enabled: true,
        }
    }
}

// ─────────────────────────────────────────────────────────────────
// SECTION 7: MUTABLE FIELD ZEROING
// ─────────────────────────────────────────────────────────────────

/// Zero all mutable IPv4 fields in a raw packet buffer
///
/// Mutable fields (per RFC 4302):
///   - Byte  1:    DSCP/ToS
///   - Bytes 6-7:  Flags (MF bit, Fragment Offset; DF bit preserved)
///   - Byte  8:    TTL
///   - Bytes 10-11: Header Checksum
fn zero_mutable_ipv4_fields(packet: &mut Vec<u8>) {
    if packet.len() < 20 { return; }

    packet[1] = 0;  // Zero DSCP/ToS

    // Flags: zero MF (bit 13) and Fragment Offset (bits 0-12), keep DF (bit 14)
    let flags_frag = u16::from_be_bytes([packet[6], packet[7]]);
    let df_only = flags_frag & 0x4000;  // Keep only DF bit
    let zeroed = df_only.to_be_bytes();
    packet[6] = zeroed[0];
    packet[7] = zeroed[1];

    packet[8]  = 0;  // Zero TTL
    packet[10] = 0;  // Zero Header Checksum
    packet[11] = 0;
}

// ─────────────────────────────────────────────────────────────────
// SECTION 8: CONSTANT-TIME COMPARISON
// ─────────────────────────────────────────────────────────────────

/// Constant-time byte slice comparison
///
/// In Rust, use a timing-safe approach: accumulate XOR differences.
/// The comparison always runs for the full length regardless of where
/// differences occur — preventing timing side-channel attacks.
fn ct_compare(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let result: u8 = a.iter().zip(b.iter()).fold(0u8, |acc, (&x, &y)| acc | (x ^ y));
    result == 0
}

// ─────────────────────────────────────────────────────────────────
// SECTION 9: OUTBOUND PACKET PROCESSING
// ─────────────────────────────────────────────────────────────────

/// Error type for AH processing
#[derive(Debug)]
enum AhError {
    SequenceOverflow,
    PacketTooShort,
    SpiMismatch,
    ReplayTooOld,
    ReplayDuplicate,
    IcvMismatch,
    InvalidPacket,
}

impl fmt::Display for AhError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AhError::SequenceOverflow  => write!(f, "Sequence number overflow"),
            AhError::PacketTooShort    => write!(f, "Packet too short"),
            AhError::SpiMismatch       => write!(f, "SPI mismatch"),
            AhError::ReplayTooOld      => write!(f, "Replay: packet too old"),
            AhError::ReplayDuplicate   => write!(f, "Replay: duplicate packet"),
            AhError::IcvMismatch       => write!(f, "ICV verification failed (tampered)"),
            AhError::InvalidPacket     => write!(f, "Invalid packet structure"),
        }
    }
}

/// Apply AH protection to an outgoing packet
///
/// Takes the raw IP packet bytes, returns AH-protected packet bytes.
fn ah_outbound(sa: &mut SecurityAssociation, packet: &[u8]) -> Result<Vec<u8>, AhError> {
    if packet.len() < 20 {
        return Err(AhError::PacketTooShort);
    }

    // Sequence number overflow check
    if sa.seq_counter == u32::MAX {
        return Err(AhError::SequenceOverflow);
    }
    sa.seq_counter += 1;

    let ah_total = AhHeader::total_size();
    let out_len = packet.len() + ah_total;

    // Build the output packet
    let mut out = Vec::with_capacity(out_len);

    // ── Copy and modify IPv4 header ──
    out.extend_from_slice(&packet[..20]);

    // Set Protocol = AH (51)
    let original_proto = out[9];
    out[9] = AH_PROTOCOL_NUMBER;

    // Update Total Length (big-endian u16)
    let total_len = (out_len as u16).to_be_bytes();
    out[2] = total_len[0];
    out[3] = total_len[1];

    // ── Build AH header with ICV = 0 ──
    let payload_len = ((ah_total / 4) - 2) as u8;
    let ah = AhHeader {
        next_header: original_proto,
        payload_len,
        reserved:    0,
        spi:         sa.spi,
        seq_number:  sa.seq_counter,
        icv:         [0u8; AH_ICV_SIZE_SHA256],  // Zeros for HMAC computation
    };

    out.extend_from_slice(&ah.to_bytes());

    // ── Copy original payload ──
    out.extend_from_slice(&packet[20..]);

    // ── Prepare zeroed copy for HMAC ──
    let mut hmac_buf = out.clone();
    zero_mutable_ipv4_fields(&mut hmac_buf);
    // ICV bytes are already zero in hmac_buf

    // ── Compute HMAC-SHA256 ──
    let full_hmac = hmac_sha256(&sa.auth_key, &hmac_buf);

    // ── Embed truncated ICV into the AH header ──
    let icv_start = 20 + 12;  // After IPv4 header + AH fixed fields
    out[icv_start..icv_start + AH_ICV_SIZE_SHA256]
        .copy_from_slice(&full_hmac[..AH_ICV_SIZE_SHA256]);

    // ── Recompute IPv4 header checksum ──
    compute_ipv4_checksum(&mut out);

    println!("[AH OUTBOUND] Packet protected:");
    println!("  SPI:      0x{:08X}", sa.spi);
    println!("  Seq Num:  {}", sa.seq_counter);
    print!("  ICV:      ");
    for b in &out[icv_start..icv_start + AH_ICV_SIZE_SHA256] {
        print!("{:02X}", b);
    }
    println!("\n  Out size: {} bytes", out.len());

    Ok(out)
}

// ─────────────────────────────────────────────────────────────────
// SECTION 10: INBOUND PACKET PROCESSING
// ─────────────────────────────────────────────────────────────────

/// Verify and strip AH from an incoming packet
///
/// Returns the recovered original packet if valid.
fn ah_inbound(sa: &mut SecurityAssociation, packet: &[u8]) -> Result<Vec<u8>, AhError> {
    let ah_total = AhHeader::total_size();

    if packet.len() < 20 + ah_total {
        return Err(AhError::PacketTooShort);
    }

    // ── Verify IP Protocol = AH ──
    if packet[9] != AH_PROTOCOL_NUMBER {
        return Err(AhError::InvalidPacket);
    }

    // ── Parse AH header ──
    let ah = AhHeader::from_bytes(&packet[20..]).ok_or(AhError::PacketTooShort)?;

    // ── SPI check ──
    if ah.spi != sa.spi {
        eprintln!("[AH] SPI mismatch: got 0x{:X}, expected 0x{:X}", ah.spi, sa.spi);
        return Err(AhError::SpiMismatch);
    }

    // ── Anti-replay check ──
    if sa.anti_replay_enabled {
        match sa.replay_window.check(ah.seq_number) {
            ReplayStatus::TooOld   => return Err(AhError::ReplayTooOld),
            ReplayStatus::Duplicate => return Err(AhError::ReplayDuplicate),
            ReplayStatus::Ok       => {}
        }
    }

    // ── Prepare zeroed copy for HMAC recomputation ──
    let mut hmac_buf = packet.to_vec();
    zero_mutable_ipv4_fields(&mut hmac_buf);

    // Zero the ICV field in the working copy
    let icv_offset = 20 + 12;  // After IPv4 (20) + AH fixed (12)
    for b in hmac_buf[icv_offset..icv_offset + AH_ICV_SIZE_SHA256].iter_mut() {
        *b = 0;
    }

    // ── Recompute HMAC ──
    let computed_full = hmac_sha256(&sa.auth_key, &hmac_buf);
    let computed_icv = &computed_full[..AH_ICV_SIZE_SHA256];

    // ── Constant-time ICV comparison ──
    if !ct_compare(&ah.icv, computed_icv) {
        eprint!("[AH] ICV MISMATCH — packet tampered or wrong key!\n");
        eprint!("  Received ICV:  ");
        for b in &ah.icv { eprint!("{:02X}", b); }
        eprint!("\n  Computed ICV:  ");
        for b in computed_icv { eprint!("{:02X}", b); }
        eprintln!();
        return Err(AhError::IcvMismatch);
    }

    // ── Update anti-replay window (only after successful verification!) ──
    if sa.anti_replay_enabled {
        sa.replay_window.update(ah.seq_number);
    }

    // ── Strip AH header — reconstruct original packet ──
    let out_len = packet.len() - ah_total;
    let mut out = Vec::with_capacity(out_len);

    // Copy IPv4 header
    out.extend_from_slice(&packet[..20]);

    // Restore original protocol
    out[9] = ah.next_header;

    // Update Total Length
    let total_len = (out_len as u16).to_be_bytes();
    out[2] = total_len[0];
    out[3] = total_len[1];

    // Copy payload (skip AH header)
    out.extend_from_slice(&packet[20 + ah_total..]);

    // Recompute checksum
    compute_ipv4_checksum(&mut out);

    println!("[AH INBOUND] Packet verified and accepted:");
    println!("  SPI:      0x{:08X}", ah.spi);
    println!("  Seq Num:  {}", ah.seq_number);
    println!("  ICV:      VALID");
    println!("  Out size: {} bytes", out.len());

    Ok(out)
}

// ─────────────────────────────────────────────────────────────────
// SECTION 11: UTILITIES
// ─────────────────────────────────────────────────────────────────

/// Compute and set IPv4 header checksum in-place
fn compute_ipv4_checksum(packet: &mut Vec<u8>) {
    packet[10] = 0;
    packet[11] = 0;
    let mut sum: u32 = 0;
    for i in (0..20).step_by(2) {
        let word = u16::from_be_bytes([packet[i], packet[i + 1]]) as u32;
        sum += word;
    }
    while sum >> 16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    let checksum = (!(sum as u16)).to_be_bytes();
    packet[10] = checksum[0];
    packet[11] = checksum[1];
}

/// Build a minimal fake IPv4 + TCP packet for demonstration
fn build_fake_packet(src_ip: [u8; 4], dst_ip: [u8; 4], payload: &[u8]) -> Vec<u8> {
    let total_len = 20u16 + payload.len() as u16;
    let mut pkt = vec![
        0x45,                                    // Version=4, IHL=5
        0x00,                                    // ToS (DSCP=0, ECN=0)
        (total_len >> 8) as u8,                  // Total Length (high)
        (total_len & 0xFF) as u8,                // Total Length (low)
        0x12, 0x34,                              // Identification
        0x40, 0x00,                              // Flags: DF=1, MF=0, Offset=0
        64,                                      // TTL = 64
        6,                                       // Protocol = TCP
        0x00, 0x00,                              // Header Checksum (computed below)
        src_ip[0], src_ip[1], src_ip[2], src_ip[3],
        dst_ip[0], dst_ip[1], dst_ip[2], dst_ip[3],
    ];
    pkt.extend_from_slice(payload);
    compute_ipv4_checksum(&mut pkt);
    pkt
}

/// Print a hex dump of bytes
fn hex_dump(label: &str, data: &[u8]) {
    println!("{} ({} bytes):", label, data.len());
    for (i, chunk) in data.chunks(16).enumerate() {
        print!("  {:04X}  ", i * 16);
        for b in chunk { print!("{:02X} ", b); }
        // Padding for short last line
        for _ in 0..(16 - chunk.len()) { print!("   "); }
        print!(" | ");
        for b in chunk {
            print!("{}", if b.is_ascii_graphic() { *b as char } else { '.' });
        }
        println!();
    }
}

// ─────────────────────────────────────────────────────────────────
// SECTION 12: MAIN DEMONSTRATION
// ─────────────────────────────────────────────────────────────────

fn main() {
    println!("═══════════════════════════════════════════════════════");
    println!("   AH Protocol (RFC 4302) — Rust Implementation Demo  ");
    println!("═══════════════════════════════════════════════════════\n");

    // ── Setup Security Associations ──
    let auth_key = b"RustAHKey256BitsLong1234567890AB".to_vec();

    let mut sa_sender = SecurityAssociation::new(0xDEADBEEF, auth_key.clone());
    let mut sa_receiver = SecurityAssociation::new(0xDEADBEEF, auth_key);

    println!("Security Association:");
    println!("  SPI:      0x{:08X}", sa_sender.spi);
    println!("  Key len:  {} bytes ({} bits)\n", sa_sender.auth_key.len(),
             sa_sender.auth_key.len() * 8);

    // ── Build original packet ──
    let src_ip = [192, 168, 1, 10];
    let dst_ip = [192, 168, 1, 20];
    let message = b"Hello, Authentication Header!";

    let original = build_fake_packet(src_ip, dst_ip, message);

    hex_dump("Original Packet", &original);
    println!("  Payload text: {:?}\n", std::str::from_utf8(&original[20..]).unwrap());

    // ── OUTBOUND ──
    println!("── OUTBOUND PROCESSING ──");
    let ah_packet = match ah_outbound(&mut sa_sender, &original) {
        Ok(p) => { println!(); p }
        Err(e) => { eprintln!("OUTBOUND FAILED: {}", e); return; }
    };
    hex_dump("AH-Protected Packet", &ah_packet);

    // ── INBOUND (valid) ──
    println!("\n── INBOUND PROCESSING (valid packet) ──");
    match ah_inbound(&mut sa_receiver, &ah_packet) {
        Ok(recovered) => {
            println!();
            hex_dump("Recovered Packet", &recovered);
            println!("  Payload text: {:?}",
                     std::str::from_utf8(&recovered[20..]).unwrap());
        }
        Err(e) => eprintln!("INBOUND FAILED (unexpected): {}", e),
    }

    // ── Tamper Detection ──
    println!("\n── TAMPER DETECTION TEST ──");
    let mut tampered = ah_packet.clone();
    let last = tampered.len() - 1;
    tampered[last] ^= 0xFF;  // Flip bits in the last payload byte

    let mut sa_recv2 = SecurityAssociation::new(0xDEADBEEF, b"RustAHKey256BitsLong1234567890AB".to_vec());
    sa_recv2.anti_replay_enabled = false; // Skip replay for this test

    match ah_inbound(&mut sa_recv2, &tampered) {
        Err(AhError::IcvMismatch) => println!("[✓] Tampered packet correctly REJECTED!"),
        Err(e)                    => println!("[?] Rejected with: {}", e),
        Ok(_)                     => println!("[✗] ERROR: Tampered packet ACCEPTED (bug!)"),
    }

    // ── Replay Attack Test ──
    println!("\n── REPLAY ATTACK TEST ──");
    // sa_receiver already accepted seq=1. Re-sending same packet should be rejected.
    match ah_inbound(&mut sa_receiver, &ah_packet) {
        Err(AhError::ReplayDuplicate) => println!("[✓] Replayed packet correctly REJECTED!"),
        Err(e)                        => println!("[?] Rejected with: {}", e),
        Ok(_)                         => println!("[✗] ERROR: Replayed packet ACCEPTED (bug!)"),
    }

    // ── HMAC Self-Test ──
    println!("\n── HMAC-SHA256 SELF-TEST ──");
    // RFC 4231 Test Vector 1:
    let key = vec![0x0b_u8; 20];
    let data = b"Hi There";
    let result = hmac_sha256(&key, data);
    let expected = [
        0xb0, 0x34, 0x4c, 0x61, 0xd8, 0xdb, 0x38, 0x53,
        0x5c, 0xa8, 0xaf, 0xce, 0xaf, 0x0b, 0xf1, 0x2b,
        0x88, 0x1d, 0xc2, 0x00, 0xc9, 0x83, 0x3d, 0xa7,
        0x26, 0xe9, 0x37, 0x6c, 0x2e, 0x32, 0xcf, 0xf7,
    ];
    if result == expected {
        println!("[✓] HMAC-SHA256 matches RFC 4231 test vector 1!");
    } else {
        println!("[✗] HMAC-SHA256 MISMATCH!");
        print!("  Got:      "); for b in &result { print!("{:02X}", b); } println!();
        print!("  Expected: "); for b in &expected { print!("{:02X}", b); } println!();
    }

    println!("\n═══════════════════════════════════════════════════════");
    println!("   All tests completed.");
    println!("═══════════════════════════════════════════════════════");
}
```

---

## 21. Security Analysis and Attack Vectors

### What AH Protects Against

```
THREAT                    │ AH PROTECTION
──────────────────────────┼────────────────────────────────────────
Packet tampering           │ ✓ ICV will mismatch → packet dropped
Payload injection          │ ✓ ICV covers payload
IP spoofing (src IP)       │ ✓ Src IP is authenticated
Replay attacks             │ ✓ Sliding window + sequence numbers
Forged AH headers          │ ✓ SPI, SeqNum, NextHdr all in ICV scope
Man-in-the-middle          │ ✓ Tampering detected via ICV
```

### What AH Does NOT Protect Against

```
THREAT                    │ WHY AH FAILS
──────────────────────────┼────────────────────────────────────────
Eavesdropping             │ ✗ AH provides NO encryption
Traffic analysis          │ ✗ Packet sizes/timing visible
Denial of Service (DoS)   │ ✗ Attacker can send random packets;
                          │   verification still costs CPU time
NAT traversal             │ ✗ NAT modifies IP header → ICV fails
```

### Timing Side-Channel Attack (Why CT Comparison Matters)

```
VULNERABLE CODE (naive):
  if (memcmp(received_icv, computed_icv, 16) != 0) DROP;

ATTACK:
  1. Attacker sends many packets with different ICVs
  2. Measures response time precisely
  3. If byte 1 matches, comparison continues to byte 2 (slightly slower)
  4. Attacker can deduce ICV byte by byte in 256 * 16 = 4096 attempts!

SAFE CODE (constant time):
  result = 0
  for each byte i: result |= received[i] ^ computed[i]
  // Same time regardless of where mismatch occurs
  if (result != 0) DROP;
```

### Key Management Attacks

```
If the HMAC key is compromised:
  - All traffic using that SA can be forged
  - Attacker can generate valid ICVs for any packet

Mitigation:
  - Rotate keys periodically (IKEv2 CHILD_SA rekeying)
  - Use strong random key generation (CSPRNG)
  - Keep key material in secure storage
  - Use Perfect Forward Secrecy (PFS) — new DH exchange for each SA
```

### Sequence Number Exhaustion

```
32-bit sequence number: 2^32 = 4,294,967,296 packets per SA

At 10 Gbps with 1500-byte packets:
  Packets/sec = 10,000,000,000 / (1500 * 8) ≈ 833,333 packets/sec
  Time to exhaust: 4,294,967,296 / 833,333 ≈ 5,159 seconds ≈ 86 minutes!

Solutions:
  1. Extended Sequence Number (ESN): 64-bit virtual counter
     → 2^64 / 833,333 ≈ 700 billion seconds → not a concern
  2. Proactive SA rekeying: start new SA before rollover
```

---

## 22. Mental Models and Summary

### The "Wax Seal" Mental Model

```
AH is like a wax seal on a transparent letter:

  ┌──────────────────────────────────────┐
  │ Letter content visible to everyone  │
  │ (no encryption = no confidentiality)│
  │                                      │
  │ But the wax seal proves:            │
  │  [1] Who sent it (authentication)   │
  │  [2] It hasn't been tampered with   │
  │      (integrity)                    │
  │  [3] This is the original, not a    │
  │      copy (anti-replay)             │
  └──────────────────────────────────────┘
```

### The "Notarized Document" Mental Model

```
AH is like a notarized document:

  The notary (HMAC key) certifies:
    "This document was created by Person X
     and has not been modified since then."

  Anyone can READ the document (no encryption).
  But only Person X and the notary can CERTIFY it.
  If anyone changes even one word, the notarization is invalid.
```

### Protocol Decision Flowchart

```
Do you need security for IP traffic?
           │ YES
           ▼
Do you need encryption (confidentiality)?
     │ YES                │ NO
     ▼                    ▼
Use ESP              Do you need to
(RFC 4303)           authenticate the
                     IP header itself?
                     │ YES         │ NO
                     ▼             ▼
                  Use AH       Use ESP
                  (RFC 4302)   (provides
                               auth without
                               IP hdr auth)

Is NAT involved in your network?
           │ YES
           ▼
AH CANNOT WORK → Use ESP with NAT-T (RFC 3948)
```

### Complete AH Data Flow Summary

```
SENDER                            NETWORK                    RECEIVER
  │                                  │                           │
  │ 1. Original IP packet            │                           │
  │ 2. SA lookup (SPI, key)          │                           │
  │ 3. seq_counter++                 │                           │
  │ 4. Build AH (ICV=0)              │                           │
  │ 5. Insert AH after IP header     │                           │
  │ 6. Zero mutable IP fields        │                           │
  │ 7. HMAC(key, zeroed_packet)      │                           │
  │ 8. Embed HMAC → ICV field        │                           │
  │ 9. Restore mutable fields        │                           │
  │10. Recompute IP checksum         │                           │
  │                                  │                           │
  │────── AH-protected packet ──────►│────── AH packet ─────────►│
  │                                  │ (TTL decremented,         │ 1. IP proto=51 → AH
  │                                  │  checksum updated         │ 2. Extract SPI
  │                                  │  at each router hop)      │ 3. SA lookup
  │                                  │                           │ 4. Anti-replay check
  │                                  │                           │ 5. Zero mutable fields
  │                                  │                           │ 6. Zero ICV field
  │                                  │                           │ 7. HMAC(key, zeroed)
  │                                  │                           │ 8. CT compare ICV
  │                                  │                           │ 9. Update replay window
  │                                  │                           │10. Strip AH header
  │                                  │                           │11. Deliver to upper layer
```

### Key Facts to Remember

```
RFC:            4302 (obsoletes 2402)
Protocol Num:   51
Header size:    12 bytes fixed + ICV length
ICV size:       12-32 bytes (algorithm dependent)
Modes:          Transport (host-to-host) / Tunnel (gateway-to-gateway)
Provides:       Integrity + Authentication + Anti-replay
Does NOT:       Encrypt (no confidentiality)
NAT compatible: NO (IP address is authenticated)
Algorithm must: HMAC-SHA1-96 (MUST), HMAC-SHA256-128 (SHOULD)
Seq numbers:    32-bit (64-bit ESN supported)
Replay window:  64 packets default
```

---

*This guide covers the complete AH protocol as defined in RFC 4302. Every concept, from byte-level header structure to cryptographic internals, anti-replay mechanics, and complete C and Rust implementations, has been provided for deep, practical understanding.*

Here is your complete, in-depth guide to the **AH (Authentication Header) Protocol**. Here's a map of what's inside:

---

**What the guide covers, end to end:**

**Conceptual Foundation** — why AH exists, what the four network threats are (eavesdropping, tampering, impersonation, replay), and exactly which three AH solves (not encryption — that's the key insight beginners miss).

**The IPsec Family** — where AH sits in the protocol stack (Layer 3), how it relates to ESP, IKE, and Security Associations, and why operating at Layer 3 gives transparent application-independent security.

**Core Vocabulary** — SPI, ICV, HMAC, SA, SAD, SPD, mutable fields — every term is defined with precise meaning before it's used.

**Header Structure** — a byte-by-byte breakdown of all six fields: Next Header, Payload Length (and its confusing formula), Reserved, SPI, Sequence Number, and ICV — with exact sizes, value ranges, and why each field exists.

**Transport vs Tunnel Mode** — full ASCII packet diagrams showing exactly how bytes are laid out in both modes, who uses each, and what is authenticated in each case.

**Anti-Replay Sliding Window** — the full state machine with a decision flowchart, bitmap mechanics, why a window is used instead of a simple threshold, and why the window is updated *only after* ICV verification.

**Mutable Fields** — the subtle but critical concept: which IPv4/IPv6 fields change in transit (TTL, ToS, checksum, flags) and must be zeroed before HMAC computation, or the receiver's HMAC will never match.

**AH and NAT** — the fatal incompatibility explained with a concrete example, and why this is the primary reason AH is rarely used in internet-facing deployments today.

**C Implementation** — full working code: manual SHA-256, HMAC-SHA256, outbound and inbound processing, anti-replay window, and constant-time ICV comparison with comments explaining every design decision.

**Rust Implementation** — idiomatic Rust with type-safe structures, `Result`-based error handling, the same anti-replay and HMAC logic, and an RFC 4231 HMAC self-test vector for correctness verification.

**Security Analysis** — what AH guards against, what it cannot protect, the timing side-channel attack on naive ICV comparison, and sequence number exhaustion analysis with real throughput numbers.