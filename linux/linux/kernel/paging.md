# Paging: A Complete, In-Depth Guide
## From First Principles to Linux Kernel Internals, with C, Go, and Rust Implementations

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [First Principles: Why Paging Exists](#2-first-principles-why-paging-exists)
3. [Memory Addressing Fundamentals](#3-memory-addressing-fundamentals)
4. [Segmentation vs. Paging](#4-segmentation-vs-paging)
5. [Page Tables: Structure and Layout](#5-page-tables-structure-and-layout)
6. [x86-64 Paging in Depth](#6-x86-64-paging-in-depth)
7. [ARM64 Paging in Depth](#7-arm64-paging-in-depth)
8. [Translation Lookaside Buffer (TLB)](#8-translation-lookaside-buffer-tlb)
9. [Linux Kernel Paging Implementation](#9-linux-kernel-paging-implementation)
10. [Page Fault Handling](#10-page-fault-handling)
11. [Demand Paging and Lazy Allocation](#11-demand-paging-and-lazy-allocation)
12. [Copy-on-Write (CoW)](#12-copy-on-write-cow)
13. [Huge Pages and Transparent Huge Pages (THP)](#13-huge-pages-and-transparent-huge-pages-thp)
14. [NUMA and Paging](#14-numa-and-paging)
15. [Memory-Mapped Files (mmap)](#15-memory-mapped-files-mmap)
16. [Kernel Address Space Layout](#16-kernel-address-space-layout)
17. [KASLR, SMEP, SMAP, and Paging Security](#17-kaslr-smep-smap-and-paging-security)
18. [Spectre, Meltdown, and KPTI](#18-spectre-meltdown-and-kpti)
19. [Paging in Virtualization (EPT/NPT)](#19-paging-in-virtualization-eptnpt)
20. [Paging in Containers and Namespaces](#20-paging-in-containers-and-namespaces)
21. [Page Reclaim, Swapping, and the LRU](#21-page-reclaim-swapping-and-the-lru)
22. [C Implementations](#22-c-implementations)
23. [Go Implementations](#23-go-implementations)
24. [Rust Implementations](#24-rust-implementations)
25. [Threat Model and Mitigations](#25-threat-model-and-mitigations)
26. [Testing, Fuzzing, and Benchmarks](#26-testing-fuzzing-and-benchmarks)
27. [Production Tuning and Observability](#27-production-tuning-and-observability)
28. [Next 3 Steps](#28-next-3-steps)
29. [References](#29-references)

---

## 1. Executive Summary

Paging is the foundational memory management mechanism that gives every process its own isolated virtual address space, mapped by hardware to physical RAM through multi-level page tables. The Linux kernel implements a 5-level page table hierarchy (PGD→P4D→PUD→PMD→PTE) that the MMU walks on every cache miss, with the TLB caching recent translations. Paging enables demand loading, copy-on-write, memory overcommit, huge pages, and kernel isolation. Security-critical extensions — SMEP, SMAP, KPTI, NX bits, and PKU — are all enforced through page table entry flags. Extended Page Tables (EPT/NPT) in virtualization add a second translation layer. Understanding paging at bit-level precision is prerequisite knowledge for exploit development, hypervisor engineering, container isolation analysis, and kernel performance tuning.

---

## 2. First Principles: Why Paging Exists

### 2.1 The Problem Space

Before virtual memory, programs ran with direct physical addresses. This caused:

**Fragmentation**: Physical RAM becomes fragmented after allocations and frees. A 100 MB program might find no contiguous 100 MB block, even when 200 MB is free in scattered chunks.

**No isolation**: Process A could read or write Process B's memory at will. A buggy or malicious program could corrupt any other program or the kernel itself.

**No overcommit**: The sum of all running programs had to fit within physical RAM. No way to run more programs than RAM allows.

**No persistence optimization**: Loading an executable means copying its entire image into RAM even if only a few pages are ever touched.

**Relocation complexity**: Compilers and linkers needed to produce position-dependent binaries; loading at different addresses required patching every pointer — the relocation problem.

### 2.2 The Solution: Indirection via Virtual Addresses

The core insight is to introduce an indirection layer: programs use *virtual addresses* that the hardware translates to *physical addresses* at runtime through a data structure (the page table) under OS control.

```
CPU issues virtual address
        |
        v
    [ MMU + TLB ]
        |
        v
  Physical address in RAM
```

This indirection buys:

- **Isolation**: Each process has its own page table. Process A's virtual address 0x400000 maps to a different physical page than Process B's virtual address 0x400000.
- **Contiguity illusion**: Physically scattered pages appear contiguous to the process.
- **Overcommit**: Virtual address space is cheap (64-bit systems have 128 TB of user VA space). Physical pages are allocated on demand.
- **Protection**: Each page table entry carries permission bits (readable, writable, executable, user/kernel).
- **Sharing**: Multiple processes can map the same physical page (shared libraries, IPC).

### 2.3 Why Fixed-Size Pages (Not Segments)?

Early systems used segmentation (variable-size regions). Paging uses fixed-size chunks (pages, typically 4 KB). The tradeoffs:

| Property | Segmentation | Paging |
|----------|-------------|--------|
| Fragmentation | External (variable gaps) | Internal (last page partially used) |
| Hardware complexity | Simpler (base+limit) | More complex (multi-level walk) |
| Protection granularity | Per-segment | Per-page (4 KB) |
| Sharing | Natural (share a segment) | Via mapping same physical page |
| Swapping unit | Variable-size segment | Fixed 4 KB page |

Fixed-size pages eliminate external fragmentation: any free physical page frame can serve any virtual page request. The page size is a fundamental architectural constant — 4 KB on x86/ARM is driven by the observation that it minimizes internal fragmentation while keeping page table overhead reasonable.

### 2.4 The Fundamental Page Table Equation

Given a virtual address VA, the page table determines:

```
Physical Address (PA) = PFN << PAGE_SHIFT | VA & (PAGE_SIZE - 1)
```

Where:
- `PFN` = Page Frame Number (physical page index)
- `PAGE_SHIFT` = 12 (log2 of 4096)
- `VA & 0xFFF` = byte offset within the page (identical in VA and PA)

The page table maps VPN (Virtual Page Number = `VA >> 12`) to PFN.

---

## 3. Memory Addressing Fundamentals

### 3.1 Address Types in a Modern System

A production system deals with at least four distinct address spaces:

```
Virtual Address (VA)
    |
    | [MMU: page table walk]
    v
Linear/Physical Address (PA) — without IOMMU
    |
    | [IOMMU: device address translation]
    v
Bus/DMA Address — as seen by devices
```

In a virtualized environment:

```
Guest Virtual Address (GVA)
    |
    | [Guest MMU: guest page table]
    v
Guest Physical Address (GPA)
    |
    | [Host MMU: EPT/NPT]
    v
Host Physical Address (HPA)
```

### 3.2 Address Space Sizes

| Architecture | Virtual Address Bits | Canonical Range |
|-------------|---------------------|-----------------|
| x86-64 (4-level) | 48 bits | 0x0000_0000_0000_0000 – 0x0000_7FFF_FFFF_FFFF (user), 0xFFFF_8000_0000_0000 – 0xFFFF_FFFF_FFFF_FFFF (kernel) |
| x86-64 (5-level) | 57 bits | 0x0000_00FF_FFFF_FFFF_FFFF (user top), 0xFF00... (kernel) |
| ARM64 (4-level) | 48 bits | TTBR0 (user, 0 – 2^48), TTBR1 (kernel, high) |
| ARM64 (5-level) | 52 bits | LPA extension |
| RISC-V Sv39 | 39 bits | 3-level |
| RISC-V Sv48 | 48 bits | 4-level |

### 3.3 Canonical Addresses (x86-64)

x86-64 hardware requires bits [63:48] (or [63:57] for 5-level) to be identical to bit 47 (or 56). Any address that violates this is non-canonical and raises a #GP fault on access. This splits the address space into two "halves":

```
0x0000_0000_0000_0000  ─┐
         ...             │  User space (128 TB)
0x0000_7FFF_FFFF_FFFF  ─┘
         [hole]          ←  Non-canonical addresses (cause #GP)
0xFFFF_8000_0000_0000  ─┐
         ...             │  Kernel space (128 TB)
0xFFFF_FFFF_FFFF_FFFF  ─┘
```

### 3.4 Page Size Variants

| Page Size | Name | Levels Consumed | Use Case |
|-----------|------|-----------------|----------|
| 4 KB | Base page | All levels | General purpose |
| 2 MB | Huge page | PTE level collapsed | Database buffers, HPC |
| 1 GB | Gigantic page | PMD level collapsed | Hypervisors, huge datasets |
| 512 GB | (theoretical) | PUD collapsed | Not commonly used |

---

## 4. Segmentation vs. Paging

### 4.1 x86-64 Segmentation Legacy

x86 originally used segmentation (real mode: CS:IP, DS:SI, etc.) and extended it through protected mode (GDT/LDT with base+limit descriptors). In 64-bit long mode, segmentation is largely vestigial:

- CS, DS, ES, SS segment bases are forced to 0
- FS and GS retain non-zero bases (used for thread-local storage and per-CPU data)
- Limits are ignored (except for FS/GS in some configurations)

The effective address formula: `Linear = Segment.Base + Virtual`. With all segment bases = 0, `Linear == Virtual`.

```
; x86-64: read fs_base (thread pointer)
rdfsbase rax        ; requires FSGSBASE feature
; or via syscall: arch_prctl(ARCH_GET_FS, &addr)
```

Linux uses `FS.base` for the `pthread` TCB (thread control block), which stores `errno`, thread-local variables, and the stack canary. The kernel uses `GS.base` for `per_cpu` data.

### 4.2 Interaction: Segmentation Then Paging

The x86 pipeline in long mode:

```
Logical Address
(segment selector : offset)
        |
        | [Segmentation: add segment base — 0 in 64-bit mode]
        v
Linear Address (== Virtual Address in 64-bit)
        |
        | [Paging: MMU page table walk]
        v
Physical Address
```

### 4.3 Why Paging Won

Segmentation provides coarse-grained protection (per-segment) with complex management (GDT/LDT entries). Paging provides fine-grained (4 KB) uniform protection with a simpler hardware interface. Modern OS design layers all protection on paging and uses segmentation only as a thin compatibility layer.

---

## 5. Page Tables: Structure and Layout

### 5.1 Single-Level Page Table (Conceptual)

The simplest page table is a flat array indexed by VPN:

```
page_table[VPN] = PTE  (Page Table Entry containing PFN + flags)
```

For 32-bit addresses with 4 KB pages: 2^20 = 1M entries × 4 bytes = 4 MB per process. Wasteful, but workable.

For 64-bit: 2^52 entries × 8 bytes = 32 PB of page table per process. Totally impractical.

### 5.2 Multi-Level Page Tables

Split the VPN into multiple sub-fields, each indexing into a different level of tables. Only allocate table pages for the portions of the address space actually in use.

```
48-bit VA (4-level, 9-9-9-9-12 split):

 63      48 47    39 38    30 29    21 20    12 11       0
 ─────────┬────────┬────────┬────────┬────────┬──────────
  (sign)  │  PGD   │  P4D   │  PUD   │  PMD   │ PTE idx  │  Offset
          └────────┴────────┴────────┴────────┴──────────┘
            9 bits   9 bits   9 bits   9 bits   12 bits
```

Each level has 512 entries (2^9). Each entry is 8 bytes. Each table is exactly 4 KB = one physical page.

Walking the table:

```
PA = CR3                          # Physical base of PGD table
PA = PA[VA[47:39]] → PGD entry   # 512 possible entries
PA = entry.pfn << 12             # Base of P4D table
PA = PA[VA[38:30]] → P4D entry
PA = entry.pfn << 12             # Base of PUD table
PA = PA[VA[29:21]] → PUD entry
PA = entry.pfn << 12             # Base of PMD table  (or 1GB page if PS=1)
PA = PA[VA[20:12]] → PMD entry   # Base of PTE table  (or 2MB page if PS=1)
PA = PA[VA[11:0] ] → PTE entry
PA = entry.pfn << 12 | VA[11:0] # Physical address
```

Memory cost per process for a sparse 48-bit space: only the pages actually allocated for each level. A process using 100 MB might have:

- 1 PGD (4 KB)
- A few P4D pages
- ~50 PTE pages (~200 KB)
- Total: << 1 MB of page table overhead

### 5.3 Page Table Entry Format (x86-64)

```
Bit  63   : XD (Execute Disable / NX) — set = non-executable
Bits 62:52 : Available to OS / PKE (Protection Key)
Bit  51:M  : Reserved (must be 0), where M = MAXPHYADDR
Bits M-1:12: Physical Page Frame Number (PFN)
Bit  11    : Available to OS
Bit  10    : Available to OS  
Bit   9    : Available to OS
Bit   8    : G (Global) — don't flush TLB on CR3 switch
Bit   7    : PS (Page Size) — at PUD/PMD level: 1GB/2MB page
Bit   6    : D (Dirty) — set by CPU on write
Bit   5    : A (Accessed) — set by CPU on read/write
Bit   4    : PCD (Page Cache Disable)
Bit   3    : PWT (Page Write-Through)
Bit   2    : U/S (User/Supervisor) — 0=kernel only, 1=user accessible
Bit   1    : R/W (Read/Write) — 0=read-only, 1=writable
Bit   0    : P (Present) — 0=not present (triggers page fault)
```

In diagram form:

```
 63  62   59 58  52 51          12 11  9  8  7  6  5  4  3  2  1  0
 ┌───┬──────┬──────┬──────────────┬─────┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
 │XD │ PKE  │ AVAIL│     PFN      │AVAIL│ G│PS│ D│ A│CD│WT│US│RW│ P│
 └───┴──────┴──────┴──────────────┴─────┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
```

### 5.4 Protection Key (PKU/PKE)

Bits [62:59] of a PTE on modern x86-64 (Icelake+) hold a 4-bit protection key index (0–15). The `PKRU` register (user-mode) or `PKRS` (supervisor) holds a 32-bit bitmap of {WD, AD} for each of 16 keys. This allows per-page-group access control without modifying page tables — useful for implementing memory-safe partitions within a single process (like `pkey_mprotect`).

```
PKRU register: bits [2k+1:2k] for key k
  bit 2k+1 = WD (write disable)
  bit 2k   = AD (access disable)
```

---

## 6. x86-64 Paging in Depth

### 6.1 Control Registers

| Register | Purpose |
|----------|---------|
| CR0.PG (bit 31) | Enable paging |
| CR0.WP (bit 16) | Write Protect — kernel respects R/W bit even in ring 0 |
| CR3 | Physical address of current PGD (+ PCID in bits [11:0] if CR4.PCIDE=1) |
| CR4.PAE | Physical Address Extension — must be set for 64-bit paging |
| CR4.PGE | Global Page Enable — G-bit pages not flushed on CR3 write |
| CR4.SMEP | Supervisor Mode Execution Prevention |
| CR4.SMAP | Supervisor Mode Access Prevention |
| CR4.PKE | Protection Key Enable (user) |
| CR4.PKS | Protection Key Enable (supervisor) |
| CR4.LA57 | Enable 5-level paging (57-bit VA) |
| EFER.NXE | Enable NX/XD bit in PTEs |

### 6.2 CR3 and PCID

CR3 holds the physical address of the PGD. Context switches write CR3, invalidating TLB entries for the old process unless `CR4.PCIDE=1` (Process-Context IDentifier). With PCID:

```
CR3 layout with PCID:
Bit 63     : NOFLUSH — if 1, don't flush TLB on this CR3 write
Bits 11:0  : PCID (12 bits, 0–4095)
Bits 51:12 : Physical address of PGD (shifted right 12)
```

PCIDs allow the TLB to hold entries from multiple address spaces simultaneously, tagged by PCID. This dramatically reduces TLB flush overhead on context switch — critical for KPTI performance.

### 6.3 5-Level Paging (LA57)

Enabled via `CR4.LA57`. Adds a 5th level (PGD becomes PML5, old PGD becomes PML4):

```
57-bit VA (5-level, 9-9-9-9-9-12 split):

 63    57 56    48 47    39 38    30 29    21 20    12 11       0
 ──────┬─────────┬────────┬────────┬────────┬────────┬──────────
(sign) │  PML5   │  PML4  │  PDP   │   PD   │   PT   │  Offset
       └─────────┴────────┴────────┴────────┴────────┴──────────
         9 bits    9 bits   9 bits   9 bits   9 bits   12 bits
```

Extends user VA space from 128 TB to 64 PB. Required for workloads needing > 128 TB of address space (large in-memory databases, HPC). Linux supports it since 4.12.

### 6.4 Inverted Page Tables (Alternative)

IBM POWER and some RISC architectures use inverted page tables: one entry per physical page, not per virtual page. VPN is hashed to find the entry. Advantage: table size proportional to physical RAM, not virtual space. Disadvantage: requires hash collision resolution, harder to implement TLB miss handlers efficiently in software. x86-64 uses hardware-walked radix page tables.

### 6.5 The Hardware Page Table Walk in Detail

On a TLB miss, the CPU's Memory Management Unit (MMU) performs the walk in hardware on x86-64:

```
1. Load CR3 → physical base of PML4 (or PML5)
2. Extract VA[47:39] → index into PML4 (512 entries × 8 bytes = 4 KB)
3. Load PML4E; check P=1, else #PF
4. Extract VA[38:30] → index into PDPT
5. Load PDPTE; check P=1, PS=0 (if PS=1 → 1GB page, stop here)
6. Extract VA[29:21] → index into PD
7. Load PDE; check P=1, PS=0 (if PS=1 → 2MB page, stop here)
8. Extract VA[20:12] → index into PT
9. Load PTE; check P=1
10. Set A bit in all traversed entries; set D bit if write
11. Check permission bits (U/S, R/W, XD) vs access type and CPL
12. PA = PTE.PFN << 12 | VA[11:0]
13. Load TLB with (VA >> 12) → PA, protection summary
```

Permission check failures raise #PF with error code bits:
- Bit 0: P (0 = not-present fault, 1 = protection violation)
- Bit 1: W (0 = read, 1 = write)
- Bit 2: U (0 = kernel, 1 = user mode)
- Bit 3: RSVD (reserved bit set in PTE — indicates corrupt page table)
- Bit 4: I/D (1 = instruction fetch)
- Bit 5: PK (protection key violation)

### 6.6 Physical Address Extension (PAE)

On 32-bit x86 with `CR4.PAE=1`, PTEs are 64-bit (allowing 52-bit physical addresses). The table structure is 2-9-9-12: PDPT (4 entries in CR3), PD, PT. Linux uses this to support up to 64 GB RAM on 32-bit systems (HIGHMEM). This is now legacy — all modern Linux deployments use 64-bit mode.

---

## 7. ARM64 Paging in Depth

### 7.1 Two Translation Regimes

ARM64 has two independent page table base registers:

- `TTBR0_EL1`: User space (VA bit 55 = 0 selects TTBR0)
- `TTBR1_EL1`: Kernel space (VA bit 55 = 1 selects TTBR1)

This eliminates the need for a kernel/user split within one page table — the hardware selects the right table based on the top VA bit. This is conceptually cleaner than x86's single CR3.

### 7.2 Translation Control Register (TCR_EL1)

`TCR_EL1` configures each translation regime:

```
TCR_EL1 fields:
  T0SZ[5:0]   : 64 - size of user VA in bits (e.g., 25 for 39-bit, 16 for 48-bit)
  T1SZ[21:16] : 64 - size of kernel VA in bits
  TG0[15:14]  : TTBR0 granule (00=4K, 01=64K, 10=16K)
  TG1[31:30]  : TTBR1 granule
  IRGN0       : Inner cacheability for TTBR0 walks
  ORGN0       : Outer cacheability
  SH0         : Shareability
  EPD0        : Disable translation for TTBR0
  A1          : ASID in TTBR0 or TTBR1
  IPS[34:32]  : Intermediate physical address size
```

### 7.3 ARM64 Page Table Entry Format

```
Bit 63    : IGNORED / UXN (Unprivileged Execute Never)
Bit 54    : PXN (Privileged Execute Never)  
Bit 53    : Contiguous (hint: 16 contiguous pages use one TLB entry)
Bit 52    : DBM (Dirty Bit Management)
Bits 51:48: Upper block attributes
Bits 47:12: Output address (OA) / next level table address
Bits 11:2 : Lower block attributes
  Bit 11  : nG (not Global) — ASID-tagged if 1
  Bit 10  : AF (Access Flag) — fault if 0 on first access
  Bits 9:8: SH (Shareability: 00=Non, 10=Outer, 11=Inner)
  Bits 7:6: AP (Access Permissions): 00=EL1 RW, 01=EL0+EL1 RW, 10=EL1 RO, 11=EL0+EL1 RO
  Bit  5  : NS (Non-Secure)
  Bits 4:2: AttrIdx (index into MAIR_EL1 — memory attribute)
  Bits 1:0: 00=Invalid, 01=Block(L1/L2), 11=Table/Page
```

### 7.4 ASID (Address Space ID)

ARM64 uses ASIDs (8 or 16 bit) to tag TLB entries. Like PCIDs on x86-64, this avoids full TLB flushes on context switch. The ASID lives in bits [63:48] of TTBR0/TTBR1. `TLBI ASIDE1IS` flushes only entries with a specific ASID.

### 7.5 Memory Attributes (MAIR)

MAIR_EL1 is an 8-slot attribute register. Each 8-bit slot defines:

```
MAIR_EL1 slot:
  Bits 7:4 : Outer attributes (cache policy for outer cache)
  Bits 3:0 : Inner attributes

Examples:
  0xFF : Normal, Inner WB/WA, Outer WB/WA (typical for RAM)
  0x00 : Device-nGnRnE (strongly ordered, no reordering — MMIO)
  0x44 : Normal, Inner NC, Outer NC (non-cacheable)
```

AttrIdx in the PTE selects which of the 8 MAIR slots applies. This is how ARM distinguishes device memory (MMIO) from normal RAM in the page tables — critical for correct memory ordering on peripherals.

---

## 8. Translation Lookaside Buffer (TLB)

### 8.1 TLB Architecture

The TLB is a small, fast, fully-associative or set-associative cache storing recent VA→PA translations. Without it, every memory access requires 4–5 additional memory accesses for the page table walk — an unacceptable overhead.

```
Modern x86-64 TLB hierarchy (example: Intel Ice Lake):

L1 DTLB: 64 entries, 4-way, 4K pages
          8 entries, fully-associative, 2MB pages
L1 ITLB: 128 entries, 8-way, 4K pages
STLB   : 2048 entries, 12-way, 4K + 2MB pages (shared data+instruction)
L2 TLB : (some microarchitectures have a larger unified L2 TLB)
```

TLB hit latency: 1 cycle (L1), ~6 cycles (STLB).
TLB miss (page walk): 10–50+ cycles, depending on whether page table pages are in L1/L2/L3 cache.

### 8.2 TLB Shootdown

When one CPU modifies a page table entry (e.g., on `munmap`, `mprotect`, CoW break), all other CPUs that might have cached the old translation must invalidate their TLB entries. This is called a **TLB shootdown**.

Mechanism on x86-64:
1. CPU A modifies PTE (clears P bit or changes PFN)
2. CPU A sends IPI (Inter-Processor Interrupt) to all CPUs sharing this address space
3. Each remote CPU executes `INVLPG <va>` in its IPI handler (or `MOV CR3, CR3` for full flush)
4. Remote CPUs signal completion
5. CPU A proceeds

TLB shootdowns are expensive (IPI latency × number of CPUs). Linux optimizes with lazy TLB (delaying flushes for processes not currently running) and batch flushes.

### 8.3 TLB Invalidation Instructions

**x86-64**:
```asm
INVLPG <va>           ; Invalidate single VA in all TLBs (local)
MOV CR3, <cr3>        ; Full TLB flush (except Global pages)
MOV CR3, CR3          ; Same, self-flush
INVPCID type, desc    ; Fine-grained PCID-aware invalidation
  ; type 0: single VA in PCID
  ; type 1: all non-global in PCID
  ; type 2: all non-global, all PCIDs
  ; type 3: all, including global
```

**ARM64**:
```asm
TLBI VMALLE1IS        ; Invalidate all EL1, Inner Shareable
TLBI VAE1IS, <va>     ; Invalidate single VA, EL1, Inner Shareable
TLBI ASIDE1IS, <asid> ; Invalidate all entries with ASID
DSB ISH               ; Data Sync Barrier (ensure stores visible)
ISB                   ; Instruction Sync Barrier
```

### 8.4 Global Pages

PTEs with the G bit set (kernel mappings) are not flushed on CR3 writes (context switches). This avoids re-walking kernel page tables on every context switch. Linux marks all kernel page tables with G=1 (unless KPTI is enabled — see §18).

### 8.5 TLB Performance Impact

TLB coverage depends on page size:

```
With 4 KB pages and 64-entry L1 DTLB:
  Coverage = 64 × 4 KB = 256 KB

With 2 MB pages and 8-entry L1 DTLB:
  Coverage = 8 × 2 MB = 16 MB

With 1 GB pages and 4-entry L1 DTLB:
  Coverage = 4 × 1 GB = 4 GB
```

This is why huge pages dramatically improve performance for large working sets — they increase TLB reach. A database buffer pool of 64 GB covered by 4 KB pages would need 16M TLB entries; covered by 1 GB pages it needs 64.

---

## 9. Linux Kernel Paging Implementation

### 9.1 Linux Page Table Abstraction

Linux abstracts the hardware page table hierarchy into up to 5 levels, compile-time configured:

```c
// include/linux/pgtable.h
pgd_t   *pgd;    // Page Global Directory      (always present)
p4d_t   *p4d;    // Page 4th level Directory   (may be folded into pgd)
pud_t   *pud;    // Page Upper Directory       (may be folded)
pmd_t   *pmd;    // Page Middle Directory      (may be folded)
pte_t   *pte;    // Page Table Entry
```

"Folded" means a level is eliminated at compile time when the hardware doesn't need it. For a 3-level architecture, P4D and PUD might be folded, making `pgd == p4d` and `pud == pgd`.

### 9.2 Core Types

```c
// arch/x86/include/asm/pgtable_types.h
typedef struct { pgdval_t pgd; } pgd_t;
typedef struct { p4dval_t p4d; } p4d_t;
typedef struct { pudval_t pud; } pud_t;
typedef struct { pmdval_t pmd; } pmd_t;
typedef struct { pteval_t pte; } pte_t;

typedef unsigned long pgdval_t;  // 64-bit PTE value

// Protection bits
typedef struct { pgprotval_t pgprot; } pgprot_t;
#define pgprot_val(x)     ((x).pgprot)
#define __pgprot(x)       ((pgprot_t) { (x) })
```

### 9.3 Key Accessor Macros

```c
// Walking the page table from mm_struct
pgd = pgd_offset(mm, address);          // Get PGD entry for address
p4d = p4d_offset(pgd, address);         // Get P4D entry
pud = pud_offset(p4d, address);         // Get PUD entry
pmd = pmd_offset(pud, address);         // Get PMD entry
pte = pte_offset_map(pmd, address);     // Get PTE (may kmap on 32-bit)

// Test entry states
pgd_none(*pgd)    // True if entry is empty (P=0, not allocated)
pgd_bad(*pgd)     // True if entry is corrupt
pgd_present(*pgd) // True if present
pte_present(*pte) // True if P=1
pte_write(*pte)   // True if R/W=1
pte_dirty(*pte)   // True if D=1
pte_young(*pte)   // True if A=1 (Accessed)
pte_exec(*pte)    // True if NX=0 (executable)
pte_user(*pte)    // True if U/S=1

// PTE construction
mk_pte(page, pgprot)          // Create PTE from struct page + pgprot
pte_mkwrite(pte)              // Set R/W bit
pte_mkdirty(pte)              // Set D bit
pte_mkyoung(pte)              // Set A bit
pte_wrprotect(pte)            // Clear R/W bit (for CoW)
pte_mkold(pte)                // Clear A bit (for LRU aging)
pte_pfn(*pte)                 // Extract PFN from PTE
```

### 9.4 mm_struct and Virtual Memory Areas (VMAs)

Each process has an `mm_struct`:

```c
struct mm_struct {
    struct maple_tree  mm_mt;      // VMA tree (maple tree since 6.1, was rb-tree)
    unsigned long      mmap_base;  // Start of mmap region
    unsigned long      task_size;  // User address space limit
    pgd_t             *pgd;        // Physical PGD (page table root)
    atomic_t           mm_users;   // Users sharing this mm (threads)
    atomic_t           mm_count;   // Kernel references
    
    unsigned long      start_code, end_code;   // .text segment
    unsigned long      start_data, end_data;   // .data segment
    unsigned long      start_brk,  brk;        // Heap
    unsigned long      start_stack;            // Stack top
    
    struct list_head   mmlist;     // List of all mm_structs
    // ... NUMA policy, RSS counters, locks ...
};
```

The address space of a process is a collection of VMAs:

```c
struct vm_area_struct {
    unsigned long   vm_start;       // Start VA
    unsigned long   vm_end;         // End VA (exclusive)
    struct mm_struct *vm_mm;        // Owning mm
    pgprot_t        vm_page_prot;   // Protection bits for new PTEs
    unsigned long   vm_flags;       // VMA flags (VM_READ, VM_WRITE, VM_EXEC, VM_SHARED, ...)
    
    const struct vm_operations_struct *vm_ops; // fault(), open(), close()
    
    unsigned long   vm_pgoff;       // Offset in backing file (in pages)
    struct file    *vm_file;        // Backing file (NULL for anonymous)
    
    // ... anon_vma for CoW tracking, maple tree node, ...
};
```

### 9.5 Page Allocation: The Buddy Allocator

The kernel allocates physical pages through the buddy allocator:

```c
// Allocate 2^order contiguous physical pages
struct page *alloc_pages(gfp_t gfp_mask, unsigned int order);
struct page *alloc_page(gfp_t gfp_mask);  // order=0, single page

// Free
__free_pages(page, order);

// GFP flags (Get Free Pages):
GFP_KERNEL   // May sleep, may reclaim — normal kernel allocation
GFP_ATOMIC   // Cannot sleep (interrupt context)
GFP_USER     // User space page
GFP_DMA      // Low memory (< 16 MB for ISA DMA)
GFP_HIGHMEM  // High memory zone (32-bit only)
GFP_NOWAIT   // Don't wait for reclaim
__GFP_ZERO   // Zero the page
__GFP_COMP   // Compound page (for huge pages)
```

The buddy allocator maintains free lists of pages in powers of 2 (order 0 to 10, i.e., 4 KB to 4 MB blocks). When a block of order N is freed and its "buddy" (adjacent block of same size) is also free, they merge into order N+1. This minimizes external fragmentation.

### 9.6 struct page

Every physical page frame in the system has a `struct page` (stored in the `mem_map` array):

```c
struct page {
    unsigned long flags;         // PG_locked, PG_dirty, PG_uptodate, PG_writeback, ...
    
    union {
        struct {                 // Page cache / anonymous pages
            struct list_head lru;         // LRU list linkage
            struct address_space *mapping; // NULL=anon, or file's address_space
            pgoff_t index;                // Offset in mapping
        };
        struct {                 // Slab allocator
            struct kmem_cache *slab_cache;
            void *freelist;
        };
        // ... many other overlapping unions for different page uses
    };
    
    atomic_t _refcount;          // Reference count
    atomic_t _mapcount;          // Number of PTEs mapping this page (-1 = none)
    
    // For compound pages (huge pages):
    unsigned long compound_head; // Points to head page; bit 0 = 1 if tail page
};
```

Key page flags (`include/linux/page-flags.h`):
- `PG_locked`: Page is locked (I/O in progress)
- `PG_dirty`: Page has been written but not flushed to disk
- `PG_uptodate`: Page data is valid
- `PG_active` / `PG_inactive`: LRU classification
- `PG_referenced`: Recently accessed
- `PG_swapbacked`: Anonymous page (will go to swap if evicted)
- `PG_mlocked`: Locked in memory via `mlock()`
- `PG_hwpoison`: Hardware memory error — don't use

### 9.7 pgd_alloc and Page Table Management

```c
// arch/x86/mm/pgtable.c

pgd_t *pgd_alloc(struct mm_struct *mm)
{
    pgd_t *pgd;
    
    pgd = _pgd_alloc();       // get_zeroed_page() — allocates one physical page
    if (!pgd)
        return NULL;
    
    pgd_ctor(mm, pgd);        // Copy kernel mappings from init_mm.pgd
    // ...
    return pgd;
}

// mm/memory.c
// Allocate a PTE page on first use:
static int __pte_alloc(struct mm_struct *mm, pmd_t *pmd)
{
    pgtable_t new = pte_alloc_one(mm);   // alloc_pages(GFP_PGTABLE_USER, 0)
    if (!new)
        return -ENOMEM;
    // Install atomically using cmpxchg
    if (likely(pmd_none(*pmd))) {
        pmd_populate(mm, pmd, new);
        new = NULL;
    }
    if (new)
        pte_free(mm, new);
    return 0;
}
```

### 9.8 Memory Zones

Physical memory is divided into zones on x86-64:

```
ZONE_DMA    : 0 – 16 MB  (legacy ISA DMA devices)
ZONE_DMA32  : 0 – 4 GB   (32-bit DMA devices)
ZONE_NORMAL : All remaining RAM
ZONE_HIGHMEM: (32-bit only; not used on x86-64)
ZONE_MOVABLE: Pages that can be migrated (for memory hotplug)
ZONE_DEVICE : Device memory (persistent memory, GPU RAM via HMM)
```

Each zone has its own buddy allocator free lists and watermarks (pages_min, pages_low, pages_high). When a zone falls below `pages_low`, `kswapd` wakes up to reclaim pages. Below `pages_min`, direct reclaim is triggered in the allocating context.

---

## 10. Page Fault Handling

### 10.1 The Page Fault Exception

When the MMU cannot complete a translation, it raises a **page fault** (#PF, exception vector 14 on x86). The CPU pushes an error code and the faulting address (in CR2) onto the kernel stack, then jumps to the page fault handler.

### 10.2 Linux's do_page_fault()

```
arch/x86/mm/fault.c: exc_page_fault()
    → handle_page_fault()
        → kernelmode_fixup_or_oops() [if kernel fault]
        → do_user_addr_fault()       [if user fault]
            → find_vma(mm, address)  — O(log n) in maple tree
            → if no VMA → SIGSEGV (bad address)
            → if VMA found:
                check permissions vs error code
                → handle_mm_fault(vma, address, flags, regs)
                    → __handle_mm_fault()
                        → pgd = pgd_offset(mm, address)
                        → p4d = p4d_alloc(mm, pgd, address)
                        → pud = pud_alloc(mm, p4d, address)
                        → pmd = pmd_alloc(mm, pud, address)
                        → handle_pte_fault()
```

### 10.3 handle_pte_fault() Decision Tree

```c
static vm_fault_t handle_pte_fault(struct vm_fault *vmf)
{
    pte_t entry = *vmf->pte;

    if (!pte_present(entry)) {
        if (pte_none(entry)) {
            // PTE is empty: brand new mapping
            if (vma->vm_ops && vma->vm_ops->fault)
                return do_fault(vmf);         // File-backed: read from disk
            else
                return do_anonymous_page(vmf); // Anonymous: allocate zero page
        }
        if (pte_file(entry))
            return do_file_page(vmf);        // File in page cache
        // else: PTE has swap entry
        return do_swap_page(vmf);            // Swap in from swap device
    }

    // PTE present but fault occurred — must be protection violation
    if (pte_protnone(entry) && vma_is_accessible(vma))
        return do_numa_page(vmf);            // NUMA migration hint fault

    // Write fault on read-only PTE
    if (vmf->flags & FAULT_FLAG_WRITE) {
        if (!pte_write(entry))
            return do_wp_page(vmf);          // Copy-on-Write
    }
    // ...
}
```

### 10.4 do_anonymous_page()

Allocates a new physical page for an anonymous (heap/stack) mapping:

```c
static vm_fault_t do_anonymous_page(struct vm_fault *vmf)
{
    struct page *page;
    
    // First access to a writable anonymous page:
    if (!(vmf->flags & FAULT_FLAG_WRITE)) {
        // Map the zero page (shared read-only zero page)
        // Avoids allocation until first write
        vmf->pte = pte_offset_map_lock(vma->vm_mm, vmf->pmd, vmf->address, &vmf->ptl);
        entry = mk_pte(ZERO_PAGE(vmf->address), vma->vm_page_prot);
        entry = pte_mkspecial(entry);
        set_pte_at(vma->vm_mm, vmf->address, vmf->pte, entry);
        return VM_FAULT_NOPAGE;
    }
    
    // Writable access: allocate a real page
    page = alloc_zeroed_user_highpage_movable(vma, vmf->address);
    if (!page)
        return VM_FAULT_OOM;
    
    // Build PTE and install
    entry = mk_pte(page, vma->vm_page_prot);
    entry = pte_sw_mkyoung(entry);
    entry = pte_mkwrite(pte_mkdirty(entry));
    
    set_pte_at(vma->vm_mm, vmf->address, vmf->pte, entry);
    update_mmu_cache(vma, vmf->address, vmf->pte);
    return VM_FAULT_NOPAGE;
}
```

### 10.5 Fault Error Codes and Signals

| Condition | Signal | Code |
|-----------|--------|------|
| Access outside any VMA | SIGSEGV | SEGV_MAPERR |
| Permission violation (write to RO, exec NX) | SIGSEGV | SEGV_ACCERR |
| Stack overflow (growing down VMA) | SIGSEGV | - |
| OOM during fault handling | SIGKILL or SIGSEGV | - |
| Bus error (hardware fault on mapped page) | SIGBUS | BUS_ADRALN/BUS_ADRERR |

---

## 11. Demand Paging and Lazy Allocation

### 11.1 The Overcommit Model

Linux's memory overcommit allows allocating more virtual memory than physical RAM:

```bash
# Check overcommit mode
cat /proc/sys/vm/overcommit_memory
# 0 = heuristic overcommit (default)
# 1 = always overcommit (no limits)
# 2 = never overcommit (strict: RAM + swap * ratio)

cat /proc/sys/vm/overcommit_ratio  # default 50 (%)
```

Mode 0: The kernel uses heuristics. `malloc(10GB)` on a 4 GB machine succeeds; physical pages are only allocated when accessed. The OOM killer handles the case where actual committed memory exceeds physical capacity.

Mode 2: `CommitLimit = swap + RAM * overcommit_ratio / 100`. `mmap`/`malloc` fail if committed exceeds limit.

### 11.2 mmap() and VMA Creation

`mmap()` creates a VMA but allocates no physical pages:

```
mmap(NULL, 1GB, PROT_READ|PROT_WRITE, MAP_ANONYMOUS|MAP_PRIVATE, -1, 0)
  → sys_mmap()
    → vm_mmap()
      → do_mmap()
        → find_free_area() — find VA range
        → vma = vm_area_alloc(mm)
        → vma->vm_start = addr; vma->vm_end = addr + len
        → vma->vm_flags = VM_READ | VM_WRITE | VM_GROWSDOWN...
        → insert_vma_struct(mm, vma)
        → RETURN addr  ← no page tables allocated yet!
```

Physical pages are allocated only when the process first touches each page (page fault).

### 11.3 Stack Growth

The stack VMA has `VM_GROWSDOWN`. When a fault occurs just below `vm_start`:

```c
// expand_stack() in mm/mmap.c
static int expand_downwards(struct vm_area_struct *vma, unsigned long address)
{
    // address must be >= stack_guard_gap below current vm_start
    // Check rlimit RLIMIT_STACK
    // Extend vma->vm_start down to cover address
    // Install guard page (PROT_NONE page at bottom)
}
```

The guard page (usually 1 page) catches stack overflow: accessing it faults but cannot be expanded further → SIGSEGV.

### 11.4 madvise() Hints

```c
madvise(addr, len, advice);

MADV_NORMAL      // No special treatment
MADV_SEQUENTIAL  // Prefetch aggressively (readahead)
MADV_RANDOM      // Disable readahead
MADV_WILLNEED    // Fault in pages now (prefault)
MADV_DONTNEED    // Free pages (backs with zero page on next fault)
MADV_FREE        // Mark pages as reclaimable (lazy free)
MADV_HUGEPAGE    // Enable THP for this range
MADV_NOHUGEPAGE  // Disable THP
MADV_DONTFORK    // Don't copy this mapping to child on fork
MADV_DONTDUMP    // Exclude from core dump
MADV_HWPOISON    // Simulate hardware memory error (testing)
MADV_SOFT_OFFLINE// Migrate page away (for bad hardware)
```

`MADV_DONTNEED` is commonly used to return memory to the OS:

```c
// After using a large buffer:
madvise(buf, buf_size, MADV_DONTNEED);
// PTEs are cleared; pages returned to buddy allocator
// Next access gets fresh zero pages via page fault
```

---

## 12. Copy-on-Write (CoW)

### 12.1 fork() and CoW

`fork()` creates a child process sharing the parent's physical pages. All writable PTEs in both parent and child are marked read-only. On first write attempt:

```
Parent: VA 0x601000 → PFN 0x1234, PTE: RW=1, D=1
fork()
Parent: VA 0x601000 → PFN 0x1234, PTE: RW=0 (write-protected for CoW)
Child:  VA 0x601000 → PFN 0x1234, PTE: RW=0 (same physical page)

Child writes to 0x601000:
  → #PF (write to RO page)
  → do_wp_page()
    → _mapcount(page) > 0? Yes (shared)
    → alloc new page (PFN 0x5678)
    → copy_page(new_page, old_page)
    → child PTE: VA 0x601000 → PFN 0x5678, RW=1
    → TLB shootdown for old mapping
```

### 12.2 do_wp_page() in Depth

```c
static vm_fault_t do_wp_page(struct vm_fault *vmf)
{
    struct page *old_page = vm_normal_page(vmf->vma, vmf->address, vmf->orig_pte);
    
    // Optimization: if page is only mapped by this PTE, just make it writable
    if (PageAnon(old_page) && !PageKsm(old_page)) {
        if (page_count(old_page) == 1 &&
            !page_mapped_with_pte(old_page)) {
            // Page is exclusively ours — just set write bit
            entry = pte_mkwrite(pte_mkdirty(vmf->orig_pte));
            set_pte_at_notify(vmf->vma->vm_mm, vmf->address,
                              vmf->pte, entry);
            return VM_FAULT_WRITE;
        }
    }
    
    // Must copy
    return wp_page_copy(vmf);
}

static vm_fault_t wp_page_copy(struct vm_fault *vmf)
{
    struct page *new_page = alloc_page_vma(GFP_HIGHUSER_MOVABLE, vmf->vma, vmf->address);
    copy_user_highpage(new_page, old_page, vmf->address, vmf->vma);
    
    // Atomically update PTE
    entry = mk_pte(new_page, vmf->vma->vm_page_prot);
    entry = pte_mkwrite(pte_mkdirty(entry));
    set_pte_at_notify(vmf->vma->vm_mm, vmf->address, vmf->pte, entry);
    
    // Release old page reference
    put_page(old_page);
    return VM_FAULT_WRITE;
}
```

### 12.3 KSM (Kernel Same-page Merging)

KSM scans anonymous pages looking for identical content. It merges them into a single physical page mapped read-only in all processes (similar to CoW). On write, the page is CoW-split again.

```bash
echo 1 > /sys/kernel/mm/ksm/run      # Enable KSM
echo 100 > /sys/kernel/mm/ksm/pages_to_scan  # Pages per scan cycle
cat /sys/kernel/mm/ksm/pages_shared  # Current shared pages
```

Security concern: KSM enables timing side-channel attacks — an attacker can detect whether a target process has a certain page by measuring CoW latency.

---

## 13. Huge Pages and Transparent Huge Pages (THP)

### 13.1 Explicit Huge Pages (hugetlbfs)

Huge pages (2 MB, 1 GB) must be pre-allocated at boot or runtime:

```bash
# Reserve 1024 × 2MB huge pages
echo 1024 > /proc/sys/vm/nr_hugepages

# Or at boot:
# hugepages=1024 hugepagesz=2M

# For 1GB pages:
echo 4 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages

# Mount hugetlbfs
mount -t hugetlbfs -o pagesize=2M none /mnt/huge

# Use in code:
int fd = open("/mnt/huge/myfile", O_CREAT|O_RDWR, 0600);
void *p = mmap(NULL, 2*1024*1024, PROT_READ|PROT_WRITE,
               MAP_SHARED, fd, 0);
# Or MAP_ANONYMOUS|MAP_HUGETLB:
void *p = mmap(NULL, 2*1024*1024, PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);
```

### 13.2 Transparent Huge Pages (THP)

THP automatically promotes suitable anonymous VMAs to use 2 MB pages without application changes:

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# Modes:
always   : promote opportunistically
madvise  : only for MADV_HUGEPAGE regions
never    : disable THP

# Per-VMA opt-in:
madvise(addr, len, MADV_HUGEPAGE);
```

**THP Promotion**: When a 2 MB-aligned region of anonymous memory is fully populated with 4 KB pages and the PMD entry isn't in use, `khugepaged` scans and promotes:

```
khugepaged wakes up
  → scan all mm_structs
  → find PMD-aligned region with all 512 PTEs present
  → alloc_pages(order=9) — allocate 2 MB contiguous physical memory
  → copy all 512 small pages into huge page
  → replace 512 PTEs with single PMD entry (PS=1)
  → free 512 small pages
  → TLB flush
```

**THP Defragmentation**: `echo defer+madvise > /sys/kernel/mm/transparent_hugepage/defrag` — try to compact memory to make huge pages available.

### 13.3 Huge Page Impact on Page Tables

A 2 MB huge page uses a PMD entry with PS=1 instead of a full 512-entry PTE page:

```
Normal 4KB pages for 2MB range:
  PMD entry → PTE page (4KB, 512 entries)
    PTE[0] → PFN 0x100
    PTE[1] → PFN 0x101
    ...
    PTE[511] → PFN 0x2FF
  → 512 TLB entries, 1 PTE page allocated

2MB huge page:
  PMD entry (PS=1) → PFN 0x200 (must be 2MB-aligned)
  → 1 TLB entry, 0 PTE pages allocated
```

Savings: 511 fewer TLB entries, 1 fewer physical page for the PTE table.

---

## 14. NUMA and Paging

### 14.1 NUMA Architecture

Non-Uniform Memory Access: different physical memory regions have different latencies depending on which CPU accesses them. Each NUMA node has local RAM and CPUs.

```
Node 0: CPU 0-15,  RAM 0-64GB  (local access: 60ns)
Node 1: CPU 16-31, RAM 64-128GB (local access: 60ns, remote: 120ns)
```

### 14.2 NUMA Page Allocation Policy

```c
// Set NUMA policy for a memory region
mbind(addr, len, MPOL_PREFERRED, &nodemask, maxnode, flags);

MPOL_DEFAULT      // Use thread's default (local node)
MPOL_BIND         // Must allocate from specified nodes
MPOL_PREFERRED    // Prefer specified node, fallback to others
MPOL_INTERLEAVE   // Round-robin across nodes (bandwidth > latency)
MPOL_LOCAL        // Always allocate on current node
```

### 14.3 NUMA Balancing (AutoNUMA)

The kernel can detect when a process is accessing memory on a remote NUMA node and migrate it:

```bash
echo 1 > /proc/sys/kernel/numa_balancing

# Tuning:
/proc/sys/kernel/numa_balancing_scan_delay_ms    # 1000ms default
/proc/sys/kernel/numa_balancing_scan_period_min_ms
/proc/sys/kernel/numa_balancing_scan_size_mb
```

Mechanism: The kernel periodically marks pages as `PROT_NONE` (NUMA hint faults). On access, the fault handler records which CPU accessed the page and migrates it to the appropriate NUMA node.

---

## 15. Memory-Mapped Files (mmap)

### 15.1 File-Backed mmap

```c
void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);

// MAP_SHARED: writes go to the file; visible to other mappers
// MAP_PRIVATE: CoW — writes don't go to file

// Example: map a file read-only
int fd = open("data.bin", O_RDONLY);
void *p = mmap(NULL, file_size, PROT_READ, MAP_SHARED, fd, 0);
// p[0] triggers page fault → do_fault() → filemap_fault()
//   → find page in page cache or read from disk
//   → install PTE pointing to page cache page
```

### 15.2 The Page Cache

The page cache (`struct address_space`) is a radix tree (now XArray) of pages indexed by file offset:

```
struct address_space {
    struct inode        *host;         // Owning inode
    struct xarray        i_pages;      // Page cache: offset → struct page
    const struct address_space_operations *a_ops;
    unsigned long        nrpages;      // Total pages in cache
    // ...
};
```

When `do_fault()` runs for a file-backed page:

```
filemap_fault(vmf)
  → find_get_page(mapping, vmf->pgoff)  // Look in page cache
  → if found: install PTE, done
  → if not: allocate page, add to page cache
             submit I/O to fill page (block device)
             wait for I/O completion
             install PTE
             return
```

The page cache is the key mechanism for sharing file data between processes and for buffering disk I/O. Modified pages are written back by `pdflush`/`writeback` threads or on explicit `msync()`/`fsync()`.

### 15.3 msync() and Coherence

```c
msync(addr, len, MS_SYNC);    // Flush dirty pages to disk, wait
msync(addr, len, MS_ASYNC);   // Schedule flush, don't wait
msync(addr, len, MS_INVALIDATE); // Invalidate cached pages
```

---

## 16. Kernel Address Space Layout

### 16.1 x86-64 Linux Kernel Virtual Address Layout

```
0xFFFF_FFFF_FFFF_FFFF  ── Top of kernel space
0xFFFF_FFFF_8000_0000  ── Kernel text/data (relative to phys 0, -2GB mapping)
0xFFFF_FFFF_0000_0000  ──
         ...
0xFFFF_C000_0000_0000  ── vmalloc / ioremap space (32 TB)
0xFFFF_8800_0000_0000  ── Direct physical memory map (64 TB, PAGE_OFFSET)
                          All of physical RAM mapped here linearly
0xFFFF_8800_0000_0000  ── Start of kernel region

       [Non-canonical hole]

0x0000_7FFF_FFFF_FFFF  ── Top of user space
         ...
0x0000_0000_0000_0000  ── User space start
```

Key regions:
- **Direct map** (`PAGE_OFFSET`): All physical RAM mapped at a fixed virtual offset. Allows O(1) `phys_to_virt` and `virt_to_phys`.
- **vmalloc**: Virtually contiguous, physically discontiguous allocations (via `vmalloc()`). Used when large physically contiguous memory isn't available.
- **Kernel text**: The kernel's own code and static data, mapped near the top of VA space.

### 16.2 phys_to_virt and virt_to_phys

```c
// Fast O(1) conversion — works only for direct map pages
#define phys_to_virt(pa)  ((void *)((pa) + PAGE_OFFSET))
#define virt_to_phys(va)  ((unsigned long)(va) - PAGE_OFFSET)

// For struct page ↔ phys conversions:
#define page_to_pfn(page)  ((page) - mem_map)
#define pfn_to_page(pfn)   (mem_map + (pfn))
#define page_to_phys(page) (page_to_pfn(page) << PAGE_SHIFT)
```

### 16.3 vmalloc

```c
void *vmalloc(unsigned long size);   // Virtually contiguous
void *vzalloc(unsigned long size);   // + zero
void vfree(const void *addr);

// vmalloc internals:
// 1. Allocate N physical pages (each from buddy allocator, potentially discontiguous)
// 2. Find N-page hole in vmalloc VA space
// 3. Map each physical page to consecutive virtual pages
// 4. Only the kernel's single page table is updated (no per-process cost)
```

---

## 17. KASLR, SMEP, SMAP, and Paging Security

### 17.1 KASLR (Kernel Address Space Layout Randomization)

At boot, the kernel randomizes its own load address (text, modules, direct map, vmalloc, stack, heap):

```bash
# Check KASLR entropy
cat /proc/kallsyms | grep " T _text"
# On each boot, _text is at a different address

# Disable (for debugging only):
nokaslr  # kernel boot parameter
```

Implementation: `arch/x86/boot/compressed/kaslr.c` uses RDRAND/RDTSC + memory layout as entropy sources. Randomizes at compressed-kernel stage before decompression.

Entropy: ~30 bits on x86-64 (2^30 positions × 2 MB alignment = up to 2 TB of randomization). Effective against return-to-kernel-text attacks; less effective if attacker can leak kernel pointers via side-channels.

Mitigations that reduce KASLR effectiveness:
- `/proc/kallsyms` (restricted to root by `kptr_restrict`)
- `dmesg` leaks (mitigated by `dmesg_restrict`)
- Speculative execution side-channels (Spectre/Meltdown)

### 17.2 SMEP (Supervisor Mode Execution Prevention)

`CR4.SMEP = 1`: When the CPU is in ring 0, it cannot execute code at user-space addresses (U/S=1 in PTE). Any attempt raises #PF with I/D=1 bit set.

Prevents: kernel exploits that redirect execution to shellcode in user space (ret2user). The attacker can no longer just map shellcode in user space and return to it from the kernel.

```c
// Enable at boot (Linux sets this automatically if CPU supports it)
// Check: grep smep /proc/cpuinfo
// Kernel code:
set_in_cr4(X86_CR4_SMEP);  // boot-time
```

Bypass attempts: ROP chains within kernel text (SMEP-unaware), or pinning kernel stack in user-accessible memory (prevented by SMAP).

### 17.3 SMAP (Supervisor Mode Access Prevention)

`CR4.SMAP = 1`: When in ring 0, the CPU faults on any access to user-space memory (U/S=1) unless `EFLAGS.AC = 1` (Alignment Check flag).

The kernel sets AC=1 with `STAC` instruction and clears it with `CLAC` when intentionally accessing user memory (via `copy_from_user`, `copy_to_user`).

```asm
; Kernel code safely accessing user memory:
stac                       ; AC=1, allow user memory access
mov rax, [rbx]             ; access user pointer
clac                       ; AC=0, re-enable SMAP
```

Prevents: kernel exploits that dereference attacker-controlled pointers that happen to point into user space.

### 17.4 NX/XD Bit

PTE bit 63 (when `EFER.NXE=1`): marks a page as non-executable. Data pages (heap, stack) should always be NX. Only code pages (.text) should be executable.

Stack should be: `PROT_READ | PROT_WRITE` (no EXEC).
Heap should be: `PROT_READ | PROT_WRITE` (no EXEC).

```bash
# Check process memory permissions
cat /proc/<pid>/maps
# 7f... r--p ... libfoo.so   ← read-only
# 7f... r-xp ... libfoo.so   ← read-execute (text)
# 7f... rw-p ... libfoo.so   ← read-write (data)
```

W^X (Write XOR Execute): enforce that no page is both writable and executable simultaneously. Linux kernel enforces this for kernel memory (`CONFIG_STRICT_KERNEL_RWX`).

### 17.5 Memory Protection Keys (PKU)

16 independent protection domains, each with write-disable and access-disable bits in PKRU register. Changed in user space without syscalls via `WRPKRU` instruction.

```c
// Assign key 1 to a memory region
pkey_mprotect(addr, len, PROT_READ|PROT_WRITE, 1);

// Disable writes to key 1:
unsigned int pkru = rdpkru();
pkru |= (1 << (1*2 + 1));  // Set WD bit for key 1
wrpkru(pkru);

// This protects against accidental writes but not adversarial code
// (attacker can also call WRPKRU)
```

---

## 18. Spectre, Meltdown, and KPTI

### 18.1 Meltdown (CVE-2017-5754)

**The attack**: A user-space process reads kernel memory by exploiting speculative out-of-order execution.

```
; Attacker code:
mov rax, [kernel_address]   ; Speculatively loads kernel byte
                             ; Architecturally faults (#PF)
                             ; BUT: CPU has already speculatively
                             ; executed the next instruction:
shl rax, 12                  ; Scale byte to page offset  
mov rbx, [probe_array + rax] ; Load probe array page — this populates
                             ; cache for the specific page
; After fault is handled (byte "shouldn't" have been read):
; Attacker times access to probe_array[0..255 << 12]
; Cached page reveals the secret byte
```

Root cause: The CPU performs the speculative memory access before the permission check resolves. The fault suppresses the architectural effect, but the microarchitectural state (cache) leaks the data.

### 18.2 KPTI (Kernel Page Table Isolation)

**Defense**: Map almost no kernel memory into the user-space page table. When in user mode, the page table (CR3) points to a "shadow" PGD that contains:

- User-space mappings (same as before)
- Only the kernel entry points (syscall trampoline, interrupt handlers) — the absolute minimum needed to enter the kernel

On syscall/interrupt entry:
```asm
; Trampoline code (mapped in both user and kernel page tables):
; 1. Switch to kernel stack
; 2. Write kernel CR3 (full kernel page table)
; 3. Jump to actual syscall handler

; On syscall return:
; 1. Write user CR3 (shadow page table)
; 2. Return to user space
```

Performance cost: every syscall/interrupt = 2 CR3 writes + TLB flushes. Mitigated by PCID: the kernel and user CR3 values use different PCIDs, so the TLB retains both sets of translations.

```bash
# Check KPTI status
cat /sys/devices/system/cpu/vulnerabilities/meltdown
# "Mitigation: PTI" or "Not affected"

# Disable (testing only, never production):
nopti  # kernel boot parameter
```

### 18.3 Spectre (CVE-2017-5753, 5715)

Spectre v1 (bounds-check bypass): Trick the branch predictor into speculatively executing code beyond an array bounds check, leaking memory via cache side-channel.

Spectre v2 (branch target injection): Poison the BTB (Branch Target Buffer) to redirect kernel speculative execution to attacker-chosen gadgets.

**Mitigations**:

- **Retpoline**: Replace indirect jumps/calls with a `CALL` + `RET` that never speculatively executes the target. Linux uses retpoline for kernel indirect calls.
- **IBRS/IBPB**: Indirect Branch Restricted Speculation / Indirect Branch Predictor Barrier — hardware mitigations (expensive).
- **STIBP**: Single Thread Indirect Branch Predictors — prevent cross-thread BTB poisoning on hyperthreaded cores.
- **`array_index_nospec()`**: Compiler barrier that prevents speculative index computation beyond bounds.

```c
// Safe array access against Spectre v1:
#include <linux/nospec.h>
index = array_index_nospec(user_index, ARRAY_SIZE(my_array));
val = my_array[index];  // Speculative access is now safe
```

---

## 19. Paging in Virtualization (EPT/NPT)

### 19.1 The Problem: Two Levels of Address Translation

Without hardware support, a VMM (hypervisor) must maintain "shadow page tables" — a merged translation from GVA directly to HPA. On every guest page table modification, the VMM must intercept and update shadow tables. This is expensive and complex.

### 19.2 Intel EPT (Extended Page Tables)

EPT (also: SLAT — Second Level Address Translation) provides hardware support for two-level paging:

```
Guest Virtual Address (GVA)
    |
    | [Guest CR3 → Guest page table walk]
    v
Guest Physical Address (GPA)
    |
    | [EPT walk: EPTP → EPT page tables]
    v
Host Physical Address (HPA)
```

The EPT page tables have the same 4-level structure as regular page tables but translate GPA→HPA. The `EPTP` (EPT Pointer) register in the VMCS points to the EPT PML4.

EPT PTE flags:
```
Bit 0: R (read access)
Bit 1: W (write access)
Bit 2: X (execute access for supervisor; or user execute if "mode-based execute control")
Bits 5:3: Memory type (0=UC, 6=WB)
Bit 6: IPAT (ignore PAT — use EPT memory type)
Bit 7: PS (page size — 1GB/2MB page)
Bit 8: A (accessed)
Bit 9: D (dirty)
Bits 51:12: PFN
Bit 57: Verify guest paging
Bit 58: Paging-write access
Bit 63: Suppress #VE (virtualization exception)
```

EPT violation: When the EPT walk fails (R/W/X permission violation, or GPA not mapped), a VM-exit occurs with `EPT_VIOLATION` reason. The VMM handles it (e.g., maps the page, sets up backing memory).

### 19.3 AMD NPT (Nested Page Tables)

AMD's equivalent. Functionally identical. Controlled by `nCR3` in VMCB (VM Control Block). Same 4-level structure.

### 19.4 IOMMU and DMA Paging

The IOMMU provides a separate address translation for device DMA operations:

```
Device issues DMA to address X (device virtual)
    |
    | [IOMMU: device page table walk]
    v
Physical address

Intel VT-d / AMD-Vi implement this.
```

Benefits:
- **DMA isolation**: Device can only access memory the IOMMU allows → protects against compromised/malicious devices (Thunderclap, DMA attacks).
- **Memory remapping**: Non-contiguous physical pages appear contiguous to device.
- **VFIO passthrough**: Guest maps device directly; IOMMU enforces guest cannot DMA outside its physical memory.

```bash
# Check IOMMU status
dmesg | grep -i iommu
# [ 0.123456] DMAR: IOMMU enabled
cat /sys/class/iommu/*/intel-iommu/cap
```

---

## 20. Paging in Containers and Namespaces

### 20.1 Containers Share the Host's Page Tables

Unlike VMs, containers share the host kernel's page tables. There is no second level of translation. Container isolation for memory comes from:

1. **Process namespaces**: Containers have their own PID namespace but share the kernel's physical memory management.
2. **cgroups**: `memory.limit_in_bytes` limits physical RSS via the kernel's `mem_cgroup` mechanism.
3. **No address space isolation at VM level**: A kernel exploit in a container can potentially access host memory (no EPT barrier).

### 20.2 cgroup Memory Accounting

Every page allocation is charged to the process's memory cgroup:

```c
// mm/memcontrol.c: charge a page to a cgroup
mem_cgroup_charge(page, mm, GFP_KERNEL)
  → find mem_cgroup from mm
  → if (page_counter_try_charge(&memcg->memory, 1, &exceeded)) {
        if (exceeded) oom_or_fail();
    }
```

```bash
# Limit container memory
echo 512M > /sys/fs/cgroup/memory/mycontainer/memory.limit_in_bytes
echo 512M > /sys/fs/cgroup/memory/mycontainer/memory.memsw.limit_in_bytes

# Monitor:
cat /sys/fs/cgroup/memory/mycontainer/memory.usage_in_bytes
cat /sys/fs/cgroup/memory/mycontainer/memory.stat
```

### 20.3 userfaultfd for Container Live Migration

`userfaultfd` allows user space to handle page faults:

```c
// Register a VA range with userfaultfd
int uffd = syscall(SYS_userfaultfd, O_CLOEXEC | O_NONBLOCK);
ioctl(uffd, UFFDIO_API, &api);
ioctl(uffd, UFFDIO_REGISTER, &reg);

// When a thread faults in the registered region:
// → kernel sends message to uffd
// → handler reads message, prepares page content
// → UFFDIO_COPY: install prepared page
// → UFFDIO_ZEROPAGE: install zero page
```

Used by CRIU (Checkpoint/Restore in Userspace) for container migration: mark all pages UFFD-watched, start process on destination, lazily transfer pages on access.

---

## 21. Page Reclaim, Swapping, and the LRU

### 21.1 The LRU Lists

Linux maintains two LRU lists per zone/memcg: active and inactive, each for anonymous and file pages:

```
active_anon     : Hot anonymous pages (recently accessed)
inactive_anon   : Cold anonymous pages (candidates for swap)
active_file     : Hot file-backed pages
inactive_file   : Cold file-backed pages (candidates for eviction)
unevictable     : mlocked, ramfs, tmpfs pages
```

Pages move between lists based on the Accessed bit (A bit in PTE):

```
New page → inactive list
    │
    │ accessed again (A=1)?
    ▼
active list (mark_page_accessed)
    │
    │ page aging (clear A bit via clear_page_young)
    ▼
inactive list (page_referenced returns 0)
    │
    │ still no access?
    ▼
  reclaim (evict to swap or discard)
```

### 21.2 kswapd and Direct Reclaim

`kswapd` is a per-NUMA-node kernel thread that runs when memory falls below the `pages_low` watermark. It reclaims pages by:

1. Scanning inactive lists
2. For file pages: if clean, free immediately; if dirty, schedule writeback
3. For anonymous pages: add to swap cache, write to swap, free physical page

Direct reclaim occurs when `kswapd` can't keep up — the allocating process itself reclaims pages before allocating.

### 21.3 Swap

Swap extends effective RAM by storing cold anonymous pages on disk:

```bash
# Create swap file
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Tuning:
echo 60 > /proc/sys/vm/swappiness   # 0-200: preference for swapping vs file cache eviction
                                     # 0 = avoid swapping, 200 = aggressive
echo 1 > /proc/sys/vm/swap_vma_size # Minimum VMA pages to swap
```

Swap entry in PTE (when page is swapped out):

```
Bit 0 : P = 0 (not present — triggers page fault on access)
Bits 7:1 : Swap type (which swap device)
Bits 63:8 : Swap offset within device
```

On access to a swapped page: `do_swap_page()` reads the page back, installs PTE, wakes up waiting processes.

### 21.4 Memory Pressure and OOM Killer

When the system cannot reclaim enough memory, the OOM (Out of Memory) killer selects a process to kill:

```
oom_kill_process()
  → select_bad_process()
    → for each process: oom_badness() score
      score = pages_used * adjustment_factor
      adjustment from /proc/<pid>/oom_score_adj (-1000 to 1000)
  → kill process with highest score
```

```bash
# Protect a process from OOM killer:
echo -1000 > /proc/<pid>/oom_score_adj

# Make a process OOM-killable first:
echo 1000 > /proc/<pid>/oom_score_adj

# Disable OOM killer (not recommended for production):
echo 2 > /proc/sys/vm/overcommit_memory
```

---

## 22. C Implementations

### 22.1 Walking the Page Table from User Space (via /proc/self/pagemap)

`/proc/self/pagemap` maps each VPN to a 64-bit entry:

```
Bits 54:0 : page frame number (if present and not swapped)
Bit  55   : PTE is soft-dirty (cleared by writing to /proc/PID/clear_refs)
Bit  61   : page is file-page or shared-anon
Bit  62   : page is swapped
Bit  63   : page is present in RAM
```

```c
// pagemap_walk.c — walk page table via /proc/self/pagemap
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define PAGE_SIZE       4096UL
#define PAGE_SHIFT      12
#define PAGEMAP_ENTRY   8UL  // 64-bit per page

typedef struct {
    uint64_t pfn         : 55; // Page frame number
    uint64_t soft_dirty  :  1; // Software dirty bit
    uint64_t exclusively :  1; // Page exclusively mapped
    uint64_t uffd_wp     :  1; // userfaultfd write-protected
    uint64_t reserved    :  4;
    uint64_t file_page   :  1; // File-backed or shared anon
    uint64_t swapped     :  1; // In swap
    uint64_t present     :  1; // Present in RAM
} pagemap_entry_t;

static int pagemap_fd = -1;

int pagemap_init(void) {
    pagemap_fd = open("/proc/self/pagemap", O_RDONLY);
    return (pagemap_fd >= 0) ? 0 : -1;
}

pagemap_entry_t pagemap_get(uintptr_t vaddr) {
    pagemap_entry_t entry = {0};
    uint64_t raw;
    uint64_t vpn = vaddr / PAGE_SIZE;
    off_t offset = (off_t)(vpn * PAGEMAP_ENTRY);
    
    if (pread(pagemap_fd, &raw, sizeof(raw), offset) != sizeof(raw)) {
        perror("pread pagemap");
        return entry;
    }
    memcpy(&entry, &raw, sizeof(entry));
    return entry;
}

uintptr_t virt_to_phys(uintptr_t vaddr) {
    pagemap_entry_t e = pagemap_get(vaddr);
    if (!e.present) return (uintptr_t)-1;
    return (e.pfn << PAGE_SHIFT) | (vaddr & (PAGE_SIZE - 1));
}

int main(void) {
    if (pagemap_init() < 0) {
        fprintf(stderr, "Need /proc/self/pagemap (may need CAP_SYS_ADMIN)\n");
        return 1;
    }
    
    // Allocate and touch a page
    char *buf = mmap(NULL, PAGE_SIZE, PROT_READ|PROT_WRITE,
                     MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    if (buf == MAP_FAILED) { perror("mmap"); return 1; }
    
    buf[0] = 'A'; // Trigger page fault → physical page allocated
    
    uintptr_t vaddr = (uintptr_t)buf;
    pagemap_entry_t e = pagemap_get(vaddr);
    
    printf("Virtual addr:  0x%016lx\n", vaddr);
    printf("Present:       %d\n", e.present);
    printf("PFN:           0x%llx\n", (unsigned long long)e.pfn);
    printf("Physical addr: 0x%016lx\n", virt_to_phys(vaddr));
    printf("File-backed:   %d\n", e.file_page);
    printf("Swapped:       %d\n", e.swapped);
    printf("Soft-dirty:    %d\n", e.soft_dirty);
    
    munmap(buf, PAGE_SIZE);
    close(pagemap_fd);
    return 0;
}
```

```bash
gcc -O2 -Wall -o pagemap_walk pagemap_walk.c
# Run as root for PFN visibility:
sudo ./pagemap_walk
```

### 22.2 Simulating a Multi-Level Page Table

```c
// sim_pagetable.c — Software-simulated 4-level page table
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

// Configuration: 48-bit VA, 4KB pages, 9-9-9-9-12 split
#define VA_BITS        48
#define PAGE_SHIFT     12
#define PAGE_SIZE      (1UL << PAGE_SHIFT)
#define PT_LEVEL_BITS  9
#define PT_ENTRIES     (1 << PT_LEVEL_BITS)  // 512

// PTE flags
#define PTE_PRESENT    (1UL << 0)
#define PTE_WRITABLE   (1UL << 1)
#define PTE_USER       (1UL << 2)
#define PTE_ACCESSED   (1UL << 5)
#define PTE_DIRTY      (1UL << 6)
#define PTE_NX         (1UL << 63)
#define PTE_PFN_MASK   0x000FFFFFFFFFF000ULL

typedef uint64_t pte_t;

// Physical memory simulation
#define PHYS_MEM_SIZE  (64 * 1024 * 1024)  // 64 MB
static uint8_t phys_mem[PHYS_MEM_SIZE];
static uint64_t next_pfn = 1;  // PFN 0 reserved

uint64_t alloc_page(void) {
    uint64_t pfn = next_pfn++;
    assert(pfn * PAGE_SIZE < PHYS_MEM_SIZE);
    memset(phys_mem + pfn * PAGE_SIZE, 0, PAGE_SIZE);
    return pfn;
}

pte_t *pfn_to_virt(uint64_t pfn) {
    return (pte_t *)(phys_mem + pfn * PAGE_SIZE);
}

// Extract 9-bit index at each level
#define PGD_INDEX(va)  (((va) >> 39) & 0x1FF)
#define P4D_INDEX(va)  (((va) >> 30) & 0x1FF)  // for 5-level; used as PUD here
#define PUD_INDEX(va)  (((va) >> 30) & 0x1FF)  // 4-level: skip p4d
#define PMD_INDEX(va)  (((va) >> 21) & 0x1FF)
#define PTE_INDEX(va)  (((va) >> 12) & 0x1FF)
#define PAGE_OFFSET(va) ((va) & 0xFFF)

// Page table root (CR3 equivalent)
static uint64_t cr3_pfn = 0;

void pt_init(void) {
    cr3_pfn = alloc_page();
}

// Map a virtual address to a physical frame with given flags
int pt_map(uint64_t va, uint64_t pa, uint64_t flags) {
    pte_t *pgd, *pud, *pmd, *pte;
    uint64_t pfn;

    // Level 1: PGD
    pgd = pfn_to_virt(cr3_pfn);
    if (!(pgd[PGD_INDEX(va)] & PTE_PRESENT)) {
        pfn = alloc_page();
        pgd[PGD_INDEX(va)] = (pfn << PAGE_SHIFT) | PTE_PRESENT | PTE_WRITABLE | PTE_USER;
    }
    pfn = (pgd[PGD_INDEX(va)] & PTE_PFN_MASK) >> PAGE_SHIFT;

    // Level 2: PUD
    pud = pfn_to_virt(pfn);
    if (!(pud[PUD_INDEX(va)] & PTE_PRESENT)) {
        pfn = alloc_page();
        pud[PUD_INDEX(va)] = (pfn << PAGE_SHIFT) | PTE_PRESENT | PTE_WRITABLE | PTE_USER;
    }
    pfn = (pud[PUD_INDEX(va)] & PTE_PFN_MASK) >> PAGE_SHIFT;

    // Level 3: PMD
    pmd = pfn_to_virt(pfn);
    if (!(pmd[PMD_INDEX(va)] & PTE_PRESENT)) {
        pfn = alloc_page();
        pmd[PMD_INDEX(va)] = (pfn << PAGE_SHIFT) | PTE_PRESENT | PTE_WRITABLE | PTE_USER;
    }
    pfn = (pmd[PMD_INDEX(va)] & PTE_PFN_MASK) >> PAGE_SHIFT;

    // Level 4: PTE
    pte = pfn_to_virt(pfn);
    if (pte[PTE_INDEX(va)] & PTE_PRESENT) {
        fprintf(stderr, "Warning: re-mapping VA 0x%lx\n", va);
    }
    pte[PTE_INDEX(va)] = (pa & PTE_PFN_MASK) | flags | PTE_PRESENT;
    return 0;
}

// Translate a virtual address to physical
int pt_walk(uint64_t va, uint64_t *pa_out, uint64_t access_flags) {
    pte_t *pgd, *pud, *pmd, *pte;
    uint64_t pfn, entry;

    pgd = pfn_to_virt(cr3_pfn);
    entry = pgd[PGD_INDEX(va)];
    if (!(entry & PTE_PRESENT)) { fprintf(stderr, "#PF: PGD not present\n"); return -1; }
    pfn = (entry & PTE_PFN_MASK) >> PAGE_SHIFT;

    pud = pfn_to_virt(pfn);
    entry = pud[PUD_INDEX(va)];
    if (!(entry & PTE_PRESENT)) { fprintf(stderr, "#PF: PUD not present\n"); return -1; }
    pfn = (entry & PTE_PFN_MASK) >> PAGE_SHIFT;

    pmd = pfn_to_virt(pfn);
    entry = pmd[PMD_INDEX(va)];
    if (!(entry & PTE_PRESENT)) { fprintf(stderr, "#PF: PMD not present\n"); return -1; }
    pfn = (entry & PTE_PFN_MASK) >> PAGE_SHIFT;

    pte = pfn_to_virt(pfn);
    entry = pte[PTE_INDEX(va)];
    if (!(entry & PTE_PRESENT)) { fprintf(stderr, "#PF: PTE not present\n"); return -1; }

    // Check permissions
    if ((access_flags & PTE_WRITABLE) && !(entry & PTE_WRITABLE)) {
        fprintf(stderr, "#PF: write to read-only page\n"); return -2;
    }
    if ((access_flags & PTE_USER) && !(entry & PTE_USER)) {
        fprintf(stderr, "#PF: user access to kernel page\n"); return -3;
    }

    // Set A and D bits
    pte[PTE_INDEX(va)] |= PTE_ACCESSED;
    if (access_flags & PTE_WRITABLE)
        pte[PTE_INDEX(va)] |= PTE_DIRTY;

    pfn = (entry & PTE_PFN_MASK) >> PAGE_SHIFT;
    *pa_out = (pfn << PAGE_SHIFT) | PAGE_OFFSET(va);
    return 0;
}

// Read/write simulation
uint8_t pt_read_byte(uint64_t va) {
    uint64_t pa;
    if (pt_walk(va, &pa, PTE_USER) < 0) return 0xFF;
    return phys_mem[pa];
}

void pt_write_byte(uint64_t va, uint8_t val) {
    uint64_t pa;
    if (pt_walk(va, &pa, PTE_USER | PTE_WRITABLE) < 0) return;
    phys_mem[pa] = val;
}

int main(void) {
    pt_init();

    // Allocate a physical page and map it at VA 0x400000
    uint64_t data_pfn = alloc_page();
    uint64_t va = 0x400000;
    uint64_t pa = data_pfn << PAGE_SHIFT;

    pt_map(va, pa, PTE_WRITABLE | PTE_USER);
    printf("Mapped VA 0x%lx → PA 0x%lx\n", va, pa);

    // Write through page table
    pt_write_byte(va + 0, 'H');
    pt_write_byte(va + 1, 'i');
    pt_write_byte(va + 2, '\0');

    // Read back
    printf("Read from VA 0x%lx: %c%c\n",
           va, pt_read_byte(va), pt_read_byte(va+1));

    // Test protection: map another page read-only
    uint64_t ro_pfn = alloc_page();
    uint64_t ro_va = 0x500000;
    pt_map(ro_va, ro_pfn << PAGE_SHIFT, PTE_USER);  // no PTE_WRITABLE
    pt_write_byte(ro_va, 0xAA);  // Should fail with #PF: write to read-only

    // Walk and print PTE for our mapping
    uint64_t phys;
    pt_walk(va, &phys, PTE_USER);
    printf("PA resolved: 0x%lx\n", phys);

    return 0;
}
```

```bash
gcc -O2 -Wall -Wextra -o sim_pagetable sim_pagetable.c
./sim_pagetable
```

### 22.3 Monitoring Page Faults and TLB Misses with perf

```c
// perf_pf.c — Count page faults and TLB events
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <stdint.h>

static int perf_event_open(struct perf_event_attr *hw_event, pid_t pid,
                           int cpu, int group_fd, unsigned long flags) {
    return (int)syscall(SYS_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

int open_counter(uint32_t type, uint64_t config) {
    struct perf_event_attr pe = {0};
    pe.type = type;
    pe.size = sizeof(pe);
    pe.config = config;
    pe.disabled = 1;
    pe.exclude_kernel = 0;
    pe.exclude_hv = 1;
    int fd = perf_event_open(&pe, 0, -1, -1, 0);
    if (fd < 0) perror("perf_event_open");
    return fd;
}

int main(void) {
    // Hardware events (PMU)
    // DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK = 0x08D0 (Intel, may differ)
    // PAGE_FAULTS = software event
    int fd_pf_maj = open_counter(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_PAGE_FAULTS_MAJ);
    int fd_pf_min = open_counter(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_PAGE_FAULTS_MIN);
    int fd_pf    = open_counter(PERF_TYPE_SOFTWARE, PERF_COUNT_SW_PAGE_FAULTS);
    
    if (fd_pf < 0 || fd_pf_min < 0 || fd_pf_maj < 0) {
        fprintf(stderr, "Failed to open perf events\n");
        return 1;
    }

    ioctl(fd_pf, PERF_EVENT_IOC_RESET, 0);
    ioctl(fd_pf_min, PERF_EVENT_IOC_RESET, 0);
    ioctl(fd_pf_maj, PERF_EVENT_IOC_RESET, 0);
    ioctl(fd_pf, PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_pf_min, PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_pf_maj, PERF_EVENT_IOC_ENABLE, 0);

    // Touch 1000 pages
    size_t N = 1000;
    size_t sz = N * 4096;
    char *mem = mmap(NULL, sz, PROT_READ|PROT_WRITE,
                     MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    for (size_t i = 0; i < N; i++)
        mem[i * 4096] = (char)i;   // Touch each page
    munmap(mem, sz);

    ioctl(fd_pf, PERF_EVENT_IOC_DISABLE, 0);
    ioctl(fd_pf_min, PERF_EVENT_IOC_DISABLE, 0);
    ioctl(fd_pf_maj, PERF_EVENT_IOC_DISABLE, 0);

    uint64_t pf, pf_min, pf_maj;
    read(fd_pf,     &pf,     sizeof(pf));
    read(fd_pf_min, &pf_min, sizeof(pf_min));
    read(fd_pf_maj, &pf_maj, sizeof(pf_maj));

    printf("Total page faults:  %lu\n", pf);
    printf("Minor page faults:  %lu\n", pf_min);
    printf("Major page faults:  %lu\n", pf_maj);

    close(fd_pf); close(fd_pf_min); close(fd_pf_maj);
    return 0;
}
```

```bash
gcc -O2 -Wall -o perf_pf perf_pf.c
./perf_pf
```

---

## 23. Go Implementations

### 23.1 Go Pagemap Inspector

```go
// pagemap_inspector.go — Inspect process page table via /proc/self/pagemap
package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"syscall"
	"unsafe"
)

const (
	pageSize    = 4096
	pageShift   = 12
	pagemapSize = 8 // bytes per page entry
)

// PagemapEntry represents a 64-bit /proc/PID/pagemap entry
type PagemapEntry struct {
	PFN        uint64 // bits 54:0 — Page Frame Number
	SoftDirty  bool   // bit 55
	Exclusive  bool   // bit 56
	UFDWriteProt bool // bit 57
	// bits 58:61 reserved
	FilePage   bool   // bit 61 — file-backed or shared anon
	Swapped    bool   // bit 62
	Present    bool   // bit 63
}

func parsePagemapEntry(raw uint64) PagemapEntry {
	return PagemapEntry{
		PFN:          raw & ((1 << 55) - 1),
		SoftDirty:    (raw>>55)&1 == 1,
		Exclusive:    (raw>>56)&1 == 1,
		UFDWriteProt: (raw>>57)&1 == 1,
		FilePage:     (raw>>61)&1 == 1,
		Swapped:      (raw>>62)&1 == 1,
		Present:      (raw>>63)&1 == 1,
	}
}

// PagemapReader reads page translation info
type PagemapReader struct {
	f *os.File
}

func NewPagemapReader(pid int) (*PagemapReader, error) {
	path := fmt.Sprintf("/proc/%d/pagemap", pid)
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w (need CAP_SYS_ADMIN for PFN)", path, err)
	}
	return &PagemapReader{f: f}, nil
}

func (r *PagemapReader) Close() { r.f.Close() }

func (r *PagemapReader) ReadEntry(vaddr uintptr) (PagemapEntry, error) {
	vpn := uint64(vaddr) / pageSize
	offset := int64(vpn * pagemapSize)

	var raw uint64
	buf := make([]byte, 8)
	if _, err := r.f.ReadAt(buf, offset); err != nil {
		return PagemapEntry{}, fmt.Errorf("ReadAt vpn=0x%x: %w", vpn, err)
	}
	raw = binary.LittleEndian.Uint64(buf)
	return parsePagemapEntry(raw), nil
}

func (r *PagemapReader) VirtToPhys(vaddr uintptr) (uintptr, error) {
	e, err := r.ReadEntry(vaddr)
	if err != nil {
		return 0, err
	}
	if !e.Present {
		return 0, fmt.Errorf("page not present (PFN meaningless)")
	}
	pa := (e.PFN << pageShift) | uint64(vaddr)&(pageSize-1)
	return uintptr(pa), nil
}

// PageWalkRange walks a VA range and returns entries for each page
func (r *PagemapReader) PageWalkRange(start, end uintptr) ([]PagemapEntry, error) {
	var entries []PagemapEntry
	for va := start &^ (pageSize - 1); va < end; va += pageSize {
		e, err := r.ReadEntry(va)
		if err != nil {
			return entries, err
		}
		entries = append(entries, e)
	}
	return entries, nil
}

// PageStats aggregates stats for a range
type PageStats struct {
	Total    int
	Present  int
	Swapped  int
	FileBacked int
	SoftDirty  int
}

func (r *PagemapReader) Stats(start, end uintptr) PageStats {
	var s PageStats
	for va := start &^ (pageSize - 1); va < end; va += pageSize {
		s.Total++
		e, err := r.ReadEntry(va)
		if err != nil {
			continue
		}
		if e.Present    { s.Present++ }
		if e.Swapped    { s.Swapped++ }
		if e.FilePage   { s.FileBacked++ }
		if e.SoftDirty  { s.SoftDirty++ }
	}
	return s
}

func main() {
	pm, err := NewPagemapReader(os.Getpid())
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer pm.Close()

	// Allocate and touch memory
	const N = 16
	buf, err := syscall.Mmap(-1, 0, N*pageSize,
		syscall.PROT_READ|syscall.PROT_WRITE,
		syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS)
	if err != nil {
		fmt.Fprintln(os.Stderr, "mmap:", err)
		os.Exit(1)
	}
	defer syscall.Munmap(buf)

	// Touch first 8 pages, leave last 8 untouched
	for i := 0; i < 8*pageSize; i++ {
		buf[i] = byte(i)
	}

	start := uintptr(unsafe.Pointer(&buf[0]))
	end := start + uintptr(len(buf))

	fmt.Printf("Buffer VA range: 0x%x – 0x%x (%d pages)\n", start, end, N)
	fmt.Println()
	fmt.Printf("%-18s %-10s %-20s %-8s %-8s\n",
		"Virtual Addr", "Present", "PFN", "Swapped", "FileBkd")
	fmt.Println("─────────────────────────────────────────────────────────────")

	for i := 0; i < N; i++ {
		va := start + uintptr(i)*pageSize
		e, _ := pm.ReadEntry(va)
		pfnStr := "-"
		if e.Present {
			pfnStr = fmt.Sprintf("0x%x", e.PFN)
		}
		fmt.Printf("0x%-16x %-10v %-20s %-8v %-8v\n",
			va, e.Present, pfnStr, e.Swapped, e.FilePage)
	}

	stats := pm.Stats(start, end)
	fmt.Printf("\nStats: total=%d present=%d swapped=%d file=%d soft_dirty=%d\n",
		stats.Total, stats.Present, stats.Swapped, stats.FileBacked, stats.SoftDirty)

	// Virtual to physical translation
	pa, err := pm.VirtToPhys(start)
	if err != nil {
		fmt.Println("VirtToPhys:", err)
	} else {
		fmt.Printf("VA 0x%x → PA 0x%x\n", start, pa)
	}
}
```

```bash
go run pagemap_inspector.go
# Run as root for PFN info:
sudo go run pagemap_inspector.go
```

### 23.2 Huge Page Allocator in Go

```go
// hugepage_alloc.go — Allocate and verify huge pages
package main

import (
	"fmt"
	"os"
	"syscall"
	"unsafe"
)

const (
	hugePageSize = 2 * 1024 * 1024 // 2 MB
	pageSize     = 4096
)

// AllocHugePage allocates a 2MB anonymous huge page using MAP_HUGETLB
func AllocHugePage() ([]byte, error) {
	// MAP_HUGETLB = 0x40000 on Linux
	const MAP_HUGETLB = 0x40000
	data, err := syscall.Mmap(-1, 0, hugePageSize,
		syscall.PROT_READ|syscall.PROT_WRITE,
		syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS|MAP_HUGETLB)
	if err != nil {
		return nil, fmt.Errorf("MAP_HUGETLB failed: %w (ensure nr_hugepages > 0)", err)
	}
	return data, nil
}

// AllocHugePageMadvise allocates regular memory and hints THP
func AllocHugePageMadvise(size int) ([]byte, error) {
	// Round up to huge page boundary
	aligned := (size + hugePageSize - 1) &^ (hugePageSize - 1)
	data, err := syscall.Mmap(-1, 0, aligned,
		syscall.PROT_READ|syscall.PROT_WRITE,
		syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS)
	if err != nil {
		return nil, err
	}
	// MADV_HUGEPAGE = 14
	const MADV_HUGEPAGE = 14
	if err := syscall.Madvise(data, MADV_HUGEPAGE); err != nil {
		// Not fatal — kernel will fall back to 4KB pages
		fmt.Fprintf(os.Stderr, "MADV_HUGEPAGE: %v\n", err)
	}
	return data, nil
}

// CheckHugePageSmaps reads /proc/self/smaps to see if THP is used
func CheckHugePageSmaps(addr uintptr) (bool, error) {
	data, err := os.ReadFile("/proc/self/smaps")
	if err != nil {
		return false, err
	}
	// Look for "AnonHugePages:" in the relevant mapping section
	// Simplified: just check if any AnonHugePages > 0
	var anonHuge int
	content := string(data)
	idx := 0
	for {
		i := indexOf(content[idx:], "AnonHugePages:")
		if i < 0 {
			break
		}
		idx += i + len("AnonHugePages:")
		var kb int
		fmt.Sscanf(content[idx:], "%d", &kb)
		anonHuge += kb
	}
	return anonHuge > 0, nil
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}

// LockPages prevents the pages from being swapped out (mlockall equivalent)
func LockPages(data []byte) error {
	_, _, errno := syscall.Syscall(syscall.SYS_MLOCK,
		uintptr(unsafe.Pointer(&data[0])),
		uintptr(len(data)), 0)
	if errno != 0 {
		return fmt.Errorf("mlock: %w", errno)
	}
	return nil
}

// Benchmark: compare access patterns on huge vs regular pages
func benchmarkAccess(data []byte, stride int, name string) {
	n := len(data) / stride
	sum := 0
	for i := 0; i < n; i++ {
		sum += int(data[i*stride])
	}
	fmt.Printf("%s: sum=%d (stride=%d, n=%d)\n", name, sum, stride, n)
}

func main() {
	// Try explicit huge pages first
	fmt.Println("=== Explicit Huge Page (MAP_HUGETLB) ===")
	hp, err := AllocHugePage()
	if err != nil {
		fmt.Println("MAP_HUGETLB not available:", err)
		fmt.Println("Check: cat /proc/sys/vm/nr_hugepages")
	} else {
		defer syscall.Munmap(hp)
		// Touch all pages
		for i := 0; i < len(hp); i += pageSize {
			hp[i] = byte(i >> 12)
		}
		if err := LockPages(hp); err != nil {
			fmt.Println("mlock:", err)
		}
		fmt.Printf("Allocated %d MB huge page at %p\n", len(hp)>>20, &hp[0])
		fmt.Printf("First byte: %d\n", hp[0])
		// Verify alignment: huge page must be 2MB-aligned
		addr := uintptr(unsafe.Pointer(&hp[0]))
		if addr%uintptr(hugePageSize) != 0 {
			fmt.Printf("WARNING: not 2MB-aligned: 0x%x\n", addr)
		} else {
			fmt.Printf("Confirmed 2MB-aligned: 0x%x\n", addr)
		}
		benchmarkAccess(hp, 64, "huge-page-stride-64")
		benchmarkAccess(hp, 4096, "huge-page-stride-4K")
	}

	fmt.Println("\n=== THP via madvise ===")
	thp, err := AllocHugePageMadvise(32 * hugePageSize)
	if err != nil {
		fmt.Println("THP alloc failed:", err)
		return
	}
	defer syscall.Munmap(thp)

	// Touch all pages to trigger THP promotion by khugepaged
	for i := 0; i < len(thp); i += pageSize {
		thp[i] = byte(i >> 12)
	}
	fmt.Printf("Allocated %d MB THP-advised region at %p\n", len(thp)>>20, &thp[0])

	hasHuge, _ := CheckHugePageSmaps(uintptr(unsafe.Pointer(&thp[0])))
	fmt.Printf("AnonHugePages detected in smaps: %v\n", hasHuge)

	benchmarkAccess(thp, 64, "thp-stride-64")
	benchmarkAccess(thp, 2*1024*1024, "thp-stride-2M")

	fmt.Println("\nHuge page configuration:")
	if data, err := os.ReadFile("/proc/sys/vm/nr_hugepages"); err == nil {
		fmt.Printf("  nr_hugepages: %s", data)
	}
	if data, err := os.ReadFile("/sys/kernel/mm/transparent_hugepage/enabled"); err == nil {
		fmt.Printf("  THP: %s", data)
	}
}
```

```bash
# First ensure some huge pages exist:
sudo bash -c 'echo 8 > /proc/sys/vm/nr_hugepages'
go run hugepage_alloc.go
```

---

## 24. Rust Implementations

### 24.1 Page Table Walker (Rust, safe abstraction)

```toml
# Cargo.toml
[package]
name = "paging"
version = "0.1.0"
edition = "2021"

[dependencies]
libc = "0.2"
```

```rust
// src/main.rs — Rust page table inspector
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::os::unix::io::AsRawFd;

const PAGE_SIZE: usize = 4096;
const PAGE_SHIFT: u64 = 12;
const PAGEMAP_ENTRY_SIZE: u64 = 8;

/// Represents a decoded /proc/PID/pagemap entry
#[derive(Debug, Clone, Copy, Default)]
pub struct PagemapEntry {
    /// Physical frame number (bits 54:0); valid only if present=true
    pub pfn: u64,
    /// Bit 55: software dirty
    pub soft_dirty: bool,
    /// Bit 56: page exclusively mapped
    pub exclusive: bool,
    /// Bit 61: file-backed page
    pub file_page: bool,
    /// Bit 62: page is in swap
    pub swapped: bool,
    /// Bit 63: page is present in RAM
    pub present: bool,
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

    /// Convert VA + this entry to physical address
    pub fn phys_addr(&self, vaddr: usize) -> Option<usize> {
        if !self.present { return None; }
        let offset = vaddr & (PAGE_SIZE - 1);
        Some(((self.pfn << PAGE_SHIFT) as usize) | offset)
    }
}

impl std::fmt::Display for PagemapEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "PagemapEntry {{ present={}, pfn=0x{:x}, swapped={}, file={}, soft_dirty={} }}",
            self.present, self.pfn, self.swapped, self.file_page, self.soft_dirty)
    }
}

/// Reader for /proc/PID/pagemap
pub struct PagemapReader {
    file: File,
}

impl PagemapReader {
    pub fn open_self() -> std::io::Result<Self> {
        let file = File::open("/proc/self/pagemap")?;
        Ok(Self { file })
    }

    pub fn open_pid(pid: u32) -> std::io::Result<Self> {
        let path = format!("/proc/{}/pagemap", pid);
        let file = File::open(&path)?;
        Ok(Self { file })
    }

    pub fn read_entry(&mut self, vaddr: usize) -> std::io::Result<PagemapEntry> {
        let vpn = (vaddr / PAGE_SIZE) as u64;
        let offset = vpn * PAGEMAP_ENTRY_SIZE;
        self.file.seek(SeekFrom::Start(offset))?;
        let mut buf = [0u8; 8];
        self.file.read_exact(&mut buf)?;
        let raw = u64::from_le_bytes(buf);
        Ok(PagemapEntry::from_raw(raw))
    }

    pub fn walk_range(&mut self, start: usize, end: usize) -> Vec<(usize, PagemapEntry)> {
        let mut results = Vec::new();
        let mut va = start & !(PAGE_SIZE - 1);
        while va < end {
            if let Ok(entry) = self.read_entry(va) {
                results.push((va, entry));
            }
            va += PAGE_SIZE;
        }
        results
    }

    pub fn virt_to_phys(&mut self, vaddr: usize) -> Option<usize> {
        self.read_entry(vaddr).ok()?.phys_addr(vaddr)
    }
}

/// Simple software page table simulation (4-level, 48-bit VA)
mod sim_pt {
    use std::collections::HashMap;

    const PAGE_SIZE: usize = 4096;
    const PTE_PRESENT:  u64 = 1 << 0;
    const PTE_WRITABLE: u64 = 1 << 1;
    const PTE_USER:     u64 = 1 << 2;
    const PTE_ACCESSED: u64 = 1 << 5;
    const PTE_DIRTY:    u64 = 1 << 6;
    const PTE_NX:       u64 = 1u64 << 63;
    const PTE_PFN_MASK: u64 = 0x000F_FFFF_FFFF_F000;

    fn pgd_idx(va: usize) -> usize { (va >> 39) & 0x1FF }
    fn pud_idx(va: usize) -> usize { (va >> 30) & 0x1FF }
    fn pmd_idx(va: usize) -> usize { (va >> 21) & 0x1FF }
    fn pte_idx(va: usize) -> usize { (va >> 12) & 0x1FF }
    fn pg_offset(va: usize) -> usize { va & 0xFFF }

    /// A single page table node (512 entries)
    type PTNode = [u64; 512];

    /// Physical memory: PFN → page contents
    pub struct PageTableSim {
        nodes: HashMap<u64, Box<PTNode>>,  // PFN → page table page
        phys_mem: HashMap<u64, Vec<u8>>,   // PFN → data page
        cr3_pfn: u64,
        next_pfn: u64,
    }

    #[derive(Debug)]
    pub enum FaultKind {
        NotPresent { level: &'static str },
        WriteToReadOnly,
        UserAccessToKernel,
        NxViolation,
    }

    impl PageTableSim {
        pub fn new() -> Self {
            let mut sim = Self {
                nodes: HashMap::new(),
                phys_mem: HashMap::new(),
                cr3_pfn: 0,
                next_pfn: 1,
            };
            sim.cr3_pfn = sim.alloc_pt_node();
            sim
        }

        fn alloc_pt_node(&mut self) -> u64 {
            let pfn = self.next_pfn;
            self.next_pfn += 1;
            self.nodes.insert(pfn, Box::new([0u64; 512]));
            pfn
        }

        fn alloc_data_page(&mut self) -> u64 {
            let pfn = self.next_pfn;
            self.next_pfn += 1;
            self.phys_mem.insert(pfn, vec![0u8; PAGE_SIZE]);
            pfn
        }

        fn get_or_alloc_entry(nodes: &mut HashMap<u64, Box<PTNode>>,
                               next_pfn: &mut u64,
                               parent_pfn: u64, idx: usize, flags: u64) -> u64 {
            let entry = nodes.get(&parent_pfn).unwrap()[idx];
            if entry & PTE_PRESENT != 0 {
                (entry & PTE_PFN_MASK) >> 12
            } else {
                let new_pfn = *next_pfn;
                *next_pfn += 1;
                nodes.insert(new_pfn, Box::new([0u64; 512]));
                let pte = (new_pfn << 12) | flags | PTE_PRESENT;
                nodes.get_mut(&parent_pfn).unwrap()[idx] = pte;
                new_pfn
            }
        }

        /// Map a virtual address to a physical data page
        pub fn map(&mut self, va: usize, flags: u64) -> u64 {
            let inner_flags = PTE_PRESENT | PTE_WRITABLE | PTE_USER;
            let pgd_pfn = self.cr3_pfn;
            let pud_pfn = Self::get_or_alloc_entry(
                &mut self.nodes, &mut self.next_pfn, pgd_pfn, pgd_idx(va), inner_flags);
            let pmd_pfn = Self::get_or_alloc_entry(
                &mut self.nodes, &mut self.next_pfn, pud_pfn, pud_idx(va), inner_flags);
            let pt_pfn  = Self::get_or_alloc_entry(
                &mut self.nodes, &mut self.next_pfn, pmd_pfn, pmd_idx(va), inner_flags);

            let data_pfn = self.alloc_data_page();
            let pte = (data_pfn << 12) | flags | PTE_PRESENT;
            self.nodes.get_mut(&pt_pfn).unwrap()[pte_idx(va)] = pte;
            data_pfn
        }

        /// Walk the page table and return the physical address
        pub fn translate(&mut self, va: usize, write: bool, user: bool)
            -> Result<usize, FaultKind>
        {
            let walk = |pfn: u64, idx: usize, level: &'static str|
                -> Result<u64, FaultKind>
            {
                let entry = self.nodes.get(&pfn)
                    .ok_or(FaultKind::NotPresent { level })?[idx];
                if entry & PTE_PRESENT == 0 {
                    return Err(FaultKind::NotPresent { level });
                }
                Ok(entry)
            };

            let pgd_e = walk(self.cr3_pfn, pgd_idx(va), "PGD")?;
            let pud_e = walk((pgd_e & PTE_PFN_MASK) >> 12, pud_idx(va), "PUD")?;
            let pmd_e = walk((pud_e & PTE_PFN_MASK) >> 12, pmd_idx(va), "PMD")?;
            let pt_pfn = (pmd_e & PTE_PFN_MASK) >> 12;
            let pte = self.nodes.get(&pt_pfn)
                .ok_or(FaultKind::NotPresent { level: "PTE" })?[pte_idx(va)];

            if pte & PTE_PRESENT == 0 { return Err(FaultKind::NotPresent { level: "PTE" }); }
            if write && (pte & PTE_WRITABLE == 0) { return Err(FaultKind::WriteToReadOnly); }
            if user && (pte & PTE_USER == 0)      { return Err(FaultKind::UserAccessToKernel); }

            // Set A and D bits
            let pt = self.nodes.get_mut(&pt_pfn).unwrap();
            pt[pte_idx(va)] |= PTE_ACCESSED;
            if write { pt[pte_idx(va)] |= PTE_DIRTY; }

            let pfn = (pte & PTE_PFN_MASK) >> 12;
            Ok((pfn as usize * PAGE_SIZE) | pg_offset(va))
        }

        pub fn write_byte(&mut self, va: usize, byte: u8) -> Result<(), FaultKind> {
            let pa = self.translate(va, true, true)?;
            let pfn = pa / PAGE_SIZE;
            let off = pa % PAGE_SIZE;
            if let Some(page) = self.phys_mem.get_mut(&(pfn as u64)) {
                page[off] = byte;
            }
            Ok(())
        }

        pub fn read_byte(&mut self, va: usize) -> Result<u8, FaultKind> {
            let pa = self.translate(va, false, true)?;
            let pfn = pa / PAGE_SIZE;
            let off = pa % PAGE_SIZE;
            Ok(self.phys_mem.get(&(pfn as u64))
                .map(|p| p[off])
                .unwrap_or(0))
        }
    }
}

fn demo_pagemap() {
    println!("=== /proc/self/pagemap demo ===");
    let mut pm = match PagemapReader::open_self() {
        Ok(p) => p,
        Err(e) => { eprintln!("pagemap: {e}"); return; }
    };

    // Allocate memory via mmap
    let len = 4 * PAGE_SIZE;
    let ptr = unsafe {
        libc::mmap(
            std::ptr::null_mut(),
            len,
            libc::PROT_READ | libc::PROT_WRITE,
            libc::MAP_PRIVATE | libc::MAP_ANONYMOUS,
            -1,
            0,
        )
    };
    assert!(!ptr.is_null());

    let buf = unsafe { std::slice::from_raw_parts_mut(ptr as *mut u8, len) };

    // Touch first 2 pages
    buf[0] = 0xAA;
    buf[PAGE_SIZE] = 0xBB;
    // Leave pages 2 and 3 untouched

    let start = ptr as usize;
    let results = pm.walk_range(start, start + len);

    println!("{:<20} {:<8} {:<20} {:<8}", "VA", "Present", "PFN", "SoftDirty");
    println!("{}", "─".repeat(60));
    for (va, e) in &results {
        let pfn_str = if e.present { format!("0x{:x}", e.pfn) } else { "-".to_string() };
        println!("0x{:<18x} {:<8} {:<20} {}", va, e.present, pfn_str, e.soft_dirty);
    }

    if let Some(pa) = pm.virt_to_phys(start) {
        println!("\nVA 0x{:x} → PA 0x{:x}", start, pa);
    } else {
        println!("\nVA 0x{:x}: not present (need root for PFN)", start);
    }

    unsafe { libc::munmap(ptr, len); }
}

fn demo_sim_pt() {
    use sim_pt::PageTableSim;
    println!("\n=== Simulated 4-level Page Table ===");

    let mut pt = PageTableSim::new();

    const PTE_WRITABLE: u64 = 1 << 1;
    const PTE_USER: u64 = 1 << 2;
    const PTE_NX: u64 = 1u64 << 63;

    let va_rw: usize = 0x0000_0000_0040_0000; // 4MB
    let va_ro: usize = 0x0000_0000_0050_0000; // 5MB

    // Map RW page
    pt.map(va_rw, PTE_WRITABLE | PTE_USER | PTE_NX);
    // Map RO page
    pt.map(va_ro, PTE_USER | PTE_NX);

    // Write to RW page
    for i in 0..8 {
        pt.write_byte(va_rw + i, b'A' + i as u8).expect("write failed");
    }

    // Read back
    print!("RW page data: ");
    for i in 0..8 {
        print!("{}", pt.read_byte(va_rw + i).unwrap() as char);
    }
    println!();

    // Attempt write to RO page — should fail
    match pt.write_byte(va_ro, 0xFF) {
        Err(e) => println!("Expected fault on RO page: {:?}", e),
        Ok(())  => println!("ERROR: write to RO page should have faulted!"),
    }

    // Translate addresses
    match pt.translate(va_rw, false, true) {
        Ok(pa)  => println!("VA 0x{:x} → PA 0x{:x}", va_rw, pa),
        Err(e)  => println!("Fault: {:?}", e),
    }

    // Unmapped address
    match pt.translate(0xDEAD_0000, false, true) {
        Ok(pa)  => println!("Unexpected success: PA 0x{:x}", pa),
        Err(e)  => println!("Expected fault on unmapped address: {:?}", e),
    }
}

fn main() {
    demo_pagemap();
    demo_sim_pt();
}
```

```bash
cargo build --release
sudo ./target/release/paging
```

### 24.2 Rust: Measuring TLB Thrashing

```rust
// src/bin/tlb_bench.rs — Benchmark TLB miss cost at different strides
use std::time::Instant;

const BUF_SIZE: usize = 256 * 1024 * 1024; // 256 MB
const PAGE_SIZE: usize = 4096;

fn access_pattern(buf: &mut [u8], stride: usize) -> u64 {
    let mut sum: u64 = 0;
    let mut i = 0usize;
    while i < buf.len() {
        sum = sum.wrapping_add(buf[i] as u64);
        buf[i] = buf[i].wrapping_add(1);
        i += stride;
    }
    sum
}

fn bench(buf: &mut [u8], stride: usize, iters: u32) -> f64 {
    let _ = access_pattern(buf, stride); // warmup
    let start = Instant::now();
    let mut sum = 0u64;
    for _ in 0..iters {
        sum = sum.wrapping_add(access_pattern(buf, stride));
    }
    let elapsed = start.elapsed().as_secs_f64();
    let _ = sum;
    let accesses = (buf.len() / stride) as f64 * iters as f64;
    // Return nanoseconds per access
    elapsed * 1e9 / accesses
}

fn main() {
    // Allocate buffer (touch all pages first)
    let mut buf = vec![0u8; BUF_SIZE];
    for i in (0..BUF_SIZE).step_by(PAGE_SIZE) {
        buf[i] = i as u8;
    }

    println!("Buffer size: {} MB", BUF_SIZE >> 20);
    println!("Testing stride access patterns (each touches buf.len/stride elements):");
    println!();
    println!("{:<20} {:<12} {:<20} {:<20}", "Stride", "Pages/iter", "ns/access", "Inferred bottleneck");
    println!("{}", "─".repeat(75));

    let strides = [
        (64,           "cache line"),
        (PAGE_SIZE,    "4KB page"),
        (4 * PAGE_SIZE,"4×4KB pages"),
        (64 * 1024,    "L2 TLB span"),
        (2 * 1024 * 1024, "2MB (huge page)"),
        (4 * 1024 * 1024, "4MB"),
    ];

    for (stride, label) in strides {
        if stride >= BUF_SIZE { continue; }
        let pages_per_iter = BUF_SIZE / stride;
        let iters = if stride < PAGE_SIZE { 3 } else { 10 };
        let ns = bench(&mut buf, stride, iters);
        let bottleneck = if ns < 5.0 {
            "L1/L2 cache hit"
        } else if ns < 20.0 {
            "L3 cache hit"
        } else if ns < 100.0 {
            "TLB miss + L3 or DRAM"
        } else {
            "DRAM + TLB thrashing"
        };
        println!("{:<20} {:<12} {:<20.1} {}", label, pages_per_iter, ns, bottleneck);
    }
}
```

```bash
cargo build --release --bin tlb_bench
./target/release/tlb_bench
```

---

## 25. Threat Model and Mitigations

### 25.1 Threat Matrix

| Threat | Attack Vector | Mitigation | Defense Depth |
|--------|--------------|------------|---------------|
| Kernel memory read (Meltdown) | Speculative execution | KPTI | Hardware microcode + SW |
| Cross-process data leak (Spectre v1) | Branch prediction | `array_index_nospec()`, retpoline | Compiler + hardware |
| Return-to-user exploit | Kernel stack overwrite → jump to user shellcode | SMEP | CPU feature |
| Kernel pointer dereference to user memory | Kernel bug uses attacker-controlled pointer | SMAP | CPU feature |
| KASLR bypass via info leak | `/proc/kallsyms`, `dmesg` | `kptr_restrict=2`, `dmesg_restrict=1` | OS config |
| Physical memory access (DMA attack) | Malicious device / Thunderbolt | IOMMU (VT-d/AMD-Vi) | Hardware |
| Rowhammer bit flips | DDR refresh attack via page access patterns | ECC RAM, TRR, `vm.memory_failure_recovery` | Hardware + firmware |
| CoW race (Dirty COW CVE-2016-5195) | Race between write fault and madvise | Patched in 4.8.3; `vm.mmap_min_addr` | Kernel patch |
| KSM timing attack | Measure CoW time to detect shared pages | Disable KSM for sensitive workloads | `echo 0 > /sys/kernel/mm/ksm/run` |
| Huge page cache side-channel | 2MB huge pages have larger TLB footprint enabling fine-grained Flush+Reload | THP madvise-only mode | Policy |
| Stack overflow | Stack VMA overgrowth | Guard page (PROT_NONE) + `ulimit -s` | OS + stack design |
| Heap spray via overcommit | Allocate huge anonymous regions to position shellcode | ASLR + `mmap_min_addr` | OS config |

### 25.2 Hardening Checklist

```bash
# kptr_restrict: prevent kernel pointer leaks
echo 2 > /proc/sys/kernel/kptr_restrict

# dmesg_restrict: prevent dmesg leaks
echo 1 > /proc/sys/kernel/dmesg_restrict

# perf_event_paranoid: restrict perf event access
echo 3 > /proc/sys/kernel/perf_event_paranoid

# Randomize VA space (ASLR)
echo 2 > /proc/sys/kernel/randomize_va_space

# mmap_min_addr: prevent null pointer dereference exploits
echo 65536 > /proc/sys/vm/mmap_min_addr

# Disable KSM if not needed
echo 0 > /sys/kernel/mm/ksm/run

# Enable memory failure handling
echo 1 > /proc/sys/vm/memory_failure_recovery

# Verify SMEP/SMAP/KPTI/NX:
grep -E 'smep|smap|nx|pti' /proc/cpuinfo /boot/config-$(uname -r) 2>/dev/null
cat /sys/devices/system/cpu/vulnerabilities/*
```

---

## 26. Testing, Fuzzing, and Benchmarks

### 26.1 Testing Page Fault Behavior

```bash
# Count page faults for a process
/usr/bin/time -v ./myprogram 2>&1 | grep -E "Major|Minor"

# perf stat for TLB events:
perf stat -e \
  dTLB-loads,dTLB-load-misses,\
  dTLB-stores,dTLB-store-misses,\
  iTLB-loads,iTLB-load-misses,\
  page-faults,minor-faults,major-faults \
  ./myprogram

# perf record for page fault tracing:
perf record -e page-faults -g -- ./myprogram
perf report

# Kernel tracepoints for page faults:
sudo trace-cmd record -e mm:mm_page_fault_begin ./myprogram
trace-cmd report
```

### 26.2 Testing with userfaultfd

```bash
# Test userfaultfd-based migration:
# Linux kernel selftests:
cd linux/tools/testing/selftests/mm
make
./userfaultfd

# Other mm selftests:
./hugepage-mmap
./hugepage-shm
./map_hugetlb
./thuge-gen
./mmap2
./mlock2
./mprotect-2
```

### 26.3 Memory Testing Tools

```bash
# memtest86+ — hardware memory test (bare metal)
# Useful for catching Rowhammer-susceptible DRAM

# stress-ng: stress page reclaim, TLB, huge pages
stress-ng --vm 4 --vm-bytes 80% --mmap 4 --mmap-bytes 1G \
          --page-in --aggressive -t 60s

# numactl: test NUMA page placement
numactl --interleave=all ./myprogram
numactl --cpunodebind=0 --membind=0 ./myprogram  # force NUMA node 0

# smem: accurate RSS/PSS/USS memory accounting
smem -r -k -p -s rss | head -20

# /proc/PID/smaps_rollup: summarize page types
cat /proc/self/smaps_rollup

# valgrind massif: heap profiling  
valgrind --tool=massif --pages-as-heap=yes ./myprogram
ms_print massif.out.*

# address sanitizer for mapping errors
gcc -fsanitize=address -o prog prog.c
```

### 26.4 Kernel Fuzzing

```bash
# syzkaller: fuzzes kernel syscalls including mmap/mprotect/mremap
# Setup (abbreviated):
git clone https://github.com/google/syzkaller
cd syzkaller && make
# Configure syzkaller.cfg with syscall list: mmap, munmap, mprotect,
# mremap, madvise, mbind, mlock, userfaultfd, brk, remap_file_pages

# Trinity: more targeted syscall fuzzer
apt install trinity
trinity -c mmap -c munmap -c mprotect -c madvise

# Kernel KASAN (Kernel Address SANitizer) — compile-time:
# CONFIG_KASAN=y
# CONFIG_KASAN_INLINE=y
# CONFIG_SLUB_DEBUG=y
```

### 26.5 Performance Benchmarks

```bash
# lmbench: fundamental memory latency and bandwidth
apt install lmbench
lat_mem_rd 256m 128  # Memory latency at 256MB working set
bw_mem 256m rd       # Memory bandwidth

# mbw: memory bandwidth test
mbw -n 20 256       # 20 runs, 256MB

# Huge page impact:
# Run same workload with/without THP:
echo never > /sys/kernel/mm/transparent_hugepage/enabled && ./bench
echo always > /sys/kernel/mm/transparent_hugepage/enabled && ./bench

# TLB miss rate (PMU counters, Intel):
perf stat -e \
  cpu/event=0x08,umask=0x10,name=dtlb_load_miss_walk/ \
  cpu/event=0x08,umask=0x20,name=dtlb_store_miss_walk/ \
  -- ./bench
```

---

## 27. Production Tuning and Observability

### 27.1 Key Kernel Parameters

```bash
# /proc/sys/vm/ tuning:
vm.swappiness           = 10         # Reduce swap usage (default 60)
vm.dirty_ratio          = 20         # % of RAM dirty before blocking writes
vm.dirty_background_ratio = 5        # % triggering background writeback
vm.min_free_kbytes      = 1048576    # 1GB minimum free (prevents OOM thrashing)
vm.zone_reclaim_mode    = 0          # 0=don't reclaim from NUMA zones too aggressively
vm.overcommit_memory    = 1          # Always overcommit (for containers/JVMs)
vm.nr_hugepages         = 2048       # Pre-allocate 2048×2MB = 4GB huge pages
vm.hugetlb_shm_group    = 1001       # GID allowed to use huge page shm

# Transparent huge pages for latency-sensitive workloads:
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo defer+madvise > /sys/kernel/mm/transparent_hugepage/defrag
```

### 27.2 Observability Commands

```bash
# Per-process memory stats
cat /proc/<pid>/status | grep -E 'VmRSS|VmPSS|VmSwap|VmPeak'
cat /proc/<pid>/smaps_rollup

# System-wide memory breakdown
cat /proc/meminfo
# MemTotal, MemFree, MemAvailable, Buffers, Cached
# AnonPages, Mapped, Shmem
# HugePages_Total, HugePages_Free, AnonHugePages

# LRU page distribution
cat /proc/zoneinfo | grep -A5 "zone  Normal"

# Page fault rates (vmstat):
vmstat -w 1

# Memory pressure events (cgroup v2):
cat /sys/fs/cgroup/<cg>/memory.pressure
# some avg10=2.50 avg60=0.75 avg300=0.20 total=12345678

# Huge page usage:
cat /proc/meminfo | grep -i huge
cat /sys/kernel/mm/transparent_hugepage/khugepaged/pages_collapsed

# NUMA statistics:
numastat -m
cat /proc/buddyinfo   # Free pages per order per zone

# TLB flush events (tracepoint):
sudo perf trace -e tlb:* sleep 1

# Page reclaim:
cat /proc/vmstat | grep -E 'pgfault|pgmajfault|pgscan|pgsteal|pgswap'
```

### 27.3 Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE PAGING ARCHITECTURE                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Process A          Process B         Kernel                                ║
║  ┌─────────┐        ┌─────────┐       ┌──────────────────────┐             ║
║  │ mm_struct│        │ mm_struct│      │ init_mm              │             ║
║  │  pgd ───┼──┐     │  pgd ───┼──┐   │  pgd ────────────────┼──┐         ║
║  └─────────┘  │     └─────────┘  │   └──────────────────────┘  │         ║
║               │                  │                               │         ║
║  ┌────────────┼──────────────────┼───────────────────────────────┼──────┐  ║
║  │            │    PAGE TABLES   │                               │      │  ║
║  │   PGD A ◄──┘        PGD B ◄──┘                   Kernel PGD ◄┘      │  ║
║  │     │                  │                               │              │  ║
║  │   PUD/PMD/PTE        PUD/PMD/PTE                  PUD/PMD/PTE        │  ║
║  │     │                  │                               │              │  ║
║  └─────┼──────────────────┼───────────────────────────────┼──────────────┘  ║
║        │                  │                               │                  ║
║  ┌─────▼──────────────────▼───────────────────────────────▼──────────────┐  ║
║  │                    PHYSICAL MEMORY (RAM)                               │  ║
║  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  ║
║  │   │ Anon page│  │File-cache│  │Huge page │  │Kernel    │            │  ║
║  │   │ (CoW)    │  │(shared)  │  │(2MB/1GB) │  │data/text │            │  ║
║  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║        │                                                                      ║
║  ┌─────▼──────────────────────────────────────────────────────────────────┐  ║
║  │                         MMU / TLB                                      │  ║
║  │   L1-ITLB    L1-DTLB    STLB (shared)      Page Walker (HW)           │  ║
║  │   (128 ent)  (64 ent)   (2048 entries)      CR3→PGD→PUD→PMD→PTE→PA   │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║        │                                                                      ║
║  ┌─────▼──────────────────────────────────────────────────────────────────┐  ║
║  │                       SECURITY LAYERS                                  │  ║
║  │   SMEP  SMAP  NX/XD  KPTI  PKU  KASLR  IOMMU  EPT/NPT               │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 28. Next 3 Steps

**Step 1: Instrument the live kernel page fault path**

```bash
# Attach kprobe to handle_mm_fault and log fault addresses + types
sudo bpftrace -e '
kprobe:handle_mm_fault {
    @faults[comm, arg2 & 0xFFFF] = count();
}
interval:s:5 { print(@faults); clear(@faults); }
'

# Or with perf-probe:
sudo perf probe --add='handle_mm_fault address flags'
sudo perf record -e probe:handle_mm_fault -a sleep 5
sudo perf script | head -50
```

**Step 2: Build and run the Linux kernel mm selftests**

```bash
git clone --depth=1 https://github.com/torvalds/linux
cd linux/tools/testing/selftests/mm
make
# Run all mm tests:
sudo ./run_vmtests.sh
# Focus on: userfaultfd, transhuge, hugepage-mmap, mlock, protection-keys
```

**Step 3: Implement a minimal userspace hypervisor (KVM + EPT)**

```bash
# Study the KVM API — open /dev/kvm, create VM, set EPT entries manually
# Reference:
# https://github.com/kvmtool/kvmtool (minimal KVM hypervisor in C)
# https://github.com/gz/rust-vmm (Rust VMM components)
# Start: implement GPA→HPA mapping via KVM_SET_USER_MEMORY_REGION
# Then: catch EPT_VIOLATION vm-exits, implement demand mapping in host

# Quickstart:
git clone https://github.com/kvmtool/kvmtool
cd kvmtool && make
lkvm run --kernel bzImage --mem 256
```

---

## 29. References

### Linux Kernel Source
- `arch/x86/mm/fault.c` — x86 page fault handler
- `arch/x86/mm/pgtable.c` — Page table allocation
- `mm/memory.c` — Core virtual memory operations
- `mm/mmap.c` — VMA management, mmap
- `mm/page_alloc.c` — Buddy allocator
- `mm/huge_memory.c` — Transparent huge pages
- `mm/memcontrol.c` — cgroup memory accounting
- `mm/swap.c`, `mm/vmscan.c` — Swap and LRU reclaim
- `include/linux/pgtable.h` — Page table abstraction
- `include/asm-generic/pgtable-nop4d.h` — Level folding

### Intel Manuals
- Intel SDM Vol. 3A, Chapter 4: Paging
- Intel SDM Vol. 3A, Chapter 11: Memory Cache Control
- Intel SDM Vol. 3C: VMX (EPT in §28.3)

### AMD Manuals
- AMD APM Vol. 2: System Programming (NPT in §15.25)

### Papers
- "Meltdown" — Lipp et al., 2018 (arxiv:1801.01207)
- "Spectre Attacks" — Kocher et al., 2019 (arxiv:1801.01203)
- "KPTI" — LWN.net (https://lwn.net/Articles/741878/)
- "Huge pages are a good idea" — Brendan Gregg
- "The Linux MM Book" — Gordon Memon (https://www.kernel.org/doc/gorman/)

### Kernel Documentation
- `Documentation/x86/x86_64/mm.rst` — x86-64 memory map
- `Documentation/admin-guide/mm/` — Huge pages, NUMA, memory hotplug
- `Documentation/core-api/mm-api.rst` — Core MM API

### Tools
- `perf-mem(1)` — Memory access profiling
- `numastat(8)` — NUMA statistics
- `smem(8)` — Accurate memory usage
- `pmap(1)` — Process memory map
- `bpftrace` — Dynamic kernel instrumentation for mm events

This will be a large document. Let me build it directly.3,221 lines, ~112 KB. Here's what the guide covers end-to-end:

**Foundations** — Why paging exists (fragmentation, isolation, overcommit), the four address types (GVA/GPA/HPA/DMA), canonical address requirements, and the fixed-size-page vs. segmentation tradeoff at first principles.

**Hardware depth** — Full x86-64 PTE bit layout (all 64 bits explained), 4-level and 5-level paging, CR3/PCID mechanics, PCIDE-based context switches, ARM64 dual-TTBR regime, MAIR memory attributes, and the hardware page table walk step-by-step with all fault error code bits.

**TLB** — Full hierarchy (L1 ITLB/DTLB → STLB), shootdown protocol (IPI→INVLPG→ACK), all x86-64 and ARM64 flush instructions, PCID/ASID optimization, and TLB coverage math for 4K vs. 2MB vs. 1GB pages.

**Linux kernel internals** — `mm_struct`, `vm_area_struct`, maple tree VMA lookup, `pgd_alloc`, `do_page_fault` → `handle_pte_fault` → `do_anonymous_page` / `do_wp_page` / `do_swap_page` call chains, buddy allocator, zone watermarks, `struct page` flags, LRU lists, `kswapd`, OOM killer scoring.

**Advanced topics** — CoW (fork + `do_wp_page`), KSM, THP promotion via `khugepaged`, NUMA balancing hint faults, `userfaultfd` for live migration, `mmap` → page cache → `filemap_fault`, KPTI shadow page tables + PCID mitigation, SMEP/SMAP enforcement, PKU domains, EPT/NPT two-level translation, IOMMU/VT-d, cgroup memory accounting.

**Implementations** — `/proc/self/pagemap` walker in C, full 4-level software page table simulator in C, `perf_event` page fault counter in C; pagemap inspector + huge page allocator + smaps checker in Go; page table walker + simulated 4-level page table with fault kinds + TLB thrashing benchmark in Rust.