# TCP Protocol — Complete In-Depth Guide
> Transmission Control Protocol · RFC 793 · Updated by RFC 1122, 2581, 5681, 7323, 9293

---

## Table of Contents

1. [What is TCP and Why Does It Exist](#1-what-is-tcp-and-why-does-it-exist)
2. [TCP vs UDP — The Design Philosophy](#2-tcp-vs-udp--the-design-philosophy)
3. [The TCP Segment Structure](#3-the-tcp-segment-structure)
4. [TCP Connection Lifecycle](#4-tcp-connection-lifecycle)
5. [Three-Way Handshake (SYN → SYN-ACK → ACK)](#5-three-way-handshake)
6. [Four-Way Termination (FIN → ACK → FIN → ACK)](#6-four-way-termination)
7. [TCP State Machine — All 11 States](#7-tcp-state-machine--all-11-states)
8. [Sequence Numbers and Acknowledgements](#8-sequence-numbers-and-acknowledgements)
9. [Sliding Window and Flow Control](#9-sliding-window-and-flow-control)
10. [Congestion Control (Tahoe, Reno, CUBIC, BBR)](#10-congestion-control)
11. [Retransmission and Timers](#11-retransmission-and-timers)
12. [TCP Options Field Deep Dive](#12-tcp-options-field-deep-dive)
13. [Nagle's Algorithm and Delayed ACKs](#13-nagles-algorithm-and-delayed-acks)
14. [Keepalive Mechanism](#14-keepalive-mechanism)
15. [TIME_WAIT — The Most Misunderstood State](#15-time_wait--the-most-misunderstood-state)
16. [TCP Half-Open and Half-Closed Connections](#16-tcp-half-open-and-half-closed-connections)
17. [TCP Urgent Data and Out-of-Band Signaling](#17-tcp-urgent-data-and-out-of-band-signaling)
18. [TCP Performance Tuning](#18-tcp-performance-tuning)
19. [TCP Security — Attacks and Defenses](#19-tcp-security--attacks-and-defenses)
20. [TCP in the Pentesting Context](#20-tcp-in-the-pentesting-context)
21. [Wireshark and Packet-Level Inspection](#21-wireshark-and-packet-level-inspection)
22. [Mental Models and Summary](#22-mental-models-and-summary)

---

## 1. What is TCP and Why Does It Exist

TCP (Transmission Control Protocol) was designed by Vint Cerf and Bob Kahn in 1974 and standardized in RFC 793 (1981). It lives at **Layer 4 (Transport Layer)** of the OSI model and sits directly above IP.

### The Core Problem TCP Solves

IP is a **best-effort, connectionless** protocol. It can:
- Drop packets silently
- Deliver packets out of order
- Deliver duplicate packets
- Corrupt data without detection (at its level)

Applications like HTTP, SSH, FTP, SMTP — anything where **every byte must arrive correctly and in order** — cannot tolerate this behavior. TCP was designed to impose reliability on top of the unreliable IP layer.

### TCP's Five Guarantees

| Guarantee | How TCP Achieves It |
|-----------|---------------------|
| **Reliable delivery** | Acknowledgements + retransmission |
| **In-order delivery** | Sequence numbers + receive buffer reordering |
| **Error detection** | 16-bit checksum on every segment |
| **Flow control** | Sliding window (receiver controls sender rate) |
| **Congestion control** | CWND algorithms (sender probes network capacity) |

### Where TCP Lives in the Stack

```
+---------------------------+
|  Application Layer        |  HTTP, SSH, FTP, SMTP, TLS
+---------------------------+
|  Transport Layer (TCP)    |  <-- THIS IS TCP
+---------------------------+
|  Network Layer (IP)       |  Routing, addressing
+---------------------------+
|  Data Link Layer          |  Ethernet, Wi-Fi frames
+---------------------------+
|  Physical Layer           |  Bits on wire/air
+---------------------------+
```

TCP takes a **stream of bytes** from the application, segments it, ensures delivery, reassembles it at the other end, and delivers it back as a stream. The application never sees segments — it sees a pipe.

---

## 2. TCP vs UDP — The Design Philosophy

Understanding when to use TCP requires understanding its tradeoffs against UDP.

```
TCP                                     UDP
+---------------------------+           +---------------------------+
| Connection-oriented       |           | Connectionless            |
| Reliable (ACK + retransmit|           | Unreliable (fire-and-forget)
| In-order delivery         |           | No ordering guarantee     |
| Flow control              |           | No flow control           |
| Congestion control        |           | No congestion control     |
| Full-duplex               |           | Full-duplex               |
| High overhead             |           | Low overhead (8-byte hdr) |
| ~20-60 byte header        |           | 8-byte header             |
+---------------------------+           +---------------------------+
Use: HTTP, SSH, FTP, SMTP               Use: DNS, DHCP, VoIP, gaming
     anything byte-accurate                  anything latency-sensitive
```

**Key insight for pentesters:** TCP's reliability mechanisms (handshake, state tracking, retransmission) create predictable state on both endpoints — and state is attack surface.

---

## 3. The TCP Segment Structure

This is the actual on-wire format of a TCP segment (header + payload). Memorize this — every TCP attack and defense relates back to fields in this header.

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
|                    Padded to 32-bit boundary                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             Data                              |
|                    (application payload)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Field-by-Field Breakdown

#### Source Port (16 bits)
- Range: 0–65535
- Ephemeral ports (client): typically 1024–65535 (OS-dependent; Linux: 32768–60999)
- Well-known ports (server): 0–1023 (require root on Unix)
- Used with destination IP to form the **socket pair** that uniquely identifies the connection

#### Destination Port (16 bits)
- Same range. Combined with source port, source IP, destination IP → **4-tuple** that identifies a unique TCP connection

#### Sequence Number (32 bits)
- Identifies the **byte offset** of the first data byte in this segment within the stream
- During SYN: this is the **Initial Sequence Number (ISN)** — the starting value
- Wraps around at 2^32 − 1 back to 0
- Critical for ordering, deduplication, and acknowledgement

#### Acknowledgment Number (32 bits)
- Only valid when **ACK flag** is set
- Means: "I have received all bytes up to but NOT including this number; send me this byte next"
- It's a **cumulative** acknowledgement — one ACK can acknowledge thousands of bytes
- Example: ACK=5001 means "I have bytes 1–5000, please send byte 5001 next"

#### Data Offset (4 bits)
- Also called "Header Length"
- Specifies where the data begins — measured in **32-bit words**
- Minimum: 5 (= 20 bytes, no options), Maximum: 15 (= 60 bytes)

#### Reserved (3 bits)
- Must be zero per RFC 793. Some implementations use bits here for experimental features (Explicit Congestion Notification uses 2 bits here in RFC 3168)

#### Control Flags (9 bits)
Each flag is 1 bit. The classic 6 flags (RFC 793) plus 3 newer:

| Flag | Bit | Meaning |
|------|-----|---------|
| **NS** | bit 8 | ECN-nonce concealment (RFC 3540) |
| **CWR** | bit 7 | Congestion Window Reduced — sender reduced CWND in response to ECN |
| **ECE** | bit 6 | ECN-Echo — receiver signals congestion to sender |
| **URG** | bit 5 | Urgent pointer field is valid |
| **ACK** | bit 4 | Acknowledgment field is valid — set on ALL segments after connection establishment |
| **PSH** | bit 3 | Push — receiver should pass data to application immediately, don't buffer |
| **RST** | bit 2 | Reset — abort the connection immediately (no graceful close) |
| **SYN** | bit 1 | Synchronize sequence numbers — used in handshake |
| **FIN** | bit 0 | No more data from sender — graceful close initiation |

**Critical flag combinations to know:**
```
SYN only          → Connection request (first packet of handshake)
SYN+ACK           → Connection accepted (second packet)
ACK only          → Data transfer or pure acknowledgement
FIN+ACK           → Graceful connection termination
RST               → Immediate connection abort
RST+ACK           → Abort with acknowledgement
PSH+ACK           → Data that should be delivered immediately to app
```

#### Window Size (16 bits)
- The **receive window** — how many bytes the sender is willing to receive
- Used for **flow control** (see Section 9)
- Maximum raw value: 65535 bytes
- With **Window Scale option**: up to 2^30 bytes (~1 GB)

#### Checksum (16 bits)
- Covers the TCP header, data, AND a **pseudo-header** (source IP, dest IP, protocol=6, TCP length)
- One's complement of the one's complement sum
- Mandatory for IPv4, also mandatory for IPv6 (unlike UDP where it's optional in v4)

#### Urgent Pointer (16 bits)
- Only valid when URG flag is set
- Points to the last byte of urgent data within the segment
- Mostly obsolete in modern usage (see Section 17)

#### Options (variable, 0–40 bytes)
- Padded to 32-bit boundary with NOP (0x01)
- See Section 12 for full breakdown

---

## 4. TCP Connection Lifecycle

A TCP connection goes through three distinct phases:

```
  CLIENT                                              SERVER
    |                                                    |
    |   Phase 1: ESTABLISHMENT (3-way handshake)        |
    |===================================================|
    |                                                    |
    |   Phase 2: DATA TRANSFER (bidirectional)          |
    |===================================================|
    |                                                    |
    |   Phase 3: TERMINATION (4-way or simultaneous)   |
    |===================================================|
```

The connection is defined by a **4-tuple**:
```
(Source IP, Source Port, Destination IP, Destination Port)
```

This tuple uniquely identifies every TCP connection on a machine. Two connections can share source IP + destination IP + destination port if they differ in source port.

---

## 5. Three-Way Handshake

The handshake serves two purposes:
1. **Establish the connection** (both sides agree to communicate)
2. **Exchange Initial Sequence Numbers (ISNs)** (both sides synchronize their byte counters)

### Why THREE ways?

You need to confirm both directions independently:
- Client → Server direction: SYN establishes it, SYN-ACK confirms Server received it
- Server → Client direction: SYN-ACK establishes it, ACK confirms Client received it

Two-way would leave one direction unconfirmed.

### The Handshake in Detail

```
CLIENT                                                    SERVER
  |                                                          |
  |  [SYN]                                                   |
  |  SEQ=x  (x = client's ISN, e.g. 1000)                   |
  |  ACK=0  (ACK flag NOT set)                               |
  |  WIN=64240                                               |
  |  CTL: SYN                                               |
  |--------------------------------------------------------->|
  |                                                          |  STATE: SYN-RECEIVED
  |                          [SYN-ACK]                       |
  |                          SEQ=y  (y = server's ISN, e.g. 5000)
  |                          ACK=x+1  (1001 — "next byte I expect from you")
  |                          WIN=65535                       |
  |                          CTL: SYN, ACK                  |
  |<---------------------------------------------------------|
  |                                                          |
  |  [ACK]                                                   |
  |  SEQ=x+1  (1001)                                         |
  |  ACK=y+1  (5001 — "next byte I expect from server")      |
  |  CTL: ACK                                               |
  |  (no data yet)                                           |
  |--------------------------------------------------------->|
  |                                                          |
  |  CONNECTION ESTABLISHED — both sides ESTABLISHED state   |
  |                                                          |
```

### Why is the ISN Random?

RFC 793 originally said ISNs should increment over time (roughly 250,000 increments/sec). Modern implementations use cryptographically random ISNs (or hashed with secret key).

**Reason:** Predictable ISNs enable:
- TCP session hijacking (blind injection)
- SYN spoofing attacks
- Connection reset attacks

A random 32-bit ISN gives 2^32 ≈ 4 billion possibilities — an attacker guessing blind has 1:4-billion odds.

### SYN Backlog and the Listen Queue

When a server calls `listen()`, the OS creates two queues:

```
INCOMPLETE CONNECTION QUEUE (SYN queue)
+-----------------------------------------------+
| Half-open connections in SYN-RECEIVED state   |
| Waiting for the final ACK from client         |
| Default size: controlled by /proc/sys/net/... |
+-----------------------------------------------+

COMPLETE CONNECTION QUEUE (Accept queue)
+-----------------------------------------------+
| Fully established connections (post-ACK)      |
| Waiting for application to call accept()      |
| Size: backlog parameter in listen() call      |
+-----------------------------------------------+
```

This two-queue structure is the foundation of the **SYN flood attack**.

---

## 6. Four-Way Termination

TCP is **full-duplex** — both directions are independent streams. Closing requires shutting down each direction independently. Each side sends a FIN and receives an ACK.

### Standard Four-Way Termination

```
ACTIVE CLOSER (Client)                          PASSIVE CLOSER (Server)
       |                                                    |
       |  [FIN+ACK]                                         |
       |  SEQ=u                                             |
       |  ACK=v  (last ACK of data transfer)                |
       |  CTL: FIN, ACK                                     |
       |--------------------------------------------------->|
       |                                                STATE: CLOSE-WAIT
       |                                                    |
       |                          [ACK]                     |
       |                          SEQ=v                     |
       |                          ACK=u+1                   |
       |<---------------------------------------------------|
  STATE: FIN-WAIT-2                                         |
       |                                                    |
       |  (Server can still send data here —                |
       |   this is a HALF-CLOSED connection)               |
       |                                                    |
       |                          [FIN+ACK]                 |
       |                          SEQ=v                     |
       |                          ACK=u+1                   |
       |<---------------------------------------------------|
       |                                                STATE: LAST-ACK
       |  [ACK]                                             |
       |  SEQ=u+1                                           |
       |  ACK=v+1                                           |
       |--------------------------------------------------->|
       |                                                    |
  STATE: TIME-WAIT                                  CONNECTION CLOSED
       |  (waits 2×MSL before releasing resources)          |
       |                                                    |
       |  [TIME-WAIT expires after 2×MSL (~60-240 seconds)] |
       |                                                    |
  CONNECTION CLOSED                                         |
```

### Simultaneous Close

Both sides can send FIN at the same time:

```
CLIENT                                              SERVER
  |  [FIN+ACK] SEQ=u ---------------------------------->|
  |  <--------------------------------- [FIN+ACK] SEQ=v |
  |  [ACK] ACK=v+1 ----------------------------------->|
  |  <--------------------------------- [ACK] ACK=u+1  |
  |                                                    |
Both go to TIME-WAIT state                            |
```

### RST — The Hard Close

Instead of FIN/ACK sequence, either side can send RST at any time:

```
CLIENT                               SERVER
  |  [RST] or [RST+ACK]              |
  |--------------------------------->|  Connection aborted immediately
  |                                  |  No TIME-WAIT, no graceful drain
```

RST is used when:
- Connection is invalid (port not open → server sends RST)
- Application crashes without closing sockets
- Firewall actively rejects (vs silently drops)
- Application calls `SO_LINGER` with timeout=0

---

## 7. TCP State Machine — All 11 States

TCP is fundamentally a **finite state machine**. Understanding every state and every valid transition is critical for both debugging and attacking.

```
                              +----------+
           PASSIVE OPEN       |  CLOSED  |         ACTIVE OPEN
             ________________ +----------+ ________________
            |                /     |      \                |
            V               / appl.|close  \               V
        +--------+         /       V        \         +---------+
        | LISTEN |<-------+   +--------+    +-------->|   SYN   |
        +--------+            | CLOSED |              |   SENT  |
          |   |               +--------+              +---------+
   rcv    |   | send                                    |
   SYN    |   | SYN             rcv SYN                | rcv SYN-ACK
          V   V               +--------+               |
      +----------+            |  SYN   |               V
      |   SYN    |<-----------| RCVD   |         +-----------+
      | RECEIVED |  (simultan.|        |         |  ESTAB-   |
      +----------+   open)    +--------+         |  LISHED   |
          |                      |               +-----------+
          | send SYN-ACK         | send SYN-ACK       |
          V                      |               appl. close
      +----------+               |               send FIN
      |   SYN    |               |                    |
      | RECEIVED |               V                    V
      +----------+          +-----------+        +---------+
          |                 |   ESTAB-  |        |  FIN    |
          | rcv ACK of SYN  |   LISHED  |        |  WAIT-1 |
          V                 +-----------+        +---------+
      +-----------+            |   |               |     |
      |   ESTAB-  |            |   |  appl. close  |     | rcv FIN
      |   LISHED  |            |   |  send FIN     |     | send ACK
      +-----------+            |   V               |     V
           |          rcv FIN  | +----------+      |  +--------+
   appl.   |          send ACK | | CLOSE-   |      |  |CLOSING |
   close   |                   | | WAIT     |      |  +--------+
   send    V                   | +----------+      |       |
   FIN  +---------+            |    |              |  rcv ACK of FIN
        | FIN     |            |    | appl. close  |       V
        | WAIT-1  |            |    | send FIN     |  +---------+
        +---------+            |    V              |  |TIME-WAIT|
           |                   | +----------+      |  +---------+
   rcv ACK |                   | |  LAST-   |      |
   of FIN  |                   | |  ACK     |      |
           V                   | +----------+      |
        +---------+            |     |             |
        | FIN     |            |     | rcv ACK     | rcv ACK of FIN
        | WAIT-2  |            |     V             V
        +---------+            | +---------+  +---------+
           |                   | |CLOSED   |  |TIME-WAIT|
    rcv FIN|                   | +---------+  +---------+
    send   |                   |                  |
    ACK    V                   |             2MSL timeout
        +---------+            |                  V
        |TIME-WAIT|<-----------+             +---------+
        +---------+                          | CLOSED  |
              |                              +---------+
         2MSL |
        timeout
              V
        +---------+
        |  CLOSED |
        +---------+
```

### All 11 States Explained

| State | Who | Meaning |
|-------|-----|---------|
| **CLOSED** | Both | No connection exists. Starting point and ending point. |
| **LISTEN** | Server | Waiting for incoming SYN (passive open). `listen()` call puts socket here. |
| **SYN-SENT** | Client | Sent SYN, waiting for SYN-ACK. Active open initiated. |
| **SYN-RECEIVED** | Server | Received SYN, sent SYN-ACK, waiting for ACK. Half-open. |
| **ESTABLISHED** | Both | Full connection. Data can flow in both directions. |
| **FIN-WAIT-1** | Active closer | Sent FIN, waiting for ACK of that FIN. |
| **FIN-WAIT-2** | Active closer | Received ACK of FIN. Waiting for remote FIN. Can still receive data. |
| **CLOSE-WAIT** | Passive closer | Received FIN from other side. Waiting for application to close. |
| **CLOSING** | Both | Simultaneous close — both sent FIN, waiting for ACK. |
| **LAST-ACK** | Passive closer | Sent FIN, waiting for final ACK from other side. |
| **TIME-WAIT** | Active closer | Waiting 2×MSL before fully closing. Prevents old segments from corrupting new connections. |

### Viewing TCP States

```bash
# Linux — show all TCP connections with states
ss -tnp

# Or with netstat (older)
netstat -tnp

# Count connections by state
ss -tn | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn

# Show listening sockets only
ss -tlnp

# Watch state changes in real time
watch -n 0.5 'ss -tn | tail -n +2 | awk "{print \$1}" | sort | uniq -c'
```

---

## 8. Sequence Numbers and Acknowledgements

This is the heart of TCP's reliability mechanism. Understanding it deeply unlocks understanding of every reliability-related attack.

### The Byte Stream Model

TCP treats data as an infinite stream of bytes, each with a **unique sequence number**. The ISN is the starting offset — not byte 0 but a random starting point.

```
ISN = 1000

Byte 1001:  'H'
Byte 1002:  'e'
Byte 1003:  'l'
Byte 1004:  'l'
Byte 1005:  'o'
```

If the sender sends "Hello" in a single segment:
```
SEQ=1001, LEN=5, DATA="Hello"
```

The receiver's ACK:
```
ACK=1006  (meaning: "I received up to byte 1005, send me 1006 next")
```

### Segment Size and the MSS

MSS (Maximum Segment Size) is negotiated in the SYN options. It's the maximum **payload** size (not including TCP/IP headers). Typically:
- Ethernet: MSS = 1460 bytes (1500 MTU − 20 IP − 20 TCP)
- With SACK/timestamps options: slightly less (options consume header space)
- Jumbo frames: up to 9000 bytes

```
Segment 1: SEQ=1001, LEN=1460, DATA=bytes[1001..2460]
Segment 2: SEQ=2461, LEN=1460, DATA=bytes[2461..3920]
Segment 3: SEQ=3921, LEN=540,  DATA=bytes[3921..4460]

Final ACK from receiver: ACK=4461
```

### Cumulative vs Selective Acknowledgements

**Cumulative ACK** (baseline TCP):
```
Sender:    [1..1000]  [1001..2000]  [2001..3000]  [3001..4000]
                                         LOST
Receiver:   ACK=1001   ACK=2001                    ACK=2001 (still!)
```
Receiver gets 3001-4000 but can't ACK it because 2001-3000 is missing.

**Selective ACK (SACK)** (RFC 2018 — TCP option):
```
Receiver: ACK=2001, SACK=[3001-4000]
```
This tells the sender exactly what was received out-of-order. Sender only retransmits the missing segment [2001-3000].

### Sequence Number Wrap-around

32-bit sequence numbers wrap at 2^32 = 4,294,967,296. At 10 Gbps, this wraps in ~3.4 seconds. TCP handles this with **PAWS (Protection Against Wrapped Sequences)** using timestamps (TCP option).

---

## 9. Sliding Window and Flow Control

### Why Flow Control?

Without flow control, a fast sender can overwhelm a slow receiver's buffer, causing the OS to drop packets. TCP prevents this by having the **receiver** tell the **sender** how much buffer space it has available.

### The Receive Window (RWND)

```
RECEIVER BUFFER
+------------------------------------------------------------+
|CONSUMED|  DATA RECEIVED  |  FREE SPACE (advertised window)|
|  by    |   (buffered,    |     RWND = 32768               |
|  app   | not read yet)   |                                |
+------------------------------------------------------------+
         ^                 ^                                ^
    rcv_next          RCV.NXT + RWND                    buffer end
```

The receiver advertises its free buffer space in the **Window** field of every TCP segment it sends. The sender must not have more than RWND bytes of unacknowledged data in flight.

### The Send Window

```
SENDER VIEW:
|<-- already ACK'd -->|<-- in flight, unACK'd -->|<-- can send -->|<-- can't send yet -->|
                      ^                          ^                ^
                   SND.UNA                   SND.NXT         SND.UNA+RWND

SND.UNA  = oldest unacknowledged byte
SND.NXT  = next byte to send
Window   = min(RWND, CWND)  [CWND = congestion window from congestion control]
```

### Sliding Window Operation

```
Initial state (RWND=4, simplified units):
Bytes:    1  2  3  4  5  6  7  8  9  10
          [ACK'd]  [  in flight  ] [window][ not allowed ]
                    ^              ^
                 SND.UNA       SND.UNA+RWND

After ACK for bytes 1-2 received (RWND still 4):
Bytes:    1  2  3  4  5  6  7  8  9  10
         [  ACK'd  ] [in flt] [window ][ not allowed ]
                      ^              ^
                   SND.UNA       SND.UNA+RWND
```

The window "slides" right as ACKs arrive and as the receiver's buffer frees up.

### Zero Window and Window Probes

If the receiver's buffer is completely full, it advertises **RWND=0**:

```
RECEIVER: [ACK] WIN=0    ← "Stop sending! I'm full!"

SENDER: Cannot send data. Must send Window Probes:
  → 1 byte probe every [timer] to check if window has opened
  ← RECEIVER: [ACK] WIN=0    (still full)
  ← RECEIVER: [ACK] WIN=8192 (buffer freed up, you can send again)
```

This prevents deadlock where sender stops and receiver forgets to notify.

### Silly Window Syndrome

**Sender-side SWS:** Application sends 1 byte at a time → 1 byte per segment → terrible efficiency (41 byte segment for 1 byte of data). **Nagle's algorithm** fixes this (Section 13).

**Receiver-side SWS:** Receiver advertises tiny windows (e.g., 2 bytes free), causing sender to send tiny segments. **Clark's solution:** Don't advertise window until it grows to either MSS or half the receive buffer.

---

## 10. Congestion Control

### The Fundamental Problem

The network has limited capacity. If all senders ignore this and blast at full speed, routers drop everything and throughput collapses (congestion collapse, as observed in 1986). TCP must **probe** the network to find its fair share of bandwidth.

Flow control (RWND) handles **receiver** capacity. Congestion control (CWND) handles **network** capacity.

```
Effective send window = min(RWND, CWND)
```

### Key Variables

| Variable | Meaning |
|----------|---------|
| **CWND** | Congestion Window — sender's estimate of how much data the network can handle |
| **SSTHRESH** | Slow Start Threshold — boundary between Slow Start and Congestion Avoidance |
| **MSS** | Maximum Segment Size |

### TCP Tahoe (1988 — Original)

The foundational algorithm. Three phases:

#### Phase 1: Slow Start

Despite the name, this is exponential growth. CWND starts at 1 MSS and doubles every RTT.

```
RTT 1:  CWND = 1 MSS  → send 1 segment, receive 1 ACK
RTT 2:  CWND = 2 MSS  → send 2 segments, receive 2 ACKs
RTT 3:  CWND = 4 MSS  → send 4 segments
RTT 4:  CWND = 8 MSS  → ...

+-------+
| CWND  |     /
|       |    /
|       |   /
|       |  /
|       | /
|       |/
+-------+----> time (RTTs)
```

Slow Start ends when CWND ≥ SSTHRESH.

#### Phase 2: Congestion Avoidance

Linear growth (additive increase). CWND grows by 1 MSS per RTT.

```
CWND += MSS * (MSS/CWND) per ACK  ≈ 1 MSS per RTT

+-------+          /
| CWND  |         /
|       |        /  SSTHRESH (linear)
|       |       /
|       |      / (exponential)
+-------+-----/-----> time (RTTs)
```

#### Phase 3: Loss Detection and Response (Tahoe)

On **any** loss (timeout OR 3 duplicate ACKs):
```
SSTHRESH = max(CWND/2, 2*MSS)
CWND = 1 MSS
→ restart Slow Start
```

```
CWND
  |        /\
  |       /  \
  |      /    \----loss detected
  |     /      \
  |    /        \ (SSTHRESH = CWND/2)
  |   /          |
  |  /           | CWND=1, restart slow start
  | /            |/
  |/             /
  +-------------+-----> time
```

### TCP Reno (1990)

Adds **Fast Retransmit** and **Fast Recovery** on top of Tahoe.

**Fast Retransmit:** Don't wait for timeout. If 3 duplicate ACKs arrive → retransmit immediately.

```
Sender:   [1][2][3][4][5]
              LOST
Receiver: ACK=2, ACK=2, ACK=2  (3rd duplicate)
Sender:   Retransmit [2] immediately (no timeout wait)
```

**Fast Recovery (Reno's key innovation):**
On 3 dup ACKs (NOT on timeout):
```
SSTHRESH = CWND / 2
CWND = SSTHRESH + 3*MSS  (3 MSS for the 3 dup ACKs = 3 packets left network)
→ stay in Congestion Avoidance (don't go back to Slow Start)
```

On timeout (still severe):
```
SSTHRESH = CWND / 2
CWND = 1 MSS
→ restart Slow Start (same as Tahoe)
```

### TCP CUBIC (Default in Linux ≥ 2.6.19)

CUBIC replaces the linear increase with a **cubic function** of time since last congestion event. Handles high-BDP (Bandwidth-Delay Product) networks much better.

```
CWND(t) = C(t - K)^3 + W_max

Where:
  t     = time since last congestion event
  K     = time to reach W_max from current CWND
  W_max = CWND at last congestion
  C     = scaling constant (0.4 by default)
```

The cubic function:
- Grows fast when far from W_max
- Slows near W_max (cautious probing)
- Grows fast again past W_max (exploring new capacity)

```
CWND
  |              W_max
  |            __|__
  |          /  |   \__________
  |         /   |              \___     cubic curve
  |        /    |                  \___
  |       /     |                      \_____
  |      /      |
  |     /       | (cubic inflection point)
  +----+--------+----> time since last congestion
```

### TCP BBR (Bottleneck Bandwidth and RTT — Google, 2016)

BBR fundamentally changes the paradigm. Instead of responding to loss as a signal of congestion, BBR **models the network** by measuring:
- **BtlBw** (Bottleneck Bandwidth)
- **RTprop** (Round-trip propagation time)

BBR tries to operate at the **optimal point**: full pipe, no queue buildup.

```
Throughput
    ^
    |    BBR target
    |      |
    |______v_______  maximum throughput (BtlBw)
    |     /
    |    /
    |   /
    |  /
    | / (packet loss starts here in loss-based CC)
    |/
    +--------------------> CWND

Delay
    ^
    |            /  (traditional CC inflates queues)
    |           /
    |__________/  ← BBR avoids this queue buildup
    |
    +--------------------> CWND
```

BBR uses **pacing** (spreading segments evenly over time) rather than bursting. Significantly reduces latency at high loads.

---

## 11. Retransmission and Timers

### RTO (Retransmission Timeout)

When a segment is sent, a **retransmission timer** starts. If ACK doesn't arrive before timeout, the segment is retransmitted.

**RTT Estimation (Jacobson's Algorithm):**
```
SRTT  = (1-α) × SRTT  + α × RTT_sample   [α = 0.125]
RTTVAR = (1-β) × RTTVAR + β × |SRTT - RTT_sample|  [β = 0.25]
RTO   = SRTT + 4 × RTTVAR
```

**Exponential Backoff:**
On each successive retransmission, RTO doubles:
```
Attempt 1:  wait RTO    (e.g., 200ms)
Attempt 2:  wait 2×RTO  (400ms)
Attempt 3:  wait 4×RTO  (800ms)
Attempt 4:  wait 8×RTO  (1600ms)
...
Max: typically 120 seconds before giving up
```

Minimum RTO: 1 second (RFC 6298)
Maximum RTO: 60-120 seconds

### Karn's Algorithm

Problem: If you retransmit a segment, you can't tell if the ACK is for the original or the retransmission → ambiguity in RTT measurement.

**Solution:** Don't update RTT estimates for retransmitted segments. Reset SRTT calculation.

### Duplicate ACK and Fast Retransmit

```
Receiver ACK flow:
  Got [1]: ACK=1001
  Got [3]: ACK=1001 (dup 1) — segment 2 missing
  Got [4]: ACK=1001 (dup 2)
  Got [5]: ACK=1001 (dup 3) ← TRIGGER: retransmit [2] immediately
  Got [2] (retransmitted): ACK=5001 (catches up to everything)
```

### Timer Summary

| Timer | Purpose | Typical Value |
|-------|---------|---------------|
| **RTO** | Retransmit unACK'd segment | 200ms–120s (adaptive) |
| **Persistence** | Send window probes when RWND=0 | Exponential backoff |
| **Keepalive** | Detect dead connections | 2 hours (idle), then probes |
| **TIME-WAIT (2MSL)** | Ensure no old segments exist | 60–240 seconds |
| **FIN-WAIT-2** | Limit half-closed connections | 60 seconds (Linux default) |

---

## 12. TCP Options Field Deep Dive

Options appear in the TCP header between the fixed fields and the data. They are type-length-value encoded (with some single-byte options).

### Option Format

```
+--------+--------+--------+--------+
|  Kind  | Length |        Data     |
+--------+--------+--------+--------+
  1 byte   1 byte  (Length-2 bytes)

Exception: Kind=0 (EOL) and Kind=1 (NOP) are single bytes
```

### All Important TCP Options

#### Kind 0: End of Option List (EOL)
Single byte `0x00`. Marks the end of the options list. Padding after this is ignored.

#### Kind 1: No-Operation (NOP)
Single byte `0x01`. Used as padding to align subsequent options to 32-bit boundaries.

#### Kind 2: Maximum Segment Size (MSS)
```
+--------+--------+--------+--------+
|  0x02  |  0x04  |    MSS value    |
+--------+--------+--------+--------+
           length=4   2 bytes, e.g. 0x05B4 = 1460
```
- Only in SYN and SYN-ACK segments
- Tells the other side the maximum segment size it's willing to receive
- Not a negotiation — each side sets its own MSS independently
- If not present, default is 536 bytes (576 IP MTU − 40 TCP/IP headers)

#### Kind 3: Window Scale (WSCALE)
```
+--------+--------+--------+
|  0x03  |  0x03  |  shift |
+--------+--------+--------+
           length=3  1 byte, 0-14
```
- Only in SYN/SYN-ACK
- Multiplies the Window field by `2^shift`
- Without WSCALE: max window = 65535 bytes
- With WSCALE (shift=8): max window = 65535 × 256 = ~16MB
- With WSCALE (shift=14): max window = ~1GB
- Critical for long-fat networks (high BDP — e.g., satellite, transoceanic fiber)

#### Kind 4: Selective Acknowledgement Permitted (SACK-Permitted)
```
+--------+--------+
|  0x04  |  0x02  |
+--------+--------+
```
- Only in SYN/SYN-ACK
- Signals willingness to use SACK option

#### Kind 5: Selective Acknowledgement (SACK)
```
+--------+--------+--------+--------+--------+--------+
|  0x05  | Length |  Left Edge 1  |  Right Edge 1   | ...
+--------+--------+--------+--------+--------+--------+
```
- Variable length: up to 4 SACK blocks (1-4 blocks, 8 bytes each + 2 header = 10–34 bytes)
- Each block: [left edge, right edge) = range of bytes received out-of-order
- Tells sender exactly what arrived out of order → sender only retransmits holes

**Example:** Segments 1-1000, 2001-3000, and 4001-5000 received. Segment 1001-2000 and 3001-4000 missing:
```
ACK=1001
SACK Block 1: [2001, 3001)
SACK Block 2: [4001, 5001)
```
Sender knows to retransmit [1001-2000] and [3001-4000] only.

#### Kind 8: Timestamps (TS)
```
+--------+--------+--------+--------+--------+--------+
|  0x08  |  0x0A  |    TSval (sender's timestamp)     |
+--------+--------+--------+--------+--------+--------+
         |         TSecr (echo of received timestamp) |
         +-------------------------------------------+
  length=10, total 10 bytes
```
- **TSval:** Sender's current clock value when sending
- **TSecr:** Echo of the most recently received TSval (from other side)

**Two purposes:**
1. **RTTM (RTT Measurement):** Accurate RTT without Karn's algorithm ambiguity. ACK echoes TSval → sender computes RTT = now − TSecr.
2. **PAWS (Protection Against Wrapped Sequences):** Prevents old duplicate segments from a previous incarnation of the same connection from being accepted.

#### Kind 34: TCP Fast Open (TFO) — RFC 7413
```
+--------+--------+--------...--------+
|  0x22  | Length |  TFO Cookie       |
+--------+--------+--------...--------+
```
- Allows data to be sent in the SYN packet (0-RTT connection)
- First connection: client requests cookie, server generates and returns it in SYN-ACK
- Subsequent connections: client sends cookie + data in SYN → server can respond before handshake completes

```
Traditional TCP:  SYN → SYN-ACK → ACK → [data] → response  (1.5 RTT minimum)
TFO:              SYN+data+cookie → response+SYN-ACK → ACK  (0.5 RTT to data)
```

Security note: TFO introduces replay attack risk for non-idempotent requests.

---

## 13. Nagle's Algorithm and Delayed ACKs

### Nagle's Algorithm (RFC 896, 1984)

**Problem:** Without Nagle, applications sending 1 byte at a time (e.g., telnet, SSH keystroke-by-keystroke) create a flood of tiny segments. Each segment has 40 bytes of IP+TCP overhead for 1 byte of data = 1% efficiency.

**Nagle's Rule:**
```
IF (there is new data to send):
    IF (CWND >= MSS AND available data >= MSS):
        Send full segment immediately  [large data case]
    ELSE:
        IF (there is unacknowledged data in flight):
            Buffer the data and wait for ACK  [Nagle holding]
        ELSE:
            Send immediately (nothing in flight, no need to wait)
```

In plain English: **You can always send a full segment. But if you have a partial segment, wait until all previous segments are ACK'd.**

### Delayed ACK (RFC 1122)

**Problem:** Sending a pure ACK for every segment wastes bandwidth (40-byte ACK for a segment that carried 1460 bytes of data = ~2.7% overhead).

**Delayed ACK Rule:**
- Wait up to **200ms** for an opportunity to piggyback ACK on outgoing data
- If no data to send within 200ms, send the pure ACK
- **Must ACK every second segment** (don't delay ACKs for more than 2 segments)

### The Nagle + Delayed ACK Interaction Problem

This is a well-known performance trap:

```
CLIENT (Nagle ON)          SERVER (Delayed ACK ON)

send("GET /")              recv → buffer ACK
send("HTTP/1.1\r\n")       (partial request, waiting for more)

→ Nagle: "I have data in flight, wait for ACK before sending more"
→ DelayedACK: "I'll wait 200ms before sending that ACK"

Result: 200ms stall — neither side moves!
```

**Solutions:**
- `TCP_NODELAY` socket option: disables Nagle (used by SSH, interactive apps, HTTP/2)
- `TCP_QUICKACK` socket option (Linux): temporarily disable delayed ACK
- Application-level: send complete requests in one write() call

---

## 14. Keepalive Mechanism

### Purpose

TCP has no built-in heartbeat. If a connection is idle for hours and one side crashes or a NAT mapping expires, the surviving side never knows the connection is dead until it tries to send data.

Keepalive solves this by sending **probe segments** during idle periods.

### Keepalive Operation

Default parameters (Linux):
```
tcp_keepalive_time    = 7200  (2 hours idle before first probe)
tcp_keepalive_intvl   = 75    (75 seconds between probes)
tcp_keepalive_probes  = 9     (9 failed probes → declare dead)
```

```
ESTABLISHED (idle for 2 hours)
    |
    | [Keepalive probe: 1 byte or 0-byte with SEQ = SND.NXT-1]
    |------------------------------------------------------>|
    |                              [ACK]  (peer alive)      |
    |<------------------------------------------------------|
    |
    | ... 2 more hours idle ...
    |
    | [Keepalive probe]
    |------------------------------------------------------>|
    |                              (no response - host dead?)|
    | [probe 2] after 75s                                   |
    |------------------------------------------------------>|
    | [probe 3] after 75s                                   |
    |------------------------------------------------------>|
    | ... 9 probes ... all unanswered ...                   |
    | → Connection declared dead → ETIMEDOUT / ECONNRESET  |
```

### Enabling Keepalive

```bash
# Per-socket in Python
import socket
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)    # first probe after 60s
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)   # probe every 10s
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)      # give up after 5 probes

# System-wide (Linux)
sysctl -w net.ipv4.tcp_keepalive_time=60
sysctl -w net.ipv4.tcp_keepalive_intvl=10
sysctl -w net.ipv4.tcp_keepalive_probes=5
```

### Keepalive vs Application-Level Heartbeat

Keepalive operates at the TCP layer — application layer doesn't see it. Many protocols (HTTP/2, WebSocket, MQTT) implement their own application-level heartbeats for finer control and to detect issues above the TCP layer.

---

## 15. TIME_WAIT — The Most Misunderstood State

### What It Is

After the active closer sends the final ACK, instead of immediately closing, it enters **TIME_WAIT** for **2 × MSL** (Maximum Segment Lifetime).

MSL is the maximum time any segment can exist in the network. RFC 793 recommends 2 minutes, making 2×MSL = 4 minutes. Linux default: 60 seconds.

### Why TIME_WAIT Exists — Two Reasons

**Reason 1: Ensure the final ACK arrives**

```
CLIENT (TIME-WAIT)                          SERVER (LAST-ACK)
  |                                              |
  |  [ACK] final ACK --------------------------->|
  |                                              | → CLOSED
  |                                              |
  | What if this ACK is lost?                   |
  |                                              |
  |                          [FIN] retransmit <--|
  |  [ACK] retransmit --------------------------->|  ← Client can only
  |                                              |    do this if in TIME-WAIT
```

If client immediately closed, the retransmitted FIN would get a RST (connection doesn't exist). Server would be stuck in LAST-ACK forever.

**Reason 2: Prevent stale segments from poisoning new connections**

```
Connection 1: (192.168.1.1:4000 ↔ 10.0.0.1:80)
  Sends: [SEQ=5000, DATA="old stale segment"] → gets lost in network
  Connection 1 closes normally.

Connection 2 (same 4-tuple reused immediately):
  (192.168.1.1:4000 ↔ 10.0.0.1:80)  ← same ports!
  Stale segment finally arrives: [SEQ=5000, DATA="old stale segment"]
  → New connection accepts it as valid data → DATA CORRUPTION!
```

TIME_WAIT ensures the 2×MSL window eliminates all stale segments before the 4-tuple can be reused.

### TIME_WAIT Problems and Solutions

**Problem:** High-traffic servers making many outgoing connections (reverse proxies, load balancers) can exhaust ephemeral port space with TIME_WAIT sockets.

```bash
# Check TIME_WAIT count
ss -tn | grep TIME-WAIT | wc -l

# Enable SO_REUSEADDR (allows new sockets to reuse port in TIME-WAIT if seq numbers differ)
# Linux-specific: tcp_tw_reuse
sysctl -w net.ipv4.tcp_tw_reuse=1  # Safe for outgoing connections only

# DANGEROUS: tcp_tw_recycle (deprecated, removed in kernel 4.12)
# Breaks with NAT — do NOT use
```

**Safe mitigation:**
- `SO_REUSEADDR` + `SO_REUSEPORT`
- Increase ephemeral port range: `sysctl -w net.ipv4.ip_local_port_range="1024 65535"`
- Use connection pools (reuse connections rather than creating new ones)
- Increase TIME_WAIT maximum: `sysctl -w net.ipv4.tcp_max_tw_buckets=2000000`

---

## 16. TCP Half-Open and Half-Closed Connections

### Half-Open Connection

A connection where one side thinks it's established but the other side has closed (or crashed and restarted).

```
CLIENT (thinks ESTABLISHED)         SERVER (crashed and restarted)
  |                                        |
  | [DATA]  -------------------------------->|
  |                          [RST] <--------|  "What connection?"
  |                                        |
```

The client's next send reveals the broken connection via RST.

**Half-open detection with keepalive:** Keepalive probes will eventually elicit an RST from the peer, cleaning up the dead connection.

### Half-Closed Connection

A legitimate TCP state where one side has sent FIN (no more data from it) but the other side can still send data.

```
CLIENT                                    SERVER
  |  [FIN+ACK] --------------------------->|   Client: "I'm done sending"
  |  <----------------------------- [ACK]  |   Server: "OK, got it"
  |                                        |
  |   ← SERVER CAN STILL SEND DATA →      |   ← This is half-closed
  |  <--------------------------- [DATA]  |
  |  [ACK] -------------------------------->|
  |  <--------------------------- [DATA]  |
  |  [ACK] -------------------------------->|
  |                                        |
  |  <------------------------ [FIN+ACK]  |   Server: "Now I'm done"
  |  [ACK] -------------------------------->|
```

In Unix: `shutdown(fd, SHUT_WR)` closes the write direction while keeping read open. This is how the `nc` utility implements "send stdin then receive until server closes".

---

## 17. TCP Urgent Data and Out-of-Band Signaling

### What Urgent Data Is

TCP's Urgent mechanism allows a sender to flag certain data as "urgent" — it should be processed by the receiver ahead of normal data, even if the receive buffer is full.

```
TCP Header: URG=1, Urgent Pointer=N

The Urgent Pointer is an offset from SEQ pointing to the LAST byte of urgent data.
All bytes from the current read position up to SEQ+UrgentPointer are "urgent."
```

### How It Works (and Why It's Broken)

```
[Normal data][Urgent data!][More normal data]
             ^            ^
           SEQ       SEQ+UrgentPointer
```

The URG flag + pointer doesn't actually jump urgent data to the front of the stream — it just marks a location. The receiver is supposed to process urgent data specially, but implementations vary wildly.

### Real-World Use

**Telnet:** Uses URG to send Ctrl-C interrupts that bypass buffered normal data. This is the primary historic use case.

**Modern reality:** URG is essentially obsolete. RFC 6093 discourages its use. Most applications implement priority mechanisms at the application layer instead.

---

## 18. TCP Performance Tuning

### Socket Buffer Sizes

```bash
# Linux defaults (bytes)
cat /proc/sys/net/ipv4/tcp_rmem  # min default max for receive
# e.g.: 4096 87380 6291456

cat /proc/sys/net/ipv4/tcp_wmem  # min default max for send
# e.g.: 4096 16384 4194304

# Increase for high-bandwidth links
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Enable autotuning (usually default on modern kernels)
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
```

### Bandwidth-Delay Product (BDP)

The BDP is the amount of data "in flight" needed to fully utilize a link:

```
BDP = Bandwidth × RTT

Example: 1 Gbps link, 100ms RTT
BDP = 1,000,000,000 bits/sec × 0.1 sec = 100,000,000 bits = 12.5 MB

Your RWND + CWND must be ≥ BDP to saturate this link.
Without Window Scaling, max is 65535 bytes = only 0.5% link utilization!
```

### Key Sysctl Parameters

```bash
# Congestion control algorithm
sysctl net.ipv4.tcp_congestion_control
sysctl -w net.ipv4.tcp_congestion_control=bbr  # set BBR

# Available algorithms
cat /proc/sys/net/ipv4/tcp_available_congestion_control

# SYN backlog queue size
sysctl -w net.ipv4.tcp_max_syn_backlog=65536

# TIME-WAIT bucket limit
sysctl -w net.ipv4.tcp_max_tw_buckets=2000000

# Reuse TIME-WAIT sockets for outgoing connections (safe)
sysctl -w net.ipv4.tcp_tw_reuse=1

# TCP Fast Open (both client and server = 3)
sysctl -w net.ipv4.tcp_fastopen=3

# Larger initial congestion window
# (set via ip route, not sysctl)
ip route change default via $GW initcwnd 10

# Enable SACK
sysctl -w net.ipv4.tcp_sack=1

# FACK (Forward Acknowledgement — builds on SACK)
sysctl -w net.ipv4.tcp_fack=1

# ECN (Explicit Congestion Notification)
sysctl -w net.ipv4.tcp_ecn=1
```

### Measuring TCP Performance

```bash
# Measure throughput
iperf3 -s                          # server
iperf3 -c SERVER_IP -t 30 -P 4    # client: 30s test, 4 parallel streams

# Measure latency
ping -c 100 SERVER_IP              # ICMP RTT
hping3 -S -p 443 SERVER_IP         # TCP SYN RTT

# Inspect TCP statistics
ss -ti                             # detailed TCP socket info including CWND, SSTHRESH
netstat -s | grep -i tcp           # aggregate TCP statistics
/proc/net/netstat                  # detailed per-protocol stats

# TCP trace with ss
watch -n 0.1 "ss -ti dst SERVER_IP"  # watch CWND grow in real-time
```

---

## 19. TCP Security — Attacks and Defenses

### 19.1 SYN Flood Attack

**Attack:** Attacker sends massive SYN stream with spoofed source IPs. Server creates half-open connections for each, filling the SYN backlog queue. Legitimate connections get dropped.

```
ATTACKER (spoofed IPs)                         SERVER
  |  [SYN] from 1.2.3.4 ---------------------->|  Queue entry 1
  |  [SYN] from 5.6.7.8 ---------------------->|  Queue entry 2
  |  [SYN] from 9.10.11.12 ------------------->|  Queue entry 3
  |  ... 10,000 more ...                        |  QUEUE FULL
  |                                             |
  |  (ACKs never arrive — all IPs are fake)     |
  |  (entries expire after ~1 min each)         |
  |                                             |
LEGITIMATE CLIENT:                              |
  |  [SYN] -------------------------------------> DROPPED (queue full)
```

**Defense: SYN Cookies (RFC 4987)**

Instead of storing state in the queue, encode the connection information in the SYN-ACK's sequence number:

```
SYN Cookie = hash(src_ip, src_port, dst_ip, dst_port, timestamp, secret) + MSS encoding

Server's SYN-ACK: SEQ = SYN Cookie

When client sends ACK:
  ACK_number = SYN_Cookie + 1
  Server: ACK_number - 1 = SYN_Cookie → verify → no state needed!
```

```bash
# Check if SYN cookies are enabled
cat /proc/sys/net/ipv4/tcp_syncookies
# 1 = enabled when queue full, 2 = always enabled
sysctl -w net.ipv4.tcp_syncookies=1
```

**Limitation:** SYN cookies don't support TCP options (SACK, window scale, timestamps) because there's no state to store them in. Connections established via cookie fall back to minimum TCP options.

### 19.2 TCP Session Hijacking

**Attack:** Attacker on-path (or with ability to sniff + inject) injects data into an established connection by using correct SEQ/ACK numbers.

```
CLIENT                  ATTACKER                  SERVER
  |  [SYN]             (observing) ----------->     |
  |  <---------------- [SYN-ACK]  <-----------      |
  |  [ACK+DATA]        (learns SEQ/ACK numbers)     |
  |                                                  |
  |                    [ACK=correct, SEQ=correct]    |
  |                    [INJECT: "rm -rf /"]  ------->|
  |                                                  | Executes as legitimate data!
```

**Requirements for success:**
- Know or predict SEQ/ACK numbers (trivial if sniffing, hard if guessing)
- Be on-path (or have ARP/BGP hijacking capability)
- Deal with RST storm (both real client and server start resetting)

**Defenses:**
- Randomized ISNs (RFC 6528 — already standard)
- TLS/SSL (encrypts and authenticates payload — hijacker can inject but not decrypt or forge valid MAC)
- TCP-AO (TCP Authentication Option — RFC 5925): HMACs every segment

### 19.3 TCP Reset Attack (RST Injection)

**Attack:** Attacker sends forged RST segments to tear down connections.

```
ATTACKER                              VICTIM
  |  [RST] SEQ=guessed_seq_number     |
  |   src_ip=peer_ip, src_port=peer_port
  |----------------------------------->|
  |                                    | Connection aborted!
```

**Challenge:** RST must have the exact SEQ number within the current receive window. With a 32-bit SEQ space, guessing is 1:65536 chance (window-sized guesses hit).

**Real-world use:**
- BGP session teardown (The Great Firewall of China uses RST injection)
- Intrusion Prevention Systems (Snort/Suricata can inject RSTs to block connections)

**Defense:**
- RFC 5961: Require RST SEQ == RCV.NXT exactly (not just within window) — reduces attack window dramatically
- TCP-AO authentication
- TLS: RST kills the transport but application can detect graceful vs abrupt close

### 19.4 IP Spoofing + Blind Attacks

**Attack:** Attacker cannot see server responses but can predict ISNs.

Before RFC 6528 randomization, systems used predictable ISNs (e.g., Berkeley-derived systems: ISN incremented by 128,000/sec). Attacker could:
1. Open connection to server, observe ISN
2. Predict server's ISN for connection to trusted host
3. Spoof source IP = trusted host, complete three-way handshake blindly

**Defense:** Cryptographically random ISNs (standard in all modern stacks).

### 19.5 Port Scanning Techniques (TCP-Based)

#### TCP Connect Scan
```bash
nmap -sT target     # Full 3-way handshake; OS connect()
```
```
SYN → SYN-ACK (open) → ACK → RST+ACK   [port open, detected]
SYN → RST (closed)                      [port closed]
SYN → [no response] (filtered)          [firewall dropping]
```

#### SYN Scan (Half-Open)
```bash
nmap -sS target     # Requires root; never completes handshake
```
```
SYN → SYN-ACK (open) → RST   [port open, less detectable]
SYN → RST (closed)            [port closed]
```
Never ACKs — never appears in application logs (connection never established).

#### FIN/NULL/XMAS Scans
```bash
nmap -sF target   # FIN only
nmap -sN target   # No flags (NULL)
nmap -sX target   # FIN+PSH+URG (XMAS)
```
RFC 793 says: closed ports respond with RST; open ports silently drop these invalid packets.
Only works reliably against RFC-compliant stacks (Windows doesn't follow this rule).

```
FIN → [silence]   = open (or filtered)
FIN → RST         = closed
```

#### ACK Scan (Firewall Mapping)
```bash
nmap -sA target
```
```
ACK → RST (unfiltered — stateless firewall passes it)
ACK → [silence] or ICMP unreachable (filtered — stateful firewall drops it)
```
Doesn't determine open/closed — determines filtered/unfiltered. Maps firewall rules.

#### TCP Idle Scan (Zombie Scan)
```bash
nmap -sI zombie_host target
```
Uses a "zombie" host with predictable IPID counter to conduct blind port scan. Attacker's IP never appears in target's logs.

```
ATTACKER              ZOMBIE                    TARGET
  |  Send SYN/ACK to zombie                        |
  |  → Learn zombie's IPID (e.g., IPID=100)         |
  |                                                 |
  |  Forge SYN to TARGET, src=ZOMBIE_IP ----------->|
  |                          TARGET → ZOMBIE        |
  |                    SYN-ACK (port open) -------->| ZOMBIE sends RST, IPID++
  |                    RST (port closed)  -------->| ZOMBIE sends nothing
  |                                                 |
  |  Send SYN/ACK to zombie                        |
  |  → IPID=101 (incremented) = port was OPEN      |
  |  → IPID=100 (unchanged)   = port was CLOSED    |
```

### 19.6 TCP Timestamp Side-Channel

TCP timestamps (RFC 7323) reveal system uptime and can uniquely fingerprint a host:
```
TSval = milliseconds since boot (often)
```

With TCPTimestampEcho from multiple connections, you can:
- Deduce system uptime
- Distinguish multiple hosts behind NAT (different clocks)
- Remotely fingerprint OS version

**Defense:**
```bash
# Disable TCP timestamps (Linux)
sysctl -w net.ipv4.tcp_timestamps=0

# Or randomize offset (better — preserves PAWS/RTTM benefits)
# Modern kernels randomize the timestamp offset per-connection
```

### 19.7 OS Fingerprinting

TCP header fields and behavior reveal OS identity:

| Parameter | Linux | Windows | macOS |
|-----------|-------|---------|-------|
| **TTL** | 64 | 128 | 64 |
| **Window size (SYN)** | 65535 | 65535 | 65535 |
| **MSS** | 1460 | 1460 | 1460 |
| **Window scale** | varies | 8 | 6 |
| **SACK** | yes | yes | yes |
| **Timestamps** | yes | no | yes |
| **DF bit** | usually set | usually set | set |
| **IPID** | 0 (Linux) | incremental | random |

Tools:
```bash
nmap -O target              # Active OS fingerprinting
p0f -i eth0                 # Passive OS fingerprinting (no packets sent)
```

### 19.8 Firewall Evasion via TCP Fragmentation

```bash
# Fragment TCP packets to confuse packet inspection
nmap -f target               # 8-byte fragments
nmap -f -f target            # 16-byte fragments
nmap --mtu 24 target         # custom MTU (multiple of 8)

# Decoys to obscure real source
nmap -D RND:10 target        # 10 random decoy IPs

# Timing to evade IDS
nmap -T0 target              # paranoid: 1 probe every 5 minutes
nmap -T1 target              # sneaky: 1 probe every 15 seconds
```

---

## 20. TCP in the Pentesting Context

### Port State Interpretation

```
OPEN     → Service is listening, accepting connections
CLOSED   → No service, but host is reachable
FILTERED → Firewall/ACL dropping packets (no response)
UNFILTERED → Firewall passes through, but open/closed unclear
OPEN|FILTERED → Can't distinguish — no response to probes
CLOSED|FILTERED → Can't distinguish
```

### Reading TCP Behavior for Intelligence

```
SYN → RST immediately = Port closed, host UP
SYN → RST+ACK        = Port closed, host UP (some stacks)
SYN → [silence]      = Firewall DROP rule
SYN → ICMP unreachable = Firewall REJECT rule (gives away firewall!)
SYN → SYN-ACK immediately = Service open, host UP
SYN → SYN-ACK after delay = Load balancer, slow service, or SYN cookie
```

### TCP Connection Reuse Attacks

**Connection Race (Race Condition via TCP):**
Some applications use TCP connection state (not TLS session state) for authentication. Attacking connection pool reuse:
```
1. Authenticate to server → session established
2. Trigger connection back to pool
3. Race another request before connection pool security checks
```

### TCP Desync / HTTP Request Smuggling

HTTP Request Smuggling exploits disagreement between frontend proxy and backend server about where HTTP request boundaries are:

```
POST / HTTP/1.1
Host: victim.com
Content-Length: 6
Transfer-Encoding: chunked

0

GPOST / HTTP/1.1
...
```

The frontend sees `Content-Length: 6` and reads 6 bytes. The backend sees `Transfer-Encoding: chunked` and reads until chunk terminator `0\r\n`. The remaining bytes become the beginning of the next HTTP request.

This is possible because TCP is a byte stream — there are no inherent "message" boundaries. Intermediate devices interpreting TCP streams differently create the attack surface.

### Banner Grabbing via Raw TCP

```bash
# Manual banner grab
echo "" | nc -v target 22    # SSH
echo "EHLO x" | nc -v target 25  # SMTP
echo "HEAD / HTTP/1.0\r\n\r\n" | nc -v target 80

# With timeout
nc -w 3 target 80 <<EOF
GET / HTTP/1.0
Host: target

EOF

# With hping3 (raw TCP)
hping3 -S -p 80 target -c 1

# Service detection
nmap -sV -p 80,443,22,21 target
```

### TCP Keepalive as Covert Channel

Keepalive probes at regular intervals maintain a connection without sending data — useful for maintaining reverse shells through NAT/firewalls:

```bash
# ncat with keepalive
ncat --keep-open target 4444

# socat with keepalive options
socat TCP:target:4444,keepalive,keepidle=10,keepintvl=5,keepcnt=3 -
```

---

## 21. Wireshark and Packet-Level Inspection

### Key TCP Display Filters

```
# All TCP traffic
tcp

# Specific port
tcp.port == 443

# SYN packets only (connection attempts)
tcp.flags.syn == 1 and tcp.flags.ack == 0

# RST packets (connection resets / port closed)
tcp.flags.reset == 1

# Retransmissions
tcp.analysis.retransmission

# Duplicate ACKs
tcp.analysis.duplicate_ack

# Zero window
tcp.analysis.zero_window

# Out-of-order segments
tcp.analysis.out_of_order

# Follow a specific stream
tcp.stream eq 5

# TCP errors (any analysis flag)
tcp.analysis.flags

# Packets with data (not pure ACKs)
tcp.len > 0

# Specific flag combinations
tcp.flags == 0x002   # SYN only
tcp.flags == 0x012   # SYN-ACK
tcp.flags == 0x010   # ACK only
tcp.flags == 0x018   # PSH+ACK
tcp.flags == 0x004   # RST
tcp.flags == 0x011   # FIN+ACK
```

### tcpdump Commands for TCP Analysis

```bash
# Capture TCP to/from host
tcpdump -i eth0 tcp host 10.0.0.1

# Capture SYN packets (port scan detection)
tcpdump -i eth0 'tcp[13] & 0x02 != 0 and tcp[13] & 0x10 == 0'

# Capture RST packets
tcpdump -i eth0 'tcp[13] & 0x04 != 0'

# Capture only SYN-ACK
tcpdump -i eth0 'tcp[13] == 0x12'

# Verbose output with timestamps and hex
tcpdump -i eth0 -nvvX tcp port 80

# Save to file
tcpdump -i eth0 -w capture.pcap tcp

# Read and filter pcap
tcpdump -r capture.pcap 'tcp[13] & 0x02 != 0'

# Decode TCP flags byte:
# Bit position: URG=32, ACK=16, PSH=8, RST=4, SYN=2, FIN=1
# tcp[13] is the flags byte in the TCP header (offset 13)
```

### Reading a TCP Segment in Hex

```
Captured bytes (TCP header, no options):
45 00 00 3C 1A 1B 40 00 40 06 B1 72
C0 A8 01 01  ← src IP: 192.168.1.1
C0 A8 01 64  ← dst IP: 192.168.1.100

TCP header:
C3 50        ← src port: 50000
00 50        ← dst port: 80 (HTTP)
00 00 00 64  ← seq number: 100
00 00 00 00  ← ack number: 0
60           ← data offset: 6 (6×4=24 bytes header), reserved=0
02           ← flags: 0x02 = SYN
FF FF        ← window: 65535
91 E6        ← checksum
00 00        ← urgent pointer: 0

Then options (4 bytes because offset=6 not 5):
02 04 05 B4  ← MSS option: kind=2, len=4, value=0x05B4=1460
```

---

## 22. Mental Models and Summary

### Mental Model 1: TCP as a Pipe with Two Valves

```
CLIENT SIDE                                    SERVER SIDE
     |                                              |
     |====== DATA STREAM (client→server) ==========>|
     |                                              |
     |<===== DATA STREAM (server→client) ===========|
     |                                              |

Each direction is independent:
- Each side controls its OWN send direction
- FIN closes ONE direction (the sender's)
- Both FINs must be exchanged to close both directions
- RST closes BOTH directions immediately
```

### Mental Model 2: TCP as a Sliding Ruler

```
Sequence space (0 to 2^32):
|==========================ACKED==========|====IN FLIGHT====|===CAN SEND===|===BLOCKED===|
                                          ^                 ^              ^
                                       SND.UNA           SND.NXT   SND.UNA+min(RWND,CWND)

- The ruler "slides right" as ACKs arrive
- Width of "can send" region = min(RWND, CWND)
- RWND: receiver's buffer available (flow control)
- CWND: network capacity estimate (congestion control)
```

### Mental Model 3: TCP States as a Story

```
LISTEN     → "I'm a server, waiting at the door"
SYN-SENT   → "I knocked on the door, waiting for answer"
SYN-RECV   → "Someone knocked, I answered, waiting for them to confirm"
ESTABLISHED → "We're talking — the conversation is live"
FIN-WAIT-1 → "I said goodbye, waiting for them to hear it"
FIN-WAIT-2 → "They heard my goodbye, now waiting for theirs"
CLOSE-WAIT → "They said goodbye to me, my app needs to say goodbye back"
CLOSING    → "We said goodbye simultaneously, verifying"
LAST-ACK   → "I said goodbye, one last acknowledgement needed"
TIME-WAIT  → "The conversation is over, but I'm waiting for echoes to die"
CLOSED     → "No connection exists"
```

### Mental Model 4: Reliability as a Post Office

```
SENDER                         NETWORK                      RECEIVER
  |                               |                              |
  | [Package 1] ──────────────────────────────────────────────>  |
  | [Package 2] ───────────────────── LOST ───────────────────X  |
  | [Package 3] ──────────────────────────────────────────────>  |
  |                               |                              |
  |                   [Receipt for 1+3, "I'm missing 2!"] <─────  |
  |                               |                              |
  | [Resend Package 2] ───────────────────────────────────────>  |
  |                               |                              |
  |                              [All received] <───────────────  |
```

### Quick Reference: Flag Combinations and Meanings

```
Flags    | Hex  | Meaning
---------|------|------------------------------------------
SYN      | 0x02 | Connection request
SYN+ACK  | 0x12 | Connection accept
ACK      | 0x10 | Pure acknowledgement / data with ACK
FIN+ACK  | 0x11 | Graceful close (one direction)
RST      | 0x04 | Abort connection
RST+ACK  | 0x14 | Abort connection with ACK
PSH+ACK  | 0x18 | Data (push to application immediately)
URG+ACK  | 0x30 | Urgent data (rare)
FIN+PSH  | 0x09 | Close after flushing (unusual)
```

### Attack Surface Summary

```
FIELD/MECHANISM     ATTACK                          DEFENSE
Sequence Numbers    Session Hijacking, RST Attack   Random ISN, RFC 5961, TLS
SYN Backlog         SYN Flood (DoS)                 SYN Cookies, backlog tuning
TIME-WAIT           Connection confusion             2×MSL enforcement
Timestamps          Uptime leak, fingerprinting     Disable or randomize offset
Window              Throttle attacks                 Monitor for window shrinkage
Keepalive           Covert channel, NAT persistence App-level heartbeats
TCP Flags           Port scan, firewall mapping     Stateful FW, honeypots
ISN prediction      Blind injection                 CSPRNG for ISN (standard)
Options             Fingerprinting                  Stack normalization
```

---

## References and Further Reading

- **RFC 793** — Transmission Control Protocol (original spec)
- **RFC 1122** — Requirements for Internet Hosts (TCP clarifications)
- **RFC 2018** — TCP Selective Acknowledgement Options (SACK)
- **RFC 2581** — TCP Congestion Control (Tahoe/Reno)
- **RFC 4987** — TCP SYN Flooding Attacks and Common Mitigations
- **RFC 5681** — TCP Congestion Control (updated)
- **RFC 5961** — Improving TCP's Robustness to Blind In-Window Attacks
- **RFC 6298** — Computing TCP's Retransmission Timer
- **RFC 7323** — TCP Extensions for High Performance (timestamps, window scale)
- **RFC 7413** — TCP Fast Open
- **RFC 9293** — Transmission Control Protocol (2022 consolidation of all TCP RFCs)
- **"TCP/IP Illustrated, Volume 1"** — W. Richard Stevens (essential reading)
- **"The TCP/IP Guide"** — Charles Kozierok
- **Google BBR Paper** — "BBR: Congestion-Based Congestion Control" (2016)
- **Beej's Guide to Network Programming** — Practical socket programming

---

*End of TCP Protocol Complete Guide*
*Version 1.0 — Covers RFC 793 through RFC 9293*

~7,500 words, 22 sections, zero fluff. Here's what's inside and why each section builds your mental model:

**The foundation (§1–3):** Why TCP exists at all, the full 32-bit header in real RFC bit-layout ASCII, and every single field explained with the "why" behind it — not just the "what."

**The lifecycle (§4–7):** Every packet of the 3-way handshake and 4-way teardown drawn out with actual SEQ/ACK numbers so the math is visible. The complete 11-state FSM with all transitions — this is what `ss` and `netstat` are showing you when you read states.

**Reliability internals (§8–11):** Sequence numbers as a byte-stream (with wrap-around and PAWS), sliding window mechanics with the sender/receiver buffer model drawn out, all four congestion control algorithms (Tahoe → Reno → CUBIC → BBR) with curve diagrams, and every retransmission timer explained.

**Advanced mechanisms (§12–17):** Every TCP option in TLV format (MSS, WSCALE, SACK, timestamps, TFO), the Nagle + Delayed ACK interaction trap that kills SSH performance, keepalive probing, TIME_WAIT's two actual reasons, half-open/half-closed states.

**Pentesting-specific (§19–21):** SYN flood + SYN cookies mechanics, session hijacking, RST injection, blind spoofing, all Nmap scan types mapped to their TCP flag behavior, OS fingerprinting table, tcpdump one-liners with the raw flags byte explained (`tcp[13] & 0x02`), and how HTTP Request Smuggling is fundamentally a TCP byte-stream ambiguity problem.

**Mental models (§22):** Four concrete mental models — the two-valve pipe, the sliding ruler, the state machine as a story, and reliability as a post office. These are what let you reason about TCP behavior you've never seen before.