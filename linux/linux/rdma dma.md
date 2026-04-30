# DMA & RDMA in the Linux Kernel
## A Complete, In-Depth Guide for Systems Programmers

> **Philosophy**: Every concept here is built from first principles. No assumption of prior knowledge. Every term is defined before use. Diagrams use ASCII art only. Code is in C and Rust.

---

## Table of Contents

1. [The Problem DMA Solves](#1-the-problem-dma-solves)
2. [CPU Architecture & Memory Fundamentals](#2-cpu-architecture--memory-fundamentals)
3. [What is DMA](#3-what-is-dma)
4. [Address Spaces - The Most Critical Concept](#4-address-spaces---the-most-critical-concept)
5. [Linux DMA API - Coherent vs Streaming](#5-linux-dma-api---coherent-vs-streaming)
6. [IOMMU - The Hardware MMU for Devices](#6-iommu---the-hardware-mmu-for-devices)
7. [DMA Engine Subsystem](#7-dma-engine-subsystem)
8. [DMA Pools](#8-dma-pools)
9. [Memory Barriers & Cache Coherency](#9-memory-barriers--cache-coherency)
10. [Writing a DMA Driver in C](#10-writing-a-dma-driver-in-c)
11. [DMA in Rust (Linux Kernel)](#11-dma-in-rust-linux-kernel)
12. [RDMA - Remote Direct Memory Access](#12-rdma---remote-direct-memory-access)
13. [RDMA Architecture & Key Concepts](#13-rdma-architecture--key-concepts)
14. [RDMA Technologies: IB, RoCE, iWARP](#14-rdma-technologies-ib-roce-iwarp)
15. [Linux RDMA Stack Deep Dive](#15-linux-rdma-stack-deep-dive)
16. [RDMA Verbs Programming in C](#16-rdma-verbs-programming-in-c)
17. [RDMA in Rust](#17-rdma-in-rust)
18. [Performance Tuning & Advanced Topics](#18-performance-tuning--advanced-topics)
19. [Debugging DMA & RDMA Issues](#19-debugging-dma--rdma-issues)
20. [Reference: Key Data Structures](#20-reference-key-data-structures)

---

## 1. The Problem DMA Solves

### 1.1 How Data Moved Before DMA

Before DMA existed, every byte of data had to pass through the CPU. This is called **Programmed I/O (PIO)**.

```
PROGRAMMED I/O (PIO) - The Old Way
====================================

  ┌──────────┐    read byte    ┌──────────┐    write byte    ┌──────────┐
  │  DEVICE  │ ──────────────► │   CPU    │ ───────────────► │  MEMORY  │
  │  (disk)  │                 │ (ALU+REG)│                  │  (RAM)   │
  └──────────┘                 └──────────┘                  └──────────┘

  Problem: CPU is the bottleneck.
  - CPU does NOTHING useful while ferrying bytes
  - 1 MB transfer = CPU executes ~1,000,000 load+store pairs
  - CPU utilization: 100% on useless work
  - All other processes STALL
```

### 1.2 The DMA Solution

DMA means a **dedicated hardware controller** moves data between device and memory **without CPU involvement**.

```
DMA - Direct Memory Access
===========================

  ┌──────────┐   (1) CPU programs DMA   ┌──────────────┐
  │   CPU    │ ─────────────────────────► │ DMA Controller│
  └──────────┘                           │   (DMAC)     │
       │                                 └──────┬───────┘
       │ (2) CPU goes to do other work          │
       ▼                                        │ (3) DMAC moves data
  ┌──────────┐                                  │     autonomously
  │ Run other│                                  ▼
  │processes │                           ┌──────────────┐    ┌──────────┐
  └──────────┘                           │   DEVICE     │───►│  MEMORY  │
                                         │   (disk/NIC) │    │  (RAM)   │
       ▲                                 └──────────────┘    └──────────┘
       │ (4) DMAC raises interrupt
       │     "Transfer done!"
  ┌──────────┐
  │   CPU    │ ◄── wakes up, uses the data
  └──────────┘
```

### 1.3 Quantifying the Difference

```
PERFORMANCE COMPARISON
=======================

Scenario: Transfer 1 GB from NVMe SSD to RAM

PIO:
  - CPU executes ~1 billion instructions (load + store)
  - At 3 GHz: ~333 ms of CPU time wasted
  - System throughput: severely degraded
  - CPU cache: completely polluted

DMA:
  - CPU programs DMAC: ~10 instructions
  - CPU is FREE during transfer
  - DMAC uses dedicated DMA bus
  - NVMe bandwidth: 7 GB/s (limited by device, not CPU)
  - CPU cache: untouched
  - System throughput: unaffected

Winner: DMA by orders of magnitude
```

---

## 2. CPU Architecture & Memory Fundamentals

### 2.1 The Memory Hierarchy (You MUST Know This)

```
MEMORY HIERARCHY
=================

  Fastest / Smallest / Most Expensive
  ┌─────────────────────────────────────┐
  │  CPU Registers (64-bit, ~16-32)     │  ~0.3 ns, ~1 KB
  ├─────────────────────────────────────┤
  │  L1 Cache (per-core)                │  ~1 ns, 32-64 KB
  ├─────────────────────────────────────┤
  │  L2 Cache (per-core or shared)      │  ~4 ns, 256 KB - 1 MB
  ├─────────────────────────────────────┤
  │  L3 Cache (shared across cores)     │  ~10-40 ns, 8-64 MB
  ├─────────────────────────────────────┤
  │  Main Memory (DRAM - RAM)           │  ~60-100 ns, 8-512 GB
  ├─────────────────────────────────────┤
  │  NVMe SSD                           │  ~100 µs, 512 GB - 4 TB
  ├─────────────────────────────────────┤
  │  SATA SSD / HDD                     │  ~0.1-10 ms, up to 20 TB
  └─────────────────────────────────────┘
  Slowest / Largest / Cheapest
```

**Key insight for DMA**: DMA deals with the boundary between RAM and devices. It needs to address RAM correctly.

### 2.2 The System Bus Architecture

```
MODERN x86-64 SYSTEM ARCHITECTURE
====================================

  ┌─────────────────────────────────────────────────────────────────┐
  │                        CPU Package                              │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
  │  │  Core 0  │  │  Core 1  │  │  Core 2  │  │  Core 3  │       │
  │  │ L1+L2    │  │ L1+L2    │  │ L1+L2    │  │ L1+L2    │       │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
  │       └─────────────┴──────────────┴─────────────┘             │
  │                              │                                  │
  │                    ┌─────────▼──────────┐                      │
  │                    │    L3 Cache (LLC)   │                      │
  │                    └─────────┬──────────┘                      │
  │                              │                                  │
  │                    ┌─────────▼──────────┐                      │
  │                    │  Memory Controller  │                      │
  │                    └─────────┬──────────┘                      │
  └──────────────────────────────┼─────────────────────────────────┘
                                 │ DDR4/DDR5 Bus
                    ┌────────────▼───────────────┐
                    │         DRAM (RAM)          │
                    │   Physical Memory Banks     │
                    └────────────────────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │    PCIe Root Complex        │◄──── In CPU or
                    │    (part of chipset/CPU)    │      Chipset
                    └────────────┬───────────────┘
                                 │ PCIe Bus
          ┌──────────────────────┼─────────────────────────┐
          │                      │                          │
  ┌───────▼──────┐    ┌──────────▼───────┐    ┌────────────▼──────┐
  │  NVMe SSD    │    │   GPU            │    │  Network Card     │
  │  (PCIe 4.0)  │    │   (PCIe 4.0 x16) │    │  (PCIe 3.0 x8)   │
  └──────────────┘    └──────────────────┘    └───────────────────┘

KEY: All PCIe devices CAN become DMA masters — they initiate
     memory reads/writes DIRECTLY to/from DRAM.
```

### 2.3 What is a Bus Master?

**Bus master**: A device that can initiate transactions on the system bus WITHOUT CPU involvement. All DMA-capable devices are bus masters.

```
BUS MASTERING
==============

Non-DMA device (bus slave):
  Device ──► CPU ──► Memory
  (device requests CPU, CPU does the work)

DMA device (bus master):
  Device ──────────────────────► Memory
  (device directly reads/writes memory)
  CPU: just watching, or doing other work
```

---

## 3. What is DMA

### 3.1 Formal Definition

**DMA (Direct Memory Access)**: A mechanism allowing hardware devices to transfer data to/from system memory independently of the CPU, using a dedicated DMA Controller (DMAC) or the device's own DMA engine.

### 3.2 Types of DMA

```
DMA TYPES
==========

1. FIRST-PARTY DMA (Bus Mastering DMA)
   - The device itself is the DMA controller
   - Modern PCIe devices (NVMe, GPU, NIC) all use this
   - Device has its own DMA engine internally
   - Example: NIC fetches packet data from RAM directly

   CPU ──── programs ───► NIC's internal DMA engine
                                    │
                                    ▼
                          NIC reads TX buffer from RAM
                          NIC writes RX data to RAM

2. THIRD-PARTY DMA (External DMAC)
   - Separate DMA controller chip (DMAC)
   - Common in embedded systems (ARM, MIPS)
   - CPU programs DMAC, DMAC does the work
   - Example: STM32 microcontroller DMA

   CPU ──── programs ───► DMAC ──── transfers ───► Memory ◄──► Device

3. IOMMU-ASSISTED DMA (Modern Systems)
   - IOMMU sits between device and RAM
   - Provides address translation for devices
   - Adds security and isolation
   - Intel VT-d / AMD-Vi
   - We cover this in Section 6
```

### 3.3 DMA Transfer Modes

```
DMA TRANSFER MODES
===================

┌─────────────────────────────────────────────────────────────────┐
│ BURST MODE                                                       │
│   - DMA takes exclusive bus control                             │
│   - Transfers entire block at once                              │
│   - CPU cannot access memory during transfer                    │
│   - Fast but blocks CPU                                         │
│                                                                  │
│   Timeline: ────[CPU]────[DMA BURST]────[CPU]────              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CYCLE STEALING MODE                                              │
│   - DMA "steals" one bus cycle at a time                        │
│   - Interleaved with CPU bus cycles                             │
│   - Slower than burst but CPU still runs                        │
│                                                                  │
│   Timeline: ──[CPU][DMA][CPU][DMA][CPU][DMA]──                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TRANSPARENT MODE                                                 │
│   - DMA only runs when CPU doesn't need the bus                 │
│   - Zero impact on CPU performance                              │
│   - Slowest for DMA                                             │
│                                                                  │
│   Timeline: ──[CPU    ][DMA][CPU      ][DMA]──                 │
└─────────────────────────────────────────────────────────────────┘

Modern PCIe DMA: Uses burst-like transfers on dedicated PCIe lanes,
no actual bus contention with CPU memory accesses (separate paths).
```

---

## 4. Address Spaces - The Most Critical Concept

> **This is the single most important concept in DMA programming. Get this wrong and you get corrupted data, crashes, or security holes.**

### 4.1 The Four Address Spaces

```
THE FOUR ADDRESS SPACES IN LINUX
==================================

┌──────────────────────────────────────────────────────────────────┐
│ 1. PHYSICAL ADDRESS (PA)                                         │
│    ─────────────────────                                         │
│    - Real hardware address on the memory bus                    │
│    - What the CPU's memory controller uses                      │
│    - Range: 0 to max_physical_memory                            │
│    - Type in kernel: phys_addr_t                                │
│    - Example: 0x100000000 (4 GB mark)                           │
│    - WHO uses it: Memory controller, sometimes DMA              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 2. VIRTUAL ADDRESS (VA) / Kernel Virtual Address (KVA)          │
│    ──────────────────────────────────────────────────           │
│    - What software (kernel + userspace) sees                    │
│    - CPU MMU translates VA → PA via page tables                 │
│    - Type in kernel: void * or unsigned long                    │
│    - Kernel range: 0xffff888000000000 (x86-64 direct map)       │
│    - WHO uses it: CPU instructions, kernel code                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 3. BUS ADDRESS / DMA ADDRESS                                     │
│    ────────────────────────────                                  │
│    - What the DEVICE sees when addressing memory                │
│    - Goes through IOMMU translation (if present)                │
│    - Type in kernel: dma_addr_t                                 │
│    - WITHOUT IOMMU: bus address == physical address             │
│    - WITH IOMMU: bus address is device-virtual, mapped to PA    │
│    - WHO uses it: DMA-capable hardware devices                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 4. USER VIRTUAL ADDRESS (UVA)                                    │
│    ───────────────────────────                                   │
│    - Virtual address in userspace process                       │
│    - Per-process page tables                                    │
│    - Range: 0 to 0x7fffffffffff (128 TB on x86-64)              │
│    - WHO uses it: User programs, RDMA pinned memory             │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Address Translation Map

```
ADDRESS TRANSLATION RELATIONSHIPS
===================================

  User Process                Kernel                    Hardware
  ──────────                  ──────                    ────────

  User Virtual Addr           Kernel Virtual Addr
       │                            │
       │    CPU MMU                 │    CPU MMU
       │  (page tables)             │  (page tables)
       │                            │
       └──────────────►  Physical Address  ◄──────────────
                                    │
                                    │  IOMMU (if present)
                                    │  (IO page tables)
                                    │
                                    └────────────────────► DMA/Bus Address
                                                          (what device uses)

CONVERSIONS IN LINUX KERNEL:
  virt_to_phys(virt)       → physical address
  phys_to_virt(phys)       → kernel virtual address
  dma_map_single(dev, virt, size, dir) → dma_addr_t
  dma_unmap_single(...)    → releases mapping
```

### 4.3 Why This Matters: A Real Bug Scenario

```
BUG: Passing Wrong Address Type to Device
===========================================

// WRONG CODE (common beginner mistake):
void *buf = kmalloc(4096, GFP_KERNEL);
// buf is a KERNEL VIRTUAL address, e.g., 0xffff888100000000

// Programmer incorrectly passes virtual address to device:
device->dma_address_register = (u64)buf;  // BUG!!!

// What happens:
// Device tries to DMA from address 0xffff888100000000
// But device's bus sees a completely different address space!
// Result: Device reads garbage, corrupts memory, or crashes

// CORRECT CODE:
void *buf = kmalloc(4096, GFP_KERNEL);
dma_addr_t dma_addr = dma_map_single(dev, buf, 4096, DMA_FROM_DEVICE);
if (dma_mapping_error(dev, dma_addr)) { /* handle error */ }

device->dma_address_register = dma_addr;  // CORRECT: bus address
// ... device does DMA ...
dma_unmap_single(dev, dma_addr, 4096, DMA_FROM_DEVICE);
// Now safe to access buf from CPU
```

### 4.4 x86-64 Virtual Address Layout

```
x86-64 LINUX VIRTUAL ADDRESS SPACE (5-level paging, 57-bit)
=============================================================

0xffffffffffffffff ┬─────────────────────────────────────────┐
                   │  Kernel Space                           │
0xffff888000000000 │  Direct mapping of physical memory      │◄── phys_to_virt()
                   │  (all of RAM mapped here)               │
0xffff000000000000 │  Kernel virtual addresses               │
                   │  (modules, vmalloc, etc.)               │
                   ├─────────────────────────────────────────┤
                   │  Non-canonical (hole)                   │
                   │  (hardware enforces gap)                │
                   ├─────────────────────────────────────────┤
0x00007fffffffffff │  User Space                             │
                   │  Stack (grows down)                     │
                   │  Memory-mapped files (mmap)             │
                   │  Heap (grows up)                        │
                   │  BSS, Data, Text segments               │
0x0000000000000000 └─────────────────────────────────────────┘
```

---

## 5. Linux DMA API - Coherent vs Streaming

### 5.1 The Two DMA Mapping Types

```
DMA MAPPING TYPES
==================

┌─────────────────────────────────────────────────────────────────┐
│ COHERENT DMA (also called "consistent" or "synchronous")        │
│                                                                  │
│ - Memory is ALWAYS visible to both CPU and device               │
│ - No explicit cache management needed                           │
│ - Allocated once, used many times                               │
│ - Usually allocated from special memory (uncached or SWIOTLB)   │
│ - Slower per-access (uncached CPU access)                       │
│ - Use for: control structures, descriptors, rings               │
│                                                                  │
│ API: dma_alloc_coherent() / dma_free_coherent()                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STREAMING DMA (also called "asynchronous")                      │
│                                                                  │
│ - Memory used for a specific, finite transfer                   │
│ - CPU must "hand off" to device, then "take back"               │
│ - Cache management IS required (flush/invalidate)               │
│ - Mapped just before use, unmapped after                        │
│ - Faster CPU access when CPU owns the buffer                    │
│ - Use for: packet buffers, I/O data, bulk transfers             │
│                                                                  │
│ API: dma_map_single() / dma_unmap_single()                      │
│      dma_map_sg() / dma_unmap_sg() (scatter-gather)             │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Coherent DMA - Deep Dive

```c
/*
 * COHERENT DMA - Complete Example
 *
 * Use Case: NIC descriptor ring (a circular buffer of
 * descriptors that both CPU and NIC read/write constantly)
 */

#include <linux/dma-mapping.h>
#include <linux/pci.h>

/* Descriptor structure - NIC reads these to know what to transmit */
struct tx_descriptor {
    __le64 buffer_address;   /* DMA address of data buffer */
    __le32 buffer_length;    /* Length of data */
    __le32 flags;            /* Descriptor control flags */
};

#define TX_RING_SIZE 256

struct my_nic {
    struct pci_dev *pdev;

    /* Coherent memory: the descriptor ring */
    struct tx_descriptor *tx_ring;      /* CPU virtual address */
    dma_addr_t            tx_ring_dma;  /* DMA/bus address for NIC */

    /* Coherent memory: status/control area */
    u32   *ctrl_reg;
    dma_addr_t ctrl_reg_dma;
};

static int allocate_coherent_memory(struct my_nic *nic)
{
    struct device *dev = &nic->pdev->dev;
    size_t ring_size = TX_RING_SIZE * sizeof(struct tx_descriptor);

    /*
     * dma_alloc_coherent():
     *   - Allocates ring_size bytes
     *   - Returns CPU virtual address (nic->tx_ring)
     *   - Fills in DMA address (nic->tx_ring_dma)
     *   - Memory is cache-coherent (no flush needed)
     *   - On x86: uses write-combining or uncached memory
     *   - On ARM: may use DMA zone or special attributes
     */
    nic->tx_ring = dma_alloc_coherent(dev,
                                       ring_size,
                                       &nic->tx_ring_dma,
                                       GFP_KERNEL);
    if (!nic->tx_ring) {
        dev_err(dev, "Failed to allocate TX ring\n");
        return -ENOMEM;
    }

    /*
     * At this point:
     *   nic->tx_ring      = 0xffff888100200000 (example kernel virt addr)
     *   nic->tx_ring_dma  = 0x0000000100200000 (example bus addr, same as PA
     *                        on x86 without IOMMU, or IOMMU-mapped on ARM)
     *
     * CPU writes: nic->tx_ring[0].buffer_address = ...;
     * NIC reads:  using nic->tx_ring_dma as base address
     * Both see the SAME data without any explicit synchronization!
     */

    dev_info(dev, "TX ring: virt=%p, dma=0x%llx, size=%zu\n",
             nic->tx_ring, (u64)nic->tx_ring_dma, ring_size);

    return 0;
}

static void free_coherent_memory(struct my_nic *nic)
{
    struct device *dev = &nic->pdev->dev;
    size_t ring_size = TX_RING_SIZE * sizeof(struct tx_descriptor);

    if (nic->tx_ring) {
        dma_free_coherent(dev, ring_size, nic->tx_ring, nic->tx_ring_dma);
        nic->tx_ring = NULL;
        nic->tx_ring_dma = 0;
    }
}

/*
 * Example: CPU sets up a descriptor for the NIC to transmit
 */
static void setup_tx_descriptor(struct my_nic *nic, int idx,
                                  dma_addr_t data_dma, u32 data_len)
{
    struct tx_descriptor *desc = &nic->tx_ring[idx];

    /* CPU writes to coherent memory - NIC will see this immediately */
    desc->buffer_address = cpu_to_le64(data_dma);
    desc->buffer_length  = cpu_to_le32(data_len);
    desc->flags          = cpu_to_le32(TX_DESC_FLAG_OWN); /* hand off to NIC */

    /*
     * On x86: write is visible to NIC immediately (coherent cache)
     * On some ARM/MIPS: still coherent because dma_alloc_coherent
     *   allocated from non-cacheable memory
     * wmb() may be needed to prevent compiler/CPU reordering:
     */
    wmb(); /* write memory barrier - ensure ordering */
}
```

### 5.3 Streaming DMA - Deep Dive

```c
/*
 * STREAMING DMA - Complete Example
 *
 * Use Case: Receiving a network packet
 * The NIC writes packet data into a pre-allocated buffer.
 * After DMA completes, CPU reads and processes the packet.
 */

#include <linux/dma-mapping.h>
#include <linux/skbuff.h>

struct rx_buffer {
    void       *cpu_addr;   /* CPU virtual address */
    dma_addr_t  dma_addr;   /* DMA address given to device */
    size_t      size;
};

/*
 * STEP 1: Allocate and MAP the buffer (before device uses it)
 */
static int prepare_rx_buffer(struct device *dev, struct rx_buffer *rxbuf)
{
    rxbuf->size = 2048; /* 2KB receive buffer */

    /* Allocate normal kernel memory */
    rxbuf->cpu_addr = kmalloc(rxbuf->size, GFP_KERNEL | GFP_DMA);
    if (!rxbuf->cpu_addr)
        return -ENOMEM;

    /*
     * dma_map_single():
     *   - Maps CPU virtual addr to a DMA address
     *   - Direction: DMA_FROM_DEVICE (device writes, CPU reads)
     *   - This may:
     *     1. Return phys_to_bus(virt_to_phys(cpu_addr)) on simple systems
     *     2. Create an IOMMU mapping on systems with IOMMU
     *     3. Copy to a "bounce buffer" if address is not DMA-able
     *        (SWIOTLB - Software I/O Translation Look-aside Buffer)
     *   - Invalidates CPU caches for this region (on non-coherent archs)
     *     so device writes won't be overwritten by stale cache data
     */
    rxbuf->dma_addr = dma_map_single(dev,
                                      rxbuf->cpu_addr,
                                      rxbuf->size,
                                      DMA_FROM_DEVICE);

    if (dma_mapping_error(dev, rxbuf->dma_addr)) {
        dev_err(dev, "DMA mapping failed!\n");
        kfree(rxbuf->cpu_addr);
        return -ENOMEM;
    }

    /*
     * Now: rxbuf->dma_addr is given to the hardware.
     * IMPORTANT: CPU must NOT touch rxbuf->cpu_addr until unmap!
     * The memory "belongs to the device" now.
     */
    return 0;
}

/*
 * STEP 2: Give dma_addr to device, device does DMA
 *
 * [This happens in hardware - NIC writes packet to rxbuf->dma_addr]
 */

/*
 * STEP 3: Unmap after device is done, before CPU reads
 */
static void process_rx_buffer(struct device *dev, struct rx_buffer *rxbuf)
{
    /*
     * dma_unmap_single():
     *   - Direction: DMA_FROM_DEVICE
     *   - Invalidates/flushes CPU caches so CPU sees fresh device data
     *   - Releases IOMMU mapping if present
     *   - MUST be called before CPU reads the buffer contents
     *   - MUST match the map call exactly (same addr, size, direction)
     */
    dma_unmap_single(dev, rxbuf->dma_addr, rxbuf->size, DMA_FROM_DEVICE);

    /*
     * Now safe to read rxbuf->cpu_addr - data is visible to CPU
     */
    u8 *packet = rxbuf->cpu_addr;
    pr_info("First byte of received packet: 0x%02x\n", packet[0]);

    /* Process the packet... */
}

/*
 * STEP 4: Free when done
 */
static void free_rx_buffer(struct rx_buffer *rxbuf)
{
    kfree(rxbuf->cpu_addr);
    rxbuf->cpu_addr = NULL;
    rxbuf->dma_addr = 0;
}
```

### 5.4 DMA Direction Flags

```
DMA DIRECTION FLAGS
====================

┌────────────────────┬──────────────────────────────────────────────┐
│ DMA_TO_DEVICE      │ CPU writes buffer, device reads it           │
│                    │ (e.g., transmit: CPU fills TX buffer,        │
│                    │  NIC reads and sends over wire)              │
│                    │ Action: flush CPU cache (write-back) so      │
│                    │         device sees latest CPU writes        │
├────────────────────┼──────────────────────────────────────────────┤
│ DMA_FROM_DEVICE    │ Device writes buffer, CPU reads it           │
│                    │ (e.g., receive: NIC writes RX buffer,        │
│                    │  CPU reads and processes packet)             │
│                    │ Action: invalidate CPU cache so CPU          │
│                    │         doesn't read stale data              │
├────────────────────┼──────────────────────────────────────────────┤
│ DMA_BIDIRECTIONAL  │ Both directions (e.g., SCSI commands)        │
│                    │ Action: flush then invalidate cache          │
│                    │ Performance cost: most expensive             │
├────────────────────┼──────────────────────────────────────────────┤
│ DMA_NONE           │ No DMA (placeholder, should not be used)     │
└────────────────────┴──────────────────────────────────────────────┘

DECISION TREE FOR CHOOSING DIRECTION:
  Who writes first?
  ├── CPU writes, device reads → DMA_TO_DEVICE
  ├── Device writes, CPU reads → DMA_FROM_DEVICE
  └── Both read and write → DMA_BIDIRECTIONAL
```

### 5.5 Scatter-Gather DMA

```
WHAT IS SCATTER-GATHER?
========================

Problem: Data is often NOT in one contiguous memory block.
A network packet might span multiple non-contiguous pages.

Without Scatter-Gather:
  Page A: [data part 1]
  Page B: [data part 2]  ← non-contiguous!
  Page C: [data part 3]

  Option 1: Copy all parts to one contiguous buffer (SLOW, extra copy)
  Option 2: Use scatter-gather DMA!

With Scatter-Gather:
  Device has a "scatter-gather list" (sg list):
  ┌─────────────────────────────────────────────┐
  │ SG Entry 0: DMA addr = 0x1000, len = 1024   │
  │ SG Entry 1: DMA addr = 0x5000, len = 512    │
  │ SG Entry 2: DMA addr = 0x9000, len = 768    │
  └─────────────────────────────────────────────┘
  Device DMAes all three regions as one logical transfer!
```

```c
/*
 * SCATTER-GATHER DMA EXAMPLE
 * Use case: sending a large buffer that spans multiple pages
 */

#include <linux/scatterlist.h>
#include <linux/dma-mapping.h>

#define NUM_SG_ENTRIES 4

static int scatter_gather_example(struct device *dev)
{
    struct scatterlist sg[NUM_SG_ENTRIES];
    struct page *pages[NUM_SG_ENTRIES];
    int nents, i, ret = 0;

    /* Allocate pages (they may be non-contiguous in physical memory) */
    for (i = 0; i < NUM_SG_ENTRIES; i++) {
        pages[i] = alloc_page(GFP_KERNEL);
        if (!pages[i]) {
            ret = -ENOMEM;
            goto free_pages;
        }
        /* Fill with some data */
        memset(page_address(pages[i]), i + 1, PAGE_SIZE);
    }

    /* Initialize scatter-gather table */
    sg_init_table(sg, NUM_SG_ENTRIES);
    for (i = 0; i < NUM_SG_ENTRIES; i++) {
        /*
         * sg_set_page: assign page to sg entry
         * offset=0: start at beginning of page
         * length=PAGE_SIZE: use full page
         */
        sg_set_page(&sg[i], pages[i], PAGE_SIZE, 0);
    }

    /*
     * dma_map_sg():
     *   - Maps all sg entries to DMA addresses
     *   - May MERGE adjacent entries (hardware optimization)
     *   - Returns number of entries AFTER merging
     *     (may be LESS than NUM_SG_ENTRIES!)
     *   - Each sg[i].dma_address contains the DMA address
     *   - Each sg[i].dma_length contains the length
     */
    nents = dma_map_sg(dev, sg, NUM_SG_ENTRIES, DMA_TO_DEVICE);
    if (!nents) {
        dev_err(dev, "DMA map SG failed\n");
        ret = -ENOMEM;
        goto free_pages;
    }

    pr_info("Original SG entries: %d, After merge: %d\n",
            NUM_SG_ENTRIES, nents);

    /* Program device with scatter-gather list */
    for (i = 0; i < nents; i++) {
        pr_info("SG[%d]: dma_addr=0x%llx, len=%u\n",
                i, (u64)sg_dma_address(&sg[i]), sg_dma_len(&sg[i]));

        /* program_device_sg(device, sg_dma_address(&sg[i]),
                                    sg_dma_len(&sg[i]), i == nents-1); */
    }

    /* ... device performs scatter-gather DMA ... */

    /* Unmap after transfer */
    dma_unmap_sg(dev, sg, NUM_SG_ENTRIES, DMA_TO_DEVICE);
    /* Note: pass ORIGINAL count (NUM_SG_ENTRIES), not nents */

free_pages:
    for (i = 0; i < NUM_SG_ENTRIES; i++) {
        if (pages[i])
            __free_page(pages[i]);
    }
    return ret;
}
```

### 5.6 DMA Masks

```
DMA MASKS - WHAT ARE THEY?
===========================

"DMA mask" = the maximum physical address a device can DMA to/from.

Why? Old hardware is limited:
  - 24-bit ISA DMA: only addresses up to 16 MB (0x00FFFFFF)
  - 32-bit PCI:     only addresses up to 4 GB  (0xFFFFFFFF)
  - 64-bit PCIe:    full address space

Problem: If RAM > 4 GB and device has 32-bit DMA mask,
         device cannot DMA from/to addresses above 4 GB!

Solution: Linux uses SWIOTLB (bounce buffers) to copy data
          from high memory to low memory for such devices.
```

```c
/*
 * SETTING DMA MASKS
 */
static int configure_dma_mask(struct pci_dev *pdev)
{
    int ret;

    /*
     * Try 64-bit DMA first (can address all of RAM)
     * dma_set_mask_and_coherent sets BOTH:
     *   - streaming mask (for dma_map_*)
     *   - coherent mask (for dma_alloc_coherent)
     */
    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (ret) {
        /* 64-bit failed, try 32-bit */
        dev_warn(&pdev->dev, "64-bit DMA not supported, trying 32-bit\n");
        ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        if (ret) {
            dev_err(&pdev->dev, "DMA mask configuration failed\n");
            return ret;
        }
        dev_info(&pdev->dev, "Using 32-bit DMA\n");
    } else {
        dev_info(&pdev->dev, "Using 64-bit DMA\n");
    }

    return 0;
}

/*
 * DMA_BIT_MASK(n) = ((n) == 64 ? ~0ULL : ((1ULL << (n)) - 1))
 * DMA_BIT_MASK(32) = 0x00000000FFFFFFFF (4 GB max)
 * DMA_BIT_MASK(64) = 0xFFFFFFFFFFFFFFFF (no limit)
 */
```

### 5.7 SWIOTLB - Software I/O TLB (Bounce Buffers)

```
SWIOTLB (SOFTWARE IO TRANSLATION LOOKASIDE BUFFER)
====================================================

Problem: Device has 32-bit DMA mask, but kernel buffer is at 5 GB PA.
Device cannot DMA to/from 5 GB!

SWIOTLB Solution:
  1. Kernel pre-allocates a "bounce buffer" in low memory (<4 GB)
  2. dma_map_single() detects address is out of device's range
  3. Returns DMA address of bounce buffer (in low memory)
  4. For DMA_TO_DEVICE: kernel copies data to bounce buffer first
  5. Device DMAs from bounce buffer
  6. For DMA_FROM_DEVICE: device DMAs to bounce buffer
  7. dma_unmap_single() copies data from bounce buffer to original location

SWIOTLB Flow:
                                                          DMA mask=32bit
  ┌─────────────────────────────────────────────────────────────────┐
  │ HIGH MEMORY (>4 GB)                                             │
  │   Real buffer: 0x140000000 (5 GB)                              │
  │   [data here] ◄─────────────────────────────────┐              │
  └────────────────────────────────────────────────── ── ── ──      │
                                                    │ (copy)         │
  ┌─────────────────────────────────────────────────────────────────┐
  │ LOW MEMORY (<4 GB)                                              │
  │   Bounce buffer: 0x1000000 (16 MB)              │              │
  │   [data copy] ◄─────────────────────────────────┘              │
  │                                                                  │
  │        ◄──────────────── DMA ─────────────────────────────────  │
  │        Device                                                    │
  └─────────────────────────────────────────────────────────────────┘

Cost: Extra memory copy. SWIOTLB = performance penalty.
Prefer 64-bit DMA to avoid SWIOTLB!

Check if SWIOTLB is active:
  $ cat /proc/swiotlb  (or dmesg | grep -i swiotlb)
```

---

## 6. IOMMU - The Hardware MMU for Devices

### 6.1 What is an IOMMU?

**IOMMU** = Input/Output Memory Management Unit

Just like the CPU's MMU translates virtual addresses to physical addresses for the CPU, the IOMMU translates **device virtual addresses (IOVA)** to **physical addresses** for DMA devices.

```
WITHOUT IOMMU:
==============

  Device sees PHYSICAL addresses directly
  ┌────────┐  PA=0x1000000  ┌──────────────────────┐
  │ Device │ ─────────────► │  Physical RAM        │
  └────────┘                │  (any page!)         │
                            └──────────────────────┘
  Security problem: A buggy/malicious device can DMA to ANY address!
  Stability problem: No isolation between devices.

WITH IOMMU:
===========

  Device sees IOVA (device-virtual addresses)
  IOMMU translates IOVA → PA using IO page tables

  ┌────────┐  IOVA=0x1000  ┌──────────┐  PA=0x1000000  ┌───────────┐
  │ Device │ ─────────────► │  IOMMU   │ ─────────────► │ Specific  │
  └────────┘                │ (IO MMU) │                │ RAM Pages │
                            └──────────┘                └───────────┘
                                 │
                                 └── Blocks access to unmapped pages!
                                     Device can ONLY access mapped pages.
```

### 6.2 IOMMU Benefits

```
IOMMU BENEFITS
===============

1. SECURITY (DMA Isolation)
   - Each device gets its own IOMMU domain
   - Device can only access its mapped memory
   - Malicious PCIe device cannot attack system memory
   - Critical for cloud computing (multiple VMs sharing hardware)

2. VIRTUALIZATION (VFIO - Virtual Function I/O)
   - Pass physical device directly to VM
   - IOMMU remaps device's DMA to VM's physical memory
   - Guest VM programs device with guest physical addresses
   - IOMMU transparently translates to host physical addresses

3. LARGE PAGES (IO Huge Pages)
   - IOMMU supports 2 MB, 1 GB page sizes
   - Reduces TLB pressure for large DMA regions

4. SCATTER-GATHER SIMPLIFICATION
   - Physically non-contiguous pages can appear CONTIGUOUS to device
   - Device DMAes to one "virtual" contiguous region
   - IOMMU remaps to multiple physical pages

IOMMU Scatter-Gather:
  Device thinks:           IOMMU maps:         Physical RAM:
  ┌───────────────┐        ┌──────────┐        ┌───────────┐
  │ IOVA 0x0000   │───────►│ PA[0]    │───────►│ Page at   │
  │ IOVA 0x1000   │───────►│ PA[1]    │───────►│ 0x4000    │
  │ IOVA 0x2000   │───────►│ PA[2]    │───────►│ Page at   │
  │ (contiguous!) │        └──────────┘        │ 0x9000    │
  └───────────────┘                            └───────────┘
  Device sees one contiguous region, physical memory is scattered!
```

### 6.3 Intel VT-d and AMD-Vi

```
IOMMU IMPLEMENTATIONS
======================

Intel VT-d (Virtualization Technology for Directed I/O):
  - Intel's IOMMU technology
  - Part of Intel Virtualization Extensions
  - Kernel driver: drivers/iommu/intel/
  - Enable in BIOS: Intel VT-d or Intel Virtualization

AMD-Vi (AMD I/O Virtualization):
  - AMD's IOMMU technology
  - Also called AMD IOMMU
  - Kernel driver: drivers/iommu/amd/
  - Enable in BIOS: IOMMU or AMD-Vi

ARM SMMU (System Memory Management Unit):
  - ARM's equivalent of IOMMU
  - Used in servers, mobile SoCs
  - Kernel driver: drivers/iommu/arm/

Check if IOMMU is active:
  $ dmesg | grep -i iommu
  $ cat /sys/kernel/iommu_groups/*/devices

Kernel boot parameters:
  intel_iommu=on  (enable Intel IOMMU)
  amd_iommu=on    (enable AMD IOMMU)
  iommu=pt        (passthrough mode - disable IOMMU for non-VM use)
```

### 6.4 IOMMU Groups

```
IOMMU GROUPS
=============

An IOMMU group = set of devices that MUST be isolated together.
Devices in the same group share DMA isolation context.

Example: PCIe topology
  ┌────────────────────────────────────────┐
  │ PCIe Root Port                         │
  │   ├── Endpoint A (GPU)                 │ ← Group 0
  │   └── Switch                           │
  │         ├── Endpoint B (NIC function 0)│ ← Group 1
  │         └── Endpoint C (NIC function 1)│ ← Group 1 (same switch!)
  └────────────────────────────────────────┘

Group 1 contains both NIC functions because they share a switch.
If you want to pass NIC to a VM, you must pass BOTH functions.

Check groups:
  $ ls /sys/kernel/iommu_groups/
  $ for g in /sys/kernel/iommu_groups/*/devices/*; do echo $g; done
```

### 6.5 IOMMU API in Linux Kernel

```c
/*
 * IOMMU API - Used internally by DMA subsystem
 * Rarely called directly by drivers (use DMA API instead)
 * But important to understand for deep driver work
 */

#include <linux/iommu.h>

/* Get IOMMU domain for a device */
struct iommu_domain *domain = iommu_get_domain_for_dev(dev);

/* Map a physical address to an IOVA in the domain */
ret = iommu_map(domain,
                iova,          /* device-virtual address */
                paddr,         /* physical address */
                size,          /* size to map */
                IOMMU_READ | IOMMU_WRITE,  /* permissions */
                GFP_KERNEL);

/* Unmap */
iommu_unmap(domain, iova, size);

/* Translate IOVA → PA (for debugging) */
phys_addr_t pa = iommu_iova_to_phys(domain, iova);
```

---

## 7. DMA Engine Subsystem

### 7.1 What is the DMA Engine?

The **DMA Engine** subsystem is a Linux kernel framework for using hardware DMA controllers — especially in embedded systems where there's a dedicated DMA controller (DMAC) separate from devices.

```
DMA ENGINE SUBSYSTEM ARCHITECTURE
===================================

  ┌─────────────────────────────────────────────────────────────┐
  │                    User/Driver Space                        │
  │  (storage driver, audio driver, network driver, memcpy)    │
  └────────────────────────────┬────────────────────────────────┘
                               │ dmaengine API
  ┌────────────────────────────▼────────────────────────────────┐
  │                  DMA Engine Core                            │
  │  dma_request_channel()  dmaengine_prep_*()  dmaengine_submit│
  │  dma_async_issue_pending()  dma_wait_for_async_tx()         │
  └────────────────────────────┬────────────────────────────────┘
                               │
        ┌──────────────────────┼─────────────────────────┐
        ▼                      ▼                          ▼
  ┌───────────┐        ┌─────────────┐          ┌──────────────┐
  │  PL330    │        │  IOAT       │          │  BCM2835     │
  │  DMA      │        │  (Intel)    │          │  DMA         │
  │  driver   │        │  driver     │          │  driver      │
  │(ARM PL330)│        │(Crystal Bch)│          │ (Raspberry Pi│
  └───────────┘        └─────────────┘          └──────────────┘
       │                      │                          │
       ▼                      ▼                          ▼
  [ARM DMA HW]        [Intel CBDMA HW]          [BCM DMA HW]
```

### 7.2 DMA Engine Concepts

```
DMA ENGINE KEY CONCEPTS
========================

CHANNEL: A single DMA transfer "lane"
  - A DMAC may have 8 channels (8 simultaneous transfers)
  - Each channel has its own descriptor queue
  - Channels can be requested and released dynamically

DESCRIPTOR (dma_async_tx_descriptor):
  - Represents one DMA transfer operation
  - Contains: src, dst, length, flags, callback
  - Submitted to channel's pending queue
  - Engine processes queue in order

COOKIE (dma_cookie_t):
  - Unique ID returned when descriptor is submitted
  - Used to check completion status
  - Monotonically increasing integer

TRANSFER TYPES:
  - memcpy: memory to memory
  - memset: fill memory with a value
  - XOR: XOR multiple sources (RAID acceleration)
  - PQ: P+Q syndrome (RAID-6)
  - interrupt: generate interrupt only
  - slave_sg: scatter-gather for slave device
  - cyclic: circular buffer (audio, video)
```

### 7.3 DMA Engine API Usage

```c
/*
 * DMA ENGINE COMPLETE EXAMPLE
 * Use case: DMA memcpy acceleration (offload memcpy to hardware)
 */

#include <linux/dmaengine.h>
#include <linux/dma-mapping.h>
#include <linux/completion.h>

struct dma_memcpy_ctx {
    struct completion   done;
    dma_cookie_t        cookie;
    enum dma_status     status;
};

/* Callback: called when DMA transfer completes */
static void dma_memcpy_callback(void *data)
{
    struct dma_memcpy_ctx *ctx = data;

    ctx->status = DMA_COMPLETE;
    complete(&ctx->done);  /* wake up waiting thread */
}

static int hardware_dma_memcpy(struct device *dev,
                                 void *dst, void *src, size_t len)
{
    struct dma_chan *chan;
    struct dma_async_tx_descriptor *tx;
    struct dma_memcpy_ctx ctx;
    dma_addr_t src_dma, dst_dma;
    dma_cap_mask_t mask;
    int ret = 0;

    /* Step 1: Request a memcpy-capable DMA channel */
    dma_cap_zero(mask);
    dma_cap_set(DMA_MEMCPY, mask);  /* we want memcpy capability */

    chan = dma_request_channel(mask, NULL, NULL);
    if (!chan) {
        pr_err("No DMA channel available for memcpy\n");
        return -ENODEV;
    }

    /* Step 2: Map source and destination for DMA */
    src_dma = dma_map_single(dev, src, len, DMA_TO_DEVICE);
    if (dma_mapping_error(dev, src_dma)) {
        ret = -ENOMEM;
        goto release_chan;
    }

    dst_dma = dma_map_single(dev, dst, len, DMA_FROM_DEVICE);
    if (dma_mapping_error(dev, dst_dma)) {
        dma_unmap_single(dev, src_dma, len, DMA_TO_DEVICE);
        ret = -ENOMEM;
        goto release_chan;
    }

    /* Step 3: Prepare the descriptor */
    tx = dmaengine_prep_dma_memcpy(chan,
                                    dst_dma,    /* destination */
                                    src_dma,    /* source */
                                    len,        /* length */
                                    DMA_PREP_INTERRUPT);  /* fire callback */
    if (!tx) {
        pr_err("Failed to prepare DMA descriptor\n");
        ret = -ENOMEM;
        goto unmap;
    }

    /* Step 4: Set completion callback */
    init_completion(&ctx.done);
    tx->callback = dma_memcpy_callback;
    tx->callback_param = &ctx;

    /* Step 5: Submit descriptor to channel queue */
    ctx.cookie = dmaengine_submit(tx);
    if (dma_submit_error(ctx.cookie)) {
        pr_err("DMA submit failed\n");
        ret = -EIO;
        goto unmap;
    }

    /* Step 6: Fire all pending transfers on this channel */
    dma_async_issue_pending(chan);

    /* Step 7: Wait for completion (with 5 second timeout) */
    if (!wait_for_completion_timeout(&ctx.done, msecs_to_jiffies(5000))) {
        pr_err("DMA memcpy timed out!\n");
        dmaengine_terminate_sync(chan);  /* cancel the transfer */
        ret = -ETIMEDOUT;
        goto unmap;
    }

    /* Step 8: Check final status */
    ctx.status = dma_async_is_tx_complete(chan, ctx.cookie, NULL, NULL);
    if (ctx.status != DMA_COMPLETE) {
        pr_err("DMA transfer failed with status %d\n", ctx.status);
        ret = -EIO;
    }

unmap:
    dma_unmap_single(dev, src_dma, len, DMA_TO_DEVICE);
    dma_unmap_single(dev, dst_dma, len, DMA_FROM_DEVICE);
release_chan:
    dma_release_channel(chan);
    return ret;
}
```

### 7.4 Cyclic DMA (Audio Use Case)

```c
/*
 * CYCLIC DMA - For audio streaming
 * 
 * Audio hardware continuously transfers data in a circular buffer.
 * When it reaches the end, it wraps back to the beginning.
 * A callback fires at each "period" boundary.
 *
 *  Buffer:  [period0][period1][period2][period3][period0]...
 *            ↑                                   ↑
 *            start                            wraps here
 */

struct audio_dma_ctx {
    struct dma_chan              *chan;
    struct dma_async_tx_descriptor *tx;
    void                         *buf;
    dma_addr_t                    buf_dma;
    size_t                        buf_size;   /* total buffer size */
    size_t                        period_size; /* one period = one IRQ */
    unsigned int                  periods;
    dma_cookie_t                  cookie;
};

static void audio_period_callback(void *data)
{
    struct audio_dma_ctx *ctx = data;
    /* Called every time one period completes */
    /* Update write/read pointer, notify ALSA layer, etc. */
    pr_debug("Audio period complete\n");
}

static int setup_cyclic_dma(struct device *dev, struct audio_dma_ctx *ctx)
{
    dma_cap_mask_t mask;

    /* Allocate circular buffer (coherent so CPU and DMA both see it) */
    ctx->buf = dma_alloc_coherent(dev, ctx->buf_size,
                                   &ctx->buf_dma, GFP_KERNEL);
    if (!ctx->buf)
        return -ENOMEM;

    /* Request a channel supporting cyclic transfers */
    dma_cap_zero(mask);
    dma_cap_set(DMA_CYCLIC, mask);
    ctx->chan = dma_request_channel(mask, NULL, NULL);
    if (!ctx->chan) {
        dma_free_coherent(dev, ctx->buf_size, ctx->buf, ctx->buf_dma);
        return -ENODEV;
    }

    /*
     * Prepare cyclic descriptor:
     * - buf_addr: DMA address of circular buffer
     * - buf_len: total buffer length
     * - period_len: length of each period (callback fires here)
     * - direction: DMA_DEV_TO_MEM (device → memory, i.e., capture)
     * - flags: 0
     */
    ctx->tx = dmaengine_prep_dma_cyclic(ctx->chan,
                                         ctx->buf_dma,
                                         ctx->buf_size,
                                         ctx->period_size,
                                         DMA_DEV_TO_MEM,
                                         0);
    if (!ctx->tx)
        return -ENOMEM;

    ctx->tx->callback = audio_period_callback;
    ctx->tx->callback_param = ctx;

    ctx->cookie = dmaengine_submit(ctx->tx);
    dma_async_issue_pending(ctx->chan);

    return 0;
}
```

---

## 8. DMA Pools

### 8.1 What is a DMA Pool?

A **DMA pool** solves the problem of many small DMA allocations. `dma_alloc_coherent()` has high overhead for small sizes (it allocates at least one page = 4096 bytes). A DMA pool pre-allocates a large coherent region and sub-allocates from it.

```
DMA POOL CONCEPT
=================

Without pool: 100 descriptors × 32 bytes each
  100 × dma_alloc_coherent(32 bytes)
  → Each call may allocate 4 KB page, wasting 4064 bytes each!
  → Total wasted: ~400 KB
  → 100 IOMMU mappings
  → High overhead

With DMA pool: Pre-allocate 4 KB, carve out 32-byte chunks
  dma_pool_create(32 bytes per element)
  → One 4 KB allocation, 128 chunks available
  → dma_pool_alloc() for each descriptor: O(1), no system call
  → Minimal IOMMU mappings

Pool visualization:
  ┌────────────────────────────────────────────────────────────────┐
  │ DMA Pool (4 KB coherent region)                               │
  │ ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐    │
  │ │Chunk0││Chunk1││Chunk2││Chunk3││Chunk4││Chunk5││Chunk6│...  │
  │ │  32B ││  32B ││  32B ││  32B ││  32B ││  32B ││  32B │    │
  │ │(used)││(free)││(used)││(free)││(free)││(used)││(free)│    │
  │ └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘    │
  └────────────────────────────────────────────────────────────────┘
```

```c
/*
 * DMA POOL EXAMPLE
 * Use case: NIC descriptor allocation
 */

#include <linux/dmapool.h>

struct nic_driver {
    struct pci_dev  *pdev;
    struct dma_pool *desc_pool;
};

struct tx_desc {
    __le64 addr;
    __le32 len;
    __le32 cmd;
};  /* 16 bytes each */

static int create_descriptor_pool(struct nic_driver *nic)
{
    /*
     * dma_pool_create(name, dev, size, align, boundary)
     *   name:     for debugging
     *   dev:      the device
     *   size:     size of each element
     *   align:    alignment requirement (64 = 64-byte aligned)
     *   boundary: elements must not cross this boundary (0 = no restriction)
     *             useful when hardware requires descriptors to not cross
     *             4KB page boundaries
     */
    nic->desc_pool = dma_pool_create("nic_tx_desc",
                                      &nic->pdev->dev,
                                      sizeof(struct tx_desc),
                                      64,   /* 64-byte aligned */
                                      4096); /* don't cross 4KB boundary */
    if (!nic->desc_pool)
        return -ENOMEM;

    pr_info("DMA pool created: element size=%zu\n", sizeof(struct tx_desc));
    return 0;
}

static struct tx_desc *alloc_one_descriptor(struct nic_driver *nic,
                                             dma_addr_t *dma_handle)
{
    struct tx_desc *desc;

    /*
     * dma_pool_alloc():
     *   - O(1) allocation from pool
     *   - GFP_ATOMIC is safe in interrupt context
     *   - *dma_handle receives DMA address of this element
     *   - Returns CPU virtual address
     */
    desc = dma_pool_alloc(nic->desc_pool, GFP_ATOMIC, dma_handle);
    if (!desc) {
        pr_err("Pool exhausted! No descriptors available\n");
        return NULL;
    }

    /* Memory is already DMA-coherent, no mapping needed */
    memset(desc, 0, sizeof(*desc));
    return desc;
}

static void free_one_descriptor(struct nic_driver *nic,
                                  struct tx_desc *desc,
                                  dma_addr_t dma_handle)
{
    dma_pool_free(nic->desc_pool, desc, dma_handle);
}

static void destroy_pool(struct nic_driver *nic)
{
    /* Must free all allocated elements before calling this! */
    dma_pool_destroy(nic->desc_pool);
    nic->desc_pool = NULL;
}
```

---

## 9. Memory Barriers & Cache Coherency

### 9.1 Why Memory Barriers Matter in DMA

```
THE REORDERING PROBLEM
=======================

Modern CPUs and compilers reorder instructions for performance.
This breaks DMA protocols!

Example of the problem:
  CPU writes: desc->data = payload;
  CPU writes: desc->flags = OWNED_BY_DEVICE;  /* hand off */
  Device reads desc->flags, sees OWNED_BY_DEVICE
  Device reads desc->data ... but CPU write may not be visible yet!

Timeline without barrier:
  CPU:    [write flags=OWN] ─── [write data=payload]  ← CPU reordered!
  Device:                [read flags=OWN][read data=GARBAGE!]

Timeline with barrier:
  CPU:    [write data=payload] ─── BARRIER ─── [write flags=OWN]
  Device:                                             [read flags=OWN][read data=payload ✓]
```

### 9.2 Linux Memory Barrier API

```c
/*
 * MEMORY BARRIERS IN DMA CONTEXT
 */

/* mb()  - Full memory barrier: all reads AND writes before mb() 
 *          complete before any reads/writes after mb() */
mb();

/* wmb() - Write memory barrier: all writes before wmb() complete
 *          before any writes after wmb()
 *          Use when: CPU writes data, then writes descriptor flag */
wmb();

/* rmb() - Read memory barrier: all reads before rmb() complete
 *          before any reads after rmb()
 *          Use when: CPU reads descriptor flag, then reads data */
rmb();

/* dma_wmb() / dma_rmb() - DMA-specific barriers (often weaker than mb())
 *   On x86: these are no-ops (x86 is TSO - Total Store Order)
 *   On ARM: actual barrier instructions needed */
dma_wmb();  /* before writing descriptor "owned by device" bit */
dma_rmb();  /* after reading descriptor "owned by device" bit */

/*
 * PRACTICAL EXAMPLE: TX descriptor ring
 */
static void submit_tx_descriptor(struct my_ring *ring, int idx,
                                   dma_addr_t data_dma, u32 data_len)
{
    struct tx_desc *desc = &ring->descs[idx];

    /* Step 1: Write data address and length FIRST */
    desc->data_addr = cpu_to_le64(data_dma);
    desc->data_len  = cpu_to_le32(data_len);

    /*
     * Step 2: BARRIER before ownership transfer
     * Ensures device sees data_addr and data_len BEFORE OWN bit
     */
    dma_wmb();

    /* Step 3: Transfer ownership to device */
    desc->flags = cpu_to_le32(DESC_FLAG_OWN | DESC_FLAG_EOP);

    /*
     * Step 4: Barrier + doorbell to wake up device
     * wmb() ensures the OWN bit write is visible before doorbell
     */
    wmb();
    writel(idx, ring->doorbell_reg);  /* tell device about new descriptor */
}

static void process_completed_rx(struct my_ring *ring, int idx)
{
    struct rx_desc *desc = &ring->descs[idx];
    u32 flags;

    /* Read completion flag */
    flags = le32_to_cpu(desc->flags);

    /* Barrier: don't read data until we confirm device is done */
    if (!(flags & DESC_FLAG_OWN)) {
        dma_rmb();  /* device no longer owns it, now safe to read data */

        u32 received_len = le32_to_cpu(desc->data_len);
        /* Now process the received data... */
    }
}
```

### 9.3 Cache Coherency on Non-Coherent Architectures

```
CACHE COHERENCY PROBLEM (ARM, MIPS, PowerPC)
=============================================

On ARM systems without hardware cache coherency:
  CPU and DMA controller do NOT automatically see each other's writes!

  CPU cache:        [buffer with old data]
  Physical RAM:     [buffer with old data]
  DMA writes to:    Physical RAM → [buffer with NEW data]
  CPU reads from:   CPU cache → [OLD data!!]  ← STALE!

Linux handles this automatically via dma_map_*:

  dma_map_single(dev, buf, size, DMA_FROM_DEVICE):
    → Invalidates CPU cache for buf region
    → CPU will fetch fresh data from RAM on next access

  dma_map_single(dev, buf, size, DMA_TO_DEVICE):
    → Flushes (write-back) CPU cache for buf region
    → Device will see latest CPU writes in RAM

  For coherent allocation (dma_alloc_coherent):
    → On ARM: memory is allocated as uncached (or write-combining)
    → CPU accesses bypass cache entirely → always coherent
    → Performance cost: no cache for these buffers

ARCHITECTURE COMPARISON:
  x86/x86-64: Coherent between CPU and devices (mostly)
               dma_map_* on x86 mostly: IOMMU mapping only
  ARM:         May be non-coherent (depends on SoC/configuration)
               dma_map_* does actual cache operations
  ARM64:       Depends on CCI/CCN (Cache Coherent Interconnect)
```

---

## 10. Writing a DMA Driver in C

### 10.1 Complete PCIe DMA Driver Example

```c
/*
 * my_dma_driver.c - A complete PCIe DMA driver
 *
 * This driver implements:
 * 1. PCI device initialization
 * 2. DMA mask setup
 * 3. Coherent memory for descriptor ring
 * 4. Streaming DMA for data buffers
 * 5. Interrupt handling
 * 6. Clean teardown
 *
 * Compile: Add to Makefile obj-m += my_dma_driver.o
 */

#include <linux/module.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/interrupt.h>
#include <linux/io.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Systems Programmer");
MODULE_DESCRIPTION("Example PCIe DMA Driver");

/* ======================== DEVICE REGISTERS ======================== */
/* These are hardware-specific - replace with your device's register map */
#define REG_DMA_CTRL        0x00   /* DMA control register */
#define REG_DMA_SRC_ADDR_LO 0x04   /* Source address low 32 bits */
#define REG_DMA_SRC_ADDR_HI 0x08   /* Source address high 32 bits */
#define REG_DMA_DST_ADDR_LO 0x0C   /* Destination address low 32 bits */
#define REG_DMA_DST_ADDR_HI 0x10   /* Destination address high 32 bits */
#define REG_DMA_LENGTH      0x14   /* Transfer length in bytes */
#define REG_DMA_STATUS      0x18   /* Status register */
#define REG_IRQ_STATUS      0x1C   /* Interrupt status */
#define REG_IRQ_ENABLE      0x20   /* Interrupt enable */
#define REG_IRQ_CLEAR       0x24   /* Interrupt clear */

/* Control register bits */
#define DMA_CTRL_START      BIT(0)  /* Start transfer */
#define DMA_CTRL_RESET      BIT(1)  /* Reset DMA engine */

/* Status register bits */
#define DMA_STATUS_DONE     BIT(0)  /* Transfer complete */
#define DMA_STATUS_ERROR    BIT(1)  /* Error occurred */
#define DMA_STATUS_BUSY     BIT(2)  /* Transfer in progress */

/* IRQ bits */
#define IRQ_DMA_DONE        BIT(0)
#define IRQ_DMA_ERROR       BIT(1)

/* ======================== DATA STRUCTURES ======================== */

#define BUFFER_SIZE         (64 * 1024)  /* 64 KB per buffer */
#define NUM_BUFFERS         8

struct dma_buffer {
    void        *cpu_addr;          /* CPU virtual address */
    dma_addr_t   dma_addr;          /* DMA/bus address */
    size_t       size;
    bool         in_use;
    unsigned int index;
};

struct my_dma_device {
    struct pci_dev          *pdev;
    void __iomem            *bar0;          /* Memory-mapped registers */
    int                      irq;

    /* Descriptor ring (coherent - always visible to device) */
    struct {
        void       *vaddr;     /* Virtual address of ring base */
        dma_addr_t  dma_addr;  /* DMA address of ring base */
        size_t      size;      /* Total size */
        unsigned int head;     /* Next to fill */
        unsigned int tail;     /* Next to process */
    } ring;

    /* Data buffers (streaming DMA) */
    struct dma_buffer    buffers[NUM_BUFFERS];

    /* Synchronization */
    struct completion    transfer_done;
    spinlock_t           lock;
    bool                 transfer_in_progress;

    /* Statistics */
    u64 total_bytes_transferred;
    u32 total_transfers;
    u32 total_errors;
};

/* ======================== HELPER FUNCTIONS ======================== */

static inline u32 reg_read(struct my_dma_device *dev, u32 offset)
{
    return readl(dev->bar0 + offset);
}

static inline void reg_write(struct my_dma_device *dev, u32 offset, u32 val)
{
    writel(val, dev->bar0 + offset);
}

static inline void reg_write64(struct my_dma_device *dev, u32 lo_reg,
                                 u32 hi_reg, u64 val)
{
    reg_write(dev, lo_reg, lower_32_bits(val));
    reg_write(dev, hi_reg, upper_32_bits(val));
}

/* ======================== DMA INITIALIZATION ======================== */

static int init_dma_masks(struct my_dma_device *mydev)
{
    struct pci_dev *pdev = mydev->pdev;
    int ret;

    /* Try 64-bit DMA */
    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (!ret) {
        pci_info(pdev, "64-bit DMA enabled\n");
        return 0;
    }

    /* Fall back to 32-bit */
    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
    if (!ret) {
        pci_warn(pdev, "Using 32-bit DMA (bounce buffers may be used)\n");
        return 0;
    }

    pci_err(pdev, "Cannot set DMA mask!\n");
    return ret;
}

static int allocate_coherent_ring(struct my_dma_device *mydev)
{
    /* Ring of 64 descriptors, 64 bytes each */
    mydev->ring.size = 64 * 64;

    mydev->ring.vaddr = dma_alloc_coherent(&mydev->pdev->dev,
                                            mydev->ring.size,
                                            &mydev->ring.dma_addr,
                                            GFP_KERNEL);
    if (!mydev->ring.vaddr) {
        pci_err(mydev->pdev, "Failed to allocate coherent ring\n");
        return -ENOMEM;
    }

    memset(mydev->ring.vaddr, 0, mydev->ring.size);
    mydev->ring.head = 0;
    mydev->ring.tail = 0;

    pci_info(mydev->pdev, "Ring: virt=%p dma=0x%llx size=%zu\n",
             mydev->ring.vaddr, (u64)mydev->ring.dma_addr, mydev->ring.size);
    return 0;
}

static int allocate_data_buffers(struct my_dma_device *mydev)
{
    int i;

    for (i = 0; i < NUM_BUFFERS; i++) {
        struct dma_buffer *buf = &mydev->buffers[i];
        buf->size  = BUFFER_SIZE;
        buf->index = i;
        buf->in_use = false;

        buf->cpu_addr = kmalloc(buf->size, GFP_KERNEL | GFP_DMA);
        if (!buf->cpu_addr) {
            pci_err(mydev->pdev, "Buffer %d alloc failed\n", i);
            goto fail;
        }

        /* Pre-map for DMA. We use DMA_BIDIRECTIONAL since buffers
         * can be used for either direction. In production code,
         * you'd map/unmap per-transfer with the correct direction. */
        buf->dma_addr = dma_map_single(&mydev->pdev->dev,
                                        buf->cpu_addr,
                                        buf->size,
                                        DMA_BIDIRECTIONAL);
        if (dma_mapping_error(&mydev->pdev->dev, buf->dma_addr)) {
            kfree(buf->cpu_addr);
            buf->cpu_addr = NULL;
            goto fail;
        }
    }

    pci_info(mydev->pdev, "Allocated %d DMA buffers of %u bytes each\n",
             NUM_BUFFERS, BUFFER_SIZE);
    return 0;

fail:
    /* Clean up successfully allocated buffers */
    while (--i >= 0) {
        struct dma_buffer *buf = &mydev->buffers[i];
        dma_unmap_single(&mydev->pdev->dev, buf->dma_addr, buf->size,
                         DMA_BIDIRECTIONAL);
        kfree(buf->cpu_addr);
    }
    return -ENOMEM;
}

/* ======================== DMA OPERATIONS ======================== */

static int start_dma_transfer(struct my_dma_device *mydev,
                               dma_addr_t src, dma_addr_t dst, u32 length)
{
    unsigned long flags;

    spin_lock_irqsave(&mydev->lock, flags);

    if (mydev->transfer_in_progress) {
        spin_unlock_irqrestore(&mydev->lock, flags);
        return -EBUSY;
    }

    mydev->transfer_in_progress = true;
    reinit_completion(&mydev->transfer_done);

    /* Enable DMA done and error interrupts */
    reg_write(mydev, REG_IRQ_ENABLE, IRQ_DMA_DONE | IRQ_DMA_ERROR);

    /* Program source and destination addresses */
    reg_write64(mydev, REG_DMA_SRC_ADDR_LO, REG_DMA_SRC_ADDR_HI, src);
    reg_write64(mydev, REG_DMA_DST_ADDR_LO, REG_DMA_DST_ADDR_HI, dst);

    /* Program length */
    reg_write(mydev, REG_DMA_LENGTH, length);

    /*
     * Memory barrier: ensure all register writes are flushed
     * to device before starting transfer
     */
    wmb();

    /* Start the transfer */
    reg_write(mydev, REG_DMA_CTRL, DMA_CTRL_START);

    spin_unlock_irqrestore(&mydev->lock, flags);
    return 0;
}

/* ======================== INTERRUPT HANDLER ======================== */

static irqreturn_t my_dma_irq_handler(int irq, void *data)
{
    struct my_dma_device *mydev = data;
    u32 irq_status, dma_status;

    irq_status = reg_read(mydev, REG_IRQ_STATUS);
    if (!irq_status)
        return IRQ_NONE;  /* Not our interrupt */

    /* Clear the interrupt immediately */
    reg_write(mydev, REG_IRQ_CLEAR, irq_status);

    dma_status = reg_read(mydev, REG_DMA_STATUS);

    if (irq_status & IRQ_DMA_DONE) {
        u32 transferred = reg_read(mydev, REG_DMA_LENGTH);
        mydev->total_bytes_transferred += transferred;
        mydev->total_transfers++;

        pci_dbg(mydev->pdev, "DMA transfer complete: %u bytes\n", transferred);
    }

    if (irq_status & IRQ_DMA_ERROR) {
        mydev->total_errors++;
        pci_err(mydev->pdev, "DMA error! status=0x%x\n", dma_status);
    }

    mydev->transfer_in_progress = false;
    complete(&mydev->transfer_done);  /* wake up waiting task */

    return IRQ_HANDLED;
}

/* ======================== PCI PROBE/REMOVE ======================== */

static int my_dma_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct my_dma_device *mydev;
    int ret;

    pci_info(pdev, "Probing device %04x:%04x\n", pdev->vendor, pdev->device);

    /* Allocate driver private data */
    mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
    if (!mydev)
        return -ENOMEM;

    mydev->pdev = pdev;
    spin_lock_init(&mydev->lock);
    init_completion(&mydev->transfer_done);
    pci_set_drvdata(pdev, mydev);

    /* Enable PCI device */
    ret = pcim_enable_device(pdev);
    if (ret) {
        pci_err(pdev, "Cannot enable PCI device\n");
        return ret;
    }

    /* Enable bus mastering (required for DMA) */
    pci_set_master(pdev);

    /* Map BAR0 (register space) */
    ret = pcim_iomap_regions(pdev, BIT(0), "my_dma");
    if (ret) {
        pci_err(pdev, "Cannot map BAR0\n");
        return ret;
    }
    mydev->bar0 = pcim_iomap_table(pdev)[0];

    /* Setup DMA masks */
    ret = init_dma_masks(mydev);
    if (ret)
        return ret;

    /* Allocate coherent ring */
    ret = allocate_coherent_ring(mydev);
    if (ret)
        return ret;

    /* Allocate streaming buffers */
    ret = allocate_data_buffers(mydev);
    if (ret)
        goto free_ring;

    /* Setup MSI interrupt */
    ret = pci_alloc_irq_vectors(pdev, 1, 1, PCI_IRQ_MSI | PCI_IRQ_MSIX);
    if (ret < 0) {
        pci_err(pdev, "Cannot allocate IRQ vectors\n");
        goto free_buffers;
    }

    mydev->irq = pci_irq_vector(pdev, 0);
    ret = request_irq(mydev->irq, my_dma_irq_handler, 0, "my_dma", mydev);
    if (ret) {
        pci_err(pdev, "Cannot request IRQ %d\n", mydev->irq);
        goto free_vectors;
    }

    pci_info(pdev, "DMA driver loaded successfully\n");
    return 0;

free_vectors:
    pci_free_irq_vectors(pdev);
free_buffers:
    for (int i = 0; i < NUM_BUFFERS; i++) {
        struct dma_buffer *buf = &mydev->buffers[i];
        if (buf->cpu_addr) {
            dma_unmap_single(&pdev->dev, buf->dma_addr, buf->size,
                             DMA_BIDIRECTIONAL);
            kfree(buf->cpu_addr);
        }
    }
free_ring:
    dma_free_coherent(&pdev->dev, mydev->ring.size,
                      mydev->ring.vaddr, mydev->ring.dma_addr);
    return ret;
}

static void my_dma_remove(struct pci_dev *pdev)
{
    struct my_dma_device *mydev = pci_get_drvdata(pdev);
    int i;

    pci_info(pdev, "Removing driver. Stats: %llu bytes, %u transfers, %u errors\n",
             mydev->total_bytes_transferred,
             mydev->total_transfers,
             mydev->total_errors);

    /* Disable interrupts first */
    reg_write(mydev, REG_IRQ_ENABLE, 0);

    /* Wait for any in-progress transfer */
    if (mydev->transfer_in_progress)
        wait_for_completion_timeout(&mydev->transfer_done,
                                    msecs_to_jiffies(1000));

    free_irq(mydev->irq, mydev);
    pci_free_irq_vectors(pdev);

    /* Free streaming buffers */
    for (i = 0; i < NUM_BUFFERS; i++) {
        struct dma_buffer *buf = &mydev->buffers[i];
        if (buf->cpu_addr) {
            dma_unmap_single(&pdev->dev, buf->dma_addr, buf->size,
                             DMA_BIDIRECTIONAL);
            kfree(buf->cpu_addr);
        }
    }

    /* Free coherent ring */
    dma_free_coherent(&pdev->dev, mydev->ring.size,
                      mydev->ring.vaddr, mydev->ring.dma_addr);
}

static const struct pci_device_id my_dma_ids[] = {
    { PCI_DEVICE(0x1234, 0x5678) },  /* Replace with real vendor/device IDs */
    { 0, }
};
MODULE_DEVICE_TABLE(pci, my_dma_ids);

static struct pci_driver my_dma_driver = {
    .name     = "my_dma",
    .id_table = my_dma_ids,
    .probe    = my_dma_probe,
    .remove   = my_dma_remove,
};

module_pci_driver(my_dma_driver);
```

---

## 11. DMA in Rust (Linux Kernel)

### 11.1 Rust in the Linux Kernel - Overview

```
RUST IN LINUX KERNEL
=====================

Since Linux 6.1, Rust is an officially supported language for
writing kernel modules. The rust/ directory in the kernel tree
contains Rust abstractions over kernel C APIs.

Key crates:
  kernel::     - Core kernel abstractions
  alloc::      - Kernel-safe alloc (kmalloc etc.)
  core::       - No-std core library

DMA in Rust:
  - kernel::dma module (in progress, some APIs available)
  - Wraps C dma_alloc_coherent, dma_map_*, etc.
  - Provides ownership semantics for DMA buffers (RAII)
  - Compile-time prevention of use-after-free, double-unmap
```

### 11.2 Rust DMA Abstractions

```rust
// rust/kernel/dma.rs equivalent abstraction
// This shows how DMA safety is modeled in Rust

use kernel::{
    bindings,
    device::Device,
    error::{Error, Result},
    types::ARef,
};
use core::{
    marker::PhantomData,
    ops::{Deref, DerefMut},
    ptr::NonNull,
};

/// Marker types for DMA direction (zero-size types)
pub struct ToDevice;
pub struct FromDevice;
pub struct Bidirectional;

/// Sealed trait for DMA direction
pub trait DmaDirection: private::Sealed {
    const DIRECTION: u32;
}

mod private {
    pub trait Sealed {}
    impl Sealed for super::ToDevice {}
    impl Sealed for super::FromDevice {}
    impl Sealed for super::Bidirectional {}
}

impl DmaDirection for ToDevice {
    const DIRECTION: u32 = bindings::dma_data_direction_DMA_TO_DEVICE;
}

impl DmaDirection for FromDevice {
    const DIRECTION: u32 = bindings::dma_data_direction_DMA_FROM_DEVICE;
}

impl DmaDirection for Bidirectional {
    const DIRECTION: u32 = bindings::dma_data_direction_DMA_BIDIRECTIONAL;
}

/// A coherent DMA allocation.
///
/// This is the Rust equivalent of dma_alloc_coherent().
/// The memory is automatically freed when this object is dropped.
/// 
/// SAFETY guarantee: You cannot accidentally free it twice (Drop runs once).
/// SAFETY guarantee: You cannot use it after free (ownership moved or dropped).
pub struct CoherentDmaBuffer<T> {
    /// CPU-accessible pointer to the buffer
    cpu_ptr: NonNull<T>,
    /// DMA/bus address for the device
    dma_handle: bindings::dma_addr_t,
    /// Number of elements
    count: usize,
    /// Reference to the device (ensures device outlives buffer)
    dev: ARef<Device>,
}

impl<T> CoherentDmaBuffer<T> {
    /// Allocate coherent DMA memory for `count` items of type T.
    ///
    /// # Errors
    /// Returns `ENOMEM` if allocation fails.
    pub fn new(dev: &Device, count: usize) -> Result<Self> {
        let size = count
            .checked_mul(core::mem::size_of::<T>())
            .ok_or(Error::EINVAL)?;

        let mut dma_handle: bindings::dma_addr_t = 0;

        // SAFETY: `dev` is a valid device, `dma_handle` will be filled,
        // size is non-zero (enforced by count > 0 check below).
        let cpu_ptr = unsafe {
            bindings::dma_alloc_coherent(
                dev.as_raw(),
                size,
                &mut dma_handle,
                bindings::GFP_KERNEL,
            )
        };

        // dma_alloc_coherent returns NULL on failure
        let cpu_ptr = NonNull::new(cpu_ptr as *mut T).ok_or(Error::ENOMEM)?;

        Ok(CoherentDmaBuffer {
            cpu_ptr,
            dma_handle,
            count,
            dev: dev.into(),
        })
    }

    /// Get the DMA address (bus address) to give to the device.
    pub fn dma_addr(&self) -> bindings::dma_addr_t {
        self.dma_handle
    }

    /// Get the number of elements.
    pub fn len(&self) -> usize {
        self.count
    }

    fn byte_size(&self) -> usize {
        self.count * core::mem::size_of::<T>()
    }
}

impl<T> Deref for CoherentDmaBuffer<T> {
    type Target = [T];

    fn deref(&self) -> &[T] {
        // SAFETY: cpu_ptr is valid and points to `count` initialized elements.
        unsafe { core::slice::from_raw_parts(self.cpu_ptr.as_ptr(), self.count) }
    }
}

impl<T> DerefMut for CoherentDmaBuffer<T> {
    fn deref_mut(&mut self) -> &mut [T] {
        // SAFETY: We have exclusive access (&mut self)
        unsafe { core::slice::from_raw_parts_mut(self.cpu_ptr.as_ptr(), self.count) }
    }
}

impl<T> Drop for CoherentDmaBuffer<T> {
    fn drop(&mut self) {
        // SAFETY: This is called exactly once (Rust Drop guarantee).
        // cpu_ptr and dma_handle were obtained from dma_alloc_coherent.
        unsafe {
            bindings::dma_free_coherent(
                self.dev.as_raw(),
                self.byte_size(),
                self.cpu_ptr.as_ptr() as *mut core::ffi::c_void,
                self.dma_handle,
            );
        }
    }
}

/// A streaming DMA mapping.
///
/// Wraps dma_map_single(). The mapping is released on drop.
/// Direction is encoded in the type: StreamingDmaMap<ToDevice>, etc.
///
/// INVARIANT: While this mapping exists, the CPU must not access
/// the underlying buffer (enforced by borrowing the cpu_addr).
pub struct StreamingDmaMap<'a, T, Dir: DmaDirection> {
    dma_addr: bindings::dma_addr_t,
    len: usize,
    dev: &'a Device,
    /// Phantom data: we "own" the CPU buffer for the duration
    _cpu_buf: PhantomData<&'a mut T>,
    _dir: PhantomData<Dir>,
}

impl<'a, T, Dir: DmaDirection> StreamingDmaMap<'a, T, Dir> {
    /// Create a DMA mapping for the given buffer.
    ///
    /// After this call, the CPU must not access `buf` until the
    /// mapping is dropped.
    pub fn new(dev: &'a Device, buf: &'a mut [T]) -> Result<Self> {
        let len = buf.len() * core::mem::size_of::<T>();

        // SAFETY: buf is a valid slice, len is correct.
        let dma_addr = unsafe {
            bindings::dma_map_single(
                dev.as_raw(),
                buf.as_mut_ptr() as *mut core::ffi::c_void,
                len,
                Dir::DIRECTION,
            )
        };

        // Check for mapping error
        // SAFETY: dma_addr was returned by dma_map_single
        if unsafe { bindings::dma_mapping_error(dev.as_raw(), dma_addr) } != 0 {
            return Err(Error::ENOMEM);
        }

        Ok(StreamingDmaMap {
            dma_addr,
            len,
            dev,
            _cpu_buf: PhantomData,
            _dir: PhantomData,
        })
    }

    /// Get the DMA address to give to the device.
    pub fn dma_addr(&self) -> bindings::dma_addr_t {
        self.dma_addr
    }
}

impl<'a, T, Dir: DmaDirection> Drop for StreamingDmaMap<'a, T, Dir> {
    fn drop(&mut self) {
        // SAFETY: dma_addr was obtained from dma_map_single, called once.
        unsafe {
            bindings::dma_unmap_single(
                self.dev.as_raw(),
                self.dma_addr,
                self.len,
                Dir::DIRECTION,
            );
        }
    }
}
```

### 11.3 Rust DMA Driver Module

```rust
// my_dma_driver.rs - Rust PCI DMA driver
// Demonstrates Rust-idiomatic DMA programming

use kernel::{
    bindings,
    device::Device,
    error::Result,
    pci,
    prelude::*,
    sync::{Arc, Mutex},
};

module! {
    type: MyDmaDriver,
    name: "my_dma_rust",
    author: "Systems Programmer",
    description: "Example Rust PCI DMA Driver",
    license: "GPL",
}

/// Our device's register offsets
const REG_DMA_CTRL: usize = 0x00;
const REG_DMA_SRC_LO: usize = 0x04;
const REG_DMA_SRC_HI: usize = 0x08;
const REG_DMA_DST_LO: usize = 0x0C;
const REG_DMA_DST_HI: usize = 0x10;
const REG_DMA_LEN: usize = 0x14;
const REG_STATUS: usize = 0x18;

/// A TX descriptor (must be repr(C) for device compatibility)
#[repr(C)]
struct TxDescriptor {
    buffer_addr: u64,  // little-endian bus address
    length: u32,       // little-endian length
    flags: u32,        // control flags
}

/// Driver state, protected by Mutex
struct MyDmaState {
    /// Coherent ring buffer for descriptors
    /// CoherentDmaBuffer<TxDescriptor> ensures:
    ///   - Freed on drop
    ///   - Cannot be used after free
    ///   - Type-safe access (slice of TxDescriptor)
    ring: CoherentDmaBuffer<TxDescriptor>,
    total_transfers: u64,
}

struct MyDmaDriver {
    state: Mutex<MyDmaState>,
}

impl pci::Driver for MyDmaDriver {
    type Data = Arc<MyDmaDriver>;

    fn probe(dev: &mut pci::Device, _id: &pci::DeviceId) -> Result<Arc<Self>> {
        dev_info!(dev, "Probing Rust DMA driver\n");

        // Enable device and bus mastering
        dev.enable_device_mem()?;
        dev.set_master();

        // Set DMA mask (try 64-bit, fall back to 32-bit)
        if dev.set_dma_mask(bindings::DMA_BIT_MASK(64)).is_err() {
            dev.set_dma_mask(bindings::DMA_BIT_MASK(32))
               .map_err(|_| Error::EINVAL)?;
        }
        dev.set_coherent_dma_mask(bindings::DMA_BIT_MASK(64))
           .or_else(|_| dev.set_coherent_dma_mask(bindings::DMA_BIT_MASK(32)))
           .map_err(|_| Error::EINVAL)?;

        // Allocate coherent descriptor ring
        // 64 descriptors — Rust ensures correct type and cleanup!
        let ring: CoherentDmaBuffer<TxDescriptor> =
            CoherentDmaBuffer::new(dev.as_ref(), 64)?;

        dev_info!(dev, "Ring DMA addr: 0x{:016x}\n", ring.dma_addr());

        let driver = Arc::new(MyDmaDriver {
            state: Mutex::new(MyDmaState {
                ring,
                total_transfers: 0,
            }),
        });

        Ok(driver)
    }

    fn remove(dev: &mut pci::Device) {
        dev_info!(dev, "Removing Rust DMA driver\n");
        // All resources freed automatically via Drop!
    }
}

/// Demonstrates streaming DMA with Rust's borrow checker enforcing correctness
fn do_dma_transfer(dev: &Device, data: &mut [u8]) -> Result<u64> {
    // Create streaming DMA mapping.
    // While `mapping` exists, `data` is borrowed mutably —
    // COMPILER prevents you from accessing `data` during DMA!
    let mapping = StreamingDmaMap::<u8, ToDevice>::new(dev, data)?;

    let dma_addr = mapping.dma_addr();
    dev_dbg!(dev, "DMA mapping: 0x{:016x}\n", dma_addr);

    // Program device registers with dma_addr...
    // (device does DMA here)

    // mapping is dropped here → dma_unmap_single called automatically
    // AFTER drop, `data` is accessible again (borrow released)
    drop(mapping);

    // Now safe to read data
    pr_debug!("First byte after DMA: {}\n", data[0]);

    Ok(dma_addr)
}
```

---

## 12. RDMA - Remote Direct Memory Access

### 12.1 What Problem Does RDMA Solve?

Traditional network communication is slow because it involves the kernel:

```
TRADITIONAL TCP/IP - The Slow Path
====================================

  APPLICATION A (machine 1)           APPLICATION B (machine 2)
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │ App buffer (user space) │         │ App buffer (user space) │
  └────────────┬────────────┘         └────────────▲────────────┘
               │ (1) write()                       │ (8) read()
               ▼                                   │
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │  KERNEL TCP/IP Stack    │         │  KERNEL TCP/IP Stack    │
  │  Socket buffer (copy1)  │         │  Socket buffer (copy2)  │
  └────────────┬────────────┘         └────────────▲────────────┘
               │ (2) TCP segmentation               │ (7) TCP reassembly
               │ (3) IP fragmentation               │
               ▼                                   │
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │  NIC Driver             │         │  NIC Driver             │
  │  TX DMA to NIC          │         │  RX DMA from NIC        │
  └────────────┬────────────┘         └────────────▲────────────┘
               │ (4) DMA + wire                    │ (5) wire + DMA
               └──────────────► NETWORK ───────────┘
                                                   (6) interrupt

PROBLEMS:
  1. DATA COPIES:
     App buffer → kernel socket buf → NIC tx buffer (copy #1)
     NIC rx buffer → kernel socket buf → App buffer (copy #2)
     Total: 4 copies!

  2. CONTEXT SWITCHES:
     App → kernel (for send/recv syscalls) → app
     Each switch: ~1-3 µs overhead

  3. CPU USAGE:
     TCP/IP processing: checksums, ACKs, retransmit timers
     At 100 Gbps: TCP/IP can consume entire CPU cores!

  4. LATENCY:
     Best case TCP latency: ~5-10 µs
     Datacenter needs: <1 µs for low-latency applications
```

### 12.2 RDMA - The Solution

```
RDMA - ZERO-COPY KERNEL-BYPASS NETWORKING
==========================================

  APPLICATION A (machine 1)           APPLICATION B (machine 2)
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │ App buffer (user space) │         │ App buffer (user space) │
  │ [PINNED & REGISTERED]   │         │ [PINNED & REGISTERED]   │
  └────────────┬────────────┘         └────────────▲────────────┘
               │                                   │
               │ RDMA WRITE: "copy data from       │
               │  my buffer directly to            │
               │  remote buffer" ──────────────────┘
               │
  ┌────────────▼────────────┐         ┌─────────────────────────┐
  │  RDMA NIC (RNIC)        │ ──────► │  RDMA NIC (RNIC)        │
  │  (handles everything)   │   wire  │  (handles everything)   │
  └─────────────────────────┘         └─────────────────────────┘

PROPERTIES:
  ✓ ZERO COPY: Data goes directly from app buffer to wire to remote app buffer
  ✓ KERNEL BYPASS: Kernel not involved in data path after setup
  ✓ CPU BYPASS: After issuing work request, CPU does nothing
  ✓ ZERO CONTEXT SWITCHES: User space ↔ NIC directly
  ✓ LATENCY: < 1 µs (vs 5-10 µs for TCP)
  ✓ THROUGHPUT: Up to 400 Gbps with modern HDR InfiniBand

RDMA vs TCP Latency:
  TCP (software):     5-20 µs round-trip
  RDMA (InfiniBand):  0.5-2 µs round-trip (10-20x better!)
```

---

## 13. RDMA Architecture & Key Concepts

### 13.1 Memory Registration - The Foundation

Before RDMA can access memory, it must be **registered**. This is the most critical concept in RDMA.

```
MEMORY REGISTRATION
====================

WHY register memory?
  1. Pin pages in physical memory (prevent OS from swapping them out)
  2. Create IOMMU mappings for the RNIC (DMA access)
  3. Associate access permissions (local read, remote read, remote write)
  4. Receive a key pair: L_Key and R_Key

WHAT happens during registration:
  ┌─────────────────────────────────────────────────────────────┐
  │ User process: ibv_reg_mr(pd, buf, size, access_flags)       │
  │   → syscall to kernel                                       │
  │   → pin all pages (get_user_pages, page_lock)               │
  │   → create IOMMU mappings (RNIC can now DMA to these pages) │
  │   → store page table in MR (Memory Region) descriptor       │
  │   → return MR with lkey (local key) and rkey (remote key)  │
  └─────────────────────────────────────────────────────────────┘

WHAT are L_Key and R_Key?
  L_Key (Local Key): 32-bit token used in local work requests
  R_Key (Remote Key): 32-bit token given to remote machines
                      Remote machine uses R_Key to access your memory!

Security model:
  Remote machine A wants to read your buffer:
    → You give them: (address of buffer, size, R_Key)
    → RNIC validates R_Key on every RDMA access
    → Invalid R_Key → hardware-level access denied
    → R_Key is cryptographically unpredictable (random 24 bits)
```

### 13.2 Protection Domain

```
PROTECTION DOMAIN (PD)
=======================

A container that groups resources together for access control.
All resources (MR, QP, CQ, SRQ) belong to a PD.
Resources in different PDs cannot communicate.

Think of PD as a "namespace" or "security context":
  ┌──────────────────────────────────────────────┐
  │ Protection Domain 0 (application A)          │
  │   Memory Region 0: buf_A, lkey=100, rkey=200 │
  │   Queue Pair 0: for sending                  │
  │   Completion Queue 0                         │
  └──────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ Protection Domain 1 (application B)          │
  │   Memory Region 1: buf_B, lkey=101, rkey=201 │
  │   Queue Pair 1: for sending                  │
  │   Completion Queue 1                         │
  └──────────────────────────────────────────────┘

  App A's QP cannot access App B's MR (different PD) even on same machine.
```

### 13.3 Queue Pairs (QP) - The Communication Endpoint

```
QUEUE PAIR (QP)
================

A QP is THE fundamental communication endpoint in RDMA.
It has two queues:

  ┌─────────────────────────────────────────────────────────────┐
  │                    QUEUE PAIR (QP)                          │
  │                                                             │
  │  ┌────────────────────────────────────┐                     │
  │  │ Send Queue (SQ)                   │                     │
  │  │  WR → WR → WR → WR → WR →        │◄── CPU posts WRs    │
  │  │  [SEND][RDMA_WRITE][RDMA_READ]    │                     │
  │  └────────────────────────────────────┘    RNIC processes  │
  │                                            ↓               │
  │  ┌────────────────────────────────────┐                     │
  │  │ Receive Queue (RQ)                │                     │
  │  │  WR → WR → WR → WR →             │◄── CPU posts Recv WRs│
  │  │  [posted receive buffers]         │   (only for SEND op)│
  │  └────────────────────────────────────┘                     │
  └─────────────────────────────────────────────────────────────┘

QP STATES (state machine):
  RESET → INIT → RTR (Ready to Receive) → RTS (Ready to Send) → ERROR
  
  Must transition through these states before use:
  ibv_modify_qp(qp, INIT) → ibv_modify_qp(qp, RTR) → ibv_modify_qp(qp, RTS)

QP TYPES:
  RC (Reliable Connected):     Connected 1:1, guaranteed delivery, ordered
  UC (Unreliable Connected):   Connected 1:1, no guarantee
  UD (Unreliable Datagram):    1:many, like UDP
  XRC (Extended RC):           Many:1, scalability for HPC
```

### 13.4 Completion Queue (CQ)

```
COMPLETION QUEUE (CQ)
======================

When RDMA operation completes, RNIC posts a Work Completion (WC) to the CQ.
CQ is shared: multiple QPs can share one CQ.

Flow:
  CPU posts Work Request → RNIC executes → RNIC posts WC to CQ → CPU polls CQ

  ┌────────────────────────────────────────────────────────────────┐
  │                 COMPLETION QUEUE (CQ)                          │
  │                                                                │
  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
  │  │ WC 0 │ │ WC 1 │ │ WC 2 │ │ WC 3 │ │      │               │
  │  │SEND  │ │RDMA  │ │RECV  │ │RDMA  │ │(empty│               │
  │  │OK    │ │WRITE │ │OK    │ │READ  │ │)     │               │
  │  │QP#0  │ │ERROR │ │QP#1  │ │OK    │ │      │               │
  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘               │
  │                                                                │
  │  ibv_poll_cq() → dequeues completed WCs                       │
  └────────────────────────────────────────────────────────────────┘

CQ NOTIFICATION MODES:
  1. POLLING (busy-wait): while (ibv_poll_cq(...) == 0) {}
     - Lowest latency (no interrupt overhead)
     - Wastes CPU
  
  2. EVENT-DRIVEN (interrupt): ibv_req_notify_cq() + wait on fd
     - Higher latency (interrupt overhead)
     - CPU-efficient for low-rate transfers
  
  3. HYBRID: Poll for N microseconds, then switch to event
     - Best of both worlds
```

### 13.5 Work Requests and Operations

```
RDMA OPERATIONS
================

┌──────────────────────────────────────────────────────────────────┐
│ 1. SEND / RECEIVE                                                │
│    ─────────────                                                 │
│    Two-sided: both sender and receiver must be involved          │
│    Sender posts SEND WR                                          │
│    Receiver posts RECV WR (buffer where data will land)          │
│    Use for: control messages, small data, connection setup       │
│                                                                  │
│    Machine A: post_send(data)                                    │
│    Machine B: post_recv(buf) ← must be posted BEFORE send!      │
│    RNIC A → wire → RNIC B → data lands in buf                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 2. RDMA WRITE                                                    │
│    ──────────                                                    │
│    One-sided: receiver is NOT involved at all!                   │
│    Initiator writes directly to remote memory                    │
│    Remote CPU doesn't know it happened (no interrupt)!           │
│    Need: remote address + R_Key (exchanged out-of-band)          │
│    Use for: bulk data transfer, storage writes                   │
│                                                                  │
│    Machine A: post_rdma_write(src, remote_addr, remote_rkey)    │
│    RNIC A reads from local buffer, sends to remote RNIC B        │
│    RNIC B writes directly to remote_addr (verified by rkey)      │
│    Machine B: CPU has no idea! (just sees data appear in memory) │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 3. RDMA READ                                                     │
│    ─────────                                                     │
│    One-sided: initiator reads from remote memory                 │
│    Remote CPU is NOT involved                                    │
│    Need: remote address + R_Key                                  │
│    Higher latency than WRITE (requires round trip)               │
│    Use for: fetching metadata, scattered reads                   │
│                                                                  │
│    Machine A: post_rdma_read(local_dst, remote_addr, remote_rkey)│
│    RNIC A sends read request to RNIC B                           │
│    RNIC B reads from remote_addr, sends data back to RNIC A      │
│    Data lands in local_dst on Machine A                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 4. ATOMIC OPERATIONS                                             │
│    ─────────────────                                             │
│    Fetch-and-Add: atomically add value to remote 64-bit int      │
│    Compare-and-Swap: CAS on remote 64-bit int                    │
│    Use for: distributed counters, lock-free distributed algos    │
│    Only supported on RC QPs                                      │
└──────────────────────────────────────────────────────────────────┘

COMPARISON TABLE:
  ┌────────────────┬────────────────┬────────────────┬────────────┐
  │ Operation      │ CPU involved?  │ Completion     │ Latency    │
  │                │ (both sides)   │ notification   │            │
  ├────────────────┼────────────────┼────────────────┼────────────┤
  │ SEND           │ YES (both)     │ Both sides     │ Lowest     │
  │ RECV           │ YES (receiver) │ CQ on receiver │            │
  ├────────────────┼────────────────┼────────────────┼────────────┤
  │ RDMA WRITE     │ NO (receiver)  │ Sender only    │ Low        │
  │ RDMA WRITE+IMM │ YES (receiver) │ CQ on receiver │ Low        │
  ├────────────────┼────────────────┼────────────────┼────────────┤
  │ RDMA READ      │ NO (target)    │ Initiator only │ Medium     │
  ├────────────────┼────────────────┼────────────────┼────────────┤
  │ ATOMIC (FA/CAS)│ NO (target)    │ Initiator only │ Medium     │
  └────────────────┴────────────────┴────────────────┴────────────┘
```

---

## 14. RDMA Technologies: IB, RoCE, iWARP

### 14.1 InfiniBand (IB)

```
INFINIBAND (IB)
================

The original RDMA technology. Custom physical layer (not Ethernet).

SPEEDS (per port):
  SDR:   2.5 Gbps  (Single Data Rate, 2001)
  DDR:   5 Gbps    (Double Data Rate)
  QDR:   10 Gbps   (Quad Data Rate)
  FDR:   14 Gbps   (Fourteen Data Rate)
  EDR:   25 Gbps   (Enhanced Data Rate)
  HDR:   50 Gbps   (High Data Rate)
  NDR:   100 Gbps  (Next Data Rate)
  XDR:   200 Gbps  (Extended Data Rate, upcoming)

TOPOLOGY:
  ┌──────┐    ┌──────┐    ┌──────┐
  │ HCA  │    │ HCA  │    │ HCA  │  HCA = Host Channel Adapter (the NIC)
  └──┬───┘    └──┬───┘    └──┬───┘
     │           │            │
  ┌──▼───────────▼────────────▼───────────────┐
  │          InfiniBand Switch                │
  │  (credit-based flow control, lossless!)   │
  └───────────────────────────────────────────┘

KEY FEATURES:
  - Lossless fabric (credit-based flow control)
  - Very low latency: 0.5-1 µs
  - Subnet Manager manages network topology
  - Uses LIDs (Local Identifiers) for addressing
  - Used in: HPC clusters, supercomputers, storage systems

Vendors: Mellanox (now NVIDIA), Intel (exiting market)
```

### 14.2 RoCE (RDMA over Converged Ethernet)

```
ROCE - RDMA OVER CONVERGED ETHERNET
=====================================

RDMA semantics over Ethernet physical layer.
No need for InfiniBand hardware! Use existing switches.

VERSIONS:
  RoCEv1: L2 only (same Ethernet broadcast domain required)
           Ethertype 0x8915
           Not routable across subnets

  RoCEv2: L3 (UDP/IP encapsulation, port 4791)
           Routable across subnets!
           ECMP (Equal Cost MultiPath) support
           The modern standard

RoCEv2 PACKET FORMAT:
  ┌──────────────────────────────────────────────────────────────┐
  │ Ethernet Header (14 bytes)                                   │
  ├──────────────────────────────────────────────────────────────┤
  │ IPv4/IPv6 Header (20/40 bytes)                               │
  ├──────────────────────────────────────────────────────────────┤
  │ UDP Header (8 bytes) - dest port 4791                        │
  ├──────────────────────────────────────────────────────────────┤
  │ IB Global Routing Header (GRH) - optional                    │
  ├──────────────────────────────────────────────────────────────┤
  │ IB Base Transport Header (BTH) - QP number, opcode, etc.     │
  ├──────────────────────────────────────────────────────────────┤
  │ IB Payload (RDMA data)                                       │
  ├──────────────────────────────────────────────────────────────┤
  │ ICRC (Invariant CRC - 4 bytes)                               │
  └──────────────────────────────────────────────────────────────┘

REQUIREMENT: Lossless Ethernet!
  Ethernet normally drops packets → breaks RDMA reliability!
  Must enable: PFC (Priority Flow Control) or ECN (Explicit Congestion Notification)
  
  PFC: Per-priority pause frames (pause a priority class if receiver overwhelmed)
  ECN: Mark packets before dropping, sender slows down (DCQCN algorithm)

ADVANTAGE: Use commodity Ethernet switches (cheaper than IB switches)
DISADVANTAGE: Requires careful network configuration (PFC tuning)

Vendors: NVIDIA/Mellanox ConnectX, Broadcom, Marvell/Cavium
```

### 14.3 iWARP

```
iWARP - RDMA OVER TCP/IP
=========================

RDMA using TCP/IP as transport.
  
Stack:
  ┌─────────────────────┐
  │ RDMA (verbs)        │
  ├─────────────────────┤
  │ MPA (Marker PDU     │  MPA = Marker-based PDU Alignment
  │      Alignment)     │
  ├─────────────────────┤
  │ DDP (Direct Data    │  DDP = Direct Data Placement
  │      Placement)     │
  ├─────────────────────┤
  │ RDMAP (RDMA         │  RDMAP = RDMA Protocol
  │        Protocol)    │
  ├─────────────────────┤
  │ TCP/IP              │
  └─────────────────────┘

ADVANTAGE: Works over regular Ethernet, routable, no lossless req.
ADVANTAGE: Works through NAT (uses TCP)
DISADVANTAGE: Higher latency than IB or RoCE (TCP overhead)
DISADVANTAGE: TCP head-of-line blocking

Vendors: Chelsio, Intel (X722 NIC)

COMPARISON TABLE:
  ┌─────────────┬────────────┬────────────┬──────────────────────┐
  │ Technology  │ Transport  │ Latency    │ Requirement          │
  ├─────────────┼────────────┼────────────┼──────────────────────┤
  │ InfiniBand  │ IB fabric  │ 0.5-1 µs   │ IB switches + HCAs  │
  │ RoCEv2      │ UDP/IP/ETH │ 1-3 µs     │ Lossless Ethernet    │
  │ iWARP       │ TCP/IP/ETH │ 3-10 µs    │ Regular Ethernet     │
  └─────────────┴────────────┴────────────┴──────────────────────┘
```

---

## 15. Linux RDMA Stack Deep Dive

### 15.1 Architecture Overview

```
LINUX RDMA SOFTWARE STACK
===========================

  ┌───────────────────────────────────────────────────────────────────┐
  │ User Space Applications                                           │
  │   (MPI, databases, distributed storage, AI training frameworks)   │
  └───────────────────────────────────┬───────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼───────────────────────────────┐
  │ libibverbs (user-space RDMA verbs library)                        │
  │   ibv_open_device(), ibv_alloc_pd(), ibv_reg_mr(), ibv_create_qp()│
  │   ibv_post_send(), ibv_poll_cq(), etc.                            │
  └───────────────────────────────────┬───────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼───────────────────────────────┐
  │ Provider libraries (vendor-specific user-space drivers)           │
  │   libmlx5 (NVIDIA/Mellanox ConnectX-5/6/7)                       │
  │   libmlx4 (NVIDIA/Mellanox ConnectX-3)                           │
  │   librxe  (Soft RoCE, software implementation)                   │
  │   libcxgb4 (Chelsio iWARP)                                       │
  └───────────────────────────────────┬───────────────────────────────┘
                                      │ ioctl / mmap (for doorbell rings)
  ═══════════════════════════════════════════════════════════════════════
  KERNEL SPACE                         │
  ┌───────────────────────────────────▼───────────────────────────────┐
  │ IB Core (drivers/infiniband/core/)                                │
  │   ib_register_device(), ib_alloc_pd(), ib_create_qp()             │
  │   ib_post_send(), ib_poll_cq()                                    │
  │   /dev/infiniband/uverbs0 (char device for user access)           │
  └───────────────────────────────────┬───────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼───────────────────────────────┐
  │ Kernel Verbs Providers (HW drivers, drivers/infiniband/hw/)       │
  │   mlx5_core (ConnectX-5/6/7)                                     │
  │   mlx4_core (ConnectX-3/4)                                       │
  │   rxe (Soft-RoCE, pure software)                                 │
  │   cxgb4 (Chelsio iWARP)                                          │
  │   hfi1 (Intel OPA)                                               │
  └───────────────────────────────────┬───────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼───────────────────────────────┐
  │ Hardware (RNIC)                                                   │
  │   NVIDIA ConnectX-7 / InfiniBand HDR / RoCEv2                    │
  └───────────────────────────────────────────────────────────────────┘

KEY INSIGHT: The data path (post_send, poll_cq) in libibverbs calls
directly into provider library code → mmaps doorbell registers →
NO KERNEL SYSCALL for data path operations!
This is the "kernel bypass" that makes RDMA fast.
```

### 15.2 Key Kernel Source Directories

```
LINUX RDMA KERNEL SOURCE LAYOUT
=================================

drivers/infiniband/
  ├── core/              IB core subsystem
  │   ├── device.c       Device registration/management
  │   ├── verbs.c        Core verbs (create_qp, reg_mr, etc.)
  │   ├── uverbs_main.c  User-kernel interface (/dev/uverbs0)
  │   ├── uverbs_cmd.c   User verbs command processing
  │   ├── mr.c           Memory region management
  │   ├── cq.c           Completion queue management
  │   ├── qp.c           Queue pair management
  │   ├── addr.c         Address resolution
  │   └── cm.c           Connection Manager
  │
  ├── hw/                Hardware drivers
  │   ├── mlx5/          NVIDIA ConnectX-5/6/7
  │   │   ├── main.c     Driver initialization
  │   │   ├── qp.c       QP operations
  │   │   ├── mr.c       Memory region
  │   │   └── cq.c       Completion queue
  │   ├── mlx4/          Mellanox ConnectX-3/4
  │   ├── hfi1/          Intel OPA (Omni-Path)
  │   └── rxe/           Software RoCE (Soft-RoCE)
  │       ├── rxe.c      Main RxE driver
  │       ├── rxe_qp.c   QP state machine
  │       ├── rxe_mr.c   Memory regions
  │       └── rxe_net.c  UDP/Ethernet transport
  │
  └── sw/                Software implementations
      ├── rdmavt/        RDMA Verbs Transport (common SW layer)
      └── siw/           Software iWARP

rdma-core (user space, separate repo):
  providers/
    ├── mlx5/            libmlx5
    ├── rxe/             librxe (Soft-RoCE user driver)
    └── cxgb4/           libcxgb4
```

### 15.3 RDMA CM - Connection Manager

```
RDMA CONNECTION MANAGER (CM)
=============================

Just like TCP has a 3-way handshake for connection setup,
RDMA needs a way to exchange QP numbers and memory info.
RDMA CM provides this.

RDMA CM Connection Flow (Server side):
  rdma_create_event_channel()
  rdma_create_id()
  rdma_bind_addr(local_addr, port)
  rdma_listen()
  ← wait for RDMA_CM_EVENT_CONNECT_REQUEST
  rdma_create_qp() ← create QP for this connection
  rdma_accept()
  ← wait for RDMA_CM_EVENT_ESTABLISHED
  [transfer data]
  rdma_disconnect()

RDMA CM Connection Flow (Client side):
  rdma_create_event_channel()
  rdma_create_id()
  rdma_resolve_addr(server_addr)   ← ARP-like resolution
  ← wait for RDMA_CM_EVENT_ADDR_RESOLVED
  rdma_resolve_route()             ← find path to server
  ← wait for RDMA_CM_EVENT_ROUTE_RESOLVED
  rdma_create_qp()
  rdma_connect()
  ← wait for RDMA_CM_EVENT_ESTABLISHED
  [transfer data]
  rdma_disconnect()

CM PRIVATE DATA:
  During connect/accept, you can pass up to 56 bytes of
  "private data" - use this to exchange R_Keys!
```

---

## 16. RDMA Verbs Programming in C

### 16.1 Complete RDMA Client-Server Example

```c
/*
 * rdma_server.c - RDMA server (receiver/target)
 *
 * This server:
 *   1. Creates a QP and registers a memory buffer
 *   2. Accepts connection from client
 *   3. Sends its R_Key and buffer address to client
 *   4. Client can then RDMA WRITE directly into this buffer
 *   5. Server polls and processes data
 *
 * Compile: gcc -o rdma_server rdma_server.c -lrdmacm -libverbs
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <rdma/rdma_cma.h>
#include <infiniband/verbs.h>

#define PORT            18515
#define BUFFER_SIZE     (4 * 1024 * 1024)  /* 4 MB */
#define CQ_DEPTH        64
#define QP_SEND_DEPTH   64
#define QP_RECV_DEPTH   64

/* Structure exchanged between client and server via CM private data */
struct rdma_info {
    uint64_t addr;    /* Buffer virtual address */
    uint32_t rkey;    /* Remote key for RDMA access */
    uint32_t size;    /* Buffer size */
};

struct rdma_server_ctx {
    struct rdma_event_channel *cm_channel;
    struct rdma_cm_id         *listen_id;
    struct rdma_cm_id         *conn_id;
    struct ibv_context        *ibv_ctx;
    struct ibv_pd             *pd;             /* Protection Domain */
    struct ibv_cq             *cq;             /* Completion Queue */
    struct ibv_qp             *qp;             /* Queue Pair */
    struct ibv_mr             *mr;             /* Memory Region */
    char                      *buf;            /* Our data buffer */
    struct rdma_info           local_info;     /* Our MR info to share */
};

static int create_resources(struct rdma_server_ctx *ctx)
{
    struct ibv_qp_init_attr qp_attr = {};
    int ret;

    /* Get the verbs context from the RDMA CM ID */
    ctx->ibv_ctx = ctx->conn_id->verbs;

    /* Step 1: Allocate Protection Domain */
    ctx->pd = ibv_alloc_pd(ctx->ibv_ctx);
    if (!ctx->pd) {
        fprintf(stderr, "ibv_alloc_pd failed\n");
        return -1;
    }

    /* Step 2: Create Completion Queue */
    ctx->cq = ibv_create_cq(ctx->ibv_ctx,
                              CQ_DEPTH,  /* max completions */
                              NULL,      /* user context */
                              NULL,      /* completion channel (NULL = poll) */
                              0);        /* completion vector */
    if (!ctx->cq) {
        fprintf(stderr, "ibv_create_cq failed\n");
        return -1;
    }

    /* Step 3: Create Queue Pair (RC - Reliable Connected) */
    qp_attr.send_cq = ctx->cq;
    qp_attr.recv_cq = ctx->cq;
    qp_attr.qp_type = IBV_QPT_RC;
    qp_attr.cap.max_send_wr  = QP_SEND_DEPTH;  /* max outstanding send WRs */
    qp_attr.cap.max_recv_wr  = QP_RECV_DEPTH;  /* max outstanding recv WRs */
    qp_attr.cap.max_send_sge = 1;              /* scatter-gather entries */
    qp_attr.cap.max_recv_sge = 1;
    qp_attr.sq_sig_all = 0;  /* Only signal when IBV_SEND_SIGNALED set */

    ret = rdma_create_qp(ctx->conn_id, ctx->pd, &qp_attr);
    if (ret) {
        perror("rdma_create_qp");
        return ret;
    }
    ctx->qp = ctx->conn_id->qp;

    /* Step 4: Allocate data buffer */
    ctx->buf = malloc(BUFFER_SIZE);
    if (!ctx->buf) {
        fprintf(stderr, "malloc failed\n");
        return -1;
    }
    memset(ctx->buf, 0, BUFFER_SIZE);

    /* Step 5: Register Memory Region
     *
     * IBV_ACCESS_LOCAL_WRITE:  CPU can write to this MR
     * IBV_ACCESS_REMOTE_WRITE: Remote RDMA WRITE allowed
     * IBV_ACCESS_REMOTE_READ:  Remote RDMA READ allowed
     *
     * This call:
     *   - Pins the pages (prevents OS from swapping them out)
     *   - Creates IOMMU mapping for RNIC
     *   - Returns lkey and rkey
     */
    ctx->mr = ibv_reg_mr(ctx->pd,
                          ctx->buf,
                          BUFFER_SIZE,
                          IBV_ACCESS_LOCAL_WRITE |
                          IBV_ACCESS_REMOTE_WRITE |
                          IBV_ACCESS_REMOTE_READ);
    if (!ctx->mr) {
        fprintf(stderr, "ibv_reg_mr failed\n");
        return -1;
    }

    /* Save our info to send to client */
    ctx->local_info.addr = (uint64_t)(uintptr_t)ctx->buf;
    ctx->local_info.rkey = ctx->mr->rkey;
    ctx->local_info.size = BUFFER_SIZE;

    printf("MR registered: addr=0x%lx, lkey=0x%x, rkey=0x%x\n",
           ctx->local_info.addr, ctx->mr->lkey, ctx->mr->rkey);

    return 0;
}

static int run_server(void)
{
    struct rdma_server_ctx ctx = {};
    struct rdma_cm_event *event;
    struct rdma_conn_param conn_param = {};
    struct sockaddr_in sin = {};
    int ret;

    /* Create RDMA CM event channel */
    ctx.cm_channel = rdma_create_event_channel();
    if (!ctx.cm_channel) {
        perror("rdma_create_event_channel");
        return -1;
    }

    /* Create listening CM ID */
    ret = rdma_create_id(ctx.cm_channel, &ctx.listen_id, NULL, RDMA_PS_TCP);
    if (ret) {
        perror("rdma_create_id");
        return ret;
    }

    /* Bind to port */
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = htonl(INADDR_ANY);
    sin.sin_port = htons(PORT);

    ret = rdma_bind_addr(ctx.listen_id, (struct sockaddr *)&sin);
    if (ret) {
        perror("rdma_bind_addr");
        return ret;
    }

    /* Listen for connections */
    ret = rdma_listen(ctx.listen_id, 10);
    if (ret) {
        perror("rdma_listen");
        return ret;
    }
    printf("Listening on port %d...\n", PORT);

    /* Wait for connection request */
    ret = rdma_get_cm_event(ctx.cm_channel, &event);
    if (ret || event->event != RDMA_CM_EVENT_CONNECT_REQUEST) {
        fprintf(stderr, "Expected CONNECT_REQUEST, got %d\n", event->event);
        return -1;
    }
    ctx.conn_id = event->id;
    rdma_ack_cm_event(event);

    printf("Got connection request!\n");

    /* Create RDMA resources (PD, CQ, QP, MR) */
    ret = create_resources(&ctx);
    if (ret) return ret;

    /* Accept connection, send our MR info as private data */
    conn_param.private_data     = &ctx.local_info;
    conn_param.private_data_len = sizeof(ctx.local_info);
    conn_param.responder_resources = 1;
    conn_param.initiator_depth     = 1;

    ret = rdma_accept(ctx.conn_id, &conn_param);
    if (ret) {
        perror("rdma_accept");
        return ret;
    }

    /* Wait for connection established */
    ret = rdma_get_cm_event(ctx.cm_channel, &event);
    if (ret || event->event != RDMA_CM_EVENT_ESTABLISHED) {
        fprintf(stderr, "Expected ESTABLISHED\n");
        return -1;
    }
    rdma_ack_cm_event(event);
    printf("Connection established!\n");

    /* Now client can RDMA WRITE into our buffer.
     * We poll the buffer to detect incoming data.
     * In production: use a sentinel value or a separate control message.
     */
    printf("Waiting for data in buffer...\n");
    while (ctx.buf[0] == 0) {
        usleep(1000);  /* 1ms poll interval */
    }
    printf("Received data: %s\n", ctx.buf);

    /* Cleanup */
    rdma_disconnect(ctx.conn_id);
    rdma_get_cm_event(ctx.cm_channel, &event);
    rdma_ack_cm_event(event);

    ibv_dereg_mr(ctx.mr);       /* Unregister MR (unpin pages) */
    rdma_destroy_qp(ctx.conn_id);
    ibv_destroy_cq(ctx.cq);
    ibv_dealloc_pd(ctx.pd);
    rdma_destroy_id(ctx.conn_id);
    rdma_destroy_id(ctx.listen_id);
    rdma_destroy_event_channel(ctx.cm_channel);
    free(ctx.buf);

    return 0;
}

int main(void)
{
    return run_server();
}
```

```c
/*
 * rdma_client.c - RDMA client (initiator)
 *
 * Connects to server, then performs RDMA WRITE directly
 * into server's memory — without server CPU involvement!
 *
 * Compile: gcc -o rdma_client rdma_client.c -lrdmacm -libverbs
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <rdma/rdma_cma.h>
#include <infiniband/verbs.h>

#define PORT            18515
#define BUFFER_SIZE     (4 * 1024 * 1024)

struct rdma_info {
    uint64_t addr;
    uint32_t rkey;
    uint32_t size;
};

struct rdma_client_ctx {
    struct rdma_event_channel *cm_channel;
    struct rdma_cm_id         *cm_id;
    struct ibv_pd             *pd;
    struct ibv_cq             *cq;
    struct ibv_qp             *qp;
    struct ibv_mr             *local_mr;
    char                      *local_buf;
    struct rdma_info           remote_info;  /* Server's MR info */
};

static int do_rdma_write(struct rdma_client_ctx *ctx,
                           const char *message)
{
    struct ibv_send_wr wr = {}, *bad_wr;
    struct ibv_sge sge = {};
    struct ibv_wc wc;
    int ret, num_completions;

    /* Copy message to our local (registered) buffer */
    strncpy(ctx->local_buf, message, BUFFER_SIZE - 1);

    /* Scatter-Gather Entry: describes our LOCAL source */
    sge.addr   = (uint64_t)(uintptr_t)ctx->local_buf;
    sge.length = strlen(message) + 1;
    sge.lkey   = ctx->local_mr->lkey;  /* local key for our MR */

    /* Work Request: the RDMA WRITE operation */
    wr.wr_id            = 1;            /* user-defined ID, returned in WC */
    wr.opcode           = IBV_WR_RDMA_WRITE;  /* RDMA WRITE operation */
    wr.send_flags       = IBV_SEND_SIGNALED;  /* generate completion */
    wr.sg_list          = &sge;
    wr.num_sge          = 1;

    /* Remote destination: server's buffer */
    wr.wr.rdma.remote_addr = ctx->remote_info.addr;   /* server buffer VA */
    wr.wr.rdma.rkey        = ctx->remote_info.rkey;   /* server's R_Key */

    printf("RDMA WRITE: local=%p → remote=0x%lx, len=%u\n",
           ctx->local_buf, ctx->remote_info.addr, sge.length);

    /*
     * ibv_post_send():
     *   - Posts WR to Send Queue
     *   - RNIC picks it up and executes RDMA WRITE
     *   - Returns immediately (async!)
     *   - CPU does NOT wait for transfer to complete
     */
    ret = ibv_post_send(ctx->qp, &wr, &bad_wr);
    if (ret) {
        perror("ibv_post_send");
        return ret;
    }

    printf("WR posted to RNIC. Polling for completion...\n");

    /* Poll Completion Queue until our WR completes */
    do {
        num_completions = ibv_poll_cq(ctx->cq, 1, &wc);
    } while (num_completions == 0);

    if (num_completions < 0) {
        fprintf(stderr, "ibv_poll_cq error\n");
        return -1;
    }

    if (wc.status != IBV_WC_SUCCESS) {
        fprintf(stderr, "WC error: %s (wr_id=%llu)\n",
                ibv_wc_status_str(wc.status), (unsigned long long)wc.wr_id);
        return -1;
    }

    printf("RDMA WRITE complete! %u bytes transferred to server.\n",
           wc.byte_len);
    return 0;
}

static int run_client(const char *server_ip)
{
    struct rdma_client_ctx ctx = {};
    struct rdma_cm_event *event;
    struct rdma_conn_param conn_param = {};
    struct ibv_qp_init_attr qp_attr = {};
    struct sockaddr_in sin = {};
    int ret;

    /* Create CM channel and ID */
    ctx.cm_channel = rdma_create_event_channel();
    ret = rdma_create_id(ctx.cm_channel, &ctx.cm_id, NULL, RDMA_PS_TCP);
    if (ret) { perror("rdma_create_id"); return ret; }

    /* Resolve server address */
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = inet_addr(server_ip);
    sin.sin_port = htons(PORT);

    ret = rdma_resolve_addr(ctx.cm_id, NULL, (struct sockaddr *)&sin, 2000);
    if (ret) { perror("rdma_resolve_addr"); return ret; }

    rdma_get_cm_event(ctx.cm_channel, &event);
    rdma_ack_cm_event(event);

    ret = rdma_resolve_route(ctx.cm_id, 2000);
    if (ret) { perror("rdma_resolve_route"); return ret; }

    rdma_get_cm_event(ctx.cm_channel, &event);
    rdma_ack_cm_event(event);

    /* Create resources */
    ctx.pd = ibv_alloc_pd(ctx.cm_id->verbs);
    ctx.cq = ibv_create_cq(ctx.cm_id->verbs, 64, NULL, NULL, 0);

    qp_attr.send_cq = ctx.cq;
    qp_attr.recv_cq = ctx.cq;
    qp_attr.qp_type = IBV_QPT_RC;
    qp_attr.cap.max_send_wr  = 64;
    qp_attr.cap.max_recv_wr  = 64;
    qp_attr.cap.max_send_sge = 1;
    qp_attr.cap.max_recv_sge = 1;
    rdma_create_qp(ctx.cm_id, ctx.pd, &qp_attr);
    ctx.qp = ctx.cm_id->qp;

    /* Allocate and register local buffer */
    ctx.local_buf = malloc(BUFFER_SIZE);
    ctx.local_mr  = ibv_reg_mr(ctx.pd, ctx.local_buf, BUFFER_SIZE,
                                 IBV_ACCESS_LOCAL_WRITE);

    /* Connect and receive server's MR info in private data */
    conn_param.initiator_depth     = 1;
    conn_param.responder_resources = 1;
    ret = rdma_connect(ctx.cm_id, &conn_param);
    if (ret) { perror("rdma_connect"); return ret; }

    ret = rdma_get_cm_event(ctx.cm_channel, &event);
    if (event->event != RDMA_CM_EVENT_ESTABLISHED) {
        fprintf(stderr, "Connection failed\n"); return -1;
    }

    /* Extract server's MR info from private data */
    memcpy(&ctx.remote_info, event->param.conn.private_data,
           sizeof(ctx.remote_info));
    rdma_ack_cm_event(event);

    printf("Connected! Server MR: addr=0x%lx, rkey=0x%x, size=%u\n",
           ctx.remote_info.addr, ctx.remote_info.rkey, ctx.remote_info.size);

    /* Perform RDMA WRITE */
    ret = do_rdma_write(&ctx, "Hello from RDMA client! Zero-copy!");
    if (ret) return ret;

    /* Cleanup */
    rdma_disconnect(ctx.cm_id);
    ibv_dereg_mr(ctx.local_mr);
    rdma_destroy_qp(ctx.cm_id);
    ibv_destroy_cq(ctx.cq);
    ibv_dealloc_pd(ctx.pd);
    rdma_destroy_id(ctx.cm_id);
    rdma_destroy_event_channel(ctx.cm_channel);
    free(ctx.local_buf);

    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <server_ip>\n", argv[0]);
        return 1;
    }
    return run_client(argv[1]);
}
```

### 16.2 High-Performance Send Loop with Inline Data

```c
/*
 * HIGH-PERFORMANCE PATTERNS
 * Techniques used in production RDMA systems
 */

/* 1. INLINE DATA SEND - Zero-copy for small messages
 *
 * For small messages (<= max_inline_data), RNIC copies data
 * directly from WR, no DMA mapping needed.
 * Eliminates MR registration overhead for small sends.
 */
static int inline_send(struct ibv_qp *qp, const void *data, size_t len)
{
    struct ibv_send_wr wr = {}, *bad_wr;
    struct ibv_sge sge = {};

    sge.addr   = (uint64_t)(uintptr_t)data;
    sge.length = len;
    sge.lkey   = 0;  /* Not used for inline */

    wr.wr_id      = 0;
    wr.opcode     = IBV_WR_SEND;
    wr.send_flags = IBV_SEND_INLINE | IBV_SEND_SIGNALED;
    wr.sg_list    = &sge;
    wr.num_sge    = 1;

    return ibv_post_send(qp, &wr, &bad_wr);
}

/* 2. BATCH POLLING - More efficient than one-by-one
 *
 * Poll up to N completions at once. Amortizes polling overhead.
 */
#define MAX_POLL_BATCH 32

static int poll_completions(struct ibv_cq *cq, process_wc_fn process_fn)
{
    struct ibv_wc wc_array[MAX_POLL_BATCH];
    int total_completed = 0;
    int n;

    do {
        n = ibv_poll_cq(cq, MAX_POLL_BATCH, wc_array);
        if (n < 0) return n;

        for (int i = 0; i < n; i++) {
            if (wc_array[i].status != IBV_WC_SUCCESS) {
                fprintf(stderr, "CQE error: %s\n",
                        ibv_wc_status_str(wc_array[i].status));
            } else {
                process_fn(&wc_array[i]);
            }
        }
        total_completed += n;
    } while (n == MAX_POLL_BATCH);  /* Keep polling if CQ was full */

    return total_completed;
}

/* 3. UNSIGNALED SENDS - Reduce CQE generation
 *
 * Don't generate completion for every send.
 * Only generate completion every N sends.
 * Reduces CQ pressure in high-throughput scenarios.
 */
#define SIGNAL_EVERY 16

static int unsignaled_send_loop(struct ibv_qp *qp, struct ibv_mr *mr,
                                  void **buffers, size_t buf_size, int num_msgs)
{
    struct ibv_send_wr wr = {}, *bad_wr;
    struct ibv_sge sge;
    int i, ret;

    for (i = 0; i < num_msgs; i++) {
        sge.addr   = (uint64_t)(uintptr_t)buffers[i];
        sge.length = buf_size;
        sge.lkey   = mr->lkey;

        wr.wr_id   = i;
        wr.opcode  = IBV_WR_SEND;
        wr.sg_list = &sge;
        wr.num_sge = 1;

        /* Only request completion every SIGNAL_EVERY sends */
        if ((i + 1) % SIGNAL_EVERY == 0 || i == num_msgs - 1) {
            wr.send_flags = IBV_SEND_SIGNALED;
        } else {
            wr.send_flags = 0;  /* No completion generated */
        }

        ret = ibv_post_send(qp, &wr, &bad_wr);
        if (ret) return ret;
    }
    return 0;
}
```

---

## 17. RDMA in Rust

### 17.1 Safe RDMA Abstractions in Rust

```rust
// rdma_safe.rs - Type-safe RDMA abstractions in Rust
// Uses RAII (Resource Acquisition Is Initialization) for automatic cleanup
// Prevents: double-free, use-after-free, wrong access flags

use std::ffi::CString;
use std::ptr::{self, NonNull};
use rdmacm_sys::*;    // raw C bindings
use ibverbs_sys::*;   // raw C bindings

/// Error type for RDMA operations
#[derive(Debug, thiserror::Error)]
pub enum RdmaError {
    #[error("RDMA CM error: {0}")]
    CmError(i32),
    #[error("Verbs error: {0}")]
    VerbsError(i32),
    #[error("Memory registration failed")]
    MrError,
    #[error("QP creation failed")]
    QpError,
    #[error("Completion error: {0}")]
    CompletionError(String),
}

type Result<T> = std::result::Result<T, RdmaError>;

/// RAII wrapper for ibv_context (RDMA device context)
pub struct DeviceContext {
    inner: NonNull<ibv_context>,
}

impl DeviceContext {
    pub fn open(device_name: &str) -> Result<Self> {
        // Get list of RDMA devices
        let mut num_devices: i32 = 0;
        let device_list = unsafe { ibv_get_device_list(&mut num_devices) };

        if device_list.is_null() || num_devices == 0 {
            return Err(RdmaError::VerbsError(-1));
        }

        let target_name = CString::new(device_name).unwrap();
        let ctx = unsafe {
            let mut selected = ptr::null_mut();
            for i in 0..num_devices as usize {
                let dev = *device_list.add(i);
                let name = ibv_get_device_name(dev);
                if libc::strcmp(name, target_name.as_ptr()) == 0 {
                    selected = ibv_open_device(dev);
                    break;
                }
            }
            ibv_free_device_list(device_list);
            selected
        };

        NonNull::new(ctx)
            .map(|inner| DeviceContext { inner })
            .ok_or(RdmaError::VerbsError(-1))
    }

    pub fn as_ptr(&self) -> *mut ibv_context {
        self.inner.as_ptr()
    }
}

impl Drop for DeviceContext {
    fn drop(&mut self) {
        unsafe { ibv_close_device(self.inner.as_ptr()); }
    }
}

/// RAII wrapper for ibv_pd (Protection Domain)
pub struct ProtectionDomain {
    inner: NonNull<ibv_pd>,
    // ProtectionDomain borrows DeviceContext — ensures ctx outlives PD
    _ctx: std::marker::PhantomData<DeviceContext>,
}

impl ProtectionDomain {
    pub fn new(ctx: &DeviceContext) -> Result<Self> {
        let pd = unsafe { ibv_alloc_pd(ctx.as_ptr()) };
        NonNull::new(pd)
            .map(|inner| ProtectionDomain { inner, _ctx: Default::default() })
            .ok_or(RdmaError::VerbsError(-1))
    }

    pub fn as_ptr(&self) -> *mut ibv_pd {
        self.inner.as_ptr()
    }
}

impl Drop for ProtectionDomain {
    fn drop(&mut self) {
        unsafe { ibv_dealloc_pd(self.inner.as_ptr()); }
    }
}

/// Access flags for Memory Region registration
#[derive(Debug, Clone, Copy)]
pub struct MrAccessFlags(pub u32);

impl MrAccessFlags {
    pub const LOCAL_WRITE: Self  = MrAccessFlags(IBV_ACCESS_LOCAL_WRITE as u32);
    pub const REMOTE_READ: Self  = MrAccessFlags(IBV_ACCESS_REMOTE_READ as u32);
    pub const REMOTE_WRITE: Self = MrAccessFlags(IBV_ACCESS_REMOTE_WRITE as u32);

    pub fn bits(self) -> u32 { self.0 }
}

impl std::ops::BitOr for MrAccessFlags {
    type Output = Self;
    fn bitor(self, rhs: Self) -> Self { MrAccessFlags(self.0 | rhs.0) }
}

/// RAII wrapper for ibv_mr (Memory Region)
///
/// KEY SAFETY PROPERTY:
/// The lifetime 'buf ties the MR to the buffer it was registered from.
/// If the buffer goes out of scope, the MR cannot exist.
/// The compiler ENFORCES this via lifetimes.
pub struct MemoryRegion<'buf> {
    inner: NonNull<ibv_mr>,
    /// We "own" a reference to the buffer for our lifetime
    _buf: std::marker::PhantomData<&'buf mut [u8]>,
}

impl<'buf> MemoryRegion<'buf> {
    /// Register a buffer for RDMA access.
    ///
    /// After this call, the RNIC can DMA to/from buf for our lifetime.
    pub fn register(
        pd: &ProtectionDomain,
        buf: &'buf mut [u8],
        access: MrAccessFlags,
    ) -> Result<Self> {
        let mr = unsafe {
            ibv_reg_mr(
                pd.as_ptr(),
                buf.as_mut_ptr() as *mut _,
                buf.len(),
                access.bits() as i32,
            )
        };

        NonNull::new(mr)
            .map(|inner| MemoryRegion { inner, _buf: Default::default() })
            .ok_or(RdmaError::MrError)
    }

    /// Get the local key for local operations
    pub fn lkey(&self) -> u32 {
        unsafe { (*self.inner.as_ptr()).lkey }
    }

    /// Get the remote key to give to remote nodes
    pub fn rkey(&self) -> u32 {
        unsafe { (*self.inner.as_ptr()).rkey }
    }

    /// Get the address of the registered region
    pub fn addr(&self) -> u64 {
        unsafe { (*self.inner.as_ptr()).addr as u64 }
    }

    /// Get the length
    pub fn length(&self) -> usize {
        unsafe { (*self.inner.as_ptr()).length }
    }
}

impl<'buf> Drop for MemoryRegion<'buf> {
    fn drop(&mut self) {
        // SAFETY: Called exactly once (Rust Drop guarantee)
        unsafe { ibv_dereg_mr(self.inner.as_ptr()); }
        // Pages are unpinned, IOMMU mapping removed after this
    }
}

/// Represents a remote memory target for RDMA operations
#[derive(Debug, Clone, Copy)]
pub struct RemoteTarget {
    pub addr: u64,   /* Remote virtual address */
    pub rkey: u32,   /* Remote key for access */
    pub size: usize, /* Size of remote region */
}

/// RDMA Write operation builder (type-safe, no raw pointers in user code)
pub struct RdmaWriteOp<'a> {
    qp: &'a QueuePair,
    local_mr: &'a MemoryRegion<'a>,
    local_offset: usize,
    remote: RemoteTarget,
    length: usize,
    wr_id: u64,
    signaled: bool,
}

impl<'a> RdmaWriteOp<'a> {
    pub fn new(qp: &'a QueuePair, local_mr: &'a MemoryRegion<'a>,
               remote: RemoteTarget) -> Self {
        RdmaWriteOp {
            qp, local_mr, local_offset: 0, remote,
            length: remote.size, wr_id: 0, signaled: true,
        }
    }

    pub fn with_offset(mut self, offset: usize) -> Self {
        self.local_offset = offset; self
    }

    pub fn with_length(mut self, len: usize) -> Self {
        self.length = len; self
    }

    pub fn with_wr_id(mut self, id: u64) -> Self {
        self.wr_id = id; self
    }

    pub fn unsignaled(mut self) -> Self {
        self.signaled = false; self
    }

    /// Execute the RDMA write. Returns Ok(()) immediately (async).
    pub fn execute(self) -> Result<()> {
        // All the raw pointer manipulation is contained HERE, not in user code
        let sge = ibv_sge {
            addr:   self.local_mr.addr() + self.local_offset as u64,
            length: self.length as u32,
            lkey:   self.local_mr.lkey(),
        };

        let mut wr: ibv_send_wr = unsafe { std::mem::zeroed() };
        wr.wr_id   = self.wr_id;
        wr.opcode  = ibv_wr_opcode::IBV_WR_RDMA_WRITE;
        wr.send_flags = if self.signaled {
            ibv_send_flags::IBV_SEND_SIGNALED as u32
        } else { 0 };
        wr.sg_list = &sge as *const _ as *mut _;
        wr.num_sge = 1;
        unsafe {
            wr.wr.rdma.remote_addr = self.remote.addr;
            wr.wr.rdma.rkey        = self.remote.rkey;
        }

        let mut bad_wr = ptr::null_mut();
        let ret = unsafe { ibv_post_send(self.qp.as_ptr(), &mut wr, &mut bad_wr) };
        if ret != 0 {
            Err(RdmaError::VerbsError(ret))
        } else {
            Ok(())
        }
    }
}

/// USAGE EXAMPLE - See how clean user code becomes with these abstractions
fn example_rdma_write(device_name: &str) -> Result<()> {
    let mut data = vec![0u8; 4096];
    data[..11].copy_from_slice(b"Hello RDMA!");

    let ctx = DeviceContext::open(device_name)?;
    let pd  = ProtectionDomain::new(&ctx)?;
    let mr  = MemoryRegion::register(
        &pd,
        &mut data,
        MrAccessFlags::LOCAL_WRITE | MrAccessFlags::REMOTE_WRITE,
    )?;

    println!("MR registered: rkey={}, addr={:#x}", mr.rkey(), mr.addr());

    // MR is automatically deregistered (pages unpinned) when it goes out of scope.
    // Rust's borrow checker ensures `data` is not accessed during MR's lifetime
    // in a way that would corrupt DMA operations.

    Ok(())
    // Drop order: mr → pd → ctx (reversed declaration order)
    // RAII ensures correct cleanup order!
}
```

---

## 18. Performance Tuning & Advanced Topics

### 18.1 RDMA Performance Tuning

```
RDMA PERFORMANCE TUNING GUIDE
================================

1. NIC FIRMWARE & DRIVER
   $ mlxconfig -d /dev/mst/mt4123_pciconf0 show  # View config
   $ mlxconfig -d /dev/mst/... set LINK_TYPE_P1=2  # Set Ethernet mode

2. MTU (Maximum Transmission Unit)
   Larger MTU = better throughput for bulk transfers
   $ ip link set ens1f0 mtu 9000   # Jumbo frames for RoCE
   Recommended: 4096 or 9000 bytes for RDMA

3. CPU AFFINITY
   Bind RDMA application to CPUs near the NIC's NUMA node:
   $ cat /sys/class/infiniband/mlx5_0/device/numa_node  # NIC's NUMA node
   $ numactl --cpunodebind=0 ./rdma_app   # Run on NUMA 0

4. INTERRUPT AFFINITY
   Bind NIC interrupts to the same NUMA node as the NIC:
   $ cat /proc/interrupts | grep mlx5   # Find IRQ numbers
   $ echo 0x3 > /proc/irq/48/smp_affinity  # Bind to CPU 0,1

5. HUGE PAGES
   Large memory registrations benefit from huge pages (2MB/1GB)
   Reduces IOMMU page table entries, fewer TLB misses:
   $ echo 512 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
   Use mmap with MAP_HUGETLB for huge page allocation

6. PFC (Priority Flow Control) for RoCE
   Without PFC, packet drops break RDMA!
   $ mlnx_qos -i ens1f0 --pfc 0,0,0,1,0,0,0,0  # Enable PFC on priority 3

7. CONGESTION CONTROL (DCQCN for RoCE)
   $ cat /sys/class/infiniband/mlx5_0/device/dcqcn_enable  # Check if enabled
   Tune DCQCN parameters:
   $ echo 1 > /sys/module/mlx5_core/parameters/cong_ctls_mode

8. POLLING vs INTERRUPTS
   For latency-critical: use polling (busy-wait on CQ)
   For throughput: consider event-driven for CPU efficiency
   Hybrid: poll for X µs, then switch to interrupt
```

### 18.2 Memory Registration Optimization

```
MR REGISTRATION OPTIMIZATION
==============================

Problem: ibv_reg_mr() is slow (microseconds to milliseconds)
         due to page pinning and IOMMU mapping
         NOT suitable for per-message registration!

SOLUTION 1: Register-once, use-many
  Register a large pool buffer once at startup.
  Sub-allocate from it at runtime.
  Only one MR for the whole pool.

SOLUTION 2: On-Demand Paging (ODP) - mlx5 feature
  Pages registered lazily (on first DMA access)
  Virtual address MR: hardware walks page tables on fault
  Advantage: No page pinning at registration time!
  $ grep ODP /sys/class/infiniband/mlx5_0/ports/1/pkey_idx/0
  Enable: IBV_ACCESS_ON_DEMAND flag in ibv_reg_mr()

SOLUTION 3: DEVX and User-Space Memory Management
  Advanced MLX5 feature: manage MR page tables from user space
  Used in projects like UCX (Unified Communication X)

SOLUTION 4: Memory region caching (used in UCX, libfabric)
  Cache recently used MRs keyed by (addr, size, access_flags)
  Re-use existing MR if buffer address/size match
  LRU eviction policy
```

### 18.3 Send Queue Optimization

```
SEND QUEUE PATTERNS
====================

PATTERN 1: WQE (Work Queue Element) batching
  Post multiple WRs in one ibv_post_send() call:
  
  struct ibv_send_wr wr[N];
  for (int i = 0; i < N-1; i++) wr[i].next = &wr[i+1];
  wr[N-1].next = NULL;  // chain end
  ibv_post_send(qp, &wr[0], &bad_wr);
  
  One doorbell ring for N WRs instead of N doorbell rings!

PATTERN 2: Doorbell batching (MLX5-specific)
  Use extended verbs (ibv_wr_*) to write multiple WQEs
  then ring doorbell ONCE:
  
  struct ibv_qp_ex *qpx = ibv_qp_to_qp_ex(qp);
  ibv_wr_start(qpx);
  for (int i = 0; i < N; i++) {
      ibv_wr_rdma_write(qpx, remote_rkey, remote_addr + i*len);
      ibv_wr_set_sge(qpx, lkey, local_addr + i*len, len);
  }
  ibv_wr_complete(qpx);  // One doorbell for all N

PATTERN 3: Software queueing for send window management
  Don't overflow the SQ! Track outstanding WRs:
  
  if (outstanding_wrs >= max_send_wr - 1) {
      /* SQ is full, drain completions first */
      drain_completions(cq);
  }
  ibv_post_send(qp, &wr, &bad_wr);
  outstanding_wrs++;
```

---

## 19. Debugging DMA & RDMA Issues

### 19.1 DMA Debugging Tools

```
DMA DEBUGGING
==============

1. DMA_API_DEBUG (Kernel Config)
   CONFIG_DMA_API_DEBUG=y
   Adds runtime checking:
     - Detects double-unmap
     - Detects use-after-unmap
     - Checks access to unmapped DMA addresses
     - Reports invalid DMA lengths

   Enable in /boot/config-$(uname -r) then recompile kernel.

2. dma-debug sysfs interface:
   /sys/kernel/debug/dma-api/
     all_errors      - Show all detected errors
     num_errors      - Count of errors
     disabled        - Whether DMA debugging is disabled
     nr_total_entries - Total DMA mapping entries
     
   Example error output:
   "DMA-API: device driver tries to free DMA memory it has not allocated"

3. IOMMU debugging:
   $ dmesg | grep -i iommu
   $ cat /sys/kernel/iommu_groups/*/devices
   
   IOMMU fault = device tried to DMA to unmapped address:
   "DMAR: DRHD: handling fault status reg 602"
   "DMAR: [DMA Read] Request device [02:00.0] fault addr 0xbad00000"

4. /proc/iomem - Physical memory map:
   $ cat /proc/iomem
   Shows RAM regions, MMIO regions, reserved regions.
   DMA must target RAM regions!

5. /sys/class/dma/ - DMA channel info:
   $ ls /sys/class/dma/
   $ cat /sys/class/dma/dma0chan0/in_use

6. ftrace for DMA tracing:
   $ echo 1 > /sys/kernel/debug/tracing/events/dma_fence/enable
   $ cat /sys/kernel/debug/tracing/trace
```

### 19.2 RDMA Debugging Tools

```
RDMA DEBUGGING TOOLS
=====================

1. ibv_devinfo - Device capabilities
   $ ibv_devinfo
   hca_id:  mlx5_0
   transport: InfiniBand (0)
   node_guid: 0002:c903:00be:c2d0
   ... (many capability fields)

2. ibstat - Port status
   $ ibstat
   CA 'mlx5_0'
     Port 1:
       State: Active
       Physical state: 5: LinkUp
       Rate: 100                  ← 100 Gbps!
       Link layer: Ethernet       ← RoCE mode

3. perfquery - Performance counters
   $ perfquery -x mlx5_0 1
   Counts errors (symbol_err, link_downed, rx_errors, etc.)
   High symbol_err → cable/signal issue
   High rx_errors → PFC misconfiguration for RoCE

4. ibping - RDMA ping (like ping but over RDMA CM)
   Server: $ ibping -s
   Client: $ ibping 192.168.1.1
   Shows RDMA latency and RTT

5. qperf - RDMA performance benchmark
   Server: $ qperf
   Client: $ qperf 192.168.1.1 rc_bw rc_lat
   Shows bandwidth and latency

6. ib_send_bw / ib_write_bw / ib_read_bw - perftest suite
   $ ib_write_bw -a -x 3        # Server (auto size, GID index 3)
   $ ib_write_bw 192.168.1.1 -a -x 3  # Client
   
   Output shows bandwidth for various message sizes.

7. rdma tool (iproute2 rdma)
   $ rdma dev         # List RDMA devices
   $ rdma link        # Link state
   $ rdma stat        # Statistics
   $ rdma stat show mlx5_0/1  # Per-port stats

8. /sys/class/infiniband/ - Runtime stats
   $ cat /sys/class/infiniband/mlx5_0/ports/1/counters/port_xmit_data
   $ cat /sys/class/infiniband/mlx5_0/ports/1/counters/VL15_dropped

9. ethtool for RoCE NIC
   $ ethtool -S ens1f0 | grep -i roce  # RoCE-specific counters
   $ ethtool -S ens1f0 | grep err      # Error counters

10. strace / ltrace for ibverbs issues
    $ strace -e trace=ioctl ./rdma_app 2>&1 | head -50
    $ ltrace -l librdmacm.so ./rdma_app 2>&1 | head -50
```

### 19.3 Common Issues and Solutions

```
COMMON DMA/RDMA ISSUES
========================

ISSUE: dma_alloc_coherent returns NULL
  Causes:
    - Out of DMA-able memory (check /proc/buddyinfo)
    - DMA mask too restrictive
    - Memory fragmentation
  Solutions:
    - Use dma_pool for small allocations
    - Call earlier in driver init (before memory fragments)
    - Use CMA (Contiguous Memory Allocator): cma_alloc()

ISSUE: DMA data corruption
  Causes:
    - Missing dma_wmb()/dma_rmb() barriers
    - CPU accessed buffer between map and unmap
    - Wrong DMA direction flag (TO vs FROM)
  Solutions:
    - Enable CONFIG_DMA_API_DEBUG
    - Verify barrier placement
    - Never touch mapped buffer on CPU side

ISSUE: RDMA write doesn't arrive
  Causes:
    - R_Key mismatch (wrong key sent to remote)
    - Remote buffer address wrong
    - QP not in RTS state
    - Network issue (check ibstat)
  Solutions:
    - Add RDMA_WRITE with IMMEDIATE and post a RECV
      (receiver will know when write completes)
    - Verify R_Key and address via out-of-band check
    - Check QP state: rdma stat show <dev>/<port>

ISSUE: RoCE packet drops
  Causes:
    - Missing PFC configuration
    - Switch not supporting lossless Ethernet
    - MTU mismatch
  Solutions:
    $ mlnx_qos -i ens1f0 --pfc 0,0,0,1,0,0,0,0
    $ ip link set ens1f0 mtu 4096
    Enable ECN on switches.

ISSUE: ibv_reg_mr fails (ENOMEM)
  Causes:
    - RLIMIT_MEMLOCK (ulimit -l) too low
    - Too many pinned pages
  Solutions:
    $ ulimit -l unlimited  # or set in /etc/security/limits.conf
    Add to /etc/security/limits.conf:
      * hard memlock unlimited
      * soft memlock unlimited

ISSUE: High RDMA latency (>> expected)
  Causes:
    - CPU power management (C-states)
    - NUMA mismatch (app on NUMA 0, NIC on NUMA 1)
    - Interrupt affinity wrong
  Solutions:
    $ cpupower frequency-set -g performance
    $ echo 1 > /sys/bus/pci/devices/0000:01:00.0/numa_node
    Pin process to NIC's NUMA node with numactl
```

---

## 20. Reference: Key Data Structures

### 20.1 Linux Kernel DMA Structures

```c
/*
 * KEY KERNEL DMA DATA STRUCTURES
 * (From include/linux/dma-mapping.h, include/linux/dmaengine.h)
 */

/* ─── dma_addr_t ─────────────────────────────────────────────────── */
/* The type for DMA/bus addresses (what devices use to address memory) */
typedef u64 dma_addr_t;  /* Always 64-bit even on 32-bit systems */

/* ─── scatterlist ────────────────────────────────────────────────── */
/* One entry in a scatter-gather list */
struct scatterlist {
    unsigned long page_link;  /* encoded: pointer to page + flags */
    unsigned int  offset;     /* offset within the page */
    unsigned int  length;     /* length of this segment */
    dma_addr_t    dma_address; /* DMA address (after dma_map_sg) */
#ifdef CONFIG_NEED_SG_DMA_LENGTH
    unsigned int  dma_length; /* DMA length after mapping */
#endif
};

/* ─── dma_async_tx_descriptor ───────────────────────────────────── */
/* Represents one pending DMA transfer in the DMA engine framework */
struct dma_async_tx_descriptor {
    dma_cookie_t         cookie;      /* unique ID */
    enum dma_ctrl_flags  flags;       /* transfer flags */
    dma_addr_t           phys;        /* physical address of descriptor */
    struct dma_chan      *chan;        /* channel this belongs to */
    dma_cookie_t (*tx_submit)(struct dma_async_tx_descriptor *tx);
    int (*desc_free)(struct dma_async_tx_descriptor *tx);
    dma_async_tx_callback callback;   /* completion callback */
    dma_async_tx_callback_result callback_result;
    void                *callback_param;
    struct dmaengine_unmap_data *unmap;
};

/* ─── dma_chan ───────────────────────────────────────────────────── */
/* Represents a DMA channel */
struct dma_chan {
    struct dma_device   *device;      /* DMA controller this belongs to */
    struct list_head     device_node; /* list of channels in device */
    struct dma_chan_percpu __percpu *local; /* per-cpu state */
    int                  chan_id;     /* channel ID */
    struct dma_chan_dev  dev;         /* sysfs device */
    const char          *name;        /* channel name */
    /* ... more fields ... */
};

/* ─── dma_device ─────────────────────────────────────────────────── */
/* Represents a DMA controller/engine */
struct dma_device {
    struct kref          ref;
    unsigned int         chancnt;     /* number of channels */
    struct list_head     channels;    /* list of dma_chan */
    struct list_head     global_node; /* list in global dma_device_list */
    dma_cap_mask_t       cap_mask;    /* capabilities: MEMCPY, XOR, etc. */
    unsigned short       max_xor;
    unsigned short       max_pq;
    /* Function pointers for operations: */
    struct dma_async_tx_descriptor *(*device_prep_dma_memcpy)(
        struct dma_chan *chan, dma_addr_t dst, dma_addr_t src,
        size_t len, unsigned long flags);
    /* ... many more operation function pointers ... */
    int (*device_alloc_chan_resources)(struct dma_chan *chan);
    void (*device_free_chan_resources)(struct dma_chan *chan);
    int (*device_terminate_all)(struct dma_chan *chan);
    /* ... */
};
```

### 20.2 RDMA Verbs Data Structures

```c
/*
 * KEY RDMA VERBS DATA STRUCTURES
 * (From /usr/include/infiniband/verbs.h)
 */

/* ─── ibv_context ───────────────────────────────────────────────── */
/* Represents an open RDMA device */
struct ibv_context {
    struct ibv_device      *device;   /* physical device */
    struct ibv_context_ops  ops;      /* function table */
    int                     cmd_fd;   /* fd for kernel communication */
    int                     async_fd; /* fd for async events */
    int                     num_comp_vectors;
    pthread_mutex_t         mutex;
    void                   *abi_compat;
};

/* ─── ibv_pd ────────────────────────────────────────────────────── */
/* Protection Domain */
struct ibv_pd {
    struct ibv_context *context;
    uint32_t            handle;  /* kernel handle */
};

/* ─── ibv_mr ────────────────────────────────────────────────────── */
/* Memory Region */
struct ibv_mr {
    struct ibv_context *context;
    struct ibv_pd      *pd;
    void               *addr;    /* starting address */
    size_t              length;  /* length in bytes */
    uint32_t            handle;  /* kernel handle */
    uint32_t            lkey;    /* local key */
    uint32_t            rkey;    /* remote key */
};

/* ─── ibv_qp ────────────────────────────────────────────────────── */
/* Queue Pair */
struct ibv_qp {
    struct ibv_context *context;
    void               *qp_context;  /* user-defined */
    struct ibv_pd      *pd;
    struct ibv_cq      *send_cq;
    struct ibv_cq      *recv_cq;
    struct ibv_srq     *srq;         /* shared receive queue (optional) */
    uint32_t            handle;
    uint32_t            qp_num;      /* the QP number (used in routing) */
    enum ibv_qp_state   state;       /* RESET/INIT/RTR/RTS/SQD/SQE/ERROR */
    enum ibv_qp_type    qp_type;     /* RC/UC/UD/XRC */
    pthread_mutex_t     mutex;
    pthread_cond_t      cond;
    uint32_t            events_completed;
};

/* ─── ibv_cq ────────────────────────────────────────────────────── */
/* Completion Queue */
struct ibv_cq {
    struct ibv_context *context;
    struct ibv_comp_channel *channel; /* event notification channel */
    void               *cq_context;  /* user-defined */
    uint32_t            handle;
    int                 cqe;          /* max completions */
    pthread_mutex_t     mutex;
    pthread_cond_t      cond;
    uint32_t            comp_events_completed;
    uint32_t            async_events_completed;
};

/* ─── ibv_wc ────────────────────────────────────────────────────── */
/* Work Completion (posted to CQ when operation finishes) */
struct ibv_wc {
    uint64_t            wr_id;      /* WR ID from your Work Request */
    enum ibv_wc_status  status;     /* IBV_WC_SUCCESS or error */
    enum ibv_wc_opcode  opcode;     /* what operation completed */
    uint32_t            vendor_err; /* vendor-specific error code */
    uint32_t            byte_len;   /* bytes transferred */
    union {
        __be32          imm_data;   /* for SEND_WITH_IMM / WRITE_WITH_IMM */
        uint32_t        invalidated_rkey;
    };
    uint32_t            qp_num;     /* QP that generated this completion */
    uint32_t            src_qp;     /* source QP (for UD) */
    unsigned int        wc_flags;   /* IBV_WC_GRH, etc. */
    uint16_t            pkey_index;
    uint16_t            slid;       /* source LID (IB) */
    uint8_t             sl;         /* service level */
    uint8_t             dlid_path_bits;
};

/* ─── ibv_send_wr ───────────────────────────────────────────────── */
/* Work Request (posted to Send Queue) */
struct ibv_send_wr {
    uint64_t             wr_id;     /* user-defined ID, returned in WC */
    struct ibv_send_wr  *next;      /* linked list (batch posting) */
    struct ibv_sge      *sg_list;   /* scatter-gather elements */
    int                  num_sge;   /* number of SGEs */
    enum ibv_wr_opcode   opcode;    /* SEND, RDMA_WRITE, RDMA_READ, etc. */
    unsigned int         send_flags; /* IBV_SEND_SIGNALED, IBV_SEND_INLINE */
    union {
        __be32           imm_data;
        uint32_t         invalidate_rkey;
    };
    union {
        struct {         /* RDMA_WRITE / RDMA_READ */
            uint64_t     remote_addr;  /* remote buffer address */
            uint32_t     rkey;         /* remote key */
        } rdma;
        struct {         /* ATOMIC operations */
            uint64_t     remote_addr;
            uint64_t     compare_add;
            uint64_t     swap;
            uint32_t     rkey;
        } atomic;
        struct {         /* UD send */
            struct ibv_ah *ah;
            uint32_t      remote_qpn;
            uint32_t      remote_qkey;
        } ud;
    } wr;
};

/* ─── ibv_sge ───────────────────────────────────────────────────── */
/* Scatter-Gather Element: one contiguous memory region */
struct ibv_sge {
    uint64_t  addr;    /* virtual address of the buffer */
    uint32_t  length;  /* length in bytes */
    uint32_t  lkey;    /* local key (from MR) */
};
```

---

## Summary: Mental Models for DMA and RDMA

```
MENTAL MODELS
==============

DMA MENTAL MODEL:
  Think of DMA as "delegation with a handoff protocol":
  1. CPU prepares work order (programs DMA registers)
  2. CPU hands off buffer to DMAC (dma_map → "buffer is device's now")
  3. DMAC does work autonomously
  4. DMAC notifies CPU (interrupt)
  5. CPU takes buffer back (dma_unmap → "buffer is CPU's again")
  INVARIANT: CPU and device NEVER own the buffer simultaneously.

ADDRESS MENTAL MODEL:
  Virtual addresses: what you write in code (pointers)
  Physical addresses: DRAM chip location
  DMA/bus addresses: what PCIe devices use
  Without IOMMU: DMA ≈ Physical
  With IOMMU: DMA is device-virtual (IOMMU translates to Physical)

RDMA MENTAL MODEL:
  Think of RDMA as "the ultimate zero-copy IPC across machines":
  - Memory Registration = pinning + granting hardware access
  - R_Key = a capability token (like a file descriptor, but for memory)
  - RDMA WRITE = "remote assignment" to another machine's variable
  - RDMA READ = "remote dereference" of another machine's pointer
  - No CPU at receiver = receiver doesn't know (or care!) until it checks

QP STATE MACHINE:
  RESET → (modify_qp INIT) → INIT
  INIT  → (modify_qp RTR, set remote QPN, LID) → RTR
  RTR   → (modify_qp RTS, set retry count, timeout) → RTS
  RTS   → (error occurs) → ERROR or SQE
  Any → (modify_qp RESET) → RESET  (soft reset)
```

---

## Quick Reference

```
DMA API QUICK REFERENCE
========================

Coherent:
  dma_alloc_coherent(dev, size, &dma_addr, GFP_KERNEL) → virt_addr
  dma_free_coherent(dev, size, virt_addr, dma_addr)

Streaming (single buffer):
  dma_map_single(dev, virt_addr, size, direction) → dma_addr
  dma_unmap_single(dev, dma_addr, size, direction)
  dma_mapping_error(dev, dma_addr) → non-zero on error

Streaming (scatter-gather):
  dma_map_sg(dev, sg, nents, direction) → mapped_nents
  dma_unmap_sg(dev, sg, nents, direction)

Pool:
  dma_pool_create(name, dev, size, align, boundary) → pool
  dma_pool_alloc(pool, GFP_ATOMIC, &dma_addr) → virt_addr
  dma_pool_free(pool, virt_addr, dma_addr)
  dma_pool_destroy(pool)

Barriers:
  wmb() / rmb() / mb()           General SMP barriers
  dma_wmb() / dma_rmb()          DMA-specific (may be weaker)

DMA Engine:
  dma_request_channel(mask, filter, param) → chan
  dmaengine_prep_dma_memcpy(chan, dst, src, len, flags) → tx
  dmaengine_submit(tx) → cookie
  dma_async_issue_pending(chan)
  dma_release_channel(chan)

RDMA VERBS QUICK REFERENCE
============================

Setup:
  ibv_get_device_list(&num)                → device_list
  ibv_open_device(device)                   → context
  ibv_alloc_pd(context)                     → pd
  ibv_create_cq(context, cqe, ...)          → cq
  ibv_create_qp(pd, &qp_init_attr)          → qp
  ibv_reg_mr(pd, addr, len, access)         → mr

Connection (via RDMA CM):
  rdma_create_event_channel()               → cm_channel
  rdma_create_id(ch, &id, NULL, PS_TCP)
  rdma_bind_addr / rdma_resolve_addr
  rdma_listen / rdma_connect / rdma_accept

Operations:
  ibv_post_send(qp, &wr, &bad_wr)           (async)
  ibv_post_recv(qp, &rwr, &bad_rwr)         (async)
  ibv_poll_cq(cq, max_wc, &wc_array)        (check completion)
  ibv_req_notify_cq(cq, solicited_only)     (event notification)

Cleanup:
  ibv_dereg_mr(mr)         unpin pages, remove IOMMU mapping
  ibv_destroy_qp(qp)
  ibv_destroy_cq(cq)
  ibv_dealloc_pd(pd)
  ibv_close_device(context)
```

---

*Guide version: 1.0 | Linux Kernel 6.x | libibverbs 39+*
*Covers: x86-64, ARM64, PCIe DMA, InfiniBand, RoCEv2, iWARP*
*Languages: C (kernel + user-space), Rust (kernel + user-space)*