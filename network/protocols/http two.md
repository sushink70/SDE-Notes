# HTTP/2: Complete, In-Depth Protocol Guide
## From Wire Bytes to Mental Models — C & Rust Implementations

---

## Table of Contents

1. [Why HTTP/2 Exists: The Fundamental Problems](#1-why-http2-exists)
2. [Protocol Overview and Design Philosophy](#2-protocol-overview)
3. [Connection Establishment and TLS ALPN](#3-connection-establishment)
4. [The Binary Framing Layer](#4-binary-framing-layer)
5. [Frame Types — Every Field, Every Bit](#5-frame-types)
6. [Streams: Multiplexing and Lifecycle](#6-streams)
7. [Flow Control — The Credit System](#7-flow-control)
8. [Header Compression: HPACK](#8-hpack)
9. [Server Push](#9-server-push)
10. [Priority and Dependency Trees](#10-priority)
11. [Error Handling](#11-error-handling)
12. [Settings Negotiation](#12-settings)
13. [HTTP Semantics over HTTP/2](#13-http-semantics)
14. [Connection Management and Keep-Alive](#14-connection-management)
15. [Security Considerations](#15-security)
16. [Performance Mental Models](#16-performance-mental-models)
17. [C Implementation](#17-c-implementation)
18. [Rust Implementation](#18-rust-implementation)
19. [Debugging HTTP/2 on the Wire](#19-debugging)
20. [Common Pitfalls and Gotchas](#20-pitfalls)

---

## 1. Why HTTP/2 Exists

### The HTTP/1.1 Performance Wall

HTTP/1.1, designed in 1999, has fundamental architectural limitations that cannot be patched:

#### Head-of-Line (HOL) Blocking
```
HTTP/1.1 — Single TCP Connection, Sequential Requests

Time -->
Req1 ████████████████ (200ms RTT + response)
Req2                  ████████████████
Req3                                  ████████████████
Req4                                                  ████████████████

Total: 4 × 200ms = 800ms minimum
```

HTTP/1.1 pipelining was supposed to fix this but failed because:
- Responses MUST be delivered in order (request order)
- Any slow response blocks all subsequent responses
- Proxies widely broken
- Barely deployed in practice

#### Browsers Open Multiple Connections as a Hack
```
HTTP/1.1 Browser Workaround

Connection Pool (6 connections to same host):
Conn1: [Req1]──────────[Req7]──────────
Conn2:  [Req2]──────────[Req8]──────────
Conn3:   [Req3]──────────[Req9]──────────
Conn4:    [Req4]──────────[Req10]─────────
Conn5:     [Req5]──────────[Req11]─────────
Conn6:      [Req6]──────────[Req12]─────────
```

Problems:
- 6× TCP handshake overhead
- 6× TLS handshake overhead
- 6× slow-start congestion window
- 6× memory per connection on server
- Unfair bandwidth sharing at the network level
- TCP connections compete with each other

#### Header Redundancy
Every HTTP/1.1 request sends full headers including `Cookie`, `User-Agent`, `Accept-*` — often 500–2000 bytes of repeated data per request. On a page with 100 resources, that's 200KB of repeated header bytes.

#### No Prioritization
A browser can't tell the server "this CSS file is more important than that analytics beacon." Everything is treated equally.

#### No Server Push
The server cannot proactively send resources it knows the client will need.

### The HTTP/2 Solution Architecture

HTTP/2 (RFC 7540, superseded by RFC 9113) solves all of these:

| Problem | HTTP/2 Solution |
|---|---|
| HOL Blocking | Multiplexed streams over single connection |
| Header redundancy | HPACK compression |
| No prioritization | Stream dependency tree + weight |
| No server push | PUSH_PROMISE frame |
| Multiple connections needed | One connection handles everything |
| Text parsing overhead | Binary framing layer |

---

## 2. Protocol Overview and Design Philosophy

### The Layered Mental Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│              HTTP Semantics (methods, status codes,              │
│              headers, body — same as HTTP/1.1)                   │
├─────────────────────────────────────────────────────────────────┤
│                    HTTP/2 FRAMING LAYER                          │
│         Binary frames, streams, flow control, HPACK              │
├─────────────────────────────────────────────────────────────────┤
│                      TLS 1.2 / 1.3                               │
│         (required for browsers, optional for h2c)                │
├─────────────────────────────────────────────────────────────────┤
│                         TCP                                      │
│         Reliable, ordered byte stream                            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Binary Protocol** — Unlike HTTP/1.1's text format, HTTP/2 uses fixed binary frames. No `\r\n` parsing, no ambiguity, faster parsing.

**Stateful Compression** — HPACK compresses headers using a shared state (dynamic table) between client and server. This is fundamentally different from per-message compression.

**Single TCP Connection** — One connection per origin (scheme + host + port). Everything multiplexed over this connection.

**Backward Compatible Semantics** — HTTP methods, status codes, and URI semantics are preserved. HTTP/2 is a new transport for HTTP, not a new HTTP.

### Protocol Identifiers

- `h2` — HTTP/2 over TLS (via ALPN extension)
- `h2c` — HTTP/2 over cleartext TCP (not used by browsers)

---

## 3. Connection Establishment

### TLS + ALPN Negotiation

HTTP/2 uses TLS Application-Layer Protocol Negotiation (ALPN, RFC 7301) to negotiate the protocol during the TLS handshake, avoiding an extra round-trip.

```
Client                                          Server
   |                                               |
   |──── TCP SYN ─────────────────────────────────>|
   |<─── TCP SYN-ACK ──────────────────────────────|
   |──── TCP ACK ─────────────────────────────────>|
   |                                               |
   |──── TLS ClientHello ─────────────────────────>|
   |     Extensions:                               |
   |       ALPN: ["h2", "http/1.1"]                |
   |       SNI: "example.com"                      |
   |                                               |
   |<──── TLS ServerHello ─────────────────────────|
   |      Extensions:                              |
   |        ALPN: "h2"    <-- server picks h2      |
   |      Certificate                              |
   |      ServerHelloDone                          |
   |                                               |
   |──── TLS Finished ────────────────────────────>|
   |<──── TLS Finished ────────────────────────────|
   |                                               |
   |  ===== Encrypted HTTP/2 Channel Begins =====  |
   |                                               |
   |──── Client Preface ──────────────────────────>|
   |     "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"        |
   |     + SETTINGS frame                          |
   |                                               |
   |<──── SETTINGS frame ──────────────────────────|
   |<──── SETTINGS ACK ────────────────────────────|
   |──── SETTINGS ACK ────────────────────────────>|
   |                                               |
   |  ======= Connection Ready for Requests =======|
```

### Client Connection Preface

The client sends a fixed 24-byte magic string FIRST, before anything else:

```
Hex: 50 52 49 20 2a 20 48 54 54 50 2f 32 2e 30 0d 0a
     0d 0a 53 4d 0d 0a 0d 0a

ASCII: "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
```

**Why this magic string?** It's designed so that an HTTP/1.1 server receiving it will return a `405 Method Not Allowed` (PRI is not a valid HTTP/1.1 method) — making misconfiguration fail gracefully.

After the magic string, the client sends its own `SETTINGS` frame (can be empty but must be sent).

### HTTP Upgrade (h2c — Cleartext Only)

For h2c (no TLS), there's an upgrade mechanism using HTTP/1.1:

```
Client                                          Server
   |                                               |
   |──── GET / HTTP/1.1 ──────────────────────────>|
   |     Host: example.com                         |
   |     Connection: Upgrade, HTTP2-Settings        |
   |     Upgrade: h2c                              |
   |     HTTP2-Settings: <base64url SETTINGS>      |
   |                                               |
   |<──── HTTP/1.1 101 Switching Protocols ────────|
   |      Upgrade: h2c                             |
   |                                               |
   |  === HTTP/2 begins (request repeated as stream 1) ===|
```

Browsers do NOT implement h2c. It's only for backend-to-backend communication.

---

## 4. Binary Framing Layer

### The Frame: Fundamental Unit of Communication

Every single thing in HTTP/2 is a frame. Frames have a fixed 9-byte header:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Length (24)                   |   Type (8)    |
+---------------+---------------+---------------+---------------+
|   Flags (8)   |R|                Stream ID (31)               |
+-+-------------+---------------+-------------------------------+
|                   Frame Payload (0...2^24-1 octets)          |
+---------------------------------------------------------------+

Length:    24 bits — payload length in bytes (NOT including 9-byte header)
           Max: 2^24-1 = 16,777,215 bytes (but default MAX_FRAME_SIZE = 16,384)
Type:      8 bits  — frame type identifier (0-9 defined, others reserved/extensions)
Flags:     8 bits  — type-specific flags
R:         1 bit   — RESERVED, MUST be 0, MUST be ignored by receiver
Stream ID: 31 bits — identifies the stream (0 = connection-level)
```

**Critical insight**: The `R` bit exists because the original SPDY protocol needed it; HTTP/2 inherited the bit for potential future use. Implementors must zero it on send and ignore it on receive.

**Stream ID 0** is special — it's used for connection-level frames like SETTINGS, PING, GOAWAY. Frames for actual requests/responses use stream IDs ≥ 1.

### Frame Type Registry

| Type ID | Name | Purpose |
|---|---|---|
| 0x0 | DATA | Request/response body bytes |
| 0x1 | HEADERS | Request/response headers (also opens stream) |
| 0x2 | PRIORITY | Set stream priority (deprecated in RFC 9218) |
| 0x3 | RST_STREAM | Immediately terminate a stream |
| 0x4 | SETTINGS | Connection parameters negotiation |
| 0x5 | PUSH_PROMISE | Server push initiation |
| 0x6 | PING | Keepalive / RTT measurement |
| 0x7 | GOAWAY | Connection shutdown |
| 0x8 | WINDOW_UPDATE | Flow control credit |
| 0x9 | CONTINUATION | Continuation of HEADERS (HPACK overflow) |

---

## 5. Frame Types — Every Field, Every Bit

### 5.1 DATA Frame (Type 0x0)

Used to carry request and response body bytes.

```
+---------------+
|Pad Length? (8)|   <-- only if PADDED flag set
+---------------+-----------------------------------------------+
|                            Data (*)                          ...
+---------------------------------------------------------------+
|                           Padding (*)                        ...
+---------------------------------------------------------------+
```

**Flags:**
- `END_STREAM (0x1)` — This frame is the last DATA frame for this stream. After sending, stream transitions to half-closed state.
- `PADDED (0x8)` — If set, first byte is "Pad Length", indicating how many padding bytes follow the data. Padding is randomized zeros for traffic analysis resistance.

**Rules:**
- DATA frames MUST NOT be sent on connection (stream 0)
- Receivers MUST treat a DATA frame on stream 0 as PROTOCOL_ERROR
- Data is subject to flow control

**Example — HTTP response body "Hello\n":**
```
Frame header (9 bytes):
  00 00 06   <- Length: 6 bytes
  00         <- Type: DATA (0x0)
  01         <- Flags: END_STREAM (0x1)
  00 00 00 01 <- Stream ID: 1

Payload (6 bytes):
  48 65 6c 6c 6f 0a  <- "Hello\n"
```

### 5.2 HEADERS Frame (Type 0x1)

Opens a new stream AND carries compressed headers. The most complex frame.

```
+---------------+
|Pad Length? (8)|   <-- only if PADDED flag
+-+-------------+-----------------------------------------------+
|E|                 Stream Dependency? (31)                     |  <-- only if PRIORITY flag
+-+-------------+-----------------------------------------------+
|  Weight? (8)  |   <-- only if PRIORITY flag
+-+-------------+-----------------------------------------------+
|                   Header Block Fragment (*)                  ...
+---------------------------------------------------------------+
|                           Padding (*)                        ...
+---------------------------------------------------------------+

E: Exclusive dependency flag (1 bit)
Stream Dependency: 31-bit stream ID this depends on
Weight: 8 bits, actual weight = value + 1 (range 1-256)
```

**Flags:**
- `END_STREAM (0x1)` — Last headers frame for this stream (no body will follow, i.e., GET request)
- `END_HEADERS (0x4)` — This frame ends the header block. If NOT set, a CONTINUATION frame MUST follow immediately.
- `PADDED (0x8)` — Padding present
- `PRIORITY (0x20)` — Priority fields present (deprecated)

**Critical rule about CONTINUATION**: If `END_HEADERS` is not set, the very next frame on that stream ID MUST be a CONTINUATION frame. No other frame type can appear between HEADERS and its CONTINUATIONs. This is enforced at the protocol level.

**Example — GET request:**
```
GET /index.html HTTP/2
Host: example.com

HEADERS frame (stream 1):
  Frame header:
    00 00 [len]  <- Length (HPACK compressed headers)
    01           <- Type: HEADERS (0x1)
    05           <- Flags: END_STREAM | END_HEADERS (no body)
    00 00 00 01  <- Stream ID: 1

  Payload (HPACK encoded):
    82           <- Indexed: :method GET (index 2 in static table)
    86           <- Indexed: :scheme https (index 7)
    84           <- Indexed: :path / (index 4)
    41 8a ...    <- Literal: :authority example.com
```

### 5.3 PRIORITY Frame (Type 0x2)

```
+-+-------------------------------------------------------------+
|E|                  Stream Dependency (31)                     |
+-+-------------+-----------------------------------------------+
|   Weight (8)  |
+-+-------------+
```

Standalone priority frame for a stream. Deprecated in RFC 9218 (Extensible Prioritization Scheme), but still defined in RFC 7540. Can be sent on idle or open streams.

### 5.4 RST_STREAM Frame (Type 0x3)

Immediately terminates a stream. After sending RST_STREAM, the sender MUST NOT send any more frames for that stream (except PRIORITY).

```
+---------------------------------------------------------------+
|                        Error Code (32)                        |
+---------------------------------------------------------------+
```

**No flags.** Fixed 4-byte payload. The receiver should stop sending on this stream.

**Use cases:**
- Client cancels a request (e.g., user navigates away)
- Server rejects a request it can't handle
- Protocol error on a specific stream (not connection-level)

**RST_STREAM vs GOAWAY:**
- RST_STREAM: terminates ONE stream, connection continues
- GOAWAY: terminates the ENTIRE connection

### 5.5 SETTINGS Frame (Type 0x4)

Connection-level parameters. Both client and server send SETTINGS right after the connection is established.

```
+-------------------------------+
|       Identifier (16)         |
+-------------------------------+-------------------------------+
|                        Value (32)                             |
+---------------------------------------------------------------+
```

Each setting is a 6-byte (ID + Value) pair. A single SETTINGS frame can contain zero or more settings.

**Flags:**
- `ACK (0x1)` — If set, this is an acknowledgment of received SETTINGS. Payload MUST be empty for ACK.

**Defined Settings:**

| ID | Name | Default | Description |
|---|---|---|---|
| 0x1 | HEADER_TABLE_SIZE | 4096 | Max size of HPACK dynamic table (bytes) |
| 0x2 | ENABLE_PUSH | 1 | 0 = disable server push |
| 0x3 | MAX_CONCURRENT_STREAMS | unlimited | Max open streams at one time |
| 0x4 | INITIAL_WINDOW_SIZE | 65535 | Initial stream flow control window (bytes) |
| 0x5 | MAX_FRAME_SIZE | 16384 | Max allowed frame payload size |
| 0x6 | MAX_HEADER_LIST_SIZE | unlimited | Max compressed header list size |

**SETTINGS handshake:**
```
Client                              Server
   |──── SETTINGS (initial) ─────────>|
   |<──── SETTINGS (initial) ──────────|
   |<──── SETTINGS ACK ────────────────|  <- ack client's settings
   |──── SETTINGS ACK ─────────────-->|  <- ack server's settings
```

Settings take effect when the other side ACKs. Between sending SETTINGS and receiving ACK, the old values apply.

**Example — client settings frame:**
```
00 00 12    <- Length: 18 bytes (3 settings × 6 bytes)
04          <- Type: SETTINGS
00          <- Flags: none
00 00 00 00 <- Stream ID: 0 (connection-level)

Settings:
  00 03  00 00 00 64  <- MAX_CONCURRENT_STREAMS = 100
  00 04  00 00 ff ff  <- INITIAL_WINDOW_SIZE = 65535
  00 05  00 00 40 00  <- MAX_FRAME_SIZE = 16384
```

### 5.6 PUSH_PROMISE Frame (Type 0x5)

Sent by the server to announce an upcoming server push. Must be sent on the stream that triggered the push (the request stream).

```
+---------------+
|Pad Length? (8)|  <-- if PADDED
+-+-------------+-----------------------------------------------+
|R|                  Promised Stream ID (31)                    |
+-+-----------------------------+-------------------------------+
|                   Header Block Fragment (*)                  ...
+---------------------------------------------------------------+
|                           Padding (*)                        ...
+---------------------------------------------------------------+
```

**Flags:**
- `END_HEADERS (0x4)` — If not set, CONTINUATION follows
- `PADDED (0x8)` — Padding present

**Promised Stream ID**: Server-initiated streams use EVEN IDs (2, 4, 6, ...). Client-initiated streams use ODD IDs (1, 3, 5, ...).

**Sequence:**
```
Client                                Server
   |──── GET /index.html (stream 1) ─>|
   |                                  |
   |<─── PUSH_PROMISE ────────────────|  stream 1, promises stream 2 (/style.css)
   |<─── PUSH_PROMISE ────────────────|  stream 1, promises stream 4 (/app.js)
   |<─── HEADERS (response) ──────────|  stream 1, 200 OK for /index.html
   |<─── DATA ────────────────────────|  stream 1, HTML body
   |<─── HEADERS (push) ─────────────|  stream 2, 200 OK for /style.css
   |<─── DATA (push) ────────────────|  stream 2, CSS bytes
   |<─── HEADERS (push) ─────────────|  stream 4, 200 OK for /app.js
   |<─── DATA (push) ────────────────|  stream 4, JS bytes
```

### 5.7 PING Frame (Type 0x6)

Measures round-trip time or checks connection liveness. Fixed 8-byte payload (opaque data chosen by sender).

```
+---------------------------------------------------------------+
|                                                               |
|                      Opaque Data (64)                         |
|                                                               |
+---------------------------------------------------------------+
```

**Flags:**
- `ACK (0x1)` — PING response. The receiver of a PING MUST respond with PING+ACK containing the same 8 bytes.

**Must be on stream 0 (connection-level).** A PING not on stream 0 is a PROTOCOL_ERROR.

**Use case — measuring RTT:**
```c
uint64_t ts = get_timestamp_ns();
send_ping(conn, ts_bytes);  // embed timestamp in opaque data
// ... receive PING ACK ...
uint64_t rtt = get_timestamp_ns() - read_uint64(ping_ack_data);
```

### 5.8 GOAWAY Frame (Type 0x7)

Graceful connection shutdown. After sending GOAWAY, the sender will not process any new streams.

```
+-+-------------------------------------------------------------+
|R|                  Last-Stream-ID (31)                        |
+-+-------------------------------------------------------------+
|                      Error Code (32)                          |
+---------------------------------------------------------------+
|                  Additional Debug Data (*)                    |
+---------------------------------------------------------------+
```

**Last-Stream-ID**: The highest-numbered stream the sender has processed. The receiver knows streams with IDs > Last-Stream-ID were NOT processed and can retry them on a new connection.

**Error codes:**
| Code | Name | Meaning |
|---|---|---|
| 0x0 | NO_ERROR | Graceful shutdown |
| 0x1 | PROTOCOL_ERROR | Invalid frame, etc. |
| 0x2 | INTERNAL_ERROR | Implementation bug |
| 0x3 | FLOW_CONTROL_ERROR | Flow control violation |
| 0x4 | SETTINGS_TIMEOUT | SETTINGS ACK not received in time |
| 0x5 | STREAM_CLOSED | Frame received on closed stream |
| 0x6 | FRAME_SIZE_ERROR | Frame payload too large |
| 0x7 | REFUSED_STREAM | Stream not processed (safe to retry) |
| 0x8 | CANCEL | Stream cancelled by user |
| 0x9 | COMPRESSION_ERROR | HPACK state error (fatal) |
| 0xa | CONNECT_ERROR | TCP error in CONNECT tunnel |
| 0xb | ENHANCE_YOUR_CALM | Rate limiting (like 429) |
| 0xc | INADEQUATE_SECURITY | TLS requirements not met |
| 0xd | HTTP_1_1_REQUIRED | Server needs HTTP/1.1 |

**GOAWAY is connection-level only (stream 0).**

**Graceful shutdown sequence:**
```
Server                              Client
   |──── GOAWAY (last=2^31-1) ───────>|  "I'm going away, but finish current"
   | (wait for in-flight streams)      |
   |──── GOAWAY (last=N) ─────────────>|  "I processed up to stream N"
   | (wait for ACK / connection close) |
   |<─── connection close ─────────────|
```

### 5.9 WINDOW_UPDATE Frame (Type 0x8)

Grants flow control credit.

```
+-+-------------------------------------------------------------+
|R|              Window Size Increment (31)                     |
+-+-------------------------------------------------------------+
```

**Increment**: 1 to 2^31-1. A value of 0 is a PROTOCOL_ERROR.

**Can be on stream 0** (connection-level flow control) **or a specific stream** (stream-level flow control). Both operate independently.

### 5.10 CONTINUATION Frame (Type 0x9)

Overflow of HEADERS or PUSH_PROMISE when the header block is too large for one frame.

```
|                   Header Block Fragment (*)                  ...
```

**Flags:**
- `END_HEADERS (0x4)` — If set, header block is complete.

**Rules:**
- MUST follow a HEADERS or PUSH_PROMISE frame (or another CONTINUATION)
- MUST have the same stream ID as the preceding HEADERS/PUSH_PROMISE
- No other frame type may appear between HEADERS and CONTINUATIONs
- An intervening frame is a PROTOCOL_ERROR

---

## 6. Streams: Multiplexing and Lifecycle

### Stream Concept

A stream is a bidirectional sequence of frames within a single HTTP/2 connection. Each stream:
- Has a unique 31-bit integer ID
- Is independent of other streams (no ordering between streams)
- Has its own flow control state
- Has its own priority weight and dependency

```
Connection (single TCP)
│
├── Stream 1  (GET /index.html)
│   ├── HEADERS [client → server]
│   └── HEADERS + DATA [server → client]
│
├── Stream 3  (GET /style.css)
│   ├── HEADERS [client → server]
│   └── HEADERS + DATA [server → client]
│
├── Stream 5  (POST /api/data)
│   ├── HEADERS + DATA [client → server]
│   └── HEADERS + DATA [server → client]
│
└── Stream 2  (PUSH /app.js — server initiated)
    ├── PUSH_PROMISE [server → client, on stream 1]
    └── HEADERS + DATA [server → client]
```

### Stream ID Assignment

- **Odd IDs (1, 3, 5, ...)**: Client-initiated (requests)
- **Even IDs (2, 4, 6, ...)**: Server-initiated (push)
- **Stream 0**: Connection-level (not a real stream)
- IDs are monotonically increasing, NEVER reused within a connection
- Starting a new stream with an ID lower than any existing stream is a PROTOCOL_ERROR

### Stream States

The stream state machine is one of the most important concepts in HTTP/2:

```
                         IDLE
                           |
              send HEADERS |  recv HEADERS
                           |
                           v
                        OPEN  ─────────────────────────────────────────────┐
                         / \                                                |
        send ES/recv RST/  \ recv ES/send RST/                             |
        send RST            \ recv RST                                     |
                             v                                             |
    HALF-CLOSED (local)    HALF-CLOSED (remote)                            |
           │                   │                                    send/recv RST
           │ recv ES           │ send ES                                   │
           │ recv RST          │ send RST                                  │
           │ send RST          │                                           │
           └──────────────────>│                                           │
                               v                                           │
                            CLOSED <──────────────────────────────────────-┘

ES = END_STREAM flag
RST = RST_STREAM frame
```

**Detailed State Descriptions:**

**IDLE**: Stream not yet used. A stream begins in IDLE state. Sending HEADERS (or PUSH_PROMISE which reserves a stream) transitions to OPEN (or RESERVED).

**RESERVED (local)**: Server sent PUSH_PROMISE. Server can now send HEADERS to open the stream fully.

**RESERVED (remote)**: Client received PUSH_PROMISE. Client can send RST_STREAM to reject the push.

**OPEN**: Both sides can send frames. Most request/response processing happens here.

**HALF-CLOSED (local)**: Local side sent END_STREAM. Local can only send WINDOW_UPDATE, PRIORITY, RST_STREAM. Remote can still send frames.

**HALF-CLOSED (remote)**: Remote side sent END_STREAM. Local can still send frames. Remote can only send WINDOW_UPDATE, PRIORITY, RST_STREAM.

**CLOSED**: Terminal state. Stream is finished. Receiving most frame types on a closed stream is a STREAM_CLOSED error.

### The Critical Rule: Stream Lifecycle on a GET Request

```
Client                              Server
   │                                   │
   │── HEADERS (END_STREAM) ──────────>│  Stream opens + immediately half-closes (no body)
   │   stream: OPEN → HALF-CLOSED      │  stream: OPEN
   │                                   │
   │<── HEADERS ───────────────────────│  response headers
   │                                   │  stream: OPEN
   │<── DATA (END_STREAM) ─────────────│  response body + end
   │   stream: CLOSED                  │  stream: HALF-CLOSED → CLOSED
```

---

## 7. Flow Control — The Credit System

### Why Flow Control?

TCP has its own flow control (window size), but HTTP/2 needs stream-level flow control because:
- Multiple streams share one TCP connection
- A fast producer on stream 1 shouldn't starve a slow consumer on stream 3
- Application needs control independent of kernel buffer sizes

### The Two-Level Credit System

Flow control in HTTP/2 operates at **two independent levels simultaneously**:

```
                    Connection Level Window
              ┌─────────────────────────────────────┐
              │  Connection Send Window: 65535 bytes │
              │  (shared by ALL streams)             │
              └────────────┬────────────┬────────────┘
                           │            │
              ┌────────────┘            └────────────┐
              ▼                                      ▼
     Stream 1 Window                       Stream 3 Window
  ┌──────────────────────┐            ┌──────────────────────┐
  │ Stream Send Window:  │            │ Stream Send Window:  │
  │ 65535 bytes          │            │ 65535 bytes          │
  └──────────────────────┘            └──────────────────────┘
```

**To send N bytes on stream X:**
- BOTH the stream window AND the connection window must have N bytes available
- The actual amount you can send = `min(stream_window, connection_window)`
- After sending N bytes: `stream_window -= N; connection_window -= N`

### Initial Window Size

- Default: 65535 bytes (2^16 - 1) for both stream and connection
- Can be changed via SETTINGS (`INITIAL_WINDOW_SIZE`)
- SETTINGS change applies to ALL currently open streams
- Can be as large as 2^31 - 1 = 2,147,483,647 bytes

### WINDOW_UPDATE Mechanism

The receiver grants credit by sending WINDOW_UPDATE:

```
Producer (sender)              Consumer (receiver)
     │                               │
     │ stream_window = 65535         │
     │                               │
     │─── DATA (50000 bytes) ───────>│   stream_window = 15535
     │─── DATA (10000 bytes) ───────>│   stream_window = 5535
     │                               │  (receiver processes data)
     │                               │
     │<─── WINDOW_UPDATE (+50000) ───│   stream_window = 55535
     │<─── WINDOW_UPDATE (+10000) ───│   (or can send one +60000)
     │                               │
     │─── DATA (55535 bytes) ───────>│   stream_window = 0
     │                               │
     │         BLOCKED!              │  (must wait)
     │<─── WINDOW_UPDATE (+65535) ───│
     │─── DATA (65535 bytes) ───────>│
```

**Flow control only applies to DATA frames**. HEADERS, RST_STREAM, SETTINGS, PING, GOAWAY, WINDOW_UPDATE, and PRIORITY are NOT subject to flow control.

### Flow Control Violations

- Sender exceeds the window: FLOW_CONTROL_ERROR (connection error)
- WINDOW_UPDATE with increment 0: PROTOCOL_ERROR
- WINDOW_UPDATE that causes window to exceed 2^31-1: FLOW_CONTROL_ERROR

### Strategy for Efficient Flow Control

**Receiver strategy**: Don't wait until window is exhausted to send WINDOW_UPDATE. Send updates proactively when you've consumed a threshold (e.g., when you've read half the window):

```c
// Good strategy: send WINDOW_UPDATE when consumed >= threshold
if (bytes_consumed >= window_size / 2) {
    send_window_update(stream_id, bytes_consumed);
    bytes_consumed = 0;
}
```

**HOL blocking within HTTP/2**: If a single stream has a large body and no flow control, it can starve other streams at the TCP level even though HTTP/2 "fixes" HOL blocking. Proper flow control makes the multiplexing fair.

---

## 8. HPACK: Header Compression

HPACK (RFC 7541) is HTTP/2's header compression format. It's NOT GZIP — it's specifically designed for HTTP headers and stateful.

### The Three Components of HPACK

#### 8.1 Static Table

A fixed, predefined table of 61 (header name, header value) pairs, indexed 1-61. Built into the spec, same for every connection.

```
Index | Header Name                 | Header Value
------|-----------------------------|-------------------
  1   | :authority                  |
  2   | :method                     | GET
  3   | :method                     | POST
  4   | :path                       | /
  5   | :path                       | /index.html
  6   | :scheme                     | http
  7   | :scheme                     | https
  8   | :status                     | 200
  9   | :status                     | 204
 10   | :status                     | 206
 11   | :status                     | 304
 12   | :status                     | 400
 13   | :status                     | 404
 14   | :status                     | 500
 15   | accept-charset              |
 16   | accept-encoding             | gzip, deflate
 17   | accept-language             |
 18   | accept-ranges               |
 19   | accept                      |
 20   | access-control-allow-origin |
 21   | age                         |
 22   | allow                       |
 23   | authorization               |
 24   | cache-control               |
 25   | content-disposition         |
 26   | content-encoding            |
 27   | content-language            |
 28   | content-length              |
 29   | content-location            |
 30   | content-range               |
 31   | content-type                |
 32   | cookie                      |
 33   | date                        |
 34   | etag                        |
 35   | expect                      |
 36   | expires                     |
 37   | from                        |
 38   | host                        |
 39   | if-match                    |
 40   | if-modified-since           |
 41   | if-none-match               |
 42   | if-range                    |
 43   | if-unmodified-since         |
 44   | last-modified               |
 45   | link                        |
 46   | location                    |
 47   | max-forwards                |
 48   | proxy-authenticate          |
 49   | proxy-authorization         |
 50   | range                       |
 51   | referer                     |
 52   | refresh                     |
 53   | retry-after                 |
 54   | server                      |
 55   | set-cookie                  |
 56   | strict-transport-security   |
 57   | te                          |
 58   | transfer-encoding           |
 59   | user-agent                  |
 60   | vary                        |
 61   | via                         |
 62   | www-authenticate            |
```

#### 8.2 Dynamic Table

A per-connection, FIFO table that grows as new headers are seen. Both encoder and decoder maintain an identical copy through synchronized operations.

**Eviction policy**: When the table exceeds `HEADER_TABLE_SIZE` bytes, entries are evicted from the end (oldest entries first, FIFO).

**Size of an entry**: `name_length + value_length + 32` bytes (the +32 accounts for overhead per entry).

**Indexing**: Dynamic table entries are indexed starting at 62 (immediately after static table). The most recently added entry is always at index 62, pushing older entries to higher indices.

```
Dynamic table state after adding entries:
  Index 62: (most recent) "content-type: application/json"
  Index 63: "authorization: Bearer abc123"
  Index 64: (oldest)      "accept: text/html"
```

#### 8.3 Huffman Encoding

HPACK includes a Huffman code for literal string values. The code is pre-defined in the RFC (not adaptive). Using Huffman is optional — the encoder signals it with a flag bit.

The Huffman code gives approximately 30-40% compression on typical HTTP headers by assigning shorter codes to more common characters (common ASCII letters get short codes; unusual bytes get long codes up to 30 bits).

### HPACK Encoding Formats

Every header field is encoded using one of these representations:

#### Indexed Header Field (Reference to table entry)

```
  0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
| 1 |        Index (7+)         |
+---+---------------------------+
```

First bit = 1 means "indexed". Remaining 7+ bits are the table index using integer encoding.

**Example**: `GET` method from static table (index 2)
```
Binary: 10000010  = 0x82
```

This encodes `:method: GET` in a single byte!

#### Literal with Incremental Indexing (Add to dynamic table)

```
  0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
| 0 | 1 |      Index (6+)       |   <- name from table
+---+---+-----------------------+
| H |     Value Length (7+)     |
+---+---------------------------+
| Value String (Length octets)  |
+-------------------------------+

OR

+---+---+-----------------------+
| 0 | 1 |           0           |   <- literal name (index=0)
+---+---+-----------------------+
| H |     Name Length (7+)      |
+---+---------------------------+
| Name String (Length octets)   |
+-------------------------------+
| H |     Value Length (7+)     |
+---+---------------------------+
| Value String (Length octets)  |
+-------------------------------+
```

H = 1 if Huffman encoded, 0 if raw bytes.
The header field IS added to the dynamic table for future reference.

#### Literal Without Indexing (Don't add to dynamic table)

```
  0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
| 0 | 0 | 0 | 0 |  Index (4+)  |
+---+---+-----------+-----------+
```

First nibble = 0000. NOT added to dynamic table. Use for headers that are unique per request (like `authorization` with a fresh token) where caching would be wasteful.

#### Literal Never Indexed (Security-sensitive)

```
  0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
| 0 | 0 | 0 | 1 |  Index (4+)  |
+---+---+-----------+-----------+
```

First nibble = 0001. NOT added to dynamic table, AND intermediaries MUST NOT add it either. Used for cookies, authorization tokens — prevents a compromised proxy from learning sensitive values via the dynamic table.

### HPACK Integer Encoding

Integers can span multiple bytes using a prefix encoding:

```
Prefix size N = available bits in first byte

If value < 2^N - 1:
  Encode directly in those N bits

If value >= 2^N - 1:
  Set all N bits to 1 in first byte
  Encode remaining = (value - (2^N - 1))
  Using base-128 (LEB128-like encoding):
    While remaining >= 128:
      Byte = (remaining % 128) | 0x80   <- set high bit
      remaining = remaining / 128
    Final byte = remaining               <- high bit clear
```

**Example**: Encode 1337 with prefix N=5:
- 2^5 - 1 = 31
- 1337 >= 31, so first byte = 0b???11111 (with top 3 bits = flags/type)
- remaining = 1337 - 31 = 1306
- 1306 / 128 = 10 remainder 26
- First continuation byte = 26 | 0x80 = 154 = 0x9a
- Second byte = 10 = 0x0a
- Result: [?11111, 0x9a, 0x0a]

### HPACK in Action: Example Compression

**Request 1**: GET /
```
Headers to send:
  :method: GET
  :scheme: https
  :path: /
  :authority: www.example.com
  accept-encoding: gzip, deflate

HPACK encoded (first request, dynamic table empty):
  82        <- indexed: :method GET (static[2])
  86        <- indexed: :scheme https (static[7])
  84        <- indexed: :path / (static[4])
  41        <- literal+index, name=static[1](:authority)
  8c f1 e3 c2 e5 f2 3a 6b a0 ab 90 f4 ff  <- huffman("www.example.com") + added to dynamic[62]
  90        <- indexed: accept-encoding gzip,deflate (static[16])

Dynamic table after: {62: (:authority, www.example.com)}
```

**Request 2**: GET /index.html
```
Headers to send:
  :method: GET
  :scheme: https
  :path: /index.html
  :authority: www.example.com
  accept-encoding: gzip, deflate

HPACK encoded:
  82        <- :method GET (static[2])
  86        <- :scheme https (static[7])
  85        <- :path /index.html (static[5])
  be        <- indexed: :authority www.example.com (dynamic[62]!) ← COMPRESSION WIN
  90        <- accept-encoding (static[16])

`:authority` is now encoded in ONE BYTE instead of 15+ bytes!
```

**This is why HPACK is stateful**: the dynamic table accumulates across requests, achieving better compression over time.

### HPACK Security: CRIME Attack Resistance

HTTP/1.1 with CRIME attack: if an attacker can force content next to a secret header and observe compressed sizes, they can reconstruct the secret byte-by-byte.

HPACK's defenses:
1. Huffman encoding is fixed (not adaptive to content) — no size leakage from adaptive coding
2. "Never indexed" representation — prevents secrets from entering the dynamic table
3. No cross-stream compression — each stream compresses independently relative to the shared dynamic table, but you can't selectively mix attacker content with victim content

---

## 9. Server Push

### Concept and Motivation

Server push allows the server to preemptively send resources the client hasn't requested yet, eliminating a full RTT for discoverable resources.

```
Without push:                      With push:
  GET /index.html                    GET /index.html
  <─── response ───>                 <─── PUSH_PROMISE /style.css
  (parse HTML, find link)            <─── PUSH_PROMISE /app.js
  GET /style.css                     <─── response (HTML)
  GET /app.js                        <─── PUSH data (CSS)  [concurrent!]
  <─── response ───>                 <─── PUSH data (JS)   [concurrent!]
  <─── response ───>
  
  3 RTTs minimum                     1 RTT effective
```

### Push Stream Lifecycle

1. Server sends PUSH_PROMISE on the stream that triggered it (e.g., stream 1)
2. PUSH_PROMISE reserves the promised stream ID (even number)
3. Server opens the push stream by sending HEADERS (with 200 OK, etc.)
4. Server sends DATA
5. Push stream closes with END_STREAM

**Client can reject a push** by sending RST_STREAM with CANCEL on the promised stream ID (e.g., if it has the resource cached).

### Push Caveats and Why It's Falling Out of Favor

1. **Cache awareness**: Server doesn't know what the client has cached. It may push a resource the client already has, wasting bandwidth.
2. **Deprecation**: HTTP/3 (QUIC) initially kept push but it's been deprecated in practice. Chrome removed support for HTTP/2 push in 2022 due to poor real-world performance.
3. **Alternative**: `103 Early Hints` (RFC 8297) is now preferred — it sends `Link` headers as a preliminary 1xx response, letting the browser decide what to prefetch.

---

## 10. Priority and Dependency Trees

### HTTP/2 Priority (RFC 7540 §5.3)

Each stream has:
- **Dependency**: Which stream this stream depends on (defaults to stream 0 = root)
- **Exclusive flag**: If set, this stream becomes the sole child of its parent, demoting existing children
- **Weight**: 1-256, proportional bandwidth allocation among siblings

```
Priority tree example:

         ROOT (0)
           │
       ┌───┴───┐
       A       B
      (16)    (16)  <- equal weight, split bandwidth 50/50
       │
    ┌──┴──┐
    C     D
   (12)  (4)   <- C gets 75%, D gets 25% of A's share
```

**Practical bandwidth allocation:**
- A and B are root's children, each weight 16 → A gets 50%, B gets 50%
- C and D are A's children, weights 12 and 4 → C gets 75% of A's, D gets 25% of A's
- Final: C=37.5%, D=12.5%, B=50%

### Exclusive Dependency

If client sends HEADERS with exclusive=1, dependency=A for new stream E:
- E becomes A's only child
- All of A's previous children become E's children

```
Before:                After (E added with exclusive=1, depending on A):
    ROOT                    ROOT
     │                       │
     A                       A
    / \                      │
   C   D                     E
                            / \
                           C   D
```

### Priority Deprecation

RFC 9218 (Extensible Prioritization Scheme) deprecates RFC 7540 priority in favor of the `Priority` HTTP header field and `PRIORITY_UPDATE` frame. This is because:
- Tree-based priority is complex to implement correctly
- Few implementations got it right
- The simpler urgency+incremental model is more useful in practice

---

## 11. Error Handling

### Two Classes of Errors

#### Connection Errors
Affect the entire connection. Response: send GOAWAY, then close TCP connection.

```
Client                              Server
   │                                   │
   │<── GOAWAY (PROTOCOL_ERROR) ───────│
   │    last-stream-id: 5              │
   │                                   │
   │    [TCP connection closes]        │
```

Streams 1, 3, 5 were processed. Streams 7, 9, etc. were NOT and can be retried.

#### Stream Errors
Affect only one stream. Response: send RST_STREAM for that stream, connection continues.

```
Client                              Server
   │──── HEADERS (stream 7) ─────────>│
   │<─── RST_STREAM (stream 7) ────────│  REFUSED_STREAM
   │                                   │
   │──── HEADERS (stream 9) ─────────>│  connection still works!
   │<─── HEADERS (stream 9) ───────────│
```

### Error Code Decision Guide

```
Received malformed frame header     → PROTOCOL_ERROR (connection)
Received frame on wrong stream type → PROTOCOL_ERROR (connection)
HPACK decoding failure              → COMPRESSION_ERROR (connection, fatal)
Flow control window exceeded        → FLOW_CONTROL_ERROR (connection)
Frame too large                     → FRAME_SIZE_ERROR (connection or stream)
Received RST_STREAM on idle stream  → PROTOCOL_ERROR (connection)
Invalid header field                → PROTOCOL_ERROR (stream)
Request refused before processing   → REFUSED_STREAM (stream)
```

---

## 12. Settings Negotiation

### Settings Change Flow

```
Client                              Server
   │──── SETTINGS (A=1, B=2) ────────>│
   │                                   │  (old values still in effect)
   │<──── SETTINGS ACK ────────────────│  (new values A=1, B=2 now active)
```

Until SETTINGS ACK is received, the sender must behave as if the old settings apply. This is critical for MAX_FRAME_SIZE — you can't send larger frames until you know the remote has acknowledged your higher limit.

### INITIAL_WINDOW_SIZE Change

If a SETTINGS frame changes `INITIAL_WINDOW_SIZE`, it affects ALL currently open streams:

```
Old INITIAL_WINDOW_SIZE = 65535
New INITIAL_WINDOW_SIZE = 131072

For each open stream:
  stream.window += (131072 - 65535) = +65537

If new window > 2^31-1 for any stream → FLOW_CONTROL_ERROR
```

### Settings Acknowledgment Timeout

If SETTINGS ACK is not received within a reasonable time, the sender should send GOAWAY with `SETTINGS_TIMEOUT`.

---

## 13. HTTP Semantics over HTTP/2

### Pseudo-Headers

HTTP/2 uses pseudo-headers (prefixed with `:`) to carry HTTP/1.1 request-line and status-line information. These MUST appear before regular headers and MUST NOT appear in trailers.

**Request pseudo-headers:**
- `:method` — HTTP method (GET, POST, etc.) — REQUIRED
- `:scheme` — URI scheme (http, https) — REQUIRED (except CONNECT)
- `:path` — Absolute path (plus query) — REQUIRED (except CONNECT and OPTIONS *)
- `:authority` — Host (like `Host:` header) — RECOMMENDED

**Response pseudo-header:**
- `:status` — Three-digit status code — REQUIRED

### Forbidden Headers

These HTTP/1.1 headers MUST NOT appear in HTTP/2:

- `Connection`, `Keep-Alive`, `Proxy-Connection`, `Transfer-Encoding`, `Upgrade`

These are connection-specific headers that have no meaning in HTTP/2 (which doesn't use chunked transfer encoding, has its own connection management, etc.).

`TE: trailers` is the only exception — it's allowed if it contains only "trailers".

### Trailers

HTTP/2 supports trailers (headers after the body) using a HEADERS frame after the DATA frames, with END_STREAM set.

```
HEADERS (request headers)
DATA (body chunk 1)
DATA (body chunk 2)
HEADERS (trailers, END_STREAM)  <- e.g., checksum after streaming body
```

### The CONNECT Method

HTTP/2 supports the CONNECT method for creating tunnels (like for WebSocket upgrades). Extended CONNECT (RFC 8441) allows WebSockets over HTTP/2.

For CONNECT:
- `:method` = CONNECT
- `:authority` = target host:port
- NO `:scheme` or `:path`
- Stream remains OPEN in both directions while tunnel is active

### Upgrade to HTTP/2 from HTTP/1.1

The `101 Switching Protocols` response doesn't exist in HTTP/2. Upgrade from within HTTP/2 is not possible — protocol negotiation happens at connection establishment via ALPN.

---

## 14. Connection Management and Keep-Alive

### Single Connection Per Origin

HTTP/2 is designed to use ONE connection per origin. Browsers create more connections only if the first connection refuses (GOAWAY with `HTTP_1_1_REQUIRED` or other errors).

### Connection Coalescing

If two origins share the same IP address AND the TLS certificate covers both (wildcard or SAN), HTTP/2 can reuse the same connection:
- `https://example.com` and `https://api.example.com` — same connection if IP matches and cert covers both

This is connection coalescing and reduces overall connection overhead.

### Keepalive via PING

HTTP/2 uses PING frames for keepalive, replacing TCP keepalive for the protocol level:

```
// Every 30 seconds:
Client ──── PING ─────────────────────────────────────> Server
Client <─── PING ACK ──────────────────────────────── Server

// If no PING ACK within timeout:
Client ──── GOAWAY (NO_ERROR) ─────────────────────> Server
```

### Graceful vs Immediate Shutdown

**Graceful** (for planned maintenance):
1. Send GOAWAY with last-stream-id = 2^31-1 (all streams OK)
2. Wait for in-flight streams to complete
3. Send GOAWAY with actual last-stream-id
4. Close TCP

**Immediate** (for errors):
1. Send GOAWAY with error code
2. Close TCP immediately

### Connection Reuse vs New Connection

The rule: if a stream is refused (REFUSED_STREAM error code), the request is safe to retry on a new connection. If the error code is anything else, the request may have been processed — retrying could cause double-processing (dangerous for POST/PUT).

---

## 15. Security Considerations

### TLS Requirements for h2

HTTP/2 over TLS requires:
- TLS 1.2 or higher (TLS 1.3 strongly preferred)
- SNI extension
- No renegotiation (TLS renegotiation is incompatible with multiplexing)
- No compression at TLS layer (CRIME vulnerability)
- Minimum cipher suites (several weak suites blacklisted by RFC 7540 Appendix A)

**Blacklisted cipher suites** include all NULL, export-grade, RC4, 3DES, and DH with < 2048-bit parameters.

### HPACK Security: Intermediary Trust

HPACK's "never indexed" representation (0x10 prefix) is crucial for:
- Authorization header values
- Cookie values
- Any token that grants access

An intermediary (proxy) MUST propagate the "never indexed" flag — it cannot "helpfully" add the value to its dynamic table.

### HTTP/2 Rapid Reset Attack (CVE-2023-44487)

Disclosed October 2023, this is the largest DDoS ever recorded (398 million RPS).

**Attack mechanism:**
1. Open stream (HEADERS)
2. Immediately cancel it (RST_STREAM)
3. Repeat rapidly
4. Server must process the request before seeing the RST
5. Creates enormous server load with minimal client resources
6. Since RST is valid, flow control and MAX_CONCURRENT_STREAMS don't protect you

**Mitigations:**
- Rate limit RST_STREAM per connection
- Track rapid request+cancel patterns
- Close connections that abuse RST
- Set lower MAX_CONCURRENT_STREAMS

### Stream Limit DOS

If MAX_CONCURRENT_STREAMS is too high, an attacker opens many streams and holds them open, exhausting server resources. Set MAX_CONCURRENT_STREAMS to a reasonable value (100-1000 depending on server capacity).

---

## 16. Performance Mental Models

### Mental Model 1: HTTP/2 Is Not Magic

HTTP/2 fixes HOL blocking at the HTTP layer but NOT at the TCP layer. If TCP has packet loss, all streams are blocked waiting for retransmission (TCP-level HOL blocking). This is why HTTP/3 moved to QUIC (UDP-based transport with per-stream flow control).

```
HTTP/1.1:  HTTP HOL + TCP HOL  (double pain)
HTTP/2:    No HTTP HOL + TCP HOL  (one pain)
HTTP/3:    No HTTP HOL + No transport HOL  (QUIC solves it)
```

### Mental Model 2: The Bandwidth-Delay Product

The optimal HTTP/2 window size = bandwidth × RTT (BDP).

```
100 Mbps link, 50ms RTT:
BDP = 100,000,000 bit/s × 0.05s = 5,000,000 bits = 625,000 bytes

Default window = 65535 bytes
This means the default window only fills 10% of the pipe!

Set INITIAL_WINDOW_SIZE = 10MB for high-BDP connections
```

### Mental Model 3: Streams Are Cheap, Connections Are Expensive

In HTTP/1.1, connections are the expensive resource. In HTTP/2, streams are cheap (they're just integers and state machines). You should freely open streams. The expensive resource is now bytes in flight (flow control window).

### Mental Model 4: HPACK Statefulness as a Weapon Against Latency

HPACK's dynamic table accumulates "context" about the HTTP conversation. If you hammer the same API endpoint, headers become nearly free after the first request. The static table handles ~90% of common request patterns; the dynamic table handles the rest.

### Mental Model 5: Multiplexing vs. Bandwidth Sharing

HTTP/2 multiplexing does NOT give you more bandwidth — it gives you more efficient use of existing bandwidth. The latency improvements come from eliminating idle time waiting for responses.

---

## 17. C Implementation

### Complete HTTP/2 Parser and Connection Handler in C

```c
/* http2.h — HTTP/2 implementation in C */

#ifndef HTTP2_H
#define HTTP2_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

/*
 * ============================================================
 * CONSTANTS AND LIMITS
 * ============================================================
 */

#define H2_CLIENT_PREFACE     "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
#define H2_CLIENT_PREFACE_LEN 24

#define H2_FRAME_HEADER_SIZE  9
#define H2_MAX_FRAME_SIZE_MIN 16384      /* 2^14 */
#define H2_MAX_FRAME_SIZE_MAX 16777215   /* 2^24 - 1 */
#define H2_DEFAULT_WINDOW     65535      /* 2^16 - 1 */
#define H2_MAX_WINDOW         2147483647 /* 2^31 - 1 */
#define H2_HPACK_STATIC_TABLE_SIZE 61

/*
 * ============================================================
 * FRAME TYPES
 * ============================================================
 */

typedef enum {
    H2_FRAME_DATA          = 0x0,
    H2_FRAME_HEADERS       = 0x1,
    H2_FRAME_PRIORITY      = 0x2,
    H2_FRAME_RST_STREAM    = 0x3,
    H2_FRAME_SETTINGS      = 0x4,
    H2_FRAME_PUSH_PROMISE  = 0x5,
    H2_FRAME_PING          = 0x6,
    H2_FRAME_GOAWAY        = 0x7,
    H2_FRAME_WINDOW_UPDATE = 0x8,
    H2_FRAME_CONTINUATION  = 0x9,
} h2_frame_type_t;

/*
 * ============================================================
 * FLAGS
 * ============================================================
 */

#define H2_FLAG_END_STREAM  0x01
#define H2_FLAG_END_HEADERS 0x04
#define H2_FLAG_PADDED      0x08
#define H2_FLAG_PRIORITY    0x20
#define H2_FLAG_ACK         0x01

/*
 * ============================================================
 * ERROR CODES
 * ============================================================
 */

typedef enum {
    H2_ERR_NO_ERROR            = 0x0,
    H2_ERR_PROTOCOL_ERROR      = 0x1,
    H2_ERR_INTERNAL_ERROR      = 0x2,
    H2_ERR_FLOW_CONTROL_ERROR  = 0x3,
    H2_ERR_SETTINGS_TIMEOUT    = 0x4,
    H2_ERR_STREAM_CLOSED       = 0x5,
    H2_ERR_FRAME_SIZE_ERROR    = 0x6,
    H2_ERR_REFUSED_STREAM      = 0x7,
    H2_ERR_CANCEL              = 0x8,
    H2_ERR_COMPRESSION_ERROR   = 0x9,
    H2_ERR_CONNECT_ERROR       = 0xa,
    H2_ERR_ENHANCE_YOUR_CALM   = 0xb,
    H2_ERR_INADEQUATE_SECURITY = 0xc,
    H2_ERR_HTTP_1_1_REQUIRED   = 0xd,
} h2_error_code_t;

/*
 * ============================================================
 * SETTINGS IDENTIFIERS
 * ============================================================
 */

typedef enum {
    H2_SETTINGS_HEADER_TABLE_SIZE      = 0x1,
    H2_SETTINGS_ENABLE_PUSH            = 0x2,
    H2_SETTINGS_MAX_CONCURRENT_STREAMS = 0x3,
    H2_SETTINGS_INITIAL_WINDOW_SIZE    = 0x4,
    H2_SETTINGS_MAX_FRAME_SIZE         = 0x5,
    H2_SETTINGS_MAX_HEADER_LIST_SIZE   = 0x6,
} h2_setting_id_t;

/*
 * ============================================================
 * STREAM STATES
 * ============================================================
 */

typedef enum {
    H2_STREAM_IDLE,
    H2_STREAM_OPEN,
    H2_STREAM_HALF_CLOSED_LOCAL,
    H2_STREAM_HALF_CLOSED_REMOTE,
    H2_STREAM_CLOSED,
    H2_STREAM_RESERVED_LOCAL,
    H2_STREAM_RESERVED_REMOTE,
} h2_stream_state_t;

/*
 * ============================================================
 * DATA STRUCTURES
 * ============================================================
 */

/* Raw frame header */
typedef struct {
    uint32_t length;    /* 24-bit payload length */
    uint8_t  type;
    uint8_t  flags;
    uint32_t stream_id; /* 31-bit (high bit reserved) */
} h2_frame_header_t;

/* Connection settings (both local and remote copies maintained) */
typedef struct {
    uint32_t header_table_size;
    uint32_t enable_push;
    uint32_t max_concurrent_streams;
    uint32_t initial_window_size;
    uint32_t max_frame_size;
    uint32_t max_header_list_size;
} h2_settings_t;

/* Header field (name-value pair) */
typedef struct {
    char    *name;
    size_t   name_len;
    char    *value;
    size_t   value_len;
    bool     never_indexed; /* sensitive header */
} h2_header_t;

/* HPACK dynamic table entry */
typedef struct h2_hpack_entry {
    char   *name;
    size_t  name_len;
    char   *value;
    size_t  value_len;
    struct h2_hpack_entry *next;
} h2_hpack_entry_t;

/* HPACK encoder/decoder state */
typedef struct {
    h2_hpack_entry_t *dynamic_table;  /* head = index 62 */
    size_t            dynamic_size;   /* current byte size */
    size_t            dynamic_max;    /* HEADER_TABLE_SIZE setting */
    uint32_t          dynamic_count;  /* number of entries */
} h2_hpack_t;

/* Stream state */
typedef struct h2_stream {
    uint32_t          id;
    h2_stream_state_t state;
    int32_t           send_window;   /* flow control window for sending */
    int32_t           recv_window;   /* flow control window for receiving */
    uint8_t           weight;        /* priority weight (1-256) */
    uint32_t          dependency;    /* parent stream ID */
    bool              exclusive;

    /* Accumulated header block (HEADERS + CONTINUATIONs) */
    uint8_t          *header_buf;
    size_t            header_buf_len;
    size_t            header_buf_cap;

    struct h2_stream *next;          /* linked list in connection */
} h2_stream_t;

/* Connection state */
typedef struct {
    int               fd;             /* TCP socket */
    h2_settings_t     local_settings;
    h2_settings_t     remote_settings;
    int32_t           send_window;    /* connection-level send window */
    int32_t           recv_window;    /* connection-level recv window */
    h2_hpack_t        encoder;        /* for compressing outgoing headers */
    h2_hpack_t        decoder;        /* for decompressing incoming headers */
    uint32_t          next_stream_id; /* next client stream ID to use (odd) */
    uint32_t          last_stream_id; /* highest stream ID seen from remote */
    h2_stream_t      *streams;        /* open streams */
    bool              goaway_sent;
    bool              goaway_received;
    uint32_t          goaway_last_id;
    bool              settings_pending_ack;
} h2_conn_t;

/*
 * ============================================================
 * FRAME WIRE FORMAT PARSING
 * ============================================================
 * All multi-byte integers in HTTP/2 are big-endian (network byte order).
 */

/*
 * Read exactly 'n' bytes from fd into buf.
 * Returns 0 on success, -1 on EOF/error.
 */
static int read_exact(int fd, uint8_t *buf, size_t n) {
    size_t total = 0;
    while (total < n) {
        ssize_t r = read(fd, buf + total, n - total);
        if (r <= 0) return -1;
        total += (size_t)r;
    }
    return 0;
}

/*
 * Write exactly 'n' bytes from buf to fd.
 */
static int write_exact(int fd, const uint8_t *buf, size_t n) {
    size_t total = 0;
    while (total < n) {
        ssize_t w = write(fd, buf + total, n - total);
        if (w <= 0) return -1;
        total += (size_t)w;
    }
    return 0;
}

/*
 * Parse 9-byte frame header from raw bytes.
 *
 * Wire format (big-endian):
 *   Bytes 0-2: Length (24 bits)
 *   Byte  3:   Type
 *   Byte  4:   Flags
 *   Bytes 5-8: Reserved(1) + Stream ID(31)
 */
static void h2_parse_frame_header(const uint8_t *buf, h2_frame_header_t *hdr) {
    /* 24-bit length — network byte order */
    hdr->length = ((uint32_t)buf[0] << 16)
                | ((uint32_t)buf[1] << 8)
                |  (uint32_t)buf[2];

    hdr->type  = buf[3];
    hdr->flags = buf[4];

    /* 31-bit stream ID — mask out reserved bit */
    hdr->stream_id = (((uint32_t)buf[5] << 24)
                    | ((uint32_t)buf[6] << 16)
                    | ((uint32_t)buf[7] << 8)
                    |  (uint32_t)buf[8]) & 0x7FFFFFFF;
}

/*
 * Serialize frame header to 9 bytes (big-endian).
 */
static void h2_serialize_frame_header(uint8_t *buf,
                                       uint32_t length,
                                       uint8_t  type,
                                       uint8_t  flags,
                                       uint32_t stream_id) {
    buf[0] = (length >> 16) & 0xFF;
    buf[1] = (length >> 8)  & 0xFF;
    buf[2] =  length        & 0xFF;
    buf[3] = type;
    buf[4] = flags;
    /* stream_id: high bit (reserved) = 0 */
    buf[5] = (stream_id >> 24) & 0x7F;
    buf[6] = (stream_id >> 16) & 0xFF;
    buf[7] = (stream_id >> 8)  & 0xFF;
    buf[8] =  stream_id        & 0xFF;
}

/*
 * ============================================================
 * HPACK INTEGER ENCODING / DECODING
 * ============================================================
 */

/*
 * Decode HPACK integer from 'src' with 'prefix_bits' prefix size.
 * Returns number of bytes consumed, or -1 on error.
 * Decoded value stored in *value.
 *
 * RFC 7541 §5.1
 */
static int hpack_decode_int(const uint8_t *src, size_t src_len,
                             int prefix_bits, uint32_t *value) {
    if (src_len == 0) return -1;

    uint8_t mask = (1 << prefix_bits) - 1;
    uint32_t v = src[0] & mask;
    int pos = 1;

    if (v < mask) {
        /* Value fits in prefix bits */
        *value = v;
        return 1;
    }

    /* Multi-byte integer */
    uint32_t m = 0;
    while (pos < (int)src_len) {
        uint8_t b = src[pos++];
        v += (b & 0x7F) << m;
        m += 7;
        if (!(b & 0x80)) {
            /* Last byte (high bit clear) */
            *value = v;
            return pos;
        }
        if (m > 28) return -1; /* overflow protection */
    }

    return -1; /* truncated */
}

/*
 * Encode integer with 'prefix_bits' prefix, starting at 'dst'.
 * The top (8 - prefix_bits) bits of dst[0] are preserved (caller sets them).
 * Returns number of bytes written.
 */
static int hpack_encode_int(uint8_t *dst, size_t dst_cap,
                             uint32_t value, int prefix_bits) {
    uint8_t max_prefix = (1 << prefix_bits) - 1;

    if (value < max_prefix) {
        dst[0] = (dst[0] & ~max_prefix) | (uint8_t)value;
        return 1;
    }

    dst[0] = (dst[0] & ~max_prefix) | max_prefix;
    value -= max_prefix;
    int pos = 1;

    while (value >= 128) {
        if (pos >= (int)dst_cap) return -1;
        dst[pos++] = (value & 0x7F) | 0x80;
        value >>= 7;
    }
    if (pos >= (int)dst_cap) return -1;
    dst[pos++] = (uint8_t)value;

    return pos;
}

/*
 * ============================================================
 * HPACK STATIC TABLE
 * ============================================================
 */

typedef struct {
    const char *name;
    const char *value; /* NULL if value-less entry */
} hpack_static_entry_t;

static const hpack_static_entry_t hpack_static_table[62] = {
    {NULL, NULL}, /* index 0 unused */
    {":authority",                  NULL},
    {":method",                     "GET"},
    {":method",                     "POST"},
    {":path",                       "/"},
    {":path",                       "/index.html"},
    {":scheme",                     "http"},
    {":scheme",                     "https"},
    {":status",                     "200"},
    {":status",                     "204"},
    {":status",                     "206"},
    {":status",                     "304"},
    {":status",                     "400"},
    {":status",                     "404"},
    {":status",                     "500"},
    {"accept-charset",              NULL},
    {"accept-encoding",             "gzip, deflate"},
    {"accept-language",             NULL},
    {"accept-ranges",               NULL},
    {"accept",                      NULL},
    {"access-control-allow-origin", NULL},
    {"age",                         NULL},
    {"allow",                       NULL},
    {"authorization",               NULL},
    {"cache-control",               NULL},
    {"content-disposition",         NULL},
    {"content-encoding",            NULL},
    {"content-language",            NULL},
    {"content-length",              NULL},
    {"content-location",            NULL},
    {"content-range",               NULL},
    {"content-type",                NULL},
    {"cookie",                      NULL},
    {"date",                        NULL},
    {"etag",                        NULL},
    {"expect",                      NULL},
    {"expires",                     NULL},
    {"from",                        NULL},
    {"host",                        NULL},
    {"if-match",                    NULL},
    {"if-modified-since",           NULL},
    {"if-none-match",               NULL},
    {"if-range",                    NULL},
    {"if-unmodified-since",         NULL},
    {"last-modified",               NULL},
    {"link",                        NULL},
    {"location",                    NULL},
    {"max-forwards",                NULL},
    {"proxy-authenticate",          NULL},
    {"proxy-authorization",         NULL},
    {"range",                       NULL},
    {"referer",                     NULL},
    {"refresh",                     NULL},
    {"retry-after",                 NULL},
    {"server",                      NULL},
    {"set-cookie",                  NULL},
    {"strict-transport-security",   NULL},
    {"te",                          NULL},
    {"transfer-encoding",           NULL},
    {"user-agent",                  NULL},
    {"vary",                        NULL},
    {"via",                         NULL},
    {"www-authenticate",            NULL},
};

/*
 * ============================================================
 * HPACK DYNAMIC TABLE OPERATIONS
 * ============================================================
 */

static void hpack_init(h2_hpack_t *h, size_t max_size) {
    memset(h, 0, sizeof(*h));
    h->dynamic_max = max_size;
}

static void hpack_entry_free(h2_hpack_entry_t *e) {
    if (!e) return;
    free(e->name);
    free(e->value);
    free(e);
}

/*
 * Evict entries until size <= target.
 */
static void hpack_evict_to(h2_hpack_t *h, size_t target) {
    /*
     * Dynamic table is a deque: head = newest (index 62),
     * tail = oldest (highest index).
     * Evict from the tail (oldest).
     */
    while (h->dynamic_size > target && h->dynamic_count > 0) {
        /* Find the last entry */
        h2_hpack_entry_t *prev = NULL;
        h2_hpack_entry_t *cur  = h->dynamic_table;
        while (cur && cur->next) {
            prev = cur;
            cur  = cur->next;
        }
        if (!cur) break;

        /* Compute entry size: name_len + value_len + 32 */
        size_t entry_size = cur->name_len + cur->value_len + 32;
        h->dynamic_size  -= entry_size;
        h->dynamic_count -= 1;

        if (prev) prev->next = NULL;
        else      h->dynamic_table = NULL;

        hpack_entry_free(cur);
    }
}

/*
 * Add a new entry to the dynamic table front (index 62).
 */
static int hpack_add_entry(h2_hpack_t *h,
                            const char *name,  size_t name_len,
                            const char *value, size_t value_len) {
    size_t entry_size = name_len + value_len + 32;

    /* If the entry itself exceeds the table max, evict everything */
    if (entry_size > h->dynamic_max) {
        hpack_evict_to(h, 0);
        return 0; /* not added */
    }

    /* Evict until there's room */
    hpack_evict_to(h, h->dynamic_max - entry_size);

    h2_hpack_entry_t *e = calloc(1, sizeof(*e));
    if (!e) return -1;

    e->name     = strndup(name,  name_len);
    e->value    = strndup(value, value_len);
    e->name_len  = name_len;
    e->value_len = value_len;

    /* Prepend to list (becomes index 62) */
    e->next          = h->dynamic_table;
    h->dynamic_table = e;
    h->dynamic_size += entry_size;
    h->dynamic_count += 1;

    return 0;
}

/*
 * Look up an entry by absolute index (1 = static[1], 62+ = dynamic).
 * Returns pointer to name and value strings.
 */
static int hpack_lookup(h2_hpack_t *h, uint32_t index,
                         const char **name,  size_t *name_len,
                         const char **value, size_t *value_len) {
    if (index == 0) return -1;

    if (index <= 61) {
        /* Static table */
        const hpack_static_entry_t *e = &hpack_static_table[index];
        *name     = e->name;
        *name_len  = e->name ? strlen(e->name) : 0;
        *value    = e->value ? e->value : "";
        *value_len = e->value ? strlen(e->value) : 0;
        return 0;
    }

    /* Dynamic table */
    uint32_t dyn_idx = index - 62; /* 0 = first (newest) */
    h2_hpack_entry_t *e = h->dynamic_table;
    for (uint32_t i = 0; i < dyn_idx; i++) {
        if (!e) return -1;
        e = e->next;
    }
    if (!e) return -1;

    *name      = e->name;
    *name_len  = e->name_len;
    *value     = e->value;
    *value_len = e->value_len;
    return 0;
}

/*
 * ============================================================
 * HPACK DECODING
 * ============================================================
 */

/*
 * Decode a complete HPACK header block.
 * 'out' array must be pre-allocated, 'out_count' is max headers.
 * Returns number of headers decoded, or -1 on error.
 */
int hpack_decode(h2_hpack_t *h,
                 const uint8_t *src, size_t src_len,
                 h2_header_t *out, size_t out_max) {
    size_t pos   = 0;
    size_t count = 0;

    while (pos < src_len && count < out_max) {
        uint8_t first = src[pos];

        if (first & 0x80) {
            /*
             * Indexed Header Field Representation
             * Pattern: 1xxxxxxx
             * Entire header (name + value) from table.
             */
            uint32_t index;
            int consumed = hpack_decode_int(src + pos, src_len - pos, 7, &index);
            if (consumed < 0 || index == 0) return -1;
            pos += consumed;

            const char *name, *value;
            size_t name_len, value_len;
            if (hpack_lookup(h, index, &name, &name_len, &value, &value_len) < 0)
                return -1;

            out[count].name          = strndup(name,  name_len);
            out[count].name_len      = name_len;
            out[count].value         = strndup(value, value_len);
            out[count].value_len     = value_len;
            out[count].never_indexed = false;
            count++;

        } else if ((first & 0xC0) == 0x40) {
            /*
             * Literal Header Field with Incremental Indexing
             * Pattern: 01xxxxxx
             * Add to dynamic table.
             */
            bool never_idx = false;
            uint32_t name_index;
            int consumed = hpack_decode_int(src + pos, src_len - pos, 6, &name_index);
            if (consumed < 0) return -1;
            pos += consumed;

            char *name;
            size_t name_len;

            if (name_index == 0) {
                /* Literal name */
                if (pos >= src_len) return -1;
                bool huffman = (src[pos] & 0x80) != 0;
                uint32_t slen;
                consumed = hpack_decode_int(src + pos, src_len - pos, 7, &slen);
                if (consumed < 0) return -1;
                pos += consumed;
                (void)huffman; /* Simplified: skip Huffman decode */
                name     = strndup((const char *)src + pos, slen);
                name_len = slen;
                pos += slen;
            } else {
                const char *sname;
                size_t sname_len;
                const char *dummy;
                size_t dummy_len;
                if (hpack_lookup(h, name_index, &sname, &sname_len, &dummy, &dummy_len) < 0)
                    return -1;
                name     = strndup(sname, sname_len);
                name_len = sname_len;
            }

            /* Decode value */
            if (pos >= src_len) { free(name); return -1; }
            bool huffman = (src[pos] & 0x80) != 0;
            uint32_t vlen;
            consumed = hpack_decode_int(src + pos, src_len - pos, 7, &vlen);
            if (consumed < 0) { free(name); return -1; }
            pos += consumed;
            (void)huffman;
            char *value = strndup((const char *)src + pos, vlen);
            pos += vlen;

            out[count].name          = name;
            out[count].name_len      = name_len;
            out[count].value         = value;
            out[count].value_len     = vlen;
            out[count].never_indexed = never_idx;
            count++;

            /* Add to dynamic table */
            hpack_add_entry(h, name, name_len, value, vlen);

        } else if ((first & 0xF0) == 0x00 || (first & 0xF0) == 0x10) {
            /*
             * Literal Header Field without Indexing (0000xxxx)
             * or Literal Header Field Never Indexed (0001xxxx)
             */
            bool never_idx = (first & 0xF0) == 0x10;
            uint32_t name_index;
            int consumed = hpack_decode_int(src + pos, src_len - pos, 4, &name_index);
            if (consumed < 0) return -1;
            pos += consumed;

            char *name;
            size_t name_len;

            if (name_index == 0) {
                if (pos >= src_len) return -1;
                bool huffman = (src[pos] & 0x80) != 0;
                uint32_t slen;
                consumed = hpack_decode_int(src + pos, src_len - pos, 7, &slen);
                if (consumed < 0) return -1;
                pos += consumed;
                (void)huffman;
                name     = strndup((const char *)src + pos, slen);
                name_len = slen;
                pos += slen;
            } else {
                const char *sname;
                size_t sname_len;
                const char *dummy;
                size_t dummy_len;
                if (hpack_lookup(h, name_index, &sname, &sname_len, &dummy, &dummy_len) < 0)
                    return -1;
                name     = strndup(sname, sname_len);
                name_len = sname_len;
            }

            if (pos >= src_len) { free(name); return -1; }
            bool huffman = (src[pos] & 0x80) != 0;
            uint32_t vlen;
            consumed = hpack_decode_int(src + pos, src_len - pos, 7, &vlen);
            if (consumed < 0) { free(name); return -1; }
            pos += consumed;
            (void)huffman;
            char *value = strndup((const char *)src + pos, vlen);
            pos += vlen;

            out[count].name          = name;
            out[count].name_len      = name_len;
            out[count].value         = value;
            out[count].value_len     = vlen;
            out[count].never_indexed = never_idx;
            count++;
            /* NOT added to dynamic table */

        } else if ((first & 0xE0) == 0x20) {
            /*
             * Dynamic Table Size Update: 001xxxxx
             */
            uint32_t new_size;
            int consumed = hpack_decode_int(src + pos, src_len - pos, 5, &new_size);
            if (consumed < 0) return -1;
            pos += consumed;

            if (new_size > h->dynamic_max) return -1; /* COMPRESSION_ERROR */
            h->dynamic_max = new_size;
            hpack_evict_to(h, new_size);
        } else {
            return -1; /* unknown */
        }
    }

    return (int)count;
}

/*
 * ============================================================
 * SENDING FRAMES
 * ============================================================
 */

/*
 * Send a SETTINGS frame.
 * 'pairs' is an array of {id, value} pairs, 'count' is the number of pairs.
 * Setting count=0 and ack=true sends a SETTINGS ACK.
 */
typedef struct { uint16_t id; uint32_t value; } h2_setting_pair_t;

static int h2_send_settings(int fd,
                             const h2_setting_pair_t *pairs,
                             size_t count,
                             bool ack) {
    size_t payload_len = count * 6;
    uint8_t buf[9 + 6 * 10]; /* max 10 settings */
    if (count > 10) return -1;

    h2_serialize_frame_header(buf,
                               (uint32_t)payload_len,
                               H2_FRAME_SETTINGS,
                               ack ? H2_FLAG_ACK : 0,
                               0 /* stream 0 */);

    for (size_t i = 0; i < count; i++) {
        size_t off = 9 + i * 6;
        buf[off + 0] = (pairs[i].id >> 8) & 0xFF;
        buf[off + 1] =  pairs[i].id       & 0xFF;
        buf[off + 2] = (pairs[i].value >> 24) & 0xFF;
        buf[off + 3] = (pairs[i].value >> 16) & 0xFF;
        buf[off + 4] = (pairs[i].value >> 8)  & 0xFF;
        buf[off + 5] =  pairs[i].value         & 0xFF;
    }

    return write_exact(fd, buf, 9 + payload_len);
}

/*
 * Send a PING frame.
 */
static int h2_send_ping(int fd, const uint8_t data[8], bool ack) {
    uint8_t buf[17];
    h2_serialize_frame_header(buf, 8, H2_FRAME_PING,
                               ack ? H2_FLAG_ACK : 0, 0);
    memcpy(buf + 9, data, 8);
    return write_exact(fd, buf, 17);
}

/*
 * Send a WINDOW_UPDATE frame.
 */
static int h2_send_window_update(int fd, uint32_t stream_id, uint32_t increment) {
    uint8_t buf[13];
    h2_serialize_frame_header(buf, 4, H2_FRAME_WINDOW_UPDATE, 0, stream_id);
    buf[ 9] = (increment >> 24) & 0x7F; /* mask reserved bit */
    buf[10] = (increment >> 16) & 0xFF;
    buf[11] = (increment >> 8)  & 0xFF;
    buf[12] =  increment         & 0xFF;
    return write_exact(fd, buf, 13);
}

/*
 * Send RST_STREAM frame.
 */
static int h2_send_rst_stream(int fd, uint32_t stream_id, h2_error_code_t error) {
    uint8_t buf[13];
    h2_serialize_frame_header(buf, 4, H2_FRAME_RST_STREAM, 0, stream_id);
    uint32_t code = (uint32_t)error;
    buf[ 9] = (code >> 24) & 0xFF;
    buf[10] = (code >> 16) & 0xFF;
    buf[11] = (code >> 8)  & 0xFF;
    buf[12] =  code         & 0xFF;
    return write_exact(fd, buf, 13);
}

/*
 * Send GOAWAY frame.
 */
static int h2_send_goaway(int fd, uint32_t last_stream_id,
                           h2_error_code_t error,
                           const char *debug, size_t debug_len) {
    size_t payload = 8 + debug_len;
    uint8_t *buf = malloc(9 + payload);
    if (!buf) return -1;

    h2_serialize_frame_header(buf, (uint32_t)payload,
                               H2_FRAME_GOAWAY, 0, 0);

    uint32_t lsid = last_stream_id & 0x7FFFFFFF;
    buf[ 9] = (lsid >> 24) & 0x7F;
    buf[10] = (lsid >> 16) & 0xFF;
    buf[11] = (lsid >> 8)  & 0xFF;
    buf[12] =  lsid         & 0xFF;

    uint32_t code = (uint32_t)error;
    buf[13] = (code >> 24) & 0xFF;
    buf[14] = (code >> 16) & 0xFF;
    buf[15] = (code >> 8)  & 0xFF;
    buf[16] =  code         & 0xFF;

    if (debug && debug_len > 0)
        memcpy(buf + 17, debug, debug_len);

    int ret = write_exact(fd, buf, 9 + payload);
    free(buf);
    return ret;
}

/*
 * Send DATA frame (with body bytes).
 */
static int h2_send_data(int fd, uint32_t stream_id,
                         const uint8_t *data, uint32_t len,
                         bool end_stream) {
    uint8_t hdr[9];
    h2_serialize_frame_header(hdr, len, H2_FRAME_DATA,
                               end_stream ? H2_FLAG_END_STREAM : 0,
                               stream_id);
    if (write_exact(fd, hdr, 9) < 0) return -1;
    if (len > 0 && write_exact(fd, data, len) < 0) return -1;
    return 0;
}

/*
 * ============================================================
 * FRAME READING
 * ============================================================
 */

/*
 * Read one complete frame from fd.
 * 'payload' is allocated by this function, caller must free().
 * Returns 0 on success, -1 on error.
 */
static int h2_read_frame(int fd, h2_frame_header_t *hdr, uint8_t **payload) {
    uint8_t raw[9];
    if (read_exact(fd, raw, 9) < 0) return -1;
    h2_parse_frame_header(raw, hdr);

    if (hdr->length == 0) {
        *payload = NULL;
        return 0;
    }

    *payload = malloc(hdr->length);
    if (!*payload) return -1;

    if (read_exact(fd, *payload, hdr->length) < 0) {
        free(*payload);
        *payload = NULL;
        return -1;
    }

    return 0;
}

/*
 * ============================================================
 * SETTINGS FRAME PARSING
 * ============================================================
 */

static int h2_parse_settings(const uint8_t *payload, size_t len,
                               h2_settings_t *settings) {
    if (len % 6 != 0) return -1; /* FRAME_SIZE_ERROR */

    for (size_t i = 0; i < len; i += 6) {
        uint16_t id  = ((uint16_t)payload[i]   << 8) | payload[i+1];
        uint32_t val = ((uint32_t)payload[i+2] << 24)
                     | ((uint32_t)payload[i+3] << 16)
                     | ((uint32_t)payload[i+4] << 8)
                     |  (uint32_t)payload[i+5];

        switch ((h2_setting_id_t)id) {
            case H2_SETTINGS_HEADER_TABLE_SIZE:
                settings->header_table_size = val;
                break;
            case H2_SETTINGS_ENABLE_PUSH:
                if (val > 1) return -1; /* PROTOCOL_ERROR */
                settings->enable_push = val;
                break;
            case H2_SETTINGS_MAX_CONCURRENT_STREAMS:
                settings->max_concurrent_streams = val;
                break;
            case H2_SETTINGS_INITIAL_WINDOW_SIZE:
                if (val > (uint32_t)H2_MAX_WINDOW) return -1; /* FLOW_CONTROL_ERROR */
                settings->initial_window_size = val;
                break;
            case H2_SETTINGS_MAX_FRAME_SIZE:
                if (val < H2_MAX_FRAME_SIZE_MIN || val > H2_MAX_FRAME_SIZE_MAX)
                    return -1; /* PROTOCOL_ERROR */
                settings->max_frame_size = val;
                break;
            case H2_SETTINGS_MAX_HEADER_LIST_SIZE:
                settings->max_header_list_size = val;
                break;
            default:
                /* Unknown settings MUST be ignored (RFC 7540 §6.5) */
                break;
        }
    }

    return 0;
}

/*
 * ============================================================
 * CONNECTION INITIALIZATION
 * ============================================================
 */

static void h2_default_settings(h2_settings_t *s) {
    s->header_table_size      = 4096;
    s->enable_push            = 1;
    s->max_concurrent_streams = 100;
    s->initial_window_size    = H2_DEFAULT_WINDOW;
    s->max_frame_size         = H2_MAX_FRAME_SIZE_MIN;
    s->max_header_list_size   = UINT32_MAX;
}

static int h2_conn_init(h2_conn_t *conn, int fd) {
    memset(conn, 0, sizeof(*conn));
    conn->fd = fd;
    h2_default_settings(&conn->local_settings);
    h2_default_settings(&conn->remote_settings);
    conn->send_window    = H2_DEFAULT_WINDOW;
    conn->recv_window    = H2_DEFAULT_WINDOW;
    conn->next_stream_id = 1; /* client starts at 1 */
    hpack_init(&conn->encoder, conn->local_settings.header_table_size);
    hpack_init(&conn->decoder, conn->remote_settings.header_table_size);
    return 0;
}

/*
 * Send client connection preface + initial SETTINGS.
 */
static int h2_send_client_preface(h2_conn_t *conn) {
    /* Magic preface bytes */
    if (write_exact(conn->fd,
                    (const uint8_t *)H2_CLIENT_PREFACE,
                    H2_CLIENT_PREFACE_LEN) < 0)
        return -1;

    /* Send initial settings */
    h2_setting_pair_t pairs[] = {
        {H2_SETTINGS_MAX_CONCURRENT_STREAMS, 100},
        {H2_SETTINGS_INITIAL_WINDOW_SIZE,    H2_DEFAULT_WINDOW},
        {H2_SETTINGS_MAX_FRAME_SIZE,         H2_MAX_FRAME_SIZE_MIN},
    };
    return h2_send_settings(conn->fd, pairs,
                             sizeof(pairs) / sizeof(pairs[0]), false);
}

/*
 * ============================================================
 * EXAMPLE: FRAME PRINTER (for debugging)
 * ============================================================
 */

static const char *h2_frame_type_name(uint8_t type) {
    switch (type) {
        case H2_FRAME_DATA:          return "DATA";
        case H2_FRAME_HEADERS:       return "HEADERS";
        case H2_FRAME_PRIORITY:      return "PRIORITY";
        case H2_FRAME_RST_STREAM:    return "RST_STREAM";
        case H2_FRAME_SETTINGS:      return "SETTINGS";
        case H2_FRAME_PUSH_PROMISE:  return "PUSH_PROMISE";
        case H2_FRAME_PING:          return "PING";
        case H2_FRAME_GOAWAY:        return "GOAWAY";
        case H2_FRAME_WINDOW_UPDATE: return "WINDOW_UPDATE";
        case H2_FRAME_CONTINUATION:  return "CONTINUATION";
        default:                     return "UNKNOWN";
    }
}

static void h2_print_frame(const h2_frame_header_t *hdr,
                             const uint8_t *payload) {
    printf("[FRAME] type=%-14s stream=%-5u length=%-6u flags=0x%02x\n",
           h2_frame_type_name(hdr->type),
           hdr->stream_id,
           hdr->length,
           hdr->flags);

    switch (hdr->type) {
        case H2_FRAME_SETTINGS:
            if (hdr->flags & H2_FLAG_ACK) {
                printf("  ACK\n");
            } else {
                for (size_t i = 0; i + 6 <= hdr->length; i += 6) {
                    uint16_t id  = ((uint16_t)payload[i] << 8) | payload[i+1];
                    uint32_t val = ((uint32_t)payload[i+2] << 24)
                                 | ((uint32_t)payload[i+3] << 16)
                                 | ((uint32_t)payload[i+4] << 8)
                                 |  (uint32_t)payload[i+5];
                    printf("  id=0x%04x val=%u\n", id, val);
                }
            }
            break;

        case H2_FRAME_RST_STREAM:
            if (hdr->length >= 4) {
                uint32_t code = ((uint32_t)payload[0] << 24)
                              | ((uint32_t)payload[1] << 16)
                              | ((uint32_t)payload[2] << 8)
                              |  (uint32_t)payload[3];
                printf("  error_code=0x%08x\n", code);
            }
            break;

        case H2_FRAME_GOAWAY:
            if (hdr->length >= 8) {
                uint32_t last = (((uint32_t)payload[0] << 24)
                               | ((uint32_t)payload[1] << 16)
                               | ((uint32_t)payload[2] << 8)
                               |  (uint32_t)payload[3]) & 0x7FFFFFFF;
                uint32_t code = ((uint32_t)payload[4] << 24)
                              | ((uint32_t)payload[5] << 16)
                              | ((uint32_t)payload[6] << 8)
                              |  (uint32_t)payload[7];
                printf("  last_stream=%u error=0x%08x\n", last, code);
                if (hdr->length > 8) {
                    printf("  debug: %.*s\n", (int)(hdr->length - 8), payload + 8);
                }
            }
            break;

        case H2_FRAME_WINDOW_UPDATE:
            if (hdr->length >= 4) {
                uint32_t inc = (((uint32_t)payload[0] << 24)
                              | ((uint32_t)payload[1] << 16)
                              | ((uint32_t)payload[2] << 8)
                              |  (uint32_t)payload[3]) & 0x7FFFFFFF;
                printf("  increment=%u\n", inc);
            }
            break;

        default:
            break;
    }
}

/*
 * ============================================================
 * MAIN FRAME DISPATCH LOOP (server/client event loop core)
 * ============================================================
 */

typedef struct {
    void (*on_headers)(h2_conn_t *conn, uint32_t stream_id,
                       h2_header_t *headers, size_t count,
                       bool end_stream, void *user);
    void (*on_data)(h2_conn_t *conn, uint32_t stream_id,
                    const uint8_t *data, size_t len,
                    bool end_stream, void *user);
    void (*on_rst_stream)(h2_conn_t *conn, uint32_t stream_id,
                          h2_error_code_t error, void *user);
    void (*on_goaway)(h2_conn_t *conn, uint32_t last_stream_id,
                      h2_error_code_t error, void *user);
    void *user;
} h2_callbacks_t;

/*
 * Process one frame from the connection.
 * Returns 0 to continue, 1 to stop (GOAWAY received), -1 on fatal error.
 */
int h2_process_frame(h2_conn_t *conn, const h2_callbacks_t *cb) {
    h2_frame_header_t hdr;
    uint8_t *payload = NULL;

    if (h2_read_frame(conn->fd, &hdr, &payload) < 0) {
        return -1;
    }

    /* Verify frame size */
    if (hdr.length > conn->local_settings.max_frame_size) {
        free(payload);
        h2_send_goaway(conn->fd, conn->last_stream_id,
                        H2_ERR_FRAME_SIZE_ERROR, NULL, 0);
        return -1;
    }

    h2_print_frame(&hdr, payload);

    int ret = 0;
    switch (hdr.type) {

        case H2_FRAME_SETTINGS:
            if (hdr.stream_id != 0) {
                /* SETTINGS on non-zero stream = PROTOCOL_ERROR */
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }
            if (hdr.flags & H2_FLAG_ACK) {
                /* ACK of our SETTINGS */
                if (hdr.length != 0) {
                    free(payload);
                    h2_send_goaway(conn->fd, conn->last_stream_id,
                                    H2_ERR_FRAME_SIZE_ERROR, NULL, 0);
                    return -1;
                }
                conn->settings_pending_ack = false;
            } else {
                /* Remote sent new settings */
                if (h2_parse_settings(payload, hdr.length,
                                       &conn->remote_settings) < 0) {
                    free(payload);
                    h2_send_goaway(conn->fd, conn->last_stream_id,
                                    H2_ERR_PROTOCOL_ERROR, NULL, 0);
                    return -1;
                }
                /* MUST send ACK */
                h2_send_settings(conn->fd, NULL, 0, true);
            }
            break;

        case H2_FRAME_PING:
            if (hdr.stream_id != 0 || hdr.length != 8) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }
            if (!(hdr.flags & H2_FLAG_ACK)) {
                /* MUST respond with PING ACK */
                h2_send_ping(conn->fd, payload, true);
            }
            break;

        case H2_FRAME_WINDOW_UPDATE: {
            if (hdr.length != 4) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_FRAME_SIZE_ERROR, NULL, 0);
                return -1;
            }
            uint32_t inc = (((uint32_t)payload[0] << 24)
                          | ((uint32_t)payload[1] << 16)
                          | ((uint32_t)payload[2] << 8)
                          |  (uint32_t)payload[3]) & 0x7FFFFFFF;
            if (inc == 0) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }
            if (hdr.stream_id == 0) {
                conn->send_window += (int32_t)inc;
                if (conn->send_window > H2_MAX_WINDOW) {
                    free(payload);
                    h2_send_goaway(conn->fd, conn->last_stream_id,
                                    H2_ERR_FLOW_CONTROL_ERROR, NULL, 0);
                    return -1;
                }
            }
            /* Stream-level window update handled similarly */
            break;
        }

        case H2_FRAME_GOAWAY:
            if (hdr.length >= 8 && cb && cb->on_goaway) {
                uint32_t last = (((uint32_t)payload[0] << 24)
                               | ((uint32_t)payload[1] << 16)
                               | ((uint32_t)payload[2] << 8)
                               |  (uint32_t)payload[3]) & 0x7FFFFFFF;
                uint32_t code = ((uint32_t)payload[4] << 24)
                              | ((uint32_t)payload[5] << 16)
                              | ((uint32_t)payload[6] << 8)
                              |  (uint32_t)payload[7];
                cb->on_goaway(conn, last, (h2_error_code_t)code, cb->user);
            }
            conn->goaway_received = true;
            ret = 1; /* stop processing */
            break;

        case H2_FRAME_RST_STREAM:
            if (hdr.length != 4 || hdr.stream_id == 0) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }
            if (cb && cb->on_rst_stream) {
                uint32_t code = ((uint32_t)payload[0] << 24)
                              | ((uint32_t)payload[1] << 16)
                              | ((uint32_t)payload[2] << 8)
                              |  (uint32_t)payload[3];
                cb->on_rst_stream(conn, hdr.stream_id,
                                   (h2_error_code_t)code, cb->user);
            }
            break;

        case H2_FRAME_HEADERS: {
            if (hdr.stream_id == 0) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }

            /* Update last seen stream ID */
            if (hdr.stream_id > conn->last_stream_id)
                conn->last_stream_id = hdr.stream_id;

            /* Decode HPACK */
            uint8_t *hpack_data = payload;
            size_t   hpack_len  = hdr.length;
            uint8_t  pad_len    = 0;
            size_t   skip       = 0;

            if (hdr.flags & H2_FLAG_PADDED) {
                pad_len = payload[0];
                skip += 1;
            }
            if (hdr.flags & H2_FLAG_PRIORITY) {
                skip += 5; /* E(1) + dependency(31) + weight(8) = 5 bytes */
            }

            hpack_data += skip;
            hpack_len   = hdr.length - skip - pad_len;

            h2_header_t headers[64];
            int nhdrs = hpack_decode(&conn->decoder,
                                      hpack_data, hpack_len,
                                      headers, 64);
            if (nhdrs < 0) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_COMPRESSION_ERROR, NULL, 0);
                return -1;
            }

            bool end_stream  = (hdr.flags & H2_FLAG_END_STREAM)  != 0;
            bool end_headers = (hdr.flags & H2_FLAG_END_HEADERS) != 0;
            (void)end_headers; /* CONTINUATION handling omitted for brevity */

            if (cb && cb->on_headers)
                cb->on_headers(conn, hdr.stream_id,
                                headers, (size_t)nhdrs,
                                end_stream, cb->user);

            /* Free decoded header strings */
            for (int i = 0; i < nhdrs; i++) {
                free(headers[i].name);
                free(headers[i].value);
            }
            break;
        }

        case H2_FRAME_DATA: {
            if (hdr.stream_id == 0) {
                free(payload);
                h2_send_goaway(conn->fd, conn->last_stream_id,
                                H2_ERR_PROTOCOL_ERROR, NULL, 0);
                return -1;
            }

            uint8_t *data    = payload;
            size_t   data_len = hdr.length;
            uint8_t  pad_len  = 0;

            if (hdr.flags & H2_FLAG_PADDED) {
                pad_len  = payload[0];
                data     = payload + 1;
                data_len = hdr.length - 1 - pad_len;
            }

            /* Flow control: update receive window */
            conn->recv_window -= (int32_t)data_len;
            /* If window drops below threshold, send WINDOW_UPDATE */
            if (conn->recv_window < H2_DEFAULT_WINDOW / 2) {
                uint32_t inc = H2_DEFAULT_WINDOW - conn->recv_window;
                h2_send_window_update(conn->fd, 0, inc);
                conn->recv_window = H2_DEFAULT_WINDOW;
            }

            bool end_stream = (hdr.flags & H2_FLAG_END_STREAM) != 0;
            if (cb && cb->on_data)
                cb->on_data(conn, hdr.stream_id,
                             data, data_len,
                             end_stream, cb->user);
            break;
        }

        default:
            /* Unknown frame types MUST be ignored (§4.1) */
            break;
    }

    free(payload);
    return ret;
}

#endif /* HTTP2_H */
```

```c
/* main.c — Example usage of HTTP/2 implementation */

#include "http2.h"
#include <arpa/inet.h>
#include <netinet/in.h>

/*
 * Simple HTTP/2 server that responds "Hello, HTTP/2!" to any request.
 * (Cleartext h2c — for demonstration without TLS)
 */

typedef struct {
    uint32_t last_stream;
    char     method[32];
    char     path[256];
} server_ctx_t;

static void on_headers(h2_conn_t *conn, uint32_t stream_id,
                        h2_header_t *headers, size_t count,
                        bool end_stream, void *user) {
    server_ctx_t *ctx = (server_ctx_t *)user;
    ctx->last_stream = stream_id;

    printf("  Request on stream %u:\n", stream_id);
    for (size_t i = 0; i < count; i++) {
        printf("    %.*s: %.*s\n",
               (int)headers[i].name_len,  headers[i].name,
               (int)headers[i].value_len, headers[i].value);
    }

    if (end_stream) {
        /*
         * Send response headers then body.
         * In a real implementation, HPACK-encode the headers properly.
         * Here we use a raw minimal HPACK response for illustration.
         */

        /*
         * Minimal HPACK for:
         *   :status: 200
         *   content-type: text/plain
         *   content-length: 15
         *
         * :status 200 = static table index 8 → 0x88
         * content-type: literal with indexing, name index 31
         * content-length: literal with indexing, name index 28
         */
        static const uint8_t resp_hpack[] = {
            0x88,                   /* :status 200 */
            0x5f, 0x00,             /* content-type: literal, name idx 31 (6-bit = 0x1f+0x00) */
            0x0a, 't', 'e', 'x', 't', '/', 'p', 'l', 'a', 'i', 'n',
            0x5c,                   /* content-length: name idx 28 */
            0x02, '1', '5',
        };

        uint8_t hdr_frame[9 + sizeof(resp_hpack)];
        h2_serialize_frame_header(hdr_frame,
                                   (uint32_t)sizeof(resp_hpack),
                                   H2_FRAME_HEADERS,
                                   H2_FLAG_END_HEADERS,
                                   stream_id);
        memcpy(hdr_frame + 9, resp_hpack, sizeof(resp_hpack));
        write_exact(conn->fd, hdr_frame, sizeof(hdr_frame));

        /* Send body */
        static const uint8_t body[] = "Hello, HTTP/2!\n";
        h2_send_data(conn->fd, stream_id, body, sizeof(body) - 1, true);
    }
}

static void on_goaway(h2_conn_t *conn, uint32_t last, h2_error_code_t err, void *user) {
    (void)conn; (void)user;
    printf("GOAWAY received: last_stream=%u error=0x%x\n", last, err);
}

int main(void) {
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family      = AF_INET,
        .sin_port        = htons(8080),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 10);
    printf("Listening on :8080 (h2c — no TLS)\n");

    while (1) {
        struct sockaddr_in caddr;
        socklen_t clen = sizeof(caddr);
        int fd = accept(srv, (struct sockaddr *)&caddr, &clen);
        if (fd < 0) continue;

        printf("Connection from %s\n", inet_ntoa(caddr.sin_addr));

        /* Verify client preface */
        uint8_t preface[H2_CLIENT_PREFACE_LEN];
        if (read_exact(fd, preface, H2_CLIENT_PREFACE_LEN) < 0 ||
            memcmp(preface, H2_CLIENT_PREFACE, H2_CLIENT_PREFACE_LEN) != 0) {
            printf("Bad preface\n");
            close(fd);
            continue;
        }
        printf("Client preface OK\n");

        h2_conn_t conn;
        h2_conn_init(&conn, fd);

        /* Send server initial SETTINGS */
        h2_setting_pair_t pairs[] = {
            {H2_SETTINGS_MAX_CONCURRENT_STREAMS, 100},
        };
        h2_send_settings(fd, pairs, 1, false);

        server_ctx_t ctx = {0};
        h2_callbacks_t cb = {
            .on_headers    = on_headers,
            .on_data       = NULL,
            .on_rst_stream = NULL,
            .on_goaway     = on_goaway,
            .user          = &ctx,
        };

        int r;
        while ((r = h2_process_frame(&conn, &cb)) == 0)
            ;

        close(fd);
        printf("Connection closed\n");
    }

    close(srv);
    return 0;
}
```

---

## 18. Rust Implementation

```rust
// http2.rs — Complete HTTP/2 implementation in Rust
// Demonstrates framing, HPACK, flow control, and connection state

use std::collections::HashMap;
use std::io::{self, Read, Write};

// ============================================================
// CONSTANTS
// ============================================================

pub const CLIENT_PREFACE: &[u8] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";
pub const FRAME_HEADER_SIZE: usize = 9;
pub const DEFAULT_WINDOW: i32 = 65535;
pub const MAX_WINDOW: i32 = 2_147_483_647;
pub const DEFAULT_MAX_FRAME_SIZE: u32 = 16384;

// ============================================================
// FRAME TYPES
// ============================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum FrameType {
    Data         = 0x0,
    Headers      = 0x1,
    Priority     = 0x2,
    RstStream    = 0x3,
    Settings     = 0x4,
    PushPromise  = 0x5,
    Ping         = 0x6,
    GoAway       = 0x7,
    WindowUpdate = 0x8,
    Continuation = 0x9,
    Unknown(u8),
}

impl From<u8> for FrameType {
    fn from(v: u8) -> Self {
        match v {
            0x0 => FrameType::Data,
            0x1 => FrameType::Headers,
            0x2 => FrameType::Priority,
            0x3 => FrameType::RstStream,
            0x4 => FrameType::Settings,
            0x5 => FrameType::PushPromise,
            0x6 => FrameType::Ping,
            0x7 => FrameType::GoAway,
            0x8 => FrameType::WindowUpdate,
            0x9 => FrameType::Continuation,
            x   => FrameType::Unknown(x),
        }
    }
}

// ============================================================
// FLAGS (as bitmask constants)
// ============================================================

pub mod flags {
    pub const END_STREAM:  u8 = 0x01;
    pub const END_HEADERS: u8 = 0x04;
    pub const PADDED:      u8 = 0x08;
    pub const PRIORITY:    u8 = 0x20;
    pub const ACK:         u8 = 0x01;
}

// ============================================================
// ERROR CODES
// ============================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum ErrorCode {
    NoError           = 0x0,
    ProtocolError     = 0x1,
    InternalError     = 0x2,
    FlowControlError  = 0x3,
    SettingsTimeout   = 0x4,
    StreamClosed      = 0x5,
    FrameSizeError    = 0x6,
    RefusedStream     = 0x7,
    Cancel            = 0x8,
    CompressionError  = 0x9,
    ConnectError      = 0xa,
    EnhanceYourCalm   = 0xb,
    InadequateSecurity = 0xc,
    Http11Required    = 0xd,
}

impl From<u32> for ErrorCode {
    fn from(v: u32) -> Self {
        match v {
            0x0 => ErrorCode::NoError,
            0x1 => ErrorCode::ProtocolError,
            0x2 => ErrorCode::InternalError,
            0x3 => ErrorCode::FlowControlError,
            0x4 => ErrorCode::SettingsTimeout,
            0x5 => ErrorCode::StreamClosed,
            0x6 => ErrorCode::FrameSizeError,
            0x7 => ErrorCode::RefusedStream,
            0x8 => ErrorCode::Cancel,
            0x9 => ErrorCode::CompressionError,
            0xa => ErrorCode::ConnectError,
            0xb => ErrorCode::EnhanceYourCalm,
            0xc => ErrorCode::InadequateSecurity,
            0xd => ErrorCode::Http11Required,
            _   => ErrorCode::ProtocolError,
        }
    }
}

// ============================================================
// H2 ERROR TYPE
// ============================================================

#[derive(Debug)]
pub enum H2Error {
    Io(io::Error),
    Protocol(ErrorCode, String),  // (error_code, description)
    ConnectionClosed,
}

impl From<io::Error> for H2Error {
    fn from(e: io::Error) -> Self {
        H2Error::Io(e)
    }
}

pub type H2Result<T> = Result<T, H2Error>;

// ============================================================
// FRAME HEADER
// ============================================================

/// Raw 9-byte HTTP/2 frame header.
#[derive(Debug, Clone)]
pub struct FrameHeader {
    /// Payload length (24-bit, max 16MB)
    pub length:    u32,
    pub frame_type: FrameType,
    pub flags:     u8,
    /// Stream ID (31-bit; 0 = connection-level)
    pub stream_id: u32,
}

impl FrameHeader {
    /// Parse 9 raw bytes into a FrameHeader.
    ///
    /// Wire format (all big-endian):
    ///   [0..3)  = 24-bit length
    ///   [3]     = type
    ///   [4]     = flags
    ///   [5..9)  = 1-bit reserved + 31-bit stream_id
    pub fn parse(buf: &[u8; 9]) -> Self {
        let length = ((buf[0] as u32) << 16)
                   | ((buf[1] as u32) << 8)
                   |   buf[2] as u32;

        let stream_id = (((buf[5] as u32) << 24)
                       | ((buf[6] as u32) << 16)
                       | ((buf[7] as u32) << 8)
                       |   buf[8] as u32)
                       & 0x7FFF_FFFF; // mask reserved bit

        FrameHeader {
            length,
            frame_type: FrameType::from(buf[3]),
            flags:      buf[4],
            stream_id,
        }
    }

    /// Serialize to 9-byte wire format.
    pub fn serialize(&self) -> [u8; 9] {
        let mut buf = [0u8; 9];
        buf[0] = ((self.length >> 16) & 0xFF) as u8;
        buf[1] = ((self.length >> 8)  & 0xFF) as u8;
        buf[2] =  (self.length        & 0xFF) as u8;
        buf[3] = self.frame_type as u8;
        buf[4] = self.flags;
        // stream_id: clear reserved bit
        let sid = self.stream_id & 0x7FFF_FFFF;
        buf[5] = ((sid >> 24) & 0x7F) as u8;
        buf[6] = ((sid >> 16) & 0xFF) as u8;
        buf[7] = ((sid >> 8)  & 0xFF) as u8;
        buf[8] =  (sid        & 0xFF) as u8;
        buf
    }

    pub fn has_flag(&self, flag: u8) -> bool {
        self.flags & flag != 0
    }
}

// ============================================================
// COMPLETE FRAME (header + payload)
// ============================================================

#[derive(Debug)]
pub struct Frame {
    pub header:  FrameHeader,
    pub payload: Vec<u8>,
}

impl Frame {
    pub fn read<R: Read>(reader: &mut R) -> H2Result<Frame> {
        let mut hdr_buf = [0u8; 9];
        reader.read_exact(&mut hdr_buf)
            .map_err(|_| H2Error::ConnectionClosed)?;

        let header = FrameHeader::parse(&hdr_buf);
        let mut payload = vec![0u8; header.length as usize];
        if !payload.is_empty() {
            reader.read_exact(&mut payload)
                .map_err(|_| H2Error::ConnectionClosed)?;
        }

        Ok(Frame { header, payload })
    }

    pub fn write<W: Write>(&self, writer: &mut W) -> H2Result<()> {
        let hdr = self.header.serialize();
        writer.write_all(&hdr)?;
        if !self.payload.is_empty() {
            writer.write_all(&self.payload)?;
        }
        Ok(())
    }
}

// ============================================================
// SETTINGS
// ============================================================

#[derive(Debug, Clone)]
pub struct Settings {
    pub header_table_size:      u32,
    pub enable_push:            bool,
    pub max_concurrent_streams: Option<u32>,
    pub initial_window_size:    u32,
    pub max_frame_size:         u32,
    pub max_header_list_size:   Option<u32>,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            header_table_size:      4096,
            enable_push:            true,
            max_concurrent_streams: None, // unlimited
            initial_window_size:    DEFAULT_WINDOW as u32,
            max_frame_size:         DEFAULT_MAX_FRAME_SIZE,
            max_header_list_size:   None, // unlimited
        }
    }
}

impl Settings {
    /// Parse SETTINGS frame payload (sequence of 6-byte id+value pairs).
    pub fn parse(payload: &[u8]) -> H2Result<Vec<(u16, u32)>> {
        if payload.len() % 6 != 0 {
            return Err(H2Error::Protocol(
                ErrorCode::FrameSizeError,
                "SETTINGS payload not multiple of 6".into(),
            ));
        }

        let mut pairs = Vec::new();
        for chunk in payload.chunks(6) {
            let id  = ((chunk[0] as u16) << 8) | chunk[1] as u16;
            let val = ((chunk[2] as u32) << 24)
                    | ((chunk[3] as u32) << 16)
                    | ((chunk[4] as u32) << 8)
                    |   chunk[5] as u32;
            pairs.push((id, val));
        }
        Ok(pairs)
    }

    /// Apply a list of (id, value) pairs to this Settings struct.
    pub fn apply(&mut self, pairs: &[(u16, u32)]) -> H2Result<()> {
        for &(id, val) in pairs {
            match id {
                0x1 => self.header_table_size = val,
                0x2 => {
                    if val > 1 {
                        return Err(H2Error::Protocol(
                            ErrorCode::ProtocolError,
                            "ENABLE_PUSH must be 0 or 1".into(),
                        ));
                    }
                    self.enable_push = val == 1;
                }
                0x3 => self.max_concurrent_streams = Some(val),
                0x4 => {
                    if val > MAX_WINDOW as u32 {
                        return Err(H2Error::Protocol(
                            ErrorCode::FlowControlError,
                            "INITIAL_WINDOW_SIZE too large".into(),
                        ));
                    }
                    self.initial_window_size = val;
                }
                0x5 => {
                    if val < DEFAULT_MAX_FRAME_SIZE || val > 16_777_215 {
                        return Err(H2Error::Protocol(
                            ErrorCode::ProtocolError,
                            "MAX_FRAME_SIZE out of range".into(),
                        ));
                    }
                    self.max_frame_size = val;
                }
                0x6 => self.max_header_list_size = Some(val),
                _   => { /* Unknown settings MUST be ignored */ }
            }
        }
        Ok(())
    }

    /// Serialize one setting pair to 6 bytes.
    pub fn encode_pair(id: u16, value: u32) -> [u8; 6] {
        [
            ((id >> 8) & 0xFF) as u8,
            (id & 0xFF) as u8,
            ((value >> 24) & 0xFF) as u8,
            ((value >> 16) & 0xFF) as u8,
            ((value >> 8)  & 0xFF) as u8,
            (value & 0xFF) as u8,
        ]
    }
}

// ============================================================
// HPACK STATIC TABLE
// ============================================================

/// Static table entry. Indices 1-61.
static HPACK_STATIC: &[(&str, &str)] = &[
    ("", ""),                              // [0] unused
    (":authority", ""),                    // [1]
    (":method", "GET"),                    // [2]
    (":method", "POST"),                   // [3]
    (":path", "/"),                        // [4]
    (":path", "/index.html"),              // [5]
    (":scheme", "http"),                   // [6]
    (":scheme", "https"),                  // [7]
    (":status", "200"),                    // [8]
    (":status", "204"),                    // [9]
    (":status", "206"),                    // [10]
    (":status", "304"),                    // [11]
    (":status", "400"),                    // [12]
    (":status", "404"),                    // [13]
    (":status", "500"),                    // [14]
    ("accept-charset", ""),               // [15]
    ("accept-encoding", "gzip, deflate"), // [16]
    ("accept-language", ""),              // [17]
    ("accept-ranges", ""),                // [18]
    ("accept", ""),                       // [19]
    ("access-control-allow-origin", ""),  // [20]
    ("age", ""),                          // [21]
    ("allow", ""),                        // [22]
    ("authorization", ""),               // [23]
    ("cache-control", ""),               // [24]
    ("content-disposition", ""),         // [25]
    ("content-encoding", ""),            // [26]
    ("content-language", ""),            // [27]
    ("content-length", ""),              // [28]
    ("content-location", ""),            // [29]
    ("content-range", ""),               // [30]
    ("content-type", ""),                // [31]
    ("cookie", ""),                      // [32]
    ("date", ""),                        // [33]
    ("etag", ""),                        // [34]
    ("expect", ""),                      // [35]
    ("expires", ""),                     // [36]
    ("from", ""),                        // [37]
    ("host", ""),                        // [38]
    ("if-match", ""),                    // [39]
    ("if-modified-since", ""),           // [40]
    ("if-none-match", ""),               // [41]
    ("if-range", ""),                    // [42]
    ("if-unmodified-since", ""),         // [43]
    ("last-modified", ""),               // [44]
    ("link", ""),                        // [45]
    ("location", ""),                    // [46]
    ("max-forwards", ""),                // [47]
    ("proxy-authenticate", ""),          // [48]
    ("proxy-authorization", ""),         // [49]
    ("range", ""),                       // [50]
    ("referer", ""),                     // [51]
    ("refresh", ""),                     // [52]
    ("retry-after", ""),                 // [53]
    ("server", ""),                      // [54]
    ("set-cookie", ""),                  // [55]
    ("strict-transport-security", ""),   // [56]
    ("te", ""),                          // [57]
    ("transfer-encoding", ""),           // [58]
    ("user-agent", ""),                  // [59]
    ("vary", ""),                        // [60]
    ("via", ""),                         // [61]
    ("www-authenticate", ""),            // [62] -- static has 61 entries [1..61]
];

// ============================================================
// HPACK INTEGER CODEC
// ============================================================

/// Decode an HPACK integer from `src` with `prefix_bits` prefix.
/// Returns (value, bytes_consumed) or error.
pub fn hpack_decode_int(src: &[u8], prefix_bits: u32) -> H2Result<(u64, usize)> {
    if src.is_empty() {
        return Err(H2Error::Protocol(
            ErrorCode::CompressionError,
            "empty integer".into(),
        ));
    }

    let mask = (1u64 << prefix_bits) - 1;
    let mut val = (src[0] as u64) & mask;
    let mut pos = 1usize;

    if val < mask {
        return Ok((val, pos));
    }

    // Multi-byte encoding
    let mut m = 0u32;
    loop {
        if pos >= src.len() {
            return Err(H2Error::Protocol(
                ErrorCode::CompressionError,
                "truncated integer".into(),
            ));
        }
        let b = src[pos] as u64;
        pos += 1;
        val += (b & 0x7F) << m;
        m += 7;
        if b & 0x80 == 0 {
            break;
        }
        if m > 32 {
            return Err(H2Error::Protocol(
                ErrorCode::CompressionError,
                "integer overflow".into(),
            ));
        }
    }

    Ok((val, pos))
}

/// Encode an integer with `prefix_bits` prefix.
/// The caller must pre-populate the top bits of dst[0] (type/flags bits).
/// Returns bytes written into dst.
pub fn hpack_encode_int(dst: &mut Vec<u8>, first_byte_top: u8,
                         value: u64, prefix_bits: u32) -> usize {
    let max_prefix = (1u64 << prefix_bits) - 1;
    if value < max_prefix {
        dst.push(first_byte_top | value as u8);
        1
    } else {
        dst.push(first_byte_top | max_prefix as u8);
        let mut rem = value - max_prefix;
        let mut written = 1;
        while rem >= 128 {
            dst.push((rem & 0x7F) as u8 | 0x80);
            rem >>= 7;
            written += 1;
        }
        dst.push(rem as u8);
        written + 1
    }
}

// ============================================================
// HPACK CONTEXT (encoder + decoder state)
// ============================================================

/// A header field name+value pair.
#[derive(Debug, Clone)]
pub struct HeaderField {
    pub name:          String,
    pub value:         String,
    pub never_indexed: bool,
}

impl HeaderField {
    /// Entry size per RFC 7541 §4.1: name_len + value_len + 32
    pub fn entry_size(&self) -> usize {
        self.name.len() + self.value.len() + 32
    }
}

/// HPACK dynamic table.
/// Entries stored newest-first (index 62 = index 0 in the vec).
#[derive(Debug, Default)]
pub struct DynamicTable {
    entries:     Vec<(String, String)>,
    current_size: usize,
    max_size:     usize,
}

impl DynamicTable {
    pub fn new(max_size: usize) -> Self {
        DynamicTable {
            entries: Vec::new(),
            current_size: 0,
            max_size,
        }
    }

    fn entry_size(name: &str, value: &str) -> usize {
        name.len() + value.len() + 32
    }

    /// Add a new entry (evicting oldest entries if needed).
    pub fn add(&mut self, name: String, value: String) {
        let size = Self::entry_size(&name, &value);
        // If entry itself exceeds max, evict everything
        if size > self.max_size {
            self.entries.clear();
            self.current_size = 0;
            return;
        }
        // Evict oldest (back of vec) until there's room
        while self.current_size + size > self.max_size {
            if let Some((n, v)) = self.entries.pop() {
                self.current_size -= Self::entry_size(&n, &v);
            } else {
                break;
            }
        }
        // Insert at front (newest = index 62)
        self.entries.insert(0, (name, value));
        self.current_size += size;
    }

    /// Resize the table, evicting entries as needed.
    pub fn resize(&mut self, new_max: usize) {
        self.max_size = new_max;
        while self.current_size > self.max_size {
            if let Some((n, v)) = self.entries.pop() {
                self.current_size -= Self::entry_size(&n, &v);
            } else {
                break;
            }
        }
    }

    /// Look up by dynamic table index (0 = newest = absolute index 62).
    pub fn get(&self, dyn_idx: usize) -> Option<(&str, &str)> {
        self.entries.get(dyn_idx)
            .map(|(n, v)| (n.as_str(), v.as_str()))
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }
}

/// Look up an absolute HPACK index (1..=61 = static, 62+ = dynamic).
fn hpack_table_lookup<'a>(
    dynamic: &'a DynamicTable,
    index: u64,
) -> H2Result<(&'a str, &'a str)> {
    if index == 0 {
        return Err(H2Error::Protocol(
            ErrorCode::CompressionError,
            "HPACK index 0 is invalid".into(),
        ));
    }
    if index <= 61 {
        let e = &HPACK_STATIC[index as usize];
        Ok((e.0, e.1))
    } else {
        let dyn_idx = (index - 62) as usize;
        dynamic.get(dyn_idx).ok_or_else(|| H2Error::Protocol(
            ErrorCode::CompressionError,
            format!("HPACK dynamic index {} out of range", index),
        ))
    }
}

// ============================================================
// HPACK DECODER
// ============================================================

pub struct HpackDecoder {
    dynamic: DynamicTable,
}

impl HpackDecoder {
    pub fn new(max_table_size: usize) -> Self {
        HpackDecoder {
            dynamic: DynamicTable::new(max_table_size),
        }
    }

    /// Decode a complete HPACK header block.
    pub fn decode(&mut self, src: &[u8]) -> H2Result<Vec<HeaderField>> {
        let mut fields = Vec::new();
        let mut pos = 0usize;

        while pos < src.len() {
            let first = src[pos];

            if first & 0x80 != 0 {
                // ─────────────────────────────────────────────
                // Indexed Header Field: 1xxxxxxx
                // ─────────────────────────────────────────────
                let (idx, consumed) = hpack_decode_int(&src[pos..], 7)?;
                pos += consumed;
                let (name, value) = hpack_table_lookup(&self.dynamic, idx)?;
                fields.push(HeaderField {
                    name:          name.to_owned(),
                    value:         value.to_owned(),
                    never_indexed: false,
                });

            } else if first & 0xC0 == 0x40 {
                // ─────────────────────────────────────────────
                // Literal with Incremental Indexing: 01xxxxxx
                // ─────────────────────────────────────────────
                let (name_idx, consumed) = hpack_decode_int(&src[pos..], 6)?;
                pos += consumed;

                let name = if name_idx == 0 {
                    let (s, n) = self.decode_string(&src[pos..])?;
                    pos += n;
                    s
                } else {
                    let (n, _) = hpack_table_lookup(&self.dynamic, name_idx)?;
                    n.to_owned()
                };

                let (value, n) = self.decode_string(&src[pos..])?;
                pos += n;

                // Add to dynamic table
                self.dynamic.add(name.clone(), value.clone());

                fields.push(HeaderField {
                    name,
                    value,
                    never_indexed: false,
                });

            } else if first & 0xF0 == 0x00 || first & 0xF0 == 0x10 {
                // ─────────────────────────────────────────────
                // Literal without Indexing:  0000xxxx
                // Literal Never Indexed:     0001xxxx
                // ─────────────────────────────────────────────
                let never_indexed = first & 0xF0 == 0x10;
                let (name_idx, consumed) = hpack_decode_int(&src[pos..], 4)?;
                pos += consumed;

                let name = if name_idx == 0 {
                    let (s, n) = self.decode_string(&src[pos..])?;
                    pos += n;
                    s
                } else {
                    let (n, _) = hpack_table_lookup(&self.dynamic, name_idx)?;
                    n.to_owned()
                };

                let (value, n) = self.decode_string(&src[pos..])?;
                pos += n;

                fields.push(HeaderField {
                    name,
                    value,
                    never_indexed,
                });

            } else if first & 0xE0 == 0x20 {
                // ─────────────────────────────────────────────
                // Dynamic Table Size Update: 001xxxxx
                // ─────────────────────────────────────────────
                let (new_size, consumed) = hpack_decode_int(&src[pos..], 5)?;
                pos += consumed;
                self.dynamic.resize(new_size as usize);
            } else {
                return Err(H2Error::Protocol(
                    ErrorCode::CompressionError,
                    format!("unknown HPACK prefix: 0x{:02x}", first),
                ));
            }
        }

        Ok(fields)
    }

    /// Decode an HPACK string (optionally Huffman encoded).
    /// Returns (decoded_string, bytes_consumed).
    fn decode_string(&self, src: &[u8]) -> H2Result<(String, usize)> {
        if src.is_empty() {
            return Err(H2Error::Protocol(
                ErrorCode::CompressionError,
                "empty string".into(),
            ));
        }
        let huffman = src[0] & 0x80 != 0;
        let (len, consumed) = hpack_decode_int(src, 7)?;
        let total = consumed + len as usize;
        if total > src.len() {
            return Err(H2Error::Protocol(
                ErrorCode::CompressionError,
                "string length exceeds buffer".into(),
            ));
        }
        let bytes = &src[consumed..total];
        let s = if huffman {
            // Huffman decode (simplified: just raw for now)
            // In production, use a proper Huffman decoder per RFC 7541 Appendix B
            String::from_utf8_lossy(bytes).into_owned()
        } else {
            String::from_utf8_lossy(bytes).into_owned()
        };
        Ok((s, total))
    }
}

// ============================================================
// HPACK ENCODER
// ============================================================

pub struct HpackEncoder {
    dynamic: DynamicTable,
}

impl HpackEncoder {
    pub fn new(max_table_size: usize) -> Self {
        HpackEncoder {
            dynamic: DynamicTable::new(max_table_size),
        }
    }

    /// Encode a list of header fields into HPACK bytes.
    pub fn encode(&mut self, fields: &[HeaderField]) -> Vec<u8> {
        let mut out = Vec::new();

        for field in fields {
            // Try indexed representation first
            if let Some(idx) = self.find_static_full(&field.name, &field.value) {
                // Full match in static table → single indexed byte
                hpack_encode_int(&mut out, 0x80, idx as u64, 7);
                continue;
            }

            if field.never_indexed {
                // Never indexed literal (0x10 prefix, 4-bit index)
                if let Some(name_idx) = self.find_name_only(&field.name) {
                    hpack_encode_int(&mut out, 0x10, name_idx as u64, 4);
                } else {
                    hpack_encode_int(&mut out, 0x10, 0, 4);
                    self.encode_string(&mut out, &field.name);
                }
                self.encode_string(&mut out, &field.value);
            } else {
                // Literal with incremental indexing (0x40 prefix, 6-bit index)
                if let Some(name_idx) = self.find_name_only(&field.name) {
                    hpack_encode_int(&mut out, 0x40, name_idx as u64, 6);
                } else {
                    hpack_encode_int(&mut out, 0x40, 0, 6);
                    self.encode_string(&mut out, &field.name);
                }
                self.encode_string(&mut out, &field.value);
                // Add to dynamic table
                self.dynamic.add(field.name.clone(), field.value.clone());
            }
        }

        out
    }

    fn encode_string(&self, out: &mut Vec<u8>, s: &str) {
        // Raw (no Huffman) for simplicity
        hpack_encode_int(out, 0x00, s.len() as u64, 7);
        out.extend_from_slice(s.as_bytes());
    }

    fn find_static_full(&self, name: &str, value: &str) -> Option<usize> {
        for (i, &(n, v)) in HPACK_STATIC.iter().enumerate().skip(1) {
            if n == name && v == value {
                return Some(i);
            }
        }
        None
    }

    fn find_name_only(&self, name: &str) -> Option<usize> {
        for (i, &(n, _)) in HPACK_STATIC.iter().enumerate().skip(1) {
            if n == name {
                return Some(i);
            }
        }
        None
    }
}

// ============================================================
// STREAM STATE MACHINE
// ============================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StreamState {
    Idle,
    Open,
    HalfClosedLocal,
    HalfClosedRemote,
    Closed,
    ReservedLocal,
    ReservedRemote,
}

#[derive(Debug)]
pub struct Stream {
    pub id:          u32,
    pub state:       StreamState,
    pub send_window: i32,
    pub recv_window: i32,
    pub weight:      u8,
    pub dependency:  u32,
}

impl Stream {
    pub fn new(id: u32, initial_window: i32) -> Self {
        Stream {
            id,
            state:       StreamState::Idle,
            send_window: initial_window,
            recv_window: DEFAULT_WINDOW,
            weight:      16, // default weight
            dependency:  0,
        }
    }

    /// Transition stream state on sending a frame.
    pub fn on_send_headers(&mut self, end_stream: bool) -> H2Result<()> {
        match self.state {
            StreamState::Idle => {
                self.state = if end_stream {
                    StreamState::HalfClosedLocal
                } else {
                    StreamState::Open
                };
                Ok(())
            }
            StreamState::ReservedLocal => {
                self.state = if end_stream {
                    StreamState::Closed
                } else {
                    StreamState::HalfClosedRemote
                };
                Ok(())
            }
            _ => Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                format!("cannot send HEADERS in state {:?}", self.state),
            )),
        }
    }

    pub fn on_recv_headers(&mut self, end_stream: bool) -> H2Result<()> {
        match self.state {
            StreamState::Idle => {
                self.state = if end_stream {
                    StreamState::HalfClosedRemote
                } else {
                    StreamState::Open
                };
                Ok(())
            }
            StreamState::Open => {
                if end_stream {
                    self.state = StreamState::HalfClosedRemote;
                }
                Ok(())
            }
            StreamState::HalfClosedLocal => {
                if end_stream {
                    self.state = StreamState::Closed;
                }
                Ok(())
            }
            _ => Err(H2Error::Protocol(
                ErrorCode::StreamClosed,
                format!("cannot recv HEADERS in state {:?}", self.state),
            )),
        }
    }

    pub fn on_send_data(&mut self, end_stream: bool, len: u32) -> H2Result<()> {
        match self.state {
            StreamState::Open | StreamState::HalfClosedRemote => {
                if self.send_window < len as i32 {
                    return Err(H2Error::Protocol(
                        ErrorCode::FlowControlError,
                        "send window exhausted".into(),
                    ));
                }
                self.send_window -= len as i32;
                if end_stream {
                    self.state = if self.state == StreamState::Open {
                        StreamState::HalfClosedLocal
                    } else {
                        StreamState::Closed
                    };
                }
                Ok(())
            }
            _ => Err(H2Error::Protocol(
                ErrorCode::StreamClosed,
                "cannot send DATA in this state".into(),
            )),
        }
    }
}

// ============================================================
// CONNECTION
// ============================================================

pub struct Connection<RW: Read + Write> {
    stream:          RW,
    local_settings:  Settings,
    remote_settings: Settings,
    send_window:     i32,  // connection-level send window
    recv_window:     i32,  // connection-level recv window
    encoder:         HpackEncoder,
    decoder:         HpackDecoder,
    streams:         HashMap<u32, Stream>,
    next_stream_id:  u32,  // next client-side stream ID (odd)
    last_stream_id:  u32,  // highest stream ID from remote
    goaway_sent:     bool,
    goaway_received: bool,
}

impl<RW: Read + Write> Connection<RW> {
    pub fn new_client(stream: RW) -> Self {
        let local  = Settings::default();
        let remote = Settings::default();
        let initial_window = local.initial_window_size as i32;

        Connection {
            stream,
            local_settings:  local.clone(),
            remote_settings: remote,
            send_window:     DEFAULT_WINDOW,
            recv_window:     DEFAULT_WINDOW,
            encoder:         HpackEncoder::new(local.header_table_size as usize),
            decoder:         HpackDecoder::new(4096),
            streams:         HashMap::new(),
            next_stream_id:  1,
            last_stream_id:  0,
            goaway_sent:     false,
            goaway_received: false,
        }
    }

    // ── Frame I/O ───────────────────────────────────────────

    pub fn read_frame(&mut self) -> H2Result<Frame> {
        Frame::read(&mut self.stream)
    }

    pub fn write_frame(&mut self, frame: &Frame) -> H2Result<()> {
        frame.write(&mut self.stream)?;
        self.stream.flush().map_err(H2Error::Io)
    }

    // ── High-level frame senders ────────────────────────────

    /// Send client connection preface (magic + SETTINGS).
    pub fn send_client_preface(&mut self) -> H2Result<()> {
        self.stream.write_all(CLIENT_PREFACE)?;

        // Build SETTINGS payload
        let mut payload = Vec::new();
        payload.extend_from_slice(&Settings::encode_pair(0x3, 100));  // MAX_CONCURRENT_STREAMS
        payload.extend_from_slice(&Settings::encode_pair(0x4, DEFAULT_WINDOW as u32));
        payload.extend_from_slice(&Settings::encode_pair(0x5, DEFAULT_MAX_FRAME_SIZE));

        let hdr = FrameHeader {
            length:    payload.len() as u32,
            frame_type: FrameType::Settings,
            flags:     0,
            stream_id: 0,
        };
        self.write_frame(&Frame { header: hdr, payload })?;
        Ok(())
    }

    /// Send SETTINGS ACK.
    pub fn send_settings_ack(&mut self) -> H2Result<()> {
        let hdr = FrameHeader {
            length:    0,
            frame_type: FrameType::Settings,
            flags:     flags::ACK,
            stream_id: 0,
        };
        self.write_frame(&Frame { header: hdr, payload: vec![] })
    }

    /// Send PING and return the sequence of bytes sent (for matching ACK).
    pub fn send_ping(&mut self, data: [u8; 8]) -> H2Result<()> {
        let hdr = FrameHeader {
            length:    8,
            frame_type: FrameType::Ping,
            flags:     0,
            stream_id: 0,
        };
        self.write_frame(&Frame { header: hdr, payload: data.to_vec() })
    }

    /// Send PING ACK with same 8 bytes.
    pub fn send_ping_ack(&mut self, data: &[u8]) -> H2Result<()> {
        let hdr = FrameHeader {
            length:    8,
            frame_type: FrameType::Ping,
            flags:     flags::ACK,
            stream_id: 0,
        };
        self.write_frame(&Frame { header: hdr, payload: data.to_vec() })
    }

    /// Send WINDOW_UPDATE.
    pub fn send_window_update(&mut self, stream_id: u32, increment: u32) -> H2Result<()> {
        if increment == 0 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "WINDOW_UPDATE increment must be > 0".into(),
            ));
        }
        let mut payload = [0u8; 4];
        payload[0] = ((increment >> 24) & 0x7F) as u8;
        payload[1] = ((increment >> 16) & 0xFF) as u8;
        payload[2] = ((increment >> 8)  & 0xFF) as u8;
        payload[3] =  (increment        & 0xFF) as u8;

        let hdr = FrameHeader {
            length:    4,
            frame_type: FrameType::WindowUpdate,
            flags:     0,
            stream_id,
        };
        self.write_frame(&Frame { header: hdr, payload: payload.to_vec() })
    }

    /// Send RST_STREAM.
    pub fn send_rst_stream(&mut self, stream_id: u32, error: ErrorCode) -> H2Result<()> {
        let code = error as u32;
        let payload = vec![
            ((code >> 24) & 0xFF) as u8,
            ((code >> 16) & 0xFF) as u8,
            ((code >> 8)  & 0xFF) as u8,
            ( code        & 0xFF) as u8,
        ];
        let hdr = FrameHeader {
            length:    4,
            frame_type: FrameType::RstStream,
            flags:     0,
            stream_id,
        };
        self.write_frame(&Frame { header: hdr, payload })
    }

    /// Send GOAWAY.
    pub fn send_goaway(&mut self,
                        last_stream_id: u32,
                        error: ErrorCode,
                        debug: &str) -> H2Result<()> {
        let code = error as u32;
        let mut payload = vec![
            ((last_stream_id >> 24) & 0x7F) as u8,
            ((last_stream_id >> 16) & 0xFF) as u8,
            ((last_stream_id >> 8)  & 0xFF) as u8,
            ( last_stream_id        & 0xFF) as u8,
            ((code >> 24) & 0xFF) as u8,
            ((code >> 16) & 0xFF) as u8,
            ((code >> 8)  & 0xFF) as u8,
            ( code        & 0xFF) as u8,
        ];
        payload.extend_from_slice(debug.as_bytes());

        let hdr = FrameHeader {
            length:    payload.len() as u32,
            frame_type: FrameType::GoAway,
            flags:     0,
            stream_id: 0,
        };
        self.goaway_sent = true;
        self.write_frame(&Frame { header: hdr, payload })
    }

    /// Open a new request stream. Returns the new stream ID.
    /// Sends HEADERS frame with given header fields.
    pub fn send_request(
        &mut self,
        headers: &[HeaderField],
        end_stream: bool,
    ) -> H2Result<u32> {
        let stream_id = self.next_stream_id;
        self.next_stream_id += 2; // client uses odd IDs

        // HPACK encode headers
        let hpack = self.encoder.encode(headers);

        let flags = flags::END_HEADERS | if end_stream { flags::END_STREAM } else { 0 };

        let hdr = FrameHeader {
            length:    hpack.len() as u32,
            frame_type: FrameType::Headers,
            flags,
            stream_id,
        };
        self.write_frame(&Frame { header: hdr, payload: hpack })?;

        // Create stream entry
        let initial_window = self.remote_settings.initial_window_size as i32;
        let mut s = Stream::new(stream_id, initial_window);
        s.on_send_headers(end_stream)?;
        self.streams.insert(stream_id, s);

        Ok(stream_id)
    }

    /// Send DATA frame on an existing stream.
    pub fn send_data(
        &mut self,
        stream_id: u32,
        data: &[u8],
        end_stream: bool,
    ) -> H2Result<()> {
        // Check connection-level window
        if self.send_window < data.len() as i32 {
            return Err(H2Error::Protocol(
                ErrorCode::FlowControlError,
                "connection send window exhausted".into(),
            ));
        }

        // Update stream state
        {
            let s = self.streams.get_mut(&stream_id).ok_or_else(|| {
                H2Error::Protocol(ErrorCode::ProtocolError, "unknown stream".into())
            })?;
            s.on_send_data(end_stream, data.len() as u32)?;
        }

        self.send_window -= data.len() as i32;

        let flags = if end_stream { flags::END_STREAM } else { 0 };
        let hdr = FrameHeader {
            length:    data.len() as u32,
            frame_type: FrameType::Data,
            flags,
            stream_id,
        };
        self.write_frame(&Frame { header: hdr, payload: data.to_vec() })
    }

    // ── Frame dispatcher ─────────────────────────────────────

    /// Read and dispatch one frame. Returns the decoded event.
    pub fn recv_event(&mut self) -> H2Result<Event> {
        let frame = self.read_frame()?;
        self.dispatch(frame)
    }

    fn dispatch(&mut self, frame: Frame) -> H2Result<Event> {
        let hdr = &frame.header;

        // Frame size check
        if hdr.length > self.local_settings.max_frame_size {
            return Err(H2Error::Protocol(
                ErrorCode::FrameSizeError,
                "frame exceeds MAX_FRAME_SIZE".into(),
            ));
        }

        match hdr.frame_type {
            FrameType::Settings => self.handle_settings(&frame),
            FrameType::Ping     => self.handle_ping(&frame),
            FrameType::GoAway   => self.handle_goaway(&frame),
            FrameType::WindowUpdate => self.handle_window_update(&frame),
            FrameType::RstStream    => self.handle_rst_stream(&frame),
            FrameType::Headers      => self.handle_headers(&frame),
            FrameType::Data         => self.handle_data(&frame),
            FrameType::Continuation => {
                // Simplified: treat as headers continuation
                Ok(Event::Unknown)
            }
            FrameType::PushPromise => Ok(Event::PushPromise {
                stream_id:         frame.header.stream_id,
                promised_stream_id: 0, // parse from payload in full impl
            }),
            FrameType::Priority => Ok(Event::Unknown), // deprecated
            FrameType::Unknown(_) => Ok(Event::Unknown), // MUST ignore
        }
    }

    fn handle_settings(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.header.stream_id != 0 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "SETTINGS on non-zero stream".into(),
            ));
        }
        if frame.header.has_flag(flags::ACK) {
            if frame.header.length != 0 {
                return Err(H2Error::Protocol(
                    ErrorCode::FrameSizeError,
                    "SETTINGS ACK with payload".into(),
                ));
            }
            return Ok(Event::SettingsAck);
        }

        let pairs = Settings::parse(&frame.payload)?;
        self.remote_settings.apply(&pairs)?;
        // Must ACK
        self.send_settings_ack()?;
        Ok(Event::Settings)
    }

    fn handle_ping(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.header.stream_id != 0 || frame.header.length != 8 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "malformed PING".into(),
            ));
        }
        if !frame.header.has_flag(flags::ACK) {
            self.send_ping_ack(&frame.payload)?;
        }
        Ok(Event::Ping { ack: frame.header.has_flag(flags::ACK) })
    }

    fn handle_goaway(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.payload.len() < 8 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "GOAWAY too short".into(),
            ));
        }
        let last = (((frame.payload[0] as u32) << 24)
                  | ((frame.payload[1] as u32) << 16)
                  | ((frame.payload[2] as u32) << 8)
                  |   frame.payload[3] as u32)
                  & 0x7FFF_FFFF;
        let code = ((frame.payload[4] as u32) << 24)
                 | ((frame.payload[5] as u32) << 16)
                 | ((frame.payload[6] as u32) << 8)
                 |   frame.payload[7] as u32;
        self.goaway_received = true;
        Ok(Event::GoAway {
            last_stream_id: last,
            error: ErrorCode::from(code),
        })
    }

    fn handle_window_update(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.payload.len() < 4 {
            return Err(H2Error::Protocol(
                ErrorCode::FrameSizeError,
                "WINDOW_UPDATE too short".into(),
            ));
        }
        let inc = (((frame.payload[0] as u32) << 24)
                 | ((frame.payload[1] as u32) << 16)
                 | ((frame.payload[2] as u32) << 8)
                 |   frame.payload[3] as u32)
                 & 0x7FFF_FFFF;

        if inc == 0 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "WINDOW_UPDATE increment 0".into(),
            ));
        }

        if frame.header.stream_id == 0 {
            self.send_window = self.send_window.checked_add(inc as i32)
                .ok_or_else(|| H2Error::Protocol(
                    ErrorCode::FlowControlError,
                    "connection window overflow".into(),
                ))?;
            if self.send_window > MAX_WINDOW {
                return Err(H2Error::Protocol(
                    ErrorCode::FlowControlError,
                    "connection window exceeds max".into(),
                ));
            }
        } else {
            if let Some(s) = self.streams.get_mut(&frame.header.stream_id) {
                s.send_window = s.send_window.checked_add(inc as i32)
                    .filter(|&w| w <= MAX_WINDOW)
                    .ok_or_else(|| H2Error::Protocol(
                        ErrorCode::FlowControlError,
                        "stream window overflow".into(),
                    ))?;
            }
        }

        Ok(Event::WindowUpdate {
            stream_id: frame.header.stream_id,
            increment: inc,
        })
    }

    fn handle_rst_stream(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.header.stream_id == 0 || frame.payload.len() < 4 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "malformed RST_STREAM".into(),
            ));
        }
        let code = ((frame.payload[0] as u32) << 24)
                 | ((frame.payload[1] as u32) << 16)
                 | ((frame.payload[2] as u32) << 8)
                 |   frame.payload[3] as u32;

        if let Some(s) = self.streams.get_mut(&frame.header.stream_id) {
            s.state = StreamState::Closed;
        }

        Ok(Event::RstStream {
            stream_id: frame.header.stream_id,
            error: ErrorCode::from(code),
        })
    }

    fn handle_headers(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.header.stream_id == 0 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "HEADERS on stream 0".into(),
            ));
        }

        // Track highest stream ID
        if frame.header.stream_id > self.last_stream_id {
            self.last_stream_id = frame.header.stream_id;
        }

        // Parse out padding and priority if present
        let mut payload = frame.payload.as_slice();
        let mut pad_len = 0usize;
        if frame.header.has_flag(flags::PADDED) {
            if payload.is_empty() {
                return Err(H2Error::Protocol(
                    ErrorCode::FrameSizeError,
                    "PADDED flag but no payload".into(),
                ));
            }
            pad_len = payload[0] as usize;
            payload = &payload[1..];
        }
        if frame.header.has_flag(flags::PRIORITY) {
            if payload.len() < 5 {
                return Err(H2Error::Protocol(
                    ErrorCode::FrameSizeError,
                    "PRIORITY flag but insufficient payload".into(),
                ));
            }
            payload = &payload[5..]; // skip E(1) + dep(31) + weight(8)
        }
        if pad_len >= payload.len() {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "padding exceeds payload".into(),
            ));
        }
        payload = &payload[..payload.len() - pad_len];

        let headers = self.decoder.decode(payload)?;

        let end_stream  = frame.header.has_flag(flags::END_STREAM);
        let end_headers = frame.header.has_flag(flags::END_HEADERS);

        // Update stream state
        let sid = frame.header.stream_id;
        let stream = self.streams.entry(sid)
            .or_insert_with(|| Stream::new(sid, DEFAULT_WINDOW));
        stream.on_recv_headers(end_stream)?;

        Ok(Event::Headers {
            stream_id:   sid,
            headers,
            end_stream,
            end_headers,
        })
    }

    fn handle_data(&mut self, frame: &Frame) -> H2Result<Event> {
        if frame.header.stream_id == 0 {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "DATA on stream 0".into(),
            ));
        }

        let mut payload = frame.payload.as_slice();
        let mut pad_len = 0usize;
        if frame.header.has_flag(flags::PADDED) {
            if payload.is_empty() {
                return Err(H2Error::Protocol(
                    ErrorCode::FrameSizeError,
                    "PADDED but no payload".into(),
                ));
            }
            pad_len  = payload[0] as usize;
            payload = &payload[1..];
        }
        if pad_len >= payload.len() {
            return Err(H2Error::Protocol(
                ErrorCode::ProtocolError,
                "padding exceeds payload".into(),
            ));
        }
        let data = payload[..payload.len() - pad_len].to_vec();
        let data_len = data.len() as i32;

        // Flow control accounting
        self.recv_window -= data_len;
        if self.recv_window < DEFAULT_WINDOW / 2 {
            let inc = (DEFAULT_WINDOW - self.recv_window) as u32;
            self.send_window_update(0, inc)?;
            self.recv_window = DEFAULT_WINDOW;
        }

        let end_stream = frame.header.has_flag(flags::END_STREAM);
        let sid = frame.header.stream_id;

        if let Some(s) = self.streams.get_mut(&sid) {
            match s.state {
                StreamState::Open => {
                    if end_stream { s.state = StreamState::HalfClosedRemote; }
                }
                StreamState::HalfClosedLocal => {
                    if end_stream { s.state = StreamState::Closed; }
                }
                _ => {
                    return Err(H2Error::Protocol(
                        ErrorCode::StreamClosed,
                        "DATA on non-open stream".into(),
                    ));
                }
            }
        }

        Ok(Event::Data {
            stream_id: sid,
            data,
            end_stream,
        })
    }
}

// ============================================================
// EVENTS (returned from recv_event)
// ============================================================

#[derive(Debug)]
pub enum Event {
    Settings,
    SettingsAck,
    Ping { ack: bool },
    GoAway { last_stream_id: u32, error: ErrorCode },
    WindowUpdate { stream_id: u32, increment: u32 },
    RstStream { stream_id: u32, error: ErrorCode },
    Headers {
        stream_id:   u32,
        headers:     Vec<HeaderField>,
        end_stream:  bool,
        end_headers: bool,
    },
    Data {
        stream_id:  u32,
        data:       Vec<u8>,
        end_stream: bool,
    },
    PushPromise {
        stream_id:          u32,
        promised_stream_id: u32,
    },
    Unknown,
}

// ============================================================
// EXAMPLE: CLIENT USAGE
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn test_frame_header_roundtrip() {
        let hdr = FrameHeader {
            length:    42,
            frame_type: FrameType::Data,
            flags:     flags::END_STREAM,
            stream_id: 7,
        };
        let bytes = hdr.serialize();
        let parsed = FrameHeader::parse(&bytes);
        assert_eq!(parsed.length,    42);
        assert_eq!(parsed.stream_id, 7);
        assert_eq!(parsed.flags,     flags::END_STREAM);
        assert!(matches!(parsed.frame_type, FrameType::Data));
    }

    #[test]
    fn test_hpack_int_roundtrip() {
        // Encode 1337 with prefix 5
        let mut buf = vec![0b110_00000u8]; // top 3 bits = flags, bottom 5 = prefix
        hpack_encode_int(&mut buf, 0b110_00000, 1337, 5);
        let (val, _) = hpack_decode_int(&buf, 5).unwrap();
        assert_eq!(val, 1337);
    }

    #[test]
    fn test_settings_parse() {
        // Encode MAX_CONCURRENT_STREAMS=100
        let payload = Settings::encode_pair(0x3, 100);
        let pairs = Settings::parse(&payload).unwrap();
        assert_eq!(pairs.len(), 1);
        assert_eq!(pairs[0], (0x3, 100));
    }

    #[test]
    fn test_hpack_encode_decode() {
        let mut encoder = HpackEncoder::new(4096);
        let mut decoder = HpackDecoder::new(4096);

        let fields = vec![
            HeaderField { name: ":method".into(),    value: "GET".into(),         never_indexed: false },
            HeaderField { name: ":scheme".into(),    value: "https".into(),       never_indexed: false },
            HeaderField { name: ":path".into(),      value: "/".into(),           never_indexed: false },
            HeaderField { name: ":authority".into(), value: "example.com".into(), never_indexed: false },
        ];

        let encoded = encoder.encode(&fields);
        let decoded = decoder.decode(&encoded).unwrap();

        assert_eq!(decoded.len(), fields.len());
        for (d, f) in decoded.iter().zip(fields.iter()) {
            assert_eq!(d.name,  f.name);
            assert_eq!(d.value, f.value);
        }
    }

    #[test]
    fn test_window_update_parse() {
        // Test WINDOW_UPDATE frame round-trip
        let mut buf = Vec::new();
        // Encode increment = 65535
        let inc: u32 = 65535;
        buf.push(((inc >> 24) & 0x7F) as u8);
        buf.push(((inc >> 16) & 0xFF) as u8);
        buf.push(((inc >> 8)  & 0xFF) as u8);
        buf.push( (inc        & 0xFF) as u8);

        let parsed = (((buf[0] as u32) << 24)
                    | ((buf[1] as u32) << 16)
                    | ((buf[2] as u32) << 8)
                    |   buf[3] as u32)
                    & 0x7FFF_FFFF;
        assert_eq!(parsed, 65535);
    }

    #[test]
    fn test_goaway_serialize() {
        // Test GOAWAY frame serialization
        let last_stream_id: u32 = 5;
        let error = ErrorCode::NoError as u32;
        let payload = vec![
            ((last_stream_id >> 24) & 0x7F) as u8,
            ((last_stream_id >> 16) & 0xFF) as u8,
            ((last_stream_id >> 8)  & 0xFF) as u8,
            ( last_stream_id        & 0xFF) as u8,
            ((error >> 24) & 0xFF) as u8,
            ((error >> 16) & 0xFF) as u8,
            ((error >> 8)  & 0xFF) as u8,
            ( error        & 0xFF) as u8,
        ];
        let parsed_last = (((payload[0] as u32) << 24)
                         | ((payload[1] as u32) << 16)
                         | ((payload[2] as u32) << 8)
                         |   payload[3] as u32)
                         & 0x7FFF_FFFF;
        assert_eq!(parsed_last, 5);
    }
}
```

---

## 19. Debugging HTTP/2 on the Wire

### Using OpenSSL to Capture h2 Traffic

```bash
# Capture with Wireshark (filter: http2)
# Wireshark can decrypt h2 if you provide the TLS session key log

# Export TLS keys for Wireshark decryption
export SSLKEYLOGFILE=/tmp/tls_keys.log
curl --http2 https://example.com

# In Wireshark: Edit > Preferences > Protocols > TLS > (Pre)-Master-Secret log
```

### Using curl to Inspect Frames

```bash
# Force HTTP/2, verbose frame-level output
curl --http2 -v https://example.com

# With nghttp2 for detailed frame dump
nghttp -v https://example.com

# h2load for load testing
h2load -n 1000 -c 10 https://example.com
```

### nghttp2 Frame Dump Output

```
[  0.001] Connected
[  0.001] send SETTINGS frame <length=12, flags=0x00, stream_id=0>
          (niv=2)
          [SETTINGS_MAX_CONCURRENT_STREAMS(0x03):100]
          [SETTINGS_INITIAL_WINDOW_SIZE(0x04):65535]
[  0.002] recv SETTINGS frame <length=18, flags=0x00, stream_id=0>
          (niv=3)
          [SETTINGS_MAX_CONCURRENT_STREAMS(0x03):128]
          [SETTINGS_INITIAL_WINDOW_SIZE(0x04):65535]
          [SETTINGS_MAX_FRAME_SIZE(0x05):16384]
[  0.002] send SETTINGS frame <length=0, flags=0x01, stream_id=0>
          ; ACK
[  0.002] recv SETTINGS frame <length=0, flags=0x01, stream_id=0>
          ; ACK
[  0.002] send HEADERS frame <length=41, flags=0x25, stream_id=1>
          ; END_STREAM | END_HEADERS | PRIORITY
          (padlen=0, dep_stream_id=0, weight=16, exclusive=0)
          ; Open new stream
          :method: GET
          :path: /
          :scheme: https
          :authority: example.com
          accept: */*
[  0.105] recv HEADERS frame <length=119, flags=0x04, stream_id=1>
          ; END_HEADERS
          :status: 200
          content-type: text/html; charset=UTF-8
          ...
```

### Decoding a Raw Frame in Python (for learning)

```python
import struct

def parse_frame_header(data: bytes) -> dict:
    """Parse 9-byte HTTP/2 frame header"""
    assert len(data) == 9
    length = (data[0] << 16) | (data[1] << 8) | data[2]
    ftype  = data[3]
    flags  = data[4]
    stream_id = struct.unpack('>I', data[5:9])[0] & 0x7FFFFFFF

    type_names = {
        0: 'DATA', 1: 'HEADERS', 2: 'PRIORITY', 3: 'RST_STREAM',
        4: 'SETTINGS', 5: 'PUSH_PROMISE', 6: 'PING', 7: 'GOAWAY',
        8: 'WINDOW_UPDATE', 9: 'CONTINUATION'
    }
    return {
        'length': length,
        'type':   type_names.get(ftype, f'UNKNOWN(0x{ftype:02x})'),
        'flags':  f'0x{flags:02x}',
        'stream': stream_id,
    }

# Example: SETTINGS ACK frame
ack = bytes.fromhex('000000040100000000')
print(parse_frame_header(ack))
# {'length': 0, 'type': 'SETTINGS', 'flags': '0x01', 'stream': 0}
```

---

## 20. Common Pitfalls and Gotchas

### Pitfall 1: HPACK State Must Be Synchronized

HPACK state is connection-level, not per-request. If you reset the dynamic table on the encoder but not the decoder (or vice versa), EVERY subsequent header decode will fail with COMPRESSION_ERROR — which terminates the ENTIRE connection.

```
Wrong:  Reset HPACK after each request
Right:  HPACK state persists for the entire connection lifetime
```

### Pitfall 2: Stream ID Exhaustion

Client stream IDs go 1, 3, 5, ... up to 2^31-1. After that, the client MUST create a new connection. A well-written client tracks this and proactively migrates connections before exhaustion.

### Pitfall 3: Processing Frames After GOAWAY

After receiving GOAWAY, you must NOT send new requests. But you can (and should) continue receiving responses for streams with IDs ≤ last-stream-id from the GOAWAY. A common bug is closing the connection immediately upon GOAWAY, dropping in-flight responses.

### Pitfall 4: Flow Control Deadlock

If both sides are waiting for WINDOW_UPDATE before sending data, and neither sends one, the connection is deadlocked. This happens when:
- Server is waiting for client to send more request body (POST)
- Client is waiting for server WINDOW_UPDATE
- Neither sends because both recv_windows are at 0

Fix: Never wait for WINDOW_UPDATE before sending your own WINDOW_UPDATE. Send WINDOW_UPDATE eagerly as you consume data.

### Pitfall 5: The CONTINUATION Rule

If you send HEADERS without END_HEADERS, the next frame MUST be CONTINUATION on the same stream. If you send anything else (even a PING on stream 0), it's a PROTOCOL_ERROR. This is enforced strictly.

### Pitfall 6: RST_STREAM vs GOAWAY Choice

```
Use RST_STREAM when:
  - One stream has a problem (bad request, timeout, etc.)
  - The connection is healthy
  - You want to free resources for that stream only

Use GOAWAY when:
  - The connection itself is broken
  - You're shutting down (graceful or immediate)
  - Too many errors have accumulated
  - A HPACK error occurs (ALWAYS connection-level)
```

### Pitfall 7: MAX_CONCURRENT_STREAMS is Advisory

Sending more streams than MAX_CONCURRENT_STREAMS is a PROTOCOL_ERROR. The sender MUST NOT exceed this limit. However, implementations often don't count closed (but not yet garbage-collected) streams correctly, leading to off-by-one bugs.

### Pitfall 8: SETTINGS Values Are Not Immediately Effective

When you send SETTINGS, the remote side applies them immediately. But YOUR side must wait for ACK before considering them effective for frames YOU SEND. This asymmetry trips people up constantly.

### Pitfall 9: Header Ordering in HTTP/2

Within a single HEADERS frame, pseudo-headers MUST come first. In HTTP/1.1 headers could appear in any order. In HTTP/2:
1. `:method`, `:scheme`, `:path`, `:authority` (in any order among themselves)
2. Regular headers (in any order among themselves)
3. Trailers after DATA

Violating this is a PROTOCOL_ERROR.

### Pitfall 10: Padding Counts Toward Frame Size

If PADDED flag is set, the pad_length byte + padding bytes count toward the frame's payload length and toward flow control. A DATA frame of length 100 with 50 bytes of padding delivers only 49 bytes of actual data (1 byte for pad_length field + 50 bytes padding + 49 bytes data).

---

## Appendix: HTTP/2 vs HTTP/1.1 vs HTTP/3 Comparison

```
Feature            HTTP/1.1        HTTP/2          HTTP/3 (QUIC)
─────────────────────────────────────────────────────────────────
Transport          TCP             TCP             UDP (QUIC)
Protocol format    Text            Binary frames   Binary frames
Multiplexing       No (pipelining  Yes (streams)   Yes (streams)
                   broken)
HOL blocking       Yes (HTTP+TCP)  TCP-level only  No
Header compression No              HPACK           QPACK
Server push        No              Yes (limited)   No (deprecated)
Connection setup   1-2 RTT         1-2 RTT         0-1 RTT
Connections/origin 6 (browser)     1               1
Stream priority    No              Yes (tree)      Yes (urgency)
TLS requirement    Optional        Effectively yes Yes (QUIC crypto)
Current RFC        RFC 9112        RFC 9113        RFC 9114
```

---

## Key Mental Models for Mastery

**Model 1: HTTP/2 = Multiplexed Binary Pipe**
One TCP connection = N concurrent streams. Every stream is a request-response pair. Frames are the atoms; streams are the molecules.

**Model 2: HPACK = Shared Dictionary Compression**
Both sides maintain an identical dictionary (dynamic table). Encode once, reference forever. State must be in perfect sync — any desync = connection death.

**Model 3: Flow Control = Two-Level Leaky Bucket**
Two buckets (connection + stream). You can only pour as fast as the slowest bucket drains. Refill (WINDOW_UPDATE) eagerly.

**Model 4: Stream State = Dual Half-Close**
Each side can close their send direction independently. Think TCP's FIN semantics applied to each logical stream.

**Model 5: GOAWAY = Last-Write Wins, Never Retry Without Knowing**
GOAWAY tells you which streams were processed. Only streams with ID > last_stream_id were NOT processed. These are safe to retry.

---

*This guide reflects RFC 9113 (HTTP/2, 2022), RFC 7541 (HPACK), and RFC 9218 (Extensible Priorities).*

