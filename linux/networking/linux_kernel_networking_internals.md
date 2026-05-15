# Linux Kernel Networking Internals: A Complete Deep-Dive

> Covering: sk_buff mechanics, layer traversal (L2→L7), pointer semantics, fragmentation, reassembly,
> retransmission, flag processing, NAPI, GRO/GSO, and C + Rust implementations.

---

## Table of Contents

1. [The Central Abstraction: `sk_buff`](#1-the-central-abstraction-sk_buff)
2. [Memory Layout and Pointer Arithmetic](#2-memory-layout-and-pointer-arithmetic)
3. [Pass by Reference or Value? The Real Answer](#3-pass-by-reference-or-value-the-real-answer)
4. [The Receive Path: Frame to Socket (L2 → L7)](#4-the-receive-path-frame-to-socket-l2--l7)
5. [The Transmit Path: Socket to Wire (L7 → L2)](#5-the-transmit-path-socket-to-wire-l7--l2)
6. [How Each Layer "Sees" the Data (skb_pull / skb_push)](#6-how-each-layer-sees-the-data-skb_pull--skb_push)
7. [IP Fragmentation: How It Works](#7-ip-fragmentation-how-it-works)
8. [IP Reassembly: How It Works](#8-ip-reassembly-how-it-works)
9. [TCP Segmentation and the TCP State Machine](#9-tcp-segmentation-and-the-tcp-state-machine)
10. [Who Asks for Retransmission? TCP Reliability Mechanisms](#10-who-asks-for-retransmission-tcp-reliability-mechanisms)
11. [TCP Flags: Every Flag, Every Operation](#11-tcp-flags-every-flag-every-operation)
12. [NAPI: Interrupt Coalescing and Polling](#12-napi-interrupt-coalescing-and-polling)
13. [GRO and GSO: Batching at Scale](#13-gro-and-gso-batching-at-scale)
14. [Netfilter Hooks: Where iptables Lives](#14-netfilter-hooks-where-iptables-lives)
15. [The Socket Buffer Queue: sk_receive_queue and sk_write_queue](#15-the-socket-buffer-queue-sk_receive_queue-and-sk_write_queue)
16. [C Implementation Patterns](#16-c-implementation-patterns)
17. [Rust: Safe Abstractions Over the Same Concepts](#17-rust-safe-abstractions-over-the-same-concepts)
18. [Complete Mental Model: End-to-End ASCII Walkthrough](#18-complete-mental-model-end-to-end-ascii-walkthrough)

---

## 1. The Central Abstraction: `sk_buff`

Every packet, at every layer, in every direction, is represented by a single C struct:
`struct sk_buff` — abbreviated `skb`. It lives in `include/linux/skbuff.h` and is the
single most important data structure in the Linux networking stack.

```
                        sk_buff (the "skb")
┌──────────────────────────────────────────────────────────────────┐
│  struct sk_buff {                                                │
│    /* Linked list / queue membership */                          │
│    struct sk_buff        *next, *prev;                           │
│    struct sk_buff_head   *list;                                  │
│                                                                  │
│    /* Device this skb arrived on / is going out of */           │
│    struct net_device     *dev;                                   │
│                                                                  │
│    /* Socket that owns this skb (rx path, TCP) */               │
│    struct sock           *sk;                                    │
│                                                                  │
│    /* Timestamps */                                              │
│    ktime_t               tstamp;                                 │
│                                                                  │
│    /* ── THE FOUR CRITICAL POINTERS ── */                        │
│    unsigned char         *head;   /* start of allocated buffer */│
│    unsigned char         *data;   /* start of current payload  */│
│    unsigned char         *tail;   /* end   of current payload  */│
│    unsigned char         *end;    /* end   of allocated buffer */│
│                                                                  │
│    /* Length of current payload (tail - data) */                │
│    unsigned int           len;                                   │
│    unsigned int           data_len; /* bytes in frag list       */│
│                                                                  │
│    /* Header pointers (set as headers are parsed) */            │
│    union { struct ethhdr *ethernet; ... } mac_header;           │
│    union { struct iphdr  *ip4;       ... } network_header;      │
│    union { struct tcphdr *tcp; ...   } transport_header;        │
│                                                                  │
│    /* Protocol at this layer (ETH_P_IP, ETH_P_IPV6, ...) */    │
│    __be16                 protocol;                              │
│                                                                  │
│    /* IP fragment / reassembly fields */                        │
│    __u32                  hash;                                  │
│                                                                  │
│    /* Shared data reference count */                            │
│    atomic_t               users;                                 │
│                                                                  │
│    /* Fragmentation list (for non-linear skbs) */               │
│    skb_frag_t             frags[MAX_SKB_FRAGS];                  │
│    struct sk_buff         *frag_list;                            │
│                                                                  │
│    /* Checksum info, GSO info, mark, priority ... */            │
│    __wsum                 csum;                                  │
│    __u32                  priority;                              │
│    __u8                   ip_summed;                             │
│    __u16                  gso_size;                              │
│    __u16                  gso_segs;                              │
│  }                                                               │
└──────────────────────────────────────────────────────────────────┘
```

### Why one struct for all layers?

The kernel does NOT copy data up through layers. It reuses the **same skb** across all layers.
Each layer simply moves the `data` pointer forward (stripping its own header) or backward
(prepending its own header on transmit). This is the foundational design decision.

---

## 2. Memory Layout and Pointer Arithmetic

The actual packet bytes live in a contiguous region of memory called the **linear data area**.
The four pointers (`head`, `data`, `tail`, `end`) carve that region into zones:

```
Physical memory (one contiguous kmalloc'd region):

 head                    data          tail                    end
  │                       │              │                      │
  ▼                       ▼              ▼                      ▼
  ┌───────────────────────┬──────────────┬──────────────────────┐
  │    headroom           │   payload    │      tailroom        │
  │  (reserved for        │  (current    │  (space to grow      │
  │   prepending hdrs)    │   headers    │   tail, e.g. CRC)    │
  │                       │   + data)    │                      │
  └───────────────────────┴──────────────┴──────────────────────┘

  skb->len = tail - data    (current meaningful bytes)
  skb_headroom(skb) = data - head  (free space before data)
  skb_tailroom(skb) = end  - tail  (free space after data)
```

### Non-linear (paged) data

For large payloads (e.g., TCP receiving 64KB), not all bytes fit in the linear area.
The kernel uses a **fragment array** (`skb->frags[]`) pointing into `struct page` objects,
and a `frag_list` chaining additional `sk_buff`s. `skb->data_len` tracks bytes
sitting outside the linear area.

```
  Linear area (skb->data ... skb->tail):
  ┌──────────────────────────────┐
  │  ETH + IP + TCP headers      │  ← always linear for fast access
  └──────────────────────────────┘
           │
           ▼
  skb->frags[0] ──► page frame (4KB)   ┐
  skb->frags[1] ──► page frame (4KB)   │  actual TCP payload
  skb->frags[2] ──► page frame (4KB)   ┘
           │
  skb->frag_list ──► sk_buff ──► sk_buff ──► NULL
                     (used for IP reassembly chains)
```

---

## 3. Pass by Reference or Value? The Real Answer

### The definitive answer: **always pointer (reference)**

Every function in the networking stack receives `struct sk_buff *skb` — a pointer.
The `sk_buff` struct itself is never copied when passed between layers.
The **payload bytes** are also never copied — all layers work on the same physical bytes.

```c
// How the Ethernet layer calls the IP layer:
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev);

// How IP calls TCP:
int tcp_v4_rcv(struct sk_buff *skb);

// How TCP calls the socket layer:
int tcp_queue_rcv(struct sock *sk, struct sk_buff *skb, int hdrlen, bool *fragstolen);
```

**The pointer is passed by value** (the pointer address is copied onto the stack),
but it points to the same `sk_buff` and the same underlying bytes.

### Reference counting and ownership

When a packet must go to multiple consumers (e.g., a promiscuous tap AND the normal stack),
the kernel calls `skb_clone()` or `skb_copy()`:

- `skb_clone()`: allocates a new `sk_buff` struct but **shares the data buffer** via
  `skb->users` reference count. Headers can diverge; payload is shared (copy-on-write).
- `skb_copy()`: full deep copy — new struct AND new data buffer.
- `skb_get(skb)`: increments `skb->users` refcount.
- `kfree_skb(skb)` / `consume_skb(skb)`: decrements refcount; frees when zero.

```c
// Reference count lifecycle:
struct sk_buff *skb = alloc_skb(size, GFP_ATOMIC); // users = 1
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC); // both point to same data; users=2

kfree_skb(clone);  // users=1, data still alive
kfree_skb(skb);    // users=0, data freed
```

### Why not copy?

Copying would be O(n) in packet size at every layer. With 10Gbps traffic you have
~14 million packets/second. Even a single extra memcpy per packet would dominate CPU.
The pointer-threading design keeps layer transitions O(1).

---

## 4. The Receive Path: Frame to Socket (L2 → L7)

### 4.1 Hardware interrupt and DMA

```
NIC Hardware
    │
    │  DMA transfer: NIC writes packet bytes directly to RAM
    │  into a pre-allocated ring buffer (RX ring).
    ▼
CPU receives hardware interrupt (IRQ)
    │
    │  net_interrupt() or equivalent driver ISR fires
    ▼
Driver ISR
    │  - Acknowledges interrupt to NIC
    │  - Schedules NAPI poll (disables IRQ for that NIC)
    │  - calls napi_schedule(&adapter->napi)
    ▼
ksoftirqd / NET_RX_SOFTIRQ
    │
    │  net_rx_action() runs — the main RX softirq handler
    ▼
NAPI poll: driver->poll() called (e.g., igb_poll, ixgbe_clean_rx_irq)
    │
    │  For each descriptor in RX ring:
    │    1. Build sk_buff from DMA'd bytes
    │    2. skb->data points to raw frame bytes
    │    3. Call netif_receive_skb(skb)
    ▼
```

### 4.2 Layer 2: Ethernet frame handler

```
netif_receive_skb(skb)
    │
    │  __netif_receive_skb()
    │    - Runs packet taps (AF_PACKET sockets, tcpdump hooks here)
    │    - Runs ingress tc (traffic control) hooks
    │    - Checks skb->protocol to decide which L3 handler to call
    │
    │  deliver_skb(skb, pt_prev, orig_dev)
    │    - calls pt->func(skb, dev, pt, orig_dev)
    │    - For IPv4: protocol = ETH_P_IP → calls ip_rcv()
    │    - For IPv6: protocol = ETH_P_IPV6 → calls ipv6_rcv()
    │    - For ARP:  protocol = ETH_P_ARP  → calls arp_rcv()
    ▼
```

At this point:
- `skb->mac_header` is set to the Ethernet header offset
- `skb->data` still points at the Ethernet header start
- `skb->protocol` is set to the EtherType

### 4.3 Layer 3: IP handler

```c
// net/ipv4/ip_input.c
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    struct iphdr *iph;
    u32 len;

    /* skb_share_check: if shared, make a private copy */
    skb = skb_share_check(skb, GFP_ATOMIC);

    /* Verify we have at least sizeof(iphdr) bytes */
    if (!pskb_may_pull(skb, sizeof(struct iphdr)))
        goto inhdr_error;

    iph = ip_hdr(skb);          // = (struct iphdr*)skb->network_header

    /* Validate IP version, header length, total length */
    if (iph->ihl < 5 || iph->version != 4)
        goto inhdr_error;

    len = ntohs(iph->tot_len);

    /* Pull IP header off — advances skb->data past IP header */
    /* skb->transport_header now points to TCP/UDP/ICMP */

    /* Netfilter PRE_ROUTING hook — iptables can DROP here */
    return NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING,
                   net, NULL, skb, dev, NULL, ip_rcv_finish);
}
```

Inside `ip_rcv_finish()`:

```
ip_rcv_finish(skb)
    │
    ├── Is this packet for us? (ip_route_input_noref)
    │     Routes lookup in FIB (Forwarding Information Base)
    │     Result stored in skb->_skb_refdst (dst_entry)
    │
    ├── Fragment? (iph->frag_off & IP_MF || iph->frag_off & IP_OFFSET)
    │     YES → ip_defrag(skb)  [see Section 8]
    │     NO  → continue
    │
    └── Dispatch to L4:
          ip_local_deliver_finish()
            │
            ├── iph->protocol == IPPROTO_TCP  → tcp_v4_rcv(skb)
            ├── iph->protocol == IPPROTO_UDP  → udp_rcv(skb)
            ├── iph->protocol == IPPROTO_ICMP → icmp_rcv(skb)
            └── iph->protocol == IPPROTO_SCTP → sctp_rcv(skb)
```

At this transition:
- `skb_pull(skb, ip_hdrlen(skb))` is called (or the equivalent via `skb->data` adjustment)
- `skb->network_header` was set at the IP header start
- Now `skb->data` advances to the transport header

### 4.4 Layer 4: TCP handler

```c
// net/ipv4/tcp_ipv4.c
int tcp_v4_rcv(struct sk_buff *skb)
{
    const struct iphdr *iph;
    const struct tcphdr *th;
    struct sock *sk;
    int ret;

    /* Need at least TCP fixed header */
    if (skb->pkt_type != PACKET_HOST)
        goto discard_it;

    if (!pskb_may_pull(skb, sizeof(struct tcphdr)))
        goto discard_it;

    th = (const struct tcphdr *)skb->data;  // transport header

    if (th->doff < sizeof(struct tcphdr) / 4)
        goto bad_packet;

    if (!pskb_may_pull(skb, th->doff * 4))
        goto discard_it;

    /* Verify TCP checksum */
    if (skb_checksum_init(skb, IPPROTO_TCP, inet_compute_pseudo))
        goto csum_error;

    iph = ip_hdr(skb);  // still accessible via skb->network_header

    /* Find the socket: 4-tuple lookup (src_ip, src_port, dst_ip, dst_port) */
    sk = __inet_lookup_skb(&tcp_hashinfo, skb,
                           __tcp_hdrlen(th), th->source, th->dest,
                           sdif, &refcounted);
    if (!sk)
        goto no_tcp_socket;

    /* Hand off to the TCP state machine */
    ret = tcp_v4_do_rcv(sk, skb);
    ...
}
```

Inside `tcp_v4_do_rcv()`:

```
tcp_v4_do_rcv(sk, skb)
    │
    ├── sk->sk_state == TCP_ESTABLISHED (fast path)
    │     tcp_rcv_established(sk, skb)
    │       ├── Process ACK number: advance send window
    │       ├── Add payload to receive queue:
    │       │     tcp_queue_rcv() → __skb_queue_tail(&sk->sk_receive_queue, skb)
    │       ├── Update sequence numbers
    │       ├── Send ACK if needed (tcp_send_ack)
    │       └── Wake up userspace: sk->sk_data_ready(sk) → socket readable
    │
    └── Other states (SYN_SENT, SYN_RECV, CLOSE_WAIT, ...)
          tcp_rcv_state_process(sk, skb)
```

### 4.5 Layer 5–7: Socket → Userspace

```
Userspace process calls:
  recv(fd, buf, len, 0)
      │
      ▼
  sys_recvfrom()  [syscall entry]
      │
      ▼
  sock_recvmsg()
      │
      ▼
  inet_recvmsg()
      │
      ▼
  tcp_recvmsg(sk, msg, len, flags, addr_len)
      │
      │  Locks the socket
      │  Loops over sk->sk_receive_queue:
      │    skb = skb_peek(&sk->sk_receive_queue)
      │    skb_copy_datagram_msg(skb, offset, msg, used)
      │      → copies bytes from skb into user-space iovec
      │    If skb fully consumed: __skb_unlink + kfree_skb
      │    Advances sk->copied_seq
      ▼
  Returns to userspace with bytes copied
```

**Key insight**: The actual copy from kernel to user space happens **once** — in `tcp_recvmsg`.
All layer transitions before that operate on the same physical bytes via pointer manipulation.

---

## 5. The Transmit Path: Socket to Wire (L7 → L2)

```
Userspace:  send(fd, buf, len, 0)
                │
                ▼
            sys_sendto() → sock_sendmsg() → inet_sendmsg() → tcp_sendmsg()

tcp_sendmsg():
    │
    │  Copies user bytes into sk_buff(s) allocated from sk->sk_sndbuf
    │  (this is the ONE kernel copy on transmit path)
    │  Adds skb to sk->sk_write_queue
    │
    ▼
tcp_push() → __tcp_push_pending_frames() → tcp_write_xmit()
    │
    │  For each skb ready to send (within cwnd and send window):
    │    tcp_transmit_skb(sk, skb, clone_it, gfp)
    │      - Prepends TCP header: skb_push(skb, tcp_header_size)
    │      - Fills struct tcphdr (seq, ack, flags, window, checksum)
    │      - Sets skb->transport_header
    ▼
ip_queue_xmit(sk, skb, &inet->cork.fl)   [or ip_local_out]
    │
    │  Route lookup → dst_entry
    │  Prepends IP header: skb_push(skb, sizeof(struct iphdr))
    │  Fills struct iphdr (version, ihl, tot_len, id, ttl, protocol, checksum)
    │  Sets skb->network_header
    │  Netfilter LOCAL_OUT hook (iptables OUTPUT chain)
    │  ip_output() → ip_finish_output()
    │
    │  Fragment if needed? (skb->len > mtu)
    │    YES → ip_fragment(skb, ip_finish_output2)
    │    NO  → ip_finish_output2(skb)
    ▼
ip_finish_output2(skb)
    │
    │  ARP lookup for next-hop MAC
    │  Prepends Ethernet header: skb_push(skb, ETH_HLEN)
    │  Fills struct ethhdr (dst_mac, src_mac, ethertype)
    │  Sets skb->mac_header
    ▼
dev_queue_xmit(skb)
    │
    │  Traffic control (tc) qdisc
    │  qdisc->enqueue(skb, qdisc)
    │  qdisc->dequeue() → skb handed to driver
    ▼
driver->ndo_start_xmit(skb, dev)   [e.g., igb_xmit_frame]
    │
    │  Maps skb data to DMA addresses
    │  Writes TX descriptors to NIC ring buffer
    │  Rings NIC doorbell register
    ▼
NIC hardware: DMA reads from RAM, sends on wire
    │
    (TX completion interrupt fires later)
    │
    ▼
Driver TX completion: kfree_skb(skb) [decrements refcount → frees if 0]
```

---

## 6. How Each Layer "Sees" the Data (skb_pull / skb_push)

This is the core mechanism by which a single buffer appears as a different "view"
to each layer without any copying.

### On receive (consuming headers):

```
After DMA — raw Ethernet frame in buffer:
┌──────┬──────────┬──────────┬─────────────────────────────┐
│      │  ETH hdr │  IP hdr  │  TCP hdr │  TCP payload     │
│head  │  14 B    │  20 B    │  20 B    │  N bytes         │
└──────┴──────────┴──────────┴─────────────────────────────┘
        ▲
        skb->data (L2 view: data points at ETH header)

After skb_pull(skb, ETH_HLEN) in eth layer:
┌──────┬──────────┬──────────┬─────────────────────────────┐
│      │  ETH hdr │  IP hdr  │  TCP hdr │  TCP payload     │
└──────┴──────────┴──────────┴─────────────────────────────┘
                   ▲
                   skb->data (L3 view: data points at IP header)
                   skb->mac_header saved pointing at ETH

After skb_pull(skb, ip_hdrlen) in IP layer:
┌──────┬──────────┬──────────┬─────────────────────────────┐
│      │  ETH hdr │  IP hdr  │  TCP hdr │  TCP payload     │
└──────┴──────────┴──────────┴─────────────────────────────┘
                              ▲
                              skb->data (L4 view)
                              skb->network_header saved at IP

After skb_pull(skb, tcp_hdrlen) in TCP layer:
┌──────┬──────────┬──────────┬─────────────────────────────┐
│      │  ETH hdr │  IP hdr  │  TCP hdr │  TCP payload     │
└──────┴──────────┴──────────┴─────────────────────────────┘
                                          ▲
                                          skb->data (app view)
                                          skb->transport_header at TCP
```

**Note**: The old headers are NOT erased. They remain in the headroom.
`skb->mac_header`, `skb->network_header`, `skb->transport_header` are **offsets**
from `skb->head`, not from `skb->data`. So any layer can re-examine any header at any time:

```c
// Access IP header from TCP layer:
struct iphdr *iph = ip_hdr(skb);
// expands to: (struct iphdr*)(skb->head + skb->network_header)
// Works regardless of where skb->data currently is.
```

### On transmit (prepending headers):

```c
// TCP prepends its header:
skb_push(skb, tcp_header_size);   // moves skb->data BACKWARD
th = (struct tcphdr *)skb->data;
// fill TCP header fields

// IP prepends its header:
skb_push(skb, sizeof(struct iphdr));
iph = (struct iphdr *)skb->data;
// fill IP header fields

// Ethernet prepends its header:
skb_push(skb, ETH_HLEN);
eth = (struct ethhdr *)skb->data;
// fill ETH header fields
```

```
Start (just payload):
┌──────────────────────┬──────────────────────┐
│  headroom reserved   │  TCP payload         │
└──────────────────────┴──────────────────────┘
                        ▲ skb->data

After skb_push for TCP:
┌────────────┬──────────┬──────────────────────┐
│  headroom  │  TCP hdr │  TCP payload         │
└────────────┴──────────┴──────────────────────┘
              ▲ skb->data

After skb_push for IP:
┌──────┬──────────┬──────────┬──────────────────────┐
│ head │  IP hdr  │  TCP hdr │  TCP payload         │
└──────┴──────────┴──────────┴──────────────────────┘
        ▲ skb->data

After skb_push for ETH:
┌──────────┬──────────┬──────────┬──────────────────────┐
│ ETH hdr  │  IP hdr  │  TCP hdr │  TCP payload         │
└──────────┴──────────┴──────────┴──────────────────────┘
▲ skb->data (head == data now, headroom exhausted)
```

### Key functions:

```c
// Advance data pointer forward (strip header on RX)
unsigned char *skb_pull(struct sk_buff *skb, unsigned int len);
// skb->data += len; skb->len -= len; returns new skb->data

// Move data pointer backward (prepend header on TX)
unsigned char *skb_push(struct sk_buff *skb, unsigned int len);
// skb->data -= len; skb->len += len; returns new skb->data

// Advance tail pointer (grow payload)
unsigned char *skb_put(struct sk_buff *skb, unsigned int len);
// skb->tail += len; skb->len += len;

// Ensure N bytes are in linear area (may realloc/copy from frags)
int pskb_may_pull(struct sk_buff *skb, unsigned int len);

// Header access macros (offset from head, not data):
#define eth_hdr(skb)    ((struct ethhdr *)skb_mac_header(skb))
#define ip_hdr(skb)     ((struct iphdr *)skb_network_header(skb))
#define tcp_hdr(skb)    ((struct tcphdr *)skb_transport_header(skb))
```

---

## 7. IP Fragmentation: How It Works

### Why fragmentation exists

Every network link has an **MTU** (Maximum Transmission Unit). Ethernet's MTU is typically
1500 bytes. An IP packet can be up to 65,535 bytes. When a packet larger than the MTU
must traverse a link, it must be split into **fragments**.

### Fragmentation fields in the IP header

```
IPv4 Header (20 bytes minimum):
┌────────────────────────────────────────────────────────────┐
│ Vers│ IHL│  DSCP/ECN  │           Total Length             │
├────────────────────────────────────────────────────────────┤
│         Identification (16 bits)  │Flags│  Frag Offset     │
│                                   │DF MF│   (13 bits)      │
├────────────────────────────────────────────────────────────┤
│  TTL  │  Protocol  │            Header Checksum            │
├────────────────────────────────────────────────────────────┤
│                     Source IP Address                      │
├────────────────────────────────────────────────────────────┤
│                  Destination IP Address                    │
└────────────────────────────────────────────────────────────┘

Flags (3 bits):
  Bit 0: Reserved (must be 0)
  Bit 1: DF (Don't Fragment) — if set, router must drop+ICMP if too big
  Bit 2: MF (More Fragments) — if set, more fragments follow

Fragment Offset (13 bits):
  Offset in 8-byte units from start of original IP payload
  (so max offset = 2^13 * 8 = 65,536 bytes → covers max IP packet)
```

### Fragmentation on transmit: `ip_fragment()`

```c
// net/ipv4/ip_output.c
int ip_do_fragment(struct net *net, struct sock *sk,
                   struct sk_buff *skb,
                   int (*output)(struct net *, struct sock *, struct sk_buff *))
{
    struct iphdr *iph = ip_hdr(skb);
    int mtu = ip_skb_dst_mtu(sk, skb);
    /* mtu minus IP header = max payload bytes per fragment */
    int hlen = iph->ihl * 4;
    int left = skb->len - hlen;   /* total payload bytes to fragment */
    int len = (mtu - hlen) & ~7;  /* max payload per frag, mult of 8 */
    int offset = (ntohs(iph->frag_off) & IP_OFFSET) << 3;
    __be16 not_last_frag;

    while (left > 0) {
        struct sk_buff *skb2;
        int copy = min(left, len);

        /* Allocate new skb for this fragment */
        skb2 = alloc_skb(copy + hlen + LL_RESERVED_SPACE(rt->dst.dev),
                         GFP_ATOMIC);

        /* Copy IP header into new fragment */
        skb_reserve(skb2, LL_RESERVED_SPACE(rt->dst.dev));
        skb_put(skb2, copy + hlen);
        skb2->transport_header = skb2->network_header + hlen;
        memcpy(skb_network_header(skb2), iph, hlen);

        /* Copy payload slice */
        skb_copy_bits(skb, hlen + (offset - orig_offset),
                      skb_transport_header(skb2), copy);

        /* Set fragment fields */
        iph2 = ip_hdr(skb2);
        iph2->tot_len = htons(copy + hlen);
        iph2->frag_off = htons((offset >> 3));
        if (left > copy)
            iph2->frag_off |= htons(IP_MF);  // More Fragments
        /* Identification stays same as original */
        ip_send_check(iph2);  // recompute checksum

        offset += copy;
        left   -= copy;

        /* Send this fragment */
        output(net, sk, skb2);
    }
}
```

### Fragmentation example: 4000-byte UDP packet, MTU=1500

```
Original IP packet (4000 bytes total, 3980 bytes payload):
┌──────────────────────────────────────────────────┐
│ IP hdr (20B) │ UDP hdr (8B) │  UDP data (3972B)  │
│ ID=0x1234    │              │                    │
│ MF=0, off=0  │              │                    │
└──────────────────────────────────────────────────┘

After fragmentation (MTU=1500, max payload=1480B, must be mult of 8=1480):

Fragment 1: offset=0, MF=1
┌─────────────────────────────────────────────┐
│ IP hdr (20B) │ UDP hdr (8B) │  data (1472B) │
│ ID=0x1234    │              │               │
│ MF=1, off=0  │              │               │  total=1500
└─────────────────────────────────────────────┘
  (UDP header only in first fragment)

Fragment 2: offset=185 (185*8=1480), MF=1
┌─────────────────────────────────────────────┐
│ IP hdr (20B) │  data (1480B)                │
│ ID=0x1234    │                              │
│ MF=1,off=185 │                              │  total=1500
└─────────────────────────────────────────────┘

Fragment 3: offset=370 (370*8=2960), MF=0
┌─────────────────────────────────────────────┐
│ IP hdr (20B) │  data (1020B)                │
│ ID=0x1234    │                              │
│ MF=0,off=370 │                              │  total=1040
└─────────────────────────────────────────────┘

3972 = 1472 + 1480 + 1020 ✓
```

### PMTUD (Path MTU Discovery)

Modern systems avoid fragmentation using **PMTUD**: set DF=1 on all packets.
If a router's link has a smaller MTU, it drops the packet and sends back:
`ICMP Type=3, Code=4 (Fragmentation Needed, DF set)` with the next-hop MTU.
The sender reduces its effective MSS and retransmits.

---

## 8. IP Reassembly: How It Works

Reassembly is handled by `ip_defrag()` in `net/ipv4/ip_fragment.c`.
The **receiver** is responsible for reassembly, not the router.

### Data structures

```c
// The reassembly queue for one fragmented datagram:
struct ipq {
    struct inet_frag_queue q;  // generic frag queue
    // q contains:
    //   struct sk_buff *fragments;  // linked list of received frags
    //   struct sk_buff *fragments_tail;
    //   int             len;        // total bytes received so far
    //   int             meat;       // confirmed bytes (no holes)
    //   unsigned long   timeout;    // reassembly timer

    /* The 4-tuple key identifying THIS datagram: */
    __be32  saddr;
    __be32  daddr;
    __be16  id;         // IP identification field
    u8      protocol;   // IPPROTO_TCP, etc.
};
```

### Reassembly algorithm

```
ip_defrag(net, skb, user)
    │
    │  Extract key: (src_ip, dst_ip, ip_id, protocol)
    │
    ├── Look up or create ipq in reassembly hash table
    │     ip_find(net, iph, user, vif)
    │     Key = (saddr, daddr, id, protocol)
    │
    ├── Add this fragment to the ipq's fragment list:
    │     ip_frag_queue(qp, skb)
    │       │
    │       │  Maintain sorted list by offset
    │       │  Handle overlapping fragments (discard overlap)
    │       │  Update qp->q.meat (bytes accounted for)
    │       │  Check: is qp->q.meat == qp->q.len?
    │       │    YES → all fragments received → reassemble
    │
    ├── If not complete: store and return -EINPROGRESS
    │     (skb is consumed, original caller gets NULL back)
    │
    └── If complete: ip_frag_reasm(qp, prev_tail, dev)
          │
          │  Allocate new sk_buff large enough for entire datagram
          │  Walk fragment list, copy each fragment's payload
          │  (OR: use skb frag_list to avoid copying)
          │  Reconstruct full IP header (MF=0, offset=0)
          │  Free ipq
          │
          └── Return reassembled skb to ip_rcv_finish()
```

### The reassembly timer

```c
// If reassembly isn't complete within this timeout, all fragments are dropped:
#define IP_FRAG_TIME    (30 * HZ)   // 30 seconds

// When timer fires:
ip_expire(unsigned long arg) {
    // Sends ICMP "Fragment Reassembly Time Exceeded" to sender
    icmp_send(qp->q.fragments, ICMP_TIME_EXCEEDED,
              ICMP_EXC_FRAGTIME, 0);
    // Drops all fragments
    ipq_destroy(qp);
}
```

### Fragment reassembly illustrated

```
Time →

t=0:  Fragment 2 arrives (offset=1480, MF=1)
      ipq created, frag inserted
      Fragment list: [off=1480, 1480B]
      meat=1480, len=? (don't know yet — haven't seen last frag)

t=1:  Fragment 1 arrives (offset=0, MF=1)
      frag inserted at head
      Fragment list: [off=0, 1480B] → [off=1480, 1480B]
      meat=2960

t=2:  Fragment 3 arrives (offset=2960, MF=0)
      NOW we know total len = 2960 + frag3_payload_len
      frag inserted
      Fragment list: [off=0] → [off=1480] → [off=2960]
      meat == len → COMPLETE

      ip_frag_reasm() called:
      ┌──────────────────────────────────────────┐
      │ IP hdr │ frag1_data │ frag2_data │ frag3 │
      │ MF=0   │            │            │       │
      │ off=0  │            │            │       │
      └──────────────────────────────────────────┘
      → handed to tcp_v4_rcv() or udp_rcv()
```

### Overlap and security

The kernel handles **overlapping fragments** (a common attack vector — "Teardrop", "Rose")
by discarding the overlapping portion. RFC 5722 mandates that overlapping IPv6 fragments
be rejected entirely. Linux does this via offset/length tracking in the fragment queue.

---

## 9. TCP Segmentation and the TCP State Machine

### Segmentation on transmit

TCP takes an arbitrarily large stream from userspace and segments it.
The maximum segment size is negotiated during the SYN handshake (**MSS option**).

```
MSS = MTU - IP_header - TCP_header
    = 1500 - 20 - 20 = 1460 bytes  (typical Ethernet)

With options (timestamps, SACK): MSS may be reduced to ~1448 bytes.
```

### The TCP sequence number space

```
┌──────────────────────────────────────────────────────────┐
│              Send Sequence Space (RFC 793)               │
│                                                          │
│  SND.UNA      SND.NXT         SND.UNA + SND.WND         │
│    │            │                    │                   │
│    ▼            ▼                    ▼                   │
│────●────────────●────────────────────●────────────       │
│    │sent but    │ can send           │ cannot send       │
│    │unACK'd     │ (within window)    │ (window limit)    │
│    │            │                    │                   │
│  oldest        next byte            send window          │
│  unACK'd       to send              edge                 │
│  segment                                                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│             Receive Sequence Space                        │
│                                                          │
│  RCV.NXT                    RCV.NXT + RCV.WND            │
│    │                              │                      │
│    ▼                              ▼                      │
│────●──────────────────────────────●────────────          │
│    │ expected next byte           │ window edge          │
│    │ (cumulative ACK position)    │                      │
└──────────────────────────────────────────────────────────┘
```

### TCP state machine (full)

```
                    CLOSED
                      │
          active open │ passive open
          (connect()) │ (listen())
                      │
            ┌─────────┴──────────┐
            ▼                    ▼
         SYN_SENT            LISTEN
            │                    │
   SYN+ACK  │           SYN rcv  │
   received │                    ▼
            │              SYN_RECEIVED
            │                    │
    ACK sent│           ACK rcv  │
            │                    │
            ├────────────────────┘
            ▼
        ESTABLISHED  ◄─── normal data exchange ───►
            │
            │ (active close: close())
            │ FIN sent
            ▼
         FIN_WAIT_1
            │
            │ ACK of FIN received
            ▼
         FIN_WAIT_2
            │
            │ FIN received from peer
            ▼
          TIME_WAIT  ────► (2*MSL timer expires)
            │
            ▼
          CLOSED

  (passive close path):
  ESTABLISHED → CLOSE_WAIT (FIN received, ACK sent)
              → LAST_ACK   (our FIN sent)
              → CLOSED     (ACK of our FIN received)
```

---

## 10. Who Asks for Retransmission? TCP Reliability Mechanisms

**UDP has no reliability mechanism at all.** Fragmentation at the IP layer is the
network layer's only "help", and even that just delivers individual fragments —
if any IP fragment is lost, the entire datagram is lost (reassembly timer expires).

**TCP** is entirely responsible for its own reliability. There is no lower-layer
mechanism asking for retransmission. TCP does it all.

### 10.1 The Retransmission Timer (RTO)

When TCP sends a segment, it starts a **retransmission timer**. If no ACK arrives
before the timer expires, TCP retransmits the oldest unACKed segment.

```c
// tcp_retransmit_timer() in net/ipv4/tcp_timer.c
// Called when rto_timer fires:
void tcp_retransmit_timer(struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);

    if (!tp->packets_out)
        return;  // nothing to retransmit

    // Exponential backoff:
    tp->backoff++;
    // RTO doubles each retry: RTO = min(RTO * 2, TCP_RTO_MAX)
    // TCP_RTO_MAX = 120 seconds

    // Retransmit oldest unACKed segment:
    tcp_retransmit_skb(sk, tcp_write_queue_head(sk), 1);

    // Congestion response: set ssthresh, reset cwnd
    tcp_enter_loss(sk);
}
```

**RTO calculation (RFC 6298)**:

```
RTT sample obtained from ACK timing:
  RTTVAR = (1 - beta) * RTTVAR + beta * |SRTT - RTT|   beta=0.25
  SRTT   = (1 - alpha) * SRTT + alpha * RTT             alpha=0.125
  RTO    = SRTT + max(G, 4 * RTTVAR)   G = clock granularity

Initial values: SRTT=0, RTTVAR=0, RTO=1s (TCP_TIMEOUT_INIT)
Bounds: TCP_RTO_MIN (200ms) <= RTO <= TCP_RTO_MAX (120s)
```

### 10.2 Fast Retransmit (Duplicate ACKs)

When the receiver gets an out-of-order segment, it sends an **immediate duplicate ACK**
for the last in-order byte received. After **3 duplicate ACKs**, the sender infers loss
and retransmits **without waiting for the RTO timer**.

```
Sender                        Receiver
  │                               │
  │── Seg 1 (seq=1,   len=1000) ──►│  rcv seq 1-1000:   ACK 1001
  │── Seg 2 (seq=1001,len=1000) ──►│  rcv seq 1001-2000: ACK 2001
  │── Seg 3 (seq=2001,len=1000) ──X│  LOST
  │── Seg 4 (seq=3001,len=1000) ──►│  out of order!    ACK 2001 (dup 1)
  │── Seg 5 (seq=4001,len=1000) ──►│  still missing 3  ACK 2001 (dup 2)
  │── Seg 6 (seq=5001,len=1000) ──►│  still missing 3  ACK 2001 (dup 3)
  │                               │
  │  3 dup ACKs received!         │
  │  Fast retransmit triggered:   │
  │── Seg 3 retransmit ──────────►│  ACK 6001 (all received now)
  │                               │
```

### 10.3 SACK (Selective Acknowledgment)

Without SACK, after a loss, the receiver can only tell the sender "I need from seq X
onwards" — the sender can't know which subsequent segments arrived. SACK lets the
receiver say exactly which ranges it has:

```
Receiver SACK option: "I have 3001-4001 and 5001-6001, missing 2001-3000"
  → SACK block 1: {3001, 4001}
  → SACK block 2: {5001, 6001}

Sender retransmits ONLY: 2001-3000
```

In the kernel:

```c
// tcp_sacktag_write_queue() processes incoming SACK blocks
// Marks sk_buff entries in write queue as SACKed (TCP_SKB_CB(skb)->sacked |= TCPCB_SACKED_ACKED)
// tcp_fastretrans_alert() decides which segments to retransmit
// tcp_retransmit_skb() does the actual retransmit
```

### 10.4 RACK (Recent ACK) — modern Linux default

RACK is a newer loss detection algorithm (RFC 8985, default in Linux ≥4.19):

```
Premise: if a packet was sent AFTER another packet, and the later packet is
         acknowledged, but the earlier one isn't → the earlier one is lost.

RACK.xmit_time: timestamp when each packet was sent
RACK.rtt:       smoothed RTT

A packet P is considered lost if:
  - A packet sent after P has been SACKed
  - AND more than RACK.rtt time has passed since P was sent
  - OR: reordering_seen && enough time passed (reorder window)
```

### 10.5 Summary: who detects loss and asks for retransmit

```
┌─────────────────┬────────────────────────────────────────────────┐
│ Mechanism       │ Who / What                                     │
├─────────────────┼────────────────────────────────────────────────┤
│ RTO timer       │ Sender's kernel TCP stack (tcp_retransmit_timer)│
│                 │ Fires when no ACK in time. Detects total loss.  │
├─────────────────┼────────────────────────────────────────────────┤
│ Dup ACKs /      │ Receiver sends dup ACKs; Sender detects 3 dup  │
│ Fast retransmit │ ACKs and retransmits (tcp_fastretrans_alert)    │
├─────────────────┼────────────────────────────────────────────────┤
│ SACK            │ Receiver reports gaps; Sender fills exact gaps  │
│                 │ (tcp_sacktag_write_queue + tcp_retransmit_skb)  │
├─────────────────┼────────────────────────────────────────────────┤
│ RACK            │ Sender tracks timing, infers loss without dup   │
│                 │ ACK threshold (handles reordering better)       │
├─────────────────┼────────────────────────────────────────────────┤
│ IP layer        │ NONE. IP is unreliable. Lost IP fragments       │
│                 │ cause reassembly timeout; TCP then retransmits. │
├─────────────────┼────────────────────────────────────────────────┤
│ UDP             │ NONE. Application must implement its own        │
│                 │ reliability (QUIC, SCTP, custom protocols)      │
└─────────────────┴────────────────────────────────────────────────┘

The sender is ALWAYS the retransmitter. The receiver only hints via ACKs.
```

### 10.6 Congestion control interaction

On any detected loss, TCP enters congestion response:

```c
// net/ipv4/tcp_cong.c, tcp_enter_loss():
tp->prior_ssthresh = tcp_current_ssthresh(sk);
tp->snd_ssthresh   = icsk->icsk_ca_ops->ssthresh(sk);  // e.g., cwnd/2
tp->snd_cwnd       = 1 * tp->mss_cache;                // slow start
tp->snd_cwnd_cnt   = 0;

// Fast retransmit (3 dup ACKs) uses different response:
// TCP Reno:  ssthresh = cwnd/2, cwnd = ssthresh + 3 (fast recovery)
// CUBIC:     W_max = cwnd, ssthresh = cwnd * beta_cubic
// BBR:       uses bandwidth-delay product model, different entirely
```

---

## 11. TCP Flags: Every Flag, Every Operation

TCP flags are in byte 13 of the TCP header (the control bits):

```
TCP Header (20 bytes minimum):
┌──────────────┬──────────────────────────────────────────┐
│  Source Port │            Destination Port              │
├──────────────┴──────────────────────────────────────────┤
│                     Sequence Number                     │
├─────────────────────────────────────────────────────────┤
│                  Acknowledgment Number                  │
├────────┬───┬─┬─┬─┬─┬─┬─┬─┬─┬──────────────────────────┤
│Data Off│Res│N│C│E│U│A│P│R│S│F│       Window Size       │
│  (4b)  │(3)│S│W│C│R│C│S│S│Y│I│          (16b)          │
│        │   │ │R│E│G│K│H│T│N│N│                         │
├────────┴───┴─┴─┴─┴─┴─┴─┴─┴─┴─┴──────────────────────────┤
│             Checksum             │     Urgent Pointer    │
└──────────────────────────────────┴───────────────────────┘
```

### Flag definitions and kernel handling

```
┌────┬──────────────────────────────────────────────────────────────┐
│SYN │ Synchronize sequence numbers.                                │
│    │ Used in handshake initiation.                                │
│    │                                                              │
│    │ Kernel: tcp_rcv_state_process() in LISTEN state             │
│    │   → creates new sock, allocates tcp_sock                    │
│    │   → sends SYN+ACK, moves to SYN_RECEIVED                   │
│    │ In SYN_SENT state (active opener):                          │
│    │   rcv SYN+ACK → sends ACK, moves to ESTABLISHED            │
│    │   rcv SYN (simultaneous open) → SYN_RECEIVED                │
│    │                                                              │
│    │ C: th->syn == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│ACK │ Acknowledgment field is valid.                               │
│    │ Present in almost all segments after initial SYN.           │
│    │                                                              │
│    │ Kernel: tcp_ack(sk, skb, flag) in tcp_rcv_established()    │
│    │   → reads th->ack_seq                                       │
│    │   → advances snd_una (oldest unACKed seq)                  │
│    │   → calls tcp_clean_rtx_queue() to free ACKed skbs         │
│    │   → updates send window: tp->snd_wnd = ntohs(th->window)   │
│    │   → runs congestion control: tcp_cong_avoid()              │
│    │                                                              │
│    │ C: th->ack == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│FIN │ No more data from sender. Initiates connection termination.  │
│    │                                                              │
│    │ Kernel: tcp_fin(sk) called when FIN received                │
│    │   ESTABLISHED → CLOSE_WAIT (passive closer)                 │
│    │   FIN_WAIT_1  → TIME_WAIT  (if ACK + FIN simultaneously)   │
│    │   FIN_WAIT_2  → TIME_WAIT  (received peer's FIN)           │
│    │   Wakes sleeping read()s with EOF (0 bytes returned)        │
│    │   Sends ACK for the FIN immediately                         │
│    │                                                              │
│    │ C: th->fin == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│RST │ Reset the connection. Abrupt termination.                    │
│    │                                                              │
│    │ Causes: connection to closed port, out-of-window segment,   │
│    │         application called SO_LINGER with l_linger=0        │
│    │                                                              │
│    │ Kernel on receive: tcp_reset(sk) or tcp_validate_incoming() │
│    │   → sets sk->sk_err = ECONNRESET                           │
│    │   → wakes all waiting processes with error                  │
│    │   → moves to CLOSED, frees resources                        │
│    │                                                              │
│    │ Kernel on send: tcp_send_reset() or tcp_v4_send_reset()    │
│    │   → sends RST without going through normal state machine    │
│    │                                                              │
│    │ Security note: RST injection is a real attack;              │
│    │ kernel validates: seq must be within window (RFC 5961)      │
│    │                                                              │
│    │ C: th->rst == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│PSH │ Push: receiver should push data to application immediately.  │
│    │ Don't wait to fill buffer.                                   │
│    │                                                              │
│    │ Kernel: tcp_push_one() on send sets PSH on last segment     │
│    │ On receive: tcp_push_pending_frames() — actually in Linux    │
│    │ PSH is largely advisory; the kernel delivers data whenever  │
│    │ a read() call comes in, regardless of PSH.                  │
│    │ sk->sk_data_ready() is called whether PSH is set or not.    │
│    │                                                              │
│    │ C: th->psh == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│URG │ Urgent pointer field is valid. Out-of-band data.            │
│    │                                                              │
│    │ The urgent pointer (16 bits in header) points to the last   │
│    │ byte of urgent data. Data before it is "urgent".            │
│    │                                                              │
│    │ Kernel: tcp_urg(sk, skb, th) processes urgent data          │
│    │   → sets sk->sk_urg_data                                    │
│    │   → sends SIGURG to socket owner process                    │
│    │   → application reads via MSG_OOB flag on recv()           │
│    │                                                              │
│    │ Rarely used in practice. Telnet used it for Ctrl+C.         │
│    │ C: th->urg == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│ECE │ ECN Echo. Set when receiver got CE (Congestion Experienced)  │
│    │ from IP layer (ECN bits in IP header).                      │
│    │                                                              │
│    │ Kernel: Processed in tcp_ecn_rcv_ecn_echo()                │
│    │   → sender reduces cwnd (congestion response w/o packet loss)│
│    │   Requires ECN negotiation during SYN (ECE+CWR in SYN)     │
│    │                                                              │
│    │ C: th->ece == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│CWR │ Congestion Window Reduced. Sender confirms it reduced cwnd.  │
│    │ In response to receiving ECE.                               │
│    │                                                              │
│    │ Kernel: tcp_ecn_send() sets CWR on next segment sent       │
│    │         after congestion response                           │
│    │                                                              │
│    │ C: th->cwr == 1                                             │
└────┴──────────────────────────────────────────────────────────────┘
┌────┬──────────────────────────────────────────────────────────────┐
│NS  │ Nonce Sum (RFC 3540). Experimental, ECN-related.            │
│    │ Rarely deployed.                                            │
│    │ C: th->res1 (occupies the nonce bit position)              │
└────┴──────────────────────────────────────────────────────────────┘
```

### Flag processing in tcp_validate_incoming()

```c
// net/ipv4/tcp_input.c — called for every incoming segment
static bool tcp_validate_incoming(struct sock *sk, struct sk_buff *skb,
                                  const struct tcphdr *th, int syn_inerr)
{
    // 1. SEQ check: is sequence number within receive window?
    if (!tcp_sequence(tp, TCP_SKB_CB(skb)->seq, TCP_SKB_CB(skb)->end_seq)) {
        // Out of window: send ACK (to update peer's window info), drop
        if (th->rst)
            goto reset;
        tcp_send_dupack(sk, skb);
        goto discard;
    }

    // 2. RST check
    if (th->rst) {
        // RFC 5961: validate RST sequence number
        if (TCP_SKB_CB(skb)->seq == tp->rcv_nxt)
            tcp_reset(sk);       // legitimate RST
        else
            tcp_send_challenge_ack(sk, skb);  // RST challenge
        goto discard;
    }

    // 3. SYN check (SYN in established is an error)
    if (th->syn) {
        // RFC 5961: send challenge ACK, don't reset
        tcp_send_challenge_ack(sk, skb);
        goto discard;
    }

    // 4. ACK check
    if (!th->ack) {
        // All post-SYN segments must have ACK set
        goto discard;
    }

    return true;

reset:
    tcp_reset(sk);
discard:
    return false;
}
```

---

## 12. NAPI: Interrupt Coalescing and Polling

### The problem with pure interrupt-driven RX

```
At 10Gbps with 64-byte packets:
  - ~14.88 million packets/second
  - Without NAPI: 14.88 million interrupts/second
  - Context switch + interrupt overhead: ~500ns each
  - 14.88M * 500ns = 7.44 seconds of interrupt overhead per second
  - System completely overwhelmed (known as "interrupt livelock")
```

### NAPI solution: hybrid interrupt + polling

```
Phase 1: Hardware interrupt fires (first packet arrives)
  │
  ├── Driver acknowledges interrupt, disables RX interrupt on NIC
  ├── Schedules NAPI poll: napi_schedule(&napi)
  │     adds to poll_list, raises NET_RX_SOFTIRQ
  └── Returns from interrupt

Phase 2: Softirq handler runs (NET_RX_SOFTIRQ)
  │
  net_rx_action():
  │  while (poll_list not empty && budget remaining):
  │    napi = poll_list.head
  │    work = napi->poll(napi, weight)  // driver polls RX ring
  │      - processes up to 'weight' packets (default 64)
  │      - calls netif_receive_skb() for each
  │      - returns # packets processed
  │    budget -= work
  │    if (work < weight):  // exhausted ring, no more packets
  │      napi_complete(napi)  // re-enable NIC RX interrupt
  └── Exit

Phase 3: If ring had more packets:
  │  poll() returned weight (hit budget limit)
  │  net_rx_action() continues loop (or reschedules)
  │  NIC interrupt stays disabled during this time
  └──► effectively: "keep polling until ring is empty"
```

### NAPI data structures

```c
struct napi_struct {
    struct list_head  poll_list;      // linked into softirq poll list
    unsigned long     state;          // NAPI_STATE_SCHED, etc.
    int               weight;         // max packets per poll (default 64)
    int             (*poll)(struct napi_struct *, int);  // driver poll fn
    struct net_device *dev;
    struct sk_buff    *skb;           // GRO accumulator
    struct list_head  rx_list;        // GRO list
    int               rx_count;       // GRO packet count
    // ...
};
```

---

## 13. GRO and GSO: Batching at Scale

### GSO (Generic Segmentation Offload) — Transmit

Instead of segmenting large TCP writes into MTU-sized segments in software and then
handing each to the driver, GSO lets the kernel pass a **"super-segment"** (up to 64KB)
to the driver and defer actual segmentation.

```
Without GSO:
  tcp_sendmsg(64KB) → 44 separate sk_buffs (64KB / 1448B)
  → 44 calls to ndo_start_xmit()
  → 44 DMA descriptors

With GSO (hardware offload = TSO):
  tcp_sendmsg(64KB) → 1 sk_buff with gso_size=1448, gso_segs=44
  → 1 call to ndo_start_xmit()
  → NIC hardware segments into 44 packets
  → 1 DMA descriptor (or few)
```

The `sk_buff` carries `skb->gso_size` and `skb->gso_segs`. If the NIC doesn't support
TSO, `dev_gso_segment()` is called in software before transmit.

### GRO (Generic Receive Offload) — Receive

GRO is the receive-side counterpart. It coalesces multiple incoming packets that belong
to the same TCP stream into one large `sk_buff` before passing up the stack.

```
Without GRO (44 packets × 1448B):
  → 44 calls to ip_rcv()
  → 44 calls to tcp_v4_rcv()
  → 44 sk_buffs queued to socket

With GRO (44 × 1448B → 1 × 64KB skb):
  → 1 call to ip_rcv()
  → 1 call to tcp_v4_rcv()
  → 1 sk_buff queued
```

GRO runs inside `napi_gro_receive()`:

```c
// Driver calls this instead of netif_receive_skb():
gro_result_t napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
{
    // Check against GRO list (napi->rx_list)
    // If matches existing flow: merge via skb_gro_receive()
    //   - append as frag_list entry, or
    //   - coalesce linear data
    // If no match: add to rx_list
    // If list full or flush timer: napi_gro_flush() → netif_receive_skb()
}
```

GRO merging conditions:
1. Same source/dest IP and port (same flow)
2. Contiguous TCP sequence numbers (next_seq == skb_seq)
3. Same IP ID (or IP ID increment by 1)
4. TCP flags compatible (no FIN, RST, URG, SYN)
5. No IP options (or same options)

---

## 14. Netfilter Hooks: Where iptables Lives

Netfilter defines 5 hook points in the packet path where registered functions can
inspect/modify/drop packets:

```
                         Incoming packet
                               │
                               ▼
                    ┌─────────────────────┐
                    │ NF_INET_PRE_ROUTING │  ← iptables PREROUTING chain
                    │   (raw, mangle,     │     DNAT happens here
                    │    conntrack init)  │
                    └────────┬────────────┘
                             │
                    ┌────────┴───────────────────────────────┐
                    │                                        │
                    ▼                                        ▼
         ┌──────────────────────┐              ┌────────────────────────┐
         │  NF_INET_LOCAL_IN    │              │  NF_INET_FORWARD       │
         │  (iptables INPUT)    │              │  (iptables FORWARD)    │
         │  packet for us       │              │  packet being routed   │
         └──────────┬───────────┘              └────────────┬───────────┘
                    │                                        │
                    ▼                                        ▼
              Local socket                      NF_INET_POST_ROUTING
                                                (iptables POSTROUTING)
                                                SNAT happens here
                                                      │
                                                      ▼
                                                  Outgoing

         For locally generated packets:
         Local process → NF_INET_LOCAL_OUT (OUTPUT) → NF_INET_POST_ROUTING → wire
```

### Hook registration

```c
static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};

nf_register_net_hook(net, &my_hook_ops);

// Hook function signature:
unsigned int my_hook_fn(void *priv, struct sk_buff *skb,
                        const struct nf_hook_state *state)
{
    struct iphdr *iph = ip_hdr(skb);
    if (iph->protocol == IPPROTO_TCP) {
        // Inspect/modify skb
    }
    return NF_ACCEPT;  // or NF_DROP, NF_STOLEN, NF_QUEUE, NF_REPEAT
}
```

### Conntrack (connection tracking)

```
nf_conntrack module adds state to each packet:
  NEW        → first packet of a flow (SYN, or UDP first pkt)
  ESTABLISHED → reply seen (SYN+ACK, or UDP reply)
  RELATED    → related connection (FTP data, ICMP error for TCP)
  INVALID    → doesn't match any known state

State stored in: struct nf_conn  (per-flow, hash-keyed by 5-tuple)
Each skb gets: skb->_nfct pointing to the nf_conn

Used by NAT, stateful firewalls, etc.
```

---

## 15. The Socket Buffer Queue: sk_receive_queue and sk_write_queue

The `struct sock` has two primary queues:

```c
struct sock {
    // Receive queue: fully reassembled TCP segments waiting for read()
    struct sk_buff_head  sk_receive_queue;
    // Write queue: segments sent but not yet ACKed (retransmit buffer)
    struct sk_buff_head  sk_write_queue;
    // Out-of-order queue (received but not yet in sequence)
    struct rb_root       tcp_rtx_queue;  // retransmit queue (red-black tree)
    struct sk_buff_head  sk_error_queue;
    // ...
    int                  sk_rcvbuf;  // max receive buffer size (bytes)
    int                  sk_sndbuf;  // max send buffer size (bytes)
};
```

### Write queue (retransmit buffer) lifecycle

```
tcp_sendmsg():
  skb allocated, user bytes copied in
  skb added to sk_write_queue (via __skb_queue_tail)
  tcp_push() called

tcp_write_xmit():
  skb = tcp_send_head(sk)     // peek at head of write queue
  tcp_transmit_skb()           // sends a clone; original stays in queue
  tcp_advance_send_head(sk, skb)  // move send pointer forward

tcp_ack():  // ACK received
  tcp_clean_rtx_queue(sk):
    while (skb = tcp_write_queue_head(sk)):
      if before(TCP_SKB_CB(skb)->end_seq, tp->snd_una):
        // This skb fully ACKed
        tcp_write_queue_head_remove(sk)  // dequeue
        sk_wmem_free_skb(sk, skb)        // kfree_skb
        break
      else:
        break  // not yet ACKed, stop
```

### Receive queue flow control (TCP window)

```
sk_rcvbuf determines how much data TCP advertises as receive window:

tp->rcv_wnd = tcp_receive_window(tp)
  = min(sk->sk_rcvbuf - sk->sk_rmem_alloc, TCP_MAX_WINDOW)

When application reads via recv():
  sk->sk_rmem_alloc decreases
  Window opens: tcp_send_ack() or tcp_send_window_probe() sent to peer

When application is slow:
  sk_rmem_alloc approaches sk_rcvbuf
  Window advertised approaches 0 ("zero window")
  Peer must stop sending
  Eventually: "zero window probe" from peer to check if window opened
```

---

## 16. C Implementation Patterns

### 16.1 Writing a minimal kernel module that intercepts packets

```c
// intercept_tcp.c — kernel module using Netfilter

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>

MODULE_LICENSE("GPL");

static unsigned int tcp_hook(void *priv,
                              struct sk_buff *skb,
                              const struct nf_hook_state *state)
{
    struct iphdr  *iph;
    struct tcphdr *th;

    if (!skb)
        return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (!iph || iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;

    // pskb_may_pull ensures the TCP header is in linear area
    if (!pskb_may_pull(skb, ip_hdrlen(skb) + sizeof(struct tcphdr)))
        return NF_ACCEPT;

    // Re-fetch iph after pskb_may_pull (may have reallocated)
    iph = ip_hdr(skb);
    th  = (struct tcphdr *)((u8 *)iph + ip_hdrlen(skb));

    printk(KERN_INFO "TCP: %pI4:%u -> %pI4:%u seq=%u ack=%u "
           "SYN=%d ACK=%d FIN=%d RST=%d PSH=%d\n",
           &iph->saddr, ntohs(th->source),
           &iph->daddr, ntohs(th->dest),
           ntohl(th->seq), ntohl(th->ack_seq),
           th->syn, th->ack, th->fin, th->rst, th->psh);

    return NF_ACCEPT;
}

static struct nf_hook_ops hook_ops = {
    .hook     = tcp_hook,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};

static int __init tcp_intercept_init(void)
{
    return nf_register_net_hook(&init_net, &hook_ops);
}

static void __exit tcp_intercept_exit(void)
{
    nf_unregister_net_hook(&init_net, &hook_ops);
}

module_init(tcp_intercept_init);
module_exit(tcp_intercept_exit);
```

### 16.2 Allocating and building an skb from scratch

```c
// Building a raw TCP packet:
struct sk_buff *build_tcp_skb(struct net_device *dev,
                               __be32 saddr, __be32 daddr,
                               __be16 sport, __be16 dport,
                               __be32 seq,  __be32 ack_seq,
                               __u16 flags, __u16 window,
                               unsigned char *payload, int plen)
{
    struct sk_buff *skb;
    struct ethhdr  *eth;
    struct iphdr   *iph;
    struct tcphdr  *th;
    int total = ETH_HLEN + sizeof(*iph) + sizeof(*th) + plen;

    // Allocate: headroom for L2/L3/L4 + payload
    skb = alloc_skb(total + NET_IP_ALIGN, GFP_ATOMIC);
    if (!skb)
        return NULL;

    skb_reserve(skb, NET_IP_ALIGN);

    // Build Ethernet header (skb_put advances tail)
    eth = (struct ethhdr *)skb_put(skb, ETH_HLEN);
    memset(eth->h_dest,   0xff, ETH_ALEN);   // broadcast
    memcpy(eth->h_source, dev->dev_addr, ETH_ALEN);
    eth->h_proto = htons(ETH_P_IP);
    skb->mac_header = (unsigned char *)eth - skb->head;

    // Build IP header
    iph = (struct iphdr *)skb_put(skb, sizeof(*iph));
    iph->version  = 4;
    iph->ihl      = sizeof(*iph) / 4;
    iph->tos      = 0;
    iph->tot_len  = htons(sizeof(*iph) + sizeof(*th) + plen);
    iph->id       = htons(prandom_u32());
    iph->frag_off = htons(IP_DF);
    iph->ttl      = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr    = saddr;
    iph->daddr    = daddr;
    ip_send_check(iph);   // computes and fills iph->check
    skb->network_header = (unsigned char *)iph - skb->head;

    // Build TCP header
    th = (struct tcphdr *)skb_put(skb, sizeof(*th));
    memset(th, 0, sizeof(*th));
    th->source   = sport;
    th->dest     = dport;
    th->seq      = htonl(seq);
    th->ack_seq  = htonl(ack_seq);
    th->doff     = sizeof(*th) / 4;
    // flags: e.g. flags = (1<<1)=SYN, (1<<4)=ACK, etc.
    ((u8 *)th)[13] = flags;
    th->window   = htons(window);
    th->check    = 0;  // compute after payload
    skb->transport_header = (unsigned char *)th - skb->head;

    // Copy payload
    if (plen > 0)
        memcpy(skb_put(skb, plen), payload, plen);

    // Compute TCP checksum (pseudo-header + TCP header + data)
    th->check = csum_tcpudp_magic(saddr, daddr,
                                   sizeof(*th) + plen,
                                   IPPROTO_TCP,
                                   csum_partial(th, sizeof(*th) + plen, 0));
    return skb;
}
```

### 16.3 Walking the fragment list

```c
// Iterate over all bytes in a (possibly non-linear) skb:
void dump_skb_data(struct sk_buff *skb)
{
    unsigned char *ptr;
    int len;

    // Linear part:
    ptr = skb->data;
    len = skb_headlen(skb);  // = skb->len - skb->data_len
    printk(KERN_INFO "Linear %d bytes at %p\n", len, ptr);

    // Page fragments:
    for (int i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
        printk(KERN_INFO "Frag[%d]: page=%p offset=%u size=%u\n",
               i,
               skb_frag_page(frag),
               skb_frag_off(frag),
               skb_frag_size(frag));
    }

    // frag_list (chained skbs — used by IP reassembly, GRO):
    struct sk_buff *frag_skb;
    skb_walk_frags(skb, frag_skb) {
        printk(KERN_INFO "frag_list skb: len=%d\n", frag_skb->len);
    }
}
```

### 16.4 eBPF / XDP — reading skb-like data in BPF programs

XDP programs run even before the sk_buff is allocated — they work directly on the
raw DMA buffer via `xdp_md`:

```c
// XDP program (loaded via BPF):
SEC("xdp")
int xdp_tcp_inspect(struct xdp_md *ctx)
{
    // ctx->data and ctx->data_end are __u64 pointers to DMA buffer:
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)   // mandatory bounds check
        return XDP_PASS;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    if (iph->protocol != IPPROTO_TCP)
        return XDP_PASS;

    struct tcphdr *th = (void *)iph + iph->ihl * 4;
    if ((void *)(th + 1) > data_end)
        return XDP_PASS;

    // Access th->syn, th->ack, th->fin etc.
    // Direct pointer to DMA bytes — zero copy, zero skb allocation
    if (th->syn && !th->ack) {
        // SYN packet: could do SYN proxy, rate limiting, etc.
        bpf_printk("SYN from port %d\n", bpf_ntohs(th->source));
    }

    return XDP_PASS;
}
```

---

## 17. Rust: Safe Abstractions Over the Same Concepts

Rust in the kernel (via `rust/` directory in Linux ≥6.1) provides safe wrappers.
For userspace/eBPF, `aya` is the primary framework.

### 17.1 Userspace packet parsing with the `pnet` crate

```rust
use pnet::packet::ethernet::{EthernetPacket, EtherTypes};
use pnet::packet::ip::IpNextHeaderProtocols;
use pnet::packet::ipv4::Ipv4Packet;
use pnet::packet::tcp::TcpPacket;
use pnet::packet::Packet;

/// Parse a raw Ethernet frame and print TCP info.
/// The bytes slice is the raw DMA frame — analogous to skb->data at L2.
pub fn parse_frame(raw: &[u8]) {
    let eth = match EthernetPacket::new(raw) {
        Some(p) => p,
        None    => return,
    };

    // EthernetPacket::payload() is analogous to skb_pull(ETH_HLEN):
    // it returns a slice starting after the Ethernet header.
    if eth.get_ethertype() != EtherTypes::Ipv4 {
        return;
    }

    let ip_raw = eth.payload();  // &raw[14..]
    let iph = match Ipv4Packet::new(ip_raw) {
        Some(p) => p,
        None    => return,
    };

    if iph.get_next_level_protocol() != IpNextHeaderProtocols::Tcp {
        return;
    }

    // iph.payload() = &ip_raw[iph.get_header_length()*4..]
    let tcp_raw = iph.payload();
    let th = match TcpPacket::new(tcp_raw) {
        Some(p) => p,
        None    => return,
    };

    let flags = th.get_flags();
    println!(
        "TCP {}:{} -> {}:{} seq={} ack={} flags: SYN={} ACK={} FIN={} RST={} PSH={}",
        iph.get_source(), th.get_source(),
        iph.get_destination(), th.get_destination(),
        th.get_sequence(), th.get_acknowledgement(),
        (flags >> 1) & 1,  // SYN
        (flags >> 4) & 1,  // ACK
        (flags >> 0) & 1,  // FIN
        (flags >> 2) & 1,  // RST
        (flags >> 3) & 1,  // PSH
    );
}
```

### 17.2 eBPF with aya (Rust eBPF framework)

aya lets you write XDP/TC programs in Rust with the same access to raw packet bytes.

```rust
// eBPF program (runs in kernel, compiled to BPF bytecode):
// File: src/bpf/xdp_tcp.rs

#![no_std]
#![no_main]

use aya_bpf::{macros::xdp, programs::XdpContext, bindings::xdp_action};
use aya_bpf::helpers::bpf_printk;
use network_types::{eth::{EthHdr, EtherType}, ip::{Ipv4Hdr, IpProto}, tcp::TcpHdr};
use core::mem;

#[xdp]
pub fn xdp_tcp_inspect(ctx: XdpContext) -> u32 {
    match try_xdp_tcp(&ctx) {
        Ok(ret) => ret,
        Err(_)  => xdp_action::XDP_PASS,
    }
}

fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();
    if start + offset + len > end {
        return Err(());  // Rust enforces bounds check — won't compile without this
    }
    Ok((start + offset) as *const T)
}

fn try_xdp_tcp(ctx: &XdpContext) -> Result<u32, ()> {
    let eth: *const EthHdr = ptr_at(ctx, 0)?;
    // SAFETY: bounds checked above
    if unsafe { (*eth).ether_type } != EtherType::Ipv4 {
        return Ok(xdp_action::XDP_PASS);
    }

    let iph: *const Ipv4Hdr = ptr_at(ctx, EthHdr::LEN)?;
    let ip_proto = unsafe { (*iph).proto };
    if ip_proto != IpProto::Tcp {
        return Ok(xdp_action::XDP_PASS);
    }
    let ip_hdr_len = unsafe { ((*iph).version_ihl & 0x0f) as usize * 4 };

    let th: *const TcpHdr = ptr_at(ctx, EthHdr::LEN + ip_hdr_len)?;
    let flags = unsafe { (*th).flags() };  // bitfield accessor

    if flags.syn() && !flags.ack() {
        // Pure SYN — new connection attempt
        unsafe {
            bpf_printk!(b"SYN from port %d\n\0", u16::from_be((*th).source) as u64);
        }
    }

    Ok(xdp_action::XDP_PASS)
}
```

```rust
// Userspace loader (runs in userspace, loads BPF program):
// File: src/main.rs

use aya::{Bpf, programs::{Xdp, XdpFlags}};
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/xdp_tcp"
    ))?;

    let program: &mut Xdp = bpf.program_mut("xdp_tcp_inspect").unwrap().try_into()?;
    program.load()?;
    program.attach("eth0", XdpFlags::default())?;  // attaches at XDP hook on eth0

    println!("XDP program attached. Press Ctrl-C to stop.");
    tokio::signal::ctrl_c().await?;
    Ok(())
}
```

### 17.3 Raw socket in Rust (analogous to AF_PACKET in C)

```rust
// Raw socket: receives Ethernet frames including all headers.
// Equivalent of the C: socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))

use std::net::UdpSocket;
use std::os::unix::io::FromRawFd;
use libc::{AF_PACKET, ETH_P_ALL, SOCK_RAW, c_int, socket, sockaddr_ll, bind};
use std::mem::{size_of, zeroed};

fn open_raw_socket(ifindex: c_int) -> Result<c_int, std::io::Error> {
    unsafe {
        // AF_PACKET raw socket — receives at L2 (before any kernel processing)
        let fd = socket(AF_PACKET, SOCK_RAW, (ETH_P_ALL as u16).to_be() as c_int);
        if fd < 0 {
            return Err(std::io::Error::last_os_error());
        }

        let mut addr: sockaddr_ll = zeroed();
        addr.sll_family   = AF_PACKET as u16;
        addr.sll_protocol = (ETH_P_ALL as u16).to_be();
        addr.sll_ifindex  = ifindex;

        let ret = bind(
            fd,
            &addr as *const _ as *const libc::sockaddr,
            size_of::<sockaddr_ll>() as u32,
        );
        if ret < 0 {
            return Err(std::io::Error::last_os_error());
        }

        Ok(fd)
    }
}

// Receive loop:
fn receive_frames(fd: c_int) {
    let mut buf = [0u8; 65535];
    loop {
        let n = unsafe { libc::recv(fd, buf.as_mut_ptr() as *mut _, buf.len(), 0) };
        if n < 0 { break; }

        let frame = &buf[..n as usize];
        // frame[0..14]  = Ethernet header (same as skb->mac_header area)
        // frame[14..]   = IP packet  (same as skb->data after skb_pull(ETH_HLEN))
        parse_frame(frame);
    }
}
```

### 17.4 smoltcp: A userspace TCP/IP stack in Rust

smoltcp implements the entire stack in safe Rust, exposing the same concepts
as the kernel stack but in userspace:

```rust
use smoltcp::iface::{Config, Interface, SocketSet};
use smoltcp::phy::{TunTapInterface, Device, Medium};
use smoltcp::socket::tcp;
use smoltcp::time::Instant;
use smoltcp::wire::{EthernetAddress, IpAddress, IpCidr, Ipv4Address};

fn main() -> Result<(), smoltcp::Error> {
    // TUN/TAP interface — kernel hands us raw IP packets
    let mut device = TunTapInterface::new("tap0", Medium::Ethernet).unwrap();

    let config = Config::new(EthernetAddress([0x02, 0x00, 0x00, 0x00, 0x00, 0x01]).into());
    let mut iface = Interface::new(config, &mut device, Instant::now());
    iface.update_ip_addrs(|addrs| {
        addrs.push(IpCidr::new(IpAddress::v4(192, 168, 69, 1), 24)).unwrap();
    });

    // TCP socket — smoltcp manages its own sk_buff equivalent internally
    let tcp_rx_buffer = tcp::SocketBuffer::new(vec![0; 65535]);  // ≈ sk_rcvbuf
    let tcp_tx_buffer = tcp::SocketBuffer::new(vec![0; 65535]);  // ≈ sk_sndbuf
    let tcp_socket    = tcp::Socket::new(tcp_rx_buffer, tcp_tx_buffer);

    let mut sockets = SocketSet::new(vec![]);
    let tcp_handle  = sockets.add(tcp_socket);

    // smoltcp's poll() = equivalent of net_rx_action() + tcp_v4_rcv():
    // Internally it:
    //   1. Reads frames from device (like NAPI poll)
    //   2. Strips Ethernet header (like netif_receive_skb)
    //   3. Processes IP: checksum, routing, fragmentation
    //   4. Processes TCP: state machine, ACKs, retransmission
    //   5. Delivers data to socket buffers
    loop {
        let timestamp = Instant::now();
        iface.poll(timestamp, &mut device, &mut sockets);

        let socket = sockets.get_mut::<tcp::Socket>(tcp_handle);
        if socket.may_recv() {
            let data = socket.recv(|buf| {
                let len = buf.len();
                (len, buf[..len].to_vec())
            }).unwrap();
            // process data...
        }

        // smoltcp handles:
        // - RTO timer via poll() being called periodically
        // - Retransmission when timer expires
        // - Window advertisement based on buffer space
        // - TCP flags: SYN/SYN-ACK exchange, ACK generation, FIN handling
        // All the same concepts as the Linux kernel, in safe Rust.
    }
}
```

### 17.5 Rust kernel module (linux ≥ 6.1 with Rust support)

```rust
// A Rust kernel module using the kernel crate (upstream rust-for-linux):
// This is the in-kernel Rust API — still evolving as of 2025

use kernel::prelude::*;
use kernel::net::filter::{self, HookOps, NfHookState, SkBuff};
use kernel::net::{Protocol, Family};

module! {
    type: TcpInspect,
    name: "tcp_inspect",
    license: "GPL",
}

struct TcpInspect {
    _hook: filter::Registration,
}

// The Rust sk_buff wrapper provides safe access:
fn hook_fn(skb: &SkBuff, _state: &NfHookState) -> filter::Action {
    // skb.ip_hdr() returns Option<&IpHdr> — safe, bounds-checked
    if let Some(iph) = skb.ip_hdr() {
        if iph.protocol() == Protocol::Tcp {
            if let Some(th) = skb.tcp_hdr() {
                pr_info!("TCP seq={} syn={} ack={}\n",
                         th.seq(), th.syn(), th.ack());
            }
        }
    }
    filter::Action::Accept
}

impl kernel::Module for TcpInspect {
    fn init(_name: &'static CStr, _module: &'static ThisModule) -> Result<Self> {
        let hook = HookOps::register(Family::Ipv4, filter::HookPoint::PreRouting,
                                      filter::Priority::First, hook_fn)?;
        Ok(TcpInspect { _hook: hook })
    }
}
```

---

## 18. Complete Mental Model: End-to-End ASCII Walkthrough

### Full receive path with all components labeled

```
════════════════════════════════════════════════════════════════════
                    COMPLETE RECEIVE PATH
════════════════════════════════════════════════════════════════════

HARDWARE LAYER:
  ┌─────────────────────────────────────────────────────────────┐
  │  Physical wire: electrical signals / photons                │
  │        │                                                    │
  │  NIC PHY layer: signal → digital bits                       │
  │        │                                                    │
  │  NIC MAC layer: frame delineation, CRC check                │
  │        │         FCS (Frame Check Sequence) verified        │
  │        │         Bad frame? Drop silently at hardware       │
  │        │                                                    │
  │  DMA engine: NIC writes frame bytes into RAM (RX ring)      │
  │        │     No CPU involvement in data transfer!           │
  │        │                                                    │
  │  NIC raises hardware interrupt (IRQ line)                   │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼  CPU receives interrupt
════════════════════════════════════════════════════════════════════

DRIVER LAYER (runs in interrupt context):
  ┌─────────────────────────────────────────────────────────────┐
  │  Driver ISR (e.g., igb_intr):                               │
  │    - Clear interrupt status register (ACK to NIC)           │
  │    - Disable RX interrupt (prevent flood)                   │
  │    - napi_schedule() → adds to softirq poll list            │
  │    - Return from interrupt (fast! <microseconds)            │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼  softirqd or ksoftirqd picks up NET_RX_SOFTIRQ
════════════════════════════════════════════════════════════════════

NAPI / DRIVER POLL (softirq context):
  ┌─────────────────────────────────────────────────────────────┐
  │  net_rx_action() → driver->poll() (e.g. igb_clean_rx_irq)  │
  │                                                             │
  │  For each descriptor in RX ring:                            │
  │    ┌─────────────────────────────────────────────────┐      │
  │    │ DMA buffer in RAM:                              │      │
  │    │ [ETH HDR 14B][IP HDR 20B][TCP HDR 20B][DATA]   │      │
  │    └─────────────────────────────────────────────────┘      │
  │                 │                                           │
  │    sk_buff allocated (just the metadata struct)             │
  │    skb->data = pointer to DMA buffer start                  │
  │    skb->len  = frame length from descriptor                 │
  │    skb->dev  = net_device                                   │
  │                 │                                           │
  │    (Optional: GRO coalescing via napi_gro_receive())        │
  │                 │                                           │
  │    netif_receive_skb(skb) called                            │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼
════════════════════════════════════════════════════════════════════

L2 — ETHERNET (__netif_receive_skb):
  ┌─────────────────────────────────────────────────────────────┐
  │  skb->data → [ETH HDR][IP HDR][TCP HDR][DATA]              │
  │               ▲                                             │
  │               mac_header set here                          │
  │                                                             │
  │  Packet taps run (AF_PACKET: tcpdump reads here)            │
  │  Ingress TC hooks run                                       │
  │                                                             │
  │  skb->protocol = ETH_P_IP extracted from eth->h_proto      │
  │                                                             │
  │  deliver_skb() → ip_rcv() dispatched                       │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼
════════════════════════════════════════════════════════════════════

L3 — IP (ip_rcv → ip_rcv_finish):
  ┌─────────────────────────────────────────────────────────────┐
  │  skb->data → [ETH HDR][IP HDR][TCP HDR][DATA]              │
  │                         ▲                                   │
  │               network_header set here                       │
  │                                                             │
  │  iph = ip_hdr(skb) = skb->head + skb->network_header       │
  │  Validate: version=4, ihl>=5, tot_len reasonable           │
  │  Verify checksum (or offloaded to hardware)                 │
  │                                                             │
  │  NF_HOOK(PRE_ROUTING) → iptables/nftables PREROUTING       │
  │    conntrack: flow lookup/creation                          │
  │    DNAT if applicable (rewrite dst IP/port)                 │
  │                                                             │
  │  Route lookup: fib_lookup() → skb->_skb_refdst             │
  │    Decision: LOCAL_IN (for us) or FORWARD (route it)       │
  │                                                             │
  │  Fragment check:                                            │
  │    if (iph->frag_off & (IP_MF | IP_OFFSET)):               │
  │      ip_defrag(skb) → reassemble or queue fragment         │
  │      if incomplete: return (skb consumed, waiting)         │
  │      if complete: skb = reassembled_skb                     │
  │                                                             │
  │  NF_HOOK(LOCAL_IN) → iptables INPUT chain                  │
  │                                                             │
  │  ip_local_deliver_finish():                                 │
  │    raw_local_deliver(skb, protocol)  // raw sockets        │
  │    ipprot = inet_protos[iph->protocol]                      │
  │    ipprot->handler(skb) → tcp_v4_rcv()                     │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼
════════════════════════════════════════════════════════════════════

L4 — TCP (tcp_v4_rcv):
  ┌─────────────────────────────────────────────────────────────┐
  │  skb->data → [ETH HDR][IP HDR][TCP HDR][DATA]              │
  │                                   ▲                         │
  │               transport_header set here                     │
  │                                                             │
  │  th = tcp_hdr(skb)                                          │
  │  Validate: doff reasonable, pskb_may_pull for full hdr     │
  │  TCP checksum verification (pseudo-header: src+dst IP)      │
  │                                                             │
  │  4-tuple lookup:                                            │
  │    sk = __inet_lookup_skb(&tcp_hashinfo,                    │
  │                            src_ip, src_port,               │
  │                            dst_ip, dst_port)               │
  │    Hash: jhash(saddr^daddr, sport^dport, secret)           │
  │                                                             │
  │  sk->sk_state == TCP_ESTABLISHED:                           │
  │    tcp_rcv_established():                                   │
  │      Header prediction (fast path):                         │
  │        if pure ACK with no data: just update snd_una       │
  │        if in-order data: go to fast path                   │
  │                                                             │
  │      tcp_validate_incoming(): check SEQ, RST, SYN, ACK     │
  │                                                             │
  │      tcp_ack(): process acknowledgment                      │
  │        tcp_clean_rtx_queue(): free ACKed skbs from wq      │
  │        tcp_cong_avoid(): increase cwnd (CUBIC, BBR, Reno)  │
  │        tcp_send_ack() if delayed ACK timer expired          │
  │                                                             │
  │      tcp_queue_rcv(): add skb to sk->sk_receive_queue      │
  │        OR: tcp_data_queue_ofo() if out of order            │
  │            (stored in sk->tcp_rtx_queue red-black tree)    │
  │                                                             │
  │      tcp_push_pending_frames() if peer's window opened     │
  │                                                             │
  │      sk->sk_data_ready(sk):                                 │
  │        → wakes up processes sleeping in recv()/select()/   │
  │           epoll_wait() waiting on this socket               │
  └────────┼────────────────────────────────────────────────────┘
           │
           ▼
════════════════════════════════════════════════════════════════════

SOCKET / VFS LAYER:
  ┌─────────────────────────────────────────────────────────────┐
  │  Process calls: recv(fd, buf, len, 0)                       │
  │                 read(fd, buf, len)                          │
  │                 recvmsg(fd, &msg, 0)                        │
  │                                                             │
  │  syscall → tcp_recvmsg():                                   │
  │    lock_sock(sk)                                            │
  │    while (sk->sk_receive_queue not empty && len > 0):      │
  │      skb = skb_peek(&sk->sk_receive_queue)                  │
  │      offset = sk->copied_seq - TCP_SKB_CB(skb)->seq        │
  │      used = skb->len - offset (bytes available in this skb) │
  │      copy = min(used, len)                                  │
  │                                                             │
  │      skb_copy_datagram_msg(skb, offset, msg, copy)         │
  │        → memcpy_to_iter() copies to user iovec             │
  │        → THIS IS THE ONLY COPY in the entire receive path   │
  │                                                             │
  │      sk->copied_seq += copy                                 │
  │      len -= copy                                            │
  │      if (skb fully consumed):                               │
  │        __skb_unlink(skb, &sk->sk_receive_queue)             │
  │        kfree_skb(skb)  // refcount→0, memory freed         │
  │                                                             │
  │    tcp_rcv_space_adjust(sk)  // adjust rcvbuf if needed    │
  │    tcp_cleanup_rbuf(sk, copied)  // maybe send window update│
  │    release_sock(sk)                                         │
  │                                                             │
  │    return copied   // bytes returned to userspace           │
  └────────┬────────────────────────────────────────────────────┘
           │
           ▼ bytes in user buffer — application processes them
════════════════════════════════════════════════════════════════════

MEMORY LIFECYCLE SUMMARY:
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  NIC DMA → skb allocated → skb passed by POINTER through   │
  │  all layers → ONE copy into userspace at recvmsg →         │
  │  skb freed when userspace has consumed all data            │
  │                                                             │
  │  Headers are never copied. skb->data pointer moves.        │
  │  Payload bytes are never copied until recvmsg.             │
  │  Fragmentation: new skbs allocated, payload sliced.        │
  │  Reassembly: fragments linked via frag_list, OR merged     │
  │              into new linear skb by ip_frag_reasm.         │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

### Retransmission decision tree

```
Packet sent (tcp_transmit_skb):
  skb cloned, placed in sk_write_queue
  RTO timer set (tcp_reset_xmit_timer)
         │
         │
  ┌──────┴──────────────────────────────────────────────────┐
  │                   What happens next?                    │
  └──────┬──────────────────────────────┬───────────────────┘
         │                              │
    ACK arrives                    No ACK arrives
    within RTO                     (timer fires)
         │                              │
    tcp_ack()                     tcp_retransmit_timer()
    tcp_clean_rtx_queue()              │
    skb freed                     tcp_retransmit_skb()
    Timer cancelled               tcp_enter_loss():
    DONE                            cwnd = 1 MSS
                                    ssthresh = cwnd/2
                                    backoff++
                                    RTO *= 2
                                  Timer restarted
                                       │
                                  (repeats up to
                                  tcp_retries2=15 times
                                  ≈ ~13 min total before
                                  ETIMEDOUT reported)

  ─── OR ───

  3 duplicate ACKs arrive (fast retransmit):
    tcp_fastretrans_alert()
    tcp_retransmit_skb(oldest_unacked)
    tcp_enter_fast_recovery():
      ssthresh = max(cwnd/2, 2)
      cwnd = ssthresh + 3  (inflate for in-flight dup ACKs)
    New ACK: exit fast recovery, cwnd = ssthresh
```

---

## Key Takeaways: The Mental Model

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. ONE sk_buff for the entire packet lifetime.                 │
│     Passed as a POINTER (by reference) between all layers.     │
│     Headers are NEVER copied — skb->data pointer moves.        │
│                                                                 │
│  2. The kernel is pointing to the SAME bytes the NIC DMA'd.    │
│     skb_pull() "removes" a header by advancing skb->data.      │
│     skb_push() "adds" a header by retreating skb->data.        │
│     Old headers remain accessible via stored offsets.          │
│                                                                 │
│  3. IP fragmentation splits ONE packet into MULTIPLE skbs.     │
│     Done by sender when packet > MTU. Each fragment is an      │
│     independent IP packet. Reassembly is RECEIVER's job.       │
│                                                                 │
│  4. IP reassembly: ipq holds fragments until all arrive or     │
│     30-second timeout. Identified by (src, dst, id, proto).    │
│                                                                 │
│  5. TCP retransmission is ENTIRELY the SENDER's responsibility. │
│     Three mechanisms: RTO timer, 3 dup ACKs (fast retransmit), │
│     SACK (selective), RACK (time-based). No lower layer helps. │
│                                                                 │
│  6. TCP flags are checked in tcp_validate_incoming() before    │
│     any state machine processing. RST must be in-window.       │
│     SYN in ESTABLISHED sends challenge ACK (RFC 5961).         │
│                                                                 │
│  7. The ONE AND ONLY memcpy on the receive path is in          │
│     tcp_recvmsg() → skb_copy_datagram_msg() → userspace.       │
│     Everything before that is zero-copy pointer manipulation.  │
│                                                                 │
│  8. NAPI prevents interrupt livelock by switching from         │
│     interrupt-driven to polling mode under high load.          │
│                                                                 │
│  9. GRO (rx) and GSO/TSO (tx) batch packets to reduce         │
│     per-packet overhead at all layers.                         │
│                                                                 │
│ 10. Netfilter hooks (iptables/nftables/conntrack) sit at 5    │
│     points in the packet path, operating on the same skb.     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- `include/linux/skbuff.h` — sk_buff definition (the most important file)
- `net/ipv4/ip_input.c` — ip_rcv, ip_rcv_finish, ip_local_deliver
- `net/ipv4/ip_output.c` — ip_queue_xmit, ip_do_fragment, ip_finish_output
- `net/ipv4/ip_fragment.c` — ip_defrag, ip_frag_queue, ip_frag_reasm
- `net/ipv4/tcp_input.c` — tcp_v4_rcv, tcp_rcv_established, tcp_ack, tcp_data_queue
- `net/ipv4/tcp_output.c` — tcp_write_xmit, tcp_transmit_skb, tcp_send_ack
- `net/ipv4/tcp_timer.c` — tcp_retransmit_timer, RTO management
- `net/core/dev.c` — netif_receive_skb, net_rx_action, dev_queue_xmit
- `net/core/skbuff.c` — alloc_skb, kfree_skb, skb_clone, skb_copy
- RFC 793 — TCP specification
- RFC 2581 / RFC 5681 — TCP congestion control
- RFC 2018 — SACK
- RFC 6298 — RTO computation
- RFC 8985 — RACK loss detection
- RFC 791 — IPv4 (fragmentation spec)
- RFC 6864 — Updated IPv4 ID field (fragmentation security)
