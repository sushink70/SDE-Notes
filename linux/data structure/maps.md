# eBPF Maps: The Complete In-Depth Guide
> *Kernel-resident data structures as the persistent storage and communication channel of eBPF*

---

## Table of Contents

1. [Conceptual Foundation — What Are eBPF Maps?](#1-conceptual-foundation)
2. [Kernel Architecture — How Maps Exist in the Kernel](#2-kernel-architecture)
3. [The `bpf()` Syscall — The Gate Between Worlds](#3-the-bpf-syscall)
4. [Map Lifecycle — Creation, Reference Counting, Destruction](#4-map-lifecycle)
5. [Map Operations — CRUD at the Kernel Boundary](#5-map-operations)
6. [Map Flags — Controlling Behaviour at Creation](#6-map-flags)
7. [All Map Types — Deep Dive into Every Type](#7-all-map-types)
8. [Per-CPU Maps — Eliminating Lock Contention](#8-per-cpu-maps)
9. [Ring Buffer Maps — High-Throughput Event Streaming](#9-ring-buffer-maps)
10. [Map-in-Map — Composing Data Structures](#10-map-in-map)
11. [BPF Filesystem (BPFFS) — Pinning and Persistence](#11-bpf-filesystem)
12. [Concurrency and Synchronization](#12-concurrency-and-synchronization)
13. [Memory Layout and Performance](#13-memory-layout-and-performance)
14. [BTF and Map Type Information](#14-btf-and-map-type-information)
15. [C Implementation — libbpf Full Examples](#15-c-implementation)
16. [Rust Implementation — Aya Full Examples](#16-rust-implementation)
17. [Advanced Patterns](#17-advanced-patterns)
18. [Introspection and Debugging](#18-introspection-and-debugging)
19. [Mental Models and Decision Trees](#19-mental-models-and-decision-trees)

---

## 1. Conceptual Foundation

### What Problem Do Maps Solve?

eBPF programs run inside the Linux kernel as **event-driven callbacks**. When a packet arrives, when a syscall fires, when a tracepoint is hit — your eBPF program runs, does its work, and **returns**. It has no persistent local state between invocations.

This creates a fundamental problem:

```
Invocation 1: packet arrives → eBPF runs → counts packet → returns → ALL STATE GONE
Invocation 2: another packet → eBPF runs → cannot see count from invocation 1
```

Maps solve this. They are **kernel-resident data structures** that:
- Survive between eBPF program invocations (persistent state)
- Are **shared** between multiple eBPF program instances (cross-CPU)
- Are **accessible from userspace** via the `bpf()` syscall (cross-privilege communication)
- Are **typed** at creation — key size, value size, maximum entries are fixed

### The Two Roles of Maps

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ROLE 1: PERSISTENT STATE                         │
│                                                                         │
│   eBPF Program                    eBPF Map (in kernel)                  │
│   (runs on event)   ──write──►  [ key: dest_ip   ]                      │
│                                  [ value: pkt_count ]                   │
│   (runs again)      ──read──►   reads previous count, increments        │
│                                                                         │
│                        ROLE 2: COMMUNICATION CHANNEL                    │
│                                                                         │
│   Userspace Process               eBPF Map (in kernel)                  │
│   (monitoring daemon) ◄──read──  [ key: cpu_id    ]                     │
│                                  [ value: latency  ]                    │
│   eBPF Program      ──write──►   writes measurements                    │
│   (kprobe on sched)                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Dual-Access Architecture

```
  USERSPACE                          KERNEL SPACE
  ─────────────────────────────────────────────────────
  
  monitoring_tool.c                  kprobe_prog.bpf.c
  │                                  │
  │  fd = bpf(BPF_MAP_CREATE, ...)   │  SEC("kprobe/sys_read")
  │  bpf(BPF_MAP_LOOKUP_ELEM, fd, k) │  int prog(ctx) {
  │  bpf(BPF_MAP_UPDATE_ELEM, fd, k) │    bpf_map_lookup_elem(&map, &key);
  │  bpf(BPF_MAP_DELETE_ELEM, fd, k) │    bpf_map_update_elem(&map, &k, &v, 0);
  │  bpf(BPF_MAP_GET_NEXT_KEY, ...)  │  }
  │                                  │
  └──────────────► MAP ◄─────────────┘
                   │
                   │  Lives in kernel memory
                   │  Reference counted (file descriptors)
                   │  Accessed by both sides
```

**Key concept**: The map is *not* copied between kernel and userspace. The userspace process accesses kernel memory through the `bpf()` syscall, which performs **copy_to_user** / **copy_from_user** to transfer data safely across the privilege boundary.

---

## 2. Kernel Architecture

### How Maps Are Stored in the Kernel

Every eBPF map, regardless of type, is backed by a **`struct bpf_map`** object in the kernel. This is the base "class" (in C struct terms). Specific map types embed or extend this structure.

```
  struct bpf_map (base, every map has this)
  ┌──────────────────────────────────────────┐
  │  const struct bpf_map_ops  *ops          │  ← vtable of function pointers
  │  struct bpf_map            *inner_map_meta│  ← for map-in-map types
  │  void                      *security     │  ← LSM security blob
  │  enum bpf_map_type          map_type     │  ← BPF_MAP_TYPE_HASH etc.
  │  u32                        key_size     │  ← bytes per key
  │  u32                        value_size   │  ← bytes per value
  │  u32                        max_entries  │  ← capacity
  │  u32                        map_flags    │  ← BPF_F_NO_PREALLOC etc.
  │  int                        spin_lock_off│  ← offset of spinlock in value
  │  u32                        id           │  ← globally unique map ID
  │  u32                        btf_key_type_id│  ← BTF type for key
  │  u32                        btf_value_type_id│← BTF type for value
  │  struct btf                *btf          │  ← BTF object reference
  │  struct bpf_map_memory      memory       │  ← accounting struct
  │  bool                       unpriv_array │
  │  bool                       frozen       │  ← BPF_F_RDONLY_PROG
  │  atomic64_t                 refcnt       │  ← reference count
  │  atomic64_t                 usercnt      │  ← userspace fd count
  │  struct work_struct         work         │  ← deferred free work
  │  struct mutex               freeze_mutex │
  │  u64                        writecnt     │
  └──────────────────────────────────────────┘
        │
        │ ops vtable (every map type implements these)
        ▼
  struct bpf_map_ops
  ┌──────────────────────────────────────────┐
  │  map_alloc_check()   ← validate params   │
  │  map_alloc()         ← allocate map      │
  │  map_release()       ← cleanup on close  │
  │  map_free()          ← free memory       │
  │  map_get_next_key()  ← iteration         │
  │  map_lookup_elem()   ← read a value      │
  │  map_update_elem()   ← write a value     │
  │  map_delete_elem()   ← remove a key      │
  │  map_push_elem()     ← for stack/queue   │
  │  map_pop_elem()      ← for stack/queue   │
  │  map_peek_elem()     ← non-destructive   │
  │  map_lookup_batch()  ← batch read        │
  │  map_update_batch()  ← batch write       │
  │  map_delete_batch()  ← batch delete      │
  │  map_mmap()          ← mmap support      │
  │  map_poll()          ← poll support      │
  └──────────────────────────────────────────┘
```

### Map Memory Allocation

When a map is created, the kernel allocates its backing store. The allocation strategy depends on the map type and flags:

```
  BPF_MAP_TYPE_ARRAY (no BPF_F_NO_PREALLOC):
  ──────────────────────────────────────────
  kvmalloc(max_entries * (value_size + alignment_padding))
  → One contiguous allocation upfront
  → Zero-initialized
  → Never freed until map is destroyed

  BPF_MAP_TYPE_HASH (with BPF_F_NO_PREALLOC):
  ──────────────────────────────────────────
  Hash table bucket array allocated upfront
  Individual elements allocated lazily on insert
  → kmalloc per element
  → Freed on delete

  BPF_MAP_TYPE_HASH (without BPF_F_NO_PREALLOC, default):
  ──────────────────────────────────────────
  All max_entries elements pre-allocated in a mempool
  → No kmalloc at runtime (interrupt-safe)
  → Memory used even if map is empty
```

**Why pre-allocation matters**: eBPF programs can run in interrupt context (e.g., XDP, tc). You **cannot** call `kmalloc(GFP_KERNEL)` in interrupt context because it might sleep. Pre-allocation ensures all memory is ready before the interrupt fires.

### The File Descriptor Model

Every map is accessed through a **file descriptor** in userspace. This is the Unix philosophy applied to kernel objects: everything is a file.

```
  Process A (fd=5 → map)          Process B (fd=7 → same map)
       │                                  │
       │  open("/proc/self/fd/5")          │
       ▼                                  ▼
  ┌──────────────────────────────────────────────────────┐
  │  struct file  (in struct files_struct of process A)   │
  │  struct file  (in struct files_struct of process B)   │
  │          both point to:                               │
  │                                                       │
  │  struct inode (anon_inode:bpf-map)                    │
  │       │                                               │
  │       └──► struct bpf_map  (refcnt=2)                 │
  │                  │                                    │
  │                  └──► actual map data in kernel mem   │
  └──────────────────────────────────────────────────────┘
```

The `refcnt` in `struct bpf_map` tracks how many references exist (both file descriptors and eBPF programs that use the map). The map is freed only when `refcnt` drops to zero.

---

## 3. The `bpf()` Syscall

The `bpf()` syscall is the **single gateway** for all eBPF operations from userspace. It was introduced in Linux 3.18 (2014).

```c
int bpf(int cmd, union bpf_attr *attr, unsigned int size);
```

**Parameters**:
- `cmd` — what operation to perform (see below)
- `attr` — a union of all possible parameter structs (passed by pointer)
- `size` — size of the `attr` struct (for forward compatibility)

### All Map-Related Commands

```
  bpf() cmd                   Purpose
  ─────────────────────────────────────────────────────────────
  BPF_MAP_CREATE              Allocate a new map, return fd
  BPF_MAP_LOOKUP_ELEM         Read a value by key
  BPF_MAP_UPDATE_ELEM         Write a value (insert/update)
  BPF_MAP_DELETE_ELEM         Remove a key-value pair
  BPF_MAP_GET_NEXT_KEY        Iterate: get next key after given key
  BPF_MAP_LOOKUP_AND_DELETE_ELEM  Atomic read+delete (for queues)
  BPF_MAP_FREEZE              Make map immutable (no more writes)
  BPF_MAP_LOOKUP_BATCH        Read multiple entries at once
  BPF_MAP_UPDATE_BATCH        Write multiple entries at once
  BPF_MAP_DELETE_BATCH        Delete multiple entries at once
  BPF_MAP_LOOKUP_AND_DELETE_BATCH  Batch atomic read+delete
  BPF_OBJ_PIN                 Pin map to BPF filesystem
  BPF_OBJ_GET                 Get fd to pinned map by path
  BPF_MAP_GET_FD_BY_ID        Get fd from global map ID
  BPF_OBJ_GET_INFO_BY_FD     Get map metadata (type, sizes, etc.)
```

### The `union bpf_attr` for Map Creation

```c
union bpf_attr {
    struct { /* BPF_MAP_CREATE */
        __u32   map_type;        /* one of BPF_MAP_TYPE_* */
        __u32   key_size;        /* size of key in bytes */
        __u32   value_size;      /* size of value in bytes */
        __u32   max_entries;     /* maximum number of entries */
        __u32   map_flags;       /* BPF_F_* flags */
        __u32   inner_map_fd;    /* fd of inner map (for map-in-map) */
        __u32   numa_node;       /* NUMA node for allocation */
        char    map_name[BPF_OBJ_NAME_LEN]; /* human-readable name */
        __u32   map_ifindex;     /* netdev ifindex for offloaded maps */
        __u32   btf_fd;          /* fd to BTF object */
        __u32   btf_key_type_id; /* BTF type ID for key */
        __u32   btf_value_type_id; /* BTF type ID for value */
        __u32   btf_vmlinux_value_type_id; /* for some special maps */
    };
    /* ... other fields for other commands ... */
};
```

### Syscall Call Flow — BPF_MAP_CREATE

```
  userspace: bpf(BPF_MAP_CREATE, &attr, sizeof(attr))
                │
                │ enters kernel via syscall gate
                ▼
  SYSCALL_DEFINE3(bpf, int, cmd, union bpf_attr __user *, uattr, unsigned int, size)
                │
                ├─ copy_from_user(&attr, uattr, size)   ← copy params from userspace
                ├─ security_bpf(cmd, &attr, size)        ← LSM check
                │
                ▼
  map_create(&attr)
                │
                ├─ find_and_alloc_map(&attr)
                │       │
                │       ├─ bpf_map_types[attr.map_type]  ← lookup vtable
                │       ├─ ops->map_alloc_check(&attr)   ← validate params
                │       ├─ bpf_map_alloc_percpu or kmalloc for struct bpf_map
                │       └─ ops->map_alloc(&attr)         ← allocate backing store
                │
                ├─ bpf_map_charge_memlock()              ← account memory against RLIMIT_MEMLOCK
                ├─ security_bpf_map_alloc(map)           ← LSM hook
                ├─ bpf_map_get_id(map)                   ← assign global unique ID
                │
                └─ bpf_map_new_fd(map)
                        │
                        ├─ anon_inode_getfd("bpf-map", &bpf_map_fops, map, O_RDWR|O_CLOEXEC)
                        └─ returns fd to userspace
```

---

## 4. Map Lifecycle

### Reference Counting — The Core Mechanism

Understanding reference counting is essential to understanding when maps are freed.

A map has **two reference counters**:

1. **`refcnt`** (atomic64_t) — total references: incremented by both fds AND loaded programs
2. **`usercnt`** (atomic64_t) — userspace fd references only

```
  Timeline:

  t=0: bpf(BPF_MAP_CREATE)
       → map allocated
       → refcnt=1, usercnt=1  (the returned fd holds one reference)

  t=1: bpf(BPF_PROG_LOAD) with map referenced in bytecode
       → verifier finds map fd in BPF_LD_MAP_FD instructions
       → calls bpf_map_inc(map) for each reference in the program
       → refcnt=2, usercnt=1  (program holds an additional ref)

  t=2: userspace closes the fd
       → bpf_map_put_uref(map): usercnt=0, refcnt=1
       → map is NOT freed! program still holds a reference

  t=3: program is unloaded (fd closed or process exits)
       → bpf_map_put(map): refcnt=0
       → map_free() called via work queue
       → memory released
```

**Critical insight**: You can close the map fd in userspace after loading your eBPF program. The program's reference keeps the map alive. This is how "fire and forget" monitoring tools work — load the program, close the fd, and the map persists as long as the program runs.

### Map Pinning Extends Lifetime

Without pinning, when ALL processes with map fds exit AND all programs using the map are unloaded, the map disappears. **Pinning** creates a persistent path in the BPF filesystem:

```
  bpf(BPF_OBJ_PIN, {pathname="/sys/fs/bpf/my_map", bpf_fd=fd}, ...)
       │
       ├─ creates a file at /sys/fs/bpf/my_map
       ├─ the file holds a reference to the map (refcnt++)
       └─ map now survives even if fd is closed and programs are unloaded

  To access the pinned map later:
  fd = bpf(BPF_OBJ_GET, {pathname="/sys/fs/bpf/my_map"}, ...)
       │
       └─ returns a new fd to the pinned map (refcnt++)
```

---

## 5. Map Operations

### From eBPF Program (Kernel Side) — In-kernel Helpers

Inside an eBPF program, you use **BPF helper functions**. These are not syscalls — they are direct function calls into the kernel's BPF helper infrastructure. The verifier checks that they are called correctly.

```c
// ─────────────── LOOKUP ───────────────
void *bpf_map_lookup_elem(struct bpf_map *map, const void *key);
// Returns: pointer to value in map (NOT a copy), or NULL if not found
// CRITICAL: the returned pointer is DIRECT kernel memory
//           - for hash maps: pointer into the hash bucket element
//           - for array maps: pointer into the pre-allocated array slot
//           - you can READ and WRITE through this pointer
//           - the pointer is ONLY valid during the current eBPF invocation
//           - after your eBPF program returns, the pointer may be invalid

// ─────────────── UPDATE ───────────────
long bpf_map_update_elem(struct bpf_map *map, const void *key,
                         const void *value, u64 flags);
// flags:
//   BPF_ANY (0)    → insert if not exists, update if exists
//   BPF_NOEXIST    → only insert (fail if key already exists)
//   BPF_EXIST      → only update (fail if key does not exist)
// Returns: 0 on success, negative errno on failure

// ─────────────── DELETE ───────────────
long bpf_map_delete_elem(struct bpf_map *map, const void *key);
// Returns: 0 on success, -ENOENT if key not found

// ─────────────── PUSH/POP (stack/queue) ───────────────
long bpf_map_push_elem(struct bpf_map *map, const void *value, u64 flags);
long bpf_map_pop_elem(struct bpf_map *map, void *value);
long bpf_map_peek_elem(struct bpf_map *map, void *value);
```

### Lookup Semantics — A Critical Detail

The return value of `bpf_map_lookup_elem` is a **direct pointer into kernel memory**, not a copy. This has profound implications:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  BPF_MAP_TYPE_ARRAY lookup:                                     │
  │                                                                 │
  │  map memory: [ val0 ][ val1 ][ val2 ] ... [ valN ]             │
  │                          ▲                                       │
  │  bpf_map_lookup_elem(map, &key=1) returns pointer here ─────►  │
  │                                                                 │
  │  You can do: *((__u64*)ptr) += 1;  ← DIRECT increment in place │
  │  This is an IN-PLACE write to kernel memory                     │
  │                                                                 │
  │  BUT: there is NO synchronization!                              │
  │  Two CPUs can both lookup and both try to increment             │
  │  → data race → undefined behavior                               │
  │                                                                 │
  │  Solutions:                                                     │
  │  1. Use BPF_MAP_TYPE_PERCPU_ARRAY (one slot per CPU)           │
  │  2. Use bpf_spin_lock() in the value struct                     │
  │  3. Use BPF_XADD / atomic operations                            │
  └─────────────────────────────────────────────────────────────────┘
```

### From Userspace — Syscall Interface

```c
// LOOKUP
struct {
    __u32 map_fd;
    __aligned_u64 key;      // pointer to key buffer
    __aligned_u64 value;    // pointer to value output buffer
    __u64 flags;
} attr;
// IMPORTANT: userspace receives a COPY of the value, not a pointer
// The kernel does copy_to_user() to transfer data across the boundary

// UPDATE
// Same attr, but value is an INPUT buffer (copy_from_user)

// GET_NEXT_KEY (iteration)
// key = NULL → returns the FIRST key in the map
// key = &some_key → returns the key AFTER some_key
// Returns -ENOENT when there are no more keys
```

### Iteration — GET_NEXT_KEY Semantics

`BPF_MAP_GET_NEXT_KEY` enables full map traversal:

```
  Hash map contents: { A→1, B→2, C→3, D→4 }

  Step 1: key=NULL   → returns some key (say B)  [order is hash-dependent]
  Step 2: key=B      → returns A
  Step 3: key=A      → returns D
  Step 4: key=D      → returns C
  Step 5: key=C      → returns -ENOENT (end of map)

  ⚠️  WARNING: If another thread/CPU modifies the map during iteration:
  - A deleted key that hasn't been visited yet → silently skipped
  - A newly inserted key → may or may not be visited
  - This is safe (no crash) but not strongly consistent
```

---

## 6. Map Flags

Flags are passed at map creation time and cannot be changed afterward.

```
  Flag                          Value   Meaning
  ─────────────────────────────────────────────────────────────────────
  BPF_F_NO_PREALLOC             (1<<0)  For hash maps: allocate elements
                                        lazily. Saves memory if map is
                                        sparse, but kmalloc at runtime
                                        (not safe in hard IRQ context)

  BPF_F_NO_COMMON_LRU           (1<<1)  For LRU hash maps: use per-CPU LRU
                                        lists instead of a shared global one.
                                        Better perf under contention, but
                                        less precise LRU eviction globally

  BPF_F_NUMA_NODE               (1<<2)  Allocate map on specific NUMA node
                                        (specified in attr.numa_node)
                                        Important for NUMA-aware networking

  BPF_F_RDONLY                  (1<<3)  Map is read-only from userspace
                                        (BPF programs can still write)

  BPF_F_WRONLY                  (1<<4)  Map is write-only from userspace
                                        (BPF programs can still read)

  BPF_F_STACK_BUILD_ID          (1<<5)  For stack trace maps: store
                                        build-id alongside ip address

  BPF_F_ZERO_SEED               (1<<6)  For hash maps: use zero as the
                                        hash seed (deterministic, but
                                        vulnerable to hash flooding attacks)

  BPF_F_RDONLY_PROG             (1<<7)  Map is read-only from BPF programs
                                        (can still be written from userspace)
                                        Combined with BPF_F_RDONLY: fully
                                        frozen/immutable map

  BPF_F_WRONLY_PROG             (1<<8)  Map is write-only from BPF programs
                                        (combined with BPF_F_WRONLY: fully
                                        write-only from both sides)

  BPF_F_CLONE                   (1<<9)  Allow cloning this map when a
                                        process calls unshare() or clone()
                                        with CLONE_FILES

  BPF_F_MMAPABLE                (1<<10) Allow mmap() of array maps
                                        (zero-copy access from userspace)
                                        Only for BPF_MAP_TYPE_ARRAY

  BPF_F_PRESERVE_ELEMS          (1<<11) For perf_event_array: preserve
                                        existing elements during map resize

  BPF_F_INNER_MAP               (1<<12) Mark map as inner map template
                                        (used for map-in-map creation)

  BPF_F_LINK                    (1<<13) Require BPF token-based access
                                        control (kernel 6.9+)
```

### Flag Decision Tree

```
  Creating a map. Which flags?
  
  Is this a hash map?
  ├─ YES: Will it be accessed in hard IRQ context (e.g., XDP)?
  │       ├─ YES: DO NOT use BPF_F_NO_PREALLOC
  │       │       (pre-allocation is interrupt-safe, lazy kmalloc is not)
  │       └─ NO:  Can the map be sparse (most keys unused most of the time)?
  │               ├─ YES: Use BPF_F_NO_PREALLOC (save memory)
  │               └─ NO:  Default (pre-alloc) is fine
  │
  ├─ Is this an array map that userspace reads frequently?
  │   └─ YES: Consider BPF_F_MMAPABLE for zero-copy mmap access
  │
  └─ Do you need to freeze the map after setup?
      └─ YES: Create normally, populate, then bpf(BPF_MAP_FREEZE)
              (after freeze, BPF programs cannot modify)
              Use BPF_F_RDONLY_PROG at creation if you know upfront
```

---

## 7. All Map Types

### 7.1 BPF_MAP_TYPE_HASH

The general-purpose hash table. Implemented using **htab** (hash table) with separate chaining.

**Conceptual Explanation**: A hash map uses a hash function to map keys to "buckets." Each bucket is a linked list of key-value pairs (for collision handling). Lookup: hash(key) → bucket index → walk the chain looking for matching key.

```
  key_size: any (hash computed over raw bytes)
  value_size: any
  max_entries: maximum number of distinct keys

  Memory layout:
  ┌──────────────────────────────────────────────────────────┐
  │  htab->buckets: array of htab_bucket[n_buckets]          │
  │                                                          │
  │  bucket[0] → [ elem: key="A", val=1 ] → [ elem: "E", 5 ]│
  │  bucket[1] → NULL                                        │
  │  bucket[2] → [ elem: key="B", val=2 ]                    │
  │  bucket[3] → [ elem: key="C", val=3 ] → [ elem: "D", 4 ]│
  │  ...                                                     │
  │                                                          │
  │  n_buckets = roundup_pow_of_two(max_entries)             │
  │  Each bucket has a spinlock for concurrent access        │
  └──────────────────────────────────────────────────────────┘

  Time complexity:
  - lookup: O(1) average, O(n) worst case (all in same bucket)
  - insert: O(1) average
  - delete: O(1) average
  - iterate: O(max_entries) via GET_NEXT_KEY

  Memory:
  - Without BPF_F_NO_PREALLOC: all max_entries pre-allocated
  - With BPF_F_NO_PREALLOC: allocated on-demand
```

**When to use**: General-purpose lookups by arbitrary key (IP address, PID, port number). The goto choice when you don't know the key space upfront.

### 7.2 BPF_MAP_TYPE_ARRAY

A fixed-size array indexed by integer. The **fastest map type** for sequential/index-based access.

**Conceptual Explanation**: Think of it as a C array in kernel memory. The index IS the key. Value at index `i` lives at `base + i * value_size`. No hashing, no chaining — pure pointer arithmetic.

```
  key_size: must be 4 (u32)
  value_size: any
  max_entries: N (indices 0 to N-1)
  Keys CANNOT be deleted (array slots exist forever, just zeroed)
  Array is ALWAYS zero-initialized on creation

  Memory layout (contiguous):
  ┌───────────────────────────────────────────────────────────┐
  │  index: 0          1          2          3          ...   │
  │         [value_0 ][value_1 ][value_2 ][value_3 ]...      │
  │          ▲                                                 │
  │          base_ptr                                          │
  │                                                            │
  │  lookup(key=2): return base_ptr + 2 * value_size           │
  │  → NO hash computation, NO pointer chasing                 │
  │  → Pure array indexing: O(1) with tiny constant           │
  └───────────────────────────────────────────────────────────┘

  Key property: array map lookup NEVER fails (key is bounded by max_entries)
  bpf_map_lookup_elem returns NULL only if key >= max_entries
```

**When to use**: Per-CPU counters (index = some small enum), configuration tables, indexed lookups where key space is dense and known.

### 7.3 BPF_MAP_TYPE_LRU_HASH

Like HASH but with **Least Recently Used** eviction. When the map is full and you try to insert a new element, the least-recently-used element is evicted automatically.

```
  Additional data structures per element:
  ┌──────────────────────────────────────────────────────────┐
  │  Each element has:                                       │
  │    - hash chain pointer (for bucket lookup)              │
  │    - LRU list pointer (doubly linked)                    │
  │    - reference bit (accessed recently?)                  │
  │                                                          │
  │  Global LRU list:                                        │
  │    MRU end ←→ elem_A ←→ elem_B ←→ elem_C ←→ LRU end    │
  │              (most recent)           (least recent)       │
  │                                                          │
  │  On access: element moved to MRU end                     │
  │  On eviction: element at LRU end is removed              │
  └──────────────────────────────────────────────────────────┘

  BPF_F_NO_COMMON_LRU flag:
    → Each CPU has its own LRU list
    → Avoids contention on the shared LRU lock
    → Eviction is per-CPU (may not be globally optimal)
```

**When to use**: Connection tracking, caching IP/flow state where you can't bound the number of flows and want automatic cleanup of stale entries.

### 7.4 BPF_MAP_TYPE_PERCPU_HASH and BPF_MAP_TYPE_PERCPU_ARRAY

**Conceptual Explanation**: Instead of one value per key, there is **one value per CPU per key**. This eliminates lock contention for updates — each CPU writes only its own slot.

```
  System with 4 CPUs:

  Regular ARRAY (value_size=8, max_entries=1):
  ┌────────────┐
  │  count: 42 │  ← shared, needs atomic or lock for updates
  └────────────┘

  PERCPU_ARRAY (value_size=8, max_entries=1):
  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │  CPU0: 10  │  │  CPU1: 11  │  │  CPU2: 9   │  │  CPU3: 12  │
  └────────────┘  └────────────┘  └────────────┘  └────────────┘
                                                   Total = 42

  eBPF program (runs on CPU 2):
    ptr = bpf_map_lookup_elem(&percpu_map, &key);
    (*ptr)++;   // safe: only CPU 2 touches this slot

  Userspace reading total:
    bpf(BPF_MAP_LOOKUP_ELEM, fd, key, values_array)
    // values_array receives ALL per-CPU values
    // userspace sums them: total = values[0]+values[1]+...+values[N]

  Memory:
    Kernel stores values in per-CPU memory regions
    value_size must be aligned to 8 bytes
    Total memory = max_entries * value_size * num_online_cpus
```

**When to use**: High-frequency counters, histograms, statistics — anywhere contention on a shared counter would be a bottleneck. The definitive answer to "how do I count packets fast?"

### 7.5 BPF_MAP_TYPE_PROG_ARRAY

A special array that holds **references to eBPF programs**. Used for **tail calls** — jumping from one eBPF program to another without returning.

**Conceptual Explanation of Tail Calls**: A tail call replaces the current program's execution context with a new program. It's like `exec()` for eBPF — the new program takes over the same kernel stack frame. This avoids the stack growth you'd get from nested function calls, and it's how you build eBPF program pipelines.

```
  key_size: 4 (u32 index)
  value_size: 4 (u32, holds a program fd internally)
  max_entries: up to 32 (BPF_MAX_TAIL_CALL_CNT per chain)

  prog_array[0] = &xdp_parse_ethernet
  prog_array[1] = &xdp_parse_ip
  prog_array[2] = &xdp_parse_tcp
  prog_array[3] = &xdp_drop_handler

  XDP program:
  ┌──────────────────────────────────────────┐
  │  xdp_parse_ethernet(ctx):               │
  │    // parse ethernet header              │
  │    bpf_tail_call(ctx, &prog_array, 1);  │  → jumps to xdp_parse_ip
  │    return XDP_PASS; // fallthrough       │    (this line only reached
  └──────────────────────────────────────────┘     if tail_call fails)

  Tail call chain:
  ethernet_parser → ip_parser → tcp_parser → drop_handler
        │                 │             │              │
        └── bpf_tail_call─┘             └──────────────┘
            (no return)

  Stack depth does NOT grow across tail calls
  Maximum chain length: BPF_MAX_TAIL_CALL_CNT = 33 (kernel 5.x+)
```

### 7.6 BPF_MAP_TYPE_HASH_OF_MAPS and BPF_MAP_TYPE_ARRAY_OF_MAPS

Maps whose **values are other maps**. See Section 10 for deep coverage.

### 7.7 BPF_MAP_TYPE_PERF_EVENT_ARRAY

Used to send **variable-length data from eBPF to userspace** via Linux perf events. Each element is a `perf_event` fd referring to a perf ring buffer.

```
  Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  eBPF prog                    perf_event_array[cpu_id]      │
  │                                                             │
  │  bpf_perf_event_output(ctx,   ──writes──►  perf ring buf    │
  │    &pea_map, BPF_F_CURRENT_CPU,              (per-CPU)      │
  │    &data, sizeof(data));                         │          │
  │                                                  │          │
  │                                                  ▼          │
  │  userspace (perf_event_open + mmap)          read events    │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

  Setup requires:
  1. Open perf_event_open for each CPU
  2. mmap each perf fd for ring buffer access
  3. Store each perf fd into the perf_event_array at index=cpu_id
  4. Call perf_event_enable() on each fd

  Data delivery:
  - bpf_perf_event_output() is non-blocking
  - Data is copied into per-CPU ring buffer
  - Userspace polls/reads via epoll or blocking read
  - Variable length: data can be any size up to PERF_SAMPLE_MAX_SIZE
```

**Limitation**: Complex setup, per-CPU ring buffers of fixed size (must be configured), can lose events if userspace is slow. **Mostly superseded by BPF_MAP_TYPE_RINGBUF.**

### 7.8 BPF_MAP_TYPE_CGROUP_ARRAY

Stores cgroup file descriptors. Used by programs that need to check if a socket/task belongs to a specific cgroup.

### 7.9 BPF_MAP_TYPE_LPM_TRIE

**LPM = Longest Prefix Match**. A trie data structure optimized for IP prefix matching (routing table lookups).

**Conceptual Explanation of LPM**: Given an IP address like `192.168.1.5`, find the most specific (longest) matching prefix. The routing table might have `0.0.0.0/0` (default), `192.168.0.0/16`, and `192.168.1.0/24`. LPM returns `192.168.1.0/24` because it's the longest match.

```
  Key structure (MUST use this layout):
  struct bpf_lpm_trie_key {
      __u32 prefixlen;  // significant bits (e.g., 24 for /24)
      __u8  data[4];    // key data (e.g., IPv4 address)
  };

  Trie structure (conceptual):
       root
       /  \
      0    1
     / \    \
    ...  ...  ...
  
  Each node represents a bit in the prefix.
  Lookup: walk bits of the query key from MSB to LSB,
          recording the last matching node with a value.
  
  Example (IPv4, /24 prefixes):
  Stored:
    0.0.0.0/0    → "default route"
    10.0.0.0/8   → "internal"
    10.1.0.0/16  → "datacenter"
    10.1.2.0/24  → "rack-42"
  
  Query: 10.1.2.55
  → matches 0.0.0.0/0        (length 0)
  → matches 10.0.0.0/8       (length 8)
  → matches 10.1.0.0/16      (length 16)
  → matches 10.1.2.0/24      (length 24) ← longest, returned
  
  Time complexity: O(prefixlen) = O(32) for IPv4, O(128) for IPv6
  Memory: O(number of distinct prefixes * sizeof(key+value))
```

**When to use**: Firewall rules by IP prefix, routing decisions, geolocation by IP range, rate-limiting by subnet.

### 7.10 BPF_MAP_TYPE_STACK_TRACE

Stores kernel/user **stack traces** (arrays of instruction pointers). Used by profiling tools.

```
  key_size: 4 (u32 stack_id)
  value_size: sizeof(struct bpf_stack_build_id) * PERF_MAX_STACK_DEPTH
           or sizeof(__u64) * PERF_MAX_STACK_DEPTH

  In eBPF:
    __u64 stack_id = bpf_get_stackid(ctx, &stack_map, flags);
    // stack_id can then be used as a key in another map
    // e.g., map: stack_id → count (for flame graphs)

  flags:
    BPF_F_SKIP_FIELD_MASK  → skip N frames from bottom
    BPF_F_USER_STACK       → capture user-space stack instead of kernel
    BPF_F_FAST_STACK_CMP   → hash-based deduplication
    BPF_F_REUSE_STACKID    → overwrite existing entry with same hash

  The map stores the stack as an array of instruction pointers (IPs)
  Userspace can then symbolize them: IP → function name + offset
```

### 7.11 BPF_MAP_TYPE_SOCKMAP and BPF_MAP_TYPE_SOCKHASH

Stores socket references. Used for **socket redirection** — intercepting and redirecting data between sockets at the kernel level.

```
  SOCKMAP: array-based (index → socket)
  SOCKHASH: hash-based (arbitrary key → socket)

  Use cases:
  1. Accelerated proxy (redirect data between sockets without userspace copy)
  2. Load balancing (incoming connection → backend socket)
  3. Session persistence

  Key helpers:
  bpf_sk_redirect_map()   → redirect sk_buff to a socket in the map
  bpf_msg_redirect_map()  → redirect MSG_SENDMSG to another socket
  bpf_sock_map_update()   → add socket to map (called from sock_ops prog)

  Flow:
  client ──TCP──► kernel receives data
                       │
                       └──► BPF prog checks sockhash
                            → finds backend socket fd
                            → bpf_sk_redirect_map() bypasses userspace
                            → data delivered directly to backend socket
```

### 7.12 BPF_MAP_TYPE_CPUMAP

A map from CPU index to a CPU redirect target. Used by XDP programs to **redirect packets to a specific CPU** for processing, implementing CPU-affinity-based load balancing.

### 7.13 BPF_MAP_TYPE_DEVMAP and BPF_MAP_TYPE_DEVMAP_HASH

Store network device (netdev) references. Used by XDP for **packet redirection between network devices**.

```
  XDP redirect pipeline:
  
  NIC receives packet
       │
       ▼
  XDP prog on NIC:
    bpf_redirect_map(&devmap, outgoing_ifindex, 0)
    return XDP_REDIRECT
       │
       ▼
  Packet transmitted on outgoing_ifindex (without going to Linux networking stack)
  
  This is how XDP-based routers and bridges work.
  Performance: can achieve near line-rate packet forwarding.
```

### 7.14 BPF_MAP_TYPE_QUEUE and BPF_MAP_TYPE_STACK

**FIFO queue** and **LIFO stack** respectively. Unlike other maps, these have NO keys — elements are pushed/popped by position.

```
  Operations (no key parameter):
  bpf_map_push_elem(map, value, flags)    → enqueue / push
  bpf_map_pop_elem(map, value)            → dequeue / pop (destructive)
  bpf_map_peek_elem(map, value)           → read front/top (non-destructive)

  QUEUE semantics:
  push: A B C  → [A, B, C]
  pop:         → returns A, map = [B, C]

  STACK semantics:
  push: A B C  → [A, B, C]
  pop:         → returns C, map = [A, B]

  flags for push:
    BPF_EXIST → if full, overwrite oldest element (queue) / overwrite top (stack)
                Without this flag, push fails when map is full

  Use cases:
  - Work queues between eBPF programs
  - Event buffers
  - Task dispatch (eBPF program pushes work items, another pops them)
```

### 7.15 BPF_MAP_TYPE_REUSEPORT_SOCKARRAY

Used with `SO_REUSEPORT` sockets. Allows eBPF programs to select which socket in a reuseport group receives an incoming connection.

### 7.16 BPF_MAP_TYPE_INODE_STORAGE, BPF_MAP_TYPE_SK_STORAGE, BPF_MAP_TYPE_TASK_STORAGE

**Local storage maps** — rather than mapping an external key to a value, these attach storage directly to a kernel object (inode, socket, or task). Added in Linux 5.2 (sk_storage), 5.10 (inode/task_storage).

```
  Traditional approach (hash map):
  ┌──────────────────────────────────────┐
  │  hash_map: { socket_ptr → data }     │
  │  Problem: must clean up when socket  │
  │  is destroyed (or memory leaks)       │
  └──────────────────────────────────────┘

  Local storage approach:
  ┌──────────────────────────────────────┐
  │  sk_storage_map (template only)      │
  │                                      │
  │  Per-socket storage:                 │
  │  socket_A.bpf_sk_storage[map] = data │
  │  socket_B.bpf_sk_storage[map] = data │
  │                                      │
  │  Storage is AUTOMATICALLY freed when │
  │  the socket/inode/task is destroyed  │
  │  No cleanup needed!                  │
  └──────────────────────────────────────┘

  eBPF helper:
  bpf_sk_storage_get(map, sk, init_val, flags)
  → Returns pointer to the per-socket value
  → Creates it (initialized to init_val) if not present and flags=BPF_LOCAL_STORAGE_GET_F_CREATE
```

**Why this is important**: Eliminates the resource leak problem of storing per-object data in external hash maps. The storage is "owned" by the kernel object and cleaned up automatically.

---

## 8. Per-CPU Maps

### The Cache Line Problem

On modern CPUs, when multiple CPUs write to the same memory location, they compete for the **cache line** that contains that location. This is called **cache thrashing** or **false sharing**:

```
  CPU 0                    CPU 1
  writes counter[0]        writes counter[0]
       │                        │
       ▼                        ▼
  cache line is             cache line is
  invalidated on CPU 1      invalidated on CPU 0
  
  Each write forces the other CPU to re-fetch from L3/RAM.
  At high packet rates, this becomes the bottleneck.
```

Per-CPU maps solve this by giving each CPU its own private slot:

```
  PERCPU layout in kernel memory:
  
  CPU 0's memory:  [  value_for_key_0  ][ value_for_key_1 ]...
  CPU 1's memory:  [  value_for_key_0  ][ value_for_key_1 ]...
  CPU 2's memory:  [  value_for_key_0  ][ value_for_key_1 ]...
  CPU 3's memory:  [  value_for_key_0  ][ value_for_key_1 ]...

  Each CPU accesses ONLY its own memory.
  No cache line contention.
  No atomic operations needed.
  Fastest possible update path.
```

### Aggregating Per-CPU Values

The tradeoff: to get a global total, userspace must sum all per-CPU values:

```c
// userspace aggregation pattern in C
__u64 values[MAX_CPUS];
__u32 key = MY_KEY;
bpf(BPF_MAP_LOOKUP_ELEM, {map_fd, &key, values, 0});

__u64 total = 0;
for (int i = 0; i < num_cpus; i++) {
    total += values[i];
}
// Note: this sum is NOT atomic — it's a point-in-time snapshot
// CPUs may update their values between reads
```

---

## 9. Ring Buffer Maps

### BPF_MAP_TYPE_RINGBUF — The Modern Event Channel

Introduced in Linux 5.8. Designed to be the **definitive solution** for sending events from eBPF to userspace. It supersedes `BPF_MAP_TYPE_PERF_EVENT_ARRAY` for most use cases.

**Conceptual Explanation**: A ring buffer (circular buffer) is a fixed-size buffer that wraps around. The producer (eBPF) writes to a "tail" pointer, the consumer (userspace) reads from a "head" pointer. When the tail catches up to the head, the buffer is full and you drop events.

```
  Ring buffer memory layout:
  
  ┌─────────────────────────────────────────────────────────────┐
  │                    ring buffer (size = 2^N bytes)           │
  │                                                             │
  │  consumer_pos ──►[consumed][consumed][ data1 ][ data2 ][ ] │
  │                                                   ▲         │
  │  producer_pos ────────────────────────────────────┘         │
  │                                                             │
  │  consumer_pos and producer_pos are SHARED via mmap          │
  │  → userspace can read them WITHOUT a syscall                 │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

  Each record in the ring buffer:
  ┌──────────────────────────────────────────┐
  │  len      (u32)  length of data          │
  │  pg_off   (u32)  flags: BPF_RINGBUF_DISCARD │
  │  data[0]  (u8[]) actual payload          │
  └──────────────────────────────────────────┘
```

### Two-Phase Write (Reserve + Submit)

Unlike perf event arrays, ringbuf supports a **two-phase write** that eliminates data copies:

```
  Method 1: One-shot (copy approach)
  bpf_ringbuf_output(rb_map, &data, sizeof(data), 0);
  → Copies data atomically into ring buffer
  → Simpler but requires data to be ready upfront

  Method 2: Reserve + Commit (zero-copy approach)
  void *ptr = bpf_ringbuf_reserve(rb_map, sizeof(struct event), 0);
  if (!ptr) {
      // ring buffer full, handle overflow
      return 0;
  }
  // ptr points DIRECTLY into ring buffer memory
  // Fill in place, no intermediate copy needed:
  struct event *e = ptr;
  e->pid = bpf_get_current_pid_tgid() >> 32;
  e->timestamp = bpf_ktime_get_ns();
  bpf_get_current_comm(e->comm, sizeof(e->comm));
  // Now commit: makes record visible to userspace
  bpf_ringbuf_submit(ptr, 0);
  // OR: discard if you decide not to send
  bpf_ringbuf_discard(ptr, 0);
```

### Ringbuf vs Perf Event Array

```
  Feature                    PERF_EVENT_ARRAY    RINGBUF
  ─────────────────────────────────────────────────────────
  Kernel version             4.4+                5.8+
  Setup complexity           High (per-CPU fds)  Low (single map)
  Memory overhead            Per-CPU buffers     Single shared buffer
  Ordering guarantee         Per-CPU ordered     Globally ordered
  BPF-to-BPF visibility      No                  Yes (reserve+check+discard)
  Variable-length records    Yes (limited)       Yes (full)
  Zero-copy writes           No                  Yes (reserve+submit)
  Userspace access method    read()/poll()        mmap + poll()
  Lost event counter         Yes                 Yes
  Recommended for new code   No                  Yes
```

### Userspace Consumption

```c
// libbpf-based userspace reader
struct ring_buffer *rb = ring_buffer__new(map_fd, handle_event, NULL, NULL);

// handle_event callback:
int handle_event(void *ctx, void *data, size_t data_sz) {
    struct event *e = data;
    printf("PID=%d comm=%s\n", e->pid, e->comm);
    return 0;
}

// Polling loop:
while (true) {
    ring_buffer__poll(rb, 100 /* timeout_ms */);
}
```

---

## 10. Map-in-Map

### What and Why

**Map-in-map** is exactly what it sounds like: a map whose values are **references to other maps**. This enables:
1. **Atomic map replacement** — swap an entire inner map atomically without affecting readers
2. **Dynamic data structures** — the outer map acts as an index into a collection of inner maps
3. **Multi-tenancy** — per-CPU or per-connection map isolation

```
  Types:
  BPF_MAP_TYPE_ARRAY_OF_MAPS    → outer is array, values are map fds
  BPF_MAP_TYPE_HASH_OF_MAPS     → outer is hash, values are map fds

  Conceptual view:
  
  outer_map:
  ┌───────────────────────────────────────────────────────┐
  │  key=0  → inner_map_A { "192.168.1.0/24" → "allow" } │
  │  key=1  → inner_map_B { "10.0.0.0/8"    → "deny"  } │
  │  key=2  → inner_map_C { (empty)                     } │
  └───────────────────────────────────────────────────────┘

  eBPF program:
    void *inner = bpf_map_lookup_elem(&outer_map, &idx);
    if (inner) {
        void *val = bpf_map_lookup_elem(inner, &ip_key);
    }
```

### Atomic Map Replacement Pattern

This is the most powerful use of map-in-map. It allows you to update a lookup table used by a running eBPF program **without any downtime or inconsistency**:

```
  Initial state:
  outer_map[0] → firewall_rules_v1

  eBPF program reads rules:
    inner = bpf_map_lookup_elem(&outer, &ZERO);
    rule = bpf_map_lookup_elem(inner, &dst_ip);

  Update procedure (userspace):
  1. Create new map: firewall_rules_v2
  2. Populate firewall_rules_v2 with new rules
  3. bpf(BPF_MAP_UPDATE_ELEM, outer_map, key=0, fd=firewall_rules_v2)
     → This update is ATOMIC
     → Any eBPF invocation sees EITHER v1 OR v2, never a mix

  After update:
  outer_map[0] → firewall_rules_v2
  firewall_rules_v1 is freed (refcnt drops to 0)
```

### Creation Requirements

Map-in-map requires specifying an **inner map template** at creation:

```c
// Step 1: Create inner map template
int inner_fd = bpf(BPF_MAP_CREATE, {
    .map_type = BPF_MAP_TYPE_HASH,
    .key_size = 4,
    .value_size = 4,
    .max_entries = 100,
    .map_flags = BPF_F_INNER_MAP,   // mark as template
});

// Step 2: Create outer map, referencing inner template
int outer_fd = bpf(BPF_MAP_CREATE, {
    .map_type = BPF_MAP_TYPE_ARRAY_OF_MAPS,
    .key_size = 4,
    .value_size = 4,    // ignored for map-in-map (always stores an fd internally)
    .max_entries = 8,
    .inner_map_fd = inner_fd,  // template defines inner map schema
});

// Step 3: Create actual inner map and store in outer
int actual_inner_fd = bpf(BPF_MAP_CREATE, /* same params as template */);
bpf(BPF_MAP_UPDATE_ELEM, outer_fd, &key, &actual_inner_fd, BPF_ANY);
```

---

## 11. BPF Filesystem (BPFFS)

### What Is BPFFS?

BPFFS is a **virtual filesystem** (`bpf` type) mounted at `/sys/fs/bpf/`. It provides a namespace for persisting eBPF objects (maps, programs, links) beyond the lifetime of the process that created them.

```
  Without pinning:
  Process creates map → Process exits → No more fd → refcnt=0 → map freed
  
  With pinning:
  Process creates map
  → bpf(BPF_OBJ_PIN, "/sys/fs/bpf/my_map")
  → Process exits
  → /sys/fs/bpf/my_map still holds a reference (refcnt=1)
  → map lives on!
  
  Another process:
  → fd = bpf(BPF_OBJ_GET, "/sys/fs/bpf/my_map")
  → Can now use the map
  
  To remove: rm /sys/fs/bpf/my_map
  → decrements refcnt
  → if no programs use the map → freed
```

### BPFFS Directory Structure (Typical)

```
  /sys/fs/bpf/
  ├── globals/                    ← pinned maps shared globally
  │   ├── events_ringbuf
  │   ├── config_array
  │   └── stats_percpu_hash
  ├── progs/                      ← pinned programs
  │   ├── xdp_filter
  │   └── tc_classifier
  └── links/                      ← pinned BPF links
      └── xdp_eth0

  Each entry is a special file (not a regular file)
  stat() shows type as S_IFREG but it's backed by bpf anon_inode
  You cannot read/write them with open()/read() — must use bpf() syscall
```

### Mounting BPFFS

```bash
# Check if mounted
mount | grep bpf

# Mount manually (usually done by systemd automatically)
mount -t bpf bpf /sys/fs/bpf

# Verify
ls /sys/fs/bpf/
```

---

## 12. Concurrency and Synchronization

### The Problem: Concurrent Access

eBPF programs can run simultaneously on multiple CPUs. Multiple programs can share the same map. Userspace can concurrently access maps via the `bpf()` syscall. Without synchronization, this leads to data races.

### Available Synchronization Primitives

#### 1. Per-CPU Maps (Recommended for Counters)
As covered in Section 8 — eliminate contention by giving each CPU private storage. No locks needed.

#### 2. Atomic Operations via `__sync_fetch_and_add`

For shared counters without per-CPU maps:

```c
// In eBPF program (kernel side)
__u64 *val = bpf_map_lookup_elem(&map, &key);
if (val) {
    __sync_fetch_and_add(val, 1);  // atomic increment
    // Uses LOCK XADD instruction on x86
    // Correctly handles concurrent updates from multiple CPUs
}
```

#### 3. BPF Spinlock (for Composite Updates)

When you need to update multiple fields atomically:

```c
// Value struct must contain bpf_spin_lock as FIRST field (or with BTF annotation)
struct my_value {
    struct bpf_spin_lock lock;    // MUST be first, or annotated with BTF
    __u64 packets;
    __u64 bytes;
    __u32 last_seen;
};

// In eBPF program:
struct my_value *v = bpf_map_lookup_elem(&map, &key);
if (v) {
    bpf_spin_lock(&v->lock);
    v->packets++;
    v->bytes += pkt_len;
    v->last_seen = bpf_ktime_get_ns();
    bpf_spin_unlock(&v->lock);
}

// Constraints on bpf_spin_lock:
// - Cannot be held across bpf_map_lookup_elem calls
// - Cannot be held across tail calls
// - Maximum held duration enforced by verifier
// - Only one lock can be held at a time (no nested locks)
```

#### 4. Timer-Based Updates (BPF Timers)

Linux 5.15+ supports `bpf_timer` inside maps:

```c
struct map_val {
    struct bpf_timer timer;
    __u64 counter;
};

// Schedule a callback after delay:
bpf_timer_init(&val->timer, &timer_map, CLOCK_BOOTTIME);
bpf_timer_set_callback(&val->timer, my_timer_cb);
bpf_timer_start(&val->timer, 1000000000ULL /* 1 second */, 0);
```

### Read-Side Safety: RCU

The kernel hash table (`htab`) implementation uses **RCU (Read-Copy-Update)** for lock-free reads:

```
  RCU conceptual model:
  
  Readers (eBPF programs):
  → Read current version of element with NO locks
  → Protected by RCU read-side critical section
  → rcu_read_lock() / rcu_read_unlock() (implicit in BPF execution)
  
  Writers (bpf() syscall updating/deleting):
  → Create a NEW version of the element
  → Atomically swap pointer (readers now see new version)
  → Wait for all ONGOING reads to finish (RCU grace period)
  → Free OLD version

  This means:
  - Reads are always lock-free and wait-free
  - Writes are serialized by a per-bucket spinlock
  - No reader can block a writer
  - No writer can corrupt a concurrent reader's view
```

---

## 13. Memory Layout and Performance

### Memory Accounting

Map memory is accounted against the process's `RLIMIT_MEMLOCK` limit (or the newer `memory.high` cgroup limit). By default, unprivileged processes have a very low limit (~64KB). Root processes or those with `CAP_BPF` (Linux 5.8+) have much higher limits.

```
  Checking limits:
  ulimit -l          → current RLIMIT_MEMLOCK (kilobytes)
  cat /proc/self/limits | grep locked
  
  For production eBPF:
  ulimit -l unlimited   # in your deployment script
  # OR
  /etc/security/limits.conf:
  *    soft    memlock    unlimited
  *    hard    memlock    unlimited

  Memory calculation formulas:
  
  BPF_MAP_TYPE_ARRAY:
    size = max_entries * value_size_aligned_to_8
  
  BPF_MAP_TYPE_HASH (pre-allocated):
    size ≈ n_buckets * sizeof(bucket) + max_entries * (key_size + value_size + metadata)
    metadata per element ≈ 64 bytes (hash chain, LRU list, etc.)
  
  BPF_MAP_TYPE_PERCPU_ARRAY:
    size = max_entries * roundup_to_8(value_size) * num_online_cpus
```

### Performance Characteristics

```
  Map type              Lookup    Update    Notes
  ──────────────────────────────────────────────────────────────
  ARRAY                 ~3ns      ~3ns      Index arithmetic only
  PERCPU_ARRAY          ~3ns      ~3ns      Same, no sharing overhead
  HASH (pre-alloc)      ~20ns     ~30ns     Hash + chain walk + lock
  PERCPU_HASH           ~20ns     ~20ns     No lock contention
  LRU_HASH              ~25ns     ~35ns     Extra LRU list update
  LPM_TRIE              O(bits)   O(bits)   ~40-100ns for IPv4
  RINGBUF (reserve)     ~10ns     N/A       Lock-free reservation
  ──────────────────────────────────────────────────────────────
  Numbers are approximate, vary by CPU, key size, value size,
  cache state, and contention level.

  Cache effects:
  - Array maps: sequential access patterns are cache-friendly
  - Hash maps: random bucket access causes cache misses
  - PerCPU maps: no false sharing, excellent cache behavior
  - Avoid large value sizes: each lookup/update does copy_to/from_user
```

### mmap Access for Arrays (BPF_F_MMAPABLE)

With `BPF_F_MMAPABLE`, the array backing store can be directly mapped into userspace:

```
  Without mmap (normal path):
  userspace                    kernel
    bpf(BPF_MAP_LOOKUP_ELEM)
    │                        → copy_to_user (copies value to userspace buffer)
    ← returns value copy

  With mmap (BPF_F_MMAPABLE):
  userspace                    kernel
    ptr = mmap(NULL, map_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0)
    ptr[index] = new_value   → DIRECT write to kernel memory (no syscall!)
    value = ptr[index]       → DIRECT read from kernel memory (no syscall!)

  ⚠️  WARNING: mmap access bypasses all BPF synchronization!
  You are directly accessing kernel memory.
  Use with BPF_F_RDONLY_PROG if eBPF programs should not modify.
  Use atomic ops if concurrent modifications are possible.
```

---

## 14. BTF and Map Type Information

### What Is BTF?

**BTF (BPF Type Format)** is a compact binary format that stores C type information — struct layouts, typedef chains, enum values — alongside eBPF programs and maps. It enables:

1. **Pretty-printing** of map contents by tools like `bpftool`
2. **CO-RE (Compile Once, Run Everywhere)** — accessing kernel structs portably
3. **Map verification** — verifier checks bpf_spin_lock position
4. **Userspace type awareness** — libbpf knows your struct layout

```
  Without BTF:
  bpftool map dump id 42
  → key: 01 00 00 00  value: 2a 00 00 00 00 00 00 00
  (raw bytes, meaningless to humans)

  With BTF:
  bpftool map dump id 42
  → key: {"pid": 1}  value: {"count": 42, "comm": "systemd"}
  (typed, readable)
```

### Attaching BTF to Maps

```c
// In your BPF program source (with clang -g):
struct event {
    __u32 pid;
    __u64 count;
    char  comm[16];
};

// Declare with BTF (libbpf macro):
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);         // BTF: key is u32
    __type(value, struct event); // BTF: value is struct event
} events_map SEC(".maps");

// libbpf automatically:
// 1. Generates BTF from debug info
// 2. Loads BTF into kernel alongside map
// 3. Sets btf_key_type_id and btf_value_type_id in map creation
```

---

## 15. C Implementation

### 15.1 Complete eBPF Kernel Program (kprobe counting open() calls per PID)

```c
// File: open_count.bpf.c
// Compile: clang -O2 -g -target bpf -c open_count.bpf.c -o open_count.bpf.o
// Or use: clang -O2 -g -target bpf open_count.bpf.c -o open_count.bpf.o

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/ptrace.h>

// ─────────────────────────────────────────────────────────────
// Map 1: Hash map — PID → open() call count
// ─────────────────────────────────────────────────────────────
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, __u32);      // pid
    __type(value, __u64);    // count
} pid_open_count SEC(".maps");

// ─────────────────────────────────────────────────────────────
// Map 2: Ring buffer — send events to userspace
// ─────────────────────────────────────────────────────────────
struct event {
    __u32 pid;
    __u32 uid;
    __u64 count;
    char  comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256 KB ring buffer
} events SEC(".maps");

// ─────────────────────────────────────────────────────────────
// Map 3: Per-CPU array — per-CPU statistics
// ─────────────────────────────────────────────────────────────
struct cpu_stats {
    __u64 processed;
    __u64 errors;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct cpu_stats);
} cpu_stats_map SEC(".maps");

// ─────────────────────────────────────────────────────────────
// Map 4: Array — global configuration (read-only from BPF)
// ─────────────────────────────────────────────────────────────
struct config {
    __u32 sample_rate;   // emit event every N calls
    __u32 max_pid;       // only track PIDs below this
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct config);
} config_map SEC(".maps");

// ─────────────────────────────────────────────────────────────
// kprobe on sys_openat — fires every time openat() is called
// ─────────────────────────────────────────────────────────────
SEC("kprobe/__x64_sys_openat")
int BPF_KPROBE(trace_openat)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;  // upper 32 bits = PID
    __u32 zero = 0;

    // Read configuration
    struct config *cfg = bpf_map_lookup_elem(&config_map, &zero);
    if (!cfg)
        return 0;

    // Filter by PID range
    if (pid > cfg->max_pid && cfg->max_pid > 0)
        return 0;

    // ── Update per-CPU stats ──────────────────────────────────
    struct cpu_stats *stats = bpf_map_lookup_elem(&cpu_stats_map, &zero);
    if (stats) {
        // Safe: per-CPU, no lock needed
        stats->processed++;
    }

    // ── Increment PID counter in hash map ────────────────────
    __u64 *count = bpf_map_lookup_elem(&pid_open_count, &pid);
    if (count) {
        // Use atomic to handle potential concurrent updates
        // (rare with same PID, but possible on SMP for multithreaded processes)
        __sync_fetch_and_add(count, 1);
        
        // Sample: only emit event every N-th call
        if (*count % cfg->sample_rate != 0)
            return 0;
            
    } else {
        // First time seeing this PID — insert with count=1
        __u64 init_val = 1;
        long ret = bpf_map_update_elem(&pid_open_count, &pid, &init_val, BPF_NOEXIST);
        if (ret != 0) {
            // Race: another CPU inserted between our lookup and update
            // Just retry lookup and increment atomically
            count = bpf_map_lookup_elem(&pid_open_count, &pid);
            if (count)
                __sync_fetch_and_add(count, 1);
            return 0;
        }
        count = bpf_map_lookup_elem(&pid_open_count, &pid);
    }

    // ── Emit event to ring buffer ─────────────────────────────
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) {
        // Ring buffer full — track dropped events
        if (stats)
            stats->errors++;
        return 0;
    }

    e->pid   = pid;
    e->uid   = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    e->count = count ? *count : 1;
    bpf_get_current_comm(e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### 15.2 Complete Userspace Loader (C with libbpf)

```c
// File: open_count.c
// Compile: gcc -O2 open_count.c -o open_count -lbpf -lelf -lz

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <sys/resource.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "open_count.skel.h"  // generated by bpftool gen skeleton

// Must match eBPF struct definition
struct event {
    __u32 pid;
    __u32 uid;
    __u64 count;
    char  comm[16];
};

struct cpu_stats {
    __u64 processed;
    __u64 errors;
};

struct config {
    __u32 sample_rate;
    __u32 max_pid;
};

static volatile bool running = true;

static void sig_handler(int sig) {
    running = false;
}

// ─────────────────────────────────────────────────────────────
// Ring buffer callback — called for each event from eBPF
// ─────────────────────────────────────────────────────────────
static int handle_event(void *ctx, void *data, size_t data_sz)
{
    const struct event *e = data;
    printf("[PID %6u] [UID %4u] [COUNT %8llu] %s\n",
           e->pid, e->uid, e->count, e->comm);
    return 0;
}

// ─────────────────────────────────────────────────────────────
// Bump RLIMIT_MEMLOCK to allow loading eBPF programs and maps
// ─────────────────────────────────────────────────────────────
static void bump_memlock_rlimit(void)
{
    struct rlimit rlim = {
        .rlim_cur = RLIM_INFINITY,
        .rlim_max = RLIM_INFINITY,
    };
    if (setrlimit(RLIMIT_MEMLOCK, &rlim)) {
        fprintf(stderr, "WARNING: failed to increase RLIMIT_MEMLOCK: %s\n",
                strerror(errno));
    }
}

// ─────────────────────────────────────────────────────────────
// Set configuration in the config array map
// ─────────────────────────────────────────────────────────────
static int configure_map(int config_fd, __u32 sample_rate, __u32 max_pid)
{
    struct config cfg = {
        .sample_rate = sample_rate,
        .max_pid     = max_pid,
    };
    __u32 key = 0;
    return bpf_map_update_elem(config_fd, &key, &cfg, BPF_ANY);
}

// ─────────────────────────────────────────────────────────────
// Dump per-CPU statistics
// ─────────────────────────────────────────────────────────────
static void dump_cpu_stats(int stats_fd, int num_cpus)
{
    __u32 key = 0;
    struct cpu_stats *values = calloc(num_cpus, sizeof(struct cpu_stats));
    if (!values) return;

    if (bpf_map_lookup_elem(stats_fd, &key, values) == 0) {
        __u64 total_processed = 0, total_errors = 0;
        for (int i = 0; i < num_cpus; i++) {
            total_processed += values[i].processed;
            total_errors    += values[i].errors;
        }
        printf("\n--- CPU Stats ---\n");
        printf("Processed: %llu  Errors (ring full): %llu\n",
               total_processed, total_errors);
    }
    free(values);
}

// ─────────────────────────────────────────────────────────────
// Iterate over hash map and print all PID counts
// ─────────────────────────────────────────────────────────────
static void dump_pid_counts(int map_fd)
{
    __u32 key = 0, next_key = 0;
    __u64 value;
    int count = 0;

    printf("\n--- PID open() counts ---\n");
    
    // GET_NEXT_KEY with key=NULL (passed as 0 pointer) returns first key
    // Loop until GET_NEXT_KEY returns -ENOENT
    __u32 *prev_key = NULL;
    while (bpf_map_get_next_key(map_fd, prev_key, &next_key) == 0) {
        if (bpf_map_lookup_elem(map_fd, &next_key, &value) == 0) {
            printf("  PID %6u: %llu calls\n", next_key, value);
            count++;
        }
        key = next_key;
        prev_key = &key;
        if (count > 50) {   // limit output
            printf("  ... (truncated)\n");
            break;
        }
    }
}

int main(int argc, char **argv)
{
    struct open_count_bpf *skel;
    struct ring_buffer *rb = NULL;
    int err;
    int num_cpus = libbpf_num_possible_cpus();

    bump_memlock_rlimit();
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    // ── Load and verify BPF programs ──────────────────────────
    skel = open_count_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }

    err = open_count_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load BPF skeleton: %d\n", err);
        goto cleanup;
    }

    // ── Configure the config map before attaching ─────────────
    err = configure_map(bpf_map__fd(skel->maps.config_map),
                        10 /* sample every 10th call */,
                        0  /* no PID limit */);
    if (err) {
        fprintf(stderr, "Failed to configure map: %d\n", err);
        goto cleanup;
    }

    // ── Attach kprobe ─────────────────────────────────────────
    err = open_count_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF programs: %d\n", err);
        goto cleanup;
    }

    // ── Set up ring buffer consumer ───────────────────────────
    rb = ring_buffer__new(bpf_map__fd(skel->maps.events),
                          handle_event, NULL, NULL);
    if (!rb) {
        err = -errno;
        fprintf(stderr, "Failed to create ring buffer: %d\n", err);
        goto cleanup;
    }

    // ── Optional: Pin maps to BPFFS ───────────────────────────
    err = bpf_obj_pin(bpf_map__fd(skel->maps.pid_open_count),
                      "/sys/fs/bpf/open_count_pid_map");
    if (err)
        fprintf(stderr, "Warning: failed to pin map (continuing): %s\n",
                strerror(-err));

    printf("Tracing openat() calls. Ctrl+C to stop.\n");
    printf("%-8s %-6s %-10s %s\n", "[TIME]", "PID", "COUNT", "COMM");

    // ── Event loop ────────────────────────────────────────────
    while (running) {
        err = ring_buffer__poll(rb, 100 /* timeout ms */);
        if (err == -EINTR) {
            err = 0;
            break;
        }
        if (err < 0) {
            fprintf(stderr, "Error polling ring buffer: %d\n", err);
            break;
        }
    }

    // ── Final statistics dump ──────────────────────────────────
    dump_cpu_stats(bpf_map__fd(skel->maps.cpu_stats_map), num_cpus);
    dump_pid_counts(bpf_map__fd(skel->maps.pid_open_count));

cleanup:
    ring_buffer__free(rb);
    // Unpin if we pinned
    unlink("/sys/fs/bpf/open_count_pid_map");
    open_count_bpf__destroy(skel);
    return -err;
}
```

### 15.3 XDP Program with LPM Trie (IP Firewall)

```c
// File: xdp_filter.bpf.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// LPM trie key: prefixlen + IPv4 address
struct ipv4_lpm_key {
    __u32 prefixlen;
    __u32 addr;          // big-endian (network byte order)
};

struct firewall_action {
    __u8  action;        // 0=PASS, 1=DROP
    __u64 hit_count;     // approx counter (racy, but acceptable for stats)
};

struct {
    __uint(type, BPF_MAP_TYPE_LPM_TRIE);
    __uint(max_entries, 65536);
    __uint(map_flags, BPF_F_NO_PREALLOC); // trie uses lazy alloc
    __type(key, struct ipv4_lpm_key);
    __type(value, struct firewall_action);
} blocklist SEC(".maps");

// Per-CPU stats
struct xdp_stats {
    __u64 passed;
    __u64 dropped;
    __u64 errors;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct xdp_stats);
} xdp_stats_map SEC(".maps");

SEC("xdp")
int xdp_ip_filter(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    __u32 key = 0;

    struct xdp_stats *stats = bpf_map_lookup_elem(&xdp_stats_map, &key);

    // Parse Ethernet header
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) {
        if (stats) stats->errors++;
        return XDP_ABORTED;
    }

    // Only process IPv4
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP) {
        if (stats) stats->passed++;
        return XDP_PASS;
    }

    // Parse IP header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) {
        if (stats) stats->errors++;
        return XDP_ABORTED;
    }

    // LPM lookup: find longest matching prefix for source IP
    struct ipv4_lpm_key lpm_key = {
        .prefixlen = 32,       // match exact address first,
                               // trie finds longest matching prefix
        .addr = ip->saddr,     // source IP in network byte order
    };

    struct firewall_action *action = bpf_map_lookup_elem(&blocklist, &lpm_key);
    if (action && action->action == 1) {
        // Matched a block rule — increment counter and drop
        __sync_fetch_and_add(&action->hit_count, 1);
        if (stats) stats->dropped++;
        return XDP_DROP;
    }

    if (stats) stats->passed++;
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### 15.4 Map-in-Map: Atomic Rule Replacement

```c
// File: atomic_rules.bpf.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

// Inner map type (template — used to define schema)
// The outer map will contain references to maps with this structure
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __uint(map_flags, BPF_F_INNER_MAP);
    __type(key, __u32);   // destination port
    __type(value, __u8);  // 0=allow, 1=block
} inner_map_template SEC(".maps");

// Outer map: array-of-maps
// Index 0 = current active ruleset
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY_OF_MAPS);
    __uint(max_entries, 1);
    __type(key, __u32);
    __array(values, struct {   // libbpf macro: specifies inner map type
        __uint(type, BPF_MAP_TYPE_HASH);
        __uint(max_entries, 1024);
        __type(key, __u32);
        __type(value, __u8);
    });
} ruleset_map SEC(".maps");

SEC("xdp")
int check_port_rules(struct xdp_md *ctx)
{
    __u32 outer_key = 0;

    // Look up the current inner map (the active ruleset)
    void *inner = bpf_map_lookup_elem(&ruleset_map, &outer_key);
    if (!inner)
        return XDP_PASS;  // no ruleset loaded, pass everything

    // TODO: parse packet to get destination port
    __u32 dst_port = 80; // simplified: would come from packet parsing

    __u8 *action = bpf_map_lookup_elem(inner, &dst_port);
    if (action && *action == 1)
        return XDP_DROP;

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

---

## 16. Rust Implementation

### 16.1 Aya Framework Overview

**Aya** is the Rust eBPF framework. It has two parts:
- `aya` crate (userspace): loads programs, manages maps, reads events
- `aya-bpf` crate (kernel/BPF side): write eBPF programs in Rust

```
  Workspace layout:
  my-ebpf-project/
  ├── Cargo.toml              ← workspace
  ├── my-ebpf/                ← eBPF programs (target: bpf)
  │   ├── Cargo.toml
  │   └── src/
  │       └── main.rs         ← eBPF program code
  └── my-userspace/           ← userspace loader (target: x86_64)
      ├── Cargo.toml
      └── src/
          └── main.rs         ← userspace code
```

### 16.2 eBPF Side (Kernel Rust)

```rust
// File: my-ebpf/src/main.rs
// This compiles to BPF bytecode (target: bpfeb-unknown-none / bpfel-unknown-none)

#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::{HashMap, PerCpuArray, RingBuf, LpmTrie},
    programs::XdpContext,
    BpfContext,
};
use aya_log_ebpf::info;

// ──────────────────────────────────────────────────────────────────
// Shared type definitions (must match userspace definitions)
// ──────────────────────────────────────────────────────────────────
#[repr(C)]
#[derive(Clone, Copy)]
pub struct Event {
    pub pid:   u32,
    pub uid:   u32,
    pub count: u64,
    pub comm:  [u8; 16],
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct CpuStats {
    pub processed: u64,
    pub errors:    u64,
}

// ──────────────────────────────────────────────────────────────────
// Map declarations (aya-bpf macro generates the correct ELF section)
// ──────────────────────────────────────────────────────────────────

/// Hash map: src_ip (u32) → packet count (u64)
#[map(name = "IP_COUNT")]
static mut IP_COUNT: HashMap<u32, u64> = HashMap::with_max_entries(65536, 0);

/// Per-CPU array for stats (index 0 = current CPU's stats)
#[map(name = "CPU_STATS")]
static mut CPU_STATS: PerCpuArray<CpuStats> = PerCpuArray::with_max_entries(1, 0);

/// Ring buffer for events to userspace
#[map(name = "EVENTS")]
static mut EVENTS: RingBuf = RingBuf::with_byte_size(256 * 1024, 0);

// ──────────────────────────────────────────────────────────────────
// XDP program entry point
// ──────────────────────────────────────────────────────────────────
#[xdp]
pub fn xdp_count(ctx: XdpContext) -> u32 {
    match try_xdp_count(ctx) {
        Ok(ret)  => ret,
        Err(_)   => xdp_action::XDP_ABORTED,
    }
}

fn try_xdp_count(ctx: XdpContext) -> Result<u32, ()> {
    // Parse ethernet header
    let ethhdr: *const EthHdr = ptr_at(&ctx, 0)?;
    // SAFETY: we checked bounds via ptr_at
    match unsafe { (*ethhdr).ether_type } {
        EtherType::Ipv4 => {}
        _ => return Ok(xdp_action::XDP_PASS),
    }

    // Parse IP header
    let ipv4hdr: *const Ipv4Hdr = ptr_at(&ctx, EthHdr::LEN)?;
    let src_addr = u32::from_be(unsafe { (*ipv4hdr).src_addr });

    // ── Update per-CPU stats (no lock needed) ──────────────────
    if let Some(stats) = unsafe { CPU_STATS.get_ptr_mut(0) } {
        // SAFETY: per-CPU, only this CPU accesses this slot
        unsafe { (*stats).processed += 1; }
    }

    // ── Update hash map counter ────────────────────────────────
    // Pattern: lookup → increment OR insert 1
    unsafe {
        match IP_COUNT.get_ptr_mut(&src_addr) {
            Some(count_ptr) => {
                // Atomic increment for SMP safety
                // In Aya, for non-percpu maps, use core::sync::atomic ops
                let count = count_ptr as *mut u64;
                // Use intrinsic for atomic add
                core::sync::atomic::AtomicU64::from_ptr(count)
                    .fetch_add(1, core::sync::atomic::Ordering::Relaxed);
            }
            None => {
                // First packet from this IP
                let _ = IP_COUNT.insert(&src_addr, &1u64, 0);
            }
        }
    }

    // ── Emit event to ring buffer (every 1000th packet per IP) ─
    let count = unsafe { IP_COUNT.get(&src_addr).copied().unwrap_or(0) };
    if count % 1000 == 0 {
        if let Some(mut entry) = unsafe { EVENTS.reserve::<Event>(0) } {
            unsafe {
                (*entry.as_mut_ptr()).pid   = 0; // XDP has no PID context
                (*entry.as_mut_ptr()).count = count;
            }
            entry.submit(0);
        }
    }

    Ok(xdp_action::XDP_PASS)
}

// Helper: safely get pointer at offset within XDP packet
#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = core::mem::size_of::<T>();

    if start + offset + len > end {
        return Err(());
    }

    Ok((start + offset) as *const T)
}

// Ethernet header constants (simplified)
#[repr(C)]
struct EthHdr {
    dst: [u8; 6],
    src: [u8; 6],
    ether_type: EtherType,
}
impl EthHdr { const LEN: usize = 14; }

#[repr(u16)]
enum EtherType {
    Ipv4 = 0x0800_u16.to_be(),
}

#[repr(C)]
struct Ipv4Hdr {
    _version_ihl:   u8,
    _tos:           u8,
    _tot_len:       u16,
    _id:            u16,
    _frag_off:      u16,
    _ttl:           u8,
    _protocol:      u8,
    _check:         u16,
    src_addr:       u32,
    dst_addr:       u32,
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    // eBPF programs cannot panic — verifier rejects unreachable code
    loop {}
}
```

### 16.3 Userspace Side (Rust with Aya)

```rust
// File: my-userspace/src/main.rs

use aya::{
    include_bytes_aligned,
    maps::{HashMap, PerCpuArray, RingBuf},
    programs::{Xdp, XdpFlags},
    util::online_cpus,
    Bpf,
};
use aya_log::BpfLogger;
use anyhow::{Context, Result};
use log::{info, warn};
use std::{
    net::Ipv4Addr,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::Duration,
};
use tokio::signal;

// Must match eBPF struct definition EXACTLY (same repr, same layout)
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Event {
    pub pid:   u32,
    pub uid:   u32,
    pub count: u64,
    pub comm:  [u8; 16],
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct CpuStats {
    pub processed: u64,
    pub errors:    u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    // ── Load BPF object ──────────────────────────────────────────
    // include_bytes_aligned! embeds the compiled .o file at compile time
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/my-ebpf"
    ))?;

    // ── Enable BPF logs (aya_log_ebpf::info! → userspace) ───────
    if let Err(e) = BpfLogger::init(&mut bpf) {
        warn!("Failed to initialize BPF logger: {}", e);
    }

    // ── Attach XDP program ───────────────────────────────────────
    let program: &mut Xdp = bpf.program_mut("xdp_count").unwrap().try_into()?;
    program.load()?;
    program.attach("eth0", XdpFlags::default())
        .context("Failed to attach XDP program to eth0")?;

    // ── Access maps ──────────────────────────────────────────────
    let ip_count_map: HashMap<_, u32, u64> =
        HashMap::try_from(bpf.map("IP_COUNT").context("IP_COUNT map not found")?)?;

    let cpu_stats_map: PerCpuArray<_, CpuStats> =
        PerCpuArray::try_from(bpf.map("CPU_STATS").context("CPU_STATS map not found")?)?;

    let mut ring_buf = RingBuf::try_from(bpf.map_mut("EVENTS").context("EVENTS map not found")?)?;

    let num_cpus = online_cpus()?.len();
    info!("XDP filter attached on eth0, monitoring with {} CPUs", num_cpus);

    // ── Spawn statistics printer ─────────────────────────────────
    let should_stop = Arc::new(AtomicBool::new(false));
    let stop_clone  = should_stop.clone();

    tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(5)).await;
            if stop_clone.load(Ordering::Relaxed) { break; }

            // Read per-CPU stats and aggregate
            match cpu_stats_map.get(&0, 0) {
                Ok(per_cpu_vals) => {
                    let total_processed: u64 = per_cpu_vals.iter().map(|s| s.processed).sum();
                    let total_errors:    u64 = per_cpu_vals.iter().map(|s| s.errors).sum();
                    info!(
                        "Stats: processed={} ring_full_drops={}",
                        total_processed, total_errors
                    );
                }
                Err(e) => warn!("Failed to read CPU stats: {}", e),
            }
        }
    });

    // ── Event loop: read ring buffer + wait for Ctrl+C ───────────
    let mut poll_fd = tokio::io::unix::AsyncFd::new(ring_buf.as_raw_fd())?;

    loop {
        tokio::select! {
            // Ring buffer readable
            _ = poll_fd.readable() => {
                // Drain all pending events
                while let Some(item) = ring_buf.next() {
                    // SAFETY: we know the BPF program writes Event structs
                    if item.len() == std::mem::size_of::<Event>() {
                        let event: Event = unsafe {
                            std::ptr::read_unaligned(item.as_ptr() as *const Event)
                        };
                        info!(
                            "Event: pid={} count={}",
                            event.pid, event.count
                        );
                    }
                }
            }

            // Ctrl+C
            _ = signal::ctrl_c() => {
                info!("Received SIGINT, stopping...");
                should_stop.store(true, Ordering::Relaxed);
                break;
            }
        }
    }

    // ── Final top-N IPs dump ─────────────────────────────────────
    info!("\nTop IP addresses by packet count:");
    let mut entries: Vec<(u32, u64)> = ip_count_map
        .iter()
        .filter_map(|r| r.ok())
        .collect();

    entries.sort_by(|a, b| b.1.cmp(&a.1));  // sort descending by count

    for (ip_u32, count) in entries.iter().take(10) {
        let ip = Ipv4Addr::from(*ip_u32);
        info!("  {:>15} : {} packets", ip, count);
    }

    Ok(())
}
```

### 16.4 Cargo.toml Files

```toml
# Workspace Cargo.toml
[workspace]
members = ["my-ebpf", "my-userspace"]
resolver = "2"

# my-ebpf/Cargo.toml
[package]
name    = "my-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-bpf     = { version = "0.1" }
aya-log-ebpf = { version = "0.1" }

[profile.release]
lto     = true
opt-level = "s"   # optimize for size in eBPF
codegen-units = 1

# my-userspace/Cargo.toml
[package]
name    = "my-userspace"
version = "0.1.0"
edition = "2021"

[dependencies]
aya     = { version = "0.13", features = ["async_tokio"] }
aya-log = { version = "0.2" }
anyhow  = "1"
log     = "0.4"
env_logger = "0.11"
tokio   = { version = "1", features = ["full"] }

[build-dependencies]
# aya-build can auto-compile the eBPF programs
aya-build = "0.1"
```

### 16.5 LPM Trie in Rust (Userspace Map Manipulation)

```rust
use aya::{
    maps::lpm_trie::{LpmTrie, Key},
    Bpf,
};
use std::net::Ipv4Addr;

// Key type for the LPM trie (must match eBPF program)
#[repr(C, packed)]
struct IpKey {
    prefixlen: u32,
    addr:      u32,   // big-endian
}

async fn setup_firewall_rules(bpf: &mut Bpf) -> anyhow::Result<()> {
    let mut trie: LpmTrie<_, IpKey, u8> =
        LpmTrie::try_from(bpf.map_mut("blocklist")?)?;

    // Block entire 192.168.0.0/16 subnet
    let block_subnet = IpKey {
        prefixlen: 16,
        addr: u32::from(Ipv4Addr::new(192, 168, 0, 0)).to_be(),
    };
    trie.insert(&Key::new(16, block_subnet), &1u8, 0)?;

    // Allow specific host 192.168.1.100/32 (overrides the /16 block)
    // NOTE: LPM finds LONGEST match, so /32 beats /16
    let allow_host = IpKey {
        prefixlen: 32,
        addr: u32::from(Ipv4Addr::new(192, 168, 1, 100)).to_be(),
    };
    trie.insert(&Key::new(32, allow_host), &0u8, 0)?;

    // Default allow (0.0.0.0/0)
    let default_allow = IpKey {
        prefixlen: 0,
        addr: 0,
    };
    trie.insert(&Key::new(0, default_allow), &0u8, 0)?;

    Ok(())
}
```

---

## 17. Advanced Patterns

### 17.1 Sliding Window Rate Limiter

A common pattern: rate-limit operations using a hash map to track per-key timestamps and counts:

```c
// BPF program (C)
struct rate_entry {
    struct bpf_spin_lock lock;
    __u64 window_start_ns;
    __u32 count;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);                // client IP
    __type(value, struct rate_entry);
} rate_limit_map SEC(".maps");

#define WINDOW_NS   (1000000000ULL)  // 1 second
#define MAX_RATE    100              // 100 requests per second

static inline int check_rate_limit(__u32 client_ip)
{
    __u64 now = bpf_ktime_get_ns();
    
    struct rate_entry *entry = bpf_map_lookup_elem(&rate_limit_map, &client_ip);
    if (!entry) {
        struct rate_entry new_entry = {
            .window_start_ns = now,
            .count = 1,
        };
        bpf_map_update_elem(&rate_limit_map, &client_ip, &new_entry, BPF_NOEXIST);
        return 0; // allow (first request)
    }

    bpf_spin_lock(&entry->lock);
    
    // Check if we're in a new window
    if (now - entry->window_start_ns > WINDOW_NS) {
        entry->window_start_ns = now;
        entry->count = 1;
        bpf_spin_unlock(&entry->lock);
        return 0; // allow (new window)
    }

    entry->count++;
    int over_limit = (entry->count > MAX_RATE);
    
    bpf_spin_unlock(&entry->lock);
    return over_limit; // 0=allow, 1=drop
}
```

### 17.2 Tail-Call Dispatch Table

Building a protocol parser pipeline with tail calls:

```c
// prog_array with dispatch table
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, 8);
    __type(key, __u32);
    __type(value, __u32);
} dispatch SEC(".maps");

// Protocol indices
#define PROTO_TCP   6
#define PROTO_UDP   17
#define PROTO_ICMP  1

SEC("xdp/entry")
int xdp_entry(struct xdp_md *ctx)
{
    // ... parse up to IP layer ...
    __u8 proto = ip->protocol;
    
    // Tail-call to protocol-specific handler
    // If no handler registered, falls through to XDP_PASS
    bpf_tail_call(ctx, &dispatch, proto);
    
    return XDP_PASS; // reached only if tail_call fails
}

SEC("xdp/tcp")
int handle_tcp(struct xdp_md *ctx)
{
    // ... TCP-specific logic ...
    return XDP_PASS;
}

// Userspace: register handlers
bpf_map_update_elem(dispatch_fd, &PROTO_TCP, &tcp_prog_fd, BPF_ANY);
bpf_map_update_elem(dispatch_fd, &PROTO_UDP, &udp_prog_fd, BPF_ANY);
```

### 17.3 Socket Local Storage for Connection Tracking

```c
// Per-connection state using SK_STORAGE
struct conn_state {
    __u64 bytes_in;
    __u64 bytes_out;
    __u64 start_time;
    __u32 req_count;
};

struct {
    __uint(type, BPF_MAP_TYPE_SK_STORAGE);
    __uint(map_flags, BPF_F_NO_PREALLOC);
    __type(key, int);                  // ignored for sk_storage
    __type(value, struct conn_state);
} conn_map SEC(".maps");

SEC("sockops")
int track_connection(struct bpf_sock_ops *skops)
{
    switch (skops->op) {
    case BPF_SOCK_OPS_TCP_CONNECT_CB: {
        // New connection: initialize state
        struct conn_state init = {
            .start_time = bpf_ktime_get_ns(),
        };
        // BPF_LOCAL_STORAGE_GET_F_CREATE: create if not exists
        bpf_sk_storage_get(&conn_map, skops->sk, &init,
                           BPF_LOCAL_STORAGE_GET_F_CREATE);
        break;
    }
    case BPF_SOCK_OPS_TCP_CLOSE_CB: {
        // Connection closing: read final stats
        struct conn_state *state = bpf_sk_storage_get(&conn_map, skops->sk, 0, 0);
        if (state) {
            __u64 duration_ns = bpf_ktime_get_ns() - state->start_time;
            // Emit final stats to ring buffer...
        }
        // Storage is automatically freed when socket is destroyed
        break;
    }
    }
    return 1;
}
```

---

## 18. Introspection and Debugging

### Using `bpftool` for Map Inspection

```bash
# List all loaded maps
bpftool map list
# Output:
# 42: hash  name pid_open_count  flags 0x0
#     key 4B  value 8B  max_entries 10240  memlock 655360B
# 43: ringbuf  name events  flags 0x0
#     max_entries 262144  memlock 278528B

# Dump map contents (requires BTF for pretty-print)
bpftool map dump id 42
# With BTF:
# [{ "key": 1234, "value": 42 }, { "key": 5678, "value": 100 }]
# Without BTF:
# key: 04 d2 00 00  value: 2a 00 00 00 00 00 00 00

# Lookup specific key
bpftool map lookup id 42 key 0x04 0xd2 0x00 0x00

# Update a value from CLI (useful for config maps)
bpftool map update id 42 key 0 0 0 0 value 10 0 0 0 0 0 0 0

# Get map info
bpftool map show id 42

# Pin a map to BPFFS
bpftool map pin id 42 /sys/fs/bpf/my_map

# Show map memory usage
bpftool map show --json id 42 | jq '.memlock'
```

### Kernel `/proc` and `/sys` Introspection

```bash
# All BPF maps visible to current user
ls -la /proc/*/fdinfo/* 2>/dev/null | grep "bpf-map"

# Map details via fdinfo
cat /proc/$(pgrep my_prog)/fdinfo/5
# pos:    0
# flags:  02000002
# mnt_id: 14
# map_type:       1
# key_size:       4
# value_size:     8
# max_entries:    10240
# map_flags:      0x0
# map_extra:      0x0
# memlock:        655360
# map_id:         42
# frozen:         0

# BPF programs currently loaded
bpftool prog list

# Verify map is pinned
ls -la /sys/fs/bpf/
```

### Map Profiling with `perf`

```bash
# Profile BPF helper calls
perf stat -e 'bpf:*' -- sleep 10

# Trace BPF map operations
bpftrace -e '
  tracepoint:bpf:bpf_map_lookup_elem {
    @lookups[args->map_id] = count();
  }
  interval:s:1 {
    print(@lookups);
    clear(@lookups);
  }
'
```

---

## 19. Mental Models and Decision Trees

### Map Type Selection Decision Tree

```
  What do you need the map for?
  │
  ├─ Store per-packet counters / high-frequency stats?
  │       └─► BPF_MAP_TYPE_PERCPU_ARRAY or PERCPU_HASH
  │               (no contention, fastest update path)
  │
  ├─ Lookup by arbitrary key (IP, PID, port)?
  │   ├─ Key space unbounded / sparse?
  │   │   ├─ Need automatic eviction when full?
  │   │   │   └─► BPF_MAP_TYPE_LRU_HASH
  │   │   └─ Manual eviction / bounded entries?
  │   │       └─► BPF_MAP_TYPE_HASH
  │   └─ Key space is dense integer range [0..N)?
  │       └─► BPF_MAP_TYPE_ARRAY (fastest possible)
  │
  ├─ IP prefix / subnet matching (routing, firewall)?
  │   └─► BPF_MAP_TYPE_LPM_TRIE
  │
  ├─ Send events from eBPF to userspace?
  │   ├─ Kernel < 5.8?
  │   │   └─► BPF_MAP_TYPE_PERF_EVENT_ARRAY (legacy)
  │   └─► BPF_MAP_TYPE_RINGBUF (modern, preferred)
  │
  ├─ Chain multiple eBPF programs in a pipeline?
  │   └─► BPF_MAP_TYPE_PROG_ARRAY + bpf_tail_call()
  │
  ├─ Per-connection / per-socket state?
  │   └─► BPF_MAP_TYPE_SK_STORAGE (auto-cleanup on socket close)
  │
  ├─ Atomically swap a ruleset while programs are running?
  │   └─► BPF_MAP_TYPE_ARRAY_OF_MAPS or HASH_OF_MAPS
  │
  ├─ FIFO work queue?
  │   └─► BPF_MAP_TYPE_QUEUE
  │
  ├─ LIFO stack?
  │   └─► BPF_MAP_TYPE_STACK
  │
  └─ Redirect packets between network interfaces?
      └─► BPF_MAP_TYPE_DEVMAP or DEVMAP_HASH
```

### Concurrency Strategy Decision Tree

```
  Is the value updated from eBPF programs?
  │
  ├─ YES:
  │   ├─ Is it just a simple counter?
  │   │   ├─ Update from multiple CPUs frequently?
  │   │   │   └─► PERCPU map + userspace aggregation
  │   │   │           (zero-overhead, best performance)
  │   │   └─► OK with some contention?
  │   │           └─► __sync_fetch_and_add (atomic)
  │   │
  │   └─ Multiple fields must be updated atomically?
  │       └─► struct bpf_spin_lock in value struct
  │
  └─ NO (read-only from eBPF, written only from userspace):
      └─► BPF_MAP_FREEZE after initial write
          or BPF_F_RDONLY_PROG flag
```

### Memory Efficiency Decision Tree

```
  Key space is:
  │
  ├─ Dense integers [0..N]:    ARRAY or PERCPU_ARRAY
  │   (no per-element metadata overhead)
  │
  ├─ Sparse / unpredictable:   HASH
  │   ├─ Will be accessed in IRQ context (XDP)?
  │   │   └─► HASH without BPF_F_NO_PREALLOC
  │   │       (pre-allocation is interrupt-safe)
  │   └─► HASH with BPF_F_NO_PREALLOC (saves memory if sparse)
  │
  └─ Unbounded (connection tracking, caches):   LRU_HASH
      Set max_entries = practical upper bound
      LRU eviction handles overflow automatically
```

### Performance Mental Model: "Where Is The Cost?"

```
  eBPF Map Access Cost Breakdown:

  1. ARRAY lookup (best case):
     ─────────────────────────
     [ bounds check key ]           ~1 cycle
     [ compute offset: base + k*vsz ] ~2 cycles
     [ return pointer ]             ~1 cycle
     Total: ~3-5 cycles

  2. HASH lookup (typical):
     ─────────────────────────
     [ hash the key (siphash) ]     ~10-20 cycles
     [ index into bucket array ]    ~5 cycles
     [ cache miss (L3) ]            ~40-100 cycles
     [ walk chain (1-2 elements) ]  ~5-10 cycles
     [ spinlock acquire/release ]   ~10-30 cycles (if contested)
     Total: ~70-165 cycles

  3. PERCPU_ARRAY (no sharing):
     ─────────────────────────
     [ get per_cpu_ptr for this CPU ] ~3 cycles
     [ offset arithmetic ]           ~2 cycles
     [ L1 cache hit (hot data) ]     ~4 cycles
     Total: ~9 cycles
     → No lock, no atomic, optimal

  Key insight:
  The dominant cost in hash maps is CACHE MISSES, not hashing.
  If your map fits in L3 cache, hash maps can approach array speed.
  If your map is large (> L3), hash maps are dominated by DRAM latency (~100ns).
```

---

## Appendix A: Complete Map Type Reference

```
  Kernel     Type constant                    Category
  ─────────────────────────────────────────────────────────
  3.18+      BPF_MAP_TYPE_HASH               Generic
  3.18+      BPF_MAP_TYPE_ARRAY              Generic
  3.18+      BPF_MAP_TYPE_PROG_ARRAY         Control flow
  3.18+      BPF_MAP_TYPE_PERF_EVENT_ARRAY   Events
  4.6+       BPF_MAP_TYPE_PERCPU_HASH        Per-CPU
  4.6+       BPF_MAP_TYPE_PERCPU_ARRAY       Per-CPU
  4.6+       BPF_MAP_TYPE_STACK_TRACE        Profiling
  4.8+       BPF_MAP_TYPE_CGROUP_ARRAY       Cgroups
  4.10+      BPF_MAP_TYPE_LRU_HASH           Caching
  4.10+      BPF_MAP_TYPE_LRU_PERCPU_HASH    Caching+PerCPU
  4.11+      BPF_MAP_TYPE_LPM_TRIE           Networking
  4.12+      BPF_MAP_TYPE_ARRAY_OF_MAPS      Composition
  4.12+      BPF_MAP_TYPE_HASH_OF_MAPS       Composition
  4.14+      BPF_MAP_TYPE_DEVMAP             XDP
  4.14+      BPF_MAP_TYPE_SOCKMAP            Sockets
  4.15+      BPF_MAP_TYPE_CPUMAP             XDP
  4.18+      BPF_MAP_TYPE_XSKMAP             AF_XDP
  4.18+      BPF_MAP_TYPE_SOCKHASH           Sockets
  4.20+      BPF_MAP_TYPE_CGROUP_STORAGE     Cgroups (deprecated)
  4.20+      BPF_MAP_TYPE_REUSEPORT_SOCKARRAY  Load balancing
  4.20+      BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE Cgroups (deprecated)
  4.20+      BPF_MAP_TYPE_QUEUE              FIFO
  4.20+      BPF_MAP_TYPE_STACK              LIFO
  5.1+       BPF_MAP_TYPE_SK_STORAGE         Local storage
  5.2+       BPF_MAP_TYPE_DEVMAP_HASH        XDP
  5.6+       BPF_MAP_TYPE_STRUCT_OPS         Kernel struct ops
  5.8+       BPF_MAP_TYPE_RINGBUF            Events (modern)
  5.10+      BPF_MAP_TYPE_INODE_STORAGE      Local storage
  5.10+      BPF_MAP_TYPE_TASK_STORAGE       Local storage
  5.15+      BPF_MAP_TYPE_BLOOM_FILTER       Probabilistic
  6.2+       BPF_MAP_TYPE_USER_RINGBUF       Userspace-to-BPF
  6.6+       BPF_MAP_TYPE_CGRP_STORAGE       Cgroups
```

---

## Appendix B: Common Errno Values from Map Operations

```
  Return code    Meaning
  ─────────────────────────────────────────────────────────────
  0              Success
  -ENOENT        Key not found (lookup, delete, get_next_key at end)
  -EEXIST        Key already exists (update with BPF_NOEXIST)
  -E2BIG         Map is full (update/insert when at max_entries)
  -EINVAL        Invalid argument (bad flags, mismatched sizes)
  -EPERM         Permission denied (CAP_BPF required, frozen map)
  -ENOMEM        Out of memory (cannot allocate element)
  -EBADF         Invalid file descriptor
  -EFAULT        Bad user-space pointer (key or value pointer invalid)
  -EACCES        Access denied (BPF_F_RDONLY or BPF_F_WRONLY violated)
  -ENOTSUPP      Operation not supported for this map type
  -EBUSY         Map is being modified (concurrent spinlock)
```

---

*This guide covers eBPF maps through Linux kernel 6.x. The landscape evolves rapidly — always check kernel documentation and kernel source (`kernel/bpf/`) for the authoritative specification.*

Now let me write the comprehensive eBPF maps guide:2,807 lines of dense, structured coverage. Here's what the guide contains and the mental architecture behind it:

---

### What This Guide Covers (and Why in That Order)

**The guide is layered deliberately** — each section is the prerequisite for the next:

1. **Conceptual Foundation** — establishes the *two roles* of maps: persistent state and communication channel. Before touching a single syscall, you need this mental model locked in.

2. **Kernel Architecture** — goes into `struct bpf_map`, the vtable (`bpf_map_ops`), and how maps live in kernel memory. Most guides skip this, but knowing the internals prevents entire categories of confusion later (e.g., "why can't I delete from an array map?").

3. **`bpf()` Syscall + Call Flow** — traces the exact kernel path from `bpf(BPF_MAP_CREATE)` all the way to `anon_inode_getfd`. This is the single gate between worlds.

4. **Reference Counting** — the most subtle concept. A map's lifetime is governed by `refcnt`. Misunderstanding this causes either premature map destruction or memory leaks.

5. **All Map Types** — every type, with conceptual explanation (no assumed knowledge), memory layout, and when to choose it. Includes types most guides ignore (SK_STORAGE, RINGBUF, QUEUE/STACK).

6. **Complete C + Rust implementations** — the C code shows a full kprobe-based monitoring tool with 4 map types simultaneously. The Rust (Aya) code shows idiomatic kernel and userspace split.

7. **Decision Trees** — the "which map type?", "which sync strategy?", and "where is the cost?" trees train your intuition to pick the right tool instantly.

**One insight to burn in**: the return value of `bpf_map_lookup_elem` inside an eBPF program is a **direct pointer into kernel memory** — not a copy. This is why per-CPU maps are so fast (you write directly into the slot), and why concurrent updates without atomics are data races.