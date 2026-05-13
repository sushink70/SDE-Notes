# Linux Network Buffers: A Complete In-Depth Guide
## sk_buff · Ring Buffers · NIC Hardware · Frames · Packets · Segments · CNI

> **Reading Map**
> Part I → Why buffers exist and what problem space they solve  
> Part II → NIC hardware: DMA rings, descriptors, interrupts  
> Part III → sk_buff: the kernel's universal packet representation  
> Part IV → The full receive path: wire to socket  
> Part V → The full transmit path: socket to wire  
> Part VI → Protocol-layer buffers: frame, packet, segment  
> Part VII → Offload engines: TSO, GSO, GRO  
> Part VIII → Fast paths: XDP and AF_XDP  
> Part IX → CNI and container networking  
> Part X → eBPF integration with the buffer subsystem  

---

# Part I: Foundations — Why Buffers Exist

## Chapter 1: The Physics of Network I/O

### The Core Problem

A network card operates at a fixed clock rate driven by the line speed. A 25 Gbps NIC
delivers one 64-byte frame every 20.48 nanoseconds. The CPU, even at 4 GHz, cannot
service an interrupt 48 million times per second (for minimum-size frames). More critically,
RAM is not wired directly to the NIC — data must traverse the PCIe bus, the IOMMU, and
caches before the CPU can touch it.

This creates three fundamental mismatches:

```
MISMATCH 1: Speed asymmetry
  NIC wire speed:  25 Gbps = 3.125 GB/s continuous
  PCIe Gen4 x8:   ~16 GB/s (shared with other devices)
  Memory BW:      ~50-100 GB/s (DRAM to CPU)
  CPU interrupt:  ~2000 ns latency per interrupt
  
  At 25 Gbps with 64-byte frames: 48.8M frames/sec
  At 1500-byte frames:            2.08M frames/sec
  One interrupt per frame = impossible at line rate

MISMATCH 2: Granularity asymmetry
  Wire delivers: bits → symbols → octets → frames
  CPU works in:  cache lines (64 bytes), pages (4096 bytes)
  Protocol stack sees: bytes, not frames
  Application sees: streams or datagrams, not bytes

MISMATCH 3: Ownership asymmetry
  NIC DMA engine: needs contiguous physical memory at a known DMA address
  Kernel allocator: works in virtual addresses, may use HIGHMEM
  Protocol stack: may split, merge, clone, or fragment data
  Application: reads arbitrary-length slices via read(2)/recv(2)
```

**The solution to all three mismatches is the buffer architecture:**

```
  Wire ──► [NIC RX DMA Ring] ──► [sk_buff + page pool] ──► [protocol stack]
                                                                    │
                    Socket receive queue ◄──── [sk_buff queue] ◄───┘
                           │
                    Application read()
```

Every component in this chain is a buffer with a contract: who owns it, how long they hold it,
and how they hand it off.

---

### The Buffer Taxonomy

Before diving into implementation, establish the vocabulary precisely. The Linux kernel
network stack uses these buffer types at different layers:

```
OSI/Layer  Linux Abstraction         Hardware Abstraction
─────────  ─────────────────         ───────────────────
L1         N/A (PHY layer)           Electrical signals, symbols, octets
L2 Frame   sk_buff (head_room used)  NIC RX descriptor + DMA buffer
L3 Packet  sk_buff (network_header)  Same sk_buff, pointer repositioned
L4 Segment sk_buff (transport_hdr)   Same sk_buff, pointer repositioned
           + TCP send queue (sk_buff_head)
L5-7 Data  socket rcv/snd buffer     Copied or zero-copied to user pages
           (sk->sk_rcvbuf)
```

**Key insight**: In Linux, a "frame", "packet", and "segment" are NOT different memory
objects. They are the SAME `sk_buff`, with different header pointers set to describe
where in the buffer each protocol header begins. The distinction is conceptual, not
structural — until fragmentation, cloning, or GSO/GRO creates actual separate `sk_buff`s.

---

# Part II: NIC Hardware — DMA Rings, Descriptors, and Interrupts

## Chapter 2: The NIC Hardware Architecture

### 2.1 Physical Anatomy of a Modern NIC

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  NIC (e.g., Intel E810, Mellanox CX6)│
                    │                                                       │
  SFP28 / QSFP ────►│  PHY/SerDes  ──► MAC ──► L2 Engine ──► DMA Engine  │
  (25G / 100G)      │  (signal)       (frame)  (RSS/flow)    (PCIe DMA)   │
                    │                                                       │
                    │  ┌──────────────────────────────────────────────┐    │
                    │  │  NIC Internal Memory                         │    │
                    │  │  ┌──────────────┐  ┌───────────────────┐    │    │
                    │  │  │  RX Queues   │  │  TX Queues        │    │    │
                    │  │  │  (per-queue  │  │  (per-queue       │    │    │
                    │  │  │   ring ptrs) │  │   ring ptrs)      │    │    │
                    │  │  └──────────────┘  └───────────────────┘    │    │
                    │  │  ┌──────────────────────────────────────┐    │    │
                    │  │  │  Flow Steering / RSS Hash Engine     │    │    │
                    │  │  │  (maps packet to queue index)        │    │    │
                    │  │  └──────────────────────────────────────┘    │    │
                    │  │  ┌──────────────────────────────────────┐    │    │
                    │  │  │  Offload Engines                     │    │    │
                    │  │  │  TSO / LRO / Checksum / VXLAN-offld  │    │    │
                    │  │  └──────────────────────────────────────┘    │    │
                    │  └──────────────────────────────────────────┘    │    │
                    │                        │                          │    │
                    │                   PCIe Gen4 x16                  │    │
                    └────────────────────────┼─────────────────────────┘    │
                                             │                               │
                    ┌────────────────────────▼───────────────────────────┐  │
                    │                  PCIe Root Complex / IOMMU          │  │
                    │         (address translation: IOVA → PA)            │  │
                    └────────────────────────┬───────────────────────────┘  │
                                             │                               │
                    ┌────────────────────────▼───────────────────────────┐  │
                    │              DRAM (Physical Memory)                  │  │
                    │  ┌──────────────────┐  ┌──────────────────────┐    │  │
                    │  │  RX Descriptor   │  │  TX Descriptor       │    │  │
                    │  │  Ring (kernel)   │  │  Ring (kernel)       │    │  │
                    │  └──────────────────┘  └──────────────────────┘    │  │
                    │  ┌──────────────────────────────────────────────┐  │  │
                    │  │  Packet Data Buffers (pages / page pool)     │  │  │
                    │  └──────────────────────────────────────────────┘  │  │
                    └────────────────────────────────────────────────────┘  │
```

### 2.2 DMA and IOMMU — The Memory Contract

**The fundamental contract**: The NIC cannot use virtual addresses. It operates on either
physical addresses (PA) or IOVA (I/O Virtual Addresses) mediated by the IOMMU.

The kernel driver performs this mapping:

```
Step 1: Allocate kernel buffer (virtual address = kvirt)
         kvirt ──► physical page ──► PA = virt_to_phys(kvirt)

Step 2: Map for DMA (via IOMMU if present)
         dma_addr = dma_map_single(dev, kvirt, size, DMA_FROM_DEVICE)
         dma_addr is IOVA that NIC will write to

Step 3: Program NIC descriptor with dma_addr
         descriptor.buffer_addr = dma_addr
         descriptor.length      = PAGE_SIZE (or buffer size)

Step 4: NIC receives frame, DMA-writes directly to PA
         (CPU caches are bypassed — this is the "direct memory access")

Step 5: Driver receives interrupt or polls (NAPI)
         dma_unmap_single(dev, dma_addr, size, DMA_FROM_DEVICE)
         (flushes cache coherency — makes DMA write visible to CPU)

Step 6: Driver wraps physical page in sk_buff for stack
```

**Why IOMMU matters for security**: Without IOMMU, a compromised NIC (or any PCIe device)
can DMA-write to arbitrary physical addresses, achieving full kernel memory write. The IOMMU
restricts the NIC to IOVA ranges explicitly mapped by the driver. This is why enabling
`intel_iommu=on` or `amd_iommu=on` is a security requirement for multi-tenant systems.

### 2.3 The RX Descriptor Ring — Physical Structure

The RX descriptor ring is a circular array of fixed-size descriptors in physically contiguous
memory. The driver and NIC share this ring using a producer-consumer model with two pointers:

```
Physical Memory Layout of RX Descriptor Ring
(e.g., Intel igb / ixgbe driver)

     DRAM                                              NIC Registers
  ┌─────────────────────────────────────────┐       ┌──────────────────┐
  │  RX Descriptor Ring (N entries)          │       │  RDBA: base addr │
  │                                           │       │  RDLEN: ring len │
  │  base ──► [desc 0] ── [desc 1] ── ...    │ ◄───► │  RDH:  hw head   │
  │           [desc N-2] ── [desc N-1] ──┐   │       │  RDT:  sw tail   │
  │                        ▲ (wraps)     │   │       └──────────────────┘
  │                        └─────────────┘   │
  └─────────────────────────────────────────┘
  
  Producer: driver (software)  → advances RDT (tail)
  Consumer: NIC hardware       → advances RDH (head)
  
  Ring state interpretation:
  ┌────────────────────────────────────────────────┐
  │  [RDH]   [...]   [RDT]   [...]   [RDH-1]       │
  │   NIC      ◄─ NIC owns ─►   ◄─ SW owns ─►     │
  │   at head  (filled/in use)  (free/posted)       │
  └────────────────────────────────────────────────┘
  
  RDH to RDT-1:  NIC has received into these; driver must consume
  RDT to RDH-1:  Driver has posted empty buffers; NIC will fill them
```

### 2.4 Intel igb/ixgbe RX Descriptor Format

This is the actual wire format of an Intel 82599 (ixgbe) Advanced RX Descriptor in
"write-back" mode — what the NIC writes back after completing DMA:

```
Advanced RX Descriptor — Read Format (driver → NIC, posting empty buffer)

  Byte offset  0        7  8       15
               ┌─────────┬─────────┐
               │ Pkt Buf │ Hdr Buf │
               │ Address │ Address │
               │ (64-bit)│ (64-bit)│
               └─────────┴─────────┘
               
  Pkt Buf Address: IOVA of the DMA-mapped page where NIC should write the packet
  Hdr Buf Address: IOVA of header split buffer (optional, for header split mode)

Advanced RX Descriptor — Write-Back Format (NIC → driver, after DMA complete)

  Bit 127                                                              Bit 0
  ┌──────┬──────┬──────┬──────────┬──────┬──────────┬────────────────┐
  │VLAN  │Length│RSS   │Ext Status│RSS   │Pkt Type  │Reserved        │
  │Tag   │      │Type  │& Error   │Hash  │          │                │
  │[16]  │[16]  │[4]   │[20]      │[32]  │[16]      │[24]            │
  └──────┴──────┴──────┴──────────┴──────┴──────────┴────────────────┘
  
  Length:      actual received byte count (set by NIC)
  RSS Hash:    Receive Side Scaling hash (used for queue selection)
  Ext Status:  DD (Descriptor Done) bit — set when NIC completes the write
  Pkt Type:    L2/L3/L4 protocol identification done in hardware
  VLAN Tag:    stripped VLAN ID if VLAN offload enabled
  Error:       L4 checksum error, L3 checksum error, etc.
```

**The DD (Descriptor Done) bit is the fundamental synchronization primitive**:
The driver polls or is interrupted when DD=1, meaning the NIC has completed writing
the packet data into the DMA buffer and has written back the descriptor metadata.
Before DD=1, the CPU must NOT read the buffer — the NIC is writing to it via DMA.

### 2.5 The TX Descriptor Ring

```
TX Descriptor Ring — driver perspective

  step 1: sk_buff arrives at net_device xmit()
  step 2: driver maps sk_buff pages via dma_map_single / dma_map_page
  step 3: driver fills TX descriptor(s) with IOVA and metadata
  step 4: driver advances TDT (TX Descriptor Tail) — doorbell to NIC
  step 5: NIC reads descriptor, DMAs from our pages to its TX FIFO
  step 6: NIC sets DD bit in descriptor when done transmitting
  step 7: driver TX cleanup task frees sk_buff and unmaps DMA

  Intel ixgbe TX descriptor (Context Descriptor for offloads):
  
  Byte  0        7   8       15
        ┌─────────┬──────────┐
        │VLAN/L4  │ MSS/L4Len│
        │ Len/L3  │ DTYP/DCMD│
        │ Tunnels │          │
        └─────────┴──────────┘
  
  Intel ixgbe TX descriptor (Data Descriptor, one per buffer segment):
  
  Bit 127                                                             Bit 0
  ┌───────┬─────┬──────┬───────────────────────────────────────────────┐
  │PAYLEN │PORTS│DCMD  │  Buffer Address (64-bit IOVA)                 │
  │[18]   │ [1] │[8]   │                                               │
  └───────┴─────┴──────┴───────────────────────────────────────────────┘
  
  DCMD flags:
    EOP  (bit 0): End Of Packet — last descriptor for this frame
    IFCS (bit 1): Insert FCS/CRC
    RS   (bit 3): Report Status — set DD when transmit complete
    TSE  (bit 7): TCP Segmentation Enable — hardware does TSO
    
  One sk_buff may require multiple TX descriptors:
    - One Context Descriptor (offload info)
    - One Data Descriptor per fragment (for non-linear sk_buff)
    - The last Data Descriptor has EOP=1
```

### 2.6 Multi-Queue NICs and RSS (Receive Side Scaling)

A modern NIC has N RX queues (N = 64 to 512 on datacenter NICs). RSS distributes
incoming packets across queues based on a Toeplitz hash of the 5-tuple:

```
RSS Hash Computation in NIC Hardware

  Incoming packet:
    Src IP: 10.0.0.1   Dst IP: 10.0.0.2
    Src Port: 54321    Dst Port: 443
    Protocol: TCP

  Toeplitz hash:
    input = [10.0.0.1 || 10.0.0.2 || 54321 || 443 || TCP]
    hash  = TOEPLITZ(input, secret_key[40 bytes])
    queue = hash & (num_queues - 1)
  
  Result: packet lands in queue #Q, which maps to CPU core #Q
  (via /proc/irq/<N>/smp_affinity or irqbalance)

  Why this matters for performance:
  ┌──────────────────────────────────────────────────────┐
  │  Without RSS: all packets → queue 0 → one CPU       │
  │  max throughput ≈ 1M pps (one core doing everything) │
  │                                                      │
  │  With RSS: packets distributed across 16 queues      │
  │  max throughput ≈ 14-16M pps (16 cores)              │
  │                                                      │
  │  Flow-consistent: same 5-tuple → same queue → same   │
  │  CPU → no TCP state machine cache thrashing          │
  └──────────────────────────────────────────────────────┘
```

### 2.7 Interrupts vs. NAPI Polling — The Interrupt Mitigation Problem

Early drivers used one interrupt per received frame. At 1Mpps this means 1M interrupts/sec —
each interrupt costs 2-10μs of CPU time, so you spend 2-10 seconds of CPU per second
just on interrupts. This is why NAPI (New API) exists.

```
NAPI State Machine

  Initial state: NIC interrupt enabled, driver waiting

  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                   │
  │  [PACKET ARRIVES]                                                 │
  │       │                                                           │
  │       ▼                                                           │
  │  NIC fires interrupt (MSI-X to specific CPU core)                 │
  │       │                                                           │
  │       ▼                                                           │
  │  Hard IRQ handler (runs with IRQs disabled):                      │
  │    1. Acknowledge interrupt in NIC                                 │
  │    2. DISABLE NIC interrupt for this queue (crucial!)             │
  │    3. Schedule NAPI poll: napi_schedule(&napi)                    │
  │       → sets NET_RX_SOFTIRQ pending                               │
  │       │                                                           │
  │       ▼                                                           │
  │  SoftIRQ runs (NET_RX_SOFTIRQ, on same CPU):                      │
  │    net_rx_action() → calls driver->napi_poll()                    │
  │       │                                                           │
  │       ▼                                                           │
  │  Driver poll loop:                                                 │
  │    while (budget > 0 && packets_remain):                          │
  │      desc = ring[head]                                             │
  │      if desc.DD == 0: break  (no more packets)                    │
  │      skb = build_skb(desc)                                        │
  │      napi_gro_receive() or netif_receive_skb()                    │
  │      refill descriptor with new buffer                            │
  │      head = (head + 1) % ring_size                                │
  │      budget--                                                      │
  │       │                                                           │
  │       ▼                                                           │
  │  If budget exhausted (ring still has packets):                    │
  │    return budget (= 0)                                             │
  │    net_rx_action reschedules poll for next softirq cycle           │
  │    NIC interrupt stays DISABLED                                    │
  │       │                                                           │
  │  If ring empty before budget:                                      │
  │    napi_complete_done(&napi, pkts_processed)                       │
  │    RE-ENABLE NIC interrupt                                         │
  │    return to wait for next interrupt                               │
  │                                                                   │
  └─────────────────────────────────────────────────────────────────┘

  Budget default: 64 packets per poll cycle (net.core.netdev_budget)
  Tunable: /proc/sys/net/core/netdev_budget
           /proc/sys/net/core/netdev_budget_usecs
```

**The NAPI insight**: By disabling the NIC interrupt during the poll loop, the driver
converts interrupt-driven I/O into polling I/O under load. Under low load (< budget packets),
it returns to interrupt mode, saving CPU cycles. Under high load, it stays in poll mode,
amortizing interrupt overhead across many packets.

---

# Part III: sk_buff — The Kernel's Universal Packet Representation

## Chapter 3: sk_buff Structure Deep Dive

### 3.1 What sk_buff Actually Is

`sk_buff` (socket buffer) is defined in `include/linux/skbuff.h` and is the central
data structure for every packet in the Linux kernel network stack. It is NOT just a buffer —
it is a descriptor that POINTS to a buffer (or collection of buffers) and carries all
metadata about that packet through its entire lifecycle.

**Analogy**: Think of `sk_buff` like an IP packet header + fragmentation descriptor. The
IP header doesn't contain the payload — it points to it and describes how it's structured.
Similarly, `sk_buff` doesn't contain the packet data inline — it points to a data area and
describes its layout.

**Where this analogy breaks**: `sk_buff` lives entirely in kernel memory. Unlike IP headers,
which travel on the wire, `sk_buff`s are destroyed and recreated at every network boundary.
They are purely a kernel-internal representation.

### 3.2 sk_buff Memory Layout — Complete Structure

```
sk_buff control block (lives in kernel slab, ~240 bytes on x86_64):

  struct sk_buff {
    /* --- Linked list linkage --- */
    struct sk_buff      *next;         // next skb in queue
    struct sk_buff      *prev;         // prev skb in queue
    struct sk_buff_head *list;         // queue this skb belongs to
    
    /* --- Timestamping --- */
    ktime_t              tstamp;       // RX timestamp (hardware or software)
    
    /* --- Device --- */
    struct net_device   *dev;          // network device this arrived on / will leave via
    
    /* --- Routing --- */
    struct  dst_entry   *dst;          // routing cache entry
    
    /* --- Transport layer socket --- */
    struct sock         *sk;           // owning socket (NULL for forwarded packets)
    
    /* --- Protocol and interface info --- */
    __be16               protocol;     // ETH_P_IP, ETH_P_IPV6, ETH_P_ARP, etc.
    __u8                 pkt_type;     // PACKET_HOST, PACKET_BROADCAST, etc.
    
    /* --- Header pointers (as offsets from head, NOT pointers!) --- */
    sk_buff_data_t       transport_header;  // TCP/UDP header offset
    sk_buff_data_t       network_header;    // IP/IPv6 header offset
    sk_buff_data_t       mac_header;        // Ethernet header offset
    sk_buff_data_t       inner_*_header;    // For tunneled packets
    
    /* === THE CRITICAL DATA AREA POINTERS === */
    unsigned char       *head;    // start of allocated buffer
    unsigned char       *data;    // start of current packet data
    sk_buff_data_t       tail;    // end of current packet data (as offset)
    sk_buff_data_t       end;     // end of allocated buffer (as offset)
    
    /* --- Length fields --- */
    unsigned int         len;     // total packet length (linear + frags)
    unsigned int         data_len; // length in frags only (nonlinear portion)
    __u16                mac_len;  // length of MAC header
    __u16                hdr_len;  // clone header size (for clones)
    
    /* --- Checksum state --- */
    __wsum               csum;     // checksum (meaning depends on ip_summed)
    __u8                 ip_summed; // CHECKSUM_NONE/PARTIAL/COMPLETE/UNNECESSARY
    
    /* --- Cloning and reference counting --- */
    atomic_t             users;    // reference count on this sk_buff descriptor
    
    /* --- Fragmentation --- */
    __u16                frag_list; // IP fragment list linkage
    
    /* --- GSO/TSO metadata --- */
    struct skb_shared_info *shinfo; // lives at skb->end (see below)
    
    /* --- Mark, priority, tc, secpath --- */
    __u32                mark;     // fwmark (used by iptables MARK, tc filter)
    __u32                priority; // QoS priority
    
    /* --- Control block (protocol-specific scratch space) --- */
    char                 cb[48];   // used by each protocol layer as scratch
                                   // TCP: struct tcp_skb_cb
                                   // IP:  struct inet_skb_parm
                                   // eBPF: struct bpf_skb_data_end
    
    /* ... many more fields ... */
  };
```

### 3.3 The Four Pointer Model — The Heart of sk_buff

This is the most important concept in the entire sk_buff system. Understand this
and everything else follows:

```
Physical memory layout of sk_buff data area:

  ┌──────────────────────────────────────────────────────────────────────┐
  │                    Allocated buffer (kmalloc / page)                  │
  │                                                                        │
  │  head                 data          tail              end              │
  │   │                    │              │                │               │
  │   ▼                    ▼              ▼                ▼               │
  │   ┌────────────────────┬─────────────┬────────────────┐               │
  │   │    head room       │  PACKET DATA│   tail room    │               │
  │   │  (for prepending   │  (live data)│  (for appending│               │
  │   │   headers later)   │             │   data later)  │               │
  │   └────────────────────┴─────────────┴────────────────┘               │
  │                                                                        │
  │   ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ skb->len ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ► │
  │   (if fully linear)                                                    │
  │                                                                        │
  │   [skb_shared_info] lives immediately after end (at skb->end offset)  │
  └──────────────────────────────────────────────────────────────────────┘

  Invariants:
    head ≤ data ≤ tail ≤ end
    len  = (tail - data) + data_len   [linear + nonlinear]
    headroom = data - head            [space to prepend headers]
    tailroom = end - tail             [space to append data]
```

**Why headroom and tailroom exist**: When a packet travels up or down the stack,
each layer must add or remove its headers. Instead of copying the packet into a new buffer
every time, the kernel uses headroom/tailroom:

- **Receiving** (bottom-up, headers are STRIPPED):
  - Driver: data points at Ethernet header
  - `eth_type_trans()`: `skb_pull(skb, ETH_HLEN)` → data now points at IP header
  - `ip_rcv()`: `skb_pull(skb, iph->ihl*4)` → data now points at TCP header
  - Each pull just advances the data pointer — no copy

- **Sending** (top-down, headers are ADDED):
  - TCP: `skb_push(skb, sizeof(tcphdr))` → data moves BACK, writes TCP header in headroom
  - IP: `skb_push(skb, sizeof(iphdr))` → data moves back further, writes IP header
  - Ethernet: `skb_push(skb, ETH_HLEN)` → writes Ethernet header
  - Result: final sk_buff has full frame from data to tail, ready for NIC

```
skb_push / skb_pull operations:

  skb_push(skb, len):              skb_pull(skb, len):
  Extends packet at the FRONT      Shrinks packet at the FRONT
    data -= len                      data += len
    skb->len += len                  skb->len -= len
  (uses headroom)                  (returns old data pointer)

  skb_put(skb, len):               skb_trim(skb, len):
  Extends packet at the TAIL       Shrinks packet at the TAIL
    old_tail = tail                  skb->len = len
    tail += len                      tail = data + len
    skb->len += len
  (uses tailroom)
```

### 3.4 skb_shared_info — The Non-Linear Extension

For packets larger than a single page (or for zero-copy optimization), `sk_buff` uses a
"shared info" structure to point to additional data in page fragments. This makes `sk_buff`
a **gather buffer** — the packet data is scattered across multiple physical pages:

```
skb_shared_info layout (lives at skb->end, immediately after linear data):

  struct skb_shared_info {
    __u8           flags;
    __u8           meta_len;
    __u8           nr_frags;         // number of page fragments (0 = linear only)
    __u8           tx_flags;
    unsigned short gso_size;         // GSO segment size
    unsigned short gso_segs;         // GSO segment count
    unsigned short gso_type;         // SKB_GSO_TCPV4, SKB_GSO_UDP_L4, etc.
    struct sk_buff *frag_list;       // IP fragment chain
    struct skb_shared_hwtstamps hwtstamps;
    u32            tskey;
    atomic_t       dataref;          // how many sk_buff descriptors share this data
    
    /* The fragment array — up to MAX_SKB_FRAGS (17) fragments */
    skb_frag_t     frags[MAX_SKB_FRAGS];
  };
  
  skb_frag_t structure:
  struct skb_frag_struct {
    struct {
      struct page *p;    // pointer to struct page
    } page;
    __u32 page_offset;  // byte offset within the page
    __u32 size;         // number of bytes in this fragment
  };
```

**Full non-linear sk_buff picture**:

```
Non-linear sk_buff with 3 page fragments:

  sk_buff descriptor (in slab)
  ┌─────────────────────────────────┐
  │ head ──────────────────────┐    │
  │ data ─────────────────┐    │    │
  │ tail ──────────────┐  │    │    │
  │ end ────────────┐  │  │    │    │
  │ len = 1448+4096 │  │  │    │    │
  │ data_len = 4096 │  │  │    │    │
  │ nr_frags = 1    │  │  │    │    │
  └─────────────────│──│──│────│────┘
                    │  │  │    │
  Physical memory:  │  │  │    │
                    ▼  ▼  ▼    ▼
  ┌───────────────────────────────────────────────────────────┐
  │  Linear area (one kmalloc buffer):                         │
  │  [headroom][ETH HDR][IP HDR][TCP HDR][TCP DATA (1448B)] │skb_shared_info│
  │  ▲head      ▲data             ▲                 ▲tail   ▲end│
  └───────────────────────────────────────────────────────────┘
                                                       │
                                                  frags[0]
                                                       │
  ┌────────────────────────────────────────────────────▼──────┐
  │  Page fragment (4096 bytes of TCP data):                   │
  │  [TCP DATA continuation ─────────────────────────────────] │
  │  ▲page                                                     │
  └────────────────────────────────────────────────────────────┘

  skb_is_nonlinear(skb):  returns true if data_len > 0 || nr_frags > 0
  skb_linearize(skb):     pulls all fragments into linear area (copies!)
```

**Why this matters for performance**: When the kernel receives a large TCP segment via GRO,
or when an application calls `sendfile()`, the packet data stays in its original pages —
the sk_buff's frag array just references those pages. No copy occurs. This is the foundation
of zero-copy I/O.

**What this means for eBPF**: XDP programs and `bpf_skb_*` helpers can only access the
LINEAR portion of an sk_buff by default. If a packet is non-linear, helpers like
`bpf_skb_load_bytes()` must be used to access fragment data, or `bpf_skb_pull_data()`
to force linearization (expensive — involves a copy).

### 3.5 sk_buff Reference Counting and Cloning

```
Reference counting model:

  skb->users:          reference count on the sk_buff DESCRIPTOR
  shinfo->dataref:     reference count on the DATA AREA

  Operations:
  
  skb_get(skb):
    atomic_inc(&skb->users)
    // another sk_buff descriptor points to same data
    // used for: multicast replication, packet tee (AF_PACKET)
  
  skb_clone(skb, gfp_mask):
    // Creates a new sk_buff descriptor pointing to SAME data area
    // Increments shinfo->dataref
    // Returns new sk_buff with shared data
    // Cheaper than skb_copy (no data copy)
    // Caller cannot modify cloned data (must use skb_copy_header)
    new_skb->head = skb->head        // same buffer
    new_skb->data = skb->data        // same start
    atomic_inc(&skinfo->dataref)    // data is now shared
  
  skb_copy(skb, gfp_mask):
    // Creates completely independent sk_buff with copied data
    // new_skb has its own buffer, all data copied
    // Safe to modify — no shared state
    // Expensive (memcpy of entire packet)

  kfree_skb(skb):
    if --skb->users > 0: return      // others still hold the descriptor
    skb_release_data(skb):
      if --shinfo->dataref > 0: return // data still referenced by clone
      // free page fragments
      // free linear buffer
    kfree(skb descriptor)            // return descriptor to slab cache
```

```
Clone vs Copy illustration:

  ORIGINAL sk_buff:
  ┌─────────────┐      ┌──────────────────────────────┐
  │ descriptor  │─────►│       DATA BUFFER             │
  │ users=1     │      │  [hdrs][payload][shared_info] │
  │ dataref=1   │      └──────────────────────────────┘
  └─────────────┘

  After skb_clone():
  ┌─────────────┐      ┌──────────────────────────────┐
  │ original    │─────►│       DATA BUFFER             │
  │ users=1     │      │  [hdrs][payload][shared_info] │
  │             │  ┌──►│       dataref = 2             │
  └─────────────┘  │   └──────────────────────────────┘
  ┌─────────────┐  │
  │ clone       │──┘   // points to SAME buffer
  │ users=1     │      // cheap: only descriptor allocated
  └─────────────┘

  After skb_copy():
  ┌─────────────┐      ┌──────────────────────────────┐
  │ original    │─────►│       DATA BUFFER (original)  │
  │ users=1     │      │  dataref = 1                  │
  │             │      └──────────────────────────────┘
  └─────────────┘
  ┌─────────────┐      ┌──────────────────────────────┐
  │ copy        │─────►│       DATA BUFFER (new copy)  │
  │ users=1     │      │  dataref = 1  (independent)   │
  │             │      └──────────────────────────────┘
  └─────────────┘
```

### 3.6 sk_buff Header Pointers — Protocol Demultiplexing

Each protocol layer sets its header pointer as it processes the packet. These are stored
as OFFSETS from `head` (not raw pointers) to survive reallocation:

```
Header pointer progression during receive:

  Ethernet frame arriving from NIC:
  
  data
   │
   ▼
  ┌──────────────┬──────────────┬───────────────────┬───────────────┐
  │ Ethernet hdr │   IP header  │    TCP header      │   TCP data    │
  │   (14 bytes) │  (20 bytes)  │    (20 bytes)      │               │
  └──────────────┴──────────────┴───────────────────┴───────────────┘
  
  eth_type_trans():
    skb->mac_header = data - head        // save Ethernet header offset
    skb_pull(skb, ETH_HLEN)             // advance data past Ethernet
    skb->protocol = eth->h_proto        // ETH_P_IP / ETH_P_IPV6
  
  ip_rcv():
    skb->network_header = data - head   // save IP header offset
    // process IP, verify checksum, route lookup
    skb_pull(skb, iph->ihl * 4)        // advance past IP header
  
  tcp_v4_rcv():
    skb->transport_header = data - head // save TCP header offset
    // process TCP, deliver to socket
  
  Access macros:
    eth_hdr(skb)  = (struct ethhdr *)(skb->head + skb->mac_header)
    ip_hdr(skb)   = (struct iphdr  *)(skb->head + skb->network_header)
    tcp_hdr(skb)  = (struct tcphdr *)(skb->head + skb->transport_header)
    skb->data     = current processing position
```

### 3.7 The cb[] Control Block — Per-Layer Scratch Space

The `cb[48]` field is the most overloaded field in `sk_buff`. Each protocol layer
casts it to its own structure while the packet is at that layer:

```c
/* TCP layer (net/ipv4/tcp.h): */
struct tcp_skb_cb {
    __u32   seq;        // starting sequence number
    __u32   end_seq;    // SEQ + FIN + SYN + datalen
    __u8    tcp_flags;  // TCP flags (SYN, ACK, FIN, etc.)
    __u8    sacked;     // SACKED, FACK, LOST, RETRANS
    __u16   urg_ptr;    // urgent pointer offset
    __u32   ack_seq;    // TCP ACK sequence number
    /* ... more TCP state ... */
};

/* IP layer (net/ip.h): */
struct inet_skb_parm {
    int         iif;         // incoming interface index
    struct ip_options opt;   // IP options parsed
    u16         flags;       // IPSKB_FORWARDED, IPSKB_XFRM_TUNNEL_SIZE, etc.
};

/* eBPF (include/linux/filter.h): */
struct bpf_skb_data_end {
    struct qdisc_skb_cb qdisc_cb;
    void *data_meta;    // XDP metadata pointer
    void *data_end;     // end of packet data (for verifier bounds checking)
};
```

**Security implication**: The `cb[]` field is NOT cleared between protocol layers. A packet
transitioning from one namespace to another carries stale cb[] data. This has historically
been a source of kernel information leaks. Drivers that expose cb[] to user space via
`AF_PACKET` must sanitize it.

---

# Part IV: The Full Receive Path

## Chapter 4: Wire to Socket — Every Step

### 4.1 Overview of the RX Path

```
Complete Linux RX packet path (simplified, no XDP):

  NIC Wire
     │ (electrical/optical signal)
     ▼
  NIC PHY+MAC (hardware frame assembly)
     │ (complete Ethernet frame in NIC FIFO)
     ▼
  NIC DMA Engine → writes frame to pre-allocated DMA buffer
     │ (IOVA in RX descriptor → physical page)
     ▼
  NIC sets DD=1 in RX descriptor, fires MSI-X interrupt
     │
     ▼
  CPU Hard IRQ handler (irq_handler_t in driver)
     │ disable_napi_irq(), napi_schedule()
     ▼
  NET_RX_SOFTIRQ raised on this CPU
     │
     ▼
  net_rx_action() [net/core/dev.c]
     │ calls driver napi_poll()
     ▼
  Driver poll(): reads completed descriptors, builds sk_buff
     │ dma_unmap_single(), build_skb() or napi_alloc_skb()
     ▼
  napi_gro_receive() [GRO layer]  ← or netif_receive_skb() if GRO disabled
     │ coalesces TCP segments into super-frames
     ▼
  __netif_receive_skb() [net/core/dev.c]
     │ delivers to registered packet_type handlers
     ▼
  Possible hooks here:
     ├── AF_PACKET sockets (tcpdump, Wireshark tap)
     ├── tc ingress (BPF/eBPF classifiers)
     ├── Netfilter PREROUTING hook
     └── bridge/vlan demux
     │
     ▼
  ip_rcv() / ipv6_rcv()  [net/ipv4/ip_input.c]
     │ IP header validation, checksum, defragmentation if needed
     ▼
  NF_INET_PRE_ROUTING (netfilter)
     │ conntrack, NAT DNAT lookup
     ▼
  ip_route_input_noref() → routing decision
     │
     ├── Local delivery: ip_local_deliver()
     │      │
     │      ▼
     │   ip_local_deliver_finish()
     │      │
     │      ▼
     │   NF_INET_LOCAL_IN (netfilter)
     │      │
     │      ▼
     │   Protocol demux: inet_protos[protocol]
     │      │
     │      ├── TCP: tcp_v4_rcv()
     │      ├── UDP: udp_rcv()
     │      └── ICMP: icmp_rcv()
     │
     └── Forward: ip_forward()
            │
            ▼
         NF_INET_FORWARD
            │
            ▼
         ip_output() → NIC TX
```

### 4.2 Driver sk_buff Construction — The build_skb() Pattern

Modern drivers use `build_skb()` or `napi_alloc_skb()` to construct the sk_buff from
a DMA-complete page. Here's what happens at the driver level:

```c
/* Simplified from drivers/net/ethernet/intel/ixgbe/ixgbe_main.c */

/* During ring setup (done once at init): */
void ixgbe_alloc_rx_buffers(struct ixgbe_ring *rx_ring, u16 cleaned_count)
{
    struct ixgbe_rx_buffer *bi;
    union ixgbe_adv_rx_desc *rx_desc;
    
    while (cleaned_count--) {
        bi = &rx_ring->rx_buffer_info[rx_ring->next_to_use];
        
        /* Allocate a page (from page pool for efficiency) */
        bi->page = dev_alloc_pages(rx_ring->rx_buf_order);
        
        /* Map for DMA — NIC will write here */
        bi->dma = dma_map_page(dev, bi->page, 0, PAGE_SIZE, DMA_FROM_DEVICE);
        
        /* Post to NIC: fill descriptor with IOVA */
        rx_desc = IXGBE_RX_DESC(rx_ring, rx_ring->next_to_use);
        rx_desc->read.pkt_addr = cpu_to_le64(bi->dma);
        rx_desc->read.hdr_addr = 0;
        
        rx_ring->next_to_use = (rx_ring->next_to_use + 1) % rx_ring->count;
    }
    
    /* DOORBELL: tell NIC new descriptors are ready */
    writel(rx_ring->next_to_use, rx_ring->tail);
}

/* During NAPI poll (called per received packet): */
static bool ixgbe_clean_rx_irq(struct ixgbe_q_vector *q_vector,
                                 struct ixgbe_ring *rx_ring, int budget)
{
    while (total_rx_packets < budget) {
        rx_desc = IXGBE_RX_DESC(rx_ring, rx_ring->next_to_clean);
        
        /* Check DD bit — is this descriptor complete? */
        if (!(rx_desc->wb.upper.status_error & IXGBE_RXD_STAT_DD))
            break;
        
        bi = &rx_ring->rx_buffer_info[rx_ring->next_to_clean];
        
        /* Unmap from DMA — makes NIC's write visible to CPU */
        dma_unmap_page(dev, bi->dma, PAGE_SIZE, DMA_FROM_DEVICE);
        
        /* Build sk_buff around the page — ZERO COPY */
        /* build_skb() only allocates the sk_buff descriptor (~240 bytes),
           not the data — the data is already in bi->page */
        skb = build_skb(page_address(bi->page) + bi->page_offset,
                        ixgbe_rx_bufsz(rx_ring));
        
        /* Set data pointers: data = page start + headroom
           tail = data + actual_packet_length */
        skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
        __skb_put(skb, le16_to_cpu(rx_desc->wb.upper.length));
        
        /* Copy hardware offload metadata to sk_buff */
        skb->protocol = eth_type_trans(skb, rx_ring->netdev);
        skb_record_rx_queue(skb, rx_ring->queue_index);
        
        /* Set checksum state from NIC's hardware offload */
        if (rx_desc->wb.upper.status_error & IXGBE_RXD_STAT_IPCS) {
            skb->ip_summed = CHECKSUM_UNNECESSARY;  // NIC verified checksum
        }
        
        /* Hand to GRO or directly to stack */
        napi_gro_receive(&q_vector->napi, skb);
        
        rx_ring->next_to_clean = (rx_ring->next_to_clean + 1) % rx_ring->count;
    }
}
```

### 4.3 GRO — Generic Receive Offload

GRO is a software technique that coalesces multiple TCP/UDP segments into a single
large sk_buff before delivering to the stack. This amortizes per-packet overhead
(skb allocation, IP/TCP header processing, socket lock acquisition) across many packets.

```
GRO Coalescing — Memory Visualization:

  Without GRO (10 x 1460-byte TCP segments):
  
  skb1[1500B] skb2[1500B] skb3[1500B] ... skb10[1500B]
       │            │            │                │
       ▼            ▼            ▼                ▼
  tcp_rcv()   tcp_rcv()   tcp_rcv()   ...  tcp_rcv()
  (10 calls, 10 socket lock acquisitions, 10 ACK decisions)
  
  With GRO (same 10 segments merged):
  
  gro_skb[14500B] = skb1 + skb2 + ... + skb10
  (linear header from skb1, payload in frag list)
       │
       ▼
  tcp_rcv()  (ONE call, ONE socket lock, ONE ACK decision)
  
  GRO merge rules (napi_gro_receive → dev_gro_receive):
    - Same 5-tuple (src/dst IP, src/dst port, protocol)
    - Consecutive TCP sequence numbers
    - Same IP ID increment pattern
    - Total size must not exceed GRO limit (65535 bytes)
    - Flush on: FIN, RST, TCP options mismatch, PSH (optional), coalesce limit
```

```
GRO internal state — napi_struct gro_list:

  struct napi_struct {
    struct list_head  gro_list;   // list of sk_buff being accumulated
    int               gro_count;  // number of flows being tracked
    /* ... */
  };
  
  Each entry in gro_list is a "GRO super-skb":
    - skb->len = total coalesced size
    - skb->data_len = size in frags (= linear header only)
    - skb_shared_info->frag_list = linked list of component skbs
  
  On flush (napi_gro_flush() at end of poll):
    GRO super-skb is delivered to stack as one large sk_buff
    Stack processes it as if it were a single segment
```

### 4.4 Netfilter Hooks — Where Firewall and NAT Intercept sk_buff

```
Netfilter hook points in the IP receive path:

     incoming sk_buff
          │
          ▼
     NF_INET_PRE_ROUTING          ← conntrack, DNAT, raw table
          │
          ├── routing decision
          │
          ▼                        ▼
     NF_INET_LOCAL_IN         NF_INET_FORWARD         ← forwarded packets
     (for local delivery)          │
          │                        ▼
          ▼                   NF_INET_POST_ROUTING     ← SNAT, MASQUERADE
     local socket
     (TCP/UDP/etc)
     
  
  Outgoing sk_buff:
     socket → sk_buff
          │
          ▼
     NF_INET_LOCAL_OUT            ← OUTPUT chain (local generated packets)
          │
          ▼
     routing
          │
          ▼
     NF_INET_POST_ROUTING         ← POSTROUTING chain (SNAT here)
          │
          ▼
     NIC TX ring
```

Each Netfilter hook is a linked list of `nf_hook_ops` structs, traversed for every packet.
Modern kernels use `nftables` instead of `iptables`, but the hook points are identical.

**eBPF and Netfilter**: tc-bpf (traffic control BPF) hooks run BEFORE Netfilter in the
ingress path and AFTER Netfilter in the egress path. Cilium uses tc-bpf hooks to implement
its network policy, NAT, and load balancing WITHOUT traversing Netfilter, dramatically
reducing per-packet overhead.

---

# Part V: The Full Transmit Path

## Chapter 5: Socket to Wire

### 5.1 TX Path Overview

```
Application write() / sendmsg() / sendfile() → kernel TX path:

  Application: write(fd, buf, len)
        │
        ▼
  VFS layer → sock_sendmsg()
        │
        ▼
  TCP: tcp_sendmsg()
        │ (for each chunk up to MSS or sndbuf limit)
        ▼
  sk_stream_alloc_skb()  ← allocate sk_buff
  skb_add_data() or
  skb_copy_to_page()     ← copy from user, or map page (sendfile)
        │
        ▼
  sk_buff joins tcp_write_queue (sk->sk_write_queue)
        │
        ▼
  tcp_push() → tcp_write_xmit()
        │ congestion control, nagle, retransmit timer
        ▼
  tcp_transmit_skb()
        │ TCP header built via skb_push
        ▼
  ip_queue_xmit()
        │
        ▼
  NF_INET_LOCAL_OUT (netfilter)
        │
        ▼
  ip_output() → ip_finish_output()
        │ fragmentation if needed
        ▼
  NF_INET_POST_ROUTING (netfilter SNAT)
        │
        ▼
  ip_finish_output2()
        │ ARP resolution → neighbour lookup
        ▼
  dev_queue_xmit()
        │
        ▼
  tc egress (qdisc enqueue)
  [pfifo_fast / tbf / fq / cake / etc.]
        │
        ▼
  qdisc dequeue → net_device->ndo_start_xmit()
        │ (driver xmit function)
        ▼
  Driver:
    dma_map_skb() → map linear + frags to DMA
    fill TX descriptors
    advance TDT (doorbell to NIC)
        │
        ▼
  NIC DMA engine reads TX descriptors → reads from our pages → transmits
        │
        ▼
  NIC fires TX completion interrupt (or driver polls in NAPI TX)
        │
        ▼
  Driver TX cleanup: dma_unmap, kfree_skb()
```

### 5.2 Qdisc — Traffic Control and Bufferbloat

The qdisc (queuing discipline) sits between the protocol stack and the NIC TX ring.
It is the mechanism for rate limiting, prioritization, and AQM (Active Queue Management):

```
Qdisc architecture:

  dev_queue_xmit(skb)
       │
       ▼
  netdev_core_pick_tx()   ← selects TX queue (based on XPS / flow hash)
       │
       ▼
  __dev_xmit_skb()
       │
       ▼
  qdisc->enqueue(skb, qdisc, &to_free)
  ┌────────────────────────────────────────┐
  │  pfifo_fast: simple FIFO, 3 bands      │
  │  fq:         fair queuing per-flow     │
  │  tbf:        token bucket (rate limit) │
  │  cake:       smart AQM + shaping      │
  │  fq_codel:   FQ + CoDel AQM          │
  └────────────────────────────────────────┘
       │
       ▼
  qdisc->dequeue() → net_device->ndo_start_xmit()
       │
       ▼
  NIC TX ring

  Bufferbloat connection:
    Large qdisc queues + slow links = high latency
    CoDel / fq_codel / cake measure sojourn time (time in queue)
    Drop or ECN-mark packets that have waited too long
    Keeps queue depth proportional to actual bandwidth
```

### 5.3 sk_buff Memory During TX — Who Owns What

```
TX sk_buff lifetime:

  Phase 1: Creation (tcp_sendmsg)
    skb = alloc_skb(header_size, GFP_KERNEL)  // descriptor + linear area
    skb_add_data_nocache(skb, ubuf, len)       // copy from userspace
    OR (for sendfile):
    skb_fill_page_desc(skb, page, offset, len) // map page, no copy!
  
  Phase 2: Stack processing (add headers)
    skb_push(skb, tcp_hdr_len)    // TCP header in headroom
    skb_push(skb, ip_hdr_len)     // IP header in headroom
    skb_push(skb, eth_hdr_len)    // Ethernet header in headroom
  
  Phase 3: At qdisc
    skb held in qdisc queue
    sk->sk_wmem_alloc -= skb->truesize  // when sk drops ownership
    sk->sk_sndbuf limits how much can be queued
  
  Phase 4: At driver (after ndo_start_xmit)
    sk_buff's data pages DMA-mapped, descriptor posted to NIC
    sk_buff still allocated — NIC might need retransmit
  
  Phase 5: TX completion
    dev_consume_skb_any(skb)      // refcount drop
    OR dev_kfree_skb_any(skb)    // if dropped (error)
    → if refcount reaches 0: kfree_skb() chain runs
    DMA unmap, page fragment release, descriptor freed
```

---

# Part VI: Protocol-Layer Buffers — Frame, Packet, Segment

## Chapter 6: The Buffer Vocabulary in Precise Detail

### 6.1 The Ethernet Frame Buffer (L2)

An "Ethernet frame" is what the NIC's MAC layer assembles from the wire. It includes:

```
Ethernet Frame Structure (IEEE 802.3):

  0        6        12   14              (14+len)    (14+len+4)
  ┌────────┬────────┬────┬───────────────┬──────────┐
  │ DST MAC│ SRC MAC│Type│   Payload     │ FCS/CRC  │
  │ 6 bytes│ 6 bytes│ 2B │  46-1500 bytes│ 4 bytes  │
  └────────┴────────┴────┴───────────────┴──────────┘
  
  Type field (EtherType):
    0x0800 = IPv4
    0x0806 = ARP
    0x8100 = 802.1Q VLAN tagged
    0x86DD = IPv6
    0x8847 = MPLS unicast
    0x88A8 = 802.1ad (QinQ, double VLAN)

  With 802.1Q VLAN tag (4 extra bytes):
  ┌────────┬────────┬──────────────────┬────┬──────────────────┬──────┐
  │ DST MAC│ SRC MAC│ 0x8100 (VLAN tag)│VLAN│ Inner EtherType │ data │
  │ 6 bytes│ 6 bytes│    2 bytes        │ 2B │    2 bytes      │      │
  └────────┴────────┴──────────────────┴────┴──────────────────┴──────┘
  VLAN field: 3-bit PCP | 1-bit DEI | 12-bit VID (VLAN ID)

  In sk_buff:
    skb->mac_header points to DST MAC
    skb->protocol   = ETH_P_IP (after eth_type_trans strips Ethernet)
    skb->vlan_tci   = VLAN tag if hardware stripped it
    FCS is NOT included in sk_buff — NIC strips it before DMA
    sk_buff->data length does NOT include FCS
```

**Jumbo frames**: When Jumbo Frames are enabled (MTU 9000), the Ethernet payload can be
up to 9000 bytes. The `sk_buff` still represents this as a single entity, but:
- The linear area typically holds only headers
- The actual payload lives in page fragments (skb_shared_info)
- The NIC must support Jumbo frames at the hardware level

### 6.2 The IP Packet Buffer (L3)

```
IPv4 Header (minimum 20 bytes, max 60 bytes with options):

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |Version|  IHL  |    DSCP   |ECN|         Total Length          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |         Identification        |Flags|      Fragment Offset     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Time to Live |    Protocol   |         Header Checksum       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                       Source Address                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    Destination Address                         |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    Options                    |    Padding     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  
  Key fields for sk_buff/routing:
  
  Total Length:      skb->len (after MAC strip) == iph->tot_len
  Protocol:          IP_P_TCP (6), IP_P_UDP (17), IP_P_ICMP (1)
  DSCP/ECN:          used by tc for QoS classification
                     ECN bits used by CoDel for congestion notification
  Flags/Frag Offset: used for IP fragmentation/reassembly
                     DF bit = Don't Fragment (PMTUD requirement)

IPv4 sk_buff state after ip_rcv():
  skb->network_header → iphdr
  skb->data           → points PAST iphdr (at transport header)
  ip_hdr(skb)         = (struct iphdr *)(skb->head + skb->network_header)
```

```
IPv6 Header (fixed 40 bytes + extension headers):

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |Version| Traffic Class |           Flow Label                  |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |         Payload Length        |  Next Header  |   Hop Limit   |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  +                         Source Address                        +
  |                        (128 bits)                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                                                               |
  +                      Destination Address                      +
  |                        (128 bits)                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  
  Next Header: same as IPv4 Protocol field, but also identifies extension headers
    0:  Hop-by-Hop Options
    43: Routing Header
    44: Fragment Header
    50: ESP (IPsec)
    51: AH (IPsec)
    59: No Next Header
    60: Destination Options
    6:  TCP
    17: UDP
  
  Flow Label: Kernel sets skb->hash from this + src/dst addresses
              NIC RSS engine uses the hash for queue selection
```

### 6.3 The TCP Segment Buffer (L4)

```
TCP Header:

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |          Source Port          |       Destination Port        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                        Sequence Number                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    Acknowledgment Number                      |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Data |           |U|A|P|R|S|F|                               |
  | Offset| Reserved  |R|C|S|S|Y|I|            Window            |
  |       |           |G|K|H|T|N|N|                               |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |           Checksum            |         Urgent Pointer        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    Options    |    Padding                    |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                             data                              |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

TCP sk_buff in the send queue:

  struct tcp_skb_cb *tcb = TCP_SKB_CB(skb);
  
  The send queue (sk->sk_write_queue) holds sk_buffs whose data
  is in USER space originally but has been copied (or referenced via sendfile).
  
  Each sk_buff in the send queue corresponds to one or more TCP segments.
  With GSO: one sk_buff can represent multiple segments (up to 64KB).
  
  TCP sequence space relationship:
  
  skb->seq     = first byte's sequence number
  skb->end_seq = last byte's sequence number + 1
  skb->len     = end_seq - seq (for non-SYN/FIN segments)
  
  TCP retransmit: DOES NOT COPY sk_buff — uses skb_clone() on the segment
  This means the same page frames are retransmitted, no copy needed.
```

### 6.4 UDP Datagram Buffer

UDP is connectionless — each `sendmsg()` creates exactly one sk_buff corresponding
to one UDP datagram:

```
UDP sk_buff lifecycle:

  sendmsg() path:
    udp_sendmsg()
      → ip_make_skb()        // builds sk_buff with IP+UDP headers
      → udp_send_skb()
        → ip_send_skb()
          → ip_local_out()
          → NIC TX

  recvmsg() path:
    udp_rcv()
      → __udp4_lib_rcv()
        → sock_queue_rcv_skb()  // queues onto socket's sk_receive_queue
          → application wakes up
          → recvmsg() dequeues skb
          → skb_copy_datagram_msg() // copies from sk_buff to user buffer
          → kfree_skb()

  UDP buffer limits:
    sk->sk_rcvbuf:  receive buffer size (default: 212992 bytes)
    UDP drops packets when sk_receive_queue is full
    (unlike TCP which applies backpressure)
    sysctl: net.core.rmem_default, net.core.rmem_max
```

---

# Part VII: Offload Engines — TSO, GSO, GRO

## Chapter 7: Hardware and Software Offloads

### 7.1 The Offload Problem

A 10 Gbps link at 1500-byte MTU = ~833,000 frames/sec. At 64KB application writes,
the TCP stack must segment each write into ~45 segments. That's 37.5M segments/sec to
process in software — one segment every 26 nanoseconds. On a 3 GHz CPU, that's ~80 cycles
per segment for JUST the IP/TCP header construction. This is why offloads exist.

### 7.2 TSO — TCP Segmentation Offload (Hardware)

TSO moves TCP segmentation from the CPU to the NIC:

```
Without TSO (CPU segments):

  Application write(64KB) → TCP creates 45 x 1460-byte sk_buffs
  Each sk_buff: full IP header, full TCP header, checksum computation
  45 x dma_map, 45 x TX descriptor fills, 45 x NIC FIFO writes

With TSO (NIC segments):

  Application write(64KB) → TCP creates ONE sk_buff (64KB payload)
  One sk_buff: IP header (no total_length yet), TCP header (no checksum yet)
  skb_shared_info->gso_size   = 1460   // segment size NIC should use
  skb_shared_info->gso_segs   = 45     // number of segments
  skb_shared_info->gso_type   = SKB_GSO_TCPV4
  
  Driver sees TSO sk_buff:
    Sets TX context descriptor with MSS=1460, TCPHeader length
    Sets TSE=1 in TX data descriptor
    NIC performs: segmentation, IP total length, TCP seq numbers,
                  IP checksum, TCP checksum for EACH of 45 segments
  
  CPU savings: 44 fewer descriptor fills, 44 fewer IP/TCP header constructions,
               checksum offloaded entirely to hardware

TSO sk_buff wire format (before NIC):

  [IP header - TotLen=0] [TCP header - no checksum] [65120 bytes payload]
       │                        │
       └─ NIC fills TotLen      └─ NIC fills checksum, splits payload,
          for each segment         adjusts TCP seq for each segment
```

### 7.3 GSO — Generic Segmentation Offload (Software)

GSO is the software equivalent of TSO. When a packet reaches a device that doesn't
support TSO (a virtual device, tunnel, or software bridge), the kernel must segment it:

```
GSO in the TX path:

  sk_buff (GSO, 64KB)
       │
       ▼
  dev_queue_xmit()
       │
       ├── if device supports TSO: pass as-is (hardware does it)
       │
       └── if device does NOT support TSO:
           skb_gso_segment(skb, features)
                │
                ▼
           Returns a linked list of sk_buffs:
           skb1[1500B] → skb2[1500B] → skb3[1500B] → ... → skb45[1500B]
           Each with proper IP/TCP headers, checksums computed
                │
                ▼
           Each segment transmitted individually

GSO types (skb_shared_info->gso_type):
  SKB_GSO_TCPV4:    TCP over IPv4
  SKB_GSO_UDP_L4:   UDP segmentation (UFO)
  SKB_GSO_TCPV6:    TCP over IPv6
  SKB_GSO_GRE:      GRE tunnel (NIC can TSO through GRE)
  SKB_GSO_VXLAN:    VXLAN tunnel TSO
  SKB_GSO_GENEVE:   GENEVE tunnel TSO
  SKB_GSO_UDP_TUNNEL: Generic UDP tunnel TSO

Why GSO matters for containers/overlay networks:
  A veth pair (kernel virtual ethernet) does NOT support TSO in hardware.
  But with GSO, the kernel defers segmentation until the packet reaches
  the physical NIC (which does support TSO).
  
  Container → veth → bridge → physical NIC
  sk_buff stays as 64KB GSO skb through veth and bridge,
  only segmented (or passed as TSO) at the physical NIC.
  Saves per-segment overhead for all the virtual hops.
```

### 7.4 GRO — Generic Receive Offload (Software, RX side)

```
GRO implementation in detail:

  napi_gro_receive(napi, skb)
       │
       ▼
  dev_gro_receive(napi, skb)
       │ (iterates registered GRO handlers by protocol)
       ▼
  inet_gro_receive() → tcp4_gro_receive()
       │
       ▼
  GRO lookup: find matching sk_buff in napi->gro_list
    Match criteria:
      - Same destination MAC, source MAC
      - Same IP: src_addr, dst_addr, protocol
      - Same TCP: src_port, dst_port
      - Consecutive sequence numbers
      - Same TCP flags (no FIN, RST, URG, or unexpected options)
       │
       ├── Match found: MERGE
       │     skb_gro_pull(skb, hdr_len)       // strip headers from new skb
       │     skb_gro_merge(prev, skb)          // append to super-skb's frag_list
       │     prev->len += skb->len
       │
       └── No match: ADD to gro_list
             (start a new accumulation)
       │
       ▼
  At end of NAPI poll (napi_complete_done):
  napi_gro_flush():
    For each super-skb in gro_list:
      napi_gro_complete()
        → tcp_gro_complete()  // fix up headers
        → netif_receive_skb() // deliver merged super-skb to IP stack

GRO and VXLAN/GENEVE:
  The kernel has GRO handlers for tunnel protocols.
  VXLAN GRO: merges inner TCP flows even through UDP/VXLAN encapsulation
  This is critical for container overlay network performance.
  Without tunnel GRO: every 1500-byte inner frame goes to stack individually
  With tunnel GRO: 64KB inner GRO super-frame goes to stack once
```

### 7.5 Checksum Offloads

```
Checksum handling in sk_buff (skb->ip_summed):

  CHECKSUM_NONE:
    No checksum computed yet.
    Stack must compute it fully in software.
    
  CHECKSUM_PARTIAL:
    TX path: stack has filled checksum field with pseudo-header checksum.
    NIC should add IP/TCP payload checksum and store in header.
    (NIC offload: TXCSUM)
    
  CHECKSUM_COMPLETE:
    RX path: NIC has computed checksum over entire L4 payload and stored
    in skb->csum. Stack can verify with __skb_checksum_complete().
    Saves CPU from iterating payload bytes.
    
  CHECKSUM_UNNECESSARY:
    NIC has verified checksum and confirmed it is correct.
    Stack can skip ALL checksum verification.
    (Most production NICs set this via RXCSUM offload)
    
Hardware checksum offload impact:
  At 10 Gbps with 1500-byte MTU: 833K frames/sec
  Checksum computation: ~5 cycles/byte × 1500 bytes = 7500 cycles/frame
  7500 × 833K = 6.25 billion cycles/sec = 2 entire CPU cores
  Offloading checksum to NIC frees those 2 cores for application work
```

---

# Part VIII: Fast Paths — XDP and AF_XDP

## Chapter 8: XDP — eXpress Data Path

### 8.1 XDP Position in the Stack

XDP is a programmable packet processing hook at the EARLIEST possible point in
the receive path — before `sk_buff` allocation. This is its defining property:
it operates on raw DMA buffers.

```
XDP position relative to full stack:

  NIC DMA completes (frame in page)
       │
       ▼
  XDP program runs  ◄──── THIS IS XDP'S HOOK POINT
  (before sk_buff allocation, before any kernel networking code)
       │
       ├── XDP_DROP:    frame discarded, page recycled immediately
       │                (cannot reach the kernel at all)
       │
       ├── XDP_PASS:    continue to normal sk_buff creation and stack
       │
       ├── XDP_TX:      transmit frame back out the same NIC
       │                (without going through full TX stack)
       │
       ├── XDP_REDIRECT: redirect to another NIC, CPU, or AF_XDP socket
       │                  (via bpf_redirect, bpf_redirect_map)
       │
       └── XDP_ABORTED: drop + trace (bug in BPF program)
       │
  (only XDP_PASS continues here)
       │
       ▼
  NAPI poll continues: build_skb(), netif_receive_skb()...
  (full kernel networking stack)
```

### 8.2 XDP Context — struct xdp_buff

XDP programs do NOT receive an `sk_buff`. They receive an `xdp_buff`:

```c
struct xdp_buff {
    void *data;          // points to start of packet data (past headroom)
    void *data_end;      // end of packet data
    void *data_meta;     // metadata area before data (for passing state to sk_buff)
    void *data_hard_start; // start of the page (for headroom adjustment)
    struct xdp_rxq_info *rxq; // RX queue info (interface, queue index, mem model)
    struct xdp_txq_info *txq; // TX queue info (for XDP_TX)
    u32 frame_sz;        // frame size (typically PAGE_SIZE)
};
```

```
xdp_buff memory layout:

  ┌───────────────────────────────────────────────────────────────┐
  │                    One 4096-byte page                          │
  │                                                                │
  │  data_hard_start  data_meta    data              data_end      │
  │       │               │          │                    │        │
  │       ▼               ▼          ▼                    ▼        │
  │  ┌────┬──────────────┬───────────────────────────┬───────┐    │
  │  │    │  XDP meta    │     PACKET DATA            │       │    │
  │  │    │  (optional,  │  [ETH][IP][TCP][payload]   │       │    │
  │  │    │   32 bytes)  │                            │       │    │
  │  └────┴──────────────┴───────────────────────────┴───────┘    │
  │  ▲ NET_SKB_PAD headroom                                ▲ tail  │
  └───────────────────────────────────────────────────────────────┘

  XDP program accesses packet:
    void *eth = data;                           // Ethernet header
    struct ethhdr *eth_hdr = data;
    if (eth_hdr + 1 > data_end) return XDP_DROP; // bounds check (verifier requires)
    
    void *ip = data + sizeof(*eth_hdr);
    struct iphdr *iph = ip;
    if (iph + 1 > data_end) return XDP_DROP;
    
  XDP metadata (for passing state to tc-bpf or sk_buff->cb):
    bpf_xdp_adjust_meta(xdp_md, -sizeof(my_meta))  // reserve meta space
    struct my_meta *meta = data_meta;
    meta->timestamp = bpf_ktime_get_ns();
    // This meta is preserved when XDP_PASS promotes to sk_buff
    // tc-bpf can read it via skb_metadata_ptr()
```

### 8.3 XDP Driver Modes

```
XDP Driver Modes — performance hierarchy:

  1. NATIVE XDP (fastest, requires driver support):
     - XDP program runs in NAPI poll context
     - Before build_skb() — NO sk_buff allocated yet
     - Driver recycling: XDP_DROP recycles the page immediately
     - XDP_TX uses a dedicated TX ring
     - Drivers: i40e, ixgbe, mlx5, bnxt, ice, nfp, virtio_net, tun
     - Latency: typically 20-100ns
  
  2. OFFLOADED XDP (fastest possible, rare):
     - XDP program compiled and loaded onto NIC's NPU/FPGA
     - Packet never enters host CPU for XDP actions
     - Only Netronome SmartNICs support this
     - CPU usage: 0 for XDP_DROP/XDP_TX at line rate
  
  3. GENERIC XDP (fallback, any device):
     - XDP program runs AFTER sk_buff allocation
     - Implemented in netif_receive_skb() before protocol handlers
     - No performance benefit for DROP (sk_buff already allocated)
     - Useful for development/testing XDP programs on any device
     - NOT for production use on data plane

XDP performance benchmark reference points:
  Generic XDP DROP:  ~2-4M pps (same as iptables DROP)
  Native XDP DROP:   ~14-24M pps per core (no sk_buff overhead)
  Native XDP TX:     ~10-20M pps bidirectional
  Native XDP with AF_XDP: user-space gets packet without copy
```

### 8.4 AF_XDP — Zero-Copy to User Space

AF_XDP is a socket type that allows XDP programs to redirect packets directly to
user-space memory — bypassing the kernel network stack entirely:

```
AF_XDP Architecture:

  NIC DMA → page pool → XDP program → bpf_redirect_map(xsks_map) → AF_XDP socket
                                                                           │
                                                              User space reads here
                                                              (zero-copy, no syscall per packet)

  Shared memory regions between kernel and user space:

  ┌──────────────────────────────────────────────────────────────────────┐
  │                    UMEM (User Memory — registered with kernel)        │
  │                                                                        │
  │  Divided into fixed-size chunks (e.g., 4096 bytes each)               │
  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                  │
  │  │ frm │ frm │ frm │ frm │ frm │ frm │ frm │ frm │ ...               │
  │  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │                  │
  │  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                  │
  │  ▲ mmap()'d by user space, also accessible by kernel/NIC via DMA     │
  └──────────────────────────────────────────────────────────────────────┘

  Four rings (all mmap()'d by user space):
  ┌─────────────────────┐   ┌─────────────────────┐
  │  FILL Ring (RX)      │   │  COMPLETION Ring(TX) │
  │  User → Kernel       │   │  Kernel → User       │
  │  "here are empty     │   │  "TX complete, you   │
  │   frames for NIC RX" │   │   can reuse these"   │
  └─────────────────────┘   └─────────────────────┘
  ┌─────────────────────┐   ┌─────────────────────┐
  │  RX Ring             │   │  TX Ring             │
  │  Kernel → User       │   │  User → Kernel       │
  │  "packet arrived at  │   │  "please transmit    │
  │   this frame offset" │   │   this frame"        │
  └─────────────────────┘   └─────────────────────┘

  RX flow (zero-copy):
    User fills FILL ring with UMEM frame offsets (empty buffers)
    NIC DMAs directly into UMEM frame (no kernel buffer, no copy)
    XDP redirects to AF_XDP: descriptor posted to RX ring
    User polls RX ring (recvmsg or ring via mmap)
    User reads packet at UMEM frame offset (direct memory read!)
    User posts frame offset back to FILL ring
```

---

# Part IX: CNI and Container Networking

## Chapter 9: How Containers Use sk_buff

### 9.1 Network Namespaces — The Isolation Boundary

Network namespaces are the kernel mechanism that gives each container its own
isolated view of the network stack. Each namespace has:

```
Network namespace contents:

  struct net {
    struct list_head    list;           // linked list of all netns
    struct net_device  *loopback_dev;  // lo interface
    struct netns_ipv4   ipv4;          // IPv4 config (route table, sysctl)
    struct netns_ipv6   ipv6;          // IPv6 config
    struct sock        *rtnl;          // RTNL socket for this netns
    
    /* Per-namespace device list */
    struct list_head    dev_base_head;  // all net_devices in this namespace
    
    /* Per-namespace routing tables */
    struct fib_table   *fib_main;      // main routing table
    struct fib_table   *fib_default;   // default routing table
    
    /* Per-namespace conntrack */
    struct netns_ct    ct;
    
    /* Per-namespace eBPF */
    struct netns_bpf   bpf;
  };

Key invariant: sk_buff->dev->nd_net == skb's current network namespace
When a packet crosses a namespace boundary (via veth, etc.),
dev->nd_net changes — this is checked by the kernel for correctness.
```

### 9.2 veth — Virtual Ethernet Pair

A veth pair is two virtual network interfaces connected in the kernel. What is sent
on one end is received on the other — like a cross-over cable, but purely in kernel memory:

```
veth pair: no physical NIC, no DMA, no interrupts

  Container netns:          Host netns:
  ┌───────────────────┐    ┌───────────────────────────────────┐
  │  eth0 (veth end)  │    │  vethXXXXXX (host end)           │
  │  net_device A     │◄──►│  net_device B                     │
  │  in_netns=C       │    │  in_netns=H                       │
  └───────────────────┘    └───────────────────────────────────┘
         │                            │
  virtual NIC                   virtual NIC
  (no hardware)                 (no hardware)

veth TX path (container sends packet):
  Container sk_buff
       │
       ▼
  veth_xmit(skb, dev_A)         // ndo_start_xmit for veth
       │
       ▼
  skb->dev = dev_B              // switch device to peer end
       │
       ▼
  netif_rx(skb) or
  napi_schedule (if GRO enabled)
       │ (now in host netns, device = vethXXXXXX)
       ▼
  __netif_receive_skb()
       │ (full kernel RX path in host netns)
       ▼
  host network stack or bridge

veth memory behavior:
  NO DMA involved — sk_buff crosses namespace boundary by pointer swap
  NO copy — same sk_buff, only skb->dev changes
  skb->skb_iif is updated to reflect incoming interface
  
  Performance implication:
    veth at line rate: ~10-15M pps per pair (CPU limited)
    Each packet: ~100-200ns processing time
    Bottleneck: cache misses on sk_buff + TCP/IP header processing
```

### 9.3 The Linux Bridge — L2 Forwarding

Docker's default networking uses a Linux bridge (`docker0`). When packets traverse
the bridge, they follow the L2 forwarding path:

```
Docker bridge network topology:

  Container A (172.17.0.2)    Container B (172.17.0.3)
  ┌─────────┐                 ┌─────────┐
  │  eth0   │                 │  eth0   │
  └────┬────┘                 └────┬────┘
       │ veth pair                 │ veth pair
  ┌────┴────────────────────────────┴────┐
  │          docker0 (Linux bridge)       │
  │          172.17.0.1/16                │
  │  FDB: 02:42:ac:11:00:02 → veth1      │
  │       02:42:ac:11:00:03 → veth2      │
  └──────────────────┬───────────────────┘
                     │ physical nic or routing
                     ▼
               host routing

Bridge RX path for forwarded packet (A→B):
  Container A sends sk_buff with dst=172.17.0.3
       │
       ▼
  veth_xmit → sk_buff arrives at docker0 bridge port
       │
       ▼
  br_handle_frame() (Netfilter bridge hooks here: BROUTING, PRE_ROUTING)
       │
       ▼
  br_fdb_find() — look up destination MAC in Forwarding Database
       │
       ├── found: br_forward(dst_port, skb)
       │         → delivers to veth2 (container B's veth end)
       │
       └── not found: br_flood() — flood to all ports
       
  Bridge sk_buff flow:
    skb->dev = docker0 bridge device (briefly)
    skb->dev = veth2 (after forwarding decision)
    No IP routing involved (L2 forwarding within same subnet)
```

### 9.4 Overlay Networks — VXLAN Encapsulation

Kubernetes uses overlay networks (Flannel, Calico, Weave) when pods on different
nodes need to communicate. VXLAN is the most common overlay:

```
VXLAN Encapsulation (RFC 7348):

  Inner packet (pod A to pod B, different nodes):
  ┌──────────────┬─────────┬─────────┬──────────────┐
  │ Inner Eth hdr│Inner IP │Inner TCP│  App Payload  │
  │  (pod MACs)  │(pod IPs)│         │               │
  └──────────────┴─────────┴─────────┴──────────────┘

  After VXLAN encapsulation (on node 1):
  ┌──────────┬─────────┬─────┬────────────┬──────────────────────────────────────┐
  │Outer Eth │Outer IP │Outer│   VXLAN    │              Inner Frame              │
  │(node MACs│(node IPs│ UDP │  Header    │  (entire inner Eth frame)             │
  │          │         │8472 │  8 bytes   │                                       │
  └──────────┴─────────┴─────┴────────────┴──────────────────────────────────────┘

VXLAN header (8 bytes):
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |R|R|R|R|I|R|R|R|            Reserved                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                VXLAN Network Identifier (VNI) |   Reserved    |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  I bit = 1: VNI field is valid
  VNI: 24-bit identifier (up to 16M virtual networks)
       Kubernetes uses VNI to separate pod networks

VXLAN sk_buff transformation on TX (node 1):

  Step 1: Pod A sends sk_buff (inner packet)
    [Inner Eth][Inner IP][TCP][data]
    skb->dev = pod-A-veth
  
  Step 2: Host routing: dst=10.200.2.0/24 → via VXLAN device vxlan0
    skb->dev = vxlan0
  
  Step 3: vxlan_xmit() builds outer headers:
    skb_push(skb, sizeof(struct vxlanhdr))   // VXLAN header
    skb_push(skb, sizeof(struct udphdr))     // outer UDP
    skb_push(skb, sizeof(struct iphdr))      // outer IP (node IPs)
    skb_push(skb, sizeof(struct ethhdr))     // outer Ethernet
    
    skb->inner_mac_header    = saved inner eth offset
    skb->inner_network_header = saved inner IP offset
    skb->inner_transport_header = saved inner TCP offset
    skb->encapsulation = 1                   // sk_buff knows it's encapsulated
  
  Step 4: sk_buff transmitted via physical NIC
    [Outer Eth][Outer IP 4789][UDP VXLAN VNI][Inner Eth][Inner IP][TCP][data]

VXLAN sk_buff on RX (node 2):
  
  Physical NIC receives outer frame
       │
       ▼
  UDP socket receives (port 4789)
       │
       ▼
  vxlan_rcv() → strip outer headers
    skb_pull(skb, VXLAN_HLEN + sizeof(udphdr))
       │
       ▼
  netif_rx(skb) with skb->dev = vxlan0
       │
       ▼
  VNI lookup → forward to correct pod namespace
       │
       ▼
  Inner Ethernet/IP/TCP processing in pod-B netns
```

### 9.5 GENEVE — Generic Network Virtualization Encapsulation

GENEVE (RFC 8926) is the evolution of VXLAN, used by Cilium, OVN, and VMware NSX:

```
GENEVE Header (variable length — TLV extensions):

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |Ver|  Opt Len  |O|C|    Rsvd.  |          Protocol Type        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |        Virtual Network Identifier (VNI)       |    Reserved   |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                    Variable Length Options                     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  Opt Len: length of options in 4-byte words (allows metadata in header)
  Protocol Type: 0x6558 = Ethernet (transparent bridging)
  Options: TLV-encoded, up to 252 bytes
    - Cilium uses GENEVE options to carry security identity metadata
    - This metadata rides IN the tunnel header, not in the payload
    - Eliminates need for a separate BPF map lookup at destination

GENEVE vs VXLAN in sk_buff terms:
  VXLAN: fixed 8-byte header — simple to parse, no metadata
  GENEVE: variable header — sk_buff must carry inner_network_header and
          account for variable option length in skb->mac_len and offsets
  
  For TSO/GSO with GENEVE:
    SKB_GSO_GENEVE is a distinct GSO type
    NIC must support GENEVE offload explicitly
    Many NICs support VXLAN offload but not GENEVE offload
    → Cilium default is GENEVE for features, but may fall back to VXLAN
       for TSO offload on unsupported NICs
```

### 9.6 Cilium — eBPF Data Plane and sk_buff Bypass

Cilium replaces the Linux bridge and iptables with eBPF programs attached to tc
(traffic control) hooks. This fundamentally changes how packets traverse the kernel:

```
Standard Kubernetes packet path (with kube-proxy + iptables):

  Pod A → veth → bridge → iptables PREROUTING → route → iptables POSTROUTING → NIC
  
  Cost: 5-7 Netfilter table traversals
        ARP for every dest MAC
        Conntrack entry per connection
        NAT table lookups

Cilium packet path (eBPF replacing iptables + bridge):

  Pod A → veth → tc-bpf INGRESS hook → direct veth redirect → Pod B
  
  Pod A to Pod B (same node):
  ┌─────────────────────────────────────────────────────────────────┐
  │  Pod A sk_buff                                                   │
  │       │                                                           │
  │       ▼                                                           │
  │  veth A TX → tc-bpf program (cilium_net.c BPF bytecode)          │
  │       │                                                           │
  │       ▼                                                           │
  │  BPF: lookup dst IP in CT map (BPF_MAP_TYPE_LRU_HASH)            │
  │       check network policy (BPF_MAP_TYPE_HASH endpoint policy)   │
  │       bpf_redirect_peer(veth_B_ifindex, 0)                       │
  │       │                                                           │
  │       ▼                                                           │
  │  sk_buff delivered directly to veth B RX queue                   │
  │  (NO bridge, NO iptables traversal, NO conntrack for same-node)  │
  │       │                                                           │
  │       ▼                                                           │
  │  Pod B receives                                                   │
  └─────────────────────────────────────────────────────────────────┘

  Cross-node with GENEVE:
  Pod A → tc-bpf → GENEVE encap → physical NIC → wire
                                                    │
  Node 2: physical NIC → XDP/tc-bpf → GENEVE decap → Pod B

Cilium's use of BPF maps for sk_buff decisions:

  BPF_MAP_TYPE_LRU_HASH:   Connection tracking (replaces conntrack)
  BPF_MAP_TYPE_HASH:        Endpoint policy map (IP → security identity)
  BPF_MAP_TYPE_PROG_ARRAY:  Tail calls (different programs per endpoint)
  BPF_MAP_TYPE_PERF_EVENT_ARRAY: Drop notifications → Hubble
  BPF_MAP_TYPE_RINGBUF:     High-throughput event export
```

### 9.7 CNI Interface — How Plugin Gets Called

The CNI (Container Network Interface) spec defines how a container runtime calls
a network plugin. The plugin's job is to set up the veth pair, assign IPs, and configure
routes. CNI does NOT directly touch sk_buffs — it configures the kernel structures
that sk_buffs will traverse:

```
CNI ADD call sequence (when pod is created):

  kubelet
    │ calls container runtime (containerd/CRI-O)
    ▼
  container runtime
    │ creates network namespace: clone(CLONE_NEWNET)
    │ starts container process in new netns
    │
    ▼
  CNI plugin invocation:
    exec("/opt/cni/bin/cilium-cni") with:
    - stdin: JSON config (version, name, type, podCIDR...)
    - env: CNI_COMMAND=ADD
           CNI_CONTAINERID=<container_id>
           CNI_NETNS=/proc/<pid>/fd/4  ← path to new netns
           CNI_IFNAME=eth0             ← name to give inside container
    │
    ▼
  CNI plugin (e.g., Cilium) does:
    1. Create veth pair:
       ip link add vethXXXX type veth peer name eth0 netns <netns>
       
    2. Configure host end:
       ip link set vethXXXX up
       ip route add <pod-cidr> dev vethXXXX    // route to pod
       
    3. Configure container end (in netns):
       ip -n <netns> addr add 10.0.0.5/24 dev eth0
       ip -n <netns> link set eth0 up
       ip -n <netns> route add default via 10.0.0.1
       
    4. Load eBPF programs:
       bpf_object__load() via libbpf
       tc filter add dev vethXXXX ingress bpf obj cilium_net.o sec tc-ingress
       tc filter add dev vethXXXX egress bpf obj cilium_net.o sec tc-egress
       
    5. Update BPF maps:
       BPF map[pod_ip] = {security_identity, veth_ifindex}
    
    6. Return JSON result:
       {"cniVersion": "1.0.0",
        "interfaces": [{"name": "eth0", "sandbox": "<netns>"}],
        "ips": [{"address": "10.0.0.5/24", "gateway": "10.0.0.1"}]}
```

### 9.8 eBPF Ring Buffer — High-Throughput Packet Events

When Cilium (or any eBPF tool) needs to send packet metadata to user space, it uses
`BPF_MAP_TYPE_RINGBUF` (since Linux 5.8):

```
Ring Buffer Architecture (BPF_MAP_TYPE_RINGBUF):

  Kernel space:                      User space:
  ┌──────────────────────────────────────────────────────────┐
  │              Shared ring buffer memory                    │
  │              (mmap()'d by both kernel and user space)     │
  │                                                           │
  │  ┌────────┬────────┬────────┬────────┬────────┐          │
  │  │producer│consumer│ event1 │ event2 │ event3 │ ...      │
  │  │position│position│        │        │        │          │
  │  └────────┴────────┴────────┴────────┴────────┘          │
  │  ▲kernel-rw        ▲user-ro ▲kernel writes here          │
  └──────────────────────────────────────────────────────────┘
  
  Single-producer (kernel BPF program) — lock-free!
  Multi-consumer (user-space readers) — multiple processes can read
  
  BPF program writes event:
    void *sample = bpf_ringbuf_reserve(&events, sizeof(struct pkt_event), 0);
    if (!sample) return;  // ring full → backpressure
    
    struct pkt_event *e = sample;
    e->timestamp = bpf_ktime_get_ns();
    e->src_ip    = ip_hdr->saddr;
    e->dst_ip    = ip_hdr->daddr;
    e->direction = INGRESS;
    bpf_ringbuf_submit(sample, 0);   // consumer can now see it
  
  User-space reads (Hubble observer, tetragon, etc.):
    ring_buffer__poll(rb, 100 /* ms timeout */);
    // callback invoked for each event — zero copy from kernel
  
  Why ring buffer over perf_event_array:
    perf_event_array: per-CPU buffers, user space must aggregate
    ringbuf: single shared buffer, ordered events, lower memory overhead
    ringbuf: supports variable-length records
    ringbuf: supports in-place reservation (write directly, no memcpy)
```

---

# Part X: eBPF Integration With the Buffer Subsystem

## Chapter 10: eBPF Program Types and sk_buff Access

### 10.1 eBPF Program Types That Touch Packets

Different eBPF program types receive different contexts (xdp_buff vs sk_buff)
and have different access capabilities:

```
eBPF program types and their packet context:

  BPF_PROG_TYPE_XDP:
    Context: struct xdp_md (wraps xdp_buff)
    Hook:    Before sk_buff allocation (NAPI poll)
    Access:  data..data_end (raw bytes, bounds-checked)
    Can:     XDP_DROP, XDP_PASS, XDP_TX, XDP_REDIRECT
    Cannot:  Access sk_buff fields, socket info
    Helper:  bpf_xdp_adjust_head(), bpf_xdp_adjust_meta()
    
  BPF_PROG_TYPE_SCHED_CLS (tc-bpf):
    Context: struct __sk_buff (safe view of sk_buff)
    Hook:    tc ingress (before IP stack) or tc egress (after IP stack)
    Access:  sk_buff fields via __sk_buff (len, mark, priority, etc.)
             data..data_end for raw packet bytes
    Can:     bpf_skb_store_bytes() (modify packet)
             bpf_skb_adjust_room() (add/remove bytes)
             bpf_redirect() / bpf_redirect_neigh()
             bpf_clone_redirect()  
    Note:    Can modify packet — used by Cilium for NAT, encap/decap
    
  BPF_PROG_TYPE_SOCKET_FILTER:
    Context: struct __sk_buff
    Hook:    Attached to a socket (SO_ATTACH_BPF)
    Access:  Read-only view of packet data
    Used by: tcpdump (uses classic BPF / cBPF converted to eBPF)
    
  BPF_PROG_TYPE_CGROUP_SKB:
    Context: struct __sk_buff
    Hook:    Cgroup ingress/egress (cgroup v2 BPF_CGROUP_INET_INGRESS)
    Used by: Network policy enforcement per cgroup
    Can:     Accept (return 1) or drop (return 0) packets for cgroup
    
  BPF_PROG_TYPE_SK_SKB:
    Context: struct __sk_buff
    Hook:    Stream parser and verdict (sockmap)
    Used by: L7 load balancing, Cilium socket-level LB
    
  BPF_PROG_TYPE_KPROBE / TRACING:
    Context: Raw kernel function arguments (sk_buff * directly)
    Hook:    Arbitrary kernel function (kprobe, fentry, fexit)
    Access:  Full sk_buff structure (via bpf_probe_read_kernel)
    Used by: Debugging, packet tracing, security monitoring (Tetragon)
```

### 10.2 struct __sk_buff — The Safe eBPF View of sk_buff

eBPF programs do NOT get a raw `sk_buff *`. They get `struct __sk_buff`, which is
a verified, bounds-checked view that the verifier understands:

```c
/* From include/uapi/linux/bpf.h — what eBPF programs see */
struct __sk_buff {
    /* Read-write fields (tc-bpf can modify these): */
    __u32 len;              // total length (skb->len)
    __u32 pkt_type;         // PACKET_HOST etc.
    __u32 mark;             // skb->mark (fwmark)
    __u32 queue_mapping;    // TX queue index
    __u32 protocol;         // ETH_P_* (network layer protocol)
    __u32 vlan_present;     // is VLAN tag present?
    __u32 vlan_tci;         // VLAN tag control info
    __u32 vlan_proto;       // VLAN protocol (802.1Q / 802.1AD)
    __u32 priority;         // packet priority (QoS)
    __u32 ingress_ifindex;  // ingress net_device ifindex
    __u32 ifindex;          // net_device ifindex  
    __u32 tc_index;         // traffic control index
    __u32 cb[5];            // sk_buff->cb scratch space (5×u32)
    __u32 hash;             // flow hash
    __u32 tc_classid;       // traffic class ID
    
    /* Data access — bounds checked by verifier: */
    __u32 data;             // pointer to start of packet data
    __u32 data_end;         // pointer to end of packet data
    __u32 napi_id;          // NAPI ID
    
    /* Socket info (only for socket-attached programs): */
    __u32 family;
    __u32 remote_ip4;
    __u32 local_ip4;
    __u32 remote_ip6[4];
    __u32 local_ip6[4];
    __u32 remote_port;
    __u32 local_port;
    
    /* Data metadata (set by XDP before PASS): */
    __u32 data_meta;
    
    /* GSO info: */
    __u32 gso_segs;
    __u32 gso_size;
    
    /* Hardware timestamp: */
    __u64 hwtstamp;
};
```

### 10.3 BPF Helpers for sk_buff Modification

```
Critical BPF helpers for packet manipulation:

bpf_skb_load_bytes(skb, offset, to, len):
  Copies len bytes from sk_buff at offset into BPF stack buffer.
  Handles non-linear sk_buffs (fragments) transparently.
  Cost: O(1) for linear data, O(n) for fragmented (copies through frags)
  Use when: reading from potentially non-linear payload

bpf_skb_store_bytes(skb, offset, from, len, flags):
  Writes len bytes into sk_buff at offset.
  flags: BPF_F_RECOMPUTE_CSUM → recompute checksum after write
         BPF_F_INVALIDATE_HASH → clear flow hash (must recalc)
  Use when: modifying packet payload or headers (NAT, modification)
  WARNING: invalidates any in-progress TSO/GSO context if headers modified

bpf_skb_adjust_room(skb, len_diff, mode, flags):
  Adds or removes bytes in the packet.
  mode: BPF_ADJ_ROOM_MAC → adjust at L2 (for encap/decap)
        BPF_ADJ_ROOM_NET → adjust at L3 (for tunnel headers)
  len_diff > 0: adds headroom (for encapsulation — VXLAN/GENEVE)
  len_diff < 0: removes bytes (for decapsulation)
  Cilium uses this for GENEVE/VXLAN encap in tc-bpf

bpf_redirect(ifindex, flags):
  Redirects sk_buff to another net_device.
  flags: BPF_F_INGRESS → inject into RX path of target device
  Use: Cilium uses bpf_redirect_peer() for same-node pod-to-pod
       bypasses bridge, no L2 lookup needed

bpf_clone_redirect(skb, ifindex, flags):
  Clones (skb_clone) the packet then redirects the clone.
  Original continues processing.
  Use: packet mirroring, monitoring taps

bpf_skb_pull_data(skb, len):
  Forces linearization of sk_buff up to len bytes.
  After this, skb->data..data_end covers at least len bytes linearly.
  Cost: MAY involve memcpy if data is in fragments (expensive!)
  Use: ONLY when bpf_skb_load_bytes is insufficient
  Note: After pull_data, ctx->data and ctx->data_end are updated
```

### 10.4 Aya — eBPF in Rust

Aya is the Rust crate for writing and loading eBPF programs. Understanding how Aya
maps to the sk_buff system:

```rust
// Cargo.toml (eBPF program crate):
// [dependencies]
// aya-bpf = "0.1"
// aya-log-ebpf = "0.1"
//
// [package.metadata.bpf]
// programs = ["tc_ingress"]

// eBPF program (tc-bpf, access to __sk_buff):
#![no_std]
#![no_main]

use aya_bpf::{
    bindings::TC_ACT_OK,
    macros::classifier,
    programs::TcContext,
    helpers::bpf_skb_load_bytes,
};
use aya_bpf::bindings::ethhdr;

#[classifier]
pub fn tc_ingress(ctx: TcContext) -> i32 {
    match try_tc_ingress(ctx) {
        Ok(ret) => ret,
        Err(_) => TC_ACT_OK as i32,
    }
}

fn try_tc_ingress(ctx: TcContext) -> Result<i32, i64> {
    // ctx wraps __sk_buff — access packet data with bounds checks
    
    // Load Ethernet header
    // ctx.data() returns pointer to start of packet
    // ctx.data_end() returns pointer to end
    // Bounds check is MANDATORY — verifier rejects programs without it
    
    let eth_hdr: *const ethhdr = ctx.data() as *const _;
    
    // Verifier bounds check:
    if (eth_hdr as usize + core::mem::size_of::<ethhdr>()) > ctx.data_end() as usize {
        return Ok(TC_ACT_OK as i32); // malformed packet, pass
    }
    
    let proto = unsafe { (*eth_hdr).h_proto };
    let proto = u16::from_be(proto);
    
    // Example: drop all ARP (0x0806)
    if proto == 0x0806 {
        return Ok(aya_bpf::bindings::TC_ACT_SHOT as i32); // DROP
    }
    
    Ok(TC_ACT_OK as i32)
}

// Loader (user-space Rust, runs on host):
// Cargo.toml: aya = "0.12"

use aya::{Bpf, programs::{tc, SchedClassifier, TcAttachType}};

fn main() -> anyhow::Result<()> {
    let mut bpf = Bpf::load_file("tc_ingress.bpf.o")?;
    
    // Load program into kernel
    let program: &mut SchedClassifier = bpf
        .program_mut("tc_ingress")
        .unwrap()
        .try_into()?;
    
    program.load()?;
    
    // Attach to veth0 ingress
    program.attach("veth0", TcAttachType::Ingress)?;
    
    println!("tc-bpf attached, watching veth0 ingress");
    
    // Keep running
    std::thread::park();
    
    Ok(())
}
```

### 10.5 XDP in Aya — Working With xdp_buff

```rust
// XDP program in Aya (no sk_buff — raw DMA buffer access):
#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::xdp,
    programs::XdpContext,
};
use network_types::{
    eth::{EthHdr, EtherType},
    ip::{Ipv4Hdr, IpProto},
    tcp::TcpHdr,
};

#[xdp]
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret) => ret,
        Err(_) => xdp_action::XDP_ABORTED,
    }
}

fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = core::mem::size_of::<T>();
    
    // MANDATORY bounds check — verifier will reject without this
    if start + offset + len > end {
        return Err(());
    }
    
    Ok((start + offset) as *const T)
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    let ethhdr: *const EthHdr = ptr_at(&ctx, 0)?;
    
    if unsafe { (*ethhdr).ether_type } != EtherType::Ipv4 as u16 {
        return Ok(xdp_action::XDP_PASS); // not IPv4, pass
    }
    
    let ipv4hdr: *const Ipv4Hdr = ptr_at(&ctx, EthHdr::LEN)?;
    let src_addr = u32::from_be(unsafe { (*ipv4hdr).src_addr });
    
    // Block specific source IP (10.0.0.99)
    if src_addr == 0x0A000063 {
        return Ok(xdp_action::XDP_DROP); // drop before sk_buff allocation
    }
    
    Ok(xdp_action::XDP_PASS)
}

// XDP performance critical: XDP_DROP here means NO sk_buff allocated,
// NO IP processing, NO Netfilter traversal — raw DMA page recycled immediately.
// This is why XDP achieves 14-24M pps DROP rate vs iptables' ~2-4M pps.
```

---

# Part XI: Advanced Topics and Production Patterns

## Chapter 11: Memory Pressure and Back-Pressure

### 11.1 Socket Buffer Limits and Memory Accounting

```
Socket memory accounting hierarchy:

  System level:
    /proc/sys/net/core/rmem_max          (max receive buffer per socket)
    /proc/sys/net/core/wmem_max          (max send buffer per socket)
    /proc/sys/net/ipv4/tcp_rmem          (min/default/max TCP rcv)
    /proc/sys/net/ipv4/tcp_wmem          (min/default/max TCP snd)
    /proc/sys/net/ipv4/tcp_mem           (system-wide TCP memory)
    
  Per-socket:
    sk->sk_rcvbuf:   total bytes allowed in receive queue
    sk->sk_sndbuf:   total bytes allowed in send queue
    sk->sk_wmem_alloc: currently allocated send bytes
    sk->sk_rmem_alloc: currently allocated receive bytes
    
  sk_buff memory accounting:
    skb->truesize:  actual memory used by skb (data + struct sk_buff)
                    = sizeof(struct sk_buff) + skb->end - skb->head
    
    When sk_buff enters socket receive queue:
      sk->sk_rmem_alloc += skb->truesize
      if sk_rmem_alloc > sk_rcvbuf: DROP the packet (sk_add_backlog or drop)
    
    When application reads from socket:
      recvmsg() → skb dequeued → kfree_skb()
      → sk->sk_rmem_alloc -= skb->truesize
      → sk->sk_forward_alloc replenished → TCP sends window update

Back-pressure propagation:
  Application slow to read
    │
    ▼
  sk->sk_rmem_alloc grows toward sk_rcvbuf
    │
    ▼
  TCP: tcp_space() shrinks receive window advertisement
    │
    ▼
  Sender slows (respects receive window)
    │
    ▼
  Sender socket buffer fills
    │
    ▼
  write() blocks or returns EAGAIN (non-blocking)
    │
    ▼
  Application back-pressure propagated end-to-end
```

### 11.2 Page Pool — Efficient Buffer Recycling

Modern NIC drivers use the page pool to avoid per-packet page allocation/free overhead:

```
Page Pool Architecture (since Linux 5.0):

  Traditional (per-packet alloc/free):
    RX each packet: alloc_page() → expensive, may sleep
    RX complete: put_page() → page returned to buddy allocator
    Cost: ~1-2μs per packet for allocation alone at high rates
    
  Page Pool:
    Init: pre-allocate N pages (N = ring_size)
    RX packet: page_pool_alloc_pages() → O(1), from pool, no lock
    XDP_DROP or kfree_skb: page returned to pool, not buddy allocator
    
  Page pool memory model:
    ┌──────────────────────────────────────────────────────────────┐
    │                    Page Pool                                  │
    │                                                               │
    │  ┌──────────────────┐  ┌──────────────────────────────────┐  │
    │  │  Cache (per-CPU) │  │  Ring (SPSC — driver/NAPI uses)  │  │
    │  │  Lock-free       │  │  Lock-free                        │  │
    │  │  pages[0..cache] │  │  pages[head..tail]                │  │
    │  └──────────────────┘  └──────────────────────────────────┘  │
    │                                                               │
    │  Recycling: XDP_DROP → page returned to ring immediately     │
    │             kfree_skb → skb_free_head() → page to pool       │
    └──────────────────────────────────────────────────────────────┘
    
  Page pool with DMA:
    Pages are pre-mapped for DMA at pool creation
    DMA address cached in page->dma_addr (or xdp_rxq_info)
    No dma_map_page() per packet — massive overhead reduction
```

### 11.3 sk_buff Slab Cache

`sk_buff` descriptors (~240 bytes each) are not individually kmalloc'd. They come
from a dedicated SLAB cache for performance:

```
SLAB/SLUB cache for sk_buff:

  Global slab: "skbuff_head_cache" (see net/core/skbuff.c)
    Size:  sizeof(struct sk_buff) ≈ 240 bytes on x86_64
    Align: hardware cache line (64 bytes) aligned
    
  Allocation: alloc_skb(size, gfp) → kmem_cache_alloc(skbuff_head_cache)
  Free:       kfree_skb() → kmem_cache_free(skbuff_head_cache, skb)
  
  Why a dedicated slab?
    1. No fragmentation: all objects same size → no internal fragmentation
    2. Per-CPU magazines: most alloc/free without lock
    3. Warm cache: recently freed sk_buff descriptor may be in L1/L2
    4. SLUB debugging: can track allocation sites per-skb for debugging
  
  For GRO and large workloads:
    napi_alloc_skb() uses a NAPI-local cache to avoid slab entirely
    for the hot allocation path (no lock, no slab overhead)
```

## Chapter 12: Kernel Source Reference Map

### 12.1 Key Files in the Kernel Tree

```
net/core/skbuff.c      — sk_buff allocation, clone, copy, push/pull/put/trim
                          skb_shared_info management, GRO core
                          
net/core/dev.c         — netif_receive_skb(), dev_queue_xmit()
                         napi_schedule(), net_rx_action() softirq
                         __netif_receive_skb(), packet_type delivery
                         
net/core/filter.c      — eBPF filter attachment, sk_filter(), BPF helpers
                         bpf_skb_load_bytes(), bpf_skb_store_bytes()
                         
net/ipv4/ip_input.c    — ip_rcv(), ip_local_deliver(), ip_forward()
net/ipv4/ip_output.c   — ip_output(), ip_finish_output(), fragmentation
net/ipv4/tcp.c         — tcp_sendmsg(), tcp_recvmsg()
net/ipv4/tcp_input.c   — tcp_v4_rcv(), GRO path
net/ipv4/tcp_output.c  — tcp_write_xmit(), tcp_transmit_skb()

drivers/net/veth.c     — veth_xmit(), veth_poll() (virtual ethernet)
drivers/net/tun.c      — tun/tap device (VM networking)
net/ipv4/udp_tunnel.c  — common UDP tunnel helpers (VXLAN/GENEVE share this)
net/ipv4/udp_tunnel_nic.c — NIC offload for UDP tunnels (TSO for VXLAN)
drivers/net/vxlan/    — VXLAN driver and encap/decap
net/ipv6/ip6_tunnel.c  — IPv6-in-IPv6 tunneling
net/xdp/xsk.c         — AF_XDP socket implementation
net/xdp/xsk_buff_pool.c — UMEM buffer pool for AF_XDP

include/linux/skbuff.h — FULL sk_buff structure, ALL accessor macros
include/linux/netdevice.h — net_device structure, NAPI structure
include/linux/bpf.h    — BPF program types, map types, helper prototypes
include/uapi/linux/bpf.h — __sk_buff, xdp_md, BPF helper numbers

kernel/bpf/verifier.c — verifier: bounds checking, register tracking
net/core/xdp.c        — XDP redirect, XDP frame lifecycle
```

### 12.2 Key Functions and Their Locations

```
sk_buff lifecycle:

  alloc_skb(size, gfp)              → net/core/skbuff.c:594
  build_skb(data, frag_size)        → net/core/skbuff.c:514
  napi_alloc_skb(napi, length)      → net/core/skbuff.c:554
  __netdev_alloc_skb(dev, len, gfp) → net/core/skbuff.c:535
  kfree_skb(skb)                    → net/core/skbuff.c:851
  skb_clone(skb, gfp)               → net/core/skbuff.c:1527
  skb_copy(skb, gfp)                → net/core/skbuff.c:1591
  skb_linearize(skb)                → net/core/skbuff.c:1754
  pskb_expand_head(skb, nhead, ntail, gfp) → net/core/skbuff.c:1836
    (reallocates head area for more headroom/tailroom)

RX path:
  napi_gro_receive(napi, skb)        → net/core/dev.c:5754
  dev_gro_receive(napi, skb)         → net/core/dev.c:5574
  __netif_receive_skb(skb)           → net/core/dev.c:5340
  ip_rcv(skb, dev, pt, orig_dev)     → net/ipv4/ip_input.c:555
  tcp_v4_rcv(skb)                    → net/ipv4/tcp_ipv4.c:1951
  
TX path:
  dev_queue_xmit(skb)               → net/core/dev.c:4251
  __dev_queue_xmit(skb, sb_dev)     → net/core/dev.c:4145
  ip_output(net, sk, skb)           → net/ipv4/ip_output.c:415
  tcp_write_xmit(sk, mss_now, ...)  → net/ipv4/tcp_output.c:2456
  
XDP:
  bpf_prog_run_xdp(prog, xdp)       → include/linux/filter.h
  xdp_do_redirect(dev, xdp, prog)   → net/core/xdp.c:780
  xsk_rcv(xs, xdp)                  → net/xdp/xsk.c
```

---

# Appendix A: Complete ASCII Reference — sk_buff in Context

## A.1 sk_buff Lifecycle State Machine

```
sk_buff State Transitions:

              alloc_skb()
              build_skb()
                  │
                  ▼
             [ALLOCATED]
             users=1, dataref=1
                  │
         ┌────────┴────────────┐
         │                     │
     skb_clone()           (no clone)
         │                     │
         ▼                     │
     [CLONED]                  │
     dataref=2                 │
     (shared data)             │
         │                     │
         │      ┌──────────────┘
         │      │
         ▼      ▼
       [IN QUEUE]
       (sk_receive_queue, tx_queue, GRO list, etc.)
         │
         ▼
       [PROCESSING]
       (in protocol handler, in eBPF, in application copy)
         │
    ┌────┴────┐
    │         │
    ▼         ▼
[kfree_skb] [skb_get()]
(consume)   (additional ref)
    │
    ▼
[FREED]
(desc to slab, data to page pool or buddy)
```

## A.2 Packet Flow Through the Kernel — Complete View

```
PHYSICAL NIC
   │ (PHY receives signal → MAC assembles frame → DMA to RAM)
   ▼
DMA RING BUFFER (in DRAM, pre-allocated by driver)
   │ NIC writes frame, sets DD=1, fires MSI-X interrupt
   ▼
HARD IRQ (driver irq handler, IRQs disabled)
   │ ack interrupt, disable NIC interrupt, napi_schedule()
   ▼
SOFT IRQ (NET_RX_SOFTIRQ, same CPU as IRQ)
   net_rx_action() → driver napi_poll()
   │
   ├─ XDP program (if attached, native mode)
   │    XDP_DROP  → recycle page, skip sk_buff
   │    XDP_TX    → transmit immediately
   │    XDP_REDIRECT → AF_XDP or other NIC
   │    XDP_PASS  → continue
   │
   ▼
build_skb() / napi_alloc_skb()
   │ wraps DMA page in sk_buff descriptor
   ▼
napi_gro_receive() → GRO coalescing
   │ merges TCP segments for same flow
   ▼
__netif_receive_skb()
   │
   ├─ AF_PACKET taps (tcpdump/Wireshark)
   ├─ tc ingress (BPF classifiers, Cilium policy)
   ├─ bridge forwarding (if device is bridge port)
   │
   ▼
ip_rcv() [NF_INET_PRE_ROUTING]
   │ IP header validation, conntrack
   ▼
ROUTING DECISION (fib_lookup)
   │
   ├─ LOCAL: ip_local_deliver()
   │    [NF_INET_LOCAL_IN]
   │    protocol demux (TCP/UDP/ICMP)
   │    tcp_v4_rcv()
   │    sk_receive_queue
   │    application recvmsg()
   │
   └─ FORWARD: ip_forward()
        [NF_INET_FORWARD]
        ip_output()
        [NF_INET_POST_ROUTING]
        NIC TX →

SOCKET SEND:
   application write()/sendmsg()
   tcp_sendmsg() → sk_write_queue
   tcp_write_xmit() → ip_queue_xmit()
   [NF_INET_LOCAL_OUT]
   ip_output() → dev_queue_xmit()
   qdisc (pfifo_fast / fq / tbf)
   ndo_start_xmit() (driver)
   TX descriptor fill, doorbell to NIC
   NIC DMA reads pages, transmits
   TX completion interrupt → kfree_skb()
```

---

# Appendix B: Failure Modes and Security Implications

## B.1 sk_buff Failure Modes

```
1. COMPILE-TIME failures:
   - Accessing sk_buff fields in eBPF without __sk_buff abstraction
     → verifier rejects: "invalid mem access 'inv'"
   - Missing bounds check before data access in XDP/tc-bpf
     → verifier rejects: "invalid variable-offset read"
   - Writing to read-only __sk_buff fields in XDP programs
     → verifier rejects: "cannot write into ctx"

2. RUNTIME panics:
   - Double-free: kfree_skb() on skb with users > 1 then decrement → 
     underflow → BUG() in debug builds
   - Use-after-free: storing sk_buff * and accessing after kfree_skb()
     → memory corruption, potential kernel exploit
   - skb_push() past head: extending data pointer before head
     → corrupts memory before the buffer → OOPS
   - skb_put() past tail (past end): writing past end → corruption

3. SECURITY failures:
   - cb[] not zeroed across namespace boundary:
     → Information leak: stale kernel pointers in cb[] accessible via AF_PACKET
   - sk_buff cloned across netns without sanitization:
     → Security context from one namespace visible in another
   - Non-linear sk_buff in XDP program:
     → If program assumes linear, accesses beyond data_end
     → Verifier prevents this, but generic XDP may not enforce
   - IOMMU not enabled:
     → Malicious/buggy PCIe NIC DMA-writes to arbitrary physical addresses
     → Bypasses all kernel memory protections
   - skb->sk not cleared on forwarded packet:
     → Forwarded packet retains socket ownership → wrong accounting,
       potential for sk destructor on wrong socket

4. PERFORMANCE failures:
   - skb_linearize() in hot path:
     → Every non-linear packet → memcpy → cache pressure
     → 100-200ns per packet extra latency
   - Excessive skb_clone() without page sharing:
     → Each clone allocates descriptor but shares data
     → High descriptor count → slab pressure
   - alloc_skb() in NAPI poll instead of page pool:
     → buddy allocator path → lock, cache misses → 1-2μs per packet
   - kfree_skb() in interrupt context:
     → Triggers page freeing in IRQ context → latency spike
   - Fragmented socket receive buffer:
     → sk_rmem_alloc oscillates → TCP window updates → sender rate variation

5. "It compiles but it's wrong" failures:
   - Setting skb->ip_summed = CHECKSUM_UNNECESSARY without NIC verification
     → Stack skips checksum verification → corrupt data delivered to app
   - Wrong endianness in protocol header fields:
     → htons() / ntohs() / cpu_to_be16() confusion → misrouting, misparse
   - Modifying sk_buff data after DMA mapping without cache flush:
     → dma_map_single() must happen AFTER all CPU writes to the buffer
     → Failure: NIC reads stale data from its DMA address cache
   - Not calling skb_orphan() before netns crossing:
     → sk_buff retains a reference to a socket in the wrong netns
     → Socket refcount never drops → memory leak
```

## B.2 Overlay Network Failure Modes

```
VXLAN/GENEVE specific failures:

1. MTU black hole:
   Inner MTU = outer MTU - encapsulation overhead
   VXLAN overhead:  14 (Eth) + 20 (IP) + 8 (UDP) + 8 (VXLAN) = 50 bytes
   If outer MTU = 1500, inner MTU = 1450
   If pod sets MSS = 1460 (wrong), TCP segments = 1510 bytes
   → fragmentation or packet loss
   → Fix: set correct MTU on veth/vxlan devices in CNI plugin
          or enable DF bit + PMTUD

2. GRO failure with tunnels:
   Without tunnel GRO (generic-receive-offload for VXLAN):
   Each inner frame processed individually
   → CPU load 10x higher than with GRO
   → Fix: ensure ethtool -K <dev> gro on AND kernel supports tunnel GRO

3. Checksum offload interaction:
   Inner checksum: CHECKSUM_PARTIAL (computed by inner TCP)
   Outer checksum: also CHECKSUM_PARTIAL
   NIC must support both inner and outer checksum offload simultaneously
   → Many NICs support outer only → inner checksum computed in software
   → Fix: check 'ethtool -k <dev> | grep tx-checksumming'

4. TSO through tunnels:
   SKB_GSO_VXLAN requires NIC support for tunnel TSO
   Without it: GSO segmentation happens in software
   → Each GSO super-frame splits before entering VXLAN
   → 64KB → 45 × 1450-byte segments processed in software
   → CPU bound at ~5-6M pps
   → Fix: confirm tunnel TSO: ethtool -k ens3 | grep tx-udp-tnl

5. Source port entropy:
   VXLAN source port must be flow-derived (RFC 7348 §6.3.1):
   src_port = hash(inner 5-tuple) in range 49152-65535
   If src_port is constant: ECMP load balancing fails (all flows → same path)
   → Fix: Linux uses jhash of inner headers; verify with 'ss -n'
```

---

# Appendix C: Tuning Reference

## C.1 Critical sysctl Parameters

```
# Ring buffer sizes (per-queue, driver-level):
ethtool -G eth0 rx 4096 tx 4096

# NAPI budget (packets per poll cycle):
sysctl net.core.netdev_budget=300
sysctl net.core.netdev_budget_usecs=8000

# Socket buffer sizes:
sysctl net.core.rmem_max=134217728      # 128MB max receive buffer
sysctl net.core.wmem_max=134217728      # 128MB max send buffer
sysctl net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl net.ipv4.tcp_wmem="4096 65536 134217728"
sysctl net.ipv4.tcp_mem="786432 1048576 26777216"

# GRO:
ethtool -K eth0 gro on
ethtool -K eth0 lro on   # hardware LRO (if supported)

# Checksum offloads:
ethtool -K eth0 rx-checksumming on
ethtool -K eth0 tx-checksumming on

# TSO/GSO:
ethtool -K eth0 tso on
ethtool -K eth0 gso on

# RSS queue count:
ethtool -L eth0 combined 16  # 16 queues, one per CPU core

# IRQ affinity (one IRQ per queue, pin to CPU):
# Use irqbalance or manual /proc/irq/N/smp_affinity_list

# XPS (Transmit Packet Steering) — TX queue affinity:
echo "ff" > /sys/class/net/eth0/queues/tx-0/xps_cpus

# RPS (Receive Packet Steering) — software RSS for devices without hardware RSS:
echo "ff" > /sys/class/net/eth0/queues/rx-0/rps_cpus
sysctl net.core.rps_sock_flow_entries=32768
echo 2048 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

---

# Appendix D: Connection Map

```
sk_buff connects to:

  ├── Pin<T> / async state machines:
  │     sk_buff cannot be moved once DMA-mapped (physical address is fixed)
  │     This is the physical-memory equivalent of Pin — the DMA address
  │     is the "self-referential pointer" that breaks on move
  │
  ├── Rust's Arc<T>:
  │     skb->users (atomic_t) is the kernel's equivalent of Arc refcount
  │     kfree_skb() is the equivalent of Arc::drop()
  │     skb_clone() is Arc::clone() but with a separate "data refcount" too
  │
  ├── eBPF verifier bounds checking:
  │     data..data_end in XDP/tc-bpf is the safe window the verifier enforces
  │     Every pointer derived from ctx->data must be proven < ctx->data_end
  │     This is the kernel's version of Rust's borrow checker for raw pointers
  │
  ├── RFC 7348 (VXLAN):
  │     VXLAN encapsulation is sk_buff headroom manipulation at its core:
  │     bpf_skb_adjust_room() or vxlan_xmit() calls skb_push() N times
  │
  ├── TCP RFC 9293:
  │     tcp_skb_cb.seq/end_seq fields implement TCP's byte-stream model
  │     TCP send queue (sk_write_queue) is a linked list of sk_buffs
  │     Retransmit uses skb_clone() — same pages, new descriptor
  │
  ├── POSIX sendfile(2):
  │     sendfile() → splice() → sk_buff with page fragments pointing to file pages
  │     No copy from file cache to socket buffer — pure zero-copy
  │     sk_buff data_len > 0, nr_frags > 0, pages are file page cache pages
  │
  ├── IPsec (ESP/AH):
  │     xfrm transforms the sk_buff: encrypt payload, add ESP header
  │     Uses skb_cow_data() to ensure writable linear data before encryption
  │     skb->sp (now secpath) carries IPsec state through the stack
  │
  └── io_uring / zero-copy send:
        io_uring sendmsg with IORING_OP_SEND_ZC:
        sk_buff pages are user pages, pinned with get_user_pages()
        No copy — user buffer DMA-mapped directly
        Completion notification when NIC finishes TX (page can be reused)
```

---

*Guide version: Linux 6.x kernel series*  
*Kernel source references: https://elixir.bootlin.com/linux/latest/source*  
*sk_buff structure: include/linux/skbuff.h*  
*NAPI: net/core/dev.c*  
*XDP: Documentation/networking/af_xdp.rst*  
*eBPF helpers: include/uapi/linux/bpf.h*  
*Aya crate: https://docs.rs/aya*  
*CNI spec: https://github.com/containernetworking/cni/blob/main/SPEC.md*