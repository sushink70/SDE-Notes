# Data Structures, Algorithms & CS Concepts in Linux
## A Complete, In-Depth Reference for Systems Programmers

> *"The kernel is not magic — it is the most disciplined application of computer science ever written."*

---

## Table of Contents

1. [Linux Kernel Architecture — The Grand Picture](#1-linux-kernel-architecture)
2. [Memory Management — From Silicon to Virtual Address](#2-memory-management)
3. [Process & Thread Management](#3-process--thread-management)
4. [CPU Scheduling Algorithms](#4-cpu-scheduling-algorithms)
5. [Data Structures Inside the Linux Kernel](#5-data-structures-inside-the-linux-kernel)
6. [Algorithms Inside the Linux Kernel](#6-algorithms-inside-the-linux-kernel)
7. [File Systems & VFS Layer](#7-file-systems--vfs-layer)
8. [Networking Stack — Data Structures & Algorithms](#8-networking-stack)
9. [Synchronization & Concurrency Primitives](#9-synchronization--concurrency-primitives)
10. [I/O Subsystem & Block Layer](#10-io-subsystem--block-layer)
11. [System Calls — The Interface Layer](#11-system-calls)
12. [Interrupt Handling & Softirqs](#12-interrupt-handling--softirqs)
13. [Device Drivers & Kernel Modules](#13-device-drivers--kernel-modules)
14. [Security Subsystems & LSM](#14-security-subsystems--lsm)
15. [Advanced Kernel Algorithms — Deep Dives](#15-advanced-kernel-algorithms)
16. [Performance Engineering & Profiling](#16-performance-engineering--profiling)

---

# 1. Linux Kernel Architecture

## 1.1 The Monolithic Kernel Philosophy

The Linux kernel is a **monolithic kernel** — all core OS services run in a single address space with ring 0 (supervisor) privilege. This contrasts with microkernels (Mach, L4) where services run in userspace.

**Why monolithic?**
- No inter-process communication overhead for system calls
- Direct function calls between subsystems (no message passing)
- Shared memory structures (no copying between address spaces)
- The performance cost of microkernel IPC was measured at 2-3x overhead in early benchmarks

**The trade-off:** A bug in any kernel subsystem can corrupt the entire system. Microkernels isolate faults. Linux compensates with:
- Memory protection (even within kernel, SMAP/SMEP)
- Kernel Address Space Layout Randomization (KASLR)
- Control Flow Integrity (CFI)
- Kernel lockdown mode

## 1.2 Kernel Address Space Layout

```
Virtual Address Space (64-bit x86_64):
┌─────────────────────────────────┐  0xFFFFFFFFFFFFFFFF
│   Kernel Direct Map             │  (physmap: direct mapping of all RAM)
│   0xFFFF888000000000            │
├─────────────────────────────────┤
│   vmalloc / ioremap area        │  (virtually contiguous, not physically)
│   0xFFFFC90000000000            │
├─────────────────────────────────┤
│   Kernel text, data, BSS        │
│   0xFFFFFFFF80000000            │
├─────────────────────────────────┤  0x00007FFFFFFFFFFF
│   User Space (128 TB)           │
│   Stack (grows down)            │
│   ...                           │
│   mmap region                   │
│   ...                           │
│   Heap (grows up)               │
│   BSS                           │
│   Data                          │
│   Text (code)                   │
└─────────────────────────────────┘  0x0000000000000000
```

The 48-bit virtual address space (AMD64) gives 256 TB total — 128 TB user, 128 TB kernel. With 5-level paging (LA57), this extends to 57-bit: 128 PB total.

**The Canonical Hole:** Addresses between `0x00007FFFFFFFFFFF` and `0xFFFF800000000000` are non-canonical — the CPU will fault on access. This is the hardware-enforced separation between user and kernel.

## 1.3 Kernel Subsystem Interaction Map

```
User Space Programs
        │
        │ syscall / int 0x80
        ▼
┌───────────────────────────────────────────────────────┐
│                   System Call Layer                    │
│  (syscall table, argument validation, copy_from_user) │
└────────┬──────────────┬──────────────┬────────────────┘
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ VFS/FS   │  │ Network  │  │ Process Mgmt │
   │ Layer    │  │ Stack    │  │ (sched, mm)  │
   └────┬─────┘  └────┬─────┘  └──────┬───────┘
        │             │               │
        ▼             ▼               ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ Block    │  │ Socket   │  │ Memory       │
   │ Layer    │  │ Buffer   │  │ Manager      │
   └────┬─────┘  └────┬─────┘  └──────┬───────┘
        │             │               │
        ▼             ▼               ▼
   ┌────────────────────────────────────────────┐
   │          Hardware Abstraction Layer        │
   │    (device drivers, interrupt handlers)    │
   └────────────────────────────────────────────┘
```

## 1.4 Kernel Build System — How It Compiles

Understanding how the kernel is built reveals its modular structure:

```bash
# Kernel configuration
make menuconfig     # Curses TUI
make defconfig      # Arch default
make allmodconfig   # All as modules

# Key config options that affect data structures
CONFIG_SLAB         # SLAB allocator
CONFIG_SLUB         # SLUB allocator (default)
CONFIG_SLOB         # Simple allocator (embedded)
CONFIG_PREEMPT      # Full preemption
CONFIG_HZ_1000      # Timer frequency → scheduling granularity
CONFIG_PAGE_TABLE_ISOLATION  # Meltdown mitigation
```

The `.config` file drives `include/generated/autoconf.h` — every `#ifdef CONFIG_X` in kernel source becomes a compile-time decision. This is not runtime overhead; it's **compile-time specialization**.

---

# 2. Memory Management

## 2.1 Physical Memory Model — From RAM to Pages

The CPU sees RAM as a flat array of bytes. The kernel imposes structure through **pages** — the fundamental unit of memory management.

**Page sizes (x86_64):**
- 4 KiB (standard) — `PAGE_SIZE = 4096`
- 2 MiB (huge page) — PMD-level mapping
- 1 GiB (gigantic page) — PUD-level mapping

**Why 4 KiB?**
- Historical: Intel 386 chose 4K as compromise between TLB coverage and fragmentation
- 4K pages → 1M pages per 4GB → manageable page table size
- Large pages reduce TLB misses but increase internal fragmentation

### Physical Memory Zones

Linux divides physical memory into **zones** based on hardware constraints:

```
ZONE_DMA        (0 - 16 MB)     — ISA DMA devices (24-bit address bus)
ZONE_DMA32      (0 - 4 GB)      — 32-bit PCI devices
ZONE_NORMAL     (rest of RAM)   — Direct kernel mapping
ZONE_HIGHMEM    (>896MB on 32-bit) — Not directly mapped (32-bit only)
ZONE_MOVABLE    — Movable pages (for memory hotplug)
ZONE_DEVICE     — Device memory (PMEM, GPU)
```

**Data structure: `struct zone`** (simplified)
```c
struct zone {
    unsigned long _watermark[NR_WMARK];  /* min, low, high watermarks */
    long lowmem_reserve[MAX_NR_ZONES];
    
    /* Free area — one per order (0 to MAX_ORDER-1) */
    struct free_area free_area[MAX_ORDER];
    
    /* LRU lists for page reclaim */
    struct lruvec __lruvec;
    
    /* Statistics */
    atomic_long_t vm_stat[NR_VM_ZONE_STAT_ITEMS];
    
    char *name;
    unsigned long zone_start_pfn;   /* Page Frame Number */
    unsigned long managed_pages;
} ____cacheline_internodealigned_in_smp;
```

The `____cacheline_internodealigned_in_smp` attribute ensures the struct begins on a cache line boundary and is padded to avoid false sharing across NUMA nodes.

## 2.2 The Buddy Allocator — Physical Page Allocation

The **buddy system** is a binary tree-based allocator that manages free pages in power-of-2 blocks. This is one of the most elegant algorithms in systems programming.

### Core Insight

Every block of size `2^k` can be split into two "buddies" of size `2^(k-1)`. When both buddies are free, they are merged back. This gives O(log n) allocation and deallocation.

**The buddy relationship:**
```
Block of order k at address A:
  Its buddy is at address: A XOR (1 << (k + PAGE_SHIFT))
```

This XOR trick is elegant: flipping bit k in the page frame number gives you the buddy. No lookup table needed.

### Free Area Structure

```c
struct free_area {
    struct list_head free_list[MIGRATE_TYPES];
    unsigned long    nr_free;
};

/* MAX_ORDER = 11 means blocks up to 2^10 = 1024 pages = 4MB */
#define MAX_ORDER 11
```

Each order has multiple free lists by **migrate type**:
- `MIGRATE_UNMOVABLE` — kernel data, cannot be moved
- `MIGRATE_MOVABLE` — user pages, can be migrated (for defrag)
- `MIGRATE_RECLAIMABLE` — page cache, can be reclaimed

### Buddy Allocator — C Implementation

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define MAX_ORDER    11
#define PAGE_SIZE    4096
#define MIN_PAGES    (1 << MAX_ORDER)  /* 2048 pages minimum pool */

typedef struct block {
    struct block *next;
    int order;
} Block;

typedef struct buddy_allocator {
    Block *free_lists[MAX_ORDER];
    uint8_t *memory;
    size_t total_pages;
    uint8_t *bitmap;  /* bit set = page allocated */
} BuddyAllocator;

static inline size_t block_size(int order) {
    return (size_t)(1 << order) * PAGE_SIZE;
}

static inline uintptr_t buddy_addr(uintptr_t addr, int order, uintptr_t base) {
    return base + ((addr - base) ^ block_size(order));
}

BuddyAllocator *buddy_init(size_t num_pages) {
    /* Align to highest power of 2 */
    int max_order = 0;
    while ((1 << (max_order + 1)) <= (int)num_pages) max_order++;
    
    BuddyAllocator *alloc = calloc(1, sizeof(BuddyAllocator));
    alloc->memory = aligned_alloc(PAGE_SIZE, num_pages * PAGE_SIZE);
    alloc->total_pages = num_pages;
    alloc->bitmap = calloc(num_pages / 8 + 1, 1);
    
    /* Initialize: put entire memory as one large block */
    size_t pages = num_pages;
    uintptr_t base = (uintptr_t)alloc->memory;
    
    for (int order = max_order; order >= 0 && pages > 0; order--) {
        size_t block_pages = (size_t)(1 << order);
        if (pages >= block_pages) {
            Block *blk = (Block *)(base + (num_pages - pages) * PAGE_SIZE);
            blk->next = alloc->free_lists[order];
            blk->order = order;
            alloc->free_lists[order] = blk;
            pages -= block_pages;
        }
    }
    return alloc;
}

void *buddy_alloc(BuddyAllocator *alloc, int order) {
    if (order >= MAX_ORDER) return NULL;
    
    /* Find smallest available order >= requested */
    int current = order;
    while (current < MAX_ORDER && alloc->free_lists[current] == NULL)
        current++;
    
    if (current == MAX_ORDER) return NULL;  /* OOM */
    
    /* Remove block from free list */
    Block *blk = alloc->free_lists[current];
    alloc->free_lists[current] = blk->next;
    
    /* Split down to requested order */
    while (current > order) {
        current--;
        /* The upper half becomes the buddy — put it back */
        Block *buddy = (Block *)((uint8_t *)blk + block_size(current));
        buddy->order = current;
        buddy->next = alloc->free_lists[current];
        alloc->free_lists[current] = buddy;
    }
    
    blk->order = order;
    return (void *)blk;
}

void buddy_free(BuddyAllocator *alloc, void *ptr, int order) {
    uintptr_t base = (uintptr_t)alloc->memory;
    uintptr_t addr = (uintptr_t)ptr;
    
    while (order < MAX_ORDER - 1) {
        uintptr_t baddr = buddy_addr(addr, order, base);
        
        /* Search for buddy in free list */
        Block **prev = &alloc->free_lists[order];
        Block *cur = *prev;
        int found = 0;
        
        while (cur) {
            if ((uintptr_t)cur == baddr) {
                *prev = cur->next;  /* Remove buddy */
                found = 1;
                break;
            }
            prev = &cur->next;
            cur = cur->next;
        }
        
        if (!found) break;  /* Buddy not free, stop merging */
        
        /* Merge: lower address is the combined block */
        if (baddr < addr) addr = baddr;
        order++;
    }
    
    /* Insert merged block into free list */
    Block *blk = (Block *)addr;
    blk->order = order;
    blk->next = alloc->free_lists[order];
    alloc->free_lists[order] = blk;
}
```

**Time Complexity:**
- Allocation: O(MAX_ORDER) = O(11) ≈ O(1) — scanning orders is bounded
- Deallocation: O(MAX_ORDER) — merging is bounded by tree height
- **This is why the buddy system is used in kernels** — bounded, predictable time

### Buddy Allocator — Rust Implementation

```rust
use std::alloc::{alloc, dealloc, Layout};
use std::ptr::NonNull;

const MAX_ORDER: usize = 11;
const PAGE_SIZE: usize = 4096;

struct FreeBlock {
    next: Option<NonNull<FreeBlock>>,
}

pub struct BuddyAllocator {
    free_lists: [Option<NonNull<FreeBlock>>; MAX_ORDER],
    base: NonNull<u8>,
    total_size: usize,
}

unsafe impl Send for BuddyAllocator {}

impl BuddyAllocator {
    /// # Safety: `size` must be a power of 2 and >= PAGE_SIZE * 2
    pub unsafe fn new(size: usize) -> Self {
        assert!(size.is_power_of_two());
        assert!(size >= PAGE_SIZE * 2);
        
        let layout = Layout::from_size_align(size, PAGE_SIZE).unwrap();
        let base = NonNull::new(alloc(layout)).expect("allocation failed");
        
        let mut alloc = BuddyAllocator {
            free_lists: [None; MAX_ORDER],
            base,
            total_size: size,
        };
        
        // Place entire memory as highest order free block
        let max_order = (size / PAGE_SIZE).trailing_zeros() as usize;
        let order = max_order.min(MAX_ORDER - 1);
        
        let block = base.as_ptr() as *mut FreeBlock;
        (*block).next = None;
        alloc.free_lists[order] = Some(NonNull::new_unchecked(block));
        
        alloc
    }
    
    fn block_size(order: usize) -> usize {
        PAGE_SIZE << order
    }
    
    fn buddy_of(&self, addr: usize, order: usize) -> usize {
        let base = self.base.as_ptr() as usize;
        base + ((addr - base) ^ Self::block_size(order))
    }
    
    /// Allocate 2^order pages. Returns None if OOM.
    pub unsafe fn allocate(&mut self, order: usize) -> Option<NonNull<u8>> {
        if order >= MAX_ORDER { return None; }
        
        // Find smallest order with available block
        let mut current = order;
        while current < MAX_ORDER && self.free_lists[current].is_none() {
            current += 1;
        }
        if current == MAX_ORDER { return None; }
        
        // Pop from free list
        let block = self.free_lists[current].take()?;
        self.free_lists[current] = (*block.as_ptr()).next;
        
        // Split until we reach requested order
        while current > order {
            current -= 1;
            let buddy_ptr = (block.as_ptr() as usize + Self::block_size(current)) 
                            as *mut FreeBlock;
            (*buddy_ptr).next = self.free_lists[current];
            self.free_lists[current] = NonNull::new(buddy_ptr);
        }
        
        Some(block.cast::<u8>())
    }
    
    /// Deallocate a block of 2^order pages at `ptr`.
    pub unsafe fn deallocate(&mut self, ptr: NonNull<u8>, mut order: usize) {
        let mut addr = ptr.as_ptr() as usize;
        
        while order < MAX_ORDER - 1 {
            let buddy_addr = self.buddy_of(addr, order);
            
            // Search for buddy in free list
            let mut found = false;
            let mut prev: *mut Option<NonNull<FreeBlock>> = &mut self.free_lists[order];
            let mut cur = self.free_lists[order];
            
            while let Some(node) = cur {
                if node.as_ptr() as usize == buddy_addr {
                    // Remove buddy from list
                    *prev = (*node.as_ptr()).next;
                    found = true;
                    break;
                }
                prev = &mut (*node.as_ptr()).next;
                cur = (*node.as_ptr()).next;
            }
            
            if !found { break; }
            
            // Merge: use lower address
            if buddy_addr < addr { addr = buddy_addr; }
            order += 1;
        }
        
        let block = addr as *mut FreeBlock;
        (*block).next = self.free_lists[order];
        self.free_lists[order] = NonNull::new(block);
    }
}

impl Drop for BuddyAllocator {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::from_size_align(self.total_size, PAGE_SIZE).unwrap();
            dealloc(self.base.as_ptr(), layout);
        }
    }
}
```

### Buddy Allocator — Go Implementation

```go
package buddy

import (
    "sync"
    "unsafe"
)

const (
    MaxOrder = 11
    PageSize = 4096
)

type freeBlock struct {
    next *freeBlock
}

type BuddyAllocator struct {
    mu        sync.Mutex
    freeLists [MaxOrder]*freeBlock
    base      uintptr
    memory    []byte
}

func blockSize(order int) uintptr {
    return uintptr(PageSize) << order
}

func NewBuddyAllocator(pages int) *BuddyAllocator {
    // Find highest power-of-2 order
    order := 0
    for (1 << (order + 1)) <= pages {
        order++
    }
    if order >= MaxOrder {
        order = MaxOrder - 1
    }
    
    totalSize := (1 << order) * PageSize
    memory := make([]byte, totalSize+PageSize) // extra for alignment
    
    // Align to page boundary
    base := (uintptr(unsafe.Pointer(&memory[0])) + PageSize - 1) &^ (PageSize - 1)
    
    alloc := &BuddyAllocator{
        base:   base,
        memory: memory,
    }
    
    // Place entire aligned memory as one block
    blk := (*freeBlock)(unsafe.Pointer(base))
    blk.next = nil
    alloc.freeLists[order] = blk
    
    return alloc
}

func (b *BuddyAllocator) buddyOf(addr uintptr, order int) uintptr {
    return b.base + ((addr - b.base) ^ blockSize(order))
}

func (b *BuddyAllocator) Allocate(order int) unsafe.Pointer {
    if order >= MaxOrder {
        return nil
    }
    
    b.mu.Lock()
    defer b.mu.Unlock()
    
    // Find available order
    current := order
    for current < MaxOrder && b.freeLists[current] == nil {
        current++
    }
    if current == MaxOrder {
        return nil // OOM
    }
    
    // Pop block
    blk := b.freeLists[current]
    b.freeLists[current] = blk.next
    
    // Split down
    for current > order {
        current--
        buddyPtr := uintptr(unsafe.Pointer(blk)) + blockSize(current)
        buddy := (*freeBlock)(unsafe.Pointer(buddyPtr))
        buddy.next = b.freeLists[current]
        b.freeLists[current] = buddy
    }
    
    return unsafe.Pointer(blk)
}

func (b *BuddyAllocator) Free(ptr unsafe.Pointer, order int) {
    b.mu.Lock()
    defer b.mu.Unlock()
    
    addr := uintptr(ptr)
    
    for order < MaxOrder-1 {
        buddyAddr := b.buddyOf(addr, order)
        
        // Find and remove buddy from free list
        var prev **freeBlock = &b.freeLists[order]
        cur := b.freeLists[order]
        found := false
        
        for cur != nil {
            if uintptr(unsafe.Pointer(cur)) == buddyAddr {
                *prev = cur.next
                found = true
                break
            }
            prev = &cur.next
            cur = cur.next
        }
        
        if !found {
            break
        }
        
        if buddyAddr < addr {
            addr = buddyAddr
        }
        order++
    }
    
    blk := (*freeBlock)(unsafe.Pointer(addr))
    blk.next = b.freeLists[order]
    b.freeLists[order] = blk
}
```

## 2.3 The SLAB/SLUB Allocator — Object Caching

The buddy allocator works at page granularity. For smaller allocations (kernel structures), Linux uses the **SLAB allocator** (now replaced by SLUB in most configs).

### The Core Problem SLAB Solves

The kernel frequently allocates and frees the same structures:
- `task_struct` (process descriptor) — created/destroyed on fork/exit
- `inode` — created on file open, destroyed on last close
- `sk_buff` — network packet descriptor — millions per second on busy servers

Without caching, each allocation goes through the buddy system (minimum 4K page), wastes memory, and is slow due to initialization overhead.

**SLAB Insight:** Keep a cache of pre-initialized objects. When freed, an object returns to the cache — it is NOT zeroed. Next allocation gets the warm object without initialization. This is the **constructor/destructor** model.

### SLUB Architecture (current Linux default)

```
kmem_cache (per object type)
├── kmem_cache_cpu (per-CPU — lockless fast path)
│   ├── freelist  ────→ [obj] → [obj] → [obj] → NULL
│   └── page      ────→ struct page (current slab)
│
└── kmem_cache_node (per NUMA node — locked slow path)
    ├── partial   ────→ [slab] → [slab] → (partially free slabs)
    └── full      ────→ [slab] → [slab] → (full slabs, Linux omits this list)
```

**Fast path (per-CPU, no lock):**
```c
void *kmem_cache_alloc(struct kmem_cache *s, gfp_t gfpflags) {
    void *ret = __kmem_cache_alloc_lru(s, NULL, gfpflags);
    /* 
     * Per-CPU path: just pop from freelist pointer.
     * If freelist is NULL, slow path to get new slab from node.
     */
    return ret;
}
```

### SLAB/SLUB — C Implementation (Simplified)

```c
#include <stddef.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>

#define SLAB_SIZE    4096  /* one page per slab */

typedef void (*ctor_fn)(void *obj);

typedef struct slab {
    struct slab *next;
    void *freelist;          /* linked list of free objects within slab */
    int  free_count;
    int  total_count;
    uint8_t data[];          /* flexible array — object storage */
} Slab;

typedef struct kmem_cache {
    const char *name;
    size_t obj_size;         /* size of each object */
    size_t obj_align;
    ctor_fn ctor;
    
    Slab *partial;           /* partially filled slabs */
    Slab *full;
    Slab *free;              /* completely empty slabs */
    
    size_t slab_count;
    size_t alloc_count;
    
    pthread_mutex_t lock;
} KmemCache;

static Slab *slab_create(KmemCache *cache) {
    size_t obj_size = (cache->obj_size + cache->obj_align - 1) 
                      & ~(cache->obj_align - 1);
    
    /* How many objects fit in a slab? */
    size_t header = sizeof(Slab);
    size_t num_objs = (SLAB_SIZE - header) / obj_size;
    
    Slab *slab = aligned_alloc(SLAB_SIZE, SLAB_SIZE);
    if (!slab) return NULL;
    
    slab->next = NULL;
    slab->free_count = (int)num_objs;
    slab->total_count = (int)num_objs;
    
    /* Build freelist: each free object stores a pointer to the next */
    uint8_t *data = slab->data;
    void **next = NULL;
    slab->freelist = data;
    
    for (size_t i = 0; i < num_objs; i++) {
        void *obj = data + i * obj_size;
        /* Call constructor if provided */
        if (cache->ctor) cache->ctor(obj);
        /* Embed next pointer at start of free object */
        *(void **)obj = (i + 1 < num_objs) ? (data + (i + 1) * obj_size) : NULL;
        next = (void **)obj;
    }
    
    return slab;
}

KmemCache *kmem_cache_create(const char *name, size_t size, 
                              size_t align, ctor_fn ctor) {
    KmemCache *cache = calloc(1, sizeof(KmemCache));
    cache->name = name;
    cache->obj_size = size;
    cache->obj_align = align < sizeof(void *) ? sizeof(void *) : align;
    cache->ctor = ctor;
    pthread_mutex_init(&cache->lock, NULL);
    return cache;
}

void *kmem_cache_alloc(KmemCache *cache) {
    pthread_mutex_lock(&cache->lock);
    
    /* Get a partial slab */
    if (!cache->partial) {
        Slab *slab = slab_create(cache);
        if (!slab) { pthread_mutex_unlock(&cache->lock); return NULL; }
        cache->partial = slab;
        cache->slab_count++;
    }
    
    Slab *slab = cache->partial;
    void *obj = slab->freelist;
    slab->freelist = *(void **)obj;  /* pop from freelist */
    slab->free_count--;
    
    /* Move to full list if no more free objects */
    if (slab->free_count == 0) {
        cache->partial = slab->next;
        slab->next = cache->full;
        cache->full = slab;
    }
    
    cache->alloc_count++;
    pthread_mutex_unlock(&cache->lock);
    return obj;
}

void kmem_cache_free(KmemCache *cache, void *obj) {
    pthread_mutex_lock(&cache->lock);
    
    /* 
     * Find which slab this object belongs to.
     * In real SLUB: page->slab_cache pointer makes this O(1).
     * Here we scan for simplicity — real kernels never do this.
     */
    Slab *slab = NULL;
    Slab **prev = &cache->full;
    Slab *cur = cache->full;
    
    while (cur) {
        uintptr_t start = (uintptr_t)cur->data;
        uintptr_t end   = (uintptr_t)cur + SLAB_SIZE;
        if ((uintptr_t)obj >= start && (uintptr_t)obj < end) {
            *prev = cur->next;
            slab = cur;
            break;
        }
        prev = &cur->next;
        cur = cur->next;
    }
    
    if (!slab) {
        /* Check partial list */
        prev = &cache->partial;
        cur = cache->partial;
        while (cur) {
            uintptr_t start = (uintptr_t)cur->data;
            uintptr_t end   = (uintptr_t)cur + SLAB_SIZE;
            if ((uintptr_t)obj >= start && (uintptr_t)obj < end) {
                slab = cur;
                break;
            }
            prev = &cur->next;
            cur = cur->next;
        }
    }
    
    if (!slab) { pthread_mutex_unlock(&cache->lock); return; }  /* corrupt */
    
    /* Push object back to freelist */
    *(void **)obj = slab->freelist;
    slab->freelist = obj;
    slab->free_count++;
    
    /* Move back to partial if was full */
    if (slab->free_count == 1) {
        slab->next = cache->partial;
        cache->partial = slab;
    }
    
    cache->alloc_count--;
    pthread_mutex_unlock(&cache->lock);
}
```

## 2.4 Virtual Memory Areas (VMAs)

When a process calls `mmap()`, `malloc()`, or accesses a new stack frame, the kernel creates a **Virtual Memory Area (VMA)**. This is the key data structure linking virtual addresses to their backing store.

```c
struct vm_area_struct {
    /* VMA covers [vm_start, vm_end) */
    unsigned long vm_start;
    unsigned long vm_end;
    
    struct vm_area_struct *vm_next, *vm_prev;  /* linked list */
    struct rb_node vm_rb;                       /* red-black tree node */
    
    pgprot_t vm_page_prot;   /* page protection flags */
    unsigned long vm_flags;  /* VM_READ, VM_WRITE, VM_EXEC, VM_SHARED... */
    
    struct file *vm_file;    /* backing file (NULL for anonymous) */
    unsigned long vm_pgoff;  /* offset in file (in pages) */
    
    const struct vm_operations_struct *vm_ops; /* fault handlers */
};
```

**Two data structures for VMAs:** Linux maintains VMAs in both:
1. **Linked list** (`vm_next`/`vm_prev`) — for sequential operations like `/proc/pid/maps`
2. **Red-black tree** (`vm_rb`) — for O(log n) address lookup during page faults

This is a classic CS pattern: **maintain multiple views of the same data** for different access patterns.

## 2.5 Page Tables — Four-Level Hierarchy (x86_64)

```
Virtual Address (48 bits):
┌─────┬─────┬─────┬─────┬────────────┐
│ PGD │ P4D │ PUD │ PMD │  PTE  │Offset│
│  9  │  9  │  9  │  9  │  9    │ 12  │
└─────┴─────┴─────┴─────┴────────────┘

PGD = Page Global Directory    (cr3 points here)
P4D = Page 4th-level Directory (added for 5-level paging)
PUD = Page Upper Directory
PMD = Page Middle Directory
PTE = Page Table Entry         (points to physical page)
```

**Page walk algorithm:**
```
CR3 → PGD[vaddr[47:39]] → PUD[vaddr[38:30]] → PMD[vaddr[29:21]] → PTE[vaddr[20:12]] → Physical page + vaddr[11:0]
```

**TLB (Translation Lookaside Buffer):** Hardware cache of recent virtual→physical translations. A TLB miss triggers a page walk (hardware walker on x86, software on MIPS/ARM older cores). TLB shootdown on SMP requires IPI (Inter-Processor Interrupt) to all CPUs — expensive!

## 2.6 Page Fault Handling — The Most Critical Path

A page fault is the mechanism by which the kernel implements lazy allocation, copy-on-write, swapping, and memory-mapped I/O.

```
CPU raises #PF exception
        │
        ▼
do_page_fault() [arch/x86/mm/fault.c]
        │
        ├─ Is the address in kernel space?
        │    Yes → check for kernel bug → oops() / panic()
        │
        ├─ find_vma(mm, fault_address)
        │    Not found → SIGSEGV
        │
        ├─ Check permissions (write to read-only?) → SIGSEGV
        │
        └─ handle_mm_fault()
               │
               ├─ Page present but protection fault → handle_pte_fault
               │    ├─ Write to shared page → COW (copy-on-write)
               │    └─ Write to private page → wp_page_copy
               │
               ├─ Page not present:
               │    ├─ Anonymous page → do_anonymous_page (zero fill)
               │    ├─ File-backed → do_fault → vm_ops->fault()
               │    └─ Swap page → do_swap_page (read from swap)
               │
               └─ Return: handle minor/major fault accounting
```

**Minor fault:** Page exists in memory (e.g., COW, zero-fill) — no I/O.
**Major fault:** Page must be read from disk — involves I/O scheduler.

## 2.7 Memory Reclaim — LRU and Clock Algorithms

When physical memory is scarce, the kernel must reclaim pages. Linux uses a **two-list LRU** approximation:

```
Active List (hot pages)     Inactive List (cold pages)
[page] → [page] → ...      [page] → [page] → ...
    ↑                                       ↓
    │   (page accessed → promoted)          │
    └───────────────────────────────────────┘
                                    │
                              page_referenced() → reclaim if not recently accessed
```

**Why two lists?**
- Single LRU: A process doing `cat large_file` scans the entire file into LRU, evicting working-set pages (cache thrashing)
- Two lists: File scan pages enter inactive list. Only pages accessed twice get promoted to active. Working set survives.

This is the **clock algorithm** (second-chance page replacement) implemented with two lists.

**Page flags controlling reclaim:**
```c
/* In struct page / folio */
PG_referenced   /* set on access, cleared by scanner */
PG_active       /* on active list */
PG_swapbacked   /* anonymous page → swap on reclaim */
PG_dirty        /* modified, must write before reclaim */
PG_writeback    /* being written to disk */
```

---

# 3. Process & Thread Management

## 3.1 task_struct — The Process Descriptor

Every process (and thread) in Linux is represented by `struct task_struct`. At ~700 fields, it is the most complex data structure in the kernel. Let's understand its key sections:

```c
struct task_struct {
    /*
     * State machine:
     * TASK_RUNNING      — on CPU or runqueue
     * TASK_INTERRUPTIBLE — sleeping, wakeup on signal
     * TASK_UNINTERRUPTIBLE — sleeping, no signal interrupt (disk I/O)
     * TASK_STOPPED      — SIGSTOP received
     * TASK_TRACED       — being ptrace'd
     * EXIT_ZOMBIE       — exited, parent not yet collected
     * EXIT_DEAD         — fully dead
     */
    unsigned int __state;
    
    /* Scheduling */
    int prio;                    /* effective priority */
    int static_prio;             /* static nice-based priority */
    int normal_prio;
    unsigned int rt_priority;    /* real-time priority (0-99) */
    const struct sched_class *sched_class;  /* CFS, RT, DL, idle */
    struct sched_entity se;      /* CFS scheduling entity */
    struct sched_rt_entity rt;   /* RT scheduling entity */
    struct sched_dl_entity dl;   /* Deadline scheduling entity */
    
    /* Process IDs */
    pid_t pid;       /* process ID (unique per thread) */
    pid_t tgid;      /* thread group ID (= pid of main thread) */
    
    /* Process tree */
    struct task_struct __rcu *real_parent;
    struct task_struct __rcu *parent;
    struct list_head children;   /* list of children */
    struct list_head sibling;    /* sibling link in parent's children */
    struct task_struct *group_leader;  /* thread group leader */
    
    /* Memory */
    struct mm_struct *mm;         /* user address space (NULL for kernel threads) */
    struct mm_struct *active_mm;  /* active address space */
    
    /* File system */
    struct fs_struct *fs;         /* filesystem info (root, pwd) */
    struct files_struct *files;   /* open file descriptors */
    
    /* Signals */
    struct signal_struct *signal;
    struct sighand_struct __rcu *sighand;
    sigset_t blocked;
    struct sigpending pending;
    
    /* Credentials */
    const struct cred __rcu *real_cred;
    const struct cred __rcu *cred;
    
    /* Timing */
    u64 utime, stime;            /* user and system time */
    u64 start_time;              /* monotonic */
    u64 start_boottime;          /* boottime */
    
    /* CPU */
    int on_cpu;                  /* currently executing on a CPU */
    int cpu;                     /* current/last CPU */
    
    /* Stack */
    void *stack;                 /* kernel stack pointer */
};
```

## 3.2 Process vs Thread — The Kernel View

In Linux, **there is no fundamental distinction** between processes and threads at the kernel level. Both are `task_struct`. The difference is in **resource sharing**:

```
fork():
  task_struct A ─── mm_struct (own copy) ─── page tables (COW)
                └── files_struct (own copy)
                └── signal_struct (own copy)

clone(CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND):
  task_struct B ─── mm_struct (SHARED with A) ─── same page tables!
                └── files_struct (SHARED)
                └── signal_struct (SHARED)
```

`pthread_create()` in glibc calls `clone()` with the flags above. The new "thread" shares the same `mm_struct`, so they see the same virtual address space.

**Key insight:** The kernel scheduler sees threads and processes identically — they are all `task_struct` nodes on runqueues. The distinction is entirely in resource sharing flags.

## 3.3 Process Creation — fork() and COW

```c
/* Simplified fork() call chain */
sys_fork()
  └─ kernel_clone()
       └─ copy_process()
            ├─ dup_task_struct()       /* allocate new task_struct + kernel stack */
            ├─ copy_mm()               /* copy_on_write duplicate of page tables */
            ├─ copy_files()            /* duplicate file descriptor table */
            ├─ copy_signal()           /* duplicate signal handlers */
            ├─ copy_namespaces()       /* PID/mount/network namespaces */
            └─ pid_alloc()             /* assign new PID */
       └─ wake_up_new_task()           /* add to runqueue */
```

**Copy-on-Write magic:**
```
Parent virtual address 0x601000 → PTE: physical 0x7f000 [RW] 

After fork():
  Parent PTE: 0x7f000 [RO]  ← write protection ADDED
  Child  PTE: 0x7f000 [RO]  ← same physical page

On first write by either:
  Page fault → kernel allocates new page → copies content
  Fault-er's PTE: new_page [RW]
  Other's PTE: 0x7f000 [RW] (restored)
```

COW makes `fork()` O(1) regardless of process size. The entire multi-GB address space of a process can be forked in microseconds.

## 3.4 Process States — State Machine Analysis

```
                    fork()
                       │
                       ▼
            ┌──────TASK_RUNNING──────┐
            │   (on runqueue)        │
            │                        │
     scheduled                  preempted/yield
     onto CPU                        │
            │                        │
            ▼                        │
       TASK_RUNNING ────────────────┘
       (on CPU)
            │
    blocking syscall / wait
            │
            ├──→ TASK_INTERRUPTIBLE
            │         │
            │    signal or event
            │         │
            ├──→ TASK_UNINTERRUPTIBLE
            │         │
            │    event only (no signal wake)
            │         │
            └──────────────────────→ (back to TASK_RUNNING)
            │
         exit()
            │
            ▼
       EXIT_ZOMBIE (task_struct remains, parent must wait())
            │
         wait() by parent
            │
            ▼
       EXIT_DEAD → task_struct freed
```

**Zombie processes:** The `task_struct` remains after `exit()` because the parent might call `wait()` to collect the exit status. If the parent never calls `wait()`, zombies accumulate. If the parent dies, zombies are reparented to `init` (PID 1), which always collects them.

## 3.5 Namespaces — The Foundation of Containers

Linux namespaces virtualize global resources. Each `task_struct` has a `nsproxy` pointer:

```c
struct nsproxy {
    atomic_t count;
    struct uts_namespace  *uts_ns;   /* hostname, domainname */
    struct ipc_namespace  *ipc_ns;   /* SysV IPC, POSIX MQ */
    struct mnt_namespace  *mnt_ns;   /* mount points */
    struct pid_namespace  *pid_ns_for_children;
    struct net            *net_ns;   /* network stack */
    struct time_namespace *time_ns;
    struct cgroup_namespace *cgroup_ns;
};
```

Docker containers are simply processes with **all namespaces** set to private:
```bash
unshare --pid --mount --net --uts --ipc --user /bin/bash
```
This creates a bash shell that sees an isolated PID space, mount table, network stack, hostname, IPC objects, and UID/GID mapping.

**PID namespace:** PIDs are local to a namespace. PID 1 in a container is some process with PID e.g. 4821 in the host namespace. If PID 1 in a container dies, all other processes in that namespace receive SIGKILL.

---

# 4. CPU Scheduling Algorithms

## 4.1 The Scheduler — Historical Context

Linux scheduler evolution:
- **O(n) scheduler** (≤2.4): Simple priority queue, O(n) to find next task
- **O(1) scheduler** (2.5-2.6.22): Two bitmap-indexed priority arrays, O(1) scheduling but poor interactivity
- **CFS** (2.6.23+): Completely Fair Scheduler using red-black tree, virtual runtime based fairness
- **EEVDF** (6.6+): Earliest Eligible Virtual Deadline First, more responsive than CFS

## 4.2 CFS — Completely Fair Scheduler

### Core Idea: Virtual Runtime

CFS tracks how much CPU time each task has **consumed** in nanoseconds, weighted by priority (nice value). The task with the **smallest vruntime** is scheduled next.

```
vruntime += actual_runtime × (NICE_0_WEIGHT / task_weight)
```

Higher priority (lower nice) tasks have higher weight → vruntime increases slower → they stay at the left (minimum) of the red-black tree → scheduled more often.

**Weight table (kernel/sched/core.c):**
```c
const int sched_prio_to_weight[40] = {
 /* -20 */ 88761, 71755, 56483, 46273, 36291,
 /* -15 */ 29154, 23254, 18705, 14949, 11916,
 /* -10 */  9548,  7620,  6100,  4904,  3906,
 /*  -5 */  3121,  2501,  1991,  1586,  1277,
 /*   0 */  1024,   820,   655,   526,   423,
 /*   5 */   335,   272,   215,   172,   137,
 /*  10 */   110,    87,    70,    56,    45,
 /*  15 */    36,    29,    23,    18,    15,
};
```

Each step is approximately 1.25× — so a nice -1 task gets ~25% more CPU than nice 0.

### The Run Queue — Red-Black Tree

CFS maintains tasks in a **red-black tree** keyed by `vruntime`. The minimum element (leftmost node) is always cached:

```c
struct cfs_rq {
    struct load_weight load;
    unsigned int nr_running;
    u64 min_vruntime;              /* leftmost vruntime (cached) */
    
    struct rb_root_cached tasks_timeline;  /* RB tree + leftmost cache */
    
    struct sched_entity *curr;     /* currently running entity */
    struct sched_entity *next;     /* next to run (skip logic) */
};
```

**Scheduling tick:** Every timer interrupt (HZ = 1000 → 1ms), `scheduler_tick()` is called. If the current task has run longer than its "ideal runtime slice" (`sysctl_sched_min_granularity`), it's marked for preemption (`TIF_NEED_RESCHED` flag set).

### CFS — Go Simulation

```go
package cfs

import (
    "container/heap"
    "fmt"
    "math"
)

const NICE0Weight = 1024

var niceToWeight = [40]int{
    88761, 71755, 56483, 46273, 36291,
    29154, 23254, 18705, 14949, 11916,
     9548,  7620,  6100,  4904,  3906,
     3121,  2501,  1991,  1586,  1277,
     1024,   820,   655,   526,   423,
      335,   272,   215,   172,   137,
      110,    87,    70,    56,    45,
       36,    29,    23,    18,    15,
}

type Task struct {
    PID      int
    Nice     int      // -20 to 19
    Vruntime float64  // nanoseconds
    Weight   int
    index    int      // heap index
}

func weightForNice(nice int) int {
    return niceToWeight[nice+20]
}

// Priority queue (min-heap by vruntime)
type TaskHeap []*Task

func (h TaskHeap) Len() int            { return len(h) }
func (h TaskHeap) Less(i, j int) bool  { return h[i].Vruntime < h[j].Vruntime }
func (h TaskHeap) Swap(i, j int) {
    h[i], h[j] = h[j], h[i]
    h[i].index = i
    h[j].index = j
}
func (h *TaskHeap) Push(x any) {
    t := x.(*Task)
    t.index = len(*h)
    *h = append(*h, t)
}
func (h *TaskHeap) Pop() any {
    old := *h
    n := len(old)
    t := old[n-1]
    t.index = -1
    *h = old[:n-1]
    return t
}

type CFSScheduler struct {
    rq         TaskHeap
    minVruntime float64
    totalWeight int
    tickNs      float64 // scheduling period per tick
}

func NewCFSScheduler(periodNs float64) *CFSScheduler {
    h := make(TaskHeap, 0)
    heap.Init(&h)
    return &CFSScheduler{rq: h, tickNs: periodNs}
}

func (s *CFSScheduler) AddTask(pid, nice int) *Task {
    t := &Task{
        PID:     pid,
        Nice:    nice,
        Weight:  weightForNice(nice),
        // New task starts at minVruntime to not starve others
        Vruntime: s.minVruntime,
    }
    s.totalWeight += t.Weight
    heap.Push(&s.rq, t)
    return t
}

func (s *CFSScheduler) Schedule() *Task {
    if s.rq.Len() == 0 {
        return nil
    }
    // Peek at minimum
    return s.rq[0]
}

func (s *CFSScheduler) Tick(actualNs float64) {
    if s.rq.Len() == 0 {
        return
    }
    
    current := heap.Pop(&s.rq).(*Task)
    
    // Weighted virtual runtime delta
    // delta_vruntime = actual_time * (NICE0_WEIGHT / task_weight)
    delta := actualNs * float64(NICE0Weight) / float64(current.Weight)
    current.Vruntime += delta
    
    // Update global min_vruntime
    if s.rq.Len() > 0 {
        s.minVruntime = math.Max(s.minVruntime, s.rq[0].Vruntime)
    }
    
    heap.Push(&s.rq, current)
}

func (s *CFSScheduler) IdealRuntime(t *Task) float64 {
    // Proportional share of scheduling period
    if s.totalWeight == 0 {
        return s.tickNs
    }
    return s.tickNs * float64(t.Weight) / float64(s.totalWeight)
}

func (s *CFSScheduler) PrintQueue() {
    fmt.Println("=== CFS Run Queue (sorted by vruntime) ===")
    for _, t := range s.rq {
        fmt.Printf("  PID %d | nice %+d | weight %d | vruntime %.2fns\n",
            t.PID, t.Nice, t.Weight, t.Vruntime)
    }
}
```

### CFS — Rust Simulation

```rust
use std::collections::BinaryHeap;
use std::cmp::Ordering;

const NICE0_WEIGHT: u64 = 1024;

static NICE_TO_WEIGHT: [u64; 40] = [
    88761, 71755, 56483, 46273, 36291,
    29154, 23254, 18705, 14949, 11916,
     9548,  7620,  6100,  4904,  3906,
     3121,  2501,  1991,  1586,  1277,
     1024,   820,   655,   526,   423,
      335,   272,   215,   172,   137,
      110,    87,    70,    56,    45,
       36,    29,    23,    18,    15,
];

fn weight_for_nice(nice: i8) -> u64 {
    NICE_TO_WEIGHT[(nice + 20) as usize]
}

#[derive(Debug, Clone)]
struct Task {
    pid: u32,
    nice: i8,
    weight: u64,
    vruntime_ns: u64,  // virtual runtime in nanoseconds
}

// Reverse ordering for min-heap (BinaryHeap is max-heap)
impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for Task {
    fn cmp(&self, other: &Self) -> Ordering {
        // Flip to make BinaryHeap behave as min-heap
        other.vruntime_ns.cmp(&self.vruntime_ns)
    }
}
impl PartialEq for Task {
    fn eq(&self, other: &Self) -> bool {
        self.vruntime_ns == other.vruntime_ns && self.pid == other.pid
    }
}
impl Eq for Task {}

struct CFSScheduler {
    runqueue: BinaryHeap<Task>,
    min_vruntime: u64,
    total_weight: u64,
    period_ns: u64,
}

impl CFSScheduler {
    fn new(period_ns: u64) -> Self {
        CFSScheduler {
            runqueue: BinaryHeap::new(),
            min_vruntime: 0,
            total_weight: 0,
            period_ns,
        }
    }
    
    fn add_task(&mut self, pid: u32, nice: i8) {
        let weight = weight_for_nice(nice);
        let task = Task {
            pid,
            nice,
            weight,
            vruntime_ns: self.min_vruntime,  // start at fair point
        };
        self.total_weight += weight;
        self.runqueue.push(task);
    }
    
    fn schedule(&self) -> Option<&Task> {
        self.runqueue.peek()
    }
    
    /// Run one scheduling tick with actual CPU time `actual_ns`
    fn tick(&mut self, actual_ns: u64) {
        if let Some(mut current) = self.runqueue.pop() {
            // delta_vruntime = actual_ns * (NICE0_WEIGHT / weight)
            // Use fixed-point: multiply first to avoid loss
            let delta_vruntime = actual_ns * NICE0_WEIGHT / current.weight;
            current.vruntime_ns += delta_vruntime;
            
            // Update min_vruntime
            if let Some(next) = self.runqueue.peek() {
                self.min_vruntime = self.min_vruntime.max(next.vruntime_ns);
            }
            
            self.runqueue.push(current);
        }
    }
    
    fn ideal_runtime_ns(&self, task: &Task) -> u64 {
        if self.total_weight == 0 { return self.period_ns; }
        self.period_ns * task.weight / self.total_weight
    }
    
    fn print_queue(&self) {
        println!("=== CFS Runqueue ===");
        let mut tasks: Vec<&Task> = self.runqueue.iter().collect();
        tasks.sort_by_key(|t| t.vruntime_ns);
        for t in tasks {
            println!("  PID {} | nice {:+} | weight {} | vruntime {}ns",
                t.pid, t.nice, t.weight, t.vruntime_ns);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_proportional_scheduling() {
        let mut sched = CFSScheduler::new(10_000_000); // 10ms period
        sched.add_task(1, 0);   // normal priority
        sched.add_task(2, -10); // high priority (2.5x weight)
        
        // Simulate 100 ticks of 1ms each
        let mut cpu_time = [0u64; 3];
        for _ in 0..100 {
            if let Some(t) = sched.schedule() {
                let pid = t.pid;
                let ideal = sched.ideal_runtime_ns(t);
                sched.tick(ideal);
                cpu_time[pid as usize] += ideal;
            }
        }
        
        // Task 2 (nice -10) should get ~2.5x more CPU
        let ratio = cpu_time[2] as f64 / cpu_time[1] as f64;
        assert!(ratio > 2.0 && ratio < 3.5, "ratio = {}", ratio);
    }
}
```

## 4.3 Real-Time Scheduling — SCHED_FIFO and SCHED_RR

```c
/* sched_setscheduler() */
struct sched_param param = { .sched_priority = 90 };
sched_setscheduler(0, SCHED_FIFO, &param);
```

**SCHED_FIFO:** Run until blocking or yielding. Higher priority preempts lower. No time slice within same priority.

**SCHED_RR:** Like FIFO but with time slice (default 100ms). Tasks at same priority round-robin.

**Priority:** 1 (lowest) to 99 (highest). RT tasks always preempt CFS tasks.

## 4.4 Deadline Scheduling — SCHED_DEADLINE

Based on **Earliest Deadline First (EDF)** algorithm:

```
Task parameters:
  Runtime  (C): How much CPU it needs per period
  Deadline (D): Must complete within D nanoseconds of activation
  Period   (P): Activation period

Schedulability: Σ(C_i / P_i) ≤ 1.0  (utilization ≤ 100%)
```

**EEVDF (since 6.6):**
Combines virtual deadline with eligible time: a task becomes "eligible" when it has waited proportionally to its share. Among eligible tasks, the one with earliest virtual deadline runs next. This handles latency-sensitive workloads better than pure CFS.

---

# 5. Data Structures Inside the Linux Kernel

## 5.1 Intrusive Linked Lists — `list_head`

The Linux kernel uses a distinctly different list design from textbook linked lists. Instead of the node containing the data, **the data structure contains the node**:

```c
/* In <linux/list.h> */
struct list_head {
    struct list_head *next, *prev;  /* circular doubly-linked */
};

/* Usage in task_struct: */
struct task_struct {
    /* ... */
    struct list_head tasks;   /* global task list */
    struct list_head children;
    struct list_head sibling;
};

/* Traversal — container_of magic */
#define list_entry(ptr, type, member) \
    container_of(ptr, type, member)

#define container_of(ptr, type, member) ({          \
    const typeof(((type *)0)->member) *__mptr = (ptr); \
    (type *)((char *)__mptr - offsetof(type, member)); })

/* Example: iterate all tasks */
struct task_struct *task;
list_for_each_entry(task, &init_task.tasks, tasks) {
    printk("PID %d: %s\n", task->pid, task->comm);
}
```

**Why intrusive?**
- No separate allocation for list nodes → no memory overhead
- Cache locality: accessing the node immediately accesses the data
- A structure can be on multiple lists simultaneously (task on `tasks`, `children`, `sibling` at once)
- `container_of` computes the enclosing struct pointer from member pointer using compile-time offset arithmetic

### Implementation: Intrusive List in C, Go, Rust

**C:**
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

struct list_head {
    struct list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define LIST_HEAD(name) struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *list) {
    list->next = list;
    list->prev = list;
}

static inline void __list_add(struct list_head *new,
                               struct list_head *prev,
                               struct list_head *next) {
    next->prev = new;
    new->next = next;
    new->prev = prev;
    prev->next = new;
}

static inline void list_add(struct list_head *new, struct list_head *head) {
    __list_add(new, head, head->next);  /* insert after head (stack) */
}

static inline void list_add_tail(struct list_head *new, struct list_head *head) {
    __list_add(new, head->prev, head);  /* insert before head (queue) */
}

static inline void list_del(struct list_head *entry) {
    entry->prev->next = entry->next;
    entry->next->prev = entry->prev;
    entry->next = (void *)0xDEADBEEF;  /* poison for debugging */
    entry->prev = (void *)0xDEADBEEF;
}

static inline int list_empty(const struct list_head *head) {
    return head->next == head;
}

#define list_entry(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

#define list_for_each_entry(pos, head, member) \
    for (pos = list_entry((head)->next, typeof(*pos), member); \
         &pos->member != (head); \
         pos = list_entry(pos->member.next, typeof(*pos), member))

/* Example usage */
struct process {
    int pid;
    char name[16];
    struct list_head list;  /* embedded list node */
};

int main(void) {
    LIST_HEAD(process_list);
    
    struct process p1 = { .pid = 1, .name = "init" };
    struct process p2 = { .pid = 2, .name = "kthreadd" };
    struct process p3 = { .pid = 3, .name = "bash" };
    INIT_LIST_HEAD(&p1.list);
    INIT_LIST_HEAD(&p2.list);
    INIT_LIST_HEAD(&p3.list);
    
    list_add_tail(&p1.list, &process_list);
    list_add_tail(&p2.list, &process_list);
    list_add_tail(&p3.list, &process_list);
    
    struct process *proc;
    list_for_each_entry(proc, &process_list, list) {
        printf("PID %d: %s\n", proc->pid, proc->name);
    }
    return 0;
}
```

**Go (intrusive-style via interface):**
```go
package intrusive

import "fmt"

// In Go we use embedding to approximate intrusive lists
type ListHead struct {
    Next, Prev *ListHead
}

func (h *ListHead) Init() {
    h.Next = h
    h.Prev = h
}

func (h *ListHead) IsEmpty() bool {
    return h.Next == h
}

func (h *ListHead) AddTail(entry *ListHead) {
    entry.Next = h
    entry.Prev = h.Prev
    h.Prev.Next = entry
    h.Prev = entry
}

func (h *ListHead) Del(entry *ListHead) {
    entry.Prev.Next = entry.Next
    entry.Next.Prev = entry.Prev
    entry.Next = nil
    entry.Prev = nil
}

// Usage: embed ListHead in your struct
type Process struct {
    PID  int
    Name string
    List ListHead
}

func Example() {
    head := &ListHead{}
    head.Init()
    
    p1 := &Process{PID: 1, Name: "init"}
    p2 := &Process{PID: 2, Name: "kthreadd"}
    p1.List.Init()
    p2.List.Init()
    
    head.AddTail(&p1.List)
    head.AddTail(&p2.List)
    
    // Traverse — Go doesn't have container_of, use pointer arithmetic via unsafe or redesign
    cur := head.Next
    for cur != head {
        // In real Go, we'd use a different approach: store the outer struct pointer in the node
        cur = cur.Next
    }
    _ = fmt.Sprintf // suppress unused
}
```

**Rust (intrusive list with Pin):**
```rust
use std::pin::Pin;
use std::ptr::NonNull;
use std::marker::PhantomPinned;

/// Intrusive linked list node.
/// Must be pinned — moving it would invalidate pointers.
pub struct ListHead {
    next: *mut ListHead,
    prev: *mut ListHead,
    _pin: PhantomPinned,
}

impl ListHead {
    pub fn new() -> Self {
        ListHead {
            next: std::ptr::null_mut(),
            prev: std::ptr::null_mut(),
            _pin: PhantomPinned,
        }
    }
    
    /// Initialize as an empty list head (sentinel node).
    pub fn init(self: Pin<&mut Self>) {
        let ptr = unsafe { self.get_unchecked_mut() as *mut ListHead };
        unsafe {
            (*ptr).next = ptr;
            (*ptr).prev = ptr;
        }
    }
    
    pub fn is_empty(self: Pin<&Self>) -> bool {
        let ptr = &*self as *const ListHead as *mut ListHead;
        unsafe { (*ptr).next == ptr }
    }
    
    /// Add `entry` before `self` (at tail of list headed by sentinel)
    pub unsafe fn add_tail(head: *mut ListHead, entry: *mut ListHead) {
        let prev = (*head).prev;
        (*entry).next = head;
        (*entry).prev = prev;
        (*prev).next = entry;
        (*head).prev = entry;
    }
    
    pub unsafe fn del(entry: *mut ListHead) {
        (*(*entry).prev).next = (*entry).next;
        (*(*entry).next).prev = (*entry).prev;
        (*entry).next = 0xDEAD_BEEF as *mut ListHead;
        (*entry).prev = 0xDEAD_BEEF as *mut ListHead;
    }
}
```

## 5.2 Red-Black Trees — `rb_root` and `rb_node`

The kernel uses red-black trees extensively:
- CFS scheduler runqueue (keyed by vruntime)
- Virtual Memory Areas (keyed by start address)
- epoll event set (keyed by file descriptor)
- Timer wheel (for rb-tree based timers)

```c
/* In <linux/rbtree.h> */
struct rb_node {
    unsigned long  __rb_parent_color;  /* parent pointer + color in low bits! */
    struct rb_node *rb_right;
    struct rb_node *rb_left;
};

struct rb_root {
    struct rb_node *rb_node;
};

/* Color stored in bit 0 of parent pointer (pointer is always aligned) */
#define RB_RED   0
#define RB_BLACK 1
#define rb_color(rb)      ((rb)->__rb_parent_color & 1)
#define rb_is_black(rb)   (rb_color(rb))
#define rb_parent(rb)     ((struct rb_node *)((rb)->__rb_parent_color & ~3UL))
```

**Packing color into pointer:** Since all pointers are at minimum 4-byte aligned, the lowest 2 bits of a pointer are always 0. The kernel stores the color in bit 0. This saves 4-8 bytes per node in cache-critical structures.

### Red-Black Tree — Full C Implementation

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef enum { RED = 0, BLACK = 1 } Color;

typedef struct RBNode {
    int key;
    int val;
    struct RBNode *parent, *left, *right;
    Color color;
} RBNode;

typedef struct {
    RBNode *root;
    RBNode *nil;  /* sentinel NIL node (black) */
} RBTree;

RBTree *rb_create(void) {
    RBTree *t = malloc(sizeof(RBTree));
    t->nil = calloc(1, sizeof(RBNode));
    t->nil->color = BLACK;
    t->nil->left = t->nil->right = t->nil->parent = t->nil;
    t->root = t->nil;
    return t;
}

static void rotate_left(RBTree *t, RBNode *x) {
    RBNode *y = x->right;
    x->right = y->left;
    if (y->left != t->nil) y->left->parent = x;
    y->parent = x->parent;
    if (x->parent == t->nil) t->root = y;
    else if (x == x->parent->left) x->parent->left = y;
    else x->parent->right = y;
    y->left = x;
    x->parent = y;
}

static void rotate_right(RBTree *t, RBNode *x) {
    RBNode *y = x->left;
    x->left = y->right;
    if (y->right != t->nil) y->right->parent = x;
    y->parent = x->parent;
    if (x->parent == t->nil) t->root = y;
    else if (x == x->parent->right) x->parent->right = y;
    else x->parent->left = y;
    y->right = x;
    x->parent = y;
}

static void insert_fixup(RBTree *t, RBNode *z) {
    while (z->parent->color == RED) {
        if (z->parent == z->parent->parent->left) {
            RBNode *y = z->parent->parent->right;  /* uncle */
            if (y->color == RED) {
                /* Case 1: uncle is red → recolor */
                z->parent->color = BLACK;
                y->color = BLACK;
                z->parent->parent->color = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->right) {
                    /* Case 2: uncle black, z is right child → rotate */
                    z = z->parent;
                    rotate_left(t, z);
                }
                /* Case 3: uncle black, z is left child → recolor + rotate */
                z->parent->color = BLACK;
                z->parent->parent->color = RED;
                rotate_right(t, z->parent->parent);
            }
        } else {
            /* Mirror of above */
            RBNode *y = z->parent->parent->left;
            if (y->color == RED) {
                z->parent->color = BLACK;
                y->color = BLACK;
                z->parent->parent->color = RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->left) {
                    z = z->parent;
                    rotate_right(t, z);
                }
                z->parent->color = BLACK;
                z->parent->parent->color = RED;
                rotate_left(t, z->parent->parent);
            }
        }
    }
    t->root->color = BLACK;
}

RBNode *rb_insert(RBTree *t, int key, int val) {
    RBNode *z = malloc(sizeof(RBNode));
    z->key = key;
    z->val = val;
    z->left = z->right = z->parent = t->nil;
    z->color = RED;
    
    RBNode *y = t->nil;
    RBNode *x = t->root;
    
    while (x != t->nil) {
        y = x;
        if (z->key < x->key) x = x->left;
        else if (z->key > x->key) x = x->right;
        else { x->val = val; free(z); return x; }  /* update */
    }
    
    z->parent = y;
    if (y == t->nil) t->root = z;
    else if (z->key < y->key) y->left = z;
    else y->right = z;
    
    insert_fixup(t, z);
    return z;
}

RBNode *rb_search(RBTree *t, int key) {
    RBNode *x = t->root;
    while (x != t->nil) {
        if (key == x->key) return x;
        x = (key < x->key) ? x->left : x->right;
    }
    return NULL;
}

/* In-order traversal to verify BST property */
void rb_inorder(RBTree *t, RBNode *x) {
    if (x == t->nil) return;
    rb_inorder(t, x->left);
    printf("[%d(%s)] ", x->key, x->color == RED ? "R" : "B");
    rb_inorder(t, x->right);
}
```

### Red-Black Tree — Rust Implementation

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy, PartialEq)]
enum Color { Red, Black }

#[derive(Debug)]
struct Node<K: Ord, V> {
    key:   K,
    val:   V,
    color: Color,
    left:  Tree<K, V>,
    right: Tree<K, V>,
}

type Tree<K, V> = Option<Box<Node<K, V>>>;

fn color_of<K: Ord, V>(t: &Tree<K, V>) -> Color {
    t.as_ref().map_or(Color::Black, |n| n.color)
}

fn rotate_left<K: Ord, V>(mut h: Box<Node<K, V>>) -> Box<Node<K, V>> {
    let mut x = h.right.take().expect("rotate_left: no right child");
    h.right = x.left.take();
    x.color = h.color;
    h.color = Color::Red;
    x.left = Some(h);
    x
}

fn rotate_right<K: Ord, V>(mut h: Box<Node<K, V>>) -> Box<Node<K, V>> {
    let mut x = h.left.take().expect("rotate_right: no left child");
    h.left = x.right.take();
    x.color = h.color;
    h.color = Color::Red;
    x.right = Some(h);
    x
}

fn flip_colors<K: Ord, V>(h: &mut Box<Node<K, V>>) {
    h.color = if h.color == Color::Red { Color::Black } else { Color::Red };
    if let Some(ref mut l) = h.left {
        l.color = if l.color == Color::Red { Color::Black } else { Color::Red };
    }
    if let Some(ref mut r) = h.right {
        r.color = if r.color == Color::Red { Color::Black } else { Color::Red };
    }
}

/// Left-Leaning Red-Black Tree (Sedgewick's LLRB — simpler than standard RB)
pub struct LLRB<K: Ord, V> {
    root: Tree<K, V>,
    size: usize,
}

impl<K: Ord, V> LLRB<K, V> {
    pub fn new() -> Self { LLRB { root: None, size: 0 } }
    
    pub fn insert(&mut self, key: K, val: V) {
        self.root = Self::insert_node(self.root.take(), key, val, &mut self.size);
        if let Some(ref mut r) = self.root {
            r.color = Color::Black;
        }
    }
    
    fn insert_node(tree: Tree<K, V>, key: K, val: V, size: &mut usize) -> Tree<K, V> {
        let mut h = match tree {
            None => {
                *size += 1;
                return Some(Box::new(Node {
                    key, val,
                    color: Color::Red,
                    left: None, right: None,
                }));
            }
            Some(h) => h,
        };
        
        match key.cmp(&h.key) {
            Ordering::Less => h.left = Self::insert_node(h.left.take(), key, val, size),
            Ordering::Greater => h.right = Self::insert_node(h.right.take(), key, val, size),
            Ordering::Equal => h.val = val,
        }
        
        // Fix-up: maintain left-leaning invariant
        if color_of(&h.right) == Color::Red && color_of(&h.left) != Color::Red {
            h = rotate_left(h);
        }
        if color_of(&h.left) == Color::Red {
            if let Some(ref ll) = h.left {
                if color_of(&ll.left) == Color::Red {
                    h = rotate_right(h);
                }
            }
        }
        if color_of(&h.left) == Color::Red && color_of(&h.right) == Color::Red {
            flip_colors(&mut h);
        }
        
        Some(h)
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let mut cur = &self.root;
        while let Some(ref node) = cur {
            match key.cmp(&node.key) {
                Ordering::Equal   => return Some(&node.val),
                Ordering::Less    => cur = &node.left,
                Ordering::Greater => cur = &node.right,
            }
        }
        None
    }
    
    pub fn len(&self) -> usize { self.size }
}
```

## 5.3 Hash Tables — `htable` and `hlist`

The kernel uses separate chaining hash tables with a twist: the bucket heads are `hlist_head` (single pointer), while nodes are `hlist_node` (double pointer but the prev points to the `next` field, not the node itself). This saves memory in buckets.

```c
/* Compact hash list — saves 1 pointer per bucket vs list_head */
struct hlist_head {
    struct hlist_node *first;
};

struct hlist_node {
    struct hlist_node *next;
    struct hlist_node **pprev;  /* pointer to previous node's 'next' field */
};
```

**Why `**pprev`?** 
With `**pprev`, deleting a node doesn't require knowing the bucket head. You just do `*node->pprev = node->next`. This is a classic **pointer-to-pointer** technique for linked list manipulation.

### Generic Hash Table — C Implementation

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define HASH_BITS   8
#define HASH_SIZE   (1 << HASH_BITS)   /* 256 buckets */
#define HASH_MASK   (HASH_SIZE - 1)

typedef struct hlist_node {
    struct hlist_node *next;
    struct hlist_node **pprev;
} hlist_node;

typedef struct { hlist_node *first; } hlist_head;

static void hlist_add_head(hlist_node *n, hlist_head *h) {
    if (h->first) h->first->pprev = &n->next;
    n->next = h->first;
    n->pprev = &h->first;
    h->first = n;
}

static void hlist_del(hlist_node *n) {
    *n->pprev = n->next;
    if (n->next) n->next->pprev = n->pprev;
}

/* FNV-1a hash for strings */
static uint32_t fnv1a(const char *key) {
    uint32_t h = 2166136261u;
    while (*key) {
        h ^= (uint8_t)*key++;
        h *= 16777619u;
    }
    return h & HASH_MASK;
}

typedef struct kv_entry {
    char *key;
    int   val;
    hlist_node node;
} kv_entry;

typedef struct {
    hlist_head buckets[HASH_SIZE];
    size_t     count;
} HashMap;

void hmap_insert(HashMap *m, const char *key, int val) {
    uint32_t h = fnv1a(key);
    
    /* Check for existing key */
    hlist_node *pos = m->buckets[h].first;
    while (pos) {
        kv_entry *e = (kv_entry *)((char*)pos - offsetof(kv_entry, node));
        if (strcmp(e->key, key) == 0) { e->val = val; return; }
        pos = pos->next;
    }
    
    kv_entry *e = malloc(sizeof(kv_entry));
    e->key = strdup(key);
    e->val = val;
    hlist_add_head(&e->node, &m->buckets[h]);
    m->count++;
}

int *hmap_get(HashMap *m, const char *key) {
    uint32_t h = fnv1a(key);
    hlist_node *pos = m->buckets[h].first;
    while (pos) {
        kv_entry *e = (kv_entry *)((char*)pos - offsetof(kv_entry, node));
        if (strcmp(e->key, key) == 0) return &e->val;
        pos = pos->next;
    }
    return NULL;
}

void hmap_delete(HashMap *m, const char *key) {
    uint32_t h = fnv1a(key);
    hlist_node *pos = m->buckets[h].first;
    while (pos) {
        kv_entry *e = (kv_entry *)((char*)pos - offsetof(kv_entry, node));
        if (strcmp(e->key, key) == 0) {
            hlist_del(pos);
            free(e->key);
            free(e);
            m->count--;
            return;
        }
        pos = pos->next;
    }
}
```

### Hash Table — Rust Implementation with Robin Hood Hashing

```rust
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

/// Robin Hood Open-Addressing Hash Map
/// Minimizes probe length variance by "stealing" from rich probes
pub struct RobinHoodMap<K: Hash + Eq + Clone, V: Clone> {
    buckets: Vec<Option<(K, V, usize)>>,  // (key, val, probe_distance)
    count:   usize,
    cap:     usize,
}

impl<K: Hash + Eq + Clone, V: Clone> RobinHoodMap<K, V> {
    pub fn new() -> Self {
        let cap = 16;
        RobinHoodMap {
            buckets: vec![None; cap],
            count: 0,
            cap,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut h = DefaultHasher::new();
        key.hash(&mut h);
        h.finish() as usize % self.cap
    }
    
    pub fn insert(&mut self, mut key: K, mut val: V) {
        if self.count * 4 >= self.cap * 3 {
            self.resize();  // load factor > 0.75
        }
        
        let mut pos = self.hash(&key);
        let mut dist = 0usize;
        
        loop {
            match &self.buckets[pos] {
                None => {
                    self.buckets[pos] = Some((key, val, dist));
                    self.count += 1;
                    return;
                }
                Some((k, _, _)) if k == &key => {
                    // Update existing
                    if let Some((_, v, _)) = &mut self.buckets[pos] {
                        *v = val;
                    }
                    return;
                }
                Some((_, _, existing_dist)) => {
                    // Robin Hood: steal from rich (longer probe) for poor (shorter probe)
                    if *existing_dist < dist {
                        // Swap our entry with existing, continue inserting displaced
                        if let Some((ek, ev, ed)) = self.buckets[pos].replace((key, val, dist)) {
                            key = ek;
                            val = ev;
                            dist = ed;
                        }
                    }
                }
            }
            pos = (pos + 1) % self.cap;
            dist += 1;
        }
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let mut pos = self.hash(key);
        let mut dist = 0;
        
        loop {
            match &self.buckets[pos] {
                None => return None,
                Some((_, _, d)) if *d < dist => return None,  // early termination!
                Some((k, v, _)) if k == key => return Some(v),
                _ => {}
            }
            pos = (pos + 1) % self.cap;
            dist += 1;
        }
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(
            &mut self.buckets,
            vec![None; self.cap * 2]
        );
        self.cap *= 2;
        self.count = 0;
        
        for bucket in old_buckets.into_iter().flatten() {
            self.insert(bucket.0, bucket.1);
        }
    }
}
```

## 5.4 Radix Trees / XArrays — `xarray`

The Linux kernel replaced radix trees with **XArray** (since 4.20). Used for:
- Page cache (mapping file offsets to pages)
- Process ID lookup (PID → task_struct)
- epoll file descriptor management

```c
struct xa_node {
    unsigned char shift;   /* Bits remaining in each slot */
    unsigned char offset;  /* Slot used in parent */
    unsigned char count;   /* Total entry count */
    unsigned char nr_values; /* Value entry count */
    struct xa_node *parent;
    struct xarray  *array;
    union {
        struct list_head private_list;
        struct rcu_head rcu_head;
    };
    void *slots[XA_CHUNK_SIZE];  /* 64 slots per node */
};
```

A radix tree on 64 slots (6 bits per level) needs only `ceil(64/6) = 11` levels for a 64-bit key. Each lookup is at most 11 pointer dereferences.

**XArray brilliance:** Stores small integers directly as `xa_mk_value(n)` — tagging the lowest bit to distinguish values from pointers. No allocation needed for small values!

## 5.5 Priority Queues — Kernel Timers

The kernel uses multiple timer mechanisms:
1. **Timer wheel** (`struct timer_list`) — O(1) coarse timers
2. **High-resolution timers** (`struct hrtimer`) — nanosecond red-black tree
3. **timerfd** — userspace timer via file descriptor

**Timer wheel algorithm:**
```
256 slots per level, 9 bits per slot, 5 levels:
Level 0: 0-255 jiffies       (immediate)
Level 1: 256-16383 jiffies   (near future)
Level 2: 16384-1048575 jiffies
Level 3: 1048576-67108863 jiffies
Level 4: 67108864+ jiffies   (far future)
```

On each timer tick, the slot pointer advances. When a slot index wraps around, the next level's slot is "cascaded" down. This gives O(1) insertion and O(n) only when cascading (amortized O(1) for typical workloads).

### Priority Queue — Rust (Binary Heap for Timer Simulation)

```rust
use std::cmp::Reverse;
use std::collections::BinaryHeap;

#[derive(Debug, Eq, PartialEq)]
struct Timer {
    expires_ns: u64,   // expiry in nanoseconds
    id:         u64,
    callback:   String,  // in real kernel: function pointer
}

impl Ord for Timer {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // Earlier expiry = higher priority
        other.expires_ns.cmp(&self.expires_ns)
            .then(self.id.cmp(&other.id))
    }
}
impl PartialOrd for Timer {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

pub struct HRTimerQueue {
    heap:       BinaryHeap<Timer>,
    now_ns:     u64,
    next_id:    u64,
}

impl HRTimerQueue {
    pub fn new() -> Self {
        HRTimerQueue { heap: BinaryHeap::new(), now_ns: 0, next_id: 0 }
    }
    
    pub fn add_timer(&mut self, delay_ns: u64, callback: &str) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        self.heap.push(Timer {
            expires_ns: self.now_ns + delay_ns,
            id,
            callback: callback.to_string(),
        });
        id
    }
    
    /// Advance time by `delta_ns`, firing all expired timers.
    pub fn advance(&mut self, delta_ns: u64) -> Vec<String> {
        self.now_ns += delta_ns;
        let mut fired = Vec::new();
        
        while let Some(timer) = self.heap.peek() {
            if timer.expires_ns <= self.now_ns {
                let t = self.heap.pop().unwrap();
                fired.push(t.callback);
            } else {
                break;
            }
        }
        fired
    }
    
    pub fn next_expiry(&self) -> Option<u64> {
        self.heap.peek().map(|t| t.expires_ns)
    }
}
```

## 5.6 Bitmaps — `find_next_bit` and CPU Masks

Bitmaps are fundamental to the kernel for tracking sets of items with fixed maximum size:
- CPU affinity masks (`cpumask_t` — one bit per CPU)
- IRQ affinity
- Memory zone page tracking
- Inode dirty tracking

```c
/* Architecture-optimized bit operations */
#include <asm/bitops.h>

/* Find first set bit — uses BSF instruction on x86 */
unsigned long __ffs(unsigned long word);

/* Find next set bit in bitmap */
unsigned long find_next_bit(const unsigned long *addr, 
                             unsigned long size,
                             unsigned long offset);

/* Atomic bit operations */
void set_bit(int nr, volatile unsigned long *addr);
void clear_bit(int nr, volatile unsigned long *addr);
int  test_and_set_bit(int nr, volatile unsigned long *addr);
```

**CPU masks:**
```c
/* cpumask — one bit per possible CPU */
typedef struct cpumask { DECLARE_BITMAP(bits, NR_CPUS); } cpumask_t;

cpumask_t online = cpu_online_mask;  /* CPUs currently online */
for_each_cpu(cpu, &online) {
    /* do something per-CPU */
}
```

### Bitmap — Rust Implementation

```rust
pub struct Bitmap {
    words: Vec<u64>,
    size:  usize,
}

impl Bitmap {
    pub fn new(size: usize) -> Self {
        let words = (size + 63) / 64;
        Bitmap { words: vec![0u64; words], size }
    }
    
    pub fn set(&mut self, n: usize) {
        assert!(n < self.size);
        self.words[n / 64] |= 1u64 << (n % 64);
    }
    
    pub fn clear(&mut self, n: usize) {
        assert!(n < self.size);
        self.words[n / 64] &= !(1u64 << (n % 64));
    }
    
    pub fn test(&self, n: usize) -> bool {
        assert!(n < self.size);
        (self.words[n / 64] >> (n % 64)) & 1 == 1
    }
    
    pub fn test_and_set(&mut self, n: usize) -> bool {
        let was_set = self.test(n);
        self.set(n);
        was_set
    }
    
    /// Find first set bit (like Linux's find_first_bit)
    pub fn find_first_set(&self) -> Option<usize> {
        for (i, &w) in self.words.iter().enumerate() {
            if w != 0 {
                let bit = w.trailing_zeros() as usize;
                let pos = i * 64 + bit;
                if pos < self.size { return Some(pos); }
            }
        }
        None
    }
    
    /// Find next set bit >= start (like Linux's find_next_bit)
    pub fn find_next_set(&self, start: usize) -> Option<usize> {
        if start >= self.size { return None; }
        
        let word_idx = start / 64;
        let bit_idx  = start % 64;
        
        // Check partial first word
        let first_word = self.words[word_idx] >> bit_idx;
        if first_word != 0 {
            let pos = word_idx * 64 + bit_idx + first_word.trailing_zeros() as usize;
            if pos < self.size { return Some(pos); }
        }
        
        // Check remaining words
        for i in (word_idx + 1)..self.words.len() {
            if self.words[i] != 0 {
                let pos = i * 64 + self.words[i].trailing_zeros() as usize;
                if pos < self.size { return Some(pos); }
            }
        }
        None
    }
    
    /// Population count — number of set bits
    pub fn popcount(&self) -> usize {
        self.words.iter().map(|w| w.count_ones() as usize).sum()
    }
    
    pub fn and(&self, other: &Bitmap) -> Bitmap {
        assert_eq!(self.size, other.size);
        Bitmap {
            words: self.words.iter().zip(&other.words).map(|(a, b)| a & b).collect(),
            size: self.size,
        }
    }
    
    pub fn or(&self, other: &Bitmap) -> Bitmap {
        assert_eq!(self.size, other.size);
        Bitmap {
            words: self.words.iter().zip(&other.words).map(|(a, b)| a | b).collect(),
            size: self.size,
        }
    }
}

impl std::fmt::Display for Bitmap {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        for i in 0..self.size {
            write!(f, "{}", if self.test(i) { '1' } else { '0' })?;
            if i % 8 == 7 { write!(f, " ")?; }
        }
        Ok(())
    }
}
```

---

# 6. Algorithms Inside the Linux Kernel

## 6.1 Sorting — `lib/sort.c`

The kernel implements a custom heapsort (not introsort) because:
- Heapsort is O(n log n) worst case — no pathological inputs (unlike quicksort)
- No stack usage proportional to input (unlike recursive quicksort)
- Kernel stack is limited (4-16 KB) — stack overflow is catastrophic

```c
/* kernel/lib/sort.c */
void sort(void *base, size_t num, size_t size,
          int (*cmp)(const void *, const void *, const void *),
          void (*swap)(void *, void *, int));
```

**Kernel heapsort key insight:** Uses an iterative (not recursive) sift-down, avoiding stack growth.

### Heapsort — C Implementation (Kernel Style)

```c
#include <stddef.h>
#include <string.h>

static void swap_bytes(void *a, void *b, size_t size) {
    char tmp[256];
    memcpy(tmp, a, size);
    memcpy(a, b, size);
    memcpy(b, tmp, size);
}

static void sift_down(void *base, size_t root, size_t n, size_t size,
                       int (*cmp)(const void *, const void *)) {
    while (1) {
        size_t largest = root;
        size_t left    = 2 * root + 1;
        size_t right   = 2 * root + 2;
        
        char *arr = (char *)base;
        
        if (left < n && cmp(arr + left * size, arr + largest * size) > 0)
            largest = left;
        if (right < n && cmp(arr + right * size, arr + largest * size) > 0)
            largest = right;
        
        if (largest == root) break;
        
        swap_bytes(arr + root * size, arr + largest * size, size);
        root = largest;
    }
}

void heapsort(void *base, size_t n, size_t size,
              int (*cmp)(const void *, const void *)) {
    char *arr = (char *)base;
    
    /* Build max-heap: heapify from last internal node to root */
    if (n <= 1) return;
    for (size_t i = n / 2; i-- > 0; )
        sift_down(arr, i, n, size, cmp);
    
    /* Extract max elements one by one */
    for (size_t i = n - 1; i > 0; i--) {
        swap_bytes(arr, arr + i * size, size);  /* move max to end */
        sift_down(arr, 0, i, size, cmp);        /* restore heap property */
    }
}

/* Example comparator */
static int int_cmp(const void *a, const void *b) {
    return *(int *)a - *(int *)b;
}
```

### Heapsort — Rust

```rust
pub fn heapsort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    if n <= 1 { return; }
    
    // Build max-heap
    for i in (0..n / 2).rev() {
        sift_down(arr, i, n);
    }
    
    // Extract elements
    for end in (1..n).rev() {
        arr.swap(0, end);
        sift_down(arr, 0, end);
    }
}

fn sift_down<T: Ord>(arr: &mut [T], mut root: usize, n: usize) {
    loop {
        let mut largest = root;
        let left  = 2 * root + 1;
        let right = 2 * root + 2;
        
        if left  < n && arr[left]  > arr[largest] { largest = left;  }
        if right < n && arr[right] > arr[largest] { largest = right; }
        
        if largest == root { break; }
        arr.swap(root, largest);
        root = largest;
    }
}

/// Introsort: quicksort + heapsort fallback + insertion sort for small slices
pub fn introsort<T: Ord>(arr: &mut [T]) {
    let max_depth = 2 * (arr.len() as f64).log2() as usize;
    introsort_inner(arr, max_depth);
}

fn introsort_inner<T: Ord>(arr: &mut [T], depth_limit: usize) {
    const THRESHOLD: usize = 16;
    
    if arr.len() <= THRESHOLD {
        insertion_sort(arr);
        return;
    }
    
    if depth_limit == 0 {
        heapsort(arr);
        return;
    }
    
    let pivot = partition(arr);
    introsort_inner(&mut arr[..pivot], depth_limit - 1);
    introsort_inner(&mut arr[pivot + 1..], depth_limit - 1);
}

fn partition<T: Ord>(arr: &mut [T]) -> usize {
    let len = arr.len();
    // Median of three pivot selection
    let mid = len / 2;
    if arr[mid] < arr[0] { arr.swap(0, mid); }
    if arr[len-1] < arr[0] { arr.swap(0, len-1); }
    if arr[mid] < arr[len-1] { arr.swap(mid, len-1); }
    let pivot = len - 1;
    
    let mut i = 0;
    for j in 0..pivot {
        if arr[j] <= arr[pivot] {
            arr.swap(i, j);
            i += 1;
        }
    }
    arr.swap(i, pivot);
    i
}

fn insertion_sort<T: Ord>(arr: &mut [T]) {
    for i in 1..arr.len() {
        let mut j = i;
        while j > 0 && arr[j-1] > arr[j] {
            arr.swap(j-1, j);
            j -= 1;
        }
    }
}
```

## 6.2 String Matching — KMP in the Kernel

The kernel uses string matching in:
- `grep`-like pattern matching in `ftrace` function filters
- `nf_conntrack` for deep packet inspection
- `uevent` matching for device hotplug

### Knuth-Morris-Pratt Algorithm

**Core insight:** When a mismatch occurs at position `j` in the pattern, we don't need to restart from pattern[0]. The **failure function** (partial match table) tells us the longest proper prefix of `pattern[0..j]` that is also a suffix — we restart from there.

```c
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* Build KMP failure function in O(m) */
int *kmp_build_table(const char *pattern, int m) {
    int *fail = malloc(m * sizeof(int));
    fail[0] = 0;
    int k = 0;
    
    for (int i = 1; i < m; i++) {
        while (k > 0 && pattern[k] != pattern[i])
            k = fail[k - 1];
        if (pattern[k] == pattern[i])
            k++;
        fail[i] = k;
    }
    return fail;
}

/* KMP search: find all occurrences of pattern in text — O(n+m) */
void kmp_search(const char *text, int n, const char *pattern, int m) {
    if (m == 0) return;
    int *fail = kmp_build_table(pattern, m);
    
    int k = 0;  /* chars matched so far */
    for (int i = 0; i < n; i++) {
        while (k > 0 && pattern[k] != text[i])
            k = fail[k - 1];  /* partial match — use failure function */
        if (pattern[k] == text[i])
            k++;
        if (k == m) {
            printf("Pattern found at index %d\n", i - m + 1);
            k = fail[k - 1];  /* prepare for next match */
        }
    }
    free(fail);
}
```

### KMP — Rust Implementation

```rust
pub fn kmp_failure_function(pattern: &[u8]) -> Vec<usize> {
    let m = pattern.len();
    let mut fail = vec![0usize; m];
    let mut k = 0usize;
    
    for i in 1..m {
        while k > 0 && pattern[k] != pattern[i] {
            k = fail[k - 1];
        }
        if pattern[k] == pattern[i] { k += 1; }
        fail[i] = k;
    }
    fail
}

pub fn kmp_search(text: &[u8], pattern: &[u8]) -> Vec<usize> {
    if pattern.is_empty() { return vec![]; }
    let fail = kmp_failure_function(pattern);
    let mut matches = Vec::new();
    let mut k = 0usize;
    
    for (i, &c) in text.iter().enumerate() {
        while k > 0 && pattern[k] != c {
            k = fail[k - 1];
        }
        if pattern[k] == c { k += 1; }
        if k == pattern.len() {
            matches.push(i + 1 - pattern.len());
            k = fail[k - 1];
        }
    }
    matches
}

/// Boyer-Moore-Horspool: faster in practice for long patterns
pub fn bmh_search(text: &[u8], pattern: &[u8]) -> Vec<usize> {
    if pattern.is_empty() || pattern.len() > text.len() { return vec![]; }
    
    let m = pattern.len();
    let n = text.len();
    
    // Bad character skip table
    let mut skip = [m; 256];
    for (i, &c) in pattern[..m-1].iter().enumerate() {
        skip[c as usize] = m - 1 - i;
    }
    
    let mut matches = Vec::new();
    let mut i = m - 1;
    
    while i < n {
        let mut k = m - 1;
        let mut j = i;
        
        while k > 0 && text[j] == pattern[k] {
            j -= 1;
            k -= 1;
        }
        
        if k == 0 && text[j] == pattern[0] {
            matches.push(j);
        }
        
        i += skip[text[i] as usize];
    }
    matches
}
```

## 6.3 CRC and Checksums — Data Integrity in the Kernel

The kernel uses CRC (Cyclic Redundancy Check) for:
- Filesystem integrity (ext4, btrfs use CRC32c)
- Network checksums (TCP/UDP/IP)
- Block device integrity (T10 DIF/DIX)

```c
/* Kernel provides hardware-accelerated CRC32c via SSE4.2 */
#include <linux/crc32.h>

u32 crc32_le(u32 crc, const unsigned char *p, size_t len);
u32 crc32c(u32 crc, const void *address, unsigned int length);
```

### CRC32c — Software Implementation

```c
#include <stdint.h>
#include <stddef.h>

/* CRC32c polynomial: 0x1EDC6F41 (Castagnoli) */
static uint32_t crc32c_table[256];

void crc32c_init_table(void) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t crc = i;
        for (int j = 0; j < 8; j++) {
            if (crc & 1)
                crc = (crc >> 1) ^ 0x82F63B78U;  /* reflected polynomial */
            else
                crc >>= 1;
        }
        crc32c_table[i] = crc;
    }
}

uint32_t crc32c(uint32_t crc, const uint8_t *data, size_t len) {
    crc = ~crc;
    while (len--)
        crc = crc32c_table[(crc ^ *data++) & 0xFF] ^ (crc >> 8);
    return ~crc;
}
```

### CRC32 — Rust (using intrinsics for hardware acceleration)

```rust
/// Software CRC32c (Castagnoli polynomial)
pub struct Crc32c {
    table: [u32; 256],
}

impl Crc32c {
    pub fn new() -> Self {
        let mut table = [0u32; 256];
        for i in 0u32..256 {
            let mut crc = i;
            for _ in 0..8 {
                crc = if crc & 1 != 0 {
                    (crc >> 1) ^ 0x82F6_3B78
                } else {
                    crc >> 1
                };
            }
            table[i as usize] = crc;
        }
        Crc32c { table }
    }
    
    pub fn update(&self, mut crc: u32, data: &[u8]) -> u32 {
        crc = !crc;
        for &byte in data {
            let idx = ((crc ^ byte as u32) & 0xFF) as usize;
            crc = self.table[idx] ^ (crc >> 8);
        }
        !crc
    }
    
    pub fn checksum(&self, data: &[u8]) -> u32 {
        self.update(0, data)
    }
}

/// Architecture-optimized CRC32c using x86 SSE4.2 CRC32 instruction
#[cfg(target_arch = "x86_64")]
pub fn crc32c_hw(data: &[u8]) -> u32 {
    use std::arch::x86_64::_mm_crc32_u64;
    
    let mut crc: u64 = !0u64;
    let (prefix, aligned, suffix) = unsafe { data.align_to::<u64>() };
    
    // Handle unaligned prefix
    for &byte in prefix {
        crc = unsafe { _mm_crc32_u64(crc, byte as u64) };
    }
    
    // Process 8 bytes at a time
    for &chunk in aligned {
        crc = unsafe { _mm_crc32_u64(crc, chunk) };
    }
    
    // Handle suffix
    for &byte in suffix {
        crc = unsafe { _mm_crc32_u64(crc, byte as u64) };
    }
    
    !crc as u32
}
```

---

# 7. File Systems & VFS Layer

## 7.1 Virtual File System (VFS) — The Abstraction Layer

The VFS allows different filesystems (ext4, btrfs, XFS, NFS, tmpfs, procfs) to be accessed through a uniform interface. When a process calls `read()`, it knows nothing about the underlying filesystem — VFS routes the call to the correct implementation.

### Core VFS Objects

```c
/* 1. superblock — filesystem instance metadata */
struct super_block {
    dev_t           s_dev;           /* device identifier */
    unsigned long   s_blocksize;
    unsigned long   s_flags;
    unsigned long   s_magic;         /* filesystem magic number */
    struct dentry   *s_root;         /* root dentry */
    struct file_system_type *s_type;
    const struct super_operations *s_op;
    unsigned long   s_time_gran;     /* timestamp granularity */
    struct list_head s_inodes;       /* all inodes in this FS */
    struct hlist_bl_head s_roots;
    /* ... */
};

/* 2. inode — file metadata (not name, not data) */
struct inode {
    umode_t         i_mode;      /* file type + permissions */
    kuid_t          i_uid;
    kgid_t          i_gid;
    unsigned int    i_flags;
    loff_t          i_size;      /* file size in bytes */
    struct timespec64 i_atime, i_mtime, i_ctime;
    unsigned long   i_ino;       /* inode number (unique within FS) */
    nlink_t         i_nlink;     /* hard link count */
    dev_t           i_rdev;      /* for device files */
    
    const struct inode_operations *i_op;  /* mkdir, create, link, etc. */
    const struct file_operations  *i_fop; /* read, write, ioctl, etc. */
    struct address_space *i_mapping;      /* page cache */
    
    /* LRU for inode cache */
    struct list_head i_lru;
    struct list_head i_sb_list;
    
    atomic_t i_count;    /* reference count */
};

/* 3. dentry — directory entry (name → inode mapping) */
struct dentry {
    unsigned int d_flags;
    seqcount_spinlock_t d_seq;
    struct hlist_bl_node d_hash;   /* lookup hash table */
    
    struct dentry *d_parent;
    struct qstr d_name;            /* quick string: hash + len + name */
    
    struct inode *d_inode;         /* NULL for negative dentry */
    
    const struct dentry_operations *d_op;
    struct super_block *d_sb;
    
    struct list_head d_child;      /* child of d_parent */
    struct list_head d_subdirs;    /* children of this dir */
    
    /* LRU for dcache */
    struct list_head d_lru;
    unsigned char d_iname[DNAME_INLINE_LEN]; /* short names inline */
};

/* 4. file — open file instance (per open() call) */
struct file {
    struct path f_path;            /* dentry + mount */
    struct inode *f_inode;
    const struct file_operations *f_op;
    
    spinlock_t f_lock;
    atomic_long_t f_count;        /* reference count */
    unsigned int f_flags;          /* O_RDONLY, O_NONBLOCK, etc. */
    fmode_t f_mode;
    loff_t f_pos;                  /* current file position */
    struct fown_struct f_owner;
    
    /* For async I/O */
    struct kiocb *f_kiocb;
};
```

### The Dentry Cache (dcache)

Path lookup (`/home/user/file.txt`) requires traversing the directory hierarchy. The dcache caches these lookups:

```
Path: /home/user/file.txt

dcache lookup sequence:
1. hash("/") → find root dentry
2. hash("home") in root → find "home" dentry
3. hash("user") in "home" → find "user" dentry  
4. hash("file.txt") in "user" → find "file.txt" dentry
   → dentry->d_inode → inode
```

Each lookup is a hash table probe. On cache hit: O(1). On miss: disk I/O to read directory contents.

**Negative dentries:** If `open("/nonexistent")` fails, the kernel caches a "negative" dentry (d_inode = NULL). Subsequent opens of the same nonexistent path hit the dcache and return ENOENT without disk I/O.

## 7.2 Ext4 — On-Disk Layout

Understanding ext4 reveals how abstract filesystem concepts map to disk structures:

```
Disk Layout (ext4):

Boot Sector (1 block) | Superblock | Block Group 0 | Block Group 1 | ...

Block Group Structure:
┌─────────────┬────────────┬─────────────┬───────────────┬──────────────┐
│ Superblock  │ Group Desc │ Block Bitmap│ Inode Bitmap  │ Inode Table  │
│ (backup)    │ Table      │             │               │              │
├─────────────┴────────────┴─────────────┴───────────────┴──────────────┤
│                        Data Blocks                                     │
└───────────────────────────────────────────────────────────────────────┘
```

**Inode structure (ext4):**
```c
struct ext4_inode {
    __le16 i_mode;        /* file type + permissions */
    __le16 i_uid;         /* owner UID (low 16 bits) */
    __le32 i_size_lo;     /* file size (low 32 bits) */
    __le32 i_atime;
    __le32 i_ctime;
    __le32 i_mtime;
    __le32 i_dtime;       /* deletion time */
    __le16 i_gid;
    __le16 i_links_count;
    __le32 i_blocks_lo;   /* 512-byte block count */
    __le32 i_flags;       /* EXT4_EXTENTS_FL, EXT4_INLINE_DATA_FL... */
    
    /* Block map: either inline data, extent tree, or direct/indirect blocks */
    union {
        struct ext4_extent_header i_eh;  /* extent tree */
        __le32 i_block[EXT4_N_BLOCKS];  /* legacy block map */
        char   i_data[60];               /* inline data (tiny files) */
    } i_block;
    
    __le32 i_generation;  /* file version for NFS */
    __le32 i_file_acl_lo;
    __le32 i_size_high;   /* file size (high 32 bits) */
    __le32 i_obso_faddr;
    /* ... extended attributes, checksums, etc. */
};
```

**Extent tree:** Modern ext4 uses extents (contiguous block ranges) instead of indirect block maps:
```
ext4_extent: { first_logical_block, physical_start, length }
```

A single extent can represent up to 128 MB of contiguous data in one structure. This dramatically reduces metadata for large files.

## 7.3 Page Cache — The Filesystem Buffer

The page cache sits between the filesystem and physical memory. Every file read/write goes through it:

```
read() syscall
    │
    ▼
vfs_read() → file->f_op->read_iter()
    │
    ▼
generic_file_read_iter()
    │
    ├─ page_cache_get_page(inode->i_mapping, page_index)
    │       │
    │       ├─ Page in cache? → copy to user buffer (page hit)
    │       │
    │       └─ Page NOT in cache? → allocate page → add to cache
    │              → submit I/O (readpage) → wait for completion
    │              → copy to user buffer (major page fault)
    │
    └─ return bytes read
```

**radix tree (xarray) for page cache:**
```c
struct address_space {
    struct inode    *host;
    struct xarray    i_pages;      /* page index → struct page */
    struct rw_semaphore invalidate_lock;
    gfp_t            gfp_mask;
    atomic_t         i_mmap_writable;
    struct rb_root_cached i_mmap;  /* VMAs mapping this file */
    pgoff_t          writeback_index;
    const struct address_space_operations *a_ops;
    unsigned long    flags;
    errseq_t         wb_err;
    spinlock_t       private_lock;
    struct list_head private_list;
};
```

The `i_pages` XArray maps `pgoff_t` (file page index) to `struct folio *` (the modern page abstraction, since 5.16).

## 7.4 journaling — Write-Ahead Logging

Ext4 uses journaling to ensure filesystem consistency after crashes. This is **write-ahead logging (WAL)** — the same algorithm used in databases.

```
Without journaling:
  1. Write inode
  2. CRASH
  3. Data written but inode not updated → filesystem inconsistency

With journaling (ordered mode):
  1. Write journal descriptor block (intent)
  2. Write metadata to journal
  3. Commit block (journal is complete)
  4. --- CRASH SAFE POINT ---
  5. Write metadata to actual location
  6. Revoke journal entries

On recovery:
  - If commit block present → redo operations from journal
  - If no commit block → journal incomplete → ignore (old state is consistent)
```

**JBD2 (Journal Block Device 2)** — ext4's journaling layer:
```c
/* Transaction lifecycle */
handle = jbd2_journal_start(journal, nblocks);  /* begin transaction */
    jbd2_journal_get_write_access(handle, bh);   /* mark block for modification */
    /* modify buffer_head data */
    jbd2_journal_dirty_metadata(handle, bh);     /* mark as dirty */
jbd2_journal_stop(handle);                       /* end transaction */
```

---

# 8. Networking Stack

## 8.1 The Network Stack Layers

```
Application (userspace)
    │ socket(), send(), recv()
    ▼
Socket Layer (BSD socket interface)
    │ sock->ops->sendmsg()
    ▼
Transport Layer (TCP/UDP)
    │ tcp_sendmsg() / udp_sendmsg()
    ▼
Network Layer (IPv4/IPv6)
    │ ip_output() / ip6_output()
    ▼
Netfilter (iptables/nftables hooks)
    │ NF_HOOK(NFPROTO_IPV4, NF_INET_LOCAL_OUT, ...)
    ▼
Routing (FIB — Forwarding Information Base)
    │ ip_route_output_key()
    ▼
Device Layer (net_device)
    │ dev_queue_xmit()
    ▼
Traffic Control (qdisc — queuing disciplines)
    │ pfifo_fast, fq_codel, HTB, HFSC...
    ▼
Driver (e1000, ixgbe, virtio_net...)
    │ hardware DMA ring
    ▼
Physical Network
```

## 8.2 sk_buff — The Network Packet Data Structure

`struct sk_buff` (socket buffer) is the central data structure of the Linux networking stack. Every packet in flight is represented by one.

```c
struct sk_buff {
    /* Delivery queue */
    struct sk_buff *next, *prev;
    
    /* Packet data layout:
     *  head         data        tail          end
     *   |----headroom----|------data------|---tailroom---|
     */
    unsigned char *head;   /* start of allocated buffer */
    unsigned char *data;   /* start of packet data */
    unsigned char *tail;   /* end of packet data */
    unsigned char *end;    /* end of allocated buffer */
    
    /* Lengths */
    unsigned int    len;       /* total length of this + frags */
    unsigned int    data_len;  /* length in frags (not in linear buffer) */
    __u16           mac_len;   /* MAC header length */
    __u16           hdr_len;   /* (for GSO) header length */
    
    /* Network / transport header pointers */
    union { /* network header */
        struct iphdr  *iph;
        struct ipv6hdr *ipv6h;
        struct arphdr  *arph;
    } network_header;
    
    union { /* transport header */
        struct tcphdr *th;
        struct udphdr *uh;
        struct icmphdr *icmph;
    } transport_header;
    
    /* The socket this skb belongs to */
    struct sock *sk;
    struct net_device *dev;  /* the device this packet arrived on */
    
    /* Timestamps */
    ktime_t tstamp;
    
    /* Checksums and GSO */
    __u16 csum;
    __u8  ip_summed;
    __u8  csum_valid;
    
    /* Reference counting */
    refcount_t users;
    
    /* Fragmented packet support */
    skb_frag_t frags[MAX_SKB_FRAGS];
};
```

**The headroom/tailroom trick:** When a packet traverses layers, each layer prepends its header by moving `skb->data` backward (`skb_push()`). No data copying occurs — just pointer manipulation. This is O(1) header addition regardless of packet size.

```
Start:           [payload]
                  ^data    ^tail

UDP header add:  [UDP|payload]
                  ^data

IP header add:   [IP|UDP|payload]
                  ^data

Ethernet add:    [ETH|IP|UDP|payload]
                  ^data
```

### sk_buff Simulation — Go

```go
package skbuff

import (
    "encoding/binary"
    "errors"
    "fmt"
    "net"
)

const (
    MaxHeadroom  = 256  // space for headers
    MaxTailroom  = 64   // space for trailers/padding
)

type SKBuff struct {
    buf      []byte
    head     int  // start of allocated buffer
    data     int  // start of packet data
    tail     int  // end of packet data
    end      int  // end of allocated buffer
    
    Proto    uint16
    Dev      string
    DataLen  int
}

func NewSKBuff(payloadSize int) *SKBuff {
    total := MaxHeadroom + payloadSize + MaxTailroom
    buf := make([]byte, total)
    
    return &SKBuff{
        buf:  buf,
        head: 0,
        data: MaxHeadroom,
        tail: MaxHeadroom + payloadSize,
        end:  total,
    }
}

func (skb *SKBuff) Len() int  { return skb.tail - skb.data }
func (skb *SKBuff) Data() []byte { return skb.buf[skb.data:skb.tail] }

// Push: add header at front (move data pointer backward)
func (skb *SKBuff) Push(n int) ([]byte, error) {
    if skb.data-n < skb.head {
        return nil, errors.New("skb: no headroom")
    }
    skb.data -= n
    return skb.buf[skb.data : skb.data+n], nil
}

// Pull: remove header from front (move data pointer forward)
func (skb *SKBuff) Pull(n int) ([]byte, error) {
    if skb.data+n > skb.tail {
        return nil, errors.New("skb: buffer underflow")
    }
    hdr := skb.buf[skb.data : skb.data+n]
    skb.data += n
    return hdr, nil
}

// Put: add data at end (move tail pointer forward)
func (skb *SKBuff) Put(n int) ([]byte, error) {
    if skb.tail+n > skb.end {
        return nil, errors.New("skb: no tailroom")
    }
    data := skb.buf[skb.tail : skb.tail+n]
    skb.tail += n
    return data, nil
}

func (skb *SKBuff) PushUDPHeader(srcPort, dstPort uint16) error {
    hdr, err := skb.Push(8)
    if err != nil {
        return err
    }
    binary.BigEndian.PutUint16(hdr[0:2], srcPort)
    binary.BigEndian.PutUint16(hdr[2:4], dstPort)
    binary.BigEndian.PutUint16(hdr[4:6], uint16(skb.Len()))
    binary.BigEndian.PutUint16(hdr[6:8], 0) // checksum placeholder
    return nil
}

func (skb *SKBuff) PushIPv4Header(src, dst net.IP, proto uint8) error {
    hdr, err := skb.Push(20)
    if err != nil {
        return err
    }
    hdr[0] = 0x45  // version=4, IHL=5
    hdr[1] = 0     // DSCP/ECN
    binary.BigEndian.PutUint16(hdr[2:4], uint16(skb.Len()))
    binary.BigEndian.PutUint16(hdr[4:6], 0)    // ID
    binary.BigEndian.PutUint16(hdr[6:8], 0)    // flags/frag offset
    hdr[8] = 64                                  // TTL
    hdr[9] = proto                               // protocol
    binary.BigEndian.PutUint16(hdr[10:12], 0)   // checksum (compute later)
    copy(hdr[12:16], src.To4())
    copy(hdr[16:20], dst.To4())
    return nil
}

func (skb *SKBuff) PushEthernetHeader(src, dst [6]byte, etherType uint16) error {
    hdr, err := skb.Push(14)
    if err != nil {
        return err
    }
    copy(hdr[0:6], dst[:])
    copy(hdr[6:12], src[:])
    binary.BigEndian.PutUint16(hdr[12:14], etherType)
    return nil
}

func (skb *SKBuff) String() string {
    return fmt.Sprintf("SKBuff{len=%d, headroom=%d, tailroom=%d}",
        skb.Len(), skb.data-skb.head, skb.end-skb.tail)
}
```

## 8.3 TCP — State Machine and Data Structures

### TCP State Machine

```
                    ┌────────────────────────────────┐
                    │            CLOSED              │
                    └──────┬──────────────┬──────────┘
                           │ passive open │ active open
                      listen()│         │ connect()
                           ▼           ▼
                        LISTEN       SYN_SENT
                           │           │
                    SYN rcv│         │SYN+ACK rcv
                           ▼           ▼
                       SYN_RCVD ──→ ESTABLISHED
                           │           │
                      close()│         │close() / FIN rcv
                           ▼           ▼
                       FIN_WAIT_1   CLOSE_WAIT
                           │           │
                   FIN+ACK │         │close()
                           ▼           ▼
                       FIN_WAIT_2   LAST_ACK
                           │           │
                    FIN rcv│         │ACK rcv
                           ▼           ▼
                        TIME_WAIT ──→ CLOSED
                    (2×MSL wait)
```

**TIME_WAIT:** After active close, the socket waits 2×MSL (Maximum Segment Lifetime = 2 minutes typically) before closing. This ensures:
1. The final ACK reaches the peer (if lost, peer retransmits FIN)
2. No delayed packets from this connection arrive for a new connection using the same 4-tuple

### TCP Send Buffer and Congestion Control

```c
struct tcp_sock {
    /* ... inherits inet_connection_sock ... */
    
    /* Sequence numbers */
    u32 rcv_nxt;     /* next byte expected from peer */
    u32 snd_una;     /* oldest unacknowledged byte */
    u32 snd_nxt;     /* next byte to send */
    u32 snd_wnd;     /* peer's receive window */
    
    /* Congestion control */
    u32 snd_cwnd;       /* congestion window (bytes) */
    u32 snd_ssthresh;   /* slow start threshold */
    u32 prior_cwnd;
    
    /* RTT estimation */
    u32 srtt_us;    /* smoothed RTT (microseconds × 8) */
    u32 mdev_us;    /* RTT deviation */
    u32 rttvar_us;  /* RTT variance (Jacobson) */
    
    /* Send queue */
    struct sk_buff_head write_queue;
    
    /* Retransmit timer */
    struct timer_list retransmit_timer;
    
    /* Selective acknowledgment */
    struct tcp_sack_block selective_acks[4];
};
```

**TCP Congestion Control — CUBIC algorithm:**
```
Window grows cubically: W(t) = C(t - K)³ + W_max
  where K = ∛(W_max × β / C)

This gives fast growth far from previous max, slow near W_max.
After loss: W_max = current_cwnd, cwnd = cwnd × (1 - β)
```

## 8.4 Netfilter — Packet Filtering Hooks

Netfilter defines 5 hooks in the packet path:

```
Incoming packet:
  → PREROUTING hook   (NF_INET_PRE_ROUTING)
  → Routing decision
  → LOCAL_IN hook     (NF_INET_LOCAL_IN)   [→ local socket]
                   or
  → FORWARD hook      (NF_INET_FORWARD)    [→ forwarded]
  → POSTROUTING hook  (NF_INET_POST_ROUTING)

Outgoing packet:
  → LOCAL_OUT hook    (NF_INET_LOCAL_OUT)
  → Routing
  → POSTROUTING hook
```

nftables registers callbacks at these hooks. Each packet traverses the registered chains and rules.

**Connection tracking (nf_conntrack):**
```c
struct nf_conn {
    struct nf_conntrack ct_general;    /* reference count */
    struct nf_conntrack_tuple_hash tuplehash[IP_CT_DIR_MAX];  /* in hash table */
    
    /* Connection state */
    unsigned long status;              /* IPS_CONFIRMED, IPS_ASSURED, ... */
    possible_net_t ct_net;
    
    /* Protocol-specific state */
    union nf_conntrack_proto proto;
    
    /* Timeout */
    u32 timeout;
    
    /* NAT info */
    struct nf_conn_nat *nat;
};
```

## 8.5 Routing — Longest Prefix Match

The IPv4 routing table uses **Longest Prefix Match (LPM)** — the most specific route wins.

Linux's FIB (Forwarding Information Base) uses **LC-trie** (Level-Compressed trie) — a Patricia trie with run compression for O(1) average-case lookup:

```
Routes:
  0.0.0.0/0       → gateway (default)
  192.168.1.0/24  → eth0
  192.168.1.0/25  → eth1 (more specific!)
  10.0.0.0/8      → vpn0

For packet to 192.168.1.100:
  Match /0: yes
  Match /24: yes (192.168.1.x)
  Match /25: yes (192.168.1.0-127, more specific!)
  → use /25 route via eth1
```

### Trie-Based LPM — Rust Implementation

```rust
use std::net::Ipv4Addr;

#[derive(Debug, Clone)]
struct Route {
    prefix: u32,
    mask_len: u8,
    nexthop: Ipv4Addr,
    dev: String,
}

#[derive(Debug, Default)]
struct TrieNode {
    route: Option<Route>,
    children: [Option<Box<TrieNode>>; 2],
}

pub struct LPMTrie {
    root: TrieNode,
}

impl LPMTrie {
    pub fn new() -> Self {
        LPMTrie { root: TrieNode::default() }
    }
    
    pub fn insert(&mut self, prefix: Ipv4Addr, mask_len: u8, 
                  nexthop: Ipv4Addr, dev: &str) {
        let prefix_bits = u32::from(prefix);
        let mut node = &mut self.root;
        
        for i in 0..mask_len {
            let bit = ((prefix_bits >> (31 - i)) & 1) as usize;
            if node.children[bit].is_none() {
                node.children[bit] = Some(Box::new(TrieNode::default()));
            }
            node = node.children[bit].as_mut().unwrap();
        }
        
        node.route = Some(Route {
            prefix: prefix_bits,
            mask_len,
            nexthop,
            dev: dev.to_string(),
        });
    }
    
    pub fn lookup(&self, addr: Ipv4Addr) -> Option<&Route> {
        let addr_bits = u32::from(addr);
        let mut node = &self.root;
        let mut best_match: Option<&Route> = None;
        
        if node.route.is_some() {
            best_match = node.route.as_ref();
        }
        
        for i in 0..32 {
            let bit = ((addr_bits >> (31 - i)) & 1) as usize;
            match &node.children[bit] {
                None => break,
                Some(child) => {
                    node = child.as_ref();
                    if node.route.is_some() {
                        best_match = node.route.as_ref();
                    }
                }
            }
        }
        
        best_match
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Ipv4Addr;
    
    #[test]
    fn test_lpm() {
        let mut trie = LPMTrie::new();
        let gw: Ipv4Addr = "10.0.0.1".parse().unwrap();
        
        trie.insert("0.0.0.0".parse().unwrap(), 0,  gw, "eth0"); // default
        trie.insert("192.168.1.0".parse().unwrap(), 24, gw, "eth1");
        trie.insert("192.168.1.128".parse().unwrap(), 25, gw, "eth2");
        
        // Should match /24
        let r = trie.lookup("192.168.1.100".parse().unwrap()).unwrap();
        assert_eq!(r.dev, "eth1");
        
        // Should match /25 (more specific)
        let r = trie.lookup("192.168.1.200".parse().unwrap()).unwrap();
        assert_eq!(r.dev, "eth2");
        
        // Should match default /0
        let r = trie.lookup("8.8.8.8".parse().unwrap()).unwrap();
        assert_eq!(r.dev, "eth0");
    }
}
```

---

# 9. Synchronization & Concurrency Primitives

## 9.1 The Memory Model — Why Synchronization Is Hard

Modern CPUs and compilers reorder memory operations for performance. Without synchronization, concurrent programs are broken.

**Memory ordering levels (from weakest to strongest):**
```
Relaxed  → no ordering guarantees (just atomicity)
Acquire  → see all writes before corresponding Release
Release  → all my writes visible to subsequent Acquire
AcqRel   → both Acquire and Release
SeqCst   → total order across all threads
```

**x86 memory model:** x86 is TSO (Total Store Order) — stores from one CPU appear in order to others, but stores may be buffered (not immediately visible). Loads are not reordered with other loads, but a load can bypass a pending store from a different address.

**ARM/POWER memory model:** Much weaker — nearly all reorderings are allowed. Requires explicit memory barriers.

## 9.2 Spinlocks

Spinlocks busy-wait on a lock — the CPU loops until the lock is available. Used when:
1. The wait is expected to be short (< few microseconds)
2. You cannot sleep (interrupt context, NMI, or atomic section)

```c
/* Kernel spinlock — x86 implementation */
typedef struct raw_spinlock {
    atomic_t rawlock;
} raw_spinlock_t;

/* Lock: atomically increment tail, wait until head catches up */
/* Ticket spinlock (older kernels): */
static inline void arch_spin_lock(arch_spinlock_t *lock) {
    short inc = 0x0100;
    asm volatile (
        LOCK_PREFIX "xaddw %w0, %1\n"
        "1:\t"
        "cmpb %h0, %b0\n"    /* compare tail to head */
        "je 2f\n"             /* equal → lock acquired */
        "rep ; nop\n"         /* PAUSE instruction */
        "movb %1, %b0\n"
        "jmp 1b\n"
        "2:"
        : "+Q" (inc), "+m" (lock->slock)
        : : "memory", "cc");
}
```

**Queued spinlocks (current Linux):** Each CPU spins on its own cache line (MCS-style). Avoids thundering herd on the lock word itself.

### Spinlock — Rust (using atomic CAS)

```rust
use std::sync::atomic::{AtomicBool, Ordering};
use std::hint;

pub struct SpinLock<T> {
    locked: AtomicBool,
    data:   std::cell::UnsafeCell<T>,
}

unsafe impl<T: Send> Send for SpinLock<T> {}
unsafe impl<T: Send> Sync for SpinLock<T> {}

pub struct SpinLockGuard<'a, T> {
    lock: &'a SpinLock<T>,
}

impl<T> SpinLock<T> {
    pub const fn new(data: T) -> Self {
        SpinLock {
            locked: AtomicBool::new(false),
            data: std::cell::UnsafeCell::new(data),
        }
    }
    
    pub fn lock(&self) -> SpinLockGuard<'_, T> {
        // Two-phase: optimistic load then CAS
        loop {
            // First: optimistic check with Relaxed (no fence, fast)
            if !self.locked.load(Ordering::Relaxed) {
                // Then: attempt to acquire with Acquire ordering
                if self.locked.compare_exchange_weak(
                    false, true,
                    Ordering::Acquire,  // success: establish happens-before
                    Ordering::Relaxed,  // failure: no guarantee needed
                ).is_ok() {
                    return SpinLockGuard { lock: self };
                }
            }
            // Exponential backoff + PAUSE hint (reduces cache line contention)
            hint::spin_loop();
        }
    }
}

impl<'a, T> std::ops::Deref for SpinLockGuard<'a, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.lock.data.get() }
    }
}

impl<'a, T> std::ops::DerefMut for SpinLockGuard<'a, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<'a, T> Drop for SpinLockGuard<'a, T> {
    fn drop(&mut self) {
        self.lock.locked.store(false, Ordering::Release);
        // Release: all my writes are visible to next lock holder
    }
}

/// MCS (Mellor-Crummey Scott) spinlock — scalable for many CPUs
/// Each waiter spins on its own node — no cache line bouncing
pub struct MCSNode {
    next:   AtomicBool, // spin here
    locked: AtomicBool,
    _pad:   [u8; 56],  // pad to cache line
}

pub struct MCSLock {
    tail: std::sync::atomic::AtomicPtr<MCSNode>,
}
```

## 9.3 Mutexes and Semaphores

**Mutex:** Binary semaphore with ownership (only the locker can unlock). Can sleep — puts task in wait queue when contended.

```c
/* Linux kernel mutex */
struct mutex {
    atomic_long_t owner;  /* task_struct* of owner + state bits */
    raw_spinlock_t wait_lock;
    struct list_head wait_list;
#ifdef CONFIG_DEBUG_MUTEXES
    unsigned long magic;
    struct lockdep_map dep_map;
#endif
};

/* Fast path (uncontended): single atomic operation */
static inline int __mutex_trylock_fast(struct mutex *lock) {
    unsigned long curr = (unsigned long)current;
    unsigned long zero = 0UL;
    return atomic_long_try_cmpxchg_acquire(&lock->owner, &zero, curr);
}
```

**Semaphore:** Counter-based — allows N concurrent holders. Used for resource pools.

```c
struct semaphore {
    raw_spinlock_t lock;
    unsigned int count;
    struct list_head wait_list;
};

void down(struct semaphore *sem);  /* decrement, sleep if 0 */
void up(struct semaphore *sem);    /* increment, wake waiter */
```

### RW Semaphore — Reader-Writer Lock

```c
/* rwsem: allows multiple concurrent readers OR one writer */
struct rw_semaphore {
    atomic_long_t count;
    /* count > 0: readers active (count = num readers)
     * count = 0: unlocked
     * count = -1: writer active
     */
    atomic_long_t owner;
    struct optimistic_spin_queue osq;  /* MCS queue for optimistic spin */
    raw_spinlock_t wait_lock;
    struct list_head wait_list;
};
```

**Read-Copy-Update (RCU):** The most scalable read-side primitive. Readers never block, never use atomic operations. Writers must wait for a "grace period" (all preexisting readers to complete) before freeing old data.

```c
/* RCU read side — zero overhead on most architectures */
rcu_read_lock();
    struct data *d = rcu_dereference(global_ptr);  /* load with barrier */
    /* read d safely */
rcu_read_unlock();

/* RCU update side */
old = global_ptr;
new = alloc_data();
*new = *old;
new->field = updated_value;
rcu_assign_pointer(global_ptr, new);  /* publish with barrier */
synchronize_rcu();   /* wait for all readers to finish using 'old' */
kfree(old);
```

**RCU grace period implementation:** RCU tracks quiescent states (context switches, explicit voluntary points). When every CPU has had a quiescent state since the RCU update, the grace period ends. On non-preemptive kernels, a context switch IS a quiescent state (no RCU read-side section survives a context switch).

### Mutex — Go Implementation

```go
package sync_primitives

import (
    "runtime"
    "sync/atomic"
    "unsafe"
)

const (
    mutexLocked = 1 << iota
    mutexWoken
    mutexStarving
    mutexWaiterShift = iota
    starvationThresholdNs = 1e6 // 1ms
)

// This mirrors Go's actual sync.Mutex implementation logic
type Mutex struct {
    state int32
    sema  uint32
}

func (m *Mutex) Lock() {
    // Fast path: grab unlocked mutex atomically
    if atomic.CompareAndSwapInt32(&m.state, 0, mutexLocked) {
        return
    }
    m.lockSlow()
}

func (m *Mutex) lockSlow() {
    var waitStartTime int64
    starving := false
    awoke := false
    iter := 0
    old := m.state
    
    for {
        // Spin if we can (CPU has multiple cores and lock is not starving)
        if old&(mutexLocked|mutexStarving) == mutexLocked && 
           runtime_canSpin(iter) {
            if !awoke && old&mutexWoken == 0 &&
               old>>mutexWaiterShift != 0 &&
               atomic.CompareAndSwapInt32(&m.state, old, old|mutexWoken) {
                awoke = true
            }
            runtime_doSpin()
            iter++
            old = m.state
            continue
        }
        
        new := old
        if old&mutexStarving == 0 {
            new |= mutexLocked // try to lock
        }
        if old&(mutexLocked|mutexStarving) != 0 {
            new += 1 << mutexWaiterShift // add to waiter count
        }
        if starving && old&mutexLocked != 0 {
            new |= mutexStarving
        }
        if awoke {
            new &^= mutexWoken
        }
        
        if atomic.CompareAndSwapInt32(&m.state, old, new) {
            if old&(mutexLocked|mutexStarving) == 0 {
                break // acquired the lock
            }
            // Queue at front if we were woken (LIFO for woken goroutines)
            queueLifo := waitStartTime != 0
            if waitStartTime == 0 {
                waitStartTime = nanotime()
            }
            runtime_SemacquireMutex(&m.sema, queueLifo, 1)
            starving = starving || nanotime()-waitStartTime > starvationThresholdNs
            old = m.state
            if old&mutexStarving != 0 {
                // We're being handed the mutex in starvation mode
                delta := int32(mutexLocked - 1<<mutexWaiterShift)
                if !starving || old>>mutexWaiterShift == 1 {
                    delta -= mutexStarving
                }
                atomic.AddInt32(&m.state, delta)
                break
            }
            awoke = true
            iter = 0
        } else {
            old = m.state
        }
    }
}

func (m *Mutex) Unlock() {
    new := atomic.AddInt32(&m.state, -mutexLocked)
    if new != 0 {
        m.unlockSlow(new)
    }
}

func (m *Mutex) unlockSlow(new int32) {
    if new&mutexStarving == 0 {
        old := new
        for {
            if old>>mutexWaiterShift == 0 || 
               old&(mutexLocked|mutexWoken|mutexStarving) != 0 {
                return
            }
            new = (old - 1<<mutexWaiterShift) | mutexWoken
            if atomic.CompareAndSwapInt32(&m.state, old, new) {
                runtime_Semrelease(&m.sema, false, 1)
                return
            }
            old = m.state
        }
    } else {
        // Starvation mode: hand off directly to first waiter
        runtime_Semrelease(&m.sema, true, 1)
    }
}

// Stubs (implemented in Go runtime assembly)
func runtime_canSpin(i int) bool { return i < 4 && runtime.NumCPU() > 1 }
func runtime_doSpin() { /* PAUSE loop */ }
func nanotime() int64 { return 0 /* syscall */ }
func runtime_SemacquireMutex(s *uint32, lifo bool, skipframes int) {}
func runtime_Semrelease(s *uint32, handoff bool, skipframes int) {}
var _ = unsafe.Pointer(nil)
```

## 9.4 Lock-Free Data Structures

Lock-free algorithms use atomic operations (CAS — Compare-And-Swap) instead of locks. They guarantee **system-wide progress** — at least one thread makes progress even if others are preempted.

### Lock-Free Stack (Treiber Stack) — Rust

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

/// Lock-free Treiber stack
pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

unsafe impl<T: Send> Send for LockFreeStack<T> {}
unsafe impl<T: Send> Sync for LockFreeStack<T> {}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack { head: AtomicPtr::new(ptr::null_mut()) }
    }
    
    pub fn push(&self, data: T) {
        let node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));
        
        loop {
            let head = self.head.load(Ordering::Relaxed);
            unsafe { (*node).next = head; }
            
            // CAS: if head is still the same, install our node
            match self.head.compare_exchange_weak(
                head, node,
                Ordering::Release,  // success: our write is visible
                Ordering::Relaxed,  // failure
            ) {
                Ok(_) => return,
                Err(_) => continue,  // another thread modified head — retry
            }
        }
    }
    
    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() { return None; }
            
            let next = unsafe { (*head).next };
            
            match self.head.compare_exchange_weak(
                head, next,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    let data = unsafe { Box::from_raw(head).data };
                    return Some(data);
                }
                Err(_) => continue,
            }
        }
    }
}

impl<T> Drop for LockFreeStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}
```

**ABA Problem:** The classical pitfall of lock-free algorithms. Thread 1 reads head=A. Thread 2 pops A, pushes B, pops B, pushes A again. Thread 1's CAS succeeds (head is still A!) but now the stack is in an incorrect state.

Solutions:
- **Tagged pointers:** Store a version counter in low bits or high bits of pointer
- **Hazard pointers:** Mark pointers before dereferencing — prevents premature free
- **Epoch-based reclamation:** Used in crossbeam-rs (Rust)

---

# 10. I/O Subsystem & Block Layer

## 10.1 Block Layer Architecture

```
File System (ext4, btrfs, xfs)
        │ bio submission
        ▼
Block Layer (submit_bio)
        │
        ├─ I/O scheduler (BFQ, mq-deadline, kyber, none)
        │
        ├─ Device Mapper (dm-crypt, dm-raid, dm-thin...)
        │
        └─ SCSI layer / NVMe layer
                │
                ▼
        Device Driver (ahci, nvme, virtio_blk)
                │
                ▼
        Hardware (SSD, HDD, NVMe)
```

## 10.2 bio — Block I/O Request

```c
struct bio {
    struct bio *bi_next;     /* chain for splits */
    struct block_device *bi_bdev;
    
    blk_opf_t bi_opf;        /* operation: REQ_OP_READ, REQ_OP_WRITE... */
    unsigned short bi_flags;
    
    struct bvec_iter bi_iter; /* current position in bi_io_vec */
    
    bio_end_io_t *bi_end_io; /* completion callback */
    void *bi_private;
    
    unsigned short bi_vcnt;   /* number of bio_vec */
    unsigned short bi_max_vecs;
    
    atomic_t bi_cnt;          /* reference count */
    
    struct bio_vec *bi_io_vec; /* array of data segments */
};

struct bio_vec {
    struct page *bv_page;   /* the page containing data */
    unsigned int bv_len;    /* bytes to transfer */
    unsigned int bv_offset; /* offset within page */
};
```

A single `bio` can describe a **scatter-gather list** of up to `BIO_MAX_VECS` (256) page fragments. The driver sets up DMA descriptors from this list, allowing the hardware to directly write to/from scattered memory pages without copying.

## 10.3 I/O Schedulers

**CFQ (Completely Fair Queuing):** Historic default. Per-process queues, time slices. Removed in 5.0.

**BFQ (Budget Fair Queuing):** Current default for rotational drives. Assigns "budgets" in sectors, provides low latency for interactive workloads.

**mq-deadline:** Simple deadline-based scheduler. Good for SSDs. Two deadline queues (read/write) + FIFO for aging.

**kyber:** Low-latency scheduler for fast NVMe. Maintains separate queues for read, sync-write, other. Token bucket for latency control.

### BFQ Core Algorithm

```
BFQ maintains:
- Per-process I/O queues (bfq_queue)
- A weight-fair service tree (by virtual finish time, like CFS!)
- Budget: number of sectors to serve before preempting

Virtual time:
  V_finish = V_start + budget / weight

BFQ serves the queue with smallest V_finish (min-heap, red-black tree)
On completion: V_start_next = max(V_current, V_finish)
```

BFQ is essentially CFS applied to I/O bandwidth instead of CPU time.

### I/O Scheduler Simulation — Go

```go
package iosched

import (
    "container/heap"
    "time"
)

type Request struct {
    Sector   uint64
    Len      uint32
    IsRead   bool
    Deadline time.Time
    PID      int
    index    int
}

// Deadline scheduler: deadline heap + sector-sorted FIFO
type ByDeadline []*Request

func (d ByDeadline) Len() int            { return len(d) }
func (d ByDeadline) Less(i, j int) bool  { return d[i].Deadline.Before(d[j].Deadline) }
func (d ByDeadline) Swap(i, j int) {
    d[i], d[j] = d[j], d[i]
    d[i].index = i
    d[j].index = j
}
func (d *ByDeadline) Push(x any) {
    r := x.(*Request)
    r.index = len(*d)
    *d = append(*d, r)
}
func (d *ByDeadline) Pop() any {
    old := *d
    n := len(old)
    r := old[n-1]
    r.index = -1
    *d = old[:n-1]
    return r
}

type DeadlineScheduler struct {
    readDeadline  ByDeadline
    writeDeadline ByDeadline
    readFIFO      []*Request  // sorted by sector
    writeFIFO     []*Request
    
    ReadLatency   time.Duration // 500ms
    WriteLatency  time.Duration // 5000ms
    
    lastSector    uint64
    readBatch     int
    currentBatches int
}

func NewDeadlineScheduler() *DeadlineScheduler {
    s := &DeadlineScheduler{
        ReadLatency:  500 * time.Millisecond,
        WriteLatency: 5000 * time.Millisecond,
        readBatch:    4, // reads per write batch
    }
    heap.Init(&s.readDeadline)
    heap.Init(&s.writeDeadline)
    return s
}

func (s *DeadlineScheduler) Insert(r *Request) {
    r.Deadline = time.Now().Add(map[bool]time.Duration{
        true:  s.ReadLatency,
        false: s.WriteLatency,
    }[r.IsRead])
    
    if r.IsRead {
        heap.Push(&s.readDeadline, r)
        s.insertSorted(&s.readFIFO, r)
    } else {
        heap.Push(&s.writeDeadline, r)
        s.insertSorted(&s.writeFIFO, r)
    }
}

func (s *DeadlineScheduler) insertSorted(q *[]*Request, r *Request) {
    i := 0
    for i < len(*q) && (*q)[i].Sector < r.Sector {
        i++
    }
    *q = append(*q, nil)
    copy((*q)[i+1:], (*q)[i:])
    (*q)[i] = r
}

func (s *DeadlineScheduler) Next() *Request {
    now := time.Now()
    
    // Check for expired deadlines (starvation prevention)
    if len(s.readDeadline) > 0 && s.readDeadline[0].Deadline.Before(now) {
        return s.dispatchRead()
    }
    if len(s.writeDeadline) > 0 && s.writeDeadline[0].Deadline.Before(now) {
        return s.dispatchWrite()
    }
    
    // Normal: prefer reads (lower latency requirement)
    if s.currentBatches < s.readBatch && len(s.readFIFO) > 0 {
        s.currentBatches++
        return s.dispatchReadFIFO()
    }
    if len(s.writeFIFO) > 0 {
        s.currentBatches = 0
        return s.dispatchWriteFIFO()
    }
    if len(s.readFIFO) > 0 {
        return s.dispatchReadFIFO()
    }
    return nil
}

func (s *DeadlineScheduler) dispatchRead() *Request {
    if len(s.readDeadline) == 0 { return nil }
    r := heap.Pop(&s.readDeadline).(*Request)
    s.removeFromFIFO(&s.readFIFO, r)
    return r
}

func (s *DeadlineScheduler) dispatchReadFIFO() *Request {
    if len(s.readFIFO) == 0 { return nil }
    r := s.readFIFO[0]
    s.readFIFO = s.readFIFO[1:]
    // Also remove from deadline heap
    return r
}

func (s *DeadlineScheduler) dispatchWrite() *Request {
    if len(s.writeDeadline) == 0 { return nil }
    r := heap.Pop(&s.writeDeadline).(*Request)
    s.removeFromFIFO(&s.writeFIFO, r)
    return r
}

func (s *DeadlineScheduler) dispatchWriteFIFO() *Request {
    if len(s.writeFIFO) == 0 { return nil }
    r := s.writeFIFO[0]
    s.writeFIFO = s.writeFIFO[1:]
    return r
}

func (s *DeadlineScheduler) removeFromFIFO(q *[]*Request, r *Request) {
    for i, req := range *q {
        if req == r {
            *q = append((*q)[:i], (*q)[i+1:]...)
            return
        }
    }
}
```

## 10.4 Direct I/O and io_uring

**Direct I/O (O_DIRECT):** Bypasses page cache. Data transferred directly between user buffer and disk. Requires buffer alignment to logical block size.

```c
int fd = open("/dev/nvme0n1", O_RDWR | O_DIRECT);
void *buf;
posix_memalign(&buf, 512, 512 * 1024);  /* 512-byte aligned */
pread(fd, buf, 512 * 1024, 0);
```

**io_uring (since 5.1):** Asynchronous I/O via shared memory ring buffers between user and kernel. Zero-copy submission and completion.

```
┌─────────────────────────────────────┐
│           User Space                │
│  ┌──────────────┐ ┌──────────────┐  │
│  │ SQ Ring      │ │ CQ Ring      │  │
│  │ (submission) │ │ (completion) │  │
│  └──────┬───────┘ └──────▲───────┘  │
│         │ mmap'd          │ mmap'd   │
└─────────┼─────────────────┼─────────┘
          │                 │
┌─────────┼─────────────────┼─────────┐
│         ▼    Kernel        │         │
│  ┌──────────────────────────────┐   │
│  │      io_uring instance       │   │
│  │  poll SQ → submit I/O → CQ   │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

io_uring eliminates:
- System call overhead (batch multiple I/Os)
- Context switch overhead (kernel polling mode: SQPOLL)
- Data copy overhead (O_DIRECT + fixed buffers)

Result: millions of IOPS possible on NVMe with single-digit CPU usage.

---

# 11. System Calls

## 11.1 The System Call Interface

System calls are the boundary between user space and kernel space. On x86_64:

```
User space:
  mov rax, 1        ; syscall number (SYS_write = 1)
  mov rdi, 1        ; arg1: fd
  mov rsi, buf      ; arg2: buffer
  mov rdx, count    ; arg3: length
  syscall           ; transitions to ring 0

Kernel entry (entry_SYSCALL_64):
  swapgs            ; switch to kernel GS (contains per-CPU data)
  mov rsp, [per_cpu kernel_stack]
  push user registers
  call do_syscall_64
      → sys_call_table[rax](args...)
  pop user registers
  sysretq           ; return to user space
```

**SYSCALL vs INT 0x80:**
- `syscall` instruction: faster (no IDT lookup), 64-bit only
- `int 0x80`: legacy, 32-bit compatibility, slower

**vsyscall/vDSO:** Some syscalls (gettimeofday, clock_gettime) are so frequent that they're mapped into user address space — callable without entering kernel! The kernel maintains a shared page (vvar) with current time, which the vDSO reads directly. Zero kernel transition for time queries.

## 11.2 System Call Table

```c
/* arch/x86/entry/syscalls/syscall_64.tbl */
0  common  read                    sys_read
1  common  write                   sys_write
2  common  open                    sys_open
3  common  close                   sys_close
...
9  common  mmap                    sys_mmap
10 common  mprotect                sys_mprotect
...
56 common  clone                   sys_clone
57 common  fork                    sys_fork
58 common  vfork                   sys_vfork
...
435 common io_uring_setup          sys_io_uring_setup
436 common io_uring_enter          sys_io_uring_enter
```

**Argument passing:** Up to 6 arguments in registers (rdi, rsi, rdx, r10, r8, r9). More than 6: pass a struct pointer.

## 11.3 copy_to_user / copy_from_user

Kernel must never blindly dereference user-provided pointers:

```c
/* Safe user memory access */
long copy_from_user(void *to, const void __user *from, unsigned long n);
long copy_to_user(void __user *to, const void *from, unsigned long n);

/* Why dangerous to dereference user pointers directly:
 * 1. User pointer might be NULL or garbage → kernel null deref (oops)
 * 2. User pointer might point to kernel memory → privilege escalation
 * 3. User might change pointer target between check and use (TOCTOU)
 * 4. User page might not be present → page fault in kernel context
 *    (allowed with proper exception table handling)
 */

/* SMEP (Supervisor Mode Execution Prevention): CPU refuses to execute
 * user-space pages in kernel mode
 * SMAP (Supervisor Mode Access Prevention): CPU refuses to access
 * user-space memory in kernel mode without STAC/CLAC instructions
 * copy_from/to_user uses STAC/CLAC around the actual access
 */
```

### System Call Implementation — C (Custom Syscall via Module)

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/uaccess.h>

/* Custom syscall: sum an array of integers from userspace */
SYSCALL_DEFINE3(my_sum,
    int __user *, array,    /* userspace pointer */
    size_t, count,          /* number of elements */
    long __user *, result)  /* output pointer */
{
    long sum = 0;
    int val;
    size_t i;
    
    /* Validate count to prevent excessive kernel time */
    if (count > 1000000)
        return -EINVAL;
    
    for (i = 0; i < count; i++) {
        /* Each access through copy_from_user:
         * - validates pointer is in user address space
         * - handles page faults gracefully
         * - on x86: SMAP protection via STAC/CLAC
         */
        if (get_user(val, array + i))
            return -EFAULT;
        sum += val;
    }
    
    if (put_user(sum, result))
        return -EFAULT;
    
    return 0;
}
```

### System Call Interception — Rust (ptrace-based)

```rust
use std::io;

/// Trace system calls using ptrace (simplified)
pub fn trace_syscalls(pid: i32) -> io::Result<()> {
    use std::io::{Error, ErrorKind};
    
    // In a real implementation, we'd use the nix crate or raw syscalls
    // This shows the conceptual flow
    
    let mut in_syscall = false;
    
    loop {
        // Wait for child to stop
        let status = waitpid(pid)?;
        
        if process_exited(status) {
            break;
        }
        
        if stopped_by_syscall(status) {
            if !in_syscall {
                // Syscall entry: read registers
                let regs = ptrace_getregs(pid)?;
                let syscall_num = regs.orig_rax;
                let arg1 = regs.rdi;
                let arg2 = regs.rsi;
                let arg3 = regs.rdx;
                
                println!("syscall {} ({:#x}, {:#x}, {:#x})",
                    syscall_name(syscall_num), arg1, arg2, arg3);
                in_syscall = true;
            } else {
                // Syscall exit: read return value
                let regs = ptrace_getregs(pid)?;
                let ret = regs.rax as i64;
                println!("  → {}", ret);
                in_syscall = false;
            }
        }
        
        // Continue until next syscall
        ptrace_syscall(pid)?;
    }
    
    Ok(())
}

// Placeholder stubs
fn waitpid(_pid: i32) -> io::Result<i32> { Ok(0) }
fn process_exited(_status: i32) -> bool { false }
fn stopped_by_syscall(_status: i32) -> bool { true }
fn ptrace_getregs(_pid: i32) -> io::Result<UserRegs> { 
    Ok(UserRegs::default()) 
}
fn ptrace_syscall(_pid: i32) -> io::Result<()> { Ok(()) }
fn syscall_name(n: u64) -> &'static str {
    match n {
        0 => "read", 1 => "write", 2 => "open", 3 => "close",
        9 => "mmap", 56 => "clone", 57 => "fork",
        _ => "unknown"
    }
}

#[derive(Default)]
struct UserRegs {
    orig_rax: u64, rax: u64,
    rdi: u64, rsi: u64, rdx: u64,
}
```

---

# 12. Interrupt Handling & Softirqs

## 12.1 Interrupt Architecture

```
Hardware IRQ (e.g., NIC receives packet)
        │
        ▼
APIC (Advanced Programmable Interrupt Controller)
        │ vector number
        ▼
CPU raises interrupt
        │
        ▼ (saves registers on stack)
Interrupt Descriptor Table (IDT)
        │
        ▼
do_IRQ() [entry point]
        │
        ├─ irq_enter()  [mark in_interrupt]
        │
        ├─ handle_irq() → irq_desc → action handlers
        │       │
        │       └─ driver's handler: e.g., e1000_intr()
        │              └─ schedule_napi_poll() → return IRQ_HANDLED
        │
        ├─ irq_exit()   [leave interrupt context]
        │       └─ raise softirq if pending
        │
        └─ return to interrupted code
```

## 12.2 Top Half and Bottom Half

**Top half (interrupt handler):** Must complete quickly. Cannot sleep. Cannot use most kernel APIs. Just: acknowledge hardware, save data, schedule bottom half.

**Bottom half:** Deferred work, can be scheduled any time. Can do more work, still cannot sleep.

**Three bottom half mechanisms:**

1. **Softirqs** — statically defined, run on the CPU that raised them, re-entrant, highest priority BH
2. **Tasklets** — dynamic, per-CPU serialized (not re-entrant), run in softirq context
3. **Workqueues** — run in kernel threads, can sleep, lowest priority BH

```c
/* Softirq types (ordered by priority) */
enum {
    HI_SOFTIRQ = 0,        /* tasklet hi */
    TIMER_SOFTIRQ,          /* timer expiry */
    NET_TX_SOFTIRQ,         /* network transmit */
    NET_RX_SOFTIRQ,         /* network receive */
    BLOCK_SOFTIRQ,          /* block I/O completion */
    IRQ_POLL_SOFTIRQ,
    TASKLET_SOFTIRQ,        /* tasklets */
    SCHED_SOFTIRQ,          /* scheduler */
    HRTIMER_SOFTIRQ,        /* high-res timers */
    RCU_SOFTIRQ,            /* RCU callbacks */
    NR_SOFTIRQS
};
```

## 12.3 NAPI — Network Interrupt Mitigation

Under high packet rates, receiving a separate interrupt per packet would overwhelm the CPU. **NAPI (New API)** solves this:

```
1. First packet arrives → hardware interrupt
2. Interrupt handler: disable NIC interrupts, schedule NAPI poll
3. softirq runs net_rx_action():
   a. Poll NIC ring buffer for ready packets
   b. Process up to budget packets (64 by default)
   c. If ring not empty: continue polling (no interrupt)
   d. If ring empty: re-enable NIC interrupts, return
```

This converts O(n) interrupts to O(1) softirq invocations per "burst" of packets. At 10 Gbps, a 1500-byte packet arrives every ~1.2 microseconds — without NAPI, that's 833,000 interrupts/second.

### Interrupt Handler Simulation — Rust

```rust
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

#[derive(Debug, Clone)]
struct Packet {
    data: Vec<u8>,
    timestamp: u64,
}

struct NICRingBuffer {
    ring:       VecDeque<Packet>,
    capacity:   usize,
    irq_enabled: AtomicBool,
}

impl NICRingBuffer {
    fn new(cap: usize) -> Self {
        NICRingBuffer {
            ring:        VecDeque::with_capacity(cap),
            capacity:    cap,
            irq_enabled: AtomicBool::new(true),
        }
    }
    
    fn receive(&mut self, pkt: Packet) -> bool {
        if self.ring.len() < self.capacity {
            self.ring.push_back(pkt);
            true
        } else {
            false  // ring full, drop packet
        }
    }
}

struct NAPIController {
    ring:        Arc<Mutex<NICRingBuffer>>,
    napi_sched:  AtomicBool,
    packets_proc: AtomicU64,
}

impl NAPIController {
    fn new(ring: Arc<Mutex<NICRingBuffer>>) -> Self {
        NAPIController {
            ring,
            napi_sched:   AtomicBool::new(false),
            packets_proc: AtomicU64::new(0),
        }
    }
    
    /// Simulates hardware interrupt handler (top half)
    fn interrupt_handler(&self) {
        let mut ring = self.ring.lock().unwrap();
        
        if ring.ring.is_empty() { return; }
        
        // Disable further IRQs — NAPI will poll instead
        ring.irq_enabled.store(false, Ordering::SeqCst);
        drop(ring);
        
        // Schedule NAPI poll (schedule_napi_poll)
        self.napi_sched.store(true, Ordering::Release);
    }
    
    /// NAPI poll — runs in softirq context (bottom half)
    /// Returns number of packets processed
    fn napi_poll(&self, budget: usize) -> usize {
        if !self.napi_sched.load(Ordering::Acquire) {
            return 0;
        }
        
        let mut processed = 0;
        
        {
            let mut ring = self.ring.lock().unwrap();
            
            while processed < budget {
                match ring.ring.pop_front() {
                    Some(pkt) => {
                        self.process_packet(pkt);
                        processed += 1;
                    }
                    None => {
                        // Ring empty — re-enable IRQs
                        ring.irq_enabled.store(true, Ordering::SeqCst);
                        self.napi_sched.store(false, Ordering::Release);
                        break;
                    }
                }
            }
        }
        
        self.packets_proc.fetch_add(processed as u64, Ordering::Relaxed);
        processed
    }
    
    fn process_packet(&self, pkt: Packet) {
        // In kernel: alloc skb, fill headers, pass to network stack
        let _ = pkt;
    }
    
    fn packets_processed(&self) -> u64 {
        self.packets_proc.load(Ordering::Relaxed)
    }
}
```

---

# 13. Device Drivers & Kernel Modules

## 13.1 Kernel Module Infrastructure

A loadable kernel module (LKM) is an object file that can be inserted into/removed from the running kernel without rebooting.

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Systems Programmer");
MODULE_DESCRIPTION("Example character device driver");
MODULE_VERSION("1.0");

static int __init mydriver_init(void) {
    pr_info("mydriver: loaded\n");
    return 0;
}

static void __exit mydriver_exit(void) {
    pr_info("mydriver: unloaded\n");
}

module_init(mydriver_init);
module_exit(mydriver_exit);
```

**`__init` and `__exit` attributes:**
`__init` marks the function as initialization-only. After `mydriver_init()` returns, the kernel frees the `.init.text` section. This is memory optimization — init code is one-time, no need to keep it resident.

## 13.2 Character Device Driver

```c
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/cdev.h>

#define DEVICE_NAME "mychar"
#define BUF_SIZE    1024

static int major;
static struct cdev my_cdev;
static struct class *my_class;
static char kernel_buf[BUF_SIZE];
static int buf_len;

static int mychar_open(struct inode *inode, struct file *file) {
    pr_info("mychar: open() called\n");
    return 0;
}

static int mychar_release(struct inode *inode, struct file *file) {
    pr_info("mychar: release() called\n");
    return 0;
}

static ssize_t mychar_read(struct file *file, char __user *buf,
                            size_t count, loff_t *ppos) {
    int bytes_to_read = min((int)count, buf_len - (int)*ppos);
    if (bytes_to_read <= 0) return 0;  /* EOF */
    
    if (copy_to_user(buf, kernel_buf + *ppos, bytes_to_read))
        return -EFAULT;
    
    *ppos += bytes_to_read;
    return bytes_to_read;
}

static ssize_t mychar_write(struct file *file, const char __user *buf,
                             size_t count, loff_t *ppos) {
    if (count > BUF_SIZE) count = BUF_SIZE;
    
    if (copy_from_user(kernel_buf, buf, count))
        return -EFAULT;
    
    buf_len = count;
    *ppos += count;
    return count;
}

static long mychar_ioctl(struct file *file, unsigned int cmd, unsigned long arg) {
    switch (cmd) {
    case 0x1001:  /* MYCHAR_GET_LEN */
        return put_user(buf_len, (int __user *)arg) ? -EFAULT : 0;
    case 0x1002:  /* MYCHAR_CLEAR */
        memset(kernel_buf, 0, BUF_SIZE);
        buf_len = 0;
        return 0;
    default:
        return -ENOTTY;
    }
}

static const struct file_operations mychar_fops = {
    .owner          = THIS_MODULE,
    .open           = mychar_open,
    .release        = mychar_release,
    .read           = mychar_read,
    .write          = mychar_write,
    .unlocked_ioctl = mychar_ioctl,
};

static int __init mychar_init(void) {
    dev_t dev;
    int ret;
    
    ret = alloc_chrdev_region(&dev, 0, 1, DEVICE_NAME);
    if (ret < 0) return ret;
    major = MAJOR(dev);
    
    cdev_init(&my_cdev, &mychar_fops);
    my_cdev.owner = THIS_MODULE;
    cdev_add(&my_cdev, dev, 1);
    
    my_class = class_create(THIS_MODULE, DEVICE_NAME);
    device_create(my_class, NULL, dev, NULL, DEVICE_NAME);
    
    pr_info("mychar: registered with major %d\n", major);
    return 0;
}

static void __exit mychar_exit(void) {
    dev_t dev = MKDEV(major, 0);
    device_destroy(my_class, dev);
    class_destroy(my_class);
    cdev_del(&my_cdev);
    unregister_chrdev_region(dev, 1);
}

module_init(mychar_init);
module_exit(mychar_exit);
MODULE_LICENSE("GPL");
```

## 13.3 Platform Device Driver Model

Modern Linux device drivers use the **platform device / driver model** — drivers declare what hardware they support, and the kernel matches devices to drivers.

```c
/* DTS (Device Tree Source) declares hardware: */
/*
uart0: serial@e0000000 {
    compatible = "mycompany,uart-1.0";
    reg = <0xe0000000 0x1000>;
    interrupts = <0 30 4>;
    clocks = <&apb_clk 0>;
};
*/

/* Driver declares compatibility: */
static const struct of_device_id myuart_of_match[] = {
    { .compatible = "mycompany,uart-1.0" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, myuart_of_match);

static int myuart_probe(struct platform_device *pdev) {
    struct resource *res;
    void __iomem *base;
    int irq;
    
    /* Get MMIO region from device tree */
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    base = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(base)) return PTR_ERR(base);
    
    /* Get IRQ */
    irq = platform_get_irq(pdev, 0);
    if (irq < 0) return irq;
    
    /* Register interrupt handler */
    devm_request_irq(&pdev->dev, irq, myuart_irq_handler,
                     IRQF_SHARED, "myuart", pdev);
    
    /* devm_ prefix: automatically cleaned up on driver removal */
    return 0;
}

static int myuart_remove(struct platform_device *pdev) {
    /* devm_ resources freed automatically */
    return 0;
}

static struct platform_driver myuart_driver = {
    .probe  = myuart_probe,
    .remove = myuart_remove,
    .driver = {
        .name = "myuart",
        .of_match_table = myuart_of_match,
    },
};

module_platform_driver(myuart_driver);
```

**`devm_` (device-managed):** Resources allocated with `devm_` prefix are automatically freed when the device is unbound. This prevents resource leaks on error paths — a critical correctness concern in kernel code.

---

# 14. Security Subsystems & LSM

## 14.1 Linux Security Modules (LSM)

LSM provides hooks throughout the kernel that security modules can use to enforce access control. Multiple LSMs can stack (since 4.17):

```
Stack: SELinux + Yama + BPF-LSM

syscall(open, path, flags)
    │
    ▼ inode_permission hook
  [Yama] → ALLOW
    ↓
  [SELinux] → check policy: does this process type have read access to this file type?
    ↓
  [BPF-LSM] → run eBPF program for custom policy
    ↓
  VFS open
```

## 14.2 SELinux — Type Enforcement

SELinux labels every resource (file, process, socket, IPC) with a **security context**:
```
user:role:type:level
system_u:system_r:httpd_t:s0  ← Apache process context
system_u:object_r:httpd_sys_content_t:s0  ← Apache's web files
```

Policy rules:
```
allow httpd_t httpd_sys_content_t:file { read getattr open };
allow httpd_t httpd_log_t:file { write append };
```

This is **mandatory access control (MAC)** — not even root can bypass it (unless process has `unconfined_t` type).

## 14.3 eBPF — Programmable Kernel Observability

eBPF (extended Berkeley Packet Filter) allows safe user-defined programs to run inside the kernel without writing kernel modules:

```
User writes eBPF program (C or Rust)
        │ clang -target bpf
        ▼
eBPF bytecode
        │ bpf() syscall
        ▼
Kernel verifier (checks: no unbounded loops, no invalid memory access,
                          no blocking operations, type safety)
        │ JIT compiler
        ▼
Native machine code (runs at hook point)
```

**eBPF use cases:**
- `kprobe`: Trace any kernel function entry/return
- `tracepoint`: Predefined stable trace points
- `XDP`: eXpress Data Path — packet filter/redirect at driver level (before sk_buff allocation)
- `perf_event`: CPU performance counter sampling
- `socket filter`: Filter packets per socket
- `lsm`: Security policy (BPF-LSM)
- `cgroup`: Per-cgroup resource control

### eBPF Program — C (Simple syscall tracer)

```c
/* Compile with: clang -O2 -target bpf -c prog.c -o prog.o */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* Map: pid → syscall count */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, __u32);
    __type(value, __u64);
} syscall_count SEC(".maps");

/* Attach to raw syscall entry tracepoint */
SEC("tracepoint/raw_syscalls/sys_enter")
int count_syscalls(struct trace_event_raw_sys_enter *ctx) {
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u64 *count = bpf_map_lookup_elem(&syscall_count, &pid);
    
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 initial = 1;
        bpf_map_update_elem(&syscall_count, &pid, &initial, BPF_ANY);
    }
    return 0;
}

/* XDP program: drop all TCP SYN packets to port 80 (simple firewall) */
SEC("xdp")
int xdp_syn_drop(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != __constant_htons(ETH_P_IP)) return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;
    
    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end) return XDP_PASS;
    
    /* Drop SYN packets to port 80 */
    if (tcp->dest == __constant_htons(80) && tcp->syn && !tcp->ack)
        return XDP_DROP;
    
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

---

# 15. Advanced Kernel Algorithms — Deep Dives

## 15.1 The Scheduler: O(1) vs CFS vs EEVDF

### Historical O(1) Scheduler (2.5-2.6.22)

```
Two priority arrays per runqueue:
  active[140]   ← tasks that haven't used their time slice
  expired[140]  ← tasks that have

Priority 0-99: real-time
Priority 100-139: CFS (nice -20 to +19)

Each priority level: linked list of tasks

Scheduling: find_first_bit(active->bitmap) → dequeue from active[prio]
  If expired, put in expired[prio]
  When active is empty: swap(active, expired)

O(1): find_first_bit on 140-bit bitmap = 3 × 64-bit BSF instructions
```

**Problem:** The heuristics for "interactive" tasks (boosting priority for I/O-bound tasks) were fragile and gamed by some workloads.

### Why CFS is Better

CFS makes no distinction between "interactive" and "CPU-bound" — it simply tracks who's been running the most (vruntime) and runs whoever hasn't. I/O-bound tasks naturally accumulate less vruntime (they sleep), so they're scheduled preferentially upon waking. No heuristics needed.

### EEVDF (6.6+)

**Problem with CFS:** The min-vruntime lag bound is O(n log n) — with many tasks, a task could wait many times its share before getting scheduled. CFS also has "latency" issues: a task might not run for 2× its target_latency under heavy load.

**EEVDF solution:** A task becomes "eligible" when its vruntime matches the global minimum (it's "owed" CPU). Among eligible tasks, pick the one with the **earliest virtual deadline** (when it should be done).

```
Virtual finish time = vruntime + slice / weight × NICE_0_WEIGHT
Task is eligible when: vruntime <= min_vruntime
Schedule: min(v_deadline) among eligible tasks
```

This bounds both lag and latency, with better theoretical guarantees.

## 15.2 Memory Compaction — Defragmentation Algorithm

Over time, free memory fragments — the buddy system can't satisfy large allocations even when enough total memory is free. **Compaction** migrates movable pages to consolidate free blocks.

```
Before:
  [USED][USED][FREE][USED][FREE][FREE][USED][USED][FREE]

After compaction:
  [USED][USED][USED][USED][USED][FREE][FREE][FREE][FREE]

Algorithm:
  1. Start two scanners: free_scanner (from top) and migrate_scanner (from bottom)
  2. migrate_scanner finds movable pages
  3. free_scanner finds free pages in upper zone
  4. Move page content, update all reverse mappings (rmap)
  5. Continue until scanners meet
```

**RMAP (Reverse Map):** For each physical page, the kernel needs to find ALL PTEs pointing to it (multiple processes may have the same page mapped). RMAP is a data structure that provides this mapping, used during page migration and reclaim.

## 15.3 Lockdep — Lock Dependency Validator

Linux's `lockdep` system validates at runtime that the locking order is consistent (to detect potential deadlocks before they occur):

```
Thread A: lock(X) then lock(Y)
Thread B: lock(Y) then lock(X)
→ Potential deadlock (circular dependency X→Y and Y→X)

lockdep detects:
  When thread A acquires X then Y: records edge X→Y in dependency graph
  When thread B tries to acquire X while holding Y:
    DFS from Y → detects path Y→X (from previous recording)
    → WARN (cycle detected!) even if deadlock hasn't happened yet
```

This has found hundreds of real deadlock bugs over the kernel's history. The key insight is detecting the **dependency cycle** before the actual deadlock — deterministic detection vs. probabilistic occurrence.

## 15.4 RCU — Read-Copy-Update Detailed Analysis

RCU is the most sophisticated synchronization mechanism in the Linux kernel. Understanding it deeply is a mark of expert systems knowledge.

### The Grace Period Problem

```
Timeline:
  t0: reader R1 starts, holds reference to old_ptr
  t1: writer updates: new_ptr = alloc(); *new_ptr = update(*old_ptr); rcu_assign_pointer(gp, new_ptr)
  t2: writer calls synchronize_rcu()
  t3: reader R2 starts (sees new_ptr due to memory barrier in rcu_assign_pointer)
  t4: reader R1 ends
  t5: synchronize_rcu() returns (grace period complete — R1 has ended)
  t6: kfree(old_ptr) — SAFE: no readers can see old_ptr anymore
```

The grace period is defined as: "all RCU read-side critical sections that began before the grace period started have completed."

### Quiescent States

On non-preemptive kernels, a **context switch** is a quiescent state — a task cannot hold an RCU read-side lock across a context switch. Therefore:

```
Grace period ends when: every CPU has had at least one context switch 
                        since the grace period began.

Implementation:
  1. Record current jiffies (grace_period_start)
  2. Send IPI to all CPUs (or wait for CPU to idle)
  3. Track per-CPU "qs_mask" — bit cleared when CPU has quiesced
  4. When all bits cleared → grace period over → call RCU callbacks
```

**Hierarchical RCU (tree RCU):** On systems with 1000+ CPUs, checking all CPUs is expensive. Tree RCU uses a tree of "rcu_node" structures — leaf nodes track individual CPUs, internal nodes aggregate. A grace period completes when the root node is quiesced.

## 15.5 Per-CPU Variables — Cache-Line Optimization

One of the most important performance optimizations in the kernel: per-CPU variables eliminate cache-line contention.

```c
/* Declare per-CPU variable */
DEFINE_PER_CPU(int, my_counter);

/* Access (must disable preemption to prevent migration) */
int val = get_cpu_var(my_counter);
get_cpu_var(my_counter)++;
put_cpu_var(my_counter);

/* Or raw access (in preemption-disabled context) */
this_cpu_inc(my_counter);
```

**Why per-CPU eliminates cache contention:**
- Global counter: all CPUs read-modify-write the same cache line → MESI protocol bouncing → O(n) time for n CPUs to increment
- Per-CPU: each CPU has its own cache line → no coherency traffic → O(1) regardless of CPU count

Example: `jiffies` updates, scheduler statistics, network statistics — all use per-CPU variables.

### Per-CPU Variables — Rust Simulation

```rust
use std::cell::Cell;
use std::sync::Arc;

/// Simulated per-CPU storage using thread-local storage
/// In kernel: __per_cpu_offset[cpu] + variable offset
thread_local! {
    static CPU_COUNTER: Cell<u64> = Cell::new(0);
    static CPU_RX_BYTES: Cell<u64> = Cell::new(0);
    static CPU_TX_BYTES: Cell<u64> = Cell::new(0);
}

pub fn this_cpu_inc_counter() {
    CPU_COUNTER.with(|c| c.set(c.get() + 1));
}

pub fn this_cpu_add_rx(bytes: u64) {
    CPU_RX_BYTES.with(|c| c.set(c.get() + bytes));
}

pub fn this_cpu_add_tx(bytes: u64) {
    CPU_TX_BYTES.with(|c| c.set(c.get() + bytes));
}

/// Aggregate statistics across all "CPUs" (threads)
pub struct PercpuStats {
    counters: Vec<Arc<std::sync::atomic::AtomicU64>>,
}

impl PercpuStats {
    pub fn new(num_cpus: usize) -> Self {
        PercpuStats {
            counters: (0..num_cpus)
                .map(|_| Arc::new(std::sync::atomic::AtomicU64::new(0)))
                .collect(),
        }
    }
    
    pub fn get(&self, cpu: usize) -> &std::sync::atomic::AtomicU64 {
        &self.counters[cpu]
    }
    
    /// Aggregate: sum across all CPUs
    pub fn sum(&self) -> u64 {
        self.counters.iter()
            .map(|c| c.load(std::sync::atomic::Ordering::Relaxed))
            .sum()
    }
    
    /// Reset: zero all per-CPU values
    pub fn reset(&self) {
        for c in &self.counters {
            c.store(0, std::sync::atomic::Ordering::Relaxed);
        }
    }
}
```

## 15.6 Waitqueues — Event-Based Sleeping

Waitqueues are the mechanism by which tasks sleep waiting for an event:

```c
/* Declare a wait queue */
DECLARE_WAIT_QUEUE_HEAD(my_queue);

/* Wait until condition is true */
wait_event_interruptible(my_queue, condition_is_true());
/* Internally:
   1. Check condition (under protection)
   2. If false: add task to wait queue, set state to TASK_INTERRUPTIBLE
   3. schedule() → give up CPU
   4. On wake: check condition again (loop — avoid spurious wakeups)
*/

/* Wake tasks sleeping on this queue */
wake_up(&my_queue);
/* Internally: walk wait queue, set each task TASK_RUNNING, dequeue */
```

**Thundering herd:** If 1000 tasks wait on one condition and `wake_up_all()` is called, all 1000 are woken — but only one can proceed. The others find the condition false and go back to sleep.

**`wake_up()` vs `wake_up_all()`:**
- `wake_up()`: wakes first exclusive waiter + all non-exclusive waiters
- `wake_up_all()`: wakes everyone (causes thundering herd)

The `WQ_FLAG_EXCLUSIVE` flag marks a waiter as exclusive — only one is woken per `wake_up()`. Used for resources where only one consumer should wake.

### Waitqueue — Rust Implementation

```rust
use std::collections::VecDeque;
use std::sync::{Condvar, Mutex, Arc};

/// Wait queue — tasks sleep here waiting for an event
pub struct WaitQueue<T> {
    inner: Arc<(Mutex<WaitQueueInner<T>>, Condvar)>,
}

struct WaitQueueInner<T> {
    queue:     VecDeque<T>,
    condition: bool,
}

impl<T: Clone> WaitQueue<T> {
    pub fn new() -> Self {
        WaitQueue {
            inner: Arc::new((
                Mutex::new(WaitQueueInner {
                    queue:     VecDeque::new(),
                    condition: false,
                }),
                Condvar::new(),
            )),
        }
    }
    
    pub fn clone_handle(&self) -> Self {
        WaitQueue { inner: self.inner.clone() }
    }
    
    /// Sleep until condition is set (like wait_event)
    pub fn wait(&self) -> Option<T> {
        let (lock, cvar) = &*self.inner;
        let mut guard = lock.lock().unwrap();
        
        loop {
            if let Some(item) = guard.queue.pop_front() {
                return Some(item);
            }
            // Spurious wakeup protection: always re-check
            guard = cvar.wait(guard).unwrap();
        }
    }
    
    /// Wake one waiter (like wake_up)
    pub fn wake_one(&self, item: T) {
        let (lock, cvar) = &*self.inner;
        let mut guard = lock.lock().unwrap();
        guard.queue.push_back(item);
        drop(guard);
        cvar.notify_one();
    }
    
    /// Wake all waiters (like wake_up_all — use carefully!)
    pub fn wake_all(&self, item: T) {
        let (lock, cvar) = &*self.inner;
        let mut guard = lock.lock().unwrap();
        // In kernel: each waiter gets an independent wake
        // Here we broadcast the same item (simplified)
        guard.queue.push_back(item);
        drop(guard);
        cvar.notify_all();
    }
}
```

---

# 16. Performance Engineering & Profiling

## 16.1 perf — Linux Performance Analysis

`perf` is the primary Linux performance analysis tool, built on the perf_events kernel subsystem.

```bash
# CPU profiling — statistical sampling
perf record -g -F 999 ./myprogram  # sample at 999 Hz with call graph
perf report --stdio               # view flamegraph-ready output

# Hardware performance counters
perf stat -e \
    cache-references,cache-misses,\
    branch-instructions,branch-misses,\
    instructions,cycles \
    ./myprogram

# Tracing specific events
perf trace -e openat,read,write ./myprogram  # trace syscalls

# Dynamic tracing (kprobe)
perf probe --add 'tcp_retransmit_skb'
perf record -e probe:tcp_retransmit_skb -ag sleep 10
perf script
```

**Key metrics to understand:**
- **IPC (Instructions Per Cycle):** > 2 is good for modern OoO CPUs. < 1 suggests memory-bound.
- **Cache miss rate:** L1: ~4 cycles, L2: ~12 cycles, L3: ~40 cycles, RAM: ~200 cycles
- **Branch misprediction rate:** Misprediction costs ~15-20 cycles on modern CPUs.

## 16.2 Cache-Conscious Data Structure Design

**Cache line size:** 64 bytes on x86_64. Accessing any byte brings in the entire 64-byte line.

**Practical rules:**
1. **Hot data together:** Fields accessed together should be in the same cache line
2. **Cold data separate:** Rarely accessed fields (error paths, config) in separate structs
3. **False sharing:** Two threads writing different fields in the same cache line causes coherency traffic even though they're "different" data
4. **Alignment:** Align structs to cache line size with `__aligned(64)` or Rust's `#[repr(align(64))]`

```c
/* Bad: hot and cold data mixed */
struct task_struct_bad {
    int pid;              /* hot */
    char name[16];        /* hot */
    char padding[32];     /* rare metadata */
    long creation_time;   /* cold */
    /* ... 700 more fields ... */
    int on_cpu;           /* HOT: checked constantly */
};
/* on_cpu might be on a different cache line than pid */

/* Good: separate hot/cold */
struct task_hot {
    int pid;
    int on_cpu;
    u64 vruntime;
} __attribute__((aligned(64)));  /* own cache line */

struct task_cold {
    long creation_time;
    char audit_data[64];
    /* ... */
};
```

### False Sharing Example — Rust

```rust
use std::sync::Arc;
use std::thread;

/// Demonstrates false sharing and how to fix it
#[repr(C)]
struct BadCounters {
    a: u64,  // Thread 1 writes this
    b: u64,  // Thread 2 writes this
    // Both on same 64-byte cache line → false sharing!
}

#[repr(C, align(64))]
struct PaddedCounter {
    value: u64,
    _pad:  [u8; 56],  // Pad to 64 bytes — own cache line
}

struct GoodCounters {
    a: PaddedCounter,  // Thread 1 writes → own cache line
    b: PaddedCounter,  // Thread 2 writes → different cache line
}

pub fn benchmark_false_sharing() {
    let bad = Arc::new(unsafe {
        std::mem::MaybeUninit::<BadCounters>::zeroed().assume_init()
    });
    
    // In benchmark: updating a and b from separate threads
    // BadCounters:  ~800ns per increment (cache line bouncing between CPUs)
    // GoodCounters: ~2ns per increment (each CPU owns its cache line)
}
```

## 16.3 Memory Barriers and the Compiler

Memory barriers have two components:
1. **CPU memory barrier:** Prevents CPU reordering
2. **Compiler barrier:** Prevents compiler reordering (different from CPU!)

```c
/* Compiler barrier only (no CPU instruction) */
barrier();  /* = asm volatile("" ::: "memory") */

/* CPU + compiler barrier */
smp_mb();   /* full barrier (mfence on x86) */
smp_rmb();  /* read barrier */
smp_wmb();  /* write barrier */

/* x86 subtlety: only StoreLoad requires mfence.
 * LoadLoad, LoadStore, StoreStore are free on x86 (TSO model)
 * But compiler might still reorder → need at minimum barrier()
 */
```

**Acquire/Release semantics:**
```c
/* Producer */
data = prepare();
smp_wmb();          /* ensure data visible before flag */
flag = 1;           /* release */

/* Consumer */
while (!flag);      /* poll */
smp_rmb();          /* acquire: ensure we see data after flag */
use(data);
```

On x86, `smp_rmb()` and `smp_wmb()` are free (just compiler barriers). On ARM, they generate `dmb ish` instructions.

## 16.4 Profiling with ftrace

ftrace is the kernel's built-in function tracer:

```bash
# Enable function tracing
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Run workload
./myworkload

# Disable and view
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace | head -100

# Trace specific function + callgraph
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo 'tcp_*' > /sys/kernel/debug/tracing/set_ftrace_filter
echo 3 > /sys/kernel/debug/tracing/max_graph_depth
echo 1 > /sys/kernel/debug/tracing/tracing_on
```

**ftrace implementation:** The kernel compiles with `-pg` (or uses `nop` → `call mcount` patching). At compile time, each function begins with a `nop` (5-byte on x86). When ftrace is enabled, these nops are **live-patched** to `call ftrace_caller` using the `stop_machine()` mechanism (pauses all CPUs simultaneously for the patch). When disabled, patched back to `nop`. Zero overhead when disabled!

## 16.5 NUMA — Non-Uniform Memory Access

Modern multi-socket servers have NUMA topology: memory access latency depends on which NUMA node the memory is on.

```
Socket 0:
  CPUs 0-7
  RAM 0: 64 GB  (local access: 50ns)
  
Socket 1:
  CPUs 8-15
  RAM 1: 64 GB  (local to socket 1)

CPU 0 accessing RAM 1: 100ns (remote — must traverse QPI/UPI bus)
```

Linux NUMA awareness:
- `numa_node`: each `struct zone` belongs to a node
- Scheduler tries to keep tasks near their memory (`sched_domain` hierarchy)
- `numactl --cpubind=0 --membind=0 ./program` — bind process to NUMA node 0
- `libnuma` / `mbind()` syscall — per-VMA memory placement policy

**NUMA balancing (automatic):** Linux periodically scans memory access patterns and migrates pages to the NUMA node where they're most accessed. Cost: page faults during scan, migration overhead.

### NUMA-Aware Allocator Simulation — Go

```go
package numa

import (
    "runtime"
    "sync"
)

type NumaNode struct {
    id      int
    memory  []byte    // simulated local memory pool
    mu      sync.Mutex
    offset  int
}

func NewNumaNode(id int, sizeBytes int) *NumaNode {
    return &NumaNode{
        id:     id,
        memory: make([]byte, sizeBytes),
    }
}

func (n *NumaNode) Alloc(size int) []byte {
    n.mu.Lock()
    defer n.mu.Unlock()
    
    if n.offset+size > len(n.memory) {
        return nil // OOM on this node
    }
    buf := n.memory[n.offset : n.offset+size]
    n.offset += size
    return buf
}

type NumaAllocator struct {
    nodes []*NumaNode
    numCPU int
}

func NewNumaAllocator(numNodes int, memPerNode int) *NumaAllocator {
    nodes := make([]*NumaNode, numNodes)
    for i := range nodes {
        nodes[i] = NewNumaNode(i, memPerNode)
    }
    return &NumaAllocator{
        nodes:  nodes,
        numCPU: runtime.NumCPU(),
    }
}

// Simulate: allocate from local NUMA node based on CPU affinity
func (a *NumaAllocator) AllocLocal(size int) []byte {
    // In real kernel: use numa_node_id() to get current CPU's NUMA node
    // Here: use goroutine ID mod numNodes as approximation
    nodeID := goroutineID() % len(a.nodes)
    
    buf := a.nodes[nodeID].Alloc(size)
    if buf != nil {
        return buf
    }
    
    // Fallback to any available node
    for _, node := range a.nodes {
        if buf = node.Alloc(size); buf != nil {
            return buf
        }
    }
    return nil
}

func goroutineID() int {
    // Simplified: in production use runtime_pollDesc or similar
    return 0
}
```

## 16.6 Lock Contention Analysis

Understanding lock contention is critical for scalable systems design:

```
Lock contention modes:
1. Uncontended (fast path): Single atomic operation
2. Contested (slow path): CAS loop or sleep in wait queue
3. High contention: Many CPUs spinning → cache line bouncing → poor scaling

Measurement:
  perf lock record ./program
  perf lock report

Output:
  Name    acquired  contended  avg_wait(ms)  total_wait(ms)
  ...
  pthread_mutex_lock  1000000  50000  0.002  100ms

Contention rate = 50000/1000000 = 5% → acceptable
If > 20% → consider:
  - Lock-free data structure
  - Per-CPU data + aggregation
  - Finer-grained locking (lock striping)
  - Reader-writer locks if mostly reads
  - RCU for read-heavy workloads
```

**Lock striping:** Instead of one lock protecting all data, use N locks — each protecting 1/N of the data. Contention reduced by N.

```go
package striped

import "sync"

type StripedMutex struct {
    locks [256]struct {
        sync.Mutex
        _pad [56]byte  // pad to cache line
    }
}

func (s *StripedMutex) Lock(key uint64) {
    s.locks[key&255].Lock()
}

func (s *StripedMutex) Unlock(key uint64) {
    s.locks[key&255].Unlock()
}

// Striped hash map: 256x reduced contention
type StripedHashMap struct {
    mu     StripedMutex
    shards [256]map[string]int
}

func NewStripedHashMap() *StripedHashMap {
    m := &StripedHashMap{}
    for i := range m.shards {
        m.shards[i] = make(map[string]int)
    }
    return m
}

func hash(key string) uint64 {
    h := uint64(14695981039346656037)
    for _, c := range []byte(key) {
        h ^= uint64(c)
        h *= 1099511628211
    }
    return h
}

func (m *StripedHashMap) Get(key string) (int, bool) {
    h := hash(key)
    m.mu.Lock(h)
    defer m.mu.Unlock(h)
    v, ok := m.shards[h&255][key]
    return v, ok
}

func (m *StripedHashMap) Set(key string, val int) {
    h := hash(key)
    m.mu.Lock(h)
    defer m.mu.Unlock(h)
    m.shards[h&255][key] = val
}
```

---

## Appendix A: Kernel Data Structure Quick Reference

| Structure | Location | Used for | Key Operation |
|-----------|----------|----------|---------------|
| `list_head` | `<linux/list.h>` | Generic linked lists | O(1) insert/delete |
| `hlist_head/node` | `<linux/list.h>` | Hash table buckets | O(1) insert/delete |
| `rb_root/node` | `<linux/rbtree.h>` | Sorted sets | O(log n) find |
| `xarray` | `<linux/xarray.h>` | Sparse arrays | O(log n) |
| `radix_tree_root` | (legacy) | Page cache (old) | O(log n) |
| `bitmap` | `<linux/bitmap.h>` | CPU/IRQ masks | O(n/64) scan |
| `cpumask_t` | `<linux/cpumask.h>` | CPU sets | O(n/64) |
| `wait_queue_head_t` | `<linux/wait.h>` | Task sleeping | O(n) wake |
| `work_struct` | `<linux/workqueue.h>` | Deferred work | O(1) queue |
| `kfifo` | `<linux/kfifo.h>` | Lock-free SPSC queue | O(1) |
| `percpu_counter` | `<linux/percpu_counter.h>` | Approximate counters | O(1) update |

## Appendix B: Critical Kernel Configuration Parameters

```bash
# Memory
/proc/sys/vm/swappiness           # 0-100: preference for swap vs file reclaim
/proc/sys/vm/dirty_ratio          # % RAM that can be dirty before forced writeback
/proc/sys/vm/overcommit_memory    # 0=heuristic, 1=always allow, 2=never overcommit
/proc/sys/vm/min_free_kbytes      # reserved free memory for atomic allocations

# Networking
/proc/sys/net/core/rmem_max       # max socket receive buffer
/proc/sys/net/core/wmem_max       # max socket send buffer
/proc/sys/net/core/netdev_max_backlog  # packet queue length per CPU
/proc/sys/net/ipv4/tcp_syncookies # SYN flood protection
/proc/sys/net/ipv4/tcp_congestion_control  # cubic, bbr, reno...

# Scheduling
/proc/sys/kernel/sched_min_granularity_ns  # minimum scheduling quantum
/proc/sys/kernel/sched_latency_ns          # target scheduling latency
/proc/sys/kernel/sched_migration_cost_ns   # cost threshold for task migration
/proc/sys/kernel/numa_balancing            # automatic NUMA balancing

# I/O
/sys/block/sda/queue/scheduler    # I/O scheduler selection
/sys/block/sda/queue/nr_requests  # queue depth
/sys/block/sda/queue/read_ahead_kb  # readahead size
```

## Appendix C: Essential Kernel Debugging Commands

```bash
# Process and scheduling
cat /proc/schedstat           # per-CPU scheduler statistics
cat /proc/sched_debug         # CFS runqueue state
cat /proc/loadavg             # load average
ps -eo pid,pcpu,pmem,vsz,rss,stat,comm  # process details

# Memory
cat /proc/meminfo             # memory overview
cat /proc/buddyinfo           # buddy allocator state (fragmentation)
cat /proc/slabinfo            # SLAB/SLUB allocator stats
cat /proc/vmstat              # virtual memory statistics
cat /proc/zoneinfo            # per-zone memory breakdown
numastat                      # NUMA statistics

# Networking
ss -tunapw                    # socket statistics
cat /proc/net/dev             # per-interface statistics
cat /proc/net/tcp             # TCP connection table
netstat -s                    # protocol statistics
nstat                         # network statistics

# I/O
iostat -xz 1                  # I/O statistics
iotop -ao                     # per-process I/O
cat /proc/diskstats           # raw disk statistics
blktrace -d /dev/sda          # block layer tracing

# Kernel internals
dmesg -T                      # kernel ring buffer with timestamps
cat /proc/interrupts          # interrupt statistics per CPU
cat /proc/softirqs            # softirq statistics
cat /proc/locks               # file locks held
lsmod                         # loaded kernel modules
cat /sys/kernel/debug/tracing/trace  # ftrace output
```

## Appendix D: Complexity Reference for Linux Kernel Operations

| Operation | Data Structure | Time Complexity | Notes |
|-----------|---------------|-----------------|-------|
| PID lookup | XArray (radix tree) | O(log n) | n = max PID |
| VMA lookup | Red-black tree | O(log n) | n = # VMAs |
| Page cache lookup | XArray | O(log n) | n = file size |
| CFS next task | Red-black tree | O(log n) | n = # runnable |
| Timer lookup | Red-black tree (hrtimer) | O(log n) | n = # timers |
| Inode cache lookup | Hash table | O(1) avg | load factor < 0.75 |
| Dentry cache lookup | Hash table | O(1) avg | per path component |
| Physical page alloc | Buddy system | O(log MAX_ORDER) | ≈ O(1) |
| kmalloc (slab) | SLUB/SLAB | O(1) | per-CPU fast path |
| Netfilter hook | Linked list | O(n) | n = # rules |
| Routing lookup | LC-trie | O(1) avg | |
| Symbol lookup | Hash table | O(1) avg | kallsyms |
| Module load | Linked list + hash | O(n) modules | |

---

## Final Words: The Mental Model of a Kernel Expert

> *Every kernel subsystem is a carefully balanced system of trade-offs — between latency and throughput, between memory and CPU, between simplicity and scalability.*

The Linux kernel is the most studied and most carefully engineered piece of software in existence. To master it is to master:

1. **Every major data structure** — lists, trees, hash tables, queues — all used optimally
2. **Every fundamental algorithm** — sorting, searching, graph traversal, string matching — all with bounded, predictable complexity
3. **Hardware-software co-design** — TLBs, cache hierarchies, NUMA, CPU pipelines
4. **Concurrency theory** — happens-before, memory models, lock-free algorithms, RCU
5. **Systems engineering** — error handling, resource management, modularity, testing

Study the kernel not to memorize it, but to *internalize its design philosophy*: solve the problem correctly first, then make it fast, then make it scale. Every optimization in the kernel exists because someone measured a real bottleneck. Premature optimization is as dangerous in the kernel as anywhere else.

The path to the top 1% is not knowing more facts — it is developing the ability to look at a problem and immediately perceive its underlying structure, the correct data structure, the correct algorithm, the correct trade-offs. The kernel is your training ground.

---

*Guide version 1.0 — Linux Kernel 6.x reference*
*All code examples are educational implementations — production kernel code has additional error handling, synchronization, and architecture-specific optimizations.*

