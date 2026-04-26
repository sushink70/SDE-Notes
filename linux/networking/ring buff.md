# Network Ring Buffers in the Linux Kernel
## A Complete, In-Depth Technical Guide

---

## Table of Contents

1. [Foundations: What Is a Ring Buffer?](#1-foundations-what-is-a-ring-buffer)
2. [Linux Kernel Network Stack Architecture](#2-linux-kernel-network-stack-architecture)
3. [Memory Model and DMA Fundamentals](#3-memory-model-and-dma-fundamentals)
4. [The `sk_buff` Structure — The Kernel's Network Packet](#4-the-sk_buff-structure--the-kernels-network-packet)
5. [Network Device Layer and `net_device`](#5-network-device-layer-and-net_device)
6. [RX Ring Buffer — Receiving Packets](#6-rx-ring-buffer--receiving-packets)
7. [TX Ring Buffer — Transmitting Packets](#7-tx-ring-buffer--transmitting-packets)
8. [NAPI — New API Polling Subsystem](#8-napi--new-api-polling-subsystem)
9. [Interrupt Coalescing and IRQ Affinity](#9-interrupt-coalescing-and-irq-affinity)
10. [Multi-Queue Networking and RSS/RPS/RFS](#10-multi-queue-networking-and-rssrpsrfs)
11. [XDP — eXpress Data Path](#11-xdp--express-data-path)
12. [AF_XDP — Zero-Copy User-Space Sockets](#12-af_xdp--zero-copy-user-space-sockets)
13. [io_uring and Networking](#13-io_uring-and-networking)
14. [Page Pool Allocator](#14-page-pool-allocator)
15. [Driver Implementation in C](#15-driver-implementation-in-c)
16. [Rust Implementation in the Kernel](#16-rust-implementation-in-the-kernel)
17. [Performance Tuning and Observability](#17-performance-tuning-and-observability)
18. [Debugging, Tracing, and BPF](#18-debugging-tracing-and-bpf)
19. [Advanced Topics: Comparison with DPDK and RDMA](#19-advanced-topics-comparison-with-dpdk-and-rdma)
20. [Complete Working Examples](#20-complete-working-examples)

---

## 1. Foundations: What Is a Ring Buffer?

### 1.1 The Core Data Structure

A **ring buffer** (also called a circular buffer, circular queue, or cyclic buffer) is a fixed-size data structure that uses a single, contiguous block of memory arranged as if it were connected end-to-end. It is one of the most important primitives in systems programming because it allows lock-free or near-lock-free communication between a producer and a consumer operating at different rates.

The essential property of a ring buffer is that both a **head** pointer (or index) and a **tail** pointer advance monotonically but wrap around when they reach the end of the allocated buffer. This means memory is reused in a circular fashion without ever needing to copy or shift data.

```
Index:   0    1    2    3    4    5    6    7
       +----+----+----+----+----+----+----+----+
Data:  | D0 | D1 | D2 |    |    |    | D6 | D7 |
       +----+----+----+----+----+----+----+----+
                        ^              ^
                       head           tail
                    (next to       (last written)
                     consume)
```

In this example:
- `tail` points to the last element written (index 7, wrapping around)
- `head` points to the next element to be consumed (index 3)
- Elements D6, D7, D0, D1, D2 are valid data — five elements in a buffer of size eight

### 1.2 Why Ring Buffers for Networking?

The network card (NIC) and the CPU operate asynchronously and at different speeds. The NIC receives packets at wire speed (e.g., 100 Gbps), while the CPU must process each packet through multiple layers of the networking stack. A ring buffer is the ideal interface for several reasons:

**Pre-allocated descriptors**: Instead of allocating memory on the critical data path (which would involve locks and a memory allocator), both the NIC and the driver pre-allocate a fixed array of **descriptors**. A descriptor is a small structure (typically 16–64 bytes) that contains a physical address (DMA address) and metadata (length, status flags). The ring itself is just an array of descriptors; the actual packet data lives at the DMA addresses they point to.

**Producer-consumer separation**: The NIC is the producer of incoming packets (RX path) and the consumer of outgoing packets (TX path). The CPU (driver) is the producer on TX and consumer on RX. They communicate purely through shared memory (the descriptor ring) and hardware registers that hold head/tail pointers.

**No locking on the fast path**: In a well-designed implementation, the producer advances one pointer and the consumer advances another. In a single-producer, single-consumer (SPSC) scenario, this requires only memory barriers — not spinlocks or mutexes.

**Bounded latency**: Because the ring is fixed size, the system degrades gracefully under load: when the ring is full, packets are dropped rather than causing unbounded memory allocation or system-wide slowdown.

### 1.3 Producer-Consumer Protocol

The canonical invariants of a ring buffer with `size` slots (always a power of two for efficiency):

```
empty:   head == tail
full:    (tail + 1) % size == head
count:   (tail - head + size) % size
space:   size - count - 1
```

When `size` is a power of two, the modulo can be replaced by a bitmask:

```c
#define RING_SIZE  4096          /* Must be power of two */
#define RING_MASK  (RING_SIZE - 1)

static inline u32 ring_count(u32 head, u32 tail) {
    return (tail - head) & RING_MASK;
}

static inline u32 ring_space(u32 head, u32 tail) {
    return RING_SIZE - ring_count(head, tail) - 1;
}
```

When using monotonically increasing integers (never wrapping), the ring index is just `ptr & RING_MASK`. This is cleaner because it avoids the empty vs. full ambiguity and allows `tail - head` to always give the correct count (assuming the difference never exceeds `UINT_MAX / 2`):

```c
/* Driver maintains u32 head and tail that increment forever */
/* Index into array:  ptr & RING_MASK                        */
bool ring_full(u32 head, u32 tail) {
    return (tail - head) >= RING_SIZE;
}
bool ring_empty(u32 head, u32 tail) {
    return head == tail;
}
```

### 1.4 Memory Barriers in Ring Buffers

On modern architectures (x86, ARM64), processors reorder memory accesses for performance. A ring buffer used between CPU and hardware (or between two CPUs) must use appropriate **memory barriers** to prevent the CPU from reordering reads/writes in ways that break the protocol.

Linux provides these primitives:

```c
/* Compiler barrier only — prevents compiler reordering, not CPU */
barrier();

/* Full memory barrier — all loads/stores before this are visible */
/* before any loads/stores after this                             */
smp_mb();

/* Read (load) barrier */
smp_rmb();

/* Write (store) barrier */
smp_wmb();

/* Acquire semantic: no later access can be reordered before this load */
smp_load_acquire(&ptr);

/* Release semantic: no earlier access can be reordered after this store */
smp_store_release(&ptr, val);
```

For DMA ring buffers shared between CPU and hardware, you additionally need:

```c
/* Ensure CPU-side stores are visible to the device before ringing doorbell */
dma_wmb();   /* write barrier for DMA                                       */
dma_rmb();   /* read barrier for DMA                                        */
```

The `dma_wmb()` macro expands to `wmb()` on architectures where DMA coherency is not guaranteed by hardware, and to `barrier()` on x86 (which has a strong memory model and coherent DMA).

---

## 2. Linux Kernel Network Stack Architecture

### 2.1 Layers of the Stack

Understanding ring buffers requires understanding how a packet traverses the kernel's networking stack. The journey from NIC to application (RX path) involves these layers:

```
Application (user space)
      ↕   [system call: recv/recvmsg/read]
─────────────────────────────────────────
      Socket Layer  (struct sock, struct socket)
      ↕
      Transport Layer  (TCP: tcp_rcv_established, UDP: __udp4_lib_rcv)
      ↕
      Network Layer   (ip_rcv, ip_local_deliver)
      ↕
      Netfilter hooks  (iptables/nftables)
      ↕
      Traffic Control  (tc qdisc — on TX path only)
      ↕
      Network Device Layer  (dev_queue_xmit, netif_receive_skb)
      ↕
      Device Driver
      ↕
      DMA + Ring Buffer
      ↕
NIC Hardware
```

### 2.2 The Critical Paths

**RX (Receive) Critical Path:**

```
NIC DMA writes packet → descriptor ring updated → interrupt fired
→ driver NAPI poll scheduled → driver reads descriptor ring
→ sk_buff allocated → packet data attached
→ netif_receive_skb() → protocol handlers
→ socket receive queue → application wakes up
```

**TX (Transmit) Critical Path:**

```
Application write() → socket send buffer
→ protocol builds sk_buff → dev_queue_xmit()
→ qdisc (queue discipline) → driver xmit callback
→ driver maps packet to DMA → descriptor written to TX ring
→ doorbell rang (notify NIC) → NIC fetches descriptor
→ NIC DMAs packet data → NIC sends packet
→ completion interrupt → driver frees descriptor + sk_buff
```

### 2.3 Softirq Processing

The Linux kernel processes network receive interrupts in two stages to avoid holding interrupts disabled for long periods:

**Stage 1 — Hardware Interrupt (hardirq)**: The NIC fires an interrupt. The interrupt handler (ISR) runs in hardirq context, which is very brief. It typically just disables further interrupts from the NIC and schedules a softirq.

**Stage 2 — Software Interrupt (softirq)**: The kernel's `NET_RX_SOFTIRQ` softirq processes the actual packets. Softirqs run with interrupts re-enabled, in a bounded time window, allowing the CPU to remain responsive.

The NAPI subsystem (covered in detail later) coordinates between these two stages.

```c
/* Simplified: what happens during a network receive interrupt */

/* Stage 1 — hardirq context, very brief */
static irqreturn_t my_nic_interrupt(int irq, void *data) {
    struct my_nic *nic = data;

    /* Acknowledge interrupt at hardware level */
    my_nic_ack_irq(nic);

    /* Disable this NIC's interrupts — NAPI will re-enable them */
    my_nic_disable_rx_irq(nic);

    /* Schedule NAPI poll — this triggers NET_RX_SOFTIRQ */
    napi_schedule(&nic->napi);

    return IRQ_HANDLED;
}

/* Stage 2 — softirq context, processes actual packets */
static int my_nic_poll(struct napi_struct *napi, int budget) {
    struct my_nic *nic = container_of(napi, struct my_nic, napi);
    int work_done;

    work_done = my_nic_clean_rx_ring(nic, budget);

    if (work_done < budget) {
        /* We're done — no more packets pending */
        napi_complete_done(napi, work_done);
        /* Re-enable hardware interrupts */
        my_nic_enable_rx_irq(nic);
    }

    return work_done;
}
```

---

## 3. Memory Model and DMA Fundamentals

### 3.1 Virtual, Physical, and Bus Addresses

To understand ring buffers, you must understand the Linux kernel's memory address spaces:

- **Virtual address (VA)**: What the CPU sees through the MMU (Memory Management Unit). All kernel code uses virtual addresses. On x86-64, the kernel lives in the upper half of the virtual address space.
- **Physical address (PA)**: The actual address on the memory bus. Obtained with `virt_to_phys()` for directly mapped memory.
- **DMA address (bus address)**: What the device sees. On most x86 systems this equals the physical address, but on systems with an IOMMU (Input-Output Memory Management Unit), the IOMMU provides a separate address space for devices — the device's DMA addresses are translated by the IOMMU to physical addresses, providing isolation and protection.

```
CPU                     IOMMU                    Device (NIC)
 │                        │                          │
 │  virtual → physical    │  DMA address → physical  │
 │  (via MMU page tables) │  (via IOMMU tables)      │
 │                        │                          │
 └──────── physical memory bus ────────────────────── ┘
```

### 3.2 DMA Mapping

Before a device can access memory, the driver must map it using the DMA API. This:
1. Ensures the physical memory pages are pinned (won't be swapped out)
2. Sets up IOMMU mappings if present
3. Performs any necessary cache flushing/invalidation
4. Returns a `dma_addr_t` that the driver writes into hardware descriptors

```c
#include <linux/dma-mapping.h>

/* Allocate coherent DMA memory — both CPU and device see the same data */
/* No explicit cache operations needed.                                  */
void *cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
/* cpu_addr: kernel virtual address to read/write                        */
/* dma_handle: DMA address to program into the NIC descriptor            */

/* When done: */
dma_free_coherent(dev, size, cpu_addr, dma_handle);

/* Map a single buffer for streaming DMA — more efficient for packet data */
dma_addr_t dma_addr = dma_map_single(dev, cpu_addr, size, DMA_FROM_DEVICE);
if (dma_mapping_error(dev, dma_addr)) {
    /* Error handling — IOMMU out of space, etc. */
}

/* After device has written data (RX completion): unmap before CPU reads */
dma_unmap_single(dev, dma_addr, size, DMA_FROM_DEVICE);

/* Map a page (common pattern for RX buffers) */
dma_addr_t dma_addr = dma_map_page(dev, page, offset, size, DMA_FROM_DEVICE);
dma_unmap_page(dev, dma_addr, size, DMA_FROM_DEVICE);
```

### 3.3 Cache Coherency

On x86, the CPU and DMA are cache-coherent: when the NIC DMA-writes to memory, the CPU automatically sees the updated data. On ARM and other architectures, explicit cache operations may be needed.

The `DMA_FROM_DEVICE` and `DMA_TO_DEVICE` flags inform the DMA layer which direction data flows, allowing it to perform appropriate cache operations:

- `DMA_TO_DEVICE`: CPU has finished writing; must flush CPU caches to memory before device reads
- `DMA_FROM_DEVICE`: Device has written; must invalidate CPU caches so CPU reads fresh data

`dma_alloc_coherent` allocates from a region that is always coherent (usually uncached or write-through), so no explicit sync operations are needed.

### 3.4 Descriptor Ring Memory Layout

The descriptor ring itself (the array of descriptors) is typically allocated as coherent DMA memory, because both CPU and NIC read and write individual descriptor fields. The packet data buffers can be streaming DMA, since they flow in one direction.

```c
/* Typical RX ring setup */
struct rx_desc {
    __le64 addr;     /* DMA address of packet buffer — NIC writes here  */
    __le16 len;      /* Length of received data — NIC fills this        */
    __le16 vlan;     /* VLAN tag if present                             */
    __le32 status;   /* Status flags: EOP, L4_CSUM_OK, etc.            */
};

struct rx_ring {
    struct rx_desc *desc;     /* Kernel VA of descriptor array (coherent DMA) */
    dma_addr_t     dma;      /* DMA address of descriptor array              */
    struct page   **pages;   /* Per-descriptor page pointers                 */
    dma_addr_t    *dma_addrs;/* Per-descriptor DMA addresses                 */
    u32            head;     /* Next descriptor to clean (CPU advances)      */
    u32            tail;     /* Next descriptor to give to NIC (CPU writes)  */
    u32            count;    /* Total number of descriptors                  */
};
```

### 3.5 Huge Pages and Memory Allocation

For high-performance networking, standard 4KB pages introduce overhead per packet because each page can only hold one MTU-sized packet (~1500 bytes). The wasted space (2596 bytes) adds up.

Several strategies exist:

**Page recycling (page pool)**: Reuse the same pages by tracking their reference counts. When the last sk_buff referencing a page is freed, return the page to the pool rather than releasing it to the buddy allocator.

**Huge pages (HugeTLB)**: Use 2MB or 1GB pages. Fewer TLB entries needed, less TLB pressure for NIC DMA operations.

**GRO (Generic Receive Offload)**: Coalesce many small sk_buffs into one large sk_buff, reducing the per-packet overhead on the stack. Described later.

---

## 4. The `sk_buff` Structure — The Kernel's Network Packet

### 4.1 Overview

The `struct sk_buff` (socket buffer, abbreviated `skb`) is the fundamental data structure representing a network packet anywhere in the Linux kernel. It is defined in `include/linux/skbuff.h` and is one of the largest and most complex structures in the kernel (over 200 fields in recent kernels).

An skb does not necessarily own the memory containing packet data. Instead, it contains **pointers** into a separately allocated buffer, plus a large amount of metadata. This allows:
- **Zero-copy cloning**: `skb_clone()` creates a new skb that shares the same data buffer (reference counted)
- **Header headroom**: Protocols can prepend headers without copying
- **Fragmented buffers**: Data can be spread across multiple pages (scatter-gather)

### 4.2 The `sk_buff` Memory Layout

```
struct sk_buff memory layout:

┌─────────────────────────────────────────┐
│           struct sk_buff                │
│                                         │
│  head ─────────────────────────────┐   │
│  data ──────────────────────┐      │   │
│  tail ──────────────────┐   │      │   │
│  end ────────────────┐  │   │      │   │
│                      │  │   │      │   │
└──────────────────────┼──┼───┼──────┼───┘
                       │  │   │      │
                       ▼  ▼   ▼      ▼
     Packet buffer:   [headroom][data][tailroom][skb_shared_info]
                                ↑
                          actual packet bytes

skb_headroom(skb) = skb->data - skb->head
skb_tailroom(skb) = skb->end  - skb->tail
skb_headlen(skb)  = skb->tail - skb->data  (linear data length)
```

The `skb_shared_info` structure lives at `skb->end` and holds:
- `nr_frags`: Number of scatter-gather page fragments
- `frags[]`: Array of `skb_frag_t`, each pointing to a page+offset+length
- `frag_list`: Chain of additional sk_buffs for non-linear data
- `gso_*`: GSO (Generic Segmentation Offload) metadata

### 4.3 Key `sk_buff` Fields

```c
struct sk_buff {
    /* --- Queue management --- */
    union {
        struct {
            struct sk_buff      *next;
            struct sk_buff      *prev;
        };
        struct rb_node          rbnode;   /* Used in TCP/other trees */
    };
    union {
        struct sock             *sk;      /* Owning socket, or NULL  */
        int                     ip_defrag_offset;
    };

    /* --- Timing --- */
    ktime_t                     tstamp;   /* Receive timestamp        */

    /* --- Device --- */
    struct net_device           *dev;     /* Source/destination device */

    /* --- Data pointers --- */
    unsigned char               *head;   /* Start of allocated buffer */
    unsigned char               *data;   /* Start of packet data      */
    unsigned char               *tail;   /* End of packet data        */
    unsigned char               *end;    /* End of allocated buffer   */

    /* --- Lengths --- */
    unsigned int                len;     /* Total packet length       */
    unsigned int                data_len;/* Non-linear (frag) length  */
    __u16                       mac_len; /* Length of MAC header      */
    __u16                       hdr_len; /* Length for GSO segments   */

    /* --- Checksum --- */
    __wsum                      csum;    /* Checksum value            */
    __u8                        ip_summed:2; /* Checksum type         */
    __u8                        csum_valid:1;

    /* --- Protocol / Type --- */
    __be16                      protocol; /* Layer 3 protocol (ETH_P_IP, etc.) */
    __u16                       transport_header; /* Offset to L4 header */
    __u16                       network_header;   /* Offset to L3 header */
    __u16                       mac_header;       /* Offset to L2 header */

    /* --- Cloning --- */
    refcount_t                  users;
    atomic_t                    dataref;  /* References to data buffer */

    /* ... many more fields ... */
};
```

### 4.4 Working with sk_buff Headers

The kernel uses offset-based header access rather than direct pointer arithmetic:

```c
/* Set header offsets (typically done during protocol processing) */
skb_reset_mac_header(skb);      /* mac_header = data - head */
skb_set_network_header(skb, ETH_HLEN);  /* Skip past Ethernet header */
skb_set_transport_header(skb, ETH_HLEN + sizeof(struct iphdr));

/* Access headers */
struct ethhdr  *eth = eth_hdr(skb);
struct iphdr   *iph = ip_hdr(skb);
struct tcphdr  *th  = tcp_hdr(skb);

/* Push/pull data pointer (add/remove header space) */
unsigned char *ptr = skb_push(skb, sizeof(struct ethhdr)); /* prepend */
unsigned char *ptr = skb_pull(skb, sizeof(struct ethhdr)); /* consume */
unsigned char *ptr = skb_put(skb,  payload_len);           /* append  */
```

### 4.5 sk_buff Allocation and Deallocation

```c
/* Allocate an skb with data buffer of `size` bytes and `priority` headroom */
struct sk_buff *skb = alloc_skb(size + NET_SKB_PAD, GFP_ATOMIC);

/* Allocate from a pre-built pool (faster, avoids slab allocator on hot path) */
struct sk_buff *skb = napi_alloc_skb(napi, data_len);

/* Build an skb around an existing data buffer (zero-copy RX) */
struct sk_buff *skb = build_skb(data, frag_size);

/* Clone — shares data, new skb metadata */
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);

/* Copy — completely independent copy */
struct sk_buff *copy = skb_copy(skb, GFP_ATOMIC);

/* Decrement refcount; free if zero */
kfree_skb(skb);           /* From error paths — records drop reason */
consume_skb(skb);         /* From success paths                     */
dev_kfree_skb_any(skb);   /* Safe from any context (hardirq/softirq) */
```

### 4.6 Fragmented Packets (Non-Linear sk_buff)

Modern NICs can scatter-gather: they DMA packet data into multiple non-contiguous memory regions. The kernel represents this with `skb_shared_info`:

```c
/* Check if skb has non-linear data */
bool is_nonlinear = skb_is_nonlinear(skb);  /* data_len > 0 */

/* Access a fragment */
skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
struct page *page = skb_frag_page(frag);
u32 offset        = skb_frag_off(frag);
u32 size          = skb_frag_size(frag);

/* Linearize (coalesce into one contiguous buffer) — may copy data */
if (skb_linearize(skb) != 0) {
    /* OOM or error */
}

/* Iterate all data (linear + frags) without linearizing */
struct skb_seq_state state;
skb_prepare_seq_read(skb, 0, skb->len, &state);
unsigned int consumed;
u8 *data;
while ((data = skb_seq_read(consumed, &consumed, &state)) != NULL) {
    /* process data bytes */
}
skb_abort_seq_read(&state);
```

---

## 5. Network Device Layer and `net_device`

### 5.1 The `net_device` Structure

Every network interface in Linux (physical NIC, virtual device, loopback) is represented by `struct net_device` (defined in `include/linux/netdevice.h`). This structure holds:

- Interface name (`ifname`: eth0, enp3s0, etc.)
- Hardware address (MAC)
- Statistics counters
- Pointers to driver operations (`net_device_ops`)
- Ethtool operations (`ethtool_ops`)
- NAPI structures for polling
- Queue structures for multi-queue support
- Feature flags (checksum offload, TSO, LRO, etc.)

### 5.2 `net_device_ops` — The Driver Interface

The driver registers a set of callbacks through `struct net_device_ops`. The most important for ring buffer management:

```c
static const struct net_device_ops my_netdev_ops = {
    .ndo_open           = my_open,         /* Interface brought up         */
    .ndo_stop           = my_stop,         /* Interface brought down       */
    .ndo_start_xmit     = my_xmit,         /* Transmit a packet            */
    .ndo_get_stats64    = my_get_stats,    /* Return stats counters        */
    .ndo_set_rx_mode    = my_set_rx_mode,  /* Promiscuous/multicast        */
    .ndo_change_mtu     = my_change_mtu,   /* MTU change                   */
    .ndo_tx_timeout     = my_tx_timeout,   /* Watchdog: TX hung            */
    .ndo_set_features   = my_set_features, /* Enable/disable offloads      */
    .ndo_bpf            = my_bpf,          /* Attach XDP program           */
    .ndo_xdp_xmit       = my_xdp_xmit,    /* XDP TX (for XDP_TX action)   */
};
```

### 5.3 Transmit Queues (`netdev_queue`)

Each network device can have multiple transmit queues, represented by `struct netdev_queue`. Each queue has:
- A `qdisc` (queue discipline — the traffic control layer)
- A spinlock protecting the queue
- Statistics counters
- State flags (stopped, frozen, etc.)

The driver communicates queue status to the kernel:

```c
/* Stop a TX queue — called when ring is full */
netif_stop_queue(dev);               /* Single queue */
netif_stop_subqueue(dev, queue_idx); /* Specific queue */
netif_tx_stop_all_queues(dev);       /* All queues    */

/* Wake a TX queue — called after ring has space again */
netif_wake_queue(dev);
netif_wake_subqueue(dev, queue_idx);
netif_tx_wake_all_queues(dev);

/* Check if a queue is stopped */
if (netif_queue_stopped(dev)) { ... }
```

### 5.4 Receive Queues and `napi_struct`

Each receive queue has an associated `napi_struct`:

```c
struct napi_struct {
    struct list_head poll_list;   /* Entry in the poll list          */
    unsigned long    state;       /* NAPI state bits                 */
    int              weight;      /* Max packets per poll (budget)   */
    int            (*poll)(struct napi_struct *, int); /* Poll func  */
    struct net_device *dev;       /* Associated device               */
    struct sk_buff   *skb;        /* skb being built (GRO)           */
    struct list_head rx_list;     /* GRO receive list                */
    int              rx_count;    /* GRO packets queued              */
    /* ... */
};
```

---

## 6. RX Ring Buffer — Receiving Packets

### 6.1 RX Descriptor Formats

Different NIC families use different descriptor formats, but the concepts are universal. Here is a typical receive descriptor pair (Intel i40e style — using separate writeback descriptors):

```c
/* Receive descriptor — what the driver writes to the NIC */
union i40e_rx_desc {
    /* Read format: written by driver, read by NIC */
    struct {
        __le64 pkt_addr;   /* DMA address of packet buffer */
        __le64 hdr_addr;   /* DMA address of header buffer (split header) */
    } read;

    /* Write-back format: written by NIC, read by driver */
    struct {
        struct {
            struct {
                __le16 mirroring_status;
                __le16 l2tag1;
            } lo_dword;
            union {
                __le32 rss;    /* RSS hash value                  */
                __le32 fd_id;  /* Flow Director filter ID         */
            } hi_dword;
        } qword0;
        struct {
            __le64 status_error_len; /* Status bits, error bits, length */
        } qword1;
    } wb;  /* write-back */
};

/* Extracting fields from the write-back descriptor */
#define I40E_RXD_QW1_LENGTH_PBUF_SHIFT  38
#define I40E_RXD_QW1_LENGTH_PBUF_MASK   (0x3FFFULL << I40E_RXD_QW1_LENGTH_PBUF_SHIFT)
#define I40E_RXD_QW1_STATUS_SHIFT       0
#define I40E_RXD_QW1_STATUS_EOF_SHIFT   1
#define I40E_RXD_QW1_STATUS_DD_SHIFT    0  /* Descriptor Done bit */
```

### 6.2 RX Ring Lifecycle

The RX ring lifecycle involves five phases that repeat continuously:

**Phase 1 — Initialization**: Allocate the descriptor ring (coherent DMA). For each descriptor, allocate a page, map it for DMA, write the DMA address into the descriptor, and advance the tail register.

**Phase 2 — NIC ownership**: The NIC owns descriptors from `head` to `tail - 1`. When a packet arrives, the NIC finds the next available descriptor, DMAs the packet data to the buffer address, writes packet metadata into the write-back descriptor, and advances its internal head pointer.

**Phase 3 — Driver polling (NAPI)**: The driver reads descriptors starting at `nxt_to_clean`. It checks the Descriptor Done (DD) bit to see if the NIC has written the descriptor. For each completed descriptor, it builds an sk_buff and passes it up the stack.

**Phase 4 — Refill**: After consuming a descriptor, the driver must give it back to the NIC with a new buffer. If refill fails (OOM), the descriptor is re-used without giving it to the NIC — the ring stalls until memory is available.

**Phase 5 — Normal operation**: The cycle continues. The key invariant is that the driver always tries to keep the ring full of pre-posted buffers for the NIC to use.

### 6.3 Complete RX Ring Implementation in C

```c
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/skbuff.h>

#define RX_RING_SIZE    512
#define RX_BUF_SIZE     2048   /* Larger than MTU to handle VLAN overhead */

/* Hardware receive descriptor */
struct hw_rx_desc {
    __le64 addr;    /* Physical address of the packet buffer */
    __le32 len;     /* [0:15]=packet len, [16:31]=status    */
    __le32 csum;    /* Hardware-computed checksum            */
};

/* Status bit definitions */
#define HW_RX_STATUS_DD     BIT(0)   /* Descriptor Done                */
#define HW_RX_STATUS_EOP    BIT(1)   /* End Of Packet                  */
#define HW_RX_STATUS_L3L4P  BIT(2)   /* L3/L4 checksum computed        */
#define HW_RX_STATUS_IPCS   BIT(3)   /* IP checksum success            */
#define HW_RX_STATUS_TCPCS  BIT(4)   /* TCP checksum success           */

/* Per-descriptor software state */
struct rx_buffer {
    struct page   *page;       /* Page holding packet data        */
    dma_addr_t     dma;        /* DMA address of the page         */
    unsigned int   page_offset;/* Offset within page              */
};

/* The RX ring structure */
struct rx_ring {
    struct hw_rx_desc  *desc;       /* Descriptor array (coherent DMA)  */
    dma_addr_t          desc_dma;   /* DMA address of descriptor array  */
    struct rx_buffer   *buffers;    /* Per-descriptor software state     */
    struct napi_struct  napi;       /* NAPI structure for polling        */
    struct net_device  *netdev;     /* Parent net_device                 */
    struct device      *dev;        /* Parent device (for DMA)           */
    void __iomem       *tail_reg;   /* MMIO register for tail pointer    */
    u32                 head;       /* Next descriptor to clean          */
    u32                 tail;       /* Next descriptor to post to NIC    */
    u32                 count;      /* Total descriptor count            */

    /* Statistics */
    u64                 rx_packets;
    u64                 rx_bytes;
    u64                 rx_dropped;
};

/*
 * rx_ring_alloc_page - Allocate a page and map it for DMA.
 *
 * Returns 0 on success, -ENOMEM on failure.
 */
static int rx_ring_alloc_page(struct rx_ring *ring, struct rx_buffer *buf)
{
    struct page *page;
    dma_addr_t dma;

    page = dev_alloc_page();
    if (unlikely(!page))
        return -ENOMEM;

    dma = dma_map_page(ring->dev, page, 0, PAGE_SIZE, DMA_FROM_DEVICE);
    if (unlikely(dma_mapping_error(ring->dev, dma))) {
        __free_page(page);
        return -ENOMEM;
    }

    buf->page        = page;
    buf->dma         = dma;
    buf->page_offset = 0;

    return 0;
}

/*
 * rx_ring_setup - Allocate and initialize an RX descriptor ring.
 */
int rx_ring_setup(struct rx_ring *ring)
{
    int i, ret;
    struct rx_buffer *buf;
    struct hw_rx_desc *desc;

    /* Allocate descriptor array as coherent DMA memory.             */
    /* Both the CPU and NIC read/write individual fields of each     */
    /* descriptor, so coherent (non-cached) memory is appropriate.   */
    ring->desc = dma_alloc_coherent(ring->dev,
                                    ring->count * sizeof(struct hw_rx_desc),
                                    &ring->desc_dma,
                                    GFP_KERNEL);
    if (!ring->desc)
        return -ENOMEM;

    /* Allocate software state array */
    ring->buffers = kcalloc(ring->count, sizeof(struct rx_buffer), GFP_KERNEL);
    if (!ring->buffers) {
        ret = -ENOMEM;
        goto err_free_desc;
    }

    /* Initialize each descriptor with a pre-allocated page buffer.  */
    /* The NIC needs buffers available before it can receive packets. */
    for (i = 0; i < ring->count; i++) {
        buf  = &ring->buffers[i];
        desc = &ring->desc[i];

        ret = rx_ring_alloc_page(ring, buf);
        if (ret)
            goto err_free_buffers;

        /* Write the DMA address into the hardware descriptor.       */
        /* The NIC will DMA packet data here when a packet arrives.  */
        desc->addr = cpu_to_le64(buf->dma + buf->page_offset);
        desc->len  = 0;  /* NIC will fill this */
        desc->csum = 0;

        /* Memory barrier: ensure CPU writes to descriptor are       */
        /* visible before we tell the NIC about them.                */
        /* (On x86 this is a no-op for coherent memory, but is       */
        /* correct practice for portability.)                         */
        dma_wmb();
    }

    ring->head = 0;
    ring->tail = ring->count - 1;  /* Give all but last to NIC      */

    /* Tell the NIC where the ring ends — hardware tail register.    */
    /* Writing to this MMIO register causes the NIC to accept        */
    /* descriptors [0, tail] as available for receive.               */
    writel(ring->tail, ring->tail_reg);

    return 0;

err_free_buffers:
    for (i--; i >= 0; i--) {
        buf = &ring->buffers[i];
        dma_unmap_page(ring->dev, buf->dma, PAGE_SIZE, DMA_FROM_DEVICE);
        __free_page(buf->page);
    }
    kfree(ring->buffers);
err_free_desc:
    dma_free_coherent(ring->dev,
                      ring->count * sizeof(struct hw_rx_desc),
                      ring->desc, ring->desc_dma);
    return ret;
}

/*
 * rx_ring_teardown - Free all resources associated with an RX ring.
 */
void rx_ring_teardown(struct rx_ring *ring)
{
    int i;
    struct rx_buffer *buf;

    for (i = 0; i < ring->count; i++) {
        buf = &ring->buffers[i];
        if (buf->page) {
            dma_unmap_page(ring->dev, buf->dma, PAGE_SIZE, DMA_FROM_DEVICE);
            __free_page(buf->page);
            buf->page = NULL;
        }
    }

    kfree(ring->buffers);

    dma_free_coherent(ring->dev,
                      ring->count * sizeof(struct hw_rx_desc),
                      ring->desc, ring->desc_dma);
    ring->desc = NULL;
}

/*
 * rx_ring_clean - Process completed RX descriptors during NAPI poll.
 *
 * @ring:   The RX ring to clean
 * @budget: Maximum number of packets to process (NAPI budget)
 *
 * Returns the number of packets processed.
 */
static int rx_ring_clean(struct rx_ring *ring, int budget)
{
    int packets_done = 0;
    u32 head         = ring->head;
    u32 tail_to_post = ring->tail;

    while (packets_done < budget) {
        struct hw_rx_desc *desc = &ring->desc[head & (ring->count - 1)];
        struct rx_buffer  *buf  = &ring->buffers[head & (ring->count - 1)];
        struct sk_buff    *skb;
        u32                status, pkt_len;

        /*
         * Check the Descriptor Done bit.
         * The NIC sets this bit after writing packet data and metadata.
         * We must read this atomically with a read barrier to prevent
         * the CPU from reading packet data before the DD bit is set.
         */
        status = le32_to_cpu(desc->len);

        /*
         * Use dma_rmb() to ensure the DD bit read is not reordered
         * with subsequent reads of descriptor fields (len, csum).
         * Without this, the CPU might read pkt_len before the NIC
         * has finished writing the write-back descriptor.
         */
        if (!(status & HW_RX_STATUS_DD))
            break;

        dma_rmb();

        pkt_len = status & 0xFFFF;  /* Lower 16 bits: packet length */

        /*
         * Unmap the DMA buffer before reading packet data.
         * This is required on non-coherent architectures to
         * invalidate CPU caches and ensure we see the NIC's writes.
         * On x86 with coherent DMA this is a no-op.
         */
        dma_unmap_page(ring->dev, buf->dma, PAGE_SIZE, DMA_FROM_DEVICE);

        /*
         * Build an sk_buff around the received packet data.
         * build_skb() attaches to an existing data buffer without
         * copying — this is the zero-copy receive path.
         *
         * The data buffer layout is:
         *   [page_address + page_offset + NET_SKB_PAD] = packet start
         *
         * NET_SKB_PAD reserves space for the skb_shared_info at the
         * end of the buffer and ensures proper alignment.
         */
        skb = build_skb(page_address(buf->page) + buf->page_offset,
                        RX_BUF_SIZE);
        if (unlikely(!skb)) {
            /* Failed to build skb — drop the packet */
            ring->rx_dropped++;
            goto refill;
        }

        /*
         * Set the data range within the buffer.
         * skb->data initially points to the start of the buffer;
         * we need to skip NET_SKB_PAD bytes of reserved space.
         */
        skb_reserve(skb, NET_SKB_PAD);
        skb_put(skb, pkt_len);

        /* Set protocol (Ethernet — parse the EtherType field) */
        skb->protocol = eth_type_trans(skb, ring->netdev);
        skb->dev      = ring->netdev;

        /* Report hardware checksum offload status */
        if (status & HW_RX_STATUS_L3L4P) {
            if ((status & HW_RX_STATUS_IPCS) &&
                (status & HW_RX_STATUS_TCPCS)) {
                skb->ip_summed = CHECKSUM_UNNECESSARY;
            }
        }

        /* Update statistics */
        ring->rx_packets++;
        ring->rx_bytes += pkt_len;

        /*
         * Deliver the packet to the networking stack.
         * napi_gro_receive() attempts GRO (Generic Receive Offload)
         * coalescing before passing to netif_receive_skb().
         */
        napi_gro_receive(&ring->napi, skb);

        /* The page is now owned by the sk_buff — don't free it */
        buf->page = NULL;

refill:
        /*
         * Allocate a new page for this descriptor slot and write
         * its DMA address back into the hardware descriptor.
         * This makes the slot available for the NIC to reuse.
         */
        if (rx_ring_alloc_page(ring, buf) == 0) {
            desc->addr = cpu_to_le64(buf->dma + buf->page_offset);
            desc->len  = 0;
            desc->csum = 0;

            /*
             * dma_wmb(): Ensure descriptor write is complete before
             * we update tail_to_post. On weak-ordering architectures,
             * without this barrier the NIC might see the tail advance
             * before seeing the valid descriptor content.
             */
            dma_wmb();

            tail_to_post = head;
        } else {
            /*
             * OOM: leave this descriptor without a buffer.
             * The ring will not advance past here until we can
             * allocate. In practice, drivers often schedule a
             * work queue to retry allocation.
             */
            ring->rx_dropped++;
        }

        head++;
        packets_done++;
    }

    ring->head = head;

    /*
     * Post new descriptors to the NIC by writing the tail register.
     * This is the "doorbell" — it signals the NIC that descriptors
     * [old_tail .. tail_to_post] are now available.
     *
     * We batch this update (write once at the end rather than per
     * descriptor) to minimize expensive MMIO writes.
     */
    if (tail_to_post != ring->tail) {
        ring->tail = tail_to_post;
        /* wmb() ensures descriptor writes are visible before doorbell */
        wmb();
        writel(ring->tail & (ring->count - 1), ring->tail_reg);
    }

    return packets_done;
}
```

---

## 7. TX Ring Buffer — Transmitting Packets

### 7.1 TX Descriptor Architecture

The TX path is more complex than RX because:

1. **Multi-segment transmits**: A single packet may span multiple sk_buff fragments. The NIC uses scatter-gather DMA to read them all without copying.
2. **Context descriptors**: Many NICs require a separate "context descriptor" before a data descriptor to configure offloads (TSO, checksumming). The context and data descriptors together describe one transmission.
3. **Completion tracking**: The driver must track which descriptors are still in use by the NIC. It cannot free an sk_buff until the NIC has finished reading it.

### 7.2 TX Descriptor Types

```c
/* Context descriptor — configures offload for following data descriptors */
struct hw_tx_ctx_desc {
    __le32 tucse;   /* TCP/UDP Checksum Start/End             */
    __le32 tucso;   /* TCP/UDP Checksum Offset               */
    __le32 tucss;   /* TCP/UDP Checksum Start                */
    __le32 ipcse;   /* IP Checksum Start/End                 */
    __le32 ipcso;   /* IP Checksum Offset                    */
    __le32 ipcss;   /* IP Checksum Start                     */
    __le16 mss;     /* Maximum Segment Size (for TSO)        */
    __le16 hdrlen;  /* Header length (for TSO)               */
    __le32 cmd;     /* Command bits (TSO enable, etc.)       */
};

/* Data descriptor — describes one DMA buffer for transmission */
struct hw_tx_data_desc {
    __le64 addr;    /* DMA address of data buffer             */
    __le16 len;     /* Length of this buffer                  */
    __le8  dtyp;    /* Descriptor type                        */
    __le8  dcmd;    /* Command: EOP, IFCS, RS, etc.          */
    __le32 paylen;  /* Total payload length (for TSO)         */
};

/* Command bits for dcmd field */
#define HW_TXD_CMD_EOP  BIT(0)  /* End Of Packet — last descriptor for this pkt */
#define HW_TXD_CMD_IFCS BIT(1)  /* Insert Frame Check Sequence (CRC)            */
#define HW_TXD_CMD_RS   BIT(3)  /* Report Status — NIC will set DD bit          */
#define HW_TXD_CMD_TSE  BIT(7)  /* TCP Segmentation Enable                      */
```

### 7.3 Complete TX Ring Implementation in C

```c
/* Per-descriptor software state for TX */
struct tx_buffer {
    struct sk_buff   *skb;       /* NULL for frags, set on EOP descriptor      */
    dma_addr_t        dma;       /* DMA address of this buffer segment         */
    u32               len;       /* Length of this buffer segment              */
    bool              is_eop;    /* Is this the End-Of-Packet descriptor?      */
};

struct tx_ring {
    struct hw_tx_data_desc *desc;      /* Descriptor array                     */
    dma_addr_t              desc_dma;  /* DMA address of descriptor array      */
    struct tx_buffer       *buffers;   /* Per-descriptor software state         */
    struct device          *dev;
    struct net_device      *netdev;
    void __iomem           *tail_reg;  /* MMIO tail pointer register           */
    u32                     head;      /* Next descriptor to clean (completed) */
    u32                     tail;      /* Next descriptor to fill (transmit)   */
    u32                     count;
    spinlock_t              lock;      /* Protects tail and tx-side state      */

    u64                     tx_packets;
    u64                     tx_bytes;
};

/*
 * tx_ring_available_descs - How many descriptors are free?
 *
 * We reserve one descriptor to distinguish full from empty:
 *   full:  (tail + 1) % count == head
 *   empty: tail == head
 */
static inline u32 tx_ring_available_descs(struct tx_ring *ring)
{
    return ring->count - (ring->tail - ring->head) - 1;
}

/*
 * tx_ring_need_descs - How many descriptors does this skb need?
 *
 * We need:
 *   - 1 context descriptor (for checksum offload / TSO)
 *   - 1 data descriptor for linear data (if any)
 *   - 1 data descriptor per fragment
 */
static inline int tx_ring_need_descs(struct sk_buff *skb)
{
    return 1 + (skb->data_len > 0 ? 1 : 0) + skb_shinfo(skb)->nr_frags + 1;
}

/*
 * tx_ring_map_skb - Map all segments of an skb for DMA transmit.
 *
 * Returns the number of descriptors used, or negative on error.
 */
static int tx_ring_map_skb(struct tx_ring *ring, struct sk_buff *skb,
                            u32 *first_desc_idx)
{
    u32 tail = ring->tail & (ring->count - 1);
    u32 nr_descs = 0;
    dma_addr_t dma;
    int i;

    *first_desc_idx = tail;

    /* Map and write the linear (head) portion of the skb */
    if (skb_headlen(skb) > 0) {
        dma = dma_map_single(ring->dev, skb->data,
                             skb_headlen(skb), DMA_TO_DEVICE);
        if (dma_mapping_error(ring->dev, dma))
            goto err_unmap;

        ring->desc[tail].addr  = cpu_to_le64(dma);
        ring->desc[tail].len   = cpu_to_le16(skb_headlen(skb));
        ring->desc[tail].dcmd  = HW_TXD_CMD_IFCS;
        ring->desc[tail].dtyp  = 1; /* Data descriptor type */

        ring->buffers[tail].dma    = dma;
        ring->buffers[tail].len    = skb_headlen(skb);
        ring->buffers[tail].skb    = NULL;
        ring->buffers[tail].is_eop = false;

        tail = (tail + 1) & (ring->count - 1);
        nr_descs++;
    }

    /* Map each page fragment */
    for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];

        dma = skb_frag_dma_map(ring->dev, frag, 0,
                               skb_frag_size(frag), DMA_TO_DEVICE);
        if (dma_mapping_error(ring->dev, dma))
            goto err_unmap;

        ring->desc[tail].addr  = cpu_to_le64(dma);
        ring->desc[tail].len   = cpu_to_le16(skb_frag_size(frag));
        ring->desc[tail].dcmd  = HW_TXD_CMD_IFCS;
        ring->desc[tail].dtyp  = 1;

        ring->buffers[tail].dma    = dma;
        ring->buffers[tail].len    = skb_frag_size(frag);
        ring->buffers[tail].skb    = NULL;
        ring->buffers[tail].is_eop = false;

        tail = (tail + 1) & (ring->count - 1);
        nr_descs++;
    }

    /* Mark the last descriptor as End-Of-Packet (EOP)             */
    /* The NIC transmits all descriptors between first and EOP      */
    /* as one packet. After EOP, it sets DD on this descriptor.    */
    {
        u32 eop_idx = (tail - 1) & (ring->count - 1);
        ring->desc[eop_idx].dcmd |= HW_TXD_CMD_EOP | HW_TXD_CMD_RS;
        ring->buffers[eop_idx].is_eop = true;
        ring->buffers[eop_idx].skb    = skb;  /* Freed on completion */
    }

    ring->tail = ring->tail + nr_descs;

    ring->tx_packets++;
    ring->tx_bytes += skb->len;

    return nr_descs;

err_unmap:
    /* Unmap everything we mapped so far */
    while (nr_descs-- > 0) {
        u32 idx = (*first_desc_idx + nr_descs) & (ring->count - 1);
        dma_unmap_single(ring->dev, ring->buffers[idx].dma,
                         ring->buffers[idx].len, DMA_TO_DEVICE);
    }
    return -ENOMEM;
}

/*
 * my_xmit - The ndo_start_xmit callback. Called by the networking stack
 *            to transmit a packet.
 *
 * Must return NETDEV_TX_OK or NETDEV_TX_BUSY.
 * MUST NOT sleep.
 */
static netdev_tx_t my_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct my_nic *nic   = netdev_priv(dev);
    struct tx_ring *ring = &nic->tx_ring;
    u32 first_desc;
    int nr_descs;

    /* Check if we have space. We need at least tx_ring_need_descs(skb)
     * free descriptors. If not, stop the queue and return BUSY.        */
    if (unlikely(tx_ring_available_descs(ring) < tx_ring_need_descs(skb))) {
        netif_stop_queue(dev);
        /* Ensure we re-check after stopping queue */
        smp_mb();
        if (tx_ring_available_descs(ring) >= tx_ring_need_descs(skb)) {
            netif_start_queue(dev);
            goto do_xmit;
        }
        return NETDEV_TX_BUSY;
    }

do_xmit:
    nr_descs = tx_ring_map_skb(ring, skb, &first_desc);
    if (unlikely(nr_descs < 0)) {
        dev_kfree_skb_any(skb);
        dev->stats.tx_dropped++;
        return NETDEV_TX_OK;
    }

    /*
     * Ensure all descriptor writes are complete before writing
     * the tail register. The NIC may start fetching descriptors
     * as soon as it sees the tail advance.
     */
    wmb();

    /* Ring the doorbell — tell the NIC new descriptors are available */
    writel(ring->tail & (ring->count - 1), ring->tail_reg);

    return NETDEV_TX_OK;
}

/*
 * tx_ring_clean - Process completed TX descriptors.
 *
 * Called from the NAPI poll function after a TX completion interrupt,
 * or periodically to free completed sk_buffs.
 *
 * Returns number of descriptors cleaned.
 */
static int tx_ring_clean(struct tx_ring *ring)
{
    u32 head   = ring->head;
    int cleaned = 0;

    while (head != ring->tail) {
        u32 idx               = head & (ring->count - 1);
        struct tx_buffer *buf = &ring->buffers[idx];
        struct hw_tx_data_desc *desc = &ring->desc[idx];

        /* Check if the NIC has finished with this descriptor.        */
        /* The RS (Report Status) bit on the EOP descriptor causes    */
        /* the NIC to set DD on that descriptor when it is done.      */
        /* We only check DD on EOP descriptors to avoid unnecessary   */
        /* MMIO reads.                                                */
        if (buf->is_eop) {
            if (!(le32_to_cpu(desc->dcmd) & HW_TXD_CMD_RS))
                break;
            /* Read DD bit from the NIC's write-back */
            dma_rmb();
        }

        /* Unmap this buffer segment */
        if (buf->dma) {
            if (buf->is_eop && skb_shinfo(buf->skb)->nr_frags == 0) {
                dma_unmap_single(ring->dev, buf->dma,
                                 buf->len, DMA_TO_DEVICE);
            } else {
                dma_unmap_page(ring->dev, buf->dma,
                               buf->len, DMA_TO_DEVICE);
            }
            buf->dma = 0;
        }

        /* Free the sk_buff when we reach the EOP descriptor */
        if (buf->is_eop && buf->skb) {
            dev_consume_skb_any(buf->skb);
            buf->skb    = NULL;
            buf->is_eop = false;
        }

        head++;
        cleaned++;
    }

    ring->head = head;

    /* Wake the TX queue if it was stopped and we now have space */
    if (netif_queue_stopped(ring->netdev) &&
        tx_ring_available_descs(ring) > tx_ring_need_descs(NULL)) {
        netif_wake_queue(ring->netdev);
    }

    return cleaned;
}
```

---

## 8. NAPI — New API Polling Subsystem

### 8.1 The Problem with Interrupt-Driven Receive

In the early Linux network stack, every packet caused a hardware interrupt. This worked well at low packet rates but caused catastrophic performance degradation at high rates because:

- **Interrupt overhead**: Each interrupt involves saving/restoring register state, flushing caches, and running interrupt handlers. At 1M pps (million packets per second), this alone consumes significant CPU cycles.
- **Livelock**: If the NIC sends interrupts faster than the CPU can process packets, the CPU spends all its time in interrupt handlers and never actually processes packets — the system becomes unresponsive.
- **Head-of-line blocking**: Interrupts fire even when the CPU is doing useful work, preempting it unnecessarily.

### 8.2 NAPI Solution: Interrupt-to-Poll Transition

NAPI (New API, merged in Linux 2.5) solves this with a hybrid approach:

1. The **first packet** triggers a hardware interrupt
2. The interrupt handler **disables further interrupts** from the NIC and **schedules a softirq poll**
3. The softirq poll function (called periodically by `net_rx_action`) processes up to `budget` packets
4. If the poll processes fewer than `budget` packets, the ring is empty — the poll re-enables interrupts and exits
5. If the poll reaches `budget`, it reschedules itself (the ring is still busy — stay in poll mode)

This way, the system uses interrupts at low traffic (low latency, low CPU usage) and switches to polling at high traffic (high throughput, no interrupt overhead).

### 8.3 NAPI State Machine

```c
/* NAPI state bits (in napi_struct.state) */
#define NAPI_STATE_SCHED      0   /* Scheduled to run (poll active) */
#define NAPI_STATE_MISSED     1   /* Packet arrived while polling    */
#define NAPI_STATE_DISABLE    2   /* Disabled via napi_disable()     */
#define NAPI_STATE_NPSVC      3   /* Marked as non-preemptible       */
#define NAPI_STATE_LISTED     4   /* On the device's napi_list       */
#define NAPI_STATE_NO_BUSY_POLL 5 /* Busy polling disabled           */
#define NAPI_STATE_IN_BUSY_POLL 6 /* Currently busy polling          */
```

The NAPI state machine:

```
   [Idle, IRQ enabled]
         │
    Packet arrives
    → Hardware IRQ fires
         │
    napi_schedule()
         │
    [Scheduled, IRQ disabled]
         │
    NET_RX_SOFTIRQ runs
    → poll() called
         │
    ┌────┴──────────────────────────┐
    │                               │
  work < budget               work == budget
  (ring drained)              (ring still full)
    │                               │
  napi_complete_done()        Reschedule NAPI
  Re-enable IRQ                     │
    │                    Return budget to kernel
    │                               │
    └───────────────────────────────┘
    [Back to Idle]
```

### 8.4 NAPI Implementation Details

```c
/* Initialize NAPI during device probe */
int my_nic_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct net_device *netdev;
    struct my_nic *nic;

    netdev = alloc_etherdev(sizeof(struct my_nic));
    nic    = netdev_priv(netdev);

    /* Register NAPI with a budget weight of 64 (typical for most NICs).
     * The weight is the maximum packets to process per poll invocation.
     * Higher weight = more packets per poll = better throughput but
     * worse latency (other NAPI instances get less CPU time).
     * The kernel default is NAPI_POLL_WEIGHT = 64.                     */
    netif_napi_add(netdev, &nic->rx_ring.napi, my_nic_poll, NAPI_POLL_WEIGHT);

    /* For multiple RX queues, use netif_napi_add() per queue */
    /* netif_napi_add_weight(netdev, &ring->napi, poll_fn, weight); */

    return 0;
}

/* Enable NAPI when interface comes up */
static int my_open(struct net_device *netdev)
{
    struct my_nic *nic = netdev_priv(netdev);

    /* ... setup rings, enable hardware ... */

    /* Enable NAPI — allow napi_schedule() to schedule polls */
    napi_enable(&nic->rx_ring.napi);

    /* Enable hardware interrupts */
    my_nic_enable_irq(nic);

    netif_start_queue(netdev);
    return 0;
}

/* Disable NAPI when interface goes down */
static int my_stop(struct net_device *netdev)
{
    struct my_nic *nic = netdev_priv(netdev);

    netif_stop_queue(netdev);

    /* Disable NAPI — blocks until any in-progress poll completes */
    napi_disable(&nic->rx_ring.napi);

    /* Disable hardware interrupts */
    my_nic_disable_irq(nic);

    return 0;
}

/*
 * The NAPI poll function — called from NET_RX_SOFTIRQ context.
 *
 * @napi:   The NAPI structure for this queue
 * @budget: Maximum packets to process
 *
 * Returns: Number of packets processed.
 *          Must be <= budget.
 *          Return budget itself to signal "ring still has work" and
 *          reschedule. Return < budget to signal "ring drained".
 */
static int my_nic_poll(struct napi_struct *napi, int budget)
{
    struct rx_ring *ring = container_of(napi, struct rx_ring, napi);
    int work_done;

    /* Clean TX completions opportunistically — TX and RX share
     * the same interrupt, so we handle both here.                */
    tx_ring_clean(ring->nic->tx_ring);

    /* Process up to `budget` received packets */
    work_done = rx_ring_clean(ring, budget);

    /* If we processed fewer packets than the budget, the ring is
     * empty. Complete NAPI processing and re-enable interrupts.  */
    if (work_done < budget) {
        /*
         * napi_complete_done() returns true if we should re-enable
         * interrupts. It may return false if napi_schedule() was
         * called concurrently (packet arrived during poll) — in that
         * case we should continue polling.
         */
        if (napi_complete_done(napi, work_done)) {
            /* Re-enable hardware interrupts for this queue */
            my_nic_enable_rx_irq(ring->nic, ring->queue_idx);
        }
    }

    return work_done;
}
```

### 8.5 Generic Receive Offload (GRO)

GRO is a software optimization that coalesces multiple received TCP segments into a single large sk_buff before passing to the IP layer. This dramatically reduces per-packet processing overhead:

- Without GRO: 1000 × 1460-byte TCP segments → 1000 sk_buff allocations, 1000 TCP ACKs, 1000 runs through the TCP state machine
- With GRO: 1000 segments coalesced → 10 × 64KB sk_buffs, 10 TCP state machine runs

GRO works in the NAPI poll context:

```c
/* Use napi_gro_receive() instead of netif_receive_skb() in your poll function */
napi_gro_receive(&ring->napi, skb);

/* When NAPI completes (napi_complete_done()), GRO flushes any
 * coalesced sk_buffs into the stack. The kernel handles this. */
```

GRO is only valid for homogeneous packets (same flow, sequential sequence numbers, no holes). The `skb_shinfo(skb)->gso_*` fields carry segmentation information up the stack.

---

## 9. Interrupt Coalescing and IRQ Affinity

### 9.1 Interrupt Moderation

Interrupt coalescing (also called interrupt moderation or interrupt throttling) delays the hardware interrupt for some microseconds or until N packets have arrived. This reduces the interrupt rate, allowing the CPU to process more packets per context switch.

The trade-off is latency: with aggressive coalescing, the first packet of a burst experiences additional delay before being processed.

Linux exposes coalescing parameters via ethtool:

```bash
# View current coalescing settings
ethtool -c eth0

# Set RX interrupt coalescing: wait 50µs or 64 packets, whichever comes first
ethtool -C eth0 rx-usecs 50 rx-frames 64

# Set TX coalescing
ethtool -C eth0 tx-usecs 50 tx-frames 64

# Adaptive coalescing (hardware auto-tunes based on traffic)
ethtool -C eth0 adaptive-rx on adaptive-tx on
```

In the driver, implement via `ethtool_ops`:

```c
static int my_get_coalesce(struct net_device *netdev,
                            struct ethtool_coalesce *ec,
                            struct kernel_ethtool_coalesce *kernel_coal,
                            struct netlink_ext_ack *extack)
{
    struct my_nic *nic = netdev_priv(netdev);
    ec->rx_coalesce_usecs  = nic->rx_itr_usecs;
    ec->rx_max_coalesced_frames = nic->rx_itr_frames;
    ec->tx_coalesce_usecs  = nic->tx_itr_usecs;
    ec->tx_max_coalesced_frames = nic->tx_itr_frames;
    ec->use_adaptive_rx_coalesce = nic->adaptive_rx;
    return 0;
}

static int my_set_coalesce(struct net_device *netdev,
                            struct ethtool_coalesce *ec,
                            struct kernel_ethtool_coalesce *kernel_coal,
                            struct netlink_ext_ack *extack)
{
    struct my_nic *nic = netdev_priv(netdev);

    nic->rx_itr_usecs  = ec->rx_coalesce_usecs;
    nic->rx_itr_frames = ec->rx_max_coalesced_frames;
    nic->tx_itr_usecs  = ec->tx_coalesce_usecs;
    nic->tx_itr_frames = ec->tx_max_coalesced_frames;
    nic->adaptive_rx   = ec->use_adaptive_rx_coalesce;

    /* Program the hardware interrupt moderation registers */
    my_nic_set_itr(nic);

    return 0;
}
```

### 9.2 IRQ Affinity and CPU Pinning

On multi-queue NICs, each queue has a separate interrupt. For best performance, each queue's interrupt should be pinned to a specific CPU core, and application threads should run on the same core (NUMA locality, cache warmth).

```bash
# View IRQ assignments
cat /proc/interrupts | grep eth0

# Set CPU affinity for IRQ 42 to CPU 2
echo 4 > /proc/irq/42/smp_affinity   # bitmask: 4 = CPU 2 (0-indexed)

# Or use irqbalance daemon for automatic balancing
systemctl start irqbalance

# Set IRQ affinity using irq_set_affinity_hint from the driver
irq_set_affinity_hint(pci_irq_vector(pdev, queue_idx),
                      cpumask_of(queue_idx % num_online_cpus()));
```

---

## 10. Multi-Queue Networking and RSS/RPS/RFS

### 10.1 Receive Side Scaling (RSS)

Modern NICs have multiple RX queues. RSS distributes incoming packets across queues based on a hash of the packet's flow (typically src/dst IP + src/dst port). This allows multiple CPU cores to process packets in parallel without contention.

The hash function is typically Toeplitz, computed in hardware:

```
RSS Hash = Toeplitz(src_ip, dst_ip, src_port, dst_port, secret_key)
Queue index = RSS Hash % num_queues
```

Configuration:

```bash
# View RSS hash configuration
ethtool -x eth0

# Set number of RX/TX queues
ethtool -L eth0 rx 8 tx 8

# Configure hash function
ethtool -X eth0 hfunc toeplitz
ethtool -X eth0 equal 8     # Spread equally across 8 queues
```

Driver implementation of multi-queue support:

```c
/* Allocate one ring per queue */
static int my_alloc_queues(struct my_nic *nic, int num_queues)
{
    int i;

    nic->rx_rings = kcalloc(num_queues, sizeof(struct rx_ring), GFP_KERNEL);
    nic->tx_rings = kcalloc(num_queues, sizeof(struct tx_ring), GFP_KERNEL);

    for (i = 0; i < num_queues; i++) {
        nic->rx_rings[i].count = RX_RING_SIZE;
        nic->rx_rings[i].queue_idx = i;

        /* Register one NAPI per queue */
        netif_napi_add(nic->netdev, &nic->rx_rings[i].napi,
                       my_nic_poll, NAPI_POLL_WEIGHT);

        rx_ring_setup(&nic->rx_rings[i]);
        tx_ring_setup(&nic->tx_rings[i]);
    }

    return 0;
}
```

### 10.2 Receive Packet Steering (RPS) — Software RSS

RPS is a software alternative to RSS for NICs with a single RX queue. It distributes packets to CPUs using a software hash and an inter-processor interrupt (IPI):

```bash
# Enable RPS: allow all CPUs to handle packets for eth0 queue 0
echo ff > /sys/class/net/eth0/queues/rx-0/rps_cpus
```

RPS adds latency because it involves an IPI, but allows single-queue NICs to benefit from multiple cores.

### 10.3 Receive Flow Steering (RFS)

RFS extends RPS by steering packets to the CPU where the application thread consuming them is actually running. This improves cache utilization:

```bash
# Enable RFS globally — set flow table size
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries

# Enable per-queue flow table
echo 4096 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

### 10.4 Transmit Packet Steering (XPS)

XPS maps CPU cores to TX queues, ensuring that packets from a given core use the same TX queue. This eliminates spinlock contention between cores on the TX queue:

```bash
# Map CPUs 0-3 to TX queue 0
echo f > /sys/class/net/eth0/queues/tx-0/xps_cpus
```

---

## 11. XDP — eXpress Data Path

### 11.1 XDP Architecture

XDP (eXpress Data Path) allows running BPF programs at the earliest possible point in the receive path — inside the device driver, before any sk_buff is allocated. This enables packet processing at line rate with minimal overhead.

XDP operates on **xdp_buff** structures, which are simpler than sk_buffs:

```c
struct xdp_buff {
    void               *data;          /* Pointer to start of packet data  */
    void               *data_end;      /* Pointer to end of packet data    */
    void               *data_meta;     /* Metadata area (before data)      */
    void               *data_hard_start; /* Start of DMA buffer           */
    struct xdp_rxq_info *rxq;          /* RX queue information             */
    struct xdp_txq_info *txq;          /* TX queue information             */
    u32                  frame_sz;     /* Frame/page size                  */
};
```

XDP programs return one of these verdicts:

```c
enum xdp_action {
    XDP_ABORTED = 0,  /* Bug — drop and trace                           */
    XDP_DROP,         /* Drop the packet silently                        */
    XDP_PASS,         /* Pass to normal network stack (allocate sk_buff) */
    XDP_TX,           /* Retransmit on the same NIC (hairpin forwarding) */
    XDP_REDIRECT,     /* Redirect to another NIC, CPU, or AF_XDP socket  */
};
```

### 11.2 Driver Integration for XDP

Integrating XDP into a driver requires the driver to call the BPF program before allocating an sk_buff:

```c
#include <linux/bpf.h>
#include <net/xdp.h>

/* In rx_ring_clean(), before allocating sk_buff: */
static int rx_ring_clean_xdp(struct rx_ring *ring, int budget)
{
    int packets_done = 0;
    u32 head = ring->head;

    while (packets_done < budget) {
        struct hw_rx_desc *desc = &ring->desc[head & (ring->count - 1)];
        struct rx_buffer  *buf  = &ring->buffers[head & (ring->count - 1)];
        u32 status, pkt_len;
        struct xdp_buff xdp;
        u32 act;

        status = le32_to_cpu(desc->len);
        if (!(status & HW_RX_STATUS_DD))
            break;
        dma_rmb();

        pkt_len = status & 0xFFFF;

        /* Sync the page for CPU access (on non-coherent architectures) */
        dma_sync_single_for_cpu(ring->dev, buf->dma, pkt_len,
                                DMA_FROM_DEVICE);

        /* Build an xdp_buff — lighter weight than sk_buff */
        xdp_init_buff(&xdp, PAGE_SIZE, &ring->xdp_rxq);
        xdp_prepare_buff(&xdp,
                         page_address(buf->page),  /* data_hard_start */
                         NET_SKB_PAD,              /* offset from hard_start to data */
                         pkt_len,                  /* data size */
                         false);                   /* not frame_sz aligned */

        /* Run the XDP BPF program if one is attached */
        act = bpf_prog_run_xdp(ring->xdp_prog, &xdp);

        switch (act) {
        case XDP_PASS:
            /* Fall through to normal stack processing */
            goto build_skb;

        case XDP_DROP:
            /* Drop the packet — recycle the page */
            ring->rx_dropped++;
            goto recycle_page;

        case XDP_TX:
            /* Retransmit on this NIC — driver must handle this */
            if (my_xdp_xmit_frame(ring, &xdp) != 0) {
                ring->rx_dropped++;
                goto recycle_page;
            }
            /* Don't recycle — xmit owns the page now */
            goto alloc_new;

        case XDP_REDIRECT:
            /* Redirect to another device or AF_XDP socket */
            if (xdp_do_redirect(ring->netdev, &xdp, ring->xdp_prog) != 0) {
                ring->rx_dropped++;
                goto recycle_page;
            }
            goto alloc_new;

        default:
            bpf_warn_invalid_xdp_action(ring->netdev, ring->xdp_prog, act);
            /* Fall through to drop */
        case XDP_ABORTED:
            trace_xdp_exception(ring->netdev, ring->xdp_prog, act);
            goto recycle_page;
        }

build_skb:
        /* Only reached for XDP_PASS — allocate sk_buff as normal */
        {
            struct sk_buff *skb = build_skb(xdp.data_hard_start, PAGE_SIZE);
            if (skb) {
                skb_reserve(skb, xdp.data - xdp.data_hard_start);
                skb_put(skb, pkt_len);
                skb->protocol = eth_type_trans(skb, ring->netdev);
                napi_gro_receive(&ring->napi, skb);
            } else {
                ring->rx_dropped++;
            }
        }
        buf->page = NULL;
        goto alloc_new;

recycle_page:
        /* Return the page to the ring — no new allocation needed */
        dma_sync_single_for_device(ring->dev, buf->dma, PAGE_SIZE,
                                   DMA_FROM_DEVICE);
        /* Repost the same descriptor */
        desc->addr = cpu_to_le64(buf->dma + buf->page_offset);
        desc->len  = 0;
        dma_wmb();
        /* Update tail to return this slot to the NIC */
        ring->tail = head;
        writel(ring->tail & (ring->count - 1), ring->tail_reg);
        head++;
        packets_done++;
        continue;

alloc_new:
        rx_ring_alloc_page(ring, buf);
        desc->addr = cpu_to_le64(buf->dma + buf->page_offset);
        desc->len  = 0;
        dma_wmb();
        ring->tail = head;
        writel(ring->tail & (ring->count - 1), ring->tail_reg);
        head++;
        packets_done++;
    }

    ring->head = head;

    /* Flush XDP redirect pending operations */
    xdp_do_flush();

    return packets_done;
}
```

### 11.3 Writing an XDP Program

XDP programs are BPF programs loaded into the kernel. Here is a complete XDP program that drops packets to a specific IP and counts all others:

```c
/* xdp_filter.c — compiled with clang -target bpf */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <arpa/inet.h>

/* BPF map to count packets per action */
struct {
    __uint(type,        BPF_MAP_TYPE_ARRAY);
    __type(key,         __u32);
    __type(value,       __u64);
    __uint(max_entries, 4);
} pkt_count SEC(".maps");

/* Drop all packets from this IP */
#define BLOCKED_IP  0x0a000001  /* 10.0.0.1 */

SEC("xdp")
int xdp_filter_prog(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;
    struct ethhdr *eth;
    struct iphdr  *iph;
    __u32 key;
    __u64 *cnt;

    /* Parse Ethernet header — always bounds-check against data_end! */
    eth = data;
    if ((void *)(eth + 1) > data_end)
        goto pass;

    /* Only handle IPv4 */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        goto pass;

    /* Parse IP header */
    iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        goto pass;

    /* Drop blocked source IP */
    if (bpf_ntohl(iph->saddr) == BLOCKED_IP) {
        key = XDP_DROP;
        cnt = bpf_map_lookup_elem(&pkt_count, &key);
        if (cnt) __sync_fetch_and_add(cnt, 1);
        return XDP_DROP;
    }

pass:
    key = XDP_PASS;
    cnt = bpf_map_lookup_elem(&pkt_count, &key);
    if (cnt) __sync_fetch_and_add(cnt, 1);
    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

Load the XDP program using libbpf:

```bash
# Compile
clang -O2 -target bpf -c xdp_filter.c -o xdp_filter.o

# Load onto interface (native mode — runs in driver)
ip link set dev eth0 xdp obj xdp_filter.o sec xdp

# Or using xdp-loader
xdp-loader load eth0 xdp_filter.o

# View attached program
ip link show eth0
```

XDP modes:

- **Native (driver mode)**: Program runs inside the driver's NAPI poll, before sk_buff allocation. Requires driver support. Fastest.
- **Generic (SKB mode)**: Program runs after sk_buff allocation in `netif_receive_skb`. Works on any driver but slower (no zero-copy benefit).
- **Offloaded**: Program runs on NIC hardware (SmartNIC). Requires hardware support. Fastest possible.

---

## 12. AF_XDP — Zero-Copy User-Space Sockets

### 12.1 Overview

AF_XDP (Address Family XDP) is a socket type that allows user-space applications to receive and transmit packets with zero-copy, bypassing most of the kernel stack. It works in conjunction with XDP programs:

- An XDP program running in the driver redirects selected packets to an AF_XDP socket using `XDP_REDIRECT`
- The AF_XDP socket directly maps DMA memory into user space
- User-space reads packets directly from the NIC's ring buffer memory

### 12.2 UMEM — User Memory

The central concept of AF_XDP is the **UMEM** (User Memory): a contiguous region of memory that the user allocates and registers with the kernel. The NIC DMAs packet data directly into this memory, and the user reads it without any copy.

UMEM is divided into fixed-size frames (chunks). The default frame size is 4096 bytes (one page).

### 12.3 AF_XDP Ring Pairs

AF_XDP exposes four rings to user space:

- **RX ring**: User reads received packet descriptors (frame address + length)
- **TX ring**: User writes packet descriptors to transmit
- **FILL ring**: User produces frame addresses for the kernel to use as RX buffers
- **COMPLETION ring**: Kernel produces frame addresses that the NIC has finished transmitting

```
User Space                              Kernel/NIC
──────────────────────────────────────────────────
FILL ring  ──→ (frame addresses)  ──→  NIC RX buffer
                                         │ (DMA write)
RX ring    ←── (frame addr+len)  ←──  Completed RX

TX ring    ──→ (frame addr+len)  ──→  NIC TX send
                                         │
COMPLETION ←── (frame addresses) ←──  TX Complete
```

### 12.4 Complete AF_XDP User-Space Implementation

```c
/* af_xdp_user.c — Zero-copy packet receive using AF_XDP */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <linux/if_link.h>
#include <xdp/xsk.h>
#include <xdp/libxdp.h>
#include <net/if.h>

#define NUM_FRAMES       4096
#define FRAME_SIZE       XSK_UMEM__DEFAULT_FRAME_SIZE  /* 4096 */
#define RX_BATCH_SIZE    64
#define INVALID_UMEM_FRAME UINT64_MAX

struct xsk_socket_info {
    struct xsk_ring_cons rx;
    struct xsk_ring_prod tx;
    struct xsk_umem_info *umem;
    struct xsk_socket    *xsk;

    /* Frame address recycling pool */
    u64 umem_frame_addr[NUM_FRAMES];
    u32 umem_frame_free;

    u64 rx_npkts;
    u64 tx_npkts;
};

struct xsk_umem_info {
    struct xsk_ring_prod fq;   /* Fill ring  */
    struct xsk_ring_cons cq;   /* Completion ring */
    struct xsk_umem     *umem;
    void                *buffer; /* UMEM buffer */
};

/*
 * xsk_configure_umem - Allocate UMEM and register with kernel.
 */
static struct xsk_umem_info *xsk_configure_umem(void *buffer, u64 size)
{
    struct xsk_umem_info *umem;
    struct xsk_umem_config cfg = {
        .fill_size      = XSK_RING_PROD__DEFAULT_NUM_DESCS * 2,
        .comp_size      = XSK_RING_CONS__DEFAULT_NUM_DESCS,
        .frame_size     = FRAME_SIZE,
        .frame_headroom = XSK_UMEM__DEFAULT_FRAME_HEADROOM,
        .flags          = 0,
    };
    int ret;

    umem = calloc(1, sizeof(*umem));

    /*
     * xsk_umem__create registers the memory region with the kernel.
     * The kernel will set up DMA mappings so the NIC can write
     * directly into this buffer.
     */
    ret = xsk_umem__create(&umem->umem, buffer, size,
                           &umem->fq, &umem->cq, &cfg);
    if (ret) {
        fprintf(stderr, "xsk_umem__create failed: %s\n", strerror(-ret));
        free(umem);
        return NULL;
    }

    umem->buffer = buffer;
    return umem;
}

/*
 * xsk_configure_socket - Create and configure an AF_XDP socket.
 */
static struct xsk_socket_info *xsk_configure_socket(
    struct xsk_umem_info *umem, const char *ifname, u32 queue_id)
{
    struct xsk_socket_config cfg;
    struct xsk_socket_info *xsk_info;
    struct xsk_ring_cons *rxr;
    struct xsk_ring_prod *txr;
    int i, ret;

    xsk_info = calloc(1, sizeof(*xsk_info));
    xsk_info->umem = umem;

    /* Initialize the free frame pool */
    for (i = 0; i < NUM_FRAMES; i++)
        xsk_info->umem_frame_addr[i] = i * FRAME_SIZE;
    xsk_info->umem_frame_free = NUM_FRAMES;

    cfg.rx_size       = XSK_RING_CONS__DEFAULT_NUM_DESCS;
    cfg.tx_size       = XSK_RING_PROD__DEFAULT_NUM_DESCS;
    cfg.libbpf_flags  = XSK_LIBBPF_FLAGS__INHIBIT_PROG_LOAD;
    cfg.xdp_flags     = XDP_FLAGS_UPDATE_IF_NOEXIST;
    cfg.bind_flags    = XDP_ZEROCOPY;  /* Request zero-copy mode */

    rxr = &xsk_info->rx;
    txr = &xsk_info->tx;

    ret = xsk_socket__create(&xsk_info->xsk, ifname, queue_id,
                             umem->umem, rxr, txr, &cfg);
    if (ret) {
        fprintf(stderr, "xsk_socket__create failed: %s\n", strerror(-ret));
        free(xsk_info);
        return NULL;
    }

    /*
     * Pre-populate the fill ring with frame addresses.
     * The kernel uses these to post RX buffers to the NIC.
     * Without filling this ring, the NIC has no buffers and
     * cannot receive packets.
     */
    u32 idx;
    ret = xsk_ring_prod__reserve(&umem->fq,
                                  XSK_RING_PROD__DEFAULT_NUM_DESCS, &idx);
    if (ret != XSK_RING_PROD__DEFAULT_NUM_DESCS) {
        fprintf(stderr, "Could not fill fill ring\n");
        xsk_socket__delete(xsk_info->xsk);
        free(xsk_info);
        return NULL;
    }

    for (i = 0; i < XSK_RING_PROD__DEFAULT_NUM_DESCS; i++)
        *xsk_ring_prod__fill_addr(&umem->fq, idx++) =
            xsk_alloc_umem_frame(xsk_info);

    xsk_ring_prod__submit(&umem->fq, XSK_RING_PROD__DEFAULT_NUM_DESCS);

    return xsk_info;
}

/* Allocate a UMEM frame from the free pool */
static u64 xsk_alloc_umem_frame(struct xsk_socket_info *xsk)
{
    if (xsk->umem_frame_free == 0)
        return INVALID_UMEM_FRAME;
    return xsk->umem_frame_addr[--xsk->umem_frame_free];
}

/* Return a UMEM frame to the free pool */
static void xsk_free_umem_frame(struct xsk_socket_info *xsk, u64 frame)
{
    xsk->umem_frame_addr[xsk->umem_frame_free++] = frame;
}

/*
 * rx_and_process - Receive a batch of packets and process them.
 *
 * This is the main receive loop. It:
 * 1. Peeks at the RX ring for completed descriptors
 * 2. Processes each packet (here just prints info)
 * 3. Returns frames to the fill ring for reuse
 */
static void rx_and_process(struct xsk_socket_info *xsk)
{
    unsigned int rcvd, i;
    u32 idx_rx = 0, idx_fq = 0;

    /*
     * xsk_ring_cons__peek checks how many packets are available.
     * idx_rx is set to the first available index.
     * This is non-blocking — returns 0 if no packets ready.
     */
    rcvd = xsk_ring_cons__peek(&xsk->rx, RX_BATCH_SIZE, &idx_rx);
    if (!rcvd) {
        /*
         * No packets received. We could block using poll(2):
         * struct pollfd pfd = { .fd = xsk_socket__fd(xsk->xsk),
         *                       .events = POLLIN };
         * poll(&pfd, 1, -1);
         */
        return;
    }

    /*
     * Reserve space in the fill ring to return frames.
     * We must always return exactly as many frames as we receive,
     * or the NIC will run out of RX buffers.
     */
    if (xsk_ring_prod__reserve(&xsk->umem->fq, rcvd, &idx_fq) != rcvd) {
        /* Fill ring is full — drop packets */
        fprintf(stderr, "Fill ring full! Dropping %u packets\n", rcvd);
        xsk_ring_cons__release(&xsk->rx, rcvd);
        return;
    }

    for (i = 0; i < rcvd; i++) {
        /* Get the received frame descriptor */
        const struct xdp_desc *desc =
            xsk_ring_cons__rx_desc(&xsk->rx, idx_rx++);

        u64 addr = desc->addr;
        u32 len  = desc->len;

        /*
         * addr is the frame address within UMEM.
         * The actual data pointer = UMEM buffer base + addr.
         * Note: addr may have an offset (headroom) added by the driver.
         */
        u64 orig_addr = xsk_umem__extract_addr(addr);
        addr = xsk_umem__add_offset_to_addr(addr);

        char *pkt_data = xsk_umem__get_data(xsk->umem->buffer, addr);

        /* Process the packet */
        xsk->rx_npkts++;
        printf("Received packet: len=%u, src_mac=%02x:%02x:%02x:%02x:%02x:%02x\n",
               len,
               (unsigned char)pkt_data[6],
               (unsigned char)pkt_data[7],
               (unsigned char)pkt_data[8],
               (unsigned char)pkt_data[9],
               (unsigned char)pkt_data[10],
               (unsigned char)pkt_data[11]);

        /*
         * Return the frame to the fill ring for reuse.
         * We use the original address (without offset).
         */
        *xsk_ring_prod__fill_addr(&xsk->umem->fq, idx_fq++) = orig_addr;
    }

    /* Release processed RX descriptors */
    xsk_ring_cons__release(&xsk->rx, rcvd);

    /* Submit refilled frames to the fill ring */
    xsk_ring_prod__submit(&xsk->umem->fq, rcvd);
}

int main(int argc, char **argv)
{
    const char *ifname = argc > 1 ? argv[1] : "eth0";
    u32 queue_id = 0;
    void *bufs;
    struct xsk_umem_info *umem;
    struct xsk_socket_info *xsk;

    /* Allocate UMEM — must be page-aligned */
    bufs = mmap(NULL, NUM_FRAMES * FRAME_SIZE,
                PROT_READ | PROT_WRITE,
                MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, /* Use huge pages */
                -1, 0);
    if (bufs == MAP_FAILED) {
        /* Retry without huge pages */
        bufs = mmap(NULL, NUM_FRAMES * FRAME_SIZE,
                    PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (bufs == MAP_FAILED) {
            perror("mmap"); return 1;
        }
    }

    umem = xsk_configure_umem(bufs, NUM_FRAMES * FRAME_SIZE);
    if (!umem) return 1;

    xsk = xsk_configure_socket(umem, ifname, queue_id);
    if (!xsk) return 1;

    printf("AF_XDP socket ready on %s queue %u\n", ifname, queue_id);
    printf("Press Ctrl+C to stop\n");

    /* Main receive loop */
    for (;;) {
        rx_and_process(xsk);
    }

    return 0;
}
```

---

## 13. io_uring and Networking

### 13.1 io_uring Overview

`io_uring` is a Linux kernel subsystem (added in 5.1) for high-performance asynchronous I/O. It uses two ring buffers — a **submission queue (SQ)** and a **completion queue (CQ)** — shared between user space and the kernel:

- User space writes **SQE** (Submission Queue Entries) describing operations (read, write, accept, recv, etc.)
- The kernel processes SQEs and writes **CQE** (Completion Queue Entries) with results
- No syscalls are needed for normal operation once the rings are set up (with `IORING_SETUP_SQPOLL`)

### 13.2 io_uring Rings Layout

```
User Space Memory (shared with kernel):
┌──────────────────────────────────────────────────────┐
│ io_uring (two rings in one mmap)                     │
│                                                      │
│  Submission Queue (SQ):                              │
│  ┌──────────────┐                                    │
│  │  sq_ring     │ → sq_head, sq_tail, sq_flags, ...  │
│  └──────────────┘                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │  sq_array[]  │ indices into sqes[]           │    │
│  └──────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────┐    │
│  │  sqes[]      │ struct io_uring_sqe entries   │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Completion Queue (CQ):                              │
│  ┌──────────────┐                                    │
│  │  cq_ring     │ → cq_head, cq_tail, cq_flags, ...  │
│  └──────────────┘                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │  cqes[]      │ struct io_uring_cqe entries   │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### 13.3 io_uring for Network I/O

```c
#include <liburing.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define QUEUE_DEPTH   256
#define BUFFER_SIZE   4096
#define BUFFER_COUNT  256

struct io_data {
    int type;         /* ACCEPT, RECV, SEND */
    int fd;
    char buf[BUFFER_SIZE];
};

int main(void)
{
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;
    int server_fd, ret;

    /* Initialize io_uring with depth 256 */
    ret = io_uring_queue_init(QUEUE_DEPTH, &ring, 0);
    if (ret < 0) { perror("io_uring_queue_init"); return 1; }

    /* Create and bind server socket */
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    /* ... bind, listen ... */

    /* Register fixed buffers with io_uring for zero-copy I/O */
    struct iovec iovecs[BUFFER_COUNT];
    char *bufs = calloc(BUFFER_COUNT, BUFFER_SIZE);
    for (int i = 0; i < BUFFER_COUNT; i++) {
        iovecs[i].iov_base = bufs + i * BUFFER_SIZE;
        iovecs[i].iov_len  = BUFFER_SIZE;
    }
    io_uring_register_buffers(&ring, iovecs, BUFFER_COUNT);

    /* Submit initial accept operation */
    struct io_data *data = malloc(sizeof(*data));
    data->type = 0; /* ACCEPT */
    data->fd   = server_fd;

    sqe = io_uring_get_sqe(&ring);
    io_uring_prep_accept(sqe, server_fd, NULL, NULL, 0);
    io_uring_sqe_set_data(sqe, data);
    io_uring_submit(&ring);

    /* Event loop */
    for (;;) {
        /* Wait for at least one completion */
        ret = io_uring_wait_cqe(&ring, &cqe);
        if (ret < 0) break;

        struct io_data *req = io_uring_cqe_get_data(cqe);
        int result = cqe->res;
        io_uring_cqe_seen(&ring, cqe);  /* Mark CQE as consumed */

        if (req->type == 0 && result >= 0) {
            /* Accept completed — result is the new client fd */
            int client_fd = result;

            /* Submit recv operation for the new client */
            struct io_data *recv_data = malloc(sizeof(*recv_data));
            recv_data->type = 1; /* RECV */
            recv_data->fd   = client_fd;

            sqe = io_uring_get_sqe(&ring);
            io_uring_prep_recv(sqe, client_fd, recv_data->buf,
                               BUFFER_SIZE, 0);
            io_uring_sqe_set_data(sqe, recv_data);

            /* Resubmit accept for next client */
            sqe = io_uring_get_sqe(&ring);
            io_uring_prep_accept(sqe, server_fd, NULL, NULL, 0);
            io_uring_sqe_set_data(sqe, req);

            io_uring_submit(&ring);

        } else if (req->type == 1 && result > 0) {
            /* Recv completed — result is number of bytes received */
            printf("Received %d bytes from fd %d\n", result, req->fd);

            /* Echo back — submit send */
            struct io_data *send_data = req;
            send_data->type = 2; /* SEND */

            sqe = io_uring_get_sqe(&ring);
            io_uring_prep_send(sqe, req->fd, req->buf, result, 0);
            io_uring_sqe_set_data(sqe, send_data);
            io_uring_submit(&ring);
        } else {
            free(req);
        }
    }

    io_uring_queue_exit(&ring);
    return 0;
}
```

---

## 14. Page Pool Allocator

### 14.1 Why Page Pool?

The regular kernel memory allocator (`__alloc_pages`) is expensive on the hot path because it:
- Acquires per-CPU or zone locks
- May need to reclaim memory
- Interacts with the page reclaim subsystem

The **page pool** (`include/net/page_pool/types.h`) is a kernel subsystem that maintains a per-CPU cache of pre-allocated pages, specifically designed for network device drivers.

### 14.2 Page Pool Design

```
                    Page Pool
                  ┌───────────────────────────────┐
                  │                               │
  alloc_pages()  →│ Pool pages (per-CPU cache)    │← recycled pages
                  │                               │
                  │  Fast alloc: return cached    │
                  │  page without lock            │
                  └───────────────────────────────┘
                             │ pages
                             ▼
                    RX Ring Buffers
                             │
                             ▼ packet arrives
                    sk_buff (references page)
                             │
                             ▼ sk_buff freed
                    page_pool_put_page() ──→ recycle
```

### 14.3 Page Pool Usage in Drivers

```c
#include <net/page_pool/helpers.h>

/* Create a page pool during ring setup */
struct page_pool_params pp_params = {
    .order         = 0,          /* 4KB pages                         */
    .flags         = PP_FLAG_DMA_MAP | PP_FLAG_DMA_SYNC_DEV,
    .pool_size     = RX_RING_SIZE,
    .nid           = dev_to_node(dev), /* NUMA node for allocation      */
    .dev           = dev,
    .dma_dir       = DMA_FROM_DEVICE,
    .offset        = 0,
    .max_len       = RX_BUF_SIZE,
};

ring->page_pool = page_pool_create(&pp_params);
if (IS_ERR(ring->page_pool)) {
    ret = PTR_ERR(ring->page_pool);
    goto err;
}

/* Register page pool with NAPI for recycling */
ret = xdp_rxq_info_reg_mem_model(&ring->xdp_rxq,
                                  MEM_TYPE_PAGE_POOL,
                                  ring->page_pool);

/* Allocate a page from the pool (fast path) */
struct page *page = page_pool_dev_alloc_pages(ring->page_pool);
dma_addr_t dma = page_pool_get_dma_addr(page); /* DMA addr already set by pool */

/* After receiving a packet — build sk_buff with page pool tracking */
struct sk_buff *skb = build_skb(page_address(page), PAGE_SIZE);
skb_mark_for_recycle(skb);  /* When sk_buff is freed, recycle page to pool */

/* Or explicitly return a page to the pool */
page_pool_put_full_page(ring->page_pool, page, false);

/* Destroy the pool during ring teardown */
page_pool_destroy(ring->page_pool);
```

---

## 15. Driver Implementation in C

### 15.1 Complete Minimal NIC Driver Skeleton

This is a production-quality skeleton for a PCI NIC driver with full ring buffer management:

```c
// SPDX-License-Identifier: GPL-2.0
/*
 * mynic.c — Minimal NIC driver skeleton with ring buffer management
 *
 * Demonstrates:
 * - PCI device probing and MMIO setup
 * - Coherent DMA for descriptor rings
 * - Streaming DMA for packet buffers
 * - NAPI polling
 * - TX with scatter-gather
 * - Interrupt handling
 * - ethtool support
 */

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/pci.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/ethtool.h>
#include <linux/interrupt.h>
#include <linux/dma-mapping.h>
#include <linux/skbuff.h>
#include <linux/if_ether.h>
#include <linux/slab.h>

#define DRIVER_NAME     "mynic"
#define DRIVER_VERSION  "1.0"

/* PCI IDs — replace with real vendor/device IDs */
#define MYNIC_VENDOR_ID  0x1234
#define MYNIC_DEVICE_ID  0x5678

/* MMIO register offsets */
#define REG_CTRL         0x0000  /* Control register              */
#define REG_STATUS       0x0004  /* Status register               */
#define REG_IRQ_MASK     0x0008  /* Interrupt mask                */
#define REG_IRQ_STATUS   0x000C  /* Interrupt status (write-clear)*/
#define REG_RX_RING_LO   0x0010  /* RX ring base address (low 32) */
#define REG_RX_RING_HI   0x0014  /* RX ring base address (high 32)*/
#define REG_RX_HEAD      0x0018  /* RX ring head (NIC writes)     */
#define REG_RX_TAIL      0x001C  /* RX ring tail (driver writes)  */
#define REG_TX_RING_LO   0x0020
#define REG_TX_RING_HI   0x0024
#define REG_TX_HEAD      0x0028
#define REG_TX_TAIL      0x002C
#define REG_MAC_ADDR_LO  0x0030  /* MAC address low 32 bits       */
#define REG_MAC_ADDR_HI  0x0034  /* MAC address high 16 bits      */

/* IRQ bits */
#define IRQ_RX_DONE      BIT(0)
#define IRQ_TX_DONE      BIT(1)
#define IRQ_LINK_CHANGE  BIT(2)
#define IRQ_ALL          (IRQ_RX_DONE | IRQ_TX_DONE | IRQ_LINK_CHANGE)

#define RX_RING_SIZE     256
#define TX_RING_SIZE     256
#define RX_BUF_SIZE      2048
#define TX_STOP_THRESH   16    /* Stop queue if fewer free descs  */

/* Hardware descriptor */
struct mynic_desc {
    __le64 addr;
    __le32 len_status;
    __le32 csum_vlan;
};

#define DESC_STATUS_DD   BIT(0)
#define DESC_STATUS_EOP  BIT(1)
#define DESC_LEN_MASK    0xFFFF
#define DESC_STATUS_SHIFT 16

struct mynic_rx_buf {
    struct page    *page;
    dma_addr_t      dma;
};

struct mynic_tx_buf {
    struct sk_buff *skb;    /* Set on EOP descriptor */
    dma_addr_t      dma;
    u32             len;
    bool            mapped_page; /* Use dma_unmap_page vs single */
};

struct mynic_priv {
    /* PCI/MMIO */
    struct pci_dev    *pdev;
    void __iomem      *base;
    struct net_device *netdev;

    /* RX */
    struct mynic_desc *rx_ring;
    dma_addr_t         rx_ring_dma;
    struct mynic_rx_buf rx_bufs[RX_RING_SIZE];
    u32                rx_head;
    u32                rx_tail;
    struct napi_struct napi;

    /* TX */
    struct mynic_desc *tx_ring;
    dma_addr_t         tx_ring_dma;
    struct mynic_tx_buf tx_bufs[TX_RING_SIZE];
    u32                tx_head;  /* NIC-completed head */
    u32                tx_tail;  /* Next to fill */
    spinlock_t         tx_lock;

    /* Stats */
    struct net_device_stats stats;
};

/* MMIO accessors */
static inline u32 mynic_rd32(struct mynic_priv *p, u32 reg) {
    return readl(p->base + reg);
}
static inline void mynic_wr32(struct mynic_priv *p, u32 reg, u32 val) {
    writel(val, p->base + reg);
}

/* ─── RX ─────────────────────────────────────────────────── */

static int mynic_alloc_rx_buf(struct mynic_priv *p, int idx)
{
    struct mynic_rx_buf *buf = &p->rx_bufs[idx];
    struct mynic_desc   *desc = &p->rx_ring[idx];

    buf->page = dev_alloc_page();
    if (!buf->page) return -ENOMEM;

    buf->dma = dma_map_page(&p->pdev->dev, buf->page, 0,
                             PAGE_SIZE, DMA_FROM_DEVICE);
    if (dma_mapping_error(&p->pdev->dev, buf->dma)) {
        __free_page(buf->page);
        buf->page = NULL;
        return -EIO;
    }

    desc->addr       = cpu_to_le64(buf->dma);
    desc->len_status = 0;
    dma_wmb();
    return 0;
}

static void mynic_free_rx_bufs(struct mynic_priv *p)
{
    int i;
    for (i = 0; i < RX_RING_SIZE; i++) {
        struct mynic_rx_buf *buf = &p->rx_bufs[i];
        if (buf->page) {
            dma_unmap_page(&p->pdev->dev, buf->dma,
                           PAGE_SIZE, DMA_FROM_DEVICE);
            __free_page(buf->page);
            buf->page = NULL;
        }
    }
}

static int mynic_setup_rx_ring(struct mynic_priv *p)
{
    int i, ret;

    p->rx_ring = dma_alloc_coherent(&p->pdev->dev,
                     RX_RING_SIZE * sizeof(struct mynic_desc),
                     &p->rx_ring_dma, GFP_KERNEL);
    if (!p->rx_ring) return -ENOMEM;

    for (i = 0; i < RX_RING_SIZE; i++) {
        ret = mynic_alloc_rx_buf(p, i);
        if (ret) goto err;
    }

    /* Program NIC with ring base address and size */
    mynic_wr32(p, REG_RX_RING_LO, lower_32_bits(p->rx_ring_dma));
    mynic_wr32(p, REG_RX_RING_HI, upper_32_bits(p->rx_ring_dma));
    mynic_wr32(p, REG_RX_TAIL, RX_RING_SIZE - 1);

    p->rx_head = 0;
    p->rx_tail = RX_RING_SIZE - 1;
    return 0;

err:
    mynic_free_rx_bufs(p);
    dma_free_coherent(&p->pdev->dev,
                      RX_RING_SIZE * sizeof(struct mynic_desc),
                      p->rx_ring, p->rx_ring_dma);
    return ret;
}

static int mynic_clean_rx(struct mynic_priv *p, int budget)
{
    int work = 0;
    u32 head = p->rx_head;

    while (work < budget) {
        u32 idx               = head % RX_RING_SIZE;
        struct mynic_desc *desc = &p->rx_ring[idx];
        struct mynic_rx_buf *buf = &p->rx_bufs[idx];
        u32 ls, pktlen;
        struct sk_buff *skb;

        ls = le32_to_cpu(desc->len_status);
        if (!(ls >> DESC_STATUS_SHIFT & 1))  /* DD bit */
            break;
        dma_rmb();

        pktlen = ls & DESC_LEN_MASK;

        dma_unmap_page(&p->pdev->dev, buf->dma, PAGE_SIZE, DMA_FROM_DEVICE);

        skb = build_skb(page_address(buf->page), PAGE_SIZE);
        if (likely(skb)) {
            skb_reserve(skb, NET_SKB_PAD);
            skb_put(skb, pktlen);
            skb->protocol = eth_type_trans(skb, p->netdev);
            p->stats.rx_packets++;
            p->stats.rx_bytes += pktlen;
            napi_gro_receive(&p->napi, skb);
        } else {
            __free_page(buf->page);
            p->stats.rx_dropped++;
        }
        buf->page = NULL;

        /* Refill */
        if (mynic_alloc_rx_buf(p, idx) == 0) {
            wmb();
            mynic_wr32(p, REG_RX_TAIL, idx);
            p->rx_tail = idx;
        }

        head++;
        work++;
    }
    p->rx_head = head;
    return work;
}

/* ─── TX ─────────────────────────────────────────────────── */

static int mynic_setup_tx_ring(struct mynic_priv *p)
{
    p->tx_ring = dma_alloc_coherent(&p->pdev->dev,
                     TX_RING_SIZE * sizeof(struct mynic_desc),
                     &p->tx_ring_dma, GFP_KERNEL);
    if (!p->tx_ring) return -ENOMEM;

    mynic_wr32(p, REG_TX_RING_LO, lower_32_bits(p->tx_ring_dma));
    mynic_wr32(p, REG_TX_RING_HI, upper_32_bits(p->tx_ring_dma));

    p->tx_head = 0;
    p->tx_tail = 0;
    spin_lock_init(&p->tx_lock);
    return 0;
}

static void mynic_clean_tx(struct mynic_priv *p)
{
    u32 head = p->tx_head;
    u32 hw_head = mynic_rd32(p, REG_TX_HEAD);

    while (head != hw_head) {
        u32 idx = head % TX_RING_SIZE;
        struct mynic_tx_buf *buf = &p->tx_bufs[idx];

        if (buf->dma) {
            if (buf->mapped_page)
                dma_unmap_page(&p->pdev->dev, buf->dma, buf->len, DMA_TO_DEVICE);
            else
                dma_unmap_single(&p->pdev->dev, buf->dma, buf->len, DMA_TO_DEVICE);
            buf->dma = 0;
        }
        if (buf->skb) {
            dev_consume_skb_irq(buf->skb);
            buf->skb = NULL;
            p->stats.tx_packets++;
        }
        head++;
    }
    p->tx_head = head;

    if (netif_queue_stopped(p->netdev) &&
        TX_RING_SIZE - (p->tx_tail - p->tx_head) > TX_STOP_THRESH) {
        netif_wake_queue(p->netdev);
    }
}

static netdev_tx_t mynic_xmit(struct sk_buff *skb, struct net_device *netdev)
{
    struct mynic_priv *p = netdev_priv(netdev);
    unsigned long flags;
    u32 tail, eop_idx;
    int nr_frags = skb_shinfo(skb)->nr_frags;
    int needed   = 1 + nr_frags;
    int i;

    spin_lock_irqsave(&p->tx_lock, flags);

    if (TX_RING_SIZE - (p->tx_tail - p->tx_head) <= needed + 1) {
        netif_stop_queue(netdev);
        spin_unlock_irqrestore(&p->tx_lock, flags);
        return NETDEV_TX_BUSY;
    }

    tail = p->tx_tail;

    /* Linear data */
    if (skb_headlen(skb)) {
        u32 idx = tail % TX_RING_SIZE;
        dma_addr_t dma = dma_map_single(&p->pdev->dev, skb->data,
                                         skb_headlen(skb), DMA_TO_DEVICE);
        p->tx_ring[idx].addr       = cpu_to_le64(dma);
        p->tx_ring[idx].len_status = cpu_to_le32(skb_headlen(skb));
        p->tx_bufs[idx].dma        = dma;
        p->tx_bufs[idx].len        = skb_headlen(skb);
        p->tx_bufs[idx].skb        = NULL;
        p->tx_bufs[idx].mapped_page = false;
        tail++;
    }

    /* Fragments */
    for (i = 0; i < nr_frags; i++) {
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
        u32 idx = tail % TX_RING_SIZE;
        dma_addr_t dma = skb_frag_dma_map(&p->pdev->dev, frag, 0,
                                            skb_frag_size(frag), DMA_TO_DEVICE);
        p->tx_ring[idx].addr       = cpu_to_le64(dma);
        p->tx_ring[idx].len_status = cpu_to_le32(skb_frag_size(frag));
        p->tx_bufs[idx].dma        = dma;
        p->tx_bufs[idx].len        = skb_frag_size(frag);
        p->tx_bufs[idx].skb        = NULL;
        p->tx_bufs[idx].mapped_page = true;
        tail++;
    }

    /* Mark EOP on last descriptor, attach skb for cleanup */
    eop_idx = (tail - 1) % TX_RING_SIZE;
    p->tx_ring[eop_idx].len_status |= cpu_to_le32(BIT(DESC_STATUS_SHIFT + 1)); /* EOP */
    p->tx_bufs[eop_idx].skb         = skb;

    wmb();
    p->tx_tail = tail;
    mynic_wr32(p, REG_TX_TAIL, (tail - 1) % TX_RING_SIZE);
    p->stats.tx_bytes += skb->len;

    if (TX_RING_SIZE - (p->tx_tail - p->tx_head) <= TX_STOP_THRESH)
        netif_stop_queue(netdev);

    spin_unlock_irqrestore(&p->tx_lock, flags);
    return NETDEV_TX_OK;
}

/* ─── NAPI + Interrupt ───────────────────────────────────── */

static int mynic_poll(struct napi_struct *napi, int budget)
{
    struct mynic_priv *p = container_of(napi, struct mynic_priv, napi);
    int work;

    mynic_clean_tx(p);
    work = mynic_clean_rx(p, budget);

    if (work < budget) {
        napi_complete_done(napi, work);
        mynic_wr32(p, REG_IRQ_MASK, IRQ_ALL);  /* Re-enable all IRQs */
    }
    return work;
}

static irqreturn_t mynic_interrupt(int irq, void *data)
{
    struct mynic_priv *p = data;
    u32 status;

    status = mynic_rd32(p, REG_IRQ_STATUS);
    if (!status) return IRQ_NONE;

    /* Clear the interrupt */
    mynic_wr32(p, REG_IRQ_STATUS, status);

    if (status & (IRQ_RX_DONE | IRQ_TX_DONE)) {
        /* Disable interrupts and hand off to NAPI */
        mynic_wr32(p, REG_IRQ_MASK, 0);
        napi_schedule(&p->napi);
    }

    if (status & IRQ_LINK_CHANGE) {
        /* Handle link state change */
        schedule_work(&p->link_work);
    }

    return IRQ_HANDLED;
}

/* ─── net_device_ops ─────────────────────────────────────── */

static int mynic_open(struct net_device *netdev)
{
    struct mynic_priv *p = netdev_priv(netdev);
    int ret;

    ret = mynic_setup_rx_ring(p);
    if (ret) return ret;

    ret = mynic_setup_tx_ring(p);
    if (ret) goto err_rx;

    ret = request_irq(p->pdev->irq, mynic_interrupt,
                      IRQF_SHARED, DRIVER_NAME, p);
    if (ret) goto err_tx;

    napi_enable(&p->napi);
    mynic_wr32(p, REG_CTRL, BIT(0));   /* Enable RX/TX */
    mynic_wr32(p, REG_IRQ_MASK, IRQ_ALL);
    netif_start_queue(netdev);
    return 0;

err_tx:
    /* teardown tx ring */
err_rx:
    mynic_free_rx_bufs(p);
    return ret;
}

static int mynic_stop(struct net_device *netdev)
{
    struct mynic_priv *p = netdev_priv(netdev);

    netif_stop_queue(netdev);
    mynic_wr32(p, REG_IRQ_MASK, 0);
    napi_disable(&p->napi);
    free_irq(p->pdev->irq, p);
    mynic_wr32(p, REG_CTRL, 0);
    mynic_free_rx_bufs(p);
    dma_free_coherent(&p->pdev->dev,
                      RX_RING_SIZE * sizeof(struct mynic_desc),
                      p->rx_ring, p->rx_ring_dma);
    dma_free_coherent(&p->pdev->dev,
                      TX_RING_SIZE * sizeof(struct mynic_desc),
                      p->tx_ring, p->tx_ring_dma);
    return 0;
}

static struct net_device_stats *mynic_get_stats(struct net_device *netdev)
{
    return &((struct mynic_priv *)netdev_priv(netdev))->stats;
}

static const struct net_device_ops mynic_netdev_ops = {
    .ndo_open       = mynic_open,
    .ndo_stop       = mynic_stop,
    .ndo_start_xmit = mynic_xmit,
    .ndo_get_stats  = mynic_get_stats,
};

/* ─── PCI Probe / Remove ─────────────────────────────────── */

static int mynic_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct net_device *netdev;
    struct mynic_priv *p;
    int ret;

    ret = pci_enable_device(pdev);
    if (ret) return ret;

    ret = pci_request_regions(pdev, DRIVER_NAME);
    if (ret) goto err_pci;

    pci_set_master(pdev);  /* Enable bus mastering DMA */

    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (ret) {
        ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        if (ret) goto err_regions;
    }

    netdev = alloc_etherdev(sizeof(struct mynic_priv));
    if (!netdev) { ret = -ENOMEM; goto err_regions; }

    SET_NETDEV_DEV(netdev, &pdev->dev);
    pci_set_drvdata(pdev, netdev);

    p         = netdev_priv(netdev);
    p->pdev   = pdev;
    p->netdev = netdev;

    p->base = pci_iomap(pdev, 0, 0);  /* Map BAR 0 */
    if (!p->base) { ret = -EIO; goto err_netdev; }

    /* Read MAC address from hardware */
    {
        u32 lo = mynic_rd32(p, REG_MAC_ADDR_LO);
        u32 hi = mynic_rd32(p, REG_MAC_ADDR_HI);
        netdev->dev_addr[0] = (lo >>  0) & 0xFF;
        netdev->dev_addr[1] = (lo >>  8) & 0xFF;
        netdev->dev_addr[2] = (lo >> 16) & 0xFF;
        netdev->dev_addr[3] = (lo >> 24) & 0xFF;
        netdev->dev_addr[4] = (hi >>  0) & 0xFF;
        netdev->dev_addr[5] = (hi >>  8) & 0xFF;
    }

    netdev->netdev_ops = &mynic_netdev_ops;
    netdev->mtu        = ETH_DATA_LEN;
    netdev->features   = NETIF_F_SG | NETIF_F_IP_CSUM | NETIF_F_RXCSUM;

    netif_napi_add(netdev, &p->napi, mynic_poll, NAPI_POLL_WEIGHT);

    ret = register_netdev(netdev);
    if (ret) goto err_napi;

    dev_info(&pdev->dev, "mynic: registered as %s\n", netdev->name);
    return 0;

err_napi:
    netif_napi_del(&p->napi);
    pci_iounmap(pdev, p->base);
err_netdev:
    free_netdev(netdev);
err_regions:
    pci_release_regions(pdev);
err_pci:
    pci_disable_device(pdev);
    return ret;
}

static void mynic_remove(struct pci_dev *pdev)
{
    struct net_device *netdev = pci_get_drvdata(pdev);
    struct mynic_priv *p      = netdev_priv(netdev);

    unregister_netdev(netdev);
    netif_napi_del(&p->napi);
    pci_iounmap(pdev, p->base);
    free_netdev(netdev);
    pci_release_regions(pdev);
    pci_disable_device(pdev);
}

static const struct pci_device_id mynic_ids[] = {
    { PCI_DEVICE(MYNIC_VENDOR_ID, MYNIC_DEVICE_ID) },
    { 0 }
};
MODULE_DEVICE_TABLE(pci, mynic_ids);

static struct pci_driver mynic_driver = {
    .name     = DRIVER_NAME,
    .id_table = mynic_ids,
    .probe    = mynic_probe,
    .remove   = mynic_remove,
};

module_pci_driver(mynic_driver);

MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Minimal NIC Driver with Ring Buffer Management");
MODULE_LICENSE("GPL");
MODULE_VERSION(DRIVER_VERSION);
```

---

## 16. Rust Implementation in the Kernel

### 16.1 Rust in the Linux Kernel

Rust support was merged into the Linux kernel starting with version 6.1. The `rust/` directory contains the core Rust infrastructure, and drivers can be written in `drivers/` using Rust. Rust kernel code:

- Has no standard library (`no_std`)
- Uses the kernel's own allocator
- Uses safe abstractions over unsafe kernel C APIs
- Provides compile-time guarantees against data races and use-after-free bugs

The key modules for networking drivers:

```
rust/kernel/
├── net.rs           (networking types)
├── net/dev.rs       (net_device wrappers)
├── dma.rs           (DMA allocations)
├── error.rs         (kernel error types)
├── sync/            (spinlocks, mutexes)
└── types.rs         (ScopeGuard, etc.)
```

### 16.2 Rust Ring Buffer Implementation

```rust
// SPDX-License-Identifier: GPL-2.0
//! Ring buffer implementation for a NIC driver in Rust.
//!
//! This module provides a type-safe ring buffer that wraps the
//! kernel's DMA coherent allocation API.

use kernel::{
    dma::{CoherentAlloc, DmaDev},
    error::{code::*, Result},
    io_mem::IoMem,
    prelude::*,
    sync::SpinLock,
    types::ARef,
};
use core::{
    mem,
    num::NonZeroU32,
    sync::atomic::{AtomicU32, Ordering},
};

/// A single descriptor in the hardware ring.
///
/// Must be `repr(C)` to match the hardware ABI, and `repr(packed)` if the
/// hardware requires densely packed fields without alignment padding.
#[repr(C)]
pub struct HwDesc {
    /// Physical address of the data buffer.
    pub addr: u64,
    /// Packet length (lower 16 bits) and status flags (upper 16 bits).
    pub len_status: u32,
    /// Checksum and VLAN metadata.
    pub meta: u32,
}

/// Status bit definitions matching hardware.
pub mod status {
    pub const DD:  u32 = 1 << 16;  // Descriptor Done
    pub const EOP: u32 = 1 << 17;  // End Of Packet
    pub const ERR: u32 = 1 << 18;  // Error
}

/// Per-descriptor software state for RX.
pub struct RxBuffer {
    /// The page backing this descriptor slot.
    page: Option<Box<PageBuffer>>,
    /// DMA address of the page.
    dma_addr: u64,
}

/// A page of memory mapped for DMA receive.
pub struct PageBuffer {
    /// Raw page pointer (obtained from kernel page allocator).
    page: *mut kernel::bindings::page,
}

// SAFETY: PageBuffer contains only a raw pointer to kernel memory,
// which is safe to send between threads.
unsafe impl Send for PageBuffer {}
unsafe impl Sync for PageBuffer {}

impl PageBuffer {
    fn alloc() -> Result<Self> {
        // SAFETY: GFP_ATOMIC is valid for allocation in atomic contexts.
        let page = unsafe {
            kernel::bindings::__alloc_page(kernel::bindings::GFP_ATOMIC)
        };
        if page.is_null() {
            return Err(ENOMEM);
        }
        Ok(PageBuffer { page })
    }

    fn as_ptr(&self) -> *mut u8 {
        // SAFETY: page is non-null (checked in alloc).
        unsafe { kernel::bindings::page_address(self.page) as *mut u8 }
    }
}

impl Drop for PageBuffer {
    fn drop(&mut self) {
        // SAFETY: page was allocated by __alloc_page and is non-null.
        unsafe { kernel::bindings::__free_page(self.page) };
    }
}

/// The ring buffer, parameterized by the number of entries N.
///
/// N must be a power of two. This is enforced at construction time.
pub struct RingBuffer<const N: usize> {
    /// Descriptor array in coherent DMA memory.
    descs: CoherentAlloc<[HwDesc; N]>,
    /// Software state per descriptor slot.
    sw_state: Box<[RxBuffer; N]>,
    /// Consumer index (CPU reads from here). Monotonically increasing.
    head: u32,
    /// Producer index (NIC writes up to here). Monotonically increasing.
    tail: u32,
}

impl<const N: usize> RingBuffer<N> {
    /// Mask to wrap indices modulo N (requires N to be a power of two).
    const MASK: usize = N - 1;

    /// Construct a new ring buffer.
    ///
    /// # Errors
    /// Returns `EINVAL` if N is not a power of two.
    /// Returns `ENOMEM` if DMA or page allocation fails.
    pub fn new(dma_dev: &DmaDev) -> Result<Self> {
        // Enforce power-of-two constraint at runtime.
        if !N.is_power_of_two() {
            return Err(EINVAL);
        }

        // Allocate descriptor ring as coherent DMA memory.
        // `CoherentAlloc` provides a safe wrapper around
        // `dma_alloc_coherent` / `dma_free_coherent`.
        let descs = CoherentAlloc::new(
            dma_dev,
            // SAFETY: HwDesc is repr(C), all-zeros is a valid initial state.
            unsafe { core::mem::zeroed() },
            kernel::dma::Direction::FromDevice,
        )?;

        // Allocate page buffers for each descriptor slot.
        // This is a `Box<[RxBuffer; N]>` which heap-allocates an array.
        let sw_state = {
            let mut v: Vec<RxBuffer> = Vec::try_with_capacity(N)?;
            for _ in 0..N {
                v.try_push(RxBuffer { page: None, dma_addr: 0 })?;
            }
            v.try_into_boxed_slice()?.try_into().map_err(|_| EINVAL)?
        };

        let mut rb = RingBuffer {
            descs,
            sw_state,
            head: 0,
            tail: 0,
        };

        // Pre-allocate a page for every descriptor.
        for i in 0..N {
            rb.alloc_slot(dma_dev, i)?;
        }

        Ok(rb)
    }

    /// Allocate a page for descriptor slot `idx` and write its DMA
    /// address into the hardware descriptor.
    fn alloc_slot(&mut self, dma_dev: &DmaDev, idx: usize) -> Result<()> {
        let page = PageBuffer::alloc()?;

        // Map the page for DMA receive.
        // On non-coherent architectures this performs cache invalidation.
        let dma_addr = dma_dev.map_page(
            page.page,
            0,
            kernel::PAGE_SIZE,
            kernel::dma::Direction::FromDevice,
        )?;

        // Write the DMA address into the hardware descriptor.
        // The descriptor array is in coherent memory, so no explicit
        // cache flush is needed after writing.
        {
            // SAFETY: descs is valid coherent DMA memory; idx < N.
            let desc = unsafe { &mut (*self.descs.cpu_addr())[idx] };
            // Use volatile write to prevent the compiler from eliding
            // or reordering the store to coherent DMA memory.
            unsafe {
                core::ptr::write_volatile(&mut desc.addr as *mut u64, dma_addr);
                core::ptr::write_volatile(&mut desc.len_status as *mut u32, 0);
            }
        }

        self.sw_state[idx] = RxBuffer { page: Some(Box::new(page)), dma_addr };
        Ok(())
    }

    /// The number of descriptors available to consume (DD bit set).
    #[inline]
    pub fn available(&self) -> u32 {
        self.tail.wrapping_sub(self.head)
    }

    /// Check whether the descriptor at `head` has been completed by the NIC.
    ///
    /// Uses a read barrier to ensure we read the DD bit before reading
    /// the rest of the descriptor's fields.
    pub fn peek_dd(&self) -> bool {
        let idx = (self.head as usize) & Self::MASK;
        // SAFETY: descs is valid; idx is in range.
        let len_status = unsafe {
            core::ptr::read_volatile(
                &(*self.descs.cpu_addr())[idx].len_status as *const u32
            )
        };
        // Architecture read barrier — ensures DD is read before len/meta.
        // SAFETY: sound FFI call to smp_rmb() barrier.
        unsafe { kernel::bindings::smp_rmb() };
        (len_status & status::DD) != 0
    }

    /// Consume the descriptor at `head`. Returns the packet length and
    /// takes ownership of the backing `PageBuffer` for zero-copy handoff.
    ///
    /// # Panics
    /// Panics in debug mode if the DD bit is not set.
    pub fn consume(&mut self, dma_dev: &DmaDev) -> Option<(u32, Box<PageBuffer>)> {
        if !self.peek_dd() {
            return None;
        }

        let idx = (self.head as usize) & Self::MASK;

        // Read the completed descriptor.
        let (pkt_len, _meta) = {
            // SAFETY: descs is valid; idx is in range.
            let desc = unsafe { &(*self.descs.cpu_addr())[idx] };
            let ls   = unsafe { core::ptr::read_volatile(&desc.len_status as *const u32) };
            let meta = unsafe { core::ptr::read_volatile(&desc.meta as *const u32) };
            (ls & 0xFFFF, meta)
        };

        // Unmap before CPU reads packet data.
        let buf = &mut self.sw_state[idx];
        dma_dev.unmap_page(buf.dma_addr, kernel::PAGE_SIZE,
                           kernel::dma::Direction::FromDevice);
        buf.dma_addr = 0;

        // Take ownership of the page — caller receives it.
        let page = buf.page.take().expect("slot must have a page on consume");

        self.head = self.head.wrapping_add(1);
        Some((pkt_len, page))
    }

    /// Refill the descriptor at the old `head` position (now available
    /// for reuse). Returns the new tail value to write to the NIC's
    /// tail register.
    pub fn refill(&mut self, dma_dev: &DmaDev) -> Result<u32> {
        // The slot just consumed is at (head - 1) % N.
        let idx = ((self.head.wrapping_sub(1)) as usize) & Self::MASK;
        self.alloc_slot(dma_dev, idx)?;

        // Write barrier: ensure descriptor is written before advancing tail.
        // SAFETY: sound FFI call.
        unsafe { kernel::bindings::dma_wmb() };

        self.tail = self.tail.wrapping_add(1);
        Ok((self.tail as usize & Self::MASK) as u32)
    }

    /// DMA address of the descriptor ring (for programming into hardware).
    pub fn dma_addr(&self) -> u64 {
        self.descs.dma_addr()
    }
}

/// A thread-safe TX ring using a spinlock.
pub struct TxRing<const N: usize> {
    inner: SpinLock<TxRingInner<N>>,
}

struct TxRingInner<const N: usize> {
    descs:    CoherentAlloc<[HwDesc; N]>,
    sw_state: Box<[TxSlot; N]>,
    head: u32,
    tail: u32,
}

struct TxSlot {
    // skb reference will be held via ARef<SkBuff> when kernel bindings
    // expose it; for now use a raw pointer.
    skb:      Option<*mut kernel::bindings::sk_buff>,
    dma_addr: u64,
    len:      u32,
    is_eop:   bool,
}

// SAFETY: TxSlot contains a raw pointer which we manage manually.
unsafe impl Send for TxSlot {}

impl<const N: usize> TxRing<N> {
    const MASK: usize = N - 1;

    pub fn new(dma_dev: &DmaDev) -> Result<Self> {
        if !N.is_power_of_two() { return Err(EINVAL); }
        let descs = CoherentAlloc::new(
            dma_dev,
            unsafe { core::mem::zeroed() },
            kernel::dma::Direction::ToDevice,
        )?;
        let sw_state = {
            let mut v: Vec<TxSlot> = Vec::try_with_capacity(N)?;
            for _ in 0..N {
                v.try_push(TxSlot { skb: None, dma_addr: 0, len: 0, is_eop: false })?;
            }
            v.try_into_boxed_slice()?.try_into().map_err(|_| EINVAL)?
        };
        Ok(TxRing {
            inner: SpinLock::new(TxRingInner { descs, sw_state, head: 0, tail: 0 }),
        })
    }

    /// Number of free descriptor slots.
    pub fn available(&self) -> u32 {
        let g = self.inner.lock();
        N as u32 - g.tail.wrapping_sub(g.head) - 1
    }

    /// Enqueue a transmit buffer. Returns the new tail index to ring the doorbell.
    ///
    /// # Safety
    /// `data_ptr` must remain valid until `complete()` returns this slot.
    pub unsafe fn enqueue(
        &self,
        dma_dev: &DmaDev,
        data_ptr: *const u8,
        len: u32,
        is_eop: bool,
        skb: *mut kernel::bindings::sk_buff,
    ) -> Result<u32> {
        let mut g = self.inner.lock();

        if N as u32 - g.tail.wrapping_sub(g.head) <= 1 {
            return Err(ENOSPC);
        }

        let idx = (g.tail as usize) & Self::MASK;

        let dma_addr = dma_dev.map_single(
            data_ptr as *mut u8,
            len as usize,
            kernel::dma::Direction::ToDevice,
        )?;

        unsafe {
            let desc = &mut (*g.descs.cpu_addr())[idx];
            core::ptr::write_volatile(&mut desc.addr as *mut u64, dma_addr);
            let mut ls = len as u32;
            if is_eop { ls |= status::EOP; }
            core::ptr::write_volatile(&mut desc.len_status as *mut u32, ls);
        }

        g.sw_state[idx] = TxSlot {
            skb: if is_eop { Some(skb) } else { None },
            dma_addr,
            len,
            is_eop,
        };

        g.tail = g.tail.wrapping_add(1);
        let new_tail = (g.tail as usize & Self::MASK) as u32;
        Ok(new_tail)
    }

    /// Process TX completions up to the hardware-reported head.
    pub fn complete(&self, dma_dev: &DmaDev, hw_head: u32) {
        let mut g = self.inner.lock();

        while g.head != hw_head {
            let idx = (g.head as usize) & Self::MASK;
            let slot = &mut g.sw_state[idx];

            if slot.dma_addr != 0 {
                dma_dev.unmap_single(slot.dma_addr, slot.len as usize,
                                     kernel::dma::Direction::ToDevice);
                slot.dma_addr = 0;
            }

            if let Some(skb) = slot.skb.take() {
                // SAFETY: skb was given to us by the kernel's xmit path
                // and we are responsible for freeing it on completion.
                unsafe { kernel::bindings::dev_consume_skb_any(skb) };
            }

            g.head = g.head.wrapping_add(1);
        }
    }
}
```

### 16.3 Rust Driver Registration

```rust
// mynic_rust.rs — Driver entry point

use kernel::{
    module_pci_driver, pci,
    net::Device as NetDevice,
    prelude::*,
};

struct MyNicDriver;

impl kernel::Module for MyNicDriver {
    fn init(_name: &'static CStr, _module: &'static ThisModule) -> Result<Self> {
        pr_info!("mynic_rust: loaded\n");
        Ok(MyNicDriver)
    }
}

struct MyNicDevice {
    // Device-specific state
    ring: RingBuffer<256>,
    tx_ring: TxRing<256>,
}

#[vtable]
impl pci::Driver for MyNicDriver {
    type Data = Box<MyNicDevice>;

    fn probe(pdev: &mut pci::Device, id: core::option::Option<&Self::IdInfo>)
        -> Result<Self::Data>
    {
        pdev.enable_device()?;
        pdev.request_selected_regions(pci::BAR_0, c_str!("mynic"))?;
        pdev.set_master();

        let dma_dev = pdev.as_ref();
        dma_dev.set_dma_mask(kernel::dma::Mask::Bit64)?;

        let ring    = RingBuffer::<256>::new(dma_dev)?;
        let tx_ring = TxRing::<256>::new(dma_dev)?;

        // Register net_device ...

        Ok(Box::try_new(MyNicDevice { ring, tx_ring })?)
    }

    fn remove(data: &Self::Data) {
        pr_info!("mynic_rust: removing device\n");
        // Cleanup happens automatically when Box<MyNicDevice> is dropped.
        // The Drop impl for RingBuffer and TxRing will free coherent DMA
        // memory and unmap all buffers.
    }
}

// SAFETY: MyNicDriver is a ZST and satisfies the module requirements.
module_pci_driver! {
    type: MyNicDriver,
    name: "mynic_rust",
    author: "Your Name",
    description: "Rust NIC driver with ring buffer",
    license: "GPL",
}
```

---

## 17. Performance Tuning and Observability

### 17.1 Ring Buffer Size Tuning

```bash
# View current ring buffer sizes
ethtool -g eth0
# Output:
# Ring parameters for eth0:
# Pre-set maximums:
# RX:     4096
# TX:     4096
# Current hardware settings:
# RX:     512
# TX:     512

# Increase ring size (reduces drops under burst traffic)
ethtool -G eth0 rx 4096 tx 4096

# Read current counters (drops, errors)
ethtool -S eth0 | grep -i "drop\|miss\|error"
```

### 17.2 Key Kernel Tuning Parameters

```bash
# Network core receive buffer
# netdev_max_backlog: max packets queued in the input_pkt_queue
# when the interface receives packets faster than the kernel can process
sysctl -w net.core.netdev_max_backlog=300000

# Maximum number of packets taken from all interfaces in one polling cycle
sysctl -w net.core.netdev_budget=600

# Budget in microseconds (hard time limit per softirq round)
sysctl -w net.core.netdev_budget_usecs=8000

# Socket receive/send buffer sizes
sysctl -w net.core.rmem_max=134217728    # 128 MB max socket recv buffer
sysctl -w net.core.wmem_max=134217728    # 128 MB max socket send buffer
sysctl -w net.core.rmem_default=262144   # 256 KB default
sysctl -w net.core.wmem_default=262144

# TCP buffer auto-tuning
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Enable TCP receive buffer auto-tuning
sysctl -w net.ipv4.tcp_moderate_rcvbuf=1

# Busy poll / low-latency networking
# Polling time in microseconds for socket recv (reduces interrupt latency)
sysctl -w net.core.busy_poll=50
sysctl -w net.core.busy_read=50
```

### 17.3 CPU Isolation for Networking

```bash
# Isolate CPUs 4-7 from the scheduler (dedicated to NIC polling)
# Add to kernel command line:
# isolcpus=4-7 nohz_full=4-7 rcu_nocbs=4-7

# Set NIC IRQ affinity to CPU 4
for irq in $(grep eth0 /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    echo 10 > /proc/irq/$irq/smp_affinity  # CPU 4 = bit 4 = 0x10
done

# Run application on same CPU for cache locality
taskset -c 4 ./my_network_app

# NUMA topology awareness
numactl --cpunodebind=0 --membind=0 ./my_network_app
```

### 17.4 GRO, GSO, and TSO

```bash
# View offload features
ethtool -k eth0

# TSO (TCP Segmentation Offload) — NIC segments large TCP writes
ethtool -K eth0 tso on

# GRO (Generic Receive Offload) — software coalescing on RX
ethtool -K eth0 gro on

# LRO (Large Receive Offload) — hardware coalescing on RX (deprecated by GRO)
ethtool -K eth0 lro off  # Usually disable in favor of GRO

# GSO (Generic Segmentation Offload) — software segmentation on TX
# (fallback when TSO is unavailable)
ethtool -K eth0 gso on

# Checksum offloading
ethtool -K eth0 tx-checksum-ip-generic on  # TX checksum offload
ethtool -K eth0 rx-checksum on             # RX checksum verification
```

### 17.5 Performance Counters and Statistics

```bash
# Per-NIC driver statistics (vendor-specific)
ethtool -S eth0

# Kernel network device statistics
cat /proc/net/dev

# Detailed per-CPU softirq statistics
cat /proc/softirqs

# Detailed per-CPU interrupt statistics
cat /proc/interrupts

# NAPI polling statistics
cat /sys/class/net/eth0/statistics/rx_dropped
cat /sys/class/net/eth0/statistics/rx_errors

# View dropped packets breakdown
ip -s link show eth0
```

---

## 18. Debugging, Tracing, and BPF

### 18.1 `perf` for Network Performance Analysis

```bash
# Trace network softirq events
perf stat -e 'net:*' sleep 1

# Count sk_buff allocations
perf stat -e 'kmem:kmalloc,kmem:kfree' -p $(pgrep ksoftirqd) sleep 5

# Profile NAPI poll function
perf record -g -e cpu-clock -p $(pgrep ksoftirqd/0) sleep 10
perf report

# Trace XDP events
perf record -e 'xdp:*' -a sleep 1
perf script
```

### 18.2 `ftrace` / `tracefs`

```bash
# Trace all network receive events
echo 1 > /sys/kernel/debug/tracing/events/net/enable
echo 1 > /sys/kernel/debug/tracing/tracing_on
sleep 1
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace | head -100

# Trace a specific function
echo 'netif_receive_skb' > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Function graph tracing (shows call tree with timing)
echo 'napi_gro_receive' > /sys/kernel/debug/tracing/set_graph_function
echo function_graph > /sys/kernel/debug/tracing/current_tracer
```

### 18.3 BPF Tracing Programs

```c
/* trace_rx_latency.bpf.c — Measure time from IRQ to netif_receive_skb */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
    __uint(type,        BPF_MAP_TYPE_HASH);
    __type(key,         u64);   /* IRQ timestamp */
    __type(value,       u64);   /* IRQ entry time */
    __uint(max_entries, 10240);
} irq_start SEC(".maps");

struct {
    __uint(type,        BPF_MAP_TYPE_HISTOGRAM);
    __uint(max_entries, 1);
} latency_hist SEC(".maps");

/* Kprobe on the NIC's interrupt handler */
SEC("kprobe/my_nic_interrupt")
int trace_irq_enter(struct pt_regs *ctx)
{
    u64 cpu = bpf_get_smp_processor_id();
    u64 ts  = bpf_ktime_get_ns();
    bpf_map_update_elem(&irq_start, &cpu, &ts, BPF_ANY);
    return 0;
}

/* Kprobe on netif_receive_skb — packet delivered to stack */
SEC("kprobe/netif_receive_skb")
int trace_rx_done(struct pt_regs *ctx)
{
    u64 cpu = bpf_get_smp_processor_id();
    u64 *ts = bpf_map_lookup_elem(&irq_start, &cpu);
    if (!ts) return 0;

    u64 delta_ns = bpf_ktime_get_ns() - *ts;
    bpf_map_delete_elem(&irq_start, &cpu);

    /* Record latency in histogram */
    u64 slot = delta_ns / 1000;  /* Convert to microseconds */
    if (slot > 99) slot = 99;
    bpf_map_update_elem(&latency_hist, &slot, &(u64){1}, BPF_ANY);

    if (delta_ns > 100000)  /* > 100µs */
        bpf_printk("High RX latency: %llu ns on CPU %llu\n", delta_ns, cpu);

    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 18.4 `dropwatch` and `devlink`

```bash
# Monitor packet drops in real time (uses kfree_skb tracepoints)
dropwatch -l kas

# devlink health reporters (for hardware errors)
devlink health show dev pci/0000:01:00.0

# devlink port statistics
devlink port show
```

### 18.5 Kernel Dynamic Debug

```bash
# Enable dynamic debug prints in a specific driver
echo 'module mynic +p' > /sys/kernel/debug/dynamic_debug/control

# Enable all network-related debug
echo 'file net/core/dev.c +p' > /sys/kernel/debug/dynamic_debug/control

# View current debug flags
cat /sys/kernel/debug/dynamic_debug/control | grep mynic
```

---

## 19. Advanced Topics: Comparison with DPDK and RDMA

### 19.1 DPDK (Data Plane Development Kit)

DPDK takes a fundamentally different approach from the Linux kernel: it runs entirely in user space, completely bypassing the kernel network stack using UIO (Userspace I/O) or VFIO (Virtual Function I/O).

**DPDK ring buffer design** (`rte_ring`):
- Lock-free MPMC (multi-producer, multi-consumer) using CAS (Compare-And-Swap)
- Hugepages for TLB efficiency
- Per-core packet processing with CPU pinning
- No context switches, no system calls on the data path

```c
/* DPDK ring API (user-space, not kernel) */
#include <rte_ring.h>
#include <rte_mbuf.h>

/* Create a ring of 1024 mbufs */
struct rte_ring *ring = rte_ring_create("my_ring", 1024,
                                         rte_socket_id(),
                                         RING_F_SP_ENQ | RING_F_SC_DEQ);

/* Burst enqueue */
struct rte_mbuf *mbufs[32];
unsigned int enqueued = rte_ring_sp_enqueue_burst(ring,
                                                    (void **)mbufs, 32, NULL);

/* Burst dequeue */
unsigned int dequeued = rte_ring_sc_dequeue_burst(ring,
                                                    (void **)mbufs, 32, NULL);
```

**Key differences from Linux kernel rings:**

| Aspect | Linux Kernel | DPDK |
|--------|-------------|------|
| Memory model | Kernel virtual memory | Hugepages, pinned physical |
| CPU usage | Interrupt + NAPI poll | Busy-poll (100% CPU) |
| Context switches | Occasional | None |
| Stack bypass | XDP/AF_XDP | Full bypass |
| Portability | Kernel ABI | Portable across OS |
| Throughput | ~20-40 Mpps (with XDP) | 80-100+ Mpps |
| Latency | ~5-50µs typical | ~1-5µs typical |
| Jitter | Higher (scheduler, IRQ) | Very low |

### 19.2 RDMA and RoCE Ring Buffers

RDMA (Remote Direct Memory Access) provides even more extreme zero-copy semantics: one machine can read or write another machine's memory without involving the remote CPU at all.

RDMA ring buffers (Work Queues) operate at the verb level:

- **SQ (Send Queue)**: Application posts WQEs (Work Queue Elements) to send data
- **RQ (Receive Queue)**: Application pre-posts receive buffers
- **CQ (Completion Queue)**: Hardware posts CQEs when operations complete

The kernel's `ib_verbs` API:

```c
#include <rdma/ib_verbs.h>

/* Create a Completion Queue */
struct ib_cq *cq = ib_create_cq(ibdev,
                                  my_cq_handler,  /* completion callback */
                                  NULL,           /* async event handler */
                                  NULL,           /* private data        */
                                  cq_entries,     /* max completions     */
                                  comp_vector);   /* IRQ affinity        */

/* Create a Queue Pair (send + receive queues) */
struct ib_qp_init_attr qp_attr = {
    .send_cq        = cq,
    .recv_cq        = cq,
    .cap = {
        .max_send_wr    = 128,  /* max outstanding send WRs */
        .max_recv_wr    = 128,
        .max_send_sge   = 4,    /* scatter-gather entries */
        .max_recv_sge   = 1,
    },
    .qp_type = IB_QPT_RC,      /* Reliable Connected */
};
struct ib_qp *qp = ib_create_qp(pd, &qp_attr);

/* Post a receive buffer */
struct ib_sge sge = {
    .addr   = dma_addr,
    .length = buf_len,
    .lkey   = mr->lkey,  /* memory region key */
};
struct ib_recv_wr rwr = {
    .wr_id      = (u64)my_buffer,
    .sg_list    = &sge,
    .num_sge    = 1,
};
struct ib_recv_wr *bad_rwr;
ib_post_recv(qp, &rwr, &bad_rwr);

/* Post a send operation */
struct ib_send_wr swr = {
    .wr_id       = my_id,
    .opcode      = IB_WR_SEND,
    .send_flags  = IB_SEND_SIGNALED,
    .sg_list     = &sge,
    .num_sge     = 1,
};
struct ib_send_wr *bad_swr;
ib_post_send(qp, &swr, &bad_swr);
```

---

## 20. Complete Working Examples

### 20.1 Monitor Ring Buffer Health with a BPF Program

```c
/* ringbuf_monitor.bpf.c — Monitor NIC ring buffer health */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

/* Track per-device statistics */
struct dev_stats {
    __u64 rx_dropped_ring_full;
    __u64 rx_oom;
    __u64 tx_queue_stopped;
    __u64 tx_queue_woken;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u64);         /* net_device pointer */
    __type(value, struct dev_stats);
    __uint(max_entries, 64);
} dev_stats_map SEC(".maps");

/* Trace when kfree_skb is called (packet dropped) */
SEC("tp/skb/kfree_skb")
int trace_kfree_skb(struct trace_event_raw_kfree_skb *ctx)
{
    struct sk_buff *skb = ctx->skbaddr;
    struct net_device *dev;

    /* Read the device pointer from the skb */
    bpf_probe_read_kernel(&dev, sizeof(dev), &skb->dev);
    if (!dev) return 0;

    __u64 key = (__u64)(uintptr_t)dev;
    struct dev_stats *stats = bpf_map_lookup_elem(&dev_stats_map, &key);
    if (!stats) {
        struct dev_stats new_stats = {};
        bpf_map_update_elem(&dev_stats_map, &key, &new_stats, BPF_NOEXIST);
        stats = bpf_map_lookup_elem(&dev_stats_map, &key);
        if (!stats) return 0;
    }

    __sync_fetch_and_add(&stats->rx_dropped_ring_full, 1);

    /* Print device name and drop reason */
    char name[16];
    bpf_probe_read_kernel_str(name, sizeof(name), dev->name);
    bpf_printk("kfree_skb on dev %s reason=%d\n", name, ctx->reason);

    return 0;
}

/* Trace TX queue stops */
SEC("kprobe/netif_stop_subqueue")
int trace_queue_stop(struct pt_regs *ctx)
{
    struct net_device *dev = (struct net_device *)PT_REGS_PARM1(ctx);
    __u64 key = (__u64)(uintptr_t)dev;

    struct dev_stats *stats = bpf_map_lookup_elem(&dev_stats_map, &key);
    if (stats)
        __sync_fetch_and_add(&stats->tx_queue_stopped, 1);

    return 0;
}

/* Trace TX queue wakes */
SEC("kprobe/netif_wake_subqueue")
int trace_queue_wake(struct pt_regs *ctx)
{
    struct net_device *dev = (struct net_device *)PT_REGS_PARM1(ctx);
    __u64 key = (__u64)(uintptr_t)dev;

    struct dev_stats *stats = bpf_map_lookup_elem(&dev_stats_map, &key);
    if (stats)
        __sync_fetch_and_add(&stats->tx_queue_woken, 1);

    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 20.2 User-Space Ring Buffer for IPC (Standalone C)

This demonstrates ring buffer principles without kernel complexity:

```c
/* spsc_ring.c — Lock-free single-producer single-consumer ring buffer */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdbool.h>
#include <stdatomic.h>

#define CACHE_LINE_SIZE  64
#define RING_CAPACITY    4096   /* Must be power of two */
#define RING_MASK        (RING_CAPACITY - 1)

typedef struct {
    char data[64];
    uint32_t len;
} Packet;

/*
 * SPSC Ring Buffer
 *
 * The producer writes to `tail` and the consumer reads from `head`.
 * Both are placed on separate cache lines to avoid false sharing:
 * false sharing occurs when two cores write to different variables
 * that happen to share a cache line, causing unnecessary cache
 * invalidation traffic.
 */
typedef struct {
    /* Producer side — only the producer writes tail */
    _Alignas(CACHE_LINE_SIZE)
    atomic_uint_fast64_t tail;
    char _pad0[CACHE_LINE_SIZE - sizeof(atomic_uint_fast64_t)];

    /* Consumer side — only the consumer writes head */
    _Alignas(CACHE_LINE_SIZE)
    atomic_uint_fast64_t head;
    char _pad1[CACHE_LINE_SIZE - sizeof(atomic_uint_fast64_t)];

    /* The ring itself — shared read-only access to slots */
    _Alignas(CACHE_LINE_SIZE)
    Packet ring[RING_CAPACITY];
} SPSCRing;

/*
 * spsc_try_push — Producer: attempt to enqueue a packet.
 *
 * Uses release ordering on the tail store so that all prior writes
 * to ring[slot] are visible to the consumer before it sees the
 * tail advance.
 *
 * Returns true on success, false if full.
 */
static bool spsc_try_push(SPSCRing *r, const Packet *pkt)
{
    /*
     * Load tail with relaxed ordering — only the producer writes tail,
     * so we don't need to synchronize with anyone else here.
     */
    uint64_t tail = atomic_load_explicit(&r->tail, memory_order_relaxed);

    /*
     * Load head with acquire ordering — we need to see the most recent
     * head value written by the consumer. Without acquire, the CPU might
     * read a stale head (from cache) and wrongly conclude the ring is full.
     */
    uint64_t head = atomic_load_explicit(&r->head, memory_order_acquire);

    if (tail - head >= RING_CAPACITY)
        return false;  /* Full */

    /* Write packet data to the ring slot */
    r->ring[tail & RING_MASK] = *pkt;

    /*
     * Store the new tail with release ordering. This ensures the packet
     * data write above is visible to the consumer before it sees tail
     * advance. The consumer will use acquire when loading tail, forming
     * a proper acquire-release synchronization pair.
     */
    atomic_store_explicit(&r->tail, tail + 1, memory_order_release);
    return true;
}

/*
 * spsc_try_pop — Consumer: attempt to dequeue a packet.
 *
 * Returns true on success, false if empty.
 */
static bool spsc_try_pop(SPSCRing *r, Packet *pkt)
{
    uint64_t head = atomic_load_explicit(&r->head, memory_order_relaxed);

    /*
     * Load tail with acquire. The acquire pairs with the release store
     * in spsc_try_push, ensuring we see the complete packet data.
     */
    uint64_t tail = atomic_load_explicit(&r->tail, memory_order_acquire);

    if (head == tail)
        return false;  /* Empty */

    /* Read packet data from the ring slot */
    *pkt = r->ring[head & RING_MASK];

    /*
     * Advance head with release so the producer sees the updated head
     * and knows this slot is now free.
     */
    atomic_store_explicit(&r->head, head + 1, memory_order_release);
    return true;
}

/* ─── Batch operations for higher throughput ─────────────── */

/*
 * spsc_push_batch — Push multiple packets in one pass.
 *
 * Returns number of packets pushed (may be < count if full).
 * Writes all packet data first, then advances tail once.
 * This is more efficient than calling spsc_try_push() in a loop.
 */
static uint32_t spsc_push_batch(SPSCRing *r, const Packet *pkts, uint32_t count)
{
    uint64_t tail  = atomic_load_explicit(&r->tail, memory_order_relaxed);
    uint64_t head  = atomic_load_explicit(&r->head, memory_order_acquire);
    uint64_t space = RING_CAPACITY - (tail - head);
    uint32_t n     = (uint32_t)(space < count ? space : count);

    for (uint32_t i = 0; i < n; i++)
        r->ring[(tail + i) & RING_MASK] = pkts[i];

    atomic_store_explicit(&r->tail, tail + n, memory_order_release);
    return n;
}

/*
 * spsc_pop_batch — Pop multiple packets in one pass.
 *
 * Returns number of packets popped.
 */
static uint32_t spsc_pop_batch(SPSCRing *r, Packet *pkts, uint32_t count)
{
    uint64_t head  = atomic_load_explicit(&r->head, memory_order_relaxed);
    uint64_t tail  = atomic_load_explicit(&r->tail, memory_order_acquire);
    uint64_t avail = tail - head;
    uint32_t n     = (uint32_t)(avail < count ? avail : count);

    for (uint32_t i = 0; i < n; i++)
        pkts[i] = r->ring[(head + i) & RING_MASK];

    atomic_store_explicit(&r->head, head + n, memory_order_release);
    return n;
}
```

### 20.3 Testing Ring Buffer Correctness

```c
/* ring_test.c — Test harness for SPSC ring buffer */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <time.h>

#define TEST_PACKETS  10000000UL

static SPSCRing g_ring;
static uint64_t g_producer_sum;
static uint64_t g_consumer_sum;

static void *producer_thread(void *arg)
{
    Packet pkt;
    uint64_t sum = 0;

    for (uint64_t i = 0; i < TEST_PACKETS; i++) {
        pkt.len = (uint32_t)i;
        memcpy(pkt.data, &i, sizeof(i));
        sum += i;

        /* Spin until we can push */
        while (!spsc_try_push(&g_ring, &pkt))
            __asm__ volatile("pause" ::: "memory");
    }

    g_producer_sum = sum;
    return NULL;
}

static void *consumer_thread(void *arg)
{
    Packet pkt;
    uint64_t sum = 0;
    uint64_t received = 0;

    while (received < TEST_PACKETS) {
        if (spsc_try_pop(&g_ring, &pkt)) {
            uint64_t val;
            memcpy(&val, pkt.data, sizeof(val));
            sum += val;
            received++;
        } else {
            __asm__ volatile("pause" ::: "memory");
        }
    }

    g_consumer_sum = sum;
    return NULL;
}

int main(void)
{
    pthread_t prod, cons;
    struct timespec start, end;

    printf("Testing SPSC ring buffer with %lu packets...\n", TEST_PACKETS);
    clock_gettime(CLOCK_MONOTONIC, &start);

    pthread_create(&prod, NULL, producer_thread, NULL);
    pthread_create(&cons, NULL, consumer_thread, NULL);
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    double mpps    = TEST_PACKETS / elapsed / 1e6;

    printf("Correctness: %s (sum match: %lu == %lu)\n",
           g_producer_sum == g_consumer_sum ? "PASS" : "FAIL",
           g_producer_sum, g_consumer_sum);
    printf("Performance: %.2f Mpps in %.3fs\n", mpps, elapsed);
    printf("Throughput:  %.2f Gbps @ 64B packets\n",
           mpps * 64 * 8 / 1000);

    return g_producer_sum == g_consumer_sum ? 0 : 1;
}
```

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **sk_buff (skb)** | Socket buffer — the kernel's universal packet representation |
| **DMA** | Direct Memory Access — hardware transfers data without CPU involvement |
| **NAPI** | New API — hybrid interrupt/poll mechanism for network receive |
| **GRO** | Generic Receive Offload — software coalescing of TCP segments |
| **GSO** | Generic Segmentation Offload — software segmentation on transmit |
| **TSO** | TCP Segmentation Offload — hardware segmentation |
| **XDP** | eXpress Data Path — BPF programs at the earliest RX point |
| **AF_XDP** | Address Family XDP — zero-copy user-space socket type |
| **RSS** | Receive Side Scaling — hardware flow-based queue distribution |
| **RPS** | Receive Packet Steering — software RSS for single-queue NICs |
| **RFS** | Receive Flow Steering — steer packets to the consuming CPU |
| **XPS** | Transmit Packet Steering — map CPUs to TX queues |
| **IRQ coalescing** | Delay/batch hardware interrupts to reduce overhead |
| **IOMMU** | I/O Memory Management Unit — device address space isolation |
| **Descriptor** | Small hardware-readable structure describing a DMA buffer |
| **Doorbell** | MMIO write to a NIC register signaling new descriptors |
| **DD bit** | Descriptor Done — bit set by NIC to indicate completion |
| **EOP** | End Of Packet — marks the last descriptor of a multi-fragment packet |
| **Headroom** | Reserved space before `skb->data` for header prepending |
| **Tailroom** | Reserved space after packet data for trailer appending |
| **Page pool** | Pre-allocated page cache for high-speed RX buffer management |
| **UMEM** | User Memory — AF_XDP's shared memory region with the kernel |
| **MPMC** | Multi-Producer Multi-Consumer ring (requires CAS operations) |
| **SPSC** | Single-Producer Single-Consumer ring (lock-free with barriers only) |
| **False sharing** | Performance bug where unrelated variables share a cache line |
| **NUMA** | Non-Uniform Memory Access — memory closer to some CPUs than others |
| **WQE** | Work Queue Element — RDMA's unit of work submission |
| **CQE** | Completion Queue Element — RDMA's completion notification unit |

---

## Appendix B: Key Header Files and Source Locations

```
include/linux/skbuff.h          — struct sk_buff and all skb operations
include/linux/netdevice.h       — struct net_device, napi_struct, net_device_ops
include/linux/dma-mapping.h     — DMA API (dma_map_*, dma_alloc_coherent)
include/net/page_pool/types.h   — Page pool API
include/net/xdp.h               — XDP types (xdp_buff, xdp_frame)
include/uapi/linux/if_xdp.h     — AF_XDP user-space ABI
net/core/dev.c                  — net_device core, NAPI, softirq processing
net/core/skbuff.c               — sk_buff allocation and management
net/core/page_pool.c            — Page pool implementation
net/xdp.c                       — XDP framework
net/core/filter.c               — BPF/XDP program execution
drivers/net/ethernet/intel/     — Intel NIC drivers (e1000e, igb, i40e, ice)
drivers/net/ethernet/mellanox/  — Mellanox/NVIDIA mlx5 driver
kernel/bpf/ringbuf.c            — BPF ring buffer (perf event ring buffer)
tools/lib/bpf/                  — libbpf user-space library
tools/include/uapi/linux/       — User-space-visible kernel headers
```

---

## Appendix C: Recommended Reading

- Jonathan Corbet, Alessandro Rubini, Greg Kroah-Hartman: *Linux Device Drivers, 3rd Edition* — Chapter 17 (Network Drivers)
- David S. Miller, Alexei Starovoitov: Linux kernel networking documentation (`Documentation/networking/`)
- The Intel i40e driver (`drivers/net/ethernet/intel/i40e/`) — production-quality reference implementation
- The mlx5 driver (`drivers/net/ethernet/mellanox/mlx5/`) — advanced features including XDP, RDMA
- Brendan Gregg: *BPF Performance Tools* — BPF tracing for networking
- Jesper Dangaard Brouer: XDP papers and presentations (Linux Plumbers Conference)
- Linux kernel source: `Documentation/networking/scaling.rst` — RSS, RPS, RFS, XPS
- Linux kernel source: `Documentation/networking/af_xdp.rst` — AF_XDP complete guide