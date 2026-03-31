# DMA in Linux — Complete Engineering Reference

> **Audience:** Senior systems/security engineers working on Linux kernel drivers, cloud infrastructure, CNCF-adjacent projects, and secure-by-design hardware-software interfaces.
>
> **Scope:** ISA → PCI → PCIe DMA hardware, full Linux DMA API (coherent, streaming, S/G), IOMMU/SMMU architecture and bypass attacks, DMA engines, bounce buffers, P2P DMA, SR-IOV DMA isolation, eBPF-based observability of DMA paths, C driver implementations, Rust kernel/userspace implementations, threat model, and production ops.

---

## Table of Contents

1. [First-Principles: What DMA Is and Why It Exists](#1-first-principles)
2. [Hardware Architecture](#2-hardware-architecture)
3. [IOMMU and SMMU — The Security Boundary](#3-iommu-and-smmu)
4. [Linux DMA Subsystem Architecture](#4-linux-dma-subsystem-architecture)
5. [DMA API — Coherent Memory](#5-dma-api--coherent-memory)
6. [DMA API — Streaming (Single + S/G)](#6-dma-api--streaming)
7. [DMA Engine Subsystem](#7-dma-engine-subsystem)
8. [Bounce Buffers and Zone DMA](#8-bounce-buffers-and-zone-dma)
9. [PCIe P2P DMA](#9-pcie-p2p-dma)
10. [SR-IOV and DMA Isolation](#10-sr-iov-and-dma-isolation)
11. [VFIO — Userspace DMA](#11-vfio--userspace-dma)
12. [DMA and Virtualization (QEMU/KVM)](#12-dma-and-virtualization)
13. [eBPF DMA Observability and Tracing](#13-ebpf-dma-observability)
14. [C Driver Implementation — End-to-End](#14-c-driver-implementation)
15. [Rust Implementation — Kernel and Userspace](#15-rust-implementation)
16. [Threat Model and Security Mitigations](#16-threat-model-and-security)
17. [Performance: Benchmarking, Tuning, and Profiling](#17-performance)
18. [Testing, Fuzzing, and Validation](#18-testing-and-fuzzing)
19. [Roll-out, Rollback, and Production Ops](#19-rollout-and-ops)
20. [References](#20-references)

---

## 1. First-Principles

### 1.1 Why DMA Exists

A CPU accessing memory in a tight loop executes on the order of ~1–4 ns/access (L3 cache miss → DRAM ≈ 70–100 ns). To transfer, say, 4 GiB of NVMe data through the CPU, you would burn ~400 ms of CPU time in pure copy overhead, plus you serialize the memory bus. DMA offloads bulk memory transfers to peripheral hardware, allowing CPU and I/O to proceed in parallel.

```
Without DMA (PIO — Programmed I/O):
  CPU: read port → write memory → read port → write memory → ...  (busy CPU)

With DMA:
  CPU: write descriptor ring entry → ring doorbell → do other work
  Device: autonomously burst-transfers data via bus mastering
  Device: raises MSI/MSI-X interrupt → CPU processes completion
```

This is not merely a performance optimization — it is a fundamental requirement for any I/O throughput approaching the line-rate of modern interconnects (PCIe Gen5 x16 = 128 GB/s bidirectional).

### 1.2 Address Spaces and the DMA Problem

The core DMA problem is **address space translation**:

```
Physical Address Space (PA)   — what DRAM chips respond to
Virtual Address Space (VA)    — what user processes see (CR3 page table)
Bus Address / DMA Address     — what a device DMA engine programs into its descriptors
IOVA (I/O Virtual Address)    — virtual address in the device's IOMMU page table
```

On a naive system without IOMMU, Bus Address == Physical Address. This means a device with DMA capability can read or write **any physical memory page** — including kernel text, page tables, credentials in memory, and hypervisor state. This is the fundamental DMA attack surface.

```
                 +-------------+
                 |     CPU     |
                 |  (VA→PA via |
                 |  MMU/CR3)   |
                 +------+------+
                        |
               System   |  Memory Bus
               Memory   |
                 +------+------+       +----------+
                 |    DRAM     |<----->|   Device |  (DMA engine)
                 |  (PA space) |       |  NIC/NVMe|
                 +-------------+       +----+-----+
                                            |
                                    Bus Address == PA  ← INSECURE (no IOMMU)
```

### 1.3 Terminology Precision

| Term | Definition |
|---|---|
| **DMA** | Transfer of data between peripheral and memory without CPU involvement per word |
| **Bus Mastering** | Device capability to initiate bus transactions (read/write) autonomously |
| **Bus Address** | Address the device programs into its DMA descriptor; what the bus fabric routes |
| **IOMMU** | I/O Memory Management Unit — translates IOVA → PA before bus fabric sees it |
| **SMMU** | ARM System MMU — ARM's IOMMU equivalent |
| **Coherent DMA** | Memory visible consistently to both CPU and device without explicit cache ops |
| **Streaming DMA** | CPU allocates a buffer, hands it to device for one direction, syncs explicitly |
| **Scatter-Gather (S/G)** | Non-contiguous physical pages presented as a logical contiguous buffer to device |
| **IOVA** | I/O Virtual Address — virtual address in IOMMU page table, programmed into device |
| **DMA Fence** | Synchronization primitive signaling DMA completion (GPU, dma-buf) |
| **Bounce Buffer** | Kernel-allocated physically contiguous buffer used when device cannot reach PA |

---

## 2. Hardware Architecture

### 2.1 Evolution: ISA → PCI → PCIe

#### ISA DMA (8237 DMA Controller)

The Intel 8237 is the ancestor of all PC DMA. Understanding it clarifies why modern APIs look the way they do.

```
8237 Architecture:
  4 channels (8-bit), extended to 8 channels (16-bit) with cascade
  Channel registers: Base Address, Current Address, Base Count, Current Count, Mode
  DMA Modes: Single, Block, Demand, Cascade
  Address width: 24-bit (16 MB addressable) — fundamental limitation

Transfer sequence:
  1. Device asserts DRQ (DMA Request)
  2. 8237 asserts HOLD to CPU
  3. CPU asserts HLDA (Hold Acknowledge) — CPU relinquishes bus
  4. 8237 drives address lines + IOR/IOW/MEMR/MEMW
  5. Data moves device ↔ memory
  6. 8237 deasserts HOLD; CPU resumes
```

Key limitation: ISA DMA requires memory in the first 16 MB (channel 0–3) or first 16 MB of the second 16 MB range (channels 4–7). This legacy constraint lives in Linux as `GFP_DMA` and `GFP_DMA32`.

#### PCI Bus Mastering

PCI introduced **bus mastering**: the device itself drives address and data lines, no separate DMA controller chip needed. The CPU sets a bit in PCI config space (`PCI_COMMAND_MASTER`) enabling the device to initiate transactions.

```
PCI Config Space (offset 0x04):
  Bit 2: Bus Master Enable — set by kernel via pci_set_master()

PCI DMA addressing:
  32-bit PCI:  device can address 4 GiB (dma_mask = 0xFFFFFFFF)
  64-bit PCI:  device can address full 64-bit PA (dma_mask = 0xFFFFFFFFFFFFFFFF)
  
  If PA of kernel buffer > dma_mask: must use bounce buffer
```

#### PCIe (PCI Express)

PCIe replaces the shared parallel bus with point-to-point serial links (Lanes). Each lane is a full-duplex differential pair. DMA still uses bus mastering semantics but over Transaction Layer Packets (TLPs).

```
PCIe TLP Types relevant to DMA:
  MRd  (Memory Read Request)   — device reads from memory
  MWr  (Memory Write Request)  — device writes to memory
  CplD (Completion with Data)  — response to MRd
  Msg  (Message)               — MSI/MSI-X interrupt delivery

PCIe Gen Bandwidth (x16 slot):
  Gen1:  4.0 GB/s
  Gen2:  8.0 GB/s
  Gen3: 16.0 GB/s
  Gen4: 32.0 GB/s
  Gen5: 64.0 GB/s  (128 GB/s bidirectional)
  Gen6: 128 GB/s   (256 GB/s bidirectional, PAM-4 signaling)
```

### 2.2 Cache Coherency and DMA

This is where most driver bugs originate. Modern CPUs use write-back caches. If the CPU writes to a buffer and the device reads it via DMA before the cache line is flushed, the device sees stale data. Conversely, if the device writes to a buffer via DMA and the CPU reads it from cache, the CPU sees stale data.

```
Cache Coherency Protocols:
  x86/x86_64: snooping-based (MESI protocol)
    — Cache controller monitors bus transactions
    — DMA writes automatically invalidate CPU cache lines (via snooping)
    — x86 is effectively DMA-coherent by hardware design
    — BUT: write-combining buffers and store buffers complicate this

  ARM (Cortex-A, server-class):
    — NOT coherent by default for DMA
    — Requires explicit cache maintenance operations:
        - Clean (flush dirty cache lines to memory before DMA read)
        - Invalidate (discard cache lines after DMA write, before CPU read)
    — Or use inner/outer shareable domains with CCI/CCN interconnect

  RISC-V:
    — Architecture does not mandate cache coherence for DMA
    — Platform-specific: may have hardware snooping or require software maintenance

Linux handles this via arch-specific dma_map_ops callbacks.
```

### 2.3 Memory Domains and DMA Masks

```
Linux Memory Zones (x86_64):
  ZONE_DMA:    0 –   16 MiB   (GFP_DMA)   — legacy ISA DMA
  ZONE_DMA32:  0 –    4 GiB   (GFP_DMA32) — 32-bit DMA capable devices
  ZONE_NORMAL: 4 GiB – ...    — general kernel memory
  ZONE_HIGHMEM: (32-bit kernels only, deprecated)
  ZONE_MOVABLE: for memory hotplug / balloon
  ZONE_DEVICE: for persistent memory (PMEM), GPU memory

Device DMA mask determines which zone allocations must come from:
  dev->dma_mask         — coherent DMA mask (what the device can address)
  dev->coherent_dma_mask — for dma_alloc_coherent()
  
  dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64));  /* preferred for modern HW */
  dma_set_mask(dev, DMA_BIT_MASK(32));               /* 32-bit only device */
```

### 2.4 NUMA and DMA

On multi-socket NUMA systems, DMA buffer allocation locality matters for performance. A device on socket 0 doing DMA to memory on socket 1 traverses the QPI/UPI/Infinity Fabric interconnect, adding ~30–80 ns latency per access and consuming inter-socket bandwidth.

```
NUMA-aware DMA allocation:
  Use: dma_alloc_attrs() with GFP_THISNODE or explicit numa_node
  Or:  alloc_pages_node(dev_to_node(dev), GFP_KERNEL, order)
       then dma_map_page()

Check device NUMA node:
  cat /sys/bus/pci/devices/0000:03:00.0/numa_node
  
Kernel: dev_to_node(pdev->dev) returns the NUMA node of the PCIe root complex
```

---

## 3. IOMMU and SMMU

### 3.1 What IOMMU Does

The IOMMU sits between the PCIe root complex (or system fabric) and the memory controller. It intercepts all device-initiated memory accesses and translates the device-programmed address (IOVA) through a set of page tables to a physical address (PA).

```
+--------+     IOVA      +--------+      PA      +--------+
| Device | ------------> | IOMMU  | -----------> |  DRAM  |
| (NIC)  |  (bus addr)   | (DPTS) |  (phys addr) |        |
+--------+               +--------+              +--------+
                              |
                         IOMMU Page Tables (per device/group)
                              |
                         Fault on unmapped access → abort + report
```

IOMMU guarantees:
1. **Isolation**: Device A cannot access memory not explicitly mapped in its IOVA page table.
2. **Translation**: PA != IOVA; kernel controls the mapping.
3. **Fault detection**: Access to unmapped IOVA generates a hardware fault → kernel logs + kills DMA.

### 3.2 Intel VT-d (Virtualization Technology for Directed I/O)

VT-d is Intel's IOMMU. Key structures:

```
Root Table:
  256 entries (one per PCI bus)
  Root Entry → Context Table

Context Table:
  256 entries (one per device:function on bus)
  Context Entry → IOMMU Page Table (domain)
  Context Entry also encodes:
    - Address Width (30, 39, 48, 57 bits)
    - DMA Remapping Domain ID
    - Pass-through bit (no translation, for trusted devices)

IOMMU Page Table (second-level):
  4-level (PML4-like) page table
  Entries encode: Read/Write permission bits, SNOOP hint, memory type
  
  Page sizes supported: 4K, 2M, 1G (huge pages for performance)

VT-d Fault Handling:
  Primary Fault Log: ring buffer in MMIO space
  Advanced Fault Log: optional, for more faults
  Fault interrupt: MSI to a specific CPU vector
  
  Fault record fields:
    - Fault Reason (FR): unmapped, permission violation, etc.
    - Source Identifier: PCIe BDF of offending device
    - Fault Address: the IOVA that caused the fault
    - Type: write (1) or read (0)
```

#### Enabling VT-d in Linux

```
Kernel boot params:
  intel_iommu=on          — enable VT-d (may default to on in newer kernels)
  intel_iommu=off         — disable (DO NOT in production)
  iommu=pt                — pass-through mode (no translation, INSECURE)
  iommu=strict            — synchronous TLB invalidation (more secure, slower)
  iommu=lazy              — batch TLB invalidations (faster, small window)
  iommu.passthrough=0     — force strict mode (kernel 5.10+)
  
  # DMAR (DMA Remapping) ACPI table presence required
  dmesg | grep -i iommu
  dmesg | grep -i dmar
  
  # Verify IOMMU groups
  find /sys/kernel/iommu_groups -type l | sort -V
  
  # Show device → group mapping
  for g in /sys/kernel/iommu_groups/*; do
    echo "Group ${g##*/}:"; ls $g/devices/; done
```

### 3.3 AMD IOMMU (AMD-Vi)

AMD's implementation uses similar concepts but different ACPI tables (IVRS — I/O Virtualization Reporting Structure) and data structures (Device Table, Command Buffer, Event Log, PPR Log).

```
AMD-Vi key structures:
  Device Table (DTE): 256 * 256 entries (BDF-indexed), 32 bytes each
    - TV bit: translation valid
    - Domain ID
    - Page Table Root Pointer
    - Interrupt Remapping Table Pointer
    - IOTLB enable, Snoop Disable, etc.
    
  Command Buffer: ring buffer for IOTLB invalidation commands
    INVALIDATE_DEVTAB_ENTRY
    INVALIDATE_IOMMU_PAGES
    INVALIDATE_IOTLB_PAGES
    COMPLETE_PPR_REQUEST
    
  Event Log: records faults (similar to VT-d fault log)
  PPR Log: Page Request Log for SVM (Shared Virtual Memory)
  
Boot params:
  amd_iommu=on
  amd_iommu=force_isolation   — force per-device isolation even for same group
  amd_iommu_dump              — dump IVRS table at boot
```

### 3.4 ARM SMMU (System Memory Management Unit)

ARM's SMMU is defined in the ARM SMMU specification (currently v3.x). It is used in all ARM-based servers (Graviton, Ampere, Neoverse) and mobile SoCs.

```
SMMU v3 Architecture:
  StreamID: identifies the device (analogous to PCIe BDF + PASID)
  SubstreamID: identifies address space within device (for PASID/SVA)
  
  Stream Table (linear or 2-level): indexed by StreamID
    STE (Stream Table Entry):
      - Config field: bypass / abort / translate
      - S1ContextPtr: pointer to CD (Context Descriptor)
      - S2TTB: Stage-2 page table base (for hypervisor use)
      
  Context Descriptor (CD): per-ASID state
    - TTB0: stage-1 page table base
    - ASID: address space ID (for TLB tagging)
    
  Command Queue (CQ): ring buffer, CPU → SMMU commands
    CFGI_STE_RANGE, TLBI_NH_ALL, SYNC, etc.
    
  Event Queue (EQ): SMMU → CPU fault events
  PRI Queue (PRQ): page request interface (for SVA)
  
Boot/DTS:
  iommu-map = <StreamID range &smmu context_id> in device tree
  or ACPI IORT table for server platforms
  
Linux driver: drivers/iommu/arm/arm-smmu-v3/
```

### 3.5 IOMMU Groups and the Isolation Guarantee

IOMMU groups are the **atomic unit of isolation**. All devices in a group share a domain (page table) and thus share memory access — you cannot isolate two devices in the same group from each other.

```
Group membership rules:
  - PCIe devices behind a switch with ACS (Access Control Services) disabled
    → entire switch subtree may be one group
  - Devices connected via legacy PCI bus → single group
  - PCIe device with no ACS-capable switch in path → isolated group (ideal)

ACS (Access Control Services):
  PCIe feature that enforces peer-to-peer isolation through switches.
  Without ACS: Device A on port 1 of switch can send TLPs directly to
               Device B on port 2, bypassing IOMMU entirely.
  With ACS:    All traffic forced through root complex → IOMMU sees it.
  
  Check ACS:
    setpci -s <BDF> CAP_EXP+0x28.w  (ACS capability register)
    lspci -vvv | grep -A5 "Access Control"
    
  Force ACS (pcie_acs_override — DANGEROUS, breaks IOMMU isolation semantics):
    pcie_acs_override=downstream,multifunction
    # Only for testing, NEVER in production security context
```

### 3.6 Shared Virtual Addressing (SVA) / PASID

Modern IOMMU hardware (VT-d 3.0+, SMMU v3.1+) supports **PASID (Process Address Space ID)**, enabling a device to directly use a process's virtual address space. This eliminates IOVA translation for accelerators.

```
SVA/PASID flow:
  1. Process p binds its mm (CR3/TTBR0) to device via iommu_sva_bind_device()
  2. Kernel programs PASID table entry with process page table root
  3. Process submits work to device using user virtual addresses directly
  4. Device DMA uses PASID in TLP prefix → IOMMU looks up PASID table
  5. IOMMU translates user VA → PA using process page tables
  
Security implications:
  + No IOVA pinning required → no memory pinning DoS attack surface
  + Device sees exact same VA as process (no translation artifact)
  - If process exits while device has outstanding DMA → IOMMU fault
    (Linux handles: iommu_sva_unbind_device on process exit via MMU notifier)
  - Page fault handling: SMMU v3 PRI (Page Request Interface) allows
    device-triggered page faults to be resolved by kernel (demand paging for DMA)
    
Kernel API:
  iommu_sva_bind_device(dev, mm, data)  → returns handle
  iommu_sva_unbind_device(handle)
  iommu_sva_get_pasid(handle)
  
Drivers using SVA: Intel QAT, ARM SMMUv3 with PRI, CXL devices
```

---

## 4. Linux DMA Subsystem Architecture

### 4.1 Layered Architecture

```
+---------------------------------------------------------------+
|                     Driver Code                               |
|  dma_alloc_coherent()  dma_map_single()  dma_map_sg()        |
+---------------------------------------------------------------+
|              DMA Mapping API (include/linux/dma-mapping.h)    |
|         Selects dma_map_ops based on device/platform          |
+---------------------------------------------------------------+
|           dma_map_ops implementations                         |
|  +------------------+  +------------------+  +-------------+ |
|  | iommu_dma_ops    |  | swiotlb_dma_ops  |  | nommu_ops   | |
|  | (IOMMU present)  |  | (bounce buffers) |  | (PA==IOVA)  | |
|  +------------------+  +------------------+  +-------------+ |
+---------------------------------------------------------------+
|   IOMMU Core (drivers/iommu/)   |   SWIOTLB (kernel/dma/)   |
|   iommu_map/unmap               |   swiotlb_tbl_map_single() |
|   iommu_iova_alloc              |   Bounce buffer management  |
+---------------------------------------------------------------+
|   Arch-specific cache ops       |   CMA (Contiguous Mem Alloc)|
|   arch_sync_dma_for_device()    |   dma_contiguous_reserve()  |
+---------------------------------------------------------------+
|             Physical Memory (DRAM)                            |
+---------------------------------------------------------------+
```

### 4.2 dma_map_ops Structure

The `dma_map_ops` struct is the polymorphic interface that makes the DMA subsystem portable:

```c
/* include/linux/dma-map-ops.h (simplified, Linux 6.x) */
struct dma_map_ops {
    /* Coherent allocation */
    void *(*alloc)(struct device *dev, size_t size,
                   dma_addr_t *dma_handle, gfp_t gfp,
                   unsigned long attrs);
    void  (*free)(struct device *dev, size_t size,
                  void *vaddr, dma_addr_t dma_handle,
                  unsigned long attrs);

    /* Streaming mapping */
    dma_addr_t (*map_page)(struct device *dev, struct page *page,
                           unsigned long offset, size_t size,
                           enum dma_data_direction dir,
                           unsigned long attrs);
    void       (*unmap_page)(struct device *dev, dma_addr_t dma_handle,
                             size_t size, enum dma_data_direction dir,
                             unsigned long attrs);

    /* Scatter-Gather */
    int  (*map_sg)(struct device *dev, struct scatterlist *sg,
                   int nents, enum dma_data_direction dir,
                   unsigned long attrs);
    void (*unmap_sg)(struct device *dev, struct scatterlist *sg,
                     int nents, enum dma_data_direction dir,
                     unsigned long attrs);

    /* Sync operations (cache maintenance) */
    void (*sync_single_for_cpu)(struct device *dev, dma_addr_t addr,
                                size_t size, enum dma_data_direction dir);
    void (*sync_single_for_device)(struct device *dev, dma_addr_t addr,
                                   size_t size, enum dma_data_direction dir);
    void (*sync_sg_for_cpu)(struct device *dev, struct scatterlist *sg,
                            int nents, enum dma_data_direction dir);
    void (*sync_sg_for_device)(struct device *dev, struct scatterlist *sg,
                               int nents, enum dma_data_direction dir);

    /* Address limits */
    u64 (*get_required_mask)(struct device *dev);
    size_t (*max_mapping_size)(struct device *dev);

    /* IOMMU-specific */
    int (*dma_supported)(struct device *dev, u64 mask);
    
    /* Attributes */
    unsigned long flags;
};
```

### 4.3 IOVA Allocator

When an IOMMU is present, every `dma_map_*` call must allocate an IOVA range for the device's page table. Linux uses a **red-black tree + free list** IOVA allocator (`lib/iova.c`).

```
IOVA domain per device (or per IOMMU group):
  - Managed as a struct iova_domain
  - Free list: per-CPU cached IOVAs (rcache) for hot-path performance
  - Allocation: best-fit from red-black tree of free ranges
  - Alignment: at least PAGE_SIZE; respects device DMA mask upper bound

Performance hot path (iommu_dma_map_page):
  1. iova_alloc() → get IOVA from rcache (per-CPU, very fast)
  2. iommu_map() → insert PTE into IOMMU page table
  3. flush IOMMU TLB if required (expensive on some HW)
  4. return IOVA as dma_addr_t to driver

IOVA TLB invalidation is the dominant overhead in high-IOPS paths.
Solutions:
  - Lazy invalidation (iommu=lazy): batch invalidations
  - IOMMU hardware queue-based invalidation (VT-d queued invalidation)
  - IOVA caching: reuse IOVAs without unmapping (for fixed-size buffers)
  - Huge page IOVAs: single TLB entry covers 2M or 1G range
```

### 4.4 DMA Attributes

DMA attributes modify behavior of the mapping API:

```c
/* include/linux/dma-mapping.h */
#define DMA_ATTR_WRITE_BARRIER          (1UL << 0)
#define DMA_ATTR_WEAK_ORDERING          (1UL << 1)
#define DMA_ATTR_WRITE_COMBINE          (1UL << 2)
#define DMA_ATTR_NON_CONSISTENT         (1UL << 3)  /* avoid cache flushes, driver manages */
#define DMA_ATTR_NO_KERNEL_MAPPING      (1UL << 4)  /* don't map into kernel VA */
#define DMA_ATTR_SKIP_CPU_SYNC          (1UL << 5)  /* no cache sync (batching) */
#define DMA_ATTR_FORCE_CONTIGUOUS       (1UL << 6)  /* physically contiguous */
#define DMA_ATTR_ALLOC_SINGLE_PAGES     (1UL << 7)  /* alloc 4K pages, not compound */
#define DMA_ATTR_NO_WARN                (1UL << 8)
#define DMA_ATTR_PRIVILEGED             (1UL << 9)  /* only for trusted devices */
```

---

## 5. DMA API — Coherent Memory

### 5.1 Coherent DMA Allocations

Coherent (a.k.a. consistent) DMA memory is visible to both CPU and device at all times without explicit sync. This is typically used for descriptor rings, completion queues, and small control structures.

```c
/**
 * dma_alloc_coherent - allocate consistent DMA memory
 * @dev:    device requesting the memory
 * @size:   size in bytes (will be rounded up to PAGE_SIZE)
 * @dma_handle: OUT — DMA address to program into device
 * @gfp:    allocation flags (GFP_KERNEL most common)
 *
 * Returns: kernel virtual address of allocated region, or NULL on failure
 *
 * The memory returned is:
 *   - Physically contiguous (guaranteed)
 *   - Cache-coherent with device
 *   - Zeroed
 *   - Mapped into kernel VA space
 *
 * Implementation path:
 *   iommu present: alloc pages → iommu_map → return kva + IOVA
 *   swiotlb:       alloc from bounce buffer pool → return kva + swiotlb PA
 *   no IOMMU:      alloc_pages → return kva + PA (PA == bus addr)
 */
void *dma_alloc_coherent(struct device *dev, size_t size,
                         dma_addr_t *dma_handle, gfp_t gfp);

void dma_free_coherent(struct device *dev, size_t size,
                       void *cpu_addr, dma_addr_t dma_handle);
```

**Internal allocation path (with IOMMU, x86_64):**

```
dma_alloc_coherent()
  → iommu_dma_alloc() [drivers/iommu/dma-iommu.c]
    → __iommu_dma_alloc_noncontiguous() or __iommu_dma_alloc()
      → alloc_pages_node() or CMA allocation
      → iommu_dma_alloc_iova() — get IOVA range
      → iommu_map_sg()         — map pages into IOMMU PT
      → dma_common_pages_remap() — map into kernel VA (vmalloc space)
    → returns (kva, iova)
```

**Attributes for coherent allocation:**

```c
/* No kernel VA mapping — device-only memory (e.g., device-local DRAM) */
void *dma_alloc_attrs(struct device *dev, size_t size,
                      dma_addr_t *dma_handle, gfp_t flag,
                      unsigned long attrs);

/* Example: write-combine mapping for BAR registers */
void *ptr = dma_alloc_attrs(dev, size, &dma_addr, GFP_KERNEL,
                             DMA_ATTR_WRITE_COMBINE);
```

### 5.2 When to Use Coherent vs. Streaming

```
Coherent DMA — use when:
  ✓ Descriptor rings (TX/RX rings for NICs, NVMe submission/completion queues)
  ✓ Shared control structures device and CPU both update frequently
  ✓ Small, long-lived allocations (< few pages)
  ✗ Avoid for large data buffers — coherent allocation is more expensive
    (may use CMA or special memory regions)

Streaming DMA — use when:
  ✓ Data plane buffers: packet payloads, disk sector data
  ✓ Large, short-lived allocations
  ✓ Scatter-gather I/O
  ✓ When CPU and device access the buffer alternately (not simultaneously)
  ✗ Never access the buffer CPU-side between map and unmap without sync
```

### 5.3 DMA Pool (dma_pool)

For many small coherent allocations of the same size, use `dma_pool`:

```c
/*
 * dma_pool: slab-like allocator for small DMA coherent allocations
 * Avoids per-allocation overhead; manages a pool of pages
 */
struct dma_pool *pool = dma_pool_create(
    "mydrv_desc",   /* name */
    dev,            /* device */
    64,             /* size of each allocation */
    64,             /* alignment (power of 2) */
    0               /* boundary: allocation won't cross this (0 = no constraint) */
);

/* Allocate from pool */
dma_addr_t dma_addr;
void *desc = dma_pool_zalloc(pool, GFP_KERNEL, &dma_addr);

/* Use desc / dma_addr ... */

/* Free back to pool */
dma_pool_free(pool, desc, dma_addr);

/* Destroy pool */
dma_pool_destroy(pool);
```

---

## 6. DMA API — Streaming

### 6.1 Single Buffer Streaming Map

```c
/**
 * dma_map_single - map a kernel-allocated buffer for DMA
 * @dev:    device
 * @ptr:    kernel virtual address of buffer
 * @size:   size in bytes
 * @dir:    DMA_TO_DEVICE / DMA_FROM_DEVICE / DMA_BIDIRECTIONAL
 *
 * Returns: DMA address (IOVA or PA) for programming into device descriptor
 *          or DMA_MAPPING_ERROR on failure
 *
 * After dma_map_single():
 *   - CPU MUST NOT access the buffer (or must call dma_sync_* first)
 *   - Device CAN access via returned DMA address
 *
 * Cache effects:
 *   DMA_TO_DEVICE:   Clean (flush) dirty CPU cache lines → device sees CPU writes
 *   DMA_FROM_DEVICE: Invalidate CPU cache lines → CPU will re-fetch from memory
 *   DMA_BIDIRECTIONAL: Both clean and invalidate
 */
dma_addr_t dma_map_single(struct device *dev, void *ptr,
                           size_t size, enum dma_data_direction dir);

/* Always check for error */
if (dma_mapping_error(dev, dma_addr)) {
    /* handle error: IOVA exhaustion, device mask constraint, etc. */
}

/**
 * dma_unmap_single - unmap and release the mapping
 * Must be called after device DMA completes (e.g., in interrupt handler)
 */
void dma_unmap_single(struct device *dev, dma_addr_t addr,
                      size_t size, enum dma_data_direction dir);
```

### 6.2 Sync Operations — Detailed Semantics

```c
/*
 * Ownership model:
 *
 *   CPU owns buffer:    can read/write freely, no sync needed
 *   Device owns buffer: CPU MUST NOT access; device has DMA access
 *
 * Transfer ownership CPU → Device:
 *   dma_sync_single_for_device(dev, addr, size, DMA_TO_DEVICE)
 *   (or this happens implicitly in dma_map_single with DMA_TO_DEVICE)
 *
 * Transfer ownership Device → CPU:
 *   dma_sync_single_for_cpu(dev, addr, size, DMA_FROM_DEVICE)
 *   (or this happens implicitly in dma_unmap_single)
 *
 * Partial sync (for large buffers where only a sub-range changes):
 *   dma_sync_single_range_for_cpu(dev, addr, offset, size, dir)
 *   dma_sync_single_range_for_device(dev, addr, offset, size, dir)
 */

/* Typical TX path (CPU → Device): */
void *buf = kmalloc(len, GFP_KERNEL);
fill_packet(buf, len);
dma_addr_t da = dma_map_single(dev, buf, len, DMA_TO_DEVICE);
BUG_ON(dma_mapping_error(dev, da));
program_descriptor(dev, da, len);
ring_doorbell(dev);
/* ... wait for completion interrupt ... */
dma_unmap_single(dev, da, len, DMA_TO_DEVICE);
process_completion();
kfree(buf);

/* Typical RX path (Device → CPU): */
void *buf = kmalloc(len, GFP_KERNEL);
dma_addr_t da = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
BUG_ON(dma_mapping_error(dev, da));
post_rx_descriptor(dev, da, len);
/* device fills buffer via DMA */
/* ... completion interrupt arrives ... */
dma_unmap_single(dev, da, len, DMA_FROM_DEVICE);
process_received_data(buf, actual_len);  /* safe to read now */
kfree(buf);
```

### 6.3 Page-Based Mapping

```c
/* dma_map_page: map a struct page for DMA (avoids kmap overhead) */
dma_addr_t dma_map_page(struct device *dev, struct page *page,
                         unsigned long offset, size_t size,
                         enum dma_data_direction dir);

void dma_unmap_page(struct device *dev, dma_addr_t addr,
                    size_t size, enum dma_data_direction dir);

/* Use case: network stack, skb fragments use struct page + offset */
struct skb_frag_struct *frag = &skb_shinfo(skb)->frags[i];
dma_addr_t da = dma_map_page(dev,
    skb_frag_page(frag),
    frag->bv_offset,
    skb_frag_size(frag),
    DMA_TO_DEVICE);
```

### 6.4 Scatter-Gather DMA

Scatter-gather allows mapping a logically contiguous I/O buffer that is physically fragmented. This is the standard for high-performance I/O (NVMe, 10G+ NICs).

```c
/* struct scatterlist: represents one physically-contiguous segment */
struct scatterlist {
    unsigned long   page_link;   /* encoded struct page * + flags */
    unsigned int    offset;      /* offset within page */
    unsigned int    length;      /* length of this segment */
    dma_addr_t      dma_address; /* set by dma_map_sg() */
    unsigned int    dma_length;  /* DMA length (may differ from length after coalescing) */
};

/* Build scatter list from struct pages */
struct scatterlist *sg;
int nsegs = ...; /* number of segments */
sg = kmalloc_array(nsegs, sizeof(*sg), GFP_KERNEL);
sg_init_table(sg, nsegs);

for (i = 0; i < nsegs; i++) {
    sg_set_page(&sg[i], pages[i], PAGE_SIZE, 0);
}
sg_mark_end(&sg[nsegs - 1]);

/* Map: returns number of DMA segments (may be <= nsegs due to coalescing) */
int mapped = dma_map_sg(dev, sg, nsegs, DMA_FROM_DEVICE);
if (!mapped) {
    /* error: too many segments, IOVA exhaustion, etc. */
}

/* Program device descriptors using mapped sg */
struct scatterlist *s;
int i;
for_each_sg(sg, s, mapped, i) {
    program_prp_entry(dev, sg_dma_address(s), sg_dma_len(s));
}

/* After device completion: */
dma_unmap_sg(dev, sg, nsegs, DMA_FROM_DEVICE);
```

#### S/G Coalescing

The IOMMU can coalesce adjacent pages into single large IOMMU mappings, reducing descriptor count and potentially TLB pressure. Linux does this transparently in `iommu_dma_map_sg()`.

```
Example: 4 physically adjacent pages
  sg[0]: page 0x1000, len 4096
  sg[1]: page 0x2000, len 4096  ← physically adjacent to sg[0]
  sg[2]: page 0x3000, len 4096  ← physically adjacent
  sg[3]: page 0x5000, len 4096  ← NOT adjacent

  dma_map_sg() with IOMMU:
    IOVA allocation: one 12K IOVA + one 4K IOVA
    mapped = 2  (two DMA segments returned)
    sg_dma_address(sg[0]) = iova_base, sg_dma_len(sg[0]) = 12288
    sg_dma_address(sg[3]) = iova_base2, sg_dma_len(sg[3]) = 4096
```

### 6.5 dma_map_sg Attributes for Performance

```c
/* Skip CPU sync (driver manages cache manually or knows buffer is WC) */
dma_map_sg_attrs(dev, sg, nsegs, dir, DMA_ATTR_SKIP_CPU_SYNC);

/* Unmap without TLB flush (batch unmaps) — use with iommu=lazy */
dma_unmap_sg_attrs(dev, sg, nsegs, dir, DMA_ATTR_SKIP_CPU_SYNC);

/* Force IOMMU huge pages for large S/G (kernel 5.15+) */
/* Achieved via iommu_map with IOMMU_NO_UNMAP or large page alignment */
```

---

## 7. DMA Engine Subsystem

### 7.1 Overview

The DMA Engine subsystem (`drivers/dma/`, `include/linux/dmaengine.h`) provides a generic API for offloading memory copy, XOR, fill, and CRC operations to dedicated DMA hardware (Intel CBDMA/IOAT, ARM PL330, Cadence DMA, etc.).

```
DMA Engine Use Cases:
  - Memory-to-memory copy (async_memcpy, kernel crypto)
  - Memory-to-memory XOR (RAID-5/6 parity via async_xor)
  - Descriptor-based I/O (SATA/AHCI, network offload)
  - Memory fill / memory test
  - CRC computation offload
  
Architecture:
  +-------------------+     +-------------------+
  |  Client (driver)  |     |  Client (driver)  |
  +--------+----------+     +----------+--------+
           |                           |
  +--------v---------------------------v--------+
  |          DMA Engine Core API                |
  |  dma_request_chan()  dmaengine_submit()      |
  |  dma_async_issue_pending()                  |
  +--------+----------------------------+--------+
           |                            |
  +--------v--------+       +-----------v-------+
  | Intel IOAT DMA  |       |  ARM PL330 DMA    |
  | (drivers/dma/   |       |  (drivers/dma/    |
  |  ioat/)         |       |  pl330.c)         |
  +-----------------+       +-------------------+
```

### 7.2 DMA Engine API

```c
/* Step 1: request a DMA channel */
struct dma_chan *chan = dma_request_chan(dev, "dma0");  /* by DT/ACPI name */
/* or */
struct dma_chan *chan = dma_find_channel(DMA_MEMCPY);  /* by capability */

/* Step 2: prepare a descriptor */
struct dma_async_tx_descriptor *desc;

/* Memory copy */
desc = dmaengine_prep_dma_memcpy(chan,
    dst_dma,    /* destination DMA address */
    src_dma,    /* source DMA address */
    len,        /* bytes to copy */
    DMA_PREP_INTERRUPT | DMA_CTRL_ACK);

/* Set completion callback */
desc->callback = my_dma_callback;
desc->callback_param = my_data;

/* Step 3: submit to channel queue */
dma_cookie_t cookie = dmaengine_submit(desc);
if (dma_submit_error(cookie)) { /* handle */ }

/* Step 4: issue pending transfers */
dma_async_issue_pending(chan);

/* Step 5: wait for completion (polling or callback) */
/* Option A: poll */
enum dma_status status;
do {
    status = dma_async_is_tx_complete(chan, cookie, NULL, NULL);
} while (status == DMA_IN_PROGRESS);

/* Option B: wait with timeout */
long ret = dma_wait_for_async_tx(desc);  /* waits on completion */

/* Release channel */
dma_release_channel(chan);
```

### 7.3 Intel IOAT/CBDMA (Data Streaming Accelerator — DSA)

Intel's DSA (Data Streaming Accelerator, successor to CBDMA/IOAT) is present on Intel Xeon Scalable (SPR+). It provides:

```
DSA Capabilities:
  - Memory copy (memmove-equivalent, cache-friendly)
  - Memory fill
  - Memory compare + write (compare and store)
  - CRC32 computation
  - Cache flush (CLFLUSH offload)
  - Batch processing (submit list of work descriptors atomically)
  
Key feature: Shared Virtual Memory (SVM) support
  - DSA can operate on user virtual addresses directly (PASID-based)
  - No pinning required for user buffers
  
Linux driver: drivers/dma/idxd/
Userspace library: accel-config, SPDK (Storage Performance Development Kit)

DSA Work Descriptor (WD) format:
  Opcode: 1 byte (MEMMOVE=0x03, FILL=0x06, CRC32C=0x10...)
  Flags: completion interrupt, fault-on-error, etc.
  Completion Record Address: where hardware writes status
  Source/Destination: DMA addresses or user VAs (with PASID)
  Transfer Size: bytes
```

---

## 8. Bounce Buffers and Zone DMA

### 8.1 Why Bounce Buffers Exist

When a device's DMA mask cannot reach the physical address of a buffer, or when there is no IOMMU, the kernel must use a **bounce buffer**: a buffer in a DMA-reachable zone, with data copied to/from the actual buffer.

```
Scenario: 32-bit DMA device, buffer at PA = 0x1_0000_0000 (4 GiB + 0)
  Device DMA mask: 0xFFFFFFFF (cannot address above 4 GiB)
  
  Without bounce buffer: DMA_MAPPING_ERROR
  With bounce buffer (SWIOTLB):
    1. Allocate bounce buffer in first 4 GiB: PA = 0x8000_0000
    2. Copy data CPU → bounce buffer (memcpy)
    3. Program device with bounce buffer PA: 0x8000_0000
    4. Device DMA completes to bounce buffer
    5. Copy data bounce buffer → original buffer (memcpy)
    6. Return DMA_MAPPING_ERROR avoided; original buffer usable
```

### 8.2 SWIOTLB — Software I/O TLB

SWIOTLB (`kernel/dma/swiotlb.c`) is Linux's bounce buffer implementation:

```
SWIOTLB memory layout:
  - Allocated at boot from low memory (below 4 GiB for 32-bit devices)
  - Default size: 64 MiB (configurable via swiotlb=<pages> or swiotlb=force)
  - Divided into fixed-size slots (2K default per slot, configurable)
  - Bitmap tracks free/used slots
  
Boot parameter:
  swiotlb=<nslabs>   — number of slots (total = nslabs * 2048 bytes)
  swiotlb=force      — always use swiotlb even if IOMMU present
  swiotlb=noforce    — never use (dangerous if 32-bit devices present)
  
  # For confidential computing (SEV, TDX): swiotlb is mandatory
  # because encrypted guest memory is not directly accessible by hypervisor/device
  
Configuration check:
  dmesg | grep -i swiotlb
  cat /proc/iomem | grep SWIOTLB
  
Tuning:
  # Increase swiotlb size for high-throughput 32-bit DMA or confidential VMs
  # /boot/grub/grub.cfg or /etc/default/grub:
  GRUB_CMDLINE_LINUX="swiotlb=65536"  # 65536 * 2K = 128 MiB
```

### 8.3 Confidential Computing and SWIOTLB

In confidential VMs (AMD SEV, Intel TDX, ARM CCA), guest memory is encrypted. When a para-virtual device (virtio) does DMA, the hypervisor must be able to access the data — but guest memory is encrypted with a key unknown to the hypervisor.

```
Solution: Shared (unencrypted) DMA bounce buffers

AMD SEV:
  Guest memory: encrypted with guest-specific key (C-bit set in PTE)
  Shared memory: unencrypted (C-bit cleared), visible to hypervisor
  
  Flow:
    1. Guest allocates bounce buffer in shared (unencrypted) memory
    2. For DMA_TO_DEVICE: copy data to bounce buffer (now plaintext)
    3. virtio device DMA: reads from shared bounce buffer
    4. For DMA_FROM_DEVICE: device writes to shared bounce buffer
    5. Copy from bounce buffer → encrypted guest memory
  
  Linux: mem_encrypt_active() → force swiotlb
  CONFIG_AMD_MEM_ENCRYPT, CONFIG_INTEL_TDX_GUEST
  
Intel TDX:
  Similar mechanism: "Shared" bit in SEPT (Secure EPT)
  tdx_shared_mask() marks pages as shared for DMA use
```

---

## 9. PCIe P2P DMA

### 9.1 Peer-to-Peer DMA

P2P DMA allows two PCIe devices to transfer data directly between each other's BAR (Base Address Register) memory or system memory, bypassing the CPU and host memory.

```
Traditional data path (e.g., GPU ← NIC):
  NIC → PCIe → CPU/DRAM → CPU copy → DRAM → PCIe → GPU
  CPU is involved; two PCIe traversals; latency ~10–50μs

P2P DMA path:
  NIC → PCIe switch → GPU
  CPU not involved; single PCIe traversal; latency ~2–5μs
  No DRAM bandwidth consumed
  
Requirements:
  1. Both devices behind a common PCIe switch with ACS disabled (or explicit P2P support)
  2. Devices support P2P DMA (most modern GPUs, NVMe, NICs do)
  3. Kernel: CONFIG_PCI_P2PDMA
  4. No IOMMU (or IOMMU configured for P2P)
  
P2P limitations:
  - Root complex may or may not support forwarding P2P TLPs
  - AMD platforms: generally support P2P through root complex
  - Intel platforms: often do NOT route P2P through root complex
    → requires switch with P2P forwarding
  - Distance: same switch subtree only (same IOMMU group usually)
```

### 9.2 Linux P2PDMA API

```c
/* Register a device's BAR as P2P memory */
int pci_p2pdma_add_resource(struct pci_dev *pdev, int bar,
                             size_t size, u64 offset);

/* Query if P2P is possible between two devices */
int pci_p2pdma_distance_many(struct pci_dev *provider,
                              struct device **clients, int num_clients,
                              bool verbose);

/* Allocate from P2P memory pool */
void *pci_alloc_p2pmem(struct pci_dev *pdev, size_t size);
void pci_free_p2pmem(struct pci_dev *pdev, void *addr, size_t size);

/* Get DMA address of P2P memory for a target device */
dma_addr_t pci_p2pmem_virt_to_bus(struct pci_dev *pdev, void *addr);

/* Map S/G list for P2P */
int pci_p2pdma_map_sg_attrs(struct device *dev, struct scatterlist *sg,
                             int nents, enum dma_data_direction dir,
                             unsigned long attrs);
```

---

## 10. SR-IOV and DMA Isolation

### 10.1 SR-IOV Architecture

SR-IOV (Single Root I/O Virtualization) enables a single PCIe device to appear as multiple independent devices (Virtual Functions, VFs) to VMs or containers.

```
SR-IOV PCIe device:
  Physical Function (PF): full PCIe device, has full config space
  Virtual Functions (VF): lightweight, share hardware with PF
    Each VF has own:
      - PCI config space (own BDF)
      - BARs (mapped to partition of PF HW resources)
      - MSI-X vectors
    VFs share:
      - PHY (physical layer)
      - Packet processing hardware (queues assigned per-VF)

IOMMU and SR-IOV:
  Each VF gets its own IOMMU domain (if platform supports it)
  VF assigned to VM: VF's IOMMU domain = VM's nested IOMMU domain
  
  VM can DMA only to memory in its EPT (Extended Page Table)
  If VF DMA targets outside VM's EPT → IOMMU fault → VM killed, not host
```

### 10.2 VF Assignment Security Concerns

```
Attack surface for SR-IOV + IOMMU:
  1. PF/VF config space attacks: VM writes to PF BARs via VF (if firmware bug)
  2. IOMMU group confusion: VF and PF in same group → no isolation
     (correct: each VF should have own IOMMU group in modern HW)
  3. Interrupt remapping: without IR, MSIs from VF can spoof LAPIC vectors
     Mitigation: iommu=pt combined with interrupt remapping (IR)
  4. PCIe FLR (Function Level Reset): VM triggers FLR on VF → affects PF state
  
Mitigations:
  - Ensure VT-d Interrupt Remapping is enabled: dmesg | grep "Enabled IRQ remapping"
  - Verify each VF in own IOMMU group:
    ls /sys/bus/pci/devices/<VF_BDF>/iommu_group/devices/
    (should contain ONLY the VF)
  - Use vfio-pci driver for VF assignment, not legacy KVM device assignment
  - Disable PCIe peer-to-peer for VFs (ACS should be enabled on switch ports)
```

---

## 11. VFIO — Userspace DMA

### 11.1 VFIO Architecture

VFIO (Virtual Function I/O) allows unprivileged userspace to directly program device DMA — safely, by mediating through IOMMU.

```
VFIO components:
  /dev/vfio/vfio              — VFIO container (IOMMU domain)
  /dev/vfio/<group_id>        — IOMMU group device
  
  vfio-pci driver:            — handles PCI config space, BAR mmap, IRQs
  vfio_iommu_type1 driver:    — manages IOMMU mappings for userspace
  
Typical VFIO flow (DPDK, QEMU device passthrough):
  1. Unbind device from kernel driver: echo vfio-pci > /sys/bus/pci/devices/<BDF>/driver_override
  2. Bind to vfio-pci: echo <BDF> > /sys/bus/pci/drivers/vfio-pci/bind
  3. Open /dev/vfio/<group>, /dev/vfio/vfio
  4. VFIO_GROUP_GET_DEVICE_FD: get device FD
  5. VFIO_IOMMU_MAP_DMA: map userspace VA range into IOMMU (pinned pages)
  6. Mmap BAR: VFIO_DEVICE_GET_REGION_INFO + mmap()
  7. Program device DMA descriptors with IOVA (from step 5)
  8. Device DMA → IOMMU translates IOVA → PA → DRAM
```

### 11.2 VFIO DMA Mapping Internals

```c
/* Userspace: map a virtual address range for DMA */
struct vfio_iommu_type1_dma_map dma_map = {
    .argsz = sizeof(dma_map),
    .flags = VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE,
    .vaddr = (uint64_t)userspace_buffer,   /* user VA */
    .iova  = desired_iova,                 /* IOVA to program into device */
    .size  = buffer_size,
};
ioctl(container_fd, VFIO_IOMMU_MAP_DMA, &dma_map);

/*
 * Kernel side (vfio_iommu_type1.c):
 *   1. pin_user_pages_fast() — pin PA, get struct pages
 *   2. iommu_map() — insert (IOVA → PA) into IOMMU page table
 *   3. Track mapping in vfio_dma tree (for unmap + accounting)
 *
 * On VFIO_IOMMU_UNMAP_DMA:
 *   1. iommu_unmap() — remove from IOMMU PT
 *   2. iommu_iotlb_sync() — flush IOMMU TLB
 *   3. unpin_user_pages() — release page pins
 */
```

### 11.3 VFIO Security Model

```
Security guarantees:
  ✓ Device cannot access memory outside its VFIO IOMMU domain
  ✓ Multiple containers → multiple isolated IOMMU domains
  ✓ BAR access via mmap (kernel validates size/offset)
  ✓ Interrupt remapping (prevents IRQ injection attacks)

Attack surface:
  - Malicious guest can exhaust IOVA space (DoS) → limit mappings
  - Huge page IOMMU mappings may include unintended pages (alignment)
  - IOMMU TLB shootdown latency creates window (mitigated by strict mode)
  - If IOMMU is disabled (iommu=pt) → VFIO provides zero isolation!
  
Verification:
  # Confirm IOMMU is active for VFIO container
  cat /sys/kernel/iommu_groups/<n>/type  # should be "DMA" not "identity"
  
  # Check vfio_iommu_type1 strict mode
  cat /sys/module/vfio_iommu_type1/parameters/dma_entry_limit  # default 65535
```

---

## 12. DMA and Virtualization

### 12.1 Nested IOMMU (KVM + VFIO Passthrough)

```
Two-stage address translation for VM device passthrough:

Stage 1 (guest IOMMU): GIOVA → GPA  (Guest Physical Address)
  - Guest programs IOMMU page tables (guest thinks it controls HW)
  - For virtio: guest maps GPA, hypervisor intercepts

Stage 2 (host IOMMU):  GPA → HPA    (Host Physical Address)
  - Host IOMMU translates GPA → HPA
  - If guest programs GIOVA, nested mode: GIOVA → GPA → HPA

Hardware support required:
  Intel: VT-d scalable mode (context entry with PASID support, nested paging)
  AMD:   IOMMU with guest CR3 tracking (nested paging)
  ARM:   SMMUv3 stage-2 only or nested (stage-1 + stage-2)
  
Without hardware nesting:
  Hypervisor shadows IOMMU page tables (expensive: every guest IOMMU write → VMExit)
  
With hardware nesting:
  Guest writes to shadow IOMMU PT → hardware walks both levels
  No VMExit per mapping → ~10x faster passthrough I/O setup
```

### 12.2 virtio and DMA

virtio devices use shared memory (split or packed virtqueues) for DMA-like I/O. In bare-metal VMs, virtio DMA goes through the SWIOTLB (in confidential VMs) or directly maps GPA → HPA.

```
virtio virtqueue descriptor:
  struct virtq_desc {
      __le64 addr;    /* GPA of buffer */
      __le32 len;     /* length */
      __le16 flags;   /* VIRTQ_DESC_F_NEXT, VIRTQ_DESC_F_WRITE, VIRTQ_DESC_F_INDIRECT */
      __le16 next;    /* next descriptor index */
  };

Available ring:  driver writes descriptor indices here
Used ring:       device writes completed descriptor indices + length here

DMA flow (non-confidential):
  Guest driver: dma_map_single(GPA of buffer) → GPA (no IOMMU in guest by default)
  Hypervisor (QEMU): GPA → HPA via EPT
  virtio device (emulated or vhost): accesses HPA directly

DMA flow (confidential VM, SEV):
  Guest driver: dma_map_single → allocates from swiotlb (shared unencrypted) → returns shared GPA
  Copy: encrypted guest buffer → unencrypted swiotlb buffer
  Hypervisor: accesses unencrypted swiotlb GPA → HPA
```

---

## 13. eBPF DMA Observability

### 13.1 Why eBPF for DMA Tracing

DMA paths are in the critical performance hot path and security boundary of every I/O-intensive system. eBPF provides:

- Zero-overhead when not active (JIT-compiled probes, disabled by default)
- No kernel recompilation required
- Ability to trace both map/unmap events and IOMMU faults
- Integration with BPF maps for aggregation and histograms

### 13.2 Key Kernel Tracepoints and Kprobes for DMA

```bash
# List DMA-related tracepoints
sudo perf list 'dma:*'
sudo ls /sys/kernel/debug/tracing/events/dma/

# Available tracepoints (kernel 5.15+):
#   dma_map_page, dma_unmap_page, dma_alloc, dma_free
#   swiotlb_bounced (when bounce buffer is used)
#   iommu_map, iommu_unmap, iommu_map_range
#   iommu_group_add, iommu_attach_device

# Key functions to kprobe:
#   dma_map_single_attrs
#   dma_unmap_single_attrs
#   dma_map_sg_attrs
#   swiotlb_tbl_map_single
#   iommu_map
#   iommu_unmap
```

### 13.3 eBPF Program: DMA Map Latency Histogram

```c
/* dma_latency.bpf.c */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

/* Histogram: dma_map_single latency in nanoseconds */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, u32);    /* tid */
    __type(value, u64);  /* entry timestamp */
} start_ts SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HISTOGRAM);  /* log2 histogram */
    __uint(max_entries, 64);
    __type(key, u32);
    __type(value, u64);
} latency_hist SEC(".maps");

/*
 * We use BPF_MAP_TYPE_ARRAY as a log2 histogram manually since
 * BPF_MAP_TYPE_HISTOGRAM is not a real type; we simulate it.
 */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 64);   /* 64 buckets for log2 histogram */
    __type(key, u32);
    __type(value, u64);
} lat_hist SEC(".maps");

SEC("kprobe/dma_map_single_attrs")
int BPF_KPROBE(dma_map_entry, struct device *dev, void *ptr,
               size_t size, int dir, unsigned long attrs)
{
    u32 tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    u64 ts = bpf_ktime_get_ns();
    bpf_map_update_elem(&start_ts, &tid, &ts, BPF_ANY);
    return 0;
}

SEC("kretprobe/dma_map_single_attrs")
int BPF_KRETPROBE(dma_map_exit, dma_addr_t ret)
{
    u32 tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    u64 *tsp = bpf_map_lookup_elem(&start_ts, &tid);
    if (!tsp) return 0;

    u64 delta = bpf_ktime_get_ns() - *tsp;
    bpf_map_delete_elem(&start_ts, &tid);

    /* Log2 bucket */
    u32 bucket = 0;
    u64 v = delta;
    while (v > 1 && bucket < 63) { v >>= 1; bucket++; }

    u64 *cnt = bpf_map_lookup_elem(&lat_hist, &bucket);
    if (cnt) {
        __sync_fetch_and_add(cnt, 1);
    } else {
        u64 one = 1;
        bpf_map_update_elem(&lat_hist, &bucket, &one, BPF_NOEXIST);
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 13.4 eBPF Program: SWIOTLB Bounce Detection

```c
/* swiotlb_trace.bpf.c — detect when bounce buffers are being used */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct bounce_event {
    u64  timestamp;
    u32  pid;
    char comm[16];
    u64  orig_addr;   /* original (high) physical address */
    u64  tlb_addr;    /* swiotlb (bounce) address */
    u32  size;
    u32  dir;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(u32));
    __uint(value_size, sizeof(u32));
} events SEC(".maps");

/* Tracepoint: swiotlb_bounced */
SEC("tracepoint/swiotlb/swiotlb_bounced")
int trace_swiotlb_bounced(struct trace_event_raw_swiotlb_bounced *ctx)
{
    struct bounce_event ev = {};
    ev.timestamp = bpf_ktime_get_ns();
    ev.pid       = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));
    ev.orig_addr = ctx->dma_mask;   /* field names vary by kernel version */
    ev.size      = ctx->size;
    ev.dir       = ctx->dir;

    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                          &ev, sizeof(ev));
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 13.5 eBPF Program: IOMMU Fault Monitoring

```c
/* iommu_fault.bpf.c — monitor IOMMU page faults in real time */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct iommu_fault_event {
    u64  timestamp;
    u32  type;           /* IOMMU_FAULT_DMA_UNRECOV or PAGE_REQ */
    u64  iova;           /* faulting IOVA */
    u64  perm;           /* IOMMU_FAULT_PERM_READ/WRITE/EXEC */
    u32  pasid;
    char dev_name[32];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);   /* 1 MiB ring buffer */
} fault_ring SEC(".maps");

/* Kprobe iommu_report_device_fault */
SEC("kprobe/iommu_report_device_fault")
int BPF_KPROBE(kprobe_iommu_fault, struct device *dev,
               struct iommu_fault *fault)
{
    struct iommu_fault_event *ev;
    ev = bpf_ringbuf_reserve(&fault_ring, sizeof(*ev), 0);
    if (!ev) return 0;

    ev->timestamp = bpf_ktime_get_ns();
    ev->type  = BPF_CORE_READ(fault, type);
    ev->iova  = BPF_CORE_READ(fault, event.addr);
    ev->perm  = BPF_CORE_READ(fault, event.perm);
    ev->pasid = BPF_CORE_READ(fault, event.pasid);

    /* Read device name */
    const char *name = BPF_CORE_READ(dev, kobj.name);
    bpf_probe_read_kernel_str(ev->dev_name, sizeof(ev->dev_name), name);

    bpf_ringbuf_submit(ev, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 13.6 eBPF Userspace Loader (C)

```c
/* dma_trace_loader.c */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include "dma_latency.skel.h"   /* generated by bpftool gen skeleton */

static volatile bool running = true;

static void sig_handler(int sig) { running = false; }

int main(void) {
    struct dma_latency_bpf *skel;
    int err;

    /* Load and verify BPF application */
    skel = dma_latency_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to load BPF skeleton\n");
        return 1;
    }

    /* Attach kprobes */
    err = dma_latency_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF programs: %d\n", err);
        goto cleanup;
    }

    signal(SIGINT, sig_handler);
    printf("Tracing DMA map latency... Ctrl-C to stop\n");

    while (running) {
        sleep(1);
        printf("\n--- DMA map_single latency histogram (ns) ---\n");
        printf("%-10s %-10s %s\n", "bucket_ns", "count", "bar");

        for (int i = 0; i < 64; i++) {
            int key = i;
            __u64 count = 0;
            bpf_map__lookup_elem(skel->maps.lat_hist,
                                 &key, sizeof(key),
                                 &count, sizeof(count), 0);
            if (count == 0) continue;
            u64 lo = (i == 0) ? 0 : (1ULL << (i-1));
            u64 hi = 1ULL << i;
            printf("[%6llu-%6llu]: %-10llu |", lo, hi, count);
            int bars = count > 40 ? 40 : (int)count;
            for (int b = 0; b < bars; b++) putchar('#');
            putchar('\n');
        }
    }

cleanup:
    dma_latency_bpf__destroy(skel);
    return err;
}
```

### 13.7 bpftrace One-Liners for DMA

```bash
# Count dma_map_single calls per device driver (by comm name)
sudo bpftrace -e '
kprobe:dma_map_single_attrs {
    @[comm] = count();
}'

# Measure dma_map_sg latency (microseconds histogram)
sudo bpftrace -e '
kprobe:dma_map_sg_attrs  { @start[tid] = nsecs; }
kretprobe:dma_map_sg_attrs /@start[tid]/ {
    @lat_us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'

# Detect IOMMU faults (requires iommu_report_device_fault symbol)
sudo bpftrace -e '
kprobe:iommu_report_device_fault {
    printf("IOMMU FAULT: dev=%s time=%lld\n",
           ((struct device *)arg0)->kobj.name, nsecs);
}'

# Count swiotlb bounce buffer usage per second
sudo bpftrace -e '
tracepoint:swiotlb:swiotlb_bounced {
    @bounces = count();
}
interval:s:1 {
    print(@bounces); clear(@bounces);
}'

# Track DMA allocation sizes (coherent)
sudo bpftrace -e '
kprobe:dma_alloc_attrs {
    @size_hist = hist(arg1);   /* arg1 = size */
}'

# Find which processes trigger most DMA mappings
sudo bpftrace -e '
kprobe:dma_map_page_attrs {
    @[pid, comm] = count();
}
END { print(@); }'
```

### 13.8 eBPF for DMA Security Monitoring

```c
/*
 * dma_security_monitor.bpf.c
 *
 * LSM-style monitoring: detect anomalous DMA patterns
 * - Large single coherent allocations (potential memory hoarding DoS)
 * - High-frequency DMA map/unmap (IOVA exhaustion attempt)
 * - DMA to/from kernel text addresses (requires knowing kernel text PA)
 */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define ALERT_LARGE_ALLOC_THRESHOLD  (64 * 1024 * 1024ULL)  /* 64 MiB */
#define ALERT_MAP_RATE_THRESHOLD     10000  /* maps per second */

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, u64);
} map_counter SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} alerts SEC(".maps");

struct alert_event {
    u64  ts;
    u32  pid;
    char comm[16];
    u32  alert_type;
    u64  value;
};

SEC("kprobe/dma_alloc_attrs")
int kprobe_dma_alloc(struct pt_regs *ctx)
{
    size_t size = (size_t)PT_REGS_PARM2(ctx);

    if (size >= ALERT_LARGE_ALLOC_THRESHOLD) {
        struct alert_event *ev = bpf_ringbuf_reserve(&alerts, sizeof(*ev), 0);
        if (ev) {
            ev->ts         = bpf_ktime_get_ns();
            ev->pid        = bpf_get_current_pid_tgid() >> 32;
            ev->alert_type = 1;  /* LARGE_ALLOC */
            ev->value      = size;
            bpf_get_current_comm(&ev->comm, sizeof(ev->comm));
            bpf_ringbuf_submit(ev, 0);
        }
    }

    u32 key = 0;
    u64 *cnt = bpf_map_lookup_elem(&map_counter, &key);
    if (cnt) __sync_fetch_and_add(cnt, 1);

    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 14. C Driver Implementation — End-to-End

### 14.1 Minimal PCIe DMA Driver Skeleton

```c
/* mydev_dma.c — production-grade PCIe DMA driver skeleton
 *
 * Demonstrates:
 *   - PCI init, MMIO mapping, bus mastering
 *   - DMA mask setup
 *   - Coherent descriptor ring allocation
 *   - Streaming DMA for data buffers
 *   - Scatter-gather DMA
 *   - MSI-X interrupt handling
 *   - IOMMU-aware operation
 *   - Error paths and cleanup
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/dmapool.h>
#include <linux/interrupt.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/completion.h>
#include <linux/io.h>
#include <linux/scatterlist.h>

/* ------------------------------------------------------------------ */
/* Device constants                                                     */
/* ------------------------------------------------------------------ */
#define MYDEV_VENDOR_ID      0x1234
#define MYDEV_DEVICE_ID      0x5678
#define MYDEV_BAR            0
#define MYDEV_NUM_QUEUES     4
#define MYDEV_DESC_COUNT     256     /* power of 2 */
#define MYDEV_DESC_SIZE      64      /* bytes per descriptor */
#define MYDEV_MAX_SG_SEGS    128

/* MMIO register offsets */
#define REG_CTRL             0x00
#define REG_STATUS           0x04
#define REG_DESC_BASE_LO     0x08
#define REG_DESC_BASE_HI     0x0C
#define REG_DESC_COUNT       0x10
#define REG_DOORBELL         0x14
#define REG_IRQ_STATUS       0x18
#define REG_IRQ_CLEAR        0x1C

/* Control register bits */
#define CTRL_DMA_ENABLE      BIT(0)
#define CTRL_INT_ENABLE      BIT(1)
#define CTRL_RESET           BIT(31)

/* ------------------------------------------------------------------ */
/* Data structures                                                      */
/* ------------------------------------------------------------------ */

/* Hardware DMA descriptor (matches device hardware layout) */
struct mydev_desc {
    __le64  src_addr;      /* DMA address of source data */
    __le64  dst_addr;      /* DMA address of dest (or 0 for Rx) */
    __le32  length;        /* transfer length in bytes */
    __le32  flags;         /* MYDEV_DESC_F_* flags */
    __le64  completion;    /* written by HW on completion (status + length) */
} __packed;

#define MYDEV_DESC_F_INTERRUPT  BIT(0)   /* generate interrupt on completion */
#define MYDEV_DESC_F_WRITE      BIT(1)   /* device writes to memory (Rx) */

/* Per-queue state */
struct mydev_queue {
    /* Descriptor ring — coherent DMA */
    struct mydev_desc  *desc_ring;      /* kernel VA */
    dma_addr_t          desc_ring_dma;  /* DMA address programmed into HW */
    size_t              desc_ring_size;

    /* Head/tail for producer-consumer management */
    u32                 head;           /* producer (CPU side) */
    u32                 tail;           /* consumer (HW side, updated on completion) */

    /* Per-descriptor completion tracking */
    struct {
        struct scatterlist *sg;
        int                 nents;
        void               *buf;        /* for single mappings */
        dma_addr_t          buf_dma;
        size_t              buf_size;
        enum dma_data_direction dir;
        struct completion   done;
    } inflight[MYDEV_DESC_COUNT];

    /* Sync */
    spinlock_t  lock;
    int         idx;
};

/* Device private data */
struct mydev {
    struct pci_dev         *pdev;
    void __iomem           *mmio_base;
    resource_size_t         mmio_len;

    /* MSI-X */
    int                     num_vectors;
    struct msix_entry       msix[MYDEV_NUM_QUEUES];

    /* DMA queues */
    struct mydev_queue      queues[MYDEV_NUM_QUEUES];

    /* DMA pool for small coherent allocations */
    struct dma_pool        *desc_pool;
};

/* ------------------------------------------------------------------ */
/* Helper: MMIO accessors                                              */
/* ------------------------------------------------------------------ */
static inline u32 mydev_rd32(struct mydev *dev, u32 reg)
{
    return ioread32(dev->mmio_base + reg);
}

static inline void mydev_wr32(struct mydev *dev, u32 reg, u32 val)
{
    iowrite32(val, dev->mmio_base + reg);
}

/* Memory barrier before doorbell write (ensure descriptor visible to HW) */
static inline void mydev_doorbell(struct mydev *dev, int queue, u32 idx)
{
    wmb();   /* store barrier: descriptors written before doorbell */
    mydev_wr32(dev, REG_DOORBELL + queue * 0x100, idx);
}

/* ------------------------------------------------------------------ */
/* Queue initialization                                                 */
/* ------------------------------------------------------------------ */
static int mydev_queue_init(struct mydev *dev, int idx)
{
    struct mydev_queue *q = &dev->queues[idx];
    struct pci_dev     *pdev = dev->pdev;
    int                 i;

    spin_lock_init(&q->lock);
    q->idx  = idx;
    q->head = 0;
    q->tail = 0;

    /* Allocate coherent descriptor ring */
    q->desc_ring_size = MYDEV_DESC_COUNT * sizeof(struct mydev_desc);
    q->desc_ring = dma_alloc_coherent(&pdev->dev,
                                       q->desc_ring_size,
                                       &q->desc_ring_dma,
                                       GFP_KERNEL);
    if (!q->desc_ring) {
        dev_err(&pdev->dev, "queue %d: descriptor ring alloc failed\n", idx);
        return -ENOMEM;
    }

    /* Initialize completion structures */
    for (i = 0; i < MYDEV_DESC_COUNT; i++)
        init_completion(&q->inflight[i].done);

    /* Program HW: descriptor ring base address (split 64-bit for 32-bit BAR) */
    mydev_wr32(dev, REG_DESC_BASE_LO + idx * 0x100,
               lower_32_bits(q->desc_ring_dma));
    mydev_wr32(dev, REG_DESC_BASE_HI + idx * 0x100,
               upper_32_bits(q->desc_ring_dma));
    mydev_wr32(dev, REG_DESC_COUNT + idx * 0x100, MYDEV_DESC_COUNT);

    dev_dbg(&pdev->dev, "queue %d: ring at DMA %pad (kva %px), size %zu\n",
            idx, &q->desc_ring_dma, q->desc_ring, q->desc_ring_size);
    return 0;
}

static void mydev_queue_cleanup(struct mydev *dev, int idx)
{
    struct mydev_queue *q = &dev->queues[idx];
    if (q->desc_ring) {
        dma_free_coherent(&dev->pdev->dev,
                          q->desc_ring_size,
                          q->desc_ring,
                          q->desc_ring_dma);
        q->desc_ring = NULL;
    }
}

/* ------------------------------------------------------------------ */
/* Submit a DMA transfer (streaming, single buffer)                    */
/* ------------------------------------------------------------------ */
int mydev_submit_single(struct mydev *dev, int qidx,
                        void *buf, size_t len,
                        enum dma_data_direction dir)
{
    struct mydev_queue *q = &dev->queues[qidx];
    struct pci_dev     *pdev = dev->pdev;
    struct mydev_desc  *desc;
    dma_addr_t          buf_dma;
    u32                 slot;
    unsigned long       flags;
    int                 ret = 0;

    /* Map buffer for DMA */
    buf_dma = dma_map_single(&pdev->dev, buf, len, dir);
    if (dma_mapping_error(&pdev->dev, buf_dma)) {
        dev_err(&pdev->dev, "DMA mapping failed for %zu bytes\n", len);
        return -ENOMEM;
    }

    spin_lock_irqsave(&q->lock, flags);

    /* Check queue full */
    if (((q->head + 1) & (MYDEV_DESC_COUNT - 1)) == q->tail) {
        dev_err(&pdev->dev, "queue %d full\n", qidx);
        ret = -EBUSY;
        goto err_unlock;
    }

    slot = q->head;
    desc = &q->desc_ring[slot];

    /* Fill descriptor */
    if (dir == DMA_TO_DEVICE) {
        desc->src_addr = cpu_to_le64(buf_dma);
        desc->dst_addr = 0;
        desc->flags    = cpu_to_le32(MYDEV_DESC_F_INTERRUPT);
    } else {
        desc->src_addr = 0;
        desc->dst_addr = cpu_to_le64(buf_dma);
        desc->flags    = cpu_to_le32(MYDEV_DESC_F_INTERRUPT | MYDEV_DESC_F_WRITE);
    }
    desc->length     = cpu_to_le32(len);
    desc->completion = 0;

    /* Track inflight */
    q->inflight[slot].buf     = buf;
    q->inflight[slot].buf_dma = buf_dma;
    q->inflight[slot].buf_size = len;
    q->inflight[slot].dir     = dir;
    q->inflight[slot].sg      = NULL;
    reinit_completion(&q->inflight[slot].done);

    q->head = (q->head + 1) & (MYDEV_DESC_COUNT - 1);
    spin_unlock_irqrestore(&q->lock, flags);

    /* Ring doorbell */
    mydev_doorbell(dev, qidx, q->head);

    /* Wait for completion (synchronous mode — production would use async) */
    if (!wait_for_completion_timeout(&q->inflight[slot].done,
                                     msecs_to_jiffies(5000))) {
        dev_err(&pdev->dev, "DMA timeout on queue %d slot %u\n", qidx, slot);
        ret = -ETIMEDOUT;
        /* Note: in production, must handle timeout: reset queue, etc. */
    }

    /* Unmap after completion */
    dma_unmap_single(&pdev->dev, buf_dma, len, dir);
    return ret;

err_unlock:
    spin_unlock_irqrestore(&q->lock, flags);
    dma_unmap_single(&pdev->dev, buf_dma, len, dir);
    return ret;
}

/* ------------------------------------------------------------------ */
/* Submit scatter-gather DMA                                           */
/* ------------------------------------------------------------------ */
int mydev_submit_sg(struct mydev *dev, int qidx,
                    struct scatterlist *sg, int nents,
                    enum dma_data_direction dir)
{
    struct mydev_queue *q = &dev->queues[qidx];
    struct pci_dev     *pdev = dev->pdev;
    struct scatterlist *s;
    int                 mapped, i;
    u32                 slot;
    unsigned long       flags;

    /* Map scatter-gather list */
    mapped = dma_map_sg(&pdev->dev, sg, nents, dir);
    if (!mapped) {
        dev_err(&pdev->dev, "S/G DMA mapping failed (%d segs)\n", nents);
        return -ENOMEM;
    }

    spin_lock_irqsave(&q->lock, flags);

    /* Simplified: one descriptor per mapped segment.
     * Production: use indirect descriptor tables for > MYDEV_DESC_COUNT segs. */
    if (mapped > MYDEV_DESC_COUNT - 1) {
        dev_err(&pdev->dev, "too many SG segments: %d\n", mapped);
        spin_unlock_irqrestore(&q->lock, flags);
        dma_unmap_sg(&pdev->dev, sg, nents, dir);
        return -E2BIG;
    }

    for_each_sg(sg, s, mapped, i) {
        slot = (q->head + i) & (MYDEV_DESC_COUNT - 1);
        struct mydev_desc *desc = &q->desc_ring[slot];

        desc->src_addr   = cpu_to_le64(sg_dma_address(s));
        desc->dst_addr   = 0;
        desc->length     = cpu_to_le32(sg_dma_len(s));
        desc->flags      = cpu_to_le32(i == mapped - 1 ?
                                        MYDEV_DESC_F_INTERRUPT : 0);
        desc->completion = 0;
    }

    /* Track last slot for completion */
    slot = (q->head + mapped - 1) & (MYDEV_DESC_COUNT - 1);
    q->inflight[slot].sg    = sg;
    q->inflight[slot].nents = nents;
    q->inflight[slot].dir   = dir;
    reinit_completion(&q->inflight[slot].done);

    q->head = (q->head + mapped) & (MYDEV_DESC_COUNT - 1);
    spin_unlock_irqrestore(&q->lock, flags);

    mydev_doorbell(dev, qidx, q->head);

    if (!wait_for_completion_timeout(&q->inflight[slot].done,
                                     msecs_to_jiffies(5000))) {
        dma_unmap_sg(&pdev->dev, sg, nents, dir);
        return -ETIMEDOUT;
    }

    dma_unmap_sg(&pdev->dev, sg, nents, dir);
    return 0;
}

/* ------------------------------------------------------------------ */
/* MSI-X interrupt handler                                             */
/* ------------------------------------------------------------------ */
static irqreturn_t mydev_irq_handler(int irq, void *data)
{
    struct mydev_queue *q = data;
    struct mydev       *dev = container_of(q, struct mydev, queues[q->idx]);
    u32                 status;
    unsigned long       flags;

    status = mydev_rd32(dev, REG_IRQ_STATUS + q->idx * 0x100);
    if (!status)
        return IRQ_NONE;

    /* Clear interrupt */
    mydev_wr32(dev, REG_IRQ_CLEAR + q->idx * 0x100, status);

    spin_lock_irqsave(&q->lock, flags);

    /* Process completions: advance tail until head */
    while (q->tail != q->head) {
        struct mydev_desc *desc = &q->desc_ring[q->tail];
        u64 completion = le64_to_cpu(READ_ONCE(desc->completion));

        if (!(completion & BIT(63)))   /* HW sets bit 63 on completion */
            break;

        /* Signal waiter */
        complete(&q->inflight[q->tail].done);
        q->tail = (q->tail + 1) & (MYDEV_DESC_COUNT - 1);
    }

    spin_unlock_irqrestore(&q->lock, flags);
    return IRQ_HANDLED;
}

/* ------------------------------------------------------------------ */
/* PCI probe                                                            */
/* ------------------------------------------------------------------ */
static int mydev_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct mydev *dev;
    int           ret, i;

    dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);
    if (!dev) return -ENOMEM;

    dev->pdev = pdev;
    pci_set_drvdata(pdev, dev);

    /* Enable device */
    ret = pcim_enable_device(pdev);
    if (ret) {
        dev_err(&pdev->dev, "pcim_enable_device failed: %d\n", ret);
        return ret;
    }

    /* Request and map MMIO BAR */
    ret = pcim_iomap_regions(pdev, BIT(MYDEV_BAR), "mydev");
    if (ret) {
        dev_err(&pdev->dev, "pcim_iomap_regions failed: %d\n", ret);
        return ret;
    }
    dev->mmio_base = pcim_iomap_table(pdev)[MYDEV_BAR];
    dev->mmio_len  = pci_resource_len(pdev, MYDEV_BAR);

    /* Set DMA mask: prefer 64-bit, fall back to 32-bit */
    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (ret) {
        dev_warn(&pdev->dev, "64-bit DMA not supported, trying 32-bit\n");
        ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        if (ret) {
            dev_err(&pdev->dev, "No usable DMA mask\n");
            return ret;
        }
    }

    /* Enable bus mastering (critical for device-initiated DMA) */
    pci_set_master(pdev);

    /* Setup MSI-X */
    for (i = 0; i < MYDEV_NUM_QUEUES; i++)
        dev->msix[i].entry = i;

    dev->num_vectors = pci_enable_msix_range(pdev, dev->msix,
                                              1, MYDEV_NUM_QUEUES);
    if (dev->num_vectors < 0) {
        dev_err(&pdev->dev, "MSI-X enable failed: %d\n", dev->num_vectors);
        return dev->num_vectors;
    }

    /* Initialize queues */
    for (i = 0; i < dev->num_vectors; i++) {
        ret = mydev_queue_init(dev, i);
        if (ret) goto err_queues;
    }

    /* Request IRQs */
    for (i = 0; i < dev->num_vectors; i++) {
        ret = devm_request_irq(&pdev->dev, dev->msix[i].vector,
                                mydev_irq_handler, 0,
                                "mydev", &dev->queues[i]);
        if (ret) {
            dev_err(&pdev->dev, "IRQ %d request failed: %d\n",
                    dev->msix[i].vector, ret);
            goto err_queues;
        }
    }

    /* Enable DMA in device */
    mydev_wr32(dev, REG_CTRL, CTRL_DMA_ENABLE | CTRL_INT_ENABLE);
    dev_info(&pdev->dev, "mydev: %d queues, %d MSI-X vectors, DMA ready\n",
             dev->num_vectors, dev->num_vectors);
    return 0;

err_queues:
    for (i = 0; i < MYDEV_NUM_QUEUES; i++)
        mydev_queue_cleanup(dev, i);
    pci_disable_msix(pdev);
    return ret;
}

static void mydev_remove(struct pci_dev *pdev)
{
    struct mydev *dev = pci_get_drvdata(pdev);
    int           i;

    /* Disable DMA first — device must stop issuing bus transactions */
    mydev_wr32(dev, REG_CTRL, CTRL_RESET);
    udelay(100);   /* let in-flight DMA complete or abort */

    for (i = 0; i < MYDEV_NUM_QUEUES; i++)
        mydev_queue_cleanup(dev, i);

    pci_disable_msix(pdev);
    pci_clear_master(pdev);
}

static const struct pci_device_id mydev_ids[] = {
    { PCI_DEVICE(MYDEV_VENDOR_ID, MYDEV_DEVICE_ID) },
    { 0 }
};
MODULE_DEVICE_TABLE(pci, mydev_ids);

static struct pci_driver mydev_driver = {
    .name     = "mydev",
    .id_table = mydev_ids,
    .probe    = mydev_probe,
    .remove   = mydev_remove,
};
module_pci_driver(mydev_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Security Systems Engineer");
MODULE_DESCRIPTION("PCIe DMA driver with IOMMU-aware operation");
```

### 14.2 VFIO Userspace DMA Driver (C)

```c
/* vfio_dma_user.c — userspace DMA via VFIO
 *
 * Demonstrates safe userspace DMA programming using VFIO + IOMMU.
 * This is the foundation for DPDK PMDs, SPDK, and GPU compute runtimes.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/vfio.h>
#include <errno.h>

#define PCI_BDF         "0000:03:00.0"
#define IOMMU_GROUP     "/dev/vfio/5"    /* from /sys/kernel/iommu_groups/ */
#define VFIO_CONTAINER  "/dev/vfio/vfio"
#define DMA_BUF_SIZE    (4 * 1024 * 1024)  /* 4 MiB */
#define DMA_IOVA_BASE   0x10000000ULL       /* chosen IOVA */

struct vfio_state {
    int  container_fd;
    int  group_fd;
    int  device_fd;
    void *dma_buf;         /* pinned userspace buffer */
    uint64_t iova;         /* IOVA mapped for this buffer */
    void *bar0;            /* mmap of BAR 0 */
    size_t bar0_size;
};

static int vfio_init(struct vfio_state *st)
{
    struct vfio_group_status   group_status = { .argsz = sizeof(group_status) };
    struct vfio_iommu_type1_info iommu_info = { .argsz = sizeof(iommu_info) };
    int ret;

    /* 1. Open container */
    st->container_fd = open(VFIO_CONTAINER, O_RDWR);
    if (st->container_fd < 0) { perror("open container"); return -1; }

    /* 2. Check VFIO API version */
    if (ioctl(st->container_fd, VFIO_GET_API_VERSION) != VFIO_API_VERSION) {
        fprintf(stderr, "VFIO API version mismatch\n");
        return -1;
    }

    /* 3. Check IOMMU type support */
    if (!ioctl(st->container_fd, VFIO_CHECK_EXTENSION, VFIO_TYPE1v2_IOMMU)) {
        fprintf(stderr, "VFIO_TYPE1v2_IOMMU not supported\n");
        return -1;
    }

    /* 4. Open IOMMU group */
    st->group_fd = open(IOMMU_GROUP, O_RDWR);
    if (st->group_fd < 0) { perror("open group"); return -1; }

    /* 5. Verify group is viable (device unbound from kernel driver) */
    ioctl(st->group_fd, VFIO_GROUP_GET_STATUS, &group_status);
    if (!(group_status.flags & VFIO_GROUP_FLAGS_VIABLE)) {
        fprintf(stderr, "IOMMU group not viable (device still bound to kernel driver?)\n");
        return -1;
    }

    /* 6. Add group to container */
    ret = ioctl(st->group_fd, VFIO_GROUP_SET_CONTAINER, &st->container_fd);
    if (ret) { perror("set container"); return -1; }

    /* 7. Enable IOMMU type */
    ret = ioctl(st->container_fd, VFIO_SET_IOMMU, VFIO_TYPE1v2_IOMMU);
    if (ret) { perror("set iommu"); return -1; }

    /* 8. Get device FD */
    st->device_fd = ioctl(st->group_fd, VFIO_GROUP_GET_DEVICE_FD, PCI_BDF);
    if (st->device_fd < 0) { perror("get device fd"); return -1; }

    return 0;
}

static int vfio_map_dma(struct vfio_state *st)
{
    /* Allocate page-aligned userspace buffer (will be pinned) */
    st->dma_buf = mmap(NULL, DMA_BUF_SIZE,
                       PROT_READ | PROT_WRITE,
                       MAP_SHARED | MAP_ANONYMOUS | MAP_LOCKED,
                       -1, 0);
    if (st->dma_buf == MAP_FAILED) { perror("mmap dma buf"); return -1; }

    /* Pre-fault pages (mandatory before VFIO_IOMMU_MAP_DMA) */
    memset(st->dma_buf, 0, DMA_BUF_SIZE);

    /* Map into IOMMU */
    struct vfio_iommu_type1_dma_map dma_map = {
        .argsz = sizeof(dma_map),
        .flags = VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE,
        .vaddr = (uint64_t)(uintptr_t)st->dma_buf,
        .iova  = DMA_IOVA_BASE,
        .size  = DMA_BUF_SIZE,
    };

    if (ioctl(st->container_fd, VFIO_IOMMU_MAP_DMA, &dma_map) < 0) {
        perror("VFIO_IOMMU_MAP_DMA");
        munmap(st->dma_buf, DMA_BUF_SIZE);
        return -1;
    }

    st->iova = DMA_IOVA_BASE;
    printf("DMA buffer: userspace VA=0x%lx IOVA=0x%lx size=%zu\n",
           (uint64_t)(uintptr_t)st->dma_buf, st->iova, (size_t)DMA_BUF_SIZE);
    return 0;
}

static int vfio_map_bar(struct vfio_state *st, int bar_idx)
{
    struct vfio_region_info reg = { .argsz = sizeof(reg) };
    reg.index = VFIO_PCI_BAR0_REGION_INDEX + bar_idx;

    if (ioctl(st->device_fd, VFIO_DEVICE_GET_REGION_INFO, &reg) < 0) {
        perror("get BAR info"); return -1;
    }

    printf("BAR%d: size=0x%llx flags=0x%x\n",
           bar_idx, reg.size, reg.flags);

    if (!(reg.flags & VFIO_REGION_INFO_FLAG_MMAP)) {
        fprintf(stderr, "BAR%d not mmap-able\n", bar_idx);
        return -1;
    }

    st->bar0 = mmap(NULL, reg.size,
                    PROT_READ | PROT_WRITE, MAP_SHARED,
                    st->device_fd, reg.offset);
    if (st->bar0 == MAP_FAILED) { perror("mmap BAR"); return -1; }
    st->bar0_size = reg.size;

    /* Now we can read/write device registers directly via st->bar0 */
    return 0;
}

static void vfio_write32(struct vfio_state *st, uint32_t offset, uint32_t val)
{
    volatile uint32_t *reg = (volatile uint32_t *)((char *)st->bar0 + offset);
    *reg = val;
    __sync_synchronize();   /* memory barrier */
}

static uint32_t vfio_read32(struct vfio_state *st, uint32_t offset)
{
    __sync_synchronize();
    volatile uint32_t *reg = (volatile uint32_t *)((char *)st->bar0 + offset);
    return *reg;
}

static void vfio_cleanup(struct vfio_state *st)
{
    if (st->bar0 && st->bar0 != MAP_FAILED)
        munmap(st->bar0, st->bar0_size);

    if (st->dma_buf && st->dma_buf != MAP_FAILED) {
        struct vfio_iommu_type1_dma_unmap dma_unmap = {
            .argsz = sizeof(dma_unmap),
            .flags = 0,
            .iova  = st->iova,
            .size  = DMA_BUF_SIZE,
        };
        ioctl(st->container_fd, VFIO_IOMMU_UNMAP_DMA, &dma_unmap);
        munmap(st->dma_buf, DMA_BUF_SIZE);
    }

    if (st->device_fd  > 0) close(st->device_fd);
    if (st->group_fd   > 0) close(st->group_fd);
    if (st->container_fd > 0) close(st->container_fd);
}

int main(void)
{
    struct vfio_state st = {};
    int ret;

    ret = vfio_init(&st);
    if (ret) goto out;

    ret = vfio_map_dma(&st);
    if (ret) goto out;

    ret = vfio_map_bar(&st, 0);
    if (ret) goto out;

    /*
     * Now program device:
     *   - Write DMA descriptor to device BAR registers
     *   - Use st->iova (= DMA_IOVA_BASE) as device DMA address
     *   - Device DMA will go to st->dma_buf via IOMMU
     */
    vfio_write32(&st, 0x10, (uint32_t)(st.iova & 0xFFFFFFFF));
    vfio_write32(&st, 0x14, (uint32_t)(st.iova >> 32));
    vfio_write32(&st, 0x18, DMA_BUF_SIZE);
    vfio_write32(&st, 0x00, 0x1);   /* DMA start */

    /* Poll for completion */
    uint32_t status;
    int timeout = 10000;
    do {
        usleep(100);
        status = vfio_read32(&st, 0x04);
    } while (!(status & 0x1) && --timeout > 0);

    if (timeout == 0) {
        fprintf(stderr, "DMA timeout\n");
        ret = -1;
    } else {
        printf("DMA completed, status=0x%x\n", status);
        printf("First bytes: %02x %02x %02x %02x\n",
               ((uint8_t *)st.dma_buf)[0], ((uint8_t *)st.dma_buf)[1],
               ((uint8_t *)st.dma_buf)[2], ((uint8_t *)st.dma_buf)[3]);
    }

out:
    vfio_cleanup(&st);
    return ret;
}
```

---

## 15. Rust Implementation

### 15.1 Rust Kernel DMA Abstractions (rust-for-linux)

The Rust-for-Linux project provides safe wrappers around Linux DMA APIs. As of Linux 6.8, DMA Rust bindings are in `rust/kernel/dma.rs`.

```rust
// rust/kernel/dma.rs — Rust bindings for Linux DMA API
// This shows the design pattern; actual API evolves with rust-for-linux

use core::{marker::PhantomData, ptr::NonNull};
use kernel::{
    bindings,
    device::Device,
    error::{Error, Result},
    types::ARef,
};

/// Direction of a DMA transfer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DmaDirection {
    ToDevice,
    FromDevice,
    Bidirectional,
    None,
}

impl DmaDirection {
    fn to_raw(self) -> u32 {
        match self {
            DmaDirection::ToDevice      => bindings::dma_data_direction_DMA_TO_DEVICE,
            DmaDirection::FromDevice    => bindings::dma_data_direction_DMA_FROM_DEVICE,
            DmaDirection::Bidirectional => bindings::dma_data_direction_DMA_BIDIRECTIONAL,
            DmaDirection::None          => bindings::dma_data_direction_DMA_NONE,
        }
    }
}

/// Coherent DMA allocation.
///
/// Wraps `dma_alloc_coherent` / `dma_free_coherent`.
/// Automatically frees on drop — prevents resource leaks.
pub struct CoherentAllocation<T> {
    cpu_addr: NonNull<T>,
    dma_addr: bindings::dma_addr_t,
    count: usize,
    dev: ARef<Device>,
}

impl<T> CoherentAllocation<T> {
    /// Allocate coherent DMA memory.
    ///
    /// # Safety
    /// The device must remain valid for the lifetime of this allocation.
    pub fn alloc(dev: &Device, count: usize) -> Result<Self> {
        let size = count
            .checked_mul(core::mem::size_of::<T>())
            .ok_or(Error::ENOMEM)?;

        let mut dma_addr: bindings::dma_addr_t = 0;

        // SAFETY: `dev.raw_device()` is valid; size is nonzero.
        let ptr = unsafe {
            bindings::dma_alloc_coherent(
                dev.raw_device(),
                size,
                &mut dma_addr,
                bindings::GFP_KERNEL,
            )
        };

        let cpu_addr = NonNull::new(ptr as *mut T).ok_or(Error::ENOMEM)?;

        // Verify DMA mapping didn't fail
        // (dma_alloc_coherent returns NULL on failure, already checked above)

        Ok(CoherentAllocation {
            cpu_addr,
            dma_addr,
            count,
            dev: dev.into(),
        })
    }

    /// Get the DMA address to program into the device.
    pub fn dma_addr(&self) -> u64 {
        self.dma_addr
    }

    /// Get a shared reference to the buffer (index-checked).
    pub fn get(&self, index: usize) -> Option<&T> {
        if index >= self.count {
            return None;
        }
        // SAFETY: index < count, buffer is valid for count elements
        unsafe { Some(&*self.cpu_addr.as_ptr().add(index)) }
    }

    /// Get a mutable reference to the buffer (index-checked).
    pub fn get_mut(&mut self, index: usize) -> Option<&mut T> {
        if index >= self.count {
            return None;
        }
        // SAFETY: index < count, we have exclusive access
        unsafe { Some(&mut *self.cpu_addr.as_ptr().add(index)) }
    }

    /// Number of elements.
    pub fn len(&self) -> usize {
        self.count
    }
}

impl<T> Drop for CoherentAllocation<T> {
    fn drop(&mut self) {
        let size = self.count * core::mem::size_of::<T>();
        // SAFETY: matching alloc parameters; called exactly once (Drop).
        unsafe {
            bindings::dma_free_coherent(
                self.dev.raw_device(),
                size,
                self.cpu_addr.as_ptr() as *mut _,
                self.dma_addr,
            );
        }
    }
}

// SAFETY: The DMA buffer is accessible from any CPU, and T must be Send.
unsafe impl<T: Send> Send for CoherentAllocation<T> {}
// SAFETY: Concurrent immutable access is safe; mutable access requires &mut self.
unsafe impl<T: Sync> Sync for CoherentAllocation<T> {}

/// Streaming DMA mapping for a single buffer.
///
/// Wraps `dma_map_single` / `dma_unmap_single`.
/// The mapping is released when this object is dropped or `unmap()` is called.
pub struct StreamingMapping<'a> {
    dma_addr: bindings::dma_addr_t,
    size: usize,
    dir: DmaDirection,
    dev: &'a Device,
    unmapped: bool,
}

impl<'a> StreamingMapping<'a> {
    /// Map a kernel slice for streaming DMA.
    pub fn map<T>(dev: &'a Device, slice: &[T], dir: DmaDirection) -> Result<Self> {
        let size = core::mem::size_of_val(slice);
        if size == 0 {
            return Err(Error::EINVAL);
        }

        // SAFETY: slice is valid, size is correct.
        let dma_addr = unsafe {
            bindings::dma_map_single(
                dev.raw_device(),
                slice.as_ptr() as *mut _,
                size,
                dir.to_raw() as i32,
            )
        };

        // SAFETY: dev.raw_device() is valid.
        if unsafe { bindings::dma_mapping_error(dev.raw_device(), dma_addr) } != 0 {
            return Err(Error::ENOMEM);
        }

        Ok(StreamingMapping {
            dma_addr,
            size,
            dir,
            dev,
            unmapped: false,
        })
    }

    /// DMA address to program into the device descriptor.
    pub fn dma_addr(&self) -> u64 {
        self.dma_addr
    }

    /// Transfer ownership to CPU (sync for CPU access).
    /// After this, CPU may read the buffer.
    pub fn sync_for_cpu(&self) {
        // SAFETY: mapping is valid and not yet unmapped.
        unsafe {
            bindings::dma_sync_single_for_cpu(
                self.dev.raw_device(),
                self.dma_addr,
                self.size,
                self.dir.to_raw() as i32,
            );
        }
    }

    /// Transfer ownership to device (sync for device access).
    pub fn sync_for_device(&self) {
        // SAFETY: mapping is valid and not yet unmapped.
        unsafe {
            bindings::dma_sync_single_for_device(
                self.dev.raw_device(),
                self.dma_addr,
                self.size,
                self.dir.to_raw() as i32,
            );
        }
    }

    /// Explicitly unmap (also happens on Drop).
    pub fn unmap(mut self) {
        self.do_unmap();
    }

    fn do_unmap(&mut self) {
        if !self.unmapped {
            // SAFETY: matching parameters from map(); called once.
            unsafe {
                bindings::dma_unmap_single(
                    self.dev.raw_device(),
                    self.dma_addr,
                    self.size,
                    self.dir.to_raw() as i32,
                );
            }
            self.unmapped = true;
        }
    }
}

impl<'a> Drop for StreamingMapping<'a> {
    fn drop(&mut self) {
        self.do_unmap();
    }
}
```

### 15.2 Rust PCIe Driver Skeleton

```rust
// mydev_pcie.rs — Rust PCIe DMA driver
//
// Requires: rust-for-linux (CONFIG_RUST=y in kernel)
// Demonstrates: PCI device lifecycle, DMA, MMIO, interrupts in safe Rust

use kernel::{
    define_pci_id_table,
    pci::{self, Bar, Device as PciDevice},
    dma::{CoherentAllocation, DmaDirection, StreamingMapping},
    irq::{self, IrqData},
    sync::{Arc, Mutex, SpinLock},
    error::Result,
    pr_info, pr_err,
    module_pci_driver,
};

const MYDEV_BAR:        u32 = 0;
const DESC_RING_SIZE:   usize = 256;

/// Hardware descriptor layout (must match device hardware spec)
#[repr(C, packed)]
struct HwDescriptor {
    src_addr:   u64,
    dst_addr:   u64,
    length:     u32,
    flags:      u32,
    completion: u64,
}

/// Safe wrapper around the device's coherent descriptor ring
struct DescRing {
    ring: CoherentAllocation<HwDescriptor>,
    head: usize,
    tail: usize,
}

impl DescRing {
    fn new(dev: &PciDevice) -> Result<Self> {
        Ok(DescRing {
            ring: CoherentAllocation::alloc(dev.as_ref(), DESC_RING_SIZE)?,
            head: 0,
            tail: 0,
        })
    }

    fn is_full(&self) -> bool {
        (self.head + 1) % DESC_RING_SIZE == self.tail
    }

    fn next_head(&mut self) -> Option<(usize, u64)> {
        if self.is_full() { return None; }
        let slot = self.head;
        let dma_addr = self.ring.dma_addr()
            + (slot * core::mem::size_of::<HwDescriptor>()) as u64;
        Some((slot, dma_addr))
    }

    fn advance_head(&mut self) {
        self.head = (self.head + 1) % DESC_RING_SIZE;
    }

    fn get_desc_mut(&mut self, idx: usize) -> Option<&mut HwDescriptor> {
        self.ring.get_mut(idx)
    }
}

/// Device state protected by a spinlock
struct MyDevState {
    ring:     DescRing,
    mmio_bar: Bar<0>,   /* BAR 0, generic parameter = BAR index */
}

/// Main device structure
struct MyPciDev {
    state: SpinLock<MyDevState>,
    _irq:  irq::Registration<MyPciDev>,
}

/// MMIO register helpers
impl MyDevState {
    fn write32(&self, offset: usize, val: u32) {
        self.mmio_bar.write32(offset, val);
    }

    fn read32(&self, offset: usize) -> u32 {
        self.mmio_bar.read32(offset)
    }

    fn doorbell(&self, head: u32) {
        // Ensure writes to descriptors are visible before doorbell
        core::sync::atomic::fence(core::sync::atomic::Ordering::Release);
        self.write32(0x14, head);
    }
}

/// IRQ handler
impl irq::Handler for MyPciDev {
    type Data = Arc<MyPciDev>;

    fn handle_irq(dev: &Arc<MyPciDev>) -> irq::Return {
        let mut state = dev.state.lock();
        let status = state.read32(0x18);
        if status == 0 {
            return irq::Return::None;
        }
        state.write32(0x1C, status);  // clear IRQ

        // Process completions
        while state.ring.tail != state.ring.head {
            let tail = state.ring.tail;
            if let Some(desc) = state.ring.get_desc_mut(tail) {
                let completion = unsafe { core::ptr::read_volatile(&desc.completion) };
                if completion & (1u64 << 63) == 0 {
                    break; // HW not done yet
                }
                state.ring.tail = (state.ring.tail + 1) % DESC_RING_SIZE;
            }
        }

        irq::Return::Handled
    }
}

impl pci::Driver for MyPciDev {
    type Data = Arc<MyPciDev>;

    define_pci_id_table! {
        (),
        [(pci::DeviceId::new(0x1234, 0x5678), ())]
    }

    fn probe(dev: &mut PciDevice, _id: &pci::DeviceId) -> Result<Arc<MyPciDev>> {
        dev.enable_device_mem()?;
        dev.set_master();

        // Set 64-bit DMA mask
        dev.set_dma_mask(u64::MAX)?;
        dev.set_coherent_dma_mask(u64::MAX)?;

        // Map BAR 0
        let bar = dev.iomap_region_sized::<0, { 4096 }>(c_str!("mydev"))?;

        // Allocate descriptor ring
        let ring = DescRing::new(dev)?;

        let state = SpinLock::new(MyDevState {
            ring,
            mmio_bar: bar,
        });

        // Setup MSI-X (simplified: single vector)
        let irq_reg = dev.request_irq(0, /* vector */ MyPciDev::handle_irq)?;

        let mydev = Arc::try_new(MyPciDev {
            state,
            _irq: irq_reg,
        })?;

        // Enable DMA in hardware
        {
            let mut s = mydev.state.lock();
            let ring_dma = s.ring.ring.dma_addr();
            s.write32(0x08, (ring_dma & 0xFFFFFFFF) as u32);
            s.write32(0x0C, (ring_dma >> 32) as u32);
            s.write32(0x10, DESC_RING_SIZE as u32);
            s.write32(0x00, 0x3);  // DMA_ENABLE | INT_ENABLE
        }

        pr_info!("mydev: probed successfully\n");
        Ok(mydev)
    }

    fn remove(_dev: &mut PciDevice, data: Arc<MyPciDev>) {
        // Disable DMA before cleanup
        let mut state = data.state.lock();
        state.write32(0x00, 1u32 << 31);  // RESET
        pr_info!("mydev: removed\n");
    }
}

module_pci_driver! {
    type: MyPciDev,
    name: "mydev_rust",
    author: "Security Systems Engineer",
    description: "Rust PCIe DMA driver",
    license: "GPL",
}
```

### 15.3 Rust Userspace VFIO Library

```rust
// vfio_dma/src/lib.rs
//! Safe Rust bindings for VFIO userspace DMA.
//!
//! Provides RAII wrappers ensuring proper cleanup of VFIO resources.

use std::{
    fs::{File, OpenOptions},
    os::unix::io::{AsRawFd, RawFd},
    ffi::CString,
    io,
};
use nix::{
    ioctl_readwrite, ioctl_write_ptr, ioctl_none,
    sys::mman::{mmap, munmap, MapFlags, ProtFlags},
};

// VFIO ioctl numbers (from linux/vfio.h)
const VFIO_TYPE: u8 = b';';
const VFIO_BASE: u8 = 100;

ioctl_none!(vfio_get_api_version, VFIO_TYPE, VFIO_BASE);
ioctl_readwrite!(vfio_check_extension, VFIO_TYPE, VFIO_BASE + 1, u32);
ioctl_write_ptr!(vfio_set_iommu, VFIO_TYPE, VFIO_BASE + 2, i32);
ioctl_write_ptr!(vfio_group_set_container, VFIO_TYPE, VFIO_BASE + 4, i32);
ioctl_readwrite!(vfio_group_get_status, VFIO_TYPE, VFIO_BASE + 3, VfioGroupStatus);
ioctl_readwrite!(vfio_iommu_map_dma, VFIO_TYPE, VFIO_BASE + 13, VfioIommuDmaMap);
ioctl_readwrite!(vfio_iommu_unmap_dma, VFIO_TYPE, VFIO_BASE + 14, VfioIommuDmaUnmap);
ioctl_readwrite!(vfio_device_get_region_info, VFIO_TYPE, VFIO_BASE + 8, VfioRegionInfo);

const VFIO_API_VERSION: i64 = 0;
const VFIO_TYPE1V2_IOMMU: i32 = 6;
const VFIO_GROUP_FLAGS_VIABLE: u32 = 1 << 0;
const VFIO_DMA_MAP_FLAG_READ: u32 = 1 << 0;
const VFIO_DMA_MAP_FLAG_WRITE: u32 = 1 << 1;

#[repr(C)]
struct VfioGroupStatus {
    argsz: u32,
    flags: u32,
}

#[repr(C)]
struct VfioIommuDmaMap {
    argsz: u32,
    flags: u32,
    vaddr: u64,
    iova:  u64,
    size:  u64,
}

#[repr(C)]
struct VfioIommuDmaUnmap {
    argsz: u32,
    flags: u32,
    iova:  u64,
    size:  u64,
}

#[repr(C)]
struct VfioRegionInfo {
    argsz: u32,
    flags: u32,
    index: u32,
    cap_offset: u32,
    size:   u64,
    offset: u64,
}

/// VFIO Container — holds the IOMMU domain.
pub struct VfioContainer {
    file: File,
}

impl VfioContainer {
    pub fn new() -> io::Result<Self> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open("/dev/vfio/vfio")?;

        // Verify API version
        let ver = unsafe { vfio_get_api_version(file.as_raw_fd()) }
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;
        if ver != VFIO_API_VERSION {
            return Err(io::Error::new(io::ErrorKind::Other, "VFIO API version mismatch"));
        }

        Ok(VfioContainer { file })
    }

    pub fn fd(&self) -> RawFd {
        self.file.as_raw_fd()
    }

    pub fn set_iommu(&self) -> io::Result<()> {
        let iommu_type = VFIO_TYPE1V2_IOMMU;
        unsafe { vfio_set_iommu(self.fd(), &iommu_type) }
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;
        Ok(())
    }
}

/// VFIO Group — represents a set of devices with a shared IOMMU domain.
pub struct VfioGroup {
    file: File,
}

impl VfioGroup {
    pub fn open(group_id: u32) -> io::Result<Self> {
        let path = format!("/dev/vfio/{}", group_id);
        let file = OpenOptions::new().read(true).write(true).open(&path)?;
        Ok(VfioGroup { file })
    }

    pub fn is_viable(&self) -> io::Result<bool> {
        let mut status = VfioGroupStatus { argsz: 8, flags: 0 };
        unsafe { vfio_group_get_status(self.file.as_raw_fd(), &mut status) }
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;
        Ok(status.flags & VFIO_GROUP_FLAGS_VIABLE != 0)
    }

    pub fn set_container(&self, container: &VfioContainer) -> io::Result<()> {
        let fd = container.fd();
        unsafe { vfio_group_set_container(self.file.as_raw_fd(), &fd) }
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;
        Ok(())
    }

    pub fn get_device_fd(&self, bdf: &str) -> io::Result<RawFd> {
        use std::os::unix::io::FromRawFd;
        let bdf_c = CString::new(bdf).unwrap();
        // Note: VFIO_GROUP_GET_DEVICE_FD requires a string ioctl (non-standard nix)
        // For production use nix::ioctl_write_buf! or direct libc::ioctl
        let fd = unsafe {
            libc::ioctl(
                self.file.as_raw_fd(),
                (b';' as u64) << 8 | (100 + 6) as u64,  /* VFIO_GROUP_GET_DEVICE_FD */
                bdf_c.as_ptr(),
            )
        };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(fd)
    }
}

/// DMA mapping in VFIO — RAII wrapper.
/// Automatically unmaps on drop.
pub struct VfioDmaMapping {
    container_fd: RawFd,
    iova: u64,
    size: u64,
    ptr:  *mut u8,
}

impl VfioDmaMapping {
    pub fn new(
        container: &VfioContainer,
        size: usize,
        iova: u64,
    ) -> io::Result<Self> {
        // Allocate and pin userspace memory
        let ptr = unsafe {
            mmap(
                None,
                std::num::NonZeroUsize::new(size).unwrap(),
                ProtFlags::PROT_READ | ProtFlags::PROT_WRITE,
                MapFlags::MAP_SHARED | MapFlags::MAP_ANONYMOUS | MapFlags::MAP_LOCKED,
                -1,
                0,
            ).map_err(|e| io::Error::from_raw_os_error(e as i32))?
        } as *mut u8;

        // Pre-fault pages (required before IOMMU mapping)
        unsafe { std::ptr::write_bytes(ptr, 0, size); }

        // Map into IOMMU domain
        let mut dma_map = VfioIommuDmaMap {
            argsz: std::mem::size_of::<VfioIommuDmaMap>() as u32,
            flags: VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE,
            vaddr: ptr as u64,
            iova,
            size:  size as u64,
        };

        let ret = unsafe {
            vfio_iommu_map_dma(container.fd(), &mut dma_map)
        };

        if let Err(e) = ret {
            unsafe { munmap(ptr as *mut _, size).ok(); }
            return Err(io::Error::from_raw_os_error(e as i32));
        }

        println!("VFIO DMA: mapped {} bytes at IOVA 0x{:016x}", size, iova);

        Ok(VfioDmaMapping {
            container_fd: container.fd(),
            iova,
            size: size as u64,
            ptr,
        })
    }

    /// IOVA to program into device descriptor.
    pub fn iova(&self) -> u64 { self.iova }

    /// Pointer to the DMA buffer (userspace side).
    pub fn as_ptr(&self) -> *mut u8 { self.ptr }

    /// Get a mutable slice view of the buffer.
    ///
    /// # Safety
    /// Caller must ensure no concurrent device DMA is accessing the buffer.
    pub unsafe fn as_slice_mut(&mut self) -> &mut [u8] {
        std::slice::from_raw_parts_mut(self.ptr, self.size as usize)
    }
}

impl Drop for VfioDmaMapping {
    fn drop(&mut self) {
        let mut unmap = VfioIommuDmaUnmap {
            argsz: std::mem::size_of::<VfioIommuDmaUnmap>() as u32,
            flags: 0,
            iova:  self.iova,
            size:  self.size,
        };
        unsafe {
            let _ = vfio_iommu_unmap_dma(self.container_fd, &mut unmap);
            let _ = munmap(self.ptr as *mut _, self.size as usize);
        }
        println!("VFIO DMA: unmapped IOVA 0x{:016x}", self.iova);
    }
}

// SAFETY: The DMA buffer is memory-mapped I/O; raw pointer access is inherently unsafe.
// The struct is marked Send since ownership transfer is valid.
unsafe impl Send for VfioDmaMapping {}

/// Full VFIO session — manages container, group, device, and DMA.
pub struct VfioSession {
    pub container: VfioContainer,
    pub group:     VfioGroup,
    device_fd:     RawFd,
}

impl VfioSession {
    pub fn open(group_id: u32, bdf: &str) -> io::Result<Self> {
        let container = VfioContainer::new()?;
        let group = VfioGroup::open(group_id)?;

        if !group.is_viable()? {
            return Err(io::Error::new(
                io::ErrorKind::Other,
                "IOMMU group not viable — unbind device from kernel driver first",
            ));
        }

        group.set_container(&container)?;
        container.set_iommu()?;

        let device_fd = group.get_device_fd(bdf)?;

        Ok(VfioSession { container, group, device_fd })
    }

    pub fn alloc_dma(&self, size: usize, iova: u64) -> io::Result<VfioDmaMapping> {
        VfioDmaMapping::new(&self.container, size, iova)
    }

    /// mmap a device BAR for direct register access.
    pub fn map_bar(&self, bar_index: u32) -> io::Result<(*mut u8, usize)> {
        let mut info = VfioRegionInfo {
            argsz: std::mem::size_of::<VfioRegionInfo>() as u32,
            flags: 0,
            index: bar_index,
            cap_offset: 0,
            size:   0,
            offset: 0,
        };

        unsafe { vfio_device_get_region_info(self.device_fd, &mut info) }
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;

        let bar_size = info.size as usize;
        if bar_size == 0 {
            return Err(io::Error::new(io::ErrorKind::Other, "BAR size is 0"));
        }

        let ptr = unsafe {
            mmap(
                None,
                std::num::NonZeroUsize::new(bar_size).unwrap(),
                ProtFlags::PROT_READ | ProtFlags::PROT_WRITE,
                MapFlags::MAP_SHARED,
                self.device_fd,
                info.offset as i64,
            ).map_err(|e| io::Error::from_raw_os_error(e as i32))?
        } as *mut u8;

        Ok((ptr, bar_size))
    }
}

impl Drop for VfioSession {
    fn drop(&mut self) {
        unsafe { libc::close(self.device_fd); }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Integration test — requires real VFIO device.
    /// Run with: sudo cargo test -- --ignored
    #[test]
    #[ignore]
    fn test_vfio_dma_map_unmap() {
        let session = VfioSession::open(5, "0000:03:00.0")
            .expect("failed to open VFIO session");

        let mapping = session.alloc_dma(4096, 0x10000000)
            .expect("DMA mapping failed");

        assert_eq!(mapping.iova(), 0x10000000);
        assert!(!mapping.as_ptr().is_null());

        // Write to buffer (CPU side)
        unsafe {
            let buf = std::slice::from_raw_parts_mut(mapping.as_ptr(), 4096);
            buf[0] = 0xDE;
            buf[1] = 0xAD;
        }

        // mapping is dropped here → automatically unmapped
        drop(mapping);
    }

    #[test]
    fn test_dma_direction_conversion() {
        assert_eq!(DmaDirection::ToDevice.to_raw(), 1);
        assert_eq!(DmaDirection::FromDevice.to_raw(), 2);
        assert_eq!(DmaDirection::Bidirectional.to_raw(), 0);
    }
}
```

### 15.4 Rust Build Configuration

```toml
# Cargo.toml for vfio_dma crate
[package]
name = "vfio_dma"
version = "0.1.0"
edition = "2021"

[dependencies]
nix = { version = "0.27", features = ["mman", "ioctl"] }
libc = "0.2"
thiserror = "1.0"

[dev-dependencies]
# For integration tests
criterion = "0.5"

[[bench]]
name = "dma_bench"
harness = false

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
```

```toml
# For rust-for-linux kernel module
# rust/kernel/Cargo.toml (simplified)
[lib]
crate-type = ["rlib"]

[features]
default = []
dma = []
pci = ["dma"]
irq = []
```

---

## 16. Threat Model and Security

### 16.1 DMA Attack Taxonomy

```
Attack Category    | Description                                   | Impact
-------------------|-----------------------------------------------|------------------
DMA Read           | Device reads arbitrary PA (credentials, keys) | Critical — CIA
DMA Write          | Device overwrites kernel memory, page tables  | Critical — RCE
IOVA Exhaustion    | Exhaust IOMMU IOVA allocator (DoS)           | High — DoS
IOMMU Bypass       | iommu=pt, pass-through mode, IOMMU disabled  | Critical
Interrupt Remap    | Device injects fake interrupts (without IR)   | High — escalation
ACS Bypass         | Peer-to-peer DMA bypasses IOMMU              | High
Thunderclap        | PCIe hot-plug device exploits IOMMU           | Critical
Rowhammer via DMA  | DMA to adjacent physical rows flips bits      | High
SWIOTLB window     | Race: access data before/after bounce copy    | Medium
SVA/PASID attack   | Device uses wrong PASID → accesses other process | High
```

### 16.2 IOMMU Bypass Scenarios

```
1. iommu=pt (pass-through): ALL devices get PA == IOVA, NO translation.
   Detection: dmesg | grep "DMA-API: device .* using .* dma_ops"
   Fix: Never use iommu=pt in production. Remove from kernel cmdline.

2. Missing DMAR/IVRS ACPI table:
   Some BIOS/firmware hides IOMMU tables for compatibility.
   Detection: dmesg | grep "DMAR: No DMAR devices" or "AMD-Vi: No IOMMU found"
   Fix: Enable "Intel VT-d" or "AMD IOMMU" in BIOS.

3. IOMMU group with multiple devices (ACS not supported):
   All devices in group share domain → if one is compromised, all are exposed.
   Detection: check group membership (see above)
   Fix: Use NIC/storage cards with native ACS support; separate PCIe switches.

4. Unsafe VFIO iommu=pt for passthrough:
   Some VFIO setups use passthrough (no translation) for performance.
   This gives VMs full DMA access to all physical memory.
   Fix: Always use VFIO with IOMMU type1/type1v2; never iommu=pt for VMs.

5. DMA-capable device in unprotected IOMMU region:
   Device mapped to "bypass" context entry in VT-d context table.
   Detection: Intel IOMMU debug: /sys/kernel/debug/iommu/intel/domain_translation_struct
   Fix: Audit all context entries; ensure no devices in bypass context.
```

### 16.3 Thunderclap Attack Class

Thunderclap (2019, Markettos et al.) demonstrated that Thunderbolt/PCIe hot-pluggable devices can exploit IOMMU weaknesses:

```
Attack flow:
  1. Attacker plugs in malicious Thunderbolt device
  2. OS (even with IOMMU) typically maps device into a broad IOVA region
     (e.g., many OSes mapped NIC packet buffers for new device immediately)
  3. Malicious device uses DMA to read adjacent memory (kernel structures)
     or write to specific offsets within the mapped region (use-after-free)
  
Linux mitigations:
  - CONFIG_INTEL_IOMMU_DEFAULT_ON: IOMMU on by default
  - CONFIG_IOMMU_DEFAULT_DMA_STRICT: strict mode (no lazy batching)
  - Thunderbolt security levels: /sys/bus/thunderbolt/devices/.../authorized
    0: no authorization (none — dangerous)
    1: user authorization required (user — default on Linux)
    2: secure connect (certified — cryptographic attestation)
    3: device policy (dponly — only via daemon policy)
  - Check current level: cat /sys/bus/thunderbolt/devices/0-0/security
  
Kernel feature (5.4+):
  CONFIG_USB4: USB4/Thunderbolt security framework
  thunderbolt-tools: boltctl authorize, boltctl list
```

### 16.4 DMA Security Hardening Checklist

```bash
# --- IOMMU verification ---
# 1. Confirm IOMMU is active
dmesg | grep -E "(IOMMU|VT-d|AMD-Vi|SMMU)" | grep -v disabled
# Expected: "DMAR: Intel(R) Virtualization Technology for Directed I/O"
# Expected: "iommu: Default domain type: Translated"

# 2. Verify no pass-through domains (for non-trusted devices)
cat /sys/kernel/debug/iommu/intel/domain_translation_struct 2>/dev/null | grep -i passthrough

# 3. Check IOMMU groups — each security-critical device should be alone
for g in /sys/kernel/iommu_groups/*/devices; do
    devs=$(ls "$g" | wc -l)
    if [ "$devs" -gt 1 ]; then
        echo "WARN: Group with $devs devices: $(ls $g)"
    fi
done

# 4. Verify interrupt remapping
dmesg | grep "Enabled IRQ remapping"

# 5. Check ACS for PCIe switches
lspci -vvv | grep -A2 "Access Control"

# 6. Confirm SWIOTLB size is sufficient (but not excessive)
dmesg | grep -i swiotlb | grep "bytes"

# 7. Verify DMA API debug (should be off in production — overhead)
# CONFIG_DMA_API_DEBUG=y adds validation of all DMA calls (test env only)

# 8. Check for DMA mask debugging
echo 1 > /sys/kernel/debug/dma-api/disabled  # ONLY for debugging
# Production: leave at 0

# --- Kernel configuration audit ---
zcat /proc/config.gz | grep -E \
    'CONFIG_INTEL_IOMMU|CONFIG_AMD_IOMMU|CONFIG_IOMMU_DEFAULT|CONFIG_VFIO|CONFIG_DMA_API_DEBUG'

# Expected:
# CONFIG_INTEL_IOMMU=y
# CONFIG_INTEL_IOMMU_DEFAULT_ON=y
# CONFIG_IOMMU_DEFAULT_DMA_STRICT=y  (kernel 5.15+)
# CONFIG_AMD_IOMMU=y
# CONFIG_VFIO=m (or y if using passthrough)
# CONFIG_DMA_API_DEBUG=n  (production)

# --- Runtime IOMMU fault monitoring ---
# Watch IOMMU fault log
dmesg -w | grep -i "DMAR\|iommu\|fault"
# Or: journalctl -k -f | grep -i iommu

# --- Thunderbolt security ---
cat /sys/bus/thunderbolt/devices/*/security 2>/dev/null
# Expect: user, secure, or dponly — NEVER none
```

### 16.5 Defense-in-Depth Architecture

```
Layer 0: Physical Security
  - Data center access controls, Thunderbolt port disable in BIOS
  - PCIe slot locking for non-removable cards

Layer 1: BIOS/UEFI
  - Enable VT-d / AMD-Vi in firmware settings
  - Enable Secure Boot (prevents rootkit from disabling IOMMU)
  - DMAR/IVRS ACPI tables exposed to OS

Layer 2: Kernel Boot
  - intel_iommu=on iommu=strict
  - Interrupt remapping enabled
  - CONFIG_INTEL_IOMMU_DEFAULT_ON=y

Layer 3: IOMMU Domain Isolation
  - Per-device IOMMU domains (not shared)
  - ACS enabled on PCIe switches
  - Thunderbolt authorization enforced

Layer 4: Driver Layer
  - DMA masks correctly set
  - No iommu=pt for untrusted devices
  - Proper map/unmap discipline (no use-after-free of DMA addresses)
  - DMA_API_DEBUG in CI/test environments

Layer 5: Hypervisor / Container
  - VFIO with IOMMU for device passthrough
  - Nested IOMMU for VM isolation
  - cgroups device controller restricting /dev/vfio access

Layer 6: Runtime Monitoring
  - eBPF IOMMU fault monitoring (iommu_report_device_fault)
  - Anomaly detection: large coherent allocations, IOVA exhaustion
  - DMAR fault interrupt handler logging to SIEM
```

---

## 17. Performance

### 17.1 DMA Performance Bottlenecks and Solutions

```
Bottleneck 1: IOMMU TLB Miss
  Cause: Too many small (4K) IOMMU page table entries → TLB thrashing
  Solution:
    a) Use huge IOMMU pages (2M/1G): iommu_map with IOMMU_CACHE | huge page size
    b) Pre-allocate IOVA ranges and reuse (avoid constant map/unmap)
    c) Use DMA_ATTR_SKIP_CPU_SYNC for TX paths where CPU won't touch buffer after map

Bottleneck 2: IOVA Allocator Contention
  Cause: Single rbtree lock for IOVA allocation on multi-CPU systems
  Solution:
    a) Per-CPU IOVA caches (rcache): enabled by default in Linux 5.x
       Check: /sys/kernel/debug/iova/<domain>/
    b) Reserve IOVA range: iova_reserve_iova() for static mappings

Bottleneck 3: TLB Invalidation (IOTLB)
  Cause: IOMMU TLB must be invalidated on unmap; can stall bus
  Solution:
    a) iommu=lazy: batch invalidations (default on many platforms)
    b) IOMMU hardware QI (Queued Invalidation) interface: async invalidation
    c) Avoid frequent unmap: use streaming mappings that live for request lifetime

Bottleneck 4: Cache Coherency Overhead (non-x86)
  Cause: ARM requires explicit cache clean/invalidate per dma_map_*
  Solution:
    a) Use DMA_ATTR_NON_CONSISTENT: avoid cache ops, manage manually
    b) Use non-cacheable memory (device memory, write-combining BAR)
    c) Ensure buffers are cache-line aligned to avoid false sharing

Bottleneck 5: Bounce Buffer Copy (SWIOTLB)
  Cause: Extra memcpy for each DMA transfer
  Solution:
    a) Allocate buffers with GFP_DMA32 to avoid SWIOTLB
    b) Use dma_set_mask_and_coherent with correct mask to match HW
    c) Increase SWIOTLB pool size if fragmentation causes fallback
    d) On modern HW: if bounce is unavoidable, use ERMS (rep movs) for copy

Bottleneck 6: NUMA Cross-Socket DMA
  Cause: Device on socket 0 DMAing to memory on socket 1
  Solution:
    a) Allocate DMA buffers on device's NUMA node: alloc_pages_node()
    b) Verify NUMA placement: numastat -p <driver>
    c) Use CPU binding (taskset/numactl) for driver interrupt affinity
```

### 17.2 Benchmarking DMA Performance

```bash
# Kernel DMA latency (requires CONFIG_DMA_API_DEBUG_SG=y in test kernel)
# Use dmatest module:
modprobe dmatest channel=dma0chan0 timeout=2000 iterations=100 \
    threads_per_chan=1 buf_size=4096 verbose=1
cat /sys/kernel/debug/dmatest/run
echo 1 > /sys/kernel/debug/dmatest/run
dmesg | grep dmatest

# Measure dma_map_single overhead (with kprobe/ftrace):
echo 1 > /sys/kernel/debug/tracing/tracing_on
echo 'p:dma_map_entry dma_map_single_attrs' > /sys/kernel/debug/tracing/kprobe_events
echo 'r:dma_map_exit dma_map_single_attrs' >> /sys/kernel/debug/tracing/kprobe_events
echo 'dma_map_entry dma_map_exit' > /sys/kernel/debug/tracing/set_event
# ... run workload ...
cat /sys/kernel/debug/tracing/trace

# IOMMU TLB miss measurement (Intel IOMMU):
# Use uncore PMU: iommu_mem_requests, iommu_tlb_misses
perf stat -e uncore_imc/cas_count_read/,uncore_imc/cas_count_write/ \
    -a sleep 5  # baseline memory bandwidth

# NVMe DMA throughput benchmark:
fio --name=dma_bench --ioengine=io_uring --direct=1 \
    --rw=read --bs=128k --numjobs=4 --iodepth=128 \
    --runtime=30 --time_based --filename=/dev/nvme0n1 \
    --output-format=json+

# Network DMA throughput (iperf3 with zero-copy):
iperf3 -c <server> -Z -P 4 -t 30 -l 128K  # -Z enables zero-copy (sendfile)

# DPDK-based NIC DMA benchmark (testpmd):
dpdk-testpmd -l 0-3 -n 4 --vdev=net_memif0 -- \
    --nb-cores=3 --rxq=2 --txq=2 \
    --forward-mode=io --stats-period=1
```

### 17.3 Key Performance Metrics

```
Metric                           | Tool                    | Target
----------------------------------|-------------------------|------------------
DMA map latency (ns)             | bpftrace kprobe         | < 500ns (IOMMU)
DMA unmap latency (ns)           | bpftrace kprobe         | < 1μs
IOTLB miss rate (%)              | perf uncore events      | < 5%
SWIOTLB bounce rate (%)          | tracepoint + bpftrace   | 0% (goal)
NUMA cross-socket DMA (%)        | numastat                | < 10%
Coherent alloc latency (μs)      | bpftrace                | < 10μs
S/G coalescing ratio             | custom counter          | > 2:1 (2 phys : 1 DMA seg)
PCIe TLP utilization (%)         | PCIe PMU / lspci stat   | > 80% for bulk I/O
```

---

## 18. Testing and Fuzzing

### 18.1 Kernel DMA API Debug Mode

```bash
# Enable DMA API debug (CONFIG_DMA_API_DEBUG=y):
# This adds runtime checking:
#   - Double-map detection
#   - Use-after-free detection (unmap then re-use)
#   - Direction violation
#   - Overlap detection
#   - Incorrect size on unmap

# Boot parameters for DMA debug:
# (automatically active with CONFIG_DMA_API_DEBUG=y)
dma_debug=on

# Check DMA error counters:
cat /sys/kernel/debug/dma-api/error_count

# Force DMA debug failures (stress test):
echo 100 > /sys/kernel/debug/dma-api/fail_nth  # fail every 100th allocation

# List all active DMA mappings:
cat /sys/kernel/debug/dma-api/dump

# DMA API debug with CONFIG_DMA_API_DEBUG_SG=y:
# Also validates scatter-gather list integrity
```

### 18.2 syzkaller Fuzzing for DMA Drivers

```yaml
# syzkaller configuration for DMA driver fuzzing
# /etc/syzkaller/dma_fuzzer.cfg
{
  "target": "linux/amd64",
  "http": "localhost:56741",
  "workdir": "/var/syzkaller",
  "kernel_obj": "/path/to/kernel/build",
  "image": "/path/to/syzkaller.img",
  "syzkaller": "/usr/local/bin/syz-manager",
  "procs": 4,
  "type": "qemu",
  "vm": {
    "count": 4,
    "kernel": "/path/to/bzImage",
    "cpu": 2,
    "mem": 2048
  },
  "enable_syscalls": [
    "ioctl$VFIO_*",        
    "mmap$VFIO",
    "read$VFIO",
    "write$VFIO",
    "open$vfio_dev",
    "open$vfio_group",
    "openat$vfio_container"
  ]
}
```

### 18.3 Unit Tests for DMA Driver

```c
/* mydev_test.c — KUnit tests for DMA driver
 * Build: CONFIG_KUNIT=y, CONFIG_MYDEV_TEST=y
 */
#include <kunit/test.h>
#include <linux/dma-mapping.h>
#include <linux/pci.h>
#include "mydev_dma.h"

/* Test: DMA mask setup */
static void mydev_test_dma_mask(struct kunit *test)
{
    struct device *dev = /* mock device */ NULL;
    int ret;

    ret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64));
    KUNIT_EXPECT_EQ(test, ret, 0);
    KUNIT_EXPECT_EQ(test, *dev->dma_mask, DMA_BIT_MASK(64));
}

/* Test: coherent allocation alignment */
static void mydev_test_coherent_alloc(struct kunit *test)
{
    dma_addr_t dma_addr;
    void *buf;
    struct device *dev = kunit_get_current_test()->priv;

    buf = dma_alloc_coherent(dev, PAGE_SIZE, &dma_addr, GFP_KERNEL);
    KUNIT_ASSERT_NOT_NULL(test, buf);
    KUNIT_EXPECT_EQ(test, dma_addr & (PAGE_SIZE - 1), 0ULL);  /* page-aligned */
    KUNIT_EXPECT_NOT_ERR_OR_NULL(test, (void *)(uintptr_t)dma_addr);

    dma_free_coherent(dev, PAGE_SIZE, buf, dma_addr);
}

/* Test: streaming DMA direction enforcement */
static void mydev_test_streaming_direction(struct kunit *test)
{
    struct device *dev = kunit_get_current_test()->priv;
    char *buf = kunit_kmalloc(test, 512, GFP_KERNEL);
    dma_addr_t da;

    KUNIT_ASSERT_NOT_NULL(test, buf);

    da = dma_map_single(dev, buf, 512, DMA_TO_DEVICE);
    KUNIT_EXPECT_FALSE(test, dma_mapping_error(dev, da));

    /* Verify: CPU should not access buf here (DMA_API_DEBUG will catch it) */

    dma_unmap_single(dev, da, 512, DMA_TO_DEVICE);
}

/* Test: scatter-gather mapping and coalescing */
static void mydev_test_sg_mapping(struct kunit *test)
{
    struct device *dev = kunit_get_current_test()->priv;
    struct scatterlist sg[4];
    struct page *pages[4];
    int i, mapped;

    sg_init_table(sg, 4);

    /* Allocate physically adjacent pages */
    for (i = 0; i < 4; i++) {
        pages[i] = alloc_page(GFP_KERNEL);
        KUNIT_ASSERT_NOT_NULL(test, pages[i]);
        sg_set_page(&sg[i], pages[i], PAGE_SIZE, 0);
    }
    sg_mark_end(&sg[3]);

    mapped = dma_map_sg(dev, sg, 4, DMA_FROM_DEVICE);
    KUNIT_EXPECT_GT(test, mapped, 0);
    KUNIT_EXPECT_LE(test, mapped, 4);  /* coalescing may reduce count */

    /* Verify all DMA lengths sum to total */
    size_t total = 0;
    struct scatterlist *s;
    for_each_sg(sg, s, mapped, i)
        total += sg_dma_len(s);
    KUNIT_EXPECT_EQ(test, total, (size_t)(4 * PAGE_SIZE));

    dma_unmap_sg(dev, sg, 4, DMA_FROM_DEVICE);
    for (i = 0; i < 4; i++)
        __free_page(pages[i]);
}

static struct kunit_case mydev_test_cases[] = {
    KUNIT_CASE(mydev_test_dma_mask),
    KUNIT_CASE(mydev_test_coherent_alloc),
    KUNIT_CASE(mydev_test_streaming_direction),
    KUNIT_CASE(mydev_test_sg_mapping),
    {}
};

static struct kunit_suite mydev_test_suite = {
    .name  = "mydev_dma",
    .test_cases = mydev_test_cases,
};
kunit_test_suite(mydev_test_suite);
```

### 18.4 Fuzzing with libfuzzer (Userspace VFIO)

```c
/* fuzz_vfio_dma.c — libfuzzer target for VFIO DMA ioctl paths */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/vfio.h>

/* Fuzzer entry point — called by libfuzzer */
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    if (size < sizeof(struct vfio_iommu_type1_dma_map))
        return 0;

    int container_fd = open("/dev/vfio/vfio", O_RDWR);
    if (container_fd < 0) return 0;

    /* Fuzz VFIO_IOMMU_MAP_DMA ioctl */
    struct vfio_iommu_type1_dma_map dma_map;
    memcpy(&dma_map, data, sizeof(dma_map));
    dma_map.argsz = sizeof(dma_map);

    /* Intentionally pass fuzzed fields — kernel must handle gracefully */
    ioctl(container_fd, VFIO_IOMMU_MAP_DMA, &dma_map);

    close(container_fd);
    return 0;
}
```

```bash
# Build and run fuzzer
clang -O1 -fsanitize=fuzzer,address,undefined \
    -o fuzz_vfio_dma fuzz_vfio_dma.c
./fuzz_vfio_dma -max_len=1024 -jobs=4 corpus/
```

---

## 19. Roll-out and Ops

### 19.1 Deploying IOMMU Changes in Production

```bash
# --- Staged rollout plan for IOMMU enforcement ---

# Stage 1: Audit (no change to behavior)
# Add to kernel cmdline: iommu=on intel_iommu=on (if not already)
# Check dmesg for IOMMU errors/warnings
# Monitor: dmesg | grep -E "DMAR-IR|IOMMU|fault" for 24h
# Metrics: track DMA error_count, map failures

# Stage 2: Enable strict mode on canary nodes
# Add: iommu=strict iommu.passthrough=0
# Measure latency impact: compare DMA map latency before/after (bpftrace)
# Expected overhead: 5–15% for I/O-bound workloads

# Stage 3: Enable DMA API debug on test nodes
# Add: CONFIG_DMA_API_DEBUG=y to test kernel
# Run full I/O test suite, check: cat /sys/kernel/debug/dma-api/error_count

# Stage 4: Production rollout
# Gradual: 1% → 10% → 50% → 100% of fleet
# Rollback trigger: DMA error_count > 0 in first 1h, or I/O latency p99 > 2x baseline

# --- Rollback procedure ---
# 1. Revert kernel cmdline: remove iommu=strict, reboot with iommu=lazy
# 2. If driver bug: modprobe -r <driver>; modprobe <driver> with debug params
# 3. Emergency: iommu=pt (TEMPORARY only, creates security hole)
#    Must create security incident and remediate within 24h

# --- Monitoring ---
# IOMMU fault rate (should be 0):
# /sys/kernel/debug/iommu/intel/dmar_perf_latency (Intel)
# or custom eBPF probe on iommu_report_device_fault

# DMA allocation failure rate:
cat /sys/kernel/debug/dma-api/error_count  # for test kernels

# SWIOTLB usage (should be 0 for modern HW):
# Add counter via eBPF tracepoint:swiotlb:swiotlb_bounced
```

### 19.2 Kernel Driver Lifecycle

```bash
# Module deployment
# 1. Sign module (for Secure Boot):
openssl genrsa -out signing_key.pem 4096
openssl req -new -x509 -key signing_key.pem -out signing_cert.pem -days 3650
/usr/src/linux-headers-$(uname -r)/scripts/sign-file \
    sha256 signing_key.pem signing_cert.pem mydev.ko

# 2. Load with debug:
modprobe mydev dyndbg=+pflmt  # enable debug prints with file/line/module/thread

# 3. Monitor immediately after load:
dmesg -T | grep -E "mydev|DMAR|iommu" | tail -50
cat /sys/kernel/debug/dma-api/error_count

# 4. Graceful unload sequence:
# Ensure no active DMA: driver's remove() must call pci_clear_master() AFTER
# stopping DMA engine and waiting for in-flight transfers
modprobe -r mydev
dmesg | grep "mydev: removed"

# 5. Verify IOMMU cleanup:
# After driver unload, its IOVA space should be freed
# (check via /sys/kernel/debug/iommu/)
```

### 19.3 Next 3 Steps

```
Step 1 — Harden existing fleet
  Audit all nodes: confirm intel_iommu=on iommu=strict in /proc/cmdline
  Script: for node in $(fleet list); do ssh $node cat /proc/cmdline; done | grep -v iommu=strict
  Action: Add to Puppet/Salt/Ansible: kernel parameter management
  Timeline: 1 sprint

Step 2 — Deploy eBPF IOMMU fault monitoring
  Build iommu_fault.bpf.c from §13.5 into your observability stack
  Integrate with Prometheus: export fault count as gauge iommu_fault_total{device, reason}
  Alert: iommu_fault_total > 0 triggers PagerDuty (P1)
  Timeline: 1 sprint

Step 3 — SR-IOV VF isolation audit
  For every SR-IOV device: verify each VF has its own IOMMU group
  Script: check /sys/kernel/iommu_groups/*/devices/ for multi-VF groups
  Action: Replace non-ACS switches; test ACS-compliant NICs/HBAs
  Timeline: 1 quarter
```

---

## 20. References

### Linux Kernel Source (6.x)

```
kernel/dma/                    — core DMA subsystem
drivers/iommu/                 — IOMMU drivers (Intel VT-d, AMD-Vi, ARM SMMU)
drivers/vfio/                  — VFIO infrastructure
drivers/dma/                   — DMA engine drivers
include/linux/dma-mapping.h    — public DMA API
include/linux/dma-map-ops.h    — dma_map_ops interface
include/linux/iommu.h          — IOMMU core API
Documentation/core-api/dma-api.rst
Documentation/core-api/dma-api-howto.rst
Documentation/driver-api/vfio.rst
Documentation/PCI/pci.rst
```

### Specifications

```
Intel VT-d Specification: Intel Virtualization Technology for Directed I/O
  https://cdrdv2.intel.com/v1/dl/getContent/671081

ARM SMMU Architecture Specification v3.3:
  https://developer.arm.com/documentation/ihi0070/

PCIe Base Specification 6.0:
  https://pcisig.com/specifications

PCIe ACS (Access Control Services) Specification:
  Part of PCIe Base Spec, Chapter 6.12

AMD IOMMU Architecture Specification v3.05:
  https://www.amd.com/system/files/TechDocs/48882_IOMMU.pdf
```

### Research Papers

```
Thunderclap: Exploring Vulnerabilities in Operating System IOMMU Protection
via DMA from Untrustworthy Peripherals (NDSS 2019)
  Markettos, Rothwell, et al.
  https://thunderclap.io/

IOMMU: Strategies for Mitigating the IOTLB Bottleneck (IEEE CAL)
  — performance analysis of IOMMU overhead

DMA Is Dangerous: How IOMMU Protection Fails (BlackHat USA 2021)
  — practical attacks and mitigations

Rowhammer.js: A Remote Software-Induced Fault Attack in JavaScript
  — DMA-induced bit flips via Rowhammer
```

### Books and Documentation

```
"Linux Device Drivers, 3rd Edition" — Corbet, Rubini, Kroah-Hartman
  Chapter 15: Memory Mapping and DMA
  https://lwn.net/Kernel/LDD3/

"Understanding the Linux Kernel, 3rd Edition" — Bovet, Cesati
  Chapter 2: Memory Addressing

LWN.net DMA Articles:
  "DMA and the Linux kernel" — https://lwn.net/Articles/486301/
  "The IOMMU and VFIO"      — https://lwn.net/Articles/509367/
  "Shared virtual addressing"— https://lwn.net/Articles/747230/
  "P2P DMA"                  — https://lwn.net/Articles/736584/
  "Rust in the kernel"       — https://lwn.net/Articles/927337/

Rust-for-Linux:
  https://rust-for-linux.com/
  https://github.com/Rust-for-Linux/linux

eBPF/BCC DMA tracing:
  https://github.com/iovisor/bcc
  https://github.com/libbpf/libbpf
  https://nakryiko.com/posts/bpf-core-reference-guide/

VFIO documentation:
  https://www.kernel.org/doc/html/latest/driver-api/vfio.html
  https://github.com/qemu/qemu/blob/master/docs/system/device-emulation.rst

DPDK (userspace DMA reference implementation):
  https://doc.dpdk.org/guides/prog_guide/mempool_lib.html
  https://doc.dpdk.org/guides/prog_guide/iova.html

SPDK (userspace NVMe DMA):
  https://spdk.io/doc/memory.html
```

---

*Document Version: 1.0 | Kernel Reference: Linux 6.8 | Rust-for-Linux: 6.8-based*
*Security Classification: Internal Engineering Reference*\

This will be a large, deeply technical document. Building it now.**3,856 lines / 127 KB** — here's the structure of what's covered:

---

**Summary (8 lines):**
DMA exists to offload bulk memory transfers from the CPU to peripheral hardware, operating across four distinct address spaces (PA, VA, IOVA, Bus Address). The IOMMU is the critical security boundary — without it, any bus-mastering device can read/write arbitrary physical memory. Linux's DMA subsystem is a polymorphic stack (`dma_map_ops`) that adapts coherent, streaming, and scatter-gather operations to IOMMU, SWIOTLB, or passthrough backends. Cache coherency semantics differ fundamentally between x86 (hardware-snooped) and ARM (explicit `clean/invalidate` required). Security-critical properties — IOMMU group isolation, ACS enforcement, interrupt remapping — must all be active simultaneously, as any single bypass defeats the model. eBPF lets you observe every map/unmap event and IOMMU fault at near-zero overhead in production. The Rust abstractions enforce correct ownership (no use-after-free of DMA addresses) at compile time — a structural improvement over C. All production deployments must verify `iommu=strict` and per-device IOMMU groups.

---

**What's covered:**

| Section | Content |
|---|---|
| §1–2 | First-principles, ISA→PCIe evolution, cache coherency by arch, NUMA DMA |
| §3 | VT-d, AMD-Vi, ARM SMMUv3 internals, IOMMU groups, ACS, SVA/PASID |
| §4–6 | `dma_map_ops` architecture, IOVA allocator, coherent/streaming/S-G API with full semantics |
| §7–9 | DMA Engine subsystem, Intel DSA, SWIOTLB bounce buffers, SEV/TDX confidential VMs, P2P DMA |
| §10–12 | SR-IOV isolation, VFIO userspace DMA internals, KVM nested IOMMU, virtio DMA |
| §13 | 6 eBPF programs: map latency histogram, SWIOTLB bounce detection, IOMMU fault monitor, security anomaly detection, + bpftrace one-liners |
| §14 | Full C PCIe driver: DMA masks, coherent descriptor rings, streaming TX/RX, scatter-gather, MSI-X completions |
| §14.2 | Complete C VFIO userspace driver with IOMMU map/unmap and BAR mmap |
| §15 | Rust kernel abstractions (CoherentAllocation, StreamingMapping with RAII), Rust PCIe driver skeleton, Rust VFIO userspace library with full tests |
| §16 | Threat model (Thunderclap, IOMMU bypass, IOVA exhaustion, ACS bypass), hardening checklist, defense-in-depth layers |
| §17–18 | Perf bottlenecks (IOTLB miss, IOVA contention, bounce copy), benchmarking commands, KUnit tests, syzkaller config, libfuzzer target |
| §19 | Staged IOMMU rollout plan, rollback triggers, signing, eBPF monitoring integration |

**Next 3 steps** are at the end of §19 — hardening fleet, eBPF IOMMU fault alerting, and SR-IOV VF isolation audit.