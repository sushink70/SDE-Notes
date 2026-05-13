# RFC vs Production Code: The Complete Guide to the Gap
### Why a 30-Page RFC Becomes 12,000+ Lines of Code

---

> "An RFC describes what the system *should do*. Production code describes everything the system *must survive*."

---

## Table of Contents

1. [The Mental Model: Two Different Universes](#1-the-mental-model-two-different-universes)
2. [What an RFC Actually Is (and Isn't)](#2-what-an-rfc-actually-is-and-isnt)
3. [The Anatomy of the Gap](#3-the-anatomy-of-the-gap)
4. [Layer 1 — Coding Conventions and Standards](#4-layer-1--coding-conventions-and-standards)
5. [Layer 2 — Error Handling and Defensive Programming](#5-layer-2--error-handling-and-defensive-programming)
6. [Layer 3 — Memory Management](#6-layer-3--memory-management)
7. [Layer 4 — Concurrency, Locking, and Synchronization](#7-layer-4--concurrency-locking-and-synchronization)
8. [Layer 5 — Performance and Optimization Infrastructure](#8-layer-5--performance-and-optimization-infrastructure)
9. [Layer 6 — Platform and OS Abstractions](#9-layer-6--platform-and-os-abstractions)
10. [Layer 7 — Observability — Logging, Tracing, Metrics](#10-layer-7--observability--logging-tracing-metrics)
11. [Layer 8 — Configuration, Tunables, and Feature Flags](#11-layer-8--configuration-tunables-and-feature-flags)
12. [Layer 9 — Backward Compatibility and Versioning](#12-layer-9--backward-compatibility-and-versioning)
13. [Layer 10 — Security Hardening](#13-layer-10--security-hardening)
14. [Layer 11 — Integration with Existing Systems](#14-layer-11--integration-with-existing-systems)
15. [Layer 12 — Testing Infrastructure Inside the Code](#15-layer-12--testing-infrastructure-inside-the-code)
16. [Layer 13 — Edge Cases, Corner Cases, and Undefined Behavior](#16-layer-13--edge-cases-corner-cases-and-undefined-behavior)
17. [VXLAN RFC 7348 vs Linux Kernel: A Deep Case Study](#17-vxlan-rfc-7348-vs-linux-kernel-a-deep-case-study)
18. [The Code Growth Equation](#18-the-code-growth-equation)
19. [Mental Models for Thinking Like a Systems Programmer](#19-mental-models-for-thinking-like-a-systems-programmer)
20. [Summary Table: RFC Says vs Code Does](#20-summary-table-rfc-says-vs-code-does)

---

## 1. The Mental Model: Two Different Universes

Before we dive deep, you need to understand that RFCs and production code exist in fundamentally different **epistemic universes** — they answer completely different questions.

```
+--------------------------------------------------+--------------------------------------------------+
|              RFC / SPECIFICATION UNIVERSE        |         PRODUCTION CODE UNIVERSE                 |
+--------------------------------------------------+--------------------------------------------------+
|                                                  |                                                  |
|  Question: WHAT should happen?                   |  Question: HOW does it actually happen,          |
|                                                  |  and what happens when everything goes wrong?    |
|                                                  |                                                  |
|  Audience: Protocol designers, implementers,     |  Audience: Compilers, CPUs, kernels, networks,   |
|            standards bodies                      |            attackers, broken hardware             |
|                                                  |                                                  |
|  Describes: The HAPPY PATH                       |  Must handle: ALL paths including impossible ones |
|                                                  |                                                  |
|  Assumes: Cooperative participants               |  Assumes: Hostile environment, malicious actors, |
|                                                  |           hardware faults, cosmic rays           |
|                                                  |                                                  |
|  Language: Natural language (English)            |  Language: Executable logic (C, Rust, Go, ...)   |
|                                                  |                                                  |
|  Time: Timeless (describes behavior)             |  Time: Real-time (must meet deadlines)           |
|                                                  |                                                  |
|  Errors: "MUST return error"                     |  Errors: WHICH error? When? Logged? Retried?      |
|                                                  |           Propagated? Recovered?                 |
|                                                  |                                                  |
+--------------------------------------------------+--------------------------------------------------+
```

### The Verbal vs Written Code Gap

When you *describe* an algorithm verbally:
- "Send the packet to the tunnel endpoint"

When you *write* it in code:
- Allocate the packet buffer (how big? from which pool?)
- Validate the source address (IPv4? IPv6? Both?)
- Look up the VTEP (Virtual Tunnel Endpoint) in the forwarding table
- Lock the forwarding table (reader lock? writer lock?)
- Handle miss: drop? flood? notify control plane?
- Encapsulate: add VXLAN header, UDP header, outer IP header
- Handle MTU: fragment? PMTUD? silently drop?
- Select the source UDP port (hash of inner flow for ECMP)
- Check if the socket is ready (send buffer full?)
- Handle socket errors
- Update statistics counters (atomically!)
- Release the lock
- Handle the case where the lock was dropped midway because another CPU changed the table

That's ONE verbal sentence becoming ~200 lines of code with 15 decision branches.

---

## 2. What an RFC Actually Is (and Isn't)

### What RFC Stands For

**RFC = Request for Comments**. Not "Rules For Code". It is a document published by the IETF (Internet Engineering Task Force) that describes a protocol, mechanism, or best practice.

```
RFC Life Cycle:
                                                                    
  Idea ──► Internet Draft ──► Working Group Review ──► IETF Last Call
                                                                    |
                                                                    ▼
                                                           RFC Published
                                                                    |
                                              ┌─────────────────────┤
                                              │                     │
                                              ▼                     ▼
                                         Informational         Standards Track
                                         (describes,          (MUST, SHOULD,
                                          explains)            MAY — normative)
```

### RFC Keywords — The Precise Vocabulary

RFC 2119 defines the meaning of these words:

```
+----------+------------------------------------------------------------------+
| Keyword  | Meaning                                                          |
+----------+------------------------------------------------------------------+
| MUST     | Absolute requirement. No exceptions.                             |
| MUST NOT | Absolute prohibition.                                            |
| REQUIRED | Same as MUST                                                     |
| SHALL    | Same as MUST                                                     |
| SHOULD   | Recommended. Can be ignored with valid reason.                   |
| SHOULD NOT | Not recommended but not forbidden.                            |
| RECOMMENDED | Same as SHOULD                                               |
| MAY      | Optional. Implementation's choice.                               |
| OPTIONAL | Same as MAY                                                      |
+----------+------------------------------------------------------------------+
```

### What an RFC Deliberately OMITS

RFCs intentionally say NOTHING about:

```
Things RFC Omits
      │
      ├── Implementation language
      ├── Data structures and algorithms to use
      ├── Memory allocation strategy
      ├── Threading / concurrency model
      ├── How to handle hardware limitations
      ├── Operating system integration
      ├── Performance targets
      ├── Security beyond the protocol itself
      ├── Logging and debugging
      ├── Configuration interfaces
      ├── How to test the implementation
      └── What happens when the network is broken DURING your operation
```

These omissions are **intentional** — the RFC describes an abstract protocol, not a concrete machine.

---

## 3. The Anatomy of the Gap

Here is the complete map of everything that lives between the RFC description and the production code:

```
                     THE GAP ANATOMY
                                                                        
    RFC TEXT                                                 PRODUCTION CODE
    ─────────────────────────────────────────────────────────────────────────
                                                                        
    "A VXLAN packet                                        +─────────────────+
     MUST have VNI                                         │  Coding         │ ◄── Naming, style, idioms
     field set"                                            │  Conventions    │     kernel coding style
                         +─────────────────────────────►  +─────────────────+
                         │                                 │  Error          │ ◄── What if malloc fails?
                         │                                 │  Handling       │     What if NIC is down?
                         │                                 +─────────────────+
                         │                                 │  Memory         │ ◄── kmalloc vs vmalloc
                         │                                 │  Management     │     slab allocators, GFP flags
                         │                                 +─────────────────+
                         │  Each "sentence"                │  Concurrency    │ ◄── RCU locks, spinlocks
                         │  in RFC expands                 │  & Locking      │     per-CPU data, barriers
                         │  into ALL these                 +─────────────────+
                         │  layers                         │  Performance    │ ◄── NAPI, GRO, GSO, XDP
                         │                                 │  Optimization   │     zero-copy, SIMD
                         │                                 +─────────────────+
                         │                                 │  Platform       │ ◄── Big-endian/little-endian
                         │                                 │  Abstraction    │     32-bit/64-bit
                         │                                 +─────────────────+
                         │                                 │  Observability  │ ◄── netstat, ethtool stats
                         │                                 │  (logs/metrics) │     /proc files, tracepoints
                         │                                 +─────────────────+
                         │                                 │  Configuration  │ ◄── ip link, netlink attrs
                         │                                 │  & Tunables     │     sysctl, ethtool
                         │                                 +─────────────────+
                         │                                 │  Backward       │ ◄── Old kernels, old tools
                         │                                 │  Compatibility  │     old userspace
                         │                                 +─────────────────+
                         │                                 │  Security       │ ◄── Namespace isolation
                         │                                 │  Hardening      │     privilege checks
                         │                                 +─────────────────+
                         │                                 │  System         │ ◄── Netfilter hooks
                         │                                 │  Integration    │     bridge, routing tables
                         │                                 +─────────────────+
                         │                                 │  Testing &      │ ◄── KUNIT, self-tests
                         │                                 │  Debug hooks    │     ftrace integration
                         │                                 +─────────────────+
                         │                                 │  Edge Cases     │ ◄── MTU=0, VNI=0xFFFFFF
                         └─────────────────────────────►  │  & Undefined    │     packet storms
                                                          │  Behavior       │
                                                          +─────────────────+
```

Now let's go through each layer **in complete depth**.

---

## 4. Layer 1 — Coding Conventions and Standards

### What This Means

Every codebase has a set of rules about how code is **written**, **named**, **formatted**, and **structured** — independent of what the code does. These rules exist so that thousands of developers can read and modify code written by strangers.

### Linux Kernel Coding Style (Documentation/process/coding-style.rst)

The Linux kernel has an explicit coding style that adds lines purely for readability and convention:

```
RFC says nothing about naming. Linux kernel enforces:

  snake_case for everything:        vxlan_find_mac()
  8-character tabs (not spaces):    <TAB>return -ENOMEM;
  80-column line limit (soft):      /* Forces line breaks and comments */
  Braces on same line (K&R style):  if (condition) {
                                        ...
                                    }
  No typedefs except for function   typedef int (*vxlan_rcv_t)(...);
  pointers:
  
  Comments in C89 style:            /* This is a comment */
                                    /* NOT // this style */
```

### Data Structure Layout Conventions

In kernel code, structures are organized with specific patterns:

```c
/*
 * RFC describes "a VXLAN header". Kernel code defines:
 *
 * struct vxlanhdr {
 *     __be32 vx_flags;    /* __be32 = big-endian 32-bit, explicit endianness */
 *     __be32 vx_vni;      /* Even field naming encodes semantics */
 * };
 *
 * struct vxlan_dev {
 *     ────────────────────── HOT PATH FIELDS (cache line 1, first 64 bytes) ──
 *     struct net_device  *dev;       /* Most accessed — first in struct */
 *     struct vxlan_sock  __rcu *vn4_sock; /* __rcu annotation = RCU protected */
 *     
 *     ────────────────────── COLD PATH FIELDS (accessed rarely) ──────────────
 *     struct list_head   next;       /* Linked list node */
 *     struct vxlan_config cfg;       /* Configuration — written once */
 *     ...
 * };
 */
```

**Why this matters:** Structure field ordering affects cache performance. Hot fields (accessed in the data path) go first so they fit in the first CPU cache line (64 bytes on x86). This is **invisible to the RFC** but critical to performance.

### Namespace Prefixing

Every function, struct, macro in a module is prefixed to avoid collision:

```
vxlan_rcv()          — receive function
vxlan_xmit()         — transmit function  
vxlan_find_mac()     — FDB lookup
vxlan_dev_alloc()    — allocation
VXLAN_VID_MASK       — constant
VXLAN_F_LEARN        — flag
```

This is **0 lines of RFC** but hundreds of lines of actual code just for the naming infrastructure.

### The `goto` Pattern for Cleanup (Linux Kernel Idiom)

The kernel uses `goto` for error cleanup — a pattern invisible to any RFC:

```c
static int vxlan_dev_configure(struct net *src_net, struct net_device *dev, ...)
{
    struct vxlan_dev *vxlan = netdev_priv(dev);
    int err;

    /* Each step that can fail gets its own label */
    err = register_netdevice(dev);
    if (err)
        goto err_register;        /* Jump to cleanup */

    err = vxlan_sock_add(vxlan);
    if (err)
        goto err_sock;            /* Jump to partial cleanup */

    err = vxlan_multicast_join(vxlan);
    if (err)
        goto err_mcast;

    return 0;                     /* SUCCESS PATH */

/* Cleanup labels — unwound in REVERSE ORDER of acquisition */
err_mcast:
    vxlan_sock_release(vxlan);
err_sock:
    unregister_netdevice(dev);
err_register:
    return err;
}
```

This pattern is **100% absent from any RFC**. It is an entire coding discipline.

---

## 5. Layer 2 — Error Handling and Defensive Programming

### What the RFC Says vs What Code Must Do

```
RFC says:   "If the VNI is not recognized, the packet MUST be dropped."

Code does:  
    1. Check if packet is large enough to even contain a VNI field
    2. Read the VNI field (endian conversion required)
    3. Look up VNI in hash table (what if table is being modified right now?)
    4. If not found: drop the packet
         - Increment "dropped" counter
         - Optionally log (but not every packet — log rate limiting!)
         - Free the packet buffer (memory leak if you forget)
         - Return error code (-ENODEV? -EINVAL? -ENOENT?)
    5. If found but device is shutting down: drop
    6. If found but device has no IP address yet: drop
    7. If found but device is in error state: drop
```

### The Error Code Universe

Linux kernel has hundreds of error codes. Choosing the right one is a convention:

```
Error Code     Meaning                              When to use
───────────────────────────────────────────────────────────────────
-ENOMEM        Out of memory                        kmalloc() failed
-EINVAL        Invalid argument                     Bad parameter from user
-ENODEV        No such device                       Device not found
-ENOENT        No such entry                        FDB entry not found
-EEXIST        Already exists                       Adding duplicate entry
-EBUSY         Resource busy                        Device in use, can't change
-EOPNOTSUPP    Operation not supported              Feature not compiled in
-EAFNOSUPPORT  Address family not supported         IPv6 on IPv4-only socket
-ERANGE        Value out of range                   VNI > 16777215
-EPROTONOSUPPORT Protocol not supported             Unknown VXLAN extension
-ETIMEDOUT     Timeout                              ARP/neighbor resolution
```

RFC says "drop the packet" — it doesn't tell you that there are 47 different reasons to drop, each requiring a different counter, different log level, different error code.

### Defensive Programming: Validating What RFC Takes for Granted

RFC assumes well-formed packets. Code must validate everything:

```
Incoming VXLAN Packet Validation Chain:

  Receive skb (socket buffer)
       │
       ▼
  ┌─────────────────────────────────────────────────────┐
  │ Is skb non-NULL?                                    │ ◄─ Kernel bug defense
  └──────────────────────────┬──────────────────────────┘
                             │ YES
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Is packet long enough for UDP header?               │ ◄─ Truncated packets
  │ (pskb_may_pull check)                               │
  └──────────────────────────┬──────────────────────────┘
                             │ YES
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Is packet long enough for VXLAN header? (8 bytes)   │ ◄─ RFC 7348 §5
  └──────────────────────────┬──────────────────────────┘
                             │ YES
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Is VXLAN I-flag set (bit 27)?                       │ ◄─ RFC MUST check
  └──────────────────────────┬──────────────────────────┘
                             │ YES (drop if NO)
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Are reserved bits zero?                             │ ◄─ RFC: MUST be 0
  │ (Some extensions reuse these — configurable)        │     BUT extensions use them
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Extract VNI (24-bit, big-endian shift)              │
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ VNI == 0? (Some implementations forbid VNI 0)       │ ◄─ NOT in RFC
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Look up vxlan_dev for this VNI + UDP port           │
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────┐
  │ Is inner packet well-formed? (Ethernet header ok?)  │ ◄─ NOT in RFC
  └──────────────────────────┬──────────────────────────┘
                             │ ALL CHECKS PASSED
                             ▼
                      Forward to inner device
```

Every box in this diagram is 5-30 lines of code. The RFC describes only the boxes that have "RFC" annotations.

### Rate-Limited Logging

This is entirely absent from RFCs but crucial:

```c
/* RFC says nothing about this. Production code MUST have it.
 * Without rate limiting, a packet flood causes a LOG flood,
 * which causes kernel ring buffer overflow,
 * which causes debugging information to be lost,
 * which causes a kernel panic or performance collapse.
 */

if (net_ratelimit())
    netdev_dbg(vxlan->dev, "invalid vxlan flags=%#x vni=%u\n",
               ntohl(vxlan->vx_flags), vxlan->vx_vni);
```

`net_ratelimit()` internally uses a token bucket to allow at most N log messages per second. This is 0 RFC lines but prevents real-world production disasters.

---

## 6. Layer 3 — Memory Management

### The RFC World Has No Memory

An RFC says "store this entry" or "create a tunnel". It never says:
- How much memory?
- Where from?
- What if allocation fails?
- How long does it live?
- Who frees it?
- What if two threads try to free it simultaneously?

### Linux Kernel Memory Allocators

The kernel has multiple allocators, each for a different purpose:

```
MEMORY ALLOCATION DECISION TREE (Linux Kernel)
                                                        
          Need memory?
               │
    ┌──────────┴────────────┐
    │                       │
  Small object           Large allocation
  (< 1 page = 4KB)       (multiple pages)
    │                       │
    ▼                       ▼
  kmalloc()             vmalloc()  or
  (physically            alloc_pages()
   contiguous,
   fast)
    │
    ├── Can sleep? (process context)
    │       └── GFP_KERNEL   ← normal allocation, can sleep
    │
    ├── Cannot sleep? (interrupt context, holding spinlock)
    │       └── GFP_ATOMIC   ← must succeed immediately or fail
    │                          uses emergency memory reserves
    │
    └── DMA needed? (hardware direct memory access)
            └── GFP_DMA      ← must be in specific address range
```

**GFP flags** — "Get Free Pages" flags — do not appear anywhere in any networking RFC. But every allocation in the Linux kernel must specify them, and choosing wrong causes kernel panics.

### Reference Counting (refcount)

The RFC says "a tunnel device". The code must track:
- Who holds a reference to this device?
- Is it safe to free it?
- What if it's being freed while a packet is being processed?

```
Reference Counting for a VXLAN Device:

  vxlan_dev created
       │
       ▼
  refcount = 1  (created by netlink configuration)
       │
       ├─── Packet arrives, takes reference
       │    refcount = 2
       │         │
       │         └── Packet processed, releases reference
       │             refcount = 1
       │
       ├─── FDB entry holds reference
       │    refcount = 2
       │
       └─── User runs "ip link delete vxlan0"
                refcount decremented
                if refcount == 0:
                    FREE the device
                else:
                    Mark as "being deleted"
                    Free when last user releases
```

Without reference counting, you get **use-after-free bugs**: code reads memory that has been freed and reused by something else. In a kernel, this is a security vulnerability and a system crash.

### Slab Allocator and Per-CPU Caches

For objects allocated and freed frequently (like FDB entries), the kernel uses the **slab allocator**:

```
SLAB ALLOCATOR CONCEPT:

  Instead of:
    malloc() → expensive system call, fragmentation
    free()   → expensive system call

  Slab allocator:
  
  +─────────────────────────────────────────────────────+
  │                   SLAB CACHE                        │
  │  (pre-allocated pool of same-sized objects)         │
  │                                                     │
  │  [ FREE ][ FREE ][ USED ][ FREE ][ USED ][ USED ]   │
  │                                                     │
  │  kmem_cache_alloc() → grab from free list           │
  │  kmem_cache_free()  → return to free list           │
  │                                                     │
  │  Per-CPU: CPU 0 has its own free list               │
  │           CPU 1 has its own free list               │
  │           → no lock contention for common case      │
  └─────────────────────────────────────────────────────+
```

The RFC describes "a forwarding table entry". The code defines a slab cache for that entry type, its size, its alignment, its constructor/destructor, and per-CPU caching behavior.

### RCU (Read-Copy-Update)

**This is one of the most important concepts absent from all RFCs.**

**Concept:** A synchronization mechanism for read-heavy data structures. Readers never lock. Writers make a copy, update it, then atomically swap the pointer.

**Why it exists:** The FDB (Forwarding Database) is read on every single packet. If you used a regular lock:
- Every packet: acquire lock → read → release lock
- On a 10Gbps link: millions of packets per second → millions of lock operations
- Lock contention → performance collapse

**RCU solution:**

```
RCU CONCEPT DIAGRAM:

  BEFORE UPDATE:
  
  vxlan_dev ──► fdb_table ──► [entry1] ──► [entry2] ──► [entry3]
  
  
  DURING UPDATE (reader can still use old table safely):
  
  vxlan_dev ──────────────► fdb_table ──► [entry1] ──► [entry2] ──► [entry3]
                                                                        │
  (Writer creates new table)                                        (old)
  new_table ──► [entry1] ──► [entry2] ──► [entry3] ──► [NEW_entry4]
  
  
  AFTER UPDATE (atomic pointer swap):
  
  vxlan_dev ──► new_table ──► [entry1] ──► [entry2] ──► [entry3] ──► [entry4]
  
  (old table freed after all current readers finish their read-side critical section)
```

In code, this manifests as:
- `rcu_read_lock()` / `rcu_read_unlock()` around every FDB lookup
- `__rcu` annotation on pointers
- `rcu_assign_pointer()` for writes
- `rcu_dereference()` for reads
- `call_rcu()` or `synchronize_rcu()` for deferred freeing

**RFC 7348 says nothing about RCU.** But removing RCU from the VXLAN implementation would reduce performance by 10x.

---

## 7. Layer 4 — Concurrency, Locking, and Synchronization

### The RFC's World is Single-Threaded

Every RFC implicitly assumes a single actor doing one thing at a time. The real world has:

```
CONCURRENT ACCESS TO A VXLAN DEVICE:

  CPU 0                    CPU 1                    CPU 2
  ─────                    ─────                    ─────
  Processing inbound        Adding FDB entry         User running
  packet, looking up        (ip neigh add ...)       "ip link delete vxlan0"
  FDB entry                                          
                                                     
  vxlan_rcv()               vxlan_fdb_add()          vxlan_dellink()
       │                         │                        │
       │  READ fdb_table         │  WRITE fdb_table       │  FREE device
       │                         │                        │
       └─────────────────────────┴────────────────────────┘
                         RACE CONDITION!
                         Without proper locking:
                         CPU 0 reads freed memory → kernel panic
```

### Types of Locks in Linux Kernel

```
LOCK DECISION TREE:
                                                              
  Who accesses this data?
         │
         ├── Only current process (no interrupts, no other CPUs)?
         │       └── No lock needed (local variable, per-thread)
         │
         ├── Multiple CPUs, but mostly reading, rarely writing?
         │       └── RCU (rcu_read_lock, rcu_assign_pointer)
         │           OR  rwlock_t (rwlock_init, read_lock, write_lock)
         │
         ├── Multiple CPUs, frequently read AND written?
         │       ├── Critical section is SHORT (no sleeping allowed)?
         │       │       └── spinlock_t (spin_lock, spin_unlock)
         │       │           spinlock_t + BH disabled (spin_lock_bh)
         │       │           spinlock_t + IRQ disabled (spin_lock_irqsave)
         │       │
         │       └── Critical section CAN sleep?
         │               └── mutex_t (mutex_lock, mutex_unlock)
         │                   semaphore (down, up)
         │
         └── Per-CPU data (each CPU has its own copy)?
                 └── per_cpu(), this_cpu_inc(), get_cpu_var()
                     → no lock needed, each CPU owns its copy
```

### What Locking Looks Like in VXLAN Code

The FDB (Forwarding Database) uses a spinlock + RCU hybrid:

```c
/* RFC says: "maintain a forwarding table"
 * Code says: HOW to maintain it safely under concurrent access
 */

struct vxlan_dev {
    spinlock_t       hash_lock[FDB_HASH_SIZE];  /* Per-bucket locks! */
    /* Not one lock for whole table — that serializes all CPUs */
    /* Per-bucket: CPUs working on different hash buckets don't contend */
    
    struct hlist_head fdb_head[FDB_HASH_SIZE] __rcu; /* RCU-protected */
};

/* Lookup (called millions of times per second): */
static struct vxlan_fdb *vxlan_find_mac(struct vxlan_dev *vxlan,
                                         const u8 *mac, __be32 vni)
{
    struct hlist_head *head = vxlan_fdb_head(vxlan, mac, vni);
    struct vxlan_fdb *f;

    hlist_for_each_entry_rcu(f, head, hlist) {  /* RCU read, no lock! */
        if (ether_addr_equal(mac, f->eth_addr) && f->vni == vni)
            return f;
    }
    return NULL;
}

/* Update (called rarely): */
static int vxlan_fdb_update(struct vxlan_dev *vxlan, ...)
{
    u32 hash_index = vxlan_fdb_find_uc(vxlan, mac, vni);
    
    spin_lock_bh(&vxlan->hash_lock[hash_index]);  /* WRITE: needs lock */
    /* ... modify the table ... */
    spin_unlock_bh(&vxlan->hash_lock[hash_index]);
}
```

The RFC has 0 lines about locking. The code has hundreds of lines for locking infrastructure alone.

### Memory Barriers

Even more invisible than locks: **memory barriers**.

Modern CPUs reorder memory operations for performance. On multi-core systems, one CPU might see writes from another CPU in a different order than they occurred. Memory barriers prevent this:

```c
/* Without memory barrier: */
vxlan->state = VXLAN_READY;   /* CPU might execute this BEFORE the line below */
vxlan->socket = new_socket;   /* ...even though we wrote this first */

/* With memory barrier: */
vxlan->socket = new_socket;
smp_wmb();                     /* "Write Memory Barrier" — all writes above */
                               /* are visible BEFORE writes below */
vxlan->state = VXLAN_READY;

/* Reader uses: */
if (vxlan->state == VXLAN_READY) {
    smp_rmb();                 /* "Read Memory Barrier" */
    use(vxlan->socket);        /* Guaranteed to see the socket write */
}
```

**RFC 7348: 0 lines about memory barriers.**  
**Linux VXLAN code: dozens of explicit barriers.**

---

## 8. Layer 5 — Performance and Optimization Infrastructure

### RFC Has No Performance Requirements

RFC 7348 describes VXLAN as a data center tunneling protocol. It says nothing about:
- Throughput targets
- Latency requirements
- CPU overhead limits
- How to achieve wire speed on a 100Gbps NIC

### NAPI (New API) — Interrupt Coalescing

**Concept:** When packets arrive at high rate, servicing each packet with a CPU interrupt wastes enormous overhead. NAPI batches packet processing:

```
WITHOUT NAPI (old interrupt-driven):
  Packet 1 arrives → INTERRUPT → CPU saves context → process packet → restore context
  Packet 2 arrives → INTERRUPT → CPU saves context → process packet → restore context
  ... (millions of times per second = context switch overhead dominates)

WITH NAPI (polling-based):
  Packets 1-64 arrive → ONE INTERRUPT → CPU enters poll loop → process 64 packets → sleep
  
  Interrupt overhead: divided by 64
```

RFC never mentions NAPI. But every high-performance network driver uses it, and VXLAN hooks into the NAPI infrastructure.

### GRO (Generic Receive Offload) and GSO (Generic Segmentation Offload)

**Concept:** Instead of processing thousands of small packets, combine them into fewer large packets before processing.

```
WITHOUT GRO:
  NIC receives 1000 x 1500-byte packets from one VXLAN tunnel
  → 1000 function calls through the network stack
  → 1000 × overhead

WITH GRO:
  NIC receives 1000 x 1500-byte packets
  GRO combines them: → 10 x 15000-byte "super packets"
  → 10 function calls through the network stack
  → 100x less overhead
  → Split back into 1000 packets at delivery point
```

The VXLAN code has specific GRO hooks (`vxlan_gro_receive`, `vxlan_gro_complete`) that are 100% absent from the RFC but account for hundreds of lines of code.

### GSO (Generic Segmentation Offload)

The reverse of GRO — on the transmit path, the kernel creates one large packet and lets the NIC segment it:

```c
/* RFC says: send a VXLAN packet */
/* Code must decide: */

if (skb_is_gso(skb)) {
    /* This packet was created as one large unit for efficiency */
    /* It will be segmented by hardware or software AFTER VXLAN encapsulation */
    /* We must set up the GSO metadata CORRECTLY or the hardware breaks it wrong */
    skb_shinfo(skb)->gso_type |= SKB_GSO_UDP_TUNNEL;
    /* Tell the hardware: "this is a VXLAN tunnel, the inner packet needs segmentation" */
    /* NOT just "segment this UDP packet" */
}
```

### XDP (eXpress Data Path)

**Concept:** Process packets at the NIC driver level, before they even enter the kernel's network stack. Allows near-hardware-speed packet processing.

```
PACKET PROCESSING PATHS:

  Wire
   │
   ▼
  NIC Hardware
   │
   ├──► XDP Hook ──► BPF program ──► DROP/REDIRECT/PASS
   │    (fastest, < 100ns per packet)
   │
   └──► Kernel Network Stack
            │
            ├──► NAPI poll
            │
            └──► GRO
                  │
                  └──► IP stack
                         │
                         └──► UDP socket
                                │
                                └──► VXLAN decode
                                       │
                                       └──► Inner Ethernet frame
                                              │
                                              └──► Delivered to VM/container
```

The VXLAN driver has XDP hooks. RFC: 0 lines. Code: hundreds of lines.

### Checksums and Hardware Offload

RFC: "Compute the UDP checksum."

Reality:
```
CHECKSUM DECISION TREE:

  Sending packet:
       │
       ├── NIC supports TX checksum offload?
       │       └── YES: Set CHECKSUM_PARTIAL flag
       │               Tell NIC where to compute checksum
       │               NIC computes in hardware (free)
       │
       └── NO: Compute checksum in software (expensive)
               Use optimized csum_partial() with SIMD if available
               
  But wait — this is a TUNNEL:
       Outer UDP checksum: calculated over outer UDP payload (= VXLAN header + inner frame)
       Inner frame may have its own checksum (TCP/UDP)
       
  Options:
  1. Outer checksum = 0 (RFC 7348 allows this, simpler)
  2. Outer checksum computed (required for IPv6 UDP)
  3. Inner checksum preserved, outer checksum computed
  4. Both checksums offloaded to hardware
  
  Each combination: different code path.
  4 combinations × (IPv4 + IPv6) = 8 distinct paths.
```

---

## 9. Layer 6 — Platform and OS Abstractions

### Byte Order (Endianness)

**Concept:** Different CPU architectures store multi-byte numbers differently.
- **Big-endian:** Most significant byte first (network byte order)
- **Little-endian:** Least significant byte first (x86, ARM in common mode)

RFC 7348 specifies VXLAN header fields in **network byte order** (big-endian). The CPU operates in **host byte order** (little-endian on x86). Every single field read requires conversion.

```
RFC says: "VNI is a 24-bit field in bits 8-31 of the second 32-bit word"

Reality on little-endian x86:

  Wire format (big-endian):    0x00 0x00 0x64 0x00    (VNI = 100 in byte 2-0 + reserved byte)
                               ^^^^                    
  If you just read this as a   0x00006400             (WRONG! Bytes are swapped)
  native 32-bit integer:
  
  Correct read:
    raw = be32_to_cpu(vxlan_hdr->vx_vni);   /* Convert network→host byte order */
    vni = raw >> 8;                          /* VNI is in bits 31-8 */
    
  Linux uses __be32 type annotation to make the compiler warn if you 
  accidentally do arithmetic on big-endian values without converting.
  sparse (a kernel static analysis tool) checks for this.
```

Every field in every header: explicit endian conversion. RFC: described in text. Code: hundreds of `be32_to_cpu`, `cpu_to_be32`, `htons`, `ntohs` calls.

### 32-bit vs 64-bit Pointer Sizes

The same code must work on 32-bit embedded systems and 64-bit servers:

```c
/* BAD (breaks on 32-bit): */
long ptr_value = (long)some_pointer;  /* long is 32-bit on 32-bit systems */

/* GOOD: */
unsigned long ptr_value = (unsigned long)some_pointer;  /* always pointer-sized */
/* OR use uintptr_t explicitly */
```

### NUMA (Non-Uniform Memory Access)

**Concept:** Modern servers have multiple CPU sockets. Each socket has its own local memory. Accessing remote memory (on another socket's memory bus) is 3x slower.

```
NUMA TOPOLOGY (2-socket server):

  Socket 0:                    Socket 1:
  ┌────────────────┐           ┌────────────────┐
  │ CPU 0-15       │           │ CPU 16-31      │
  │                │           │                │
  │ Local RAM      │◄──SLOW───►│ Local RAM      │
  │ (32 GB)        │  QPI link │ (32 GB)        │
  └────────────────┘           └────────────────┘

  Allocating memory for a VXLAN socket on CPU 1's NUMA node
  when CPU 0 processes packets = REMOTE memory access = SLOW
```

The VXLAN code uses `GFP_KERNEL | __GFP_THISNODE` or NUMA-aware allocation to keep data local to the CPU using it. RFC: 0 lines.

### Compiler Hints and Annotations

```c
/* RFC says nothing about this. Code must tell the compiler what's likely: */

if (likely(vxlan_dev_exists))    /* Branch predictor hint: this is the common case */
    process_packet();
else
    drop_and_count();

if (unlikely(packet_malformed))  /* Rarely happens */
    goto drop;

/* Attributes: */
static inline __always_inline void fast_path_function(...)  /* Force inline */
static noinline void slow_path(...)                          /* Never inline */
__attribute__((packed)) struct vxlan_hdr { ... }            /* No padding */
__attribute__((aligned(64))) struct hot_data { ... }        /* Cache aligned */
```

---

## 10. Layer 7 — Observability — Logging, Tracing, Metrics

### The RFC's Black Box

RFC 7348 describes the VXLAN protocol. It says nothing about:
- How do you know if it's working?
- How do you diagnose problems?
- How do you measure performance?
- How do you trace packet drops?

Production code implements a complete observability infrastructure.

### Statistics Counters

Every event that can go wrong has a counter:

```c
/* struct vxlan_stats — per-CPU statistics (no lock contention!) */
struct vxlan_stats {
    u64 tx_packets;           /* Packets sent */
    u64 tx_bytes;             /* Bytes sent */
    u64 rx_packets;           /* Packets received */
    u64 rx_bytes;             /* Bytes received */
    
    /* RFC-related drops: */
    u64 rx_drop_iflag;        /* VXLAN I-flag not set */
    u64 rx_drop_vni;          /* VNI not found */
    u64 rx_drop_skb;          /* skb allocation failed */
    
    /* Non-RFC drops (real world): */
    u64 rx_drop_too_short;    /* Packet shorter than VXLAN header */
    u64 rx_drop_no_socket;    /* Socket closed during receive */
    u64 rx_drop_no_space;     /* Receive queue full */
    u64 rx_errors;            /* Generic error counter */
    
    struct u64_stats_sync syncp;  /* 32-bit arch: prevent partial reads */
};

/* PER-CPU: each CPU increments its own counter — no atomic overhead */
/* Collection: sum all CPUs when user requests stats */
```

These counters are exposed via:
- `ip -s link show vxlan0` (netlink interface)
- `ethtool -S vxlan0` (ethtool statistics)
- `/sys/class/net/vxlan0/statistics/` (sysfs)

RFC: 0 lines. Production code: entire statistics subsystem.

### Netlink Events and Notifications

When an FDB entry is learned (added automatically), the kernel sends a notification:

```c
/* RFC 7348 §6: "A VTEP MAY learn source addresses" */
/* Code must notify all interested parties when learning happens */

vxlan_fdb_notify(vxlan, f, NULL, RTM_NEWNEIGH, swapped, extack);
/* This generates a netlink message:                         */
/* - Sent to all sockets subscribed to RTNLGRP_NEIGH         */
/* - Includes: VNI, MAC address, remote VTEP IP, aging time  */
/* - Used by: BGP daemons, SDN controllers, monitoring tools */
```

### ftrace Tracepoints

The kernel has a dynamic tracing infrastructure. VXLAN registers tracepoints:

```c
TRACE_EVENT(vxlan_fdb_create,
    TP_PROTO(const struct vxlan_dev *vxlan,
             const struct vxlan_fdb *f),
    TP_ARGS(vxlan, f),
    TP_STRUCT__entry(
        __field(u32, vni)
        __array(u8, eth_addr, ETH_ALEN)
        __field(__be32, dst)
    ),
    ...
);
```

A network engineer can dynamically enable this tracepoint (`echo 1 > /sys/kernel/debug/tracing/events/vxlan/vxlan_fdb_create/enable`) and see every FDB entry creation in real time — with zero overhead when disabled.

RFC: 0 lines. Code: entire tracing infrastructure.

### Dynamic Debug

```c
/* net_dbg_ratelimited — only logs if CONFIG_DYNAMIC_DEBUG is enabled */
/* AND the user has explicitly enabled debug for this module */
/* Zero overhead in production (compiled out) */

netdev_dbg(dev, "vxlan rcv: bad flags %#x\n", ntohl(vxlan->vx_flags));
```

---

## 11. Layer 8 — Configuration, Tunables, and Feature Flags

### RFC Has One Configuration: "Configure It"

RFC 7348 says a VTEP has a VNI and an IP address. Real production configuration:

```
VXLAN DEVICE CONFIGURATION (via 'ip link add'):

  ip link add vxlan0 type vxlan \
      id 100              \  # VNI = 100
      dev eth0            \  # Physical device to bind to
      remote 10.0.0.2     \  # Remote VTEP (unicast mode)
      local 10.0.0.1      \  # Local VTEP address
      dstport 4789        \  # UDP destination port
      srcport 1024 65535  \  # Source port range (for ECMP)
      nolearning          \  # Disable MAC learning (SDN mode)
      proxy               \  # Enable ARP proxy
      rsc                 \  # Route Short Circuit
      l2miss              \  # Generate L2 miss notifications
      l3miss              \  # Generate L3 miss notifications
      ageing 300          \  # FDB entry aging timeout (seconds)
      maxaddress 0        \  # Max FDB entries (0 = unlimited)
      gbp                 \  # Enable Group-Based Policy extension
      gpe                 \  # Enable Generic Protocol Extension
      udp6zerocsumtx      \  # Zero UDP checksum on TX for IPv6
      udp6zerocsumrx      \  # Accept zero checksum on RX for IPv6
      remcsumtx           \  # Remote checksum offload TX
      remcsumrx           \  # Remote checksum offload RX
      tos 0               \  # Outer IP TOS field
      ttl 64              \  # Outer IP TTL
      df set|unset|inherit\  # Don't Fragment bit handling
      flowlabel 0            # IPv6 flow label
```

Every one of these parameters:
1. Is parsed from netlink message
2. Validated (range checks, combination checks)
3. Stored in `struct vxlan_config`
4. Used in the data path with conditional branches
5. Readable back via `ip link show vxlan0`

RFC covers `id`, `remote`, `local`, `dstport`. Everything else: real-world requirements.

### Netlink Configuration Interface

**Concept:** Netlink is the kernel ↔ userspace communication channel for networking configuration. It is a binary socket protocol.

```
CONFIGURATION FLOW:

  User types: ip link add vxlan0 type vxlan id 100 ...
       │
       ▼
  iproute2 (ip tool)
       │ constructs netlink message
       │ RTM_NEWLINK + IFLA_VXLAN_* attributes
       ▼
  Kernel: rtnl_newlink()
       │
       ├── Find vxlan_link_ops (registered by vxlan module)
       │
       ├── vxlan_validate() — validate all attributes
       │       ├── Check IFLA_VXLAN_ID range (0 to 2^24-1)
       │       ├── Check IFLA_VXLAN_PORT range (1-65535)
       │       ├── Check conflicting options
       │       └── Return -EINVAL if anything wrong
       │
       ├── vxlan_newlink() — actually create the device
       │       ├── Allocate struct vxlan_dev
       │       ├── Parse all IFLA_VXLAN_* attributes
       │       ├── vxlan_dev_configure()
       │       └── register_netdevice()
       │
       └── Send RTM_NEWLINK notification to all listeners
```

The netlink parsing code alone is hundreds of lines. RFC: none.

---

## 12. Layer 9 — Backward Compatibility and Versioning

### The Permanent Compatibility Contract

**The Linux kernel's most sacred rule:** Never break userspace. Once an API is exported, it works forever.

This means:

```
BACKWARD COMPATIBILITY EXAMPLES IN VXLAN CODE:

  Feature Added in Kernel 3.7:  Basic VXLAN (VNI, unicast, multicast)
  Feature Added in Kernel 3.8:  IPv6 VTEP support
  Feature Added in Kernel 3.10: FDB aging, MAC learning
  Feature Added in Kernel 3.12: GRO support
  Feature Added in Kernel 3.14: UDP socket sharing between VTEPs
  Feature Added in Kernel 3.15: RX checksum offload
  Feature Added in Kernel 4.0:  Route Short Circuit (RSC)
  Feature Added in Kernel 4.1:  Group Based Policy (GBP) extension
  Feature Added in Kernel 4.4:  Generic Protocol Extension (GPE)
  Feature Added in Kernel 4.6:  PMTUD (Path MTU Discovery)
  ...
  
  Code in kernel 6.x STILL supports all of the above configurations.
  A script that configured VXLAN in 2013 still works on a 2024 kernel.
```

This means code paths for old configurations are permanently maintained. "Dead code" from the RFC perspective; critical code from the production perspective.

### Kernel Version Guards

```c
/* Code that only exists for backward compatibility */
#if KERNEL_VERSION(5, 0, 0) <= LINUX_VERSION_CODE
    /* New API available */
    err = dev_set_threaded(dev, true);
#else
    /* Old kernel: do it the old way */
    /* This code exists ONLY for old kernels */
    /* RFC: completely unaware of kernel version differences */
#endif
```

### ABI Stability

The `struct vxlan_config` structure that userspace sees through `/proc` or netlink can **never** have fields removed or reordered. New fields can only be added at the end.

---

## 13. Layer 10 — Security Hardening

### RFC Security Considerations = 1 Short Section

RFC 7348's Security Considerations section is ~1 page. It says:
- "VXLAN does not provide encryption"
- "Use IPsec for security"
- "VTEP should restrict traffic to known VNIs"

That is essentially the entire RFC security guidance.

### Production Security Code

```
SECURITY CONCERNS NOT IN RFC:

  1. NETWORK NAMESPACE ISOLATION
     ─────────────────────────────
     Linux namespaces: containers get their own network stack.
     A VXLAN device created in container namespace X MUST NOT
     be accessible from container namespace Y.
     
     Code: every operation checks current_net() and compares
     to the device's network namespace.
     
     Attack: container escape via VXLAN if this check is missing.

  2. CAPABILITY CHECKS
     ─────────────────────────────
     Creating a VXLAN device: requires CAP_NET_ADMIN
     Modifying FDB entries: requires CAP_NET_ADMIN
     Reading FDB entries: any user
     
     Code: explicit capable(CAP_NET_ADMIN) checks everywhere
     
     RFC says nothing about privilege levels.

  3. INPUT VALIDATION AGAINST MALICIOUS PACKETS
     ─────────────────────────────────────────────
     A remote attacker can send crafted VXLAN packets.
     
     Attack surface:
     - Packet with VNI that exists but wrong VTEP → information leak?
     - Packet with malformed inner Ethernet frame → parser crash?
     - Flood of packets with random VNIs → CPU exhaustion?
     - Packet with inner source MAC = existing FDB entry → FDB poisoning!
     
     Code: each attack vector has explicit defense.
     FDB learning: rate limited, configurable max entries.
     
  4. PRIVILEGE ESCALATION VIA MULTICAST
     ─────────────────────────────────────────────
     VXLAN multicast group joining requires:
     - Socket that can join multicast
     - ip_mcast_join() call
     - This touches the routing table
     
     Without proper namespace and capability checks:
     A process in a container could affect the host's multicast routing.
     
  5. INFORMATION LEAKAGE VIA ERROR MESSAGES
     ─────────────────────────────────────────────
     Error messages returned via netlink MUST NOT reveal:
     - Kernel addresses (KASLR bypass)
     - Other tenants' VNI existence
     - Internal state timing
```

---

## 14. Layer 11 — Integration with Existing Systems

### The RFC Describes a Protocol in Isolation

VXLAN RFC describes VXLAN as a standalone protocol. But in Linux, VXLAN is one component of a vast ecosystem:

```
LINUX NETWORKING ECOSYSTEM VXLAN MUST INTEGRATE WITH:

                    ┌─────────────────────────────────────┐
                    │         USERSPACE                   │
                    │  ip, bridge, tc, ovs, docker, k8s   │
                    └────────────────┬────────────────────┘
                                     │ netlink
                    ┌────────────────▼────────────────────┐
                    │  rtnetlink / generic netlink         │
                    └──────────────────┬──────────────────┘
                                       │
         ┌─────────────────────────────▼─────────────────────────────┐
         │                   NETWORK DEVICE LAYER                     │
         │               (net/core/dev.c — struct net_device)         │
         └──┬────────────┬────────────┬──────────────┬───────────────┘
            │            │            │              │
    ┌───────▼──┐  ┌──────▼────┐  ┌───▼──────┐  ┌───▼──────────────┐
    │ Netfilter│  │  Traffic  │  │ Bonding/ │  │  Bridging        │
    │ (iptables│  │  Control  │  │  LACP    │  │  (bridge.ko)     │
    │  nftables│  │  (tc/BPF) │  │          │  │  STP, FDB        │
    │  conntrack│  └──────┬────┘  └───┬──────┘  └───┬──────────────┘
    └───────┬──┘         │           │              │
            │            │           │              │
            └────────────┴─────┬─────┴──────────────┘
                               │
              ┌────────────────▼────────────────────┐
              │          VXLAN DRIVER               │
              │    (drivers/net/vxlan/vxlan*.c)     │
              └────────────────┬────────────────────┘
                               │
              ┌────────────────▼────────────────────┐
              │         UDP SOCKET LAYER            │
              │    (net/ipv4/udp.c, net/ipv6/udp.c) │
              └────────────────┬────────────────────┘
                               │
              ┌────────────────▼────────────────────┐
              │        IP ROUTING LAYER             │
              │  (net/ipv4/route.c — ECMP, policy)  │
              └────────────────┬────────────────────┘
                               │
              ┌────────────────▼────────────────────┐
              │        NIC DRIVER                   │
              └─────────────────────────────────────┘
```

**Each arrow is an integration point with its own API, conventions, and bugs.**

### Netfilter Integration

**Concept:** Netfilter is Linux's packet filtering framework (iptables lives on top of it). Packets passing through VXLAN must trigger Netfilter hooks.

```
PACKET FLOW WITH NETFILTER HOOKS:

  Packet arrives on physical NIC
       │
       ▼
  NF_INET_PRE_ROUTING hook        ◄── iptables PREROUTING rules apply here
       │                               (on the OUTER packet)
       ▼
  UDP receive → VXLAN decode
       │
       ▼
  Inner packet extracted
       │
       ▼
  NF_INET_PRE_ROUTING hook        ◄── iptables PREROUTING rules apply AGAIN
       │                               (on the INNER packet — different chain!)
       ▼
  Forward to inner device
       │
       ▼
  NF_INET_FORWARD hook            ◄── iptables FORWARD rules
       │
       ▼
  NF_INET_POST_ROUTING hook       ◄── iptables POSTROUTING (MASQUERADE etc.)
       │
       ▼
  VXLAN encapsulate
       │
       ▼
  NF_INET_POST_ROUTING hook       ◄── AGAIN on outer packet
       │
       ▼
  Physical NIC transmit
```

RFC: 0 lines about Netfilter. VXLAN code: explicit calls to `nf_reset_ct()`, careful handling of `skb->nf_bridge`, conntrack state preservation across encapsulation.

### Bridge Integration

VXLAN devices are commonly used as bridge ports:

```
TYPICAL DATA CENTER TOPOLOGY:

  VM1 (MAC: aa:bb) ──► br0 (Linux bridge) ──► vxlan100 ──► Wire
                         │
  VM2 (MAC: cc:dd) ──┘   └──► eth0 (local traffic)
```

The Linux bridge code calls VXLAN's `ndo_fdb_add`, `ndo_fdb_del`, `ndo_fdb_dump` operations. VXLAN must implement these `ndo_*` function pointers in `struct net_device_ops`. RFC: none.

### Traffic Control (tc) Integration

Linux `tc` (traffic control) can attach BPF programs, rate limiters, and classifiers to network devices. VXLAN must properly propagate:
- `skb->priority` (for QoS)
- `skb->mark` (for policy routing)
- `skb->tc_index` (for traffic control)

These fields are not in the RFC but are critical for production deployments.

---

## 15. Layer 12 — Testing Infrastructure Inside the Code

### Self-Tests Embedded in the Module

```c
/* CONFIG_VXLAN_SELFTESTS — kernel self-tests */
/* These are compiled into the kernel when enabled */
/* And run at module load time or via /sys/kernel/debug/selftest */

static int __init vxlan_selftest(void)
{
    /* Test 1: VNI encoding/decoding round trip */
    /* Test 2: FDB hash distribution */
    /* Test 3: Packet encapsulation format */
    /* Test 4: UDP source port selection (ECMP hash) */
    /* Test 5: GBP extension bits */
    /* Test 6: GPE next protocol field */
    ...
}
```

### Fault Injection Points

```c
/* KASAN (Kernel Address Sanitizer) compatibility */
/* Every allocation has metadata for KASAN to detect buffer overflows */
/* This is debug-mode only but affects code structure */

/* LOCKDEP — lock dependency validator */
/* Every lock acquisition is traced in debug builds */
/* Detects potential deadlocks at runtime */
/* Requires lock class annotations in code */

lockdep_set_class(&vxlan->hash_lock[i], &vxlan_netdev_addr_lock_key);
```

---

## 16. Layer 13 — Edge Cases, Corner Cases, and Undefined Behavior

### The RFC's Happy Path vs The World's Chaos

```
EDGE CASE CATALOG FOR VXLAN:

  ┌─────────────────────────────────────────────────────────────────┐
  │ EDGE CASES MENTIONED IN RFC 7348                                │
  ├─────────────────────────────────────────────────────────────────┤
  │ - Unknown VNI → drop                                            │
  │ - Reserved bits non-zero → implementation-specific behavior     │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │ EDGE CASES NOT IN RFC (found through production experience)     │
  ├─────────────────────────────────────────────────────────────────┤
  │ MTU CASES:                                                      │
  │ - Inner MTU = 9000 (jumbo), outer MTU = 1500 → MUST fragment   │
  │   or send ICMP "fragmentation needed" back                      │
  │ - Outer MTU unknown (tunnel to internet) → PMTUD               │
  │ - MTU changes during active connections → notify inner devices  │
  │ - MTU = 0 (interface not yet configured) → don't crash         │
  │                                                                 │
  │ FDB CASES:                                                      │
  │ - FDB entry for broadcast MAC (ff:ff:ff:ff:ff:ff)              │
  │ - FDB entry for multicast MAC (01:xx:xx:xx:xx:xx)              │
  │ - Source MAC = 00:00:00:00:00:00 (null MAC — don't learn)      │
  │ - FDB table full → drop new entries? evict old? notify?        │
  │ - Two VTEPs claim same MAC in different VNIs → OK (isolated)   │
  │ - Two VTEPs claim same MAC in SAME VNI → FDB conflict          │
  │                                                                 │
  │ TUNNEL CASES:                                                   │
  │ - VXLAN inside VXLAN (recursive tunneling) → TTL prevents loop │
  │ - VXLAN packet arrives on wrong UDP port                       │
  │ - VXLAN packet from same VTEP as self (hairpin) → drop?        │
  │ - Outer IP TTL expires in transit → ICMP Time Exceeded         │
  │ - Outer IP DF bit + MTU exceeded → ICMP Frag Needed            │
  │                                                                 │
  │ NETWORKING PROTOCOL CASES:                                      │
  │ - ARP over VXLAN (needs special handling for proxy ARP)        │
  │ - IPv6 Neighbor Discovery over VXLAN                           │
  │ - IGMP (multicast group management) over VXLAN                 │
  │ - STP (Spanning Tree Protocol) BPDUs — should they pass?       │
  │ - LACP (Link Aggregation) PDUs — should they pass?             │
  │                                                                 │
  │ SYSTEM CASES:                                                   │
  │ - Network namespace deletion while VXLAN device exists         │
  │ - Physical NIC removed (hotplug) while VXLAN tunnel active     │
  │ - System suspend/resume with active VXLAN tunnels              │
  │ - Memory pressure: kmalloc fails for FDB entry                 │
  │ - CPU hotplug: CPU added/removed while VXLAN active           │
  │ - Kernel module unload while packets are in flight             │
  └─────────────────────────────────────────────────────────────────┘
```

Each edge case in the second box is typically 10-50 lines of code. There are 30+ such cases. That's 300-1500 lines for **edge cases alone**.

---

## 17. VXLAN RFC 7348 vs Linux Kernel: A Deep Case Study

### Where the 12,000 Lines Come From

Let's map RFC 7348's sections to code files and estimate line counts:

```
RFC 7348 STRUCTURE vs LINUX KERNEL CODE:

  RFC Section                  Lines in RFC    Code File(s)                  Approx Lines
  ─────────────────────────────────────────────────────────────────────────────────────────
  §1 Introduction                   40          vxlan_core.c comments             100
  §2 VXLAN Header Format            30          vxlan.h (vxlanhdr struct)          20
  §3 Inner Frame                    20          vxlan_rcv(), inner eth parse       200
  §4 VTEP and VNI concepts          80          struct vxlan_dev, vxlan_config    400
  §5 VXLAN Packet Format            50          vxlan_xmit(), vxlan_build_skb()   500
  §6 VXLAN Deployment               80          (config/management)              1000
  §6.1 Unicast mode                 30          vxlan_xmit_one() unicast path     300
  §6.2 Multicast mode               40          vxlan_multicast_join/leave()      400
  §7 Inner Frame MAC learning       30          vxlan_fdb_learn()                 300
  §8 Security Considerations        60          (distributed throughout)          600
  §9 IANA Considerations            20          (UDP port 4789 hardcoded)          10
  ─────────────────────────────────────────────────────────────────────────────────────────
  RFC Total: ~480 lines of normative text
  
  ADDITIONAL CODE NOT MAPPED TO RFC SECTIONS:
  
  Error handling                                                                  800
  Memory management / slab caches                                                 300
  Locking (RCU, spinlocks, barriers)                                             600
  Statistics and counters                                                         400
  Netlink interface (parse/build all 40+ attributes)                            1200
  GRO / GSO / checksum offload                                                   600
  XDP integration                                                                 400
  Netfilter hooks                                                                 200
  Bridge integration (ndo_fdb_* ops)                                             400
  IPv6 VTEP support                                                               500
  GBP extension (RFC 8926)                                                        300
  GPE extension (draft)                                                           300
  PMTUD (Path MTU Discovery)                                                      300
  ECMP (source port selection)                                                    200
  ARP/ND proxy                                                                    300
  FDB aging / garbage collection                                                  300
  Namespace handling                                                              300
  Security / capability checks                                                    200
  Debug/tracing/selftests                                                         400
  Backward compatibility shims                                                    300
  Platform abstraction (endian, NUMA)                                             200
  Miscellaneous kernel integration                                                600
  ─────────────────────────────────────────────────────────────────────────────────────────
  TOTAL                                                                         ~12,000
```

### The Actual Linux VXLAN File Structure

```
drivers/net/vxlan/
├── vxlan_core.c       (~4000 lines) — Main: init, xmit, rcv, FDB, socket mgmt
├── vxlan.h            (~500 lines)  — Structures, constants, function prototypes
├── vxlan_private.h    (~200 lines)  — Internal structures, not exported
├── vxlan_vnifilter.c  (~600 lines)  — VNI filter (per-VNI statistics, filtering)
├── vxlan_mdb.c        (~800 lines)  — Multicast Database (IGMP snooping for VXLAN)
└── Makefile           (~10 lines)

net/ipv4/udp_tunnel.c  (~400 lines)  — Shared UDP tunnel infrastructure
net/core/fib_rules.c   (VXLAN uses this for route lookup)
```

**But wait — it's not just these files.** VXLAN touches:
- `net/ipv4/route.c` — route lookup calls
- `net/ipv6/route.c` — IPv6 route lookup
- `net/core/dev.c` — `register_netdevice`
- `net/bridge/br_vlan.c` — bridge integration
- `net/sched/` — traffic control
- `net/netfilter/` — packet filtering
- `include/linux/vxlan.h` — exported header used by other modules

The **real** code footprint is closer to 20,000 lines if you count all touched infrastructure.

### A Single RFC Sentence Exploded Into Code

Let's take RFC 7348, Section 4.1:
> "A VTEP MUST NOT forward VXLAN packets to a destination address for which it has not received forwarding information."

```c
/*
 * This one sentence requires ALL of this code:
 */

/* Step 1: Look up forwarding information */
static struct vxlan_rdst *vxlan_fdb_find_rdst(struct vxlan_fdb *f,
                                               union vxlan_addr *addr, __be16 port,
                                               __be32 vni, __u32 ifindex)
{
    struct vxlan_rdst *rd;

    list_for_each_entry(rd, &f->remotes, list) {
        if (vxlan_addr_equal(&rd->remote_ip, addr) &&
            rd->remote_port == port &&
            rd->remote_vni == vni &&
            rd->remote_ifindex == ifindex)
            return rd;
    }
    return NULL;
}

/* Step 2: The actual "MUST NOT forward" logic in xmit path */
static netdev_tx_t vxlan_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct vxlan_dev *vxlan = netdev_priv(dev);
    struct ethhdr *eth;
    struct vxlan_fdb *f;
    struct vxlan_rdst *rdst;

    eth = eth_hdr(skb);

    /* Look up FDB */
    f = vxlan_find_mac(vxlan, eth->h_dest, vxlan->default_dst.remote_vni);
    if (f == NULL) {
        /* "MUST NOT forward" — but HOW to not forward? */
        /* Option 1: Drop (unicast mode, no flooding) */
        /* Option 2: Flood to all known VTEPs (default mode) */
        /* Option 3: Generate L2 miss notification (SDN mode) */
        
        if (vxlan->cfg.flags & VXLAN_F_L2MISS) {
            /* SDN mode: notify controller, drop for now */
            vxlan_fdb_miss(vxlan, eth->h_dest);
            /* Controller will install FDB entry later */
            goto drop;
        }
        
        if (vxlan->cfg.flags & VXLAN_F_PROXY) {
            /* Try ARP proxy before dropping */
            if (vxlan_arp_reply(vxlan, skb))
                goto drop;
        }
        
        /* Flood to all remote VTEPs (if flooding enabled) */
        f = vxlan_find_mac(vxlan, all_zeros_mac, 
                           vxlan->default_dst.remote_vni);
        if (f == NULL) {
            /* No flooding entry either — genuinely drop */
            dev->stats.tx_dropped++;
            goto drop;
        }
    }
    
    /* Forward to all destinations in the FDB entry */
    list_for_each_entry_rcu(rdst, &f->remotes, list) {
        struct sk_buff *skb1;
        
        if (!fdst && (dst_flags & VXLAN_F_REDIR)) /* redirect case */
            continue;

        if (rdst == first_rdst)
            skb1 = skb;   /* Use original for last destination */
        else
            skb1 = skb_clone(skb, GFP_ATOMIC); /* Clone for each dest */
        
        if (skb1)
            vxlan_xmit_one(skb1, dev, vni, rdst, did_rsc);
    }
    
    /* ... */

drop:
    dev_kfree_skb(skb);
    return NETDEV_TX_OK;
}
```

One RFC sentence → ~80 lines of code with 6 different code paths.

---

## 18. The Code Growth Equation

Here is the mathematical model for why RFC lines × N = Code lines:

```
CODE SIZE EXPANSION FACTORS:

  Let RFC_lines = lines of normative RFC text (call it R)

  Code = R × (happy_path_factor)
           × (error_handling_factor)
           × (concurrency_factor)
           × (platform_factor)
           × (observability_factor)
           × (configuration_factor)
           × (compatibility_factor)
           × (security_factor)
           × (integration_factor)
           × (edge_case_factor)

  Typical values for a kernel networking driver:
  
    happy_path_factor       = 3  (translate abstract to concrete)
    error_handling_factor   = 3  (every operation can fail multiple ways)
    concurrency_factor      = 2  (locks, RCU, atomics, barriers)
    platform_factor         = 1.5 (endian, 32/64, NUMA)
    observability_factor    = 2  (stats, logs, tracepoints, proc)
    configuration_factor    = 3  (netlink, sysctl, validate, document)
    compatibility_factor    = 1.5 (old kernels, extensions)
    security_factor         = 1.5 (namespaces, capabilities, input validation)
    integration_factor      = 2  (bridge, netfilter, tc, routing)
    edge_case_factor        = 1.5 (all the "impossible" things that happen)

  Multiplied together:
    3 × 3 × 2 × 1.5 × 2 × 3 × 1.5 × 1.5 × 2 × 1.5 ≈ 729

  VXLAN RFC normative text: ~480 lines
  480 × 729 = 350,000 — too high
  
  (Many factors apply to the SAME lines, and code is modular — 
   but this explains the ORDER OF MAGNITUDE gap.)

  A simpler model:
  
  For every CONCEPT in the RFC:
    - Define its data structure:           ×3
    - Initialize and destroy it:           ×2  
    - Validate all inputs to it:           ×2
    - Handle all errors involving it:      ×3
    - Lock it for concurrent access:       ×1.5
    - Make it configurable:                ×2
    - Make it observable (stats/logs):     ×2
    - Integrate with the OS:               ×2
    - Handle edge cases:                   ×1.5
    ─────────────────────────────────────────
    Total: ×3×2×2×3×1.5×2×2×2×1.5 = 648
```

---

## 19. Mental Models for Thinking Like a Systems Programmer

### Mental Model 1: The "What If" Expansion

When you read any specification sentence, expand it with these questions:

```
FOR EVERY STATEMENT IN THE RFC, ASK:

  "WHAT IF..."
  ├── ...the memory allocation fails?
  ├── ...another thread modifies this data right now?
  ├── ...this is called from interrupt context?
  ├── ...the caller passes NULL?
  ├── ...the value is 0, INT_MAX, or INT_MIN?
  ├── ...the network interface goes down mid-operation?
  ├── ...we're in a different network namespace?
  ├── ...the user has no privileges?
  ├── ...we're running on a big-endian MIPS CPU?
  ├── ...we're running on a 32-bit embedded system?
  ├── ...the system is running out of memory?
  ├── ...this code runs 10 million times per second?
  └── ...we need to debug why this doesn't work?
```

### Mental Model 2: The Three Domains of Code

```
EVERY LINE OF CODE BELONGS TO ONE DOMAIN:

  ┌─────────────────────────────────────────────────────────────────┐
  │  DOMAIN 1: PROTOCOL LOGIC                                       │
  │  "What does the RFC say we must do?"                            │
  │  ~10% of production code                                        │
  │  Example: Parse VNI field, look up FDB, encapsulate            │
  └─────────────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────────────┐
  │  DOMAIN 2: EXECUTION ENVIRONMENT MANAGEMENT                     │
  │  "How do we do it on THIS system, correctly and safely?"        │
  │  ~60% of production code                                        │
  │  Example: Locks, memory management, endian conversions,         │
  │           error handling, OS integration                        │
  └─────────────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────────────┐
  │  DOMAIN 3: OPERATIONAL EXCELLENCE                               │
  │  "How do humans manage and observe this in production?"         │
  │  ~30% of production code                                        │
  │  Example: Configuration interface, statistics, logging,         │
  │           debugging hooks, backward compatibility               │
  └─────────────────────────────────────────────────────────────────┘
```

When reading production code, mentally label every function: which domain is it in?

### Mental Model 3: The Hostile Dual Reader

Your code has two readers with opposite goals:

```
  FRIENDLY READER (the happy path):
  "Here comes a well-formed VXLAN packet from a legitimate VTEP.
   Process it quickly and correctly."

  HOSTILE READER (the adversary):
  "What if I send a packet with VNI = 0xFFFFFF?
   What if I send 1 million packets per second?
   What if I send a VXLAN packet that contains another VXLAN packet?
   What if I configure two VXLAN devices with the same VNI?"

  Production code must satisfy BOTH readers simultaneously.
```

### Mental Model 4: The Five Abstraction Levels

```
LEVEL 5: APPLICATION
  "I want to connect container A to container B"
  
LEVEL 4: PROTOCOL (RFC)
  "Encapsulate Ethernet frame in VXLAN/UDP/IP"
  
LEVEL 3: OS (WHAT CODE IMPLEMENTS)
  "Create socket, bind, add FDB entry, configure encapsulation"
  
LEVEL 2: KERNEL SUBSYSTEM
  "Register net_device, implement ndo_ops, integrate with netfilter"
  
LEVEL 1: HARDWARE
  "Program NIC's offload engine, handle DMA, manage IRQs"
  
The RFC describes Level 4.
Production code implements Level 3 and connects to Levels 2 and 1.
```

### Mental Model 5: Chunking the Code (Cognitive Science)

When you look at a 12,000-line file, **chunk** it by function, not by line:

```
VXLAN CORE CHUNKS:
  
  CHUNK A: Initialization / Teardown
    vxlan_init_net(), vxlan_exit_net()
    vxlan_newlink(), vxlan_dellink()
    vxlan_dev_alloc(), vxlan_dev_free()
    
  CHUNK B: Data Path (hot, performance-critical)
    vxlan_xmit() — transmit
    vxlan_rcv()  — receive
    vxlan_xmit_one() — send one packet to one destination
    
  CHUNK C: Forwarding Database (FDB)
    vxlan_fdb_find()
    vxlan_fdb_add() / vxlan_fdb_del()
    vxlan_fdb_learn()
    vxlan_fdb_age_event() — garbage collection
    
  CHUNK D: Socket Management
    vxlan_sock_add() / vxlan_sock_release()
    vxlan_open() / vxlan_stop()
    
  CHUNK E: Configuration Interface
    vxlan_fill_metadata_dst()
    vxlan_changelink()
    vxlan_get_size() / vxlan_fill_info()
    
  CHUNK F: Extensions
    vxlan_gbp_*()  — Group Based Policy
    vxlan_gpe_*()  — Generic Protocol Extension

  Once you know the chunks, you can navigate 12,000 lines
  as if it were 6 x 2000-line files.
```

### Mental Model 6: The Iceberg of Correctness

```
           ┌─────────────────────────────────────────────┐
           │         VISIBLE BEHAVIOR (RFC)              │
           │   Packet in → Correct behavior out          │
           │            10% of code                      │
           └─────────────────────────────────────────────┘
                              │
                              │
          ═══════════════════ WATER LINE ══════════════════
                              │
                              │
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │                    INVISIBLE CORRECTNESS                        │
    │                     (Not in RFC)                               │
    │                     90% of code                                │
    │                                                                 │
    │  Memory safety          Thread safety         Error recovery    │
    │  Resource management    Platform portability  Performance       │
    │  Security hardening     Observability         Configuration     │
    │  Integration correctness  Backward compat     Edge cases        │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
```

**The RFC describes only the tip of the iceberg. Production code must implement the entire iceberg.**

---

## 20. Summary Table: RFC Says vs Code Does

```
╔══════════════════════════════╦═══════════════════════════════════════════════════════════════╗
║  RFC SAYS                    ║  CODE DOES (All the "extra")                                  ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "VXLAN header has VNI field" ║ Define struct with __be32, endian conversion, bit extraction  ║
║                              ║ with shifts, validation that VNI < 2^24, special handling    ║
║                              ║ of VNI=0, slab cache for VNI data structures                 ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Look up the FDB"            ║ Hash table with per-bucket spinlocks, RCU read path, aging   ║
║                              ║ timer, max size limit, eviction policy, notification on miss  ║
║                              ║ (L2MISS), per-CPU stats for lookups/misses/hits              ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Encapsulate the packet"     ║ skb headroom check, realloc if needed, endian conversion of  ║
║                              ║ all header fields, checksum calculation or offload, GSO meta  ║
║                              ║ data update, DSCP/TOS inheritance, TTL setting, DF bit       ║
║                              ║ handling, IPv4/IPv6 outer header selection                   ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Send to VTEP"               ║ Route lookup for VTEP IP, source IP selection, UDP socket    ║
║                              ║ selection, source port hash for ECMP, NUMA-aware socket      ║
║                              ║ selection, send buffer full handling, ICMP error processing  ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Learn source MAC"           ║ Rate limit learning, check for existing entry (update vs     ║
║                              ║ create), notify bridge via netlink RTM_NEWNEIGH, update      ║
║                              ║ aging timer, enforce max FDB size, generate notification     ║
║                              ║ event via VXLAN_F_LEARN flag check                          ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Drop invalid packets"       ║ Increment one of 15 specific drop counters, rate-limited     ║
║                              ║ log message, free skb (kfree_skb with drop reason), update  ║
║                              ║ netdev stats, potentially trace via tracepoint              ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Support multicast mode"     ║ Join IGMP group, handle group membership changes, process    ║
║                              ║ IGMP queries, age out unused groups, handle multicast         ║
║                              ║ routing table changes, IPv6 MLD support                      ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "Configure VNI"              ║ Parse IFLA_VXLAN_ID netlink attribute, validate range,       ║
║                              ║ check for VNI conflict with existing devices, store in       ║
║                              ║ cfg struct, expose via rtnetlink, validate in changelink,    ║
║                              ║ document in rtnl_link_ops.policy array                      ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ "UDP destination port 4789"  ║ Default value, but configurable via IFLA_VXLAN_PORT, validate║
║                              ║ range 1-65535, IANA port 4789 as default, socket binding,   ║
║                              ║ port matching in recv path, multiple VTEPs per port possible ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ (nothing about performance)  ║ GRO callbacks, GSO segmentation, XDP hooks, NAPI batching,  ║
║                              ║ per-CPU statistics (no lock), hot/cold struct layout,        ║
║                              ║ likely/unlikely branch hints, RCU for FDB reads             ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ (nothing about monitoring)   ║ ethtool statistics (40+ counters), /proc/net/vxlan, sysfs   ║
║                              ║ attributes, ftrace tracepoints, netlink notifications,       ║
║                              ║ dynamic debug messages, RTNL link info dump                 ║
╠══════════════════════════════╬═══════════════════════════════════════════════════════════════╣
║ (nothing about security)     ║ CAP_NET_ADMIN checks, network namespace isolation, input     ║
║                              ║ validation for all netlink attributes, FDB entry rate        ║
║                              ║ limiting, max address enforcement                           ║
╚══════════════════════════════╩═══════════════════════════════════════════════════════════════╝
```

---

## Conclusion: The Real Nature of the Gap

The gap between RFC and production code is not a failure of RFCs or an excess in code. It is a **fundamental translation gap** between two different modes of describing a system:

```
RFC MODE:                              CODE MODE:
─────────────────────────────────────────────────────────────────
Describes WHAT                         Implements HOW
Assumes cooperative actors             Assumes hostile universe
Timeless (no hardware)                 Real-time on real hardware
Happy path focused                     All paths handled
Abstract data model                    Concrete memory layout
Sequential description                 Concurrent execution
High-level concepts                    Machine-level operations
Platform-independent                   Platform-specific
No resource constraints                Finite CPU, memory, bandwidth
No operational concerns                Full observability required
No security model                      Hardened against adversaries
No integration context                 Embedded in complex ecosystem
```

The **best systems programmers** hold both worlds in their head simultaneously. They can read an RFC and immediately visualize:
1. The happy-path code (10% of the work)
2. The execution environment challenges (60% of the work)
3. The operational requirements (30% of the work)

That is the meta-skill — the ability to translate between the specification universe and the production universe. It is built by reading production code alongside RFCs, understanding why every "extra" line exists, and internalizing the patterns until they become instinct.

When you look at 12,000 lines of VXLAN code and an RFC, the question is not "why is there so much code?" The question is: **"for each block of code, which production reality is it responding to, and why did the RFC not need to address it?"**

Answer that question for every file you read, and you will develop a systems programmer's intuition.

---

*Document compiled from analysis of: RFC 7348 (VXLAN), Linux kernel drivers/net/vxlan/, net/ipv4/udp_tunnel.c, kernel coding-style.rst, and production networking experience.*

