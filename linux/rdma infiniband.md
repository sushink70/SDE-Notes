# RDMA & InfiniBand in the Linux Kernel
## A Complete, In-Depth Reference Guide

---

> **Philosophy:** Understanding RDMA is not just about learning an API. It is about
> internalizing a completely different mental model of how two machines can exchange
> data — one that bypasses the operating system entirely. Master this model and you
> will think about networking at a level most engineers never reach.

---

## Table of Contents

1. [Foundational Concepts: Why RDMA Exists](#1-foundational-concepts)
2. [Traditional Networking vs RDMA — A Deep Comparison](#2-traditional-vs-rdma)
3. [InfiniBand Architecture](#3-infiniband-architecture)
4. [RDMA Transport Flavors: IB, RoCE, iWARP](#4-rdma-transport-flavors)
5. [Linux Kernel RDMA Stack — Layer by Layer](#5-linux-kernel-rdma-stack)
6. [InfiniBand Verbs API — The Programming Interface](#6-verbs-api)
7. [Protection Domains and Memory Registration](#7-protection-domains-and-memory-registration)
8. [Queue Pairs — The Heart of RDMA](#8-queue-pairs)
9. [Work Requests and Scatter-Gather Lists](#9-work-requests-and-scatter-gather)
10. [Completion Queues and Event Handling](#10-completion-queues)
11. [RDMA Operations: Send/Recv, Read, Write, Atomic](#11-rdma-operations)
12. [Connection Management (RDMA_CM)](#12-connection-management)
13. [InfiniBand Fabric: Switches, Routers, Subnet Manager](#13-infiniband-fabric)
14. [Shared Receive Queues (SRQ)](#14-shared-receive-queues)
15. [Memory Windows and On-Demand Paging](#15-memory-windows)
16. [RDMA in the Linux Kernel — Driver Architecture](#16-kernel-driver-architecture)
17. [C Implementation — Complete Working Examples](#17-c-implementation)
18. [Rust Implementation — Safe RDMA Abstractions](#18-rust-implementation)
19. [Performance Tuning and Optimization](#19-performance-tuning)
20. [Debugging, Monitoring, and Diagnostics](#20-debugging-and-monitoring)
21. [Advanced Topics: SRD, DC, XRC](#21-advanced-topics)
22. [Mental Models and Expert Intuition](#22-mental-models)

---

## 1. Foundational Concepts

### 1.1 The Problem RDMA Solves

To understand RDMA, you must first feel the pain of the problem it solves.

In a traditional network stack, when Process A on Machine 1 wants to send data
to Process B on Machine 2, the following chain of events occurs:

```
TRADITIONAL NETWORK DATA PATH
==============================

Machine 1 (Sender)                        Machine 2 (Receiver)
+-----------------------------+            +-----------------------------+
|  Application (Process A)    |            |  Application (Process B)    |
|  [User Space]               |            |  [User Space]               |
|    data in app buffer       |            |    data received in buffer  |
+------------|----------------+            +-------------|---------------+
             | (1) write() / send()                      | (8) read()
             v                                           ^
+-----------------------------+            +-----------------------------+
|  Socket Layer               |            |  Socket Layer               |
|  [Kernel Space]             |            |  [Kernel Space]             |
|  Copy: app_buf -> sock_buf  |            |  Copy: sock_buf -> app_buf  |
+------------|----------------+            +-------------|---------------+
             | (2) copy data                             | (7) deliver data
             v                                           ^
+-----------------------------+            +-----------------------------+
|  TCP/IP Stack               |            |  TCP/IP Stack               |
|  [Kernel Space]             |            |  [Kernel Space]             |
|  Segment, Checksum, Route   |            |  Checksum verify, Reassemble|
+------------|----------------+            +-------------|---------------+
             | (3) pass to driver                        | (6) interrupt
             v                                           ^
+-----------------------------+            +-----------------------------+
|  NIC Driver                 |            |  NIC Driver                 |
|  [Kernel Space]             |            |  [Kernel Space]             |
|  DMA: sock_buf -> NIC ring  |            |  DMA: NIC ring -> kern_buf  |
+------------|----------------+            +-------------|---------------+
             | (4) send                                  | (5) receive
             v                                           ^
           [Wire / Fabric]----------------------------->+
```

**Every step has a cost:**

| Step | Cost Type | Impact |
|------|-----------|--------|
| User→Kernel copy | Memory bandwidth | Up to 2x data movement |
| Kernel→Kernel copy | Memory bandwidth | Additional CPU cycles |
| Interrupt (IRQ) | CPU cycles | Context switch overhead |
| Syscall overhead | CPU cycles | Ring crossing costs |
| TCP processing | CPU cycles | Checksum, retransmit logic |
| Kernel scheduler | Latency | Unpredictable scheduling delays |

At 100 Gbps line rate:
- 100 Gbps / 8 = 12.5 GB/s of data per second
- Modern CPUs can sustain ~50-100 GB/s memory bandwidth
- Every copy costs you 12.5 GB/s of precious memory bandwidth
- Two copies = 25 GB/s bandwidth consumed just moving the same data around
- TCP processing at 100 Gbps requires substantial CPU cores

**The result:** At 100 Gbps, traditional networking burns 2-4 CPU cores just for
the network stack, adds 10-100 µs latency, and wastes memory bandwidth on copies.

---

### 1.2 What RDMA Actually Means

**RDMA = Remote Direct Memory Access**

Break down each word:

- **Remote:** The memory being accessed is on a different machine across a network
- **Direct:** The access goes directly to/from application memory — NO kernel involvement in the data path
- **Memory Access:** You are literally reading/writing the other machine's RAM

```
RDMA DATA PATH
==============

Machine 1 (Initiator)                     Machine 2 (Target)
+-----------------------------+            +-----------------------------+
|  Application (Process A)    |            |  Application (Process B)    |
|  [User Space]               |            |  [User Space]               |
|  app_buffer at addr X       |            |  app_buffer at addr Y       |
+------------|----------------+            +-------------|---------------+
             |                                           |
             | (1) Post WR to QP                        | (no involvement!)
             | (user space doorbell ring)                |
             |                                           |
+------------|----------------+            +-------------|---------------+
|  RDMA NIC (HCA/RNIC)        |            |  RDMA NIC (HCA/RNIC)        |
|  [Hardware]                 |            |  [Hardware]                 |
|  DMA directly from app_buf  |            |  DMA directly to app_buf    |
+------------|----------------+            +-------------|---------------+
             | (2) send                                  | (3) receive
             v                                           ^
           [InfiniBand / RoCE / iWARP Fabric]---------->+

  (4) Completion event notified to Process A
  (Process B may never even be interrupted!)
```

**The revolutionary insight:** Process B on Machine 2 does NOT need to:
- Be scheduled by the OS
- Handle an interrupt
- Copy data from a kernel buffer
- Make any system call

Its memory is written directly by the network hardware on Machine 1's command.
This is the essence of RDMA: **one machine writes into another machine's memory
without the remote CPU's involvement.**

---

### 1.3 Key Performance Numbers (Mental Benchmarks)

Internalize these numbers — they are your compass when reasoning about RDMA:

```
PERFORMANCE MENTAL MODEL
=========================

Technology          | Latency      | Bandwidth     | CPU Usage
--------------------|--------------|---------------|----------
TCP/IP (1 GbE)      | 100-500 µs   | ~1 Gbps       | High
TCP/IP (10 GbE)     | 50-200 µs    | ~10 Gbps      | High
TCP/IP (100 GbE)    | 20-100 µs    | ~50-90 Gbps   | Very High
                    |              |               |
RDMA IB (56 Gb/s)   | 1-2 µs       | ~6 GB/s       | Near-Zero
RDMA IB (100 Gb/s)  | 0.6-1.5 µs   | ~12 GB/s      | Near-Zero
RDMA IB (200 Gb/s)  | 0.5-1.0 µs   | ~24 GB/s      | Near-Zero
RDMA RoCEv2         | 2-5 µs       | Similar to IB | Near-Zero
                    |              |               |
Local Memory Access | ~100 ns      | 50-100 GB/s   | N/A
NVMe SSD            | 20-100 µs    | ~7 GB/s       | Low
DRAM RDMA           | ~1 µs        | ~12 GB/s      | Near-Zero
```

**Key insight:** RDMA latency (1-2 µs) is closer to local DRAM access (100 ns)
than to TCP networking (100+ µs). This is why RDMA enables distributed systems
that behave like shared memory systems.

---

## 2. Traditional Networking vs RDMA — A Deep Comparison

### 2.1 Data Path Philosophy

```
PHILOSOPHY COMPARISON
=====================

Traditional Networking:              RDMA:
"The OS is the trusted mediator"     "The Hardware is the trusted executor"

App -> OS -> NIC -> Network          App -> NIC -> Network
       ^                                    ^
       |                                    |
  (kernel controls                    (hardware controls
   all data movement)                  all data movement)
```

### 2.2 The Zero-Copy Principle

**Zero-copy** means data is never copied — it moves only from its source to its
destination in a single DMA operation.

```
ZERO-COPY vs COPY-BASED
========================

Copy-Based (Traditional):
+----------+     copy      +----------+     copy      +----------+
| App Buf  |  ==========>  | Sock Buf |  ==========>  | NIC Ring |
+----------+   (CPU cost)  +----------+   (CPU cost)  +----------+
                                                            |
                                                          [wire]

Zero-Copy (RDMA):
+----------+                                           +----------+
| App Buf  |  =========================================| NIC Ring |
+----------+           (Single DMA, no CPU)            +----------+
                                                            |
                                                          [wire]
```

For zero-copy to work, the NIC must be able to access application memory
directly. This requires **memory registration** — a process where the application
tells the OS "pin this memory region so it cannot be swapped out, and give the
NIC a key to access it."

### 2.3 Kernel Bypass

**Kernel bypass** means the application communicates with the NIC directly,
without making system calls:

```
KERNEL BYPASS MECHANISM
========================

Without Bypass:                       With Bypass (RDMA):
                                      
App ----syscall----> Kernel           App ----mmap'd doorbell----> NIC
                       |              (user-space write to register)
                       v
                     NIC

The "doorbell" is a memory-mapped register on the NIC.
Writing to it (a single user-space store instruction!)
tells the NIC to process the next work request.
```

A "doorbell ring" in RDMA is literally:
```c
// This single write triggers the NIC to process a work request
// No syscall, no kernel, no context switch
*((volatile uint32_t*)doorbell_addr) = queue_num;
```

---

## 3. InfiniBand Architecture

### 3.1 What InfiniBand Is

InfiniBand (IB) is a networking standard developed to address the limitations
of Ethernet for high-performance computing. It is:

- A **complete network architecture** (physical, link, network, transport layers)
- Designed from the ground up for **low latency and high bandwidth**
- Natively supports **RDMA and kernel bypass**
- **Lossless** by design (uses credit-based flow control, not TCP retransmits)
- Widely used in HPC clusters, financial systems, AI training infrastructure

**Key distinction:** InfiniBand is NOT just a cable type. It is an entire
protocol stack from the physical layer to the application layer.

### 3.2 InfiniBand Physical Layer

```
INFINIBAND LINK SPEEDS
=======================

Generation  | Name    | Per-Lane  | 4x Link   | 12x Link
------------|---------|-----------|-----------|----------
1st Gen     | SDR     | 2.5 Gbps  | 10 Gbps   | 30 Gbps
2nd Gen     | DDR     | 5.0 Gbps  | 20 Gbps   | 60 Gbps
3rd Gen     | QDR     | 10.0 Gbps | 40 Gbps   | 120 Gbps
4th Gen     | FDR     | 14.0 Gbps | 56 Gbps   | 168 Gbps
5th Gen     | EDR     | 25.0 Gbps | 100 Gbps  | 300 Gbps
6th Gen     | HDR     | 50.0 Gbps | 200 Gbps  | 600 Gbps
7th Gen     | NDR     | 100.0 Gbps| 400 Gbps  | 1200 Gbps
8th Gen     | XDR     | 200.0 Gbps| 800 Gbps  | 2400 Gbps

"4x" means 4 physical lanes bonded together. Most HPC deployments use 4x.
"12x" means 12 lanes; used for switches and high-bandwidth connections.
```

### 3.3 InfiniBand Network Topology

A complete InfiniBand fabric consists of several types of devices:

```
INFINIBAND FABRIC TOPOLOGY
===========================

                         +------------------+
                         | Subnet Manager   |
                         | (OpenSM / OFED)  |
                         | - Assigns LIDs   |
                         | - Computes routes|
                         | - Monitors fabric|
                         +--------|---------+
                                  | Management
                                  |
+--------+    +--------+    +-----|--------+    +--------+    +--------+
|  HCA   |    |  HCA   |    |    Switch   |    |  HCA   |    |  HCA   |
| Node 1 |----| Node 2 |----|  (Fabric)   |----| Node 3 |----| Node 4 |
+--------+    +--------+    |             |    +--------+    +--------+
                            | 36-port     |
                            | non-blocking|
                            +-------------+

HCA  = Host Channel Adapter (the RDMA NIC in a server)
Switch = InfiniBand switch (like Ethernet switch but lossless)
```

**Device Types:**
- **HCA (Host Channel Adapter):** The InfiniBand NIC installed in servers
- **Switch:** Forwards packets between HCAs; typically 36-64 ports
- **Router:** Connects multiple InfiniBand subnets
- **Subnet Manager (SM):** Software that manages the entire fabric (like a
  controller in SDN); assigns addresses, computes routing tables

### 3.4 InfiniBand Addressing

InfiniBand uses its own addressing scheme — completely different from IP:

```
INFINIBAND ADDRESS TYPES
========================

1. GID (Global Identifier) — 128-bit, globally unique
   Format: EUI-64 based (similar to IPv6 link-local)
   Used for: Global routing, cross-subnet communication
   Example: fe80::0002:c903:0012:3456

2. LID (Local Identifier) — 16-bit, subnet-local
   Assigned by: Subnet Manager at initialization
   Used for: Within-subnet packet routing
   Range: 0x0001 to 0xBFFF (unicast)
            0xC000 to 0xFFFE (multicast)
   
3. GUID (Globally Unique Identifier) — 64-bit hardware address
   Like: MAC address in Ethernet
   Burned into: HCA hardware at manufacture
   
4. QP Number — 24-bit
   Identifies: A specific Queue Pair within an HCA
   Used for: Multiplexing many connections on one HCA

PACKET ADDRESSING EXAMPLE:
+---------+-------+-------+--------+--------+
| GRH     | LRH   | BTH   | Payload| ICRC   |
| (opt)   | 8B    | 12B   | var    | 4B     |
+---------+-------+-------+--------+--------+
  |         |       |
  |         |       +-- Queue Pair Number (destination QP)
  |         +---------- Destination LID (which node)
  +-------------------- Destination GID (global routing)

LRH = Local Routing Header
BTH = Base Transport Header
GRH = Global Routing Header (for cross-subnet)
ICRC = Invariant CRC (hardware-computed)
VCRC = Variant CRC (per-link)
```

### 3.5 InfiniBand Service Levels and Virtual Lanes

InfiniBand supports **Quality of Service (QoS)** natively:

```
SERVICE LEVELS AND VIRTUAL LANES
==================================

Service Level (SL): 0-15 (4 bits)
  - Application-specified priority
  - Maps to a Virtual Lane

Virtual Lane (VL): 0-14 (VL15 reserved for management)
  - Physical queue on the link
  - Each VL has independent buffer
  - Prevents head-of-line blocking

SL -> VL MAPPING (set by Subnet Manager):
+----+----+----+----+----+----+----+----+
| SL | 0  | 1  | 2  | 3  | 4  | 5  | 6 |
+----+----+----+----+----+----+----+----+
| VL | 0  | 1  | 0  | 2  | 0  | 3  | 0 |
+----+----+----+----+----+----+----+----+

Multiple SLs can map to the same VL.
VL15 is always used for subnet management traffic (SM communications).
```

---

## 4. RDMA Transport Flavors: IB, RoCE, iWARP

Three technologies implement RDMA over different physical fabrics:

```
RDMA TRANSPORT COMPARISON
==========================

                IB (InfiniBand)    RoCEv1         RoCEv2         iWARP
----------------|-----------------|--------------|--------------|----------------
Physical Layer  | IB Cable        | Ethernet     | Ethernet     | Ethernet
Link Layer      | IB Link         | Ethernet     | Ethernet     | Ethernet
Network Layer   | IB Network      | IB over Eth  | UDP/IP       | TCP/IP
Transport       | IB Transport    | IB Transport | IB Transport | MPA/DDP/RDMAP
Lossless        | Yes (native)    | Yes (PFC)    | Yes (PFC)    | No (TCP handles)
Latency         | 0.5-1 µs        | 1-2 µs       | 1-3 µs       | 5-20 µs
Routable        | Limited         | No (L2 only) | Yes (L3/IP)  | Yes (TCP/IP)
CPU Overhead    | Minimal         | Minimal      | Minimal      | Low (TCP)
WAN Support     | No              | No           | Limited      | Yes
```

### 4.1 RoCE (RDMA over Converged Ethernet)

RoCE allows RDMA over standard Ethernet hardware, making it cheaper than
dedicated InfiniBand fabric.

**"Converged Ethernet"** means Ethernet that can carry both storage and network
traffic reliably, achieved through:

- **PFC (Priority Flow Control):** IEEE 802.1Qbb — pauses specific traffic
  classes instead of dropping packets when buffers fill up
- **ECN (Explicit Congestion Notification):** Signals congestion before drops
- **DCQCN:** Combines ECN with a congestion control algorithm

```
ROCE LOSSLESS SETUP (PFC)
==========================

Sender                    Switch                  Receiver
+------+                +--------+               +------+
| NIC  |---[packets]--->| Buffer |---[packets]-->| NIC  |
+------+                +--------+               +------+
                              |
                    Buffer fills up!
                              |
                    [PAUSE frame sent back]
                              |
                    Sender stops that priority class
                    (but other priority classes continue!)

PFC Pause = "Stop sending traffic of priority X"
           (unlike traditional PAUSE which stops everything)
```

**RoCEv1 vs RoCEv2:**
- **RoCEv1:** Encapsulates IB transport directly in Ethernet frames (L2 only,
  not routable across subnets)
- **RoCEv2:** Encapsulates IB transport in UDP/IP (L3 routable, the current
  standard)

### 4.2 iWARP (Internet Wide Area RDMA Protocol)

iWARP runs RDMA over TCP, making it:
- Routable over any IP network (including WAN)
- Lossless by default (TCP handles retransmission)
- Higher latency than IB or RoCE (due to TCP stack)
- Simpler to deploy (standard Ethernet switches, no PFC needed)

```
iWARP PROTOCOL STACK
=====================

+-----------------------------+
|     RDMA Application        |
+-----------------------------+
|     RDMAP (RDMA Protocol)   |   <-- RDMA verbs
+-----------------------------+
|     DDP (Direct Data Place) |   <-- places data directly in buffers
+-----------------------------+
|     MPA (Marker PDU Aligned)|   <-- allows TCP segmentation
+-----------------------------+
|     TCP / IP                |   <-- standard transport
+-----------------------------+
|     Ethernet                |
+-----------------------------+
```

**MPA (Marker PDU Aligned)** is a clever layer that inserts markers every 512
bytes into the TCP stream so the receiver can find message boundaries even
after TCP reassembly. This is necessary because TCP is a byte stream and does
not preserve message boundaries.

---

## 5. Linux Kernel RDMA Stack — Layer by Layer

### 5.1 Overview of the Stack

The Linux RDMA stack (also called the OFED stack — OpenFabrics Enterprise
Distribution) is organized in layers:

```
LINUX RDMA SOFTWARE STACK
==========================

+------------------------------------------------------------------+
|                    User Applications                              |
|         (MPI, databases, storage, custom apps)                    |
+------------------------------------------------------------------+
|                    User-Space Libraries                           |
|  libibverbs  |  librdmacm  |  libmpi  |  librxe  | libmlx5     |
+------------------------------------------------------------------+
      |                |
      | verbs calls    | CM calls
      | (ioctl/mmap)   | (sockets)
      v                v
+------------------------------------------------------------------+
|              Kernel RDMA Subsystem (drivers/infiniband/)          |
|  +--------------+  +-----------+  +-----------+  +-----------+  |
|  | IB Core      |  | RDMA CM   |  | IPoIB     |  | SRP       |  |
|  | (ib_core.ko) |  |(rdma_cm.ko|  |(ib_ipoib) |  |(ib_srp)   |  |
|  +--------------+  +-----------+  +-----------+  +-----------+  |
|         |                                                         |
|         v                                                         |
|  +------------------------------------------------------------------+
|  |              Hardware Provider Drivers                           |
|  | mlx5_ib   | mlx4_ib  | rxe (soft) | hns_roce | irdma | erdma  |
|  +------------------------------------------------------------------+
+------------------------------------------------------------------+
         |
         v
+------------------------------------------------------------------+
|              Physical Hardware (HCA / RNIC)                       |
|    Mellanox ConnectX  |  Intel E810  |  Chelsio T6  |  AMD      |
+------------------------------------------------------------------+
```

### 5.2 Key Kernel Modules

```
KERNEL MODULE MAP
=================

Module Name         | Role
--------------------|--------------------------------------------------
ib_core             | Core IB/RDMA subsystem; defines the verbs API
ib_uverbs           | Exposes verbs to user space via /dev/infiniband/
ib_umad             | User Mode Access to Management Datagrams
rdma_cm             | RDMA Connection Manager (kernel side)
ib_cm               | IB-specific connection management (CM)
ib_mad              | Management Datagram handling
ib_sa               | Subnet Administration queries
iw_cm               | iWARP connection management
mlx5_ib             | Mellanox ConnectX-5/6/7 driver
mlx4_ib             | Mellanox ConnectX-3 driver
rxe                 | Software RDMA (RoCE over any Ethernet NIC)
siw                 | Software iWARP
ib_ipoib            | IP over InfiniBand (uses RDMA HW for TCP/IP too)
ib_srp              | SCSI RDMA Protocol (storage)
nvmet-rdma          | NVMe over Fabrics (NVMe-oF) RDMA transport
```

### 5.3 The /dev and /sys Interface

```
RDMA DEVICE INTERFACE IN LINUX
================================

/dev/infiniband/
├── uverbs0        # User verbs for first HCA (ioctl interface)
├── uverbs1        # User verbs for second HCA
├── umad0          # Management datagrams for port 0
└── issm0          # Subnet management

/sys/class/infiniband/
├── mlx5_0/        # First HCA
│   ├── ports/
│   │   └── 1/
│   │       ├── state       # Port state (ACTIVE, DOWN, etc.)
│   │       ├── rate        # Link rate
│   │       ├── lid         # LID assigned by SM
│   │       └── gids/       # GID table
│   ├── fw_ver      # Firmware version
│   ├── hw_rev      # Hardware revision
│   └── node_guid   # Hardware GUID
└── mlx5_1/

/sys/class/net/
└── ib0/           # IPoIB network interface

ibstat             # Command to query state
ibv_devinfo        # Query HCA capabilities
```

### 5.4 Sysfs Exploration Commands

```bash
# List all RDMA devices
ls /sys/class/infiniband/

# Check port state
cat /sys/class/infiniband/mlx5_0/ports/1/state

# Check link rate
cat /sys/class/infiniband/mlx5_0/ports/1/rate

# Check LID
cat /sys/class/infiniband/mlx5_0/ports/1/lid

# Full device info
ibv_devinfo
ibv_devinfo -d mlx5_0

# Show all ports
ibstat mlx5_0
```

---

## 6. InfiniBand Verbs API — The Programming Interface

### 6.1 What "Verbs" Means

The term **"verbs"** in InfiniBand refers to the abstract programming interface
defined by the InfiniBand specification. Think of it like "system calls" but for
RDMA hardware.

The verbs API defines a set of operations (verbs) that any compliant RDMA
device must support. The implementation details differ by hardware vendor, but
the API is portable.

**Analogy:** Verbs are to RDMA what POSIX sockets are to TCP/IP networking —
a portable abstraction over different hardware.

### 6.2 The Resource Hierarchy

Every RDMA program creates resources in a specific hierarchy. Violating this
order causes errors:

```
RDMA RESOURCE HIERARCHY
========================

ibv_get_device_list()
        |
        v
ibv_open_device()  -->  struct ibv_context  (device handle)
        |
        |-----> ibv_query_device()     (get capabilities)
        |-----> ibv_query_port()       (get port info)
        |
        v
ibv_alloc_pd()  -->  struct ibv_pd  (Protection Domain)
        |
        |-----> ibv_reg_mr()  -->  struct ibv_mr  (Memory Region)
        |       (register application memory with NIC)
        |
        |-----> ibv_create_cq()  -->  struct ibv_cq  (Completion Queue)
        |       (where completions/notifications arrive)
        |
        |-----> ibv_create_qp()  -->  struct ibv_qp  (Queue Pair)
                (the actual communication endpoint)
                        |
                        v
                ibv_modify_qp()  (transition QP through states)
                        |
                        v
                ibv_post_send() / ibv_post_recv()
                (submit work requests)
                        |
                        v
                ibv_poll_cq()  (check for completions)
```

**Why this hierarchy?** Each parent resource provides a security and resource
boundary. A QP belongs to a PD. A memory region is registered with a PD. This
means a QP can only access memory registered in its own PD — hardware enforces
this isolation.

### 6.3 Key Data Structures

Understanding the data structures is essential before writing code:

```c
// --- Device ---
struct ibv_context {
    struct ibv_device *device;     // The actual hardware device
    struct ibv_context_ops ops;    // Function pointers to vendor impl
    int cmd_fd;                    // FD for kernel commands (/dev/uverbs0)
    int async_fd;                  // FD for async events
    int num_comp_vectors;          // Number of completion vectors (for MSI-X)
    // ... more internal fields
};

// --- Protection Domain ---
struct ibv_pd {
    struct ibv_context *context;   // Which device owns this PD
    uint32_t handle;               // Kernel handle
};

// --- Memory Region ---
struct ibv_mr {
    struct ibv_context *context;
    struct ibv_pd *pd;
    void *addr;                    // Start address of registered memory
    size_t length;                 // Length of the region
    uint32_t handle;
    uint32_t lkey;                 // Local key (used in work requests)
    uint32_t rkey;                 // Remote key (sent to peer for RDMA access)
};

// --- Completion Queue ---
struct ibv_cq {
    struct ibv_context *context;
    struct ibv_comp_channel *channel;  // Event notification channel
    void *cq_context;              // User-provided opaque context
    uint32_t handle;
    int cqe;                       // Number of CQ entries
};

// --- Queue Pair ---
struct ibv_qp {
    struct ibv_context *context;
    void *qp_context;              // User-provided opaque
    struct ibv_pd *pd;             // Protection domain
    struct ibv_cq *send_cq;        // Completion queue for sends
    struct ibv_cq *recv_cq;        // Completion queue for receives
    struct ibv_srq *srq;           // Shared receive queue (optional)
    uint32_t handle;
    uint32_t qp_num;               // The 24-bit QP number
    enum ibv_qp_state state;       // Current state machine state
    enum ibv_qp_type qp_type;      // RC, UC, UD, XRC, etc.
};
```

---

## 7. Protection Domains and Memory Registration

### 7.1 Protection Domains

A **Protection Domain (PD)** is the fundamental security boundary in RDMA.

**Mental model:** Think of a PD like a Unix process — just as a process provides
memory isolation between programs, a PD provides communication isolation between
RDMA endpoints.

```
PROTECTION DOMAIN ISOLATION
============================

Application A                       Application B
+------------------+               +------------------+
|  PD_A            |               |  PD_B            |
|  +----+  +----+  |               |  +----+  +----+  |
|  | QP |  | MR |  |               |  | QP |  | MR |  |
|  +----+  +----+  |               |  +----+  +----+  |
+------------------+               +------------------+

QP in PD_A can ONLY access MRs in PD_A
QP in PD_B can ONLY access MRs in PD_B
Hardware enforces this — no software check needed at data-path time
```

**Rules:**
1. A QP must belong to exactly one PD
2. A memory region must belong to exactly one PD
3. A QP can only use memory regions from its own PD
4. Remote RDMA access is protected by the rkey (remote key) mechanism

### 7.2 Memory Registration — The Critical Concept

Memory registration is one of the most important concepts in RDMA, and
understanding WHY it is needed makes everything else clearer.

**Problem:** The NIC needs to perform DMA (Direct Memory Access) — it needs to
read/write physical memory. But applications use virtual addresses, and the OS
may:
1. Swap pages to disk (making physical memory disappear)
2. Move pages in physical memory (while virtual address stays same)
3. Share pages between processes (copy-on-write)

**Solution:** Memory registration pins the pages:
1. The OS marks the registered pages as **non-swappable (pinned/locked)**
2. The OS creates a **mapping from virtual address → physical address pages**
3. This mapping is stored in the HCA's **Memory Translation Table (MTT)**
4. The HCA uses MTT to translate virtual addresses to physical for DMA

```
MEMORY REGISTRATION PROCESS
=============================

1. Application allocates buffer:
   void *buf = malloc(4096);  // virtual addr = 0x7f123456000
   
2. Registration call:
   ibv_reg_mr(pd, buf, 4096, IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_READ)
   
3. Kernel actions:
   a) Lock pages in RAM (mlock): prevents swapping
   b) Walk page tables to find physical pages:
      Virtual 0x7f123456000 -> Physical Page Frame 0x1a3b4c
   c) Build MTT entry in HCA:
      MTT[lkey] = { phys_addr = 0x1a3b4c000, length = 4096, 
                    permissions = RW }
   
4. Returns ibv_mr with:
   - lkey = 0xDEADBEEF  (local key, use in send/recv WRs)
   - rkey = 0xCAFEBABE  (remote key, share with peer for RDMA R/W)

HCA Memory Translation Table (MTT):
+-------+---------------+--------+-------------+
| lkey  | Physical Addr | Length | Permissions |
+-------+---------------+--------+-------------+
| 0xDE  | 0x1a3b4c000   | 4096   | RW          |
| 0xCA  | 0x2b4c5d000   | 8192   | R-only      |
+-------+---------------+--------+-------------+
```

### 7.3 Access Flags

When registering memory, you specify what operations are allowed:

```c
// Access flags for ibv_reg_mr()
enum ibv_access_flags {
    IBV_ACCESS_LOCAL_WRITE      = 1,  // Local QP can write (needed for recv)
    IBV_ACCESS_REMOTE_WRITE     = 2,  // Remote peer can do RDMA Write
    IBV_ACCESS_REMOTE_READ      = 4,  // Remote peer can do RDMA Read
    IBV_ACCESS_REMOTE_ATOMIC    = 8,  // Remote peer can do Atomic ops
    IBV_ACCESS_MW_BIND          = 16, // Memory Windows can be bound
    IBV_ACCESS_ZERO_BASED       = 32, // Addr in WR is offset from start
    IBV_ACCESS_ON_DEMAND        = 64, // On-Demand Paging (don't pin yet)
    IBV_ACCESS_HUGETLB          = 128,// Use huge pages for MTT
};
```

**Security model for remote access:**

```
RKEY SECURITY MODEL
====================

Machine 1 (Initiator):
  - Has: peer's virtual address + rkey

Machine 2 (Target):
  - Registered MR with rkey = 0xCAFEBABE, addr = 0x7fff0000, len = 4096

Machine 1 does RDMA Read:
  WR = { addr = 0x7fff0000, rkey = 0xCAFEBABE, len = 4096 }
  
HCA on Machine 2 checks:
  1. Is rkey 0xCAFEBABE valid? YES
  2. Is addr 0x7fff0000 within the registered region? YES
  3. Does rkey permit READ? YES
  --> DMA read proceeds, data sent back to Machine 1
  
If wrong rkey or out-of-bounds address:
  --> Hardware generates IBV_WC_REM_ACCESS_ERR (remote access error)
  --> Connection may be terminated
```

### 7.4 The Cost of Registration and Caching

Memory registration is **expensive**:
- Requires kernel call (no bypass)
- Pins physical pages (increases memory pressure)
- Creates MTT entries in HCA (limited resource)

**Expert optimization:** Use a **Memory Region Cache** — register large regions
up front and reuse them. Many RDMA libraries (UCX, libfabric) implement this.

```
MR CACHE STRATEGY
==================

Naive (Bad):
  for each message:
    ibv_reg_mr(...)   // EXPENSIVE!
    ibv_post_send(...)
    ibv_poll_cq(...)
    ibv_dereg_mr(...) // EXPENSIVE!

Optimized (Good):
  at startup:
    pool = ibv_reg_mr(pd, large_buf, 100MB, RW)  // ONE registration
  
  for each message:
    // Find pre-registered sub-region
    ibv_post_send(...)  // Uses pool's lkey
    ibv_poll_cq(...)
    // No dereg needed! Reuse pool.
```

---

## 8. Queue Pairs — The Heart of RDMA

### 8.1 What a Queue Pair Is

A **Queue Pair (QP)** is the fundamental communication endpoint in RDMA —
conceptually similar to a socket, but implemented entirely in hardware.

A QP consists of two queues:
1. **Send Queue (SQ):** Where you post Work Requests to send data
2. **Receive Queue (RQ):** Where you post buffers to receive incoming data

```
QUEUE PAIR INTERNAL STRUCTURE
==============================

                    SEND QUEUE (SQ)
                    +----+----+----+----+----+
Application    +--> | WR | WR | WR |    |    |  <-- you post here
posts WRs      |    +----+----+----+----+----+
               |           |
               |           | HCA processes WRs in order
               |           v
               |    [HCA hardware engine reads WR,
               |     performs DMA, sends packet]
               |           |
               |           v
               |    SEND COMPLETION QUEUE (send_cq)
               |    +---+---+---+---+
               +--- | CQ | CQ | CQ |   |   <-- you poll here
                    +---+---+---+---+

                    RECEIVE QUEUE (RQ)
                    +----+----+----+----+----+
Application    +--> | WR | WR | WR |    |    |  <-- you pre-post buffers
pre-posts      |    +----+----+----+----+----+
buffers        |           |
               |           | When packet arrives:
               |           v
               |    [HCA DMA's incoming data into next RQ buffer]
               |           |
               |           v
               |    RECEIVE COMPLETION QUEUE (recv_cq)
               |    +---+---+---+---+
               +--- | CQ | CQ | CQ |   |   <-- you poll here
                    +---+---+---+---+

Note: send_cq and recv_cq can be the SAME cq or DIFFERENT cqs.
```

### 8.2 QP Types

There are several types of Queue Pairs, each with different properties:

```
QP TYPE COMPARISON
==================

Type  | Full Name              | Connection | Reliability | Use Case
------|------------------------|------------|-------------|------------------
RC    | Reliable Connected     | 1:1        | Yes         | Most common; like TCP
UC    | Unreliable Connected   | 1:1        | No          | Rare; like UDP but connected
UD    | Unreliable Datagram    | 1:N        | No          | Multicast, discovery
RD    | Reliable Datagram      | 1:N        | Yes         | Deprecated
XRC   | Extended RC            | N:M        | Yes         | Many-to-many with less QPs
DC    | Dynamically Connected  | 1:N        | Yes         | Mellanox extension
SRD   | Scalable Reliable Datagram | 1:N   | Yes         | AWS EFA extension

RC = Reliable Connected (most important to learn first)
  - Like TCP: guarantees delivery, in-order
  - One QP per connection pair (1:1)
  - Supports: Send/Recv, RDMA Read, RDMA Write, Atomics

UD = Unreliable Datagram
  - Like UDP: fire and forget
  - One QP can communicate with MANY peers
  - Only supports: Send/Recv (no RDMA Read/Write!)
  - Used for: Service discovery, multicast
  - Messages limited to MTU size (4096 bytes for IB)
```

### 8.3 QP State Machine

A QP goes through a series of states before it can transfer data. This is one
of the trickiest parts for beginners:

```
QP STATE MACHINE
================

        ibv_create_qp()
               |
               v
         +----------+
         |  RESET   |  <-- Initial state after creation
         +----------+
               |
               | ibv_modify_qp(RESET -> INIT)
               | (set: port, pkey, access flags)
               v
         +----------+
         |   INIT   |  <-- Can post receives here (but no sends)
         +----------+
               |
               | ibv_modify_qp(INIT -> RTR)
               | (set: dest QPN, dest LID/GID, path MTU)
               v
         +----------+
         |   RTR    |  <-- Ready To Receive (peer can send to us now)
         +----------+     You can now post receives AND receives work
               |
               | ibv_modify_qp(RTR -> RTS)
               | (set: timeout, retry_cnt, rnr_retry, sq_psn, max_rd_atomic)
               v
         +----------+
         |   RTS    |  <-- Ready To Send (fully operational!)
         +----------+     You can post sends AND receives
               |
               | Error or explicit transition
               v
         +----------+
         |   SQD    |  <-- Send Queue Draining (completing in-flight)
         +----------+
               |
         +----------+
         |   SQE    |  <-- Send Queue Error (recoverable error)
         +----------+
               |
         +----------+
         |   ERR    |  <-- Error state (unrecoverable; must re-create QP)
         +----------+

KEY INSIGHT: You must transition the QP through these states in order.
The state machine ensures both sides are ready before data flows.
For RC QPs, the critical exchange is:
  Side A: RESET -> INIT -> RTR (knows side B's QPN/LID)
  Side B: RESET -> INIT -> RTR (knows side A's QPN/LID)
  Side A: RTR -> RTS
  Side B: RTR -> RTS
  
This exchange of QPN/LID is done OUT-OF-BAND (e.g., via TCP socket)
before the RDMA connection is established!
```

### 8.4 QP Parameters for State Transition

Each state transition requires specific parameters:

```c
struct ibv_qp_attr {
    enum ibv_qp_state   qp_state;      // Target state
    enum ibv_qp_state   cur_qp_state;  // Current state (for verification)
    enum ibv_mtu        path_mtu;      // MTU for the path (IBV_MTU_4096 etc)
    enum ibv_mig_state  path_mig_state;
    uint32_t            qkey;          // For UD QPs
    uint32_t            rq_psn;        // Starting packet sequence number for recv
    uint32_t            sq_psn;        // Starting packet sequence number for send
    uint32_t            dest_qp_num;   // REMOTE QP number (from peer)
    int                 qp_access_flags;
    struct ibv_qp_cap   cap;           // Queue capacities
    struct ibv_ah_attr  ah_attr;       // Address Handle attributes (LID/GID of peer)
    struct ibv_ah_attr  alt_ah_attr;   // Alternate path
    uint16_t            pkey_index;    // Partition key index
    uint16_t            alt_pkey_index;
    uint8_t             en_sqd_async_notify;
    uint8_t             sq_draining;
    uint8_t             max_rd_atomic; // Max outstanding RDMA reads/atomics (initiator)
    uint8_t             max_dest_rd_atomic;// Max outstanding RDMA reads/atomics (target)
    uint8_t             min_rnr_timer; // RNR (Receiver Not Ready) timer
    uint8_t             port_num;      // Physical port (1-based)
    uint8_t             timeout;       // Timeout for RC (4.096µs * 2^timeout)
    uint8_t             retry_cnt;     // Retry count for RC
    uint8_t             rnr_retry;     // RNR retry count
    uint8_t             alt_port_num;
    uint8_t             alt_timeout;
};

// For INIT -> RTR transition, ah_attr contains:
struct ibv_ah_attr {
    struct ibv_global_route grh;       // GRH (for RoCE or cross-subnet)
    uint16_t          dlid;            // Destination LID (for IB)
    uint8_t           sl;              // Service Level
    uint8_t           src_path_bits;   // Path bits
    uint8_t           static_rate;     // Rate limit
    uint8_t           is_global;       // 1 if using GRH
    uint8_t           port_num;        // Source port
};
```

---

## 9. Work Requests and Scatter-Gather Lists

### 9.1 Work Requests

A **Work Request (WR)** is a descriptor that tells the HCA what operation to
perform. You post WRs to QPs; the HCA processes them asynchronously.

```
WORK REQUEST STRUCTURE
======================

struct ibv_send_wr {
    uint64_t         wr_id;       // Your ID; returned in completion
    struct ibv_send_wr *next;     // Linked list (chain multiple WRs)
    struct ibv_sge  *sg_list;     // Scatter-gather list (what to send)
    int              num_sge;     // Number of SGE entries
    enum ibv_wr_opcode opcode;    // SEND, RDMA_WRITE, RDMA_READ, etc.
    int              send_flags;  // IBV_SEND_SIGNALED, INLINE, FENCE
    union {
        uint32_t     imm_data;    // Immediate data (32-bit out-of-band value)
        uint32_t     invalidate_rkey;
    };
    union {
        struct {
            uint64_t remote_addr; // RDMA target address (for Read/Write)
            uint32_t rkey;        // Remote key (for Read/Write)
        } rdma;
        struct {
            uint64_t remote_addr;
            uint64_t compare_add; // Atomic: compare value / add value
            uint64_t swap;        // Atomic: swap value
            uint32_t rkey;
        } atomic;
        struct {
            struct ibv_ah *ah;    // Address Handle (for UD sends)
            uint32_t remote_qpn; // Dest QP number (for UD)
            uint32_t remote_qkey;// Dest Q_Key (for UD)
        } ud;
    } wr;
};

struct ibv_recv_wr {
    uint64_t         wr_id;
    struct ibv_recv_wr *next;
    struct ibv_sge  *sg_list;    // Where to put incoming data
    int              num_sge;
};
```

### 9.2 Scatter-Gather Elements

**Scatter-Gather (SGE)** allows you to describe non-contiguous memory as if it
were a single buffer. This is extremely powerful:

```
SCATTER-GATHER CONCEPT
=======================

Without Scatter-Gather:
  Send buffer must be contiguous in memory:
  [header][data][trailer] -- must be one malloc

With Scatter-Gather:
  Three separate memory regions, sent as ONE packet:
  
  SGE[0]: addr=0x1000, len=20, lkey=X  --> [header 20 bytes]
  SGE[1]: addr=0x5000, len=4000, lkey=Y --> [data 4000 bytes]
  SGE[2]: addr=0x9000, len=4, lkey=Z   --> [trailer 4 bytes]
  
  The HCA gathers these into one packet:
  [header][........data........][trailer]
  
  On receive side (scatter):
  SGE[0]: addr=0x2000, len=20, lkey=A  <-- header goes here
  SGE[1]: addr=0x6000, len=4000, lkey=B<-- data goes here  
  SGE[2]: addr=0xA000, len=4, lkey=C  <-- trailer goes here
```

```c
struct ibv_sge {
    uint64_t addr;   // Virtual address of the buffer
    uint32_t length; // Length of this buffer segment
    uint32_t lkey;   // Local key from ibv_reg_mr
};
```

**Why SGE matters:**
- No data copies needed for protocol headers/trailers
- Can work directly with application data structures
- Zero-copy for complex message formats

### 9.3 Send Flags

```c
enum ibv_send_flags {
    IBV_SEND_FENCE     = 1, // All prior sends must complete first
    IBV_SEND_SIGNALED  = 2, // Generate a completion (CQE) for this WR
    IBV_SEND_SOLICITED = 4, // Peer gets solicited event notification
    IBV_SEND_INLINE    = 8, // Data in sg_list is inlined into WR (no DMA!)
};
```

**IBV_SEND_SIGNALED** is critical for understanding RDMA performance:

```
SELECTIVE SIGNALING (CRITICAL OPTIMIZATION)
============================================

Without selective signaling (every WR generates a CQE):
  Post WR1 -> CQE1 -> Poll -> Post WR2 -> CQE2 -> Poll -> ...
  (lots of polling, CQ overhead)

With selective signaling (only some WRs generate CQEs):
  Post WR1 (no signal)
  Post WR2 (no signal)
  Post WR3 (no signal)
  ...
  Post WR64 (SIGNALED) -> CQE -> Poll (one poll covers 64 sends!)
  
This batching dramatically increases throughput.
Rule: ALWAYS signal at least every max_send_wr/2 WRs to avoid SQ overflow.

IBV_SEND_INLINE: For small messages (typically < 64 bytes), the data is
copied directly into the WR descriptor and sent immediately without DMA.
This reduces latency for small messages by eliminating the DMA setup.
```

---

## 10. Completion Queues and Event Handling

### 10.1 Completion Queue Structure

A **Completion Queue (CQ)** is where the HCA reports the result of completed
Work Requests. Think of it as a ring buffer shared between hardware and software.

```
COMPLETION QUEUE INTERNALS
===========================

CQ Ring Buffer (shared between HCA and CPU):
+-----+-----+-----+-----+-----+-----+-----+-----+
| CQE | CQE | CQE | CQE |     |     |     |     |
+-----+-----+-----+-----+-----+-----+-----+-----+
  ^                        ^
  |                        |
Consumer Pointer        Producer Pointer
(your code reads here)  (HCA writes here)

CQE (Completion Queue Entry):
+--------+--------+--------+--------+--------+--------+
| wr_id  | status | opcode | byte_len | qp_num | ...  |
+--------+--------+--------+--------+--------+--------+
  |         |
  |         +-- IBV_WC_SUCCESS or error code
  +-- The wr_id you put in the WR
```

### 10.2 Completion Queue Entry Fields

```c
struct ibv_wc {
    uint64_t          wr_id;        // Your WR ID (from send/recv WR)
    enum ibv_wc_status status;      // Success or error
    enum ibv_wc_opcode opcode;      // What operation completed
    uint32_t          vendor_err;   // Vendor-specific error info
    uint32_t          byte_len;     // Bytes transferred (recv only)
    union {
        __be32        imm_data;     // Immediate data (if applicable)
        uint32_t      invalidate_rkey;
    };
    uint32_t          qp_num;       // Which QP this completion is from
    uint32_t          src_qp;       // Source QP number (UD receives)
    int               wc_flags;     // IBV_WC_GRH, IBV_WC_WITH_IMM, etc.
    uint16_t          pkey_index;
    uint16_t          slid;         // Source LID (UD receives)
    uint8_t           sl;           // Service Level
    uint8_t           dlid_path_bits;
};

// Status codes (know these by heart!):
enum ibv_wc_status {
    IBV_WC_SUCCESS          = 0,  // All good
    IBV_WC_LOC_LEN_ERR      = 1,  // Local length error (SGE too small)
    IBV_WC_LOC_QP_OP_ERR    = 2,  // Local QP operation error
    IBV_WC_LOC_EEC_OP_ERR   = 3,  // Local EE context operation error
    IBV_WC_LOC_PROT_ERR     = 4,  // Local protection error (bad lkey)
    IBV_WC_WR_FLUSH_ERR     = 5,  // QP in error state; WR flushed
    IBV_WC_MW_BIND_ERR      = 6,  // Memory Window bind error
    IBV_WC_BAD_RESP_ERR     = 7,  // Unexpected response received
    IBV_WC_LOC_ACCESS_ERR   = 8,  // Local access violation
    IBV_WC_REM_INV_REQ_ERR  = 9,  // Remote invalid request
    IBV_WC_REM_ACCESS_ERR   = 10, // Remote access error (bad rkey)
    IBV_WC_REM_OP_ERR       = 11, // Remote operation error
    IBV_WC_RETRY_EXC_ERR    = 12, // Retry exceeded (link down?)
    IBV_WC_RNR_RETRY_EXC_ERR=13, // RNR retry exceeded (recv not posted)
    IBV_WC_LOC_RDD_VIOL_ERR = 14,
    IBV_WC_REM_INV_RD_REQ_ERR=15,
    IBV_WC_REM_ABORT_ERR    = 16,
    IBV_WC_INV_EECN_ERR     = 17,
    IBV_WC_INV_EEC_STATE_ERR= 18,
    IBV_WC_FATAL_ERR        = 19, // HCA fatal error
    IBV_WC_RESP_TIMEOUT_ERR = 20, // Response timeout
    IBV_WC_GENERAL_ERR      = 21, // General error
};
```

### 10.3 Polling vs Event-Driven Notification

There are two ways to handle completions:

```
POLLING vs EVENT-DRIVEN
========================

1. BUSY POLLING (lowest latency, highest CPU):
   
   while (running) {
       n = ibv_poll_cq(cq, batch_size, wc_array);
       if (n > 0) {
           // Process completions
           process_completions(wc_array, n);
       }
       // No sleep! Spin continuously.
   }
   
   Latency: ~1 µs (poll catches completion immediately)
   CPU: 100% of one core dedicated
   Best for: Latency-sensitive applications (trading, HPC)

2. EVENT-DRIVEN (lower CPU, higher latency):
   
   // Create completion channel (file descriptor)
   struct ibv_comp_channel *ch = ibv_create_comp_channel(ctx);
   
   // Associate CQ with channel
   struct ibv_cq *cq = ibv_create_cq(ctx, 100, NULL, ch, 0);
   
   // Request notification
   ibv_req_notify_cq(cq, 0);
   
   // Block on FD (like epoll)
   pollfd.fd = ch->fd;
   pollfd.events = POLLIN;
   poll(&pollfd, 1, timeout_ms);
   
   // Acknowledge the event
   ibv_get_cq_event(ch, &cq, &ctx);
   ibv_ack_cq_events(cq, 1);
   
   // Now poll for completions
   n = ibv_poll_cq(cq, batch_size, wc);
   
   // Re-arm the notification
   ibv_req_notify_cq(cq, 0);
   
   Latency: 10-50 µs (interrupt latency)
   CPU: Minimal (sleeps waiting for events)
   Best for: Throughput-focused, many connections, cloud environments

HYBRID APPROACH (adaptive polling):
   // Spin for a short burst, then sleep
   deadline = now() + 10us;
   while (now() < deadline) {
       n = ibv_poll_cq(cq, batch, wc);
       if (n > 0) return handle(wc, n);
   }
   // No completion in 10µs, sleep on event
   wait_for_event(ch);
```

---

## 11. RDMA Operations: Send/Recv, Read, Write, Atomic

### 11.1 Operation Types Overview

```
RDMA OPERATION TAXONOMY
========================

CHANNEL SEMANTICS (two-sided — both sides participate):
  +----------+                              +----------+
  |  Sender  |  --- SEND + data ------->   | Receiver |
  +----------+                              +----------+
  
  Both sides must post a WR:
  - Sender posts SEND WR to SQ
  - Receiver must have pre-posted RECV WR to RQ
  - Receiver's CPU IS involved (at least to pre-post the buffer)

MEMORY SEMANTICS (one-sided — only initiator participates):
  +------------+                            +----------+
  | Initiator  |  --- RDMA WRITE -------->  |  Target  |
  +------------+   (data goes directly      +----------+
                    to target memory;
                    target CPU unaware!)

  Only initiator posts a WR. Target CPU is NOT interrupted.
  Target must have pre-registered memory and shared rkey.

ATOMIC OPERATIONS (one-sided, special):
  +------------+                            +----------+
  | Initiator  |  --- FETCH_AND_ADD -----> |  Target  |
  +------------+   (reads+modifies target  +----------+
                    memory atomically)
```

### 11.2 Send/Receive (Two-Sided)

```
SEND/RECEIVE FLOW
=================

Setup Phase (both sides):
  Server: ibv_post_recv(recv_wr)  // Pre-post receive buffer
  
Transfer Phase:
  Client: ibv_post_send(send_wr with opcode=IBV_WR_SEND)
       |
       | [network]
       v
  Server HCA: received data, writes to pre-posted recv buffer
       |
       v
  Server CQ: RECV completion appears
  Server: ibv_poll_cq() -> sees data arrived, len=X bytes
  
CRITICAL: If server has no pre-posted recv buffer when data arrives:
  - RNR (Receiver Not Ready) NAK is sent back
  - Sender retries RNR_RETRY times
  - If retry exceeded: IBV_WC_RNR_RETRY_EXC_ERR
  
RULE: ALWAYS pre-post recv WRs BEFORE telling the peer to send!
```

### 11.3 RDMA Write

```
RDMA WRITE FLOW
===============

Target (Machine 2) Setup (one-time):
  ibv_reg_mr(pd, buf, len, IBV_ACCESS_REMOTE_WRITE)
  --> share buf_addr and mr->rkey with Initiator (out-of-band, e.g., TCP)

Initiator (Machine 1) Write:
  wr.opcode = IBV_WR_RDMA_WRITE
  wr.wr.rdma.remote_addr = target_buf_addr  // Received from target
  wr.wr.rdma.rkey = target_rkey            // Received from target
  wr.sg_list = [{local_buf, len, lkey}]    // Source data
  ibv_post_send(qp, &wr, &bad_wr)
  
  [HCA reads local_buf via DMA]
  [HCA sends data over fabric]
  [Remote HCA writes directly into target_buf via DMA]
  
  Target CPU is NEVER interrupted!
  Target application can poll the buffer for a "magic value" to know data arrived.

RDMA WRITE WITH IMMEDIATE:
  wr.opcode = IBV_WR_RDMA_WRITE_WITH_IMM
  wr.imm_data = htonl(42)  // 32-bit value
  
  This IS two-sided! The target receives:
  - A RECV completion (consumes a pre-posted recv buffer)
  - The immediate data value (42)
  - But the actual data goes to the RDMA addr, not the recv buffer!
  
  Use case: Notify target which region was written, without extra messages.
```

### 11.4 RDMA Read

```
RDMA READ FLOW
==============

Target (Machine 2) Setup:
  ibv_reg_mr(pd, buf, len, IBV_ACCESS_REMOTE_READ)
  --> share buf_addr and mr->rkey with Initiator

Initiator (Machine 1) Read:
  wr.opcode = IBV_WR_RDMA_READ
  wr.wr.rdma.remote_addr = target_buf_addr
  wr.wr.rdma.rkey = target_rkey
  wr.sg_list = [{local_dst_buf, len, lkey}]  // WHERE to put the data locally
  ibv_post_send(qp, &wr, &bad_wr)
  
  [HCA sends READ REQUEST to remote]
  [Remote HCA reads from target_buf via DMA]
  [Remote HCA sends data back]
  [Local HCA writes data into local_dst_buf]
  
  Completion appears in local send CQ.
  Target CPU is NEVER interrupted!

IMPORTANT DIFFERENCES:
  - RDMA Read generates TWICE the network traffic (request + response)
  - RDMA Write generates ONCE the network traffic (just the write)
  - RDMA Read is limited by max_rd_atomic (max outstanding reads)
  - Typical limit: 16-32 outstanding RDMA Reads per QP
```

### 11.5 Atomic Operations

Atomic operations are **indivisible** — the HCA guarantees no other operation
can see an intermediate state:

```
ATOMIC OPERATIONS
=================

1. FETCH_AND_ADD (FAA):
   - Reads 64-bit value at remote_addr
   - Adds compare_add to it
   - Writes result back
   - Returns ORIGINAL value
   
   Use case: Distributed counter, queue tail pointer

2. COMPARE_AND_SWAP (CAS):
   - Reads 64-bit value at remote_addr
   - If value == compare_add: write swap value
   - If value != compare_add: no change
   - Returns ORIGINAL value (allows retry if CAS failed)
   
   Use case: Lock-free data structures, distributed mutex

ATOMICS CONSTRAINTS:
   - Address must be 8-byte aligned
   - Only 8-byte operands
   - Limited by max_rd_atomic (same as RDMA Read)
   - NOT all hardware supports atomics equally (check device caps)

EXAMPLE: Distributed Lock Using CAS
  // Attempt to acquire lock: CAS(lock_addr, 0, 1)
  wr.opcode = IBV_WR_ATOMIC_CMP_AND_SWP
  wr.wr.atomic.remote_addr = lock_addr
  wr.wr.atomic.rkey = lock_rkey
  wr.wr.atomic.compare_add = 0  // Expected: unlocked
  wr.wr.atomic.swap = 1         // Set to: locked
  wr.sg_list = [{result_buf, 8, lkey}]  // Will hold original value
  
  // If result == 0: we got the lock
  // If result == 1: someone else has it; retry
```

---

## 12. Connection Management (RDMA_CM)

### 12.1 The Problem: Out-of-Band Exchange

Before a QP can become RTS (Ready To Send), both sides need to exchange:
- QP number (dest_qp_num)
- LID / GID (for ah_attr)
- Initial PSN values
- Maximum QP parameters

This information exchange is called **out-of-band signaling** and must happen
through a separate channel (often a TCP socket or a management plane).

**RDMA CM (Connection Manager)** automates this process, providing a
socket-like interface for RDMA connections:

### 12.2 RDMA CM Concepts

```
RDMA CM ABSTRACTION
===================

rdma_cm wraps the QP exchange into a socket-like API:

Server:                              Client:
rdma_create_id()                     rdma_create_id()
rdma_bind_addr()                     
rdma_listen()                        
                                     rdma_resolve_addr()  (DNS-like lookup)
                                     rdma_resolve_route()  (path computation)
                                     rdma_connect()
rdma_get_cm_event() -> CONNECT_REQ  
rdma_create_qp()   <- create QP here
rdma_accept()                        rdma_get_cm_event() -> ESTABLISHED
rdma_get_cm_event() -> ESTABLISHED   
   [RDMA communication begins]       [RDMA communication begins]
rdma_disconnect()                    rdma_disconnect()
rdma_get_cm_event() -> DISCONNECTED  rdma_get_cm_event() -> DISCONNECTED
rdma_destroy_qp()                    rdma_destroy_qp()
rdma_destroy_id()                    rdma_destroy_id()
```

### 12.3 CM Event Types

```c
enum rdma_cm_event_type {
    RDMA_CM_EVENT_ADDR_RESOLVED,     // rdma_resolve_addr() completed
    RDMA_CM_EVENT_ADDR_ERROR,        // rdma_resolve_addr() failed
    RDMA_CM_EVENT_ROUTE_RESOLVED,    // rdma_resolve_route() completed
    RDMA_CM_EVENT_ROUTE_ERROR,       // rdma_resolve_route() failed
    RDMA_CM_EVENT_CONNECT_REQUEST,   // Server: client wants to connect
    RDMA_CM_EVENT_CONNECT_RESPONSE,
    RDMA_CM_EVENT_CONNECT_ERROR,     // Connection failed
    RDMA_CM_EVENT_UNREACHABLE,       // Destination not reachable
    RDMA_CM_EVENT_REJECTED,          // Connection rejected by server
    RDMA_CM_EVENT_ESTABLISHED,       // Connection established!
    RDMA_CM_EVENT_DISCONNECTED,      // Connection closed
    RDMA_CM_EVENT_DEVICE_REMOVAL,    // HCA was removed (hot-plug)
    RDMA_CM_EVENT_MULTICAST_JOIN,
    RDMA_CM_EVENT_MULTICAST_ERROR,
    RDMA_CM_EVENT_ADDR_CHANGE,       // Address changed
    RDMA_CM_EVENT_TIMEWAIT_EXIT,     // QP exited TIME_WAIT
};
```

### 12.4 Private Data in CM Messages

CM messages can carry **private data** (up to 56 bytes for CONNECT, 148 for
ACCEPT) — this is how applications exchange initial parameters:

```c
// Server side: private data in CONNECT_REQUEST
struct rdma_conn_param {
    const void *private_data;      // App-specific data
    uint8_t private_data_len;      // 0-56 bytes
    uint8_t responder_resources;   // Max incoming RDMA reads
    uint8_t initiator_depth;       // Max outgoing RDMA reads
    uint8_t flow_control;
    uint8_t retry_count;           // RC retry count
    uint8_t rnr_retry_count;       // RC RNR retry count
    uint8_t srq;                   // 1 if using SRQ
    uint32_t qp_num;               // QP number (filled by rdma_cm)
};

// Use private_data to exchange application params like:
struct my_app_params {
    uint64_t buf_addr;    // My RDMA buffer address
    uint32_t buf_rkey;    // My RDMA buffer rkey
    uint32_t buf_size;    // Buffer size
};
```

---

## 13. InfiniBand Fabric: Switches, Routers, Subnet Manager

### 13.1 Subnet Manager in Depth

The **Subnet Manager (SM)** is the control plane of an InfiniBand fabric. There
is exactly one Active SM per subnet (others may run in Standby for failover).

```
SUBNET MANAGER RESPONSIBILITIES
================================

1. DISCOVERY:
   - Queries all nodes via management datagrams (MADs)
   - Discovers all HCAs, switches, and their connections
   - Builds a complete topology map

2. LID ASSIGNMENT:
   - Assigns unique 16-bit LIDs to every HCA port
   - Stores these in Switch Linear Forwarding Tables (LFT)

3. ROUTING:
   - Computes paths between all node pairs
   - Programs LFTs (forwarding tables) in all switches
   - Algorithms: Min-hop, ECMP, Escape routing, etc.

4. MONITORING:
   - Periodically sweeps fabric to detect changes
   - Handles port up/down events
   - Re-routes around failures

5. PARTITION MANAGEMENT:
   - Manages PKeys (partition keys) for multi-tenancy
   - Like VLANs in Ethernet

SM SOFTWARE:
   OpenSM    -- Open-source SM (most common in Linux HPC)
   MLNX-OFED -- Mellanox's SM implementation
   UFM       -- Mellanox's Unified Fabric Manager (enterprise)

START OPENSM:
   opensm -g <port_guid> &
   
   Or as a service:
   systemctl start opensm
```

### 13.2 Switch Forwarding Tables

```
SWITCH FORWARDING TABLE (LFT)
==============================

Physical switch has 36 ports (example):
Port 1: Connected to HCA on Node A (LID 1)
Port 2: Connected to HCA on Node B (LID 2)
Port 3: Connected to another switch (LID 3, 4, 5, ...)
...

LFT (Linear Forwarding Table):
+-----+------+
| LID | Port |
+-----+------+
|  1  |  1   |  --> Packets for LID 1 go out port 1
|  2  |  2   |  --> Packets for LID 2 go out port 2
|  3  |  3   |  --> Packets for LID 3 go out port 3
|  4  |  3   |  --> Packets for LID 4 also go out port 3 (via next switch)
|  5  |  3   |  --> Packets for LID 5 also go out port 3
+-----+------+

This is the ENTIRE routing algorithm in hardware:
  receive_packet(pkt):
    dst_lid = pkt.lrh.dlid
    out_port = LFT[dst_lid]
    forward(pkt, out_port)

It's that simple! All routing complexity is in the SM computing the LFT.
```

### 13.3 Fat Tree Topology (Most Common in HPC)

```
FAT TREE TOPOLOGY
=================

2-Level Fat Tree (k=4 example, k=ports per switch)

                    [Core Switches]
                    +---+   +---+
                    | S5|   | S6|
                    +---+   +---+
                   /|\ /\  /|\ /\
                  / | X  \/ | X  \
                 /  |/    \/|    \
        +---+  +---+  +---+  +---+
        | S1|  | S2|  | S3|  | S4|   [Leaf Switches]
        +---+  +---+  +---+  +---+
        |\ |   |\ |   |\ |   |\ |
        | \|   | \|   | \|   | \|
      H1  H2  H3  H4  H5  H6  H7  H8  [Hosts/HCAs]

Properties of Fat Tree:
  - Bisection bandwidth: FULL (every host can talk to every other host
    at full speed simultaneously, if routing is good)
  - Non-blocking: No congestion if routes are spread across paths
  - Fault tolerant: Multiple paths between any pair
  - Scales: 3-level fat tree with k=48 switches = 27,648 hosts

ROUTING CHALLENGE:
  For any host pair, there are k/2 equal-cost paths (ECMP).
  Subnet Manager must spread traffic across these paths.
  Common algorithms:
    - FTREE (fat-tree specific, near-optimal)
    - SSSP (single-source shortest paths, simpler)
    - DOR (dimension-order routing for torus)
```

### 13.4 InfiniBand Management Datagram (MAD) Protocol

```
MAD PROTOCOL
============

MADs are special management packets in IB. The SM uses them to:
  - Query node information (NodeInfo MAD)
  - Set port states (PortInfo MAD)
  - Set forwarding tables (LinearForwardingTable MAD)
  - Read performance counters (PerfMgt MAD)

MAD Structure:
+--------+--------+--------+--------+--------+
| Header | Class  | Method | AttrID | Attr   |
|  24B   | 1B     | 1B     | 2B     | Data   |
+--------+--------+--------+--------+--------+

Management Classes:
  0x01 = Subnet Management (SM)
  0x03 = Subnet Administration (SA) -- path record lookups
  0x04 = Performance Management (PM) -- counter queries
  0x06 = Device Management
  0x0A = General Management

EXAMPLE: Reading PortInfo
  MAD { Class=SM, Method=GET, AttrID=PortInfo, AttrMod=port_num }
  Response: { state, physical_state, LID, LMC, MTU, speed, ... }
```

---

## 14. Shared Receive Queues (SRQ)

### 14.1 The Scalability Problem

Each RC QP needs its own Receive Queue with pre-posted buffers.

```
WITHOUT SRQ (N=1000 QPs, each needing 100 recv buffers):
  1000 QPs * 100 buffers * 4096 bytes = ~400 MB pinned memory!
  
  And you must pre-post to EVERY QP, even if most are idle.
  
WITH SRQ (1 SRQ shared by 1000 QPs):
  1 SRQ * 100 buffers * 4096 bytes = ~400 KB pinned memory!
  
  Buffers are consumed from the pool only when data actually arrives.
```

### 14.2 SRQ Operation

```
SRQ OPERATION
=============

                 +----------------------------------+
                 |  Shared Receive Queue (SRQ)      |
                 |  [buf0][buf1][buf2][buf3][buf4]  |
                 +----------------------------------+
                      /        |        \
                     /         |         \
                    /          |          \
              +------+     +------+     +------+
              |  QP1 |     |  QP2 |     |  QP3 |
              +------+     +------+     +------+
              
When QP1 receives data:
  HCA takes buf0 from SRQ, places data there
  CQE for QP1 appears in QP1's recv_cq
  
When QP2 receives data:
  HCA takes buf1 from SRQ, places data there
  CQE for QP2 appears in QP2's recv_cq
  
SRQ_LIMIT EVENT:
  When SRQ drops below srq_attr.srq_limit:
  Async event generated -> IBV_EVENT_SRQ_LIMIT_REACHED
  You must re-post buffers!
```

```c
// Creating an SRQ
struct ibv_srq_init_attr srq_attr = {
    .attr = {
        .max_wr = 1000,   // Total receive buffers
        .max_sge = 1,
        .srq_limit = 100, // Alert when below this
    }
};
struct ibv_srq *srq = ibv_create_srq(pd, &srq_attr);

// Creating QP with SRQ
struct ibv_qp_init_attr qp_attr = {
    .srq = srq,           // Use this SRQ instead of individual RQ
    .send_cq = send_cq,
    .recv_cq = recv_cq,
    // ...
};
struct ibv_qp *qp = ibv_create_qp(pd, &qp_attr);

// Posting to SRQ (not to QP!)
ibv_post_srq_recv(srq, recv_wr, &bad_wr);
```

---

## 15. Memory Windows and On-Demand Paging

### 15.1 Memory Windows

**Memory Windows (MW)** are a mechanism to grant fine-grained, revocable remote
access to sub-regions of a registered memory region.

**Why MWs?** Registering an MR with REMOTE_WRITE gives remote access to the
ENTIRE MR. But you may want to grant access to only a specific sub-range,
or revoke access without deregistering the whole MR.

```
MEMORY WINDOW USE CASE
=======================

Registered MR:
+-----------------------------------------------------------+
|                   Large Buffer (1GB)                       |
|  [region_A: addr 0x0-0xFFF] [region_B: addr 0x1000-0x1FFF]|
+-----------------------------------------------------------+
  rkey = 0x1234 (grants access to ENTIRE buffer!)

With Memory Window (Type 2B):
  MW1 bound to [0x0-0xFFF]    -> separate rkey_A (revocable!)
  MW2 bound to [0x1000-0x1FFF]-> separate rkey_B (revocable!)
  
  Give rkey_A to Client_A, rkey_B to Client_B.
  To revoke Client_A's access: ibv_bind_mw(mw1, qp, NULL)
  (No deregistration needed!)
```

### 15.2 On-Demand Paging (ODP)

**On-Demand Paging** allows RDMA without pinning memory:

```
ODP CONCEPT
===========

Traditional MR:
  ibv_reg_mr() --> immediately pins ALL pages
  Pages cannot be swapped for duration of MR
  Registration is slow (must pin every page now)
  
ODP MR (IBV_ACCESS_ON_DEMAND):
  ibv_reg_mr() --> registers the VIRTUAL ADDRESS RANGE only
  Pages are NOT pinned immediately
  
  When HCA needs to access a page:
  1. HCA detects page fault (page not in MTT or not present)
  2. HCA sends interrupt to OS
  3. OS faults in the page (loads from swap if needed)
  4. OS adds page to HCA's MTT
  5. HCA retries the DMA
  
  Benefits:
  - Faster registration (no upfront pinning)
  - Enables overcommit (total MR size > physical RAM)
  - Pages can still be swapped when not in use
  
  Drawbacks:
  - First access latency penalty (page fault)
  - More complex HCA hardware required (needs MMU notifier)
  
Implicit ODP (mlx5):
  ibv_reg_mr(pd, 0, UINT64_MAX, IBV_ACCESS_ON_DEMAND)
  Register the ENTIRE virtual address space!
  No need to register individual buffers.
  The HCA handles everything on-demand.
```

---

## 16. Linux Kernel RDMA Stack — Driver Architecture

### 16.1 The ib_core Module

`ib_core` is the master module that defines the in-kernel RDMA abstraction:

```
IB_CORE INTERNAL ARCHITECTURE
==============================

+------------------------------------------------------------------+
|                         ib_core.ko                               |
|                                                                   |
|  +-------------------+        +----------------------------+     |
|  |   Device Registry |        |   Verb Dispatch Layer      |     |
|  |   (ib_devices[])  |        |   (function pointer table) |     |
|  +-------------------+        +----------------------------+     |
|            |                              |                       |
|            v                             v                        |
|  +-------------------+        +----------------------------+     |
|  | Client Notifiers  |        |   MAD Agent Subsystem      |     |
|  | (ib_register_     |        |   (management datagrams)   |     |
|  |  client())        |        |                            |     |
|  +-------------------+        +----------------------------+     |
|            |                              |                       |
|            v                             v                        |
|  +-------------------+        +----------------------------+     |
|  | GID Cache         |        |   Path Record Cache        |     |
|  | (gid_table)       |        |   (path lookups)           |     |
|  +-------------------+        +----------------------------+     |
+------------------------------------------------------------------+
                    |                    |
           +--------+                   +--------+
           v                                     v
  +------------------+               +------------------+
  |  mlx5_ib.ko      |               |  rxe.ko          |
  |  (HW driver)     |               |  (SW emulation)  |
  +------------------+               +------------------+
```

### 16.2 The Provider (Driver) Interface

Hardware vendors implement the `ib_device_ops` interface:

```c
// From include/rdma/ib_verbs.h
struct ib_device_ops {
    // Device management
    int (*query_device)(struct ib_device *device,
                        struct ib_device_attr *device_attr,
                        struct ib_udata *udata);
    int (*query_port)(struct ib_device *device, u32 port_num,
                      struct ib_port_attr *port_attr);
    
    // Protection Domain
    int (*alloc_pd)(struct ib_pd *pd, struct ib_udata *udata);
    void (*dealloc_pd)(struct ib_pd *pd, struct ib_udata *udata);
    
    // Memory Registration
    struct ib_mr *(*reg_user_mr)(struct ib_pd *pd, u64 start, u64 length,
                                  u64 virt_addr, int access_flags,
                                  struct ib_udata *udata);
    int (*dereg_mr)(struct ib_mr *mr, struct ib_udata *udata);
    
    // Queue Pair
    struct ib_qp *(*create_qp)(struct ib_pd *pd,
                                struct ib_qp_init_attr *qp_init_attr,
                                struct ib_udata *udata);
    int (*modify_qp)(struct ib_qp *qp, struct ib_qp_attr *qp_attr,
                     int qp_attr_mask, struct ib_udata *udata);
    int (*destroy_qp)(struct ib_qp *qp, struct ib_udata *udata);
    
    // Send/Receive (kernel-space only, user-space uses doorbell)
    int (*post_send)(struct ib_qp *qp, const struct ib_send_wr *send_wr,
                     const struct ib_send_wr **bad_send_wr);
    int (*post_recv)(struct ib_qp *qp, const struct ib_recv_wr *recv_wr,
                     const struct ib_recv_wr **bad_recv_wr);
    
    // Completion Queue
    struct ib_cq *(*create_cq)(struct ib_device *device,
                                const struct ib_cq_init_attr *attr,
                                struct ib_udata *udata);
    int (*poll_cq)(struct ib_cq *ibcq, int num_entries, struct ib_wc *wc);
    int (*req_notify_cq)(struct ib_cq *ibcq, enum ib_cq_notify_flags flags);
    void (*destroy_cq)(struct ib_cq *ibcq, struct ib_udata *udata);
    
    // ... many more ops
};
```

### 16.3 User Space to Kernel Communication

The `ib_uverbs` module bridges user space to the kernel:

```
USER-KERNEL COMMUNICATION FLOW
================================

User Space                            Kernel Space
+------------------+                  +------------------+
| libibverbs       |                  | ib_uverbs.ko     |
|                  |                  |                  |
| ibv_create_qp()  |                  |                  |
|   |              |                  |                  |
|   | ioctl()      |                  |                  |
|   +------------- | --------------->(|                  |
|   |              | /dev/uverbs0     | ib_uverbs_       |
|   |              |  (fd)            |  create_qp()     |
|   |              |                  |       |          |
|   |              |                  |       v          |
|   |              |                  | mlx5_ib_create_qp|
|   |              |                  | (hardware setup) |
|   |              |                  |       |          |
|   |              |                  |       v          |
|   |<------------ | -----------------| return handle    |
|   |              |                  |                  |
|   | mmap()       |                  |                  |
|   +------------- | --------------->(| Map doorbell     |
|   |              |                  | register to      |
|   |              |                  | user space       |
|   |<------------ | -----------------| (mmap'd page)    |
|   |              |                  |                  |
| [Now user can write to doorbell directly!]
| [No more syscalls for data path!]     |
+------------------+                  +------------------+

After initial setup, data path is:
User: *doorbell_addr = qp_num;  // One store, no syscall
HCA:  [reads WR from SQ, starts DMA, sends packet]
```

### 16.4 RXE — Software RDMA

**RXE (Soft RoCE)** is a pure software implementation of RoCEv2 in the Linux
kernel. It allows any standard Ethernet NIC to act as an RDMA device (for
testing, development, or low-bandwidth use):

```
RXE ARCHITECTURE
================

+---------------------------+
|  User Space RDMA App      |
+---------------------------+
|  libibverbs               |
+---------------------------+
|  ib_uverbs                |
+---------------------------+
|  rxe.ko                   |
|  - Implements ib_device_ops|
|  - RoCEv2 packet building  |
|  - UDP encapsulation       |
+---------------------------+
|  Linux Network Stack      |
|  (UDP/IP, routing)        |
+---------------------------+
|  Standard Ethernet NIC    |
|  (e1000, virtio, etc.)    |
+---------------------------+

Setup:
  rxe_cfg add eth0  # Create rxe0 RDMA device on top of eth0
  # OR via iproute2:
  rdma link add rxe0 type rxe netdev eth0

Test:
  ibv_devinfo                    # Should now show rxe0
  rping -s &                     # Start server
  rping -c -a 192.168.1.1 -v     # Connect client
```

---

## 17. C Implementation — Complete Working Examples

### 17.1 Complete RDMA Send/Receive Example (C)

This is a full, working example of RDMA send/receive using RC QPs:

```c
// rdma_sendrecv.c
// Compile: gcc -o rdma_sendrecv rdma_sendrecv.c -libverbs -lrdmacm

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <errno.h>
#include <infiniband/verbs.h>
#include <rdma/rdma_cma.h>
#include <arpa/inet.h>

// ============================================================
// CONSTANTS AND CONFIGURATION
// ============================================================
#define RDMA_PORT        7471
#define RDMA_MSG_SIZE    4096
#define RDMA_MAX_RECV    64
#define RDMA_MAX_SEND    64
#define RDMA_CQ_DEPTH    128

// ============================================================
// DATA STRUCTURES
// ============================================================

// Connection parameters exchanged via CM private data
struct app_conn_params {
    uint64_t buf_addr;    // Address of RDMA target buffer
    uint32_t buf_rkey;    // Remote key for the RDMA buffer
    uint32_t buf_size;    // Buffer size
};

// Context for one RDMA connection
struct rdma_ctx {
    struct rdma_cm_id    *cm_id;      // CM connection ID
    struct ibv_context   *verbs;      // Device handle
    struct ibv_pd        *pd;         // Protection domain
    struct ibv_cq        *cq;         // Completion queue
    struct ibv_qp        *qp;         // Queue pair
    struct ibv_comp_channel *comp_chan;// For event notifications

    char                 *send_buf;   // Send buffer (pinned)
    char                 *recv_buf;   // Receive buffer (pinned)
    struct ibv_mr        *send_mr;    // MR for send buffer
    struct ibv_mr        *recv_mr;    // MR for recv buffer
    
    struct app_conn_params remote;    // Remote side parameters
};

// ============================================================
// HELPER: Check and print error
// ============================================================
#define CHECK(expr, msg) do {                               \
    if (!(expr)) {                                          \
        fprintf(stderr, "ERROR [%s:%d] %s: %s\n",          \
                __FILE__, __LINE__, (msg), strerror(errno));\
        return -1;                                          \
    }                                                       \
} while(0)

// ============================================================
// STEP 1: SETUP RDMA RESOURCES
// ============================================================

static int setup_resources(struct rdma_ctx *ctx)
{
    // Allocate Protection Domain
    ctx->pd = ibv_alloc_pd(ctx->verbs);
    CHECK(ctx->pd, "ibv_alloc_pd");

    // Create Completion Event Channel (for event-driven notification)
    ctx->comp_chan = ibv_create_comp_channel(ctx->verbs);
    CHECK(ctx->comp_chan, "ibv_create_comp_channel");

    // Create Completion Queue
    // Use completion vector 0 for interrupt affinity
    ctx->cq = ibv_create_cq(ctx->verbs, RDMA_CQ_DEPTH,
                             NULL,         // user_context (opaque)
                             ctx->comp_chan,
                             0);           // completion vector
    CHECK(ctx->cq, "ibv_create_cq");

    // Request notification for completions
    // 0 = notify on next completion (not just solicited)
    if (ibv_req_notify_cq(ctx->cq, 0)) {
        fprintf(stderr, "ibv_req_notify_cq failed\n");
        return -1;
    }

    // Allocate and register send buffer
    // posix_memalign for alignment (cache-line and page alignment helps DMA)
    if (posix_memalign((void**)&ctx->send_buf, 4096, RDMA_MSG_SIZE) != 0) {
        perror("posix_memalign send");
        return -1;
    }
    if (posix_memalign((void**)&ctx->recv_buf, 4096, RDMA_MSG_SIZE) != 0) {
        perror("posix_memalign recv");
        return -1;
    }

    // Register send buffer:
    // IBV_ACCESS_LOCAL_WRITE is needed for any recv buffer
    // We only send from this buffer, but LOCAL_WRITE is needed for
    // the HCA to do DMA read from it
    ctx->send_mr = ibv_reg_mr(ctx->pd, ctx->send_buf, RDMA_MSG_SIZE,
                               IBV_ACCESS_LOCAL_WRITE);
    CHECK(ctx->send_mr, "ibv_reg_mr send");

    // Register recv buffer
    ctx->recv_mr = ibv_reg_mr(ctx->pd, ctx->recv_buf, RDMA_MSG_SIZE,
                               IBV_ACCESS_LOCAL_WRITE);
    CHECK(ctx->recv_mr, "ibv_reg_mr recv");

    printf("[setup] PD=%p, CQ=%p, send_mr.lkey=0x%x, recv_mr.lkey=0x%x\n",
           ctx->pd, ctx->cq, ctx->send_mr->lkey, ctx->recv_mr->lkey);
    return 0;
}

// ============================================================
// STEP 2: CREATE AND CONFIGURE QUEUE PAIR
// ============================================================

static int create_qp(struct rdma_ctx *ctx)
{
    struct ibv_qp_init_attr attr = {
        .send_cq        = ctx->cq,       // Send completions go here
        .recv_cq        = ctx->cq,       // Recv completions go here (same CQ)
        .qp_type        = IBV_QPT_RC,    // Reliable Connected
        .cap = {
            .max_send_wr        = RDMA_MAX_SEND,
            .max_recv_wr        = RDMA_MAX_RECV,
            .max_send_sge       = 1,     // One SGE per WR is common
            .max_recv_sge       = 1,
            .max_inline_data    = 64,    // Inline up to 64 bytes (no DMA)
        },
        // sq_sig_all = 0: only signal WRs with IBV_SEND_SIGNALED
        // sq_sig_all = 1: signal ALL send WRs (more CQE overhead)
        .sq_sig_all     = 0,
    };

    // Use rdma_create_qp() when using CM (handles state machine internally)
    // This creates QP and automatically associates it with the cm_id
    if (rdma_create_qp(ctx->cm_id, ctx->pd, &attr)) {
        perror("rdma_create_qp");
        return -1;
    }
    ctx->qp = ctx->cm_id->qp;
    
    printf("[setup] QP created: qp_num=0x%x, type=RC\n", ctx->qp->qp_num);
    return 0;
}

// ============================================================
// STEP 3: POST RECEIVE WORK REQUESTS (must do before peer sends!)
// ============================================================

static int post_recv(struct rdma_ctx *ctx, int n)
{
    struct ibv_sge sge = {
        .addr   = (uint64_t)ctx->recv_buf,
        .length = RDMA_MSG_SIZE,
        .lkey   = ctx->recv_mr->lkey,
    };

    struct ibv_recv_wr wr = {
        .wr_id   = 1000,       // Our chosen ID (returned in CQE)
        .sg_list = &sge,
        .num_sge = 1,
        .next    = NULL,
    };

    struct ibv_recv_wr *bad_wr = NULL;
    
    for (int i = 0; i < n; i++) {
        wr.wr_id = 1000 + i;
        if (ibv_post_recv(ctx->qp, &wr, &bad_wr)) {
            fprintf(stderr, "ibv_post_recv failed at i=%d: %s\n",
                    i, strerror(errno));
            return -1;
        }
    }
    printf("[recv] Posted %d recv WRs\n", n);
    return 0;
}

// ============================================================
// STEP 4: POST SEND WORK REQUEST
// ============================================================

static int post_send(struct rdma_ctx *ctx, const char *msg, size_t len)
{
    // Copy message into registered send buffer
    memcpy(ctx->send_buf, msg, len < RDMA_MSG_SIZE ? len : RDMA_MSG_SIZE);

    struct ibv_sge sge = {
        .addr   = (uint64_t)ctx->send_buf,
        .length = (uint32_t)len,
        .lkey   = ctx->send_mr->lkey,
    };

    struct ibv_send_wr wr = {
        .wr_id      = 2000,
        .sg_list    = &sge,
        .num_sge    = 1,
        .opcode     = IBV_WR_SEND,   // Basic two-sided send
        .send_flags = IBV_SEND_SIGNALED, // Generate CQE for this WR
        .next       = NULL,
    };

    // For small messages, use inline to avoid DMA setup overhead:
    // wr.send_flags = IBV_SEND_SIGNALED | IBV_SEND_INLINE;
    // (Data copied into WR descriptor; no need for registered memory)

    struct ibv_send_wr *bad_wr = NULL;
    if (ibv_post_send(ctx->qp, &wr, &bad_wr)) {
        perror("ibv_post_send");
        return -1;
    }
    printf("[send] Posted SEND WR: len=%zu, lkey=0x%x\n",
           len, sge.lkey);
    return 0;
}

// ============================================================
// STEP 5: POLL FOR COMPLETIONS
// ============================================================

static int poll_completion(struct rdma_ctx *ctx)
{
    struct ibv_wc wc[16];
    int n;
    
    // Event-driven: wait for CQ event notification
    struct ibv_cq *ev_cq;
    void *ev_ctx;
    
    if (ibv_get_cq_event(ctx->comp_chan, &ev_cq, &ev_ctx)) {
        perror("ibv_get_cq_event");
        return -1;
    }
    
    // Acknowledge the event (batching is possible: ack N events at once)
    ibv_ack_cq_events(ev_cq, 1);
    
    // Re-arm for next notification BEFORE polling
    // (to avoid race: completion arrives between poll end and req_notify)
    if (ibv_req_notify_cq(ctx->cq, 0)) {
        perror("ibv_req_notify_cq");
        return -1;
    }
    
    // Poll all available completions
    while ((n = ibv_poll_cq(ctx->cq, 16, wc)) > 0) {
        for (int i = 0; i < n; i++) {
            if (wc[i].status != IBV_WC_SUCCESS) {
                fprintf(stderr, "CQE error: wr_id=%lu, status=%s, vendor_err=0x%x\n",
                        wc[i].wr_id,
                        ibv_wc_status_str(wc[i].status),
                        wc[i].vendor_err);
                return -1;
            }
            
            if (wc[i].opcode & IBV_WC_RECV) {
                // Receive completion
                printf("[completion] RECV: wr_id=%lu, byte_len=%u\n",
                       wc[i].wr_id, wc[i].byte_len);
                printf("[data] Received: '%.*s'\n",
                       wc[i].byte_len, ctx->recv_buf);
            } else {
                // Send completion
                printf("[completion] SEND: wr_id=%lu\n", wc[i].wr_id);
            }
        }
    }
    
    if (n < 0) {
        perror("ibv_poll_cq");
        return -1;
    }
    return 0;
}

// ============================================================
// SERVER SIDE
// ============================================================

int run_server(const char *port_str)
{
    struct rdma_ctx ctx = {0};
    struct rdma_cm_id *listen_id = NULL;
    struct rdma_cm_event *event = NULL;
    struct rdma_event_channel *ec = NULL;
    struct sockaddr_in sin = {0};
    
    // Create event channel for CM events
    ec = rdma_create_event_channel();
    CHECK(ec, "rdma_create_event_channel");

    // Create listening CM ID
    if (rdma_create_id(ec, &listen_id, NULL, RDMA_PS_TCP)) {
        perror("rdma_create_id");
        return -1;
    }

    // Bind to address
    sin.sin_family = AF_INET;
    sin.sin_port = htons(RDMA_PORT);
    sin.sin_addr.s_addr = INADDR_ANY;
    
    if (rdma_bind_addr(listen_id, (struct sockaddr*)&sin)) {
        perror("rdma_bind_addr");
        return -1;
    }

    // Listen for connections
    if (rdma_listen(listen_id, 5)) {
        perror("rdma_listen");
        return -1;
    }
    printf("[server] Listening on port %d...\n", RDMA_PORT);

    // Wait for connection request
    if (rdma_get_cm_event(ec, &event)) {
        perror("rdma_get_cm_event");
        return -1;
    }
    
    if (event->event != RDMA_CM_EVENT_CONNECT_REQUEST) {
        fprintf(stderr, "Unexpected event: %d\n", event->event);
        return -1;
    }
    
    // Accept: first save the new cm_id
    ctx.cm_id = event->id;
    ctx.verbs = ctx.cm_id->verbs;
    rdma_ack_cm_event(event);

    // Setup RDMA resources
    if (setup_resources(&ctx)) return -1;
    
    // POST RECEIVES BEFORE ACCEPTING! (critical ordering)
    if (post_recv(&ctx, RDMA_MAX_RECV)) return -1;
    
    if (create_qp(&ctx)) return -1;

    // Accept connection, send our buffer info as private data
    struct app_conn_params params = {
        .buf_addr = (uint64_t)ctx.recv_buf,
        .buf_rkey = ctx.recv_mr->rkey,
        .buf_size = RDMA_MSG_SIZE,
    };
    
    struct rdma_conn_param conn_param = {
        .private_data       = &params,
        .private_data_len   = sizeof(params),
        .responder_resources= 4,   // Accept up to 4 outstanding RDMA reads from client
        .initiator_depth    = 4,   // We can issue up to 4 RDMA reads to client
    };
    
    if (rdma_accept(ctx.cm_id, &conn_param)) {
        perror("rdma_accept");
        return -1;
    }

    // Wait for ESTABLISHED event
    if (rdma_get_cm_event(ec, &event)) {
        perror("rdma_get_cm_event");
        return -1;
    }
    if (event->event != RDMA_CM_EVENT_ESTABLISHED) {
        fprintf(stderr, "Expected ESTABLISHED, got %d\n", event->event);
        return -1;
    }
    rdma_ack_cm_event(event);
    printf("[server] Connection established!\n");

    // Poll for receive
    if (poll_completion(&ctx)) return -1;

    // Send a response
    if (post_send(&ctx, "Hello from server!", 19)) return -1;
    if (poll_completion(&ctx)) return -1;

    // Wait for disconnect
    rdma_get_cm_event(ec, &event);
    rdma_ack_cm_event(event);

    // Cleanup
    ibv_dereg_mr(ctx.send_mr);
    ibv_dereg_mr(ctx.recv_mr);
    free(ctx.send_buf);
    free(ctx.recv_buf);
    rdma_destroy_qp(ctx.cm_id);
    ibv_destroy_cq(ctx.cq);
    ibv_destroy_comp_channel(ctx.comp_chan);
    ibv_dealloc_pd(ctx.pd);
    rdma_destroy_id(ctx.cm_id);
    rdma_destroy_id(listen_id);
    rdma_destroy_event_channel(ec);
    
    return 0;
}

// ============================================================
// CLIENT SIDE
// ============================================================

int run_client(const char *server_addr)
{
    struct rdma_ctx ctx = {0};
    struct rdma_cm_event *event = NULL;
    struct rdma_event_channel *ec = NULL;
    struct sockaddr_in sin = {0};

    ec = rdma_create_event_channel();
    CHECK(ec, "rdma_create_event_channel");

    if (rdma_create_id(ec, &ctx.cm_id, NULL, RDMA_PS_TCP)) {
        perror("rdma_create_id");
        return -1;
    }

    // Resolve server address (like DNS for RDMA)
    sin.sin_family = AF_INET;
    sin.sin_port = htons(RDMA_PORT);
    inet_pton(AF_INET, server_addr, &sin.sin_addr);
    
    if (rdma_resolve_addr(ctx.cm_id, NULL, (struct sockaddr*)&sin, 2000)) {
        perror("rdma_resolve_addr");
        return -1;
    }
    
    // Wait for address resolution
    rdma_get_cm_event(ec, &event);
    if (event->event != RDMA_CM_EVENT_ADDR_RESOLVED) {
        fprintf(stderr, "Expected ADDR_RESOLVED\n");
        return -1;
    }
    rdma_ack_cm_event(event);

    // Resolve route (computes path through fabric)
    if (rdma_resolve_route(ctx.cm_id, 2000)) {
        perror("rdma_resolve_route");
        return -1;
    }
    
    rdma_get_cm_event(ec, &event);
    if (event->event != RDMA_CM_EVENT_ROUTE_RESOLVED) {
        fprintf(stderr, "Expected ROUTE_RESOLVED\n");
        return -1;
    }
    rdma_ack_cm_event(event);
    
    ctx.verbs = ctx.cm_id->verbs;
    if (setup_resources(&ctx)) return -1;
    
    // Post receives BEFORE connecting!
    if (post_recv(&ctx, RDMA_MAX_RECV)) return -1;
    
    if (create_qp(&ctx)) return -1;

    // Connect
    struct app_conn_params our_params = {
        .buf_addr = (uint64_t)ctx.recv_buf,
        .buf_rkey = ctx.recv_mr->rkey,
        .buf_size = RDMA_MSG_SIZE,
    };
    
    struct rdma_conn_param conn_param = {
        .private_data       = &our_params,
        .private_data_len   = sizeof(our_params),
        .responder_resources= 4,
        .initiator_depth    = 4,
        .retry_count        = 7,    // Retry 7 times on error
        .rnr_retry_count    = 7,    // 7 = infinite RNR retries
    };
    
    if (rdma_connect(ctx.cm_id, &conn_param)) {
        perror("rdma_connect");
        return -1;
    }

    // Wait for ESTABLISHED, extract server's private data
    rdma_get_cm_event(ec, &event);
    if (event->event != RDMA_CM_EVENT_ESTABLISHED) {
        fprintf(stderr, "Expected ESTABLISHED\n");
        return -1;
    }
    
    // Extract server's parameters from private data
    if (event->param.conn.private_data_len >= sizeof(struct app_conn_params)) {
        memcpy(&ctx.remote, event->param.conn.private_data,
               sizeof(struct app_conn_params));
        printf("[client] Server buffer: addr=0x%lx, rkey=0x%x, size=%u\n",
               ctx.remote.buf_addr, ctx.remote.buf_rkey, ctx.remote.buf_size);
    }
    rdma_ack_cm_event(event);
    printf("[client] Connected!\n");

    // Send a message
    if (post_send(&ctx, "Hello from client!", 19)) return -1;
    if (poll_completion(&ctx)) return -1;  // Wait for send completion
    if (poll_completion(&ctx)) return -1;  // Wait for response from server

    // Disconnect
    rdma_disconnect(ctx.cm_id);
    
    // Cleanup
    ibv_dereg_mr(ctx.send_mr);
    ibv_dereg_mr(ctx.recv_mr);
    free(ctx.send_buf);
    free(ctx.recv_buf);
    rdma_destroy_qp(ctx.cm_id);
    ibv_destroy_cq(ctx.cq);
    ibv_destroy_comp_channel(ctx.comp_chan);
    ibv_dealloc_pd(ctx.pd);
    rdma_destroy_id(ctx.cm_id);
    rdma_destroy_event_channel(ec);

    return 0;
}

// ============================================================
// MAIN
// ============================================================
int main(int argc, char *argv[])
{
    if (argc < 2) {
        printf("Usage: %s server\n", argv[0]);
        printf("       %s client <server_ip>\n", argv[0]);
        return 1;
    }
    
    if (strcmp(argv[1], "server") == 0) {
        return run_server(NULL);
    } else if (strcmp(argv[1], "client") == 0 && argc >= 3) {
        return run_client(argv[2]);
    } else {
        fprintf(stderr, "Invalid arguments\n");
        return 1;
    }
}
```

### 17.2 RDMA Write Example (One-Sided, C)

```c
// rdma_write.c — demonstrates one-sided RDMA WRITE
// The target (server) registers memory and shares rkey.
// The initiator (client) writes directly into target memory.
// Target's CPU is NEVER interrupted during the write!

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <infiniband/verbs.h>
#include <rdma/rdma_cma.h>

#define MSG_SIZE    (1 << 20)  // 1 MB
#define MAGIC_DONE  0xDEADBEEFull  // Sentinel value written at end of buffer

// After connection, server does:
//   1. Register 1MB buffer with REMOTE_WRITE permission
//   2. Send rkey + addr to client (via rdma_accept private data)
//   3. Poll the magic location for MAGIC_DONE (spin-poll; no interrupts)

// Client does:
//   1. Receive rkey + addr from server (via rdma_connect private data echo)
//   2. RDMA WRITE 1MB of data + MAGIC_DONE sentinel
//   3. Done! No send/recv needed.

static int do_rdma_write(struct ibv_qp *qp,
                          uint64_t local_addr, uint32_t lkey,
                          uint64_t remote_addr, uint32_t rkey,
                          uint32_t len)
{
    struct ibv_sge sge = {
        .addr   = local_addr,
        .length = len,
        .lkey   = lkey,
    };

    struct ibv_send_wr wr = {
        .wr_id          = 3000,
        .sg_list        = &sge,
        .num_sge        = 1,
        .opcode         = IBV_WR_RDMA_WRITE,   // ONE-SIDED WRITE
        .send_flags     = IBV_SEND_SIGNALED,
        .wr.rdma = {
            .remote_addr = remote_addr,         // Target buffer address
            .rkey        = rkey,                // Target buffer rkey
        },
    };

    struct ibv_send_wr *bad_wr;
    if (ibv_post_send(qp, &wr, &bad_wr)) {
        perror("ibv_post_send RDMA_WRITE");
        return -1;
    }
    
    // Poll for send completion (means data was sent; NOT that target has it yet!)
    // For true ordering guarantees, use FENCE or explicit Read back.
    struct ibv_wc wc;
    int n;
    do {
        n = ibv_poll_cq(qp->send_cq, 1, &wc);
    } while (n == 0);
    
    if (wc.status != IBV_WC_SUCCESS) {
        fprintf(stderr, "RDMA WRITE failed: %s\n",
                ibv_wc_status_str(wc.status));
        return -1;
    }
    
    printf("[rdma_write] Completed: %u bytes -> remote 0x%lx\n",
           len, remote_addr);
    return 0;
}

// Write sentinel to signal completion
static int write_sentinel(struct ibv_qp *qp,
                           uint64_t sentinel_buf, uint32_t lkey,
                           uint64_t remote_sentinel, uint32_t rkey)
{
    // Write with FENCE to ensure all prior writes complete first!
    *(uint64_t*)sentinel_buf = MAGIC_DONE;
    
    struct ibv_sge sge = {
        .addr   = sentinel_buf,
        .length = sizeof(uint64_t),
        .lkey   = lkey,
    };

    struct ibv_send_wr wr = {
        .wr_id          = 3001,
        .sg_list        = &sge,
        .num_sge        = 1,
        .opcode         = IBV_WR_RDMA_WRITE,
        .send_flags     = IBV_SEND_SIGNALED | IBV_SEND_FENCE, // FENCE!
        .wr.rdma = {
            .remote_addr = remote_sentinel,
            .rkey        = rkey,
        },
    };
    
    // IBV_SEND_FENCE ensures all prior WRs complete before this one.
    // The target can then safely read the sentinel after the fence WR completes.
    
    struct ibv_send_wr *bad_wr;
    ibv_post_send(qp, &wr, &bad_wr);
    
    struct ibv_wc wc;
    int n;
    do { n = ibv_poll_cq(qp->send_cq, 1, &wc); } while (n == 0);
    
    return (wc.status == IBV_WC_SUCCESS) ? 0 : -1;
}

// Target (server) polls for completion without any network involvement
static void target_poll_for_data(volatile uint64_t *sentinel)
{
    printf("[target] Waiting for data (spin-polling sentinel)...\n");
    while (*sentinel != MAGIC_DONE) {
        // Busy-wait; no syscalls, no interrupts
        // In real code: add pause/yield/backoff
        __asm__ volatile("pause" ::: "memory");
    }
    printf("[target] Data received! (sentinel = 0x%lx)\n", *sentinel);
}
```

### 17.3 Atomic FETCH_AND_ADD Example (C)

```c
// rdma_atomic.c — distributed counter using RDMA Atomics

static int rdma_fetch_and_add(struct ibv_qp *qp,
                               uint64_t local_result_addr, uint32_t lkey,
                               uint64_t remote_counter_addr, uint32_t rkey,
                               uint64_t add_value)
{
    struct ibv_sge sge = {
        .addr   = local_result_addr,    // Where to put original value
        .length = sizeof(uint64_t),
        .lkey   = lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id      = 5000,
        .sg_list    = &sge,
        .num_sge    = 1,
        .opcode     = IBV_WR_ATOMIC_FETCH_AND_ADD,
        .send_flags = IBV_SEND_SIGNALED,
        .wr.atomic  = {
            .remote_addr = remote_counter_addr,  // MUST be 8-byte aligned!
            .rkey        = rkey,
            .compare_add = add_value,            // Value to add
        },
    };
    
    struct ibv_send_wr *bad_wr;
    if (ibv_post_send(qp, &wr, &bad_wr)) {
        perror("FAA post_send");
        return -1;
    }
    
    struct ibv_wc wc;
    int n;
    do { n = ibv_poll_cq(qp->send_cq, 1, &wc); } while (n == 0);
    
    if (wc.status == IBV_WC_SUCCESS) {
        uint64_t original = *(uint64_t*)local_result_addr;
        printf("[atomic] FAA: remote_counter was %lu, now %lu\n",
               original, original + add_value);
        return 0;
    }
    
    fprintf(stderr, "FAA failed: %s\n", ibv_wc_status_str(wc.status));
    return -1;
}

// Distributed CAS-based spinlock
static int rdma_acquire_lock(struct ibv_qp *qp,
                              uint64_t result_buf, uint32_t lkey,
                              uint64_t lock_addr, uint32_t lock_rkey)
{
    struct ibv_sge sge = {
        .addr   = result_buf,
        .length = sizeof(uint64_t),
        .lkey   = lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id      = 6000,
        .sg_list    = &sge,
        .num_sge    = 1,
        .opcode     = IBV_WR_ATOMIC_CMP_AND_SWP,
        .send_flags = IBV_SEND_SIGNALED,
        .wr.atomic  = {
            .remote_addr = lock_addr,
            .rkey        = lock_rkey,
            .compare_add = 0,  // Expected: 0 (unlocked)
            .swap        = 1,  // Set to: 1 (locked)
        },
    };

    struct ibv_send_wr *bad_wr;
    struct ibv_wc wc;
    
    // Spin until we acquire the lock
    while (1) {
        ibv_post_send(qp, &wr, &bad_wr);
        int n;
        do { n = ibv_poll_cq(qp->send_cq, 1, &wc); } while (n == 0);
        
        uint64_t old_val = *(uint64_t*)result_buf;
        if (old_val == 0) {
            printf("[atomic] Lock acquired!\n");
            return 0;  // CAS succeeded: we got the lock
        }
        // Lock was taken; back off and retry
        usleep(1);  // Or use exponential backoff
    }
}

static int rdma_release_lock(struct ibv_qp *qp,
                              uint64_t zero_buf, uint32_t lkey,
                              uint64_t lock_addr, uint32_t lock_rkey)
{
    // Simply write 0 to the lock to release it
    *(uint64_t*)zero_buf = 0;
    
    struct ibv_sge sge = {
        .addr   = zero_buf,
        .length = sizeof(uint64_t),
        .lkey   = lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id      = 7000,
        .sg_list    = &sge,
        .num_sge    = 1,
        .opcode     = IBV_WR_RDMA_WRITE,
        .send_flags = IBV_SEND_SIGNALED | IBV_SEND_FENCE,
        .wr.rdma    = {
            .remote_addr = lock_addr,
            .rkey        = lock_rkey,
        },
    };
    
    struct ibv_send_wr *bad_wr;
    struct ibv_wc wc;
    ibv_post_send(qp, &wr, &bad_wr);
    int n;
    do { n = ibv_poll_cq(qp->send_cq, 1, &wc); } while (n == 0);
    
    printf("[atomic] Lock released\n");
    return (wc.status == IBV_WC_SUCCESS) ? 0 : -1;
}
```

---

## 18. Rust Implementation — Safe RDMA Abstractions

### 18.1 Why Rust for RDMA?

RDMA involves raw pointers, pinned memory, hardware state machines, and careful
resource lifecycle management — all areas where Rust's ownership and type systems
provide enormous safety guarantees.

**Key challenges Rust solves:**
- Memory registration lifetime (MR must outlive all WRs that use it)
- QP state machine correctness (can be encoded in type states)
- Completion queue ownership (exactly one consumer)
- Unsafe FFI to libibverbs (contained in well-defined boundary)

### 18.2 Rust FFI Bindings

```rust
// Cargo.toml
// [dependencies]
// libc = "0.2"
// rdma-sys = "0.3"  # bindgen-generated bindings to libibverbs

// Or generate your own:
// [build-dependencies]
// bindgen = "0.69"
```

### 18.3 Safe Rust RDMA Context

```rust
// rdma_ctx.rs — Safe wrapper around libibverbs

use std::ptr::{self, NonNull};
use std::marker::PhantomData;
use std::sync::Arc;
use libc::{c_int, c_void};

// ============================================================
// FFI DECLARATIONS (normally generated by bindgen)
// Shown manually for clarity
// ============================================================

#[repr(C)]
pub struct IbvContext { _opaque: [u8; 0] }

#[repr(C)]
pub struct IbvPd { 
    pub context: *mut IbvContext,
    pub handle: u32,
    _opaque: [u8; 0],
}

#[repr(C)]
pub struct IbvMr {
    pub context: *mut IbvContext,
    pub pd: *mut IbvPd,
    pub addr: *mut c_void,
    pub length: usize,
    pub handle: u32,
    pub lkey: u32,
    pub rkey: u32,
}

#[repr(C)]
pub struct IbvCq { _opaque: [u8; 0] }

#[repr(C)]
pub struct IbvQp {
    pub context: *mut IbvContext,
    pub qp_context: *mut c_void,
    pub pd: *mut IbvPd,
    pub send_cq: *mut IbvCq,
    pub recv_cq: *mut IbvCq,
    pub qp_num: u32,
    pub state: u32,
    pub qp_type: u32,
    _opaque: [u8; 0],
}

#[repr(C)]
pub struct IbvWc {
    pub wr_id: u64,
    pub status: u32,
    pub opcode: u32,
    pub vendor_err: u32,
    pub byte_len: u32,
    pub imm_data: u32,
    pub qp_num: u32,
    pub src_qp: u32,
    pub wc_flags: c_int,
    pub pkey_index: u16,
    pub slid: u16,
    pub sl: u8,
    pub dlid_path_bits: u8,
}

extern "C" {
    fn ibv_get_device_list(num_devices: *mut c_int) -> *mut *mut IbvDevice;
    fn ibv_free_device_list(list: *mut *mut IbvDevice);
    fn ibv_get_device_name(device: *mut IbvDevice) -> *const libc::c_char;
    fn ibv_open_device(device: *mut IbvDevice) -> *mut IbvContext;
    fn ibv_close_device(context: *mut IbvContext) -> c_int;
    fn ibv_alloc_pd(context: *mut IbvContext) -> *mut IbvPd;
    fn ibv_dealloc_pd(pd: *mut IbvPd) -> c_int;
    fn ibv_reg_mr(pd: *mut IbvPd, addr: *mut c_void, length: usize,
                  access: c_int) -> *mut IbvMr;
    fn ibv_dereg_mr(mr: *mut IbvMr) -> c_int;
    fn ibv_create_cq(context: *mut IbvContext, cqe: c_int,
                     cq_context: *mut c_void,
                     channel: *mut c_void,
                     comp_vector: c_int) -> *mut IbvCq;
    fn ibv_destroy_cq(cq: *mut IbvCq) -> c_int;
    fn ibv_poll_cq(cq: *mut IbvCq, num_entries: c_int,
                   wc: *mut IbvWc) -> c_int;
}

#[repr(C)]
pub struct IbvDevice { _opaque: [u8; 0] }

// ============================================================
// ACCESS FLAGS
// ============================================================
pub mod access {
    pub const LOCAL_WRITE:   i32 = 1;
    pub const REMOTE_WRITE:  i32 = 2;
    pub const REMOTE_READ:   i32 = 4;
    pub const REMOTE_ATOMIC: i32 = 8;
}

// ============================================================
// RAII WRAPPER: Protection Domain
// ============================================================

/// Safe wrapper around IbvPd.
/// When this is dropped, ibv_dealloc_pd() is called automatically.
pub struct ProtectionDomain {
    inner: NonNull<IbvPd>,
    // PhantomData tells Rust: "this type acts as if it owns an IbvPd"
    _marker: PhantomData<IbvPd>,
}

impl ProtectionDomain {
    /// Allocate a new Protection Domain on the given device context.
    /// 
    /// # Safety
    /// `ctx` must be a valid, open IbvContext pointer.
    pub unsafe fn alloc(ctx: *mut IbvContext) -> Result<Self, &'static str> {
        let pd = ibv_alloc_pd(ctx);
        NonNull::new(pd)
            .map(|inner| Self { inner, _marker: PhantomData })
            .ok_or("ibv_alloc_pd failed")
    }

    pub fn as_ptr(&self) -> *mut IbvPd {
        self.inner.as_ptr()
    }
}

impl Drop for ProtectionDomain {
    fn drop(&mut self) {
        unsafe {
            let ret = ibv_dealloc_pd(self.inner.as_ptr());
            if ret != 0 {
                eprintln!("ibv_dealloc_pd failed: {}", ret);
            }
        }
    }
}

// SAFETY: ProtectionDomain contains only a raw pointer to kernel-managed
// memory. Multiple threads can read from it, but we ensure all QPs
// in the same PD share the underlying driver state safely.
unsafe impl Send for ProtectionDomain {}
unsafe impl Sync for ProtectionDomain {}

// ============================================================
// RAII WRAPPER: Memory Region
// ============================================================

/// Safe wrapper around IbvMr.
///
/// LIFETIME INVARIANT: The memory region `T` MUST outlive this MR.
/// Rust's lifetime system enforces this at compile time.
pub struct MemoryRegion<'mem> {
    inner: NonNull<IbvMr>,
    // Tie this MR to the lifetime of the buffer it wraps.
    // This prevents the buffer from being freed while this MR exists.
    _lifetime: PhantomData<&'mem mut ()>,
}

impl<'mem> MemoryRegion<'mem> {
    /// Register a buffer with a protection domain.
    ///
    /// The returned MR borrows `buf` for lifetime `'mem`.
    /// You cannot free `buf` while this MR is alive.
    pub fn register(
        pd: &ProtectionDomain,
        buf: &'mem mut [u8],
        access: i32,
    ) -> Result<Self, &'static str> {
        let mr = unsafe {
            ibv_reg_mr(
                pd.as_ptr(),
                buf.as_mut_ptr() as *mut c_void,
                buf.len(),
                access,
            )
        };
        NonNull::new(mr)
            .map(|inner| Self { inner, _lifetime: PhantomData })
            .ok_or("ibv_reg_mr failed")
    }

    pub fn lkey(&self) -> u32 {
        unsafe { (*self.inner.as_ptr()).lkey }
    }

    pub fn rkey(&self) -> u32 {
        unsafe { (*self.inner.as_ptr()).rkey }
    }

    pub fn addr(&self) -> u64 {
        unsafe { (*self.inner.as_ptr()).addr as u64 }
    }

    pub fn length(&self) -> usize {
        unsafe { (*self.inner.as_ptr()).length }
    }
}

impl<'mem> Drop for MemoryRegion<'mem> {
    fn drop(&mut self) {
        unsafe {
            let ret = ibv_dereg_mr(self.inner.as_ptr());
            if ret != 0 {
                eprintln!("ibv_dereg_mr failed: {}", ret);
            }
        }
    }
}

unsafe impl<'mem> Send for MemoryRegion<'mem> {}

// ============================================================
// RAII WRAPPER: Completion Queue
// ============================================================

pub struct CompletionQueue {
    inner: NonNull<IbvCq>,
    _marker: PhantomData<IbvCq>,
}

impl CompletionQueue {
    pub unsafe fn create(
        ctx: *mut IbvContext,
        cqe: i32,
    ) -> Result<Self, &'static str> {
        let cq = ibv_create_cq(ctx, cqe, ptr::null_mut(), ptr::null_mut(), 0);
        NonNull::new(cq)
            .map(|inner| Self { inner, _marker: PhantomData })
            .ok_or("ibv_create_cq failed")
    }

    pub fn as_ptr(&self) -> *mut IbvCq {
        self.inner.as_ptr()
    }

    /// Poll for completions. Returns vector of completed WC entries.
    pub fn poll(&self, max: i32) -> Vec<IbvWc> {
        let mut wcs = vec![
            IbvWc {
                wr_id: 0, status: 0, opcode: 0, vendor_err: 0,
                byte_len: 0, imm_data: 0, qp_num: 0, src_qp: 0,
                wc_flags: 0, pkey_index: 0, slid: 0, sl: 0,
                dlid_path_bits: 0,
            };
            max as usize
        ];
        let n = unsafe {
            ibv_poll_cq(self.inner.as_ptr(), max, wcs.as_mut_ptr())
        };
        if n > 0 {
            wcs.truncate(n as usize);
            wcs
        } else {
            Vec::new()
        }
    }

    /// Spin-poll until at least one completion arrives.
    pub fn poll_blocking(&self) -> Vec<IbvWc> {
        loop {
            let wcs = self.poll(16);
            if !wcs.is_empty() {
                return wcs;
            }
            std::hint::spin_loop();
        }
    }
}

impl Drop for CompletionQueue {
    fn drop(&mut self) {
        unsafe {
            ibv_destroy_cq(self.inner.as_ptr());
        }
    }
}

unsafe impl Send for CompletionQueue {}
unsafe impl Sync for CompletionQueue {}

// ============================================================
// TYPE-STATE QP: Encode QP state in the type system
// ============================================================

// QP states as zero-sized marker types
pub struct Reset;
pub struct Init;
pub struct Rtr;
pub struct Rts;
pub struct Error;

/// A Queue Pair parameterized by its current state.
/// This makes invalid state transitions a COMPILE-TIME error!
pub struct QueuePair<State> {
    inner: NonNull<IbvQp>,
    state: PhantomData<State>,
}

impl QueuePair<Reset> {
    /// Transition from RESET to INIT.
    /// Only allowed when QP is in Reset state (enforced by type system).
    pub fn to_init(self, port_num: u8, pkey_index: u16, access_flags: i32)
        -> Result<QueuePair<Init>, i32>
    {
        // Call ibv_modify_qp with RESET->INIT attributes
        // (implementation calls actual FFI)
        todo!("ibv_modify_qp RESET->INIT");
    }
}

impl QueuePair<Init> {
    pub fn to_rtr(self, dest_qp_num: u32, dest_lid: u16, path_mtu: u32)
        -> Result<QueuePair<Rtr>, i32>
    {
        todo!("ibv_modify_qp INIT->RTR");
    }
    
    // Can post receives in INIT state
    pub fn post_recv(&self, wr: &RecvWorkRequest) -> Result<(), i32> {
        todo!("post_recv");
    }
}

impl QueuePair<Rtr> {
    pub fn to_rts(self, sq_psn: u32, timeout: u8, retry_cnt: u8)
        -> Result<QueuePair<Rts>, i32>
    {
        todo!("ibv_modify_qp RTR->RTS");
    }
}

impl QueuePair<Rts> {
    /// Post a send work request — only valid in RTS state
    pub fn post_send(&self, wr: &SendWorkRequest) -> Result<(), i32> {
        todo!("ibv_post_send");
    }
    
    pub fn post_recv(&self, wr: &RecvWorkRequest) -> Result<(), i32> {
        todo!("ibv_post_recv");
    }
}

// Note: you CANNOT call post_send on QueuePair<Reset> or QueuePair<Init>
// because the method simply doesn't exist for those types!
// The COMPILER catches this, not a runtime error.

// Placeholder types for the example
pub struct SendWorkRequest;
pub struct RecvWorkRequest;

// ============================================================
// RUST RDMA PING-PONG EXAMPLE
// ============================================================

/// Demonstrates a minimal send/recv loop using the safe wrappers above.
fn rdma_ping_pong_example() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Open device (normally via rdma-sys or rdmacm crate)
    //    For demonstration, assume we have a context pointer
    let ctx_ptr: *mut IbvContext = ptr::null_mut(); // Would be ibv_open_device()
    
    // 2. Create Protection Domain
    let pd = unsafe { ProtectionDomain::alloc(ctx_ptr)? };
    
    // 3. Allocate aligned buffers
    // Using vec for alignment; real code uses posix_memalign or mmap
    let mut send_buf = vec![0u8; 4096];
    let mut recv_buf = vec![0u8; 4096];
    
    // 4. Register memory regions
    // RUST MAGIC: recv_mr borrows recv_buf for its lifetime.
    // You CANNOT drop recv_buf while recv_mr exists!
    let recv_mr = MemoryRegion::register(
        &pd,
        &mut recv_buf,
        access::LOCAL_WRITE,
    )?;
    
    let send_mr = MemoryRegion::register(
        &pd,
        &mut send_buf,
        access::LOCAL_WRITE,
    )?;
    
    println!("Send MR: lkey=0x{:x}, addr=0x{:x}", send_mr.lkey(), send_mr.addr());
    println!("Recv MR: lkey=0x{:x}, rkey=0x{:x}", recv_mr.lkey(), recv_mr.rkey());
    
    // 5. Create Completion Queue
    let cq = unsafe { CompletionQueue::create(ctx_ptr, 128)? };
    
    // 6. Create QP (starts in Reset state — enforced by type)
    // QueuePair<Reset> can ONLY call to_init()
    // let qp_reset: QueuePair<Reset> = ...;
    // let qp_init = qp_reset.to_init(1, 0, access::LOCAL_WRITE)?;
    // let qp_rtr = qp_init.to_rtr(remote_qpn, remote_lid, IBV_MTU_4096)?;
    // let qp_rts = qp_rtr.to_rts(psn, 14, 7)?;
    // NOW you can call qp_rts.post_send(...)
    
    // Rust ensures you can NEVER call post_send on a non-RTS QP!
    
    Ok(())
    // When pd, recv_mr, send_mr, cq drop here:
    // - ibv_dereg_mr(recv_mr) called
    // - ibv_dereg_mr(send_mr) called
    // - ibv_destroy_cq(cq) called
    // - ibv_dealloc_pd(pd) called
    // Correct order enforced by drop order (reverse declaration order)!
}
```

### 18.4 Rust Async RDMA with Tokio

```rust
// rdma_async.rs — Async RDMA completion handling with Tokio

use tokio::io::unix::AsyncFd;
use std::os::unix::io::RawFd;

/// Wraps a completion channel FD for async polling
/// The completion channel FD becomes readable when a CQE is available.
pub struct AsyncCompletionChannel {
    fd: AsyncFd<RawFd>,
    cq: CompletionQueue,
}

impl AsyncCompletionChannel {
    pub fn new(channel_fd: RawFd, cq: CompletionQueue) -> std::io::Result<Self> {
        Ok(Self {
            fd: AsyncFd::new(channel_fd)?,
            cq,
        })
    }

    /// Wait asynchronously for completions — doesn't block the Tokio thread!
    pub async fn wait_for_completion(&self) -> std::io::Result<Vec<IbvWc>> {
        loop {
            // Wait until the FD is readable (a CQE arrived)
            let mut guard = self.fd.readable().await?;
            
            // Try to get completions
            let wcs = self.cq.poll(16);
            if !wcs.is_empty() {
                guard.retain_ready(); // Keep ready for next poll
                return Ok(wcs);
            }
            
            // No completions yet; clear the ready state and wait again
            guard.clear_ready();
        }
    }
}

// This allows writing RDMA code in async style:
// 
// async fn rdma_send_recv(ctx: &AsyncCompletionChannel) {
//     // Post sends/recvs
//     // ...
//     
//     // Await completions without blocking the thread!
//     let completions = ctx.wait_for_completion().await.unwrap();
//     for wc in completions {
//         println!("Completed: wr_id={}", wc.wr_id);
//     }
// }
//
// Multiple such tasks can run concurrently on the same Tokio runtime!
// This is impossible with blocking polling without dedicating threads.
```

---

## 19. Performance Tuning and Optimization

### 19.1 The RDMA Performance Hierarchy

```
PERFORMANCE KNOBS (highest impact first)
=========================================

1. POLLING MODE vs EVENT MODE
   +-----------+-------------------+-------------------+
   | Mode      | Latency           | CPU Usage         |
   +-----------+-------------------+-------------------+
   | Spin Poll | ~1 µs (minimum)   | 100% one core     |
   | Adaptive  | ~2-5 µs           | 20-60% one core   |
   | Event     | ~10-50 µs         | ~1% (sleeping)    |
   +-----------+-------------------+-------------------+
   Choose based on your latency vs CPU tradeoff.

2. INLINE DATA (small messages)
   Without inline: post_send -> DMA read -> NIC -> send
   With inline:    post_send -> data copied into WQE -> NIC -> send
   Benefit: Eliminates DMA for small (<64-256 bytes) messages
   Cost: Increases WQE size (reduces SQ depth)

3. SELECTIVE SIGNALING
   Signal every N sends, not every send.
   Reduces CQE overhead dramatically.
   Typical: signal every 16-64 sends.

4. BATCH POSTING
   Post multiple WRs in one call using the linked-list WR chain.
   One ibv_post_send() call with next-pointer chain is faster
   than N separate ibv_post_send() calls.

5. MEMORY REGISTRATION CACHING
   Never register/deregister on the data path.
   Use pre-registered large MR pools.

6. HUGE PAGES
   Use 2MB huge pages for RDMA buffers:
   - Fewer TLB entries needed
   - Fewer MTT entries in HCA
   - Better DMA performance
   mmap(NULL, size, PROT_RW, MAP_ANONYMOUS|MAP_HUGETLB, -1, 0)

7. CPU AFFINITY
   Pin RDMA threads to CPUs local to the NUMA node of the HCA.
   mismatch = 2x latency penalty from cross-NUMA memory access.
   
   Check HCA NUMA node:
   cat /sys/class/infiniband/mlx5_0/device/numa_node
   
   Pin thread to that NUMA node:
   numactl --cpunodebind=1 --membind=1 ./rdma_app

8. INTERRUPT COALESCING
   HCA interrupt moderation (mlx5):
   ethtool -C eth0 rx-usecs 50  # Coalesce interrupts to 50µs
   (trades latency for reduced interrupt overhead)
```

### 19.2 Tuning QP Parameters

```
QP PARAMETER TUNING GUIDE
==========================

Parameter              | Impact              | Recommendation
-----------------------|---------------------|-------------------
max_send_wr            | Memory use          | 256-4096 for throughput
max_recv_wr            | Memory use, RNR     | Keep 2x flight size
max_send_sge           | Flexibility         | 1-4 for most cases
max_recv_sge           | Flexibility         | 1 (usually)
max_inline_data        | Small msg latency   | 64-256 bytes
max_rd_atomic          | RDMA Read concurr.  | 16 (match hardware limit)
timeout (RC)           | Error detection     | 14 (~67 ms)
retry_cnt (RC)         | Reliability         | 7 (max)
rnr_retry (RC)         | RNR tolerance       | 7 (infinite)
min_rnr_timer          | Retry wait          | 1 (fast retry)
sq_psn                 | Packet sequence     | Random (security)

TIMEOUT FORMULA:
  timeout_us = 4.096 * 2^timeout
  timeout=14 -> 4.096 * 16384 = ~67 ms
  timeout=18 -> 4.096 * 262144 = ~1 sec
```

### 19.3 Throughput Optimization Pipeline

```
MAXIMUM THROUGHPUT PIPELINE
============================

Goal: Fill the wire at 100 Gbps = 12.5 GB/s

Step 1: Calculate required concurrency
  Bandwidth-Delay Product = BDP = Rate * RTT
  At 100 Gbps, RTT = 2 µs:
  BDP = 12.5 GB/s * 2 µs = 25 KB = ~6 x 4KB messages in flight
  
  But for maximum throughput, pipeline more:
  Target: 64-256 outstanding WRs at any time

Step 2: Use large messages
  Small messages: more header overhead per byte
  Large messages (64KB-4MB): better efficiency
  
  Rule of thumb:
  > 16KB per message -> approaches hardware-limited throughput
  < 1KB per message -> consider batching

Step 3: Multiple QPs
  One QP may not saturate the link if:
  - CPU processing is the bottleneck
  - HCA has per-QP limits
  
  Use N QPs in parallel:
  for (int i = 0; i < num_qps; i++)
      post_sends(qps[i], batch_size);

Step 4: Selective signaling
  Signal every 64 sends: reduces CQE overhead by 64x

Step 5: WR chaining
  Link 16 WRs with next pointer: one ibv_post_send() call
  
  IDEAL SEND LOOP:
  while (outstanding < max_outstanding) {
      // Build chain of 16 WRs
      for (int i = 0; i < 16; i++) {
          wrs[i].next = (i < 15) ? &wrs[i+1] : NULL;
          // Only signal the last one
          wrs[i].send_flags = (i == 15) ? IBV_SEND_SIGNALED : 0;
      }
      ibv_post_send(qp, &wrs[0], &bad_wr);  // ONE syscall-free call
      outstanding += 16;
      
      // Drain completions to prevent SQ overflow
      int n = ibv_poll_cq(cq, 16, wcs);
      outstanding -= n;
  }
```

### 19.4 Latency Optimization

```
MINIMUM LATENCY CHECKLIST
==========================

Hardware:
  [ ] Use ConnectX-6 or newer (lower base latency)
  [ ] Direct cable connection or single switch hop
  [ ] 4x HDR (200 Gbps) for lowest latency
  [ ] Set link to maximum speed (no auto-downgrade)

OS:
  [ ] Disable CPU frequency scaling: 
      echo performance > /sys/devices/.../cpufreq/scaling_governor
  [ ] Disable C-states (CPU power states):
      cpupower idle-set -D 0  (disable all C-states)
  [ ] Disable NMI watchdog:
      echo 0 > /proc/sys/kernel/nmi_watchdog
  [ ] Use RHEL/CentOS with realtime kernel (-rt) for deterministic latency
  [ ] Set IRQ affinity for HCA interrupts to local NUMA node

Application:
  [ ] Spin-poll CQ (no event channel)
  [ ] Use IBV_SEND_INLINE for messages < 64 bytes
  [ ] Use RDMA Write (one-sided) instead of Send/Recv when possible
  [ ] Avoid ibv_reg_mr on data path
  [ ] Use hugepages for buffers
  [ ] Lock pages: mlockall(MCL_CURRENT | MCL_FUTURE)
  [ ] Set realtime priority: sched_setscheduler(pid, SCHED_FIFO, &param)
  [ ] Pin thread to HCA-local CPU: sched_setaffinity()
```

---

## 20. Debugging, Monitoring, and Diagnostics

### 20.1 Essential Commands

```bash
# === DEVICE INFORMATION ===

# List all RDMA devices
ibv_devinfo

# Detailed info for specific device
ibv_devinfo -d mlx5_0 -v

# Device status (like 'ip link' for RDMA)
ibstat mlx5_0

# Show all IB links
rdma link

# Show all IB devices
rdma dev

# === FABRIC TOPOLOGY ===

# Show subnet topology (requires opensm running)
ibnetdiscover

# Show all hosts in fabric
ibhosts

# Show all switches in fabric
ibswitches

# Trace path between two nodes
ibtracert <lid1> <lid2>

# Ping via InfiniBand (like icmp ping but for IB)
ibping -S          # Start server
ibping -c 1000 -L <dest_lid>  # Ping

# === PERFORMANCE COUNTERS ===

# Show port performance counters
perfquery          # All ports
perfquery -x <lid> <port>  # Specific port

# Continuous counter monitoring
watch -n 1 perfquery

# Clear counters
perfquery -R

# === BANDWIDTH AND LATENCY TESTING ===

# InfiniBand bandwidth test (built into OFED)
ib_send_bw -d mlx5_0         # Server
ib_send_bw -d mlx5_0 <srv_ip> # Client

ib_write_bw -d mlx5_0        # RDMA Write bandwidth
ib_read_bw -d mlx5_0         # RDMA Read bandwidth
ib_atomic_bw -d mlx5_0       # Atomic operation bandwidth

# Latency tests
ib_send_lat -d mlx5_0
ib_write_lat -d mlx5_0
ib_read_lat -d mlx5_0

# === RDMA CM TEST ===
rping -s -a 0.0.0.0 -v       # Server
rping -c -a <server_ip> -v    # Client

# === MELLANOX-SPECIFIC ===
mst status                    # MST (MellanoX Software Tools) status
mst start
mlxconfig -d /dev/mst/mt4119_pciconf0 q  # Query device config
mlxstat /dev/mst/mt4119_pciconf0        # Hardware stats
```

### 20.2 Performance Counter Analysis

```
PERFORMANCE COUNTER MEANING
============================

Counter                  | Meaning                      | Alert if?
-------------------------|------------------------------|-------------
PortXmitData             | Bytes transmitted (4B units) | Monitor trend
PortRcvData              | Bytes received               | Monitor trend
PortXmitPkts             | Packets transmitted          | 
PortRcvPkts              | Packets received             |
PortXmitDiscards         | Sent packets dropped         | > 0 = problem!
PortRcvErrors            | Receive errors               | > 0 = bad link
PortRcvRemPhysErrors     | Remote physical errors       | > 0 = bad cable
PortXmitConstraintErrors | Partition violations         | > 0 = PKey issue
VL15Dropped              | Mgmt packets dropped         | > 0 = SM issue
PortRcvSwitchRelayErrors | Switch relay errors          | > 0 = congestion

SYMBOLS (per-symbol error rate):
SymbolErrorCounter       | Bit errors on the link       | Increasing = bad link
LinkRecovers             | Auto-negotiation recoveries  | > 0 = unstable
LinkDowned               | Times link went down         | > 0 = failures
```

### 20.3 Debugging Connection Issues

```
CONNECTION DEBUGGING FLOWCHART
==============================

Problem: RDMA connection fails / high latency / errors

1. CHECK PHYSICAL LAYER
   ibstat mlx5_0
   Expected: State: Active, Physical state: LinkUp
   If DOWN: Check cable, check switch port, check SFP
   
2. CHECK LID ASSIGNMENT (Subnet Manager active?)
   cat /sys/class/infiniband/mlx5_0/ports/1/lid
   Expected: non-zero value like "0x3"
   If 0: opensm not running, or SM not discovering this port
   Start SM: systemctl start opensm

3. CHECK CONNECTIVITY
   ibping -S &               # Start server on node A
   ibping -c 10 -L <A_lid>  # From node B, ping node A
   If fails: routing issue, check ibnetdiscover

4. CHECK FOR ERRORS
   perfquery                 # Zero errors = healthy
   If PortRcvErrors > 0: bad cable or SFP

5. APPLICATION DEBUGGING
   # Enable verbose RDMA CM debugging
   export RDMA_DEBUG=1
   
   # libibverbs debug
   export IBV_SHOW_WARNINGS=1
   
   # Mellanox HCA logs
   dmesg | grep mlx5
   
   # RDMA netlink debug
   rdma stat

6. COMMON ERRORS AND CAUSES:
   IBV_WC_RETRY_EXC_ERR   -> peer not responding; check QP state, link
   IBV_WC_RNR_RETRY_EXC_ERR -> peer not posting recvs fast enough
   IBV_WC_LOC_PROT_ERR    -> bad lkey; check MR registration
   IBV_WC_REM_ACCESS_ERR  -> bad rkey; check remote MR permissions
   IBV_WC_WR_FLUSH_ERR    -> QP in error state; must destroy and recreate
```

### 20.4 Linux Kernel RDMA Debug Interface

```bash
# Enable RDMA debug in kernel
echo 1 > /sys/class/infiniband/mlx5_0/ports/1/hw_counters/...

# rdmatool (iproute2 rdma command)
rdma stat                    # Statistics
rdma res                     # Resources (QPs, MRs, etc.)
rdma res show qp             # Show all QPs

# Example rdma res output:
# mlx5_0/1: pd 3 mr 45 cq 89 qp 12 srq 0 xrcd 0 ah 0

# Show a specific QP's details:
rdma res show qp lqpn <qp_number>

# Monitor events
rdma monitor               # Watch for link/device events
```

---

## 21. Advanced Topics: SRD, DC, XRC

### 21.1 XRC — Extended Reliable Connected

**Problem:** In an N-node cluster with RC QPs, each node needs N-1 QPs
(one per peer). For N=1000 nodes, each server needs 999 QPs. QPs are expensive
(consume HCA memory, software resources).

**XRC solution:** N nodes with XRC need only O(√N) QPs per node.

```
XRC ARCHITECTURE
================

Traditional RC (N=4 servers, 2 processes each):
  Each process pair needs one QP:
  8 processes * 7 peers = 56 QPs total

XRC (N=4 servers, 2 processes each):
  One XRCD (Extended RC Domain) per server:
  8 processes * 4 servers = 32 XRC SRQs
  Only 4 initiator QPs per process (one per remote server)
  
  +----------+              +----------+
  | Server1  |              | Server2  |
  |  Proc_A -|--QP_to_S2-->-|  XRCD   |
  |  Proc_B -|--QP_to_S2-->-|  (SRQ_A)|  Data goes to Proc_A's SRQ
  +----------+              |  (SRQ_B)|  Data goes to Proc_B's SRQ
                            +----------+
                            
  Same QP number (QP_to_S2) used by both Proc_A and Proc_B
  to target different SRQs in Server2's XRCD!
  
  Result: 2 QPs instead of 4 for the Proc_A, Proc_B -> Server2 case.
```

### 21.2 DC — Dynamically Connected Transport

**DC** (Mellanox proprietary, now part of ConnectX) creates connections
dynamically, combining RC reliability with UD scalability:

```
DC TRANSPORT
============

Problem with RC: QP per peer = O(N) QPs
Problem with UD: No reliability, no RDMA Read/Write

DC solution:
  DCT (DC Target) -- like a server QP, one per server process
  DCI (DC Initiator) -- one per connection thread

  DCI connects dynamically to any DCT on demand:
  - No per-peer QP allocation
  - Reliability guaranteed
  - Supports RDMA Write (not Read in basic form)
  
  +----------+               +----------+
  | Server1  |               | Server2  |
  |   DCI_1  |---connect---->|   DCT_2  |
  |          |<--complete----|          |
  |   DCI_2  |---connect---->|   DCT_3  |
  +----------+               +----------+

  DCI transitions are invisible to application.
  Latency: slightly higher than RC (connection setup overhead)
```

### 21.3 SRD — Scalable Reliable Datagram (AWS EFA)

**SRD** is the RDMA transport used by AWS EFA (Elastic Fabric Adapter):

```
SRD CHARACTERISTICS
===================

- Reliable Datagram (like RD but actually implemented!)
- One QP can communicate with MANY peers (like UD)
- Supports RDMA Write and RDMA Read
- Out-of-order delivery (but in-order to application)
- Multipath: automatically uses multiple network paths
- Used by: AWS EFA (p3, p4, trn1 instances)

SRD vs RC:
  RC: One QP per peer, fixed path, in-order delivery
  SRD: One QP for all peers, multipath, automatic failover

This enables:
  N nodes needing only O(1) QPs each (not O(N) like RC)
  Perfect for large ML training clusters (AWS Trainium, SageMaker)
```

---

## 22. Mental Models and Expert Intuition

### 22.1 The Five Mental Models for RDMA Mastery

```
MENTAL MODEL 1: THE POST OFFICE ANALOGY
=========================================

Traditional Networking = Postal Service
  - You write a letter (copy data to socket buffer)
  - Give it to the post office (kernel)
  - Post office processes, stamps, routes (TCP/IP stack)
  - Carrier delivers (NIC sends)
  - Recipient picks up from mailbox (interrupt, kernel delivers)
  Every step requires a human (kernel) to handle the package.

RDMA = Teleportation
  - You put the object in the teleporter (register memory)
  - Press the button (post WR to QP, ring doorbell)
  - Object appears in recipient's room (DMA to target)
  No intermediaries. No copies. Just physics (DMA).

MENTAL MODEL 2: THE TRUST FRAMEWORK
=====================================

Traditional: "The kernel is always in control"
  App cannot bypass OS for any resource access.
  This is safe but slow.

RDMA: "Hardware is trusted with controlled capabilities"
  The HCA is given a list of approved memory regions (MTT).
  QPs are pre-configured with allowed operations.
  Hardware checks against this list without kernel involvement.
  Breaking trust (wrong key, out-of-bounds) = hardware exception.

MENTAL MODEL 3: THE PRODUCER-CONSUMER QUEUE
============================================

A QP's Send Queue is a lock-free SPSC (Single Producer, Single Consumer) ring:
  Producer: Your code (posting WRs)
  Consumer: HCA hardware (processing WRs)
  
  No mutex needed! The HCA reads from one end,
  you write to the other end. Doorbell tells HCA "there's new work."
  
  Same for CQ: HCA produces CQEs, your code consumes them.

MENTAL MODEL 4: THE STATE MACHINE AS CONTRACT
==============================================

QP states are not just implementation detail — they are a CONTRACT:
  RESET: "I exist but can do nothing"
  INIT:  "I'm configured; accept receives"
  RTR:   "I know who to talk to; peer can send to me"
  RTS:   "I'm ready to send AND receive"
  
  Violating this order (e.g., posting sends before RTS) corrupts
  the contract with the hardware. Kernel enforces these transitions.

MENTAL MODEL 5: MEMORY AS NETWORK ENDPOINT
==========================================

In RDMA, memory itself becomes a network endpoint.
  Traditional: "Send to IP:port" (process endpoint)
  RDMA Write:  "Write to memory_address:rkey" (memory endpoint)
  
  This inversion is profound:
  - No need for both processes to be running simultaneously
  - The "receiver" is just a memory region, not a process
  - One process can write to 1000 remote memory regions
    with the same CPU cost as writing to one!
```

### 22.2 Common Pitfalls and How Experts Think About Them

```
PITFALL 1: RNR (Receiver Not Ready)
=====================================

SYMPTOM: IBV_WC_RNR_RETRY_EXC_ERR errors

CAUSE: You post sends faster than the peer posts receives.
  Your QP attempts to send -> peer has no recv buffer ready
  -> peer sends RNR NAK -> you retry -> eventually give up.

EXPERT FIX:
  1. Always pre-post receives BEFORE sending any data
  2. Set rnr_retry = 7 (infinite) during development
  3. Maintain a high watermark of recv WRs in flight
  4. Use SRQ to decouple receive posting from specific QPs

PITFALL 2: WR_FLUSH_ERR Cascade
=================================

SYMPTOM: Many IBV_WC_WR_FLUSH_ERR in CQ

CAUSE: QP entered ERROR state. ALL pending WRs in SQ and RQ
  are immediately flushed (completed with WR_FLUSH_ERR).

EXPERT FIX:
  1. One real error causes cascade of FLUSH_ERR — normal!
  2. Check for the REAL first error (usually not WR_FLUSH_ERR)
  3. Track the FIRST non-FLUSH error in your CQE handler
  4. Recreate the QP and reconnect; you cannot recover a broken QP

PITFALL 3: Memory Registration on Data Path
============================================

SYMPTOM: Terrible performance, high CPU usage

CAUSE: Calling ibv_reg_mr/ibv_dereg_mr per message.
  These call the kernel! No bypass! Very expensive.

EXPERT FIX:
  Use a memory pool: one large registration, subdivide for messages.
  Libraries (UCX, libfabric) implement this as MR caches.

PITFALL 4: Forgetting IBV_ACCESS_LOCAL_WRITE for Receives
==========================================================

SYMPTOM: ibv_reg_mr succeeds but ibv_post_recv fails or
  receive completions have LOC_PROT_ERR.

CAUSE: Receive WRs require LOCAL_WRITE permission on the MR
  because the HCA needs to WRITE incoming data into your buffer.
  Even though you're "receiving" (from your perspective), the
  HCA is WRITING to your memory.

EXPERT FIX:
  Always register receive buffers with IBV_ACCESS_LOCAL_WRITE.

PITFALL 5: Completion Queue Overflow
======================================

SYMPTOM: ibv_poll_cq returns negative; missing completions.

CAUSE: You posted more WRs with IBV_SEND_SIGNALED than the CQ
  can hold (cqe parameter when creating CQ).
  CQ overflow is a fatal error; you lose completions.

EXPERT FIX:
  CQ depth >= SQ depth + RQ depth (for all QPs sharing this CQ).
  Or use selective signaling to reduce CQE rate.

PITFALL 6: NUMA Mismatch
==========================

SYMPTOM: Latency 2x higher than expected despite correct code.

CAUSE: Your thread runs on CPU 0 (NUMA node 0) but HCA is on
  NUMA node 1. Every buffer access crosses the NUMA interconnect
  (adds ~100 ns) and buffer DMA by HCA also crosses NUMA.

EXPERT FIX:
  1. Find HCA NUMA node: cat /sys/class/infiniband/mlx5_0/device/numa_node
  2. Allocate buffers on that NUMA node: numa_alloc_onnode()
  3. Pin threads to that NUMA node: numactl --cpunodebind=N
```

### 22.3 Expert Design Patterns

```
PATTERN 1: RDMA RENDEZVOUS PROTOCOL
=====================================

For variable-length messages where receiver doesn't know size in advance:

  Sender                              Receiver
    |                                    |
    |-- SEND (small header with size)--->|
    |                                    | Allocate buffer of that size
    |                                    | Register MR
    |<-- SEND (rkey + addr) -------------|
    |                                    |
    | RDMA WRITE (entire payload) ------>|
    | RDMA WRITE (sentinel/flag) ------->|
    |                                    | Poll sentinel (no CPU interrupt)
    |-- SEND (ack) --------------------->|

This combines:
  - Two-sided for control (small, cheap)
  - One-sided RDMA Write for data (large, cheap, zero-copy)

PATTERN 2: DOORBELL BATCHING
==============================

Instead of ringing doorbell after every WR:
  for 1..N:
      write WR to SQ (no doorbell)
  ring doorbell once  // One MMIO write for N WRs
  
  Reduces PCI bus transactions by N.
  Critical for small-message high-rate workloads.

PATTERN 3: CREDIT-BASED FLOW CONTROL
======================================

In application-level flow control (above the HCA's RDMA):
  Receiver maintains N recv credits
  Sends credit updates to sender via RDMA Write (fast!)
  Sender can only have N outstanding sends
  
  This prevents RNR without dedicated monitoring threads.
  Used by: MPI libraries, RPC frameworks over RDMA.

PATTERN 4: TWO-SIDED FOR CONTROL, ONE-SIDED FOR DATA
======================================================

The golden rule of RDMA application design:
  
  Use Send/Recv for:   Control messages, small messages, signaling
  Use RDMA Write for:  Bulk data transfer (MBs to GBs)
  Use RDMA Read for:   Fetching remote state (when push isn't possible)
  Use Atomics for:     Synchronization, distributed counters
  
  Never use Send/Recv for bulk data! It's slower because:
  1. Requires pre-posted recv buffers (management overhead)
  2. CPU on receiver side (even just to re-post buffers)
  3. One completion per message on BOTH sides
  
  RDMA Write generates only ONE completion (on sender side).
  Receiver is never involved. Scale to thousands of senders!
```

---

## Appendix A: Quick Reference Card

```
RDMA VERB QUICK REFERENCE
==========================

SETUP:
  ibv_get_device_list()     -> list of devices
  ibv_open_device()         -> ibv_context *
  ibv_alloc_pd()            -> ibv_pd *
  ibv_reg_mr()              -> ibv_mr * (has lkey, rkey)
  ibv_create_cq()           -> ibv_cq *
  ibv_create_qp()           -> ibv_qp * (in RESET state)
  ibv_modify_qp()           -> transition: RESET->INIT->RTR->RTS

OPERATIONS:
  ibv_post_recv()           -> pre-post receive buffers
  ibv_post_send()           -> send/rdma_write/rdma_read/atomic
  ibv_poll_cq()             -> check for completions (returns ibv_wc[])

RDMA CM:
  rdma_create_event_channel()
  rdma_create_id()
  rdma_bind_addr() + rdma_listen()  [server]
  rdma_resolve_addr() + rdma_resolve_route() + rdma_connect()  [client]
  rdma_get_cm_event()       -> events: CONNECT_REQUEST, ESTABLISHED, etc.
  rdma_create_qp()          -> create QP tied to cm_id
  rdma_accept() / rdma_connect()

CLEANUP (reverse order of creation!):
  ibv_dereg_mr()
  ibv_destroy_qp() or rdma_destroy_qp()
  ibv_destroy_cq()
  ibv_dealloc_pd()
  ibv_close_device()
  rdma_destroy_id()
  rdma_destroy_event_channel()

OPCODES:
  IBV_WR_SEND               -> two-sided send
  IBV_WR_SEND_WITH_IMM      -> two-sided send with 32b immediate
  IBV_WR_RDMA_WRITE         -> one-sided write (no recv needed)
  IBV_WR_RDMA_WRITE_WITH_IMM-> one-sided write + recv notification
  IBV_WR_RDMA_READ          -> one-sided read (fetch from remote)
  IBV_WR_ATOMIC_CMP_AND_SWP -> atomic CAS (8B, must be aligned)
  IBV_WR_ATOMIC_FETCH_AND_ADD-> atomic FAA (8B, must be aligned)
```

## Appendix B: System Setup and Installation

```bash
# Install OFED (RDMA software stack) on Ubuntu:
apt-get install rdma-core ibverbs-utils infiniband-diags
apt-get install libibverbs-dev librdmacm-dev  # development headers

# For Mellanox:
# Download MLNX_OFED from mellanox.com (HCA-specific drivers)
./mlnxofedinstall

# Load RDMA modules:
modprobe ib_core
modprobe ib_uverbs
modprobe rdma_cm
modprobe mlx5_ib   # for Mellanox ConnectX

# Setup soft-RoCE for testing (no special hardware needed):
modprobe rdma_rxe
rdma link add rxe0 type rxe netdev eth0
ibv_devinfo  # should now show rxe0

# Setup IPoIB:
modprobe ib_ipoib
ip link set ib0 up
ip addr add 10.0.0.1/24 dev ib0

# Key config files:
# /etc/rdma/rdma.conf          - module load config
# /etc/opensm/opensm.conf      - Subnet Manager config
# /etc/security/limits.conf    - increase memlock for large MRs:
echo "* soft memlock unlimited" >> /etc/security/limits.conf
echo "* hard memlock unlimited" >> /etc/security/limits.conf
```

---

*This guide covers RDMA and InfiniBand from first principles through expert-level
implementation. The mental models presented here — particularly the memory-as-endpoint
model, the hardware-as-trusted-executor model, and the producer-consumer queue model —
are the foundations upon which all RDMA expertise is built. Master these abstractions
and you will be able to reason about any RDMA system, debug any RDMA problem, and
design any RDMA application with clarity and confidence.*

*Study it once to understand. Study it again to internalize. Study it a third time
and you will start teaching it.*