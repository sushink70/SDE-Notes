# HTTP/3 — A Complete, In-Depth Technical Guide

> *"To understand HTTP/3, you must first understand every problem it was built to solve."*

---

## Table of Contents

1. [The Evolution of HTTP — Why HTTP/3 Exists](#1-the-evolution-of-http)
2. [The Core Problem: TCP and Head-of-Line Blocking](#2-the-core-problem-tcp-and-head-of-line-blocking)
3. [What is QUIC? The Engine Behind HTTP/3](#3-what-is-quic)
4. [UDP — The Foundation QUIC Builds On](#4-udp-the-foundation-quic-builds-on)
5. [QUIC Connection Establishment](#5-quic-connection-establishment)
6. [TLS 1.3 Integration in QUIC](#6-tls-13-integration-in-quic)
7. [0-RTT and 1-RTT Handshakes](#7-0-rtt-and-1-rtt-handshakes)
8. [QUIC Streams — The Core Abstraction](#8-quic-streams)
9. [Multiplexing Without Head-of-Line Blocking](#9-multiplexing-without-head-of-line-blocking)
10. [QUIC Packet Structure — Anatomy of Every Byte](#10-quic-packet-structure)
11. [QUIC Frame Types](#11-quic-frame-types)
12. [Flow Control — Per-Stream and Connection-Level](#12-flow-control)
13. [Congestion Control in QUIC](#13-congestion-control-in-quic)
14. [Loss Detection and Recovery](#14-loss-detection-and-recovery)
15. [Connection Migration](#15-connection-migration)
16. [Connection IDs — What They Are and Why They Matter](#16-connection-ids)
17. [HTTP/3 — The Application Layer on QUIC](#17-http3-the-application-layer)
18. [HTTP/3 Framing Layer](#18-http3-framing-layer)
19. [QPACK — Header Compression in HTTP/3](#19-qpack-header-compression)
20. [HPACK vs QPACK — The Deep Comparison](#20-hpack-vs-qpack)
21. [HTTP/3 Request/Response Lifecycle](#21-http3-requestresponse-lifecycle)
22. [Server Push in HTTP/3](#22-server-push-in-http3)
23. [Prioritization in HTTP/3](#23-prioritization-in-http3)
24. [The QUIC vs TCP Comparison — Every Dimension](#24-quic-vs-tcp-comparison)
25. [HTTP/1.1 vs HTTP/2 vs HTTP/3 — Side-by-Side](#25-http-versions-comparison)
26. [Performance Characteristics and Real Numbers](#26-performance-characteristics)
27. [Security Model of HTTP/3](#27-security-model)
28. [Ossification and Why QUIC Uses UDP](#28-ossification-and-why-quic-uses-udp)
29. [NAT Traversal and Middleboxes](#29-nat-traversal-and-middleboxes)
30. [HTTP/3 in Practice — Deployment, Discovery, Alt-Svc](#30-http3-in-practice)
31. [QUIC Versions and the IETF Standard](#31-quic-versions-and-ietf-standard)
32. [Implementation Landscape](#32-implementation-landscape)
33. [Mental Models and Expert Intuition](#33-mental-models-and-expert-intuition)

---

## 1. The Evolution of HTTP

### What is HTTP?

**HTTP (HyperText Transfer Protocol)** is an application-layer protocol that defines how clients (browsers, apps) and servers communicate over a network. It is the foundation of data exchange on the web.

Before understanding HTTP/3, you must understand *every step* of the journey — because each version was a direct response to the failures of the previous one.

---

### HTTP/0.9 (1991) — The One-Liner

- Only `GET` method.
- No headers. No status codes.
- One request, one response, connection closed.

```
Client: GET /index.html
Server: <html>...</html>   [connection closes]
```

---

### HTTP/1.0 (1996) — Headers Arrive

- Added `POST`, `HEAD` methods.
- Added headers: `Content-Type`, `Content-Length`.
- Added status codes: `200 OK`, `404 Not Found`.
- **Still one request per TCP connection.** After each response, the connection is torn down.

**Problem:** Creating a new TCP connection for every resource is expensive:
- TCP 3-way handshake = 1 Round-Trip Time (RTT) wasted before any data.
- A modern web page may need 50–100 resources.
- 100 resources × 1 RTT = enormous latency.

```
[TCP Handshake] → [Request /index.html] → [Response] → [TCP Teardown]
[TCP Handshake] → [Request /style.css]  → [Response] → [TCP Teardown]
[TCP Handshake] → [Request /logo.png]   → [Response] → [TCP Teardown]
... (repeated for every single resource)
```

---

### HTTP/1.1 (1997, revised 2014) — Keep-Alive and Pipelining

**Improvements:**
- **Persistent connections** (`Connection: keep-alive`): Reuse the same TCP connection for multiple requests.
- **Pipelining**: Send multiple requests without waiting for each response.
- **Chunked transfer encoding**: Stream response body.
- **Host header**: Required, enabling virtual hosting.

**Persistent Connection:**
```
[TCP Handshake]
  → GET /index.html
  ← 200 OK (HTML)
  → GET /style.css
  ← 200 OK (CSS)
  → GET /logo.png
  ← 200 OK (PNG)
[Connection kept alive or closed]
```

**Remaining Problems:**
1. **Head-of-Line (HoL) Blocking** (explained in detail in Section 2).
2. **Pipelining is broken in practice** — most browsers disabled it because servers and proxies handle it incorrectly.
3. **Header redundancy** — headers are resent with every request as plain text (cookies, user-agent, etc.).
4. **No multiplexing** — responses must arrive in order.

---

### HTTP/2 (2015) — Binary, Multiplexed, Compressed

HTTP/2 was a major redesign. It introduced:

- **Binary framing** instead of plain text.
- **Multiplexing**: Multiple requests/responses over a *single* TCP connection simultaneously.
- **Header compression** via **HPACK** — a stateful compression algorithm that uses a shared dictionary.
- **Stream prioritization**.
- **Server Push**: Server can proactively send resources the client will need.

**HTTP/2 Multiplexing:**
```
TCP Connection
 ├── Stream 1: GET /index.html  ──→  ←── 200 HTML
 ├── Stream 3: GET /style.css   ──→  ←── 200 CSS
 ├── Stream 5: GET /logo.png    ──→  ←── 200 PNG
 └── Stream 7: GET /script.js   ──→  ←── 200 JS
(all interleaved as frames on one TCP connection)
```

**But a critical problem remained:**
- HTTP/2 solved application-level HoL blocking.
- But **TCP-level HoL blocking** still exists.
- If any TCP segment is lost, ALL streams stall — even those with no lost data.

This is the fundamental problem HTTP/3 solves.

---

### HTTP/3 (2022, RFC 9114) — QUIC Replaces TCP

HTTP/3 keeps the HTTP/2 semantics (methods, headers, status codes) but replaces the transport:

| Layer         | HTTP/1.1 & HTTP/2 | HTTP/3         |
|--------------|-------------------|----------------|
| Application  | HTTP              | HTTP/3         |
| Transport    | TCP               | QUIC (over UDP)|
| Crypto       | TLS (separate)    | TLS 1.3 (built-in to QUIC) |
| Network      | IP                | IP             |

---

## 2. The Core Problem: TCP and Head-of-Line Blocking

### What is a TCP Segment?

TCP (Transmission Control Protocol) sends data as a stream of bytes, broken into **segments**. Each segment has a **sequence number**. The receiver must acknowledge (ACK) each segment in order.

**Key rule of TCP:** Data is delivered to the application **in order**. If segment 5 is lost but segment 6 arrives, segment 6 is buffered and the application cannot read it until segment 5 is retransmitted and received.

### TCP Head-of-Line Blocking — The Core Problem

```
TCP Byte Stream (HTTP/2 streams multiplexed on it):

Segment 1 [Stream A: Frame 1]  ✓ Delivered
Segment 2 [Stream B: Frame 1]  ✓ Delivered
Segment 3 [Stream A: Frame 2]  ✗ LOST  ← packet dropped by network
Segment 4 [Stream C: Frame 1]  ? Held (cannot deliver, out of order)
Segment 5 [Stream B: Frame 2]  ? Held (cannot deliver, out of order)
Segment 6 [Stream A: Frame 3]  ? Held (cannot deliver, out of order)
...

   [TIME PASSES — retransmission of segment 3]

Segment 3 [Stream A: Frame 2]  ✓ Re-delivered
Segment 4,5,6...               ✓ Now released from buffer
```

**The tragedy:** Stream B and Stream C had zero packet loss. Yet they were completely stalled because Stream A lost a segment. This is **TCP Head-of-Line Blocking** — a fundamental property of TCP's ordered delivery guarantee.

### Why Can't HTTP/2 Fix This?

HTTP/2 multiplexing works at the **application layer** (above TCP). It cannot tell TCP to deliver data out of order — that is TCP's core contract. TCP is a kernel-level protocol, and changing its behavior would require OS changes globally.

### The Scale of the Problem

In a typical HTTP/2 page load:
- 1% packet loss → 3× slower than HTTP/1.1 (because all streams stall).
- On mobile networks with 2-5% packet loss, HTTP/2 can be *worse* than HTTP/1.1.

This is why Google engineers at Google started working on **QUIC** in 2012.

---

## 3. What is QUIC?

### Definition

**QUIC** (originally: Quick UDP Internet Connections, now just a proper noun — "QUIC") is a **general-purpose, multiplexed, encrypted transport protocol** built on top of UDP.

QUIC was:
- Originally designed by **Jim Roskind at Google** in 2012.
- Deployed in Chrome and Google's servers starting 2013.
- Standardized by the IETF as **RFC 9000** in May 2021.
- The IETF QUIC is significantly different from Google's original QUIC (gQUIC).

### What QUIC Provides

| Feature                      | TCP+TLS | QUIC        |
|-----------------------------|---------|-------------|
| Reliable delivery            | ✓       | ✓           |
| Ordered delivery             | ✓       | Per-stream  |
| Encryption                   | TLS sep.| Built-in    |
| Multiplexing                 | ✗       | ✓ (native)  |
| HoL blocking                 | Yes     | No          |
| Connection migration         | ✗       | ✓           |
| 0-RTT reconnection           | Limited | ✓           |
| Handshake RTTs               | 2-3     | 1 (0 resume)|
| Congestion control           | ✓       | ✓ (flexible)|
| Flow control                 | Connection-level | Per-stream + Connection |

### QUIC Architecture

```
+----------------------------------------------------------+
|                   HTTP/3 (Application)                   |
+----------------------------------------------------------+
|              QUIC Streams (Multiplexing)                 |
+----------------------------------------------------------+
|         QUIC Transport (Reliability, Flow Control)       |
+----------------------------------------------------------+
|              TLS 1.3 (Encryption, built-in)              |
+----------------------------------------------------------+
|                     QUIC Framing                         |
+----------------------------------------------------------+
|              UDP (Datagram Transport)                    |
+----------------------------------------------------------+
|                      IP                                  |
+----------------------------------------------------------+
```

---

## 4. UDP — The Foundation QUIC Builds On

### What is UDP?

**UDP (User Datagram Protocol)** is a transport-layer protocol that provides:
- **No connection establishment** — just send datagrams.
- **No guaranteed delivery** — datagrams can be lost, duplicated, or reordered.
- **No ordering** — packets arrive in any order.
- **No congestion control** — sends as fast as it wants.
- **Low overhead** — 8-byte header (vs TCP's 20+ bytes).

### UDP Header

```
 0      7 8     15 16    23 24    31
+--------+--------+--------+--------+
|   Source Port   |  Destination Port|
+--------+--------+--------+--------+
|     Length      |    Checksum     |
+--------+--------+--------+--------+
|            Data (payload)         |
```

### Why Build on UDP?

UDP is the **blank canvas**. It gives QUIC:
1. **The ability to implement its own reliability** — with smarter semantics than TCP.
2. **Freedom from kernel changes** — QUIC runs in user space.
3. **Traversal of middleboxes** — UDP is widely permitted by firewalls.
4. **Independent evolution** — QUIC can be updated without OS kernel updates.

The key insight: **QUIC is not "unreliable UDP." QUIC is a reliable protocol that implements its own reliability on top of UDP**, but with better properties than TCP.

### QUIC Packet Encapsulation

```
+--------------------+
|    IP Header       |  (Layer 3)
+--------------------+
|    UDP Header      |  (Layer 4) — 8 bytes
+--------------------+
|    QUIC Header     |  (QUIC packet header)
+--------------------+
|    QUIC Frames     |  (actual content, fully encrypted)
+--------------------+
```

Every QUIC packet is a UDP datagram. Multiple QUIC packets can be coalesced into a single UDP datagram.

---

## 5. QUIC Connection Establishment

### The Problem with TCP+TLS Handshake

**TCP 3-Way Handshake:**
```
Client                          Server
  |                               |
  |--------- SYN --------------->|  RTT 0.5
  |<-------- SYN-ACK ------------|  RTT 0.5
  |--------- ACK --------------->|
  |  [TCP established — 1 RTT]   |
  |                               |
  |--------- ClientHello ------->|  (TLS begins)
  |<-------- ServerHello,        |
  |           Certificate,       |  RTT 1.5
  |           ServerHelloDone ---|
  |--------- ClientKeyExchange,  |
  |           ChangeCipherSpec,  |
  |           Finished ---------->|
  |<-------- ChangeCipherSpec,   |  RTT 2.5
  |           Finished -----------|
  |                               |
  | [TLS established — 2 RTTs]   |
  | [Total: 3 RTTs before data]  |
```

With TLS 1.3 (TCP):
```
Client                          Server
  | SYN                   -->     |  TCP: 1 RTT
  | <-- SYN-ACK                   |
  | ACK + ClientHello     -->     |  TLS: 1 more RTT
  | <-- ServerHello + cert        |
  | Finished + HTTP Request -->   |  HTTP: data starts
```
Total: **2 RTTs** before first byte of HTTP data.

### QUIC 1-RTT Handshake

QUIC combines the transport handshake and TLS 1.3 into a **single round trip**:

```
Client                                      Server
  |                                          |
  | Initial Packet                           |
  | [QUIC header + TLS ClientHello]  ------> |
  |                                          |
  | <------ Initial Packet                   |
  |         [QUIC header +                   |
  |          TLS ServerHello +               |
  |          Certificate +                   |
  |          CertificateVerify +             |
  |          Finished]                       |
  |          + Handshake Packets             |
  |                                          |
  | Handshake Packet                         |
  | [Finished] + 1-RTT Packets  ----------->|
  | [HTTP/3 data starts HERE]   ----------->|
  |                                          |
  | <------- 1-RTT Packets                   |
  |          [HTTP/3 response]               |
```

**Total: 1 RTT** before HTTP data. This is 2× faster than TCP+TLS 1.3.

### QUIC Packet Number Spaces

QUIC separates packet number spaces for different phases:

| Space       | Used For                          | Encryption     |
|------------|-----------------------------------|----------------|
| Initial    | First ClientHello/ServerHello     | AEAD (fixed key derived from DCID) |
| Handshake  | TLS handshake messages            | Handshake keys |
| 0-RTT      | Early application data            | 0-RTT keys     |
| 1-RTT      | Application data post-handshake   | 1-RTT keys     |

Each space has **independent packet numbers starting at 0**. This prevents cross-space attacks.

---

## 6. TLS 1.3 Integration in QUIC

### What is TLS 1.3?

**TLS (Transport Layer Security) 1.3** (RFC 8446, 2018) is the cryptographic protocol that provides:
- **Authentication**: Verify the server is who it claims.
- **Confidentiality**: Encrypt data so eavesdroppers cannot read it.
- **Integrity**: Detect tampering.
- **Forward secrecy**: Past sessions cannot be decrypted even if keys are compromised later.

### How TLS 1.3 Differs from TLS 1.2

TLS 1.2 required **2 RTTs** for the handshake. TLS 1.3:
- Reduced to **1 RTT** (0 RTT for resumption).
- Removed weak cipher suites (RSA key exchange, SHA-1, etc.).
- Made forward secrecy mandatory (ECDHE key exchange).

### QUIC's Deep Integration with TLS 1.3

In TCP+TLS, TLS runs *on top of* TCP — they are separate protocols:
```
TLS record layer → TCP → IP
```

In QUIC, TLS 1.3 is **embedded within QUIC** — but with a twist:
- QUIC does **not** use TLS record layer.
- QUIC uses only the **TLS handshake** to negotiate keys.
- QUIC then uses those keys with its own **AEAD encryption** on QUIC packets.

```
                   TLS 1.3 Handshake
                   (generates keys)
                         |
                         v
         +---------------------------------+
         |  QUIC Packet Encryption (AEAD)  |
         |  using keys from TLS 1.3        |
         +---------------------------------+
```

**AEAD (Authenticated Encryption with Associated Data):** Every QUIC packet is encrypted AND authenticated. An attacker cannot:
- Read the contents.
- Modify the contents without detection.
- Replay packets (nonces prevent this).

### Encryption Keys Derived in QUIC

```
Initial Keys  → Derived from Connection ID (public, provides basic protection)
Handshake Keys → Derived from TLS 1.3 handshake (protect certificate exchange)
0-RTT Keys    → Derived from previous session's resumption secret
1-RTT Keys    → Final session keys (used for all application data)
```

Each set of keys uses **HKDF (HMAC-based Key Derivation Function)** to derive:
- `client_write_key` / `server_write_key`
- `client_write_iv` / `server_write_iv`
- `client_hp_key` / `server_hp_key` (header protection)

### Header Protection

QUIC encrypts not just the payload but also part of the header (packet number, flags). This prevents **traffic analysis** — an observer cannot even see packet sequence numbers.

```
QUIC Packet:
+-------------------+------------------------+
| Protected Header  |  Encrypted Payload     |
| (flags, pkt num) |  (AEAD encrypted)      |
+-------------------+------------------------+
        ^
        | HP (Header Protection) key applied
        | to obscure packet number bits
```

---

## 7. 0-RTT and 1-RTT Handshakes

### What is RTT?

**RTT (Round-Trip Time)** is the time for a signal to travel from client to server and back. If a server is 50ms away, RTT ≈ 100ms. Every "RTT" you spend in handshaking is pure latency overhead before any useful data flows.

### 1-RTT Handshake (New Connection)

```
Time 0ms:
  Client sends: UDP packet with QUIC Initial
                [QUIC header | TLS ClientHello]

Time 100ms (1 RTT later):
  Server sends: QUIC Initial + Handshake packets
                [TLS ServerHello | ServerCertificate | Finished]

Time 100ms:
  Client can NOW send:
  - QUIC Handshake [TLS Finished]
  - QUIC 1-RTT [HTTP/3 GET request]   ← DATA FLOWS HERE

Time 200ms (2 RTTs after start):
  Server sends:
  - QUIC 1-RTT [HTTP/3 response]      ← RESPONSE ARRIVES
```

**First byte of response: 200ms** (with 100ms RTT)

Compare to TCP+TLS 1.3: First byte at **300ms** (3 RTTs × 100ms).

### 0-RTT Handshake (Session Resumption)

When a client has previously connected to a server, it stores a **PSK (Pre-Shared Key)** session ticket. On reconnection:

```
Time 0ms:
  Client sends: QUIC Initial
                [TLS ClientHello + early_data extension]
                QUIC 0-RTT Packet
                [HTTP/3 GET request]  ← DATA SENT IMMEDIATELY

Time 100ms (1 RTT later):
  Server sends: QUIC response
                [HTTP/3 data]         ← RESPONSE ARRIVES
```

**First byte of response: 100ms** — same as if there was no handshake at all!

### 0-RTT Security Warning — Replay Attacks

0-RTT has a known limitation: **replay attacks**.

Because the 0-RTT data is sent before the server confirms the session, an attacker who captures a 0-RTT packet can replay it to the server, causing the same request to be processed again.

**Mitigation:**
- Servers should only accept **idempotent** requests (GET, HEAD) in 0-RTT.
- Never accept state-changing requests (POST, DELETE) in 0-RTT.
- Servers maintain a **replay cache** of 0-RTT tokens.
- 0-RTT data has **no forward secrecy** — if the PSK is compromised, past 0-RTT data is exposed.

```
0-RTT Data Properties:
  ✓ Zero latency overhead
  ✗ No forward secrecy
  ✗ Vulnerable to replay attacks
  → Use only for safe, idempotent, non-sensitive requests
```

---

## 8. QUIC Streams

### What is a Stream?

A **QUIC stream** is a lightweight, ordered, reliable byte channel within a QUIC connection. Think of it as a **mini-TCP connection** inside QUIC.

- Multiple streams can be **active simultaneously** within one QUIC connection.
- Each stream is **independently reliable** — a lost packet for one stream does not block others.
- Streams are identified by a **Stream ID** (a 62-bit integer).

### Stream Types

QUIC defines 4 stream types based on the **2 least-significant bits** of the Stream ID:

| Stream ID (mod 4) | Type                        |
|------------------|-----------------------------|
| 0x0              | Client-initiated bidirectional |
| 0x1              | Server-initiated bidirectional |
| 0x2              | Client-initiated unidirectional |
| 0x3              | Server-initiated unidirectional |

**Bidirectional stream:** Both endpoints can send data. Used for HTTP/3 request/response pairs.

**Unidirectional stream:** Only the initiator sends data. Used in HTTP/3 for:
- Control stream (stream type 0x00)
- QPACK encoder stream (type 0x02)
- QPACK decoder stream (type 0x03)
- Push stream (type 0x01)

### Stream ID Assignment

```
Client streams (even IDs): 0, 4, 8, 12, ...
  Bidirectional: 0, 4, 8, ...
  Unidirectional: 2, 6, 10, ...

Server streams (odd IDs): 1, 5, 9, 13, ...
  Bidirectional: 1, 5, 9, ...
  Unidirectional: 3, 7, 11, ...
```

Incrementing by 4 (not 1) ensures the type bits are preserved.

### Stream States (Bidirectional)

```
                     Sending Side
                          |
               [Stream created]
                          |
                          v
                +------------------+
                |      READY       |
                +------------------+
                          |
                   [STREAM frame sent]
                          |
                          v
                +------------------+
                |      SEND        |<--+
                +------------------+   |
                          |            | (more data)
                 [FIN sent or          |
                  MAX_STREAM_DATA]      |
                          |
                          v
                +------------------+
                |  DATA SENT       |
                +------------------+
                          |
              [All data acknowledged]
                          |
                          v
                +------------------+
                |  DATA RECVD      |
                +------------------+

                     Receiving Side
                          |
               [STREAM frame received]
                          |
                          v
                +------------------+
                |      RECV        |<--+
                +------------------+   |
                          |            | (more data)
              [FIN received]           |
                          |
                          v
                +------------------+
                |  SIZE KNOWN      |
                +------------------+
                          |
              [All data received]
                          |
                          v
                +------------------+
                |  DATA RECVD      |
                +------------------+
                          |
              [App consumes data]
                          |
                          v
                +------------------+
                |  DATA READ       |
                +------------------+
```

### Stream Termination

A stream can end in three ways:
1. **Normal close**: Sender sets FIN bit. All data acknowledged. Stream cleanly done.
2. **Reset**: Sender sends `RESET_STREAM`. Abruptly terminates — receiver discards buffered data.
3. **Stop sending**: Receiver sends `STOP_SENDING`. Tells sender to reset voluntarily.

---

## 9. Multiplexing Without Head-of-Line Blocking

### The Key Difference from HTTP/2

In **HTTP/2 over TCP**:
- All HTTP/2 streams share one TCP connection.
- TCP guarantees in-order delivery of ALL bytes.
- A lost TCP segment blocks ALL streams.

In **HTTP/3 over QUIC**:
- Each HTTP/3 request runs on its own QUIC stream.
- QUIC streams are only ordered *within themselves*.
- A lost QUIC packet carrying Stream A data **does not block** Stream B.

### Visual Comparison

**HTTP/2 HoL Blocking:**
```
TCP Segment Timeline:

Seg 1 [Stream A] ─────────────────────────────→ ✓ App receives
Seg 2 [Stream B] ─────────────────────────────→ ✓ 
Seg 3 [Stream A] ─ X (LOST)                   → ✗ 
Seg 4 [Stream C] ──────────────────────────────→ ✗ BLOCKED (in TCP buffer)
Seg 5 [Stream B] ──────────────────────────────→ ✗ BLOCKED (in TCP buffer)
                     |
               [Retransmit Seg 3]
                     |
Seg 3 [Stream A] ───────────────────────────────→ ✓ Finally received
Seg 4 [Stream C] ───────────────────────────────→ ✓ Unblocked
Seg 5 [Stream B] ───────────────────────────────→ ✓ Unblocked
```

**HTTP/3 — No HoL Blocking:**
```
UDP Datagram Timeline:

Pkt 1 [QUIC Stream A] ──→ ✓ Stream A app receives immediately
Pkt 2 [QUIC Stream B] ──→ ✓ Stream B app receives immediately
Pkt 3 [QUIC Stream A] ──→ ✗ LOST
Pkt 4 [QUIC Stream C] ──→ ✓ Stream C app receives immediately ← NO BLOCKING
Pkt 5 [QUIC Stream B] ──→ ✓ Stream B app receives immediately ← NO BLOCKING
                     |
               [Retransmit Pkt 3]
                     |
Pkt 3 [QUIC Stream A] ──→ ✓ Stream A recovers, others unaffected
```

This is the single most impactful improvement HTTP/3 provides.

### Why This Matters for Real Users

On modern mobile networks (LTE, 5G):
- Packet loss is common: 1–5%.
- With 20 concurrent streams and 2% loss, probability at least one stream is blocked = 1 - (0.98)^20 ≈ 33%.
- HTTP/3 eliminates this class of stall entirely.

---

## 10. QUIC Packet Structure

### Overview of Packet Types

QUIC has two main categories of packets:

1. **Long Header Packets**: Used during connection establishment.
2. **Short Header Packets** (1-RTT): Used for application data after handshake.

### Long Header Packet Structure

```
Long Header Packet:
+───────────────────────────────────────────────────────────+
| Byte 0: Header Form (1) | Fixed Bit (1) | Long Packet Type (2) |
|         Reserved (2)    | Packet Number Length (2)            |
+───────────────────────────────────────────────────────────+
| Version (4 bytes) — e.g., 0x00000001 for QUIC v1          |
+───────────────────────────────────────────────────────────+
| DCID Length (1 byte) + Destination Connection ID (0-20 B) |
+───────────────────────────────────────────────────────────+
| SCID Length (1 byte) + Source Connection ID (0-20 B)      |
+───────────────────────────────────────────────────────────+
| Type-specific fields (Token, Length, etc.)                 |
+───────────────────────────────────────────────────────────+
| Packet Number (1-4 bytes, protected by header protection) |
+───────────────────────────────────────────────────────────+
| Payload (QUIC frames, AEAD encrypted)                     |
+───────────────────────────────────────────────────────────+
| AEAD tag (16 bytes)                                       |
+───────────────────────────────────────────────────────────+
```

Long Header Packet Types:
- `Initial (0x00)` — Carries TLS ClientHello / ServerHello.
- `0-RTT (0x01)` — Early application data.
- `Handshake (0x02)` — TLS Handshake continuation.
- `Retry (0x03)` — Server requests address validation.

### Short Header Packet Structure (1-RTT)

After handshake, short header is used (smaller overhead):

```
Short Header (1-RTT) Packet:
+─────────────────────────────────────────────────────────+
| Byte 0: Header Form (0) | Fixed Bit (1) | Spin Bit (1) |
|         Reserved (2)    | Key Phase (1) | PN Len (2)   |
+─────────────────────────────────────────────────────────+
| Destination Connection ID (variable, pre-negotiated)    |
+─────────────────────────────────────────────────────────+
| Packet Number (1-4 bytes, header protected)             |
+─────────────────────────────────────────────────────────+
| Payload (QUIC frames, AEAD encrypted)                   |
+─────────────────────────────────────────────────────────+
| AEAD tag (16 bytes)                                     |
+─────────────────────────────────────────────────────────+
```

### The Spin Bit

The **Spin Bit** (bit 2 of the first byte in short header) is a 1-bit field that **alternates** with each RTT. Network operators can observe this bit (it's not encrypted) to measure RTT without seeing packet contents.

```
Client            Network Probe          Server
  |  spin=0  ─────────────────────────>   |
  |  <─────────────────────────  spin=0   |
  |  [client flips bit]                   |
  |  spin=1  ─────────────────────────>   |
  |           [observer sees flip → RTT]  |
```

### Version Negotiation

If a server doesn't support the client's QUIC version, it sends a **Version Negotiation packet** (not encrypted — it has no keys yet):

```
Version Negotiation Packet:
+─────────────────────────────────────────+
| Header Form (1) | Unused (7 bits)        |
+─────────────────────────────────────────+
| Version = 0x00000000 (4 bytes)          | ← all zeros = VN packet
+─────────────────────────────────────────+
| DCID, SCID                              |
+─────────────────────────────────────────+
| Supported Version 1 (4 bytes)           |
| Supported Version 2 (4 bytes)           |
| ...                                     |
+─────────────────────────────────────────+
```

### Coalescing Packets

Multiple QUIC packets (of different types) can be **coalesced into a single UDP datagram**. This reduces overhead:

```
Single UDP Datagram:
+──────────────────────────────────────────────────────+
| UDP Header                                           |
+──────────────────────────────────────────────────────+
| QUIC Initial Packet (Long Header)                    |
|   [TLS ClientHello]                                  |
+──────────────────────────────────────────────────────+
| QUIC 0-RTT Packet (Long Header)                      |
|   [Early HTTP/3 data]                                |
+──────────────────────────────────────────────────────+
```

The receiver identifies packet boundaries from the Length fields.

---

## 11. QUIC Frame Types

QUIC packets carry **frames** in their payload. A frame is a unit of protocol action. Unlike TCP (which has only one data format), QUIC has many specialized frame types.

### Complete Frame Type Table

| Frame Type    | Value  | Purpose                                    |
|--------------|--------|--------------------------------------------|
| PADDING       | 0x00   | Fill packet to desired size                |
| PING          | 0x01   | Elicit an ACK (keep-alive)                 |
| ACK           | 0x02/03| Acknowledge received packets               |
| RESET_STREAM  | 0x04   | Abruptly terminate a stream (sender)       |
| STOP_SENDING  | 0x05   | Request stream reset (receiver)            |
| CRYPTO        | 0x06   | TLS handshake data                         |
| NEW_TOKEN     | 0x07   | Provide token for future 0-RTT             |
| STREAM        | 0x08-0f| Carry stream data                          |
| MAX_DATA      | 0x10   | Set connection-level flow control limit    |
| MAX_STREAM_DATA| 0x11  | Set stream-level flow control limit        |
| MAX_STREAMS   | 0x12/13| Limit on number of streams                 |
| DATA_BLOCKED  | 0x14   | Sender blocked by connection limit         |
| STREAM_DATA_BLOCKED| 0x15| Sender blocked by stream limit            |
| STREAMS_BLOCKED| 0x16/17| Sender wants more stream quota            |
| NEW_CONNECTION_ID| 0x18| Provide additional connection IDs         |
| RETIRE_CONNECTION_ID| 0x19| Retire a connection ID                 |
| PATH_CHALLENGE| 0x1a   | Verify network path reachability           |
| PATH_RESPONSE | 0x1b   | Respond to PATH_CHALLENGE                  |
| CONNECTION_CLOSE| 0x1c/1d| Close the connection                    |
| HANDSHAKE_DONE| 0x1e   | Signal handshake completion (server→client)|

### STREAM Frame Structure

```
STREAM Frame (type 0x08 to 0x0f):
+─────────────────────────────────────────────────────────+
| Type (1 byte): bits indicate OFF, LEN, FIN flags        |
+─────────────────────────────────────────────────────────+
| Stream ID (variable-length integer)                     |
+─────────────────────────────────────────────────────────+
| [Offset] (variable, present if OFF bit set)             |
+─────────────────────────────────────────────────────────+
| [Length] (variable, present if LEN bit set)             |
+─────────────────────────────────────────────────────────+
| Stream Data (bytes)                                     |
+─────────────────────────────────────────────────────────+
```

- **OFF bit**: Whether Offset field is present (0 = offset is 0).
- **LEN bit**: Whether Length field is present (absent = data continues to end of packet).
- **FIN bit**: Whether this is the final data on the stream.

### ACK Frame Structure

```
ACK Frame (type 0x02):
+──────────────────────────────────────────────────────────+
| Type (0x02 or 0x03)                                      |
+──────────────────────────────────────────────────────────+
| Largest Acknowledged (variable-length int)               |
+──────────────────────────────────────────────────────────+
| ACK Delay (variable-length int) — in microseconds        |
+──────────────────────────────────────────────────────────+
| ACK Range Count (variable-length int)                    |
+──────────────────────────────────────────────────────────+
| First ACK Range (variable-length int)                    |
+──────────────────────────────────────────────────────────+
| [ACK Range (Gap, Range) × ACK Range Count]               |
+──────────────────────────────────────────────────────────+
| [ECN Counts — if type 0x03]                              |
+──────────────────────────────────────────────────────────+
```

QUIC ACKs use **SACK-like range encoding** — the receiver can report gaps (missing packets) and ranges (received blocks) in a single ACK. This is far more efficient than TCP's basic ACK.

### Variable-Length Integer Encoding

QUIC uses a clever variable-length integer (varint) encoding:

```
First 2 bits determine length:
00 = 1 byte  (values 0–63)
01 = 2 bytes (values 0–16383)
10 = 4 bytes (values 0–1073741823)
11 = 8 bytes (values 0–4611686018427387903)

Example: value 151
Binary: 10010111
2-byte varint: 01 000000 10010111
               ^^ prefix = 01 → 2 bytes
```

---

## 12. Flow Control

### Why Flow Control is Needed

Flow control prevents a **fast sender from overwhelming a slow receiver**. If a sender sends data faster than the receiver can process it, the receiver runs out of buffer space and has to drop data — wasting bandwidth.

### Two-Level Flow Control in QUIC

QUIC has flow control at **two levels simultaneously**:

1. **Stream-level flow control**: Limits data on each individual stream.
2. **Connection-level flow control**: Limits total data across all streams combined.

This is more granular than TCP (which only has connection-level).

### How QUIC Flow Control Works

Each stream has a **flow control credit** — a maximum byte offset the sender is allowed to send to.

```
Stream A Flow Control:
                    Initial limit: 65536 bytes
                    
Sender side:         |──── can send ────|
                     0               65536
                     
As receiver reads:
  - Receiver reads 10000 bytes from app buffer
  - Receiver sends MAX_STREAM_DATA(stream A, 75536)
  - Sender can now send up to offset 75536

Diagram:
  [XXXXXXXXXXXXXXXXXX....................]
  0    consumed    ^  ^               limit
                   |  |
               read   buffered (not yet read)
```

### MAX_DATA and MAX_STREAM_DATA

- `MAX_DATA`: Increases the connection-level limit (total bytes across all streams).
- `MAX_STREAM_DATA`: Increases a specific stream's limit.

**Rule:** Sender MUST stop sending if it would exceed the limit. Sending a `DATA_BLOCKED` or `STREAM_DATA_BLOCKED` frame signals the sender is blocked waiting for more credit.

### Flow Control and 0-RTT

In 0-RTT connections, the client uses **remembered flow control limits** from the previous connection (stored in the session ticket). The server can override these on handshake completion.

---

## 13. Congestion Control in QUIC

### What is Congestion Control?

Congestion control prevents a sender from overwhelming the **network** (as opposed to the receiver). If too many senders send too fast, routers drop packets, causing a death spiral.

### TCP Congestion Control Background

TCP's congestion control (Reno/CUBIC) uses:
- **Slow start**: Begin with small window, double each RTT.
- **Congestion avoidance**: Grow linearly after threshold.
- **Fast retransmit**: After 3 duplicate ACKs, retransmit immediately.
- **Fast recovery**: Don't go back to slow start on fast retransmit.

Key metric: **cwnd (Congestion Window)** — max bytes in flight.

### QUIC and Congestion Control

QUIC **does not define a specific congestion control algorithm** — it provides hooks for any algorithm to plug in. The IETF recommends **CUBIC** or **NewReno** as defaults (RFC 9002).

However, QUIC has key advantages for congestion control:

#### Advantage 1: Accurate RTT Measurement

In TCP, if a packet is lost and retransmitted, it's **ambiguous** whether an ACK is for the original or retransmitted packet (the Retransmission Ambiguity problem). This causes RTT measurement errors.

In QUIC:
- Every retransmission gets a **new packet number**.
- ACKs reference specific packet numbers.
- No ambiguity — RTT measurement is precise.

```
TCP (ambiguous):
  Send pkt #100 → lost
  Retransmit pkt #100 → ACK received
  Was ACK for original or retransmit? Unknown! → RTT estimate is wrong.

QUIC (unambiguous):
  Send pkt #100 → lost
  Retransmit same data as pkt #200 → ACK #200 received
  RTT = now - send_time(pkt #200) → Precise!
```

#### Advantage 2: Packet Number Monotonicity

QUIC packet numbers are strictly increasing and never reused. This simplifies:
- Loss detection
- RTT calculation
- Congestion window management

#### Advantage 3: ECN Support

QUIC natively supports **ECN (Explicit Congestion Notification)** — routers can mark packets (instead of dropping) to signal congestion. The receiver reports ECN marks in ACK frames.

### BBR Congestion Control

Many QUIC implementations (especially Google's) use **BBR (Bottleneck Bandwidth and Round-trip time)**, a fundamentally different approach:

- TCP Reno/CUBIC: React to **loss** as signal of congestion.
- BBR: Model the network's **bandwidth and RTT** directly.

BBR measures:
- `BtlBw` — Bottleneck Bandwidth (max delivery rate observed)
- `RTprop` — Round-trip propagation time (min RTT observed)

BBR then sends at exactly the rate the bottleneck can handle, maintaining the minimum queue depth needed. This avoids **bufferbloat** — where TCP fills router queues causing high latency.

```
BBR States:
  STARTUP   → Send faster, estimate BtlBw
  DRAIN     → Drain queue built during startup
  PROBE_BW  → Cruise at optimal rate, periodic probes
  PROBE_RTT → Reduce cwnd to measure min RTT
```

---

## 14. Loss Detection and Recovery

### How QUIC Detects Loss

QUIC uses three mechanisms to detect lost packets:

#### 1. ACK-Based Loss Detection

If packet N is acknowledged but packets N-3, N-2, N-1 are not (i.e., 3 or more packets with higher numbers are acknowledged), the unacknowledged packets are **declared lost** (similar to TCP's 3 duplicate ACK rule).

This is called the **packet threshold** — default value is 3.

```
Sent:  [1][2][3][4][5][6][7][8]
ACKed:  ✓  ✗  ✗  ✓  ✓  ✓  ✓  ✓

Packets 2 and 3 have 3+ higher-numbered packets acknowledged.
→ Packets 2 and 3 declared LOST → retransmit.
```

#### 2. Time Threshold

If a packet is not acknowledged within:
```
max(kTimeThreshold × max(smoothed_rtt, latest_rtt), kGranularity)
```
it is declared lost. `kTimeThreshold` = 9/8 (12.5% more than RTT). This handles reordering.

#### 3. Probe Timeout (PTO)

A **PTO (Probe Timeout)** fires when no acknowledgment is received for a period. On PTO, QUIC sends 1-2 probe packets to elicit an ACK and confirm the path is alive. PTO handles:
- Tail-loss probes (last packet in a send burst is lost).
- Path blackholes (no ACKs at all).

PTO timer:
```
PTO = smoothed_rtt + max(4 × rttvar, kGranularity) + max_ack_delay
```

### Retransmission — NOT the Same Data

**Key QUIC concept:** When QUIC retransmits, it sends the **same logical data** (stream bytes) in a **new packet with a new packet number**.

```
Original: Packet #50 carries Stream 4, bytes 1000-1499
Lost!

Retransmit: Packet #87 carries Stream 4, bytes 1000-1499
            (different packet number, same stream data)
```

This is different from TCP, where retransmitted data has the same sequence number. QUIC's approach makes loss detection unambiguous.

---

## 15. Connection Migration

### What is Connection Migration?

**Connection migration** allows a QUIC connection to survive a change in the client's network address (IP address and/or port) without breaking the connection.

### Why This Matters

Scenario: You're downloading a large file over WiFi, and you walk away from the WiFi router. Your device switches to cellular (4G/5G). Your IP address changes.

- **TCP**: Connection is broken. The 4-tuple (src IP, src port, dst IP, dst port) changes → TCP considers it a new connection → download restarts.
- **QUIC**: Connection migrates seamlessly → download continues without interruption.

### How QUIC Migration Works

QUIC connections are identified by **Connection IDs** (not 4-tuple). When the network path changes:

```
Before migration:
  Client IP: 192.168.1.5:54321 ──→ Server IP: 1.2.3.4:443
  QUIC Connection ID: ABCDEF1234

[WiFi drops, cellular connects]
  Client IP changes to: 10.0.0.2:58000

After migration:
  Client IP: 10.0.0.2:58000 ──→ Server IP: 1.2.3.4:443
  QUIC Connection ID: ABCDEF1234   ← SAME ID

Server sees new 4-tuple but same Connection ID → migration detected.
```

### Path Validation During Migration

When migration is detected, the server must validate the new path to prevent **reflection attacks** (attacker spoofing migration to redirect traffic):

```
Server → Client (new path): PATH_CHALLENGE [random 8-byte token]
Client → Server (new path): PATH_RESPONSE  [same token]
                             ← Server now trusts new path
```

### Preferred Addresses

Servers can advertise a **preferred address** during the handshake. After handshake, the client migrates to that address. Useful for:
- Load balancing (connect to one IP, migrate to optimal server)
- Anycast → unicast migration

---

## 16. Connection IDs

### What is a Connection ID?

A **Connection ID (CID)** is an opaque byte sequence (0-20 bytes) that identifies a QUIC connection **independent of network address**.

Unlike TCP which identifies connections by 4-tuple `(srcIP, srcPort, dstIP, dstPort)`, QUIC uses CIDs. This enables connection migration.

### Multiple Connection IDs

Each endpoint can have **multiple active Connection IDs** simultaneously. This serves two purposes:

1. **Migration**: Use different CID after migration to prevent correlation.
2. **Privacy**: An observer can't link packets before and after migration if CIDs differ.

```
Before migration:
  Packets: [CID=AAAA] [CID=AAAA] [CID=AAAA]

After migration to new network:
  Packets: [CID=BBBB] [CID=BBBB] [CID=BBBB]
           ^^^^^^^^^ new CID, same logical connection
```

### NEW_CONNECTION_ID and RETIRE_CONNECTION_ID

- `NEW_CONNECTION_ID`: Provides the peer with additional CIDs it can use.
- `RETIRE_CONNECTION_ID`: Tells the peer a CID is no longer valid.

This creates a **pool** of available CIDs. Each CID comes with a **Stateless Reset Token** — a secret used to send a stateless reset if connection state is lost.

### CID Length = 0

A CID length of 0 is valid — this means the connection is identified solely by the 4-tuple. This is used when connection migration is not needed (e.g., server-to-server communication).

---

## 17. HTTP/3 — The Application Layer on QUIC

### HTTP/3 vs HTTP/2 Semantics

HTTP/3 preserves HTTP/2's semantics:
- Same methods: `GET`, `POST`, `PUT`, `DELETE`, etc.
- Same status codes: `200`, `404`, `500`, etc.
- Same header fields: `:method`, `:path`, `:authority`, etc.
- Same concept of request/response.

What changes is the **transport and framing layer**.

### HTTP/3 Stream Mapping

HTTP/3 maps HTTP semantics onto QUIC streams:

```
HTTP/3 over QUIC:

Client-initiated bidirectional streams:
  Stream 0:  Request 1 (GET /index.html)
  Stream 4:  Request 2 (GET /style.css)
  Stream 8:  Request 3 (GET /logo.png)
  Stream 12: Request 4 (GET /script.js)

Client-initiated unidirectional streams:
  Stream 2:  HTTP/3 Control Stream (client→server)
  Stream 6:  QPACK Encoder Stream (client→server)
  Stream 10: QPACK Decoder Stream (client→server)

Server-initiated unidirectional streams:
  Stream 3:  HTTP/3 Control Stream (server→client)
  Stream 7:  QPACK Encoder Stream (server→client)
  Stream 11: QPACK Decoder Stream (server→client)
  Stream 15: Push Stream (server-initiated push)
```

### Required Streams

Immediately after the QUIC handshake, both endpoints MUST open:
1. **HTTP/3 Control Stream** — for HTTP/3 settings and connection-level frames.
2. **QPACK Encoder Stream** — for sending QPACK encoder instructions.
3. **QPACK Decoder Stream** — for sending QPACK decoder acknowledgments.

These 3 streams MUST remain open for the life of the connection.

### The SETTINGS Frame

The first frame on the control stream MUST be a `SETTINGS` frame:

```
SETTINGS Frame:
+──────────────────────────────────────────────────────+
| Frame Type: SETTINGS (0x04)                          |
+──────────────────────────────────────────────────────+
| Frame Length (varint)                                |
+──────────────────────────────────────────────────────+
| Setting Identifier 1 (varint)                        |
| Setting Value 1 (varint)                             |
| Setting Identifier 2 (varint)                        |
| Setting Value 2 (varint)                             |
| ...                                                  |
+──────────────────────────────────────────────────────+
```

Common HTTP/3 settings:
- `SETTINGS_MAX_FIELD_SECTION_SIZE (0x06)`: Max header section size.
- `SETTINGS_QPACK_MAX_TABLE_CAPACITY (0x01)`: QPACK dynamic table size.
- `SETTINGS_QPACK_BLOCKED_STREAMS (0x07)`: Max streams that can be blocked on QPACK.

---

## 18. HTTP/3 Framing Layer

### HTTP/3 Frame Format

Every HTTP/3 frame has this structure:
```
+───────────────────────────────────────────────────+
| Type (varint)                                     |
+───────────────────────────────────────────────────+
| Length (varint) — number of bytes in Payload      |
+───────────────────────────────────────────────────+
| Payload (Length bytes)                            |
+───────────────────────────────────────────────────+
```

### HTTP/3 Frame Types

| Type Value | Frame Name   | Description                               |
|-----------|--------------|-------------------------------------------|
| 0x00      | DATA         | Request/response body                     |
| 0x01      | HEADERS      | Compressed headers (QPACK encoded)        |
| 0x04      | SETTINGS     | Connection-level settings                 |
| 0x05      | PUSH_PROMISE | Server push advertisement                 |
| 0x07      | GOAWAY       | Initiate graceful shutdown                |
| 0x0d      | MAX_PUSH_ID  | Limit server push IDs                     |

### Request/Response Framing

A complete HTTP/3 request:
```
Client QUIC Stream 0 (bidirectional):

  ┌─────────────────────────────────────────┐
  │ HEADERS frame                           │
  │ [QPACK-compressed request headers]      │
  │ :method = GET                           │
  │ :path = /api/data                       │
  │ :authority = example.com               │
  │ :scheme = https                         │
  │ accept = application/json               │
  └─────────────────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │ DATA frame (optional, for POST/PUT)     │
  │ [Request body bytes]                    │
  └─────────────────────────────────────────┘

Server response on same stream:

  ┌─────────────────────────────────────────┐
  │ HEADERS frame                           │
  │ [QPACK-compressed response headers]     │
  │ :status = 200                           │
  │ content-type = application/json         │
  │ content-length = 1234                   │
  └─────────────────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │ DATA frame                              │
  │ {"key": "value", ...}                   │
  └─────────────────────────────────────────┘
```

### GOAWAY Frame

The `GOAWAY` frame initiates graceful connection shutdown:
- Server sends `GOAWAY` with the **last processed stream ID**.
- All streams before that ID were processed.
- Client should not start new streams after `GOAWAY`.
- Existing streams continue until complete.

```
+──────────────────────────────+
| Type: GOAWAY (0x07)          |
+──────────────────────────────+
| Length                       |
+──────────────────────────────+
| Stream ID (varint)           | ← last processed stream
+──────────────────────────────+
```

---

## 19. QPACK — Header Compression in HTTP/3

### What is Header Compression?

HTTP headers are sent with **every request and response**. Consider a typical request:
```
GET /api/endpoint HTTP/1.1
Host: api.example.com
Cookie: session=AbCdEfGh12345678...
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
```

This is 500-1000 bytes of headers per request. If you make 100 requests, that's 50-100 KB of header overhead. Header compression reduces this dramatically.

### Why Not Use HPACK (HTTP/2's Compression)?

**HPACK** uses a **dynamic table** — a shared dictionary of previously seen header name-value pairs. Both endpoints maintain synchronized copies.

Problem in QUIC: **Out-of-order delivery**.

HPACK requires that header blocks are processed **in order**. If request N's headers reference a dynamic table entry added by request N-1, and request N-1's headers arrive after request N's, the decoder is out of sync — this is **HPACK decoding error**, crashing the connection.

QUIC streams can deliver data independently, potentially out of order. Using HPACK over QUIC would reintroduce HoL blocking (you'd need to order header delivery even if bodies are independent).

### QPACK Design Philosophy

**QPACK** (RFC 9204) solves this with a key insight: **separate the header encoding from the dynamic table updates**. 

QPACK uses **3 separate communication channels**:
1. **Request/response streams**: Carry encoded headers.
2. **Encoder stream**: Carries dynamic table insert instructions (unidirectional, server→client and client→server).
3. **Decoder stream**: Carries acknowledgments of table insertions (unidirectional).

```
QPACK Architecture:

  Client                              Server
    │                                   │
    │◄──── Encoder Stream (S→C) ────────│
    │──── Decoder Stream (C→S) ────────►│
    │                                   │
    │──── Request Stream 0 ────────────►│
    │     (HEADERS: uses QPACK)         │
    │◄─── Response on Stream 0 ─────────│
    │                                   │
    │──── Request Stream 4 ────────────►│
    │◄─── Response on Stream 4 ─────────│
```

### QPACK Static Table

QPACK has a **62-entry static table** of the most common header name-value pairs (e.g., `:method GET`, `:status 200`, `content-type text/html`, etc.). These are always available, no synchronization needed.

```
Static Table (partial):
+─────+────────────────────────────────────────+
| Idx | Name              | Value              |
+─────+────────────────────────────────────────+
|  0  | :authority        |                    |
|  1  | :path             | /                  |
|  2  | age               | 0                  |
|  3  | content-disposition|                   |
|  4  | content-length    | 0                  |
|  5  | cookie            |                    |
|  6  | date              |                    |
|  7  | etag              |                    |
|  8  | if-modified-since |                    |
|  9  | if-none-match     |                    |
| ... | ...               | ...                |
| 15  | :method           | CONNECT            |
| 16  | :method           | DELETE             |
| 17  | :method           | GET                |
| 18  | :method           | HEAD               |
| 19  | :method           | OPTIONS            |
| 20  | :method           | POST               |
| 21  | :method           | PUT                |
| 22  | :scheme           | http               |
| 23  | :scheme           | https              |
| 24  | :status           | 103                |
| 25  | :status           | 200                |
| 26  | :status           | 304                |
| 27  | :status           | 404                |
| 28  | :status           | 503                |
+─────+────────────────────────────────────────+
```

### QPACK Dynamic Table

The **dynamic table** caches header pairs seen during the connection. Unlike HPACK, QPACK's dynamic table handles out-of-order streams via **Required Insert Count**:

Every QPACK-encoded header block includes a **Required Insert Count (RIC)** — the minimum number of dynamic table insertions the decoder must have processed before it can decode this block.

```
Encoder inserts: "content-type: application/json" → dynamic table entry #0
Encoder inserts: "x-custom: value123"              → dynamic table entry #1

Header block for Request 5:
  Required Insert Count = 2  ← need at least 2 entries in dynamic table
  Reference: dynamic entry #1 (x-custom: value123)

If decoder has only processed 1 insertion:
  → Cannot decode Request 5 yet
  → Block this stream until insert count reaches 2
  → Other streams (not needing entry #1) continue normally
```

This stream-level blocking is **deliberate and isolated** — only streams depending on unacknowledged table entries are blocked, not all streams.

### QPACK Encoding Modes

QPACK headers can be encoded in several ways:

1. **Indexed Representation**: Reference a static or dynamic table entry by index (tiny — 1-2 bytes).
2. **Literal with Name Reference**: Use a table name, supply a new value.
3. **Literal without Name Reference**: Encode name and value as raw strings.
4. **Post-Base Indexing**: Reference a dynamic entry that was added *after* the base index (forward reference).

### QPACK Encoder Instructions

Sent on the encoder stream:
- `Insert with Name Reference`: Insert a new entry using an existing table name.
- `Insert with Literal Name`: Insert a completely new name-value pair.
- `Set Dynamic Table Capacity`: Update the maximum table size.
- `Duplicate`: Insert a copy of an existing entry (moves it to front for LRU efficiency).

### QPACK Decoder Instructions

Sent on the decoder stream:
- `Section Acknowledgment`: Decoder finished processing a header block → encoder can evict referenced entries.
- `Stream Cancellation`: Stream was cancelled → encoder should not wait for acks from it.
- `Insert Count Increment`: Tells encoder how many dynamic table entries decoder has processed.

---

## 20. HPACK vs QPACK — The Deep Comparison

```
+────────────────────────┬────────────────────┬───────────────────────────+
| Feature                │ HPACK (HTTP/2)     │ QPACK (HTTP/3)            |
+────────────────────────┼────────────────────┼───────────────────────────+
| Transport              │ TCP (ordered)      │ QUIC (unordered streams)  |
| Static table size      │ 61 entries         │ 99 entries                |
| Dynamic table          │ Yes, mandatory     │ Yes, optional             |
| Out-of-order handling  │ Not needed (TCP)   │ Required Insert Count     |
| HoL blocking           │ TCP-level          │ Per-stream, isolated      |
| Encoder stream         │ None (in-band)     │ Separate QUIC stream      |
| Decoder stream         │ None               │ Separate QUIC stream      |
| Literal encoding       │ Never-indexed flag │ Never-indexed flag        |
| Huffman encoding       │ Yes                │ Yes                       |
| Forward references     │ No                 │ Yes (post-base indexing)  |
| Compression ratio      │ High               │ Similar (slightly lower)  |
| Complexity             │ Lower              │ Higher                    |
+────────────────────────┴────────────────────┴───────────────────────────+
```

### Trade-off

QPACK achieves slightly lower compression than HPACK in some cases because:
- It cannot always safely reference dynamic table entries (might cause HoL blocking).
- Some implementations use **literal-only mode** (no dynamic table) to avoid complexity.

In practice, the difference is small (QPACK ≈ 95% of HPACK compression ratio) and the elimination of HOL blocking is worth it.

---

## 21. HTTP/3 Request/Response Lifecycle

### Complete End-to-End Flow

```
Time 0ms:
  Client                              Server
    │                                    │
    │ UDP packet (QUIC Initial +         │
    │  TLS ClientHello)  ─────────────► │
    │                                    │
    │                   100ms later      │
    │◄──────────────────────────────────│
    │ QUIC Initial (ServerHello)         │
    │ QUIC Handshake (Certificate,       │
    │   CertVerify, Finished)            │
    │ QUIC 1-RTT (HANDSHAKE_DONE)        │
    │                                    │
    │ QUIC Handshake (Finished)          │
    │ QUIC 1-RTT:                        │
    │   Stream 2: Control (SETTINGS)     │
    │   Stream 6: QPACK Encoder          │
    │   Stream 10: QPACK Decoder         │
    │   Stream 0: HEADERS frame          │
    │     (:method GET, :path /)  ─────►│
    │                                    │
    │              100ms later           │
    │◄───────────────────────────────────│
    │ QUIC 1-RTT:                        │
    │   Stream 3: Control (SETTINGS)     │
    │   Stream 7: QPACK Encoder          │
    │   Stream 11: QPACK Decoder         │
    │   Stream 0: HEADERS frame          │
    │     (:status 200,                  │
    │      content-type text/html)       │
    │   Stream 0: DATA frame             │
    │     (<html>...</html>)             │
    │                                    │
    │ Connection continues...            │
```

### Trailers (HTTP Trailers)

HTTP/3 supports **trailers** — headers sent *after* the response body. Used for:
- Checksums computed over the body (e.g., `Digest:` header).
- Transfer metadata not known until the body is complete.

```
Stream 0 (server sends):
  HEADERS frame  ← response headers (:status 200, content-type, ...)
  DATA frame     ← body bytes
  DATA frame     ← more body bytes
  HEADERS frame  ← trailer headers (Digest: sha256=ABC..., Timing-Allow-Origin: *)
  FIN bit set    ← stream complete
```

---

## 22. Server Push in HTTP/3

### What is Server Push?

Server Push allows a server to **proactively send resources** the client will need, before the client requests them.

Example: Client requests `/index.html`. Server knows the page needs `/style.css` and `/logo.png`. Server pushes these immediately alongside the HTML response.

### HTTP/3 Server Push

In HTTP/3, server push is done via:
1. Server sends a `PUSH_PROMISE` frame on the request stream.
2. Server opens a **server-initiated unidirectional stream** (odd stream IDs: 3, 7, 11...).
3. Server sends `HEADERS` + `DATA` frames on that push stream.

```
Stream 0 (HTML request/response):
  → HEADERS (GET /)
  ← HEADERS (200 OK)
  ← PUSH_PROMISE [push_id=0, path=/style.css]  ← "I'm about to push this"
  ← PUSH_PROMISE [push_id=1, path=/logo.png]
  ← DATA (<html>...</html>)

Stream 3 (Server Push, push_id=0):
  ← HEADERS (:status 200, content-type text/css)
  ← DATA (body of style.css)

Stream 7 (Server Push, push_id=1):
  ← HEADERS (:status 200, content-type image/png)
  ← DATA (PNG bytes)
```

### MAX_PUSH_ID Frame

Clients control how many pushes they accept:
```
MAX_PUSH_ID frame on control stream:
  ← MAX_PUSH_ID [push_id = 5]   ← server may not exceed push ID 5
```

Clients can cancel an unwanted push with `CANCEL_PUSH` frame.

### Push in Practice

Server push was **deprecated in Chrome** for HTTP/2 and has limited adoption in HTTP/3. Reasons:
- Hard to predict what the client needs (client might have it cached).
- Push consumes bandwidth for resources client already has.
- Better alternatives: `Link: rel=preload` hints, 103 Early Hints response.

---

## 23. Prioritization in HTTP/3

### The Need for Prioritization

Not all HTTP/3 streams are equal. A browser rendering a page needs to prioritize:
1. HTML (to build DOM)
2. Render-blocking CSS (to paint page)
3. Images (visible, lazy)
4. Analytics scripts (defer)

### HTTP/3 Extensible Priorities (RFC 9218)

HTTP/3 uses the **Extensible Priorities** scheme (separate from HTTP/2's complex stream dependency tree):

Each stream has:
- **Urgency** (0-7): 0 = highest urgency, 7 = lowest. Servers drain higher urgency streams first.
- **Incremental** (boolean): Whether the resource can be partially processed. `true` = interleave with other streams of same urgency.

```
Priority scheme examples:

:priority: u=0         ← urgency=0 (highest), incremental=false
:priority: u=3, i      ← urgency=3, incremental=true
:priority: u=7, i=?1   ← urgency=7, incremental=true (structured field)
```

### PRIORITY_UPDATE Frame

Priorities can be changed dynamically via `PRIORITY_UPDATE` frames on the control stream:

```
PRIORITY_UPDATE:
  Prioritized Element Type: REQUEST_STREAM
  Prioritized Element ID: 4  (Stream 4)
  Priority Field Value: u=1  (urgency raised to 1)
```

This allows JavaScript to dynamically reprioritize resources as the page loads.

---

## 24. QUIC vs TCP Comparison — Every Dimension

```
+───────────────────────────────┬───────────────────┬───────────────────────+
| Dimension                     │ TCP               │ QUIC                  |
+───────────────────────────────┼───────────────────┼───────────────────────+
| Transport layer               │ L4 (kernel)       │ L4 (user-space)       |
| Base protocol                 │ IP                │ UDP                   |
| Connection establishment      │ 3-way handshake   │ Combined with TLS     |
| New connection latency        │ 2-3 RTTs          │ 1 RTT                 |
| Resumed connection latency    │ 1-2 RTTs          │ 0 RTT                 |
| Encryption                    │ Optional (TLS)    │ Mandatory (TLS 1.3)   |
| Multiplexing                  │ None (app level)  │ Native streams        |
| HoL blocking                  │ Yes               │ No                    |
| Packet ordering               │ Strict (all)      │ Per-stream            |
| Connection identity           │ 4-tuple           │ Connection ID         |
| Connection migration          │ No                │ Yes                   |
| Packet numbering              │ Seq numbers reused│ Monotonically increasing|
| RTT measurement               │ Ambiguous         │ Precise               |
| Loss detection                │ Limited SACK      │ ACK ranges + PTO      |
| Congestion control            │ Fixed (OS)        │ Pluggable             |
| Flow control                  │ Connection-level  │ Per-stream + connection|
| Header compression            │ None              │ QPACK                 |
| Header protection             │ No                │ Yes                   |
| Middlebox friendliness        │ High              │ Moderate              |
| CPU overhead                  │ Lower             │ Higher (encryption)   |
| Kernel changes needed         │ Required          │ No (user-space)       |
| Deployment speed              │ Slow (OS updates) │ Fast (app updates)    |
| Protocol ossification         │ Severe            │ Reduced               |
+───────────────────────────────┴───────────────────┴───────────────────────+
```

---

## 25. HTTP Versions Comparison

```
+──────────────────────────┬──────────────┬──────────────┬────────────────+
| Feature                  │ HTTP/1.1     │ HTTP/2       │ HTTP/3         |
+──────────────────────────┼──────────────┼──────────────┼────────────────+
| Format                   │ Text         │ Binary       │ Binary         |
| Transport                │ TCP          │ TCP          │ QUIC/UDP       |
| Connections per host     │ 6 (browser)  │ 1            │ 1              |
| Multiplexing             │ No (pipeline)│ Yes          │ Yes            |
| Header compression       │ None         │ HPACK        │ QPACK          |
| Server push              │ No           │ Yes          │ Yes (limited)  |
| Stream prioritization    │ No           │ Complex tree │ Extensible     |
| HoL blocking (app-level) │ Yes          │ No           │ No             |
| HoL blocking (TCP-level) │ Yes          │ Yes          │ No (QUIC)      |
| TLS required             │ No (HTTPS)   │ Effectively  │ Yes (always)   |
| Connection migration     │ No           │ No           │ Yes            |
| 0-RTT reconnection       │ No           │ No           │ Yes            |
| ALPN negotiation         │ Optional     │ h2           │ h3             |
| RFC                      │ 9110-9117    │ 7540         │ 9114           |
| Year                     │ 1997         │ 2015         │ 2022           |
+──────────────────────────┴──────────────┴──────────────┴────────────────+
```

### Network Stack Comparison

```
HTTP/1.1 Stack:             HTTP/2 Stack:              HTTP/3 Stack:

Application                 Application                Application
    │                           │                           │
    │ HTTP/1.1 (text)           │ HTTP/2 (binary frames)    │ HTTP/3 (binary)
    │                           │                           │
    │ TLS 1.3 (optional)        │ TLS 1.3                   │ QUIC (includes TLS 1.3)
    │                           │                           │
    │ TCP                       │ TCP                       │ UDP
    │                           │                           │
    │ IP                        │ IP                        │ IP
    ▼                           ▼                           ▼
 Network                     Network                    Network
```

---

## 26. Performance Characteristics

### Latency

| Scenario                    | HTTP/1.1+TLS | HTTP/2+TLS | HTTP/3    |
|----------------------------|-------------|------------|-----------|
| New connection (100ms RTT) | 300ms        | 300ms      | 200ms     |
| Resumed connection         | 200ms        | 200ms      | 100ms (0-RTT) |
| 0% packet loss             | Baseline     | 2× faster  | 2.5× faster |
| 1% packet loss             | Baseline     | Slower     | 3× faster  |
| 5% packet loss (mobile)    | Baseline     | 3× slower  | 2× faster  |

### Throughput

- On clean networks: HTTP/2 ≈ HTTP/3 (both fully utilize bandwidth).
- On lossy networks: HTTP/3 significantly better (no TCP HoL blocking).
- High-latency satellite links: HTTP/3 much better (0-RTT + no HoL blocking).

### CPU Overhead

QUIC has higher CPU overhead than TCP because:
1. Every packet is AEAD encrypted/decrypted (TLS is mandatory).
2. QUIC runs in user-space (no kernel offloading for checksums, etc.).
3. Packet processing at UDP level is less optimized in OS.

Google reports ~2× CPU overhead for QUIC vs TCP for the same traffic. This is improving as hardware and software optimize.

### Real-World Measurements

- **Google**: HTTP/3 (gQUIC) reduced page load latency by 3-8%.
- **Facebook**: 8% reduction in request delay, 20% reduction in tail latency.
- **Akamai**: 13% faster page loads on mobile networks.
- **Cloudflare**: 17% faster TTFB (Time to First Byte) over HTTP/3.

Tail latency (99th percentile) sees the most improvement — the worst cases get dramatically better.

---

## 27. Security Model

### Mandatory Encryption

Every QUIC packet (after Initial) is encrypted. There is no plaintext QUIC. This means:
- No passive interception of application data.
- No injection of fake QUIC packets (AEAD authentication).
- Limited traffic analysis (header protection, connection ID rotation).

### What Observers Can See

Even with QUIC's encryption, a network observer can see:
- The destination IP and port.
- Packet timing and sizes.
- Connection establishment (Initial packets are weakly protected).
- The SNI (Server Name Indication) in the TLS ClientHello — unless **ECH (Encrypted Client Hello)** is used.
- Spin bit (for RTT estimation).
- QUIC version.

### ECH — Encrypted Client Hello

ECH (RFC draft) encrypts the TLS ClientHello using the server's public key (obtained via DNS HTTPS records). This hides:
- SNI (which server you're connecting to).
- ALPN (which protocol you're using).

### Anti-Amplification

QUIC protects against **UDP amplification attacks** (attacker sends small spoofed packet, server sends large response to victim):

- Before address validation, server limits response to **3× the bytes received**.
- Server sends a `Retry` packet to force client to prove its address.
- Only after address validation can server send unlimited data.

```
Amplification limit:
  Client sends 1200-byte Initial
  Server can send at most 3600 bytes (3×)
  Server sends Retry or waits for more from client
```

### Stateless Reset

If a QUIC endpoint loses connection state (e.g., server restart), it can send a **Stateless Reset** to cleanly terminate the connection:

```
Stateless Reset Packet:
+────────────────────────────────────────+
| Random bytes (looks like a 1-RTT pkt) |
+────────────────────────────────────────+
| Stateless Reset Token (16 bytes)       | ← matches token from NEW_CONNECTION_ID
+────────────────────────────────────────+
```

The peer recognizes the token and closes the connection without waiting for timeout.

---

## 28. Ossification and Why QUIC Uses UDP

### What is Protocol Ossification?

**Protocol ossification** is when a protocol becomes impossible to evolve because middleboxes (firewalls, NATs, load balancers) have been deployed that rely on specific protocol behaviors — including behaviors that were never specified.

**TCP Ossification Example:**
- TCP Option values beyond the original set are often stripped by firewalls.
- TCP middleboxes assume specific flag combinations.
- The MPTCP (Multipath TCP) extension took 10+ years to deploy because it breaks many middleboxes.
- TCP Fast Open was blocked by many firewalls.

### How Deeply TCP is Ossified

Changing TCP to solve HoL blocking would require:
1. OS kernel changes in billions of devices.
2. All middleboxes understanding the new TCP behavior.
3. Years of coordinated rollout.
4. Even then, old devices would break.

This is why Google concluded: **TCP cannot be fixed**. A new protocol is needed.

### Why UDP Was Chosen

UDP is **nearly transparent** to most middleboxes:
- Firewalls generally pass UDP.
- NATs handle UDP (timeout-based state).
- UDP has no protocol-level behavior that middleboxes rely on.

By running QUIC over UDP, protocol evolution happens:
- In user-space code (updateable like any app).
- Without OS changes.
- Without middlebox awareness.

### QUIC's Defense Against Ossification

QUIC encrypts everything possible to prevent middleboxes from making assumptions:
- Packet numbers are header-protected.
- All frames are encrypted.
- Only the connection ID and version are observable (and version negotiation handles mismatches).

The **Grease (Generate Random Extensions And Sustain Extensibility)** technique is used: QUIC implementations send random unknown frame types and transport parameters to ensure that middleboxes and implementations don't reject unknown values (they must ignore them per spec).

---

## 29. NAT Traversal and Middleboxes

### NAT and UDP

**NAT (Network Address Translation)** maps private IP:port pairs to public IP:port. For UDP, NAT maintains a state table with timeouts (since UDP has no connection-close signal).

Challenge: If a QUIC connection is idle, the NAT mapping may expire. The connection appears alive to endpoints but packets are being dropped.

**QUIC's solution:** `PING` frames keep the connection alive and the NAT mapping fresh.

### Port 443 UDP

HTTP/3 runs on **UDP port 443** (same port as HTTPS/TLS, but TCP vs UDP). Most firewalls allow UDP port 443 because they see the port number and assume it's benign.

Some enterprise firewalls block all UDP except DNS (port 53). In this case, HTTP/3 cannot be used, and the client falls back to HTTP/2 or HTTP/1.1 over TCP.

### QUIC and Load Balancers

Traditional load balancers route connections based on TCP 4-tuple. With QUIC:
- Connection IDs enable consistent routing.
- **QUIC-LB (RFC 9386)** defines how Connection IDs encode routing information for load balancers.

```
Connection ID structure for load balancing:
  [LB config ID (1 byte)][Server ID (encoded)][Random bytes]
  ─────────────────────────────────────────────────────────
  Load balancer decodes server ID from CID → routes to correct backend
  Even after client migration, same CID → same backend
```

---

## 30. HTTP/3 in Practice — Deployment, Discovery, Alt-Svc

### How Does a Client Know to Use HTTP/3?

A client doesn't know in advance if a server supports HTTP/3. Discovery happens via:

#### Method 1: Alt-Svc Response Header

The server advertises HTTP/3 support in an HTTP/2 or HTTP/1.1 response:

```
HTTP/2 Response:
HTTP/2 200 OK
Alt-Svc: h3=":443"; ma=86400
Content-Type: text/html
```

- `h3` = HTTP/3 (QUIC v1).
- `:443` = same host, port 443.
- `ma=86400` = max-age 86400 seconds (cache this for 1 day).

On the next visit, the client can try HTTP/3 directly.

#### Method 2: HTTPS DNS Record (SVCB/HTTPS RR)

RFC 9460 defines a DNS HTTPS resource record:
```
example.com. HTTPS 1 . alpn="h3,h2" port=443
```

This tells the client before the first connection that HTTP/3 is supported. Enables **0-RTT first connection** with HTTP/3!

#### Method 3: Alt-Svc on UDP QUIC

If the client already knows (from cache) to use HTTP/3, it connects directly over UDP port 443 with `h3` ALPN.

### ALPN Negotiation

**ALPN (Application Layer Protocol Negotiation)** is a TLS extension where client and server negotiate which application protocol to use during the TLS handshake.

For HTTP/3:
- Client includes `h3` in its ALPN list.
- Server responds with `h3` if it supports it.
- This happens inside the QUIC TLS handshake.

```
TLS ClientHello extensions:
  ALPN: ["h3", "h2", "http/1.1"]  ← preference order

Server selects "h3":
  TLS ServerHello:
    ALPN: "h3"
```

### Fallback Strategy

Browsers implement **Happy Eyeballs v2** for QUIC:
1. Start HTTP/3 connection (UDP).
2. Simultaneously start HTTP/2 connection (TCP) with a 250ms delay.
3. Use whichever completes first.
4. If HTTP/3 fails, blacklist it and use TCP.

This ensures users never experience degradation from HTTP/3 failures.

### Current HTTP/3 Adoption (as of 2024-2025)

- **Cloudflare**: 100% of traffic supports HTTP/3.
- **Google**: All Google services support HTTP/3.
- **Meta/Facebook**: Full HTTP/3 support.
- **Browser support**: Chrome, Firefox, Safari, Edge all support HTTP/3.
- **Web adoption**: ~30% of the top 10 million websites support HTTP/3.
- **Traffic share**: ~27% of all web traffic uses HTTP/3 (W3Techs data).

---

## 31. QUIC Versions and the IETF Standard

### Version History

| Version      | Description                              | Status          |
|-------------|------------------------------------------|-----------------|
| gQUIC (2013-2018) | Google's original implementation  | Deprecated      |
| draft-00 to draft-34 | IETF working group iterations  | Historical      |
| QUIC v1 (0x00000001) | RFC 9000, May 2021             | **Current**     |
| QUIC v2 (0x6b3343cf) | RFC 9369, 2023                | Deployed        |

### QUIC v2 (RFC 9369)

QUIC v2 is functionally identical to v1 with minor changes:
- Different initial salt (changes Initial packet encryption).
- Different retry token integrity key.
- Purpose: **Greasing** — ensures clients and servers handle version negotiation correctly. Prevents ossification of QUIC v1 as the only valid version.

### HTTP/3 over QUIC v2

HTTP/3 can run over QUIC v1 or v2. The ALPN for QUIC v2 is `h3` (same as v1 — HTTP/3 is independent of QUIC version).

---

## 32. Implementation Landscape

### Server Implementations

| Implementation | Language | Notes                          |
|---------------|----------|--------------------------------|
| **nginx** (quic branch) | C | Mainstream web server |
| **Caddy** | Go | Native HTTP/3 support |
| **quiche** (Cloudflare) | Rust | Production-grade, used by Cloudflare |
| **msquic** (Microsoft) | C | Used in Windows, .NET |
| **quic-go** | Go | Pure Go, used in many projects |
| **lsquic** (LiteSpeed) | C | High performance |
| **aioquic** | Python | Python async |
| **ngtcp2** | C | Low-level QUIC library |
| **s2n-quic** (AWS) | Rust | AWS production library |

### Client Implementations

| Browser/Client | QUIC Support |
|---------------|-------------|
| Chrome/Chromium | Full HTTP/3 (QUIC v1) |
| Firefox | Full HTTP/3 |
| Safari (WebKit) | HTTP/3 |
| curl | HTTP/3 with quiche or ngtcp2 backend |

### Rust Implementation Example (s2n-quic / Quinn)

```rust
// Using Quinn (QUIC implementation in pure Rust)
use quinn::{ClientConfig, Endpoint};
use std::net::SocketAddr;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Create client config with TLS
    let client_config = ClientConfig::with_native_roots()?;
    
    // Bind to local UDP socket
    let mut endpoint = Endpoint::client("0.0.0.0:0".parse()?)?;
    endpoint.set_default_client_config(client_config);
    
    // Connect to server
    let server_addr: SocketAddr = "93.184.216.34:443".parse()?;
    let connection = endpoint
        .connect(server_addr, "example.com")?
        .await?;
    
    println!("Connected to server: {}", connection.remote_address());
    
    // Open a bidirectional stream
    let (mut send, mut recv) = connection.open_bi().await?;
    
    // Send HTTP/3-like request (simplified)
    send.write_all(b"GET / HTTP/3\r\n").await?;
    send.finish().await?;
    
    // Read response
    let response = recv.read_to_end(1024 * 1024).await?;
    println!("Response: {} bytes", response.len());
    
    Ok(())
}
```

### Go Implementation Example (quic-go)

```go
package main

import (
    "context"
    "crypto/tls"
    "fmt"
    "io"
    "log"

    "github.com/quic-go/quic-go"
    "github.com/quic-go/quic-go/http3"
    "net/http"
)

func main() {
    // HTTP/3 client using quic-go
    roundTripper := &http3.RoundTripper{
        TLSClientConfig: &tls.Config{
            InsecureSkipVerify: false, // always true in prod!
        },
        QuicConfig: &quic.Config{
            MaxIdleTimeout:        30 * time.Second,
            KeepAlivePeriod:       10 * time.Second,
        },
    }
    defer roundTripper.Close()

    client := &http.Client{Transport: roundTripper}

    resp, err := client.Get("https://example.com")
    if err != nil {
        log.Fatal(err)
    }
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)
    fmt.Printf("Status: %s\n", resp.Proto) // Should print "HTTP/3.0"
    fmt.Printf("Body length: %d bytes\n", len(body))
}
```

### Verifying HTTP/3 Usage

With `curl` (built with HTTP/3 support):
```bash
# Using curl with HTTP/3
curl --http3 -I https://cloudflare.com

# Expected output:
HTTP/3 200
date: Mon, 01 Jan 2024 00:00:00 GMT
content-type: text/html
alt-svc: h3=":443"; ma=86400
```

In Chrome DevTools:
- Network tab → Protocol column shows `h3` for HTTP/3 connections.

---

## 33. Mental Models and Expert Intuition

### Mental Model 1: QUIC as "Virtual TCP Connections in UDP"

Think of QUIC as a **container** running inside a UDP packet. Inside that container:
- Each QUIC stream is like a mini-TCP connection.
- But the container itself doesn't require ordering — only the mini-connections do.
- A stall in one mini-connection doesn't freeze the container.

**Analogy:** HTTP/2 over TCP is like a highway with one lane — if one car breaks down, all cars behind it stop. HTTP/3 over QUIC is like a highway with independent lanes — a breakdown in lane 1 doesn't affect lane 2.

### Mental Model 2: The Separation of Concerns

QUIC cleanly separates:
- **Reliability**: Handled per-stream (not per-connection).
- **Security**: Mandatory, built-in at the packet level.
- **Identity**: Connection ID (not network address).
- **Ordering**: Per-stream (not globally).
- **Congestion**: Connection-level (shared across streams).
- **Flow control**: Both per-stream AND per-connection.

When analyzing any QUIC behavior, ask: "Which layer handles this? Stream? Connection? Crypto?"

### Mental Model 3: Every Design Decision Traces to a Problem

| HTTP/3 Feature            | Problem it Solves                              |
|--------------------------|------------------------------------------------|
| QUIC over UDP            | TCP ossification, HoL blocking                 |
| Mandatory TLS 1.3        | Security + ossification prevention             |
| Connection IDs           | Mobile connection migration                    |
| Stream independence       | TCP HoL blocking                               |
| 0-RTT                    | Reconnection latency                           |
| QPACK (not HPACK)        | HPACK requires ordered delivery (not in QUIC)  |
| Header protection        | Traffic analysis / fingerprinting              |
| Per-stream flow control  | Slow streams don't consume connection credit   |
| PTO (probe timeout)      | Tail loss not detected by ACK-based methods    |

**Master insight:** Every protocol feature is a tradeoff. To understand HTTP/3 deeply, trace every feature back to its problem.

### Mental Model 4: The Reliability Inversion

TCP: Connection is reliable → use it for multiple things → get HoL blocking.
QUIC: Connection is NOT reliable → implement reliability per-stream → no HoL blocking.

The key insight is that **reliability should be scoped to what actually needs it**, not applied globally.

### Mental Model 5: User-Space Liberation

QUIC being in user-space means:
- Deploy updates like software, not OS patches.
- Experiment with congestion control without kernel patches.
- A/B test QUIC versions on live traffic instantly.
- Different processes can run different QUIC configurations.

This is why Google could iterate on QUIC rapidly from 2013-2021 while TCP barely changed.

### Cognitive Framework: Layered Analysis

When debugging or analyzing HTTP/3 performance, apply this layered analysis:

```
Layer 1: Network
  - Packet loss rate? (> 1% hurts TCP more than QUIC)
  - RTT? (high RTT → 0-RTT matters more)
  - UDP blocked? (fallback to TCP)

Layer 2: QUIC Transport
  - Connection establishment time?
  - Connection migration happening?
  - Congestion window utilization?
  - PTO firing frequently? (indicates path issues)

Layer 3: HTTP/3
  - How many streams are concurrent?
  - QPACK blocking? (check SETTINGS_QPACK_BLOCKED_STREAMS)
  - Prioritization correct?

Layer 4: Application
  - Critical path resources identified?
  - Push promises useful or wasted?
  - 0-RTT data safe (idempotent only)?
```

---

## Summary: The Complete HTTP/3 Picture

```
                    HTTP/3 COMPLETE ARCHITECTURE
                    ==============================

 Client                                           Server
   │                                                 │
   │   ┌─────────────────────────────────────────┐   │
   │   │         QUIC Connection                 │   │
   │   │  (identified by Connection ID, not IP)  │   │
   │   │                                         │   │
   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
   │   │  │Stream 0 │ │Stream 4 │ │Stream 8 │  │   │
   │   │  │ Req #1  │ │ Req #2  │ │ Req #3  │  │   │
   │   │  │         │ │         │ │         │  │   │
   │   │  │HEADERS  │ │HEADERS  │ │HEADERS  │  │   │
   │   │  │DATA     │ │DATA     │ │DATA     │  │   │
   │   │  └─────────┘ └─────────┘ └─────────┘  │   │
   │   │                                         │   │
   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
   │   │  │Stream 2 │ │Stream 6 │ │Stream 10│  │   │
   │   │  │ Control │ │QPACK Enc│ │QPACK Dec│  │   │
   │   │  └─────────┘ └─────────┘ └─────────┘  │   │
   │   │                                         │   │
   │   │  All streams → QUIC frames              │   │
   │   │  QUIC frames → Encrypted QUIC packets   │   │
   │   │  QUIC packets → UDP datagrams           │   │
   │   └─────────────────────────────────────────┘   │
   │                                                 │
   │ UDP/IP                                          │
   └─────────────────────────────────────────────────┘

 Key Properties:
  ✓ No TCP HoL blocking (streams independent)
  ✓ 1 RTT new connection, 0 RTT resume
  ✓ TLS 1.3 mandatory encryption
  ✓ Connection migration (switch networks seamlessly)
  ✓ QPACK header compression (no HoL in compression)
  ✓ Precise loss detection (monotonic packet numbers)
  ✓ Per-stream flow control
  ✓ User-space (fast evolution)
```

---

## Reference: Key RFCs

| RFC    | Title                                        | Year |
|--------|----------------------------------------------|------|
| RFC 9000 | QUIC: A UDP-Based Multiplexed and Secure Transport | 2021 |
| RFC 9001 | Using TLS to Secure QUIC                    | 2021 |
| RFC 9002 | QUIC Loss Detection and Congestion Control  | 2021 |
| RFC 9114 | HTTP/3                                      | 2022 |
| RFC 9204 | QPACK: Field Compression for HTTP/3         | 2022 |
| RFC 9218 | Extensible Prioritization Scheme for HTTP   | 2022 |
| RFC 9369 | QUIC Version 2                              | 2023 |
| RFC 9386 | QUIC-LB: Generating Routable QUIC Connection IDs | 2023 |
| RFC 8446 | TLS 1.3                                     | 2018 |
| RFC 9460 | SVCB and HTTPS DNS Resource Records         | 2023 |

---

*"The deeper you understand each protocol layer, the more clearly you see that HTTP/3 is not a replacement for HTTP/2 — it is a complete rethinking of the transport contract. Every constraint of TCP that HTTP/2 worked around, HTTP/3 eliminates at the root."*

Now let me build the full guide. This will be extensive — covering every layer of HTTP/3.Here's your complete HTTP/3 guide — 33 deeply interconnected sections covering every concept from first principles. Here's what's inside and why each section matters for building a truly strong mental model:

**The learning path the guide takes:**
- **Sections 1–2**: Builds the *"why"* — you can't appreciate HTTP/3 without feeling the pain of TCP HoL blocking viscerally. Every diagram shows exactly which bytes stall and why.
- **Sections 3–7**: QUIC's foundations — UDP, the combined TLS 1.3 handshake, and why 0-RTT is both powerful and dangerous.
- **Sections 8–14**: The engine room — streams, multiplexing, packet anatomy, every frame type, flow control at two levels, congestion control, and precise loss detection.
- **Sections 15–16**: Connection migration and Connection IDs — the features that make QUIC feel magical on mobile.
- **Sections 17–23**: HTTP/3 as an application layer — framing, QPACK (and *why* HPACK couldn't work), request lifecycle, server push, and prioritization.
- **Sections 24–29**: The comparative and strategic view — QUIC vs TCP, all HTTP versions, real performance numbers, security model, and the deep insight about *ossification*.
- **Sections 30–33**: Practical deployment and — most importantly — the **mental models section**, which shows you how an expert thinks about HTTP/3 as a system of design decisions, not facts to memorize.

**The single most important insight to internalize:** Every feature in HTTP/3 is a direct consequence of one principle — *reliability should be scoped to what actually needs it, not applied globally*. TCP's global ordered delivery guarantee was the root of all HTTP/2's remaining problems. QUIC inverts this at the transport layer.