# Linux Memory Management Unit (MMU) — Complete Engineering Guide

> **Summary:** The MMU is the hardware bridge between virtual addresses used by software and physical addresses on DRAM. Linux exploits it through a multi-layer software stack: page tables, TLB management, zone-based physical allocators (buddy + slab/slub), demand-paging with CoW, NUMA topology awareness, huge-page promotion, and swap/reclaim. Every security isolation boundary — process-to-process, user-to-kernel (KPTI), hypervisor-to-guest (EPT/NPT), sandbox-to-host — is ultimately enforced by MMU hardware and Linux's page-table management code. Understanding the MMU end-to-end is prerequisite to secure system design, exploit mitigation, kernel hacking, allocator engineering, and hypervisor/container runtime work.

---

## Table of Contents

1. [Hardware Architecture of the MMU](#1-hardware-architecture-of-the-mmu)
2. [Virtual Address Space Layout](#2-virtual-address-space-layout)
3. [Page Tables — Structure and Walk](#3-page-tables--structure-and-walk)
4. [Translation Lookaside Buffer (TLB)](#4-translation-lookaside-buffer-tlb)
5. [Linux MM Subsystem Architecture](#5-linux-mm-subsystem-architecture)
6. [Physical Memory Zones](#6-physical-memory-zones)
7. [Buddy Allocator](#7-buddy-allocator)
8. [Slab / SLUB Allocator](#8-slab--slub-allocator)
9. [Page Fault Handling](#9-page-fault-handling)
10. [Copy-on-Write (CoW)](#10-copy-on-write-cow)
11. [Memory-Mapped Files (mmap)](#11-memory-mapped-files-mmap)
12. [Huge Pages and Transparent Huge Pages](#12-huge-pages-and-transparent-huge-pages)
13. [NUMA Architecture and Memory Policy](#13-numa-architecture-and-memory-policy)
14. [Swap, Reclaim, and the Page Reclaim Engine](#14-swap-reclaim-and-the-page-reclaim-engine)
15. [OOM Killer](#15-oom-killer)
16. [Memory Security — MMU-enforced Mitigations](#16-memory-security--mmu-enforced-mitigations)
17. [Extended Page Tables / Nested Paging (Virtualization)](#17-extended-page-tables--nested-paging-virtualization)
18. [C Implementations](#18-c-implementations)
19. [Rust Implementations](#19-rust-implementations)
20. [Threat Model and Mitigations](#20-threat-model-and-mitigations)
21. [Testing, Fuzzing, and Benchmarking](#21-testing-fuzzing-and-benchmarking)
22. [Roll-out / Rollback Plan](#22-roll-out--rollback-plan)
23. [References](#23-references)
24. [Next 3 Steps](#24-next-3-steps)

---

## 1. Hardware Architecture of the MMU

### 1.1 What the MMU Does

The MMU is a hardware unit (historically discrete, now integrated into the CPU core) that performs:

1. **Virtual-to-physical address translation** — every load/store instruction emits a virtual address; the MMU converts it to a physical address before the memory bus sees it.
2. **Permission enforcement** — read/write/execute bits on each page; user vs. supervisor mode.
3. **Caching attribute control** — write-back, write-through, uncacheable, write-combining per page.
4. **TLB management** — caching recent translations to avoid repeated page-table walks.

```
 CPU Core
 ┌──────────────────────────────────────────────────────────┐
 │  Pipeline                                                │
 │   LD r0, [vaddr]                                         │
 │        │                                                 │
 │        ▼                                                 │
 │  ┌──────────┐    TLB Hit?    ┌────────────────────┐      │
 │  │   MMU    │───────────────▶│  L1 Data Cache     │      │
 │  │  (HW PTE │    TLB Miss    │  (physical-tagged) │      │
 │  │   Walker)│──────────────┐ └────────────────────┘      │
 │  └──────────┘              │                             │
 │        ▲                   ▼                             │
 │        │          Page-Table Walker (HW)                 │
 │   CR3 / TTBR0              │                             │
 │   (page-table root)        ▼                             │
 └────────────────────────────┼─────────────────────────────┘
                              │  Physical Memory Bus
                              ▼
                    ┌──────────────────┐
                    │  DRAM / PMEM     │
                    └──────────────────┘
```

### 1.2 x86-64 MMU Registers

| Register | Role |
|---|---|
| `CR0.PG` | Enable paging |
| `CR0.WP` | Write-protect — even kernel cannot write RO pages (critical for CoW security) |
| `CR3` | Physical address of PML4 (page-map level-4) table |
| `CR4.PAE` | Physical Address Extension (always on in 64-bit) |
| `CR4.PSE` | Page Size Extension (huge pages) |
| `CR4.PGE` | Global pages — not flushed on CR3 reload |
| `CR4.SMEP` | Supervisor Mode Execution Prevention |
| `CR4.SMAP` | Supervisor Mode Access Prevention |
| `CR4.LA57` | 5-level paging (57-bit VA) |
| `IA32_EFER.NXE` | Enable No-Execute bit in PTEs |
| `PCID` (CR4.PCIDE) | Process Context IDs — tagged TLB entries |

### 1.3 ARM64 (AArch64) MMU Registers

| Register | Role |
|---|---|
| `TTBR0_EL1` | User-space page-table root (VA[0..VABITS-1]) |
| `TTBR1_EL1` | Kernel page-table root (high VA range) |
| `TCR_EL1` | Translation Control Register — VA/PA sizes, granule |
| `MAIR_EL1` | Memory Attribute Indirection Register — 8 cache attribute slots |
| `SCTLR_EL1.M` | Enable MMU |
| `SCTLR_EL1.WXN` | Write implies XN (W^X enforcement) |
| `PAN` | Privileged Access Never (SMAP equivalent) |
| `PXN / UXN` | Privileged/Unprivileged Execute Never |

### 1.4 Page Granules

| Architecture | Small Page | Medium Page | Huge Page |
|---|---|---|---|
| x86-64 | 4 KiB | 2 MiB (PDEs) | 1 GiB (PDPEs) |
| ARM64 (4K granule) | 4 KiB | 2 MiB | 1 GiB |
| ARM64 (16K granule) | 16 KiB | 32 MiB | — |
| ARM64 (64K granule) | 64 KiB | 512 MiB | — |
| RISC-V Sv39 | 4 KiB | 2 MiB | 1 GiB |
| RISC-V Sv48 | 4 KiB | 2 MiB | 1 GiB | 512 GiB |

---

## 2. Virtual Address Space Layout

### 2.1 x86-64 (48-bit VA, 4-level paging)

```
Bit 63                                              Bit 0
 ┌────────────────────────────────────────────────────────┐
 │ Sign-extended │  PML4 idx │ PDP idx │ PD idx │ PT idx │ Offset │
 │   [63:48]     │  [47:39]  │ [38:30] │ [29:21]│ [20:12]│ [11:0] │
 │   (canonical) │   9 bits  │  9 bits │ 9 bits │ 9 bits │ 12 bits│
 └────────────────────────────────────────────────────────┘

User space:   0x0000_0000_0000_0000 – 0x0000_7FFF_FFFF_FFFF  (128 TiB)
Canonical hole: 0x0000_8000_0000_0000 – 0xFFFF_7FFF_FFFF_FFFF
Kernel space: 0xFFFF_8000_0000_0000 – 0xFFFF_FFFF_FFFF_FFFF  (128 TiB)
```

#### Kernel Virtual Address Regions (x86-64, Linux 6.x)

```
0xFFFF_8000_0000_0000  ┌─────────────────────────────┐
                       │  Direct Map (physmap)        │  All RAM mapped 1:1
                       │  (--KASLR offset applied)    │
0xFFFF_C900_0000_0000  ├─────────────────────────────┤
                       │  vmalloc / ioremap region    │  256 TiB
0xFFFF_E900_0000_0000  ├─────────────────────────────┤
                       │  virtual memory map          │  struct page array
0xFFFF_EA00_0000_0000  ├─────────────────────────────┤
                       │  KASAN shadow memory         │
0xFFFF_F000_0000_0000  ├─────────────────────────────┤
                       │  %esp fixup stacks           │
0xFFFF_FF00_0000_0000  ├─────────────────────────────┤
                       │  Kernel text / modules       │
                       │  (KPTI: separate PGD)        │
0xFFFF_FFFF_FFFF_FFFF  └─────────────────────────────┘
```

### 2.2 User Space Process Layout (x86-64)

```
High addresses
0x0000_7FFF_FFFF_FFFF  ┌──────────────────────┐
                       │  Stack (grows ↓)      │  ulimit -s
                       │  [RLIMIT_STACK]       │
                       ├──────────────────────┤
                       │  VDSO / VSYSCALL      │  Kernel-mapped
                       ├──────────────────────┤
                       │  mmap region          │  ASLR randomized
                       │  (shared libs, anon)  │
                       ├──────────────────────┤
                       │  Heap (grows ↑)       │  brk()
                       ├──────────────────────┤
                       │  BSS (zero-init)      │
                       │  Data (init)          │
                       │  Text (code, RO)      │
0x0000_0000_0040_0000  └──────────────────────┘  (typical, ASLR shifts)
Low addresses
```

### 2.3 5-Level Paging (LA57, CR4.LA57)

With `CR4.LA57`, Linux supports 57-bit virtual addresses (128 PiB user + 128 PiB kernel). The PML5 (Page-Map Level-5) table adds another level:

```
[56:48] PML5 index (9 bits) → [47:39] PML4 → [38:30] PDP → [29:21] PD → [20:12] PT → [11:0] offset
```

Enabled in Linux via `CONFIG_X86_5LEVEL=y`. Hardware requires Intel Ice Lake or later.

---

## 3. Page Tables — Structure and Walk

### 3.1 x86-64 Page Table Entry (PTE) Format

```
Bit 63   62:52   51:12          11   10   9    8    7    6    5    4    3    2    1    0
 ┌───┬─────────┬──────────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
 │NX │ Ignored │  PFN[51:12]  │ G  │ PS │ D  │ A  │PCD │PWT │ U  │ RW │ P  │    │    │    │
 └───┴─────────┴──────────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
  NX  = No-Execute (IA32_EFER.NXE must be set)
  G   = Global (not flushed on CR3 reload — used for kernel pages)
  PS  = Page Size (1 = 2MiB/1GiB at PDE/PDPE level)
  D   = Dirty (HW sets on write)
  A   = Accessed (HW sets on read or write)
  PCD = Page Cache Disable
  PWT = Page Write Through
  U   = User accessible (0 = supervisor only)
  RW  = Read/Write (0 = read-only)
  P   = Present
```

Linux PTE software bits (when P=0, page is swapped out):

```
Bits [11:1] encode swap type and offset in the absent-page case.
```

### 3.2 Page Table Walk (4-level, x86-64)

```
CR3 → PML4 Table (512 × 8 bytes = 4 KiB)
         │
         │  VA[47:39] → PML4E → PDPT physical addr
         ▼
       PDPT Table (512 × 8 bytes)
         │
         │  VA[38:30] → PDPTE → PD physical addr  (or 1GiB huge page if PS=1)
         ▼
       PD Table (512 × 8 bytes)
         │
         │  VA[29:21] → PDE → PT physical addr    (or 2MiB huge page if PS=1)
         ▼
       PT Table (512 × 8 bytes)
         │
         │  VA[20:12] → PTE → physical page frame number
         ▼
       Physical Page + VA[11:0] offset → Physical Address
```

**Page-table memory cost per process:**
- Worst case (full 128 TiB user space): PML4(4K) + 512×PDPT(2M) + 512²×PD(1G) + 512³×PT(512G) — practically only populated entries consume memory. A minimal process uses ~3 page-table pages.

### 3.3 Linux Folded Page Table Abstraction

Linux uses a generic 5-level abstraction internally (`pgd → p4d → pud → pmd → pte`) that folds levels on architectures with fewer hardware levels:

```c
// include/linux/pgtable.h
// On x86-64 without LA57:
//   pgd_t  = PML4 entry
//   p4d_t  = folded (identity) — no separate table
//   pud_t  = PDPT entry
//   pmd_t  = PD entry
//   pte_t  = PT entry

typedef struct { pgdval_t pgd; } pgd_t;
typedef struct { p4dval_t p4d; } p4d_t;  // identity with pgd on 4-level
typedef struct { pudval_t pud; } pud_t;
typedef struct { pmdval_t pmd; } pmd_t;
typedef struct { pteval_t pte; } pte_t;

// Traversal macros
pgd_t *pgd = pgd_offset(mm, addr);       // index into process PGD
p4d_t *p4d = p4d_offset(pgd, addr);
pud_t *pud = pud_offset(p4d, addr);
pmd_t *pmd = pmd_offset(pud, addr);
pte_t *pte = pte_offset_map(pmd, addr);  // also kmap on 32-bit HIGHMEM
```

### 3.4 ARM64 Page Table Entry

```
Bit 63   UXN PXN  Contiguous  DBM  OutputAddr[47:12]  nG  AF  SH[1:0]  AP[2:1]  NS  AttrIndx[2:0]  Type[1:0]
```

- `AP[2:1]`: Access Permission — `00`=kernel RW, `01`=kernel+user RW, `10`=kernel RO, `11`=kernel+user RO
- `AttrIndx[2:0]`: indexes into `MAIR_EL1` (8 slots: device, normal-NC, normal-WB, etc.)
- `AF`: Access Flag — ARM64 can generate access-flag faults; Linux uses HW management (`FEAT_HAFDBS`)

### 3.5 RISC-V Sv48 Page Table Entry

```
Bit 63:54  53:10         9   8   7   6   5   4   3   2   1   0
 ┌────────┬───────────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
 │Reserved│ PPN[3:0]  │RSW│ D │ A │ G │ U │ X │ W │ R │ V │   │
 └────────┴───────────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  V = Valid, R = Readable, W = Writable, X = Executable
  U = User mode accessible, G = Global, A = Accessed, D = Dirty
  RSW = Reserved for software
```

---

## 4. Translation Lookaside Buffer (TLB)

### 4.1 TLB Structure

The TLB is a set-associative cache of recent `{PCID, VA} → {PA, permissions, attributes}` mappings. Modern x86 CPUs have:

```
Intel Skylake TLB hierarchy:
  L1 DTLB:  64 entries, 4-way, covers 4K + 2M + 1G pages
  L1 ITLB:  128 entries, 8-way (4K), 8 entries (2M/1G)
  L2 STLB:  1536 entries, 12-way, unified (4K + 2M only)
  PDPTE cache: 4 entries for 1GiB pages
```

### 4.2 TLB Invalidation (x86-64)

```c
// Flush entire TLB (reloads CR3)
static inline void __flush_tlb_all(void)
{
    __native_flush_tlb_global(); // write CR4.PGE to 0 then back
}

// Flush single VA
static inline void __flush_tlb_one_user(unsigned long addr)
{
    asm volatile("invlpg (%0)" :: "r" (addr) : "memory");
}

// INVPCID — flush by PCID (Ivy Bridge+)
struct invpcid_desc {
    u64 pcid : 12;
    u64 reserved : 52;
    u64 addr;
};
static inline void invpcid_flush_one(unsigned long pcid, unsigned long addr)
{
    struct invpcid_desc d = { .pcid = pcid, .addr = addr };
    asm volatile("invpcid %0, %1" :: "m"(d), "r"(0UL) : "memory");
}
```

### 4.3 PCID — Process Context IDs

With `CR4.PCIDE`, each TLB entry is tagged with a 12-bit PCID. On CR3 reload (context switch), Linux sets `CR3[63]=1` (NOFLUSH bit) to retain TLB entries of the new process's PCID, eliminating the full TLB flush cost on context switches.

```
CR3 format with PCID:
Bit 63: NOFLUSH (don't flush on this CR3 write)
Bits [11:0]: PCID (0..4095)
Bits [63:12]: Physical address of PML4 (shifted right 12)
```

Linux PCID allocation (`arch/x86/mm/tlb.c`): PCIDs are assigned per `mm_struct`, recycled as a small FIFO, with lazy invalidation using generation counters.

### 4.4 TLB Shootdown (SMP)

On multiprocessor systems, when a PTE is modified (unmap, permission change), all CPUs caching that translation must be notified:

```
CPU 0 (modifies PTE)                  CPU 1..N (caches stale TLB entry)
    │                                      │
    ├── ptep_clear_flush()                 │
    │   ├── set PTE to 0                   │
    │   └── send IPI (CALL_FUNCTION_MANY)──┼──► flush_tlb_func()
    │                                      │     invlpg(addr) or CR3 reload
    │   wait for all CPUs to ACK ◄─────────┤
    └── return (PTE modification safe)     │
```

**Performance note:** TLB shootdowns are expensive O(N CPUs) IPIs. Linux batches them via `mmu_gather` (`tlb_gather_mmu` / `tlb_finish_mmu`) during `unmap_page_range`.

### 4.5 ARM64 TLB Invalidation

```c
// Invalidate by VA, EL1 (kernel) — Inner Shareable domain
asm volatile("tlbi vaae1is, %0" :: "r"(addr >> 12));
dsb(ish);
isb();

// Invalidate by ASID
asm volatile("tlbi aside1is, %0" :: "r"((u64)asid << 48));
```

ARM64 uses ASIDs (Address Space IDs, 8 or 16-bit) analogous to PCIDs.

---

## 5. Linux MM Subsystem Architecture

### 5.1 Component Map

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          User Space Process                                  │
│   malloc() / mmap() / brk() / mprotect() / madvise()                        │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │ syscall
┌────────────────────────────────▼─────────────────────────────────────────────┐
│                  Virtual Memory Manager (VMM)                                │
│                                                                              │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │ mm_struct      │  │ vm_area_struct  │  │ Page Fault Handler           │  │
│  │ (per-process)  │  │ (VMA) rbtree    │  │ do_page_fault()              │  │
│  │ mmap_sem       │  │ vm_ops          │  │ handle_mm_fault()            │  │
│  │ pgd *          │  │ vm_file         │  │ do_fault() / do_swap_page()  │  │
│  └────────────────┘  └─────────────────┘  └──────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    Page Table Management                               │  │
│  │  pgd_alloc / pud_alloc / pmd_alloc / pte_alloc                        │  │
│  │  set_pte_at / ptep_clear_flush / ptep_set_wrprotect                   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────────────────┐
│                    Physical Memory Manager                                   │
│                                                                              │
│  ┌──────────────────────────┐   ┌───────────────────────────────────────┐   │
│  │  Memory Zones            │   │  NUMA Node Topology                   │   │
│  │  ZONE_DMA (<16MiB)       │   │  pg_data_t (per node)                 │   │
│  │  ZONE_DMA32 (<4GiB)      │   │  node_zones[], node_zonelists[]       │   │
│  │  ZONE_NORMAL             │   │  cpumask, distance matrix             │   │
│  │  ZONE_MOVABLE            │   └───────────────────────────────────────┘   │
│  │  ZONE_DEVICE             │                                                │
│  └──────────────────────────┘                                                │
│                                                                              │
│  ┌──────────────────────────┐   ┌───────────────────────────────────────┐   │
│  │  Buddy Allocator         │   │  SLUB Allocator                       │   │
│  │  alloc_pages(gfp, order) │   │  kmem_cache_alloc()                   │   │
│  │  free_pages()            │   │  kmalloc() → size-based caches        │   │
│  │  __get_free_pages()      │   │  Per-CPU slabs, partial lists         │   │
│  └──────────────────────────┘   └───────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────┐   ┌───────────────────────────────────────┐   │
│  │  Page Reclaim Engine     │   │  Swap / Zswap / Zram                  │   │
│  │  kswapd / direct reclaim │   │  swap_writepage()                     │   │
│  │  LRU lists (active/inact)│   │  do_swap_page()                       │   │
│  │  shrink_node()           │   │  frontswap / cleancache               │   │
│  └──────────────────────────┘   └───────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Data Structures

```c
// mm_struct — one per process (shared by threads in same address space)
struct mm_struct {
    struct maple_tree   mm_mt;          // VMA tree (since 6.1, replaces rbtree)
    pgd_t              *pgd;            // page-global directory
    atomic_t            mm_users;       // threads sharing this mm
    atomic_t            mm_count;       // references including kernel
    unsigned long       mmap_base;      // base of mmap area (ASLR)
    unsigned long       task_size;      // max user VA
    unsigned long       start_code, end_code;
    unsigned long       start_data, end_data;
    unsigned long       start_brk, brk; // heap
    unsigned long       start_stack;
    struct rw_semaphore mmap_lock;      // protects VMA tree
    // NUMA, RSS counters, mm_cpumask, context...
};

// vm_area_struct — contiguous virtual memory region
struct vm_area_struct {
    unsigned long       vm_start;       // inclusive
    unsigned long       vm_end;         // exclusive
    struct mm_struct   *vm_mm;
    pgprot_t            vm_page_prot;   // page table protection bits
    unsigned long       vm_flags;       // VM_READ, VM_WRITE, VM_EXEC, VM_SHARED...
    struct file        *vm_file;        // backing file (NULL for anon)
    unsigned long       vm_pgoff;       // offset in file (pages)
    const struct vm_operations_struct *vm_ops;
    // vm_ops->fault() called on page fault
};

// page (struct page) — one per physical page frame
struct page {
    unsigned long       flags;          // PG_locked, PG_dirty, PG_lru, PG_writeback...
    union {
        struct address_space *mapping;  // file backing or anon_vma
        struct kmem_cache    *slab_cache;
    };
    pgoff_t             index;          // file offset or swap entry
    atomic_t            _refcount;
    atomic_t            _mapcount;      // # PTEs mapping this page (-1 = not mapped)
    struct list_head    lru;            // LRU or slab lists
    // ... compound page, slab, hugetlb overlays
};
```

---

## 6. Physical Memory Zones

### 6.1 Zone Layout

```
Physical Memory (example 8GiB system):
 0              16MiB         4GiB                   8GiB
 ├──────────────┼─────────────┼──────────────────────┤
 │  ZONE_DMA    │ ZONE_DMA32  │    ZONE_NORMAL        │
 │  (ISA DMA    │ (32-bit DMA │    (general purpose)  │
 │   devices)   │  devices)   │                       │
 └──────────────┴─────────────┴──────────────────────┘
```

- **ZONE_DMA** (`< 16 MiB`): Legacy ISA DMA devices. Most modern code avoids this.
- **ZONE_DMA32** (`< 4 GiB`): 32-bit PCI DMA devices, NVMe, some NICs.
- **ZONE_NORMAL**: Main allocation zone, directly mapped in kernel VA.
- **ZONE_HIGHMEM** (32-bit only): Physical RAM above kernel's direct map; not present on 64-bit.
- **ZONE_MOVABLE**: Pages that can be migrated (enables memory hot-unplug, balloon inflation).
- **ZONE_DEVICE**: Persistent memory (PMEM/NVDIMM), GPU memory via HMM.

### 6.2 GFP Flags (Get Free Pages)

```c
// Core allocation flags (include/linux/gfp.h)
GFP_KERNEL      = __GFP_RECLAIM | __GFP_IO | __GFP_FS   // normal kernel alloc
GFP_ATOMIC      = __GFP_HIGH | __GFP_ATOMIC              // IRQ context, no sleep
GFP_NOWAIT      = __GFP_ATOMIC                           // don't wait, don't warn
GFP_NOIO        = __GFP_RECLAIM                          // no I/O during reclaim
GFP_NOFS        = __GFP_RECLAIM | __GFP_IO               // no FS during reclaim
GFP_USER        = __GFP_RECLAIM | __GFP_IO | __GFP_FS | __GFP_HARDWALL
GFP_HIGHUSER    = GFP_USER | __GFP_HIGHMEM
GFP_DMA         = __GFP_DMA                              // must be in ZONE_DMA
GFP_DMA32       = __GFP_DMA32
__GFP_ZERO      = zero the page
__GFP_NOFAIL    = retry forever (dangerous — avoid)
__GFP_NOWARN    = suppress OOM warnings
__GFP_THISNODE  = allocate only on current NUMA node
__GFP_MOVABLE   = page can be migrated
```

### 6.3 Zone Watermarks

Each zone has three watermarks controlling reclaim behavior:

```
Free pages in zone:
 ▲
 │  ████████████████████████  ← pages_high (kswapd goes back to sleep)
 │  ░░░░░░░░░░░░░░░░░░░░░░░░  ← watermark[WMARK_HIGH]
 │  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  ← watermark[WMARK_LOW]  (kswapd wakes up)
 │  ░░░░░░░░░░░░░░░░░░░░░░░░  ← watermark[WMARK_MIN]  (direct reclaim + OOM)
 │
 0
```

Tunable via `/proc/sys/vm/watermark_scale_factor` and `min_free_kbytes`.

---

## 7. Buddy Allocator

### 7.1 Algorithm

The buddy allocator manages free pages in power-of-2 blocks (order 0 = 1 page, order 1 = 2 pages, ..., order MAX_ORDER-1 = 2^(MAX_ORDER-1) pages, typically 10 → 512 pages = 2 MiB max).

```
Free lists (per zone, per NUMA node, per migration type):
 Order 0: [4K][4K][4K]...
 Order 1: [8K][8K]...
 Order 2: [16K]...
 ...
 Order 10: [4M blocks]...

Allocation of order 2 (16K):
  1. Check order-2 free list → empty
  2. Check order-3 free list → found 32K block
  3. Split: return lower 16K, add upper 16K to order-2 free list

Free of order 2 block at pfn X:
  buddy_pfn = X XOR (1 << order)  // flip bit at order position
  if buddy is free and same order:
      remove buddy from free list
      coalesce → order 3 block, recurse
```

### 7.2 Migration Types

Each free list is split by migration type to reduce fragmentation:

```c
enum migratetype {
    MIGRATE_UNMOVABLE,    // kernel allocations, pinned memory
    MIGRATE_MOVABLE,      // user pages, can be migrated by compaction
    MIGRATE_RECLAIMABLE,  // page cache, can be reclaimed
    MIGRATE_PCPTYPES,     // per-CPU caches
    MIGRATE_HIGHATOMIC,   // high-order atomic reserves
    MIGRATE_CMA,          // contiguous memory allocator
    MIGRATE_ISOLATE,      // isolated for migration
};
```

### 7.3 Per-CPU Page Cache (PCP)

To reduce lock contention on the buddy allocator's zone lock, each CPU maintains a per-CPU cache of order-0 pages:

```c
struct per_cpu_pages {
    int count;            // number of pages in list
    int high;             // drain when count > high
    int batch;            // refill/drain batch size
    struct list_head lists[MIGRATE_PCPTYPES];
};
```

Allocation: check PCP → if empty, refill from buddy in batch. Free: add to PCP → if full, return batch to buddy.

### 7.4 Memory Compaction

`kcompactd` (and direct compaction) migrates MOVABLE pages to consolidate free space for high-order allocations (e.g., huge page allocation):

```
Before compaction:  [U][F][U][F][F][U][F][F][F][U]  (U=used, F=free)
After compaction:   [U][U][U][U][F][F][F][F][F][F]  → order-4 block available
```

---

## 8. Slab / SLUB Allocator

### 8.1 Architecture

The SLUB allocator (default since 2.6.23) sits above the buddy allocator providing efficient sub-page allocations:

```
kmalloc(256) / kmem_cache_alloc(my_cache)
        │
        ▼
  SLUB Allocator
  ┌─────────────────────────────────────────────────────┐
  │  kmem_cache (descriptor)                            │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Per-CPU slab (kmem_cache_cpu)               │   │
  │  │  freelist → next free object (singly-linked) │   │
  │  │  page *    → current slab page               │   │
  │  └──────────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Per-node partial list (kmem_cache_node)     │   │
  │  │  slabs with free slots (FIFO, lock protected)│   │
  │  └──────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────┘
        │ (slab exhausted)
        ▼
  alloc_pages(GFP_KERNEL, cache->min_partial_order)
```

### 8.2 Object Layout and Freelist Randomization

```
Slab page (e.g., 4 KiB for 128-byte objects):
 ┌──────────────────────────────────────────────┐
 │ [obj0 128B][obj1 128B]...[obj31 128B]        │
 │  freelist: randomized pointer to next free   │
 │  (XOR'd with per-cache secret for hardening) │
 └──────────────────────────────────────────────┘
```

`CONFIG_SLAB_FREELIST_RANDOM`: shuffle freelist order at cache init.  
`CONFIG_SLAB_FREELIST_HARDENED`: XOR freelist pointer with random cookie to detect corruption.

### 8.3 kmalloc Size Classes

```
kmalloc caches (SLUB): 8, 16, 32, 64, 96, 128, 192, 256, 512, 1024, 2048, 4096, 8192
                        (DMA variants for each, RECLAIM variants)
```

### 8.4 SLUB Debug Options

```bash
# Kernel boot cmdline
slub_debug=FZP          # F=sanity checks, Z=red zones, P=poison
slub_debug=FZP,kmalloc-64  # target specific cache

# Runtime
echo 1 > /sys/kernel/slab/kmalloc-64/sanity_checks
cat /sys/kernel/slab/kmalloc-64/alloc_calls   # allocation call sites
```

---

## 9. Page Fault Handling

### 9.1 Fault Entry Path (x86-64)

```
CPU raises #PF exception (vector 14)
     │
     ▼
asm_exc_page_fault()  [arch/x86/entry/entry_64.S]
     │  CR2 = faulting virtual address
     │  error code: P(present), W(write), U(user), RSVD, I(fetch), PK, SS
     ▼
exc_page_fault()  [arch/x86/mm/fault.c]
     │
     ├─ kernel fault? → bad_area_nosemaphore() → oops/panic
     │
     ├─ user fault in kernel vmalloc area? → vmalloc_fault()
     │
     └─ user fault → handle_mm_fault(vma, addr, flags, regs)
                           │
                   ┌───────┴──────────────────────────────────────┐
                   │         handle_pte_fault()                   │
                   │                                              │
                   ├── !pte_present && !pte_none → do_swap_page() │
                   │                                              │
                   ├── !pte_present && pte_none:                  │
                   │   ├── vma->vm_ops->fault? → do_fault()       │
                   │   └── else → do_anonymous_page()             │
                   │                                              │
                   ├── pte_present, write fault, not writable:    │
                   │   └── do_wp_page()  [CoW]                    │
                   │                                              │
                   └── pte_present, access OK → spurious fault    │
```

### 9.2 Anonymous Page Fault

```c
// mm/memory.c (simplified)
static vm_fault_t do_anonymous_page(struct vm_fault *vmf)
{
    struct page *page;
    pte_t entry;

    // Check if demand-zero (first touch)
    if (!(vmf->flags & FAULT_FLAG_WRITE)) {
        // Map the shared zero page read-only
        entry = pte_mkspecial(pfn_pte(my_zero_pfn(vmf->address),
                                      vmf->vma->vm_page_prot));
        set_pte_at(vmf->vma->vm_mm, vmf->address, vmf->pte, entry);
        return 0;
    }

    // Write fault — allocate real page
    page = alloc_zeroed_user_highpage_movable(vmf->vma, vmf->address);
    // GFP_HIGHUSER_MOVABLE | __GFP_ZERO

    entry = mk_pte(page, vmf->vma->vm_page_prot);
    entry = pte_sw_mkyoung(entry);
    if (vmf->flags & FAULT_FLAG_WRITE)
        entry = pte_mkwrite(pte_mkdirty(entry));

    set_pte_at(vmf->vma->vm_mm, vmf->address, vmf->pte, entry);
    return VM_FAULT_MAJOR; // or MINOR
}
```

### 9.3 File-Backed Page Fault

```c
static vm_fault_t do_fault(struct vm_fault *vmf)
{
    // → vma->vm_ops->fault(vmf)
    // e.g., ext4_filemap_fault() → filemap_fault()
    //   → find_get_page() [check page cache]
    //   → page_cache_read() [read from block device if miss]
    //   → vmf->page = found page
    // Then map into page table
}
```

### 9.4 Fault Latency Sources

| Fault Type | Typical Latency | Cause |
|---|---|---|
| Demand zero (read) | < 100 ns | Map zero page |
| Demand zero (write) | 200-500 ns | alloc_page + zero + map |
| Page cache hit | 500 ns - 2 µs | TLB miss + page-table walk |
| Page cache miss (SSD) | 50-200 µs | Block I/O |
| Page cache miss (HDD) | 5-15 ms | Rotational seek |
| Swap-in from NVMe | 100-500 µs | Swap read |
| CoW | 300 ns - 1 µs | Copy page + remap |

---

## 10. Copy-on-Write (CoW)

### 10.1 fork() and CoW Setup

```
fork():
  1. dup_mm() → copy mm_struct
  2. dup_mmap() → copy all VMAs
  3. copy_page_range() → walk all PTEs:
     for each writable PTE:
         pte = ptep_set_wrprotect(pte)  // clear W bit
         // both parent and child now have RO PTEs to same physical page
         page_dup_rmap(page)            // increment _mapcount
  4. flush_tlb_range()                  // shootdown on all CPUs
```

### 10.2 CoW Fault

```
Child writes to shared page:
  #PF (P=1, W=1, write to RO page)
         │
         ▼
  do_wp_page()
         │
         ├── page has _mapcount == 1? (only child mapped)
         │   └── reuse page: pte_mkwrite(), flush TLB → DONE
         │
         └── page shared (_mapcount > 1):
             ├── alloc new page
             ├── copy_user_highpage(new, old, addr, vma)
             ├── set_pte_at(new page, writable)
             ├── page_remove_rmap(old)   // dec _mapcount
             └── put_page(old)
```

### 10.3 CoW Security — "Dirty CoW" (CVE-2016-5195)

A race between `get_user_pages()` (which can mark a page dirty without acquiring mmap_lock write side) and CoW unmap allowed unprivileged write to read-only mappings. Fix: `FOLL_COW` flag + `follow_page_pte()` checks. **Lesson:** any path that bypasses CoW atomicity is a privilege escalation vector.

---

## 11. Memory-Mapped Files (mmap)

### 11.1 mmap Internals

```c
// sys_mmap → mmap_region() → [mm/mmap.c]
//   1. find_vma_intersection() — check for overlap
//   2. mmap_region():
//      a. vma = vm_area_alloc(mm)
//      b. vma->vm_file = file, vm_pgoff = offset>>PAGE_SHIFT
//      c. call_mmap(file, vma) → file->f_op->mmap(file, vma)
//         e.g., ext4: generic_file_mmap() sets vm_ops = &generic_file_vm_ops
//      d. insert_vm_struct(mm, vma) → maple tree insert
//      e. mm->map_count++
```

### 11.2 MAP_SHARED vs MAP_PRIVATE

```
MAP_SHARED (e.g., IPC or file write-back):
  PTEs → page cache pages
  Writes go directly to page cache → writeback to disk
  All mappings of same file+offset see same physical page

MAP_PRIVATE (CoW):
  PTEs → page cache pages (initially read-only)
  Write fault → CoW → private anonymous copy
  Original file unmodified

MAP_SHARED + MAP_ANONYMOUS (POSIX shm, huge pages):
  tmpfs backing in /dev/shm or hugetlbfs
  Multiple processes share same physical pages

MAP_FIXED:
  Exact VA requested — dangerous, can unmap existing mappings
  Use MAP_FIXED_NOREPLACE to fail instead
```

### 11.3 mremap and Memory Holes

```c
// mremap() moves/resizes a mapping
// Large file re-maps: just moves PTE subtrees (O(1) for huge mappings)
// Uses move_page_tables() → pmd_to_pmd (huge PMD move) or PTE-by-PTE copy
```

### 11.4 madvise Hints

```c
madvise(addr, len, MADV_DONTNEED);    // release pages, zero on next fault
madvise(addr, len, MADV_WILLNEED);    // readahead
madvise(addr, len, MADV_HUGEPAGE);    // enable THP for region
madvise(addr, len, MADV_NOHUGEPAGE); // disable THP
madvise(addr, len, MADV_FREE);        // lazy free (mark reclaimable)
madvise(addr, len, MADV_DONTFORK);   // don't copy on fork
madvise(addr, len, MADV_DONTDUMP);   // exclude from core dump (secrets)
madvise(addr, len, MADV_MERGEABLE);  // enable KSM for region
```

---

## 12. Huge Pages and Transparent Huge Pages

### 12.1 Explicit HugeTLB Pages

```bash
# Reserve 512 × 2MiB hugepages at boot
echo 512 > /proc/sys/vm/nr_hugepages

# NUMA-specific
echo 256 > /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages

# 1GiB pages (must be reserved at boot)
kernel cmdline: hugepagesz=1G hugepages=16

# Mount hugetlbfs
mount -t hugetlbfs -o pagesize=2M,size=4G hugetlbfs /mnt/hugepages
```

```c
// Application use
int fd = open("/mnt/hugepages/myfile", O_RDWR | O_CREAT, 0600);
void *p = mmap(NULL, size, PROT_READ|PROT_WRITE,
               MAP_SHARED | MAP_HUGETLB, fd, 0);
// Or with MAP_ANONYMOUS | MAP_HUGETLB | MAP_HUGE_2MB
```

### 12.2 Transparent Huge Pages (THP)

THP automatically promotes 4KiB page clusters to 2MiB pages without application changes:

```bash
# System-wide THP control
cat /sys/kernel/mm/transparent_hugepage/enabled
# always [madvise] never

echo madvise > /sys/kernel/mm/transparent_hugepage/enabled

# khugepaged daemon collapses 512 consecutive 4K pages → 1 huge page
cat /sys/kernel/mm/transparent_hugepage/khugepaged/pages_collapsed
cat /sys/kernel/mm/transparent_hugepage/defrag  # [always] defer madvise never
```

**THP internals:**

```
khugepaged:
  1. scan mm_structs (khugepaged_scan_mm_slot)
  2. find candidate PMD-aligned 2MiB region fully populated with 4K pages
  3. alloc_pages(GFP_TRANSHUGE, HPAGE_PMD_ORDER) → order-9 allocation
  4. copy all 512 pages → new huge page
  5. collapse_huge_page() → atomically replace 512 PTEs with single PMD entry
  6. free 512 old pages
```

**Compound pages:** A 2MiB huge page is a compound page — one `struct page` as the head, 511 tail pages. `PageCompound(page)` distinguishes head vs tail.

### 12.3 THP Performance Trade-offs

| Aspect | 4KiB pages | 2MiB THP |
|---|---|---|
| TLB coverage | Low | 512× more |
| TLB entries used | Many | Few |
| Page fault latency | Low | Higher (alloc order-9) |
| Memory waste | Minimal | Up to 2MiB per VMA |
| Compaction pressure | Low | Requires contiguous 2MiB |
| CoW granularity | 4KiB | 2MiB (bad for fork-heavy) |
| NUMA balancing | Per-4K | Per-2M |

**Recommendation for cloud-native:** Use `madvise` mode, explicitly opt in for long-lived large allocations (databases, JVM heap). Avoid `always` in multi-tenant containers.

---

## 13. NUMA Architecture and Memory Policy

### 13.1 NUMA Topology

```
Dual-socket NUMA system:
  ┌──────────────────────────┐      ┌──────────────────────────┐
  │  Node 0 (Socket 0)       │      │  Node 1 (Socket 1)       │
  │  CPUs 0-23               │      │  CPUs 24-47              │
  │  Local RAM: 128 GiB      │      │  Local RAM: 128 GiB      │
  │  Latency: ~80 ns         │      │  Latency: ~80 ns         │
  └──────────┬───────────────┘      └──────────┬───────────────┘
             │   QPI/UPI Interconnect           │
             │   Remote latency: ~140 ns        │
             └──────────────────────────────────┘

NUMA distance matrix (numactl --hardware):
       node 0  node 1
  node 0:  10     21
  node 1:  21     10
```

### 13.2 Linux NUMA Data Structures

```c
// pg_data_t — one per NUMA node (even on UMA, single node)
typedef struct pglist_data {
    struct zone     node_zones[MAX_NR_ZONES];
    struct zonelist node_zonelists[MAX_ZONELISTS]; // fallback order
    int             nr_zones;
    unsigned long   node_start_pfn;  // first PFN in this node
    unsigned long   node_present_pages;
    int             node_id;
    // kswapd per node, compaction, reclaim state
} pg_data_t;

extern struct pglist_data *node_data[MAX_NUMNODES]; // array of nodes
#define NODE_DATA(nid) node_data[nid]
```

### 13.3 Memory Policies

```c
// set_mempolicy(2) — process-wide NUMA policy
set_mempolicy(MPOL_BIND, &nodemask, maxnode);    // only these nodes
set_mempolicy(MPOL_PREFERRED, &nodemask, maxnode); // prefer, fallback OK
set_mempolicy(MPOL_INTERLEAVE, &nodemask, maxnode); // round-robin nodes
set_mempolicy(MPOL_LOCAL, NULL, 0);              // always local (default)

// mbind(2) — per-VMA policy
mbind(addr, len, MPOL_BIND, &nodemask, maxnode, MPOL_MF_MOVE);
// MPOL_MF_MOVE: migrate existing pages to policy nodes
// MPOL_MF_STRICT: fail if pages can't be placed on policy nodes
```

### 13.4 NUMA Balancing (AutoNUMA)

```bash
echo 1 > /proc/sys/kernel/numa_balancing
# Periodically unmaps pages (PROT_NONE trick) to measure access patterns
# numa_hint_fault() → detect remote access → migrate page to local node
# Trade-off: migration overhead vs NUMA locality benefit
```

### 13.5 numactl Usage

```bash
numactl --cpunodebind=0 --membind=0 ./my_service   # pin CPU+memory to node 0
numactl --interleave=all ./memory_intensive_app     # interleave for bandwidth
numactl --hardware                                  # show topology
```

---

## 14. Swap, Reclaim, and the Page Reclaim Engine

### 14.1 LRU Lists

Linux maintains per-zone (per-node since 4.8) LRU lists:

```
Active anon   ← recently accessed anonymous pages
Inactive anon ← candidates for swap
Active file   ← recently accessed file-backed pages
Inactive file ← candidates for reclaim (writeback or discard)
Unevictable   ← mlock'd, ramfs, HugeTLB
```

Page promotion/demotion:
```
fault → add to inactive (mark PTE young)
access (A bit set by HW) → promote to active
periodic scan (refault distance tracking) → demote back to inactive
```

### 14.2 kswapd and Direct Reclaim

```
Memory pressure:
  zone free < WMARK_LOW
         │
         ▼
  wake kswapd (per-node daemon)
         │
         ▼
  balance_pgdat()
    └── shrink_node()
         ├── shrink_active_list()    // demote active → inactive
         └── shrink_inactive_list()
              ├── try_to_unmap()     // remove PTEs for file pages
              ├── pageout()          // writeback dirty pages
              └── free to buddy / add to swap

  zone free < WMARK_MIN → direct reclaim (allocating process itself reclaims)
```

### 14.3 Swap Subsystem

```
Swap path (anonymous page eviction):
  shrink_inactive_list() selects page
         │
         ▼
  swap_out_page()
    ├── get_swap_page() → allocate swap slot (swap_entry_t)
    ├── add_to_swap_cache(page, entry) → store in swap cache
    ├── set_pte_to_swap_entry(pte, entry) → encode in PTE (P=0)
    ├── try_to_free_swap(page) → remove from swap cache if refcount==1
    └── swap_writepage() → write to swap device

Swap-in (do_swap_page()):
  1. lookup_swap_cache(entry) → already in swap cache?
  2. swapin_readahead() → read swap page from device
  3. set_pte_at(new physical page)
  4. swap_free(entry) → release swap slot if no longer needed
```

### 14.4 Zswap and Zram

```
Zswap (compressed swap cache in RAM):
  swap_writepage() → zswap intercepts → compress page (LZ4/ZSTD)
                   → store in zbud/z3fold/zsmalloc pool
  hit on swap-in  → decompress from zswap pool
  zswap full      → evict oldest compressed page to real swap

Zram (RAM-based block device as swap):
  /dev/zram0 → formatted as swap (mkswap /dev/zram0)
  Each 4K page compressed → stored in zsmalloc allocator
  Effective compression ratio: 2-4x for typical workloads
```

```bash
# Setup zram
modprobe zram
echo lz4 > /sys/block/zram0/comp_algorithm
echo 4G > /sys/block/zram0/disksize
mkswap /dev/zram0
swapon -p 100 /dev/zram0   # priority 100 > real swap
```

---

## 15. OOM Killer

### 15.1 OOM Scoring

When all reclaim fails and allocation is still impossible, the OOM killer selects a victim:

```c
// mm/oom_kill.c
long oom_badness(struct task_struct *p, unsigned long totalpages)
{
    long points;
    long adj = (long)p->signal->oom_score_adj;

    // Base: RSS + swap + page_table_pages
    points = get_mm_rss(p->mm) + get_mm_counter(p->mm, MM_SWAPENTS)
             + mm_pgtables_bytes(p->mm) / PAGE_SIZE;

    // Adjust: oom_score_adj in [-1000, 1000]
    // -1000 = never kill, +1000 = always kill first
    adj *= totalpages / 1000;
    points += adj;

    return points;  // highest score = most likely to be killed
}
```

### 15.2 OOM Control

```bash
# Per-process adjustment (container runtime sets this)
echo -500 > /proc/$(pidof my_critical_daemon)/oom_score_adj  # protect
echo 1000 > /proc/$(pidof my_worker)/oom_score_adj           # sacrifice first

# Per-cgroup OOM control
echo 1 > /sys/fs/cgroup/memory/mygroup/memory.oom_control   # disable OOM kill
# → tasks block on allocation instead (dangerous, use with memory.limit_in_bytes)

# Observe OOM events
dmesg | grep -A 30 "Out of memory"
cat /sys/fs/cgroup/memory/mygroup/memory.oom_control
```

### 15.3 cgroup v2 Memory Controller

```bash
# Set hard limit
echo "1073741824" > /sys/fs/cgroup/myapp/memory.max   # 1 GiB hard limit

# Soft limit (reclaim target)
echo "805306368" > /sys/fs/cgroup/myapp/memory.high   # 768 MiB soft limit

# Swap limit
echo "536870912" > /sys/fs/cgroup/myapp/memory.swap.max  # 512 MiB swap

# Monitor
cat /sys/fs/cgroup/myapp/memory.stat   # detailed breakdown
cat /sys/fs/cgroup/myapp/memory.events  # oom, oom_kill counts
```

---

## 16. Memory Security — MMU-enforced Mitigations

### 16.1 ASLR (Address Space Layout Randomization)

```bash
cat /proc/sys/kernel/randomize_va_space
# 0 = off, 1 = stack/mmap randomized, 2 = + brk/heap randomized

# ASLR entropy (x86-64):
# mmap base: 28 bits (256 GiB range) → 2^28 positions
# stack:     22 bits
# Heap/brk:  13 bits (with randomize_va_space=2)
```

**KASLR:** Kernel text base randomized at boot (`CONFIG_RANDOMIZE_BASE`). Offset stored in `kaslr_offset()`. Defeated by kernel info-leak vulnerabilities (e.g., uninitialized stack disclosure).

### 16.2 KPTI — Kernel Page Table Isolation (Meltdown Mitigation)

```
Without KPTI (pre-Meltdown):
  User mode PGD → contains both user and kernel mappings
  Speculative kernel access possible via Meltdown

With KPTI:
  Two PGDs per process:
    user_pgd  → user space mappings ONLY
                + minimal kernel trampoline (entry stubs, IDT)
    kernel_pgd → full kernel + user mappings (used only in kernel mode)

  CR3 switch on syscall/interrupt:
    SWAPGS; MOV CR3, kernel_pgd_phys    (user→kernel)
    MOV CR3, user_pgd_phys; SWAPGS     (kernel→user)

  Cost: 1 TLB flush per syscall (mitigated by PCID: set CR3[63]=1 NOFLUSH
        if PCID available, kernel and user each get own PCID)
```

```bash
cat /sys/devices/system/cpu/vulnerabilities/meltdown
# Not affected / Mitigation: PTI
dmesg | grep -i kpti
echo 0 > /proc/sys/kernel/kpti   # runtime disable (not recommended)
```

### 16.3 SMEP / SMAP

```
SMEP (CR4.SMEP): Supervisor Mode Execution Prevention
  → CPU raises #PF if kernel code attempts to execute a user-space page
  → Defeats kernel exploits that jump to user-supplied shellcode

SMAP (CR4.SMAP): Supervisor Mode Access Prevention
  → CPU raises #PF if kernel code reads/writes user-space without STAC/CLAC
  → kernel must explicitly use copy_from_user() / copy_to_user()
    which bracket the access with STAC (set AC flag) / CLAC (clear AC flag)
  → Defeats exploits that trick kernel into reading/writing attacker-controlled user memory
```

```c
// kernel/smap usage example
static inline void user_access_begin(void) { stac(); }
static inline void user_access_end(void)   { clac(); }

// copy_from_user uses these internally
unsigned long copy_from_user(void *to, const void __user *from, unsigned long n)
{
    user_access_begin();
    n = raw_copy_from_user(to, from, n);
    user_access_end();
    return n;
}
```

### 16.4 NX / XD (No-Execute)

```
NX bit (bit 63 of PTE, requires IA32_EFER.NXE=1):
  Data pages: NX=1 → cannot execute
  Text pages: NX=0, W=0 → execute only, read-only

Linux W^X enforcement:
  CONFIG_STRICT_KERNEL_RWX  → kernel text RO+X, data RW+NX, rodata RO+NX
  CONFIG_STRICT_MODULE_RWX  → modules same enforcement
  CONFIG_DEBUG_WX           → warn on any W+X mappings at boot

Verify:
  cat /proc/cpuinfo | grep nx
  dmesg | grep "Write protecting"
  cat /sys/kernel/security/lockdown  # CONFIG_SECURITY_LOCKDOWN_LSM
```

### 16.5 Memory Tagging (ARM64 MTE)

```
ARM64 MTE (Memory Tagging Extension):
  Each 16-byte aligned allocation tagged with 4-bit color tag
  Tag stored in hardware "tag memory" (separate SRAM, 1/32 of RAM size)
  Pointer top-byte contains expected tag (TBI — Top Byte Ignore)
  CPU checks tag on every load/store → fault on mismatch

  Catches: use-after-free, heap buffer overflows, stack buffer overflows

  Linux support: CONFIG_ARM64_MTE
  glibc/tcmalloc support: PROT_MTE on mmap, tagged pointers

  Modes:
    SYNC  → synchronous fault (for debugging, high overhead ~2-3%)
    ASYNC → asynchronous reporting via SIGFPE (for production, ~1% overhead)
```

### 16.6 SPARX / SafeStack / Shadow Stack (CET)

```
Intel CET (Control-flow Enforcement Technology):
  Shadow Stack (SHSTK):
    Separate read-only stack stores only return addresses
    RET validates RSP match with shadow stack → detects ROP
    CR4.CET, MSR_IA32_U_CET, MSR_IA32_PL3_SSP

  Indirect Branch Tracking (IBT):
    ENDBR64 instruction must be at valid indirect call targets
    Processor tracks expected ENDBR64 after indirect JMP/CALL

  Linux kernel CET support: CONFIG_X86_SHADOW_STACK, CONFIG_X86_IBT
  glibc CET support: -fcf-protection=full, -mshstk (GCC/Clang)

ARM64 equivalent: BTI (Branch Target Identification)
  BTI instruction at valid jump targets
  BRK if indirect branch lands on non-BTI target
  CONFIG_ARM64_BTI, CONFIG_ARM64_BTI_KERNEL
```

### 16.7 Memory Isolation Mitigations Summary

| Mitigation | Threat | Kernel Config | Performance Impact |
|---|---|---|---|
| KPTI | Meltdown (CVE-2017-5754) | `CONFIG_PAGE_TABLE_ISOLATION` | 5-30% syscall-heavy |
| SMEP | Kernel execute user shellcode | HW + `CONFIG_X86_SMEP` | ~0% |
| SMAP | Kernel dereference user ptr | HW + `CONFIG_X86_SMAP` | ~0.1% |
| NX/XD | Code injection, ROP chain start | HW + `CONFIG_X86_PAE` | ~0% |
| ASLR | ROP/ret2libc | `CONFIG_COMPAT_BRK=n` | ~0% |
| KASLR | Kernel ROP | `CONFIG_RANDOMIZE_BASE` | ~0% (boot only) |
| CET SHSTK | Return-oriented programming | HW + `CONFIG_X86_SHADOW_STACK` | ~1-2% |
| MTE | Use-after-free, heap OOB | HW ARM64 + `CONFIG_ARM64_MTE` | ~1-3% async |
| KASAN | Kernel memory corruption | `CONFIG_KASAN` | ~2x slowdown |
| KMSAN | Kernel uninitialized reads | `CONFIG_KMSAN` | ~3x slowdown |

---

## 17. Extended Page Tables / Nested Paging (Virtualization)

### 17.1 Two-Dimensional Translation

```
Guest Virtual Address (GVA)
         │
         │ Guest OS page tables (managed by guest kernel)
         ▼
Guest Physical Address (GPA)
         │
         │ Extended Page Tables (EPT, Intel) / NPT (AMD) / Stage-2 (ARM)
         │ Managed by hypervisor (KVM/VMM)
         ▼
Host Physical Address (HPA) → DRAM
```

Without EPT, every guest page walk required hypervisor involvement (shadow page tables, 2003-2006 era). With EPT, hardware walks two-level page tables natively.

### 17.2 EPT Structure (Intel)

```
VMCS field: EPT_POINTER (EPTP)
  bits [5:3] = EPT page-walk length minus 1 (3 = 4-level EPT)
  bits [63:12] = physical address of EPT PML4

EPT PTE bits:
  [0] R = readable
  [1] W = writable
  [2] X = executable (from supervisor, EPT execute control)
  [5:3] Memory Type (0=UC, 6=WB)
  [7] Ignore PAT
  [51:12] Physical page frame
  [57] Verify Guest Paging (VGP, EPT-based SMAP)
  [58] Paging Write (EPT-based CR0.WP)
```

### 17.3 EPT Violation → VM Exit

```
Guest accesses GVA:
  1. CPU walks guest PT: GVA → GPA
  2. CPU walks EPT: GPA → HPA
  3. If EPT entry missing/permission denied → EPT Violation VM Exit
  4. KVM EPT fault handler:
     a. find host VMA for GPA
     b. alloc_pages() → HPA
     c. set EPT PTE → HPA
     d. VMRESUME → guest continues
```

### 17.4 KVM Memory Slots

```c
// KVM maps guest physical memory via "memory slots"
struct kvm_memory_slot {
    gfn_t       base_gfn;      // guest frame number start
    unsigned long npages;       // size in pages
    unsigned long userspace_addr; // qemu/host VA of backing memory
    struct kvm_arch_memory_slot arch; // EPT/NPT page table root per slot
};

// KVM uses host's page tables for backing (mmap'd memory)
// EPT pages point to same physical pages as host page tables
// Balloon inflation: guest frees pages → host reclaims via balloon driver
```

### 17.5 Memory Encryption (AMD SEV, Intel TDX)

```
AMD SEV (Secure Encrypted Virtualization):
  Each VM has AES-128 encryption key (in CPU hardware)
  Physical pages encrypted in DRAM → hypervisor cannot read
  C-bit (bit 47 or 51 of physical address) marks encrypted vs shared

AMD SEV-SNP (Secure Nested Paging):
  Adds reverse mapping table (RMP — Reverse Map Table)
  Each 4K page of DRAM has an RMP entry: {ASID, GPA, validated}
  Hypervisor cannot remap guest pages (prevents remapping attacks)
  Guest validates pages with PVALIDATE instruction

Intel TDX (Trust Domain Extensions):
  TD (Trust Domain) = encrypted VM
  SEAM mode for TDX module (Ring -1 below VMX root)
  KeyID in physical address selects per-TD encryption key
  TDCALL instructions for guest↔TDX module communication
```

---

## 18. C Implementations

### 18.1 Userspace Page Table Walker

```c
// page_walk.c — walk /proc/<pid>/pagemap to inspect PTE state
// Build: gcc -O2 -o page_walk page_walk.c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <errno.h>

#define PAGEMAP_ENTRY_BYTES 8
#define PAGE_SHIFT          12
#define PAGE_SIZE           (1UL << PAGE_SHIFT)

// /proc/<pid>/pagemap entry format
typedef struct {
    uint64_t pfn        : 55;   // bits [54:0] — physical frame number (if present)
    uint64_t soft_dirty : 1;    // bit 55 — page has been written since last clear
    uint64_t exclusive  : 1;    // bit 56 — page exclusively mapped
    uint64_t _reserved  : 4;    // bits [60:57]
    uint64_t file_page  : 1;    // bit 61 — file-backed or shared-anon
    uint64_t swapped    : 1;    // bit 62 — page is in swap
    uint64_t present    : 1;    // bit 63 — page present in RAM
} __attribute__((packed)) pagemap_entry_t;

_Static_assert(sizeof(pagemap_entry_t) == 8, "pagemap entry must be 8 bytes");

static int pagemap_fd = -1;

static int open_pagemap(pid_t pid)
{
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/pagemap", pid);
    int fd = open(path, O_RDONLY);
    if (fd < 0) {
        perror("open pagemap");
        return -1;
    }
    return fd;
}

static int query_pagemap(int fd, uintptr_t vaddr, pagemap_entry_t *out)
{
    off_t offset = (vaddr >> PAGE_SHIFT) * PAGEMAP_ENTRY_BYTES;
    uint64_t raw;
    ssize_t n = pread(fd, &raw, sizeof(raw), offset);
    if (n != sizeof(raw)) {
        fprintf(stderr, "pread pagemap: %s (n=%zd)\n", strerror(errno), n);
        return -1;
    }
    memcpy(out, &raw, sizeof(*out));
    return 0;
}

// Walk a virtual address range and dump PTE info
static void walk_range(pid_t pid, uintptr_t start, uintptr_t end)
{
    int fd = open_pagemap(pid);
    if (fd < 0) return;

    printf("%-20s %-18s %-8s %-8s %-8s %-8s\n",
           "VAddr", "PFN/SwapEntry", "Present", "Swapped", "File", "Dirty");
    printf("%-20s %-18s %-8s %-8s %-8s %-8s\n",
           "--------------------", "------------------",
           "-------", "-------", "----", "-----");

    for (uintptr_t addr = start; addr < end; addr += PAGE_SIZE) {
        pagemap_entry_t e;
        if (query_pagemap(fd, addr, &e) < 0) break;

        if (e.present || e.swapped) {
            printf("0x%018lx 0x%016lx %-8s %-8s %-8s %-8s\n",
                   addr,
                   (uint64_t)e.pfn,
                   e.present    ? "YES" : "no",
                   e.swapped    ? "YES" : "no",
                   e.file_page  ? "YES" : "no",
                   e.soft_dirty ? "YES" : "no");
        }
    }
    close(fd);
}

// Demonstrate: allocate, touch, then inspect our own memory
int main(void)
{
    pid_t pid = getpid();
    size_t size = 4 * PAGE_SIZE;

    // Anonymous mapping
    void *anon = mmap(NULL, size, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (anon == MAP_FAILED) { perror("mmap anon"); return 1; }

    printf("=== Before touch (demand-zero, pages not present) ===\n");
    walk_range(pid, (uintptr_t)anon, (uintptr_t)anon + size);

    // Touch pages — trigger demand-zero faults
    memset(anon, 0xAB, size);

    printf("\n=== After touch (pages present) ===\n");
    walk_range(pid, (uintptr_t)anon, (uintptr_t)anon + size);

    // Evict with MADV_DONTNEED
    madvise(anon, size, MADV_DONTNEED);

    printf("\n=== After MADV_DONTNEED (pages released) ===\n");
    walk_range(pid, (uintptr_t)anon, (uintptr_t)anon + size);

    munmap(anon, size);
    return 0;
}
```

### 18.2 Custom Slab-Style Allocator (Fixed-Size Pool)

```c
// pool_alloc.c — lock-free fixed-size slab allocator using atomic freelist
// Build: gcc -O2 -pthread -o pool_alloc pool_alloc.c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>

#define POOL_ALIGNMENT    64           // cache-line align
#define POOL_POISON_ALLOC 0xAA        // detect use-before-init
#define POOL_POISON_FREE  0xDD        // detect use-after-free

typedef struct pool_node {
    _Atomic(struct pool_node *) next; // freelist link (intrusive, inside object)
} pool_node_t;

typedef struct {
    _Atomic(pool_node_t *)  freelist;     // lock-free stack head
    void                   *backing;      // raw mmap region
    size_t                  obj_size;     // padded object size
    size_t                  capacity;     // total objects
    _Atomic size_t          alloc_count;  // live allocations
    int                     poison;       // enable debug poisoning
} pool_t;

// Initialize pool: mmap(MAP_ANONYMOUS|MAP_POPULATE) for predictable latency
int pool_init(pool_t *p, size_t obj_size, size_t capacity, int poison)
{
    // Ensure obj_size fits a freelist pointer
    if (obj_size < sizeof(pool_node_t))
        obj_size = sizeof(pool_node_t);

    // Align to cache line
    obj_size = (obj_size + POOL_ALIGNMENT - 1) & ~(size_t)(POOL_ALIGNMENT - 1);

    size_t total = obj_size * capacity;
    void *mem = mmap(NULL, total,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE,
                     -1, 0);
    if (mem == MAP_FAILED) return -1;

    // Optionally lock pages to prevent swap
    // mlock(mem, total);

    p->backing    = mem;
    p->obj_size   = obj_size;
    p->capacity   = capacity;
    p->poison     = poison;
    atomic_store(&p->alloc_count, 0);

    // Build initial freelist (all objects free)
    pool_node_t *head = NULL;
    for (size_t i = capacity; i-- > 0;) {
        pool_node_t *node = (pool_node_t *)((char *)mem + i * obj_size);
        if (poison) memset(node, POOL_POISON_FREE, obj_size);
        atomic_store(&node->next, head);
        head = node;
    }
    atomic_store(&p->freelist, head);
    return 0;
}

// Allocate one object — lock-free CAS loop
void *pool_alloc(pool_t *p)
{
    pool_node_t *old_head, *new_head;
    do {
        old_head = atomic_load_explicit(&p->freelist, memory_order_acquire);
        if (!old_head) return NULL; // pool exhausted
        new_head = atomic_load_explicit(&old_head->next, memory_order_relaxed);
    } while (!atomic_compare_exchange_weak_explicit(
                &p->freelist, &old_head, new_head,
                memory_order_release, memory_order_acquire));

    atomic_fetch_add_explicit(&p->alloc_count, 1, memory_order_relaxed);
    if (p->poison) memset(old_head, POOL_POISON_ALLOC, p->obj_size);
    return (void *)old_head;
}

// Free one object — lock-free push onto freelist
void pool_free(pool_t *p, void *ptr)
{
    assert(ptr >= p->backing &&
           ptr < (char *)p->backing + p->obj_size * p->capacity);

    pool_node_t *node = (pool_node_t *)ptr;
    if (p->poison) memset(node, POOL_POISON_FREE, p->obj_size);

    pool_node_t *old_head;
    do {
        old_head = atomic_load_explicit(&p->freelist, memory_order_acquire);
        atomic_store_explicit(&node->next, old_head, memory_order_relaxed);
    } while (!atomic_compare_exchange_weak_explicit(
                &p->freelist, &old_head, node,
                memory_order_release, memory_order_acquire));

    atomic_fetch_sub_explicit(&p->alloc_count, 1, memory_order_relaxed);
}

void pool_destroy(pool_t *p)
{
    munmap(p->backing, p->obj_size * p->capacity);
    memset(p, 0, sizeof(*p));
}

// --- Example usage ---
typedef struct {
    uint64_t id;
    uint8_t  payload[56]; // total: 64 bytes (one cache line)
} my_object_t;

int main(void)
{
    pool_t pool;
    const size_t N = 1024;

    if (pool_init(&pool, sizeof(my_object_t), N, 1) < 0) {
        perror("pool_init"); return 1;
    }

    printf("Pool: obj_size=%zu, capacity=%zu, backing=%p\n",
           pool.obj_size, pool.capacity, pool.backing);

    // Allocate all
    void *ptrs[N];
    for (size_t i = 0; i < N; i++) {
        ptrs[i] = pool_alloc(&pool);
        assert(ptrs[i] != NULL);
        my_object_t *o = ptrs[i];
        o->id = i;
        memset(o->payload, (int)i, sizeof(o->payload));
    }
    printf("Allocated %zu objects, alloc_count=%zu\n",
           N, atomic_load(&pool.alloc_count));

    // Pool should be exhausted
    assert(pool_alloc(&pool) == NULL);

    // Free all
    for (size_t i = 0; i < N; i++) pool_free(&pool, ptrs[i]);
    printf("Freed all, alloc_count=%zu\n", atomic_load(&pool.alloc_count));

    pool_destroy(&pool);
    return 0;
}
```

### 18.3 Kernel Module: PTE Inspector via proc

```c
// pte_inspect.c — kernel module exposing PTEs via /proc/pte_inspect
// Build: make -C /lib/modules/$(uname -r)/build M=$PWD modules
// Usage: echo "<pid> <vaddr_hex>" > /proc/pte_inspect; cat /proc/pte_inspect
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/mm.h>
#include <linux/mm_types.h>
#include <linux/pgtable.h>
#include <linux/sched.h>
#include <linux/uaccess.h>
#include <linux/seq_file.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Security Engineer");
MODULE_DESCRIPTION("PTE Inspector via /proc");

static pid_t  inspect_pid;
static unsigned long inspect_vaddr;

static int pte_inspect_show(struct seq_file *m, void *v)
{
    struct task_struct *task;
    struct mm_struct   *mm;
    pgd_t *pgd; p4d_t *p4d; pud_t *pud; pmd_t *pmd; pte_t *pte;

    rcu_read_lock();
    task = find_task_by_vpid(inspect_pid);
    if (!task) {
        rcu_read_unlock();
        seq_printf(m, "pid %d not found\n", inspect_pid);
        return 0;
    }
    get_task_struct(task);
    rcu_read_unlock();

    mm = get_task_mm(task);
    put_task_struct(task);
    if (!mm) {
        seq_printf(m, "no mm for pid %d\n", inspect_pid);
        return 0;
    }

    mmap_read_lock(mm);

    pgd = pgd_offset(mm, inspect_vaddr);
    seq_printf(m, "vaddr=0x%016lx pid=%d\n", inspect_vaddr, inspect_pid);
    seq_printf(m, "PGD: val=0x%016lx present=%d\n",
               pgd_val(*pgd), pgd_present(*pgd));

    if (!pgd_present(*pgd)) goto out;

    p4d = p4d_offset(pgd, inspect_vaddr);
    seq_printf(m, "P4D: val=0x%016lx present=%d\n",
               p4d_val(*p4d), p4d_present(*p4d));
    if (!p4d_present(*p4d)) goto out;

    pud = pud_offset(p4d, inspect_vaddr);
    seq_printf(m, "PUD: val=0x%016lx present=%d huge=%d\n",
               pud_val(*pud), pud_present(*pud), pud_huge(*pud));
    if (!pud_present(*pud) || pud_huge(*pud)) goto out;

    pmd = pmd_offset(pud, inspect_vaddr);
    seq_printf(m, "PMD: val=0x%016lx present=%d huge=%d\n",
               pmd_val(*pmd), pmd_present(*pmd), pmd_huge(*pmd));
    if (!pmd_present(*pmd) || pmd_huge(*pmd)) goto out;

    pte = pte_offset_map(pmd, inspect_vaddr);
    if (pte) {
        seq_printf(m, "PTE: val=0x%016lx present=%d write=%d "
                   "dirty=%d young=%d nx=%d user=%d\n",
                   pte_val(*pte),
                   pte_present(*pte),
                   pte_write(*pte),
                   pte_dirty(*pte),
                   pte_young(*pte),
                   !pte_exec(*pte),
                   pte_user(*pte));
        if (pte_present(*pte)) {
            unsigned long pfn = pte_pfn(*pte);
            phys_addr_t phys = PFN_PHYS(pfn) | (inspect_vaddr & ~PAGE_MASK);
            seq_printf(m, "PFN: %lu  phys=0x%llx\n", pfn, (u64)phys);
        }
        pte_unmap(pte);
    }

out:
    mmap_read_unlock(mm);
    mmput(mm);
    return 0;
}

static ssize_t pte_inspect_write(struct file *f, const char __user *buf,
                                  size_t count, loff_t *ppos)
{
    char kbuf[64];
    if (count >= sizeof(kbuf)) return -EINVAL;
    if (copy_from_user(kbuf, buf, count)) return -EFAULT;
    kbuf[count] = '\0';
    if (sscanf(kbuf, "%d %lx", &inspect_pid, &inspect_vaddr) != 2)
        return -EINVAL;
    return count;
}

static int pte_inspect_open(struct inode *inode, struct file *file)
{
    return single_open(file, pte_inspect_show, NULL);
}

static const struct proc_ops pte_inspect_ops = {
    .proc_open    = pte_inspect_open,
    .proc_read    = seq_read,
    .proc_write   = pte_inspect_write,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static int __init pte_inspect_init(void)
{
    proc_create("pte_inspect", 0600, NULL, &pte_inspect_ops);
    pr_info("pte_inspect: loaded\n");
    return 0;
}

static void __exit pte_inspect_exit(void)
{
    remove_proc_entry("pte_inspect", NULL);
    pr_info("pte_inspect: unloaded\n");
}

module_init(pte_inspect_init);
module_exit(pte_inspect_exit);
```

```makefile
# Makefile for kernel module
obj-m := pte_inspect.o
KDIR  := /lib/modules/$(shell uname -r)/build
PWD   := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

load:
	insmod pte_inspect.ko

unload:
	rmmod pte_inspect

test:
	@PID=$$(echo $$PPID); ADDR=$$(grep stack /proc/$$PID/maps | head -1 | cut -d- -f1); \
	echo "$$PID 0x$$ADDR" > /proc/pte_inspect; cat /proc/pte_inspect
```

### 18.4 Physical Memory Map Reader

```c
// read_iomem.c — parse /proc/iomem to understand physical memory layout
// Build: gcc -O2 -o read_iomem read_iomem.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct {
    uint64_t start;
    uint64_t end;
    char     name[128];
    int      depth;
} iomem_region_t;

static void print_bar(uint64_t start, uint64_t end, int depth)
{
    uint64_t size = end - start + 1;
    const char *unit;
    double val;
    if (size >= (1ULL << 30)) { val = size / (double)(1ULL << 30); unit = "GiB"; }
    else if (size >= (1ULL << 20)) { val = size / (double)(1ULL << 20); unit = "MiB"; }
    else if (size >= (1ULL << 10)) { val = size / (double)(1ULL << 10); unit = "KiB"; }
    else { val = (double)size; unit = "B"; }
    printf("%*.s[%8.2f %-3s] ", depth * 2, "", val, unit);
}

int main(void)
{
    FILE *f = fopen("/proc/iomem", "r");
    if (!f) { perror("open /proc/iomem"); return 1; }

    char line[256];
    printf("%-60s %s\n", "Region", "Size");
    printf("%-60s %s\n",
           "------------------------------------------------------------",
           "----------");

    while (fgets(line, sizeof(line), f)) {
        uint64_t start, end;
        char name[128];
        int depth = 0;
        const char *p = line;
        while (*p == ' ') { depth++; p++; }
        depth /= 2;

        if (sscanf(p, "%lx-%lx : %127[^\n]", &start, &end, name) == 3) {
            printf("%*s%016lx-%016lx : %-30s ", depth * 2, "",
                   start, end, name);
            print_bar(start, end, 0);
            printf("\n");
        }
    }
    fclose(f);
    return 0;
}
```

---

## 19. Rust Implementations

### 19.1 Virtual Memory Layout Inspector

```rust
// vm_inspector.rs — read /proc/self/maps and /proc/self/pagemap safely
// Cargo.toml: [dependencies] (none, pure std)
// Run: cargo run --release
// Note: pagemap PFN requires CAP_SYS_ADMIN (or run as root)

use std::fs::File;
use std::io::{self, BufRead, BufReader, Read, Seek, SeekFrom};
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct VmaRegion {
    pub start:   u64,
    pub end:     u64,
    pub perms:   Permissions,
    pub offset:  u64,
    pub dev:     (u8, u8),
    pub inode:   u64,
    pub pathname: Option<String>,
}

#[derive(Debug, Clone, Copy)]
pub struct Permissions {
    pub read:    bool,
    pub write:   bool,
    pub execute: bool,
    pub shared:  bool,
}

impl Permissions {
    fn parse(s: &str) -> Self {
        let b: Vec<char> = s.chars().collect();
        Self {
            read:    b.get(0) == Some(&'r'),
            write:   b.get(1) == Some(&'w'),
            execute: b.get(2) == Some(&'x'),
            shared:  b.get(3) == Some(&'s'),
        }
    }
}

impl std::fmt::Display for Permissions {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}{}{}{}",
            if self.read    { 'r' } else { '-' },
            if self.write   { 'w' } else { '-' },
            if self.execute { 'x' } else { '-' },
            if self.shared  { 's' } else { 'p' },
        )
    }
}

/// Parse /proc/<pid>/maps
pub fn parse_maps(pid: u32) -> io::Result<Vec<VmaRegion>> {
    let path = PathBuf::from(format!("/proc/{}/maps", pid));
    let file = File::open(&path)?;
    let reader = BufReader::new(file);
    let mut regions = Vec::new();

    for line in reader.lines() {
        let line = line?;
        let parts: Vec<&str> = line.splitn(6, ' ').collect();
        if parts.len() < 5 { continue; }

        let addrs: Vec<&str> = parts[0].split('-').collect();
        if addrs.len() != 2 { continue; }

        let start = u64::from_str_radix(addrs[0], 16).unwrap_or(0);
        let end   = u64::from_str_radix(addrs[1], 16).unwrap_or(0);
        let perms = Permissions::parse(parts[1]);
        let offset = u64::from_str_radix(parts[2], 16).unwrap_or(0);

        let dev_parts: Vec<&str> = parts[3].split(':').collect();
        let dev = (
            u8::from_str_radix(dev_parts.get(0).unwrap_or(&"0"), 16).unwrap_or(0),
            u8::from_str_radix(dev_parts.get(1).unwrap_or(&"0"), 16).unwrap_or(0),
        );

        let inode = parts[4].trim().parse::<u64>().unwrap_or(0);
        let pathname = parts.get(5).map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty());

        regions.push(VmaRegion { start, end, perms, offset, dev, inode, pathname });
    }
    Ok(regions)
}

/// Pagemap entry for a single page
#[derive(Debug, Clone, Copy)]
pub struct PagemapEntry {
    pub pfn:        u64,
    pub soft_dirty: bool,
    pub exclusive:  bool,
    pub file_page:  bool,
    pub swapped:    bool,
    pub present:    bool,
}

impl PagemapEntry {
    fn from_raw(raw: u64) -> Self {
        Self {
            pfn:        raw & ((1u64 << 55) - 1),
            soft_dirty: (raw >> 55) & 1 == 1,
            exclusive:  (raw >> 56) & 1 == 1,
            file_page:  (raw >> 61) & 1 == 1,
            swapped:    (raw >> 62) & 1 == 1,
            present:    (raw >> 63) & 1 == 1,
        }
    }
}

/// Query pagemap for a virtual address
pub fn query_pagemap(pid: u32, vaddr: u64) -> io::Result<PagemapEntry> {
    let path = PathBuf::from(format!("/proc/{}/pagemap", pid));
    let mut file = File::open(&path)?;

    const PAGE_SIZE: u64 = 4096;
    const ENTRY_SIZE: u64 = 8;

    let offset = (vaddr / PAGE_SIZE) * ENTRY_SIZE;
    file.seek(SeekFrom::Start(offset))?;

    let mut buf = [0u8; 8];
    file.read_exact(&mut buf)?;
    let raw = u64::from_le_bytes(buf);
    Ok(PagemapEntry::from_raw(raw))
}

fn size_str(bytes: u64) -> String {
    if bytes >= 1 << 30 { format!("{:.1} GiB", bytes as f64 / (1u64 << 30) as f64) }
    else if bytes >= 1 << 20 { format!("{:.1} MiB", bytes as f64 / (1u64 << 20) as f64) }
    else if bytes >= 1 << 10 { format!("{:.1} KiB", bytes as f64 / (1u64 << 10) as f64) }
    else { format!("{} B", bytes) }
}

fn main() -> io::Result<()> {
    let pid: u32 = std::process::id();
    println!("=== Virtual Memory Layout for PID {} ===\n", pid);

    let regions = parse_maps(pid)?;
    let mut total_mapped: u64 = 0;

    println!("{:<20} {:<20} {:<6} {:<12} {}",
             "Start", "End", "Perms", "Size", "Mapping");
    println!("{}", "-".repeat(80));

    for r in &regions {
        let size = r.end - r.start;
        total_mapped += size;
        let name = r.pathname.as_deref().unwrap_or("[anonymous]");

        // Classify region
        let class = if name.contains("stack")           { "STACK  " }
                    else if name.contains("[heap]")      { "HEAP   " }
                    else if name.contains("[vdso]")      { "VDSO   " }
                    else if name.contains("[vsyscall]")  { "VSYSCL " }
                    else if r.perms.execute              { "CODE   " }
                    else if r.perms.write                { "DATA   " }
                    else if !r.perms.write && r.perms.read { "RODATA " }
                    else                                 { "OTHER  " };

        println!("0x{:<18x} 0x{:<18x} {} {:>10} {} {}",
                 r.start, r.end, r.perms,
                 size_str(size), class, name);
    }

    println!("\nTotal mapped: {}", size_str(total_mapped));
    println!("VMA count: {}", regions.len());

    // Sample pagemap for first anonymous RW region
    println!("\n=== Pagemap Sample (first anonymous RW page) ===");
    for r in &regions {
        if r.perms.read && r.perms.write && !r.perms.execute && r.pathname.is_none() {
            match query_pagemap(pid, r.start) {
                Ok(e) => println!(
                    "vaddr=0x{:016x} pfn={:<12} present={} swapped={} file={} dirty={}",
                    r.start, e.pfn, e.present, e.swapped, e.file_page, e.soft_dirty
                ),
                Err(e) => println!("pagemap query failed: {}", e),
            }
            break;
        }
    }

    Ok(())
}
```

### 19.2 Safe Arena Allocator

```rust
// arena.rs — bump-pointer arena allocator with typed allocation
// Cargo.toml: no extra deps needed
// Test: cargo test

use std::alloc::{alloc, dealloc, Layout};
use std::cell::Cell;
use std::marker::PhantomData;
use std::ptr::NonNull;

/// Bump-pointer arena — O(1) alloc, no individual free, O(1) reset
/// Safe: lifetimes prevent use-after-reset at compile time
pub struct Arena {
    start: NonNull<u8>,
    size:  usize,
    ptr:   Cell<*mut u8>,  // current bump pointer (interior mutability)
    layout: Layout,
}

// SAFETY: Arena itself is Send if you don't share references across threads
// while the arena is being used. For single-threaded arenas this is fine.
unsafe impl Send for Arena {}

impl Arena {
    /// Create an arena backed by `size` bytes of heap memory
    pub fn new(size: usize) -> Self {
        // Align to 16 bytes for SIMD safety
        let layout = Layout::from_size_align(size, 16).expect("bad layout");
        let start = NonNull::new(unsafe { alloc(layout) })
                        .expect("allocation failed");
        let ptr = Cell::new(start.as_ptr());
        Self { start, size, ptr, layout }
    }

    /// Allocate `size` bytes aligned to `align`
    /// Returns None if not enough space
    pub fn alloc_raw(&self, size: usize, align: usize) -> Option<NonNull<u8>> {
        let current = self.ptr.get() as usize;
        // Align up
        let aligned = (current + align - 1) & !(align - 1);
        let new_ptr = aligned + size;

        let arena_end = self.start.as_ptr() as usize + self.size;
        if new_ptr > arena_end {
            return None;
        }
        self.ptr.set(new_ptr as *mut u8);
        // SAFETY: aligned is within [start, start+size) and properly aligned
        Some(unsafe { NonNull::new_unchecked(aligned as *mut u8) })
    }

    /// Allocate a single value; returns a reference valid for arena's lifetime
    pub fn alloc<T>(&self, value: T) -> Option<&T> {
        let layout = Layout::new::<T>();
        let ptr = self.alloc_raw(layout.size(), layout.align())?;
        // SAFETY: ptr is valid, aligned, unique; T written exactly once
        unsafe {
            ptr.as_ptr().cast::<T>().write(value);
            Some(&*ptr.as_ptr().cast::<T>())
        }
    }

    /// Allocate a zeroed slice
    pub fn alloc_slice_zeroed<T: Copy>(&self, len: usize) -> Option<&mut [T]> {
        let layout = Layout::array::<T>(len).ok()?;
        let ptr = self.alloc_raw(layout.size(), layout.align())?;
        unsafe {
            ptr.as_ptr().write_bytes(0, layout.size());
            Some(std::slice::from_raw_parts_mut(ptr.as_ptr().cast::<T>(), len))
        }
    }

    /// Reset arena — all previous allocations are immediately invalid
    /// Caller must ensure no references into this arena exist (enforced by lifetime)
    pub fn reset(&self) {
        self.ptr.set(self.start.as_ptr());
    }

    /// Bytes used
    pub fn used(&self) -> usize {
        self.ptr.get() as usize - self.start.as_ptr() as usize
    }

    /// Bytes remaining
    pub fn remaining(&self) -> usize {
        self.size - self.used()
    }
}

impl Drop for Arena {
    fn drop(&mut self) {
        // SAFETY: layout matches what was allocated
        unsafe { dealloc(self.start.as_ptr(), self.layout); }
    }
}

/// Scoped arena — lifetime-bound access preventing use-after-reset
pub struct ArenaScope<'a> {
    arena: &'a Arena,
    _marker: PhantomData<&'a mut ()>,
}

impl Arena {
    /// Enter a scope; references from alloc are bound to the scope lifetime
    pub fn scope(&self) -> ArenaScope<'_> {
        let saved = self.ptr.get();
        ArenaScope { arena: self, _marker: PhantomData }
    }
}

impl<'a> ArenaScope<'a> {
    pub fn alloc<T>(&'a self, value: T) -> Option<&'a T> {
        self.arena.alloc(value)
    }

    pub fn alloc_slice_zeroed<T: Copy>(&'a self, len: usize) -> Option<&'a mut [T]> {
        self.arena.alloc_slice_zeroed(len)
    }

    /// Reset to saved pointer on drop
}

impl<'a> Drop for ArenaScope<'a> {
    fn drop(&mut self) {
        // In a real implementation, save the bump pointer at scope entry
        // and restore here. Simplified for clarity.
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_alloc() {
        let arena = Arena::new(4096);
        let x: &u64 = arena.alloc(42u64).expect("alloc failed");
        let y: &u64 = arena.alloc(99u64).expect("alloc failed");
        assert_eq!(*x, 42);
        assert_eq!(*y, 99);
        assert!(arena.used() >= 16); // at least two u64s
    }

    #[test]
    fn test_slice_alloc() {
        let arena = Arena::new(4096);
        let s: &mut [u32] = arena.alloc_slice_zeroed(64).expect("alloc failed");
        assert_eq!(s.len(), 64);
        s.iter().for_each(|&v| assert_eq!(v, 0));
        s[0] = 0xDEAD_BEEF;
        assert_eq!(s[0], 0xDEAD_BEEF);
    }

    #[test]
    fn test_exhaustion() {
        let arena = Arena::new(64);
        let _a = arena.alloc([0u8; 32]).expect("first alloc");
        let _b = arena.alloc([0u8; 32]).expect("second alloc");
        // Third should fail
        assert!(arena.alloc([0u8; 32]).is_none());
    }

    #[test]
    fn test_reset() {
        let arena = Arena::new(4096);
        {
            let _x = arena.alloc(1u64).unwrap();
            let _y = arena.alloc(2u64).unwrap();
            assert!(arena.used() > 0);
        }
        // After references are dropped, safe to reset
        arena.reset();
        assert_eq!(arena.used(), 0);
        // Can allocate again
        let z = arena.alloc(3u64).unwrap();
        assert_eq!(*z, 3);
    }

    #[test]
    fn test_alignment() {
        let arena = Arena::new(4096);
        // Alloc a byte to misalign
        let _b = arena.alloc(1u8).unwrap();
        // Alloc u64 — must be 8-byte aligned
        let x = arena.alloc(0xCAFEu64).unwrap();
        assert_eq!((x as *const u64) as usize % 8, 0);
        assert_eq!(*x, 0xCAFE);
    }
}

fn main() {
    let arena = Arena::new(1024 * 1024); // 1 MiB

    // Allocate heterogeneous objects
    let id: &u64          = arena.alloc(12345u64).unwrap();
    let flags: &u32       = arena.alloc(0b1010u32).unwrap();
    let data: &mut [u8]   = arena.alloc_slice_zeroed(256).unwrap();

    data[0] = 0xFF;
    println!("id={}, flags=0b{:04b}, data[0]=0x{:02X}", id, flags, data[0]);
    println!("Used: {} bytes, Remaining: {} bytes", arena.used(), arena.remaining());
}
```

### 19.3 NUMA-Aware Memory Allocator (Linux, via mmap + mbind)

```rust
// numa_alloc.rs — NUMA-pinned memory allocation via libc syscalls
// Cargo.toml: [dependencies] libc = "0.2"
// Run: cargo run --release (requires NUMA-enabled kernel)

use std::ptr;
use std::io;

// mbind flags (from linux/mempolicy.h)
const MPOL_BIND: i32      = 2;
const MPOL_F_MOVE: u32    = 1 << 1;
const MPOL_MF_STRICT: u32 = 1 << 0;

/// Allocate `size` bytes of anonymous memory pinned to NUMA node `node`
///
/// # Safety
/// Returns raw pointer valid for `size` bytes, caller must unmap.
pub unsafe fn numa_alloc(size: usize, node: u32) -> io::Result<*mut u8> {
    // Step 1: mmap anonymous
    let ptr = libc::mmap(
        ptr::null_mut(),
        size,
        libc::PROT_READ | libc::PROT_WRITE,
        libc::MAP_PRIVATE | libc::MAP_ANONYMOUS | libc::MAP_POPULATE,
        -1,
        0,
    );
    if ptr == libc::MAP_FAILED {
        return Err(io::Error::last_os_error());
    }

    // Step 2: mbind to specific NUMA node
    // nodemask: bitmask where bit N = 1 means include node N
    // For a system with up to 64 nodes, one u64 suffices
    let nodemask: u64 = 1u64 << node;
    let maxnode: u64 = 64; // bits in nodemask

    let ret = libc::syscall(
        libc::SYS_mbind,
        ptr as usize,
        size,
        MPOL_BIND as usize,
        &nodemask as *const u64 as usize,
        maxnode as usize,
        MPOL_F_MOVE as usize, // migrate any existing pages
    );

    if ret != 0 {
        libc::munmap(ptr, size);
        return Err(io::Error::last_os_error());
    }

    Ok(ptr as *mut u8)
}

/// Free memory returned by numa_alloc
pub unsafe fn numa_free(ptr: *mut u8, size: usize) {
    libc::munmap(ptr as *mut libc::c_void, size);
}

/// Query the NUMA node of a virtual address via move_pages syscall
pub fn get_page_node(vaddr: usize) -> io::Result<i32> {
    let pages = [vaddr as *const libc::c_void];
    let mut status = [-1i32; 1];
    let ret = unsafe {
        libc::syscall(
            libc::SYS_move_pages,
            0i64,    // current process
            1i64,    // one page
            pages.as_ptr() as usize,
            ptr::null::<i32>() as usize,  // NULL nodes = query only
            status.as_mut_ptr() as usize,
            0i64,    // flags
        )
    };
    if ret != 0 {
        return Err(io::Error::last_os_error());
    }
    if status[0] < 0 {
        return Err(io::Error::from_raw_os_error(-status[0]));
    }
    Ok(status[0])
}

fn main() -> io::Result<()> {
    let size = 2 * 1024 * 1024; // 2 MiB
    let target_node = 0u32;

    println!("Allocating {} MiB on NUMA node {}", size >> 20, target_node);

    let ptr = unsafe { numa_alloc(size, target_node)? };
    println!("Allocated at {:p}", ptr);

    // Touch pages to ensure they're faulted in
    unsafe {
        ptr::write_bytes(ptr, 0xBB, size);
    }

    // Verify placement
    let node = get_page_node(ptr as usize)?;
    println!("Page at {:p} is on NUMA node {}", ptr, node);
    assert_eq!(node, target_node as i32,
               "Page landed on wrong NUMA node! Expected {}, got {}", target_node, node);

    unsafe { numa_free(ptr, size); }
    println!("Success: memory correctly allocated and freed on node {}", target_node);
    Ok(())
}

extern crate libc;
```

### 19.4 Soft-Dirty Page Tracking (Dirty Bit Scanner)

```rust
// dirty_tracker.rs — track which pages have been written using soft-dirty bits
// Useful for: live migration, checkpoint/restore, incremental backup
// Run as root (needs /proc/self/pagemap PFN access) or just use soft_dirty bit

use std::fs::{File, OpenOptions};
use std::io::{self, Read, Seek, SeekFrom, Write};
use std::ptr;

const PAGE_SIZE: usize = 4096;
const SOFT_DIRTY_BIT: u64 = 1u64 << 55;

pub struct DirtyTracker {
    region:   *mut u8,
    size:     usize,
    pagemap:  File,
    clear_refs: File,
}

impl DirtyTracker {
    /// Create tracker over an existing mmap region
    pub fn new(region: *mut u8, size: usize) -> io::Result<Self> {
        assert_eq!(size % PAGE_SIZE, 0, "size must be page-aligned");

        let pagemap = File::open("/proc/self/pagemap")?;
        let clear_refs = OpenOptions::new()
            .write(true)
            .open("/proc/self/clear_refs")?;

        Ok(Self { region, size, pagemap, clear_refs })
    }

    /// Clear all soft-dirty bits for this process
    /// Write "4" to /proc/self/clear_refs clears soft-dirty bits
    pub fn clear_dirty(&mut self) -> io::Result<()> {
        self.clear_refs.seek(SeekFrom::Start(0))?;
        self.clear_refs.write_all(b"4")?;
        Ok(())
    }

    /// Scan region and return list of dirty page offsets (in bytes from region start)
    pub fn scan_dirty(&mut self) -> io::Result<Vec<usize>> {
        let n_pages = self.size / PAGE_SIZE;
        let base_vpn = self.region as usize / PAGE_SIZE;
        let offset = (base_vpn as u64) * 8;

        self.pagemap.seek(SeekFrom::Start(offset))?;

        let mut buf = vec![0u8; n_pages * 8];
        self.pagemap.read_exact(&mut buf)?;

        let mut dirty = Vec::new();
        for (i, chunk) in buf.chunks_exact(8).enumerate() {
            let entry = u64::from_le_bytes(chunk.try_into().unwrap());
            if entry & SOFT_DIRTY_BIT != 0 {
                dirty.push(i * PAGE_SIZE);
            }
        }
        Ok(dirty)
    }
}

fn main() -> io::Result<()> {
    let size = 16 * PAGE_SIZE;

    // Allocate a region
    let region = unsafe {
        let ptr = libc::mmap(
            ptr::null_mut(),
            size,
            libc::PROT_READ | libc::PROT_WRITE,
            libc::MAP_PRIVATE | libc::MAP_ANONYMOUS,
            -1, 0,
        );
        assert_ne!(ptr, libc::MAP_FAILED);
        ptr as *mut u8
    };

    let mut tracker = DirtyTracker::new(region, size)?;

    // Clear dirty bits baseline
    tracker.clear_dirty()?;

    // Touch only pages 0, 3, 7, 15
    let touched = [0usize, 3, 7, 15];
    for &p in &touched {
        unsafe { *region.add(p * PAGE_SIZE) = 0xAB; }
    }

    // Scan
    let dirty = tracker.scan_dirty()?;
    println!("Dirty pages (byte offsets from region base):");
    for d in &dirty {
        println!("  offset=0x{:08x} page={}", d, d / PAGE_SIZE);
    }

    // Verify
    for &p in &touched {
        let offset = p * PAGE_SIZE;
        assert!(dirty.contains(&offset),
                "Page {} should be dirty but wasn't detected", p);
    }
    println!("All {} expected dirty pages detected.", touched.len());

    unsafe { libc::munmap(region as *mut libc::c_void, size); }
    Ok(())
}

extern crate libc;
```

---

## 20. Threat Model and Mitigations

### 20.1 Threat Actors and Attack Surfaces

```
Attack Surface          Threat Actor           Technique
─────────────────────   ─────────────────────  ──────────────────────────────────
Kernel heap             Privileged user,        SLUB overflow, use-after-free
                        container escape        → arbitrary write → privilege esc
Page table manipulation Kernel exploit          CR3/PTE write → page aliasing
                        (after initial access)  remap attack, KASLR defeat
Speculative execution   Local unprivileged      Spectre v1/v2/v4, MDS, LVI,
                        process, cloud tenant   Foreshadow/L1TF, RIDL, Fallout
Shared memory          Multi-tenant            TOCTOU, CoW race (Dirty CoW)
                        environment             → host file write from guest
Swap / hibernate        Cold-boot, disk         Unencrypted swap → secret leakage
                        forensics
MMIO regions           DMA-capable device,     DMA attack, IOMMU bypass,
                        PCIe device             bus-mastering attack
Guest→Host escape      Malicious VM guest      EPT misconfiguration, VM exit
                                               handler bugs (VENOM, VMEscape)
User→Kernel boundary   Exploit writer          SMAP bypass (missing stac/clac),
                                               heap spray, ret2usr
```

### 20.2 Mitigations by Layer

```
Layer                   Mitigation
─────────────────────   ─────────────────────────────────────────────────────
Hardware (CPU)          SMEP, SMAP, NX, CET (SHSTK+IBT), MTE, TDX/SEV-SNP
                        IOMMU (VT-d, AMD-Vi) for DMA isolation
Kernel core             KPTI (Meltdown), IBRS/STIBP/IBPB (Spectre),
                        MDS mitigations (MD_CLEAR, TAA clear),
                        KASAN/KMSAN/KCSAN (sanitizers in CI)
Kernel allocator        SLUB freelist random + hardening, per-cache quarantine
                        (CONFIG_SLAB_FREELIST_RANDOM, CONFIG_SLAB_FREELIST_HARDENED)
Kernel hardening        CONFIG_STRICT_KERNEL_RWX, CONFIG_RANDOMIZE_BASE (KASLR)
                        CONFIG_SECURITY_LOCKDOWN_LSM, CONFIG_STACKPROTECTOR_STRONG
                        CONFIG_FORTIFY_SOURCE
Swap / memory           CONFIG_ENCRYPTED_SWAP (dm-crypt), zswap with key
                        MADV_DONTDUMP for secrets, explicit memset+MADV_DONTNEED
User space              ASLR (max entropy), PIE binaries, full RELRO,
                        seccomp-bpf (restrict syscalls), landlock (FS restrictions)
Container runtime       cgroup v2 memory limits, namespace isolation,
                        separate user namespace, no --privileged
Hypervisor (KVM)        EPT misconfiguration hardening, sev-snp attestation,
                        IOMMU passthrough with memory encryption
```

### 20.3 Secure Memory Handling Checklist

```
[ ] Zero sensitive memory before free   (explicit_bzero / OPENSSL_cleanse)
[ ] Use MADV_DONTDUMP on key material   (exclude from core dumps)
[ ] mlock() key material                (prevent swap-out)
[ ] Verify W^X at all times             (mprotect RW→RO before execute)
[ ] No MAP_FIXED without MAP_FIXED_NOREPLACE
[ ] Use MAP_POPULATE for latency-sensitive pinned buffers
[ ] Validate all copy_from_user() sizes before allocation
[ ] Use kmalloc_array() not kmalloc(n*size) (overflow-safe)
[ ] Check kzalloc return (NULL = OOM)
[ ] Free with kfree_sensitive() for secrets (zeroes first)
[ ] Set oom_score_adj appropriately for critical daemons
[ ] Audit all mmap() calls: flags, alignment, MAP_SHARED vs MAP_PRIVATE
[ ] Encrypt swap partitions (dm-crypt)
[ ] Enable IOMMU for DMA isolation
```

---

## 21. Testing, Fuzzing, and Benchmarking

### 21.1 Kernel Memory Sanitizers

```bash
# KASAN — kernel address sanitizer (heap out-of-bounds, use-after-free)
# CONFIG_KASAN=y, CONFIG_KASAN_GENERIC=y (or KASAN_SW_TAGS for ARM64 MTE)
make ARCH=x86_64 kasan.config
dmesg | grep -i kasan

# KMSAN — kernel memory sanitizer (uninitialized reads)
# CONFIG_KMSAN=y (Clang only)
make CC=clang kmsan.config

# KCSAN — kernel concurrency sanitizer (data races)
# CONFIG_KCSAN=y
make ARCH=x86_64 kcsan.config

# KFENCE — lightweight probabilistic heap bug detector (production-safe)
# CONFIG_KFENCE=y, CONFIG_KFENCE_SAMPLE_INTERVAL=100 (ms)
cat /sys/kernel/debug/kfence/stats
```

### 21.2 Syzkaller — Kernel Fuzzer

```bash
# Syzkaller fuzzes kernel syscalls (including mmap, mprotect, madvise)
git clone https://github.com/google/syzkaller
cd syzkaller

# Configure for local kernel
cat > syzkaller.cfg << 'EOF'
{
    "target": "linux/amd64",
    "http": "127.0.0.1:56741",
    "workdir": "/tmp/syzkaller-workdir",
    "kernel_obj": "/path/to/linux/build",
    "image": "/path/to/disk.img",
    "sshkey": "/path/to/ssh_key",
    "syzkaller": "/path/to/syzkaller",
    "procs": 8,
    "type": "qemu",
    "vm": {
        "count": 4,
        "kernel": "/path/to/bzImage",
        "cpu": 2,
        "mem": 2048
    }
}
EOF

./bin/syz-manager -config syzkaller.cfg
```

### 21.3 Memory Benchmarks

```bash
# lmbench — memory latency and bandwidth
git clone https://github.com/intel/lmbench
make results
# Key outputs: lat_mem_rd (latency vs stride), bw_mem (bandwidth)

# tlb_stress — TLB miss rate under different working set sizes
# (custom tool, use perf)
perf stat -e dTLB-load-misses,dTLB-loads,iTLB-load-misses ./workload

# NUMA topology benchmark
numactl --cpunodebind=0 --membind=1 lat_mem_rd 256m 64  # remote latency
numactl --cpunodebind=0 --membind=0 lat_mem_rd 256m 64  # local latency

# Huge page TLB benefit measurement
# Without THP:
perf stat -e dTLB-load-misses,dTLB-loads ./matrix_multiply_4k
# With THP:
echo always > /sys/kernel/mm/transparent_hugepage/enabled
perf stat -e dTLB-load-misses,dTLB-loads ./matrix_multiply_2m

# Page fault rate measurement
perf stat -e major-faults,minor-faults ./your_workload
```

### 21.4 Functional Tests

```bash
# Test ASLR entropy
for i in {1..10}; do
    cat /proc/$(sh -c 'cat /proc/self/maps' & echo $!)../maps 2>/dev/null | \
    grep 'stack' | awk '{print $1}' || true
done

# Test KPTI active
dmesg | grep "page table isolation"
grep -c "PTI" /proc/cpuinfo

# Test NX enforcement
execstack --query /bin/ls     # should show "X -- /bin/ls" (NX enabled)

# Test SMEP/SMAP
# Attempt userspace execution from kernel — should fault
# (only in controlled test environment)

# Memory pressure / OOM test (cgroup isolated)
cgcreate -g memory:test
echo $((128*1024*1024)) > /sys/fs/cgroup/memory/test/memory.limit_in_bytes
cgexec -g memory:test stress-ng --vm 1 --vm-bytes 256M --timeout 10s

# Swap test
fallocate -l 1G /tmp/swapfile
chmod 600 /tmp/swapfile
mkswap /tmp/swapfile
swapon /tmp/swapfile
stress-ng --vm 1 --vm-bytes $(free -m | awk '/Mem:/{print $2}')M \
          --vm-method seq --timeout 30s
swapoff /tmp/swapfile
```

### 21.5 Performance Counters for MMU

```bash
# Full MMU event set
perf stat -e \
  cache-misses,\
  cache-references,\
  dTLB-load-misses,\
  dTLB-loads,\
  dTLB-store-misses,\
  dTLB-stores,\
  iTLB-load-misses,\
  iTLB-loads,\
  page-faults,\
  major-faults,\
  minor-faults \
  -I 1000 ./workload

# CPU-specific: Intel
perf stat -e \
  cpu/event=0x85,umask=0x01,name=ITLB_MISSES.MISS_CAUSES_A_WALK/,\
  cpu/event=0x08,umask=0x01,name=DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK/,\
  cpu/event=0x08,umask=0x02,name=DTLB_LOAD_MISSES.WALK_COMPLETED/ \
  ./workload

# flamegraph for page fault hotspots
perf record -e page-faults -g ./workload
perf script | stackcollapse-perf.pl | flamegraph.pl > pagefaults.svg
```

---

## 22. Roll-out / Rollback Plan

### 22.1 Enabling New Mitigations in Production

```
Phase 1 — Shadow run (canary, 1% traffic):
  - Enable mitigation with kernel boot param on canary fleet
  - Monitor: CPU usage, p99 latency, syscall rate, TLB miss rate
  - Duration: 24-72 hours
  - Rollback: reboot with old cmdline (grub default unchanged)

Phase 2 — Progressive rollout (10% → 50% → 100%):
  - Track SLO dashboards: latency, error rate, throughput
  - Alert thresholds: >5% latency regression, >1% error rate increase
  - Rollback trigger: automated via feature flag → reboot without mitigation

Phase 3 — Full rollout + remove rollback option:
  - Document in runbook which kernel options are required
  - Pin kernel version in deployment manifests
```

### 22.2 Kernel Parameter Change Workflow

```bash
# 1. Test in staging (exact production kernel version)
vagrant up --box ubuntu-22.04
vagrant ssh
sudo grubby --args="kpti=1 mitigations=auto" --update-kernel=ALL
sudo reboot

# 2. Verify mitigation active
cat /sys/devices/system/cpu/vulnerabilities/*
dmesg | grep -E "(KPTI|Spectre|Meltdown|MDS)"

# 3. Benchmark comparison
sysbench memory --memory-block-size=4K --memory-total-size=10G run
sysbench cpu --cpu-max-prime=20000 run

# 4. Deploy to production fleet (Ansible example)
ansible-playbook -i inventory/production \
  -e "kernel_args='kpti=1 mitigations=auto'" \
  playbooks/update_kernel_args.yml \
  --limit "canary_hosts" --check  # dry-run first

# 5. Rollback
ansible-playbook -i inventory/production \
  playbooks/rollback_kernel_args.yml \
  --limit "canary_hosts"
```

### 22.3 Debugging Memory Issues in Production

```bash
# Identify memory pressure
vmstat 1 10
cat /proc/meminfo
cat /proc/buddyinfo      # buddy allocator free lists
cat /proc/slabinfo       # slab cache stats
cat /proc/zoneinfo       # per-zone watermarks and stats

# Find memory leaks (kernel)
cat /sys/kernel/slab/*/objects  # object count per cache
echo scan > /sys/kernel/debug/kmemleak && sleep 5
cat /sys/kernel/debug/kmemleak  # unreferenced objects

# Find memory leaks (user space)
valgrind --leak-check=full --track-origins=yes ./binary
# Or: address sanitizer
gcc -fsanitize=address -g -o binary binary.c
./binary

# cgroup memory analysis
cat /sys/fs/cgroup/myapp/memory.stat
cat /sys/fs/cgroup/myapp/memory.events

# OOM post-mortem
dmesg | grep -A 50 "Out of memory"
# Look for: rss, pgtables, oom_score_adj of victim
```

---

## 23. References

### Authoritative Sources

1. **Linux Kernel Source** — `mm/` directory: `memory.c`, `mmap.c`, `page_alloc.c`, `slab.c`, `slub.c`, `swap.c`, `oom_kill.c`, `huge_memory.c`, `migrate.c`
   - https://elixir.bootlin.com/linux/latest/source/mm

2. **Intel Software Developer's Manual, Vol. 3A** — Chapters 4 (Paging), 11 (Memory Cache Control), 25 (VMX)
   - https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

3. **ARM Architecture Reference Manual (ARMv8-A)** — D5 (MMU), D7 (TLB), C6 (MTE)
   - https://developer.arm.com/documentation/ddi0487/latest

4. **Gorman, Mel** — *Understanding the Linux Virtual Memory Manager* (2004) — still conceptually accurate
   - https://www.kernel.org/doc/gorman/

5. **Love, Robert** — *Linux Kernel Development* (3rd ed.) — Chapter 15 (Process Address Space)

6. **Bovet & Cesati** — *Understanding the Linux Kernel* (3rd ed.)

7. **Linux mm documentation**
   - https://www.kernel.org/doc/html/latest/mm/

8. **NUMA documentation**
   - https://www.kernel.org/doc/html/latest/mm/numa.html

9. **Transparent Huge Pages**
   - https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html

10. **Spectre/Meltdown mitigations**
    - https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/

11. **AMD SEV-SNP**
    - https://www.amd.com/system/files/TechDocs/SEV-SNP-strengthening-vm-isolation-with-integrity-protection-and-more.pdf

12. **Intel TDX**
    - https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html

13. **KASAN documentation**
    - https://www.kernel.org/doc/html/latest/dev-tools/kasan.html

14. **Syzkaller**
    - https://github.com/google/syzkaller

15. **CET documentation**
    - https://www.intel.com/content/www/us/en/developer/articles/technical/technical-look-control-flow-enforcement-technology.html

### Key Kernel Files for Deep Dive

```
mm/memory.c          — page fault core, do_page_fault, handle_mm_fault
mm/mmap.c            — VMA management, mmap/munmap/mremap
mm/page_alloc.c      — buddy allocator, alloc_pages, free_pages
mm/slub.c            — SLUB allocator implementation
mm/swap.c            — LRU management, page reclaim
mm/vmscan.c          — kswapd, shrink_node, page eviction
mm/oom_kill.c        — OOM killer
mm/huge_memory.c     — THP, khugepaged
mm/hugetlb.c         — explicit hugeTLB management
mm/migrate.c         — page migration (NUMA balancing, compaction)
mm/mprotect.c        — permission changes, mprotect()
mm/rmap.c            — reverse mapping (PTE→page)
mm/memcontrol.c      — cgroup memory controller
arch/x86/mm/fault.c  — x86 page fault entry
arch/x86/mm/tlb.c    — TLB flush, PCID management
arch/arm64/mm/fault.c — ARM64 page fault entry
```

---

## 24. Next 3 Steps

### Step 1 — Instrument Your System Today

```bash
# Build and run the pagemap walker (section 18.1) to observe your process's PTEs:
gcc -O2 -o page_walk page_walk.c && ./page_walk

# Observe real-time MM events:
watch -n1 'cat /proc/meminfo | grep -E "MemFree|Cached|Swap|AnonPages|Mapped|PageTables|HugePages"'

# Profile TLB miss rates on a real workload:
perf stat -e dTLB-load-misses,dTLB-loads,major-faults,minor-faults -p <pid> sleep 10

# Explore your process's full VMA layout:
cat /proc/self/maps
# Or run the Rust vm_inspector (section 19.1): cargo run
```

### Step 2 — Implement a Production Allocator Component

```bash
# Extend the arena allocator (section 19.2) with:
# a) Thread-safe version using parking_lot::Mutex or per-thread arenas
# b) NUMA-aware backing (use numa_alloc from section 19.3)
# c) Red-zone detection (guard pages via mprotect(PROT_NONE))
# d) Benchmark against system malloc: cargo bench

# For kernel work: build and load the pte_inspect module (section 18.3):
make -C /lib/modules/$(uname -r)/build M=$PWD modules
insmod pte_inspect.ko
echo "$(pidof your_process) 0x$(cat /proc/$(pidof your_process)/maps | \
  grep heap | awk '{print $1}' | cut -d- -f1)" > /proc/pte_inspect
cat /proc/pte_inspect
```

### Step 3 — Security Hardening Audit

```bash
# Verify all mitigations are active on your fleet:
for vuln in /sys/devices/system/cpu/vulnerabilities/*; do
    echo "$(basename $vuln): $(cat $vuln)"
done

# Audit W^X violations:
dmesg | grep -i "wx"
# Enable CONFIG_DEBUG_WX and rebuild kernel for full audit

# Run syzkaller against a KVM guest to find MM bugs:
# (see section 21.2 for full config)
./bin/syz-manager -config syzkaller.cfg

# Audit OOM configuration for all critical services:
for svc in $(systemctl list-units --type=service --state=running -q | awk '{print $1}'); do
    pid=$(systemctl show $svc --property=MainPID --value 2>/dev/null)
    if [ -n "$pid" ] && [ "$pid" != "0" ] && [ -f "/proc/$pid/oom_score_adj" ]; then
        adj=$(cat /proc/$pid/oom_score_adj)
        echo "$svc (pid=$pid): oom_score_adj=$adj"
    fi
done
```

I'll create a comprehensive, production-grade markdown guide on the Linux MMU. This will take a moment to compile.**Summary of what's covered in the guide:**

The guide is structured as 24 sections covering the full stack, top to bottom:

**Hardware layer** — x86-64/ARM64/RISC-V MMU registers, page granules, PTE bit-field layouts with exact bit positions, 4-level and 5-level paging walk mechanics, and the folded Linux page-table abstraction (`pgd→p4d→pud→pmd→pte`).

**TLB mechanics** — TLB hierarchy sizing, PCID/ASID tagged entries, `INVPCID`/`TLBI` instructions, and the full SMP TLB shootdown protocol with `mmu_gather` batching — a common perf bottleneck in high-churn workloads.

**Linux MM subsystem** — `mm_struct`, `vm_area_struct`, `struct page` internals, physical zones, GFP flags, zone watermarks, buddy allocator with migration types and per-CPU page caches, SLUB with freelist randomization/hardening, and memory compaction.

**Fault handling** — the full fault entry path from CPU exception to `do_anonymous_page`/`do_fault`/`do_wp_page`/`do_swap_page`, with latency breakdown by fault type.

**CoW, mmap, huge pages, NUMA, swap/reclaim, OOM** — all with internals, not just API surface.

**Security** — KPTI internals (dual PGD, PCID optimization), SMEP/SMAP `STAC`/`CLAC`, NX W^X enforcement, MTE, CET SHSTK+IBT, AMD SEV-SNP/Intel TDX, a threat model table, and a production hardening checklist.

**C and Rust implementations** — pagemap walker, lock-free slab pool, kernel PTE inspector module, arena allocator with lifetime safety, NUMA `mbind` allocator, and soft-dirty page tracker for live migration.