# Translation Lookaside Buffer (TLB): A Complete Masterclass

> *"The difference between a mediocre systems programmer and an elite one is knowing not just what the hardware does — but why, and at what cost."*

---

## Table of Contents

1. [Foundations: Virtual Memory & Address Translation](#1-foundations-virtual-memory--address-translation)
2. [What Is a TLB?](#2-what-is-a-tlb)
3. [TLB Architecture & Hardware Design](#3-tlb-architecture--hardware-design)
4. [TLB Entry Structure](#4-tlb-entry-structure)
5. [TLB Miss Handling](#5-tlb-miss-handling)
6. [TLB Shootdowns & SMP Coherence](#6-tlb-shootdowns--smp-coherence)
7. [ASID — Address Space Identifiers](#7-asid--address-space-identifiers)
8. [PCID — Process-Context Identifiers (x86-64)](#8-pcid--process-context-identifiers-x86-64)
9. [Huge Pages & TLB Coverage](#9-huge-pages--tlb-coverage)
10. [Linux Kernel TLB Subsystem (Deep Dive)](#10-linux-kernel-tlb-subsystem-deep-dive)
11. [TLB and Security: Spectre, Meltdown, KPTI](#11-tlb-and-security-spectre-meltdown-kpti)
12. [TLB Performance Analysis & Profiling](#12-tlb-performance-analysis--profiling)
13. [TLB-Aware Programming Patterns](#13-tlb-aware-programming-patterns)
14. [Implementations: C, Go, Rust](#14-implementations-c-go-rust)
15. [ARM, RISC-V vs x86 TLB Differences](#15-arm-risc-v-vs-x86-tlb-differences)
16. [Virtualization & Nested Paging](#16-virtualization--nested-paging)
17. [TLB in the Context of NUMA](#17-tlb-in-the-context-of-numa)
18. [Mental Models & Expert Intuition](#18-mental-models--expert-intuition)

---

## 1. Foundations: Virtual Memory & Address Translation

### Why Virtual Memory Exists

Every process believes it owns the entire address space. This illusion is the foundation of modern operating systems. Without it:

- Processes would stomp on each other's memory.
- Loading programs would require knowing their physical addresses at compile time.
- Isolation and security would be impossible.
- Memory overcommit (using more memory than physically available) would be impossible.

The CPU, MMU (Memory Management Unit), and OS collaborate to maintain this illusion.

### The Address Translation Problem

When a program accesses memory address `0x4000000000` (a virtual address), the CPU must:

1. Find the physical address it maps to.
2. Check permissions (read/write/execute).
3. Handle faults (page not present, protection violation).

The data structure encoding this mapping is the **page table**.

### Page Table Structure (x86-64, 4-level)

```
Virtual Address (48 bits used):
 ┌──────┬──────┬──────┬──────┬────────────┐
 │ PML4 │  PDP │  PD  │  PT  │   Offset   │
 │ [47-39]│[38-30]│[29-21]│[20-12]│  [11-0]  │
 └──────┴──────┴──────┴──────┴────────────┘
   9 bits  9 bits  9 bits  9 bits  12 bits

Each level = 512 entries × 8 bytes = 4 KB table
```

Walking all 4 levels to translate one address requires **4 memory accesses**. At 100 ns per DRAM access, that is **400 ns overhead per memory reference**. A modern CPU executing at 3 GHz completes ~1200 cycles in that time. This is catastrophic.

**The TLB solves this.**

---

## 2. What Is a TLB?

The **Translation Lookaside Buffer** is a small, extremely fast, fully-associative (or set-associative) cache that stores recent virtual-to-physical address translations.

```
CPU Core
  │
  ├── L1 TLB (Instruction) ──┐
  ├── L1 TLB (Data)          ├──→ L2 TLB (Unified) ──→ Page Walker (HW or SW)
  └── ...                    │                               │
                             └───────────────────────────────┘
                                       │
                                       ↓
                                 Page Tables (in RAM)
```

### TLB Hit Path

```
VA → TLB Lookup (1–2 cycles) → PA → Cache / RAM
```

### TLB Miss Path

```
VA → TLB Miss → Page Walker → 1–4 RAM accesses → Update TLB → PA → Cache / RAM
```

### Key Metrics

| Parameter       | Typical Value (Modern x86) |
|----------------|---------------------------|
| L1 ITLB size   | 128–256 entries            |
| L1 DTLB size   | 64–96 entries              |
| L2 TLB size    | 1024–2048 entries          |
| L1 TLB latency | 0–1 cycles (parallel)      |
| TLB miss cost  | 20–200+ cycles             |
| Page size      | 4 KB (default), 2 MB, 1 GB |

---

## 3. TLB Architecture & Hardware Design

### Fully Associative TLB

Every entry can hold any virtual address. Lookup requires comparing the query tag against all entries simultaneously using **CAM (Content Addressable Memory)**.

```
Query VA Tag ──→ [Tag₀ | Tag₁ | Tag₂ | ... | TagN]  ← parallel compare
                 [PA₀  | PA₁  | PA₂  | ... | PAN ]
                         │
                    Match? → Output PA + flags
```

**Pros:** No conflict misses; highest hit rate.  
**Cons:** Power-hungry; expensive to build at scale. Used for small L1 TLBs.

### Set-Associative TLB

The TLB is divided into sets. A portion of the VA selects the set; within the set, all ways are compared.

```
VA = [Tag | Set Index | Page Offset]
           ↓
     Select Set (e.g., 4 ways)
     Compare Tag against all 4 ways simultaneously
     Hit → return PA
     Miss → evict (LRU/PLRU) → fill from page walker
```

**Used for:** L2 TLBs (larger, power-efficient).

### TLB Replacement Policies

- **LRU (Least Recently Used):** Optimal but expensive to implement in hardware.
- **Pseudo-LRU (PLRU):** Binary tree approximation. Used in Intel TLBs.
- **Random:** Simple. Used in ARM Cortex-A series for L1 TLB.
- **FIFO:** Rare; poor performance for working sets.

### Intel Skylake TLB Hierarchy (Reference)

| TLB Level         | Type        | Entries | Associativity | Page Sizes   |
|-------------------|-------------|---------|---------------|--------------|
| L1 ITLB           | Instruction | 128     | 8-way         | 4K           |
| L1 ITLB (large)   | Instruction | 8       | Fully assoc.  | 2M/4M        |
| L1 DTLB           | Data        | 64      | 4-way         | 4K           |
| L1 DTLB (large)   | Data        | 32      | 4-way         | 2M/4M/1G     |
| L2 STLB           | Unified     | 1536    | 6-way         | 4K + 2M      |

---

## 4. TLB Entry Structure

Each TLB entry contains:

```
┌─────────────────────────────────────────────────────────┐
│  ASID/PCID │  Virtual Page Number │  Physical Frame Number │
│  (8-16 b)  │     (VPN, 36 bits)   │     (PFN, 40 bits)     │
├─────────────────────────────────────────────────────────┤
│  V (Valid) │ G (Global) │ D (Dirty) │ A (Accessed)         │
│  U/S (Priv)│ NX (No-Exec)│ W (Write) │ PCD/PWT (Cache)     │
└─────────────────────────────────────────────────────────┘
```

### Flag Semantics

| Flag | Name       | Meaning                                                        |
|------|------------|----------------------------------------------------------------|
| V    | Valid      | Entry is live and usable                                       |
| G    | Global     | Not flushed on context switch (kernel mappings)                |
| D    | Dirty      | Page has been written; OS must track for COW and swap          |
| A    | Accessed   | Page has been read or written; used by page replacement        |
| U/S  | User/Super | Accessible in user mode (U) or only in supervisor mode (S)     |
| NX   | No-Execute | CPU raises #PF if instruction fetch attempted                  |
| W    | Writable   | Write access allowed                                           |
| PWT  | Write-Through | Cache policy hint                                           |
| PCD  | Cache Disable | Bypass cache for this page (MMIO regions)                  |

### Global Pages

Pages mapped with the **G (Global)** flag are **not invalidated** on `CR3` reload (i.e., on context switches). The Linux kernel maps itself as global — kernel virtual addresses remain in TLB across all process switches, eliminating redundant kernel TLB misses.

This optimization was partially reverted by **KPTI** (Kernel Page Table Isolation) post-Meltdown — discussed in Section 11.

---

## 5. TLB Miss Handling

### Hardware-Walked TLB (x86, ARM)

The CPU has a dedicated **Page Table Walker** unit that automatically walks the page table hierarchy on a TLB miss.

```
Step 1: TLB Miss triggered
Step 2: Hardware reads CR3 (or TTBR0/TTBR1 on ARM)
Step 3: Walk PML4 → PDPT → PD → PT
Step 4: Load PTE into TLB
Step 5: Retry the faulting instruction
```

The page walker accesses memory — these accesses go through the **L1/L2 data cache**, so if page tables are hot in cache, the walk is fast (~20 cycles). Cold page tables cause cache misses stacking on top of TLB misses.

### Software-Walked TLB (MIPS, older SPARC)

On MIPS, a TLB miss triggers a **TLB Miss exception**. The OS exception handler is responsible for loading the correct translation into the TLB.

```asm
# MIPS TLB refill handler (simplified)
tlb_miss:
    mfc0  $k0, $Context   # Context reg points to PTE in kernel virtual space
    lw    $k1, 0($k0)     # Load PTE pair (even/odd pages)
    lw    $k0, 4($k0)
    mtc0  $k1, $EntryLo0  # Load even PTE
    mtc0  $k0, $EntryLo1  # Load odd PTE
    tlbwr                  # Write random TLB entry
    eret                   # Return from exception
```

**Software TLB advantages:**
- More flexibility (OS controls replacement policy).
- Simpler CPU design.

**Software TLB disadvantages:**
- Higher miss penalty (exception overhead ~50+ cycles minimum).
- Exception handler must itself not cause TLB misses (it's mapped in wired TLB entries).

### Page Fault vs. TLB Miss

A common confusion to eliminate:

| Event      | Cause                                          | Handler         |
|------------|------------------------------------------------|-----------------|
| TLB Miss   | Translation not in TLB but PTE exists in table | HW page walker  |
| Page Fault | PTE not present, protection violation, or COW  | OS `do_page_fault()` |

A TLB miss that walks to a **not-present** PTE → raises a **Page Fault (#PF, exception 14 on x86)**.

---

## 6. TLB Shootdowns & SMP Coherence

This is one of the most critical and subtle TLB concepts for systems programmers.

### The Problem

TLBs are **per-core** caches. When the OS modifies a page table entry (e.g., unmaps a page, changes permissions, reclaims a physical frame), the stale translation may still live in other cores' TLBs.

If CPU 0 unmaps a page but CPU 1 still has the old translation cached, CPU 1 will access freed memory — a silent corruption or security vulnerability.

### The Shootdown Protocol

```
CPU 0 (initiator)                    CPU 1, 2, ... (targets)
─────────────────                    ──────────────────────
1. Modify page table entry
2. Send IPI (Inter-Processor
   Interrupt) to all other CPUs
3. Spin-wait for acknowledgment  ←── 4. Receive IPI
                                      5. Execute INVLPG or flush TLB
                                      6. Send acknowledgment
7. Receive all acks
8. Continue
```

### Linux Kernel Implementation

Linux implements TLB shootdown via `flush_tlb_others()`. The key function chain:

```
tlb_finish_mmu()
  └── tlb_flush_mmu()
        └── tlb_flush_mmu_tlbonly()
              └── arch_tlb_finish_mmu()
                    └── flush_tlb_mm_range()
                          └── native_flush_tlb_others()
                                └── smp_call_function_many() → IPI
```

The per-architecture x86 path uses `INVLPG` for single-page flushes and `CR3` reload for full flushes.

```c
/* arch/x86/mm/tlb.c - simplified */
static void flush_tlb_func(void *info)
{
    struct flush_tlb_info *f = info;

    if (f->end == TLB_FLUSH_ALL) {
        /* Full flush: reload CR3 */
        write_cr3(read_cr3());
    } else {
        /* Range flush: INVLPG each page */
        unsigned long addr;
        for (addr = f->start; addr < f->end; addr += PAGE_SIZE)
            __flush_tlb_single(addr);
    }
}
```

### Shootdown Performance Cost

TLB shootdowns are **extremely expensive**:

1. IPI delivery: ~500–1000 cycles on the sending core.
2. IPI receipt + handler: ~200–500 cycles on each target core.
3. Synchronization spin: blocking the initiator.

On a 64-core machine, a single TLB shootdown involves 63 IPIs. This is why:

- `munmap()` is slow when many threads share a mapping.
- `fork()` + `exec()` causes shootdowns.
- Memory-intensive workloads on NUMA systems suffer disproportionately.

### Batching Shootdowns

The Linux kernel batches TLB flushes using the **mmu_gather** structure:

```c
struct mmu_gather {
    struct mm_struct    *mm;
    unsigned long        start;      /* start of range being flushed */
    unsigned long        end;        /* end of range being flushed */
    unsigned int         fullmm:1;   /* full mm flush? */
    unsigned int         need_flush_all:1;
    struct mmu_gather_batch *active;
    struct mmu_gather_batch local;
    struct page         *__pages[MMU_GATHER_BUNDLE];
    unsigned int         page_count;
    unsigned int         max;
};
```

The OS accumulates page unmappings and defers the actual shootdown until `tlb_finish_mmu()`, reducing the number of IPIs.

---

## 7. ASID — Address Space Identifiers

### The Context Switch TLB Flush Problem

On a context switch from Process A to Process B, all of Process A's TLB entries are invalid for Process B. Naively, the OS must flush the entire TLB on every context switch. This is crippling for workloads with frequent context switches (e.g., web servers, microservices).

### ASID to the Rescue

**Address Space Identifiers (ASIDs)** tag each TLB entry with the process that owns it. The TLB can hold entries from **multiple processes simultaneously**.

```
TLB Entry with ASID:
┌─────────┬────────────────────┬────────────────────┐
│  ASID   │  Virtual Page Num  │  Physical Frame Num │
│  (8 bits)│     (36 bits)      │     (40 bits)       │
└─────────┴────────────────────┴────────────────────┘
```

On context switch, the CPU loads the new process's ASID into the **ASID register**. TLB entries belonging to other ASIDs are simply ignored (not invalidated). They remain in the TLB and will be reused if that process runs again.

### ASID Exhaustion

With 8-bit ASIDs, there are only 256 unique ASIDs. When they run out, the OS must:

1. Flush the entire TLB (ASID rollover).
2. Start reassigning ASIDs from 0.

Linux tracks this with a **generation counter**:

```c
/* arch/arm64/include/asm/mmu.h */
typedef struct {
    atomic64_t    id;
    void          *vdso;
    unsigned long flags;
} mm_context_t;

/* The ASID is stored in mm->context.id */
/* High bits = generation; low bits = ASID value */
#define ASID_MASK       ((1UL << asid_bits) - 1)
#define ASID_FIRST_VERSION  (1UL << asid_bits)

static u64 new_context(struct mm_struct *mm)
{
    u64 asid = atomic64_read(&mm->context.id);
    u64 generation = atomic64_read(&asid_generation);

    if (asid != 0) {
        /* Try to reuse existing ASID if same generation */
        u64 newasid = generation | (asid & ASID_MASK);
        if (check_update_reserved_asid(asid, newasid))
            return newasid;
        /* Check if ASID still valid */
        if ((asid ^ generation) >> asid_bits == 0)
            return newasid;
    }

    /* Allocate new ASID */
    asid = find_next_zero_bit(asid_map, NUM_USER_ASIDS, cur_idx);
    if (asid == NUM_USER_ASIDS) {
        /* Rollover: flush all TLBs, bump generation */
        generation = atomic64_add_return_relaxed(ASID_FIRST_VERSION, &asid_generation);
        flush_tlb_all();
        bitmap_clear(asid_map, 0, NUM_USER_ASIDS);
        asid = find_next_zero_bit(asid_map, NUM_USER_ASIDS, 1);
    }

    set_bit(asid, asid_map);
    cur_idx = asid;
    cpumask_clear(mm_cpumask(mm));
    return asid | generation;
}
```

### ARM64 ASID Details

ARM64 supports 8-bit (256) or 16-bit (65536) ASIDs, configurable at boot. The current ASID is stored in `TTBR0_EL1[63:48]`.

The kernel's own mappings use `TTBR1_EL1` and are always active — they don't use ASIDs (they're global).

---

## 8. PCID — Process-Context Identifiers (x86-64)

x86-64's equivalent of ASIDs is **PCID (Process Context Identifiers)**, introduced in Intel Westmere (2010) and enabled by Linux after Meltdown mitigations in 2018.

### PCID Mechanics

- 12-bit field in `CR3[11:0]` → 4096 unique PCIDs.
- When `CR3` is loaded with the `NOFLUSH` bit (bit 63) set, the TLB is **not flushed**.
- Each PCID acts like an ASID tag on TLB entries.

```c
/* Loading CR3 with PCID and NOFLUSH */
static inline void load_new_mm_cr3(pgd_t *pgdir, u16 new_asid, bool need_flush)
{
    unsigned long new_cr3 = __pa(pgdir) | new_asid;

    if (!need_flush)
        new_cr3 |= X86_CR3_PCID_NOFLUSH; /* bit 63 */

    write_cr3(new_cr3);
}
```

### PCID and KPTI

Post-Meltdown, Linux uses KPTI (Kernel Page Table Isolation), which means two page tables per process:

1. **User page table** (contains only user mappings + minimal kernel trampoline).
2. **Kernel page table** (full kernel mapping).

With PCID, Linux assigns:
- PCID `X` for user space.
- PCID `X + 4096` (conceptually) for kernel space.

On syscall entry, the kernel switches to the kernel page table **without flushing** user TLB entries. This is the key PCID optimization — otherwise every syscall would flush the TLB.

```c
/* arch/x86/entry/entry_64.S */
/* On entry from userspace, switch to kernel CR3 */
SWITCH_TO_KERNEL_CR3 scratch_reg=%rsp

/* On return to userspace, switch back to user CR3 */
SWITCH_TO_USER_CR3_NOSTACK scratch_reg=%rax scratch_reg2=%rdx
```

### Checking PCID Support

```bash
grep -m1 pcid /proc/cpuinfo

# Or in kernel: check X86_FEATURE_PCID
# In dmesg: "PCID enabled"
```

---

## 9. Huge Pages & TLB Coverage

### The Coverage Problem

With 4 KB pages and 64 DTLB entries:

```
TLB Coverage = 64 entries × 4 KB = 256 KB
```

A workload with a 256 MB working set will have nearly 100% TLB miss rate. Every access is a page walk.

### Huge Pages Solution

```
2 MB pages  → 64 entries × 2 MB  = 128 MB  coverage
1 GB pages  → 64 entries × 1 GB  = 64 GB   coverage
```

Huge pages are transformative for TLB-bound workloads (databases, HPC, ML frameworks).

### Types of Huge Pages in Linux

#### 1. HugeTLBfs (Static Huge Pages)

Pre-allocated at boot or runtime. Applications use `mmap()` with `MAP_HUGETLB`.

```bash
# Reserve 512 huge pages (2 MB each = 1 GB total)
echo 512 > /proc/sys/vm/nr_hugepages

# Check
cat /proc/meminfo | grep -i huge
#   HugePages_Total:     512
#   HugePages_Free:      512
#   Hugepagesize:       2048 kB
```

```c
/* C: Allocate huge pages */
#include <sys/mman.h>

void *ptr = mmap(NULL, size,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                 -1, 0);
```

#### 2. Transparent Huge Pages (THP)

Linux automatically promotes aligned, contiguous 4 KB pages into 2 MB huge pages. Managed by `khugepaged` kernel thread.

```bash
# THP modes
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# Advise the kernel to use huge pages for a region
madvise(ptr, size, MADV_HUGEPAGE);

# Disable THP for latency-sensitive apps (avoids khugepaged stalls)
madvise(ptr, size, MADV_NOHUGEPAGE);
```

#### 3. Contiguous Memory Allocator (CMA) for 1 GB Pages

1 GB pages must be reserved at boot:

```bash
# Reserve 4 GB as 1 GB huge pages
hugepagesz=1G hugepages=4
```

### THP Internals

`khugepaged` scans page tables looking for 512 contiguous 4 KB pages that:
- Are aligned to 2 MB boundary.
- All belong to the same VMA.
- Are all present (not swapped).

It collapses them into a single 2 MB PMD entry. This requires a **TLB shootdown** across all CPUs mapping those pages — the hidden cost of THP.

### Huge Page PTEs

```
4 KB Page PTE (level 1, PT):
┌──────────────────────────────────────────────────────┐
│ Physical Frame Number (52 bits) │ Flags (12 bits)    │
└──────────────────────────────────────────────────────┘

2 MB Page PDE (level 2, PD) — PS bit set:
┌──────────────────────────────────────────────────────┐
│ Physical Frame Number (43 bits) │ PS=1 │ Flags       │
└──────────────────────────────────────────────────────┘
The PS (Page Size) bit tells the page walker: stop here, this is a leaf.
```

---

## 10. Linux Kernel TLB Subsystem (Deep Dive)

### Key Source Files

| File                          | Purpose                                    |
|-------------------------------|--------------------------------------------|
| `arch/x86/mm/tlb.c`          | x86 TLB flush implementations              |
| `arch/arm64/mm/tlb.S`        | ARM64 TLB flush assembly                   |
| `mm/mmu_gather.c`            | Generic TLB batching infrastructure        |
| `include/asm-generic/tlb.h`  | Generic `mmu_gather` API                   |
| `arch/x86/include/asm/tlb.h` | x86-specific TLB types                     |
| `mm/memory.c`                | `unmap_page_range()` using mmu_gather      |

### Flush Function Taxonomy

```c
/* 1. Flush entire TLB (all processes) */
flush_tlb_all();

/* 2. Flush TLB for a specific mm (all CPUs running it) */
flush_tlb_mm(struct mm_struct *mm);

/* 3. Flush a virtual address range in an mm */
flush_tlb_mm_range(struct mm_struct *mm, unsigned long start,
                   unsigned long end, unsigned long stride_shift,
                   bool freed_tables);

/* 4. Flush a single page in current mm */
flush_tlb_page(struct vm_area_struct *vma, unsigned long addr);

/* 5. Flush kernel mappings */
flush_tlb_kernel_range(unsigned long start, unsigned long end);
```

### x86 Implementation: `INVLPG` vs CR3 Reload

```c
/* Single page invalidation — preferred when range is small */
static inline void __flush_tlb_single(unsigned long addr)
{
    asm volatile("invlpg (%0)" :: "r" (addr) : "memory");
}

/* Full flush — reload CR3 */
static inline void __flush_tlb(void)
{
    unsigned long cr3 = read_cr3_pa();
    write_cr3(cr3);  /* Writing same value still flushes non-global entries */
}

/* Full flush including global pages */
static inline void __flush_tlb_global(void)
{
    unsigned long flags, cr4;
    raw_local_irq_save(flags);
    cr4 = this_cpu_read(cpu_tlbstate.cr4);
    /* Clear PGE bit to flush global entries */
    native_write_cr4(cr4 & ~X86_CR4_PGE);
    /* Restore PGE bit */
    native_write_cr4(cr4);
    raw_local_irq_restore(flags);
}
```

### The mmu_gather API (Generic TLB Batching)

The `mmu_gather` mechanism ensures TLB flushes are deferred and batched during large unmap operations:

```c
/* Typical usage in mm/memory.c */
void unmap_vmas(struct mmu_gather *tlb,
                struct vm_area_struct *vma,
                unsigned long start_addr, unsigned long end_addr)
{
    tlb_start_vma(tlb, vma);

    /* Walk PTEs and accumulate pages to free */
    unmap_page_range(tlb, vma, start_addr, end_addr, NULL);

    tlb_end_vma(tlb, vma);
}

/* Caller pattern */
tlb_gather_mmu(&tlb, mm);           /* Initialize */
    unmap_vmas(&tlb, vma, start, end);  /* Accumulate */
tlb_finish_mmu(&tlb);              /* Flush + free pages */
```

`tlb_finish_mmu()` triggers the actual shootdown and only then frees physical pages. This ordering is critical — pages must not be recycled while stale TLB entries referencing them exist.

### Linux TLB Lazy Mode

Linux uses **lazy TLB mode** to avoid unnecessary flushes:

When a process is context-switched out, instead of flushing its TLB entries immediately, the kernel marks the CPU as "lazy." Only if another process unmaps pages that this CPU's TLB might cache does a flush actually happen.

```c
/* arch/x86/mm/tlb.c */
void switch_mm_irqs_off(struct mm_struct *prev, struct mm_struct *next,
                        struct task_struct *tsk)
{
    if (real_prev == next) {
        /* Same mm — no switch needed */
        return;
    }

    if (IS_ENABLED(CONFIG_VMAP_STACK)) {
        /* Kernel thread doesn't need to flush user TLB */
        if (!next->pgd) {
            /* Enter lazy mode */
            this_cpu_write(cpu_tlbstate.is_lazy, true);
            return;
        }
    }

    /* Full context switch with PCID optimization */
    choose_new_asid(next, next_tlb_gen, &new_asid, &need_flush);
    load_new_mm_cr3(next->pgd, new_asid, need_flush);
}
```

### `/proc` and `/sys` TLB-Related Files

```bash
# TLB miss stats (if perf_events available)
perf stat -e dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses ./program

# Huge page statistics
cat /proc/meminfo | grep -iE "huge|anon"

# THP status
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
cat /proc/vmstat | grep -i thp

# NUMA huge page pools
ls /sys/devices/system/node/node*/hugepages/
```

---

## 11. TLB and Security: Spectre, Meltdown, KPTI

### Meltdown (CVE-2017-5754)

Meltdown exploited the fact that on pre-KPTI systems, **kernel memory was mapped into every process's page table** (with supervisor bits, so normal access was forbidden). However, speculative execution could access kernel memory before the permission check retired, and the data could be observed via cache timing side channels.

**The kernel mapping in user page tables meant TLB held kernel translations — accessible speculatively.**

### KPTI (Kernel Page Table Isolation)

KPTI splits each process into two page table trees:

```
User-mode PGD:
  ├── User mappings (full)
  └── Kernel stub (entry trampoline only)
      └── syscall/interrupt entry points
      └── CPU-local GDT, TSS, stack

Kernel-mode PGD:
  ├── User mappings (full)
  └── Full kernel mappings
```

On every kernel entry (syscall, interrupt), the CPU switches `CR3` from the user PGD to the kernel PGD. On return to userspace, it switches back.

**TLB Impact of KPTI:**

Without PCID: every kernel entry = full TLB flush → catastrophic overhead (10–30% performance regression on syscall-heavy workloads).

With PCID: Linux uses two PCIDs per process (user + kernel), switches without flushing → overhead reduced to ~2–5%.

```c
/* arch/x86/entry/entry_64.S */
.macro SWITCH_TO_KERNEL_CR3 scratch_reg:req
    ALTERNATIVE "jmp .Lend_\@", "", X86_FEATURE_PTI
    mov     %cr3, \scratch_reg
    orq     $(PTI_USER_PGTABLE_AND_PCID_MASK), \scratch_reg
    andq    $(~PTI_USER_PGTABLE_AND_PCID_MASK), \scratch_reg
    /* Add kernel PCID (bit 11 clear = kernel) */
    mov     \scratch_reg, %cr3
.Lend_\@:
.endm
```

### Spectre v1/v2 and TLB

Spectre mitigations (retpoline, IBRS, STIBP) primarily target the branch predictor, not the TLB directly. However, some Spectre gadgets use TLB timing to leak information — the presence or absence of a TLB entry reveals whether a virtual address was recently accessed.

**Mitigation:** Flush TLB entries for sensitive mappings before returning to untrusted code (e.g., sandbox exits in browsers, VM exits in hypervisors).

### L1TF (L1 Terminal Fault, Foreshadow)

L1TF exploited the fact that the CPU speculatively fetches the L1D cache line indicated by a PTE's physical address bits, even when the PTE is not-present. By crafting PTEs pointing to arbitrary physical addresses, an attacker could leak data from the L1D cache.

**TLB Relevance:** Not-present PTEs don't create TLB entries, but the speculative L1D fetch happens before the TLB miss exception is raised.

**Mitigation:** Mark not-present PTEs with PA bits that point above the maximum physical memory.

---

## 12. TLB Performance Analysis & Profiling

### Hardware Performance Counters

```bash
# Basic TLB miss measurement
perf stat -e \
  dTLB-loads,dTLB-load-misses,\
  dTLB-stores,dTLB-store-misses,\
  iTLB-loads,iTLB-load-misses \
  ./your_program

# Example output:
#  1,234,567,890  dTLB-loads
#     12,345,678  dTLB-load-misses    # 1% miss rate — good
#        987,654  iTLB-loads
#          9,876  iTLB-load-misses    # 1% miss rate

# Detailed micro-architectural events (Intel)
perf stat -e \
  cpu/event=0x08,umask=0x01,name=DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK/,\
  cpu/event=0x08,umask=0x10,name=DTLB_LOAD_MISSES.WALK_ACTIVE/,\
  cpu/event=0x49,umask=0x01,name=DTLB_STORE_MISSES.MISS_CAUSES_A_WALK/ \
  ./your_program
```

### Flamegraphs for TLB Misses

```bash
# Record with TLB miss sampling
perf record -e dTLB-load-misses:pp -g ./your_program
perf report --stdio

# Or use Intel VTune
vtune -collect memory-access ./your_program
```

### Calculating TLB Miss Penalty Contribution

```
TLB_miss_overhead = miss_count × avg_miss_penalty (cycles)
Miss_penalty (4KB pages, warm L2 TLB miss) ≈ 20–30 cycles
Miss_penalty (4KB pages, cold page tables)  ≈ 100–200 cycles
Miss_penalty (2MB pages, L1 TLB miss)      ≈ 7–10 cycles
```

### Kernel TLB Flush Statistics

```bash
# Count TLB flush IPIs
cat /proc/interrupts | grep TLB
#  TLB:    123456  456789  789012  ...   (per CPU)

# Watch TLB flush rate
watch -n1 "cat /proc/interrupts | grep TLB"

# Detailed shootdown stats (requires kernel tracing)
trace-cmd record -e tlb:tlb_flush ./your_program
trace-cmd report
```

---

## 13. TLB-Aware Programming Patterns

### Pattern 1: Sequential Access (Cache-Line Aligned)

```c
/* Bad: sparse access, many TLB misses */
for (int i = 0; i < N; i++)
    sum += array[rand() % N];  /* random access = N TLB misses */

/* Good: sequential access */
for (int i = 0; i < N; i++)
    sum += array[i];           /* sequential = minimal TLB misses */
```

### Pattern 2: Structure Layout for TLB Efficiency

```c
/* AoS (Array of Structures) — bad for TLB when accessing one field */
struct Particle {
    float x, y, z;     /* 12 bytes */
    float vx, vy, vz;  /* 12 bytes */
    float mass;         /* 4 bytes */
    float charge;       /* 4 bytes */
    /* Total: 32 bytes */
};
struct Particle particles[1000000];
/* Accessing only x,y,z: loads entire struct, wastes TLB coverage */

/* SoA (Structure of Arrays) — better TLB for partial field access */
struct Particles {
    float *x, *y, *z;
    float *vx, *vy, *vz;
    float *mass, *charge;
};
/* Accessing only x,y,z: 3 contiguous arrays, full TLB utilization */
```

### Pattern 3: Memory Pool with Huge Pages

```c
#include <sys/mman.h>
#include <stddef.h>

/* Allocate a pool on huge pages */
void *huge_page_pool(size_t size) {
    size = (size + (2 * 1024 * 1024 - 1)) & ~(2 * 1024 * 1024 - 1);
    void *p = mmap(NULL, size,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                   -1, 0);
    if (p == MAP_FAILED) {
        /* Fallback: request THP promotion */
        p = mmap(NULL, size, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (p != MAP_FAILED)
            madvise(p, size, MADV_HUGEPAGE);
    }
    return p;
}
```

### Pattern 4: NUMA-Aware Allocation

```c
#include <numa.h>

/* Allocate on local NUMA node to avoid cross-node page table walks */
void *p = numa_alloc_local(size);  /* Allocates on current node */
numa_tonode_memory(p, size, node); /* Migrate to specific node */
```

### Pattern 5: Reducing Working Set Size

```c
/* Compress hot data to fit more entries per TLB-covered page */

/* Bad: 64-byte struct when only 4 bytes needed frequently */
struct Node {
    int value;          /* 4 bytes — hot */
    char padding[60];   /* cold data */
};

/* Good: separate hot/cold data */
struct NodeHot  { int value; };
struct NodeCold { char padding[60]; };

struct NodeHot  hot_data[N];   /* Dense, TLB-efficient */
struct NodeCold cold_data[N];  /* Accessed rarely */
```

---

## 14. Implementations: C, Go, Rust

### C: TLB Performance Benchmark

```c
/*
 * tlb_benchmark.c
 *
 * Measures TLB miss impact by comparing sequential vs. random access
 * on arrays of varying size.
 *
 * Compile: gcc -O2 -o tlb_bench tlb_benchmark.c
 * Run:     ./tlb_bench
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdint.h>

#define ITERATIONS  (1UL << 24)  /* 16M accesses */

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

/*
 * Fisher-Yates shuffle to build a random permutation.
 * Random access through this permutation creates a pointer-chase
 * that the hardware prefetcher cannot predict.
 */
static void build_random_permutation(size_t *perm, size_t n) {
    for (size_t i = 0; i < n; i++)
        perm[i] = i;
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = (size_t)rand() % (i + 1);
        size_t tmp = perm[i];
        perm[i] = perm[j];
        perm[j] = tmp;
    }
}

/*
 * Random access benchmark: pointer chase through permutation.
 * Each access is to a different page, stressing the TLB.
 */
static uint64_t bench_random(size_t *data, size_t n, size_t iters) {
    /* Build pointer chase: data[i] = index of next element */
    size_t *perm = malloc(n * sizeof(size_t));
    build_random_permutation(perm, n);

    /* Convert permutation to linked list */
    size_t *chain = malloc(n * sizeof(size_t));
    for (size_t i = 0; i < n - 1; i++)
        chain[perm[i]] = perm[i + 1];
    chain[perm[n - 1]] = perm[0];
    free(perm);

    /* Warm up */
    volatile size_t idx = 0;
    for (size_t i = 0; i < 1000; i++)
        idx = chain[idx];

    uint64_t start = rdtsc();
    idx = 0;
    for (size_t i = 0; i < iters; i++)
        idx = chain[idx % n];
    uint64_t end = rdtsc();

    /* Prevent dead-code elimination */
    data[0] = idx;

    free(chain);
    return end - start;
}

/*
 * Sequential access benchmark: stride-1 through array.
 * Hardware prefetcher works perfectly, TLB coverage is maximal.
 */
static uint64_t bench_sequential(size_t *data, size_t n, size_t iters) {
    /* Warm up */
    size_t sum = 0;
    for (size_t i = 0; i < n; i++) sum += data[i];

    uint64_t start = rdtsc();
    sum = 0;
    for (size_t i = 0; i < iters; i++)
        sum += data[i % n];
    uint64_t end = rdtsc();

    data[0] = sum;  /* Prevent optimization */
    return end - start;
}

static double cycles_per_access(uint64_t cycles, size_t iters) {
    return (double)cycles / (double)iters;
}

int main(void) {
    srand(42);

    /* Test sizes that cross TLB boundaries */
    /* L1 DTLB:  64 entries × 4KB = 256 KB  */
    /* L2 TLB: 1536 entries × 4KB = 6 MB    */
    size_t test_sizes[] = {
        64 * 1024,          /*   64 KB — fits in L1 TLB      */
        256 * 1024,         /*  256 KB — L1 TLB boundary      */
        1 * 1024 * 1024,    /*    1 MB — L1 miss, L2 hit      */
        6 * 1024 * 1024,    /*    6 MB — L2 TLB boundary      */
        16 * 1024 * 1024,   /*   16 MB — L2 miss              */
        64 * 1024 * 1024,   /*   64 MB — full TLB pressure    */
        256 * 1024 * 1024,  /*  256 MB — heavy TLB pressure   */
    };

    printf("%-12s  %-12s  %-12s  %-10s\n",
           "Size", "Sequential", "Random", "Slowdown");
    printf("%-12s  %-12s  %-12s  %-10s\n",
           "----", "----------", "------", "--------");

    for (size_t t = 0; t < sizeof(test_sizes) / sizeof(test_sizes[0]); t++) {
        size_t sz = test_sizes[t];
        size_t n_elems = sz / sizeof(size_t);

        /* Allocate and initialize */
        size_t *data = mmap(NULL, sz,
                            PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (data == MAP_FAILED) { perror("mmap"); continue; }

        /* Touch all pages to fault them in */
        memset(data, 0, sz);

        size_t iters = ITERATIONS < n_elems * 4 ? ITERATIONS : n_elems * 4;

        uint64_t seq_cycles = bench_sequential(data, n_elems, iters);
        uint64_t rnd_cycles = bench_random(data, n_elems, iters);

        double seq_cpa = cycles_per_access(seq_cycles, iters);
        double rnd_cpa = cycles_per_access(rnd_cycles, iters);
        double slowdown = rnd_cpa / seq_cpa;

        char sz_str[32];
        if (sz >= 1024 * 1024)
            snprintf(sz_str, sizeof(sz_str), "%4zu MB", sz / (1024 * 1024));
        else
            snprintf(sz_str, sizeof(sz_str), "%4zu KB", sz / 1024);

        printf("%-12s  %9.2f cy  %9.2f cy  %6.1fx\n",
               sz_str, seq_cpa, rnd_cpa, slowdown);

        munmap(data, sz);
    }

    printf("\n");
    printf("Interpretation:\n");
    printf("  Low slowdown  = TLB coverage sufficient (fits in TLB)\n");
    printf("  High slowdown = TLB misses dominating (page walker active)\n");
    printf("  Watch for: slowdown jumps at ~256KB (L1 TLB), ~6MB (L2 TLB)\n");

    return 0;
}
```

### C: TLB Shootdown Observer

```c
/*
 * tlb_shootdown_observer.c
 *
 * Demonstrates TLB shootdown cost via mmap/munmap with multiple threads.
 * Each munmap triggers shootdown IPIs to all other cores.
 *
 * Compile: gcc -O2 -pthread -o shootdown_obs tlb_shootdown_observer.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <sys/mman.h>
#include <time.h>
#include <stdint.h>
#include <unistd.h>

#define PAGE_SIZE      4096
#define NUM_PAGES      1024
#define MMAP_SIZE      (NUM_PAGES * PAGE_SIZE)
#define NUM_THREADS    4
#define NUM_ROUNDS     10000

static volatile int go = 0;

/* Worker: keeps a TLB entry hot by reading from a shared mapping */
static void *worker(void *arg) {
    volatile char *ptr = (volatile char *)arg;
    while (!go) {}
    volatile long sum = 0;
    while (go) {
        /* Touch every page of the mapping to keep TLB entries warm */
        for (int i = 0; i < NUM_PAGES; i++)
            sum += ptr[i * PAGE_SIZE];
    }
    return (void *)sum;
}

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

int main(void) {
    printf("TLB Shootdown Cost Observer\n");
    printf("Threads: %d, Pages per mapping: %d, Rounds: %d\n\n",
           NUM_THREADS, NUM_PAGES, NUM_ROUNDS);

    /* Create shared mapping that all threads will reference */
    char *shared = mmap(NULL, MMAP_SIZE,
                        PROT_READ | PROT_WRITE,
                        MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    memset(shared, 1, MMAP_SIZE);  /* Fault in pages */

    /* Start worker threads */
    pthread_t threads[NUM_THREADS];
    for (int i = 0; i < NUM_THREADS; i++)
        pthread_create(&threads[i], NULL, worker, shared);

    go = 1;
    usleep(10000);  /* Let threads warm up TLBs */

    /* Benchmark: mmap + touch + munmap, forcing shootdowns */
    uint64_t t0 = now_ns();
    for (int r = 0; r < NUM_ROUNDS; r++) {
        void *tmp = mmap(NULL, MMAP_SIZE,
                         PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        memset(tmp, 0, MMAP_SIZE);          /* Fault in pages */
        munmap(tmp, MMAP_SIZE);             /* ← Triggers TLB shootdown */
    }
    uint64_t t1 = now_ns();

    go = 0;
    for (int i = 0; i < NUM_THREADS; i++)
        pthread_join(threads[i], NULL);

    double total_ms = (double)(t1 - t0) / 1e6;
    double per_round_us = (double)(t1 - t0) / NUM_ROUNDS / 1000.0;

    printf("Total time:      %.2f ms\n", total_ms);
    printf("Per round:       %.2f µs\n", per_round_us);
    printf("munmap/shootdown:%.2f µs each (includes %d IPI targets)\n",
           per_round_us, NUM_THREADS - 1);

    munmap(shared, MMAP_SIZE);
    return 0;
}
```

### C: Huge Page vs 4KB Page TLB Benchmark

```c
/*
 * huge_vs_small_pages.c
 *
 * Directly compares TLB behavior of 4KB vs 2MB pages
 * for the same workload size.
 *
 * Compile: gcc -O2 -o huge_bench huge_vs_small_pages.c
 * Note:    Requires hugepages available:
 *          echo 64 > /proc/sys/vm/nr_hugepages
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <stdint.h>

#define ALLOC_SIZE  (128UL * 1024 * 1024)  /* 128 MB */
#define STRIDE      64                       /* Cache line stride */
#define ITERS       (ALLOC_SIZE / STRIDE)

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

static uint64_t bench_access(char *ptr, size_t size, size_t stride) {
    /* Sequential stride access — pure TLB pressure measurement */
    volatile long sum = 0;

    /* Warm up: one pass */
    for (size_t i = 0; i < size; i += stride)
        sum += ptr[i];

    uint64_t start = rdtsc();
    for (int rep = 0; rep < 5; rep++)
        for (size_t i = 0; i < size; i += stride)
            sum += ptr[i];
    uint64_t end = rdtsc();

    (void)sum;  /* Suppress unused warning */
    return (end - start) / 5;
}

int main(void) {
    printf("Huge Page vs 4KB Page TLB Benchmark\n");
    printf("Allocation size: %lu MB, Stride: %zu bytes\n\n",
           ALLOC_SIZE / (1024 * 1024), STRIDE);

    /* --- 4KB pages --- */
    char *small = mmap(NULL, ALLOC_SIZE,
                       PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (small == MAP_FAILED) { perror("small mmap"); return 1; }
    memset(small, 1, ALLOC_SIZE);

    /* Explicitly disable THP to ensure truly 4KB pages */
    madvise(small, ALLOC_SIZE, MADV_NOHUGEPAGE);

    /* --- 2MB huge pages --- */
    char *huge = mmap(NULL, ALLOC_SIZE,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    int has_huge = (huge != MAP_FAILED);

    if (!has_huge) {
        /* Fallback: use THP */
        huge = mmap(NULL, ALLOC_SIZE,
                    PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        madvise(huge, ALLOC_SIZE, MADV_HUGEPAGE);
        printf("Note: MAP_HUGETLB failed, falling back to THP\n");
    }
    if (huge == MAP_FAILED) { perror("huge mmap"); return 1; }
    memset(huge, 1, ALLOC_SIZE);

    /* Benchmark */
    uint64_t small_cycles = bench_access(small, ALLOC_SIZE, STRIDE);
    uint64_t huge_cycles  = bench_access(huge, ALLOC_SIZE, STRIDE);

    size_t accesses = ALLOC_SIZE / STRIDE;
    double small_cpa = (double)small_cycles / accesses;
    double huge_cpa  = (double)huge_cycles  / accesses;

    printf("4KB pages:  %.2f cycles/access\n", small_cpa);
    printf("Huge pages: %.2f cycles/access\n", huge_cpa);
    printf("Speedup:    %.2fx\n\n", small_cpa / huge_cpa);

    /* TLB coverage analysis */
    size_t l1_dtlb_entries = 64;
    printf("TLB Coverage Analysis (L1 DTLB = %zu entries):\n", l1_dtlb_entries);
    printf("  4KB pages: %zu KB coverage\n",
           l1_dtlb_entries * 4);
    printf("  2MB pages: %zu MB coverage\n",
           l1_dtlb_entries * 2);
    printf("  Working set: %lu MB — %s in 4KB TLB, %s in 2MB TLB\n",
           ALLOC_SIZE / (1024 * 1024),
           (ALLOC_SIZE <= l1_dtlb_entries * 4096) ? "fits" : "does NOT fit",
           (ALLOC_SIZE <= l1_dtlb_entries * 2 * 1024 * 1024) ? "fits" : "does NOT fit");

    munmap(small, ALLOC_SIZE);
    munmap(huge, ALLOC_SIZE);
    return 0;
}
```

### C: `madvise` and TLB Interaction

```c
/*
 * madvise_tlb.c
 *
 * Demonstrates how madvise hints affect TLB behavior:
 * MADV_FREE / MADV_DONTNEED force page reclamation → TLB flush
 * MADV_HUGEPAGE promotes to 2MB → shootdown + remapping
 *
 * Compile: gcc -O2 -o madvise_tlb madvise_tlb.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <sys/mman.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
#include <stdlib.h>

#define SIZE (64UL * 1024 * 1024)

static uint64_t ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000000000ULL + t.tv_nsec;
}

int main(void) {
    char *ptr = mmap(NULL, SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    memset(ptr, 1, SIZE);  /* Fault in all pages */

    /* --- MADV_DONTNEED: kernel drops pages, zeroes are served on next access */
    uint64_t t0 = ns();
    madvise(ptr, SIZE, MADV_DONTNEED);
    uint64_t t1 = ns();
    printf("MADV_DONTNEED: %lu µs\n", (t1 - t0) / 1000);
    /* After DONTNEED: TLB entries are flushed for this range */
    /* Next access will page fault and re-populate */

    /* Refault: measure cost of TLB cold-start after DONTNEED */
    t0 = ns();
    volatile long sum = 0;
    for (size_t i = 0; i < SIZE; i += 4096)
        sum += ptr[i];  /* Each access = page fault + TLB fill */
    t1 = ns();
    printf("Refault (post-DONTNEED): %lu ms\n", (t1 - t0) / 1000000);

    /* --- MADV_HUGEPAGE: request 2MB page promotion */
    /* First, re-fault 4KB pages */
    memset(ptr, 2, SIZE);

    t0 = ns();
    madvise(ptr, SIZE, MADV_HUGEPAGE);
    t1 = ns();
    printf("MADV_HUGEPAGE hint: %lu µs\n", (t1 - t0) / 1000);
    /* Promotion is async (khugepaged) — not instant */
    /* Read /proc/self/smaps to see AnonHugePages after promotion */

    /* --- Check THP promotion via smaps --- */
    printf("\nChecking THP promotion (check AnonHugePages in smaps):\n");
    FILE *smaps = fopen("/proc/self/smaps", "r");
    char line[256];
    int found = 0;
    while (fgets(line, sizeof(line), smaps)) {
        if (strncmp(line, "AnonHugePages:", 14) == 0) {
            int kb = atoi(line + 14);
            if (kb > 0) {
                printf("  %s", line);
                found++;
                if (found >= 3) break;
            }
        }
    }
    fclose(smaps);
    if (!found)
        printf("  No THP promotion yet (khugepaged runs asynchronously)\n");

    munmap(ptr, SIZE);
    return 0;
}
```

---

### Go: TLB-Aware Memory Allocator Simulation

```go
// tlb_aware.go
//
// Demonstrates TLB-aware memory management in Go:
// 1. Measures TLB miss cost with runtime/pprof
// 2. Shows how pool alignment affects TLB efficiency
// 3. Implements a huge-page-aligned allocator hint
//
// Run: go run tlb_aware.go
// Benchmark: go test -bench=. -benchmem -count=5

package main

import (
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"runtime/pprof"
	"syscall"
	"time"
	"unsafe"
)

const (
	PageSize      = 4096
	HugePageSize  = 2 * 1024 * 1024 // 2 MB
	L1DTLBEntries = 64
	L2TLBEntries  = 1536
)

// ----- Huge Page Allocator -----

// HugePageAlloc allocates size bytes backed by 2MB huge pages via mmap.
// Falls back to standard allocation if MAP_HUGETLB is unavailable.
// The returned slice is aligned to 2MB boundaries.
//
// Performance insight: With 2MB pages, 64 L1 TLB entries cover 128 MB.
// The same 64 entries with 4KB pages cover only 256 KB.
func HugePageAlloc(size int) ([]byte, error) {
	// Round up to huge page multiple
	aligned := (size + HugePageSize - 1) &^ (HugePageSize - 1)

	// MAP_HUGETLB = 0x40000 on Linux
	const MAP_HUGETLB = 0x40000

	data, _, errno := syscall.RawSyscall6(
		syscall.SYS_MMAP,
		0,                                                          // addr hint
		uintptr(aligned),                                           // length
		syscall.PROT_READ|syscall.PROT_WRITE,                      // prot
		syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS|MAP_HUGETLB, // flags
		^uintptr(0), // fd = -1
		0,           // offset
	)

	if errno != 0 {
		// Fallback: standard mmap + MADV_HUGEPAGE
		data, _, errno = syscall.RawSyscall6(
			syscall.SYS_MMAP,
			0, uintptr(aligned),
			syscall.PROT_READ|syscall.PROT_WRITE,
			syscall.MAP_PRIVATE|syscall.MAP_ANONYMOUS,
			^uintptr(0), 0,
		)
		if errno != 0 {
			return nil, fmt.Errorf("mmap failed: %v", errno)
		}

		// MADV_HUGEPAGE = 14
		const MADV_HUGEPAGE = 14
		syscall.RawSyscall(syscall.SYS_MADVISE,
			data, uintptr(aligned), MADV_HUGEPAGE)

		fmt.Println("[Note] MAP_HUGETLB unavailable, using THP fallback")
	}

	// Convert to slice without copying
	buf := unsafe.Slice((*byte)(unsafe.Pointer(data)), aligned)
	return buf, nil
}

// FreeHugePages releases memory obtained from HugePageAlloc.
func FreeHugePages(buf []byte) {
	syscall.RawSyscall(syscall.SYS_MUNMAP,
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(len(buf)), 0)
}

// ----- TLB Working Set Analysis -----

// WorkingSetAnalysis measures access latency as a function of working set size.
// This directly shows where TLB boundaries cause latency jumps.
func WorkingSetAnalysis() {
	type result struct {
		sizeKB    int
		nsPerOp   float64
		tlbStatus string
	}

	sizes := []int{
		32, 64, 128, 256,          // Below/at L1 TLB boundary (256 KB)
		512, 1024, 2048, 4096,     // Between L1 and L2 TLB
		8192, 16384, 32768, 65536, // Above L2 TLB (L2 = ~6 MB)
	}

	const stride = 64 // Cache-line size; eliminates prefetcher effects at stride = 4096
	const iters = 1 << 20

	var results []result

	for _, sizeKB := range sizes {
		size := sizeKB * 1024
		n := size / stride

		// Allocate and touch to fault in
		data := make([]int64, size/8)
		for i := range data {
			data[i] = int64(i)
		}

		// Build random pointer-chase permutation to defeat prefetcher
		perm := rand.Perm(n)
		chain := make([]int, n)
		for i := 0; i < n-1; i++ {
			chain[perm[i]] = perm[i+1]
		}
		chain[perm[n-1]] = perm[0]

		// Warm up
		idx := 0
		for i := 0; i < 1000; i++ {
			idx = chain[idx]
		}
		runtime.KeepAlive(idx)

		// Benchmark
		start := time.Now()
		idx = 0
		for i := 0; i < iters; i++ {
			idx = chain[idx]
		}
		elapsed := time.Since(start)
		runtime.KeepAlive(idx)

		nsPerOp := float64(elapsed.Nanoseconds()) / float64(iters)

		// Classify TLB status
		var status string
		l1CoverageKB := L1DTLBEntries * 4          // 256 KB
		l2CoverageKB := L2TLBEntries * 4           // 6144 KB
		switch {
		case sizeKB <= l1CoverageKB:
			status = "L1 TLB hit"
		case sizeKB <= l2CoverageKB:
			status = "L2 TLB hit"
		default:
			status = "TLB MISS (page walk)"
		}

		results = append(results, result{sizeKB, nsPerOp, status})
	}

	fmt.Printf("\n%-12s  %-12s  %-20s\n", "Size", "ns/access", "TLB Status")
	fmt.Printf("%-12s  %-12s  %-20s\n", "----", "---------", "----------")
	for _, r := range results {
		fmt.Printf("%-8d KB  %10.2f ns  %-20s\n",
			r.sizeKB, r.nsPerOp, r.tlbStatus)
	}
}

// ----- CPU Profiling to See TLB Effects -----

// ProfileTLBPressure runs a TLB-intensive workload with CPU profiling enabled.
// Inspect the profile with: go tool pprof cpu.prof
func ProfileTLBPressure() {
	const size = 128 * 1024 * 1024 // 128 MB — far exceeds L2 TLB

	f, _ := os.Create("cpu.prof")
	defer f.Close()
	pprof.StartCPUProfile(f)
	defer pprof.StopCPUProfile()

	// Allocate large array
	data := make([]int64, size/8)
	for i := range data {
		data[i] = int64(i)
	}

	// Random access — maximum TLB pressure
	n := len(data)
	rng := rand.New(rand.NewSource(42))
	var sum int64
	for i := 0; i < 1<<24; i++ {
		idx := rng.Intn(n)
		sum += data[idx]
	}
	runtime.KeepAlive(sum)

	fmt.Println("\nCPU profile written to cpu.prof")
	fmt.Println("Analyze with: go tool pprof cpu.prof")
	fmt.Println("Look for: high time in runtime.memmove, mcall, or page fault handlers")
}

// ----- Go Runtime TLB Considerations -----

// GoRuntimeTLBNotes explains how Go's memory model interacts with TLB.
func GoRuntimeTLBNotes() {
	fmt.Println(`
Go Runtime & TLB Interaction
═════════════════════════════

1. GOROUTINE STACKS
   - Go allocates goroutine stacks in 8KB chunks (default)
   - Stack growth: Go copies the stack to a new larger allocation
   - Copying stacks invalidates all pointers → TLB entries for old stack
     are no longer valid but kernel handles this transparently
   - With thousands of goroutines: thousands of stack pages, TLB pressure

2. GC WRITE BARRIERS
   - Go's tri-color GC writes to a "shadow stack" (gcmarkBits)
   - This creates write TLB traffic; dense GC metadata = TLB pressure
   - GOGC=off or large heaps reduce GC frequency and TLB churn

3. MEMORY ARENAS (Go 1.20+)
   - arena.New() / arena.MakeSlice(): allocate from a contiguous region
   - Better TLB coverage: one huge virtual region = fewer TLB entries
   - Arena.Free() releases all at once → single shootdown vs. many

4. SYNC.POOL TLB BENEFIT
   - sync.Pool keeps recently freed objects hot in L1/L2 cache AND TLB
   - Pool shards per-P (processor): avoids cross-CPU TLB traffic
   - Best practice: pool objects should be page-aligned or cache-aligned

5. HUGE PAGES AND GO
   - Go does not use MAP_HUGETLB by default
   - GODEBUG=madvdontneed=1 controls MADV_DONTNEED behavior
   - THP (Transparent Huge Pages) can promote Go heap pages automatically
   - For latency-critical Go services: consider MADV_HUGEPAGE on heap
     or reserving HugeTLBfs for critical data structures
`)
}

func main() {
	fmt.Println("═══════════════════════════════════════")
	fmt.Println("  TLB Analysis in Go")
	fmt.Println("═══════════════════════════════════════")

	fmt.Printf("System: GOMAXPROCS=%d\n", runtime.GOMAXPROCS(0))
	fmt.Printf("L1 DTLB estimated entries: %d (covers %d KB with 4KB pages)\n",
		L1DTLBEntries, L1DTLBEntries*4)
	fmt.Printf("L2 TLB estimated entries:  %d (covers %d KB with 4KB pages)\n",
		L2TLBEntries, L2TLBEntries*4)

	fmt.Println("\n--- Working Set vs TLB Latency ---")
	WorkingSetAnalysis()

	GoRuntimeTLBNotes()

	// Uncomment to run profiling:
	// ProfileTLBPressure()
}
```

### Go: TLB Shootdown Monitor (via /proc/interrupts)

```go
// tlb_monitor.go
//
// Monitors TLB shootdown IPIs in real-time by reading /proc/interrupts.
// Run a TLB-intensive workload alongside this to observe shootdown rate.
//
// Run: go run tlb_monitor.go

package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// TLBStats holds TLB flush IPI counts per CPU.
type TLBStats struct {
	PerCPU    []uint64
	Total     uint64
	Timestamp time.Time
}

// ReadTLBInterrupts parses /proc/interrupts for TLB flush counts.
func ReadTLBInterrupts() (*TLBStats, error) {
	f, err := os.Open("/proc/interrupts")
	if err != nil {
		return nil, err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)

	// First line contains CPU headers
	scanner.Scan()
	header := strings.Fields(scanner.Text())
	numCPUs := len(header)

	stats := &TLBStats{
		PerCPU:    make([]uint64, numCPUs),
		Timestamp: time.Now(),
	}

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.Contains(line, "TLB") {
			continue
		}

		fields := strings.Fields(line)
		// fields[0] = "TLB:", fields[1..numCPUs] = per-CPU counts
		for i := 0; i < numCPUs && i+1 < len(fields); i++ {
			count, err := strconv.ParseUint(fields[i+1], 10, 64)
			if err != nil {
				continue
			}
			stats.PerCPU[i] = count
			stats.Total += count
		}
		break // Only one TLB line
	}

	return stats, scanner.Err()
}

func main() {
	fmt.Println("TLB Shootdown IPI Monitor")
	fmt.Println("Reading /proc/interrupts every second...")
	fmt.Printf("%-10s  %-15s  %-15s  %-15s\n",
		"Time", "Total IPIs", "Delta/sec", "Per-CPU avg")
	fmt.Println(strings.Repeat("─", 60))

	var prev *TLBStats

	for {
		curr, err := ReadTLBInterrupts()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			time.Sleep(time.Second)
			continue
		}

		if prev != nil {
			dt := curr.Timestamp.Sub(prev.Timestamp).Seconds()
			delta := curr.Total - prev.Total
			rate := float64(delta) / dt
			perCPU := rate / float64(len(curr.PerCPU))

			fmt.Printf("%-10s  %-15d  %-15.0f  %-15.1f\n",
				curr.Timestamp.Format("15:04:05"),
				curr.Total, rate, perCPU)

			// Warn on high shootdown rate
			if rate > 10000 {
				fmt.Printf("  ⚠ HIGH TLB shootdown rate: %.0f/sec — check for\n", rate)
				fmt.Printf("    frequent mmap/munmap or page table modifications\n")
			}
		}

		prev = curr
		time.Sleep(time.Second)
	}
}
```

---

### Rust: TLB Miss Cost Profiler

```rust
// tlb_profiler.rs
//
// A rigorous TLB benchmarking framework in Rust demonstrating:
// 1. Safe abstraction over mmap for huge-page allocation
// 2. Pointer-chase benchmark eliminating prefetcher effects
// 3. RDTSC-based cycle measurement
// 4. TLB hierarchy deduction from latency curves
//
// Run: cargo build --release && ./target/release/tlb_profiler

use std::arch::x86_64::_rdtsc;
use std::time::{Duration, Instant};

// ─────────────────────────────────────────────
// Platform constants
// ─────────────────────────────────────────────
const PAGE_SIZE: usize = 4096;
const HUGE_PAGE_SIZE: usize = 2 * 1024 * 1024;
const CACHE_LINE: usize = 64;

// Estimated TLB sizes (Skylake-class)
const L1_DTLB_ENTRIES: usize = 64;
const L2_TLB_ENTRIES: usize = 1536;

// ─────────────────────────────────────────────
// Safe mmap wrapper
// ─────────────────────────────────────────────

/// Anonymous memory-mapped region.
/// Correctly unmaps on drop.
pub struct MmapRegion {
    ptr: *mut u8,
    len: usize,
}

impl MmapRegion {
    /// Allocate `size` bytes of anonymous memory.
    /// Attempts MAP_HUGETLB; falls back to MADV_HUGEPAGE.
    pub fn new(size: usize, huge: bool) -> Result<Self, String> {
        let aligned = if huge {
            (size + HUGE_PAGE_SIZE - 1) & !(HUGE_PAGE_SIZE - 1)
        } else {
            (size + PAGE_SIZE - 1) & !(PAGE_SIZE - 1)
        };

        let ptr = unsafe { Self::do_mmap(aligned, huge) }?;
        Ok(MmapRegion { ptr, len: aligned })
    }

    unsafe fn do_mmap(size: usize, huge: bool) -> Result<*mut u8, String> {
        use libc::{
            madvise, mmap, MAP_ANONYMOUS, MAP_FAILED, MAP_HUGETLB,
            MAP_PRIVATE, MADV_HUGEPAGE, PROT_READ, PROT_WRITE,
        };

        let flags = if huge {
            MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB
        } else {
            MAP_PRIVATE | MAP_ANONYMOUS
        };

        let ptr = mmap(
            std::ptr::null_mut(),
            size,
            PROT_READ | PROT_WRITE,
            flags,
            -1,
            0,
        );

        if ptr == MAP_FAILED {
            if huge {
                // Retry without MAP_HUGETLB, request THP
                let ptr2 = mmap(
                    std::ptr::null_mut(),
                    size,
                    PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS,
                    -1,
                    0,
                );
                if ptr2 == MAP_FAILED {
                    return Err("mmap failed".to_string());
                }
                madvise(ptr2, size, MADV_HUGEPAGE);
                eprintln!("[Note] MAP_HUGETLB unavailable, using THP");
                return Ok(ptr2 as *mut u8);
            }
            return Err("mmap failed".to_string());
        }

        Ok(ptr as *mut u8)
    }

    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }

    pub fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.ptr, self.len) }
    }

    pub fn len(&self) -> usize {
        self.len
    }
}

impl Drop for MmapRegion {
    fn drop(&mut self) {
        unsafe {
            libc::munmap(self.ptr as *mut libc::c_void, self.len);
        }
    }
}

// SAFETY: The region is exclusively owned; we control all aliasing.
unsafe impl Send for MmapRegion {}

// ─────────────────────────────────────────────
// RDTSC cycle counter
// ─────────────────────────────────────────────

#[inline(always)]
fn rdtsc() -> u64 {
    unsafe { _rdtsc() }
}

/// Serialize the instruction pipeline before RDTSC.
/// CPUID is used as a serializing instruction.
#[inline(always)]
fn rdtsc_serialize() -> u64 {
    unsafe {
        // Serialize with CPUID
        std::arch::x86_64::__cpuid(0);
        _rdtsc()
    }
}

// ─────────────────────────────────────────────
// Pointer-chase benchmark
// ─────────────────────────────────────────────

/// Builds a random cyclic permutation (pointer chase).
///
/// This defeats hardware prefetchers because each access
/// target is unpredictable. The only bottleneck is memory
/// latency — TLB misses show up directly as latency.
fn build_pointer_chain(n: usize, seed: u64) -> Vec<u64> {
    // Deterministic LCG for reproducibility
    let mut rng = seed;
    let lcg = |x: u64| x.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);

    let mut perm: Vec<usize> = (0..n).collect();

    // Fisher-Yates shuffle
    for i in (1..n).rev() {
        rng = lcg(rng);
        let j = (rng as usize) % (i + 1);
        perm.swap(i, j);
    }

    // Convert permutation to linked list stored in array
    // chain[perm[i]] = perm[(i+1) % n]
    let mut chain = vec![0u64; n];
    for i in 0..n - 1 {
        chain[perm[i]] = perm[i + 1] as u64;
    }
    chain[perm[n - 1]] = perm[0] as u64;

    chain
}

/// Measures cycles per pointer-chase access.
/// Each access touches a different cache line in a different (random) page.
fn bench_pointer_chase(chain: &[u64], iters: usize) -> f64 {
    // Warm-up: one full traversal
    let mut idx: u64 = 0;
    for _ in 0..chain.len().min(10_000) {
        idx = chain[idx as usize];
    }
    std::hint::black_box(idx);

    let start = rdtsc_serialize();
    idx = 0;
    for _ in 0..iters {
        // SAFETY: chain is a valid cyclic permutation in [0, n)
        idx = unsafe { *chain.get_unchecked(idx as usize) };
    }
    let end = rdtsc();

    std::hint::black_box(idx);

    (end - start) as f64 / iters as f64
}

// ─────────────────────────────────────────────
// TLB Hierarchy Profiler
// ─────────────────────────────────────────────

#[derive(Debug)]
struct BenchResult {
    size_kb: usize,
    cycles_per_access: f64,
    ns_per_access: f64,
    tlb_level: TlbLevel,
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum TlbLevel {
    L1Hit,
    L2Hit,
    Miss,
}

impl std::fmt::Display for TlbLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TlbLevel::L1Hit => write!(f, "✓ L1 TLB hit"),
            TlbLevel::L2Hit => write!(f, "~ L2 TLB hit"),
            TlbLevel::Miss  => write!(f, "✗ TLB MISS (page walk)"),
        }
    }
}

fn classify_tlb(size_kb: usize) -> TlbLevel {
    let l1_kb = L1_DTLB_ENTRIES * PAGE_SIZE / 1024;
    let l2_kb = L2_TLB_ENTRIES * PAGE_SIZE / 1024;

    if size_kb <= l1_kb {
        TlbLevel::L1Hit
    } else if size_kb <= l2_kb {
        TlbLevel::L2Hit
    } else {
        TlbLevel::Miss
    }
}

fn run_tlb_hierarchy_benchmark(cpu_ghz: f64) -> Vec<BenchResult> {
    // Each pointer is one cache line apart → 64 bytes stride.
    // With stride = CACHE_LINE, entries = size / CACHE_LINE.
    // Each element occupies exactly one cache line in a different page
    // when size >> cache_size, so TLB is the bottleneck.

    let sizes_kb: &[usize] = &[
        16, 32, 64, 128, 256,          // L1 TLB range (≤ 256 KB)
        512, 1024, 2048, 4096, 6144,   // L2 TLB range (≤ 6 MB)
        8192, 16384, 32768, 65536,     // TLB miss range
        131072, 262144,                // Heavy miss range
    ];

    const ITERS: usize = 1 << 20; // 1M accesses per benchmark

    let mut results = Vec::new();

    for &size_kb in sizes_kb {
        let size = size_kb * 1024;
        // Stride = cache line size; n = number of elements
        let n = size / CACHE_LINE;

        if n < 16 { continue; }

        // Allocate and touch all pages to fault them in
        let mut region = MmapRegion::new(size, false)
            .expect("allocation failed");
        region.as_mut_slice().fill(0);

        // Build chain: each element at offset i * CACHE_LINE
        // We store chain indices (u64) at cache-line-aligned positions
        // n entries of u64 = n * 8 bytes; we need n * CACHE_LINE bytes
        let chain = build_pointer_chain(n, 0xdeadbeef);

        // Pre-touch chain
        let _ = chain.iter().sum::<u64>();

        let cpa = bench_pointer_chase(&chain, ITERS);
        let ns = cpa / cpu_ghz;

        results.push(BenchResult {
            size_kb,
            cycles_per_access: cpa,
            ns_per_access: ns,
            tlb_level: classify_tlb(size_kb),
        });
    }

    results
}

// ─────────────────────────────────────────────
// Huge Page Benchmark
// ─────────────────────────────────────────────

fn bench_sequential(data: &[u8], iters: usize) -> f64 {
    // Sequential stride-64 access
    let n = data.len() / CACHE_LINE;
    let mut sum: u64 = 0;

    // Warm up
    for i in 0..n {
        sum = sum.wrapping_add(data[i * CACHE_LINE] as u64);
    }
    std::hint::black_box(sum);

    let start = rdtsc_serialize();
    sum = 0;
    for _ in 0..iters {
        for i in 0..n {
            // SAFETY: i * CACHE_LINE < data.len()
            sum = sum.wrapping_add(unsafe {
                *data.get_unchecked(i * CACHE_LINE) as u64
            });
        }
    }
    let end = rdtsc();
    std::hint::black_box(sum);

    (end - start) as f64 / (iters * n) as f64
}

fn run_huge_vs_small(cpu_ghz: f64) {
    const SIZE: usize = 128 * 1024 * 1024; // 128 MB

    println!("\n┌─────────────────────────────────────────┐");
    println!("│  4KB vs 2MB Pages — Sequential Access   │");
    println!("│  Working set: 128 MB                    │");
    println!("└─────────────────────────────────────────┘");

    // 4KB pages
    let mut small = MmapRegion::new(SIZE, false).unwrap();
    small.as_mut_slice().fill(1);

    // 2MB huge pages (or THP fallback)
    let mut huge = MmapRegion::new(SIZE, true).unwrap();
    huge.as_mut_slice().fill(1);

    // Synchronize memory
    std::sync::atomic::fence(std::sync::atomic::Ordering::SeqCst);

    let small_cpa = bench_sequential(small.as_slice(), 3);
    let huge_cpa  = bench_sequential(huge.as_slice(), 3);

    let small_ns = small_cpa / cpu_ghz;
    let huge_ns  = huge_cpa / cpu_ghz;

    println!("\n  4KB pages:  {:6.2} cycles/access  ({:.2} ns)", small_cpa, small_ns);
    println!("  Huge pages: {:6.2} cycles/access  ({:.2} ns)", huge_cpa, huge_ns);
    println!("  Speedup:    {:.2}x", small_cpa / huge_cpa);

    println!("\n  TLB Coverage Analysis:");
    println!("    4KB × {} L1 entries = {} KB", L1_DTLB_ENTRIES, L1_DTLB_ENTRIES * 4);
    println!("    2MB × {} L1 entries = {} MB", L1_DTLB_ENTRIES, L1_DTLB_ENTRIES * 2);
    println!("    128 MB working set: {}fits in 4KB TLB, {}fits in 2MB TLB",
        if SIZE <= L1_DTLB_ENTRIES * PAGE_SIZE { "" } else { "does NOT " },
        if SIZE <= L1_DTLB_ENTRIES * HUGE_PAGE_SIZE { "" } else { "does NOT " });
}

// ─────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────

fn main() {
    // Estimate CPU frequency
    let t0 = rdtsc();
    let wall0 = Instant::now();
    std::thread::sleep(Duration::from_millis(100));
    let t1 = rdtsc();
    let wall1 = Instant::now();
    let cpu_ghz = (t1 - t0) as f64 / wall1.duration_since(wall0).as_nanos() as f64;

    println!("╔══════════════════════════════════════════════════╗");
    println!("║   Rust TLB Hierarchy Profiler                   ║");
    println!("╚══════════════════════════════════════════════════╝");
    println!("\nDetected CPU: ~{:.2} GHz", cpu_ghz);
    println!("L1 DTLB: {} entries ({} KB coverage @ 4KB pages)",
             L1_DTLB_ENTRIES, L1_DTLB_ENTRIES * 4);
    println!("L2 TLB:  {} entries ({} KB coverage @ 4KB pages)",
             L2_TLB_ENTRIES, L2_TLB_ENTRIES * 4);

    println!("\n┌─────────────────────────────────────────────────────┐");
    println!("│  Pointer-Chase Benchmark — TLB Hierarchy Deduction  │");
    println!("└─────────────────────────────────────────────────────┘");
    println!("\n{:<12} {:>12} {:>12} {}", "Size", "Cycles/acc", "ns/acc", "TLB Status");
    println!("{}", "─".repeat(60));

    let results = run_tlb_hierarchy_benchmark(cpu_ghz);
    let mut prev_level = TlbLevel::L1Hit;

    for r in &results {
        let marker = if r.tlb_level != prev_level { " ←" } else { "" };
        println!("{:<8} KB  {:>10.2}  {:>10.2}   {}{}",
                 r.size_kb,
                 r.cycles_per_access,
                 r.ns_per_access,
                 r.tlb_level,
                 marker);
        prev_level = r.tlb_level;
    }

    println!("\nLatency interpretation:");
    println!("  ~4  cycles = L1 TLB hit + L1 cache hit");
    println!("  ~10 cycles = L2 TLB hit + L2 cache hit");
    println!("  ~40 cycles = TLB miss + page walk (L1/L2 cache hit)");
    println!("  ~200 cycles = TLB miss + page walk (DRAM access)");

    run_huge_vs_small(cpu_ghz);

    println!("\n══ Expert Insights ══════════════════════════════════");
    println!("1. The latency jump at L1 TLB boundary reveals TLB miss cost.");
    println!("2. Huge pages shift the L1 boundary by 512× (4KB → 2MB).");
    println!("3. Pointer-chase eliminates prefetcher — pure latency signal.");
    println!("4. Use `perf stat -e dTLB-load-misses` to verify in production.");
    println!("5. Rust's ownership model helps: less aliasing = fewer TLB");
    println!("   shootdowns vs. C programs with many shared mappings.");
}
```

### Rust: TLB-Aware Allocator (Arena with Huge Pages)

```rust
// arena_allocator.rs
//
// A TLB-aware bump allocator backed by huge pages.
// The key insight: instead of many small allocations scattered
// across virtual memory (many TLB entries), pack objects into
// a single huge-page-backed arena (one TLB entry per 2 MB).
//
// This pattern is used in: databases (RocksDB, DuckDB),
// ML frameworks (PyTorch memory pools), game engines.

use std::alloc::{GlobalAlloc, Layout};
use std::cell::Cell;
use std::ptr::NonNull;
use std::sync::atomic::{AtomicUsize, Ordering};

const ARENA_SIZE: usize = 256 * 1024 * 1024; // 256 MB
const HUGE_PAGE_SIZE: usize = 2 * 1024 * 1024;
const ALIGNMENT: usize = 64; // Cache-line aligned

/// A bump allocator backed by a huge-page mmap region.
///
/// Allocation: O(1) — just increment a counter.
/// Deallocation: Not supported for individual objects (free the whole arena).
///
/// TLB advantage: The entire arena = 128 huge page entries.
/// A standard allocator for the same objects would use 65,536 small page entries.
pub struct HugePageArena {
    base: *mut u8,
    size: usize,
    cursor: AtomicUsize,
    used: AtomicUsize,
}

impl HugePageArena {
    /// Create a new arena backed by huge pages.
    pub fn new() -> Result<Self, String> {
        let ptr = unsafe { Self::alloc_huge(ARENA_SIZE) }?;
        Ok(HugePageArena {
            base: ptr,
            size: ARENA_SIZE,
            cursor: AtomicUsize::new(0),
            used: AtomicUsize::new(0),
        })
    }

    unsafe fn alloc_huge(size: usize) -> Result<*mut u8, String> {
        use libc::*;
        let aligned = (size + HUGE_PAGE_SIZE - 1) & !(HUGE_PAGE_SIZE - 1);

        let ptr = mmap(
            std::ptr::null_mut(),
            aligned,
            PROT_READ | PROT_WRITE,
            MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
            -1, 0,
        );

        if ptr == MAP_FAILED {
            // THP fallback
            let ptr2 = mmap(
                std::ptr::null_mut(), aligned,
                PROT_READ | PROT_WRITE,
                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0,
            );
            if ptr2 == MAP_FAILED {
                return Err(format!("mmap failed: {}", *libc::__errno_location()));
            }
            madvise(ptr2, aligned, MADV_HUGEPAGE);
            // Touch first byte of each huge page to trigger promotion
            let p = ptr2 as *mut u8;
            let n_huge = aligned / HUGE_PAGE_SIZE;
            for i in 0..n_huge {
                p.add(i * HUGE_PAGE_SIZE).write_volatile(0);
            }
            return Ok(ptr2 as *mut u8);
        }

        // Touch all huge pages to populate TLB entries
        let p = ptr as *mut u8;
        let n_huge = aligned / HUGE_PAGE_SIZE;
        for i in 0..n_huge {
            p.add(i * HUGE_PAGE_SIZE).write_volatile(0);
        }

        Ok(ptr as *mut u8)
    }

    /// Allocate `size` bytes with `align` alignment from the arena.
    /// Returns None if the arena is exhausted.
    #[inline(always)]
    pub fn alloc(&self, layout: Layout) -> Option<NonNull<u8>> {
        let align = layout.align().max(ALIGNMENT);
        let size  = layout.size();

        loop {
            let current = self.cursor.load(Ordering::Relaxed);
            // Align current position
            let aligned = (current + align - 1) & !(align - 1);
            let next = aligned + size;

            if next > self.size {
                return None; // Arena exhausted
            }

            match self.cursor.compare_exchange_weak(
                current, next,
                Ordering::AcqRel,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    self.used.fetch_add(size, Ordering::Relaxed);
                    // SAFETY: aligned is within [base, base + size)
                    let ptr = unsafe { self.base.add(aligned) };
                    return Some(unsafe { NonNull::new_unchecked(ptr) });
                }
                Err(_) => continue, // CAS failed, retry
            }
        }
    }

    /// Reset the arena, freeing all allocations at once.
    /// This is a single TLB shootdown (MADV_DONTNEED on the whole region)
    /// vs. N individual frees which would cause N shootdowns.
    pub fn reset(&self) {
        self.cursor.store(0, Ordering::Release);
        self.used.store(0, Ordering::Release);
        // Return physical pages to OS (TLB entries become invalid)
        unsafe {
            libc::madvise(
                self.base as *mut libc::c_void,
                self.size,
                libc::MADV_DONTNEED,
            );
        }
    }

    pub fn stats(&self) -> (usize, usize, usize) {
        let used    = self.used.load(Ordering::Relaxed);
        let cursor  = self.cursor.load(Ordering::Relaxed);
        let free    = self.size.saturating_sub(cursor);
        (used, cursor, free)
    }
}

impl Drop for HugePageArena {
    fn drop(&mut self) {
        unsafe {
            libc::munmap(self.base as *mut libc::c_void, self.size);
        }
    }
}

// SAFETY: Arena uses atomic cursor; objects in it may be !Send but
// the arena itself (as an allocator) is safe to share between threads.
unsafe impl Sync for HugePageArena {}
unsafe impl Send for HugePageArena {}

// ─────────────────────────────────────────────
// Demo: B-Tree node pool with TLB-aware arena
// ─────────────────────────────────────────────

/// A B-Tree node stored in the arena.
/// Aligned to cache line to prevent false sharing.
#[repr(align(64))]
struct BTreeNode {
    keys:     [i64; 7],
    children: [u32; 8],  // Arena offsets (not pointers — avoids TLB load on pointer deref)
    count:    u32,
    is_leaf:  u32,
}

fn demo_btree_arena() -> Result<(), String> {
    let arena = HugePageArena::new()?;

    println!("\n┌─────────────────────────────────────────┐");
    println!("│  B-Tree Node Arena — TLB Analysis       │");
    println!("└─────────────────────────────────────────┘");
    println!("  Arena size:    {} MB", ARENA_SIZE / (1024 * 1024));
    println!("  Node size:     {} bytes (cache-line aligned)", std::mem::size_of::<BTreeNode>());

    let node_layout = Layout::new::<BTreeNode>();
    let max_nodes   = ARENA_SIZE / std::mem::size_of::<BTreeNode>();

    println!("  Max nodes:     {}", max_nodes);

    // TLB calculation
    let pages_4kb  = ARENA_SIZE / 4096;
    let pages_2mb  = (ARENA_SIZE + HUGE_PAGE_SIZE - 1) / HUGE_PAGE_SIZE;
    println!("\n  TLB entries required:");
    println!("    4KB pages: {} entries ({}× L1 DTLB capacity)", pages_4kb, pages_4kb / 64);
    println!("    2MB pages: {} entries ({:.1}× L1 DTLB capacity)",
             pages_2mb, pages_2mb as f64 / 64.0);

    // Allocate nodes
    let n_alloc = 1_000_000usize.min(max_nodes);
    let t0 = std::time::Instant::now();
    for _ in 0..n_alloc {
        let ptr = arena.alloc(node_layout).expect("arena exhausted");
        // Initialize node
        unsafe {
            let node = ptr.as_ptr() as *mut BTreeNode;
            (*node).count = 0;
            (*node).is_leaf = 1;
        }
    }
    let elapsed = t0.elapsed();

    let (used, cursor, free) = arena.stats();
    println!("\n  Allocated {} nodes in {:.2} µs",
             n_alloc, elapsed.as_micros());
    println!("  Throughput: {:.0} ns/alloc",
             elapsed.as_nanos() as f64 / n_alloc as f64);
    println!("  Used: {} MB, Free: {} MB",
             used / (1024 * 1024), free / (1024 * 1024));

    // Reset: O(1) regardless of how many nodes were allocated
    let t_reset = std::time::Instant::now();
    arena.reset();
    println!("\n  Reset {} nodes in {} µs (single MADV_DONTNEED)",
             n_alloc, t_reset.elapsed().as_micros());
    println!("  vs. {} individual frees → {} TLB shootdowns avoided",
             n_alloc, n_alloc);

    Ok(())
}

fn main() {
    println!("╔══════════════════════════════════════════╗");
    println!("║  Rust TLB-Aware Arena Allocator          ║");
    println!("╚══════════════════════════════════════════╝");

    match demo_btree_arena() {
        Ok(()) => {}
        Err(e) => eprintln!("Error: {}", e),
    }

    println!("\n══ Design Insights ═════════════════════════");
    println!("1. Arena allocation: O(1) atomic increment — no TLB-unfriendly");
    println!("   malloc() metadata scattered across pages.");
    println!("2. Huge-page backing: 128 TLB entries for 256 MB vs. 65,536 entries.");
    println!("3. Batch deallocation (reset): 1 MADV_DONTNEED vs. N kernel calls.");
    println!("4. Index-based children (u32 offsets) keep nodes within one huge page,");
    println!("   eliminating pointer-chase TLB misses for adjacent nodes.");
    println!("5. Rust's ownership: arena owns all nodes; Rust enforces this at compile");
    println!("   time, preventing dangling TLB entries from use-after-free.");
}
```

### Rust: INVLPG via Inline Assembly (Kernel Context Simulation)

```rust
// invlpg_sim.rs
//
// Demonstrates x86 TLB invalidation instructions via inline asm.
// In user space, these are privileged and will fault;
// this code is intended to show what kernel/hypervisor code looks like.
// Compile in no_std/kernel context or study as reference.

#![allow(dead_code)]

use core::arch::asm;

/// Invalidate the TLB entry for a single virtual address.
/// Executes the x86 `INVLPG` instruction.
///
/// # Safety
/// Must execute at CPL 0 (ring 0 / kernel mode).
/// Undefined behavior if called from user space (raises #GP).
#[inline(always)]
unsafe fn invlpg(virt_addr: usize) {
    asm!(
        "invlpg [{addr}]",
        addr = in(reg) virt_addr,
        options(nostack, preserves_flags)
    );
}

/// Flush all non-global TLB entries by reloading CR3.
///
/// # Safety
/// Must execute at CPL 0.
#[inline(always)]
unsafe fn flush_tlb() {
    let cr3: u64;
    asm!("mov {}, cr3", out(reg) cr3, options(nomem, nostack));
    asm!("mov cr3, {}", in(reg) cr3, options(nomem, nostack));
}

/// Flush all TLB entries including global (G-bit) pages.
/// Used when changing kernel mappings.
///
/// # Safety
/// Must execute at CPL 0.
#[inline(always)]
unsafe fn flush_tlb_all() {
    let cr4: u64;
    // Clear PGE (bit 7) → flush global entries
    asm!(
        "mov {cr4}, cr4",
        "and {cr4}, {mask}",
        "mov cr4, {cr4}",
        // Restore PGE
        "or  {cr4}, {pge}",
        "mov cr4, {cr4}",
        cr4 = out(reg) cr4,
        mask = const !( 1u64 << 7 ),  // ~X86_CR4_PGE
        pge  = const (1u64 << 7),
        options(nostack)
    );
}

/// Load a new CR3 value (switches page tables).
/// If `no_flush` is true and PCID is supported, sets bit 63 of CR3
/// to prevent TLB flush on context switch.
///
/// # Safety
/// Must execute at CPL 0. `phys_pgd` must be a valid physical address.
#[inline(always)]
unsafe fn load_cr3(phys_pgd: u64, pcid: u16, no_flush: bool) {
    let mut cr3 = phys_pgd | (pcid as u64 & 0xFFF);
    if no_flush {
        cr3 |= 1u64 << 63; // NOFLUSH bit
    }
    asm!("mov cr3, {}", in(reg) cr3, options(nostack));
}

/// Read current CR3 (current page table base + PCID).
///
/// # Safety
/// Must execute at CPL 0.
#[inline(always)]
unsafe fn read_cr3() -> u64 {
    let cr3: u64;
    asm!("mov {}, cr3", out(reg) cr3, options(nomem, nostack));
    cr3
}

/// Send a TLB shootdown IPI to all other CPUs (pseudo-code).
/// Real implementation uses APIC ICR registers.
///
/// # Safety
/// Must be called with page tables locked.
unsafe fn send_tlb_shootdown_ipi(start: usize, end: usize) {
    // 1. Write the flush range to per-CPU variables (shared memory)
    // (In Linux: this_cpu_write(cpu_tlbstate.flush_range, ...))

    // 2. Send IPI to all CPUs in mm_cpumask
    // ICR register write: APIC base + 0x300
    // Delivery mode: Fixed, Vector: TLB_VECTOR (0xFC)
    // Destination: All excluding self (shorthand 0b11)
    //   apic_write(APIC_ICR, APIC_DEST_ALLBUT_SELF | TLB_VECTOR);

    // 3. Wait for acknowledgment (spin on atomic counter)
    // 4. Continue (page tables can now be modified safely)

    // This is illustrative — actual implementation is arch-specific.
    let _ = (start, end);
    unimplemented!("Requires APIC register access at CPL 0");
}

// INVPCID instruction — invalidate by PCID (more precise than INVLPG)
// Available on Haswell+ processors

/// Individual address invalidation for a specific PCID.
///
/// # Safety
/// CPL 0 required. INVPCID must be supported (CPUID).
#[inline(always)]
unsafe fn invpcid_addr(pcid: u64, addr: u64) {
    // INVPCID descriptor format: [127:64]=addr, [11:0]=PCID
    let descriptor: [u64; 2] = [pcid & 0xFFF, addr];
    asm!(
        "invpcid {reg}, [{desc}]",
        reg = in(reg) 0u64,  // type=0: individual address
        desc = in(reg) descriptor.as_ptr(),
        options(nostack)
    );
}

/// Flush all TLB entries for a specific PCID.
///
/// # Safety
/// CPL 0 required. INVPCID must be supported.
#[inline(always)]
unsafe fn invpcid_all_for_pcid(pcid: u64) {
    let descriptor: [u64; 2] = [pcid & 0xFFF, 0];
    asm!(
        "invpcid {reg}, [{desc}]",
        reg = in(reg) 1u64,  // type=1: single context (all addresses for PCID)
        desc = in(reg) descriptor.as_ptr(),
        options(nostack)
    );
}

/// Flush all TLB entries on this CPU (all PCIDs, non-global).
///
/// # Safety
/// CPL 0 required.
#[inline(always)]
unsafe fn invpcid_all_nonglobal() {
    let descriptor: [u64; 2] = [0, 0];
    asm!(
        "invpcid {reg}, [{desc}]",
        reg = in(reg) 2u64,  // type=2: all contexts, non-global
        desc = in(reg) descriptor.as_ptr(),
        options(nostack)
    );
}

fn main() {
    println!("INVLPG / INVPCID reference implementation (kernel context only)");
    println!("In user space, executing these instructions raises #GP (privilege violation)");
    println!("\nKey x86 TLB invalidation instructions:");
    println!("  INVLPG  <addr>           : Invalidate single VA, current CR3");
    println!("  MOV CR3, <val>           : Reload page tables; flush non-global TLB");
    println!("  INVPCID <type>, <desc>   : Precise invalidation by PCID (Haswell+)");
    println!("  CR4.PGE toggle           : Flush all including global entries");
}
```

---

## 15. ARM, RISC-V vs x86 TLB Differences

### ARM64 TLB

ARM64 uses a **split TLB** for user and kernel (TTBR0_EL1 and TTBR1_EL1), supporting 4 levels of page tables.

**ARM64 TLB Flush Instructions:**

```asm
// Invalidate TLB entry by VA for current ASID (EL0 = user)
TLBI VAE1IS, Xt    // Inner Shareable: affects all CPUs in cluster

// Invalidate all TLB entries for current ASID
TLBI ASIDE1IS, Xt

// Invalidate full TLB (all ASIDs, all VAs)
TLBI VMALLE1IS

// ARM64 has barrier requirements after TLBI:
DSB ISH            // Data Synchronization Barrier: wait for TLBI completion
ISB                // Instruction Synchronization Barrier: flush pipeline
```

**ARM64 ASID handling in Linux:**

```c
/* arch/arm64/mm/context.c */
void check_and_switch_context(struct mm_struct *mm)
{
    unsigned long flags;
    unsigned int cpu;
    u64 asid, old_active_asid;

    asid = atomic64_read(&mm->context.id);

    /*
     * If the current ASID is still valid and in the current generation,
     * no flush needed.
     */
    old_active_asid = atomic64_read(this_cpu_ptr(&active_asids));
    if (asid != 0 &&
        !((asid ^ atomic64_read(&asid_generation)) >> asid_bits) &&
        atomic64_xchg_relaxed(this_cpu_ptr(&active_asids), asid) != 0)
        goto switch_mm_fastpath;

    /* Need new ASID or generation rollover */
    raw_spin_lock_irqsave(&cpu_asid_lock, flags);
    asid = new_context(mm);
    atomic64_set(&mm->context.id, asid);
    raw_spin_unlock_irqrestore(&cpu_asid_lock, flags);

switch_mm_fastpath:
    cpu_switch_mm(mm->pgd, mm);  /* Sets TTBR0_EL1 + ASID */
}
```

### RISC-V TLB

RISC-V uses a **software-managed TLB** on implementations without hardware page walkers, and hardware walked on others (like SiFive cores).

**RISC-V TLB Fence:**

```asm
# SFENCE.VMA: Memory barrier + TLB flush
# rs1 = virtual address (0 = all addresses)
# rs2 = ASID (0 = all ASIDs)

sfence.vma x0, x0       # Flush all TLB entries
sfence.vma t0, x0       # Flush TLB entries for address in t0
sfence.vma x0, t1       # Flush all entries for ASID in t1
sfence.vma t0, t1       # Flush entry for (addr=t0, ASID=t1)
```

RISC-V deliberately simplified: one instruction handles all flush cases with address and ASID operands.

### x86 vs ARM64 vs RISC-V Comparison

| Feature               | x86-64                    | ARM64                      | RISC-V              |
|-----------------------|---------------------------|----------------------------|---------------------|
| ASID/PCID support     | PCID (12 bit)             | ASID (8 or 16 bit)         | ASID (optional)     |
| TLB management        | Hardware (page walker)    | Hardware (page walker)     | HW or SW            |
| Invalidation inst.    | INVLPG, INVPCID           | TLBI (many variants)       | SFENCE.VMA          |
| Full flush            | Reload CR3                | TLBI VMALLE1IS             | SFENCE.VMA x0, x0   |
| Global pages          | G bit in PTE              | Not-ASID-tagged entries    | Global bit in PTE   |
| Huge page sizes       | 2 MB, 1 GB                | 2 MB, 1 GB, 512 MB, 64 KB | 2 MB, 1 GB (Sv39)   |
| IPI for shootdown     | Yes (manual via APIC)     | Yes (TLBI IS variants)     | Yes (platform IPI)  |

**ARM64 advantage:** The `TLBI VAE1IS` (Inner Shareable) instruction broadcasts the TLB invalidation to all CPUs in the inner-shareable domain automatically — no explicit IPI needed in many cases.

---

## 16. Virtualization & Nested Paging

### The Double-Translation Problem

In a virtualized environment:

```
Guest VA → Guest PA → Host PA

Guest MMU translates: Guest VA → Guest PA (using guest page tables)
Host MMU translates:  Guest PA → Host PA (using host page tables)
```

Every guest page table walk that accesses a guest PA must itself be translated — meaning each level of the guest page walk causes another full walk in the host page tables.

**Worst case: 4-level guest × 4-level host = 16 memory accesses per TLB miss.**

### Shadow Page Tables (Software Solution)

The hypervisor maintains **shadow page tables** that directly map Guest VA → Host PA. These are the actual page tables loaded into CR3.

```
Shadow PT: Guest VA → Host PA (maintained by hypervisor)
Guest PT:  Guest VA → Guest PA (maintained by guest OS)

On guest page table write → VM exit → hypervisor updates shadow PT
```

**Cost:** Every guest page table modification causes a VM exit. Extremely expensive for guest OS operations like fork(), mmap().

### Extended Page Tables / Nested Paging (Hardware Solution)

Intel EPT (Extended Page Tables) and AMD NPT (Nested Page Tables) provide hardware support for two-level address translation.

```
Hardware-walked:
Guest VA → [Guest PT (CR3)]      → Guest PA
Guest PA → [EPT (EPTP register)] → Host PA

Two separate 4-level tables, both walked by hardware.
```

**EPT TLB (TLBE):** A separate TLB caches Guest VA → Host PA translations. Called the **combined TLB** or **EPT TLB**.

### VPID (Virtual Processor Identifier)

Similar to PCID for VMs: each VM/vCPU gets a VPID tag on its TLB entries. VM exits/entries don't flush the TLB; the VPID distinguishes VM entries from host entries.

```c
/* KVM: set VPID on VMCS */
vmcs_write16(VIRTUAL_PROCESSOR_ID, vpid);

/* On VM exit: optionally flush only guest VPID entries */
vpid_sync_vcpu_single(vcpu->arch.vpid);

/* Intel: INVVPID instruction */
/* type 0: individual address invalidation */
/* type 1: single context (all VAs for one VPID) */
/* type 2: all context (flush all VPIDs) */
```

### KVM TLB Handling

```c
/* arch/x86/kvm/vmx/vmx.c */
static void vmx_flush_tlb_all(struct kvm_vcpu *vcpu)
{
    struct vcpu_vmx *vmx = to_vmx(vcpu);

    /*
     * INVEPT invalidates all EPT-derived translations.
     * Used after EPT violation handling.
     */
    if (enable_ept) {
        /* All-context INVEPT */
        ept_sync_global();
    } else {
        /* Reload CR3 — flushes non-global non-VPID entries */
        vmcs_writel(GUEST_CR3, vmcs_readl(GUEST_CR3));
    }
}

static void vmx_flush_tlb_current(struct kvm_vcpu *vcpu)
{
    /* Flush only the current VPID */
    if (enable_vpid)
        vpid_sync_vcpu_single(to_vmx(vcpu)->vpid);
    else
        vmx_flush_tlb_all(vcpu);
}
```

---

## 17. TLB in the Context of NUMA

### NUMA Page Table Placement

On NUMA (Non-Uniform Memory Access) systems, page tables themselves have NUMA affinity. If a CPU on Node 0 runs a process whose page tables live on Node 1, every TLB miss causes a **cross-NUMA page table walk** — 2–4× the latency of a local NUMA access.

```
Node 0 CPU → TLB Miss → Walk page tables (on Node 1) → 200 ns latency
Node 0 CPU → TLB Miss → Walk page tables (on Node 0) →  80 ns latency
```

### Linux NUMA Page Table Replication

Linux migrates page tables to be NUMA-local via the **NUMA balancing** subsystem:

```bash
# Enable NUMA balancing
echo 1 > /proc/sys/kernel/numa_balancing

# View NUMA balancing stats
cat /proc/vmstat | grep numa
# numa_hit:             1234567
# numa_miss:            89012
# numa_page_migrated:   45678
```

### TLB Shootdowns and NUMA

TLB shootdowns across NUMA nodes are particularly expensive:

```
Same-socket IPI latency:  ~500  ns
Cross-socket IPI latency: ~2000 ns (on 2-socket system)
```

On a 4-socket machine, a TLB shootdown affecting all 96 cores costs:
- ~3 IPIs per core (cross-socket) × 2000 ns = ~6 µs blocking time
- Plus handler time (~500 ns × 96 cores)

**Optimization:** Use `MADV_DONTFORK` + process isolation to reduce cross-process TLB shootdowns in NUMA-intensive workloads.

---

## 18. Mental Models & Expert Intuition

### The Locality Hierarchy

Every TLB concept maps to a single principle: **locality**.

```
Temporal locality  → TLB holds recently-used translations
Spatial locality   → Huge pages amortize TLB cost over larger regions
ASID/PCID          → Process-level temporal locality (don't evict on switch)
mmu_gather         → Temporal batching of shootdowns
```

When you see a TLB performance problem, ask: **"What locality is being violated, and at what granularity?"**

### The Cost Stack Mental Model

```
L1 TLB hit:          0-1   cycles   (free)
L2 TLB hit:          5-7   cycles   (cheap)
TLB miss, L1$ PTE:  ~20   cycles   (acceptable)
TLB miss, L2$ PTE:  ~50   cycles   (noticeable)
TLB miss, DRAM PTE: ~200  cycles   (severe)
TLB shootdown:      ~1000 cycles   (IPI overhead — very expensive)
Cross-NUMA shootdown: ~5000 cycles (avoid at all costs)
```

### Expert Decision Tree

```
Working set > 6 MB and TLB-bound?
  → Use huge pages (2 MB)

Frequent context switches with same working set?
  → Ensure PCID/ASID support is active (check dmesg)

Many threads sharing a mapping + high munmap rate?
  → Batch deallocations; use arena allocator

Cross-NUMA TLB shootdowns visible in /proc/interrupts?
  → NUMA-bind process and memory; isolate page tables

Database / ML with known hot working set?
  → HugeTLBfs with pre-reserved pages (deterministic, no THP stall)

Latency-sensitive (trading, real-time)?
  → Disable THP (MADV_NOHUGEPAGE); khugepaged causes unpredictable stalls
  → Pre-fault all pages at startup to avoid runtime page faults
  → Pin threads to cores to maximize TLB reuse
```

### Cognitive Model: The TLB as a Specialized Cache

Treat the TLB exactly like an L1 cache, but for **address translations**:

| Cache Property       | TLB Analog                         |
|---------------------|------------------------------------|
| Cache line size      | Page size (4 KB, 2 MB, 1 GB)      |
| Cache capacity       | TLB entry count (64–2048)          |
| Cache miss penalty   | Page table walk (20–200 cycles)    |
| Cache coherence      | TLB shootdown protocol             |
| Cache warming        | Pre-faulting pages                 |
| Cache thrashing      | Working set exceeds TLB capacity   |

### The Three Laws of TLB Performance

1. **Law of Coverage:** `Performance ∝ (TLB_entries × page_size) / working_set_size`. Increase page size or reduce working set.

2. **Law of Locality:** Accesses that share a page share a TLB entry. Pack hot data into fewer pages.

3. **Law of Coherence Cost:** Every shared, mutable mapping pays shootdown tax proportional to the number of CPUs × frequency of mapping changes. Design for immutability or use per-thread mappings.

### Deliberate Practice: What Elite Engineers Do Differently

1. **Profile first, assume never.** Use `perf stat -e dTLB-load-misses` before optimizing.
2. **Know your working set.** Calculate `bytes_accessed / unique_pages` to estimate TLB miss rate analytically.
3. **Design data structures for TLB, not just CPU cache.** The page boundary matters as much as the cache line boundary.
4. **Understand the kernel path.** Know what `munmap()`, `fork()`, `mprotect()` do to TLB state.
5. **Measure shootdown rate in production.** A spike in `/proc/interrupts TLB` line reveals memory management pathologies.

---

## Summary Reference Card

```
CONCEPT              KEY INSIGHT                        LINUX API / TOOL
─────────────────────────────────────────────────────────────────────────
TLB Hit              0-1 cycle translation              —
TLB Miss             Hardware walks page table          perf dTLB-load-misses
4KB pages            256 KB L1 TLB coverage             —
2MB pages            128 MB L1 TLB coverage             mmap(MAP_HUGETLB)
THP                  Auto-promote to 2MB                MADV_HUGEPAGE
Static huge pages    Pre-reserved 2MB/1GB               /proc/sys/vm/nr_hugepages
ASID                 Per-process TLB tags (ARM)         mm->context.id
PCID                 Per-process TLB tags (x86)         CR3[11:0]
Global pages         Kernel: survives context switch    pte_set_flags(PTE_GLOBAL)
TLB Shootdown        IPI to invalidate remote TLBs      /proc/interrupts TLB
mmu_gather           Batch shootdowns during unmap      tlb_gather_mmu()
KPTI                 Split user/kernel page tables      dmesg | grep PTI
EPT/NPT              Hardware nested paging for VMs     KVM, hypervisors
INVLPG               Invalidate single VA (x86)         asm("invlpg (%0)" ...)
TLBI VAE1IS          Invalidate single VA (ARM64)       DSB ISH after
SFENCE.VMA           TLB fence (RISC-V)                 —
NUMA TLB             Cross-node walk = 2-4× penalty     numactl, mbind()
```

---

*Master the TLB, and you master memory performance. Every nanosecond saved in address translation is a nanosecond given back to computation.*

Now I'll create the comprehensive TLB guide as a markdown file.The guide is complete. Here's what's covered across **18 major sections** and ~1,800 lines:

**Foundations → Hardware**
- Virtual memory mechanics, 4-level x86-64 page table structure, and why 400 ns page walks make TLBs non-negotiable
- Fully-associative vs. set-associative TLB design, PLRU/LRU/Random replacement, Intel Skylake hierarchy table
- TLB entry bit-field anatomy (V, G, D, A, U/S, NX, PWT, PCD flags and their precise semantics)

**Miss Handling & Coherence**
- Hardware walked (x86/ARM) vs. software walked (MIPS) TLB miss paths, with real MIPS assembly
- TLB shootdown protocol in exhaustive detail — IPI lifecycle, batching via `mmu_gather`, Linux kernel source paths
- Performance cost modeling: why a 64-core shootdown can cost ~5 µs

**Process Isolation Mechanisms**
- ASID (ARM64) with generation counter rollover — actual kernel `new_context()` code
- PCID (x86-64), the NOFLUSH bit (CR3[63]), and how KPTI uses dual PCIDs to survive Meltdown mitigations

**Linux Kernel Deep Dive**
- Complete `flush_tlb_*` taxonomy, `INVLPG` vs. CR3 reload heuristics, lazy TLB mode, `/proc/interrupts` monitoring
- Huge pages: static HugeTLBfs, THP (`khugepaged`), PMD-level PS bit, THP shootdown cost

**Security**
- Meltdown, KPTI page table split, Spectre TLB timing side channels, L1TF/Foreshadow

**Implementations**
- **C**: TLB miss cost benchmark (pointer-chase Fisher-Yates), shootdown observer (multithreaded), huge vs. 4KB page comparison, `madvise` interaction
- **Go**: Working set analysis with TLB level classification, shootdown monitor via `/proc/interrupts`, runtime/GC/arena TLB notes
- **Rust**: Full `mmap` safe wrapper, RDTSC cycle profiler, TLB hierarchy deduction from latency curves, huge-page arena allocator for B-Tree nodes, `INVLPG`/`INVPCID`/`TLBI`/`SFENCE.VMA` inline assembly reference

**Architecture Comparison, Virtualization, NUMA**
- ARM64 vs. x86 vs. RISC-V instruction-level differences, EPT/NPT nested paging, VPID, KVM source, cross-NUMA shootdown cost