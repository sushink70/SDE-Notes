# UDP Protocol — Complete & Comprehensive Guide
### From Fundamentals to Systems-Level Mastery

---

## Table of Contents

1. [Mental Model Before You Begin](#1-mental-model-before-you-begin)
2. [Networking Fundamentals — The Foundation](#2-networking-fundamentals--the-foundation)
3. [What is UDP?](#3-what-is-udp)
4. [The OSI Model and Where UDP Lives](#4-the-osi-model-and-where-udp-lives)
5. [The Internet Protocol Stack — Reality](#5-the-internet-protocol-stack--reality)
6. [UDP Header — Real Protocol Structure](#6-udp-header--real-protocol-structure)
7. [UDP Checksum — Deep Dive](#7-udp-checksum--deep-dive)
8. [UDP vs TCP — Architectural Comparison](#8-udp-vs-tcp--architectural-comparison)
9. [IP Fragmentation and UDP](#9-ip-fragmentation-and-udp)
10. [UDP Addressing — IP + Port System](#10-udp-addressing--ip--port-system)
11. [UDP Socket Programming — C](#11-udp-socket-programming--c)
12. [UDP Socket Programming — Go](#12-udp-socket-programming--go)
13. [UDP Socket Programming — Rust](#13-udp-socket-programming--rust)
14. [Broadcast UDP](#14-broadcast-udp)
15. [Multicast UDP](#15-multicast-udp)
16. [UDP Buffer Management and Kernel Internals](#16-udp-buffer-management-and-kernel-internals)
17. [Performance Characteristics and Cache Behavior](#17-performance-characteristics-and-cache-behavior)
18. [Real-World Protocols Built on UDP](#18-real-world-protocols-built-on-udp)
19. [UDP Security — Attacks and Mitigations](#19-udp-security--attacks-and-mitigations)
20. [Modern UDP Evolution — QUIC, DTLS, WebRTC](#20-modern-udp-evolution--quic-dtls-webrtc)
21. [Expert Mental Models and Problem-Solving Patterns](#21-expert-mental-models-and-problem-solving-patterns)

---

## 1. Mental Model Before You Begin

Before diving into bytes and bits, build the correct **abstract model** in your mind. This is how expert network engineers think.

### The Postal Analogy

Imagine two types of mail delivery:

- **TCP** is like **certified registered mail** — tracked, confirmed, ordered, and if the letter gets lost, it is resent. You know exactly when it arrives.
- **UDP** is like dropping a **postcard in a mailbox** — you write the address, drop it, and walk away. You do not know if it arrived, in what order if you sent many, or whether it got damaged. But it is *extremely fast* because there is zero overhead.

### The Three Core Guarantees UDP Does NOT Provide

| Property       | TCP | UDP |
|----------------|-----|-----|
| Delivery       | ✅  | ❌  |
| Ordering       | ✅  | ❌  |
| Duplication    | ✅  | ❌  |

UDP intentionally sacrifices all three for **maximum speed and minimum latency**.

### The Fundamental Trade-off

```
Reliability  <------------------------>  Speed / Simplicity
   [TCP]                                     [UDP]
```

**Expert insight:** UDP is not "broken TCP." It is a *deliberately minimal* protocol designed for situations where:
1. The application can tolerate loss (video streaming)
2. The application handles reliability itself (QUIC)
3. Latency matters more than delivery (online gaming, DNS)
4. Broadcast/multicast is needed (TCP cannot broadcast)

---

## 2. Networking Fundamentals — The Foundation

### What is a Protocol?

A **protocol** is a set of **rules** that define:
- How data is **formatted** (structure/syntax)
- How data is **transmitted** (timing/sequence)
- How data is **interpreted** (semantics)

Without agreed-upon protocols, two machines cannot communicate, just as two people speaking different languages cannot understand each other.

### What is a Packet?

A **packet** is a small, discrete unit of data that travels across a network. Instead of sending one massive stream of data, networks break data into packets. Each packet:
- Travels independently through the network
- Contains a **header** (control information: source, destination, size)
- Contains a **payload** (the actual data)
- May take a different route to the destination

### What is a Port?

A **port** is a 16-bit number (0–65535) used to identify a **specific process or service** on a machine. Think of it like apartment numbers in a building:
- The IP address is the **building address**
- The port is the **apartment number**

This way, multiple applications on the same machine can all receive network data simultaneously. The OS delivers each packet to the right process based on the port number.

**Port ranges:**
```
0     –  1023  : Well-known ports  (DNS=53, HTTP=80, HTTPS=443)
1024  – 49151  : Registered ports  (assigned by IANA)
49152 – 65535  : Ephemeral/dynamic ports (OS assigns to clients)
```

### What is a Socket?

A **socket** is an **endpoint** for communication — it is the software abstraction that represents one end of a network connection. A socket is identified by:

```
(IP address, Port number, Protocol)
```

Example socket:
```
(192.168.1.10, 54321, UDP)
```

Think of a socket as a telephone handset. To call someone, you pick up your handset (open a socket) and dial their number (specify IP:port).

---

## 3. What is UDP?

### Definition

**UDP — User Datagram Protocol** is a **connectionless, unreliable, stateless** transport-layer protocol defined in **RFC 768** (August 1980) by Jon Postel. It is part of the **Internet Protocol Suite** (TCP/IP).

The word **"datagram"** is key:
- **Data** — it carries data
- **gram** — like a telegram, it is self-contained and independent
- Each UDP packet (datagram) is **independent** — it carries its own addressing information and is processed independently of all other datagrams

### RFC 768 — The Original Specification

The entire UDP specification fits on **one page** — RFC 768 is famously tiny. This simplicity is by design. Here is what it specifies:

1. Header format (8 bytes)
2. Checksum algorithm
3. Pseudo-header construction

That is literally all. There is no connection setup, no state machine, no flow control, no retransmission logic. The design philosophy is: *"Do the minimum necessary, let the application handle the rest."*

### Connectionless — What Does This Mean?

**Connectionless** means there is **no handshake before data transfer**. Compare:

```
TCP (Connection-Oriented):
  Client                     Server
    |                           |
    |------ SYN --------------->|   (I want to connect)
    |<----- SYN-ACK ------------|   (OK, I acknowledge)
    |------ ACK --------------->|   (Acknowledged)
    |                           |
    |====== DATA TRANSFER =======|
    |                           |
    |------ FIN --------------->|   (I'm done)
    |<----- ACK ----------------|
    |<----- FIN ----------------|
    |------ ACK --------------->|


UDP (Connectionless):
  Client                     Server
    |                           |
    |------ DATAGRAM ---------->|   (data sent immediately)
    |------ DATAGRAM ---------->|   (another, independently)
    |------ DATAGRAM ---------->|   (and another)
```

In UDP, the client sends data **immediately without waiting** for any acknowledgment from the server. The server may or may not be listening. The packet may or may not arrive. UDP does not care.

### Stateless — What Does This Mean?

**Stateless** means the protocol maintains **zero state** about previous or future packets. Each UDP datagram is processed in complete isolation. The kernel:
- Does not track which packets arrived
- Does not remember past datagrams
- Does not anticipate future datagrams
- Does not assign sequence numbers

This means UDP has essentially **zero per-connection memory overhead**.

---

## 4. The OSI Model and Where UDP Lives

### What is the OSI Model?

The **Open Systems Interconnection (OSI) model** is a conceptual framework that divides network communication into **7 distinct layers**. Each layer has a specific responsibility and communicates only with the layers immediately above and below it.

```
+-------+------------------+------------------------------------------+
| Layer | Name             | Responsibility                           |
+-------+------------------+------------------------------------------+
|   7   | Application      | HTTP, DNS, SMTP — user-facing protocols  |
|   6   | Presentation     | Encryption, compression, encoding        |
|   5   | Session          | Session management, synchronization      |
|   4   | Transport        | End-to-end communication (TCP, UDP) ◄── |
|   3   | Network          | Routing between networks (IP)            |
|   2   | Data Link        | MAC addresses, frames (Ethernet)         |
|   1   | Physical         | Bits over wire, fiber, radio waves       |
+-------+------------------+------------------------------------------+
```

**UDP lives at Layer 4 — the Transport Layer.**

Its job is to provide **process-to-process communication** (via ports) on top of the **host-to-host** communication provided by IP (Layer 3).

### What Each Layer Adds

Think of each layer as adding a "wrapper" (called an **encapsulation header**) around the data as it travels down the stack:

```
Application data
      |
      v
[ UDP Header | Application Data ]         <-- Transport Layer adds UDP header
      |
      v
[ IP Header | UDP Header | App Data ]     <-- Network Layer adds IP header
      |
      v
[ Eth Header | IP | UDP | App | Eth FCS ] <-- Data Link adds Ethernet frame
      |
      v
Electrical/optical signals on wire        <-- Physical Layer
```

At the receiving end, each layer **strips** its header and passes the payload up to the next layer.

---

## 5. The Internet Protocol Stack — Reality

The real-world Internet uses a **4-layer model** (TCP/IP model), not the 7-layer OSI model. OSI is a teaching model; TCP/IP is what actually runs the Internet:

```
+------------------+---------------------------------------------+
| TCP/IP Layer     | Protocols                                   |
+------------------+---------------------------------------------+
| Application      | HTTP, HTTPS, DNS, DHCP, SNMP, NTP, RTP     |
| Transport        | TCP, UDP, SCTP                               |
| Internet         | IPv4, IPv6, ICMP, IGMP                      |
| Network Access   | Ethernet, Wi-Fi, ARP, PPP                  |
+------------------+---------------------------------------------+
```

### Full Packet Journey — UDP Datagram on the Wire

```
 Application Layer
 ┌────────────────────────────────────────────────────┐
 │  "Hello, World!"  (13 bytes of payload)            │
 └────────────────────────────────────────────────────┘
                        ↓ UDP wraps it
 Transport Layer (UDP)
 ┌────────────────┬───────────────────────────────────┐
 │  UDP Header    │  "Hello, World!"                  │
 │  (8 bytes)     │  (13 bytes)                       │
 └────────────────┴───────────────────────────────────┘
                        ↓ IP wraps it
 Internet Layer (IPv4)
 ┌──────────────────┬────────────────┬─────────────────┐
 │  IPv4 Header     │  UDP Header    │  "Hello, World!"│
 │  (20 bytes min)  │  (8 bytes)     │  (13 bytes)     │
 └──────────────────┴────────────────┴─────────────────┘
                        ↓ Ethernet wraps it
 Network Access (Ethernet)
 ┌─────────────┬──────────────────┬────────────────┬─────────────────┬─────────┐
 │  Eth Header │  IPv4 Header     │  UDP Header    │  "Hello, World!"│  FCS   │
 │  (14 bytes) │  (20 bytes)      │  (8 bytes)     │  (13 bytes)     │(4 bytes)│
 └─────────────┴──────────────────┴────────────────┴─────────────────┴─────────┘
 Total on wire: 14 + 20 + 8 + 13 + 4 = 59 bytes
```

**FCS** = Frame Check Sequence — a CRC used by Ethernet for error detection at the hardware level.

---

## 6. UDP Header — Real Protocol Structure

### The Real RFC 768 UDP Header Format

This is the **actual, real** UDP header as defined in the standard. It is exactly **8 bytes** (64 bits):

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
|           (16 bits)           |           (16 bits)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            Length             |           Checksum            |
|           (16 bits)           |           (16 bits)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                          Data (payload)                       |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**The number line at the top is the bit position counter (0–31), representing one 32-bit word per row.**

### Field-by-Field Breakdown

#### Field 1: Source Port (bits 0–15, 2 bytes)

```
Bits:    0        7 8       15
         +---------+---------+
         |   Source Port     |
         +---------+---------+
         |   0x1F 0x90      | = 8080 in decimal
```

- **Size:** 16 bits (values 0–65535)
- **Purpose:** Identifies the **sending process's port** on the source machine
- **Optional in UDP:** If the source does not need a reply, this field can be set to **zero** (0x0000)
- **Example:** A client sending a DNS query might have source port 54321 (ephemeral)

**Why optional?** Unlike TCP, UDP is used for one-way transmissions (like syslog). If the sender never expects a reply, there's no need to tell the receiver where to respond.

#### Field 2: Destination Port (bits 16–31, 2 bytes)

```
Bits:   16       23 24      31
         +---------+---------+
         | Destination Port  |
         +---------+---------+
         |   0x00  0x35     | = 53 in decimal (DNS)
```

- **Size:** 16 bits (values 0–65535)
- **Purpose:** Identifies the **target process** on the destination machine
- **Required:** Must always be set. This is how the kernel knows which process to deliver the datagram to.
- **Example:** DNS server listens on port 53

#### Field 3: Length (bits 32–47, 2 bytes)

```
Bits:   32       39 40      47
         +---------+---------+
         |       Length      |
         +---------+---------+
         |   0x00  0x15     | = 21 in decimal
```

- **Size:** 16 bits
- **Purpose:** The **total length** of the UDP datagram: UDP header (8 bytes) + payload
- **Minimum value:** 8 (a UDP header with zero payload)
- **Maximum value:** 65535 (theoretical; IP limits it further)
- **Example:** If payload is 13 bytes, Length = 8 + 13 = 21

**Important:** The maximum payload size is:
```
Max UDP payload = 65535 - 8 (UDP header) - 20 (IPv4 header) = 65507 bytes
```

For IPv6:
```
Max UDP payload = 65535 - 8 (UDP header) - 40 (IPv6 header) = 65487 bytes
```

#### Field 4: Checksum (bits 48–63, 2 bytes)

```
Bits:   48       55 56      63
         +---------+---------+
         |      Checksum     |
         +---------+---------+
         |   0xAB  0xCD     | = checksum value
```

- **Size:** 16 bits
- **Purpose:** Error detection — detects corruption in the header and payload
- **In IPv4:** Optional. A value of 0x0000 means "no checksum"
- **In IPv6:** **Mandatory** (since IPv6 removed the IP-level checksum)
- **Algorithm:** One's complement sum (detailed in Section 7)

### Complete Visual — A Real DNS Query UDP Datagram

```
Byte Offset  Content (hex)   Description
-----------  -------------   -----------
  Ethernet Header (14 bytes):
  00-05      FF FF FF FF FF FF   Destination MAC (broadcast)
  06-11      AA BB CC DD EE FF   Source MAC
  12-13      08 00               EtherType: IPv4

  IPv4 Header (20 bytes):
  14         45                  Version=4, IHL=5 (20 bytes)
  15         00                  DSCP/ECN
  16-17      00 39               Total Length = 57
  18-19      AB CD               Identification
  20-21      40 00               Flags + Fragment Offset (DF=1)
  22         40                  TTL = 64
  23         11                  Protocol = 17 (UDP)
  24-25      checksum            IP Header Checksum
  26-29      C0 A8 01 0A         Source IP: 192.168.1.10
  30-33      08 08 08 08         Destination IP: 8.8.8.8 (Google DNS)

  UDP Header (8 bytes):
  34-35      D4 31               Source Port: 54321
  36-37      00 35               Destination Port: 53 (DNS)
  38-39      00 25               Length: 37 (8 header + 29 payload)
  40-41      XX XX               Checksum

  DNS Payload (29 bytes):
  42-...     [DNS query bytes]
```

---

## 7. UDP Checksum — Deep Dive

### What is a Checksum?

A **checksum** is a simple error-detection mechanism. You compute a mathematical value over a block of data before sending it, include that value in the packet, and the receiver recomputes the value. If they match, the data (probably) arrived intact. If they differ, it was corrupted.

The UDP checksum uses the **Internet Checksum Algorithm** (RFC 1071):
- Treats data as a sequence of 16-bit integers
- Sums them all using **one's complement arithmetic**
- The result is the checksum

### One's Complement Arithmetic

**One's complement** is a way of representing negative numbers in binary where:
- You negate a number by flipping all its bits
- -0 and +0 are both valid (two representations of zero)

For our purposes, the key property is: **carry out of the most significant bit wraps around to the least significant bit** (called "end-around carry").

```
Normal addition:   1111 + 0001 = 1 0000 (carry goes out, lost)
One's complement:  1111 + 0001 = 0001   (carry wraps around)
                               = 0000 + 0001 = 0001
```

### The Pseudo-Header — Critical Concept

**The UDP checksum is computed over more than just the UDP header and data.** It also includes a **pseudo-header** — a fictional header containing IP-level information that is prepended **only for checksum calculation** and is **never transmitted on the wire**.

This is a design choice: it catches errors where packets are delivered to the wrong IP address (which the UDP header alone cannot detect, since it only has ports, not IP addresses).

**IPv4 Pseudo-Header:**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Source Address                         |
|                          (32 bits)                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Destination Address                      |
|                          (32 bits)                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|      Zero     |   Protocol    |          UDP Length           |
|    (8 bits)   |   (8 bits)    |           (16 bits)           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Source Address:** 32-bit sender IPv4 address
- **Destination Address:** 32-bit receiver IPv4 address
- **Zero:** 8-bit field, always 0 (padding)
- **Protocol:** 8-bit IP protocol number for UDP = 17 (0x11)
- **UDP Length:** Same as the Length field in the UDP header

**IPv6 Pseudo-Header:**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                    Source Address (128 bits)                  |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                  Destination Address (128 bits)               |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    UDP Length (32 bits)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Zeros (24 bits)   |  Next Header (8 bits)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Checksum Computation — Step-by-Step Algorithm

```
Checksum Computation:
─────────────────────
Input: [pseudo-header] + [UDP header] + [payload]
       with checksum field set to 0x0000

Step 1: Pad data to even length (append 0x00 if odd number of bytes)
Step 2: Split into 16-bit words
Step 3: Sum all 16-bit words using one's complement addition
Step 4: Take the one's complement of the sum (flip all bits)
Step 5: If result is 0xFFFF, use 0xFFFF (not 0x0000)
        If result is 0x0000, use 0xFFFF (0 means "no checksum")

Verification (receiver side):
Step 1: Repeat Steps 1-3 above (including the actual checksum field)
Step 2: If result is 0xFFFF → no error detected
        If result is anything else → error (discard packet)
```

### Worked Example in C

```c
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <arpa/inet.h>

/* -----------------------------------------------------------------------
 * Internet checksum (RFC 1071)
 * Computes one's complement sum of all 16-bit words in the buffer.
 * Used as a building block for UDP/TCP checksum computation.
 * ----------------------------------------------------------------------- */
static uint32_t checksum_accumulate(const void *data, size_t len, uint32_t sum) {
    const uint16_t *ptr = (const uint16_t *)data;

    /* Sum complete 16-bit words */
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    /* Handle trailing odd byte — pad with zero on the right */
    if (len == 1) {
        uint16_t last = 0;
        *(uint8_t *)&last = *(const uint8_t *)ptr; /* host byte order */
        sum += last;
    }

    return sum;
}

/* Fold 32-bit sum into 16-bit one's complement checksum */
static uint16_t checksum_finalize(uint32_t sum) {
    /* Fold the carries */
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    /* One's complement */
    return (uint16_t)(~sum);
}

/* -----------------------------------------------------------------------
 * Pseudo-header for IPv4 UDP checksum (RFC 768)
 * Never transmitted — used only for checksum calculation.
 * ----------------------------------------------------------------------- */
typedef struct __attribute__((packed)) {
    uint32_t src_addr;    /* Source IP address (network byte order)      */
    uint32_t dst_addr;    /* Destination IP address (network byte order)  */
    uint8_t  zero;        /* Always 0                                     */
    uint8_t  protocol;    /* IP Protocol number (17 for UDP)              */
    uint16_t udp_length;  /* UDP Length field (network byte order)        */
} ipv4_pseudo_header_t;

/* -----------------------------------------------------------------------
 * UDP Header (RFC 768) — exactly 8 bytes
 * ----------------------------------------------------------------------- */
typedef struct __attribute__((packed)) {
    uint16_t src_port;    /* Source port (optional, 0 if unused)          */
    uint16_t dst_port;    /* Destination port                             */
    uint16_t length;      /* Total length: UDP header + payload (bytes)   */
    uint16_t checksum;    /* One's complement checksum (0=disabled in v4) */
} udp_header_t;

/* -----------------------------------------------------------------------
 * Compute UDP checksum over pseudo-header + UDP header + payload.
 *
 * Returns the checksum in network byte order.
 * A return value of 0xFFFF means "all ones" (valid checksum).
 * A return value of 0x0000 would be sent as 0xFFFF per RFC 768.
 * ----------------------------------------------------------------------- */
uint16_t udp_compute_checksum(
    uint32_t    src_ip,    /* network byte order */
    uint32_t    dst_ip,    /* network byte order */
    uint16_t    src_port,  /* network byte order */
    uint16_t    dst_port,  /* network byte order */
    const void *payload,
    uint16_t    payload_len)
{
    const uint16_t UDP_PROTOCOL  = 17;
    const uint16_t udp_total_len = htons(sizeof(udp_header_t) + payload_len);

    /* Construct pseudo-header */
    ipv4_pseudo_header_t pseudo = {
        .src_addr   = src_ip,
        .dst_addr   = dst_ip,
        .zero       = 0,
        .protocol   = UDP_PROTOCOL,
        .udp_length = udp_total_len,
    };

    /* Construct UDP header with checksum field zeroed */
    udp_header_t udp_hdr = {
        .src_port = src_port,
        .dst_port = dst_port,
        .length   = udp_total_len,
        .checksum = 0x0000,  /* zero for computation */
    };

    /* Accumulate all components */
    uint32_t sum = 0;
    sum = checksum_accumulate(&pseudo,   sizeof(pseudo),   sum);
    sum = checksum_accumulate(&udp_hdr,  sizeof(udp_hdr),  sum);
    sum = checksum_accumulate(payload,   payload_len,       sum);

    uint16_t result = checksum_finalize(sum);

    /* RFC 768: If computed checksum is 0, transmit as 0xFFFF */
    return (result == 0x0000) ? 0xFFFF : result;
}
```

---

## 8. UDP vs TCP — Architectural Comparison

### State Machine Comparison

**TCP State Machine (simplified):**
```
CLOSED
  │
  │ connect()         listen()
  ↓                      ↓
SYN_SENT  ────────── LISTEN
  │  (SYN received)       │ (SYN received)
  │                       ↓
  │                  SYN_RECEIVED
  │  (SYN-ACK)            │ (ACK received)
  ↓                       ↓
ESTABLISHED ◄───────── ESTABLISHED
  │
  │ (close)
  ↓
FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED
```

**UDP State Machine:**
```
CLOSED
  │
  │ bind() / sendto()
  ↓
OPEN (ready to send/receive)
  │
  │ close()
  ↓
CLOSED
```

UDP has essentially **no state machine**. You open a socket, send or receive, and close. There are no connection states to track.

### Detailed Feature Comparison

```
┌─────────────────────────┬──────────────────────────┬──────────────────────────┐
│ Feature                 │ TCP                      │ UDP                      │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Connection              │ Required (3-way HSK)     │ Not required             │
│ Reliability             │ Guaranteed               │ Not guaranteed           │
│ Ordering                │ Guaranteed (seq nums)    │ Not guaranteed           │
│ Error detection         │ Checksum                 │ Checksum (optional v4)   │
│ Error recovery          │ Retransmission           │ None                     │
│ Flow control            │ Sliding window           │ None                     │
│ Congestion control      │ AIMD (Reno/CUBIC/BBR)    │ None (app responsible)   │
│ Header size             │ 20–60 bytes              │ 8 bytes (fixed)          │
│ Data boundaries         │ Byte stream (no bounds)  │ Preserved (datagram)     │
│ Broadcast support       │ None                     │ Yes                      │
│ Multicast support       │ None                     │ Yes                      │
│ Setup latency           │ 1 RTT minimum            │ 0 (fire immediately)     │
│ Teardown                │ Required (FIN/ACK)       │ Not required             │
│ State per connection    │ ~20 KB kernel state      │ ~0 bytes                 │
│ Throughput              │ High but regulated       │ Maximum possible         │
│ Latency                 │ Higher (ACK wait)        │ Lowest possible          │
│ Packet size control     │ MSS negotiation          │ App controls size        │
│ Half-open connections   │ Possible (attack vector) │ Not applicable           │
│ Message boundaries      │ None (stream)            │ Preserved per datagram   │
└─────────────────────────┴──────────────────────────┴──────────────────────────┘
```

### Message Boundaries — Critical Distinction

This is one of the most important practical differences:

**TCP is a byte stream:**
```
Sender writes:   [MSG1: 100 bytes] [MSG2: 200 bytes]
Receiver reads:  [100 bytes]  or  [150 bytes] [150 bytes]  or  [300 bytes]
                 (ANY combination is possible — TCP does not preserve boundaries)
```

**UDP preserves message boundaries:**
```
Sender sends:    [Datagram1: 100 bytes] [Datagram2: 200 bytes]
Receiver reads:  [100 bytes]             [200 bytes]
                 (Always complete datagrams, always in distinct recvfrom() calls)
```

This means with TCP you must implement your own **framing protocol** (e.g., length-prefix: send the message length before the message). With UDP, each `recvfrom()` call delivers exactly one complete datagram.

---

## 9. IP Fragmentation and UDP

### What is Fragmentation?

Every network link has a **Maximum Transmission Unit (MTU)** — the largest packet it can carry. For Ethernet, MTU is typically **1500 bytes**.

When a UDP datagram (including IP header) exceeds the MTU, the IP layer **fragments** it into multiple smaller IP packets that are reassembled at the destination.

**MTU Path:**
```
Sender (MTU=1500) ──── Router ──── Router (MTU=576) ──── Receiver
                                   ↑
                          Fragmentation happens here
```

### Fragmentation Fields in IPv4

The IPv4 header has specific fields for fragmentation:

```
IPv4 Header Fragmentation Fields:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Identification         |Flags|      Fragment Offset    |
|           (16 bits)           | (3) |        (13 bits)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Flags:
  Bit 0: Reserved, must be 0
  Bit 1: DF (Don't Fragment) — if set, router MUST NOT fragment
  Bit 2: MF (More Fragments) — if set, more fragments follow

Fragment Offset: Offset of this fragment's data in the original datagram
                 Units: 8-byte blocks (multiply by 8 to get byte offset)
```

### Fragmentation Example

Sending a 4000-byte UDP payload over Ethernet (MTU=1500):

```
Original datagram:
┌──────────────┬──────────────┬─────────────────────────────────────┐
│  IP Header   │  UDP Header  │  Payload (4000 bytes)               │
│  (20 bytes)  │  (8 bytes)   │                                     │
└──────────────┴──────────────┴─────────────────────────────────────┘
Total = 4028 bytes > 1500 MTU → FRAGMENTED

Fragment 1 (1500 bytes):
┌──────────────┬──────────────┬─────────────────────────────────────┐
│  IP Header   │  UDP Header  │  Payload bytes 0–1471 (1472 bytes)  │
│  MF=1,Off=0  │  (8 bytes)   │  (only in first fragment)           │
└──────────────┴──────────────┴─────────────────────────────────────┘
Data portion: 1480 bytes (1472 payload + 8 UDP header), offset=0

Fragment 2 (1500 bytes):
┌──────────────┬─────────────────────────────────────────────────────┐
│  IP Header   │  Payload bytes 1472–2951 (1480 bytes)               │
│  MF=1,Off=185│  (no UDP header in fragments 2+)                    │
└──────────────┴─────────────────────────────────────────────────────┘
Offset = 1480/8 = 185

Fragment 3 (1048 bytes):
┌──────────────┬─────────────────────────────────────────────────────┐
│  IP Header   │  Payload bytes 2952–3999 (1048 bytes)               │
│  MF=0,Off=370│                                                     │
└──────────────┴─────────────────────────────────────────────────────┘
Offset = 2960/8 = 370, MF=0 (last fragment)
```

**Key insight:** Only the **first fragment** contains the UDP header. The receiver reassembles all fragments before passing to the UDP layer.

### Problems with Fragmentation

1. **Performance:** Fragmentation is expensive — it requires copying and managing fragments
2. **Reliability amplification:** If **any** fragment is lost, the **entire datagram** is dropped and must be resent at the application level
3. **Firewall issues:** Firewalls often cannot inspect or filter fragmented packets properly
4. **NAT issues:** Some NAT devices mishandle fragments

### Path MTU Discovery (PMTUD)

Modern systems use **Path MTU Discovery** (RFC 1191) to avoid fragmentation:

```
1. Sender sets DF=1 (Don't Fragment) in IPv4
2. Sends large packet
3. If router needs to fragment, it drops packet and sends ICMP "Fragmentation Needed" back
4. Sender reduces packet size and retries
5. Repeat until optimal MTU is found

Flow:
Client ──[DF=1, 1500 bytes]──► Router
Client ◄──[ICMP: Too Big, MTU=1280]─── Router
Client ──[DF=1, 1280 bytes]──► Router ──► ... ──► Server  ✓
```

**Best practice:** UDP applications should limit payload to safe sizes:
- **Safe for most networks:** ≤ 508 bytes (IPv4 minimum MTU 576 - 60 byte max IP header - 8 byte UDP)
- **Safe for Ethernet:** ≤ 1472 bytes (1500 - 20 IP - 8 UDP)
- **Safe across Internet:** ≤ 1232 bytes (common PMTUD-safe value used by DNS-over-UDP)

---

## 10. UDP Addressing — IP + Port System

### The Socket 4-Tuple

A UDP communication flow is identified by a **4-tuple**:
```
(Source IP, Source Port, Destination IP, Destination Port)
```

Example:
```
Client: 192.168.1.10:54321  ──UDP──►  Server: 8.8.8.8:53
```

### Unicast, Broadcast, and Multicast Addressing

```
┌─────────────┬──────────────────────┬────────────────────────────────────┐
│ Type        │ Destination          │ Who receives?                      │
├─────────────┼──────────────────────┼────────────────────────────────────┤
│ Unicast     │ Single IP (e.g.      │ One specific host                  │
│             │ 192.168.1.10)        │                                    │
├─────────────┼──────────────────────┼────────────────────────────────────┤
│ Broadcast   │ Network broadcast    │ ALL hosts on local network segment │
│             │ (e.g. 192.168.1.255) │ (does not cross routers)          │
│             │ or 255.255.255.255   │                                    │
├─────────────┼──────────────────────┼────────────────────────────────────┤
│ Multicast   │ Class D address      │ All hosts SUBSCRIBED to that group │
│             │ (224.0.0.0/4)        │ (can cross routers with IGMP)      │
└─────────────┴──────────────────────┴────────────────────────────────────┘
```

### Port Number Registration (IANA)

Well-known UDP ports:
```
Port    Protocol    Service
────    ────────    ──────────────────────────────────────────
7       UDP         Echo
53      UDP/TCP     DNS (Domain Name System)
67      UDP         DHCP Server
68      UDP         DHCP Client
69      UDP         TFTP (Trivial File Transfer Protocol)
123     UDP         NTP (Network Time Protocol)
161     UDP         SNMP (Simple Network Management Protocol)
162     UDP         SNMP Trap
514     UDP         Syslog
1194    UDP         OpenVPN
4500    UDP         IPsec NAT Traversal
5353    UDP         mDNS (Multicast DNS)
5004    UDP         RTP (Real-time Transport Protocol)
5005    UDP         RTCP (RTP Control Protocol)
```

---

## 11. UDP Socket Programming — C

### Concepts Before Code

**Socket API** is a POSIX standard interface to network communication. Key system calls for UDP:

| Function    | Purpose                                      |
|-------------|----------------------------------------------|
| `socket()`  | Create a socket file descriptor              |
| `bind()`    | Assign a local address/port to the socket    |
| `sendto()`  | Send a datagram to a specific address        |
| `recvfrom()`| Receive a datagram and learn sender's address|
| `close()`   | Release the socket                           |

**Why `sendto()` instead of `send()`?** Because UDP is connectionless — each call must specify the destination address since there is no established connection.

### UDP Server — C (Production-grade)

```c
/*
 * udp_server.c — Production-grade UDP echo server
 *
 * Demonstrates:
 *   - Proper error handling with errno reporting
 *   - Buffer size control via setsockopt
 *   - Signal-safe shutdown
 *   - Input validation
 *   - IPv4/IPv6 portability via getaddrinfo
 *
 * Compile: gcc -Wall -Wextra -O2 -o udp_server udp_server.c
 * Usage:   ./udp_server 9000
 */

#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

/* ── Constants ─────────────────────────────────────────────────── */
#define MAX_DATAGRAM_SIZE   65507   /* Max UDP payload over IPv4     */
#define RECV_BUF_SIZE       (1 << 20) /* 1 MiB kernel receive buffer */
#define SEND_BUF_SIZE       (1 << 20) /* 1 MiB kernel send buffer    */
#define BACKLOG             128     /* Not used in UDP but idiomatic */

/* ── Global shutdown flag (set by signal handler) ───────────────── */
static volatile sig_atomic_t g_running = 1;

static void signal_handler(int signum) {
    (void)signum;
    g_running = 0;
}

/* ── Helper: configure signal handlers ─────────────────────────── */
static int setup_signals(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;  /* No SA_RESTART — allow EINTR for clean shutdown */

    if (sigaction(SIGINT,  &sa, NULL) < 0) return -1;
    if (sigaction(SIGTERM, &sa, NULL) < 0) return -1;
    return 0;
}

/* ── Helper: set socket buffer sizes ───────────────────────────── */
static int set_socket_buffers(int sockfd) {
    int rcvbuf = RECV_BUF_SIZE;
    int sndbuf = SEND_BUF_SIZE;

    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf)) < 0) {
        /* Non-fatal: OS may cap this; log and continue */
        fprintf(stderr, "Warning: setsockopt SO_RCVBUF: %s\n", strerror(errno));
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf)) < 0) {
        fprintf(stderr, "Warning: setsockopt SO_SNDBUF: %s\n", strerror(errno));
    }
    return 0;
}

/* ── Helper: format peer address as "ip:port" string ───────────── */
static void format_peer(const struct sockaddr_storage *addr, socklen_t addrlen,
                         char *buf, size_t buflen) {
    char host[NI_MAXHOST];
    char serv[NI_MAXSERV];

    int ret = getnameinfo((const struct sockaddr *)addr, addrlen,
                           host, sizeof(host),
                           serv, sizeof(serv),
                           NI_NUMERICHOST | NI_NUMERICSERV);
    if (ret != 0) {
        snprintf(buf, buflen, "<unknown>");
        return;
    }
    snprintf(buf, buflen, "%s:%s", host, serv);
}

/* ── Main server loop ───────────────────────────────────────────── */
int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *port_str = argv[1];

    /* ── Resolve bind address ──────────────────────────────── */
    struct addrinfo hints = {
        .ai_family   = AF_UNSPEC,    /* Accept IPv4 or IPv6      */
        .ai_socktype = SOCK_DGRAM,   /* UDP socket               */
        .ai_flags    = AI_PASSIVE,   /* Bind to all interfaces   */
        .ai_protocol = IPPROTO_UDP,
    };

    struct addrinfo *res = NULL;
    int gai_ret = getaddrinfo(NULL, port_str, &hints, &res);
    if (gai_ret != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(gai_ret));
        return EXIT_FAILURE;
    }

    /* ── Create socket ─────────────────────────────────────── */
    int sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sockfd < 0) {
        perror("socket");
        freeaddrinfo(res);
        return EXIT_FAILURE;
    }

    /* Allow reuse of port immediately after restart */
    int opt = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt SO_REUSEADDR");
        /* Non-fatal */
    }

    set_socket_buffers(sockfd);

    /* ── Bind to port ──────────────────────────────────────── */
    if (bind(sockfd, res->ai_addr, res->ai_addrlen) < 0) {
        perror("bind");
        close(sockfd);
        freeaddrinfo(res);
        return EXIT_FAILURE;
    }
    freeaddrinfo(res);
    res = NULL;

    /* ── Setup signals ─────────────────────────────────────── */
    if (setup_signals() < 0) {
        perror("sigaction");
        close(sockfd);
        return EXIT_FAILURE;
    }

    /* ── Allocate receive buffer ───────────────────────────── */
    char *recv_buf = malloc(MAX_DATAGRAM_SIZE);
    if (!recv_buf) {
        perror("malloc");
        close(sockfd);
        return EXIT_FAILURE;
    }

    printf("UDP echo server listening on port %s\n", port_str);

    /* ── Main receive loop ─────────────────────────────────── */
    while (g_running) {
        struct sockaddr_storage peer_addr;
        socklen_t peer_addrlen = sizeof(peer_addr);

        /* recvfrom returns number of bytes in the datagram, or -1 on error */
        ssize_t nbytes = recvfrom(
            sockfd,
            recv_buf, MAX_DATAGRAM_SIZE,
            0,   /* flags: none */
            (struct sockaddr *)&peer_addr, &peer_addrlen
        );

        if (nbytes < 0) {
            if (errno == EINTR) {
                /* Signal interrupted the call — check g_running */
                continue;
            }
            perror("recvfrom");
            break;
        }

        /* ── Log the received datagram ───────────────────── */
        char peer_str[INET6_ADDRSTRLEN + 8];
        format_peer(&peer_addr, peer_addrlen, peer_str, sizeof(peer_str));
        printf("Received %zd bytes from %s\n", nbytes, peer_str);

        /* ── Echo it back ────────────────────────────────── */
        ssize_t sent = sendto(
            sockfd,
            recv_buf, (size_t)nbytes,
            0,   /* flags: none */
            (const struct sockaddr *)&peer_addr, peer_addrlen
        );

        if (sent < 0) {
            if (errno == EINTR) continue;
            perror("sendto");
            /* UDP: sendto errors are usually not fatal, continue */
        } else if (sent != nbytes) {
            fprintf(stderr, "Partial send: sent %zd of %zd bytes\n", sent, nbytes);
        }
    }

    /* ── Cleanup ───────────────────────────────────────────── */
    printf("\nShutting down.\n");
    free(recv_buf);
    close(sockfd);
    return EXIT_SUCCESS;
}
```

### UDP Client — C (Production-grade)

```c
/*
 * udp_client.c — Production-grade UDP client
 *
 * Compile: gcc -Wall -Wextra -O2 -o udp_client udp_client.c
 * Usage:   ./udp_client 127.0.0.1 9000 "Hello, World!"
 */

#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/time.h>

/* ── Constants ─────────────────────────────────────────────────── */
#define RECV_TIMEOUT_SEC    3     /* Wait 3 seconds for echo reply  */
#define MAX_RESPONSE_SIZE   65507

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <host> <port> <message>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *host    = argv[1];
    const char *port    = argv[2];
    const char *message = argv[3];
    size_t      msglen  = strlen(message);

    /* ── Resolve destination address ───────────────────────── */
    struct addrinfo hints = {
        .ai_family   = AF_UNSPEC,
        .ai_socktype = SOCK_DGRAM,
        .ai_protocol = IPPROTO_UDP,
    };

    struct addrinfo *res = NULL;
    int gai = getaddrinfo(host, port, &hints, &res);
    if (gai != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(gai));
        return EXIT_FAILURE;
    }

    /* ── Create socket ─────────────────────────────────────── */
    int sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sockfd < 0) {
        perror("socket");
        freeaddrinfo(res);
        return EXIT_FAILURE;
    }

    /* ── Set receive timeout ───────────────────────────────── */
    struct timeval tv = { .tv_sec = RECV_TIMEOUT_SEC, .tv_usec = 0 };
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0) {
        perror("setsockopt SO_RCVTIMEO");
        /* non-fatal */
    }

    /* ── Send datagram ─────────────────────────────────────── */
    ssize_t sent = sendto(
        sockfd,
        message, msglen,
        0,
        res->ai_addr, res->ai_addrlen
    );

    if (sent < 0) {
        perror("sendto");
        freeaddrinfo(res);
        close(sockfd);
        return EXIT_FAILURE;
    }

    printf("Sent %zd bytes to %s:%s\n", sent, host, port);

    /* ── Receive echo response ─────────────────────────────── */
    char response_buf[MAX_RESPONSE_SIZE];
    struct sockaddr_storage from_addr;
    socklen_t from_addrlen = sizeof(from_addr);

    ssize_t nbytes = recvfrom(
        sockfd,
        response_buf, sizeof(response_buf) - 1,  /* -1 for null terminator */
        0,
        (struct sockaddr *)&from_addr, &from_addrlen
    );

    if (nbytes < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            fprintf(stderr, "Timeout: no response received within %d seconds\n",
                    RECV_TIMEOUT_SEC);
        } else {
            perror("recvfrom");
        }
        freeaddrinfo(res);
        close(sockfd);
        return EXIT_FAILURE;
    }

    response_buf[nbytes] = '\0';  /* null-terminate for printf */
    printf("Received %zd bytes: \"%s\"\n", nbytes, response_buf);

    freeaddrinfo(res);
    close(sockfd);
    return EXIT_SUCCESS;
}
```

---

## 12. UDP Socket Programming — Go

### Go's net Package — Key Abstractions

Go provides a clean, idiomatic network API. Key types for UDP:

| Type / Function       | Purpose                                          |
|-----------------------|--------------------------------------------------|
| `net.ResolveUDPAddr`  | Parse "host:port" into `*net.UDPAddr`            |
| `net.ListenUDP`       | Create a listening UDP socket (server)           |
| `net.DialUDP`         | Create a connected UDP socket (client)           |
| `conn.ReadFromUDP`    | Receive a datagram + sender address              |
| `conn.WriteToUDP`     | Send a datagram to a specific address            |
| `conn.ReadFrom`       | Generic (implements `net.PacketConn`)            |
| `conn.WriteTo`        | Generic send                                     |

### UDP Server — Go

```go
// udp_server.go — Production-grade UDP echo server in Go
//
// Key concepts demonstrated:
//   - Graceful shutdown via context + OS signals
//   - Worker goroutines with a bounded pool
//   - Structured error handling (no panic in production)
//   - Configurable buffer sizes
//
// Usage: go run udp_server.go :9000

package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// ── Constants ───────────────────────────────────────────────────────────────

const (
	maxDatagramSize = 65507         // Maximum UDP payload over IPv4
	readBufferSize  = 1 << 20      // 1 MiB OS receive buffer
	numWorkers      = 4            // Parallel datagram processors
	readDeadline    = 500 * time.Millisecond // How long to block on read
)

// ── Datagram represents a received UDP packet ───────────────────────────────

type Datagram struct {
	Payload []byte
	From    *net.UDPAddr
}

// ── Server encapsulates the UDP server state ─────────────────────────────────

type Server struct {
	conn    *net.UDPConn
	logger  *slog.Logger
	queue   chan Datagram
	wg      sync.WaitGroup
}

// NewServer creates and initializes a UDP server bound to addr.
func NewServer(addr string, logger *slog.Logger) (*Server, error) {
	udpAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		return nil, fmt.Errorf("resolve address %q: %w", addr, err)
	}

	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		return nil, fmt.Errorf("listen UDP on %q: %w", addr, err)
	}

	// Set kernel receive buffer size
	if err := conn.SetReadBuffer(readBufferSize); err != nil {
		logger.Warn("failed to set read buffer", "error", err)
		// non-fatal: OS will use its default
	}
	if err := conn.SetWriteBuffer(readBufferSize); err != nil {
		logger.Warn("failed to set write buffer", "error", err)
	}

	return &Server{
		conn:   conn,
		logger: logger,
		queue:  make(chan Datagram, numWorkers*4), // buffered channel
	}, nil
}

// Run starts the server and blocks until ctx is cancelled.
func (s *Server) Run(ctx context.Context) error {
	s.logger.Info("UDP server started", "local_addr", s.conn.LocalAddr())

	// Start worker goroutines that process datagrams
	for i := range numWorkers {
		s.wg.Add(1)
		go s.worker(ctx, i)
	}

	// Read loop — runs in main goroutine
	err := s.readLoop(ctx)

	// Signal workers to stop by closing the queue channel
	close(s.queue)
	s.wg.Wait()

	return err
}

// readLoop continuously reads datagrams from the UDP socket.
func (s *Server) readLoop(ctx context.Context) error {
	buf := make([]byte, maxDatagramSize)

	for {
		// Check for cancellation (non-blocking)
		select {
		case <-ctx.Done():
			return nil
		default:
		}

		// Set a deadline so we can check ctx periodically
		deadline := time.Now().Add(readDeadline)
		if err := s.conn.SetReadDeadline(deadline); err != nil {
			return fmt.Errorf("set read deadline: %w", err)
		}

		n, from, err := s.conn.ReadFromUDP(buf)
		if err != nil {
			var netErr net.Error
			if errors.As(err, &netErr) && netErr.Timeout() {
				// Normal: deadline expired, loop and check ctx
				continue
			}
			if errors.Is(err, net.ErrClosed) {
				return nil // Socket closed cleanly
			}
			return fmt.Errorf("read from UDP: %w", err)
		}

		// Copy payload — buf will be reused in next iteration
		payload := make([]byte, n)
		copy(payload, buf[:n])

		// Non-blocking send to queue (drop if queue full — UDP is lossy by design)
		select {
		case s.queue <- Datagram{Payload: payload, From: from}:
		default:
			s.logger.Warn("queue full, dropping datagram", "from", from)
		}
	}
}

// worker processes datagrams from the queue.
func (s *Server) worker(ctx context.Context, id int) {
	defer s.wg.Done()
	s.logger.Debug("worker started", "id", id)

	for dg := range s.queue {
		// Context check inside the loop
		select {
		case <-ctx.Done():
			return
		default:
		}

		s.handleDatagram(dg)
	}

	s.logger.Debug("worker stopped", "id", id)
}

// handleDatagram processes a single received datagram (echo it back).
func (s *Server) handleDatagram(dg Datagram) {
	s.logger.Info("received datagram",
		"from", dg.From,
		"bytes", len(dg.Payload),
	)

	// Echo the datagram back to the sender
	n, err := s.conn.WriteToUDP(dg.Payload, dg.From)
	if err != nil {
		s.logger.Error("failed to send echo", "to", dg.From, "error", err)
		return
	}
	if n != len(dg.Payload) {
		s.logger.Warn("partial write",
			"expected", len(dg.Payload),
			"actual", n,
		)
	}
}

// Close shuts down the server's UDP socket.
func (s *Server) Close() error {
	return s.conn.Close()
}

// ── main ─────────────────────────────────────────────────────────────────────

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelDebug,
	}))

	addr := ":9000"
	if len(os.Args) > 1 {
		addr = os.Args[1]
	}

	srv, err := NewServer(addr, logger)
	if err != nil {
		logger.Error("failed to create server", "error", err)
		os.Exit(1)
	}
	defer srv.Close()

	// Graceful shutdown via OS signals
	ctx, cancel := signal.NotifyContext(context.Background(),
		syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	if err := srv.Run(ctx); err != nil {
		logger.Error("server error", "error", err)
		os.Exit(1)
	}

	logger.Info("server shutdown complete")
}
```

### UDP Client — Go

```go
// udp_client.go — Production-grade UDP client in Go
//
// Usage: go run udp_client.go localhost:9000 "Hello, World!"

package main

import (
	"errors"
	"fmt"
	"net"
	"os"
	"time"
)

const (
	clientReadTimeout = 3 * time.Second
	maxResponseSize   = 65507
)

// UDPClient sends a datagram and waits for a response.
func UDPClient(serverAddr, message string) error {
	// Resolve server address
	raddr, err := net.ResolveUDPAddr("udp", serverAddr)
	if err != nil {
		return fmt.Errorf("resolve %q: %w", serverAddr, err)
	}

	// DialUDP with nil local address lets OS pick ephemeral port.
	// This creates a "connected" UDP socket — only receives datagrams
	// from the specific raddr. Simpler than unconnected for client use.
	conn, err := net.DialUDP("udp", nil, raddr)
	if err != nil {
		return fmt.Errorf("dial UDP: %w", err)
	}
	defer conn.Close()

	// Send the message
	payload := []byte(message)
	n, err := conn.Write(payload) // Write() works on DialUDP (connected) sockets
	if err != nil {
		return fmt.Errorf("send: %w", err)
	}
	fmt.Printf("Sent %d bytes to %s\n", n, raddr)

	// Wait for echo response
	if err := conn.SetReadDeadline(time.Now().Add(clientReadTimeout)); err != nil {
		return fmt.Errorf("set deadline: %w", err)
	}

	buf := make([]byte, maxResponseSize)
	n, err = conn.Read(buf) // Read() on connected socket
	if err != nil {
		var netErr net.Error
		if errors.As(err, &netErr) && netErr.Timeout() {
			return fmt.Errorf("timeout: no response within %s", clientReadTimeout)
		}
		return fmt.Errorf("receive: %w", err)
	}

	fmt.Printf("Received %d bytes: %q\n", n, buf[:n])
	return nil
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: %s <host:port> <message>\n", os.Args[0])
		os.Exit(1)
	}

	if err := UDPClient(os.Args[1], os.Args[2]); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

---

## 13. UDP Socket Programming — Rust

### Rust's std::net — Key Types

| Type                | Purpose                                           |
|---------------------|---------------------------------------------------|
| `UdpSocket`         | The core UDP socket type                          |
| `SocketAddr`        | An IP:port address (IPv4 or IPv6)                 |
| `SocketAddrV4/V6`   | Version-specific address types                    |
| `IpAddr`            | An IP address without port                        |

Rust's `UdpSocket` uses a **blocking** model by default. For async, use `tokio::net::UdpSocket`.

### UDP Server — Rust (std, blocking)

```rust
//! udp_server.rs — Production-grade UDP echo server in Rust (std blocking)
//!
//! Demonstrates:
//!   - Proper error propagation with std::io::Error (no unwrap in logic)
//!   - Explicit buffer ownership and lifetime management
//!   - Graceful signal handling via ctrlc crate
//!   - Socket buffer tuning via socket2 crate pattern
//!
//! Cargo.toml dependencies:
//!   [dependencies]
//!   # None required for std-only; add ctrlc for signal handling
//!
//! Run: cargo run --bin udp_server -- 9000

use std::net::{SocketAddr, UdpSocket};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

/// Maximum size of a UDP datagram payload over IPv4.
const MAX_DATAGRAM_SIZE: usize = 65507;

/// Receive loop timeout. Allows periodic shutdown checks.
const READ_TIMEOUT: Duration = Duration::from_millis(500);

/// Entry point.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let port: u16 = std::env::args()
        .nth(1)
        .ok_or("Usage: udp_server <port>")?
        .parse()
        .map_err(|e| format!("Invalid port: {e}"))?;

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    run_server(addr)?;
    Ok(())
}

/// Core server loop.
fn run_server(bind_addr: SocketAddr) -> std::io::Result<()> {
    // Bind the UDP socket
    let socket = UdpSocket::bind(bind_addr)?;
    println!("UDP echo server listening on {}", socket.local_addr()?);

    // Set a read timeout so we can poll the shutdown flag
    socket.set_read_timeout(Some(READ_TIMEOUT))?;

    // Atomic flag for clean shutdown (set by Ctrl+C handler)
    let running = Arc::new(AtomicBool::new(true));
    let running_clone = Arc::clone(&running);

    // Register Ctrl+C handler
    ctrlc::set_handler(move || {
        println!("\nShutdown signal received.");
        running_clone.store(false, Ordering::SeqCst);
    })
    .expect("Error setting Ctrl+C handler");

    // Pre-allocate a reusable receive buffer on the stack.
    // Stack allocation is preferred here: MAX_DATAGRAM_SIZE (65507 bytes)
    // is within safe stack limits for most platforms.
    // However, for very large buffers, use Vec<u8> on the heap.
    let mut buf = vec![0u8; MAX_DATAGRAM_SIZE];

    while running.load(Ordering::Relaxed) {
        match socket.recv_from(&mut buf) {
            Ok((nbytes, peer_addr)) => {
                handle_datagram(&socket, &buf[..nbytes], peer_addr);
            }
            Err(ref e)
                if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut =>
            {
                // Timeout expired — loop back and check `running`
                continue;
            }
            Err(e) => {
                eprintln!("recv_from error: {e}");
                // Distinguish fatal vs transient errors
                return Err(e);
            }
        }
    }

    println!("Server stopped cleanly.");
    Ok(())
}

/// Process a single received datagram.
///
/// # Arguments
/// * `socket` — the bound UDP socket to echo back through
/// * `payload` — the received bytes (slice — no allocation)
/// * `peer`    — the sender's address
fn handle_datagram(socket: &UdpSocket, payload: &[u8], peer: SocketAddr) {
    println!(
        "Received {} bytes from {} | content: {:?}",
        payload.len(),
        peer,
        String::from_utf8_lossy(payload)
    );

    match socket.send_to(payload, peer) {
        Ok(sent) => {
            if sent != payload.len() {
                eprintln!(
                    "Partial send: sent {sent} of {} bytes to {peer}",
                    payload.len()
                );
            }
        }
        Err(e) => {
            // UDP send errors are typically non-fatal (ICMP unreachable, etc.)
            eprintln!("send_to {peer} failed: {e}");
        }
    }
}
```

### Async UDP Server — Rust (Tokio)

```rust
//! udp_server_async.rs — Production async UDP server using Tokio
//!
//! Cargo.toml:
//!   [dependencies]
//!   tokio = { version = "1", features = ["full"] }

use std::net::SocketAddr;
use std::sync::Arc;
use tokio::net::UdpSocket;
use tokio::signal;

const MAX_DATAGRAM_SIZE: usize = 65507;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let port: u16 = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "9000".to_string())
        .parse()?;

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let socket = UdpSocket::bind(addr).await?;

    println!("Async UDP server on {}", socket.local_addr()?);

    // Wrap in Arc so it can be shared across async tasks
    let socket = Arc::new(socket);

    tokio::select! {
        result = serve(Arc::clone(&socket)) => {
            if let Err(e) = result {
                eprintln!("Server error: {e}");
            }
        }
        _ = signal::ctrl_c() => {
            println!("Ctrl+C received, shutting down.");
        }
    }

    Ok(())
}

async fn serve(socket: Arc<UdpSocket>) -> std::io::Result<()> {
    let mut buf = vec![0u8; MAX_DATAGRAM_SIZE];

    loop {
        // recv_from is async — yields to Tokio runtime while waiting
        let (nbytes, peer) = socket.recv_from(&mut buf).await?;

        println!("Received {nbytes} bytes from {peer}");

        // Clone socket for the spawned task
        let socket = Arc::clone(&socket);
        let payload: Vec<u8> = buf[..nbytes].to_vec(); // clone payload

        // Spawn a task per datagram (cheap with Tokio's green threads)
        tokio::spawn(async move {
            if let Err(e) = socket.send_to(&payload, peer).await {
                eprintln!("send_to {peer}: {e}");
            }
        });
    }
}
```

### UDP Client — Rust

```rust
//! udp_client.rs — Production-grade UDP client in Rust
//!
//! Run: cargo run --bin udp_client -- 127.0.0.1:9000 "Hello"

use std::net::{SocketAddr, UdpSocket};
use std::time::Duration;

const READ_TIMEOUT: Duration = Duration::from_secs(3);
const MAX_RESPONSE: usize = 65507;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let server: SocketAddr = std::env::args()
        .nth(1)
        .ok_or("Usage: udp_client <server:port> <message>")?
        .parse()?;

    let message = std::env::args()
        .nth(2)
        .ok_or("Provide a message")?;

    send_and_receive(server, message.as_bytes())?;
    Ok(())
}

fn send_and_receive(server: SocketAddr, payload: &[u8]) -> std::io::Result<()> {
    // Bind to 0.0.0.0:0 — OS assigns an ephemeral port
    let socket = UdpSocket::bind("0.0.0.0:0")?;
    println!("Client bound to {}", socket.local_addr()?);

    // Connect — restricts send/recv to server address.
    // After connect(), use send()/recv() instead of send_to()/recv_from().
    // The kernel will also FILTER incoming datagrams — only from server.
    socket.connect(server)?;
    socket.set_read_timeout(Some(READ_TIMEOUT))?;

    // Send payload
    let sent = socket.send(payload)?;
    println!("Sent {sent} bytes to {server}");

    // Receive echo
    let mut buf = vec![0u8; MAX_RESPONSE];
    match socket.recv(&mut buf) {
        Ok(nbytes) => {
            println!(
                "Received {nbytes} bytes: {:?}",
                String::from_utf8_lossy(&buf[..nbytes])
            );
        }
        Err(e) if e.kind() == std::io::ErrorKind::WouldBlock
               || e.kind() == std::io::ErrorKind::TimedOut => {
            eprintln!("Timeout: no response from {server} within {:?}", READ_TIMEOUT);
            return Err(e);
        }
        Err(e) => return Err(e),
    }

    Ok(())
}
```

---

## 14. Broadcast UDP

### What is Broadcast?

**Broadcast** means sending a single UDP datagram that is **received by all hosts** on a network segment. Unlike unicast (one-to-one), broadcast is one-to-all.

### Broadcast Address Types

```
Type                    Address             Scope
──────────────────────  ──────────────────  ──────────────────────────
Limited broadcast       255.255.255.255     Current subnet only
                                            (never forwarded by routers)

Directed broadcast      Network broadcast   Specific network
                        (e.g. 192.168.1.255 for 192.168.1.0/24)
                                            (can be routed, often disabled)

Subnet broadcast        Subnet's last addr  Specific subnet
```

### Broadcast Packet Flow

```
Sender: 192.168.1.10
Sends to: 192.168.1.255 (subnet broadcast)

                    Network Switch
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
 192.168.1.20    192.168.1.30    192.168.1.40
 (receives)      (receives)      (receives)

Router (192.168.1.1): discards broadcast — does NOT forward to other subnets
```

### Why Routers Don't Forward Broadcasts

By default, routers **drop directed broadcast packets** (RFC 2644). This prevents **broadcast storms** from propagating across the entire Internet. Broadcasts are strictly limited to the local link.

### Broadcast Socket Options

To send a broadcast, you must explicitly enable it with `SO_BROADCAST`:

```c
// C: Enable broadcast
int enable = 1;
setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &enable, sizeof(enable));

// Then send to broadcast address
sendto(sockfd, data, len, 0, broadcast_addr, addrlen);
```

```go
// Go: No special option needed for send — but receiver must bind correctly
// Sender sends to "255.255.255.255:port" or "192.168.x.255:port"
conn.WriteToUDP(data, broadcastAddr)
```

```rust
// Rust: Use socket2 crate for SO_BROADCAST
use socket2::{Socket, Domain, Type, Protocol};
let socket = Socket::new(Domain::IPV4, Type::DGRAM, Some(Protocol::UDP))?;
socket.set_broadcast(true)?;
```

### Broadcast Use Cases

- **DHCP**: Client broadcasts on 255.255.255.255:67 to find any DHCP server
- **ARP**: Resolves IP → MAC addresses (but at Ethernet layer)
- **mDNS**: Multicast DNS for local service discovery
- **SSDP**: Simple Service Discovery Protocol (UPnP)
- **NetBIOS**: Windows name resolution (legacy)

---

## 15. Multicast UDP

### What is Multicast?

**Multicast** allows a single sender to efficiently send to a **group of interested receivers** across routers. Unlike broadcast (all hosts receive), multicast uses a subscription model:
- Receivers **join a multicast group**
- Only joined receivers receive the traffic
- Routers can replicate packets only where needed

### Multicast Address Space (IPv4)

```
224.0.0.0/4  (224.0.0.0 – 239.255.255.255)

Subdivided as:
  224.0.0.0/24     Link-local (not routed): OSPF, RIP, mDNS
  224.0.1.0/24     Internetwork control
  232.0.0.0/8      Source-specific multicast (SSM)
  233.0.0.0/8      GLOP addressing
  239.0.0.0/8      Organization-local scope (private multicast)

Common well-known addresses:
  224.0.0.1    All hosts on subnet
  224.0.0.2    All routers on subnet
  224.0.0.9    RIP version 2
  224.0.0.251  mDNS (Bonjour/Avahi)
  239.255.255.250  SSDP (UPnP)
```

### IGMP — The Subscription Protocol

**IGMP (Internet Group Management Protocol)** is how hosts tell their local router which multicast groups they want to join. This enables routers to efficiently route multicast traffic.

```
Host                          Router
  │                              │
  │── IGMP Join (224.0.0.251) ──►│  "I want multicast group 224.0.0.251"
  │                              │
  │        [Multicast traffic flows to this router]
  │                              │
  │◄── Multicast data ───────────│  Router delivers to subscribed hosts
  │                              │
  │── IGMP Leave ───────────────►│  "I no longer want this group"
```

### Multicast Socket Options (C)

```c
/* Join a multicast group */
struct ip_mreq mreq = {
    .imr_multiaddr.s_addr = inet_addr("239.255.255.250"),  /* group address */
    .imr_interface.s_addr = INADDR_ANY,                    /* any interface */
};
setsockopt(sockfd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq));

/* Leave a multicast group */
setsockopt(sockfd, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq, sizeof(mreq));

/* Set TTL for outgoing multicast (controls hop count) */
int ttl = 32;  /* number of hops before packet is discarded */
setsockopt(sockfd, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof(ttl));

/* Disable loopback (don't receive your own multicast on same host) */
int loop = 0;
setsockopt(sockfd, IPPROTO_IP, IP_MULTICAST_LOOP, &loop, sizeof(loop));
```

### Multicast vs Unicast vs Broadcast Efficiency

```
Sending video to 1000 subscribers on different networks:

UNICAST (1000 separate streams):
 Server ──[copy 1]──► Router ──► Subscriber 1
 Server ──[copy 2]──► Router ──► Subscriber 2
 ...
 Server sends 1000 copies. Network traffic: N × stream_bandwidth.

BROADCAST (limited to LAN):
 Only works within a subnet. Cannot cross routers.

MULTICAST (1 stream, replicated only where needed):
 Server ──[1 copy]──► Router ──[2 copies]──► Router A ──► Subs on A
                              └──[1 copy]──► Router B ──► Subs on B
 Server sends 1 copy. Network traffic: proportional to topology.
```

Multicast is essential for **IPTV**, **live streaming infrastructure**, and **financial market data feeds**.

---

## 16. UDP Buffer Management and Kernel Internals

### What Happens Inside the Kernel When UDP Packet Arrives

```
NIC (Network Interface Card)
  │
  │ DMA transfer to ring buffer (sk_buff allocated)
  ▼
Interrupt Handler / NAPI poll
  │
  │ Ethernet frame validation
  ▼
Network Stack (softirq context)
  │
  │ Strip Ethernet header → pass to IP
  ▼
ip_rcv() — IPv4 receive
  │
  │ IP header validation
  │ Routing decision
  │ Defragmentation (if fragmented)
  ▼
udp_rcv() — UDP receive handler
  │
  │ Port lookup: find socket with matching 4-tuple
  │ Checksum verification
  │
  ├── Socket found → enqueue to socket receive buffer
  │      └── sk_buff added to sk->sk_receive_queue
  │
  └── No socket → send ICMP Port Unreachable
           └── type=3 (Destination Unreachable), code=3 (Port Unreachable)

Application (user space)
  │
  │ recvfrom() system call
  │ → copy sk_buff payload to user buffer
  │ → free sk_buff
  ▼
Returns data to application
```

### Socket Receive Buffer — The Critical Queue

Each UDP socket has a **receive buffer** in the kernel. When datagrams arrive faster than the application reads them, they queue here. If the queue fills up:

```
Receive Buffer (default: 208 KB on Linux):
┌──────────────────────────────────────┐
│ Datagram 1 │ Datagram 2 │ Datagram 3 │ ← Waiting to be read
└──────────────────────────────────────┘
                                         ← Buffer full!
       New Datagram Arrives → DROPPED SILENTLY
```

**Critically: UDP drop is silent.** The kernel simply discards the datagram with no notification. This is in contrast to TCP which would slow down the sender via flow control.

### Tuning Kernel Buffers (Linux)

```bash
# View current UDP buffer settings
sysctl net.core.rmem_default   # Default receive buffer size
sysctl net.core.rmem_max       # Maximum receive buffer size
sysctl net.core.wmem_default   # Default send buffer size
sysctl net.core.wmem_max       # Maximum send buffer size

# Increase for high-throughput UDP (e.g. video streaming server)
sysctl -w net.core.rmem_max=26214400     # 25 MB max receive
sysctl -w net.core.wmem_max=26214400     # 25 MB max send
sysctl -w net.core.rmem_default=4194304  # 4 MB default receive

# UDP-specific statistics
cat /proc/net/snmp | grep Udp
# Shows: InDatagrams, NoPorts, InErrors, OutDatagrams, RcvbufErrors, SndbufErrors
# RcvbufErrors: datagrams dropped due to full receive buffer
```

### Monitoring UDP Drops

```bash
# Watch for UDP receive errors (drops due to buffer overflow)
watch -n 1 'netstat -su | grep -A5 "Udp:"'

# Or with ss (socket statistics)
ss -u -n -p

# With detailed stats
cat /proc/net/udp
```

### sk_buff — The Kernel's Packet Structure

Every packet in the Linux kernel is represented by a `struct sk_buff`. Understanding this is crucial for system-level thinking:

```
struct sk_buff {
    /* Linked list pointers (for queue management) */
    struct sk_buff *next, *prev;

    /* Packet metadata */
    struct sock     *sk;       /* owning socket */
    unsigned int     len;      /* payload length */
    unsigned int     data_len; /* length of paged data */
    __u16            protocol; /* packet protocol (ETH_P_IP, etc.) */

    /* Data pointers — all point into a contiguous memory region */
    unsigned char   *head;     /* start of allocated buffer */
    unsigned char   *data;     /* start of current data (moves as headers are stripped) */
    unsigned char   *tail;     /* end of data */
    unsigned char   *end;      /* end of allocated buffer */

    /* Timestamps, checksums, priority, etc. */
};
```

When the IP layer strips the IP header, it simply advances `data` by 20 bytes — **no copying required**. This is why the Linux network stack is so efficient.

---

## 17. Performance Characteristics and Cache Behavior

### Why UDP is Faster Than TCP — Systems Analysis

**1. No connection state → less memory → better cache locality**

TCP maintains significant per-connection state:
```
TCP per-connection state (simplified):
- Send/receive sequence numbers (8 bytes)
- Send/receive windows (8 bytes)
- Congestion window, slow-start threshold (8 bytes)
- Retransmission timer, RTT estimates (16 bytes)
- Out-of-order packet queue (variable)
Total: easily 20KB+ per connection in kernel

UDP per-socket state:
- Source/destination address (16 bytes)
- Buffer pointers (16 bytes)
Total: ~64 bytes
```

With thousands of concurrent connections, TCP state overflows CPU caches. UDP's minimal state fits in L2 cache.

**2. Zero copy potential with recvmmsg/sendmmsg**

Linux provides `recvmmsg()` and `sendmmsg()` — system calls that receive/send **multiple UDP datagrams in a single syscall**:

```c
/* Send 10 UDP datagrams in 1 system call instead of 10 */
struct mmsghdr msgs[10];
/* ... fill msgs ... */
int sent = sendmmsg(sockfd, msgs, 10, 0);
/* Reduces syscall overhead by ~10x */
```

**3. No ACK overhead — unidirectional traffic is pure throughput**

For one-way data (video streaming, telemetry), UDP eliminates:
- ACK packets (≈50% of TCP packet count in bulk transfer)
- ACK timing delays
- Head-of-line blocking (lost packet stalls entire stream in TCP)

**4. No Nagle's Algorithm**

TCP has **Nagle's Algorithm** which delays small sends to coalesce them (to avoid sending many tiny packets). This adds up to 40ms of latency. UDP sends immediately, always.

### CPU and Cache Behavior

```
UDP Receive Path — Cache Profile:
─────────────────────────────────
L1 Cache (< 1 ns access):
  - Socket file descriptor metadata
  - Recent sk_buff structures (ring buffer head)

L2 Cache (< 5 ns access):
  - UDP socket structure (64 bytes)
  - Packet headers (28 bytes: IP + UDP)

L3 Cache / RAM (< 100 ns):
  - Packet payload (varies, up to 65507 bytes)
  - Socket receive queue

Conclusion: Headers always hot (L1/L2), payload cold.
Implication: Small UDP datagrams (< 1500 bytes) are cache-friendly.
             Large UDP datagrams cause L3/RAM pressure.
```

### Memory Allocation Pattern

```
UDP Send Path (sendto system call):
─────────────────────────────────────────────────────
1. System call entry (ring crossing: user → kernel)
2. alloc_skb() — allocate sk_buff from slab allocator
   └── sk_buff pool is pre-warmed → L2 cache hit
3. Copy user payload to sk_buff (one copy)
4. Build IP/UDP headers (in-place, no alloc)
5. Send via NIC driver (DMA from sk_buff)
6. Interrupt on completion → free sk_buff

Allocation count per UDP send: 1 (just the sk_buff)
Allocation count per TCP send: 1 + potential retransmit clones
```

### Throughput Benchmarks (Reference, modern server)

```
Protocol    Throughput    CPU Usage    Latency (p99)
────────    ──────────    ─────────    ─────────────
Raw UDP     ~40 Gbps      ~30%         ~10 µs
TCP         ~25 Gbps      ~60%         ~100 µs
UDP+QUIC    ~20 Gbps      ~50%         ~20 µs

(Conditions: 10GbE NIC, kernel bypass off, single socket, localhost)
```

### NUMA (Non-Uniform Memory Access) Considerations

On multi-socket servers (NUMA systems), network performance depends critically on which CPU processes the network interrupt vs which CPU runs your application:

```
NUMA Node 0          NUMA Node 1
┌─────────────┐      ┌─────────────┐
│ CPU 0-7     │      │ CPU 8-15    │
│ RAM (local) │      │ RAM (local) │
│ NIC IRQ     │      │ Application │
└─────────────┘      └─────────────┘
        ↑                    ↑
        │    QPI/UPI link    │  (expensive cross-NUMA access)

Solution: Pin NIC IRQ affinity and application to same NUMA node.
```

---

## 18. Real-World Protocols Built on UDP

### DNS — Domain Name System (RFC 1035)

DNS is the Internet's phone book — it maps domain names to IP addresses. It uses UDP port 53 for queries (responses ≤ 512 bytes; modern DNS uses up to 4096 with EDNS0).

```
DNS Query over UDP:
─────────────────────────────────────────────────────────────
Client                              DNS Server (8.8.8.8:53)
  │                                       │
  │── UDP: "What is the IP of google.com?" ──►│
  │                                       │
  │◄── UDP: "google.com = 142.250.80.46" ─│
  │                                       │

Total round trips: 1 (no connection setup)
Typical latency: 1–20 ms
```

**DNS Message Format:**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Transaction ID       |           Flags               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Questions            |         Answer RRs            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Authority RRs           |       Additional RRs          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Questions (variable length)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Answers (variable length)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### DHCP — Dynamic Host Configuration Protocol (RFC 2131)

DHCP assigns IP addresses to devices. It uses UDP because at startup a device has **no IP address**, so it cannot establish a TCP connection. Broadcast is essential.

```
DHCP 4-Way Handshake (DORA):
────────────────────────────────────────────────────────────
Client (0.0.0.0)           DHCP Server (255.255.255.255:67)
     │                               │
     │──[DISCOVER: broadcast]────────►│  "I need an IP!"
     │                               │
     │◄──[OFFER: 192.168.1.100]──────│  "Use this IP"
     │                               │
     │──[REQUEST: 192.168.1.100]─────►│  "I'll take it"
     │                               │
     │◄──[ACK]───────────────────────│  "Confirmed. Yours for 24h"
     │                               │
  Client configures 192.168.1.100
```

### NTP — Network Time Protocol (RFC 5905)

NTP synchronizes clocks over UDP port 123. Time synchronization is latency-critical — a TCP connection setup overhead would introduce variance. NTP uses sophisticated algorithms to compensate for network delay.

```
NTP Timestamp Format (64-bit):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Seconds (32 bits)                         |
|            (seconds since Jan 1, 1900 UTC)                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Fraction (32 bits)                          |
|              (fraction of a second, resolution ~233 ps)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### RTP — Real-time Transport Protocol (RFC 3550)

RTP carries audio/video over UDP. It adds sequence numbers and timestamps **at the application layer** to handle out-of-order packets and jitter, without adding TCP's reliability overhead.

```
RTP Header Format:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V=2|P|X|  CC   |M|     PT      |       Sequence Number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Timestamp                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Synchronization Source (SSRC) identifier           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

V:  Version (2)
P:  Padding
X:  Extension header present
CC: CSRC count
M:  Marker bit (end of frame, etc.)
PT: Payload type (96-127 = dynamic, e.g. 96=H.264, 97=OPUS)
```

**Key insight:** RTP *can* handle dropped packets by interpolation (audio: comfort noise; video: frame repeat/freeze). A momentary gap in voice is barely noticeable; TCP's retransmission would cause a 100ms+ stutter.

### SNMP — Simple Network Management Protocol

SNMP uses UDP port 161 (queries) and 162 (traps). Network devices use SNMP to report metrics. The "fire-and-forget" nature of UDP traps is intentional — if the network is so broken that a trap can't get through, TCP wouldn't help either.

### QUIC — The Modern Successor

QUIC is Google's protocol (now an IETF standard, RFC 9000) that runs **on top of UDP** and implements its own reliability, ordering, encryption (TLS 1.3 built-in), and multiplexing. HTTP/3 runs on QUIC.

```
HTTP/3 Stack:          HTTP/2 Stack (comparison):
┌────────────┐         ┌────────────┐
│   HTTP/3   │         │   HTTP/2   │
├────────────┤         ├────────────┤
│    QUIC    │         │    TLS     │
│ (reliability│        ├────────────┤
│  TLS 1.3   │         │    TCP     │
│ mux/flow)  │         │            │
├────────────┤         ├────────────┤
│    UDP     │         │    TCP     │  (TCP already handles reliability)
├────────────┤         ├────────────┤
│     IP     │         │     IP     │
└────────────┘         └────────────┘

Key advantage: QUIC eliminates TCP head-of-line blocking
(in HTTP/2, a single lost TCP segment blocks ALL multiplexed streams)
```

---

## 19. UDP Security — Attacks and Mitigations

### UDP Flood (DDoS Attack)

**Attack:** Send massive volumes of UDP datagrams to a target's random ports, forcing the target to:
1. Process each datagram
2. Look up destination port
3. Find no application → generate ICMP Port Unreachable
4. Exhaust NIC bandwidth, CPU, and ICMP rate limits

```
Attack Pattern:
Botnet (millions of compromised machines)
  │  │  │  │  │
  ▼  ▼  ▼  ▼  ▼
[millions of UDP packets/sec] ──► Target Server
                                  (overwhelmed, legitimate traffic dropped)
```

**Mitigations:**
- Rate limiting (iptables, tc)
- BPF/XDP filtering (drop malicious packets in kernel before routing)
- Anycast routing with scrubbing centers
- Cloud DDoS protection (AWS Shield, Cloudflare)

### IP Spoofing with UDP

Because UDP is connectionless, attackers can forge the source IP address. TCP's 3-way handshake makes spoofing much harder (you need to see the SYN-ACK to complete the handshake).

```
Attacker (IP: 1.2.3.4)
Sends UDP packet with forged source: 5.6.7.8 ──► Server

Server processes packet, sees source = 5.6.7.8
Server's response goes to 5.6.7.8 (innocent victim)

This enables:
1. Amplification attacks (see below)
2. Anonymity in attacks
3. One-way communication channels
```

### UDP Amplification Attacks

**The most dangerous UDP attack vector.** The attacker exploits protocols where a small request produces a large response.

```
Amplification Attack (DNS example):
──────────────────────────────────────────────────────────
Attacker (IP: 1.2.3.4)
│
│ Sends 60-byte DNS query
│ Source IP spoofed as: VICTIM (9.9.9.9)
│
▼
Open DNS Resolver (8.8.8.8)
│
│ Sends 3000-byte DNS response
│ to: VICTIM (9.9.9.9)
│
▼
VICTIM (9.9.9.9) ← receives 3000 bytes it never asked for

Amplification factor: 3000/60 = 50x
Attacker sends 1 Gbps → Victim receives 50 Gbps
```

**Known amplification factors:**
```
Protocol    Port    Max Amplification
────────    ────    ─────────────────
DNS         53      28–54×
NTP         123     556×
SSDP        1900    30×
Memcached   11211   50,000×
SNMP        161     650×
```

**Mitigations for service operators:**
- Never run open resolvers (DNS accessible from the Internet)
- BCP38: Ingress filtering — ISPs should drop spoofed source addresses
- Response Rate Limiting (RRL) in DNS servers
- Disable unused UDP services

### ICMP Port Unreachable — Information Leakage

When no application listens on a UDP port, the kernel sends **ICMP Type 3, Code 3 (Port Unreachable)** back to the sender. This can be used for:
- **Port scanning:** Send UDP packets to all 65535 ports; no response = port open, ICMP = port closed
- **OS fingerprinting:** Different OSes have different ICMP rate limiting behaviors

**Mitigation:** `iptables -A OUTPUT -p icmp --icmp-type port-unreach -j DROP` (use carefully — breaks legitimate PMTUD)

---

## 20. Modern UDP Evolution — QUIC, DTLS, WebRTC

### DTLS — Datagram TLS (RFC 6347)

TLS was designed for streams (TCP). **DTLS** adapts TLS for datagrams. It handles:
- Out-of-order handshake messages
- Packet loss during handshake (retransmit timers)
- Anti-replay protection (sliding window of sequence numbers)

```
DTLS Handshake (simplified):
─────────────────────────────────────────────────────────────
Client                               Server
  │                                     │
  │──[ClientHello] ─────────────────────►│
  │◄──[HelloVerifyRequest + Cookie]──────│  (prevents DoS)
  │──[ClientHello + Cookie]─────────────►│
  │◄──[ServerHello, Certificate, Done]───│
  │──[ClientKeyExchange, Finished]───────►│
  │◄──[Finished]────────────────────────│
  │                                     │
  │◄═══[Encrypted UDP datagrams]════════►│
```

The **cookie** in the handshake prevents reflection attacks — the server won't allocate state until the client proves it can receive (validating its source IP).

### QUIC — Complete Architecture

```
QUIC Connection Establishment:
─────────────────────────────────────────────────────────────
TCP + TLS 1.3:
  Client                     Server
    │── SYN ─────────────────►│   } 1 RTT
    │◄── SYN-ACK ─────────────│   }
    │── ACK + ClientHello ────►│   } 2 RTT total
    │◄── ServerHello + Cert ──│   }
    │── Finished ─────────────►│   }
    │◄── Finished ─────────────│
    │══ Application Data ══════│  (data starts)

QUIC (first connection):
  Client                     Server
    │── Initial (ClientHello)─►│  } 1 RTT
    │◄── Initial + Handshake──│  }
    │── Handshake + 1-RTT ────►│
    │◄═══[Application Data]════│  (data starts in 1 RTT)

QUIC (0-RTT resumption):
  Client                     Server
    │── 0-RTT data ────────────►│  (immediate, using cached session)
    │◄═══[Application Data]════│  (0 RTT for resumed connections!)
```

**QUIC Stream Multiplexing vs TCP:**
```
HTTP/2 over TCP (head-of-line blocking):
Stream 1: [seg1][seg2][ LOST ][seg4]  ← seg4 cannot be delivered until seg3 arrives
Stream 2: [seg1][seg2][seg3]          ← ALSO BLOCKED, even though complete
Stream 3: [seg1][seg2][seg3]          ← ALSO BLOCKED

HTTP/3 over QUIC (no head-of-line blocking):
Stream 1: [pkt1][pkt2][ LOST ][pkt4]  ← gap, retransmit pkt3 only
Stream 2: [pkt1][pkt2][pkt3]          ← delivered IMMEDIATELY despite Stream 1 loss
Stream 3: [pkt1][pkt2][pkt3]          ← delivered IMMEDIATELY
```

### WebRTC — Real-Time Browser Communication

WebRTC uses a stack of protocols, all ultimately over UDP:

```
WebRTC Protocol Stack:
─────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────┐
│  Application (Video call, Screen share, Game, etc.)        │
├──────────────────┬─────────────────────────────────────────┤
│  MediaStream API │  DataChannel API                        │
├──────────────────┤─────────────────────────────────────────┤
│  RTP/RTCP        │  SCTP (over DTLS)                      │
│  (media)         │  (reliable data)                        │
├──────────────────┴─────────────────────────────────────────┤
│  SRTP / DTLS (encryption)                                  │
├────────────────────────────────────────────────────────────┤
│  ICE / STUN / TURN (NAT traversal)                         │
├────────────────────────────────────────────────────────────┤
│  UDP                                                        │
├────────────────────────────────────────────────────────────┤
│  IP                                                         │
└────────────────────────────────────────────────────────────┘
```

**ICE/STUN/TURN — NAT Traversal:**

UDP faces challenges with NAT (Network Address Translation). Most devices are behind NAT routers that don't know how to route incoming UDP to the right device.

```
NAT Traversal Problem:
─────────────────────────────────────────────────────────────
Client A (192.168.1.10) behind NAT
Client B (10.0.0.5) behind different NAT
Both want to communicate directly.

Solution — ICE (Interactive Connectivity Establishment):
1. Both clients contact a STUN server (on public Internet)
2. STUN tells each client their public IP:port (as seen from outside NAT)
3. Clients exchange this info (via signaling server)
4. Clients simultaneously send UDP to each other's public address
5. NAT maps the outgoing packet and allows the incoming response

STUN exchange:
Client A ──[STUN Binding Request]──► STUN Server
Client A ◄──[Your public address: 203.0.113.10:54321]── STUN Server

If STUN fails (symmetric NAT), TURN (relay) is used as fallback.
```

---

## 21. Expert Mental Models and Problem-Solving Patterns

### Mental Model 1: The Reliability Spectrum

When designing a system, think of reliability as a spectrum:

```
No reliability                           Full reliability
     │                                         │
     ▼                                         ▼
[Raw UDP] → [UDP+Seq] → [UDP+Seq+ACK] → [UDP+Seq+ACK+Flow] → [TCP]
             (detect    (detect &        (detect, recover,
              loss)      recover)         & throttle)

Ask yourself: "Which point on this spectrum do I need?"
- Video conferencing: Left (loss tolerable, latency critical)
- File transfer:      Right (every bit must arrive)
- Online gaming:      Left-center (sequence numbers, but skip old data)
- Financial orders:   Right (reliability mandatory)
```

### Mental Model 2: UDP as a Primitive

UDP is a **building block**, not a complete solution. Expert designers use UDP as the foundation and add only the reliability primitives they need:

```
Problem: "I need reliable UDP but with lower latency than TCP"
Solution: Build selective reliability:

  Application layer adds:
  ┌─────────────────────────────────────────────┐
  │  Sequence number (detect loss, reordering)  │
  │  ACK bitmap (acknowledge multiple at once)  │
  │  Selective retransmit (only lost packets)   │
  │  No blocking (reader skips to newest data)  │
  └─────────────────────────────────────────────┘
  
  This is exactly what QUIC, Enet, KCP, RakNet implement.
  They implement reliability on TOP of UDP without TCP's HoL blocking.
```

### Mental Model 3: The Zero-Copy Pipeline

For maximum UDP performance, eliminate every unnecessary memory copy:

```
Naive path (4 copies):
  App buffer → kernel → NIC buffer → network → NIC buffer → kernel → App buffer

Optimized path (1 copy or 0 with DPDK):
  App buffer → NIC DMA → network (sendmsg with zerocopy flag, Linux 4.14+)
  
Code: setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));
      sendmsg(fd, &msg, MSG_ZEROCOPY);
      // Poll for completion via io_uring or SO_EE_ORIGIN_ZEROCOPY
```

### Mental Model 4: Failure Mode Thinking

**Expert question:** "What happens when this UDP packet is lost?"

```
For each UDP message you design, ask:
┌─────────────────────────────────────────────────────────┐
│ 1. Is loss detectable?     → Add sequence numbers       │
│ 2. Is loss recoverable?    → Add ACK + retransmit       │
│ 3. Is loss acceptable?     → Handle stale/missing state │
│ 4. Is loss catastrophic?   → Use TCP instead            │
│ 5. Is loss frequent?       → Fix your network first     │
└─────────────────────────────────────────────────────────┘
```

### Mental Model 5: The Datagram Contract

**UDP gives you one promise and one promise only:**

> "If the datagram arrives at the destination, its content is either intact (checksum passes) or discarded (checksum fails). There are no partial datagrams."

Everything else — delivery, order, speed, deduplication — is **your problem**. This mental model prevents the common mistake of assuming "UDP might partially deliver a message."

### Common Expert Patterns

#### Pattern 1: Sequence Number + Ring Buffer (Game Networking)

```
Sender adds sequence number to each packet.
Receiver maintains a ring buffer of received sequence numbers.
Receiver processes only the latest sequence (or within a window).
Old/duplicate packets are ignored.

Effect: No head-of-line blocking. Stale data is discarded, not buffered.
```

#### Pattern 2: Negative ACK (NACK)

```
Instead of ACKing every packet (expensive), receiver only sends NACK
when it detects a gap in sequence numbers.

Receiver: seq 1,2,3, [5] received → send NACK(4)
Sender:   retransmits only packet 4

Benefit: Dramatically reduces ACK overhead for low-loss networks.
Used by: MPEG DASH, video conferencing, custom game protocols.
```

#### Pattern 3: Forward Error Correction (FEC)

```
Send redundant data that allows reconstruction without retransmission.

Example (Reed-Solomon):
  Send packets: [P1][P2][P3][FEC1][FEC2]
  Any 3 of the 5 packets can reconstruct all data.

If P2 is lost:
  Receive [P1][P3][FEC1][FEC2] → reconstruct P2 mathematically.
  
No retransmission needed! Zero added latency.
Cost: 40% bandwidth overhead (2 FEC for 3 data packets).
```

#### Pattern 4: Jitter Buffer (Audio/Video)

```
Network delay varies (jitter). A jitter buffer smooths this:

Received:  [P1 at t=0ms][P3 at t=5ms][P2 at t=12ms]  ← out of order
Buffer:    Wait until t=30ms, reorder → [P1][P2][P3]
Playback:  Smooth, ordered, 30ms delayed

The 30ms delay is the price for smooth playback.
Adaptive jitter buffers adjust this delay in real-time based on network conditions.
```

### Cognitive Framework: How Experts Diagnose UDP Issues

When a UDP-based system misbehaves, experts ask:

```
Step 1: Is data being sent?
  └── tcpdump/Wireshark: see the packets leaving the sender?

Step 2: Are packets arriving at destination?
  └── tcpdump on receiver: packets arriving?

Step 3: Are packets being consumed by the application?
  └── /proc/net/udp, ss -un: is buffer filling up?
  └── netstat -su: RcvbufErrors increasing?

Step 4: What is the loss rate?
  └── Application sequence numbers → calculate loss %
  └── Typical acceptable loss: <1% voice, <5% video

Step 5: What is the latency distribution?
  └── Use timestamps in packets, compute RTT
  └── p50, p95, p99 — tail latency is what hurts users

Step 6: Is the checksum causing drops?
  └── Checksum failures logged in /proc/net/snmp
```

---

## Appendix A: Complete UDP RFC 768 Reference

```
User Datagram Protocol (RFC 768)
Jon Postel, ISI, 28 August 1980

Format:
                  0      7 8     15 16    23 24    31
                 +--------+--------+--------+--------+
                 |     Source      |   Destination   |
                 |      Port       |      Port       |
                 +--------+--------+--------+--------+
                 |                 |                 |
                 |     Length      |    Checksum     |
                 +--------+--------+--------+--------+
                 |
                 |          data octets ...
                 +---------------- ...

Fields:
  Source Port is an optional field, when meaningful, it indicates
  the port of the sending process, and may be assumed to be the
  port to which a reply should be addressed in the absence of any
  other information. If not used, a value of zero is inserted.

  Destination Port has a meaning within the context of a particular
  internet destination address.

  Length is the length in octets of this user datagram including
  this header and the data. (This means the minimum value of the
  length is eight.)

  Checksum is the 16-bit ones's complement of the ones's complement
  sum of a pseudo header of information from the IP header, the UDP
  header, and the data, padded with zero octets at the end (if
  necessary) to make a multiple of two octets.

  The pseudo  header  conceptually prefixed to the UDP header
  contains the source address, the destination address, the
  protocol, and the UDP length. This information gives protection
  against misrouted datagrams.

                  0      7 8     15 16    23 24    31
                 +--------+--------+--------+--------+
                 |          source address           |
                 +--------+--------+--------+--------+
                 |        destination address        |
                 +--------+--------+--------+--------+
                 |  zero  |protocol|   UDP length    |
                 +--------+--------+--------+--------+

  If the computed checksum is zero, it is transmitted as all ones
  (the equivalent in one's complement arithmetic). An all zero
  transmitted checksum value means that the transmitter generated
  no checksum (for debugging or for higher level protocols that
  don't care).
```

---

## Appendix B: Quick Reference — System Calls

```
POSIX UDP Socket System Calls:
────────────────────────────────────────────────────────────────────────
socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)  → sockfd
  Creates a UDP socket.

bind(sockfd, &addr, addrlen)
  Assigns local IP:port. Servers must bind; clients optional.
  Without bind(), OS assigns ephemeral port on first sendto().

sendto(sockfd, buf, len, flags, &dest_addr, addrlen)
  Sends a datagram. Returns bytes sent or -1 on error.
  UDP sends are atomic: all or nothing, never partial.

recvfrom(sockfd, buf, len, flags, &src_addr, &addrlen)
  Receives one complete datagram. Returns bytes received.
  If buf is too small, excess bytes are DISCARDED (truncated).
  src_addr is filled with the sender's address.

connect(sockfd, &addr, addrlen) [optional for UDP]
  "Connects" UDP socket to a specific remote address.
  Enables send()/recv() instead of sendto()/recvfrom().
  Filters incoming datagrams to only from connected address.
  Does NOT establish a real connection — no packets sent.

setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size))
  Set kernel receive buffer size.

setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &enable, sizeof(enable))
  Enable sending broadcast datagrams.

setsockopt(sockfd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq))
  Join a multicast group.

getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &err, &errlen)
  Retrieve pending error on connected UDP socket.
  Important: sendto() errors on unconnected sockets may be async.

close(sockfd)
  Release the socket and all associated resources.
```

---

## Appendix C: Wireshark / tcpdump Filter Reference

```bash
# Capture all UDP traffic
tcpdump -i eth0 udp

# Capture UDP on specific port
tcpdump -i eth0 udp port 53

# Capture UDP between two hosts
tcpdump -i eth0 udp host 192.168.1.10 and host 8.8.8.8

# Show packet contents in hex + ASCII
tcpdump -i eth0 -X udp port 9000

# Save to file for Wireshark analysis
tcpdump -i eth0 -w capture.pcap udp

# Wireshark display filter for UDP
# In filter bar: udp
#                udp.port == 53
#                udp.length > 100
#                ip.src == 192.168.1.10 && udp
```

---

*End of UDP Protocol — Complete Guide*
*Coverage: RFC 768, Real Protocol Structures, C/Go/Rust implementation,*
*Kernel internals, Performance analysis, Security, Modern Evolution (QUIC/DTLS/WebRTC)*

Now I'll create the comprehensive UDP guide as a markdown file.Here is your complete UDP guide — 21 sections of deep, systems-level coverage. Here is exactly what is inside:

**Sections 1–5 — Foundation**
Builds your mental model from first principles: what a protocol, packet, port, and socket *actually are*, where UDP sits in both the OSI and real TCP/IP stack, and the full packet journey from application bytes to electrical signals on the wire — with byte-offset accounting.

**Section 6 — Real Protocol Structure**
The actual RFC 768 ASCII wire diagram with bit-position numbering, every field explained at the bit level, including why Source Port is optional, the exact maximum payload formulas for IPv4 and IPv6, and a real DNS query shown byte-by-byte.

**Section 7 — Checksum Deep Dive**
One's complement arithmetic explained from scratch, the pseudo-header concept and *why* it exists (it catches wrong-destination delivery, which the UDP header alone cannot), and a fully working, production-quality C implementation of the checksum algorithm.

**Section 8 — UDP vs TCP**
The full TCP state machine vs UDP's trivial two-state existence, and the critical **message boundary distinction** — the most important practical difference that trips up almost every beginner.

**Sections 9–10 — IP Fragmentation and Addressing**
How fragmentation works internally with fragment offset arithmetic, why losing one fragment loses the whole datagram, Path MTU Discovery, and safe payload size guidelines for real networks.

**Sections 11–13 — Production Code (C, Go, Rust)**
Not toy examples. Signal-safe shutdown, kernel buffer tuning, `recvmmsg`, async Tokio server, proper error propagation, ownership discipline, and zero `unwrap()` without justification.

**Sections 14–15 — Broadcast and Multicast**
The DORA DHCP flow, IGMP subscription protocol, multicast address space breakdown, and the efficiency argument for multicast over unicast at scale.

**Sections 16–17 — Kernel Internals and Performance**
The full `sk_buff` journey through the Linux network stack, why silent buffer drops happen, NUMA considerations for server design, and the quantitative throughput/latency comparison between UDP, TCP, and QUIC.

**Section 18 — Real Protocols Built on UDP**
DNS, DHCP, NTP (with the 64-bit timestamp format), RTP (with header wire diagram), SNMP, and QUIC — each with their wire format and the *reason* UDP was chosen over TCP.

**Section 19 — Security**
UDP flood, IP spoofing mechanics, amplification attack math (Memcached at 50,000×), and ICMP port scanning — all with concrete mitigations.

**Section 20 — Modern Evolution**
DTLS handshake with the DoS-preventing cookie, QUIC's 0-RTT resumption, head-of-line blocking elimination diagram, and the full WebRTC protocol stack down to ICE/STUN/TURN NAT traversal.

**Section 21 — Expert Mental Models**
The reliability spectrum, failure mode thinking framework, FEC/NACK/jitter buffer patterns, and the diagnostic decision tree experts use to debug UDP systems in production.