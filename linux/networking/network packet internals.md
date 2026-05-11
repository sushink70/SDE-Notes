# Network Packet / Frame / Segment Internals
## A Complete, In-Depth Guide: Reading, Writing, Processing

---

## Table of Contents

1. [The Mental Model — What Is Being Transmitted?](#1-the-mental-model)
2. [The OSI/TCP-IP Layering and Encapsulation](#2-osi-tcpip-layering)
3. [How Bits Travel — Physical Reality](#3-how-bits-travel)
4. [Real Protocol Wire Formats (ASCII Diagrams)](#4-real-protocol-wire-formats)
   - Ethernet II Frame
   - ARP
   - IPv4
   - IPv6
   - ICMP
   - UDP
   - TCP
5. [Memory Layout: Endianness, Alignment, Padding](#5-memory-layout)
6. [How the Transmitter WRITES a Packet](#6-how-transmitter-writes)
7. [How the NIC Sends — DMA, Ring Buffers](#7-nic-dma-ring-buffers)
8. [How the NIC Receives — NAPI, Interrupts](#8-nic-receive-path)
9. [How the Receiver READS a Packet](#9-how-receiver-reads)
10. [Linux Kernel Network Stack Deep Dive](#10-linux-kernel-network-stack)
    - sk_buff structure
    - netif_receive_skb
    - protocol handlers
    - tc (traffic control)
    - netfilter/iptables hooks
11. [Packet Processing Decisions](#11-packet-processing-decisions)
    - Accept/Deliver
    - Drop
    - Ignore
    - Forward/Route
    - Redirect
    - Rate-limit
    - NAT/Rewrite
12. [Implementing in C](#12-c-implementation)
13. [Implementing in Rust](#13-rust-implementation)
14. [Implementing in Go](#14-go-implementation)
15. [Checksums — Theory and Implementation](#15-checksums)
16. [Raw Sockets and Packet Sockets (Linux)](#16-raw-sockets)
17. [AF_XDP, eBPF/XDP Fast Path](#17-ebpf-xdp)
18. [DPDK and Kernel Bypass](#18-dpdk)
19. [Common Bugs and Pitfalls](#19-common-bugs)
20. [Mental Models Summary](#20-mental-models)

---

## 1. The Mental Model

Before reading code, internalize this truth:

> **A packet is just a contiguous sequence of bytes in memory. Every field is defined by its byte offset and byte length from the start of the buffer. The "protocol" is the agreed-upon interpretation of those bytes.**

There is no magic. The NIC receives bits, assembles them into bytes, and DMAs them into a kernel memory buffer. The kernel then hands a pointer and a length to protocol handlers that each read their slice of those bytes by known offsets.

```
Physical wire:  0 1 1 0 1 0 0 1 0 1 1 0 ...  (raw bits, serially clocked)
                 \_______byte 0_______/  \___...
NIC assembles:  [0x69][0x6A][0x00][0x45]...    (bytes in DMA buffer)
CPU sees:       uint8_t *buf = dma_addr;        (pointer to that buffer)
Protocol:       eth_hdr  = (struct ethhdr *)buf;
                ip_hdr   = (struct iphdr  *)(buf + 14);
                tcp_hdr  = (struct tcphdr *)(buf + 14 + ip_hdr->ihl*4);
```

The transmit path is the mirror: fill a buffer byte by byte per the protocol spec, hand the pointer+length to the NIC, the NIC DMAs it out and serializes bits onto the wire.

---

## 2. OSI/TCP-IP Layering and Encapsulation

### TCP/IP (Practical) Model

```
Application Layer        HTTP, DNS, TLS, SMTP, ...
Transport Layer          TCP, UDP, SCTP, QUIC
Network Layer            IPv4, IPv6, ICMP, ARP
Link Layer               Ethernet, Wi-Fi (802.11), PPP
Physical Layer           Electrical/optical signals
```

### Encapsulation on TX (Transmit)

When an application sends "Hello", this is what happens:

```
Application data:
  [H][e][l][l][o]

TCP adds header:
  [TCP HDR 20B][H][e][l][l][o]
   src_port dst_port seq ack flags window checksum urgent

IP adds header:
  [IP HDR 20B][TCP HDR 20B][H][e][l][l][o]
   version ihl dscp len id flags offset ttl proto cksum src dst

Ethernet adds header+trailer:
  [ETH DST 6B][ETH SRC 6B][ETHERTYPE 2B][IP HDR][TCP HDR][DATA][FCS 4B]

Wire (bits, MSB first per byte):
  01101001 01101010 00000000 01000101 ...
```

### De-encapsulation on RX (Receive)

The receiver strips layers from outside in:
1. Ethernet driver validates FCS, strips L2 header
2. `net_rx_action` → `ip_rcv()` validates IP, strips L3 header
3. `tcp_v4_rcv()` validates TCP, strips L4 header
4. Data arrives in socket receive buffer, `read()` syscall returns it

---

## 3. How Bits Travel — Physical Reality

### Serial Transmission

All physical media are fundamentally **serial** — one bit at a time:

```
Ethernet (1000BASE-T): bits clocked at 1 Gbps per pair
                       NIC PHY chip serializes/deserializes
                       Line encoding: 4D-PAM5 for 1GbE,
                                      PAP-4 for 10GbE

Byte boundary:  after 8 clocks → 1 byte assembled in shift register
Frame boundary: detected via preamble + SFD (Start Frame Delimiter)
```

### Ethernet Preamble and SFD

Every Ethernet frame is preceded by:
```
Preamble (7 bytes):  10101010 10101010 10101010 10101010
                     10101010 10101010 10101010
SFD      (1 byte):   10101011   ← last two bits 11 signal frame start
```

The PHY/MAC hardware detects the SFD and begins assembling the frame. Software **never sees** the preamble — the NIC strips it before DMA.

### NIC Hardware Pipeline

```
Wire
 │
 ▼
Analog Front End (AFE) — amplify, filter, equalize signal
 │
 ▼
Serializer/Deserializer (SerDes) — recover clock, deserialize bits
 │
 ▼
MAC (Media Access Controller) — frame delineation, FCS check
 │
 ▼
Receive Descriptor Ring — DMA into pre-allocated kernel memory
 │
 ▼
Interrupt / NAPI poll — CPU wakes up and processes
```

### Bit Order Within a Byte

**Network byte order** (big-endian) applies to **multi-byte fields**, not individual bytes. Within a byte, transmission order is:
- Ethernet: LSB first (least significant bit first) per 802.3
- The NIC handles this transparently; software always sees bytes in correct order

---

## 4. Real Protocol Wire Formats (ASCII Diagrams)

Diagrams use bit numbering: bit 0 = MSB (most significant bit) on the left.
Each row = 32 bits (4 bytes). All multi-byte integers are in **network byte order (big-endian)**.

---

### 4.1 Ethernet II Frame

```
Bit  0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Destination MAC Address                     |
    +                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |     (cont'd, 6 bytes total)   |      Source MAC Address        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
    |            (cont'd, 6 bytes total)            | EtherType/Len |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                     Payload (46-1500 bytes)                   |
    ~                        (variable)                             ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |               Frame Check Sequence (FCS) 4 bytes              |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Byte offsets:
  0-5:   Destination MAC (6 bytes)
  6-11:  Source MAC (6 bytes)
  12-13: EtherType (2 bytes)
         0x0800 = IPv4
         0x0806 = ARP
         0x86DD = IPv6
         0x8100 = 802.1Q VLAN tag
  14-N:  Payload
  N+1..N+4: FCS (CRC-32) — stripped by NIC before DMA in most cases

Total frame size: 64 bytes minimum (with FCS), 1518 bytes maximum (standard)
Jumbo frames: up to 9000 bytes (non-standard, negotiated)
```

### 4.2 ARP (Address Resolution Protocol) — RFC 826

Sent inside Ethernet payload (EtherType 0x0806):
```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Hardware Type         |         Protocol Type         |
    |          (HTYPE)              |          (PTYPE)              |
    |  0x0001 = Ethernet            |  0x0800 = IPv4                |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |   HW Addr Len |  Proto Addr   |           Operation           |
    |   (HLEN)=6    |  Len(PLEN)=4  |  1=Request  2=Reply          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                   Sender Hardware Address                     |
    +                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |       (SHA, 6 bytes)          |    Sender Protocol Address    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |   Sender Protocol Addr (cont) |   Target Hardware Address     |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               +
    |                (THA, 6 bytes total, 0 in request)             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                   Target Protocol Address                     |
    |                   (TPA, 4 bytes = target IPv4)                |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Total ARP payload: 28 bytes for Ethernet/IPv4 ARP
```

### 4.3 IPv4 Header — RFC 791

```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version|  IHL  |     DSCP  |ECN|         Total Length          |
    | (4)   | (4b)  |   (6b)    |(2b|           (16 bits)           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Identification        |Flags|      Fragment Offset     |
    |           (16 bits)           |(3b) |       (13 bits)          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Time to Live |    Protocol   |         Header Checksum       |
    |    (8 bits)   |    (8 bits)   |           (16 bits)           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Source Address                          |
    |                         (32 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Destination Address                        |
    |                         (32 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options (if IHL > 5)                       |
    ~                  (0-40 bytes, padded to 4B boundary)          ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Payload                               |
    ~                         (varies)                              ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Field details:
  Version (4b):         Always 4 for IPv4
  IHL     (4b):         Header length in 32-bit words. Minimum 5 = 20 bytes.
                        Actual header size = IHL * 4 bytes
  DSCP    (6b):         Differentiated Services (QoS marking)
  ECN     (2b):         Explicit Congestion Notification
  Total Length (16b):  Total datagram size including header, in bytes
  ID      (16b):        Fragment reassembly identifier
  Flags   (3b):         bit0=reserved(0), bit1=DF(Don't Fragment), bit2=MF(More Fragments)
  Fragment Offset(13b): Offset of this fragment in 8-byte units
  TTL     (8b):         Decremented by each router; packet dropped at 0
  Protocol(8b):         6=TCP, 17=UDP, 1=ICMP, 89=OSPF, 132=SCTP
  Checksum(16b):        One's complement sum of header only (NOT payload)
  Src/Dst (32b each):  IP addresses in network byte order

Payload offset = ethernet_header(14) + IHL*4
```

### 4.4 IPv6 Header — RFC 8200

```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version| Traffic Class |           Flow Label                  |
    | (4b)  |    (8b)       |           (20 bits)                   |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Payload Length        |  Next Header  |   Hop Limit   |
    |           (16 bits)           |    (8 bits)   |   (8 bits)    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                                                               +
    |                                                               |
    +                    Source Address (128 bits)                  +
    |                                                               |
    +                                                               +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                                                               +
    |                                                               |
    +                 Destination Address (128 bits)                +
    |                                                               |
    +                                                               +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Fixed header = 40 bytes. No checksum (unlike IPv4).
Next Header field chains extension headers (like options) and finally the
upper layer protocol: 6=TCP, 17=UDP, 58=ICMPv6, 43=Routing, 44=Fragment
```

### 4.5 ICMP — RFC 792

```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |      Type     |      Code     |            Checksum           |
    |    (8 bits)   |    (8 bits)   |           (16 bits)           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Rest of Header (varies by Type)            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Data (varies)                         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Echo Request (ping) Type=8 Code=0:
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |     Type=8    |    Code=0     |            Checksum           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |          Identifier           |        Sequence Number        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Data (echo payload)                   |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Common Types:
  0  = Echo Reply
  3  = Destination Unreachable (Code 0-15 describes reason)
  8  = Echo Request
  11 = Time Exceeded (TTL = 0; used by traceroute)
  12 = Parameter Problem
```

### 4.6 UDP Header — RFC 768

```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |          Source Port          |       Destination Port        |
    |           (16 bits)           |          (16 bits)            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |            Length             |            Checksum           |
    |     (header + data, 16b)      |    (optional in IPv4, 16b)    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Data                                  |
    ~                        (varies)                               ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Minimum header: 8 bytes.
Checksum covers: pseudo-header (src IP, dst IP, protocol=17, UDP length)
                 + UDP header + UDP data.
In IPv4, UDP checksum is optional (0 = disabled).
In IPv6, UDP checksum is mandatory.
```

### 4.7 TCP Header — RFC 793

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
    |  Data |       |C|E|U|A|P|R|S|F|                               |
    | Offset|Reserv |W|C|R|C|S|S|Y|I|          Window Size         |
    |  (4b) | (4b)  |R|E|G|K|H|T|N|N|           (16 bits)          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |           Checksum            |         Urgent Pointer        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options (if Data Offset > 5)               |
    ~                   (0-40 bytes, padded to 32-bit boundary)     ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                             Data                              |
    ~                           (varies)                            ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Field details:
  Source Port     (16b): sender's port
  Dest Port       (16b): receiver's port
  Sequence Number (32b): byte offset of first data byte in this segment
  Ack Number      (32b): next expected byte from peer (if ACK flag set)
  Data Offset     (4b):  TCP header length in 32-bit words (min=5=20 bytes)
  Reserved        (4b):  must be zero
  Flags           (8b):
     CWR: Congestion Window Reduced
     ECE: ECN-Echo
     URG: Urgent Pointer valid
     ACK: Acknowledgment Number valid
     PSH: Push — deliver data to application immediately
     RST: Reset connection
     SYN: Synchronize sequence numbers (connection setup)
     FIN: No more data from sender (connection teardown)
  Window Size     (16b): Receive window (flow control), in bytes
                          Can be scaled by Window Scale option (RFC 1323)
  Checksum        (16b): Covers pseudo-header + TCP header + data
  Urgent Pointer  (16b): If URG set: offset to end of urgent data

Data offset field: actual header length = Data Offset * 4 bytes
TCP options (common):
  Kind=0:  End of Options
  Kind=1:  NOP (padding)
  Kind=2:  Maximum Segment Size (MSS) — 4 bytes: kind, len, mss_value
  Kind=3:  Window Scale — 3 bytes: kind, len, shift_count
  Kind=8:  Timestamps — 10 bytes: kind, len, tsval, tsecr
  Kind=4:  SACK Permitted
  Kind=5:  SACK — variable length
```

### 4.8 DNS Query (UDP payload example)

```
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |            Transaction ID     |            Flags              |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |       Questions Count         |       Answer RR Count         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |    Authority RR Count         |    Additional RR Count        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |               Question Section (variable)                     |
    ~   QNAME (labels) | QTYPE (2B) | QCLASS (2B)                  ~
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

DNS name encoding (QNAME):
  "www.example.com" →  [03]www[07]example[03]com[00]
  each label prefixed by its 1-byte length, terminated by 0x00
```

---

## 5. Memory Layout: Endianness, Alignment, Padding

### Network Byte Order vs Host Byte Order

```
Network byte order: Big-endian (most significant byte first)
  Value 0x0800 (EtherType IPv4):
    Wire: [0x08][0x00]   byte 0 = 0x08 (high byte), byte 1 = 0x00 (low byte)

x86/x86-64 (little-endian):
    In memory: [0x00][0x08]   byte 0 = low byte, byte 1 = high byte
    uint16_t x = 0x0800;
    ((uint8_t*)&x)[0] == 0x00   ← little-endian!

ARM: typically little-endian in user mode, can be big-endian (ARMBE)
MIPS: can be either (MIPS routers often big-endian)
SPARC, PowerPC (networking chips): big-endian
```

### Conversion Functions (POSIX)

```c
#include <arpa/inet.h>   // or <netinet/in.h>

uint16_t htons(uint16_t hostshort);   // host to network short (16-bit)
uint32_t htonl(uint32_t hostlong);    // host to network long  (32-bit)
uint16_t ntohs(uint16_t netshort);    // network to host short
uint32_t ntohl(uint32_t netlong);     // network to host long

// 64-bit (Linux-specific)
uint64_t htobe64(uint64_t x);
uint64_t be64toh(uint64_t x);
```

### Why Struct Padding Matters

The C compiler may insert padding bytes for alignment:

```c
// WRONG — compiler may add 3 bytes padding after 'ttl'
struct bad_iphdr {
    uint8_t  version_ihl;  // offset 0
    uint8_t  tos;          // offset 1
    uint16_t tot_len;      // offset 2
    // ... 
    uint8_t  ttl;          // offset 8   ← only 1 byte
    // COMPILER PADS 3 BYTES HERE to align protocol to 4 bytes!
    uint32_t protocol;     // offset 12  ← should be offset 9!
};

// RIGHT — use __attribute__((packed)) or #pragma pack(1)
struct __attribute__((packed)) good_iphdr {
    uint8_t  version_ihl;
    uint8_t  tos;
    uint16_t tot_len;
    uint16_t id;
    uint16_t frag_off;
    uint8_t  ttl;
    uint8_t  protocol;     // offset 9 — no padding!
    uint16_t check;
    uint32_t saddr;
    uint32_t daddr;
};
```

### Bit Fields in C (Sub-byte fields)

```c
// IP header: version (4 bits) + IHL (4 bits) in first byte
// WARNING: bit field ordering is implementation-defined!

// On little-endian x86 (Linux kernel style):
struct iphdr {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    uint8_t ihl:4, version:4;   // ihl in low bits, version in high bits
#elif defined(__BIG_ENDIAN_BITFIELD)
    uint8_t version:4, ihl:4;   // version in high bits, ihl in low bits
#endif
    // ...
};

// Safer manual approach (used in many network stacks):
uint8_t first_byte = buf[0];
uint8_t version = (first_byte >> 4) & 0x0F;  // top 4 bits
uint8_t ihl     = (first_byte     ) & 0x0F;  // bottom 4 bits
```

### The Linux Kernel's Actual IP Header

From `include/uapi/linux/ip.h`:

```c
struct iphdr {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u8    ihl:4,
            version:4;
#elif defined (__BIG_ENDIAN_BITFIELD)
    __u8    version:4,
            ihl:4;
#else
#error  "Please fix <asm/byteorder.h>"
#endif
    __u8    tos;
    __be16  tot_len;
    __be16  id;
    __be16  frag_off;
    __u8    ttl;
    __u8    protocol;
    __sum16 check;
    __be32  saddr;
    __be32  daddr;
    /*The options start here. */
};
```

`__be16` and `__be32` are "big-endian annotated" types — the kernel uses sparse (a static analysis tool) to catch incorrect byte-order operations.

---

## 6. How the Transmitter WRITES a Packet

### Step-by-step: Sending a UDP Packet from Userspace

```
Application:   sendto(sockfd, "hello", 5, 0, &addr, sizeof(addr))
                │
                ▼ syscall
Kernel socket: sock_sendmsg()
                │
                ▼ protocol-specific
UDP:           udp_sendmsg()
                │  allocates sk_buff
                │  fills UDP header
                ▼
IP:            ip_make_skb() / ip_send_skb()
                │  fills IP header (src, dst, TTL, proto=17, checksum)
                │  fragments if needed
                ▼
Routing:       ip_route_output() — looks up routing table, finds egress
                                    interface and next-hop MAC
                ▼
ARP:           if next-hop MAC unknown → send ARP request, queue packet
                │  on ARP resolution:
                ▼
Ethernet:      dev_hard_header() — fills Ethernet header (src/dst MAC, ethertype)
                │
                ▼
Driver:        ndo_start_xmit() — puts sk_buff into TX ring
                │
                ▼
NIC hardware:  DMA reads buffer → serializes bits → sends preamble+SFD → wire
```

### Filling the Buffer (C example, raw view)

```c
// Allocate buffer: Ethernet + IP + UDP + data
uint8_t pkt[1500];
int offset = 0;

// === Ethernet Header (14 bytes) ===
struct ethhdr *eth = (struct ethhdr *)pkt;
memcpy(eth->h_dest,   dst_mac, 6);
memcpy(eth->h_source, src_mac, 6);
eth->h_proto = htons(ETH_P_IP);   // 0x0800
offset += sizeof(struct ethhdr);   // offset = 14

// === IP Header (20 bytes minimum) ===
struct iphdr *ip = (struct iphdr *)(pkt + offset);
ip->version  = 4;
ip->ihl      = 5;          // 20 bytes, no options
ip->tos      = 0;
ip->tot_len  = htons(20 + 8 + data_len);   // IP + UDP + data
ip->id       = htons(rand());
ip->frag_off = htons(IP_DF);  // Don't Fragment
ip->ttl      = 64;
ip->protocol = IPPROTO_UDP;  // 17
ip->check    = 0;            // zero before checksum calc
ip->saddr    = src_ip;       // already in network byte order
ip->daddr    = dst_ip;
ip->check    = ip_checksum((uint16_t *)ip, sizeof(struct iphdr));
offset += sizeof(struct iphdr);            // offset = 34

// === UDP Header (8 bytes) ===
struct udphdr *udp = (struct udphdr *)(pkt + offset);
udp->source = htons(src_port);
udp->dest   = htons(dst_port);
udp->len    = htons(8 + data_len);
udp->check  = 0;  // optional in IPv4, compute if desired
offset += sizeof(struct udphdr);           // offset = 42

// === Data ===
memcpy(pkt + offset, data, data_len);
offset += data_len;

// Total: offset = 42 + data_len bytes
// Send via raw socket:
sendto(raw_sockfd, pkt, offset, 0, (struct sockaddr *)&sa, sizeof(sa));
```

### Key insight: byte-by-byte vs field-by-field

The transmitter writes **field by field** using struct pointers or explicit byte writes. The hardware then sends **bit by bit** (serialized). The application never manually "writes bit by bit" — that's the PHY's job.

---

## 7. NIC DMA and Ring Buffers

### TX Path (Transmit)

```
Kernel                            NIC Hardware
───────────────────────────────   ─────────────────────────────
TX Descriptor Ring (in RAM):      NIC's TX Engine:
┌─────────────────────────┐       
│ desc[0]: buf_addr=X     │──DMA──▶ reads bytes from buf_addr
│          len=60         │        serializes onto wire
│          flags=EOP      │        
├─────────────────────────┤       
│ desc[1]: buf_addr=Y     │       
│          len=1500       │       
│          ...            │       
└─────────────────────────┘       

head pointer: next free descriptor  (CPU writes here)
tail pointer: last consumed desc    (NIC writes here via MMIO/DMA)

TX flow:
1. Driver allocates sk_buff
2. Driver writes descriptor: buffer physical address + length + flags
3. Driver advances head pointer (MMIO write to NIC register)
4. NIC DMA-reads the buffer at that physical address
5. NIC serializes and transmits bits
6. NIC writes completion (status) back to descriptor
7. NIC raises interrupt (or driver polls)
8. Driver frees the sk_buff and advances tail pointer
```

### RX Path (Receive)

```
Kernel                            NIC Hardware
───────────────────────────────   ─────────────────────────────
RX Descriptor Ring:               NIC's RX Engine:
┌─────────────────────────┐       
│ desc[0]: buf_addr=A     │◀─DMA── writes received bytes to buf_addr
│          len=0 (empty)  │        fills in length, status
├─────────────────────────┤       
│ desc[1]: buf_addr=B     │       
│          len=0          │       
│ ...                     │       
└─────────────────────────┘       

RX flow:
1. Driver pre-allocates buffers (skb's), writes addresses into descriptors
2. NIC receives frame, validates FCS
3. NIC DMA-writes frame bytes into buffer at desc[current]
4. NIC writes length and status into descriptor
5. NIC raises interrupt (or NAPI polls)
6. Driver reads descriptor: length, status (checksum offload result, VLAN, etc.)
7. Driver builds sk_buff pointing at buffer
8. Driver replenishes descriptor ring with new empty buffer
9. sk_buff passed up the network stack
```

### Physical Addressing and IOMMU

```
The NIC uses physical (bus/DMA) addresses, not virtual addresses.
Driver must:
  dma_addr_t dma = dma_map_single(dev, virt_addr, len, DMA_FROM_DEVICE);
  descriptor->addr = dma;
  // After DMA completes:
  dma_unmap_single(dev, dma, len, DMA_FROM_DEVICE);

IOMMU (Intel VT-d / AMD-Vi):
  Hardware page table between NIC and RAM
  Prevents DMA attacks (NIC can only access regions it's mapped to)
  Driver programs IOMMU via kernel DMA API
```

---

## 8. How the NIC Receives — NAPI and Interrupts

### Old Way: Pure Interrupt-Driven

```
1. Frame arrives → NIC raises IRQ
2. CPU: interrupts current task, jumps to ISR
3. ISR: process ONE packet, ack interrupt
4. Return from ISR, resume previous task
5. Next frame → another IRQ

Problem: at 1Gbps, ~1.5M small packets/sec → 1.5M interrupts/sec
         → interrupt overhead dominates CPU time (interrupt storm)
```

### Modern Way: NAPI (New API)

```
1. Frame arrives → NIC raises IRQ
2. ISR: disable NIC interrupts, schedule NAPI poll
3. net_rx_action() runs in softirq context (ksoftirqd or return from syscall)
4. Driver's poll() called: process up to 'budget' (e.g. 64) packets in a loop
5. If budget exhausted: yield, reschedule (more packets waiting)
6. If all packets processed: re-enable NIC interrupts
7. Next batch of frames → single IRQ → process N packets

This amortizes interrupt overhead across batches.
```

```c
// Simplified NAPI poll callback in a driver:
static int my_napi_poll(struct napi_struct *napi, int budget)
{
    struct my_nic *nic = container_of(napi, struct my_nic, napi);
    int work_done = 0;

    while (work_done < budget) {
        struct rx_desc *desc = &nic->rx_ring[nic->rx_head];
        
        if (!(desc->status & DESC_DONE))
            break;  // no more completed descriptors
        
        struct sk_buff *skb = nic->rx_skbs[nic->rx_head];
        skb_put(skb, desc->length);  // set actual data length
        skb->protocol = eth_type_trans(skb, nic->netdev); // set protocol
        
        // Checksum offload result
        if (desc->status & DESC_CSUM_OK)
            skb->ip_summed = CHECKSUM_UNNECESSARY;
        
        netif_receive_skb(skb);  // pass to network stack
        
        // Replenish ring with new buffer
        nic->rx_skbs[nic->rx_head] = alloc_and_map_skb(nic);
        desc->status = 0;  // mark as available
        
        nic->rx_head = (nic->rx_head + 1) % RX_RING_SIZE;
        work_done++;
    }

    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        enable_nic_interrupts(nic);  // re-arm interrupt
    }
    return work_done;
}
```

### Checksum Offload

Modern NICs can compute and verify checksums in hardware:

```
TX Offload:
  Driver sets flags in descriptor / sk_buff:
    skb->ip_summed = CHECKSUM_PARTIAL
    skb->csum_start = offset to start of checksum coverage
    skb->csum_offset = offset from csum_start to put the checksum
  NIC fills in checksum during DMA

RX Offload:
  NIC verifies IP/TCP/UDP checksum during receive
  Sets descriptor status bit if correct
  Driver sets:
    skb->ip_summed = CHECKSUM_UNNECESSARY  (kernel skips software check)

Other offloads:
  TSO (TCP Segmentation Offload): NIC splits large TCP buffers into MSS-sized segments
  LRO/GRO (Large/Generic Receive Offload): NIC or driver coalesces small segments
  VLAN offload: NIC strips/inserts VLAN tags
  RSS (Receive Side Scaling): multiple RX queues, hash-based per-flow distribution
```

---

## 9. How the Receiver READS a Packet

### The sk_buff Pointer Journey

```
NIC DMA buffer (physical RAM):
  [ETHHDR 14B][IPHDR 20B][TCPHDR 20B][DATA ...]
       ^
       │ dma_map
       │
sk_buff->data ──────────────────────────────────────┐
                                                     │
eth_type_trans():                                    │
  skb->mac_header = skb->data  (ethernet header here)
  skb_pull(skb, ETH_HLEN)      (move data pointer past ethernet)
  skb->data now points to IP header

ip_rcv():
  skb->network_header = skb->data  (IP header here)
  skb_pull(skb, ip_hdrlen(skb))    (move data pointer past IP header)
  skb->data now points to TCP/UDP header

tcp_v4_rcv():
  skb->transport_header = skb->data  (TCP header here)
  skb_pull(skb, tcp_hdrlen(skb))     (move data pointer past TCP header)
  skb->data now points to application data
  → copy to socket receive buffer
  → wake up blocking read() or signal readable via epoll

The SAME physical bytes are never copied for headers —
only the data pointer is advanced. Zero-copy for header processing.
```

### Reading a Field: The Mechanics

```
Buffer in memory at address 0x1000:
Offset  Value   Field
0x1000  0x45    IP: version=4, IHL=5
0x1001  0x00    IP: DSCP/ECN
0x1002  0x00    IP: Total Length (high byte)
0x1003  0x3C    IP: Total Length (low byte) → 0x003C = 60 bytes
0x1004  0xAB    IP: ID (high byte)
0x1005  0xCD    IP: ID (low byte) → 0xABCD
...

To read Total Length:
  uint8_t *p = buf + 0x1000;
  uint16_t total_len = (p[2] << 8) | p[3];  // manual big-endian read
  // OR using struct:
  struct iphdr *iph = (struct iphdr *)p;
  uint16_t total_len = ntohs(iph->tot_len);  // struct field + ntohs

Why ntohs? iph->tot_len is stored as [0x00][0x3C] in network byte order.
On x86 (little-endian), reading it as uint16_t gives 0x3C00 (WRONG).
ntohs() swaps bytes → 0x003C (CORRECT: 60 bytes).
```

---

## 10. Linux Kernel Network Stack Deep Dive

### sk_buff Structure (Simplified)

From `include/linux/skbuff.h` — the most important data structure in the kernel:

```c
struct sk_buff {
    /* --- Pointers to data --- */
    unsigned char       *head;      // start of allocated buffer
    unsigned char       *data;      // start of current data (moves as headers stripped)
    unsigned char       *tail;      // end of current data
    unsigned char       *end;       // end of allocated buffer

    /* --- Header pointers (offsets from head) --- */
    sk_buff_data_t      transport_header;  // L4 (TCP/UDP) header
    sk_buff_data_t      network_header;    // L3 (IP) header
    sk_buff_data_t      mac_header;        // L2 (Ethernet) header

    /* --- Metadata --- */
    __u32               len;         // total length of all data
    __u32               data_len;    // length in frags (for nonlinear skbs)
    __be16              protocol;    // EtherType (e.g. ETH_P_IP)
    __u8                pkt_type;    // PACKET_HOST, PACKET_BROADCAST, etc.
    __u8                ip_summed;   // checksum status
    __wsum              csum;        // checksum value
    
    /* --- Device --- */
    struct net_device   *dev;        // receiving/sending network interface
    
    /* --- Routing/socket --- */
    struct dst_entry    *_skb_refdst; // routing destination cache entry
    struct sock         *sk;          // owning socket (NULL if not yet delivered)

    /* --- Timestamps --- */
    ktime_t             tstamp;       // receive timestamp

    /* --- Fragmentation --- */
    skb_frag_t          frags[MAX_SKB_FRAGS]; // scatter-gather fragments
    
    /* --- cb: control block (per-protocol scratch space) --- */
    char                cb[48] __aligned(8);  // TCP uses this for TCP_SKB_CB
    
    /* --- List management --- */
    struct sk_buff      *next, *prev;  // queue linkage
    
    /* many more fields... */
};
```

### sk_buff Layout in Memory

```
head                                                    end
  │                                                      │
  ▼                                                      ▼
  ┌──────────┬──────────┬──────────┬────────┬──────────┐
  │ headroom │ eth hdr  │  ip hdr  │tcp hdr │   data   │ tailroom
  │ (empty)  │  14 bytes│ 20 bytes │20 bytes│          │
  └──────────┴──────────┴──────────┴────────┴──────────┘
             ▲                              ▲           ▲
             │                              │           │
            data (initially)               tail        end

headroom: space for prepending headers (used on TX to add headers)
tailroom: space for appending data

skb_push(skb, len): move data backward (prepend, expand headroom)
skb_pull(skb, len): move data forward  (strip header, consume)
skb_put (skb, len): move tail forward  (append data)
```

### The RX Path: Function Call Chain

```
hardware interrupt
  └─ driver ISR: napi_schedule()

softirq: net_rx_action()
  └─ driver->poll(): netif_receive_skb(skb)
       └─ __netif_receive_skb_core()
            │
            ├─ tc ingress (traffic control, eBPF)
            │
            ├─ ptype handlers registered for ETH_P_ALL (packet sockets, tcpdump)
            │
            └─ protocol handler lookup by skb->protocol
                 │
                 ├─ ETH_P_IP  (0x0800) → ip_rcv()
                 │    └─ NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING)
                 │         └─ ip_rcv_finish()
                 │              └─ ip_route_input() — routing decision
                 │                   │
                 │                   ├─ local delivery → ip_local_deliver()
                 │                   │    └─ NF_HOOK(NF_INET_LOCAL_IN)
                 │                   │         └─ ip_local_deliver_finish()
                 │                   │              └─ protocol handler:
                 │                   │                   tcp_v4_rcv()
                 │                   │                   udp_rcv()
                 │                   │                   icmp_rcv()
                 │                   │
                 │                   └─ forward → ip_forward()
                 │                        └─ NF_HOOK(NF_INET_FORWARD)
                 │                             └─ ip_output()
                 │
                 ├─ ETH_P_ARP (0x0806) → arp_rcv()
                 │
                 └─ ETH_P_IPV6(0x86DD) → ipv6_rcv()
```

### Netfilter Hooks

```
                 ┌─────────────────────────────────────────────┐
                 │              IPv4 Packet Path               │
                 │                                             │
  Network ──────▶│  PRE_ROUTING ──▶ routing ──▶ LOCAL_IN      │──▶ Socket
  Interface      │       │                                     │
                 │       └──── FORWARD ──▶ POST_ROUTING ───────│──▶ Network
                 │                                             │    Interface
  Socket ────────│  LOCAL_OUT ──▶ routing ──▶ POST_ROUTING    │
                 └─────────────────────────────────────────────┘

Hook points:
  NF_INET_PRE_ROUTING:   After receive, before routing
  NF_INET_LOCAL_IN:      For packets destined to local host
  NF_INET_FORWARD:       For packets being forwarded
  NF_INET_LOCAL_OUT:     From local sockets, before routing
  NF_INET_POST_ROUTING:  Before sending to NIC

Hook return values:
  NF_ACCEPT:   continue processing
  NF_DROP:     drop packet, free sk_buff
  NF_STOLEN:   hook takes ownership of skb, do not process further
  NF_QUEUE:    queue for userspace (nfqueue)
  NF_REPEAT:   call hook again

iptables uses these hooks.
nftables uses these hooks.
conntrack (connection tracking) uses PRE_ROUTING and LOCAL_OUT.
```

### TCP Receive: tcp_v4_rcv()

```c
// Highly simplified view of tcp_v4_rcv
int tcp_v4_rcv(struct sk_buff *skb)
{
    const struct iphdr *iph = ip_hdr(skb);
    const struct tcphdr *th;
    struct sock *sk;

    // 1. Basic TCP header validation
    if (skb->pkt_type != PACKET_HOST) goto discard;  // not for us
    if (!pskb_may_pull(skb, sizeof(struct tcphdr))) goto discard;  // too short
    
    th = (const struct tcphdr *)skb->data;
    if (th->doff < sizeof(struct tcphdr)/4) goto bad_packet;  // invalid offset
    if (!pskb_may_pull(skb, th->doff*4)) goto discard;
    
    // 2. TCP checksum verification
    if (skb->ip_summed != CHECKSUM_UNNECESSARY) {
        if (tcp_v4_checksum_init(skb)) goto bad_packet;  // checksum fail → drop
    }
    
    // 3. Look up socket by (src_ip, src_port, dst_ip, dst_port)
    sk = __inet_lookup_skb(&tcp_hashinfo, skb, __tcp_hdrlen(th),
                           th->source, th->dest, ...);
    if (!sk) goto no_tcp_socket;  // no socket → send RST or drop
    
    // 4. State machine: process according to connection state
    tcp_v4_do_rcv(sk, skb);  // handles SYN, ESTABLISHED, FIN, etc.
    return 0;

no_tcp_socket:
    // Send RST if not a RST itself, and no socket listening
    tcp_v4_send_reset(NULL, skb);
    goto discard;
discard:
    kfree_skb(skb);
    return 0;
}
```

---

## 11. Packet Processing Decisions

When the kernel (or a router, switch, firewall) receives a packet, it makes one of several decisions:

### 11.1 ACCEPT / DELIVER

Deliver to local process via socket.

```
Decision triggers:
  - Destination IP matches a local address
  - Destination port has a listening socket
  - TCP is in ESTABLISHED state for that 4-tuple

Path:
  ip_local_deliver() → tcp_v4_rcv() / udp_rcv()
  → __skb_queue_tail(&sk->sk_receive_queue, skb)
  → sk->sk_data_ready(sk)  // wake up blocking read()
  → userspace: read()/recv()/recvfrom() returns data

Socket receive queue:
  sk_buff objects are queued here (zero-copy from NIC to socket)
  read() calls tcp_recvmsg() which copies from sk_buff to userspace buffer
```

### 11.2 DROP

Free the sk_buff, no notification to sender.

```
When to drop:
  - IP checksum fails
  - TCP checksum fails
  - Firewall rule says DROP
  - Rate limit exceeded
  - Buffer overflow (socket receive buffer full, or NIC ring full)
  - TTL = 0
  - Malformed header (too short, invalid field values)
  - RPF check fails (Reverse Path Filtering)

kfree_skb(skb);  // the drop primitive in kernel
                  // decrements reference count, frees when 0

From iptables:
  iptables -A INPUT -j DROP  → NF_DROP → kfree_skb

From BPF/XDP:
  return XDP_DROP;  // drop before sk_buff even allocated!
```

### 11.3 IGNORE (Silent Drop)

No processing, no response. Indistinguishable from DROP at the code level.
The distinction is semantic:
- **DROP**: explicit policy decision (firewall)
- **IGNORE**: packet is not meant for us (wrong port, wrong protocol, etc.)

Example: UDP packet to an unbound port →
`udp_rcv()` finds no socket → `icmp_send(skb, ICMP_DEST_UNREACH, ICMP_PORT_UNREACH)` → `kfree_skb()`

But `iptables -j DROP` simply drops without ICMP — this is "ignore".

### 11.4 FORWARD (Route)

Pass packet to another network interface after decrementing TTL.

```
Decision: destination IP is not local → routing table lookup → forward

ip_forward():
  1. Verify packet isn't expired (TTL check)
  2. ip_decrease_ttl(skb)  // TTL -= 1
  3. If TTL hits 0: icmp_send(ICMP_TIME_EXCEEDED) + drop
  4. NF_HOOK(NF_INET_FORWARD)  // firewall check for forwarded traffic
  5. ip_output() → dev_queue_xmit() → NIC TX

To enable forwarding on Linux:
  echo 1 > /proc/sys/net/ipv4/ip_forward
  # or:
  sysctl -w net.ipv4.ip_forward=1

Router behavior:
  For each incoming packet:
    dst = routing_table_lookup(pkt->dst_ip)
    if dst == local: deliver to socket
    else:
        pkt->ttl--
        if pkt->ttl == 0: send ICMP Time Exceeded, drop
        new_eth_dst = arp_lookup(dst.next_hop)
        rewrite ethernet header
        send out dst.interface
```

### 11.5 REJECT

Drop but send ICMP error back:

```
iptables -A INPUT -j REJECT --reject-with icmp-port-unreachable

→ NF_DROP but before freeing: send ICMP unreachable to source
→ kfree_skb(skb)

Types of ICMP reject:
  icmp-net-unreachable:   ICMP Type 3, Code 0
  icmp-host-unreachable:  ICMP Type 3, Code 1
  icmp-port-unreachable:  ICMP Type 3, Code 3
  icmp-proto-unreachable: ICMP Type 3, Code 2
  tcp-reset:              TCP RST (for TCP packets)
```

### 11.6 RATE LIMIT (Token Bucket / Police)

```
Linux tc (traffic control) with police action:

tc qdisc add dev eth0 ingress
tc filter add dev eth0 parent ffff: \
    matchall \
    action police rate 10mbit burst 1mbit drop

Or iptables hashlimit:
iptables -A INPUT -m hashlimit \
    --hashlimit-name ssh \
    --hashlimit-upto 5/min \
    --hashlimit-burst 10 \
    --hashlimit-mode srcip \
    -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP
```

### 11.7 NAT / REWRITE

Modify packet fields:

```
Source NAT (SNAT): rewrite source IP (e.g. for internet access from LAN)
  iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

Destination NAT (DNAT): rewrite destination IP (e.g. port forwarding)
  iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to 192.168.1.10:8080

Kernel conntrack tracks NAT mappings; reverse translation on return packets.

In code (nf_nat):
  nf_nat_packet() modifies sk_buff in place:
    - overwrites IP src or dst
    - updates IP checksum (incremental update)
    - updates TCP/UDP checksum (pseudo-header changed)
    - updates conntrack tuple for tracking
```

### 11.8 Decision Summary Table

```
Decision      | Code Action               | Sender Notified | Example
─────────────────────────────────────────────────────────────────────
ACCEPT/DELIVER| deliver to socket         | via application | Normal RX
DROP          | kfree_skb()               | No              | iptables DROP
REJECT        | send ICMP + kfree_skb()   | Yes (ICMP)      | iptables REJECT
FORWARD       | decrement TTL, resend     | No              | Router
NAT           | rewrite fields, forward   | No              | iptables MASQ
STOLEN        | module keeps skb          | Depends         | nfqueue
QUEUE         | send to userspace         | No              | NFQUEUE
RATELIMIT     | drop some, accept rest    | No              | hashlimit
XDP_DROP      | drop before alloc         | No              | BPF/XDP
XDP_TX        | transmit back out same NIC| No              | BPF/XDP
XDP_REDIRECT  | redirect to other NIC/CPU | No              | BPF/XDP
```

---

## 12. C Implementation

### Complete Packet Parser in C

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/ip_icmp.h>
#include <net/ethernet.h>
#include <net/if_arp.h>

/* ─────────────────────────────────────────────────────
   Utilities
   ───────────────────────────────────────────────────── */

// Read a big-endian uint16 from an arbitrary byte offset
// (avoids unaligned access which is UB in C on some platforms)
static inline uint16_t read_be16(const uint8_t *p) {
    return ((uint16_t)p[0] << 8) | p[1];
}

static inline uint32_t read_be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
         | ((uint32_t)p[2] <<  8) |  (uint32_t)p[3];
}

/* ─────────────────────────────────────────────────────
   IP Checksum (one's complement sum)
   ───────────────────────────────────────────────────── */
uint16_t ip_checksum(const void *vdata, size_t length)
{
    const uint8_t *data = vdata;
    uint32_t acc = 0;
    
    // Sum 16-bit words
    for (size_t i = 0; i + 1 < length; i += 2) {
        acc += ((uint16_t)data[i] << 8) | data[i+1];
    }
    // Handle odd byte
    if (length & 1) {
        acc += (uint16_t)data[length-1] << 8;
    }
    // Fold 32-bit sum to 16-bit
    while (acc >> 16)
        acc = (acc & 0xFFFF) + (acc >> 16);
    
    return ~(uint16_t)acc;  // one's complement
}

/* ─────────────────────────────────────────────────────
   Packet Buffer Bounds Checking
   ───────────────────────────────────────────────────── */
typedef struct {
    const uint8_t *data;
    size_t         len;
    size_t         offset;  // current parse cursor
} pktbuf_t;

static int pb_advance(pktbuf_t *pb, size_t n) {
    if (pb->offset + n > pb->len) return -1;  // out of bounds
    pb->offset += n;
    return 0;
}

static const uint8_t *pb_ptr(const pktbuf_t *pb) {
    return pb->data + pb->offset;
}

/* ─────────────────────────────────────────────────────
   Layer 2: Ethernet Parser
   ───────────────────────────────────────────────────── */
typedef struct {
    uint8_t  dst[6];
    uint8_t  src[6];
    uint16_t ethertype;
    // If ethertype == 0x8100: VLAN tag here (4 more bytes)
} eth_frame_t;

#define ETH_HDR_LEN 14

int parse_ethernet(pktbuf_t *pb, eth_frame_t *out) {
    if (pb->len - pb->offset < ETH_HDR_LEN) return -1;
    const uint8_t *p = pb_ptr(pb);
    
    memcpy(out->dst, p,     6);
    memcpy(out->src, p + 6, 6);
    out->ethertype = read_be16(p + 12);
    
    // Handle 802.1Q VLAN tag
    if (out->ethertype == 0x8100) {
        if (pb->len - pb->offset < ETH_HDR_LEN + 4) return -1;
        // VLAN TCI at p+14, real ethertype at p+16
        out->ethertype = read_be16(p + 16);
        pb_advance(pb, ETH_HDR_LEN + 4);  // consume eth + vlan tag
    } else {
        pb_advance(pb, ETH_HDR_LEN);
    }
    return 0;
}

/* ─────────────────────────────────────────────────────
   Layer 3: IPv4 Parser
   ───────────────────────────────────────────────────── */
typedef struct {
    uint8_t  version;
    uint8_t  ihl;
    uint8_t  dscp;
    uint8_t  ecn;
    uint16_t total_len;
    uint16_t id;
    uint8_t  flags;
    uint16_t frag_offset;
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t checksum;
    uint32_t src;
    uint32_t dst;
} ipv4_hdr_t;

int parse_ipv4(pktbuf_t *pb, ipv4_hdr_t *out) {
    if (pb->len - pb->offset < 20) return -1;
    const uint8_t *p = pb_ptr(pb);
    
    out->version    = (p[0] >> 4) & 0x0F;
    out->ihl        = (p[0]     ) & 0x0F;
    
    if (out->version != 4) return -1;   // not IPv4
    if (out->ihl < 5)      return -1;   // invalid header length
    
    size_t hdr_len = out->ihl * 4;
    if (pb->len - pb->offset < hdr_len) return -1;
    
    out->dscp       = (p[1] >> 2) & 0x3F;
    out->ecn        = (p[1]     ) & 0x03;
    out->total_len  = read_be16(p + 2);
    out->id         = read_be16(p + 4);
    out->flags      = (p[6] >> 5) & 0x07;
    out->frag_offset= (read_be16(p + 6) & 0x1FFF) * 8;  // in bytes
    out->ttl        = p[8];
    out->protocol   = p[9];
    out->checksum   = read_be16(p + 10);
    out->src        = read_be32(p + 12);
    out->dst        = read_be32(p + 16);
    
    // Verify checksum
    uint16_t saved = out->checksum;
    // checksum of header with checksum field zeroed must be 0xFFFF
    // Alternatively: checksum over all bytes (including checksum) == 0xFFFF
    uint16_t computed = ip_checksum(p, hdr_len);
    if (computed != 0) return -1;  // checksum mismatch → drop
    
    pb_advance(pb, hdr_len);  // consume IP header (including options)
    return 0;
}

/* ─────────────────────────────────────────────────────
   Layer 4: TCP Parser
   ───────────────────────────────────────────────────── */
typedef struct {
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq;
    uint32_t ack;
    uint8_t  data_offset;
    // Flags
    uint8_t  cwr:1, ece:1, urg:1, ack_f:1,
             psh:1, rst:1, syn:1, fin:1;
    uint16_t window;
    uint16_t checksum;
    uint16_t urgent_ptr;
} tcp_hdr_t;

int parse_tcp(pktbuf_t *pb, tcp_hdr_t *out) {
    if (pb->len - pb->offset < 20) return -1;
    const uint8_t *p = pb_ptr(pb);
    
    out->src_port   = read_be16(p);
    out->dst_port   = read_be16(p + 2);
    out->seq        = read_be32(p + 4);
    out->ack        = read_be32(p + 8);
    out->data_offset= (p[12] >> 4) & 0x0F;
    
    if (out->data_offset < 5) return -1;
    size_t hdr_len = out->data_offset * 4;
    if (pb->len - pb->offset < hdr_len) return -1;
    
    uint8_t flags = p[13];
    out->cwr   = (flags >> 7) & 1;
    out->ece   = (flags >> 6) & 1;
    out->urg   = (flags >> 5) & 1;
    out->ack_f = (flags >> 4) & 1;
    out->psh   = (flags >> 3) & 1;
    out->rst   = (flags >> 2) & 1;
    out->syn   = (flags >> 1) & 1;
    out->fin   = (flags >> 0) & 1;
    
    out->window     = read_be16(p + 14);
    out->checksum   = read_be16(p + 16);
    out->urgent_ptr = read_be16(p + 18);
    
    pb_advance(pb, hdr_len);
    return 0;
}

/* ─────────────────────────────────────────────────────
   UDP Parser
   ───────────────────────────────────────────────────── */
typedef struct {
    uint16_t src_port;
    uint16_t dst_port;
    uint16_t length;
    uint16_t checksum;
} udp_hdr_t;

int parse_udp(pktbuf_t *pb, udp_hdr_t *out) {
    if (pb->len - pb->offset < 8) return -1;
    const uint8_t *p = pb_ptr(pb);
    out->src_port = read_be16(p);
    out->dst_port = read_be16(p + 2);
    out->length   = read_be16(p + 4);
    out->checksum = read_be16(p + 6);
    if (out->length < 8) return -1;
    pb_advance(pb, 8);
    return 0;
}

/* ─────────────────────────────────────────────────────
   Main Dispatcher: Process a Raw Frame
   ───────────────────────────────────────────────────── */
typedef enum {
    PKT_ACCEPT,
    PKT_DROP,
    PKT_FORWARD,
} pkt_action_t;

pkt_action_t process_packet(const uint8_t *raw, size_t len)
{
    pktbuf_t pb = { .data = raw, .len = len, .offset = 0 };
    
    // --- Layer 2: Ethernet ---
    eth_frame_t eth;
    if (parse_ethernet(&pb, &eth) < 0) {
        fprintf(stderr, "Bad Ethernet header\n");
        return PKT_DROP;
    }
    
    char mac_str[18];
    printf("ETH: %02X:%02X:%02X:%02X:%02X:%02X → "
           "%02X:%02X:%02X:%02X:%02X:%02X, type=0x%04X\n",
           eth.src[0],eth.src[1],eth.src[2],eth.src[3],eth.src[4],eth.src[5],
           eth.dst[0],eth.dst[1],eth.dst[2],eth.dst[3],eth.dst[4],eth.dst[5],
           eth.ethertype);
    
    if (eth.ethertype == 0x0806) {
        printf("ARP packet\n");
        return PKT_ACCEPT;
    }
    
    if (eth.ethertype != 0x0800) {
        printf("Unknown EtherType 0x%04X, ignoring\n", eth.ethertype);
        return PKT_DROP;
    }
    
    // --- Layer 3: IPv4 ---
    ipv4_hdr_t ip;
    if (parse_ipv4(&pb, &ip) < 0) {
        fprintf(stderr, "Bad IPv4 header or checksum\n");
        return PKT_DROP;
    }
    
    struct in_addr src_addr = { .s_addr = htonl(ip.src) };
    struct in_addr dst_addr = { .s_addr = htonl(ip.dst) };
    printf("IPv4: %s → %s, proto=%d, ttl=%d\n",
           inet_ntoa(src_addr), inet_ntoa(dst_addr),
           ip.protocol, ip.ttl);
    
    // TTL check (router behavior)
    if (ip.ttl == 0) {
        printf("TTL expired → DROP + send ICMP Time Exceeded\n");
        return PKT_DROP;
    }
    
    // Fragmented packet: reassembly needed before L4 parse
    if (ip.frag_offset != 0 || (ip.flags & 0x1)) {  // MF bit
        printf("Fragmented packet, queuing for reassembly\n");
        return PKT_ACCEPT;  // real code would reassemble
    }
    
    // --- Layer 4 ---
    if (ip.protocol == IPPROTO_TCP) {
        tcp_hdr_t tcp;
        if (parse_tcp(&pb, &tcp) < 0) {
            fprintf(stderr, "Bad TCP header\n");
            return PKT_DROP;
        }
        printf("TCP: port %d → %d, seq=%u, ack=%u, "
               "flags=[%s%s%s%s%s%s]\n",
               tcp.src_port, tcp.dst_port,
               tcp.seq, tcp.ack,
               tcp.syn?"SYN ":"", tcp.ack_f?"ACK ":"",
               tcp.fin?"FIN ":"", tcp.rst?"RST ":"",
               tcp.psh?"PSH ":"", tcp.urg?"URG ":"");
        
        // Application data at pb.data + pb.offset
        size_t data_len = pb.len - pb.offset;
        printf("TCP payload: %zu bytes\n", data_len);
        
    } else if (ip.protocol == IPPROTO_UDP) {
        udp_hdr_t udp;
        if (parse_udp(&pb, &udp) < 0) {
            fprintf(stderr, "Bad UDP header\n");
            return PKT_DROP;
        }
        printf("UDP: port %d → %d, len=%d\n",
               udp.src_port, udp.dst_port, udp.length);
        
    } else if (ip.protocol == IPPROTO_ICMP) {
        const uint8_t *p = pb_ptr(&pb);
        printf("ICMP: type=%d, code=%d\n", p[0], p[1]);
        
    } else {
        printf("Unknown protocol %d\n", ip.protocol);
        return PKT_DROP;
    }
    
    return PKT_ACCEPT;
}
```

### Raw Socket Capture in C

```c
#include <sys/socket.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <stdio.h>

int main(void)
{
    // AF_PACKET + SOCK_RAW = receive raw Ethernet frames
    // ETH_P_ALL = receive all protocols
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sock < 0) { perror("socket"); return 1; }
    
    // Optionally bind to a specific interface
    struct ifreq ifr;
    strncpy(ifr.ifr_name, "eth0", IFNAMSIZ-1);
    ioctl(sock, SIOCGIFINDEX, &ifr);
    
    struct sockaddr_ll sll = {
        .sll_family   = AF_PACKET,
        .sll_protocol = htons(ETH_P_ALL),
        .sll_ifindex  = ifr.ifr_ifindex,
    };
    bind(sock, (struct sockaddr *)&sll, sizeof(sll));
    
    uint8_t buf[65536];
    while (1) {
        ssize_t n = recv(sock, buf, sizeof(buf), 0);
        if (n < 0) { perror("recv"); break; }
        printf("\n=== Received %zd bytes ===\n", n);
        process_packet(buf, n);
    }
    close(sock);
    return 0;
}
```

### TCP Packet Crafting (Raw Socket, Requires CAP_NET_RAW)

```c
// Build a TCP SYN from scratch
void craft_syn(uint32_t src_ip, uint32_t dst_ip,
               uint16_t src_port, uint16_t dst_port,
               uint8_t *buf, size_t *out_len)
{
    memset(buf, 0, 40);
    
    // IP header at buf[0]
    struct iphdr *ip = (struct iphdr *)buf;
    ip->version  = 4;
    ip->ihl      = 5;
    ip->tot_len  = htons(40);  // 20 IP + 20 TCP
    ip->id       = htons(0x1234);
    ip->frag_off = htons(IP_DF);
    ip->ttl      = 64;
    ip->protocol = IPPROTO_TCP;
    ip->saddr    = src_ip;    // must be in network byte order
    ip->daddr    = dst_ip;
    ip->check    = ip_checksum(ip, 20);
    
    // TCP header at buf[20]
    struct tcphdr *tcp = (struct tcphdr *)(buf + 20);
    tcp->source  = htons(src_port);
    tcp->dest    = htons(dst_port);
    tcp->seq     = htonl(0xDEADBEEF);
    tcp->ack_seq = 0;
    tcp->doff    = 5;  // 20 bytes, no options
    tcp->syn     = 1;  // SYN flag
    tcp->window  = htons(65535);
    
    // TCP checksum uses pseudo-header
    // pseudo-header: src_ip(4) + dst_ip(4) + 0(1) + proto(1) + tcp_len(2)
    struct {
        uint32_t src, dst;
        uint8_t  zero, proto;
        uint16_t tcp_len;
    } pseudo = {
        .src     = src_ip,
        .dst     = dst_ip,
        .zero    = 0,
        .proto   = IPPROTO_TCP,
        .tcp_len = htons(20),
    };
    
    // Compute checksum over pseudo-header + TCP header
    // (real implementation uses a gather checksum)
    uint8_t csum_buf[32];
    memcpy(csum_buf,      &pseudo, 12);
    memcpy(csum_buf + 12, tcp,     20);
    tcp->check = ip_checksum(csum_buf, 32);
    
    *out_len = 40;
}
```

---

## 13. Rust Implementation

### Packet Parsing in Rust (Manual, Zero-Copy)

```rust
// Cargo.toml:
// [dependencies]
// # no external deps needed for basic parsing

use std::convert::TryInto;

/// Read big-endian u16 from a byte slice at offset
fn read_u16_be(buf: &[u8], offset: usize) -> Option<u16> {
    let b = buf.get(offset..offset + 2)?;
    Some(u16::from_be_bytes(b.try_into().unwrap()))
}

fn read_u32_be(buf: &[u8], offset: usize) -> Option<u32> {
    let b = buf.get(offset..offset + 4)?;
    Some(u32::from_be_bytes(b.try_into().unwrap()))
}

// ─── Ethernet ─────────────────────────────────────────────────

#[derive(Debug)]
pub struct EthernetFrame<'a> {
    pub dst_mac:   [u8; 6],
    pub src_mac:   [u8; 6],
    pub ethertype: u16,
    pub payload:   &'a [u8],  // zero-copy slice of original buffer
}

#[derive(Debug)]
pub enum ParseError {
    TooShort,
    InvalidField(&'static str),
    BadChecksum,
}

pub fn parse_ethernet(buf: &[u8]) -> Result<EthernetFrame, ParseError> {
    if buf.len() < 14 {
        return Err(ParseError::TooShort);
    }
    
    let dst_mac: [u8; 6] = buf[0..6].try_into().unwrap();
    let src_mac: [u8; 6] = buf[6..12].try_into().unwrap();
    let ethertype = u16::from_be_bytes(buf[12..14].try_into().unwrap());
    
    // Handle 802.1Q VLAN tag
    let (ethertype, payload_start) = if ethertype == 0x8100 {
        if buf.len() < 18 {
            return Err(ParseError::TooShort);
        }
        let real_etype = u16::from_be_bytes(buf[16..18].try_into().unwrap());
        (real_etype, 18)
    } else {
        (ethertype, 14)
    };
    
    Ok(EthernetFrame {
        dst_mac,
        src_mac,
        ethertype,
        payload: &buf[payload_start..],
    })
}

// ─── IPv4 ──────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct Ipv4Header {
    pub version:      u8,
    pub ihl:          u8,       // header length in 32-bit words
    pub dscp:         u8,
    pub ecn:          u8,
    pub total_len:    u16,
    pub id:           u16,
    pub dont_frag:    bool,
    pub more_frags:   bool,
    pub frag_offset:  u16,      // in bytes
    pub ttl:          u8,
    pub protocol:     u8,
    pub checksum:     u16,
    pub src:          std::net::Ipv4Addr,
    pub dst:          std::net::Ipv4Addr,
    pub header_len:   usize,    // actual header length in bytes
}

pub fn parse_ipv4(buf: &[u8]) -> Result<(Ipv4Header, &[u8]), ParseError> {
    if buf.len() < 20 {
        return Err(ParseError::TooShort);
    }
    
    let version = (buf[0] >> 4) & 0x0F;
    let ihl     = (buf[0]     ) & 0x0F;
    
    if version != 4 {
        return Err(ParseError::InvalidField("version"));
    }
    if ihl < 5 {
        return Err(ParseError::InvalidField("ihl"));
    }
    
    let header_len = ihl as usize * 4;
    if buf.len() < header_len {
        return Err(ParseError::TooShort);
    }
    
    // Verify checksum: sum of all 16-bit words in header must be 0xFFFF
    if ip_checksum(&buf[..header_len]) != 0 {
        return Err(ParseError::BadChecksum);
    }
    
    let flags_frag = u16::from_be_bytes(buf[6..8].try_into().unwrap());
    
    let hdr = Ipv4Header {
        version,
        ihl,
        dscp:         (buf[1] >> 2) & 0x3F,
        ecn:          buf[1] & 0x03,
        total_len:    u16::from_be_bytes(buf[2..4].try_into().unwrap()),
        id:           u16::from_be_bytes(buf[4..6].try_into().unwrap()),
        dont_frag:    (flags_frag >> 14) & 1 == 1,
        more_frags:   (flags_frag >> 13) & 1 == 1,
        frag_offset:  (flags_frag & 0x1FFF) * 8,
        ttl:          buf[8],
        protocol:     buf[9],
        checksum:     u16::from_be_bytes(buf[10..12].try_into().unwrap()),
        src:          std::net::Ipv4Addr::new(buf[12], buf[13], buf[14], buf[15]),
        dst:          std::net::Ipv4Addr::new(buf[16], buf[17], buf[18], buf[19]),
        header_len,
    };
    
    Ok((hdr, &buf[header_len..]))
}

// ─── TCP ───────────────────────────────────────────────────────

#[derive(Debug)]
pub struct TcpHeader<'a> {
    pub src_port:   u16,
    pub dst_port:   u16,
    pub seq:        u32,
    pub ack:        u32,
    pub flags:      TcpFlags,
    pub window:     u16,
    pub checksum:   u16,
    pub urgent_ptr: u16,
    pub payload:    &'a [u8],
}

#[derive(Debug, Default)]
pub struct TcpFlags {
    pub cwr: bool, pub ece: bool,
    pub urg: bool, pub ack: bool,
    pub psh: bool, pub rst: bool,
    pub syn: bool, pub fin: bool,
}

pub fn parse_tcp(buf: &[u8]) -> Result<TcpHeader, ParseError> {
    if buf.len() < 20 {
        return Err(ParseError::TooShort);
    }
    
    let data_offset = ((buf[12] >> 4) & 0x0F) as usize;
    if data_offset < 5 {
        return Err(ParseError::InvalidField("data_offset"));
    }
    let hdr_len = data_offset * 4;
    if buf.len() < hdr_len {
        return Err(ParseError::TooShort);
    }
    
    let flags_byte = buf[13];
    
    Ok(TcpHeader {
        src_port:   u16::from_be_bytes(buf[0..2].try_into().unwrap()),
        dst_port:   u16::from_be_bytes(buf[2..4].try_into().unwrap()),
        seq:        u32::from_be_bytes(buf[4..8].try_into().unwrap()),
        ack:        u32::from_be_bytes(buf[8..12].try_into().unwrap()),
        flags: TcpFlags {
            cwr: (flags_byte >> 7) & 1 == 1,
            ece: (flags_byte >> 6) & 1 == 1,
            urg: (flags_byte >> 5) & 1 == 1,
            ack: (flags_byte >> 4) & 1 == 1,
            psh: (flags_byte >> 3) & 1 == 1,
            rst: (flags_byte >> 2) & 1 == 1,
            syn: (flags_byte >> 1) & 1 == 1,
            fin: (flags_byte >> 0) & 1 == 1,
        },
        window:     u16::from_be_bytes(buf[14..16].try_into().unwrap()),
        checksum:   u16::from_be_bytes(buf[16..18].try_into().unwrap()),
        urgent_ptr: u16::from_be_bytes(buf[18..20].try_into().unwrap()),
        payload:    &buf[hdr_len..],
    })
}

// ─── IP Checksum ───────────────────────────────────────────────

pub fn ip_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;
    
    while i + 1 < data.len() {
        sum += u16::from_be_bytes([data[i], data[i+1]]) as u32;
        i += 2;
    }
    if i < data.len() {
        sum += (data[i] as u32) << 8;
    }
    while (sum >> 16) != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }
    !(sum as u16)
}

// ─── Dispatcher ────────────────────────────────────────────────

#[derive(Debug)]
pub enum PacketAction { Accept, Drop, Forward }

pub fn process_frame(raw: &[u8]) -> PacketAction {
    // Layer 2
    let eth = match parse_ethernet(raw) {
        Ok(e) => e,
        Err(e) => {
            eprintln!("Bad Ethernet: {:?}", e);
            return PacketAction::Drop;
        }
    };
    
    println!("ETH {:02X?} → {:02X?}, type=0x{:04X}",
             eth.src_mac, eth.dst_mac, eth.ethertype);
    
    match eth.ethertype {
        0x0806 => {
            println!("ARP");
            return PacketAction::Accept;
        }
        0x0800 => {} // IPv4, continue
        0x86DD => {
            println!("IPv6 (not implemented)");
            return PacketAction::Drop;
        }
        t => {
            println!("Unknown EtherType 0x{:04X}", t);
            return PacketAction::Drop;
        }
    }
    
    // Layer 3
    let (ip, l4_data) = match parse_ipv4(eth.payload) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("Bad IPv4: {:?}", e);
            return PacketAction::Drop;
        }
    };
    
    println!("IP {} → {}, proto={}, ttl={}",
             ip.src, ip.dst, ip.protocol, ip.ttl);
    
    if ip.ttl == 0 {
        println!("TTL expired");
        return PacketAction::Drop;
    }
    
    // Layer 4
    match ip.protocol {
        6 => {  // TCP
            match parse_tcp(l4_data) {
                Ok(tcp) => {
                    println!("TCP {}→{} seq={} ack={} {:?}",
                             tcp.src_port, tcp.dst_port,
                             tcp.seq, tcp.ack, tcp.flags);
                    PacketAction::Accept
                }
                Err(e) => {
                    eprintln!("Bad TCP: {:?}", e);
                    PacketAction::Drop
                }
            }
        }
        17 => { // UDP
            if l4_data.len() < 8 {
                return PacketAction::Drop;
            }
            let sp = u16::from_be_bytes(l4_data[0..2].try_into().unwrap());
            let dp = u16::from_be_bytes(l4_data[2..4].try_into().unwrap());
            println!("UDP {} → {}", sp, dp);
            PacketAction::Accept
        }
        1 => { // ICMP
            if l4_data.len() < 4 {
                return PacketAction::Drop;
            }
            println!("ICMP type={} code={}", l4_data[0], l4_data[1]);
            PacketAction::Accept
        }
        _ => {
            println!("Unknown L4 proto {}", ip.protocol);
            PacketAction::Drop
        }
    }
}
```

### Using the `pnet` Crate (Production-Ready)

```rust
// Cargo.toml:
// [dependencies]
// pnet = "0.34"
// pnet_datalink = "0.34"

use pnet::datalink::{self, NetworkInterface};
use pnet::datalink::Channel::Ethernet;
use pnet::packet::ethernet::{EthernetPacket, EtherTypes};
use pnet::packet::ipv4::Ipv4Packet;
use pnet::packet::tcp::TcpPacket;
use pnet::packet::udp::UdpPacket;
use pnet::packet::ip::IpNextHeaderProtocols;
use pnet::packet::Packet;

fn handle_ipv4_packet(ip_pkt: &Ipv4Packet) {
    println!("  IPv4: {} → {}, TTL={}, proto={:?}",
             ip_pkt.get_source(),
             ip_pkt.get_destination(),
             ip_pkt.get_ttl(),
             ip_pkt.get_next_level_protocol());
    
    match ip_pkt.get_next_level_protocol() {
        IpNextHeaderProtocols::Tcp => {
            if let Some(tcp) = TcpPacket::new(ip_pkt.payload()) {
                println!("  TCP: {} → {} [{}{}{}{}{}{}]",
                    tcp.get_source(), tcp.get_destination(),
                    if tcp.get_flags() & 0x02 != 0 {"SYN "} else {""},
                    if tcp.get_flags() & 0x10 != 0 {"ACK "} else {""},
                    if tcp.get_flags() & 0x01 != 0 {"FIN "} else {""},
                    if tcp.get_flags() & 0x04 != 0 {"RST "} else {""},
                    if tcp.get_flags() & 0x08 != 0 {"PSH "} else {""},
                    if tcp.get_flags() & 0x20 != 0 {"URG "} else {""},
                );
            }
        }
        IpNextHeaderProtocols::Udp => {
            if let Some(udp) = UdpPacket::new(ip_pkt.payload()) {
                println!("  UDP: {} → {}  len={}",
                    udp.get_source(), udp.get_destination(), udp.get_length());
            }
        }
        _ => {}
    }
}

fn main() {
    // Find interface named "eth0"
    let interfaces = datalink::interfaces();
    let interface = interfaces.into_iter()
        .find(|iface: &NetworkInterface| iface.name == "eth0")
        .expect("interface eth0 not found");
    
    // Open a datalink channel (raw Ethernet capture)
    let (_, mut rx) = match datalink::channel(&interface, Default::default()) {
        Ok(Ethernet(tx, rx)) => (tx, rx),
        _ => panic!("Failed to open channel"),
    };
    
    loop {
        match rx.next() {
            Ok(packet) => {
                if let Some(eth) = EthernetPacket::new(packet) {
                    println!("Frame: {:?} → {:?} ({:?})",
                             eth.get_source(), eth.get_destination(),
                             eth.get_ethertype());
                    match eth.get_ethertype() {
                        EtherTypes::Ipv4 => {
                            if let Some(ip) = Ipv4Packet::new(eth.payload()) {
                                handle_ipv4_packet(&ip);
                            }
                        }
                        _ => {}
                    }
                }
            }
            Err(e) => eprintln!("Error: {}", e),
        }
    }
}
```

### Zero-Copy with `zerocopy` Crate

```rust
// Cargo.toml:
// [dependencies]
// zerocopy = { version = "0.7", features = ["derive"] }
// zerocopy-derive = "0.7"

use zerocopy::{AsBytes, FromBytes, FromZeroes, BigEndian, U16, U32};

/// Direct memory-mapped struct — NO deserialization, NO copy
/// The struct IS the wire format
#[derive(Debug, FromBytes, FromZeroes, AsBytes)]
#[repr(C, packed)]
struct Ipv4HeaderWire {
    version_ihl: u8,
    dscp_ecn:    u8,
    total_len:   U16<BigEndian>,
    id:          U16<BigEndian>,
    flags_frag:  U16<BigEndian>,
    ttl:         u8,
    protocol:    u8,
    checksum:    U16<BigEndian>,
    src:         [u8; 4],
    dst:         [u8; 4],
}

fn parse_ipv4_zerocopy(buf: &[u8]) -> Option<&Ipv4HeaderWire> {
    // Cast the byte slice directly to the struct — ZERO COPY!
    // zerocopy verifies the buffer is large enough and properly aligned
    Ipv4HeaderWire::ref_from_prefix(buf).ok().map(|(hdr, _)| hdr)
}

fn demo_zerocopy(buf: &[u8]) {
    if let Some(hdr) = parse_ipv4_zerocopy(buf) {
        let version = (hdr.version_ihl >> 4) & 0xF;
        let ihl = hdr.version_ihl & 0xF;
        let total_len = hdr.total_len.get(); // reads big-endian, returns u16
        let src = std::net::Ipv4Addr::from(hdr.src);
        let dst = std::net::Ipv4Addr::from(hdr.dst);
        
        println!("IP v{}, hdrlen={}, len={}, {} → {}",
                 version, ihl * 4, total_len, src, dst);
        // hdr is a reference into buf — no allocation, no copy
    }
}
```

### Building Packets with `pnet`

```rust
use pnet::packet::ethernet::{MutableEthernetPacket, EtherTypes};
use pnet::packet::ipv4::{MutableIpv4Packet, checksum};
use pnet::packet::udp::MutableUdpPacket;
use pnet::packet::MutablePacket;
use pnet::util::MacAddr;
use std::net::Ipv4Addr;

fn build_udp_packet(
    src_mac: MacAddr, dst_mac: MacAddr,
    src_ip: Ipv4Addr, dst_ip: Ipv4Addr,
    src_port: u16, dst_port: u16,
    payload: &[u8],
) -> Vec<u8> {
    let total = 14 + 20 + 8 + payload.len();
    let mut buf = vec![0u8; total];
    
    // Build from outer to inner, filling each layer's slice
    
    // Ethernet
    let mut eth = MutableEthernetPacket::new(&mut buf[..14]).unwrap();
    eth.set_destination(dst_mac);
    eth.set_source(src_mac);
    eth.set_ethertype(EtherTypes::Ipv4);
    
    // IPv4
    {
        let mut ip = MutableIpv4Packet::new(&mut buf[14..14+20+8+payload.len()]).unwrap();
        ip.set_version(4);
        ip.set_header_length(5);
        ip.set_total_length((20 + 8 + payload.len()) as u16);
        ip.set_ttl(64);
        ip.set_next_level_protocol(pnet::packet::ip::IpNextHeaderProtocols::Udp);
        ip.set_source(src_ip);
        ip.set_destination(dst_ip);
        ip.set_checksum(checksum(&ip.to_immutable()));
    }
    
    // UDP
    {
        let mut udp = MutableUdpPacket::new(&mut buf[14+20..]).unwrap();
        udp.set_source(src_port);
        udp.set_destination(dst_port);
        udp.set_length((8 + payload.len()) as u16);
        udp.set_payload(payload);
        let cs = pnet::packet::udp::ipv4_checksum(
            &udp.to_immutable(), &src_ip, &dst_ip);
        udp.set_checksum(cs);
    }
    
    buf
}
```

---

## 14. Go Implementation

### Packet Parsing in Go

```go
package main

import (
    "encoding/binary"
    "fmt"
    "net"
)

// ─── Read helpers ─────────────────────────────────────────────

func readU16BE(b []byte, off int) uint16 {
    return binary.BigEndian.Uint16(b[off : off+2])
}

func readU32BE(b []byte, off int) uint32 {
    return binary.BigEndian.Uint32(b[off : off+4])
}

// ─── Ethernet ─────────────────────────────────────────────────

type EthernetHeader struct {
    Dst       net.HardwareAddr
    Src       net.HardwareAddr
    EtherType uint16
}

func ParseEthernet(buf []byte) (*EthernetHeader, []byte, error) {
    if len(buf) < 14 {
        return nil, nil, fmt.Errorf("ethernet: too short (%d bytes)", len(buf))
    }
    hdr := &EthernetHeader{
        Dst:       net.HardwareAddr(append([]byte(nil), buf[0:6]...)),
        Src:       net.HardwareAddr(append([]byte(nil), buf[6:12]...)),
        EtherType: readU16BE(buf, 12),
    }
    payload := buf[14:]
    
    // 802.1Q VLAN tag
    if hdr.EtherType == 0x8100 {
        if len(buf) < 18 {
            return nil, nil, fmt.Errorf("ethernet: too short for VLAN tag")
        }
        hdr.EtherType = readU16BE(buf, 16)
        payload = buf[18:]
    }
    return hdr, payload, nil
}

// ─── IPv4 ──────────────────────────────────────────────────────

type IPv4Header struct {
    Version    uint8
    IHL        uint8  // in 32-bit words
    DSCP       uint8
    ECN        uint8
    TotalLen   uint16
    ID         uint16
    DontFrag   bool
    MoreFrags  bool
    FragOffset uint16 // in bytes
    TTL        uint8
    Protocol   uint8
    Checksum   uint16
    Src        net.IP
    Dst        net.IP
    HeaderLen  int // in bytes
}

func ParseIPv4(buf []byte) (*IPv4Header, []byte, error) {
    if len(buf) < 20 {
        return nil, nil, fmt.Errorf("ipv4: too short")
    }
    
    version := (buf[0] >> 4) & 0x0F
    ihl := buf[0] & 0x0F
    
    if version != 4 {
        return nil, nil, fmt.Errorf("ipv4: invalid version %d", version)
    }
    if ihl < 5 {
        return nil, nil, fmt.Errorf("ipv4: invalid IHL %d", ihl)
    }
    
    hdrLen := int(ihl) * 4
    if len(buf) < hdrLen {
        return nil, nil, fmt.Errorf("ipv4: buffer too short for header")
    }
    
    // Verify checksum
    if cksum := IPChecksum(buf[:hdrLen]); cksum != 0 {
        return nil, nil, fmt.Errorf("ipv4: bad checksum (got 0x%04X, want 0x0000)", cksum)
    }
    
    flagsFrag := readU16BE(buf, 6)
    
    hdr := &IPv4Header{
        Version:    version,
        IHL:        ihl,
        DSCP:       (buf[1] >> 2) & 0x3F,
        ECN:        buf[1] & 0x03,
        TotalLen:   readU16BE(buf, 2),
        ID:         readU16BE(buf, 4),
        DontFrag:   (flagsFrag>>14)&1 == 1,
        MoreFrags:  (flagsFrag>>13)&1 == 1,
        FragOffset: (flagsFrag & 0x1FFF) * 8,
        TTL:        buf[8],
        Protocol:   buf[9],
        Checksum:   readU16BE(buf, 10),
        Src:        net.IP(append([]byte(nil), buf[12:16]...)),
        Dst:        net.IP(append([]byte(nil), buf[16:20]...)),
        HeaderLen:  hdrLen,
    }
    return hdr, buf[hdrLen:], nil
}

// ─── TCP ───────────────────────────────────────────────────────

type TCPFlags struct {
    CWR, ECE, URG, ACK, PSH, RST, SYN, FIN bool
}

type TCPHeader struct {
    SrcPort    uint16
    DstPort    uint16
    SeqNum     uint32
    AckNum     uint32
    Flags      TCPFlags
    Window     uint16
    Checksum   uint16
    UrgentPtr  uint16
    HeaderLen  int
}

func ParseTCP(buf []byte) (*TCPHeader, []byte, error) {
    if len(buf) < 20 {
        return nil, nil, fmt.Errorf("tcp: too short")
    }
    
    dataOffset := int((buf[12] >> 4) & 0x0F)
    if dataOffset < 5 {
        return nil, nil, fmt.Errorf("tcp: invalid data offset %d", dataOffset)
    }
    hdrLen := dataOffset * 4
    if len(buf) < hdrLen {
        return nil, nil, fmt.Errorf("tcp: buffer too short for header")
    }
    
    flags := buf[13]
    hdr := &TCPHeader{
        SrcPort:   readU16BE(buf, 0),
        DstPort:   readU16BE(buf, 2),
        SeqNum:    readU32BE(buf, 4),
        AckNum:    readU32BE(buf, 8),
        Flags: TCPFlags{
            CWR: (flags>>7)&1 == 1,
            ECE: (flags>>6)&1 == 1,
            URG: (flags>>5)&1 == 1,
            ACK: (flags>>4)&1 == 1,
            PSH: (flags>>3)&1 == 1,
            RST: (flags>>2)&1 == 1,
            SYN: (flags>>1)&1 == 1,
            FIN: (flags>>0)&1 == 1,
        },
        Window:    readU16BE(buf, 14),
        Checksum:  readU16BE(buf, 16),
        UrgentPtr: readU16BE(buf, 18),
        HeaderLen: hdrLen,
    }
    return hdr, buf[hdrLen:], nil
}

// ─── IP Checksum ───────────────────────────────────────────────

func IPChecksum(data []byte) uint16 {
    var sum uint32
    for i := 0; i+1 < len(data); i += 2 {
        sum += uint32(binary.BigEndian.Uint16(data[i : i+2]))
    }
    if len(data)%2 == 1 {
        sum += uint32(data[len(data)-1]) << 8
    }
    for sum>>16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16)
    }
    return ^uint16(sum)
}

// ─── Packet Dispatcher ─────────────────────────────────────────

type Action int

const (
    ActionAccept  Action = iota
    ActionDrop
    ActionForward
)

func ProcessFrame(raw []byte) Action {
    eth, payload, err := ParseEthernet(raw)
    if err != nil {
        fmt.Printf("Bad ethernet: %v\n", err)
        return ActionDrop
    }
    fmt.Printf("ETH: %v → %v, type=0x%04X\n",
        eth.Src, eth.Dst, eth.EtherType)
    
    switch eth.EtherType {
    case 0x0806:
        fmt.Println("ARP")
        return ActionAccept
    case 0x0800:
        // IPv4, continue
    case 0x86DD:
        fmt.Println("IPv6 (not implemented)")
        return ActionDrop
    default:
        fmt.Printf("Unknown EtherType 0x%04X\n", eth.EtherType)
        return ActionDrop
    }
    
    ip, l4data, err := ParseIPv4(payload)
    if err != nil {
        fmt.Printf("Bad IPv4: %v\n", err)
        return ActionDrop
    }
    fmt.Printf("IP: %v → %v, proto=%d, ttl=%d\n",
        ip.Src, ip.Dst, ip.Protocol, ip.TTL)
    
    if ip.TTL == 0 {
        fmt.Println("TTL expired → drop")
        return ActionDrop
    }
    
    switch ip.Protocol {
    case 6: // TCP
        tcp, data, err := ParseTCP(l4data)
        if err != nil {
            fmt.Printf("Bad TCP: %v\n", err)
            return ActionDrop
        }
        fmt.Printf("TCP: %d → %d, seq=%d, ack=%d, payload=%d bytes\n",
            tcp.SrcPort, tcp.DstPort, tcp.SeqNum, tcp.AckNum, len(data))
        fmt.Printf("  flags: CWR=%v ECE=%v URG=%v ACK=%v PSH=%v RST=%v SYN=%v FIN=%v\n",
            tcp.Flags.CWR, tcp.Flags.ECE, tcp.Flags.URG, tcp.Flags.ACK,
            tcp.Flags.PSH, tcp.Flags.RST, tcp.Flags.SYN, tcp.Flags.FIN)
    case 17: // UDP
        if len(l4data) < 8 {
            return ActionDrop
        }
        sp := readU16BE(l4data, 0)
        dp := readU16BE(l4data, 2)
        ln := readU16BE(l4data, 4)
        fmt.Printf("UDP: %d → %d, len=%d\n", sp, dp, ln)
    case 1: // ICMP
        if len(l4data) >= 4 {
            fmt.Printf("ICMP: type=%d, code=%d\n", l4data[0], l4data[1])
        }
    default:
        fmt.Printf("Unknown L4 proto %d\n", ip.Protocol)
        return ActionDrop
    }
    return ActionAccept
}
```

### Raw Packet Capture with `gopacket`

```go
package main

import (
    "fmt"
    "log"
    "github.com/google/gopacket"
    "github.com/google/gopacket/layers"
    "github.com/google/gopacket/pcap"
)

func main() {
    // Open device for live capture
    handle, err := pcap.OpenLive("eth0", 65536, true, pcap.BlockForever)
    if err != nil {
        log.Fatal(err)
    }
    defer handle.Close()
    
    // Optional: set BPF filter
    if err := handle.SetBPFFilter("tcp and port 80"); err != nil {
        log.Fatal(err)
    }
    
    packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
    
    for packet := range packetSource.Packets() {
        // gopacket lazily decodes layers
        
        // Access Ethernet layer
        if ethLayer := packet.Layer(layers.LayerTypeEthernet); ethLayer != nil {
            eth, _ := ethLayer.(*layers.Ethernet)
            fmt.Printf("ETH: %v → %v, type=%v\n",
                eth.SrcMAC, eth.DstMAC, eth.EthernetType)
        }
        
        // Access IP layer
        if ipLayer := packet.Layer(layers.LayerTypeIPv4); ipLayer != nil {
            ip, _ := ipLayer.(*layers.IPv4)
            fmt.Printf("IP: %v → %v, TTL=%d, proto=%v\n",
                ip.SrcIP, ip.DstIP, ip.TTL, ip.Protocol)
        }
        
        // Access TCP layer
        if tcpLayer := packet.Layer(layers.LayerTypeTCP); tcpLayer != nil {
            tcp, _ := tcpLayer.(*layers.TCP)
            fmt.Printf("TCP: %d → %d, SYN=%v, ACK=%v, seq=%d\n",
                tcp.SrcPort, tcp.DstPort, tcp.SYN, tcp.ACK, tcp.Seq)
            fmt.Printf("  Payload: %q\n", tcp.Payload)
        }
        
        // Access UDP layer
        if udpLayer := packet.Layer(layers.LayerTypeUDP); udpLayer != nil {
            udp, _ := udpLayer.(*layers.UDP)
            fmt.Printf("UDP: %d → %d\n", udp.SrcPort, udp.DstPort)
        }
        
        // Application layer data
        if app := packet.ApplicationLayer(); app != nil {
            fmt.Printf("Application: %d bytes\n", len(app.Payload()))
        }
        
        // Any errors?
        if err := packet.ErrorLayer(); err != nil {
            fmt.Printf("Error decoding: %v\n", err.Error())
        }
    }
}
```

### Building a Packet with `encoding/binary`

```go
package main

import (
    "bytes"
    "encoding/binary"
    "fmt"
    "net"
)

// Build raw UDP datagram (IP + UDP, no Ethernet)
func BuildUDPDatagram(
    srcIP, dstIP net.IP,
    srcPort, dstPort uint16,
    payload []byte,
) []byte {
    udpLen := uint16(8 + len(payload))
    ipLen  := uint16(20 + int(udpLen))
    
    buf := &bytes.Buffer{}
    
    // ── IP Header ──────────────────────────────────────
    buf.WriteByte(0x45)              // version=4, IHL=5
    buf.WriteByte(0x00)              // DSCP+ECN
    binary.Write(buf, binary.BigEndian, ipLen)
    binary.Write(buf, binary.BigEndian, uint16(0x1234)) // ID
    binary.Write(buf, binary.BigEndian, uint16(1<<14))  // DF flag
    buf.WriteByte(64)                // TTL
    buf.WriteByte(17)                // Protocol=UDP
    binary.Write(buf, binary.BigEndian, uint16(0)) // checksum placeholder
    buf.Write(srcIP.To4())
    buf.Write(dstIP.To4())
    
    // Fill in IP checksum
    ipHdr := buf.Bytes()[:20]
    cs := IPChecksum(ipHdr)
    ipHdr[10] = byte(cs >> 8)
    ipHdr[11] = byte(cs & 0xFF)
    
    // ── UDP Header ─────────────────────────────────────
    binary.Write(buf, binary.BigEndian, srcPort)
    binary.Write(buf, binary.BigEndian, dstPort)
    binary.Write(buf, binary.BigEndian, udpLen)
    binary.Write(buf, binary.BigEndian, uint16(0)) // checksum=0 (optional in IPv4)
    
    // ── Payload ────────────────────────────────────────
    buf.Write(payload)
    
    return buf.Bytes()
}
```

### Go's `net.Listen` and how the kernel does the work underneath

```go
// When you write:
listener, _ := net.Listen("tcp", ":8080")
conn, _ := listener.Accept()
data := make([]byte, 1500)
n, _ := conn.Read(data)

// The kernel:
//  1. socket() syscall → creates TCP socket fd
//  2. bind() → associates with port 8080 on all interfaces
//  3. listen() → puts socket in LISTEN state, sets backlog queue
//  4. accept() syscall (blocks) → waits for SYN in tcp_v4_rcv()
//
// When SYN arrives:
//  tcp_v4_rcv() → tcp_rcv_state_process()
//    LISTEN state → sends SYN-ACK
//    half-open connection queued in request_sock queue
//  When ACK arrives → connection moved to accept queue
//  accept() syscall returns fd for new connected socket
//
// conn.Read(data):
//  read() syscall → tcp_recvmsg()
//    copies from sk->sk_receive_queue (sk_buff chain) to userspace buffer
//    if empty: blocks until data arrives (or returns EAGAIN for non-blocking)
```

---

## 15. Checksums — Theory and Implementation

### IP Header Checksum (One's Complement)

The algorithm:
1. Set checksum field to 0
2. Sum all 16-bit words of the header as unsigned 16-bit integers, using **one's complement** addition (i.e. add carry back in)
3. Store the one's complement (bitwise NOT) of the sum

Verification: sum all 16-bit words **including** the checksum field. Result should be 0xFFFF (all ones).

```c
// One's complement sum
uint16_t ip_cksum(const uint16_t *data, int nwords) {
    uint32_t sum = 0;
    for (int i = 0; i < nwords; i++)
        sum += ntohs(data[i]);
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);
    return ~sum & 0xFFFF;
}
```

### TCP/UDP Checksum (Pseudo-Header)

TCP and UDP checksums cover a **pseudo-header** that includes IP fields to prevent misdelivered packets:

```
IPv4 Pseudo-Header:
┌─────────────────────────────────────────────┐
│            Source IP Address (32 bits)      │
├─────────────────────────────────────────────┤
│         Destination IP Address (32 bits)    │
├────────────┬────────────────┬───────────────┤
│  Zeros (8) │  Protocol (8)  │  Length (16)  │
└────────────┴────────────────┴───────────────┘
Then append the TCP/UDP header + data.
Compute one's complement sum over all of it.

IPv6 Pseudo-Header (40 bytes):
  Source address (128 bits)
  Destination address (128 bits)
  Upper-Layer packet length (32 bits)
  Zero (24 bits)
  Next Header (8 bits) = protocol
```

### Incremental Checksum Update (Used in NAT)

When NAT changes an IP field, it updates the checksum without recomputing from scratch:

```c
// RFC 1624 incremental checksum update
// Old checksum: HC
// Old field value: m (old)
// New field value: m' (new)
// New checksum:
//   HC' = ~(~HC + ~m + m')
//
// In practice, for NAT changing src IP:
uint16_t update_checksum(uint16_t old_ck, uint32_t old_val, uint32_t new_val)
{
    uint32_t sum = (uint16_t)~old_ck;
    sum += (uint16_t)(~old_val >> 16) + (uint16_t)~old_val;
    sum += (uint16_t)(new_val >> 16)  + (uint16_t)new_val;
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);
    return ~sum;
}
```

### Hardware Checksum Offload

```c
// In Linux kernel sk_buff:
// ip_summed values:
CHECKSUM_NONE        // No hardware assistance; software must verify/compute
CHECKSUM_UNNECESSARY // NIC verified checksum; software can skip verification
CHECKSUM_COMPLETE    // NIC computed a full checksum; stored in skb->csum
CHECKSUM_PARTIAL     // SW filled in pseudo-header; NIC will fill actual checksum on TX

// For TX path:
skb->ip_summed = CHECKSUM_PARTIAL;
skb->csum_start = (unsigned char *)tcp_hdr(skb) - skb->head;
skb->csum_offset = offsetof(struct tcphdr, check);
// NIC computes TCP checksum from csum_start to end of packet
// and stores at csum_start + csum_offset
```

---

## 16. Raw Sockets and Packet Sockets (Linux)

### Socket Types

```c
// L2 raw socket (all Ethernet frames, requires root/CAP_NET_RAW):
int s = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
// Receives full Ethernet frames including headers
// You can also SEND arbitrary Ethernet frames

// L2 cooked socket (no Ethernet header on recv):
int s = socket(AF_PACKET, SOCK_DGRAM, htons(ETH_P_IP));

// L3 raw socket (IP layer, no Ethernet header):
int s = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
// Receives IP datagrams (with IP header)
// On send: you provide IP header (with IP_HDRINCL option)

// With IP_HDRINCL (you control the entire IP datagram):
int one = 1;
setsockopt(s, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));
```

### MMAP Packet Socket (AF_PACKET + TPACKET_V3) — Zero-Copy Capture

```c
// Set up a memory-mapped ring buffer for packet capture
// Much faster than recv() for high-throughput capture

struct tpacket_req3 req = {
    .tp_block_size  = 1 << 22,   // 4MB per block
    .tp_block_nr    = 64,         // 64 blocks = 256MB total
    .tp_frame_size  = 1 << 11,   // 2048 bytes per frame
    .tp_frame_nr    = (1<<22)/(1<<11) * 64,
    .tp_retire_blk_tov = 60,     // block retire timeout ms
    .tp_feature_req_word = TP_FT_REQ_FILL_RXHASH,
};

setsockopt(s, SOL_PACKET, PACKET_RX_RING, &req, sizeof(req));

// mmap the ring buffer
void *ring = mmap(NULL, req.tp_block_size * req.tp_block_nr,
                  PROT_READ|PROT_WRITE, MAP_SHARED|MAP_LOCKED, s, 0);

// Kernel DMA's packets directly into this mmap'd area
// Userspace reads from ring buffer without syscall
// poll() to wait for new blocks:
struct pollfd pfd = { .fd = s, .events = POLLIN };
poll(&pfd, 1, -1);

// Walk the ring:
struct tpacket_block_desc *block = ring;
struct tpacket3_hdr *pkt = (void*)block + block->hdr.bh1.offset_to_first_pkt;
// pkt->tp_mac = offset to Ethernet header
// pkt->tp_net = offset to IP header
```

---

## 17. eBPF/XDP Fast Path

### XDP (eXpress Data Path)

XDP runs BPF programs at the earliest point in the receive path — in the **driver's interrupt/NAPI poll context**, before sk_buff is even allocated. This makes it extremely fast.

```
Wire
 │
 ▼
NIC DMA (bytes in memory)
 │
 ▼
XDP Program (eBPF, runs in NIC driver's NAPI poll)
 │   Has access to: xdp_md->data, xdp_md->data_end, xdp_md->data_meta
 │
 ├─ XDP_DROP      → free buffer immediately, NIC re-use
 ├─ XDP_PASS      → continue to normal sk_buff path
 ├─ XDP_TX        → transmit back out the same NIC (zero-copy bounce)
 ├─ XDP_REDIRECT  → redirect to another NIC, CPU queue, or AF_XDP socket
 └─ XDP_ABORTED   → drop + increment counter (for debugging)
```

### XDP Program in C (loaded via libbpf)

```c
// xdp_filter.c — compiled with clang to BPF bytecode
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Helper: bounds check (mandatory in BPF verifier)
#define CHECK_BOUNDS(ctx, ptr, size) \
    if ((void *)(ptr) + (size) > (void *)(ctx)->data_end) \
        return XDP_DROP;

SEC("xdp")
int xdp_packet_filter(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // ── Ethernet ──────────────────────────────────────
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;
    
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;
    
    // ── IPv4 ──────────────────────────────────────────
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_DROP;
    
    // Drop all traffic from 10.0.0.1
    if (ip->saddr == bpf_htonl(0x0A000001))
        return XDP_DROP;
    
    // TTL check
    if (ip->ttl == 0)
        return XDP_DROP;
    
    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;
    
    // ── TCP ───────────────────────────────────────────
    // IP header length from IHL field
    __u32 ip_hdrlen = ip->ihl * 4;
    struct tcphdr *tcp = (void *)ip + ip_hdrlen;
    if ((void *)(tcp + 1) > data_end)
        return XDP_DROP;
    
    // Block SYN flood: drop SYN packets to port 80 from unknown sources
    if (tcp->syn && !tcp->ack && bpf_ntohs(tcp->dest) == 80) {
        // In a real firewall, check a BPF map for allowed IPs
        // bpf_map_lookup_elem(&allowed_ips, &ip->saddr)
        return XDP_DROP;
    }
    
    return XDP_PASS;
}

// BPF map for statistics
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 4);
    __type(key, __u32);
    __type(value, __u64);
} stats_map SEC(".maps");

char _license[] SEC("license") = "GPL";
```

### Loading XDP with iproute2

```bash
# Compile:
clang -O2 -target bpf -c xdp_filter.c -o xdp_filter.o

# Load onto interface (native mode = driver supports XDP):
ip link set eth0 xdp obj xdp_filter.o sec xdp

# Generic mode (works on any driver, slower):
ip link set eth0 xdp generic obj xdp_filter.o sec xdp

# Remove:
ip link set eth0 xdp off

# Check:
ip link show eth0
# Output will show: prog/xdp id 42 ...
```

### eBPF TC (Traffic Control) — Bidirectional, After sk_buff

```c
// tc_filter.c — runs AFTER sk_buff allocation, can modify packets
#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>

SEC("tc")
int tc_ingress(struct __sk_buff *skb)
{
    // bpf_skb_load_bytes: safely read from sk_buff
    struct iphdr ip;
    if (bpf_skb_load_bytes(skb, sizeof(struct ethhdr), &ip, sizeof(ip)) < 0)
        return TC_ACT_SHOT;  // drop
    
    if (ip.protocol == IPPROTO_TCP) {
        // Can modify packet fields:
        // bpf_skb_store_bytes(skb, offset, &new_val, sizeof(new_val), flags);
        // bpf_l3_csum_replace(), bpf_l4_csum_replace() for checksum fixup
    }
    
    return TC_ACT_OK;  // pass to next handler
    // TC_ACT_SHOT: drop
    // TC_ACT_REDIRECT: redirect to another interface
    // TC_ACT_STOLEN: tc takes ownership, don't process further
}
```

### AF_XDP (Zero-Copy to Userspace)

```c
// AF_XDP provides a ring-buffer interface from kernel to userspace
// that completely bypasses the socket layer.
// Packets are DMA'd to userspace-mapped memory.

// Regions:
//   UMEM: large userspace memory area for packet buffers
//   RX ring: kernel writes completed received frame addresses
//   TX ring: userspace writes frames to transmit
//   Fill ring: userspace provides free UMEM chunks to kernel
//   Completion ring: kernel marks transmitted frames as done

// This is how DPDK-like performance is achieved within the kernel model.
// Used by: Cilium, Katran (Facebook LB), Cloudflare, snort3, etc.
```

---

## 18. DPDK and Kernel Bypass

DPDK (Data Plane Development Kit) completely bypasses the kernel network stack:

```
Normal kernel path:
  NIC IRQ → kernel ISR → NAPI → netfilter → socket → syscall → userspace
  Latency: ~10-100μs, ~5M pps per core

DPDK path:
  NIC (poll mode driver) ← userspace thread polls NIC registers directly
  NIC DMA → DPDK mempool (huge pages, NUMA-aware)
  Userspace thread processes packets directly in tight loop
  Latency: ~1-5μs, ~20-80M pps per core

How it works:
  1. DPDK driver binds NIC via vfio-pci (uses IOMMU, bypasses kernel driver)
  2. Userspace maps NIC registers via /dev/vfio
  3. DPDK allocates hugepage memory as packet buffers
  4. PMD (Poll Mode Driver) polls NIC TX/RX rings in busy-loop
  5. No interrupts, no context switches, no sk_buff overhead

Cost: that CPU core is 100% dedicated to packet processing
      kernel can no longer use the NIC for normal networking

rte_mbuf (DPDK's equivalent of sk_buff):
  Contains: buffer pointer, data offset, data length, port, flags
  Arranged in mempool for fast allocation/deallocation
```

---

## 19. Common Bugs and Pitfalls

### 1. Missing ntohs/ntohl (Endianness Bug)

```c
// BUG: port 80 on x86 is stored as 0x5000 in memory
if (udp->dest == 80) { ... }  // WRONG on little-endian!

// FIX:
if (ntohs(udp->dest) == 80) { ... }  // CORRECT
// OR compare in network byte order:
if (udp->dest == htons(80)) { ... }  // CORRECT
```

### 2. Not Validating Lengths Before Dereferencing

```c
// BUG: crash if packet is truncated
struct iphdr *ip = (struct iphdr *)buf;
printf("%d\n", ip->ttl);  // BUG if buf is only 5 bytes!

// FIX:
if (buf_len < sizeof(struct iphdr)) return -1;
if (buf_len < ip->ihl * 4) return -1;  // also check IHL value!
```

### 3. Integer Overflow in Length Calculation

```c
// BUG: ihl could be 0-15, uint8_t; if ihl=0 after cast, 0*4=0
// but ip_hdrlen is often uint8_t and ihl*4 could be 60,
// which fits in uint8_t, but the comparison might not work if len is int:
uint8_t ip_hdrlen = ip->ihl * 4;  // safe since max is 60
// But:
int data_offset = (buf[12] >> 4) & 0xF;
int header_len = data_offset * 4;  // safe

// BUG in total length:
uint16_t total = ntohs(ip->tot_len);
if (total < 20 || total > buf_len) ... // buf_len might be size_t (unsigned)
// if buf_len > 65535, comparison with uint16_t total is fine
// but: total - 20 could underflow if total < 20 and you use it as unsigned
```

### 4. Struct Alignment and Unaligned Access

```c
// BUG on architectures requiring alignment (ARM, MIPS without unaligned access):
uint8_t *buf = /* odd address */;
struct iphdr *ip = (struct iphdr *)buf;  // UB: unaligned pointer!
uint16_t len = ip->tot_len;  // crash on strict-alignment CPUs

// FIX 1: use memcpy
uint16_t len;
memcpy(&len, buf + 2, 2);
len = ntohs(len);

// FIX 2: use __attribute__((packed)) on the struct so compiler uses byte accesses
// FIX 3: ensure buffer is aligned (e.g. allocate with alignas(4))
```

### 5. Forgetting to Check Fragment Offset

```c
// BUG: trying to read TCP header from a fragment that doesn't start at offset 0
if (ip->protocol == IPPROTO_TCP) {
    struct tcphdr *tcp = (struct tcphdr *)(buf + ip->ihl*4);
    // BUG: fragment with frag_offset > 0 has no TCP header!
}

// FIX:
if (ip->frag_off & htons(IP_OFFMASK)) {
    // This is a non-first fragment — no L4 header
    // Queue for reassembly
    return;
}
```

### 6. IP Checksum Computed with Non-Zero Checksum Field

```c
// BUG: forgetting to zero checksum before computing
struct iphdr *ip = ...;
ip->saddr = new_ip;
ip->check = ip_checksum(ip, ip->ihl*4);  // BUG! old checksum still in field

// FIX:
ip->check = 0;  // MUST zero first
ip->check = ip_checksum(ip, ip->ihl*4);
```

### 7. Buffer Overwrite in Packet Build

```c
// BUG: writing past end of buffer (classic buffer overflow)
uint8_t pkt[100];
memcpy(pkt + 14 + 20, data, data_len);  // BUG if data_len > 66!

// FIX: always check:
assert(14 + 20 + data_len <= sizeof(pkt));
```

### 8. Race Condition in Ring Buffer

```c
// BUG in driver: read descriptor BEFORE memory barrier
// NIC writes data to buffer, then writes "done" status to descriptor
// CPU might see "done" before seeing the data (CPU/compiler reorder)

// FIX: use memory barrier
if (desc->status & DESC_DONE) {
    rmb();  // read memory barrier: ensure data is visible after status
    process(nic->rx_bufs[idx]);
}
```

---

## 20. Mental Models Summary

### The Big Picture Mental Model

```
TRANSMIT:
  Application
    │ write bytes (protocol messages)
    ▼
  Socket (kernel)
    │ prepend TCP header
    ▼
  TCP layer
    │ prepend IP header, fragment if needed
    ▼
  IP layer
    │ look up route, ARP for MAC
    ▼
  Ethernet layer
    │ prepend Ethernet header
    ▼
  NIC ring buffer
    │ DMA bytes to NIC
    ▼
  NIC hardware → bits on wire → PHY → medium

RECEIVE (mirror):
  PHY → NIC → FCS check → DMA to ring buffer
    │ interrupt/NAPI
    ▼
  Ethernet driver
    │ validate, strip Ethernet header, set skb->protocol
    ▼
  ip_rcv()
    │ validate, route, strip IP header
    ▼
  tcp_v4_rcv() / udp_rcv() / icmp_rcv()
    │ validate, look up socket, strip L4 header
    ▼
  Socket receive queue
    │ user calls read()
    ▼
  Application reads bytes
```

### Key Principles

1. **A packet is bytes at an offset.** Every field is `buf + offset`, read with the right size and byte-order conversion.

2. **Always bounds-check before reading.** `if (offset + n > len) return error;` is your most important line of code.

3. **Network byte order is big-endian.** Call `ntohs`/`ntohl` when reading multi-byte fields on little-endian systems (x86), and `htons`/`htonl` when writing.

4. **The NIC sends bits; you send bytes.** You never deal with individual bits on the wire. You deal with bytes in memory organized by the protocol spec.

5. **Headers are prepended, not appended.** On TX, each layer prepends its header (using headroom). On RX, each layer strips its header by advancing the data pointer.

6. **Zero-copy means sharing a pointer.** sk_buff holds a pointer into the DMA buffer; protocol layers advance that pointer rather than copying.

7. **The checksum is the guard.** Always verify checksums on receive before doing anything with the data. Always zero the checksum field before computing it on transmit.

8. **NAPI amortizes interrupt cost.** At high packet rates, polling beats per-packet interrupts.

9. **XDP/BPF = decision before allocation.** If you need to drop, rate-limit, or redirect at line rate, do it before sk_buff is allocated.

10. **Byte order bugs are silent.** `port == 80` looks right but is wrong on little-endian without `htons`. The code compiles and runs; only behavior differs.

---

## References and Further Reading

- **RFC 791**: Internet Protocol (IPv4)
- **RFC 793**: Transmission Control Protocol (TCP)
- **RFC 768**: User Datagram Protocol (UDP)
- **RFC 826**: Address Resolution Protocol (ARP)
- **RFC 792**: Internet Control Message Protocol (ICMP)
- **RFC 8200**: IPv6
- **IEEE 802.3**: Ethernet standard
- **Linux kernel source**: `net/ipv4/`, `net/core/`, `include/linux/skbuff.h`
- **Linux Device Drivers (LDD3)**: Chapter on Network Drivers
- **"TCP/IP Illustrated, Vol 1"** — W. Richard Stevens
- **"Understanding Linux Network Internals"** — Christian Benvenuti
- **DPDK documentation**: https://doc.dpdk.org
- **libbpf/BPF docs**: https://docs.kernel.org/bpf/
- **Wireshark**: best tool for watching real protocol bytes on wire
- **`ip`, `tc`, `ss`, `netstat`, `ethtool`**: Linux network utilities
- **`tcpdump -XX`**: shows hex dump of real packets