# Linux Traffic Control (tc) — Complete In-Depth Guide

> *"Control the flow of packets, and you control the network."*
> This guide builds from first principles to advanced internals — every concept
> explained before it is used.

---

## Table of Contents

1. [Mental Model: Why Traffic Control Exists](#1-mental-model-why-traffic-control-exists)
2. [Fundamental Concepts — Glossary First](#2-fundamental-concepts--glossary-first)
3. [Where tc Lives in the Linux Network Stack](#3-where-tc-lives-in-the-linux-network-stack)
4. [The Three Pillars of tc](#4-the-three-pillars-of-tc)
5. [Queueing Disciplines (qdiscs) — Deep Dive](#5-queueing-disciplines-qdiscs--deep-dive)
6. [Classless qdiscs](#6-classless-qdiscs)
7. [Classful qdiscs](#7-classful-qdiscs)
8. [Filters and Classifiers](#8-filters-and-classifiers)
9. [Actions (tc Actions Framework)](#9-actions-tc-actions-framework)
10. [Policing vs Shaping — The Core Distinction](#10-policing-vs-shaping--the-core-distinction)
11. [Token Bucket Algorithm — The Mathematical Heart](#11-token-bucket-algorithm--the-mathematical-heart)
12. [HTB — Hierarchical Token Bucket (Master Class)](#12-htb--hierarchical-token-bucket-master-class)
13. [HFSC — Hierarchical Fair Service Curve](#13-hfsc--hierarchical-fair-service-curve)
14. [FQ-CoDel — The Modern Default](#14-fq-codel--the-modern-default)
15. [CAKE — The Most Advanced Classless qdisc](#15-cake--the-most-advanced-classless-qdisc)
16. [netem — Network Emulation](#16-netem--network-emulation)
17. [IFB — Intermediate Functional Block (Ingress Shaping)](#17-ifb--intermediate-functional-block-ingress-shaping)
18. [tc Command Syntax — Complete Reference](#18-tc-command-syntax--complete-reference)
19. [Real-World Scenarios and Recipes](#19-real-world-scenarios-and-recipes)
20. [Internals: How tc Works in the Kernel](#20-internals-how-tc-works-in-the-kernel)
21. [Netlink Protocol — How Userspace Talks to tc](#21-netlink-protocol--how-userspace-talks-to-tc)
22. [XDP and eBPF Integration with tc](#22-xdp-and-ebpf-integration-with-tc)
23. [Performance Analysis and Debugging](#23-performance-analysis-and-debugging)
24. [Mental Models and Intuition Building](#24-mental-models-and-intuition-building)

---

## 1. Mental Model: Why Traffic Control Exists

### The Core Problem

Imagine a highway with 4 lanes merging into 1. Without rules, every car rushes
in and creates gridlock. A police officer managing the merge point IS traffic
control. In networking, **tc** is that officer — standing at every network
interface, deciding which packets go first, which wait, and which get dropped.

**The Fundamental Mismatch:**

```
Producer (CPU/Applications) can generate data FASTER than
the wire can carry it.

CPU Speed: nanoseconds per operation
1 Gbps wire: 1 bit per nanosecond (1000 bits per microsecond)

A 1500-byte packet (12,000 bits) takes 12 microseconds to transmit.
In that same time, CPU generates megabytes of data.

Result: QUEUES form. Someone must manage them.
```

### Why Not Just "First Come, First Served"?

```
Without tc (pure FIFO):

[Video Call]──┐
[SSH Session]─┼──► [FIFO Queue]──► Wire ──► Internet
[Huge Download]┘
              ^
              A 5GB download fills this queue.
              Your SSH keystrokes wait BEHIND gigabytes of file data.
              Result: 2-second lag on interactive sessions.

With tc (priority shaping):

[Video Call]──► [Priority Queue 1]──┐
[SSH Session]──► [Priority Queue 2]─┼──► Scheduler ──► Wire
[Huge Download]──► [Priority Queue 3]┘
                                     ^
                                     Scheduler sends Video/SSH first.
                                     Download gets remaining bandwidth.
                                     All three work smoothly.
```

### The tc Philosophy

tc implements **Quality of Service (QoS)** at the kernel level, with three
primary capabilities:

```
┌─────────────────────────────────────────────────────────┐
│                    tc Capabilities                       │
├─────────────────┬───────────────────┬───────────────────┤
│   SHAPING       │    SCHEDULING     │    POLICING        │
│                 │                   │                    │
│ Control the     │ Decide ORDER of   │ Enforce rate       │
│ RATE of traffic │ packet departure  │ limits by          │
│ (slow it down)  │ (who goes first)  │ dropping excess    │
│                 │                   │                    │
│ Buffers packets │ Implements        │ Hard enforcement   │
│ to smooth bursts│ priority/fairness │ no buffering       │
└─────────────────┴───────────────────┴───────────────────┘
```

---

## 2. Fundamental Concepts — Glossary First

Before going further, master these terms. They appear everywhere.

### Packet
The fundamental unit of data in networking. A chunk of bytes with a header
(source/destination IP, port, etc.) and payload (actual data). Size: typically
64 bytes to 1500 bytes (Ethernet MTU).

### Interface (NIC — Network Interface Card)
The hardware (or virtual) device through which packets enter/leave a machine.
Examples: `eth0`, `wlan0`, `lo`, `docker0`, `veth0`.

```
Physical:  eth0 (Ethernet), wlan0 (WiFi)
Virtual:   lo (loopback), tun0 (VPN tunnel), veth (container pair)
```

### Queue
A data structure (like a line at a bank) where packets wait before being sent.
The kernel manages queues per-interface.

### Egress / Ingress
- **Egress**: Traffic LEAVING the machine through an interface (outbound).
- **Ingress**: Traffic ARRIVING at the interface (inbound).

tc primarily acts on **egress**. Ingress control requires tricks (IFB, covered
later).

### Bandwidth
The maximum data transfer rate of a link. Measured in bits per second (bps),
Kbps, Mbps, Gbps.

```
1 Gbps = 1,000,000,000 bits per second = 125,000,000 bytes per second
       = ~125 MB/s
```

### Latency
The time it takes a packet to travel from source to destination. Composed of:
- **Propagation delay**: Physics — speed of light through medium.
- **Transmission delay**: Time to push bits onto the wire.
- **Queueing delay**: Time spent waiting in buffers.

tc primarily influences **queueing delay**.

### Throughput
Actual data transfer rate achieved (may be less than bandwidth due to protocol
overhead, congestion, errors).

### Jitter
Variation in packet arrival times. Enemy of real-time applications (video
calls, gaming, VoIP). A video call needs 30ms delay every frame — not 10ms
sometimes and 80ms other times.

### Queue Discipline (qdisc)
The **algorithm** that manages a packet queue. It decides:
1. When to accept a packet into the queue.
2. What order to send packets.
3. When to drop packets.

### Class
A subdivision within a classful qdisc. Packets are sorted into classes, and
each class can have different priority, rate, and even its own qdisc.

### Handle
A unique identifier for a qdisc or class. Format: `MAJOR:MINOR`
- `1:0` — Root qdisc with major number 1.
- `1:1` — First class under major 1.
- `1:10` — Another class.
- `ffff:` — Special: the ingress qdisc.

```
Handle Format:   MAJOR : MINOR
                  |         |
               Identifies  Identifies
               the qdisc   the class
               (1-65535)   (0 = qdisc itself)
                           (1+ = classes)
```

### Filter
Rules that classify packets into classes. Based on IP addresses, ports,
protocol type, DSCP bits, etc.

### Shaping
Smoothing traffic to not exceed a rate. Uses buffers — packets are delayed,
not dropped.

### Policing
Enforcing a rate limit by **dropping** packets that exceed the limit.
No buffering.

### DSCP (Differentiated Services Code Point)
6 bits in the IP header's ToS (Type of Service) field that mark the packet's
priority class. Routers and tc can read this to make decisions.

```
IP Header ToS Field (8 bits):
┌──────────────────────┬────────┐
│   DSCP (6 bits)      │  ECN   │
│   (priority marking) │(2 bits)│
└──────────────────────┴────────┘

Common DSCP Values:
  CS0 = 0  = Best effort (default)
  CS1 = 8  = Background (bulk transfers)
  AF11= 10 = Low priority assured forwarding
  CS4 = 32 = Video
  EF  = 46 = Expedited Forwarding (VoIP, video calls)
  CS6 = 48 = Network control
  CS7 = 56 = Reserved
```

### ECN (Explicit Congestion Notification)
2 bits in IP header. Routers signal congestion to endpoints WITHOUT dropping
packets. Modern TCP uses this to slow down proactively.

```
ECN Bits:
  00 = Not ECN-capable
  01 = ECN-capable transport (ECT(1))
  10 = ECN-capable transport (ECT(0))
  11 = Congestion Experienced (CE) — router set this!
```

### MTU (Maximum Transmission Unit)
Maximum packet size an interface can carry. Ethernet: 1500 bytes. If a packet
is larger, it gets fragmented.

### TSO / GSO / GRO (Offloading)
Hardware/software features that batch multiple packets together to reduce CPU
overhead. This interacts importantly with tc (discussed in internals section).

---

## 3. Where tc Lives in the Linux Network Stack

Understanding the exact position of tc in the kernel is critical.

### The Complete Linux Network Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER SPACE                                   │
│  Applications: curl, nginx, ssh, browser                        │
│        │                        ▲                               │
│        ▼                        │                               │
│   Socket API (send/recv)   Socket API                           │
└────────────────────────────────────────────────────────────────-┘
         │                        ▲
         ▼                        │
┌─────────────────────────────────────────────────────────────────┐
│                     KERNEL SPACE                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Socket Layer (VFS)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                        ▲                              │
│         ▼                        │                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Transport Layer (TCP / UDP / SCTP)           │   │
│  │  - TCP: connection, flow control, congestion control      │   │
│  │  - UDP: datagram, no connection                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                        ▲                              │
│         ▼                        │                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Network Layer (IP — IPv4 / IPv6)                │   │
│  │  - Routing decisions, TTL, fragmentation                  │   │
│  │  - Netfilter hooks (iptables/nftables live here)          │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                        ▲                              │
│         ▼                        │                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ◄══════════════  tc EGRESS  ═══════════════►            │   │
│  │         Traffic Control Layer                             │   │
│  │  - qdiscs, classes, filters, actions                     │   │
│  │  - Shaping, scheduling, policing                         │   │
│  │  ◄══════════════  tc INGRESS ═══════════════►            │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                        ▲                              │
│         ▼                        │                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Network Device Drivers (Data Link Layer)         │   │
│  │  - Ethernet, WiFi, PPP, TUN/TAP drivers                  │   │
│  │  - Hardware ring buffers (TX ring, RX ring)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                        ▲                              │
└─────────────────────────────────────────────────────────────────┘
          │                        │
          ▼                        │
┌─────────────────────────────────────────────────────────────────┐
│                    HARDWARE (NIC)                                 │
│  Physical wire: Ethernet frame transmission/reception            │
└─────────────────────────────────────────────────────────────────┘
```

### Egress Path — Detailed Flow

```
Application calls send()
        │
        ▼
┌───────────────────┐
│  Socket Buffer    │  (sk_buff allocated)
│  (sk_buff struct) │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  TCP Segmentation │  (packets created)
│  or UDP datagram  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  IP Routing       │  (which interface to use?)
│  Lookup           │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Netfilter        │  (iptables OUTPUT chain)
│  (optional)       │
└───────────────────┘
        │
        ▼
┌═══════════════════╗
║   tc EGRESS       ║  ◄── tc acts HERE on outbound packets
║   qdisc           ║
║   (enqueue)       ║
╚═══════════════════╝
        │
        ▼  (NET_TX_SOFTIRQ dequeues packets)
┌═══════════════════╗
║   tc EGRESS       ║  ◄── tc scheduler selects next packet
║   qdisc           ║
║   (dequeue)       ║
╚═══════════════════╝
        │
        ▼
┌───────────────────┐
│  Driver TX Ring   │  (packet handed to driver)
│  Buffer           │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  NIC DMA          │  (DMA to hardware)
│  Hardware TX      │
└───────────────────┘
        │
        ▼
      WIRE
```

### Ingress Path — Detailed Flow

```
      WIRE
        │
        ▼
┌───────────────────┐
│  NIC DMA          │  (packet arrives in RX ring)
│  Hardware RX      │
└───────────────────┘
        │
        ▼  (NET_RX_SOFTIRQ)
┌═══════════════════╗
║   tc INGRESS      ║  ◄── tc acts HERE on inbound packets
║   qdisc (ffff:)   ║       (policing only — no shaping!)
╚═══════════════════╝
        │
        ▼
┌───────────────────┐
│  Netfilter        │  (iptables PREROUTING chain)
│  (optional)       │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  IP Routing       │  (is this for me or forward?)
│  Decision         │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Socket Receive   │  (packet delivered to application)
│  Buffer           │
└───────────────────┘
        │
        ▼
Application calls recv()
```

### Key Insight: Why Ingress Shaping is Hard

```
PROBLEM:
  Traffic is ALREADY on the wire when it arrives.
  You cannot "slow it down" — it's already here!
  You can only:
    1. DROP excess packets (policing).
    2. Redirect to IFB (trick: re-enqueue as egress on virtual device).

SOLUTION (IFB — Intermediate Functional Block):

[External Traffic]
       │
       ▼ (arrives at eth0 ingress)
  ┌─────────────┐
  │ tc ingress  │──── redirect ────► [IFB device: ifb0]
  │ (eth0)      │                         │
  └─────────────┘                         ▼
                                    ┌──────────────┐
                                    │ tc EGRESS     │  ◄── Full shaping!
                                    │ qdisc on ifb0 │
                                    └──────────────┘
                                          │
                                          ▼
                                   Enters normal
                                   IP stack
```

---

## 4. The Three Pillars of tc

### Pillar 1: Queueing Disciplines (qdiscs)

A qdisc is an **algorithm** attached to a network interface that manages packet
queuing. It answers: "When a packet arrives, where does it go? When the driver
asks for the next packet, which one to send?"

```
QDISC TYPES:

Classless qdiscs:
  ├── pfifo         : Pure FIFO (first in, first out)
  ├── bfifo         : FIFO measured in bytes
  ├── pfifo_fast    : 3-band priority FIFO (kernel default)
  ├── sfq           : Stochastic Fair Queuing
  ├── tbf           : Token Bucket Filter (rate limiting)
  ├── fq            : Fair Queue
  ├── codel         : Controlled Delay
  ├── fq_codel      : Fair Queue + Controlled Delay
  ├── cake          : Common Applications Kept Enhanced
  └── netem         : Network Emulator (add delay/loss/reorder)

Classful qdiscs:
  ├── prio          : Priority scheduling (no rate control)
  ├── cbq           : Class-Based Queuing (legacy)
  ├── htb           : Hierarchical Token Bucket (most used)
  └── hfsc          : Hierarchical Fair Service Curve (advanced)
```

### Pillar 2: Classes

Classes subdivide traffic WITHIN a classful qdisc. Each class can have:
- Its own guaranteed and maximum bandwidth.
- Its own priority.
- Its own child qdisc.
- Sub-classes (nested hierarchy).

### Pillar 3: Filters

Filters classify packets into classes based on:
- IP address (source/destination).
- Port number.
- Protocol (TCP, UDP, ICMP).
- DSCP/TOS bits.
- Packet marks (fwmark from iptables).
- Arbitrary byte patterns.

```
FILTER TYPES:
  ├── u32       : Universal 32-bit filter (most powerful, matches any field)
  ├── flower    : Flower classifier (modern, efficient)
  ├── fw        : Firewall mark (reads iptables MARK)
  ├── route     : Based on routing table realm
  ├── basic     : Simple expression-based
  ├── bpf       : eBPF program as classifier (most flexible)
  ├── matchall  : Matches all packets
  └── cgroup    : Based on cgroup of originating process
```

---

## 5. Queueing Disciplines (qdiscs) — Deep Dive

### The qdisc Interface

Every qdisc implements exactly these operations:

```
QDISC OPERATIONS (Kernel Interface):

enqueue(packet, qdisc)
  → Called when packet arrives at this qdisc
  → Returns: NET_XMIT_SUCCESS or NET_XMIT_DROP
  → Can buffer, classify, or drop the packet

dequeue(qdisc) → packet
  → Called by driver when wire is ready for next packet
  → Returns: next packet to transmit, or NULL if nothing
  → This is where scheduling decisions happen

peek(qdisc) → packet
  → Like dequeue but does NOT remove the packet

drop(qdisc)
  → Force drop one packet (called under memory pressure)

reset(qdisc)
  → Flush all queued packets

destroy(qdisc)
  → Cleanup resources

dump(qdisc, skb)
  → Serialize qdisc statistics to Netlink message
```

### The sk_buff Structure — The Packet in Memory

Every packet is represented as an `sk_buff` (socket buffer) in the kernel:

```c
// Simplified sk_buff (actual struct has 200+ fields)
struct sk_buff {
    // Linked list pointers (for queue chains)
    struct sk_buff *next;
    struct sk_buff *prev;

    // Timing
    ktime_t tstamp;         // Arrival timestamp

    // Device
    struct net_device *dev; // Which interface

    // Data pointers
    unsigned char *head;    // Start of allocated buffer
    unsigned char *data;    // Start of packet data
    unsigned char *tail;    // End of packet data
    unsigned char *end;     // End of allocated buffer

    // Lengths
    unsigned int len;       // Total length
    unsigned int data_len;  // Data in frags

    // Classification
    __u32 mark;             // fwmark (set by iptables)
    __u8  tc_index;         // tc class index
    __u16 queue_mapping;    // TX queue

    // Headers (pointers into data buffer)
    // mac_header, network_header, transport_header

    // ... 200+ more fields
};
```

### Queue Length and Txqueuelen

Every interface has a **txqueuelen** — the maximum number of packets the
kernel's default qdisc can hold.

```
Default: 1000 packets (for most interfaces)

Check with:
  ip link show eth0
  → ... qlen 1000

Change with:
  ip link set eth0 txqueuelen 10000

This is the size of the ROOT qdisc's queue.
Custom qdiscs have their own configurable limits.
```

---

## 6. Classless qdiscs

Classless qdiscs treat all traffic as one stream. No classification into sub-
classes. Simple but powerful.

### 6.1 pfifo — Pure FIFO

The simplest possible queue. First packet in = first packet out.

```
PFIFO:

Incoming packets:   [P7][P6][P5][P4][P3][P2][P1]
                                                 ↑ enqueue here
                                          (P1 was first)

Dequeue:           [P7][P6][P5][P4][P3][P2]    ──► [P1] to wire
                                          ↑          (P1 leaves first)
                                      front

Limit: txqueuelen packets (default 1000)

PROBLEM: Head-of-line blocking.
  A large burst of traffic fills the queue.
  Small real-time packets wait behind bulk traffic.
  No priority differentiation.
```

Command:
```bash
tc qdisc add dev eth0 root pfifo limit 1000
```

### 6.2 bfifo — Byte FIFO

Same as pfifo but limit is in bytes (not packets). Better for rate limiting
across mixed packet sizes.

```bash
tc qdisc add dev eth0 root bfifo limit 100000
# Limit: 100,000 bytes = ~100KB
```

### 6.3 pfifo_fast — The Kernel Default

The default qdisc on every Linux interface. Uses 3 priority bands.

```
PFIFO_FAST STRUCTURE:

Band 0 (Highest Priority):  [  ][ ][ ][ ][ ][ ][ ]
Band 1 (Normal Priority):   [  ][ ][ ][ ][ ][ ][ ]
Band 2 (Lowest Priority):   [  ][ ][ ][ ][ ][ ][ ]
                              ↑
                           Dequeue: Band 0 first.
                           Only when Band 0 is EMPTY,
                           dequeue from Band 1.
                           Only when Band 1 is EMPTY,
                           dequeue from Band 2.

Packet → band mapping is done via TOS field in IP header:

TOS Field (4 bits used):
  Bits: PPPDTRXX
         |||||||
         |||||||→ Reserved
         ||||||→ Reserved
         |||||→ Low Cost (Throughput)
         ||||→ Reliability
         |||→ Throughput (maximize)
         ||→ Delay (minimize)
         |→ Precedence bits

TOS to Band mapping:
  TOS 0x00 (Normal)             → Band 1
  TOS 0x02 (Minimize Cost)      → Band 1
  TOS 0x04 (Maximize Reliability)→ Band 1
  TOS 0x06                      → Band 1
  TOS 0x08 (Maximize Throughput)→ Band 2  (bulk!)
  TOS 0x0a                      → Band 2
  TOS 0x0c                      → Band 2
  TOS 0x0e                      → Band 2
  TOS 0x10 (Minimize Delay)     → Band 0  (interactive!)
  TOS 0x12                      → Band 0
  ...  (0x10-0x1e all → Band 0)
```

This is why SSH (which sets Minimize Delay) feels responsive even during heavy
downloads — it goes to Band 0.

### 6.4 SFQ — Stochastic Fair Queuing

SFQ solves the problem of one flow dominating the queue. It creates **virtual
queues per flow** and round-robins between them.

**Key concepts:**
- **Flow**: A packet stream identified by (src IP, dst IP, src port, dst port,
  protocol). This is a 5-tuple.
- **Hashing**: Flows are mapped to buckets using a hash function.
- **Stochastic**: Hash function changes periodically (every `perturb` seconds)
  to prevent a bad actor from always mapping to the same bucket.

```
SFQ OPERATION:

Flows:
  Flow A (SSH):   [A1][A2][A3]
  Flow B (HTTP):  [B1][B2]
  Flow C (Bulk):  [C1][C2][C3][C4][C5][C6]

SFQ assigns each flow a bucket via hash:
  Flow A → Bucket 3
  Flow B → Bucket 7
  Flow C → Bucket 1

Round-Robin dequeue:
  Bucket 1: [C1] ──► wire
  Bucket 3: [A1] ──► wire
  Bucket 7: [B1] ──► wire
  Bucket 1: [C2] ──► wire
  Bucket 3: [A2] ──► wire
  Bucket 7: [B2] ──► wire
  Bucket 1: [C3] ──► wire
  Bucket 3: [A3] ──► wire
  Bucket 7: (empty, skip)
  Bucket 1: [C4] ──► wire
  ...

Result: Flow C gets at most 1/3 of bandwidth,
        even though it has 6 packets queued!
        A and B are never starved.
```

```
HASH COLLISION PROBLEM:

  Two flows might hash to the same bucket → unfair!
  SFQ adds "perturb" parameter — changes hash function every N seconds.
  This makes it stochastic (probabilistically fair) rather than guaranteed fair.

  perturb=10 means hash changes every 10 seconds.
  Best practice: always set perturb.
```

```bash
tc qdisc add dev eth0 root sfq perturb 10
# perturb: change hash every 10 seconds
# limit: 127 packets per bucket (default)
# quantum: 1 MTU (bytes dequeued per round-robin turn)
```

Advanced SFQ (kernel 3.3+):
```bash
tc qdisc add dev eth0 root sfq \
    perturb 10  \
    limit 10000 \     # total packet limit
    quantum 1514 \    # bytes per round-robin
    divisor 1024 \    # number of hash buckets
    qavg 50ms \       # EWMA for RED (see below)
    qlow 2000 \       # RED low threshold
    qhigh 6000 \      # RED high threshold
    probability 0.20  # RED drop probability
```

### 6.5 TBF — Token Bucket Filter

TBF is the primary tool for **rate limiting** (shaping). It implements the
Token Bucket Algorithm (explained in depth in Section 11).

```
TBF PARAMETERS:
  rate    : Average rate to allow (e.g., 1mbit)
  burst   : Maximum burst size in bytes
  latency : Maximum time a packet can wait in the queue
  limit   : Maximum bytes in the queue (alternative to latency)
  peakrate: Maximum instantaneous rate (limits burst speed)
  mtu     : Minimum burst (typically MTU size)

TBF STRUCTURE:

        Tokens arrive at rate R (rate parameter)
                    │
                    ▼
    ┌───────────────────────────────┐
    │        Token Bucket           │
    │  ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○   │  ← Max tokens = burst
    │  (each token = 1 byte)        │
    └───────────────────────────────┘
                    │
                    │  Packet arrives
                    ▼
         Does bucket have enough tokens?
                    │
            YES ────┴──── NO
             │                │
             ▼                ▼
    Remove tokens &      Wait in queue or
    transmit packet      drop if queue full
```

```bash
# Limit eth0 to 1 Mbit/s
tc qdisc add dev eth0 root tbf \
    rate 1mbit \
    burst 32kbit \   # allow 32KB burst
    latency 50ms     # max 50ms in queue
```

### 6.6 fq — Fair Queue (for servers)

Designed by Eric Dumazet specifically for servers. Provides per-socket fair
queuing with pacing.

**Key feature**: TCP pacing — spreads packet transmission evenly within a
congestion window instead of bursting.

```
WITHOUT TCP PACING:
  TCP gets a window of 10 packets to send.
  Sends all 10 immediately → BURST → queue spike → latency spike.

WITH fq PACING:
  fq knows the flow's rate (from TCP socket).
  Spreads 10 packets evenly over RTT.
  Wire utilization is smooth. Latency is stable.

  Time:  |──|──|──|──|──|──|──|──|──|──|
  Pkts:   P1 P2 P3 P4 P5 P6 P7 P8 P9 P10
  (evenly spaced, not burst)
```

```bash
tc qdisc add dev eth0 root fq \
    limit 10000 \        # max packets in queue
    flow_limit 100 \     # max packets per flow
    quantum 3028 \       # bytes per round-robin turn
    initial_quantum 15140 \ # first round gets more (slow start)
    maxrate 0 \          # no global rate limit
    buckets 1024         # hash buckets
```

### 6.7 CoDel — Controlled Delay

CoDel (pronounced "coddle") solves **bufferbloat** — the plague of modern
networking.

**What is bufferbloat?**

```
BUFFERBLOAT PROBLEM:

Modern hardware has huge buffers (1MB, 16MB, even 256MB).
TCP fills these buffers completely.
Result: Packets sit in buffer for SECONDS.

Example:
  10 Mbps link, 256MB buffer
  Buffer drains at 10Mbps = ~200 seconds to drain!
  Packet at back of buffer: 200 second latency.
  Ping goes from 5ms to 5000ms under load.
  This is bufferbloat.

CODEL INSIGHT:
  We don't care about queue LENGTH.
  We care about SOJOURN TIME (how long a packet stays in queue).
  
  Target: packets should spend < 5ms in queue (target = 5ms default).
  If packets consistently exceed this target → we have a problem.
  Solution: drop packets to signal congestion to TCP.
```

```
CODEL STATE MACHINE:

                      START
                        │
              ┌─────────▼──────────┐
              │   Measure sojourn  │
              │   time of each     │
              │   dequeued packet  │
              └─────────┬──────────┘
                        │
               sojourn < target (5ms)?
                  │              │
                 YES             NO
                  │              │
           ┌──────▼──────┐  ┌───▼──────────────────┐
           │ Reset state  │  │ Has it been > interval│
           │ (everything  │  │ (100ms) of sustained  │
           │  is fine)    │  │ high sojourn?         │
           └─────────────┘  └───────┬───────────────┘
                                    │
                              NO ───┴─── YES
                               │              │
                         ┌─────▼────┐  ┌─────▼──────────────┐
                         │Wait and  │  │ DROP packet (or ECN │
                         │keep      │  │ mark) and increase  │
                         │measuring │  │ drop frequency      │
                         └──────────┘  └────────────────────-┘

Drop frequency: proportional to √(number of drops)
  → 1st drop, wait 100ms
  → 2nd drop, wait 100ms/√2 = 70ms
  → 3rd drop, wait 100ms/√3 = 57ms
  → ...
  Drops accelerate if problem persists.
```

```bash
tc qdisc add dev eth0 root codel \
    limit 1000 \      # max packets in queue
    target 5ms \      # target sojourn time
    interval 100ms \  # interval for drop state check
    ecn               # use ECN instead of drop (if supported)
```

### 6.8 FQ-CoDel — Fair Queue + CoDel

The **modern recommended default** qdisc. Combines SFQ's per-flow fairness
with CoDel's bufferbloat control.

```
FQ-CODEL STRUCTURE:

Incoming packets
       │
       ▼
  Hash to flow bucket
       │
       ▼
┌──────────────────────────────────────────────────────┐
│                   Flow Buckets                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Flow A   │  │ Flow B   │  │ Flow C   │    ...     │
│  │ CoDel    │  │ CoDel    │  │ CoDel    │           │
│  │ queue    │  │ queue    │  │ queue    │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │             │                  │
└───────┼─────────────┼─────────────┼──────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
              Round-robin scheduler
              (with DRR — Deficit Round Robin)
                      │
                      ▼
                   To wire

Each flow's queue is managed by CoDel independently.
→ Per-flow fair queuing (like SFQ)
→ Per-flow bufferbloat control (like CoDel)
= Best of both worlds
```

```
FQ-CODEL also has TWO queues per flow:
  1. "new flow" queue: freshly started flows (get priority)
  2. "old flow" queue: ongoing flows

New flows get priority → interactive sessions start fast!
Old flows are round-robined → bulk doesn't starve interactive.
```

```bash
tc qdisc add dev eth0 root fq_codel \
    limit 10240 \     # total packet limit
    flows 1024 \      # number of flow buckets
    quantum 1514 \    # bytes per round-robin
    target 5ms \      # CoDel target sojourn
    interval 100ms \  # CoDel interval
    ecn               # ECN marking instead of drop
```

### 6.9 CAKE — Common Applications Kept Enhanced

CAKE is the most sophisticated classless qdisc (2018+). It builds on
FQ-CoDel and adds:
- Automatic flow classification (3 flows types: host, flow, dst-host).
- Built-in NAT awareness.
- 8 traffic priorities via DSCP.
- Overhead compensation (PPPoE, VLAN, ATM, etc.).
- Split GSO (de-offloading for accurate shaping).

Covered in detail in Section 15.

```bash
tc qdisc add dev eth0 root cake \
    bandwidth 100mbit \
    besteffort            # single priority tier
```

### 6.10 netem — Network Emulator

Used for **testing** — simulates bad network conditions.

```bash
# Add 100ms delay to all packets
tc qdisc add dev eth0 root netem delay 100ms

# Add delay with jitter (variation)
tc qdisc add dev eth0 root netem delay 100ms 10ms

# Add delay with jitter following normal distribution
tc qdisc add dev eth0 root netem delay 100ms 10ms distribution normal

# Add packet loss (1%)
tc qdisc add dev eth0 root netem loss 1%

# Add packet corruption (0.1%)
tc qdisc add dev eth0 root netem corrupt 0.1%

# Add packet reordering
tc qdisc add dev eth0 root netem delay 10ms reorder 25% 50%

# Add packet duplication
tc qdisc add dev eth0 root netem duplicate 1%

# Combine: WAN simulation
tc qdisc add dev eth0 root netem \
    delay 50ms 10ms distribution normal \
    loss 0.1% \
    corrupt 0.01% \
    limit 1000
```

---

## 7. Classful qdiscs

Classful qdiscs divide traffic into **classes**. Each class can have its own
bandwidth guarantee, priority, and child qdisc. This is where complex QoS
policies are implemented.

### 7.1 The Class Tree Structure

```
CLASSFUL QDISC TREE (Example):

                  root qdisc (1:0)
                       │
             ┌─────────┴──────────┐
             │                    │
         Class 1:1            Class 1:2
         (VoIP Traffic)       (Data Traffic)
         rate: 500kbit         rate: 9.5mbit
             │                    │
       ┌─────┘             ┌──────┴──────┐
       │                   │             │
   Class 1:10          Class 1:20   Class 1:30
   (SIP signaling)    (HTTP/HTTPS)  (Bulk/FTP)
   rate: 100kbit       rate: 7mbit   rate: 2.5mbit
       │                   │             │
   [sfq qdisc]         [sfq qdisc]  [sfq qdisc]
   (fair within)       (fair within) (fair within)

Each leaf class has a qdisc (sfq for fairness within that class).
Inner nodes are just HTB classes with bandwidth allocation.
```

### 7.2 PRIO — Priority Queue

PRIO divides traffic into N bands (default 3) with strict priority. No rate
limiting — just ordering.

```
PRIO STRUCTURE:

                 root: prio (1:0)
                 [3 bands]
                       │
         ┌─────────────┼─────────────┐
         │             │             │
     Class 1:1     Class 1:2     Class 1:3
     (Band 0)      (Band 1)      (Band 2)
     HIGHEST       MEDIUM        LOWEST
     PRIORITY      PRIORITY      PRIORITY
         │             │             │
     [sfq]          [sfq]          [sfq]

Dequeue: 1:1 is always drained before 1:2 or 1:3!
Warning: Low priority bands can be STARVED completely
         if high priority band is always full.
```

```bash
# Create PRIO with 3 bands
tc qdisc add dev eth0 root handle 1: prio bands 3 \
    priomap 1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1

# priomap: maps TOS bits (0-15) to bands (0-2)
# Position i → TOS value i → band number

# Add sfq to each band
tc qdisc add dev eth0 parent 1:1 handle 10: sfq perturb 10
tc qdisc add dev eth0 parent 1:2 handle 20: sfq perturb 10
tc qdisc add dev eth0 parent 1:3 handle 30: sfq perturb 10

# Add filters to classify traffic
tc filter add dev eth0 parent 1:0 protocol ip prio 1 \
    u32 match ip dport 22 0xffff flowid 1:1   # SSH → Band 0

tc filter add dev eth0 parent 1:0 protocol ip prio 2 \
    u32 match ip dport 80 0xffff flowid 1:2   # HTTP → Band 1
```

### 7.3 CBQ — Class-Based Queuing (Legacy)

CBQ was the original classful qdisc (1990s). It's complex and has been
superseded by HTB. Understanding it builds historical context.

```
CBQ CONCEPTS:

  Borrowing: A class can "borrow" bandwidth from its parent
             if the parent is not using it.

  Isolation: A class can be marked "isolated" — it won't borrow.
             And "bounded" — its children won't lend to others.

  Problem: CBQ uses link-sharing curves that are mathematically
           complex and behave unexpectedly at low bandwidths.
           HTB replaced it with cleaner token bucket semantics.

AVOID CBQ in new configurations. Use HTB instead.
```

### 7.4 HTB — Hierarchical Token Bucket

HTB is the workhorse of Linux QoS. Section 12 covers it in complete depth.

### 7.5 HFSC — Hierarchical Fair Service Curve

HFSC provides **service curves** — mathematical descriptions of bandwidth
over time, not just rates. Section 13 covers it.

---

## 8. Filters and Classifiers

Filters are the "traffic police" that inspect each packet and direct it to
the correct class. Without filters, all packets go to the default class.

### Filter Processing Order

```
Packet arrives at classful qdisc
              │
              ▼
    Apply filter priority 1 (lowest number = highest priority)
              │
    Match found? ──YES──► Send to class specified by filter
              │
             NO
              │
    Apply filter priority 2
              │
    Match found? ──YES──► Send to class
              │
             NO
              │
    ... (continue through all priorities)
              │
    No filter matched → Default class
              │
              ▼
    Enqueue into class's qdisc
```

### 8.1 u32 Filter — Universal 32-bit Matcher

The most powerful and flexible filter. Can match ANY field in the IP header,
TCP/UDP header, or payload.

**Understanding u32:**

u32 matches 4-byte (32-bit) chunks at specific byte offsets in the packet.
Then applies a bitmask to select specific bits.

```
u32 match syntax:
  u32 match SELECTOR VALUE MASK

SELECTOR:
  ip src 1.2.3.4/32    → match source IP
  ip dst 1.2.3.4/32    → match destination IP
  ip dport 80 0xffff   → match destination port 80
  ip sport 1024 0xfc00 → match source ports 1024-1027
  ip protocol 6 0xff   → match TCP (protocol 6)
  ip tos 0x10 0xff     → match TOS byte
  u8 at 0 0x0f         → match 4 low bits at byte 0
  u16 at 2 0xffff      → match 2 bytes at offset 2
  u32 at 4 0xffffffff  → match 4 bytes at offset 4
```

```
PACKET STRUCTURE AT BYTE LEVEL (IPv4 + TCP):

Byte:  0   1   2   3   4   5   6   7   8   9   10  11
      ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
      │VHL│TOS│ Total Length  │Ident  │FlagFrag│TTL│Pro│ ...
      └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

Byte: 12  13  14  15  16  17  18  19  20  21  22  23
      ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
      │  Source IP        │  Destination IP            │ ...
      └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

(After 20 bytes IP header, TCP header begins)
Byte: 20  21  22  23  24  25  26  27 ...
      ┌───┬───┬───┬───┬───┬───┬───┬───┐
      │ Src Port  │ Dst Port  │ Seq # │ ...
      └───┴───┴───┴───┴───┴───┴───┴───┘

u32 match ip dport 80 0xffff:
  → offset 20 (after IP hdr) + 2 (past src port) = offset 22
  → match 2 bytes (0xffff mask = match exactly)
  → value must be 80 (0x0050)
```

```bash
# Match packets to 192.168.1.5
tc filter add dev eth0 parent 1:0 protocol ip prio 1 \
    u32 match ip dst 192.168.1.5/32 flowid 1:1

# Match TCP port 443 (HTTPS)
tc filter add dev eth0 parent 1:0 protocol ip prio 2 \
    u32 match ip protocol 6 0xff \
    match ip dport 443 0xffff \
    flowid 1:2

# Match UDP port 5060 (SIP/VoIP)
tc filter add dev eth0 parent 1:0 protocol ip prio 3 \
    u32 match ip protocol 17 0xff \
    match ip dport 5060 0xffff \
    flowid 1:3

# Match by TOS (Minimize-Delay flag)
tc filter add dev eth0 parent 1:0 protocol ip prio 4 \
    u32 match ip tos 0x10 0xff \
    flowid 1:1
```

### 8.2 fw Filter — Firewall Mark

Uses iptables MARK to classify packets. Flexible because iptables has many
matchers.

```
WORKFLOW:

1. iptables marks packets:
   iptables -t mangle -A OUTPUT -p tcp --dport 22 -j MARK --set-mark 1
   iptables -t mangle -A OUTPUT -p tcp --dport 80 -j MARK --set-mark 2

2. tc filter reads the mark:
   tc filter add dev eth0 parent 1:0 prio 1 handle 1 fw flowid 1:1
   tc filter add dev eth0 parent 1:0 prio 2 handle 2 fw flowid 1:2

ADVANTAGE: iptables can match many things tc cannot:
  - Connection state (NEW, ESTABLISHED, RELATED)
  - User/group (UID/GID via owner match)
  - Conntrack marks
  - String matches in payload
  - Time-based matches
```

### 8.3 flower Filter — Modern Efficient Classifier

Flower classifies based on L2-L4 fields. More readable than u32 and can be
offloaded to hardware.

```bash
# Match by source MAC
tc filter add dev eth0 parent 1:0 protocol ip prio 1 \
    flower \
    src_mac 00:11:22:33:44:55 \
    flowid 1:1

# Match by IP and port
tc filter add dev eth0 parent 1:0 protocol ip prio 2 \
    flower \
    dst_ip 10.0.0.1/24 \
    ip_proto tcp \
    dst_port 443 \
    flowid 1:2

# Match VLAN-tagged traffic
tc filter add dev eth0 parent 1:0 protocol 802.1Q prio 3 \
    flower \
    vlan_id 100 \
    ip_proto tcp \
    flowid 1:3

# Match DSCP (EF = 46, shifted left by 2 = 0xb8 in TOS byte)
tc filter add dev eth0 parent 1:0 protocol ip prio 4 \
    flower \
    ip_flags nofrag \
    dst_ip 0.0.0.0/0 \
    ip_tos 0xb8/0xfc \   # DSCP EF = 46 << 2 = 184 = 0xb8
    flowid 1:1
```

### 8.4 BPF Filter — eBPF as Classifier

Most powerful option. Write arbitrary packet classification logic in C,
compile to eBPF bytecode, attach as filter.

```c
// classifier.c (eBPF program)
#include <linux/bpf.h>
#include <linux/pkt_cls.h>

SEC("classifier")
int classify(struct __sk_buff *skb) {
    // skb has full packet access
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return TC_ACT_OK;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return TC_ACT_OK;

    // Classify TCP port 22 to high priority
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)(ip + 1);
        if ((void *)(tcp + 1) > data_end) return TC_ACT_OK;
        if (ntohs(tcp->dest) == 22) {
            skb->tc_classid = TC_H_MAKE(1, 1); // class 1:1
        }
    }
    return TC_ACT_OK;
}
```

```bash
# Compile and attach
clang -O2 -target bpf -c classifier.c -o classifier.o
tc filter add dev eth0 parent 1:0 bpf obj classifier.o sec classifier
```

### 8.5 Filter Actions

Filters can do more than just classify. They can take **actions**:

```
FILTER ACTIONS:

  reclassify  : Try next filter in chain
  ok / pass   : Accept packet, use classification
  drop        : Drop packet immediately
  continue    : Skip this filter, try next
  pipe        : Pass to next action

REDIRECT ACTION:
  Send packet to DIFFERENT interface:
  tc filter add dev eth0 ingress ... action mirred egress \
      redirect dev ifb0

MIRROR ACTION:
  Copy packet to another interface (tap):
  tc filter add dev eth0 ingress ... action mirred egress \
      mirror dev eth1

MARK ACTION:
  Set fwmark on packet:
  tc filter add dev eth0 parent 1: ... action skbedit mark 42

POLICE ACTION (inline rate limiting):
  tc filter add dev eth0 parent 1: ... \
      police rate 1mbit burst 10k \
      action drop  # drop if over rate
```

---

## 9. Actions (tc Actions Framework)

Actions are standalone operations that can be chained to filters. The tc
actions framework (LKML: Jamal Hadi Salim, 2004) made actions first-class
objects.

### Available Actions

```
ACTION CATALOG:

gact    : Generic action (drop, pass, reclassify)
mirred  : Mirror/redirect to another interface
nat     : Source/destination NAT
pedit   : Packet editing (modify header fields)
police  : Rate policing
skbedit : Edit sk_buff metadata (mark, priority, queue_mapping)
vlan    : VLAN push/pop/modify
tunnel_key: Manage tunnel metadata
connmark: Copy conntrack mark to/from fwmark
csum    : Recalculate checksums after pedit
bpf     : Execute eBPF program as action
gate    : Time-based gate (IEEE 802.1Qbv)
mpls    : Push/pop MPLS labels
```

### pedit Action — Packet Surgery

```bash
# Change destination IP of packets matching filter
tc filter add dev eth0 parent 1: prio 1 u32 \
    match ip dst 10.0.0.1/32 \
    action pedit \
        munge ip dst set 10.0.0.2 \  # change dst IP
    action csum all                  # fix checksum

# Change DSCP to EF (Expedited Forwarding)
tc filter add dev eth0 parent 1: prio 1 u32 \
    match ip protocol 17 0xff \  # UDP
    action pedit \
        munge ip tos set 0xb8    # DSCP EF = 46 << 2 = 0xb8
```

### Police Action

```bash
# Drop packets exceeding 1Mbit/s, conforming traffic passes
tc filter add dev eth0 parent 1: prio 1 u32 \
    match ip src 10.0.0.1/32 \
    police rate 1mbit burst 100k \
    action drop  # drop non-conforming
    # conforming packets → ok (continue)
```

---

## 10. Policing vs Shaping — The Core Distinction

This is one of the most important distinctions in traffic control.

```
SHAPING:                        POLICING:
                                
Packets arrive too fast →        Packets arrive too fast →
Buffer them (queue them) →       DROP them immediately
Release at controlled rate       
                                
TIMELINE:                        TIMELINE:
                                
Rate limit: 1 Mbit/s             Rate limit: 1 Mbit/s
                                
Burst:       ████████            Burst:       ████████
Limit:       ────────            Limit:       ────────
After shape: ── ── ──            After police:  (dropped)
                                
Sender:      OK, TCP            Sender:        DROPS!
             will see           TCP gets       TCP sees loss
             smooth rate        no signal       → retransmit
             and not            except loss     → congestion
             retransmit                         reaction

WHEN TO USE SHAPING:            WHEN TO USE POLICING:
  - Egress traffic              - Ingress traffic (can't buffer)
  - When you own the sender     - When you DON'T own sender
  - Video encoding pipelines    - ISP edge enforcement
  - Avoiding ISP throttling     - DDoS mitigation
  - Smoothing bursty traffic    - SLA enforcement
```

### The Buffer Dilemma

```
SHAPING ADDS DELAY!

If you shape a 100 Mbps link to 1 Mbps:
  Queue can hold N packets.
  Each packet: 1500 bytes = 12,000 bits.
  At 1 Mbps: each packet takes 12ms to transmit.
  
  With 100 packets queued:
    Last packet waits: 100 × 12ms = 1200ms = 1.2 seconds!
  
  This is intentional delay (latency penalty for shaping).

SOLUTION: Keep queues SHORT when shaping.
  Use small burst sizes.
  Use CoDel/FQ-CoDel at leaf qdiscs.
  Monitor queue depth.
```

---

## 11. Token Bucket Algorithm — The Mathematical Heart

The Token Bucket is the foundation of TBF, HTB, HFSC, and most rate limiting.

### The Algorithm

```
TOKEN BUCKET:

State:
  tokens : current tokens in bucket (bytes)
  burst  : maximum tokens (bucket capacity)
  rate   : token generation rate (bytes/sec)
  last_t : last time tokens were added

On packet arrival (size S bytes, time T):

  1. Add tokens: tokens += (T - last_t) × rate
  2. Cap at burst: tokens = min(tokens, burst)
  3. Update time: last_t = T
  4. Can we send?
       if tokens >= S:
           tokens -= S
           TRANSMIT packet
       else:
           WAIT (shaping) or DROP (policing)
```

```
TOKEN BUCKET VISUALIZATION:

Rate: 1 Mbit/s = 125,000 bytes/sec
Burst: 10,000 bytes
Initial: full bucket (10,000 tokens)

t=0ms:    Bucket [■■■■■■■■■■] 10000 tokens
          Packet arrives (3000 bytes)
          3000 ≤ 10000 → SEND
          Bucket [■■■■■■■] 7000 tokens

t=1ms:    +125 tokens added (1ms × 125000 bytes/s)
          Bucket [■■■■■■■] 7125 tokens
          Packet arrives (3000 bytes)
          3000 ≤ 7125 → SEND
          Bucket [■■■■] 4125 tokens

t=2ms:    +125 tokens
          Bucket [■■■■] 4250 tokens
          Packet arrives (5000 bytes)
          5000 > 4250 → WAIT (shaping) or DROP (policing)

          Tokens needed: 5000 - 4250 = 750 more tokens
          At 125 bytes/ms: wait 750/125 = 6ms

t=8ms:    +125×6 = 750 tokens added
          Bucket [■■■■■] 5000 tokens
          5000 ≥ 5000 → SEND
          Bucket [] 0 tokens

t=9ms:    +125 tokens
          Bucket [.] 125 tokens

This implements SHAPING. Packets are delayed, not dropped.
```

### Dual Token Bucket (TBF with peakrate)

TBF supports a second bucket for burst limiting:

```
DUAL BUCKET:

               [MAIN BUCKET]         [PEAK BUCKET]
               rate: 1 Mbit/s        peakrate: 2 Mbit/s
               burst: 32KB           mtu: 1500 bytes

Packet must pass BOTH buckets:
  Main bucket: controls average rate
  Peak bucket: controls burst speed

Without peakrate:
  Burst of 32KB transmitted at WIRE SPEED (100 Mbps?)
  Then silence until tokens accumulate
  → Very spiky delivery

With peakrate=2Mbit:
  Burst transmitted at max 2 Mbit/s
  → Smoother burst delivery
  
FORMULAS:
  Time to transmit burst at peakrate:
    32KB / 2Mbit/s = 32768 bytes / 250000 bytes/s = 131ms

  Latency (max queueing delay):
    latency = burst / rate = 32768 / 125000 = ~262ms
```

---

## 12. HTB — Hierarchical Token Bucket (Master Class)

HTB is the most commonly used classful qdisc. It implements a token bucket
hierarchy where classes can borrow unused bandwidth from each other.

### HTB Concepts

**Key Terms:**
- **rate**: Guaranteed minimum bandwidth for this class.
- **ceil**: Maximum bandwidth this class can use (including borrowed).
- **burst**: Bytes of burst before rate is enforced.
- **cburst**: Burst above ceil (should be small or zero).
- **prio**: Priority when multiple classes want to borrow (lower = higher
  priority).
- **quantum**: How much can be sent in one round-robin turn when borrowing.

### HTB Borrowing Algorithm

```
HTB BORROWING RULES:

Scenario: 3 classes sharing 10 Mbit uplink.

        root: htb (1:0)
        rate: 10mbit ceil: 10mbit
               │
    ┌──────────┼──────────┐
    │          │          │
 Class 1:1  Class 1:2  Class 1:3
 VoIP       HTTP       Bulk
 rate: 1m   rate: 5m   rate: 2m
 ceil: 10m  ceil: 10m  ceil: 10m
             
CASE 1: All classes are active
  Each gets AT LEAST its rate:
  VoIP: 1m, HTTP: 5m, Bulk: 2m = 8m total
  Remaining 2m is distributed by priority.

CASE 2: Bulk class is idle
  Its 2m allocation is available.
  VoIP can borrow up to its ceil (10m).
  HTTP can borrow up to its ceil (10m).
  Distribution via priority (prio field).

CASE 3: Only HTTP is active
  HTTP gets up to 10m (its ceil).
  
HTB STATE MACHINE (per class):

         ┌──────────────────────────────────┐
         │                                  │
         ▼                                  │
    CAN_SEND ──► (send packet) ──► check if still CAN_SEND
         │              │
         │       sent too much?
         │              │
         │             YES
         │              │
         ▼              ▼
    CANT_SEND ──────────────────────► MAY_BORROW
    (no tokens,         (tokens from parent avail?)
     can't borrow)              │
                               YES
                                │
                                ▼
                          BORROW from parent
                          (parent may borrow from ITS parent)
```

### Complete HTB Configuration Example

```bash
# ═══════════════════════════════════════════════
# SCENARIO: Home router, 10 Mbit uplink
# Classes:
#   1:10 VoIP/RTP      - 1mbit guaranteed, 10mbit ceiling
#   1:20 Interactive   - 3mbit guaranteed, 10mbit ceiling
#   1:30 Bulk Transfer - 6mbit guaranteed, 10mbit ceiling
# ═══════════════════════════════════════════════

# Step 1: Remove existing qdisc
tc qdisc del dev eth0 root 2>/dev/null

# Step 2: Create root HTB qdisc
# default 30: unclassified packets → class 1:30 (bulk)
tc qdisc add dev eth0 root handle 1: htb default 30

# Step 3: Create root class (total bandwidth)
tc class add dev eth0 parent 1: classid 1:1 htb \
    rate 10mbit \
    burst 15k

# Step 4: Create leaf classes
tc class add dev eth0 parent 1:1 classid 1:10 htb \
    rate 1mbit \
    ceil 10mbit \
    burst 15k \
    prio 0           # Highest priority

tc class add dev eth0 parent 1:1 classid 1:20 htb \
    rate 3mbit \
    ceil 10mbit \
    burst 15k \
    prio 1           # Medium priority

tc class add dev eth0 parent 1:1 classid 1:30 htb \
    rate 6mbit \
    ceil 10mbit \
    burst 15k \
    prio 2           # Lowest priority

# Step 5: Attach leaf qdiscs for fairness within each class
tc qdisc add dev eth0 parent 1:10 handle 10: sfq perturb 10
tc qdisc add dev eth0 parent 1:20 handle 20: sfq perturb 10
tc qdisc add dev eth0 parent 1:30 handle 30: sfq perturb 10

# Step 6: Add filters to classify traffic

# VoIP (SIP port 5060, RTP ports 10000-20000)
tc filter add dev eth0 parent 1:0 protocol ip prio 1 u32 \
    match ip protocol 17 0xff \
    match ip dport 5060 0xffff \
    flowid 1:10

tc filter add dev eth0 parent 1:0 protocol ip prio 2 u32 \
    match ip protocol 17 0xff \
    match ip dport 10000 0xe000 \  # 10000-12000 range
    flowid 1:10

# DSCP EF (Expedited Forwarding) → VoIP
tc filter add dev eth0 parent 1:0 protocol ip prio 3 u32 \
    match ip tos 0xb8 0xfc \       # DSCP EF
    flowid 1:10

# Interactive (SSH, DNS, HTTP, HTTPS, small ACKs)
tc filter add dev eth0 parent 1:0 protocol ip prio 10 u32 \
    match ip protocol 6 0xff \
    match ip dport 22 0xffff \
    flowid 1:20

tc filter add dev eth0 parent 1:0 protocol ip prio 11 u32 \
    match ip protocol 17 0xff \
    match ip dport 53 0xffff \
    flowid 1:20

tc filter add dev eth0 parent 1:0 protocol ip prio 12 u32 \
    match ip protocol 6 0xff \
    match ip dport 80 0xffff \
    flowid 1:20

tc filter add dev eth0 parent 1:0 protocol ip prio 13 u32 \
    match ip protocol 6 0xff \
    match ip dport 443 0xffff \
    flowid 1:20

# Everything else → Bulk (default class 1:30, no filter needed)
```

### HTB Tree Visualization

```
                    [WAN Interface: eth0]
                           │
                    ┌──────▼──────┐
                    │  htb 1:0    │ Root qdisc
                    │  handle 1:  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  class 1:1  │ Root class
                    │  rate 10m   │ (total bandwidth)
                    │  ceil 10m   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────▼──────┐  ┌───────▼─────┐  ┌───────▼─────┐
  │ class 1:10  │  │ class 1:20  │  │ class 1:30  │
  │ VoIP        │  │ Interactive │  │ Bulk        │
  │ rate: 1m    │  │ rate: 3m    │  │ rate: 6m    │
  │ ceil: 10m   │  │ ceil: 10m   │  │ ceil: 10m   │
  │ prio: 0     │  │ prio: 1     │  │ prio: 2     │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │                │                 │
  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
  │ sfq 10:     │  │ sfq 20:     │  │ sfq 30:     │
  │ (fair queue │  │ (fair queue │  │ (fair queue │
  │  within)    │  │  within)    │  │  within)    │
  └─────────────┘  └─────────────┘  └─────────────┘

Filters (applied at 1:0):
  → RTP/SIP → 1:10
  → DSCP EF → 1:10
  → SSH/DNS/HTTP → 1:20
  → Everything else → 1:30 (default)
```

### HTB Quantum Calculation

```
QUANTUM: bytes sent in one round-robin turn when borrowing.

HTB auto-calculates quantum from rate:
  quantum = rate / r2q

Default r2q = 10.
  rate = 1mbit = 125000 bytes/s
  quantum = 125000 / 10 = 12500 bytes

If rate < r2q × mtu → quantum is set to mtu.
If quantum is too small → scheduling overhead increases.
If quantum is too large → fairness degrades.

Adjust r2q at root:
  tc qdisc add dev eth0 root handle 1: htb r2q 20

Or set per-class:
  tc class add ... htb rate 1mbit quantum 1514
```

---

## 13. HFSC — Hierarchical Fair Service Curve

HFSC is more complex than HTB but provides precise latency guarantees, not
just rate guarantees.

### The Service Curve Concept

```
HTB says: "This class gets X bps guaranteed."
HFSC says: "This class gets X bps, and I GUARANTEE the first
            packet arrives within Y milliseconds."

SERVICE CURVE: A two-slope function defining:
  - Initial burst: fast service for the first M bytes
  - Long-term rate: sustained service rate

  Bandwidth
  (bytes/s)
      │
  m1  │────────────────┐
      │                │
      │                │  Slope = m2 (sustained rate)
      │                └────────────────────────────────
  m2  │                 
      │
      └──────────────────────────────────────────────── Time
      0       d

  m1 = initial rate (burst)
  d  = duration of initial rate
  m2 = long-term rate (after burst)

Meaning:
  "For the first d seconds, serve at m1 rate.
   After that, serve at m2 rate."

This gives:
  - Latency guarantee (via m1, d)
  - Bandwidth guarantee (via m2)
```

### HFSC Parameters

```
HFSC per-class parameters:
  sc  = service curve (both rt and ls combined)
  rt  = realtime service curve (hard guarantee)
  ls  = link-sharing service curve (fair share)
  ul  = upper limit (ceiling, like HTB ceil)

REALTIME CURVE (rt):
  Hard latency + rate guarantee.
  HFSC ensures these deadlines are met FIRST.
  Use for VoIP, real-time video.

LINK-SHARING CURVE (ls):
  Fair share of spare bandwidth.
  Like HTB's rate but curve-based.
  Classes without rt use this.

UPPER LIMIT (ul):
  Maximum bandwidth (like HTB ceil).
```

```bash
# HFSC Example
tc qdisc add dev eth0 root handle 1: hfsc default 30

# Root class (10 Mbit total)
tc class add dev eth0 parent 1: classid 1:1 hfsc sc rate 10mbit ul rate 10mbit

# VoIP: guarantee 500kbps with fast initial service
#   rt m1 2m d 10ms m2 500k: initially 2Mbps for 10ms, then 500kbps
#   ul rate 2m: max 2Mbps
tc class add dev eth0 parent 1:1 classid 1:10 hfsc \
    rt m1 2m d 10ms m2 500k \
    ls m1 2m d 10ms m2 500k \
    ul rate 2m

# Interactive: 3Mbps sustained, burst 10Mbps for 20ms
tc class add dev eth0 parent 1:1 classid 1:20 hfsc \
    rt m1 10m d 20ms m2 3m \
    ls m1 10m d 20ms m2 3m \
    ul rate 10m

# Bulk: just link sharing, no realtime guarantee
tc class add dev eth0 parent 1:1 classid 1:30 hfsc \
    ls rate 6m \
    ul rate 10m
```

### HFSC Scheduler Flow

```
HFSC SCHEDULER DECISION:

At each dequeue call:
  1. Check REALTIME eligible classes:
       For each class, virtual time (vt) compared to current time.
       Class is eligible if vt ≤ current_time.
       Among eligible → pick class with EARLIEST deadline (EDF).

  2. If no realtime class is eligible:
       Use LINK-SHARING:
       Among all classes → pick class with lowest virtual time.
       (Approximates fair share)

Virtual Time (vt) concept:
  vt = time at which class has received its fair share.
  Fast service → vt advances slowly (class got more than fair share).
  Slow service → vt advances quickly (class is behind).
  Always serve class with smallest vt → catches up the "behind" ones.
```

---

## 14. FQ-CoDel — The Modern Default

Since kernel 3.5, fq_codel has been recommended as the default qdisc for
most use cases. It replaced pfifo_fast in many distributions (Ubuntu, Fedora,
Debian since 2020).

### Why FQ-CoDel Solves Everything

```
PROBLEM SUMMARY (what fq_codel solves):

1. BUFFERBLOAT: Deep buffers → huge latency under load.
   Solution: CoDel measures sojourn time, drops to signal congestion.

2. UNFAIRNESS: Bulk flows starve interactive flows.
   Solution: FQ separates into per-flow queues, round-robins.

3. TCP BURST PROBLEM: New connections get stuck in back of queue.
   Solution: New flows get "new flow" queue (higher priority).

4. INCAST: Many flows arriving at same time overwhelm one queue.
   Solution: Each flow isolated → one bad flow can't hurt others.
```

### DRR — Deficit Round Robin (used by FQ-CoDel)

```
DRR (Deficit Round Robin) — fair even with variable packet sizes:

Each flow has:
  quantum  : bytes allowed per round (e.g., 1514)
  deficit  : credit carried from previous round

ROUND EXAMPLE (3 flows, quantum=1514):
  Flow A: has 3000 byte packet
  Flow B: has 500 byte packet
  Flow C: has 1514 byte packet

Round 1:
  Flow A: deficit=0+1514=1514. Packet=3000 > deficit. SKIP. deficit=1514.
  Flow B: deficit=0+1514=1514. Packet=500 ≤ deficit. SEND. deficit=1014.
  Flow C: deficit=0+1514=1514. Packet=1514 ≤ deficit. SEND. deficit=0.

Round 2:
  Flow A: deficit=1514+1514=3028. Packet=3000 ≤ deficit. SEND. deficit=28.
  Flow B: deficit=1014+1514=2528. Has more packets? If yes...
  Flow C: deficit=0+1514=1514. ...

Result: Each flow gets ~same BYTE ALLOCATION per time period.
Large packets don't get penalized — they just accumulate credit.
```

### FQ-CoDel Internal Architecture

```
FQ-CODEL DETAILED FLOW:

Packet arrives
      │
      ▼
Hash(src_ip, dst_ip, src_port, dst_port, proto) → bucket index
      │
      ▼
Is bucket empty? ─── YES ──► Create new flow, add to "new flows" list
      │
     NO
      │
      ▼
Add packet to flow's queue
      │
      ▼ (CoDel check on enqueue)
Flow queue too old? (sojourn > target for > interval?)
      │
    YES → Mark for dropping at dequeue
      │
     NO → Normal enqueue

══════════════ DEQUEUE (driver asks for next packet) ══════════════

New flows list empty?
  NO → Take first flow from new flows list
  YES → Take from old flows list

Dequeue next packet from selected flow's CoDel queue
      │
CoDel says drop this packet?
  YES → Drop it, try again with same flow
   NO → Send it to wire
      │
Flow still has packets?
  YES → Move to END of old flows list
   NO → Remove from active lists

Deficit handling (DRR):
  If flow's deficit < 0 after sending → move to end of list
  Add quantum to deficit for next round
```

---

## 15. CAKE — Common Applications Kept Enhanced

CAKE is the culmination of all qdisc knowledge — created by the sqm-scripts
community, merged in kernel 4.19.

### CAKE's Three Layers

```
CAKE ARCHITECTURE:

Layer 1: RATE LIMITING (Token Bucket)
  Simple bandwidth limit with overhead compensation.

Layer 2: PRIORITY (8-tier DSCP-based)
  Traffic classified into tiers by DSCP.
  Each tier is a separate flow queue.

Layer 3: FLOW ISOLATION (FQ-CoDel per tier)
  Within each tier: per-flow fair queuing.
  CoDel per flow for bufferbloat control.

         ┌────────────────────────────────────────┐
         │              CAKE                       │
         │                                        │
         │  ┌──────────────────────────────────┐  │
         │  │  RATE LIMITER (Token Bucket)      │  │
         │  │  bandwidth 100mbit                │  │
         │  │  overhead 18 (PPPoE)              │  │
         │  └──────────────┬───────────────────┘  │
         │                 │                       │
         │  ┌──────────────▼───────────────────┐  │
         │  │  PRIORITY TIERS (8 tiers)         │  │
         │  │                                   │  │
         │  │  Tier 8 ██████ (Network Control)  │  │
         │  │  Tier 7 ██████ (Internet Control) │  │
         │  │  Tier 6 ██████ (Critical Apps)    │  │
         │  │  Tier 5 ██████ (Voice)            │  │
         │  │  Tier 4 ██████ (Video)            │  │
         │  │  Tier 3 ██████ (Best Effort)      │  │
         │  │  Tier 2 ██████ (Low Priority)     │  │
         │  │  Tier 1 ██████ (Bulk)             │  │
         │  └──────────────┬───────────────────┘  │
         │                 │                       │
         │  ┌──────────────▼───────────────────┐  │
         │  │  FLOW ISOLATION (FQ-CoDel)        │  │
         │  │  Per-flow queues with CoDel       │  │
         │  └──────────────────────────────────┘  │
         └────────────────────────────────────────┘
```

### CAKE Flow Isolation Modes

```
FLOW ISOLATION OPTIONS (what defines a "flow"?):

  flowblind : No isolation (one big queue)
  srchost   : Per source IP
  dsthost   : Per destination IP
  hosts     : Per src+dst IP pair
  flows     : Per 5-tuple (src IP, dst IP, src port, dst port, proto)
  dual-srchost : 2-level: per-host fairness, then per-flow within host
  dual-dsthost : 2-level: per-destination, then per-flow
  triple-isolate : 3-level: per src host, per dst host, per flow (DEFAULT)

triple-isolate EXPLAINED:

  Level 1: Fair between src hosts
  Level 2: Fair between dst hosts (given a src host)
  Level 3: Fair between flows (given src+dst)

  Example: Host A has 100 flows to server S.
           Host B has 1 flow to server S.

  Without triple-isolate (just flow isolation):
    A gets 100/101 of bandwidth (100 flows)
    B gets 1/101 of bandwidth (1 flow)
    → UNFAIR (A dominates)

  With triple-isolate:
    A and B each get 50% (host fairness)
    Within A's 50%, each of A's 100 flows gets 0.5%
    B's 1 flow gets 50%
    → FAIR (host-level fairness)
```

### CAKE Overhead Compensation

```
OVERHEAD COMPENSATION — Critical for accurate shaping:

The wire carries MORE than just your IP packet.
If you set bandwidth=10mbit but don't account for overhead,
you're actually sending MORE than 10mbit on the wire.

ETHERNET OVERHEAD:
  [Preamble 7B][SFD 1B][Dst MAC 6B][Src MAC 6B][Ethertype 2B]
  [Payload ≤1500B][FCS 4B][Interframe Gap 12B]
  
  Ethernet overhead per packet: 7+1+6+6+2+4+12 = 38 bytes
  Plus Ethernet header (14 bytes) is INSIDE the IP frame
  
  CAKE overhead "ethernet" = 38 bytes

ADSL/PPPoE overhead:
  PPPoE header: 8 bytes
  PPP header: 2 bytes
  ATM cell padding: variable
  
  CAKE overhead "pppoe-vcmux" = 40 bytes
  CAKE overhead "pppoa-vcmux" = 42 bytes

VDSL/VLAN overhead:
  VLAN tag: 4 bytes
  CAKE overhead "ether-vlan" = 4 bytes (adds to ethernet)

CAKE compensates AUTOMATICALLY:
  tc qdisc add dev eth0 root cake bandwidth 100mbit ethernet
  → Subtracts 38 bytes per packet from accounting
  → 100mbit means 100mbit of WIRE bandwidth
     (not 100mbit of IP payload)
```

### CAKE NAT Awareness

```
CAKE NAT AWARENESS:

Problem with NAT (masquerade):
  Router does NAT: all outbound packets have ROUTER's src IP.
  CAKE sees ALL flows as coming from ONE host.
  Flow isolation breaks — can't differentiate clients.

nat keyword enables CAKE to look up conntrack table:
  → Finds original pre-NAT src IP
  → Uses that for flow isolation

tc qdisc add dev wan0 root cake bandwidth 50mbit \
    triple-isolate \
    nat \            ← Enable NAT awareness
    overhead 44      ← PPPoE overhead
```

### Complete CAKE Configuration

```bash
# CAKE for home router (WAN egress)
tc qdisc replace dev wan0 root cake \
    bandwidth 50mbit \    # your uplink speed
    diffserv4 \           # 4 priority tiers (simplified DSCP)
    triple-isolate \      # 3-level fairness
    nat \                 # NAT awareness
    wash \                # Reset DSCP on ingress (don't trust ISP)
    no-ack-filter \       # Don't filter TCP ACKs (causes issues with some apps)
    overhead 44 \         # PPPoE overhead
    mpu 64               # minimum packet unit (ATM padding)

# CAKE for home router (WAN ingress via IFB)
tc qdisc replace dev ifb4wan0 root cake \
    bandwidth 200mbit \   # your downlink speed
    diffserv4 \
    triple-isolate \
    nat \
    ingress \             # Tell CAKE this is ingress (swaps src/dst for isolation)
    wash \
    overhead 44 \
    mpu 64
```

---

## 16. netem — Network Emulation (Complete Reference)

netem simulates real-world network conditions for testing. Used by developers
to test how applications behave on bad networks.

### Complete netem Options

```
DELAY:
  delay TIME [JITTER [CORRELATION]]
  delay 100ms              # fixed 100ms delay
  delay 100ms 20ms         # 100ms ± 20ms uniform
  delay 100ms 20ms 25%     # 25% correlation between consecutive delays
  delay 100ms 20ms distribution normal   # normal distribution
  delay 100ms 20ms distribution pareto  # heavy-tail distribution

LOSS:
  loss random PERCENT [CORRELATION]
  loss random 1%           # 1% random loss
  loss random 5% 25%       # 5% with 25% correlation (burst loss)

  loss gemodel P [R [1-H [1-K]]]  # Gilbert-Elliott model
  # P = transition good→bad
  # R = transition bad→good
  # H = loss prob in bad state
  # K = loss prob in good state
  loss gemodel 1% 10% 50%  # burst loss model

  loss state P13 [P31 [P32 [P23 [P14]]]]  # 4-state Markov model

CORRUPTION:
  corrupt PERCENT [CORRELATION]
  corrupt 0.1%             # 0.1% of packets corrupted

DUPLICATION:
  duplicate PERCENT [CORRELATION]
  duplicate 1%             # 1% packets duplicated

REORDERING:
  reorder PERCENT [CORRELATION] [gap DISTANCE]
  reorder 25% 50%          # 25% reorder with 50% correlation
  # Reorder with gap: every DISTANCE-th packet is not delayed
  # (creates reordering by delaying most but not gap-th)

RATE LIMITING (within netem):
  rate RATE [PACKETOVERHEAD [CELLSIZE [CELLOVERHEAD]]]
  rate 1mbit               # limit to 1mbit
  rate 1mbit 0 1500 0      # with cell size for ATM simulation

SLOT (burst model):
  slot MIN_DELAY MAX_DELAY [packets N] [bytes B]
  # Groups packets into slots, releases in bursts
  slot 800us 1600us packets 16
```

### netem + TBF for Realistic WAN Simulation

```bash
# Simulate a 100ms RTT, 10Mbit/s DSL with 1% loss
# Use TBF for rate limiting + netem for delay/loss

# Step 1: TBF for rate shaping
tc qdisc add dev eth0 root handle 1: tbf \
    rate 10mbit \
    burst 32kbit \
    latency 50ms

# Step 2: netem as child of TBF (delay/loss applied AFTER shaping)
tc qdisc add dev eth0 parent 1:1 handle 2: netem \
    delay 50ms 5ms \    # 50ms delay (50ms each way = 100ms RTT)
    loss 1%

# Order matters!
# TBF first: shapes rate
# netem inside: adds delay
# Net effect: 10Mbit/s link with 100ms RTT and 1% loss
```

---

## 17. IFB — Intermediate Functional Block (Ingress Shaping)

IFB is the solution to the fundamental problem: **you cannot shape ingress
traffic** because it's already in your buffer when tc sees it.

### The IFB Trick

```
INGRESS SHAPING USING IFB:

WITHOUT IFB (Problem):
  [Internet] ──► eth0 ingress ──► tc can only POLICE (drop)
  Traffic already in NIC buffer when we see it.

WITH IFB (Solution):
  [Internet] ──► eth0 ingress ──► REDIRECT ──► ifb0 egress ──► full tc!
                    │                               │
              (policing filter               (HTB/CAKE shaping
               redirects all                 works perfectly here)
               to ifb0)                           │
                                                  ▼
                                       ip_stack (normal processing)

The magic: After ifb0 "transmits" (dequeues), packet is
           re-injected into the IP stack, not actually sent
           to any physical interface.

SETUP:

# Load IFB module
modprobe ifb numifbs=1

# Bring up ifb0
ip link set ifb0 up

# Redirect ALL ingress from eth0 to ifb0
tc qdisc add dev eth0 ingress handle ffff:
tc filter add dev eth0 parent ffff: protocol all prio 1 \
    u32 match u32 0 0 \       # match all packets
    action mirred egress redirect dev ifb0

# Now configure FULL shaping on ifb0 egress
tc qdisc add dev ifb0 root handle 1: htb default 10
tc class add dev ifb0 parent 1: classid 1:1 htb rate 100mbit ceil 100mbit
tc class add dev ifb0 parent 1:1 classid 1:10 htb rate 100mbit ceil 100mbit
# ... add filters as needed
```

### IFB with CAKE (SQM-Scripts Style)

```bash
# Create IFB for ingress shaping
modprobe ifb numifbs=1
ip link set ifb0 up

# Redirect eth0 ingress to ifb0
tc qdisc add dev eth0 handle ffff: ingress
tc filter add dev eth0 parent ffff: matchall \
    action mirred egress redirect dev ifb0

# CAKE on egress (outbound shaping)
tc qdisc replace dev eth0 root cake \
    bandwidth 50mbit \
    diffserv4 \
    triple-isolate \
    nat \
    overhead 44

# CAKE on ifb0 for ingress shaping
tc qdisc replace dev ifb0 root cake \
    bandwidth 500mbit \    # your download speed
    diffserv4 \
    triple-isolate \
    nat \
    ingress \              # reversed src/dst for host isolation
    overhead 44
```

---

## 18. tc Command Syntax — Complete Reference

### Global Syntax

```
tc OBJECT COMMAND [OPTIONS]

OBJECT:
  qdisc   : queue discipline
  class   : traffic class
  filter  : packet classifier
  action  : standalone action

COMMAND:
  add     : create new object
  del     : delete object
  replace : create or replace
  change  : modify existing
  show    : display (also: list)

OPTIONS:
  -s / --statistics  : show statistics
  -d / --details     : show details
  -r / --raw         : raw format
  -p / --pretty      : pretty print
  -j / --json        : JSON output
  -n NETNS           : operate in network namespace
  -b FILE            : batch mode (read commands from file)
  -f / --force       : force operation
```

### qdisc Commands

```bash
# Add qdisc
tc qdisc add dev DEV [parent PARENT | root] [handle HANDLE] TYPE [OPTIONS]

# Delete qdisc
tc qdisc del dev DEV [parent PARENT | root | ingress] [handle HANDLE]

# Show qdiscs
tc qdisc show [dev DEV]
tc -s qdisc show dev eth0    # with statistics

# Replace (atomic: del+add in one operation)
tc qdisc replace dev DEV root handle HANDLE TYPE [OPTIONS]

# Ingress qdisc (special)
tc qdisc add dev eth0 handle ffff: ingress

# EXAMPLES:
tc qdisc add dev eth0 root handle 1: htb default 10
tc qdisc add dev eth0 root fq_codel
tc qdisc add dev eth0 root netem delay 100ms
tc qdisc del dev eth0 root
```

### class Commands

```bash
# Add class
tc class add dev DEV parent PARENT classid CLASSID TYPE [OPTIONS]

# Delete class
tc class del dev DEV parent PARENT classid CLASSID

# Show classes
tc class show [dev DEV]
tc -s class show dev eth0

# Change class parameters
tc class change dev DEV classid CLASSID TYPE [OPTIONS]

# EXAMPLES:
tc class add dev eth0 parent 1:   classid 1:1  htb rate 10mbit
tc class add dev eth0 parent 1:1  classid 1:10 htb rate 1mbit ceil 10mbit prio 0
tc class add dev eth0 parent 1:1  classid 1:20 htb rate 9mbit ceil 10mbit prio 1
```

### filter Commands

```bash
# Add filter
tc filter add dev DEV [parent PARENT | root] protocol PROTO \
    prio PRIO TYPE [OPTIONS] [flowid CLASSID] [action ACTION]

# Delete filter
tc filter del dev DEV [parent PARENT | root] [prio PRIO] [handle HANDLE TYPE]

# Show filters
tc filter show [dev DEV] [parent PARENT | root]

# EXAMPLES:
# u32 filter matching TCP port 80
tc filter add dev eth0 parent 1:0 protocol ip prio 10 \
    u32 match ip dport 80 0xffff flowid 1:20

# u32 with multiple match conditions (AND logic)
tc filter add dev eth0 parent 1:0 protocol ip prio 20 \
    u32 match ip protocol 6 0xff \
    match ip dport 443 0xffff \
    flowid 1:20

# fw filter (reads iptables mark)
tc filter add dev eth0 parent 1:0 prio 1 handle 10 fw flowid 1:10

# flower filter
tc filter add dev eth0 parent 1:0 protocol ip prio 5 \
    flower dst_ip 10.0.0.0/8 ip_proto tcp dst_port 22 flowid 1:10

# matchall (catch-all)
tc filter add dev eth0 parent 1:0 protocol all prio 999 \
    matchall flowid 1:30
```

### Statistics and Monitoring

```bash
# Show qdisc stats (packets/bytes/drops per qdisc)
tc -s qdisc show dev eth0

# Sample output explained:
# qdisc htb 1: root refcnt 9 r2q 10 default 0x30 direct_packets_stat 0
#  Sent 152847 bytes 1337 pkt (dropped 0, overlimits 22 requeues 0)
#  backlog 0b 0p requeues 0
#  ^       ^    ^  ^         ^       ^
#  bytes   pkts drops overlimits   requeues
#
# overlimits: packets that exceeded the rate limit (had to wait)
# dropped: packets dropped (buffer full)
# requeues: driver asked to requeue (should be rare)

# Show class stats (per-class breakdown)
tc -s class show dev eth0

# Show filter stats
tc -s filter show dev eth0 parent 1:

# Live monitoring (watch mode)
watch -n 1 'tc -s qdisc show dev eth0'

# JSON output for programmatic use
tc -j -s qdisc show dev eth0 | python3 -m json.tool
```

### Batch Mode

```bash
# Create script file
cat > /etc/tc-rules.sh << 'EOF'
qdisc del dev eth0 root 2>/dev/null || true
qdisc add dev eth0 root handle 1: htb default 30
class add dev eth0 parent 1: classid 1:1 htb rate 100mbit
class add dev eth0 parent 1:1 classid 1:10 htb rate 10mbit ceil 100mbit prio 0
class add dev eth0 parent 1:1 classid 1:20 htb rate 40mbit ceil 100mbit prio 1
class add dev eth0 parent 1:1 classid 1:30 htb rate 50mbit ceil 100mbit prio 2
filter add dev eth0 parent 1:0 protocol ip prio 1 u32 match ip tos 0x10 0xff flowid 1:10
EOF

# Run batch
tc -batch /etc/tc-rules.sh

# Or pipe:
cat /etc/tc-rules.sh | tc -batch -
```

---

## 19. Real-World Scenarios and Recipes

### Scenario 1: Prevent a Single Download from Killing VoIP

```
PROBLEM:
  Home network: 10 Mbit uplink, 50 Mbit downlink.
  When someone torrents, VoIP calls drop out.
  
SOLUTION:
  HTB on uplink: Prioritize VoIP above everything.
  CAKE on downlink: Fair queuing prevents download queue from
                    filling up (bufferbloat fix).

UPLINK (egress on WAN interface):
  ┌─── VoIP (1mbit guaranteed, 10mbit max, prio 0) ───┐
  │─── Interactive (3mbit, 10mbit, prio 1) ────────────┤
  └─── Bulk/Torrent (6mbit, 10mbit, prio 2) ──────────┘

DOWNLINK (IFB with CAKE):
  CAKE with triple-isolate: each host gets fair share
  CoDel per flow: prevents bufferbloat
```

```bash
#!/bin/bash
# === UPLINK: HTB Priority Shaping ===
WAN=eth0
UPLINK=10mbit

tc qdisc del dev $WAN root 2>/dev/null
tc qdisc add dev $WAN root handle 1: htb default 20

tc class add dev $WAN parent 1:  classid 1:1  htb rate $UPLINK burst 15k
tc class add dev $WAN parent 1:1 classid 1:10 htb rate 1mbit ceil $UPLINK burst 15k prio 0
tc class add dev $WAN parent 1:1 classid 1:20 htb rate 3mbit ceil $UPLINK burst 15k prio 1
tc class add dev $WAN parent 1:1 classid 1:30 htb rate 6mbit ceil $UPLINK burst 15k prio 2

tc qdisc add dev $WAN parent 1:10 handle 10: fq_codel
tc qdisc add dev $WAN parent 1:20 handle 20: fq_codel
tc qdisc add dev $WAN parent 1:30 handle 30: fq_codel

# VoIP: SIP (UDP 5060) and RTP (UDP 10000-20000)
tc filter add dev $WAN parent 1:0 protocol ip prio 1 u32 \
    match ip protocol 17 0xff match ip dport 5060 0xffff flowid 1:10
tc filter add dev $WAN parent 1:0 protocol ip prio 2 u32 \
    match ip protocol 17 0xff match ip dport 10000 0xe000 flowid 1:10

# DSCP EF (VoIP typically sets this)
tc filter add dev $WAN parent 1:0 protocol ip prio 3 u32 \
    match ip tos 0xb8 0xfc flowid 1:10

# Interactive: SSH, DNS, small HTTP
tc filter add dev $WAN parent 1:0 protocol ip prio 10 u32 \
    match ip protocol 6 0xff match ip dport 22 0xffff flowid 1:20
tc filter add dev $WAN parent 1:0 protocol ip prio 11 u32 \
    match ip protocol 17 0xff match ip dport 53 0xffff flowid 1:20

# Torrent detection: high port numbers UDP (common with BitTorrent)
# Torrent goes to default class 1:20 (or add specific rules for 1:30)

# === DOWNLINK: CAKE with IFB ===
DOWNLINK=50mbit
modprobe ifb numifbs=1
ip link set ifb0 up

tc qdisc add dev $WAN handle ffff: ingress
tc filter add dev $WAN parent ffff: matchall \
    action mirred egress redirect dev ifb0

tc qdisc replace dev ifb0 root cake \
    bandwidth $DOWNLINK \
    diffserv4 \
    triple-isolate \
    nat \
    ingress

echo "QoS configured successfully"
```

### Scenario 2: Rate Limiting Customers on an ISP Edge

```
SCENARIO:
  ISP with 100 customers.
  Each customer has a plan:
    Basic: 10 Mbit/s download, 1 Mbit/s upload
    Premium: 50 Mbit/s, 5 Mbit/s
    Business: 100 Mbit/s, 10 Mbit/s

IMPLEMENTATION: HTB per customer IP, iptables marks per-plan.
```

```bash
#!/bin/bash
# ISP edge QoS
IFACE=eth0

tc qdisc del dev $IFACE root 2>/dev/null
tc qdisc add dev $IFACE root handle 1: htb default 9999

# Root class (1 Gbps total uplink)
tc class add dev $IFACE parent 1:  classid 1:1 htb rate 1gbit burst 100k

# Plan templates
# Basic customers: class 1:1000-1999, rate 1mbit, ceil 1mbit
# Premium: 1:2000-2999, rate 5mbit, ceil 5mbit
# Business: 1:3000-3999, rate 10mbit, ceil 10mbit

# Example: Add one customer each plan
# Customer 101 (Basic, IP 10.0.0.101)
tc class add dev $IFACE parent 1:1 classid 1:1101 htb \
    rate 1mbit ceil 1mbit burst 32k
tc filter add dev $IFACE parent 1:0 protocol ip prio 100 u32 \
    match ip src 10.0.0.101/32 flowid 1:1101

# Customer 201 (Premium, IP 10.0.0.201)
tc class add dev $IFACE parent 1:1 classid 1:2201 htb \
    rate 5mbit ceil 5mbit burst 64k
tc filter add dev $IFACE parent 1:0 protocol ip prio 100 u32 \
    match ip src 10.0.0.201/32 flowid 1:2201

# Drop class (default for unclassified = unlimited is dangerous)
tc class add dev $IFACE parent 1:1 classid 1:9999 htb \
    rate 1mbit ceil 1mbit   # unknown customers get 1Mbit

# Script to add customers dynamically:
add_customer() {
    local IP=$1 PLAN=$2 CLASSID=$3
    local RATE
    case $PLAN in
        basic)   RATE="1mbit" ;;
        premium) RATE="5mbit" ;;
        business)RATE="10mbit" ;;
    esac

    tc class add dev $IFACE parent 1:1 classid 1:$CLASSID htb \
        rate $RATE ceil $RATE burst 32k
    tc filter add dev $IFACE parent 1:0 protocol ip prio 100 u32 \
        match ip src $IP/32 flowid 1:$CLASSID
}

add_customer 10.0.0.102 basic 1102
add_customer 10.0.0.202 premium 2202
add_customer 10.0.0.302 business 3302
```

### Scenario 3: Network Emulation for Testing

```bash
#!/bin/bash
# Simulate various real-world network conditions for testing

simulate() {
    local SCENARIO=$1
    tc qdisc del dev lo root 2>/dev/null

    case $SCENARIO in
        "wifi-home")
            # Home WiFi: 50ms delay, 0.1% loss, jitter
            tc qdisc add dev lo root netem \
                delay 20ms 5ms distribution normal \
                loss 0.1%
            ;;
        "mobile-4g")
            # 4G LTE: ~30ms latency, occasional loss, variable
            tc qdisc add dev lo root handle 1: netem \
                delay 30ms 15ms distribution normal \
                loss gemodel 1% 5% 50%
            ;;
        "mobile-3g")
            # 3G: high latency, limited bandwidth
            tc qdisc add dev lo root handle 1: tbf \
                rate 384kbit burst 32kbit latency 100ms
            tc qdisc add dev lo parent 1:1 handle 2: netem \
                delay 100ms 40ms distribution pareto \
                loss 2%
            ;;
        "satellite")
            # Satellite: 600ms RTT, occasional loss
            tc qdisc add dev lo root netem \
                delay 300ms 20ms \
                loss 0.5%
            ;;
        "bad-wifi")
            # Congested WiFi: packet loss, reordering, corruption
            tc qdisc add dev lo root netem \
                delay 50ms 30ms \
                loss random 3% 25% \
                corrupt 0.1% \
                reorder 10% 50% \
                duplicate 0.5%
            ;;
        "perfect")
            # Remove all impairments
            echo "Removed all impairments"
            ;;
    esac
    echo "Applied: $SCENARIO"
}

# Usage: simulate wifi-home / mobile-4g / satellite / bad-wifi / perfect
simulate "${1:-wifi-home}"
```

### Scenario 4: Container/Kubernetes Network Rate Limiting

```bash
#!/bin/bash
# Rate limit a specific container's network usage
# Uses cgroup-based classification

CONTAINER_ID="abc123"
IFACE="docker0"
LIMIT="100mbit"

# Find cgroup for container
CGROUP_PATH="/sys/fs/cgroup/net_cls/docker/${CONTAINER_ID}"

# Set net_cls classid for the cgroup
# This marks packets from processes in this cgroup
CLASSID=1:100
echo 0x00010064 > ${CGROUP_PATH}/net_cls.classid  # 1:100 in hex

# Setup HTB
tc qdisc add dev $IFACE root handle 1: htb default 9999
tc class add dev $IFACE parent 1:  classid 1:1    htb rate 10gbit
tc class add dev $IFACE parent 1:1 classid 1:100  htb rate $LIMIT ceil $LIMIT
tc class add dev $IFACE parent 1:1 classid 1:9999 htb rate 10gbit ceil 10gbit

# Filter: match cgroup classid
tc filter add dev $IFACE parent 1:0 protocol ip prio 1 \
    cgroup flowid 1:100
```

---

## 20. Internals: How tc Works in the Kernel

### The sk_buff Journey Through a Classful qdisc

```
KERNEL CALL FLOW — Packet Transmission

dev_queue_xmit(skb)                    [net/core/dev.c]
    │
    ├── Get txq = skb_get_tx_queue(dev, skb)
    │   (select TX queue — NIC may have multiple)
    │
    └── __dev_queue_xmit(skb, sb_dev)
            │
            ├── rc = q->enqueue(skb, q, &to_free)
            │   ^─── THIS IS THE TC QDISC!
            │   (e.g., htb_enqueue, fq_codel_enqueue)
            │
            └── __qdisc_run(q)
                    │
                    └── Loop:
                        skb = dequeue_skb(q, &validate, quota)
                        ^─── q->dequeue(q) = TC SCHEDULER!
                             (htb_dequeue, fq_codel_dequeue)
                        │
                        ootx_transmit(skb, dev, q, validate)
                        │
                        netdev_start_xmit(skb, dev, txq, ...)
                        (→ driver's ndo_start_xmit)
```

### NET_TX_SOFTIRQ — Deferred Transmission

```
WHY SOFTIRQ?

Problem: Dequeue must run in interrupt context or process context.
  If we dequeue synchronously in dev_queue_xmit:
    - We might block (if NIC TX ring full)
    - We hold locks too long
    - Latency increases

Solution: NET_TX_SOFTIRQ (software interrupt)
  - Raises a soft interrupt (scheduled, not immediate)
  - Runs in softirq context (non-preemptible but yields between runs)
  - Responsible for draining the qdisc and feeding the driver

FLOW:
  1. Process calls send() → packets go into qdisc (enqueue)
  2. NET_TX_SOFTIRQ fires (on same or different CPU)
  3. net_tx_action() runs:
     - Calls qdisc_run() for all pending qdiscs
     - qdisc_run() dequeues and sends to driver
  4. Driver uses DMA to push to NIC hardware
```

### TSO/GSO Interaction with tc

```
GSO (Generic Segmentation Offload) / TSO (TCP Segmentation Offload):

APPLICATION SENDS: one huge 64KB buffer
TCP CREATES: one giant "super-packet" (GSO packet)
  → This super-packet is 64KB but NOT a real packet
  → It will be segmented before hitting the wire

WHERE IS tc?
  tc sees the SUPER-PACKET (64KB), not 45 individual 1500B packets.

PROBLEM: tc counts the 64KB packet as "one packet" for scheduling.
  Round-robin thinks it's fair (one per flow) but flow A sent 64KB
  while flow B sent 1500B. Not fair!

SOLUTION: "Split GSO" in CAKE (and some other qdiscs):
  CAKE has a built-in "GSO splitter":
  → Before enqueue, splits GSO into real 1500B segments
  → Now round-robin is truly fair (per real packet)

  tc qdisc add dev eth0 root cake ...
  (CAKE does this automatically via the 'split_gso' feature)

For other qdiscs, GSO splitting is done by the infrastructure
if the qdisc sets the TCQ_F_CAN_BYPASS_EGQ flag and GSO
splitting is enabled.

Check:
  ethtool -k eth0 | grep segmentation
  # tcp-segmentation-offload: on
  # generic-segmentation-offload: on

Disable GSO for accurate tc (PERFORMANCE COST):
  ethtool -K eth0 tso off gso off
```

### The Qdisc Lock

```
LOCKING:

Each qdisc has a spinlock (q->lock).
  - All enqueue/dequeue ops hold this lock.
  - This is the main contention point on multi-core systems.

Per-CPU qdiscs (bypass the lock):
  - pfifo_fast uses per-CPU queues in some implementations
  - fq uses per-CPU flow selection

qdisc_lock(q) / qdisc_unlock(q) macros wrap spin_lock_bh.
  _bh = "bottom half" = disables softirq during lock
  (prevents deadlock between process context and softirq context)

Lock-free path (TCQ_F_CAN_BYPASS):
  Some qdiscs allow bypassing enqueue/dequeue when:
  - NIC TX ring is empty
  - qdisc queue is empty
  - → Packet goes directly to driver (no queueing at all)
  
  This is the "direct transmit" fast path.
  Shown in tc stats as "direct_packets_stat".
```

### Rate Calculation: Ticks and Clocks

```
HOW tc MEASURES TIME:

Linux kernel uses "jiffies" for coarse timing (10ms granularity).
tc needs MICROSECOND precision.

tc uses PSCHED_NS2TICKS / PSCHED_TICKS2NS:
  Kernel has a high-resolution clock (hrtimer).
  Timestamps in nanoseconds.

Token bucket clock:
  Every time the qdisc is invoked, check current time.
  Calculate tokens accumulated since last invocation.
  tokens += (now - last_time) * rate

TIME REPRESENTATION in kernel:
  ktime_t = 64-bit nanoseconds since boot
  
Rate representation:
  tc stores rates in bytes per nanosecond (scaled by 2^32):
  rate_in_kernel = (rate_bps / 8) * (2^32 / NSEC_PER_SEC)
  
This avoids floating point (kernel has no FPU in softirq context).
All rate math is integer arithmetic with pre-computed scaling tables.
```

---

## 21. Netlink Protocol — How Userspace Talks to tc

tc (the `iproute2` tool) communicates with the kernel via **Netlink sockets**
— a special IPC mechanism designed for kernel-userspace communication.

### Netlink Basics

```
NETLINK OVERVIEW:

Regular socket: TCP/UDP (user↔user or kernel IP stack)
Netlink socket: kernel↔userspace for MANAGEMENT operations
  → No network goes out. Pure local IPC.

Netlink families (relevant to tc):
  NETLINK_ROUTE = 0    → Routing, interfaces, addresses, tc
  NETLINK_GENERIC      → Generic Netlink (for newer subsystems)

NETLINK MESSAGE FORMAT:
  ┌──────────────────────────────────────────────────────┐
  │              Netlink Message Header (16 bytes)        │
  │  nlmsglen(4) nlmsgtype(2) nlmsgflags(2) seq(4) pid(4)│
  └──────────────────────────────────────────────────────┘
  │              Payload                                   │
  │  (depends on nlmsgtype)                               │
  └──────────────────────────────────────────────────────┘

Message types for tc (RTM_ = Route Table Message):
  RTM_NEWQDISC  = 36  → Create/replace qdisc
  RTM_DELQDISC  = 37  → Delete qdisc
  RTM_GETQDISC  = 38  → Get qdisc info
  RTM_NEWTCLASS = 40  → Create/replace class
  RTM_DELTCLASS = 41  → Delete class
  RTM_GETTCLASS = 42  → Get class info
  RTM_NEWTFILTER= 44  → Create/replace filter
  RTM_DELTFILTER= 45  → Delete filter
  RTM_GETTFILTER= 46  → Get filter info
```

### TC Netlink Message Structure

```
RTM_NEWQDISC MESSAGE (add a qdisc):

┌─────────────────────────────────────────┐
│ nlmsghdr                                │
│  nlmsg_len  = total message size        │
│  nlmsg_type = RTM_NEWQDISC             │
│  nlmsg_flags= NLM_F_REQUEST | NLM_F_ACK│
│  nlmsg_seq  = sequence number          │
│  nlmsg_pid  = sender PID               │
├─────────────────────────────────────────┤
│ tcmsg (traffic control message)         │
│  tcm_family  = AF_UNSPEC               │
│  tcm_ifindex = interface index (eth0=2) │
│  tcm_handle  = MAJOR:MINOR (e.g., 1:0) │
│  tcm_parent  = parent handle           │
│  tcm_info    = priority << 16 | proto  │
├─────────────────────────────────────────┤
│ Netlink Attributes (NLA):               │
│  ┌──────────────────────────────┐       │
│  │ TCA_KIND = "htb\0"          │       │ ← qdisc type name
│  ├──────────────────────────────┤       │
│  │ TCA_OPTIONS = nested attrs   │       │ ← qdisc parameters
│  │  ┌────────────────────────┐  │       │
│  │  │ TCA_HTB_INIT (r2q=10) │  │       │
│  │  └────────────────────────┘  │       │
│  ├──────────────────────────────┤       │
│  │ TCA_STAB = size table       │       │ ← packet sizing table
│  └──────────────────────────────┘       │
└─────────────────────────────────────────┘

Netlink Attribute format:
  ┌────────────────┬─────────────────────┐
  │  nla_len (2B)  │  nla_type (2B)      │
  ├────────────────┴─────────────────────┤
  │  data (nla_len - 4 bytes)            │
  └──────────────────────────────────────┘
```

### Python Code to Send Netlink tc Message

```python
#!/usr/bin/env python3
"""
Low-level example showing Netlink message construction for tc.
(Educational purposes — use iproute2 in production)
"""
import socket
import struct
import os

# Netlink constants
NETLINK_ROUTE = 0
RTM_NEWQDISC = 36
NLM_F_REQUEST = 0x01
NLM_F_ACK = 0x04
NLM_F_CREATE = 0x400
NLM_F_EXCL = 0x200

TCA_KIND = 1
TCA_OPTIONS = 2
TCA_UNSPEC = 0

def nlattr(attr_type, data):
    """Build a Netlink attribute."""
    if isinstance(data, str):
        data = data.encode() + b'\x00'  # null-terminated
    elif isinstance(data, int):
        data = struct.pack('I', data)
    length = 4 + len(data)
    padding = (4 - len(data) % 4) % 4
    return struct.pack('HH', length, attr_type) + data + b'\x00' * padding

def send_tc_qdisc_add(ifindex, handle, parent, kind, options=b''):
    """Send RTM_NEWQDISC netlink message."""
    sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_ROUTE)
    sock.bind((os.getpid(), 0))

    # tcmsg structure
    tcmsg = struct.pack(
        'BxxxiIII',
        socket.AF_UNSPEC,   # tcm_family
        ifindex,            # tcm_ifindex
        handle,             # tcm_handle (0x00010000 = 1:0)
        parent,             # tcm_parent (0xFFFFFFFF = root)
        0                   # tcm_info
    )

    # Attributes
    attrs = nlattr(TCA_KIND, kind)
    if options:
        attrs += nlattr(TCA_OPTIONS, options)

    # Build nlmsghdr
    payload = tcmsg + attrs
    nlhdr = struct.pack(
        'IHHII',
        16 + len(payload),                      # nlmsg_len
        RTM_NEWQDISC,                           # nlmsg_type
        NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_EXCL,
        1,                                      # seq
        os.getpid()                             # pid
    )

    sock.send(nlhdr + payload)
    response = sock.recv(4096)
    # Parse ACK/ERROR from response...
    sock.close()

# Add pfifo_fast to eth0 (ifindex=2)
# This is what 'tc qdisc add dev eth0 root pfifo_fast' does internally
send_tc_qdisc_add(
    ifindex=2,
    handle=0x00010000,      # 1:0 in MAJOR<<16|MINOR format
    parent=0xFFFFFFFF,      # TC_H_ROOT = 0xFFFFFFFF
    kind="pfifo_fast"
)
```

---

## 22. XDP and eBPF Integration with tc

### eBPF in tc Context

eBPF programs can be attached at two hook points in tc:
- **TC ingress** (clsact qdisc, ingress hook)
- **TC egress** (clsact qdisc, egress hook)

```
CLSACT QDISC — The eBPF attachment point:

              eth0
               │
  ┌────────────▼────────────────────────────────┐
  │         clsact qdisc                         │
  │                                              │
  │  INGRESS hook ──► eBPF program ──► action    │
  │  (before routing decision)                   │
  │                                              │
  │  EGRESS hook ──► eBPF program ──► action     │
  │  (after routing decision, before driver TX)  │
  └──────────────────────────────────────────────┘

DIFFERENCE FROM XDP:
  XDP = runs at NIC driver level (BEFORE sk_buff allocation)
        Extremely fast. Limited access.
  TC eBPF = runs after sk_buff allocation
            Full packet access. More powerful.
            Still faster than traditional tc filters.
```

### eBPF tc Program Example

```c
// tc_prog.c — eBPF program for tc
#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// BPF map: track per-IP byte counts
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);   // IP address
    __type(value, __u64); // byte count
} ip_stats SEC(".maps");

SEC("classifier/ingress")
int tc_ingress(struct __sk_buff *skb) {
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    // Parse Ethernet header
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    // Only process IPv4
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return TC_ACT_OK;

    // Parse IP header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_OK;

    // Track bytes per source IP
    __u32 src_ip = ip->saddr;
    __u64 *count = bpf_map_lookup_elem(&ip_stats, &src_ip);
    if (count) {
        __sync_fetch_and_add(count, skb->len);
    } else {
        __u64 initial = skb->len;
        bpf_map_update_elem(&ip_stats, &src_ip, &initial, BPF_ANY);
    }

    // Drop packets from 10.0.0.99 (example blocking)
    if (src_ip == bpf_htonl(0x0A000063)) // 10.0.0.99
        return TC_ACT_SHOT;  // DROP

    return TC_ACT_OK;  // PASS
}

// eBPF action return codes:
// TC_ACT_OK (0)         = pass packet to next stage
// TC_ACT_SHOT (2)       = drop packet
// TC_ACT_STOLEN (4)     = consume packet (no further processing)
// TC_ACT_REDIRECT (7)   = redirect to another device
// TC_ACT_TRAP (8)       = send to userspace via upcall

char __license[] SEC("license") = "GPL";
```

```bash
# Compile
clang -O2 -target bpf -c tc_prog.c -o tc_prog.o

# Attach to eth0 ingress using clsact
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf da obj tc_prog.o sec classifier/ingress

# 'da' = direct-action mode (eBPF program returns TC_ACT_* directly)
# Without 'da': return value is treated as classid (for HTB classification)

# List attached programs
tc filter show dev eth0 ingress

# Remove
tc filter del dev eth0 ingress
tc qdisc del dev eth0 clsact
```

---

## 23. Performance Analysis and Debugging

### Reading tc Statistics

```
tc -s qdisc show dev eth0

Output for HTB:
  qdisc htb 1: root refcnt 9 r2q 10 default 0x30 direct_packets_stat 0 ver 3.17
   Sent 15284700 bytes 133700 pkt (dropped 1230, overlimits 22340 requeues 0)
   backlog 45220b 30p requeues 0

FIELD EXPLANATIONS:

"Sent X bytes Y pkt"     = Total transmitted
"dropped Z"              = Packets dropped (queue full OR policed)
"overlimits N"           = Packets that hit the rate limit
                           (had to wait for tokens — this is NORMAL for shaping)
"requeues R"             = Driver rejected packet, re-added to queue
                           (SHOULD BE ZERO — indicates driver/ring issues)
"backlog Xb Yp"          = Current queue depth (bytes and packets)
                           (If persistently high → congestion)
"direct_packets_stat N"  = Packets that bypassed qdisc (fast path)
                           (High value = qdisc mostly idle)
```

```
tc -s class show dev eth0

Output:
  class htb 1:10 parent 1:1 prio 0 rate 1Mbit ceil 10Mbit burst 15Kb cburst 1500b
   Sent 5284700 bytes 43700 pkt (dropped 0, overlimits 15340 requeues 0)
   backlog 0b 0p requeues 0
   lended: 5234700 borrowed: 50000 giants: 0
   tokens: 1875000 ctokens: 18750000

"lended"       = bytes sent from own token bucket (within rate)
"borrowed"     = bytes sent using parent's tokens (above rate, up to ceil)
"giants"       = packets larger than burst — dropped!
                 (NONZERO = problem: burst too small for MTU!)
"tokens"       = current token count (main bucket)
"ctokens"      = current ceil token count
```

### Debugging Checklist

```
DEBUGGING FLOW:

Problem: Network is slow / high latency
         │
         ▼
Is it queueing delay (bufferbloat)?
  ping -f 8.8.8.8 while doing a large download.
  Normal: 5-10ms. Bufferbloat: 500ms+
  Fix: Switch to fq_codel or cake.
         │
Problem: One flow starving others
         │
         ▼
Check if using pfifo (default)?
  tc qdisc show dev eth0 | grep pfifo
  Fix: Switch to fq_codel or sfq.
         │
Problem: HTB not shaping correctly
         │
         ▼
Check "overlimits" — should be nonzero if shaping:
  tc -s class show dev eth0
  If overlimits=0 for all classes → traffic not hitting rate limit
  → Check filter classification (packets going to wrong class?)
         │
Check "dropped" — should be near zero:
  High drops = buffer overflow = burst too small or queue too short
  Fix: Increase burst or use fq_codel at leaf.
         │
Problem: "giants" nonzero:
  burst size < MTU.
  tc class change dev eth0 classid 1:10 htb rate 1mbit burst 1520
  (burst must be ≥ MTU = 1500 bytes)
```

### Using ss and ip to Correlate

```bash
# Check socket buffer sizes and TCP congestion state
ss -ti dst 8.8.8.8

# Output includes:
#   cwnd: X        — TCP congestion window
#   retrans: X/Y   — retransmissions (high = loss)
#   rtt: X/Y       — RTT and variation (jitter)
#   snd_wscale     — window scaling
#   rcvbuf, sndbuf — socket buffer sizes

# Check interface statistics
ip -s link show eth0
# Includes TX/RX bytes, packets, errors, drops, overrun

# Check NIC ring buffer size
ethtool -g eth0
# Ring parameters:
#   Pre-set maximums:
#   RX: 4096, TX: 4096
#   Current hardware settings:
#   RX: 256, TX: 256

# Increase ring buffer (reduces drops at driver level)
ethtool -G eth0 rx 4096 tx 4096
```

### Performance Impact of tc

```
PERFORMANCE COST OF tc:

Benchmark (approximate, varies by hardware):

  No qdisc (direct transmit):
    ~15 million packets/second (1Mpps = ~1Gbps of small packets)

  pfifo_fast:
    ~14 Mpps (minimal overhead)

  fq_codel:
    ~10 Mpps (hashing + CoDel overhead)

  HTB:
    ~5 Mpps (token bucket math per packet)

  HTB + complex filters:
    ~2-3 Mpps (filter matching overhead)

  eBPF classifier:
    ~12 Mpps (JIT-compiled, very fast)

OPTIMIZATION TIPS:
  1. Use eBPF instead of u32 for complex matching.
  2. Use flower (hardware-offloadable) when possible.
  3. Avoid deep class hierarchies (>3 levels).
  4. Use sfq at leaves (cheap, effective).
  5. Set txqueuelen appropriately.
  6. Use cake instead of HTB+fq_codel (integrated = faster).
```

---

## 24. Mental Models and Intuition Building

### The Five Core Abstractions

```
1. PIPE MODEL:
   Network = pipe.
   Pipe has finite capacity (bandwidth).
   If you pour more in than capacity, it overflows.
   tc manages the overflow — decides what to overflow, what to delay.

2. TOKEN BUCKET:
   Rate limiting = tokens accumulating.
   Can't send without tokens.
   Tokens accumulate up to burst (bucket size).
   This gives smooth long-term rate + burst tolerance.

3. WATERFALL (HTB HIERARCHY):
   Parent pours into child buckets.
   Children can borrow when parent has excess.
   Guaranteed floor (rate) + possible ceiling.
   Excess flows downhill (lower priority).

4. SERVICE CURVE (HFSC):
   Not "what rate" but "what service over time."
   "First 10ms at 10Mbps, then 1Mbps forever."
   Combines latency guarantee + rate guarantee.

5. SOJOURN TIME (CoDel):
   Don't measure queue LENGTH.
   Measure how long packets WAIT.
   If waiting too long → signal congestion (drop/ECN).
   Self-regulating: TCP sees drop, slows down, queue drains.
```

### Decision Tree: Which qdisc to use?

```
START: What is your goal?
           │
    ┌──────┼──────────────────────────────┐
    │      │                              │
    ▼      ▼                              ▼
FAIR   RATE LIMIT              TESTING/EMULATION
QUEUE  (shaping)
    │      │                              │
    ▼      ▼                              ▼
Single Simple rate limit?          netem
class?  └─► TBF or CAKE bandwidth
    │
    ▼
Do you need priorities?
    │
   YES → Need rate guarantees too?
    │         │
    │        YES → HTB (most common)
    │              → HFSC (if you need latency guarantees)
    │        NO  → PRIO (strict priority, no rate control)
    │
   NO → Do you need per-flow fairness?
            │
           YES → fq_codel (modern default)
                → sfq (simpler, older)
                → cake (best, if supported)
                → fq (for servers, with pacing)
            NO  → pfifo_fast (kernel default)

ADDITIONAL QUESTIONS:
  Working on a home router/ISP edge? → CAKE
  Need to ingress shape?             → IFB + above
  Need complex matching?             → u32 or eBPF filters
  Container rate limiting?           → HTB + cgroup filter
  Bufferbloat is the problem?        → Replace pfifo_fast with fq_codel or cake
```

### Cognitive Framework: Layers of Understanding

```
MASTERY LAYERS:

Layer 1 — CONCEPTUAL (What)
  "tc manages packet queues at network interfaces"
  "qdisc = algorithm for queue management"
  "HTB = hierarchical rate limiting with borrowing"

Layer 2 — OPERATIONAL (How)
  "tc qdisc add dev eth0 root handle 1: htb"
  "tc class add ... htb rate 10mbit ceil 100mbit"
  "tc filter add ... u32 match ip dport 22 0xffff flowid 1:1"

Layer 3 — MECHANICAL (Why it works)
  "Token bucket accumulates rate*time tokens"
  "HTB checks bucket before dequeue, borrows if empty"
  "CoDel measures sojourn time per packet in queue"

Layer 4 — SYSTEM THINKING (How it fits)
  "tc sits between IP stack and NIC driver"
  "Netlink RTM_NEWQDISC creates qdisc in kernel"
  "sk_buff carries classid through the stack"

Layer 5 — OPTIMIZATION (Make it fast)
  "eBPF classifiers are JIT-compiled, fastest option"
  "Avoid deep hierarchies: O(depth) per packet"
  "GSO interaction: CAKE splits GSO for accurate shaping"
```

### Problem-Solving Pattern

```
WHEN FACING A TC PROBLEM:

Step 1: IDENTIFY THE AXIS
  → Is this about RATE (too fast/slow)?
  → Or ORDERING (wrong packets going first)?
  → Or FAIRNESS (one flow eating all)?
  → Or LATENCY (bufferbloat)?

Step 2: LOCATE IN THE STACK
  → Ingress or Egress?
  → Which interface?
  → Which class/queue?

Step 3: MEASURE FIRST
  → tc -s qdisc show (drops? overlimits? backlog?)
  → ping under load (latency?)
  → ss -ti (cwnd? retrans?)

Step 4: CHOOSE THE RIGHT TOOL
  → Rate problem → TBF or HTB
  → Fairness problem → SFQ or FQ-CoDel
  → Latency problem → CoDel or CAKE
  → Ingress problem → IFB

Step 5: VERIFY
  → Measure again after change
  → Look for unintended side effects
  → Check all statistics fields
```

---

## Appendix A: Rate Units in tc

```
UNITS:
  bit   = bits per second
  kbit  = kilobits per second (1000 bit)
  mbit  = megabits per second (1000 kbit)
  gbit  = gigabits per second (1000 mbit)
  
  bps   = bytes per second
  kbps  = kilobytes per second (1000 bps)
  mbps  = megabytes per second (1000 kbps)
  
  Note: 1 mbit = 125 kbps (divide by 8 to convert)

SIZE UNITS:
  b     = bytes (NOT bits!)
  kb    = kilobytes (1000 bytes)
  mb    = megabytes
  kbit  = kilobits (used in burst size too)
  
TIME UNITS:
  s     = seconds
  ms    = milliseconds (1/1000 s)
  us    = microseconds (1/1,000,000 s)
  ns    = nanoseconds (1/1,000,000,000 s)
```

## Appendix B: Handle Arithmetic

```
HANDLE FORMAT: MAJOR:MINOR (each 16 bits, expressed in hex or decimal)

In kernel: MAJOR<<16 | MINOR (32-bit integer)

Special handles:
  TC_H_ROOT    = 0xFFFFFFFF (root of qdisc)
  TC_H_INGRESS = 0xFFFFFFF1 (ingress qdisc)
  TC_H_CLSACT  = 0xFFFFFFF1 (clsact qdisc, same value)
  TC_H_UNSPEC  = 0x00000000 (unspecified)

Convention:
  1:0   = qdisc 1 (MAJOR=1, MINOR=0 means the qdisc itself)
  1:1   = class 1 of qdisc 1
  1:10  = class 10 of qdisc 1
  ffff: = 0xFFFF:0x0000 = ingress qdisc handle

Examples:
  tc qdisc add dev eth0 root handle 1: htb
  → Creates qdisc with handle 0x00010000 (1:0)
  
  tc class add dev eth0 parent 1: classid 1:1 htb rate 10mbit
  → Creates class 0x00010001 (1:1), parent is qdisc 0x00010000
```

## Appendix C: Protocol Numbers

```
IP PROTOCOL NUMBERS (used in tc filters):
  1   = ICMP
  6   = TCP
  17  = UDP
  47  = GRE (Generic Routing Encapsulation)
  50  = ESP (IPSec Encapsulating Security Payload)
  51  = AH (IPSec Authentication Header)
  89  = OSPF
  132 = SCTP

USAGE IN tc:
  match ip protocol 6 0xff    → TCP only
  match ip protocol 17 0xff   → UDP only
  
ETHERTYPE (for protocol ip vs 802.1Q etc.):
  0x0800 = IPv4
  0x0806 = ARP
  0x86DD = IPv6
  0x8100 = 802.1Q VLAN
  0x8847 = MPLS unicast
  0x8848 = MPLS multicast
```

## Appendix D: Common tc Troubleshooting Commands

```bash
# ─── INSPECTION ───────────────────────────────────────

# Show ALL qdiscs on system
tc qdisc show

# Show ALL classes on interface with stats
tc -s class show dev eth0

# Show ALL filters with details
tc -d filter show dev eth0 parent 1:

# Show ingress filters
tc filter show dev eth0 parent ffff:

# Monitor qdisc stats live
watch -n 0.5 'tc -s qdisc show dev eth0'

# JSON output for parsing
tc -j qdisc show dev eth0

# ─── TESTING ──────────────────────────────────────────

# Test bandwidth (needs iperf3)
iperf3 -s &
iperf3 -c SERVER -t 30 -P 4   # 4 parallel streams

# Test latency under load
ping -i 0.01 8.8.8.8 &
iperf3 -c SERVER -t 30
kill %1
# Compare ping with/without load

# Test with netem (simulate bad network on loopback)
tc qdisc add dev lo root netem delay 100ms
ping -c 5 127.0.0.1   # should show ~100ms RTT
tc qdisc del dev lo root

# ─── RESET ────────────────────────────────────────────

# Remove all tc config from interface
tc qdisc del dev eth0 root
tc qdisc del dev eth0 ingress

# Check kernel default after reset
tc qdisc show dev eth0
# Should show: qdisc pfifo_fast ...

# ─── DEBUGGING SPECIFIC ISSUES ────────────────────────

# Check if HTB is classifying correctly (watch class stats change)
watch -n 1 'tc -s class show dev eth0'
# Generate some traffic and see which class counters increase

# Check filter matches (trace with iptables logging)
iptables -t mangle -A OUTPUT -p tcp --dport 22 -j LOG --log-prefix "SSH: "
# Then check dmesg or journalctl for SSH packets

# Check current qdisc on all interfaces
for dev in $(ip link show | awk -F: '/^[0-9]/{print $2}'); do
    echo "=== $dev ==="
    tc qdisc show dev $dev
done
```

---

*This guide covers the complete Linux tc subsystem from first principles to
kernel internals. Master each section sequentially — the concepts build on
each other like a mathematical proof. The true expert knows not just HOW to
configure tc, but WHY each algorithm behaves as it does under every condition.*

*"The difference between a good engineer and a great one is whether they can
predict the behavior of a system they've never seen before." — Mental model
over memorization, always.*

