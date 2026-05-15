# Network Protocol Connection Management: A Complete In-Depth Guide
## From Raw Packets to Linux Kernel Internals — C & Rust

---

> **Mental Model Goal**: By the end of this guide, you will be able to trace a single TCP connection from the first SYN bit through Linux kernel data structures, across protocol layers, through state machines, all the way to connection teardown — and implement/observe it in C and Rust.

---

## Table of Contents

1. [Foundational Concepts — Before Everything Else](#1-foundational-concepts)
2. [The Network Stack — OSI and TCP/IP Models](#2-the-network-stack)
3. [What Is a "Connection" — Defining the Concept](#3-what-is-a-connection)
4. [Protocol Flags — What They Are and How They Are Tracked](#4-protocol-flags)
5. [Connection Initialization — Layer by Layer](#5-connection-initialization)
6. [How Connections Are Remembered — State Storage](#6-how-connections-are-remembered)
7. [Cross-Layer Protocol Coordination](#7-cross-layer-protocol-coordination)
8. [Connection Lifetime Management](#8-connection-lifetime-management)
9. [Connection Termination — Who, How, When](#9-connection-termination)
10. [Session Handling — Who Owns the Session](#10-session-handling)
11. [Linux Kernel Network Stack Deep Dive](#11-linux-kernel-network-stack)
12. [C Implementations — Real Code](#12-c-implementations)
13. [Rust Integration — Safe Networking Over C Primitives](#13-rust-integration)
14. [Mental Models and Pattern Recognition](#14-mental-models)

---

## 1. Foundational Concepts

Before we talk about connections, you must internalize these primitives. Every term below is used throughout the entire guide.

### 1.1 What Is a Protocol?

A **protocol** is a set of formal rules that two or more parties agree to follow so they can communicate. A protocol defines:

- **Message format** — how bytes are arranged (header + payload)
- **Sequence of messages** — who sends what, in what order
- **State** — what each party must remember between messages
- **Error handling** — what to do when something goes wrong
- **Termination** — how the conversation ends

### 1.2 What Is a Socket?

A **socket** is an abstraction provided by the OS that represents one endpoint of a communication channel. Think of it as a "door" into the network.

```
Application
    |
    |  write(fd, data, len)
    v
[Socket FD] --------> [Kernel Socket Buffer] --------> [Network]
    ^
    |  read(fd, buf, len)
    |
Application
```

A socket is identified by a **5-tuple**:

```
{ Protocol, Source IP, Source Port, Destination IP, Destination Port }
```

This 5-tuple is THE KEY used to look up a connection in every kernel hash table.

### 1.3 What Is a Port?

A **port** is a 16-bit number (0–65535) that identifies a specific process/service on a machine. IP routes packets to a machine. Ports route packets to a process.

```
IP Address  = Street Address of a Building
Port        = Apartment Number inside the Building
```

- **Well-known ports**: 0–1023 (HTTP=80, HTTPS=443, SSH=22)
- **Registered ports**: 1024–49151
- **Ephemeral ports**: 49152–65535 (used by clients for source port)

### 1.4 What Is a Flag in a Protocol?

A **flag** is a single bit (or small field) inside a protocol header that signals a specific condition or action.

```
TCP Header Flags (6 bits in classic TCP, 9 in modern):
Bit Position:  8  7  6  5  4  3  2  1  0
               |  |  |  |  |  |  |  |  |
Flag Name:    NS CWR ECE URG ACK PSH RST SYN FIN

Each flag is either 0 (off) or 1 (on).
```

### 1.5 What Is a Handshake?

A **handshake** is an initialization protocol — a sequence of messages exchanged before any real data flows. Its purpose is to:

1. Establish that both parties exist and are reachable
2. Agree on parameters (sequence numbers, window sizes, encryption keys)
3. Synchronize state machines on both sides

### 1.6 What Is a State Machine?

A **state machine** is a model of a system that:
- Has a finite set of **states** (e.g., CLOSED, LISTEN, ESTABLISHED)
- Transitions between states based on **events** (e.g., receiving SYN)
- Produces **actions** during transitions (e.g., send SYN-ACK)

The TCP protocol IS a state machine. Every connection on every host moves through a sequence of states.

### 1.7 What Is Sequence Number / Acknowledgment Number?

- **Sequence Number (SEQ)**: A 32-bit number representing the byte offset of the first byte in this segment. This is how TCP tracks ordering.
- **Acknowledgment Number (ACK)**: Tells the sender "I have received all bytes up to ACK-1, send me byte ACK next."

```
Sender sends bytes 1-1000: SEQ=1
Sender sends bytes 1001-2000: SEQ=1001
Receiver got both: ACK=2001 (means "give me byte 2001 next")
```

### 1.8 What Is a Window?

The **window** (receive window / RWND) is how many bytes the receiver can accept before the sender must stop and wait. It is TCP's flow control mechanism.

```
Sender                  Receiver
  |                        |
  |  [window = 4000 bytes] |
  |  Can send up to 4000   |
  |  bytes without ACK     |
```

### 1.9 What Is TTL / Hop Limit?

**Time To Live (TTL)** in IPv4 (called **Hop Limit** in IPv6) is a counter decremented by each router. When it reaches 0, the packet is discarded. Prevents packets from circulating forever.

### 1.10 What Is MSS?

**Maximum Segment Size (MSS)** is the largest TCP payload (not including TCP/IP headers) that a host is willing to receive in a single segment. Negotiated during the handshake.

```
MSS is NOT the same as MTU.
MTU (Maximum Transmission Unit) = max frame size on the link (typically 1500 bytes for Ethernet)
MSS = MTU - IP header (20 bytes) - TCP header (20 bytes) = 1460 bytes
```

---

## 2. The Network Stack

### 2.1 OSI Model — The Conceptual Framework

The **OSI (Open Systems Interconnection)** model divides networking into 7 layers. Each layer provides services to the layer above and uses services from the layer below.

```
+---------------------------+-------------------------------------+
|  Layer  |   Name          |  Protocol Examples                  |
+---------+-----------------+-------------------------------------+
|    7    | Application     | HTTP, FTP, SMTP, DNS, TLS (partly)  |
|    6    | Presentation    | TLS/SSL, JPEG encoding               |
|    5    | Session         | NetBIOS, RPC, TLS (partly)           |
|    4    | Transport       | TCP, UDP, SCTP, QUIC                 |
|    3    | Network         | IP (v4/v6), ICMP, OSPF, BGP         |
|    2    | Data Link       | Ethernet, Wi-Fi (802.11), ARP        |
|    1    | Physical        | Electrical signals, fiber, radio     |
+---------+-----------------+-------------------------------------+
```

**Key Insight**: The OSI model is a REFERENCE model. In practice, TCP/IP collapses it.

### 2.2 TCP/IP Model — What Actually Runs

```
+---------------------------+-------------------------------------+
|  Layer  |   Name          |  Protocols                          |
+---------+-----------------+-------------------------------------+
|    4    | Application     | HTTP, FTP, DNS, TLS, SSH            |
|    3    | Transport       | TCP, UDP, QUIC                      |
|    2    | Internet        | IP, ICMP, ARP                       |
|    1    | Link            | Ethernet, Wi-Fi, PPP                |
+---------+-----------------+-------------------------------------+
```

### 2.3 How Layers Communicate — Encapsulation and Decapsulation

**Encapsulation** = wrapping data with headers as it goes DOWN the stack (sender side).
**Decapsulation** = stripping headers as it goes UP the stack (receiver side).

```
APPLICATION LAYER (HTTP Request):
+------------------------------------------+
| GET /index.html HTTP/1.1\r\n...          |
+------------------------------------------+

TRANSPORT LAYER adds TCP header:
+----------------+------------------------------------------+
| TCP Header     | GET /index.html HTTP/1.1\r\n...          |
| (src/dst port, | (HTTP payload)                           |
| SEQ, ACK, flags|                                          |
+----------------+------------------------------------------+
        ^
        | This whole thing is called a "TCP Segment"

INTERNET LAYER adds IP header:
+----------+----------------+------------------------------------------+
| IP Header| TCP Header     | HTTP Data                                |
| (src/dst |                |                                          |
| IP addr) |                |                                          |
+----------+----------------+------------------------------------------+
        ^
        | This whole thing is called an "IP Packet"

LINK LAYER adds Ethernet frame:
+--------+----------+----------------+------------------+--------+
| Eth    | IP Header| TCP Header     | HTTP Data        | FCS    |
| Header |          |                |                  | (CRC)  |
+--------+----------+----------------+------------------+--------+
        ^
        | This whole thing is called an "Ethernet Frame"
```

**FCS** = Frame Check Sequence (error detection checksum).

### 2.4 Demultiplexing — How a Packet Finds the Right Process

When a packet arrives at a machine, the kernel must route it to the correct process. This is **demultiplexing**:

```
Incoming Ethernet Frame
         |
         v
   [Ethernet Driver]
         |
         | Strip Ethernet header, look at EtherType field
         | EtherType=0x0800 -> IPv4
         | EtherType=0x86DD -> IPv6
         v
   [IP Layer]
         |
         | Strip IP header, look at Protocol field
         | Protocol=6  -> TCP
         | Protocol=17 -> UDP
         | Protocol=1  -> ICMP
         v
   [TCP Layer]
         |
         | Look up 5-tuple in connection hash table
         | {TCP, src_ip, src_port, dst_ip, dst_port}
         v
   [Socket Receive Buffer]
         |
         v
   [Application process via read()/recv()]
```

---

## 3. What Is a "Connection"

### 3.1 Connection vs. Connectionless

| Feature          | Connection-Oriented (TCP)       | Connectionless (UDP)          |
|------------------|---------------------------------|-------------------------------|
| Handshake        | Yes (3-way)                     | No                            |
| State            | Maintained on both ends         | None                          |
| Reliability      | Guaranteed delivery, ordering   | Best-effort                   |
| Flow Control     | Yes (window)                    | No                            |
| Congestion Ctrl  | Yes (CWND)                      | No                            |
| Overhead         | Higher                          | Lower                         |
| Use Case         | HTTP, SSH, database             | DNS, video streaming, gaming  |

### 3.2 What Defines a Unique Connection?

A TCP connection is uniquely identified by its **5-tuple**:

```
+------------------------------------------------------------------+
|  5-TUPLE                                                         |
|                                                                  |
|  Protocol  = TCP (always 6)                                      |
|  Src IP    = 192.168.1.100                                       |
|  Src Port  = 54321  (ephemeral, chosen by OS)                    |
|  Dst IP    = 93.184.216.34  (example.com)                        |
|  Dst Port  = 80   (HTTP)                                         |
|                                                                  |
|  HASH(5-tuple) -> bucket in kernel connection hash table         |
+------------------------------------------------------------------+
```

Two connections to the same server are DIFFERENT if they have different source ports. This is how the OS allows 65535 simultaneous connections to the same server port.

---

## 4. Protocol Flags

### 4.1 TCP Flags — Complete Reference

TCP flags occupy bits in the **Control Bits** field of the TCP header. Modern TCP uses 9 flags:

```
TCP Header (20 bytes minimum):

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |           |N|C|E|U|A|P|R|S|F|                        |
| Offset| Reserved  |S|W|C|R|C|S|S|Y|I|        Window         |
|       |           | |R|E|G|K|H|T|N|N|                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Flag Definitions**:

| Flag | Bit | Meaning | When Set |
|------|-----|---------|----------|
| FIN  | 0   | Finish — no more data from sender | Connection teardown initiation |
| SYN  | 1   | Synchronize — initiate connection | Handshake only (SYN, SYN-ACK) |
| RST  | 2   | Reset — abort connection immediately | Error, port closed, forced close |
| PSH  | 3   | Push — deliver data to app immediately, don't buffer | Interactive apps (SSH, telnet) |
| ACK  | 4   | Acknowledgment number is valid | All packets except initial SYN |
| URG  | 5   | Urgent pointer field is valid | Rarely used (out-of-band data) |
| ECE  | 6   | ECN Echo — congestion experienced | Congestion notification |
| CWR  | 7   | Congestion Window Reduced | Sender reduced CWND |
| NS   | 8   | Nonce Sum (ECN-related, RFC 3540) | Rarely used |

**How flags are stored in kernel (Linux)**:

```c
/* From linux/tcp.h */
struct tcphdr {
    __be16  source;          /* source port */
    __be16  dest;            /* destination port */
    __be32  seq;             /* sequence number */
    __be32  ack_seq;         /* acknowledgment number */
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u16   res1:4,
            doff:4,          /* data offset (header length in 32-bit words) */
            fin:1,
            syn:1,
            rst:1,
            psh:1,
            ack:1,
            urg:1,
            ece:1,
            cwr:1;
#elif defined(__BIG_ENDIAN_BITFIELD)
    __u16   doff:4,
            res1:4,
            cwr:1,
            ece:1,
            urg:1,
            ack:1,
            psh:1,
            rst:1,
            syn:1,
            fin:1;
#endif
    __be16  window;          /* receive window */
    __sum16 check;           /* checksum */
    __be16  urg_ptr;         /* urgent pointer */
};
```

### 4.2 IP Flags

IPv4 header has a **3-bit Flags field**:

```
IP Header Flags (3 bits):
  Bit 0: Reserved (must be 0)
  Bit 1: DF = Don't Fragment (0=may fragment, 1=don't fragment)
  Bit 2: MF = More Fragments (0=last fragment, 1=more coming)

Also: Fragment Offset (13 bits) — byte offset of this fragment / 8
```

```c
/* From linux/ip.h */
struct iphdr {
    __u8    ihl:4,           /* header length in 32-bit words */
            version:4;       /* IP version (4) */
    __u8    tos;             /* type of service */
    __be16  tot_len;         /* total length */
    __be16  id;              /* identification (for fragment reassembly) */
    __be16  frag_off;        /* fragment offset + flags */
    __u8    ttl;             /* time to live */
    __u8    protocol;        /* upper layer protocol (6=TCP, 17=UDP) */
    __sum16 check;           /* header checksum */
    __be32  saddr;           /* source IP */
    __be32  daddr;           /* destination IP */
};
```

### 4.3 How Are Flags Checked in the Kernel?

```c
/* Example: checking if SYN flag is set */
if (tcp_hdr->syn && !tcp_hdr->ack) {
    /* This is an initial SYN — new connection attempt */
}

if (tcp_hdr->fin) {
    /* Sender is done sending data */
}

if (tcp_hdr->rst) {
    /* Immediate connection abort */
}

/* Checking IP flags */
#define IP_DF   0x4000   /* don't fragment flag */
#define IP_MF   0x2000   /* more fragments flag */
#define IP_OFFSET 0x1FFF /* mask for fragmenting bits */

if (ntohs(iph->frag_off) & IP_DF) {
    /* Don't fragment this packet */
}
```

### 4.4 TCP Option Flags (Negotiated During Handshake)

During the SYN/SYN-ACK, TCP options are exchanged:

```
TCP Options in SYN:
+--------+--------+
| Kind=2 | Len=4  | MSS Option (Max Segment Size)
+--------+--------+--------+--------+
| Maximum Segment Size Value (2 bytes)
+--------+--------+

+--------+--------+--------+
| Kind=3 | Len=3  | Shift  | Window Scale Option
+--------+--------+--------+

+--------+--------+
| Kind=4 | Len=2  | SACK Permitted (Selective ACK)
+--------+--------+

+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| Kind=8 | Len=10 | Timestamp Value (4 bytes)              | Timestamp Echo Reply (4 bytes) |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+--------+
```

**Window Scale**: The window field is only 16 bits (max 65535 bytes). The Window Scale option allows shifting it left by up to 14 bits, giving a window up to ~1GB.

---

## 5. Connection Initialization

### 5.1 TCP Three-Way Handshake — Complete Deep Dive

**Concept**: Before any data flows, TCP must:
1. Verify both parties are reachable
2. Synchronize sequence numbers (ISN = Initial Sequence Number)
3. Exchange parameters (MSS, SACK, window scale)

**Why random ISN?** If ISN were always 0, an attacker could inject packets into old connections that have the same 5-tuple. The OS generates a pseudo-random ISN using a hash of the 5-tuple + timestamp + secret key.

```
CLIENT                          SERVER
(CLOSED)                        (LISTEN)
   |                               |
   |  Step 1: Client sends SYN    |
   |  SYN=1, SEQ=x                |
   |  (x = client's random ISN)   |
   |------------------------------>|
   |                               |  Server: receives SYN
(SYN_SENT)                     (SYN_RCVD)
   |                               |
   |  Step 2: Server sends SYN-ACK |
   |  SYN=1, ACK=1                |
   |  SEQ=y   (server's ISN)      |
   |  ACK_SEQ=x+1 (x+1 expected)  |
   |<------------------------------|
   |                               |
   |  Step 3: Client sends ACK    |
   |  ACK=1                       |
   |  SEQ=x+1                     |
   |  ACK_SEQ=y+1                 |
   |------------------------------>|
   |                               |
(ESTABLISHED)               (ESTABLISHED)
   |                               |
   |  Data can now flow both ways  |
   |<=============================>|
```

**Why x+1?** The SYN flag itself "consumes" one sequence number. So after sending SYN with SEQ=x, the next expected byte is x+1.

**SYN packet contents** (with options):

```
TCP SYN Segment:
+-------------------+-------------------+
| Source Port: 54321| Dest Port: 80     |
+-------------------------------------------+
| Sequence Number: 0x7F3A2B1C               |
+-------------------------------------------+
| Acknowledgment: 0x00000000                 |
+-------------------------------------------+
| Offset:5  Reserved | CWR ECE URG ACK PSH RST SYN FIN |
|           0010     | 0   0   0   0   0   0   1   0   |
+-------------------------------------------+
| Window: 65535                             |
+-------------------------------------------+
| Checksum: 0xABCD   | Urgent Ptr: 0        |
+-------------------------------------------+
| Options:                                  |
|   MSS = 1460                              |
|   SACK Permitted                          |
|   Timestamp: val=1000, ecr=0              |
|   Window Scale = 7  (multiply window by 128)|
+-------------------------------------------+
```

### 5.2 TCP SYN Queue and Accept Queue — Server Side

The server maintains **two queues** for incoming connections:

```
                        SERVER KERNEL

Incoming SYN
    |
    v
+------------------+
|  SYN Queue       |  (also called incomplete connection queue)
|  (backlog/2)     |  Entries: half-open connections in SYN_RCVD
|                  |  Max size: net.ipv4.tcp_max_syn_backlog
+------------------+
    |
    | After receiving final ACK from client
    | (3-way handshake complete)
    v
+------------------+
|  Accept Queue    |  (also called complete connection queue)
|                  |  Entries: ESTABLISHED connections
|                  |  Max size: listen() backlog parameter
+------------------+
    |
    | Application calls accept()
    v
+------------------+
|  Application     |  Gets a new socket fd for this connection
+------------------+
```

**SYN Flood Attack**: Attacker sends many SYN packets with spoofed source IPs. Never sends the final ACK. Fills the SYN queue until no new connections can be accepted.

**SYN Cookies** (defense): When SYN queue is full, instead of storing state, the server encodes the connection parameters INTO the sequence number of the SYN-ACK. If a valid ACK comes back, the state can be reconstructed from the sequence number. Net result: no SYN queue entry needed.

### 5.3 UDP — "Connectionless" Initialization

UDP has no handshake. However, applications can call `connect()` on a UDP socket, which does NOT send any network packet — it merely records the default destination in the socket structure, allowing `send()` instead of `sendto()`.

```
UDP sendto() flow:
Application                         Kernel
    |                                  |
    | sendto(fd, data, len, 0,         |
    |        &dest_addr, addrlen)      |
    |--------------------------------->|
    |                                  |  Create UDP datagram:
    |                                  |  + UDP header (8 bytes)
    |                                  |  + IP header
    |                                  |  + Ethernet frame
    |                                  |  -> Send to NIC immediately
```

**No state is stored for the "connection".** Each UDP datagram is independent.

### 5.4 TLS Handshake (TLS 1.3) — Application Layer Connection Init

TLS sits between Transport (TCP) and Application (HTTP). It establishes an encrypted channel AFTER the TCP connection is established.

```
CLIENT                                          SERVER
  |                                               |
  | TCP 3-way handshake (already established)    |
  |<=============================================>|
  |                                               |
  | --- TLS ClientHello -----------------------> |
  |  - supported TLS versions                    |
  |  - random nonce (client_random)              |
  |  - session_id (for resumption)               |
  |  - cipher suites (e.g. AES-GCM, ChaCha20)   |
  |  - supported_groups (elliptic curves)        |
  |  - key_share (Diffie-Hellman public key)     |
  |                                               |
  | <-- TLS ServerHello + encrypted data ------  |
  |  - chosen cipher suite                       |
  |  - server_random                             |
  |  - key_share (DH public key)                 |
  |  [From here: all data is ENCRYPTED]          |
  |  + {EncryptedExtensions}                     |
  |  + {Certificate}                             |
  |  + {CertificateVerify}                       |
  |  + {Finished}                                |
  |                                               |
  | --- {Finished} ----------------------------> |
  |                                               |
  | <====== Encrypted Application Data =======>  |
  |            (HTTP, etc.)                       |
```

**TLS 1.3 key innovation**: The client sends its DH key share in the ClientHello itself, so the server can compute the shared secret immediately and send encrypted data in its first response. This achieves **0-RTT for the handshake itself** (1 round-trip vs 2 in TLS 1.2).

**Key Derivation** (conceptual):
```
client_random + server_random + DH_shared_secret
         |
         v
    HKDF (Hash-based Key Derivation Function)
         |
         v
   handshake_key + application_key + resumption_key
```

### 5.5 HTTP/1.1 Connection Setup

HTTP/1.1 uses **persistent connections** by default (`Connection: keep-alive`). After TCP (and optionally TLS) setup, HTTP itself has no handshake — the client just sends the first request.

```
CLIENT                          SERVER
  |  [TCP established]            |
  |  GET /index.html HTTP/1.1     |
  |  Host: example.com            |
  |  Connection: keep-alive       |
  |------------------------------>|
  |                               |
  |  HTTP/1.1 200 OK              |
  |  Content-Length: 1234         |
  |  Connection: keep-alive       |
  |<------------------------------|
  |  [TCP connection stays open]  |
  |  GET /style.css HTTP/1.1      |
  |------------------------------>|
  |  ...                          |
```

### 5.6 HTTP/2 Connection Setup

HTTP/2 starts with a **connection preface** after TLS:

```
CLIENT sends immediately after TLS:
  PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n  (24 bytes, magic string)
  + SETTINGS frame

SERVER responds with:
  SETTINGS frame
  SETTINGS_ACK

Then multiplexed streams can begin.
```

### 5.7 QUIC Connection Setup (HTTP/3)

QUIC runs over UDP and combines TLS 1.3 + transport-layer connection establishment:

```
CLIENT                                  SERVER
  |                                       |
  | --- Initial Packet (QUIC+TLS) ------> |
  |  connection ID                        |
  |  TLS ClientHello                      |
  |                                       |
  | <-- Initial + Handshake Packets ----- |
  |  TLS ServerHello + certificate        |
  |  Handshake Keys derived               |
  |                                       |
  | --- Handshake Packet (Finished) ----> |
  |                                       |
  | <====== 1-RTT encrypted data ======>  |
```

QUIC eliminates the extra TCP handshake RTT. On resumption, it can achieve **0-RTT** (data sent before server confirmation).

### 5.8 DNS — Initialization Is Just a Query

DNS typically uses UDP. There is no connection. Client sends query, server sends response. If response exceeds 512 bytes (or more with EDNS0), TCP is used.

```
CLIENT                     DNS RESOLVER (UDP/53)
  |                              |
  | DNS Query (UDP datagram)     |
  | ID=0x1234, Type=A            |
  | QNAME=example.com            |
  |----------------------------->|
  |                              |  Look up in cache or recurse
  | DNS Response (UDP datagram)  |
  | ID=0x1234 (same ID!)         |
  | ANSWER: 93.184.216.34, TTL=86400 |
  |<-----------------------------|
```

---

## 6. How Connections Are Remembered — State Storage

### 6.1 The Socket Structure in Linux Kernel

Every TCP connection is represented by a `struct sock` (and its TCP-specific extension `struct tcp_sock`) in the Linux kernel.

```
struct sock (simplified from include/net/sock.h):
+----------------------------------------------------------+
|  sk_family       : AF_INET or AF_INET6                   |
|  sk_type         : SOCK_STREAM / SOCK_DGRAM              |
|  sk_protocol     : IPPROTO_TCP / IPPROTO_UDP             |
|                                                          |
|  sk_rcvbuf       : receive buffer size                   |
|  sk_sndbuf       : send buffer size                      |
|  sk_receive_queue: struct sk_buff_head  (RX queue)       |
|  sk_write_queue  : struct sk_buff_head  (TX queue)       |
|                                                          |
|  sk_state        : TCP state (TCP_ESTABLISHED, etc.)     |
|  sk_err          : last error                            |
|  sk_socket       : pointer to VFS socket                 |
|  sk_prot         : pointer to proto struct (tcp_prot)    |
+----------------------------------------------------------+

struct tcp_sock (extends sock, from include/linux/tcp.h):
+----------------------------------------------------------+
|  [struct inet_connection_sock  (inherits from sock)]     |
|    icsk_retransmit_timer  : retransmission timer         |
|    icsk_delack_timer      : delayed ACK timer            |
|                                                          |
|  rcv_nxt      : next expected receive sequence number    |
|  snd_nxt      : next sequence number to send             |
|  snd_una      : oldest unacknowledged sequence number    |
|  rcv_wnd      : receive window                          |
|  snd_wnd      : send window (from remote's advertisement)|
|  snd_cwnd     : congestion window                       |
|  snd_ssthresh : slow start threshold                    |
|                                                          |
|  rx_opt       : TCP options received                    |
|    .mss_clamp : maximum segment size                    |
|    .wscale    : window scale factor                     |
|    .sack_ok   : SACK permitted                          |
|    .tstamp_ok : timestamps ok                           |
+----------------------------------------------------------+
```

### 6.2 The Connection Hash Table

Linux maintains a hash table to quickly find the socket for an incoming packet. The key is the 5-tuple.

```
Incoming packet: {TCP, 10.0.0.1:54321, 10.0.0.2:80}
         |
         | HASH(src_ip, src_port, dst_ip, dst_port, net_namespace)
         v
+--------+--------+--------+--------+--------+
| bucket | bucket | bucket | bucket | bucket |  <-- ehash (established hash)
+--------+--------+--------+--------+--------+
             |
             v
         [ struct sock * ] -> [ struct sock * ] -> NULL
                (linked list for hash collisions)
```

**Three separate hash tables in Linux TCP**:

```
1. tcp_hashinfo.ehash    : ESTABLISHED and CLOSE_WAIT connections
2. tcp_hashinfo.bhash    : Bound sockets (LISTEN state, indexed by port)
3. tcp_hashinfo.lhash2   : Listening sockets (indexed by addr+port)
```

```c
/* From include/net/inet_hashtables.h */
struct inet_hashinfo {
    struct inet_ehash_bucket    *ehash;       /* established connections */
    spinlock_t                  *ehash_locks;
    unsigned int                 ehash_mask;

    struct inet_bind_hashbucket *bhash;       /* bound ports */
    unsigned int                 bhash_size;

    struct inet_listen_hashbucket *lhash2;    /* listening sockets */
};
```

### 6.3 Netfilter Connection Tracking (conntrack)

The Linux firewall subsystem (Netfilter/iptables/nftables) maintains its OWN connection tracking table, separate from the TCP socket table. This allows stateful firewalling for ALL protocols (including UDP, ICMP).

```
+--------------------------------------------------------------+
|  NETFILTER CONNTRACK TABLE                                   |
|                                                              |
|  Each entry = struct nf_conn                                 |
|                                                              |
|  Key: { proto, src_ip, src_port, dst_ip, dst_port }         |
|                                                              |
|  State for TCP:                                              |
|    TCP_CONNTRACK_NONE        = 0                             |
|    TCP_CONNTRACK_SYN_SENT    = 1                             |
|    TCP_CONNTRACK_SYN_RECV    = 2                             |
|    TCP_CONNTRACK_ESTABLISHED = 3                             |
|    TCP_CONNTRACK_FIN_WAIT    = 4                             |
|    TCP_CONNTRACK_CLOSE_WAIT  = 5                             |
|    TCP_CONNTRACK_LAST_ACK    = 6                             |
|    TCP_CONNTRACK_TIME_WAIT   = 7                             |
|    TCP_CONNTRACK_CLOSE       = 8                             |
|                                                              |
|  Timeout: auto-expires entries after inactivity             |
|  Direction: tracks ORIGINAL and REPLY directions            |
|  NAT: can be attached for NAT translations                  |
+--------------------------------------------------------------+
```

**conntrack** allows rules like "ACCEPT packets belonging to ESTABLISHED connections" without explicitly tracking ports.

### 6.4 TCP State Machine — Complete States

```
                              +--------+
                              | CLOSED |
                              +--------+
                              /        \
                    passive      |        |   active
                    open()       |        |   open()
                                 |        |
                                 v        v
                            +--------+  +----------+
                            | LISTEN |  | SYN_SENT |
                            +--------+  +----------+
                                 |              |
                    recv SYN     |              |   recv SYN+ACK
                    send SYN+ACK |              |   send ACK
                                 v              |
                           +----------+         |
                           | SYN_RCVD |         |
                           +----------+         |
                                 |              |
                    recv ACK     |              |
                                 v              v
                           +-------------+------+
                           |  ESTABLISHED       |
                           +--------------------+
                           /                    \
                 close()  /                      \  recv FIN
                 send FIN /                       \  send ACK
                         v                         v
                  +-----------+             +------------+
                  | FIN_WAIT_1|             | CLOSE_WAIT |
                  +-----------+             +------------+
                  /           \                   |
       recv FIN  /             \ recv ACK          |  close()
       send ACK /               \                 |  send FIN
               v                 v                v
        +-----------+     +-----------+    +----------+
        | CLOSING   |     | FIN_WAIT_2|    | LAST_ACK |
        +-----------+     +-----------+    +----------+
               \                 |                |
      recv ACK  \       recv FIN |       recv ACK |
                 v        send ACK|               v
           +-----------+  |    +--------+    +--------+
           | TIME_WAIT |<-+    |TIME_WAIT|   | CLOSED |
           +-----------+       +--------+
                 |
       2*MSL timeout
                 v
           +--------+
           | CLOSED |
           +--------+
```

**Explanation of each state**:

| State       | Who           | Meaning                                               |
|-------------|---------------|-------------------------------------------------------|
| CLOSED      | Both          | No connection exists                                  |
| LISTEN      | Server        | Waiting for incoming SYN                              |
| SYN_SENT    | Client        | Sent SYN, waiting for SYN-ACK                         |
| SYN_RCVD    | Server        | Received SYN, sent SYN-ACK, waiting for ACK           |
| ESTABLISHED | Both          | Connection open, data can flow                        |
| FIN_WAIT_1  | Active closer | Sent FIN, waiting for ACK or FIN                      |
| FIN_WAIT_2  | Active closer | Received ACK of FIN, waiting for remote FIN           |
| CLOSE_WAIT  | Passive closer| Received FIN, sent ACK, waiting for app to close      |
| CLOSING     | Both          | Both sides sent FIN simultaneously, waiting for ACKs  |
| LAST_ACK    | Passive closer| Sent FIN after CLOSE_WAIT, waiting for final ACK      |
| TIME_WAIT   | Active closer | Waiting 2*MSL to ensure remote received final ACK     |

### 6.5 TIME_WAIT — Why It Exists

**TIME_WAIT** lasts **2 * MSL** (Maximum Segment Lifetime, typically 60 seconds = 2 minutes total).

**Two reasons**:

1. **Ensure the remote received the final ACK**: If the ACK is lost, remote will resend FIN. We must be able to respond with ACK again. If we went to CLOSED immediately, we'd send RST instead.

2. **Prevent stale packets from old connections**: If a new connection uses the same 5-tuple as an old one, stale packets from the old connection floating in the network could corrupt the new one. TIME_WAIT ensures all such packets have expired (TTL-based expiry).

```
TIME_WAIT Problem in High-Traffic Servers:
  - Server handles 10,000 connections/sec
  - Each stays in TIME_WAIT for 60s
  - That's 600,000 TIME_WAIT sockets simultaneously
  - Solution: SO_REUSEADDR + tcp_tw_reuse + tcp_fin_timeout
```

---

## 7. Cross-Layer Protocol Coordination

### 7.1 How TCP Talks to IP

When TCP wants to send a segment, it calls into the IP layer via function pointers in the protocol structure:

```
TCP Layer                           IP Layer
    |                                  |
    |  tcp_transmit_skb()              |
    |  -> ip_queue_xmit()              |
    |  -> skb_push(skb, ip_hdr_len)   |
    |  -> ip_local_out()               |
    |  -> dst_output()                 |
    |  -> ip_output()                  |
    |  -> ip_finish_output()           |
    |  -> ip_finish_output2()          |
    |  -> dev_queue_xmit()             |
    |                                  |
    v                                  v
[Network Interface Driver]
    |
    v
[Physical Network]
```

### 7.2 The sk_buff — Kernel's Packet Container

`sk_buff` (socket buffer) is the kernel data structure that holds a packet as it travels through the network stack. It is the single most important data structure in Linux networking.

```
struct sk_buff (simplified):
+----------------------------------------------------------+
|  next, prev        : doubly linked list pointers         |
|  sk                : owning socket (or NULL for rx)      |
|  tstamp            : arrival timestamp                   |
|                                                          |
|  head              : start of allocated buffer           |
|  data              : start of valid data                 |
|  tail              : end of valid data                   |
|  end               : end of allocated buffer             |
|                                                          |
|  len               : length of actual data               |
|  data_len          : length in fragments (scatter-gather)|
|                                                          |
|  mac_header        : offset to MAC (Ethernet) header     |
|  network_header    : offset to IP header                 |
|  transport_header  : offset to TCP/UDP header            |
|                                                          |
|  csum              : checksum                            |
|  ip_summed         : checksum status                     |
+----------------------------------------------------------+

Buffer Layout:
+--------+-----------+---------+---------+-----------+--------+
| head   | headroom  | ETH HDR | IP HDR  | TCP HDR   | DATA   |
+--------+-----------+---------+---------+-----------+--------+
^        ^           ^         ^         ^           ^        ^
head  (reserved)  mac_header  network   transport  data      tail
                              _header   _header
```

**Headroom** is reserved space at the front of the buffer. Lower layers push their headers into this space using `skb_push()`, which moves the `data` pointer backward.

```
Application data added:           [        DATA        ]
TCP adds header:     [TCP HDR][        DATA        ]
IP adds header:  [IP HDR][TCP HDR][        DATA        ]
Eth adds header: [ETH][IP HDR][TCP HDR][        DATA        ]
```

This is done WITHOUT copying the data — only pointer manipulation.

### 7.3 ARP — How IP Finds MAC Addresses

**ARP (Address Resolution Protocol)** translates IP addresses to MAC (Ethernet) addresses. It operates at Layer 2/3 boundary.

```
Scenario: Host A (10.0.0.1) wants to send to Host B (10.0.0.2)
          Host A knows B's IP but not B's MAC address.

HOST A                    (Ethernet Broadcast)              HOST B
  |                                                          |
  | ARP Request (broadcast)                                  |
  | "Who has 10.0.0.2? Tell 10.0.0.1"                       |
  | Src MAC: AA:BB:CC:DD:EE:FF                              |
  | Dst MAC: FF:FF:FF:FF:FF:FF (broadcast)                  |
  |--------------------------------------------------------->|
  |                               (all hosts receive this)   |
  |                                                          |
  | ARP Reply (unicast from B)                              |
  | "10.0.0.2 is at 11:22:33:44:55:66"                     |
  |<---------------------------------------------------------|
  |                                                          |
  | [Host A stores in ARP cache]                             |
  | Now can send IP packets to B directly via MAC           |
```

**ARP Cache** in Linux:
```bash
ip neigh show    # show ARP/neighbor table
# Output: 10.0.0.2 dev eth0 lladdr 11:22:33:44:55:66 STALE
```

### 7.4 ICMP — Control Messages for IP

**ICMP (Internet Control Message Protocol)** is used by IP-layer devices to send error and informational messages.

```
ICMP Message Types:
  Type 0: Echo Reply      (ping response)
  Type 3: Destination Unreachable
    Code 0: Net Unreachable
    Code 1: Host Unreachable
    Code 3: Port Unreachable    <- UDP sends this when port closed!
    Code 4: Fragmentation Needed (and DF bit set)  <- Path MTU Discovery
  Type 8: Echo Request    (ping)
  Type 11: Time Exceeded
    Code 0: TTL exceeded  <- traceroute uses this!
  Type 12: Parameter Problem
```

**Path MTU Discovery**: If a router needs to fragment a packet but DF=1, it sends ICMP Type 3 Code 4 back to the sender. TCP reacts by reducing MSS.

### 7.5 Protocol Multiplexing at Each Layer

```
RECEIVE PATH (top to bottom in this diagram = packet going UP the stack):

[NIC Hardware Interrupt / NAPI Poll]
         |
         v
[Ethernet Driver: netif_receive_skb()]
         |
         | Check EtherType field:
         | 0x0800 = IPv4  -> ip_rcv()
         | 0x86DD = IPv6  -> ipv6_rcv()
         | 0x0806 = ARP   -> arp_rcv()
         v
[IP Layer: ip_rcv() -> ip_rcv_finish()]
         |
         | Check Protocol field:
         | 6  = TCP  -> tcp_v4_rcv()
         | 17 = UDP  -> udp_rcv()
         | 1  = ICMP -> icmp_rcv()
         | 89 = OSPF -> (raw socket)
         v
[TCP Layer: tcp_v4_rcv()]
         |
         | Lookup 5-tuple in ehash
         | Find struct sock
         | Call tcp_rcv_established() or tcp_rcv_state_process()
         v
[Socket Receive Buffer]
         |
         v
[Application: read() / recv() / recvmsg()]
```

---

## 8. Connection Lifetime Management

### 8.1 TCP Keepalive

**Problem**: A TCP connection can be ESTABLISHED with no data flowing. How do we know if the remote end is still alive? NAT boxes often silently drop idle connections.

**TCP Keepalive**: After a period of inactivity, TCP sends **keepalive probes** — small ACK packets with SEQ one less than the current (so they don't advance the window but force a response).

```
Configuration (per socket or system-wide):
  tcp_keepalive_time    : idle time before first probe (default: 7200s = 2h)
  tcp_keepalive_intvl   : interval between probes (default: 75s)
  tcp_keepalive_probes  : number of probes before giving up (default: 9)

Timeline:
  t=0           Connection established
  t=7200s       First keepalive probe sent
  t=7275s       No response: second probe
  t=7350s       No response: third probe
  ...
  t=7875s       After 9 probes: connection declared dead, ETIMEDOUT
```

**Setting keepalive on a socket (C)**:
```c
int optval = 1;
setsockopt(sockfd, SOL_SOCKET, SO_KEEPALIVE, &optval, sizeof(optval));

int idle = 60;    // start probing after 60s idle
setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPIDLE, &idle, sizeof(idle));

int intvl = 10;   // probe every 10s
setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPINTVL, &intvl, sizeof(intvl));

int cnt = 3;      // give up after 3 failed probes
setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPCNT, &cnt, sizeof(cnt));
```

### 8.2 TCP Timeouts

TCP maintains several timers per connection:

```
+-------------------+------------------------------------------+-------------------+
| Timer             | Purpose                                  | Default           |
+-------------------+------------------------------------------+-------------------+
| Retransmit Timer  | Resend unACK'd segment                   | 200ms (doubles)   |
| Persist Timer     | Probe zero-window (window opened)        | Variable          |
| Keepalive Timer   | Detect dead peers                        | 2 hours           |
| FIN_WAIT_2 Timer  | Limit time in FIN_WAIT_2 state           | 60s               |
| TIME_WAIT Timer   | Linger after close                       | 2*MSL = 60-120s   |
| Delayed ACK Timer | Batch ACKs for efficiency                | 40ms              |
+-------------------+------------------------------------------+-------------------+
```

**Retransmission**: Uses **Exponential Backoff**. Initial RTO (Retransmission Timeout) is calculated from RTT measurements (Karn's algorithm). Each retry doubles the timeout.

```
RTO calculation:
  SRTT = Smoothed RTT  (exponential moving average of measured RTTs)
  RTTVAR = RTT Variance
  RTO = SRTT + max(G, 4 * RTTVAR)   (G = clock granularity, typically 1ms)
```

### 8.3 Connection Pooling

**Connection pooling** is an application-level technique where connections are created once and reused, avoiding the overhead of repeated TCP+TLS handshakes.

```
Without pooling (per-request):
  Request 1: TCP SYN -> SYN-ACK -> ACK -> TLS -> Request -> Response -> FIN
  Request 2: TCP SYN -> SYN-ACK -> ACK -> TLS -> Request -> Response -> FIN

RTT cost per request: ~4 RTTs for HTTPS/1.1

With pooling:
  Initial: TCP SYN -> SYN-ACK -> ACK -> TLS
  Request 1: Request -> Response         (kept alive)
  Request 2: Request -> Response         (reused)
  Request N: Request -> Response
  Final: FIN

RTT cost after warmup: ~1 RTT per request
```

### 8.4 Half-Open Connections

A **half-open connection** is one where one side thinks it's ESTABLISHED but the other side has no knowledge of it (e.g., after a crash). When the "alive" side sends data, the dead side will send RST.

```
HOST A                      HOST B
  |  [ESTABLISHED]            |  [CRASHED and rebooted]
  |                           |
  |  data segment ----------->|
  |                           |  No connection found for 5-tuple
  |  <----------- RST --------|
  |                           |
  | [connection aborted]      |
```

---

## 9. Connection Termination

### 9.1 TCP Four-Way Handshake (Graceful Close)

TCP is **full-duplex**: each direction must be closed independently. This is why teardown requires 4 messages instead of 3.

**Who initiates**: Either side can initiate the close by calling `close()` or `shutdown()`. The initiator is called the **active closer**; the other side is the **passive closer**.

```
ACTIVE CLOSER              PASSIVE CLOSER
(calls close())            (app still running)
     |                           |
     | Step 1: FIN              |
     | FIN=1, ACK=1             |
     | SEQ=x, ACK_SEQ=y         |
     |-------------------------->|
     |                           |
(FIN_WAIT_1)             (CLOSE_WAIT)
     |                           | [Kernel: notify app that peer closed]
     |                           | [App: can still send data!]
     |                           |
     | Step 2: ACK              |
     | ACK=1, ACK_SEQ=x+1      |
     |<--------------------------|
     |                           |
(FIN_WAIT_2)                     |
     |                           | [App calls close()]
     |                           |
     | Step 3: FIN              |
     | FIN=1, ACK=1             |
     |<--------------------------|
     |                           |
(TIME_WAIT)              (LAST_ACK)
     |                           |
     | Step 4: ACK              |
     | ACK=1, ACK_SEQ=y+1      |
     |-------------------------->|
     |                           |
     | [Wait 2*MSL = 60-120s]    | [CLOSED immediately]
     |                           |
(CLOSED)
```

**Why 4 packets and not 3?** The ACK in Step 2 and the FIN in Step 3 are sent SEPARATELY because the application might still have data to send after receiving the peer's FIN. The kernel ACKs the FIN immediately, but the application-level FIN must wait until the app calls `close()`.

### 9.2 Simultaneous Close

Both sides call `close()` at the same time:

```
HOST A                      HOST B
  |  FIN ---------------------->|
  |<--------------------- FIN  |
  |  (both go to CLOSING state) |
  |  ACK ---------------------->|
  |<--------------------- ACK  |
  |                             |
(TIME_WAIT on both sides)
```

### 9.3 RST — Abortive Close

**RST (Reset)** immediately destroys the connection without the 4-way handshake. No TIME_WAIT. All buffered data is discarded.

**When is RST sent?**

```
Scenario 1: Client connects to a port where nothing is listening
  CLIENT                      SERVER
    | SYN ---------------------->|
    | (port 8080 not listening)  |
    |<--------------------- RST |

Scenario 2: Application calls close() with SO_LINGER and l_linger=0
  setsockopt(fd, SOL_SOCKET, SO_LINGER, &linger, sizeof(linger))
  (linger.l_onoff=1, linger.l_linger=0)
  close(fd)  -->  sends RST instead of FIN

Scenario 3: Data arrives for CLOSED connection
  Any data for a 5-tuple with no matching socket -> RST

Scenario 4: Sequence number out of window (half-open detection)
  Out-of-window segment -> RST
```

**Setting SO_LINGER for RST close (C)**:
```c
struct linger sl = { .l_onoff = 1, .l_linger = 0 };
setsockopt(sockfd, SOL_SOCKET, SO_LINGER, &sl, sizeof(sl));
close(sockfd);  /* sends RST, immediate */
```

### 9.4 shutdown() vs close()

```c
shutdown(fd, SHUT_RD)   /* close read side: recv() returns 0 */
shutdown(fd, SHUT_WR)   /* close write side: sends FIN, peer gets EOF */
shutdown(fd, SHUT_RDWR) /* close both: sends FIN */
close(fd)               /* decrements refcount; FIN sent when refcount=0 */
```

`shutdown()` immediately sends FIN (write side) regardless of reference count. `close()` only sends FIN when the last reference to the socket is closed (important for forked processes sharing a socket).

### 9.5 Who Is Responsible for Termination?

```
+------------------------------------------+
|  RESPONSIBILITY MAP                      |
|                                          |
|  TCP Layer (kernel):                     |
|    - Sends ACKs automatically            |
|    - Manages TIME_WAIT                   |
|    - Handles RST for unknown connections |
|    - Retransmits unACK'd FINs            |
|                                          |
|  Application:                            |
|    - Decides WHEN to close (call close())|
|    - Chooses graceful (FIN) or abortive  |
|      (SO_LINGER+RST)                     |
|    - Handles CLOSE_WAIT (must close fd)  |
|                                          |
|  OS / Kernel:                            |
|    - Sends FIN when fd is closed         |
|    - Manages TIME_WAIT timeout           |
|    - Cleans up socket buffers            |
+------------------------------------------+
```

**CLOSE_WAIT leak**: A common bug — if the application never calls `close()` after the peer closes, the socket stays in CLOSE_WAIT forever. This is always an application bug.

---

## 10. Session Handling

### 10.1 What Is a Session vs Connection?

```
+----------------------------------------------------------+
|  LAYER      | TERM       | LIFESPAN                     |
+----------------------------------------------------------+
|  Transport  | Connection | TCP: from SYN to TIME_WAIT   |
|  Session    | Session    | May span multiple connections|
|  Application| Session    | Defined by application logic |
+----------------------------------------------------------+

Examples:
  HTTP/1.1 persistent: 1 TCP connection = many request/response pairs
  TLS Session: Can be resumed across different TCP connections
  HTTP Session: Cookie-based, may span many TCP connections/days
  SSH Session: Lasts until user disconnects (single TCP connection)
```

### 10.2 TLS Session Resumption

TLS sessions can be **resumed** on new TCP connections without full handshake:

**Session ID (TLS 1.2)**:
```
First connection: Full handshake -> Server sends session_id=0xABCD1234
                  Both sides store session state keyed by session_id

Second connection (same server):
  ClientHello: session_id=0xABCD1234
  Server: "I know this session"
  ServerHello: session_id=0xABCD1234
  [skip Certificate + KeyExchange]
  Both sides derive keys from stored master_secret
  -> 1 RTT instead of 2 RTT
```

**Session Tickets (TLS 1.2/1.3)**:
```
Server encrypts session state with its own key
Sends it to client as "session ticket"
Client stores the opaque blob

Second connection:
  ClientHello + session ticket
  Server decrypts ticket, recovers state
  -> No server-side storage needed!
```

**TLS 1.3 0-RTT**:
```
On first connection: server sends "early data" key material
On reconnect: client can send application data WITH the ClientHello
  -> 0 additional round trips for resumption
  
Security cost: 0-RTT is susceptible to replay attacks
               (an attacker can replay the initial data)
```

### 10.3 HTTP Session — Cookies

HTTP is **stateless** (no memory between requests). Sessions are implemented via **cookies**:

```
Browser                             Server
  |  GET /login                      |
  |--------------------------------->|
  |  POST /login {user, pass}        |
  |--------------------------------->|
  |                                  | Verify credentials
  |                                  | Generate: session_id = random_token
  |                                  | Store in DB: {session_id -> user_id}
  |  HTTP/1.1 200 OK                 |
  |  Set-Cookie: sess=abc123; Path=/ |
  |<---------------------------------|
  |                                  |
  | [Browser stores cookie]          |
  |                                  |
  |  GET /dashboard                  |
  |  Cookie: sess=abc123             |
  |--------------------------------->|
  |                                  | Lookup session_id in DB -> user_id
  |  HTTP/1.1 200 OK (dashboard)     |
  |<---------------------------------|
```

**Session storage options**:
- In-memory (fast, lost on restart, not distributable)
- Database (durable, shareable, slower)
- Redis (fast, shared, TTL-based expiry)
- JWT (stateless: token IS the session, no storage needed)

### 10.4 Who Is Responsible for Session Handling?

```
+-----------------------------------------------+
|  LAYER            | RESPONSIBLE FOR           |
+-----------------------------------------------+
|  Kernel (TCP)     | Connection lifetime only  |
|                   | Has no concept of session |
+-----------------------------------------------+
|  TLS Library      | TLS session resumption    |
|  (OpenSSL,        | Session tickets/IDs       |
|   rustls, etc.)   | Key material storage      |
+-----------------------------------------------+
|  HTTP Library     | Keep-Alive connection reuse|
|  (nginx, hyper)   | Connection pooling        |
+-----------------------------------------------+
|  Application      | User sessions via cookies |
|                   | Session storage (DB/Redis)|
|                   | Session timeout logic     |
+-----------------------------------------------+
```

---

## 11. Linux Kernel Network Stack Deep Dive

### 11.1 Complete Receive Path — From NIC to Application

```
NIC HARDWARE
    |
    | DMA: NIC writes packet to ring buffer in RAM
    | Raises hardware interrupt
    v
[Hardware Interrupt Handler]
    |
    | Disable further interrupts for this NIC (NAPI)
    | Schedule softirq (NET_RX_SOFTIRQ)
    v
[SoftIRQ: net_rx_action()]
    |
    | Call driver's poll() function
    v
[Driver poll(): e.g., igb_poll(), e1000_clean()]
    |
    | Allocate sk_buff
    | Copy/map packet from DMA ring buffer
    | Call netif_receive_skb()
    v
[netif_receive_skb()]
    |
    | XDP (eXpress Data Path) hook [optional]
    | tc (traffic control) ingress hook
    v
[__netif_receive_skb_core()]
    |
    | Deliver to packet_type handlers based on EtherType:
    | ip_rcv() for IPv4
    v
[ip_rcv()]
    |
    | Verify IP checksum
    | Call Netfilter hook: NF_INET_PRE_ROUTING
    | (iptables PREROUTING chain runs here)
    v
[ip_rcv_finish()]
    |
    | Routing decision: ip_route_input()
    | Is this for us or forward?
    |
    +-- For us -> ip_local_deliver()
    |
    +-- Forward -> ip_forward()
    v
[ip_local_deliver()]
    |
    | Call Netfilter hook: NF_INET_LOCAL_IN
    | (iptables INPUT chain runs here)
    v
[ip_local_deliver_finish()]
    |
    | Lookup protocol: inet_protos[proto]
    | For TCP: tcp_v4_rcv()
    v
[tcp_v4_rcv()]
    |
    | Verify TCP checksum
    | Lookup socket: __inet_lookup_skb()
    |   Search ehash (established) -> sock found?
    |   Search lhash2 (listening) -> passive open?
    |
    +-- Socket in ESTABLISHED -> tcp_rcv_established()
    |
    +-- Socket in other state  -> tcp_rcv_state_process()
    v
[tcp_rcv_established()]
    |
    | Fast path: update rcv_nxt, ack_seq
    | Copy data to socket receive buffer: sk_add_backlog()
    | Wake up waiting process: sk->sk_data_ready()
    v
[Application: read(fd, buf, len)]
    |
    | tcp_recvmsg()
    | Copy from socket buffer to user space
    v
[Application receives data]
```

### 11.2 Complete Send Path — From Application to NIC

```
[Application: write(fd, data, len)]
    |
    v
[tcp_sendmsg()]
    |
    | Lock socket
    | Segment data into MSS-sized chunks
    | Allocate sk_buff for each chunk
    | Copy data from user space into sk_buff
    | Add to sk->sk_write_queue
    v
[tcp_push()]
    |
    | Congestion control check: can we send?
    | (cwnd > 0 and send window > 0)
    v
[tcp_write_xmit()]
    |
    | Build TCP header: tcp_transmit_skb()
    | Set SEQ, ACK, window, flags, checksum
    v
[ip_queue_xmit()]
    |
    | Build IP header
    | Set src/dst IP, TTL, checksum
    | Call Netfilter hook: NF_INET_LOCAL_OUT
    | (iptables OUTPUT chain runs here)
    v
[ip_output()]
    |
    | Fragmentation if needed
    | Call Netfilter hook: NF_INET_POST_ROUTING
    | (iptables POSTROUTING chain runs here)
    v
[dev_queue_xmit()]
    |
    | Traffic control (tc) qdisc
    | Add Ethernet header (ARP lookup for dst MAC)
    | Hand to NIC driver: ndo_start_xmit()
    v
[NIC Driver: ndo_start_xmit()]
    |
    | Write packet to TX DMA ring buffer
    | Doorbell: notify NIC to send
    v
[NIC Hardware]
    |
    | Reads from DMA ring, puts bits on wire
    | Raises interrupt when done: free sk_buff
```

### 11.3 Netfilter Hooks — Where iptables Rules Run

```
                           LOCAL PROCESS
                               |   ^
                               |   |
                        OUTPUT |   | INPUT
                               v   |
                         [NF_INET_LOCAL_OUT]    [NF_INET_LOCAL_IN]
                               |                      ^
                               v                      |
NETWORK --> [NF_INET_PRE_ROUTING] --> [ROUTING] --> [Forward] --> [NF_INET_FORWARD] -->
                                                                                       |
                                                                          [NF_INET_POST_ROUTING] --> NETWORK
```

Each hook point is where **iptables chains** run:
- `PREROUTING`: DNAT, conntrack
- `INPUT`: filter incoming packets to this host
- `FORWARD`: filter forwarded packets (router mode)
- `OUTPUT`: filter outgoing packets from this host
- `POSTROUTING`: SNAT/MASQUERADE

### 11.4 Socket System Calls — The Full API

```
Server lifecycle:
  socket()     -> Create socket fd
  bind()       -> Attach to local address:port
  listen()     -> Mark as passive (listening), set backlog
  accept()     -> Block until connection arrives, get new fd
  read/write() -> Exchange data
  close()      -> Send FIN, release resources

Client lifecycle:
  socket()     -> Create socket fd
  connect()    -> 3-way handshake, blocks until ESTABLISHED
  read/write() -> Exchange data
  close()      -> Send FIN, release resources
```

**Socket file descriptor flow**:
```
socket() returns fd=3
    |
    | fd=3 -> struct file -> struct socket -> struct sock
    |                          (VFS layer)    (network layer)
    v
bind() attaches local addr to struct sock.sk_rcv_saddr, sk_num
listen() allocates backlog queues, adds to lhash2
accept() waits on accept_queue, returns new fd=4 for each client
```

### 11.5 Viewing Connection State in Linux

```bash
# Show all TCP connections with state
ss -tnp
# -t: TCP only
# -n: numeric (no DNS lookup)
# -p: show process

# Output example:
# State    Recv-Q  Send-Q   Local Address:Port   Peer Address:Port   Process
# ESTAB    0       0        192.168.1.2:22       192.168.1.1:54321   sshd,1234
# LISTEN   0       128      0.0.0.0:80           0.0.0.0:*           nginx,567
# TIME-WAIT 0      0        192.168.1.2:80       10.0.0.5:44444

# Show conntrack table
conntrack -L
# Output:
# tcp 6 ESTABLISHED src=10.0.0.1 dst=93.184.216.34 sport=54321 dport=80 ...

# Show listening sockets
ss -tlnp

# Socket statistics
ss -s

# Show TCP internals per connection
ss -tin   (includes RTT, cwnd, ssthresh, etc.)
```

### 11.6 Linux TCP Sysctl Parameters

```bash
# Key parameters affecting connection management

# SYN queue size
net.ipv4.tcp_max_syn_backlog = 4096

# Enable SYN cookies (defense against SYN flood)
net.ipv4.tcp_syncookies = 1

# TIME_WAIT reuse (allow reusing TIME_WAIT sockets for new connections)
net.ipv4.tcp_tw_reuse = 1

# FIN_WAIT_2 timeout
net.ipv4.tcp_fin_timeout = 60

# Keepalive parameters
net.ipv4.tcp_keepalive_time = 7200
net.ipv4.tcp_keepalive_intvl = 75
net.ipv4.tcp_keepalive_probes = 9

# Maximum number of orphaned (not attached to fd) TCP sockets
net.ipv4.tcp_max_orphans = 65536

# Local port range for ephemeral ports
net.ipv4.ip_local_port_range = 32768 60999

# Socket receive/send buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216   (min, default, max)
net.ipv4.tcp_wmem = 4096 65536 16777216
```

---

## 12. C Implementations

### 12.1 TCP Server — Complete with All Edge Cases

```c
/* tcp_server.c - Complete TCP server with state handling */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netinet/tcp.h>    /* TCP_NODELAY, TCP_KEEPIDLE, etc. */
#include <arpa/inet.h>
#include <fcntl.h>

#define PORT        8080
#define BACKLOG     128       /* listen() backlog: accept queue size */
#define BUFSIZE     4096

/* Make socket non-blocking */
static int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

/* Configure TCP options for production use */
static void configure_socket(int fd) {
    int optval = 1;

    /* SO_REUSEADDR: Allow binding to a port in TIME_WAIT state
     * (Essential for servers that restart quickly)
     * Without this, bind() fails with EADDRINUSE for ~60s after restart */
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    /* SO_REUSEPORT: Allow multiple sockets to bind to same port
     * (Enables multi-process/multi-thread servers without a single accept())
     * Each socket gets its own accept queue — kernel load-balances SYNs */
    setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &optval, sizeof(optval));

    /* TCP_NODELAY: Disable Nagle's algorithm
     * Nagle: hold small segments until previous segment ACK'd (reduces chattiness)
     * Disable for latency-sensitive apps (games, terminals, RPC)
     * Enable (default) for throughput-sensitive apps (file transfer) */
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &optval, sizeof(optval));

    /* SO_KEEPALIVE: Enable TCP keepalive probes */
    setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &optval, sizeof(optval));

    int keepidle = 60;    /* Start probing after 60s of idleness */
    int keepintvl = 10;   /* Probe every 10s */
    int keepcnt = 3;      /* Give up after 3 failed probes */
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE,  &keepidle,  sizeof(keepidle));
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
    setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT,   &keepcnt,   sizeof(keepcnt));

    /* Set receive and send buffer sizes
     * Larger buffers = better throughput for high-bandwidth connections
     * But: each connection consumes this memory */
    int rcvbuf = 256 * 1024;  /* 256KB receive buffer */
    int sndbuf = 256 * 1024;  /* 256KB send buffer */
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));
    setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
}

/* Handle one client connection */
static void handle_client(int client_fd, struct sockaddr_in *client_addr) {
    char client_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &client_addr->sin_addr, client_ip, sizeof(client_ip));
    uint16_t client_port = ntohs(client_addr->sin_port);

    printf("[+] Client connected: %s:%d\n", client_ip, client_port);

    char buf[BUFSIZE];
    ssize_t n;

    /* Read loop: handles partial reads (TCP is a stream protocol!) */
    while ((n = recv(client_fd, buf, sizeof(buf) - 1, 0)) > 0) {
        buf[n] = '\0';
        printf("[*] Received %zd bytes: %s\n", n, buf);

        /* Echo back */
        ssize_t sent = 0;
        while (sent < n) {
            /* Write loop: handles partial writes (kernel buffer may be full) */
            ssize_t w = send(client_fd, buf + sent, n - sent, 0);
            if (w == -1) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    /* Non-blocking: would block, try again */
                    continue;
                }
                perror("send");
                goto done;
            }
            sent += w;
        }
    }

    if (n == 0) {
        /* Peer closed connection (sent FIN) — clean EOF */
        printf("[-] Client %s:%d disconnected gracefully\n", client_ip, client_port);
    } else if (n == -1) {
        if (errno == ECONNRESET) {
            /* Peer sent RST — abortive close */
            printf("[-] Client %s:%d reset connection\n", client_ip, client_port);
        } else {
            perror("recv");
        }
    }

done:
    /* close() sends FIN, initiating graceful TCP teardown
     * Kernel handles the 4-way handshake and TIME_WAIT automatically */
    close(client_fd);
}

int main(void) {
    /* Ignore SIGPIPE: without this, writing to a closed connection
     * sends SIGPIPE and kills the process instead of returning -1/EPIPE */
    signal(SIGPIPE, SIG_IGN);

    /* Step 1: Create socket
     * AF_INET = IPv4
     * SOCK_STREAM = TCP (reliable, stream)
     * SOCK_CLOEXEC = close fd on exec() (prevent fd leak to child processes) */
    int listen_fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (listen_fd == -1) { perror("socket"); exit(1); }

    configure_socket(listen_fd);

    /* Step 2: Bind — associate socket with local address:port */
    struct sockaddr_in addr = {
        .sin_family      = AF_INET,
        .sin_port        = htons(PORT),      /* host-to-network byte order */
        .sin_addr.s_addr = INADDR_ANY,       /* 0.0.0.0: all interfaces */
    };
    if (bind(listen_fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        perror("bind");
        exit(1);
    }

    /* Step 3: Listen — mark socket as passive, set accept queue size
     * BACKLOG = max number of completed connections waiting for accept()
     * Connections beyond backlog: kernel silently drops SYNs (or SYN cookies) */
    if (listen(listen_fd, BACKLOG) == -1) {
        perror("listen");
        exit(1);
    }

    printf("[*] Listening on 0.0.0.0:%d\n", PORT);

    /* Step 4: Accept loop */
    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        /* accept() blocks until a connection arrives from accept queue
         * Returns new fd dedicated to THIS connection
         * listen_fd remains open and continues accepting new connections */
        int client_fd = accept(listen_fd,
                               (struct sockaddr *)&client_addr,
                               &client_len);
        if (client_fd == -1) {
            if (errno == EINTR) continue;      /* interrupted by signal, retry */
            perror("accept");
            continue;
        }

        /* Fork for simplicity; production uses thread pool or epoll */
        pid_t pid = fork();
        if (pid == 0) {
            /* Child process */
            close(listen_fd);                  /* child doesn't need listen fd */
            handle_client(client_fd, &client_addr);
            exit(0);
        } else {
            /* Parent process */
            close(client_fd);                  /* parent doesn't use this fd */
        }
    }

    close(listen_fd);
    return 0;
}
```

### 12.2 TCP Client — With Connection Timeout

```c
/* tcp_client.c - TCP client with timeout and proper error handling */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/select.h>

/* Connect with timeout using non-blocking connect + select() */
static int connect_with_timeout(int fd, const struct sockaddr *addr,
                                 socklen_t addrlen, int timeout_sec) {
    /* Make socket non-blocking */
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);

    int ret = connect(fd, addr, addrlen);
    if (ret == 0) {
        /* Immediately connected (unlikely, but happens on loopback) */
        goto restore_blocking;
    }

    if (errno != EINPROGRESS) {
        /* Real error (not "operation in progress") */
        return -1;
    }

    /* Wait for connect to complete using select() */
    fd_set wfds;
    FD_ZERO(&wfds);
    FD_SET(fd, &wfds);
    struct timeval tv = { .tv_sec = timeout_sec, .tv_usec = 0 };

    ret = select(fd + 1, NULL, &wfds, NULL, &tv);
    if (ret == 0) {
        errno = ETIMEDOUT;
        return -1;
    }
    if (ret == -1) return -1;

    /* Check if connect succeeded or failed */
    int error = 0;
    socklen_t errlen = sizeof(error);
    getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &errlen);
    if (error != 0) {
        errno = error;
        return -1;
    }

restore_blocking:
    /* Restore blocking mode */
    fcntl(fd, F_SETFL, flags);
    return 0;
}

int main(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd == -1) { perror("socket"); exit(1); }

    struct sockaddr_in server = {
        .sin_family      = AF_INET,
        .sin_port        = htons(8080),
        .sin_addr.s_addr = inet_addr("127.0.0.1"),
    };

    printf("[*] Connecting to 127.0.0.1:8080...\n");
    if (connect_with_timeout(fd, (struct sockaddr *)&server,
                              sizeof(server), 5) == -1) {
        perror("connect");
        exit(1);
    }
    printf("[+] Connected!\n");

    const char *msg = "Hello, server!\n";
    send(fd, msg, strlen(msg), 0);

    char buf[4096];
    ssize_t n = recv(fd, buf, sizeof(buf) - 1, 0);
    if (n > 0) {
        buf[n] = '\0';
        printf("[*] Server replied: %s", buf);
    }

    /* Graceful close: call close() -> kernel sends FIN
     * 4-way handshake happens automatically in the kernel */
    close(fd);
    printf("[-] Connection closed\n");
    return 0;
}
```

### 12.3 Examining TCP State via getsockopt()

```c
/* tcp_state.c - Read TCP connection internals */
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/tcp.h>

void print_tcp_info(int fd) {
    struct tcp_info info;
    socklen_t len = sizeof(info);

    if (getsockopt(fd, IPPROTO_TCP, TCP_INFO, &info, &len) == -1) {
        perror("getsockopt TCP_INFO");
        return;
    }

    /* TCP state names */
    const char *states[] = {
        "ESTABLISHED", "SYN_SENT", "SYN_RECV",
        "FIN_WAIT1", "FIN_WAIT2", "TIME_WAIT",
        "CLOSE", "CLOSE_WAIT", "LAST_ACK",
        "LISTEN", "CLOSING", "NEW_SYN_RECV"
    };

    printf("TCP State:        %s\n", states[info.tcpi_state]);
    printf("RTT:              %u us\n",  info.tcpi_rtt);
    printf("RTT variance:     %u us\n",  info.tcpi_rttvar);
    printf("Send window:      %u\n",     info.tcpi_snd_wnd);
    printf("Recv window:      %u\n",     info.tcpi_rcv_space);
    printf("Congestion window:%u\n",     info.tcpi_snd_cwnd);
    printf("SSThreshold:      %u\n",     info.tcpi_snd_ssthresh);
    printf("Retransmits:      %u\n",     info.tcpi_retransmits);
    printf("Unacked segments: %u\n",     info.tcpi_unacked);
    printf("Lost segments:    %u\n",     info.tcpi_lost);
    printf("Retransmitted:    %u\n",     info.tcpi_retrans);
    printf("MSS:              %u\n",     info.tcpi_snd_mss);
    printf("Recv MSS:         %u\n",     info.tcpi_rcv_mss);
}
```

### 12.4 Raw Socket — Reading IP/TCP Headers Directly

```c
/* raw_capture.c - Read packets using raw socket (requires root) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

void print_tcp_flags(struct tcphdr *tcp) {
    printf("Flags: ");
    if (tcp->syn) printf("SYN ");
    if (tcp->ack) printf("ACK ");
    if (tcp->fin) printf("FIN ");
    if (tcp->rst) printf("RST ");
    if (tcp->psh) printf("PSH ");
    if (tcp->urg) printf("URG ");
    if (tcp->ece) printf("ECE ");
    if (tcp->cwr) printf("CWR ");
    printf("\n");
}

int main(void) {
    /* IPPROTO_TCP: only receive TCP packets
     * Could use ETH_P_ALL (with AF_PACKET) to get ALL packets */
    int raw_fd = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (raw_fd == -1) {
        perror("socket (need root!)");
        exit(1);
    }

    /* Request that IP header is included in received data */
    int one = 1;
    setsockopt(raw_fd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));

    unsigned char buf[65536];
    while (1) {
        ssize_t n = recvfrom(raw_fd, buf, sizeof(buf), 0, NULL, NULL);
        if (n < 0) { perror("recvfrom"); break; }

        /* Parse IP header */
        struct iphdr *iph = (struct iphdr *)buf;
        int ip_hdr_len = iph->ihl * 4;   /* ihl = header length in 32-bit words */

        if (iph->protocol != IPPROTO_TCP) continue;

        /* Parse TCP header (immediately after IP header) */
        struct tcphdr *tcp = (struct tcphdr *)(buf + ip_hdr_len);

        char src_ip[INET_ADDRSTRLEN], dst_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &iph->saddr, src_ip, sizeof(src_ip));
        inet_ntop(AF_INET, &iph->daddr, dst_ip, sizeof(dst_ip));

        printf("TCP: %s:%d -> %s:%d | SEQ=%u ACK=%u | ",
               src_ip, ntohs(tcp->source),
               dst_ip, ntohs(tcp->dest),
               ntohl(tcp->seq),
               ntohl(tcp->ack_seq));
        print_tcp_flags(tcp);
    }

    close(raw_fd);
    return 0;
}
```

### 12.5 epoll-Based Server — Production-Grade Event Loop

```c
/* epoll_server.c - Non-blocking server with epoll */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define MAX_EVENTS  1024
#define PORT        8080
#define BACKLOG     512

static void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main(void) {
    /* Create listening socket */
    int lfd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    int one = 1;
    setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    setsockopt(lfd, SOL_SOCKET, SO_REUSEPORT, &one, sizeof(one));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(PORT),
        .sin_addr.s_addr = INADDR_ANY
    };
    bind(lfd, (struct sockaddr *)&addr, sizeof(addr));
    listen(lfd, BACKLOG);

    /* Create epoll instance
     * epoll is O(1) for monitoring N fds (unlike select/poll which are O(N)) */
    int epfd = epoll_create1(EPOLL_CLOEXEC);

    /* Register listening socket with epoll */
    struct epoll_event ev;
    ev.events = EPOLLIN;          /* interested in read events */
    ev.data.fd = lfd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, lfd, &ev);

    printf("[*] epoll server listening on port %d\n", PORT);

    struct epoll_event events[MAX_EVENTS];
    char buf[4096];

    while (1) {
        /* Wait for events: -1 = block indefinitely */
        int nready = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (int i = 0; i < nready; i++) {
            int fd = events[i].data.fd;

            if (fd == lfd) {
                /* New connection on listening socket */
                struct sockaddr_in caddr;
                socklen_t clen = sizeof(caddr);

                /* Accept all pending connections (EPOLLET edge-trigger would need loop) */
                int cfd = accept4(lfd, (struct sockaddr *)&caddr, &clen,
                                  SOCK_NONBLOCK | SOCK_CLOEXEC);
                if (cfd == -1) continue;

                /* Register new connection with epoll
                 * EPOLLET = edge-triggered (only notified on state CHANGE)
                 * Level-triggered (default): notified as long as data available */
                ev.events = EPOLLIN | EPOLLET | EPOLLRDHUP;
                ev.data.fd = cfd;
                epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &ev);

                char ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &caddr.sin_addr, ip, sizeof(ip));
                printf("[+] Accepted from %s:%d (fd=%d)\n",
                       ip, ntohs(caddr.sin_port), cfd);

            } else if (events[i].events & (EPOLLRDHUP | EPOLLHUP | EPOLLERR)) {
                /* Peer closed connection or error */
                printf("[-] fd=%d closed/error\n", fd);
                epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                close(fd);

            } else if (events[i].events & EPOLLIN) {
                /* Data available to read */
                ssize_t n;
                while ((n = recv(fd, buf, sizeof(buf), 0)) > 0) {
                    /* Echo back */
                    send(fd, buf, n, 0);
                }
                if (n == 0) {
                    /* EOF: peer sent FIN */
                    printf("[-] fd=%d EOF\n", fd);
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);   /* sends our FIN */
                } else if (n == -1 && errno != EAGAIN) {
                    perror("recv");
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);
                }
            }
        }
    }

    close(epfd);
    close(lfd);
    return 0;
}
```

---

## 13. Rust Integration

### 13.1 Architecture — How Rust Uses Linux Network Primitives

```
Rust Application
      |
      |  uses std::net or tokio or mio
      v
+-------------------+
|  Rust std::net    |  Safe wrapper over libc calls
|  (or tokio/mio)   |
+-------------------+
      |
      |  via libc crate or direct syscalls (via std)
      v
+-------------------+
|  libc / glibc     |  C library
+-------------------+
      |
      |  syscall instruction (sysenter / syscall)
      v
+-------------------+
|  Linux Kernel     |  socket(), connect(), send(), recv()...
|  Network Stack    |
+-------------------+
      |
      v
[Hardware / NIC]
```

### 13.2 Rust std::net — Synchronous TCP

```rust
// tcp_server_std.rs - Synchronous TCP server in Rust
use std::net::{TcpListener, TcpStream};
use std::io::{Read, Write};
use std::thread;

fn handle_client(mut stream: TcpStream) {
    // TcpStream wraps the fd; Drop impl calls close() automatically
    let peer = stream.peer_addr().unwrap();
    println!("[+] Connected: {}", peer);

    let mut buf = [0u8; 4096];
    loop {
        match stream.read(&mut buf) {
            Ok(0) => {
                // n=0 means EOF: peer sent FIN
                println!("[-] {} disconnected", peer);
                break;
            }
            Ok(n) => {
                println!("[*] {} bytes from {}", n, peer);
                // Echo back; write_all handles partial writes internally
                if stream.write_all(&buf[..n]).is_err() {
                    break;
                }
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                break;
            }
        }
    }
    // TcpStream dropped here -> close() called -> FIN sent
}

fn main() -> std::io::Result<()> {
    let listener = TcpListener::bind("0.0.0.0:8080")?;
    println!("[*] Listening on 0.0.0.0:8080");

    for stream in listener.incoming() {
        match stream {
            Ok(s) => {
                thread::spawn(move || handle_client(s));
            }
            Err(e) => eprintln!("Accept error: {}", e),
        }
    }
    Ok(())
}
```

### 13.3 Tokio — Async TCP with Epoll Under the Hood

Tokio uses **epoll** (Linux), **kqueue** (macOS), or **IOCP** (Windows) under the hood. The `async/await` abstraction maps to non-blocking I/O + event loop.

```rust
// tcp_server_tokio.rs
// Cargo.toml: tokio = { version = "1", features = ["full"] }

use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

async fn handle_client(mut stream: TcpStream) {
    let peer = stream.peer_addr().unwrap();
    println!("[+] Connected: {}", peer);

    let mut buf = vec![0u8; 4096];
    loop {
        match stream.read(&mut buf).await {
            Ok(0) => {
                // EOF — peer sent FIN
                println!("[-] {} disconnected", peer);
                break;
            }
            Ok(n) => {
                // Echo back
                if stream.write_all(&buf[..n]).await.is_err() {
                    break;
                }
            }
            Err(e) => {
                eprintln!("Error from {}: {}", peer, e);
                break;
            }
        }
    }
    // TcpStream dropped -> close() -> FIN
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind("0.0.0.0:8080").await?;
    println!("[*] Tokio server on 0.0.0.0:8080");

    loop {
        let (stream, addr) = listener.accept().await?;
        println!("[*] Accepted from {}", addr);
        // Spawn a lightweight async task (not a thread)
        tokio::spawn(async move {
            handle_client(stream).await;
        });
    }
}
```

**How tokio maps to epoll**:
```
tokio::spawn(async { stream.read().await })
       |
       | Registers fd with epoll (EPOLLIN)
       | Suspends the future (no OS thread blocked)
       v
[epoll_wait() in tokio runtime thread]
       |
       | epoll notifies: fd readable
       v
[Wake the future, resume execution]
       |
       | stream.read() returns with data
       v
[Continue async function]
```

### 13.4 Setting Socket Options in Rust via libc

```rust
// socket_options.rs
// Cargo.toml: libc = "0.2"

use std::net::TcpStream;
use std::os::unix::io::AsRawFd;
use libc::{c_int, setsockopt, IPPROTO_TCP, SOL_SOCKET, SO_KEEPALIVE};
use libc::{TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT, TCP_NODELAY};

fn set_tcp_options(stream: &TcpStream) -> std::io::Result<()> {
    let fd = stream.as_raw_fd();

    unsafe {
        // Helper closure for setsockopt
        let setopt = |level: c_int, optname: c_int, val: c_int| -> bool {
            setsockopt(
                fd,
                level,
                optname,
                &val as *const c_int as *const libc::c_void,
                std::mem::size_of::<c_int>() as libc::socklen_t,
            ) == 0
        };

        // Enable TCP keepalive
        setopt(SOL_SOCKET, SO_KEEPALIVE, 1);

        // Keepalive parameters
        setopt(IPPROTO_TCP, TCP_KEEPIDLE, 60);    // 60s before first probe
        setopt(IPPROTO_TCP, TCP_KEEPINTVL, 10);   // 10s between probes
        setopt(IPPROTO_TCP, TCP_KEEPCNT, 3);      // 3 probes max

        // Disable Nagle's algorithm for low latency
        setopt(IPPROTO_TCP, TCP_NODELAY, 1);
    }

    Ok(())
}

fn main() -> std::io::Result<()> {
    let stream = TcpStream::connect("127.0.0.1:8080")?;
    set_tcp_options(&stream)?;
    println!("[+] Socket options configured");
    // ... use stream
    Ok(())
}
```

### 13.5 Reading TCP_INFO in Rust

```rust
// tcp_info.rs - Reading kernel TCP state from Rust
use std::net::TcpStream;
use std::os::unix::io::AsRawFd;

// Mirror of Linux's struct tcp_info
// This must match the kernel's ABI exactly!
#[repr(C)]
#[derive(Default, Debug)]
struct TcpInfo {
    tcpi_state: u8,
    tcpi_ca_state: u8,
    tcpi_retransmits: u8,
    tcpi_probes: u8,
    tcpi_backoff: u8,
    tcpi_options: u8,
    tcpi_snd_wscale: u8,   // actually 4:4 bitfield in kernel
    tcpi_delivery_rate_app_limited: u8,
    tcpi_rto: u32,
    tcpi_ato: u32,
    tcpi_snd_mss: u32,
    tcpi_rcv_mss: u32,
    tcpi_unacked: u32,
    tcpi_sacked: u32,
    tcpi_lost: u32,
    tcpi_retrans: u32,
    tcpi_fackets: u32,
    tcpi_last_data_sent: u32,
    tcpi_last_ack_sent: u32,
    tcpi_last_data_recv: u32,
    tcpi_last_ack_recv: u32,
    tcpi_pmtu: u32,
    tcpi_rcv_ssthresh: u32,
    tcpi_rtt: u32,          // Smoothed RTT in microseconds
    tcpi_rttvar: u32,       // RTT variance in microseconds
    tcpi_snd_ssthresh: u32,
    tcpi_snd_cwnd: u32,
    tcpi_advmss: u32,
    tcpi_reordering: u32,
    // ... more fields in newer kernels
}

fn get_tcp_info(stream: &TcpStream) -> Option<TcpInfo> {
    let fd = stream.as_raw_fd();
    let mut info = TcpInfo::default();
    let mut len = std::mem::size_of::<TcpInfo>() as libc::socklen_t;

    let ret = unsafe {
        libc::getsockopt(
            fd,
            libc::IPPROTO_TCP,
            libc::TCP_INFO,
            &mut info as *mut TcpInfo as *mut libc::c_void,
            &mut len,
        )
    };

    if ret == 0 { Some(info) } else { None }
}

fn main() -> std::io::Result<()> {
    let stream = TcpStream::connect("93.184.216.34:80")?;

    if let Some(info) = get_tcp_info(&stream) {
        let states = ["ESTABLISHED","SYN_SENT","SYN_RECV","FIN_WAIT1",
                      "FIN_WAIT2","TIME_WAIT","CLOSE","CLOSE_WAIT",
                      "LAST_ACK","LISTEN","CLOSING"];
        println!("State:  {}", states.get(info.tcpi_state as usize).unwrap_or(&"UNKNOWN"));
        println!("RTT:    {} us", info.tcpi_rtt);
        println!("CWND:   {}", info.tcpi_snd_cwnd);
        println!("MSS:    {}", info.tcpi_snd_mss);
        println!("Lost:   {}", info.tcpi_lost);
    }

    Ok(())
}
```

### 13.6 Using the socket2 Crate — Idiomatic Rust Socket Control

```rust
// Cargo.toml: socket2 = { version = "0.5", features = ["all"] }
use socket2::{Socket, Domain, Type, Protocol, TcpKeepalive};
use std::time::Duration;
use std::net::SocketAddr;

fn create_production_socket(addr: &str) -> std::io::Result<Socket> {
    let socket = Socket::new(Domain::IPV4, Type::STREAM, Some(Protocol::TCP))?;

    // SO_REUSEADDR
    socket.set_reuse_address(true)?;

    // SO_REUSEPORT
    socket.set_reuse_port(true)?;

    // TCP_NODELAY
    socket.set_nodelay(true)?;

    // TCP Keepalive
    let keepalive = TcpKeepalive::new()
        .with_time(Duration::from_secs(60))
        .with_interval(Duration::from_secs(10))
        .with_retries(3);
    socket.set_tcp_keepalive(&keepalive)?;

    // Set receive/send buffer sizes
    socket.set_recv_buffer_size(256 * 1024)?;
    socket.set_send_buffer_size(256 * 1024)?;

    // Bind
    let bind_addr: SocketAddr = addr.parse().unwrap();
    socket.bind(&bind_addr.into())?;

    // Listen
    socket.listen(512)?;

    Ok(socket)
}
```

### 13.7 Rust Raw Socket — Parsing IP/TCP Headers

```rust
// raw_socket.rs - Parsing packets at IP level in Rust
// Must run as root

use std::net::Ipv4Addr;

fn main() -> std::io::Result<()> {
    // Create raw socket (requires root or CAP_NET_RAW capability)
    let socket = unsafe {
        libc::socket(libc::AF_INET, libc::SOCK_RAW, libc::IPPROTO_TCP)
    };
    if socket == -1 {
        eprintln!("Need root/CAP_NET_RAW");
        std::process::exit(1);
    }

    let mut buf = vec![0u8; 65536];

    loop {
        let n = unsafe {
            libc::recvfrom(socket, buf.as_mut_ptr() as *mut libc::c_void,
                           buf.len(), 0,
                           std::ptr::null_mut(), std::ptr::null_mut())
        };
        if n < 0 { break; }

        let packet = &buf[..n as usize];

        // Parse IP header (first 20+ bytes)
        if packet.len() < 20 { continue; }
        let ihl = (packet[0] & 0x0F) as usize * 4;  // IP header length
        let protocol = packet[9];

        if protocol != 6 { continue; }  // Skip non-TCP

        let src_ip = Ipv4Addr::new(packet[12], packet[13], packet[14], packet[15]);
        let dst_ip = Ipv4Addr::new(packet[16], packet[17], packet[18], packet[19]);

        // Parse TCP header (starts after IP header)
        if packet.len() < ihl + 20 { continue; }
        let tcp = &packet[ihl..];

        let src_port = u16::from_be_bytes([tcp[0], tcp[1]]);
        let dst_port = u16::from_be_bytes([tcp[2], tcp[3]]);
        let seq_num  = u32::from_be_bytes([tcp[4], tcp[5], tcp[6], tcp[7]]);
        let ack_num  = u32::from_be_bytes([tcp[8], tcp[9], tcp[10], tcp[11]]);
        let flags    = tcp[13];  // Control bits byte

        let syn = (flags & 0x02) != 0;
        let ack = (flags & 0x10) != 0;
        let fin = (flags & 0x01) != 0;
        let rst = (flags & 0x04) != 0;
        let psh = (flags & 0x08) != 0;

        print!("TCP {}:{} -> {}:{} | SEQ={} ACK={} | Flags:",
               src_ip, src_port, dst_ip, dst_port, seq_num, ack_num);
        if syn { print!(" SYN"); }
        if ack { print!(" ACK"); }
        if fin { print!(" FIN"); }
        if rst { print!(" RST"); }
        if psh { print!(" PSH"); }
        println!();
    }

    Ok(())
}
```

---

## 14. Mental Models

### 14.1 The State Machine Mental Model

Every protocol IS a state machine. When you read protocol specs, always extract:
1. What are all the possible states?
2. What events cause state transitions?
3. What actions are performed during transitions?
4. What states can I be in when I receive each message type?

This is how you reason about protocols without memorizing rules — you derive correct behavior from the state machine.

### 14.2 The Buffer Mental Model

Network programming is about **buffers moving through stages**:

```
App write buffer -> Kernel socket send buffer -> NIC TX ring -> Wire
Wire -> NIC RX ring -> Kernel socket recv buffer -> App read buffer
```

Partial reads/writes happen because these buffers are bounded and can fill up or have less data than expected. Always loop your reads and writes.

### 14.3 The Ownership Mental Model (Rust/C)

- In C: You must track who owns each `sk_buff`, when to free it, and who closes file descriptors.
- In Rust: `TcpStream`'s `Drop` impl closes the fd. Ownership rules prevent double-close.

```
Rust ownership maps to network connection semantics:
  - One owner = one active connection handler
  - Clone = shared reference (for reading only, use Arc<Mutex<>>)
  - Move into thread = transfer responsibility for closing
```

### 14.4 The Layers Are Leaky Mental Model

Despite strict layering, layers DO communicate side-band information:
- TCP informs IP about MSS (affects IP fragmentation decisions)
- ICMP Type 3 Code 4 messages (from IP layer) flow UP to TCP to adjust MSS
- ECN bits are set by routers (IP layer) and interpreted by TCP (transport layer)
- TCP timestamps are used by NIC offload engines (link layer)

Real protocols are not perfectly isolated layers — they cooperate.

### 14.5 Decision Tree: What Happens When a Packet Arrives?

```
Packet arrives at NIC
       |
       v
   Is checksum valid?
   NO  -> discard silently
   YES -> continue
       |
       v
   Is destination IP mine?
   NO  -> am I a router? YES -> forward; NO -> discard
   YES -> continue
       |
       v
   What protocol?
   ICMP -> handle ping/error
   UDP  -> find socket by dst_port
         -> socket found? deliver to recv queue
         -> not found? send ICMP port unreachable
   TCP  -> check flags:
           SYN only (no ACK)?
             -> Is port LISTENING? -> SYN queue entry + send SYN-ACK
             -> Not listening? -> send RST
           Has ACK?
             -> Find ESTABLISHED socket by 5-tuple
             -> found: process as data/ACK
             -> not found: send RST (half-open)
           FIN?
             -> Notify app of EOF
             -> Transition to CLOSE_WAIT / FIN_WAIT_2
           RST?
             -> Immediately destroy connection
             -> Wake app with ECONNRESET
```

### 14.6 Cognitive Framework: Four Questions for Every Protocol

When studying any protocol, answer these four questions:

```
1. INITIALIZATION
   What state does each party start in?
   What messages are exchanged to establish shared state?
   What parameters are negotiated?

2. STEADY STATE
   How is data transferred?
   How is ordering guaranteed?
   How is flow controlled?

3. ERROR HANDLING
   What happens when a message is lost?
   What happens when a message is corrupted?
   What happens when a party crashes?

4. TERMINATION
   How does each party signal "I'm done"?
   How is confirmation given?
   What cleanup is needed?
```

Apply these to TCP, TLS, HTTP/2, QUIC, DNS, or any protocol and you will understand it completely.

---

## Appendix A: Quick Reference — TCP State Transitions

```
Event         | Current State    | Action              | New State
---------------------------------------------------------------------------
passive open  | CLOSED           | create socket       | LISTEN
active open   | CLOSED           | send SYN            | SYN_SENT
recv SYN      | LISTEN           | send SYN-ACK        | SYN_RCVD
recv SYN-ACK  | SYN_SENT         | send ACK            | ESTABLISHED
recv ACK      | SYN_RCVD         | -                   | ESTABLISHED
close()       | ESTABLISHED      | send FIN            | FIN_WAIT_1
recv FIN      | ESTABLISHED      | send ACK            | CLOSE_WAIT
close()       | CLOSE_WAIT       | send FIN            | LAST_ACK
recv ACK      | FIN_WAIT_1       | -                   | FIN_WAIT_2
recv FIN      | FIN_WAIT_2       | send ACK            | TIME_WAIT
recv FIN      | FIN_WAIT_1       | send ACK            | CLOSING
recv ACK      | CLOSING          | -                   | TIME_WAIT
recv ACK      | LAST_ACK         | -                   | CLOSED
2MSL timeout  | TIME_WAIT        | -                   | CLOSED
recv RST      | any              | -                   | CLOSED
```

## Appendix B: Port and Protocol Numbers

```
Protocol  | Number | Notes
-------------------------------
ICMP      | 1      |
TCP       | 6      |
UDP       | 17     |
GRE       | 47     | VPN tunneling
ESP       | 50     | IPsec
AH        | 51     | IPsec
OSPF      | 89     |
SCTP      | 132    |
```

## Appendix C: Useful Commands for Observing All of This

```bash
# Watch TCP state machine live
watch -n1 'ss -tn'

# Capture packets and decode flags
tcpdump -i any -n 'tcp port 8080' -S

# Show SYN queue depth for port 80
ss -ltn 'sport = :80'
# Recv-Q = current SYN queue size
# Send-Q = backlog (max accept queue size)

# Watch conntrack table
watch -n1 'conntrack -L --proto tcp 2>/dev/null | grep ESTAB | wc -l'

# Monitor TCP retransmits
watch -n1 'netstat -s | grep retransmit'

# View kernel TCP parameters
sysctl -a | grep tcp

# Trace TCP events with BPF (requires bcc tools)
tcplife    # shows connection lifetimes
tcpretrans # shows retransmission events
tcpconnect # shows outgoing connection attempts
tcpaccept  # shows incoming connection acceptances

# strace a network call to see actual syscalls
strace -e trace=network curl -s http://example.com
```

---

*This guide covers the complete lifecycle of network connections from hardware interrupt to application — the same mental model that kernel network engineers and performance experts use daily. The path from here: implement a mini-TCP state machine, then study TCP congestion control algorithms (Reno, CUBIC, BBR), then Linux's NAPI and XDP for high-performance packet processing.*
