# Deep Performance Comparison: Shared Memory vs Unix Domain Sockets vs TCP
### A Kernel-Level, Systems-Programming Master Reference
> *Target: C · Rust · Go — Linux internals — gRPC concepts — Production-grade code*

---

## Table of Contents

1. [Mental Model: What Is IPC?](#1-mental-model-what-is-ipc)
2. [The Linux Memory Architecture — Foundation](#2-the-linux-memory-architecture--foundation)
3. [Shared Memory — Zero-Copy IPC](#3-shared-memory--zero-copy-ipc)
   - 3.1 POSIX Shared Memory (`shm_open`)
   - 3.2 `mmap` — The Real Mechanism
   - 3.3 SysV Shared Memory (Legacy)
   - 3.4 Kernel Internals: Page Tables & TLB
   - 3.5 Synchronization Primitives
   - 3.6 Ring Buffer Pattern (Lock-Free)
   - 3.7 C, Rust, Go Implementations
4. [Unix Domain Sockets (UDS)](#4-unix-domain-sockets-uds)
   - 4.1 What UDS Actually Is
   - 4.2 Socket Types: STREAM vs DGRAM vs SEQPACKET
   - 4.3 Kernel Path: send() → receive()
   - 4.4 SCM_RIGHTS: File Descriptor Passing
   - 4.5 Abstract Namespace
   - 4.6 C, Rust, Go Implementations
5. [TCP Sockets](#5-tcp-sockets)
   - 5.1 Loopback Interface (127.0.0.1)
   - 5.2 Full Kernel Network Stack Path
   - 5.3 TCP State Machine & Overhead
   - 5.4 Nagle's Algorithm & TCP_NODELAY
   - 5.5 SO_REUSEPORT & Socket Options
   - 5.6 C, Rust, Go Implementations
6. [gRPC — Transport Layer Concepts](#6-grpc--transport-layer-concepts)
   - 6.1 What gRPC Is (Protocol Layers)
   - 6.2 HTTP/2 Framing & Multiplexing
   - 6.3 Protobuf Serialization
   - 6.4 gRPC over UDS
   - 6.5 gRPC over TCP
   - 6.6 Go gRPC Implementation
7. [Kernel-Level Performance Analysis](#7-kernel-level-performance-analysis)
   - 7.1 System Call Overhead
   - 7.2 Context Switches
   - 7.3 Cache Behavior (L1/L2/L3)
   - 7.4 NUMA Topology Impact
   - 7.5 Memory Allocation Patterns
8. [Quantitative Performance Comparison](#8-quantitative-performance-comparison)
9. [Decision Framework](#9-decision-framework)
10. [Advanced Patterns](#10-advanced-patterns)
    - 10.1 io_uring for UDS/TCP
    - 10.2 Huge Pages with Shared Memory
    - 10.3 CPU Pinning & Affinity
11. [Complete Benchmark Harness in C](#11-complete-benchmark-harness-in-c)
12. [Mental Models for Experts](#12-mental-models-for-experts)

---

## 1. Mental Model: What Is IPC?

**IPC = Inter-Process Communication.** When two separate OS processes need to exchange data, they cannot simply share a variable — each process has its own **virtual address space**, isolated by the MMU (Memory Management Unit). The kernel must act as a broker.

```
Process A                    Kernel                    Process B
[Virtual Space A]   ──────→  [Broker]  ──────→   [Virtual Space B]
  0x0000 - 0xFFFF                                   0x0000 - 0xFFFF
```

> **Key insight:** Every IPC mechanism differs in *where* the data lives during transit, *how many times* it is copied, and *what kernel subsystem* mediates access.

### The Three Contenders at a Glance

```
┌──────────────────┬──────────────┬────────────────┬─────────────────────┐
│ Mechanism        │ Data Copies  │ Kernel Syscalls│ Who Mediates?       │
├──────────────────┼──────────────┼────────────────┼─────────────────────┤
│ Shared Memory    │ 0            │ 0 (after setup)│ MMU / page table    │
│ UDS              │ 1 (internal) │ 2 (send+recv)  │ VFS / socket layer  │
│ TCP (loopback)   │ 2            │ 2+             │ Full network stack  │
└──────────────────┴──────────────┴────────────────┴─────────────────────┘
```

---

## 2. The Linux Memory Architecture — Foundation

Before diving into each IPC mechanism, you must understand how Linux manages memory. Every IPC mechanism exploits or works around this architecture.

### 2.1 Virtual vs Physical Address Space

Every process sees a **virtual address space** — a fiction maintained by the kernel. The hardware MMU translates virtual addresses → physical addresses using **page tables**.

```
Virtual Address Space (per process, 64-bit):
┌───────────────────────────┐  0xFFFFFFFFFFFFFFFF
│  Kernel Space (128 TB)    │  ← only kernel can access
├───────────────────────────┤  0xFFFF800000000000
│  (non-canonical hole)     │
├───────────────────────────┤  0x00007FFFFFFFFFFF
│  Stack                    │  ← grows downward
│  ...                      │
│  mmap region              │  ← shared libs, shm, mmap files
│  ...                      │
│  Heap                     │  ← malloc/new
│  BSS / Data / Text        │  ← program code & globals
└───────────────────────────┘  0x0000000000000000
```

### 2.2 Pages — The Fundamental Unit

The MMU works in **pages** (usually 4 KB on x86-64, optionally 2 MB or 1 GB with huge pages). A page is the smallest unit of memory that can be:
- Mapped into a process
- Swapped to disk
- Made read-only, writable, executable

**Why this matters for IPC:** Shared memory works by mapping the *same physical page* into *two different virtual address spaces*. No copy — the physical RAM is literally shared.

### 2.3 The TLB — Translation Lookaside Buffer

The TLB is a hardware cache inside the CPU that caches recent virtual→physical translations. It has:
- **L1 TLB:** ~64 entries, 1 cycle latency
- **L2 TLB:** ~1536 entries, ~7 cycle latency
- **Page walk (miss):** 100+ cycles

**TLB shootdown** — when a mapping changes (e.g., you `munmap` shared memory), the kernel must invalidate TLB entries on *all CPUs* currently running that process. This is an expensive cross-CPU IPI (Inter-Processor Interrupt) and is why shared memory setup/teardown has overhead even though steady-state access is fast.

### 2.4 Cache Hierarchy

```
Register (0 cycles)
    │
L1 Cache  ─── 32 KB, 4 cycles latency,   line = 64 bytes
    │
L2 Cache  ─── 256 KB, 12 cycles latency
    │
L3 Cache  ─── 8–32 MB, 40 cycles latency  (shared between cores)
    │
DRAM      ─── GBs, ~100 cycles latency
    │
NVMe SSD  ─── TBs, ~10,000 cycles
```

**Cache line = 64 bytes.** When you read one byte, the entire 64-byte cache line is loaded. This means:
- Reading sequential memory is fast (prefetcher kicks in)
- Random access is slow (cache miss each time)
- **False sharing**: Two variables on the same cache line, written by different CPUs, cause constant cache invalidation even if they're logically independent

---

## 3. Shared Memory — Zero-Copy IPC

### 3.1 What Is Shared Memory?

Shared memory is the **fastest IPC mechanism** because it involves **zero copies** after setup. The same physical memory pages are mapped into multiple process address spaces. When Process A writes to address `0x7f000000`, it directly modifies RAM that Process B sees at (potentially different) address `0x7f800000` — no kernel involvement.

```
Physical RAM
┌─────────────────────────────┐
│   Page Frame #4521          │  ← one physical page
│   [producer_data ............│
│    ring buffer state ........│
│    consumer_data ............│
└─────────────────────────────┘
         ↑                ↑
         │                │
[Process A]          [Process B]
 virtual: 0x7f00      virtual: 0x7f80
 "sees" same RAM       "sees" same RAM
```

### 3.2 `mmap` — The Real Kernel Mechanism

**`mmap`** (memory-mapped file/anonymous) is the fundamental Linux system call behind all shared memory:

```c
void *mmap(void *addr,    // suggested address (NULL = kernel picks)
           size_t length, // how many bytes to map
           int prot,      // PROT_READ | PROT_WRITE | PROT_EXEC
           int flags,     // MAP_SHARED | MAP_PRIVATE | MAP_ANONYMOUS
           int fd,        // file descriptor (-1 for anonymous)
           off_t offset); // offset into file
```

**Flags explained:**
- `MAP_SHARED` — writes are visible to other processes mapping the same backing (essential for IPC)
- `MAP_PRIVATE` — copy-on-write; writes are private to this process
- `MAP_ANONYMOUS` — not backed by a file; backed by anonymous pages (RAM only, no file)
- `MAP_HUGETLB` — use huge pages (reduces TLB pressure)
- `MAP_LOCKED` — lock pages in RAM (prevent swap; requires `CAP_IPC_LOCK`)
- `MAP_POPULATE` — fault-in pages immediately (avoid page faults later)

**The kernel path for `mmap`:**
1. Kernel creates a `vm_area_struct` (VMA) — a descriptor for this virtual region
2. No physical memory allocated yet (lazy allocation — demand paging)
3. First access triggers a **page fault** → kernel allocates a physical page frame → updates page tables → returns to userspace
4. Subsequent accesses: TLB hit → direct DRAM access, zero kernel involvement

### 3.3 POSIX Shared Memory (`shm_open`)

POSIX shared memory uses a named object in `/dev/shm` (a `tmpfs` filesystem in RAM):

```c
// Conceptual flow:
int fd = shm_open("/my_shm", O_CREAT | O_RDWR, 0600);
ftruncate(fd, SIZE);                        // set size
void *ptr = mmap(NULL, SIZE, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
close(fd);  // fd no longer needed after mmap

// Access directly — no syscall:
((int*)ptr)[0] = 42;
```

`/dev/shm` is `tmpfs` — a filesystem that lives entirely in RAM (and swap if needed). `shm_open` is simply `open("/dev/shm/my_shm", ...)` with some validation. The resulting fd points to an inode on tmpfs, and `mmap` maps those tmpfs pages.

**Lifecycle:**
- Object persists until explicitly `shm_unlink`ed (survives process death)
- Visible in `/dev/shm/` — can cause memory leaks if process crashes without cleanup

### 3.4 SysV Shared Memory (Legacy)

Older API, still widely used. Uses integer keys instead of names:

```c
key_t key = ftok("/tmp/myapp", 'A');  // generate key from path+id
int shmid = shmget(key, SIZE, IPC_CREAT | 0600);
void *ptr = shmat(shmid, NULL, 0);    // attach
// use ptr...
shmdt(ptr);                           // detach
shmctl(shmid, IPC_RMID, NULL);        // destroy
```

**Kernel internals (SysV shm):**
- Each segment has a `shmid_ds` structure in kernel memory
- `shmat` calls `mmap` internally — same page table mechanism
- Visible via `ipcs -m` command
- Survives process death unless `IPC_RMID` called or system reboots

### 3.5 Kernel Internals: Page Tables & TLB on Shared Memory Access

When Process A writes to shared memory:

```
Process A writes to virtual 0x7f000000
    │
    ▼
CPU checks TLB:
  HIT?  → Directly access physical page (0 cycles kernel overhead)
  MISS? → Page table walk:
          PGD → PUD → PMD → PTE → Physical address
          Cost: 100–200 ns (multiple DRAM accesses)
          TLB entry updated
    │
    ▼
Write to physical page frame
Cache coherency protocol (MESI) ensures other CPU cores see the write
```

**False sharing in shared memory (critical performance trap):**

```
Cache line (64 bytes):
[ producer_counter(8B) | consumer_counter(8B) | padding(48B) ]

If producer writes producer_counter AND consumer writes consumer_counter:
→ They share one cache line
→ Every write by either causes a cache invalidation on the other's CPU
→ Coherency traffic floods the cache bus
→ Performance degrades to ~10% of theoretical maximum
```

**Fix: align to cache line boundaries (pad to 64 bytes)**

### 3.6 Synchronization — The Shared Memory Problem

Shared memory gives you a raw region of RAM. It provides **no synchronization**. If two processes write simultaneously, you get a **data race** — undefined behavior. You must add synchronization:

#### Option A: Mutex in Shared Memory (POSIX)

```c
// The mutex must be initialized with PTHREAD_PROCESS_SHARED
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setpshared(&attr, PTHREAD_PROCESS_SHARED);  // key flag!
pthread_mutex_init(&shm->mutex, &attr);
```

**Problem:** If the owner process dies while holding the mutex, it's permanently locked (deadlock). Use `PTHREAD_MUTEX_ROBUST` to handle this.

#### Option B: Lock-Free Ring Buffer (Preferred for High Performance)

A ring buffer (circular queue) allows one producer and one consumer to operate without locks if:
1. Only one producer, only one consumer (SPSC = Single Producer Single Consumer)
2. Reads and writes to the head/tail indices use atomic operations
3. Memory barriers ensure ordering

```
Ring Buffer Layout:
┌─────────────────────────────────────────────────┐
│ head (atomic) │ tail (atomic) │ data[CAPACITY]  │
└─────────────────────────────────────────────────┘
                  ↑                    ↑
              consumer              producer
              reads here            writes here

head == tail → empty
(tail - head) == CAPACITY → full
```

**Memory barriers (crucial concept):**

A **memory barrier** (fence) prevents the CPU and compiler from reordering memory operations across the barrier. Without them, the CPU might:
1. Write data to the slot
2. Update the tail index (making slot visible to consumer)

...or do it in reverse order 2 → 1, causing consumer to read uninitialized data.

- `__atomic_store_n(&tail, new_tail, __ATOMIC_RELEASE)` — release barrier: all previous writes visible before this store
- `__atomic_load_n(&tail, __ATOMIC_ACQUIRE)` — acquire barrier: all subsequent reads happen after this load

---

### 3.7 C Implementation: Production Shared Memory Ring Buffer

```c
/* shm_ringbuf.h — SPSC Lock-Free Ring Buffer over POSIX Shared Memory */

#ifndef SHM_RINGBUF_H
#define SHM_RINGBUF_H

#include <stdatomic.h>
#include <stdint.h>
#include <stdbool.h>

/* ── Constants ─────────────────────────────────────────────────────────── */
#define RING_CAPACITY   4096U          /* must be power of 2 */
#define RING_MSG_SIZE   256U           /* max bytes per message */
#define CACHE_LINE_SIZE 64U

/* Compile-time assertion that capacity is power of 2 */
_Static_assert((RING_CAPACITY & (RING_CAPACITY - 1)) == 0,
               "RING_CAPACITY must be power of 2");

/* ── Slot — one message slot ────────────────────────────────────────────── */
typedef struct {
    uint32_t len;                   /* actual message length */
    uint8_t  data[RING_MSG_SIZE];   /* message payload */
} __attribute__((aligned(CACHE_LINE_SIZE))) RingSlot;

/* ── Shared Control Block ───────────────────────────────────────────────── */
/*
 * Layout in shared memory:
 *   [RingHeader][RingSlot × RING_CAPACITY]
 *
 * head and tail are on separate cache lines to prevent false sharing.
 * Producer only writes tail; consumer only writes head.
 */
typedef struct {
    /* Padding ensures head and tail are on separate cache lines */
    atomic_uint_least64_t head;
    uint8_t _pad0[CACHE_LINE_SIZE - sizeof(atomic_uint_least64_t)];

    atomic_uint_least64_t tail;
    uint8_t _pad1[CACHE_LINE_SIZE - sizeof(atomic_uint_least64_t)];

    /* Slots follow immediately after this header in memory */
    RingSlot slots[RING_CAPACITY];
} SharedRing;

#define SHARED_RING_SIZE sizeof(SharedRing)

/* ── API ────────────────────────────────────────────────────────────────── */
SharedRing *ring_create(const char *name);  /* producer creates */
SharedRing *ring_open(const char *name);    /* consumer opens   */
void        ring_destroy(const char *name, SharedRing *ring);
void        ring_close(SharedRing *ring);

bool ring_push(SharedRing *ring, const void *data, uint32_t len);
bool ring_pop (SharedRing *ring, void *data, uint32_t *len);

#endif /* SHM_RINGBUF_H */
```

```c
/* shm_ringbuf.c */

#define _POSIX_C_SOURCE 200809L
#include "shm_ringbuf.h"

#include <fcntl.h>       /* O_CREAT, O_RDWR */
#include <sys/mman.h>    /* shm_open, mmap, munmap */
#include <sys/stat.h>    /* ftruncate */
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

/* ── Internal helpers ───────────────────────────────────────────────────── */

static SharedRing *
ring_map(int fd, int prot)
{
    void *ptr = mmap(
        NULL,
        SHARED_RING_SIZE,
        prot,
        MAP_SHARED,   /* writes visible to all processes mapping this fd */
        fd,
        0             /* offset: start of file */
    );
    if (ptr == MAP_FAILED) {
        perror("mmap");
        return NULL;
    }
    return (SharedRing *)ptr;
}

/* ── Public API ─────────────────────────────────────────────────────────── */

SharedRing *
ring_create(const char *name)
{
    /*
     * O_CREAT | O_EXCL — fail if already exists (prevents races at startup).
     * For production, add robust error handling / retry logic.
     */
    int fd = shm_open(name, O_CREAT | O_EXCL | O_RDWR, 0600);
    if (fd < 0) {
        perror("shm_open create");
        return NULL;
    }

    if (ftruncate(fd, (off_t)SHARED_RING_SIZE) < 0) {
        perror("ftruncate");
        close(fd);
        shm_unlink(name);
        return NULL;
    }

    SharedRing *ring = ring_map(fd, PROT_READ | PROT_WRITE);
    close(fd);  /* fd no longer needed; mapping keeps the reference */

    if (!ring) {
        shm_unlink(name);
        return NULL;
    }

    /* Zero-initialize: atomics start at 0 (head == tail == 0 → empty) */
    memset(ring, 0, SHARED_RING_SIZE);

    return ring;
}

SharedRing *
ring_open(const char *name)
{
    int fd = shm_open(name, O_RDWR, 0);
    if (fd < 0) {
        perror("shm_open open");
        return NULL;
    }

    SharedRing *ring = ring_map(fd, PROT_READ | PROT_WRITE);
    close(fd);
    return ring;
}

void
ring_destroy(const char *name, SharedRing *ring)
{
    if (ring) {
        munmap(ring, SHARED_RING_SIZE);
    }
    shm_unlink(name);  /* remove the /dev/shm entry */
}

void
ring_close(SharedRing *ring)
{
    if (ring) {
        munmap(ring, SHARED_RING_SIZE);
    }
}

/*
 * ring_push — called by PRODUCER only.
 *
 * Memory ordering:
 *   - We load head with ACQUIRE to get the consumer's latest position.
 *   - We write data to the slot (plain store — only we write here).
 *   - We store tail with RELEASE, publishing the new slot to consumer.
 */
bool
ring_push(SharedRing *ring, const void *data, uint32_t len)
{
    if (len == 0 || len > RING_MSG_SIZE) return false;

    uint64_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&ring->head, memory_order_acquire);

    /* Full check: (tail - head) >= RING_CAPACITY */
    if ((tail - head) >= RING_CAPACITY) {
        return false;  /* ring is full */
    }

    /* Slot index: use bitwise AND instead of modulo (works because power of 2) */
    uint64_t idx = tail & (RING_CAPACITY - 1);
    RingSlot *slot = &ring->slots[idx];

    slot->len = len;
    memcpy(slot->data, data, len);

    /* RELEASE: ensures data write is visible before tail update */
    atomic_store_explicit(&ring->tail, tail + 1, memory_order_release);

    return true;
}

/*
 * ring_pop — called by CONSUMER only.
 *
 * Memory ordering:
 *   - We load tail with ACQUIRE to get producer's latest position.
 *   - We read data from the slot.
 *   - We store head with RELEASE, telling producer the slot is free.
 */
bool
ring_pop(SharedRing *ring, void *data, uint32_t *len)
{
    uint64_t head = atomic_load_explicit(&ring->head, memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&ring->tail, memory_order_acquire);

    if (head == tail) {
        return false;  /* ring is empty */
    }

    uint64_t idx = head & (RING_CAPACITY - 1);
    RingSlot *slot = &ring->slots[idx];

    *len = slot->len;
    memcpy(data, slot->data, slot->len);

    /* RELEASE: tells producer this slot is now free */
    atomic_store_explicit(&ring->head, head + 1, memory_order_release);

    return true;
}
```

```c
/* producer.c — example usage */
#define _POSIX_C_SOURCE 200809L
#include "shm_ringbuf.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

static uint64_t
now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int main(void)
{
    SharedRing *ring = ring_create("/ipc_demo");
    if (!ring) return 1;

    const char *msg = "hello from producer";
    uint32_t    len = (uint32_t)strlen(msg);

    uint64_t t0 = now_ns();
    uint64_t count = 0;

    for (uint64_t i = 0; i < 1000000; i++) {
        while (!ring_push(ring, msg, len)) {
            /* spin-wait: in production, use futex or yield */
            __asm__ volatile("pause" ::: "memory");  /* x86 spin hint */
        }
        count++;
    }

    uint64_t elapsed_ns = now_ns() - t0;
    printf("Sent %lu messages in %lu ns\n", count, elapsed_ns);
    printf("Throughput: %.2f M msg/s\n",
           (double)count / ((double)elapsed_ns / 1e9) / 1e6);

    ring_destroy("/ipc_demo", ring);
    return 0;
}
```

---

### 3.8 Rust Implementation: Shared Memory Ring Buffer

```rust
// src/shm_ring.rs
//! Lock-free SPSC ring buffer over POSIX shared memory.
//! Safety: This code requires single-producer / single-consumer discipline.

use std::sync::atomic::{AtomicU64, Ordering};
use std::ffi::CString;
use std::ptr::NonNull;

/* ── Constants ──────────────────────────────────────────────────────────── */
const RING_CAPACITY: usize = 4096;  // must be power of 2
const RING_MSG_SIZE: usize = 256;
const CACHE_LINE: usize = 64;

const _: () = assert!(RING_CAPACITY.is_power_of_two(), "must be power of 2");

/* ── FFI bindings (minimal, production would use `nix` crate) ─────────── */
mod ffi {
    use std::ffi::c_void;

    pub const O_RDWR:   i32 = 0o002;
    pub const O_CREAT:  i32 = 0o100;
    pub const O_EXCL:   i32 = 0o200;
    pub const PROT_READ:  i32 = 0x1;
    pub const PROT_WRITE: i32 = 0x2;
    pub const MAP_SHARED: i32 = 0x1;

    extern "C" {
        pub fn shm_open(name: *const i8, oflag: i32, mode: u32) -> i32;
        pub fn shm_unlink(name: *const i8) -> i32;
        pub fn ftruncate(fd: i32, length: i64) -> i32;
        pub fn mmap(addr: *mut c_void, len: usize, prot: i32, flags: i32,
                    fd: i32, offset: i64) -> *mut c_void;
        pub fn munmap(addr: *mut c_void, len: usize) -> i32;
        pub fn close(fd: i32) -> i32;
    }

    pub const MAP_FAILED: *mut c_void = !0usize as *mut c_void;
}

/* ── Ring slot ──────────────────────────────────────────────────────────── */
#[repr(C, align(64))]  // align to cache line
struct Slot {
    len:  u32,
    data: [u8; RING_MSG_SIZE],
}

/* ── Shared ring header ─────────────────────────────────────────────────── */
#[repr(C)]
struct RingHeader {
    head:  AtomicU64,
    _pad0: [u8; CACHE_LINE - std::mem::size_of::<AtomicU64>()],
    tail:  AtomicU64,
    _pad1: [u8; CACHE_LINE - std::mem::size_of::<AtomicU64>()],
}

/* ── Public handle ──────────────────────────────────────────────────────── */
pub struct SharedRing {
    ptr:    NonNull<RingHeader>,
    name:   Option<String>,  // Some if we own it (creator), None if just mapped
    size:   usize,
}

/// SAFETY: SharedRing is designed for inter-process use; within one process,
/// the caller must ensure single-producer / single-consumer discipline.
unsafe impl Send for SharedRing {}

impl SharedRing {
    fn shm_size() -> usize {
        std::mem::size_of::<RingHeader>()
            + RING_CAPACITY * std::mem::size_of::<Slot>()
    }

    unsafe fn do_map(name: &str, create: bool) -> Result<(NonNull<RingHeader>, i32), String> {
        let cname = CString::new(name).map_err(|e| e.to_string())?;
        let size  = Self::shm_size();

        let flags = if create {
            ffi::O_RDWR | ffi::O_CREAT | ffi::O_EXCL
        } else {
            ffi::O_RDWR
        };

        let fd = ffi::shm_open(cname.as_ptr(), flags, 0o600);
        if fd < 0 {
            return Err(format!("shm_open failed: {}", std::io::Error::last_os_error()));
        }

        if create && ffi::ftruncate(fd, size as i64) < 0 {
            ffi::close(fd);
            ffi::shm_unlink(cname.as_ptr());
            return Err("ftruncate failed".to_string());
        }

        let ptr = ffi::mmap(
            std::ptr::null_mut(),
            size,
            ffi::PROT_READ | ffi::PROT_WRITE,
            ffi::MAP_SHARED,
            fd,
            0,
        );

        ffi::close(fd);

        if ptr == ffi::MAP_FAILED {
            return Err("mmap failed".to_string());
        }

        NonNull::new(ptr as *mut RingHeader)
            .map(|nn| (nn, fd))
            .ok_or_else(|| "null mmap result".to_string())
    }

    /// Create a new shared ring buffer (producer side).
    pub fn create(name: &str) -> Result<Self, String> {
        let size = Self::shm_size();
        let (ptr, _) = unsafe { Self::do_map(name, true)? };

        // Zero-initialize atomics
        unsafe {
            std::ptr::write_bytes(ptr.as_ptr() as *mut u8, 0, size);
        }

        Ok(SharedRing { ptr, name: Some(name.to_string()), size })
    }

    /// Open an existing shared ring buffer (consumer side).
    pub fn open(name: &str) -> Result<Self, String> {
        let size = Self::shm_size();
        let (ptr, _) = unsafe { Self::do_map(name, false)? };
        Ok(SharedRing { ptr, name: None, size })
    }

    fn header(&self) -> &RingHeader {
        unsafe { self.ptr.as_ref() }
    }

    fn slots(&self) -> *mut Slot {
        let base = self.ptr.as_ptr() as usize;
        (base + std::mem::size_of::<RingHeader>()) as *mut Slot
    }

    /// Push a message (producer only). Returns false if ring is full.
    pub fn push(&self, data: &[u8]) -> bool {
        if data.is_empty() || data.len() > RING_MSG_SIZE {
            return false;
        }

        let header = self.header();
        let tail = header.tail.load(Ordering::Relaxed);
        let head = header.head.load(Ordering::Acquire);

        if tail.wrapping_sub(head) >= RING_CAPACITY as u64 {
            return false; // full
        }

        let idx = (tail as usize) & (RING_CAPACITY - 1);
        let slot = unsafe { &mut *self.slots().add(idx) };

        slot.len = data.len() as u32;
        slot.data[..data.len()].copy_from_slice(data);

        // RELEASE: ensure data is visible before tail is bumped
        header.tail.store(tail.wrapping_add(1), Ordering::Release);
        true
    }

    /// Pop a message (consumer only). Returns None if ring is empty.
    pub fn pop(&self) -> Option<Vec<u8>> {
        let header = self.header();
        let head = header.head.load(Ordering::Relaxed);
        let tail = header.tail.load(Ordering::Acquire);

        if head == tail {
            return None; // empty
        }

        let idx = (head as usize) & (RING_CAPACITY - 1);
        let slot = unsafe { &*self.slots().add(idx) };

        let len  = slot.len as usize;
        let data = slot.data[..len].to_vec();

        // RELEASE: tell producer this slot is free
        header.head.store(head.wrapping_add(1), Ordering::Release);
        Some(data)
    }
}

impl Drop for SharedRing {
    fn drop(&mut self) {
        unsafe {
            ffi::munmap(self.ptr.as_ptr() as *mut _, self.size);
            if let Some(ref name) = self.name {
                let cname = CString::new(name.as_str()).unwrap();
                ffi::shm_unlink(cname.as_ptr());
            }
        }
    }
}
```

```rust
// Cargo.toml
// [dependencies]
// (no external deps for core shm; add nix = "0.27" for ergonomic FFI)

// src/main.rs — producer example
fn main() {
    let ring = SharedRing::create("/ipc_rust_demo")
        .expect("failed to create ring");

    let msg = b"hello from rust producer";
    let t0  = std::time::Instant::now();
    let mut count = 0u64;

    for _ in 0..1_000_000u64 {
        loop {
            if ring.push(msg) {
                count += 1;
                break;
            }
            std::hint::spin_loop(); // emit PAUSE on x86
        }
    }

    let elapsed = t0.elapsed();
    println!("Sent {} messages in {:?}", count, elapsed);
    println!(
        "Throughput: {:.2} M msg/s",
        count as f64 / elapsed.as_secs_f64() / 1e6
    );
}
```

---

### 3.9 Go Implementation: Shared Memory via mmap

> Go's runtime makes shared memory tricky: the GC does not know about memory outside its heap. Use `[]byte` slices backed by `mmap` and keep Go objects out of the shared region — only store plain bytes.

```go
// shm/ring.go
package shm

import (
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"sync/atomic"
	"syscall"
	"unsafe"
)

const (
	RingCapacity = 4096              // must be power of 2
	RingMsgSize  = 256
	CacheLine    = 64
	SlotSize     = 4 + RingMsgSize  // 4 bytes len + payload
)

// SharedRing wraps a mmap'd region representing a SPSC ring buffer.
// The memory layout (from offset 0):
//   [8 bytes head][56 bytes pad][8 bytes tail][56 bytes pad][slots...]
type SharedRing struct {
	data []byte
	name string
	owns bool // true if we created (and should shm_unlink)
}

// headerSize returns the size of the control block (2 cache lines)
func headerSize() int { return 2 * CacheLine }

// totalSize returns the total mmap size
func totalSize() int {
	return headerSize() + RingCapacity*SlotSize
}

// head/tail are at fixed offsets in the first two cache lines
func (r *SharedRing) head() *uint64 { return (*uint64)(unsafe.Pointer(&r.data[0])) }
func (r *SharedRing) tail() *uint64 { return (*uint64)(unsafe.Pointer(&r.data[CacheLine])) }

// slotAt returns a pointer to the raw bytes of slot idx
func (r *SharedRing) slotAt(idx uint64) []byte {
	off := headerSize() + int(idx)*SlotSize
	return r.data[off : off+SlotSize]
}

// CreateRing creates a new POSIX shared memory ring. Producer calls this.
func CreateRing(name string) (*SharedRing, error) {
	// Use syscall.Open on /dev/shm directly (portable to Linux)
	path := "/dev/shm" + name
	fd, err := syscall.Open(path,
		syscall.O_CREAT|syscall.O_EXCL|syscall.O_RDWR, 0600)
	if err != nil {
		return nil, fmt.Errorf("shm create: %w", err)
	}
	defer syscall.Close(fd)

	size := totalSize()
	if err := syscall.Ftruncate(fd, int64(size)); err != nil {
		os.Remove(path)
		return nil, fmt.Errorf("ftruncate: %w", err)
	}

	data, err := syscall.Mmap(fd, 0, size,
		syscall.PROT_READ|syscall.PROT_WRITE, syscall.MAP_SHARED)
	if err != nil {
		os.Remove(path)
		return nil, fmt.Errorf("mmap: %w", err)
	}

	return &SharedRing{data: data, name: path, owns: true}, nil
}

// OpenRing opens an existing shared memory ring. Consumer calls this.
func OpenRing(name string) (*SharedRing, error) {
	path := "/dev/shm" + name
	fd, err := syscall.Open(path, syscall.O_RDWR, 0)
	if err != nil {
		return nil, fmt.Errorf("shm open: %w", err)
	}
	defer syscall.Close(fd)

	data, err := syscall.Mmap(fd, 0, totalSize(),
		syscall.PROT_READ|syscall.PROT_WRITE, syscall.MAP_SHARED)
	if err != nil {
		return nil, fmt.Errorf("mmap: %w", err)
	}

	return &SharedRing{data: data, name: path, owns: false}, nil
}

// Push writes msg into the ring. Returns false if full.
// Must be called from a single goroutine (producer).
func (r *SharedRing) Push(msg []byte) bool {
	if len(msg) == 0 || len(msg) > RingMsgSize {
		return false
	}

	tail := atomic.LoadUint64(r.tail())
	head := atomic.LoadUint64(r.head())

	if tail-head >= RingCapacity {
		return false // full
	}

	idx  := tail & (RingCapacity - 1)
	slot := r.slotAt(idx)

	binary.LittleEndian.PutUint32(slot[:4], uint32(len(msg)))
	copy(slot[4:], msg)

	// Release store: data visible before tail bump
	atomic.StoreUint64(r.tail(), tail+1)
	return true
}

// Pop reads one message from the ring. Returns nil if empty.
// Must be called from a single goroutine (consumer).
func (r *SharedRing) Pop() []byte {
	head := atomic.LoadUint64(r.head())
	tail := atomic.LoadUint64(r.tail())

	if head == tail {
		return nil // empty
	}

	idx  := head & (RingCapacity - 1)
	slot := r.slotAt(idx)

	msgLen := binary.LittleEndian.Uint32(slot[:4])
	if msgLen == 0 || int(msgLen) > RingMsgSize {
		return nil // corrupted
	}

	out := make([]byte, msgLen)
	copy(out, slot[4:4+msgLen])

	// Release store: slot is free for producer
	atomic.StoreUint64(r.head(), head+1)
	return out
}

// Close unmaps the memory and optionally unlinks the shm object.
func (r *SharedRing) Close() error {
	errs := []error{}
	if err := syscall.Munmap(r.data); err != nil {
		errs = append(errs, err)
	}
	if r.owns {
		if err := os.Remove(r.name); err != nil {
			errs = append(errs, err)
		}
	}
	return errors.Join(errs...)
}
```

---

## 4. Unix Domain Sockets (UDS)

### 4.1 What Is a Unix Domain Socket?

A **Unix Domain Socket** (UDS) is a socket that communicates within the same machine using the **filesystem namespace** (or abstract namespace) as an address, instead of IP:port. It uses the same `socket()`, `bind()`, `connect()`, `send()`, `recv()` API as TCP, but:

- **No network stack traversal** — data never leaves the kernel
- **One copy** — data is copied from sender's buffer to receiver's buffer inside kernel socket buffers
- **Lower latency** than TCP — skips IP routing, checksum calculation, packet segmentation

The address is a **filesystem path** like `/tmp/myapp.sock` or an **abstract name** like `\0myapp`.

### 4.2 Socket Types

**`SOCK_STREAM`** — bidirectional, connection-oriented, ordered, reliable byte stream
- Like TCP but local-only
- Needs `listen()` / `accept()` handshake
- No message boundaries — you get a stream of bytes
- Must implement your own framing (length-prefix, delimiter, etc.)

**`SOCK_DGRAM`** — connectionless, message-oriented
- Each `sendmsg()` delivers exactly one message to `recvmsg()`
- Natural message boundaries
- No connection state
- Messages can be dropped if buffers full (unlike SOCK_STREAM which blocks)

**`SOCK_SEQPACKET`** — connection-oriented + message boundaries
- Best of both worlds: reliable delivery + natural message framing
- Less commonly used but excellent for IPC
- Like SCTP but local

### 4.3 Kernel Path: `send()` → `recv()` for UDS

This is the critical difference from shared memory. Data is **copied once** through kernel socket buffers:

```
Process A (sender)                    Process B (receiver)
──────────────────────────────────────────────────────────────
userspace buffer                       userspace buffer
  [message data]                         [empty]
       │                                     ↑
  send() syscall                        recv() syscall
       │                                     │
──────────────────────── kernel ─────────────────────────────
       ▼                                     │
  sock_sendmsg()                             │
       │                                     │
  unix_stream_sendmsg()                      │
       │                                     │
  alloc sk_buff (socket buffer)              │
  memcpy: user → sk_buff  ← ONE COPY        │
       │                                     │
  append to recv queue of peer socket        │
       │                                     │
       ─────────────────────────────────────→
                                        unix_stream_recvmsg()
                                        memcpy: sk_buff → user
                                        ← (this is the "one copy")
                                        free sk_buff
```

**`sk_buff` (socket buffer):** The fundamental data structure in Linux networking. It contains:
- A header with metadata (socket, protocol info, timestamps)
- A pointer to the actual data (which may be scattered across multiple pages)
- Reference count

**Key insight:** For UDS, the kernel does NOT go through `ip_rcv()`, `tcp_v4_rcv()`, or any network protocol. It goes directly through the `unix_*` family of functions in `net/unix/af_unix.c` in the kernel source.

### 4.4 Zero-Copy Optimization with `SCM_RIGHTS` and `MSG_ZEROCOPY`

#### SCM_RIGHTS — File Descriptor Passing

UDS has a unique superpower: you can **pass open file descriptors** between processes. This is used to:
- Share file access without copying file contents
- Pass a connected socket to a worker process
- Share a memfd (in-memory file) — effectively zero-copy data transfer

```c
/* Passing a file descriptor over UDS */
struct msghdr   msg     = {0};
struct cmsghdr *cmsg;
int             fd_to_pass = open("/some/file", O_RDONLY);
char            cmsg_buf[CMSG_SPACE(sizeof(int))];

msg.msg_control    = cmsg_buf;
msg.msg_controllen = sizeof(cmsg_buf);

cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_RIGHTS;            /* "send rights" */
cmsg->cmsg_len   = CMSG_LEN(sizeof(int));
memcpy(CMSG_DATA(cmsg), &fd_to_pass, sizeof(int));

/* Combine with memfd for zero-copy large data:
   1. Create memfd, write data
   2. Pass memfd via SCM_RIGHTS
   3. Receiver mmap's the memfd → reads without copy */
```

#### Abstract Namespace

Instead of a filesystem path, you can use a **null-byte prefix** for an abstract socket address:

```c
struct sockaddr_un addr = {0};
addr.sun_family = AF_UNIX;
addr.sun_path[0] = '\0';   // null byte = abstract namespace
strcpy(addr.sun_path + 1, "myapp");
// length = offsetof(struct sockaddr_un, sun_path) + 1 + strlen("myapp")
```

**Abstract namespace advantages:**
- Auto-cleaned when all processes close it (no stale socket file)
- Not visible in filesystem (no permissions issues)
- Faster than filesystem path (no VFS lookup)

### 4.5 C Implementation: Production UDS Server/Client

```c
/* uds_server.c — SOCK_SEQPACKET server */

#define _POSIX_C_SOURCE 200809L
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>

#define SOCKET_PATH    "/tmp/ipc_demo.sock"
#define MAX_MSG_SIZE   4096
#define BACKLOG        128
#define MAX_CLIENTS    64

static volatile int g_running = 1;

static void
signal_handler(int sig)
{
    (void)sig;
    g_running = 0;
}

static int
make_server_socket(void)
{
    int fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    if (fd < 0) {
        perror("socket");
        return -1;
    }

    /* Remove stale socket file */
    unlink(SOCKET_PATH);

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(fd);
        return -1;
    }

    /* Set socket buffer size for throughput optimization */
    int bufsize = 1 << 20;  /* 1 MiB */
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
    setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));

    if (listen(fd, BACKLOG) < 0) {
        perror("listen");
        close(fd);
        return -1;
    }

    return fd;
}

static void
handle_client(int client_fd)
{
    uint8_t buf[MAX_MSG_SIZE];
    ssize_t n;

    while ((n = recv(client_fd, buf, sizeof(buf), 0)) > 0) {
        /* Echo back — in production, dispatch to handler */
        if (send(client_fd, buf, (size_t)n, MSG_NOSIGNAL) < 0) {
            if (errno != EPIPE && errno != ECONNRESET) {
                perror("send");
            }
            break;
        }
    }
    close(client_fd);
}

int main(void)
{
    signal(SIGINT,  signal_handler);
    signal(SIGTERM, signal_handler);
    signal(SIGPIPE, SIG_IGN);  /* handle EPIPE via errno, not signal */

    int server_fd = make_server_socket();
    if (server_fd < 0) return 1;

    printf("UDS server listening on %s\n", SOCKET_PATH);

    while (g_running) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }
        /* In production: dispatch to thread pool or event loop */
        handle_client(client_fd);
    }

    close(server_fd);
    unlink(SOCKET_PATH);
    return 0;
}
```

```c
/* uds_client.c */

#define _POSIX_C_SOURCE 200809L
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>

#define SOCKET_PATH  "/tmp/ipc_demo.sock"
#define ITERATIONS   100000
#define MSG_SIZE     64

static uint64_t
now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int main(void)
{
    int fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    if (fd < 0) { perror("socket"); return 1; }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect");
        close(fd);
        return 1;
    }

    uint8_t  send_buf[MSG_SIZE];
    uint8_t  recv_buf[MSG_SIZE];
    uint64_t total_latency_ns = 0;

    memset(send_buf, 0xAB, sizeof(send_buf));

    for (int i = 0; i < ITERATIONS; i++) {
        uint64_t t0 = now_ns();

        ssize_t n = send(fd, send_buf, sizeof(send_buf), 0);
        if (n < 0) { perror("send"); break; }

        n = recv(fd, recv_buf, sizeof(recv_buf), 0);
        if (n < 0) { perror("recv"); break; }

        total_latency_ns += now_ns() - t0;
    }

    printf("UDS round-trip latency: avg %.2f µs over %d iterations\n",
           (double)total_latency_ns / ITERATIONS / 1000.0, ITERATIONS);

    close(fd);
    return 0;
}
```

---

### 4.6 Rust Implementation: UDS with tokio

```rust
// Cargo.toml
// [dependencies]
// tokio = { version = "1", features = ["full"] }
// bytes = "1"

// src/uds_server.rs
use tokio::net::{UnixListener, UnixStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::path::Path;

const SOCKET_PATH: &str = "/tmp/ipc_rust.sock";
const MAX_MSG_SIZE: usize = 4096;

async fn handle_client(mut stream: UnixStream) -> std::io::Result<()> {
    let mut buf = vec![0u8; MAX_MSG_SIZE];
    loop {
        let n = stream.read(&mut buf).await?;
        if n == 0 {
            return Ok(()); // client disconnected
        }
        // Echo back — production: parse framing and dispatch
        stream.write_all(&buf[..n]).await?;
    }
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    // Remove stale socket
    if Path::new(SOCKET_PATH).exists() {
        std::fs::remove_file(SOCKET_PATH)?;
    }

    let listener = UnixListener::bind(SOCKET_PATH)?;
    println!("UDS server listening on {}", SOCKET_PATH);

    loop {
        let (stream, _addr) = listener.accept().await?;
        tokio::spawn(async move {
            if let Err(e) = handle_client(stream).await {
                eprintln!("client error: {}", e);
            }
        });
    }
}
```

```rust
// src/uds_client.rs — latency benchmark
use tokio::net::UnixStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::time::Instant;

const SOCKET_PATH: &str = "/tmp/ipc_rust.sock";
const ITERATIONS:  u64  = 100_000;
const MSG_SIZE:    usize = 64;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let mut stream = UnixStream::connect(SOCKET_PATH).await?;

    let send_buf = vec![0xABu8; MSG_SIZE];
    let mut recv_buf = vec![0u8; MSG_SIZE];
    let mut total_ns: u128 = 0;

    for _ in 0..ITERATIONS {
        let t0 = Instant::now();
        stream.write_all(&send_buf).await?;
        stream.read_exact(&mut recv_buf).await?;
        total_ns += t0.elapsed().as_nanos();
    }

    println!(
        "UDS round-trip latency: avg {:.2} µs over {} iterations",
        total_ns as f64 / ITERATIONS as f64 / 1000.0,
        ITERATIONS
    );

    Ok(())
}
```

---

### 4.7 Go Implementation: UDS

```go
// uds/server.go
package main

import (
	"fmt"
	"io"
	"net"
	"os"
)

const (
	SocketPath = "/tmp/ipc_go.sock"
	MaxMsgSize = 4096
)

func handleConn(conn net.Conn) {
	defer conn.Close()
	buf := make([]byte, MaxMsgSize)
	for {
		n, err := conn.Read(buf)
		if err != nil {
			if err != io.EOF {
				fmt.Fprintf(os.Stderr, "read error: %v\n", err)
			}
			return
		}
		if _, err := conn.Write(buf[:n]); err != nil {
			fmt.Fprintf(os.Stderr, "write error: %v\n", err)
			return
		}
	}
}

func main() {
	os.Remove(SocketPath)

	// Use "unixpacket" for SOCK_SEQPACKET semantics
	// Use "unix" for SOCK_STREAM
	ln, err := net.Listen("unixpacket", SocketPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "listen: %v\n", err)
		os.Exit(1)
	}
	defer ln.Close()

	fmt.Printf("UDS server on %s\n", SocketPath)

	for {
		conn, err := ln.Accept()
		if err != nil {
			fmt.Fprintf(os.Stderr, "accept: %v\n", err)
			continue
		}
		go handleConn(conn)
	}
}
```

```go
// uds/client_bench.go
package main

import (
	"fmt"
	"net"
	"time"
)

func main() {
	conn, err := net.Dial("unixpacket", SocketPath)
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	const iterations = 100_000
	const msgSize    = 64

	send := make([]byte, msgSize)
	recv := make([]byte, msgSize)
	for i := range send { send[i] = 0xAB }

	total := time.Duration(0)

	for i := 0; i < iterations; i++ {
		t0 := time.Now()
		if _, err := conn.Write(send); err != nil {
			panic(err)
		}
		if _, err := conn.Read(recv); err != nil {
			panic(err)
		}
		total += time.Since(t0)
	}

	fmt.Printf("UDS avg latency: %.2f µs over %d iterations\n",
		float64(total.Microseconds())/iterations, iterations)
}
```

---

## 5. TCP Sockets

### 5.1 Loopback Interface — `127.0.0.1`

When two processes on the same machine communicate via TCP to `127.0.0.1`, the data never hits a physical network card. Instead, the kernel has a **loopback network interface** (`lo`) that acts as a virtual NIC:

```
Process A → TCP socket → [lo interface driver] → TCP socket → Process B
```

But crucially, the **full network stack** is still traversed:

```
Application (write syscall)
    │
    ▼
Socket layer (sock_write)
    │
    ▼
TCP layer (tcp_sendmsg)
  → Segment data
  → Calculate checksum (though loopback may skip actual checksum)
  → Manage congestion window, retransmits, timers
    │
    ▼
IP layer (ip_local_out)
  → IP header construction
  → Routing table lookup (resolves to lo)
    │
    ▼
Loopback driver (loopback_xmit)
  → "Transmit" by re-injecting into receive path
    │
    ▼
IP receive (ip_rcv)
  → IP header validation
    │
    ▼
TCP receive (tcp_v4_rcv)
  → TCP state machine (sequence numbers, ACKs)
  → Place data in receive buffer
    │
    ▼
Application (read syscall)
```

**This full traversal costs ~5–15 µs even for tiny messages.** This is why TCP is slowest for local IPC.

### 5.2 TCP State Machine — The Overhead Source

TCP maintains a state machine per connection: CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → CLOSED. This state machine handles:

- **Sequence numbers:** Every byte is numbered; receiver must ACK receipt
- **Retransmission:** Timer fires if no ACK received
- **Congestion control:** Slow start, CWND (congestion window)
- **Flow control:** Receiver advertises window size
- **Nagle's algorithm:** Buffers small writes to reduce packet count

All of this adds latency and CPU overhead even on loopback where no actual network issues exist.

### 5.3 Critical TCP Socket Options for Local IPC

```c
/* For low-latency local IPC, set these options: */

/* 1. Disable Nagle's algorithm — sends immediately, don't buffer */
int flag = 1;
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));

/* 2. Increase socket buffers */
int bufsize = 4 * 1024 * 1024;  /* 4 MiB */
setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));

/* 3. Quick ACK — don't delay ACKs */
flag = 1;
setsockopt(fd, IPPROTO_TCP, TCP_QUICKACK, &flag, sizeof(flag));

/* 4. Allow port reuse (prevents "address already in use" on restart) */
flag = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &flag, sizeof(flag));
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &flag, sizeof(flag));

/* 5. Keep connections alive (detect dead peers) */
flag = 1;
setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &flag, sizeof(flag));
int keepidle  = 10;  /* seconds before first keepalive */
int keepintvl = 5;   /* interval between keepalives */
int keepcnt   = 3;   /* retries before giving up */
setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE, &keepidle, sizeof(keepidle));
setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT, &keepcnt, sizeof(keepcnt));
```

### 5.4 C Implementation: Production TCP Echo Server

```c
/* tcp_server.c — production TCP server with proper socket options */

#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>

#define SERVER_PORT  9876
#define BACKLOG      1024
#define MAX_MSG_SIZE 4096

static void
set_socket_options(int fd)
{
    int flag = 1;

    /* Disable Nagle — critical for latency-sensitive local IPC */
    if (setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag)) < 0)
        perror("TCP_NODELAY");

    /* Quick ACK */
    if (setsockopt(fd, IPPROTO_TCP, TCP_QUICKACK, &flag, sizeof(flag)) < 0)
        perror("TCP_QUICKACK");

    /* Reuse address/port */
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &flag, sizeof(flag)) < 0)
        perror("SO_REUSEADDR");
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &flag, sizeof(flag)) < 0)
        perror("SO_REUSEPORT");

    /* Large buffers */
    int bufsize = 4 << 20;
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
    setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));
}

static void
handle_client(int client_fd)
{
    /* Re-enable TCP_QUICKACK per-receive (Linux resets it) */
    int flag = 1;
    setsockopt(client_fd, IPPROTO_TCP, TCP_QUICKACK, &flag, sizeof(flag));

    uint8_t buf[MAX_MSG_SIZE];
    ssize_t n;

    while ((n = recv(client_fd, buf, sizeof(buf), 0)) > 0) {
        /* Re-arm quick ACK after each recv */
        setsockopt(client_fd, IPPROTO_TCP, TCP_QUICKACK, &flag, sizeof(flag));

        ssize_t sent = 0;
        while (sent < n) {
            ssize_t s = send(client_fd, buf + sent, (size_t)(n - sent),
                             MSG_NOSIGNAL);
            if (s < 0) {
                if (errno == EINTR) continue;
                goto done;
            }
            sent += s;
        }
    }
done:
    close(client_fd);
}

int main(void)
{
    signal(SIGPIPE, SIG_IGN);

    int server_fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (server_fd < 0) { perror("socket"); return 1; }

    set_socket_options(server_fd);

    struct sockaddr_in addr = {0};
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  /* 127.0.0.1 */
    addr.sin_port        = htons(SERVER_PORT);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); close(server_fd); return 1;
    }

    if (listen(server_fd, BACKLOG) < 0) {
        perror("listen"); close(server_fd); return 1;
    }

    printf("TCP server on 127.0.0.1:%d\n", SERVER_PORT);

    for (;;) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept"); break;
        }
        set_socket_options(client_fd);
        handle_client(client_fd);
    }

    close(server_fd);
    return 0;
}
```

### 5.5 Go Implementation: TCP with proper tuning

```go
// tcp/server.go
package main

import (
	"fmt"
	"io"
	"net"
	"os"
	"syscall"
)

const (
	ListenAddr = "127.0.0.1:9876"
	MaxMsgSize = 4096
)

func configureTCP(conn *net.TCPConn) error {
	rawConn, err := conn.SyscallConn()
	if err != nil {
		return err
	}
	return rawConn.Control(func(fd uintptr) {
		// TCP_NODELAY: disable Nagle
		syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, syscall.TCP_NODELAY, 1)
		// TCP_QUICKACK: don't delay ACKs
		syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP, syscall.TCP_QUICKACK, 1)
		// Large buffers
		syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_RCVBUF, 4<<20)
		syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_SNDBUF, 4<<20)
	})
}

func handleConn(conn *net.TCPConn) {
	defer conn.Close()
	if err := configureTCP(conn); err != nil {
		fmt.Fprintln(os.Stderr, "configure:", err)
	}
	buf := make([]byte, MaxMsgSize)
	for {
		n, err := conn.Read(buf)
		if err != nil {
			if err != io.EOF {
				fmt.Fprintln(os.Stderr, "read:", err)
			}
			return
		}
		if _, err := conn.Write(buf[:n]); err != nil {
			fmt.Fprintln(os.Stderr, "write:", err)
			return
		}
	}
}

func main() {
	lc := net.ListenConfig{Control: func(network, address string, c syscall.RawConn) error {
		return c.Control(func(fd uintptr) {
			syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_REUSEADDR, 1)
			syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, syscall.SO_REUSEPORT, 1)
		})
	}}

	ln, err := lc.Listen(nil, "tcp", ListenAddr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "listen:", err)
		os.Exit(1)
	}
	defer ln.Close()

	fmt.Println("TCP server on", ListenAddr)

	for {
		conn, err := ln.Accept()
		if err != nil {
			fmt.Fprintln(os.Stderr, "accept:", err)
			continue
		}
		go handleConn(conn.(*net.TCPConn))
	}
}
```

---

## 6. gRPC — Transport Layer Concepts

### 6.1 What gRPC Is

**gRPC** (Google Remote Procedure Call) is a framework for calling functions in a remote process as if they were local. It is composed of **four distinct layers**:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Application — your .proto service definitions  │
│   service Calculator { rpc Add(AddRequest) returns ... }│
├─────────────────────────────────────────────────────────┤
│ Layer 3: Serialization — Protocol Buffers (protobuf)    │
│   Encode/decode structs to/from compact binary format   │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Framing — HTTP/2                               │
│   Multiplexing, flow control, header compression (HPACK)│
├─────────────────────────────────────────────────────────┤
│ Layer 1: Transport — TCP or UDS                         │
│   Reliable byte stream delivery                         │
└─────────────────────────────────────────────────────────┘
```

**gRPC does NOT use shared memory.** It always goes through a socket (TCP or UDS). This is its main performance limitation compared to shared memory.

### 6.2 Protocol Buffers — Serialization

**Serialization** is the process of converting a data structure (struct in memory) into a sequence of bytes that can be sent over the wire, then **deserialization** reconstructs the struct on the other side.

**Protobuf encoding** is binary and compact:
- Each field is identified by a field number (not name) → no schema needed at runtime
- Variable-length integer encoding (varint) saves space for small numbers
- No padding, no JSON keys, no XML tags

```protobuf
// calculator.proto
syntax = "proto3";

package calculator;

service Calculator {
  rpc Add (AddRequest)  returns (AddResponse);
  rpc Mul (MulRequest)  returns (MulResponse);
}

message AddRequest  { int64 a = 1; int64 b = 2; }
message AddResponse { int64 result = 1; }
message MulRequest  { int64 a = 1; int64 b = 2; }
message MulResponse { int64 result = 1; }
```

**Binary encoding of `AddRequest{a: 300, b: 5}`:**

```
Field 1 (a), varint:  0x08 0xAC 0x02   (3 bytes for 300)
Field 2 (b), varint:  0x10 0x05        (2 bytes for 5)
Total: 5 bytes — vs JSON: {"a":300,"b":5} = 16 bytes
```

### 6.3 HTTP/2 Framing and Multiplexing

**HTTP/2** allows multiple RPC calls to share a **single TCP connection** simultaneously, using **streams**:

```
One TCP connection:
┌──────────────────────────────────────────────────────────────────┐
│ Stream 1: Add(300,5)    ──── request ────────── response ──      │
│ Stream 3: Mul(7,8)      ────── request ─ response ──             │
│ Stream 5: Add(1,2)      request ──────────────────── response ── │
└──────────────────────────────────────────────────────────────────┘
```

Each stream is independent. Responses can come back out of order. This is **multiplexing** — it eliminates the Head-of-Line blocking problem of HTTP/1.1.

**HTTP/2 frame structure (9-byte header + payload):**

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─────────────────────────────┼───────────┼─────────────────────────┤
│         Length (24 bits)    │Type(8bits)│   Flags (8 bits)        │
├─────────────────────────────┴───────────┴─────────────────────────┤
│R│              Stream Identifier (31 bits)                        │
├─────────────────────────────────────────────────────────────────── │
│                   Frame Payload (Length bytes)                    │
└─────────────────────────────────────────────────────────────────── ┘
```

### 6.4 gRPC over UDS — Go Implementation

```go
// grpc_uds/server.go
package main

import (
	"context"
	"fmt"
	"net"
	"os"

	"google.golang.org/grpc"
	pb "your_module/calculator" // generated from .proto
)

const SocketPath = "/tmp/grpc_demo.sock"

// calculatorServer implements the generated gRPC interface
type calculatorServer struct {
	pb.UnimplementedCalculatorServer
}

func (s *calculatorServer) Add(
	ctx context.Context,
	req *pb.AddRequest,
) (*pb.AddResponse, error) {
	return &pb.AddResponse{Result: req.A + req.B}, nil
}

func (s *calculatorServer) Mul(
	ctx context.Context,
	req *pb.MulRequest,
) (*pb.MulResponse, error) {
	return &pb.MulResponse{Result: req.A * req.B}, nil
}

func main() {
	os.Remove(SocketPath)

	// Listen on UDS instead of TCP — this is the key
	lis, err := net.Listen("unix", SocketPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "listen:", err)
		os.Exit(1)
	}

	// gRPC server options for performance
	opts := []grpc.ServerOption{
		grpc.MaxRecvMsgSize(16 * 1024 * 1024),  // 16 MiB
		grpc.MaxSendMsgSize(16 * 1024 * 1024),
		// In production: add TLS, interceptors, rate limiting
	}

	srv := grpc.NewServer(opts...)
	pb.RegisterCalculatorServer(srv, &calculatorServer{})

	fmt.Println("gRPC server on", SocketPath)
	if err := srv.Serve(lis); err != nil {
		fmt.Fprintln(os.Stderr, "serve:", err)
		os.Exit(1)
	}
}
```

```go
// grpc_uds/client.go
package main

import (
	"context"
	"fmt"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	pb "your_module/calculator"
)

func main() {
	// Dial over UDS using a custom dialer
	dialer := func(ctx context.Context, addr string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, "unix", addr)
	}

	conn, err := grpc.Dial(
		"/tmp/grpc_demo.sock",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithContextDialer(dialer),
	)
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	client := pb.NewCalculatorClient(conn)
	ctx    := context.Background()

	const iterations = 10_000
	total := time.Duration(0)

	for i := 0; i < iterations; i++ {
		t0 := time.Now()
		resp, err := client.Add(ctx, &pb.AddRequest{A: 300, B: int64(i)})
		if err != nil {
			panic(err)
		}
		total += time.Since(t0)
		_ = resp
	}

	fmt.Printf("gRPC/UDS avg latency: %.2f µs over %d iterations\n",
		float64(total.Microseconds())/iterations, iterations)
}
```

### 6.5 gRPC over TCP — The Difference

To switch from UDS to TCP, you only change the listener:

```go
// Change only this line in the server:
lis, err := net.Listen("tcp", "127.0.0.1:50051")

// Change only this in the client:
conn, err := grpc.Dial("127.0.0.1:50051", ...)
// No custom dialer needed for TCP
```

**Performance difference (gRPC UDS vs TCP):**
- UDS skips IP routing, IP header processing, and some TCP overhead
- In practice: UDS gRPC is **15–30% faster** than TCP gRPC for local communication
- For remote calls: must use TCP (UDS doesn't cross machine boundaries)

### 6.6 Rust gRPC with Tonic over UDS

```rust
// Cargo.toml
// [dependencies]
// tonic = "0.11"
// prost = "0.12"
// tokio = { version = "1", features = ["full"] }
// tower = "0.4"
// hyper = "0.14"
// [build-dependencies]
// tonic-build = "0.11"

// build.rs
fn main() {
    tonic_build::compile_protos("proto/calculator.proto")
        .expect("failed to compile proto");
}

// src/grpc_server.rs
use tonic::{transport::Server, Request, Response, Status};
use tokio::net::UnixListener;
use tokio_stream::wrappers::UnixListenerStream;

pub mod calculator {
    tonic::include_proto!("calculator");
}

use calculator::{
    calculator_server::{Calculator, CalculatorServer},
    AddRequest, AddResponse, MulRequest, MulResponse,
};

#[derive(Default)]
struct CalculatorService;

#[tonic::async_trait]
impl Calculator for CalculatorService {
    async fn add(
        &self,
        request: Request<AddRequest>,
    ) -> Result<Response<AddResponse>, Status> {
        let req = request.into_inner();
        Ok(Response::new(AddResponse { result: req.a + req.b }))
    }

    async fn mul(
        &self,
        request: Request<MulRequest>,
    ) -> Result<Response<MulResponse>, Status> {
        let req = request.into_inner();
        Ok(Response::new(MulResponse { result: req.a * req.b }))
    }
}

const SOCKET_PATH: &str = "/tmp/grpc_rust.sock";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Remove stale socket
    let _ = std::fs::remove_file(SOCKET_PATH);

    let uds = UnixListener::bind(SOCKET_PATH)?;
    let stream = UnixListenerStream::new(uds);

    println!("gRPC/Rust server on {}", SOCKET_PATH);

    Server::builder()
        .add_service(CalculatorServer::new(CalculatorService))
        .serve_with_incoming(stream)
        .await?;

    Ok(())
}
```

---

## 7. Kernel-Level Performance Analysis

### 7.1 System Call Overhead

A **system call** (syscall) is a controlled transition from **user mode** (ring 3) to **kernel mode** (ring 0). This transition is expensive:

```
User mode → kernel mode transition cost:
  - SYSCALL instruction: ~5 ns (modern x86-64 with KPTI off)
  - With KPTI (Meltdown mitigation): ~100–200 ns (requires CR3 switch = TLB flush)
  - Context: ~2–10 µs total round-trip for a simple syscall
```

**KPTI (Kernel Page Table Isolation):** Post-Spectre/Meltdown, Linux keeps separate page tables for user and kernel mode. Switching between them flushes the TLB — very expensive. This is why high-performance systems use shared memory to **avoid syscalls entirely** in the hot path.

| IPC Mechanism  | Syscalls per message (round trip) |
|----------------|----------------------------------|
| Shared Memory  | 0 (after setup)                  |
| UDS            | 2 (send + recv)                  |
| TCP            | 2+ (plus ACK processing)         |
| gRPC/UDS       | 2+ (HTTP/2 framing overhead)     |
| gRPC/TCP       | 2+ + network stack               |

### 7.2 Context Switches

A **context switch** occurs when the CPU switches from running one thread/process to another. The cost:
- Save all registers (FPU, GPRs, SSE/AVX state)
- Switch page tables (if different processes)
- Invalidate TLB (or use PCID to avoid this)
- Load new register state
- Cold caches — the new thread's working set may not be in cache

**Cost: 1–10 µs per context switch.** For blocking I/O (UDS, TCP), a context switch typically occurs on each `send()`/`recv()` pair if the receiver is blocked.

**Shared memory avoids context switches** — the producer writes, the consumer's spin loop detects it, no kernel involvement. The flip side: one core is burning 100% CPU on the spin loop.

### 7.3 Cache Behavior — The Hidden Performance Dimension

This is where expert knowledge distinguishes great systems engineers.

**Shared Memory (Producer/Consumer on different cores):**

```
CPU Core 0 (producer)           CPU Core 1 (consumer)
L1 Cache: [tail=100]            L1 Cache: [tail=stale]
     │                                    │
     │  MESI protocol: when producer      │
     │  writes tail, Core 1's cache       │
     │  line is INVALIDATED               │
     ▼                                    ▼
Producer stores new tail     Consumer's cache miss on tail
                             → Fetch from L3 or producer's L1
                             → Cost: 40–100 ns (L3 hit) or 200+ ns (DRAM)
```

**This is why shared memory throughput is not unlimited.** Each atomic operation involves a **coherency traffic burst** on the cache bus.

**UDS (kernel copy):**

```
Kernel sk_buff resides in kernel virtual address space.
When the kernel copies user buffer → sk_buff:
  - The user's buffer may be hot in L1 (just written)
  - The sk_buff pages are kernel pages — likely L3 cold
  - memcpy() of 256 bytes is ~5–10 ns if both buffers are L1 hot
  - But sk_buff allocation (kmalloc) adds overhead
```

**TCP (additional overhead):**

```
Additional copies vs UDS:
  1. User buffer → TCP send buffer (kernel sk_buff)
  2. TCP checksum computation (can be offloaded to NIC, but not on loopback)
  3. IP header processing
  4. Copy sk_buff pointer through loopback driver
  5. TCP receive processing, reassembly
  6. TCP recv buffer → user buffer
```

### 7.4 NUMA — Non-Uniform Memory Access

On multi-socket servers (common in data centers), memory is divided between **NUMA nodes**. Memory attached to CPU socket 0 is fast for cores on socket 0, but slow for cores on socket 1:

```
Socket 0                    Socket 1
[Core 0 | Core 1 | Core 2]  [Core 4 | Core 5 | Core 6]
     [Local RAM]                  [Local RAM]
         │                              │
         └────── QPI/UPI link ──────────┘
                 (latency: 2–3x local)
```

**Impact on shared memory IPC:**
- If producer runs on Socket 0 and consumer on Socket 1, shared memory accesses go through QPI
- Latency can be **3x higher** than same-socket communication
- Fix: Pin processes to same NUMA node using `numactl` or `sched_setaffinity`

```bash
# Run producer and consumer on NUMA node 0
numactl --cpunodebind=0 --membind=0 ./producer
numactl --cpunodebind=0 --membind=0 ./consumer
```

### 7.5 Memory Allocation Patterns

**Shared memory:** Setup cost is `shm_open` + `ftruncate` + `mmap`. After that, the memory is a fixed region — **zero allocation** in the hot path. No `malloc`, no GC, no fragmentation.

**UDS:** Each `send()` allocates a `sk_buff` (socket buffer) in kernel space via `kmalloc`. These are returned from a slab allocator (fast, but not zero-cost). Each `recv()` frees one. Under high message rates, this constant alloc/free churns the kernel slab allocator.

**TCP:** Same as UDS plus additional TCP buffer management (sk_buff cloning for retransmits).

**gRPC:** Additional allocations for HTTP/2 frames, protobuf encoding buffers, and the Go/Rust runtime's own heap.

---

## 8. Quantitative Performance Comparison

> The following numbers are representative of a modern x86-64 Linux machine (kernel 6.x, no Nagle, same NUMA node). Actual numbers vary by workload, message size, and hardware.

### 8.1 Latency (Round-Trip Time, small messages ≤ 256 bytes)

```
┌──────────────────────────┬────────────────┬───────────────────────────────┐
│ Mechanism                │ Latency (RTT)  │ Notes                         │
├──────────────────────────┼────────────────┼───────────────────────────────┤
│ Shared Memory (spinlock) │ 0.1 – 0.5 µs   │ No syscall; cache bounce cost │
│ Shared Memory (futex)    │ 1 – 3 µs       │ Kernel wakeup latency         │
│ UDS SEQPACKET            │ 3 – 8 µs       │ 2 syscalls + 1 copy           │
│ UDS STREAM               │ 3 – 9 µs       │ Similar + framing overhead    │
│ TCP (127.0.0.1) tuned    │ 8 – 20 µs      │ Full network stack            │
│ TCP (127.0.0.1) default  │ 30 – 100 µs    │ Nagle delay + ACK delay       │
│ gRPC over UDS            │ 50 – 200 µs    │ HTTP/2 + protobuf overhead    │
│ gRPC over TCP            │ 100 – 500 µs   │ All overheads combined        │
└──────────────────────────┴────────────────┴───────────────────────────────┘
```

### 8.2 Throughput (Messages/second, 256-byte messages, single core)

```
┌──────────────────────────┬─────────────────┬──────────────────────────────┐
│ Mechanism                │ Throughput      │ Notes                        │
├──────────────────────────┼─────────────────┼──────────────────────────────┤
│ Shared Memory (lock-free)│ 50–200 M msg/s  │ Cache bandwidth limited      │
│ UDS SEQPACKET            │ 1–5 M msg/s     │ Syscall + copy overhead      │
│ TCP tuned                │ 0.5–2 M msg/s   │ Network stack overhead       │
│ gRPC over UDS            │ 50–200 K RPC/s  │ HTTP/2 multiplexing helps    │
│ gRPC over TCP            │ 20–100 K RPC/s  │ Full overhead                │
└──────────────────────────┴─────────────────┴──────────────────────────────┘
```

### 8.3 CPU Overhead (per message, single direction)

```
┌────────────────────────┬──────────────────────────────────────────────────┐
│ Mechanism              │ CPU Overhead                                     │
├────────────────────────┼──────────────────────────────────────────────────┤
│ Shared Memory          │ ~1–5 ns (atomic store + cache coherency)         │
│ UDS                    │ ~300–800 ns (syscall + memcpy + sk_buff alloc)   │
│ TCP                    │ ~1–3 µs (syscall + TCP stack + IP + checksum)    │
│ gRPC (any transport)   │ ~10–50 µs (protobuf encode + HTTP/2 frame + TLS)│
└────────────────────────┴──────────────────────────────────────────────────┘
```

### 8.4 Data Copy Count Analysis

```
┌─────────────────────┬───────┬──────────────────────────────────────────────┐
│ Mechanism           │Copies │ Where                                        │
├─────────────────────┼───────┼──────────────────────────────────────────────┤
│ Shared Memory       │  0    │ Physical page is directly shared              │
│ UDS (sendmsg)       │  1    │ user buffer → kernel sk_buff                  │
│ UDS (recvmsg)       │  1    │ kernel sk_buff → user buffer                  │
│ TCP (send)          │  1–2  │ user → sock send buf → (loopback inject)      │
│ TCP (recv)          │  1–2  │ loopback recv → sock recv buf → user          │
│ gRPC (any)          │ 3–5   │ struct → protobuf bytes → HTTP/2 frame → sock│
└─────────────────────┴───────┴──────────────────────────────────────────────┘
```

---

## 9. Decision Framework

### 9.1 Choosing the Right IPC Mechanism

```
START: What do you need?
│
├─ Both processes on same machine?
│   ├─ NO  → TCP (or gRPC/TCP for structured RPCs)
│   └─ YES → continue ↓
│
├─ Need <1 µs latency? (trading, real-time audio, game engines)
│   ├─ YES → Shared Memory + Lock-Free Ring Buffer
│   └─ NO  → continue ↓
│
├─ Need structured RPCs with schema evolution?
│   ├─ YES → gRPC over UDS (local) or gRPC over TCP (remote)
│   └─ NO  → continue ↓
│
├─ Need message boundaries (not byte streams)?
│   ├─ YES → UDS SOCK_SEQPACKET or SOCK_DGRAM
│   └─ NO  → UDS SOCK_STREAM
│
├─ Need to pass file descriptors between processes?
│   └─ UDS with SCM_RIGHTS
│
├─ Need multi-process (not just two processes)?
│   ├─ Hub-spoke model → UDS (server manages connections)
│   └─ Many-to-many → Shared Memory ring per pair, or message broker
│
└─ Default for new services → UDS (simple, fast, no network overhead)
```

### 9.2 Anti-Patterns to Avoid

**Anti-pattern 1:** Using TCP for local IPC without `TCP_NODELAY`
- Nagle's algorithm buffers small writes for 40–200 ms → massive latency spikes
- Always set `TCP_NODELAY` for interactive/latency-sensitive local comms

**Anti-pattern 2:** Shared memory without cache-line alignment
- False sharing between head and tail → 10x performance degradation

**Anti-pattern 3:** Shared memory without memory barriers
- On x86: less catastrophic (TSO memory model) but still incorrect
- On ARM: catastrophic — reads can be reordered before writes

**Anti-pattern 4:** gRPC for high-frequency small messages
- 50+ µs per call is 50,000 ns — 50,000x slower than shared memory
- gRPC shines for: structured RPCs, schema evolution, cross-language, cross-machine

**Anti-pattern 5:** Spin-waiting without `pause` instruction on x86
- A tight `while(!available){}` loop causes CPU pipeline stalls
- `__asm__("pause")` (Rust: `std::hint::spin_loop()`) signals the CPU to reduce power and avoid memory order violations

---

## 10. Advanced Patterns

### 10.1 `io_uring` — Zero-Syscall I/O for UDS and TCP

**`io_uring`** (Linux 5.1+) is a kernel subsystem that allows batching of I/O operations through a pair of shared memory ring buffers between userspace and kernel. This dramatically reduces syscall overhead for UDS and TCP.

```c
/* io_uring conceptual flow for UDS read: */

/* Setup — done once */
io_uring_queue_init(QUEUE_DEPTH, &ring, 0);

/* Submit reads — no syscall per operation */
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_recv(sqe, client_fd, buf, buf_size, 0);
sqe->user_data = (uint64_t)ctx;  /* tag for completion */

/* Batch submit — one syscall for many operations */
io_uring_submit(&ring);

/* Wait for completions */
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
/* cqe->res = bytes received */
io_uring_cqe_seen(&ring, cqe);
```

**io_uring advantage:** In the best case (kernel-side polling), zero syscalls per I/O operation. The kernel polls the submission ring for new requests and posts results to the completion ring.

### 10.2 Huge Pages with Shared Memory

Standard 4 KB pages mean a 1 GB shared memory region needs **262,144 TLB entries** — far more than the TLB can hold. With **2 MB huge pages**, only **512 TLB entries** are needed.

```c
/* Allocate shared memory with huge pages */
void *ptr = mmap(
    NULL,
    HUGE_PAGE_ALIGNED_SIZE,
    PROT_READ | PROT_WRITE,
    MAP_SHARED | MAP_ANONYMOUS | MAP_HUGETLB,
    -1,
    0
);

/* Or via /dev/shm with mmap hint: */
madvise(ptr, size, MADV_HUGEPAGE);  /* transparent huge pages */
```

**Transparent Huge Pages (THP):** The kernel can automatically promote 4 KB pages into 2 MB pages for frequently accessed regions. Enable with:
```bash
echo always > /sys/kernel/mm/transparent_hugepage/enabled
```

### 10.3 CPU Affinity and Isolation

For maximum shared memory performance:

```c
/* Pin producer to CPU 0, consumer to CPU 1 (same socket) */
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(0, &cpuset);                            /* CPU 0 for this thread */
pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
```

```bash
# Isolate CPUs 2 and 3 from OS scheduler interference
# Add to kernel boot params:
isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3

# Then run:
taskset -c 2 ./producer
taskset -c 3 ./consumer
```

With CPU isolation, the OS scheduler never preempts your process on those CPUs, eliminating jitter. Latency drops from "1 µs average, 50 µs p99" to "0.5 µs average, 1 µs p99".

---

## 11. Complete Benchmark Harness in C

```c
/*
 * ipc_bench.c — Unified latency benchmark for all three IPC mechanisms.
 *
 * Compile: gcc -O2 -o ipc_bench ipc_bench.c -lpthread -lrt
 * Usage:
 *   ./ipc_bench shm      # shared memory ping-pong
 *   ./ipc_bench uds      # unix domain socket ping-pong
 *   ./ipc_bench tcp      # tcp loopback ping-pong
 */

#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE

#include <sys/socket.h>
#include <sys/un.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdatomic.h>
#include <time.h>
#include <errno.h>

/* ── Configuration ──────────────────────────────────────────────────────── */
#define BENCH_ITERATIONS  100000
#define MSG_SIZE          64
#define WARMUP_ITERS      1000
#define UDS_PATH          "/tmp/ipc_bench.sock"
#define TCP_PORT          19876
#define SHM_NAME          "/ipc_bench_shm"

/* ── Timing ─────────────────────────────────────────────────────────────── */
static inline uint64_t
now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/* ── Statistics ─────────────────────────────────────────────────────────── */
static void
print_stats(const char *label, uint64_t *samples, size_t n)
{
    /* Simple bubble sort for percentiles — replace with qsort for production */
    uint64_t *sorted = malloc(n * sizeof(uint64_t));
    memcpy(sorted, samples, n * sizeof(uint64_t));

    /* Insertion sort (fine for small n in benchmark context) */
    for (size_t i = 1; i < n; i++) {
        uint64_t key = sorted[i];
        ssize_t  j   = (ssize_t)i - 1;
        while (j >= 0 && sorted[j] > key) {
            sorted[j + 1] = sorted[j];
            j--;
        }
        sorted[j + 1] = key;
    }

    uint64_t sum = 0;
    for (size_t i = 0; i < n; i++) sum += sorted[i];

    printf("\n=== %s (n=%zu, msg=%d bytes) ===\n", label, n, MSG_SIZE);
    printf("  avg:  %7.2f µs\n", (double)sum / n / 1000.0);
    printf("  min:  %7.2f µs\n", (double)sorted[0] / 1000.0);
    printf("  p50:  %7.2f µs\n", (double)sorted[n * 50 / 100] / 1000.0);
    printf("  p90:  %7.2f µs\n", (double)sorted[n * 90 / 100] / 1000.0);
    printf("  p99:  %7.2f µs\n", (double)sorted[n * 99 / 100] / 1000.0);
    printf("  p999: %7.2f µs\n", (double)sorted[n * 999 / 1000] / 1000.0);
    printf("  max:  %7.2f µs\n", (double)sorted[n - 1] / 1000.0);

    free(sorted);
}

/* ─────────────────────────────────────────────────────────────────────────
 * SHARED MEMORY BENCHMARK
 * ─────────────────────────────────────────────────────────────────────── */

typedef struct {
    atomic_uint_least64_t ping;  /* parent → child signal  */
    uint8_t _pad0[56];
    atomic_uint_least64_t pong;  /* child → parent signal  */
    uint8_t _pad1[56];
    uint8_t data[MSG_SIZE];
} ShmPingPong;

static void
bench_shm(void)
{
    int fd = shm_open(SHM_NAME, O_CREAT | O_EXCL | O_RDWR, 0600);
    if (fd < 0) { perror("shm_open"); exit(1); }
    ftruncate(fd, sizeof(ShmPingPong));

    ShmPingPong *shm = mmap(NULL, sizeof(ShmPingPong),
                             PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);

    memset(shm, 0, sizeof(ShmPingPong));

    pid_t child = fork();
    if (child == 0) {
        /* Child: consumer/pong */
        uint64_t expected = 1;
        for (uint64_t i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
            /* Wait for ping */
            while (atomic_load_explicit(&shm->ping, memory_order_acquire) != expected)
                __asm__ volatile("pause" ::: "memory");
            /* Send pong */
            atomic_store_explicit(&shm->pong, expected, memory_order_release);
            expected++;
        }
        munmap(shm, sizeof(ShmPingPong));
        exit(0);
    }

    /* Parent: producer/ping */
    uint64_t  samples[BENCH_ITERATIONS];
    uint64_t  seq = 1;

    for (uint64_t i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
        uint64_t t0 = now_ns();

        atomic_store_explicit(&shm->ping, seq, memory_order_release);
        while (atomic_load_explicit(&shm->pong, memory_order_acquire) != seq)
            __asm__ volatile("pause" ::: "memory");

        uint64_t elapsed = now_ns() - t0;

        if (i >= WARMUP_ITERS) {
            samples[i - WARMUP_ITERS] = elapsed;
        }
        seq++;
    }

    waitpid(child, NULL, 0);
    munmap(shm, sizeof(ShmPingPong));
    shm_unlink(SHM_NAME);

    print_stats("Shared Memory (spin)", samples, BENCH_ITERATIONS);
}

/* ─────────────────────────────────────────────────────────────────────────
 * UDS BENCHMARK
 * ─────────────────────────────────────────────────────────────────────── */

static void
bench_uds(void)
{
    unlink(UDS_PATH);

    int sv[2];
    /* socketpair: creates a connected pair — avoids bind/connect */
    if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) < 0) {
        perror("socketpair"); exit(1);
    }

    pid_t child = fork();
    if (child == 0) {
        close(sv[0]);  /* child uses sv[1] */
        uint8_t buf[MSG_SIZE];
        for (int i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
            ssize_t n = recv(sv[1], buf, sizeof(buf), 0);
            if (n <= 0) exit(1);
            send(sv[1], buf, (size_t)n, 0);
        }
        close(sv[1]);
        exit(0);
    }

    close(sv[1]);  /* parent uses sv[0] */

    uint8_t  send_buf[MSG_SIZE];
    uint8_t  recv_buf[MSG_SIZE];
    uint64_t samples[BENCH_ITERATIONS];

    memset(send_buf, 0xAB, sizeof(send_buf));

    for (int i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
        uint64_t t0 = now_ns();
        send(sv[0], send_buf, sizeof(send_buf), 0);
        recv(sv[0], recv_buf, sizeof(recv_buf), 0);
        uint64_t elapsed = now_ns() - t0;

        if (i >= WARMUP_ITERS) {
            samples[i - WARMUP_ITERS] = elapsed;
        }
    }

    waitpid(child, NULL, 0);
    close(sv[0]);

    print_stats("Unix Domain Socket (SEQPACKET)", samples, BENCH_ITERATIONS);
}

/* ─────────────────────────────────────────────────────────────────────────
 * TCP BENCHMARK
 * ─────────────────────────────────────────────────────────────────────── */

static void
set_tcp_opts(int fd)
{
    int flag = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY,  &flag, sizeof(flag));
    setsockopt(fd, IPPROTO_TCP, TCP_QUICKACK, &flag, sizeof(flag));
    setsockopt(fd, SOL_SOCKET,  SO_REUSEADDR, &flag, sizeof(flag));
}

static void
bench_tcp(void)
{
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    set_tcp_opts(server_fd);

    struct sockaddr_in addr = {0};
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port        = htons(TCP_PORT);

    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 1);

    pid_t child = fork();
    if (child == 0) {
        /* Child: server */
        int client_fd = accept(server_fd, NULL, NULL);
        set_tcp_opts(client_fd);
        close(server_fd);

        uint8_t buf[MSG_SIZE];
        for (int i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
            ssize_t n = recv(client_fd, buf, sizeof(buf), 0);
            if (n <= 0) break;
            send(client_fd, buf, (size_t)n, 0);
        }
        close(client_fd);
        exit(0);
    }

    /* Parent: client */
    usleep(50000);  /* give server time to start */

    int client_fd = socket(AF_INET, SOCK_STREAM, 0);
    set_tcp_opts(client_fd);
    connect(client_fd, (struct sockaddr *)&addr, sizeof(addr));
    close(server_fd);

    uint8_t  send_buf[MSG_SIZE];
    uint8_t  recv_buf[MSG_SIZE];
    uint64_t samples[BENCH_ITERATIONS];

    memset(send_buf, 0xCD, sizeof(send_buf));

    for (int i = 0; i < BENCH_ITERATIONS + WARMUP_ITERS; i++) {
        uint64_t t0 = now_ns();
        send(client_fd, send_buf, sizeof(send_buf), 0);
        recv(client_fd, recv_buf, sizeof(recv_buf), 0);
        uint64_t elapsed = now_ns() - t0;

        if (i >= WARMUP_ITERS) {
            samples[i - WARMUP_ITERS] = elapsed;
        }
        /* Re-arm quick ACK on every recv */
        int f = 1;
        setsockopt(client_fd, IPPROTO_TCP, TCP_QUICKACK, &f, sizeof(f));
    }

    waitpid(child, NULL, 0);
    close(client_fd);

    print_stats("TCP Loopback (127.0.0.1, TCP_NODELAY)", samples, BENCH_ITERATIONS);
}

/* ── Entry point ────────────────────────────────────────────────────────── */
int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [shm|uds|tcp|all]\n", argv[0]);
        return 1;
    }

    const char *mode = argv[1];

    if (strcmp(mode, "shm") == 0 || strcmp(mode, "all") == 0) bench_shm();
    if (strcmp(mode, "uds") == 0 || strcmp(mode, "all") == 0) bench_uds();
    if (strcmp(mode, "tcp") == 0 || strcmp(mode, "all") == 0) bench_tcp();

    return 0;
}
```

**Compile and run:**
```bash
gcc -O2 -march=native -o ipc_bench ipc_bench.c -lpthread -lrt
./ipc_bench all
```

---

## 12. Mental Models for Experts

### 12.1 The Fundamental Trade-off Triad

Every IPC choice navigates three dimensions:

```
              LATENCY (speed)
                   ▲
                   │ Shared Memory
                   │   (0.1–0.5 µs)
                   │
                   │   UDS
                   │   (3–8 µs)
                   │
                   │          TCP / gRPC
                   │          (8–500 µs)
                   └──────────────────────────────→
              COMPLEXITY                    PORTABILITY
            (hard to sync)                 (crosses machines,
                                            languages, services)
```

You rarely get all three. Shared memory is fast but requires careful synchronization. gRPC is portable and structured but slow. UDS is the pragmatic middle ground.

### 12.2 The Kernel as a Cost Center

Every kernel boundary crossing costs cycles. The key mental model:

> **"Staying in userspace = free. Entering kernel = pay a toll."**

- Shared memory hot path: 0 kernel crossings. Cost = cache coherency only.
- UDS: 2 kernel crossings (send + recv) + 1 memcpy inside kernel.
- TCP: 2 kernel crossings + full network stack (dozens of function calls).
- gRPC: same as transport + serialization + HTTP/2 framing.

When you need to push performance to the limit, count your kernel crossings.

### 12.3 Cognitive Model: Think in Data Flows, Not APIs

Expert systems engineers do not think "I'll use TCP" or "I'll use shared memory." They think:

1. **Where does the data live?** (same cache? same NUMA? same machine? same datacenter?)
2. **How large is each unit?** (1 byte? 256 bytes? 1 MB? 1 GB?)
3. **What is the access pattern?** (sequential? random? bursty? steady?)
4. **Who coordinates?** (one writer + one reader? multiple writers? need ordering?)
5. **What is the failure model?** (what if one side crashes? message in flight?)

The IPC mechanism falls out naturally from these answers.

### 12.4 Deliberate Practice Prescription

To internalize these concepts at the level of expert intuition:

1. **Implement the benchmark harness** — run it on your machine, observe the actual numbers. Numbers anchor intuition.
2. **Break things intentionally** — remove `TCP_NODELAY` and observe Nagle delay. Remove memory barriers in the ring buffer and watch corruption. Misalign cache lines and measure the false sharing penalty.
3. **Profile with hardware counters** — use `perf stat -e cache-misses,cache-references,context-switches,page-faults` to see the exact hardware-level cost of each IPC mechanism.
4. **Read kernel source** — `net/unix/af_unix.c` (UDS), `net/ipv4/tcp.c` (TCP), `mm/mmap.c` (mmap). Reading source is the highest-leverage investment.
5. **Chunking practice** — when you see "high-frequency small message IPC," your brain should automatically respond: "shared memory + lock-free ring + SPSC + cache-aligned atomics + CPU pinning." Build that chunk by repeated exposure.

### 12.5 Psychological Principle: The Performance Mental Simulation

Before writing code, run a mental simulation:

```
For each message exchanged:
  1. How many cache lines does the data touch?
  2. Are those cache lines hot or cold?
  3. How many CPU cores are involved (coherency traffic)?
  4. How many times does the data cross the user/kernel boundary?
  5. How many memory allocations happen?
  6. What is the context switch probability?

Multiply each cost by message frequency → total throughput budget.
If budget exceeded → optimization needed → pick IPC mechanism with fewer steps.
```

This mental simulation, practiced until automatic, is what separates a systems engineer who writes correct code from one who writes fast, correct code.

---

## Appendix A: Quick Reference

### System Calls Summary

| Operation           | Shared Memory      | UDS                | TCP                |
|---------------------|-------------------|-------------------|-------------------|
| Create              | `shm_open`+`mmap` | `socket`+`bind`   | `socket`+`bind`   |
| Connect             | N/A               | `connect`         | `connect`         |
| Send data           | *pointer write*   | `send`/`sendmsg`  | `send`/`write`    |
| Receive data        | *pointer read*    | `recv`/`recvmsg`  | `recv`/`read`     |
| Synchronize         | atomics/futex     | implicit          | implicit          |
| Cleanup             | `munmap`+`unlink` | `close`+`unlink`  | `close`           |

### Kernel Tuning for Production

```bash
# Increase max socket buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'
sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'

# Increase listen backlog
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Shared memory limits
sysctl -w kernel.shmmax=68719476736   # 64 GB
sysctl -w kernel.shmall=4294967296    # 16 GB in pages

# Disable transparent huge pages for latency-critical (reduces jitter)
echo never > /sys/kernel/mm/transparent_hugepage/enabled

# Enable huge pages for throughput-critical
echo 1024 > /proc/sys/vm/nr_hugepages  # 1024 × 2MB = 2GB
```

### Rust Crate Recommendations

| Use Case              | Crate                | Note                              |
|-----------------------|----------------------|-----------------------------------|
| Shared Memory         | `shared_memory`      | Safe wrapper over mmap            |
| Lock-free structures  | `crossbeam`          | Production-grade MPMC queues      |
| UDS async             | `tokio` + `UnixListener` | Best-in-class async runtime  |
| TCP async             | `tokio`              | Same runtime, seamless            |
| gRPC                  | `tonic`              | Official Rust gRPC                |
| Protobuf              | `prost`              | Used by tonic                     |
| io_uring              | `io-uring`           | Low-level; `tokio-uring` for async|

### Go Package Recommendations

| Use Case              | Package              | Note                              |
|-----------------------|----------------------|-----------------------------------|
| Shared Memory         | `syscall.Mmap`       | Built-in, no deps                 |
| UDS                   | `net.Listen("unix")` | Built-in, idiomatic               |
| TCP                   | `net.Listen("tcp")`  | Built-in                          |
| gRPC                  | `google.golang.org/grpc` | Official                      |
| Protobuf              | `google.golang.org/protobuf` | Official                  |
| io_uring              | `github.com/iceber/iouring-go` | Community               |

---

*End of Guide — Shared Memory vs UDS vs TCP: Kernel-Level Deep Dive*

This is going to be a deep, production-grade guide. Let me build it in full.Here is your complete guide. Here's a map of what's inside:

---

**What the guide covers end-to-end:**

**Foundation first** — The guide opens with Linux virtual memory, page tables, TLB, and cache hierarchy because every IPC difference is rooted in how these work. You can't reason about performance without understanding what the MMU does.

**Shared Memory** — Full coverage of `mmap`, POSIX `shm_open`, SysV (legacy), and how the kernel sets up the page table so two processes share the same physical RAM with zero copies. The lock-free SPSC ring buffer is built from scratch in all three languages with proper memory barrier semantics (`ACQUIRE`/`RELEASE`) explained, cache-line alignment for head/tail, and the `pause` instruction for spin hints.

**UDS** — Kernel path traced through `unix_stream_sendmsg` → `sk_buff` allocation → peer socket receive queue. All three socket types compared (`STREAM`, `DGRAM`, `SEQPACKET`). SCM_RIGHTS (file descriptor passing) is covered as the zero-copy superpower most engineers miss. Abstract namespace explained.

**TCP** — The full loopback stack path is traced step-by-step. All critical socket options (`TCP_NODELAY`, `TCP_QUICKACK`, `SO_REUSEPORT`) are implemented with justification, not magic numbers.

**gRPC** — All four protocol layers (protobuf → HTTP/2 → transport) demystified. Protobuf binary encoding shown byte-by-byte. Switching between UDS and TCP transport in gRPC is a one-line change — shown in Go and Rust (tonic).

**Quantitative tables** — Latency, throughput, copy count, and CPU overhead all compared across all mechanisms with realistic numbers.

**Benchmark harness in C** — A complete `ipc_bench.c` that forks producer/consumer pairs for all three mechanisms and produces min/p50/p90/p99/p999/max statistics.

**Kernel tuning** — Production `sysctl` settings for buffers, backlog, huge pages, and shared memory limits.