# gRPC & HTTP/2: Multiple Streams Over a Single TCP Connection
### A Complete End-to-End Deep Dive — Protocol · Kernel · Network · Code

---

## Table of Contents

1. [Mental Model First — The Core Analogy](#1-mental-model-first--the-core-analogy)
2. [The Problem HTTP/2 Solves — HTTP/1.x Pain](#2-the-problem-http2-solves--http1x-pain)
3. [TCP Fundamentals — The Foundation](#3-tcp-fundamentals--the-foundation)
4. [HTTP/2 Architecture — The Binary Framing Layer](#4-http2-architecture--the-binary-framing-layer)
5. [Streams, Messages, and Frames — The Holy Trinity](#5-streams-messages-and-frames--the-holy-trinity)
6. [HTTP/2 Frame Format — Byte-Level Protocol Anatomy](#6-http2-frame-format--byte-level-protocol-anatomy)
7. [Stream Lifecycle — State Machine Deep Dive](#7-stream-lifecycle--state-machine-deep-dive)
8. [Flow Control — Backpressure Mechanism](#8-flow-control--backpressure-mechanism)
9. [HPACK — Header Compression](#9-hpack--header-compression)
10. [TLS and ALPN — How HTTP/2 is Negotiated](#10-tls-and-alpn--how-http2-is-negotiated)
11. [Multiplexing Under the Hood — Frame Interleaving](#11-multiplexing-under-the-hood--frame-interleaving)
12. [gRPC on Top of HTTP/2 — The Mapping](#12-grpc-on-top-of-http2--the-mapping)
13. [gRPC Streaming Types — All Four Patterns](#13-grpc-streaming-types--all-four-patterns)
14. [Kernel Level — Socket Buffers and TCP Stack](#14-kernel-level--socket-buffers-and-tcp-stack)
15. [Network Level — Wire Format and Packet Flow](#15-network-level--wire-format-and-packet-flow)
16. [Complete C Implementation](#16-complete-c-implementation)
17. [Complete Rust Implementation (Tonic)](#17-complete-rust-implementation-tonic)
18. [Complete Go Implementation](#18-complete-go-implementation)
19. [Performance Tuning — Expert Knobs](#19-performance-tuning--expert-knobs)
20. [Hidden Gotchas and Expert Insights](#20-hidden-gotchas-and-expert-insights)

---

## 1. Mental Model First — The Core Analogy

Before diving into bytes and bits, build the right mental model.

### The Old Way (HTTP/1.1): A Single-Lane Road

```
CLIENT                            SERVER
  |                                  |
  |---[ Request A ]----------------->|
  |                                  | (server processes A)
  |<--[ Response A ]-----------------|
  |                                  |
  |---[ Request B ]----------------->|   ← B must WAIT for A to finish
  |                                  | (server processes B)
  |<--[ Response B ]-----------------|
  |                                  |
```

One request at a time. Like a single-lane bridge — only one car crosses at a time.

### The New Way (HTTP/2): A Multi-Lane Highway

```
CLIENT                            SERVER
  |                                  |
  |---[ Stream 1: Request A ]------->|
  |---[ Stream 3: Request B ]------->|   ← All sent simultaneously
  |---[ Stream 5: Request C ]------->|
  |                                  |
  |<--[ Stream 3: Response B ]-------|   ← B finishes first, returns first
  |<--[ Stream 1: Response A ]-------|   ← A returns next
  |<--[ Stream 5: Response C ]-------|
  |                                  |
```

Multiple requests fly in parallel over ONE TCP connection. Each is a **stream**.

### The Fundamental Insight

```
┌─────────────────────────────────────────────────────────────┐
│                    ONE TCP CONNECTION                        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Stream 1   │  │  Stream 3   │  │  Stream 5   │  . . .  │
│  │ (Request A) │  │ (Request B) │  │ (Request C) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  All streams share the same bytes on the wire,              │
│  tagged with stream IDs to keep them separated.             │
└─────────────────────────────────────────────────────────────┘
```

**A stream is just a logical concept.** On the wire, there is no "stream" — only frames tagged with a stream ID. The receiver reassembles frames by ID.

---

## 2. The Problem HTTP/2 Solves — HTTP/1.x Pain

### Concept: Head-of-Line (HOL) Blocking

**Head-of-Line blocking** means: a slow/large item at the front of a queue blocks everything behind it, even if those items are small and ready.

Think of a grocery store with one cashier. A person with a full cart blocks the person behind with just one item.

### HTTP/1.0: One Request Per Connection

```
Connection 1:  [REQ]-------[RESP]
                                  [REQ]-------[RESP]   ← Sequential, same connection
```

### HTTP/1.1 Improvement: Pipelining (Rarely Used)

```
Connection 1:  [REQ-A][REQ-B][REQ-C]→→→[RESP-A][RESP-B][RESP-C]
```

Requests sent together, but responses MUST come back in order. If RESP-A is slow, RESP-B and RESP-C are stuck. Still head-of-line blocked at the response level.

### Browser Hack: Multiple Connections

```
Connection 1:  [REQ-A]----[RESP-A]
Connection 2:  [REQ-B]----[RESP-B]
Connection 3:  [REQ-C]----[RESP-C]
Connection 4:  [REQ-D]----[RESP-D]
Connection 5:  [REQ-E]----[RESP-E]
Connection 6:  [REQ-F]----[RESP-F]   ← Browsers open 6 connections per host
```

**Problems with this approach:**
- Each TCP connection needs a 3-way handshake (1.5 RTT overhead)
- Each TLS connection needs another 1-2 RTT handshake
- TCP slow start restarts for each connection
- Server sees 6x more connections → 6x more memory
- Unfair bandwidth distribution

### HTTP/2 Solution: True Multiplexing

```
ONE Connection:

Wire: [F1-S1][F1-S3][F2-S1][F1-S5][F3-S3][F2-S5][F4-S1]...

     S1=Stream1, S3=Stream3, S5=Stream5
     F1=Frame1 of that stream, etc.

Receiver reassembles:
  Stream 1: [F1-S1][F2-S1][F4-S1]... → Response A
  Stream 3: [F1-S3][F3-S3]...         → Response B (arrives first!)
  Stream 5: [F1-S5][F2-S5]...         → Response C
```

---

## 3. TCP Fundamentals — The Foundation

Before HTTP/2, you must understand what TCP gives us and what it doesn't.

### What TCP Provides

```
┌─────────────────────────────────────────────────────────┐
│                   TCP GUARANTEES                         │
│                                                          │
│  1. Reliable delivery — every byte arrives              │
│  2. Ordered delivery — bytes arrive in send order       │
│  3. Error detection — corrupt packets retransmitted      │
│  4. Flow control — receiver can throttle sender          │
│  5. Congestion control — adapts to network capacity      │
└─────────────────────────────────────────────────────────┘
```

### What TCP Does NOT Provide

```
┌─────────────────────────────────────────────────────────┐
│                 TCP DOES NOT KNOW ABOUT                  │
│                                                          │
│  1. Messages or requests                                 │
│  2. Multiple logical conversations                       │
│  3. Priority between different data                      │
│  4. Header compression                                   │
│                                                          │
│  TCP sees only a stream of bytes — no structure.         │
└─────────────────────────────────────────────────────────┘
```

### TCP: The Byte Stream Model

```
Application writes:  "Hello, World!"
TCP sees:            48 65 6C 6C 6F 2C 20 57 6F 72 6C 64 21
                     └──────────────────────────────────────┘
                                  Just bytes.
                     No concept of where one message ends
                     and another begins.
```

**This is why HTTP/2 needs a framing layer** — to impose structure on the TCP byte stream.

### TCP 3-Way Handshake

```
CLIENT                          SERVER
  |                               |
  |---SYN (seq=x)---------------->|    Step 1: Client says "hello"
  |<--SYN-ACK (seq=y, ack=x+1)---|    Step 2: Server says "hello back"
  |---ACK (ack=y+1)-------------->|    Step 3: Client acknowledges
  |                               |
  |   CONNECTION ESTABLISHED      |
  |   (1.5 Round Trip Times)      |
```

### TCP Slow Start

```
Time→    0    1    2    3    4    5    6
cwnd:    1    2    4    8   16   32   64   ← Doubles until congestion
         MSS  MSS  MSS  MSS  MSS  MSS  MSS
         
cwnd = Congestion Window (how many packets can be in-flight)
MSS  = Maximum Segment Size (~1460 bytes for Ethernet)
```

New TCP connections start slow. This hurts small requests. HTTP/2's connection reuse avoids this — the connection is already "warmed up."

---

## 4. HTTP/2 Architecture — The Binary Framing Layer

### The Layered Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                          │
│                   (gRPC / HTTP semantics)                     │
├──────────────────────────────────────────────────────────────┤
│                   HTTP/2 FRAMING LAYER                        │
│         (Streams, Flow Control, Header Compression)           │
├──────────────────────────────────────────────────────────────┤
│                       TLS 1.2/1.3                             │
│              (Encryption + ALPN Negotiation)                  │
├──────────────────────────────────────────────────────────────┤
│                          TCP                                  │
│           (Reliable, Ordered Byte Stream)                     │
├──────────────────────────────────────────────────────────────┤
│                          IP                                   │
│              (Packet Routing, Addressing)                     │
├──────────────────────────────────────────────────────────────┤
│                       Ethernet / WiFi                         │
│               (Physical Signal Transmission)                  │
└──────────────────────────────────────────────────────────────┘
```

### HTTP/2 vs HTTP/1.1: Text vs Binary

**HTTP/1.1 (Text-based):**
```
GET /api/users HTTP/1.1\r\n
Host: example.com\r\n
Accept: application/json\r\n
\r\n
```
Human-readable but wasteful. Parsers are error-prone (injection attacks, whitespace issues).

**HTTP/2 (Binary):**
```
00 00 1F  ← Length: 31 bytes
01        ← Type: HEADERS frame
04        ← Flags: END_HEADERS
00 00 00  ← Reserved bit + Stream ID
00 01
[HPACK-encoded headers...]
```

Binary is compact, faster to parse, and harder to corrupt with invalid characters.

---

## 5. Streams, Messages, and Frames — The Holy Trinity

These three concepts are the foundation of HTTP/2. Memorize them.

### Definitions

```
┌──────────────────────────────────────────────────────────┐
│  FRAME   = Smallest unit of communication in HTTP/2      │
│            Every byte on the wire is inside a frame.     │
│            A frame has: type, stream ID, flags, payload  │
├──────────────────────────────────────────────────────────┤
│  MESSAGE = Complete HTTP request or response             │
│            Made of one or more frames (on one stream)    │
│            e.g., HEADERS frame + DATA frames             │
├──────────────────────────────────────────────────────────┤
│  STREAM  = Bidirectional logical channel                 │
│            Has an integer ID (1, 3, 5... client-init)   │
│            Carries one request-response pair (or more   │
│            for gRPC streaming)                           │
└──────────────────────────────────────────────────────────┘
```

### The Relationship

```
CONNECTION
│
├── Stream 1
│   ├── Message (Request)
│   │   ├── HEADERS frame  (method, path, headers)
│   │   └── DATA frame     (request body)
│   └── Message (Response)
│       ├── HEADERS frame  (status, response headers)
│       ├── DATA frame     (response body chunk 1)
│       ├── DATA frame     (response body chunk 2)
│       └── DATA frame     (END_STREAM flag set)
│
├── Stream 3
│   ├── Message (Request)  ... (interleaved with Stream 1)
│   └── Message (Response) ...
│
└── Stream 5
    └── ...
```

### Stream ID Numbering Rules

```
Client-initiated streams:  1, 3, 5, 7, ...  (odd numbers)
Server-initiated streams:  2, 4, 6, 8, ...  (even numbers, for server push)
Stream 0:                  Connection-level frames (SETTINGS, PING, GOAWAY)

Why odd/even? Prevents collision when both sides initiate streams simultaneously.
Each side increments their own counter independently.
```

### Concurrent Streams Example

```
Timeline (→ is time):

Client sends:
  t=0: [HEADERS Stream-1] [HEADERS Stream-3] [HEADERS Stream-5]
  t=1: [DATA Stream-1, chunk1] [DATA Stream-3, chunk1]
  t=2: [DATA Stream-5, chunk1] [DATA Stream-1, chunk2, END]
  t=3: [DATA Stream-3, END] [DATA Stream-5, END]

Server sends (independently, simultaneously):
  t=1: [HEADERS Stream-3 response] 
  t=2: [DATA Stream-3 response, END]  ← Stream 3 done first
  t=3: [HEADERS Stream-1 response] [DATA Stream-1 response, END]
  t=4: [HEADERS Stream-5 response] [DATA Stream-5 response, END]

All over ONE TCP connection.
```

---

## 6. HTTP/2 Frame Format — Byte-Level Protocol Anatomy

Every frame has a fixed 9-byte header followed by a payload.

### Frame Header Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─────────────────────────────────────────┤
│               Length (24 bits)          │   ← Payload size in bytes
├─────────────┬───────────────────────────┤
│  Type (8b)  │       Flags (8 bits)      │   ← Frame type + behavioral flags
├─┬───────────────────────────────────────┤
│R│           Stream Identifier (31 bits) │   ← Which stream this frame belongs to
├─┴───────────────────────────────────────┤
│                  Payload                │   ← Frame-type specific data
│            (Length bytes)               │
└─────────────────────────────────────────┘

R = Reserved bit (always 0, ignored on receive)
Total header = 9 bytes
```

### All Frame Types

```
Type  Name              Purpose
────  ────────────────  ────────────────────────────────────────────────
0x0   DATA              Carries request/response body payload
0x1   HEADERS           HTTP headers (request line, response status, etc.)
0x2   PRIORITY          Stream priority hints (deprecated in RFC 9113)
0x3   RST_STREAM        Immediately terminate a stream (error or cancel)
0x4   SETTINGS          Connection parameters (window size, max streams)
0x5   PUSH_PROMISE      Server announces a resource it will push
0x6   PING              Heartbeat / RTT measurement
0x7   GOAWAY            Gracefully shut down connection, report last stream
0x8   WINDOW_UPDATE     Flow control credit (increase receive window)
0x9   CONTINUATION      Continuation of a HEADERS frame (large headers)
```

### DATA Frame Layout

```
Frame Header:
  Length:    0x000064  (100 bytes)
  Type:      0x00      (DATA)
  Flags:     0x01      (END_STREAM = this is the last data frame)
  Stream ID: 0x00000001 (Stream 1)

Payload (if padded):
  ┌──────────────┬──────────────────────────────────┬──────────────┐
  │ Pad Length   │           Data                   │   Padding    │
  │  (1 byte)    │      (Length - PadLen - 1)        │  (PadLen)    │
  └──────────────┴──────────────────────────────────┴──────────────┘

Payload (not padded, flag PADDED not set):
  ┌──────────────────────────────────────────────────────────────┐
  │                        Data (Length bytes)                    │
  └──────────────────────────────────────────────────────────────┘

Flags:
  0x1 = END_STREAM  → Last frame for this stream (half-close)
  0x8 = PADDED      → Payload has padding bytes
```

### HEADERS Frame Layout

```
Frame Header:
  Length:    variable
  Type:      0x01  (HEADERS)
  Flags:     0x05  (END_HEADERS | END_STREAM for requests with no body)
  Stream ID: 0x00000001

Payload:
  ┌─────────────────────────────────────────────┐
  │ [E|Dep. Stream ID (31b)] [Weight (8b)]       │  ← Only if PRIORITY flag set
  ├─────────────────────────────────────────────┤
  │          HPACK-encoded Header Block          │
  │  (compressed :method, :path, :authority,    │
  │   :scheme, content-type, custom headers)    │
  └─────────────────────────────────────────────┘

Flags:
  0x1 = END_STREAM   → No DATA frames will follow (GET requests)
  0x4 = END_HEADERS  → No CONTINUATION frames follow
  0x8 = PADDED
  0x20 = PRIORITY    → Stream dependency info included
```

### SETTINGS Frame Layout

```
Type: 0x4, Stream ID: 0 (connection-level)

Payload: List of (Identifier: 16bit, Value: 32bit) pairs

Setting ID  Name                        Default
──────────  ──────────────────────────  ─────────
0x1         HEADER_TABLE_SIZE           4096
0x2         ENABLE_PUSH                 1
0x3         MAX_CONCURRENT_STREAMS      unlimited
0x4         INITIAL_WINDOW_SIZE         65535 bytes
0x5         MAX_FRAME_SIZE              16384 bytes
0x6         MAX_HEADER_LIST_SIZE        unlimited

Example SETTINGS payload (hex):
  00 03  00 00 00 64    ← MAX_CONCURRENT_STREAMS = 100
  00 04  00 04 00 00    ← INITIAL_WINDOW_SIZE = 262144 (256KB)
  00 05  00 00 40 00    ← MAX_FRAME_SIZE = 16384 (16KB)
```

### WINDOW_UPDATE Frame Layout

```
Type: 0x8, 4-byte payload

  ┌─┬──────────────────────────────────┐
  │R│  Window Size Increment (31 bits)  │
  └─┴──────────────────────────────────┘

  Stream ID = 0 → connection-level window update
  Stream ID > 0 → stream-level window update
```

### RST_STREAM Frame

```
Type: 0x3, 4-byte payload

  ┌──────────────────────────────────────┐
  │         Error Code (32 bits)          │
  └──────────────────────────────────────┘

Error Codes:
  0x0  NO_ERROR          Graceful reset
  0x1  PROTOCOL_ERROR    HTTP/2 protocol violation
  0x2  INTERNAL_ERROR    Implementation error
  0x3  FLOW_CONTROL_ERROR  Violated flow control
  0x5  STREAM_CLOSED     Frame sent on closed stream
  0x8  CANCEL            Stream cancelled by peer
  0xB  ENHANCE_YOUR_CALM  Rate-limit violation
```

---

## 7. Stream Lifecycle — State Machine Deep Dive

A stream progresses through states. Understanding this is essential for debugging gRPC errors.

### Stream State Machine

```
                         ┌─────────┐
                         │  IDLE   │  ← Every stream starts here
                         └────┬────┘
                              │
              Client sends    │   Server receives
              HEADERS frame   │   PUSH_PROMISE
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │   OPEN   │    │RESERVED  │    │RESERVED  │
         │          │    │(local)   │    │(remote)  │
         └────┬─────┘    └────┬─────┘    └────┬─────┘
              │               │               │
              │    Send/Recv  │               │
              │    END_STREAM │               │
         ┌────┴──────────────────────────────┴────┐
         │                                         │
         ↓                           ↓             ↓
  ┌──────────────┐          ┌──────────────┐
  │ HALF-CLOSED  │          │ HALF-CLOSED  │
  │  (local)     │          │  (remote)    │
  │ Can receive, │          │ Can send,    │
  │ cannot send  │          │ cannot recv  │
  └──────┬───────┘          └──────┬───────┘
         │                         │
         │    Both sides sent      │
         │    END_STREAM / RST     │
         └─────────────┬───────────┘
                        ↓
                  ┌──────────┐
                  │  CLOSED  │  ← Stream ID freed, can be reused
                  └──────────┘
```

### State Transition Examples

**Unary RPC (single request, single response):**

```
Client                                    Server
   │                                         │
   │ Stream 1: IDLE                           │
   │                                         │
   │──[HEADERS + END_HEADERS]──────────────→ │  Client: IDLE → OPEN
   │──[DATA + END_STREAM]──────────────────→ │  Client: OPEN → HALF-CLOSED(local)
   │                                         │  Server: IDLE → OPEN → HALF-CLOSED(remote)
   │                                         │
   │ ←──────────────[HEADERS + END_HEADERS]──│  Server: HALF-CLOSED → OPEN
   │ ←──────────────[DATA + END_STREAM]──────│  Server: OPEN → CLOSED
   │                                         │  Client: HALF-CLOSED(local) → CLOSED
   │                                         │
   │ Stream 1: CLOSED                         │
```

**Server Streaming RPC:**

```
Client                                    Server
   │──[HEADERS + END_STREAM]──────────────→ │  Client sends request + closes send side
   │                                         │  (END_STREAM on request means no body)
   │ ←──────────────[HEADERS]───────────────│
   │ ←──────────────[DATA, chunk 1]──────── │
   │ ←──────────────[DATA, chunk 2]──────── │  Server sends many DATA frames
   │ ←──────────────[DATA, chunk 3]──────── │
   │ ←──────────────[DATA + END_STREAM]──── │  Server closes stream
```

---

## 8. Flow Control — Backpressure Mechanism

### What is Flow Control?

**Flow control** prevents a fast sender from overwhelming a slow receiver. Without it, the sender could fill up the receiver's buffers, causing packet loss and retransmissions.

**Concept: Backpressure** — The receiver tells the sender how much data it can handle. If the receiver is slow (busy processing), it sends smaller window updates, slowing the sender down. This propagates back through the system — **pressure flows backward** from consumer to producer.

### Two Levels of Flow Control in HTTP/2

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: Connection-Level Flow Control                      │
│                                                              │
│  Total bytes in-flight across ALL streams combined           │
│  Default: 65,535 bytes (64KB - 1)                           │
│  Can be increased via WINDOW_UPDATE on stream ID 0          │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 2: Stream-Level Flow Control                          │
│                                                              │
│  Bytes in-flight for ONE specific stream                     │
│  Default: 65,535 bytes per stream                           │
│  Increased via WINDOW_UPDATE on that stream's ID            │
└─────────────────────────────────────────────────────────────┘
```

Both must have space for data to flow. The effective window = min(connection window, stream window).

### Flow Control Mechanism Step by Step

```
CLIENT                                              SERVER
  │                                                   │
  │  Initial window: 65535 bytes (stream)             │
  │  Initial window: 65535 bytes (connection)         │
  │                                                   │
  │──[DATA, 16384 bytes, Stream 1]─────────────────→ │
  │    Stream window: 65535 - 16384 = 49151           │
  │    Conn window:   65535 - 16384 = 49151           │
  │                                                   │
  │──[DATA, 16384 bytes, Stream 1]─────────────────→ │
  │    Stream window: 49151 - 16384 = 32767           │
  │    Conn window:   49151 - 16384 = 32767           │
  │                                                   │
  │──[DATA, 16384 bytes, Stream 1]─────────────────→ │
  │    Stream window: 32767 - 16384 = 16383           │
  │    Conn window:   32767 - 16384 = 16383           │
  │                                                   │
  │  (server processes data, frees buffer)            │
  │                                                   │
  │ ←──[WINDOW_UPDATE, Stream 1, +65535]─────────── │  Server grants more credit
  │ ←──[WINDOW_UPDATE, Stream 0, +65535]─────────── │
  │    Stream window: 16383 + 65535 = 81918           │
  │    Conn window:   16383 + 65535 = 81918           │
  │                                                   │
  │  Can now send more data...                        │
```

### Flow Control Deadlock (Critical Bug to Know)

```
DEADLOCK SCENARIO:

  Connection window = 0 (exhausted)
  Stream 1 wants to send a WINDOW_UPDATE for Stream 3
  But WINDOW_UPDATE is a non-DATA frame — NOT subject to flow control!
  
  WAIT: Only DATA frames consume flow control window.
        HEADERS, WINDOW_UPDATE, PING, SETTINGS are never blocked.
        
  Real deadlock: Client and server both waiting for WINDOW_UPDATE
  from each other, but neither can send DATA to trigger the update.
  
  Prevention: Libraries like gRPC send WINDOW_UPDATE proactively,
              before the window is fully exhausted.
```

### gRPC Window Sizes (Recommended for Production)

```
Initial connection window:  1MB   (1 << 20)
Initial stream window:      1MB   (1 << 20)
Max frame size:             16KB  (default, usually fine)
```

---

## 9. HPACK — Header Compression

### The Problem

HTTP headers repeat constantly:
```
:method: GET          ← Same for every GET request
:scheme: https        ← Same for all requests
:authority: api.foo   ← Same for all requests in session
user-agent: grpc-go   ← Same for all requests
content-type: application/grpc  ← Same for all gRPC calls
authorization: Bearer eyJh...   ← Same token, 200+ bytes, repeated!
```

Without compression, headers consume 200-800 bytes per request. In gRPC microservices with thousands of RPCs/second, this adds up to gigabytes.

### HPACK Solution: Two Compression Techniques

**Technique 1: Static Table (61 pre-defined header pairs)**

```
Index  Name                Value
─────  ──────────────────  ─────────────────────
1      :authority          
2      :method             GET
3      :method             POST
4      :path               /
5      :path               /index.html
6      :scheme             http
7      :scheme             https
8      :status             200
...
61     www-authenticate    

Instead of sending ":method: POST" (12 bytes),
send index 3 (1 byte).  12x compression!
```

**Technique 2: Dynamic Table (learned during session)**

```
First request:
  Send: content-type: application/grpc  (full, 36 bytes)
  HPACK adds this to dynamic table at index 62
  
Second request:
  Send: index 62  (1 byte!)
  Receiver knows: "index 62 = content-type: application/grpc"
  
Dynamic table evicts old entries (LRU) when full.
```

**Technique 3: Huffman Encoding**

Values that aren't in the table are Huffman-encoded:
```
Authorization: Bearer eyJhbGci...

Huffman encoding reduces arbitrary strings by ~30%.
```

### HPACK Wire Format (Simplified)

```
Indexed Header Field (from table):
  ┌─────────────────────────────┐
  │ 1 │    Index (7 bits)       │   Prefix bit 1 = "use table lookup"
  └─────────────────────────────┘

Literal Header with Incremental Indexing:
  ┌──────────────────────────────┐
  │ 0 1 │  Index/0 (6 bits)     │   "01" prefix = "add to dynamic table"
  ├──────────────────────────────┤
  │ H │    Name Length           │   H = Huffman-encoded?
  ├──────────────────────────────┤
  │         Name String          │
  ├──────────────────────────────┤
  │ H │    Value Length          │
  ├──────────────────────────────┤
  │         Value String         │
  └──────────────────────────────┘

Never-Indexed Literal (for sensitive headers like auth tokens):
  ┌──────────────────────────────┐
  │ 0 0 0 1 │ Index (4 bits)    │   "0001" = "never add to table"
  └──────────────────────────────┘
  This prevents intermediaries (proxies) from caching sensitive values.
```

---

## 10. TLS and ALPN — How HTTP/2 is Negotiated

### ALPN: Application-Layer Protocol Negotiation

HTTP/2 needs to be negotiated with the server. You can't just send HTTP/2 frames to a server expecting HTTP/1.1. **ALPN** (a TLS extension) handles this during the TLS handshake.

```
CLIENT                                           SERVER
  │                                               │
  │──TLS ClientHello──────────────────────────→  │
  │   Extensions:                                 │
  │     ALPN: ["h2", "http/1.1"]                 │  "I speak H2 and HTTP/1.1"
  │                                               │
  │ ←─TLS ServerHello─────────────────────────── │
  │   Extensions:                                 │
  │     ALPN: "h2"                               │  "Let's use HTTP/2"
  │                                               │
  │ ←─TLS Certificate──────────────────────────  │
  │ ←─TLS Finished─────────────────────────────  │
  │──TLS Finished────────────────────────────→   │
  │                                               │
  │  NOW: Send HTTP/2 Connection Preface          │
  │──PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n──────────→│  (24-byte magic string)
  │──SETTINGS frame──────────────────────────→   │
  │ ←─SETTINGS frame─────────────────────────── │
  │──SETTINGS ACK────────────────────────────→   │
  │ ←─SETTINGS ACK───────────────────────────── │
  │                                               │
  │  HTTP/2 CONNECTION READY                      │
```

### HTTP/2 Connection Preface (Magic String)

```
Hex:  50 52 49 20 2A 20 48 54 54 50 2F 32 2E 30 0D 0A
      0D 0A 53 4D 0D 0A 0D 0A

ASCII: "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

Purpose: If a confused HTTP/1.1 server receives this, it will respond
         with a 400 or 505 error, signaling the protocol mismatch clearly.
         
After this magic string, the client immediately sends a SETTINGS frame.
```

### Cleartext HTTP/2 (h2c)

HTTP/2 without TLS — used in internal microservices (gRPC internal traffic):

```
Client sends HTTP/1.1 Upgrade request:
  GET / HTTP/1.1
  Host: example.com
  Connection: Upgrade, HTTP2-Settings
  Upgrade: h2c
  HTTP2-Settings: <base64-encoded SETTINGS>

Server responds:
  HTTP/1.1 101 Switching Protocols
  Connection: Upgrade
  Upgrade: h2c

Now both sides speak HTTP/2.
```

---

## 11. Multiplexing Under the Hood — Frame Interleaving

This is the heart of HTTP/2. Let's trace exactly how multiple streams coexist.

### The Multiplexer: Shared TCP Write Buffer

```
                    ┌────────────────────────────────┐
                    │         APPLICATION              │
                    │                                  │
                    │  Stream 1: 1MB file upload       │
                    │  Stream 3: Small API call        │
                    │  Stream 5: Streaming response    │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │         HTTP/2 FRAMER            │
                    │                                  │
                    │  Chops data into frames          │
                    │  (max MAX_FRAME_SIZE each)       │
                    │  Interleaves based on priority   │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼─────────────────┐
                    │      TCP SEND BUFFER             │
                    │                                  │
                    │  [F-S1][F-S3][F-S1][F-S5][F-S1] │
                    │  ←──────────────────────────     │
                    │  (FIFO queue, kernel drains it)  │
                    └──────────────┬─────────────────┘
                                   │
                                   ▼
                              To the wire
```

### Why Interleaving Matters: The Large File Problem

**HTTP/1.1 Without Multiplexing:**
```
Client uploading 10MB file:
  [1MB][1MB][1MB][1MB][1MB][1MB][1MB][1MB][1MB][1MB] ← All of stream 1
  
  Stream 3 (small urgent call) must WAIT behind 10MB of data.
  Latency: 10MB / bandwidth
```

**HTTP/2 With Multiplexing:**
```
Client uploading 10MB file AND sending urgent request:
  [S1: 16KB][S3: headers+body][S1: 16KB][S1: 16KB]...
  
  Stream 3's small request slips between stream 1's chunks.
  Stream 3 latency: ~1 RTT, regardless of stream 1 size.
```

### Frame Interleaving Visualization

```
Time ────────────────────────────────────────────────────────────→

Stream 1 (Large Upload, 64KB):
  ████████████████████████████████████████████████████████████████

Stream 3 (Small API Call):
  ░░

On the Wire (HTTP/2 multiplexed):
  ████░░████████████████████████████████████████████████████████
  S1   S3 S1   S1   S1   S1   S1   S1   S1   S1   S1   S1   S1

Stream 3 finishes in milliseconds despite stream 1 being huge!
```

### Priority and Weight (HTTP/2 Stream Priority)

Note: Explicit priority was deprecated in RFC 9113 (HTTP/2 revision) but widely implemented. Understanding it helps debug legacy systems.

```
Priority Tree:

Stream 0 (root)
├── Stream 1 (weight=32)   ← Normal priority
├── Stream 3 (weight=128)  ← High priority (4x more bandwidth than Stream 1)
└── Stream 5 (weight=16)   ← Low priority (background task)

Bandwidth allocation:
  Total weight = 32 + 128 + 16 = 176
  Stream 1: 32/176  ≈ 18%
  Stream 3: 128/176 ≈ 73%
  Stream 5: 16/176  ≈ 9%
```

---

## 12. gRPC on Top of HTTP/2 — The Mapping

gRPC is a thin layer on HTTP/2. Understanding the mapping is critical.

### gRPC Request → HTTP/2 Mapping

```
gRPC Call:
  Service: UserService
  Method:  GetUser
  Request: { user_id: 42 }

Becomes HTTP/2:
  ┌──────────────────────────────────────────────────────┐
  │  HEADERS Frame (stream 1)                            │
  │                                                      │
  │  :method = POST           ← gRPC always uses POST   │
  │  :scheme = https                                     │
  │  :path   = /UserService/GetUser  ← /{pkg}.{svc}/{method}│
  │  :authority = api.example.com                        │
  │  content-type = application/grpc  ← REQUIRED        │
  │  grpc-timeout = 30S        ← optional deadline       │
  │  grpc-encoding = gzip      ← optional compression    │
  │  authorization = Bearer... ← custom metadata         │
  └──────────────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────────────┐
  │  DATA Frame (stream 1)                               │
  │                                                      │
  │  [Compressed Flag: 1 byte]                           │
  │  [Message Length:  4 bytes] ← Big-endian uint32     │
  │  [Protobuf Bytes:  N bytes] ← Serialized message    │
  └──────────────────────────────────────────────────────┘
```

### gRPC Message Framing (Length-Prefixed)

```
gRPC adds its own framing INSIDE the HTTP/2 DATA frame payload:

Byte 0:     Compressed-Flag (0 = not compressed, 1 = compressed)
Bytes 1-4:  Message-Length (big-endian 32-bit unsigned integer)
Bytes 5+:   Message (Protocol Buffer bytes)

Example: A 100-byte protobuf message, uncompressed:
  00                ← Not compressed
  00 00 00 64       ← Length = 100
  [100 bytes of protobuf]

Total: 105 bytes in the DATA frame payload.
```

### gRPC Response → HTTP/2 Mapping

```
gRPC unary response needs TWO HTTP/2 messages:

Message 1 (response headers + body):
  ┌──────────────────────────────────────────────────────┐
  │  HEADERS Frame                                       │
  │  :status = 200                                       │
  │  content-type = application/grpc                     │
  │  [response metadata]                                 │
  └──────────────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────────────┐
  │  DATA Frame                                          │
  │  [grpc message framing][protobuf bytes]              │
  └──────────────────────────────────────────────────────┘

Message 2 (trailers — gRPC status):
  ┌──────────────────────────────────────────────────────┐
  │  HEADERS Frame (with END_STREAM flag)                │
  │  grpc-status = 0             ← 0 = OK               │
  │  grpc-message = ""           ← Error message if any │
  │  [response metadata]                                 │
  └──────────────────────────────────────────────────────┘

Why two HEADERS frames? HTTP/2 "trailers" (end-of-stream headers)
allow gRPC to send status AFTER the body, enabling streaming.
```

### gRPC Status Codes (Trailers)

```
grpc-status value → Meaning
──────────────────────────────────────────────────────
0   OK                 Success
1   CANCELLED          Operation cancelled
2   UNKNOWN            Unknown error
3   INVALID_ARGUMENT   Bad request data
4   DEADLINE_EXCEEDED  Timeout expired
5   NOT_FOUND          Resource not found
6   ALREADY_EXISTS     Duplicate creation
7   PERMISSION_DENIED  Authorization failure
8   RESOURCE_EXHAUSTED  Rate limit / quota
9   FAILED_PRECONDITION State mismatch
10  ABORTED            Concurrency conflict
11  OUT_OF_RANGE       Value out of range
12  UNIMPLEMENTED      Method not implemented
13  INTERNAL           Internal server error
14  UNAVAILABLE        Server not ready (retry!)
15  DATA_LOSS          Unrecoverable data loss
16  UNAUTHENTICATED    Invalid credentials
```

---

## 13. gRPC Streaming Types — All Four Patterns

### Pattern 1: Unary RPC

One request → One response. Like a regular function call.

```
Client                          Server
  │──[HEADERS + DATA]──────────→ │   Send request
  │ ←──[HEADERS + DATA + HEADERS]─│   Receive response + trailers
  │                               │
  Stream lifecycle: ~2 RTT
  
  Use case: GetUser, CreateOrder, ValidateToken
```

### Pattern 2: Server Streaming RPC

One request → Stream of responses. Server sends multiple messages.

```
Client                          Server
  │──[HEADERS + DATA]──────────→ │   Send single request
  │ ←──[HEADERS]────────────────│   Response headers
  │ ←──[DATA: update 1]─────────│   First update
  │ ←──[DATA: update 2]─────────│   Second update
  │ ←──[DATA: update 3]─────────│   Third update
  │         ...                  │
  │ ←──[DATA + END_STREAM]──────│   Final update
  │ ←──[HEADERS: trailers]──────│   gRPC status
  │                               │
  Use case: Watch(resource), SubscribeToEvents, StreamLargeFile
  
  Key: Client sends END_STREAM early (no body); server streams until done.
```

### Pattern 3: Client Streaming RPC

Stream of requests → One response. Client sends multiple messages.

```
Client                          Server
  │──[HEADERS]─────────────────→ │   Open stream
  │──[DATA: chunk 1]────────────→│   Upload chunk
  │──[DATA: chunk 2]────────────→│   Upload chunk
  │──[DATA: chunk 3]────────────→│   Upload chunk
  │         ...                  │
  │──[DATA + END_STREAM]────────→│   Last chunk
  │ ←──[HEADERS + DATA + HEADERS]─│   Single response + trailers
  │                               │
  Use case: UploadFile, BatchInsert, AggregateMetrics
```

### Pattern 4: Bidirectional Streaming RPC

Stream of requests ↔ Stream of responses. Both sides stream simultaneously.

```
Client                          Server
  │──[HEADERS]─────────────────→ │   Open stream
  │──[DATA: msg 1]──────────────→│
  │ ←──[HEADERS]────────────────│   Server opens response stream
  │ ←──[DATA: response 1]───────│
  │──[DATA: msg 2]──────────────→│
  │ ←──[DATA: response 2]───────│   Responses don't need to match requests
  │ ←──[DATA: response 3]───────│   Server can send proactively
  │──[DATA + END_STREAM]────────→│   Client done sending
  │ ←──[DATA: response 4]───────│   Server can still send after client done
  │ ←──[HEADERS: trailers]──────│   Server closes stream
  │                               │
  Use case: Chat, RealTimeCollaboration, TelemetryPipeline, Gaming
  
  This is gRPC's most powerful pattern.
  Full-duplex: Both sides send/receive independently.
```

---

## 14. Kernel Level — Socket Buffers and TCP Stack

### The Journey of a gRPC Frame Through the Kernel

```
USER SPACE                          KERNEL SPACE

┌──────────────┐    write()        ┌──────────────────────────────────┐
│  gRPC App    │ ────────────────→ │   TCP Send Buffer (SO_SNDBUF)    │
│  (your code) │                   │   Default: 128KB - 4MB           │
└──────────────┘                   │   Accumulates data until ACK'd   │
                                   └──────────────┬───────────────────┘
                                                  │
                                   ┌──────────────▼───────────────────┐
                                   │         TCP Protocol Stack        │
                                   │                                   │
                                   │  1. Segment data into MSS chunks  │
                                   │     (MSS ≈ 1460 bytes for Eth)   │
                                   │  2. Add TCP header (20+ bytes)   │
                                   │  3. Track sequence numbers        │
                                   │  4. Apply congestion control      │
                                   │     (cwnd, ssthresh)             │
                                   │  5. Apply Nagle's algorithm       │
                                   └──────────────┬───────────────────┘
                                                  │
                                   ┌──────────────▼───────────────────┐
                                   │          TLS Layer (kernel)       │
                                   │  (or userspace: OpenSSL/rustls)  │
                                   │  Encrypt TCP payload              │
                                   │  Add TLS record header (5 bytes) │
                                   └──────────────┬───────────────────┘
                                                  │
                                   ┌──────────────▼───────────────────┐
                                   │        IP Protocol Stack          │
                                   │  Add IP header (20 bytes)         │
                                   │  Route to next hop               │
                                   └──────────────┬───────────────────┘
                                                  │
                                   ┌──────────────▼───────────────────┐
                                   │       NIC TX Ring Buffer          │
                                   │  DMA: kernel → NIC memory        │
                                   │  NIC sends electrical signal      │
                                   └──────────────┬───────────────────┘
                                                  │
                                              To network
```

### Socket Buffer Deep Dive

```
┌──────────────────────────────────────────────────────────┐
│                    TCP SOCKET BUFFERS                     │
│                                                          │
│  Send Buffer (SK_SNDBUF):                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ [sent, not ACK'd] [to send] [app write buffer]   │  │
│  └───────────────────────────────────────────────────┘  │
│    ← kernel manages →   ← kernel drains →               │
│                                                          │
│  Recv Buffer (SK_RCVBUF):                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ [received, not read by app] [free space]          │  │
│  └───────────────────────────────────────────────────┘  │
│    ← kernel fills →         ← app reads →               │
│                                                          │
│  TCP advertises recv buffer free space as its window.   │
│  When app is slow reading: recv buffer fills up →       │
│  TCP window shrinks → Sender slows down.                │
│  This is kernel-level backpressure.                      │
└──────────────────────────────────────────────────────────┘
```

### Nagle's Algorithm and TCP_NODELAY

**Nagle's Algorithm**: Delay sending small packets. Wait until:
- Data to send >= MSS (1460 bytes), OR
- All previous data has been ACK'd

**Problem for gRPC**: Small WINDOW_UPDATE frames (9 + 4 = 13 bytes) may be delayed by Nagle's algorithm, causing flow control stalls.

**Solution**: `TCP_NODELAY = 1` — disables Nagle's algorithm. gRPC implementations always set this.

```c
// C: Disabling Nagle's algorithm
int flag = 1;
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
```

### TCP Keep-Alive vs gRPC Keep-Alive

```
TCP Keep-Alive (kernel-level):
  Sends empty ACK packets when connection is idle
  Purpose: Detect dead connections (TCP half-open)
  Default interval: 2 hours (too slow for microservices!)
  
  setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &enable, sizeof(enable));
  setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE, &idle, sizeof(idle));    // 60s
  setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &interval, sizeof(interval)); // 10s
  setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT, &count, sizeof(count));   // 3

gRPC Keep-Alive (application-level, HTTP/2 PING frames):
  HTTP/2 PING frame sent by gRPC runtime
  If no PING ACK within timeout: connection declared dead
  More reliable than TCP keepalive for detecting broken paths
  (TCP keepalive doesn't detect middlebox timeouts)
  
  gRPC PING frame:
    Type: 0x6
    Flags: 0x0  (or 0x1 for PING ACK)
    Stream ID: 0
    Payload: 8-byte opaque value (echoed in ACK)
```

### Memory Layout: How Kernel Sees HTTP/2 Frames

```
TCP Receive Buffer (kernel memory):

Offset 0:  [TLS Record Header: 5 bytes]
Offset 5:  [HTTP/2 Frame Header: 9 bytes]
Offset 14: [HTTP/2 Frame Payload: N bytes]
...
Offset N:  [TLS Record Header: 5 bytes]  ← Next TLS record
Offset N+5:[HTTP/2 Frame Header: 9 bytes]
...

The kernel doesn't know about HTTP/2 — it just stores bytes.
The HTTP/2 library (nghttp2, h2, etc.) reads from the socket
and parses frames from the byte stream.
```

### Kernel Syscall Flow for gRPC

```
gRPC SEND PATH:
  app calls:  grpc_channel.unary_call()
              → proto.encode() → grpc_frame_write()
              → TLS.encrypt()
              → write(fd, buf, len)  [syscall]
              → kernel copies buf to TCP send buffer
              → kernel schedules TCP segment transmission
              → NIC DMA sends packet

gRPC RECEIVE PATH:
  NIC receives packet
  → NIC DMA copies to kernel RX ring buffer
  → Hardware interrupt → kernel interrupt handler
  → TCP stack: verify checksum, in-sequence, update ACK
  → TLS: decrypt record
  → Bytes land in TCP recv buffer
  → epoll/kqueue wakes up HTTP/2 library
  → Library calls: read(fd, buf, len)  [syscall]
  → HTTP/2 parser reads frames
  → Dispatches to correct stream
  → gRPC deserializes protobuf
  → Calls your handler function
```

---

## 15. Network Level — Wire Format and Packet Flow

### A Complete gRPC Request on the Wire

Let's trace a single unary gRPC call: `GetUser(user_id: 42)` byte by byte.

**Step 1: TCP 3-Way Handshake**
```
CLIENT → SERVER:  [IP][TCP: SYN, seq=1000]
SERVER → CLIENT:  [IP][TCP: SYN-ACK, seq=2000, ack=1001]
CLIENT → SERVER:  [IP][TCP: ACK, ack=2001]
```

**Step 2: TLS Handshake (abbreviated)**
```
CLIENT → SERVER:  [IP][TCP][TLS: ClientHello, ALPN: h2]
SERVER → CLIENT:  [IP][TCP][TLS: ServerHello, ALPN: h2]
SERVER → CLIENT:  [IP][TCP][TLS: Certificate, ServerHelloDone]
CLIENT → SERVER:  [IP][TCP][TLS: ClientKeyExchange, Finished]
SERVER → CLIENT:  [IP][TCP][TLS: Finished]
```

**Step 3: HTTP/2 Connection Preface**
```
CLIENT → SERVER:  [IP][TCP][TLS: "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"]
CLIENT → SERVER:  [IP][TCP][TLS: SETTINGS frame]
SERVER → CLIENT:  [IP][TCP][TLS: SETTINGS frame]
CLIENT → SERVER:  [IP][TCP][TLS: SETTINGS ACK]
SERVER → CLIENT:  [IP][TCP][TLS: SETTINGS ACK]
```

**Step 4: gRPC Request**
```
CLIENT → SERVER:  [IP][TCP][TLS][HTTP/2 HEADERS frame, Stream 1]
  HTTP/2 header bytes (9):
    00 00 XX   ← length of HPACK block
    01         ← Type: HEADERS
    04         ← Flags: END_HEADERS
    00 00 00 01 ← Stream ID: 1
  HPACK bytes:
    83         ← Index 3: :method = POST
    87         ← Index 7: :scheme = https
    84         ← Index 4: :path = / (+ literal: /UserService/GetUser)
    ... (HPACK-encoded headers)

CLIENT → SERVER:  [IP][TCP][TLS][HTTP/2 DATA frame, Stream 1]
  HTTP/2 header bytes (9):
    00 00 09   ← length = 9 (4 grpc header + 5 proto bytes)
    00         ← Type: DATA
    01         ← Flags: END_STREAM
    00 00 00 01 ← Stream ID: 1
  gRPC message framing (5 bytes):
    00         ← Not compressed
    00 00 00 04 ← Message length = 4 bytes
  Protobuf bytes (4 bytes):
    08 2A      ← field 1 (user_id), varint 42
```

**Step 5: gRPC Response**
```
SERVER → CLIENT:  [IP][TCP][TLS][HTTP/2 HEADERS frame, Stream 1]
  :status = 200
  content-type = application/grpc

SERVER → CLIENT:  [IP][TCP][TLS][HTTP/2 DATA frame, Stream 1]
  [grpc framing][protobuf bytes of User message]

SERVER → CLIENT:  [IP][TCP][TLS][HTTP/2 HEADERS frame, Stream 1, END_STREAM]
  grpc-status = 0
  grpc-message = (empty)
```

### Packet Size Breakdown

```
For a typical gRPC GetUser request:

Layer               Bytes    Cumulative
──────────────────  ───────  ──────────
Ethernet header     14       14
IP header           20       34
TCP header          20-60    54-94
TLS record header   5        59-99
HTTP/2 frame hdr    9        68-108
HPACK headers       ~30      98-138
gRPC msg framing    5        103-143
Protobuf payload    ~10      113-153

Total: ~153 bytes for a tiny request.
Compare: JSON REST equivalent might be 600+ bytes.
```

### TCP Segment Anatomy

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├───────────────────────────┬──────────────────────────────────────┤
│       Source Port         │        Destination Port              │
├──────────────────────────────────────────────────────────────────┤
│                      Sequence Number                              │
├──────────────────────────────────────────────────────────────────┤
│                   Acknowledgment Number                           │
├──────┬────────┬─┬─┬─┬─┬─┬─┬─┬─┬───────────────────────────────┤
│ Offs │Reservd │C│E│U│A│P│R│S│F│         Window Size            │
│  set │        │W│C│R│C│S│S│Y│I│                                │
│      │        │R│E│G│K│H│T│N│N│                                │
├──────┴────────┴─┴─┴─┴─┴─┴─┴─┴─┴───────────────────────────────┤
│           Checksum          │        Urgent Pointer             │
├──────────────────────────────────────────────────────────────────┤
│                    Options (if Data Offset > 5)                   │
├──────────────────────────────────────────────────────────────────┤
│                         Data (payload)                            │
└──────────────────────────────────────────────────────────────────┘

Key fields for HTTP/2:
  Window Size: TCP-level flow control (separate from HTTP/2 flow control)
  PSH flag:    Tells receiver to pass data to app immediately
  ACK flag:    Acknowledges received bytes
```

---

## 16. Complete C Implementation

The C implementation uses `nghttp2` (the reference HTTP/2 C library) to demonstrate the raw framing layer.

### Install Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install libnghttp2-dev libssl-dev

# macOS
brew install nghttp2 openssl
```

### proto/user.proto

```protobuf
syntax = "proto3";
package user;

service UserService {
  rpc GetUser (UserRequest) returns (UserResponse);
  rpc ListUsers (ListRequest) returns (stream UserResponse);
  rpc UploadUsers (stream UserRequest) returns (UploadResponse);
  rpc Chat (stream ChatMessage) returns (stream ChatMessage);
}

message UserRequest {
  uint64 user_id = 1;
}

message UserResponse {
  uint64 user_id = 1;
  string name = 2;
  string email = 3;
}

message ListRequest {
  uint32 page_size = 1;
}

message UploadResponse {
  uint32 count = 1;
}

message ChatMessage {
  string sender = 1;
  string text = 2;
}
```

### http2_utils.h

```c
#ifndef HTTP2_UTILS_H
#define HTTP2_UTILS_H

#include <stdint.h>
#include <stddef.h>

/* gRPC message prefix: 1 byte compressed flag + 4 bytes message length */
#define GRPC_HEADER_SIZE 5

/*
 * grpc_encode_message - Encodes a protobuf message with gRPC length prefix.
 *
 * The gRPC wire format for a message:
 *   [0]: Compressed-Flag (0 = not compressed)
 *   [1-4]: Message-Length (big-endian uint32)
 *   [5..]: Protobuf bytes
 *
 * @out:      Output buffer (caller allocates: msg_len + GRPC_HEADER_SIZE)
 * @msg:      Raw protobuf bytes
 * @msg_len:  Length of protobuf bytes
 */
static inline void grpc_encode_message(uint8_t *out,
                                        const uint8_t *msg,
                                        uint32_t msg_len) {
    out[0] = 0; /* not compressed */
    out[1] = (msg_len >> 24) & 0xFF;
    out[2] = (msg_len >> 16) & 0xFF;
    out[3] = (msg_len >> 8)  & 0xFF;
    out[4] = (msg_len)       & 0xFF;
    if (msg && msg_len > 0) {
        memcpy(out + GRPC_HEADER_SIZE, msg, msg_len);
    }
}

/*
 * grpc_decode_message - Decodes gRPC length prefix from buffer.
 *
 * @buf:       Buffer starting at gRPC header
 * @buf_len:   Total buffer length
 * @compressed: Output: 1 if compressed, 0 if not
 * @msg_len:   Output: length of the message that follows
 *
 * Returns: 0 on success, -1 on error (buffer too short)
 */
static inline int grpc_decode_message(const uint8_t *buf,
                                       size_t buf_len,
                                       int *compressed,
                                       uint32_t *msg_len) {
    if (buf_len < GRPC_HEADER_SIZE) return -1;
    *compressed = buf[0];
    *msg_len = ((uint32_t)buf[1] << 24)
             | ((uint32_t)buf[2] << 16)
             | ((uint32_t)buf[3] << 8)
             | ((uint32_t)buf[4]);
    return 0;
}

/* Manually encode a tiny protobuf message (field 1, varint) */
static inline int proto_encode_user_request(uint8_t *buf,
                                              size_t buf_size,
                                              uint64_t user_id) {
    if (buf_size < 2) return -1;
    /* Field 1, wire type 0 (varint): tag = (1 << 3) | 0 = 0x08 */
    int pos = 0;
    buf[pos++] = 0x08;
    /* Encode user_id as varint */
    while (user_id > 0x7F) {
        buf[pos++] = (uint8_t)((user_id & 0x7F) | 0x80);
        user_id >>= 7;
    }
    buf[pos++] = (uint8_t)(user_id);
    return pos;
}

#endif /* HTTP2_UTILS_H */
```

### grpc_client.c

```c
/*
 * grpc_client.c
 *
 * Demonstrates HTTP/2 multiplexing at the raw frame level using nghttp2.
 * Sends multiple concurrent gRPC streams over a single TCP connection.
 *
 * Compile:
 *   gcc -o grpc_client grpc_client.c \
 *       -lnghttp2 -lssl -lcrypto -lpthread -O2 -g
 *
 * Run:
 *   ./grpc_client localhost 50051
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netdb.h>
#include <netinet/tcp.h>    /* TCP_NODELAY */
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <nghttp2/nghttp2.h>

#include "http2_utils.h"

#define MAX_EVENTS     64
#define RECV_BUF_SIZE  65536
#define MAX_STREAMS    100

/* ─────────────────────────────────────────────────────────────────────────
 * Connection State
 * ─────────────────────────────────────────────────────────────────────────
 */
typedef struct {
    int          fd;            /* TCP socket file descriptor           */
    SSL_CTX     *ssl_ctx;       /* OpenSSL context                      */
    SSL         *ssl;           /* OpenSSL connection                   */
    nghttp2_session *session;   /* nghttp2 session (HTTP/2 state)       */
    int          epoll_fd;      /* epoll file descriptor                */
    int          done;          /* Set to 1 when all streams complete   */
    int          stream_count;  /* Number of active streams             */
} http2_conn_t;

/* ─────────────────────────────────────────────────────────────────────────
 * Stream State
 * ─────────────────────────────────────────────────────────────────────────
 */
typedef struct {
    int32_t  stream_id;
    int      complete;
    uint8_t  response_buf[4096];
    size_t   response_len;
} stream_state_t;

static stream_state_t streams[MAX_STREAMS];
static int            stream_map_size = 0;

static stream_state_t *find_stream(int32_t stream_id) {
    for (int i = 0; i < stream_map_size; i++) {
        if (streams[i].stream_id == stream_id) return &streams[i];
    }
    return NULL;
}

static stream_state_t *alloc_stream(int32_t stream_id) {
    if (stream_map_size >= MAX_STREAMS) return NULL;
    stream_state_t *s = &streams[stream_map_size++];
    memset(s, 0, sizeof(*s));
    s->stream_id = stream_id;
    return s;
}

/* ─────────────────────────────────────────────────────────────────────────
 * nghttp2 Callbacks
 *
 * nghttp2 is a callback-driven library. You register callbacks,
 * then feed it data. It calls your callbacks for each event.
 * ─────────────────────────────────────────────────────────────────────────
 */

/*
 * send_callback - Called by nghttp2 when it wants to write data.
 * We write to the SSL (TLS) layer.
 */
static ssize_t send_callback(nghttp2_session *session,
                               const uint8_t *data, size_t length,
                               int flags, void *user_data) {
    (void)session; (void)flags;
    http2_conn_t *conn = (http2_conn_t *)user_data;
    int rv = SSL_write(conn->ssl, data, (int)length);
    if (rv <= 0) {
        int err = SSL_get_error(conn->ssl, rv);
        if (err == SSL_ERROR_WANT_WRITE || err == SSL_ERROR_WANT_READ) {
            return NGHTTP2_ERR_WOULDBLOCK;
        }
        return NGHTTP2_ERR_CALLBACK_FAILURE;
    }
    return rv;
}

/*
 * on_frame_recv_callback - Called for every complete HTTP/2 frame received.
 * This is where we track stream completion.
 */
static int on_frame_recv_callback(nghttp2_session *session,
                                   const nghttp2_frame *frame,
                                   void *user_data) {
    (void)session;
    http2_conn_t *conn = (http2_conn_t *)user_data;

    printf("[FRAME RECV] type=0x%02X stream_id=%d flags=0x%02X\n",
           frame->hd.type, frame->hd.stream_id, frame->hd.flags);

    /* Check for END_STREAM on DATA or HEADERS frames */
    if (frame->hd.flags & NGHTTP2_FLAG_END_STREAM) {
        stream_state_t *s = find_stream(frame->hd.stream_id);
        if (s) {
            s->complete = 1;
            conn->stream_count--;
            printf("[STREAM %d] Complete. Remaining: %d\n",
                   frame->hd.stream_id, conn->stream_count);
            if (conn->stream_count <= 0) {
                conn->done = 1;
            }
        }
    }
    return 0;
}

/*
 * on_data_chunk_recv_callback - Called when DATA frame payload arrives.
 * For gRPC, this contains the length-prefixed protobuf response.
 */
static int on_data_chunk_recv_callback(nghttp2_session *session,
                                        uint8_t flags, int32_t stream_id,
                                        const uint8_t *data, size_t len,
                                        void *user_data) {
    (void)session; (void)flags; (void)user_data;

    stream_state_t *s = find_stream(stream_id);
    if (!s) return 0;

    /* Accumulate response data */
    size_t copy = len;
    if (s->response_len + copy > sizeof(s->response_buf)) {
        copy = sizeof(s->response_buf) - s->response_len;
    }
    memcpy(s->response_buf + s->response_len, data, copy);
    s->response_len += copy;

    /* Parse gRPC message framing */
    if (s->response_len >= GRPC_HEADER_SIZE) {
        int compressed;
        uint32_t msg_len;
        grpc_decode_message(s->response_buf, s->response_len,
                            &compressed, &msg_len);
        printf("[STREAM %d] gRPC response: compressed=%d msg_len=%u\n",
               stream_id, compressed, msg_len);

        /* Print raw protobuf bytes (in real code, decode with protobuf lib) */
        if (s->response_len >= GRPC_HEADER_SIZE + msg_len) {
            printf("[STREAM %d] Proto bytes: ", stream_id);
            for (uint32_t i = 0; i < msg_len && i < 32; i++) {
                printf("%02X ", s->response_buf[GRPC_HEADER_SIZE + i]);
            }
            printf("\n");
        }
    }
    return 0;
}

/*
 * on_header_callback - Called for each decoded HTTP/2 header.
 * Headers are decoded from HPACK format one by one.
 */
static int on_header_callback(nghttp2_session *session,
                               const nghttp2_frame *frame,
                               const uint8_t *name, size_t namelen,
                               const uint8_t *value, size_t valuelen,
                               uint8_t flags, void *user_data) {
    (void)session; (void)frame; (void)flags; (void)user_data;
    printf("[HEADER] stream=%d %.*s: %.*s\n",
           frame->hd.stream_id,
           (int)namelen, name,
           (int)valuelen, value);
    return 0;
}

/*
 * on_stream_close_callback - Called when a stream is fully closed.
 */
static int on_stream_close_callback(nghttp2_session *session,
                                     int32_t stream_id,
                                     uint32_t error_code,
                                     void *user_data) {
    (void)session; (void)user_data;
    printf("[STREAM %d] Closed. Error code: %u\n", stream_id, error_code);
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * TLS Setup
 * ─────────────────────────────────────────────────────────────────────────
 */

/*
 * alpn_select_proto_cb - OpenSSL ALPN negotiation callback (server side).
 * For client, we set ALPN in SSL_CTX_set_alpn_protos.
 */
static SSL_CTX *create_ssl_ctx(void) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx) {
        ERR_print_errors_fp(stderr);
        return NULL;
    }

    /* Set ALPN: offer "h2" (HTTP/2) and "http/1.1" as fallback.
     * Format: length-prefixed strings:
     *   \x02h2\x08http/1.1
     */
    static const unsigned char alpn[] = "\x02h2\x08http/1.1";
    SSL_CTX_set_alpn_protos(ctx, alpn, sizeof(alpn) - 1);

    /* For development: skip certificate verification */
    SSL_CTX_set_verify(ctx, SSL_VERIFY_NONE, NULL);

    return ctx;
}

/* ─────────────────────────────────────────────────────────────────────────
 * TCP Connection
 * ─────────────────────────────────────────────────────────────────────────
 */

static int connect_tcp(const char *host, const char *port) {
    struct addrinfo hints = {0};
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    struct addrinfo *res;
    int rv = getaddrinfo(host, port, &hints, &res);
    if (rv != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        return -1;
    }

    int fd = -1;
    for (struct addrinfo *ai = res; ai; ai = ai->ai_next) {
        fd = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (fd < 0) continue;

        /*
         * TCP_NODELAY: Disable Nagle's algorithm.
         *
         * Why critical for gRPC:
         *   Nagle buffers small packets until ACK received.
         *   gRPC sends small WINDOW_UPDATE and PING frames.
         *   Without TCP_NODELAY, these get delayed, causing stalls.
         */
        int flag = 1;
        setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));

        if (connect(fd, ai->ai_addr, ai->ai_addrlen) == 0) {
            printf("[TCP] Connected to %s:%s (fd=%d)\n", host, port, fd);
            break;
        }
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);
    return fd;
}

/* ─────────────────────────────────────────────────────────────────────────
 * HTTP/2 Session Initialization
 * ─────────────────────────────────────────────────────────────────────────
 */

static int init_http2_session(http2_conn_t *conn) {
    /* Register all callbacks */
    nghttp2_session_callbacks *callbacks;
    nghttp2_session_callbacks_new(&callbacks);
    nghttp2_session_callbacks_set_send_callback(callbacks, send_callback);
    nghttp2_session_callbacks_set_on_frame_recv_callback(callbacks, on_frame_recv_callback);
    nghttp2_session_callbacks_set_on_data_chunk_recv_callback(callbacks, on_data_chunk_recv_callback);
    nghttp2_session_callbacks_set_on_header_callback(callbacks, on_header_callback);
    nghttp2_session_callbacks_set_on_stream_close_callback(callbacks, on_stream_close_callback);

    /* Create client session */
    int rv = nghttp2_session_client_new(&conn->session, callbacks, conn);
    nghttp2_session_callbacks_del(callbacks);
    if (rv != 0) {
        fprintf(stderr, "nghttp2_session_client_new: %s\n", nghttp2_strerror(rv));
        return -1;
    }

    /*
     * Send HTTP/2 SETTINGS frame.
     *
     * We configure:
     *   INITIAL_WINDOW_SIZE: 1MB per stream (gRPC recommendation)
     *   MAX_CONCURRENT_STREAMS: 100
     *
     * nghttp2 also sends the 24-byte connection preface automatically.
     */
    nghttp2_settings_entry settings[] = {
        { NGHTTP2_SETTINGS_INITIAL_WINDOW_SIZE, 1 * 1024 * 1024 },
        { NGHTTP2_SETTINGS_MAX_CONCURRENT_STREAMS, 100 },
    };
    rv = nghttp2_submit_settings(conn->session, NGHTTP2_FLAG_NONE,
                                  settings,
                                  sizeof(settings) / sizeof(settings[0]));
    if (rv != 0) {
        fprintf(stderr, "nghttp2_submit_settings: %s\n", nghttp2_strerror(rv));
        return -1;
    }

    /*
     * Send connection-level WINDOW_UPDATE.
     *
     * Default connection window is 65535 bytes.
     * We expand it to 16MB to allow high-throughput streaming.
     * stream_id=0 means connection level.
     */
    rv = nghttp2_submit_window_update(conn->session, NGHTTP2_FLAG_NONE,
                                       0, /* stream_id=0 = connection */
                                       (1 << 24) - 65535); /* delta */
    if (rv != 0) {
        fprintf(stderr, "nghttp2_submit_window_update: %s\n", nghttp2_strerror(rv));
        return -1;
    }

    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Submit a gRPC Request as an HTTP/2 Stream
 * ─────────────────────────────────────────────────────────────────────────
 */

static int32_t submit_grpc_request(http2_conn_t *conn,
                                    const char *path,
                                    const uint8_t *proto_bytes,
                                    size_t proto_len,
                                    const char *host) {
    /*
     * Build HTTP/2 headers for gRPC.
     *
     * nghttp2_nv = name-value pair with flags.
     * NGHTTP2_NV_FLAG_NO_INDEX: Don't add to HPACK dynamic table.
     *   Used for sensitive headers (auth tokens).
     * NGHTTP2_NV_FLAG_NONE: Normal header, can be indexed.
     */
    const nghttp2_nv headers[] = {
        /* Pseudo-headers MUST come first */
        { (uint8_t*)":method",       (uint8_t*)"POST",
          7, 4, NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)":scheme",       (uint8_t*)"https",
          7, 5, NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)":path",         (uint8_t*)path,
          5, strlen(path), NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)":authority",    (uint8_t*)host,
          10, strlen(host), NGHTTP2_NV_FLAG_NONE },
        /* gRPC required headers */
        { (uint8_t*)"content-type",  (uint8_t*)"application/grpc",
          12, 16, NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)"te",            (uint8_t*)"trailers",
          2, 8, NGHTTP2_NV_FLAG_NONE },
        /* gRPC optional: deadline (30 seconds) */
        { (uint8_t*)"grpc-timeout",  (uint8_t*)"30S",
          12, 3, NGHTTP2_NV_FLAG_NONE },
    };
    int nheaders = sizeof(headers) / sizeof(headers[0]);

    /*
     * Prepare gRPC message body: [compressed-flag][length][proto-bytes]
     *
     * For DATA frames, nghttp2 uses a "data provider" — a callback
     * that provides chunks of data on demand.
     */
    uint8_t *grpc_buf = malloc(GRPC_HEADER_SIZE + proto_len);
    if (!grpc_buf) return -1;
    grpc_encode_message(grpc_buf, proto_bytes, (uint32_t)proto_len);

    /*
     * nghttp2_data_provider: Tells nghttp2 how to get the request body.
     *
     * read_callback is called by nghttp2 when it's ready to send data.
     * We use a simple in-memory approach with a source pointer.
     */
    typedef struct {
        const uint8_t *data;
        size_t         len;
        size_t         pos;
    } mem_source_t;

    /*
     * Note: For simplicity, we embed data in the source pointer.
     * In production code, use a proper buffer management system.
     */
    static uint8_t request_body[4096];
    static size_t  request_body_len = 0;
    memcpy(request_body, grpc_buf, GRPC_HEADER_SIZE + proto_len);
    request_body_len = GRPC_HEADER_SIZE + proto_len;
    free(grpc_buf);

    /* Read callback: nghttp2 calls this to get DATA frame payload */
    nghttp2_data_source_read_callback read_cb =
        ^(nghttp2_session *sess, int32_t sid,
          uint8_t *buf, size_t length,
          uint32_t *data_flags,
          nghttp2_data_source *source,
          void *ud) {
        (void)sess; (void)sid; (void)ud;
        size_t *pos_ptr = (size_t *)source->ptr;
        size_t remaining = request_body_len - *pos_ptr;
        size_t copy = remaining < length ? remaining : length;
        memcpy(buf, request_body + *pos_ptr, copy);
        *pos_ptr += copy;
        if (*pos_ptr >= request_body_len) {
            /*
             * NGHTTP2_DATA_FLAG_EOF: Tell nghttp2 this is the last data.
             * nghttp2 will set END_STREAM on the last DATA frame.
             */
            *data_flags |= NGHTTP2_DATA_FLAG_EOF;
        }
        return (ssize_t)copy;
    };

    static size_t body_pos = 0;
    body_pos = 0;

    nghttp2_data_provider data_prd = {
        .source.ptr    = &body_pos,
        .read_callback = read_cb,
    };

    /*
     * nghttp2_submit_request: Queues HEADERS + DATA frames for a new stream.
     *
     * Returns the stream ID assigned (1, 3, 5, ... for client).
     * Frames are not sent immediately — they're queued until
     * nghttp2_session_send() is called.
     */
    int32_t stream_id = nghttp2_submit_request(
        conn->session,
        NULL,        /* priority (NULL = default) */
        headers, nheaders,
        &data_prd,   /* body */
        NULL         /* stream user data */
    );

    if (stream_id < 0) {
        fprintf(stderr, "nghttp2_submit_request: %s\n",
                nghttp2_strerror(stream_id));
        return -1;
    }

    /* Allocate stream tracking state */
    stream_state_t *s = alloc_stream(stream_id);
    if (s) {
        printf("[STREAM %d] Submitted request to %s\n", stream_id, path);
    }
    conn->stream_count++;
    return stream_id;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Event Loop — epoll-based I/O
 *
 * This is the core: reads from socket, feeds nghttp2, sends queued frames.
 * ─────────────────────────────────────────────────────────────────────────
 */

static int event_loop(http2_conn_t *conn) {
    conn->epoll_fd = epoll_create1(0);
    if (conn->epoll_fd < 0) {
        perror("epoll_create1");
        return -1;
    }

    struct epoll_event ev = {
        .events  = EPOLLIN | EPOLLOUT | EPOLLET, /* Edge-triggered */
        .data.fd = conn->fd,
    };
    epoll_ctl(conn->epoll_fd, EPOLL_CTL_ADD, conn->fd, &ev);

    /* Non-blocking socket for epoll */
    int flags = fcntl(conn->fd, F_GETFL, 0);
    fcntl(conn->fd, F_SETFL, flags | O_NONBLOCK);

    uint8_t recv_buf[RECV_BUF_SIZE];
    struct epoll_event events[MAX_EVENTS];

    while (!conn->done) {
        int n = epoll_wait(conn->epoll_fd, events, MAX_EVENTS, 5000);
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("epoll_wait");
            return -1;
        }
        if (n == 0) {
            printf("[TIMEOUT] No events for 5 seconds.\n");
            break;
        }

        for (int i = 0; i < n; i++) {
            if (events[i].events & EPOLLIN) {
                /*
                 * Data available to read from socket.
                 * Read all available data, feed to nghttp2.
                 *
                 * nghttp2_session_mem_recv2: Feed raw bytes to the HTTP/2
                 * state machine. It parses frames and calls our callbacks.
                 */
                for (;;) {
                    ssize_t nread = SSL_read(conn->ssl, recv_buf, sizeof(recv_buf));
                    if (nread <= 0) {
                        int err = SSL_get_error(conn->ssl, (int)nread);
                        if (err == SSL_ERROR_WANT_READ) break;
                        if (err == SSL_ERROR_ZERO_RETURN) {
                            conn->done = 1;
                        }
                        break;
                    }

                    ssize_t rv = nghttp2_session_mem_recv2(
                        conn->session, recv_buf, (size_t)nread);
                    if (rv < 0) {
                        fprintf(stderr, "nghttp2_session_mem_recv2: %s\n",
                                nghttp2_strerror((int)rv));
                        return -1;
                    }
                }
            }

            if (events[i].events & EPOLLOUT) {
                /*
                 * Socket ready to write.
                 *
                 * nghttp2_session_send: Drains nghttp2's internal send queue.
                 * Calls our send_callback (which calls SSL_write) for each
                 * chunk of data it wants to transmit.
                 */
                int rv = nghttp2_session_send(conn->session);
                if (rv != 0) {
                    fprintf(stderr, "nghttp2_session_send: %s\n",
                            nghttp2_strerror(rv));
                    return -1;
                }
            }
        }

        /* Always try to send after processing received data */
        if (nghttp2_session_want_write(conn->session)) {
            nghttp2_session_send(conn->session);
        }
    }
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Main: Demonstrate Multiplexing — Multiple Concurrent Streams
 * ─────────────────────────────────────────────────────────────────────────
 */

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <host> <port>\n", argv[0]);
        return 1;
    }
    const char *host = argv[1];
    const char *port = argv[2];

    /* Initialize OpenSSL */
    SSL_library_init();
    OpenSSL_add_all_algorithms();
    SSL_load_error_strings();

    http2_conn_t conn = {0};

    /* Step 1: TCP connect */
    conn.fd = connect_tcp(host, port);
    if (conn.fd < 0) return 1;

    /* Step 2: TLS handshake with ALPN */
    conn.ssl_ctx = create_ssl_ctx();
    conn.ssl     = SSL_new(conn.ssl_ctx);
    SSL_set_fd(conn.ssl, conn.fd);

    /* SNI (Server Name Indication) */
    SSL_set_tlsext_host_name(conn.ssl, host);

    if (SSL_connect(conn.ssl) != 1) {
        ERR_print_errors_fp(stderr);
        return 1;
    }

    /* Verify ALPN negotiated h2 */
    const unsigned char *proto;
    unsigned int proto_len;
    SSL_get0_alpn_selected(conn.ssl, &proto, &proto_len);
    if (!proto || proto_len != 2 || memcmp(proto, "h2", 2) != 0) {
        fprintf(stderr, "ALPN did not negotiate h2. Got: %.*s\n",
                proto_len, proto ? (char*)proto : "(none)");
        return 1;
    }
    printf("[TLS] ALPN negotiated: h2\n");

    /* Step 3: Initialize HTTP/2 session */
    if (init_http2_session(&conn) < 0) return 1;

    /*
     * Step 4: Submit MULTIPLE concurrent gRPC requests.
     *
     * This is the multiplexing demonstration:
     * All three requests are submitted before the event loop runs.
     * nghttp2 queues them as separate streams (IDs: 1, 3, 5).
     * They will be sent as interleaved frames over ONE TCP connection.
     */

    /* Request 1: GetUser for user_id=1 */
    uint8_t req1_proto[16];
    int req1_len = proto_encode_user_request(req1_proto, sizeof(req1_proto), 1);
    submit_grpc_request(&conn, "/user.UserService/GetUser",
                         req1_proto, req1_len, host);

    /* Request 2: GetUser for user_id=2 */
    uint8_t req2_proto[16];
    int req2_len = proto_encode_user_request(req2_proto, sizeof(req2_proto), 2);
    submit_grpc_request(&conn, "/user.UserService/GetUser",
                         req2_proto, req2_len, host);

    /* Request 3: GetUser for user_id=3 */
    uint8_t req3_proto[16];
    int req3_len = proto_encode_user_request(req3_proto, sizeof(req3_proto), 3);
    submit_grpc_request(&conn, "/user.UserService/GetUser",
                         req3_proto, req3_len, host);

    printf("\n[MULTIPLEXING] 3 streams submitted concurrently on 1 TCP connection\n");
    printf("[MULTIPLEXING] Stream IDs: 1, 3, 5 (client uses odd numbers)\n\n");

    /* Step 5: Run event loop */
    event_loop(&conn);

    /* Cleanup */
    nghttp2_session_del(conn.session);
    SSL_shutdown(conn.ssl);
    SSL_free(conn.ssl);
    SSL_CTX_free(conn.ssl_ctx);
    close(conn.fd);
    close(conn.epoll_fd);

    printf("\n[DONE] All streams completed.\n");
    return 0;
}
```

### grpc_server.c

```c
/*
 * grpc_server.c
 *
 * Minimal HTTP/2 / gRPC server using nghttp2.
 * Demonstrates server-side stream handling and multiplexing.
 *
 * Compile:
 *   gcc -o grpc_server grpc_server.c \
 *       -lnghttp2 -lssl -lcrypto -lpthread -O2 -g
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <nghttp2/nghttp2.h>

#include "http2_utils.h"

#define LISTEN_PORT  50051
#define BACKLOG      128

typedef struct {
    int              fd;
    SSL             *ssl;
    nghttp2_session *session;
} server_conn_t;

/* ─────────────────────────────────────────────────────────────────────────
 * Server-side nghttp2 Callbacks
 * ─────────────────────────────────────────────────────────────────────────
 */

static ssize_t server_send_callback(nghttp2_session *session,
                                     const uint8_t *data, size_t length,
                                     int flags, void *user_data) {
    (void)session; (void)flags;
    server_conn_t *conn = (server_conn_t *)user_data;
    int rv = SSL_write(conn->ssl, data, (int)length);
    if (rv <= 0) return NGHTTP2_ERR_CALLBACK_FAILURE;
    return rv;
}

/*
 * on_request_recv - Called when a complete request has been received.
 * We send a synthetic gRPC response.
 *
 * In a real server, this would: decode protobuf, call handler, encode response.
 */
static void send_grpc_response(server_conn_t *conn, int32_t stream_id,
                                 const char *name, const char *email) {
    /*
     * Step 1: Send response HEADERS frame.
     *
     * gRPC response must have:
     *   :status = 200
     *   content-type = application/grpc
     */
    const nghttp2_nv resp_headers[] = {
        { (uint8_t*)":status",      (uint8_t*)"200",
          7, 3, NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)"content-type", (uint8_t*)"application/grpc",
          12, 16, NGHTTP2_NV_FLAG_NONE },
    };
    nghttp2_submit_headers(conn->session,
                            NGHTTP2_FLAG_NONE,
                            stream_id,
                            NULL,
                            resp_headers, 2,
                            NULL);

    /*
     * Step 2: Build protobuf response manually.
     *
     * UserResponse { user_id: 42, name: "Alice", email: "alice@x.com" }
     *
     * Protobuf encoding (simplified):
     *   field 1 (user_id), varint: 08 2A
     *   field 2 (name), length-delimited: 12 05 "Alice"
     *   field 3 (email), length-delimited: 1A 0B "alice@x.com"
     */
    uint8_t proto_resp[256];
    int pos = 0;

    /* field 1: user_id = 42 */
    proto_resp[pos++] = 0x08; /* tag: field 1, varint */
    proto_resp[pos++] = 42;

    /* field 2: name */
    proto_resp[pos++] = 0x12; /* tag: field 2, length-delimited */
    proto_resp[pos++] = (uint8_t)strlen(name);
    memcpy(proto_resp + pos, name, strlen(name));
    pos += strlen(name);

    /* field 3: email */
    proto_resp[pos++] = 0x1A; /* tag: field 3, length-delimited */
    proto_resp[pos++] = (uint8_t)strlen(email);
    memcpy(proto_resp + pos, email, strlen(email));
    pos += strlen(email);

    /* gRPC frame = [flag][length][proto_bytes] */
    uint8_t grpc_body[256 + GRPC_HEADER_SIZE];
    grpc_encode_message(grpc_body, proto_resp, pos);
    size_t grpc_body_len = GRPC_HEADER_SIZE + pos;

    /*
     * Step 3: Send DATA frame with gRPC message.
     */
    static uint8_t data_buf[512];
    static size_t  data_len, data_pos;
    memcpy(data_buf, grpc_body, grpc_body_len);
    data_len = grpc_body_len;
    data_pos = 0;

    nghttp2_data_source_read_callback read_cb =
        ^(nghttp2_session *sess, int32_t sid,
          uint8_t *buf, size_t length, uint32_t *data_flags,
          nghttp2_data_source *source, void *ud) {
        (void)sess; (void)sid; (void)ud; (void)source;
        size_t remaining = data_len - data_pos;
        size_t copy = remaining < length ? remaining : length;
        memcpy(buf, data_buf + data_pos, copy);
        data_pos += copy;
        if (data_pos >= data_len) *data_flags |= NGHTTP2_DATA_FLAG_EOF;
        return (ssize_t)copy;
    };

    nghttp2_data_provider data_prd = {
        .read_callback = read_cb,
    };
    nghttp2_submit_data(conn->session, NGHTTP2_FLAG_NONE,
                         stream_id, &data_prd);

    /*
     * Step 4: Send trailers (gRPC status).
     *
     * gRPC status is sent as HTTP/2 trailers — HEADERS with END_STREAM.
     * This signals the end of the gRPC call.
     *
     * grpc-status = 0 means OK.
     */
    const nghttp2_nv trailers[] = {
        { (uint8_t*)"grpc-status",  (uint8_t*)"0",
          11, 1, NGHTTP2_NV_FLAG_NONE },
        { (uint8_t*)"grpc-message", (uint8_t*)"",
          12, 0, NGHTTP2_NV_FLAG_NONE },
    };
    nghttp2_submit_headers(conn->session,
                            NGHTTP2_FLAG_END_STREAM, /* END_STREAM = trailers */
                            stream_id,
                            NULL,
                            trailers, 2,
                            NULL);

    printf("[SERVER] Sent response on stream %d\n", stream_id);
}

static int server_on_frame_recv(nghttp2_session *session,
                                 const nghttp2_frame *frame,
                                 void *user_data) {
    server_conn_t *conn = (server_conn_t *)user_data;

    /* When client sends END_STREAM on DATA frame, the request is complete */
    if (frame->hd.type == NGHTTP2_DATA &&
        frame->hd.flags & NGHTTP2_FLAG_END_STREAM) {
        send_grpc_response(conn, frame->hd.stream_id, "Alice", "alice@example.com");
        nghttp2_session_send(conn->session);
    }

    /* HEADERS with END_STREAM = GET-style request (no body) */
    if (frame->hd.type == NGHTTP2_HEADERS &&
        frame->hd.flags & NGHTTP2_FLAG_END_STREAM) {
        send_grpc_response(conn, frame->hd.stream_id, "Bob", "bob@example.com");
        nghttp2_session_send(conn->session);
    }

    return 0;
}

static int server_on_begin_headers(nghttp2_session *session,
                                    const nghttp2_frame *frame,
                                    void *user_data) {
    (void)session; (void)user_data;
    if (frame->hd.type == NGHTTP2_HEADERS &&
        frame->headers.cat == NGHTTP2_HCAT_REQUEST) {
        printf("[SERVER] New request on stream %d\n", frame->hd.stream_id);
    }
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * TLS Server Setup
 * ─────────────────────────────────────────────────────────────────────────
 */

static SSL_CTX *create_server_ssl_ctx(const char *cert, const char *key) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());
    if (!ctx) return NULL;

    /* ALPN: Advertise h2 support */
    SSL_CTX_set_alpn_select_cb(ctx,
        ^(SSL *ssl, const unsigned char **out, unsigned char *outlen,
          const unsigned char *in, unsigned int inlen, void *arg) {
        (void)ssl; (void)arg;
        /* nghttp2 helper: selects h2 from client's ALPN list */
        int rv = nghttp2_select_next_protocol(
            (unsigned char **)out, outlen, in, inlen);
        if (rv <= 0) return SSL_TLSEXT_ERR_NOACK;
        return SSL_TLSEXT_ERR_OK;
    }, NULL);

    SSL_CTX_use_certificate_file(ctx, cert, SSL_FILETYPE_PEM);
    SSL_CTX_use_PrivateKey_file(ctx, key, SSL_FILETYPE_PEM);

    return ctx;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Handle One Client Connection
 * ─────────────────────────────────────────────────────────────────────────
 */

static void handle_client(int client_fd, SSL_CTX *ssl_ctx) {
    /* Set TCP_NODELAY on accepted socket */
    int flag = 1;
    setsockopt(client_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));

    server_conn_t conn = {.fd = client_fd};

    /* TLS accept */
    conn.ssl = SSL_new(ssl_ctx);
    SSL_set_fd(conn.ssl, client_fd);
    if (SSL_accept(conn.ssl) != 1) {
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }

    /* Initialize server-side HTTP/2 session */
    nghttp2_session_callbacks *callbacks;
    nghttp2_session_callbacks_new(&callbacks);
    nghttp2_session_callbacks_set_send_callback(callbacks, server_send_callback);
    nghttp2_session_callbacks_set_on_frame_recv_callback(callbacks, server_on_frame_recv);
    nghttp2_session_callbacks_set_on_begin_headers_callback(callbacks, server_on_begin_headers);
    nghttp2_session_server_new(&conn.session, callbacks, &conn);
    nghttp2_session_callbacks_del(callbacks);

    /* Send server SETTINGS */
    nghttp2_settings_entry settings[] = {
        { NGHTTP2_SETTINGS_MAX_CONCURRENT_STREAMS, 100 },
        { NGHTTP2_SETTINGS_INITIAL_WINDOW_SIZE, 1024 * 1024 },
    };
    nghttp2_submit_settings(conn.session, NGHTTP2_FLAG_NONE,
                             settings, 2);
    nghttp2_session_send(conn.session);

    /* Read-process loop */
    uint8_t buf[65536];
    for (;;) {
        ssize_t nread = SSL_read(conn.ssl, buf, sizeof(buf));
        if (nread <= 0) break;

        ssize_t rv = nghttp2_session_mem_recv2(conn.session, buf, nread);
        if (rv < 0) break;

        nghttp2_session_send(conn.session);

        if (!nghttp2_session_want_read(conn.session) &&
            !nghttp2_session_want_write(conn.session)) break;
    }

    nghttp2_session_del(conn.session);

cleanup:
    SSL_shutdown(conn.ssl);
    SSL_free(conn.ssl);
    close(client_fd);
}

int main(void) {
    SSL_library_init();
    OpenSSL_add_all_algorithms();
    SSL_load_error_strings();

    /* For demo: generate a self-signed cert with:
     *   openssl req -x509 -newkey rsa:4096 -keyout key.pem \
     *     -out cert.pem -days 365 -nodes -subj '/CN=localhost'
     */
    SSL_CTX *ssl_ctx = create_server_ssl_ctx("cert.pem", "key.pem");
    if (!ssl_ctx) {
        fprintf(stderr, "Failed to create SSL context\n");
        return 1;
    }

    /* Listen socket */
    int server_fd = socket(AF_INET6, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt));

    struct sockaddr_in6 addr = {
        .sin6_family = AF_INET6,
        .sin6_port   = htons(LISTEN_PORT),
        .sin6_addr   = in6addr_any,
    };
    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, BACKLOG);

    printf("[SERVER] Listening on port %d\n", LISTEN_PORT);

    for (;;) {
        struct sockaddr_in6 client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd,
                                (struct sockaddr *)&client_addr,
                                &client_len);
        if (client_fd < 0) continue;

        printf("[SERVER] Accepted connection\n");
        handle_client(client_fd, ssl_ctx);
    }

    SSL_CTX_free(ssl_ctx);
    close(server_fd);
    return 0;
}
```

---

## 17. Complete Rust Implementation (Tonic)

### Cargo.toml

```toml
[package]
name = "grpc-http2-demo"
version = "0.1.0"
edition = "2021"

[dependencies]
tonic          = { version = "0.12", features = ["tls"] }
prost          = "0.13"
tokio          = { version = "1", features = ["full"] }
tokio-stream   = "0.1"
futures        = "0.3"
tower          = "0.4"
h2             = "0.4"    # Direct HTTP/2 library (tonic uses this internally)
bytes          = "1"
tracing        = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[build-dependencies]
tonic-build = "0.12"
```

### build.rs

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile(
            &["proto/user.proto"],
            &["proto/"],
        )?;
    Ok(())
}
```

### src/server.rs

```rust
//! gRPC Server with all four streaming patterns.
//!
//! Architecture: tokio (async runtime) → tonic (gRPC) → h2 (HTTP/2) → TCP.
//!
//! Each gRPC stream maps to an h2::server::SendResponse/RecvStream pair.
//! Tonic wraps these in higher-level stream types.

use std::pin::Pin;
use std::net::SocketAddr;
use tokio::sync::mpsc;
use tokio_stream::{wrappers::ReceiverStream, Stream, StreamExt};
use tonic::{transport::Server, Request, Response, Status, Streaming};
use tracing::{info, instrument};

// Generated code from proto/user.proto
pub mod user {
    tonic::include_proto!("user");
}

use user::{
    user_service_server::{UserService, UserServiceServer},
    ChatMessage, ListRequest, UploadResponse, UserRequest, UserResponse,
};

/// Our service implementation
#[derive(Debug, Default)]
pub struct UserServiceImpl;

/// Type alias for server-streaming responses.
/// Pin<Box<dyn Stream<...> + Send>> is the standard tonic pattern.
type ResponseStream<T> = Pin<Box<dyn Stream<Item = Result<T, Status>> + Send>>;

#[tonic::async_trait]
impl UserService for UserServiceImpl {
    // ─────────────────────────────────────────────────────────────────────
    // Pattern 1: Unary RPC
    //
    // HTTP/2 mapping:
    //   Client → [HEADERS][DATA + END_STREAM]
    //   Server → [HEADERS][DATA][HEADERS + END_STREAM (trailers)]
    // ─────────────────────────────────────────────────────────────────────
    #[instrument(skip_all)]
    async fn get_user(
        &self,
        request: Request<UserRequest>,
    ) -> Result<Response<UserResponse>, Status> {
        // tonic extracts HTTP/2 metadata (custom headers) here
        let metadata = request.metadata();
        info!("GetUser called. Metadata keys: {}", metadata.len());

        // The actual gRPC request payload (decoded from protobuf)
        let req = request.into_inner();
        info!("GetUser user_id={}", req.user_id);

        // Simulate database lookup
        if req.user_id == 0 {
            // tonic translates this to:
            //   HTTP/2 trailers: grpc-status=3, grpc-message="user_id required"
            return Err(Status::invalid_argument("user_id must be non-zero"));
        }

        let response = UserResponse {
            user_id: req.user_id,
            name: format!("User-{}", req.user_id),
            email: format!("user{}@example.com", req.user_id),
        };

        Ok(Response::new(response))
    }

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 2: Server Streaming RPC
    //
    // HTTP/2 mapping:
    //   Client → [HEADERS + END_STREAM] (request has no body in this case,
    //             END_STREAM on HEADERS means no DATA frames follow)
    //   Server → [HEADERS][DATA][DATA]...[DATA + END_STREAM][HEADERS(trailers)]
    //
    // The server sends multiple UserResponse messages on the SAME stream.
    // Each message = one DATA frame (or multiple for large messages).
    // ─────────────────────────────────────────────────────────────────────
    type ListUsersStream = ResponseStream<UserResponse>;

    #[instrument(skip_all)]
    async fn list_users(
        &self,
        request: Request<ListRequest>,
    ) -> Result<Response<Self::ListUsersStream>, Status> {
        let page_size = request.into_inner().page_size as u64;
        let page_size = if page_size == 0 { 10 } else { page_size };

        info!("ListUsers streaming {} users", page_size);

        // Create a channel: handler sends UserResponse, stream receives them.
        // This is the idiomatic Rust pattern for server streaming.
        //
        // Under the hood:
        //   - Each .send() on tx causes tonic to encode the protobuf message
        //   - Wrap it in gRPC length-prefix framing
        //   - Submit it as an HTTP/2 DATA frame on the stream
        let (tx, rx) = mpsc::channel(32);

        tokio::spawn(async move {
            for i in 1..=page_size {
                let user = UserResponse {
                    user_id: i,
                    name: format!("User-{}", i),
                    email: format!("user{}@example.com", i),
                };

                // Simulate work
                tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

                if tx.send(Ok(user)).await.is_err() {
                    // Client disconnected — RST_STREAM frame received
                    info!("Client cancelled stream at user {}", i);
                    break;
                }

                info!("Streamed user {}/{}", i, page_size);
            }
            // When tx is dropped, the stream ends.
            // tonic sends: last DATA frame (or empty DATA with END_STREAM)
            // followed by: HEADERS frame with grpc-status=0 (trailers)
        });

        // ReceiverStream adapts mpsc::Receiver into a futures::Stream
        let stream = ReceiverStream::new(rx);
        Ok(Response::new(Box::pin(stream)))
    }

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 3: Client Streaming RPC
    //
    // HTTP/2 mapping:
    //   Client → [HEADERS][DATA][DATA]...[DATA + END_STREAM]
    //   Server → [HEADERS][DATA][HEADERS + END_STREAM (trailers)]
    //
    // tonic gives us a Streaming<UserRequest> — an async iterator
    // that yields decoded protobuf messages as the DATA frames arrive.
    // ─────────────────────────────────────────────────────────────────────
    #[instrument(skip_all)]
    async fn upload_users(
        &self,
        request: Request<Streaming<UserRequest>>,
    ) -> Result<Response<UploadResponse>, Status> {
        // Extract the stream from the request
        let mut stream = request.into_inner();
        let mut count = 0u32;

        // Consume the stream: each .next() reads one gRPC message
        // from the incoming HTTP/2 DATA frames.
        while let Some(user_req) = stream.next().await {
            let user_req = user_req?; // propagates gRPC errors
            info!("Received user_id={}", user_req.user_id);
            count += 1;

            // In a real server: persist to database, validate, etc.
        }

        info!("Upload complete: {} users received", count);
        Ok(Response::new(UploadResponse { count }))
    }

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 4: Bidirectional Streaming RPC
    //
    // HTTP/2 mapping:
    //   Client and Server both send DATA frames independently.
    //   Stream is OPEN in both directions until each side sends END_STREAM.
    //
    // This is the most complex pattern — both sides are simultaneously:
    //   - Reading from the incoming HTTP/2 DATA frames
    //   - Writing to the outgoing HTTP/2 DATA frames
    //
    // Flow control applies independently to each direction.
    // ─────────────────────────────────────────────────────────────────────
    type ChatStream = ResponseStream<ChatMessage>;

    #[instrument(skip_all)]
    async fn chat(
        &self,
        request: Request<Streaming<ChatMessage>>,
    ) -> Result<Response<Self::ChatStream>, Status> {
        let mut incoming = request.into_inner();
        let (tx, rx) = mpsc::channel(32);

        tokio::spawn(async move {
            // Process incoming messages and send responses
            while let Some(msg) = incoming.next().await {
                match msg {
                    Ok(chat_msg) => {
                        info!("Received from {}: {}", chat_msg.sender, chat_msg.text);

                        // Echo back with transformation
                        let response = ChatMessage {
                            sender: "server".to_string(),
                            text: format!("Echo: {}", chat_msg.text),
                        };

                        if tx.send(Ok(response)).await.is_err() {
                            break; // Client gone
                        }

                        // Server can also send UNSOLICITED messages
                        // (not a response to any specific client message)
                        let broadcast = ChatMessage {
                            sender: "server-broadcast".to_string(),
                            text: "Server-initiated message".to_string(),
                        };
                        let _ = tx.send(Ok(broadcast)).await;
                    }
                    Err(status) => {
                        info!("Stream error: {}", status);
                        break;
                    }
                }
            }
        });

        Ok(Response::new(Box::pin(ReceiverStream::new(rx))))
    }
}

/// Server entry point.
///
/// Shows how to configure HTTP/2 settings via tonic/hyper.
pub async fn run_server() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;

    info!("gRPC server starting on {}", addr);

    Server::builder()
        // HTTP/2 settings exposed by tonic:
        //
        // initial_connection_window_size: Connection-level flow control window.
        //   Increasing this allows more data in-flight across ALL streams.
        .initial_connection_window_size(Some(4 * 1024 * 1024)) // 4MB
        //
        // initial_stream_window_size: Per-stream flow control window.
        //   Larger = more data per stream before waiting for WINDOW_UPDATE.
        .initial_stream_window_size(Some(1 * 1024 * 1024)) // 1MB
        //
        // max_concurrent_streams: SETTINGS_MAX_CONCURRENT_STREAMS.
        //   Clients exceeding this get RST_STREAM with REFUSED_STREAM.
        .max_concurrent_streams(Some(1000))
        //
        // http2_keepalive_interval: Sends HTTP/2 PING frames to detect dead connections.
        //   More reliable than TCP keepalive for gRPC.
        .http2_keepalive_interval(Some(std::time::Duration::from_secs(10)))
        .http2_keepalive_timeout(Some(std::time::Duration::from_secs(5)))
        //
        // tcp_keepalive: OS-level TCP keepalive (belt AND suspenders approach).
        .tcp_keepalive(Some(std::time::Duration::from_secs(60)))
        //
        // tcp_nodelay: Disable Nagle's algorithm. Critical for gRPC latency.
        .tcp_nodelay(true)
        .add_service(UserServiceServer::new(UserServiceImpl))
        .serve(addr)
        .await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    run_server().await
}
```

### src/client.rs

```rust
//! gRPC Client demonstrating multiplexing: multiple concurrent RPCs
//! over a single HTTP/2 connection.
//!
//! Key insight: tonic reuses ONE channel (one TCP + HTTP/2 connection)
//! for ALL concurrent RPCs. Each RPC gets its own HTTP/2 stream.

use futures::future::join_all;
use tokio::time::{sleep, Duration};
use tokio_stream::StreamExt;
use tonic::transport::Channel;
use tonic::Request;
use tracing::{info, instrument};

pub mod user {
    tonic::include_proto!("user");
}

use user::{
    user_service_client::UserServiceClient,
    ChatMessage, ListRequest, UserRequest,
};

/// Demonstrate all four streaming patterns over one HTTP/2 connection.
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    // ─────────────────────────────────────────────────────────────────────
    // Channel: This is the HTTP/2 connection pool.
    //
    // tonic::transport::Channel maintains a pool of HTTP/2 connections.
    // By default, it uses ONE connection and multiplexes streams over it.
    //
    // Under the hood:
    //   Channel → hyper::client → h2::client → TCP socket
    //
    // All RPCs below share this single Channel.
    // ─────────────────────────────────────────────────────────────────────
    let channel = Channel::from_static("http://[::1]:50051")
        .connect()
        .await?;

    info!("Connected to gRPC server via HTTP/2");

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 1: Concurrent Unary RPCs — True Multiplexing Demo
    //
    // We fire 10 GetUser requests SIMULTANEOUSLY.
    // tonic creates 10 HTTP/2 streams (IDs: 1,3,5,...,19) on ONE connection.
    // Server processes them concurrently and responds to each independently.
    //
    // This is the core multiplexing feature:
    //   10 requests, 1 TCP connection, 10 HTTP/2 streams.
    // ─────────────────────────────────────────────────────────────────────
    info!("\n=== MULTIPLEXING: 10 concurrent unary RPCs ===");

    let futures: Vec<_> = (1u64..=10)
        .map(|user_id| {
            // Each clone() of the channel is cheap — it shares the connection.
            let mut client = UserServiceClient::new(channel.clone());
            async move {
                let request = Request::new(UserRequest { user_id });
                let response = client.get_user(request).await?;
                let user = response.into_inner();
                info!("Got user: id={}, name={}", user.user_id, user.name);
                Ok::<_, tonic::Status>(user)
            }
        })
        .collect();

    // join_all runs all futures concurrently.
    // They all run on the SAME HTTP/2 connection, different streams.
    let results = join_all(futures).await;
    info!("All {} requests completed", results.len());

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 2: Server Streaming
    //
    // HTTP/2 stream stays open. Server sends multiple DATA frames.
    // Client reads them one by one as they arrive.
    // ─────────────────────────────────────────────────────────────────────
    info!("\n=== SERVER STREAMING: ListUsers ===");

    let mut client = UserServiceClient::new(channel.clone());
    let mut stream = client
        .list_users(Request::new(ListRequest { page_size: 5 }))
        .await?
        .into_inner();

    while let Some(user) = stream.next().await {
        let user = user?;
        info!("Streamed user: id={}, name={}", user.user_id, user.name);
    }

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 3: Client Streaming
    //
    // Client sends multiple requests, server responds once.
    // ─────────────────────────────────────────────────────────────────────
    info!("\n=== CLIENT STREAMING: UploadUsers ===");

    let mut client = UserServiceClient::new(channel.clone());

    // Create an async stream of requests to send
    let requests = async_stream::stream! {
        for i in 1u64..=5 {
            sleep(Duration::from_millis(100)).await;
            info!("Uploading user {}", i);
            yield UserRequest { user_id: i };
        }
    };

    let response = client.upload_users(Request::new(requests)).await?;
    info!("Upload complete: {} users", response.into_inner().count);

    // ─────────────────────────────────────────────────────────────────────
    // Pattern 4: Bidirectional Streaming
    //
    // Most powerful pattern: full-duplex communication.
    // Client and server send messages independently.
    // ─────────────────────────────────────────────────────────────────────
    info!("\n=== BIDIRECTIONAL STREAMING: Chat ===");

    let mut client = UserServiceClient::new(channel.clone());

    let outbound = async_stream::stream! {
        let messages = ["Hello!", "How are you?", "Goodbye!"];
        for msg in messages {
            sleep(Duration::from_millis(200)).await;
            yield ChatMessage {
                sender: "client".to_string(),
                text: msg.to_string(),
            };
        }
    };

    let mut response_stream = client
        .chat(Request::new(outbound))
        .await?
        .into_inner();

    while let Some(msg) = response_stream.next().await {
        let msg = msg?;
        info!("Chat response from {}: {}", msg.sender, msg.text);
    }

    info!("\n=== All patterns demonstrated successfully ===");
    Ok(())
}
```

### src/http2_internals.rs

```rust
//! Direct HTTP/2 frame inspection using the `h2` crate.
//!
//! This shows what tonic does internally — raw HTTP/2 frame manipulation.
//! Use this to understand the protocol layer beneath gRPC.

use bytes::Bytes;
use h2::client;
use http::{HeaderMap, Method, Request};
use std::net::SocketAddr;
use tokio::net::TcpStream;
use tracing::info;

/// Sends a raw HTTP/2 request and demonstrates frame-level control.
///
/// h2 is the HTTP/2 implementation that tonic (via hyper) uses.
/// This shows the abstraction level tonic operates at.
pub async fn send_raw_http2_request(
    addr: SocketAddr,
    path: &str,
    body: Bytes,
) -> Result<Bytes, Box<dyn std::error::Error>> {
    // TCP connect (no TLS for simplicity — use h2c)
    let tcp = TcpStream::connect(addr).await?;

    // Disable Nagle at the tokio level
    tcp.set_nodelay(true)?;

    // ─────────────────────────────────────────────────────────────────────
    // HTTP/2 Handshake
    //
    // h2::client::handshake performs:
    //   1. Send the 24-byte HTTP/2 connection preface
    //   2. Send initial SETTINGS frame
    //   3. Receive server SETTINGS frame
    //   4. Send SETTINGS ACK
    //   5. Return (SendRequest, Connection) pair
    //
    // SendRequest: Handle to submit new HTTP/2 streams.
    // Connection:  Drives the HTTP/2 state machine (MUST be polled).
    // ─────────────────────────────────────────────────────────────────────
    let (client, conn) = client::handshake(tcp).await?;

    info!("HTTP/2 handshake complete");

    // The Connection must be driven to completion.
    // It handles: SETTINGS, PING, WINDOW_UPDATE, flow control.
    // Spawn it on a separate task so it runs concurrently.
    tokio::spawn(async move {
        if let Err(e) = conn.await {
            eprintln!("HTTP/2 connection error: {}", e);
        }
    });

    // Wait until ready to send (SETTINGS exchange complete)
    let mut client = client.ready().await?;

    // ─────────────────────────────────────────────────────────────────────
    // Build gRPC/HTTP/2 request headers
    //
    // These become a HEADERS frame on the wire.
    // h2 HPACK-encodes them automatically.
    // ─────────────────────────────────────────────────────────────────────
    let mut request = Request::builder()
        .method(Method::POST)
        .uri(format!("http://{}{}", addr, path))
        .header("content-type", "application/grpc")
        .header("te", "trailers")
        .body(())?;

    // ─────────────────────────────────────────────────────────────────────
    // Send request and get stream handles
    //
    // send_request returns:
    //   send_stream: Write request body (DATA frames)
    //   response:    Future that resolves to the response HEADERS frame
    //
    // end_of_stream=false means we'll send a body after the headers.
    // ─────────────────────────────────────────────────────────────────────
    let (response, mut send_stream) = client.send_request(request, false)?;

    info!("HEADERS frame sent, stream opened");

    // ─────────────────────────────────────────────────────────────────────
    // Send request body as DATA frames
    //
    // reserve_capacity: Requests flow control credits from the receiver.
    //   This maps to HTTP/2 flow control: we can't send until we have credits.
    //
    // send_data: Sends a DATA frame.
    //   end_of_stream=true → sets END_STREAM flag on this DATA frame.
    // ─────────────────────────────────────────────────────────────────────
    send_stream.reserve_capacity(body.len());

    // Wait for flow control credits if needed
    // (connection/stream window must accommodate our data)
    let mut capacity = send_stream.capacity();
    while capacity < body.len() {
        // Wait for WINDOW_UPDATE from server
        tokio::task::yield_now().await;
        capacity = send_stream.capacity();
    }

    // Send the gRPC body as one DATA frame with END_STREAM
    send_stream.send_data(body, true)?;
    info!("DATA frame sent with END_STREAM");

    // ─────────────────────────────────────────────────────────────────────
    // Await response HEADERS frame
    // ─────────────────────────────────────────────────────────────────────
    let (head, mut recv_stream) = response.await?.into_parts();
    info!("Response status: {}", head.status);

    // ─────────────────────────────────────────────────────────────────────
    // Receive response body DATA frames
    //
    // Each recv_stream.data().await reads from the next DATA frame.
    // We must call flow_control().release_capacity() after processing
    // each chunk to send WINDOW_UPDATE back to the server.
    // This is HTTP/2 flow control in action.
    // ─────────────────────────────────────────────────────────────────────
    let mut full_body = bytes::BytesMut::new();

    while let Some(chunk) = recv_stream.data().await {
        let chunk = chunk?;
        let chunk_len = chunk.len();
        info!("Received DATA frame: {} bytes", chunk_len);

        full_body.extend_from_slice(&chunk);

        // CRITICAL: Release flow control capacity.
        // This sends a WINDOW_UPDATE frame to the server.
        // Without this, the server's flow control window shrinks to 0
        // and it stops sending. Flow control deadlock!
        recv_stream
            .flow_control()
            .release_capacity(chunk_len)?;
    }

    // ─────────────────────────────────────────────────────────────────────
    // Read trailers (gRPC status headers)
    //
    // Trailers are a HEADERS frame with END_STREAM flag.
    // h2 delivers them via recv_stream.trailers().
    // ─────────────────────────────────────────────────────────────────────
    if let Some(trailers) = recv_stream.trailers().await? {
        if let Some(status) = trailers.get("grpc-status") {
            info!("gRPC status: {}", status.to_str().unwrap_or("?"));
        }
        if let Some(msg) = trailers.get("grpc-message") {
            let msg = msg.to_str().unwrap_or("");
            if !msg.is_empty() {
                info!("gRPC message: {}", msg);
            }
        }
    }

    Ok(full_body.freeze())
}

/// Demonstrate multiplexing: open N concurrent HTTP/2 streams.
pub async fn demonstrate_multiplexing(
    addr: SocketAddr,
    n: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    let tcp = TcpStream::connect(addr).await?;
    tcp.set_nodelay(true)?;

    let (mut client, conn) = client::handshake(tcp).await?;

    tokio::spawn(async move {
        conn.await.ok();
    });

    client.ready().await?;

    info!("Opening {} concurrent streams on ONE TCP connection", n);

    // Collect all stream handles first (opens all streams simultaneously)
    let mut stream_handles = Vec::new();

    for i in 0..n {
        let request = Request::builder()
            .method(Method::POST)
            .uri(format!("http://{}/user.UserService/GetUser", addr))
            .header("content-type", "application/grpc")
            .header("te", "trailers")
            .body(())?;

        // This submits a HEADERS frame (opens a new HTTP/2 stream)
        // Stream IDs: 1, 3, 5, ..., 2n-1
        let (response, mut send) = client.send_request(request, false)?;

        // Build tiny protobuf: user_id = i+1
        let mut proto = vec![0x08u8]; // field 1, varint
        proto.push((i + 1) as u8);

        // gRPC framing
        let mut grpc_body = vec![0u8, 0, 0, 0, proto.len() as u8];
        grpc_body.extend_from_slice(&proto);

        send.send_data(Bytes::from(grpc_body), true)?;

        info!("Stream {} opened (HTTP/2 stream ID {})", i, 2 * i + 1);
        stream_handles.push(response);
    }

    info!("{} streams opened simultaneously. Awaiting responses...", n);

    // Now await all responses concurrently
    // Each response may arrive in any order — that's multiplexing!
    let responses = futures::future::join_all(stream_handles.into_iter().map(|r| async {
        r.await
    }))
    .await;

    for (i, resp) in responses.into_iter().enumerate() {
        match resp {
            Ok(r) => info!("Stream {} response: status={}", i, r.status()),
            Err(e) => info!("Stream {} error: {}", i, e),
        }
    }

    Ok(())
}
```

---

## 18. Complete Go Implementation

### go.mod

```
module grpc-http2-demo

go 1.22

require (
    google.golang.org/grpc v1.65.0
    google.golang.org/protobuf v1.34.2
    golang.org/x/net v0.27.0
)
```

### proto/user.proto

(Same as defined earlier in the C section)

### Generate:
```bash
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       proto/user.proto
```

### server/main.go

```go
// Package main implements a gRPC server demonstrating all streaming patterns.
//
// Architecture:
//   net.Listener → grpc.Server → http2 (golang.org/x/net/http2) → TCP
//
// gRPC in Go uses golang.org/x/net/http2 for the HTTP/2 layer.
// Each RPC call is a goroutine. Streams are managed by the http2 library.
package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/peer"
	"google.golang.org/grpc/status"

	pb "grpc-http2-demo/proto"
)

// userServer implements all four gRPC patterns.
type userServer struct {
	pb.UnimplementedUserServiceServer
}

// ─────────────────────────────────────────────────────────────────────────────
// Pattern 1: Unary RPC
//
// HTTP/2 event sequence (what happens inside grpc-go):
//
//   1. http2.Server receives HEADERS frame → creates new stream (goroutine)
//   2. http2.Server receives DATA + END_STREAM frame → decodes protobuf
//   3. gRPC middleware runs (auth, logging, tracing interceptors)
//   4. Handler called with decoded request
//   5. Handler returns → gRPC encodes response to protobuf
//   6. http2 sends HEADERS frame (:status=200, content-type=application/grpc)
//   7. http2 sends DATA frame (gRPC length prefix + protobuf bytes)
//   8. http2 sends HEADERS frame (grpc-status=0) with END_STREAM flag
// ─────────────────────────────────────────────────────────────────────────────
func (s *userServer) GetUser(ctx context.Context, req *pb.UserRequest) (*pb.UserResponse, error) {
	// Extract peer information (remote address)
	if p, ok := peer.FromContext(ctx); ok {
		log.Printf("GetUser from %s: user_id=%d", p.Addr, req.UserId)
	}

	// Check context deadline (maps to grpc-timeout header / HTTP/2 stream)
	deadline, ok := ctx.Deadline()
	if ok {
		log.Printf("Deadline: %v remaining", time.Until(deadline))
	}

	if req.UserId == 0 {
		// status.Errorf creates gRPC status error.
		// grpc-go translates this to: grpc-status=3 in the trailers HEADERS frame.
		return nil, status.Errorf(codes.InvalidArgument, "user_id must be non-zero")
	}

	return &pb.UserResponse{
		UserId: req.UserId,
		Name:   fmt.Sprintf("User-%d", req.UserId),
		Email:  fmt.Sprintf("user%d@example.com", req.UserId),
	}, nil
}

// ─────────────────────────────────────────────────────────────────────────────
// Pattern 2: Server Streaming
//
// Key: stream.Send() sends each response as a separate HTTP/2 DATA frame.
// The stream stays OPEN (no END_STREAM) until the handler returns.
// On return: grpc-go sends trailing HEADERS with grpc-status.
// ─────────────────────────────────────────────────────────────────────────────
func (s *userServer) ListUsers(req *pb.ListRequest, stream pb.UserService_ListUsersServer) error {
	pageSize := int(req.PageSize)
	if pageSize == 0 {
		pageSize = 10
	}

	log.Printf("ListUsers: streaming %d users", pageSize)

	for i := 1; i <= pageSize; i++ {
		// Check if client cancelled (received RST_STREAM frame)
		select {
		case <-stream.Context().Done():
			log.Printf("Client cancelled at user %d", i)
			return status.Error(codes.Cancelled, "client cancelled")
		default:
		}

		user := &pb.UserResponse{
			UserId: uint64(i),
			Name:   fmt.Sprintf("User-%d", i),
			Email:  fmt.Sprintf("user%d@example.com", i),
		}

		// stream.Send() internally:
		//   1. Encodes user to protobuf bytes
		//   2. Adds gRPC 5-byte length prefix
		//   3. Submits as HTTP/2 DATA frame
		//   4. http2 library handles flow control (blocks if window=0)
		if err := stream.Send(user); err != nil {
			return err
		}

		log.Printf("Sent user %d/%d", i, pageSize)
		time.Sleep(50 * time.Millisecond) // Simulate work
	}

	// Returning nil here causes grpc-go to:
	//   Send trailing HEADERS frame: grpc-status=0, END_STREAM
	return nil
}

// ─────────────────────────────────────────────────────────────────────────────
// Pattern 3: Client Streaming
//
// stream.Recv() reads each incoming DATA frame and decodes protobuf.
// io.EOF means the client sent END_STREAM (finished uploading).
// ─────────────────────────────────────────────────────────────────────────────
func (s *userServer) UploadUsers(stream pb.UserService_UploadUsersServer) error {
	var count uint32

	for {
		req, err := stream.Recv()
		if err == io.EOF {
			// Client sent END_STREAM — upload complete
			// Now send the single response and close.
			log.Printf("Upload complete: %d users received", count)
			return stream.SendAndClose(&pb.UploadResponse{Count: count})
		}
		if err != nil {
			return status.Errorf(codes.Internal, "recv error: %v", err)
		}

		log.Printf("Received user_id=%d", req.UserId)
		count++
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// Pattern 4: Bidirectional Streaming
//
// Both sides send/receive concurrently.
// In Go, we use a goroutine to handle sending while the main goroutine
// handles receiving (or vice versa).
//
// HTTP/2: Stream is HALF-CLOSED(local) from client's perspective when
// client sends END_STREAM. Server can still send.
// ─────────────────────────────────────────────────────────────────────────────
func (s *userServer) Chat(stream pb.UserService_ChatServer) error {
	log.Println("Chat stream opened")

	// Goroutine for sending: allows us to send proactively
	// while also receiving from client.
	sendCh := make(chan *pb.ChatMessage, 32)
	errCh := make(chan error, 1)

	go func() {
		for msg := range sendCh {
			if err := stream.Send(msg); err != nil {
				errCh <- err
				return
			}
		}
		errCh <- nil
	}()

	// Receive loop: reads client messages
	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			// Client done sending. We can still send.
			close(sendCh) // Signal sender goroutine to finish
			return <-errCh
		}
		if err != nil {
			close(sendCh)
			return err
		}

		log.Printf("Chat from %s: %s", msg.Sender, msg.Text)

		// Echo back
		sendCh <- &pb.ChatMessage{
			Sender: "server",
			Text:   "Echo: " + msg.Text,
		}

		// Server-initiated message (not in response to any specific client msg)
		sendCh <- &pb.ChatMessage{
			Sender: "server-broadcast",
			Text:   "Server push at " + time.Now().Format(time.RFC3339),
		}
	}
}

// ─────────────────────────────────────────────────────────────────────────────
// HTTP/2 and gRPC Server Configuration
//
// These settings map directly to HTTP/2 SETTINGS frames and TCP socket options.
// ─────────────────────────────────────────────────────────────────────────────
func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("listen: %v", err)
	}

	srv := grpc.NewServer(
		// ─── HTTP/2 Flow Control ─────────────────────────────────────────
		// InitialWindowSize: Per-stream HTTP/2 flow control window.
		//   Sent as SETTINGS_INITIAL_WINDOW_SIZE in the SETTINGS frame.
		//   Default: 65535 (too small for high-throughput streaming)
		grpc.InitialWindowSize(1 << 20), // 1MB

		// InitialConnWindowSize: Connection-level HTTP/2 flow control.
		//   Sent as a WINDOW_UPDATE on stream 0 after SETTINGS.
		//   Default: 65535 (too small for multiple concurrent large streams)
		grpc.InitialConnWindowSize(1 << 23), // 8MB

		// ─── gRPC Keep-Alive (HTTP/2 PING frames) ────────────────────────
		// Keep-alive detects dead connections faster than TCP keepalive.
		// Uses HTTP/2 PING frames (type=0x6) for detection.
		//
		// Example PING frame flow:
		//   Client → Server: PING (8-byte opaque payload, flags=0x0)
		//   Server → Client: PING (same payload, flags=0x1 = ACK)
		//   If no ACK within KeepaliveTimeout: connection closed.
		grpc.KeepaliveParams(keepalive.ServerParameters{
			// Time: How long to wait before sending a PING if idle.
			Time: 10 * time.Second,
			// Timeout: How long to wait for PING ACK before declaring dead.
			Timeout: 5 * time.Second,
			// MaxConnectionAge: Force reconnect after this duration.
			// Useful to spread load after deployments.
			MaxConnectionAge: 30 * time.Minute,
			// MaxConnectionAgeGrace: Grace period after MaxConnectionAge.
			// Server sends GOAWAY, then waits this long for streams to finish.
			MaxConnectionAgeGrace: 30 * time.Second,
		}),

		// KeepaliveEnforcementPolicy: Protect server from too-aggressive clients.
		// Prevents a client from sending PINGs too frequently (DoS protection).
		grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
			// MinTime: Minimum time client must wait between PINGs.
			//   If client sends PINGs too fast: server sends GOAWAY.
			MinTime: 5 * time.Second,
			// PermitWithoutStream: Allow PING even when no active streams.
			//   Set true if clients maintain long-lived idle connections.
			PermitWithoutStream: true,
		}),

		// ─── Unary Interceptor ────────────────────────────────────────────
		// Interceptors run for every RPC. Like HTTP middleware.
		// Runs BEFORE the handler, on the same goroutine.
		grpc.UnaryInterceptor(func(
			ctx context.Context,
			req interface{},
			info *grpc.UnaryServerInfo,
			handler grpc.UnaryHandler,
		) (interface{}, error) {
			start := time.Now()
			resp, err := handler(ctx, req)
			log.Printf("[%s] took %v err=%v", info.FullMethod, time.Since(start), err)
			return resp, err
		}),
	)

	pb.RegisterUserServiceServer(srv, &userServer{})

	log.Printf("gRPC server listening on :50051")
	if err := srv.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
```

### client/main.go

```go
// Package main demonstrates gRPC client with multiplexing.
//
// Key insight: grpc.Dial creates ONE HTTP/2 connection (or a pool).
// ALL concurrent RPCs share this connection via HTTP/2 multiplexing.
//
// grpc.Dial is non-blocking by default — it returns immediately and
// connects lazily when the first RPC is made.
package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"

	pb "grpc-http2-demo/proto"
)

func main() {
	// ─── Connection Configuration ─────────────────────────────────────────
	// grpc.NewClient (or grpc.Dial) configures the HTTP/2 channel.
	//
	// The connection is NOT established here — it's lazy.
	// The first RPC triggers the TCP+TLS+HTTP/2 handshake.
	conn, err := grpc.NewClient(
		"localhost:50051",

		// For demo without TLS. In production: grpc.WithTransportCredentials(tls...)
		grpc.WithTransportCredentials(insecure.NewCredentials()),

		// ─── HTTP/2 Flow Control ────────────────────────────────────────
		grpc.WithInitialWindowSize(1 << 20),     // 1MB per stream
		grpc.WithInitialConnWindowSize(1 << 23), // 8MB per connection

		// ─── Client Keep-Alive ───────────────────────────────────────────
		// Sends HTTP/2 PING frames to server when idle.
		// KeepWithoutStream: true → ping even when no active RPCs.
		//   Useful for long-lived connections in service meshes.
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second,
			Timeout:             5 * time.Second,
			PermitWithoutStream: true,
		}),

		// ─── Max Message Size ────────────────────────────────────────────
		// Default: 4MB. Increase for large payloads.
		// This controls the maximum size of a single protobuf message
		// (not the HTTP/2 frame size — a message can span multiple frames).
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(16*1024*1024), // 16MB
			grpc.MaxCallSendMsgSize(16*1024*1024), // 16MB
		),
	)
	if err != nil {
		log.Fatalf("dial: %v", err)
	}
	defer conn.Close()

	client := pb.NewUserServiceClient(conn)

	// ─────────────────────────────────────────────────────────────────────
	// MULTIPLEXING DEMO: 20 concurrent goroutines, 1 HTTP/2 connection.
	//
	// Each goroutine makes a GetUser RPC.
	// grpc-go creates a separate HTTP/2 stream for each.
	// All 20 streams run concurrently on ONE TCP connection.
	//
	// Without HTTP/2: need 20 connections, 20 TLS handshakes.
	// With HTTP/2:    1 connection, 1 TLS handshake, 20 streams.
	// ─────────────────────────────────────────────────────────────────────
	fmt.Println("\n=== MULTIPLEXING: 20 concurrent RPCs on 1 connection ===")

	var wg sync.WaitGroup
	start := time.Now()

	for i := 1; i <= 20; i++ {
		wg.Add(1)
		go func(userID uint64) {
			defer wg.Done()

			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			resp, err := client.GetUser(ctx, &pb.UserRequest{UserId: userID})
			if err != nil {
				log.Printf("GetUser(%d) error: %v", userID, err)
				return
			}
			log.Printf("GetUser(%d) → %s <%s>", userID, resp.Name, resp.Email)
		}(uint64(i))
	}

	wg.Wait()
	log.Printf("20 RPCs completed in %v (1 connection)", time.Since(start))

	// ─────────────────────────────────────────────────────────────────────
	// Server Streaming Demo
	// ─────────────────────────────────────────────────────────────────────
	fmt.Println("\n=== SERVER STREAMING: ListUsers ===")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	stream, err := client.ListUsers(ctx, &pb.ListRequest{PageSize: 5})
	if err != nil {
		log.Fatalf("ListUsers: %v", err)
	}

	for {
		user, err := stream.Recv()
		if err == io.EOF {
			break // Server sent END_STREAM
		}
		if err != nil {
			log.Fatalf("stream.Recv: %v", err)
		}
		log.Printf("Streamed: id=%d, name=%s", user.UserId, user.Name)
	}

	// ─────────────────────────────────────────────────────────────────────
	// Client Streaming Demo
	// ─────────────────────────────────────────────────────────────────────
	fmt.Println("\n=== CLIENT STREAMING: UploadUsers ===")

	uploadStream, err := client.UploadUsers(context.Background())
	if err != nil {
		log.Fatalf("UploadUsers: %v", err)
	}

	for i := 1; i <= 5; i++ {
		if err := uploadStream.Send(&pb.UserRequest{UserId: uint64(i)}); err != nil {
			log.Fatalf("Send: %v", err)
		}
		log.Printf("Uploaded user %d", i)
		time.Sleep(100 * time.Millisecond)
	}

	// CloseAndRecv: sends END_STREAM, then waits for server response.
	// Under the hood: sets END_STREAM flag on last DATA frame,
	// then reads response HEADERS + DATA + trailer HEADERS.
	uploadResp, err := uploadStream.CloseAndRecv()
	if err != nil {
		log.Fatalf("CloseAndRecv: %v", err)
	}
	log.Printf("Upload done: %d users accepted", uploadResp.Count)

	// ─────────────────────────────────────────────────────────────────────
	// Bidirectional Streaming Demo
	// ─────────────────────────────────────────────────────────────────────
	fmt.Println("\n=== BIDIRECTIONAL STREAMING: Chat ===")

	chatStream, err := client.Chat(context.Background())
	if err != nil {
		log.Fatalf("Chat: %v", err)
	}

	done := make(chan struct{})

	// Receiving goroutine — runs concurrently with sender
	go func() {
		defer close(done)
		for {
			msg, err := chatStream.Recv()
			if err == io.EOF {
				return
			}
			if err != nil {
				log.Printf("recv error: %v", err)
				return
			}
			log.Printf("Server says [%s]: %s", msg.Sender, msg.Text)
		}
	}()

	// Sending: client pushes messages
	messages := []string{"Hello!", "How are you?", "Goodbye!"}
	for _, text := range messages {
		err := chatStream.Send(&pb.ChatMessage{
			Sender: "client",
			Text:   text,
		})
		if err != nil {
			log.Fatalf("Send: %v", err)
		}
		log.Printf("Client sent: %s", text)
		time.Sleep(200 * time.Millisecond)
	}

	// Close send side (END_STREAM from client)
	// Server can still send after this!
	chatStream.CloseSend()

	// Wait for receiver goroutine to finish
	<-done
	fmt.Println("\n=== All patterns complete ===")
}
```

### http2_inspector.go

```go
// http2_inspector.go
//
// Uses golang.org/x/net/http2 directly to inspect HTTP/2 frames.
// This is what grpc-go uses under the hood.
// Demonstrates the raw framing layer.
package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/hpack"
)

// inspectHTTP2Frames connects to a server and prints every HTTP/2 frame.
func inspectHTTP2Frames(addr string) {
	// TLS connect with ALPN h2
	tlsConf := &tls.Config{
		InsecureSkipVerify: true, // Dev only
		NextProtos:         []string{"h2"},
	}

	conn, err := tls.Dial("tcp", addr, tlsConf)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	// Verify ALPN negotiated h2
	state := conn.ConnectionState()
	fmt.Printf("ALPN negotiated: %s\n", state.NegotiatedProtocol)

	// Wrap the TCP+TLS conn with HTTP/2 framing
	// http2.NewFramer reads/writes HTTP/2 frames on the conn
	framer := http2.NewFramer(conn, conn)

	// Enable header logging (HPACK decoding)
	framer.ReadMetaHeaders = hpack.NewDecoder(4096, func(f hpack.HeaderField) {
		fmt.Printf("  HPACK header: %s = %s (sensitive=%v)\n",
			f.Name, f.Value, f.Sensitive)
	})

	// Send HTTP/2 connection preface
	conn.Write([]byte("PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"))

	// Send SETTINGS frame
	framer.WriteSettings(
		http2.Setting{ID: http2.SettingInitialWindowSize, Val: 1 << 20},
		http2.Setting{ID: http2.SettingMaxConcurrentStreams, Val: 100},
	)

	// Read and print all frames
	for {
		frame, err := framer.ReadFrame()
		if err != nil {
			fmt.Printf("Read error: %v\n", err)
			return
		}

		switch f := frame.(type) {
		case *http2.SettingsFrame:
			fmt.Printf("[SETTINGS] ack=%v\n", f.IsAck())
			f.ForeachSetting(func(s http2.Setting) error {
				fmt.Printf("  %s = %d\n", s.ID, s.Val)
				return nil
			})
			// Acknowledge server settings
			if !f.IsAck() {
				framer.WriteSettingsAck()
			}

		case *http2.MetaHeadersFrame:
			fmt.Printf("[HEADERS] stream=%d endStream=%v endHeaders=%v\n",
				f.StreamID, f.StreamEnded(), f.HeadersEnded())

		case *http2.DataFrame:
			fmt.Printf("[DATA] stream=%d len=%d endStream=%v\n",
				f.StreamID, f.Length, f.StreamEnded())

		case *http2.WindowUpdateFrame:
			fmt.Printf("[WINDOW_UPDATE] stream=%d increment=%d\n",
				f.StreamID, f.Increment)

		case *http2.PingFrame:
			fmt.Printf("[PING] ack=%v data=%x\n", f.IsAck(), f.Data)
			if !f.IsAck() {
				// Respond to server PING
				framer.WritePing(true, f.Data)
			}

		case *http2.GoAwayFrame:
			fmt.Printf("[GOAWAY] lastStream=%d errCode=%v debug=%s\n",
				f.LastStreamID, f.ErrCode, f.DebugData())
			return

		case *http2.RSTStreamFrame:
			fmt.Printf("[RST_STREAM] stream=%d errCode=%v\n",
				f.StreamID, f.ErrCode)

		default:
			fmt.Printf("[FRAME] type=%T stream=%d\n", frame, frame.Header().StreamID)
		}
	}
}

// Demonstrate connection-level WINDOW_UPDATE
func demonstrateFlowControl() {
	// Show the byte-level format of WINDOW_UPDATE frame
	//
	// Frame header (9 bytes):
	//   Length:    4 (payload size)
	//   Type:      0x08 (WINDOW_UPDATE)
	//   Flags:     0x00
	//   Stream ID: 0x00000000 (connection level)
	//
	// Payload (4 bytes):
	//   Reserved bit (1) + Window Size Increment (31 bits)
	//   = 0x00400000 → 4,194,304 bytes = 4MB increment
	frame := []byte{
		0x00, 0x00, 0x04, // Length: 4
		0x08,             // Type: WINDOW_UPDATE
		0x00,             // Flags: none
		0x00, 0x00, 0x00, 0x00, // Stream ID: 0 (connection)
		0x00, 0x40, 0x00, 0x00, // Increment: 4MB
	}

	fmt.Printf("WINDOW_UPDATE frame (hex): % X\n", frame)
	fmt.Printf("  Length:    %d\n", int(frame[0])<<16|int(frame[1])<<8|int(frame[2]))
	fmt.Printf("  Type:      0x%02X (WINDOW_UPDATE)\n", frame[3])
	fmt.Printf("  Flags:     0x%02X\n", frame[4])
	streamID := int(frame[5])<<24 | int(frame[6])<<16 | int(frame[7])<<8 | int(frame[8])
	fmt.Printf("  Stream ID: %d\n", streamID)
	increment := int(frame[9])<<24 | int(frame[10])<<16 | int(frame[11])<<8 | int(frame[12])
	increment &= 0x7FFFFFFF // Clear reserved bit
	fmt.Printf("  Increment: %d bytes\n", increment)
}

// demonstrateHPACK shows how headers are compressed
func demonstrateHPACK() {
	encoder := hpack.NewEncoder(new(bytes.Buffer))

	headers := []hpack.HeaderField{
		{Name: ":method", Value: "POST"},
		{Name: ":scheme", Value: "https"},
		{Name: ":path", Value: "/user.UserService/GetUser"},
		{Name: ":authority", Value: "api.example.com"},
		{Name: "content-type", Value: "application/grpc"},
		{Name: "te", Value: "trailers"},
	}

	var compressed bytes.Buffer
	enc := hpack.NewEncoder(&compressed)

	var uncompressedSize int
	for _, h := range headers {
		uncompressedSize += len(h.Name) + len(h.Value) + 32 // HTTP/2 header overhead
		enc.WriteField(h)
	}

	fmt.Printf("HPACK compression:\n")
	fmt.Printf("  Uncompressed: %d bytes\n", uncompressedSize)
	fmt.Printf("  Compressed:   %d bytes (%.1f%% reduction)\n",
		compressed.Len(),
		float64(uncompressedSize-compressed.Len())/float64(uncompressedSize)*100)
	fmt.Printf("  Compressed bytes: % X\n", compressed.Bytes())
}
```

---

## 19. Performance Tuning — Expert Knobs

### HTTP/2 Settings to Tune

```
Setting                  Default    Recommended (gRPC)   Why
───────────────────────  ─────────  ───────────────────  ──────────────────────────────────
INITIAL_WINDOW_SIZE      65535      1-4 MB               Default is tiny; causes stalls on
                                                         high-throughput streams
Initial Conn Window      65535      8-64 MB              Total bandwidth for all streams
MAX_FRAME_SIZE           16384      16384-1MB            Larger = fewer frames, less overhead
MAX_CONCURRENT_STREAMS   unlimited  100-1000             Prevent OOM on server
MAX_HEADER_LIST_SIZE     unlimited  8192                 Prevent header injection
```

### Operating System Tuning

```bash
# Increase TCP buffer sizes (affects all connections)
sysctl -w net.core.rmem_max=134217728      # 128MB max recv buffer
sysctl -w net.core.wmem_max=134217728      # 128MB max send buffer
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"  # min/default/max
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Enable TCP BBR congestion control (better than CUBIC for high-BDP links)
sysctl -w net.core.default_qdisc=fq
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Increase file descriptor limit (each connection = 1 fd)
ulimit -n 1048576

# Verify:
sysctl net.ipv4.tcp_congestion_control
# Should show: bbr
```

### gRPC-specific Performance Settings

```go
// Go: Maximum number of concurrent streams per connection
// Maps to SETTINGS_MAX_CONCURRENT_STREAMS
grpc.MaxConcurrentStreams(1000)

// Go: Disable gRPC-level message compression for small messages
// (compression CPU overhead > bandwidth savings for small payloads)
grpc.WithDefaultCallOptions(grpc.UseCompressor("")) // disable

// Go: Connection pool (for very high concurrency)
// grpc-go uses connection pooling when NumChannels > 1
// Each channel = one HTTP/2 connection
grpc.WithConnectParams(grpc.ConnectParams{
    MinConnectTimeout: 10 * time.Second,
})
```

### Latency vs Throughput Tradeoffs

```
┌────────────────────────────────────────────────────────────────────┐
│                    TUNING DECISION TREE                             │
│                                                                     │
│  Optimize for LATENCY (small, frequent RPCs):                       │
│    - Small window sizes (64KB-256KB) → WINDOW_UPDATE sent sooner   │
│    - TCP_NODELAY = true (already default in gRPC)                  │
│    - Small MAX_FRAME_SIZE → less waiting for full frame            │
│    - Disable Nagle's (already done)                                │
│                                                                     │
│  Optimize for THROUGHPUT (large payloads, streaming):              │
│    - Large window sizes (1MB-64MB) → fewer WINDOW_UPDATE frames    │
│    - Large MAX_FRAME_SIZE → fewer frame headers overhead           │
│    - Enable compression (gzip/snappy) for compressible data        │
│    - TCP BBR congestion control                                     │
│                                                                     │
│  Balance:                                                           │
│    - Per-stream window: 1MB (handles most streaming cases)         │
│    - Connection window: 8MB (handles 8 concurrent 1MB streams)     │
│    - MAX_FRAME_SIZE: 16KB-64KB                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 20. Hidden Gotchas and Expert Insights

### 1. HTTP/2 Head-of-Line Blocking Still Exists at TCP Level

```
┌──────────────────────────────────────────────────────────────────┐
│  HTTP/2 solves APPLICATION-level HOL blocking.                   │
│  But TCP-level HOL blocking remains!                             │
│                                                                  │
│  Scenario:                                                       │
│    Packet 1 (Stream 1 data) ──LOST──→                           │
│    Packet 2 (Stream 3 data) → arrived                           │
│    Packet 3 (Stream 5 data) → arrived                           │
│                                                                  │
│  TCP must deliver in ORDER. Packets 2 & 3 wait in receive buffer │
│  until packet 1 is retransmitted and received.                   │
│                                                                  │
│  Stream 3 and 5 are blocked even though their data arrived!      │
│                                                                  │
│  Solution: HTTP/3 uses QUIC (UDP-based) which has per-stream    │
│  delivery — a lost packet only blocks ITS stream, not others.   │
└──────────────────────────────────────────────────────────────────┘
```

### 2. Stream ID Exhaustion

```
Client-initiated streams use odd IDs: 1, 3, 5, ..., 2^31-1

After 2^31-1 streams on one connection, IDs wrap — which is illegal.
The connection MUST be closed with GOAWAY and a new one opened.

For a service making 1 million RPCs/second:
  2^31 / 1,000,000 = ~2147 seconds = ~35 minutes

gRPC handles this automatically with GOAWAY + reconnect.
Set MaxConnectionAge to force periodic recycling.
```

### 3. GOAWAY is Graceful — Not Error

```
GOAWAY frame:
  Last-Stream-ID: The highest stream ID the server processed.
  Streams > Last-Stream-ID: Were NOT processed → safe to retry.
  Streams ≤ Last-Stream-ID: Were processed → DO NOT retry (might double-execute).

When you see GOAWAY in logs — it's normal during rolling deployments,
connection recycling, or load balancer drain. Not a bug.
```

### 4. gRPC Trailers-Only Response

```
For errors (non-OK status), gRPC can send a "trailers-only" response:
  Single HEADERS frame with END_STREAM that contains BOTH
  :status=200 (HTTP level) AND grpc-status=<error-code>

This is legal HTTP/2 but confusing:
  HTTP status = 200 (OK)
  gRPC status = 14 (UNAVAILABLE)

Don't be fooled: an HTTP 200 does NOT mean gRPC success.
Always check grpc-status trailer.
```

### 5. The `te: trailers` Header is Required

```
gRPC requires the te: trailers header in every request.

Why: HTTP/1.1 proxies that upgrade to HTTP/2 might not understand
trailers. The te: trailers header signals "I know about trailers,
don't strip them." Without it, some proxies drop the grpc-status
trailer → client gets a mysterious error.

Always include: te: trailers
```

### 6. Flow Control and Goroutine/Thread Starvation

```
Scenario in Go:
  Server streams 1GB of data.
  Handler is blocked in stream.Send() (flow control window = 0).
  
  Meanwhile: New connection comes in. New goroutine spawned.
  HTTP/2 PING arrives. Must be handled quickly.
  
  If all goroutines are blocked in Send():
    PING not processed → client declares connection dead → RST_STREAM
    
Solution: grpc-go handles PING in the connection goroutine, separate
          from handler goroutines. Don't block the connection goroutine.
```

### 7. Header Table Poisoning

```
HPACK dynamic table is shared across all streams on a connection.

If two concurrent requests update the dynamic table simultaneously:
  No problem! HPACK table updates are processed in frame order,
  which is single-threaded on the connection.

But: Large headers that evict useful entries cause future requests
to send headers verbatim (no compression). Watch for this if your
headers are huge and variable.
```

### 8. SETTINGS_MAX_FRAME_SIZE and Large Protobuf Messages

```
MAX_FRAME_SIZE default: 16,384 bytes (16KB)
Protobuf message: 1MB

gRPC splits the 1MB message across:
  1,048,576 / 16,384 = 64 DATA frames

Each frame has 9-byte overhead:
  64 × 9 = 576 bytes overhead (tiny, ~0.05%)

BUT: 64 frames × 64 streams = 4096 frames in-flight
     High frame count increases CPU for parsing.

For large messages: increase MAX_FRAME_SIZE to 1MB:
  One frame per message → minimal parsing overhead.
  Tradeoff: Multiplexing granularity decreases
            (other streams must wait for the 1MB frame to finish).
```

### 9. The Ping-Pong Problem with Bidirectional Streaming

```
BAD pattern:
  Client sends → Server processes → Server responds →
  Client processes → Client sends → ...

This is SEQUENTIAL despite being "bidirectional."
RTT doubles every round trip. Throughput = message_size / RTT.

GOOD pattern:
  Client sends continuously without waiting for responses.
  Server sends continuously without waiting for requests.
  Both sides use separate goroutines/tasks for send and receive.

This is TRUE full-duplex. Throughput = min(client_bw, server_bw).
```

### Complete Decision Flowchart: Which gRPC Pattern to Use?

```
START: What is your RPC shape?
         │
         ▼
Is request a single message?
    │              │
   YES             NO
    │              │
    ▼              ▼
Is response      ┌─────────────────────────────────┐
a single         │  Is server response a           │
message?         │  single message?                │
  │    │         └─────────────────────────────────┘
YES   NO              │              │
  │    │             YES             NO
  ▼    ▼              │              │
UNARY  SERVER         ▼              ▼
RPC    STREAMING   CLIENT       BIDIRECTIONAL
       RPC         STREAMING    STREAMING RPC
                   RPC
       
Examples:
  UNARY:         GetUser, CreateOrder, ValidateToken
  SERVER:        SubscribeToEvents, StreamLargeFile, WatchResource
  CLIENT:        UploadFile, BatchWrite, StreamingSensorData
  BIDI:          Chat, RealTimeCollab, GameState, VideoConference
```

---

## Summary: The Complete Picture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    HOW IT ALL FITS TOGETHER                               │
│                                                                           │
│  Your code calls: client.GetUser(request)                                 │
│         ↓                                                                 │
│  Protobuf: Serializes struct to binary bytes                              │
│         ↓                                                                 │
│  gRPC framing: [0x00][length 4 bytes][proto bytes]                        │
│         ↓                                                                 │
│  HTTP/2 HEADERS frame: :method=POST :path=/pkg.Svc/Method                 │
│  HTTP/2 DATA frame:    [gRPC frame bytes]                                 │
│         ↓                                                                 │
│  HPACK: Compresses headers (3-10x reduction)                              │
│         ↓                                                                 │
│  TLS: Encrypts frames (after ALPN negotiated h2)                          │
│         ↓                                                                 │
│  TCP: Reliable ordered byte stream, flow controlled                       │
│       TCP_NODELAY=true, SO_SNDBUF=4MB+                                    │
│         ↓                                                                 │
│  Kernel: sk_buff allocation, NIC DMA, interrupt, ring buffer              │
│         ↓                                                                 │
│  Network: Ethernet frame, IP packet, TCP segment                          │
│         ↓                                                                 │
│  WIRE: ~150-200 bytes total for a tiny request                            │
│        (vs 600-2000 bytes for JSON REST)                                  │
│                                                                           │
│  MULTIPLEXING: 1000 streams, 1 connection, 1 TLS handshake               │
│  STREAMING:    DATA frames flow until END_STREAM or RST_STREAM            │
│  FLOW CONTROL: WINDOW_UPDATE prevents buffer overflow at 2 levels        │
│  COMPRESSION:  HPACK shrinks repeated headers to 1-2 bytes               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

*This document covers: HTTP/2 multiplexing internals, frame-level protocol analysis, kernel-level socket mechanics, network packet flow, and production-grade implementations in C (nghttp2), Rust (tonic/h2), and Go (grpc-go).*

