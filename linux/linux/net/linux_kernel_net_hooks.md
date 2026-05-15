# Linux Kernel Network Subsystem Hooks
## A Complete, In-Depth Guide — From Fundamentals to Rust Integration

---

## Table of Contents

1. [Mental Model: What Is a Hook?](#1-mental-model-what-is-a-hook)
2. [Linux Network Stack — The Big Picture](#2-linux-network-stack--the-big-picture)
3. [Core Data Structures You Must Know](#3-core-data-structures-you-must-know)
   - sk_buff (Socket Buffer)
   - net_device
   - sock / socket
   - net namespace
4. [The Netfilter Framework](#4-the-netfilter-framework)
   - Hook Points and Their Positions
   - nf_hook_ops Structure
   - Verdict Return Values
   - Writing a Netfilter Hook in C
   - Priority System
   - Connection Tracking
5. [eBPF Hooks in the Network Stack](#5-ebpf-hooks-in-the-network-stack)
   - XDP (eXpress Data Path)
   - TC (Traffic Control) BPF
   - Socket BPF Filters (cBPF / eBPF)
   - cgroup BPF Hooks
   - SK_MSG and SK_SKB
6. [NAPI — The Driver-Level Hook](#6-napi--the-driver-level-hook)
7. [Protocol Registration Hooks](#7-protocol-registration-hooks)
   - inet_add_protocol / net_protocol
   - Layer 3 Protocol Hooks
   - Layer 4 Protocol Hooks
8. [Socket-Level Hooks — proto and proto_ops](#8-socket-level-hooks--proto-and-proto_ops)
9. [LSM (Linux Security Module) Network Hooks](#9-lsm-linux-security-module-network-hooks)
10. [Tracepoints and kprobes in Networking](#10-tracepoints-and-kprobes-in-networking)
11. [Notification Chains — netdev_chain and inetaddr_chain](#11-notification-chains--netdev_chain-and-inetaddr_chain)
12. [Routing Hooks — FIB Rules and Custom Routes](#12-routing-hooks--fib-rules-and-custom-routes)
13. [The sk_buff Lifecycle Through All Hooks](#13-the-sk_buff-lifecycle-through-all-hooks)
14. [Complete C Module Examples](#14-complete-c-module-examples)
15. [Rust in the Linux Kernel — Network Hooks](#15-rust-in-the-linux-kernel--network-hooks)
16. [Comparison Table: Which Hook for Which Job?](#16-comparison-table-which-hook-for-which-job)
17. [Performance Characteristics](#17-performance-characteristics)
18. [Common Pitfalls and Debugging](#18-common-pitfalls-and-debugging)

---

## 1. Mental Model: What Is a Hook?

### The Concept of a Hook (Start from Zero)

A **hook** is a pre-defined location in a program's execution flow where you can **insert custom code** that runs automatically when execution reaches that point — without modifying the original code.

Think of it like this:

```
Normal flow (without hook):
  [Step A] --> [Step B] --> [Step C] --> [Step D]

Flow with hook at Step B:
  [Step A] --> [Step B] --> [YOUR CODE RUNS HERE] --> [Step C] --> [Step D]
                                    |
                          (can also MODIFY data,
                           DROP the packet,
                           or REDIRECT it)
```

In the Linux kernel's network subsystem, hooks let you:
- **Inspect** packets as they flow through the kernel
- **Modify** packet headers or payloads
- **Drop** packets (firewall behavior)
- **Redirect** packets to other interfaces
- **Count/meter** traffic (statistics, rate limiting)
- **Intercept** system calls related to networking

### Why Hooks Exist in Kernelspace

The Linux kernel is monolithic — everything runs in a single privileged address space. But not every feature belongs in the core kernel. Hooks provide:

1. **Extensibility** — Add features (NAT, firewall, VPN) without patching the core
2. **Modularity** — Load/unload kernel modules that use hooks at runtime
3. **Separation of concerns** — The core packet path stays clean; policies live in modules
4. **eBPF safety** — Run custom code in kernel space with a verifier-enforced sandbox

### The Hook Mental Model in the Network Stack

```
NIC Hardware
    |
    v
[DRIVER / NAPI poll()]          <-- Hook point 1: Driver RX hook
    |
    v
[XDP hook]                      <-- Hook point 2: eXpress Data Path (earliest)
    |
    v
[TC ingress hook]               <-- Hook point 3: Traffic Control (eBPF)
    |
    v
[Netfilter NF_INET_PRE_ROUTING] <-- Hook point 4: Netfilter (iptables/nftables)
    |
    v
[Routing Decision]
   /         \
  /           \
[local?]    [forward?]
  |               |
  v               v
[NF_LOCAL_IN]  [NF_FORWARD]     <-- Hook point 5 & 6
  |               |
  v               v
[Socket]    [NF_POST_ROUTING]   <-- Hook point 7
  |               |
  v               v
[Application] [TC egress hook]  <-- Hook point 8
              |
              v
           [NIC TX]
```

---

## 2. Linux Network Stack — The Big Picture

### Layers and Their Kernel Representation

```
OSI Layer        Linux Kernel Component           Key Files
-----------      --------------------------       -------------------------
Layer 7 (App)    User space (syscalls)            net/socket.c
Layer 4 (Trans)  TCP/UDP/SCTP/etc.               net/ipv4/tcp.c, udp.c
Layer 3 (Net)    IP (IPv4/IPv6)                  net/ipv4/ip_input.c
Layer 2 (Link)   Ethernet / netdev               net/ethernet/, drivers/net/
Layer 1 (Phys)   NIC driver                      drivers/net/ethernet/
```

### Packet RX (Receive) Path — Step by Step

```
1. NIC DMA → kernel ring buffer (memory)
2. NIC raises hardware interrupt
3. Interrupt handler: schedules NAPI softirq
4. NAPI poll(): calls driver's poll function
5. Driver creates sk_buff, calls netif_receive_skb()
6. XDP hook (if attached)
7. Generic Receive Offload (GRO)
8. TC ingress BPF (if attached)
9. Packet enters network layer: ip_rcv()
10. Netfilter PRE_ROUTING hook
11. Routing lookup: ip_route_input()
12. If local: Netfilter LOCAL_IN → deliver to socket
13. If forward: Netfilter FORWARD → ip_forward()
14. Socket receive queue → application read()
```

### Packet TX (Transmit) Path — Step by Step

```
1. Application: write() / send() / sendmsg()
2. Socket layer: sock->ops->sendmsg()
3. Protocol layer: tcp_sendmsg() / udp_sendmsg()
4. IP layer: ip_queue_xmit() → ip_output()
5. Netfilter LOCAL_OUT hook
6. Routing: ip_route_output()
7. Netfilter POST_ROUTING hook
8. dev_queue_xmit()
9. TC egress BPF (if attached)
10. Queueing discipline (qdisc)
11. Driver: dev->ndo_start_xmit()
12. DMA to NIC hardware
```

---

## 3. Core Data Structures You Must Know

Before you can write a single hook, you MUST understand these data structures.
Every hook receives or manipulates them.

---

### 3.1 `sk_buff` — The Packet Container

**What it is:** `sk_buff` (Socket Buffer) is THE central data structure in the Linux network stack. Every packet, from arrival at the NIC to delivery to userspace, lives inside an `sk_buff`.

**Definition** (simplified from `include/linux/skbuff.h`):

```c
struct sk_buff {
    /* --- Chaining --- */
    struct sk_buff      *next;        // linked list pointer
    struct sk_buff      *prev;        // linked list pointer

    /* --- Arrival metadata --- */
    ktime_t             tstamp;       // arrival timestamp
    struct net_device   *dev;         // device this packet arrived on

    /* --- Socket owner --- */
    struct sock         *sk;          // owning socket (NULL for forwarded pkts)

    /* --- Packet data pointers --- */
    unsigned char       *head;        // start of allocated buffer
    unsigned char       *data;        // start of actual packet data
    unsigned char       *tail;        // end of actual packet data
    unsigned char       *end;         // end of allocated buffer
    unsigned int        len;          // total length of packet data
    unsigned int        data_len;     // length of paged data

    /* --- Protocol info --- */
    __be16              protocol;     // ETH_P_IP, ETH_P_IPV6, etc.
    __u16               transport_header; // offset to L4 header
    __u16               network_header;   // offset to L3 header
    __u16               mac_header;       // offset to L2 header

    /* --- Flags --- */
    __u8                pkt_type;     // PACKET_HOST, PACKET_BROADCAST, etc.
    __u8                ip_summed;    // checksum status
    __u16               queue_mapping;// for multiqueue devices

    /* --- Connection tracking (Netfilter) --- */
    struct nf_conntrack *nfct;        // connection tracking entry

    /* --- Mark --- */
    __u32               mark;         // skb mark (used by routing, iptables)

    /* --- Hash --- */
    __u32               hash;         // flow hash

    /* ... many more fields ... */
};
```

#### Memory Layout of sk_buff

```
sk_buff struct
+-------------------+
| next / prev       |  (linked list for queues)
| dev               |  (which NIC)
| sk                |  (owning socket)
| head              |---> +---------------------------+
| data              |---> |  [headroom]               |  <- push headers here
| tail              |     |  [packet data: L2+L3+L4]  |  <- actual bytes
| end               |---> |  [tailroom]               |  <- append data here
| len               |     +---------------------------+
| protocol          |
| *_header offsets  |
+-------------------+

head <= data <= tail <= end

data..tail = current packet content
head..data = headroom (for prepending headers)
tail..end  = tailroom (for appending data)
```

#### Key sk_buff Operations

```c
/* Access headers */
struct iphdr  *iph = ip_hdr(skb);        // L3 header
struct tcphdr *tcph = tcp_hdr(skb);      // L4 header
struct ethhdr *eth = eth_hdr(skb);       // L2 header

/* Headroom/tailroom manipulation */
skb_push(skb, len);   // move data pointer BACK (add header)
skb_pull(skb, len);   // move data pointer FORWARD (consume header)
skb_put(skb, len);    // move tail pointer FORWARD (append data)
skb_reserve(skb, len); // move data AND tail (reserve headroom)

/* Cloning */
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);  // shallow copy
struct sk_buff *copy  = skb_copy(skb, GFP_ATOMIC);   // deep copy

/* Freeing */
kfree_skb(skb);        // decrement refcount, free if zero
consume_skb(skb);      // "normal" free (not dropped)
```

---

### 3.2 `net_device` — The Network Interface

**What it is:** Represents a network interface (eth0, lo, wlan0, etc.).

```c
struct net_device {
    char            name[IFNAMSIZ];     // "eth0", "lo", etc.
    unsigned long   state;             // IFF_UP, IFF_RUNNING, etc.
    unsigned int    flags;             // net device flags
    unsigned int    mtu;               // Maximum Transmission Unit
    unsigned char   dev_addr[MAX_ADDR_LEN]; // MAC address

    const struct net_device_ops *netdev_ops;  // driver callbacks
    const struct ethtool_ops    *ethtool_ops; // ethtool callbacks

    struct netdev_rx_queue  *_rx;      // per-queue RX info
    struct netdev_queue     *_tx;      // per-queue TX info

    struct net              *nd_net;   // network namespace
    /* ... */
};
```

#### `net_device_ops` — The Driver Hook Table

```c
struct net_device_ops {
    int  (*ndo_init)(struct net_device *dev);
    void (*ndo_uninit)(struct net_device *dev);
    int  (*ndo_open)(struct net_device *dev);
    int  (*ndo_stop)(struct net_device *dev);
    netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb,
                                   struct net_device *dev);
    void (*ndo_set_rx_mode)(struct net_device *dev);
    int  (*ndo_set_mac_address)(struct net_device *dev, void *addr);
    int  (*ndo_do_ioctl)(struct net_device *dev,
                          struct ifreq *ifr, int cmd);
    /* ... ~50 more callbacks ... */
};
```

Every `ndo_*` function is a hook that drivers implement. When the kernel calls `dev_queue_xmit()`, it internally calls `dev->netdev_ops->ndo_start_xmit()` — that is a hook invocation.

---

### 3.3 `sock` and `socket`

**Two different but related structures:**

```
struct socket   (VFS layer — represents a file descriptor)
    |
    v
struct sock     (protocol layer — contains protocol state)
    |
    v
struct tcp_sock / udp_sock / raw_sock (protocol-specific)
```

```c
struct socket {
    socket_state        state;          // SS_UNCONNECTED, SS_CONNECTED, etc.
    short               type;           // SOCK_STREAM, SOCK_DGRAM, etc.
    const struct proto_ops *ops;        // socket-level operations (syscall handlers)
    struct sock         *sk;            // pointer to protocol sock
    struct file         *file;          // back-pointer to VFS file
};

struct sock {
    struct sock_common  __sk_common;    // addr, port, state
    socket_lock_t       sk_lock;
    struct sk_buff_head sk_receive_queue; // incoming packets
    struct sk_buff_head sk_write_queue;   // outgoing packets
    void (*sk_state_change)(struct sock *sk);  // callback hook!
    void (*sk_data_ready)(struct sock *sk);    // callback hook!
    void (*sk_write_space)(struct sock *sk);   // callback hook!
    void (*sk_error_report)(struct sock *sk);  // callback hook!
    /* ... */
};
```

`sk_data_ready`, `sk_state_change` etc. are **socket-level hooks**. You can replace them to intercept events.

---

### 3.4 Network Namespaces (`struct net`)

Every network stack instance lives in a `struct net`. By default there is one (`init_net`). Containers get their own `struct net`.

```c
struct net {
    struct list_head    list;           // list of all namespaces
    struct proc_dir_entry *proc_net;
    struct net_device   *loopback_dev;  // lo interface
    struct netns_ipv4   ipv4;           // IPv4-specific state
    struct netns_ipv6   ipv6;           // IPv6-specific state
    /* ... */
};
```

When writing hooks, always be namespace-aware. Use `dev_net(dev)` to get the namespace from a device.

---

## 4. The Netfilter Framework

Netfilter is the PRIMARY hooking framework in the Linux network stack. `iptables`, `nftables`, `conntrack` (connection tracking), and NAT are all built on top of Netfilter.

### 4.1 Architecture

```
                    NETFILTER HOOK POINTS
                    =====================

  [NETWORK] ──> NF_INET_PRE_ROUTING ──> [ROUTING] ──> NF_INET_FORWARD ──> [OUTPUT NIC]
                                              |
                                              v
                                    NF_INET_LOCAL_IN
                                              |
                                              v
                                         [SOCKET]
                                              |
                                              v
                                    NF_INET_LOCAL_OUT ──> [ROUTING] ──> NF_INET_POST_ROUTING ──> [OUTPUT NIC]
```

More detailed view:

```
Incoming packet from NIC
        |
        v
  +-----------+
  | PRE_ROUTE |  NF_INET_PRE_ROUTING (hook #0)
  +-----------+
        |
        v
  [Routing decision: is this for me?]
        |
   -----+------
   |           |
   v           v
+---------+  +-------+
| LOCAL_IN|  |FORWARD|  NF_INET_LOCAL_IN (#1), NF_INET_FORWARD (#2)
+---------+  +-------+
   |           |
   v           v
[Socket]  [POST_ROUTING]
           NF_INET_POST_ROUTING (#4)

For locally generated traffic:
[Application] --> LOCAL_OUT (#3) --> [Routing] --> POST_ROUTING (#4)
```

### 4.2 Hook Numbers and Their Meaning

```c
/* Defined in include/uapi/linux/netfilter.h */

enum nf_inet_hooks {
    NF_INET_PRE_ROUTING,   /* 0: Before routing decision (incoming) */
    NF_INET_LOCAL_IN,      /* 1: After routing, packet IS for this host */
    NF_INET_FORWARD,       /* 2: After routing, packet must be forwarded */
    NF_INET_LOCAL_OUT,     /* 3: Before routing, packet from local process */
    NF_INET_POST_ROUTING,  /* 4: After routing, packet going out */
    NF_INET_NUMHOOKS       /* 5: sentinel, not a real hook */
};
```

**When to use which hook:**

| Hook              | Use Case                              |
|-------------------|---------------------------------------|
| PRE_ROUTING       | DNAT, port forwarding, early drop     |
| LOCAL_IN          | Firewall (INPUT chain in iptables)    |
| FORWARD           | Firewall (FORWARD chain)              |
| LOCAL_OUT         | Firewall (OUTPUT chain), SNAT         |
| POST_ROUTING      | SNAT/Masquerade, egress manipulation  |

### 4.3 The `nf_hook_ops` Structure

This is the registration structure for a Netfilter hook:

```c
/* include/linux/netfilter.h */
struct nf_hook_ops {
    /* Pointer to your hook function */
    nf_hookfn               *hook;

    /* The net_device to apply to (NULL = all devices) */
    struct net_device       *dev;

    /* Private data for your hook */
    void                    *priv;

    /* Protocol family: NFPROTO_IPV4, NFPROTO_IPV6, NFPROTO_NETDEV, etc. */
    u_int8_t                pf;

    /* Which hook point: NF_INET_PRE_ROUTING, etc. */
    unsigned int            hooknum;

    /* Priority: lower number = runs first */
    int                     priority;
};
```

#### Protocol Families (`pf` field)

```c
/* include/uapi/linux/netfilter.h */
#define NFPROTO_UNSPEC   0
#define NFPROTO_INET     1    /* Both IPv4 and IPv6 */
#define NFPROTO_IPV4     2    /* IPv4 only */
#define NFPROTO_ARP      3    /* ARP */
#define NFPROTO_NETDEV   5    /* Network device (for XDP-like hooks) */
#define NFPROTO_BRIDGE   7    /* Bridge */
#define NFPROTO_IPV6    10    /* IPv6 only */
```

### 4.4 Hook Function Signature

```c
/* The hook function type */
typedef unsigned int nf_hookfn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state);
```

**Parameters:**
- `priv`: your private data from `nf_hook_ops.priv`
- `skb`: the packet (socket buffer — THE most important parameter)
- `state`: metadata about the hook invocation

#### `nf_hook_state` Structure

```c
struct nf_hook_state {
    unsigned int        hook;   /* Which hook number (0-4) */
    u_int8_t            pf;     /* Protocol family */
    struct net_device   *in;    /* Input device */
    struct net_device   *out;   /* Output device */
    struct sock         *sk;    /* Socket (may be NULL) */
    struct net          *net;   /* Network namespace */
    int (*okfn)(struct net *, struct sock *, struct sk_buff *); /* continue fn */
};
```

### 4.5 Verdict Return Values

Your hook function MUST return one of these:

```c
/* include/uapi/linux/netfilter.h */

#define NF_DROP   0   /* DROP: discard the packet entirely */
#define NF_ACCEPT 1   /* ACCEPT: continue normal processing */
#define NF_STOLEN 2   /* STOLEN: you own the packet now, do NOT free it */
#define NF_QUEUE  3   /* QUEUE: send to userspace via nfnetlink */
#define NF_REPEAT 4   /* REPEAT: call this hook again */
#define NF_STOP   5   /* STOP: like ACCEPT but skip remaining hooks */
```

**Visual flow of verdicts:**

```
Hook function called with skb
        |
        v
  +------------------+
  | return NF_ACCEPT |  --> packet continues to next hook / processing
  +------------------+
  | return NF_DROP   |  --> kfree_skb() called, packet gone
  +------------------+
  | return NF_STOLEN |  --> packet is yours; you MUST free it later
  +------------------+
  | return NF_QUEUE  |  --> packet goes to userspace queue (nfqueue)
  +------------------+
  | return NF_REPEAT |  --> hook is called again for this packet
  +------------------+
```

**Critical rule:** If you return `NF_STOLEN`, YOU are responsible for eventually calling `kfree_skb(skb)` or `consume_skb(skb)`. If you forget, you have a memory leak.

### 4.6 Priority System

Multiple hooks can be registered on the same hook point. They run in **ascending priority order** (lowest number first).

```c
/* include/uapi/linux/netfilter_ipv4.h */
enum nf_ip_hook_priorities {
    NF_IP_PRI_FIRST          = INT_MIN,     /* -2147483648 */
    NF_IP_PRI_RAW_BEFORE_DEFRAG = -450,
    NF_IP_PRI_CONNTRACK_DEFRAG = -400,
    NF_IP_PRI_RAW            = -300,
    NF_IP_PRI_SELINUX_FIRST  = -225,
    NF_IP_PRI_CONNTRACK      = -200,        /* conntrack runs here */
    NF_IP_PRI_MANGLE         = -150,        /* mangle table */
    NF_IP_PRI_NAT_DST        = -100,        /* DNAT */
    NF_IP_PRI_FILTER         =    0,        /* filter table (iptables) */
    NF_IP_PRI_SECURITY       =   50,        /* security table */
    NF_IP_PRI_NAT_SRC        =  100,        /* SNAT */
    NF_IP_PRI_SELINUX_LAST   =  225,
    NF_IP_PRI_CONNTRACK_HELPER = 300,
    NF_IP_PRI_LAST           = INT_MAX      /* +2147483647 */
};
```

**Rule:** Run before conntrack? Use priority < -200. Run after filter/iptables? Use priority > 0.

### 4.7 Registering and Unregistering Hooks

```c
/* Register a single hook */
int nf_register_net_hook(struct net *net, const struct nf_hook_ops *ops);

/* Unregister a single hook */
void nf_unregister_net_hook(struct net *net, const struct nf_hook_ops *ops);

/* Register multiple hooks at once */
int nf_register_net_hooks(struct net *net,
                           const struct nf_hook_ops *reg,
                           unsigned int n);

/* Unregister multiple hooks */
void nf_unregister_net_hooks(struct net *net,
                              const struct nf_hook_ops *reg,
                              unsigned int n);
```

### 4.8 Complete Netfilter Hook — C Module Example

This module drops all TCP packets going to port 8080:

```c
/* File: nf_drop_8080.c */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/skbuff.h>
#include <linux/inet.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Drop TCP packets to port 8080");
MODULE_VERSION("1.0");

/*
 * nf_hook_ops: our hook registration structure.
 * We declare it as static so it lives for the module lifetime.
 */
static struct nf_hook_ops nfho;

/*
 * The hook function — called for every IPv4 packet at PRE_ROUTING.
 *
 * Parameters:
 *   priv  : our private data (NULL here, we don't use it)
 *   skb   : the packet buffer — THIS IS THE PACKET
 *   state : hook metadata (in/out device, hook number, etc.)
 *
 * Returns: NF_ACCEPT or NF_DROP
 */
static unsigned int hook_func(void *priv,
                               struct sk_buff *skb,
                               const struct nf_hook_state *state)
{
    struct iphdr  *iph;   /* IPv4 header pointer */
    struct tcphdr *tcph;  /* TCP header pointer */

    /* Safety check: skb must not be NULL */
    if (!skb)
        return NF_ACCEPT;

    /* Get the IP header.
     * ip_hdr(skb) uses skb->network_header offset to find it.
     * At PRE_ROUTING, the IP header is already parsed by the kernel.
     */
    iph = ip_hdr(skb);

    /* Only process TCP packets.
     * iph->protocol is the IP protocol number:
     *   IPPROTO_TCP = 6
     *   IPPROTO_UDP = 17
     *   IPPROTO_ICMP = 1
     */
    if (iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;  /* Not TCP, let it pass */

    /*
     * Get the TCP header.
     * tcp_hdr(skb) = skb->head + skb->transport_header
     *
     * IMPORTANT: At PRE_ROUTING, transport_header may NOT be set yet
     * for all packet types. We must manually compute it or use
     * skb_transport_header() after calling skb_set_transport_header().
     *
     * Safer approach: compute offset from IP header.
     */
    tcph = (struct tcphdr *)((__u32 *)iph + iph->ihl);

    /*
     * tcph->dest is the destination port in network byte order.
     * ntohs() converts from network byte order to host byte order.
     * Network byte order = Big Endian.
     * Host byte order on x86 = Little Endian.
     */
    if (ntohs(tcph->dest) == 8080) {
        /* Log the dropped packet */
        printk(KERN_INFO "nf_drop_8080: Dropping TCP packet to port 8080 "
               "from %pI4\n", &iph->saddr);
        /* DROP the packet — kernel will call kfree_skb(skb) */
        return NF_DROP;
    }

    return NF_ACCEPT;  /* Let all other packets through */
}

/*
 * Module initialization — runs when the module is loaded (insmod).
 * This is where we register our hook.
 */
static int __init nf_drop_8080_init(void)
{
    int ret;

    /* Fill in the hook_ops structure */
    nfho.hook     = hook_func;          /* Our function */
    nfho.hooknum  = NF_INET_PRE_ROUTING; /* Hook point */
    nfho.pf       = PF_INET;            /* IPv4 (= NFPROTO_IPV4) */
    nfho.priority = NF_IP_PRI_FIRST;    /* Run before everything */
    nfho.dev      = NULL;               /* Apply to ALL devices */
    nfho.priv     = NULL;               /* No private data */

    /*
     * Register the hook in the init network namespace (&init_net).
     * For container-aware code, you would iterate all namespaces
     * or use pernet_operations.
     */
    ret = nf_register_net_hook(&init_net, &nfho);
    if (ret < 0) {
        printk(KERN_ERR "nf_drop_8080: Failed to register hook: %d\n", ret);
        return ret;
    }

    printk(KERN_INFO "nf_drop_8080: Hook registered. Dropping port 8080.\n");
    return 0;
}

/*
 * Module cleanup — runs when the module is removed (rmmod).
 * MUST unregister the hook here. Forgetting this = kernel panic on rmmod.
 */
static void __exit nf_drop_8080_exit(void)
{
    /* Unregister MUST be called before module unloads.
     * If a packet is currently in the hook when we unregister,
     * nf_unregister_net_hook() will synchronize (wait for it to finish).
     */
    nf_unregister_net_hook(&init_net, &nfho);
    printk(KERN_INFO "nf_drop_8080: Hook unregistered.\n");
}

module_init(nf_drop_8080_init);
module_exit(nf_drop_8080_exit);
```

**Makefile for building:**

```makefile
# Makefile
obj-m += nf_drop_8080.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

**Build and load:**
```bash
make
sudo insmod nf_drop_8080.ko
dmesg | tail        # see printk output
sudo rmmod nf_drop_8080
```

---

### 4.9 Advanced: Modifying Packets in a Netfilter Hook

To modify a packet, you must be careful about:
1. **Checksums** — IP and TCP/UDP checksums must be recalculated
2. **skb writability** — You must call `skb_make_writable()` before modifying
3. **skb_linearize** — If the skb has paged data, linearize it first

```c
static unsigned int modify_ttl_hook(void *priv,
                                     struct sk_buff *skb,
                                     const struct nf_hook_state *state)
{
    struct iphdr *iph;

    if (!skb)
        return NF_ACCEPT;

    /*
     * skb_make_writable(): ensures the packet data is in a writable
     * memory region. Some packets share memory via clone, so writing
     * to them directly would corrupt other packets (copy-on-write).
     * This function makes a private copy if needed.
     *
     * sizeof(struct iphdr) = minimum bytes we need to modify.
     */
    if (!skb_make_writable(skb, sizeof(struct iphdr)))
        return NF_DROP;

    iph = ip_hdr(skb);

    /* Modify the TTL field.
     * ip_decrease_ttl() subtracts 1 and updates checksum correctly.
     * Alternatively, manually update:
     *   ip_send_check(iph) recalculates the IP header checksum.
     */
    if (iph->ttl > 64) {
        iph->ttl = 64;
        ip_send_check(iph);  /* Recalculate IP checksum after change */
    }

    return NF_ACCEPT;
}
```

---

## 5. eBPF Hooks in the Network Stack

**What is eBPF?** eBPF (extended Berkeley Packet Filter) is a virtual machine inside the Linux kernel that lets you run sandboxed programs in kernel space. The kernel **verifies** the program before running it — ensuring it cannot crash the kernel, loop forever, or access arbitrary memory.

Think of eBPF as: "write kernel code in a restricted language, the kernel verifies it's safe, then runs it at a hook point."

```
User writes eBPF program (C with restrictions)
    |
    v
clang/LLVM compiles to eBPF bytecode (.o file)
    |
    v
bpf() syscall loads bytecode into kernel
    |
    v
Kernel VERIFIER checks:
  - No infinite loops
  - No out-of-bounds memory access
  - No uninitialized memory reads
  - Correct function call conventions
    |
    v
JIT compiler converts eBPF bytecode to native machine code
    |
    v
Program is ATTACHED to a hook point
    |
    v
Runs for every packet at that hook point
```

### 5.1 XDP — eXpress Data Path

**What is XDP?** XDP is the EARLIEST hook in the receive path — it runs BEFORE the sk_buff is even allocated. This makes it incredibly fast.

```
NIC hardware raises interrupt
    |
    v
Interrupt handler
    |
    v
NAPI poll()
    |
    v
+--------------+
|  XDP HOOK    |  <--- Runs HERE (before sk_buff allocation!)
+--------------+
    |
    v (if XDP_PASS)
sk_buff allocated
    |
    v
Rest of network stack...
```

#### XDP Operation Modes

```
XDP_NATIVE (offloaded)     Runs in NIC driver before DMA, fastest
XDP_NATIVE (driver)        Runs in driver's NAPI poll, very fast
XDP_GENERIC (skb mode)     Runs after sk_buff allocated, slowest but any driver
```

#### XDP Return Codes

```c
/* include/uapi/linux/bpf.h */
enum xdp_action {
    XDP_ABORTED = 0,  /* Bug in program — drop + trace */
    XDP_DROP,         /* Silently discard the packet */
    XDP_PASS,         /* Pass to normal network stack */
    XDP_TX,           /* Retransmit on same interface (bounce) */
    XDP_REDIRECT,     /* Redirect to another interface/CPU/socket */
};
```

#### XDP Context Structure

```c
/* The "skb-equivalent" for XDP */
struct xdp_md {
    __u32 data;        /* pointer to packet data start */
    __u32 data_end;    /* pointer to packet data end */
    __u32 data_meta;   /* pointer to metadata area */
    __u32 ingress_ifindex; /* arriving interface index */
    __u32 rx_queue_index;  /* RX queue index */
    __u32 egress_ifindex;  /* used with XDP_REDIRECT */
};
```

#### Complete XDP Program in C (eBPF C)

```c
/* File: xdp_drop_icmp.c — eBPF program to drop ICMP packets */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <bpf/bpf_helpers.h>  /* eBPF helper functions */
#include <bpf/bpf_endian.h>   /* bpf_ntohs(), bpf_htons() */

/*
 * SEC() macro: defines the ELF section name.
 * The loader reads section names to know what type of eBPF program this is
 * and which hook to attach it to.
 */
SEC("xdp")
int xdp_drop_icmp(struct xdp_md *ctx)
{
    /*
     * In eBPF XDP programs, you cannot use pointers directly.
     * You must cast data/data_end offsets to void* and do your own
     * bounds checking. The VERIFIER will reject programs that
     * access memory beyond data_end.
     */
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    /* Ethernet header */
    struct ethhdr *eth = data;

    /*
     * BOUNDS CHECK — MANDATORY.
     * If (eth + 1) > data_end, the Ethernet header doesn't fit in
     * the packet. The verifier requires this check.
     * "(eth + 1)" means "pointer past end of struct ethhdr"
     */
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;  /* Malformed or truncated — let stack handle */

    /* Only process IPv4 packets */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    /* IPv4 header starts right after Ethernet header */
    struct iphdr *iph = (struct iphdr *)(eth + 1);

    /* Bounds check for IP header */
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    /* Check IP protocol */
    if (iph->protocol == IPPROTO_ICMP) {
        /* Optional: log using eBPF trace */
        bpf_printk("XDP: dropping ICMP from %u\n", iph->saddr);
        return XDP_DROP;  /* Drop ICMP */
    }

    return XDP_PASS;
}

/*
 * eBPF programs MUST have a GPL-compatible license
 * or the verifier will reject them for using GPL-only helpers.
 */
char _license[] SEC("license") = "GPL";
```

**Compile and load XDP:**

```bash
# Compile eBPF C to eBPF bytecode
clang -O2 -target bpf -c xdp_drop_icmp.c -o xdp_drop_icmp.o

# Attach to interface eth0 (using ip tool)
sudo ip link set dev eth0 xdp obj xdp_drop_icmp.o sec xdp

# Or using xdp-tools
sudo xdp-loader load eth0 xdp_drop_icmp.o

# Verify
ip link show eth0 | grep xdp

# Detach
sudo ip link set dev eth0 xdp off
```

---

### 5.2 TC BPF — Traffic Control Hooks

TC BPF hooks run slightly LATER than XDP (after sk_buff is allocated). They are more flexible because they have access to the full `sk_buff`.

```
INGRESS path:
  [XDP] --> [sk_buff created] --> [TC ingress qdisc] --> [IP layer]
                                          ^
                                   TC BPF hook runs here

EGRESS path:
  [IP layer] --> [TC egress qdisc] --> [NIC driver TX]
                        ^
                 TC BPF hook runs here
```

TC BPF uses the `__sk_buff` structure (a restricted view of `sk_buff`):

```c
/* eBPF-visible subset of sk_buff */
struct __sk_buff {
    __u32 len;          /* Total packet length */
    __u32 pkt_type;     /* PACKET_HOST, PACKET_BROADCAST, etc. */
    __u32 mark;         /* skb->mark */
    __u32 queue_mapping;
    __u32 protocol;     /* ETH_P_IP etc. */
    __u32 vlan_present;
    __u32 vlan_tci;
    __u32 vlan_proto;
    __u32 priority;
    __u32 ingress_ifindex;
    __u32 ifindex;
    __u32 tc_index;
    __u32 cb[5];        /* control buffer (scratch space) */
    __u32 hash;
    __u32 tc_classid;
    __u32 data;         /* pointer to packet start */
    __u32 data_end;     /* pointer to packet end */
    /* ... more fields ... */
};
```

#### TC BPF Return Codes

```c
/* include/uapi/linux/pkt_cls.h */
#define TC_ACT_UNSPEC      (-1)   /* Use default action */
#define TC_ACT_OK           0     /* Accept, continue */
#define TC_ACT_SHOT         2     /* Drop the packet */
#define TC_ACT_STOLEN       4     /* Consume (you own it now) */
#define TC_ACT_QUEUED       5     /* Queue for later */
#define TC_ACT_REPEAT       6     /* Redo classification */
#define TC_ACT_REDIRECT     7     /* Redirect to another device */
```

#### TC BPF Program Example

```c
/* File: tc_mark.c — mark packets from specific IP */
#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

SEC("tc")
int tc_mark_packets(struct __sk_buff *skb)
{
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return TC_ACT_OK;

    struct iphdr *iph = (struct iphdr *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return TC_ACT_OK;

    /* Mark packets from 10.0.0.1 */
    if (iph->saddr == bpf_htonl(0x0A000001)) {  /* 10.0.0.1 */
        /* skb->mark is writable from TC BPF */
        skb->mark = 42;
        bpf_printk("TC: marked packet from 10.0.0.1\n");
    }

    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
```

**Attach TC BPF:**

```bash
# Create clsact qdisc (required for TC BPF)
sudo tc qdisc add dev eth0 clsact

# Attach to ingress
sudo tc filter add dev eth0 ingress bpf da obj tc_mark.o sec tc

# Attach to egress
sudo tc filter add dev eth0 egress bpf da obj tc_mark.o sec tc

# Show
sudo tc filter show dev eth0 ingress

# Remove
sudo tc qdisc del dev eth0 clsact
```

---

### 5.3 Socket BPF Filters (cBPF / eBPF)

**What it is:** Attach a BPF filter directly to a socket. Only packets matching the filter are delivered to the socket. This is the original BPF (Berkeley Packet Filter) mechanism — `tcpdump` uses this!

```
Network stack delivers packet to socket
    |
    v
+----------------+
| Socket BPF     |  <-- runs before packet enters receive buffer
| filter         |
+----------------+
    |              \
    v               v
[pass to app]    [drop silently]
```

```c
/* Attaching a BPF filter to a raw socket (classic BPF) */
#include <sys/socket.h>
#include <linux/filter.h>
#include <arpa/inet.h>

/* Classic BPF bytecode to accept only ICMP packets:
 * ldh [12]         ; load 2 bytes at offset 12 (EtherType)
 * jeq #0x0800, L1  ; if IPv4, jump to L1
 * ret #0           ; else drop
 * L1: ldb [23]     ; load byte at offset 23 (IP protocol)
 * jeq #0x01, L2    ; if ICMP (1), jump to L2
 * ret #0           ; else drop
 * L2: ret #65535   ; accept all bytes
 */
struct sock_filter icmp_filter[] = {
    { 0x28, 0, 0, 0x0000000c },  /* ldh  [12] */
    { 0x15, 0, 3, 0x00000800 },  /* jeq  #0x800 */
    { 0x30, 0, 0, 0x00000017 },  /* ldb  [23] */
    { 0x15, 0, 1, 0x00000001 },  /* jeq  #0x1 */
    { 0x06, 0, 0, 0x0000ffff },  /* ret  #65535 */
    { 0x06, 0, 0, 0x00000000 },  /* ret  #0 */
};

struct sock_fprog prog = {
    .len    = sizeof(icmp_filter) / sizeof(icmp_filter[0]),
    .filter = icmp_filter,
};

int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

/* SO_ATTACH_FILTER attaches the BPF program to the socket */
setsockopt(sock, SOL_SOCKET, SO_ATTACH_FILTER, &prog, sizeof(prog));
```

---

### 5.4 cgroup BPF Hooks

cgroup BPF hooks attach programs at the cgroup level — affecting all sockets/processes in a cgroup.

```
Process in cgroup A
    |
    v
socket() syscall
    |
    v
connect() / bind() / sendmsg()
    |
    v
+------------------+
| cgroup BPF hook  |  <-- runs here, can modify/block
+------------------+
    |
    v
Network stack
```

Hook types:
```c
BPF_CGROUP_INET_INGRESS    /* ingress packets to sockets in cgroup */
BPF_CGROUP_INET_EGRESS     /* egress packets from sockets in cgroup */
BPF_CGROUP_INET_SOCK_CREATE /* when a socket is created */
BPF_CGROUP_SOCK_OPS        /* TCP socket state changes */
BPF_CGROUP_DEVICE          /* device access */
BPF_CGROUP_INET4_BIND      /* IPv4 bind() */
BPF_CGROUP_INET6_BIND      /* IPv6 bind() */
BPF_CGROUP_INET4_CONNECT   /* IPv4 connect() */
BPF_CGROUP_INET6_CONNECT   /* IPv6 connect() */
BPF_CGROUP_INET4_GETPEERNAME
BPF_CGROUP_INET6_GETPEERNAME
BPF_CGROUP_UDP4_SENDMSG
BPF_CGROUP_UDP6_SENDMSG
```

---

## 6. NAPI — The Driver-Level Hook

**What is NAPI?** NAPI (New API) is the interrupt-mitigation mechanism for network drivers. Instead of handling each packet in a separate interrupt, the driver:

1. Gets ONE interrupt when packets arrive
2. Disables further interrupts for that NIC queue
3. Schedules a **softirq** (soft interrupt) to run in process context
4. The softirq calls the driver's **poll function** in a loop, draining the receive queue
5. When the queue is empty, re-enables interrupts

```
NIC raises hardware interrupt
    |
    v
CPU interrupt handler (hardirq context, very fast)
    |
    | schedule softirq
    v
NET_RX_SOFTIRQ fires (process context, can sleep? NO — still softirq)
    |
    v
net_rx_action() loops over NAPI instances
    |
    v
+----------------------------+
| driver->poll() CALLED HERE |  <-- This is the NAPI hook
+----------------------------+
    |
    v (for each packet in ring buffer)
alloc sk_buff
copy/DMA packet data into sk_buff
call netif_receive_skb(skb)
    |
    v
Packet enters network stack
```

### 6.1 How a Driver Implements NAPI

```c
/* Step 1: Initialize NAPI in driver probe */
struct my_driver_priv {
    struct net_device *dev;
    struct napi_struct napi;   /* NAPI instance per RX queue */
    /* ... */
};

/* Step 2: Initialize NAPI with poll function and weight */
netif_napi_add(dev,           /* net_device */
               &priv->napi,   /* napi_struct to initialize */
               my_poll,       /* Your poll function */
               64);           /* NAPI weight (max packets per poll) */

/* Step 3: In interrupt handler, schedule NAPI */
static irqreturn_t my_interrupt(int irq, void *dev_id)
{
    struct my_driver_priv *priv = dev_id;

    /* Disable NIC interrupts for this queue */
    my_hw_disable_rx_irq(priv);

    /* Schedule NAPI poll — returns true if scheduled */
    napi_schedule(&priv->napi);

    return IRQ_HANDLED;
}

/* Step 4: The NAPI poll function — THE HOOK */
static int my_poll(struct napi_struct *napi, int budget)
{
    struct my_driver_priv *priv =
        container_of(napi, struct my_driver_priv, napi);
    int packets_processed = 0;

    /* Process up to `budget` packets */
    while (packets_processed < budget) {
        struct sk_buff *skb;
        struct my_hw_desc *desc;

        /* Check if hardware has a packet ready */
        desc = my_hw_get_next_rx(priv);
        if (!desc)
            break;  /* No more packets */

        /* Allocate an sk_buff */
        skb = netdev_alloc_skb(priv->dev, desc->length);
        if (!skb) {
            priv->dev->stats.rx_dropped++;
            break;
        }

        /* Copy packet data into sk_buff */
        memcpy(skb_put(skb, desc->length), desc->data, desc->length);

        /* Set protocol (the kernel needs to know this for routing) */
        skb->protocol = eth_type_trans(skb, priv->dev);

        /* Hand off to network stack
         * This is where XDP is checked, then normal stack processing begins
         */
        netif_receive_skb(skb);

        packets_processed++;
        my_hw_advance_rx(priv);  /* Tell hardware we consumed this descriptor */
    }

    /* If we processed fewer than budget, we drained the queue */
    if (packets_processed < budget) {
        /* Re-enable interrupts */
        napi_complete_done(napi, packets_processed);
        my_hw_enable_rx_irq(priv);
    }

    return packets_processed;
}
```

**Mental model:** `my_poll` is a hook that the kernel calls repeatedly to drain the NIC's receive queue. The driver author "hooks into" the kernel's softirq processing by registering this poll function via `netif_napi_add`.

---

## 7. Protocol Registration Hooks

At Layer 3 and Layer 4, protocols register themselves with hook tables. This is how `IP`, `ARP`, `TCP`, `UDP`, `ICMP` etc. are plugged into the kernel.

### 7.1 Layer 2 → Layer 3 Dispatch: `ptype_base`

When `netif_receive_skb()` is called, it looks up the EtherType in a hash table called `ptype_base` and calls the registered handler:

```c
/* Each L3 protocol registers a packet_type */
struct packet_type {
    __be16              type;   /* ETH_P_IP, ETH_P_IPV6, ETH_P_ARP, etc. */
    bool                ignore_outgoing;
    struct net_device   *dev;   /* NULL = all devices */

    /* The RX handler — this IS the hook function */
    int (*func)(struct sk_buff *skb,
                struct net_device *dev,
                struct packet_type *pt,
                struct net_device *orig_dev);

    /* Optional TX handler */
    int (*list_func)(struct list_head *head,
                     struct packet_type *pt,
                     struct net_device *orig_dev);

    void *af_packet_priv;
    struct list_head list;
};
```

**How IPv4 registers itself** (from `net/ipv4/af_inet.c`):

```c
/* IPv4 registers its handler for ETH_P_IP packets */
static struct packet_type ip_packet_type __read_mostly = {
    .type = cpu_to_be16(ETH_P_IP),  /* 0x0800 */
    .func = ip_rcv,                  /* ip_rcv is the L3 entry point */
    .list_func = ip_list_rcv,
};

/* Called at kernel startup */
dev_add_pack(&ip_packet_type);
```

**Registering your own L3 protocol handler:**

```c
/* Intercept all IPv4 packets at L2/L3 boundary */
static int my_ip_sniffer(struct sk_buff *skb,
                          struct net_device *dev,
                          struct packet_type *pt,
                          struct net_device *orig_dev)
{
    struct iphdr *iph = (struct iphdr *)skb->data;
    printk(KERN_INFO "Got packet from %pI4 to %pI4\n",
           &iph->saddr, &iph->daddr);

    /* IMPORTANT: We must not consume the skb here if we want
     * normal IP processing to continue. This handler gets a CLONE.
     * The real ip_rcv() also gets called.
     * Return 0 = we consumed our clone
     */
    kfree_skb(skb);  /* Free OUR copy */
    return 0;
}

static struct packet_type my_sniffer_ptype = {
    .type = cpu_to_be16(ETH_P_IP),  /* ETH_P_ALL = 0x0003 for all types */
    .func = my_ip_sniffer,
    .dev  = NULL,
};

/* Register */
dev_add_pack(&my_sniffer_ptype);

/* Unregister */
dev_remove_pack(&my_sniffer_ptype);
```

**Important:** When multiple handlers are registered for the same EtherType, each gets a **clone** of the sk_buff. The original is passed to the first (real) handler.

---

### 7.2 Layer 4 Protocol Hooks: `net_protocol`

When `ip_local_deliver_finish()` receives a packet for the local machine, it looks up the IP protocol number (TCP=6, UDP=17, etc.) in `inet_protos[]` array and calls the handler.

```c
/* Each L4 protocol registers a net_protocol */
struct net_protocol {
    /* Main receive handler — this IS the L4 hook */
    int (*early_demux)(struct sk_buff *skb);   /* fast path (optional) */
    int (*early_demux_handler)(struct sk_buff *skb);
    int (*handler)(struct sk_buff *skb);        /* main handler */

    /* Error handler (called for ICMP errors) */
    int (*err_handler)(struct sk_buff *skb, u32 info);

    unsigned int    flags;
    unsigned char   no_policy;  /* don't check IPsec policies */
};
```

**How TCP registers** (from `net/ipv4/af_inet.c`):

```c
static const struct net_protocol tcp_protocol = {
    .early_demux        = tcp_v4_early_demux,
    .early_demux_handler = tcp_v4_early_demux,
    .handler            = tcp_v4_rcv,      /* main TCP entry point */
    .err_handler        = tcp_v4_err,      /* handle ICMP errors for TCP */
    .no_policy          = 1,
    .flags              = INET_PROTO_NOPOLICY | INET_PROTO_ICMP_MAP,
};

/* Register TCP for protocol number 6 */
inet_add_protocol(&tcp_protocol, IPPROTO_TCP);
```

**Register your own L4 protocol handler:**

```c
/* WARNING: You CANNOT replace TCP/UDP (protocol numbers in use).
 * Use an unused protocol number (e.g., 253 or 254 for testing).
 * Or use raw sockets.
 */
static int my_proto_handler(struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);
    printk(KERN_INFO "my_proto: received %d bytes from %pI4\n",
           skb->len, &iph->saddr);

    /* Consume the skb */
    kfree_skb(skb);
    return 0;
}

static const struct net_protocol my_protocol = {
    .handler     = my_proto_handler,
    .no_policy   = 1,
};

/* Register for protocol number 253 (unassigned by IANA) */
if (inet_add_protocol(&my_protocol, 253) < 0) {
    printk(KERN_ERR "Cannot register protocol 253\n");
}

/* Unregister */
inet_del_protocol(&my_protocol, 253);
```

---

## 8. Socket-Level Hooks — `proto` and `proto_ops`

### 8.1 Two Levels of Socket Operations

```
User calls: connect(fd, addr, len)
    |
    v
sys_connect() in kernel
    |
    v
sock->ops->connect()      <-- proto_ops (VFS level hook)
    |
    v
sock->sk->prot->connect() <-- proto (protocol level hook)
```

### 8.2 `proto_ops` — VFS-to-Socket Bridge

```c
/* One per socket type (SOCK_STREAM / SOCK_DGRAM / etc.) per address family */
struct proto_ops {
    int         family;     /* AF_INET, AF_INET6, AF_UNIX, etc. */
    struct module *owner;

    /* All socket syscalls map to these function pointers */
    int  (*bind)   (struct socket *sock, struct sockaddr *myaddr, int sockaddr_len);
    int  (*connect)(struct socket *sock, struct sockaddr *vaddr,  int sockaddr_len, int flags);
    int  (*accept) (struct socket *sock, struct socket *newsock,  struct proto_accept_arg *arg);
    int  (*listen) (struct socket *sock, int backlog);
    int  (*sendmsg)(struct socket *sock, struct msghdr *m, size_t total_len);
    int  (*recvmsg)(struct socket *sock, struct msghdr *m, size_t total_len, int flags);
    int  (*setsockopt)(struct socket *sock, int level, int optname, sockptr_t optval, unsigned int optlen);
    int  (*getsockopt)(struct socket *sock, int level, int optname, char __user *optval, int __user *optlen);
    int  (*shutdown)(struct socket *sock, int flags);
    /* ... more ... */
};
```

**TCP's proto_ops** (from `net/ipv4/af_inet.c`):

```c
const struct proto_ops inet_stream_ops = {
    .family      = PF_INET,
    .owner       = THIS_MODULE,
    .bind        = inet_bind,
    .connect     = inet_stream_connect,  /* TCP connect */
    .accept      = inet_accept,
    .listen      = inet_listen,
    .sendmsg     = inet_sendmsg,
    .recvmsg     = inet_recvmsg,
    .setsockopt  = sock_common_setsockopt,
    .getsockopt  = sock_common_getsockopt,
    .shutdown    = inet_shutdown,
    /* ... */
};
```

### 8.3 `proto` — Protocol Implementation Hooks

```c
/* Lower level than proto_ops — this is the actual protocol implementation */
struct proto {
    char            name[32];   /* "TCP", "UDP", etc. */
    struct module   *owner;

    /* Core operations */
    int  (*connect)   (struct sock *sk, struct sockaddr *uaddr, int addr_len);
    int  (*disconnect)(struct sock *sk, int flags);
    int  (*accept)    (struct sock *sk, int flags, int *err, bool kern);
    int  (*init)      (struct sock *sk);  /* called when socket is created */
    void (*destroy)   (struct sock *sk);  /* called when socket is freed */
    void (*shutdown)  (struct sock *sk, int how);
    int  (*setsockopt)(struct sock *sk, int level, int optname, sockptr_t optval, unsigned int optlen);
    int  (*getsockopt)(struct sock *sk, int level, int optname, char __user *optval, int __user *optlen);
    int  (*sendmsg)   (struct sock *sk, struct msghdr *msg, size_t len);
    int  (*recvmsg)   (struct sock *sk, struct msghdr *msg, size_t len, int flags, int *addr_len);
    int  (*bind)      (struct sock *sk, struct sockaddr *uaddr, int addr_len);
    int  (*backlog_rcv)(struct sock *sk, struct sk_buff *skb);  /* RX hook */
    void (*release_cb)(struct sock *sk);

    /* Memory accounting */
    struct percpu_counter   sockets_allocated;
    int                     sysctl_mem[3];
    /* ... */
};
```

### 8.4 Replacing Socket Callbacks — A Power Technique

You can intercept a specific socket's events by replacing its callback pointers:

```c
/*
 * Technique: Replace sk_data_ready callback on a TCP listening socket
 * to get notified when new data arrives.
 * Used by: TLS-in-kernel (ktls), kTCP, various in-kernel proxies.
 */

typedef void (*sk_data_ready_t)(struct sock *sk);

static sk_data_ready_t original_data_ready;

static void my_data_ready(struct sock *sk)
{
    printk(KERN_INFO "Data arrived on socket %p!\n", sk);

    /* MUST call the original to wake up the application */
    original_data_ready(sk);
}

/* In your module initialization, after obtaining the sock pointer: */
void intercept_socket(struct sock *sk)
{
    write_lock_bh(&sk->sk_callback_lock);
    original_data_ready = sk->sk_data_ready;
    sk->sk_data_ready = my_data_ready;
    write_unlock_bh(&sk->sk_callback_lock);
}

/* Restore original when done */
void restore_socket(struct sock *sk)
{
    write_lock_bh(&sk->sk_callback_lock);
    sk->sk_data_ready = original_data_ready;
    write_unlock_bh(&sk->sk_callback_lock);
}
```

**This pattern is used by:** `net/tls/tls_sw.c`, `net/kcm/kcmsock.c`, `net/core/sock_reuseport.c`.

---

## 9. LSM (Linux Security Module) Network Hooks

**What is LSM?** LSM provides a framework of security hooks scattered throughout the kernel. SELinux, AppArmor, Smack, and TOMOYO implement these hooks to enforce mandatory access control.

Network-related LSM hooks:

```c
/* include/linux/lsm_hooks.h */

/* Called when a socket is created */
int (*socket_create)(int family, int type, int protocol, int kern);

/* Called when bind() is invoked */
int (*socket_bind)(struct socket *sock, struct sockaddr *address, int addrlen);

/* Called when connect() is invoked */
int (*socket_connect)(struct socket *sock, struct sockaddr *address, int addrlen);

/* Called when listen() is invoked */
int (*socket_listen)(struct socket *sock, int backlog);

/* Called when accept() is invoked */
int (*socket_accept)(struct socket *sock, struct socket *newsock);

/* Called when sendmsg() is invoked */
int (*socket_sendmsg)(struct socket *sock, struct msghdr *msg, int size);

/* Called when recvmsg() is invoked */
int (*socket_recvmsg)(struct socket *sock, struct msghdr *msg, int size, int flags);

/* Called when a packet is received */
int (*socket_sock_rcv_skb)(struct sock *sk, struct sk_buff *skb);

/* Called for Unix domain socket connections */
int (*unix_stream_connect)(struct socket *sock, struct socket *other, struct sock *newsk);

/* Called when setting socket options */
int (*socket_setsockopt)(struct socket *sock, int level, int optname);
```

### Writing an LSM Module

```c
/* Minimal LSM that logs all socket connections */
#include <linux/lsm_hooks.h>
#include <linux/security.h>
#include <linux/net.h>

static int my_socket_connect(struct socket *sock,
                              struct sockaddr *address,
                              int addrlen)
{
    struct sockaddr_in *sin;

    if (address->sa_family == AF_INET && addrlen >= sizeof(*sin)) {
        sin = (struct sockaddr_in *)address;
        printk(KERN_INFO "LSM: connect() to %pI4:%d\n",
               &sin->sin_addr.s_addr,
               ntohs(sin->sin_port));
    }

    return 0;  /* 0 = allow; negative errno = deny */
}

/* LSM hooks structure — only fill in hooks you want */
static struct security_hook_list my_hooks[] __lsm_ro_after_init = {
    LSM_HOOK_INIT(socket_connect, my_socket_connect),
};

/* LSM must be registered via LSM_DEFINE_EARLY_MODULE or similar.
 * Modern LSMs use the security_initcall mechanism.
 * This requires kernel config CONFIG_SECURITY and being listed
 * in CONFIG_LSM or CONFIG_DEFAULT_SECURITY_* options.
 */
static int __init my_lsm_init(void)
{
    security_add_hooks(my_hooks, ARRAY_SIZE(my_hooks), "my_lsm");
    printk(KERN_INFO "my_lsm: initialized\n");
    return 0;
}

DEFINE_LSM(my_lsm) = {
    .name = "my_lsm",
    .init = my_lsm_init,
};
```

---

## 10. Tracepoints and kprobes in Networking

### 10.1 Tracepoints

Tracepoints are **static** hooks compiled into the kernel at specific locations. They have near-zero overhead when not enabled (just a comparison and a NOP instruction).

```
Kernel source code:
  ip_rcv_finish() {
      ...
      trace_net_dev_queue(skb);   <-- tracepoint definition
      ...
  }

At runtime (when tracepoint is NOT enabled):
  NOP instruction (1 ns overhead)

At runtime (when tracepoint IS enabled):
  Calls your registered probe function
```

**Network-related tracepoints** (from `include/trace/events/net.h`):

```c
TRACE_EVENT(net_dev_xmit, ...)       /* packet transmitted */
TRACE_EVENT(net_dev_queue, ...)      /* packet queued */
TRACE_EVENT(netif_receive_skb, ...)  /* packet received */
TRACE_EVENT(netif_rx, ...)           /* netif_rx called */
TRACE_EVENT(napi_poll, ...)          /* NAPI poll */

/* TCP tracepoints (include/trace/events/tcp.h) */
TRACE_EVENT(tcp_send_reset, ...)
TRACE_EVENT(tcp_receive_reset, ...)
TRACE_EVENT(tcp_destroy_sock, ...)
TRACE_EVENT(tcp_rcv_space_adjust, ...)
TRACE_EVENT(tcp_retransmit_skb, ...)
TRACE_EVENT(tcp_retransmit_synack, ...)
TRACE_EVENT(tcp_probe, ...)
TRACE_EVENT(tcp_bad_csum, ...)

/* UDP tracepoints (include/trace/events/udp.h) */
TRACE_EVENT(udp_fail_queue_rcv_skb, ...)

/* Socket tracepoints */
TRACE_EVENT(inet_sock_set_state, ...)
```

**Using tracepoints from userspace:**

```bash
# List all network tracepoints
ls /sys/kernel/debug/tracing/events/net/
ls /sys/kernel/debug/tracing/events/tcp/

# Enable tcp_retransmit tracepoint
echo 1 > /sys/kernel/debug/tracing/events/tcp/tcp_retransmit_skb/enable
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Read trace output
cat /sys/kernel/debug/tracing/trace_pipe

# Or use perf
perf record -e tcp:tcp_retransmit_skb -a sleep 10
perf script
```

**Registering a tracepoint probe in a kernel module:**

```c
#include <linux/tracepoint.h>
#include <trace/events/net.h>

/* Must define TRACE_INCLUDE_FILE before including headers */

static void my_netif_recv_probe(void *ignore,
                                 struct sk_buff *skb)
{
    if (skb && skb->dev)
        printk(KERN_DEBUG "Tracepoint: received on %s\n",
               skb->dev->name);
}

/* Register */
register_trace_netif_receive_skb(my_netif_recv_probe, NULL);

/* Unregister */
unregister_trace_netif_receive_skb(my_netif_recv_probe, NULL);

/* Wait for all current users to finish */
tracepoint_synchronize_unregister();
```

---

### 10.2 kprobes — Dynamic Hooks at ANY Kernel Instruction

**What is a kprobe?** A kprobe lets you insert a hook at ANY kernel instruction address — even functions that have no built-in hooks. It works by replacing the instruction with a software breakpoint (INT3 on x86), causing a trap that calls your handler.

```
Normal execution:
  [instruction A] --> [instruction B] --> [instruction C]

With kprobe on instruction B:
  [instruction A] --> [INT3 trap] --> [your pre_handler runs]
                              --> [instruction B executes] --> [your post_handler runs]
                              --> [instruction C]
```

**Types:**
- **kprobe**: hook at any instruction
- **kretprobe**: hook at function RETURN (to capture return values)
- **jprobe**: hook at function ENTRY with argument access (deprecated, removed in 5.4)

```c
#include <linux/kprobes.h>
#include <linux/ip.h>

/* kprobe on ip_rcv (entry to IPv4 receive path) */
static int ip_rcv_pre_handler(struct kprobe *p, struct pt_regs *regs)
{
    /*
     * pt_regs contains CPU register values at the probe point.
     * On x86-64, function arguments are in:
     *   rdi = first arg  (struct sk_buff *skb for ip_rcv)
     *   rsi = second arg (struct net_device *dev)
     *   rdx = third arg  (struct packet_type *pt)
     *   rcx = fourth arg
     */
    struct sk_buff *skb = (struct sk_buff *)regs->di;
    struct iphdr *iph;

    if (skb && skb->data) {
        iph = (struct iphdr *)skb->data;
        printk(KERN_DEBUG "kprobe ip_rcv: src=%pI4\n", &iph->saddr);
    }

    return 0;  /* 0 = continue normally, 1 = skip original function */
}

static struct kprobe kp = {
    .symbol_name = "ip_rcv",          /* Function to probe */
    .pre_handler = ip_rcv_pre_handler, /* Called before function executes */
    .post_handler = NULL,              /* Called after function executes */
    .fault_handler = NULL,             /* Called if memory fault occurs */
};

/* Register */
register_kprobe(&kp);

/* Unregister */
unregister_kprobe(&kp);
```

**kretprobe — capture return values:**

```c
/* Probe ip_rcv's return value */
static int ip_rcv_ret_handler(struct kretprobe_instance *ri,
                               struct pt_regs *regs)
{
    /* regs_return_value() gets the return value */
    int retval = (int)regs_return_value(regs);
    printk(KERN_DEBUG "ip_rcv returned: %d\n", retval);
    return 0;
}

static struct kretprobe krp = {
    .handler     = ip_rcv_ret_handler,
    .entry_handler = NULL,  /* optional: called on function entry */
    .maxactive   = 20,      /* max simultaneous instances */
    .kp = {
        .symbol_name = "ip_rcv",
    },
};

register_kretprobe(&krp);
unregister_kretprobe(&krp);
```

---

## 11. Notification Chains — netdev_chain and inetaddr_chain

**What are Notification Chains?** A mechanism for kernel subsystems to notify interested parties when something changes. Unlike hook functions that run on every packet, notification chain callbacks run when **events** occur (interface comes up/down, IP address added/removed).

```
Event occurs (e.g., "eth0 is brought up")
    |
    v
blocking_notifier_call_chain(&netdev_chain, event, data)
    |
    v (calls all registered callbacks)
callback1(notifier_block, event, data)
callback2(notifier_block, event, data)
callback3(notifier_block, event, data)
```

### 11.1 Network Device Events

```c
/* include/linux/netdevice.h — event types */
#define NETDEV_UP         0x0001  /* interface came up */
#define NETDEV_DOWN       0x0002  /* interface went down */
#define NETDEV_REBOOT     0x0003  /* hardware crashed/reset */
#define NETDEV_CHANGE     0x0004  /* something changed (flags, etc.) */
#define NETDEV_REGISTER   0x0005  /* new interface registered */
#define NETDEV_UNREGISTER 0x0006  /* interface being removed */
#define NETDEV_CHANGEMTU  0x0007  /* MTU changed */
#define NETDEV_CHANGEADDR 0x0008  /* MAC address changed */
#define NETDEV_GOING_DOWN 0x0009  /* going down (before DOWN) */
#define NETDEV_CHANGENAME 0x000A  /* interface renamed */
#define NETDEV_FEAT_CHANGE 0x000B /* features changed (TSO, GSO, etc.) */
#define NETDEV_BONDING_FAILOVER 0x000C
#define NETDEV_PRE_UP     0x000D
#define NETDEV_PRE_TYPE_CHANGE 0x000E
#define NETDEV_POST_TYPE_CHANGE 0x000F
#define NETDEV_POST_INIT  0x0010
#define NETDEV_RELEASE    0x0011
#define NETDEV_NOTIFY_PEERS 0x0012
#define NETDEV_JOIN       0x0013
```

### 11.2 Registering a Notifier

```c
#include <linux/notifier.h>
#include <linux/netdevice.h>
#include <linux/inetdevice.h>

/*
 * Callback function.
 * event: one of NETDEV_UP, NETDEV_DOWN, etc.
 * data: pointer to struct net_device for network events.
 */
static int my_netdev_notifier_call(struct notifier_block *nb,
                                    unsigned long event,
                                    void *data)
{
    struct net_device *dev = netdev_notifier_info_to_dev(data);

    switch (event) {
    case NETDEV_UP:
        printk(KERN_INFO "Interface UP: %s\n", dev->name);
        break;
    case NETDEV_DOWN:
        printk(KERN_INFO "Interface DOWN: %s\n", dev->name);
        break;
    case NETDEV_REGISTER:
        printk(KERN_INFO "New interface: %s (ifindex=%d)\n",
               dev->name, dev->ifindex);
        break;
    case NETDEV_UNREGISTER:
        printk(KERN_INFO "Interface removed: %s\n", dev->name);
        break;
    case NETDEV_CHANGEMTU:
        printk(KERN_INFO "MTU changed on %s: new MTU=%d\n",
               dev->name, dev->mtu);
        break;
    }

    /* NOTIFY_OK = we processed the notification
     * NOTIFY_DONE = we ignored it
     * NOTIFY_BAD = error (for PRE_ events, may cancel the operation)
     * NOTIFY_STOP = stop notifying others
     */
    return NOTIFY_OK;
}

/* The notifier_block structure */
static struct notifier_block my_netdev_nb = {
    .notifier_call = my_netdev_notifier_call,
    .priority = 0,  /* 0 = default priority */
};

/* Register — called for all network devices in all namespaces */
register_netdevice_notifier(&my_netdev_nb);

/* Or namespace-specific */
register_netdevice_notifier_net(&init_net, &my_netdev_nb);

/* Unregister */
unregister_netdevice_notifier(&my_netdev_nb);
```

### 11.3 IPv4 Address Change Notifications

```c
/* Events for IP address changes */
#define NETDEV_UP         /* reuse of netdev events */
/* But use inetaddr_chain for IP-specific events */

static int my_inetaddr_notifier(struct notifier_block *nb,
                                 unsigned long event,
                                 void *ptr)
{
    struct in_ifaddr *ifa = (struct in_ifaddr *)ptr;

    switch (event) {
    case NETDEV_UP:   /* IP address added */
        printk(KERN_INFO "IP added: %pI4 on %s\n",
               &ifa->ifa_local, ifa->ifa_dev->dev->name);
        break;
    case NETDEV_DOWN: /* IP address removed */
        printk(KERN_INFO "IP removed: %pI4 on %s\n",
               &ifa->ifa_local, ifa->ifa_dev->dev->name);
        break;
    }

    return NOTIFY_OK;
}

static struct notifier_block my_inetaddr_nb = {
    .notifier_call = my_inetaddr_notifier,
};

register_inetaddr_notifier(&my_inetaddr_nb);
unregister_inetaddr_notifier(&my_inetaddr_nb);
```

---

## 12. Routing Hooks — FIB Rules and Custom Routes

### 12.1 The FIB (Forwarding Information Base)

The FIB is the kernel's routing table. When a packet arrives, `ip_route_input()` consults the FIB to decide where to send it.

```
Packet arrives
    |
    v
ip_rcv_finish()
    |
    v
ip_route_input_noref()
    |
    v
fib_lookup() --- looks up routing table
    |
    v (result stored in skb->_skb_refdst)
RTN_LOCAL    --> deliver to local socket
RTN_UNICAST  --> forward to next-hop
RTN_BROADCAST --> deliver to all
RTN_MULTICAST --> multicast handling
RTN_UNREACHABLE --> send ICMP unreachable
```

### 12.2 FIB Rules — Policy Routing Hooks

FIB rules are evaluated BEFORE the main routing tables. They allow policy-based routing (e.g., "use a different routing table for packets from 192.168.1.0/24"):

```c
/* Register a FIB rule hook */
struct fib_rules_ops {
    int         family;
    struct list_head list;
    int         rule_size;
    int         addr_size;
    int         unresolved_rules;
    int         nr_goto_rules;

    /* Hook functions */
    int  (*action)(struct fib_rule *rule, struct flowi *fl, int flags,
                   struct fib_lookup_arg *arg);
    bool (*suppress)(struct fib_rule *rule, int suppress_ifgroup,
                     struct fib_lookup_arg *arg);
    int  (*match)(struct fib_rule *rule, struct flowi *fl, int flags);
    int  (*configure)(struct fib_rule *rule, struct sk_buff *skb,
                      struct fib_rule_hdr *frh, struct nlattr **tb,
                      struct netlink_ext_ack *extack);
    int  (*delete)(struct fib_rule *rule);
    int  (*compare)(struct fib_rule *rule, struct fib_rule_hdr *frh,
                    struct nlattr **tb);
    int  (*fill)(struct fib_rule *rule, struct sk_buff *skb,
                 struct fib_rule_hdr *frh);
    /* ... */
};
```

### 12.3 Custom Route Lookup with fib_notifier

```c
/* Get notified when routing table changes */
#include <net/fib_notifier.h>

static int my_fib_notifier(struct notifier_block *nb,
                            unsigned long event,
                            void *ptr)
{
    struct fib_notifier_info *info = ptr;

    switch (event) {
    case FIB_EVENT_ENTRY_REPLACE: /* Route added/replaced */
        printk(KERN_INFO "FIB: route added in table %u\n", info->tb_id);
        break;
    case FIB_EVENT_ENTRY_DEL:    /* Route deleted */
        printk(KERN_INFO "FIB: route deleted\n");
        break;
    case FIB_EVENT_RULE_ADD:     /* Routing rule added */
    case FIB_EVENT_RULE_DEL:     /* Routing rule deleted */
        break;
    }

    return NOTIFY_OK;
}

static struct notifier_block my_fib_nb = {
    .notifier_call = my_fib_notifier,
};

register_fib_notifier(&init_net, &my_fib_nb, NULL, NULL);
unregister_fib_notifier(&init_net, &my_fib_nb);
```

---

## 13. The sk_buff Lifecycle Through All Hooks

This is the **complete journey of a single TCP packet** from NIC to application, with every hook point marked:

```
=============================================================================
                     COMPLETE PACKET RX LIFECYCLE
=============================================================================

[1] NIC DMA: Packet copied to kernel ring buffer via DMA
        |
        v
[2] NAPI poll(): driver's poll() called
    HOOK: net_device_ops.ndo_start_poll (driver-defined)
        |
        v
[3] sk_buff allocated: netdev_alloc_skb()
    Memory layout: [headroom | ethernet | IP | TCP | data | tailroom]
        |
        v
[4] XDP hook (if program attached):
    HOOK: bpf_prog attached to device via XDP
    VERDICT: XDP_PASS / XDP_DROP / XDP_TX / XDP_REDIRECT
        |  (if XDP_PASS)
        v
[5] netif_receive_skb() called
    GRO (Generic Receive Offload) may merge packets here
        |
        v
[6] TC ingress BPF (if attached):
    HOOK: tc filter with cls_bpf attached to clsact qdisc ingress
    VERDICT: TC_ACT_OK / TC_ACT_SHOT / TC_ACT_REDIRECT
        |  (if TC_ACT_OK)
        v
[7] ptype_base dispatch: packet_type.func() called
    For ETH_P_IP: ip_rcv() is called
        |
        v
[8] Netfilter PRE_ROUTING:
    HOOK: NF_INET_PRE_ROUTING
    Conntrack begins tracking connection here
    DNAT (port forwarding) happens here
    VERDICT: NF_ACCEPT / NF_DROP / NF_QUEUE / NF_STOLEN
        |  (if NF_ACCEPT)
        v
[9] ip_rcv_finish(): routing decision
    fib_lookup() → determines: LOCAL, FORWARD, or DROP
        |
    ----+---------------------
    |                        |
    v (RTN_LOCAL)            v (RTN_UNICAST = forward)
    |                        |
[10a] Netfilter LOCAL_IN:    [10b] Netfilter FORWARD:
    HOOK: NF_INET_LOCAL_IN       HOOK: NF_INET_FORWARD
        |                            |
        v                            v
[11a] ip_local_deliver():       [11b] ip_forward():
    inet_protos[] dispatch           decrement TTL
    TCP: tcp_v4_rcv()                send to NF_POST_ROUTING
    UDP: udp_rcv()
        |
        v
[12] Socket lookup:
    __inet_lookup() finds matching socket
        |
        v
[13] LSM socket_sock_rcv_skb hook:
    HOOK: security_sock_rcv_skb()
        |
        v
[14] Socket BPF filter (if attached):
    HOOK: sk_filter()
        |
        v
[15] sk_receive_queue: skb enqueued
    sk->sk_data_ready() called
    HOOK: sk->sk_data_ready (replaceable callback)
        |
        v
[16] Application: read() / recv() / recvmsg()
    Copies data from sk_receive_queue to userspace buffer

=============================================================================
                     COMPLETE PACKET TX LIFECYCLE
=============================================================================

[1] Application: write() / send() / sendmsg()
        |
        v
[2] sys_sendmsg() → sock->ops->sendmsg() (proto_ops hook)
        |
        v
[3] Protocol sendmsg: tcp_sendmsg() or udp_sendmsg()
    sk_buff allocated and filled with payload
        |
        v
[4] IP layer: ip_queue_xmit() or ip_send_skb()
        |
        v
[5] Netfilter LOCAL_OUT:
    HOOK: NF_INET_LOCAL_OUT
        |
        v
[6] Routing: ip_route_output()
        |
        v
[7] Netfilter POST_ROUTING:
    HOOK: NF_INET_POST_ROUTING
    SNAT/Masquerade happens here
        |
        v
[8] dev_queue_xmit()
        |
        v
[9] Queueing discipline (qdisc): pfifo, fq, htb, etc.
        |
        v
[10] TC egress BPF (if attached):
    HOOK: tc filter on clsact qdisc egress
        |
        v
[11] net_device_ops.ndo_start_xmit() (driver hook)
        |
        v
[12] DMA to NIC hardware
```

---

## 14. Complete C Module Examples

### 14.1 Packet Logger Module — Multiple Hooks

```c
/* File: netlog.c — logs all packets with hook point info */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/icmp.h>
#include <linux/skbuff.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("example");
MODULE_DESCRIPTION("Log all packets at multiple hook points");
MODULE_VERSION("1.0");

/* Atomic counter to avoid logging too many packets */
static atomic_t pkt_count = ATOMIC_INIT(0);
#define MAX_PKTS_PER_SEC 100

/*
 * Generic hook function used for all hook points.
 * Uses priv to identify which hook is running.
 */
static unsigned int generic_hook(void *priv,
                                  struct sk_buff *skb,
                                  const struct nf_hook_state *state)
{
    const char *hook_name = (const char *)priv;
    struct iphdr *iph;
    const char *proto_str = "???";

    if (!skb)
        return NF_ACCEPT;

    /* Rate limiting: only log first MAX_PKTS_PER_SEC per reset */
    if (atomic_inc_return(&pkt_count) > MAX_PKTS_PER_SEC)
        return NF_ACCEPT;

    iph = ip_hdr(skb);

    /* Determine protocol string */
    switch (iph->protocol) {
    case IPPROTO_TCP:  proto_str = "TCP";  break;
    case IPPROTO_UDP:  proto_str = "UDP";  break;
    case IPPROTO_ICMP: proto_str = "ICMP"; break;
    }

    printk(KERN_INFO "[%s] %s: %pI4 -> %pI4 ttl=%d len=%d dev=%s\n",
           hook_name,
           proto_str,
           &iph->saddr,
           &iph->daddr,
           iph->ttl,
           ntohs(iph->tot_len),
           state->in  ? state->in->name :
           (state->out ? state->out->name : "?"));

    return NF_ACCEPT;
}

/* Define all 5 hooks */
static struct nf_hook_ops netlog_hooks[] = {
    {
        .hook     = generic_hook,
        .priv     = "PRE_ROUTING",
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_PRE_ROUTING,
        .priority = NF_IP_PRI_FIRST + 1,
    },
    {
        .hook     = generic_hook,
        .priv     = "LOCAL_IN",
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_LOCAL_IN,
        .priority = NF_IP_PRI_FIRST + 1,
    },
    {
        .hook     = generic_hook,
        .priv     = "FORWARD",
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_FORWARD,
        .priority = NF_IP_PRI_FIRST + 1,
    },
    {
        .hook     = generic_hook,
        .priv     = "LOCAL_OUT",
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_LOCAL_OUT,
        .priority = NF_IP_PRI_FIRST + 1,
    },
    {
        .hook     = generic_hook,
        .priv     = "POST_ROUTING",
        .pf       = NFPROTO_IPV4,
        .hooknum  = NF_INET_POST_ROUTING,
        .priority = NF_IP_PRI_FIRST + 1,
    },
};

/* Timer to reset rate limit counter */
static struct timer_list rate_timer;

static void rate_timer_cb(struct timer_list *t)
{
    atomic_set(&pkt_count, 0);
    mod_timer(&rate_timer, jiffies + HZ);  /* Reset every second */
}

static int __init netlog_init(void)
{
    int ret;

    /* Register all 5 hooks at once */
    ret = nf_register_net_hooks(&init_net,
                                 netlog_hooks,
                                 ARRAY_SIZE(netlog_hooks));
    if (ret < 0) {
        printk(KERN_ERR "netlog: Failed to register hooks\n");
        return ret;
    }

    /* Set up rate limiting timer */
    timer_setup(&rate_timer, rate_timer_cb, 0);
    mod_timer(&rate_timer, jiffies + HZ);

    printk(KERN_INFO "netlog: All 5 IPv4 hook points registered\n");
    return 0;
}

static void __exit netlog_exit(void)
{
    del_timer_sync(&rate_timer);
    nf_unregister_net_hooks(&init_net,
                             netlog_hooks,
                             ARRAY_SIZE(netlog_hooks));
    printk(KERN_INFO "netlog: Hooks unregistered\n");
}

module_init(netlog_init);
module_exit(netlog_exit);
```

---

### 14.2 Port Knocking Module using Netfilter

Port knocking: a sequence of packets to "closed" ports opens a firewall hole.

```c
/* File: port_knock.c — Simple port knocking firewall */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/hashtable.h>
#include <linux/timer.h>
#include <linux/spinlock.h>

MODULE_LICENSE("GPL");

/* Knock sequence: 1234, 5678, 9012 */
static const __u16 knock_seq[] = { 1234, 5678, 9012 };
#define KNOCK_LEN ARRAY_SIZE(knock_seq)
#define OPEN_PORT 22     /* Unblock SSH after correct knock */
#define KNOCK_TIMEOUT (5 * HZ) /* 5 seconds to complete sequence */

/*
 * Track knock state per source IP.
 * In production you'd use a proper LRU cache with timestamps.
 */
struct knock_state {
    __be32          src_ip;         /* Source IP */
    int             knock_pos;      /* Current position in sequence */
    unsigned long   last_knock;     /* Timestamp of last knock */
    int             unlocked;       /* 1 if access is granted */
    struct hlist_node hnode;
};

/* Hash table: key=src_ip, value=knock_state */
static DEFINE_HASHTABLE(knock_table, 8);  /* 2^8 = 256 buckets */
static DEFINE_SPINLOCK(knock_lock);

static struct knock_state *find_or_create_state(__be32 src_ip)
{
    struct knock_state *ks;

    /* Search existing */
    hash_for_each_possible(knock_table, ks, hnode, src_ip) {
        if (ks->src_ip == src_ip)
            return ks;
    }

    /* Create new */
    ks = kmalloc(sizeof(*ks), GFP_ATOMIC);
    if (!ks)
        return NULL;

    ks->src_ip     = src_ip;
    ks->knock_pos  = 0;
    ks->last_knock = jiffies;
    ks->unlocked   = 0;

    hash_add(knock_table, &ks->hnode, src_ip);
    return ks;
}

static unsigned int knock_hook(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr  *iph;
    struct tcphdr *tcph;
    struct knock_state *ks;
    __u16 dport;
    unsigned long flags;
    int result = NF_ACCEPT;

    if (!skb)
        return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;

    /* Get TCP header: IP header length is iph->ihl * 4 bytes */
    tcph = (struct tcphdr *)((u8 *)iph + iph->ihl * 4);
    dport = ntohs(tcph->dest);

    spin_lock_irqsave(&knock_lock, flags);

    ks = find_or_create_state(iph->saddr);
    if (!ks) {
        spin_unlock_irqrestore(&knock_lock, flags);
        return NF_DROP;  /* OOM — fail closed */
    }

    /* Reset if timeout expired */
    if (time_after(jiffies, ks->last_knock + KNOCK_TIMEOUT)) {
        ks->knock_pos = 0;
        ks->unlocked  = 0;
    }

    /* If already unlocked and packet is for OPEN_PORT: allow */
    if (ks->unlocked && dport == OPEN_PORT) {
        spin_unlock_irqrestore(&knock_lock, flags);
        return NF_ACCEPT;
    }

    /* Check if this matches the next knock in sequence */
    if (dport == knock_seq[ks->knock_pos]) {
        ks->knock_pos++;
        ks->last_knock = jiffies;

        if (ks->knock_pos >= KNOCK_LEN) {
            /* Sequence complete! */
            ks->unlocked = 1;
            ks->knock_pos = 0;
            printk(KERN_INFO "port_knock: %pI4 unlocked port %d!\n",
                   &iph->saddr, OPEN_PORT);
        }
        result = NF_DROP;  /* Drop the knock packet itself */
    } else if (dport == OPEN_PORT && !ks->unlocked) {
        result = NF_DROP;  /* Access not yet unlocked */
    }

    spin_unlock_irqrestore(&knock_lock, flags);
    return result;
}

static struct nf_hook_ops knock_ops = {
    .hook     = knock_hook,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_LOCAL_IN,
    .priority = NF_IP_PRI_FILTER - 1,  /* Run just before iptables filter */
};

static int __init port_knock_init(void)
{
    hash_init(knock_table);
    nf_register_net_hook(&init_net, &knock_ops);
    printk(KERN_INFO "port_knock: Loaded. Sequence: 1234->5678->9012 opens port 22\n");
    return 0;
}

static void __exit port_knock_exit(void)
{
    struct knock_state *ks;
    struct hlist_node *tmp;
    int bkt;

    nf_unregister_net_hook(&init_net, &knock_ops);

    /* Free all hash table entries */
    hash_for_each_safe(knock_table, bkt, tmp, ks, hnode) {
        hash_del(&ks->hnode);
        kfree(ks);
    }
    printk(KERN_INFO "port_knock: Unloaded\n");
}

module_init(port_knock_init);
module_exit(port_knock_exit);
```

---

## 15. Rust in the Linux Kernel — Network Hooks

### 15.1 Background: Rust for Linux

Since Linux 6.1, Rust is officially supported as a second implementation language in the Linux kernel. The `rust/` directory contains abstractions over kernel APIs.

**Key principle:** Rust abstractions are THIN wrappers around C kernel APIs. They provide:
- Memory safety (no use-after-free, no null pointer dereference)
- Thread safety (the borrow checker enforces lock discipline)
- Zero-cost abstractions (same performance as C)

### 15.2 Current State of Rust Network Abstractions

As of Linux 6.x, the following network abstractions exist in `rust/kernel/net/`:

```
rust/kernel/
├── net.rs              # Core networking types
├── net/
│   ├── filter.rs       # Socket filter (BPF) bindings
│   └── ...
```

**Available types:**

```rust
// From rust/kernel/net.rs
pub struct Namespace(Opaque<bindings::net>);       // struct net
pub struct Device(Opaque<bindings::net_device>);   // struct net_device  
pub struct SkBuff(Opaque<bindings::sk_buff>);      // struct sk_buff
pub struct TcpListener(...);                       // TCP listener
pub struct TcpStream(...);                         // TCP stream
```

### 15.3 Writing a Netfilter Hook in Rust

Currently, direct Netfilter hook registration from Rust requires using `unsafe` bindings because the abstraction layer is not yet complete. Here is how it works:

```rust
// File: rust_netfilter_hook/src/lib.rs

#![no_std]
#![feature(allocator_api, global_asm)]

use kernel::prelude::*;
use kernel::bindings;
use core::ffi::c_void;

module! {
    type: RustNetfilterHook,
    name: "rust_netfilter_hook",
    author: "example",
    description: "Netfilter hook written in Rust",
    license: "GPL",
}

/// Our module state — holds the registered hook ops.
/// This struct is stored in the kernel's module data.
struct RustNetfilterHook {
    // We store the hook_ops here so it lives as long as the module.
    // The C nf_hook_ops struct must be pinned in memory —
    // its address is stored in the kernel and must not change.
    _hook_ops: Pin<Box<bindings::nf_hook_ops>>,
}

/// The hook function called by the Netfilter framework.
/// This uses `unsafe` because we're crossing the C/Rust boundary.
/// The C kernel calls this function directly.
unsafe extern "C" fn hook_fn(
    priv_: *mut c_void,
    skb: *mut bindings::sk_buff,
    state: *const bindings::nf_hook_state,
) -> core::ffi::c_uint {
    // Safety: The kernel guarantees skb and state are valid pointers
    // when this function is called.
    if skb.is_null() {
        // NF_ACCEPT = 1
        return bindings::NF_ACCEPT;
    }

    // Access the IP header.
    // In C: ip_hdr(skb) = skb->head + skb->network_header
    // In Rust with raw bindings:
    let skb_ref = &*skb;

    // Get the network header pointer safely.
    // skb->network_header is a u16 offset from skb->head.
    let ip_hdr_ptr = skb_ref.head.add(skb_ref.network_header as usize)
        as *const bindings::iphdr;

    if ip_hdr_ptr.is_null() {
        return bindings::NF_ACCEPT;
    }

    let iph = &*ip_hdr_ptr;

    // Check if it's TCP (protocol 6)
    if iph.protocol == bindings::IPPROTO_TCP as u8 {
        // pr_info! is a Rust wrapper for printk(KERN_INFO ...)
        pr_info!("Rust hook: TCP packet, protocol={}\n", iph.protocol);
    }

    bindings::NF_ACCEPT
}

impl kernel::Module for RustNetfilterHook {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("Rust Netfilter hook: initializing\n");

        // Allocate and initialize nf_hook_ops.
        // We use Box::pin to ensure the address is stable (pinned).
        let mut hook_ops = Box::pin(bindings::nf_hook_ops {
            hook:     Some(hook_fn),
            dev:      core::ptr::null_mut(),
            priv_:    core::ptr::null_mut(),
            pf:       bindings::NFPROTO_IPV4 as u8,
            hooknum:  bindings::NF_INET_PRE_ROUTING,
            priority: bindings::NF_IP_PRI_FIRST as i32 + 1,
            list:     bindings::list_head {
                next: core::ptr::null_mut(),
                prev: core::ptr::null_mut(),
            },
        });

        // Register the hook.
        // Safety: init_net is a valid global, hook_ops is properly initialized.
        let ret = unsafe {
            bindings::nf_register_net_hook(
                &mut bindings::init_net,
                hook_ops.as_mut().get_unchecked_mut(),
            )
        };

        if ret < 0 {
            pr_err!("Rust hook: registration failed with {}\n", ret);
            return Err(Error::from_kernel_errno(ret));
        }

        pr_info!("Rust Netfilter hook: registered at PRE_ROUTING\n");
        Ok(Self { _hook_ops: hook_ops })
    }
}

impl Drop for RustNetfilterHook {
    fn drop(&mut self) {
        pr_info!("Rust Netfilter hook: unregistering\n");
        unsafe {
            bindings::nf_unregister_net_hook(
                &mut bindings::init_net,
                self._hook_ops.as_mut().get_unchecked_mut(),
            );
        }
    }
}
```

**Kconfig entry** (required for Rust modules):

```kconfig
# Kconfig
config RUST_NETFILTER_HOOK
    tristate "Rust Netfilter hook example"
    depends on RUST && NETFILTER
    help
      Example Netfilter hook written in Rust.
```

**Makefile (Kbuild)**:

```makefile
# Makefile
obj-$(CONFIG_RUST_NETFILTER_HOOK) += rust_netfilter_hook.o
```

---

### 15.4 Writing XDP Programs and Loading from Rust Userspace

While Rust kernel modules for XDP are evolving, you can write a complete XDP loader in Rust userspace using the `aya` library:

**aya** is a pure-Rust eBPF library that replaces libbpf:

```toml
# Cargo.toml for the userspace loader
[package]
name = "xdp_loader"
version = "0.1.0"
edition = "2021"

[dependencies]
aya = "0.12"
aya-log = "0.2"
anyhow = "1"
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

```rust
// src/main.rs — userspace XDP loader using aya
use aya::{
    include_bytes_aligned,
    programs::{Xdp, XdpFlags},
    Bpf,
};
use anyhow::Context;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load the compiled eBPF object file.
    // include_bytes_aligned! embeds the .o file at compile time.
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/xdp_drop_icmp"
    ))?;

    // Get the XDP program from the object.
    // "xdp_drop_icmp" matches the function name in the eBPF C program.
    let program: &mut Xdp = bpf
        .program_mut("xdp_drop_icmp")
        .unwrap()
        .try_into()?;

    // Load the program into the kernel (verifier runs here).
    program.load()?;

    // Attach to network interface "eth0".
    // XdpFlags::default() = SKB mode (works with any driver).
    // XdpFlags::DRV_MODE = native driver mode (faster).
    program
        .attach("eth0", XdpFlags::default())
        .context("failed to attach XDP program")?;

    println!("XDP program loaded and attached to eth0. Press Ctrl+C to stop.");

    // Keep running
    tokio::signal::ctrl_c().await?;
    println!("Detaching XDP program...");
    // XDP is automatically detached when `program` is dropped.

    Ok(())
}
```

**Writing the eBPF program in Rust using aya-bpf:**

```rust
// src/bpf/xdp_drop_icmp.rs — eBPF program in Rust!
#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::xdp,
    programs::XdpContext,
};
use aya_log_ebpf::info;
use network_types::{
    eth::{EthHdr, EtherType},
    ip::{IpProto, Ipv4Hdr},
};

/// Helper: safely get a pointer to T at offset `offset` in the XDP context.
/// Returns None if the pointer would be out of bounds.
#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Option<*const T> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = core::mem::size_of::<T>();

    // Bounds check: required by the verifier
    if start + offset + len > end {
        return None;
    }
    Some((start + offset) as *const T)
}

/// XDP program entry point.
/// The #[xdp] macro generates the correct ELF section name.
#[xdp]
pub fn xdp_drop_icmp(ctx: XdpContext) -> u32 {
    match inner_xdp_drop_icmp(ctx) {
        Ok(action) => action,
        Err(_)     => xdp_action::XDP_PASS,
    }
}

fn inner_xdp_drop_icmp(ctx: XdpContext) -> Result<u32, ()> {
    // Parse Ethernet header
    let eth_hdr = ptr_at::<EthHdr>(&ctx, 0).ok_or(())?;
    // Safety: bounds check done by ptr_at
    let eth = unsafe { &*eth_hdr };

    // Only process IPv4
    if eth.ether_type != EtherType::Ipv4 {
        return Ok(xdp_action::XDP_PASS);
    }

    // Parse IPv4 header (after Ethernet header)
    let ip_hdr = ptr_at::<Ipv4Hdr>(&ctx, EthHdr::LEN).ok_or(())?;
    let ip = unsafe { &*ip_hdr };

    // Drop ICMP
    if ip.proto == IpProto::Icmp {
        info!(&ctx, "Dropping ICMP from {:i}", u32::from_be(ip.src_addr));
        return Ok(xdp_action::XDP_DROP);
    }

    Ok(xdp_action::XDP_PASS)
}

/// Panic handler required for no_std
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
```

---

### 15.5 Using aya for TC BPF from Rust

```rust
// TC filter attachment with aya
use aya::{
    programs::{tc, SchedClassifier, TcAttachType},
    Bpf,
};

let mut bpf = Bpf::load_file("tc_mark.o")?;

// Add clsact qdisc to eth0 (needed for TC BPF)
tc::qdisc_add_clsact("eth0")?;

let program: &mut SchedClassifier = bpf
    .program_mut("tc_mark_packets")
    .unwrap()
    .try_into()?;

program.load()?;

// Attach to ingress
program.attach("eth0", TcAttachType::Ingress)?;

// Attach to egress
program.attach("eth0", TcAttachType::Egress)?;
```

---

### 15.6 eBPF Maps from Rust — Sharing State Between Kernel and Userspace

eBPF maps are key-value stores shared between the eBPF program (kernel) and userspace:

```rust
// eBPF side (in bpf program):
use aya_bpf::{
    macros::map,
    maps::HashMap,
};

// Declare a map: IP -> packet count
#[map]
static mut PACKET_COUNT: HashMap<u32, u64> = HashMap::with_max_entries(1024, 0);

// In the XDP program, increment counter:
unsafe {
    let src_ip = u32::from_be(ip.src_addr);
    let count = PACKET_COUNT.get(&src_ip).copied().unwrap_or(0);
    PACKET_COUNT.insert(&src_ip, &(count + 1), 0).ok();
}
```

```rust
// Userspace side (Rust with aya):
use aya::maps::HashMap;

let packet_count: HashMap<_, u32, u64> =
    HashMap::try_from(bpf.map("PACKET_COUNT").unwrap())?;

// Read packet counts
for result in packet_count.iter() {
    let (ip, count) = result?;
    let ip_str = std::net::Ipv4Addr::from(ip);
    println!("{}: {} packets", ip_str, count);
}
```

---

## 16. Comparison Table: Which Hook for Which Job?

```
+--------------------+----------+-----------+-----------+------------------------+
| Hook               | Position | Overhead  | Modifiable| Use Case               |
+--------------------+----------+-----------+-----------+------------------------+
| XDP (native)       | Before   | Lowest    | Yes       | DDoS mitigation,       |
|                    | sk_buff  | (~100ns)  |           | load balancing         |
+--------------------+----------+-----------+-----------+------------------------+
| XDP (generic)      | After    | Low       | Yes       | Any driver, testing    |
|                    | sk_buff  |           |           |                        |
+--------------------+----------+-----------+-----------+------------------------+
| TC BPF (ingress)   | After    | Low       | Yes       | Traffic shaping,       |
|                    | sk_buff  | (~200ns)  |           | marking, redirect      |
+--------------------+----------+-----------+-----------+------------------------+
| NF PRE_ROUTING     | Before   | Medium    | Yes       | DNAT, early firewall   |
|                    | routing  | (~500ns)  |           |                        |
+--------------------+----------+-----------+-----------+------------------------+
| NF LOCAL_IN        | After    | Medium    | Yes       | INPUT firewall,        |
|                    | routing  |           |           | rate limiting          |
+--------------------+----------+-----------+-----------+------------------------+
| NF FORWARD         | Forwarded| Medium    | Yes       | Router firewall        |
|                    | packets  |           |           |                        |
+--------------------+----------+-----------+-----------+------------------------+
| NF LOCAL_OUT       | Before   | Medium    | Yes       | OUTPUT firewall,       |
|                    | routing  |           |           | redirect local pkts    |
+--------------------+----------+-----------+-----------+------------------------+
| NF POST_ROUTING    | After    | Medium    | Yes       | SNAT, masquerade       |
|                    | routing  |           |           |                        |
+--------------------+----------+-----------+-----------+------------------------+
| TC BPF (egress)    | Before   | Low       | Yes       | Egress traffic ctrl    |
|                    | TX       | (~200ns)  |           |                        |
+--------------------+----------+-----------+-----------+------------------------+
| Socket BPF filter  | Socket   | Low       | No        | Per-socket filtering   |
|                    | level    |           | (drop only)| (like tcpdump)        |
+--------------------+----------+-----------+-----------+------------------------+
| cgroup BPF         | Per-     | Low       | Yes       | Container networking,  |
|                    | cgroup   |           |           | per-app firewall       |
+--------------------+----------+-----------+-----------+------------------------+
| NAPI poll          | Driver   | None      | Yes       | Custom driver behavior |
|                    | level    | (mandatory)|           |                       |
+--------------------+----------+-----------+-----------+------------------------+
| packet_type.func   | L2/L3    | Low       | Gets clone| Protocol sniffing      |
|                    | boundary |           |           | (AF_PACKET)            |
+--------------------+----------+-----------+-----------+------------------------+
| sk_data_ready      | Socket   | Minimal   | Yes       | In-kernel proxy,       |
|                    | callback |           |           | TLS offload            |
+--------------------+----------+-----------+-----------+------------------------+
| Tracepoint         | Anywhere | Near-zero | No        | Observability, tracing |
|                    | static   | when off  | (read only)|                      |
+--------------------+----------+-----------+-----------+------------------------+
| kprobe             | Anywhere | Higher    | Via regs  | Dynamic tracing,       |
|                    | dynamic  | (~1µs)    |           | debugging              |
+--------------------+----------+-----------+-----------+------------------------+
| LSM hooks          | Syscall  | Low       | Allow/deny| Security policy        |
|                    | level    |           | only      |                        |
+--------------------+----------+-----------+-----------+------------------------+
| Notifier chain     | Events   | Near-zero | State only| Interface monitoring   |
|                    | only     | (async)   |           | (up/down events)       |
+--------------------+----------+-----------+-----------+------------------------+
```

---

## 17. Performance Characteristics

### Throughput Benchmarks (approximate, vary by hardware)

```
Hook Type         | Throughput   | Latency   | Notes
------------------|--------------|-----------|---------------------------
XDP (native)      | 25-100 Mpps  | 30-100ns  | Before sk_buff, zero copy
XDP (generic)     | 5-10 Mpps    | 100-200ns | After sk_buff
TC BPF            | 5-10 Mpps    | 100-300ns | Full sk_buff access
Netfilter         | 1-5 Mpps     | 300-800ns | Full stack
iptables (Netfilter) | 1-3 Mpps  | 500ns-1µs | iptables overhead on top
nftables (Netfilter) | 2-4 Mpps  | 400-700ns | Better than iptables
```

### Why XDP is the Fastest

```
Regular path:
  NIC → DMA → sk_buff alloc (malloc) → L2/L3 headers parsed →
  conntrack lookup → Netfilter → routing → socket → user space
  [~20-50 function calls, multiple memory allocations]

XDP path:
  NIC → DMA → XDP program runs → verdict → (drop = done!)
  [~3-5 function calls, ZERO memory allocations]
```

### Locking Considerations

Every hook runs in one of these contexts:

```
Context          | Can sleep? | Can alloc? | Lock type needed
-----------------|------------|------------|------------------
Hardirq          | NO         | NO         | spin_lock_irqsave
Softirq (NAPI)   | NO         | GFP_ATOMIC | spin_lock_bh
Process          | YES        | GFP_KERNEL | mutex or spin_lock
XDP              | NO         | NO         | per-cpu (lockless!)
```

**Rule:** In Netfilter hooks (which run in softirq context), ALWAYS use `GFP_ATOMIC` for memory allocation, never `GFP_KERNEL`.

```c
/* Wrong — GFP_KERNEL can sleep, softirq context cannot */
void *buf = kmalloc(size, GFP_KERNEL);  /* BUG! */

/* Correct */
void *buf = kmalloc(size, GFP_ATOMIC);  /* OK: won't sleep */
```

---

## 18. Common Pitfalls and Debugging

### 18.1 Top 10 Mistakes

**1. Forgetting to free sk_buff after NF_STOLEN:**
```c
/* Wrong */
return NF_STOLEN;  /* You own skb now but forgot to free it → memory leak */

/* Correct */
kfree_skb(skb);    /* or consume_skb(skb) */
return NF_STOLEN;
```

**2. Not unregistering hooks in module exit:**
```c
/* Wrong — crash on rmmod if a packet is in the hook */
static void __exit bad_exit(void) {
    /* forgot nf_unregister_net_hook() */
}

/* Correct */
static void __exit good_exit(void) {
    nf_unregister_net_hook(&init_net, &my_hook);
    /* nf_unregister blocks until all in-flight calls complete */
}
```

**3. Modifying sk_buff without making it writable:**
```c
/* Wrong — may corrupt shared packet data */
struct iphdr *iph = ip_hdr(skb);
iph->ttl = 64;  /* BUG if skb is cloned/shared */

/* Correct */
if (!skb_make_writable(skb, sizeof(struct iphdr)))
    return NF_DROP;
iph = ip_hdr(skb);  /* Re-fetch after skb_make_writable! */
iph->ttl = 64;
ip_send_check(iph);
```

**4. Not recalculating checksums after header modification:**
```c
/* After modifying IP header */
ip_send_check(iph);

/* After modifying TCP header */
/* TCP checksum covers the IP pseudo-header too */
skb->ip_summed = CHECKSUM_NONE;  /* Force hardware/software recalc */
```

**5. Wrong memory allocation flags in softirq context:**
```c
/* Wrong in hook function */
buf = kmalloc(size, GFP_KERNEL);  /* may sleep → BUG in softirq */

/* Correct */
buf = kmalloc(size, GFP_ATOMIC);  /* never sleeps */
```

**6. Race condition in socket callback replacement:**
```c
/* Wrong — no lock */
sk->sk_data_ready = my_handler;

/* Correct */
write_lock_bh(&sk->sk_callback_lock);
sk->sk_data_ready = my_handler;
write_unlock_bh(&sk->sk_callback_lock);
```

**7. Not checking skb->len before accessing headers:**
```c
/* Wrong — packet may be too short */
struct tcphdr *tcph = tcp_hdr(skb);

/* Correct */
if (skb->len < sizeof(struct iphdr) + sizeof(struct tcphdr))
    return NF_DROP;
```

**8. kprobe on inlined function:**
Heavily optimized functions may be inlined by the compiler and not have a standalone symbol. kprobe will fail to find the address.
```c
/* Check if symbol exists before registering */
if (!kallsyms_lookup_name("target_function"))
    return -EINVAL;
```

**9. Registering hook at wrong priority (interferes with conntrack):**
```c
/* If you need connection tracking info, run AFTER conntrack */
.priority = NF_IP_PRI_CONNTRACK + 1,  /* after -200 */

/* If you want to block before conntrack tracks it */
.priority = NF_IP_PRI_CONNTRACK - 1,  /* before -200 */
```

**10. eBPF bounds check failure — packet truncated:**
```c
/* Always check BEFORE accessing packet data */
if ((void *)(iph + 1) > data_end)
    return XDP_PASS;  /* Never XDP_DROP for truncated packets you can't parse */
```

---

### 18.2 Debugging Tools

**View registered Netfilter hooks:**
```bash
# See all registered hooks (Linux 4.x+)
cat /proc/net/ip_tables_matches
cat /proc/net/ip_tables_targets

# nft (nftables) shows hooks too
nft list ruleset

# For debug builds with CONFIG_NF_CONNTRACK_CHAIN_EVENTS:
cat /sys/kernel/debug/nf_hooks
```

**eBPF program inspection:**
```bash
# List loaded eBPF programs
bpftool prog list

# Show a specific program's bytecode
bpftool prog dump xlated id <ID>

# Show JIT-compiled code
bpftool prog dump jited id <ID>

# Show all eBPF maps
bpftool map list

# Dump map contents
bpftool map dump id <MAP_ID>

# Trace output from bpf_printk
cat /sys/kernel/debug/tracing/trace_pipe
```

**kprobe debugging:**
```bash
# List all kprobes
cat /sys/kernel/debug/kprobes/list

# Enable/disable kprobes globally
echo 0 > /sys/kernel/debug/kprobes/enabled
echo 1 > /sys/kernel/debug/kprobes/enabled

# Dynamic kprobes via tracefs
echo 'p:my_probe ip_rcv' > /sys/kernel/debug/tracing/kprobe_events
echo 1 > /sys/kernel/debug/tracing/events/kprobes/my_probe/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

**Packet tracing with ftrace:**
```bash
# Trace the entire packet receive path
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo ip_rcv > /sys/kernel/debug/tracing/set_graph_function
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace_pipe
```

**dmesg and printk levels:**
```bash
# See all kernel messages
dmesg -w

# Set printk level to show DEBUG messages
echo 8 > /proc/sys/kernel/printk

# Or: echo "module_name +p" > /sys/kernel/debug/dynamic_debug/control
echo "file nf_drop_8080.c +p" > /sys/kernel/debug/dynamic_debug/control
```

---

### 18.3 Testing Your Hook Module

```bash
# Build
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules

# Load
sudo insmod my_module.ko

# Verify it's loaded
lsmod | grep my_module

# Generate test traffic
ping -c 5 8.8.8.8                          # ICMP
curl http://example.com                     # TCP
nc -u 8.8.8.8 1234                         # UDP

# Watch kernel log
sudo dmesg -wH

# Unload
sudo rmmod my_module

# Check for memory leaks (if kmemleak enabled)
echo scan > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak
```

---

## Summary: The Mental Model Map

```
=====================================================================
          LINUX KERNEL NETWORK HOOK MENTAL MODEL
=====================================================================

QUESTION: "Where should I put my hook?"
                    |
         +----------+----------+
         |                     |
         v                     v
   "I want SPEED"        "I need full sk_buff / socket info"
         |                     |
    Use XDP             "Firewall/NAT/filtering?"
         |                     |
   Earliest point          Use Netfilter
   in RX path              (5 hook points)
                               |
                    "Need socket callbacks?"
                               |
                    Replace sk->sk_data_ready
                    or sk->sk_state_change
                               |
                    "Just observe (read-only)?"
                               |
                       Tracepoints > kprobes

QUESTION: "What context am I in?"
         |
    XDP  -> per-CPU, no allocation, no locks needed
    NAPI -> softirq, GFP_ATOMIC, spin_lock_bh
    Netfilter -> softirq, GFP_ATOMIC, spin_lock_bh
    Notifier -> process context, GFP_KERNEL, mutex OK
    Tracepoint -> depends on where placed
    kprobe -> depends on where placed (be careful)

QUESTION: "Rust or C?"
         |
    C    -> Full access, mature APIs, more footguns
    Rust -> Safe bindings emerging, use `aya` for
            eBPF userspace loader, unsafe {} for kernel
            module hooks until abstractions mature
=====================================================================
```

---

*This guide covers the complete landscape of Linux kernel network hooks as of Linux 6.x. The kernel is a living codebase — APIs evolve, new mechanisms emerge (e.g., BPF kfuncs, struct_ops), and internals shift between versions. Always cross-reference with the current kernel source at [elixir.bootlin.com](https://elixir.bootlin.com) when writing production code.*
