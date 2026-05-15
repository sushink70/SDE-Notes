# Linux Kernel Network Subsystem: Complete Learning Roadmap & Contributor's Guide

> **Goal**: Build a deep mental model of how Linux processes packets end-to-end,
> understand every major subsystem, and contribute production-quality patches.

---

## Table of Contents

1. [Prerequisites & Mental Model](#1-prerequisites--mental-model)
2. [Linux Kernel Internals Foundations](#2-linux-kernel-internals-foundations)
3. [Network Subsystem Architecture — Big Picture](#3-network-subsystem-architecture--big-picture)
4. [Core Data Structures](#4-core-data-structures)
5. [Socket Layer — The User–Kernel Interface](#5-socket-layer--the-userkernel-interface)
6. [Transport Layer — TCP & UDP Deep Dive](#6-transport-layer--tcp--udp-deep-dive)
7. [IP Layer — Routing, Fragmentation, and Forwarding](#7-ip-layer--routing-fragmentation-and-forwarding)
8. [Netfilter & iptables Subsystem](#8-netfilter--iptables-subsystem)
9. [Network Device Layer & Drivers](#9-network-device-layer--drivers)
10. [NAPI — New API for High-Speed Packet Ingress](#10-napi--new-api-for-high-speed-packet-ingress)
11. [sk_buff — The Packet Buffer in Depth](#11-sk_buff--the-packet-buffer-in-depth)
12. [Complete RX Path — NIC to Userspace](#12-complete-rx-path--nic-to-userspace)
13. [Complete TX Path — Userspace to NIC](#13-complete-tx-path--userspace-to-nic)
14. [Traffic Control & Queuing Disciplines (tc/qdisc)](#14-traffic-control--queuing-disciplines-tcqdisc)
15. [Routing Subsystem Internals](#15-routing-subsystem-internals)
16. [Network Namespaces & Virtualization](#16-network-namespaces--virtualization)
17. [eBPF & XDP — Programmable Networking](#17-ebpf--xdp--programmable-networking)
18. [Kernel Synchronization in Networking](#18-kernel-synchronization-in-networking)
19. [Memory Management in the Network Stack](#19-memory-management-in-the-network-stack)
20. [Kernel Development Workflow](#20-kernel-development-workflow)
21. [Finding & Fixing Bugs — First Contributions](#21-finding--fixing-bugs--first-contributions)
22. [Writing a New Network Feature — End-to-End](#22-writing-a-new-network-feature--end-to-end)
23. [Key Source Files & Where Everything Lives](#23-key-source-files--where-everything-lives)
24. [Essential Reading & Resources](#24-essential-reading--resources)
25. [12-Month Study Plan](#25-12-month-study-plan)

---

## 1. Prerequisites & Mental Model

### 1.1 The Right Mental Model

Before touching a single line of kernel code, you need to rewire how you think
about networking. In userspace, you think in terms of **abstractions**: sockets,
file descriptors, send/recv. In the kernel, you think in terms of:

- **Data pipelines**: a packet is a blob of memory (`sk_buff`) that flows
  through a series of function pointers, hooks, and queues.
- **Layered processing**: each layer examines only its own headers and passes
  the payload down/up.
- **Concurrency everywhere**: packets arrive on multiple CPUs simultaneously.
  Locks, RCU, per-CPU variables, lock-free queues — all are mandatory knowledge.
- **No malloc/free**: you use kernel memory allocators (`kmalloc`, `kzalloc`,
  `vmalloc`, slab caches). No exceptions from stack overflows; kernel stack is 8 KB.
- **No floating point**: the kernel never uses FP. Everything is integer,
  fixed-point, or bit manipulation.
- **No blocking anywhere unexpected**: you must know which contexts can sleep
  and which cannot (interrupt context cannot sleep).

### 1.2 C Language Mastery Required

You need not just C knowledge, but **kernel C** knowledge:

```
Standard C             Kernel C
-----------            --------
malloc/free            kmalloc/kfree, slab allocators
printf                 printk, pr_info, netdev_dbg
NULL pointer crash     BUG_ON(), WARN_ON(), kernel panic
threads                kthreads, workqueues, tasklets
mutexes                spinlocks, rwlocks, mutexes, RCU, seqlocks
errno                  negative errno values returned directly
bool                   explicit int with 0/non-zero convention
```

**Kernel-specific C idioms you must internalize:**

```c
/* Container-of macro — the most important kernel macro */
#define container_of(ptr, type, member) ({          \
    void *__mptr = (void *)(ptr);                   \
    ((type *)(__mptr - offsetof(type, member))); })

/* Usage: given a pointer to list_head inside a struct,
   get back the enclosing struct */
struct net_device *dev = container_of(ptr, struct net_device, dev_list);

/* RCU read-side critical section */
rcu_read_lock();
p = rcu_dereference(gp);   /* safe pointer dereference */
if (p)
    do_something(p->x);
rcu_read_unlock();

/* Linked list manipulation (intrusive linked lists) */
struct list_head my_list = LIST_HEAD_INIT(my_list);
list_add(&entry->list, &my_list);
list_for_each_entry(entry, &my_list, list) { ... }
```

### 1.3 Prerequisite Knowledge Checklist

```
[ ] C programming (pointers, structs, function pointers, bitfields)
[ ] Computer networking (OSI model, TCP/IP, Ethernet, ARP, routing)
[ ] OS concepts (processes, interrupts, system calls, virtual memory)
[ ] Data structures (linked lists, hash tables, trees, queues)
[ ] Basic assembly reading ability (x86-64 or ARM64)
[ ] Git basics
[ ] Linux user-space networking tools (ip, ss, tc, ethtool, netstat)
[ ] Make / Kbuild system basics
[ ] GDB / crash / ftrace basics
```

---

## 2. Linux Kernel Internals Foundations

### 2.1 Kernel Memory Layout

```
Virtual Address Space (64-bit x86-64):

0xFFFFFFFFFFFFFFFF +--------------------------+
                   |  Kernel modules          |
0xFFFFFFFFC0000000 +--------------------------+
                   |  Direct mapping          |
                   |  of physical memory      |
                   |  (physmap)               |
0xFFFF888000000000 +--------------------------+
                   |  vmalloc / ioremap       |
0xFFFFC90000000000 +--------------------------+
                   |  ... (kernel use)        |
0xFFFF000000000000 +--------------------------+
                   |                          |
                   |  (non-canonical hole)    |
                   |                          |
0x00007FFFFFFFFFFF +--------------------------+
                   |  User space              |
                   |  (per-process)           |
0x0000000000000000 +--------------------------+
```

The network stack lives **entirely in kernel virtual address space**. Packet
buffers allocated via `kmalloc` or `alloc_skb` come from the slab/slub allocator
which ultimately maps to physical pages.

### 2.2 Interrupt Handling — Critical for Networking

Packet arrival is driven by hardware interrupts. Understanding interrupt
handling is non-negotiable for networking.

```
Hardware interrupt lifecycle:

NIC receives packet
       |
       v
NIC raises IRQ line
       |
       v
CPU receives interrupt signal
       |
       v
CPU saves registers, switches to interrupt stack
       |
       v
Kernel calls do_IRQ() / handle_irq()
       |
       v
Driver's interrupt handler runs (hardirq context)
    - Acknowledges the interrupt to hardware
    - Schedules NAPI poll (for packet processing)
    - Returns IRQ_HANDLED
       |
       v
Softirq (NET_RX_SOFTIRQ) runs on same CPU
    - NAPI poll reads packets from ring buffer
    - Calls netif_receive_skb()
       |
       v
Packet handed to protocol layers
```

**Interrupt contexts and what you can do:**

```
Context          | Can sleep? | Can use locks? | Stack
-----------------+------------+----------------+--------
Process context  | YES        | All locks      | ~8 KB
Softirq context  | NO         | Spinlocks only | ~8 KB
Hardirq context  | NO         | Spinlocks only | ~4-8 KB
NMI context      | NO         | Almost nothing | tiny
```

### 2.3 Workqueues, Tasklets, Softirqs

The kernel has a deferred execution hierarchy. Networking uses all of them:

```
Deferred Execution Hierarchy:

  HARDIRQ (highest priority, preempts everything)
     |
     | schedules
     v
  SOFTIRQ (runs after hardirq, preempts process)
     |-- NET_RX_SOFTIRQ  (packet receive processing)
     |-- NET_TX_SOFTIRQ  (transmit queue wakeup)
     |-- BLOCK_SOFTIRQ
     |-- TASKLET_SOFTIRQ (tasklets run here)
     v
  WORKQUEUE (kernel threads, can sleep)
     |-- system_wq
     |-- system_highpri_wq
     |-- Networking uses for: DHCP, nl80211 ops, etc.
```

In networking code, `NET_RX_SOFTIRQ` is the most important. It is raised by
`napi_schedule()` inside the driver's interrupt handler and processed by
`net_rx_action()` in the softirq handler.

### 2.4 RCU — Read-Copy-Update

RCU is used **extensively** throughout the network stack for lock-free reads of
frequently-read data structures (routing tables, ARP cache, socket lists).

```
RCU Mental Model:

Reader:                     Writer:
                            
rcu_read_lock()             old_ptr = gp;
p = rcu_dereference(gp)     new_ptr = kmalloc(...);
use(p)                      new_ptr->val = new_val;
rcu_read_unlock()           rcu_assign_pointer(gp, new_ptr);
                            synchronize_rcu(); /* wait for readers */
                            kfree(old_ptr);    /* now safe */

Key guarantee: between rcu_read_lock() and rcu_read_unlock(),
the data pointed to by p WILL NOT be freed.
```

In networking: `rcu_read_lock()` protects reads of `dev->ip_ptr` (in_device),
FIB table lookups, socket lookup tables, neighbour cache entries.

### 2.5 Per-CPU Variables

High-speed packet processing uses per-CPU variables to avoid cache bouncing:

```c
/* Declaration */
DEFINE_PER_CPU(struct softnet_data, softnet_data);

/* Access */
struct softnet_data *sd = this_cpu_ptr(&softnet_data);
sd->total_rx_packets++;

/* The softnet_data per-CPU struct is THE central structure
   for packet ingress on each CPU */
```

---

## 3. Network Subsystem Architecture — Big Picture

### 3.1 Layered Architecture

```
                    USERSPACE
                    
  Application: send()/recv()/read()/write()
                         |
  ===================== syscall boundary ======================
                         |
  +----------------------+----------------------+
  |              SOCKET LAYER (af_*.c)          |
  |   struct socket  <->  struct sock            |
  |   VFS operations mapped to proto_ops         |
  +---------------------++-----------------------+
                         ||
          +==============++===============+
          |    TCP        |    UDP         |   RAW
          | (tcp_*.c)     | (udp.c)        |   etc.
          +==============+================+
                         |
  +----------------------+----------------------+
  |              IP LAYER (ip_*.c)              |
  |   Input: ip_rcv()                           |
  |   Output: ip_output() / ip_queue_xmit()     |
  |   Forward: ip_forward()                     |
  +--------+------------------+-----------------+
           |                  |
    [NETFILTER HOOKS]  [ROUTING SUBSYSTEM]
    PRE_ROUTING        fib_lookup()
    LOCAL_IN           rt_cache
    FORWARD            neighbour/ARP
    LOCAL_OUT
    POST_ROUTING
           |
  +--------+-----------------------------------------+
  |        NETWORK DEVICE LAYER                      |
  |   netif_receive_skb() / dev_queue_xmit()         |
  |   struct net_device  /  net_device_ops           |
  +--------+-----------------------------------------+
           |
  +--------+-----------------------------------------+
  |        DRIVER / NAPI                             |
  |   Ring buffers (RX/TX)                           |
  |   DMA descriptors                                |
  |   Hardware interrupts                            |
  +--------+-----------------------------------------+
           |
    HARDWARE (NIC, PHY, cable)
```

### 3.2 Key Kernel Source Tree Layout

```
linux/
├── net/                        ← ALL networking code
│   ├── core/                   ← Core: dev.c, sock.c, skbuff.c
│   │   ├── dev.c               ← net_device management, rx/tx
│   │   ├── sock.c              ← struct sock lifecycle
│   │   ├── skbuff.c            ← sk_buff allocation/manipulation
│   │   ├── dst.c               ← Destination cache
│   │   ├── filter.c            ← BPF/socket filter
│   │   ├── neighbour.c         ← ARP/neighbour subsystem
│   │   ├── rtnetlink.c         ← Netlink for routing
│   │   └── net_namespace.c     ← Network namespaces
│   ├── ipv4/                   ← IPv4 stack
│   │   ├── ip_input.c          ← ip_rcv(), ip_local_deliver()
│   │   ├── ip_output.c         ← ip_output(), ip_finish_output()
│   │   ├── ip_forward.c        ← ip_forward()
│   │   ├── tcp.c               ← TCP main
│   │   ├── tcp_input.c         ← TCP receive path
│   │   ├── tcp_output.c        ← TCP transmit path
│   │   ├── tcp_timer.c         ← TCP timers (retransmit, keepalive)
│   │   ├── tcp_cong.c          ← Congestion control framework
│   │   ├── udp.c               ← UDP
│   │   ├── raw.c               ← RAW sockets
│   │   ├── arp.c               ← ARP protocol
│   │   ├── fib_trie.c          ← FIB (routing table) LC-trie
│   │   ├── route.c             ← Route lookup and cache
│   │   └── af_inet.c           ← inet socket family
│   ├── ipv6/                   ← IPv6 stack (mirrors ipv4/)
│   ├── netfilter/              ← iptables/nftables
│   ├── sched/                  ← Traffic control (tc/qdisc)
│   │   ├── sch_generic.c       ← Generic qdisc framework
│   │   ├── sch_pfifo.c         ← Simple FIFO qdisc
│   │   ├── sch_htb.c           ← HTB (Hierarchical Token Bucket)
│   │   └── cls_*.c             ← Packet classifiers
│   ├── bridge/                 ← Ethernet bridging
│   ├── wireless/               ← mac80211 wireless stack
│   └── bpf/                    ← BPF/XDP infrastructure
├── drivers/net/                ← NIC drivers
│   ├── ethernet/
│   │   ├── intel/              ← e1000, igb, ixgbe, i40e, ice
│   │   ├── mellanox/           ← mlx4, mlx5
│   │   └── ...
│   └── loopback.c              ← lo device
└── include/
    ├── linux/
    │   ├── skbuff.h            ← sk_buff definition
    │   ├── netdevice.h         ← net_device definition
    │   └── socket.h
    └── net/
        ├── sock.h              ← struct sock definition
        ├── tcp.h
        ├── ip.h
        └── route.h
```

---

## 4. Core Data Structures

### 4.1 struct sk_buff — The Central Packet Structure

`sk_buff` (socket buffer) is **the most important data structure** in the entire
network stack. Every packet in flight is represented by an `sk_buff`. It is
defined in `include/linux/skbuff.h` and is roughly 240 bytes on 64-bit kernels.

```
sk_buff memory layout:

struct sk_buff {
    /* 1. Linked list pointers */
    struct sk_buff  *next, *prev;       /* queue linkage */
    struct sk_buff_head *list;          /* owning queue */

    /* 2. Socket & device */
    struct sock     *sk;                /* owning socket (NULL if forwarding) */
    struct net_device *dev;             /* device packet arrived on or going to */

    /* 3. Timestamps */
    ktime_t          tstamp;

    /* 4. Protocol-specific headers (union) */
    union { struct tcphdr *th; struct udphdr *uh;
            struct icmphdr *icmph; struct iphdr *iph; ... };

    /* 5. Packet data pointers */
    unsigned char   *head;     /* start of allocated buffer */
    unsigned char   *data;     /* start of packet data (moves as headers stripped) */
    unsigned char   *tail;     /* end of packet data */
    unsigned char   *end;      /* end of allocated buffer */

    /* 6. Lengths */
    unsigned int     len;      /* total length of all data */
    unsigned int     data_len; /* amount in frags (for scatter-gather) */
    __u16            mac_len;  /* length of Ethernet header */
    __u16            hdr_len;  /* for cloned skbs */

    /* 7. Checksum state */
    __wsum           csum;
    __u8             ip_summed;  /* CHECKSUM_NONE/UNNECESSARY/COMPLETE/PARTIAL */

    /* 8. Metadata / flags */
    __u16            protocol;      /* L3 protocol (ETH_P_IP etc.) */
    __u8             pkt_type;      /* PACKET_HOST/BROADCAST/MULTICAST/... */
    __u8             nohdr:1;
    __u8             fclone:2;      /* fast clone state */
    __u8             nf_trace:1;    /* netfilter trace */
    ...

    /* 9. Control buffer — 48 bytes, protocol-specific scratch */
    char             cb[48] __aligned(8);
    /* TCP uses this for: tcp_skb_cb with seq, end_seq, ack, flags */
    /* IP uses this for: inet_skb_parm with iif, opt info */

    /* 10. Fragment list (for IP fragmentation) */
    skb_frag_t       frags[MAX_SKB_FRAGS];   /* page fragments */
    struct sk_buff   *frag_list;              /* IP fragment list */

    /* 11. Hash for load balancing */
    __u32            hash;
    __u8             l4_hash:1;
    __u8             sw_hash:1;

    /* 12. Mark for policy routing, firewall */
    __u32            mark;

    /* 13. Queue mapping (for multiqueue NICs) */
    __u16            queue_mapping;
};
```

**The four data pointers:**

```
Allocated buffer (from kmalloc or page pool):

  head                                            end
   |                                               |
   v                                               v
   +-------+---------------------------+-----------+
   | head  | [L2][L3][L4][ PAYLOAD ]  |  tailroom |
   | room  |                           |           |
   +-------+--^------------------+----+-----------+
              |                  |
             data               tail

- skb_push(skb, len): moves data BACKWARD (adds header)
- skb_pull(skb, len): moves data FORWARD (strips header)
- skb_put(skb, len):  moves tail FORWARD (adds to tail)
- skb_trim(skb, len): moves tail BACKWARD (trims tail)
- skb_headroom(skb) = data - head
- skb_tailroom(skb) = end - tail
- skb->len           = tail - data  (for linear skbs)
```

**How headers are built (TX path):**

```
Starting with allocated skb with headroom:

  head     data=tail           end
   |          |                 |
   +----------+-----------------+
   |  (room)  |                 |
   +----------+-----------------+

After skb_push(skb, sizeof(tcphdr)):
  head    data  tail            end
   |       |     |               |
   +-------+-----+---------------+
   | room  | TCP |               |
   +-------+-----+---------------+

After skb_push(skb, sizeof(iphdr)):
  head  data   tail             end
   |     |       |               |
   +-----+-------+---------------+
   |room |IP|TCP |               |
   +-----+-------+---------------+

After skb_push(skb, sizeof(ethhdr)):
  data               tail
   |                   |
   +-------------------+
   |ETH|IP|TCP|PAYLOAD |
   +-------------------+
```

### 4.2 struct net_device — The Network Interface

Defined in `include/linux/netdevice.h`. Represents a network interface (eth0, lo, etc.).

```c
struct net_device {
    char            name[IFNAMSIZ];    /* "eth0", "lo", etc. */
    unsigned long   state;             /* __LINK_STATE_* flags */
    
    /* Device operations — function pointer table */
    const struct net_device_ops *netdev_ops;
    const struct ethtool_ops    *ethtool_ops;
    
    /* Hardware address */
    unsigned char   dev_addr[MAX_ADDR_LEN];    /* MAC address */
    unsigned char   broadcast[MAX_ADDR_LEN];
    unsigned short  type;              /* ARP HW type (ARPHRD_ETHER) */
    unsigned short  hard_header_len;   /* 14 for Ethernet */
    
    /* MTU and features */
    unsigned int    mtu;               /* 1500 for Ethernet */
    netdev_features_t features;        /* NETIF_F_* flags */
    netdev_features_t hw_features;
    
    /* Queueing */
    struct netdev_queue  *_tx;         /* array of TX queues */
    unsigned int     num_tx_queues;
    struct Qdisc     *qdisc;           /* root qdisc */
    
    /* Statistics */
    struct net_device_stats stats;
    
    /* Network namespace */
    possible_net_t nd_net;
    
    /* Interface index */
    int ifindex;
    
    /* Private driver data */
    void *priv;    /* accessed via netdev_priv(dev) */
};
```

**net_device_ops — the driver's function pointer table:**

```c
struct net_device_ops {
    int     (*ndo_open)(struct net_device *dev);
    int     (*ndo_stop)(struct net_device *dev);
    netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb,
                                   struct net_device *dev);
    void    (*ndo_set_rx_mode)(struct net_device *dev);
    int     (*ndo_set_mac_address)(struct net_device *dev, void *addr);
    int     (*ndo_ioctl)(struct net_device *dev, struct ifreq *ifr, int cmd);
    void    (*ndo_tx_timeout)(struct net_device *dev, unsigned int txqueue);
    struct  net_device_stats* (*ndo_get_stats)(struct net_device *dev);
    int     (*ndo_change_mtu)(struct net_device *dev, int new_mtu);
    int     (*ndo_vlan_rx_add_vid)(struct net_device *dev,
                                    __be16 proto, u16 vid);
    ...
};
```

### 4.3 struct sock — The Protocol Control Block

`struct sock` is the **kernel-side** representation of a socket. It is the
foundation upon which protocol-specific control blocks are layered.

```
Socket Layering:

  struct socket      (VFS-facing: file operations, inode)
       |
       | sk pointer
       v
  struct sock        (protocol-independent: buffers, state, locks)
       |
       | embedded as first member
       v
  struct inet_sock   (IPv4/IPv6 common: src/dst addr, ports)
       |
       v
  struct tcp_sock    (TCP: sequence numbers, windows, timers)
  struct udp_sock    (UDP: pending queue, multicast)
  struct raw_sock    (RAW: filter, bind)
```

```c
struct sock {
    /* Socket state */
    volatile unsigned char sk_state;   /* TCP_ESTABLISHED, TCP_LISTEN, etc. */
    
    /* Addressing */
    __be32              sk_rcv_saddr;  /* bound local address */
    __be32              sk_daddr;      /* destination address */
    __be16              sk_num;        /* local port (host byte order) */
    __be16              sk_dport;      /* destination port */
    
    /* Receive buffer */
    struct sk_buff_head  sk_receive_queue;  /* received packets */
    int                  sk_rcvbuf;         /* max receive buffer size */
    atomic_t             sk_rmem_alloc;     /* bytes in receive queue */
    
    /* Send buffer */
    struct sk_buff_head  sk_write_queue;    /* packets waiting to send */
    int                  sk_sndbuf;         /* max send buffer size */
    atomic_t             sk_wmem_alloc;     /* bytes in write queue */
    
    /* Backlog queue (from softirq when socket is locked) */
    struct {
        atomic_t         len;
        struct sk_buff   *head, *tail;
    } sk_backlog;
    
    /* Locking */
    socket_lock_t        sk_lock;       /* process-context lock */
    
    /* Wait queue for blocked readers/writers */
    struct sock_common   __sk_common;
    wait_queue_head_t   *sk_sleep;
    
    /* Protocol operations */
    struct proto        *sk_prot;       /* TCP ops, UDP ops, etc. */
    
    /* Error queue (for MSG_ERRQUEUE) */
    struct sk_buff_head  sk_error_queue;
    
    /* Callbacks */
    void (*sk_state_change)(struct sock *sk);
    void (*sk_data_ready)(struct sock *sk);
    void (*sk_write_space)(struct sock *sk);
    void (*sk_error_report)(struct sock *sk);
    
    /* Socket options */
    int                  sk_rcvtimeo;   /* SO_RCVTIMEO */
    int                  sk_sndtimeo;   /* SO_SNDTIMEO */
    int                  sk_priority;   /* SO_PRIORITY */
    
    /* Filtering */
    struct sk_filter    *sk_filter;     /* BPF socket filter */
    
    /* Network namespace */
    struct net          *sk_net;
};
```

### 4.4 struct proto — Protocol Operations

Each L4 protocol registers a `struct proto` with the kernel:

```c
struct proto {
    /* Name for /proc/net/protocols */
    char        name[32];
    
    /* Core operations */
    int         (*connect)(struct sock *sk, struct sockaddr *addr, int len);
    int         (*disconnect)(struct sock *sk, int flags);
    int         (*accept)(struct sock *sk, int flags, int *err, bool kern);
    int         (*ioctl)(struct sock *sk, int cmd, unsigned long arg);
    int         (*init)(struct sock *sk);
    void        (*destroy)(struct sock *sk);
    void        (*shutdown)(struct sock *sk, int how);
    int         (*setsockopt)(struct sock *sk, int level, int optname, ...);
    int         (*getsockopt)(struct sock *sk, int level, int optname, ...);
    int         (*sendmsg)(struct sock *sk, struct msghdr *msg, size_t len);
    int         (*recvmsg)(struct sock *sk, struct msghdr *msg, ...);
    int         (*bind)(struct sock *sk, struct sockaddr *addr, int len);
    int         (*backlog_rcv)(struct sock *sk, struct sk_buff *skb);
    void        (*close)(struct sock *sk, long timeout);
    int         (*hash)(struct sock *sk);
    void        (*unhash)(struct sock *sk);
    
    /* Memory accounting */
    bool        (*stream_memory_free)(const struct sock *sk);
    
    /* Slab cache for sock allocation */
    struct kmem_cache  *slab;
    unsigned int        obj_size;
    
    /* Hash table for socket lookup */
    struct sock **  hashinfo;
};

/* Example: tcp_prot in net/ipv4/tcp_ipv4.c */
struct proto tcp_prot = {
    .name           = "TCP",
    .connect        = tcp_v4_connect,
    .sendmsg        = tcp_sendmsg,
    .recvmsg        = tcp_recvmsg,
    .backlog_rcv    = tcp_v4_do_rcv,
    .hash           = inet_hash,
    ...
};
```

### 4.5 struct socket vs struct sock

This is a common confusion point. They are **different** and serve different purposes:

```
struct socket (include/linux/net.h)
    — The VFS-facing object
    — Created by sys_socket()
    — Has: file*, inode*, proto_ops*, sock*
    — Represents: the file descriptor interface

struct sock (include/net/sock.h)
    — The protocol-facing object  
    — Has all actual networking state
    — Pointed to by socket->sk
    — Protocol-specific structs embed this

struct proto_ops (operations on struct socket, VFS level):
    .bind, .connect, .accept, .listen
    .sendmsg, .recvmsg
    .poll, .ioctl, .shutdown

struct proto (operations on struct sock, protocol level):
    .connect, .disconnect, .sendmsg, .recvmsg
    .init, .destroy, .backlog_rcv
```

### 4.6 sk_buff_head — The Packet Queue

```c
struct sk_buff_head {
    struct sk_buff  *next;
    struct sk_buff  *prev;
    __u32            qlen;    /* number of packets in queue */
    spinlock_t       lock;
};

/* Locking variants */
skb_queue_tail(&sk->sk_receive_queue, skb);   /* with spinlock */
__skb_queue_tail(&sk->sk_receive_queue, skb); /* already locked */
skb = skb_dequeue(&queue);                     /* dequeue head */
skb = skb_peek(&queue);                        /* peek without remove */
```

---

## 5. Socket Layer — The User–Kernel Interface

### 5.1 System Call to Kernel Path

When userspace calls `socket(AF_INET, SOCK_STREAM, 0)`:

```
sys_socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
    |
    v
sock_create(AF_INET, SOCK_STREAM, IPPROTO_TCP, &sock)
    |
    v
__sock_create()
    |
    +-- Finds registered address family: AF_INET -> inet_family_ops
    |
    +-- inet_family_ops.create() -> inet_create()
         |
         +-- Allocates struct socket (from slab cache)
         +-- Allocates struct sock / tcp_sock (sk = sk_alloc())
         +-- Sets up proto_ops: inet_stream_ops (for SOCK_STREAM)
         +-- Calls sk->sk_prot->init(sk) -> tcp_v4_init_sock()
         +-- Returns populated struct socket
    |
    v
sock_map_fd()
    |
    +-- Allocates file descriptor
    +-- Creates file object pointing to socket
    +-- Returns fd to userspace
```

### 5.2 send() System Call Path

```
userspace: send(fd, buf, len, flags)
    |
    v
sys_sendto() / sys_send()
    |
    v
sock_sendmsg(sock, msg)
    |
    v
sock->ops->sendmsg(sock, msg, len)  /* proto_ops level */
      [inet_sendmsg for AF_INET]
    |
    v
sk->sk_prot->sendmsg(sk, msg, len)  /* proto level */
      [tcp_sendmsg for TCP]
    |
    v
tcp_sendmsg():
    - Acquires socket lock (lock_sock)
    - Copies userspace data into sk_buff(s)
    - Calls tcp_push() to trigger transmission
    - sk_buff goes into sk->sk_write_queue
    |
    v
tcp_write_xmit()
    |
    +-- Checks congestion window, send window
    +-- Builds TCP header (tcp_transmit_skb)
    +-- Calls ip_queue_xmit() or inet_send_skb()
```

### 5.3 recv() System Call Path

```
userspace: recv(fd, buf, len, flags)
    |
    v
sys_recvfrom()
    |
    v
sock_recvmsg(sock, msg, flags)
    |
    v
sock->ops->recvmsg()   [inet_recvmsg]
    |
    v
sk->sk_prot->recvmsg() [tcp_recvmsg]
    |
    v
tcp_recvmsg():
    - Acquires socket lock
    - Checks sk->sk_receive_queue for data
    - If empty: sk_wait_data() puts process to sleep
    - When woken: copies data from skb to userspace msghdr
    - Advances tcp_sk->copied_seq
    - Releases socket lock
    - Returns bytes copied
```

### 5.4 The socket lock and sk_lock

The socket lock (`sk->sk_lock`) is a special "owned" lock:

```
Socket lock mechanisms:

lock_sock(sk):
    - spin_lock_bh(&sk->sk_lock.slock)
    - If already locked: add to backlog queue and sleep
    - Sets sk->sk_lock.owned = 1

release_sock(sk):
    - Processes sk_backlog queue
    - Clears sk->sk_lock.owned = 0
    - Wakes up any sleepers

bh_lock_sock(sk):  [used from softirq]
    - spin_lock(&sk->sk_lock.slock) only
    - Does NOT set owned
    - If socket is owned (process is in it), adds skb to backlog

This is why backlog exists: softirq arrives while process is
inside socket — can't block, so skb goes to backlog and is
processed when process releases the socket.
```

---

## 6. Transport Layer — TCP & UDP Deep Dive

### 6.1 TCP State Machine

```
TCP State Machine:

                    +--------+
         passive    |  CLOSED|             active
          open     +--------+              open
         -------> | LISTEN |  <-------     -----
                  +--------+             SYN sent
                      |                      |
                  SYN received            +--------+
                      |                  |SYN_SENT|
                      v                  +--------+
                  +-------+                  |
                  |SYN_   |   SYN received   |
                  |RCVD   |<-----------------+
                  +-------+  (simultaneous open)
                      |
                   SYN+ACK sent, ACK received
                      |
                      v
               +--------------+
               | ESTABLISHED  |<--------+
               +--------------+         |
                      |                 |
               close  |                 |
                      v                 |
               +-----------+            |
               |  FIN_WAIT1|            |
               +-----------+            |
                 |        |             |
        FIN      |        | ACK         |
        received |        |             |
                 v        v             |
          +----------+ +----------+     |
          | CLOSING  | |FIN_WAIT2 |     |
          +----------+ +----------+     |
               |              |        |
         ACK   |          FIN |        |
               |          rcvd|        |
               v              v        |
          +---------+   +----------+   |
          | TIME_   |   | TIME_    |   |
          | WAIT    |   | WAIT     |   |
          +---------+   +----------+   |
               |              |        |
              2MSL           2MSL      |
               +-------> CLOSED <------+
                                       ^
    CLOSE_WAIT ---> LAST_ACK ----------+
    (passive closer path)
```

### 6.2 TCP Control Block: struct tcp_sock

```c
struct tcp_sock {
    /* inet_sock must be the first member */
    struct inet_sock inet;  /* embeds struct sock */
    
    /* === Sequence number accounting === */
    u32 rcv_nxt;       /* next expected byte from peer */
    u32 rcv_wup;       /* rcv_nxt at time last window update sent */
    u32 snd_nxt;       /* next sequence number to send */
    u32 snd_una;       /* first byte not yet acknowledged */
    u32 snd_sml;       /* last byte of most recently sent small packet */
    u32 rcv_tstamp;    /* timestamp of last received ACK */
    
    /* === Send window === */
    u32 snd_wnd;       /* peer's receive window (from peer's header) */
    u32 max_window;    /* maximum window peer has offered */
    u32 snd_cwnd;      /* congestion window */
    u32 snd_cwnd_cnt;  /* used to increment cwnd */
    u32 snd_ssthresh;  /* slow start threshold */
    
    /* === Receive window === */
    u32 rcv_wnd;       /* current receiver window we advertise */
    
    /* === RTT measurement === */
    u32 srtt_us;       /* smoothed RTT (in microseconds, scaled) */
    u32 mdev_us;       /* mean deviation of RTT */
    u32 rttvar_us;     /* RTT variance */
    u32 rto;           /* retransmission timeout */
    
    /* === Retransmission queue === */
    struct sk_buff_head out_of_order_queue;   /* OOO receive queue */
    struct rb_root      out_of_order_queue_rb;
    
    /* === Timers === */
    struct hrtimer      pacing_timer;
    /* Also: retransmit_timer embedded in sk->sk_timer */
    
    /* === Congestion control === */
    const struct tcp_congestion_ops *ca_ops;
    u8   ca_state;    /* TCP_CA_Open/Disorder/CWR/Recovery/Loss */
    u32  prior_cwnd;  /* before going to CA_Loss */
    
    /* === SACK state === */
    u8   sacked_out;  /* SACK'd segments */
    u8   retrans_out; /* retransmitted segments */
    u8   lost_out;    /* lost segments */
    
    /* === Options === */
    u8   nonagle:4;   /* Nagle algorithm state */
    u8   thin_lto:1;  /* thin stream loss timeout */
    
    /* === TSO/GSO === */
    u16  gso_segs;    /* target number of GSO segments */
};
```

### 6.3 TCP Receive Path — Detailed

```
Incoming TCP segment:

ip_local_deliver_finish()
    |
    v
tcp_v4_rcv(skb)           [net/ipv4/tcp_ipv4.c]
    |
    +-- Extract TCP header
    +-- Validate checksum
    +-- Look up socket: __inet_lookup_skb()
    |     Hash: (src_ip, src_port, dst_ip, dst_port)
    |     Checks established hash, then listening hash
    |
    +-- If socket found in TIME_WAIT state:
    |     tcp_timewait_state_process()
    |
    +-- If socket found in LISTEN state:
    |     tcp_v4_hnd_req() -> tcp_check_req() -> tcp_v4_syn_recv_sock()
    |
    +-- Normal case: socket in ESTABLISHED/etc:
         bh_lock_sock(sk)
         |
         +-- If socket is owned by user (locked):
         |     __sk_add_backlog(sk, skb)   [defer to release_sock]
         |
         +-- If socket not owned:
               tcp_v4_do_rcv(sk, skb)
                   |
                   v
               tcp_rcv_established(sk, skb)   [fast path]
                   |
                   +-- Checks if it's the expected next segment
                   +-- Updates rcv_nxt
                   +-- Copies to receive queue OR directly to user
                   +-- Schedules ACK
                   
               [or tcp_rcv_state_process for non-ESTABLISHED]
```

### 6.4 TCP Congestion Control Framework

The congestion control framework is a beautiful example of kernel polymorphism:

```c
struct tcp_congestion_ops {
    /* Called when cwnd changes are needed */
    void (*cong_avoid)(struct sock *sk, u32 ack, u32 acked);
    
    /* Snapshot of the current window */
    u32  (*ssthresh)(struct sock *sk);
    
    /* Signal that congestion occurred */
    void (*cong_control)(struct sock *sk, const struct rate_sample *rs);
    
    /* Undo cwnd reduction after a false retransmit */
    u32  (*undo_cwnd)(struct sock *sk);
    
    /* Called on packet acknowledgment */
    void (*pkts_acked)(struct sock *sk, const struct ack_sample *sample);
    
    /* Called when entering fast retransmit */
    void (*set_state)(struct sock *sk, u8 new_state);
    
    /* Called when all retransmitted packets are acknowledged */
    void (*cwnd_event)(struct sock *sk, enum tcp_ca_event ev);
    
    char name[TCP_CA_NAME_MAX];   /* "cubic", "bbr", "reno" */
    struct module *owner;
};

/* Registered algorithms: */
/* CUBIC  (default): net/ipv4/tcp_cubic.c */
/* BBR:              net/ipv4/tcp_bbr.c */
/* RENO:             net/ipv4/tcp_cong.c */
/* DCTCP:            net/ipv4/tcp_dctcp.c */
```

### 6.5 UDP Path

UDP is much simpler than TCP. No connection state, no retransmission.

```
UDP receive:

udp_rcv(skb)              [net/ipv4/udp.c]
    |
    v
__udp4_lib_rcv(skb, &udp_table, AF_INET)
    |
    +-- Validate UDP header and checksum
    +-- Look up socket: __udp4_lib_lookup()
    |     (src_ip, src_port, dst_ip, dst_port, dev->ifindex)
    |
    +-- If no socket found: send ICMP Port Unreachable
    |
    +-- udp_unicast_rcv_skb(sk, skb, uh)
         |
         v
    udp_queue_rcv_skb(sk, skb)
         |
         +-- Apply socket filter (if any)
         +-- Check receive buffer space (sk_rcvbuf)
         +-- sock_queue_rcv_skb(sk, skb)
              |
              v
         __skb_queue_tail(&sk->sk_receive_queue, skb)
         sk->sk_data_ready(sk)    /* wakes up recv() */
```

---

## 7. IP Layer — Routing, Fragmentation, and Forwarding

### 7.1 IP Input Processing

```
ip_rcv(skb, dev, pt, orig_dev)     [net/ipv4/ip_input.c]
    |
    +-- Sanity checks:
    |   - skb->len >= sizeof(iphdr)
    |   - ip_hdr->ihl >= 5 (header length valid)
    |   - ip_hdr->version == 4
    |   - skb->pkt_type != PACKET_OTHERHOST
    |
    +-- Checksum verification: ip_fast_csum()
    |
    +-- NETFILTER HOOK: NF_INET_PRE_ROUTING
    |   (iptables PREROUTING, conntrack, DNAT happen here)
    |
    v
ip_rcv_finish(net, sk, skb)
    |
    +-- Route lookup: ip_route_input_noref()
    |   Sets skb->_skb_refdst to:
    |   - rt_input_route: for locally-destined packets
    |   - ip_mr_input: for multicast
    |   - ip_forward: for forwarded packets
    |
    +-- Process IP options if present
    |
    +-- Call dst_input(skb) -> calls skb->dst->input(skb)
         |
         +-- If local: ip_local_deliver()
         +-- If forward: ip_forward()
```

### 7.2 ip_local_deliver — Delivering to L4

```
ip_local_deliver(skb)
    |
    +-- Reassemble fragments if needed:
    |   ip_defrag(net, skb, IP_DEFRAG_LOCAL_DELIVER)
    |
    +-- NETFILTER HOOK: NF_INET_LOCAL_IN
    |   (iptables INPUT chain)
    |
    v
ip_local_deliver_finish(net, sk, skb)
    |
    +-- Strip IP header: skb_pull(skb, iph->ihl * 4)
    +-- Lookup L4 protocol handler:
    |   inet_protos[iph->protocol]
    |   (registered by tcp_v4_rcv, udp_rcv, etc.)
    |
    +-- Call ipprot->handler(skb):
         tcp_v4_rcv(skb)   for protocol=6
         udp_rcv(skb)      for protocol=17
         icmp_rcv(skb)     for protocol=1
```

### 7.3 ip_forward — Packet Forwarding

```
ip_forward(skb)                [net/ipv4/ip_forward.c]
    |
    +-- Decrement TTL; if TTL == 0: send ICMP Time Exceeded
    +-- Check MTU: if skb > mtu and DF bit set: ICMP Frag Needed
    +-- NETFILTER HOOK: NF_INET_FORWARD
    |   (iptables FORWARD chain)
    |
    v
ip_forward_finish(net, sk, skb)
    |
    +-- ip_decrease_ttl(skb)
    +-- Update IP header checksum
    +-- dst_output(net, sk, skb)
         |
         v
    ip_output(net, sk, skb)
         |
         +-- NETFILTER HOOK: NF_INET_POST_ROUTING
         +-- ip_finish_output()
              |
              +-- Fragmentation if needed: ip_do_fragment()
              +-- ip_finish_output2() -> neigh_output()
                   |
                   +-- ARP resolution (if not cached)
                   +-- dev_queue_xmit(skb)
```

### 7.4 IP Fragmentation

```
Fragmentation (ip_do_fragment):

Original packet:
+------+----------------------------------+
|  IP  |        DATA (3000 bytes)         |
+------+----------------------------------+

After fragmentation (MTU=1500):
+------+---------------+--+
|  IP  | DATA[0:1480]  |MF|   Fragment 1 (MF=More Fragments)
+------+---------------+--+
+------+---------------+--+
|  IP  | DATA[1480:2960]|MF|  Fragment 2
+------+---------------+--+
+------+-----------+
|  IP  |DATA[2960:3000]|   Fragment 3 (MF=0, last)
+------+-----------+

Reassembly (ip_defrag):
- Fragments identified by (src, dst, id, protocol)
- Stored in ipq (IP fragmentation queue)
- Reassembled when all fragments received
- Timer: if not complete in ipfrag_time seconds, discard
```

---

## 8. Netfilter & iptables Subsystem

### 8.1 Netfilter Hooks

Netfilter provides 5 hooks in the IP stack where external code can intercept
packets. Every iptables rule, conntrack entry, and NAT translation works through
these hooks.

```
Netfilter Hook Points:

              PREROUTING      LOCAL_IN
                  |               |
                  v               v
[NIC] --> ip_rcv() --> route --> ip_local_deliver --> [Socket]
                  |
                  +-- (forwarded) --> ip_forward --> ip_output
                                          |               |
                                          v               v
                                       FORWARD       POST_ROUTING --> [NIC]
                                       
[Socket] --> ip_local_out --> ip_output
                                  |
                                  v
                            LOCAL_OUT
                                  |
                                  v
                            POST_ROUTING --> [NIC]

Hook values:
  NF_INET_PRE_ROUTING  = 0
  NF_INET_LOCAL_IN     = 1
  NF_INET_FORWARD      = 2
  NF_INET_LOCAL_OUT    = 3
  NF_INET_POST_ROUTING = 4
```

### 8.2 Netfilter Hook Return Values

```c
#define NF_DROP   0    /* Drop the packet completely */
#define NF_ACCEPT 1    /* Continue packet processing */
#define NF_STOLEN 2    /* Hook took ownership of skb (free it yourself) */
#define NF_QUEUE  3    /* Queue to userspace (NFQUEUE) */
#define NF_REPEAT 4    /* Call this hook again */
```

### 8.3 Registering a Netfilter Hook

```c
/* Registering a hook (e.g. in a kernel module) */
static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph = ip_hdr(skb);
    
    /* Drop all packets from 192.168.1.1 */
    if (iph->saddr == htonl(0xC0A80101))
        return NF_DROP;
    
    return NF_ACCEPT;
}

static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = PF_INET,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,    /* -300 */
};

/* Register: */
nf_register_net_hook(&init_net, &my_hook_ops);

/* Unregister: */
nf_unregister_net_hook(&init_net, &my_hook_ops);
```

### 8.4 Connection Tracking (conntrack)

Conntrack is the stateful firewall engine. It tracks connection state so that
related packets (e.g. established TCP flows, related ICMP) can be classified.

```
Conntrack state machine:

New packet arrives at PREROUTING:
    |
    v
nf_conntrack_in()
    |
    +-- Compute 5-tuple hash (src_ip, dst_ip, src_port, dst_port, proto)
    +-- Look up in conntrack hash table
    |
    +-- If not found: create new struct nf_conn (NEW state)
    |
    +-- If found: update state (ESTABLISHED, RELATED, etc.)
    |
    +-- Set skb->_nfct = &ct->ct_general
         (every skb carries pointer to its conntrack entry)

struct nf_conn {
    struct nf_conntrack     ct_general;
    spinlock_t              lock;
    
    /* Connection tuple (bidirectional) */
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];
    
    /* State */
    unsigned long  status;    /* IPS_SEEN_REPLY, IPS_ASSURED, etc. */
    
    /* Timeout */
    struct timer_list timeout;
    
    /* NAT info (if NAT module loaded) */
    struct nf_conn_nat *nat;
    
    /* Protocol-specific tracking */
    union nf_conntrack_proto proto;
};
```

### 8.5 NAT (Network Address Translation)

NAT is implemented on top of conntrack as a netfilter extension:

```
SNAT (Source NAT, e.g. masquerade):
  Applied at POST_ROUTING
  Rewrites src IP/port in outgoing packet
  Stored in conntrack tuple for reply rewriting

DNAT (Destination NAT, e.g. port forwarding):
  Applied at PREROUTING
  Rewrites dst IP/port in incoming packet
  Reply packets automatically get reverse SNAT

Implementation:
  nf_nat_packet() -> nf_nat_manip_pkt()
    -> nf_nat_ipv4_manip_pkt()  [rewrites IP header]
    -> nf_nat_proto_manip_pkt() [rewrites TCP/UDP ports]
    -> ip_send_check()          [recomputes IP checksum]
    -> inet_proto_csum_replace4() [recomputes TCP/UDP checksum]
```

---

## 9. Network Device Layer & Drivers

### 9.1 NIC Driver Structure

A typical NIC driver has these components:

```
NIC Driver Components:

  +-------------------------------------------------------+
  |                 PCI/PCIe Layer                        |
  |  pci_register_driver(&my_driver)                      |
  |  .probe = my_probe, .remove = my_remove               |
  +----------------------------+--------------------------+
                               |
  +----------------------------v--------------------------+
  |              Net Device Registration                  |
  |  alloc_etherdev(sizeof(struct my_priv))               |
  |  SET_NETDEV_DEV(dev, &pdev->dev)                      |
  |  dev->netdev_ops = &my_netdev_ops                     |
  |  register_netdev(dev)                                 |
  +----------------------------+--------------------------+
                               |
  +----------------------------v--------------------------+
  |              Hardware Resources                       |
  |  PCI BARs (memory-mapped registers)                   |
  |  MSI/MSI-X interrupts                                 |
  |  DMA engine setup (dma_alloc_coherent)                |
  +----------------------------+--------------------------+
                               |
  +----------------------------v--------------------------+
  |              Ring Buffers                             |
  |                                                       |
  |  TX Ring:                   RX Ring:                  |
  |  +---+---+---+---+          +---+---+---+---+         |
  |  | D | D | D | D |          | D | D | D | D |         |
  |  +---+---+---+---+          +---+---+---+---+         |
  |    |                          |                       |
  |    | DMA descriptors          | DMA descriptors       |
  |    v                          v                       |
  |  Mapped skb data            Pre-allocated skbs        |
  +-------------------------------------------------------+

  D = DMA descriptor (address + length + flags)
```

### 9.2 NIC Interrupt Handler and NAPI

```c
/* Hardware interrupt handler (hardirq) */
static irqreturn_t my_nic_irq(int irq, void *data)
{
    struct my_priv *priv = data;
    u32 status;
    
    /* Read and clear interrupt status from hardware */
    status = readl(priv->base + IRQ_STATUS_REG);
    writel(status, priv->base + IRQ_STATUS_REG);
    
    if (status & IRQ_RX_COMPLETE) {
        /* Disable RX interrupts to avoid interrupt storm */
        my_disable_rx_irq(priv);
        
        /* Schedule NAPI poll — this triggers NET_RX_SOFTIRQ */
        napi_schedule(&priv->napi);
    }
    
    if (status & IRQ_TX_COMPLETE) {
        my_tx_cleanup(priv);
    }
    
    return IRQ_HANDLED;
}

/* NAPI poll callback (softirq context) */
static int my_napi_poll(struct napi_struct *napi, int budget)
{
    struct my_priv *priv = container_of(napi, struct my_priv, napi);
    int work_done = 0;
    
    while (work_done < budget) {
        struct sk_buff *skb;
        
        /* Check if there's a completed RX descriptor */
        if (!my_rx_descriptor_done(priv))
            break;
        
        /* Build skb from DMA buffer */
        skb = my_build_skb(priv);
        if (!skb)
            break;
        
        /* Set skb metadata */
        skb->protocol = eth_type_trans(skb, priv->netdev);
        skb->ip_summed = CHECKSUM_UNNECESSARY; /* if HW verified checksum */
        
        /* Hand skb to network stack */
        napi_gro_receive(napi, skb);   /* with GRO */
        /* OR: netif_receive_skb(skb); /* without GRO */
        
        work_done++;
    }
    
    /* If we processed fewer than budget, we're done */
    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        my_enable_rx_irq(priv);   /* re-enable interrupts */
    }
    
    return work_done;
}
```

### 9.3 TX Path in the Driver

```c
/* Called by the network stack to transmit a packet */
static netdev_tx_t my_ndo_start_xmit(struct sk_buff *skb,
                                       struct net_device *dev)
{
    struct my_priv *priv = netdev_priv(dev);
    struct my_tx_ring *ring = &priv->tx_rings[skb->queue_mapping];
    dma_addr_t dma_addr;
    
    /* Check if TX ring has space */
    if (my_tx_ring_full(ring)) {
        netif_stop_subqueue(dev, skb->queue_mapping);
        return NETDEV_TX_BUSY;
    }
    
    /* DMA map the skb data */
    dma_addr = dma_map_single(&priv->pdev->dev,
                               skb->data, skb->len,
                               DMA_TO_DEVICE);
    if (dma_mapping_error(&priv->pdev->dev, dma_addr)) {
        dev_kfree_skb_any(skb);
        dev->stats.tx_dropped++;
        return NETDEV_TX_OK;
    }
    
    /* Write DMA descriptor to hardware */
    my_write_tx_descriptor(ring, dma_addr, skb->len,
                           skb == last_frag ? TX_DESC_EOP : 0);
    
    /* Save skb for cleanup after transmission */
    ring->tx_buf[ring->tail].skb = skb;
    ring->tx_buf[ring->tail].dma = dma_addr;
    
    /* Advance tail pointer — hardware will see this */
    ring->tail = (ring->tail + 1) % ring->size;
    
    /* Ring the doorbell — tell NIC there's new work */
    writel(ring->tail, priv->base + TX_TAIL_REG);
    
    return NETDEV_TX_OK;
}

/* TX completion cleanup (called from interrupt handler) */
static void my_tx_cleanup(struct my_priv *priv)
{
    struct my_tx_ring *ring = &priv->tx_rings[0];
    
    /* Process all completed TX descriptors */
    while (ring->head != my_read_hw_head(priv)) {
        struct my_tx_buf *buf = &ring->tx_buf[ring->head];
        
        dma_unmap_single(&priv->pdev->dev, buf->dma,
                         buf->skb->len, DMA_TO_DEVICE);
        dev_kfree_skb_any(buf->skb);
        
        ring->head = (ring->head + 1) % ring->size;
    }
    
    /* Restart queue if it was stopped due to ring full */
    if (netif_queue_stopped(priv->netdev))
        netif_wake_subqueue(priv->netdev, 0);
}
```

### 9.4 DMA Ring Buffer Layout

```
TX Ring Buffer:

  Hardware registers:
    HEAD register: hardware advances this after transmit complete
    TAIL register: driver writes here to notify hardware of new work

  Ring array (circular buffer of descriptors):

  Index:  0       1       2       3       4  ...  N-1
          +-------+-------+-------+-------+-------+
          | desc  | desc  | desc  | desc  | desc  |
          +-------+-------+-------+-------+-------+
                    ^                       ^
                   HEAD                   TAIL
                (hw done up here)    (driver wrote here)

  Each descriptor:
    u64 addr;     /* DMA address of buffer */
    u32 len;      /* length in bytes */
    u32 flags;    /* EOP, checksum offload, VLAN, etc. */

  TX buffer array (parallel to ring, for cleanup):
    struct my_tx_buf {
        struct sk_buff *skb;
        dma_addr_t      dma;
    } tx_buf[RING_SIZE];

RX Ring Buffer:

  Driver pre-allocates skbs and DMA maps them.
  Hardware fills them with received data.
  Driver checks descriptors for completion, hands skbs to stack.
```

---

## 10. NAPI — New API for High-Speed Packet Ingress

### 10.1 Why NAPI Exists

Before NAPI, each received packet caused one interrupt. At 10 Gbps, this means
~15 million interrupts/second — overwhelming CPUs.

NAPI uses **interrupt coalescing + polling**:

```
Without NAPI:                     With NAPI:

Packet 1 arrives -> interrupt     Packet 1 arrives -> interrupt
Packet 2 arrives -> interrupt     -> disable RX interrupts
Packet 3 arrives -> interrupt     -> schedule softirq poll
...                               
15M interrupts/sec                Poll loop: read N packets (budget)
= CPU thrashing                   -> if still packets: continue poll
                                  -> if no more packets: re-enable IRQ
                                  
                                  = Amortized cost per packet
```

### 10.2 NAPI Data Structure and Flow

```c
struct napi_struct {
    struct list_head poll_list;   /* on per-CPU softnet_data.poll_list */
    unsigned long    state;       /* NAPI_STATE_SCHED, etc. */
    int              weight;      /* polling budget (typical: 64) */
    int              (*poll)(struct napi_struct *, int);  /* driver callback */
    struct net_device *dev;
    struct sk_buff   *skb;        /* GRO accumulator */
    struct list_head rx_list;     /* GRO list */
    int              rx_count;
    ...
};

/* NAPI state flags */
NAPI_STATE_SCHED      /* 0: napi is scheduled to run */
NAPI_STATE_MISSED     /* 1: napi missed a packet while polling */
NAPI_STATE_DISABLE    /* 2: napi is disabled */
NAPI_STATE_NPSVC      /* 3: napi is being serviced */
NAPI_STATE_LISTED     /* 4: in the poll list */
NAPI_STATE_NO_BUSY_POLL  /* 5: busy-poll disabled */
NAPI_STATE_IN_BUSY_POLL  /* 6: busy poll in progress */
```

### 10.3 GRO — Generic Receive Offload

GRO (Generic Receive Offload) combines multiple small packets into a single
large one before passing to the IP layer, reducing per-packet overhead:

```
GRO combines:

  Packet 1: [ETH][IP][TCP seq=1000  len=1448]
  Packet 2: [ETH][IP][TCP seq=2448  len=1448]
  Packet 3: [ETH][IP][TCP seq=3896  len=1448]

  --> One coalesced skb:
  [ETH][IP][TCP seq=1000  len=4344]
  
  Delivered as one large skb to tcp_rcv()
  Massive reduction in function call overhead
```

GRO implementation uses `napi_gro_receive()` and the `napi->rx_list`:

```c
/* In driver poll function: */
napi_gro_receive(&priv->napi, skb);

/* Internally: */
dev_gro_receive(napi, skb)
    -> tries to merge with existing GRO flow
    -> if match: extend existing skb, don't deliver yet
    -> if no match or flush: deliver accumulated skb
```

---

## 11. sk_buff — The Packet Buffer in Depth

### 11.1 sk_buff Allocation

```c
/* Primary allocation functions */

/* Allocate a new skb with linear data area */
struct sk_buff *alloc_skb(unsigned int size, gfp_t priority);
/* size: data area size. priority: GFP_ATOMIC (no sleep), GFP_KERNEL */

/* Allocate with headroom (for adding headers later) */
struct sk_buff *alloc_skb_with_frags(unsigned long header_len,
                                      unsigned long data_len, ...);

/* Allocate for network device (adds NET_SKB_PAD headroom) */
struct sk_buff *netdev_alloc_skb(struct net_device *dev, unsigned int len);

/* Clone an skb (shared data, own metadata) */
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t priority);
/* Clone shares the data area — only refcount incremented */
/* Metadata (headers, cb, etc.) is NOT shared */

/* Copy an skb (fully independent copy) */
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t priority);
struct sk_buff *pskb_copy(struct sk_buff *skb, gfp_t gfp_mask);
```

### 11.2 sk_buff Reference Counting

```
skb->users: reference count for the skb metadata
skb->dataref: reference count for the data area (in skb_shinfo)

Operations:
  skb_get(skb)         — increments users
  kfree_skb(skb)       — decrements users, frees if 0
  consume_skb(skb)     — same as kfree_skb but marks as "consumed" not dropped
  dev_kfree_skb(skb)   — for driver TX completion
  dev_kfree_skb_any()  — safe from any context

The skb_shared_info:
  Stored AFTER the data area (at skb->end):
  struct skb_shared_info {
      __u8        nr_frags;        /* number of page fragments */
      __u8        tx_flags;
      unsigned short gso_size;     /* GSO segment size */
      unsigned short gso_segs;     /* GSO segment count */
      unsigned short gso_type;     /* SKB_GSO_TCPV4, etc. */
      struct sk_buff *frag_list;   /* IP fragment list */
      atomic_t    dataref;         /* data area refcount */
      skb_frag_t  frags[MAX_SKB_FRAGS];  /* page references */
  };
```

### 11.3 Checksum Offload States

```
skb->ip_summed values:

CHECKSUM_NONE:
  - No checksum computed at all
  - Stack must compute it in software
  - Common for received packets where HW couldn't verify

CHECKSUM_UNNECESSARY:
  - Hardware verified checksum already
  - Stack can skip verification
  - Set by drivers with RX checksum offload

CHECKSUM_COMPLETE:
  - Hardware computed full checksum and stored in skb->csum
  - Stack can add/subtract from it without full recompute

CHECKSUM_PARTIAL:
  - Stack wrote pseudo-header checksum to skb->csum_offset
  - Hardware will complete the checksum before transmission
  - Used for TX checksum offload (TSO/UFO)
```

### 11.4 GSO/TSO — Segmentation Offload

```
GSO (Generic Segmentation Offload):

Without GSO:
  TCP sends 1448-byte segments
  Each segment: ip_output() -> netfilter -> neigh -> driver
  = many function calls per segment

With GSO:
  TCP creates one large "super-segment" (up to 64KB)
  Passes it through the entire stack as ONE packet
  GSO splits it into wire-size segments at:
    - The NIC (TSO: hardware does it)
    - Just before the NIC if hardware doesn't support TSO (software GSO)

GSO segment creation:
  skb_gso_segment(skb, features)
    -> calls gso_segment for each protocol (tcp4_gso_segment, etc.)
    -> returns a list of skbs linked via skb->next
```

---

## 12. Complete RX Path — NIC to Userspace

### 12.1 End-to-End RX Flow

```
COMPLETE PACKET RECEIVE PATH:

[HARDWARE]
  NIC receives frame from wire
  NIC DMA's frame into pre-allocated buffer (RX ring)
  NIC writes completion descriptor
  NIC raises MSI-X interrupt on designated CPU
            |
            | (hardirq)
            v
[DRIVER - hardirq context]
  my_nic_irq() fires
  Reads interrupt status
  Calls napi_schedule(&priv->napi)
  Disables RX interrupts
  Returns IRQ_HANDLED
            |
            | (raises NET_RX_SOFTIRQ)
            v
[NET_RX_SOFTIRQ]
  net_rx_action() runs on same CPU
  Iterates priv->napi.poll_list
  Calls my_napi_poll(napi, budget=64)
            |
            v
[DRIVER - softirq context]
  my_napi_poll():
    Reads RX completion ring
    For each completed descriptor:
      Unmap DMA (dma_sync_single_for_cpu)
      Build sk_buff (build_skb or napi_build_skb)
      skb->dev = netdev
      skb->protocol = eth_type_trans(skb, dev)  [identifies ETH_P_IP]
      napi_gro_receive(napi, skb)
            |
            v
[GRO Layer - softirq]
  dev_gro_receive(napi, skb):
    Extract flow hash
    Look for matching GRO flow in napi->rx_list
    If match: coalesce into existing skb, return GRO_MERGED
    If no match: add new flow, return GRO_HELD
  On flush (budget exhausted, non-matching proto, etc.):
    napi_gro_flush(napi, false)
      -> netif_receive_skb_list_internal(list)
            |
            v
[NETWORK DEVICE LAYER - net/core/dev.c]
  netif_receive_skb(skb)
    -> __netif_receive_skb(skb)
    -> __netif_receive_skb_core(skb)
      |
      +-- deliver to packet sniffers (tcpdump via af_packet)
      |    ptype_all list: packet_type->func(skb)
      |
      +-- look up L3 protocol handler:
      |    ptype_base[ETH_P_IP] -> ip_rcv
      |
      +-- call ip_rcv(skb, dev, pt, orig_dev)
            |
            v
[IP LAYER - net/ipv4/ip_input.c]
  ip_rcv():
    Validate IP header
    NETFILTER: NF_INET_PRE_ROUTING -> conntrack, DNAT
    ip_rcv_finish():
      Route lookup: ip_route_input_noref()
      dst_input(skb) -> ip_local_deliver() [if local]
            |
            v
  ip_local_deliver():
    IP defragmentation if needed
    NETFILTER: NF_INET_LOCAL_IN -> iptables INPUT
    ip_local_deliver_finish():
      Lookup transport protocol handler
      tcp_v4_rcv(skb)
            |
            v
[TCP LAYER - net/ipv4/tcp_ipv4.c]
  tcp_v4_rcv(skb):
    Validate TCP header + checksum
    Lookup socket: __inet_lookup_skb()
    bh_lock_sock(sk)
    tcp_v4_do_rcv(sk, skb)
      tcp_rcv_established(sk, skb):
        Update sequence state
        Push data to sk->sk_receive_queue
        sk->sk_data_ready(sk) [wakes blocked recv]
        Schedule ACK
            |
            v
[SOCKET LAYER - wakeup]
  sk->sk_data_ready = sock_def_readable()
    wake_up_interruptible(&sk->sk_wq->wait)
            |
            | (wakes process)
            v
[PROCESS CONTEXT]
  recv() syscall:
    tcp_recvmsg(sk, msg, ...):
      lock_sock(sk)
      Process sk_backlog if any
      Copy from sk->sk_receive_queue to userspace
      Update rcv_wnd, send ACK if needed
      release_sock(sk)
    Return bytes to userspace application
```

---

## 13. Complete TX Path — Userspace to NIC

```
COMPLETE PACKET TRANSMIT PATH:

[PROCESS CONTEXT]
  Application calls: send(fd, data, len, 0)
            |
            v
[SYSCALL - sys_sendto]
  sock_sendmsg(sock, msg)
  inet_sendmsg(sock, msg, len)
  tcp_sendmsg(sk, msg, len):
    lock_sock(sk)
    
    Allocate sk_buff(s) for user data:
      sk_stream_alloc_skb() -> alloc_skb_with_frags()
    
    Copy user data into skb:
      skb_add_data_nocache() or get_user_pages (zerocopy)
    
    Enqueue to write queue:
      __skb_queue_tail(&sk->sk_write_queue, skb)
    
    tcp_push(sk, flags, mss, nonagle):
      tcp_write_xmit(sk, mss, nonagle, 1, GFP_KERNEL)
            |
            v
[TCP OUTPUT - net/ipv4/tcp_output.c]
  tcp_write_xmit(sk, mss, nonagle, push_one, gfp):
    while (skb = tcp_send_head(sk)):
      Check: cwnd, send_window, Nagle algorithm
      
      tcp_transmit_skb(sk, skb, clone_it, gfp):
        Build TCP header:
          skb_push(skb, tcp_hdr_size)
          th = tcp_hdr(skb)
          th->source = sk->sk_num
          th->dest   = sk->sk_dport
          th->seq    = htonl(tcb->seq)
          th->ack_seq= htonl(rcv_nxt)
          th->window = htons(rcv_wnd >> scale)
          th->check  = 0 (filled later, or by HW)
          
        Pass to IP:
          tp->af_specific->queue_xmit(sk, skb, &inet->cork.fl)
            |
            v
[IP OUTPUT - net/ipv4/ip_output.c]
  ip_queue_xmit(sk, skb, fl):
    Route lookup or use cached route
    
  ip_local_out(net, sk, skb):
    NETFILTER: NF_INET_LOCAL_OUT (iptables OUTPUT)
    dst_output(net, sk, skb)
      -> ip_output(net, sk, skb)
            |
            v
  ip_output():
    NETFILTER: NF_INET_POST_ROUTING (iptables POSTROUTING, SNAT)
    ip_finish_output(net, sk, skb):
      
      GSO check:
        if skb is a GSO super-segment:
          ip_do_gso_segment() -> splits into segments
      
      Fragmentation check:
        if skb->len > mtu:
          ip_do_fragment()
      
      ip_finish_output2(net, sk, skb):
        neigh = __ipv4_neigh_lookup_noref(dev, nexthop)
        neigh_output(neigh, skb):
          if neigh->nud_state == NUD_CONNECTED:
            dev_queue_xmit(skb)   [ARP resolved, go fast]
          else:
            ARP resolution needed: arp_solicit()
            Queue skb until ARP reply
            dev_queue_xmit() after ARP
            |
            v
[DEVICE LAYER - net/core/dev.c]
  dev_queue_xmit(skb):
    txq = netdev_core_pick_tx(dev, skb, NULL)  [multiqueue]
    q   = rcu_dereference(txq->qdisc)          [get root qdisc]
    
    if q->enqueue:           [qdisc with queuing]
      __dev_xmit_skb(skb, q, dev, txq):
        qdisc_run_begin(q)
        q->enqueue(skb, q, &skb2)  [enqueue into qdisc]
        __qdisc_run(q)              [dequeue and transmit]
    else:                    [qdisc passthrough]
      dev_hard_start_xmit(skb, dev, txq)
            |
            v
  dev_hard_start_xmit(skb, dev, txq):
    ops = dev->netdev_ops
    rc = ops->ndo_start_xmit(skb, dev)
            |
            v
[DRIVER - process context or softirq]
  my_ndo_start_xmit(skb, dev):
    DMA map skb data
    Write TX descriptor to ring
    Ring NIC doorbell (write TAIL register)
    Return NETDEV_TX_OK
            |
            | (hardware picks up descriptor)
            v
[HARDWARE]
  NIC reads TX descriptor
  Fetches data via DMA from RAM
  Transmits frame to wire
  Writes TX completion descriptor
  Raises interrupt
            |
            v
[DRIVER - interrupt/softirq]
  my_tx_cleanup():
    Unmap DMA
    kfree_skb(skb)    [skb finally freed here]
    Wake netif queue if stopped
```

---

## 14. Traffic Control & Queuing Disciplines (tc/qdisc)

### 14.1 Qdisc Framework

The traffic control subsystem sits between the IP layer and the NIC driver.
It provides packet scheduling, shaping, and policing.

```
Qdisc Hierarchy:

  dev->qdisc (root qdisc)
      |
      +-- Can be simple: pfifo_fast (default, 3-band FIFO)
      |
      +-- Or complex hierarchy:
      
         HTB root (1:0)
          |
          +-- class 1:1 (10 Mbps total)
          |    |
          |    +-- class 1:10 (web traffic, 5 Mbps)
          |    |    +-- pfifo leaf qdisc
          |    |
          |    +-- class 1:20 (bulk traffic, 3 Mbps)
          |    |    +-- SFQ (Stochastic Fair Queuing)
          |    |
          |    +-- class 1:30 (VoIP, 2 Mbps priority)
          |         +-- pfifo_fast leaf
          |
          +-- filter (u32): classify packets into classes
```

### 14.2 Qdisc Data Structure

```c
struct Qdisc {
    int     (*enqueue)(struct sk_buff *skb, struct Qdisc *sch,
                       struct sk_buff **to_free);
    struct sk_buff * (*dequeue)(struct Qdisc *sch);
    
    const struct Qdisc_ops *ops;
    
    /* Queue statistics */
    struct gnet_stats_basic_packed bstats;  /* bytes/packets */
    struct gnet_stats_queue         qstats; /* drops, overlimits */
    
    struct netdev_queue *dev_queue;
    
    /* For hierarchical qdiscs */
    struct Qdisc *parent;
    u32  handle;       /* major:minor, e.g. 1:0 */
    u32  parent_id;
    
    /* Token bucket state (for TBF, HTB) */
    struct psched_ratecfg rate;
    
    /* Scheduler state */
    unsigned long   state;    /* __QDISC_STATE_RUNNING, etc. */
    
    spinlock_t  q_lock;
    
    /* Packet queue (for simple qdiscs) */
    struct sk_buff_head q;
};

struct Qdisc_ops {
    struct Qdisc_ops    *next;
    const struct Qdisc_class_ops *cl_ops;
    char                id[IFNAMSIZ];   /* "pfifo", "htb", "sfq" */
    int                 priv_size;
    
    int     (*enqueue)(struct sk_buff *, struct Qdisc *, struct sk_buff **);
    struct sk_buff * (*dequeue)(struct Qdisc *);
    struct sk_buff * (*peek)(struct Qdisc *);
    int     (*init)(struct Qdisc *, struct nlattr *, struct netlink_ext_ack *);
    void    (*reset)(struct Qdisc *);
    void    (*destroy)(struct Qdisc *);
    int     (*change)(struct Qdisc *, struct nlattr *, struct netlink_ext_ack *);
    void    (*attach)(struct Qdisc *);
    int     (*dump)(struct Qdisc *, struct sk_buff *);
    int     (*dump_stats)(struct Qdisc *, struct gnet_dump *);
};
```

### 14.3 pfifo_fast — The Default Qdisc

The default qdisc is `pfifo_fast`. It has 3 priority bands driven by the
IP TOS/DSCP field:

```
pfifo_fast:

  Band 0 (highest priority): interactive traffic (TOS 0x10)
  Band 1 (medium priority): normal traffic
  Band 2 (lowest priority): bulk traffic (TOS 0x08)

  Dequeue: always drain band 0 first, then 1, then 2.
  
  Packet classification (prio2band table):
  IP precedence 7 -> band 0
  IP precedence 6 -> band 0
  IP precedence 5 -> band 0
  IP precedence 4 -> band 0
  IP precedence 3 -> band 1
  IP precedence 2 -> band 1
  IP precedence 1 -> band 2
  IP precedence 0 -> band 1 (default)
```

---

## 15. Routing Subsystem Internals

### 15.1 FIB (Forwarding Information Base)

Linux routing uses an **LC-trie** (Level Compressed Trie) for O(1) average
route lookups. Implemented in `net/ipv4/fib_trie.c`.

```
FIB Lookup Flow:

ip_route_input_noref(skb, dst, src, tos, dev)
    |
    v
fib_lookup(net, fl4, res, flags)
    |
    v
fib_table_lookup(tb, fl4, res, fib_flags)
    |
    +-- LC-trie traversal
    +-- Match on dst address, tos, oif
    +-- Returns: fib_result with:
         - type: RTN_UNICAST / RTN_LOCAL / RTN_BLACKHOLE / etc.
         - fi: fib_info (nexthop info)
         - prefixlen: matched prefix length

struct fib_result {
    __be32          prefix;
    unsigned char   prefixlen;
    unsigned char   nh_sel;    /* selected nexthop */
    unsigned char   type;      /* RTN_UNICAST, RTN_LOCAL, etc. */
    unsigned char   scope;
    u32             tclassid;
    struct fib_info *fi;
    struct fib_table *table;
    struct hlist_head *fa_head;
};

struct fib_info {
    /* Nexthop list */
    int             fib_nhs;         /* number of nexthops */
    struct fib_nh   fib_nh[0];       /* nexthop array */
    
    /* Gateway */
    __be32          fib_prefsrc;
    
    /* Route metrics */
    u32             fib_priority;
    struct dst_metrics *fib_metrics;
    
    /* Protocol that added this route */
    unsigned char   fib_protocol;    /* RTPROT_KERNEL, RTPROT_STATIC, etc. */
};
```

### 15.2 Route Cache and dst_entry

```c
struct dst_entry {
    struct net_device   *dev;       /* output device */
    struct dst_ops      *ops;       /* ip_dst_ops */
    
    /* Input/output function pointers — SET BY ROUTING */
    int (*input)(struct sk_buff *);   /* ip_local_deliver or ip_forward */
    int (*output)(struct net *net, struct sock *sk, struct sk_buff *skb);
    
    unsigned long       expires;
    
    /* MTU and metrics */
    u32                 _metrics[RTAX_MAX];
    
    /* Reference counting */
    atomic_t            __refcnt;
};

/* rtable extends dst_entry for IPv4 */
struct rtable {
    struct dst_entry dst;
    
    int         rt_genid;       /* route cache generation */
    unsigned    rt_flags;       /* RTCF_LOCAL, RTCF_BROADCAST, etc. */
    __u16       rt_type;        /* RTN_UNICAST, RTN_LOCAL, etc. */
    __u8        rt_is_input;
    __u8        rt_uses_gateway;
    
    int         rt_iif;         /* input interface index */
    u8          rt_gw_family;
    union {
        __be32      rt_gw4;     /* IPv4 gateway */
        struct in6_addr rt_gw6;
    };
    
    u32         rt_mtu_locked:1, rt_pmtu:31;
};
```

### 15.3 ARP and Neighbour Subsystem

```
Neighbour (ARP) resolution:

  neigh_output(neigh, skb)
      |
      +-- neigh->nud_state == NUD_CONNECTED?
          YES -> neigh->output(neigh, skb)
                  -> dev_hard_header(skb, dev, ETH_P_IP,
                                     neigh->ha,  /* MAC address */
                                     dev->dev_addr, skb->len)
                  -> dev_queue_xmit(skb)
                  
          NO  -> arp_solicit(neigh, skb):
                  Build ARP request:
                    arp_create(ARPOP_REQUEST, ETH_P_ARP,
                               target_ip, dev, src_ip, NULL,
                               dev->dev_addr, NULL)
                  dev_queue_xmit(arp_skb)
                  
                  Queue original skb in neigh->arp_queue
                  Wait for ARP reply...
                  
  On ARP reply:
    arp_rcv() -> arp_process()
      Finds neigh entry, updates neigh->ha with sender MAC
      Sets neigh->nud_state = NUD_REACHABLE
      Dequeues and transmits all queued skbs

struct neighbour {
    struct neighbour    *next;      /* hash chain */
    struct neigh_table  *tbl;       /* &arp_tbl */
    struct neigh_parms  *parms;
    
    unsigned long       confirmed;  /* time last confirmed reachable */
    unsigned long       updated;    /* time neigh entry was updated */
    
    rwlock_t            lock;
    atomic_t            refcnt;
    
    unsigned char       ha[ALIGN(MAX_ADDR_LEN, sizeof(unsigned long))]; /* MAC */
    struct hh_cache     hh;         /* cached hardware header */
    
    int     (*output)(struct neighbour *, struct sk_buff *);  /* fast path */
    
    unsigned char nud_state;        /* NUD_INCOMPLETE/REACHABLE/STALE/etc. */
    unsigned char type;
    unsigned char dead;
    
    u8   flags;
    
    /* Primary IP address this entry is for */
    u8   primary_key[0];  /* IP address follows */
};
```

---

## 16. Network Namespaces & Virtualization

### 16.1 struct net — The Network Namespace

Every network namespace (`ip netns add foo`) creates a `struct net`:

```c
struct net {
    refcount_t          passive;
    spinlock_t          rules_mod_lock;
    atomic_t            dev_unreg_count;
    
    unsigned int        dev_base_seq;
    int                 ifindex;
    
    spinlock_t          nsid_lock;
    atomic_t            fnhe_genid;
    
    struct list_head    list;       /* list of all namespaces */
    struct list_head    exit_list;
    
    struct user_namespace   *user_ns;
    struct ucounts          *ucounts;
    
    /* Per-namespace routing */
    struct net_device   *loopback_dev;     /* lo device for this ns */
    struct netns_core   core;
    struct netns_mib    mib;
    struct netns_packet packet;
    struct netns_unix   unx;
    struct netns_nexthop nexthop;
    struct netns_ipv4   ipv4;              /* IPv4 specific: routing, etc. */
    struct netns_ipv6   ipv6;
    
    struct net_generic __rcu    *gen;      /* for modules to store per-ns data */
    
    /* sysctl: /proc/sys/net/... entries for this namespace */
    struct ctl_table_set    sysctls;
    
    struct sock             *rtnl;         /* rtnetlink socket for this ns */
};
```

### 16.2 Virtual Devices

Linux supports multiple virtual network device types:

```
Virtual Device Types:

veth pair:
  +--------+       +--------+
  | veth0  |<----->| veth1  |  (kernel connects them directly)
  +--------+       +--------+
  [In NS1]         [In NS2 or host]
  Packets out veth0 appear in veth1 instantly (no copy)

vlan (802.1Q):
  +-------+    +--------+   +--------+
  |  eth0 |    |eth0.10 |   |eth0.20 |  VLAN tagged
  +-------+    +--------+   +--------+
  
bridge:
  +-------+-------+-------+
  |  br0 (software L2 switch)  |
  +---+-------+-------+---+
      |       |       |
    eth0    eth1    veth0

tun/tap:
  Userspace reads/writes raw packets via /dev/net/tun
  tun: layer 3 (IP packets)
  tap: layer 2 (Ethernet frames)

bonding/team:
  Combines multiple physical NICs into one logical interface
  Modes: active-backup, balance-rr, balance-xor, 802.3ad LACP

macvlan/ipvlan:
  Multiple virtual interfaces on one physical NIC
  Each with its own MAC (macvlan) or same MAC, different IP (ipvlan)
```

---

## 17. eBPF & XDP — Programmable Networking

### 17.1 eBPF Architecture

eBPF (extended Berkeley Packet Filter) allows safe, JIT-compiled programs to
run inside the kernel at specific hook points.

```
eBPF Program Lifecycle:

  [Userspace]
  bpf_prog.c source
       |
       v
  clang -target bpf -O2 -c bpf_prog.c -o bpf_prog.o
       |
       v
  BPF bytecode (ELF section)
       |
       | bpf(BPF_PROG_LOAD, ...)  syscall
       v
  [Kernel]
  Verifier:
    - Checks all paths terminate (no infinite loops)
    - Checks memory accesses are safe
    - Checks stack usage < 512 bytes
    - Checks all registers are initialized before use
    - Simulates all execution paths
       |
       v
  JIT Compiler:
    Converts BPF bytecode -> native x86-64 / ARM64 instructions
       |
       v
  Attached to hook:
    - XDP (earliest possible: in driver, before skb allocation)
    - TC (traffic control ingress/egress)
    - Socket filter (per-socket packet filter)
    - kprobe/tracepoint (debugging/tracing)
    - cgroup hooks (per-cgroup network control)
```

### 17.2 XDP — eXpress Data Path

XDP is the highest-performance eBPF hook, running **in the driver's interrupt
handler** before any sk_buff is allocated:

```
XDP Modes and Performance:

  NIC Offload XDP (fastest):
    eBPF program runs on NIC SmartNIC CPU
    Packet never touches host CPU

  Native XDP (very fast):
    eBPF runs in driver NAPI poll, before alloc_skb()
    ~10-25M pps per CPU core

  Generic XDP (slower, but works everywhere):
    eBPF runs after skb allocation
    Fallback for drivers without native support

XDP Return Codes:
  XDP_DROP:     Drop the packet (free immediately, no skb ever allocated)
  XDP_PASS:     Continue to normal network stack (alloc skb, ip_rcv, etc.)
  XDP_TX:       Transmit the packet back out the same NIC (hairpin)
  XDP_REDIRECT: Redirect to another NIC, CPU, or AF_XDP socket
  XDP_ABORTED:  Bug in program, drop + increment error counter

XDP context passed to program:
  struct xdp_md {
      __u32 data;          /* pointer to start of packet data */
      __u32 data_end;      /* pointer to end of packet data */
      __u32 data_meta;     /* metadata area before data */
      __u32 ingress_ifindex;
      __u32 rx_queue_index;
      __u32 egress_ifindex;
  };
```

### 17.3 AF_XDP — Zero-Copy to Userspace

AF_XDP allows userspace to receive/transmit packets with **zero copy**:

```
AF_XDP Architecture:

  NIC RX ring
       |
       | (driver maps pages into UMEM)
       v
  UMEM (User Memory region)
  Shared between kernel and userspace via mmap()
       |
       +--> RX ring (kernel -> userspace: completed RX)
       +--> TX ring (userspace -> kernel: submit TX)
       +--> FILL ring (userspace -> kernel: give RX buffers)
       +--> COMPLETION ring (kernel -> userspace: TX done)

Kernel driver:
  Does NOT copy. Just gives userspace the DMA buffer address.
  Packet data is in UMEM directly.

Use case: DPDK-alternative, high-performance packet processing
          in userspace without leaving ring-0 for every packet.
```

### 17.4 BPF Maps

BPF programs communicate with userspace and share state via maps:

```c
/* Common BPF map types: */

BPF_MAP_TYPE_HASH          /* hash table: key -> value */
BPF_MAP_TYPE_ARRAY         /* fixed-size array indexed by u32 */
BPF_MAP_TYPE_PERCPU_HASH   /* per-CPU hash (no lock needed) */
BPF_MAP_TYPE_PERCPU_ARRAY  /* per-CPU array */
BPF_MAP_TYPE_LPM_TRIE      /* longest prefix match (routing table) */
BPF_MAP_TYPE_RINGBUF       /* lock-free ring buffer for events */
BPF_MAP_TYPE_SOCKMAP       /* map of sockets for redirection */
BPF_MAP_TYPE_XSKMAP        /* map of AF_XDP sockets */
BPF_MAP_TYPE_DEVMAP        /* map of net_device for XDP_REDIRECT */

/* Example: per-CPU packet counter */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, u32);
    __type(value, u64);
    __uint(max_entries, 1);
} pkt_count SEC(".maps");

SEC("xdp")
int xdp_count(struct xdp_md *ctx)
{
    u32 key = 0;
    u64 *count = bpf_map_lookup_elem(&pkt_count, &key);
    if (count)
        (*count)++;
    return XDP_PASS;
}
```

---

## 18. Kernel Synchronization in Networking

### 18.1 Synchronization Primitives Used in Net Stack

```
Primitive        | Where used in net stack
-----------------+--------------------------------------------------
spinlock_t       | sk_buff_head.lock, neigh->lock, hash table buckets
rwlock_t         | dev->addr_list_lock, fib_info_lock
rw_semaphore     | net->rwsem (rtnl vs non-rtnl ops)
mutex_t          | Less common; where sleeping is OK
RCU              | Routing tables, dev list, socket lookup tables
seqlock_t        | jiffies, TCP timestamps
per-CPU vars     | softnet_data, TCP/UDP stats, socket memory
atomic_t         | sk->sk_refcnt, skb->users, neigh->refcnt
RTNL (rtnl_lock) | Device configuration: add/del/change interfaces
```

### 18.2 RTNL Lock — The Big Kernel Lock of Networking

`rtnl_lock()` is a global mutex that protects network device configuration.
It is held during `ip link add`, `ip link del`, `ip addr add`, etc.

```c
/* Functions requiring RTNL held: */
register_netdev(dev)
unregister_netdev(dev)
dev_change_flags()
dev_change_name()
netdev_rx_handler_register()

/* How to use: */
rtnl_lock();
/* ... device configuration ... */
rtnl_unlock();

/* ASSERT_RTNL() verifies it's held (for debugging): */
ASSERT_RTNL();
```

### 18.3 Socket Locking Sequence

Understanding the locking sequence prevents deadlocks:

```
Correct locking order (never reverse these):

1. RTNL lock (rtnl_lock)          [device-level]
2. socket lock (lock_sock)        [socket-level]
3. spinlock (spin_lock_bh)        [queue-level]

In softirq:
  bh_lock_sock(sk)                [only the spinlock part]
  if sock_owned_by_user(sk):
    add to backlog
  else:
    process immediately
  bh_unlock_sock(sk)
```

### 18.4 RCU in Socket Lookups

The UDP/TCP socket lookup tables use RCU for lockless reads:

```c
/* TCP socket lookup (simplified) */
static struct sock *__inet_lookup_established(struct net *net,
    struct inet_hashinfo *hashinfo, ...)
{
    /* Compute hash */
    hash = inet_ehashfn(net, daddr, hnum, saddr, sport);
    head = &hashinfo->ehash[hash & hashinfo->ehash_mask];
    
    rcu_read_lock();
    sk_nulls_for_each_rcu(sk, node, &head->chain) {
        if (inet_match(net, sk, acookie, raddr, rport, laddr, lport, dif, sdif)) {
            if (unlikely(!refcount_inc_not_zero(&sk->sk_refcnt)))
                goto out_noref;
            if (unlikely(!inet_match(...)))  /* recheck after refcnt */
                goto out_put;
            goto found;
        }
    }
    sk = NULL;
found:
    rcu_read_unlock();
    return sk;
}
```

---

## 19. Memory Management in the Network Stack

### 19.1 Slab Allocator for Network Objects

```
Key slab caches in networking:

  skbuff_head_cache     — struct sk_buff objects
  skbuff_fclone_cache   — sk_buff pairs (for fast cloning)
  sock_inode_cache      — struct socket_alloc (socket + inode)
  tcp_sock              — struct tcp_sock
  udp_sock              — struct udp_sock
  inet_peer_cache       — struct inet_peer (per-destination state)
  ip_dst_cache          — struct rtable (route entries)

Created with:
  kmem_cache_create("skbuff_head_cache",
                    sizeof(struct sk_buff), 0,
                    SLAB_HWCACHE_ALIGN | SLAB_PANIC, NULL)
```

### 19.2 Socket Memory Accounting

```
Memory accounting prevents sockets from consuming all RAM:

Global level:
  sysctl_tcp_mem[0,1,2] = [pressure_low, pressure_high, max]
  tcp_memory_allocated: atomic_long tracking all TCP socket memory

Per-socket level:
  sk->sk_rcvbuf: max receive buffer bytes (default: 87380 * 2)
  sk->sk_sndbuf: max send buffer bytes (default: 87380 * 2)

When a packet arrives at a socket:
  sk_rmem_schedule(sk, skb, skb->truesize):
    sk->sk_rmem_alloc += skb->truesize
    if sk_rmem_alloc > sk_rcvbuf: DROP packet
    
    Charge against global TCP memory pool.
    If global pressure: shrink per-socket limits.

When sk_buff is freed:
  skb_orphan(skb)        — disassociates skb from socket
  kfree_skb_partial(skb) — decrements sk_rmem_alloc
```

### 19.3 Page Pool — High Performance Buffer Management

Modern drivers use the **page pool** allocator for zero-copy RX:

```c
/* Page pool: pre-allocates pages, allows DMA recycling */

struct page_pool *pp = page_pool_create(&params);
/* params: pool size, nid (NUMA node), dev (for DMA), dma_dir */

/* In driver init (per RX queue): */
for (i = 0; i < ring_size; i++) {
    page = page_pool_dev_alloc_pages(pp);
    /* DMA map is done by page pool automatically */
    ring->rx_buf[i].page = page;
    ring->rx_buf[i].dma  = page_pool_get_dma_addr(page);
    /* Write DMA address to RX descriptor */
}

/* On packet receive: */
skb = build_skb(page_address(page), PAGE_SIZE);
skb_mark_for_recycle(skb);  /* when skb freed, page goes back to pool */
napi_gro_receive(napi, skb);

/* Page pool recycling avoids alloc_page() overhead */
```

---

## 20. Kernel Development Workflow

### 20.1 Setting Up Your Development Environment

```bash
# 1. Clone the kernel source tree
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
# OR the networking-specific tree (faster for net patches):
git clone https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git

# 2. Clone Dave Miller / Jakub Kicinski's networking trees
# net.git   — bug fixes for current release
# net-next  — new features for next release

# 3. Build tools
sudo apt install build-essential flex bison libelf-dev libssl-dev \
                 libncurses-dev dwarves pahole bc python3 cpio

# 4. Configure kernel (start from current config)
cp /boot/config-$(uname -r) .config
make olddefconfig
# Enable extra debugging:
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_KASAN            # memory error detection
scripts/config --enable CONFIG_KCSAN            # concurrency bug detection
scripts/config --enable CONFIG_LOCKDEP          # lock order tracking
scripts/config --enable CONFIG_NET_SCH_SFQ      # if testing qdisc
scripts/config --enable CONFIG_DYNAMIC_DEBUG

# 5. Build
make -j$(nproc) 2>&1 | tee build.log

# 6. Install (on test VM, never on production machine)
sudo make modules_install
sudo make install
sudo reboot
```

### 20.2 Setting Up a Test VM

**Always develop and test in a VM.** Never test kernel changes on your
primary machine.

```bash
# Use QEMU for kernel development:
# qemu-kvm with virtio networking for fast testing

qemu-system-x86_64 \
    -enable-kvm \
    -m 4G \
    -smp 4 \
    -kernel arch/x86/boot/bzImage \
    -initrd /path/to/initramfs.cpio.gz \
    -append "root=/dev/sda1 console=ttyS0 nokaslr" \
    -drive file=/path/to/rootfs.img,if=virtio \
    -netdev user,id=n1,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=n1 \
    -nographic

# For networking tests, use two VMs or namespaces:
# virtio-net or vhost-net for high-performance testing

# Use 'syzkaller' VM images for reproducing fuzzer bugs.
```

### 20.3 Kernel Debug Tools for Networking

```bash
# 1. Dynamic debug — enable specific pr_debug() calls
echo "file net/ipv4/tcp_input.c +p" > /sys/kernel/debug/dynamic_debug/control
echo "module ixgbe +p" > /sys/kernel/debug/dynamic_debug/control

# 2. ftrace — function tracer
cd /sys/kernel/debug/tracing
echo function > current_tracer
echo 'tcp_*' > set_ftrace_filter
echo 1 > tracing_on
# ... run workload ...
cat trace

# 3. perf — performance profiling
perf record -g -e net:netif_receive_skb sleep 10
perf report

# 4. ss — socket statistics (much better than netstat)
ss -tipm    # TCP sockets with processes and memory info
ss -u       # UDP sockets
ss -l       # listening sockets

# 5. ip/tc — network configuration and diagnostics
ip route show table main
ip neigh show
tc qdisc show dev eth0
tc -s class show dev eth0

# 6. ethtool — driver/NIC info
ethtool -S eth0          # driver statistics
ethtool -k eth0          # offload features
ethtool -g eth0          # ring buffer sizes
ethtool -l eth0          # queue count

# 7. dropwatch — track where packets are dropped in kernel
dropwatch -l kas

# 8. bpftrace — one-liners for networking
# Count TCP state changes:
bpftrace -e 'kprobe:tcp_set_state { @[args->newstate] = count(); }'

# Trace TCP retransmissions:
bpftrace -e 'kprobe:tcp_retransmit_skb { @[comm] = count(); }'

# 9. KASAN — detect use-after-free and buffer overflows
# Enable CONFIG_KASAN in build, run and watch for reports in dmesg
```

### 20.4 Kernel Coding Style

The networking subsystem has strict coding style requirements:

```c
/* CORRECT kernel networking style */

/* Line length: <= 80 columns preferred, 100 max */
/* Tabs for indentation, NOT spaces */
/* Opening brace on same line as statement (K&R style) */

static int my_net_function(struct sock *sk, struct sk_buff *skb,
			   int flags)  /* continuation: align to open paren */
{
	struct tcp_sock *tp = tcp_sk(sk);
	int ret = 0;

	if (!skb)    /* no braces for single-statement if */
		return -EINVAL;

	if (condition1 && condition2) {
		do_thing1();
		do_thing2();
	}

	/* Error path: use goto for cleanup */
	ret = do_something(sk);
	if (ret < 0)
		goto out;

	ret = do_something_else(skb);
	if (ret < 0)
		goto out_free;

	return ret;

out_free:
	kfree_skb(skb);
out:
	return ret;
}

/* Function names: lowercase_with_underscores */
/* Variable names: short but descriptive */
/* No typedefs for structs (except special cases) */
/* No C++ style comments in .c files (// is OK in headers) */
```

### 20.5 Running the Network Selftests

```bash
# Kernel has a large selftest suite for networking:
cd tools/testing/selftests/net

# Run all network selftests:
make
sudo make run_tests

# Specific tests:
sudo ./tcp_mmap           # TCP zerocopy
sudo ./udpgso             # UDP GSO
sudo ./reuseport_bpf      # SO_REUSEPORT with BPF
sudo ./tls                # kernel TLS
sudo ./fcnal-test.sh      # FIB (routing) tests

# For namespace-based tests:
sudo ./pmtu.sh            # Path MTU discovery
sudo ./fib_tests.sh       # FIB rules and routes
```

---

## 21. Finding & Fixing Bugs — First Contributions

### 21.1 Where to Find Work

```
Sources of networking bugs and TODO items:

1. Bugzilla: https://bugzilla.kernel.org
   Filter: Networking

2. Syzbot (automated fuzzer): https://syzkaller.appspot.com
   Look for "net" tagged bugs, especially ones with:
   - KASAN reports (use-after-free, out-of-bounds)
   - KCSAN reports (data races)
   - Reproducers (C programs that trigger the bug)

3. TODO comments in source code:
   git grep -r "TODO\|FIXME\|HACK" net/

4. netdev mailing list: https://lore.kernel.org/netdev/
   Watch for "RFC" patches requesting feedback
   Watch for patches with "NEEDS WORK" in cover letter

5. Sparse/smatch/coccinelle warnings:
   make C=2 net/ipv4/tcp.o   # run sparse checker
   Look for: context imbalance, bad bitwise ops, null derefs

6. W=1 compiler warnings:
   make W=1 net/ipv4/        # extra compiler warnings

7. KUnit tests that fail:
   make ARCH=um O=.kunit/    # UML kernel for unit tests
   ./tools/testing/kunit/kunit.py run

8. Documentation gaps:
   Good first contribution: add kernel-doc comments to 
   undocumented functions in net/core/
```

### 21.2 Syzkaller Bug Reproduction Example

```
Syzkaller reports look like:

  KASAN: use-after-free Read in __tcp_retransmit_skb
  BUG: KASAN: use-after-free in __tcp_retransmit_skb+0x1234/0x5678
  Read of size 4 at addr ffff8881234 by task syz-executor/1234
  
  Call Trace:
    __tcp_retransmit_skb
    tcp_retransmit_skb
    tcp_retransmit_timer

Steps to work a syzbot bug:
1. Download the reproducer C program from syzbot dashboard
2. Set up syzbot's kernel config (they provide it)
3. Run reproducer in VM: observe crash
4. Read the KASAN/UBSAN report carefully:
   - What type of bug (UAF, OOB, race)?
   - What was the allocation and where was it freed?
   - What is the access point?
5. Use KASAN's stack traces to find the bug:
   - Allocation stack shows where object was created
   - Free stack shows where it was freed
   - Access stack shows where the buggy access is
6. Write a fix, test it suppresses the crash
7. Send patch with "Reported-by: syzbot+xxxxx@syzkaller.appspotmail.com"
```

### 21.3 Sending Your First Patch

```bash
# 1. Make your changes in a new branch
git checkout -b fix/tcp-skb-use-after-free

# 2. Write the fix in the appropriate file
vim net/ipv4/tcp_output.c

# 3. Build and test
make -j$(nproc) net/ipv4/tcp_output.o  # fast incremental build
# Run selftests
cd tools/testing/selftests/net && sudo make run_tests

# 4. Commit with proper format
git add net/ipv4/tcp_output.c
git commit -s   # -s adds Signed-off-by line (REQUIRED)

# Commit message format:
# -----------------------------------------------
# net/tcp: fix use-after-free in __tcp_retransmit_skb
#
# When [describe the scenario that causes the bug],
# the [struct/function] can [describe what happens].
#
# This leads to [describe the consequence: UAF, crash, etc.]
#
# Fix this by [describe your fix].
#
# Fixes: abc123def456 ("net/tcp: commit that introduced the bug")
# Reported-by: syzbot+xxxxx@syzkaller.appspotmail.com
# Signed-off-by: Your Name <your@email.com>
# -----------------------------------------------

# 5. Check your patch for style issues
./scripts/checkpatch.pl --strict -g HEAD

# 6. Find the maintainer(s) to send to
./scripts/get_maintainer.pl net/ipv4/tcp_output.c
# Output: Jakub Kicinski, Paolo Abeni, David Miller, netdev@vger.kernel.org

# 7. Format patch
git format-patch -1 --cover-letter   # for single patch
# For series: git format-patch -N (N patches)

# 8. Send via email (git send-email)
git send-email \
    --to="netdev@vger.kernel.org" \
    --cc="jakub@cloudflare.com" \
    --cc="pabeni@redhat.com" \
    0001-net-tcp-fix-use-after-free.patch

# 9. Monitor lore.kernel.org/netdev for replies
# Respond promptly to review comments
# For v2: add "Changes in v2:" section to cover letter
```

### 21.4 Understanding the Networking Patch Review Process

```
Networking patch review workflow:

  You send patch to netdev@vger.kernel.org
       |
       v
  Reviewers (community) comment on:
    - Correctness
    - Style
    - Test coverage
    - Edge cases
       |
       v
  Jakub Kicinski / Paolo Abeni (maintainers) review
       |
       +-- "Acked-by:" from other maintainers (e.g. Eric Dumazet)
       |
       v
  Maintainer applies to net.git (for fixes) or net-next.git (for features)
       |
       v
  Linus Torvalds pulls net-next into mainline at merge window
       |
       v
  Your patch in linux-next, then mainline kernel

Timeline:
  Bug fix:    2-4 weeks to mainline (goes into -rc kernels)
  Feature:    1-2 kernel cycles (each ~3 months)
```

---

## 22. Writing a New Network Feature — End-to-End

### 22.1 Example: Adding a New Socket Option

Let's walk through adding a hypothetical new TCP socket option
`TCP_MY_OPTION`:

```c
/* Step 1: Add constant to include/uapi/linux/tcp.h */
/* (UAPI = User-space API, exported to userspace headers) */
#define TCP_MY_OPTION   37   /* choose unused number */

/* Step 2: Add field to tcp_sock (include/linux/tcp.h) */
struct tcp_sock {
    /* ... existing fields ... */
    u32  my_option_value;   /* description of what it does */
};

/* Step 3: Implement setsockopt handler in net/ipv4/tcp.c */
static int do_tcp_setsockopt(struct sock *sk, int level, int optname,
			     sockptr_t optval, unsigned int optlen)
{
    struct tcp_sock *tp = tcp_sk(sk);
    /* ... existing options ... */
    
    case TCP_MY_OPTION:
        if (optlen < sizeof(int))
            return -EINVAL;
        if (copy_from_sockptr(&val, optval, sizeof(val)))
            return -EFAULT;
        if (val < 0 || val > MY_OPTION_MAX)
            return -EINVAL;
        
        lock_sock(sk);
        tp->my_option_value = val;
        release_sock(sk);
        return 0;
}

/* Step 4: Implement getsockopt handler */
static int do_tcp_getsockopt(struct sock *sk, int level, int optname,
			     char __user *optval, int __user *optlen)
{
    /* ... existing options ... */
    case TCP_MY_OPTION:
        if (get_user(len, optlen))
            return -EFAULT;
        len = min_t(unsigned int, len, sizeof(int));
        val = tp->my_option_value;
        if (put_user(len, optlen) || copy_to_user(optval, &val, len))
            return -EFAULT;
        return 0;
}

/* Step 5: Use the option in the TCP logic */
/* Somewhere in tcp_output.c or tcp_input.c: */
if (tp->my_option_value) {
    /* do something different */
}

/* Step 6: Write a selftest (tools/testing/selftests/net/) */
/* Step 7: Update Documentation/networking/ */
/* Step 8: Send as patch series:
   [PATCH 1/4] tcp: add TCP_MY_OPTION uapi constant
   [PATCH 2/4] tcp: add my_option_value to tcp_sock
   [PATCH 3/4] tcp: implement TCP_MY_OPTION setsockopt/getsockopt
   [PATCH 4/4] selftests: add test for TCP_MY_OPTION
*/
```

### 22.2 Writing a Simple Network Protocol Module

```c
/* A minimal kernel network protocol (educational skeleton) */

#include <linux/module.h>
#include <linux/net.h>
#include <net/sock.h>

#define PF_MYPROTO 45   /* hypothetical protocol family */

/* Our protocol control block */
struct myproto_sock {
    struct sock sk;   /* MUST be first */
    /* protocol-specific state */
    u32 my_state;
};

static int myproto_create(struct net *net, struct socket *sock,
			  int protocol, int kern)
{
    struct sock *sk;
    
    if (sock->type != SOCK_DGRAM)
        return -ESOCKTNOSUPPORT;
    
    sk = sk_alloc(net, PF_MYPROTO, GFP_KERNEL, &myproto_proto, kern);
    if (!sk)
        return -ENOMEM;
    
    sock->ops = &myproto_ops;
    sock_init_data(sock, sk);
    
    return 0;
}

static int myproto_sendmsg(struct socket *sock, struct msghdr *msg,
			   size_t len)
{
    struct sock *sk = sock->sk;
    struct sk_buff *skb;
    
    skb = sock_alloc_send_skb(sk, len, msg->msg_flags & MSG_DONTWAIT, &err);
    if (!skb)
        return err;
    
    skb_reserve(skb, /* headroom for headers */);
    
    if (memcpy_from_msg(skb_put(skb, len), msg, len)) {
        kfree_skb(skb);
        return -EFAULT;
    }
    
    /* Build your protocol header */
    /* ... */
    
    /* Hand to IP layer */
    return ip_send_skb(sock_net(sk), skb);
}

static const struct proto_ops myproto_ops = {
    .family     = PF_MYPROTO,
    .owner      = THIS_MODULE,
    .sendmsg    = myproto_sendmsg,
    .recvmsg    = myproto_recvmsg,
    .bind       = myproto_bind,
    /* ... */
};

static struct proto myproto_proto = {
    .name      = "MYPROTO",
    .owner     = THIS_MODULE,
    .obj_size  = sizeof(struct myproto_sock),
};

static const struct net_proto_family myproto_family = {
    .family  = PF_MYPROTO,
    .create  = myproto_create,
    .owner   = THIS_MODULE,
};

static int __init myproto_init(void)
{
    int err;
    
    err = proto_register(&myproto_proto, 1);  /* 1 = create slab cache */
    if (err)
        return err;
    
    err = sock_register(&myproto_family);
    if (err) {
        proto_unregister(&myproto_proto);
        return err;
    }
    
    return 0;
}

static void __exit myproto_exit(void)
{
    sock_unregister(PF_MYPROTO);
    proto_unregister(&myproto_proto);
}

module_init(myproto_init);
module_exit(myproto_exit);
MODULE_LICENSE("GPL");
```

---

## 23. Key Source Files & Where Everything Lives

### 23.1 Must-Read Source Files

```
Priority 1 — Read these first:

  net/core/skbuff.c         ← sk_buff lifecycle (alloc, clone, free)
  net/core/dev.c            ← net_device, netif_receive_skb, dev_queue_xmit
  net/core/sock.c           ← struct sock lifecycle
  net/ipv4/ip_input.c       ← ip_rcv(), ip_local_deliver()
  net/ipv4/ip_output.c      ← ip_output(), ip_finish_output()
  net/ipv4/tcp_ipv4.c       ← TCP IPv4 glue: tcp_v4_rcv(), tcp_v4_connect()
  net/ipv4/tcp_input.c      ← TCP receive processing
  net/ipv4/tcp_output.c     ← TCP transmit: tcp_transmit_skb()
  net/ipv4/udp.c            ← UDP protocol
  net/ipv4/af_inet.c        ← inet socket family: inet_create(), inet_sendmsg()

Priority 2 — Core infrastructure:

  net/core/neighbour.c      ← ARP/neighbour subsystem
  net/ipv4/arp.c            ← ARP protocol implementation
  net/ipv4/route.c          ← Route lookup and rtable management
  net/ipv4/fib_trie.c       ← FIB LC-trie implementation
  net/sched/sch_generic.c   ← Qdisc framework
  net/netfilter/nf_conntrack_core.c ← Connection tracking

Priority 3 — Advanced topics:

  net/core/filter.c         ← BPF socket filters
  net/core/xdp.c            ← XDP infrastructure
  kernel/bpf/verifier.c     ← BPF verifier (large, complex)
  net/ipv4/tcp_cong.c       ← Congestion control framework
  net/ipv4/tcp_cubic.c      ← CUBIC implementation (study this)
  net/ipv4/tcp_bbr.c        ← BBR implementation
  drivers/net/loopback.c    ← Simplest possible NIC driver
  drivers/net/virtio_net.c  ← Clean virtio NIC driver
  drivers/net/ethernet/intel/e1000e/ ← Real-world NIC driver

Priority 4 — Headers to memorize:

  include/linux/skbuff.h    ← sk_buff: read every field
  include/linux/netdevice.h ← net_device, net_device_ops
  include/net/sock.h        ← struct sock
  include/net/tcp.h         ← TCP control block, constants
  include/net/ip.h          ← IP utilities
  include/linux/netfilter.h ← Netfilter hooks
  include/uapi/linux/tcp.h  ← TCP socket options (UAPI)
  include/uapi/linux/in.h   ← AF_INET, SOCK_*, SOL_* constants
```

### 23.2 Kernel Networking Maintainers

```
Networking subsystem maintainers (as of 2024):

  Jakub Kicinski <kuba@kernel.org>     — co-maintainer, net/net-next
  Paolo Abeni <pabeni@redhat.com>      — co-maintainer
  David S. Miller <davem@davemloft.net>— former maintainer, still reviews

Area-specific maintainers:
  Eric Dumazet <edumazet@google.com>   — TCP, sockets, performance
  Daniel Borkmann <daniel@iogearbox.net> — BPF/XDP
  Alexei Starovoitov <ast@kernel.org>  — BPF
  Florian Westphal <fw@strlen.de>      — Netfilter/nftables
  Cong Wang <cong.wang@bytedance.com>  — TC/qdisc
  Willem de Bruijn <willemb@google.com>— UDP, socket APIs
  Martin KaFai Lau <martinlau@kernel.org> — BPF, TCP

Follow their activity:
  https://lore.kernel.org/netdev/
  https://patchwork.kernel.org/project/netdevbpf/list/
```

---

## 24. Essential Reading & Resources

### 24.1 Books (In Reading Order)

```
1. "Linux Kernel Development" — Robert Love
   Start here. Not networking-specific but essential kernel context.

2. "Understanding Linux Networking Internals" — Christian Benvenuti
   THE book. Goes deep on sk_buff, net_device, each protocol.
   Warning: based on 2.6 kernel; some APIs changed. Concepts are solid.

3. "TCP/IP Illustrated Vol. 1" — W. Richard Stevens
   Protocol-level understanding. Read alongside kernel code.

4. "TCP/IP Illustrated Vol. 2" — Gary Wright & W. Richard Stevens
   The 4.4BSD implementation. Many concepts translate directly to Linux.

5. "Linux Device Drivers" — Corbet, Rubini, Kroah-Hartman (LDD3)
   Chapter 17: Network Drivers. Available free online.
   https://lwn.net/Kernel/LDD3/

6. "BPF Performance Tools" — Brendan Gregg
   Modern eBPF/BPF for networking and performance analysis.
```

### 24.2 Online Resources

```
Kernel documentation:
  https://www.kernel.org/doc/html/latest/networking/
  https://www.kernel.org/doc/html/latest/bpf/
  https://docs.kernel.org/networking/

Mailing list (read actively):
  https://lore.kernel.org/netdev/      ← primary networking list
  https://lore.kernel.org/bpf/         ← BPF list

Patch tracking:
  https://patchwork.kernel.org/project/netdevbpf/list/

LWN.net articles (excellent deep-dives):
  https://lwn.net/Kernel/Index/#Networking
  Notable series:
    "How TCP/IP stack works" by Jonathan Corbet
    "BPF: the universal in-kernel virtual machine"
    "Controlling network device queuing"
    "Generic Receive Offload"

Kernel Newbies:
  https://kernelnewbies.org/
  https://kernelnewbies.org/KernelHacking

Eric Dumazet's blog (TCP performance deep-dives):
  https://blog.cloudflare.com/ (Cloudflare engineering, many kernel net posts)
  https://netdevconf.info/ (conference talks, slides, papers)

Julia Evans (great kernel debugging explanations):
  https://jvns.ca/

Elixir cross-reference (browse kernel source with hyperlinks):
  https://elixir.bootlin.com/linux/latest/source/net
```

### 24.3 Tools to Master

```
Source navigation:
  cscope + ctags    — classic, fast
  clangd + LSP      — modern IDE integration
  Elixir online     — great for quick lookups without local build

Packet analysis:
  Wireshark / tshark
  tcpdump
  perf-net-*

Kernel debugging:
  KGDB              — kernel GDB remote debugging
  kdb               — simple built-in debugger
  crash + vmcore    — post-mortem analysis of kernel crashes
  ftrace/perf/bpftrace — live tracing

Performance:
  iperf3            — bandwidth testing
  netperf           — latency and throughput
  pktgen            — kernel packet generator (/proc/net/pktgen)
  neper             — Google's network performance tool

Fuzzing:
  syzkaller         — must understand to work bugs from syzbot
  Trinity           — older syscall fuzzer
```

---

## 25. 12-Month Study Plan

### Month 1–2: Foundation

```
Week 1-2:
  [ ] Read Linux Kernel Development (Love) chapters 1-11
  [ ] Build and boot a kernel in a VM
  [ ] Read net/core/skbuff.c completely, understand every field
  [ ] Write a simple kernel module (hello world, then chardev)

Week 3-4:
  [ ] Read include/linux/skbuff.h line by line with notes
  [ ] Read include/linux/netdevice.h
  [ ] Study net/core/dev.c: understand netif_receive_skb() and dev_queue_xmit()
  [ ] Exercise: add a pr_debug() to ip_rcv() and generate traffic
  [ ] Use ftrace to trace ip_rcv -> tcp_v4_rcv for a real connection
```

### Month 3–4: Protocol Stack

```
Week 5-6:
  [ ] Read net/ipv4/ip_input.c and ip_output.c completely
  [ ] Read net/ipv4/af_inet.c: understand how socket() syscall works
  [ ] Trace a complete ping (ICMP echo) through the kernel with ftrace
  [ ] Read net/ipv4/arp.c and net/core/neighbour.c

Week 7-8:
  [ ] Read TCP/IP Illustrated Vol.1 chapters on TCP
  [ ] Read net/ipv4/tcp_ipv4.c, tcp_input.c, tcp_output.c
  [ ] Understand the tcp_sock structure field by field
  [ ] Write a program that tests SO_REUSEPORT with multiple processes
  [ ] Trace a TCP three-way handshake through the kernel
```

### Month 5–6: Advanced Infrastructure

```
Week 9-10:
  [ ] Study Netfilter: read net/netfilter/nf_conntrack_core.c
  [ ] Write a simple netfilter module that logs packets
  [ ] Understand iptables rules -> netfilter hook correspondence
  [ ] Study NAT: nf_nat_packet(), nf_nat_ipv4_manip_pkt()

Week 11-12:
  [ ] Read net/ipv4/route.c and net/ipv4/fib_trie.c
  [ ] Understand ip_route_input_noref() and struct rtable
  [ ] Study policy routing: multiple routing tables
  [ ] Write scripts to test routing with ip route rules
  [ ] Read net/core/neighbour.c: understand NUD state machine
```

### Month 7–8: Device Layer and Performance

```
Week 13-14:
  [ ] Read drivers/net/loopback.c (simplest driver)
  [ ] Read drivers/net/virtio_net.c (clean real driver)
  [ ] Write a virtual NIC driver (tun-like) as learning exercise
  [ ] Understand NAPI: napi_schedule(), napi_complete_done()
  [ ] Study GRO: dev_gro_receive(), napi_gro_flush()

Week 15-16:
  [ ] Read net/sched/sch_generic.c: qdisc enqueue/dequeue
  [ ] Understand pfifo_fast, SFQ, HTB qdiscs
  [ ] Use tc to create complex qdisc hierarchies and observe behavior
  [ ] Read about GSO/TSO: skb_gso_segment()
  [ ] Study checksum offload: ip_summed states
```

### Month 9–10: eBPF/XDP and Modern Networking

```
Week 17-18:
  [ ] Install bpftool, libbpf
  [ ] Write XDP programs: counter, firewall, load balancer
  [ ] Understand the BPF verifier at a high level
  [ ] Write TC BPF programs for traffic classification
  [ ] Study AF_XDP: write a zero-copy packet processor

Week 19-20:
  [ ] Study network namespaces: read net/core/net_namespace.c
  [ ] Understand veth pairs, bridges, overlay networks (VXLAN)
  [ ] Study virtio-net and vhost: how VMs get networking
  [ ] Read about DPDK and how it differs from XDP/AF_XDP
```

### Month 11–12: Contributing

```
Week 21-22:
  [ ] Set up git send-email with your email (use kernel.org account)
  [ ] Subscribe to netdev@vger.kernel.org (read-only is OK to start)
  [ ] Find 3 bugs from syzbot tagged "net"
  [ ] Reproduce at least 1 bug in your VM
  [ ] Write a fix and run checkpatch.pl

Week 23-24:
  [ ] Send your first patch (even a documentation fix counts!)
  [ ] Respond to review comments
  [ ] Find a small feature from TODO list or mailing list discussion
  [ ] Write the feature with selftests
  [ ] Send as proper patch series
  [ ] Continue: each cycle, aim for increasing complexity
```

---

## Appendix A: Key Kernel Networking Constants & Macros

```c
/* Protocol families */
AF_INET          = 2    /* IPv4 */
AF_INET6         = 10   /* IPv6 */
AF_PACKET        = 17   /* Raw packet (tcpdump) */
AF_UNIX          = 1    /* Unix domain sockets */

/* Socket types */
SOCK_STREAM      = 1    /* TCP */
SOCK_DGRAM       = 2    /* UDP */
SOCK_RAW         = 3    /* Raw IP */
SOCK_PACKET      = 10   /* Obsolete raw packet */

/* Ethernet protocol IDs (in network byte order) */
ETH_P_IP         = 0x0800   /* IPv4 */
ETH_P_IPV6       = 0x86DD   /* IPv6 */
ETH_P_ARP        = 0x0806   /* ARP */
ETH_P_8021Q      = 0x8100   /* VLAN */

/* IP protocol numbers */
IPPROTO_TCP      = 6
IPPROTO_UDP      = 17
IPPROTO_ICMP     = 1
IPPROTO_IPV6     = 41   /* IPv6 tunnel */
IPPROTO_GRE      = 47
IPPROTO_ESP      = 50   /* IPsec ESP */

/* Packet type (skb->pkt_type) */
PACKET_HOST      = 0    /* for us */
PACKET_BROADCAST = 1    /* broadcast */
PACKET_MULTICAST = 2    /* multicast */
PACKET_OTHERHOST = 3    /* not for us, but we received it */
PACKET_OUTGOING  = 4    /* outgoing packet */

/* NIC feature flags (netdev_features_t) */
NETIF_F_SG              /* scatter-gather DMA */
NETIF_F_IP_CSUM         /* HW IP checksum */
NETIF_F_IPV6_CSUM       /* HW IPv6 checksum */
NETIF_F_HW_CSUM         /* HW checksum all protocols */
NETIF_F_TSO             /* TCP Segmentation Offload */
NETIF_F_TSO6            /* TSO for IPv6 */
NETIF_F_UFO             /* UDP Fragmentation Offload */
NETIF_F_GSO             /* Generic Segmentation Offload */
NETIF_F_GRO             /* Generic Receive Offload */
NETIF_F_RXCSUM          /* HW RX checksum verification */
NETIF_F_HW_VLAN_CTAG_RX /* HW VLAN tag stripping */
NETIF_F_HW_VLAN_CTAG_TX /* HW VLAN tag insertion */
NETIF_F_NTUPLE          /* HW flow steering (n-tuple filter) */
NETIF_F_RXHASH          /* HW receive-side hash (RSS) */

/* GFP (Get Free Pages) flags */
GFP_KERNEL       /* can sleep, normal allocation */
GFP_ATOMIC       /* cannot sleep (interrupt/softirq context) */
GFP_NOWAIT       /* cannot sleep, no reclaim */
__GFP_NOFAIL     /* never fail (use rarely) */
__GFP_ZERO       /* zero the memory */
__GFP_DMA        /* must be DMA-able */
```

## Appendix B: Useful Kernel Networking Functions Reference

```c
/* sk_buff allocation */
alloc_skb(size, gfp)
netdev_alloc_skb(dev, len)
build_skb(data, frag_size)
napi_alloc_skb(napi, len)

/* sk_buff data manipulation */
skb_push(skb, len)           /* add header at front */
skb_pull(skb, len)           /* strip header at front */
skb_put(skb, len)            /* add data at tail */
skb_trim(skb, len)           /* trim tail */
skb_reserve(skb, len)        /* reserve headroom */
skb_headroom(skb)            /* bytes before data */
skb_tailroom(skb)            /* bytes after tail */

/* sk_buff queue operations */
skb_queue_tail(head, skb)
skb_queue_head(head, skb)
skb_dequeue(head)
skb_peek(head)
skb_queue_len(head)
skb_queue_walk(head, skb)    /* iterate without dequeue */

/* Protocol header accessors */
eth_hdr(skb)                 /* -> struct ethhdr* */
ip_hdr(skb)                  /* -> struct iphdr* */
ipv6_hdr(skb)                /* -> struct ipv6hdr* */
tcp_hdr(skb)                 /* -> struct tcphdr* */
udp_hdr(skb)                 /* -> struct udphdr* */

/* Checksum utilities */
ip_compute_csum(buff, len)
csum_tcpudp_magic(saddr, daddr, len, proto, sum)
skb_checksum(skb, offset, len, csum)
skb_csum_unnecessary(skb)

/* Socket wakeup */
sk->sk_data_ready(sk)        /* wakes recv() */
sk->sk_write_space(sk)       /* wakes send() when buffer available */
sk->sk_error_report(sk)      /* wakes poll for EPOLLERR */

/* netdev transmit */
dev_queue_xmit(skb)          /* normal path */
dev_direct_xmit(skb, queue_id) /* bypass qdisc */

/* RCU utilities */
rcu_read_lock() / rcu_read_unlock()
rcu_dereference(p)
rcu_assign_pointer(p, v)
synchronize_rcu()
call_rcu(&head, callback)

/* Memory */
kmalloc(size, gfp)
kzalloc(size, gfp)
kfree(ptr)
vmalloc(size)
vfree(ptr)
get_zeroed_page(gfp)
__get_free_pages(gfp, order)
```

---

*This document was written for Linux kernel version 6.x.*
*The networking subsystem evolves rapidly; always cross-reference with the*
*actual kernel source at https://elixir.bootlin.com/linux/latest/source*

*Good luck on your journey. The networking subsystem is vast but deeply*
*rewarding. Every packet you help improve flows through millions of machines.*

Now let me build this comprehensive guide. This will be a large, deeply detailed document.Here's your complete guide — a dense, production-grade reference. Here's what's packed inside:

**25 major sections covering:**

- **Mental model rewiring** — how to think in kernel terms (pipelines, concurrency, no malloc, no sleep in softirq)
- **Core data structures with full annotated field listings** — `sk_buff`, `net_device`, `struct sock`, `tcp_sock`, `struct proto`, `Qdisc`, `struct neighbour`, `nf_conn`
- **ASCII architecture diagrams** — full stack layout, sk_buff memory layout with head/data/tail/end pointers, TCP state machine, NIC ring buffers, qdisc hierarchy, netfilter hook points, DMA ring layout
- **Complete RX path** — from NIC wire → hardirq → softirq → NAPI poll → GRO → ip_rcv → tcp_v4_rcv → socket wakeup → userspace recv()
- **Complete TX path** — from send() → tcp_sendmsg → tcp_write_xmit → ip_output → neigh → qdisc → driver → NIC doorbell → DMA → wire
- **Deep TCP internals** — state machine, congestion control framework (cubic/bbr/reno plug-in model), SACK, RTT measurement, socket locking protocol
- **Netfilter/conntrack/NAT** — hook registration, NUD state machine, registering your own hook in a module
- **eBPF/XDP** — verifier lifecycle, XDP return codes, AF_XDP zero-copy, BPF map types
- **Traffic control** — qdisc framework, pfifo_fast bands, HTB hierarchy
- **Kernel dev workflow** — build, VM setup, debug tools (ftrace, KASAN, bpftrace one-liners), patch format, sending via `git send-email`, review cycle
- **Syzbot bug workflow** — how to reproduce and fix fuzzer-found bugs
- **12-month study plan** — week-by-week with concrete checkboxes
- **Function reference appendix** — all key networking functions in one place

The single most important thing to internalize first: **`sk_buff` is everything.** Every packet is one, and every layer only manipulates its pointers.