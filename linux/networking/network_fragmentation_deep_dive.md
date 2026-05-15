# Network Fragmentation: A Complete, Layer-by-Layer Deep Dive

> **What happens when you send a 1 GB file over the network?**
> Who splits it? Who reassembles it? What code runs? What data structures exist?
> This guide answers every one of those questions, from silicon to socket.

---

## Table of Contents

1. [The Mental Model: Why Fragmentation Exists](#1-the-mental-model-why-fragmentation-exists)
2. [The Stack at a Glance](#2-the-stack-at-a-glance)
3. [Layer 1 — Physical: Bits and Signal Boundaries](#3-layer-1--physical-bits-and-signal-boundaries)
4. [Layer 2 — Data Link: Frames and the MTU](#4-layer-2--data-link-frames-and-the-mtu)
5. [Layer 3 — Network: IP Fragmentation](#5-layer-3--network-ip-fragmentation)
6. [Layer 4 — Transport: TCP Segmentation and UDP](#6-layer-4--transport-tcp-segmentation-and-udp)
7. [Layer 5-7 — Application: Chunking and Protocol Framing](#7-layer-5-7--application-chunking-and-protocol-framing)
8. [The Linux Kernel Code Path: Sending a 1 GB File](#8-the-linux-kernel-code-path-sending-a-1-gb-file)
9. [The Linux Kernel Code Path: Receiving Side](#9-the-linux-kernel-code-path-receiving-side)
10. [Hardware Offloading: TSO, GSO, GRO, LRO, UFO](#10-hardware-offloading-tso-gso-gro-lro-ufo)
11. [Path MTU Discovery (PMTUD)](#11-path-mtu-discovery-pmtud)
12. [C: Raw Socket and IP Fragmentation Implementation](#12-c-raw-socket-and-ip-fragmentation-implementation)
13. [Rust: Building a UDP Chunker and TCP Stream Handler](#13-rust-building-a-udp-chunker-and-tcp-stream-handler)
14. [Go: Implementing Fragmentation-Aware File Transfer](#14-go-implementing-fragmentation-aware-file-transfer)
15. [Key Data Structures Reference](#15-key-data-structures-reference)
16. [Common Pitfalls and Debugging](#16-common-pitfalls-and-debugging)
17. [Mental Model Summary](#17-mental-model-summary)

---

## 1. The Mental Model: Why Fragmentation Exists

Every physical medium — copper wire, fiber, radio — has a **maximum frame size** it can carry in one shot. This is called the **Maximum Transmission Unit (MTU)**. You cannot "just send 1 GB" over Ethernet any more than you can mail a car in one envelope. The car must be disassembled, each part packed into a separate box, each box labeled with a sequence number, and the receiver must reassemble everything in order.

This disassembly and reassembly happens at **multiple layers of the network stack simultaneously**, each layer unaware of what the layers above and below are doing — except where they deliberately negotiate.

```
YOU SEND:    [  1,073,741,824 bytes — 1 GB file  ]
             |
             v
APP LAYER:   [chunk 1][chunk 2][chunk 3]...[chunk N]     (e.g., 64KB chunks in HTTP)
             |
             v
TCP LAYER:   [seg 1][seg 2]...[seg M]                    (e.g., 1460 bytes per seg)
             |
             v
IP LAYER:    [pkt 1][pkt 2]...[pkt M]                   (each fits in MTU, usually no IP frag w/ TCP)
             |
             v
ETHERNET:    [frame 1][frame 2]...[frame M]              (max 1500 bytes payload per frame)
             |
             v
WIRE:        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~          (electrical/optical signals)
```

The key insight: **fragmentation is layered, and responsibility is explicitly separated**:

| Layer | What it splits | Unit name | Who reassembles |
|-------|---------------|-----------|-----------------|
| Application | File / stream | Chunk / message | Application receiver |
| TCP | Byte stream | Segment | TCP receiver (kernel) |
| IP | Datagram | Fragment | IP receiver (kernel) |
| Ethernet | Frame | Nothing (MTU enforced) | N/A |

---

## 2. The Stack at a Glance

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        YOUR APPLICATION                             │
 │         send(fd, buffer, 1GB, 0)  or  write(fd, buf, len)           │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │  system call boundary (int 0x80 / syscall)
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │                     SOCKET LAYER  (sock.c)                          │
 │    struct socket → struct sock → sk_buff (skb) allocation           │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │               TCP / UDP LAYER  (tcp.c / udp.c)                      │
 │    TCP: tcp_sendmsg() → tcp_write_xmit() → tcp_transmit_skb()       │
 │    Splits data into MSS-sized segments, adds TCP header              │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │                   IP LAYER  (ip_output.c)                           │
 │    ip_queue_xmit() → ip_finish_output() → ip_fragment()             │
 │    Adds IP header; fragments if datagram > MTU (rarely needed w/TCP)│
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │               NETFILTER / IPTABLES  (nf_*.c)                        │
 │    Hooks: PRE_ROUTING, LOCAL_IN, FORWARD, LOCAL_OUT, POST_ROUTING   │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │             NETWORK DEVICE LAYER  (dev.c)                           │
 │    dev_queue_xmit() → qdisc (traffic shaping) → driver              │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │                   NIC DRIVER  (e.g., e1000e, ixgbe)                 │
 │    Maps skb to DMA descriptors; hardware TSO if supported            │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
                    ═════════╪════════  WIRE / FIBER / RADIO
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │                RECEIVER NIC DRIVER                                  │
 │    DMA into sk_buff; LRO/GRO coalesces frames before delivery        │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │             RECEIVER IP LAYER  (ip_input.c)                         │
 │    ip_rcv() → ip_defrag() reassembles IP fragments                  │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │            RECEIVER TCP LAYER  (tcp_input.c)                        │
 │    tcp_rcv_established() → sk_receive_queue → reorder out-of-order  │
 └───────────────────────────┬─────────────────────────────────────────┘
                             │
 ┌───────────────────────────▼─────────────────────────────────────────┐
 │                    YOUR APPLICATION                                  │
 │            read(fd, buffer, len) / recv()                           │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 1 — Physical: Bits and Signal Boundaries

Layer 1 is not really about fragmentation — it is about **encoding bits as signals** and dealing with the physical limits of the medium.

### What Layer 1 does

- Converts binary 0/1 into voltage levels (copper), light pulses (fiber), or radio waves (WiFi).
- Defines clock speed (baud rate), voltage levels, connector pinouts.
- Has **no concept of "packets"** — it just sees a stream of bits.

### Why it matters for fragmentation

Layer 1 defines the **bit rate** (e.g., 1 Gbps Ethernet). It can carry bits at 10^9 bits/second, but it cannot carry a 1 GB transfer in one atomic operation — the bits arrive **serially over time**. Higher layers must package data into bounded units (frames) so that the receiver knows where one transmission ends and the next begins.

Layer 2 solves this by defining **start delimiters** and **end delimiters** for frames.

---

## 4. Layer 2 — Data Link: Frames and the MTU

### 4.1 Ethernet Frame Structure

This is the most important boundary in understanding fragmentation: the **Ethernet MTU of 1500 bytes**.

```
 Ethernet II Frame
 ┌──────────┬──────────┬──────┬─────────────────────────┬─────┐
 │ Preamble │  Dest MAC│ Src  │ EtherType │   PAYLOAD    │ FCS │
 │  7 bytes │  6 bytes │  MAC │  2 bytes  │ 46–1500 bytes│4 B  │
 │ + 1 SFD  │          │ 6 B  │           │              │     │
 └──────────┴──────────┴──────┴───────────┴──────────────┴─────┘
                                           ↑             ↑
                                        IP packet lives here
                                        Min 46, Max 1500 bytes
```

- **Preamble (7 bytes) + SFD (1 byte)**: Synchronization — tells the NIC "a frame is starting."
- **Destination MAC (6 bytes)**: Layer 2 address of the next hop.
- **Source MAC (6 bytes)**: Sender's MAC.
- **EtherType (2 bytes)**: `0x0800` = IPv4, `0x86DD` = IPv6, `0x0806` = ARP.
- **Payload (46–1500 bytes)**: This is where your IP packet lives.
- **FCS (4 bytes)**: CRC-32 checksum over the entire frame.

### 4.2 The MTU: 1500 Bytes

The **Maximum Transmission Unit (MTU)** is the largest Layer 3 payload that a Layer 2 frame can carry. For standard Ethernet, this is **1500 bytes**. This number comes from the original 10 Mbps Ethernet design by DEC/Intel/Xerox in 1980 — a tradeoff between collision domain efficiency and memory costs of the era.

This single number, 1500, is **the source of essentially all fragmentation in the modern internet**.

```
MTU = 1500 bytes
  └─> IP Header = 20 bytes (minimum, up to 60 with options)
       └─> TCP Header = 20 bytes (minimum, up to 60 with options)
            └─> TCP Payload = 1500 - 20 - 40 = 1440 bytes  ← MSS
```

**MSS (Maximum Segment Size)** = MTU - IP Header - TCP Header = 1460 bytes typically.

### 4.3 Jumbo Frames

Jumbo frames allow MTUs up to **9000 bytes** on modern data center Ethernet. This reduces CPU overhead because fewer frames are needed. Both endpoints and all switches in the path must support jumbo frames; otherwise, packets are dropped.

```
Standard Ethernet:  MTU = 1500  bytes → MSS ≈ 1460 bytes
Jumbo Frame:        MTU = 9000  bytes → MSS ≈ 8960 bytes
                    → ~6x fewer segments for the same data
```

### 4.4 802.1Q VLAN Tagging

VLAN tags add 4 bytes to the Ethernet header:

```
 ┌──────────┬──────────┬──────┬────────┬──────────┬──────────────┬─────┐
 │ Preamble │  Dest MAC│ Src  │802.1Q  │EtherType │   PAYLOAD    │ FCS │
 │  8 bytes │  6 bytes │ MAC  │4 bytes │  2 bytes │ 46–1500 bytes│4 B  │
 └──────────┴──────────┴──────┴────────┴──────────┴──────────────┴─────┘
```

This reduces the effective MTU to 1496 bytes if the network doesn't account for the tag. Many networks set their MTU to 1504 to compensate.

### 4.5 Who Is Responsible at Layer 2?

**Fragmentation at Layer 2 does not exist.** If a packet is larger than the MTU, the NIC **drops it**. The responsibility lies with Layer 3 (IP) to ensure packets are never larger than the path MTU.

The Linux kernel struct that represents a Layer 2 frame in memory is the `sk_buff` (socket buffer), defined in `include/linux/skbuff.h`.

---

## 5. Layer 3 — Network: IP Fragmentation

### 5.1 The IPv4 Header

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
 │Version│  IHL  │Type of Service│          Total Length             │
 ├───────┴───────┴───────────────┼───────────────────────────────────┤
 │         Identification        │Flags│     Fragment Offset         │
 ├───────────────────────────────┼─────┴─────────────────────────────┤
 │  Time to Live │   Protocol    │         Header Checksum           │
 ├───────────────┴───────────────┴───────────────────────────────────┤
 │                       Source Address                              │
 ├───────────────────────────────────────────────────────────────────┤
 │                    Destination Address                            │
 ├───────────────────────────────────────────────────────────────────┤
 │                    Options                    │    Padding        │
 └───────────────────────────────────────────────┴───────────────────┘
```

The three fields that control fragmentation:

| Field | Size | Purpose |
|-------|------|---------|
| **Identification** | 16 bits | Unique ID shared by all fragments of a datagram |
| **Flags** | 3 bits | bit 1 = DF (Don't Fragment), bit 2 = MF (More Fragments) |
| **Fragment Offset** | 13 bits | Byte offset of this fragment ÷ 8 (so offset is in 8-byte units) |

### 5.2 How IPv4 Fragmentation Works

Suppose a router receives an IP datagram of 4000 bytes but the outgoing link has MTU = 1500.

```
 Original Datagram: 4000 bytes total
 ┌────────────────────────────────────────────────────────────┐
 │ IP HDR (20B) │         DATA: 3980 bytes                   │
 │  ID=555      │                                            │
 │  DF=0        │                                            │
 └────────────────────────────────────────────────────────────┘
                             │
               MTU = 1500, router must fragment
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
 Fragment 1:          Fragment 2:          Fragment 3:
 ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
 │ IP HDR (20B)     │ │ IP HDR (20B)     │ │ IP HDR (20B)     │
 │  ID=555          │ │  ID=555          │ │  ID=555          │
 │  MF=1            │ │  MF=1            │ │  MF=0 (last)     │
 │  offset=0        │ │  offset=185      │ │  offset=370      │
 │  len=1500        │ │  len=1500        │ │  len=1020        │
 │ DATA: 1480 bytes │ │ DATA: 1480 bytes │ │ DATA: 1000 bytes │
 └──────────────────┘ └──────────────────┘ └──────────────────┘
```

**Offset calculation:**
- Fragment 1: bytes 0–1479, offset = 0/8 = 0
- Fragment 2: bytes 1480–2959, offset = 1480/8 = 185
- Fragment 3: bytes 2960–3979, offset = 2960/8 = 370

**Why divide by 8?** The fragment offset field is only 13 bits, giving max value 8191. If stored as raw bytes, max addressable = 8191 bytes — too small. By using 8-byte units (so the actual byte offset = offset × 8), the maximum becomes 8191 × 8 = 65,528 bytes. This matches IPv4's maximum datagram size of 65,535 bytes.

### 5.3 The DF (Don't Fragment) Bit and PMTUD

When the **DF bit is set**, a router that cannot forward the packet without fragmenting it must **drop the packet and send an ICMP "Fragmentation Needed" message** back to the sender:

```
 ICMP Type 3 (Destination Unreachable), Code 4 (Fragmentation Needed)
 ┌──────────────────────────────────────────────────────────────┐
 │ Type=3 │ Code=4 │  Checksum  │  unused  │ Next-Hop MTU      │
 │        │        │            │  (0)     │ (what MTU to use) │
 └──────────────────────────────────────────────────────────────┘
```

TCP sockets set DF=1 by default, enabling **Path MTU Discovery (PMTUD)** — the sender reduces its segment size when it gets these ICMP messages. More on this in Section 11.

### 5.4 IPv4 Reassembly at the Receiver

The receiving host must reassemble fragments into the original datagram **before** passing to Layer 4. The kernel maintains a **fragment reassembly queue** keyed by `(src_ip, dst_ip, protocol, identification)`.

Linux kernel implementation: `net/ipv4/ip_fragment.c`

```c
// Key data structures in ip_fragment.c

struct ipq {                        // IPv4 fragment queue
    struct inet_frag_queue q;       // generic fragment queue (timers, etc.)
    // ...
};

struct inet_frag_queue {
    spinlock_t      lock;
    struct timer_list timer;        // 30-second reassembly timeout
    struct rb_root  rb_fragments;   // red-black tree of received fragments
    struct sk_buff  *fragments;     // list of fragments (older kernels)
    int             len;            // total length received so far
    int             meat;           // total bytes received
    __u8            flags;
    // ...
};
```

**Reassembly timeout**: If all fragments don't arrive within **30 seconds** (Linux default: `net.ipv4.ipfrag_time`), the partial datagram is discarded, and an ICMP "Time Exceeded" (fragment reassembly timeout) is sent back to the sender.

### 5.5 IPv6 and Fragmentation

IPv6 **does not allow routers to fragment packets**. Only the **originating host** can fragment. Routers that cannot forward a packet send back an **ICMPv6 "Packet Too Big"** message.

The IPv6 fragmentation header is a separate extension header:

```
 IPv6 Fragment Header (8 bytes):
 ┌────────────┬────────────────────┬──────────────┬────────────────┐
 │ Next Header│   Reserved (8b)    │ Frag Offset  │ Res │ M Flag   │
 │  (8 bits)  │                   │   (13 bits)  │(2b) │ (1 bit)  │
 ├────────────┴────────────────────┴──────────────┴─────┴──────────┤
 │                    Identification (32 bits)                      │
 └─────────────────────────────────────────────────────────────────┘
```

Note: IPv6 fragment Identification is **32 bits** (vs IPv4's 16 bits), reducing collision probability.

In practice, IPv6 networks rely on PMTUD so fragmentation rarely occurs. The minimum IPv6 MTU is **1280 bytes** (vs IPv4's 68 bytes).

### 5.6 Linux Kernel: ip_fragment() Function

File: `net/ipv4/ip_output.c`

```c
int ip_fragment(struct net *net, struct sock *sk, struct sk_buff *skb,
                unsigned int mtu, int (*output)(struct net *, struct sock *,
                                                struct sk_buff *))
{
    struct iphdr *iph = ip_hdr(skb);
    // ...

    // Check if DF bit is set — if so, we cannot fragment
    if (unlikely((iph->frag_off & htons(IP_DF)) && skb->ignore_df == 0)) {
        // Send ICMP "Fragmentation Needed"
        icmp_send(skb, ICMP_DEST_UNREACH, ICMP_FRAG_NEEDED,
                  htonl(mtu));
        IP_INC_STATS(net, IPSTATS_MIB_FRAGFAILS);
        kfree_skb(skb);
        return -EMSGSIZE;
    }

    // Calculate how many bytes fit per fragment
    // mtu already accounts for IP header
    unsigned int hlen = iph->ihl * 4;
    unsigned int left = skb->len - hlen;  // data left to fragment
    unsigned int len  = (mtu - hlen) & ~7; // must be multiple of 8

    // Allocate and send each fragment
    while (left > 0) {
        struct sk_buff *skb2 = alloc_skb(len + hlen + ..., GFP_ATOMIC);
        // Copy IP header into new skb
        skb_copy_from_linear_data(skb, skb_network_header(skb2), hlen);
        // Copy data slice
        // ...
        // Set fragment offset and MF flag
        iph2 = ip_hdr(skb2);
        iph2->frag_off = htons(offset >> 3);
        if (left > len)
            iph2->frag_off |= htons(IP_MF);  // more fragments coming
        // ...
        output(net, sk, skb2);
        left -= len;
        offset += len;
    }
}
```

---

## 6. Layer 4 — Transport: TCP Segmentation and UDP

### 6.1 TCP: The Primary Mechanism for Large Transfers

TCP is the layer that **does most of the work** when you send a 1 GB file. It transforms a **byte stream** into a sequence of **segments**, each small enough to fit in an IP datagram, which itself fits in an Ethernet frame.

#### TCP Segment Header

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 ┌─────────────────────────────────┬─────────────────────────────────┐
 │          Source Port            │       Destination Port          │
 ├─────────────────────────────────┴─────────────────────────────────┤
 │                        Sequence Number                            │
 ├───────────────────────────────────────────────────────────────────┤
 │                    Acknowledgment Number                          │
 ├─────────┬───────────────────────┬───────────────────────────────┤
 │  Data   │    Reserved   │Flags  │           Window Size          │
 │ Offset  │               │       │                               │
 ├─────────┴───────────────┴───────┴───────────────────────────────┤
 │           Checksum              │         Urgent Pointer         │
 ├─────────────────────────────────┴─────────────────────────────────┤
 │                    Options (if Data Offset > 5)                   │
 └───────────────────────────────────────────────────────────────────┘
```

#### MSS Negotiation During Handshake

When a TCP connection is established, both sides announce their MSS in the SYN packets:

```
 Client → Server:  SYN, MSS=1460
 Server → Client:  SYN+ACK, MSS=1460
 Client → Server:  ACK

 Both sides will send no more than min(local_MSS, remote_MSS) bytes per segment.
 MSS = MTU - IP_header(20) - TCP_header(20) = 1500 - 40 = 1460 bytes
```

### 6.2 How tcp_sendmsg() Works

When your application calls `send(fd, buf, 1GB, 0)`, the kernel executes:

```
 Application:  send(fd, buf, 1073741824, 0)
               │
               ▼
 sys_sendmsg() / sys_send()
               │
               ▼
 sock_sendmsg()
               │
               ▼
 tcp_sendmsg()    ← PRIMARY FUNCTION in net/ipv4/tcp.c
   │
   ├── Copies data from userspace into sk_buff(s) in the send queue
   │   Each skb holds up to MSS bytes of data
   │
   ├── sk_stream_wait_memory() — blocks if send buffer is full
   │
   └── tcp_push()
         │
         └── tcp_write_xmit()   ← in net/ipv4/tcp_output.c
               │
               ├── tcp_nagle_check() — Nagle algorithm: delay small segments
               │
               ├── tcp_cwnd_test()   — Congestion window check
               │
               ├── tcp_snd_wnd_test() — Receiver window check
               │
               └── tcp_transmit_skb()
                     │
                     ├── Build TCP header
                     ├── tcp_options_write() — add SACK, timestamps, etc.
                     └── ip_queue_xmit()    → down to IP layer
```

#### Key State Variables in struct tcp_sock

```c
struct tcp_sock {
    // Sequence numbers
    u32 snd_una;     // oldest unacknowledged sequence number
    u32 snd_nxt;     // next sequence number to send
    u32 rcv_nxt;     // next sequence number expected from peer

    // Window management
    u32 snd_wnd;     // receiver's window (from ACK)
    u32 rcv_wnd;     // our receive window
    u32 cwnd;        // congestion window (sender-side limit)
    u32 ssthresh;    // slow start threshold

    // Segmentation
    u16 advmss;      // MSS advertised to peer
    u16 mss_cache;   // current effective MSS

    // Retransmission
    u32 srtt_us;     // smoothed round-trip time
    u32 rttvar_us;   // RTT variance
    // ...
};
```

### 6.3 TCP Reassembly at the Receiver

The receiver's kernel in `net/ipv4/tcp_input.c`:

```
 NIC receives frame
         │
         ▼
 tcp_rcv_established()     ← fast path
         │
         ├── In-order segment?
         │     ├── YES: copy to socket receive buffer, update rcv_nxt
         │     └── NO:  tcp_data_queue() → out-of-order queue (rb_tree)
         │
         ├── Send ACK
         │     ├── Immediate for out-of-order
         │     └── Delayed ACK (40ms) for in-order (tcp_send_delayed_ack())
         │
         └── Wake up application (sk->sk_data_ready())
               │
               ▼
         Application: read(fd, buf, len) gets reassembled bytes
```

The out-of-order queue is a **red-black tree** keyed on sequence number. When the missing segment arrives, the kernel merges the queued segments into the receive buffer in order.

### 6.4 TCP Flow Control vs. Congestion Control

These are two separate mechanisms that both limit how much data TCP sends at once:

```
 Sender can transmit at most:
 
    bytes_in_flight ≤ min(congestion_window, receiver_window)
    
    where:
      congestion_window = cwnd  (sender's estimate of network capacity)
      receiver_window   = snd_wnd (receiver's available buffer space)

 ┌─────────────────────────────────────────────────────────────────┐
 │                    TCP SEND BUFFER (sk_sndbuf)                  │
 │                                                                 │
 │  [sent, ACKed]  [sent, unACKed]  [not yet sent]  [app data]   │
 │  ─────────────  ────────────────  ─────────────   ───────────  │
 │               ↑                ↑                ↑              │
 │             snd_una          snd_nxt         write_seq         │
 │                  ←── in-flight ──→                             │
 │                  must fit in min(cwnd, wnd)                    │
 └─────────────────────────────────────────────────────────────────┘
```

### 6.5 UDP: No Built-in Segmentation

UDP provides **no segmentation, no reliability, no ordering**. If you try to send a 70,000-byte UDP datagram, the kernel will:

1. Accept the `sendto()` call.
2. Pass it to IP.
3. IP will fragment it into multiple IP packets (if DF=0).
4. If DF=1 or if any router drops it, the entire datagram is lost.

UDP is used when the **application** wants to control segmentation — e.g., video streaming (RTP), DNS, QUIC (which implements its own reliability over UDP).

```c
// UDP kernel path: net/ipv4/udp.c
int udp_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    // If len > 65507 (UDP max payload), return EMSGSIZE
    if (len > 0xFFFF)
        return -EMSGSIZE;

    // Build UDP header
    // Call ip_make_skb() then udp_send_skb()
    // ip_append_data() → ip_push_pending_frames()
    // → ip_finish_output() → may call ip_fragment()
}
```

---

## 7. Layer 5-7 — Application: Chunking and Protocol Framing

The application layer does its own "fragmentation" independently of the lower layers. This is about **protocol design**, not physical constraints.

### 7.1 HTTP/1.1: Transfer-Encoding: chunked

```
 HTTP/1.1 POST /upload HTTP/1.1
 Content-Type: application/octet-stream
 Transfer-Encoding: chunked

 1A3F\r\n              ← chunk size in hex (0x1A3F = 6719 bytes)
 [6719 bytes of data]\r\n
 1A3F\r\n
 [6719 bytes of data]\r\n
 ...
 0\r\n                 ← terminal chunk: size=0 means end
 \r\n
```

This is application-level framing. The receiver (HTTP server) reassembles chunks into a complete request body. This is **independent of TCP segmentation** — each HTTP chunk may span many TCP segments, or multiple HTTP chunks may fit in one TCP segment.

### 7.2 HTTP/2: Multiplexed Streams

HTTP/2 introduces **frames** at the application layer:

```
 HTTP/2 Frame:
 ┌────────────────────┬──────────┬─────────┬──────────────────────┐
 │  Length (24 bits)  │ Type (8b)│Flags(8b)│   Stream ID (31b)    │
 └────────────────────┴──────────┴─────────┴──────────────────────┘
 │                         Payload                                 │
 └─────────────────────────────────────────────────────────────────┘

 Frame types:
 - DATA (0x0):        Carries the actual request/response body
 - HEADERS (0x1):     HTTP headers (HPACK compressed)
 - WINDOW_UPDATE(0x8): Flow control — similar to TCP window but per-stream
 - SETTINGS (0x4):    Connection parameters including SETTINGS_MAX_FRAME_SIZE
```

HTTP/2 DATA frames are typically up to 16KB (default `SETTINGS_MAX_FRAME_SIZE = 16384`). Each DATA frame maps to one or more TCP segments.

### 7.3 QUIC: Application-Layer Transport

QUIC runs over UDP and implements its own segmentation, reliability, and flow control. A QUIC packet fits in a single UDP datagram (which fits in one IP packet, which fits in one Ethernet frame).

```
 QUIC Packet (sits entirely within one UDP datagram):
 ┌──────────────────────────────────────────────────────────────────┐
 │  Header (Short or Long form)                                     │
 ├──────────────────────────────────────────────────────────────────┤
 │  STREAM Frame: [Stream ID][Offset][Length][Data]                 │
 │  ACK Frame: [Largest Acked][ACK Delay][ACK Ranges...]            │
 └──────────────────────────────────────────────────────────────────┘
```

QUIC avoids head-of-line blocking: if one QUIC packet is lost, only the streams it carries are stalled — other streams continue. This is a key advantage over TCP where **one lost segment stalls all streams** in the connection.

### 7.4 sendfile() — Zero-Copy File Transfer

When you use `sendfile(out_fd, in_fd, offset, count)`, the kernel:

1. Reads file pages from the page cache (no copy to userspace).
2. Passes them directly to the NIC via DMA.
3. TCP/IP headers are added in the kernel.

```
 Normal send():                   sendfile():
 
 Disk → kernel page cache         Disk → kernel page cache
      → user buffer                    → NIC DMA  (no user copy!)
      → kernel socket buffer
      → NIC DMA
 
 Copies: 4                        Copies: 2 (or 1 with hardware support)
```

This is how tools like `nginx` serve static files with near-zero CPU overhead.

---

## 8. The Linux Kernel Code Path: Sending a 1 GB File

Let's trace the exact kernel code path for `sendfile(socket_fd, file_fd, 0, 1073741824)`.

```
 USER SPACE
 ─────────────────────────────────────────────────────────
 KERNEL SPACE

 syscall: sys_sendfile64()          [fs/read_write.c]
     │
     └── do_sendfile()
           │
           └── generic_sendpage() or file->f_op->sendpage()
                 │
                 ├── For each PAGE_SIZE (4096 bytes) chunk of the file:
                 │
                 └── tcp_sendpage()             [net/ipv4/tcp.c]
                       │
                       ├── sk_stream_wait_memory()   ← block if no send buffer space
                       │
                       ├── skb = tcp_write_queue_tail(sk)
                       │      or alloc_skb_fclone() for new skb
                       │
                       ├── skb_fill_page_desc()      ← point skb to file page (zero copy)
                       │
                       └── __tcp_push_pending_frames()
                             │
                             └── tcp_write_xmit()    [net/ipv4/tcp_output.c]
                                   │
                                   ├── [for each segment up to cwnd limit]
                                   │
                                   └── tcp_transmit_skb()
                                         │
                                         ├── tcp_options_write()  ← timestamps, SACK
                                         ├── Build tcp hdr: src/dst port, seq, ack, flags
                                         ├── tcp_v4_send_check() ← checksum
                                         │
                                         └── ip_queue_xmit()     [net/ipv4/ip_output.c]
                                               │
                                               ├── __ip_route_output_key()  ← routing
                                               │
                                               ├── ip_select_ident()        ← set IP ID
                                               │
                                               ├── Build IP header
                                               │
                                               └── ip_finish_output()
                                                     │
                                                     ├── Packet > MTU?
                                                     │     ├── YES → ip_fragment()
                                                     │     └── NO  → ip_finish_output2()
                                                     │
                                                     └── ip_finish_output2()
                                                           │
                                                           └── neigh_output()  ← ARP/neighbor
                                                                 │
                                                                 └── dev_queue_xmit()
                                                                       │
                                                                       ├── qdisc (tc)
                                                                       └── dev->netdev_ops->ndo_start_xmit()
                                                                             │
                                                                             └── NIC DRIVER (e.g., ixgbe_xmit_frame)
                                                                                   │
                                                                                   └── DMA → WIRE
```

### 8.1 The sk_buff: The Kernel's Swiss Army Knife

The `sk_buff` (socket buffer) is the central data structure of the Linux network stack. Everything — frames, packets, segments — is represented as an `sk_buff`.

```c
// include/linux/skbuff.h (simplified)
struct sk_buff {
    // Linked list pointers (for queues)
    struct sk_buff      *next;
    struct sk_buff      *prev;

    // Timestamps
    ktime_t             tstamp;

    // Network device
    struct net_device   *dev;

    // Data pointers — the "window" into the actual buffer
    unsigned char       *head;   // start of allocated buffer
    unsigned char       *data;   // start of valid data
    unsigned char       *tail;   // end of valid data
    unsigned char       *end;    // end of allocated buffer
    unsigned int        len;     // length of data + fragments
    unsigned int        data_len; // length in frags (for scatter/gather)

    // Header room (pre-allocated space for headers)
    // As packet goes DOWN the stack, headers are PREPENDED (pushed)
    // As packet goes UP the stack, headers are STRIPPED (pulled)

    // Transport layer header
    union {
        struct tcphdr   *th;
        struct udphdr   *uh;
        // ...
    } h;

    // Network layer header
    union {
        struct iphdr    *iph;
        struct ipv6hdr  *ipv6h;
        // ...
    } nh;

    // Link layer header
    union {
        struct ethhdr   *ethernet;
        // ...
    } mac;

    // Checksum information
    __wsum              csum;
    __u8                ip_summed;  // CHECKSUM_NONE, CHECKSUM_PARTIAL, CHECKSUM_COMPLETE

    // Fragment list (for scatter/gather I/O)
    skb_frag_t          frags[MAX_SKB_FRAGS];  // up to 17 page fragments

    // Reference count, destructor, etc.
    atomic_t            users;
    void                (*destructor)(struct sk_buff *skb);
};
```

#### How the sk_buff grows as it goes down the stack:

```
 After tcp_transmit_skb():
 ┌──────┬────────────────────────────────────────────────────┐
 │      │ TCP Header (20B) │ DATA (1460B)                   │
 └──────┴────────────────────────────────────────────────────┘
        ↑                  ↑
       data               tail

 After ip_queue_xmit() prepends IP header:
 ┌──┬──────────────────────────────────────────────────────────┐
 │  │ IP Header (20B) │ TCP Header (20B) │ DATA (1460B)        │
 └──┴──────────────────────────────────────────────────────────┘
    ↑                                    ↑
   data (moved back 20 bytes)           tail

 After dev layer prepends Ethernet header:
 ┌──────────────────────────────────────────────────────────────┐
 │ ETH Hdr(14B) │ IP Header (20B) │ TCP Header (20B) │ DATA    │
 └──────────────────────────────────────────────────────────────┘
 ↑                                                    ↑
data (moved back 14 bytes)                           tail
```

Headers are **prepended** efficiently by moving the `data` pointer backward — no data is copied.

---

## 9. The Linux Kernel Code Path: Receiving Side

```
 WIRE → NIC DMA → Driver receive ring buffer
         │
         ▼
 Driver: ixgbe_clean_rx_irq() or similar
         │
         ├── Allocate sk_buff
         ├── Map DMA buffer into skb->data
         └── Call netif_receive_skb()
               │
               ▼
         __netif_receive_skb()           [net/core/dev.c]
               │
               ├── GRO (Generic Receive Offload): napi_gro_receive()
               │     └── Coalesces multiple small frames into one big skb
               │
               └── Deliver to protocol handler via ptype->func()
                     │
               ┌─────┴──────┐
        IPv4 handler      IPv6 handler
        ip_rcv()          ipv6_rcv()
               │
               ▼
         ip_rcv_finish()               [net/ipv4/ip_input.c]
               │
               ├── Fragment? → ip_defrag()  [net/ipv4/ip_fragment.c]
               │     │
               │     ├── Create/find struct ipq for this (src,dst,id,proto)
               │     ├── Add fragment to rb_tree ordered by offset
               │     └── All fragments arrived? → ip_frag_reasm()
               │           └── Coalesce into single skb, return
               │
               └── Pass complete datagram to L4:
                     TCP: tcp_v4_rcv()
                     UDP: udp_rcv()
                           │
               ┌───────────┴─────────────┐
         tcp_v4_rcv()              udp_rcv()
               │
               ▼
         tcp_rcv_established()     [net/ipv4/tcp_input.c]
               │
               ├── Check sequence number
               │
               ├── In order? → tcp_queue_rcv()  → sk_receive_queue
               │
               ├── Out of order? → tcp_ofo_queue() → out-of-order rb_tree
               │
               ├── Send ACK (possibly delayed)
               │
               └── sk->sk_data_ready(sk)  ← wake up application
                     │
                     ▼
               Application: read() / recv() returns reassembled data
```

---

## 10. Hardware Offloading: TSO, GSO, GRO, LRO, UFO

Modern NICs offload fragmentation/reassembly work from the CPU to hardware. This is critical for performance at 10Gbps+.

### 10.1 TSO — TCP Segmentation Offload (Send side)

Without TSO, the CPU must split a large TCP write into 1460-byte segments, build a TCP/IP header for each, and hand each one to the NIC. For 10Gbps, that's ~850,000 segments per second.

With TSO, the CPU hands the NIC **one large "super-segment"** (up to 64KB), and the NIC splits it into proper 1460-byte segments and adds headers automatically.

```
 Without TSO (CPU does segmentation):
 
 CPU: [TCP hdr][1460B][TCP hdr][1460B][TCP hdr][1460B]...  → NIC
      ↑ lots of CPU work per segment

 With TSO (NIC does segmentation):
 
 CPU: [TCP hdr][64KB of data]  → NIC
      ↑ one operation!
 
 NIC: [TCP hdr][1460B] [TCP hdr][1460B] [TCP hdr][1460B]...  → WIRE
      ↑ NIC splits and adds headers
```

**GSO (Generic Segmentation Offload)**: A software fallback for TSO. The kernel delays segmentation until the last possible moment. Even if the NIC doesn't support TSO, GSO reduces header-building overhead by doing it in bulk just before the driver.

```
 GSO in kernel (net/core/gso.c):
 skb_gso_segment() → splits large skb into segment-sized skbs
                    → called in dev_hard_start_xmit() if NIC lacks TSO
```

### 10.2 GRO — Generic Receive Offload (Receive side)

GRO coalesces multiple incoming TCP segments into a single large skb before handing it to the protocol stack. This reduces the number of times `tcp_rcv_established()` is called.

```
 Without GRO:
 NIC delivers: [skb:1460B] [skb:1460B] [skb:1460B] → tcp_rcv() called 3 times

 With GRO:
 NIC delivers: [skb:4380B]  → tcp_rcv() called once
```

GRO is implemented in `net/core/gro.c`. The `napi_gro_receive()` function checks if the new packet can be merged with an existing GRO packet (same flow, consecutive sequence numbers).

### 10.3 LRO — Large Receive Offload

LRO is the **hardware** equivalent of GRO. The NIC coalesces packets before DMA into host memory. LRO is less flexible than GRO (can't distinguish flows as well) and has largely been replaced by GRO in modern systems.

### 10.4 UFO — UDP Fragmentation Offload

For large UDP datagrams, UFO allows the NIC to handle IP fragmentation in hardware:

```
 CPU sends: [IP hdr][UDP hdr][65000B of data]
 
 NIC splits into IP fragments automatically:
 [IP hdr frag 1][1480B] [IP hdr frag 2][1480B] ... [IP hdr frag N][remainder]
```

UFO has been removed from Linux (as of 4.14) due to security concerns — the fragmentation ID assignment was trivially predictable.

### 10.5 Checking Offload Status

```bash
# Check which offloads are enabled
ethtool -k eth0

# Output includes:
# tcp-segmentation-offload: on
# generic-segmentation-offload: on
# generic-receive-offload: on
# large-receive-offload: off
# udp-fragmentation-offload: off [fixed]

# Disable TSO for testing/debugging:
ethtool -K eth0 tso off

# Check statistics
ethtool -S eth0 | grep -i segment
```

---

## 11. Path MTU Discovery (PMTUD)

PMTUD is the mechanism by which TCP automatically discovers the smallest MTU along the entire path from sender to receiver, and adjusts its MSS accordingly.

### 11.1 PMTUD for IPv4 (RFC 1191)

```
 Sender                    Router                    Receiver
    │                         │                         │
    │── TCP SYN, MSS=1460 ──►│──────────────────────►│
    │◄── TCP SYN+ACK ─────────│◄─── MSS=1460 ─────────│
    │── TCP ACK ─────────────►│──────────────────────►│
    │                         │                         │
    │── IP pkt, 1500B, DF=1 ─►│                         │
    │     (TCP data)          │   Outgoing link MTU=1400│
    │                         │   Can't forward!         │
    │◄── ICMP "Frag Needed" ──│   Next-hop MTU = 1400   │
    │    Type=3, Code=4        │                         │
    │    Next-hop MTU: 1400    │                         │
    │                         │                         │
    │  Kernel updates route    │                         │
    │  cache: MTU=1400         │                         │
    │  New MSS = 1400-40=1360  │                         │
    │                         │                         │
    │── IP pkt, 1400B, DF=1 ─►│──────────────────────►│
    │                         │                         │
```

The kernel stores MTU per destination in the routing cache:
- `ip_rt_update_pmtu()` in `net/ipv4/route.c`
- Cache entry: `struct rtable` → `dst.metrics[RTAX_MTU]`
- TTL: 10 minutes by default, then re-probed

### 11.2 PMTUD Blackholes

Some firewalls block ICMP packets ("ICMP blocking"). When a router drops an oversized packet and sends ICMP "Frag Needed", the firewall blocks that ICMP response. The sender never learns the correct MTU and keeps sending large packets that are silently dropped.

This is called a **PMTUD Blackhole** and is responsible for many mysterious TCP connection stalls.

```
 Sender                    Firewall                  Router
    │                         │                         │
    │── large TCP segment ───►│──────────────────────►│
    │                         │                         │  drops packet
    │                         │◄── ICMP Frag Needed ───│
    │                         │  (BLOCKED by firewall)  │
    │                         │                         │
    │  ← no ICMP arrives      │                         │
    │  ← connection stalls!   │                         │
```

**Linux fix**: TCP Blackhole Detection (`net.ipv4.tcp_mtu_probing`):

```bash
sysctl net.ipv4.tcp_mtu_probing=1   # Enable probing when stall detected
sysctl net.ipv4.tcp_base_mss=1024   # Start with smaller MSS when probing
```

### 11.3 MSS Clamping

Routers at network edges can inject a corrected MSS into TCP SYN/SYN-ACK packets — even if they can't modify data packets. This avoids PMTUD entirely for TCP:

```bash
# iptables MSS clamping (common on DSL routers, VPN gateways)
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu
# or
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --set-mss 1452  # PPPoE reduces MTU to 1492, MSS = 1452
```

---

## 12. C: Raw Socket and IP Fragmentation Implementation

### 12.1 Sending Fragmented IP Packets with Raw Sockets

```c
// ip_frag_sender.c
// Compile: gcc -o ip_frag_sender ip_frag_sender.c
// Run as root: sudo ./ip_frag_sender <dst_ip> <payload_size>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <linux/if_ether.h>

#define MTU          1500
#define IP_HDR_LEN   20
#define UDP_HDR_LEN  8
#define MAX_FRAG_DATA (MTU - IP_HDR_LEN)  // 1480 bytes per fragment

// Compute checksum (RFC 1071)
uint16_t checksum(void *data, int len) {
    uint32_t sum = 0;
    uint16_t *ptr = data;
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }
    if (len == 1)
        sum += *(uint8_t *)ptr;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    return (uint16_t)(~sum);
}

// Send a large UDP payload fragmented manually at the IP level.
// This demonstrates exactly what the kernel does in ip_fragment().
int send_fragmented(int sock, const char *dst_ip,
                    const char *payload, size_t payload_len) {
    struct sockaddr_in dst = {
        .sin_family = AF_INET,
        .sin_port   = htons(9999),
    };
    inet_pton(AF_INET, dst_ip, &dst.sin_addr);

    // Total data to fragment = UDP header + payload
    uint8_t udp_and_data[65535];
    struct udphdr *udph = (struct udphdr *)udp_and_data;
    udph->source = htons(12345);
    udph->dest   = htons(9999);
    udph->len    = htons(UDP_HDR_LEN + payload_len);
    udph->check  = 0;  // optional for UDP
    memcpy(udp_and_data + UDP_HDR_LEN, payload, payload_len);

    size_t total_data = UDP_HDR_LEN + payload_len;  // data to be fragmented
    uint16_t ip_id   = htons(rand() & 0xFFFF);       // shared fragment ID
    size_t offset    = 0;                             // byte offset
    uint8_t packet[MTU + 100];

    printf("Sending %zu bytes in fragments (max frag data = %d bytes)\n",
           total_data, MAX_FRAG_DATA);

    while (offset < total_data) {
        size_t frag_data_len = total_data - offset;
        int more_frags = 1;

        if (frag_data_len > MAX_FRAG_DATA) {
            // Must fragment — and fragment data must be multiple of 8
            frag_data_len = MAX_FRAG_DATA & ~7;
            more_frags = 1;
        } else {
            more_frags = 0;  // last fragment
        }

        // Build IP header
        struct iphdr *iph = (struct iphdr *)packet;
        iph->version  = 4;
        iph->ihl      = 5;           // 5 * 4 = 20 bytes, no options
        iph->tos      = 0;
        iph->tot_len  = htons(IP_HDR_LEN + frag_data_len);
        iph->id       = ip_id;       // SAME for all fragments of this datagram
        
        // Fragment offset is in units of 8 bytes
        uint16_t frag_offset_field = (offset / 8) & 0x1FFF;
        if (more_frags)
            frag_offset_field |= (1 << 13);  // set MF bit (bit 13 in network byte order)
        iph->frag_off = htons(frag_offset_field);
        
        iph->ttl      = 64;
        iph->protocol = IPPROTO_UDP;  // 17
        iph->check    = 0;
        iph->saddr    = htonl(INADDR_LOOPBACK);  // 127.0.0.1
        inet_pton(AF_INET, dst_ip, &iph->daddr);

        // Compute IP checksum
        iph->check = checksum(iph, IP_HDR_LEN);

        // Copy fragment data
        memcpy(packet + IP_HDR_LEN, udp_and_data + offset, frag_data_len);

        // Send fragment
        ssize_t sent = sendto(sock, packet, IP_HDR_LEN + frag_data_len, 0,
                              (struct sockaddr *)&dst, sizeof(dst));
        if (sent < 0) {
            perror("sendto");
            return -1;
        }

        printf("  Fragment: offset=%zu, data_len=%zu, MF=%d, total_sent=%zd\n",
               offset, frag_data_len, more_frags, sent);

        offset += frag_data_len;
    }
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <dst_ip> <payload_size>\n", argv[0]);
        return 1;
    }

    const char *dst_ip  = argv[1];
    size_t payload_size = atoi(argv[2]);

    // Create RAW socket (requires root / CAP_NET_RAW)
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sock < 0) {
        perror("socket");
        return 1;
    }

    // Tell kernel WE are building the IP header
    int one = 1;
    setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));

    // Build a payload
    char *payload = malloc(payload_size);
    memset(payload, 'A', payload_size);

    send_fragmented(sock, dst_ip, payload, payload_size);

    free(payload);
    close(sock);
    return 0;
}
```

### 12.2 IP Fragment Receiver and Reassembler

```c
// ip_frag_receiver.c
// Listens on a raw socket and manually reassembles IP fragments.
// This mirrors what ip_defrag() does in the Linux kernel.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <time.h>

#define MAX_DATAGRAM 65535
#define MAX_FRAGS    100
#define TIMEOUT_SEC  30    // reassembly timeout like kernel

// Represents one fragment
typedef struct {
    uint8_t  data[MAX_DATAGRAM];
    uint16_t offset;     // byte offset
    uint16_t len;        // data length
    int      valid;
} Fragment;

// Represents a datagram being reassembled
typedef struct {
    uint16_t  id;
    uint32_t  src_ip;
    uint32_t  dst_ip;
    uint8_t   proto;

    Fragment  frags[MAX_FRAGS];
    int       frag_count;
    int       total_len;   // known when last fragment arrives
    int       received;    // bytes received so far
    time_t    first_seen;
} Datagram;

// Fragment table (in a real implementation, use a hash table)
#define MAX_DATAGRAMS 64
static Datagram datagrams[MAX_DATAGRAMS];

Datagram *find_or_create(uint16_t id, uint32_t src, uint32_t dst, uint8_t proto) {
    for (int i = 0; i < MAX_DATAGRAMS; i++) {
        if (datagrams[i].id == id && datagrams[i].src_ip == src &&
            datagrams[i].dst_ip == dst && datagrams[i].proto == proto)
            return &datagrams[i];
    }
    // Not found — create new entry
    for (int i = 0; i < MAX_DATAGRAMS; i++) {
        if (datagrams[i].frag_count == 0) {
            memset(&datagrams[i], 0, sizeof(Datagram));
            datagrams[i].id       = id;
            datagrams[i].src_ip   = src;
            datagrams[i].dst_ip   = dst;
            datagrams[i].proto    = proto;
            datagrams[i].first_seen = time(NULL);
            return &datagrams[i];
        }
    }
    return NULL;
}

// Try to reassemble a complete datagram.
// Returns pointer to reassembled buffer, or NULL if incomplete.
uint8_t *try_reassemble(Datagram *dg, int *out_len) {
    if (dg->total_len == 0) return NULL;  // don't know total size yet
    if (dg->received < dg->total_len) return NULL;

    // Sort fragments by offset
    for (int i = 0; i < dg->frag_count - 1; i++) {
        for (int j = i + 1; j < dg->frag_count; j++) {
            if (dg->frags[j].offset < dg->frags[i].offset) {
                Fragment tmp = dg->frags[i];
                dg->frags[i] = dg->frags[j];
                dg->frags[j] = tmp;
            }
        }
    }

    // Check we have a contiguous sequence
    uint8_t *buf = malloc(dg->total_len);
    int covered = 0;
    for (int i = 0; i < dg->frag_count; i++) {
        if (dg->frags[i].offset > covered) {
            printf("  Gap at offset %d!\n", covered);
            free(buf);
            return NULL;
        }
        int copy_offset = dg->frags[i].offset;
        int copy_len    = dg->frags[i].len;
        memcpy(buf + copy_offset, dg->frags[i].data, copy_len);
        covered = copy_offset + copy_len;
    }

    *out_len = covered;
    return buf;
}

int main(void) {
    // Capture all IP packets
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_UDP);
    if (sock < 0) {
        perror("socket (need root)");
        return 1;
    }

    printf("Listening for IP fragments (UDP)...\n");

    uint8_t buf[65535];
    while (1) {
        ssize_t n = recv(sock, buf, sizeof(buf), 0);
        if (n <= 0) continue;

        struct iphdr *iph = (struct iphdr *)buf;
        if (iph->version != 4) continue;

        int ip_hdr_len = iph->ihl * 4;
        uint16_t frag_off_raw = ntohs(iph->frag_off);
        uint16_t frag_offset  = (frag_off_raw & 0x1FFF) * 8;  // byte offset
        int      more_frags   = (frag_off_raw >> 13) & 1;
        int      dont_frag    = (frag_off_raw >> 14) & 1;

        // Is this a fragment? (offset != 0) or (offset == 0 and MF=1)
        if (frag_offset == 0 && !more_frags) continue;  // not a fragment

        uint16_t ip_id  = ntohs(iph->id);
        uint32_t src_ip = iph->saddr;
        uint32_t dst_ip = iph->daddr;
        uint8_t  proto  = iph->protocol;

        int data_len = n - ip_hdr_len;

        printf("Fragment received: id=0x%04x offset=%d len=%d MF=%d\n",
               ip_id, frag_offset, data_len, more_frags);

        Datagram *dg = find_or_create(ip_id, src_ip, dst_ip, proto);
        if (!dg) { printf("Fragment table full!\n"); continue; }

        // Check timeout
        if (time(NULL) - dg->first_seen > TIMEOUT_SEC) {
            printf("  Reassembly timeout for id=0x%04x — discarding\n", ip_id);
            memset(dg, 0, sizeof(Datagram));
            continue;
        }

        // Add fragment to table
        if (dg->frag_count < MAX_FRAGS) {
            Fragment *f = &dg->frags[dg->frag_count++];
            f->offset = frag_offset;
            f->len    = data_len;
            f->valid  = 1;
            memcpy(f->data, buf + ip_hdr_len, data_len);
            dg->received += data_len;
        }

        // If this is the last fragment, we now know total length
        if (!more_frags) {
            dg->total_len = frag_offset + data_len;
            printf("  Last fragment — total datagram size: %d bytes\n",
                   dg->total_len);
        }

        // Try to reassemble
        int complete_len = 0;
        uint8_t *complete = try_reassemble(dg, &complete_len);
        if (complete) {
            printf("  REASSEMBLY COMPLETE: %d bytes\n", complete_len);
            // Parse UDP header (first 8 bytes)
            struct udphdr *udph = (struct udphdr *)complete;
            printf("  UDP: src=%d dst=%d len=%d\n",
                   ntohs(udph->source), ntohs(udph->dest), ntohs(udph->len));
            // Process payload...
            free(complete);
            // Clean up datagram entry
            memset(dg, 0, sizeof(Datagram));
        }
    }

    close(sock);
    return 0;
}
```

### 12.3 Setting DF Bit and MSS Clamping in C

```c
// Set DF bit on a UDP socket to enable PMTUD
int sock = socket(AF_INET, SOCK_DGRAM, 0);

// Linux: IP_MTU_DISCOVER
int pmtudisc = IP_PMTUDISC_DO;  // set DF=1 always
setsockopt(sock, IPPROTO_IP, IP_MTU_DISCOVER, &pmtudisc, sizeof(pmtudisc));

// After ICMP Frag Needed is received, query the discovered MTU:
int mtu;
socklen_t mtu_len = sizeof(mtu);
getsockopt(sock, IPPROTO_IP, IP_MTU, &mtu, &mtu_len);
printf("Discovered path MTU: %d\n", mtu);

// For TCP: kernel handles this automatically when TCP_NODELAY is used.
// You can also query current MSS:
int mss;
socklen_t mss_len = sizeof(mss);
getsockopt(tcp_sock, IPPROTO_TCP, TCP_MAXSEG, &mss, &mss_len);
printf("Current TCP MSS: %d\n", mss);
```

---

## 13. Rust: Building a UDP Chunker and TCP Stream Handler

### 13.1 Rust TCP File Transfer with Explicit Buffer Management

```rust
// Cargo.toml:
// [dependencies]
// tokio = { version = "1", features = ["full"] }

use std::path::Path;
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader, BufWriter};
use tokio::net::{TcpListener, TcpStream};

// Optimal buffer size: large enough to keep pipeline full,
// aligned to common MSS (1460 bytes) or page size (4096).
// Common choice: 64KB (44 TCP segments worth of data).
// The kernel's TCP send buffer (sk_sndbuf) is typically 128KB–4MB.
const CHUNK_SIZE: usize = 65536; // 64KB

/// Sender: reads file, sends over TCP.
/// The kernel's TCP stack will split this into MSS-sized segments automatically.
/// With TSO enabled on the NIC, even CHUNK_SIZE-sized writes are efficient.
pub async fn send_file(path: &Path, addr: &str) -> std::io::Result<()> {
    let stream = TcpStream::connect(addr).await?;

    // Disable Nagle's algorithm for lower latency (optional for bulk transfer)
    // Nagle buffers small writes — we don't want that for large sequential sends.
    stream.set_nodelay(false)?; // keep Nagle ON for bulk file transfer

    let mut writer = BufWriter::with_capacity(CHUNK_SIZE, stream);
    let mut file   = BufReader::new(File::open(path).await?);

    let file_size = file.get_ref().metadata().await?.len();

    // Send file size header (8 bytes, big-endian)
    writer.write_u64(file_size).await?;

    let mut buf = vec![0u8; CHUNK_SIZE];
    let mut total_sent: u64 = 0;

    loop {
        let n = file.read(&mut buf).await?;
        if n == 0 { break; }

        // write_all() loops internally until all bytes are written to the
        // kernel socket buffer — it handles partial writes from TCP backpressure.
        writer.write_all(&buf[..n]).await?;

        total_sent += n as u64;

        // Print progress every 10MB
        if total_sent % (10 * 1024 * 1024) == 0 {
            let pct = total_sent * 100 / file_size;
            eprintln!("Sent: {}MB / {}MB ({}%)",
                      total_sent / 1_048_576,
                      file_size / 1_048_576,
                      pct);
        }
    }

    writer.flush().await?; // flush BufWriter's internal buffer

    println!("File sent: {} bytes", total_sent);
    Ok(())
}

/// Receiver: receives over TCP, writes to file.
/// TCP delivers data in-order and complete — no reassembly needed by us.
pub async fn receive_file(output_path: &Path, bind_addr: &str) -> std::io::Result<()> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("Listening on {}", bind_addr);

    let (stream, peer) = listener.accept().await?;
    println!("Connection from {}", peer);

    let mut reader = BufReader::with_capacity(CHUNK_SIZE, stream);
    let mut file   = BufWriter::new(File::create(output_path).await?);

    // Read file size header
    let file_size = reader.read_u64().await?;
    println!("Receiving {} bytes ({} MB)", file_size, file_size / 1_048_576);

    let mut buf = vec![0u8; CHUNK_SIZE];
    let mut total_received: u64 = 0;

    loop {
        let remaining = (file_size - total_received).min(CHUNK_SIZE as u64) as usize;
        if remaining == 0 { break; }

        // read() may return fewer bytes than requested — TCP gives us
        // whatever is currently in the receive buffer.
        // read_exact() would block until exactly `remaining` bytes arrive.
        let n = reader.read(&mut buf[..remaining]).await?;
        if n == 0 {
            return Err(std::io::Error::new(
                std::io::ErrorKind::UnexpectedEof,
                "Connection closed before all data received",
            ));
        }

        file.write_all(&buf[..n]).await?;
        total_received += n as u64;
    }

    file.flush().await?;
    println!("File received: {} bytes → {:?}", total_received, output_path);
    Ok(())
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("send") => {
            let path = Path::new(args.get(2).expect("file path"));
            let addr = args.get(3).unwrap_or(&"127.0.0.1:8080".to_string());
            send_file(path, addr).await.unwrap();
        }
        Some("recv") => {
            let path = Path::new(args.get(2).expect("output path"));
            let addr = args.get(3).unwrap_or(&"0.0.0.0:8080".to_string());
            receive_file(path, addr).await.unwrap();
        }
        _ => eprintln!("Usage: {} send <file> [addr:port]\n       {} recv <outfile> [addr:port]",
                       args[0], args[0]),
    }
}
```

### 13.2 Rust UDP Fragmenter/Defragmenter

```rust
// UDP doesn't give you reassembly — implement it yourself.
// This is what QUIC and other UDP-based protocols do internally.

use std::collections::HashMap;
use std::net::UdpSocket;
use std::time::{Duration, Instant};

const MAX_UDP_PAYLOAD: usize = 1400; // leave room for UDP + IP headers
const REASSEMBLY_TIMEOUT: Duration = Duration::from_secs(30);

/// Application-level fragment header (prepended to each UDP packet).
/// This is analogous to the IP fragment header, but at application level.
#[repr(C)]
#[derive(Clone, Copy, Debug)]
struct FragHeader {
    msg_id:    u32,  // unique per-message ID (like IP Identification)
    frag_idx:  u16,  // zero-based fragment index
    frag_total:u16,  // total number of fragments
    msg_len:   u32,  // total message length (for pre-allocation)
}

impl FragHeader {
    fn to_bytes(&self) -> [u8; 12] {
        let mut b = [0u8; 12];
        b[0..4].copy_from_slice(&self.msg_id.to_be_bytes());
        b[4..6].copy_from_slice(&self.frag_idx.to_be_bytes());
        b[6..8].copy_from_slice(&self.frag_total.to_be_bytes());
        b[8..12].copy_from_slice(&self.msg_len.to_be_bytes());
        b
    }

    fn from_bytes(b: &[u8]) -> Option<Self> {
        if b.len() < 12 { return None; }
        Some(FragHeader {
            msg_id:     u32::from_be_bytes(b[0..4].try_into().ok()?),
            frag_idx:   u16::from_be_bytes(b[4..6].try_into().ok()?),
            frag_total: u16::from_be_bytes(b[6..8].try_into().ok()?),
            msg_len:    u32::from_be_bytes(b[8..12].try_into().ok()?),
        })
    }
}

const FRAG_HEADER_LEN: usize = 12;
const DATA_PER_FRAG: usize   = MAX_UDP_PAYLOAD - FRAG_HEADER_LEN; // 1388 bytes

/// Send a large message fragmented over UDP.
pub fn send_fragmented(sock: &UdpSocket, dst: &str, data: &[u8]) -> std::io::Result<()> {
    static MSG_COUNTER: std::sync::atomic::AtomicU32
        = std::sync::atomic::AtomicU32::new(1);

    let msg_id = MSG_COUNTER.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let total_frags = (data.len() + DATA_PER_FRAG - 1) / DATA_PER_FRAG;

    println!("Sending {} bytes in {} fragments (max {}/frag)",
             data.len(), total_frags, DATA_PER_FRAG);

    let mut packet = vec![0u8; MAX_UDP_PAYLOAD];

    for (idx, chunk) in data.chunks(DATA_PER_FRAG).enumerate() {
        let hdr = FragHeader {
            msg_id,
            frag_idx:   idx as u16,
            frag_total: total_frags as u16,
            msg_len:    data.len() as u32,
        };

        let hdr_bytes = hdr.to_bytes();
        packet[..FRAG_HEADER_LEN].copy_from_slice(&hdr_bytes);
        packet[FRAG_HEADER_LEN..FRAG_HEADER_LEN + chunk.len()].copy_from_slice(chunk);

        let send_len = FRAG_HEADER_LEN + chunk.len();
        sock.send_to(&packet[..send_len], dst)?;

        println!("  Sent fragment {}/{}: {} bytes", idx + 1, total_frags, chunk.len());
    }

    Ok(())
}

/// Reassembly buffer for one in-progress message.
struct PendingMsg {
    data:        Vec<Option<Vec<u8>>>,  // indexed by frag_idx
    received:    usize,
    total_frags: usize,
    msg_len:     usize,
    first_seen:  Instant,
}

/// Receive and reassemble fragmented UDP messages.
pub fn receive_defragmented(sock: &UdpSocket) -> std::io::Result<Vec<u8>> {
    let mut pending: HashMap<u32, PendingMsg> = HashMap::new();
    let mut buf = vec![0u8; MAX_UDP_PAYLOAD + 100];

    loop {
        let (n, _src) = sock.recv_from(&mut buf)?;

        // Parse fragment header
        let hdr = match FragHeader::from_bytes(&buf[..n]) {
            Some(h) => h,
            None => { eprintln!("Malformed packet"); continue; }
        };

        let frag_data = &buf[FRAG_HEADER_LEN..n];

        // Expire old incomplete messages
        pending.retain(|_, pm| pm.first_seen.elapsed() < REASSEMBLY_TIMEOUT);

        // Find or create reassembly buffer
        let pm = pending.entry(hdr.msg_id).or_insert_with(|| {
            let total = hdr.frag_total as usize;
            PendingMsg {
                data:        vec![None; total],
                received:    0,
                total_frags: total,
                msg_len:     hdr.msg_len as usize,
                first_seen:  Instant::now(),
            }
        });

        let idx = hdr.frag_idx as usize;
        if idx >= pm.total_frags {
            eprintln!("Fragment index {} out of range {}", idx, pm.total_frags);
            continue;
        }

        if pm.data[idx].is_none() {
            pm.data[idx] = Some(frag_data.to_vec());
            pm.received += 1;
            println!("  Received fragment {}/{} for msg_id={}",
                     idx + 1, pm.total_frags, hdr.msg_id);
        }

        // Check if complete
        if pm.received == pm.total_frags {
            println!("  Message {} complete — reassembling {} bytes",
                     hdr.msg_id, pm.msg_len);

            let mut result = Vec::with_capacity(pm.msg_len);
            for part in &pm.data {
                result.extend_from_slice(part.as_ref().unwrap());
            }

            pending.remove(&hdr.msg_id);
            return Ok(result);
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    match args.get(1).map(|s| s.as_str()) {
        Some("send") => {
            let sock = UdpSocket::bind("0.0.0.0:0").unwrap();
            let msg = b"A".repeat(50_000); // 50KB — requires ~36 fragments
            send_fragmented(&sock, "127.0.0.1:9000", &msg).unwrap();
        }
        Some("recv") => {
            let sock = UdpSocket::bind("0.0.0.0:9000").unwrap();
            let data = receive_defragmented(&sock).unwrap();
            println!("Received: {} bytes", data.len());
        }
        _ => eprintln!("Usage: {} [send|recv]", args[0]),
    }
}
```

### 13.3 Querying MTU and TCP Info in Rust

```rust
use std::net::TcpStream;
use std::os::unix::io::AsRawFd;

fn get_tcp_info(stream: &TcpStream) -> std::io::Result<()> {
    let fd = stream.as_raw_fd();

    unsafe {
        // TCP_INFO gives rich stats about the connection
        #[repr(C)]
        struct TcpInfo {
            tcpi_state:         u8,
            tcpi_ca_state:      u8,
            tcpi_retransmits:   u8,
            tcpi_probes:        u8,
            tcpi_backoff:       u8,
            tcpi_options:       u8,
            tcpi_snd_rcv_wscale: u8,
            _pad: u8,
            tcpi_rto:           u32,
            tcpi_ato:           u32,
            tcpi_snd_mss:       u32,  // ← CURRENT MSS
            tcpi_rcv_mss:       u32,
            tcpi_unacked:       u32,
            tcpi_sacked:        u32,
            tcpi_lost:          u32,
            tcpi_retrans:       u32,
            tcpi_fackets:       u32,
            tcpi_last_data_sent: u32,
            tcpi_last_ack_sent:  u32,
            tcpi_last_data_recv: u32,
            tcpi_last_ack_recv:  u32,
            tcpi_pmtu:          u32,  // ← PATH MTU
            tcpi_rcv_ssthresh:  u32,
            tcpi_rtt:           u32,  // smoothed RTT (microseconds)
            tcpi_rttvar:        u32,
            tcpi_snd_ssthresh:  u32,
            tcpi_snd_cwnd:      u32,  // ← CONGESTION WINDOW (segments)
            tcpi_advmss:        u32,
            tcpi_reordering:    u32,
        }

        let mut info = std::mem::zeroed::<TcpInfo>();
        let mut len  = std::mem::size_of::<TcpInfo>() as libc::socklen_t;

        let TCP_INFO: libc::c_int = 11;
        if libc::getsockopt(fd, libc::IPPROTO_TCP, TCP_INFO,
                            &mut info as *mut _ as *mut libc::c_void,
                            &mut len) == 0 {
            println!("TCP Info:");
            println!("  MSS:                {} bytes", info.tcpi_snd_mss);
            println!("  Path MTU:           {} bytes", info.tcpi_pmtu);
            println!("  Congestion window:  {} segments", info.tcpi_snd_cwnd);
            println!("  Smooth RTT:         {} μs", info.tcpi_rtt);
            println!("  RTT variance:       {} μs", info.tcpi_rttvar);
            println!("  Unacked segments:   {}", info.tcpi_unacked);
            println!("  Retransmits:        {}", info.tcpi_retrans);
        }
    }
    Ok(())
}
```

---

## 14. Go: Implementing Fragmentation-Aware File Transfer

### 14.1 Go TCP File Transfer with Backpressure

```go
// main.go
// Usage:
//   go run main.go send <file> [host:port]
//   go run main.go recv <outfile> [host:port]

package main

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

// Buffer size aligned to typical TSO super-segment size.
// Go's net package uses the OS TCP stack, which handles MSS segmentation.
// Our job is just to keep the kernel send buffer full.
const bufferSize = 1 << 17 // 128 KB

// sendFile connects to addr and sends the file at path.
// The OS TCP stack splits our writes into MSS-sized segments automatically.
func sendFile(path, addr string) error {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return fmt.Errorf("dial: %w", err)
	}
	defer conn.Close()

	// Optional: disable Nagle for bulk transfer (often not needed)
	if tc, ok := conn.(*net.TCPConn); ok {
		tc.SetNoDelay(false) // keep Nagle ON — it helps bulk throughput
		tc.SetWriteBuffer(1 << 20) // 1MB kernel send buffer (default is ~128KB)
		tc.SetReadBuffer(1 << 20)
	}

	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	stat, _ := f.Stat()
	fileSize := stat.Size()

	// Send 8-byte big-endian size header
	var header [8]byte
	binary.BigEndian.PutUint64(header[:], uint64(fileSize))
	if _, err := conn.Write(header[:]); err != nil {
		return err
	}

	// Use io.Copy with a custom buffer.
	// io.Copy internally calls Read() then Write() in a loop.
	// Each Write() goes to the kernel socket buffer; TCP sends it asynchronously.
	start := time.Now()
	buf := make([]byte, bufferSize)
	sent, err := io.CopyBuffer(conn, f, buf)
	if err != nil {
		return fmt.Errorf("copy: %w", err)
	}

	elapsed := time.Since(start)
	mbps := float64(sent) / elapsed.Seconds() / 1e6
	fmt.Printf("Sent %d bytes in %v (%.1f MB/s)\n", sent, elapsed, mbps)
	return nil
}

// receiveFile listens on addr and writes incoming data to path.
func receiveFile(path, addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	defer ln.Close()

	fmt.Printf("Listening on %s\n", addr)
	conn, err := ln.Accept()
	if err != nil {
		return err
	}
	defer conn.Close()

	if tc, ok := conn.(*net.TCPConn); ok {
		tc.SetReadBuffer(1 << 20)
	}

	// Read 8-byte size header
	var header [8]byte
	if _, err := io.ReadFull(conn, header[:]); err != nil {
		return fmt.Errorf("read header: %w", err)
	}
	fileSize := binary.BigEndian.Uint64(header[:])
	fmt.Printf("Receiving %d bytes (%d MB)\n", fileSize, fileSize>>20)

	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	buf := make([]byte, bufferSize)
	start := time.Now()

	// io.ReadFull would block until all data arrives — use LimitedReader
	// to not read past fileSize, then io.CopyBuffer for efficiency.
	limited := &io.LimitedReader{R: conn, N: int64(fileSize)}
	received, err := io.CopyBuffer(f, limited, buf)
	if err != nil {
		return fmt.Errorf("receive: %w", err)
	}

	elapsed := time.Since(start)
	mbps := float64(received) / elapsed.Seconds() / 1e6
	fmt.Printf("Received %d bytes in %v (%.1f MB/s)\n", received, elapsed, mbps)
	return nil
}

func main() {
	args := os.Args
	if len(args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: %s [send|recv] <file> [addr:port]\n", args[0])
		os.Exit(1)
	}

	addr := "127.0.0.1:8080"
	if len(args) >= 4 {
		addr = args[3]
	}

	var err error
	switch args[1] {
	case "send":
		err = sendFile(args[2], addr)
	case "recv":
		err = receiveFile(args[2], addr)
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n", args[1])
		os.Exit(1)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

### 14.2 Go: Querying Path MTU

```go
package main

import (
	"fmt"
	"net"
	"syscall"
	"unsafe"
)

// getTCPInfo reads TCP_INFO from the kernel for a connected TCP socket.
// This gives you live MSS, PMTU, RTT, cwnd, and retransmit counts.
type TCPInfo struct {
	State          uint8
	CaState        uint8
	Retransmits    uint8
	Probes         uint8
	Backoff         uint8
	Options        uint8
	Pad            [2]uint8
	Rto            uint32
	Ato            uint32
	SndMss         uint32 // current MSS (bytes)
	RcvMss         uint32
	Unacked        uint32
	Sacked         uint32
	Lost           uint32
	Retrans        uint32
	Fackets        uint32
	LastDataSent   uint32
	LastAckSent    uint32
	LastDataRecv   uint32
	LastAckRecv    uint32
	Pmtu           uint32 // path MTU (bytes)
	RcvSsthresh    uint32
	Rtt            uint32 // smoothed RTT (microseconds)
	Rttvar         uint32
	SndSsthresh    uint32
	SndCwnd        uint32 // congestion window (in segments)
	Advmss         uint32
	Reordering     uint32
}

func getTCPInfo(conn *net.TCPConn) (*TCPInfo, error) {
	rawConn, err := conn.SyscallConn()
	if err != nil {
		return nil, err
	}

	var info TCPInfo
	var sockErr error

	rawConn.Control(func(fd uintptr) {
		size := uint32(unsafe.Sizeof(info))
		_, _, errno := syscall.Syscall6(
			syscall.SYS_GETSOCKOPT,
			fd,
			uintptr(syscall.IPPROTO_TCP),
			uintptr(11), // TCP_INFO = 11
			uintptr(unsafe.Pointer(&info)),
			uintptr(unsafe.Pointer(&size)),
			0,
		)
		if errno != 0 {
			sockErr = errno
		}
	})

	if sockErr != nil {
		return nil, sockErr
	}
	return &info, nil
}

func inspectConnection(addr string) error {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return err
	}
	defer conn.Close()

	tc := conn.(*net.TCPConn)
	info, err := getTCPInfo(tc)
	if err != nil {
		return fmt.Errorf("TCP_INFO: %w", err)
	}

	fmt.Printf("=== TCP Connection Info ===\n")
	fmt.Printf("  Path MTU:           %d bytes\n",   info.Pmtu)
	fmt.Printf("  Current MSS:        %d bytes\n",   info.SndMss)
	fmt.Printf("  Congestion window:  %d segments\n", info.SndCwnd)
	fmt.Printf("  Smoothed RTT:       %d μs\n",      info.Rtt)
	fmt.Printf("  RTT variance:       %d μs\n",      info.Rttvar)
	fmt.Printf("  Unacked:            %d\n",          info.Unacked)
	fmt.Printf("  Retransmits:        %d\n",          info.Retrans)

	// Effective throughput limit (BDP: Bandwidth-Delay Product)
	// max_throughput = cwnd * MSS / RTT
	if info.Rtt > 0 {
		cwndBytes := uint64(info.SndCwnd) * uint64(info.SndMss)
		rttSec := float64(info.Rtt) / 1e6
		maxMbps := float64(cwndBytes) / rttSec / 1e6 * 8
		fmt.Printf("  BDP throughput cap: %.1f Mbps\n", maxMbps)
	}

	return nil
}
```

### 14.3 Go UDP Fragmentation with Reliable Delivery

```go
// Implements application-level fragmentation + simple ARQ (Automatic Repeat reQuest)
// over UDP — similar to how QUIC works conceptually.

package main

import (
	"encoding/binary"
	"fmt"
	"net"
	"sync"
	"time"
)

const (
	maxPayload    = 1400              // conservative UDP payload
	headerLen     = 13               // 4+2+2+4+1 bytes
	maxDataPerFrag = maxPayload - headerLen
	ackTimeout    = 200 * time.Millisecond
	maxRetries    = 5
)

// FragPacket is our application-level fragment.
// Analogous to an IP fragment header + data.
//
//  Offset  Size  Field
//  0       4     message_id  (unique per message, like IP Identification)
//  4       2     frag_index  (0-based)
//  6       2     frag_total
//  8       4     message_len
//  12      1     flags: 0x01 = ACK packet, 0x02 = NACK
//  13      N     data
type FragPacket struct {
	MsgID    uint32
	FragIdx  uint16
	FragTotal uint16
	MsgLen   uint32
	Flags    uint8
	Data     []byte
}

func encodeFragPacket(p *FragPacket) []byte {
	buf := make([]byte, headerLen+len(p.Data))
	binary.BigEndian.PutUint32(buf[0:], p.MsgID)
	binary.BigEndian.PutUint16(buf[4:], p.FragIdx)
	binary.BigEndian.PutUint16(buf[6:], p.FragTotal)
	binary.BigEndian.PutUint32(buf[8:], p.MsgLen)
	buf[12] = p.Flags
	copy(buf[headerLen:], p.Data)
	return buf
}

func decodeFragPacket(buf []byte) (*FragPacket, error) {
	if len(buf) < headerLen {
		return nil, fmt.Errorf("packet too short")
	}
	p := &FragPacket{
		MsgID:     binary.BigEndian.Uint32(buf[0:]),
		FragIdx:   binary.BigEndian.Uint16(buf[4:]),
		FragTotal: binary.BigEndian.Uint16(buf[6:]),
		MsgLen:    binary.BigEndian.Uint32(buf[8:]),
		Flags:     buf[12],
		Data:      append([]byte(nil), buf[headerLen:]...),
	}
	return p, nil
}

// Sender with per-fragment ACK (stop-and-wait for simplicity; use sliding window in production)
func sendWithACK(conn *net.UDPConn, dst *net.UDPAddr, msgID uint32, data []byte) error {
	total := (len(data) + maxDataPerFrag - 1) / maxDataPerFrag

	for idx, chunk := range chunked(data, maxDataPerFrag) {
		pkt := &FragPacket{
			MsgID:     msgID,
			FragIdx:   uint16(idx),
			FragTotal: uint16(total),
			MsgLen:    uint32(len(data)),
			Data:      chunk,
		}
		encoded := encodeFragPacket(pkt)

		for retry := 0; retry < maxRetries; retry++ {
			conn.WriteToUDP(encoded, dst)
			conn.SetReadDeadline(time.Now().Add(ackTimeout))

			buf := make([]byte, 64)
			n, _, err := conn.ReadFromUDP(buf)
			if err == nil && n >= headerLen {
				ack, _ := decodeFragPacket(buf[:n])
				if ack != nil && ack.Flags&0x01 != 0 &&
					ack.MsgID == msgID && ack.FragIdx == uint16(idx) {
					fmt.Printf("  ACK for fragment %d/%d\n", idx+1, total)
					break
				}
			}
			fmt.Printf("  Timeout/NACK for fragment %d — retry %d\n", idx, retry+1)
		}
	}
	return nil
}

func chunked(data []byte, size int) [][]byte {
	var chunks [][]byte
	for len(data) > 0 {
		n := size
		if n > len(data) {
			n = len(data)
		}
		chunks = append(chunks, data[:n])
		data = data[n:]
	}
	return chunks
}

// Receiver with ACK sending
type reassembler struct {
	mu      sync.Mutex
	pending map[uint32]*pendingMsg
}

type pendingMsg struct {
	frags    map[uint16][]byte
	total    uint16
	msgLen   uint32
	firstSeen time.Time
}

func (r *reassembler) addFragment(p *FragPacket) []byte {
	r.mu.Lock()
	defer r.mu.Unlock()

	pm, ok := r.pending[p.MsgID]
	if !ok {
		pm = &pendingMsg{
			frags:     make(map[uint16][]byte),
			total:     p.FragTotal,
			msgLen:    p.MsgLen,
			firstSeen: time.Now(),
		}
		r.pending[p.MsgID] = pm
	}

	pm.frags[p.FragIdx] = p.Data

	if len(pm.frags) < int(pm.total) {
		return nil // not complete yet
	}

	// Reassemble
	result := make([]byte, 0, pm.msgLen)
	for i := uint16(0); i < pm.total; i++ {
		result = append(result, pm.frags[i]...)
	}

	delete(r.pending, p.MsgID)
	return result
}

func receiveWithACK(conn *net.UDPConn) ([]byte, error) {
	r := &reassembler{pending: make(map[uint32]*pendingMsg)}
	buf := make([]byte, maxPayload+100)

	for {
		n, src, err := conn.ReadFromUDP(buf)
		if err != nil {
			return nil, err
		}

		pkt, err := decodeFragPacket(buf[:n])
		if err != nil {
			continue
		}

		fmt.Printf("Received fragment %d/%d for msg %d\n",
			pkt.FragIdx+1, pkt.FragTotal, pkt.MsgID)

		// Send ACK
		ack := encodeFragPacket(&FragPacket{
			MsgID:   pkt.MsgID,
			FragIdx: pkt.FragIdx,
			Flags:   0x01, // ACK flag
		})
		conn.WriteToUDP(ack, src)

		if result := r.addFragment(pkt); result != nil {
			return result, nil
		}
	}
}
```

---

## 15. Key Data Structures Reference

### 15.1 Linux Kernel Structures

```
struct sk_buff          → Universal packet container (include/linux/skbuff.h)
struct iphdr            → IPv4 header (include/linux/ip.h)
struct ipv6hdr          → IPv6 header (include/linux/ipv6.h)
struct tcphdr           → TCP header (include/linux/tcp.h)
struct udphdr           → UDP header (include/linux/udp.h)
struct ethhdr           → Ethernet header (include/linux/if_ether.h)
struct tcp_sock         → TCP socket state (include/linux/tcp.h)
struct inet_frag_queue  → IP reassembly queue (include/net/inet_frag.h)
struct ipq              → IPv4 specific frag queue (net/ipv4/ip_fragment.c)
struct rtable           → IPv4 routing table entry (include/net/route.h)
struct net_device       → Network interface (include/linux/netdevice.h)
struct napi_struct      → NAPI poll for RX (include/linux/netdevice.h)
```

### 15.2 Key Kernel Files

```
net/ipv4/ip_output.c    → ip_queue_xmit(), ip_fragment(), ip_finish_output()
net/ipv4/ip_input.c     → ip_rcv(), ip_rcv_finish()
net/ipv4/ip_fragment.c  → ip_defrag(), ip_frag_reasm()
net/ipv4/tcp.c          → tcp_sendmsg(), tcp_recvmsg()
net/ipv4/tcp_output.c   → tcp_write_xmit(), tcp_transmit_skb()
net/ipv4/tcp_input.c    → tcp_rcv_established(), tcp_data_queue()
net/ipv4/udp.c          → udp_sendmsg(), udp_rcv()
net/core/dev.c          → dev_queue_xmit(), netif_receive_skb()
net/core/gso.c          → skb_gso_segment()  (GSO segmentation)
net/core/gro.c          → napi_gro_receive() (GRO coalescing)
include/linux/skbuff.h  → struct sk_buff definition
include/net/tcp.h       → TCP constants, inline functions
```

### 15.3 Important sysctl Parameters

```bash
# TCP buffer sizes (min, default, max in bytes)
net.ipv4.tcp_rmem = 4096 131072 6291456    # receive buffer
net.ipv4.tcp_wmem = 4096  16384 4194304    # send buffer

# IP fragment reassembly
net.ipv4.ipfrag_time = 30           # seconds to wait for all fragments
net.ipv4.ipfrag_high_thresh = 4MB   # max memory for frag queues
net.ipv4.ipfrag_low_thresh  = 3MB   # reclaim memory below this

# PMTUD / MTU probing
net.ipv4.tcp_mtu_probing = 0        # 0=off, 1=on when PMTUD blackhole, 2=always
net.ipv4.tcp_base_mss     = 1024    # starting MSS when probing
net.ipv4.ip_no_pmtu_disc  = 0       # 0=PMTUD enabled (DF=1 on TCP sockets)

# TCP congestion control
net.ipv4.tcp_congestion_control = cubic   # or bbr, reno, htcp
net.core.rmem_max = 134217728       # max receive buffer (128MB)
net.core.wmem_max = 134217728       # max send buffer (128MB)

# GSO/GRO
net.core.gro_normal_batch = 8       # max packets coalesced by GRO
```

---

## 16. Common Pitfalls and Debugging

### 16.1 Diagnosing Fragmentation Problems

```bash
# Watch IP fragmentation counters in real-time
watch -n1 "cat /proc/net/snmp | grep -A1 Ip | tail -1 | \
  awk '{print \"ReasmOKs=\"$14, \"ReasmFails=\"$15, \"FragOKs=\"$16, \"FragFails=\"$17}'"

# Or use ss to check TCP socket state
ss -tin dst <server_ip>
# Output includes: mss:1460 pmtu:1500 rcvmss:536 advmss:1460
# Also shows cwnd, ssthresh, rtt, etc.

# Check if MTU is causing issues on a path
ping -M do -s 1472 <destination>   # 1472 + 28(IP+ICMP hdr) = 1500 byte packet
# If you get "Message too long" but smaller sizes work → PMTUD blackhole

# Trace path MTU using tracepath
tracepath <destination>
# Shows MTU at each hop: "pmtu 1500", "pmtu 1492", etc.

# Watch retransmissions (fragmentation-related packet loss)
ss -s
# Shows: retrans - number of TCP retransmissions

# TCP segment size in Wireshark/tcpdump:
tcpdump -i eth0 -nn 'tcp[tcpflags] & (tcp-syn) != 0' -v
# Look for: mss <value> in TCP options during handshake
```

### 16.2 The Nagle Algorithm and Small Writes

Nagle's algorithm (RFC 896) prevents "silly window syndrome" by buffering small writes:

```
 Rule: send immediately if:
   (a) no unacknowledged data in flight (pipe is empty), OR
   (b) enough data to fill an MSS-sized segment

 Otherwise: buffer and wait for ACK.
```

**Pitfall**: If you write header (20 bytes) and then body (1MB) separately, Nagle will hold the header for up to one RTT waiting for an ACK. Fix:

```c
// Option 1: Disable Nagle (TCP_NODELAY)
int one = 1;
setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));

// Option 2: Use TCP_CORK — buffer all writes, then flush with uncork
int corked = 1;
setsockopt(sock, IPPROTO_TCP, TCP_CORK, &corked, sizeof(corked));
send(sock, header, sizeof(header), 0);
send(sock, body, body_len, 0);
corked = 0;
setsockopt(sock, IPPROTO_TCP, TCP_CORK, &corked, sizeof(corked)); // flushes

// Option 3: Use writev() to combine into one syscall
struct iovec iov[2] = {
    { .iov_base = header, .iov_len = sizeof(header) },
    { .iov_base = body,   .iov_len = body_len }
};
writev(sock, iov, 2);
```

### 16.3 IP Fragmentation is Harmful for Performance

In practice, **IP-level fragmentation is avoided** for several reasons:

1. **Loss amplification**: If one fragment is lost, the entire datagram must be retransmitted. For a datagram split into N fragments, loss probability = `1 - (1 - P_loss)^N` ≈ `N * P_loss` for small P.

2. **Reassembly overhead**: The receiver must maintain reassembly buffers and timers.

3. **Firewall traversal**: Many firewalls drop fragments because stateful inspection is hard — they can't examine the transport header (TCP/UDP ports) in non-first fragments.

4. **Router processing**: Fragmentation and reassembly burn CPU cycles in routers.

**Best practice**: Always use PMTUD + TCP (which prevents IP fragmentation), or QUIC. If you use UDP, keep your application-level datagrams below the path MTU (typically 1400 bytes to be safe with VPNs, tunnels, etc.).

### 16.4 The 576-Byte Problem

IPv4 guarantees that all hosts can handle datagrams up to **576 bytes**. Some old or misconfigured systems (VPN devices, legacy networks) have an effective MTU of 576 bytes, causing large TCP connections to silently break if PMTUD fails.

The "safe" minimum MSS is `576 - 20 - 20 = 536 bytes`. You'll see this as the initial MSS in some kernel logs.

### 16.5 VPN Tunnels and Double Fragmentation

VPNs (OpenVPN, WireGuard, IPsec) encapsulate packets in another IP packet, adding 20–80 bytes of overhead:

```
 Original TCP segment:
 [ETH 14B][IP 20B][TCP 20B][DATA 1460B] = 1514 bytes total, fits in 1500B MTU

 After VPN encapsulation (WireGuard adds ~60 bytes):
 [ETH 14B][IP 20B][UDP 8B][WireGuard 32B][IP 20B][TCP 20B][DATA 1460B]
 = 1574 bytes → EXCEEDS MTU!

 Solution: VPN reduces effective MTU:
 WireGuard sets MTU = 1420 (leaving room for its overhead)
 → TCP MSS = 1420 - 40 = 1380 bytes
```

WireGuard does this automatically. OpenVPN requires manual `--mssfix 1380` configuration.

---

## 17. Mental Model Summary

Here is the complete mental model, distilled:

```
QUESTION: Who splits the 1GB file?

ANSWER (layered):

1. YOUR APPLICATION
   - You call send() / write() / sendfile()
   - The OS copies data into the kernel send buffer
   - You see one contiguous write; the kernel handles the rest

2. TCP LAYER (net/ipv4/tcp_output.c: tcp_write_xmit)
   - Splits the byte stream into segments of size MSS (typically 1460 bytes)
   - Adds TCP header (seq numbers, ack, flags, checksum)
   - Enforces flow control (receiver window) and congestion control (cwnd)
   - THIS IS THE PRIMARY FRAGMENTATION for reliable streams

3. IP LAYER (net/ipv4/ip_output.c: ip_fragment)
   - Rarely needed with TCP (TCP already sizes segments to fit MTU)
   - Needed for UDP or if MTU shrinks along the path
   - Adds IP header with Identification + Fragment Offset
   - DF=1 on TCP sockets prevents this and enables PMTUD instead

4. NIC / DRIVER (e.g., ixgbe_xmit_frame)
   - With TSO: CPU hands large super-segment; NIC does TCP splitting in hardware
   - Without TSO: GSO does splitting in software just before driver

QUESTION: Who reassembles?

1. IP LAYER at receiver (net/ipv4/ip_fragment.c: ip_defrag)
   - Reassembles IP fragments using (src,dst,id,proto) key
   - 30-second timeout; drops incomplete datagrams
   - Delivers complete datagram to TCP/UDP

2. TCP LAYER at receiver (net/ipv4/tcp_input.c: tcp_rcv_established)
   - Buffers out-of-order segments in red-black tree
   - Reorders and delivers in-sequence bytes to application
   - ACKs control retransmission of lost segments

3. YOUR APPLICATION
   - read() / recv() returns a stream of bytes
   - Your protocol (HTTP, gRPC, custom) reassembles into messages

KEY NUMBERS TO REMEMBER:
  Ethernet MTU         = 1500 bytes   (the root cause of all fragmentation)
  IPv4 header          = 20 bytes minimum
  TCP header           = 20 bytes minimum
  Default TCP MSS      = 1460 bytes   (= 1500 - 20 - 20)
  IPv4 max datagram    = 65535 bytes
  IPv6 minimum MTU     = 1280 bytes
  IP frag timeout      = 30 seconds
  TSO super-segment    = up to 64KB
  Jumbo frame MTU      = 9000 bytes
  Safe UDP payload     = 1400 bytes   (conservative, works through VPNs)
```

```
LAYERED RESPONSIBILITY TABLE:

  +------------------+------------------+------------------+------------------+
  |      Layer       |    Who Splits    |  When It Splits  |  Who Reassembles |
  +------------------+------------------+------------------+------------------+
  | Application      | Your code        | Protocol-defined | Your code        |
  +------------------+------------------+------------------+------------------+
  | TCP              | Kernel tcp.c     | Data > MSS       | Kernel tcp_input |
  |                  | tcp_write_xmit() | cwnd/wnd limit   | tcp_rcv_establ.  |
  +------------------+------------------+------------------+------------------+
  | IP               | Kernel ip_out.c  | Datagram > MTU   | Kernel ip_frag.c |
  |                  | ip_fragment()    | (DF=0 required)  | ip_defrag()      |
  +------------------+------------------+------------------+------------------+
  | NIC Hardware     | NIC firmware     | TSO enabled      | LRO / GRO        |
  |                  | (TSO)            | segment > MSS    | (GRO in kernel)  |
  +------------------+------------------+------------------+------------------+
  | Ethernet         | Nobody           | MTU enforced;    | Nobody           |
  |                  | (drop if too big)| drop oversized   | (no reassembly)  |
  +------------------+------------------+------------------+------------------+
```

---

*This document covers the complete theory, implementation, and debugging of network fragmentation across all layers of the TCP/IP stack. The goal is to give you the mental model to reason about any fragmentation-related behavior you encounter in production systems, network tools, or kernel code.*
