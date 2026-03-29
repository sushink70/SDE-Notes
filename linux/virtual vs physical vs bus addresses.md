# Virtual vs Physical vs Bus Addresses: The Complete Systems Guide

> **Target audience**: Systems programmers working with C, Rust, Go on Linux x86-64  
> **Scope**: From CPU pins to kernel internals to language-level abstractions  
> **Depth**: Production-grade understanding, not textbook theory

---

## Table of Contents

1. [The Three Address Spaces — Mental Model](#1-the-three-address-spaces--mental-model)
2. [Physical Addresses](#2-physical-addresses)
3. [Virtual Addresses](#3-virtual-addresses)
4. [Bus / DMA Addresses](#4-bus--dma-addresses)
5. [Hardware: MMU, TLB, Cache Hierarchy](#5-hardware-mmu-tlb-cache-hierarchy)
6. [Linux x86-64 Virtual Address Layout](#6-linux-x86-64-virtual-address-layout)
7. [Page Tables: 4-Level and 5-Level](#7-page-tables-4-level-and-5-level)
8. [Address Translation: Full Walk-through](#8-address-translation-full-walk-through)
9. [NUMA, Physical Memory Zones](#9-numa-physical-memory-zones)
10. [DMA, IOMMU, and Bus Mastering](#10-dma-iommu-and-bus-mastering)
11. [Linux Kernel Memory APIs](#11-linux-kernel-memory-apis)
12. [C — Userspace Memory Introspection](#12-c--userspace-memory-introspection)
13. [Rust — Safe and Unsafe Memory Introspection](#13-rust--safe-and-unsafe-memory-introspection)
14. [Go — Runtime Heap, Stack, and Address Visibility](#14-go--runtime-heap-stack-and-address-visibility)
15. [ASLR, KASLR, and Security Implications](#15-aslr-kaslr-and-security-implications)
16. [Memory Mapped I/O (MMIO)](#16-memory-mapped-io-mmio)
17. [Shared Memory Across Processes](#17-shared-memory-across-processes)
18. [Common Pitfalls & War Stories](#18-common-pitfalls--war-stories)
19. [Hands-on Exercises](#19-hands-on-exercises)
20. [Security Checklist](#20-security-checklist)
21. [Further Reading](#21-further-reading)

---

## 1. The Three Address Spaces — Mental Model

### One-line Summary

Three coordinate systems exist for the same physical memory: the CPU speaks **virtual**, RAM speaks **physical**, and peripheral buses speak **bus/DMA**. Hardware translates between them.

### The Analogy

Think of a large city with a postal system:

- **Physical address**: The GPS coordinate of a building — absolute, unique, real. Only city planners and emergency services use it directly.
- **Virtual address**: The street address on an envelope — what you write when sending mail. Multiple buildings can share the same street address in different cities (processes). The post office (MMU) routes correctly.
- **Bus address**: The address used by courier services (DMA controllers, GPUs, NICs). They use a different map — their own coordinate system — managed by a separate routing layer (IOMMU).

### The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CPU Core                                  │
│  ┌──────────────────┐     ┌────────────────────────────────┐    │
│  │ User / Kernel    │     │  Virtual Address (64-bit ptr)  │    │
│  │    Program       │────▶│  e.g., 0x7fff_dead_beef_0000   │    │
│  └──────────────────┘     └────────────┬───────────────────┘    │
│                                        │                         │
│                                  ┌─────▼──────┐                 │
│                                  │    MMU     │                 │
│                                  │ (page walk)│                 │
│                                  └─────┬──────┘                 │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                          ┌──────────────▼────────────────┐
                          │  Physical Address              │
                          │  e.g., 0x0000_0002_3abc_0000   │
                          └──────────────┬────────────────┘
                                         │
                    ┌────────────────────┼──────────────────────┐
                    │                    │                        │
             ┌──────▼──────┐    ┌───────▼──────┐    ┌─────────▼───────┐
             │  DRAM/RAM   │    │  Memory Ctlr │    │  IOMMU / PCIe   │
             │ (physical   │    │  (MCH/IMC)   │    │  (bus address   │
             │  storage)   │    └──────────────┘    │   translation)  │
             └─────────────┘                        └──────┬──────────┘
                                                           │
                                                    ┌──────▼──────┐
                                                    │  Bus Address │
                                                    │  (DMA addr)  │
                                                    │  e.g., NIC   │
                                                    │  GPU, NVME   │
                                                    └─────────────┘
```

---

## 2. Physical Addresses

### What They Are

A **physical address** directly identifies a byte location in the system's physical address space. This space includes:

- DRAM (main memory)
- ROM/firmware regions (BIOS, UEFI)
- Memory-Mapped I/O (MMIO) for PCI devices, APIC, etc.
- Reserved holes (legacy ISA, VGA, etc.)

On x86-64, the physical address bus is 52 bits wide (theoretical maximum ~4 PB), though most consumer hardware implements 36–46 bits.

### Physical Address Space Map (Typical x86-64 System, 16 GB RAM)

```
Physical Address   Size      Contents
─────────────────────────────────────────────────────────────────
0x0000_0000        640 KB    Conventional Memory (usable)
0x000A_0000        384 KB    VGA / Legacy BIOS area (reserved)
0x000F_0000        64 KB     BIOS ROM shadow
0x0010_0000        ~15.5 GB  Extended Memory (usable RAM)
0x3C00_0000_0000   varies    PCIe MMIO BARs (assigned by firmware)
0xFEC0_0000        4 KB      I/O APIC (MMIO)
0xFEE0_0000        4 KB      Local APIC (MMIO)
0xFFFF_0000        64 KB     Legacy BIOS
```

Check your system:

```bash
# Kernel's view of physical memory layout
sudo cat /proc/iomem

# Physical memory ranges
sudo dmidecode --type 17  # DIMM info
sudo dmidecode --type 6   # Memory module

# Physical page count per NUMA node
cat /sys/devices/system/node/node0/meminfo
```

### How the OS Discovers Physical Memory

The BIOS/UEFI populates an **E820 memory map** (for legacy BIOS) or **EFI memory map** (for UEFI). The Linux bootloader reads this and passes it to the kernel via the boot parameters.

```bash
# E820 map as seen by the kernel at boot
sudo dmesg | grep -E 'BIOS-e820|e820:'

# Example output:
# [    0.000000] BIOS-e820: [mem 0x0000000000000000-0x000000000009fbff] usable
# [    0.000000] BIOS-e820: [mem 0x00000000000f0000-0x00000000000fffff] reserved
# [    0.000000] BIOS-e820: [mem 0x0000000000100000-0x00000000bfecffff] usable
# [    0.000000] BIOS-e820: [mem 0x00000000bfed0000-0x00000000bfefefff] ACPI data
# [    0.000000] BIOS-e820: [mem 0x0000000100000000-0x000000023fffffff] usable
```

### Physical Page Frames

Physical memory is divided into fixed-size **page frames** (4 KB on x86). Each frame has a **Page Frame Number (PFN)**:

```
Physical Address = PFN × PAGE_SIZE + offset
PFN = Physical Address >> 12   (for 4 KB pages)
```

The kernel maintains a `struct page` for every physical page frame — this is the `mem_map` array.

---

## 3. Virtual Addresses

### What They Are

A **virtual address** is what your program (and the CPU's instruction pointer) actually uses. The CPU's Memory Management Unit (MMU) translates virtual → physical on every memory access. No two processes share the same virtual address space (unless explicitly mapped).

### Key Properties

1. **Isolation**: Each process has its own full virtual address space (2^48 or 2^57 bytes on x86-64). A pointer value in process A has no relation to the same value in process B.
2. **Sparse**: Only a tiny fraction of the virtual space is actually mapped. Accessing an unmapped region triggers a page fault → SIGSEGV.
3. **Contiguous illusion**: Virtually contiguous pages can be physically scattered. The page table handles the scatter-gather.
4. **Protection bits**: Each page mapping carries R/W/X/U permissions enforced by hardware.

### Virtual Address Structure on x86-64 (4-level paging)

```
63        48 47      39 38      30 29      21 20      12 11         0
┌───────────┬──────────┬──────────┬──────────┬──────────┬────────────┐
│  Sign ext │  PGD idx │  PUD idx │  PMD idx │  PTE idx │   Offset   │
│  (16 bit) │  (9 bit) │  (9 bit) │  (9 bit) │  (9 bit) │  (12 bit)  │
└───────────┴──────────┴──────────┴──────────┴──────────┴────────────┘

Bits 63-48 must be copies of bit 47 (canonical form)
Valid ranges:
  0x0000_0000_0000_0000 – 0x0000_7FFF_FFFF_FFFF  (user space, 128 TB)
  0xFFFF_8000_0000_0000 – 0xFFFF_FFFF_FFFF_FFFF  (kernel space, 128 TB)
Non-canonical addresses (bits 63-48 don't match bit 47) → #GP fault
```

### Checking Virtual Mappings in Linux

```bash
# Process virtual address space
cat /proc/self/maps
# or more detail:
cat /proc/self/smaps

# Example output from /proc/self/maps:
# 55f3c8a00000-55f3c8a01000 r--p 00000000 fd:01 123456 /usr/bin/cat
# 55f3c8a01000-55f3c8a02000 r-xp 00001000 fd:01 123456 /usr/bin/cat
# 7fff12340000-7fff12361000 rw-p 00000000 00:00 0       [stack]
# 7ffff7ffd000-7ffff7fff000 r--p 00000000 00:00 0       [vvar]
# 7ffff7fff000-7ffff8000000 r-xp 00000000 00:00 0       [vdso]

# Translate virtual → physical (requires root)
# Uses /proc/PID/pagemap (see C code below)
```

---

## 4. Bus / DMA Addresses

### What They Are

When a device (NIC, GPU, NVMe, USB host controller) does **Direct Memory Access (DMA)**, it reads/writes physical memory bypassing the CPU. It uses a **bus address** (also called **DMA address** or **I/O virtual address** in IOMMU context).

On simple systems without an IOMMU, bus address == physical address.  
On systems with an **IOMMU** (Intel VT-d, AMD-Vi), the IOMMU has its own page tables that translate device bus addresses to physical addresses.

### Why Bus Addresses Differ from Physical Addresses

1. **IOMMU remapping**: Lets the kernel isolate devices; a compromised GPU can't DMA to kernel memory it shouldn't see.
2. **Legacy 32-bit DMA**: Old ISA/PCI devices can only address 32-bit bus addresses (4 GB). The IOMMU can "bounce" these to arbitrary physical locations using a bounce buffer.
3. **NUMA topology**: On NUMA systems, the memory controller on different sockets may assign different bus addresses to the same physical address.
4. **Virtualization**: In a VM, the hypervisor (KVM/QEMU) may present different physical addresses to the guest than the host's actual physical addresses.

### IOMMU Address Translation

```
Device issues DMA to Bus Address 0x8000_0000
          │
          ▼
    ┌──────────┐
    │  IOMMU   │  (I/O page tables, one per device/group)
    └────┬─────┘
         │ translates to
         ▼
Physical Address 0x2_3abc_0000  (actual DRAM location)
```

```bash
# Check if IOMMU is active
sudo dmesg | grep -i iommu
# Intel VT-d:
# [    0.050409] DMAR: IOMMU enabled
# AMD-Vi:
# [    0.088762] AMD-Vi: AMD IOMMUv2 loaded and initialized

# IOMMU groups (device isolation)
ls /sys/kernel/iommu_groups/

# Per-device IOMMU domain
find /sys/bus/pci/devices/*/iommu_group -type l
```

---

## 5. Hardware: MMU, TLB, Cache Hierarchy

### The MMU (Memory Management Unit)

The MMU is a hardware unit inside the CPU that performs virtual-to-physical translation. Key components:

1. **CR3 register**: Points to the top-level page table (PGD) of the current process. Updated on context switch.
2. **Page walker**: Hardware state machine that traverses the 4/5-level page table structure.
3. **TLB** (Translation Lookaside Buffer): Cache of recent virtual→physical translations.
4. **Page Fault logic**: When a virtual address is not mapped or violates permissions, raises #PF exception → kernel's page fault handler.

### The TLB

The TLB is a fully-associative cache holding ~1,024–8,192 entries per core (varies by CPU). Each entry maps one virtual page → physical frame + permission bits.

```
TLB Entry Structure:
┌──────────────────────────────────────────────────────┐
│ PCID(12b) │ VPN(36b) │ PFN(40b) │ Flags(R/W/X/U/G) │
└──────────────────────────────────────────────────────┘
PCID = Process Context ID (avoids TLB flush on context switch for PCID-aware kernels)
VPN  = Virtual Page Number (bits 47:12)
PFN  = Physical Frame Number
```

TLB misses cause a **page table walk** (4 memory accesses for 4-level paging), taking ~10–100 ns. TLB hit: ~1 ns.

TLB flush events (expensive):
- `mov cr3, rax` (context switch without PCID)
- `invlpg addr` (single-page invalidation)
- `wbinvd` (full invalidation)
- Cross-core TLB shootdown (IPI to other cores) — tracked in `/proc/interrupts` as `TLB`

```bash
# TLB shootdown IPIs (column TLB in /proc/interrupts)
watch -n 1 'grep TLB /proc/interrupts'

# Huge pages reduce TLB pressure (2 MB pages use fewer TLB entries)
cat /proc/meminfo | grep -i huge
echo 512 | sudo tee /proc/sys/vm/nr_hugepages
```

### Cache Hierarchy and Physical Addresses

Modern CPUs use **physically-indexed, physically-tagged (PIPT)** L1/L2/L3 caches. This means:

1. Virtual address → MMU → physical address
2. Physical address → cache lookup

The cache uses physical addresses to avoid aliasing (two virtual addresses pointing to same physical frame would appear as separate cache lines in a VIVT cache, causing inconsistency).

**Cache line** = 64 bytes on x86-64.  
**Cache set index** = bits [11:6] of physical address (for a typical 32 KB, 8-way L1).  
The OS must be careful with **cache coloring** and **page alignment** for performance-critical code.

---

## 6. Linux x86-64 Virtual Address Layout

### Complete Kernel Memory Map (x86-64, 4-level paging, 5-level in parentheses)

```
Virtual Address Range                    Size     Purpose
──────────────────────────────────────────────────────────────────────────────
0000_0000_0000_0000 – 0000_7FFF_FFFF_FFFF  128 TB   User space
  ├── text/code (r-xp)                              [program binary]
  ├── rodata (r--p)                                 [constants]
  ├── data/bss (rw-p)                               [globals]
  ├── heap (rw-p)                                   [malloc / sbrk]
  ├── mmap region (grows downward)                  [shared libs, anonymous]
  ├── [vvar]                                        [vsyscall data page]
  ├── [vdso]                                        [virtual dynamic SO]
  └── stack (rw-p, grows downward)                  [thread stacks]

ffff_8000_0000_0000 – ffff_87ff_ffff_ffff  8 TB     Direct mapping of all physical memory
ffff_8800_0000_0000 – ffff_887f_ffff_ffff  512 GB   LDT remap (for Xen)
ffff_c900_0000_0000 – ffff_e8ff_ffff_ffff  32 TB    vmalloc / ioremap space
ffff_e900_0000_0000 – ffff_e9ff_ffff_ffff  1 TB     Unused
ffff_ea00_0000_0000 – ffff_eaff_ffff_ffff  1 TB     EFI region mapping
ffff_f000_0000_0000 – ffff_f7ff_ffff_ffff  8 TB     cpu_entry_area mapping
ffff_fe00_0000_0000 – ffff_feff_ffff_ffff  1 TB     fixmap
ffff_ff00_0000_0000 – ffff_ff7f_ffff_ffff  512 GB   %esp fixup stacks
ffff_ff80_0000_0000 – ffff_ffff_7fff_ffff  ~512 GB  Unused
ffff_ffff_8000_0000 – ffff_ffff_ffff_ffff  2 GB     Kernel text, data, BSS
```

### The Direct Mapping Region

The most important kernel memory region: the **direct mapping** at `0xffff_8000_0000_0000` maps ALL physical memory linearly. This means:

```c
// In kernel code:
// Virtual address of any physical address is simply:
void *virt = phys_to_virt(phys_addr);
// Which computes: virt = phys + PAGE_OFFSET
// PAGE_OFFSET = 0xffff_8000_0000_0000

// Conversely:
phys_addr_t phys = virt_to_phys(virt);
// phys = virt - PAGE_OFFSET
```

This is why kernel bugs that corrupt the direct mapping are catastrophic — it's a window into all of physical memory.

```bash
# See kernel symbols and their virtual addresses
sudo cat /proc/kallsyms | head -20
sudo cat /proc/kallsyms | grep ' T ' | head -10  # text symbols

# Kernel load address (with KASLR, changes each boot)
sudo cat /proc/kallsyms | grep _text
# e.g.: ffffffff92200000 T _text
```

---

## 7. Page Tables: 4-Level and 5-Level

### 4-Level Page Table Structure (48-bit virtual address)

```
CR3 → PGD (Page Global Directory)    [512 entries × 8 bytes = 4 KB page]
         └─→ PUD (Page Upper Directory) [512 entries × 8 bytes]
                └─→ PMD (Page Middle Directory) [512 entries × 8 bytes]
                       └─→ PTE (Page Table Entry) [512 entries × 8 bytes]
                                └─→ Physical Page (4 KB)
```

Each level indexes 9 bits of the virtual address. Total: 9+9+9+9+12 = 48 bits.

### Page Table Entry (PTE) Format on x86-64

```
Bit(s)  Field        Description
────────────────────────────────────────────────────────────────────────
0       P            Present: 1 = page is in physical memory
1       R/W          Read/Write: 0 = read-only, 1 = writable
2       U/S          User/Supervisor: 0 = kernel only, 1 = user accessible
3       PWT          Page-Level Write-Through cache policy
4       PCD          Page-Level Cache Disable
5       A            Accessed: set by hardware on any access
6       D            Dirty: set by hardware on write (PTE only)
7       PS / PAT     Page Size (PMD/PUD) or PAT index
8       G            Global: not flushed from TLB on CR3 write (kernel pages)
9-11    AVL          Available for OS use (Linux uses for soft-dirty, etc.)
12-51   PFN          Physical Frame Number (physical address >> 12)
52-62   AVL          Available for OS use (Linux: swap type, file offset, etc.)
63      XD/NX        Execute Disable: 1 = page is non-executable (NX bit)
```

### Huge Pages: 2 MB and 1 GB Pages

```
2 MB pages (PMD-level): PMD.PS=1 → PMD points directly to 2 MB frame
  Virtual address: [9-PGD][9-PUD][9-PMD][21-offset]
  
1 GB pages (PUD-level): PUD.PS=1 → PUD points directly to 1 GB frame
  Virtual address: [9-PGD][9-PUD][30-offset]
```

Huge pages reduce TLB pressure dramatically: mapping 1 GB needs 1 TLB entry vs 262,144 entries with 4 KB pages.

```bash
# Transparent Huge Pages status
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# Force a range to use huge pages
# (see madvise(2) with MADV_HUGEPAGE in C code below)

# Check huge page usage
cat /proc/meminfo | grep -i anon_huge
grep -i hugepages /proc/meminfo
```

### 5-Level Paging (LA57, 57-bit virtual address)

Introduced in Linux 4.14, requires Intel Ice Lake or later (CPUID.7.0:ECX[16]):

```
CR4.LA57 = 1 enables 5-level paging
Adds P4D level between PGD and PUD
Virtual address: [9-PGD][9-P4D][9-PUD][9-PMD][9-PTE][12-offset] = 57 bits
User space: 128 PB (vs 128 TB with 4-level)
```

```bash
# Check if 5-level paging is active
grep -i "page_size_5level\|la57" /proc/cpuinfo || true
cat /proc/cpuinfo | grep la57
# Check kernel config
zcat /proc/config.gz | grep X86_5LEVEL || sudo grep X86_5LEVEL /boot/config-$(uname -r)
```

---

## 8. Address Translation: Full Walk-through

### Step-by-Step: Accessing Virtual Address `0x7fff_1234_5678`

```
Virtual address: 0x0000_7FFF_1234_5678
Binary:          0000 0000 0000 0000  0111 1111 1111 1111  0001 0010 0011 0100  0101 0110 0111 1000

Extract fields (4-level paging):
  Bits 63-48: 0x0000         (canonical, user space ✓)
  Bits 47-39: 0b0_1111_1111  = 0xFF  = 255  → PGD[255]
  Bits 38-30: 0b1_1111_1110  = 0x1FE = 510  → PUD[510]
  Bits 29-21: 0b0_0100_1000  = 0x048 = 72   → PMD[72]
  Bits 20-12: 0b1_1010_0101  = 0x1A5 = 421  → PTE[421]
  Bits 11-0:  0b0110_0111_1000 = 0x678       → offset within page

Translation walk:
  1. CR3 → physical address of PGD (loaded on context switch)
  2. PGD[255] → physical address of PUD table (if P=1)
  3. PUD[510] → physical address of PMD table (if P=1, PS=0)
  4. PMD[72]  → physical address of PTE table (if P=1, PS=0)
  5. PTE[421] → PFN × 4096 = physical page base (if P=1)
  6. physical_addr = PFN×4096 + 0x678
```

### What Happens on TLB Miss (Page Table Walk)

```
CPU issues load to virtual address VA
         │
         ▼
    Check TLB ──── HIT ──→ Physical address → Cache/RAM
         │
        MISS
         │
         ▼
   Hardware Page Walker (in CPU microcode)
         │
         ├── Read PGD entry from CR3 + PGD_index×8   [memory access 1]
         │   If not Present → #PF (page fault)
         │
         ├── Read PUD entry from PGD.addr + PUD_index×8  [memory access 2]
         │   If not Present → #PF
         │   If PS=1 → 1GB huge page, done
         │
         ├── Read PMD entry from PUD.addr + PMD_index×8  [memory access 3]
         │   If not Present → #PF
         │   If PS=1 → 2MB huge page, done
         │
         └── Read PTE entry from PMD.addr + PTE_index×8  [memory access 4]
             If not Present → #PF
             Extract PFN → load TLB entry → retry original access
```

### Page Fault Handling (Linux)

```
#PF exception → do_page_fault() → handle_mm_fault()
    │
    ├── Not in any VMA? → SIGSEGV
    ├── Permission violation (write to r/o)? → SIGSEGV (or CoW)
    │
    ├── Anonymous page (heap/stack)
    │   └── alloc_page() → zero page → map PTE → return
    │
    ├── File-backed page (mmap'd file)
    │   └── read page from disk → map PTE → return
    │
    ├── Swap page
    │   └── read from swap device → map PTE → return
    │
    └── Copy-on-Write (fork)
        └── Copy parent's page → new PTE → mark writable → return
```

---

## 9. NUMA, Physical Memory Zones

### NUMA (Non-Uniform Memory Access)

In multi-socket systems, each CPU socket has local RAM. Accessing local RAM is fast (~70 ns), remote RAM is slow (~140 ns, crosses QPI/UPI interconnect).

Linux models this as NUMA nodes. Each node has **zones**:

```
ZONE_DMA    (0 – 16 MB)     Legacy ISA DMA, requires 24-bit bus address
ZONE_DMA32  (0 – 4 GB)      32-bit DMA capable devices
ZONE_NORMAL (> 4 GB)        Normal allocations, directly mapped
ZONE_HIGHMEM                 (32-bit only, not relevant for x86-64)
ZONE_MOVABLE                 Movable pages (for memory hotplug, balloon)
ZONE_DEVICE                  Device memory (PMEM, GPU HBM via DAX)
```

```bash
# NUMA topology
numactl --hardware
numastat
cat /proc/buddyinfo  # free pages per zone per order

# Bind process to NUMA node 0
numactl --membind=0 --cpunodebind=0 ./my_program

# NUMA memory stats per process
cat /proc/self/numa_maps | head -5
# 7f3abc000000 default file=/lib/x86_64-linux-gnu/libc.so.6 mapped=30 ...
```

### The Buddy Allocator and Physical Pages

The Linux kernel's physical page allocator is the **buddy system**. It manages pages in power-of-2 blocks (orders 0–10, i.e., 4 KB – 4 MB).

```bash
# Current buddy allocator state
cat /proc/buddyinfo
# Node 0, zone   Normal  100 120 80 40 20 10 5 3 1 0 0
# ^ counts of free blocks of each order (2^0 to 2^10 pages)

# Memory fragmentation stats
cat /sys/kernel/debug/extfrag/extfrag_index 2>/dev/null || true
```

---

## 10. DMA, IOMMU, and Bus Mastering

### DMA Basics

When a device does DMA:
1. Kernel allocates a buffer in physical memory
2. Kernel tells the device the **bus address** of that buffer
3. Device reads/writes directly to physical memory
4. Kernel reads the result

### DMA API in Linux Kernel

```c
/* Allocate coherent DMA memory (CPU and device see same data, no cache flush needed) */
dma_addr_t dma_handle;
void *cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
// cpu_addr  = virtual address (kernel uses this)
// dma_handle = bus address (device uses this)
// Without IOMMU: dma_handle ≈ virt_to_phys(cpu_addr)
// With IOMMU: dma_handle is the IOMMU-mapped address

/* Streaming DMA (for existing buffers) */
dma_addr_t dma_handle = dma_map_single(dev, cpu_addr, size, DMA_TO_DEVICE);
// Pins the pages, flushes CPU cache, sets up IOMMU mapping
// Device can now DMA from dma_handle

/* After DMA completes */
dma_unmap_single(dev, dma_handle, size, DMA_TO_DEVICE);
// Tears down IOMMU mapping, invalidates CPU cache if needed
```

### IOMMU Security Model

```
Without IOMMU:
  Compromised NIC firmware → DMA anywhere in physical memory → kernel pwned

With IOMMU + device isolation:
  NIC firmware → bus address → IOMMU check against device's I/O page table
  Only pre-authorized physical pages accessible → sandbox escape prevented

IOMMU groups = set of devices that share an IOMMU context (must be isolated together)
Used by VFIO for PCI passthrough to VMs
```

```bash
# Check IOMMU groups (important for GPU passthrough)
for g in /sys/kernel/iommu_groups/*; do
    echo "IOMMU Group ${g##*/}:"
    for d in $g/devices/*; do
        echo -e "\t$(lspci -nns ${d##*/})"
    done
done

# VFIO device passthrough requires IOMMU
lsmod | grep vfio
ls /dev/vfio/
```

---

## 11. Linux Kernel Memory APIs

### Key Kernel Functions (for kernel module / driver development context)

```c
/* Physical ↔ Virtual (kernel direct mapping) */
void *phys_to_virt(phys_addr_t addr);  // phys → kernel virtual
phys_addr_t virt_to_phys(void *addr);  // kernel virtual → phys
                                        // ONLY valid for kmalloc/direct-mapped pages

/* User virtual → Physical (requires page pinning) */
struct page *get_user_pages(unsigned long start, ...);
phys_addr_t page_to_phys(struct page *page);
void *page_to_virt(struct page *page);
unsigned long page_to_pfn(struct page *page);

/* I/O memory (MMIO) */
void __iomem *ioremap(phys_addr_t offset, unsigned long size);
// Maps MMIO physical address into kernel virtual space (non-cacheable)
void iounmap(void __iomem *addr);

/* DMA addresses */
dma_addr_t dma_map_single(struct device *dev, void *ptr, size_t size, ...);
void dma_unmap_single(struct device *dev, dma_addr_t addr, size_t size, ...);

/* Page allocation */
struct page *alloc_pages(gfp_t gfp_mask, unsigned int order);
void *__get_free_pages(gfp_t gfp_mask, unsigned int order);
void *kmalloc(size_t size, gfp_t flags);        // small, physically contiguous
void *vmalloc(unsigned long size);               // large, virtually contiguous only
```

### The /proc/PID/pagemap Interface

The kernel exposes a pagemap file that lets userspace translate virtual → physical (with CAP_SYS_ADMIN in newer kernels, or readable by process owner for some fields):

```
/proc/PID/pagemap: 8 bytes per page in the process's virtual address space
Byte layout of each entry:
  Bits 54-0:  Page Frame Number (if present and not swapped)
  Bit  55:    PTE soft-dirty
  Bit  56:    Page exclusively mapped
  Bits 60-57: Zero
  Bit  61:    Page is file-page or shared-anon
  Bit  62:    Page swapped
  Bit  63:    Page present (in RAM)
```

---

## 12. C — Userspace Memory Introspection

### File: `addr_inspect.c`

```c
/**
 * addr_inspect.c
 * Demonstrates virtual→physical translation using /proc/self/pagemap
 * Shows VMA layout, huge pages, and address arithmetic.
 *
 * Build: gcc -O2 -o addr_inspect addr_inspect.c
 * Run:   sudo ./addr_inspect   (root needed for pagemap PFN read)
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <errno.h>
#include <assert.h>

#define PAGE_SIZE       4096UL
#define HUGE_PAGE_SIZE  (2 * 1024 * 1024UL)  /* 2 MB */
#define PFN_MASK        ((1ULL << 55) - 1)
#define PAGE_PRESENT    (1ULL << 63)
#define PAGE_SWAPPED    (1ULL << 62)
#define PAGE_FILE       (1ULL << 61)
#define PAGE_SOFT_DIRTY (1ULL << 55)

/* ─── Virtual address decomposition ─────────────────────────────── */
typedef struct {
    uint64_t offset;    /* bits 11-0  */
    uint64_t pte_idx;   /* bits 20-12 */
    uint64_t pmd_idx;   /* bits 29-21 */
    uint64_t pud_idx;   /* bits 38-30 */
    uint64_t pgd_idx;   /* bits 47-39 */
    int      canonical; /* bits 63-48 == sign-extension of bit 47 */
} vaddr_parts_t;

vaddr_parts_t decompose_vaddr(uint64_t vaddr) {
    vaddr_parts_t p;
    p.offset   = vaddr & 0xFFF;
    p.pte_idx  = (vaddr >> 12) & 0x1FF;
    p.pmd_idx  = (vaddr >> 21) & 0x1FF;
    p.pud_idx  = (vaddr >> 30) & 0x1FF;
    p.pgd_idx  = (vaddr >> 39) & 0x1FF;
    /* canonical check: bits 63-48 must equal bit 47 */
    uint64_t sign_bits = vaddr >> 47;
    p.canonical = (sign_bits == 0 || sign_bits == 0x1FFFF);
    return p;
}

void print_vaddr_decomp(const char *label, void *ptr) {
    uint64_t vaddr = (uint64_t)ptr;
    vaddr_parts_t p = decompose_vaddr(vaddr);

    printf("\n=== %s ===\n", label);
    printf("Virtual address : 0x%016lx\n", vaddr);
    printf("Canonical       : %s\n", p.canonical ? "YES" : "NO (FAULT!)");
    printf("PGD index       : %lu  (bits 47-39)\n", p.pgd_idx);
    printf("PUD index       : %lu  (bits 38-30)\n", p.pud_idx);
    printf("PMD index       : %lu  (bits 29-21)\n", p.pmd_idx);
    printf("PTE index       : %lu  (bits 20-12)\n", p.pte_idx);
    printf("Page offset     : 0x%03lx (bits 11-0)\n", p.offset);
}

/* ─── /proc/self/pagemap translation ────────────────────────────── */
typedef struct {
    uint64_t pfn;
    uint64_t phys_addr;
    int      present;
    int      swapped;
    int      soft_dirty;
} phys_info_t;

phys_info_t virt_to_phys_user(void *vaddr) {
    phys_info_t info = {0};
    uint64_t va = (uint64_t)vaddr;
    uint64_t page_num = va / PAGE_SIZE;
    uint64_t offset_in_page = va % PAGE_SIZE;

    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0) {
        perror("open /proc/self/pagemap");
        return info;
    }

    uint64_t entry;
    off_t offset = page_num * sizeof(uint64_t);
    if (pread(fd, &entry, sizeof(entry), offset) != sizeof(entry)) {
        perror("pread pagemap");
        close(fd);
        return info;
    }
    close(fd);

    info.present    = !!(entry & PAGE_PRESENT);
    info.swapped    = !!(entry & PAGE_SWAPPED);
    info.soft_dirty = !!(entry & PAGE_SOFT_DIRTY);

    if (info.present && !info.swapped) {
        info.pfn       = entry & PFN_MASK;
        info.phys_addr = (info.pfn * PAGE_SIZE) + offset_in_page;
    }
    return info;
}

void print_phys_info(const char *label, void *ptr) {
    phys_info_t info = virt_to_phys_user(ptr);
    printf("%-30s virt=0x%016lx  ", label, (uint64_t)ptr);
    if (info.present) {
        printf("phys=0x%016lx  pfn=%lu\n", info.phys_addr, info.pfn);
    } else if (info.swapped) {
        printf("SWAPPED\n");
    } else {
        printf("NOT PRESENT (demand paging, touch first)\n");
    }
}

/* ─── Show /proc/self/maps entries ──────────────────────────────── */
void print_vma_map(void) {
    printf("\n=== /proc/self/maps (VMA layout) ===\n");
    FILE *f = fopen("/proc/self/maps", "r");
    if (!f) { perror("fopen maps"); return; }
    char line[512];
    while (fgets(line, sizeof(line), f)) {
        printf("  %s", line);
    }
    fclose(f);
}

/* ─── Huge page demonstration ────────────────────────────────────── */
void demo_huge_pages(void) {
    printf("\n=== Huge Page Allocation ===\n");

    /* Allocate 2 MB aligned anonymous region */
    void *base = mmap(NULL, HUGE_PAGE_SIZE * 4,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED) { perror("mmap"); return; }

    /* Align to 2 MB boundary (mmap may not return 2 MB-aligned) */
    void *aligned = (void *)(((uint64_t)base + HUGE_PAGE_SIZE - 1)
                              & ~(HUGE_PAGE_SIZE - 1));

    /* Advise kernel to use huge pages for this region */
    if (madvise(aligned, HUGE_PAGE_SIZE, MADV_HUGEPAGE) < 0) {
        perror("madvise MADV_HUGEPAGE (non-fatal, THP may be disabled)");
    }

    /* Touch the pages to trigger allocation */
    memset(aligned, 0xAB, HUGE_PAGE_SIZE);

    printf("2 MB mmap base    : 0x%016lx\n", (uint64_t)aligned);

    /* Check if huge page was actually allocated */
    char smaps_path[64];
    snprintf(smaps_path, sizeof(smaps_path), "/proc/self/smaps");
    FILE *f = fopen(smaps_path, "r");
    char line[512];
    uint64_t thp_size = 0;
    if (f) {
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "AnonHugePages:", 14) == 0) {
                thp_size += strtoul(line + 14, NULL, 10);
            }
        }
        fclose(f);
    }
    printf("AnonHugePages used: %lu KB\n", thp_size);
    printf("Huge page backing : %s\n",
           thp_size >= 2048 ? "YES (2 MB THP allocated)" : "NO (4 KB pages used)");

    /* Show physical address of huge page (contiguous 2 MB frame) */
    print_phys_info("  huge page start", aligned);
    print_phys_info("  huge page +1 MB", (char*)aligned + 1024*1024);

    munmap(base, HUGE_PAGE_SIZE * 4);
}

/* ─── Memory type demonstration ─────────────────────────────────── */
void demo_memory_types(void) {
    printf("\n=== Memory Region Physical Addresses ===\n");

    /* Stack variable */
    volatile int stack_var = 42;
    print_phys_info("stack variable", (void*)&stack_var);

    /* Global (BSS) */
    static int bss_var;
    bss_var = 1;  /* touch to allocate */
    print_phys_info("BSS (static) var", (void*)&bss_var);

    /* Heap (malloc) */
    void *heap = malloc(PAGE_SIZE);
    memset(heap, 1, PAGE_SIZE);  /* touch to allocate */
    print_phys_info("heap (malloc)", heap);
    free(heap);

    /* Anonymous mmap */
    void *anon = mmap(NULL, PAGE_SIZE, PROT_READ|PROT_WRITE,
                      MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    if (anon != MAP_FAILED) {
        *(int*)anon = 1;  /* touch */
        print_phys_info("anonymous mmap", anon);
        munmap(anon, PAGE_SIZE);
    }

    /* Code (text segment) */
    print_phys_info("code (main fn)", (void*)main);
}

/* ─── mlock and physical memory pinning ─────────────────────────── */
void demo_mlock(void) {
    printf("\n=== mlock: Pin Pages in Physical Memory ===\n");
    size_t sz = 4 * PAGE_SIZE;
    void *buf = malloc(sz);
    memset(buf, 0, sz);

    if (mlock(buf, sz) == 0) {
        printf("mlock() succeeded: pages pinned in RAM, won't be swapped\n");
        print_phys_info("  mlocked page[0]", buf);
        print_phys_info("  mlocked page[1]", (char*)buf + PAGE_SIZE);
        munlock(buf, sz);
    } else {
        printf("mlock() failed (may need CAP_IPC_LOCK or raise RLIMIT_MEMLOCK): %s\n",
               strerror(errno));
    }
    free(buf);
}

int main(void) {
    printf("PAGE_SIZE       = %lu bytes\n", PAGE_SIZE);
    printf("HUGE_PAGE_SIZE  = %lu bytes (2 MB)\n", HUGE_PAGE_SIZE);
    printf("PID             = %d\n", getpid());
    printf("UID             = %d\n", getuid());

    int stack_local = 99;
    print_vaddr_decomp("Stack variable", &stack_local);
    print_vaddr_decomp("main() function", (void*)main);

    demo_memory_types();
    demo_mlock();
    demo_huge_pages();

    if (getuid() == 0) {
        print_vma_map();
    } else {
        printf("\n[Run as root to see full VMA map and physical addresses]\n");
        print_vma_map();
    }
    return 0;
}
```

**Build and run:**

```bash
gcc -O2 -Wall -o addr_inspect addr_inspect.c
sudo ./addr_inspect 2>&1 | tee addr_inspect.log

# Expected output (abbreviated):
# PAGE_SIZE       = 4096 bytes
# HUGE_PAGE_SIZE  = 2097152 bytes (2 MB)
# PID             = 12345
#
# === Stack variable ===
# Virtual address : 0x00007ffd1234ab40
# Canonical       : YES
# PGD index       : 255  (bits 47-39)
# ...
#
# === Memory Region Physical Addresses ===
# stack variable                 virt=0x00007ffd1234ab40  phys=0x0000000123456000  pfn=...
```

### File: `mmio_demo.c` — MMIO Access Pattern (educational)

```c
/**
 * mmio_demo.c
 * Demonstrates accessing MMIO regions (like a PCI device BAR)
 * Uses /dev/mem to map a physical MMIO region.
 * 
 * IMPORTANT: This requires root and iomem=relaxed kernel param
 * Real drivers use ioremap() in kernel space.
 *
 * Build: gcc -O2 -o mmio_demo mmio_demo.c
 * Run:   sudo ./mmio_demo <physical_address_hex> <size>
 *        e.g.: sudo ./mmio_demo 0xfee00000 0x1000   (Local APIC)
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <phys_addr_hex> <size_hex>\n", argv[0]);
        fprintf(stderr, "Requires: root, /dev/mem access\n");
        fprintf(stderr, "Kernel param: iomem=relaxed (or CONFIG_STRICT_DEVMEM=n)\n");
        return 1;
    }

    uint64_t phys_addr = strtoull(argv[1], NULL, 0);
    uint64_t size      = strtoull(argv[2], NULL, 0);
    uint64_t page_mask = ~(getpagesize() - 1ULL);
    uint64_t aligned_addr = phys_addr & page_mask;
    uint64_t offset_in_page = phys_addr - aligned_addr;
    uint64_t map_size = size + offset_in_page;

    printf("Physical address : 0x%016lx\n", phys_addr);
    printf("Size             : 0x%lx bytes\n", size);
    printf("Aligned addr     : 0x%016lx\n", aligned_addr);
    printf("Offset in page   : 0x%lx\n", offset_in_page);

    int fd = open("/dev/mem", O_RDONLY | O_SYNC);
    if (fd < 0) {
        perror("open /dev/mem (need root + iomem=relaxed)");
        return 1;
    }

    /* Map physical memory into our virtual address space */
    void *virt = mmap(NULL, map_size, PROT_READ,
                      MAP_SHARED, fd, aligned_addr);
    if (virt == MAP_FAILED) {
        perror("mmap /dev/mem");
        close(fd);
        return 1;
    }

    volatile uint32_t *regs = (volatile uint32_t *)((char*)virt + offset_in_page);

    printf("Virtual address  : 0x%016lx\n", (uint64_t)virt + offset_in_page);
    printf("\nFirst 64 bytes (as 32-bit words):\n");
    for (int i = 0; i < 16 && (uint64_t)(i*4) < size; i++) {
        printf("  [0x%03x] = 0x%08x\n", i*4, regs[i]);
    }

    /* KEY POINT: regs[0] is a VIRTUAL address in OUR process.
     * The MMU maps it to physical address phys_addr + 0.
     * This is how MMIO works: device registers appear at fixed
     * physical addresses, kernel maps them with ioremap() or
     * we can use /dev/mem from userspace. */

    printf("\nAddress relationship:\n");
    printf("  Our virtual ptr  : 0x%016lx\n", (uint64_t)regs);
    printf("  Maps to physical : 0x%016lx\n", phys_addr);
    printf("  Offset           : +0x%lx bytes\n",
           (uint64_t)regs - (uint64_t)virt - offset_in_page + offset_in_page);

    munmap(virt, map_size);
    close(fd);
    return 0;
}
```

---

## 13. Rust — Safe and Unsafe Memory Introspection

### File: `src/main.rs` — Address Space Inspector

```rust
//! addr_space/src/main.rs
//! Rust address space and virtual→physical translation tool.
//! 
//! Cargo.toml:
//! [package]
//! name = "addr_space"
//! version = "0.1.0"
//! edition = "2021"
//!
//! [dependencies]
//! libc = "0.2"
//!
//! Build: cargo build --release
//! Run:   sudo ./target/release/addr_space

use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::os::unix::io::AsRawFd;
use libc::{mmap, munmap, mlock, munlock, madvise};
use libc::{MAP_PRIVATE, MAP_ANONYMOUS, MAP_FAILED, PROT_READ, PROT_WRITE, MADV_HUGEPAGE};

const PAGE_SIZE: usize = 4096;
const HUGE_PAGE_SIZE: usize = 2 * 1024 * 1024; // 2 MB
const PFN_MASK: u64 = (1u64 << 55) - 1;
const PAGE_PRESENT: u64 = 1u64 << 63;
const PAGE_SWAPPED: u64 = 1u64 << 62;

// ─── Virtual address decomposition ──────────────────────────────────────────

#[derive(Debug)]
struct VAddrParts {
    offset:    u64,   // bits 11-0
    pte_idx:   u64,   // bits 20-12
    pmd_idx:   u64,   // bits 29-21
    pud_idx:   u64,   // bits 38-30
    pgd_idx:   u64,   // bits 47-39
    sign_ext:  u64,   // bits 63-48
    canonical: bool,
}

impl VAddrParts {
    fn from_ptr<T>(ptr: *const T) -> Self {
        let vaddr = ptr as u64;
        let bit47 = (vaddr >> 47) & 1;
        let sign_ext = vaddr >> 48;
        VAddrParts {
            offset:   vaddr & 0xFFF,
            pte_idx:  (vaddr >> 12) & 0x1FF,
            pmd_idx:  (vaddr >> 21) & 0x1FF,
            pud_idx:  (vaddr >> 30) & 0x1FF,
            pgd_idx:  (vaddr >> 39) & 0x1FF,
            sign_ext,
            // Canonical: all high bits must equal bit 47
            canonical: if bit47 == 0 { sign_ext == 0 } else { sign_ext == 0xFFFF },
        }
    }

    fn print(&self, label: &str, ptr: u64) {
        println!("\n=== {} ===", label);
        println!("Virtual address : 0x{:016x}", ptr);
        println!("Canonical       : {}", if self.canonical { "YES" } else { "NO (would #GP fault)" });
        println!("PGD index       : {} (bits 47-39)", self.pgd_idx);
        println!("PUD index       : {} (bits 38-30)", self.pud_idx);
        println!("PMD index       : {} (bits 29-21)", self.pmd_idx);
        println!("PTE index       : {} (bits 20-12)", self.pte_idx);
        println!("Page offset     : 0x{:03x} (bits 11-0)", self.offset);
    }
}

// ─── Physical address translation via /proc/self/pagemap ────────────────────

#[derive(Debug, Default)]
struct PhysInfo {
    pfn:        u64,
    phys_addr:  u64,
    present:    bool,
    swapped:    bool,
    soft_dirty: bool,
}

fn virt_to_phys(vaddr: u64) -> io::Result<PhysInfo> {
    let page_num = vaddr / PAGE_SIZE as u64;
    let offset_in_page = vaddr % PAGE_SIZE as u64;

    let mut f = File::open("/proc/self/pagemap")?;
    f.seek(SeekFrom::Start(page_num * 8))?;

    let mut buf = [0u8; 8];
    f.read_exact(&mut buf)?;
    let entry = u64::from_le_bytes(buf);

    let present    = (entry & PAGE_PRESENT) != 0;
    let swapped    = (entry & PAGE_SWAPPED) != 0;
    let soft_dirty = (entry & (1u64 << 55)) != 0;

    let (pfn, phys_addr) = if present && !swapped {
        let pfn = entry & PFN_MASK;
        (pfn, pfn * PAGE_SIZE as u64 + offset_in_page)
    } else {
        (0, 0)
    };

    Ok(PhysInfo { pfn, phys_addr, present, swapped, soft_dirty })
}

fn print_phys<T>(label: &str, ptr: *const T) {
    let vaddr = ptr as u64;
    match virt_to_phys(vaddr) {
        Ok(info) if info.present =>
            println!("{:<35} virt=0x{:016x}  phys=0x{:016x}  pfn={}",
                     label, vaddr, info.phys_addr, info.pfn),
        Ok(info) if info.swapped =>
            println!("{:<35} virt=0x{:016x}  SWAPPED", label, vaddr),
        Ok(_) =>
            println!("{:<35} virt=0x{:016x}  NOT PRESENT (touch first)", label, vaddr),
        Err(e) =>
            println!("{:<35} virt=0x{:016x}  ERROR: {}", label, vaddr, e),
    }
}

// ─── VMA map reader ──────────────────────────────────────────────────────────

fn print_vma_map() {
    println!("\n=== /proc/self/maps ===");
    match std::fs::read_to_string("/proc/self/maps") {
        Ok(s) => print!("{}", s),
        Err(e) => println!("Error reading maps: {}", e),
    }
}

// ─── Heap allocation and tracking ───────────────────────────────────────────

fn demo_heap() {
    println!("\n=== Heap (Box<T>) Allocation ===");

    // Rust's Box<T> uses the global allocator (jemalloc or system malloc)
    let heap_val: Box<u64> = Box::new(0xDEAD_BEEF_CAFE_0000u64);
    let ptr: *const u64 = &*heap_val;
    print_phys("Box<u64> on heap", ptr);

    // Vec<u8> - heap buffer
    let mut buf: Vec<u8> = vec![0u8; PAGE_SIZE * 4];
    // Touch all pages to force physical allocation (demand paging)
    for chunk in buf.chunks_mut(PAGE_SIZE) {
        chunk[0] = 0xFF;
    }
    print_phys("Vec<u8>[0]  (heap)", buf.as_ptr());
    print_phys("Vec<u8>[4096] (heap+page)", unsafe { buf.as_ptr().add(PAGE_SIZE) });
}

// ─── Stack vs heap distinction ───────────────────────────────────────────────

fn demo_stack() {
    println!("\n=== Stack vs Heap ===");

    let stack_val: u64 = 0xCAFE_BABE;
    let heap_val: Box<u64> = Box::new(0xDEAD_C0DE);

    let stack_ptr: *const u64 = &stack_val;
    let heap_ptr: *const u64 = &*heap_val;

    print_phys("stack variable", stack_ptr);
    print_phys("heap (Box) variable", heap_ptr);

    println!("Stack addr: 0x{:016x}", stack_ptr as u64);
    println!("Heap addr:  0x{:016x}", heap_ptr as u64);
    println!("Stack is higher: {}", stack_ptr as u64 > heap_ptr as u64);
}

// ─── Anonymous mmap (unsafe FFI) ────────────────────────────────────────────

fn demo_mmap() {
    println!("\n=== Anonymous mmap ===");

    unsafe {
        // Allocate 2 anonymous pages
        let ptr = mmap(
            std::ptr::null_mut(),
            PAGE_SIZE * 2,
            PROT_READ | PROT_WRITE,
            MAP_PRIVATE | MAP_ANONYMOUS,
            -1,
            0,
        );

        if ptr == MAP_FAILED {
            println!("mmap failed");
            return;
        }

        // Touch pages to force physical allocation
        let slice = std::slice::from_raw_parts_mut(ptr as *mut u8, PAGE_SIZE * 2);
        slice[0] = 0xAB;
        slice[PAGE_SIZE] = 0xCD;

        print_phys("mmap page 0", slice.as_ptr());
        print_phys("mmap page 1", unsafe { slice.as_ptr().add(PAGE_SIZE) });

        // Note: the two pages MAY be physically non-contiguous even though
        // they appear contiguous in virtual address space.
        let phys0 = virt_to_phys(slice.as_ptr() as u64).unwrap_or_default();
        let phys1 = virt_to_phys(unsafe { slice.as_ptr().add(PAGE_SIZE) } as u64)
            .unwrap_or_default();

        println!("Pages physically contiguous: {}",
                 phys0.present && phys1.present &&
                 phys1.pfn == phys0.pfn + 1);

        munmap(ptr, PAGE_SIZE * 2);
    }
}

// ─── mlock: pin pages in physical memory ────────────────────────────────────

fn demo_mlock() {
    println!("\n=== mlock: Pin Pages in Physical RAM ===");

    let mut buf = vec![0u8; PAGE_SIZE * 4];
    buf.iter_mut().enumerate().for_each(|(i, b)| *b = (i % 256) as u8);

    unsafe {
        let ret = mlock(buf.as_ptr() as *const libc::c_void, buf.len());
        if ret == 0 {
            println!("mlock() OK: {} pages pinned, won't be swapped", buf.len() / PAGE_SIZE);
            print_phys("mlocked page[0]", buf.as_ptr());
            print_phys("mlocked page[3]", unsafe { buf.as_ptr().add(PAGE_SIZE * 3) });
            munlock(buf.as_ptr() as *const libc::c_void, buf.len());
        } else {
            println!("mlock() failed: {} (need CAP_IPC_LOCK or higher RLIMIT_MEMLOCK)",
                     io::Error::last_os_error());
        }
    }
}

// ─── Huge pages via madvise ──────────────────────────────────────────────────

fn demo_huge_pages() {
    println!("\n=== Transparent Huge Pages (THP) ===");

    unsafe {
        // Allocate 4 MB (over-allocate to ensure 2 MB alignment)
        let alloc_size = HUGE_PAGE_SIZE * 3;
        let raw = mmap(
            std::ptr::null_mut(),
            alloc_size,
            PROT_READ | PROT_WRITE,
            MAP_PRIVATE | MAP_ANONYMOUS,
            -1,
            0,
        );
        if raw == MAP_FAILED {
            println!("mmap failed for huge page demo");
            return;
        }

        // Align to 2 MB
        let raw_u64 = raw as u64;
        let aligned_u64 = (raw_u64 + HUGE_PAGE_SIZE as u64 - 1) & !(HUGE_PAGE_SIZE as u64 - 1);
        let aligned = aligned_u64 as *mut u8;

        // Request THP
        let ret = madvise(aligned as *mut libc::c_void, HUGE_PAGE_SIZE, MADV_HUGEPAGE);
        if ret != 0 {
            println!("madvise MADV_HUGEPAGE: {} (THP may be disabled)", io::Error::last_os_error());
        }

        // Touch the entire huge page
        let slice = std::slice::from_raw_parts_mut(aligned, HUGE_PAGE_SIZE);
        for chunk in slice.chunks_mut(PAGE_SIZE) {
            chunk[0] = 0xFF;
        }

        println!("Huge page base virt: 0x{:016x}", aligned as u64);
        print_phys("  offset=0",       aligned);
        print_phys("  offset=4KB",     aligned.add(PAGE_SIZE));
        print_phys("  offset=1MB",     aligned.add(HUGE_PAGE_SIZE / 2));

        // With real huge pages, the physical addresses are:
        // phys(offset+N*4KB) == phys(offset) + N*4KB
        let p0 = virt_to_phys(aligned as u64).unwrap_or_default();
        let p1 = virt_to_phys(aligned.add(PAGE_SIZE) as u64).unwrap_or_default();
        if p0.present && p1.present {
            println!("Physical pages contiguous: {}  (pfn[0]={}, pfn[1]={})",
                     p1.pfn == p0.pfn + 1, p0.pfn, p1.pfn);
        }

        munmap(raw, alloc_size);
    }
}

// ─── Address space segments analysis ────────────────────────────────────────

fn analyze_address_space() {
    println!("\n=== Address Space Segment Analysis ===");

    // Determine user/kernel boundary
    let user_max: u64 = 0x0000_7FFF_FFFF_FFFF;
    let kernel_min: u64 = 0xFFFF_8000_0000_0000;

    let stack_local: u64 = 42;
    let heap_val: Box<u64> = Box::new(0);
    let fn_ptr = main as u64;

    let classify = |addr: u64, label: &str| {
        let region = if addr <= user_max {
            "USER SPACE"
        } else if addr >= kernel_min {
            "KERNEL SPACE"
        } else {
            "NON-CANONICAL (invalid)"
        };
        println!("  {:30} 0x{:016x}  → {}", label, addr, region);
    };

    classify(&stack_local as *const u64 as u64, "stack variable");
    classify(&*heap_val as *const u64 as u64, "heap (Box)");
    classify(fn_ptr, "main() code");
    classify(0xFFFF_FFFF_8100_0000u64, "kernel text (typical)");
    classify(0xFFFF_8800_0000_0000u64, "direct mapping");
}

fn main() {
    println!("Rust Address Space Inspector");
    println!("============================");
    println!("PID: {}", std::process::id());
    println!("PAGE_SIZE: {} bytes", PAGE_SIZE);

    let local: u64 = 0xDEAD;
    let parts = VAddrParts::from_ptr(&local as *const u64);
    parts.print("Stack variable", &local as *const u64 as u64);

    let parts_fn = VAddrParts::from_ptr(main as *const ());
    parts_fn.print("main() function", main as u64);

    demo_stack();
    demo_heap();
    demo_mmap();
    demo_mlock();
    demo_huge_pages();
    analyze_address_space();

    if std::env::var("SHOW_MAPS").is_ok() {
        print_vma_map();
    } else {
        println!("\n[Set SHOW_MAPS=1 to print full VMA map]");
    }
}

// ─── Tests ──────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vaddr_decomposition_user_stack() {
        // Typical user stack address on x86-64
        let addr: u64 = 0x0000_7fff_dead_beef;
        let parts = VAddrParts::from_ptr(addr as *const u8);
        assert!(parts.canonical);
        assert_eq!(parts.offset, 0xeef);
        assert_eq!(parts.pte_idx, (addr >> 12) & 0x1FF);
        assert_eq!(parts.pgd_idx, (addr >> 39) & 0x1FF);
    }

    #[test]
    fn test_vaddr_decomposition_kernel() {
        // Kernel direct mapping address
        let addr: u64 = 0xffff_8000_0000_0000u64;
        let parts = VAddrParts::from_ptr(addr as *const u8);
        assert!(parts.canonical);
    }

    #[test]
    fn test_non_canonical() {
        // Non-canonical address (hole between user and kernel)
        let addr: u64 = 0x8000_0000_0000u64;  // bit 47 = 0, but high bits ≠ 0
        let parts = VAddrParts::from_ptr(addr as *const u8);
        assert!(!parts.canonical);
    }

    #[test]
    fn test_pfn_from_physical() {
        let phys: u64 = 0x0000_0001_2345_6000u64;
        let pfn = phys / PAGE_SIZE as u64;
        let reconstructed = pfn * PAGE_SIZE as u64;
        assert_eq!(reconstructed, phys);
        assert_eq!(phys & 0xFFF, 0);  // page-aligned
    }

    #[test]
    fn test_stack_is_higher_than_heap() {
        let stack: i64 = 0;
        let heap: Box<i64> = Box::new(0);
        // On Linux x86-64, stack grows down from high addresses,
        // heap is lower in address space.
        assert!(&stack as *const i64 as u64 > &*heap as *const i64 as u64);
    }

    #[test]
    fn test_pagemap_read_self() {
        // Allocate and touch a page, then read its pagemap entry
        let mut v = vec![0u8; PAGE_SIZE];
        v[0] = 1;  // force physical allocation
        let ptr = v.as_ptr();
        let result = virt_to_phys(ptr as u64);
        assert!(result.is_ok());
        let info = result.unwrap();
        // After touching, page should be present
        assert!(info.present, "page should be present after touching");
        assert!(!info.swapped);
    }
}
```

**Run:**

```bash
cd addr_space
cargo build --release
sudo ./target/release/addr_space
sudo SHOW_MAPS=1 ./target/release/addr_space

# Run tests (some require root for pagemap PFN access)
cargo test -- --nocapture

# Benchmark memory allocation
cargo bench  # add [[bench]] section to Cargo.toml
```

---

## 14. Go — Runtime Heap, Stack, and Address Visibility

Go has a managed runtime that handles stack growth, heap allocation (via garbage collector), and goroutine scheduling. Understanding how Go maps to the underlying virtual/physical address model is critical for performance and debugging.

### File: `addr_space.go`

```go
// addr_space.go
// Go address space inspector: virtual addresses, physical translation,
// goroutine stack behavior, heap escape analysis.
//
// Build:  go build -o addr_space addr_space.go
// Run:    sudo ./addr_space
// Race:   go run -race addr_space.go
//
// go:build linux

package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"runtime"
	"runtime/debug"
	"sync"
	"syscall"
	"unsafe"
)

const (
	PageSize      = 4096
	HugePageSize  = 2 * 1024 * 1024 // 2 MB
	PFNMask       = (uint64(1) << 55) - 1
	PagePresent   = uint64(1) << 63
	PageSwapped   = uint64(1) << 62
)

// ─── Virtual address decomposition ──────────────────────────────────────────

type VAddrParts struct {
	Offset    uint64
	PTEIdx    uint64
	PMDIdx    uint64
	PUDIdx    uint64
	PGDIdx    uint64
	Canonical bool
}

func decomposeVAddr(addr uintptr) VAddrParts {
	a := uint64(addr)
	bit47 := (a >> 47) & 1
	signExt := a >> 48
	canonical := (bit47 == 0 && signExt == 0) || (bit47 == 1 && signExt == 0xFFFF)
	return VAddrParts{
		Offset:    a & 0xFFF,
		PTEIdx:    (a >> 12) & 0x1FF,
		PMDIdx:    (a >> 21) & 0x1FF,
		PUDIdx:    (a >> 30) & 0x1FF,
		PGDIdx:    (a >> 39) & 0x1FF,
		Canonical: canonical,
	}
}

func printVAddr(label string, addr uintptr) {
	p := decomposeVAddr(addr)
	fmt.Printf("\n=== %s ===\n", label)
	fmt.Printf("Virtual address : 0x%016x\n", addr)
	fmt.Printf("Canonical       : %v\n", p.Canonical)
	fmt.Printf("PGD index       : %d (bits 47-39)\n", p.PGDIdx)
	fmt.Printf("PUD index       : %d (bits 38-30)\n", p.PUDIdx)
	fmt.Printf("PMD index       : %d (bits 29-21)\n", p.PMDIdx)
	fmt.Printf("PTE index       : %d (bits 20-12)\n", p.PTEIdx)
	fmt.Printf("Page offset     : 0x%03x (bits 11-0)\n", p.Offset)
}

// ─── Physical address via /proc/self/pagemap ─────────────────────────────────

type PhysInfo struct {
	PFN       uint64
	PhysAddr  uint64
	Present   bool
	Swapped   bool
	SoftDirty bool
}

func virtToPhys(vaddr uintptr) (PhysInfo, error) {
	f, err := os.Open("/proc/self/pagemap")
	if err != nil {
		return PhysInfo{}, err
	}
	defer f.Close()

	pageNum := uint64(vaddr) / PageSize
	offsetInPage := uint64(vaddr) % PageSize

	_, err = f.Seek(int64(pageNum*8), 0)
	if err != nil {
		return PhysInfo{}, err
	}

	var entry uint64
	if err := binary.Read(f, binary.LittleEndian, &entry); err != nil {
		return PhysInfo{}, err
	}

	info := PhysInfo{
		Present:   (entry & PagePresent) != 0,
		Swapped:   (entry & PageSwapped) != 0,
		SoftDirty: (entry & (1 << 55)) != 0,
	}
	if info.Present && !info.Swapped {
		info.PFN = entry & PFNMask
		info.PhysAddr = info.PFN*PageSize + offsetInPage
	}
	return info, nil
}

func printPhys(label string, ptr unsafe.Pointer) {
	addr := uintptr(ptr)
	info, err := virtToPhys(addr)
	if err != nil {
		fmt.Printf("%-35s virt=0x%016x  ERROR: %v\n", label, addr, err)
		return
	}
	if info.Present {
		fmt.Printf("%-35s virt=0x%016x  phys=0x%016x  pfn=%d\n",
			label, addr, info.PhysAddr, info.PFN)
	} else if info.Swapped {
		fmt.Printf("%-35s virt=0x%016x  SWAPPED\n", label, addr)
	} else {
		fmt.Printf("%-35s virt=0x%016x  NOT PRESENT\n", label, addr)
	}
}

// ─── Go-specific: goroutine stacks ──────────────────────────────────────────
//
// IMPORTANT: Go goroutine stacks are:
// 1. Allocated on the HEAP (not the OS stack)
// 2. Start small (2-4 KB) and grow via stack copying
// 3. Can move in virtual memory when they grow (pointers within stack are updated)
// 4. The main goroutine uses the OS thread stack initially

func demoGoroutineStacks() {
	fmt.Println("\n=== Goroutine Stack Behavior ===")

	var wg sync.WaitGroup
	addrs := make([]uintptr, 5)

	for i := 0; i < 5; i++ {
		wg.Add(1)
		i := i
		go func() {
			defer wg.Done()
			// local variable on this goroutine's stack
			var local int = i * 100
			addr := uintptr(unsafe.Pointer(&local))
			addrs[i] = addr
			fmt.Printf("  goroutine[%d] stack var addr: 0x%016x\n", i, addr)
			// These addresses are in the Go runtime's heap, not
			// the OS thread's stack region (0x7fff...) typically
		}()
	}
	wg.Wait()

	// Show that goroutine stacks may have different addresses
	fmt.Println("\n  Stack addresses (all in Go runtime heap region):")
	for i, addr := range addrs {
		fmt.Printf("    goroutine[%d]: 0x%016x\n", i, addr)
	}

	// Show main goroutine stack location
	var mainLocal int = 42
	fmt.Printf("\n  Main goroutine stack var: 0x%016x\n",
		uintptr(unsafe.Pointer(&mainLocal)))
}

// ─── Go-specific: escape analysis ───────────────────────────────────────────
//
// Build with: go build -gcflags="-m -m" addr_space.go
// to see escape analysis decisions.

//go:noinline
func allocOnStack() *int {
	// This ESCAPES to heap because we return a pointer to it.
	// The compiler detects this and allocates on heap instead.
	x := 42
	return &x // x escapes to heap
}

//go:noinline
func noEscape() int {
	// This stays on stack — value return, no pointer escape
	x := 42
	return x
}

//go:noinline
func largeStackAlloc() {
	// Large arrays: Go may allocate on heap if they escape,
	// or keep on stack if they don't.
	arr := [8192]byte{} // 8 KB — stays on stack if no escape
	arr[0] = 1
	_ = arr
}

func demoEscapeAnalysis() {
	fmt.Println("\n=== Escape Analysis Demo ===")
	fmt.Println("Build with 'go build -gcflags=\"-m\"' to see decisions")

	ptr := allocOnStack()
	val := noEscape()

	ptrAddr := uintptr(unsafe.Pointer(ptr))
	var valAddr uintptr
	// We can't take address of non-addressable int, use a local copy
	valCopy := val
	valAddr = uintptr(unsafe.Pointer(&valCopy))

	fmt.Printf("  allocOnStack() result : 0x%016x (heap — pointer escaped)\n", ptrAddr)
	fmt.Printf("  noEscape() copy       : 0x%016x (stack — value, no escape)\n", valAddr)

	// Physical check
	printPhys("  heap-escaped ptr", unsafe.Pointer(ptr))
	printPhys("  stack value copy", unsafe.Pointer(&valCopy))
}

// ─── Go runtime heap regions ────────────────────────────────────────────────

func demoHeapRegions() {
	fmt.Println("\n=== Go Runtime Heap Layout ===")

	// Go's runtime manages a large virtual memory reservation upfront
	// (on 64-bit: up to 512 GB virtual address space for the heap)
	// Physical pages are committed on demand.

	stats := runtime.MemStats{}
	runtime.ReadMemStats(&stats)

	fmt.Printf("  HeapSys    (virtual reserved): %d MB\n", stats.HeapSys/1024/1024)
	fmt.Printf("  HeapAlloc  (live objects)     : %d KB\n", stats.HeapAlloc/1024)
	fmt.Printf("  HeapInuse  (spans in use)     : %d MB\n", stats.HeapInuse/1024/1024)
	fmt.Printf("  HeapReleased (OS reclaimed)   : %d MB\n", stats.HeapReleased/1024/1024)
	fmt.Printf("  StackSys   (OS stack)         : %d KB\n", stats.StackSys/1024)
	fmt.Printf("  StackInuse (goroutine stacks) : %d KB\n", stats.StackInuse/1024)

	// Allocate many objects and observe heap growth
	var objs []*[PageSize]byte
	for i := 0; i < 100; i++ {
		obj := new([PageSize]byte)
		obj[0] = byte(i)
		objs = append(objs, obj)
	}

	runtime.ReadMemStats(&stats)
	fmt.Printf("\n  After 100 × 4KB allocations:\n")
	fmt.Printf("  HeapAlloc: %d KB\n", stats.HeapAlloc/1024)

	// Show that objects are in the heap region (low virtual addresses for Go heap)
	firstAddr := uintptr(unsafe.Pointer(objs[0]))
	lastAddr := uintptr(unsafe.Pointer(objs[len(objs)-1]))
	fmt.Printf("  First obj addr: 0x%016x\n", firstAddr)
	fmt.Printf("  Last  obj addr: 0x%016x\n", lastAddr)
	printPhys("  First 4KB obj", unsafe.Pointer(objs[0]))

	runtime.GC()
	runtime.KeepAlive(objs)
}

// ─── mmap via syscall ────────────────────────────────────────────────────────

func demoSyscallMmap() {
	fmt.Println("\n=== Anonymous mmap via syscall ===")

	// Go's syscall package wraps the mmap(2) syscall directly
	addr, _, errno := syscall.Syscall6(
		syscall.SYS_MMAP,
		0,                                     // let kernel choose address
		PageSize*4,                            // length
		syscall.PROT_READ|syscall.PROT_WRITE,  // prot
		syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS, // flags
		^uintptr(0),                           // fd = -1
		0,                                     // offset
	)
	if errno != 0 {
		fmt.Printf("mmap syscall failed: %v\n", errno)
		return
	}

	// Touch pages
	ptr := (*[PageSize * 4]byte)(unsafe.Pointer(addr))
	ptr[0] = 0xAB
	ptr[PageSize] = 0xCD
	ptr[PageSize*2] = 0xEF
	ptr[PageSize*3] = 0x12

	fmt.Printf("  mmap base: 0x%016x\n", addr)
	for i := 0; i < 4; i++ {
		p := unsafe.Pointer(addr + uintptr(i)*PageSize)
		printPhys(fmt.Sprintf("  mmap page[%d]", i), p)
	}

	// Unmap
	_, _, errno = syscall.Syscall(syscall.SYS_MUNMAP, addr, PageSize*4, 0)
	if errno != 0 {
		fmt.Printf("munmap failed: %v\n", errno)
	}
}

// ─── GC and physical memory ─────────────────────────────────────────────────

func demoGCAndPhysical() {
	fmt.Println("\n=== GC and Physical Memory Release ===")

	// Allocate a large slice
	big := make([]byte, 64*1024*1024) // 64 MB
	for i := range big {
		big[i] = byte(i)
	}

	addr := uintptr(unsafe.Pointer(&big[0]))
	fmt.Printf("  64 MB slice virt addr : 0x%016x\n", addr)
	printPhys("  big slice [0]", unsafe.Pointer(&big[0]))
	printPhys("  big slice [32MB]", unsafe.Pointer(&big[32*1024*1024]))

	// Release reference
	big = nil

	// Force GC — this marks memory free but may NOT immediately release to OS
	runtime.GC()
	debug.FreeOSMemory() // Explicitly return to OS (calls madvise MADV_DONTNEED)

	var stats runtime.MemStats
	runtime.ReadMemStats(&stats)
	fmt.Printf("  HeapReleased after GC + FreeOSMemory: %d MB\n",
		stats.HeapReleased/1024/1024)
	// After FreeOSMemory(), the virtual address range may still be mapped
	// (still shows in /proc/maps) but physical pages are returned to OS.
	// Next access to those pages will trigger a fresh page fault.
}

// ─── VMA map ─────────────────────────────────────────────────────────────────

func printVMAMap() {
	fmt.Println("\n=== /proc/self/maps ===")
	data, err := os.ReadFile("/proc/self/maps")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	fmt.Print(string(data))
}

// ─── Main ────────────────────────────────────────────────────────────────────

func main() {
	fmt.Printf("Go Address Space Inspector\n")
	fmt.Printf("==========================\n")
	fmt.Printf("GOOS: %s, GOARCH: %s\n", runtime.GOOS, runtime.GOARCH)
	fmt.Printf("NumCPU: %d, NumGoroutine: %d\n", runtime.NumCPU(), runtime.NumGoroutine())
	fmt.Printf("PID: %d, UID: %d\n", os.Getpid(), os.Getuid())
	fmt.Printf("PageSize: %d\n\n", os.Getpagesize())

	// Decompose a few important addresses
	var localVar int = 42
	printVAddr("main goroutine stack var", uintptr(unsafe.Pointer(&localVar)))
	printVAddr("main() func address", uintptr(unsafe.Pointer(reflect_main())))

	demoGoroutineStacks()
	demoEscapeAnalysis()
	demoHeapRegions()
	demoSyscallMmap()
	demoGCAndPhysical()

	if os.Getenv("SHOW_MAPS") != "" {
		printVMAMap()
	}
}

// reflect_main returns a pointer to main for address display
//
//go:linkname reflect_main main.main
func reflect_main() unsafe.Pointer

func init() {
	// No-op: just ensure the unsafe import is used
	_ = unsafe.Pointer(nil)
}
```

**Note:** The `go:linkname` trick for getting `main`'s address needs a workaround. Here is the clean version:

```go
// Clean main snippet (replace reflect_main usage):
funcAddr := *(*uintptr)(unsafe.Pointer(&struct{ f func() }{main}))
printVAddr("main() func address", funcAddr)
```

**Run:**

```bash
go build -o addr_space addr_space.go
sudo ./addr_space

# See escape analysis
go build -gcflags="-m -m" addr_space.go 2>&1 | grep -E "escape|stack|heap"

# Race detector (for concurrent goroutine address access)
go run -race addr_space.go

# Profiling
go tool pprof -alloc_space <(go test -memprofile=mem.out -bench=. && cat mem.out)
```

### Go-Specific Address Space Notes

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Go Process Virtual Layout                          │
├───────────────────────────────┬─────────────────────────────────────┤
│ Region                        │ Notes                               │
├───────────────────────────────┼─────────────────────────────────────┤
│ Go runtime heap               │ Large reservation (up to 512 GB)    │
│ (arenas, spans, mcache)       │ Physical pages committed on demand  │
├───────────────────────────────┼─────────────────────────────────────┤
│ Goroutine stacks              │ Allocated FROM Go heap, not OS stack│
│                               │ Start: 2-8 KB, grow by copying      │
│                               │ Old stack freed, new stack at new VA│
├───────────────────────────────┼─────────────────────────────────────┤
│ Binary text/data              │ Same as any ELF binary              │
├───────────────────────────────┼─────────────────────────────────────┤
│ OS thread stacks              │ One per M (OS thread), 8 MB default │
│ (g0 stack)                    │ Used only for runtime/syscall code  │
├───────────────────────────────┼─────────────────────────────────────┤
│ CGo C stacks                  │ Traditional per-thread C stacks     │
└───────────────────────────────┴─────────────────────────────────────┘
```

**Critical implication**: Because goroutine stacks can move (stack copying on growth), you **must never** pass a pointer to a goroutine stack variable to C code (CGo). Go's runtime can move the stack while the C code holds the pointer, resulting in a dangling pointer. The `go vet` tool catches most such cases.

---

## 15. ASLR, KASLR, and Security Implications

### ASLR (Address Space Layout Randomization)

ASLR randomizes the base virtual addresses of key regions at process startup, making exploit development harder (prevents hardcoding addresses).

```bash
# Check ASLR status
cat /proc/sys/kernel/randomize_va_space
# 0 = disabled
# 1 = randomize stack, mmap, vdso, heap
# 2 = also randomize brk/heap (default on modern Linux)

# Disable ASLR for a specific process (for debugging)
setarch $(uname -m) -R ./my_program

# Show ASLR in action (different addresses each run)
for i in 1 2 3; do
    cat /proc/self/maps | grep "stack" | head -1
done
```

### KASLR (Kernel ASLR)

The kernel text, modules, and direct mapping are randomized at boot:

```bash
# KASLR status (check if kernel address is randomized)
sudo dmesg | grep -i kaslr
# [    0.000000] KASLR enabled

# Kernel image base (changes each boot with KASLR)
sudo cat /proc/kallsyms | grep " T _text"
# Without KASLR: ffffffff81000000 T _text
# With KASLR:    ffffffff92200000 T _text (different each boot)

# Disable KASLR (for kernel debugging) — add to kernel cmdline:
# nokaslr
```

### PIE (Position Independent Executable)

PIE enables ASLR for the executable itself (without PIE, the executable's .text is fixed):

```bash
# Check if binary is PIE
file ./my_binary
# PIE:     ELF 64-bit LSB pie executable
# non-PIE: ELF 64-bit LSB executable

# Build without PIE (fixed addresses, easier debugging but less secure)
gcc -no-pie -o non_pie_binary source.c
# Build with PIE (default on modern distros)
gcc -fPIE -pie -o pie_binary source.c

# Check runtime addresses with PIE
for i in 1 2 3; do
    ./pie_binary &
    sleep 0.1
    cat /proc/$!/maps | grep "pie_binary" | head -1
    kill $! 2>/dev/null
done
```

### SMEP, SMAP, and Protection Keys

```
SMEP (Supervisor Mode Execution Prevention):
  CPU raises #PF if kernel (CPL=0) tries to execute a user-space page
  Prevents kernel-mode code injection via user pointer

SMAP (Supervisor Mode Access Prevention):
  CPU raises #PF if kernel (CPL=0) accesses a user-space page WITHOUT
  setting AC flag via stac/clac instructions
  Forces kernel to use explicit copy_from_user/copy_to_user

PKU (Protection Keys for Userspace):
  16 protection domains per page, controlled by PKRU register
  Can change permissions for entire domain in 1 cycle (vs. mprotect syscall)
  Used by gVisor, some memory allocators
```

```bash
# Check CPU support for SMEP/SMAP/PKU
grep -E "smep|smap|pku" /proc/cpuinfo

# Check kernel has SMEP/SMAP enforcement
sudo dmesg | grep -E "SMEP|SMAP|PKU"
```

---

## 16. Memory Mapped I/O (MMIO)

### How MMIO Works

PCI/PCIe devices expose their registers as physical memory ranges (BARs — Base Address Registers). The OS maps these into kernel virtual address space using `ioremap()`. Reads/writes to these virtual addresses go directly to device hardware, not DRAM.

```bash
# View PCI device MMIO regions (BARs)
sudo lspci -v | grep -A 5 "Memory at"

# Example output:
# 00:02.0 VGA compatible controller: Intel Corporation ...
#         Memory at e0000000 (64-bit, non-prefetchable) [size=16M]
#         Memory at d0000000 (64-bit, prefetchable) [size=256M]

# The physical addresses (e0000000, d0000000) are visible in /proc/iomem
sudo cat /proc/iomem | grep -i "pci\|VGA\|MMIO"
```

### Volatile Accesses and Memory Ordering

MMIO requires:
1. **Non-cached mappings** (`ioremap` uses WC or UC, not WB cache policy)
2. **Compiler barriers** to prevent reordering
3. **Memory fences** (mfence/sfence) for ordering across CPUs

```c
/* Kernel driver pattern for MMIO */
void __iomem *regs = ioremap(phys_bar_addr, bar_size);

/* WRONG: compiler may optimize/reorder these */
((uint32_t*)regs)[0] = cmd;
uint32_t status = ((uint32_t*)regs)[4];

/* CORRECT: use accessor macros that include barriers */
writel(cmd, regs + 0x00);      /* iowrite32 + wmb */
uint32_t status = readl(regs + 0x10); /* rmb + ioread32 */
```

In Rust (for bare-metal/embedded or kernel modules via helper crates):

```rust
// Using volatile_register or similar crate for MMIO
use core::ptr::{read_volatile, write_volatile};

unsafe {
    let regs = base_addr as *mut u32;
    // Volatile prevents compiler optimization/reordering
    write_volatile(regs.add(0), command);
    core::sync::atomic::fence(core::sync::atomic::Ordering::SeqCst);
    let status = read_volatile(regs.add(4));
}
```

---

## 17. Shared Memory Across Processes

### Virtual Addresses Differ, Physical Frames Same

When two processes mmap the same file or use `shm_open`, they have **different virtual addresses** pointing to the **same physical pages**.

```c
/* Process A */
void *p = mmap(NULL, 4096, PROT_READ|PROT_WRITE,
               MAP_SHARED, shm_fd, 0);
// p = 0x7f3abc000000

/* Process B */
void *q = mmap(NULL, 4096, PROT_READ|PROT_WRITE,
               MAP_SHARED, shm_fd, 0);
// q = 0x7f9def000000

/* p and q are DIFFERENT virtual addresses
 * but /proc/A/pagemap and /proc/B/pagemap show same PFN */
```

### Copy-on-Write (CoW) After fork()

After `fork()`, parent and child share physical pages with **write-protected PTEs**. On first write, the kernel:
1. Catches the write-protection page fault
2. Allocates a new physical page
3. Copies the content
4. Updates the PTE to point to the new page
5. Marks it writable
6. Resumes execution

```bash
# Observe CoW in action:
# Parent forks, child modifies memory
# Check /proc/PID/smaps for:
#   Private_Dirty: pages child dirtied (CoW happened)
#   Shared_Clean:  pages still shared with parent

cat /proc/self/smaps | grep -A 15 "heap"
# Shared_Clean:     0 kB
# Private_Clean:    0 kB
# Private_Dirty:  128 kB   ← these were CoW'd
```

---

## 18. Common Pitfalls & War Stories

### 1. Assuming Kernel Virtual = Physical

```c
/* WRONG in userspace */
uintptr_t phys = (uintptr_t)&my_var;  // This is VIRTUAL, not physical!

/* WRONG even in kernel for vmalloc'd memory */
phys_addr_t phys = virt_to_phys(vmalloc_ptr);  // UNDEFINED BEHAVIOR

/* CORRECT in kernel */
phys_addr_t phys = virt_to_phys(kmalloc_ptr);  // only for direct-mapped
```

### 2. DMA to Stack / vmalloc Memory

```c
/* CATASTROPHIC: DMA to stack — not physically contiguous */
char buf[1024];
dma_addr_t dma = dma_map_single(dev, buf, 1024, DMA_FROM_DEVICE);
// BUG: Stack buffer may straddle multiple non-contiguous physical pages
// The DMA controller writes past the buffer into adjacent physical memory!

/* CORRECT: Use DMA-safe allocation */
char *buf = dma_alloc_coherent(dev, 1024, &dma, GFP_KERNEL);
```

### 3. Go Stack Pointer Invalidation After Growth

```go
/* DANGEROUS: pointer to stack variable passed to long-lived operation */
func bad() {
    x := 42
    ptr := &x
    go func() {
        // If the parent goroutine's stack grows after this point,
        // the stack is COPIED to a new location.
        // Go's GC updates ALL known pointers, but:
        // if ptr was passed to C via CGo, that C pointer is now dangling
        _ = ptr
    }()
}
```

### 4. TLB Shootdown Stalls

When the kernel unmaps a page (munmap, mprotect), it must invalidate TLB entries on ALL cores that might have that address cached. This requires an Inter-Processor Interrupt (IPI) — a TLB shootdown.

```bash
# Monitor TLB shootdown IPIs
watch -n 1 'grep "TLB" /proc/interrupts'
# If this counter is growing rapidly, you have excessive munmap/mprotect calls
# Fix: use mremap instead of munmap+mmap, use longer-lived mappings
```

### 5. Physical Address Aliasing with DMA

```c
/* BUG: CPU cache holds stale data after device DMA write */
char *buf = kmalloc(4096, GFP_KERNEL);
dma_addr_t dma_addr = dma_map_single(dev, buf, 4096, DMA_FROM_DEVICE);

trigger_dma(dev, dma_addr, 4096);
wait_for_dma_complete(dev);

/* BUG: CPU cache may still have old data! Must sync: */
dma_sync_single_for_cpu(dev, dma_addr, 4096, DMA_FROM_DEVICE);
/* NOW safe to read buf */
process(buf);
```

### 6. NUMA-Unaware Allocation

```c
/* SLOW: allocating memory on remote NUMA node */
void *buf = malloc(HUGE_SIZE);  // may land on remote node
// All accesses cross the QPI/UPI interconnect

/* FAST: allocate on local NUMA node */
#include <numa.h>
void *buf = numa_alloc_local(HUGE_SIZE);
// Guaranteed local DRAM access
```

### 7. Rust: Raw Pointer Provenance

```rust
/* UNDEFINED BEHAVIOR: creating pointer from integer without provenance */
let addr: usize = 0x7fff_0000;
let ptr = addr as *const u8;  // UB: no provenance

/* CORRECT: use std::ptr::from_exposed_addr (nightly) or
   derive pointer from a valid reference */
let array = [0u8; 1024];
let base = array.as_ptr() as usize;
let ptr = unsafe { array.as_ptr().add(42) };  // valid provenance
```

---

## 19. Hands-on Exercises

### Exercise 1: Physical Address Scanner (C)

Write a program that:
1. Allocates 1 MB of memory
2. Touches every page
3. Reads `/proc/self/pagemap` for each page
4. Reports: total pages, how many are contiguous in physical memory, the "fragmentation ratio"
5. Repeat with `mlock()` and compare

Expected insight: Normal allocation gives fragmented physical pages. `mlock()` may improve contiguity.

```bash
# Skeleton:
gcc -O2 -o phys_scanner phys_scanner.c
sudo ./phys_scanner
# Output:
# Allocated 256 pages (1 MB)
# Physically contiguous runs: 12 (max run: 43 pages)
# Fragmentation ratio: 0.95
```

### Exercise 2: TLB Pressure Benchmark (C/Rust)

Write two allocators:
- **Scattered**: allocate 512 individual 4 KB pages (non-contiguous virtual)
- **Huge**: allocate 1 × 2 MB huge page

Benchmark random-access read throughput on both. The huge page version should be ~10–30% faster due to TLB efficiency.

```bash
# Use perf to measure TLB misses:
perf stat -e dTLB-misses,dTLB-loads ./bench_scattered
perf stat -e dTLB-misses,dTLB-loads ./bench_huge
```

### Exercise 3: Shared Memory Physical Proof (C + Go)

1. C process: creates shared memory via `shm_open` + `mmap`, writes PID to first page
2. Go process: opens same shm, reads PID
3. Both processes: read their own `/proc/self/pagemap` and print the PFN for the shared page
4. Verify: both PFNs are identical (same physical frame, different virtual addresses)

```bash
# C:  sudo ./shm_writer
# Go: sudo ./shm_reader
# Both should report: PFN = 0x1234 (same value)
```

### Exercise 4: MMIO Simulation (C)

1. Create a large anonymous mmap (acts as fake "device memory")
2. Write a "driver" that accesses it with volatile pointers
3. Use `perf` to compare: WB (write-back) access vs uncached (`mprotect` + `PROT_NONE` trick to simulate)
4. Document the latency difference

### Exercise 5: Go Goroutine Stack Migration Tracer

Write a Go program that:
1. Spawns a goroutine with a local `[4096]byte` array
2. Records the address of the array
3. Forces stack growth by making deeply recursive calls
4. After growth, records the new address of the array
5. Proves the stack moved (different virtual addresses before/after growth)

```go
// Hint: use runtime.Stack() to get goroutine info
// Use //go:noinline to force real stack frames
```

---

## 20. Security Checklist

For any system code dealing with memory addresses and mappings:

```
ASLR & PIE
  [ ] PIE enabled for all executables (-fPIE -pie / rustc default)
  [ ] ASLR is 2 in /proc/sys/kernel/randomize_va_space
  [ ] No hardcoded virtual addresses in code
  [ ] RELRO enabled (prevents .got.plt overwrites)

DMA Security
  [ ] IOMMU enabled (Intel VT-d / AMD-Vi) in firmware + kernel
  [ ] All DMA memory allocated via kernel DMA API, not raw physical
  [ ] dma_sync_* called correctly before CPU access post-DMA
  [ ] No DMA to stack, vmalloc, or highmem without bounce buffering
  [ ] IOMMU groups properly configured for device isolation

Memory Mapping
  [ ] mmap regions have minimum required permissions (no RWX)
  [ ] Shared mappings (MAP_SHARED) audited for cross-process data leaks
  [ ] MADV_DONTDUMP on sensitive memory (prevents core dump leaks)
  [ ] MADV_WIPEONFORK on cryptographic key material

Kernel/Userspace Boundary
  [ ] Never dereference user pointers directly in kernel (use copy_from_user)
  [ ] SMEP/SMAP enabled (check /proc/cpuinfo)
  [ ] No kernel pointer leaks to userspace (check %pK in printk)
  [ ] KASLR enabled (/proc/sys/kernel/kptr_restrict = 2)

Rust Specifics
  [ ] unsafe blocks minimized and documented
  [ ] Raw pointer provenance tracked (no usize→pointer casts without provenance)
  [ ] No dangling pointers from stack variables passed to long-lived contexts
  [ ] MIRI run for all unsafe code (cargo miri test)
  [ ] No unsound Send/Sync implementations for pointer-holding types

Go Specifics
  [ ] No stack pointers passed to CGo
  [ ] runtime.Pinner used when pinning Go memory for CGo/external use
  [ ] No unsafe.Pointer arithmetic outside documented patterns
  [ ] Memory not read after it may have been collected (runtime.KeepAlive)

Physical Memory
  [ ] /proc/mem and /dev/mem access restricted (CONFIG_STRICT_DEVMEM=y)
  [ ] CAP_SYS_RAWIO not granted to untrusted processes
  [ ] pagemap access restricted (/proc/sys/kernel/perf_event_paranoid)
  [ ] NUMA topology considered for latency-sensitive allocations
```

---

## 21. Further Reading

### Books

1. **"What Every Programmer Should Know About Memory"** — Ulrich Drepper (free PDF)  
   The definitive ~100-page paper on CPU caches, virtual memory, TLB, NUMA, and DMA from a programmer's perspective.

2. **"Linux Kernel Development"** — Robert Love (3rd ed.)  
   Chapters 15–17 cover the Linux memory model, page tables, slab allocator.

3. **"Understanding the Linux Virtual Memory Manager"** — Mel Gorman (free online)  
   Exhaustive deep-dive into the Linux VM subsystem internals.

4. **"Computer Organization and Design (RISC-V Edition)"** — Patterson & Hennessy  
   Chapters 5-6: hardware memory hierarchy, TLB, cache design.

### Key Source Files in the Linux Kernel

```bash
# Page table definitions
arch/x86/include/asm/pgtable.h
arch/x86/include/asm/pgtable_types.h

# MMU/TLB management
arch/x86/mm/tlb.c          # TLB flush, shootdown
arch/x86/mm/fault.c        # Page fault handler (do_page_fault)
arch/x86/mm/pgtable.c      # Page table allocation/manipulation

# Memory zones and NUMA
mm/page_alloc.c            # Buddy allocator
mm/mmap.c                  # mmap/munmap implementation
mm/memory.c                # Page fault handling, CoW

# DMA
kernel/dma/mapping.c       # DMA API implementation
drivers/iommu/             # IOMMU drivers (Intel VT-d, AMD-Vi)
```

### Key Repositories

1. **linux/mm** — `https://github.com/torvalds/linux/tree/master/mm`  
   The entire Linux memory management subsystem. Start with `mm/memory.c` (page fault), `mm/mmap.c` (virtual memory areas), `mm/page_alloc.c` (physical page allocator).

2. **rust-vmm** — `https://github.com/rust-vmm`  
   Collection of VMM building blocks in Rust: `vm-memory` crate for safe abstraction over guest physical/virtual memory, `kvm-ioctls` for KVM hypervisor interaction.

3. **bpftool + libbpf** — `https://github.com/libbpf/libbpf`  
   eBPF-based memory tracing tools. Use `bpftrace` probes on `do_page_fault` and `handle_mm_fault` to trace page fault behavior in real workloads.

### Useful Commands Reference

```bash
# Memory layout and stats
cat /proc/self/maps           # Virtual memory areas
cat /proc/self/smaps          # Detailed VMA stats (RSS, PSS, swap)
cat /proc/self/smaps_rollup   # Aggregated smaps
cat /proc/self/status         # VmRSS, VmSwap, VmPeak
cat /proc/meminfo             # System-wide memory stats
cat /proc/buddyinfo           # Physical page allocator state
cat /proc/pagetypeinfo        # Page type breakdown
cat /proc/iomem               # Physical memory map
cat /proc/zoneinfo            # NUMA zone statistics

# Hardware info
sudo dmidecode --type 17      # DIMM physical slots
numactl --hardware            # NUMA topology
lstopo --of ascii             # Hardware topology (hwloc)

# Tracing
perf stat -e cache-misses,cache-references,dTLB-misses ./prog
perf mem record ./prog && perf mem report
valgrind --tool=massif ./prog # Heap profiling with physical details
heaptrack ./prog              # Low-overhead heap profiler

# Kernel debugging
sudo cat /sys/kernel/debug/page_owner   # Who allocated each page (CONFIG_PAGE_OWNER=y)
sudo cat /sys/kernel/debug/kmemleak     # Memory leak detection (CONFIG_KMEMLEAK=y)
sudo perf kmem stat --slab              # Slab allocator statistics
```

---

*Guide written for Linux 6.x, x86-64. Concepts apply broadly to ARM64 (4-level pages, IOMMU via SMMU) with register/constant differences. Go version ≥ 1.21, Rust ≥ 1.75 assumed.*

Here's what the guide covers end-to-end:

**Structure (21 sections):**

1. **Mental model** — The three-coordinate-system analogy with full ASCII pipeline diagram
2. **Physical addresses** — E820 map, PFN arithmetic, how Linux discovers RAM at boot
3. **Virtual addresses** — 48-bit decomposition, canonical form, `/proc/self/maps`
4. **Bus/DMA addresses** — IOMMU remapping, bounce buffers, why `bus_addr ≠ phys_addr`
5. **MMU, TLB, caches** — TLB entry layout, PCID, shootdown IPIs, PIPT cache model
6. **Linux x86-64 layout** — Complete virtual address map (128 TB user, direct mapping, vmalloc, kernel text)
7. **Page tables (4 & 5 level)** — Full PTE bit layout, huge pages (2 MB / 1 GB), LA57
8. **Address translation walkthrough** — Exact bit extraction for a real address, hardware page walker, page fault handler path
9. **NUMA and zones** — DMA/DMA32/NORMAL/MOVABLE zones, buddy allocator, `numactl`
10. **DMA / IOMMU internals** — Kernel DMA API (`dma_alloc_coherent`, `dma_map_single`), IOMMU security model
11. **Kernel memory APIs** — `phys_to_virt`, `ioremap`, `get_user_pages`, pagemap format
12. **C implementation** — Full `addr_inspect.c`: pagemap reader, VAddr decomposer, huge page demo, mlock, mmio access via `/dev/mem`
13. **Rust implementation** — Safe + unsafe introspection, escape analysis, goroutine-equivalent stack tracking, `mmap` via `libc` FFI, pagemap translation, full test suite
14. **Go implementation** — Goroutine stack behavior (heap-allocated, moves on growth!), escape analysis traps, `runtime.MemStats`, syscall-level `mmap`, GC→physical memory release
15. **ASLR/KASLR/SMEP/SMAP** — Security primitives and their kernel enforcement
16. **MMIO** — Why volatile + memory fences are mandatory, `ioremap` pattern
17. **Shared memory / CoW** — Same PFN across processes, fork CoW mechanics
18. **Pitfalls** — 7 real war stories (DMA to stack, Go stack migration, TLB shootdown stalls, cache coherency bugs, NUMA-blind allocation)
19. **Exercises** — 5 hands-on labs with expected outputs
20. **Security checklist** — Production-ready checklist across ASLR, DMA, kernel boundary, Rust/Go specifics
21. **Further reading** — Ulrich Drepper's paper, kernel source pointers, rust-vmm repo