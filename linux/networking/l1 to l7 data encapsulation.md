# L1–L7 Data Encapsulation: Complete Kernel, Driver, and Userspace Deep Dive

> **Summary (6 lines):** Data encapsulation in Linux traverses at least seven distinct execution
> domains — application syscall boundary, VFS/socket layer, protocol stacks (TCP/UDP/IP),
> Netfilter hooks, the network device abstraction layer, NIC driver ring buffers, and finally
> PHY/MAC hardware. The fundamental unit crossing all these boundaries is `struct sk_buff`
> (skb), the kernel's unified packet descriptor that avoids copying data by growing headers
> via `skb_push()` and shrinking them via `skb_pull()`. Each layer prepends its header into
> a pre-allocated headroom, sets protocol-specific fields, computes or offloads checksums,
> and hands the skb down via well-defined function-pointer dispatch tables. NIC hardware
> consumes DMA descriptors pointing into skb data pages, applies hardware offloads (TSO,
> checksum, VLAN tagging), and serializes bits onto the wire via PHY/SerDes; the reverse
> path reassembles frames through GRO/LRO, IRQ/NAPI coalescing, and netif_receive_skb()
> back up to the waiting socket receive queue — all without a single extra memcpy in the
> fast path if zero-copy is configured.

---

## Table of Contents

1. [Execution Domain Map](#1-execution-domain-map)
2. [The Central Data Structure: `struct sk_buff`](#2-the-central-data-structure-struct-sk_buff)
3. [L7 — Application Layer (Userspace)](#3-l7--application-layer-userspace)
4. [L6 — Presentation / TLS (Userspace kTLS hybrid)](#4-l6--presentation--tls-userspace-ktls-hybrid)
5. [L5 — Session Layer](#5-l5--session-layer)
6. [L4 — Transport Layer: TCP/UDP in the Kernel](#6-l4--transport-layer-tcpudp-in-the-kernel)
7. [L3 — Network Layer: IP in the Kernel](#7-l3--network-layer-ip-in-the-kernel)
8. [Netfilter / eBPF Hook Plane](#8-netfilter--ebpf-hook-plane)
9. [L2 — Data Link Layer: Ethernet Framing](#9-l2--data-link-layer-ethernet-framing)
10. [Network Device Abstraction (`struct net_device`)](#10-network-device-abstraction-struct-net_device)
11. [NIC Driver Ring Buffers and DMA](#11-nic-driver-ring-buffers-and-dma)
12. [L1 — Physical Layer: PHY, SerDes, PCI-e](#12-l1--physical-layer-phy-serdes-pci-e)
13. [NAPI, IRQ Coalescing, and the Receive Path](#13-napi-irq-coalescing-and-the-receive-path)
14. [XDP — eXpress Data Path](#14-xdp--express-data-path)
15. [Hardware Offloads: TSO, GRO, RSS, Checksum, VLAN](#15-hardware-offloads-tso-gro-rss-checksum-vlan)
16. [Zero-Copy Paths: sendfile, splice, MSG_ZEROCOPY](#16-zero-copy-paths-sendfile-splice-msg_zerocopy)
17. [DPDK Userspace Networking (Bypass)](#17-dpdk-userspace-networking-bypass)
18. [Memory Subsystem: NUMA, DMA, IOMMU, Huge Pages](#18-memory-subsystem-numa-dma-iommu-huge-pages)
19. [Complete Annotated C Implementation](#19-complete-annotated-c-implementation)
20. [Complete Annotated Rust Implementation](#20-complete-annotated-rust-implementation)
21. [Architecture: Full Stack ASCII Diagram](#21-architecture-full-stack-ascii-diagram)
22. [Threat Model and Security Analysis](#22-threat-model-and-security-analysis)
23. [Testing, Fuzzing, and Benchmarking](#23-testing-fuzzing-and-benchmarking)
24. [Kernel Source File Reference Index](#24-kernel-source-file-reference-index)
25. [Next 3 Steps](#25-next-3-steps)

---

## 1. Execution Domain Map

Before diving per-layer, understand *where* code runs. This is the most important mental model:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RING 3 / USERSPACE                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │ App code │  │ libc/glibc   │  │ OpenSSL/   │  │ DPDK / io_uring     │   │
│  │ (Go/Rust)│  │ send()/recv()│  │ BoringSSL  │  │ PMD (poll-mode drv) │   │
│  └──────────┘  └──────────────┘  └────────────┘  └─────────────────────┘   │
├─────────────────────────── syscall boundary ────────────────────────────────┤
│  RING 0 / KERNEL SPACE                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ VFS / Socket Layer    net/socket.c   include/linux/net.h            │    │
│  │ INET / AF_INET6       net/ipv4/af_inet.c                            │    │
│  │ ┌──────────────────────────────────────────────────────────────┐    │    │
│  │ │ TCP      net/ipv4/tcp.c tcp_output.c tcp_input.c tcp_timer.c│    │    │
│  │ │ UDP      net/ipv4/udp.c                                      │    │    │
│  │ └──────────────────────────────────────────────────────────────┘    │    │
│  │ IP (v4/v6)  net/ipv4/ip_output.c  net/ipv6/ip6_output.c            │    │
│  │ Netfilter   net/netfilter/   (iptables/nftables/eBPF)               │    │
│  │ Routing     net/ipv4/route.c  fib_trie                              │    │
│  │ ARP/NDP     net/ipv4/arp.c   net/ipv6/ndisc.c                      │    │
│  │ Ethernet    net/ethernet/eth.c                                      │    │
│  │ net_device  net/core/dev.c   include/linux/netdevice.h              │    │
│  │ qdisc/TC    net/sched/                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
├─────────────────────── driver boundary (kernel module) ─────────────────────┤
│  RING 0 / NIC DRIVER                                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ igb/ixgbe/mlx5/i40e/virtio-net/ena                                   │   │
│  │ TX ring: DMA descriptor → NIC MMIO doorbell                          │   │
│  │ RX ring: DMA descriptor ← NIC fills → NAPI poll                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
├─────────────────────── PCIe / MMIO boundary ────────────────────────────────┤
│  HARDWARE                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ NIC MAC (Media Access Controller)                                     │   │
│  │ NIC PHY (Physical layer chip)     SerDes / PCS                        │   │
│  │ TSO engine, checksum engine, RSS hash, VLAN strip/insert              │   │
│  │ DMA engine ↔ PCIe ↔ CPU memory bus ↔ IOMMU                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insight:** The Linux kernel does NOT copy data between layers. It manipulates a single
`sk_buff` whose `data` pointer walks forward (pull) or backward (push) as headers are
added/removed. The actual payload bytes written by the application stay in place from the
moment `tcp_sendmsg()` copies them from userspace until the NIC DMA engine reads them.

---

## 2. The Central Data Structure: `struct sk_buff`

**Kernel source:** `include/linux/skbuff.h` (≈1500 lines of documented struct + inline functions)

The `sk_buff` (socket buffer) is the most important struct in the Linux network stack. Every
packet — inbound and outbound — is represented as an skb from the moment it enters the kernel
until it leaves via the NIC driver.

### 2.1 Memory Layout

```
skb_shared_info (at end of data buffer)
┌─────────────────────────────────────────────────────────────────────┐
│  struct sk_buff (control plane, in slab cache)                      │
│  ┌──────────────┬────────────────────────────────────────────────┐  │
│  │ sk_buff      │ next/prev (skb queue links)                    │  │
│  │ meta         │ sk      (owning socket)                        │  │
│  │              │ dev     (net_device)                           │  │
│  │              │ cb[48]  (protocol private scratch space)       │  │
│  │              │ len / data_len                                 │  │
│  │              │ protocol, pkt_type, ip_summed                  │  │
│  │              │ hash, vlan_tci, mark, priority                 │  │
│  └──────────────┴────────────────────────────────────────────────┘  │
│  Pointer members:                                                    │
│    head  ──────────────────────────────────────────────────────►┐   │
│    data  ──────────────────────────────►┐                        │   │
│    tail  ────────────────────────────────────────────►┐          │   │
│    end   ──────────────────────────────────────────────────────►┐│   │
└─────────────────────────────────────────────────────────────────┘│   │
                                                                    │   │
Physical memory (page or slab):                                     │   │
┌──────────┬────────────────────────────────────────────┬──────────┴───┤
│ headroom │  [ETH][IP][TCP][ P A Y L O A D         ]  │ skb_shinfo   │
│ (for hdr │ ▲              ▲                        ▲  │ (frags,      │
│ prepend) │ head          data                     tail│  gso_size,   │
└──────────┴────────────────────────────────────────────┴──────────────┘
           ▲                                             ▲
           head                                         end
```

### 2.2 Critical sk_buff Fields

```c
/* include/linux/skbuff.h */
struct sk_buff {
    /* --- Queue/list management --- */
    struct sk_buff      *next;
    struct sk_buff      *prev;
    union {
        ktime_t          tstamp;    /* RX timestamp */
        u64              skb_mstamp_ns;
    };

    /* --- Device and socket ownership --- */
    struct sock         *sk;        /* owning socket (NULL for forwarded pkts) */
    struct net_device   *dev;       /* device this skb was received on / will TX on */

    /* --- Header pointers (set per-layer as skb traverses stack) --- */
    /* These live inside the data buffer, not separate allocations */
    union {
        struct {
            /* L2 */
            unsigned char *mac_header;   /* points to ETH header */
        };
    };
    sk_buff_data_t      network_header;  /* L3: IP header offset from head */
    sk_buff_data_t      transport_header;/* L4: TCP/UDP header offset from head */
    sk_buff_data_t      inner_*;        /* for tunnels (VXLAN, GRE, etc.) */

    /* --- Data pointers --- */
    unsigned char       *head;   /* start of allocated buffer */
    unsigned char       *data;   /* start of current useful data */
    sk_buff_data_t      tail;    /* end of current useful data */
    sk_buff_data_t      end;     /* end of allocated buffer */

    /* --- Length fields --- */
    unsigned int        len;         /* total length (linear + frags) */
    unsigned int        data_len;    /* length of paged (non-linear) data */
    __u16               mac_len;     /* length of L2 header */
    __u16               hdr_len;     /* L2 header for cloned skbs */

    /* --- Protocol / classification --- */
    __be16              protocol;    /* L3 protocol: ETH_P_IP, ETH_P_IPV6, etc. */
    __u16               transport_header_valid:1;
    __u8                pkt_type;    /* PACKET_HOST, PACKET_BROADCAST, etc. */
    __u8                ip_summed;   /* CHECKSUM_NONE/PARTIAL/COMPLETE/UNNECESSARY */

    /* --- GSO (Generic Segmentation Offload) --- */
    __u16               gso_size;    /* MSS for GSO */
    __u16               gso_segs;    /* number of GSO segments */
    __u16               gso_type;    /* SKB_GSO_TCPV4, SKB_GSO_UDP_L4, etc. */

    /* --- Marks / hash / priority --- */
    __u32               priority;    /* queueing priority */
    __u32               hash;        /* flow hash for RSS */
    __u32               mark;        /* SO_MARK / nfmark */
    __u16               vlan_tci;    /* VLAN tag (if stripped by NIC) */
    __u16               vlan_proto;  /* ETH_P_8021Q or ETH_P_8021AD */

    /* --- Per-protocol scratch space (48 bytes) --- */
    /* TCP uses this for tcp_skb_cb, IP for IPCB, etc. */
    char                cb[48] __aligned(8);

    /* --- Fragment list (for non-linear skbs / scatter-gather) --- */
    /* skb_shared_info is at skb->end, contains: */
    /*   skb_frag_t frags[MAX_SKB_FRAGS] -- page references */
    /*   struct sk_buff *frag_list        -- for IP fragments */

    /* --- Cloning / reference counting --- */
    atomic_t            users;   /* reference count */
    refcount_t          dataref; /* data area reference count for clones */

    /* --- eBPF / XDP metadata --- */
    unsigned long       _nfct;   /* conntrack handle */
    /* ... many more fields omitted for brevity ... */
};
```

### 2.3 Header Manipulation Primitives

```c
/* net/core/skbuff.c + include/linux/skbuff.h */

/* Push: move data pointer back, prepend header space (TX path, adding headers) */
static inline void *skb_push(struct sk_buff *skb, unsigned int len) {
    skb->data -= len;
    skb->len  += len;
    /* BUG_ON(skb->data < skb->head) -- headroom exhausted */
    return skb->data;
}

/* Pull: move data pointer forward, strip header (RX path, consuming headers) */
static inline void *skb_pull(struct sk_buff *skb, unsigned int len) {
    return skb->len < len ? NULL : __skb_pull(skb, len);
}

/* Put: extend tail (appending data) */
static inline void *skb_put(struct sk_buff *skb, unsigned int len) {
    void *tmp = skb_tail_pointer(skb);
    SKB_LINEAR_ASSERT(skb);
    skb->tail += len;
    skb->len  += len;
    /* BUG_ON(skb->tail > skb->end) */
    return tmp;
}

/* Reserve headroom BEFORE writing any data (done at allocation time) */
static inline void skb_reserve(struct sk_buff *skb, int len) {
    skb->data += len;
    skb->tail += len;
}

/* Key allocation function */
struct sk_buff *alloc_skb(unsigned int size, gfp_t priority);
/* With headroom pre-reserved: */
struct sk_buff *dev_alloc_skb(unsigned int length);
/* length + NET_SKB_PAD headroom reserved for driver use */
```

The **headroom** is pre-allocated when the skb is created. For a TCP segment going out:

1. TCP calls `alloc_skb()` with `MAX_TCP_HEADER` headroom reserved
2. `skb_reserve(skb, MAX_TCP_HEADER)` — data pointer moves forward by `MAX_TCP_HEADER`
3. `skb_put(skb, payload_len)` — tail moves forward, payload copied here
4. TCP: `skb_push(skb, sizeof(tcphdr))` — prepends TCP header
5. IP: `skb_push(skb, sizeof(iphdr))` — prepends IP header
6. Ethernet: `skb_push(skb, sizeof(ethhdr))` — prepends ETH header
7. Driver reads `skb->data` through `skb->tail` — no copies needed

---

## 3. L7 — Application Layer (Userspace)

### 3.1 System Call Entry

An application writes data via `write()`, `send()`, `sendto()`, or `sendmsg()`.
All of these converge at the same kernel entry point.

**Kernel source:** `net/socket.c`

```c
/* net/socket.c — syscall dispatch */
SYSCALL_DEFINE4(send, int, fd, void __user *, buff, size_t, len, unsigned, flags)
{
    return __sys_sendto(fd, buff, len, flags, NULL, 0);
}

SYSCALL_DEFINE6(sendto, int, fd, void __user *, buff, size_t, len,
                unsigned, flags, struct sockaddr __user *, addr, int, addr_len)
{
    return __sys_sendto(fd, buff, len, flags, addr, addr_len);
}

int __sys_sendto(int fd, void __user *buff, size_t len, unsigned flags,
                 struct sockaddr __user *addr, int addr_len)
{
    struct socket *sock;
    struct msghdr msg;
    struct iovec iov;

    /* 1. Look up the file descriptor → struct socket */
    sock = sockfd_lookup_light(fd, &err, &fput_needed);

    /* 2. Build msghdr (scatter-gather IO descriptor) */
    iov_iter_init(&msg.msg_iter, WRITE, &iov, 1, len);
    msg.msg_name    = addr;
    msg.msg_namelen = addr_len;
    msg.msg_flags   = flags;

    /* 3. Dispatch to protocol-specific sendmsg */
    /* sock->ops is set at socket creation to inet_stream_ops or inet_dgram_ops */
    err = sock_sendmsg(sock, &msg);
    /* → calls sock->ops->sendmsg(sock, msg, msg_data_left(msg)) */
}
```

### 3.2 Socket Structures

```c
/* include/linux/net.h */
struct socket {
    socket_state        state;      /* SS_UNCONNECTED, SS_CONNECTED, etc. */
    short               type;       /* SOCK_STREAM, SOCK_DGRAM, SOCK_RAW */
    unsigned long       flags;
    struct file         *file;      /* backing file (for fd) */
    struct sock         *sk;        /* protocol-level socket (the "real" socket) */
    const struct proto_ops *ops;    /* protocol operations vtable */
    struct socket_wq    wq;         /* wait queue for poll/select/epoll */
};

/* include/net/sock.h — the protocol-level socket */
struct sock {
    /* --- Addressing --- */
    struct sock_common  __sk_common;  /* contains sk_family, sk_state, addresses */

    /* --- Send/Recv buffers --- */
    int                 sk_sndbuf;    /* SO_SNDBUF: TX socket buffer size */
    int                 sk_rcvbuf;    /* SO_RCVBUF: RX socket buffer size */
    struct sk_buff_head sk_receive_queue; /* received-but-not-read packets */
    struct sk_buff_head sk_write_queue;   /* queued-for-send packets */
    int                 sk_wmem_queued;   /* bytes in write queue */
    int                 sk_forward_alloc; /* pre-allocated memory quota */

    /* --- Protocol operations --- */
    struct proto        *sk_prot;        /* TCP/UDP/RAW protocol struct */
    struct proto        *sk_prot_creator;

    /* --- Socket options --- */
    int                 sk_rcvlowat;   /* SO_RCVLOWAT */
    long                sk_rcvtimeo;   /* SO_RCVTIMEO */
    long                sk_sndtimeo;   /* SO_SNDTIMEO */
    u32                 sk_priority;   /* SO_PRIORITY */
    u32                 sk_mark;       /* SO_MARK */

    /* --- Callbacks (used by TCP for connection events) --- */
    void                (*sk_state_change)(struct sock *sk);
    void                (*sk_data_ready)(struct sock *sk);
    void                (*sk_write_space)(struct sock *sk);
    void                (*sk_error_report)(struct sock *sk);
};
```

### 3.3 `struct proto_ops` — The VTable

```c
/* include/linux/net.h */
struct proto_ops {
    int             family;
    struct module   *owner;
    int             (*release)   (struct socket *sock);
    int             (*bind)      (struct socket *sock, struct sockaddr *myaddr, int sockaddr_len);
    int             (*connect)   (struct socket *sock, struct sockaddr *vaddr, int sockaddr_len, int flags);
    int             (*accept)    (struct socket *sock, struct socket *newsock, int flags, bool kern);
    int             (*getname)   (struct socket *sock, struct sockaddr *addr, int peer);
    __poll_t        (*poll)      (struct file *file, struct socket *sock, struct poll_table_struct *wait);
    int             (*ioctl)     (struct socket *sock, unsigned int cmd, unsigned long arg);
    int             (*sendmsg)   (struct socket *sock, struct msghdr *m, size_t total_len);
    int             (*recvmsg)   (struct socket *sock, struct msghdr *m, size_t total_len, int flags);
    int             (*mmap)      (struct file *file, struct socket *sock, struct vm_area_struct *vma);
    ssize_t         (*sendpage)  (struct socket *sock, struct page *page, int offset, size_t size, int flags);
    /* ... */
};

/* net/ipv4/af_inet.c — TCP stream ops */
const struct proto_ops inet_stream_ops = {
    .family     = PF_INET,
    .sendmsg    = inet_sendmsg,   /* → tcp_sendmsg() */
    .recvmsg    = inet_recvmsg,   /* → tcp_recvmsg() */
    .poll       = tcp_poll,
    .mmap       = sock_no_mmap,
    .sendpage   = inet_sendpage,  /* for sendfile/splice */
    /* ... */
};

/* UDP */
const struct proto_ops inet_dgram_ops = {
    .sendmsg    = inet_sendmsg,   /* → udp_sendmsg() */
    .recvmsg    = inet_recvmsg,   /* → udp_recvmsg() */
    /* ... */
};
```

### 3.4 Go Userspace: What Happens Before syscall

In Go, `net.Conn.Write()` calls:

```
net.Conn.Write()
  → netFD.Write()
    → poll.FD.Write()
      → syscall.Write() / syscall.Sendmsg()
        → raw syscall instruction (SYSCALL on amd64)
```

Go uses `netpoll` (epoll on Linux) via the runtime scheduler. When a `Write()` would block
(socket buffer full), the goroutine is parked and another goroutine runs — this is the
`runtime.netpollblock()` mechanism integrated with the Go scheduler's M:N threading model.

The goroutine doesn't make a blocking syscall; instead:
1. It tries a non-blocking `send()` (with `MSG_DONTWAIT`)
2. If `EAGAIN`, it registers the fd with epoll via `runtime_pollWait()`
3. The network poller (`sysmon` goroutine or epoll thread) wakes it when the fd is writable

---

## 4. L6 — Presentation / TLS (Userspace kTLS hybrid)

### 4.1 Standard TLS in Userspace (OpenSSL/BoringSSL)

Classically, TLS is entirely in userspace:

```
Application plaintext
  → TLS record: [ContentType(1)][Version(2)][Length(2)][Payload][MAC/AEAD-tag]
  → send() to kernel socket
```

TLS record structure (RFC 5246 / RFC 8446):

```c
/* RFC 5246 §6.2 */
struct TLSPlaintext {
    uint8_t  type;        /* 20=change_cipher, 21=alert, 22=handshake, 23=application_data */
    uint16_t version;     /* 0x0303 for TLS 1.2, 0x0303 for TLS 1.3 (legacy compat) */
    uint16_t length;      /* length of fragment (max 2^14 bytes) */
    uint8_t  fragment[]; /* actual data */
};

/* TLS 1.3 adds inner type at end of ciphertext */
struct TLSInnerPlaintext {
    uint8_t  content[];
    uint8_t  type;       /* actual content type, hidden from network */
    uint8_t  zeros[];    /* optional padding */
};
```

### 4.2 Kernel TLS (kTLS) — `net/tls/`

Linux 4.13+ supports kTLS where the symmetric crypto (AES-GCM) happens in kernel space,
allowing `sendfile()` to work with TLS without copying data to userspace for encryption.

**Kernel source:** `net/tls/tls_main.c`, `net/tls/tls_sw.c`, `net/tls/tls_device.c`

```c
/* net/tls/tls_main.c — setup */
static int tls_setsockopt(struct sock *sk, int level, int optname,
                           sockptr_t optval, unsigned int optlen)
{
    /* Application negotiates TLS in userspace, then passes cipher keys to kernel: */
    /* setsockopt(fd, SOL_TLS, TLS_TX, &crypto_info, sizeof(crypto_info)) */
    /* After this, write() → kernel encrypts inline before TCP segmentation */
}

/* net/tls/tls_sw.c — software crypto path */
static int tls_push_record(struct sock *sk, int flags, unsigned char record_type)
{
    struct tls_context *tls_ctx = tls_get_ctx(sk);
    struct tls_sw_context_tx *ctx = tls_sw_ctx_tx(tls_ctx);
    struct sk_msg *msg_pl, *msg_en;

    /* 1. Build TLS header in skb headroom */
    /* 2. Call AEAD encrypt (AES-128-GCM or ChaCha20-Poly1305) */
    /* 3. Append authentication tag */
    /* 4. Hand skb to TCP stack normally */
}
```

### 4.3 NIC-offloaded TLS (`tls_device.c`)

Some NICs (Mellanox ConnectX-5+, Chelsio T6) can offload TLS encryption to hardware:

```
Application → write() → kernel TCP (no encrypt) → NIC encrypts in hardware → wire
```

The kernel tracks TLS sequence numbers per-connection and programs them into NIC TLS offload
context registers. This achieves line-rate TLS without any CPU crypto overhead.

---

## 5. L5 — Session Layer

In the Linux network stack, there is no explicit L5 implementation. The session concept is
handled implicitly:

- **TCP connections** serve as sessions: `struct tcp_sock` tracks connection state
- **TLS sessions** are managed by userspace (OpenSSL session resumption, tickets)
- **QUIC** (HTTP/3) combines L4 transport + session + presentation in userspace or in kernel
  (via `net/tls/` for some vendors)
- **SCTP** (`net/sctp/`) has explicit association/stream concepts that map to L5

For practical purposes, when analyzing Linux code, treat L5 as "TCP connection state" in
`struct tcp_sock`, specifically the fields managing connection lifetime, ordering, and
retransmission.

---

## 6. L4 — Transport Layer: TCP/UDP in the Kernel

### 6.1 TCP Send Path

**Kernel source:** `net/ipv4/tcp.c`, `net/ipv4/tcp_output.c`, `net/ipv4/tcp_input.c`

```c
/* net/ipv4/tcp.c — tcp_sendmsg() entry point */
int tcp_sendmsg(struct sock *sk, struct msghdr *msg, size_t size)
{
    struct tcp_sock *tp = tcp_sk(sk);
    struct sk_buff *skb;
    int flags = msg->msg_flags;
    int mss_now, size_goal;
    bool sg; /* scatter-gather capable? */

    lock_sock(sk);  /* acquire socket lock (process context) */

    /* Determine MSS and GSO goal size */
    mss_now   = tcp_send_mss(sk, &size_goal, flags);
    /* size_goal = mss_now * gso_max_segs if GSO enabled, else mss_now */

    /* Main loop: copy userspace data into skbs */
    while (msg_data_left(msg)) {
        int copy = 0;
        int max  = size_goal;

        /* Try to continue filling the last skb in write queue */
        skb = tcp_write_queue_tail(sk);
        if (skb) {
            /* Does this skb still have room? */
            if (skb->ip_summed == CHECKSUM_PARTIAL) {
                copy = size_goal - skb->len;
            }
        }

        if (copy <= 0 || !tcp_skb_can_collapse_to(skb)) {
new_segment:
            /* Allocate a new skb */
            if (!sk_stream_memory_free(sk))
                goto wait_for_sndbuf;

            skb = sk_stream_alloc_skb(sk,
                                       SELECT_SIZE(sk, sg, first_skb),
                                       sk->sk_allocation,
                                       first_skb);
            /* Pre-reserve headroom for all protocol headers */
            skb_reserve(skb, MAX_TCP_HEADER);
            /* MAX_TCP_HEADER = sizeof(eth)+sizeof(ip_options)+sizeof(tcphdr)+LL_MAX_HEADER */
            skb_entail(sk, skb); /* add to write queue */
        }

        /* Copy data from userspace into skb */
        /* Uses skb_add_data_nocache or skb_copy_to_page_nocache */
        if (skb_availroom(skb) > 0 && !zc) {
            /* Linear copy into skb tail */
            copy = min_t(int, copy, skb_availroom(skb));
            err  = skb_add_data_nocache(sk, skb, &msg->msg_iter, copy);
        } else {
            /* Copy into page fragments (scatter-gather / paged data) */
            copy = min_t(int, copy, PAGE_SIZE);
            err  = skb_copy_to_page_nocache(sk, &msg->msg_iter, skb,
                                             pfrag->page, pfrag->offset, copy);
            /* Records page in skb_shinfo(skb)->frags[] */
        }
    }

    /* If MSG_NOWAIT not set, call tcp_push() to transmit */
    if (!(flags & MSG_SENDPAGE_NOTLAST))
        tcp_push(sk, flags, mss_now, tp->nonagle, size_goal);

out:
    release_sock(sk);
    return copied;
}
```

### 6.2 TCP Output: Building the Segment

```c
/* net/ipv4/tcp_output.c */

/* tcp_transmit_skb() — main function that builds TCP header and hands to IP */
static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb, int clone_it,
                             gfp_t gfp_mask)
{
    struct tcp_sock *tp;
    struct tcphdr *th;
    int err;

    /* Clone or copy the skb (original stays in retransmit queue) */
    if (likely(clone_it)) {
        skb = skb_clone(skb, gfp_mask);
        /* skb_clone: new sk_buff descriptor, shared data pages */
    }

    tp = tcp_sk(sk);

    /* Push TCP header into headroom */
    skb_push(skb, tcp_header_size);     /* moves data pointer back */
    skb_reset_transport_header(skb);    /* sets transport_header = data - head */

    /* Fill TCP header */
    th = (struct tcphdr *)skb->data;
    th->source  = inet->inet_sport;     /* source port (network byte order) */
    th->dest    = inet->inet_dport;     /* dest port */
    th->seq     = htonl(tcb->seq);      /* sequence number */
    th->ack_seq = htonl(tp->rcv_nxt);   /* acknowledgment number */
    th->doff    = (tcp_header_size >> 2);/* data offset (header length / 4) */
    th->window  = htons(tcp_select_window(sk)); /* advertised receive window */
    th->check   = 0;                    /* filled by checksum offload or manually */
    th->urg_ptr = 0;

    /* TCP flags: SYN, ACK, FIN, RST, PSH, URG */
    tcp_flags = tcb->tcp_flags;
    th->fin = !!(tcp_flags & TCPHDR_FIN);
    th->syn = !!(tcp_flags & TCPHDR_SYN);
    th->rst = !!(tcp_flags & TCPHDR_RST);
    th->psh = !!(tcp_flags & TCPHDR_PSH);
    th->ack = !!(tcp_flags & TCPHDR_ACK);

    /* Checksum: mark as partial (NIC will complete it) or compute in software */
    if (sk->sk_route_caps & NETIF_F_HW_CSUM) {
        /* Hardware checksum offload: set pseudo-header checksum */
        skb->ip_summed  = CHECKSUM_PARTIAL;
        skb->csum_start = skb_transport_header(skb) - skb->head;
        skb->csum_offset = offsetof(struct tcphdr, check);
        th->check = ~tcp_v4_check(skb->len, saddr, daddr, 0);
        /* NIC will compute final checksum over payload + pseudo-header */
    } else {
        /* Software checksum */
        th->check = tcp_v4_check(skb->len, saddr, daddr,
                                  csum_partial(th, tcp_header_size, skb->csum));
    }

    /* Hand to IP layer */
    err = icsk->icsk_af_ops->queue_xmit(sk, skb, &inet->cork.fl);
    /* For IPv4: ip_queue_xmit() */
}
```

### 6.3 TCP Receive Path

```c
/* net/ipv4/tcp_input.c — simplified receive */

/* Called from ip_local_deliver_finish() after IP header processing */
int tcp_v4_do_rcv(struct sock *sk, struct sk_buff *skb)
{
    /* State machine dispatch */
    if (sk->sk_state == TCP_ESTABLISHED) {
        /* Fast path for established connections */
        tcp_rcv_established(sk, skb);
        return 0;
    }
    /* Slow path: SYN, FIN, etc. */
    return tcp_rcv_state_process(sk, skb);
}

static void tcp_rcv_established(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);

    /* Header prediction (fast path) */
    /* Checks: in-order, no options, no URG, etc. */
    if (likely(tcp_header_matches_prediction(th, tp))) {
        /* Acknowledge and queue data */
        eaten = tcp_queue_rcv(sk, skb, &fragstolen);
        /* Wakes up sk_data_ready → application can read() */
        if (eaten > 0)
            sk->sk_data_ready(sk);
        /* Send ACK */
        if (!copied_early)
            tcp_event_data_recv(sk, skb);
        return;
    }
    /* Slow path: out-of-order, etc. */
    tcp_data_queue(sk, skb);
}
```

### 6.4 TCP Control Block (the `cb` field)

```c
/* include/net/tcp.h */
/* TCP stores per-skb metadata in sk_buff::cb[] */
struct tcp_skb_cb {
    __u32   seq;           /* Starting sequence number */
    __u32   end_seq;       /* SEQ + FIN + SYN + datalen */
    union {
        struct {
            u16 tcp_gso_segs; /* number of GSO segments in this skb */
            u16 tcp_gso_size; /* size of each segment */
        };
    };
    __u8    tcp_flags;     /* TCP header flags for this segment */
    __u8    sacked;        /* State flags: TCPCB_SACKED_ACKED, TCPCB_RETRANS */
    __u8    ip_dsfield;    /* DSCP/ECN bits */
    __u8    txstamp_ack;   /* transmit timestamp ack flag */
    __u32   ack_seq;       /* Sequence number ACK'd by remote */
};
/* Access: TCP_SKB_CB(skb)->seq */
```

### 6.5 UDP Send Path

```c
/* net/ipv4/udp.c */
int udp_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    struct udp_sock *up = udp_sk(sk);
    struct inet_sock *inet = inet_sk(sk);
    struct flowi4 fl4;
    struct rtable *rt;
    int err;

    /* 1. Route lookup (may be cached) */
    rt = ip_route_output_flow(net, &fl4, sk);

    /* 2. If MSG_MORE or cork, accumulate data into cork buffer */
    if (up->pending) {
        /* Append to existing UDP cork */
        goto do_append_data;
    }

    /* 3. Build UDP cork for this datagram */
    up->len     = 0;
    up->pending = AF_INET;

do_append_data:
    up->len += ulen;
    err = ip_append_data(sk, &fl4,
                         getfrag, msg,     /* getfrag copies from userspace */
                         ulen,             /* data length */
                         sizeof(struct udphdr),  /* header length to reserve */
                         &ipc, &rt,
                         msg->msg_flags);

    /* 4. If datagram complete, flush */
    if (!(msg->msg_flags & MSG_MORE)) {
        err = udp_push_pending_frames(sk);
        /* → ip_push_pending_frames() → ip_finish_skb() → adds UDP+IP headers */
    }
}

/* UDP header is inserted by ip_append_data via getfrag callback */
static int udp_getfrag(void *from, char *to, int offset, int len, int odd,
                        struct sk_buff *skb)
{
    struct msghdr *msg = from;
    if (offset == 0) {
        /* First fragment: prepend UDP header */
        struct udphdr *uh = (struct udphdr *)to;
        uh->source = SPORT;
        uh->dest   = DPORT;
        uh->len    = htons(data_len + sizeof(*uh));
        uh->check  = 0; /* will be computed or offloaded */
        to  += sizeof(*uh);
        len -= sizeof(*uh);
    }
    return copy_from_iter(to, len, &msg->msg_iter);
}
```

### 6.6 TCP State Machine

```c
/* net/ipv4/tcp_input.c — state transitions */
/* TCP states: include/net/tcp_states.h */
/*
 * TCP_CLOSE         = 0  -- not allocated
 * TCP_ESTABLISHED   = 1  -- data transfer
 * TCP_SYN_SENT      = 2  -- SYN sent, awaiting SYN-ACK
 * TCP_SYN_RECV      = 3  -- SYN received, SYN-ACK sent
 * TCP_FIN_WAIT1     = 4  -- FIN sent, awaiting ACK
 * TCP_FIN_WAIT2     = 5  -- FIN ACK'd, awaiting remote FIN
 * TCP_TIME_WAIT     = 6  -- waiting for stale packets to die
 * TCP_CLOSE_WAIT    = 7  -- remote FIN received, ACK sent
 * TCP_LAST_ACK      = 8  -- FIN sent (passive close), awaiting ACK
 * TCP_LISTEN        = 10 -- listening for connections
 * TCP_CLOSING       = 11 -- both sides sent FIN simultaneously
 */

/* Three-way handshake (active open, client side): */
/* CLOSE → send SYN → SYN_SENT */
/* SYN_SENT + SYN-ACK received → send ACK → ESTABLISHED */

/* TCP struct for per-connection state */
struct tcp_sock {
    struct inet_connection_sock inet_conn; /* base */
    u16     tcp_header_len;    /* bytes of tcp header to send */
    u32     snd_nxt;           /* next sequence number to send */
    u32     snd_una;           /* oldest unacknowledged sequence number */
    u32     snd_wnd;           /* send window (from remote receiver) */
    u32     rcv_nxt;           /* next sequence number expected from peer */
    u32     rcv_wup;           /* rcv_nxt on last window update sent */
    u32     rcv_wnd;           /* current receive window size */
    u32     srtt_us;           /* smoothed RTT << 3 in usecs */
    u32     rttvar_us;         /* mean deviation */
    u32     rto;               /* retransmit timeout */
    u32     snd_cwnd;          /* congestion window */
    u32     snd_ssthresh;      /* slow start threshold */
    /* Congestion control: net/ipv4/tcp_cubic.c, tcp_bbr.c, etc. */
    const struct tcp_congestion_ops *ca_ops;
    /* ... 100+ more fields */
};
```

---

## 7. L3 — Network Layer: IP in the Kernel

### 7.1 IP Output Path

**Kernel source:** `net/ipv4/ip_output.c`

```c
/* net/ipv4/ip_output.c */

/* ip_queue_xmit() — called by TCP */
int ip_queue_xmit(struct sock *sk, struct sk_buff *skb, struct flowi *fl)
{
    struct inet_sock *inet = inet_sk(sk);
    struct rtable *rt;
    struct iphdr *iph;

    /* 1. Route lookup (socket has cached route in sk->sk_dst_cache) */
    rt = skb_rtable(skb);
    if (!rt) {
        rt = ip_route_output_ports(net, &fl4, sk,
                                    daddr, saddr,
                                    inet->inet_dport, inet->inet_sport,
                                    sk->sk_protocol, RT_CONN_FLAGS(sk), sk->sk_bound_dev_if);
        sk_setup_caps(sk, &rt->dst);
    }
    skb_dst_set_noref(skb, &rt->dst);

    /* 2. Check if fragmentation needed */
    /* If skb->len > MTU and DF bit set → send ICMP frag-needed, return EMSGSIZE */

    /* 3. Prepend IP header */
    skb_push(skb, sizeof(struct iphdr));
    skb_reset_network_header(skb);
    iph = ip_hdr(skb);

    /* 4. Fill IP header fields */
    *((__be16 *)iph) = htons((4 << 12) | (5 << 8) | (inet->tos & 0xff));
    /* ↑ version=4, IHL=5 (20 bytes, no options), DSCP+ECN */
    iph->tot_len  = htons(skb->len);
    iph->id       = htons(atomic_inc_return(&inet->inet_id));
    iph->frag_off = htons(IP_DF); /* Don't Fragment by default */
    iph->ttl      = ip_select_ttl(inet, &rt->dst);
    iph->protocol = sk->sk_protocol; /* IPPROTO_TCP=6, IPPROTO_UDP=17 */
    iph->saddr    = fl4.saddr;
    iph->daddr    = fl4.daddr;
    ip_select_ident_segs(net, skb, sk, skb_shinfo(skb)->gso_segs ?: 1);

    /* 5. IP checksum (header only, not payload) */
    iph->check = 0;
    iph->check = ip_fast_csum((unsigned char *)iph, iph->ihl);
    /* Or: ip_summed = CHECKSUM_PARTIAL if NIC handles it */

    /* 6. Netfilter OUTPUT hook (iptables OUTPUT chain / nftables) */
    /* 7. Hand to ip_output() */
    return NF_HOOK(NFPROTO_IPV4, NF_INET_LOCAL_OUT,
                   net, sk, skb, NULL, rt->dst.dev,
                   ip_output);   /* → dst_output() → ip_finish_output() */
}

/* ip_output() — called after NF_INET_LOCAL_OUT hook */
int ip_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct net_device *dev = skb_dst(skb)->dev;

    skb->dev      = dev;
    skb->protocol = htons(ETH_P_IP);

    /* Netfilter POSTROUTING hook */
    return NF_HOOK_COND(NFPROTO_IPV4, NF_INET_POST_ROUTING,
                        net, sk, skb, NULL, dev,
                        ip_finish_output,
                        !(IPCB(skb)->flags & IPSKB_REROUTED));
}

int ip_finish_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    /* GSO: if skb is larger than MSS, split here for devices without TSO */
    if (skb_is_gso(skb))
        return ip_finish_output_gso(net, sk, skb, mtu);

    /* Fragmentation if skb->len > MTU */
    if (skb->len > ip_skb_dst_mtu(sk, skb))
        return ip_fragment(net, sk, skb, mtu, ip_finish_output2);

    return ip_finish_output2(net, sk, skb);
}

/* ip_finish_output2() — ARP resolution and neighbor subsystem */
static int ip_finish_output2(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct dst_entry *dst = skb_dst(skb);
    struct neighbour *neigh;

    /* Neighbor (ARP) lookup — fills in dst MAC address */
    neigh = ip_neigh_for_gw(rt, skb, &is_v6gw);
    /* If ARP not resolved, queue packet and send ARP request */
    /* When ARP resolves: neigh_output() is called */

    return neigh_output(neigh, skb, is_v6gw);
    /* → dev_queue_xmit() */
}
```

### 7.2 IP Header Structure

```c
/* include/uapi/linux/ip.h */
struct iphdr {
#if defined(__LITTLE_ENDIAN_BITFIELD)
    __u8    ihl:4,       /* Internet Header Length (in 32-bit words) */
            version:4;   /* IP version = 4 */
#elif defined(__BIG_ENDIAN_BITFIELD)
    __u8    version:4,
            ihl:4;
#endif
    __u8    tos;         /* Type of Service / DSCP+ECN */
    __be16  tot_len;     /* Total length including header */
    __be16  id;          /* Identification (for fragmentation) */
    __be16  frag_off;    /* Fragment offset + flags (DF, MF) */
    __u8    ttl;         /* Time To Live */
    __u8    protocol;    /* Next layer: 6=TCP, 17=UDP, 1=ICMP, 47=GRE, 50=ESP */
    __sum16 check;       /* Header checksum */
    __be32  saddr;       /* Source IP address */
    __be32  daddr;       /* Destination IP address */
    /* Options follow if ihl > 5 */
};
/* Total: 20 bytes minimum */
```

### 7.3 Routing: FIB and Route Cache

```c
/* net/ipv4/route.c, net/ipv4/fib_trie.c */

/* Route lookup: ip_route_output_flow() */
/* Uses the Forwarding Information Base (FIB) trie */
/* Result: struct rtable (contains next-hop, device, neighbour entry) */

struct rtable {
    struct dst_entry    dst;         /* generic destination cache entry */
    int                 rt_genid;
    unsigned int        rt_flags;    /* RTCF_LOCAL, RTCF_BROADCAST, RTCF_MULTICAST */
    __u16               rt_type;     /* RTN_UNICAST, RTN_LOCAL, RTN_BROADCAST */
    __u8                rt_tos;
    __u8                rt_scope;
    u8                  rt_gw_family;
    union { __be32 rt_gw4; struct in6_addr rt_gw6; }; /* next hop GW */
};

struct dst_entry {
    struct net_device   *dev;       /* output device */
    struct dst_ops      *ops;       /* dst_output function pointer */
    unsigned long       _metrics;
    unsigned long       expires;
    struct neighbour    *neighbour; /* ARP cache entry */
    int                 (*output)(struct net *, struct sock *, struct sk_buff *);
    /* output = ip_output for unicast */
};
```

### 7.4 ARP — Address Resolution Protocol

```c
/* net/ipv4/arp.c */

/* ARP packet format: include/uapi/linux/if_arp.h */
struct arphdr {
    __be16  ar_hrd;     /* hardware type: 1 = Ethernet */
    __be16  ar_pro;     /* protocol type: 0x0800 = IPv4 */
    unsigned char ar_hln; /* hardware address length: 6 (MAC) */
    unsigned char ar_pln; /* protocol address length: 4 (IPv4) */
    __be16  ar_op;      /* operation: 1=REQUEST, 2=REPLY */
    /* Followed by: sender HA, sender PA, target HA, target PA */
};

/* ARP cache = neighbour table */
/* struct neighbour: net/core/neighbour.c */
/* Lookup: neigh_lookup(&arp_tbl, &next_hop_ip, dev) */
/* If STALE/INCOMPLETE: arp_send() broadcasts ARP request */
/* On ARP reply: neigh_update() sets ha (hardware/MAC address) */
```

---

## 8. Netfilter / eBPF Hook Plane

### 8.1 Netfilter Hook Points

```c
/* include/uapi/linux/netfilter.h, net/netfilter/ */

/* IPv4 hook points (called via NF_HOOK macro): */
/* NF_INET_PRE_ROUTING    -- on RX, before routing decision */
/* NF_INET_LOCAL_IN       -- on RX, for local delivery */
/* NF_INET_FORWARD        -- on RX, for forwarded packets */
/* NF_INET_LOCAL_OUT      -- on TX, after socket output */
/* NF_INET_POST_ROUTING   -- on TX, after routing decision */

/* Hook return values: */
#define NF_DROP         0  /* drop the packet */
#define NF_ACCEPT       1  /* continue processing */
#define NF_STOLEN       2  /* hook consumed the packet */
#define NF_QUEUE        3  /* queue to userspace (nfqueue) */
#define NF_REPEAT       4  /* call hook again */
#define NF_STOP         5  /* like ACCEPT but don't continue hook traversal */

/* Hook registration: */
static const struct nf_hook_ops ipv4_conntrack_ops[] = {
    {
        .hook       = ipv4_conntrack_in,       /* hook function */
        .pf         = NFPROTO_IPV4,
        .hooknum    = NF_INET_PRE_ROUTING,
        .priority   = NF_IP_PRI_CONNTRACK,     /* priority among hooks */
    },
    /* ... */
};

/* net/netfilter/nf_tables_core.c — nftables */
/* net/ipv4/netfilter/ip_tables.c  — iptables */
```

### 8.2 Connection Tracking (conntrack)

```c
/* net/netfilter/nf_conntrack_core.c */
/* Every packet in NF_INET_PRE_ROUTING passes through nf_conntrack_in() */
/* Creates/finds struct nf_conn for this 5-tuple (src_ip, dst_ip, src_port, dst_port, proto) */

struct nf_conn {
    struct nf_conntrack ct_general; /* reference count */
    spinlock_t          lock;
    u16                 cpu;
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];
    /* tuplehash[ORIGINAL] = original direction (client → server) */
    /* tuplehash[REPLY]    = reply direction (server → client) */
    unsigned long       status;     /* IPS_CONFIRMED, IPS_SEEN_REPLY, IPS_ASSURED */
    possible_net_t      ct_net;
    struct nf_ct_ext    *ext;       /* extension: NAT, helpers, labels */
    union nf_conntrack_proto proto; /* TCP state, UDP timeout */
};
```

### 8.3 eBPF TC (Traffic Control) Programs

```c
/* eBPF programs can attach at tc ingress/egress hooks */
/* Access skb via struct __sk_buff (ABI-stable view of sk_buff) */

/* Example BPF program: drop TCP RST packets */
SEC("tc")
int tc_drop_rst(struct __sk_buff *skb)
{
    void *data_end = (void *)(long)skb->data_end;
    void *data     = (void *)(long)skb->data;
    struct ethhdr *eth = data;

    if (eth + 1 > data_end) return TC_ACT_OK;
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return TC_ACT_OK;

    struct iphdr *ip = data + sizeof(*eth);
    if (ip + 1 > data_end) return TC_ACT_OK;
    if (ip->protocol != IPPROTO_TCP) return TC_ACT_OK;

    struct tcphdr *tcp = data + sizeof(*eth) + ip->ihl * 4;
    if (tcp + 1 > data_end) return TC_ACT_OK;
    if (tcp->rst) return TC_ACT_SHOT; /* drop */

    return TC_ACT_OK;
}

/* TC actions: TC_ACT_OK (pass), TC_ACT_SHOT (drop),
               TC_ACT_REDIRECT (to other dev), TC_ACT_STOLEN (consumed by BPF) */
```

---

## 9. L2 — Data Link Layer: Ethernet Framing

### 9.1 Ethernet Header

**Kernel source:** `net/ethernet/eth.c`, `include/uapi/linux/if_ether.h`

```c
/* include/uapi/linux/if_ether.h */
struct ethhdr {
    unsigned char   h_dest[ETH_ALEN];   /* destination MAC address (6 bytes) */
    unsigned char   h_source[ETH_ALEN]; /* source MAC address (6 bytes) */
    __be16          h_proto;             /* Ethertype: ETH_P_IP=0x0800,
                                                       ETH_P_IPV6=0x86DD,
                                                       ETH_P_ARP=0x0806,
                                                       ETH_P_8021Q=0x8100 (VLAN) */
};
/* Total: 14 bytes */

/* 802.1Q VLAN tag inserted after src MAC and before ethertype: */
struct vlan_hdr {
    __be16          h_vlan_TCI;          /* Priority (3) + DEI (1) + VID (12) */
    __be16          h_vlan_encapsulated_proto; /* actual ethertype */
};
/* Total: 4 bytes. Full VLAN Ethernet header = 18 bytes */
```

### 9.2 Ethernet Header Insertion

```c
/* net/ethernet/eth.c */
int eth_header(struct sk_buff *skb, struct net_device *dev,
               unsigned short type, const void *daddr,
               const void *saddr, unsigned int len)
{
    struct ethhdr *eth = skb_push(skb, ETH_HLEN); /* prepend 14 bytes */
    /* ETH_HLEN = 14 */

    if (type != ETH_P_802_3 && type != ETH_P_802_2)
        eth->h_proto = htons(type);
    else
        eth->h_proto = htons(len);

    /* Fill destination MAC from ARP/neighbour cache */
    if (daddr) {
        memcpy(eth->h_dest, daddr, ETH_ALEN);
    } else {
        /* Unknown: set to broadcast, ARP will fill it later */
        eth_broadcast_addr(eth->h_dest);
    }

    /* Source MAC = device MAC address */
    if (saddr)
        memcpy(eth->h_source, saddr, ETH_ALEN);
    else
        memcpy(eth->h_source, dev->dev_addr, ETH_ALEN);

    return ETH_HLEN;
}
```

### 9.3 VLAN Handling

```c
/* net/8021q/vlan_core.c */
/* VLAN can be: */
/* 1. Software-inserted by kernel before driver sees skb */
/* 2. Offloaded to NIC hardware (NIC inserts/strips VLAN tag) */

/* For HW offload: skb->vlan_tci is set, NIC inserts the 4-byte tag */
/* net/core/dev.c — vlan_put_tag() for software path */
static inline struct sk_buff *vlan_put_tag(struct sk_buff *skb,
                                            __be16 vlan_proto, u16 vlan_tci)
{
    struct vlan_hdr *vhdr;
    skb = skb_cow_head(skb, VLAN_HLEN);
    vhdr = skb_push(skb, VLAN_HLEN);       /* prepend 4 bytes */
    vhdr->h_vlan_TCI = htons(vlan_tci);
    vhdr->h_vlan_encapsulated_proto = skb->protocol;
    skb->protocol = vlan_proto;
    return skb;
}
```

### 9.4 Ethernet Receive Path (L2 demux)

```c
/* net/core/dev.c — netif_receive_skb_internal() */
static int __netif_receive_skb_core(struct sk_buff **pskb, bool pfmemalloc,
                                     struct packet_type **ppt_prev)
{
    struct sk_buff *skb = *pskb;
    struct packet_type *ptype, *pt_prev;

    /* 1. Update statistics */
    net_timestamp_check(!READ_ONCE(netdev_tstamp_prequeue), skb);

    /* 2. Handle VLAN stripping (if not done by NIC) */
    if (skb_vlan_tag_present(skb))
        vlan_do_receive(&skb);

    /* 3. Deliver to raw sockets (AF_PACKET / tcpdump hooks) */
    list_for_each_entry_rcu(ptype, &ptype_all, list) {
        /* deliver_skb() to AF_PACKET sockets */
    }

    /* 4. Demux by L3 protocol (skb->protocol) */
    type = skb->protocol;
    list_for_each_entry_rcu(ptype, &ptype_base[ntohs(type) & PTYPE_HASH_MASK], list) {
        if (ptype->type == type && ptype->dev == skb->dev) {
            /* For ETH_P_IP: ip_rcv() */
            /* For ETH_P_ARP: arp_rcv() */
            /* For ETH_P_IPV6: ipv6_rcv() */
            deliver_skb(skb, ptype, orig_dev);
        }
    }
}

/* ip_rcv() entry point: net/ipv4/ip_input.c */
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    /* Validate IP header: version, checksum, length */
    /* Netfilter PRE_ROUTING hook */
    /* ip_rcv_finish() → routing decision → local delivery or forward */
}
```

---

## 10. Network Device Abstraction (`struct net_device`)

**Kernel source:** `include/linux/netdevice.h`, `net/core/dev.c`

```c
/* include/linux/netdevice.h — abbreviated */
struct net_device {
    char                name[IFNAMSIZ];  /* "eth0", "ens3", "bond0" */
    unsigned long       mem_end;
    unsigned long       mem_start;
    unsigned long       base_addr;
    unsigned long       state;           /* __LINK_STATE_START, etc. */
    struct list_head    dev_list;

    /* --- TX/RX stats --- */
    struct pcpu_sw_netstats __percpu *tstats;

    /* --- Capabilities / features --- */
    netdev_features_t   features;       /* NETIF_F_* bitmask */
    netdev_features_t   hw_features;    /* what NIC supports */
    netdev_features_t   wanted_features;
    /* Key features:
     * NETIF_F_HW_CSUM     -- hardware checksum
     * NETIF_F_SG          -- scatter-gather DMA
     * NETIF_F_TSO         -- TCP segmentation offload
     * NETIF_F_TSO6        -- TCP segmentation offload for IPv6
     * NETIF_F_GSO_GRE     -- GRE GSO
     * NETIF_F_GRO         -- generic receive offload
     * NETIF_F_RXHASH      -- RSS hash in hardware
     * NETIF_F_HW_VLAN_CTAG_TX/RX -- VLAN offload
     * NETIF_F_RXCSUM      -- RX checksum offload
     */

    /* --- MTU --- */
    unsigned int        mtu;             /* default 1500 for Ethernet */
    unsigned int        min_mtu;
    unsigned int        max_mtu;

    /* --- MAC address --- */
    unsigned char       dev_addr[MAX_ADDR_LEN]; /* 6 bytes for Ethernet */
    unsigned char       broadcast[MAX_ADDR_LEN];

    /* --- Device operations vtable --- */
    const struct net_device_ops *netdev_ops;
    const struct ethtool_ops    *ethtool_ops;

    /* --- TX queues (multi-queue support) --- */
    unsigned int        num_tx_queues;
    unsigned int        real_num_tx_queues;
    struct netdev_queue *_tx;  /* array of TX queues */

    /* --- RX queues --- */
    unsigned int        num_rx_queues;
    unsigned int        real_num_rx_queues;
    struct rx_queue_attribute *rx_queue_attrs;

    /* --- qdisc (traffic control) --- */
    struct Qdisc        *qdisc;          /* root qdisc (e.g., pfifo_fast, htb) */
    struct Qdisc        *qdisc_sleeping; /* qdisc being replaced */
};

/* Device operations vtable */
struct net_device_ops {
    int         (*ndo_open)(struct net_device *dev);
    int         (*ndo_stop)(struct net_device *dev);
    netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb, struct net_device *dev);
    /* ↑ Called by dev_queue_xmit() to hand skb to driver */
    u16         (*ndo_select_queue)(struct net_device *dev, struct sk_buff *skb,
                                    struct net_device *sb_dev);
    void        (*ndo_set_rx_mode)(struct net_device *dev);
    int         (*ndo_set_mac_address)(struct net_device *dev, void *addr);
    int         (*ndo_do_ioctl)(struct net_device *dev, struct ifreq *ifr, int cmd);
    int         (*ndo_change_mtu)(struct net_device *dev, int new_mtu);
    void        (*ndo_tx_timeout)(struct net_device *dev, unsigned int txqueue);
    struct      rtnl_link_stats64 *(*ndo_get_stats64)(...);
    int         (*ndo_setup_tc)(struct net_device *dev, ...);    /* for TC/eBPF */
    int         (*ndo_bpf)(struct net_device *dev, struct netdev_bpf *bpf); /* XDP */
    int         (*ndo_xdp_xmit)(struct net_device *dev, int n,
                                 struct xdp_frame **xdp, u32 flags);
    /* ... many more */
};
```

### 10.1 TX Path: `dev_queue_xmit()`

```c
/* net/core/dev.c */
int dev_queue_xmit(struct sk_buff *skb)
{
    struct net_device *dev = skb->dev;
    struct netdev_queue *txq;
    struct Qdisc *q;

    /* 1. Select TX queue (multi-queue NIC) */
    /* Based on skb->hash, CPU affinity, or ndo_select_queue */
    txq = netdev_core_pick_tx(dev, skb, NULL);

    /* 2. Get the qdisc (traffic shaper/scheduler) for this queue */
    q = rcu_dereference_bh(txq->qdisc);

    /* 3. If qdisc is a bypass (pfifo_fast with no backlog): direct TX */
    if (q->flags & TCQ_F_CAN_BYPASS && !qdisc_qlen(q)) {
        /* Direct call to driver's ndo_start_xmit */
        rc = __dev_xmit_skb(skb, q, dev, txq);
    } else {
        /* Enqueue into qdisc, then dequeue and transmit */
        rc = dev_xmit_skb(skb, q, dev, txq);
    }
    return rc;
}

/* Ultimately calls: dev->netdev_ops->ndo_start_xmit(skb, dev) */
```

---

## 11. NIC Driver Ring Buffers and DMA

This is where kernel meets hardware. We'll use the **Intel igb** driver as the canonical example.

**Kernel source:** `drivers/net/ethernet/intel/igb/igb_main.c`, `igb_tx.h`

### 11.1 TX Ring Buffer Structure

```c
/* drivers/net/ethernet/intel/igb/igb.h */

struct igb_tx_buffer {
    union e1000_adv_tx_desc *next_to_watch;
    unsigned long           time_stamp;
    struct sk_buff          *skb;        /* reference to sk_buff being DMA'd */
    unsigned int            bytecount;
    u16                     gso_segs;
    __be16                  protocol;
    DEFINE_DMA_UNMAP_ADDR(dma);          /* DMA address for unmap after TX complete */
    DEFINE_DMA_UNMAP_LEN(len);
};

struct igb_ring {
    struct igb_tx_buffer    *tx_buffer_info; /* array indexed by ring position */
    union {
        /* TX descriptor ring (mapped to NIC via DMA) */
        struct e1000_tx_desc    *tx_desc;
        union e1000_adv_tx_desc *tx_desc_adv;
    };
    void                    *desc;       /* DMA-coherent memory for descriptor ring */
    unsigned long           flags;
    void __iomem            *tail;       /* MMIO register: NIC's tail pointer */
    dma_addr_t              dma;         /* DMA address of descriptor ring base */
    unsigned int            size;        /* byte size of descriptor ring */
    u16                     count;       /* number of descriptors (power of 2) */
    u16                     next_to_use; /* producer index */
    u16                     next_to_clean;/* consumer index (after TX complete) */
    struct net_device       *netdev;
    struct device           *dev;
    /* ... */
};

/* TX descriptor format (82576/igb Advanced TX descriptor) */
union e1000_adv_tx_desc {
    struct {
        __le64  buffer_addr;     /* physical (DMA bus) address of data buffer */
        __le32  cmd_type_len;    /* command, type, length */
        __le32  olinfo_status;   /* offload info + status */
    } read;
    struct {
        __le64  rsvd;
        __le32  nxtseq_seed;
        __le32  status;
    } wb; /* writeback: NIC fills this after TX complete */
};

/* cmd_type_len bits: */
/* ADVTXD_DCMD_EOP  -- end of packet (last descriptor for this frame) */
/* ADVTXD_DCMD_IFCS -- insert FCS (Ethernet CRC) */
/* ADVTXD_DCMD_RS   -- report status (generate TX complete interrupt) */
/* ADVTXD_DCMD_TSE  -- TCP segmentation enable */
/* ADVTXD_DTYP_DATA -- data descriptor */
/* ADVTXD_DTYP_CTXT -- context descriptor (for TSO/checksum params) */
```

### 11.2 TX Path in the igb Driver

```c
/* drivers/net/ethernet/intel/igb/igb_main.c */

static netdev_tx_t igb_xmit_frame(struct sk_buff *skb, struct net_device *netdev)
{
    struct igb_adapter *adapter = netdev_priv(netdev);
    struct igb_ring *tx_ring;

    /* Select TX ring (for multi-queue: based on skb->queue_mapping) */
    tx_ring = igb_tx_queue_mapping(adapter, skb);

    return igb_xmit_frame_ring(skb, tx_ring);
}

netdev_tx_t igb_xmit_frame_ring(struct sk_buff *skb, struct igb_ring *tx_ring)
{
    struct igb_tx_buffer *first;
    int tso;
    u32 tx_flags = 0;
    u16 count = TXD_USE_COUNT(skb_headlen(skb)); /* descriptors for linear data */
    __be16 protocol = vlan_get_protocol(skb);
    u8 hdr_len = 0;

    /* Count descriptors needed for paged (scatter-gather) data */
    count += igb_txd_use_count(skb_shinfo(skb)->nr_frags);

    /* Check ring has enough space */
    if (igb_maybe_stop_tx(tx_ring, count + 4)) {
        /* Ring full: stop queue, driver will restart in TX completion interrupt */
        return NETDEV_TX_BUSY;
    }

    /* Save first buffer slot */
    first = &tx_ring->tx_buffer_info[tx_ring->next_to_use];
    first->skb       = skb;
    first->bytecount = skb->len;
    first->gso_segs  = 1;

    /* VLAN offload */
    if (skb_vlan_tag_present(skb)) {
        tx_flags |= IGB_TX_FLAGS_VLAN;
        tx_flags |= skb_vlan_tag_get(skb) << IGB_TX_FLAGS_VLAN_SHIFT;
    }

    /* Protocol-specific offloads */
    tso = igb_tso(tx_ring, first, &hdr_len);
    /* igb_tso(): if GSO, write Context Descriptor with MSS/hdr_len for TSO */
    /* NIC hardware will split the large segment into MTU-sized frames */

    if (!tso)
        igb_tx_csum(tx_ring, first, tx_flags, protocol);
    /* igb_tx_csum(): set CHECKSUM_PARTIAL offload info in Context Descriptor */

    /* Map skb buffers to DMA addresses and fill TX descriptors */
    igb_tx_map(tx_ring, first, hdr_len);

    return NETDEV_TX_OK;
}

static void igb_tx_map(struct igb_ring *tx_ring, struct igb_tx_buffer *first,
                        const u8 hdr_len)
{
    struct sk_buff *skb = first->skb;
    struct igb_tx_buffer *tx_buffer;
    union e1000_adv_tx_desc *tx_desc;
    struct skb_frag_struct *frag;
    dma_addr_t dma;
    unsigned int data_len, size;
    u32 tx_flags = first->tx_flags;
    u32 cmd_type;
    u16 i = tx_ring->next_to_use;

    tx_desc = IGB_TX_DESC(tx_ring, i);  /* pointer into descriptor ring */

    /* Map the linear (head) portion of skb */
    size  = skb_headlen(skb);
    data_len = skb->data_len; /* paged data */

    dma = dma_map_single(tx_ring->dev,
                          skb->data,    /* kernel virtual address */
                          size,
                          DMA_TO_DEVICE);
    /* dma_map_single():
     * 1. Looks up IOMMU mapping (if IOMMU enabled)
     * 2. Returns DMA bus address (what NIC DMA engine uses)
     * 3. Sets up IOMMU page tables if needed
     * 4. Issues cache flush if architecture requires it (x86 is cache-coherent)
     */

    /* Fill descriptor */
    tx_desc->read.buffer_addr = cpu_to_le64(dma); /* NIC will DMA from this addr */
    tx_desc->read.cmd_type_len = cpu_to_le32(size | IGB_TXD_DCMD);
    first->dma = dma;
    first->len = size;

    /* Advance ring pointer */
    i++;
    if (i == tx_ring->count) i = 0;

    /* Map each scatter-gather fragment (paged data) */
    for (frag = &skb_shinfo(skb)->frags[0]; ; frag++) {
        /* Each fragment is a struct skb_frag_t: page + offset + size */
        dma = skb_frag_dma_map(tx_ring->dev, frag, 0, size, DMA_TO_DEVICE);
        tx_desc = IGB_TX_DESC(tx_ring, i);
        tx_desc->read.buffer_addr = cpu_to_le64(dma);
        /* ... */
        i++;
        if (i == tx_ring->count) i = 0;
        if (data_len == 0) break;
    }

    /* Set EOP (End of Packet) on last descriptor */
    cmd_type |= size | IGB_TXD_DCMD;
    tx_desc->read.cmd_type_len = cpu_to_le32(cmd_type);

    /* Memory barrier: ensure all descriptor writes visible before doorbell */
    wmb();

    /* WRITE DOORBELL: tell NIC the tail pointer has advanced */
    /* NIC sees the new tail and starts DMA'ing the descriptors */
    writel(i, tx_ring->tail);  /* MMIO write to NIC register */
    /* writel() is a barrier on x86, fence on ARM */
}
```

### 11.3 TX Completion (Interrupt/NAPI)

```c
/* After NIC DMA completes TX, NIC writes back to descriptor (RS bit set) */
/* This triggers an MSI-X interrupt → igb_msix_ring() */

static bool igb_clean_tx_irq(struct igb_q_vector *q_vector, int napi_budget)
{
    struct igb_ring *tx_ring = q_vector->tx.ring;
    struct igb_tx_buffer *tx_buffer;
    union e1000_adv_tx_desc *tx_desc;
    unsigned int budget = adapter->tx_work_limit;

    while (budget > 0) {
        tx_desc = IGB_TX_DESC(tx_ring, i);

        /* Check if NIC has written back status (DD = Descriptor Done bit) */
        if (!(tx_desc->wb.status & cpu_to_le32(E1000_TXD_STAT_DD)))
            break;  /* NIC hasn't finished yet */

        tx_buffer = &tx_ring->tx_buffer_info[i];

        /* Unmap DMA addresses (allows kernel to reclaim/move the pages) */
        dma_unmap_single(tx_ring->dev, tx_buffer->dma,
                         tx_buffer->len, DMA_TO_DEVICE);

        /* If last descriptor of packet, free the skb */
        if (tx_buffer->skb) {
            dev_kfree_skb_any(tx_buffer->skb);
            /* → eventually calls skb_release_data() → put_page() on all frags */
            tx_buffer->skb = NULL;
        }

        budget--;
        i++;
        if (i == tx_ring->count) i = 0;
    }

    /* If ring was stopped due to full, restart it */
    if (__netif_subqueue_stopped(netdev, ring_idx) && budget) {
        netif_wake_subqueue(netdev, ring_idx);
    }
}
```

### 11.4 RX Ring Buffer

```c
/* RX descriptor ring: NIC writes received frames here */
/* Driver pre-fills ring with DMA-mapped buffers before NIC uses them */

union e1000_adv_rx_desc {
    struct {
        __le64  buffer_addr;  /* PA of buffer where NIC should DMA received data */
        __le64  hdr_addr;     /* PA for header (split-header mode) */
    } read;
    struct {
        struct {
            union {
                __le32  data;
                struct {
                    __le16  pkt_info;  /* RSS type, packet type */
                    __le16  hdr_info;  /* header length */
                } hs_rss;
            };
            __le16  length;   /* length of received frame */
            __le16  vlan;     /* stripped VLAN tag */
        } lower;
        struct {
            __le32  status_error; /* DD=done, EOP, L4CS=L4 checksum valid */
            __le32  rss;          /* RSS hash value */
        } upper;
    } wb; /* writeback: filled by NIC on frame reception */
};

/* Driver fills RX ring at init time and after each received packet */
static void igb_alloc_rx_buffers(struct igb_ring *rx_ring, u16 cleaned_count)
{
    struct igb_rx_buffer *bi;
    union e1000_adv_rx_desc *rx_desc;

    while (cleaned_count--) {
        bi = &rx_ring->rx_buffer_info[rx_ring->next_to_use];

        /* Allocate a page for the received frame */
        if (!bi->page) {
            bi->page = dev_alloc_pages(igb_rx_pg_order(rx_ring));
            bi->dma  = dma_map_page(rx_ring->dev, bi->page, 0,
                                     igb_rx_pg_size(rx_ring), DMA_FROM_DEVICE);
        }

        /* Fill descriptor with physical address of the buffer */
        rx_desc = IGB_RX_DESC(rx_ring, rx_ring->next_to_use);
        rx_desc->read.buffer_addr = cpu_to_le64(bi->dma);

        /* Advance tail: tells NIC this buffer is ready to receive into */
        rx_ring->next_to_use++;
        if (rx_ring->next_to_use == rx_ring->count)
            rx_ring->next_to_use = 0;
    }

    /* Write tail to NIC (MMIO doorbell) */
    writel(rx_ring->next_to_use, rx_ring->tail);
}
```

---

## 12. L1 — Physical Layer: PHY, SerDes, PCI-e

### 12.1 The PHY (Physical Layer Device)

The PHY chip (or PHY block inside the NIC ASIC) converts between:
- Digital frame bits (from MAC) → analog signals (on the wire)
- Analog signals (from wire) → digital frame bits (to MAC)

```
MAC (in NIC ASIC)
  │  GMII/SGMII/XGMII/KR interface (parallel or serial digital)
  ▼
SerDes (Serializer/Deserializer) — inside NIC ASIC
  │  High-speed serial (PAM4 at 25G/100G, NRZ at 10G)
  ▼
PHY chip (or integrated PHY block)
  │  Performs: PCS (Physical Coding Sublayer), PMA, PMD
  │  Encoding: 8b/10b (1G), 64b/66b (10G+), RS-FEC (100G+)
  │  Auto-negotiation (copper 1G), link training (10G+)
  ▼
Medium (copper twisted pair, multimode/singlemode fiber, DAC/AOC)
```

Kernel PHY management: `drivers/net/phy/` (phylib framework)

```c
/* include/linux/phy.h */
struct phy_device {
    struct mdio_device   mdio;       /* MDIO bus interface */
    struct phy_driver    *drv;       /* PHY driver */
    u32                  phy_id;     /* OUI + model + revision */
    enum phy_state       state;      /* PHY_READY, PHY_UP, PHY_RUNNING, etc. */
    int                  link;       /* 1 = link up */
    int                  speed;      /* 10, 100, 1000, 2500, 5000, 10000 Mbps */
    int                  duplex;     /* DUPLEX_HALF or DUPLEX_FULL */
    int                  pause;      /* flow control: PAUSE frames */
    phy_interface_t      interface;  /* PHY_INTERFACE_MODE_SGMII, _RGMII, _SFI */
    struct net_device    *attached_dev; /* MAC that owns this PHY */
    /* Linked from phy_connect(netdev, "phy_bus_id", handler, interface) */
};

/* PHY operations are via MDIO (Management Data Input/Output) bus */
/* MDIO register read/write: phy_read(phydev, regnum), phy_write(phydev, regnum, val) */
```

### 12.2 PCI-Express Interface

The NIC connects to the CPU via PCIe. This matters for performance:

```
CPU ←[PCIe Root Complex]← PCIe bus ←[NIC endpoint]
       ↓
  IOMMU (Intel VT-d / AMD-Vi)
       ↓
  CPU Memory (DMA target/source)
```

```c
/* NIC driver PCI probe: */
static int igb_probe(struct pci_dev *pdev, const struct pci_device_id *ent)
{
    /* 1. Enable PCI device */
    pci_enable_device_mem(pdev);

    /* 2. Set DMA mask (how many bits of physical address NIC can address) */
    dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    /* 64-bit DMA: NIC can access any physical address */

    /* 3. Request and map MMIO BAR (Base Address Register) */
    /* BAR0 = NIC control registers (descriptor rings, doorbells, etc.) */
    pci_request_mem_regions(pdev, igb_driver_name);
    hw->hw_addr = pci_ioremap_bar(pdev, 0);
    /* Now driver can access NIC registers via readl/writel to hw->hw_addr + offset */

    /* 4. Enable Bus Mastering (allows NIC to initiate DMA) */
    pci_set_master(pdev);

    /* 5. Enable MSI-X interrupts */
    /* Each TX/RX queue gets its own interrupt vector → CPU affinity per queue */
    igb_msix_entries = kcalloc(numvecs, sizeof(struct msix_entry), GFP_KERNEL);
    pci_enable_msix_range(pdev, igb_msix_entries, min_vectors, numvecs);
}
```

### 12.3 DMA and Cache Coherence

```c
/* DMA API: include/linux/dma-mapping.h */

/* Allocate DMA-coherent memory (accessible by both CPU and device) */
/* Used for descriptor rings (read/written by both CPU and NIC frequently) */
void *dma_alloc_coherent(struct device *dev, size_t size,
                          dma_addr_t *dma_handle, gfp_t gfp);
/* Returns kernel virtual address; *dma_handle = DMA bus address */
/* On x86 with IOMMU: may allocate any physical page, IOMMU maps it */
/* On x86 without IOMMU: bus address = physical address (identity mapping) */

/* Map existing memory for DMA (for data buffers: one-shot per packet) */
dma_addr_t dma_map_single(struct device *dev, void *cpu_addr,
                           size_t size, enum dma_data_direction dir);
/* dir: DMA_TO_DEVICE (TX), DMA_FROM_DEVICE (RX), DMA_BIDIRECTIONAL */
/* On architectures without hardware cache coherence: flushes CPU cache */
/* On x86: no-op for the cache flush (hardware maintains coherence) */
/* Returns DMA bus address */

/* Must unmap after DMA completes: */
void dma_unmap_single(struct device *dev, dma_addr_t handle,
                       size_t size, enum dma_data_direction dir);
```

### 12.4 IOMMU

```c
/* drivers/iommu/ — IOMMU subsystem */
/* Intel IOMMU: drivers/iommu/intel/iommu.c */
/* AMD IOMMU: drivers/iommu/amd/iommu.c */

/* IOMMU provides I/O virtual address → physical address translation */
/* Benefits: */
/* 1. DMA protection: NIC cannot access memory outside its IOMMU domain */
/* 2. Allows non-contiguous physical memory to appear contiguous to device */
/* 3. Required for SR-IOV VF isolation in virtualization */

/* iommu_map(): programs IOMMU page tables for a DMA mapping */
/* Example: Physical pages 0x1000, 0x5000, 0x9000 mapped as 0x2000000, 0x2001000, 0x2002000 */
/* NIC sees contiguous IOVA range; CPU memory is scattered */

/* In Linux, the DMA API abstracts this: */
/* dma_map_single() → iommu_dma_map_page() → iommu_map() if IOMMU present */
/*                  → phys_to_dma(phys) if no IOMMU (identity mapping) */
```

---

## 13. NAPI, IRQ Coalescing, and the Receive Path

### 13.1 NAPI (New API)

NAPI is the Linux mechanism for interrupt-driven RX at low load and polling at high load.

**Kernel source:** `net/core/dev.c`, `include/linux/netdevice.h` (struct napi_struct)

```c
/* include/linux/netdevice.h */
struct napi_struct {
    struct list_head    poll_list;      /* on ksoftirqd or NET_RX_SOFTIRQ list */
    unsigned long       state;          /* NAPI_STATE_SCHED, NAPI_STATE_DISABLE */
    int                 weight;         /* max packets to process per poll (64) */
    int                 (*poll)(struct napi_struct *, int); /* driver's poll fn */
    struct net_device   *dev;
    struct gro_list     gro_list;       /* GRO packet list */
    struct sk_buff      *skb;           /* current GRO skb */
    /* ... */
};

/* Flow: */
/* 1. NIC receives frame, DMA's it to pre-allocated RX buffer */
/* 2. NIC asserts MSI-X interrupt → CPU calls igb_msix_ring() */

static irqreturn_t igb_msix_ring(int irq, void *data)
{
    struct igb_q_vector *q_vector = data;

    /* Acknowledge and DISABLE the interrupt (prevent storm) */
    igb_write_itr(q_vector);  /* writes interrupt throttle register */

    /* Schedule NAPI poll (adds to softirq processing) */
    napi_schedule(&q_vector->napi);
    /* napi_schedule sets NAPI_STATE_SCHED and raises NET_RX_SOFTIRQ */

    return IRQ_HANDLED;
}

/* NET_RX_SOFTIRQ runs net_rx_action() on the same CPU */
/* net_rx_action() calls driver's poll function */

static int igb_poll(struct napi_struct *napi, int budget)
{
    struct igb_q_vector *q_vector = container_of(napi, ...);
    bool clean_complete = true;
    int work_done = 0;

    /* TX completion processing (reclaim descriptors) */
    if (q_vector->tx.ring)
        clean_complete = igb_clean_tx_irq(q_vector, budget);

    /* RX processing: up to `budget` packets */
    if (q_vector->rx.ring)
        work_done = igb_clean_rx_irq(q_vector, budget);

    /* If we processed fewer than budget packets: we're done (not overloaded) */
    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        /* Re-enable the interrupt */
        igb_ring_irq_enable(q_vector);
    }
    /* If work_done == budget: ring still has packets, stay in poll mode */
    /* Kernel will call us again via NET_RX_SOFTIRQ without re-enabling IRQ */

    return work_done;
}

static int igb_clean_rx_irq(struct igb_q_vector *q_vector, const int budget)
{
    struct igb_ring *rx_ring = q_vector->rx.ring;
    struct sk_buff *skb = rx_ring->skb;
    u16 cleaned_count = igb_desc_unused(rx_ring);
    unsigned int total_bytes = 0, total_packets = 0;

    while (total_packets < budget) {
        union e1000_adv_rx_desc *rx_desc;
        struct igb_rx_buffer *rx_buffer;

        rx_desc = IGB_RX_DESC(rx_ring, rx_ring->next_to_clean);

        /* Check DD (Descriptor Done) bit — NIC sets this when frame is written */
        if (!igb_test_staterr(rx_desc, E1000_RXD_STAT_DD))
            break;  /* No more received frames */

        /* Memory barrier: ensure we read descriptor AFTER DD bit */
        dma_rmb();

        rx_buffer = igb_get_rx_buffer(rx_ring, size);

        /* Unmap the DMA buffer */
        dma_sync_single_range_for_cpu(rx_ring->dev,
                                       rx_buffer->dma,
                                       rx_buffer->page_offset,
                                       size, DMA_FROM_DEVICE);

        /* Build sk_buff (or reuse existing for multi-descriptor frames) */
        skb = igb_build_skb(rx_ring, rx_buffer, rx_desc);
        /* igb_build_skb: sets skb->data to the DMA buffer, avoids copy */
        /* (page flip: the page is now owned by the skb, not the ring) */

        /* Strip VLAN (or set skb->vlan_tci if NIC stripped it) */
        igb_process_skb_fields(rx_ring, rx_desc, skb);

        /* Hand to network stack */
        napi_gro_receive(&q_vector->napi, skb);
        /* napi_gro_receive → GRO → netif_receive_skb → ip_rcv → ... */

        total_packets++;
        total_bytes += size;

        /* Replenish the RX buffer we just consumed */
        igb_reuse_rx_page(rx_ring, rx_buffer);
    }

    /* Refill RX ring with new buffers */
    igb_alloc_rx_buffers(rx_ring, cleaned_count);

    return total_packets;
}
```

### 13.2 Interrupt Coalescing

```c
/* drivers/net/ethernet/intel/igb/igb_ethtool.c */
/* ethtool -C eth0 rx-usecs 50 rx-frames 0 */
/* → igb_set_coalesce() → writes ITR (Interrupt Throttle Rate) registers */

/* igb ITR: interrupt every N microseconds */
/* ITR=0: interrupt per packet (low latency, high CPU) */
/* ITR=50: interrupt every 50μs (~20K interrupts/sec max at 10Gbps) */
/* Dynamic ITR (LADIS): igb adjusts ITR based on packet rate automatically */

static void igb_update_itr(struct igb_q_vector *q_vector,
                            struct igb_ring_container *ring_container)
{
    unsigned int packets = ring_container->total_packets;
    unsigned int bytes   = ring_container->total_bytes;
    struct igb_adapter *adapter = q_vector->adapter;
    unsigned int itr_val = adapter->rx_itr_setting;

    /* Heuristic: */
    /* High packet rate (small pkts): low ITR (defer less) → lower latency */
    /* High byte rate (large pkts): high ITR (defer more) → higher throughput */
    if (packets < 4) {
        itr_val = IGB_4K_ITR;  /* 4000 interrupts/sec */
    } else if (bytes/packets < 1024) {
        itr_val = IGB_20K_ITR; /* 20000 interrupts/sec */
    } else {
        itr_val = IGB_8K_ITR;  /* 8000 interrupts/sec */
    }
}
```

---

## 14. XDP — eXpress Data Path

XDP is eBPF at the earliest possible point in the RX path — inside the driver's NAPI poll,
before sk_buff allocation. This is the key performance benefit.

**Kernel source:** `net/core/xdp.c`, `include/net/xdp.h`

```c
/* XDP program receives a struct xdp_md (or xdp_buff inside driver) */
/* It can: XDP_PASS, XDP_DROP, XDP_TX (hairpin), XDP_REDIRECT, XDP_ABORTED */

/* Example XDP program: */
SEC("xdp")
int xdp_firewall(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if (eth + 1 > data_end) return XDP_DROP;

    struct iphdr *ip = data + sizeof(*eth);
    if (ip + 1 > data_end) return XDP_DROP;

    /* Drop all ICMP */
    if (ip->protocol == IPPROTO_ICMP) return XDP_DROP;

    /* XDP_TX: send frame back out the same interface (DDoS reflection) */
    /* XDP_REDIRECT: redirect to another CPU queue or interface */
    /* bpf_redirect_map(&xsks_map, ctx->rx_queue_index, 0) → AF_XDP socket */

    return XDP_PASS;
}

/* Driver integration (igb example): */
/* drivers/net/ethernet/intel/igb/igb_main.c */
static struct xdp_buff igb_xdp_buff; /* or allocated per-ring */

static int igb_clean_rx_irq_zc(struct igb_q_vector *q_vector, const int budget)
{
    /* In XDP driver path, called instead of igb_clean_rx_irq() when XDP prog loaded */
    struct xdp_buff xdp;
    u32 act;

    xdp.data     = rx_buffer->addr;     /* pointer to frame data */
    xdp.data_end = xdp.data + size;
    xdp.data_meta = xdp.data;           /* metadata area (before data) */
    xdp.rxq     = &rx_ring->xdp_rxq;   /* ring metadata */
    xdp.frame_sz = igb_rx_frame_truesize(rx_ring, size);

    /* Run the eBPF XDP program */
    act = bpf_prog_run_xdp(rx_ring->xdp_prog, &xdp);

    switch (act) {
    case XDP_PASS:
        /* Convert xdp_buff to sk_buff and continue normal path */
        skb = igb_build_skb(rx_ring, rx_buffer, rx_desc);
        napi_gro_receive(napi, skb);
        break;
    case XDP_TX:
        /* Hairpin TX: send frame back on same NIC */
        igb_xdp_ring_update_tail(tx_ring);
        break;
    case XDP_DROP:
        /* Drop: just recycle the page, no sk_buff ever allocated */
        igb_reuse_rx_page(rx_ring, rx_buffer);
        break;
    case XDP_REDIRECT:
        /* Redirect to another interface, CPU, or AF_XDP socket */
        xdp_do_redirect(rx_ring->netdev, &xdp, rx_ring->xdp_prog);
        break;
    }
}
```

### 14.1 AF_XDP — Zero-Copy to Userspace

```c
/* AF_XDP sockets bypass the kernel stack entirely: */
/* NIC DMA → UMEM (userspace memory) directly */

/* Kernel side: net/xdp/xsk.c */
/* Userspace: shared ring buffers (FILL, COMPLETION, TX, RX) in UMEM */

/* Setup (userspace): */
int xsk_setup(int ifindex, int queue_id)
{
    int fd = socket(AF_XDP, SOCK_RAW, 0);

    /* Allocate UMEM (huge page recommended) */
    struct xdp_umem_reg mr = {
        .addr = (uint64_t)umem_area,   /* mmap'd userspace memory */
        .len  = UMEM_SIZE,
        .chunk_size = FRAME_SIZE,      /* 4096 typically */
        .headroom   = 0,
    };
    setsockopt(fd, SOL_XDP, XDP_UMEM_REG, &mr, sizeof(mr));

    /* Bind to queue */
    struct sockaddr_xdp sxdp = {
        .sxdp_family   = AF_XDP,
        .sxdp_ifindex  = ifindex,
        .sxdp_queue_id = queue_id,
        .sxdp_flags    = XDP_ZEROCOPY,  /* zero-copy: NIC DMA directly into UMEM */
    };
    bind(fd, (struct sockaddr *)&sxdp, sizeof(sxdp));

    /* mmap the ring descriptors */
    /* FILL ring: producer adds free UMEM addresses for NIC to fill */
    /* RX ring: consumer reads received frames (just addresses into UMEM) */
    /* TX ring: producer adds frames to transmit */
    /* COMPLETION ring: consumer reads TX-completed frame addresses */
}
```

---

## 15. Hardware Offloads: TSO, GRO, RSS, Checksum, VLAN

### 15.1 TSO — TCP Segmentation Offload

Without TSO: TCP must produce ≤MSS (1460 byte) segments before handing to IP.
With TSO: TCP produces a "super-segment" (up to 64KB), NIC splits into MSS-sized frames.

```c
/* kernel sets up TSO context descriptor */
/* drivers/net/ethernet/intel/igb/igb_main.c */
static bool igb_tso(struct igb_ring *tx_ring, struct igb_tx_buffer *first,
                     u8 *hdr_len)
{
    struct sk_buff *skb = first->skb;
    u32 vlan_macip_lens, type_tucmd;
    u32 mss_l4len_idx, l4len;

    if (!skb_is_gso(skb)) return false;  /* not a GSO/TSO packet */

    /* GSO: Generic Segmentation Offload (kernel software TSO) */
    /* TSO: NIC hardware segmentation */

    /* Build Context Descriptor (tells NIC about MSS and header lengths) */
    struct e1000_adv_tx_context_desc *context_desc;
    context_desc = IGB_TX_CTXTDESC(tx_ring, i);

    l4len = tcp_hdrlen(skb);
    *hdr_len = skb_transport_offset(skb) + l4len;

    /* MSS = Maximum Segment Size = MTU - IP_hdr - TCP_hdr */
    u16 mss = skb_shinfo(skb)->gso_size;

    context_desc->vlan_macip_lens =
        cpu_to_le32((skb_network_offset(skb)) |
                    (skb_transport_offset(skb) - skb_network_offset(skb)) << 9);
    context_desc->type_tucmd_mlhl =
        cpu_to_le32(E1000_ADVTXD_TUCMD_L4T_TCP |   /* TCP segmentation */
                    E1000_ADVTXD_TUCMD_IPV4);        /* IPv4 checksum */
    context_desc->mss_l4len_idx =
        cpu_to_le32((mss << 16) | (l4len << 8));    /* MSS in bits [31:16] */

    /* NIC will: */
    /* 1. Read the full "super-segment" from memory */
    /* 2. Split into ceil(total_len / mss) segments */
    /* 3. For each segment: update IP.tot_len, IP.id, IP.check, TCP.seq, TCP.check */
    /* 4. Transmit each segment as a complete Ethernet frame */
    return true;
}
```

### 15.2 GRO — Generic Receive Offload

GRO is the kernel software receive counterpart to TSO:

```c
/* net/core/gro.c — kernel 6.x (moved from dev.c in 5.x) */

/* napi_gro_receive() is called by driver for each received frame */
gro_result_t napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
{
    /* GRO checks if this skb can be merged with an existing GRO skb */
    /* Criteria: same 5-tuple, contiguous sequence numbers, same device/VLAN */

    skb_gro_reset_offset(skb, 0);

    /* For TCP: net/ipv4/tcp_offload.c :: tcp4_gro_receive() */
    /* For UDP: net/ipv4/udp_offload.c :: udp4_gro_receive() */

    /* If mergeable: extend existing GRO skb's length, add as fragment */
    /* If not: flush existing GRO skb upward, start new one */

    return dev_gro_receive(napi, skb);
}

/* GRO flush: when max coalescing reached or different flow */
static void napi_gro_flush(struct napi_struct *napi, bool flush_old)
{
    /* Walk gro_list, call napi_skb_finish() for each */
    /* napi_skb_finish() → netif_receive_skb() → ip_rcv() → tcp_v4_rcv() */
    /* TCP receives one large skb instead of many small ones */
    /* This dramatically reduces protocol processing overhead */
}
```

### 15.3 RSS — Receive Side Scaling

```c
/* RSS distributes RX packets across multiple CPU cores by hardware flow hashing */

/* NIC computes Toeplitz hash over:
 * - IPv4: src_ip XOR dst_ip XOR src_port XOR dst_port
 * - IPv6: equivalent
 * Uses a configurable 40-byte secret key (set by driver via ethtool)
 */

/* Hash result → index into Redirection Table (RETA) → RX queue number */
/* Each RX queue has its own MSI-X interrupt → different CPU core */

/* igb: drivers/net/ethernet/intel/igb/igb_main.c */
static void igb_setup_rss(struct igb_adapter *adapter)
{
    /* Set random Toeplitz key */
    get_random_bytes(rsskey, sizeof(rsskey));
    for (i = 0; i < 10; i++)
        wr32(E1000_RSSRK(i), rsskey[i]);

    /* Fill Redirection Table: distribute queues round-robin across CPUs */
    for (i = 0; i < 128; i++) {
        reta |= (adapter->rx_ring[i % adapter->num_rx_queues]->reg_idx) << shift;
        if ((i & 3) == 3) {
            wr32(E1000_RETA(i >> 2), reta);
            reta = 0;
        }
    }

    /* Enable RSS and multi-queue receive */
    mrqc = E1000_MRQC_ENABLE_RSS_4Q;
    mrqc |= E1000_MRQC_RSS_FIELD_IPV4_TCP | E1000_MRQC_RSS_FIELD_IPV4 |
            E1000_MRQC_RSS_FIELD_IPV6 | E1000_MRQC_RSS_FIELD_IPV6_TCP;
    wr32(E1000_MRQC, mrqc);
}
```

### 15.4 Checksum Offload Summary

```
TX Checksum Offload:
  TCP fills pseudo-header checksum (src_ip, dst_ip, proto, len)
  Sets: skb->ip_summed = CHECKSUM_PARTIAL
        skb->csum_start = offset to transport header from skb->head
        skb->csum_offset = offset of checksum field within transport header
  NIC reads these offsets, computes 1's complement over payload, writes final checksum

RX Checksum Offload:
  NIC verifies TCP/UDP checksum on received frame
  Writes result to RX descriptor status bits
  Driver checks: if (rx_desc->wb.upper.status & E1000_RXD_STAT_TCPCS)
      skb->ip_summed = CHECKSUM_UNNECESSARY;  → TCP skips verification
  If checksum error: skb->ip_summed = CHECKSUM_NONE, packet may be dropped
```

---

## 16. Zero-Copy Paths: sendfile, splice, MSG_ZEROCOPY

### 16.1 sendfile()

```c
/* net/socket.c, mm/filemap.c */
/* sendfile(out_fd, in_fd, offset, count) */
/* For file → socket: avoids copy to userspace */

/* Path: */
/* file pages (page cache) → TCP write queue (as page fragments) → NIC DMA */
/* No copy to userspace at all. Page cache pages DMA'd directly by NIC. */

SYSCALL_DEFINE4(sendfile64, int, out_fd, int, in_fd, loff_t __user *, offset, size_t, count)
{
    /* sock_sendpage() → tcp_sendpage() */
    /* tcp_sendpage() adds file page as skb fragment: skb_frag_set_page() */
    /* No memcpy: page reference count incremented, DMA mapping created */
}
```

### 16.2 MSG_ZEROCOPY

```c
/* Linux 4.14+: zero-copy TCP TX for userspace buffers */
/* Application memory DMA'd directly by NIC, no copy to kernel */

/* send(fd, buf, len, MSG_ZEROCOPY) */
/* Kernel pins user pages (get_user_pages()) */
/* Creates DMA mapping directly to userspace physical pages */
/* Notification via error queue (MSG_ERRQUEUE) when NIC completes TX */

/* Requirement: SO_ZEROCOPY socket option must be set */
setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));
send(fd, buf, len, MSG_ZEROCOPY);

/* Poll for completion: */
struct msghdr msg = {0};
struct cmsghdr *cm;
char control[100];
msg.msg_control    = control;
msg.msg_controllen = sizeof(control);
recvmsg(fd, &msg, MSG_ERRQUEUE);
/* Inspect cm for ZEROCOPY_RECV notification with byte range */
```

---

## 17. DPDK Userspace Networking (Bypass)

DPDK bypasses the kernel entirely. The NIC is bound to `vfio-pci` or `uio_pci_generic`,
and the DPDK Poll-Mode Driver (PMD) runs in userspace.

```
Application
  → DPDK PMD (e.g., librte_net_ixgbe)
    → MMIO: ring doorbell write
      → NIC DMA (mapped via VFIO/UIO)

No syscalls, no kernel network stack, no softirq.
```

```c
/* Simplified DPDK TX: */
#include <rte_mbuf.h>
#include <rte_ethdev.h>

/* rte_mbuf: DPDK equivalent of sk_buff */
struct rte_mbuf {
    void                *buf_addr;     /* virtual address of buffer */
    rte_iova_t          buf_iova;      /* physical/IOVA address for DMA */
    uint16_t            data_off;      /* offset from buf_addr to data start */
    uint16_t            nb_segs;       /* number of segments in chain */
    uint16_t            pkt_len;       /* total packet length */
    /* ol_flags: PKT_TX_IPV4 | PKT_TX_TCP_CKSUM | PKT_TX_TCP_SEG etc. */
    uint64_t            ol_flags;
    /* ... */
};

/* PMD TX path (no kernel context switches): */
uint16_t sent = rte_eth_tx_burst(port_id, queue_id, mbufs, nb_pkts);

/* Inside PMD: */
/* 1. Get TX ring pointer from device (mmap'd BAR) */
/* 2. Fill hardware TX descriptors directly (same format as kernel igb driver) */
/* 3. Write doorbell (writel equivalent: iowrite32() to mmap'd BAR) */
/* 4. Poll TX completion ring (no interrupts) */
```

DPDK uses `hugepages` (2MB or 1GB pages) for mbufs to avoid TLB misses during DMA:

```bash
# Setup DPDK hugepages
echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
mount -t hugetlbfs nodev /mnt/huge

# Bind NIC to VFIO
modprobe vfio-pci
dpdk-devbind.py --bind=vfio-pci 0000:00:1f.6  # PCI address
```

---

## 18. Memory Subsystem: NUMA, DMA, IOMMU, Huge Pages

### 18.1 NUMA Awareness

```c
/* On multi-socket servers: PCIe NIC is local to one NUMA node */
/* Allocating memory on the wrong NUMA node → PCIe crossbar traffic → latency */

/* igb allocates per-ring memory on the NUMA node of the PCI device: */
int igb_setup_rx_resources(struct igb_ring *rx_ring)
{
    struct device *dev = rx_ring->dev;
    int orig_node = dev_to_node(dev);  /* NIC's NUMA node */

    /* Descriptor ring: DMA coherent, on NIC's NUMA node */
    rx_ring->desc = dma_alloc_coherent(dev, rx_ring->size,
                                        &rx_ring->dma, GFP_KERNEL);

    /* RX buffer array: normal kernel memory, also on NIC's NUMA node */
    rx_ring->rx_buffer_info = vmalloc_node(size, orig_node);
}

/* Page allocation for RX buffers: prefer NIC's NUMA node */
struct page *page = alloc_pages_node(rx_ring->numa_node,
                                      GFP_ATOMIC | __GFP_NOWARN,
                                      igb_rx_pg_order(rx_ring));
```

### 18.2 Page Recycling

```c
/* igb_reuse_rx_page(): instead of freeing and reallocating pages, */
/* the driver recycles them to avoid memory allocator pressure: */

static void igb_reuse_rx_page(struct igb_ring *rx_ring, struct igb_rx_buffer *old_buff)
{
    struct igb_rx_buffer *new_buff = &rx_ring->rx_buffer_info[rx_ring->next_to_alloc];

    /* Copy page reference to next slot (without calling get_page/put_page) */
    *new_buff = *old_buff;

    /* Advance the next-to-allocate pointer */
    rx_ring->next_to_alloc++;
    if (rx_ring->next_to_alloc == rx_ring->count)
        rx_ring->next_to_alloc = 0;
}
```

---

## 19. Complete Annotated C Implementation

This C program demonstrates the complete outbound encapsulation path using raw sockets,
allowing inspection of every header added at each layer:

```c
/* network_stack_demo.c
 * Demonstrates L2-L7 encapsulation using raw sockets.
 * Build: gcc -O2 -o network_stack_demo network_stack_demo.c
 * Run:   sudo ./network_stack_demo eth0 192.168.1.100 8080
 *
 * This sends a complete Ethernet frame with hand-crafted:
 *   ETH header → IP header → TCP header → payload
 * using AF_PACKET raw socket (bypasses L3/L4 kernel processing).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <errno.h>

/* Network headers — these mirror kernel include/uapi/linux/ structures */
#include <arpa/inet.h>          /* htons, htonl, inet_pton */
#include <net/if.h>             /* if_nametoindex */
#include <netinet/ip.h>         /* struct iphdr */
#include <netinet/tcp.h>        /* struct tcphdr */
#include <net/ethernet.h>       /* struct ether_header, ETH_ALEN */
#include <linux/if_packet.h>    /* AF_PACKET, struct sockaddr_ll */
#include <sys/ioctl.h>          /* SIOCGIFHWADDR, SIOCGIFINDEX */
#include <sys/socket.h>

/* ─────────────────────────────────────────────────────────────────────────
 * Packet structure: this is what sits in memory on the TX path.
 * The kernel sk_buff grows headers backward from tail via skb_push().
 * Here we build it forward into a static buffer (conceptually equivalent).
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * Memory layout (matches sk_buff->data after all headers prepended):
 *
 * +------------------+------------------+------------------+-------------+
 * | struct ethhdr    | struct iphdr     | struct tcphdr    | payload     |
 * | 14 bytes         | 20 bytes         | 20 bytes         | N bytes     |
 * | (L2)             | (L3)             | (L4)             | (L7 data)   |
 * +------------------+------------------+------------------+-------------+
 * ▲ skb->mac_header  ▲ skb->network_hdr ▲ skb->transport_hdr
 */

#pragma pack(push, 1)
struct packet {
    struct ethhdr   eth;    /* L2: 14 bytes */
    struct iphdr    ip;     /* L3: 20 bytes */
    struct tcphdr   tcp;    /* L4: 20 bytes */
    uint8_t         payload[64]; /* L7: application data */
};
#pragma pack(pop)

/* ─────────────────────────────────────────────────────────────────────────
 * Checksum computation — mirrors kernel's ip_fast_csum() and
 * csum_partial() in arch/x86/lib/checksum_32.S
 * ─────────────────────────────────────────────────────────────────────────
 */
static uint16_t checksum(const void *data, size_t len)
{
    const uint16_t *ptr = data;
    uint32_t sum = 0;

    /* Sum all 16-bit words */
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    /* If odd byte, pad with zero */
    if (len == 1)
        sum += *(const uint8_t *)ptr;

    /* Fold 32-bit sum into 16 bits (add carry bits) */
    while (sum >> 16)
        sum = (sum & 0xffff) + (sum >> 16);

    return (uint16_t)~sum;
}

/* TCP/UDP pseudo-header for checksum computation (RFC 793 §3.1) */
struct pseudo_header {
    uint32_t src_addr;
    uint32_t dst_addr;
    uint8_t  zero;       /* always 0 */
    uint8_t  protocol;   /* IPPROTO_TCP = 6 */
    uint16_t tcp_length; /* TCP header + data length */
};

static uint16_t tcp_checksum(const struct iphdr *ip, const struct tcphdr *tcp,
                               const uint8_t *payload, size_t payload_len)
{
    /* Build pseudo-header + TCP header + data in a contiguous buffer */
    size_t tcp_seg_len = sizeof(struct tcphdr) + payload_len;
    size_t buf_len     = sizeof(struct pseudo_header) + tcp_seg_len;
    uint8_t *buf = calloc(1, buf_len);
    if (!buf) return 0;

    struct pseudo_header ph = {
        .src_addr   = ip->saddr,
        .dst_addr   = ip->daddr,
        .zero       = 0,
        .protocol   = IPPROTO_TCP,
        .tcp_length = htons((uint16_t)tcp_seg_len),
    };

    memcpy(buf, &ph, sizeof(ph));
    memcpy(buf + sizeof(ph), tcp, sizeof(struct tcphdr));
    memcpy(buf + sizeof(ph) + sizeof(struct tcphdr), payload, payload_len);

    uint16_t csum = checksum(buf, buf_len);
    free(buf);
    return csum;
}

/* ─────────────────────────────────────────────────────────────────────────
 * L7: Application data (HTTP GET)
 * In a real stack: this lives in user VMA, copied by tcp_sendmsg() via
 * copy_from_iter() into sk_buff data pages.
 * ─────────────────────────────────────────────────────────────────────────
 */
static const char *http_request = "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n";

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <iface> <dst_ip> <dst_port>\n", argv[0]);
        return 1;
    }

    const char *iface    = argv[1];
    const char *dst_ip   = argv[2];
    uint16_t    dst_port = (uint16_t)atoi(argv[3]);

    /* ─────────────────────────────────────────────────────────────────
     * Open AF_PACKET raw socket.
     * In the kernel, this is handled by packet_create() (net/packet/af_packet.c).
     * AF_PACKET bypasses L3/L4; we provide the complete frame manually.
     * ─────────────────────────────────────────────────────────────────
     */
    int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (fd < 0) {
        perror("socket(AF_PACKET)");
        return 1;
    }

    /* Get interface index (used in sockaddr_ll for bind/sendto) */
    struct ifreq ifr = {0};
    strncpy(ifr.ifr_name, iface, IFNAMSIZ - 1);

    if (ioctl(fd, SIOCGIFINDEX, &ifr) < 0) {
        perror("SIOCGIFINDEX");
        return 1;
    }
    int if_index = ifr.ifr_ifindex;

    /* Get source MAC address (kernel: dev->dev_addr) */
    if (ioctl(fd, SIOCGIFHWADDR, &ifr) < 0) {
        perror("SIOCGIFHWADDR");
        return 1;
    }
    uint8_t src_mac[6];
    memcpy(src_mac, ifr.ifr_hwaddr.sa_data, 6);

    /* ─────────────────────────────────────────────────────────────────
     * Build the packet: L2 → L3 → L4 → L7
     * Each step mirrors what the kernel does in:
     *   eth_header() → ip_queue_xmit() → tcp_transmit_skb()
     * ─────────────────────────────────────────────────────────────────
     */
    struct packet pkt = {0};
    size_t payload_len = strlen(http_request);

    /* ── L7: Copy application payload ── */
    /* In kernel: copy_from_iter() in tcp_sendmsg() */
    memcpy(pkt.payload, http_request, payload_len);

    /* ── L4: TCP header (net/ipv4/tcp_output.c::tcp_transmit_skb()) ── */
    pkt.tcp.source  = htons(12345);     /* ephemeral source port */
    pkt.tcp.dest    = htons(dst_port);
    pkt.tcp.seq     = htonl(0x00000001);/* SYN sequence number */
    pkt.tcp.ack_seq = 0;
    pkt.tcp.doff    = 5;                /* Data offset: 5 * 4 = 20 bytes */
    pkt.tcp.syn     = 1;                /* SYN flag for connection initiation */
    pkt.tcp.window  = htons(65535);     /* Maximum receive window */
    pkt.tcp.check   = 0;                /* computed below */
    pkt.tcp.urg_ptr = 0;

    /* ── L3: IP header (net/ipv4/ip_output.c::ip_queue_xmit()) ── */
    pkt.ip.version  = 4;
    pkt.ip.ihl      = 5;                /* 5 * 4 = 20 bytes, no options */
    pkt.ip.tos      = 0;                /* Best-effort (DSCP CS0) */
    pkt.ip.tot_len  = htons(sizeof(struct iphdr) + sizeof(struct tcphdr) + payload_len);
    pkt.ip.id       = htons(0x1234);    /* fragmentation ID */
    pkt.ip.frag_off = htons(IP_DF);     /* Don't Fragment */
    pkt.ip.ttl      = 64;               /* hop limit */
    pkt.ip.protocol = IPPROTO_TCP;
    pkt.ip.check    = 0;                /* computed below */
    pkt.ip.saddr    = inet_addr("192.168.1.1"); /* source (would be from routing) */
    inet_pton(AF_INET, dst_ip, &pkt.ip.daddr);

    /* IP header checksum (covers IP header only, not payload) */
    /* kernel: ip_fast_csum() in ip_output.c */
    pkt.ip.check = checksum(&pkt.ip, sizeof(struct iphdr));

    /* TCP checksum (covers pseudo-header + TCP header + data) */
    /* kernel: tcp_v4_check() → csum_partial() */
    pkt.tcp.check = tcp_checksum(&pkt.ip, &pkt.tcp, pkt.payload, payload_len);

    /* ── L2: Ethernet header (net/ethernet/eth.c::eth_header()) ── */
    /* Destination MAC: would come from ARP cache (neigh table in kernel) */
    /* For demo: use broadcast (kernel would ARP resolve this) */
    memset(pkt.eth.h_dest, 0xff, ETH_ALEN);  /* broadcast */
    memcpy(pkt.eth.h_source, src_mac, ETH_ALEN);
    pkt.eth.h_proto = htons(ETH_P_IP);

    /* ─────────────────────────────────────────────────────────────────
     * Transmit: equivalent to dev_queue_xmit() → ndo_start_xmit()
     * AF_PACKET bypasses qdisc and calls the driver directly via
     * dev_queue_xmit() with skb->protocol = ETH_P_ALL.
     * ─────────────────────────────────────────────────────────────────
     */
    struct sockaddr_ll sa = {
        .sll_family   = AF_PACKET,
        .sll_protocol = htons(ETH_P_IP),
        .sll_ifindex  = if_index,
        .sll_halen    = ETH_ALEN,
    };
    memset(sa.sll_addr, 0xff, ETH_ALEN); /* dst MAC for sockaddr_ll */

    size_t frame_len = sizeof(struct ethhdr) + sizeof(struct iphdr) +
                       sizeof(struct tcphdr) + payload_len;

    ssize_t sent = sendto(fd, &pkt, frame_len, 0,
                           (struct sockaddr *)&sa, sizeof(sa));
    if (sent < 0) {
        perror("sendto");
        return 1;
    }

    printf("Sent %zd bytes\n", sent);
    printf("Frame layout (offsets from start):\n");
    printf("  L2 ETH:  offset=0,   size=%zu\n", sizeof(struct ethhdr));
    printf("  L3 IP:   offset=%zu, size=%zu\n", sizeof(struct ethhdr), sizeof(struct iphdr));
    printf("  L4 TCP:  offset=%zu, size=%zu\n", sizeof(struct ethhdr)+sizeof(struct iphdr), sizeof(struct tcphdr));
    printf("  L7 Data: offset=%zu, size=%zu\n", sizeof(struct ethhdr)+sizeof(struct iphdr)+sizeof(struct tcphdr), payload_len);

    close(fd);
    return 0;
}
```

### 19.1 Kernel Module: sk_buff Inspector

```c
/* skb_inspector.c — loadable kernel module
 * Attaches a netfilter hook to dump skb metadata at each hook point.
 * Build: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 * Load:  insmod skb_inspector.ko
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <linux/inetdevice.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("security-engineer");
MODULE_DESCRIPTION("sk_buff encapsulation inspector");

/* Dump sk_buff header information at each layer */
static void dump_skb(const struct sk_buff *skb, const char *hook_name)
{
    struct iphdr *iph;
    struct tcphdr *tcph;

    /* L2 info: from skb->dev and skb->mac_header */
    if (skb->dev)
        printk(KERN_INFO "[%s] dev=%s protocol=0x%04x len=%u data_len=%u\n",
               hook_name, skb->dev->name, ntohs(skb->protocol),
               skb->len, skb->data_len);

    /* skb layout: head, data, tail, end */
    printk(KERN_INFO "[%s] skb headroom=%u tailroom=%u linear=%u\n",
           hook_name,
           skb_headroom(skb),   /* bytes of headroom before data */
           skb_tailroom(skb),   /* bytes of tailroom after data */
           skb_headlen(skb));   /* bytes in linear region (not paged) */

    /* sk_buff feature flags */
    printk(KERN_INFO "[%s] ip_summed=%d gso_size=%u gso_segs=%u gso_type=0x%x\n",
           hook_name, skb->ip_summed,
           skb_shinfo(skb)->gso_size,
           skb_shinfo(skb)->gso_segs,
           skb_shinfo(skb)->gso_type);

    /* Scatter-gather fragment count */
    printk(KERN_INFO "[%s] nr_frags=%u (paged data fragments)\n",
           hook_name, skb_shinfo(skb)->nr_frags);

    /* L3: IP header */
    if (!skb_network_header_was_set(skb)) return;
    iph = ip_hdr(skb);
    if (!iph) return;

    printk(KERN_INFO "[%s] IP: ver=%u ihl=%u tos=0x%02x tot_len=%u id=0x%04x "
           "frag_off=0x%04x ttl=%u proto=%u saddr=%pI4 daddr=%pI4\n",
           hook_name,
           iph->version, iph->ihl, iph->tos, ntohs(iph->tot_len),
           ntohs(iph->id), ntohs(iph->frag_off), iph->ttl, iph->protocol,
           &iph->saddr, &iph->daddr);

    /* L4: TCP header */
    if (iph->protocol != IPPROTO_TCP) return;
    tcph = tcp_hdr(skb);
    if (!tcph) return;

    printk(KERN_INFO "[%s] TCP: sport=%u dport=%u seq=%u ack=%u "
           "flags=%s%s%s%s%s win=%u check=0x%04x\n",
           hook_name,
           ntohs(tcph->source), ntohs(tcph->dest),
           ntohl(tcph->seq), ntohl(tcph->ack_seq),
           tcph->syn ? "S" : "",
           tcph->ack ? "A" : "",
           tcph->fin ? "F" : "",
           tcph->rst ? "R" : "",
           tcph->psh ? "P" : "",
           ntohs(tcph->window), ntohs(tcph->check));
}

/* Netfilter hook at LOCAL_OUT (TX path, after socket layer) */
static unsigned int nf_local_out_hook(void *priv,
                                       struct sk_buff *skb,
                                       const struct nf_hook_state *state)
{
    dump_skb(skb, "LOCAL_OUT");
    return NF_ACCEPT;
}

/* Netfilter hook at PRE_ROUTING (RX path, before routing) */
static unsigned int nf_pre_routing_hook(void *priv,
                                         struct sk_buff *skb,
                                         const struct nf_hook_state *state)
{
    dump_skb(skb, "PRE_ROUTING");
    return NF_ACCEPT;
}

static struct nf_hook_ops hooks[] = {
    {
        .hook     = nf_pre_routing_hook,
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_PRE_ROUTING,
        .priority = NF_IP_PRI_FIRST,
    },
    {
        .hook     = nf_local_out_hook,
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_LOCAL_OUT,
        .priority = NF_IP_PRI_FIRST,
    },
};

static int __init skb_inspector_init(void)
{
    return nf_register_net_hooks(&init_net, hooks, ARRAY_SIZE(hooks));
}

static void __exit skb_inspector_exit(void)
{
    nf_unregister_net_hooks(&init_net, hooks, ARRAY_SIZE(hooks));
}

module_init(skb_inspector_init);
module_exit(skb_inspector_exit);
```

### 19.2 Makefile for Kernel Module

```makefile
# Makefile
obj-m += skb_inspector.o

KDIR := /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod skb_inspector.ko
	# View output: sudo dmesg -wT | grep -E 'LOCAL_OUT|PRE_ROUTING'

uninstall:
	sudo rmmod skb_inspector
```

---

## 20. Complete Annotated Rust Implementation

### 20.1 Raw Packet Sender (AF_PACKET)

```rust
//! network_stack_demo.rs
//! Demonstrates L2-L7 encapsulation using raw sockets in Rust.
//!
//! Build: cargo build --release
//! Run:   sudo ./target/release/network_stack_demo eth0 192.168.1.100 8080
//!
//! Mirrors what Linux kernel does in:
//!   tcp_transmit_skb()  → ip_queue_xmit()  → eth_header()
//!   → dev_queue_xmit() → igb_xmit_frame()  → DMA descriptor fill

use std::io;
use std::mem;
use std::net::Ipv4Addr;
use std::os::unix::io::RawFd;

// libc for Linux-specific socket constants
use std::ffi::CString;

// ─────────────────────────────────────────────────────────────────────────────
// FFI: Linux socket/network syscalls and structures
// In production: use the `libc` or `nix` crates
// ─────────────────────────────────────────────────────────────────────────────

extern "C" {
    fn socket(domain: i32, type_: i32, protocol: i32) -> i32;
    fn close(fd: i32) -> i32;
    fn ioctl(fd: i32, request: u64, ...) -> i32;
    fn sendto(fd: i32, buf: *const u8, len: usize, flags: i32,
              addr: *const u8, addrlen: u32) -> isize;
    fn htons(hostshort: u16) -> u16;
    fn htonl(hostlong: u32) -> u32;
    fn inet_addr(cp: *const i8) -> u32;
}

const AF_PACKET: i32 = 17;
const SOCK_RAW: i32 = 3;
const ETH_P_ALL: i32 = 0x0003;
const ETH_P_IP: u16 = 0x0800;
const IPPROTO_TCP: u8 = 6;
const SIOCGIFINDEX: u64 = 0x8933;
const SIOCGIFHWADDR: u64 = 0x8927;

/// Internet Checksum — RFC 1071
/// Mirrors kernel's ip_fast_csum() (arch/x86/lib/checksum_32.S)
/// and csum_partial() (include/linux/skbuff.h)
fn internet_checksum(data: &[u8]) -> u16 {
    let mut sum: u32 = 0;
    let mut i = 0;

    // Sum all 16-bit words (big-endian)
    while i + 1 < data.len() {
        let word = (data[i] as u32) << 8 | data[i + 1] as u32;
        sum += word;
        i += 2;
    }

    // Odd byte: pad with zero
    if i < data.len() {
        sum += (data[i] as u32) << 8;
    }

    // Fold 32-bit sum into 16 bits (carry folding)
    while sum >> 16 != 0 {
        sum = (sum & 0xffff) + (sum >> 16);
    }

    !(sum as u16)
}

// ─────────────────────────────────────────────────────────────────────────────
// Packet structures — repr(C, packed) to match wire format exactly
// These mirror kernel include/uapi/linux/ structures.
// ─────────────────────────────────────────────────────────────────────────────

/// L2: Ethernet Header (14 bytes)
/// Kernel: include/uapi/linux/if_ether.h :: struct ethhdr
/// Built by: net/ethernet/eth.c :: eth_header()
#[repr(C, packed)]
struct EthernetHeader {
    h_dest:   [u8; 6],   // Destination MAC (from ARP cache / neighbour table)
    h_source: [u8; 6],   // Source MAC (from dev->dev_addr)
    h_proto:  u16,       // Ethertype (big-endian): 0x0800 = IPv4
}

/// L3: IPv4 Header (20 bytes, no options)
/// Kernel: include/uapi/linux/ip.h :: struct iphdr
/// Built by: net/ipv4/ip_output.c :: ip_queue_xmit()
#[repr(C, packed)]
struct Ipv4Header {
    version_ihl:   u8,   // [7:4]=version=4, [3:0]=IHL=5 (20 bytes)
    tos:           u8,   // DSCP[7:2] + ECN[1:0]
    tot_len:       u16,  // Total length including header (big-endian)
    id:            u16,  // Fragment identification
    frag_off:      u16,  // [15]=reserved, [14]=DF, [13]=MF, [12:0]=offset
    ttl:           u8,   // Time To Live (hop limit)
    protocol:      u8,   // Next layer: 6=TCP, 17=UDP
    check:         u16,  // Header checksum (ones complement)
    saddr:         u32,  // Source IP (big-endian)
    daddr:         u32,  // Destination IP (big-endian)
}

/// L4: TCP Header (20 bytes, no options)
/// Kernel: include/uapi/linux/tcp.h :: struct tcphdr
/// Built by: net/ipv4/tcp_output.c :: tcp_transmit_skb()
#[repr(C, packed)]
struct TcpHeader {
    source:   u16,   // Source port
    dest:     u16,   // Destination port
    seq:      u32,   // Sequence number
    ack_seq:  u32,   // Acknowledgment number
    doff_res: u8,    // [7:4]=data offset, [3:0]=reserved
    flags:    u8,    // [7]=CWR,[6]=ECE,[5]=URG,[4]=ACK,[3]=PSH,[2]=RST,[1]=SYN,[0]=FIN
    window:   u16,   // Receive window size
    check:    u16,   // Checksum (pseudo-header + header + data)
    urg_ptr:  u16,   // Urgent pointer
}

/// TCP/UDP Pseudo-header for checksum computation (RFC 793)
/// Kernel: net/ipv4/tcp.c :: tcp_v4_check()
#[repr(C, packed)]
struct PseudoHeader {
    saddr:      u32,
    daddr:      u32,
    zero:       u8,
    protocol:   u8,
    tcp_length: u16,  // TCP header + data length (big-endian)
}

/// Complete frame: ETH + IP + TCP + payload
/// This is what sits in sk_buff->data after all headers are prepended
/// via skb_push() in the kernel TX path.
#[repr(C, packed)]
struct Frame {
    eth:     EthernetHeader,
    ip:      Ipv4Header,
    tcp:     TcpHeader,
    payload: [u8; 128],
}

fn tcp_checksum(ip: &Ipv4Header, tcp: &TcpHeader, payload: &[u8]) -> u16 {
    let tcp_len = mem::size_of::<TcpHeader>() + payload.len();

    // Build pseudo-header for checksum computation
    // Kernel: tcp_v4_check() builds this and calls csum_partial()
    let pseudo = PseudoHeader {
        saddr:      ip.saddr,
        daddr:      ip.daddr,
        zero:       0,
        protocol:   IPPROTO_TCP,
        tcp_length: u16::to_be(tcp_len as u16),
    };

    // Concatenate pseudo-header + TCP header + payload for checksum
    let mut buf = Vec::with_capacity(
        mem::size_of::<PseudoHeader>() + mem::size_of::<TcpHeader>() + payload.len()
    );

    // Safety: these are packed repr(C) structs; reading as bytes is valid
    let ph_bytes = unsafe {
        std::slice::from_raw_parts(&pseudo as *const _ as *const u8,
                                   mem::size_of::<PseudoHeader>())
    };
    let tcp_bytes = unsafe {
        std::slice::from_raw_parts(tcp as *const _ as *const u8,
                                   mem::size_of::<TcpHeader>())
    };

    buf.extend_from_slice(ph_bytes);
    buf.extend_from_slice(tcp_bytes);
    buf.extend_from_slice(payload);

    internet_checksum(&buf)
}

/// Build complete Ethernet frame with IP/TCP headers
///
/// This function replicates what these kernel functions do:
///   eth_header()        — net/ethernet/eth.c
///   ip_queue_xmit()     — net/ipv4/ip_output.c
///   tcp_transmit_skb()  — net/ipv4/tcp_output.c
///
/// In the kernel, this happens via skb_push() growing headers backward.
/// Here we build them forward into a single struct.
fn build_frame(
    src_mac: [u8; 6],
    dst_ip: Ipv4Addr,
    dst_port: u16,
    payload: &[u8],
) -> (Frame, usize) {
    let payload_len = payload.len().min(128);

    // ── L7 (Application): payload is already in `payload` slice
    // In the kernel: copy_from_iter() in tcp_sendmsg() copies from userspace
    let mut frame = Frame {
        eth: EthernetHeader {
            h_dest:   [0xff; 6],                    // broadcast (ARP would resolve)
            h_source: src_mac,
            h_proto:  ETH_P_IP.to_be(),             // 0x0800 big-endian
        },
        ip: Ipv4Header {
            // version=4, IHL=5 (no options)
            // Kernel sets this as: *((__be16 *)iph) = htons((4 << 12) | (5 << 8) | tos)
            version_ihl:   (4 << 4) | 5,
            tos:           0,
            tot_len:       u16::to_be(
                (mem::size_of::<Ipv4Header>() +
                 mem::size_of::<TcpHeader>() +
                 payload_len) as u16
            ),
            id:            u16::to_be(0x1234),
            frag_off:      u16::to_be(0x4000),      // DF bit set (0x4000 = bit 14)
            ttl:           64,
            protocol:      IPPROTO_TCP,
            check:         0,                        // computed below
            saddr:         u32::from_be_bytes([192, 168, 1, 1]),
            daddr:         u32::from_ne_bytes(dst_ip.octets()),
        },
        tcp: TcpHeader {
            source:   u16::to_be(12345),
            dest:     u16::to_be(dst_port),
            seq:      u32::to_be(1),
            ack_seq:  0,
            // doff = 5 (20 bytes / 4), packed into high nibble
            doff_res: 5 << 4,
            flags:    0x02,  // SYN flag (bit 1)
            window:   u16::to_be(65535),
            check:    0,     // computed below
            urg_ptr:  0,
        },
        payload: [0u8; 128],
    };

    frame.payload[..payload_len].copy_from_slice(&payload[..payload_len]);

    // ── L3: IP header checksum (kernel: ip_fast_csum())
    // Covers only the IP header (20 bytes), not the payload
    let ip_bytes = unsafe {
        std::slice::from_raw_parts(&frame.ip as *const _ as *const u8,
                                   mem::size_of::<Ipv4Header>())
    };
    frame.ip.check = internet_checksum(ip_bytes);

    // ── L4: TCP checksum (kernel: tcp_v4_check() + csum_partial())
    // Covers: pseudo-header (12 bytes) + TCP header (20 bytes) + payload
    // Must be computed after IP checksum (ip.check field is set)
    frame.tcp.check = tcp_checksum(&frame.ip, &frame.tcp, &frame.payload[..payload_len]);

    let total_size = mem::size_of::<EthernetHeader>()
        + mem::size_of::<Ipv4Header>()
        + mem::size_of::<TcpHeader>()
        + payload_len;

    (frame, total_size)
}

fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!("Usage: {} <iface> <dst_ip> <dst_port>", args[0]);
        std::process::exit(1);
    }

    let iface    = &args[1];
    let dst_ip: Ipv4Addr = args[2].parse().expect("invalid IP");
    let dst_port: u16    = args[3].parse().expect("invalid port");

    // ── Open AF_PACKET raw socket
    // Kernel: sys_socket() → packet_create() (net/packet/af_packet.c)
    let fd = unsafe { socket(AF_PACKET, SOCK_RAW, ETH_P_ALL.to_be() as i32) };
    if fd < 0 {
        return Err(io::Error::last_os_error());
    }

    println!("AF_PACKET socket fd={}", fd);
    println!("Sending {} → {}:{}", iface, dst_ip, dst_port);

    // Get source MAC (dev->dev_addr equivalent)
    let src_mac = [0x02, 0x00, 0x00, 0x00, 0x00, 0x01]; // placeholder

    let payload = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n";
    let (frame, total_size) = build_frame(src_mac, dst_ip, dst_port, payload);

    // Print layer sizes (mirrors sk_buff header pointer arithmetic)
    println!("\nPacket layout (sk_buff view):");
    println!("  L2 ETH header: {} bytes at offset 0", mem::size_of::<EthernetHeader>());
    println!("  L3 IP  header: {} bytes at offset {}", mem::size_of::<Ipv4Header>(), mem::size_of::<EthernetHeader>());
    println!("  L4 TCP header: {} bytes at offset {}", mem::size_of::<TcpHeader>(), mem::size_of::<EthernetHeader>()+mem::size_of::<Ipv4Header>());
    println!("  L7 Payload:    {} bytes at offset {}", payload.len(), mem::size_of::<EthernetHeader>()+mem::size_of::<Ipv4Header>()+mem::size_of::<TcpHeader>());
    println!("  Total frame:   {} bytes", total_size);

    // Note: actual sendto requires root + correct sockaddr_ll setup
    // Omitting sendto for safe demo; real implementation uses libc crate
    println!("\nFrame built successfully (sendto omitted in demo; requires root + correct sockaddr_ll)");

    unsafe { close(fd) };
    Ok(())
}
```

### 20.2 eBPF Program in Rust (via aya)

```rust
//! Cargo.toml for eBPF (using aya framework):
//! [dependencies]
//! aya = "0.12"
//! aya-log = "0.2"
//! tokio = { version = "1", features = ["full"] }

//! tc_filter.rs — Rust eBPF TC filter
//! Mirrors what a C eBPF program does at the tc egress hook.
//! This runs inside the kernel at the net/sched boundary.

#![no_std]
#![no_main]

use aya_ebpf::{
    bindings::TC_ACT_OK,
    bindings::TC_ACT_SHOT,
    macros::classifier,
    programs::TcContext,
};
use aya_ebpf::helpers::bpf_printk;
use network_types::{
    eth::{EthHdr, EtherType},
    ip::{IpProto, Ipv4Hdr},
    tcp::TcpHdr,
    udp::UdpHdr,
};

/// TC classifier: drop all packets to port 4444 (C2 exfiltration example)
///
/// Kernel attachment point: net/sched/ (after dev_queue_xmit in egress)
/// or at NAPI ingress (before netif_receive_skb).
///
/// struct __sk_buff is the ABI-stable userspace view of sk_buff:
///   - skb->data offset accessible via ctx.data()
///   - Context validated by BPF verifier (enforces bounds checking)
#[classifier]
pub fn tc_drop_c2(ctx: TcContext) -> i32 {
    match unsafe { try_tc_drop_c2(ctx) } {
        Ok(ret) => ret,
        Err(_) => TC_ACT_OK as i32,  // on error: pass (fail open)
    }
}

unsafe fn try_tc_drop_c2(ctx: TcContext) -> Result<i32, ()> {
    // Load Ethernet header from skb data
    // Kernel: skb->mac_header → struct ethhdr
    let eth = ctx.load::<EthHdr>(0).map_err(|_| ())?;

    // Check EtherType (skb->protocol)
    if eth.ether_type != EtherType::Ipv4 as u16 {
        return Ok(TC_ACT_OK as i32);
    }

    // Load IP header: skb->network_header → struct iphdr
    let ip = ctx.load::<Ipv4Hdr>(EthHdr::LEN).map_err(|_| ())?;

    match ip.proto {
        IpProto::Tcp => {
            // Load TCP header: skb->transport_header → struct tcphdr
            let tcp = ctx.load::<TcpHdr>(
                EthHdr::LEN + Ipv4Hdr::LEN
            ).map_err(|_| ())?;

            let dst_port = u16::from_be(tcp.dest);

            // Drop known C2 port (replace with your blocklist logic)
            if dst_port == 4444 {
                // bpf_printk is rate-limited; safe for production debugging
                bpf_printk!(b"Dropping TCP to port 4444\0");
                return Ok(TC_ACT_SHOT as i32);
            }
        }
        IpProto::Udp => {
            let udp = ctx.load::<UdpHdr>(
                EthHdr::LEN + Ipv4Hdr::LEN
            ).map_err(|_| ())?;

            if u16::from_be(udp.dest) == 53 {
                // Allow DNS always (could be extended for DNS inspection)
                return Ok(TC_ACT_OK as i32);
            }
        }
        _ => {}
    }

    Ok(TC_ACT_OK as i32)
}

// Panic handler required for no_std
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
```

### 20.3 Userspace eBPF Loader (aya)

```rust
//! main.rs — loads and attaches the eBPF TC filter

use aya::{
    programs::{tc::TcAttachType, SchedClassifier},
    Bpf,
};
use std::convert::TryInto;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load compiled eBPF bytecode
    // The BPF verifier in the kernel will verify it on load
    let mut bpf = Bpf::load_file("tc_filter.bpf.o")?;

    // Get the TC classifier program
    let program: &mut SchedClassifier = bpf
        .program_mut("tc_drop_c2")
        .unwrap()
        .try_into()?;

    // Load into kernel: sys_bpf(BPF_PROG_LOAD, ...) → verifier → JIT compile
    program.load()?;

    // Attach to tc egress hook on eth0
    // Kernel: net/sched/cls_bpf.c
    // Equivalent: tc qdisc add dev eth0 clsact
    //             tc filter add dev eth0 egress bpf obj tc_filter.bpf.o sec classifier
    program.attach("eth0", TcAttachType::Egress)?;

    println!("TC filter loaded. Press Ctrl+C to remove.");
    tokio::signal::ctrl_c().await?;

    Ok(())
}
```

---

## 21. Architecture: Full Stack ASCII Diagram

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE L1-L7 DATA ENCAPSULATION PATH                    ║
║                    Linux Kernel + NIC Hardware Deep Dive                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  APPLICATION (RING 3 / USERSPACE)
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Go/Rust/C App                                                           │
  │  "GET / HTTP/1.1\r\n..."  ← L7 Application Data                         │
  │  net.Conn.Write() / send() / sendmsg()                                   │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │  SYSCALL boundary (int 0x80 / SYSCALL insn)
  ════════════════════════════════════════════════════════════════════════════
  KERNEL SPACE (RING 0)         │
                                ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/socket.c                                                            │
  │  sys_sendmsg() → sock_sendmsg() → sock->ops->sendmsg()                  │
  │  struct socket { struct sock *sk; struct proto_ops *ops; }               │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼  [L6: TLS record wrapping if kTLS]
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/tls/tls_sw.c (kTLS)   OR   userspace OpenSSL before syscall        │
  │  TLS Record: [Type(1)][Ver(2)][Len(2)][Encrypted Payload][AEAD Tag]     │
  │  AES-128-GCM / ChaCha20-Poly1305 symmetric encryption                   │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/ipv4/tcp.c :: tcp_sendmsg()              [L4 TCP]                  │
  │                                                                          │
  │  alloc_skb() with MAX_TCP_HEADER headroom reserved                      │
  │  skb_reserve(skb, MAX_TCP_HEADER)  ← moves data ptr forward            │
  │  skb_put(skb, payload_len)         ← appends payload at tail           │
  │  copy_from_iter()                  ← copies from userspace              │
  │                                                                          │
  │  struct sk_buff memory layout after tcp_sendmsg():                      │
  │  [    headroom    ][   PAYLOAD   ][  tailroom  ][skb_shinfo]            │
  │   ▲ head          ▲ data         ▲ tail                                 │
  │                                                                          │
  │  tcp_push() → tcp_write_xmit() → tcp_transmit_skb()                    │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼  skb_push(skb, sizeof(tcphdr))
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/ipv4/tcp_output.c :: tcp_transmit_skb()  [L4 TCP header]          │
  │                                                                          │
  │  struct sk_buff: [headroom][TCP HDR 20B][PAYLOAD][tailroom]             │
  │                              ▲ data (moved back by skb_push)            │
  │                                                                          │
  │  tcphdr: sport|dport|seq|ack_seq|doff|flags|window|check|urg_ptr       │
  │  ip_summed = CHECKSUM_PARTIAL (NIC will complete the checksum)           │
  │                                                                          │
  │  Congestion control: tcp_cwnd_test() — do we have cwnd space?           │
  │  → icsk->icsk_af_ops->queue_xmit(sk, skb, &fl)                        │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼  skb_push(skb, sizeof(iphdr))
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/ipv4/ip_output.c :: ip_queue_xmit()      [L3 IP header]           │
  │                                                                          │
  │  struct sk_buff: [headroom][IP HDR 20B][TCP HDR 20B][PAYLOAD]          │
  │                              ▲ data                                     │
  │                                                                          │
  │  iphdr: ver|ihl|tos|tot_len|id|frag_off|ttl|proto|check|saddr|daddr   │
  │  Route lookup: fib_lookup() → struct rtable → next-hop                 │
  │  ARP: neigh_output() → fills dst MAC in Ethernet header                │
  │                                                                          │
  │  Netfilter hooks (iptables/nftables/eBPF):                             │
  │    NF_INET_LOCAL_OUT  ← OUTPUT chain                                   │
  │    NF_INET_POST_ROUTING ← POSTROUTING chain (NAT, masquerade)          │
  │                                                                          │
  │  ip_finish_output() → ip_finish_output2()                              │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼  skb_push(skb, sizeof(ethhdr))
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/ethernet/eth.c :: eth_header()           [L2 Ethernet header]     │
  │                                                                          │
  │  struct sk_buff: [ETH HDR 14B][IP HDR 20B][TCP HDR 20B][PAYLOAD]      │
  │                   ▲ data (mac_header)                                   │
  │                                                                          │
  │  ethhdr: h_dest[6] | h_source[6] | h_proto(2)                         │
  │  h_dest from neighbour/ARP table  h_source from dev->dev_addr          │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  net/core/dev.c :: dev_queue_xmit()           [Traffic Control]        │
  │                                                                          │
  │  1. netdev_core_pick_tx() → select TX queue by CPU/hash                │
  │  2. qdisc enqueue/dequeue (pfifo_fast, htb, fq, cake, ...)            │
  │  3. dev->netdev_ops->ndo_start_xmit(skb, dev) → NIC driver            │
  └─────────────────────────────┬────────────────────────────────────────────┘
  ════════════════════════════════════════════════════════════════════════════
  NIC DRIVER (KERNEL MODULE)    │
                                ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  drivers/net/ethernet/intel/igb/igb_main.c :: igb_xmit_frame()        │
  │                                                                          │
  │  1. igb_tso(): write Context Descriptor if GSO/TSO                     │
  │     → MSS, header lengths → NIC will segment super-frame               │
  │  2. igb_tx_csum(): set CHECKSUM_PARTIAL offload info                   │
  │  3. igb_tx_map(): DMA map each buffer                                  │
  │                                                                          │
  │  dma_map_single(dev, skb->data, len, DMA_TO_DEVICE)                   │
  │  → IOMMU: maps PA → IOVA (I/O Virtual Address)                        │
  │  → returns dma_addr_t (bus address that NIC DMA engine uses)           │
  │                                                                          │
  │  TX Descriptor Ring (DMA-coherent memory, shared CPU ↔ NIC):          │
  │  ┌──────────────────────────────────────────────────────────┐          │
  │  │ [Desc 0][Desc 1][Desc 2]...[Desc N] (ring, power of 2)  │          │
  │  │ Each descriptor: { buffer_addr: dma_addr_t,              │          │
  │  │                    cmd_type_len: u32 (EOP, TSE, RS),     │          │
  │  │                    olinfo_status: u32 (checksum offload)} │          │
  │  └──────────────────────────────────────────────────────────┘          │
  │                                                                          │
  │  wmb()  ← memory barrier (ensure descriptor writes visible)            │
  │  writel(next_to_use, tx_ring->tail) ← DOORBELL: tell NIC!             │
  │  (MMIO write to NIC BAR0 register via PCIe)                            │
  └─────────────────────────────┬────────────────────────────────────────────┘
  ════════════════════════════════════════════════════════════════════════════
  PCIe BUS                      │  MMIO write propagates via PCIe TLP
                                ▼  (Transaction Layer Packet)
  ════════════════════════════════════════════════════════════════════════════
  NIC HARDWARE (ASICon PCIe card)│
                                ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  NIC DMA Engine                                                          │
  │  Reads tail pointer update → fetches TX descriptors via PCIe DMA read  │
  │  For each descriptor: DMA reads buffer_addr → copies data over PCIe    │
  │                                                                          │
  │  Hardware Offloads (if enabled):                                        │
  │  ┌────────────────────────────────────────────────────────────────┐     │
  │  │ TSO Engine:   read Context Desc → segment large skb into MTU  │     │
  │  │               update TCP seq#, IP id, IP len, IP/TCP checksums │     │
  │  │ Checksum:     complete partial checksum started by TCP/IP      │     │
  │  │ VLAN insert:  prepend 802.1Q tag from skb->vlan_tci           │     │
  │  │ FCS/CRC:     append 4-byte Ethernet CRC (FCS)                 │     │
  │  └────────────────────────────────────────────────────────────────┘     │
  │                                                                          │
  │  NIC MAC (Media Access Controller)                                      │
  │  Frame format on MAC→PHY interface (XGMII/GMII):                       │
  │  [PRE(7B)][SFD(1B)][ETH(14B)][IP(20B)][TCP(20B)][DATA][FCS(4B)][IFG] │
  │   Preamble Start-of-frame Ethernet IP      TCP     App   CRC  Inter-   │
  │             delimiter     header    header header  data       frame gap │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │
                                ▼  Serial bits via SerDes / PHY
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  NIC PHY (Physical Layer Chip / Integrated Block)                       │
  │                                                                          │
  │  Encoding:                                                               │
  │    1Gbps:   8b/10b encoding, 125 MHz symbol rate                        │
  │    10Gbps:  64b/66b encoding, 156.25 MHz × 4 lanes (XLAUI)             │
  │    25Gbps:  64b/66b, single lane, PAM2, 25.78125 GBaud                 │
  │    100Gbps: RS(528,514) FEC, 4×25G lanes (CAUI-4) or PAM4              │
  │                                                                          │
  │  PHY layers (IEEE 802.3):                                               │
  │    PCS (Physical Coding Sublayer) — encode/decode, alignment markers   │
  │    PMA (Physical Medium Attachment) — CDR, equalization                 │
  │    PMD (Physical Medium Dependent) — laser/transceiver for fiber        │
  │                                   — DAC driver for copper              │
  │  Auto-negotiation (1G copper) / Link training (10G+)                   │
  │  PHY management: MDIO bus → driver: drivers/net/phy/ (phylib)          │
  └─────────────────────────────┬────────────────────────────────────────────┘
                                │  Analog electrical / optical signal
                                ▼
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║                    TRANSMISSION MEDIUM (L1)                             ║
  ║  Cat5e/6 UTP (copper) / Single-mode fiber / Multi-mode fiber            ║
  ║  DAC (Direct Attach Copper) / AOC (Active Optical Cable)               ║
  ╚══════════════════════════════════════════════════════════════════════════╝
                                │
                          ══════════════  WIRE / FIBER  ══════════════
                                │
                                ▼  (RX path: reverse of TX)
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  RECEIVE PATH (reverse direction, summarized)                           │
  │                                                                          │
  │  PHY: deserialize bits, decode 8b/10b or 64b/66b, check FEC            │
  │  MAC: detect preamble/SFD, receive frame, strip FCS, validate CRC      │
  │  DMA Engine:                                                            │
  │    read RX ring (pre-filled with DMA-mapped buffers by driver)         │
  │    DMA-write received frame into buffer (DMA_FROM_DEVICE direction)     │
  │    write back RX descriptor (set DD bit, length, offload status)        │
  │    assert MSI-X interrupt                                               │
  │  Driver IRQ handler: igb_msix_ring() → napi_schedule()                │
  │  NAPI poll: igb_clean_rx_irq() — processes up to `budget` frames       │
  │    dma_sync_single_for_cpu()   ← unmap / cache sync                   │
  │    igb_build_skb()             ← build sk_buff pointing to DMA buffer  │
  │    igb_process_skb_fields()    ← set protocol, vlan_tci, ip_summed     │
  │    napi_gro_receive()          ← GRO: merge consecutive TCP segments   │
  │      → netif_receive_skb()     ← protocol demux                        │
  │        → ip_rcv()              ← NF_INET_PRE_ROUTING, routing          │
  │          → tcp_v4_rcv()        ← TCP input processing                  │
  │            → tcp_rcv_established() / tcp_data_queue()                  │
  │              → sk_data_ready() ← wakes up application read()           │
  └──────────────────────────────────────────────────────────────────────────┘

  ════════ WIRE FORMAT: What bytes actually appear on the Ethernet wire ════

  Preamble  SFD   ←────── Ethernet Frame ────────────────────────────────→  IFG
  55 55 55  D5   | DST MAC(6) | SRC MAC(6) | Type(2) |                  | FCS(4)
  55 55 55       |            |            | 0x0800  |                  |
                              [IP Header 20B][TCP Header 20B][Payload N B]

  Total overhead per Ethernet frame: Preamble(7)+SFD(1)+ETH(14)+FCS(4)+IFG(12) = 38 bytes
  For 1460-byte TCP payload: (38+20+20+1460) = 1538 bytes on wire per frame
  Efficiency: 1460/1538 = 94.9%
```

---

## 22. Threat Model and Security Analysis

### 22.1 Attack Surface by Layer

```
Layer  │ Component                 │ Threat                        │ Mitigation
───────┼───────────────────────────┼───────────────────────────────┼───────────────────────────────
L7     │ Application code          │ Logic bugs, injection          │ Fuzz, SAST, sandboxing
L6     │ TLS (OpenSSL/BoringSSL)   │ Protocol downgrade, BEAST,CRIME│ TLS 1.3 only, HSTS, cert pinning
L5     │ Session / Connection state│ Session hijacking, fixation    │ Ephemeral sessions, TCP syncookies
L4     │ TCP stack (net/ipv4/tcp.c)│ SYN flood, RST injection       │ syncookies, RPF, tcp_tw_reuse
L3     │ IP routing (route.c)      │ IP spoofing, route injection   │ Martian filtering, RPKI, BCP38
L3↔L2 │ ARP (net/ipv4/arp.c)      │ ARP poisoning                  │ DARP, static entries, 802.1X
L2     │ Ethernet (net/ethernet/)  │ MAC spoofing, VLAN hopping     │ 802.1X port auth, private VLANs
L2     │ Switching hardware        │ CAM table overflow             │ Port security, DHCP snooping
NIC    │ Driver (igb/mlx5)         │ DMA attack, malicious FW       │ IOMMU, signed FW, Thunderclap
NIC    │ SR-IOV VFs                │ VF isolation bypass            │ IOMMU, VF reset, vfio-pci
PCIe   │ DMA controller            │ DMA attacks (Thunderbolt)      │ IOMMU, VT-d, ACS
PHY/L1 │ Physical medium           │ Tap, fiber tap, EMI            │ Encrypted L4 (TLS/IPsec), physical security
```

### 22.2 SYN Flood Mitigation (TCP Syncookies)

```c
/* net/ipv4/tcp_input.c — syncookies */
/* When sk->sk_max_ack_backlog exceeded AND sysctl_tcp_syncookies enabled: */
/* Server doesn't allocate TCB for SYN; instead computes a cookie: */

/* cookie = SHA1(src_ip, dst_ip, src_port, dst_port, seq, secretkey, timestamp) */
/* Encodes MSS and window scale in cookie bits */
/* On ACK: verify cookie, reconstruct connection state */

/* Enable: echo 2 > /proc/sys/net/ipv4/tcp_syncookies */
/* 2 = unconditional (more secure), 1 = conditional */
```

### 22.3 IOMMU Threat Mitigation

```c
/* Without IOMMU: malicious/buggy NIC firmware can DMA to any physical address */
/* → arbitrary kernel memory read/write */

/* With IOMMU enabled: */
/* NIC can only DMA to addresses mapped in its IOMMU domain */
/* Even if NIC firmware is compromised, it cannot access host memory */
/* outside its allocated IOMMU domain */

/* Enable Intel VT-d: */
/* GRUB: GRUB_CMDLINE_LINUX="intel_iommu=on iommu=strict" */
/* Verify: dmesg | grep -i iommu */
/* cat /proc/interrupts | grep DMAR */

/* iommu=strict: synchronous TLB invalidation (secure but ~1% slower) */
/* iommu=pt: passthrough mode (no protection, for trusted devices only) */
```

### 22.4 BPF Verifier (Security Critical)

```c
/* kernel/bpf/verifier.c — the gatekeeper for all eBPF programs */
/* Performs: */
/* 1. Control flow graph analysis (no unbounded loops) */
/* 2. Register type tracking (typed values: PTR_TO_MAP, PTR_TO_SKB, INT) */
/* 3. Memory access bounds checking */
/* 4. Stack depth analysis */
/* 5. Privilege checks (CAP_BPF or CAP_SYS_ADMIN) */

/* An eBPF program that tries to access skb->data beyond data_end */
/* is REJECTED at load time, before any packet is processed */
/* This prevents kernel memory safety violations in eBPF */
```

### 22.5 Kernel Network Hardening

```bash
# Critical sysctl settings for network hardening

# IP spoofing prevention (Reverse Path Filtering)
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.default.rp_filter=1

# Disable IP source routing
sysctl -w net.ipv4.conf.all.accept_source_route=0

# Disable ICMP redirects (MitM risk)
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0

# SYN flood protection
sysctl -w net.ipv4.tcp_syncookies=2
sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Time-Wait assassination prevention
sysctl -w net.ipv4.tcp_rfc1337=1

# IP fragmentation attack prevention (tune with care)
sysctl -w net.ipv4.ipfrag_max_dist=64

# Disable IPv6 if not used (reduces attack surface)
# sysctl -w net.ipv6.conf.all.disable_ipv6=1

# TCP timestamps (privacy concern: disclose kernel uptime)
sysctl -w net.ipv4.tcp_timestamps=0

# ARP hardening (prevent cross-interface ARP spoofing)
sysctl -w net.ipv4.conf.all.arp_filter=1
sysctl -w net.ipv4.conf.all.arp_ignore=1
sysctl -w net.ipv4.conf.all.arp_announce=2
```

---

## 23. Testing, Fuzzing, and Benchmarking

### 23.1 Protocol Testing with scapy

```python
# Test raw packet handling
from scapy.all import *

# Craft fragmented IP packet (test reassembly)
pkt1 = IP(dst="192.168.1.1", flags="MF", frag=0) / TCP() / ("A" * 1000)
pkt2 = IP(dst="192.168.1.1", frag=125) / ("B" * 100)
send([pkt1, pkt2])

# Test TCP RST injection (verify rp_filter works)
rst = IP(src="1.2.3.4", dst="192.168.1.100") / TCP(dport=80, flags="R")
send(rst)  # should be dropped if rp_filter=1
```

### 23.2 Kernel TCP Stack Fuzzing

```bash
# syzkaller — kernel syscall fuzzer
# https://github.com/google/syzkaller
# Targets: net/ipv4/tcp.c, net/ipv4/ip_output.c, drivers/net/

# Build syzkaller corpus for network syscalls
# syzkaller has built-in network protocol descriptions (sys/linux/socket*.txt)

# Manual: use kcov for coverage-guided kernel fuzzing
echo 1 > /sys/kernel/debug/kcov/enable

# AFL++ with network targets
# Use AFL_NET_PROXY or preload LD_PRELOAD for socket interception
```

### 23.3 Performance Benchmarking

```bash
# iperf3: measure TCP throughput and UDP packet rate
iperf3 -s                                              # server
iperf3 -c 192.168.1.1 -P 4 -t 30 --bidir             # client: 4 parallel, bidirectional

# netperf: lower-level, measures TCP RR (request-response latency)
netserver &
netperf -H 192.168.1.1 -t TCP_RR -l 30               # latency
netperf -H 192.168.1.1 -t TCP_STREAM -l 30            # throughput

# nuttcp: similar to iperf, reports CPU utilization
nuttcp -S                                              # server
nuttcp -r -T 30 192.168.1.1                           # receive mode

# pktgen: kernel packet generator (in-kernel, zero userspace overhead)
modprobe pktgen
# Configure via /proc/net/pktgen/
echo "add_device eth0@0" > /proc/net/pktgen/kpktgend_0
echo "pkt_size 64" > /proc/net/pktgen/eth0@0
echo "count 0" > /proc/net/pktgen/eth0@0       # 0 = unlimited
echo "dst 192.168.1.1" > /proc/net/pktgen/eth0@0
echo "start" > /proc/net/pktgen/pgctrl

# DPDK testpmd: measure NIC raw packet rate
testpmd -l 0-3 -n 4 -- --interactive
# testpmd> start tx_first 32
# testpmd> show port stats all

# ethtool statistics
ethtool -S eth0 | grep -E 'rx_missed|rx_over|tx_dropped|rx_errors'

# Check interrupt affinity and coalescing
ethtool -c eth0        # show coalescing parameters
ethtool -l eth0        # show queue counts
cat /proc/interrupts | grep eth0

# CPU cycles per packet (perf)
perf stat -e cycles,instructions,cache-misses -p $(pgrep ksoftirqd/0)
perf top -g -p $(pgrep ksoftirqd)  # find hot kernel functions

# Trace packet through stack (ftrace)
echo 1 > /sys/kernel/debug/tracing/events/net/enable
cat /sys/kernel/debug/tracing/trace_pipe | grep -E 'net_dev_xmit|netif_receive'
```

### 23.4 Key Performance Metrics and Targets

```
Metric              │ 1GbE        │ 10GbE       │ 25GbE       │ 100GbE
────────────────────┼─────────────┼─────────────┼─────────────┼──────────────
Max pps (64B pkt)   │ 1.488 Mpps  │ 14.88 Mpps  │ 37.2 Mpps   │ 148.8 Mpps
Max throughput      │ 125 MB/s    │ 1.25 GB/s   │ 3.125 GB/s  │ 12.5 GB/s
Latency (DPDK)      │ ~2 μs       │ ~2 μs       │ ~1.5 μs     │ ~1 μs
Latency (kernel)    │ ~20-50 μs   │ ~20-50 μs   │ ~20-50 μs   │ ~20-50 μs
CPU cycles/pkt      │ ~200        │ ~200        │ ~300        │ ~400
IRQ coalescing      │ 50-200 μs   │ 50-100 μs   │ 50 μs       │ 10-50 μs
```

---

## 24. Kernel Source File Reference Index

```
FILE                                    │ PURPOSE
════════════════════════════════════════════════════════════════════════════════

CORE sk_buff AND SOCKET:
include/linux/skbuff.h                  │ struct sk_buff, skb_push/pull/put, GSO types
net/core/skbuff.c                       │ alloc_skb, skb_clone, kfree_skb, GRO
include/linux/net.h                     │ struct socket, proto_ops vtable
include/net/sock.h                      │ struct sock, sk_buff_head
net/core/sock.c                         │ Socket buffer management, sk_alloc

SOCKET LAYER:
net/socket.c                            │ sys_socket, sys_sendmsg, sys_recvmsg
net/ipv4/af_inet.c                      │ inet_stream_ops, inet_dgram_ops
net/ipv4/inet_connection_sock.c         │ Connection setup, accept

TCP:
net/ipv4/tcp.c                          │ tcp_sendmsg, tcp_recvmsg, tcp_close
net/ipv4/tcp_output.c                   │ tcp_transmit_skb, tcp_push, TCP header
net/ipv4/tcp_input.c                    │ tcp_rcv_established, tcp_data_queue
net/ipv4/tcp_timer.c                    │ RTO, keepalive, TIME_WAIT timers
net/ipv4/tcp_ipv4.c                     │ tcp_v4_rcv, tcp_v4_do_rcv, tcp_v4_send_check
include/net/tcp.h                       │ struct tcp_sock, tcp_skb_cb, congestion ops
net/ipv4/tcp_cubic.c                    │ CUBIC congestion control
net/ipv4/tcp_bbr.c                      │ BBR congestion control
include/uapi/linux/tcp.h               │ struct tcphdr (wire format)

UDP:
net/ipv4/udp.c                          │ udp_sendmsg, udp_recvmsg, udp_rcv
include/uapi/linux/udp.h               │ struct udphdr (wire format)

IP (L3):
net/ipv4/ip_output.c                    │ ip_queue_xmit, ip_output, ip_finish_output
net/ipv4/ip_input.c                     │ ip_rcv, ip_local_deliver, ip_rcv_finish
net/ipv4/ip_fragment.c                  │ ip_fragment, ip_defrag
net/ipv4/route.c                        │ ip_route_output_flow, route cache
net/ipv4/fib_trie.c                     │ FIB (Forwarding Information Base) trie
include/uapi/linux/ip.h                │ struct iphdr (wire format)

ARP / NEIGHBOUR:
net/ipv4/arp.c                          │ arp_send, arp_rcv, ARP cache operations
net/core/neighbour.c                    │ neigh_lookup, neigh_output, neigh_update
include/uapi/linux/if_arp.h            │ struct arphdr

ETHERNET (L2):
net/ethernet/eth.c                      │ eth_header, eth_header_parse, eth_type_trans
include/uapi/linux/if_ether.h          │ struct ethhdr, ETH_P_* constants
net/8021q/vlan_core.c                   │ VLAN tag insertion/stripping
net/8021q/vlan_dev.c                    │ VLAN virtual device operations

NETFILTER:
net/netfilter/nf_conntrack_core.c      │ nf_conntrack_in, nf_conn lifecycle
net/netfilter/nf_tables_core.c         │ nftables rule evaluation
net/ipv4/netfilter/ip_tables.c         │ iptables rule evaluation
include/uapi/linux/netfilter.h         │ NF_DROP, NF_ACCEPT, hook points
include/linux/netfilter_ipv4.h         │ NF_INET_* hook point constants

NETWORK DEVICE CORE:
net/core/dev.c                          │ dev_queue_xmit, netif_receive_skb, NAPI
include/linux/netdevice.h              │ struct net_device, net_device_ops, napi_struct
net/sched/                             │ Traffic control (qdisc): sch_pfifo.c, sch_htb.c
net/core/xdp.c                         │ XDP core, xdp_buff, xdp_frame

TLS:
net/tls/tls_main.c                     │ kTLS socket setup, tls_setsockopt
net/tls/tls_sw.c                       │ kTLS software crypto path (TX/RX)
net/tls/tls_device.c                   │ kTLS NIC offload path (TX/RX)

XDP / BPF:
include/net/xdp.h                       │ struct xdp_buff, xdp_frame, XDP actions
net/core/filter.c                       │ BPF filter execution, tc/xdp program hooks
kernel/bpf/verifier.c                   │ BPF verifier (safety enforcement)
net/xdp/xsk.c                          │ AF_XDP socket implementation

NIC DRIVERS:
drivers/net/ethernet/intel/igb/igb_main.c    │ igb: probe, xmit_frame, NAPI poll
drivers/net/ethernet/intel/igb/igb_ethtool.c │ igb: ethtool, coalescing, RSS
drivers/net/ethernet/intel/ixgbe/           │ ixgbe: 10GbE driver (similar structure)
drivers/net/ethernet/mellanox/mlx5/         │ mlx5: ConnectX-4/5/6 driver
drivers/net/ethernet/amazon/ena/            │ ENA: AWS Elastic Network Adapter
drivers/net/virtio_net.c                    │ virtio-net: QEMU/KVM virtual NIC
drivers/net/ethernet/intel/i40e/            │ i40e: Intel XL710 25/40GbE

PHY / PHYLIB:
drivers/net/phy/phy.c                       │ PHY state machine, link monitoring
drivers/net/phy/phy_device.c               │ PHY driver framework
include/linux/phy.h                         │ struct phy_device, phy_interface_t
drivers/net/phy/sfp.c                       │ SFP/SFP+ transceiver management

DMA / IOMMU:
include/linux/dma-mapping.h                │ dma_map_single, dma_alloc_coherent
drivers/iommu/intel/iommu.c               │ Intel VT-d IOMMU
drivers/iommu/amd/iommu.c                 │ AMD-Vi IOMMU
include/linux/iommu.h                      │ iommu_map, iommu_unmap, iommu_domain

MEMORY:
mm/page_alloc.c                             │ alloc_pages, __get_free_pages
mm/slab.c / mm/slub.c                      │ kmalloc, kmem_cache (slab allocator)
include/linux/gfp.h                         │ GFP_KERNEL, GFP_ATOMIC, __GFP_NOWARN
mm/huge_memory.c                            │ Huge page support (for DPDK)

INTERRUPTS:
arch/x86/kernel/irq.c                      │ do_IRQ, IRQ handling (x86)
kernel/irq/manage.c                         │ request_irq, free_irq, IRQ affinity
kernel/softirq.c                            │ NET_RX_SOFTIRQ, NET_TX_SOFTIRQ
```

---

## 25. Next 3 Steps

**Step 1: Run the sk_buff kernel module and trace a real packet.**

```bash
# Build and load the inspector module
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
sudo insmod skb_inspector.ko

# Generate traffic
ping -c 3 8.8.8.8

# Observe the complete sk_buff dump at PRE_ROUTING and LOCAL_OUT
sudo dmesg -T | grep -E 'PRE_ROUTING|LOCAL_OUT' | head -50

# Also: trace at driver level with eBPF kprobes
sudo bpftrace -e '
  kprobe:igb_xmit_frame_ring {
    printf("igb TX: len=%d gso_size=%d nr_frags=%d\n",
           ((struct sk_buff *)arg0)->len,
           ((struct skb_shared_info *)((struct sk_buff *)arg0)->end)->gso_size,
           ((struct skb_shared_info *)((struct sk_buff *)arg0)->end)->nr_frags);
  }'
```

**Step 2: Measure the overhead of each stack layer with perf + flamegraph.**

```bash
# Capture perf data during high-rate network workload
iperf3 -s &
perf record -F 999 -g -p $(pgrep ksoftirqd/0) -- sleep 10

# Generate flamegraph
perf script | stackcollapse-perf.pl | flamegraph.pl > net_flamegraph.svg

# Expected: tcp_transmit_skb, ip_output, dev_queue_xmit should be top callers
# Look for: cache miss rates, lock contention (spin_lock hits)

# Also profile with eBPF/bpftrace for microsecond-resolution per-layer timing
sudo bpftrace -e '
  kprobe:tcp_transmit_skb { @start[tid] = nsecs; }
  kretprobe:tcp_transmit_skb { @tcp_ns = hist(nsecs - @start[tid]); delete(@start[tid]); }
  kprobe:dev_queue_xmit { @dqx_start[tid] = nsecs; }
  kretprobe:dev_queue_xmit { @dqx_ns = hist(nsecs - @dqx_start[tid]); }'
```

**Step 3: Implement XDP-based packet filter and compare throughput with iptables.**

```bash
# Compile XDP program (using clang/LLVM BPF target)
clang -O2 -target bpf -c xdp_filter.c -o xdp_filter.bpf.o

# Load with ip (iproute2)
ip link set eth0 xdp obj xdp_filter.bpf.o sec xdp

# Benchmark: pktgen at 10 Mpps, measure drop rate with XDP vs iptables
# XDP: packets dropped at NAPI poll level (before sk_buff allocation)
# iptables: packets dropped after full sk_buff + IP processing

# Expected result:
# iptables DROP:  ~2-3 Mpps @ 100% CPU (one core)
# XDP_DROP:      ~14 Mpps @ 60% CPU (one core)  -- 5-7x improvement

# Verify XDP drops:
ip -s link show eth0 | grep -A2 xdp

# Unload XDP:
ip link set eth0 xdp off
```

---

## References

- Linux Kernel Source: https://elixir.bootlin.com/linux/latest (cross-reference all files above)
- David S. Miller & Eric Dumazet — Linux networking maintainers, LWN.net articles on sk_buff, GRO, XDP
- Intel 82576 Datasheet — for igb descriptor ring format and register offsets
- RFC 793 (TCP), RFC 791 (IP), RFC 894 (Ethernet), RFC 8446 (TLS 1.3)
- IEEE 802.3 — Ethernet standard (PHY encoding, frame format, auto-negotiation)
- DPDK Documentation: https://doc.dpdk.org/guides/
- BPF and XDP: https://www.kernel.org/doc/html/latest/bpf/index.html
- Brendan Gregg — "Systems Performance" (DMA, NUMA, NIC tuning chapters)
- Jonathan Corbet — "Linux Device Drivers, 3rd Ed." (DMA chapter)
- "The Linux Kernel Networking Implementation" — Rami Rosen (detailed skb walkthrough)
- Netdev conference proceedings — https://www.netdevconf.info (XDP, GRO, kTLS papers)