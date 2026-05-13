# DMA, RDMA, DMABuf & Buffer Management: A Complete In-Depth Guide

---

## Table of Contents

1. [Foundational Concepts: How Data Moves](#1-foundational-concepts-how-data-moves)
2. [DMA — Direct Memory Access](#2-dma--direct-memory-access)
3. [RDMA — Remote Direct Memory Access](#3-rdma--remote-direct-memory-access)
4. [DMABuf — DMA Buffer Sharing Framework](#4-dmabuf--dma-buffer-sharing-framework)
5. [TCP Buffers & Retransmission: How Lost Data Works](#5-tcp-buffers--retransmission-how-lost-data-works)
6. [Buffer Lifecycle: Who Owns What](#6-buffer-lifecycle-who-owns-what)
7. [Buffer Sizing: How It Is Calculated](#7-buffer-sizing-how-it-is-calculated)
8. [What Happens When a Buffer Is Full](#8-what-happens-when-a-buffer-is-full)
9. [Mental Model: The Complete Picture](#9-mental-model-the-complete-picture)

---

## 1. Foundational Concepts: How Data Moves

Before diving into DMA/RDMA/DMABuf, you need a rock-solid mental model of how data physically moves inside a computer.

### 1.1 The Classical CPU-Driven Transfer (PIO — Programmed I/O)

In the oldest computing model, the CPU is responsible for every single byte of data movement:

```
  Device                   CPU                   Memory
  ------                   ---                   ------
  [ NIC / Disk ]  --read--> [ Core ]  --write--> [ RAM ]
                 <--write-- [ Core ] <--read---  [ RAM ]
```

- CPU reads from a peripheral register (one word at a time).
- CPU writes that word into RAM.
- This burns CPU cycles entirely on data copying, starving the rest of the application.

**Problem:** A 10 Gbps NIC generates ~1.2 GB/s. The CPU has to service every byte. Modern CPUs doing PIO for high-speed NICs would spend virtually all time just moving data.

### 1.2 The Memory Hierarchy (Speeds Matter)

```
 L1 Cache   ~  0.5 ns    |████|
 L2 Cache   ~  5   ns    |████████|
 L3 Cache   ~  20  ns    |████████████████|
 RAM (DRAM) ~  60  ns    |████████████████████████████████████████|
 NVMe SSD   ~  100 µs    |[very far away]
 Network    ~  ms range  |[astronomically far]
```

Every technique covered in this guide exists to reduce the number of times data crosses this hierarchy unnecessarily. The golden rule: **copy less, pin more**.

---

## 2. DMA — Direct Memory Access

### 2.1 What Is DMA?

DMA is the mechanism that allows a hardware device (NIC, GPU, disk controller, audio card) to read from and write to system RAM **without involving the CPU** for each byte transferred.

The CPU sets up the transfer, then does other work while the DMA engine moves the data autonomously. When done, the device raises an interrupt.

```
                         System Bus / PCIe
                              │
      ┌───────────────────────┼────────────────────────┐
      │                       │                        │
  ┌───┴───┐            ┌──────┴──────┐          ┌──────┴──────┐
  │  CPU  │            │  RAM (DRAM) │          │  Device     │
  │       │            │             │          │  (NIC/GPU)  │
  │  Core │◄──control─►│ DMA Region  │◄────────►│  DMA Engine │
  │       │            │ [pinned buf]│          │             │
  └───────┘            └─────────────┘          └─────────────┘
      │
      └── CPU sets up:
            - Source address
            - Destination address
            - Transfer length
          Then WALKS AWAY.
          Device DMA engine does the rest.
          IRQ fires when done.
```

### 2.2 The IOMMU: Making DMA Safe

A device using DMA gets to read/write RAM. This is catastrophically dangerous if unrestricted — a rogue/buggy device could read your entire memory, including passwords, cryptographic keys, etc.

**IOMMU (Input-Output Memory Management Unit)** is the hardware solution:

```
  Device (NIC)
      │
      │  Issues DMA with "device virtual address" (IOVA)
      ▼
  ┌──────────┐
  │  IOMMU   │   ← Sits on the PCIe bus, between device and RAM
  │          │
  │ IOVA→PA  │   ← Translation table, set up by the OS kernel
  │ map table│
  └──────────┘
      │
      │  Translates to physical address
      ▼
  Physical RAM
```

- The kernel (via the IOMMU driver) programs which physical pages a device is allowed to access.
- If a device tries to access memory outside its allowed window → IOMMU raises a fault → kernel can kill the driver.
- Intel calls this **VT-d**. AMD calls it **AMD-Vi**. ARM calls it **SMMU**.

### 2.3 DMA Coherency Problem

CPUs have caches. When a device DMA-writes into RAM, the CPU's cache may still hold a stale copy of those pages. When a device DMA-reads from RAM, the CPU's cache may have dirty (modified) data not yet flushed.

This is the **cache coherency** problem.

**Hardware-coherent DMA** (most x86 systems): The hardware cache coherency protocol (MESI/MOESI) automatically handles this. Devices on PCIe see the same view of memory as the CPU. No software intervention needed.

**Non-coherent DMA** (many ARM SoCs, embedded): Software must explicitly:
- **Flush** (CPU → RAM) before device reads.
- **Invalidate** (discard CPU cache lines) before CPU reads from a region written by the device.

Linux kernel functions:
```c
// Coherent (automatically consistent)
dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);

// Streaming (you manage sync)
dma_map_single(dev, cpu_addr, size, DMA_TO_DEVICE);   // flush before device reads
dma_map_single(dev, cpu_addr, size, DMA_FROM_DEVICE); // invalidate before CPU reads
dma_sync_single_for_cpu(...);    // transfer ownership back to CPU
dma_sync_single_for_device(...); // transfer ownership to device
```

### 2.4 DMA Scatter-Gather

Real data is rarely contiguous in physical RAM. The kernel uses virtual memory, and pages can be scattered across physical RAM. DMA Scatter-Gather (SG) allows a single DMA operation to cover a list of non-contiguous physical memory regions:

```
Virtual buffer (contiguous in VA space):
  [-------- 16KB --------]

Physical RAM (fragmented):
  Page A: phys 0x1000  [4KB]
  Page B: phys 0x9000  [4KB]
  Page C: phys 0x3000  [4KB]
  Page D: phys 0xF000  [4KB]

Scatter-Gather List (given to DMA engine):
  entry[0]: addr=0x1000, len=4096
  entry[1]: addr=0x9000, len=4096
  entry[2]: addr=0x3000, len=4096
  entry[3]: addr=0xF000, len=4096
```

The DMA engine walks the SG list and transfers each segment in order. No need to copy to a single contiguous buffer first. This is critical for performance.

### 2.5 DMA in the Linux Kernel: Full Stack

```
  Application (userspace)
        │  write(fd, buf, len)
        ▼
  System Call (VFS layer)
        │
        ▼
  Network Stack / Block Layer
        │  builds sk_buff / bio
        ▼
  Driver (e.g., ixgbe for Intel NIC)
        │  dma_map_sg()         ← maps pages, gets IOVA
        │  writes descriptors   ← tells HW: "here's the SG list"
        ▼
  NIC Hardware
        │  DMA engine reads from RAM (using IOVA via IOMMU)
        │  Puts bits on wire
        ▼
  Wire / Network
```

---

## 3. RDMA — Remote Direct Memory Access

### 3.1 Concept and Motivation

RDMA extends DMA across a network. It allows one machine's DMA engine to read from or write to another machine's RAM, **bypassing both machines' CPUs and OS kernels** for the data path.

Classical TCP/IP has these overheads:
- Data copied from userspace → kernel socket buffer.
- Kernel builds packet headers.
- Data copied again into NIC ring buffer.
- On receiver: data copied from NIC → kernel socket buffer → userspace.
- System calls on both ends.

For 100GbE links doing HPC, storage (NVMe-oF), or AI training (all-reduce), this is too slow and too CPU-intensive.

### 3.2 RDMA Architecture

```
  Machine A (Initiator)                    Machine B (Target)
  ─────────────────────                    ─────────────────
  ┌──────────┐                             ┌──────────┐
  │  App     │                             │  App     │
  │  Buffer  │◄── App registers            │  Buffer  │◄── App registers
  │ (pinned) │    memory with RDMA NIC     │ (pinned) │    memory with RDMA NIC
  └──────────┘                             └──────────┘
       │                                        │
  ┌────┴──────┐                           ┌─────┴─────┐
  │ RDMA NIC  │◄═══════ Network ══════════►│ RDMA NIC │
  │ (HCA)     │   (InfiniBand / RoCE)      │ (HCA)    │
  └───────────┘                           └───────────┘
       │                                        │
       │ DMA read/write                         │ DMA read/write
       ▼                                        ▼
     RAM (A)                                  RAM (B)

  CPU on A is NOT involved in data movement.
  CPU on B is NOT involved in data movement.
```

**HCA** = Host Channel Adapter (the RDMA NIC).

### 3.3 Key RDMA Verbs (Operations)

RDMA has two classes of operations:

**Two-sided (both ends must post work):**
- `SEND` / `RECV`: App on A sends, app on B must have posted a Receive work request. Similar to UDP but zero-copy.

**One-sided (initiator does everything; target CPU uninvolved):**
- `RDMA READ`: Machine A's NIC reads directly from Machine B's RAM, without B's CPU doing anything.
- `RDMA WRITE`: Machine A's NIC writes directly into Machine B's RAM, without B's CPU doing anything.
- `ATOMIC` (fetch-and-add, compare-and-swap): Atomic operations on remote memory.

### 3.4 Memory Registration

Before RDMA can use a buffer, it must be **registered**:

```c
// ibverbs API (Linux)
struct ibv_mr *mr = ibv_reg_mr(
    pd,          // Protection Domain
    buf,         // virtual address
    length,      // size
    IBV_ACCESS_LOCAL_WRITE |
    IBV_ACCESS_REMOTE_READ |
    IBV_ACCESS_REMOTE_WRITE
);
// mr->lkey = local key (used by local NIC)
// mr->rkey = remote key (shared with remote, used by remote NIC to access this buffer)
```

What registration does:
1. **Pins** the pages in physical RAM (prevents the OS from swapping them out or moving them).
2. Programs the IOMMU with the IOVA→PA mappings for those pages.
3. Creates a **Memory Region (MR)** with an `lkey` (local key) and `rkey` (remote key).
4. The `rkey` is communicated out-of-band to the remote machine (e.g., via a small TCP control message), which then uses it to authorize RDMA READ/WRITE operations.

This is expensive to set up (page-table walking, IOMMU programming, TLB shootdowns). That's why registration is done once and the buffer is reused many times.

### 3.5 RDMA Transport Variants

| Transport | Full Name | Medium | Notes |
|---|---|---|---|
| InfiniBand | — | InfiniBand fabric | Native RDMA. Lossless. Dedicated hardware. Used in HPC/supercomputers. |
| RoCE v1 | RDMA over Converged Ethernet v1 | Ethernet (L2) | RDMA over Ethernet. No routing (same L2 domain). |
| RoCE v2 | RDMA over Converged Ethernet v2 | Ethernet (L3/UDP) | Routable. Uses UDP port 4791. Modern datacenter standard. |
| iWARP | Internet Wide-Area RDMA Protocol | TCP/IP | RDMA over TCP. Lossless not required. Slower than RoCE. |

```
  InfiniBand Stack:
  ─────────────────
  App (ibverbs)
      │
  IB Transport (reliable, unreliable, raw)
      │
  IB Link Layer (credit-based flow control, lossless)
      │
  Physical (copper/optical)


  RoCE v2 Stack:
  ──────────────
  App (ibverbs)
      │
  IB Transport (same as IB)
      │
  UDP / IP
      │
  Ethernet (with PFC/ECN for lossless)
      │
  Physical
```

### 3.6 Queue Pairs (QP): The Core Abstraction

RDMA communication happens through **Queue Pairs**:

```
  Machine A                              Machine B
  ─────────                              ─────────
  ┌─────────────────┐                   ┌─────────────────┐
  │  Queue Pair(QP) │                   │  Queue Pair(QP) │
  │                 │                   │                 │
  │  Send Queue(SQ) │──── network ─────►│  Recv Queue(RQ) │
  │  Recv Queue(RQ) │◄─── network ──────│  Send Queue(SQ) │
  └─────────────────┘                   └─────────────────┘
         │                                      │
  Completion Queue (CQ)                  Completion Queue (CQ)
  (polled by app to                      (polled by app to
   know when done)                        know when done)
```

The app:
1. Posts a **Work Request (WR)** to the SQ: "send this buffer".
2. The NIC processes the WR asynchronously.
3. The NIC posts a **Completion Queue Entry (CQE)** to the CQ when done.
4. The app polls the CQ (busy-poll, not interrupt, for lowest latency).

### 3.7 RDMA in AI/ML: All-Reduce Example

Modern LLM training (e.g., across 1000s of GPUs) uses RDMA for gradient synchronization:

```
  GPU 0 (Machine A)        GPU 1 (Machine B)        GPU 2 (Machine C)
  ─────────────────        ─────────────────        ─────────────────
  gradient tensor          gradient tensor          gradient tensor
  [in GPU VRAM]            [in GPU VRAM]            [in GPU VRAM]
       │                         │                         │
  GPUDirect RDMA           GPUDirect RDMA           GPUDirect RDMA
       │                         │                         │
  RDMA NIC ════════════════ RDMA NIC ════════════════ RDMA NIC
                                 │
                          Ring All-Reduce
                    (NCCL library orchestrates)

  GPUDirect: NIC DMA engine can read/write GPU VRAM directly,
             bypassing CPU and system RAM entirely.
```

---

## 4. DMABuf — DMA Buffer Sharing Framework

### 4.1 The Problem DMABuf Solves

Modern systems have multiple DMA-capable devices: GPU, NIC, camera ISP, video decoder, display engine. A common workflow:

```
  Camera → capture frame → GPU processes → Display shows it
```

Without DMABuf, each device would:
1. Camera writes frame into its own buffer.
2. CPU copies camera buffer → GPU buffer.
3. GPU processes, writes result to GPU buffer.
4. CPU copies GPU buffer → display buffer.
5. Display reads.

Every copy is wasteful. The frame could be gigabytes per second (4K 60fps = ~750 MB/s).

### 4.2 DMABuf: Zero-Copy Buffer Sharing

DMABuf is a Linux kernel framework (introduced in 3.3, 2012) that allows a buffer allocated by one device to be shared with — and DMA'd by — another device **without any CPU copying**.

```
  ┌────────────────────────────────────────────────────┐
  │                  Linux Kernel                      │
  │                                                    │
  │   Camera Driver          GPU Driver                │
  │   ┌───────────┐          ┌───────────┐             │
  │   │  allocate │          │   import  │             │
  │   │  dmabuf   │          │   dmabuf  │             │
  │   └─────┬─────┘          └─────┬─────┘             │
  │         │                      │                   │
  │         └──────► dmabuf fd ◄───┘                   │
  │                 (file descriptor                   │
  │                  passed between                    │
  │                  drivers/processes)                │
  │                                                    │
  │   Physical Memory: [─────────────────────]         │
  │                    ▲ camera DMA writes             │
  │                    ▲ GPU DMA reads/writes          │
  │                    ▲ display DMA reads             │
  └────────────────────────────────────────────────────┘
```

The buffer is identified by a **file descriptor (fd)**. This fd can be:
- Passed between processes via Unix domain socket (`SCM_RIGHTS`).
- Used by any driver that supports DMABuf import.
- The kernel tracks a reference count; buffer is freed when all fds are closed.

### 4.3 DMABuf Exporter and Importer

```
  Exporter (allocates the buffer):
    struct dma_buf *dmabuf = dma_buf_export(&exp_info);
    int fd = dma_buf_fd(dmabuf, O_CLOEXEC);
    // send fd to userspace or another driver

  Importer (uses the buffer):
    struct dma_buf *dmabuf = dma_buf_get(fd);
    struct dma_buf_attachment *attach = dma_buf_attach(dmabuf, dev);
    struct sg_table *sgt = dma_buf_map_attachment(attach, DMA_BIDIRECTIONAL);
    // sgt contains scatter-gather list → program into device DMA engine
```

The importer gets an SG table with physical addresses it can program into its own DMA engine. The buffer never moves. No CPU copy.

### 4.4 DMABuf Fence Synchronization

Multiple devices operating on the same buffer concurrently would cause races (e.g., display reading while GPU is still writing). DMABuf has a **fence** mechanism:

```
  GPU writes to buf → signals fence
  Display reads buf → waits on fence before starting DMA
```

Fences are implemented via `dma_fence` objects in the kernel, with explicit sync points. Userspace can use `sync_file` (Android's sync framework) to expose these fences.

### 4.5 DMABuf in Practice: V4L2 + GPU Pipeline

```
  Camera (V4L2 driver)
      │
      │  dma_buf_export() → fd
      │
  ─── fd passed to userspace (e.g., via ioctl VIDIOC_EXPBUF) ───
      │
  GPU driver
      │  dma_buf_get(fd)
      │  dma_buf_attach(buf, gpu_dev)
      │  dma_buf_map_attachment() → sg_table
      │  GPU IOMMU programmed with sg_table
      │  GPU shader reads camera frame natively (no copy)
      │
  Display Engine
      │  dma_buf_get(fd)
      │  programs display scanout registers with buffer address
      │  Scanout DMA reads GPU output directly
```

**DMABuf is the plumbing behind:** Android's graphics stack, Wayland's buffer passing, V4L2 media pipelines, CUDA/OpenCL interop with NICs (GPUDirect).

---

## 5. TCP Buffers & Retransmission: How Lost Data Works

### 5.1 The Socket Buffer (sk_buff)

In the Linux network stack, every piece of data is wrapped in an `sk_buff` (socket buffer, often called "skb"). This is the fundamental data structure:

```
  sk_buff (skb):
  ┌──────────────────────────────────────────────────────┐
  │  struct sk_buff {                                    │
  │    sk_buff *next, *prev;  // doubly linked list      │
  │    sk_buff_head *list;    // which queue             │
  │    unsigned char *head;   // start of allocated buf  │
  │    unsigned char *data;   // start of valid data     │
  │    unsigned char *tail;   // end of valid data       │
  │    unsigned char *end;    // end of allocated buf    │
  │    unsigned int len;      // data length             │
  │    unsigned int truesize; // total memory used       │
  │    refcount_t users;      // reference count         │
  │    // ... many more fields: timestamps, marks, etc   │
  │  }                                                   │
  └──────────────────────────────────────────────────────┘

  Memory layout of the actual buffer:
  head                data       tail             end
   │                   │          │                │
   ▼                   ▼          ▼                ▼
  [headroom ........] [DATA DATA DATA] [tailroom ...]
        (for headers)   (actual payload)  (for growth)
```

The headroom is reserved so that protocol layers can prepend headers (TCP → IP → Ethernet) without allocating new memory. Each layer just moves the `data` pointer backward and writes its header.

### 5.2 The TCP Send Buffer

When your application calls `write(fd, buf, len)` or `send()`, data goes into the **TCP send socket buffer** (`sk->sk_sndbuf`):

```
  Application
      │
      │  send(fd, data, len)
      ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                   TCP Send Buffer (sk_sndbuf)                │
  │                                                              │
  │  [skb₁][skb₂][skb₃][skb₄][skb₅][skb₆][skb₇][skb₈]         │
  │   sent   sent  sent  sent  →unacked←  →unsent←             │
  │                                                              │
  │  ◄──── already ACKed ────►◄── in flight ──►◄── queued ──►   │
  │          (freed)         (cannot free yet) (not sent yet)   │
  └──────────────────────────────────────────────────────────────┘
```

**Critical insight:** Data in the send buffer is NOT freed when sent. It is only freed when the receiver acknowledges it (ACK received). Until then, TCP must be able to retransmit it.

### 5.3 TCP Sequence Numbers: The Foundation of Reliability

Every byte in a TCP stream has a **sequence number**. The sender tracks:

```
  SND.UNA  = oldest unacknowledged byte
  SND.NXT  = next byte to be sent
  SND.WND  = receiver's advertised window (how much receiver can accept)

  |---------|-------------|------------|
  SND.UNA   SND.NXT       SND.UNA+SND.WND
      ↑           ↑              ↑
  "Must keep    "Next to      "Cannot send
   in send buf   send"         beyond here"
   for rexmit"
```

### 5.4 TCP Retransmission: The Full Mechanism

When a packet is lost, TCP detects it and retransmits. There are two main detection mechanisms:

#### 5.4.1 Retransmission Timeout (RTO)

```
  Sender                                         Receiver
  ──────                                         ────────
  Send seq=1000, len=500  ──────────────────────►  OK
  Send seq=1500, len=500  ──────────────────────►  OK
  Send seq=2000, len=500  ──────X (LOST)
  Send seq=2500, len=500  ──────────────────────►  Receiver buffers this
                                                   (out of order, can't ACK yet)

  [RTO timer fires]
  
  Retransmit seq=2000     ──────────────────────►  OK!
                                                   ACK=3000 (cumulative ACK)
  ◄──────────────────────────────────────────────  (ACKs everything up to 3000)
```

RTO is calculated using RTT measurements:

```
  SRTT = smoothed RTT = α * SRTT + (1-α) * latest_RTT   (α = 7/8)
  RTTVAR = RTT variance = β * RTTVAR + (1-β) * |SRTT - latest_RTT|  (β = 3/4)
  RTO = SRTT + 4 * RTTVAR
  RTO has a minimum of 200ms (Linux default), maximum of 120s
```

When RTO fires → retransmit the lost segment → double RTO (exponential backoff) → enter slow-start.

#### 5.4.2 Fast Retransmit (Duplicate ACKs)

More efficient than waiting for RTO. When the receiver gets an out-of-order segment, it sends a **duplicate ACK** for the last in-order byte it received:

```
  Sender                                         Receiver
  ──────                                         ────────
  seq=1  ────────────────────────────────────►  ACK=2
  seq=2  ──────X (LOST)
  seq=3  ────────────────────────────────────►  DupACK=2  (got 3, expected 2)
  seq=4  ────────────────────────────────────►  DupACK=2  (got 4, expected 2)
  seq=5  ────────────────────────────────────►  DupACK=2  (got 5, expected 2)
                                                           ← 3 dup ACKs!
  [3 duplicate ACKs → fast retransmit, no need to wait for RTO]

  Retransmit seq=2 ──────────────────────────►  ACK=6  (SACK covers 3,4,5)
```

3 duplicate ACKs trigger fast retransmit. This is RFC 5681 (TCP Congestion Control).

#### 5.4.3 SACK — Selective Acknowledgment

Without SACK (TCP original): If seq=2 is lost but seq=3,4,5 arrived, the sender would retransmit ALL of 2,3,4,5 (go-back-N behavior).

With SACK (RFC 2018): The receiver tells the sender exactly which segments it has. The sender retransmits only what's missing:

```
  ACK=2, SACK=[3-5]
  → Sender knows: "2 is missing, but 3,4,5 are fine. Retransmit only 2."
```

SACK blocks in the TCP header:
```
  TCP Options field:
  [SACK Permitted] (in SYN)
  [SACK block: left_edge=3, right_edge=6]
  [SACK block: left_edge=8, right_edge=10]
  (up to 4 SACK blocks per ACK)
```

### 5.5 The TCP Receive Buffer

On the receiver side, data lands in the **receive socket buffer** (`sk->sk_rcvbuf`):

```
  NIC                                               Application
  ───                                               ───────────
  DMA → sk_buff created → TCP stack processes
                                │
                                ▼
              ┌──────────────────────────────────────┐
              │        TCP Receive Buffer            │
              │                                      │
              │  In-order data:  [aaa][bbb][ccc]     │  ← read() drains this
              │  Out-of-order:        [eee]    [ggg] │  ← held here (OOO queue)
              │                                      │
              │  rcv_nxt = next expected seq number  │
              └──────────────────────────────────────┘
                                │
                                │ app calls read()/recv()
                                ▼
                          Application buffer
```

Out-of-order segments sit in a separate queue (the OOO queue) until the missing segment arrives, at which point they're merged into the in-order data queue and made available to the application.

### 5.6 TCP Flow: Complete Data Flow Diagram

```
  Sender Application                              Receiver Application
  ──────────────────                              ──────────────────

  write(fd, "Hello World")
         │
         ▼
  [ TCP Send Buffer ]
  sk_sndbuf (default: 87380 bytes, auto-tuned up to 4MB)
         │
         │ TCP segments the data by MSS
         │ Adds TCP header (seq, ack, flags, window)
         ▼
  [ IP Layer ]
         │ Adds IP header (src, dst, TTL, protocol)
         ▼
  [ Ethernet Layer ]
         │ Adds Ethernet frame (MAC src, dst, type)
         ▼
  [ NIC TX Ring Buffer ]
  sk_buff descriptors queued in ring
         │
         │ DMA: NIC reads from RAM
         ▼
  [ Wire ]
         │
         │
         ▼
  [ NIC RX Ring Buffer ]                    ← NIC DMA writes here
         │
         │ IRQ or NAPI poll
         ▼
  [ sk_buff allocated, headers stripped ]
         │
         │ TCP layer: check seq, update rcv_nxt
         ▼
  [ TCP Receive Buffer ]
  sk_rcvbuf (default: 87380 bytes, auto-tuned up to 6MB)
         │
         │ Send ACK back to sender
         │
         │ read(fd, buf, len)
         ▼
  Application buffer                         read() called by app
  
  ◄──────────────────────────── ACK ────────────────────────────────
  Sender: ACK received → slides window → frees ACKed sk_buffs → can send more
```

---

## 6. Buffer Lifecycle: Who Owns What

### 6.1 The Send Path: Who Adds, Who Takes, Who Frees

#### Who Adds Data to the Send Buffer?

The **application** adds data via syscalls:
```
  write(fd, buf, len)
  send(fd, buf, len, flags)
  sendmsg(fd, &msg, flags)
  sendfile(out_fd, in_fd, offset, count)  ← zero-copy: no userspace copy
```

The kernel's TCP layer calls `tcp_sendmsg()` which:
1. Allocates `sk_buff` structs (from slab allocator, `kmem_cache`).
2. Copies application data into skb (or uses zero-copy if possible).
3. Appends skb to `sk->sk_write_queue`.

#### Who Takes Data from the Send Buffer (Sends It)?

The **TCP output engine** (`tcp_write_xmit()`), triggered by:
- The application calling send (triggers immediate send if window allows).
- ACKs arriving (opens the window → can send more).
- The TCP pacing timer.

The TCP layer dequeues skbs from `sk_write_queue`, segments them at MSS, passes to IP → NIC. **But it does NOT dequeue from the queue for retransmission purposes.** The skb stays in the queue.

Actually, there are **two pointers**:
- `sk_send_head` points to the first unsent skb in `sk_write_queue`.
- All skbs before `sk_send_head` have been sent but not yet ACKed.
- When more can be sent: advance `sk_send_head`, push those skbs.
- When retransmitting: go back to the unACKed skbs.

#### Who Frees the Send Buffer?

The **ACK handler** (`tcp_ack()` → `tcp_clean_rtx_queue()`):
- When an ACK arrives covering seq numbers up to X.
- All skbs in `sk_write_queue` with `end_seq <= X` are dequeued and freed.
- `kfree_skb()` is called → skb reference count drops → if 0, memory returned to slab.

```
  sk_write_queue (doubly-linked list of sk_buff):
  
  HEAD → [skb₁: seq 1-500]  → [skb₂: seq 501-1000] → [skb₃: seq 1001-1500] → NULL
          ACKed (seq<1001)      ACKed (seq<1001)          sent, unACKed
          
  ACK=1001 arrives:
  → tcp_clean_rtx_queue() called
  → skb₁ and skb₂ dequeued
  → kfree_skb(skb₁), kfree_skb(skb₂)
  → sk->sk_sndbuf_used decreases → application unblocked if it was blocked in send()
```

### 6.2 The Receive Path: Who Adds, Who Takes, Who Frees

#### Who Adds to the Receive Buffer?

The **kernel's NIC driver + TCP stack**:
1. NIC DMA writes packet into a pre-allocated ring buffer slot.
2. Driver's NAPI poll function calls `netif_receive_skb()`.
3. Passes through IP, reaches TCP: `tcp_rcv_established()`.
4. TCP checks seq number, if in-order: `tcp_queue_rcv()` → adds skb to `sk->sk_receive_queue`.
5. If out-of-order: adds to `sk->tcp_rtx_queue` (OOO queue).

#### Who Takes from the Receive Buffer?

The **application** via:
```
  read(fd, buf, len)
  recv(fd, buf, len, flags)
  recvmsg(fd, &msg, flags)
```

Internally: `tcp_recvmsg()` dequeues skbs from `sk_receive_queue`, copies data to userspace buffer, advances `copied_seq`.

#### Who Frees the Receive Buffer?

When `tcp_recvmsg()` copies data from an skb:
- It calls `sk_eat_skb()` when the entire skb has been consumed.
- `sk_eat_skb()` calls `__kfree_skb()` → returns memory.
- If only part of the skb was consumed (partial read), the skb stays in the queue; `sk->sk_data_ready` is updated.

```
  sk_receive_queue:
  HEAD → [skb₁: seq 1-1460, fully copied by app] → [skb₂: seq 1461-2920] → NULL
  
  read() copies skb₁:
  → sk_eat_skb(skb₁) → kfree_skb(skb₁)
  → sk_rcvbuf_used decreases
  → Kernel sends TCP window update to sender (more room)
```

### 6.3 Reference Counting: The Real Memory Manager

`sk_buff` uses reference counting (`skb->users`, actually `skb->_refcount`):

```
  skb_get(skb)    → increment refcount
  kfree_skb(skb)  → decrement refcount; if 0, actually free

  Why multiple references?
  - Network taps (tcpdump) hold a reference
  - GSO (Generic Segmentation Offload) fragments share parent
  - Multicast: same skb sent to multiple interfaces
```

Memory is freed only when the last reference is dropped.

### 6.4 NIC Ring Buffers: The Hardware Layer

The NIC has its own ring buffers — circular arrays of DMA descriptors:

```
  TX Ring Buffer (send):
  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
  │desc0│desc1│desc2│desc3│desc4│desc5│desc6│desc7│  (ring of N descriptors)
  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
         ↑                          ↑
      HW tail                    SW head
      (NIC reads here             (driver writes here)
       and advances)

  Each descriptor:
  struct tx_desc {
    __le64 buffer_addr;   // physical address of skb data (IOVA)
    __le32 cmd_type_len;  // length, flags (EOP=end of packet, etc.)
    __le32 status_error;  // set by HW when done
  };

  RX Ring Buffer (receive):
  - Driver pre-fills each descriptor with a physical address of a pre-allocated page
  - NIC DMA-writes incoming packet data into those pages
  - Driver polls for completed descriptors → builds sk_buff from them
```

The driver must always keep the RX ring full of pre-allocated buffers. If it runs out → the NIC has nowhere to put incoming packets → they're dropped (RX buffer exhaustion → drops visible in `ethtool -S` as `rx_missed_errors`).

---

## 7. Buffer Sizing: How It Is Calculated

### 7.1 TCP Socket Buffer Sizes

Linux has three values per buffer (send and receive):

```
  /proc/sys/net/ipv4/tcp_rmem = min default max
  /proc/sys/net/ipv4/tcp_wmem = min default max

  Typical values:
  tcp_rmem: 4096    87380   6291456    (4KB, 85KB, 6MB)
  tcp_wmem: 4096    16384   4194304    (4KB, 16KB, 4MB)
```

- **min**: Minimum guaranteed, even under memory pressure.
- **default**: Initial size of the socket buffer.
- **max**: Maximum the auto-tuning can grow to.

### 7.2 TCP Auto-Tuning

With `net.ipv4.tcp_moderate_rcvbuf = 1` (default on), the kernel auto-tunes:

```
  Optimal receive buffer size = Bandwidth × RTT   (Bandwidth-Delay Product)

  Example:
  Link: 1 Gbps = 125 MB/s
  RTT:  50ms = 0.05s

  BDP = 125 MB/s × 0.05s = 6.25 MB

  The receive buffer must be at least 6.25 MB to fully utilize the link.
  (Because if buf fills up before ACKs return, sender stalls.)
```

The kernel measures throughput and adjusts `sk_rcvbuf` dynamically up to `tcp_rmem[2]`.

### 7.3 MSS — Maximum Segment Size

MSS is the largest TCP payload in one segment:

```
  Ethernet MTU:   1500 bytes
  IP header:        20 bytes (minimum)
  TCP header:       20 bytes (minimum)
                  ─────────
  MSS default:    1460 bytes

  With TCP options (timestamps, SACK):
  TCP header ≈ 32 bytes → MSS ≈ 1448 bytes

  With Jumbo Frames (MTU=9000):
  MSS ≈ 8948 bytes
```

MSS is negotiated in the SYN/SYN-ACK handshake via the MSS TCP option. Each side advertises the maximum it can receive.

### 7.4 NIC Ring Buffer Size

Configurable via `ethtool`:

```bash
ethtool -g eth0          # show current ring sizes
ethtool -G eth0 rx 4096  # set RX ring to 4096 descriptors

Typical defaults:  256 or 512 descriptors
Typical maximums:  4096 descriptors (NIC-dependent)
```

Each RX descriptor points to one packet buffer. With MTU=1500, each descriptor covers one 1500B packet (or one 2KB page in practice, to avoid DMA crossing page boundaries).

Memory consumed by RX ring:
```
  4096 descriptors × 2048 bytes/buf = 8 MB pinned memory (per NIC queue)
  Modern NICs have 8-64 queues → 64MB-512MB pinned for rings alone
```

### 7.5 sk_buff Size Calculation

```
  sizeof(struct sk_buff) ≈ 240 bytes (kernel struct, not payload)

  For a 1500-byte packet:
  - sk_buff struct:      240 bytes
  - skb_shared_info:     320 bytes (frag list, GSO info)
  - Linear data buffer: 1536 bytes (rounded up for alignment)
  Total: ~2096 bytes per packet → ~2KB slab allocation
```

The kernel uses the slab allocator (`kmem_cache`) for `sk_buff` structs and the page allocator for data buffers.

### 7.6 UDP Receive Buffer

```
  /proc/sys/net/core/rmem_max    = max socket rcv buffer (all sockets)
  /proc/sys/net/core/wmem_max    = max socket snd buffer
  /proc/sys/net/core/rmem_default = default socket rcv buffer
  /proc/sys/net/core/wmem_default = default socket snd buffer

  For high-throughput UDP (DPDK alternatives, video streaming):
  Typical recommendation: rmem_max = 134217728 (128 MB)
```

---

## 8. What Happens When a Buffer Is Full

### 8.1 Send Buffer Full → Application Blocks (or EAGAIN)

```
  Application calls send():
       │
       ▼
  sk_sndbuf used ≥ sk_sndbuf limit?
       │
       ├── YES (blocking socket):
       │     → Process sleeps on sk->sk_sleep (wait queue)
       │     → Woken up when ACKs arrive and buffer drains
       │     → Then send() copies data and returns
       │
       └── YES (non-blocking socket, O_NONBLOCK):
             → send() returns -1, errno = EAGAIN / EWOULDBLOCK
             → Application must retry (epoll/select for writeability)
```

This is **backpressure**: TCP naturally slows the application to match the network speed + receiver capacity.

### 8.2 Receive Buffer Full → TCP Window Zero

The receiver's receive buffer fills when the application isn't reading fast enough:

```
  Receiver:
  sk_rcvbuf used → approaching sk_rcvbuf limit
       │
       ▼
  TCP advertises smaller receive window in ACKs:
  TCP header field: Window = (sk_rcvbuf - used) / scale_factor
       │
       ▼
  Sender sees Window = 0 → MUST STOP SENDING
       │
       ▼
  Sender enters "zero window probe" mode:
  → Sends 1-byte probes periodically (persist timer)
  → Waiting for receiver to advertise non-zero window
       │
       ▼
  Application reads data → receive buffer drains
       │
       ▼
  TCP sends "window update" ACK with larger window
       │
       ▼
  Sender resumes transmission
```

This is **TCP's end-to-end flow control** — it propagates backpressure from the slowest reader all the way back to the sender.

```
  Time →
  Sender: [====sending===] [===zero window, blocked===] [===resumes===]
  Recv buf: [__________] [FULL FULL FULL] [draining__] [____________]
  App read:   fast             SLOW/STOPPED              fast again
```

### 8.3 NIC RX Ring Full → Packet Drops

If the NIC's RX ring runs out of pre-filled descriptors (driver too slow to refill), **the NIC hardware drops packets**. These drops happen before any software buffer:

```
  Packets/sec arriving
         │
         ▼
  NIC RX ring
  [■][■][■][■][■][■][■][■]  ← all descriptors in use
         │
  New packet arrives → NO FREE DESCRIPTOR
         │
         ▼
  NIC DROPS packet internally
  (increments rx_missed_errors / rx_fifo_errors counter)
         │
  NAPI poll eventually drains ring → refills descriptors
```

**Mitigation:**
- Increase ring size: `ethtool -G eth0 rx 4096`
- Use more CPU cores / RSS (Receive Side Scaling): spread load across queues
- NAPI budget tuning (how many packets processed per poll cycle)
- Use kernel bypass (DPDK, XDP) to avoid kernel overhead entirely

### 8.4 UDP — No Retransmission, Just Drops

UDP has no retransmission. If the receive socket buffer fills:

```
  /proc/sys/net/core/rmem_max = 212992 (208KB default)

  UDP socket rcvbuf full → kernel drops incoming packet → packet gone forever
  → Application sees this as: read() never returns that data
  → Visible in: /proc/net/udp (column 'drops'), netstat -su
```

Applications using UDP must implement their own reliability (like QUIC, RTP/RTCP) or accept loss.

### 8.5 RDMA Receive Side — WQE Exhaustion

In RDMA, when the receiver runs out of posted Receive Work Requests:

```
  Receiver posts RWRs (Receive Work Requests) to RQ:
  [RWR₁][RWR₂][RWR₃] ← these are the "slots" for incoming SEND messages

  Sender sends a SEND message → no RWR available on receiver
       │
       ▼
  InfiniBand: Receiver NACKs with "RNR NAK" (Receiver Not Ready)
  → Sender waits RNR timeout → retransmits
  → If RNR NAK count exceeds threshold → QP goes to ERROR state
  → Application must handle QP recovery

  RoCE v2: No RNR NAK. Packet is dropped → relies on congestion control + timeout retransmit.
```

---

## 9. Mental Model: The Complete Picture

### 9.1 The Full Stack: From App to Wire

```
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║                        SENDER MACHINE                                   ║
  ║                                                                          ║
  ║  ┌─────────────┐                                                         ║
  ║  │ Application │  write(fd, buf, len)                                    ║
  ║  └──────┬──────┘                                                         ║
  ║         │ syscall (copy_from_user)                                       ║
  ║         ▼                                                                ║
  ║  ┌──────────────────────────────────────────────────────────┐            ║
  ║  │               TCP Send Buffer (sk_sndbuf)                │            ║
  ║  │  [skb₁][skb₂][skb₃] ← unACKed  │  [skb₄] ← unsent      │            ║
  ║  └──────────────────────────────────┬───────────────────────┘            ║
  ║                                     │ tcp_write_xmit()                   ║
  ║                                     ▼                                    ║
  ║  TCP Header added (seq, ack, window, flags)                               ║
  ║  IP Header added (src/dst IP, TTL, checksum)                             ║
  ║  Ethernet Header added (MAC src/dst)                                     ║
  ║                                     │                                    ║
  ║                                     ▼                                    ║
  ║  ┌──────────────────────────────────────────────────────────┐            ║
  ║  │              NIC TX Ring Buffer                          │            ║
  ║  │  [desc: phys_addr, len] × N  (circular ring)            │            ║
  ║  └──────────────────────────────┬───────────────────────────┘            ║
  ║                                 │ NIC DMA engine reads sk_buff data      ║
  ║                                 │ from RAM (IOMMU-validated)             ║
  ╚═════════════════════════════════╪════════════════════════════════════════╝
                                    │
                              Network Wire
                       (Ethernet / InfiniBand / RoCE)
                                    │
  ╔═════════════════════════════════╪════════════════════════════════════════╗
  ║                                 │               RECEIVER MACHINE         ║
  ║                                 ▼                                        ║
  ║  ┌──────────────────────────────────────────────────────────┐            ║
  ║  │              NIC RX Ring Buffer                          │            ║
  ║  │  [desc: phys_addr] pre-filled by driver                 │            ║
  ║  │  NIC DMA-writes incoming packet into each slot          │            ║
  ║  └──────────────────────────────┬───────────────────────────┘            ║
  ║                                 │ NAPI poll / IRQ                        ║
  ║                                 ▼                                        ║
  ║  sk_buff allocated, headers parsed & stripped                            ║
  ║  TCP: check seq_num, send ACK                                            ║
  ║                                 │                                        ║
  ║                                 ▼                                        ║
  ║  ┌──────────────────────────────────────────────────────────┐            ║
  ║  │              TCP Receive Buffer (sk_rcvbuf)              │            ║
  ║  │  In-order:  [skb₁][skb₂][skb₃]                         │            ║
  ║  │  OOO queue: [skb₅] (waiting for skb₄)                  │            ║
  ║  └──────────────────────────────┬───────────────────────────┘            ║
  ║                                 │ read(fd, buf, len) drains this        ║
  ║                                 ▼                                        ║
  ║  ┌─────────────┐                                                         ║
  ║  │ Application │  receives data                                          ║
  ║  └─────────────┘                                                         ║
  ╚══════════════════════════════════════════════════════════════════════════╝

  ◄──────────────────── ACK flows back ──────────────────────────────────────
  Sender: on ACK → tcp_clean_rtx_queue() → kfree_skb() → buffer drains
```

### 9.2 DMABuf Zero-Copy Pipeline

```
  ╔════════════════════════════════════════════════════════════════╗
  ║                  Kernel (single machine)                       ║
  ║                                                                ║
  ║  Camera ISP           GPU                  Display Engine      ║
  ║  ─────────            ───                  ───────────────     ║
  ║  alloc_buf()          import dmabuf fd     import dmabuf fd    ║
  ║  export dmabuf fd─────►                ───►                   ║
  ║                        map_attachment()    map_attachment()    ║
  ║                        sg_table→GPU IOMMU  sg_table→Disp IOMMU║
  ║       │                     │                    │             ║
  ║       │ DMA write           │ DMA read/write     │ DMA read    ║
  ║       ▼                     ▼                    ▼             ║
  ║  ┌─────────────────────────────────────────────────────────┐  ║
  ║  │              Physical RAM (single allocation)           │  ║
  ║  │              [frame data lives here, never copied]      │  ║
  ║  └─────────────────────────────────────────────────────────┘  ║
  ║                                                                ║
  ║  Fence: GPU signals fence → Display waits on fence            ║
  ║         (ensures no tearing/race)                             ║
  ╚════════════════════════════════════════════════════════════════╝
```

### 9.3 RDMA One-Sided Read (No Remote CPU)

```
  Machine A (Initiator)                    Machine B (Target)
  ─────────────────────                    ─────────────────

  App A:                                   App B:
  ibv_reg_mr(local_buf) → lkey             ibv_reg_mr(remote_buf) → rkey
                                           sends rkey + addr to A out-of-band

  App A posts RDMA READ WR:
  {remote_addr, rkey, local_addr, lkey, length}
         │
         ▼
  HCA (RDMA NIC) on A:
  Sends RDMA READ request over network ───────────────────────►
                                                               │
                                                        HCA on B:
                                                        Validates rkey
                                                        DMA reads remote_buf
                                                        from Machine B's RAM
                                                        Sends data back
                                        ◄───────────────────────
  HCA on A:
  DMA writes data into local_buf
  Posts CQE to Completion Queue
         │
         ▼
  App A polls CQ → gets completion → data is in local_buf

  B's CPU was NEVER involved. B's OS was NEVER involved.
  Zero kernel crossings on Machine B.
```

### 9.4 Key Numbers to Remember

| Parameter | Typical Value | Notes |
|---|---|---|
| MSS (Ethernet) | 1460 bytes | MTU 1500 - 20 IP - 20 TCP |
| MSS (Jumbo) | 8948 bytes | MTU 9000 - 20 - 20 - options |
| TCP rcvbuf default | 87380 bytes (~85KB) | `tcp_rmem[1]` |
| TCP rcvbuf max | 6 MB | `tcp_rmem[2]` (auto-tuned) |
| TCP sndbuf max | 4 MB | `tcp_wmem[2]` |
| NIC RX ring default | 256-512 descriptors | per queue |
| NIC RX ring max | 4096 descriptors | per queue |
| sk_buff struct size | ~240 bytes | just the struct |
| Total per-packet | ~2 KB | struct + data + overhead |
| BDP (1Gbps, 10ms RTT) | 1.25 MB | need buffer ≥ this |
| BDP (100Gbps, 1ms RTT) | 12.5 MB | HPC/datacenter |
| RDMA registration | µs-ms | one-time cost, then fast |
| RTO minimum | 200ms | Linux default (RFC: 1s) |

### 9.5 Concept Relationships

```
  DMA          → Device reads/writes RAM without CPU per-byte involvement
  IOMMU        → Makes DMA safe (address translation + protection)
  DMABuf       → Shares DMA buffers between multiple devices (zero-copy)
  RDMA         → DMA across network (device-to-device, machine-to-machine)
  sk_buff      → Kernel's fundamental network buffer struct
  TCP sndbuf   → Holds sent-but-unACKed data for retransmission
  TCP rcvbuf   → Holds received data until app reads it
  NIC ring buf → Hardware circular queue; sits below sk_buff
  MSS          → Largest TCP payload per segment
  BDP          → Minimum buffer size to saturate a link
  RTO          → Timeout-based loss detection (slow but robust)
  Fast rexmit  → 3 dup ACKs → retransmit without waiting for timeout
  SACK         → Selective ACK; retransmit only missing, not everything
  Zero window  → Flow control: receiver tells sender to stop
  NAPI         → Polling mode for NIC interrupts (avoids IRQ storm)
```

---

## Appendix: Useful Commands

```bash
# View TCP buffer settings
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.core.rmem_max

# View per-socket buffer usage
ss -timep | grep -A1 ESTABLISHED

# View NIC ring buffer sizes
ethtool -g eth0

# View NIC statistics (drops, errors)
ethtool -S eth0 | grep -E 'miss|drop|fifo|error'

# Monitor retransmissions
ss -s | grep retrans
netstat -st | grep -i retran
/proc/net/snmp (column: RetransSegs)

# View sk_buff memory usage
cat /proc/net/sockstat

# DMABuf: list exported buffers (via debugfs)
ls /sys/kernel/debug/dma_buf/bufinfo

# RDMA: list devices and ports
ibv_devinfo
rdma link show

# RDMA: show queue pair stats
perfquery     # InfiniBand performance counters
```

---

*This guide covers the complete mental model from physical DMA mechanics through RDMA's kernel-bypass networking, DMABuf's zero-copy device sharing, TCP's reliability and retransmission machinery, and the full lifecycle of every buffer involved — who allocates, who fills, who drains, who frees, and what happens when any stage becomes the bottleneck.*
