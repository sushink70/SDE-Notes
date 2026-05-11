# DTLS — Datagram Transport Layer Security: The Complete In-Depth Guide

> **Scope**: DTLS 1.0 (RFC 4347), DTLS 1.2 (RFC 6347), DTLS 1.3 (RFC 9147), Connection ID (RFC 9146).  
> Everything from first principles through production deployment.

---

## Table of Contents

1. [Why DTLS Exists — The Problem Space](#1-why-dtls-exists)
2. [TLS Recap — What We Are Adapting From](#2-tls-recap)
3. [Why TLS Cannot Run Directly Over UDP](#3-why-tls-cannot-run-over-udp)
4. [DTLS Architecture — The 10,000-Foot View](#4-dtls-architecture)
5. [Record Layer](#5-record-layer)
6. [Epoch and Sequence Numbers](#6-epoch-and-sequence-numbers)
7. [Handshake Protocol](#7-handshake-protocol)
8. [Cookie Exchange — DoS Prevention](#8-cookie-exchange)
9. [Retransmission and Reliability](#9-retransmission-and-reliability)
10. [Fragmentation and Reassembly](#10-fragmentation-and-reassembly)
11. [Cipher Suites and Cryptography](#11-cipher-suites-and-cryptography)
12. [Alert Protocol](#12-alert-protocol)
13. [Session Resumption](#13-session-resumption)
14. [DTLS 1.3 — What Changed](#14-dtls-13)
15. [Connection ID Extension (RFC 9146)](#15-connection-id-extension)
16. [PMTU Discovery and Handling](#16-pmtu-discovery-and-handling)
17. [Replay Protection](#17-replay-protection)
18. [SRTP and WebRTC Integration](#18-srtp-and-webrtc-integration)
19. [State Machine — Complete](#19-state-machine)
20. [Security Analysis and Threat Model](#20-security-analysis-and-threat-model)
21. [Implementation Guide (Rust + Go)](#21-implementation-guide)
22. [Debugging and Observability](#22-debugging-and-observability)
23. [Performance Tuning](#23-performance-tuning)
24. [Production Checklist](#24-production-checklist)
25. [Further Reading](#25-further-reading)

---

## 1. Why DTLS Exists

### The Core Problem

The Internet has two dominant transport-layer contracts:

| Property | TCP | UDP |
|---|---|---|
| Ordered delivery | ✅ | ❌ |
| Reliable delivery | ✅ | ❌ |
| Congestion control | ✅ | ❌ |
| Connection-oriented | ✅ | ❌ |
| Head-of-line blocking | ✅ (problem) | ❌ |
| Latency overhead | Higher | Lower |
| State on network path | Firewall sees connection | No connection state |

TLS was designed to sit atop TCP's reliable, ordered byte stream. Entire categories of applications — **real-time voice, video, online games, IoT sensors, tunnelling, VPNs, DNS over secure transport** — inherently need UDP because:

- They can tolerate or even prefer lost packets over stale retransmitted data (a game frame from 200ms ago is worthless).
- TCP head-of-line blocking compounds latency unpredictably.
- The application already implements its own reliability where required.

But these applications still need **confidentiality, integrity, and authentication**. IPSEC covers layer-3, but is heavyweight, kernel-level, and difficult to deploy in user space or through NATs. Application-layer security over UDP was ad-hoc before DTLS.

**DTLS provides the security guarantees of TLS to datagram transport protocols.**

### Design Mandate (from RFC 6347 §1)

> "The primary goal of the DTLS protocol is to construct a TLS protocol that can run over an unreliable datagram transport, in the sense that a lost or reordered record will not break the security of the channel."

The designers made a crucial architectural decision: **make DTLS as mechanically close to TLS as possible**, adding only the minimum machinery needed to handle the unreliable transport. This minimises the new attack surface and lets implementations share code.

### Canonical Use Cases

- **WebRTC**: DTLS-SRTP for media encryption, DTLS for SCTP data channels.
- **OpenVPN / WireGuard predecessors**: VPN tunnels over UDP.
- **CoAP/IoT**: Constrained Application Protocol (RFC 7252) mandates DTLS.
- **QUIC (pre-standardisation)**: Early QUIC versions used DTLS concepts; modern QUIC integrates TLS 1.3 directly but DTLS inspired the design.
- **Gaming**: Authenticated, encrypted game state.
- **DNS over DTLS (RFC 8094)**: Encrypted DNS using datagrams.
- **RADIUS over DTLS (RFC 7360)**: Secure AAA protocol.

---

## 2. TLS Recap

To understand what DTLS changes, you must first internalise what TLS does. This section is a precise technical recap.

### TLS Record Protocol

Every TLS message — including handshake, alert, and application data — is wrapped in a **TLS Record**:

```
TLS Record Format (RFC 8446 §5.1):

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  ContentType  |    Legacy Version (0x03 0x03)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Length (uint16)     |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|                  Fragment (variable)                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

ContentType:
  20 = change_cipher_spec
  21 = alert
  22 = handshake
  23 = application_data
  24 = heartbeat
```

**Key properties TLS assumes:**
1. Records arrive **in order** (TCP guarantees this).
2. Records arrive **reliably** (TCP retransmits if needed).
3. The record sequence number is **implicit** — it's the position in the byte stream.
4. A single record may span multiple TCP segments; TCP reassembles before delivery.

### TLS Handshake (1.2 abbreviated)

```
Client                                               Server
  |                                                      |
  |--- ClientHello ---------------------------------->   |
  |                                                      |
  |<-- ServerHello -----------------------------------   |
  |<-- Certificate -----------------------------------   |
  |<-- ServerKeyExchange (if needed) ----------------   |
  |<-- ServerHelloDone -------------------------------   |
  |                                                      |
  |--- ClientKeyExchange ---------------------------->   |
  |--- ChangeCipherSpec ----------------------------->   |
  |--- Finished (encrypted) ------------------------->   |
  |                                                      |
  |<-- ChangeCipherSpec ------------------------------   |
  |<-- Finished (encrypted) --------------------------   |
  |                                                      |
  |=== Application Data (encrypted) =================   |
```

### TLS 1.3 Handshake (abbreviated)

```
Client                                               Server
  |                                                      |
  |--- ClientHello (+ key_share, supported_versions) --> |
  |                                                      |
  |<-- ServerHello (+ key_share) ---------------------   |
  |<-- {EncryptedExtensions} ------------------------    |  Handshake keys
  |<-- {Certificate} --------------------------------    |  derived here
  |<-- {CertificateVerify} --------------------------    |
  |<-- {Finished} -----------------------------------    |
  |                                                      |
  |--- {Finished} ----------------------------------->   |
  |                                                      |
  |=== [Application Data] ============================   |  App keys
```

The TLS 1.3 handshake achieves **1-RTT** for new connections and **0-RTT** for session resumption.

---

## 3. Why TLS Cannot Run Directly Over UDP

This section is the most important conceptual foundation. Understanding **exactly why** TLS breaks over UDP tells you exactly **what DTLS had to add**.

### Problem 1: Implicit Sequence Numbers

TLS uses the byte position in the TCP stream as its implicit record sequence number. The MAC is computed over:

```
MAC(seq_num || type || version || length || data)
```

Over UDP, records have no inherent ordering or position. If you receive a DTLS record, you cannot know its sequence number unless it is **explicitly included** in the record itself.

**DTLS Fix**: Add an explicit 48-bit sequence number to every record header. The MAC computation includes this explicit number.

### Problem 2: Record Reordering Breaks State Machine

The TLS handshake state machine is strictly sequential. If `ServerKeyExchange` arrives before `Certificate`, the state machine is confused. Over TCP, this cannot happen. Over UDP it absolutely can.

**DTLS Fix**: The handshake state machine is explicitly designed to handle out-of-order messages. Messages that arrive for a future state are buffered. The state machine retries from its current state on timeout.

### Problem 3: Loss Causes Handshake Deadlock

```
Client             Server
  |                  |
  |-- ClientHello -> |
  |                  |
  |    (UDP packet   |
  |     dropped)     |
  |                  |
  |   (Both sides    |
  |    now wait)     |
  |     DEADLOCK     |
```

TLS has no timeout-based retransmission because TCP handles reliability. If a TCP segment is lost, TCP retransmits transparently. If a TLS handshake message is lost over UDP, there is no mechanism to recover.

**DTLS Fix**: Implement a **flight-based retransmission timer** (similar to TCP's RTO) at the handshake layer. Each group of handshake messages is called a **flight**. If an expected response does not arrive within the timeout, the last flight is retransmitted.

### Problem 4: Large Handshake Messages Exceed MTU

A TLS Certificate message may be several kilobytes — far larger than the typical path MTU of 1500 bytes (Ethernet) or 1280 bytes (IPv6 minimum). TCP segments the data automatically. UDP does not — a datagram larger than the MTU will be fragmented at the IP layer, and **any single IP fragment being lost causes the entire UDP datagram to be dropped**.

**DTLS Fix**: Implement application-layer fragmentation and reassembly of handshake messages. Each handshake message carries `fragment_offset` and `fragment_length` fields.

### Problem 5: DoS via Stateful Handshake Initiation

Over TCP, the three-way handshake requires the client to demonstrate reachability before the server allocates any state. Over UDP, the first packet from a client (ClientHello) immediately causes the server to allocate handshake state, buffer messages, start a timer, etc.

An attacker with a spoofed source IP can send millions of ClientHellos, exhausting the server's memory and CPU.

**DTLS Fix**: The **cookie mechanism** — a stateless challenge-response before any server state is allocated.

### Problem 6: Message Boundary Preservation

TLS records may be split across or merged in TCP segments. TCP is a byte stream; the TLS library must buffer and parse. UDP preserves message boundaries — a UDP datagram corresponds to exactly one application `sendmsg()` call. This is actually helpful for DTLS, but it means the framing model is completely different.

### Summary of Problems and Fixes

```
TLS Assumption                    UDP Reality              DTLS Fix
───────────────────────────────────────────────────────────────────────────────
Implicit ordering (TCP position)  Any order possible       Explicit seq# in record
Reliable delivery (TCP rexmit)    Packets lost             Handshake retransmission timer
Sequential state machine          Out-of-order arrives     Buffer + message_seq fields
MTU handled by TCP                IP fragmentation kills   App-layer fragmentation
DoS: TCP SYN cookie               Free packet spoofing     Cookie exchange
```

---

## 4. DTLS Architecture

### Layering

```
Application
     │
     ▼
┌──────────────────────────────────────────────────────┐
│               DTLS Protocol                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Handshake   │  │    Alert     │  │   App     │  │
│  │  Protocol    │  │   Protocol   │  │   Data    │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                │        │
│         ▼                 ▼                ▼        │
│  ┌──────────────────────────────────────────────┐   │
│  │           DTLS Record Layer                  │   │
│  │  (content type, epoch, seq#, length, data)   │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
     │
     ▼
  UDP / DCCP / SCTP / raw datagram transport
     │
     ▼
  IP Network
```

### Key Concepts Introduced by DTLS

| Concept | Purpose |
|---|---|
| **Epoch** | Monotonically increasing counter; incremented each time keys change (ChangeCipherSpec equivalent) |
| **Sequence number** | 48-bit per-epoch counter; replaces implicit TCP position |
| **message_seq** | Handshake message ordering field (separate from record seq#) |
| **Fragment offset/length** | Application-layer handshake fragmentation |
| **Cookie** | Stateless DoS prevention token |
| **Flight** | A logical group of handshake messages sent together |
| **Retransmit timer** | SRTT-estimated timeout for handshake flights |
| **Sliding window** | Replay attack detection on received records |

---

## 5. Record Layer

### DTLS 1.2 Record Format (RFC 6347 §4.1)

```
DTLS 1.2 Record:

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  ContentType  |   Version (Major)  |  Version (Minor)          |
|    (1 byte)   |     0xFE           |   0xFD (DTLS 1.2)         |
|               |     0xFE           |   0xFF (DTLS 1.0)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Epoch (uint16)           |                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                           |
|          Sequence Number (48-bit)                             |
+                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |       Length (uint16)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                        Fragment (variable)                    |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Total header: 13 bytes
(vs TLS: 5 bytes — DTLS adds 8 bytes for epoch + seq#)
```

### Field Definitions

**ContentType** (1 byte):
- `20` — `change_cipher_spec`
- `21` — `alert`
- `22` — `handshake`
- `23` — `application_data`
- `24` — `heartbeat`

**Version** (2 bytes):
- DTLS versions use **inverted minor version numbers** to avoid confusion with TLS:
  - DTLS 1.0 → `0xFEFF` (TLS would be `0x0301`)
  - DTLS 1.2 → `0xFEFD` (TLS would be `0x0303`)
  - The major byte `0xFE` is a deliberate marker.

**Why inverted?** TLS has a version negotiation rule: "accept records with version ≥ minimum supported." If you naively used `0x0302` for DTLS 1.0 and `0x0304` for DTLS 1.2, then a DTLS 1.0 library might accept a DTLS 1.2 record thinking it's a lower protocol version. By inverting, DTLS 1.2 (`0xFEFD`) numerically precedes DTLS 1.0 (`0xFEFF`), breaking any TLS version comparison logic.

**Epoch** (2 bytes):
- Starts at 0.
- Incremented each time the cipher state changes (conceptually, each `ChangeCipherSpec`).
- Records from different epochs are independent; a record's MAC is verified using the keys for its epoch.
- An implementation MUST NOT process records from an old epoch if it has moved past it (except in a brief transition window).

**Sequence Number** (48 bits = 6 bytes):
- Per-epoch monotonically increasing counter.
- Resets to 0 when epoch increments.
- Explicitly included in the record; included in MAC computation.
- Used for replay window detection.

**Length** (2 bytes):
- Length of the fragment in bytes.
- Does NOT include the 13-byte header.
- Maximum: 2^14 + 2048 bytes (same as TLS, but practically limited by MTU).

### Record Processing — Sending

```
Plaintext Payload
        │
        ▼
┌───────────────────┐
│  Compress (null)  │  DTLS doesn't use compression (CRIME vulnerability)
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────────┐
│  Encrypt + MAC  (or AEAD)                 │
│  Using current epoch's write keys         │
│  Additional data for AEAD:                │
│    epoch || seq_num || type || ver || len │
└────────────────────┬──────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│  Prepend DTLS Record Header (13 bytes)     │
│  type | version | epoch | seq | len       │
└────────────────────────────────────────────┘
                     │
                     ▼
          UDP sendmsg() → network
```

### Record Processing — Receiving

```
UDP recvmsg() → raw datagram
        │
        ▼
┌───────────────────────────────┐
│  Parse DTLS Record Header     │
│  Extract: type, version,      │
│  epoch, seq_num, length       │
└──────────────┬────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Epoch check:                            │
│  - If epoch == current read epoch: OK    │
│  - If epoch == current-1: may be in      │
│    flight, buffer briefly                │
│  - Otherwise: DROP (old or future epoch) │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Replay window check:                    │
│  Reject if seq_num already seen          │
│  (sliding window of 64 bits)             │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Decrypt + verify MAC / AEAD tag         │
│  Using epoch's read keys                 │
│  On failure: SILENTLY DROP (not alert)   │
└──────────────┬───────────────────────────┘
               │
               ▼
       Deliver to upper layer
```

**Why silently drop on decryption failure?** Sending an alert leaks information about which packets were received, enabling oracle attacks. The remote end's retransmission timer will handle the loss.

### Multiple Records in One Datagram

DTLS allows — and implementations should use — **multiple records packed into a single UDP datagram** to reduce header overhead. Each record has its own 13-byte header.

```
UDP Datagram
├── DTLS Record 1 (Handshake fragment)
│   └── 13-byte header | payload
├── DTLS Record 2 (Handshake fragment)
│   └── 13-byte header | payload
└── DTLS Record 3 (ChangeCipherSpec)
    └── 13-byte header | payload
```

This is especially important during the handshake where small messages can be coalesced efficiently.

---

## 6. Epoch and Sequence Numbers

This is the most subtle aspect of DTLS and the root cause of most implementation bugs.

### Epoch Lifecycle

```
Epoch 0:  Cleartext (pre-handshake)
          - ClientHello, ServerHello, Certificate, etc. travel here
          - seq# counts from 0

ChangeCipherSpec signal:
          - Client sends CCS → client's write epoch becomes 1
          - Server sends CCS → server's write epoch becomes 1
          - After CCS, the sending side resets its write seq# to 0

Epoch 1:  Encrypted with handshake-derived session keys
          - Finished messages, then application data

Renegotiation (DTLS 1.2 only):
          - New handshake runs while existing session is in epoch 1
          - New CCS moves both sides to epoch 2
```

### The Epoch Transition Problem

During the handshake transition, the client sends CCS and then immediately sends the encrypted Finished message. But what if the server receives the Finished before the CCS? This is a real race condition over UDP.

```
Client                                    Server
  |                                          |
  |--- CCS (epoch 0, seq 5) ----------->    |  (may be delayed/lost)
  |--- Finished (epoch 1, seq 0) ------->   |
  |                                          |
  |         Server receives Finished         |
  |         but hasn't seen CCS yet!        |
  |         (It's epoch 1, but server's     |
  |          current read epoch is 0)       |
```

**DTLS specification solution** (RFC 6347 §4.1):  
A receiver SHOULD buffer records from the next epoch for a brief period (one PMTU's worth of records) to allow for CCS reordering. Once the CCS for that epoch arrives, the buffered records can be processed.

### Sequence Number Rules

1. The sequence number is a **48-bit integer**, never wrapping in practice.
2. It is incremented by 1 for each record sent in a given epoch.
3. Each epoch has **its own independent sequence number counter** starting at 0.
4. The full 64-bit value used for replay detection is `epoch (16 bits) || seq_num (48 bits)`.

### Sequence Number in AEAD

For AEAD ciphers (GCM, ChaCha20-Poly1305), the Additional Data (AD) used for authentication includes:

```
AD = epoch (2 bytes) || seq_num (6 bytes) || content_type (1 byte)
   || version (2 bytes) || length (2 bytes)
```

The nonce is typically constructed as:
```
nonce = fixed_iv XOR (epoch || seq_num padded to nonce length)
```

For AES-128-GCM (12-byte nonce):
```
nonce = write_iv (12 bytes) XOR (0x0000 || epoch (2 bytes) || seq_num (6 bytes))
         ^---- left 2 bytes from write_iv       ^---- explicit part (8 bytes)
```

---

## 7. Handshake Protocol

### Handshake Message Format

Every DTLS handshake message has a header that extends the TLS handshake header with three new fields:

```
DTLS Handshake Message:

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  HandshakeType|               Length (uint24)                 |
|    (1 byte)   |              (3 bytes)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        message_seq (uint16)   |      fragment_offset (uint24) |
|          [DTLS NEW]           |         [DTLS NEW]  ...       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  ...fragment_offset (cont.)   |      fragment_length (uint24) |
|                               |         [DTLS NEW]            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  ...fragment_length (cont.)   |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|                         Body (variable)                       |
|                    (fragment of full message)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Header size: 12 bytes (vs TLS: 4 bytes)
DTLS adds 8 bytes: message_seq(2) + fragment_offset(3) + fragment_length(3)
```

**HandshakeType values:**

| Value | Name |
|---|---|
| 1 | client_hello |
| 2 | server_hello |
| 3 | hello_verify_request |
| 4 | new_session_ticket |
| 11 | certificate |
| 12 | server_key_exchange |
| 13 | certificate_request |
| 14 | server_hello_done |
| 15 | certificate_verify |
| 16 | client_key_exchange |
| 20 | finished |
| 24 | key_update (DTLS 1.3) |
| 25 | compressed_certificate |

**message_seq**: Monotonically increasing per-handshake counter assigned to each *logical* handshake message (not each fragment). If message 5 is fragmented into 3 records, all 3 records have `message_seq = 5` but different `fragment_offset` values. This is the key distinction: record-layer `seq_num` counts records; handshake `message_seq` counts logical messages.

**fragment_offset**: Byte offset of this fragment within the full message body.

**fragment_length**: Byte length of this fragment's body data.

For a non-fragmented message: `fragment_offset = 0`, `fragment_length = Length`.

### Complete DTLS 1.2 Handshake (With Cookie)

```
Client                                          Server
  |                                                |
  |=== FLIGHT 1 ================================>  |
  |--- ClientHello (no cookie) ----------------->  |
  |    seq=0, msg_seq=0                            |
  |                                                |
  |<== FLIGHT 2 ==================================  |
  |<-- HelloVerifyRequest (cookie) --------------  |
  |    seq=0, msg_seq=0                            |
  |                                                |
  |=== FLIGHT 3 ================================>  |
  |--- ClientHello (with cookie) --------------->  |
  |    seq=1, msg_seq=1  [NOTE: msg_seq increments |
  |                        even on retry]          |
  |                                                |
  |<== FLIGHT 4 ==================================  |
  |<-- ServerHello --------------------------------  msg_seq=1
  |<-- Certificate --------------------------------  msg_seq=2
  |<-- ServerKeyExchange --------------------------  msg_seq=3 (if DHE/ECDHE)
  |<-- CertificateRequest -------------------------  msg_seq=4 (if mutual auth)
  |<-- ServerHelloDone ----------------------------  msg_seq=5
  |                                                |
  |=== FLIGHT 5 ================================>  |
  |--- Certificate --------------------------------> msg_seq=2 (if requested)
  |--- ClientKeyExchange ------------------------->  msg_seq=3
  |--- CertificateVerify ------------------------->  msg_seq=4 (if cert sent)
  |--- [ChangeCipherSpec] ------------------------>  (not handshake, but record)
  |--- Finished (encrypted) --------------------->  msg_seq=5
  |    epoch=1, seq=0                              |
  |                                                |
  |<== FLIGHT 6 ==================================  |
  |<-- [ChangeCipherSpec] ------------------------  |
  |<-- Finished (encrypted) ----------------------  epoch=1, seq=0
  |                                                |
  |========= APPLICATION DATA (epoch=1) =========  |
```

### Handshake Without Cookie (when DoS protection not needed)

The cookie exchange adds 1 RTT. When the server has alternative DoS mitigations (rate limiting, IP allowlisting), it may choose to skip the cookie exchange by sending an empty cookie in HelloVerifyRequest or omitting the HelloVerifyRequest entirely.

### ClientHello Structure

```
ClientHello {
    ProtocolVersion client_version;     // 0xFEFD for DTLS 1.2
    Random random;                      // 32 bytes: 4 byte unix time + 28 random
    SessionID session_id;               // 0-32 bytes (empty for new session)
    opaque cookie<0..2^8-1>;           // DTLS ONLY — for cookie exchange
    CipherSuite cipher_suites<2..2^16-2>;
    CompressionMethod compression_methods<1..2^8-1>;
    Extension extensions<0..2^16-1>;
}
```

The `cookie` field is the critical DTLS addition to ClientHello. In the first ClientHello, it is empty. In the second (after HelloVerifyRequest), it contains the cookie provided by the server.

### HelloVerifyRequest Structure

```
HelloVerifyRequest {
    ProtocolVersion server_version;    // Server's version
    opaque cookie<0..2^8-1>;          // Generated by server
}
```

The HelloVerifyRequest is **NOT** included in the handshake transcript hash used for Finished message computation. This is important: the Finished MAC covers the handshake as if only the second ClientHello and later messages exist.

### Finished Message Verification

The Finished message proves that both sides computed the same handshake transcript:

```
verify_data = PRF(master_secret, finished_label,
                  Hash(handshake_messages))
                  
                  Where handshake_messages is the concatenation of all
                  handshake message bodies (the 12-byte DTLS headers
                  are included in this hash, NOT the record headers).
                  HelloVerifyRequest is EXCLUDED.
```

---

## 8. Cookie Exchange

### Motivation: Stateless Handshake Challenge

The cookie mechanism (inspired by TCP SYN cookies) allows a server to cryptographically verify client reachability and source IP/port before allocating any handshake state.

### The Attack Without Cookies

```
Attacker                    Server
  |                            |
  |-- ClientHello              |
  |   src=victim_ip:port -----> Server allocates:
  |                            |  - Handshake context
  |-- ClientHello              |  - Certificate buffer
  |   src=victim_ip:port -----> |  - Timer
  |                            |  - Crypto state
  |-- (millions more) -------> MEMORY EXHAUSTED / CPU SATURATED
```

### Cookie Design Requirements (RFC 6347 §4.2.1)

1. **Stateless**: The server must be able to verify a cookie **without retaining any state** from the initial ClientHello.
2. **Unpredictable**: An attacker cannot forge a valid cookie without receiving the server's response (proving reachability).
3. **Time-bounded**: Cookies should expire to prevent replay.
4. **Covers client identity**: The cookie must be bound to the client's IP address and port.

### Recommended Cookie Construction

```
cookie = HMAC-SHA256(
    server_secret,
    client_ip || client_port || client_random || timestamp_epoch
)

Where:
  server_secret   = randomly generated at server startup, rotated periodically
  client_ip       = source IP address (4 or 16 bytes)
  client_port     = source port (2 bytes)
  client_random   = the Random field from the ClientHello
  timestamp_epoch = current time / cookie_lifetime (e.g., divide by 30 seconds)
```

### Cookie Verification

When the server receives a ClientHello with a cookie:

```
1. Recompute HMAC with current timestamp_epoch
2. If matches: ACCEPT — allocate handshake state
3. If not: Recompute HMAC with (current timestamp_epoch - 1)
            This handles the epoch boundary edge case where
            the cookie was issued just before the epoch rolled over
4. If still not: REJECT — send new HelloVerifyRequest
```

### Cookie Exchange Sequence (Detailed)

```
Client                          Network               Server
  |                                |                     |
  |---- UDP Datagram ------------->|-------------------> |
  |     DTLS Record (epoch=0):     |    epoch=0          |
  |       ContentType=22           |    seq=0            |
  |       Handshake:               |                     |
  |         Type=ClientHello       |    ┌───────────────┐|
  |         msg_seq=0              |    │ Compute cookie│|
  |         cookie = (empty)       |    │ from src IP,  │|
  |         cipher_suites=[...]    |    │ port, random  │|
  |         random=[28 bytes]      |    │ NO STATE SAVED│|
  |                                |    └───────┬───────┘|
  |                                |            │        |
  |<--- UDP Datagram --------------|<----------- |        |
  |     DTLS Record (epoch=0):                           |
  |       ContentType=22                                 |
  |       Handshake:                                     |
  |         Type=HelloVerifyRequest                      |
  |         msg_seq=0                                    |
  |         cookie=[32 bytes HMAC]                       |
  |                                                      |
  |---- UDP Datagram ------------------------------------> |
  |     DTLS Record (epoch=0):                           |
  |       ContentType=22                                 |
  |       Handshake:                                     |
  |         Type=ClientHello                             |
  |         msg_seq=1  [incremented!]                    |
  |         cookie=[32 bytes from server]  <-- ECHOED    |
  |         cipher_suites=[same as before]               |
  |         random=[SAME 28 bytes as before]             |
  |                                                      |
  |                    ┌─────────────────────────────┐   |
  |                    │ Verify cookie               │   |
  |                    │ Reachability proven!        │   |
  |                    │ NOW allocate handshake state│   |
  |                    └─────────────────────────────┘   |
  |                                                      |
  |<====== Full handshake proceeds from here ==========  |
```

### Cookie Size Limits

RFC 6347 requires that cookies be at most 255 bytes. In practice, a 32-byte HMAC-SHA256 output is common. Larger cookies reduce the benefit by increasing the size of the second ClientHello.

### Interaction with message_seq

Note that the second ClientHello has `message_seq = 1`, not 0. The RFC requires that message_seq be incremented even when retransmitting due to HelloVerifyRequest. This is because the second ClientHello is semantically a *new* message (it has the cookie field filled in), even though it's nominally the same handshake message type.

---

## 9. Retransmission and Reliability

### The Flight Concept

DTLS groups handshake messages into **flights** — logical groups that are sent together and acknowledged implicitly when the peer sends its next flight.

```
FLIGHT 1:  ClientHello (initial, no cookie)
FLIGHT 2:  HelloVerifyRequest
FLIGHT 3:  ClientHello (with cookie)
FLIGHT 4:  ServerHello + Certificate + ServerKeyExchange + ServerHelloDone
FLIGHT 5:  Certificate + ClientKeyExchange + CertificateVerify + CCS + Finished
FLIGHT 6:  CCS + Finished
```

### Implicit Acknowledgement

There are no explicit ACK messages in DTLS. A flight is implicitly acknowledged when the peer sends its next flight. For example:
- Client sends Flight 3 (ClientHello with cookie).
- Server starts sending Flight 4 (ServerHello etc.) — this implicitly ACKs Flight 3.
- If the client does not receive Flight 4 within the timeout, it retransmits Flight 3.

### Retransmission Timer (RFC 6347 §4.2.4)

DTLS uses a simple exponential backoff timer modeled loosely after TCP's RTO:

```
Initial timeout: 1 second (configurable, typically 1s)
On timeout: double the timeout (exponential backoff)
Maximum timeout: 60 seconds (configurable)

Pseudocode:
    timeout = INITIAL_TIMEOUT
    attempts = 0
    
    LOOP:
        send_current_flight()
        wait(timeout)
        
        if received_response:
            break
        
        attempts++
        if attempts > MAX_RETRANSMIT:
            fail("handshake timeout")
        
        timeout = min(timeout * 2, MAX_TIMEOUT)
```

### Timer State Machine

```
States:
  PREPARING   - Constructing the next flight
  SENDING     - Flight has been sent, timer running
  WAITING     - Waiting for response, timer running
  FINISHED    - Handshake complete
  ERRORED     - Unrecoverable failure

Transitions:
  PREPARING --[send flight]--> SENDING
  SENDING --[start timer]--> WAITING
  WAITING --[receive next flight]--> PREPARING (or FINISHED)
  WAITING --[timeout]--> SENDING (retransmit)
  SENDING --[too many retransmits]--> ERRORED
```

### Retransmission of Which Messages?

When retransmitting a flight, the sender retransmits **all** messages in that flight, not just the ones that may have been lost. This is because the sender has no way to know which individual datagrams (and hence which records within them) were lost. This is a simplification compared to TCP's selective acknowledgement.

```
Flight 4 (Server's turn) contains 4 messages:
  - ServerHello
  - Certificate
  - ServerKeyExchange
  - ServerHelloDone

If the client doesn't respond in time, the server retransmits
ALL FOUR messages, even if the client received some of them.

The client must handle receiving duplicate messages gracefully:
  - Use message_seq to deduplicate
  - A message already received and processed is simply dropped
```

### Handling Received Retransmissions

When an endpoint receives a retransmitted message it has already processed:

```
IF received message_seq <= last_processed_message_seq:
    IF we are in WAITING state (we sent a response):
        Retransmit our last flight (the peer didn't receive it)
    ELIF we are in SENDING/PREPARING state:
        Drop silently (we haven't sent a response yet)
```

This is the **retransmit-on-duplicate** behavior: receiving a duplicate of a previous flight means your response was lost, so retransmit it.

### Concrete Retransmission Example

```
Client                  Network               Server
  |                        |                     |
  |--Flight 3 (CHello) --->|  [DROPPED]          |
  |                        |                     |
  |     (timer fires,      |                     |
  |      1 second)         |                     |
  |                        |                     |
  |--Flight 3 (retx) ----->|-------------------> |
  |                        |                     |
  |<---Flight 4 (SHello)---|<------------------- |
  |<---Flight 4 (Cert) ----|<------------------- |
  |<---Flight 4 (SKE) -----|  [DROPPED]          |
  |<---Flight 4 (SHD) -----|<------------------- |
  |                        |                     |
  | Client receives SHello, Cert, SHD            |
  | but NOT ServerKeyExchange                    |
  | Client cannot complete processing of Flight 4|
  | until all messages arrive; timer fires       |
  |                        |                     |
  |--Flight 3 retx ------->|-------------------> | (server receives dup)
  |                        |                     |
  |                        |  Server is in       |
  |                        |  WAITING state,     |
  |                        |  retransmits Flight4|
  |                        |                     |
  |<---Flight 4 (all) -----|<------------------- | (all arrive this time)
  |                        |                     |
  | Client now has complete Flight 4             |
  |--Flight 5 ------------>|-------------------> |
```

---

## 10. Fragmentation and Reassembly

### Why Fragmentation is Necessary

TLS Certificate chains can be 4-8KB. TLS Certificate messages with intermediate CAs can easily exceed 16KB. A typical path MTU (PMTU) is:
- Ethernet: 1500 bytes IP payload
- IPv6 minimum: 1280 bytes
- VPN tunnels: often 1400 bytes or less (due to VPN overhead)

A DTLS record larger than the PMTU will be fragmented by IP. If **any** IP fragment is lost, the **entire UDP datagram** is dropped (UDP doesn't handle partial datagrams). This is far worse than TCP, which only needs to retransmit the lost segment.

**Therefore, DTLS implements fragmentation at the handshake message layer, above UDP.**

### Fragmentation Design

Each handshake message has a canonical `Length` (the full body size). When fragmented, the body is split into multiple pieces. Each piece is transmitted in a separate DTLS record, each containing a DTLS handshake message fragment header with the same `message_seq` but different `fragment_offset` and `fragment_length`.

```
Original Certificate Message (3000 bytes body):

message_seq=2, Length=3000

Fragment 1 (first 900 bytes):
  message_seq=2, fragment_offset=0, fragment_length=900
  [bytes 0-899 of certificate body]

Fragment 2 (next 900 bytes):
  message_seq=2, fragment_offset=900, fragment_length=900
  [bytes 900-1799 of certificate body]

Fragment 3 (last 1200 bytes):
  message_seq=2, fragment_offset=1800, fragment_length=1200
  [bytes 1800-2999 of certificate body]
```

### Fragment Size Selection

The implementation must choose fragment sizes such that each DTLS record fits within the PMTU:

```
max_fragment_size = PMTU
                  - IP_header (20 bytes IPv4, 40 bytes IPv6)
                  - UDP_header (8 bytes)
                  - DTLS_record_header (13 bytes)
                  - DTLS_handshake_header (12 bytes)
                  - AEAD_overhead (0-16 bytes, depending on cipher)

For IPv4, Ethernet PMTU (1500):
  max_fragment_size = 1500 - 20 - 8 - 13 - 12 = 1447 bytes
  (minus AEAD overhead if encrypted)
```

### Reassembly

The receiver must reassemble fragmented messages before processing them:

```
Reassembly State per (message_seq):
  - full_length: uint24 (from first fragment received)
  - received_ranges: sorted list of (offset, length) pairs
  - buffer: byte array of full_length bytes

For each received fragment:
  1. Extract message_seq, fragment_offset, fragment_length
  2. Allocate reassembly buffer if first fragment for this msg_seq
  3. Copy fragment data into buffer at fragment_offset
  4. Update received_ranges
  5. Check if received_ranges covers [0, full_length)
  6. If complete: process the full message; release buffer
```

### Non-Contiguous Fragment Handling

Fragments may arrive out of order:

```
Arrive:  Fragment at offset 900 (bytes 900-1799)
         Fragment at offset 0   (bytes 0-899)
         Fragment at offset 1800 (bytes 1800-2999)

received_ranges after each:
  After 1st: [(900, 900)]           -- gap: [0,900) and [1800,3000)
  After 2nd: [(0, 900), (900, 900)] -- can merge to [(0, 1800)]; gap: [1800, 3000)
  After 3rd: [(0, 3000)]            -- complete!
```

### Non-Fragmented Messages Can Arrive Fragmented Across Datagrams

Importantly, the DTLS spec allows implementations to send a single non-fragmented handshake message across multiple DTLS records, each sent in a separate datagram. While unusual, implementations must handle this.

### Fragment Reassembly Attacks

An attacker could:
1. **Flood with fake fragments**: Cause buffer exhaustion by sending many fake fragments for non-existent messages.
2. **Fragment overlap attacks**: Send overlapping fragments with conflicting data.

**Mitigations**:
- Limit total buffered fragments per connection.
- Limit total memory per in-progress reassembly.
- For overlapping fragments: RFC 6347 says implementations MUST NOT accept overlapping fragments with different data. If overlap with different data is detected, terminate with `illegal_parameter` alert.
- Only buffer fragments from the *current flight* being received, not arbitrary future messages.

---

## 11. Cipher Suites and Cryptography

### Cipher Suite Categories

DTLS 1.2 inherits TLS 1.2 cipher suites. The structure is:

```
CipherSuite = Key Exchange + Authentication + Cipher + MAC

Example: TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
          │      │         │              │
          │      │         │              └── PRF/HMAC hash
          │      │         └── Symmetric cipher + mode
          │      └── Server auth (cert type)
          └── Key exchange algorithm
```

### Recommended Cipher Suites for DTLS 1.2

**Mandatory to implement (RFC 6347):**
- `TLS_RSA_WITH_AES_128_CBC_SHA`

**Recommended (secure as of 2024):**
- `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256` ← prefer for IoT
- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384`
- `TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256` ← prefer for constrained devices

**Deprecated/Forbidden (do not use):**
- Anything with `NULL` cipher
- Anything with `RC4`
- Anything with `DES` or `3DES`
- Anything without PFS (RSA key exchange without ECDHE/DHE)
- `CBC` mode without Encrypt-then-MAC (`TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA` — vulnerable to Lucky13)

### AEAD Ciphers (Preferred)

AEAD (Authenticated Encryption with Associated Data) combines encryption and authentication in a single operation, with no separate MAC:

```
AES-128-GCM:
  Key:   128 bits
  Nonce: 96 bits (12 bytes) = 4-byte salt || 8-byte explicit nonce
  Tag:   128 bits (16 bytes)
  Max:   ~64GB per key (2^32 blocks)

AES-256-GCM:
  Key:   256 bits
  Same structure, higher security margin

ChaCha20-Poly1305:
  Key:   256 bits
  Nonce: 96 bits
  Tag:   128 bits
  Preferred when AES hardware acceleration unavailable
```

### Nonce Construction for DTLS 1.2 AEAD

```
For AES-128-GCM:
  implicit_nonce = write_key_material[key_length..key_length+4]  (4 bytes)
  explicit_nonce = epoch (2 bytes) || seq_num (6 bytes)           (8 bytes)
  
  nonce = implicit_nonce || explicit_nonce                         (12 bytes)
  
  The explicit_nonce is transmitted in the record (prepended to ciphertext).
  The receiver reconstructs from the record's epoch and seq_num.
```

Note: In TLS 1.3 / DTLS 1.3, the explicit nonce is removed. The nonce is derived entirely from the implicit write_iv XOR'd with the sequence number.

### CBC Mode (Legacy)

For `AES-128-CBC-SHA`:

```
Encryption:
  1. Generate random IV (16 bytes) — prepend to ciphertext
  2. HMAC-SHA1(MAC_write_key, seq_num || type || version || length || plaintext)
  3. Append MAC to plaintext
  4. Pad to block boundary
  5. Encrypt: CBC(write_key, IV, plaintext || MAC || padding)

Authentication:
  1. Decrypt
  2. Strip and verify padding
  3. Verify HMAC

DTLS-specific: use epoch || seq_num as the sequence number in MAC computation
```

**Lucky13 Attack on CBC**: Due to timing differences in MAC verification (more data to MAC when padding is stripped), an attacker can perform a padding oracle attack. Mitigated by constant-time MAC computation but still problematic. Prefer AEAD.

### Key Material Derivation

DTLS 1.2 uses the TLS 1.2 PRF (pseudorandom function):

```
PRF(secret, label, seed) = P_<hash>(secret, label || seed)

P_hash(secret, seed) = HMAC_hash(secret, A(1) || seed) ||
                        HMAC_hash(secret, A(2) || seed) || ...

A(0) = seed
A(i) = HMAC_hash(secret, A(i-1))

Key expansion:
key_block = PRF(master_secret,
                "key expansion",
                server_random || client_random)

Key block layout:
  client_write_MAC_key[mac_key_length]
  server_write_MAC_key[mac_key_length]
  client_write_key[enc_key_length]
  server_write_key[enc_key_length]
  client_write_IV[fixed_iv_length]    (AEAD only)
  server_write_IV[fixed_iv_length]    (AEAD only)
```

---

## 12. Alert Protocol

### Alert Record Format

```
Alert Record:

 0                   1
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| AlertLevel    | AlertDescription|
| (1 byte)      | (1 byte)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

AlertLevel:
  1 = warning
  2 = fatal
```

### Alert Handling in DTLS vs TLS

DTLS has additional concerns with alerts:

1. **Alerts may be lost**: Since UDP is unreliable, a fatal alert may never reach the peer.
2. **Alert replay**: An attacker could capture and replay a `close_notify` to terminate connections.
3. **No ordering guarantee**: An alert may arrive before the data it refers to.

**Best practice**: After sending a fatal alert, wait briefly for a response, then forcibly close the UDP socket. Do not rely on the peer receiving the alert.

### Alert Descriptions

| Value | Name | Meaning |
|---|---|---|
| 0 | close_notify | Orderly shutdown |
| 10 | unexpected_message | Protocol error |
| 20 | bad_record_mac | AEAD/MAC verification failed |
| 21 | decryption_failed | Decryption failed (deprecated in TLS 1.3) |
| 22 | record_overflow | Record too large |
| 40 | handshake_failure | No acceptable cipher suite |
| 42 | bad_certificate | Certificate invalid |
| 43 | unsupported_certificate | Certificate type not supported |
| 44 | certificate_revoked | Certificate revoked |
| 45 | certificate_expired | Certificate expired |
| 46 | certificate_unknown | Other certificate error |
| 47 | illegal_parameter | Protocol field has invalid value |
| 48 | unknown_ca | CA not trusted |
| 49 | access_denied | Certificate valid but no access |
| 50 | decode_error | Message cannot be decoded |
| 51 | decrypt_error | Handshake crypto operation failed |
| 70 | protocol_version | Version not supported |
| 71 | insufficient_security | Cipher suites too weak |
| 80 | internal_error | Server-side error |
| 86 | inappropriate_fallback | SCSV detected fallback |
| 90 | user_canceled | User cancelled |
| 100 | no_renegotiation | Renegotiation not allowed |
| 110 | unsupported_extension | Unrecognized extension |

### Alert Processing Rules

```
On receiving a fatal alert:
  1. Record the alert type (for logging/debugging)
  2. Immediately terminate the connection
  3. Do NOT send any more data
  4. Close the underlying socket

On receiving a warning alert:
  - close_notify: initiate clean shutdown
  - Other warnings: log and continue (implementation-defined)

On receiving an alert with invalid MAC (bad_record_mac decryption failure):
  SILENTLY DROP — do not send an alert in response
  (Sending "bad_record_mac" on bad MAC would enable padding oracle attacks)
```

---

## 13. Session Resumption

### Why Resumption Matters More for DTLS

The DTLS handshake adds 1-2 extra RTTs (cookie exchange) compared to TLS, making it 3-4 RTTs total for a full handshake. For latency-sensitive applications (IoT sensors reconnecting every few seconds, mobile clients switching networks), this is unacceptable.

Session resumption allows completing the secure channel in 1 RTT (using session IDs) or even 0 RTT (using session tickets).

### Session ID Resumption

```
Original Connection:
  Client                          Server
    |                                |
    |-- ClientHello (session_id=0)->  | (empty = new session)
    |<-- ServerHello (session_id=X)--  | (X = new session identifier)
    |... full handshake ...          |
    |                                | Server caches:
    |                                |   session_id=X → master_secret, cipher, etc.

Resumed Connection (1 RTT after cookie exchange):
  Client                          Server
    |                                |
    |-- ClientHello (session_id=X)-> | (non-empty = resumption request)
    |                                |
    |<-- ServerHello (session_id=X)-- | (Server agrees to resume)
    |<-- [ChangeCipherSpec] ---------  |
    |<-- Finished (encrypted) -------  |
    |                                |
    |-- [ChangeCipherSpec] --------->  |
    |-- Finished (encrypted) ------->  |
    |                                |
    |====== Application Data ======  | Full handshake skipped!
```

With the cookie exchange: 2 RTT total (1 for cookie, 1 for resumed handshake). Without: 1 RTT.

### Session Ticket Resumption (RFC 5077)

Session tickets move the session state storage from the server to the client (encrypted by the server's ticket key):

```
Original Connection ends:
  Server sends NewSessionTicket message containing:
    encrypted_state = AES-128-CBC(ticket_key, {master_secret, cipher_suite,
                                                client_identity, expiry})
    + HMAC-SHA256(hmac_key, encrypted_state)

Client stores the opaque ticket blob.

Resumed Connection:
  Client                          Server
    |                                |
    |-- ClientHello                ->  |
    |     SessionTicket extension:    |
    |     [encrypted ticket blob]     |
    |                                |
    |<-- ServerHello -----------------  |
    |      (no session_id = accepted)  |
    |<-- NewSessionTicket ------------  | (optional: new ticket)
    |<-- CCS + Finished --------------  |
    |                                |
    |-- CCS + Finished ------------->  |
    |                                |
    |====== Application Data ======  |
```

**Security concern**: The ticket key is a long-term server secret. If it's compromised, an attacker can decrypt all past sessions (no PFS for session tickets). Rotate ticket keys frequently (every 24h recommended).

### DTLS-Specific Resumption Considerations

- Session IDs and tickets can be reused across IP address changes (e.g., client roaming between networks) — but only if the cookie mechanism is used to verify the new address.
- DTLS 1.3 uses PSK (pre-shared key) from NewSessionTicket for resumption, eliminating explicit session ID/ticket mechanisms.

---

## 14. DTLS 1.3

### Overview

DTLS 1.3 (RFC 9147, published April 2022) is a port of TLS 1.3 to datagram transports. It is **not** backward compatible with DTLS 1.2.

### What TLS 1.3 Changed (Relevant to DTLS)

- All public-key operations moved to extensions (KeyShare).
- No more CBC cipher suites; only AEAD.
- No more RSA key exchange; only (EC)DHE or PSK.
- Handshake is encrypted earlier (after ServerHello, keys are available).
- Session resumption uses PSK from NewSessionTicket only (no session IDs).
- 0-RTT (early data) is supported.
- Renegotiation replaced by KeyUpdate.
- ChangeCipherSpec message still exists for middlebox compatibility but is ignored.

### DTLS 1.3 Record Format

DTLS 1.3 introduces a **new, shorter record format** because:
- The content type is usually `application_data` (most records encrypted).
- The version field is fixed (always `0xFEFC`).
- Sequence numbers can be short in steady state.

**Unified Header (encrypted records):**

```
DTLS 1.3 Unified Header (for encrypted records):

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+
|0|0|1|C|S|L|E E|    First byte: Unified Header marker bits
+-+-+-+-+-+-+-+-+
(optional Connection ID, if C=1)
(optional: Sequence number, 8 or 16 bits, if S=0→8bit, S=1→16bit)
(optional: Length field, 16 bits, if L=1)
(mandatory: Epoch (low 2 bits), indicated by E field)

Followed by encrypted data + AEAD tag.
```

**Fixed Header Bit Fields (first byte):**

```
Bit 7: 0 (fixed, identifies DTLS 1.3 unified header vs DTLS 1.2 record)
Bit 6: 0 (fixed)
Bit 5: 1 (fixed, distinguishes from short vs long headers)
Bit 4: C — Connection ID present (1=yes)
Bit 3: S — Sequence number length (0=8-bit, 1=16-bit)
Bit 2: L — Length field present (0=no, 1=yes)
Bits 1-0: E — Low 2 bits of epoch
```

**For cleartext records (handshake before keys are established), DTLS 1.3 still uses the old 13-byte DTLS 1.2 record format but with version `0xFEFC`.**

### DTLS 1.3 Handshake

```
Client                                          Server
  |                                                |
  |=== FLIGHT 1 ================================>  |
  |--- ClientHello --------------------------------> |
  |    (version negotiation via supported_versions) |
  |    (key_share extension with ECDHE keys)        |
  |    (cookie extension if server requested it)    |
  |                                                |
  |                    IF FIRST CONNECTION (no cookie):
  |<== FLIGHT 1.5 ================================  |
  |<-- HelloRetryRequest (with cookie) ----------  |
  |                                                |
  |=== FLIGHT 2 (if cookie needed) ============>  |
  |--- ClientHello (with cookie extension) ------> |
  |                                                |
  |<== FLIGHT 2/3 ================================  |
  |<-- ServerHello --------------------------------  |  ← Keys derived here!
  |<-- {EncryptedExtensions} ---------------------  |  ← Encrypted with
  |<-- {CertificateRequest} (optional) -----------  |    handshake keys
  |<-- {Certificate} -----------------------------  |
  |<-- {CertificateVerify} -----------------------  |
  |<-- {Finished} --------------------------------  |
  |                                                |
  |=== FLIGHT 3/4 ==============================>  |
  |--- {Certificate} (if requested) ------------->  |
  |--- {CertificateVerify} (if cert sent) ------->  |
  |--- {Finished} --------------------------------> |  ← Client sends Finished
  |                                                |
  |<=== [NewSessionTicket] (async) ===============  |
  |                                                |
  |====== [Application Data] (encrypted) ========  |
```

**Key change**: In DTLS 1.3, the cookie is carried in a **HelloRetryRequest** message (not a HelloVerifyRequest), and the cookie lives in the `cookie` extension within ClientHello (not the legacy cookie field).

### DTLS 1.3 Sequence Number Encryption

DTLS 1.3 adds **sequence number encryption** to prevent traffic analysis based on sequence numbers:

```
The sequence number in the record header is encrypted using a
derived key (sn_key) and the ciphertext itself as a mask source.

Receiver:
  1. Read the ciphertext (without knowing seq#)
  2. Derive mask = sn_mask(sn_key, first_N_bytes_of_ciphertext)
  3. seq_num = encrypted_seq_num XOR mask[0:seq_num_length]
  4. Reconstruct full seq_num using sliding window
  5. Verify AEAD with reconstructed seq_num as nonce component

This hides seq_nums from passive observers, preventing:
  - Traffic analysis (which flow has high loss rates)
  - Correlation attacks across NAT rebindings
```

### DTLS 1.3 ACK Message

DTLS 1.3 introduces an explicit **ACK message** (ContentType = 26) for acknowledging handshake records. This replaces the implicit flight acknowledgement of DTLS 1.2.

```
ACK Message:
  record_numbers: list of (epoch, seq_num) pairs
  
  Semantics: "I have received these specific records."
  
  Sent by:
    - Client after receiving server's handshake messages
    - Server after receiving client's Finished
    - Either side for post-handshake messages
```

This allows selective retransmission: instead of retransmitting the entire flight, retransmit only the specific records not acknowledged.

### DTLS 1.3 Epoch Semantics

```
Epoch 0:  Cleartext (initial ClientHello, HelloRetryRequest)
Epoch 1:  Unused (for middlebox compatibility)  
Epoch 2:  Handshake keys (EncryptedExtensions through Finished)
Epoch 3:  Application data keys
Epoch 4+: Post-handshake key updates (KeyUpdate)
```

### 0-RTT (Early Data) in DTLS 1.3

When resuming with a session ticket (PSK), the client can send application data in the very first flight, before the handshake is complete:

```
Client                                          Server
  |                                                |
  |--- ClientHello ---------------------------->   |
  |     early_data extension                       |
  |     psk extension (session ticket)             |
  |                                                |
  |--- [0-RTT data] (encrypted with PSK) ------>  |
  |                                                |
  |<-- ServerHello ----------------------------    |
  |<-- {EncryptedExtensions} -----------------    |
  |<-- {Finished} ----------------------------    |
  |                                                |
  |--- {EndOfEarlyData} --------------------->    |
  |--- {Finished} ---------------------------->    |
  |                                                |
```

**0-RTT Security Warning**: 0-RTT data is **not forward-secret** and is **replayable**. An attacker who captures a 0-RTT datagram can replay it to the server. Only use 0-RTT for **idempotent** requests. Applications must handle replay at the application layer.

---

## 15. Connection ID Extension (RFC 9146)

### The NAT Rebinding Problem

UDP connections have no inherent identity. They are identified by the 4-tuple: `(src_ip, src_port, dst_ip, dst_port)`. When a mobile client moves from Wi-Fi to cellular:
- The client's IP changes.
- From the server's perspective, the old DTLS session is dead.
- The client must perform a full new DTLS handshake.

For long-lived DTLS sessions (IoT devices, VPNs), this is wasteful and disruptive.

### Connection ID Concept

The Connection ID (CID) extension assigns a short opaque identifier to a DTLS session. This identifier is:
- Chosen by the receiver (the entity that will use it to demultiplex incoming records).
- Included in every record header.
- Independent of the IP/port 4-tuple.

```
With Connection ID:
  Server assigns CID "0xABCD" to the client's session.
  Client includes "0xABCD" in every record it sends to the server.
  
  When client's IP changes (NAT rebind):
    New record arrives from 203.0.113.5:44321 (new address)
    Server reads CID "0xABCD" from record
    Server looks up: CID 0xABCD → session for original_client
    Server verifies the record's MAC (still uses same session keys)
    Server continues the session, updating the client's remote address
```

### CID Record Format (RFC 9146)

DTLS 1.2 with CID uses a new ContentType: `tls12_cid = 25`.

```
DTLS 1.2 + CID Record:

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    25 (CID)   |   Version (0xFEFD)            |               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+               |
|      Epoch            |   Sequence Number (48 bits)           |
+                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |       Length (uint16)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Connection ID (variable length, negotiated)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Encrypted Payload (includes actual ContentType at end)  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

The actual ContentType is the last byte of the plaintext payload.
This is called "content type confusion protection" — the wire type
is always 25 (tls12_cid), hiding whether it's handshake or data.
```

### CID Negotiation

```
ClientHello extension:
  extension_type = connection_id (54)
  client_cid: opaque<0..2^8-1>  
    -- The CID the client wants the server to use when sending to it.
    -- Empty means "I support CID but don't want to receive CID now"

ServerHello extension:
  extension_type = connection_id (54)  
  server_cid: opaque<0..2^8-1>
    -- The CID the server wants the client to use when sending to it.
    -- Empty means "I support CID but don't want to receive CID now"

After negotiation:
  - Client includes server_cid in every record it sends
  - Server includes client_cid in every record it sends
  - Each side independently decides its own receive CID
```

### CID and AEAD

The CID is included in the Additional Data (AD) used for AEAD:

```
AD for DTLS 1.2 + CID:
  epoch || seq_num || tls12_cid || version || cid || cid_length ||
  length_of_DTLSInnerPlaintext

(vs regular DTLS 1.2 AEAD AD: epoch || seq_num || type || version || length)
```

Including the CID in the AD ensures that an attacker cannot redirect a record from one CID session to another (the MAC would fail).

### CID in DTLS 1.3

DTLS 1.3 integrates CID natively into the unified record header (the `C` bit in the first byte). See Section 14.

---

## 16. PMTU Discovery and Handling

### Why PMTU Matters for DTLS

IP fragmentation is harmful for DTLS:
1. If any IP fragment is lost, the whole UDP datagram is dropped.
2. IP fragmentation can be blocked by firewalls.
3. Fragment reassembly adds latency and memory usage.
4. An attacker can inject fake fragments (fragmentation attacks).

**The goal**: Send DTLS records that fit within the path MTU without IP fragmentation.

### PMTU Values

```
Common PMTU values:
  Ethernet:           1500 bytes (IP payload including IP header)
  PPPoE:              1492 bytes
  IPv6 minimum:       1280 bytes
  VPN (IPSec/UDP):   ~1400 bytes
  Tunnel overhead:   ~1370 bytes (depending on tunnel type)
  
  "Safe" default:    1200 bytes IP payload (conservative for all networks)
  
  Calculation:
    Available for DTLS payload = PMTU - IP_hdr - UDP_hdr - DTLS_record_hdr
    IPv4: PMTU - 20 - 8 - 13 = PMTU - 41
    IPv6: PMTU - 40 - 8 - 13 = PMTU - 61
```

### PMTU Discovery Methods

**Method 1: ICMP-based (RFC 1191 / RFC 1981)**

Set the Don't Fragment (DF) bit on IPv4 packets. If a packet is too large for an intermediate router, the router returns an ICMP "Fragmentation Needed" message indicating the next-hop MTU. Use this MTU for subsequent packets.

```
Problems:
  - Many networks block ICMP → Black hole
  - ICMP comes from intermediate router, not from peer → Attribution
  - Race condition: multiple large packets in flight simultaneously
```

**Method 2: Packetization Layer PMTU Discovery (RFC 4821)**

Binary search or probe approach: Start with a large packet and reduce until it succeeds.

```
Algorithm:
  1. Start with current best guess for PMTU (e.g., 1400)
  2. Send probes of this size periodically
  3. If probe is acknowledged (via DTLS ACK or implicit):
       Update PMTU estimate upward
  4. If probe is lost (timeout without response):
       Could be PMTU exceeded or plain packet loss
       Reduce PMTU estimate
  5. Periodically attempt larger probes to detect PMTU increases
     (path may change and become capable of larger packets)
```

**Method 3: Conservative default**

Use 1200 bytes as the maximum datagram size. This is below virtually all real-world PMTUs and avoids IP fragmentation on all common paths. Cost: ~15-20% lower efficiency.

### DTLS Interaction with PMTU

During the handshake, DTLS MUST fragment handshake messages to fit within the PMTU estimate. The handshake is also the ideal time to probe for PMTU:

```
1. Start handshake with conservative PMTU estimate (1200 bytes).
2. After handshake succeeds, start sending application data.
3. Gradually increase record size to probe for larger PMTU.
4. If loss is detected that correlates with larger packet sizes, reduce.
5. Periodically (every 10 minutes) attempt a larger probe again.
```

### Reacting to PMTU Reduction

If the PMTU decreases mid-session (route change):

```
Large records may now be dropped (lost from the app's perspective).
The DTLS layer sees this as packet loss.
The application should shrink its write chunk size.
DTLS should reduce its maximum record size.
```

---

## 17. Replay Protection

### The Replay Attack

An attacker captures a legitimate DTLS record and retransmits it later. Without replay protection:
- A captured `buy 1000 shares` command could be replayed.
- A captured authentication response could be replayed.

### DTLS Replay Window

DTLS uses a sliding window to track which sequence numbers have been received and processed:

```
Sliding Window Design:

Window size: 64 bits (standard) or larger (implementation choice)

State per epoch:
  - highest_received_seq: the highest seq_num seen so far
  - window: 64-bit bitmask

  Window bit[i] = 1 means seq_num (highest_received_seq - i) was received.
  Window bit[0] = highest_received_seq itself.

Acceptance rules for incoming record with seq_num S:

  IF S > highest_received_seq:
    // New sequence number, ahead of window
    Slide the window: shift left by (S - highest_received_seq) bits
    Mark bit[0] = 1
    Update highest_received_seq = S
    ACCEPT

  ELIF S == highest_received_seq:
    // Exact duplicate of highest
    REJECT (replay)

  ELIF S < highest_received_seq - WINDOW_SIZE:
    // Too old, before our window
    REJECT (too old)

  ELIF window bit [(highest_received_seq - S)] == 1:
    // Already received
    REJECT (replay)

  ELSE:
    // Within window, not yet seen
    Set window bit [(highest_received_seq - S)] = 1
    ACCEPT
```

### Replay Window Diagram

```
Sequence numbers: ...42  43  44  45  46  47  48  49  50
                                                      ^
                                          highest_received = 50

Window (64 bits):
  bit 0 → seq 50 (received: 1)
  bit 1 → seq 49 (received: 1)
  bit 2 → seq 48 (received: 0) ← lost or not yet arrived
  bit 3 → seq 47 (received: 1)
  ...
  bit 63 → seq (50-63) = seq -13 (received: irrelevant)

Arriving packet with seq=48:
  48 < 50 → within window check
  bit 2 = 0 → NOT yet received
  → ACCEPT, set bit 2 = 1

Arriving packet with seq=48 again:
  bit 2 = 1 → already received
  → REJECT (replay)

Arriving packet with seq=51:
  51 > 50 → slide window left 1 bit
  new highest = 51, bit 0 = 1 (seq 51)
  (bit 1 now represents seq 50, which was received → still 1)
  → ACCEPT
```

### Replay Protection and Retransmission

DTLS's own retransmission mechanism may cause the receiver to see duplicate records. This is handled by the replay window: a retransmitted record with the same sequence number is silently dropped after the first processing.

**Important**: The replay window check occurs **before** AEAD decryption. This is correct because:
1. It saves CPU (no decryption attempt for obvious replays).
2. An attacker could flood with sequence numbers in the window — but they'd all need valid AEAD tags to actually be replays, and forging AEAD tags is computationally infeasible.

The downside: an attacker can cause denial of selective packets by sending fake records with valid-looking seq#s (but invalid AEAD tags). These will pass the window check, consume a slot in the window, and cause real retransmissions of those seq#s to be dropped as "replays". This is considered acceptable.

---

## 18. SRTP and WebRTC Integration

### Overview

WebRTC uses DTLS in two ways:
1. **DTLS-SRTP**: Negotiate SRTP keys using DTLS, then use SRTP (not DTLS) for actual media encryption.
2. **DTLS over SCTP**: Encrypt SCTP data channels using DTLS for arbitrary data transfer.

### DTLS-SRTP (RFC 5764)

The motivation: SRTP is a purpose-built protocol for encrypted RTP (real-time media). It has lower per-packet overhead than DTLS-protected data because it uses pre-allocated header extensions and shorter authentication tags. But SRTP needs keys. DTLS provides the key exchange.

```
Design:
  1. DTLS handshake establishes shared keying material.
  2. DTLS does NOT encrypt the media packets.
  3. DTLS keying material is exported using TLS Exporter (RFC 5705).
  4. SRTP sessions are initialized with the exported keys.
  5. Media flows as SRTP/SRTCP packets (not DTLS records).

Result:
  - DTLS provides key exchange security (authentication, PFS)
  - SRTP provides efficient media encryption with minimal overhead
```

### SRTP Key Export

```
TLS Exporter (RFC 5705):
  exported_material = PRF(master_secret,
                          label,
                          client_random || server_random,
                          length)

For DTLS-SRTP (RFC 5764):
  label = "EXTRACTOR-dtls_srtp"
  length = 2 * (srtp_key_length + srtp_salt_length)

Output layout:
  client_write_SRTP_master_key[srtp_key_length]   = 16 bytes (AES-128)
  server_write_SRTP_master_key[srtp_key_length]   = 16 bytes
  client_write_SRTP_master_salt[srtp_salt_length] = 14 bytes
  server_write_SRTP_master_salt[srtp_salt_length] = 14 bytes
```

### use_srtp Extension

During the DTLS handshake, both sides signal which SRTP profiles they support via the `use_srtp` extension:

```
ClientHello extension:
  use_srtp:
    SRTPProtectionProfiles:
      SRTP_AES128_CM_HMAC_SHA1_80  = {0x00, 0x01}  (most common)
      SRTP_AES128_CM_HMAC_SHA1_32  = {0x00, 0x02}
      SRTP_NULL_HMAC_SHA1_80       = {0x00, 0x05}  (no encryption, just auth)
      SRTP_AEAD_AES_128_GCM        = {0x00, 0x07}  (preferred, RFC 7714)
      SRTP_AEAD_AES_256_GCM        = {0x00, 0x08}

ServerHello extension:
  use_srtp:
    Exactly one SRTPProtectionProfile (the chosen one)
```

### WebRTC DTLS Roles

In WebRTC, each peer connection has a DTLS role:
- **Active** (client): Initiates the DTLS handshake.
- **Passive** (server): Responds to the DTLS handshake.
- **Actpass**: Can do either.

The roles are negotiated in SDP:
```
a=setup:actpass   → can be active or passive
a=setup:active    → will be active (client)
a=setup:passive   → will be passive (server)
a=setup:holdconn  → suspend connection
```

When `actpass` is offered, the answerer picks the role. Typically:
- Offerer: actpass
- Answerer: active (becomes the DTLS client)

### Certificate Fingerprinting

In WebRTC, DTLS certificates are self-signed. The browser's WebRTC stack generates a per-session (or per-browser) certificate. Authentication is provided not by a CA chain but by **fingerprint matching**:

```
SDP offer/answer exchange (out-of-band via signaling):
  a=fingerprint:sha-256 AB:CD:EF:...  (hash of the DTLS certificate)

DTLS handshake:
  The peer presents its certificate.
  We verify: SHA-256(peer_certificate) == fingerprint from SDP
  
  This proves: the entity doing DTLS is the same entity we
  negotiated with via signaling (which may be authenticated
  by the WebRTC application's own auth mechanism).
```

### ICE + DTLS Flow

```
1. ICE (Interactive Connectivity Establishment):
   - Discover IP addresses (host, srflx, relay candidates)
   - Perform connectivity checks (STUN BINDING requests/responses)
   - Select best candidate pair (e.g., direct UDP path)

2. ICE completes: selected path is known

3. DTLS handshake over ICE-established UDP path:
   - STUN and DTLS records may arrive on the same UDP 5-tuple
   - Demultiplex by packet content:
     * DTLS: first byte is 20-63 (ContentType)
     * STUN: first two bits are 00
     * SRTP/RTP: first byte >= 128 (has RTP version=2)
     * SRTCP: RTP payload type = 200-204

4. DTLS handshake (DTLS-SRTP extension negotiated)

5. Keys exported via TLS Exporter

6. SRTP/SRTCP sessions initialized

7. Media flows as SRTP/SRTCP
   SCTP data channels flow as DTLS-over-SCTP (separate DTLS session)
```

### Packet Demultiplexing at the UDP Level

```
Incoming UDP datagram:

First byte value:
  0-3   → STUN (first 2 bits = 00)
  20-63 → DTLS (ContentType range)
        → 20: change_cipher_spec
        → 21: alert
        → 22: handshake
        → 23: application_data
        → 24: heartbeat
  64-79 → TURN channel data
  128-191 → RTP (version=2, M=0/1, PT=0-127)
  192-223 → RTCP (version=2, M=0/1, PT=128-223)
```

---

## 19. State Machine — Complete

### DTLS 1.2 Server State Machine

```
                    START
                      │
                      ▼
            ┌─────────────────┐
            │    IDLE         │  Waiting for ClientHello
            └────────┬────────┘
                     │  Receive ClientHello (no cookie or invalid)
                     ▼
            ┌─────────────────────┐
            │  COOKIE_WAIT        │  Send HelloVerifyRequest
            └────────┬────────────┘
                     │  Receive ClientHello (valid cookie)
                     ▼
            ┌─────────────────────┐
            │  SERVER_HELLO       │  Send: ServerHello
            │                     │        Certificate
            │                     │        ServerKeyExchange
            │                     │        (CertificateRequest)
            │                     │        ServerHelloDone
            └────────┬────────────┘
                     │  Waiting for client's flight
                     ▼
            ┌─────────────────────┐
            │  CLIENT_KEY_EXCHANGE│  Receive: Certificate (if requested)
            │                     │           ClientKeyExchange
            │                     │           CertificateVerify
            │                     │           CCS
            │                     │           Finished
            └────────┬────────────┘
                     │  Verify Finished
                     ▼
            ┌─────────────────────┐
            │  SERVER_FINISHED    │  Send: CCS + Finished
            └────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │  ESTABLISHED        │  Application data flows
            └────────┬────────────┘
                     │  close_notify or fatal alert
                     ▼
            ┌─────────────────────┐
            │  CLOSED             │
            └─────────────────────┘

On any fatal error → send fatal alert → go to CLOSED
On timeout in any state → retransmit last flight → if max retransmits exceeded → CLOSED
```

### DTLS 1.2 Client State Machine

```
                    START
                      │
                      ▼
            ┌─────────────────────┐
            │  CLIENT_HELLO       │  Send: ClientHello (empty cookie)
            └────────┬────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
  HelloVerifyRequest      ServerHello
  received                received
          │                     │
          ▼                     │
  ┌──────────────────┐          │
  │ CLIENT_HELLO_2   │          │
  │ Send ClientHello │          │
  │ (with cookie)    │          │
  └────────┬─────────┘          │
           │                    │
           └──────────┬─────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ SERVER_HELLO_WAIT   │  Receive: ServerHello
            │                     │           Certificate
            │                     │           ServerKeyExchange
            │                     │           ServerHelloDone
            └────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ CLIENT_KEY_EXCHANGE │  Send: (Certificate if requested)
            │                     │        ClientKeyExchange
            │                     │        (CertificateVerify)
            │                     │        CCS + Finished
            └────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ SERVER_FINISHED_WAIT│  Receive: CCS + Finished from server
            └────────┬────────────┘
                     │  Verify server Finished
                     ▼
            ┌─────────────────────┐
            │  ESTABLISHED        │  Application data flows
            └────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │  CLOSED             │
            └─────────────────────┘
```

### Handshake Retransmission State (Both Sides)

```
SENDING ──────── timer_start ──────────► WAITING
   ▲                                         │
   │                               ┌─────────┴─────────┐
   │                               │                   │
   │                          timeout          receive_next_flight
   │                               │                   │
   └── retransmit_flight ──────────┘          PREPARING/FINISHED
```

---

## 20. Security Analysis and Threat Model

### DTLS Security Goals

1. **Confidentiality**: Encrypted payload not readable by passive observers.
2. **Integrity**: Modified records are detected and dropped.
3. **Authentication**: Both endpoints authenticated (mutually or server-only).
4. **Replay protection**: Captured records cannot be replayed later.
5. **DoS resistance**: The cookie mechanism prevents state exhaustion.

### Threat Model

```
Adversary capabilities:
  - PASSIVE: Can observe all traffic on the path
  - ACTIVE: Can inject, modify, drop, delay, reorder packets
  - OFF-PATH: Can send packets with spoofed source addresses

What DTLS protects against:
  ✅ Passive eavesdropping (confidentiality)
  ✅ Active injection (integrity via AEAD)
  ✅ Record modification (integrity)
  ✅ Replay attacks (sliding window)
  ✅ Spoofed source IP (cookie exchange proves reachability)
  ✅ Downgrade attacks (cipher suite negotiation in Finished hash)
  ✅ Certificate substitution (Finished hash covers ServerCertificate)
  
What DTLS does NOT protect against:
  ❌ Denial of Service via packet dropping (attacker can drop all UDP)
  ❌ Traffic analysis (volume, timing, packet sizes visible in 1.2)
      → DTLS 1.3 mitigates with seq# encryption and content type hiding
  ❌ Endpoint compromise (implementation bugs, key leakage)
  ❌ Side-channel attacks (timing-based on implementation)
```

### Attack Vectors

#### 1. Cookie Forgery

**Attack**: Attacker forges a cookie without access to the server secret.  
**Difficulty**: Requires breaking HMAC-SHA256 → computationally infeasible.  
**Mitigation**: Use a strong random server secret; rotate frequently.

#### 2. Cookie Replay

**Attack**: Attacker observes a valid ClientHello (with cookie) and replays it.  
**Problem**: The replayed ClientHello has the same client random. The server would start a new handshake.  
**Mitigation**: The cookie includes `client_random`. A replayed ClientHello has the original client_random. When the server processes the Cookie-verified ClientHello, the subsequent handshake includes a Finished message that authenticates the entire transcript. An attacker replaying a ClientHello cannot complete the handshake without the client's private key. The Finished message cannot be forged.

#### 3. Fragmentation Bomb

**Attack**: Send thousands of fake handshake fragments with large `Length` values.  
**Defense**: Limit memory allocation per connection during reassembly. Drop connections that allocate excessive fragment buffer memory.

#### 4. Record Flooding / Replay Window Poisoning

**Attack**: Send UDP datagrams with valid-looking DTLS record headers (but invalid AEAD tags) and sequence numbers within the receiver's window. The receiver checks the window, sees seq# as fresh, updates the window, then fails AEAD verification and discards. Real packets with those seq# now look like replays.  
**Impact**: Can suppress reception of specific records, but the retransmission mechanism will eventually recover.  
**Mitigation**: Rate-limit records from unexpected sources; use Connection ID to verify source.

#### 5. Lucky13 / BEAST (CBC Mode)

**Attack**: Timing oracle attacks against CBC-mode decryption.  
**Mitigation**: Use AEAD ciphers exclusively. If CBC must be used: implement constant-time MAC verification (compare MAC in constant time regardless of padding validity).

#### 6. DTLS Stripping

**Attack**: A network middlebox strips DTLS and presents plaintext.  
**Context**: Only possible if the application doesn't enforce DTLS (i.e., accepts both DTLS and plaintext).  
**Mitigation**: Always require DTLS. For WebRTC: the SDP fingerprint mechanism prevents stripping without detection.

#### 7. Handshake Downgrade

**Attack**: Remove strong cipher suites from ClientHello.  
**Mitigation**: The Finished message is a MAC over the entire handshake transcript (including ClientHello). If the client's real ClientHello offered AES-GCM but the attacker modified it to offer only 3DES, the Finished verification will fail (the server's hash of the manipulated transcript won't match the client's hash of the real transcript).

#### 8. Renegotiation Attack (DTLS 1.2)

**Attack**: Inject malicious handshake data before a legitimate renegotiation.  
**Mitigation**: The Renegotiation Info extension (RFC 5746). Implementations MUST implement it. DTLS 1.3 removes renegotiation entirely.

### DTLS vs IPSec Security Comparison

```
Property                    DTLS            IPSec (ESP)
───────────────────────────────────────────────────────
OSI Layer                   Application(7)  Network(3)
User-space deployable       ✅              ❌ (kernel)
NAT traversal               ✅ (natural)    ✅ (with NAT-T)
Per-application control     ✅              ❌
Overhead per packet         13-29 bytes     30-50+ bytes
Key exchange                TLS handshake   IKEv2
Certificate-based auth      ✅              ✅
PSK support                 ✅              ✅
Forward secrecy             ✅ (with ECDHE) ✅ (with DH)
Traffic analysis resistance Low (1.2)       Medium
DoS resistance              Cookie          IKEv2 puzzles
```

---

## 21. Implementation Guide (Rust + Go)

### Rust: Using `webrtc-rs` / `rustls` for DTLS

The primary Rust DTLS library is `dtls` from the `webrtc-rs` project. For lower-level work, OpenSSL bindings or `rustls` (TLS only, no DTLS yet) are alternatives.

**File: `Cargo.toml`**
```toml
[package]
name = "dtls-example"
version = "0.1.0"
edition = "2021"

[dependencies]
webrtc-dtls = "0.9"
webrtc-util = "0.9"
tokio = { version = "1", features = ["full"] }
anyhow = "1"
bytes = "1"
rcgen = "0.12"           # Self-signed certificate generation
rustls = "0.23"
```

**File: `src/server.rs`**
```rust
use std::sync::Arc;
use std::net::SocketAddr;
use webrtc_dtls::config::{Config, ExtendedMasterSecretType, ClientAuthType};
use webrtc_dtls::conn::DTLSConn;
use webrtc_dtls::crypto::{Certificate, CryptoPrivateKey};
use webrtc_dtls::listener::listen;

/// Generate a self-signed certificate for testing.
fn generate_self_signed_cert() -> anyhow::Result<Certificate> {
    let rcgen_cert = rcgen::generate_simple_self_signed(vec!["localhost".to_string()])?;
    let cert_pem = rcgen_cert.serialize_pem()?;
    let key_pem = rcgen_cert.serialize_private_key_pem();
    
    let cert = Certificate::from_pem(&cert_pem, &key_pem)?;
    Ok(cert)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let addr: SocketAddr = "0.0.0.0:4444".parse()?;
    
    let cert = generate_self_signed_cert()?;
    
    let config = Config {
        // Present our certificate
        certificates: vec![cert],
        
        // Server: verify client certificates (mutual TLS)
        // For server-only auth, use ClientAuthType::NoClientCert
        client_auth: ClientAuthType::RequireAnyClientCert,
        
        // Require extended master secret (RFC 7627)
        // Prevents triple handshake attacks
        extended_master_secret: ExtendedMasterSecretType::Require,
        
        // SRTP profiles if doing WebRTC media
        srtp_protection_profiles: vec![],
        
        // Insecure skip verify: for testing only, NEVER production
        insecure_skip_verify: false,
        
        ..Default::default()
    };
    
    println!("DTLS server listening on {addr}");
    let listener = listen(addr, config).await?;
    
    loop {
        let (conn, remote_addr) = listener.accept().await?;
        
        tokio::spawn(async move {
            if let Err(e) = handle_connection(conn, remote_addr).await {
                eprintln!("Connection error from {remote_addr}: {e}");
            }
        });
    }
}

async fn handle_connection(
    conn: Arc<DTLSConn>,
    remote_addr: SocketAddr,
) -> anyhow::Result<()> {
    println!("New DTLS connection from {remote_addr}");
    
    // Print negotiated cipher suite and protocol version
    let state = conn.connection_state().await;
    println!("  Cipher suite: {:?}", state.cipher_suite_id);
    
    // Echo loop
    let mut buf = vec![0u8; 8192];
    loop {
        let n = conn.read(&mut buf, None).await?;
        if n == 0 {
            break;
        }
        
        let msg = &buf[..n];
        println!("  Received {} bytes: {:?}", n, 
                 std::str::from_utf8(msg).unwrap_or("<binary>"));
        
        // Echo back
        conn.write(msg, None).await?;
    }
    
    println!("Connection from {remote_addr} closed");
    conn.close().await?;
    Ok(())
}
```

**File: `src/client.rs`**
```rust
use std::net::SocketAddr;
use std::sync::Arc;
use webrtc_dtls::config::{Config, ExtendedMasterSecretType};
use webrtc_dtls::conn::DTLSConn;
use webrtc_dtls::dial::dial;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let server_addr: SocketAddr = "127.0.0.1:4444".parse()?;
    
    let config = Config {
        // For testing with self-signed certs
        insecure_skip_verify: true,
        
        extended_master_secret: ExtendedMasterSecretType::Require,
        
        ..Default::default()
    };
    
    println!("Connecting to DTLS server at {server_addr}");
    let conn = dial("udp", server_addr, config).await?;
    
    // Send messages
    for i in 0..5 {
        let msg = format!("Hello DTLS, message #{i}");
        conn.write(msg.as_bytes(), None).await?;
        
        let mut buf = vec![0u8; 4096];
        let n = conn.read(&mut buf, None).await?;
        println!("Echo: {}", std::str::from_utf8(&buf[..n])?);
    }
    
    conn.close().await?;
    Ok(())
}
```

### Go: Using `pion/dtls`

The `pion/dtls` library is the most complete, production-ready DTLS 1.2 + 1.3 implementation in Go.

**File: `go.mod`**
```
module dtls-example

go 1.22

require (
    github.com/pion/dtls/v3 v3.0.0
    github.com/pion/logging v0.2.2
)
```

**File: `server/main.go`**
```go
package main

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "fmt"
    "net"
    "time"

    "github.com/pion/dtls/v3"
    "github.com/pion/dtls/v3/pkg/crypto/selfsign"
    "github.com/pion/logging"
)

func main() {
    // Generate a self-signed certificate
    // In production: load from files or cert manager
    certificate, err := selfsign.GenerateSelfSigned()
    if err != nil {
        panic(fmt.Sprintf("failed to generate cert: %v", err))
    }

    // Parse the certificate to extract the x509.Certificate for verification
    x509Cert, err := x509.ParseCertificate(certificate.Certificate[0])
    if err != nil {
        panic(err)
    }
    fmt.Printf("Server certificate fingerprint (SHA-256): %x\n",
        sha256Fingerprint(x509Cert.Raw))

    // Configure DTLS
    config := &dtls.Config{
        Certificates: []tls.Certificate{certificate},
        
        // Require client certificate (mutual TLS)
        // For server-only: ClientAuth: tls.NoClientCert
        ClientAuth: tls.RequireAnyClientCert,
        
        // Extended Master Secret (RFC 7627): MUST enable in production
        ExtendedMasterSecret: dtls.RequireExtendedMasterSecret,
        
        // Cipher suites: explicitly enumerate to avoid weak ones
        CipherSuites: []dtls.CipherSuiteID{
            dtls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            dtls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
            dtls.TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA,
        },
        
        // Handshake timeout
        ConnectContextMaker: func() (context.Context, func()) {
            return context.WithTimeout(context.Background(), 30*time.Second)
        },
        
        // Flight interval: how long to wait before retransmitting
        FlightInterval: time.Second,
        
        // PSK (pre-shared key) — alternative to certificate-based auth
        // PSK: func(hint []byte) ([]byte, error) { return key, nil },
        
        // Custom logger
        LoggerFactory: logging.NewDefaultLoggerFactory(),
    }

    addr := &net.UDPAddr{IP: net.ParseIP("0.0.0.0"), Port: 4444}
    listener, err := dtls.Listen("udp", addr, config)
    if err != nil {
        panic(fmt.Sprintf("failed to listen: %v", err))
    }
    defer listener.Close()

    fmt.Printf("DTLS server listening on %s\n", addr)

    for {
        conn, err := listener.Accept()
        if err != nil {
            fmt.Printf("accept error: %v\n", err)
            continue
        }
        go handleConn(conn)
    }
}

func handleConn(conn net.Conn) {
    defer conn.Close()
    
    remote := conn.RemoteAddr()
    fmt.Printf("[%s] New connection\n", remote)
    
    // Print connection details (cast to dtls.Conn for DTLS-specific info)
    if dtlsConn, ok := conn.(*dtls.Conn); ok {
        state := dtlsConn.ConnectionState()
        fmt.Printf("[%s] DTLS version: %d, Cipher suite: %v\n",
            remote, state.Version, state.CipherSuite)
    }

    buf := make([]byte, 8192)
    for {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        
        n, err := conn.Read(buf)
        if err != nil {
            fmt.Printf("[%s] Read error: %v\n", remote, err)
            return
        }
        
        fmt.Printf("[%s] Received %d bytes: %q\n", remote, n, buf[:n])
        
        // Echo
        _, err = conn.Write(buf[:n])
        if err != nil {
            fmt.Printf("[%s] Write error: %v\n", remote, err)
            return
        }
    }
}

func sha256Fingerprint(certDER []byte) []byte {
    h := sha256.Sum256(certDER)
    return h[:]
}
```

**File: `client/main.go`**
```go
package main

import (
    "context"
    "crypto/tls"
    "fmt"
    "net"
    "time"

    "github.com/pion/dtls/v3"
    "github.com/pion/dtls/v3/pkg/crypto/selfsign"
)

func main() {
    certificate, err := selfsign.GenerateSelfSigned()
    if err != nil {
        panic(err)
    }

    config := &dtls.Config{
        Certificates: []tls.Certificate{certificate},
        
        // In production: verify server certificate against trusted CAs
        // InsecureSkipVerify: true is for testing ONLY
        InsecureSkipVerify: true,
        
        ExtendedMasterSecret: dtls.RequireExtendedMasterSecret,
        
        CipherSuites: []dtls.CipherSuiteID{
            dtls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            dtls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        },
        
        ConnectContextMaker: func() (context.Context, func()) {
            return context.WithTimeout(context.Background(), 30*time.Second)
        },
    }

    addr := &net.UDPAddr{IP: net.ParseIP("127.0.0.1"), Port: 4444}
    
    fmt.Printf("Connecting to DTLS server at %s\n", addr)
    conn, err := dtls.Dial("udp", addr, config)
    if err != nil {
        panic(fmt.Sprintf("failed to connect: %v", err))
    }
    defer conn.Close()

    fmt.Println("DTLS handshake complete")
    
    state := conn.ConnectionState()
    fmt.Printf("Cipher suite: %v\n", state.CipherSuite)
    fmt.Printf("DTLS version: %d\n", state.Version)

    for i := 0; i < 5; i++ {
        msg := fmt.Sprintf("Hello DTLS, message #%d", i)
        
        _, err = conn.Write([]byte(msg))
        if err != nil {
            panic(fmt.Sprintf("write error: %v", err))
        }
        
        buf := make([]byte, 4096)
        conn.SetReadDeadline(time.Now().Add(5 * time.Second))
        n, err := conn.Read(buf)
        if err != nil {
            panic(fmt.Sprintf("read error: %v", err))
        }
        
        fmt.Printf("Echo #%d: %q\n", i, buf[:n])
    }
}
```

### Go: PSK (Pre-Shared Key) Mode

For IoT devices where certificate management is impractical:

```go
// Server PSK configuration
config := &dtls.Config{
    PSK: func(hint []byte) ([]byte, error) {
        // hint is the identity sent by the client
        // Look up the key for this identity in your key store
        identity := string(hint)
        key, ok := keyStore[identity]
        if !ok {
            return nil, fmt.Errorf("unknown identity: %s", identity)
        }
        return key, nil
    },
    PSKIdentityHint: []byte("server-identity"),
    CipherSuites: []dtls.CipherSuiteID{
        dtls.TLS_PSK_WITH_AES_128_CCM_8,   // IoT-optimized
        dtls.TLS_PSK_WITH_AES_128_GCM_SHA256,
    },
}

// Client PSK configuration
config := &dtls.Config{
    PSK: func(hint []byte) ([]byte, error) {
        return []byte("pre-shared-secret-32-bytes-long!!"), nil
    },
    PSKIdentityHint: []byte("client-001"),
    CipherSuites: []dtls.CipherSuiteID{
        dtls.TLS_PSK_WITH_AES_128_CCM_8,
    },
}
```

**PSK Security Note**: PSK eliminates PKI complexity but provides no forward secrecy (PSK + ECDHE does: `TLS_ECDHE_PSK_WITH_AES_128_CBC_SHA`). PSK compromise exposes all past and future sessions.

### Go: Unit Tests

**File: `dtls_test.go`**
```go
package dtls_test

import (
    "context"
    "crypto/tls"
    "net"
    "testing"
    "time"

    "github.com/pion/dtls/v3"
    "github.com/pion/dtls/v3/pkg/crypto/selfsign"
    "github.com/stretchr/testify/require"
)

// TestDTLSEcho verifies basic DTLS connect + echo functionality.
func TestDTLSEcho(t *testing.T) {
    cert, err := selfsign.GenerateSelfSigned()
    require.NoError(t, err)

    serverCfg := &dtls.Config{
        Certificates:         []tls.Certificate{cert},
        InsecureSkipVerify:   true,
        ExtendedMasterSecret: dtls.RequireExtendedMasterSecret,
    }

    clientCfg := &dtls.Config{
        InsecureSkipVerify:   true,
        ExtendedMasterSecret: dtls.RequireExtendedMasterSecret,
    }

    addr := &net.UDPAddr{IP: net.ParseIP("127.0.0.1"), Port: 0}
    listener, err := dtls.Listen("udp", addr, serverCfg)
    require.NoError(t, err)
    defer listener.Close()

    actualAddr := listener.Addr()

    // Server goroutine
    errCh := make(chan error, 1)
    go func() {
        conn, err := listener.Accept()
        if err != nil {
            errCh <- err
            return
        }
        defer conn.Close()

        buf := make([]byte, 1024)
        n, err := conn.Read(buf)
        if err != nil {
            errCh <- err
            return
        }
        _, err = conn.Write(buf[:n])
        errCh <- err
    }()

    // Client
    conn, err := dtls.Dial("udp", actualAddr.(*net.UDPAddr), clientCfg)
    require.NoError(t, err)
    defer conn.Close()

    testMsg := []byte("hello DTLS")
    _, err = conn.Write(testMsg)
    require.NoError(t, err)

    buf := make([]byte, 1024)
    conn.SetReadDeadline(time.Now().Add(5 * time.Second))
    n, err := conn.Read(buf)
    require.NoError(t, err)
    require.Equal(t, testMsg, buf[:n])

    require.NoError(t, <-errCh)
}

// TestDTLSHandshakeTimeout verifies timeout behavior.
func TestDTLSHandshakeTimeout(t *testing.T) {
    addr := &net.UDPAddr{IP: net.ParseIP("127.0.0.1"), Port: 19999}

    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()

    config := &dtls.Config{
        InsecureSkipVerify: true,
        ConnectContextMaker: func() (context.Context, func()) {
            return ctx, cancel
        },
    }

    // Nothing listening on port 19999 → should timeout
    _, err := dtls.Dial("udp", addr, config)
    require.Error(t, err, "expected timeout error")
}
```

### Go: Benchmark

```go
func BenchmarkDTLSThroughput(b *testing.B) {
    cert, _ := selfsign.GenerateSelfSigned()
    
    cfg := &dtls.Config{
        Certificates:       []tls.Certificate{cert},
        InsecureSkipVerify: true,
    }
    
    listener, _ := dtls.Listen("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1"), Port: 0}, cfg)
    defer listener.Close()
    
    serverConn := make(chan net.Conn, 1)
    go func() {
        c, _ := listener.Accept()
        serverConn <- c
    }()
    
    clientConn, _ := dtls.Dial("udp", listener.Addr().(*net.UDPAddr), cfg)
    sConn := <-serverConn
    
    payload := make([]byte, 1200) // near-MTU payload
    recvBuf := make([]byte, 4096)
    
    b.SetBytes(int64(len(payload)))
    b.ResetTimer()
    
    for i := 0; i < b.N; i++ {
        clientConn.Write(payload)
        sConn.Read(recvBuf)
    }
}
```

**Run**: `go test -bench=BenchmarkDTLSThroughput -benchmem -cpuprofile=cpu.out`

---

## 22. Debugging and Observability

### Wireshark / Tshark DTLS Capture

```bash
# Capture DTLS traffic on port 4444
tshark -i lo -f "udp port 4444" -d "udp.port==4444,dtls" -w dtls.pcap

# Analyze capture
tshark -r dtls.pcap -V | head -200

# Decrypt if you have the key log file (not applicable to ECDHE without NSS keylog)
# For PSK: tshark can decrypt with PSK configured in preferences
```

Wireshark recognizes DTLS automatically if the port matches common DTLS ports. For custom ports, right-click a UDP packet → "Decode As" → DTLS.

### OpenSSL s_client/s_server for DTLS

```bash
# DTLS server (OpenSSL)
openssl s_server -dtls1_2 -accept 4444 -key server.key -cert server.crt -debug

# DTLS client
openssl s_client -dtls1_2 -connect localhost:4444 -debug -state

# With verbose handshake tracing
openssl s_client -dtls1_2 -connect localhost:4444 \
    -msg -state -debug -trace
```

OpenSSL output shows each handshake message with its content type, epoch, and sequence number.

### Key Log File (for DTLS 1.2)

Set `SSLKEYLOGFILE=/tmp/dtls.keys` before running your application (if it uses OpenSSL or a library that respects this env var). Then load the key log in Wireshark to decrypt captured traffic.

Format:
```
CLIENT_RANDOM <client_random_hex> <master_secret_hex>
```

### Go: Structured Logging for DTLS Events

```go
import (
    "log/slog"
    "github.com/pion/logging"
)

// Custom pion logger that bridges to slog
type slogDTLSLogger struct {
    logger *slog.Logger
    scope  string
}

func (l *slogDTLSLogger) Trace(msg string) {
    l.logger.Debug(msg, "scope", l.scope, "level", "TRACE")
}

func (l *slogDTLSLogger) Debug(msg string) {
    l.logger.Debug(msg, "scope", l.scope)
}

func (l *slogDTLSLogger) Info(msg string) {
    l.logger.Info(msg, "scope", l.scope)
}

func (l *slogDTLSLogger) Warn(msg string) {
    l.logger.Warn(msg, "scope", l.scope)
}

func (l *slogDTLSLogger) Error(msg string) {
    l.logger.Error(msg, "scope", l.scope)
}

// Important metrics to expose:
type DTLSMetrics struct {
    HandshakesTotal      uint64  // Total handshakes attempted
    HandshakesSucceeded  uint64  // Successful handshakes
    HandshakesFailed     uint64  // Failed handshakes (by error type)
    HandshakeDuration    histogram  // P50/P95/P99 handshake latency
    
    RecordsReceived      uint64  // Total records received
    RecordsDropped       uint64  // Dropped (replay / bad MAC / old epoch)
    RecordsDecryptFailed uint64  // AEAD verification failures
    
    RetransmitsTotal     uint64  // Handshake retransmit events
    CookieValidations    uint64  // Cookie challenge/response cycles
    
    BytesSent            uint64  // Application data bytes sent
    BytesReceived        uint64  // Application data bytes received
    
    ActiveConnections    gauge   // Current active DTLS connections
}
```

### Common Failure Modes and Diagnosis

```
Symptom: Handshake never completes, both sides hang
Cause:   Last flight lost, retransmit timer not firing
Diagnosis: tcpdump/tshark — look for flight retransmissions
Fix:     Check retransmit timer configuration; check firewall rules

Symptom: "bad_record_mac" or silent drops after handshake
Cause 1: Epoch mismatch — CCS record lost, records arriving in wrong epoch
Cause 2: Replay attack detected (window overflow from packet burst)
Cause 3: MTU mismatch causing IP fragmentation and partial datagrams
Diagnosis: Enable DTLS debug logging; check epoch numbers in Wireshark
Fix:     Reduce MTU/record size; check for IP fragmentation

Symptom: Client can connect but server drops all packets after ~60s
Cause:   Server-side read deadline / keepalive not configured
Fix:     Implement application-level keepalive (heartbeat extension or app ping)

Symptom: Connection breaks when client moves between networks
Cause:   No Connection ID; server rejects packets from new IP
Fix:     Implement CID extension (RFC 9146)

Symptom: High CPU usage during handshake
Cause:   ECDHE computation; or too many concurrent handshakes
Fix:     Pre-generate ECDH key pairs; rate-limit incoming ClientHellos

Symptom: "certificate verify failed" 
Cause 1: Self-signed cert not in trust store
Cause 2: Certificate fingerprint mismatch (WebRTC)
Cause 3: System clock skew causing cert validity check failure
Fix:     Check notBefore/notAfter; sync NTP; verify fingerprint in SDP
```

---

## 23. Performance Tuning

### Handshake Performance

The DTLS handshake CPU cost is dominated by:
1. **ECDHE key generation**: ~0.1ms (P-256)
2. **Certificate signature verification**: ~0.3ms (RSA-2048) or ~0.05ms (ECDSA P-256)
3. **Certificate parsing**: proportional to chain length
4. **PRF computation**: negligible

```
Tuning strategies:

1. Use ECDSA certificates instead of RSA:
   - ECDSA P-256 signature verification: ~3x faster than RSA-2048
   - Smaller certificates: less fragmentation needed

2. Pre-generate ECDHE key pairs:
   - Don't generate fresh ECDH keypair per handshake
   - Reuse for a short window (e.g., 100ms) with slight security tradeoff
   - Called "key material pre-computation"

3. Session resumption:
   - Full handshake: ~2-4 RTT (with cookie)
   - Session ID/ticket resumption: ~1-2 RTT
   - DTLS 1.3 PSK resumption: 1 RTT
   - Aim for >80% of connections to use resumption in steady state

4. Worker pool for handshakes:
   - ECDHE + cert verification is CPU-intensive
   - Use fixed-size goroutine/thread pool
   - Don't let burst traffic exhaust GOMAXPROCS/CPU cores

5. Cookie validation is free (no state, only HMAC):
   - Cookie exchange costs 1 RTT but CPU is negligible
   - Worth the cost: prevents full handshake DoS
```

### Throughput Performance

```
Factors limiting DTLS throughput vs raw UDP:

1. AEAD overhead:
   - AES-128-GCM: ~16 bytes per record (authentication tag)
   - For 1200-byte records: 1.3% overhead
   - For small records (50 bytes): 32% overhead → send larger records

2. Record header overhead:
   - 13 bytes per record
   - For 1200-byte records: 1.1% overhead
   - Strategy: maximize record size (up to PMTU)

3. Encryption CPU cost:
   - AES-128-GCM with AES-NI: ~1-2 cycles/byte (extremely fast)
   - ChaCha20-Poly1305: ~2-4 cycles/byte (fast without hardware AES)
   - At 10 Gbps: ~8GB/s → AES-NI can sustain this easily

4. System call overhead:
   - Each record → one sendmsg() syscall
   - Batch multiple records into one datagram where possible
   - Use sendmmsg() on Linux to send multiple datagrams per syscall

5. Memory allocation:
   - Pre-allocate receive buffers
   - Use sync.Pool for record buffers in Go
   - Avoid per-record heap allocation in hot path
```

### Optimal Record Size

```
For throughput-oriented applications:
  Max record size = PMTU - headers = ~1200 bytes payload

For latency-oriented applications (gaming, voice):
  Small records: send immediately, don't wait for more data
  Accept higher overhead percentage for lower latency
  Typically 100-400 bytes per record

For mixed (like QUIC):
  Multiple logical messages per DTLS record
  Coalesce small messages with a brief delay (0-1ms)
```

### Go-Specific Optimizations

```go
// Use sync.Pool for DTLS buffers
var bufPool = sync.Pool{
    New: func() interface{} {
        b := make([]byte, 1500)
        return &b
    },
}

func receive(conn net.Conn) {
    bufPtr := bufPool.Get().(*[]byte)
    defer bufPool.Put(bufPtr)
    buf := *bufPtr
    
    n, err := conn.Read(buf)
    // process buf[:n]
    _ = err
}

// Avoid goroutine-per-connection for high connection counts
// Use io_uring (via giouring) or epoll-based approach
// pion/dtls handles this internally

// Profile with:
// go tool pprof -http=:6060 http://localhost:6061/debug/pprof/profile?seconds=30
```

---

## 24. Production Checklist

### Cryptography

```
□ Use only AEAD cipher suites (AES-GCM or ChaCha20-Poly1305)
□ No NULL, RC4, DES, 3DES, EXPORT cipher suites
□ Prefer ECDHE for forward secrecy (ephemeral key exchange)
□ ECDSA certificates preferred over RSA (smaller, faster)
□ RSA if used: minimum 2048 bits (3072 bits recommended)
□ ECDSA: P-256 or P-384 curves only (not P-521, too slow)
□ Extended Master Secret extension (RFC 7627) MUST be enabled
□ No renegotiation allowed (disable or implement RFC 5746)
□ DTLS 1.3 preferred; DTLS 1.2 if legacy support needed
□ DTLS 1.0 MUST be disabled
□ TLS 1.0/1.1 must be disabled if sharing code with TLS
```

### Certificate Management

```
□ Use short-lived certificates (90 days max; automate renewal)
□ OCSP stapling for revocation status (or CRL distribution)
□ Certificate pinning for IoT/embedded (not for web)
□ Monitor certificate expiry; alert at 30 days
□ Separate CA for internal services (do not reuse public CA certs internally)
□ Private key material: NEVER logged, stored in HSM or secrets manager
□ For WebRTC: verify SDP fingerprints before trusting connection
```

### Network / Firewall

```
□ Restrict source IPs where possible
□ Rate limit incoming ClientHellos per source IP (cookie exchange)
□ UDP fragment blocking: configure to drop IP fragments for DTLS ports
  (DTLS handles its own fragmentation; IP fragments indicate misconfiguration)
□ ICMP unreachable messages: ensure they reach the application
  (needed for PMTU discovery)
□ Monitor for DTLS handshake flood (many CookieRequests from same IP)
□ Connection ID: implement if client mobility expected
□ Heartbeat extension: implement application-level keepalive
  (not the TLS heartbeat, which caused Heartbleed in OpenSSL)
```

### Implementation

```
□ Constant-time operations for all cryptographic comparisons
  (MAC comparison, PSK comparison)
□ Replay window: minimum 64 records; consider 128 for bursty traffic
□ Fragment reassembly memory limits: cap per-connection buffer
□ Handshake timeout: 30 seconds maximum; 10 seconds recommended
□ Maximum handshake retransmits: 5-7 attempts with exponential backoff
□ Cookie rotation: rotate server secret every 5-10 minutes
□ Session ticket rotation: rotate ticket key every 24 hours
□ Secure random number generation: /dev/urandom or CSPRNG
□ Memory zeroization: zero key material from memory after use
□ Prevent debug logging of plaintext content or key material
□ Fuzzing: run protocol parser fuzzer (go-fuzz, cargo-fuzz, AFL)
```

### Observability

```
□ Metric: handshake success/failure rate
□ Metric: handshake duration (P50, P95, P99)
□ Metric: handshake retransmit count
□ Metric: active DTLS connection count
□ Metric: records dropped (replay, bad MAC, old epoch)
□ Metric: bytes sent/received per connection
□ Alert: certificate expiry < 30 days
□ Alert: handshake failure rate > 1%
□ Alert: retransmit rate > 5% (indicates network issues)
□ Alert: AEAD failure rate > 0 (active attacker or bug)
□ Log: handshake completion (with peer identity, cipher suite, version)
□ Log: fatal alerts (with alert type and peer identity)
□ Log: connection teardown (with duration and bytes transferred)
```

---

## 25. Further Reading

### RFCs (Read in This Order)

| RFC | Title | Priority |
|---|---|---|
| RFC 6347 | DTLS 1.2 | **Essential** |
| RFC 9147 | DTLS 1.3 | **Essential** |
| RFC 8446 | TLS 1.3 (foundation) | Essential |
| RFC 9146 | Connection ID for DTLS | Important |
| RFC 5764 | DTLS-SRTP | Important (WebRTC) |
| RFC 7925 | TLS/DTLS Profiles for IoT | Important (IoT) |
| RFC 4821 | PMTU Discovery | Useful |
| RFC 7627 | Extended Master Secret | Important |
| RFC 5705 | TLS Exporters | Useful (DTLS-SRTP) |
| RFC 6083 | DTLS for SCTP | Useful (WebRTC data channels) |
| RFC 8094 | DNS over DTLS | Reference |
| RFC 7360 | RADIUS over DTLS | Reference |

### Books

- **"Network Security with OpenSSL"** — Viega, Messier, Chandra (O'Reilly)  
  Deep protocol internals, TLS record formats, cipher implementation details.

- **"Real World Cryptography"** — David Wong (Manning)  
  Modern cryptographic primitives used in DTLS; AEAD, ECDHE, signature schemes.

- **"TLS Mastery"** — Michael W. Lucas  
  Practical TLS/DTLS deployment; certificate management; debugging.

### Reference Implementations

- **pion/dtls** (Go): https://github.com/pion/dtls  
  Most complete Go DTLS 1.2/1.3 implementation; production quality; used in WebRTC.

- **webrtc-rs** (Rust): https://github.com/webrtc-rs/webrtc  
  Rust port of the pion ecosystem including DTLS.

- **OpenSSL** (C): https://github.com/openssl/openssl  
  The reference C implementation; read `ssl/d1_*.c` files for DTLS specifics.

- **tinydtls** (C, embedded): https://github.com/eclipse/tinydtls  
  Minimal DTLS 1.2 for constrained devices; CoAP-oriented.

- **mbedTLS** (C, embedded): https://github.com/ARMmbed/mbedtls  
  DTLS implementation for ARM Cortex-M; full PSK + certificate support.

### Articles and Papers

- **"DTLS Reconsidered"** — Eric Rescorla (IETF blog)  
  Design rationale behind DTLS 1.3 changes.

- **"Lucky 13: Breaking the TLS and DTLS Record Protocols"** — AlFardan, Paterson (IEEE S&P 2013)  
  The attack that killed CBC mode; essential for understanding why AEAD is mandatory.

- **"Scanning the Internet for Loci of Criminal Activity"** — Durumeric et al.  
  ZMap paper; techniques for measuring DTLS deployment in the wild.

- **"Adapting TLS 1.3 for Use in Datagram Protocols"** — RFC 9147 appendix A  
  Detailed rationale for every design decision in DTLS 1.3.

### Tools

```bash
# Test DTLS server (like curl for DTLS)
openssl s_client -dtls1_2 -connect host:port

# Scan for DTLS services
nmap -sU -p 4444 --script dtls-<script> host

# Generate DTLS test certificates
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
    -keyout key.pem -out cert.pem -days 90 -nodes \
    -subj "/CN=dtls-test"

# Fuzz DTLS parser (Go)
go-fuzz-build && go-fuzz

# Fuzz DTLS parser (Rust)
cargo fuzz run dtls_parser

# Analyze DTLS traffic
tshark -r capture.pcap -Y dtls -T fields \
    -e frame.number \
    -e dtls.record.content_type \
    -e dtls.record.version \
    -e dtls.record.epoch \
    -e dtls.record.sequence_number \
    -e dtls.handshake.type
```

---

## Appendix A: DTLS vs TLS — Complete Diff Table

```
Feature                    TLS 1.2              DTLS 1.2
─────────────────────────────────────────────────────────────────────
Transport                  TCP (reliable)       UDP (unreliable)
Record sequence#           Implicit (TCP pos)   Explicit 48-bit field
Record header size         5 bytes              13 bytes (+8 for epoch+seq)
Epoch field                No                   Yes (2 bytes)
Version encoding           0x0303               0xFEFD (inverted)
Handshake header size      4 bytes              12 bytes (+8 for msg fields)
message_seq field          No                   Yes (2 bytes)
fragment_offset field      No                   Yes (3 bytes)
fragment_length field       No                   Yes (3 bytes)
Handshake fragmentation    By TCP               By DTLS itself
Handshake reliability      By TCP               By DTLS retransmit timer
DoS prevention             TCP SYN cookies      DTLS cookie exchange
HelloVerifyRequest         No                   Yes
Cookie in ClientHello      No                   Yes
Replay protection          Not needed (TCP seq) 64-bit sliding window
Record reordering          Not possible (TCP)   Handled by DTLS layer
Flight concept             No                   Yes (groups of messages)
Retransmission timer       No                   Yes (exponential backoff)
PMTU handling              TCP MSS negotiation  App-layer fragmentation
ChangeCipherSpec           Message type 20      Same; resets per-epoch seq#
Session resumption         Session ID / Ticket  Same mechanisms
Renegotiation              Yes (with RFC 5746)  Yes (DTLS 1.2 only)
Connection ID              No                   RFC 9146 extension
```

---

## Appendix B: Wireshark DTLS Filter Cheatsheet

```
# Show all DTLS traffic
dtls

# Filter by handshake type
dtls.handshake.type == 1   # ClientHello
dtls.handshake.type == 2   # ServerHello
dtls.handshake.type == 11  # Certificate
dtls.handshake.type == 20  # Finished

# Filter by record content type
dtls.record.content_type == 22  # Handshake
dtls.record.content_type == 23  # Application data
dtls.record.content_type == 21  # Alert

# Filter by epoch
dtls.record.epoch == 0   # Pre-encryption records
dtls.record.epoch >= 1   # Encrypted records

# Filter by DTLS version
dtls.record.version == 0xfefd  # DTLS 1.2
dtls.record.version == 0xfeff  # DTLS 1.0

# Show alerts only
dtls.alert.message

# Show fragmented handshake messages
dtls.handshake.fragment_offset > 0
```

---

## Appendix C: DTLS 1.2 vs 1.3 Migration Guide

```
Step 1: Identify current DTLS 1.2 usage
  - Which cipher suites are negotiated? (tshark + logs)
  - Which extensions are used? (use_srtp, session tickets, etc.)
  - Any PSK or mutual auth scenarios?

Step 2: Update cipher suites
  DTLS 1.3 supports only:
    TLS_AES_128_GCM_SHA256       (mandatory)
    TLS_AES_256_GCM_SHA384
    TLS_CHACHA20_POLY1305_SHA256
    TLS_AES_128_CCM_SHA256
    TLS_AES_128_CCM_8_SHA256     (IoT, 8-byte tag)

Step 3: Update key exchange
  DTLS 1.3 eliminates:
    - RSA key exchange (no PFS)
    - static ECDH
    - DHE (finite-field)
  Use only:
    - ECDHE (X25519 recommended)
    - PSK with (EC)DHE

Step 4: Update handshake handling
  - HelloVerifyRequest → HelloRetryRequest (cookie in extension)
  - cookie field in ClientHello → cookie extension
  - epoch 0/1 → epoch 0/2/3 scheme
  - ACK messages now required

Step 5: Update record parsing
  - New unified header format for epoch >= 1
  - Sequence number encryption
  - Content type at end of plaintext (not in header)

Step 6: Testing matrix
  □ DTLS 1.2 client ↔ DTLS 1.3 server (should fail gracefully)
  □ DTLS 1.3 client ↔ DTLS 1.2 server (should negotiate 1.2)
  □ DTLS 1.3 client ↔ DTLS 1.3 server (target)
  □ Session resumption across DTLS versions
  □ Cookie exchange in 1.3 mode
  □ ACK handling under packet loss simulation
```

---

*Guide version: 2025-05. Covers RFCs through April 2022 (RFC 9147). Always verify against the latest IETF DTLS working group drafts at https://datatracker.ietf.org/wg/tls/documents/*

