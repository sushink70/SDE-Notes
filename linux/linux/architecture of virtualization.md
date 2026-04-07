# The Complete Architecture of Virtualization: Physical CPU, vCPU, RAM, and Virtual Memory in QEMU/KVM on Linux

> *"To understand virtualization is to understand the machine itself — layer by layer, abstraction by abstraction, until the illusion becomes transparent."*

---

## Table of Contents

1. [Foundation: What Is Physical Hardware Really?](#1-foundation-what-is-physical-hardware-really)
2. [Physical Memory (RAM): How It Actually Works](#2-physical-memory-ram-how-it-actually-works)
3. [The CPU: Rings, Modes, and Privilege Levels](#3-the-cpu-rings-modes-and-privilege-levels)
4. [Virtual Memory in Linux (Host)](#4-virtual-memory-in-linux-host)
5. [The Linux Kernel Memory Subsystem (Deep Dive)](#5-the-linux-kernel-memory-subsystem-deep-dive)
6. [Paging: Page Tables, TLB, and MMU](#6-paging-page-tables-tlb-and-mmu)
7. [KVM: Kernel-Based Virtual Machine](#7-kvm-kernel-based-virtual-machine)
8. [QEMU: The Userspace Orchestrator](#8-qemu-the-userspace-orchestrator)
9. [Virtual CPU (vCPU): Deep Architecture](#9-virtual-cpu-vcpu-deep-architecture)
10. [Memory Virtualization: The Four-Layer Model](#10-memory-virtualization-the-four-layer-model)
11. [Extended Page Tables (EPT) / Nested Paging (NPT)](#11-extended-page-tables-ept--nested-paging-npt)
12. [Guest Linux: Virtual Memory Inside the VM](#12-guest-linux-virtual-memory-inside-the-vm)
13. [The Full Memory Translation Walk](#13-the-full-memory-translation-walk)
14. [Memory Overcommit, Balloon Driver, and KSM](#14-memory-overcommit-balloon-driver-and-ksm)
15. [Huge Pages and Transparent Huge Pages (THP)](#15-huge-pages-and-transparent-huge-pages-thp)
16. [NUMA Topology in Virtual Machines](#16-numa-topology-in-virtual-machines)
17. [I/O Virtualization and Memory-Mapped I/O (MMIO)](#17-io-virtualization-and-memory-mapped-io-mmio)
18. [VM Exits: The Trap Mechanism](#18-vm-exits-the-trap-mechanism)
19. [C Implementation: Core Concepts](#19-c-implementation-core-concepts)
20. [Rust Implementation: Safe Virtualization Abstractions](#20-rust-implementation-safe-virtualization-abstractions)
21. [Performance Analysis and Tuning](#21-performance-analysis-and-tuning)
22. [Security: Spectre, Meltdown, and Side Channels in VMs](#22-security-spectre-meltdown-and-side-channels-in-vms)

---

## 1. Foundation: What Is Physical Hardware Really?

### The Physical CPU Die

A modern x86-64 CPU (Intel/AMD) is a silicon die with billions of transistors. From the virtualization perspective, the most critical structures are:

- **Execution Cores**: Each core has ALUs, FPUs, branch predictors, instruction decoders, out-of-order execution engines, and register files (general-purpose, segment, control, MSRs).
- **Cache Hierarchy**: L1 (per-core, ~32 KB I+D), L2 (per-core, ~256 KB–1 MB), L3 (shared across cores, 8–64 MB+).
- **Memory Management Unit (MMU)**: Hardware page table walker, TLB (Translation Lookaside Buffer).
- **VMCS/VMCB Support**: Intel VT-x provides `VMCS` (Virtual Machine Control Structure); AMD-V provides `VMCB` (Virtual Machine Control Block). These are special hardware memory regions that store VM state.
- **APIC**: Advanced Programmable Interrupt Controller — handles interrupts. In VMs, this becomes a virtual APIC (vAPIC).
- **MSRs**: Model-Specific Registers — thousands of them, controlling everything from power management to performance counters to virtualization behavior.

### The Memory Bus

```
CPU <--[QPI/HyperTransport/UPI]--> Memory Controller <--[DDR4/DDR5 bus]--> DIMM slots (Physical RAM)
```

The Memory Controller is integrated into modern CPUs (since ~2008). It translates physical addresses (used by the CPU after paging) into actual DRAM row/column/bank signals.

### Physical Address Space

The CPU has a physical address space — on x86-64 it can be up to 52 bits wide (2^52 bytes = 4 PB). But what occupies this address space is not only RAM:

```
Physical Address Space Layout (example, simplified):
0x0000_0000_0000 - 0x0000_0009_FFFF  : Low conventional RAM (640 KB)
0x0000_000A_0000 - 0x0000_000F_FFFF  : ROM, VGA buffer (legacy)
0x0000_0010_0000 - RAM_TOP            : Extended RAM
RAM_TOP          - 0xFFFF_FFFF        : PCI MMIO, APIC, ACPI, firmware ROMs
0x0001_0000_0000+                     : More RAM (if > 4 GB)
```

This is called the **physical memory map**. The OS (Linux kernel) reads this from BIOS/UEFI firmware via the E820 memory map.

---

## 2. Physical Memory (RAM): How It Actually Works

### DRAM Internals

Physical RAM is DRAM (Dynamic RAM) — capacitors that hold charge. Each cell = 1 bit. Cells are arranged in:
- **Banks** → **Rows** → **Columns**

Reading/writing requires: select bank → activate row (load entire row into row buffer) → access column → precharge.

### Memory Pages

The MMU and OS manage memory in fixed-size chunks called **pages**. On x86-64:
- Standard page: **4 KB** (2^12 bytes)
- Huge page: **2 MB** (2^21 bytes)
- Gigantic page: **1 GB** (2^30 bytes)

Every page has a **page frame number (PFN)** = physical address >> 12.

### The `struct page` in Linux Kernel

Every physical page of RAM is tracked by the Linux kernel with a `struct page`:

```c
// Simplified from linux/mm_types.h
struct page {
    unsigned long flags;           // PG_locked, PG_dirty, PG_uptodate, etc.
    union {
        struct {                   // For page cache / anonymous mappings
            struct address_space *mapping;
            pgoff_t index;
        };
        struct {                   // For compound pages (huge pages)
            unsigned long compound_head;
        };
        struct {                   // For slab allocator
            struct kmem_cache *slab_cache;
            void *freelist;
        };
    };
    union {
        atomic_t _mapcount;        // # of page table entries mapping this page
        unsigned int page_type;
    };
    atomic_t _refcount;            // Reference count
    // ... many more fields (64+ bytes total)
};
```

On a system with 16 GB RAM:
- Number of 4 KB pages = 16 * 1024 * 1024 * 1024 / 4096 = 4,194,304 pages
- `struct page` ≈ 64 bytes each → total overhead ≈ **256 MB just for page metadata**

### Memory Zones

Linux divides physical memory into **zones** for different purposes:

```
ZONE_DMA    : 0 - 16 MB       (legacy ISA DMA, 24-bit bus)
ZONE_DMA32  : 0 - 4 GB        (32-bit DMA capable devices)
ZONE_NORMAL : rest of RAM      (directly mapped by kernel)
ZONE_HIGHMEM: > 896 MB (32-bit only) (not permanently mapped)
ZONE_MOVABLE: for memory hot-plug / huge page defrag
```

On 64-bit systems, `ZONE_HIGHMEM` doesn't exist — the entire RAM is directly accessible.

### The Buddy Allocator

Linux uses the **buddy allocator** for physical page allocation. It manages free pages in order-based free lists (order 0 = 1 page, order 1 = 2 pages, order 2 = 4 pages, ..., order 11 = 2048 pages = 8 MB).

When you need N pages:
1. Find the smallest order ≥ log2(N)
2. If free, split the block, give one half, keep the other (the "buddy") in a lower order list
3. On free, check if the buddy is free → merge into higher order

This minimizes **external fragmentation** at the physical level.

---

## 3. The CPU: Rings, Modes, and Privilege Levels

### Privilege Rings (x86)

```
Ring 0 (most privileged): Kernel mode — direct hardware access
Ring 1: (rarely used)
Ring 2: (rarely used)
Ring 3 (least privileged): User mode — restricted instructions
```

In practice, Linux uses only Ring 0 (kernel) and Ring 3 (user).

Privileged instructions (ring 0 only):
- `lgdt` / `lidt` (load GDT/IDT)
- `mov cr0` / `mov cr3` / `mov cr4` (control registers — paging, protection)
- `wrmsr` / `rdmsr` (read/write MSRs)
- `in` / `out` (I/O port access)
- `sti` / `cli` (enable/disable interrupts)
- `hlt` (halt CPU)

### CPU Operating Modes

```
Real Mode        : 16-bit, 1 MB address space (boot state)
Protected Mode   : 32-bit, segmentation + paging, privilege rings
Long Mode        : 64-bit, paging mandatory, segmentation mostly disabled
                   ├── 64-bit mode (64-bit code)
                   └── Compatibility mode (32-bit code in 64-bit OS)
```

### VT-x / AMD-V: The Virtualization Extensions

Intel VT-x adds a new orthogonal privilege axis: **VMX root** vs **VMX non-root**.

```
VMX Root Mode   : Hypervisor runs here (KVM in Ring 0)
VMX Non-Root    : Guest runs here (restricted Ring 0-3)
```

In VMX non-root mode, even Ring 0 instructions that would normally work can cause a **VM Exit** — trapping back to the hypervisor. This is configurable via the VMCS.

**AMD-V** (also called AMD SVM — Secure Virtual Machine) is AMD's equivalent, using VMCB instead of VMCS.

### VMX Instructions

```asm
VMXON     : Enter VMX operation (hypervisor starts)
VMXOFF    : Leave VMX operation
VMLAUNCH  : Launch a new VM (first entry)
VMRESUME  : Resume a VM after VM Exit
VMEXIT    : (automatic, not an instruction) — hardware traps to hypervisor
VMREAD    : Read from VMCS field
VMWRITE   : Write to VMCS field
VMCLEAR   : Initialize/deactivate a VMCS
VMPTRLD   : Make a VMCS the current one
INVEPT    : Invalidate EPT-derived TLB entries
INVVPID   : Invalidate VPID-tagged TLB entries
```

---

## 4. Virtual Memory in Linux (Host)

### Why Virtual Memory?

Without virtual memory:
- Processes could access each other's memory
- Physical address layout would be exposed to userspace
- Memory fragmentation would be catastrophic
- No protection, no isolation

Virtual memory gives each process its own **virtual address space** — a private 64-bit address space. The CPU (via the MMU) translates virtual → physical addresses using **page tables**.

### 64-bit Virtual Address Space Layout (x86-64 Linux)

```
Virtual Address Space (48-bit canonical addresses):

0x0000_0000_0000_0000 - 0x0000_7FFF_FFFF_FFFF  : User space  (128 TB)
  0x0000_0000_0000_0000                           : NULL (unmapped, catches null ptr deref)
  0x0000_0000_0040_0000                           : text segment (typical ELF load)
  ...                                              : heap (grows up)
  0x0000_7FFF_FFFF_FFFF                           : stack (grows down, at top of user space)

  [gap - non-canonical addresses]

0xFFFF_8000_0000_0000 - 0xFFFF_FFFF_FFFF_FFFF  : Kernel space (128 TB)
  0xFFFF_8000_0000_0000 - 0xFFFF_BFFF_FFFF_FFFF  : direct mapping of all physical RAM
  0xFFFF_C000_0000_0000 - 0xFFFF_C7FF_FFFF_FFFF  : vmalloc/ioremap space
  0xFFFF_E000_0000_0000 - 0xFFFF_E7FF_FFFF_FFFF  : virtual memory map (struct page array)
  0xFFFF_FFFF_8000_0000 - 0xFFFF_FFFF_FFFF_FFFF  : kernel text, data, BSS
```

**Canonical address rule**: On x86-64 with 48-bit virtual addresses, bits 48-63 must be copies of bit 47. Anything in between (non-canonical) causes a general protection fault. This is the "hole" in the middle of the address space.

With 5-level paging (57-bit addresses), this extends to 57 bits. Linux supports this since kernel 4.14.

### Virtual Memory Areas (VMAs)

A process's virtual address space is a collection of **VMAs** (Virtual Memory Areas), represented as `struct vm_area_struct`:

```c
// Simplified from linux/mm_types.h
struct vm_area_struct {
    unsigned long vm_start;       // Start address (inclusive)
    unsigned long vm_end;         // End address (exclusive)
    struct vm_area_struct *vm_next, *vm_prev;  // Linked list
    struct rb_node vm_rb;         // Red-black tree node (for fast lookup)
    pgprot_t vm_page_prot;        // Access permissions (rwx, user/kernel)
    unsigned long vm_flags;       // VM_READ, VM_WRITE, VM_EXEC, VM_SHARED, ...
    struct mm_struct *vm_mm;      // Back pointer to process memory descriptor
    const struct vm_operations_struct *vm_ops;  // mmap/fault/close callbacks
    unsigned long vm_pgoff;       // Offset (in pages) into file/device
    struct file *vm_file;         // File being mapped (NULL for anonymous)
    void *vm_private_data;        // For driver use
};
```

Types of VMAs:
- **Anonymous**: Stack, heap, `mmap(MAP_ANONYMOUS)` — backed by physical RAM or swap
- **File-backed**: `mmap()` of a file — backed by the page cache
- **Special**: VDSO, vsyscall, MMIO regions

### Memory Descriptor: `mm_struct`

Every process has an `mm_struct` (one per process, shared across threads):

```c
struct mm_struct {
    struct vm_area_struct *mmap;       // VMA list head
    struct rb_root mm_rb;              // VMA red-black tree root
    pgd_t *pgd;                        // Page Global Directory (root of page tables)
    atomic_t mm_users;                 // # of users (threads)
    atomic_t mm_count;                 // # of references (including kernel)
    unsigned long total_vm;            // Total pages mapped
    unsigned long locked_vm;           // Pages locked in RAM (mlock)
    unsigned long pinned_vm;           // Permanently pinned
    unsigned long data_vm;             // Data segment pages
    unsigned long exec_vm;             // Executable pages
    unsigned long stack_vm;            // Stack pages
    unsigned long start_code, end_code;// Code segment bounds
    unsigned long start_data, end_data;// Data segment bounds
    unsigned long start_brk, brk;     // Heap bounds
    unsigned long start_stack;         // Stack top
    unsigned long arg_start, arg_end;  // argv
    unsigned long env_start, env_end;  // envp
    // ... much more
};
```

---

## 5. The Linux Kernel Memory Subsystem (Deep Dive)

### The Slab Allocator (kmalloc)

For kernel objects smaller than a page, Linux uses the **SLAB/SLUB/SLOB allocator** (SLUB is default):

- Maintains per-object-size caches (`kmem_cache`)
- Groups objects into slabs (one or more pages)
- Per-CPU free lists for lock-free fast allocation
- Falls through to buddy allocator for new slabs

```c
// Kernel internal allocation
void *ptr = kmalloc(size, GFP_KERNEL);  // Allocate, may sleep
void *ptr = kmalloc(size, GFP_ATOMIC);  // Allocate, cannot sleep (interrupt context)
kfree(ptr);

// Named cache for frequently allocated objects
struct kmem_cache *cache = kmem_cache_create("my_object", sizeof(struct my_obj),
                                              0, SLAB_HWCACHE_ALIGN, NULL);
struct my_obj *obj = kmem_cache_alloc(cache, GFP_KERNEL);
kmem_cache_free(cache, obj);
```

### Memory Allocation Flags (GFP — Get Free Pages)

```c
GFP_KERNEL   : Normal allocation, can sleep, can reclaim (for kernel data)
GFP_ATOMIC   : Cannot sleep (interrupt handlers, spinlock-held paths)
GFP_DMA      : Must come from DMA zone (<16 MB)
GFP_DMA32    : Must come from DMA32 zone (<4 GB)
GFP_HIGHUSER : For user pages (can use high memory)
GFP_NOWAIT   : Don't wait if memory pressure, return NULL immediately
__GFP_ZERO   : Zero the page before returning
__GFP_NOFAIL : Keep retrying until success (dangerous, may deadlock)
__GFP_NORETRY: Return NULL instead of reclaiming
```

### Page Reclaim (kswapd and Direct Reclaim)

When free memory drops below a threshold (`/proc/sys/vm/min_free_kbytes`):

1. **kswapd** (per-NUMA-node kernel thread) wakes up and starts reclaiming pages
2. Pages to reclaim are selected using LRU (Least Recently Used) lists:
   - `LRU_INACTIVE_ANON` / `LRU_ACTIVE_ANON`: Anonymous pages
   - `LRU_INACTIVE_FILE` / `LRU_ACTIVE_FILE`: File-backed pages
3. File-backed pages: write if dirty → drop
4. Anonymous pages: write to **swap** (if configured) → free

If kswapd can't keep up, **direct reclaim** happens — the allocating thread itself reclaims.

### The OOM Killer

If memory cannot be reclaimed (no swap, everything in use), the **OOM (Out Of Memory) Killer** activates:
- Scores all processes (`/proc/PID/oom_score`)
- Kills the one with highest score (typically the largest memory consumer)
- OOM score influenced by: `oom_score_adj` (`/proc/PID/oom_score_adj`, range -1000 to +1000)

For QEMU processes, it's common to set `oom_score_adj = -900` to protect VMs from being OOM-killed.

### mmap and Demand Paging

When a process calls `mmap()`, Linux does **NOT** immediately allocate physical memory. It only creates a VMA. Physical pages are allocated on first access — this is **demand paging**:

1. Process accesses a virtual address inside the VMA
2. MMU finds no valid page table entry → **page fault** (hardware exception)
3. Linux page fault handler (`do_page_fault()` → `handle_mm_fault()` → `__handle_mm_fault()`) runs
4. Handler allocates a physical page, fills it (zeroes for anonymous, reads from file for file-backed)
5. Installs a page table entry mapping virtual → physical
6. Returns from fault handler; CPU retries the faulting instruction

This is the cornerstone of **Copy-on-Write (CoW)** — used by `fork()`:
- Parent and child share the same physical pages (mapped read-only in both)
- On write by either, page fault fires → kernel allocates a new page → copies content → makes it private

---

## 6. Paging: Page Tables, TLB, and MMU

### 4-Level Paging on x86-64

A 48-bit virtual address is decoded as:

```
Bits 63-48: Sign extension (canonical check)
Bits 47-39: PGD index (9 bits → 512 entries)  [Page Global Directory]
Bits 38-30: PUD index (9 bits → 512 entries)  [Page Upper Directory]
Bits 29-21: PMD index (9 bits → 512 entries)  [Page Middle Directory]
Bits 20-12: PTE index (9 bits → 512 entries)  [Page Table Entry]
Bits 11-0:  Page offset (12 bits → 4096 bytes)
```

Page table walk for virtual address VA:
```
CR3 register → physical address of PGD
PGD[VA[47:39]] → physical address of PUD
PUD[VA[38:30]] → physical address of PMD  (or 1 GB huge page if bit 7 set)
PMD[VA[29:21]] → physical address of PT   (or 2 MB huge page if bit 7 set)
PT[VA[20:12]]  → physical address of page + VA[11:0] = final physical address
```

With **5-level paging** (57-bit addresses, CR4.LA57 = 1), a P4D level is added:
```
PGD → P4D → PUD → PMD → PT → page
```

### Page Table Entry (PTE) Format

Each PTE is 8 bytes on x86-64:

```
Bit  0  : Present (P) — entry is valid
Bit  1  : Read/Write (R/W) — 0=read-only, 1=read-write
Bit  2  : User/Supervisor (U/S) — 0=kernel only, 1=user accessible
Bit  3  : Page Write-Through (PWT)
Bit  4  : Page Cache Disable (PCD)
Bit  5  : Accessed (A) — set by hardware on any access
Bit  6  : Dirty (D) — set by hardware on write (PTE level only)
Bit  7  : Page Size (PS) — for huge pages at PMD/PUD level
Bit  8  : Global (G) — don't flush from TLB on CR3 reload (for kernel pages)
Bits 9-11: Available for OS use
Bits 12-51: Physical Page Frame Number (PFN) << 12 = physical address
Bits 52-62: Available for OS use (Linux uses some for software bits)
Bit 63  : Execute Disable (XD/NX) — page cannot be executed (requires EFER.NXE=1)
```

### The TLB (Translation Lookaside Buffer)

Page table walks require 4 memory accesses per virtual address — catastrophically slow. The TLB caches recent virtual → physical translations. Modern CPUs have:
- L1 ITLB: 128 entries (4 KB pages), 8 entries (2 MB pages)
- L1 DTLB: 64 entries (4 KB), 32 entries (2 MB), 4 entries (1 GB)
- L2 STLB: 1536–2048 unified entries

**TLB Shootdowns**: When the OS changes a page table entry, it must invalidate the TLB not only on the current CPU but on all other CPUs that might have cached the translation. This is done via **IPI (Inter-Processor Interrupt)** — very expensive (`smp_call_function_many()`). This is why `munmap()`, `mprotect()`, and `mmap()` can be slow.

**PCID (Process-Context Identifier)**: Allows TLB entries to be tagged with a process ID, avoiding full TLB flushes on context switches (introduced to mitigate Meltdown performance regression).

### KPTI (Kernel Page Table Isolation)

Post-Meltdown (2018), Linux isolates kernel and user page tables:
- User mode: minimal page tables — only user pages + tiny kernel stub (VDSO, interrupt handlers)
- Kernel mode: full page tables

On syscall/interrupt: switch CR3 (flush TLB). With PCID: tag user CR3 and kernel CR3 differently to avoid flush. Still a performance cost (~5-30%).

---

## 7. KVM: Kernel-Based Virtual Machine

### What KVM Is

KVM (Kernel-based Virtual Machine) is a **Linux kernel module** (`kvm.ko` + `kvm_intel.ko` / `kvm_amd.ko`) that turns the Linux kernel into a **Type-1.5 hypervisor**. It is:

- Not a full hypervisor by itself — it provides kernel-level virtualization primitives
- Exposed to userspace via `/dev/kvm` (ioctl interface)
- QEMU uses KVM for hardware-accelerated virtualization

KVM was merged into the mainline Linux kernel in version 2.6.20 (2007).

### KVM Architecture

```
+------------------------------------------+
|              User Space                   |
|    +-----------+      +-----------+       |
|    |  QEMU/KVM |      | libvirt   |       |
|    |  process  |      | virt-mgr  |       |
|    +-----------+      +-----------+       |
|         |                  |              |
|    ioctl(/dev/kvm)    ioctl(/dev/kvm)     |
+---------|--------------------------------+
|         ↓       Kernel Space             |
|  +------------------+                    |
|  |    KVM Module    |                    |
|  |  kvm.ko          |                    |
|  |  kvm_intel.ko    |   <-- uses VT-x   |
|  |  (or kvm_amd.ko) |   <-- uses AMD-V  |
|  +------------------+                    |
|         ↓                                |
|  +------------------+                    |
|  |  Linux Scheduler |   (schedules vCPUs)|
|  |  Memory Manager  |   (manages EPT)    |
|  |  Device drivers  |                    |
|  +------------------+                    |
+------------------------------------------+
         ↓
  Physical Hardware (VT-x / AMD-V)
```

### The `/dev/kvm` Interface

```c
// 1. Open /dev/kvm
int kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);

// 2. Check API version
int api_version = ioctl(kvm_fd, KVM_GET_API_VERSION, 0);
// Must be 12

// 3. Create a VM
int vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);
// Returns a new file descriptor for the VM

// 4. Set up memory slots
struct kvm_userspace_memory_region mem = {
    .slot = 0,
    .guest_phys_addr = 0x0,           // Guest sees this as physical address 0
    .memory_size = 256 * 1024 * 1024, // 256 MB
    .userspace_addr = (uint64_t)host_memory_ptr,  // QEMU's mmap'd buffer
    .flags = 0,
};
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &mem);

// 5. Create a vCPU
int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0); // 0 = vcpu_id

// 6. Map the kvm_run structure
int run_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
struct kvm_run *run = mmap(NULL, run_size, PROT_READ|PROT_WRITE,
                           MAP_SHARED, vcpu_fd, 0);

// 7. Run the vCPU
while (1) {
    ioctl(vcpu_fd, KVM_RUN, 0);
    switch (run->exit_reason) {
        case KVM_EXIT_HLT:   // Guest halted
        case KVM_EXIT_IO:    // Guest did I/O (in/out instruction)
        case KVM_EXIT_MMIO:  // Guest accessed MMIO region
        case KVM_EXIT_SHUTDOWN: // Guest crashed
        // etc.
    }
}
```

### KVM Memory Slots

KVM maps guest physical memory using **memory slots**. Each slot maps a contiguous range of guest physical addresses to a contiguous range of host virtual addresses (QEMU's address space).

```c
struct kvm_userspace_memory_region {
    __u32 slot;              // Slot ID (0-511 typically)
    __u32 flags;             // KVM_MEM_LOG_DIRTY_PAGES | KVM_MEM_READONLY
    __u64 guest_phys_addr;   // Start of guest physical address range
    __u64 memory_size;       // Size of the region
    __u64 userspace_addr;    // Host virtual address (QEMU's mmap buffer)
};
```

KVM then uses these memory slots to build the **Extended Page Tables (EPT)** — the second level of address translation.

### KVM Internal Structures

```c
// Simplified KVM VM structure
struct kvm {
    spinlock_t mmu_lock;
    struct mm_struct *mm;           // Host process mm (QEMU's mm)
    struct kvm_memslots *memslots;  // Array of memory slots
    struct kvm_vcpu *vcpus[KVM_MAX_VCPUS];
    // IRQ routing, IOAPIC, APIC, etc.
};

// Simplified KVM vCPU structure
struct kvm_vcpu {
    struct kvm *kvm;
    int vcpu_id;
    struct kvm_run *run;            // Shared page with userspace
    struct kvm_vcpu_arch arch;      // x86-specific state
    // ...
};

// x86-specific vCPU state
struct kvm_vcpu_arch {
    struct kvm_mmu *mmu;            // vCPU's MMU (EPT pointer)
    struct kvm_mmu *walk_mmu;
    unsigned long cr0, cr2, cr3, cr4, cr8;
    u64 efer;                       // Extended Feature Enable Register
    struct kvm_lapic *apic;         // Local APIC state
    struct kvm_regs regs;           // General purpose registers
    // MSRs, FPU state, etc.
};
```

---

## 8. QEMU: The Userspace Orchestrator

### QEMU's Role

QEMU (Quick EMUlator) is a userspace program that:
1. Emulates virtual hardware (disk controllers, network cards, USB, BIOS/UEFI, etc.)
2. Manages guest memory (allocates host virtual memory, tells KVM about it)
3. Handles VM exits that KVM cannot handle alone (MMIO, BIOS calls, virtio)
4. Provides device models (VirtIO, e1000, rtl8139, IDE, AHCI, etc.)
5. Manages vCPU threads (one thread per vCPU)

### QEMU's Memory Model

QEMU uses its own **memory model** (`MemoryRegion` tree) to represent the guest physical address space.

```c
// QEMU memory regions (simplified)
typedef struct MemoryRegion {
    const MemoryRegionOps *ops;    // Read/write callbacks (for MMIO)
    uint64_t size;
    bool ram;                      // Is this RAM or MMIO?
    uint8_t *ram_block;            // Pointer to actual host memory (for RAM regions)
    char name[32];
    QTAILQ_HEAD(, MemoryRegion) subregions;
    // ...
} MemoryRegion;
```

When QEMU starts, it:

1. **Allocates host memory** for the guest RAM:
```c
// QEMU allocates guest RAM via mmap
void *guest_ram = mmap(NULL,
                       guest_ram_size,
                       PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                       -1, 0);
```

2. **Registers it with KVM**:
```c
struct kvm_userspace_memory_region region = {
    .slot = 0,
    .guest_phys_addr = 0,           // Guest physical address 0
    .memory_size = guest_ram_size,
    .userspace_addr = (uint64_t)guest_ram,
};
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);
```

3. Now when the **guest** (the Linux kernel inside the VM) accesses what it thinks is "physical address 0x1000", KVM translates that to the host virtual address `guest_ram + 0x1000`.

### QEMU's Address Spaces

QEMU maintains multiple address spaces:
- **`address_space_memory`**: The main guest physical address space (RAM + MMIO)
- **`address_space_io`**: Guest I/O port space (for `in`/`out` instructions)
- Per-device address spaces (for PCI DMA, etc.)

### vCPU Threads

For each vCPU, QEMU creates a POSIX thread:

```c
// Each vCPU is a host thread
pthread_create(&vcpu_thread, NULL, vcpu_thread_fn, vcpu);

void *vcpu_thread_fn(void *arg) {
    CPUState *cpu = arg;
    // Initialize KVM state
    kvm_init_vcpu(cpu);
    
    while (!cpu->stopped) {
        // Run the vCPU until VM exit
        kvm_cpu_exec(cpu);
        // Handle VM exit
        handle_vm_exit(cpu);
    }
}
```

These threads are scheduled by the **Linux scheduler** like any other thread — they can be preempted, migrated between physical cores, etc.

### QEMU's BIOS/UEFI

QEMU includes (or loads):
- **SeaBIOS**: Legacy BIOS emulation (for PC-compatible VMs)
- **OVMF**: UEFI firmware (TianoCore, for modern guests)

These are loaded into the guest's physical address space before the vCPU starts executing (at physical address `0xFFFF_0000` for BIOS, which in real mode appears at `0xF000:0xFFF0`).

---

## 9. Virtual CPU (vCPU): Deep Architecture

### What a vCPU Is

A vCPU is a **software abstraction of a CPU core**. It consists of:

1. **VMCS (Intel) / VMCB (AMD)**: A hardware-managed data structure in physical memory that contains the full guest CPU state + hypervisor control fields.

2. **KVM state**: `struct kvm_vcpu` and `struct kvm_vcpu_arch` in kernel memory.

3. **QEMU state**: `CPUState` and `X86CPU` structures in QEMU's heap.

### The VMCS Structure (Intel VT-x)

The VMCS is a 4 KB (or larger) page that the hardware uses to save/restore guest state on VM exits/entries. It contains:

**Guest State Area**: Loaded into CPU registers on VM entry
```
CR0, CR3, CR4          : Guest control registers
ES, CS, SS, DS, FS, GS : Segment registers (selector, base, limit, attributes)
LDTR, TR               : Local Descriptor Table, Task Register
GDTR, IDTR             : GDT and IDT base/limit
DR7                    : Debug register
RSP, RIP, RFLAGS       : Stack pointer, instruction pointer, flags
IA32_DEBUGCTL MSR
SYSENTER_CS/ESP/EIP MSRs
Guest PDPTE registers (for PAE paging)
Guest EFER MSR
Guest activity state (active/halted/shutdown/wait-for-SIPI)
```

**Host State Area**: Restored on VM exit (hypervisor state)
```
CR0, CR3, CR4
ES, CS, SS, DS, FS, GS
TR, GDTR, IDTR
RSP, RIP (hypervisor entry point on VM exit)
IA32_SYSENTER_CS/ESP/EIP
FS.base, GS.base, TR.base, GDTR.base, IDTR.base
IA32_EFER, IA32_PAT
```

**VM Execution Control Fields**: What triggers VM exits
```
Pin-based controls:
  External-interrupt exiting: VM exit on hardware interrupt?
  NMI exiting: VM exit on NMI?
  Virtual NMIs
  VMX-preemption timer

Processor-based controls:
  Interrupt-window exiting
  Use TSC offsetting
  HLT exiting: VM exit on HLT instruction?
  INVLPG exiting
  MWAIT exiting
  RDPMC exiting
  RDTSC exiting
  CR3-load exiting, CR3-store exiting
  CR8-load exiting, CR8-store exiting
  MOV-DR exiting
  Unconditional I/O exiting (or bitmap-based)
  Use I/O bitmaps
  Use MSR bitmaps
  MONITOR exiting
  PAUSE exiting
  Activate secondary controls

Secondary processor-based controls:
  Enable EPT (Extended Page Tables)
  Enable VPID
  Enable unrestricted guest
  APIC-register virtualization
  Virtual-interrupt delivery
  Enable VMFUNC
  ENCLS exiting
```

**VM Exit Information Fields**:
```
Exit reason (why did we exit?)
Exit qualification (additional detail)
Guest linear address (for page faults)
Guest physical address (for EPT violations)
VM-exit interruption information
VM-exit instruction length
VM-exit instruction information
```

### vCPU State Save/Restore

On every VM exit, hardware automatically:
1. Saves guest registers to VMCS Guest State Area
2. Loads host registers from VMCS Host State Area
3. Sets exit reason fields
4. Jumps to host entry point (KVM's `vmx_vmexit` handler)

On every VM entry (`VMRESUME`), hardware automatically:
1. Restores guest registers from VMCS Guest State Area
2. Jumps to guest RIP

### TSC (Time Stamp Counter) Virtualization

The guest needs a consistent, correct view of time. The real TSC ticks at the physical CPU's rate, but:
- VMs can be paused, migrated, or scheduled on different cores
- Different physical cores may have slightly different TSC values (TSC skew)

KVM handles this via **TSC offsetting** (VMCS field): guest sees `rdtsc` result + offset. The offset is adjusted on migration.

For live migration, **TSC scaling** is also needed if source and destination CPUs have different frequencies.

### vCPU Scheduling

vCPU threads are scheduled by the Linux scheduler (CFS — Completely Fair Scheduler). This has implications:
- A vCPU "thinks" it's always running, but it actually gets preempted
- **vCPU steal time**: Time a vCPU was runnable but not scheduled (visible as `st` in `top` inside the guest)
- **Paravirtualized tickless scheduling**: The guest can tell KVM "I'm halting, please don't wake me until an interrupt" via `HLT` instruction, so the vCPU thread sleeps instead of spinning

```c
// KVM handle of HLT instruction (simplified)
static int handle_halt(struct kvm_vcpu *vcpu) {
    vcpu->arch.halt_request = 1;
    kvm_vcpu_halt(vcpu);         // Thread sleeps in wait_event()
    return 1;
}
```

---

## 10. Memory Virtualization: The Four-Layer Model

### Your Intuition Was Correct — Here Is the Complete Picture

You said: *"host provides virtual RAM for KVM/QEMU and that gives native-like RAM for Linux to run, and that guest Linux also makes virtual RAM for processes."*

**This is exactly correct.** Let's name each layer precisely:

```
Layer 1: Host Physical Address (HPA)
         ↑
         Managed by: Host hardware MMU + Host Linux kernel
         ↑
Layer 2: Host Virtual Address (HVA)
         ↑
         This is QEMU's address space — a huge mmap'd buffer IS the guest's "RAM"
         ↑
Layer 3: Guest Physical Address (GPA)
         ↑
         What the guest OS (and its kernel) thinks is "physical RAM"
         ↑
Layer 4: Guest Virtual Address (GVA)
         ↑
         What guest processes see — managed by the guest Linux kernel
```

### Detailed Layer Breakdown

#### Layer 1 → 2: Host Physical to Host Virtual (Standard Linux Paging)

The host Linux kernel manages physical RAM normally. QEMU is just a process — it has an `mm_struct` with VMAs. The guest RAM is a `MAP_ANONYMOUS | MAP_PRIVATE` VMA in QEMU's address space.

- Host Linux page tables: `GVA_host_QEMU → HPA`
- These are normal 4-level page tables managed by the host kernel

#### Layer 2 → 3: Host Virtual to Guest Physical (EPT/NPT)

This is the key virtualization layer. The EPT (Extended Page Table) maps:
- `GPA (Guest Physical Address) → HPA (Host Physical Address)`

EPT is a hardware page table structure maintained by KVM in kernel memory. When the guest CPU accesses a GPA, the MMU walks the EPT to find the HPA.

Without EPT (software emulation — "shadow page tables"):
- KVM maintained page tables that mapped `GVA → HPA` directly
- On every guest page table modification, KVM had to update shadow page tables
- Extremely expensive — every guest CR3 write caused a VM exit

With EPT (hardware — modern standard):
- Guest manages its own `GVA → GPA` page tables freely
- Hardware MMU uses EPT to translate `GPA → HPA` automatically
- No VM exits for guest page table modifications

#### Layer 3 → 4: Guest Physical to Guest Virtual (Guest Linux Paging)

Inside the guest VM, Linux runs exactly as it would on bare metal. It:
- Sets up page tables in what it thinks is physical RAM (but is actually GPA space)
- Manages `GVA → GPA` mappings for all guest processes
- Handles page faults, memory allocation, etc.

The guest has no idea it's inside a VM (unless it checks CPUID or uses paravirt).

### The Complete Address Translation Path

```
Guest process accesses GVA 0x7FFF_1234_5678

Step 1: Guest MMU walks guest page tables (GVA → GPA)
        Guest CR3 = GPA of guest PGD
        GPA_of_PGD = 0x0010_0000 (example)
        
        MMU needs to READ memory at GPA_of_PGD to start the walk
        → Triggers EPT walk: GPA 0x0010_0000 → HPA ?
        
Step 2: EPT walk for each page table level (GPA → HPA)
        EPT root (EPTP in VMCS) → HPA of EPT PML4
        EPT PML4[GPA[47:39]] → HPA of EPT PDP
        EPT PDP[GPA[38:30]]  → HPA of EPT PD
        EPT PD[GPA[29:21]]   → HPA of EPT PT
        EPT PT[GPA[20:12]]   → HPA of the guest PGD page
        Final HPA = EPT_PT_entry_value + GPA[11:0]

Step 3: Now the guest MMU can read guest PGD at the actual HPA
        Continues guest page table walk (GVA → GPA) for each level
        Each intermediate GPA must be EPT-walked to get to HPA

Step 4: Eventually obtains GPA of the actual data page
        One more EPT walk → HPA of data page
        
Step 5: Access HPA + offset within page
        Data is read from physical RAM

Total: Up to 24 memory accesses for a TLB-cold 4-level GVA→GPA + 4-level EPT walk
       (4 guest page table levels × 5 EPT walks each, but TLB/EPT cache helps)
```

---

## 11. Extended Page Tables (EPT) / Nested Paging (NPT)

### EPT Structure

EPT uses the same 4-level (or 5-level) structure as regular page tables, but with different entry formats:

**EPT Entry Format**:
```
Bit 0   : Read access
Bit 1   : Write access
Bit 2   : Execute access (for supervisor-mode linear addresses)
Bits 5-3: Memory type (for MTRR/PAT — 0=UC, 1=WC, 4=WT, 5=WP, 6=WB)
Bit 6   : Ignore PAT (use memory type from EPT entry directly)
Bit 7   : Page Size (for 2 MB at EPT PDE, 1 GB at EPT PDPE)
Bit 8   : Accessed (set by hardware)
Bit 9   : Dirty (set by hardware on write)
Bit 10  : Execute access for user-mode linear addresses
Bits 51-12: Physical address (PFN) of next table or final page
Bit 63  : Suppress #VE (virtualization exceptions)
```

**EPT Violation** (EPT equivalent of page fault):
- When the guest accesses a GPA with no valid EPT entry, or with wrong permissions
- Causes a VM exit with exit reason = EPT Violation
- KVM handles it: allocates a host page, populates the EPT entry, resumes guest

### EPT Memory Faults and the GPA Lifecycle

```
Guest accesses GPA → EPT miss → VM Exit (EPT Violation)
    ↓
KVM: kvm_mmu_page_fault()
    ↓
KVM: tdp_page_fault() [for Two-Dimensional Paging, i.e., EPT]
    ↓
KVM: kvm_tdp_mmu_map() — allocate EPT page tables if needed
    ↓
KVM: kvm_faultin_pfn() — get host page for GPA
    ↓
    [If GPA → HVA mapping exists (from KVM memory slot)]
    KVM converts GPA → HVA (using memory slot: HVA = slot->userspace_addr + (GPA - slot->base_gfn * PAGE_SIZE))
    ↓
    KVM calls get_user_pages_fast(HVA) — pins the host page
    This may trigger host page fault if the QEMU page was never touched
    ↓
KVM: tdp_mmu_set_spte() — install entry in EPT
    ↓
VM entry resumed — guest continues
```

### VPID (Virtual Processor Identifier)

Without VPID, every VM entry/exit required TLB flushing (since guest and host translations are different). VPID tags TLB entries with a 16-bit identifier:
- Host: VPID = 0
- Each VM: VPID = some nonzero value

This allows guest and host TLB entries to coexist, drastically reducing VM entry/exit overhead.

### INVEPT and INVVPID

When EPT entries are modified (e.g., page unmapped), the EPT-cached translations must be invalidated:

```asm
; Invalidate all EPT-derived translations for a specific EPTP
INVEPT  EAX, [mem]   ; mem = {0, EPTP}  (type 1: single context)
INVEPT  EAX, [mem]   ; type 2: all contexts

; Invalidate VPID-tagged TLB entries
INVVPID EAX, [mem]   ; type 0: individual address
                      ; type 1: single context (all addresses for one VPID)
                      ; type 2: all contexts
                      ; type 3: single context retaining globals
```

KVM calls these via `kvm_flush_remote_tlbs()` when EPT entries change.

---

## 12. Guest Linux: Virtual Memory Inside the VM

### Guest Linux's Perspective

Inside the VM, the guest Linux kernel has no knowledge of the host. From its perspective:
- It has "physical RAM" (actually GPA space)
- It reads the memory map from the virtual BIOS/UEFI (e820 table, ACPI)
- It sets up its own page tables (GVA → GPA)
- It manages its own buddy allocator, SLUB, VMAs, etc.

The guest Linux kernel **itself uses virtual memory** just like the host kernel. Its `mm_structs`, VMAs, page tables — all are identical in structure to what runs on bare metal. The only difference is that "physical RAM" is actually GPA space.

### Guest Process Memory (GVA → GPA)

A process inside the VM has:
- GVA 0x7FFF... → GPA (managed by guest kernel page tables)
- GPA (what guest kernel thinks is physical) → HPA (via EPT, invisible to guest)

The guest kernel's `mm_struct.pgd` points to a GPA. The guest's page table entries contain GPAs (which they believe are physical addresses).

### The Double Fault Path

If a guest process causes a page fault:
1. Guest hardware raises a page fault exception
2. Guest kernel's page fault handler runs (at guest Ring 0)
3. Guest kernel may need to allocate a new page (from its own buddy allocator)
4. Guest kernel writes a new GVA → GPA mapping into page tables
5. If the GPA has no EPT entry yet → another (nested) EPT violation VM exit
6. KVM allocates a host page, maps GPA → HPA in EPT
7. Guest kernel continues, page fault handler returns
8. Guest process resumes

### QEMU's Guest Physical Memory Lifecycle

```
QEMU starts:
  mmap(NULL, guest_ram_size, PROT_READ|PROT_WRITE,
       MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE, -1, 0)
  → Creates a VMA in QEMU's address space
  → NO physical pages allocated yet (MAP_NORESERVE means no swap reserved either)

Guest accesses GPA 0x1000:
  → EPT violation VM exit
  → KVM: GPA 0x1000 → HVA (QEMU mmap base + 0x1000)
  → KVM calls get_user_pages(HVA)
  → Host Linux: HVA not backed → page fault → allocate physical page → zero it
  → Host page table: HVA → HPA
  → KVM: populate EPT: GPA 0x1000 → HPA
  → Resume guest

Result: Physical RAM is allocated lazily, on first guest access.
This is "demand paging" at two levels — guest AND host.
```

---

## 13. The Full Memory Translation Walk

### Complete Walk: GVA → GPA → HPA (With EPT)

Let's trace a complete translation for a 64-bit guest on a 64-bit host. Guest accesses GVA = `0x0000_7FFF_1234_5000`.

**Given:**
- Guest CR3 = GPA `0x0010_0000` (guest's root page table)
- EPT root = HPA `0x0020_0000` (set in VMCS EPTP field)

**Step 1: EPT walk for guest PGD (to read PGD entry)**
```
GPA to translate: 0x0010_0000 (guest CR3)

EPT PML4 base = HPA 0x0020_0000
GPA[47:39] = 0 → EPT PML4[0] → HPA 0x0020_1000 (EPT PDP base)
GPA[38:30] = 0 → EPT PDP[0]  → HPA 0x0020_2000 (EPT PD base)
GPA[29:21] = 0 → EPT PD[0]   → HPA 0x0020_3000 (EPT PT base)
GPA[20:12] = 0x100 → EPT PT[0x100] → HPA 0x4000_0000

GPA 0x0010_0000 maps to HPA 0x4000_0000 + 0x000 = HPA 0x4000_0000
```

**Step 2: Read guest PGD entry at HPA 0x4000_0000**
```
GVA bits [47:39] = 0xFF = 255 → PGD[255] at HPA 0x4000_0000 + 255*8
Read 8 bytes → PGD entry = GPA 0x0010_1000 | flags
```

**Step 3: EPT walk for guest PUD (to read PUD entry)**
```
GPA 0x0010_1000 → EPT walk → HPA 0x4000_1000
Read guest PUD entry at HPA 0x4000_1000 + GVA[38:30]*8
→ PUD entry = GPA 0x0010_2000 | flags
```

**Step 4: EPT walk for guest PMD**
```
GPA 0x0010_2000 → EPT walk → HPA 0x4000_2000
Read guest PMD entry → GPA 0x0010_3000 | flags
```

**Step 5: EPT walk for guest PT**
```
GPA 0x0010_3000 → EPT walk → HPA 0x4000_3000
Read guest PT entry at + GVA[20:12]*8
→ PT entry = GPA 0x0100_0000 | flags
```

**Step 6: EPT walk for actual data page**
```
GPA 0x0100_0000 → EPT walk → HPA 0x5000_0000

Final physical access:
HPA 0x5000_0000 + GVA[11:0] (0x000) = HPA 0x5000_0000

Done: GVA 0x7FFF_1234_5000 → HPA 0x5000_0000
```

**Total memory accesses (worst case, cold TLB and EPT)**:
- 4 EPT walks × 4 levels each = 16 EPT memory accesses
- 4 guest page table reads = 4 memory accesses (each needing EPT walks above)
- 1 final data access
- **Total: ~24 memory reads** (in practice, TLBs and EPT caches reduce this dramatically)

### AMD-V: Nested Page Tables (NPT)

AMD's equivalent of EPT. Works identically in concept but uses:
- `nCR3` field in VMCB instead of EPTP in VMCS
- 4-level page table with slight format differences
- `INVLPGA` instruction instead of INVVPID
- `#NPF` (Nested Page Fault) instead of EPT Violation

---

## 14. Memory Overcommit, Balloon Driver, and KSM

### Memory Overcommit

QEMU by default uses `MAP_NORESERVE` — it doesn't commit physical RAM upfront. This enables **memory overcommit**: running VMs whose total configured RAM exceeds host physical RAM.

```
Host physical RAM: 16 GB
VM1 configured: 8 GB  (guest thinks it has 8 GB)
VM2 configured: 8 GB  (guest thinks it has 8 GB)
VM3 configured: 8 GB  (guest thinks it has 8 GB)
Total configured: 24 GB > 16 GB physical
```

This works because:
- Not all guest RAM is necessarily used at once
- OS pages are demand-paged — only used GPA ranges consume HPA
- If overcommit goes too far → OOM killer or host swapping

The host kernel's overcommit policy is controlled by:
```bash
# /proc/sys/vm/overcommit_memory:
# 0 = heuristic (default)
# 1 = always allow (DANGEROUS for VM hosts)
# 2 = never overcommit beyond (RAM + SWAP) * overcommit_ratio / 100
cat /proc/sys/vm/overcommit_ratio  # default 50
```

### The Balloon Driver (virtio-balloon)

The balloon driver is a guest kernel driver (`virtio_balloon`) that coordinates with QEMU/host to dynamically adjust the effective guest RAM:

**Inflate** (host needs memory back):
1. QEMU tells balloon driver: "give me N pages"
2. Guest balloon driver allocates N pages from guest buddy allocator
3. Guest balloon driver tells QEMU the GFNs (guest frame numbers)
4. QEMU calls `madvise(ptr, size, MADV_DONTNEED)` on the corresponding HVAs
5. Host kernel frees the physical pages backing those HVAs
6. Guest OS can no longer use those pages (they're "in the balloon")

**Deflate** (give memory back to guest):
1. Guest balloon driver releases held pages
2. Guest buddy allocator regains them
3. On next guest access → EPT fault → host re-allocates physical pages

```c
// Balloon driver interaction via virtio queue
// Guest kernel side (drivers/virtio/virtio_balloon.c)
static void fill_balloon(struct virtio_balloon *vb, size_t num) {
    for (i = 0; i < num; i++) {
        page = alloc_page(GFP_HIGHUSER | __GFP_NOMEMALLOC | __GFP_NORETRY);
        vb->pfns[i] = page_to_balloon_pfn(page);
    }
    // Tell host via virtio queue
    tell_host(vb, vb->inflate_vq);
}
```

### KSM (Kernel Same-page Merging)

KSM is a Linux kernel feature that scans memory pages and merges identical ones:

1. KSM daemon (`ksmd`) periodically scans registered memory regions
2. Computes a hash of each page content
3. Pages with identical content are merged into a single physical page (mapped copy-on-write in all processes)
4. On write → CoW → new page allocated

For VMs, KSM can dramatically reduce RAM usage when multiple VMs run the same OS (identical kernel pages, shared libraries, etc.).

```bash
# Enable KSM
echo 1 > /sys/kernel/mm/ksm/run
echo 1000 > /sys/kernel/mm/ksm/pages_to_scan  # pages per scan cycle
echo 20 > /sys/kernel/mm/ksm/sleep_millisecs

# QEMU marks guest RAM as KSM-eligible
madvise(guest_ram, guest_ram_size, MADV_MERGEABLE);

# Check KSM stats
cat /sys/kernel/mm/ksm/pages_shared    # pages currently shared
cat /sys/kernel/mm/ksm/pages_sharing   # pages saved
```

---

## 15. Huge Pages and Transparent Huge Pages (THP)

### Why Huge Pages Matter for VMs

With 4 KB pages, EPT for 8 GB of guest RAM needs:
- 8 GB / 4 KB = 2,097,152 PTE entries in EPT
- Multiple levels of EPT tables
- Each EPT miss → memory access to walk the table
- High TLB pressure (limited TLB entries per page)

With 2 MB huge pages:
- 8 GB / 2 MB = 4,096 large PTE entries
- 512× fewer EPT entries
- Dramatic TLB reach improvement
- EPT walks faster (one level less)

### Explicit Huge Pages (HugeTLBFS)

```bash
# Allocate 2 MB huge pages on host
echo 4096 > /proc/sys/vm/nr_hugepages  # 4096 * 2 MB = 8 GB for VMs

# QEMU uses huge pages for guest RAM:
# -mem-path /dev/hugepages -mem-prealloc
qemu-system-x86_64 -m 8G \
    -mem-path /dev/hugepages \
    -mem-prealloc \
    ...
```

QEMU maps guest RAM using `mmap()` on `/dev/hugepages`, getting 2 MB mappings. KVM then maps EPT with 2 MB entries.

### Transparent Huge Pages (THP)

THP (enabled by default in Linux) automatically promotes 4 KB page groups to 2 MB huge pages when a VMA has 2 MB-aligned, 2 MB-sized, contiguous anonymous pages all present in memory.

```bash
# THP policy:
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# For VMs: use madvise mode, QEMU advises with MADV_HUGEPAGE
madvise(guest_ram, guest_ram_size, MADV_HUGEPAGE);
```

THP for VMs is beneficial but has a caveat: **khugepaged** (the promotion daemon) can cause latency spikes while it copies pages to promote them.

### 1 GB Huge Pages

For extremely large, latency-sensitive VMs:

```bash
# Reserve 1 GB huge pages at boot (cannot be allocated dynamically)
# Add to kernel command line:
hugepagesz=1G hugepages=16  # 16 GB as 1 GB pages

# Verify
cat /proc/meminfo | grep Huge
```

KVM with 1 GB huge pages creates EPT entries at the PDP level, giving the largest TLB reach.

---

## 16. NUMA Topology in Virtual Machines

### Physical NUMA

Modern multi-socket servers have NUMA (Non-Uniform Memory Access):

```
Socket 0 (NUMA node 0):        Socket 1 (NUMA node 1):
  CPU cores 0-15                 CPU cores 16-31
  Local RAM: 64 GB               Local RAM: 64 GB
      ↑                               ↑
      └─────── QPI/UPI link ──────────┘

Access latency:
  Socket 0 CPU → Socket 0 RAM: ~100 ns (local)
  Socket 0 CPU → Socket 1 RAM: ~160 ns (remote, ~1.6× slower)
```

### Exposing NUMA to the Guest

QEMU can expose a virtual NUMA topology to the guest:

```bash
qemu-system-x86_64 \
    -m 16G \
    -smp 8,sockets=2,cores=2,threads=2 \
    -numa node,nodeid=0,cpus=0-3,mem=8G \
    -numa node,nodeid=1,cpus=4-7,mem=8G \
    -numa dist,src=0,dst=1,val=20 \
    ...
```

The guest Linux will see 2 NUMA nodes and schedule accordingly.

### Host NUMA Pinning

For best performance, pin the VM's vCPUs and memory to the same host NUMA node:

```bash
# Pin QEMU process to NUMA node 0
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# Or use libvirt's <numatune>
```

Without pinning, vCPU threads may run on socket 0 while guest RAM is on socket 1 → remote NUMA accesses → 60% bandwidth penalty.

---

## 17. I/O Virtualization and Memory-Mapped I/O (MMIO)

### MMIO in VMs

Physical devices expose registers and buffers via MMIO — memory regions that, when read/written, interact with the hardware (not actual RAM).

In a VM, when the guest writes to a GPA that falls in an MMIO region (not backed by real RAM):

1. EPT entry for that GPA has present bit = 0 (or is marked as MMIO)
2. → EPT Violation VM Exit
3. KVM identifies it as MMIO (not regular RAM miss)
4. KVM exits to QEMU with `KVM_EXIT_MMIO`
5. QEMU's device model handles the access (e.g., writes to emulated PCI config space)
6. QEMU returns result to KVM
7. VM resumed

This is **slow** (~10,000 ns per MMIO operation).

### VirtIO: Para-Virtualized I/O

VirtIO avoids MMIO overhead by using shared memory rings (virtqueues):

1. Guest driver places request in a virtqueue (shared memory ring buffer)
2. Guest writes one value to a "kick" register (one MMIO write → one VM Exit)
3. QEMU processes multiple requests from the ring in one VM exit
4. QEMU places responses in the ring
5. QEMU injects a virtual interrupt to the guest
6. Guest driver reads all responses

This batching drastically improves I/O throughput.

```
Virtqueue structure:
  Descriptor Table: Array of buffer descriptors (guest physical address + length + flags)
  Available Ring: Guest → Host: "I've added descriptor N to the queue"
  Used Ring: Host → Guest: "I've processed descriptor N, here's the result"
```

### VFIO: Direct Hardware Assignment

For maximum performance, hardware devices can be directly assigned to VMs using VFIO (Virtual Function I/O) / IOMMU:

- The IOMMU (Intel VT-d / AMD-Vi) provides DMA remapping
- The physical device DMA engine uses guest physical addresses
- The IOMMU translates GPA → HPA for DMA operations
- Guest device driver talks directly to real hardware
- Near-native performance (only overhead: interrupt injection)

```bash
# Enable IOMMU
# Kernel command line: intel_iommu=on iommu=pt

# Bind device to vfio-pci driver
echo "1234 5678" > /sys/bus/pci/drivers/vfio-pci/new_id

# Pass to QEMU
qemu-system-x86_64 -device vfio-pci,host=0000:02:00.0 ...
```

---

## 18. VM Exits: The Trap Mechanism

### What Causes a VM Exit

A VM Exit is the hardware mechanism by which the guest CPU returns control to the hypervisor. Exit reasons include:

```
0  : Exception or NMI (page fault, #GP, #UD, etc.)
1  : External interrupt (hardware IRQ while guest running)
2  : Triple fault (guest triple-faulted → shutdown)
7  : Interrupt window (hypervisor can now inject interrupt)
9  : Task switch
10 : CPUID instruction
12 : HLT instruction
13 : INVD instruction
14 : INVLPG instruction
16 : RDPMC instruction
17 : RDTSC instruction
18 : RSM instruction
21 : VMCALL instruction (hypercall from guest)
28 : MOV CR (read/write control registers)
29 : MOV DR (debug registers)
30 : I/O instruction (in/out)
31 : RDMSR (read model-specific register)
32 : WRMSR (write model-specific register)
33 : VM-entry failure (invalid guest state)
36 : MWAIT instruction
40 : PAUSE instruction
41 : VM-entry failure (machine check)
43 : TPR below threshold (virtual APIC)
44 : APIC access
48 : EPT violation
49 : EPT misconfiguration
54 : WBINVD instruction
55 : XSETBV instruction
```

### VM Exit Overhead

A VM exit + re-entry costs approximately:
- **Intel (no EPT)**: 1,000–5,000 cycles
- **Intel (with EPT, no VPID)**: 1,500–8,000 cycles (TLB flush overhead)
- **Intel (with EPT + VPID)**: 800–3,000 cycles
- **AMD (with NPT)**: similar

This is why minimizing VM exits is critical for performance.

### Paravirtualization (KVM-specific hypercalls)

To reduce VM exits, KVM implements **paravirtualization** — the guest knows it's in a VM and uses optimized paths:

```c
// Guest detects KVM via CPUID leaf 0x40000000
// "KVMKVMKVM\0\0\0" signature

// KVM hypercalls (VMCALL instruction)
#define KVM_HC_VAPIC_POLL_IRQ      1
#define KVM_HC_MMU_OP             2  (deprecated)
#define KVM_HC_FEATURES           3
#define KVM_HC_PPC_MAP_MAGIC_PAGE 4
#define KVM_HC_KICK_CPU           5
#define KVM_HC_MIPS_GET_CLOCK_FREQ 6
#define KVM_HC_CLOCK_PAIRING      9
#define KVM_HC_SEND_IPI          10
#define KVM_HC_SCHED_YIELD       11
```

**Paravirt TLB shootdown**: Instead of each vCPU sending IPIs (each causing a VM exit), KVM provides `KVM_HC_SEND_IPI` — a single hypercall that KVM handles, sending virtual IPIs to target vCPUs without expensive exit-per-CPU.

**PV clock**: `kvmclock` — guest reads time via a shared memory page (no VM exit needed for `clock_gettime`).

**PV steal time**: Kernel accounts for time the vCPU was runnable but not scheduled. Available via `/proc/stat` `steal` field.

---

## 19. C Implementation: Core Concepts

### Minimal KVM-Based Hypervisor in C

```c
// minimal_kvm.c
// A minimal hypervisor demonstrating the KVM API
// Runs a tiny piece of guest code: write 'H' to serial port, then HLT

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/kvm.h>
#include <stdint.h>

#define GUEST_MEM_SIZE  (1 << 22)  // 4 MB guest physical RAM
#define GUEST_LOAD_ADDR 0x1000     // Guest code starts at GPA 0x1000

// Minimal 16-bit real-mode guest code
// Writes 'H' to I/O port 0x3F8 (COM1), then halts
static const uint8_t guest_code[] = {
    0xb0, 0x48,        // mov al, 'H'
    0xe6, 0x3f,        // out 0x3f, al  (low byte of 0x3F8)
    0xf4,              // hlt
};

// Wait for COM1 status register to confirm ready (simplified: skip that here)

typedef struct {
    int kvm_fd;
    int vm_fd;
    int vcpu_fd;
    void *guest_mem;
    struct kvm_run *run;
} HypervisorState;

static int setup_kvm(HypervisorState *h) {
    // 1. Open /dev/kvm
    h->kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (h->kvm_fd < 0) {
        perror("open /dev/kvm");
        return -1;
    }

    // 2. Check API version
    int api_version = ioctl(h->kvm_fd, KVM_GET_API_VERSION, 0);
    if (api_version != 12) {
        fprintf(stderr, "KVM API version mismatch: %d\n", api_version);
        return -1;
    }

    // 3. Check for required extensions
    if (!ioctl(h->kvm_fd, KVM_CHECK_EXTENSION, KVM_CAP_USER_MEMORY)) {
        fprintf(stderr, "KVM_CAP_USER_MEMORY not available\n");
        return -1;
    }

    // 4. Create VM
    h->vm_fd = ioctl(h->kvm_fd, KVM_CREATE_VM, 0);
    if (h->vm_fd < 0) {
        perror("KVM_CREATE_VM");
        return -1;
    }

    return 0;
}

static int setup_memory(HypervisorState *h) {
    // Allocate guest physical memory
    h->guest_mem = mmap(NULL, GUEST_MEM_SIZE,
                        PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                        -1, 0);
    if (h->guest_mem == MAP_FAILED) {
        perror("mmap guest memory");
        return -1;
    }

    // Copy guest code at GPA GUEST_LOAD_ADDR
    memcpy((uint8_t *)h->guest_mem + GUEST_LOAD_ADDR, guest_code, sizeof(guest_code));

    // Register memory slot with KVM
    struct kvm_userspace_memory_region mem_region = {
        .slot            = 0,
        .flags           = 0,
        .guest_phys_addr = 0x0,              // GPA 0 maps to our mmap
        .memory_size     = GUEST_MEM_SIZE,
        .userspace_addr  = (uint64_t)h->guest_mem,
    };

    if (ioctl(h->vm_fd, KVM_SET_USER_MEMORY_REGION, &mem_region) < 0) {
        perror("KVM_SET_USER_MEMORY_REGION");
        return -1;
    }

    return 0;
}

static int setup_vcpu(HypervisorState *h) {
    // Create vCPU 0
    h->vcpu_fd = ioctl(h->vm_fd, KVM_CREATE_VCPU, 0);
    if (h->vcpu_fd < 0) {
        perror("KVM_CREATE_VCPU");
        return -1;
    }

    // Map kvm_run structure
    int mmap_size = ioctl(h->kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
    if (mmap_size < 0) {
        perror("KVM_GET_VCPU_MMAP_SIZE");
        return -1;
    }

    h->run = mmap(NULL, mmap_size,
                  PROT_READ | PROT_WRITE,
                  MAP_SHARED, h->vcpu_fd, 0);
    if (h->run == MAP_FAILED) {
        perror("mmap kvm_run");
        return -1;
    }

    // Set up initial CPU state (16-bit real mode)
    struct kvm_sregs sregs;
    if (ioctl(h->vcpu_fd, KVM_GET_SREGS, &sregs) < 0) {
        perror("KVM_GET_SREGS");
        return -1;
    }

    // Set CS to point to our code segment
    // In real mode: CS.base = CS.selector * 16
    // We want execution at GPA 0x1000
    // So: CS.selector = 0x0000, CS.base = 0x0000, then IP = 0x1000
    sregs.cs.selector = 0x0000;
    sregs.cs.base     = 0x0000;

    if (ioctl(h->vcpu_fd, KVM_SET_SREGS, &sregs) < 0) {
        perror("KVM_SET_SREGS");
        return -1;
    }

    // Set RIP to 0x1000 (GPA where we loaded the code)
    struct kvm_regs regs = {};
    regs.rip    = GUEST_LOAD_ADDR;
    regs.rflags = 0x0002;  // Reserved bit 1 must be set

    if (ioctl(h->vcpu_fd, KVM_SET_REGS, &regs) < 0) {
        perror("KVM_SET_REGS");
        return -1;
    }

    return 0;
}

static int run_vm(HypervisorState *h) {
    printf("[Hypervisor] Starting VM...\n");

    while (1) {
        // Enter guest mode (blocks until VM exit)
        if (ioctl(h->vcpu_fd, KVM_RUN, 0) < 0) {
            perror("KVM_RUN");
            return -1;
        }

        switch (h->run->exit_reason) {
            case KVM_EXIT_HLT:
                printf("[Hypervisor] Guest halted (HLT instruction).\n");
                return 0;

            case KVM_EXIT_IO:
                // Guest executed an I/O instruction (in/out)
                if (h->run->io.direction == KVM_EXIT_IO_OUT) {
                    // The I/O data is in run->io data area
                    uint8_t *data = (uint8_t *)h->run + h->run->io.data_offset;
                    printf("[Hypervisor] Guest I/O write: port=0x%x, size=%d, data=0x%x ('%c')\n",
                           h->run->io.port,
                           h->run->io.size,
                           *data,
                           (*data >= 32 && *data < 127) ? *data : '?');
                }
                break;

            case KVM_EXIT_MMIO:
                printf("[Hypervisor] MMIO: addr=0x%llx, len=%d, is_write=%d\n",
                       h->run->mmio.phys_addr,
                       h->run->mmio.len,
                       h->run->mmio.is_write);
                break;

            case KVM_EXIT_SHUTDOWN:
                printf("[Hypervisor] Guest triple-faulted (shutdown).\n");
                return -1;

            case KVM_EXIT_FAIL_ENTRY:
                fprintf(stderr, "[Hypervisor] VM entry failed: hardware_entry_failure_reason=0x%llx\n",
                        h->run->fail_entry.hardware_entry_failure_reason);
                return -1;

            default:
                fprintf(stderr, "[Hypervisor] Unexpected exit reason: %d\n", h->run->exit_reason);
                return -1;
        }
    }
}

int main(void) {
    HypervisorState h = {};

    if (setup_kvm(&h) < 0)    { return 1; }
    if (setup_memory(&h) < 0) { return 1; }
    if (setup_vcpu(&h) < 0)   { return 1; }
    if (run_vm(&h) < 0)        { return 1; }

    printf("[Hypervisor] VM completed successfully.\n");
    return 0;
}
```

### Page Table Walker in C

```c
// page_table_walker.c
// Demonstrates walking x86-64 page tables from userspace
// Uses /proc/self/pagemap and /proc/kpageflags for physical page info

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#define PAGE_SIZE       4096ULL
#define PAGE_SHIFT      12
#define PAGEMAP_ENTRY   8ULL

typedef struct {
    uint64_t pfn    : 55;  // Page Frame Number (if present)
    uint64_t soft_dirty : 1;
    uint64_t exclusive  : 1;
    uint64_t unused     : 4;
    uint64_t file_anon  : 1;  // 0=anon, 1=file
    uint64_t swap       : 1;
    uint64_t present    : 1;  // Page is in RAM (not swapped)
} __attribute__((packed)) PagemapEntry;

// Read pagemap entry for a virtual address
static int get_pagemap_entry(int pagemap_fd, uintptr_t vaddr, PagemapEntry *entry) {
    uint64_t offset = (vaddr / PAGE_SIZE) * PAGEMAP_ENTRY;
    if (pread(pagemap_fd, entry, PAGEMAP_ENTRY, offset) != PAGEMAP_ENTRY) {
        perror("pread pagemap");
        return -1;
    }
    return 0;
}

// Get physical address of a virtual address
static uintptr_t virt_to_phys(uintptr_t vaddr) {
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0) { perror("open pagemap"); return 0; }

    PagemapEntry entry;
    if (get_pagemap_entry(fd, vaddr, &entry) < 0) {
        close(fd);
        return 0;
    }
    close(fd);

    if (!entry.present) {
        printf("  Page NOT present (swapped or never faulted)\n");
        return 0;
    }
    return (entry.pfn * PAGE_SIZE) + (vaddr & (PAGE_SIZE - 1));
}

// Demonstrate virtual memory info for a buffer
static void analyze_buffer(const char *label, void *buf, size_t size) {
    uintptr_t vaddr = (uintptr_t)buf;
    printf("\n=== %s ===\n", label);
    printf("Virtual address:  0x%016lx\n", vaddr);
    printf("VMA page aligned: 0x%016lx\n", vaddr & ~(PAGE_SIZE - 1));
    printf("Page offset:      0x%lx\n",    vaddr & (PAGE_SIZE - 1));

    uintptr_t paddr = virt_to_phys(vaddr);
    if (paddr) {
        printf("Physical address: 0x%016lx\n", paddr);
        printf("Physical PFN:     0x%lx (%lu)\n", paddr >> PAGE_SHIFT, paddr >> PAGE_SHIFT);
    }
    printf("Size:             %zu bytes\n", size);
}

// Demonstrate demand paging: allocate large buffer but only access some
static void demo_demand_paging(void) {
    printf("\n=== Demand Paging Demonstration ===\n");

    const size_t BUFSIZE = 16 * 1024 * 1024;  // 16 MB
    char *buf = malloc(BUFSIZE);

    printf("Allocated 16 MB buffer at %p\n", buf);
    printf("First page (before access): ");
    virt_to_phys((uintptr_t)buf);  // May not be present yet

    // Access first page
    buf[0] = 'A';
    printf("First page (after write): ");
    uintptr_t pa = virt_to_phys((uintptr_t)buf);
    if (pa) printf("  → Physical: 0x%lx\n", pa);

    // Access middle page
    buf[BUFSIZE / 2] = 'B';
    printf("Middle page (after write): ");
    pa = virt_to_phys((uintptr_t)buf + BUFSIZE / 2);
    if (pa) printf("  → Physical: 0x%lx\n", pa);

    free(buf);
}

// EPT-equivalent: show how GPA → HVA translation works conceptually
static void demo_memory_slot_logic(void) {
    printf("\n=== Memory Slot Logic (GPA → HVA) ===\n");

    // Simulate what KVM does: map GPA ranges to host virtual addresses
    typedef struct {
        uint64_t guest_phys_addr;  // GPA start
        uint64_t memory_size;      // Region size
        uint64_t userspace_addr;   // HVA start (host mmap base)
    } MemSlot;

    // Simulate 256 MB guest RAM at GPA 0
    size_t guest_ram_size = 256 * 1024 * 1024;
    void *host_buf = mmap(NULL, guest_ram_size,
                          PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                          -1, 0);

    MemSlot slot = {
        .guest_phys_addr = 0x0,
        .memory_size     = guest_ram_size,
        .userspace_addr  = (uint64_t)host_buf,
    };

    printf("Memory slot:\n");
    printf("  GPA range: 0x%llx - 0x%llx\n",
           slot.guest_phys_addr,
           slot.guest_phys_addr + slot.memory_size - 1);
    printf("  HVA range: 0x%llx - 0x%llx\n",
           slot.userspace_addr,
           slot.userspace_addr + slot.memory_size - 1);

    // GPA → HVA translation (what KVM does internally)
    uint64_t test_gpa = 0x0010_0000;  // 1 MB mark
    uint64_t hva = slot.userspace_addr + (test_gpa - slot.guest_phys_addr);
    printf("\nGPA 0x%llx → HVA 0x%llx\n", test_gpa, hva);

    // Write to HVA (simulating guest writing to "physical RAM")
    *(uint64_t *)hva = 0xDEADBEEFCAFEBABE;
    printf("Wrote 0xDEADBEEFCAFEBABE to guest 'physical' address 0x%llx\n", test_gpa);

    // Verify by reading back
    uint64_t readback = *(uint64_t *)hva;
    printf("Readback: 0x%llx %s\n", readback,
           readback == 0xDEADBEEFCAFEBABE ? "(correct)" : "(ERROR)");

    munmap(host_buf, guest_ram_size);
}

int main(void) {
    int x = 42;
    int *heap = malloc(sizeof(int));
    *heap = 99;

    analyze_buffer("Stack variable", &x, sizeof(x));
    analyze_buffer("Heap variable", heap, sizeof(*heap));
    analyze_buffer("Code segment", (void*)main, 1);

    demo_demand_paging();
    demo_memory_slot_logic();

    free(heap);
    return 0;
}
```

### Memory-Mapped I/O Emulation in C

```c
// mmio_emulation.c
// Demonstrates how a hypervisor handles MMIO emulation
// When a guest accesses a non-RAM GPA, KVM exits to userspace with KVM_EXIT_MMIO

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Simulated MMIO device: a simple 256-byte register file
typedef struct {
    uint8_t   regs[256];
    uint64_t  base_gpa;  // Base guest physical address of this device
} MmioDevice;

typedef struct {
    uint64_t phys_addr;  // GPA that was accessed
    uint8_t  data[8];    // Data read/written
    uint32_t len;        // Access size (1, 2, 4, 8 bytes)
    uint8_t  is_write;   // 1=write, 0=read
} MmioAccess;

// Handle an MMIO access from the guest
// Returns 0 on success, -1 if GPA not in our device range
int mmio_dispatch(MmioDevice *dev, MmioAccess *acc) {
    if (acc->phys_addr < dev->base_gpa ||
        acc->phys_addr + acc->len > dev->base_gpa + sizeof(dev->regs)) {
        return -1;  // Not our device
    }

    uint32_t offset = (uint32_t)(acc->phys_addr - dev->base_gpa);

    if (acc->is_write) {
        memcpy(&dev->regs[offset], acc->data, acc->len);
        printf("[MMIO] WRITE: GPA=0x%lx, offset=0x%x, len=%u, data=",
               acc->phys_addr, offset, acc->len);
        for (uint32_t i = 0; i < acc->len; i++)
            printf("%02x ", acc->data[i]);
        printf("\n");
    } else {
        memcpy(acc->data, &dev->regs[offset], acc->len);
        printf("[MMIO] READ:  GPA=0x%lx, offset=0x%x, len=%u, data=",
               acc->phys_addr, offset, acc->len);
        for (uint32_t i = 0; i < acc->len; i++)
            printf("%02x ", acc->data[i]);
        printf("\n");
    }

    return 0;
}

// Simulate the hypervisor main loop handling MMIO exits
void simulate_hypervisor_mmio_loop(void) {
    MmioDevice virtio_device = {
        .base_gpa = 0xFEBC_0000,  // VirtIO MMIO base (common address)
        .regs = {0},
    };

    // Initialize some device registers
    // VirtIO magic value (0x74726976 = "virt")
    uint32_t magic = 0x74726976;
    memcpy(&virtio_device.regs[0], &magic, 4);

    // Simulate guest accesses (normally come from KVM_EXIT_MMIO)
    MmioAccess accesses[] = {
        // Guest reads magic register at offset 0
        { .phys_addr = 0xFEBC_0000, .len = 4, .is_write = 0 },
        // Guest writes queue_num_max at offset 0x38
        { .phys_addr = 0xFEBC_0038, .len = 4, .is_write = 1,
          .data = { 0x80, 0x00, 0x00, 0x00 } },
        // Guest reads it back
        { .phys_addr = 0xFEBC_0038, .len = 4, .is_write = 0 },
    };

    printf("=== MMIO Emulation Simulation ===\n");
    for (size_t i = 0; i < sizeof(accesses)/sizeof(accesses[0]); i++) {
        if (mmio_dispatch(&virtio_device, &accesses[i]) < 0) {
            printf("[MMIO] ERROR: No device at GPA 0x%lx\n", accesses[i].phys_addr);
        }
    }
}

int main(void) {
    simulate_hypervisor_mmio_loop();
    return 0;
}
```

### EPT / Page Table Structure in C

```c
// ept_structure.c
// Demonstrates the EPT page table structure

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define EPT_READ    (1ULL << 0)
#define EPT_WRITE   (1ULL << 1)
#define EPT_EXEC    (1ULL << 2)
#define EPT_WB      (6ULL << 3)   // Write-back memory type
#define EPT_PS      (1ULL << 7)   // Page size (huge page at PD/PDP level)
#define EPT_ACCESSED (1ULL << 8)
#define EPT_DIRTY   (1ULL << 9)
#define EPT_RWX     (EPT_READ | EPT_WRITE | EPT_EXEC)

#define PAGE_SIZE   4096ULL
#define PAGE_SHIFT  12

typedef uint64_t ept_entry_t;

// EPT page table (512 entries × 8 bytes = 4096 bytes = 1 page)
typedef struct {
    ept_entry_t entries[512];
} __attribute__((aligned(4096))) EptTable;

// Simulated EPT: maps GPA 0x0 - 0x3FFFFF (4 MB) to HPA 0x40000000+
typedef struct {
    EptTable *pml4;   // Level 4 (PML4)
    // For simplicity, pre-allocate all levels
} EptContext;

static uint64_t gpa_index(uint64_t gpa, int level) {
    // Level 4 (PML4): bits 47:39
    // Level 3 (PDP):  bits 38:30
    // Level 2 (PD):   bits 29:21
    // Level 1 (PT):   bits 20:12
    int shift = 12 + (level - 1) * 9;
    return (gpa >> shift) & 0x1FF;
}

void print_ept_walk(EptTable *pml4, uint64_t gpa) {
    printf("\n=== EPT Walk for GPA 0x%012lx ===\n", gpa);
    printf("Indices: PML4[%lu] PDP[%lu] PD[%lu] PT[%lu] Offset[0x%lx]\n",
           gpa_index(gpa, 4),
           gpa_index(gpa, 3),
           gpa_index(gpa, 2),
           gpa_index(gpa, 1),
           gpa & (PAGE_SIZE - 1));
}

// Create a minimal 4-level EPT mapping GPA→HPA
EptContext *ept_create(void) {
    EptContext *ctx = calloc(1, sizeof(EptContext));
    // In a real implementation, these tables are physically contiguous
    // and their physical addresses are used in EPT entries.
    // Here we simulate with virtual addresses for demonstration.
    ctx->pml4 = aligned_alloc(PAGE_SIZE, sizeof(EptTable));
    memset(ctx->pml4, 0, sizeof(EptTable));
    return ctx;
}

// Map a single 4 KB GPA → HPA in the EPT
// Returns 0 on success
int ept_map_page(EptContext *ctx, uint64_t gpa, uint64_t hpa, uint64_t flags) {
    uint64_t i4 = gpa_index(gpa, 4);
    uint64_t i3 = gpa_index(gpa, 3);
    uint64_t i2 = gpa_index(gpa, 2);
    uint64_t i1 = gpa_index(gpa, 1);

    // Level 4: PML4
    EptTable *pdp_table;
    if (!(ctx->pml4->entries[i4] & EPT_READ)) {
        pdp_table = aligned_alloc(PAGE_SIZE, sizeof(EptTable));
        memset(pdp_table, 0, sizeof(EptTable));
        // In real EPT: use HPA of pdp_table, here we use VA for demo
        ctx->pml4->entries[i4] = ((uint64_t)pdp_table & ~(PAGE_SIZE-1)) | EPT_RWX;
    } else {
        pdp_table = (EptTable *)(ctx->pml4->entries[i4] & ~0xFFFULL);
    }

    // Level 3: PDP
    EptTable *pd_table;
    if (!(pdp_table->entries[i3] & EPT_READ)) {
        pd_table = aligned_alloc(PAGE_SIZE, sizeof(EptTable));
        memset(pd_table, 0, sizeof(EptTable));
        pdp_table->entries[i3] = ((uint64_t)pd_table & ~(PAGE_SIZE-1)) | EPT_RWX;
    } else {
        pd_table = (EptTable *)(pdp_table->entries[i3] & ~0xFFFULL);
    }

    // Level 2: PD
    EptTable *pt_table;
    if (!(pd_table->entries[i2] & EPT_READ)) {
        pt_table = aligned_alloc(PAGE_SIZE, sizeof(EptTable));
        memset(pt_table, 0, sizeof(EptTable));
        pd_table->entries[i2] = ((uint64_t)pt_table & ~(PAGE_SIZE-1)) | EPT_RWX;
    } else {
        pt_table = (EptTable *)(pd_table->entries[i2] & ~0xFFFULL);
    }

    // Level 1: PT — leaf entry maps GPA→HPA
    pt_table->entries[i1] = (hpa & ~(PAGE_SIZE-1)) | flags | EPT_WB;

    printf("EPT: mapped GPA 0x%012lx → HPA 0x%012lx (flags: %c%c%c)\n",
           gpa, hpa,
           (flags & EPT_READ)  ? 'R' : '-',
           (flags & EPT_WRITE) ? 'W' : '-',
           (flags & EPT_EXEC)  ? 'X' : '-');

    return 0;
}

int main(void) {
    EptContext *ept = ept_create();

    // Simulate mapping first 4 MB of guest RAM (GPA 0x0 - 0x3FFFFF)
    // to host physical 0x40000000+
    uint64_t host_base = 0x40000000;
    for (uint64_t offset = 0; offset < 4 * 1024 * 1024; offset += PAGE_SIZE) {
        ept_map_page(ept, offset, host_base + offset, EPT_RWX);
    }

    // Demonstrate the walk
    print_ept_walk(ept->pml4, 0x0000_1234_5000);
    print_ept_walk(ept->pml4, 0x003F_FFFF_F000);

    return 0;
}
```

---

## 20. Rust Implementation: Safe Virtualization Abstractions

### KVM Abstraction Layer in Rust

```rust
// kvm_abstractions.rs
// Safe Rust wrappers around the KVM ioctl interface
// This is the kind of code found in rust-vmm/kvm-ioctls

use std::fs::{File, OpenOptions};
use std::os::unix::io::{AsRawFd, RawFd, FromRawFd};
use std::os::raw::c_int;
use std::ptr;

// ─── KVM ioctl numbers (x86_64 Linux) ───────────────────────────────────────

const KVM_GET_API_VERSION:       u64 = 0xAE00;
const KVM_CREATE_VM:             u64 = 0xAE01;
const KVM_CHECK_EXTENSION:       u64 = 0xAE03;
const KVM_GET_VCPU_MMAP_SIZE:    u64 = 0xAE04;
const KVM_CREATE_VCPU:           u64 = 0xAE41;
const KVM_SET_USER_MEMORY_REGION:u64 = 0x4020AE46;
const KVM_RUN:                   u64 = 0xAE80;
const KVM_GET_REGS:              u64 = 0x8090AE81;
const KVM_SET_REGS:              u64 = 0x4090AE82;
const KVM_GET_SREGS:             u64 = 0x8138AE83;
const KVM_SET_SREGS:             u64 = 0x4138AE84;

// ─── Structures ─────────────────────────────────────────────────────────────

#[repr(C)]
#[derive(Debug, Default)]
pub struct KvmUserspaceMemoryRegion {
    pub slot:            u32,
    pub flags:           u32,
    pub guest_phys_addr: u64,
    pub memory_size:     u64,
    pub userspace_addr:  u64,
}

// KVM exit reasons
#[repr(u32)]
#[derive(Debug, PartialEq)]
pub enum KvmExitReason {
    Unknown   = 0,
    Exception = 1,
    Io        = 2,
    Hypercall = 3,
    Debug     = 4,
    Hlt       = 5,
    Mmio      = 6,
    IrqWindow = 7,
    Shutdown  = 8,
    FailEntry = 9,
    Other(u32),
}

impl From<u32> for KvmExitReason {
    fn from(v: u32) -> Self {
        match v {
            0 => Self::Unknown,
            1 => Self::Exception,
            2 => Self::Io,
            3 => Self::Hypercall,
            4 => Self::Debug,
            5 => Self::Hlt,
            6 => Self::Mmio,
            7 => Self::IrqWindow,
            8 => Self::Shutdown,
            9 => Self::FailEntry,
            n => Self::Other(n),
        }
    }
}

// ─── Error type ─────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum KvmError {
    OpenFailed(std::io::Error),
    ApiVersionMismatch(i32),
    CreateVmFailed(std::io::Error),
    CreateVcpuFailed(std::io::Error),
    MmapFailed(std::io::Error),
    IoctlFailed { name: &'static str, err: std::io::Error },
    InvalidGpa(u64),
}

impl std::fmt::Display for KvmError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Self::OpenFailed(e)          => write!(f, "Failed to open /dev/kvm: {e}"),
            Self::ApiVersionMismatch(v)  => write!(f, "KVM API version mismatch: {v}"),
            Self::CreateVmFailed(e)      => write!(f, "KVM_CREATE_VM failed: {e}"),
            Self::CreateVcpuFailed(e)    => write!(f, "KVM_CREATE_VCPU failed: {e}"),
            Self::MmapFailed(e)          => write!(f, "mmap failed: {e}"),
            Self::IoctlFailed { name, err } =>
                write!(f, "ioctl({name}) failed: {err}"),
            Self::InvalidGpa(gpa)        => write!(f, "Invalid GPA: 0x{gpa:x}"),
        }
    }
}

// ─── KVM handle ──────────────────────────────────────────────────────────────

pub struct Kvm {
    file: File,
}

impl Kvm {
    pub fn open() -> Result<Self, KvmError> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open("/dev/kvm")
            .map_err(KvmError::OpenFailed)?;

        let kvm = Self { file };

        // Verify KVM API version
        let version = kvm.ioctl_noarg(KVM_GET_API_VERSION)?;
        if version != 12 {
            return Err(KvmError::ApiVersionMismatch(version));
        }

        Ok(kvm)
    }

    pub fn create_vm(&self) -> Result<Vm, KvmError> {
        let fd = self.ioctl_noarg(KVM_CREATE_VM)
            .map_err(|e| KvmError::CreateVmFailed(e.into()))?;
        Ok(Vm {
            file: unsafe { File::from_raw_fd(fd) },
            kvm_fd: self.file.as_raw_fd(),
        })
    }

    pub fn vcpu_mmap_size(&self) -> Result<usize, KvmError> {
        self.ioctl_noarg(KVM_GET_VCPU_MMAP_SIZE)
            .map(|v| v as usize)
    }

    fn ioctl_noarg(&self, request: u64) -> Result<i32, std::io::Error> {
        let ret = unsafe {
            libc_ioctl(self.file.as_raw_fd(), request, 0usize)
        };
        if ret < 0 {
            Err(std::io::Error::last_os_error())
        } else {
            Ok(ret as i32)
        }
    }
}

// ─── VM handle ───────────────────────────────────────────────────────────────

pub struct Vm {
    file: File,
    kvm_fd: RawFd,
}

impl Vm {
    /// Register a memory slot mapping guest physical → host virtual memory
    pub fn set_user_memory_region(
        &self,
        slot: u32,
        guest_phys_addr: u64,
        memory_size: u64,
        userspace_addr: u64,
    ) -> Result<(), KvmError> {
        let region = KvmUserspaceMemoryRegion {
            slot,
            flags: 0,
            guest_phys_addr,
            memory_size,
            userspace_addr,
        };
        let ret = unsafe {
            libc_ioctl(
                self.file.as_raw_fd(),
                KVM_SET_USER_MEMORY_REGION,
                &region as *const _ as usize,
            )
        };
        if ret < 0 {
            Err(KvmError::IoctlFailed {
                name: "KVM_SET_USER_MEMORY_REGION",
                err: std::io::Error::last_os_error(),
            })
        } else {
            Ok(())
        }
    }

    pub fn create_vcpu(&self, id: u64) -> Result<Vcpu, KvmError> {
        let fd = unsafe {
            libc_ioctl(self.file.as_raw_fd(), KVM_CREATE_VCPU, id)
        };
        if fd < 0 {
            return Err(KvmError::CreateVcpuFailed(std::io::Error::last_os_error()));
        }

        // Get mmap size from KVM fd
        let mmap_size = unsafe {
            libc_ioctl(self.kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0)
        };
        if mmap_size < 0 {
            return Err(KvmError::MmapFailed(std::io::Error::last_os_error()));
        }

        // mmap the kvm_run structure
        let run_ptr = unsafe {
            libc::mmap(
                ptr::null_mut(),
                mmap_size as usize,
                libc::PROT_READ | libc::PROT_WRITE,
                libc::MAP_SHARED,
                fd as RawFd,
                0,
            )
        };
        if run_ptr == libc::MAP_FAILED {
            return Err(KvmError::MmapFailed(std::io::Error::last_os_error()));
        }

        Ok(Vcpu {
            file: unsafe { File::from_raw_fd(fd as RawFd) },
            run_ptr: run_ptr as *mut KvmRun,
            run_size: mmap_size as usize,
        })
    }
}

// ─── kvm_run structure (partial) ─────────────────────────────────────────────

#[repr(C)]
pub struct KvmRun {
    pub request_interrupt_window: u8,
    pub immediate_exit:           u8,
    _padding1:                    [u8; 6],
    pub exit_reason:              u32,
    pub ready_for_interrupt_injection: u8,
    pub if_flag:                  u8,
    pub flags:                    u16,
    pub cr8:                      u64,
    pub apic_base:                u64,
    // Union for exit-specific data (simplified)
    pub exit_data:                [u8; 256],
}

// ─── vCPU handle ─────────────────────────────────────────────────────────────

pub struct Vcpu {
    file:     File,
    run_ptr:  *mut KvmRun,
    run_size: usize,
}

impl Vcpu {
    pub fn run(&self) -> Result<KvmExitReason, KvmError> {
        let ret = unsafe { libc_ioctl(self.file.as_raw_fd(), KVM_RUN, 0) };
        if ret < 0 {
            return Err(KvmError::IoctlFailed {
                name: "KVM_RUN",
                err: std::io::Error::last_os_error(),
            });
        }
        let exit_reason = unsafe { (*self.run_ptr).exit_reason };
        Ok(KvmExitReason::from(exit_reason))
    }

    pub fn kvm_run(&self) -> &KvmRun {
        unsafe { &*self.run_ptr }
    }

    pub fn kvm_run_mut(&mut self) -> &mut KvmRun {
        unsafe { &mut *self.run_ptr }
    }
}

impl Drop for Vcpu {
    fn drop(&mut self) {
        unsafe {
            libc::munmap(self.run_ptr as *mut libc::c_void, self.run_size);
        }
    }
}

// ─── Guest memory: RAII wrapper ───────────────────────────────────────────────

pub struct GuestMemory {
    ptr:  *mut u8,
    size: usize,
}

impl GuestMemory {
    /// Allocate anonymous memory for guest RAM (demand-paged, overcommittable)
    pub fn new(size: usize) -> Result<Self, KvmError> {
        let ptr = unsafe {
            libc::mmap(
                ptr::null_mut(),
                size,
                libc::PROT_READ | libc::PROT_WRITE,
                libc::MAP_PRIVATE | libc::MAP_ANONYMOUS | libc::MAP_NORESERVE,
                -1,
                0,
            )
        };
        if ptr == libc::MAP_FAILED {
            return Err(KvmError::MmapFailed(std::io::Error::last_os_error()));
        }
        Ok(Self { ptr: ptr as *mut u8, size })
    }

    /// Write bytes at a guest physical address offset
    pub fn write_at(&mut self, gpa_offset: usize, data: &[u8]) -> Result<(), KvmError> {
        if gpa_offset + data.len() > self.size {
            return Err(KvmError::InvalidGpa(gpa_offset as u64));
        }
        unsafe {
            ptr::copy_nonoverlapping(data.as_ptr(), self.ptr.add(gpa_offset), data.len());
        }
        Ok(())
    }

    /// Read bytes from a guest physical address offset
    pub fn read_at(&self, gpa_offset: usize, buf: &mut [u8]) -> Result<(), KvmError> {
        if gpa_offset + buf.len() > self.size {
            return Err(KvmError::InvalidGpa(gpa_offset as u64));
        }
        unsafe {
            ptr::copy_nonoverlapping(self.ptr.add(gpa_offset), buf.as_mut_ptr(), buf.len());
        }
        Ok(())
    }

    pub fn host_addr(&self) -> u64 {
        self.ptr as u64
    }

    pub fn size(&self) -> usize {
        self.size
    }
}

impl Drop for GuestMemory {
    fn drop(&mut self) {
        unsafe {
            libc::munmap(self.ptr as *mut libc::c_void, self.size);
        }
    }
}

// Safety: GuestMemory owns the memory exclusively
unsafe impl Send for GuestMemory {}
unsafe impl Sync for GuestMemory {}

// ─── Page table abstractions in Rust ─────────────────────────────────────────

/// Represents a 64-bit page table entry (host or guest, same format)
#[derive(Clone, Copy, Debug, Default)]
#[repr(transparent)]
pub struct PageTableEntry(u64);

impl PageTableEntry {
    // Flags
    pub const PRESENT:    u64 = 1 << 0;
    pub const WRITABLE:   u64 = 1 << 1;
    pub const USER:       u64 = 1 << 2;
    pub const ACCESSED:   u64 = 1 << 5;
    pub const DIRTY:      u64 = 1 << 6;
    pub const HUGE_PAGE:  u64 = 1 << 7;
    pub const GLOBAL:     u64 = 1 << 8;
    pub const NO_EXECUTE: u64 = 1 << 63;

    const PFN_MASK: u64 = 0x000F_FFFF_FFFF_F000;

    pub fn new_page(pfn: u64, flags: u64) -> Self {
        Self((pfn << 12) | flags | Self::PRESENT)
    }

    pub fn new_table(pfn: u64) -> Self {
        Self((pfn << 12) | Self::PRESENT | Self::WRITABLE | Self::USER)
    }

    pub fn pfn(self) -> u64 {
        (self.0 & Self::PFN_MASK) >> 12
    }

    pub fn is_present(self) -> bool { self.0 & Self::PRESENT != 0 }
    pub fn is_writable(self) -> bool { self.0 & Self::WRITABLE != 0 }
    pub fn is_user(self) -> bool { self.0 & Self::USER != 0 }
    pub fn is_huge(self) -> bool { self.0 & Self::HUGE_PAGE != 0 }
    pub fn is_nx(self) -> bool { self.0 & Self::NO_EXECUTE != 0 }
}

impl std::fmt::Display for PageTableEntry {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "PTE(pfn=0x{:010x}, {}{}{}{}{}{})",
            self.pfn(),
            if self.is_present()  { "P" } else { "-" },
            if self.is_writable() { "W" } else { "-" },
            if self.is_user()     { "U" } else { "K" },
            if self.is_huge()     { "H" } else { "-" },
            if self.is_nx()       { "X" } else { "-" },
            if self.0 & PageTableEntry::ACCESSED != 0 { "A" } else { "-" },
        )
    }
}

/// Virtual address decomposition for 4-level x86-64 paging
#[derive(Debug)]
pub struct Vaddr48 {
    pub raw:    u64,
    pub pgd:    usize,  // PGD index (bits 47:39)
    pub pud:    usize,  // PUD index (bits 38:30)
    pub pmd:    usize,  // PMD index (bits 29:21)
    pub pte:    usize,  // PTE index (bits 20:12)
    pub offset: usize,  // Page offset (bits 11:0)
}

impl Vaddr48 {
    pub fn new(vaddr: u64) -> Self {
        Self {
            raw:    vaddr,
            pgd:    ((vaddr >> 39) & 0x1FF) as usize,
            pud:    ((vaddr >> 30) & 0x1FF) as usize,
            pmd:    ((vaddr >> 21) & 0x1FF) as usize,
            pte:    ((vaddr >> 12) & 0x1FF) as usize,
            offset: (vaddr & 0xFFF)          as usize,
        }
    }

    pub fn is_canonical(&self) -> bool {
        // Bits 63:48 must be sign-extension of bit 47
        let bit47 = (self.raw >> 47) & 1;
        let high = self.raw >> 48;
        if bit47 == 0 { high == 0 } else { high == 0xFFFF }
    }
}

impl std::fmt::Display for Vaddr48 {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f,
            "VA 0x{:016x}: PGD[{}] PUD[{}] PMD[{}] PTE[{}] +0x{:x} ({}canonical)",
            self.raw, self.pgd, self.pud, self.pmd, self.pte, self.offset,
            if self.is_canonical() { "" } else { "non-" }
        )
    }
}

// ─── Memory translation simulation ───────────────────────────────────────────

/// Four-layer memory translation model
/// Demonstrates GVA → GPA → HPA chain
pub struct TranslationModel {
    /// Simulated guest page tables: GVA → GPA mappings
    guest_mappings: std::collections::HashMap<u64, u64>,
    /// Simulated EPT: GPA → HPA mappings
    ept_mappings:   std::collections::HashMap<u64, u64>,
}

impl TranslationModel {
    pub fn new() -> Self {
        Self {
            guest_mappings: std::collections::HashMap::new(),
            ept_mappings:   std::collections::HashMap::new(),
        }
    }

    /// Map a GVA page → GPA page (guest kernel action)
    pub fn map_gva_to_gpa(&mut self, gva: u64, gpa: u64) {
        let gva_page = gva & !0xFFF;
        let gpa_page = gpa & !0xFFF;
        self.guest_mappings.insert(gva_page, gpa_page);
        println!("[Guest MMU] Mapped GVA 0x{gva_page:012x} → GPA 0x{gpa_page:012x}");
    }

    /// Map a GPA page → HPA page (KVM/EPT action)
    pub fn map_gpa_to_hpa(&mut self, gpa: u64, hpa: u64) {
        let gpa_page = gpa & !0xFFF;
        let hpa_page = hpa & !0xFFF;
        self.ept_mappings.insert(gpa_page, hpa_page);
        println!("[EPT]       Mapped GPA 0x{gpa_page:012x} → HPA 0x{hpa_page:012x}");
    }

    /// Translate GVA → HPA (full hardware walk simulation)
    pub fn translate(&self, gva: u64) -> Option<u64> {
        let gva_page = gva & !0xFFF;
        let offset   = gva & 0xFFF;

        // Step 1: Guest page table walk (GVA → GPA)
        let gpa_page = self.guest_mappings.get(&gva_page).copied()?;
        println!("[Walk] GVA 0x{gva:012x} → GPA 0x{:012x} (guest page tables)", gpa_page | offset);

        // Step 2: EPT walk (GPA → HPA)
        let hpa_page = self.ept_mappings.get(&gpa_page).copied()?;
        let hpa = hpa_page | offset;
        println!("[Walk] GPA 0x{:012x} → HPA 0x{hpa:012x} (EPT)", gpa_page | offset);

        Some(hpa)
    }
}

// ─── libc wrappers ───────────────────────────────────────────────────────────

extern "C" {
    fn ioctl(fd: c_int, request: u64, ...) -> c_int;
}

fn libc_ioctl(fd: RawFd, request: u64, arg: usize) -> i32 {
    unsafe { ioctl(fd, request, arg) }
}

// ─── Demo / tests ─────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vaddr_decomposition() {
        let va = Vaddr48::new(0x0000_7FFF_1234_5678);
        println!("{va}");
        assert!(va.is_canonical());
        assert_eq!(va.pgd, (0x0000_7FFF_1234_5678 >> 39) & 0x1FF);

        let non_canonical = Vaddr48::new(0xDEAD_BEEF_1234_5678);
        assert!(!non_canonical.is_canonical());
    }

    #[test]
    fn test_pte_construction() {
        let pte = PageTableEntry::new_page(0x12345, PageTableEntry::WRITABLE | PageTableEntry::USER);
        assert!(pte.is_present());
        assert!(pte.is_writable());
        assert!(pte.is_user());
        assert_eq!(pte.pfn(), 0x12345);
        println!("{pte}");
    }

    #[test]
    fn test_four_layer_translation() {
        let mut model = TranslationModel::new();

        // Guest kernel maps GVA 0x7FFF_1234_5000 → GPA 0x0020_0000
        model.map_gva_to_gpa(0x7FFF_1234_5000, 0x0020_0000);
        // KVM maps GPA 0x0020_0000 → HPA 0x4000_0000
        model.map_gpa_to_hpa(0x0020_0000, 0x4000_0000);

        // Translate with page offset
        let hpa = model.translate(0x7FFF_1234_5ABC);
        assert_eq!(hpa, Some(0x4000_0ABC));
        println!("Final HPA: 0x{:012x}", hpa.unwrap());
    }

    #[test]
    fn test_guest_memory_raii() {
        // Allocate 1 MB of "guest RAM"
        let mut mem = GuestMemory::new(1024 * 1024).expect("alloc failed");

        let data = b"Hello from guest!";
        mem.write_at(0x1000, data).expect("write failed");

        let mut buf = vec![0u8; data.len()];
        mem.read_at(0x1000, &mut buf).expect("read failed");
        assert_eq!(&buf, data);
        // Drop automatically unmaps
    }
}

fn main() {
    println!("=== Virtual Address Decomposition ===");
    for &va in &[
        0x0000_0000_0040_0000u64,   // Typical ELF load address
        0x0000_7FFF_FFFF_8000u64,   // Near top of user space
        0xFFFF_8000_0000_0000u64,   // Kernel direct mapping base
        0xFFFF_FFFF_8000_0000u64,   // Kernel text
    ] {
        println!("{}", Vaddr48::new(va));
    }

    println!("\n=== Four-Layer Translation Demo ===");
    let mut model = TranslationModel::new();
    model.map_gva_to_gpa(0x7FFF_0000_0000, 0x0000_1000_0000);
    model.map_gpa_to_hpa(0x0000_1000_0000, 0x0000_4000_0000);
    if let Some(hpa) = model.translate(0x7FFF_0000_0123) {
        println!("Result: HPA = 0x{hpa:012x}");
    }

    println!("\n=== Page Table Entries ===");
    let entries = [
        PageTableEntry::new_page(0x00001, PageTableEntry::WRITABLE | PageTableEntry::USER),
        PageTableEntry::new_page(0xFEDCB, PageTableEntry::NO_EXECUTE),
        PageTableEntry::new_table(0x00002),
    ];
    for entry in &entries {
        println!("{entry}");
    }
}
```

---

## 21. Performance Analysis and Tuning

### Measuring VM Exit Frequency

```bash
# Use perf to count VM exits per second
perf stat -e 'kvm:kvm_exit' -a sleep 5

# Detailed exit reason breakdown
perf stat -e 'kvm:kvm_exit' \
          -e 'kvm:kvm_entry' \
          -e 'kvm:kvm_mmio' \
          -e 'kvm:kvm_pio' \
          -a sleep 5

# Or use ftrace
echo 'kvm:*' > /sys/kernel/debug/tracing/set_event
cat /sys/kernel/debug/tracing/trace_pipe
```

### Key Performance Metrics

| Metric | Good | Investigate | Unit |
|--------|------|-------------|------|
| VM exits/sec | < 100,000 | > 500,000 | exits/s |
| EPT violations/s | < 10,000 | > 100,000 | /s |
| vCPU steal time | < 5% | > 20% | % |
| Memory bandwidth | > 80% of bare-metal | < 60% | GB/s |
| IPI cost | < 1 μs | > 10 μs | μs |

### CPU Pinning and Isolation

```bash
# Pin vCPU threads to specific host cores
# First, find the QEMU vCPU thread PIDs
ps -eLf | grep qemu

# Pin thread to core 2
taskset -cp 2 <vcpu_thread_pid>

# Or use isolcpus (isolate cores from scheduler)
# Kernel cmdline: isolcpus=2,3,4,5 nohz_full=2,3,4,5 rcu_nocbs=2,3,4,5

# Run QEMU with CPU pinning
qemu-system-x86_64 \
    -smp 4 \
    -vcpu vcpunum=0,affinity=2 \
    -vcpu vcpunum=1,affinity=3 \
    -vcpu vcpunum=2,affinity=4 \
    -vcpu vcpunum=3,affinity=5 \
    ...
```

### Hugepage Tuning for VMs

```bash
# Pre-allocate huge pages (2 MB) for VM workloads
echo 4096 > /proc/sys/vm/nr_hugepages

# Check availability
grep -i huge /proc/meminfo

# Defragment memory if huge pages unavailable
echo 1 > /proc/sys/vm/compact_memory

# For latency-sensitive VMs: pre-allocate 1 GB pages at boot
# /etc/default/grub: GRUB_CMDLINE_LINUX="hugepagesz=1G hugepages=8"
```

### KVM Dirty Page Tracking (for Live Migration)

```bash
# Enable dirty logging on a memory slot
struct kvm_userspace_memory_region region = {
    .flags = KVM_MEM_LOG_DIRTY_PAGES,
    ...
};

# Get dirty bitmap
struct kvm_dirty_log dirty_log = {
    .slot = 0,
    .dirty_bitmap = bitmap_ptr,
};
ioctl(vm_fd, KVM_GET_DIRTY_LOG, &dirty_log);
```

Live migration copies dirty pages iteratively until the "dirty rate" drops below a threshold, then pauses the VM for a final sync.

---

## 22. Security: Spectre, Meltdown, and Side Channels in VMs

### Why VMs Make This Harder

In a single-OS system, Spectre/Meltdown primarily threaten privilege boundaries (kernel vs user). In VMs:
- A malicious guest could use Spectre to leak host kernel data
- A malicious guest could use Meltdown (pre-mitigation) to read host memory via the EPT
- Multiple guests on the same host could spy on each other via shared CPU microarchitecture

### Linux/KVM Mitigations

**Meltdown** (exploits speculative reads of unmapped kernel memory):
- **KPTI** (Kernel Page Table Isolation): Separate page tables for user and kernel mode
- Cost: ~5-30% on I/O-heavy workloads

**Spectre v1** (branch prediction poisoning — bounds check bypass):
- **LFENCE** barriers in kernel code
- **Array index masking**
- **Retpoline** for indirect branches

**Spectre v2** (branch target injection — BTB poisoning across privilege levels):
- **Retpoline**: Replace indirect `jmp`/`call` with `ret`-based trampoline (prevents BTB speculation)
- **IBRS** (Indirect Branch Restricted Speculation): Hardware fence — very expensive on pre-2019 CPUs
- **eIBRS** (Enhanced IBRS): Stays active across privilege changes — cheaper
- **IBPB** (Indirect Branch Predictor Barrier): Flush BTB on VM exit/entry — ~300 cycle cost

**L1TF** (L1 Terminal Fault — Foreshadow):
- Speculative reads of EPT entries can leak L1 cache
- **Mitigation**: Flush L1 cache on VM entry (`l1tf=full` in KVM)
- Or: Disable HyperThreading (siblings share L1)

**MDS** (Microarchitectural Data Sampling — RIDL, Fallout, ZombieLoad):
- Leaks data from CPU internal buffers (fill buffers, load ports, store buffers)
- **VERW** instruction flushes these buffers (inserted on VM exit and context switch)
- Cost: ~10% on some workloads

### Checking Mitigations

```bash
# See all CPU vulnerability status
grep -r . /sys/devices/system/cpu/vulnerabilities/

# Expected output (fully mitigated system):
# /sys/devices/system/cpu/vulnerabilities/spectre_v1: Mitigation: usercopy/swapgs barriers...
# /sys/devices/system/cpu/vulnerabilities/spectre_v2: Mitigation: Enhanced IBRS, IBPB: ...
# /sys/devices/system/cpu/vulnerabilities/meltdown: Mitigation: PTI
# /sys/devices/system/cpu/vulnerabilities/l1tf: Mitigation: PTE Inversion; VMX: ...
# /sys/devices/system/cpu/vulnerabilities/mds: Mitigation: Clear CPU buffers; SMT vulnerable

# KVM-specific mitigation parameters
cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush  # "always" or "cond"
```

### HyperThreading and Security

Two HyperThreads on the same physical core share:
- L1 / L2 cache
- Branch predictor structures
- Load/store buffers

This means a malicious guest vCPU on HT0 can potentially spy on host kernel running on HT1, even with all other mitigations active. For maximum isolation of sensitive VMs:

```bash
# Disable HyperThreading (SMT)
echo off > /sys/devices/system/cpu/smt/control

# Or: use nosmt=force kernel cmdline parameter
# Or: use core scheduling (newer kernel feature — schedules trusted threads only on HT-sibling cores)
echo 1 > /sys/kernel/debug/sched/core_sched  # enable core scheduling
```

---

## Summary: The Complete Mental Model

```
┌─────────────────────────────────────────────────────────┐
│                    GUEST PROCESS                         │
│  GVA 0x7FFF_XXXX_XXXX  (Virtual Address)                │
│  Managed by: guest Linux MMU + guest page tables         │
└─────────────────────┬───────────────────────────────────┘
                      │ Guest page table walk (GVA→GPA)
                      ▼
┌─────────────────────────────────────────────────────────┐
│                GUEST PHYSICAL ADDRESS (GPA)              │
│  0x0000_XXXX_XXXX (Guest's "physical RAM")               │
│  Managed by: guest Linux kernel (buddy, slab, etc.)      │
│  This is what the guest OS thinks is real hardware RAM   │
└─────────────────────┬───────────────────────────────────┘
                      │ EPT/NPT walk (GPA→HPA) — hardware
                      │ KVM maintains EPT, handles EPT faults
                      ▼
┌─────────────────────────────────────────────────────────┐
│                HOST VIRTUAL ADDRESS (HVA)                │
│  QEMU process address space — mmap'd anonymous buffer    │
│  Managed by: QEMU + host Linux VMA system                │
│  Slot mapping: HVA = slot.userspace_addr + (GPA - base) │
└─────────────────────┬───────────────────────────────────┘
                      │ Host page table walk (HVA→HPA)
                      │ Host Linux kernel manages these
                      ▼
┌─────────────────────────────────────────────────────────┐
│              HOST PHYSICAL ADDRESS (HPA)                 │
│  Actual DRAM, managed by host Linux buddy allocator      │
│  struct page tracks each frame                           │
│  Physical DIMM: row/column/bank signals                  │
└─────────────────────────────────────────────────────────┘

vCPU = POSIX thread in QEMU, scheduled by host Linux CFS
     = executes in VMX non-root mode (hardware enforced)
     = state saved in VMCS on every VM exit
     = KVM handles exits, QEMU handles complex ones (MMIO, I/O)
```

### Key Principles to Internalize

1. **Every "physical RAM" access in the guest requires EPT translation** — hardware does this transparently, but TLB misses expose the cost.

2. **QEMU's heap IS the guest's physical RAM** — a massive `mmap(MAP_ANONYMOUS)` allocation. KVM teaches the hardware about this via memory slots + EPT.

3. **vCPU threads are scheduled like any thread** — the guest has no guaranteed CPU time. Steal time (`%st`) measures this cost.

4. **VM exits are the critical path** — minimizing them (via EPT, VPID, paravirt, virtio) is the core challenge of hypervisor performance engineering.

5. **The guest kernel's virtual memory system runs atop a lie** — it manages GVAs and GPAs, never knowing that another address translation layer (EPT) lies beneath.

6. **Security mitigations multiply costs** — KPTI, Retpoline, IBPB, L1D flush, VERW — each VM exit can cost 2,000–10,000 cycles on a fully-mitigated system.

---

*This guide covers the complete virtualization stack from transistors to process virtual memory. Every concept here is directly observable in production systems — `/proc/kvm_stat`, `perf kvm stat`, `/sys/kernel/mm/`, `/proc/self/maps`, and the Linux kernel source (`arch/x86/kvm/`, `virt/kvm/`, `mm/`) are your living laboratory.*

Now let me create this comprehensive guide. This is a deeply technical topic — I'll cover every layer from silicon to process virtual memory.~2,900 lines, ~100 KB — a complete reference. Here's what the guide covers and how to use it as a mental framework:

---

**Your intuition was exactly right** — and here's the precise terminology to crystallize it:

```
Guest process   → GVA  (Guest Virtual Address)   — managed by guest Linux
                      ↓ guest page tables
Guest OS        → GPA  (Guest Physical Address)   — what guest thinks is "physical RAM"
                      ↓ EPT (Extended Page Tables, hardware-level)
QEMU process    → HVA  (Host Virtual Address)     — a massive mmap'd buffer in QEMU's heap
                      ↓ host Linux page tables
Physical DRAM   → HPA  (Host Physical Address)    — actual electrons in DIMM slots
```

The deep insight is this: **QEMU's `mmap(MAP_ANONYMOUS)` allocation IS the guest's "physical RAM"**. KVM registers this mapping via `KVM_SET_USER_MEMORY_REGION`, and the hardware MMU uses EPT to transparently translate GPA → HPA without the guest ever knowing.

**What the guide covers section by section:**
- §1–3: Physical CPU die, DRAM structure, x86 privilege rings, VT-x VMX root/non-root modes
- §4–6: Linux host virtual memory — `mm_struct`, VMAs, 4-level page tables, TLB, KPTI
- §7–8: KVM's `/dev/kvm` ioctl interface, memory slots architecture; QEMU's role as orchestrator
- §9: vCPU deep dive — VMCS structure, all fields, TSC virtualization, vCPU scheduling and steal time
- §10–11: The four-layer GVA→GPA→HVA→HPA model with a traced walk, EPT entry format, EPT violation handling
- §12–13: Guest Linux running inside the VM — double fault path, demand paging at two levels
- §14–17: Balloon driver, KSM, huge pages (2 MB/1 GB), NUMA topology, MMIO emulation, VirtIO, VFIO
- §18: VM exit taxonomy — all 55+ exit reasons, overhead numbers, paravirt hypercalls
- §19–20: **C and Rust implementations** — minimal hypervisor, page table walker, EPT structure, KVM abstraction layer, safe `GuestMemory` RAII, `TranslationModel` demonstrating all four layers
- §21–22: Performance tuning, perf counters, Spectre/Meltdown mitigations and their costs

# Virtual CPU, Physical CPU, RAM, and Virtual RAM: A Complete Systems Guide
## QEMU · KVM · Linux Host (Ubuntu) — From Hardware to Process Memory

> **Summary (8 lines):** When QEMU/KVM runs a VM, three memory-virtualization layers stack on top of each other. The physical host CPU (x86_64 with VMX/AMD-V) exposes *hardware-assisted* virtualization that lets KVM run guest code at near-native speed without emulation. QEMU allocates contiguous regions of *host virtual memory* (via `mmap`) that back the guest's *physical address space* (GPA). KVM programs the CPU's Extended Page Tables (EPT / NPT) so the hardware MMU translates GPA → HPA in a single two-dimensional table walk without VM-exits. Inside the guest, Linux boots and treats that QEMU-allocated memory as raw physical RAM, building its own buddy allocator, slab caches, per-process page tables (GVA → GPA), and swap space — completely unaware of the host layer below. A full address translation therefore involves: *GVA → GPA* (guest page tables in guest CR3) composed with *GPA → HPA* (EPT tables managed by KVM). vCPUs are POSIX threads in the QEMU process, each executing `ioctl(KVM_RUN)` in a tight loop; the host kernel scheduler sees them as ordinary threads and can preempt/migrate them. This document covers every concept in depth with Linux kernel internals, ASCII architecture diagrams, C and Rust implementations, threat models, and rollout guidance.

---

## Table of Contents

1. [Physical Hardware: CPU Virtualization Extensions](#1-physical-hardware-cpu-virtualization-extensions)
2. [Linux Kernel KVM Subsystem](#2-linux-kernel-kvm-subsystem)
3. [QEMU Architecture and vCPU Threading](#3-qemu-architecture-and-vcpu-threading)
4. [Physical RAM: Host Perspective](#4-physical-ram-host-perspective)
5. [QEMU Guest Memory Allocation](#5-qemu-guest-memory-allocation)
6. [KVM Memory Management: kvm_mem_slot and EPT/NPT](#6-kvm-memory-management-kvm_mem_slot-and-eptnpt)
7. [The Three-Level Address Translation Stack](#7-the-three-level-address-translation-stack)
8. [Guest Linux Memory Management](#8-guest-linux-memory-management)
9. [Virtual Memory for Guest Processes (The Hidden Layer)](#9-virtual-memory-for-guest-processes-the-hidden-layer)
10. [Huge Pages, THP, KSM, Ballooning](#10-huge-pages-thp-ksm-ballooning)
11. [vCPU Lifecycle: KVM_RUN Loop and VM-Exits](#11-vcpu-lifecycle-kvm_run-loop-and-vm-exits)
12. [C Implementation: Minimal KVM VM from Scratch](#12-c-implementation-minimal-kvm-vm-from-scratch)
13. [Rust Implementation: KVM-bindings VM](#13-rust-implementation-kvm-bindings-vm)
14. [Linux Kernel Data Structures Reference](#14-linux-kernel-data-structures-reference)
15. [Threat Model and Security Analysis](#15-threat-model-and-security-analysis)
16. [Performance Analysis, Benchmarks, Tuning](#16-performance-analysis-benchmarks-tuning)
17. [Next 3 Steps](#17-next-3-steps)
18. [References](#18-references)

---

## 1. Physical Hardware: CPU Virtualization Extensions

### 1.1 Intel VMX (Virtual Machine Extensions)

Intel VMX, introduced in the Pentium 4 Prescott / Core 2 era (2005-2006), adds two new CPU operating modes:

- **VMX Root Mode** — where the hypervisor (KVM) runs. Full ring 0-3 privilege, but "aware" of virtualization.
- **VMX Non-Root Mode** — where the guest VM runs. Same ring 0-3 privilege, but certain instructions and events cause *VM-exits* that transfer control back to the host.

The central data structure is the **VMCS (Virtual Machine Control Structure)**, a CPU-hardware-maintained 4KB region per vCPU that stores:

```
VMCS Fields (partial):
┌─────────────────────────────────────────────────────┐
│  GUEST STATE AREA                                   │
│    RIP, RSP, RFLAGS, CR0, CR3, CR4                  │
│    Segment selectors (CS, DS, SS, ES, FS, GS)       │
│    GDTR, IDTR, LDTR, TR                             │
│    MSRs: IA32_EFER, IA32_PAT, IA32_SYSENTER_*       │
│                                                     │
│  HOST STATE AREA                                    │
│    RIP (VMEXIT handler addr), RSP, CR0, CR3, CR4    │
│    Segment selectors, GS/FS base                    │
│                                                     │
│  VM-EXECUTION CONTROL FIELDS                        │
│    PIN-BASED: External interrupts, NMI, VMX preempt │
│    PROC-BASED: HLT, MWAIT, CPUID, RDTSC, CR access  │
│    SECONDARY: EPT enable, VPID, UNRESTRICTED GUEST  │
│    EXCEPTION BITMAP: per-exception VM-exit control  │
│                                                     │
│  VM-EXIT CONTROL FIELDS                             │
│    Host address space size (64-bit), MSR store/load │
│                                                     │
│  VM-ENTRY CONTROL FIELDS                            │
│    Guest IA32e mode, load IA32_EFER, MSR load       │
│                                                     │
│  VM-EXIT INFORMATION                                │
│    Exit reason, exit qualification, guest linear    │
│    addr, guest physical addr, IDT vectoring info    │
└─────────────────────────────────────────────────────┘
```

**VMX instruction set additions:**

| Instruction | Privilege | Action |
|-------------|-----------|--------|
| `VMXON`     | Root ring 0 | Enable VMX operation, specify VMXON region |
| `VMXOFF`    | Root ring 0 | Disable VMX operation |
| `VMCLEAR`   | Root ring 0 | Initialize and deactivate a VMCS |
| `VMPTRLD`   | Root ring 0 | Load VMCS pointer into CPU |
| `VMPTRST`   | Root ring 0 | Store current VMCS pointer |
| `VMREAD`    | Root ring 0 | Read a VMCS field |
| `VMWRITE`   | Root ring 0 | Write a VMCS field |
| `VMLAUNCH`  | Root ring 0 | Launch VM (first time) → enters non-root mode |
| `VMRESUME`  | Root ring 0 | Resume VM (subsequent) → re-enters non-root mode |
| `VMEXIT`    | Non-root   | Hardware-triggered; transfers control to host |
| `INVEPT`    | Root ring 0 | Invalidate EPT-based TLB entries |
| `INVVPID`   | Root ring 0 | Invalidate VPID-based TLB entries |

### 1.2 AMD SVM (Secure Virtual Machine / AMD-V)

AMD's equivalent uses **VMCB (Virtual Machine Control Block)** instead of VMCS, and the instructions are:
- `VMRUN` — enter guest (analogous to VMLAUNCH/VMRESUME)
- `VMSAVE`/`VMLOAD` — save/load extended guest state
- `#VMEXIT` — exit event (same concept, different encoding)

AMD uses **NPT (Nested Page Tables)** instead of Intel's EPT — functionally identical.

### 1.3 Extended Page Tables (EPT) / Nested Page Tables (NPT)

Without EPT/NPT, every guest page table walk triggers a VM-exit (shadow paging). EPT eliminates this by adding a second level of hardware page table walking:

```
HARDWARE MMU ADDRESS TRANSLATION WITH EPT:

  Guest code accesses GVA (Guest Virtual Address)
           │
           ▼
  Guest CR3 → Guest PML4 → Guest PDP → Guest PD → Guest PT
  (Each of these is a GPA — Guest Physical Address)
           │
           ▼ (for EACH guest PTE access, hardware also walks EPT)
  EPT PML4 → EPT PDP → EPT PD → EPT PT → HPA (Host Physical Address)
           │
           ▼
  Physical DRAM cell

  Total: up to (4+1) × 4 = 20 memory accesses per TLB miss
  (4 levels of guest PT × 4 EPT walks per level, plus final EPT walk)
  
  With TLB hit (gTLB tagged with VPID): 0 extra memory accesses
```

EPT format (Intel 64-bit, 4-level):

```
EPT PML4E (bit layout):
  [0]     = Read access
  [1]     = Write access
  [2]     = Execute access (supervisor mode)
  [3:5]   = EPT memory type (0=UC, 6=WB) — for leaf entries
  [6]     = Ignore PAT (leaf only)
  [7]     = Large page (1GB for PDP, 2MB for PD)
  [8]     = Accessed flag (requires "EPT accessed and dirty" feature)
  [9]     = Dirty flag
  [10]    = Execute access for user-mode linear addresses
  [11]    = Reserved
  [12:51] = Physical address of next-level EPT table (or final HPA)
  [52:62] = Reserved
  [63]    = Suppress #VE (virtualization exception)
```

### 1.4 CPU Rings and Guest Privilege Levels

In VMX non-root mode, the guest still uses rings 0-3 in the *same* sense:

```
HOST VIEW:                          GUEST VIEW:
┌──────────────────────┐            ┌──────────────────────┐
│  Ring 0 (ROOT)       │            │  Ring 0 (NON-ROOT)   │
│  KVM module          │            │  Guest Linux kernel  │
│  VMCS management     │            │  Handles page faults │
│  EPT management      │            │  Runs SYSCALL        │
│  Handles VM-exits    │            │                      │
├──────────────────────┤            ├──────────────────────┤
│  Ring 3 (ROOT)       │            │  Ring 3 (NON-ROOT)   │
│  QEMU process        │            │  Guest userspace     │
│  vCPU threads        │            │  bash, nginx, etc.   │
│  Memory management   │            │  Guest SYSCALL →     │
│  Device emulation    │            │  Guest kernel        │
└──────────────────────┘            └──────────────────────┘
```

Guest ring 0 is *not* real ring 0 — attempts to execute privileged instructions cause VM-exits handled by KVM (if configured), or are allowed if the guest is running in "unrestricted guest" mode with hardware assistance.

### 1.5 Checking VMX/SVM Support

```bash
# Check Intel VMX
grep -m1 vmx /proc/cpuinfo

# Check AMD SVM
grep -m1 svm /proc/cpuinfo

# Check KVM modules
lsmod | grep kvm

# Full VMX capability flags (Intel)
rdmsr -ax 0x480  # IA32_VMX_BASIC
rdmsr -ax 0x48C  # IA32_VMX_PROCBASED_CTLS
rdmsr -ax 0x48D  # IA32_VMX_EXIT_CTLS

# Check EPT support
rdmsr -ax 0x48B  # IA32_VMX_EPT_VPID_CAP
# Bit 6 = 1 → EPT supported
# Bit 14 = 1 → EPT supports 2MB pages
# Bit 16 = 1 → EPT accessed and dirty flags

# KVM capabilities via /proc
cat /sys/module/kvm_intel/parameters/enable_ept
cat /sys/module/kvm_intel/parameters/enable_vpid
cat /sys/module/kvm_intel/parameters/unrestricted_guest
```

---

## 2. Linux Kernel KVM Subsystem

### 2.1 KVM Architecture in the Kernel

KVM lives in `arch/x86/kvm/` and `virt/kvm/`. It exposes a character device `/dev/kvm` with an `ioctl`-based API.

```
KERNEL KVM SUBSYSTEM (Linux kernel space):

  /dev/kvm (character device, major 10)
       │
       ▼
  kvm_chardev_ioctl()
  ├── KVM_CREATE_VM        → struct kvm
  ├── KVM_GET_API_VERSION  → 12
  ├── KVM_CHECK_EXTENSION  → capability check
  └── KVM_GET_VCPU_MMAP_SIZE → size of kvm_run struct
       │
       ▼ (per-VM fd)
  kvm_vm_ioctl()
  ├── KVM_CREATE_VCPU          → struct kvm_vcpu (one per thread)
  ├── KVM_SET_USER_MEMORY_REGION → maps HVA range to GPA
  ├── KVM_CREATE_IRQCHIP       → in-kernel LAPIC/IOAPIC emulation
  ├── KVM_SET_GSI_ROUTING      → interrupt routing table
  ├── KVM_IRQFD                → eventfd → IRQ injection
  ├── KVM_IOEVENTFD           → eventfd on MMIO/PIO write
  └── KVM_CREATE_PIT2         → in-kernel PIT emulation
       │
       ▼ (per-vCPU fd)
  kvm_vcpu_ioctl()
  ├── KVM_RUN                  → VMLAUNCH / VMRESUME
  ├── KVM_GET/SET_REGS         → general purpose registers
  ├── KVM_GET/SET_SREGS        → segment registers + CR*
  ├── KVM_GET/SET_FPU          → x87/SSE state
  ├── KVM_GET/SET_MSRS         → model-specific registers
  ├── KVM_GET/SET_CPUID2       → guest CPUID leaf values
  ├── KVM_TRANSLATE            → GVA → GPA translation
  └── KVM_SET_SIGNAL_MASK      → signals to unblock during KVM_RUN
```

### 2.2 Core Kernel Data Structures

```c
/* linux/include/linux/kvm_host.h — simplified */

struct kvm {
    struct mm_struct         *mm;               /* host mm (QEMU process) */
    struct kvm_memslots __rcu *memslots[KVM_ADDRESS_SPACE_NUM];
    struct kvm_vcpu          *vcpus[KVM_MAX_VCPUS];
    atomic_t                  online_vcpus;
    struct list_head          vm_list;          /* global VM list */
    struct mutex              lock;
    struct kvm_io_bus __rcu  *buses[KVM_NR_BUSES];
    struct kvm_arch           arch;             /* x86-specific: MTRR, CPUID, APIC... */
    struct kvm_stat           stat;
    struct srcu_struct        srcu;
    struct srcu_struct        irq_srcu;
    /* EPT root: arch.mmu_valid_gen, etc. */
};

struct kvm_vcpu {
    struct kvm               *kvm;
    int                       vcpu_id;
    struct pid               *pid;             /* host thread PID */
    struct mutex              mutex;
    struct kvm_run           *run;             /* shared userspace/kernel page */
    struct kvm_vcpu_arch      arch;            /* x86: vmcs, regs, FPU, APIC... */
    /* Scheduling */
    struct preempt_notifier   preempt_notifier;
    int                       cpu;            /* last pCPU this vCPU ran on */
    /* Stats */
    u64                       stat_exits;
};

struct kvm_memory_slot {
    gfn_t                     base_gfn;         /* guest frame number */
    unsigned long             npages;           /* number of pages */
    unsigned long            *dirty_bitmap;
    struct kvm_arch_memory_slot arch;           /* EPT root, rmap, etc. */
    unsigned long             userspace_addr;   /* HVA: host virtual address */
    u32                       flags;
    short                     id;
    u16                       as_id;
};
```

### 2.3 The `kvm_run` Structure (Shared Page)

The vCPU fd is mmap'd by QEMU. The resulting page is `struct kvm_run` — a shared memory interface between user and kernel space for each vCPU:

```c
/* linux/include/uapi/linux/kvm.h */
struct kvm_run {
    /* IN: set by userspace before KVM_RUN */
    __u8   request_interrupt_window;
    __u8   immediate_exit;
    __u8   padding1[6];

    /* OUT: set by kernel on VM-exit */
    __u32  exit_reason;     /* KVM_EXIT_IO, KVM_EXIT_MMIO, KVM_EXIT_HLT, etc. */
    __u8   ready_for_interrupt_injection;
    __u8   if_flag;
    __u16  flags;

    /* IN/OUT: guest registers (when applicable) */
    __u64  cr8;
    __u64  apic_base;

    union {
        struct { /* KVM_EXIT_IO */
            __u8  direction;   /* KVM_EXIT_IO_IN / KVM_EXIT_IO_OUT */
            __u8  size;        /* 1, 2, 4 bytes */
            __u16 port;
            __u32 count;
            __u64 data_offset; /* offset into this struct for the data */
        } io;

        struct { /* KVM_EXIT_MMIO */
            __u64 phys_addr;
            __u8  data[8];
            __u32 len;
            __u8  is_write;
        } mmio;

        struct { /* KVM_EXIT_HYPERCALL */
            __u64 nr;
            __u64 args[6];
            __u64 ret;
            __u32 longmode;
        } hypercall;

        struct { /* KVM_EXIT_FAIL_ENTRY */
            __u64 hardware_entry_failure_reason;
            __u32 cpu;
        } fail_entry;

        /* ... KVM_EXIT_EXCEPTION, KVM_EXIT_SHUTDOWN, KVM_EXIT_INTERNAL_ERROR ... */
    };

    /* Shared data area follows at offset given by KVM_GET_VCPU_MMAP_SIZE */
};
```

### 2.4 KVM Page Fault Handling and EPT Violation

When the guest accesses a GPA that has no EPT mapping (EPT violation / EPT misconfiguration):

```
GUEST CPU accesses unmapped GPA
         │
         ▼ (hardware)
  EPT violation VM-exit
         │
         ▼ (host kernel, ring 0)
  kvm_vmx_exit_handlers[EXIT_REASON_EPT_VIOLATION]()
         │
         ▼
  kvm_mmu_page_fault(vcpu, gpa, error_code)
         │
         ▼
  kvm_mmu_do_page_fault()
  ├── Lookup kvm_memory_slot for this GPA
  ├── Compute HVA = slot->userspace_addr + (gfn - slot->base_gfn) * PAGE_SIZE
  ├── hva_to_pfn(hva, false, false, &pfn)
  │     └── get_user_pages_fast(hva, 1, FOLL_GET, &page)
  │           └── Host kernel page fault if HVA not backed yet
  │               └── Allocate host physical page (buddy allocator)
  │               └── Map into QEMU's page tables (HVA → HPA)
  └── __direct_map(vcpu, gpa, pfn, level, map_writable)
        └── mmu_set_spte() — write EPT entry: GPA → HPA
              └── KVM_EPT_PAGE_SHIFT, access bits, memory type
```

This is the critical path: **guest page fault → EPT violation → host page fault → buddy allocator → EPT entry written**. After this, subsequent guest accesses to the same GPA are handled entirely in hardware (no VM-exit).

---

## 3. QEMU Architecture and vCPU Threading

### 3.1 QEMU Process Structure

```
QEMU PROCESS (userspace, PID = qemu-system-x86_64):

  Main Thread (IOThread)
  ├── Event loop: aio_poll() / epoll_wait()
  ├── Handles device I/O: disk, network, VirtIO
  ├── QEMU monitor: HMP/QMP protocol
  ├── Memory hotplug, live migration
  └── vCPU coordination (IPI, reset, halt polling)

  vCPU Thread 0 (POSIX thread, SCHED_OTHER or SCHED_RR)
  ├── kvm_cpu_exec() → ioctl(vcpu_fd, KVM_RUN)
  ├── Blocked in kernel during guest execution
  └── Unblocked on VM-exit, handles exit in userspace

  vCPU Thread 1
  └── Same pattern as vCPU Thread 0

  ... (one POSIX thread per vCPU)
```

### 3.2 QEMU vCPU Thread Execution Loop

```c
/* qemu/accel/kvm/kvm-all.c — conceptual reconstruction */

int kvm_cpu_exec(CPUState *cpu) {
    struct kvm_run *run = cpu->kvm_run;   /* mmap'd shared page */
    int ret;

    for (;;) {
        /* 1. Inject pending interrupts, set IRQ window if needed */
        if (cpu->interrupt_request & CPU_INTERRUPT_HARD) {
            if (run->ready_for_interrupt_injection)
                kvm_inject_interrupt(cpu);
            else
                run->request_interrupt_window = 1;
        }

        /* 2. Enter guest — blocks until VM-exit */
        ret = ioctl(cpu->kvm_fd, KVM_RUN, 0);

        /* 3. Handle VM-exit reason */
        switch (run->exit_reason) {
            case KVM_EXIT_IO:
                /* Port I/O: call device model */
                kvm_handle_io(run->io.port, run->io.direction,
                              (void *)run + run->io.data_offset,
                              run->io.size, run->io.count);
                break;

            case KVM_EXIT_MMIO:
                /* MMIO: call device model */
                address_space_rw(&address_space_memory,
                                 run->mmio.phys_addr, MEMTXATTRS_UNSPECIFIED,
                                 run->mmio.data, run->mmio.len,
                                 run->mmio.is_write);
                break;

            case KVM_EXIT_HLT:
                /* Guest executed HLT — idle or halt */
                kvm_handle_halt(cpu);
                break;

            case KVM_EXIT_SHUTDOWN:
                /* Guest triple-faulted or called RESET */
                return EXCP_INTERRUPT;

            case KVM_EXIT_FAIL_ENTRY:
                fprintf(stderr, "KVM: entry failed: 0x%llx\n",
                        run->fail_entry.hardware_entry_failure_reason);
                return -1;

            case KVM_EXIT_INTERNAL_ERROR:
                return -1;

            /* KVM_EXIT_INTR: host signal interrupted KVM_RUN — continue */
            case KVM_EXIT_INTR:
                break;
        }
    }
}
```

### 3.3 QEMU Memory Architecture

QEMU uses a layered `AddressSpace` / `MemoryRegion` / `RAMBlock` hierarchy:

```
QEMU MEMORY OBJECT HIERARCHY:

  AddressSpace "memory"               AddressSpace "I/O"
  (all RAM + MMIO)                    (ISA I/O ports 0–0xFFFF)
       │                                    │
       ▼                                    ▼
  MemoryRegion (root, 2^64 bytes)    MemoryRegion (root, 64KB)
  ├── MemoryRegion "ram-below-4g"    ├── MemoryRegion "piix4-pm"
  │   size = min(ram, 3.5GB)         ├── MemoryRegion "rtc"
  │   type = RAM (backed by mmap)    └── ...
  │   offset = 0x00000000
  ├── MemoryRegion "pci"             
  │   size = 512MB (0xE0000000-0xFFFFF000)
  │   type = I/O memory (not RAM)
  ├── MemoryRegion "ram-above-4g"    
  │   size = max(0, total_ram - 3.5GB)
  │   offset = 0x100000000 (4GB)
  │   type = RAM (backed by mmap)
  └── MemoryRegion "bios"
      size = 256KB
      offset = 0xFFFC0000
      type = ROM

  RAMBlock (backing for RAM MemoryRegions):
  ┌────────────────────────────────────────────┐
  │  host  = mmap(NULL, size, PROT_READ|WRITE, │
  │               MAP_PRIVATE|MAP_ANONYMOUS, -1)│
  │  offset = GPA start                         │
  │  max_length = maximum size (for hotplug)    │
  │  flags = RAM_PREALLOC | RAM_SHARED | etc.   │
  └────────────────────────────────────────────┘
```

Key QEMU source files:
- `exec.c` — `qemu_ram_alloc()`, `RAMBlock` management
- `memory.c` — `MemoryRegion`, `AddressSpace`, `flatview`
- `accel/kvm/kvm-all.c` — KVM backend, `kvm_set_phys_mem()`
- `hw/i386/pc.c` — x86 PC machine init, memory layout

---

## 4. Physical RAM: Host Perspective

### 4.1 NUMA (Non-Uniform Memory Access)

Modern servers have NUMA topology — RAM is physically attached to specific CPU sockets. Accessing remote NUMA node RAM is 1.5–3× slower:

```
DUAL-SOCKET NUMA TOPOLOGY (example):

  Socket 0                         Socket 1
  ├── CPU cores 0-15               ├── CPU cores 16-31
  ├── L1 cache (per core, 32KB)    ├── L1 cache (per core, 32KB)
  ├── L2 cache (per core, 256KB)   ├── L2 cache (per core, 256KB)
  ├── L3 cache (shared, 30MB)      ├── L3 cache (shared, 30MB)
  └── DIMM slots: 192GB            └── DIMM slots: 192GB
       (local, ~80ns latency)           (local, ~80ns latency)
       │                                │
       └────── QPI/UPI link ───────────┘
               (~120ns remote access latency)

  /sys/devices/system/node/node0/meminfo
  /sys/devices/system/node/node1/meminfo
```

```bash
# View NUMA topology
numactl --hardware
lstopo --of ascii    # from hwloc package

# Check NUMA stats
numastat -p $(pgrep qemu)

# Bind QEMU to specific NUMA node (critical for performance)
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# Check THP and NUMA balancing
cat /proc/sys/kernel/numa_balancing
cat /sys/kernel/mm/transparent_hugepage/enabled
```

### 4.2 Linux Physical Memory Management (Host)

The host Linux kernel manages physical RAM with:

```
LINUX PHYSICAL MEMORY ZONES (x86_64):

  Physical Address Space:
  0x0000000000000000 ──────────────────────────────────────────
    Zone: DMA (0 - 16MB)
    Purpose: ISA DMA, legacy devices (BIOS, floppy, etc.)
    Managed by: mem_map[] page descriptors
  0x0000000001000000 ──────────────────────────────────────────
    Zone: DMA32 (16MB - 4GB)
    Purpose: 32-bit PCI DMA, older hardware
  0x0000000100000000 ──────────────────────────────────────────
    Zone: NORMAL (4GB - max physical RAM)
    Purpose: All general allocations, kernel, user pages
    Size: Everything above 4GB

  KERNEL MEMORY AREAS (virtual, x86_64):
  0xffff888000000000  Direct mapping of all physical RAM (physmap)
                      sizeof = total_ram, identity-mapped
  0xffffc90000000000  vmalloc / ioremap area
  0xffffe90000000000  struct page array (mem_map)
  0xffffffff80000000  Kernel text (.text, .data, .bss)
```

**The Buddy Allocator** manages physical pages in power-of-2 sized blocks (orders 0–10, i.e., 1 page to 1024 pages = 4KB to 4MB):

```
BUDDY ALLOCATOR FREE LISTS (per NUMA node, per zone):

  order 0 (4KB):   [page] [page] [page] → free list
  order 1 (8KB):   [page pair] [page pair] → free list
  order 2 (16KB):  [page quad] → free list
  ...
  order 9 (2MB):   [512-page block] → free list
  order 10 (4MB):  [1024-page block] → free list

  Allocation of N pages:
  1. Find smallest order ≥ ceil(log2(N))
  2. If empty, split from next higher order ("buddy split")
  3. Return lower half, put upper half ("buddy") in lower order list

  Deallocation:
  1. Find buddy of freed block (XOR page frame number with block size)
  2. If buddy is also free, coalesce and recurse up
```

```bash
# View buddy allocator state
cat /proc/buddyinfo

# Node 0, zone DMA32:
# Free pages per order:  4K  8K 16K 32K 64K 128K 256K 512K 1M  2M  4M
cat /proc/buddyinfo | grep -i normal

# Page frame number → physical address
# pfn = physical_address / 4096
```

### 4.3 The `page` Struct (struct page)

Every physical 4KB page in the system has a corresponding `struct page` in the kernel:

```c
/* linux/include/linux/mm_types.h — heavily simplified */
struct page {
    unsigned long flags;        /* PG_locked, PG_referenced, PG_uptodate,
                                   PG_dirty, PG_lru, PG_active, PG_slab,
                                   PG_reserved, PG_private, PG_writeback,
                                   PG_head (compound), PG_mlocked, etc. */
    union {
        struct {            /* Page cache / anonymous pages */
            struct list_head lru;
            struct address_space *mapping;
            pgoff_t index;      /* file offset / anon_vma ptr */
            unsigned long private;
        };
        struct {            /* Slab allocator */
            struct kmem_cache *slab_cache;
            void *freelist;
            union { void *s_mem; unsigned long counters; };
        };
        struct {            /* Compound page (HugeTLB) */
            unsigned long compound_head;
            unsigned char compound_dtor;
            unsigned char compound_order;
        };
    };
    atomic_t _refcount;         /* reference count */
    atomic_t _mapcount;         /* number of PTEs that map this page (-1 = unmapped) */
    /* ... more union members for different page uses ... */
} __attribute__((packed));
```

Memory consumption: `sizeof(struct page)` ≈ 64 bytes. For 128GB RAM: 32M pages × 64 bytes = **2GB just for page descriptors**.

---

## 5. QEMU Guest Memory Allocation

### 5.1 How QEMU Allocates Guest RAM

QEMU allocates guest RAM using `mmap()` during machine initialization:

```c
/* Conceptual QEMU RAM allocation path */

/* In qemu/exec.c: qemu_ram_alloc_internal() */
RAMBlock *ram_block_alloc(size_t size, uint32_t flags) {
    RAMBlock *block = g_malloc0(sizeof(RAMBlock));

    if (flags & RAM_SHARED) {
        /* Shared memory: for memory-mapped guest RAM visible to other processes */
        /* e.g., vhost-user, shared memory live migration */
        block->fd = memfd_create("qemu-ram", MFD_CLOEXEC | MFD_ALLOW_SEALING);
        ftruncate(block->fd, size);
        block->host = mmap(NULL, size,
                           PROT_READ | PROT_WRITE,
                           MAP_SHARED, block->fd, 0);
    } else if (flags & RAM_PREALLOC) {
        /* Pre-allocate (touch all pages now) */
        block->host = mmap(NULL, size,
                           PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE, -1, 0);
        /* MAP_POPULATE faults in all pages immediately */
    } else {
        /* Default: demand paging — pages allocated lazily on first access */
        block->host = mmap(NULL, size,
                           PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        /* No MAP_POPULATE — pages are NOT allocated yet!
           Physical pages only appear when KVM causes EPT violations,
           which trigger host page faults, which call get_user_pages() */
    }

    block->max_length = size;
    block->flags = flags;
    return block;
}
```

**Critical insight**: After `mmap(MAP_PRIVATE|MAP_ANONYMOUS)`, the host kernel creates a **VMA (Virtual Memory Area)** entry in the QEMU process's `mm_struct`, but does **NOT** allocate any physical pages. The HVA range is reserved in virtual address space, backed by the zero page or demand-allocated pages.

### 5.2 VMA (Virtual Memory Area) Structure

```c
/* linux/include/linux/mm_types.h */
struct vm_area_struct {
    unsigned long vm_start;        /* HVA start: e.g., 0x7f1234000000 */
    unsigned long vm_end;          /* HVA end:   e.g., 0x7f2234000000 (4GB) */
    struct vm_area_struct *vm_next; /* sorted list of VMAs */
    pgprot_t vm_page_prot;         /* page protection flags */
    unsigned long vm_flags;        /* VM_READ, VM_WRITE, VM_EXEC, VM_SHARED,
                                      VM_DONTCOPY, VM_LOCKED, VM_HUGETLB... */
    struct {                       /* Tree node for fast lookup */
        struct rb_node rb;
    } shared;
    struct anon_vma *anon_vma;     /* anonymous VMA (no file backing) */
    const struct vm_operations_struct *vm_ops;
    unsigned long vm_pgoff;        /* offset into file (0 for anonymous) */
    struct file *vm_file;          /* file backing (NULL for anonymous) */
    struct mm_struct *vm_mm;       /* owning mm_struct */
};
```

### 5.3 QEMU → KVM Memory Registration

After allocating the RAMBlock, QEMU registers the HVA → GPA mapping with KVM:

```c
/* qemu/accel/kvm/kvm-all.c: kvm_set_phys_mem() */
int kvm_set_phys_mem(KVMMemoryListener *kml,
                     MemoryRegionSection *section, bool add) {
    struct kvm_userspace_memory_region mem = {
        .slot            = slot_id,
        .flags           = 0,         /* or KVM_MEM_LOG_DIRTY_PAGES */
        .guest_phys_addr = section->offset_within_address_space,  /* GPA */
        .memory_size     = section->size,
        .userspace_addr  = (uintptr_t)section->mr->ram_block->host
                           + section->offset_within_region,        /* HVA */
    };

    return ioctl(kvm_state->vmfd, KVM_SET_USER_MEMORY_REGION, &mem);
}
```

The kernel handler `kvm_vm_ioctl_set_memory_region()` creates a `kvm_memory_slot`:

```c
/* linux/arch/x86/kvm/x86.c */
int kvm_arch_prepare_memory_region(struct kvm *kvm,
                                    struct kvm_memory_slot *memslot,
                                    const struct kvm_userspace_memory_region *mem,
                                    enum kvm_mr_change change) {
    /* Validate HVA range: must be page-aligned, writable, anonymous or hugetlb */
    /* For each page in range: set up reverse mapping (rmap) for EPT tracking */
    /* Record: memslot->userspace_addr = HVA, memslot->base_gfn = GPA/PAGE_SIZE */
}
```

### 5.4 Memory Slot Layout

```
KVM MEMORY SLOT MAP (example: 4GB VM):

  Slot 0: GPA 0x00000000 → HVA 0x7f0000000000, size=3584MB (below 4GB)
  Slot 1: GPA 0x100000000 → HVA 0x7f1E0000000, size=512MB  (above 4GB)
  Slot 2: GPA 0xFFFE0000 → HVA 0x555ABC000000, size=128KB   (BIOS ROM)

  GPA layout:
  0x00000000  ─── Slot 0 ───────────────────────────────────── 0xDFFFFFFF
  0xE0000000  ─── PCI MMIO (no RAM slot, device registers) ─── 0xFFFEFFFF
  0xFFFF0000  ─── Slot 2 (BIOS) ──────────────────────────── 0xFFFFFFFF
  0x100000000 ─── Slot 1 (high RAM) ───────────────────────── 0x11FFFFFFF
```

---

## 6. KVM Memory Management: kvm_mem_slot and EPT/NPT

### 6.1 EPT Page Table Management

KVM maintains EPT page tables in host kernel memory. The root EPT pointer is loaded into the VMCS field `EPT_POINTER`:

```
EPT PAGE TABLE WALK (4-level, 4KB pages):

  Guest Physical Address (GPA): 48 bits
  ┌───────┬───────┬───────┬───────┬──────────────┐
  │ 47:39 │ 38:30 │ 29:21 │ 20:12 │    11:0      │
  │ PML4  │  PDP  │  PD   │  PT   │  Page offset │
  │ index │ index │ index │ index │  (4096 bytes)│
  │ 9 bits│ 9 bits│ 9 bits│ 9 bits│  12 bits     │
  └───────┴───────┴───────┴───────┴──────────────┘
       │       │       │       │
       │       │       │       └── Index into EPT PT (512 entries × 8 bytes = 4KB page)
       │       │       └────────── Index into EPT PD
       │       └────────────────── Index into EPT PDP
       └────────────────────────── Index into EPT PML4 (root, stored in VMCS)

  For 2MB pages: PD entry has bit 7=1 (Large Page), skip PT level
  For 1GB pages: PDP entry has bit 7=1, skip PD+PT levels

  EPT entry (leaf, 4KB page):
  Bits 0   = Read
  Bits 1   = Write
  Bits 2   = Supervisor Execute
  Bits 3-5 = EPT Memory Type (000=UC, 110=WB)
  Bit  6   = Ignore PAT
  Bit  8   = Accessed
  Bit  9   = Dirty
  Bits 12-51 = Host Physical Frame Number (HPA >> 12)
  Bit  63  = Suppress #VE
```

### 6.2 VPID (Virtual Processor ID)

Without VPID, every VM-entry and VM-exit requires a TLB flush (INVVPID). VPID tags TLB entries per vCPU:

```bash
# Check VPID support
cat /sys/module/kvm_intel/parameters/enable_vpid  # Should be "Y"

# VPID assignment: each vCPU gets a unique 16-bit VPID (1-65535)
# VPID 0 is reserved for host
# KVM assigns: vcpu->arch.vpid = 1, 2, 3, ... per VM
```

### 6.3 Reverse Mapping (rmap)

KVM maintains a reverse map from each physical page (pfn) to all EPT entries pointing to it. This is needed for:
- Dirty page tracking (live migration)
- Memory balloon / hot-unplug
- KSM (Kernel Same-page Merging) deduplication

```
RMAP DATA STRUCTURE:

  pfn 0x1A3F5  →  rmap entry
                  ├── EPT entry in VM-0, slot 0, gfn 0x84320
                  └── (KSM: might point to same pfn from multiple VMs)

  struct kvm_rmap_head {
      unsigned long val;
      /* val & 1 == 0: val is a pointer to kvm_pte_t (single entry) */
      /* val & 1 == 1: val is a pointer to pte_list_desc (multiple entries) */
  };
```

### 6.4 Memory Pressure: madvise and KVM

QEMU can hint to the host kernel about guest memory usage patterns:

```c
/* Guest memory idle → tell host kernel it can reclaim these pages */
madvise(host_va, size, MADV_PAGEOUT);   /* force immediate reclaim */
madvise(host_va, size, MADV_COLD);      /* move to inactive LRU */
madvise(host_va, size, MADV_FREE);      /* pages may be reused */

/* Guest memory accessed frequently → prevent reclaim */
madvise(host_va, size, MADV_WILLNEED);  /* prefetch */
mlock(host_va, size);                   /* pin in RAM, never swapped */

/* KVM dirty page logging for live migration */
ioctl(vmfd, KVM_SET_USER_MEMORY_REGION, &mem_with_KVM_MEM_LOG_DIRTY_PAGES);
ioctl(vmfd, KVM_GET_DIRTY_LOG, &dirty_log);  /* bitmap of modified pages */
```

---

## 7. The Three-Level Address Translation Stack

This is the core of the "hidden thing" you described. Here is the complete picture:

### 7.1 Complete Address Translation Path

```
COMPLETE ADDRESS TRANSLATION (GVA → GPA → HPA):

  Guest Process (e.g., nginx in the VM)
  issues: MOV RAX, [0x00007f1234567890]
          ↑ this is a GVA (Guest Virtual Address)

  LAYER 1: Guest Page Tables (software, maintained by guest Linux kernel)
  ══════════════════════════════════════════════════════════════════════
  Guest CR3 register holds the GPA of the guest PML4 table.

  GVA 0x00007f1234567890 (47-bit canonical)
  ├── PML4 index = bits[47:39] = 0x00F (= 15)
  ├── PDP  index = bits[38:30] = 0x048 (= 72)
  ├── PD   index = bits[29:21] = 0x11A (= 282)
  ├── PT   index = bits[20:12] = 0x067 (= 103)
  └── Page offset = bits[11:0] = 0x890

  Walk:
  Guest CR3 → PML4[15] → PDP[72] → PD[282] → PT[103] → GPA 0x000000A134567000
  + offset 0x890
  = GPA 0x000000A134567890

  BUT: Each PML4[15], PDP[72], etc. is itself a GPA!
  Each step in this walk requires the hardware to also do an EPT walk.

  LAYER 2: EPT (hardware, maintained by KVM/host kernel)
  ══════════════════════════════════════════════════════════════════════
  For EVERY GPA access during the guest PT walk, the hardware MMU
  automatically consults the EPT to translate GPA → HPA.

  GPA 0x000000A134567890 (example, final data page)
  ├── EPT PML4 index = bits[47:39] = 0x000
  ├── EPT PDP  index = bits[38:30] = 0x002
  ├── EPT PD   index = bits[29:21] = 0x08D
  ├── EPT PT   index = bits[20:12] = 0x167
  └── Page offset    = bits[11:0]  = 0x890

  EPT walk: EPT_ROOT → EPT_PML4[0] → EPT_PDP[2] → EPT_PD[141] → EPT_PT[359]
  → HPA 0x00000002B34A7000
  + offset 0x890
  = HPA 0x00000002B34A7890

  LAYER 3: Host CPU Physical Addressing
  ══════════════════════════════════════════════════════════════════════
  HPA 0x00000002B34A7890 → DRAM controller → physical DRAM cell
  at byte address 0x00000002B34A7890

  TOTAL MEMORY ACCESSES (worst case, all TLB-miss, 4-level paging):
  - Guest PT walk: 4 levels × 1 access each = 4 accesses (each is a GPA)
  - EPT walk per guest PT access: 4 levels × 4 accesses = 16 accesses
  - EPT walk for final data: 4 accesses
  - Total: 4 + 16 + 4 = 24 physical memory accesses
  
  With TLB (gTLB for GVA→GPA, TLB for HPA): 1 physical memory access
```

### 7.2 Translation ASCII Diagram

```
  ┌───────────────────────────────────────────────────────────────┐
  │                   GUEST PROCESS (ring 3, non-root)            │
  │                                                               │
  │  GVA: 0x7f1234567890  ──► [Guest CPU issues load instruction] │
  └───────────────────────────────────┬───────────────────────────┘
                                       │ GVA in guest TLB (VPID-tagged)?
                                       │ YES: skip to HPA directly
                                       │ NO: walk guest page tables
                                       ▼
  ┌───────────────────────────────────────────────────────────────┐
  │            GUEST PAGE TABLES (in guest physical memory)       │
  │                                                               │
  │  Guest CR3 (GPA) → PML4[idx] → PDP[idx] → PD[idx] → PT[idx]  │
  │                                                               │
  │  Each table entry is a GPA. Every GPA access goes through EPT │
  │  transparently. Guest kernel doesn't know about this!         │
  └───────────────────────────────────┬───────────────────────────┘
                                       │ Result: GPA
                                       ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                    EPT (Extended Page Tables)                  │
  │              Maintained by KVM (host kernel ring 0)           │
  │                                                               │
  │  EPT ROOT (in VMCS) → EPT_PML4 → EPT_PDP → EPT_PD → EPT_PT   │
  │                                                               │
  │  EPT entry not present?                                       │
  │  → EPT Violation VM-exit                                      │
  │  → kvm_mmu_page_fault() → get_user_pages() → buddy alloc     │
  │  → Write EPT entry: GPA → HPA                                 │
  │  → VMRESUME (no guest visible effect)                         │
  └───────────────────────────────────┬───────────────────────────┘
                                       │ Result: HPA
                                       ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                 HOST PHYSICAL MEMORY (DRAM)                   │
  │                                                               │
  │  HPA → DRAM controller → memory bank → row → column → bit    │
  │                                                               │
  │  This page was originally allocated by:                       │
  │  QEMU mmap() → host kernel page fault → buddy allocator       │
  │  → page frame assigned to QEMU's VMA → mapped into EPT       │
  └───────────────────────────────────────────────────────────────┘
```

### 7.3 The "Hidden Layer" Explained

Your intuition was correct. Here is the exact chain for a process allocating memory in the VM:

```
1. Guest process (e.g., malloc in nginx):
   brk() or mmap() syscall → guest Linux kernel

2. Guest Linux kernel:
   Creates VMA in guest process's mm_struct (GVA range)
   Does NOT allocate guest physical pages yet (demand paging)

3. Guest process writes to new memory:
   GVA not in guest TLB → walk guest page tables
   Guest page table entry (PTE) not present → #PF (page fault)
   Trap to guest Linux kernel (ring 3 → ring 0, NON-ROOT)

4. Guest Linux page fault handler (do_page_fault / do_user_addr_fault):
   alloc_page() → guest Linux buddy allocator
   Gets a "guest physical page" (a GPA / guest frame number)
   Writes the GPA into the guest PTE
   iret back to ring 3

5. Guest process retries the write:
   GVA → PTE lookup → GPA found
   GPA not in EPT (first access) → EPT Violation VM-exit
   kvm_mmu_page_fault() in host kernel ring 0

6. Host kernel page fault via get_user_pages():
   HVA (= QEMU mmap base + GPA offset) → host process page table
   Host PTE not present → host page fault handler
   Host buddy allocator: alloc physical page → HPA
   Writes HPA into QEMU's host PTE (HVA → HPA)

7. KVM writes EPT entry:
   GPA → HPA (EPT PTE updated)
   VMRESUME

8. Guest CPU retries from step 4's iret:
   EPT hit → GPA → HPA in one hardware step
   Data written to physical DRAM

SUMMARY OF LAYERS:
  nginx (GVA)
    │ Guest PTE
  Guest Physical Frame (GPA)
    │ EPT PTE
  QEMU mmap HVA
    │ Host PTE (QEMU process page table)
  Physical DRAM page (HPA)
```

---

## 8. Guest Linux Memory Management

### 8.1 Guest Boot: Memory Detection

When guest Linux boots, it detects available RAM via BIOS/ACPI or E820:

```
BIOS/QEMU provides E820 memory map to guest:
  Type 1 (Usable RAM):    0x00000000 - 0x0009FBFF (639KB)
  Type 2 (Reserved):      0x0009FC00 - 0x0009FFFF (EBDA)
  Type 2 (Reserved):      0x000F0000 - 0x000FFFFF (BIOS)
  Type 1 (Usable RAM):    0x00100000 - 0xBFFFFFFF (3071MB)
  Type 2 (Reserved):      0xC0000000 - 0xFFFFFFFF (PCI MMIO)
  Type 1 (Usable RAM):    0x100000000 - 0x13FFFFFFF (1GB above 4G)

Guest Linux reads this via int 0x15 (E820) in real mode,
then passes it to start_kernel() → setup_memory_map() → memblock_add()
```

### 8.2 memblock: Early Boot Memory Management

Before the buddy allocator is initialized, the kernel uses `memblock`:

```c
/* linux/mm/memblock.c */
struct memblock {
    bool           bottom_up;
    phys_addr_t    current_limit;
    struct memblock_type memory;    /* all RAM regions */
    struct memblock_type reserved;  /* kernel, initrd, page tables */
};

/* Early allocation: */
void *ptr = memblock_alloc(size, PAGE_SIZE);
/* Used for: page tables, mem_map array, kernel data structures */
```

### 8.3 Guest Buddy Allocator

After `mem_init()`, the guest Linux buddy allocator takes over with the *guest physical pages* as its pool. These GPAs are exactly the pages that QEMU allocated via mmap and registered with KVM.

```
GUEST LINUX MEMORY ZONES:

  GPA 0x00000000 - 0x00FFFFFF  → Zone DMA   (16MB)
  GPA 0x01000000 - 0xBFFFFFFF  → Zone DMA32 (3056MB for 4GB VM)
  GPA 0x100000000 - ...        → Zone Normal (above-4GB RAM, if any)

  Guest /proc/buddyinfo shows guest physical page availability.
  This is completely independent of host physical memory state.
  The guest CANNOT see that its "physical pages" are actually
  host virtual addresses in QEMU's address space.
```

### 8.4 Guest Process Virtual Memory (Guest VMA / Guest Page Tables)

Inside the guest, each process gets a 128TB virtual address space (x86_64, 48-bit addressing):

```
GUEST PROCESS VIRTUAL ADDRESS SPACE (48-bit, canonical):

  0x0000000000000000 ─────────────────────────────────────────────
    NULL (unmapped, 64KB guard)
  0x0000000000010000
    Text segment (.text, read+exec)
  0x0000...dynamic
    Data segment (.data, .bss, read+write)
    Heap (grows up from brk)
    ...
  0x00007f0000000000
    mmap region: shared libraries, anonymous mmap, file-backed
    Stack (grows down from 0x7fffffffffff)
  0x00007fffffffffff ── User space top ──────────────────────────
  0xffff800000000000 ── (non-canonical hole) ────────────────────
  0xffff888000000000
    Guest kernel direct mapping (physmap of guest physical RAM)
  0xffffffff80000000
    Guest kernel text (.text, .data, .bss, modules)
  0xffffffffffffffff ── End ──────────────────────────────────────

  Guest kernel virtual address → GPA translation (direct map):
  GVA 0xffff888000000000 + GPA = kernel virtual address
  (Same as host: __va(pfn * PAGE_SIZE) = 0xffff888000000000 + phys)
```

### 8.5 Guest page_fault Handler

```c
/* linux/arch/x86/mm/fault.c — simplified */
void do_user_addr_fault(struct pt_regs *regs, unsigned long hw_error_code,
                         unsigned long address) {
    /* address = faulting GVA */
    struct mm_struct *mm = current->mm;
    struct vm_area_struct *vma;
    
    /* 1. Find VMA covering faulting address */
    vma = find_vma(mm, address);
    if (!vma || vma->vm_start > address)
        goto bad_area;  /* segfault */

    /* 2. Check permissions */
    if (hw_error_code & X86_PF_WRITE && !(vma->vm_flags & VM_WRITE))
        goto bad_area;  /* write to read-only → SIGSEGV */

    /* 3. Handle the fault */
    fault = handle_mm_fault(vma, address, flags, regs);
    /* This allocates a guest physical page from guest buddy allocator,
       writes the guest PTE (GVA → GPA), and returns */
}

vm_fault_t handle_pte_fault(struct vm_fault *vmf) {
    if (!vmf->pte) {
        /* No PTE yet */
        if (vma_is_anonymous(vmf->vma))
            return do_anonymous_page(vmf);  /* anonymous: alloc page, zero it */
        else
            return do_fault(vmf);           /* file-backed: read from file */
    }
    if (!pte_present(*vmf->pte))
        return do_swap_page(vmf);           /* swapped out: read from swap */
    if (vmf->flags & FAULT_FLAG_WRITE && !pte_write(*vmf->pte))
        return do_wp_page(vmf);             /* CoW: copy-on-write */
}
```

### 8.6 Guest Swap

The guest can have swap configured, which adds another indirection:

```
GUEST SWAP PATH:

  Guest process accesses GVA
    └── Guest PTE: present=0, swap_type=X, swap_offset=Y
          └── Guest Linux swap_in from /dev/sdX (virtio-blk)
                └── VirtIO I/O request → QEMU → host disk file
                      └── Reads page into guest physical memory
                            └── Updates guest PTE: GVA → GPA
                                  └── EPT: GPA → HPA (as before)

  Guest cannot swap "below" its physical layer. It only knows about GPAs.
  The host can independently page out the HPA backing that GPA
  (host swaps out the QEMU process page — this is doubly bad for performance).
```

---

## 9. Virtual Memory for Guest Processes (The Hidden Layer)

### 9.1 The Full Stack (Complete Picture)

```
FULL MEMORY VIRTUALIZATION STACK:

  ┌─────────────────────────────────────────────────────────────┐
  │  LAYER 4: GUEST PROCESS VIRTUAL MEMORY                      │
  │                                                             │
  │  nginx/bash/python sees a flat 128TB virtual address space  │
  │  (GVA). Allocated by malloc(), mmap(), brk(). Backed by    │
  │  guest Linux page tables (GVA → GPA).                       │
  │                                                             │
  │  Guest process has no idea it's inside a VM.                │
  │  Its "physical memory" is the guest's view of RAM.          │
  └─────────────────────────┬───────────────────────────────────┘
                             │ Guest page table (GVA → GPA)
  ┌─────────────────────────▼───────────────────────────────────┐
  │  LAYER 3: GUEST PHYSICAL ADDRESS SPACE (GPA)                │
  │                                                             │
  │  Guest Linux treats this as raw physical RAM.               │
  │  Buddy allocator, slab, page cache all use GPAs.            │
  │  Guest /proc/meminfo, /proc/buddyinfo describe GPA pool.    │
  │                                                             │
  │  GPA range: 0x0 → VM_RAM_SIZE (e.g., 0xFFFFF000 for 4GB)   │
  └─────────────────────────┬───────────────────────────────────┘
                             │ EPT (GPA → HPA), managed by KVM
  ┌─────────────────────────▼───────────────────────────────────┐
  │  LAYER 2: HOST VIRTUAL ADDRESS (HVA)                        │
  │                                                             │
  │  QEMU allocated via mmap(MAP_ANONYMOUS). Each GPA is a      │
  │  range in QEMU's virtual address space. Host page tables    │
  │  map HVA → HPA (demand-paged from buddy allocator).         │
  │                                                             │
  │  HVA range: e.g., 0x7f0000000000 → 0x7f0FFFFFFFFF          │
  │  (visible in /proc/<qemu_pid>/maps as anonymous mapping)    │
  └─────────────────────────┬───────────────────────────────────┘
                             │ Host page table (HVA → HPA)
  ┌─────────────────────────▼───────────────────────────────────┐
  │  LAYER 1: HOST PHYSICAL ADDRESS (HPA) / PHYSICAL DRAM       │
  │                                                             │
  │  Real silicon. Managed by host Linux buddy allocator.       │
  │  struct page at pfn = HPA/4096 in host mem_map[].           │
  │  Can be on any NUMA node, any DIMM slot.                    │
  └─────────────────────────────────────────────────────────────┘
```

### 9.2 Verifying the Stack at Runtime

```bash
# === HOST SIDE ===

# Find QEMU process
QEMU_PID=$(pgrep -f "qemu-system-x86_64" | head -1)

# View QEMU virtual address space — find the large anonymous mapping (guest RAM)
cat /proc/$QEMU_PID/maps | grep -v "\.so" | grep "rw-p" | awk '$2~/rw/ {print $1, $5, $6}' | sort -k1 -t '-'

# The large anonymous mmap is guest RAM. Example output:
# 7f0000000000-7f1000000000 rw-p 00000000 00:00 0  (= 4GB anonymous = guest RAM)

# Find the HVA base of guest RAM:
GUEST_RAM_HVA=$(cat /proc/$QEMU_PID/maps | awk '/rw-p.*00:00 0/{
  split($1, a, "-"); size=strtonum("0x"a[2])-strtonum("0x"a[1]);
  if(size > 1073741824) print a[1]}' | head -1)
echo "Guest RAM HVA base: 0x$GUEST_RAM_HVA"

# Show physical pages backing a specific HVA (requires root)
# pagemap: 8 bytes per page, bit 63=present, bits 0-54=pfn
python3 - <<'EOF'
import struct, sys

pid = int(open('/proc/self/status').read().split('Pid:')[1].split()[0])
# Replace with QEMU pid and HVA
hva = 0x7f0000000000  # guest RAM start HVA
page_size = 4096

with open(f'/proc/{pid}/pagemap', 'rb') as f:
    f.seek((hva // page_size) * 8)
    data = f.read(8)
    entry = struct.unpack('<Q', data)[0]
    if entry & (1 << 63):
        pfn = entry & ((1 << 55) - 1)
        print(f"HVA 0x{hva:x} → PFN {pfn} → HPA 0x{pfn * page_size:x}")
    else:
        print("Page not present (not yet faulted in)")
EOF

# View EPT page tables (requires KVM debug)
cat /sys/kernel/debug/kvm/*/vcpu0/ept_root 2>/dev/null || \
    echo "Requires CONFIG_KVM_MMU_AUDIT=y"

# === GUEST SIDE (inside VM) ===
# View guest process virtual memory
cat /proc/self/maps
cat /proc/self/smaps  # detailed stats per VMA

# View guest physical memory state
cat /proc/meminfo
cat /proc/buddyinfo

# Translate guest virtual to guest physical (requires CAP_SYS_ADMIN)
# using /proc/PID/pagemap inside the guest
```

---

## 10. Huge Pages, THP, KSM, Ballooning

### 10.1 Huge Pages and VM Performance

Default 4KB pages require 1 EPT entry per page. For a 4GB VM: 1M EPT entries, and a TLB miss costs 20 memory accesses. Huge pages dramatically reduce TLB pressure:

| Page Size | EPT entries (4GB VM) | TLB miss cost | TLB Coverage per entry |
|-----------|---------------------|---------------|------------------------|
| 4KB       | 1,048,576           | 20 accesses   | 4KB                    |
| 2MB       | 2,048               | 12 accesses   | 2MB                    |
| 1GB       | 4                   | 8 accesses    | 1GB                    |

```bash
# Enable 1GB huge pages on host for QEMU guest RAM
echo 4 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages

# Enable 2MB huge pages
echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Run QEMU with huge pages backing guest RAM
qemu-system-x86_64 \
  -m 4G \
  -mem-path /dev/hugepages \
  -mem-prealloc \
  ...

# Or with 1GB pages:
mkdir -p /mnt/hugepages1g
mount -t hugetlbfs -o pagesize=1G none /mnt/hugepages1g
qemu-system-x86_64 \
  -m 4G \
  -mem-path /mnt/hugepages1g \
  -mem-prealloc \
  ...

# Verify huge page backed mapping (inside host):
cat /proc/$QEMU_PID/smaps | grep -A10 "KernelPageSize"
# Should show: KernelPageSize: 1048576 kB (1GB) or 2048 kB (2MB)
```

### 10.2 Transparent Huge Pages (THP)

THP automatically promotes 4KB anonymous pages to 2MB pages when they're adjacent and aligned:

```bash
# Host THP settings:
cat /sys/kernel/mm/transparent_hugepage/enabled
# Options: always | madvise | never

# For KVM guests: "madvise" + QEMU explicitly calling madvise(MADV_HUGEPAGE)
# is recommended over "always" (avoids compaction stalls)

# QEMU uses madvise(MADV_HUGEPAGE) on guest RAM when:
#   hugepages=on in -machine (QEMU 5.0+)
# Or set manually:
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled

# Check THP promotions:
grep -i huge /proc/$QEMU_PID/smaps | head
# AnonHugePages: 4194304 kB  ← THP-backed guest RAM
```

### 10.3 KSM (Kernel Same-page Merging)

KSM deduplicates identical pages across VMs. Useful when running many identical VMs (same OS):

```
KSM OPERATION:

  Host:
  VM-0: GPA 0x1000 → HPA 0xA1000  (content: zeroed page)
  VM-1: GPA 0x1000 → HPA 0xB2000  (content: zeroed page)
  VM-2: GPA 0x1000 → HPA 0xC3000  (content: zeroed page)

  After KSM:
  VM-0: GPA 0x1000 → HPA 0xA1000  (shared, read-only in EPT)
  VM-1: GPA 0x1000 → HPA 0xA1000  (same HPA)
  VM-2: GPA 0x1000 → HPA 0xA1000  (same HPA)
  → 2 physical pages freed

  On write (copy-on-write):
  VM-1 writes to GPA 0x1000
  → EPT violation (read-only page)
  → KVM allocates new page, copies content, updates EPT
  → EPT: VM-1 GPA 0x1000 → new HPA (no longer shared)
```

```bash
# Enable KSM
echo 1 > /sys/kernel/mm/ksm/run
echo 100 > /sys/kernel/mm/ksm/pages_to_scan  # pages per scan cycle

# QEMU enables KSM on guest RAM with:
madvise(host_va, size, MADV_MERGEABLE);

# View KSM stats:
cat /sys/kernel/mm/ksm/pages_shared      # pages being shared
cat /sys/kernel/mm/ksm/pages_sharing     # references to shared pages
cat /sys/kernel/mm/ksm/pages_unshared    # unique pages scanned
cat /sys/kernel/mm/ksm/pages_volatile    # too volatile to share

# Security note: KSM introduces timing side-channels (see threat model)
```

### 10.4 VirtIO Balloon Driver

The balloon driver allows the host to reclaim guest memory without the guest knowing the exact physical layout:

```
BALLOON OPERATION (inflating = host reclaims memory):

  Host (management) signals QEMU: "inflate balloon by 512MB"
     │
  QEMU sends balloon request via VirtIO PCI virtqueue
     │
  Guest virtio_balloon driver:
  ├── Allocates 131072 pages (512MB) from guest buddy allocator
  ├── Gets the GPAs of these pages
  ├── Sends GPA list to QEMU via virtqueue
  └── Pages are now "owned" by balloon — guest cannot use them
     │
  QEMU receives GPA list from guest
     │
  QEMU calls: madvise(hva_of_gpa, PAGE_SIZE, MADV_PAGEOUT)
     │        or madvise(hva_of_gpa, PAGE_SIZE, MADV_FREE)
     │
  Host kernel reclaims physical pages (HPA) backing those GPAs
     │
  Net effect: 512MB of host physical RAM freed, 
              guest RAM reduced by 512MB (guest knows)
```

```bash
# Set balloon target from host (QEMU QMP):
echo '{"execute": "balloon", "arguments": {"value": 2147483648}}' | \
    nc -U /tmp/qemu.sock  # Reduce guest to 2GB

# In guest, check balloon:
cat /proc/meminfo | grep Balloon

# View balloon stats:
virsh dominfo <vm> | grep Memory
```

### 10.5 Memory Hotplug

```bash
# Add memory to running VM (QEMU QMP):
echo '{"execute":"object-add","arguments":{
  "qom-type":"memory-backend-ram",
  "id":"mem1",
  "size":1073741824}}' | nc -U /tmp/qemu.sock

echo '{"execute":"device_add","arguments":{
  "driver":"pc-dimm",
  "id":"dimm1",
  "memdev":"mem1"}}' | nc -U /tmp/qemu.sock

# In guest Linux (auto-onlines with udev):
cat /sys/devices/system/memory/auto_online_blocks
echo online > /sys/devices/system/memory/memory128/state
```

---

## 11. vCPU Lifecycle: KVM_RUN Loop and VM-Exits

### 11.1 vCPU Thread State Machine

```
VCPU THREAD STATE (host kernel perspective):

  CREATED ──────────────────────► RUNNING (in guest)
    │         ioctl(KVM_RUN)           │
    │                                  │ VM-exit (IO, MMIO, HLT,
    │                                  │  interrupt window, etc.)
    │                           HANDLING EXIT (host ring 0)
    │                                  │
    │                           HANDLING EXIT (QEMU ring 3)
    │         ioctl(KVM_RUN)           │
    └──────────────────────────────────┘

  Host kernel views the vCPU thread as:
  - TASK_RUNNING: executing in kernel (KVM_RUN ioctl, handling exit)
  - TASK_INTERRUPTIBLE: waiting in kvm_vcpu_block() (guest HLT)

  Scheduler can preempt vCPU threads at any time.
  On preemption: vCPU state is saved in VMCS guest area.
  On resume: VMRESUME restores it atomically.
```

### 11.2 VM-Exit Categories and Costs

```
VM-EXIT REASONS AND TYPICAL HANDLING COSTS:

  FAST EXITS (handled in kernel, no userspace):
  ├── External interrupt (host IRQ):   ~500ns   (reschedule, etc.)
  ├── CPUID:                           ~1000ns  (kvm_emulate_cpuid)
  ├── MSR read/write:                  ~500ns   (kvm_msr_*)
  ├── CR0/CR3/CR4 access:              ~500ns   (handle_cr)
  ├── EPT violation (page alloc):      ~5-50μs  (get_user_pages)
  └── EPT violation (TLB shootdown):   ~1-5μs   (tlb invalidation)

  SLOW EXITS (require userspace QEMU):
  ├── I/O port (IN/OUT):               ~2-10μs  (device model)
  ├── MMIO (read/write):               ~2-10μs  (device model)
  ├── HLT (guest idle):                varies   (kvm_vcpu_block)
  └── SHUTDOWN (triple fault):         varies   (VM reset)

  COSTED EXITS (per-VM, check):
  cat /sys/kernel/debug/kvm/vm_count   # total VMs
  cat /sys/kernel/debug/kvm/exits      # per-exit-reason counters
  # Or per-vCPU:
  cat /sys/kernel/debug/kvm/<vm_id>/vcpu0/exit_reasons
```

### 11.3 Interrupt Injection

```
INTERRUPT INJECTION PATH (e.g., virtio-net receives packet):

  Host: TAP/netdev receives packet → eventfd triggered
     │
  QEMU (IOThread): reads eventfd, queues virtqueue notification
     │
  QEMU: sets irq level → kvm_set_irq() → ioctl(vmfd, KVM_IRQ_LINE)
     │
  KVM: kvm_set_irq() → in-kernel IOAPIC → in-kernel LAPIC → vCPU
     │
  KVM: sets VMCS "interrupt_info" field (vector, type, error code)
     │
  On next VMENTRY: CPU delivers virtual interrupt to guest
     │
  Guest: IDT[vector] → guest interrupt handler (e.g., virtio_net)
```

---

## 12. C Implementation: Minimal KVM VM from Scratch

This creates a minimal x86_64 VM that runs a small payload in 16-bit real mode.

```c
/* kvm_minimal.c — Minimal KVM VM in C
 * Compile: gcc -O2 -Wall -o kvm_minimal kvm_minimal.c
 * Run:     sudo ./kvm_minimal
 * Requires: /dev/kvm access (add user to 'kvm' group)
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/kvm.h>
#include <err.h>
#include <errno.h>

/* Guest RAM size: 64MB */
#define GUEST_RAM_SIZE  (64 * 1024 * 1024UL)
/* Guest code loads at physical address 0x1000 (4KB) */
#define GUEST_CODE_GPA  0x1000UL
/* Stack at 0x200000 */
#define GUEST_STACK_GPA 0x200000UL

/*
 * Guest payload: tiny x86 real-mode program
 * Writes 'Hello' to serial port (COM1, 0x3F8) and halts.
 * Assembled bytes (16-bit real mode):
 *
 *   mov si, msg          ; B8 -> actually use SI
 *   .loop:
 *     lodsb              ; AC  — load byte at DS:SI into AL, increment SI
 *     or al, al          ; 08 C0
 *     jz .halt           ; 74 xx
 *     out 0x3f8, al      ; E6 F8  — write to COM1 data register
 *     jmp .loop          ; EB F8
 *   .halt:
 *     hlt                ; F4
 *   msg: db "Hello from KVM!\n", 0
 */
static const uint8_t guest_code[] = {
    /* mov si, offset(msg) — in real mode CS=0, IP=0x1000, so msg at offset 0x10 */
    0xBE, 0x10, 0x10,   /* mov si, 0x1010  (0x1000 + 0x10) */
    /* loop: lodsb */
    0xAC,               /* lodsb */
    0x08, 0xC0,         /* or al, al */
    0x74, 0x04,         /* jz halt (+4 bytes) */
    0xE6, 0xF8,         /* out 0x3f8, al */
    0xEB, 0xF8,         /* jmp loop (-8 from next = back 8) */
    /* hlt */
    0xF4,               /* hlt */
    /* padding to offset 0x10 */
    0x90, 0x90, 0x90,
    /* msg at offset 0x10 from start of code: */
    'H','e','l','l','o',' ','f','r','o','m',' ','K','V','M','!','\n',0
};

/* Set up standard x86 real-mode segment registers */
static void setup_sregs(int vcpu_fd) {
    struct kvm_sregs sregs;
    if (ioctl(vcpu_fd, KVM_GET_SREGS, &sregs) < 0)
        err(1, "KVM_GET_SREGS");

    /* Real mode: CS base=0, limit=0xFFFF, selector=0 */
    #define SEG_INIT(seg, base_, sel_) do { \
        (seg).base = (base_);               \
        (seg).limit = 0xFFFF;               \
        (seg).selector = (sel_);            \
        (seg).present = 1;                  \
        (seg).type = 3;   /* read/write accessed */ \
        (seg).dpl = 0;                      \
        (seg).db = 0;     /* 16-bit */      \
        (seg).s = 1;      /* code/data */   \
        (seg).l = 0;                        \
        (seg).g = 0;                        \
    } while(0)

    SEG_INIT(sregs.cs, 0, 0);
    SEG_INIT(sregs.ds, 0, 0);
    SEG_INIT(sregs.es, 0, 0);
    SEG_INIT(sregs.fs, 0, 0);
    SEG_INIT(sregs.gs, 0, 0);
    SEG_INIT(sregs.ss, 0, 0);

    /* Disable protected mode */
    sregs.cr0 &= ~(1ULL); /* CR0.PE = 0: real mode */

    if (ioctl(vcpu_fd, KVM_SET_SREGS, &sregs) < 0)
        err(1, "KVM_SET_SREGS");
}

/* Handle I/O port exits */
static int handle_io(struct kvm_run *run) {
    if (run->io.direction == KVM_EXIT_IO_OUT &&
        run->io.port == 0x3F8) {
        /* COM1 output: print the byte */
        char *data = (char *)run + run->io.data_offset;
        fwrite(data, 1, run->io.size, stdout);
        fflush(stdout);
        return 1;  /* continue */
    }
    fprintf(stderr, "Unhandled I/O: dir=%d port=0x%x size=%d\n",
            run->io.direction, run->io.port, run->io.size);
    return 0;  /* stop */
}

int main(void) {
    int kvm_fd, vm_fd, vcpu_fd;
    void *guest_ram;
    struct kvm_run *run;
    int mmap_size;

    /* Step 1: Open /dev/kvm */
    kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (kvm_fd < 0) err(1, "open /dev/kvm");

    /* Verify API version */
    int version = ioctl(kvm_fd, KVM_GET_API_VERSION, 0);
    if (version != 12) errx(1, "KVM API version %d != 12", version);

    /* Check EPT support (Intel) or NPT (AMD) */
    if (!ioctl(kvm_fd, KVM_CHECK_EXTENSION, KVM_CAP_USER_MEMORY))
        errx(1, "KVM_CAP_USER_MEMORY not supported");

    printf("KVM API version: %d\n", version);

    /* Step 2: Create VM */
    vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);
    if (vm_fd < 0) err(1, "KVM_CREATE_VM");

    /* Step 3: Allocate guest RAM */
    /* mmap: anonymous, private, no MAP_POPULATE (demand paging) */
    guest_ram = mmap(NULL, GUEST_RAM_SIZE,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                     -1, 0);
    if (guest_ram == MAP_FAILED) err(1, "mmap guest RAM");

    /* Copy guest code to GPA 0x1000 */
    memcpy((uint8_t *)guest_ram + GUEST_CODE_GPA,
           guest_code, sizeof(guest_code));

    /* Step 4: Register guest RAM with KVM (HVA → GPA mapping) */
    struct kvm_userspace_memory_region mem_region = {
        .slot            = 0,
        .flags           = 0,
        .guest_phys_addr = 0,              /* GPA: entire 0..GUEST_RAM_SIZE */
        .memory_size     = GUEST_RAM_SIZE,
        .userspace_addr  = (uint64_t)guest_ram,  /* HVA */
    };
    if (ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &mem_region) < 0)
        err(1, "KVM_SET_USER_MEMORY_REGION");

    printf("Guest RAM: HVA %p → GPA 0x0 (size %lu MB)\n",
           guest_ram, GUEST_RAM_SIZE / (1024*1024));

    /* Step 5: Create vCPU */
    vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);
    if (vcpu_fd < 0) err(1, "KVM_CREATE_VCPU");

    /* mmap kvm_run shared page */
    mmap_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
    if (mmap_size < 0) err(1, "KVM_GET_VCPU_MMAP_SIZE");

    run = mmap(NULL, mmap_size,
               PROT_READ | PROT_WRITE,
               MAP_SHARED, vcpu_fd, 0);
    if (run == MAP_FAILED) err(1, "mmap kvm_run");

    /* Step 6: Set up vCPU registers */
    struct kvm_regs regs = {0};
    regs.rip = GUEST_CODE_GPA;  /* CS:IP = 0:0x1000 (real mode) */
    regs.rsp = GUEST_STACK_GPA; /* stack */
    regs.rflags = 0x0002;       /* reserved bit 1 must be set */
    if (ioctl(vcpu_fd, KVM_SET_REGS, &regs) < 0)
        err(1, "KVM_SET_REGS");

    setup_sregs(vcpu_fd);

    printf("vCPU created: RIP=0x%llx\n", regs.rip);

    /* Step 7: Run the VM */
    printf("--- Guest Output ---\n");
    for (;;) {
        /* Enter guest — blocks until VM-exit */
        if (ioctl(vcpu_fd, KVM_RUN, 0) < 0) {
            if (errno == EINTR) continue;  /* interrupted by signal */
            err(1, "KVM_RUN");
        }

        /* Handle VM-exit */
        switch (run->exit_reason) {
            case KVM_EXIT_IO:
                if (!handle_io(run)) goto done;
                break;

            case KVM_EXIT_HLT:
                printf("\n--- Guest executed HLT, exiting ---\n");
                goto done;

            case KVM_EXIT_MMIO:
                fprintf(stderr, "MMIO at 0x%llx (len=%d, write=%d)\n",
                        run->mmio.phys_addr, run->mmio.len, run->mmio.is_write);
                goto done;

            case KVM_EXIT_SHUTDOWN:
                printf("Guest shutdown\n");
                goto done;

            case KVM_EXIT_FAIL_ENTRY:
                fprintf(stderr, "VM entry failed: reason=0x%llx cpu=%u\n",
                        run->fail_entry.hardware_entry_failure_reason,
                        run->fail_entry.cpu);
                goto done;

            case KVM_EXIT_INTERNAL_ERROR:
                fprintf(stderr, "KVM internal error: suberror=0x%x\n",
                        run->internal.suberror);
                goto done;

            default:
                fprintf(stderr, "Unhandled exit reason: %d\n", run->exit_reason);
                goto done;
        }
    }

done:
    /* Dump final register state */
    if (ioctl(vcpu_fd, KVM_GET_REGS, &regs) == 0) {
        printf("Final RIP: 0x%llx  RAX: 0x%llx  RSI: 0x%llx\n",
               regs.rip, regs.rax, regs.rsi);
    }

    munmap(run, mmap_size);
    munmap(guest_ram, GUEST_RAM_SIZE);
    close(vcpu_fd);
    close(vm_fd);
    close(kvm_fd);
    return 0;
}
```

### 12.2 Extended C Example: 64-bit Long Mode VM

```c
/* kvm_longmode.c — 64-bit VM with EPT, paging, and memory inspection
 * Shows the GVA→GPA→HPA stack explicitly.
 * Compile: gcc -O2 -Wall -o kvm_longmode kvm_longmode.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/kvm.h>
#include <err.h>

/* Memory layout:
 * 0x1000: Page map L4 (PML4) — 1 page
 * 0x2000: Page directory pointer (PDPT) — 1 page
 * 0x3000: Page directory (PD) — 1 page, maps 0..2MB with 2MB huge page
 * 0x4000: Guest code (64-bit long mode)
 * 0x200000: Stack
 */
#define RAM_SIZE     (4 * 1024 * 1024UL)  /* 4MB */
#define PML4_GPA     0x1000
#define PDPT_GPA     0x2000
#define PD_GPA       0x3000
#define CODE_GPA     0x4000
#define STACK_GPA    0x200000

/* GDT for 64-bit mode */
static const uint64_t gdt[] = {
    0,                          /* null descriptor */
    0x00AF9A000000FFFFULL,      /* 64-bit code: present, DPL=0, long mode */
    0x00CF92000000FFFFULL,      /* 64-bit data: present, DPL=0, 32-bit */
};
#define GDT_GPA  0x500
#define GDT_SIZE sizeof(gdt)

/* Guest code: write to port 0xE9 (QEMU debug port) and halt */
static const uint8_t guest64_code[] = {
    /* mov rax, 0x48454C4C4F0A (= "HELLO\n") */
    0x48, 0xB8, 0x48, 0x45, 0x4C, 0x4C, 0x4F, 0x0A, 0x00, 0x00,
    /* Write each byte to port 0xE9 */
    0xB9, 0x06, 0x00, 0x00, 0x00,   /* mov ecx, 6 */
    /* loop: */
    0x66, 0xE7, 0xE9,               /* out 0xE9, ax (low byte) */
    0x48, 0xD3, 0xE8,               /* shr rax, cl... actually ror */
    /* simplified: just write 'H' */
    0xB0, 0x48,                     /* mov al, 'H' */
    0xE6, 0xE9,                     /* out 0xE9, al */
    0xB0, 0x69,                     /* mov al, 'i' */
    0xE6, 0xE9,                     /* out 0xE9, al */
    0xB0, 0x0A,                     /* mov al, '\n' */
    0xE6, 0xE9,                     /* out 0xE9, al */
    0xF4,                           /* hlt */
};

/* Set up identity-mapped page tables for first 2MB (2MB huge page) */
static void setup_paging(uint8_t *ram) {
    uint64_t *pml4 = (uint64_t *)(ram + PML4_GPA);
    uint64_t *pdpt = (uint64_t *)(ram + PDPT_GPA);
    uint64_t *pd   = (uint64_t *)(ram + PD_GPA);

    /* PML4[0] → PDPT at PDP_GPA */
    pml4[0] = PDPT_GPA | 0x3;  /* present + writable */

    /* PDPT[0] → PD at PD_GPA */
    pdpt[0] = PD_GPA | 0x3;    /* present + writable */

    /* PD[0] → 2MB identity map: GPA 0x0 → HPA 0x0 (via EPT) */
    /* Bit 7 = PS (Page Size) = 1 for 2MB huge page */
    pd[0] = 0x0 | 0x83;        /* present + writable + huge (2MB) */
    /* GPA 0x0..0x1FFFFF maps to itself */
}

/* Set up GDT and segment registers for 64-bit mode */
static void setup_long_mode(int vcpu_fd, uint8_t *ram) {
    /* Write GDT into guest RAM */
    memcpy(ram + GDT_GPA, gdt, sizeof(gdt));

    struct kvm_sregs sregs;
    ioctl(vcpu_fd, KVM_GET_SREGS, &sregs);

    /* Set GDTR */
    sregs.gdt.base = GDT_GPA;
    sregs.gdt.limit = sizeof(gdt) - 1;

    /* Code segment: selector 0x08 (index 1, ring 0) */
    sregs.cs.selector = 0x08;
    sregs.cs.base = 0;
    sregs.cs.limit = 0xFFFFFFFF;
    sregs.cs.present = 1;
    sregs.cs.type = 0xA;   /* execute/read */
    sregs.cs.dpl = 0;
    sregs.cs.db = 0;
    sregs.cs.s = 1;
    sregs.cs.l = 1;        /* 64-bit */
    sregs.cs.g = 1;

    /* Data segments: selector 0x10 (index 2, ring 0) */
    #define DS_INIT(seg) do {         \
        (seg).selector = 0x10;        \
        (seg).base = 0;               \
        (seg).limit = 0xFFFFFFFF;     \
        (seg).present = 1;            \
        (seg).type = 0x3;             \
        (seg).dpl = 0;                \
        (seg).db = 1;                 \
        (seg).s = 1;                  \
        (seg).l = 0;                  \
        (seg).g = 1;                  \
    } while(0)
    DS_INIT(sregs.ds); DS_INIT(sregs.ss);
    DS_INIT(sregs.es); DS_INIT(sregs.fs); DS_INIT(sregs.gs);

    /* CR3 = PML4 physical address */
    sregs.cr3 = PML4_GPA;

    /* CR4: enable PAE (required for 64-bit paging) */
    sregs.cr4 = (1 << 5);   /* CR4.PAE = 1 */

    /* CR0: enable protected mode + paging */
    sregs.cr0 = (1 << 0)    /* CR0.PE: protected mode */
              | (1 << 31);   /* CR0.PG: paging */

    /* EFER: enable long mode */
    sregs.efer = (1 << 8)   /* EFER.LME: long mode enable */
               | (1 << 10); /* EFER.LMA: long mode active */

    ioctl(vcpu_fd, KVM_SET_SREGS, &sregs);
}

int main(void) {
    int kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (kvm_fd < 0) err(1, "open /dev/kvm");

    int vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);
    if (vm_fd < 0) err(1, "KVM_CREATE_VM");

    /* Allocate 4MB guest RAM */
    uint8_t *ram = mmap(NULL, RAM_SIZE, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (ram == MAP_FAILED) err(1, "mmap");

    /* Set up page tables */
    setup_paging(ram);

    /* Copy guest code */
    memcpy(ram + CODE_GPA, guest64_code, sizeof(guest64_code));

    /* Register RAM with KVM */
    struct kvm_userspace_memory_region mem = {
        .slot = 0,
        .flags = 0,
        .guest_phys_addr = 0,
        .memory_size = RAM_SIZE,
        .userspace_addr = (uint64_t)ram,
    };
    ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &mem);

    /* Show the address translation mappings */
    printf("=== Address Translation Stack ===\n");
    printf("Guest code GVA: 0x%x (identity mapped)\n", CODE_GPA);
    printf("Guest code GPA: 0x%x (same as GVA via identity PT)\n", CODE_GPA);
    printf("QEMU HVA:       %p (= mmap base + GPA)\n", ram + CODE_GPA);
    printf("HPA:            (not determined until first page fault)\n\n");

    /* Create and configure vCPU */
    int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);
    if (vcpu_fd < 0) err(1, "KVM_CREATE_VCPU");

    int run_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
    struct kvm_run *run = mmap(NULL, run_size, PROT_READ | PROT_WRITE,
                               MAP_SHARED, vcpu_fd, 0);
    if (run == MAP_FAILED) err(1, "mmap kvm_run");

    struct kvm_regs regs = { .rip = CODE_GPA, .rsp = STACK_GPA, .rflags = 2 };
    ioctl(vcpu_fd, KVM_SET_REGS, &regs);

    setup_long_mode(vcpu_fd, ram);

    printf("=== Running 64-bit Guest ===\n");

    int running = 1;
    while (running) {
        ioctl(vcpu_fd, KVM_RUN, 0);
        switch (run->exit_reason) {
            case KVM_EXIT_IO:
                if (run->io.port == 0xE9) {
                    char *data = (char *)run + run->io.data_offset;
                    putchar(*data);
                    fflush(stdout);
                }
                break;
            case KVM_EXIT_HLT:
                printf("\nGuest halted.\n");
                running = 0;
                break;
            default:
                fprintf(stderr, "Unexpected exit: %d\n", run->exit_reason);
                running = 0;
        }
    }

    /* Use KVM_TRANSLATE to demonstrate GVA → GPA */
    struct kvm_translation tr = { .linear_address = CODE_GPA };
    if (ioctl(vcpu_fd, KVM_TRANSLATE, &tr) == 0) {
        printf("\n=== KVM_TRANSLATE (GVA → GPA) ===\n");
        printf("GVA 0x%x → GPA 0x%llx (valid=%d, writeable=%d)\n",
               CODE_GPA, tr.physical_address, tr.valid, tr.writeable);
    }

    return 0;
}
```

---

## 13. Rust Implementation: KVM-bindings VM

```toml
# Cargo.toml
[package]
name = "kvm-demo"
version = "0.1.0"
edition = "2021"

[dependencies]
kvm-bindings = "0.7"
kvm-ioctls = "0.16"
vm-memory = "0.14"
libc = "0.2"
```

```rust
// src/main.rs — KVM VM in Rust using kvm-ioctls + vm-memory
// Demonstrates the full HVA → GPA → KVM registration chain.
//
// cargo build && sudo ./target/debug/kvm-demo

use kvm_bindings::{
    kvm_regs, kvm_sregs, kvm_userspace_memory_region,
    KVM_EXIT_HLT, KVM_EXIT_IO, KVM_EXIT_MMIO, KVM_EXIT_SHUTDOWN,
    KVM_EXIT_FAIL_ENTRY,
};
use kvm_ioctls::{Kvm, VcpuExit};
use std::io::{self, Write};
use vm_memory::{
    GuestAddress, GuestMemory, GuestMemoryMmap, GuestMemoryRegion,
    MmapRegion,
};

/// Guest memory layout constants (GPA = Guest Physical Address)
const GUEST_MEM_SIZE: u64  = 64 * 1024 * 1024;  // 64 MB
const GUEST_CODE_GPA: u64  = 0x1000;
const GUEST_STACK_GPA: u64 = 0x200000;

/// Real-mode x86 guest payload:
/// Writes "Hi!\n" to COM1 (port 0x3F8) then HLTs.
const GUEST_CODE: &[u8] = &[
    // mov si, 0x1010  (address of string in guest memory)
    0xBE, 0x10, 0x10,
    // loop: lodsb
    0xAC,               // lodsb: al = [ds:si], si++
    0x08, 0xC0,         // or al, al
    0x74, 0x04,         // jz halt
    0xE6, 0xF8,         // out 0x3f8, al  (COM1)
    0xEB, 0xF8,         // jmp loop
    // halt:
    0xF4,               // hlt
    0x90, 0x90, 0x90,   // padding to offset 0x10
    // string at offset 0x10:
    b'H', b'i', b'!', b'\n', 0,
];

/// Print memory layout for educational purposes
fn print_translation_info(mem: &GuestMemoryMmap, code_gpa: u64) {
    println!("=== Address Translation Stack ===");
    
    for region in mem.iter() {
        let hva = region.as_ptr();
        let gpa_start = region.start_addr().0;
        let size = region.len();
        println!(
            "  GPA 0x{:016x}..0x{:016x} → HVA {:p}..{:p} ({} MB)",
            gpa_start,
            gpa_start + size,
            hva,
            unsafe { hva.add(size as usize) },
            size / (1024 * 1024)
        );
    }
    
    // Demonstrate the HVA for a specific GPA
    if let Some(hva) = mem.get_host_address(GuestAddress(code_gpa)) {
        println!(
            "\n  Guest code GPA 0x{:x} → HVA {:p}",
            code_gpa, hva
        );
        println!("  (HPA assigned lazily on first EPT violation)");
    }
    println!();
}

/// Set up x86 real-mode segment registers
fn setup_sregs(vcpu: &kvm_ioctls::VcpuFd) -> Result<(), kvm_ioctls::Error> {
    let mut sregs = vcpu.get_sregs()?;

    // Real mode segment setup
    macro_rules! set_seg {
        ($seg:expr) => {
            $seg.base = 0;
            $seg.limit = 0xFFFF;
            $seg.selector = 0;
            $seg.present = 1;
            $seg.type_ = 3;   // read/write/accessed
            $seg.dpl = 0;
            $seg.db = 0;      // 16-bit
            $seg.s = 1;       // data/code
            $seg.l = 0;
            $seg.g = 0;
        };
    }

    set_seg!(sregs.cs);
    set_seg!(sregs.ds);
    set_seg!(sregs.es);
    set_seg!(sregs.fs);
    set_seg!(sregs.gs);
    set_seg!(sregs.ss);

    // Disable protected mode (real mode)
    sregs.cr0 &= !1u64; // CR0.PE = 0

    vcpu.set_sregs(&sregs)?;
    Ok(())
}

/// Handle an I/O port exit — simulate COM1 serial output
fn handle_io_exit(kvm_run: &kvm_bindings::kvm_run) -> bool {
    // Safety: io field valid when exit_reason == KVM_EXIT_IO
    let io = unsafe { kvm_run.__bindgen_anon_1.io };

    if io.direction == kvm_bindings::KVM_EXIT_IO_OUT as u8
        && io.port == 0x3F8
    {
        // The I/O data is at (kvm_run_ptr + io.data_offset)
        let data_ptr = kvm_run as *const _ as *const u8;
        let byte = unsafe { *data_ptr.add(io.data_offset as usize) };
        print!("{}", byte as char);
        io::stdout().flush().ok();
        return true; // continue
    }
    
    eprintln!(
        "Unhandled I/O: dir={} port=0x{:x} size={}",
        io.direction, io.port, io.size
    );
    false
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Step 1: Open /dev/kvm
    let kvm = Kvm::new()?;
    
    let api_version = kvm.get_api_version();
    if api_version != 12 {
        return Err(format!("Unexpected KVM API version: {}", api_version).into());
    }
    println!("KVM API version: {}", api_version);
    
    // Check for required extensions
    if !kvm.check_extension(kvm_ioctls::Cap::UserMemory) {
        return Err("KVM_CAP_USER_MEMORY not supported".into());
    }
    println!("EPT/NPT memory management: supported");

    // Step 2: Create VM
    let vm = kvm.create_vm()?;

    // Step 3: Allocate guest RAM using vm-memory GuestMemoryMmap
    // This performs mmap(MAP_ANONYMOUS|MAP_PRIVATE) for the backing.
    // The GuestMemoryMmap enforces GPA → HVA mappings in a type-safe way.
    let guest_mem = GuestMemoryMmap::from_ranges(&[
        (GuestAddress(0), GUEST_MEM_SIZE as usize),
    ])?;

    // Step 4: Print the address translation info
    print_translation_info(&guest_mem, GUEST_CODE_GPA);

    // Step 5: Write guest code into guest RAM (via HVA)
    guest_mem.write(GUEST_CODE, GuestAddress(GUEST_CODE_GPA))?;

    // Step 6: Register each GuestMemoryMmap region with KVM
    // This calls ioctl(KVM_SET_USER_MEMORY_REGION) for each region.
    for (idx, region) in guest_mem.iter().enumerate() {
        let mem_region = kvm_userspace_memory_region {
            slot: idx as u32,
            flags: 0,
            guest_phys_addr: region.start_addr().0,
            memory_size: region.len(),
            userspace_addr: region.as_ptr() as u64,
        };
        // Safety: memory region is valid and will live for VM lifetime
        unsafe { vm.set_user_memory_region(mem_region)? };
        
        println!(
            "Registered mem slot {}: GPA 0x{:x} → HVA {:p}, size {} MB",
            idx,
            region.start_addr().0,
            region.as_ptr(),
            region.len() / (1024 * 1024)
        );
    }

    // Step 7: Create vCPU
    let vcpu = vm.create_vcpu(0)?;
    
    // mmap size for kvm_run shared page
    let kvm_run_size = kvm.get_vcpu_mmap_size()? as usize;
    println!("\nkvm_run shared page size: {} bytes", kvm_run_size);

    // Step 8: Set general-purpose registers
    let mut regs = vcpu.get_regs()?;
    regs.rip = GUEST_CODE_GPA;
    regs.rsp = GUEST_STACK_GPA;
    regs.rflags = 0x0002;  // reserved bit 1 must be 1
    vcpu.set_regs(&regs)?;

    // Step 9: Set segment registers (real mode)
    setup_sregs(&vcpu)?;

    println!("\n=== Running Guest VM ===");
    println!("Guest output:");

    // Step 10: Run loop
    loop {
        match vcpu.run()? {
            VcpuExit::Io => {
                // kvm_run is accessible via the vcpu's mmap'd page
                // kvm-ioctls handles this through the VcpuFd abstraction
                let run = unsafe { &*vcpu.get_kvm_run() };
                if !handle_io_exit(run) {
                    break;
                }
            }
            VcpuExit::Hlt => {
                println!("\nGuest executed HLT — halted cleanly.");
                break;
            }
            VcpuExit::MmioRead { addr, data } => {
                eprintln!("MMIO read at 0x{:x} (len={})", addr, data.len());
                break;
            }
            VcpuExit::MmioWrite { addr, data } => {
                eprintln!("MMIO write at 0x{:x}: {:?}", addr, data);
                break;
            }
            VcpuExit::Shutdown => {
                println!("Guest shutdown.");
                break;
            }
            VcpuExit::FailEntry {
                hardware_entry_failure_reason,
                cpu,
            } => {
                eprintln!(
                    "VM entry failed: reason=0x{:x} cpu={}",
                    hardware_entry_failure_reason, cpu
                );
                break;
            }
            VcpuExit::InternalError => {
                eprintln!("KVM internal error");
                break;
            }
            exit => {
                eprintln!("Unexpected exit: {:?}", exit);
                break;
            }
        }
    }

    // Dump final state
    let regs = vcpu.get_regs()?;
    println!(
        "\nFinal register state:\n  RIP=0x{:x}  RAX=0x{:x}  RSI=0x{:x}",
        regs.rip, regs.rax, regs.rsi
    );

    Ok(())
}
```

```rust
// src/memory_introspect.rs — Read EPT page walk state
// Shows how to use KVM_TRANSLATE and pagemap to trace the full stack

use kvm_ioctls::VcpuFd;
use kvm_bindings::kvm_translation;
use std::fs::File;
use std::io::Read;

/// Use KVM_TRANSLATE to convert GVA → GPA
pub fn kvm_translate_gva(vcpu: &VcpuFd, gva: u64) -> Option<u64> {
    let mut tr = kvm_translation {
        linear_address: gva,
        ..Default::default()
    };
    if vcpu.translate_gva(&mut tr).is_ok() && tr.valid != 0 {
        Some(tr.physical_address)
    } else {
        None
    }
}

/// Read /proc/self/pagemap to get HPA from HVA
/// Returns PFN (physical frame number) for the given virtual address
pub fn hva_to_pfn(hva: u64) -> Option<u64> {
    let page_size = unsafe { libc::sysconf(libc::_SC_PAGE_SIZE) } as u64;
    let vpn = hva / page_size;
    
    let mut f = File::open("/proc/self/pagemap").ok()?;
    let offset = vpn * 8;
    
    use std::io::Seek;
    f.seek(std::io::SeekFrom::Start(offset)).ok()?;
    
    let mut buf = [0u8; 8];
    f.read_exact(&mut buf).ok()?;
    
    let entry = u64::from_le_bytes(buf);
    
    // Bit 63: page present
    if entry & (1 << 63) != 0 {
        // Bits 0-54: PFN
        Some(entry & ((1 << 55) - 1))
    } else {
        None  // page not yet faulted in (demand paging)
    }
}

/// Print complete address translation for a GVA in the running VM
pub fn print_full_translation(vcpu: &VcpuFd, gva: u64, guest_ram_hva_base: u64) {
    println!("\n=== Full Address Translation for GVA 0x{:x} ===", gva);
    
    // Step 1: GVA → GPA using KVM_TRANSLATE
    match kvm_translate_gva(vcpu, gva) {
        Some(gpa) => {
            println!("  GVA 0x{:016x}", gva);
            println!("  └─(guest page tables)─► GPA 0x{:016x}", gpa);
            
            // Step 2: GPA → HVA (QEMU's mapping)
            let hva = guest_ram_hva_base + gpa;
            println!("  └─(QEMU mmap offset)──► HVA 0x{:016x}", hva);
            
            // Step 3: HVA → HPA using /proc/self/pagemap
            match hva_to_pfn(hva) {
                Some(pfn) => {
                    let page_offset = gva & 0xFFF;
                    let hpa = pfn * 4096 + page_offset;
                    println!("  └─(host page tables)──► HPA 0x{:016x}", hpa);
                    println!("  └─(physical DRAM)──────► PFN {} ({}MB offset)",
                             pfn, pfn * 4 / 1024);
                }
                None => {
                    println!("  └─(host page tables)──► NOT YET MAPPED");
                    println!("     (demand paging: page not yet accessed)");
                }
            }
        }
        None => {
            println!("  GVA 0x{:x} is not mapped (no valid guest PTE)", gva);
        }
    }
}
```

---

## 14. Linux Kernel Data Structures Reference

### 14.1 x86 paging (guest and host)

```c
/* linux/arch/x86/include/asm/pgtable_types.h */

/* Page table entry flags */
#define _PAGE_PRESENT   (_AT(pteval_t, 1) << 0)   /* bit 0: present */
#define _PAGE_RW        (_AT(pteval_t, 1) << 1)   /* bit 1: read/write */
#define _PAGE_USER      (_AT(pteval_t, 1) << 2)   /* bit 2: user/supervisor */
#define _PAGE_PWT       (_AT(pteval_t, 1) << 3)   /* bit 3: write-through */
#define _PAGE_PCD       (_AT(pteval_t, 1) << 4)   /* bit 4: cache disabled */
#define _PAGE_ACCESSED  (_AT(pteval_t, 1) << 5)   /* bit 5: accessed */
#define _PAGE_DIRTY     (_AT(pteval_t, 1) << 6)   /* bit 6: dirty */
#define _PAGE_PSE       (_AT(pteval_t, 1) << 7)   /* bit 7: large page (2MB/1GB) */
#define _PAGE_GLOBAL    (_AT(pteval_t, 1) << 8)   /* bit 8: global */
#define _PAGE_SPECIAL   (_AT(pteval_t, 1) << 9)   /* bit 9: special (software) */
#define _PAGE_NX        (_AT(pteval_t, 1) << 63)  /* bit 63: no-execute */

/* 4-level paging (48-bit addresses):
 *
 * Virtual address decomposition:
 * ┌──────────┬──────┬──────┬──────┬──────┬────────────┐
 * │  63:48   │47:39 │38:30 │29:21 │20:12 │   11:0     │
 * │  (sign)  │ PGD  │ P4D  │ PUD  │ PMD  │  Offset    │
 * │  extend  │ idx  │ idx  │ idx  │ idx  │            │
 * └──────────┴──────┴──────┴──────┴──────┴────────────┘
 *
 * In Linux naming:
 *   pgd_t = PML4 entry   (points to P4D)
 *   p4d_t = PML4E/PDPT   (folded if 4-level)
 *   pud_t = PDPT entry   (points to PMD, or 1GB if PS=1)
 *   pmd_t = PD entry     (points to PT, or 2MB if PS=1)
 *   pte_t = PT entry     (points to 4KB page)
 */
```

### 14.2 mm_struct and Memory Accounting

```c
/* linux/include/linux/mm_types.h */
struct mm_struct {
    struct vm_area_struct *mmap;          /* sorted VMA list */
    struct rb_root mm_rb;                 /* VMA red-black tree */
    unsigned long mmap_base;             /* base of mmap area */
    unsigned long task_size;             /* max user address */
    pgd_t *pgd;                          /* page global directory */
    atomic_t mm_users;                   /* users (threads, etc.) */
    atomic_t mm_count;                   /* references */
    struct rw_semaphore mmap_lock;        /* VMA modification lock */

    unsigned long total_vm;              /* total virtual pages */
    unsigned long locked_vm;             /* mlock'd pages */
    unsigned long pinned_vm;             /* get_user_pages() pinned */
    unsigned long data_vm;               /* VM_WRITE non-shared */
    unsigned long exec_vm;               /* VM_EXEC */
    unsigned long stack_vm;              /* VM_GROWSDOWN */

    unsigned long start_code, end_code;  /* text segment bounds */
    unsigned long start_data, end_data;  /* data segment bounds */
    unsigned long start_brk, brk;        /* heap bounds */
    unsigned long start_stack;           /* stack base */
    unsigned long arg_start, arg_end;    /* cmdline */
    unsigned long env_start, env_end;    /* environment */
};
```

### 14.3 KVM MMU (Shadow / EPT)

```c
/* linux/arch/x86/include/asm/kvm_host.h */
struct kvm_mmu {
    /* Shadow / EPT page tables */
    hpa_t root_hpa;              /* EPT root physical address → VMCS EPT_POINTER */
    gpa_t root_cr3;              /* for shadow paging: tracked guest CR3 */
    int   root_level;            /* 4 for PML4, 3 for PAE, 2 for 32-bit */

    /* Page fault callback */
    int (*page_fault)(struct kvm_vcpu *, gva_t, u32, bool);

    /* GVA → GPA translation */
    gpa_t (*gva_to_gpa)(struct kvm_vcpu *, gva_t, u32, struct x86_exception *);

    /* Sync guest CR3 changes */
    void (*sync_page)(struct kvm_vcpu *, struct kvm_mmu_page *);
    void (*invlpg)(struct kvm_vcpu *, gva_t);
};

/* kvm_mmu_page: host kernel page holding part of EPT hierarchy */
struct kvm_mmu_page {
    struct list_head      link;      /* global mmu_pages list */
    struct hlist_node     hash_link; /* hash by gfn */
    gfn_t                 gfn;      /* guest frame number this SPT covers */
    union kvm_mmu_page_role {
        u32 word;
        struct {
            u8  level:4;     /* EPT level (1=PTE, 2=PD, 3=PDP, 4=PML4) */
            u8  gpte_is_8_bytes:1;
            u8  quadrant:2;
            u8  direct:1;    /* EPT (direct) vs shadow paging */
            u8  access:3;    /* max access (r/w/x) from guest */
            u8  invalid:1;
            u8  efer_lma:1;
            u8  cr4_pae:1;
            u8  cr0_wp:1;
        };
    } role;
    u64  *spt;               /* the actual page table data (64 entries of u64) */
    atomic_t  root_count;   /* reference count */
    bool      unsync;       /* needs re-sync with guest PT */
};
```

---

## 15. Threat Model and Security Analysis

### 15.1 Threat Model: KVM/QEMU Virtualization Stack

```
TRUST BOUNDARIES AND ATTACK SURFACES:

  ┌─── Untrusted ─────────────────────────────────────────────┐
  │  Guest VM / Guest OS / Guest Applications                  │
  │  • Can issue any instruction in non-root mode             │
  │  • Can access all guest physical memory (GPA)             │
  │  • Cannot directly access host memory                     │
  └────────────────────────────┬──────────────────────────────┘
                                │ VM-exits (controlled by KVM)
  ┌─── Semi-trusted ───────────▼──────────────────────────────┐
  │  QEMU Process (host ring 3)                                │
  │  • Handles I/O exits, device emulation                    │
  │  • Large C codebase (~4M lines), significant attack surface│
  │  • Compromise = host ring 3 access                        │
  └────────────────────────────┬──────────────────────────────┘
                                │ syscalls, ioctls
  ┌─── Trusted ────────────────▼──────────────────────────────┐
  │  Host Linux Kernel + KVM Module                            │
  │  • Manages EPT, VMCS                                      │
  │  • Enforces memory isolation                              │
  └────────────────────────────┬──────────────────────────────┘
                                │ HW privileges
  ┌─── Hardware ───────────────▼──────────────────────────────┐
  │  CPU (VMX/AMD-V) + DRAM + IOMMU                           │
  └────────────────────────────────────────────────────────────┘
```

### 15.2 Known Attack Vectors and Mitigations

**VM Escape via QEMU Device Emulation:**
- CVE-2015-3456 (VENOM): floppy controller buffer overflow in QEMU
- CVE-2019-14378: SLiRP heap overflow
- CVE-2021-3527: USB redirect heap overflow
- Mitigation: seccomp-bpf on QEMU, SELinux/AppArmor, minimal device set, virtio-only

**EPT Misconfiguration (Guest → Host Memory Access):**
- Theoretical: guest manipulates GPA to alias host kernel pages via misconfigured EPT
- KVM defense: EPT entries only cover registered `kvm_memory_slots`
- GPA outside registered slots → VM-exit with #EPT_MISCONFIG → QEMU terminates

**Spectre/Meltdown and CPU Side-Channels:**
- Meltdown: guest kernel could read host memory via speculative execution (mitigated by KPTI)
- Spectre v2: BTB-based cross-VM attacks → Retpoline, IBRS, eIBRS in host kernel
- L1TF (CVE-2018-3646): L1 data cache side-channel across VMs → L1D flush on VMEXIT, core scheduling
- MDS (RIDL/Fallout, CVE-2018-12130 etc.): microarchitectural data sampling
  - `echo 1 > /sys/kernel/debug/x86/cpu_mds_mitigations` — VERW on VM-exit

```bash
# Check all CPU vulnerability mitigations
grep . /sys/devices/system/cpu/vulnerabilities/*

# Enable full mitigations (performance cost: 10-30%):
# kernel boot params:
# mitigations=auto,nosmt    ← disable SMT (HyperThreading) for L1TF
# pti=on                    ← Kernel Page Table Isolation (Meltdown)
# kpti=1
# ibrs=1                    ← Indirect Branch Restricted Speculation
# l1tf=full,force           ← L1 Terminal Fault mitigation

# For KVM workloads, add to QEMU:
# -cpu host,+spec-ctrl,+ssbd,+md-clear,+pcid
```

**KSM Timing Side-Channel:**
- KSM merges identical pages between VMs
- Attack: measure time to write to a page; if it's fast (no CoW) → not shared
- If slow (CoW allocation needed) → shared with another VM → infer victim's data
- Mitigation: disable KSM for security-sensitive workloads:
  `echo 2 > /sys/kernel/mm/ksm/run  # KSM_RUN_MERGE=2 → disable`

**Rowhammer (Memory DRAM Attack):**
- Guest repeatedly hammers adjacent DRAM rows → flips bits in host pages
- ECC DRAM mitigates (corrects single-bit, detects double-bit)
- Mitigation: DDRMC refresh rate increase, TRR (Target Row Refresh), pTRR

**Guest-to-Guest via Shared Memory:**
- Virtio-shared-memory or IVSHMEM between VMs
- Ensure proper IOMMU isolation if hardware sharing is needed

### 15.3 Security Hardening Checklist

```bash
# 1. QEMU seccomp-bpf filter (requires QEMU 2.5+)
qemu-system-x86_64 -sandbox on,obsolete=deny,elevateprivileges=deny,...

# 2. SELinux / AppArmor confinement
aa-status | grep qemu
# /etc/apparmor.d/usr.bin.qemu-system-x86_64

# 3. Run QEMU as non-root, dedicated user
useradd -r -s /sbin/nologin qemu-vm
chown qemu-vm:qemu-vm /var/lib/qemu/

# 4. IOMMU for PCI passthrough isolation (prevents DMA attacks)
# Kernel boot: intel_iommu=on,sm_on  or  amd_iommu=on
dmesg | grep -i iommu
cat /sys/kernel/iommu_groups/*/devices

# 5. Disable unnecessary QEMU devices (reduce attack surface)
qemu-system-x86_64 \
  -nodefaults \
  -device virtio-net-pci,netdev=net0 \
  -device virtio-blk-pci,drive=hd0 \
  -device virtio-serial-pci \
  # NO: -device floppy, -device sb16, -device ac97, -device usb-*

# 6. Memory encryption (AMD SEV / Intel TDX)
# AMD SEV: encrypts VM memory with per-VM key, host cannot read
# AMD SEV-SNP: adds integrity protection, VM attestation
qemu-system-x86_64 \
  -object sev-guest,id=sev0,policy=0x1 \
  -machine ...,memory-encryption=sev0

# 7. Kernel lockdown for KVM host
echo integrity > /sys/kernel/security/lockdown

# 8. Limit VCPU CPU affinity (prevent cross-core L1TF)
taskset -cp 0,2,4,6 $(pgrep -f "qemu.*vm0")  # pin to physical cores only
```

---

## 16. Performance Analysis, Benchmarks, Tuning

### 16.1 Key Performance Metrics

```bash
# VM-exit rates (high rate = performance problem)
perf stat -e 'kvm:kvm_exit,kvm:kvm_entry' -p $(pgrep qemu) sleep 5

# Per-exit-reason breakdown
cat /sys/kernel/debug/kvm/exits
# HALT exits: high → guest idle (OK)
# IO exits:   high → PIO I/O heavy workload (consider virtio + ioeventfd)
# EPT_MISCONFIG: non-zero → misconfigured MMIO (investigate)

# EPT violation rate (page fault overhead)
cat /sys/kernel/debug/kvm/ept_violations

# TLB shootdown overhead
perf stat -e 'tlb:tlb_flush' -p $(pgrep qemu) sleep 5

# NUMA misses
numastat -p $(pgrep qemu) -s

# Cache misses
perf stat -e 'cache-misses,cache-references,L1-dcache-load-misses' \
    -p $(pgrep qemu) sleep 5
```

### 16.2 Memory Performance Tuning

```bash
# 1. Use huge pages (critical: 10-30% perf improvement)
echo 4 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
# Run QEMU with: -mem-path /dev/hugepages -mem-prealloc

# 2. NUMA pinning (critical for multi-socket hosts)
numactl --cpunodebind=0 --membind=0 \
    qemu-system-x86_64 -m 32G -smp 8 ...

# 3. CPU pinning (reduce vCPU migration overhead)
# vcpu_id → host_cpu_id mapping:
virsh vcpupin <domain> 0 0
virsh vcpupin <domain> 1 2
# (use physical cores, avoid HT siblings for security)

# 4. Disable THP compaction (reduces latency spikes)
echo defer+madvise > /sys/kernel/mm/transparent_hugepage/defrag

# 5. Halt polling (avoid HLT exit overhead)
# KVM busy-polls instead of blocking on HLT
cat /sys/module/kvm/parameters/halt_poll_ns
echo 400000 > /sys/module/kvm/parameters/halt_poll_ns

# 6. Enable nested virtualization (for dev/test)
modprobe kvm_intel nested=1
# or: options kvm_intel nested=1 in /etc/modprobe.d/kvm.conf

# 7. MSR filtering (reduce MSR exit overhead, Linux 5.10+)
# kvm.enable_vmware_backdoor=N
# kvm_intel.enable_pml=Y  (Page Modification Logging, reduces dirty tracking cost)
```

### 16.3 Memory Allocation Timing Benchmark

```c
/* bench_page_alloc.c — measure first-access page fault cost in guest */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>

#define BENCH_SIZE (256 * 1024 * 1024UL)  /* 256 MB */
#define PAGE_SIZE  4096

static long ns_diff(struct timespec *a, struct timespec *b) {
    return (b->tv_sec - a->tv_sec) * 1000000000L + (b->tv_nsec - a->tv_nsec);
}

int main(void) {
    struct timespec t0, t1, t2, t3;
    
    /* Allocate without touching (demand paging) */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    char *mem = mmap(NULL, BENCH_SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    
    /* First touch (triggers page faults → EPT violations) */
    clock_gettime(CLOCK_MONOTONIC, &t2);
    for (size_t i = 0; i < BENCH_SIZE; i += PAGE_SIZE)
        mem[i] = 0xAB;
    clock_gettime(CLOCK_MONOTONIC, &t3);
    
    size_t npages = BENCH_SIZE / PAGE_SIZE;
    printf("mmap (no pages):     %8ld ns\n", ns_diff(&t0, &t1));
    printf("First touch (%zu MB): %8ld ns  (%ld ns/page = %ld μs/page)\n",
           BENCH_SIZE / (1024*1024),
           ns_diff(&t2, &t3),
           ns_diff(&t2, &t3) / (long)npages,
           ns_diff(&t2, &t3) / (long)npages / 1000);
    
    /* Second touch (all pages mapped, no faults) */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (size_t i = 0; i < BENCH_SIZE; i += PAGE_SIZE)
        mem[i] = 0xCD;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("Second touch:        %8ld ns  (%ld ns/page)\n",
           ns_diff(&t0, &t1),
           ns_diff(&t0, &t1) / (long)npages);
    
    munmap(mem, BENCH_SIZE);
    return 0;
}
```

---

## 17. Next 3 Steps

1. **Build and run the C KVM minimal example** — compile `kvm_minimal.c` and `kvm_longmode.c` on a KVM-capable host, add `strace` and `perf kvm stat` to observe EPT violations, VM-exits, and page fault rates in real time. Instrument the loop with RDTSC to measure KVM_RUN latency per exit type.

2. **Trace the full address translation stack live** — use `virsh qemu-monitor-command --hmp 'gpa2hva <gpa>'` + the Rust `hva_to_pfn` code to trace a specific GPA through all four layers (GVA → GPA → HVA → HPA). Compare results with and without huge pages to see the TLB entry count difference in `/proc/$QEMU_PID/smaps`.

3. **Benchmark memory subsystem configurations** — run the `bench_page_alloc.c` binary inside a VM across four configurations: (a) default demand paging, (b) MAP_POPULATE pre-allocation, (c) 2MB huge pages, (d) 1GB huge pages with NUMA pinning. Measure EPT violation rate (`perf kvm stat`), page fault latency, and workload throughput (e.g., STREAM benchmark). This gives you a concrete, quantified feel for each layer's cost.

---

## 18. References

| Topic | Source |
|-------|--------|
| Intel VMX | Intel SDM Vol. 3C, Chapters 23–34 (intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) |
| AMD SVM | AMD64 APM Vol. 2, Chapter 15 (AMD-V) |
| KVM API | `linux/Documentation/virt/kvm/api.rst` in kernel source |
| KVM source | `linux/arch/x86/kvm/`, `linux/virt/kvm/` |
| QEMU memory | `qemu/docs/devel/memory.rst`, `qemu/exec.c`, `qemu/memory.c` |
| EPT/NPT internals | lwn.net/Articles/612705/ — "KVM: the Linux Virtual Machine Monitor" |
| Linux VM | `linux/mm/memory.c`, `linux/arch/x86/mm/fault.c` |
| Page tables | `linux/Documentation/x86/x86_64/mm.rst` |
| kvm-ioctls (Rust) | github.com/rust-vmm/kvm-ioctls |
| vm-memory (Rust) | github.com/rust-vmm/vm-memory |
| EPT side-channels | L1TF: software.intel.com/security-software-guidance/api-app/sites/default/files/336983-Intel-Analysis-of-L1-Terminal-Fault.pdf |
| KSM | `linux/Documentation/admin-guide/mm/ksm.rst` |
| Huge pages | `linux/Documentation/admin-guide/mm/hugetlbpage.rst` |
| VirtIO balloon | virtio-spec.lustre.org (OASIS VirtIO spec, section 5.5) |
| IOMMU / VFIO | `linux/Documentation/driver-api/vfio.rst` |
| AMD SEV | developer.amd.com/sev |
| Intel TDX | intel.com/content/www/us/en/developer/articles/technical/intel-trust-domain-extensions.html |
| Cloud Hypervisor | github.com/cloud-hypervisor/cloud-hypervisor (Rust, clean KVM impl) |
| rust-vmm | github.com/rust-vmm — reference Rust VMM components |

---

*Document version: 1.0 — covers Linux 6.x, QEMU 8.x, Rust Edition 2021, x86_64 (Intel VMX + AMD-V)*

This is going to be a large, deeply technical document. Let me build it comprehensively covering every layer from hardware to process virtual memory.**~2,750 lines / 105KB** — here's what the document covers, organized top-down:

---

**Your intuition was exactly right.** The stack is:

```
Guest process GVA
   └─[guest page tables]─► GPA (guest thinks this is "physical RAM")
         └─[EPT, managed by KVM]─► HVA (QEMU's mmap'd anonymous region)
               └─[host page tables]─► HPA (actual DRAM cell)
```

The "hidden thing" is that *two independent demand-paging systems stack on top of each other*: the guest Linux buddy allocator + guest page faults (GVA→GPA layer) sit entirely on top of KVM's EPT (GPA→HPA layer), and neither side knows what the other is doing. A guest `malloc()` triggers a guest page fault which allocates a GPA, and only when the guest writes to that GPA does the EPT violation fire, which then triggers a **host** page fault inside `get_user_pages()`, which finally hits the host buddy allocator to produce a physical frame.

---

**What's in the document:**

- **§1** — Intel VMX + AMD SVM deep dive: VMCS structure, VMX instruction set, EPT entry bit layout, VPID, ring model in non-root mode
- **§2** — KVM kernel subsystem: full ioctl API tree, `kvm_run` structure, EPT violation → `kvm_mmu_page_fault()` → `get_user_pages()` → buddy allocator path
- **§3** — QEMU process architecture: vCPU thread model, `kvm_cpu_exec()` loop, `AddressSpace`/`MemoryRegion`/`RAMBlock` hierarchy
- **§4** — Host physical RAM: NUMA topology, Linux zones, buddy allocator free-list mechanics, `struct page` (64 bytes × every physical page)
- **§5** — QEMU guest RAM allocation: `mmap(MAP_ANONYMOUS)` → VMA creation, `struct vm_area_struct`, KVM memory slot registration
- **§6** — EPT page table structure: 4-level walk diagram, entry bit layout, rmap (reverse mapping), `madvise` integration
- **§7** — **The full 3-layer translation stack** with ASCII walk diagram showing all 24 potential memory accesses on a TLB miss, plus the complete demand-paging chain from `malloc()` to physical DRAM
- **§8** — Guest Linux memory: E820 map, memblock, guest buddy allocator, guest page fault handler (`do_user_addr_fault` → `handle_mm_fault`)
- **§9** — Guest process virtual memory: 128TB address space layout, the complete 4-layer chain with verification commands (`pagemap`, `KVM_TRANSLATE`)
- **§10** — Huge pages (2MB/1GB), THP, KSM with timing side-channel analysis, virtio balloon driver mechanics, memory hotplug
- **§11** — vCPU lifecycle, VM-exit categories with cost table (~500ns fast exits vs ~10μs MMIO), interrupt injection path
- **§12** — Full C implementation: 16-bit real-mode KVM VM + 64-bit long-mode VM with identity-mapped EPT paging, `kvm_translation` usage
- **§13** — Full Rust implementation using `kvm-ioctls` + `vm-memory`, including `hva_to_pfn()` via `/proc/self/pagemap` to trace the complete stack
- **§14** — Kernel data structure reference: `struct page`, `mm_struct`, `kvm_mmu`, `kvm_mmu_page`
- **§15** — Threat model: VM escape (VENOM, SLiRP), L1TF, Spectre v2, KSM timing side-channel, Rowhammer, SEV/TDX, IOMMU, seccomp-bpf hardening
- **§16** — Perf tuning: `perf kvm stat`, NUMA pinning, halt polling, huge pages benchmarks, `bench_page_alloc.c`