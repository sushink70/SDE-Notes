# Memory Pages: A Complete & In-Depth Guide
### From Silicon to Syscall — Everything You Need to Master Virtual Memory

---

## Table of Contents

1. [Why Pages Exist — The Fundamental Problem](#1-why-pages-exist)
2. [What is a Page — Precise Definition](#2-what-is-a-page)
3. [Physical Memory: Page Frames](#3-physical-memory-page-frames)
4. [Virtual Memory: The Illusion](#4-virtual-memory-the-illusion)
5. [Page Tables: The Translation Mechanism](#5-page-tables)
6. [Multi-Level Page Tables](#6-multi-level-page-tables)
7. [TLB: Translation Lookaside Buffer](#7-tlb)
8. [Page Faults: Types, Causes, Resolution](#8-page-faults)
9. [Demand Paging](#9-demand-paging)
10. [Copy-on-Write (CoW)](#10-copy-on-write)
11. [Memory-Mapped Files (mmap)](#11-mmap)
12. [The Page Cache](#12-page-cache)
13. [Page Replacement Algorithms](#13-page-replacement-algorithms)
14. [Swapping and the Swap Subsystem](#14-swapping)
15. [Huge Pages and Transparent Huge Pages](#15-huge-pages)
16. [The Buddy Allocator](#16-buddy-allocator)
17. [The Slab Allocator](#17-slab-allocator)
18. [NUMA and Memory Topology](#18-numa)
19. [Memory Protection: Bits, Flags, Hardware Enforcement](#19-memory-protection)
20. [Key Syscalls for Page Control](#20-key-syscalls)
21. [Observability: Reading the System's Memory State](#21-observability)
22. [Pages in Rust, Go, and C](#22-language-perspective)
23. [Security: How Page Mechanisms Are Exploited and Defended](#23-security)
24. [Master Reference: Every Term Defined](#24-reference)

---

## 1. Why Pages Exist — The Fundamental Problem

To understand pages deeply, you must first understand the problem they solve. There are actually **three distinct problems** that the page abstraction addresses simultaneously.

### Problem 1: Fragmentation

Before virtual memory, programs were loaded into contiguous physical RAM. If you needed 10MB of RAM but only had two free 6MB blocks with a used block in between, you could not run the program — even though 12MB was technically free. This is **external fragmentation**.

```
Physical RAM (32MB total)
[USED: 6MB][FREE: 6MB][USED: 4MB][FREE: 6MB][USED: 10MB]

Program needs 10MB contiguous → FAILS
Even though 12MB free total → FAILS
```

Pages solve this by allowing a program's memory to be scattered across non-contiguous physical locations while appearing contiguous to the program.

### Problem 2: Isolation

Without address isolation, process A at address `0x4000` would collide directly with process B at address `0x4000`. One buggy write corrupts the other. There is no OS protection possible without an address translation layer.

### Problem 3: Efficient Sharing

libc is used by every process on the system. Without pages, every process would need its own physical copy. With pages, one physical copy can be mapped into every process's address space simultaneously.

Pages solve all three problems with a single mechanism: **a level of indirection between virtual addresses (what programs see) and physical addresses (what hardware uses).**

---

## 2. What is a Page — Precise Definition

A **page** is the smallest unit of memory that the OS manages as a single atomic block. It is a fixed-size, aligned chunk of address space.

### The Size Choice

On x86-64 Linux, the standard page size is **4096 bytes (4KB)**. This is not arbitrary:

- It must be a power of 2 (for bitwise address splitting, explained in section 5)
- It must be large enough that page table overhead is manageable
- It must be small enough that internal fragmentation is acceptable
- 4KB has been the dominant choice since the 386 era (1985)

```
A 4KB page:
  4096 bytes = 2^12 bytes
  Byte offset within page: needs 12 bits (0 to 4095)
  
  Any virtual address (64-bit):
  ┌────────────────────────────────────────┬────────────────┐
  │  Bits [63:12] — Virtual Page Number   │  Bits [11:0]   │
  │  (which page)                         │  (byte offset) │
  │  52 bits                              │  12 bits       │
  └────────────────────────────────────────┴────────────────┘
```

### Page Alignment

A page-aligned address is any address where `address % 4096 == 0`, i.e., the low 12 bits are all zero. When you call `mmap()` or `malloc()` for large allocations, the kernel always works in page-aligned units, even if you requested an odd size.

```c
// You request 1 byte
void *p = mmap(NULL, 1, PROT_READ|PROT_WRITE,
               MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
// Kernel allocates an ENTIRE 4KB page
// Internal fragmentation: 4095 bytes wasted
```

---

## 3. Physical Memory: Page Frames

While "page" refers to the virtual address space unit, a **page frame** (or **physical frame**) is the corresponding unit in physical RAM. They are the same size (4KB) but the distinction is important:

- **Page**: a region in virtual address space
- **Frame**: a region in physical RAM

Every byte of physical RAM is part of exactly one frame. The kernel maintains a global **frame table** (also called the `mem_map` array in Linux source) — one entry per physical frame, tracking:

```
struct page (Linux kernel, simplified):
┌────────────────────────────────────────────────────────┐
│  flags          — dirty, locked, referenced, uptodate  │
│  _refcount      — how many page tables point here      │
│  _mapcount      — how many VMAs map this page          │
│  mapping        — which address_space owns this page   │
│  index          — offset within that address_space     │
│  lru            — LRU list linkage (for eviction)      │
│  private        — buffer_head pointer (for page cache) │
└────────────────────────────────────────────────────────┘
```

On a system with 8GB of RAM, there are `8 * 1024^3 / 4096 = 2,097,152` physical frames, each with a `struct page` entry. The `mem_map` array alone consumes roughly 56 bytes × 2M = ~112MB of RAM just for bookkeeping.

### Physical Frame Numbering (PFN)

Each frame is identified by its **Physical Frame Number**:

```
Physical Address = PFN * 4096 + offset
PFN              = Physical Address >> 12

Example:
  Physical address 0x00200000
  PFN = 0x00200000 >> 12 = 0x200 = 512
  This is physical frame #512
  It holds bytes 0x00200000 through 0x00200FFF
```

---

## 4. Virtual Memory: The Illusion

Every process has its own **virtual address space** — a private, isolated view of memory. On x86-64 Linux:

- Virtual address space: 128TB per process (2^47 bytes, using 47-bit addresses)
- Upper half (~128TB): reserved for kernel
- Lower half (~128TB): user space

```
Virtual Address Space (x86-64 Linux):

0xFFFFFFFFFFFFFFFF  ─────────────────────────────────
                    │  Kernel Space (128TB)          │
                    │  Same physical pages mapped    │
                    │  into every process            │
0xFFFF800000000000  ─────────────────────────────────
                    │                                │
                    │  HOLE (invalid, canonical gap) │
                    │  (addresses 47-63 are copies   │
                    │   of bit 47 — canonical form)  │
                    │                                │
0x00007FFFFFFFFFFF  ─────────────────────────────────
                    │  User Space (128TB)            │
                    │                                │
                    │  [stack]    grows downward     │
                    │      ↓                         │
                    │  [mmap region]                 │
                    │  (libraries, mmap() calls)     │
                    │      ↑                         │
                    │  [heap]     grows upward       │
                    │  [bss]      zero-init globals  │
                    │  [data]     initialized globals│
                    │  [text]     executable code    │
0x0000000000400000  ─────────────────────────────────
0x0000000000000000  (NULL — never mapped)
```

The critical insight: **two different processes can both have a pointer to address `0x400000`, and those pointers refer to completely different physical memory.** The virtual address is meaningless without knowing which process (which page table) to use for translation.

### Virtual Memory Areas (VMAs)

The kernel doesn't track every page individually in user space. Instead it tracks **VMAs** — contiguous ranges of virtual pages with the same permissions and backing:

```
/proc/PID/maps output (what VMAs look like):

00400000-00452000 r-xp 00000000 08:01 123456  /usr/bin/myprogram  [text]
00651000-00652000 r--p 00051000 08:01 123456  /usr/bin/myprogram  [rodata]
00652000-00653000 rw-p 00052000 08:01 123456  /usr/bin/myprogram  [data]
019a0000-019c1000 rw-p 00000000 00:00 0       [heap]
7f8a000000-7f8a200000 r-xp 00000000 08:01 999 /lib/libc.so.6
7fff000000-7fff021000 rw-p 00000000 00:00 0   [stack]

Columns: start-end  permissions  offset  dev  inode  name
Permissions: r=read, w=write, x=execute, p=private(CoW), s=shared
```

Each VMA is a `struct vm_area_struct` in the kernel, linked in a red-black tree for O(log n) lookup by address.

---

## 5. Page Tables

A **page table** is the data structure that maps virtual page numbers to physical frame numbers. It is the core of the translation mechanism.

### Simple (Single-Level) Conceptual Model

Conceptually, a page table is just an array indexed by virtual page number:

```
Virtual Page Number → Page Table Entry → Physical Frame Number

page_table[VPN] = PFN

Example (4KB pages, 32-bit address space):
  Virtual address: 0x00405010
  VPN = 0x00405010 >> 12 = 0x405    (page 1029)
  Offset = 0x00405010 & 0xFFF = 0x010  (byte 16 within page)
  
  page_table[0x405] → PFN 0x1A3   (physical frame 419)
  
  Physical address = (0x1A3 << 12) | 0x010
                   = 0x001A3010
```

### Page Table Entry (PTE) — Detailed Bit Layout

A PTE on x86-64 is exactly 8 bytes (64 bits):

```
PTE Bit Layout (x86-64):

Bits  63      : XD (Execute Disable / NX bit) — 1=no-execute
Bits  62:52   : Available for OS use
Bits  51:12   : Physical Frame Number (40 bits → up to 1TB physical RAM)
Bit   11      : Available for OS use
Bit   10      : Available for OS use
Bit    9      : Available for OS use
Bit    8      : G (Global) — don't flush from TLB on CR3 switch
Bit    7      : PS (Page Size) — 1=2MB/1GB huge page
Bit    6      : D (Dirty) — CPU sets this on first write
Bit    5      : A (Accessed) — CPU sets this on first access
Bit    4      : PCD (Cache Disable)
Bit    3      : PWT (Write Through)
Bit    2      : U/S (User/Supervisor) — 0=kernel only
Bit    1      : R/W (Read/Write) — 0=read-only
Bit    0      : P (Present) — 1=page is in RAM, 0=not present
```

**The Present bit (P) is the key to demand paging.** When P=0, accessing this address causes a page fault. The OS uses the remaining 63 bits to store whatever it needs (disk location, swap offset, etc.) — the CPU ignores them when P=0.

---

## 6. Multi-Level Page Tables

A single-level page table for a 64-bit address space would need `2^52` entries × 8 bytes = 32 petabytes. This is obviously impossible. The solution: **multi-level page tables**.

### x86-64: 4-Level Page Table (PML4)

x86-64 uses 4 levels. A 48-bit virtual address is split into 5 fields:

```
48-bit Virtual Address:
┌────────┬────────┬────────┬────────┬──────────────┐
│ 9 bits │ 9 bits │ 9 bits │ 9 bits │   12 bits    │
│ PML4   │  PDPT  │   PD   │   PT   │    Offset    │
│ index  │ index  │ index  │ index  │              │
└────────┴────────┴────────┴────────┴──────────────┘
  [47:39]  [38:30]  [29:21]  [20:12]    [11:0]

Each index: 9 bits → 512 entries per table
Each entry: 8 bytes
Each table: 512 × 8 = 4096 bytes = exactly ONE PAGE
```

### Translation Walk (4-Level)

```
CR3 register → Physical address of PML4 table
                          │
                          ▼
                    PML4 Table (512 entries)
                    pml4[VA[47:39]]
                          │ → PDPT physical address
                          ▼
                    PDPT Table (512 entries)
                    pdpt[VA[38:30]]
                          │ → PD physical address
                          ▼
                    Page Directory (512 entries)
                    pd[VA[29:21]]
                          │ → PT physical address
                          ▼
                    Page Table (512 entries)
                    pt[VA[20:12]]
                          │ → Physical Frame Number
                          ▼
              Physical Address = (PFN << 12) | VA[11:0]
```

### Why This Saves Memory

A process using only 1MB of stack + 1MB of code needs page tables for only those regions. The PML4 has 512 entries — only 1 or 2 will be non-null. Entire subtrees that are unused don't exist at all. A minimal process might use:

```
PML4:  1 page = 4KB
PDPT:  1 page = 4KB
PD:    1 page = 4KB
PT:    2 pages = 8KB (one for text, one for stack)
─────────────────
Total: 5 pages = 20KB of page table overhead
```

Compare to a flat array: 2^36 entries × 8 bytes = 512GB. The multi-level structure makes sparse address spaces cheap.

### 5-Level Page Tables (LA57)

Modern Linux (since 4.12) supports **5-level page tables** on CPUs with the LA57 feature:
- Adds one more level: PML5
- Virtual address space: 128PB per process (2^57 bytes)
- Required for systems with more than 4TB of RAM
- Disabled by default unless the system needs it (extra table walk = slightly slower)

---

## 7. TLB — Translation Lookaside Buffer

Every memory access requires a 4-level page table walk: 4 additional memory reads to get the physical address of the target. This would make every memory access 5× slower. The **TLB** solves this.

### What the TLB Is

The TLB is a **hardware cache of recent virtual-to-physical translations**, built directly into the CPU. It is a fully associative (or set-associative) cache typically holding 64–2048 entries.

```
TLB Entry Structure:
┌───────────────┬───────────────┬──────────────────────────┐
│  ASID (8-16b) │  VPN (36+ b)  │  PFN + flags (52 bits)   │
│  Process ID   │  Virtual Page │  Physical Frame + perms  │
└───────────────┴───────────────┴──────────────────────────┘

ASID = Address Space ID, allows entries from different processes
       to coexist without flushing on context switch
```

### TLB Hit vs Miss

```
Memory Access to virtual address VA:

1. CPU checks TLB for (ASID, VPN) pair
   
   TLB HIT (common case, ~99%):
   ├── Found → extract PFN → form physical address → access RAM
   └── Cost: ~1 cycle overhead (essentially free)
   
   TLB MISS (rare, ~1%):
   ├── Hardware Page Table Walker activates (on x86)
   ├── Reads PML4[i] from RAM (cache miss: ~100 cycles)
   ├── Reads PDPT[i] from RAM
   ├── Reads PD[i] from RAM
   ├── Reads PT[i] from RAM → gets PFN
   ├── Loads new entry into TLB
   └── Cost: 100-1000 cycles (4 memory reads, often cached in L2/L3)
```

### TLB Shootdown

When the kernel modifies a page table entry (e.g., changing permissions, unmapping a page), it must **invalidate TLB entries on all CPU cores** that might have cached the old translation. This is called a **TLB shootdown** and is one of the most expensive operations in multi-core systems:

```
CPU 0 changes PTE for VA 0x400000:
  1. CPU 0 modifies the page table
  2. CPU 0 sends IPI (Inter-Processor Interrupt) to all other CPUs
  3. Each CPU executes INVLPG (invalidate TLB entry) for that VA
  4. Each CPU ACKs
  5. CPU 0 continues
  
Cost: microseconds per shootdown
      At high frequency (fork/exec heavy workloads): serious bottleneck
```

### INVLPG vs CR3 Reload

```c
// Invalidate single TLB entry (cheaper):
asm volatile("invlpg (%0)" ::"r" (virtual_address) : "memory");

// Invalidate entire TLB for current process (context switch):
// Write the page table base address to CR3 register
// This flushes ALL TLB entries for the current ASID
```

### TLB Coverage and Huge Pages

A 4KB page TLB with 1024 entries covers: `1024 × 4KB = 4MB` of address space before misses become frequent. For workloads with large working sets (databases, ML), this causes constant TLB pressure. **Huge pages** (2MB) extend coverage to `1024 × 2MB = 2GB` — a 512× improvement. This is a primary motivation for huge page support.

---

## 8. Page Faults — Types, Causes, Resolution

A **page fault** is a hardware exception raised by the CPU's Memory Management Unit (MMU) when a virtual address access cannot be completed directly. It is not necessarily an error — most page faults are normal and intentional.

### How a Page Fault is Triggered

```
CPU attempts to access virtual address VA:
  1. MMU checks TLB → miss
  2. MMU walks page table → finds PTE
  3. One of these is true:
     a. P=0 (not present) → PAGE FAULT
     b. W=1 but R/W=0 (write to read-only) → PAGE FAULT
     c. User mode but U/S=0 (kernel page) → PAGE FAULT
     d. Execute but XD=1 (no-execute) → PAGE FAULT
  4. CPU pushes fault info onto stack, jumps to kernel fault handler
  5. Kernel fault handler (do_page_fault in Linux) runs
```

### Fault Classification

Linux's fault handler classifies faults into distinct categories:

#### Type 1: Minor Fault (No I/O Required)

```
Causes:
  - First access to a demand-paged anonymous page
    (page not yet allocated — needs a new physical frame from free list)
  - First access to a CoW page after fork()
  - Stack expansion (accessing just below the current stack guard)

Resolution:
  1. Allocate a free physical frame
  2. Zero-fill it (security: must not leak previous contents)
  3. Map it into the page table (set P=1)
  4. Return from fault handler
  5. CPU retries the faulting instruction — succeeds

Cost: ~1-10 microseconds (no disk I/O)
```

#### Type 2: Major Fault (I/O Required)

```
Causes:
  - Page was mapped but has been swapped to disk
  - mmap'd file page not yet loaded (demand paging from file)
  - Process accessed a memory-mapped file region for the first time

Resolution:
  1. Find the page's location (swap slot or file offset)
  2. Allocate a free physical frame
  3. Schedule a disk I/O to read the page
  4. Block the faulting thread/process
  5. When I/O completes: map the frame, wake the process
  6. CPU retries — succeeds

Cost: 1-100 milliseconds (disk I/O latency)
```

#### Type 3: Invalid / Fatal Fault (Segfault)

```
Causes:
  - Access to unmapped virtual address (no VMA covers this address)
  - Write to read-only page (text segment, mmap PROT_READ only)
  - Execute from no-execute page (stack/heap with NX bit set)
  - NULL pointer dereference (address 0x0 — no VMA at 0)
  - Stack overflow (grew beyond the maximum stack VMA)

Resolution:
  1. Kernel checks: does this address belong to any VMA? → No
  2. Kernel sends SIGSEGV to the process
  3. Default SIGSEGV handler: terminate process + core dump

This is the segmentation fault you see in C programs.
```

### The Page Fault Handler in Detail

```
do_page_fault(regs, error_code):
  
  VA = CR2 register  (CPU puts faulting address here)
  
  // Check for kernel fault (bug in kernel code)
  if fault in kernel space:
      check fixup table → oops() or BUG()
  
  // Find the VMA covering this address
  vma = find_vma(current->mm, VA)
  
  if no vma:
      → SIGSEGV (invalid address)
  
  if vma->start > VA:
      if vma is the stack VMA and VA is close enough:
          → expand stack (grow VMA downward)
      else:
          → SIGSEGV
  
  // Check permissions
  if write fault and VMA not writable:
      → SIGSEGV (write to read-only mapping)
  
  if exec fault and VMA not executable:
      → SIGSEGV (NX violation)
  
  // Handle the actual fault
  handle_mm_fault(vma, VA, fault_flags):
      
      // Navigate/create page table entries
      pgd → p4d → pud → pmd → pte
      
      if pte_none(*pte):
          → do_anonymous_page()   // demand alloc
          or do_fault()           // file-backed mmap
      
      if pte_present(*pte) but write fault:
          → do_wp_page()          // CoW
      
      if not pte_present(*pte):
          → do_swap_page()        // swap in
```

### Soft vs Hard Page Fault (Linux Terminology)

Linux uses "minor" and "major" interchangeably with "soft" and "hard":

```bash
# See per-process fault counts:
/usr/bin/time -v ./myprogram
  Major (requiring I/O) page faults: 12
  Minor (reclaiming a frame) page faults: 4521

# Live monitoring:
perf stat -e page-faults,major-faults ./myprogram
```

---

## 9. Demand Paging

**Demand paging** is the policy: "do not load anything into RAM until it is actually accessed." This is the default strategy in Linux for all memory.

### Anonymous Demand Paging (Heap/Stack)

When you call `malloc(1MB)` or expand your stack:

```
Step 1: malloc() calls brk() or mmap() syscall
Step 2: Kernel creates a VMA entry (4 bytes in kernel, basically free)
Step 3: NO physical memory allocated yet
        NO page table entries yet
        The VMA just says "this range exists"

Step 4: Your code accesses buf[0]
Step 5: MMU: no PTE for this address → PAGE FAULT (minor)
Step 6: Kernel: VMA exists, anonymous mapping
        → allocate one physical frame (from free list)
        → zero-fill it (memset to 0)
        → create PTE: PFN=X, P=1, R/W=1
Step 7: Access completes

Step 8: Your code accesses buf[4096]  (next page)
Step 9: PAGE FAULT again (different page)
        → allocate another frame
        ... continues as you touch more pages
```

**The result**: A `malloc(1GB)` that only uses 1MB of actual data only consumes 1MB of physical RAM. This is why Linux systems can appear to "overcommit" memory.

### File-Backed Demand Paging (Executables, Libraries)

When you `exec()` a program:

```
execve("/usr/bin/ls"):
  1. Kernel reads ELF header (just the header, ~64 bytes)
  2. Creates VMAs for each ELF segment:
     - text (r-x): virtual range A-B, backed by file offset X
     - rodata (r--): virtual range C-D, backed by file offset Y
     - data (rw-): virtual range E-F, backed by file offset Z
  3. Sets up initial stack VMA
  4. Jumps to ELF entry point (e.g., _start)
  
  At this point: 0 physical frames allocated (except stack page)
  
  5. _start executes → faults on each new code page as execution proceeds
  6. Each fault: kernel reads 4KB from the ELF file on disk
  7. Maps it into page table
  8. Continues execution
  
  A 500KB program might only fault in 20-30 pages during its lifetime
  The rest (dead code, unused data) never loads into RAM
```

### Prefetching

The kernel performs **readahead**: when a page fault occurs on a file-backed page, it speculatively reads the next several pages too (typically 32KB = 8 pages). This turns sequential access into efficient streaming. For random-access workloads, this is wasteful (can be controlled with `madvise(MADV_RANDOM)`).

---

## 10. Copy-on-Write (CoW)

**Copy-on-Write** is one of the most elegant optimizations in OS design. It allows multiple processes to share the same physical pages, deferring actual copying until a write occurs.

### CoW During fork()

```
Parent process (PID 1) has:
  VMA [0x400000 - 0x401000]: writable, mapped to Frame #42

fork() is called:

After fork():
  Parent (PID 1):                Child (PID 2):
  VMA [0x400000-0x401000]        VMA [0x400000-0x401000]
  PTE: PFN=42, P=1, R/W=0        PTE: PFN=42, P=1, R/W=0
                   ↑ CHANGED                       ↑ CHANGED
                   to READ-ONLY                    to READ-ONLY
                          ↓               ↓
                        SAME physical Frame #42
                        refcount = 2

Cost of fork(): copy VMAs + page tables (cheap)
                do NOT copy physical pages (0 frames copied)
```

When either process writes to this page:

```
Child writes to 0x400000:
  MMU: PTE says R/W=0 → PAGE FAULT (write protection fault)
  
  Kernel do_wp_page():
    Is refcount > 1? YES → must copy
    Allocate new Frame #77
    Copy contents of Frame #42 → Frame #77
    Update child's PTE: PFN=77, R/W=1
    Decrement refcount of Frame #42 → 1
    
  Now:
  Parent: 0x400000 → Frame #42 (still read/write)
  Child:  0x400000 → Frame #77 (its own copy)
  
  If parent also writes later → same process, gets its own copy
```

### CoW for Zero Pages

Linux maintains a **single global zero page** (a physical frame filled with zeros). All fresh anonymous allocations initially point to this zero page:

```
malloc(1MB) + first read:
  All 256 pages → PFN = zero_page, R/W=0
  
  Reads: served from zero page (all zeros), no copy needed
  
  First write to any page:
  → CoW fault → allocate real frame → copy zeros → write
  
  Memory savings: programs that allocate but never dirty
                  all their pages share ONE physical frame
```

### CoW in Rust

Rust's `std::borrow::Cow<'a, B>` (Clone-on-Write) is a direct application of this concept at the language level:

```rust
use std::borrow::Cow;

fn process(input: Cow<str>) {
    // If input is borrowed and we don't modify it: zero allocation
    // If we need to modify: clone happens exactly once, lazily
    
    let result = if needs_modification {
        let mut owned = input.into_owned(); // Clone happens HERE
        owned.push_str(" suffix");
        Cow::Owned(owned)
    } else {
        input  // Zero allocation, just passes through the borrow
    };
}
```

---

## 11. mmap — Memory-Mapped Files

`mmap()` is the syscall that maps a file (or anonymous memory) directly into a process's virtual address space. It is one of the most powerful Linux primitives.

### Signature and Parameters

```c
void *mmap(void *addr,      // suggested start address (usually NULL)
           size_t length,   // how many bytes to map
           int prot,        // PROT_READ | PROT_WRITE | PROT_EXEC | PROT_NONE
           int flags,       // MAP_SHARED | MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED
           int fd,          // file descriptor (-1 for anonymous)
           off_t offset);   // offset within file (must be page-aligned)
```

### File-Backed mmap (Shared)

```
mmap(NULL, filesize, PROT_READ, MAP_SHARED, fd, 0):

  Process virtual space:          Page Cache (kernel):
  [0x7f000000 - 0x7f001000]  →   File block 0 (page)
  [0x7f001000 - 0x7f002000]  →   File block 1 (page)
  [0x7f002000 - 0x7f003000]  →   File block 2 (page)
  
  Physical pages are SHARED:
  - Multiple processes mmap the same file → same physical pages
  - Write by process A immediately visible to process B
  - MAP_SHARED + write → change written back to file (when msync or evicted)
```

### File-Backed mmap (Private / CoW)

```
MAP_PRIVATE:
  - Reads see the file contents
  - Writes trigger CoW → private copy, NOT written back to file
  - This is how executables are loaded:
    - Text segment: MAP_PRIVATE | PROT_READ | PROT_EXEC
    - Data segment: MAP_PRIVATE | PROT_READ | PROT_WRITE
    - Modifications to data are private to this process
```

### Anonymous mmap

```c
// This is what malloc uses internally for large allocations:
void *p = mmap(NULL, size,
               PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS,
               -1, 0);

// No file backing. Pages are zero-initialized on first access.
// CoW zero page optimization applies.
```

### mmap vs read() — Why mmap is Often Faster

```
read() path:
  File data → Kernel page cache → copy → User buffer
  Two copies: disk→cache, cache→userspace
  Extra system call overhead per read chunk

mmap() path:
  File data → Kernel page cache → directly mapped into user VA space
  Zero copies after initial page fault
  Access file data as if it's a pointer — no syscall per access
  
  Ideal for:
    - Random access to large files (databases)
    - Multiple processes reading same file
    - Zero-copy I/O
```

### mmap in Rust

```rust
use memmap2::MmapOptions;
use std::fs::File;

fn main() {
    let file = File::open("large_dataset.bin").unwrap();
    
    let mmap = unsafe {
        MmapOptions::new()
            .map(&file)
            .unwrap()
    };
    
    // mmap[0..4096] reads first page from page cache
    // No intermediate buffer. Zero-copy.
    // Page faults happen transparently on first access to each region
    let first_bytes = &mmap[0..8];
    println!("{:?}", first_bytes);
}
```

---

## 12. The Page Cache

The **page cache** is the kernel's unified cache of file data in RAM. It is not a separate structure — it IS the memory used by mmap, read(), write(), and the block layer. Everything flows through it.

### Architecture

```
User Process                    Kernel                      Disk
──────────                      ──────                      ────

read(fd, buf, n)    ──────→   VFS layer
                               │
                               ▼
                          find_get_page(inode, offset)
                               │
                    ┌──────────┴─────────────┐
                    │                        │
               Page found               Page NOT found
               in cache                 in cache
                    │                        │
                    ▼                        ▼
              copy to buf           alloc new page
              return               submit_bio() → disk I/O
                                   wait for I/O
                                   fill page with data
                                   add to page cache
                                   copy to buf
                                   return
```

### The address_space Structure

Each file in Linux has an `address_space` object which is essentially a **radix tree** (now an XArray in newer kernels) mapping `file_offset / 4096` → `struct page *`. The page cache is this radix tree.

```
inode for /etc/passwd:
  address_space {
    xarray {
      0 → struct page (bytes 0-4095 of file)
      1 → struct page (bytes 4096-8191 of file)
      2 → NULL (not cached yet)
      ...
    }
  }
```

### Dirty Pages and Write-Back

When you write to a file:

```
write(fd, data, n):
  1. Find page in page cache (or create new page)
  2. Copy data into the page (user → kernel copy, only once)
  3. Mark page as DIRTY
  4. Return to userspace immediately (write is asynchronous!)
  
  Later (background):
  5. pdflush/writeback kernel thread wakes up
  6. Finds dirty pages older than dirty_expire_centisecs (default: 30s)
  7. Submits writeback I/O to disk
  8. Clears dirty bit
  
  sync() / fsync():
  - Forces immediate writeback of dirty pages
  - Guarantees durability on crash
```

### Page Cache Pressure and Reclaim

```
When free RAM is low:
  kswapd (kernel thread) activates
  
  It reclaims pages from the LRU lists:
  
  LRU_INACTIVE_FILE: file pages, not recently accessed → evict first
    (can be re-read from disk if needed)
  
  LRU_ACTIVE_FILE: file pages, recently accessed → protect longer
  
  LRU_INACTIVE_ANON: anonymous pages, not recent → swap out
  
  LRU_ACTIVE_ANON: anonymous pages, recent → most protected
  
  UNEVICTABLE: mlock'd pages, ramfs → never evict
```

### Cache Hit Rate

```bash
# Check page cache statistics:
cat /proc/meminfo | grep -E 'Cached|Buffers|MemFree|MemAvailable'

# More detailed:
vmstat -s | head -20

# Per-file cache status:
# (which pages of a file are currently in cache)
fincore /path/to/large/file
```

---

## 13. Page Replacement Algorithms

When physical RAM is full and a new page must be loaded, the OS must choose a **victim page** to evict. The choice determines performance.

### Optimal (OPT / Bélády's Algorithm)

Evict the page that will not be used for the longest time in the future. Provably optimal. **Impossible in practice** (requires knowing the future) but serves as a theoretical upper bound for comparison.

### FIFO (First-In, First-Out)

Evict the page that has been in RAM the longest. Simple but poor — a page that has been in RAM a long time might be heavily used (e.g., libc). Suffers from **Bélády's anomaly**: adding more physical frames can increase page faults.

### LRU (Least Recently Used)

Evict the page that was least recently accessed. Approximates OPT well under temporal locality (the observation that recently accessed data is likely to be accessed again). The theoretical ideal for most workloads.

**Exact LRU is expensive**: every memory access would need to update a timestamp or linked list. With millions of accesses per second, this overhead is unacceptable in hardware.

### Clock Algorithm (Second Chance)

Linux's approximation of LRU:

```
Pages arranged in a circular list (the "clock"):

      ┌───┐   ┌───┐   ┌───┐   ┌───┐
  → → │ A │→→ │ B │→→ │ C │→→ │ D │ → (wraps around)
      │ R=1│   │ R=0│   │ R=1│   │ R=1│
      └───┘   └───┘   └───┘   └───┘
               ↑
           Clock hand

R = Referenced bit (set by CPU on access, cleared by OS periodically)

Eviction process:
  Clock hand sweeps:
    If R=1: clear R → 0, advance (give second chance)
    If R=0: EVICT this page (it wasn't accessed since last sweep)

This is O(1) and requires no per-access overhead.
```

### Linux's Two-List LRU (Active/Inactive)

Linux uses a more sophisticated two-list variant:

```
Active List:           Inactive List:
(recently used)        (eviction candidates)
[P1, P5, P8, P2]      [P3, P7, P4, P6]
     ↑                      ↑
  Protected              Vulnerable

Flow:
  New page → Inactive list tail
  Page accessed → promoted to Active list tail
  Active list full → demote head to Inactive
  Eviction needed → take from Inactive list head

Separate lists for file-backed and anonymous pages,
each with their own active/inactive pair.
```

### Working Set Model

The **working set** `W(t, Δ)` is the set of pages a process has accessed in the past Δ time units. If a process's working set fits in RAM, page fault rate is low. If not (working set > available RAM), **thrashing** occurs: the system spends more time handling page faults than doing useful work.

---

## 14. Swapping and the Swap Subsystem

**Swapping** (more precisely: **paging out**) moves anonymous pages from RAM to disk when RAM is under pressure. This extends effective RAM at the cost of latency.

### Swap Space

```
Two forms of swap space:
  1. Swap partition: a raw disk partition dedicated to swap
     /dev/sda2 (no filesystem, used raw)
  
  2. Swap file: a regular file used as swap
     /swapfile (on any filesystem supporting direct I/O)

Swap size convention:
  Old rule: 2× RAM. Outdated.
  Modern rule: enough to hold the working set that doesn't fit in RAM.
  Typical: 1× RAM or 2-8GB fixed.
```

### The Swap Out Process

```
kswapd detects low RAM:
  
  1. Select victim anonymous page (from Inactive list)
  2. Find a free slot in swap space (the swap map)
  3. Write the page's 4KB to disk at that slot
  4. Update PTE: P=0, encode swap slot in bits [63:1]
     (P=0 means CPU won't interpret these bits — OS can use them freely)
  5. Free the physical frame → add back to free list
  
  PTE when swapped out:
  ┌────────────────────────────────────────────────────┬───┐
  │  Swap type (5 bits) + Swap offset (50 bits)        │ 0 │
  │  (encodes exactly where on disk this page lives)   │ P │
  └────────────────────────────────────────────────────┴───┘
```

### The Swap In Process (Page Fault)

```
Process accesses swapped-out address:
  
  1. MMU: PTE has P=0 → PAGE FAULT (major fault)
  2. Kernel: PTE P=0 but not zero → it's a swap entry
  3. Extract swap type + offset from PTE
  4. Allocate a free physical frame
  5. Submit I/O: read 4KB from swap slot → new frame
  6. Block the process (waiting for disk)
  7. I/O completes
  8. Update PTE: PFN = new frame, P=1, clear swap entry
  9. Free the swap slot (or keep it as a hint for future swap-out)
  10. Process unblocks, retries instruction
```

### swappiness

Linux's `vm.swappiness` parameter (0-200, default 60) controls the balance between swapping anonymous pages vs reclaiming file cache pages:

```
swappiness = 0:   prefer to reclaim file cache, avoid swapping
swappiness = 60:  balanced default
swappiness = 100: treat anonymous and file pages equally
swappiness = 200: aggressively swap anonymous pages

Set permanently:
echo "vm.swappiness=10" >> /etc/sysctl.conf
```

For latency-sensitive servers (databases), `swappiness=1` prevents the latency spikes caused by swap-in faults.

### zswap and zram

```
zswap: a compressed page cache in front of real swap
  - Pages are compressed (LZO/LZ4/zstd) before swap-out
  - Compressed pages live in a kernel memory pool
  - Only evicted to disk if pool is full
  - Typical compression: 3:1 → 6GB of data in 2GB of RAM
  - Reduces disk I/O at cost of CPU cycles

zram: a RAM-based compressed block device used as swap
  - No disk I/O at all — purely RAM
  - Effective on systems with no swap disk (phones, small VMs)
  - Trade CPU (compression) for RAM (fits more pages)
```

---

## 15. Huge Pages and Transparent Huge Pages

Standard 4KB pages become a bottleneck for large memory workloads due to TLB pressure. **Huge pages** use larger page sizes to reduce TLB misses.

### Available Page Sizes (x86-64)

```
4KB   (2^12):  Standard, universally supported
2MB   (2^21):  Huge page (uses PD entry directly, skips PT level)
1GB   (2^30):  Gigantic page (uses PDPT entry directly, skips PD+PT)
```

### How 2MB Pages Work

In the 4-level page table, a 2MB page skips the final PT level:

```
Standard 4KB:          Huge 2MB:
PML4 → PDPT → PD → PT → Frame    PML4 → PDPT → PD → Frame (PS=1 in PD entry)

TLB entries needed to cover 1GB:
  4KB pages: 1GB / 4KB = 262,144 TLB entries needed (impossible)
  2MB pages: 1GB / 2MB = 512 TLB entries needed ✓
  1GB pages: 1 TLB entry ✓
```

### Explicit Huge Pages (HugeTLBfs)

Huge pages must be pre-allocated at boot or early runtime:

```bash
# Reserve 512 huge pages (512 × 2MB = 1GB):
echo 512 > /proc/sys/vm/nr_hugepages

# Mount hugetlbfs:
mount -t hugetlbfs nodev /mnt/huge

# Use in C:
int fd = open("/mnt/huge/myfile", O_CREAT | O_RDWR, 0600);
void *addr = mmap(NULL, 2*1024*1024, PROT_READ|PROT_WRITE,
                  MAP_SHARED, fd, 0);
// addr is backed by a 2MB huge page
```

**Drawbacks of explicit huge pages:**
- Must be reserved in advance (reduces flexibility)
- Cannot be swapped (always locked in RAM)
- Internal fragmentation: 2MB allocated even for small data

### Transparent Huge Pages (THP)

THP automates huge page use without application changes:

```
THP policies (controlled via /sys/kernel/mm/transparent_hugepage/enabled):
  always:   try to use 2MB pages whenever possible
  madvise:  only for regions explicitly marked with madvise(MADV_HUGEPAGE)
  never:    disable THP

THP behavior:
  When allocating a large anonymous region (e.g., malloc(10MB)):
    → khugepaged thread monitors for 2MB-aligned, 2MB-size regions
    → If suitable: collapse 512 individual 4KB pages into one 2MB page
    → Or: allocate 2MB huge page directly on fault if available

THP splitting:
  When a huge page must be partially remapped (e.g., mprotect on part):
  → Linux splits the 2MB page back into 512 × 4KB pages (expensive)
  → Avoid frequent partial remaps of huge page regions
```

### Performance Impact

```
Benchmark: PostgreSQL 16 on 64GB RAM, large shared_buffers:

THP disabled:
  TLB misses: 15% of memory access cycles
  Throughput: baseline

THP enabled:
  TLB misses: 0.3% of memory access cycles
  Throughput: +20-40% on memory-bound queries

Redis:
  THP causes WORSE performance due to CoW during fork() for RDB saves:
  A write to any byte of a 2MB huge page causes CoW of the ENTIRE 2MB
  (vs only 4KB with standard pages)
  → Redis recommends: echo never > .../transparent_hugepage/enabled
```

---

## 16. The Buddy Allocator

The kernel's physical memory allocator. It manages the free frame pool and handles allocations of power-of-2 page quantities.

### Structure

The buddy allocator maintains **11 free lists** (on x86-64), one for each order from 0 to 10:

```
Order 0:  free list of 1-page  (4KB)   blocks
Order 1:  free list of 2-page  (8KB)   blocks
Order 2:  free list of 4-page  (16KB)  blocks
Order 3:  free list of 8-page  (32KB)  blocks
...
Order 10: free list of 1024-page (4MB) blocks
```

### Allocation Algorithm

```
Request: allocate 2 pages (order 1)

1. Check order-1 free list
   → If non-empty: remove one block, return it
   
2. If empty: check order-2 free list
   → Find one 4-page block
   → SPLIT: divide into two 2-page blocks ("buddies")
   → Return one, add other to order-1 free list
   
3. If empty: check order-3, split into two order-2, one splits again...
   Continue up until a free block is found or OOM.
```

### Deallocation (Merging)

```
Return a 2-page block at address A:

1. Compute buddy address: B = A XOR (2 * 4096)  [flip the order-1 bit]
2. Is the buddy also free in the order-1 free list?
   YES: remove buddy, merge into one 4-page block → add to order-2 free list
        Repeat at order-2 with its buddy
        Continue until buddy is not free or max order reached
   NO: just add A to order-1 free list
```

### Why Power-of-2? The XOR Trick

```
For an order-N block at address A:
  buddy_address = A XOR (2^N * PAGE_SIZE)
  
  This works because power-of-2 aligned addresses differ in exactly one bit.
  XOR flips that bit → instant buddy address computation.
  
  Example: order-1 block at 0x10000 (page 16)
  buddy = 0x10000 XOR (2 * 4096) = 0x10000 XOR 0x2000 = 0x12000 (page 18)
```

### Fragmentation Problem

The buddy allocator eliminates external fragmentation at the page level but can suffer from **internal fragmentation**: requesting 3 pages gets a 4-page block (order 2), wasting 1 page.

More seriously: **memory fragmentation over time** means order-10 allocations (4MB contiguous) can fail even when 4MB of free pages exist — scattered in small non-contiguous blocks. This is why THP allocation can fail on a running system.

### Memory Zones

The buddy allocator is actually divided into **memory zones** because hardware imposes constraints:

```
ZONE_DMA   (0-16MB):    ISA DMA devices can only access low 16MB
ZONE_DMA32 (0-4GB):     32-bit PCI devices
ZONE_NORMAL (>4GB):     Main RAM, no hardware restrictions
ZONE_HIGHMEM:           (32-bit kernels only, now rare)
ZONE_MOVABLE:           Pages that can be migrated (for memory hotplug)

Each zone has its own buddy allocator free lists.
Allocations try ZONE_NORMAL first, fall back to lower zones if needed.
```

---

## 17. The Slab Allocator

The buddy allocator works in page-size units. But the kernel constantly needs small objects — 64 bytes for a PTE, 232 bytes for a `task_struct`, 56 bytes for a `struct page`. The **slab allocator** provides efficient sub-page allocation.

### Architecture

```
SLAB / SLUB / SLOB (three implementations, SLUB is default since 2.6.23):

  kmem_cache for "struct file" (size: 232 bytes):
  ┌────────────────────────────────────────────────────────────┐
  │  Slab 1 (one physical page = 4096 bytes)                   │
  │  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬────┐  │
  │  │obj 0 │obj 1 │obj 2 │obj 3 │obj 4 │obj 5 │obj 6 │... │  │
  │  │232B  │232B  │232B  │232B  │232B  │FREE  │FREE  │    │  │
  │  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴────┘  │
  └────────────────────────────────────────────────────────────┘
  
  Allocation: O(1) — take from free list of this cache
  Deallocation: O(1) — return to free list
  No initialization overhead: objects can be CONSTRUCTED once,
    reused many times (constructor/destructor pattern)
```

### SLUB Improvement

SLUB (the default) simplified slab by eliminating most per-slab metadata. It stores the free list pointer in the object itself (first word when free) and per-CPU caches mean no lock contention in the common case.

### kmalloc

```c
// General kernel allocator — uses size-class slab caches:
// kmalloc-8, kmalloc-16, kmalloc-32, ..., kmalloc-8192

void *p = kmalloc(100, GFP_KERNEL);
// Internally: uses kmalloc-128 slab cache (next power of 2 ≥ 100)
// O(1) allocation, no lock in fast path (per-CPU cache)

kfree(p);
// Returns object to kmalloc-128 per-CPU free list
```

### GFP Flags (Get Free Pages)

Every kernel allocation specifies context via GFP flags:

```
GFP_KERNEL:   May sleep, may do I/O, normal process context
GFP_ATOMIC:   Cannot sleep (interrupt context, spinlock held)
              Will fail rather than block
GFP_NOWAIT:   Cannot sleep, returns NULL if no immediate page available
GFP_DMA:      Must come from ZONE_DMA (hardware constraint)
GFP_HIGHUSER: For user-space pages, prefer ZONE_HIGHMEM
__GFP_ZERO:   Zero-fill the allocated memory
__GFP_NOFAIL: Loop forever until allocation succeeds (use carefully)
```

---

## 18. NUMA — Non-Uniform Memory Access

Modern multi-socket servers have **NUMA**: multiple CPU dies, each with local RAM. Accessing local RAM is fast (~80ns); accessing another CPU's RAM crosses an interconnect (~160-200ns, 2-3× slower).

### NUMA Topology

```
NUMA Node 0:              NUMA Node 1:
  CPU 0-15               CPU 16-31
  RAM: 64GB              RAM: 64GB
  Local latency: 80ns    Local latency: 80ns
  
  Connected via: QPI / UPI / Infinity Fabric
  Remote access latency: 160-200ns

The OS is NUMA-aware:
  → Try to allocate RAM on the same node as the CPU running the process
  → "First touch" policy: page is allocated on the node of the CPU
     that first touches it (faults it in)
```

### NUMA Effects on Pages

```
First-touch allocation:
  Thread on CPU 0 (Node 0) allocates and touches 1GB buffer
  → 1GB of pages allocated from Node 0's RAM
  
  Later: thread migrates to CPU 20 (Node 1)
  → Thread now accesses Node 0 RAM remotely → 2× slower
  
  Solution: use numactl or set NUMA policy:
  numactl --membind=1 --cpunodebind=1 ./myprogram
```

### NUMA System Calls

```c
#include <numa.h>

// Bind process to node 0 RAM and CPUs:
numa_run_on_node(0);
numa_set_membind(numa_parse_nodestring("0"));

// Allocate on specific node:
void *p = numa_alloc_onnode(size, 0);

// Query topology:
int num_nodes = numa_num_configured_nodes();
int max_node = numa_max_node();
```

### NUMA in Rust

```rust
// Using the hwloc crate for NUMA topology:
use hwloc::{Topology, ObjectType, CpuBindFlags};

let topo = Topology::new();
let nodes = topo.objects_with_type(&ObjectType::NUMANode).unwrap();
println!("NUMA nodes: {}", nodes.len());
```

---

## 19. Memory Protection — Bits, Flags, Hardware Enforcement

Pages carry permission bits enforced by the MMU in hardware. No software check is needed — the CPU refuses illegal accesses at the instruction level.

### The Three Permission Bits

```
Every PTE has three protection bits:
  P   (Present):  0=not in RAM (demand paging or invalid)
  R/W (Writable): 0=read-only, 1=read-write
  U/S (User):     0=kernel-only, 1=user accessible
  XD  (NX):       1=no-execute (the NX bit, bit 63 of PTE)
```

### NX/XD Bit — Non-Executable Pages

The NX bit prevents execution of data pages. This defeats classic shellcode injection (write shellcode to stack/heap, jump to it):

```
Without NX:
  Stack page: R/W=1, XD=0 (executable!)
  Attacker writes shellcode to stack buffer → overflows return address
  CPU happily executes stack memory → arbitrary code execution

With NX:
  Stack page: R/W=1, XD=1 (not executable)
  CPU attempts to execute stack address → #PF fault (protection violation)
  → Process killed with SIGSEGV

Linux default:
  Stack:  PROT_READ | PROT_WRITE (not executable)
  Heap:   PROT_READ | PROT_WRITE (not executable)
  Text:   PROT_READ | PROT_EXEC  (not writable)
  
  This is "W^X" (Write XOR Execute): a page is EITHER writable OR
  executable, never both simultaneously.
```

### SMEP and SMAP

Hardware defenses against kernel exploits:

```
SMEP (Supervisor Mode Execution Prevention):
  When CPU is in ring 0 (kernel mode):
  → Attempting to execute a USER-space page → #PF
  → Prevents kernel from being tricked into jumping to user-allocated code
  → Enabled if CPU supports it (Intel Sandy Bridge+, AMD 2012+)

SMAP (Supervisor Mode Access Prevention):
  When CPU is in ring 0 (kernel mode):
  → Attempting to READ OR WRITE a USER-space page → #PF
  → Prevents kernel from accidentally/maliciously accessing user memory
  → Kernel must use explicit copy_from_user() / copy_to_user() which
    temporarily disable SMAP via STAC/CLAC instructions
```

### ASLR — Address Space Layout Randomization

ASLR randomizes the base addresses of all segments on each execution:

```
Without ASLR:
  Stack always at: 0x7FFFFFFFE000
  libc always at:  0x7FFFF7A00000
  
  Attacker knows exact addresses → craft exploit with hardcoded ROP gadget addresses

With ASLR:
  Stack at:  0x7FFD2A8DE000  (random each run)
  libc at:   0x7F4BC1200000  (random each run)
  
  48-bit address space, 28 bits of stack entropy = 2^28 = 268 million possible locations
  Brute force is infeasible

Linux ASLR levels:
  /proc/sys/kernel/randomize_va_space
  0: disabled
  1: randomize stack, mmap, VDSO
  2: also randomize heap (brk) ← default
```

### mprotect — Runtime Permission Changes

```c
// JIT compilers use this pattern (e.g., LuaJIT, Java HotSpot):
void *code_buf = mmap(NULL, 4096, 
                      PROT_READ | PROT_WRITE,   // Write phase
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

// Write machine code into buffer:
memcpy(code_buf, machine_instructions, code_size);

// Switch to executable, remove write permission (W^X):
mprotect(code_buf, 4096, PROT_READ | PROT_EXEC);

// Execute:
((void(*)())code_buf)();
```

### Guard Pages

A **guard page** is a page mapped with `PROT_NONE` — no permissions at all. Any access triggers a segfault. Used to detect buffer overflows and stack overflows:

```
Stack layout with guard page:

  [stack memory: PROT_READ|PROT_WRITE]   ← actual stack
  [guard page:   PROT_NONE]              ← one page below stack
  [unmapped]

Stack overflow → touches guard page → SIGSEGV
Without guard page → stack silently corrupts heap below it
```

Rust's standard threads use an 8KB guard page by default.

---

## 20. Key Syscalls for Page Control

### mmap / munmap

```c
// Map:
void *addr = mmap(hint, length, prot, flags, fd, offset);

// Unmap (returns pages to OS):
munmap(addr, length);
```

### mprotect

```c
// Change permissions on mapped region:
mprotect(addr, length, PROT_READ | PROT_WRITE);
// Must be page-aligned. Can only change within existing VMAs.
```

### mlock / munlock / mlockall

```c
// Pin pages in RAM (prevent swap-out):
mlock(addr, length);   // pin specific region
mlockall(MCL_CURRENT | MCL_FUTURE);  // pin entire process

// Used by:
//   - OpenSSL: lock private key pages in RAM
//   - Real-time processes: guarantee no page fault latency
//   - Requires CAP_IPC_LOCK capability (or RLIMIT_MEMLOCK)

munlock(addr, length); // allow swapping again
```

### madvise

```c
// Give kernel hints about future access patterns:
madvise(addr, length, advice);

MADV_NORMAL:      no special hint (default)
MADV_SEQUENTIAL:  access will be sequential → aggressive readahead
MADV_RANDOM:      access will be random → minimal readahead
MADV_WILLNEED:    will access soon → prefetch pages into cache now
MADV_DONTNEED:    won't access for a while → free these pages
                  (for anonymous: pages are freed, next access → zero fault)
                  (for file: pages evicted from cache)
MADV_FREE:        pages are unused but don't free immediately
                  (lazy free — reuse without zeroing if no pressure)
MADV_HUGEPAGE:    use THP for this region
MADV_NOHUGEPAGE:  don't use THP for this region
MADV_DONTFORK:    don't copy to child on fork()
MADV_DONTDUMP:    exclude from core dump
```

### brk / sbrk

```c
// The original heap expansion syscall (used by malloc internally):
void *current_end = sbrk(0);   // get current heap end
sbrk(4096);                    // extend heap by 4KB
brk(new_end);                  // set heap end explicitly

// Modern malloc prefers mmap for large allocations.
// brk is used for small heap allocations to avoid mmap overhead.
```

### mremap

```c
// Resize or move a mapped region:
void *new_addr = mremap(old_addr, old_size, new_size, flags);

// This is how realloc() is implemented efficiently for large allocations:
// Kernel can remap page table entries → O(1) "move" of huge regions
// No data copying needed if no physical relocation required
```

### mincore

```c
// Query which pages are currently in RAM:
unsigned char vec[num_pages];
mincore(addr, length, vec);
// vec[i] & 1 == 1 means page i is in RAM
// vec[i] & 1 == 0 means page i is NOT in RAM (would cause major fault)

// Use case: prefault critical data, verify cache warmth
```

---

## 21. Observability — Reading the System's Memory State

### /proc/meminfo

```
MemTotal:       16384000 kB    # Total physical RAM
MemFree:          512000 kB    # Unused frames
MemAvailable:    8192000 kB    # Available without swapping (free + reclaimable cache)
Buffers:          256000 kB    # Kernel buffer cache (metadata)
Cached:          6144000 kB    # Page cache (file data)
SwapCached:        32000 kB    # Swap pages also in RAM (to avoid re-reading on fault)
Active:          5120000 kB    # Recently used pages (hard to evict)
Inactive:        3072000 kB    # Less recently used (eviction candidates)
Active(anon):    2048000 kB    # Active anonymous pages (heap/stack)
Inactive(anon):   512000 kB    # Inactive anonymous (swap candidates)
Active(file):    3072000 kB    # Active file-backed pages
Inactive(file):  2560000 kB    # Inactive file-backed (reclaimable)
Unevictable:      128000 kB    # mlock'd or special pages
Mlocked:          128000 kB    # mlock'd pages
SwapTotal:       8388608 kB    # Total swap space
SwapFree:        7168000 kB    # Unused swap
Dirty:             16384 kB    # Pages awaiting write-back to disk
Writeback:          4096 kB    # Pages currently being written to disk
AnonPages:       2560000 kB    # Total anonymous pages
Mapped:           512000 kB    # Pages in page tables (mmap'd)
Shmem:            256000 kB    # Shared memory (tmpfs, SHM)
KReclaimable:     384000 kB    # Kernel memory reclaimable under pressure
Slab:             512000 kB    # Slab allocator total
SReclaimable:     384000 kB    # Reclaimable slab (caches)
SUnreclaim:       128000 kB    # Unreclaimable slab (kernel structures)
PageTables:        64000 kB    # Memory used by page tables themselves
HugePages_Total:     256        # Number of 2MB huge pages reserved
HugePages_Free:      200        # Unused huge pages
```

### /proc/PID/maps and /proc/PID/smaps

```bash
# Basic VMA listing:
cat /proc/self/maps

# Detailed per-VMA statistics:
cat /proc/self/smaps

# smaps output for one VMA:
7f4bc1200000-7f4bc13f4000 r-xp 00000000 fd:01 12345 /lib/x86_64-linux-gnu/libc.so.6
Size:               1936 kB      # Virtual size
KernelPageSize:        4 kB      # Page size used
MMUPageSize:           4 kB
Rss:                1024 kB      # Resident set size (in RAM)
Pss:                 512 kB      # Proportional SS (RSS / sharing factor)
Shared_Clean:        900 kB      # In RAM, shared with other processes
Shared_Dirty:          0 kB
Private_Clean:       124 kB      # In RAM, private to this process
Private_Dirty:         0 kB
Referenced:         1024 kB      # Recently accessed
Anonymous:             0 kB      # Not file-backed
LazyFree:              0 kB
AnonHugePages:         0 kB      # THP usage
ShmemPmdMapped:        0 kB
Swap:                  0 kB      # Swapped-out bytes for this VMA
SwapPss:               0 kB
```

### /proc/PID/pagemap

A binary interface for per-page physical information:

```
Each 8-byte entry for page N:
  Bits 54:0  — Physical Frame Number (if present)
  Bit  55    — Page is in swap
  Bits 62:58 — Swap type (if swapped)
  Bit  63    — Page is PRESENT in RAM
```

### perf and page fault profiling

```bash
# Count page faults for a command:
perf stat -e page-faults,minor-faults,major-faults ./myprogram

# Record which code paths cause page faults:
perf record -e page-faults -g ./myprogram
perf report

# flamegraph of page fault stacks:
perf script | stackcollapse-perf.pl | flamegraph.pl > faults.svg
```

### vmstat

```bash
vmstat 1   # update every 1 second

procs  memory              swap      io    system  cpu
r  b   swpd   free  buff  cache   si   so   bi   bo  in   cs us sy id wa
1  0      0 512000 25600 614400    0    0    0    0 250  800  5  2 93  0

# si = swap-in (pages per second) → if non-zero: RAM pressure
# so = swap-out (pages per second) → if non-zero: evicting anonymous pages
# bi = blocks in from disk (page-in I/O)
# bo = blocks out to disk (dirty page writeback)
```

---

## 22. Pages in Rust, Go, and C

### Rust — Memory Safety at the Page Level

```rust
// Rust's allocator (jemalloc or system) uses mmap under the hood for large allocs.
// The borrow checker prevents use-after-free at the language level,
// but the page-level mechanisms still apply.

// Stack allocation — pages faulted in as stack grows:
fn deep_recursion(n: usize) {
    let buf = [0u8; 4096];  // 4KB on stack — faults in one page
    if n > 0 { deep_recursion(n - 1); }
}
// At depth 1000: stack has consumed ~4MB, faulting in pages as it grows
// Stack guard page catches overflow before it corrupts heap

// Checking page size:
fn page_size() -> usize {
    unsafe { libc::sysconf(libc::_SC_PAGESIZE) as usize }
}

// mmap via memmap2 crate:
use memmap2::MmapMut;
let mut mmap = MmapMut::map_anon(4096 * 1024).unwrap();
mmap[0] = 42;  // First write → page fault → frame allocated

// mlock to prevent swap:
mmap.lock().unwrap();  // mlockall equivalent for this region

// Aligning allocations to page boundaries:
use std::alloc::{alloc, Layout};
let layout = Layout::from_size_align(4096, 4096).unwrap();
let ptr = unsafe { alloc(layout) };  // guaranteed page-aligned
```

### Rust: The CoW Implication in Arc<T>

```rust
// Arc<Vec<u8>>: reference counted, shared, but CoW is NOT automatic.
// If you clone an Arc and modify the inner Vec, you must do it explicitly.

use std::sync::Arc;

let data = Arc::new(vec![1u8; 1_000_000]);  // 1MB, one allocation

// Cheap clone (just increments refcount — pointer copy):
let data2 = Arc::clone(&data);  // No memory copy. Both point to same heap page(s).

// To modify: must get exclusive access or make a copy:
let mut data3 = (*data).clone();  // NOW copies the actual 1MB
data3[0] = 99;
```

### Go — Runtime-Managed Pages

```go
package main

import (
    "runtime"
    "unsafe"
)

// Go's runtime manages pages internally via its own allocator (mheap).
// The GC works in terms of "spans" — runs of pages.

// Go span sizes: 8KB, 16KB, 32KB, ..., up to 32MB
// Small objects go into mcache (per-P, no lock)
// Large objects (>32KB) directly allocated from mheap

// Getting page size:
pageSize := int(unsafe.Sizeof(uintptr(0))) * 8  // wrong way
// Correct:
// There's no os.Getpagesize in stdlib? Actually there is:
import "os"
pageSize = os.Getpagesize()  // returns 4096 on x86-64

// Go runtime page fault behavior:
// - goroutine stacks start at 8KB, grow via page faults (actually segmented/copied)
// - Actually Go uses stack copying, NOT OS page faults for stack growth
// - The runtime detects small remaining stack → copies entire goroutine stack to new
//   larger allocation → updates all pointers (the "stack scanning" GC interaction)

// This is different from C/Rust where OS handles stack growth via page faults.

// runtime.ReadMemStats for page-level insight:
var stats runtime.MemStats
runtime.ReadMemStats(&stats)
fmt.Printf("HeapSys: %d MB\n", stats.HeapSys/1024/1024)    // Total OS pages acquired
fmt.Printf("HeapInuse: %d MB\n", stats.HeapInuse/1024/1024) // Pages with live objects
fmt.Printf("HeapIdle: %d MB\n", stats.HeapIdle/1024/1024)   // Pages returned or idle
fmt.Printf("HeapReleased: %d MB\n", stats.HeapReleased/1024/1024) // Released to OS
```

### C — Direct Page Control

```c
#include <sys/mman.h>
#include <unistd.h>

// Allocate anonymous pages:
long page_size = sysconf(_SC_PAGESIZE);
void *buf = mmap(NULL, 100 * page_size,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS,
                 -1, 0);

// Prefault all pages (avoid future fault latency):
madvise(buf, 100 * page_size, MADV_WILLNEED);
// Or explicitly touch every page:
for (size_t i = 0; i < 100 * page_size; i += page_size)
    ((volatile char*)buf)[i] = 0;

// Lock in RAM (no swap):
mlock(buf, 100 * page_size);

// Use memory...

// Return pages to OS immediately (DONTNEED = free backing):
madvise(buf, 100 * page_size, MADV_DONTNEED);

// Unmap:
munmap(buf, 100 * page_size);

// Secure clearing of sensitive data before unmap:
explicit_bzero(key_buffer, key_size);  // NOT optimized away by compiler
munmap(key_buffer, key_size);
```

---

## 23. Security — How Page Mechanisms Are Exploited and Defended

### Attack 1: Stack Buffer Overflow → Return Address Overwrite

```
Vulnerability: out-of-bounds write crosses page boundary from data
               into the page containing the return address.

Defense layers:
  1. Stack canary (SSP): random value between local vars and return addr
     → overwrite canary → detected before RET → abort()
  
  2. NX stack: PROT_EXEC not set on stack pages
     → can't inject shellcode directly
     → attacker must use ROP (Return-Oriented Programming)
  
  3. ASLR: randomize stack address
     → ROP gadget addresses are unknown
     → requires info leak to bypass
  
  4. Shadow stack (CET, Intel Control-flow Enforcement Technology):
     → Hardware maintains a second read-only stack of return addresses
     → RET checks: shadow stack return addr == stack return addr
     → Any mismatch → #CP fault → immediate termination
     → Cannot be bypassed without an ADDITIONAL kernel vulnerability
```

### Attack 2: Heap Spray

```
Attacker allocates thousands of objects containing shellcode/ROP chains,
hoping that a subsequent use-after-free or type confusion accesses one.

Page-level defense:
  ASLR on heap (vm.randomize_va_space=2): randomizes brk()
  But heap WITHIN the brk region is predictable order.
  
  Mitigation: heap randomization (jemalloc's randomized bucket selection),
              guard pages between allocations
```

### Attack 3: Meltdown / Spectre — Exploiting CPU Speculation

```
Meltdown (2018):
  Out-of-order CPU executes kernel memory read speculatively:
  
  1. Access kernel address (would normally → #PF)
  2. CPU speculatively reads the value before the permission check
  3. The speculative read loads data into cache
  4. Exception fires, rolls back the register value
  5. But the CACHE SIDE-CHANNEL remains!
  6. Attacker times memory accesses to detect cache occupancy
  7. Deduces the value that was "secretly" read
  
  Defense: KPTI (Kernel Page Table Isolation)
  → Kernel pages are UNMAPPED from user-space page tables
  → Separate page tables for user mode (no kernel mappings)
     and kernel mode (full mappings)
  → Accessing a kernel address from user mode → guaranteed #PF
     because the PTE literally doesn't exist in the user-mode page table
  → Cost: context switch now flushes TLB (CR3 change)
           ~5-30% overhead on syscall-heavy workloads
```

### Attack 4: Use-After-Free via Page Reuse

```
1. Allocate object A (secret data)
2. Free object A
3. Allocate object B (attacker-controlled) → may receive same pages
4. A's secret data still in those pages (not zeroed by default)
5. Read object B → read A's secret data

Defense:
  - Kernel zeroes pages before giving them to user processes
    (do_anonymous_page() calls clear_user_highpage())
  - Prevents cross-process information leaks
  - Does NOT prevent same-process UAF (A and B in same process)
  
  Language-level:
  - Rust: use-after-free is a compile error (borrow checker prevents it)
  - C: requires AddressSanitizer, Valgrind, or careful coding
```

### Attack 5: Dirty COW (CVE-2016-5195)

```
A race condition in Linux's CoW mechanism allowed writing to read-only
file-backed memory:

1. mmap a read-only file (PROT_READ, MAP_PRIVATE)
2. Thread 1: write() to the mapping via /proc/self/mem
3. Thread 2: madvise(MADV_DONTNEED) to throw away the CoW copy
4. Race: kernel writes to the original read-only page
         before realizing the CoW copy was discarded

Effect: write to any read-only file — including /etc/passwd, SUID binaries

Fixed in: Linux 4.8.3 (2016)
Lesson: Page table modifications must be atomic with respect to their invariants
```

---

## 24. Master Reference — Every Term Defined

| Term | Definition |
|------|-----------|
| **Page** | Fixed-size (4KB) unit of virtual address space |
| **Page Frame** | Fixed-size (4KB) unit of physical RAM |
| **PFN** | Physical Frame Number: frame's index in physical RAM |
| **VPN** | Virtual Page Number: page's index in virtual address space |
| **PTE** | Page Table Entry: maps VPN → PFN + permission bits |
| **Page Table** | Array of PTEs for a process |
| **PML4/PDPT/PD/PT** | Four levels of x86-64 page table hierarchy |
| **CR3** | CPU register holding physical address of current process's PML4 |
| **TLB** | Hardware cache of recent VA→PA translations |
| **ASID** | Address Space ID: disambiguates TLB entries across processes |
| **TLB Shootdown** | Invalidating stale TLB entries on all CPU cores |
| **Page Fault** | CPU exception when a virtual address access cannot complete |
| **Minor Fault** | Page fault resolved without disk I/O |
| **Major Fault** | Page fault requiring disk I/O |
| **Demand Paging** | Policy: only load pages into RAM when first accessed |
| **VMA** | Virtual Memory Area: contiguous range of virtual pages with shared properties |
| **CoW** | Copy-on-Write: share pages until write, then copy |
| **mmap** | Syscall mapping a file or anonymous memory into virtual address space |
| **Page Cache** | Kernel's unified cache of file data in RAM |
| **Dirty Page** | Page modified in RAM but not yet written back to disk |
| **Writeback** | Process of flushing dirty pages to disk |
| **LRU** | Least Recently Used: eviction policy, approximate in Linux |
| **Working Set** | Set of pages a process actively uses at a given time |
| **Thrashing** | Working set exceeds RAM; system spends most time on page faults |
| **Swap** | Disk area for storing evicted anonymous pages |
| **Swap-out** | Moving a page from RAM to swap disk |
| **Swap-in** | Loading a page from swap back into RAM (major fault) |
| **swappiness** | Linux parameter controlling swap aggressiveness |
| **zswap** | Compressed memory cache in front of swap disk |
| **Huge Page** | 2MB or 1GB page (reduces TLB pressure) |
| **THP** | Transparent Huge Pages: automatic 2MB page promotion |
| **Buddy Allocator** | Physical frame allocator using power-of-2 free lists |
| **Slab Allocator** | Sub-page allocator for kernel objects (SLUB is default) |
| **GFP Flags** | Context flags for kernel memory allocation (GFP_KERNEL, GFP_ATOMIC, etc.) |
| **NUMA** | Non-Uniform Memory Access: different latency for local vs remote RAM |
| **NX bit** | No-Execute: prevents executing data pages |
| **SMEP** | Supervisor Mode Execution Prevention |
| **SMAP** | Supervisor Mode Access Prevention |
| **ASLR** | Address Space Layout Randomization |
| **mprotect** | Syscall to change page permissions |
| **mlock** | Syscall to pin pages in RAM (prevent swap) |
| **madvise** | Syscall to give kernel hints about access patterns |
| **Guard Page** | PROT_NONE page used to detect buffer/stack overflow |
| **KPTI** | Kernel Page Table Isolation (Meltdown mitigation) |
| **Readahead** | Prefetching subsequent pages on a file-backed fault |
| **INVLPG** | x86 instruction: invalidate single TLB entry |
| **Page Reclaim** | Kernel process of freeing pages under memory pressure |
| **kswapd** | Kernel thread performing background page reclaim |
| **Address Space** | The complete virtual memory layout of a process (`mm_struct`) |
| **RSS** | Resident Set Size: pages of a process currently in RAM |
| **PSS** | Proportional Set Size: RSS divided by sharing factor |
| **VSZ** | Virtual Size: total virtual address space used (includes non-resident pages) |
| **mincore** | Syscall to query which pages are currently resident in RAM |
| **explicit_bzero** | Secure memory zeroing that cannot be optimized away |
| **W^X** | Write XOR Execute: security policy where pages are never both writable and executable |

---

*This guide covers the complete landscape of virtual memory pages — from the hardware transistors of the MMU through every layer of the Linux kernel, up to the language-level abstractions in Rust, Go, and C. Every concept builds on the previous. Master the page table walk, and everything else — demand paging, CoW, THP, NUMA — becomes a natural extension.*