# L4 vs L7 Load Balancers & Protocols — Complete In-Depth Guide

---

> **Mental Model Goal:** By the end of this guide, you will think of network traffic like a postal
> system — L4 is the *post office sorting room* (looks only at the envelope: from/to address,
> port), while L7 is the *smart mail clerk* (opens the envelope, reads the content, and decides
> where to route based on meaning).

---

## Table of Contents

1. [Foundation — The OSI Model](#1-foundation--the-osi-model)
2. [What is a Load Balancer?](#2-what-is-a-load-balancer)
3. [The Network Stack in Practice](#3-the-network-stack-in-practice)
4. [Layer 4 (Transport Layer) — Deep Dive](#4-layer-4-transport-layer--deep-dive)
5. [Layer 7 (Application Layer) — Deep Dive](#5-layer-7-application-layer--deep-dive)
6. [Real Protocol Wire Diagrams (ASCII)](#6-real-protocol-wire-diagrams-ascii)
7. [L4 Load Balancer — Architecture & Internals](#7-l4-load-balancer--architecture--internals)
8. [L7 Load Balancer — Architecture & Internals](#8-l7-load-balancer--architecture--internals)
9. [Load Balancing Algorithms](#9-load-balancing-algorithms)
10. [Health Checks](#10-health-checks)
11. [SSL/TLS Termination](#11-ssltls-termination)
12. [Sticky Sessions (Session Persistence)](#12-sticky-sessions-session-persistence)
13. [Connection Pooling](#13-connection-pooling)
14. [L4 vs L7 — Head-to-Head Comparison](#14-l4-vs-l7--head-to-head-comparison)
15. [Real-World Tools & Systems](#15-real-world-tools--systems)
16. [Advanced Topics](#16-advanced-topics)
17. [Mental Models & Expert Intuition](#17-mental-models--expert-intuition)

---

## 1. Foundation — The OSI Model

### What is the OSI Model?

**OSI** stands for **Open Systems Interconnection**. It is a conceptual framework invented by ISO
(International Organization for Standardization) in 1984 to describe how different network
protocols interact and how data travels from one computer to another across a network.

Think of it like layers of a cake — each layer has a specific job, and it only communicates with
the layer directly above and below it.

### The 7 Layers

```
+---+---------------------+------------------------------------------+-------------------+
| # | Layer Name          | Responsibility                           | Example Protocols |
+---+---------------------+------------------------------------------+-------------------+
| 7 | Application         | User-facing services, app protocols      | HTTP, FTP, SMTP   |
| 6 | Presentation        | Encoding, encryption, compression        | TLS/SSL, JPEG     |
| 5 | Session             | Session management, sync                 | RPC, NetBIOS      |
| 4 | Transport           | End-to-end delivery, ports, reliability  | TCP, UDP          |
| 3 | Network             | Logical addressing, routing              | IP, ICMP, OSPF    |
| 2 | Data Link           | Physical addressing, frames              | Ethernet, ARP     |
| 1 | Physical            | Bits on wire/radio                       | Cables, Wi-Fi     |
+---+---------------------+------------------------------------------+-------------------+
```

### Key Vocabulary

| Term            | Meaning                                                                    |
|-----------------|----------------------------------------------------------------------------|
| **PDU**         | Protocol Data Unit — the name of data at each layer (frame, packet, segment, etc.) |
| **Encapsulation** | Wrapping data with headers as it goes DOWN the layers before sending     |
| **Decapsulation** | Stripping headers as data goes UP the layers after receiving             |
| **Port**        | A 16-bit number (0–65535) identifying a specific process/service on a host |
| **Socket**      | A combination of IP address + Port (e.g., `192.168.1.1:443`)              |
| **Segment**     | TCP PDU at Layer 4                                                         |
| **Datagram**    | UDP PDU at Layer 4                                                         |
| **Packet**      | IP PDU at Layer 3                                                          |
| **Frame**       | Ethernet PDU at Layer 2                                                    |

### Data Encapsulation — How a Message Travels Down the Stack

```
Application generates: "GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"

Layer 7 (App)    [ HTTP DATA                                              ]
                  ↓ add TCP header
Layer 4 (Trans)  [ TCP HDR | HTTP DATA                                   ]
                  ↓ add IP header
Layer 3 (Net)    [ IP HDR  | TCP HDR | HTTP DATA                         ]
                  ↓ add Ethernet header+trailer
Layer 2 (DL)     [ ETH HDR | IP HDR | TCP HDR | HTTP DATA | ETH TRAILER  ]
                  ↓ converted to bits
Layer 1 (Phys)   01001101001001010001110010001011010010011...
```

On the receiving end, each layer strips its own header and passes up to the next layer.

---

## 2. What is a Load Balancer?

### Definition

A **Load Balancer** is a device or software that distributes incoming network traffic across
multiple backend servers to:

- Prevent any single server from becoming overwhelmed
- Increase availability and fault tolerance
- Scale horizontally (add more servers instead of buying a bigger one)
- Enable zero-downtime deployments

### The Core Problem It Solves

```
Without Load Balancer:

   Client A ──────────────────────────▶ Server (overloaded, single point of failure)
   Client B ──────────────────────────▶ Server
   Client C ──────────────────────────▶ Server (crashes → everyone affected)


With Load Balancer:

   Client A ──▶ ┌──────────────┐ ──▶ Server 1 (healthy)
   Client B ──▶ │ Load Balancer│ ──▶ Server 2 (healthy)
   Client C ──▶ └──────────────┘ ──▶ Server 3 (healthy)
                                 ╳──▶ Server 4 (dead, LB knows, skips it)
```

### Where Load Balancers Sit (Topology)

```
Internet
   │
   ▼
[DNS] ──resolves to VIP──▶ [Load Balancer VIP: 203.0.113.10]
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                    [Backend 1]   [Backend 2]   [Backend 3]
                    10.0.0.1      10.0.0.2      10.0.0.3
```

**VIP** = Virtual IP — the single IP address clients connect to. The LB owns it.

---

## 3. The Network Stack in Practice

### How a Browser Connects to example.com (Full Journey)

```
Step 1: DNS Resolution
  Browser → DNS Server: "What is the IP of example.com?"
  DNS Server → Browser: "203.0.113.10"

Step 2: TCP 3-Way Handshake (to port 80 or 443)
  Browser ──SYN──────────────────▶ LB (203.0.113.10:443)
  Browser ◀──SYN-ACK─────────────  LB
  Browser ──ACK──────────────────▶ LB

Step 3: TLS Handshake (if HTTPS)
  Browser ◀──────────────────────▶ LB (certificates, keys negotiated)

Step 4: HTTP Request
  Browser ──"GET / HTTP/1.1"─────▶ LB
  LB decides which backend to forward to
  LB ──forwards request──────────▶ Backend Server

Step 5: HTTP Response
  Backend ──"HTTP/1.1 200 OK"────▶ LB
  LB ──forwards response─────────▶ Browser
```

The fundamental question is: **At which step does the load balancer make its routing decision?**

- **L4 LB**: Makes decision at Step 2 (TCP handshake) — before any application data
- **L7 LB**: Makes decision at Step 4 (HTTP request) — after reading content

---

## 4. Layer 4 (Transport Layer) — Deep Dive

### What Layer 4 Sees

At Layer 4, the load balancer only has access to:

```
+--------------------------------------------------+
|              TCP/UDP Header Fields               |
+--------------------------------------------------+
| Source IP Address       | 192.168.1.100          |
| Destination IP Address  | 203.0.113.10           |
| Source Port             | 52341 (ephemeral)      |
| Destination Port        | 443                    |
| Sequence Number         | 1234567890             |
| Acknowledgment Number   | 0                      |
| Flags                   | SYN                    |
| Window Size             | 65535                  |
+--------------------------------------------------+
```

**It does NOT see:** HTTP headers, cookies, URL paths, request body — nothing from Layer 7.

### TCP — Transmission Control Protocol

**TCP** is a **connection-oriented**, **reliable**, **ordered** protocol.

#### Key Concepts in TCP:

| Concept             | Meaning                                                                       |
|---------------------|-------------------------------------------------------------------------------|
| **Connection-oriented** | A connection must be established (handshake) before data flows          |
| **Reliable**        | Lost packets are retransmitted; every byte is acknowledged                    |
| **Ordered**         | Data arrives in the same sequence it was sent                                 |
| **Flow Control**    | Receiver tells sender how much data it can handle (Window Size)               |
| **Congestion Control** | TCP slows down if the network is congested (AIMD algorithm)               |
| **Full Duplex**     | Both sides can send and receive simultaneously                                |

#### TCP 3-Way Handshake (SYN → SYN-ACK → ACK)

```
Client                        Server
  │                              │
  │──── SYN (seq=x) ────────────▶│  "I want to connect, my seq starts at x"
  │                              │
  │◀─── SYN-ACK (seq=y, ack=x+1)│  "OK, my seq starts at y, I got your x"
  │                              │
  │──── ACK (ack=y+1) ──────────▶│  "Got it, your seq acknowledged"
  │                              │
  │  <<< CONNECTION ESTABLISHED >>>
  │                              │
  │──── DATA ───────────────────▶│
  │◀─── DATA ────────────────────│
```

#### TCP Termination (4-Way)

```
Client                        Server
  │                              │
  │──── FIN ────────────────────▶│  "I'm done sending"
  │◀─── ACK ─────────────────────│  "OK, I got your FIN"
  │◀─── FIN ─────────────────────│  "I'm also done sending"
  │──── ACK ────────────────────▶│  "OK, goodbye"
  │                              │
  │  <<< CONNECTION CLOSED >>>
```

#### TCP Segment Header (Real Wire Format)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |           |U|A|P|R|S|F|                               |
| Offset| Reserved  |R|C|S|S|Y|I|            Window             |
|       |           |G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (if Data Offset > 5)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Flags explained:
  URG = Urgent pointer field is significant
  ACK = Acknowledgment field is significant
  PSH = Push function (flush buffer immediately)
  RST = Reset the connection
  SYN = Synchronize sequence numbers (used in handshake)
  FIN = No more data from sender (used in close)
```

### UDP — User Datagram Protocol

**UDP** is **connectionless**, **unreliable**, **unordered** — but very fast.

#### UDP Use Cases

| Protocol | Why UDP?                                                    |
|----------|-------------------------------------------------------------|
| DNS      | Query-response, tiny payloads, fast is better than reliable |
| DHCP     | Bootstrap protocol, no existing connection possible         |
| Video streaming | Drop a frame, not the whole stream                   |
| Online gaming   | Latency matters more than perfect reliability         |
| QUIC     | Builds its own reliability on top of UDP                   |

#### UDP Datagram Header (Real Wire Format)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Only 8 bytes of overhead (TCP has 20+ bytes). That's why UDP is faster.
```

### TCP vs UDP — Fundamental Comparison

```
Property            TCP                         UDP
─────────────────────────────────────────────────────────────────
Connection          Required (3-way handshake)  None
Reliability         Guaranteed delivery         Best-effort
Ordering            Preserved                   Not guaranteed
Error Recovery      Retransmission              None (app must handle)
Flow Control        Yes (window size)           No
Congestion Control  Yes (AIMD, etc.)            No
Header Size         20–60 bytes                 8 bytes
Speed               Slower (overhead)           Faster
Use Case            HTTP, FTP, SMTP, SSH        DNS, DHCP, VoIP, Games
```

---

## 5. Layer 7 (Application Layer) — Deep Dive

### What Layer 7 Sees

An L7 load balancer can read the **full application message**:

```
GET /api/v2/users/profile HTTP/1.1
Host: api.example.com
User-Agent: Mozilla/5.0 ...
Accept: application/json
Cookie: session_id=abc123xyz; user_pref=dark_mode
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
X-Request-ID: 7f3d9e2a-1b4c-4d8e-9f0a-2b5c6d7e8f9a

{"action": "get_profile", "user_id": 42}
```

This means routing decisions can be based on:
- URL path (`/api/users` → User Service, `/api/orders` → Order Service)
- HTTP method (GET, POST, DELETE)
- Query parameters
- Cookies (session affinity)
- Headers (authentication, content type)
- Request body content
- Hostname (virtual hosting)

### HTTP/1.1 Protocol

**HTTP** = HyperText Transfer Protocol. A **text-based**, **stateless**, **request-response** protocol.

#### HTTP Request Structure

```
REQUEST LINE:   METHOD  SP  REQUEST-URI  SP  HTTP-VERSION  CRLF
HEADERS:        Header-Name: Header-Value  CRLF
                ...
EMPTY LINE:     CRLF
BODY:           (optional, for POST/PUT)

Example:
┌─────────────────────────────────────────────────────────────┐
│ POST /api/login HTTP/1.1\r\n                                │
│ Host: example.com\r\n                                       │
│ Content-Type: application/json\r\n                          │
│ Content-Length: 47\r\n                                      │
│ Connection: keep-alive\r\n                                  │
│ \r\n                                                        │
│ {"username":"alice","password":"s3cr3t_p4ssw0rd"}           │
└─────────────────────────────────────────────────────────────┘
```

#### HTTP Response Structure

```
STATUS LINE:    HTTP-VERSION  SP  STATUS-CODE  SP  REASON-PHRASE  CRLF
HEADERS:        Header-Name: Header-Value  CRLF
                ...
EMPTY LINE:     CRLF
BODY:           (HTML, JSON, image bytes, etc.)

Example:
┌─────────────────────────────────────────────────────────────┐
│ HTTP/1.1 200 OK\r\n                                         │
│ Content-Type: application/json\r\n                          │
│ Content-Length: 89\r\n                                      │
│ Set-Cookie: session=abc123; Path=/; HttpOnly; Secure\r\n    │
│ X-Request-ID: 7f3d9e2a-1b4c-4d8e-9f0a-2b5c6d7e8f9a\r\n    │
│ \r\n                                                        │
│ {"status":"ok","token":"eyJhbG...","expires_in":3600}       │
└─────────────────────────────────────────────────────────────┘
```

#### HTTP Methods and Their Semantics

| Method  | Purpose                   | Idempotent? | Safe? | Has Body? |
|---------|---------------------------|-------------|-------|-----------|
| GET     | Retrieve resource         | Yes         | Yes   | No        |
| POST    | Create resource           | No          | No    | Yes       |
| PUT     | Replace resource entirely | Yes         | No    | Yes       |
| PATCH   | Update resource partially | No          | No    | Yes       |
| DELETE  | Remove resource           | Yes         | No    | No        |
| HEAD    | GET without body          | Yes         | Yes   | No        |
| OPTIONS | Describe communication options | Yes    | Yes   | No        |

> **Idempotent** = Calling it multiple times has the same result as calling once.
> **Safe** = Has no side effects on the server.

#### Important HTTP Status Codes

```
1xx — Informational
  100 Continue       : Client should continue sending request body

2xx — Success
  200 OK             : Request succeeded
  201 Created        : Resource created (POST succeeded)
  204 No Content     : Success but no response body

3xx — Redirection
  301 Moved Permanently : Resource URL has permanently changed
  302 Found             : Temporary redirect
  304 Not Modified      : Cached version is still valid

4xx — Client Errors
  400 Bad Request    : Malformed request syntax
  401 Unauthorized   : Not authenticated
  403 Forbidden      : Authenticated but not authorized
  404 Not Found      : Resource doesn't exist
  429 Too Many Requests : Rate limit exceeded

5xx — Server Errors
  500 Internal Server Error : Generic server failure
  502 Bad Gateway           : LB got invalid response from backend
  503 Service Unavailable   : Backend is down
  504 Gateway Timeout       : Backend took too long to respond
```

### HTTP/2 Protocol

HTTP/2 is a **binary**, **multiplexed** protocol — a major redesign of HTTP/1.1.

#### Key Concepts in HTTP/2

| Term              | Meaning                                                                      |
|-------------------|------------------------------------------------------------------------------|
| **Stream**        | A bidirectional sequence of frames within a connection; each request/response is one stream |
| **Frame**         | The smallest unit of communication in HTTP/2 (replaces text headers)        |
| **Multiplexing**  | Multiple streams simultaneously on ONE TCP connection (solves head-of-line blocking) |
| **Header Compression** | HPACK algorithm — compresses headers, reducing overhead dramatically   |
| **Server Push**   | Server can proactively send resources before client asks                    |
| **Stream Priority** | Clients can signal which streams are more important                       |

#### HTTP/1.1 vs HTTP/2 Connection Model

```
HTTP/1.1 (One request at a time per connection):

Connection 1:  [GET /] ──────▶ [200 HTML] ──▶ [GET /style.css] ──▶ [200 CSS]
Connection 2:  [GET /logo.png] ──────────▶ [200 PNG]
Connection 3:  [GET /app.js] ────────────▶ [200 JS]
(Browsers open 6 parallel connections to workaround this)

HTTP/2 (Multiple streams, one connection):

Connection 1:
  Stream 1:  [GET /]         ════════════════▶ [200 HTML]
  Stream 3:  [GET /style.css]     ════════════▶ [200 CSS]
  Stream 5:  [GET /logo.png]           ═══════▶ [200 PNG]
  Stream 7:  [GET /app.js]                ══════▶ [200 JS]
  (All interleaved on ONE TCP connection)
```

#### HTTP/2 Frame Structure (Real Wire Format)

```
+-----------------------------------------------+
|                 Length (24)                   |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+-------------------------------+
|R|                 Stream Identifier (31)                      |
+=+=============================================================+
|                   Frame Payload (0...)                      ...
+---------------------------------------------------------------+

Type values:
  0x0 = DATA
  0x1 = HEADERS
  0x2 = PRIORITY
  0x3 = RST_STREAM
  0x4 = SETTINGS
  0x5 = PUSH_PROMISE
  0x6 = PING
  0x7 = GOAWAY
  0x8 = WINDOW_UPDATE
  0x9 = CONTINUATION
```

### HTTP/3 Protocol (QUIC-based)

HTTP/3 moves from TCP to **QUIC** (which runs on UDP).

#### Why HTTP/3 Exists — The Problem with TCP

```
HTTP/2 over TCP — Head-of-Line Blocking at TCP level:

Stream 1: [Frame A] ─── ─── [Frame C]   (Frame B is LOST in network)
Stream 2: [Frame D] [Frame E] [Frame F]
Stream 3: [Frame G] [Frame H] [Frame I]

TCP forces ALL streams to wait until the OS retransmits Frame B,
even though Streams 2 and 3 don't need Frame B at all!

HTTP/3 over QUIC — No head-of-line blocking:

QUIC Stream 1: [Frame A] ─── ─── [Frame C]   (waits for retransmit)
QUIC Stream 2: [Frame D] [Frame E] [Frame F]  (continues independently!)
QUIC Stream 3: [Frame G] [Frame H] [Frame I]  (continues independently!)
```

#### QUIC Key Features

| Feature                   | Description                                               |
|---------------------------|-----------------------------------------------------------|
| **0-RTT Connection**      | Reconnecting clients skip handshake entirely              |
| **1-RTT Handshake**       | New connections take only 1 round trip (vs 2 for TCP+TLS) |
| **Stream Multiplexing**   | At QUIC level, not TCP — so no L4 HOL blocking            |
| **Connection Migration**  | Same connection survives IP change (e.g., switching Wi-Fi to 4G) |
| **Integrated TLS 1.3**    | Encryption is mandatory and built in                      |

### WebSocket Protocol

**WebSockets** allow **full-duplex**, **persistent** connections over a single TCP connection.

#### WebSocket Upgrade Handshake

```
Client → Server (HTTP Upgrade):
──────────────────────────────────────────────────────────────
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

Server → Client (101 Switching Protocols):
──────────────────────────────────────────────────────────────
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

<<< NOW IN WEBSOCKET MODE — FULL DUPLEX >>>
Client ──── "Hello!" ────────────────────▶ Server
Server ◀─── "Hey there!" ───────────────── Server
Client ──── "Ping!" ─────────────────────▶ Server
```

#### WebSocket Frame Format (Real Wire Format)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)    |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - -+
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - -+-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - -+
:                     Payload Data continued ...                :
+---------------------------------------------------------------+

Opcodes:
  0x0 = Continuation frame
  0x1 = Text frame
  0x2 = Binary frame
  0x8 = Connection close
  0x9 = Ping
  0xA = Pong
```

### gRPC Protocol

**gRPC** is a high-performance RPC (Remote Procedure Call) framework by Google that runs over
HTTP/2 and uses Protocol Buffers for serialization.

#### gRPC vs REST

| Aspect            | REST/JSON                          | gRPC/Protobuf                         |
|-------------------|------------------------------------|---------------------------------------|
| Protocol          | HTTP/1.1 or HTTP/2                 | HTTP/2 only                           |
| Data Format       | JSON (text, human-readable)        | Protocol Buffers (binary, compact)    |
| Contract          | OpenAPI/Swagger (optional)         | .proto file (required, strict)        |
| Streaming         | SSE or WebSocket (separate)        | Native 4 types of streaming           |
| Performance       | Higher overhead                    | ~10x smaller, faster serialization    |
| Code Generation   | Optional                           | Built-in (generates client stubs)     |

#### gRPC Streaming Types

```
1. Unary RPC (one request, one response)
   Client ──[Request]──────────────────────────▶ Server
   Client ◀──[Response]────────────────────────── Server

2. Server Streaming (one request, many responses)
   Client ──[Request]──────────────────────────▶ Server
   Client ◀──[Response1][Response2][Response3]─── Server

3. Client Streaming (many requests, one response)
   Client ──[Req1][Req2][Req3]─────────────────▶ Server
   Client ◀──[Response]────────────────────────── Server

4. Bidirectional Streaming
   Client ──[Req1]──────────────────────────────▶ Server
   Client ◀──[Resp1]─────────────────────────────
   Client ──[Req2]──────────────────────────────▶
   Client ◀──[Resp2]─────────────────────────────
   (Fully independent streams, simultaneously)
```

---

## 6. Real Protocol Wire Diagrams (ASCII)

### Complete HTTP/1.1 Transaction Over TCP (Full Stack View)

```
CLIENT (192.168.1.5)                      SERVER (203.0.113.10)
Port: 54321                               Port: 80

═══════════════════ TCP HANDSHAKE ═══════════════════════════════
──SYN seq=1000─────────────────────────────────────────────────▶
◀──SYN-ACK seq=5000, ack=1001───────────────────────────────────
──ACK ack=5001──────────────────────────────────────────────────▶

═══════════════════ HTTP REQUEST ════════════════════════════════
──PSH+ACK seq=1001──────────────────────────────────────────────▶
  PAYLOAD:
  "GET /index.html HTTP/1.1\r\n"
  "Host: example.com\r\n"
  "User-Agent: curl/7.68.0\r\n"
  "Accept: */*\r\n"
  "\r\n"

═══════════════════ ACK ═════════════════════════════════════════
◀──ACK ack=1078─────────────────────────────────────────────────

═══════════════════ HTTP RESPONSE ═══════════════════════════════
◀──PSH+ACK seq=5001─────────────────────────────────────────────
  PAYLOAD:
  "HTTP/1.1 200 OK\r\n"
  "Date: Sat, 02 May 2026 10:00:00 GMT\r\n"
  "Content-Type: text/html; charset=utf-8\r\n"
  "Content-Length: 1234\r\n"
  "Connection: keep-alive\r\n"
  "\r\n"
  "<html>...</html>"

──ACK ack=5890──────────────────────────────────────────────────▶

═══════════════════ TCP CLOSE ═══════════════════════════════════
◀──FIN+ACK seq=5890─────────────────────────────────────────────
──ACK ack=5891──────────────────────────────────────────────────▶
──FIN+ACK seq=1078──────────────────────────────────────────────▶
◀──ACK ack=1079─────────────────────────────────────────────────
```

### TLS 1.3 Handshake (Full Wire Diagram)

> **TLS** = Transport Layer Security. It provides encryption, authentication, and integrity for
> any TCP connection. TLS 1.3 (2018) is the current standard.

```
CLIENT                                           SERVER
  │                                                │
  │──── ClientHello ──────────────────────────────▶│
  │     ┌──────────────────────────────────────┐   │
  │     │ TLS Version: 1.3                     │   │
  │     │ Random: 32 bytes of random data      │   │
  │     │ Cipher Suites: [AES-GCM, ChaCha20]  │   │
  │     │ Extensions:                          │   │
  │     │   supported_versions: [1.3, 1.2]    │   │
  │     │   key_share: [X25519 public key]    │   │
  │     │   server_name: "example.com"        │   │
  │     └──────────────────────────────────────┘   │
  │                                                │
  │◀─── ServerHello ────────────────────────────── │
  │     ┌──────────────────────────────────────┐   │
  │     │ TLS Version: 1.3 (agreed)            │   │
  │     │ Random: 32 bytes                     │   │
  │     │ Cipher: TLS_AES_256_GCM_SHA384       │   │
  │     │ key_share: [Server X25519 pub key]  │   │
  │     └──────────────────────────────────────┘   │
  │                                                │
  │  [BOTH sides compute shared secret using ECDH] │
  │  [Handshake keys derived, everything below     │
  │   is ENCRYPTED from here]                      │
  │                                                │
  │◀═══ {EncryptedExtensions} ══════════════════ ══│
  │◀═══ {Certificate} ══════════════════════════ ══│
  │     (Server's X.509 certificate, signed by CA) │
  │◀═══ {CertificateVerify} ════════════════════ ══│
  │     (Signature over handshake transcript)      │
  │◀═══ {Finished} ═════════════════════════════ ══│
  │     (HMAC of entire handshake)                 │
  │                                                │
  │════ {Finished} ════════════════════════════════▶
  │     (Client's HMAC of handshake)               │
  │                                                │
  │  [Application traffic keys derived]            │
  │                                                │
  │════ {Application Data} ════════════════════════▶  (ENCRYPTED)
  │◀═══ {Application Data} ════════════════════════   (ENCRYPTED)
```

> TLS 1.3 completes in **1 Round Trip** (1-RTT) vs TLS 1.2's 2-RTT.
> With session resumption (0-RTT), returning clients skip the handshake entirely.

### DNS Resolution (UDP Wire Diagram)

```
CLIENT (192.168.1.5:12345)              DNS SERVER (8.8.8.8:53)
  │                                              │
  │──── UDP DATAGRAM ───────────────────────────▶│
  │     ┌───────────────────────────────────┐    │
  │     │ ID: 0x1234                        │    │
  │     │ Flags: 0x0100 (Standard Query)    │    │
  │     │ Questions: 1                      │    │
  │     │ QNAME: api.example.com            │    │
  │     │ QTYPE: A (IPv4 Address)           │    │
  │     │ QCLASS: IN (Internet)             │    │
  │     └───────────────────────────────────┘    │
  │                                              │
  │◀─── UDP DATAGRAM ─────────────────────────── │
  │     ┌───────────────────────────────────┐    │
  │     │ ID: 0x1234 (same as query)        │    │
  │     │ Flags: 0x8180 (Standard Response) │    │
  │     │ Questions: 1                      │    │
  │     │ Answer RRs: 1                     │    │
  │     │ ANSWER:                           │    │
  │     │   NAME: api.example.com           │    │
  │     │   TYPE: A                         │    │
  │     │   TTL: 300 seconds                │    │
  │     │   RDATA: 203.0.113.10             │    │
  │     └───────────────────────────────────┘    │
```

### IP Packet Header (Real Wire Format)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Protocol field values:
  1  = ICMP
  6  = TCP
  17 = UDP
  41 = IPv6 encapsulation
  89 = OSPF
```

---

## 7. L4 Load Balancer — Architecture & Internals

### How L4 Load Balancing Works

An L4 LB acts at the **Transport Layer**. When a new TCP SYN arrives, the LB:

1. Reads the 5-tuple: `{src_ip, src_port, dst_ip, dst_port, protocol}`
2. Applies a load balancing algorithm to select a backend
3. **Either:**
   - **NAT mode**: Rewrites destination IP/port, forwards packet
   - **Proxy mode**: Terminates the TCP connection, opens new one to backend
   - **DSR mode**: Doesn't rewrite, backend replies directly to client

### L4 NAT Mode (Network Address Translation)

```
CLIENT                    L4 LOAD BALANCER               BACKEND
IP: 10.0.0.5              VIP: 203.0.113.10              IP: 10.0.1.3
Port: 52341               DIP: 10.0.0.1                  Port: 8080


SYN packet arrives at LB:
  src: 10.0.0.5:52341
  dst: 203.0.113.10:443

LB rewrites destination:
  src: 10.0.0.5:52341    (unchanged)
  dst: 10.0.1.3:8080     (changed!)

LB writes to its connection table:
  { 10.0.0.5:52341 → 10.0.1.3:8080 }

All subsequent packets for this flow go to same backend.

Return packets:
  src: 10.0.1.3:8080     → LB rewrites to: src: 203.0.113.10:443
  dst: 10.0.0.5:52341    →                 dst: 10.0.0.5:52341
```

### L4 Connection Table (Flow Table)

The most critical data structure in an L4 LB is the **connection table** (also called flow table):

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Connection Table                               │
├───────────────────┬──────────────────┬──────────────────┬─────────────┤
│   Client 5-tuple  │  Backend 5-tuple │  State           │  Timestamp  │
├───────────────────┼──────────────────┼──────────────────┼─────────────┤
│ 10.0.0.5:52341    │ 10.0.1.3:8080    │ ESTABLISHED      │ T+0s        │
│ 10.0.0.7:43210    │ 10.0.1.1:8080    │ ESTABLISHED      │ T+1s        │
│ 10.0.0.9:60001    │ 10.0.1.2:8080    │ TIME_WAIT        │ T+120s      │
│ 10.0.0.2:55000    │ 10.0.1.3:8080    │ SYN_SENT         │ T+2s        │
└───────────────────┴──────────────────┴──────────────────┴─────────────┘

This table enables the LB to route ALL packets of the same TCP connection
to the SAME backend — even though subsequent packets have no SYN flag.
Without this table, every packet would be independently load balanced,
breaking TCP entirely.
```

### L4 DSR Mode (Direct Server Return)

**DSR** = Direct Server Return. A clever optimization where the backend responds **directly** to
the client, bypassing the LB for return traffic.

```
                    ┌─────────────────────────────────────────┐
                    │             L4 Load Balancer            │
                    │             VIP: 203.0.113.10           │
                    └────────────────┬────────────────────────┘
                                     │ (forward only, lightweight)
         ┌───────────────────────────┼────────────────────────┐
         ▼                           ▼                        ▼
   Backend 1                   Backend 2                Backend 3
   10.0.1.1                    10.0.1.2                 10.0.1.3
   (also has VIP               (also has VIP            (also has VIP
    on loopback!)               on loopback!)            on loopback!)

Flow:
1. Client → LB:       src=Client, dst=203.0.113.10
2. LB → Backend:      src=Client, dst=203.0.113.10 (UNCHANGED!)
   (LB uses MAC-level rewrite, not IP rewrite)
3. Backend → Client:  src=203.0.113.10, dst=Client  (DIRECT! LB bypassed)

Why DSR is faster:
  - LB only handles INCOMING traffic, not responses
  - Response traffic (typically 10x larger) bypasses LB
  - LB doesn't become a bottleneck
  - Lower latency (one fewer hop for responses)

Requirements:
  - All backends must have the VIP configured on loopback interface
  - Only works in same L2 network (LAN/VLAN)
```

---

## 8. L7 Load Balancer — Architecture & Internals

### How L7 Load Balancing Works

An L7 LB is a **full HTTP proxy**. It terminates the client's TCP+TLS connection completely,
reads the HTTP request, makes a routing decision, and opens a **new** connection to the backend.

```
CLIENT                    L7 LOAD BALANCER               BACKEND
                          (Full HTTP Proxy)

TCP Connection 1:                        TCP Connection 2:
  Client ◀════════════ LB                LB ════════════▶ Backend

TLS Connection 1:                        TLS Connection 2 (or plain):
  Client ◀════════════ LB                LB ════════════▶ Backend

HTTP Request:
  Client ──[GET /api/users]──▶ LB
           LB reads: URL = /api/users
           LB decides: route to "User Service" pool
           LB ──[GET /api/users]──▶ Backend (User Service pool)
```

### L7 Routing Rules — Content-Based Routing

```
┌─────────────────────────────────────────────────────────────────────┐
│                    L7 Routing Rule Engine                           │
├─────────────────────────────────────────────────────────────────────┤
│  Rule 1: Host == "api.example.com" AND Path starts with "/v1"       │
│    → Route to: API v1 Pool (10.0.1.10, 10.0.1.11, 10.0.1.12)       │
├─────────────────────────────────────────────────────────────────────┤
│  Rule 2: Host == "api.example.com" AND Path starts with "/v2"       │
│    → Route to: API v2 Pool (10.0.2.10, 10.0.2.11)                  │
├─────────────────────────────────────────────────────────────────────┤
│  Rule 3: Host == "static.example.com"                               │
│    → Route to: CDN / Static File Servers                            │
├─────────────────────────────────────────────────────────────────────┤
│  Rule 4: Cookie "canary=true" is present                            │
│    → Route to: Canary Pool (5% of servers running new version)      │
├─────────────────────────────────────────────────────────────────────┤
│  Rule 5: Header "X-Internal: yes" is present                        │
│    → Route to: Internal API Pool (no rate limiting)                 │
├─────────────────────────────────────────────────────────────────────┤
│  Default: Route to: Main Pool                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### L7 Connection Flow — Detailed

```
Client         L7 LB          Backend Pool          Backend Server
  │              │                  │                      │
  │──SYN────────▶│                  │                      │
  │◀─SYN-ACK────│                  │                      │
  │──ACK────────▶│                  │                      │
  │              │                  │                      │
  │══TLS Hello══▶│                  │                      │
  │◀═TLS Cert═══│                  │                      │
  │══TLS Fin════▶│                  │                      │
  │              │                  │                      │
  │──HTTP GET───▶│                  │                      │
  │              │                  │                      │
  │              │ [reads headers]  │                      │
  │              │ [applies rules]  │                      │
  │              │ [picks backend]──▶                      │
  │              │                  │──check pool──────────▶
  │              │                  │                      │
  │              │◀─────────────────│  (from connection    │
  │              │ (get connection) │   pool if available) │
  │              │                  │                      │
  │              │──────────HTTP GET (forwarded)──────────▶│
  │              │◀──────────HTTP 200 OK──────────────────│
  │              │                  │                      │
  │◀─HTTP 200───│                  │                      │
```

### L7 Capabilities — What Makes It Powerful

#### 1. Header Manipulation

```
Incoming request:
  GET /api/user HTTP/1.1
  Host: example.com

LB adds before forwarding:
  GET /api/user HTTP/1.1
  Host: example.com
  X-Forwarded-For: 10.0.0.5          ← Original client IP
  X-Forwarded-Proto: https           ← Was HTTPS to LB
  X-Request-ID: 7f3d9e2a-1b4c-4d8e  ← Generated by LB for tracing
  X-Real-IP: 10.0.0.5
```

#### 2. Rate Limiting

```
LB tracks requests per client IP or API key:

Rate Limit Table:
  10.0.0.5 (API key: abc123): 95/100 req/min  ← allow
  10.0.0.7 (API key: xyz789): 100/100 req/min ← block, return 429
  10.0.0.9 (no key):          50/60 req/min   ← allow

When limit exceeded, LB responds directly without forwarding:
  HTTP/1.1 429 Too Many Requests
  Retry-After: 30
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 0
```

#### 3. Authentication Offloading

```
Client ──JWT Token in header──▶ L7 LB
                                  │
                                  ├── Verify JWT signature (LB has public key)
                                  ├── Check expiry
                                  ├── Check claims
                                  │
                          Valid ──┼── Forward to backend
                                  │    (add X-User-ID: 42 header)
                        Invalid ──┼── Return 401 immediately
                                  │   (backend never sees bad requests)
```

#### 4. A/B Testing and Canary Deployments

```
Traffic Split:
┌──────────────────────────────────────────────────────┐
│ Rule: 90% → Stable Pool (v1.2.0)                     │
│        5% → Canary Pool (v1.3.0-beta)                │
│        5% → Experiment Pool (v1.4.0-alpha)           │
│                                                      │
│ Based on: consistent hashing on user_id cookie       │
│ (same user always goes to same pool — reproducible!) │
└──────────────────────────────────────────────────────┘
```

---

## 9. Load Balancing Algorithms

### 1. Round Robin

Each new request goes to the next server in a circular list.

```
Servers: [A, B, C]
Request 1 → A
Request 2 → B
Request 3 → C
Request 4 → A  ← wraps around
Request 5 → B
...

State:
  current_index = 0
  On each request: server = servers[current_index % len(servers)]
                   current_index++

Problem: Ignores server capacity.
  If A has 8GB RAM and C has 64GB RAM, they get equal traffic.
```

### 2. Weighted Round Robin

Servers have weights proportional to their capacity.

```
Servers: [A(weight=1), B(weight=2), C(weight=3)]
Total weight = 6

Distribution over 6 requests:
  Request 1 → A
  Request 2 → B
  Request 3 → B
  Request 4 → C
  Request 5 → C
  Request 6 → C
  (then repeats)

Why this matters:
  A: 1/6 = 16.7% of traffic (small server)
  B: 2/6 = 33.3% of traffic (medium server)
  C: 3/6 = 50.0% of traffic (large server)
```

### 3. Least Connections

Route to the server with **fewest active connections** right now.

```
Servers and their current connections:
  A: 150 connections
  B: 23 connections   ← next request goes here
  C: 97 connections

Why better than Round Robin:
  Round Robin ignores slow requests.
  If A has 150 slow requests (each taking 5 seconds),
  Round Robin might still send 1/3 of traffic to A.
  Least Connections sees A is busy and avoids it.

Formula: score(server) = active_connections(server) / weight(server)
         pick server with lowest score
```

### 4. IP Hash (Source IP Affinity)

The client's IP is hashed to consistently pick the same backend.

```
hash(client_ip) % num_servers = backend_index

Example:
  hash("10.0.0.5") % 3 = 1  → always Backend B
  hash("10.0.0.7") % 3 = 0  → always Backend A
  hash("10.0.0.9") % 3 = 2  → always Backend C

Problem: If a backend dies:
  hash("10.0.0.5") % 2 = 1  → now goes to C instead of B!
  ALL clients are remapped when any server changes.
  Solution: Consistent Hashing (below)
```

### 5. Consistent Hashing

A smarter hashing algorithm where adding/removing a server only remaps **1/N** of clients
(not all of them).

```
Concept: Hash Ring
  - Hash space is [0, 2^32) arranged in a circle
  - Each server is placed on the ring at hash(server_ip)
  - Each request hashes its key, lands on ring, walks clockwise to next server

           0
    ┌──────┴──────────────────────────────────────────────┐
    │                                                      │
  Server A                                             Server D
  (hash=100)                                          (hash=900)
    │                                                      │
    │               Ring                                   │
    │                                                      │
  Server B                                             Server C
  (hash=350)                                          (hash=700)
    │                                                      │
    └──────────────────────────────────────────────────────┘
                         2^32

Request with hash=200 → walk clockwise from 200 → hits Server B (hash=350)
Request with hash=500 → walk clockwise from 500 → hits Server C (hash=700)
Request with hash=950 → walk clockwise from 950 → wraps to Server A (hash=100)

If Server B (hash=350) is removed:
  Only requests that were going to B now go to C (next clockwise)
  All other requests are UNAFFECTED
```

### 6. Random with Two Choices (Power of Two Choices)

Pick **2 random servers**, then choose the one with fewer connections.

```
Servers: [A(50), B(120), C(30), D(80), E(10)]

Pick random two: B(120) and D(80)
Choose: D (fewer connections)

Why better than just random:
  Pure random: might pick B(120) even though E(10) is idle
  Two choices: statistically much better distribution
  Proven to perform close to optimal with far less coordination overhead

This is used in systems like Nginx when consistent hashing isn't needed
and you want to avoid the coordination overhead of tracking all connections.
```

### 7. Resource-Based (Adaptive)

The LB periodically asks each backend its current resource usage and routes accordingly.

```
Backend reports (via health check response headers or separate channel):
  A: CPU=23%, Memory=40%, Connections=150, Latency_p99=12ms
  B: CPU=85%, Memory=78%, Connections=300, Latency_p99=250ms  ← avoid!
  C: CPU=41%, Memory=55%, Connections=200, Latency_p99=35ms

LB computes a composite score:
  score = w1*cpu + w2*memory + w3*connections + w4*latency
  
Lower score = healthier = gets more traffic.
```

---

## 10. Health Checks

Health checks are how the LB knows which backends are alive and ready.

### Types of Health Checks

#### L4 Health Check (TCP Ping)

```
LB → Backend: TCP SYN to port 8080
Backend → LB: SYN-ACK (port is open)
LB → Backend: RST (immediately close)
Result: Port is open → mark as HEALTHY

Limitation: Doesn't tell you if the app is actually working,
just that the TCP port is listening.
```

#### L7 Health Check (HTTP Probe)

```
LB ──GET /health HTTP/1.1──▶ Backend
Backend ──HTTP/1.1 200 OK──▶ LB
         Body: {"status":"ok","db":"connected","cache":"connected"}

LB checks:
  - Status code is 2xx? ✓
  - Body contains "status":"ok"? ✓
  - Response time < 2000ms? ✓
  → Mark HEALTHY

If backend returns 500 or times out → mark UNHEALTHY → remove from pool
```

#### Health Check State Machine

```
               ┌─────────────────────────────────────────┐
               │                                         │
               ▼                                         │
         ┌──────────┐     fail_threshold=3 failures   ┌──────────┐
  ──────▶│ HEALTHY  │──────────────────────────────────▶│UNHEALTHY│
         └──────────┘                                  └──────────┘
               ▲                                           │
               │   pass_threshold=2 successes             │
               └───────────────────────────────────────────┘
                                              │
                                              ▼
                                        ┌──────────┐
                                        │  DRAINING│ ← In-flight requests
                                        │          │   complete, no new ones
                                        └──────────┘

Typical config:
  interval:          5 seconds (check every 5s)
  timeout:           2 seconds (wait 2s for response)
  unhealthy_threshold: 3 (fail 3 times → unhealthy)
  healthy_threshold:   2 (pass 2 times → healthy again)
```

---

## 11. SSL/TLS Termination

### The Three TLS Configurations

#### Option A: SSL Termination (Most Common)

```
Client ◀═══════TLS═══════▶ LB ◀───────HTTP───────▶ Backend

- LB holds the certificate and private key
- LB decrypts all client traffic
- LB-to-backend is plain HTTP (no encryption)
- Backend in protected data center, so HTTP is fine
- LB can inspect HTTP content → enables L7 features
- All SSL processing overhead on LB

Pro:  LB can do L7 routing, rate limiting, etc.
Pro:  Backends don't need certificates
Con:  Traffic is unencrypted inside the datacenter
Con:  LB has private key → security risk if LB is compromised
```

#### Option B: SSL Passthrough

```
Client ◀═══════TLS═══════════════════════════════▶ Backend

- LB sees only encrypted bytes — cannot read HTTP
- LB routes based on TLS SNI (Server Name Indication)
- Backend holds certificate and private key
- This is actually L4 load balancing, not L7

What is SNI?
  SNI is an extension in the TLS ClientHello that tells the server
  which hostname the client is trying to reach — before the
  certificate is sent. This allows multiple HTTPS sites on one IP.

  ClientHello contains:
    server_name: "api.example.com"
  LB routes based on this name (from TLS header, not HTTP header)

Pro:  End-to-end encryption
Pro:  LB cannot see/modify traffic
Con:  No L7 features possible
Con:  Backend manages certificates
```

#### Option C: SSL Re-encryption (Bridge)

```
Client ◀═══TLS 1═══▶ LB ◀═══TLS 2═══▶ Backend

- LB terminates client TLS (can inspect HTTP)
- LB opens a NEW TLS connection to backend
- Two separate TLS sessions
- LB has its own cert (for clients)
- Backend has its own cert (for LB-to-backend)

Pro:  Full end-to-end encryption
Pro:  L7 features still possible
Con:  Double TLS overhead
Con:  Complex certificate management
Use:  Regulatory requirements (PCI-DSS, HIPAA)
```

---

## 12. Sticky Sessions (Session Persistence)

### The Problem

HTTP is stateless. But many applications store session state in server memory:

```
Without Sticky Sessions:
  User logs in: Request → Backend A  (A creates session, stores in RAM)
  Next request: Request → Backend B  (B doesn't know this session!)
  → User gets logged out! 

With Sticky Sessions:
  User logs in: Request → Backend A  (A creates session)
  Next request: Request → Backend A  (LB ensures same backend)
  Next request: Request → Backend A  (same backend again)
```

### Cookie-Based Stickiness

```
First Request:
  Client ──GET /────────────────────────────────────▶ LB
  LB routes to Backend A (10.0.1.1)
  Backend A responds:
    HTTP/1.1 200 OK
    Set-Cookie: JSESSIONID=abc123
  LB adds its own stickiness cookie:
    Set-Cookie: SERVERID=backend_A; Path=/; HttpOnly
  LB returns both cookies to client

Subsequent Requests:
  Client ──GET /dashboard──────────────────────────▶ LB
  Cookie: JSESSIONID=abc123; SERVERID=backend_A
  LB reads SERVERID=backend_A → routes to Backend A always
```

### IP-Based Stickiness

```
hash(client_ip) → consistent backend selection
Simple but breaks when client's IP changes (NAT, mobile network switch)
```

### Problem with Sticky Sessions

```
Backend A (10.0.1.1) has 10,000 sticky users  ← overloaded!
Backend B (10.0.1.2) has 2,000 sticky users
Backend C (10.0.1.3) has 1,000 sticky users  ← underloaded

If a popular user or IP is sticky to A, you can't rebalance.
This is why modern architectures prefer STATELESS backends:
  - Store sessions in a shared cache (Redis)
  - Use JWT tokens (session state in the token itself)
  - Any backend can serve any request
```

---

## 13. Connection Pooling

### The Problem with Naive Forwarding

Without connection pooling, every client request creates a NEW TCP (+ TLS) connection to the backend:

```
Client Request 1 → LB → [NEW TCP+TLS HANDSHAKE] → Backend
Client Request 2 → LB → [NEW TCP+TLS HANDSHAKE] → Backend
Client Request 3 → LB → [NEW TCP+TLS HANDSHAKE] → Backend

TLS Handshake cost: ~100ms, 3+ round trips
1000 requests/sec = 1000 TCP+TLS handshakes/sec to backend
Backend overwhelmed by handshakes!
```

### Connection Pool Architecture

```
                    ┌─────────────────────────────────────┐
                    │          L7 LOAD BALANCER            │
                    │                                     │
Client Pool         │         Backend Connection Pool     │
(many short         │         (few, long-lived)           │
 connections)       │                                     │
                    │  ┌────────────────────────────┐     │
 C1 ══HTTP/2══════════▶│  Pool to Backend A:        │     │
 C2 ══HTTP/2══════════▶│  Conn1: IDLE               │═══▶A│
 C3 ══HTTP/1.1════════▶│  Conn2: IN_USE (C1's req)  │═══▶A│
                    │  │  Conn3: IN_USE (C2's req)  │═══▶A│
                    │  │  Conn4: IDLE               │═══▶A│
                    │  └────────────────────────────┘     │
                    │                                     │
                    │  ┌────────────────────────────┐     │
                    │  │  Pool to Backend B:        │     │
                    │  │  Conn1: IN_USE (C3's req)  │═══▶B│
                    │  │  Conn2: IDLE               │═══▶B│
                    │  └────────────────────────────┘     │
                    └─────────────────────────────────────┘

Benefits:
  - Amortize TCP/TLS handshake cost across thousands of requests
  - Backend sees constant N connections instead of spiky new connections
  - LB manages connection lifecycle (reconnect on failure)
```

---

## 14. L4 vs L7 — Head-to-Head Comparison

```
┌──────────────────────────────────┬───────────────────────────┬───────────────────────────┐
│ Feature                          │ L4 Load Balancer          │ L7 Load Balancer          │
├──────────────────────────────────┼───────────────────────────┼───────────────────────────┤
│ OSI Layer                        │ 4 (Transport)             │ 7 (Application)           │
│ Protocols                        │ TCP, UDP                  │ HTTP, HTTPS, WS, gRPC     │
│ What it sees                     │ IP, Port, TCP flags only  │ Full HTTP headers + body  │
│ Routing basis                    │ IP + Port (5-tuple)       │ URL, headers, cookies     │
│ Connection handling              │ Transparent or proxied    │ Always full proxy         │
│ TLS termination                  │ No (passthrough only)     │ Yes                       │
│ Content inspection               │ No                        │ Yes                       │
│ Header manipulation              │ No                        │ Yes (add/remove/modify)   │
│ URL-based routing                │ No                        │ Yes                       │
│ Cookie-based routing             │ No                        │ Yes                       │
│ Rate limiting                    │ Limited (by IP only)      │ Full (URL, API key, etc.) │
│ Authentication offload           │ No                        │ Yes                       │
│ WebSocket support                │ Yes (transparent)         │ Yes (with upgrade)        │
│ gRPC support                     │ Yes (transparent)         │ Yes (native)              │
│ Performance (latency)            │ Very Low (~microseconds)  │ Low (~milliseconds)       │
│ Performance (throughput)         │ Extremely High            │ High                      │
│ CPU usage                        │ Very Low                  │ Higher (parsing HTTP)     │
│ Memory usage                     │ Low (small flow table)    │ Higher (connection state) │
│ Encryption visibility            │ No (can't decrypt)        │ Yes (must terminate TLS)  │
│ Non-HTTP protocols               │ Yes (any TCP/UDP)         │ No (HTTP family only)     │
│ Database load balancing          │ Yes (MySQL, PostgreSQL)   │ No                        │
│ Game server load balancing       │ Yes (UDP)                 │ No                        │
│ Observability (metrics)          │ Connection-level only     │ Request-level (p99, etc.) │
│ Logging granularity              │ Connection logs           │ Per-request logs          │
│ Canary deployments               │ No (coarse)               │ Yes (per-request control) │
│ A/B testing                      │ No                        │ Yes                       │
│ Typical tools                    │ LVS, IPVS, AWS NLB        │ Nginx, HAProxy, Envoy     │
│ Cloud examples                   │ AWS NLB, GCP TCP LB       │ AWS ALB, GCP HTTP LB      │
└──────────────────────────────────┴───────────────────────────┴───────────────────────────┘
```

### When to Use L4

- **Non-HTTP protocols**: Database connections (MySQL, PostgreSQL, Redis), SMTP, custom TCP
- **Extreme performance needed**: Millions of connections/sec, sub-millisecond latency
- **UDP traffic**: DNS, gaming, QUIC, media streaming
- **You don't need to inspect application content**
- **End-to-end encryption is required** and you can't terminate TLS at the LB
- **Simple infrastructure**: Fewer moving parts, easier to operate

### When to Use L7

- **Microservices routing**: Route `/api/users` to User Service, `/api/orders` to Order Service
- **Multi-tenant SaaS**: Route based on `Host:` header or subdomain
- **Advanced traffic management**: Canary, blue-green, A/B testing
- **Security**: JWT validation, rate limiting per API key, WAF integration
- **Observability**: Per-request metrics, distributed tracing
- **WebSocket or gRPC**: Requires understanding application protocol
- **SSL termination**: Offload TLS from backends

### Layered Architecture (Real World)

In practice, production systems use **both**:

```
Internet Traffic
       │
       ▼
┌─────────────┐
│  L4 LB      │  ← DDoS protection, raw TCP flood mitigation
│  (AWS NLB)  │    Routes TCP connections to L7 fleet
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  L7 LB      │  ← TLS termination, routing, auth, rate limiting
│  (Nginx /   │    Routes HTTP requests to microservices
│   Envoy)    │
└──────┬──────┘
       │
       ├──────────────────────────────────────────────┐
       ▼                         ▼                    ▼
┌─────────────┐         ┌─────────────┐       ┌─────────────┐
│  User Svc   │         │  Order Svc  │       │  Auth Svc   │
│  Instances  │         │  Instances  │       │  Instances  │
└─────────────┘         └─────────────┘       └─────────────┘
```

---

## 15. Real-World Tools & Systems

### HAProxy

HAProxy is the reference implementation for both L4 and L7 load balancing. Written in C,
it is famous for extreme performance and feature richness.

```haproxy
# haproxy.cfg — Example configuration

global
    maxconn 100000
    log /dev/log local0
    user haproxy
    group haproxy

defaults
    mode http                    # L7 mode (use 'tcp' for L4)
    timeout connect 5s
    timeout client  30s
    timeout server  30s
    option http-server-close     # Close server connection, reuse client
    option forwardfor            # Add X-Forwarded-For header

frontend web_frontend
    bind *:443 ssl crt /etc/ssl/example.com.pem  # TLS termination
    default_backend web_backends

    # L7 routing rules
    acl is_api path_beg /api/
    acl is_admin path_beg /admin/
    acl is_static path_beg /static/

    use_backend api_backends    if is_api
    use_backend admin_backends  if is_admin
    use_backend static_backends if is_static

backend api_backends
    balance leastconn           # Algorithm: Least Connections
    option httpchk GET /health  # L7 health check
    http-check expect status 200
    server api1 10.0.1.1:8080 check weight 1
    server api2 10.0.1.2:8080 check weight 2
    server api3 10.0.1.3:8080 check weight 2

backend admin_backends
    balance roundrobin
    option httpchk GET /healthz
    server admin1 10.0.2.1:8080 check
    server admin2 10.0.2.2:8080 check backup  # Only used if admin1 fails

backend static_backends
    balance uri                 # Hash based on URL (cache efficiency)
    server static1 10.0.3.1:80 check
    server static2 10.0.3.2:80 check
    server static3 10.0.3.3:80 check
```

### Nginx (as Load Balancer)

```nginx
# nginx.conf — Upstream load balancing

http {
    # Define upstream pools
    upstream api_servers {
        least_conn;                     # Algorithm

        server 10.0.1.1:8080 weight=1;
        server 10.0.1.2:8080 weight=2;
        server 10.0.1.3:8080 weight=2 backup;  # Only if others fail
        server 10.0.1.4:8080 down;             # Manually disabled

        keepalive 32;  # Connection pool: 32 idle connections per worker
    }

    upstream ws_servers {
        ip_hash;  # Sticky by IP (for WebSocket)
        server 10.0.2.1:8080;
        server 10.0.2.2:8080;
    }

    server {
        listen 443 ssl http2;
        ssl_certificate     /etc/nginx/certs/example.com.crt;
        ssl_certificate_key /etc/nginx/certs/example.com.key;
        ssl_protocols       TLSv1.2 TLSv1.3;

        # Routing rules
        location /api/ {
            proxy_pass http://api_servers;
            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 5s;
            proxy_read_timeout    60s;
        }

        location /ws/ {
            proxy_pass http://ws_servers;
            proxy_http_version 1.1;
            proxy_set_header Upgrade    $http_upgrade;  # WebSocket
            proxy_set_header Connection "Upgrade";
        }
    }
}

# L4 (TCP stream) load balancing
stream {
    upstream mysql_servers {
        server 10.0.3.1:3306;
        server 10.0.3.2:3306;
    }

    server {
        listen 3306;
        proxy_pass mysql_servers;
    }
}
```

### Envoy Proxy

Envoy is the data plane for service meshes (Istio, etc.). It is written in C++ and has
extremely powerful L7 features including native gRPC, distributed tracing, and circuit breaking.

```
Key Envoy Concepts:

  Listener:     Port + address Envoy listens on
  Filter Chain: Ordered list of filters applied to each connection
  Router:       Matches requests to clusters
  Cluster:      A group of backend endpoints
  Endpoint:     Individual backend server

L7 Filter Pipeline:
  Connection
       │
       ▼
  ┌──────────────┐
  │  TLS Filter  │  ← Terminates TLS
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ HTTP Filter  │  ← Parses HTTP
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ Rate Limit   │  ← Checks rate limit
  │ Filter       │
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ JWT Auth     │  ← Validates JWT token
  │ Filter       │
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ Router       │  ← Selects cluster, routes request
  │ Filter       │
  └──────────────┘
```

### AWS Load Balancers

| AWS Service | OSI Layer | Protocol       | Use Case                               |
|-------------|-----------|----------------|----------------------------------------|
| **NLB**     | L4        | TCP, UDP, TLS  | Ultra-low latency, non-HTTP, static IP |
| **ALB**     | L7        | HTTP, HTTPS, WS, gRPC | Microservices, URL routing       |
| **CLB**     | L4 + L7   | TCP, HTTP      | Legacy (deprecated for new deployments)|
| **GWLB**    | L3        | Any            | Network appliance (firewall, IDS)      |

---

## 16. Advanced Topics

### Circuit Breaker Pattern

A circuit breaker prevents a failed backend from receiving traffic until it recovers.
It is implemented at the LB level (like Envoy) or application level (like Hystrix).

```
States:

CLOSED (normal operation)
  ─────────────────────────────────────────────────────▶
  Requests pass through to backend
  LB counts failures: 0/10, 1/10, 2/10 ...
  
  threshold exceeded (5 failures in 10 seconds)?
  → OPEN

OPEN (backend considered failed)
  ─────────────────────────────────────────────────────▶
  ALL requests immediately fail with 503
  Backend gets ZERO traffic (time to recover!)
  
  After timeout (30 seconds)?
  → HALF-OPEN

HALF-OPEN (testing recovery)
  ─────────────────────────────────────────────────────▶
  ONE request allowed through as probe
  
  Probe succeeds? → CLOSED (backend is healthy again)
  Probe fails?    → OPEN (wait another 30 seconds)

State Diagram:

  ┌──────────┐  error_rate > threshold  ┌──────────┐
  │  CLOSED  │─────────────────────────▶│   OPEN   │
  └──────────┘                          └──────────┘
       ▲                                     │
       │                                     │ timeout expires
       │                               ┌─────▼─────┐
       └───────────────────────────────│ HALF-OPEN │
              probe succeeds           └───────────┘
```

### Service Mesh and Sidecar Pattern

In a **service mesh**, every microservice instance gets a sidecar proxy (Envoy) deployed
alongside it. The sidecar handles all L7 concerns.

```
Without Service Mesh:
  ┌───────────────────────────────────────────────────────┐
  │  User Service Pod                                     │
  │   ┌──────────────────────────────────────────────┐   │
  │   │  App Code (Go/Rust/etc.)                     │   │
  │   │  Must handle: TLS, auth, retry, circuit break│   │
  │   │  Must include: service discovery library     │   │
  │   └──────────────────────────────────────────────┘   │
  └───────────────────────────────────────────────────────┘

With Service Mesh (Istio/Envoy):
  ┌───────────────────────────────────────────────────────┐
  │  User Service Pod                                     │
  │   ┌──────────────┐        ┌──────────────────────┐   │
  │   │  App Code    │◀──────▶│  Envoy Sidecar       │   │
  │   │  (pure biz   │        │  handles:            │   │
  │   │   logic)     │        │  - mTLS              │   │
  │   │              │        │  - load balancing    │   │
  │   │              │        │  - circuit breaking  │   │
  │   │              │        │  - tracing           │   │
  │   └──────────────┘        └──────────────────────┘   │
  └───────────────────────────────────────────────────────┘

mTLS = mutual TLS: both sides verify each other's certificates
       → automatic service-to-service authentication
```

### Global Server Load Balancing (GSLB)

GSLB distributes traffic across **multiple data centers** in different geographic regions.

```
Client in Tokyo requests api.example.com:

Step 1: DNS Query
  Client ──DNS?──▶ Local Resolver ──DNS?──▶ GSLB DNS (ns1.example.com)

Step 2: GSLB DNS Decision
  GSLB checks:
    - Client geo-IP: Tokyo, Japan
    - Data center latencies: Tokyo DC=5ms, US-West DC=120ms, EU DC=250ms
    - Data center health: Tokyo=OK, US-West=OK, EU=OK
    - Data center load: Tokyo=30%, US-West=80%, EU=20%
  
  Decision: Tokyo DC is closest and healthy → return Tokyo DC IP

Step 3: DNS Response
  GSLB ──▶ Client: "api.example.com → 103.42.1.10 (Tokyo DC)"
  TTL: 30 seconds (short, so failover is fast)

Step 4: Client connects directly to Tokyo DC
  Client ──────────────────────────────────▶ Tokyo LB ──▶ Tokyo Backends
```

### Anycast Routing

**Anycast** is a routing technique where the same IP address is announced from multiple
data centers, and the network (BGP routing) automatically directs clients to the **nearest** one.

```
Same IP: 1.1.1.1 announced from:
  - Cloudflare's data center in New York
  - Cloudflare's data center in London
  - Cloudflare's data center in Singapore
  - Cloudflare's data center in São Paulo

Client in Mumbai:
  BGP routing finds shortest path → Singapore DC handles request

Client in Paris:
  BGP routing finds shortest path → London DC handles request

Benefits:
  - No DNS tricks needed (unlike GSLB)
  - Works at network layer (L3)
  - Automatic failover: if Singapore goes down,
    Mumbai clients are rerouted to nearest surviving DC
  - Used by: CDNs, DNS providers, DDoS mitigation
```

### The Thundering Herd Problem

```
Scenario: All backends crash simultaneously.
          Health checks detect failure.
          All backends recover simultaneously.
          
Result: Thousands of clients reconnect AT THE SAME TIME.
        Each backend receives a massive spike.
        Some may fail again due to the spike.
        Oscillation occurs (crash → recover → crash).

Solutions:
  1. Jitter: Add random delay to reconnect/retry
     retry_delay = base_delay + random(0, max_jitter)
  
  2. Exponential Backoff: Double the wait time on each failure
     wait = min(base * 2^attempt, max_wait)
  
  3. Gradual Traffic Restoration:
     LB slowly increases traffic to recovering backend:
     0% → 10% → 25% → 50% → 100% (over several seconds)
```

### Slow Loris Attack (L7 DDoS)

An attacker sends HTTP requests very slowly, keeping connections open indefinitely.

```
Normal client:
  ──GET / HTTP/1.1\r\nHost: x.com\r\n\r\n──▶  (sent in ~1ms)

Slow Loris attack:
  ──GET /──▶  (waits 10 seconds)
  ──H──▶ (waits 10 seconds)
  ──o──▶ (waits 10 seconds)
  ──s──▶ ... (never finishes the request)

Result: LB holds a connection open for each attacker
        With 1000 attackers, 1000 connections occupied
        Real users can't connect (connection limit reached)

Defense:
  - Set client_header_timeout (Nginx: 10s by default)
  - Limit connections per IP
  - Use a CDN (Cloudflare absorbs this at the edge)
  - L4 LB in front can limit connections per source IP
```

---

## 17. Mental Models & Expert Intuition

### The Postal System Mental Model

```
┌────────────────────────────────────────────────────────────┐
│  L4 LOAD BALANCER = Post Office Sorting Room               │
│                                                            │
│  Sees only: Envelope (From address, To address, size)      │
│  Does NOT open the envelope                                │
│  Routes based on: ZIP code (port)                          │
│  Very fast: mechanical sorting, no reading required        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  L7 LOAD BALANCER = Smart Mail Clerk                       │
│                                                            │
│  Opens the envelope and reads the letter                   │
│  Routes based on CONTENT: "This is for Legal Dept"         │
│  Can modify the letter before forwarding                   │
│  Can reject letters that don't meet criteria               │
│  Can stamp the letter with tracking info                   │
│  Slower than sorting room, but much smarter                │
└────────────────────────────────────────────────────────────┘
```

### The Traffic Dispatcher Mental Model

```
L4 = Dispatcher who only sees license plates
     Routes: "All red cars go to Parking Lot A"
             "All blue cars go to Parking Lot B"
     Cannot see: number of passengers, cargo weight

L7 = Dispatcher who talks to the driver
     Routes: "Cargo trucks to loading dock"
             "VIP guests to valet"
             "Delivery vehicles to service entrance"
     Can modify: "Please take this alternate route"
     Can reject: "No entry without reservation"
```

### The Key Decision Framework

```
When designing a system, ask these questions in order:

Q1: Is this HTTP/HTTPS/gRPC/WebSocket?
    NO  → You MUST use L4 (databases, custom protocols, UDP)
    YES → Continue

Q2: Do you need content-based routing?
    (different URLs → different backends)
    YES → Use L7
    NO  → Continue

Q3: Do you need SSL termination at the LB?
    YES → Use L7
    NO  → Continue

Q4: Do you need rate limiting, auth, or header manipulation?
    YES → Use L7
    NO  → Use L4 (simpler, faster)

Q5: Do you need maximum performance (millions of packets/sec)?
    YES → Use L4 (or L4 in front of L7)
    NO  → Either works
```

### Performance Intuition — Numbers to Know

```
L4 LB (kernel bypass, DPDK):
  Throughput:  ~100 Gbps
  PPS:         ~100 million packets/sec
  Latency:     ~10 microseconds
  Connections: ~100 million concurrent

L4 LB (software, kernel):
  Throughput:  ~10-40 Gbps
  PPS:         ~5-20 million packets/sec
  Latency:     ~50-200 microseconds
  Connections: ~1-10 million concurrent

L7 LB (Nginx/Envoy, optimized):
  Throughput:  ~40 Gbps (HTTP/2)
  RPS:         ~500K-2M requests/sec
  Latency:     ~1-5 milliseconds (added by LB)
  Connections: ~100K-1M concurrent HTTP sessions
```

### Chunking and Pattern Recognition — Expert Heuristics

Over time, world-class engineers build these immediate mental associations:

```
Pattern: "App is stateful, sessions in memory"
→ Immediate thought: Need sticky sessions OR migrate to shared session store (Redis)

Pattern: "Traffic suddenly fails with 502/504"
→ Immediate thought: Backend pool degraded, check health check thresholds
   and backend logs for errors

Pattern: "P99 latency is high but P50 is fine"
→ Immediate thought: One or two slow backends dragging the tail
   Check least_conn algorithm and backend outliers

Pattern: "Need to deploy a new version without downtime"
→ Immediate thought: Canary deployment at L7 LB layer
   10% → 25% → 50% → 100% with rollback at each stage

Pattern: "Database connection count exploding"
→ Immediate thought: Missing connection pooling layer (PgBouncer for PostgreSQL)
   Applications opening too many direct connections to DB

Pattern: "Need to handle WebSocket and REST on same domain"
→ Immediate thought: L7 LB routes /ws/* to WebSocket backends
   and /* to REST backends

Pattern: "Service receiving spoofed IPs in logs"
→ Immediate thought: X-Forwarded-For not configured
   or PROXY Protocol not enabled for L4 LB
```

### The PROXY Protocol

When an L4 LB forwards a TCP connection, the backend server loses the original client IP
(it only sees the LB's IP). PROXY Protocol solves this.

```
Without PROXY Protocol:
  Client: 203.0.113.5:54321
  L4 LB: 10.0.0.1
  Backend sees connection from: 10.0.0.1:xxxxx (LB's IP)
  Backend has no idea who the real client is!

With PROXY Protocol v1 (text):
  When L4 LB connects to backend, it PREPENDS:
  "PROXY TCP4 203.0.113.5 10.0.0.3 54321 443\r\n"
  
  Then the real TCP data follows.
  Backend reads this header first → knows real client IP.

With PROXY Protocol v2 (binary):
  Same concept but binary format (12-byte fixed header)
  More efficient, supports more protocols
```

---

## Summary — The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OSI LAYERS REVISITED                             │
├────────────────────────────────────────┬────────────────────────────────┤
│  L7 LOAD BALANCER operates here        │  L4 LOAD BALANCER here         │
│                                        │                                │
│  Layer 7: HTTP, gRPC, WS               │  Layer 4: TCP, UDP             │
│  Layer 6: TLS (terminated here)        │  Layer 3: IP (reads only)      │
│  Layer 5: Sessions (manages)           │  Layer 2+1: untouched          │
│                                        │                                │
│  READS:  URLs, headers, cookies, body  │  READS: IP, port, TCP flags    │
│  WRITES: Modified headers, new cookies │  WRITES: Rewrites IP/port only │
│  DECIDES: Per-request routing          │  DECIDES: Per-connection       │
├────────────────────────────────────────┴────────────────────────────────┤
│                       KEY PROTOCOLS                                     │
│                                                                         │
│  TCP:   Reliable, ordered, connection-oriented. Foundation of web.     │
│  UDP:   Fast, connectionless. Foundation of DNS, gaming, QUIC.         │
│  HTTP/1.1: Text, stateless, one req/connection (or pipelined).         │
│  HTTP/2: Binary, multiplexed streams, header compression (HPACK).     │
│  HTTP/3: QUIC-based (UDP), no HOL blocking, 0-RTT, connection migrate. │
│  TLS 1.3: 1-RTT handshake, mandatory encryption, forward secrecy.     │
│  gRPC:  HTTP/2 + Protobuf. Fast, strict contracts, 4 stream types.    │
│  WS:    Upgrade from HTTP, full-duplex, persistent TCP connection.     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*"The expert programmer does not merely know how systems work — they have internalized WHY
each design choice exists, what problem it solves, and what trade-off it makes. Every protocol
header field exists because someone suffered without it."*

---

