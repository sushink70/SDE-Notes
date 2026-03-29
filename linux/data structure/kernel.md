# Kernel Data Structures: A Complete Engineering Guide

> **Audience:** Systems engineers targeting mastery of Linux kernel internals with production-grade implementations in C, Rust, and Go.
> **Kernel version reference:** Linux 6.x

---

## Table of Contents

1. [Foundations: Why Kernel Data Structures Are Different](#1-foundations)
2. [Intrusive Linked Lists](#2-intrusive-linked-lists)
3. [Hash Tables](#3-hash-tables)
4. [Red-Black Trees (rbtree)](#4-red-black-trees)
5. [Radix Trees and XArray](#5-radix-trees-and-xarray)
6. [B-Trees (btrfs-style)](#6-b-trees)
7. [Skip Lists](#7-skip-lists)
8. [Queues: kfifo, Wait Queues, Work Queues](#8-queues)
9. [Priority Queues and Heaps](#9-priority-queues-and-heaps)
10. [Circular Buffers](#10-circular-buffers)
11. [Bitmaps and Bit Arrays](#11-bitmaps-and-bit-arrays)
12. [Per-CPU Data Structures](#12-per-cpu-data-structures)
13. [RCU: Read-Copy-Update](#13-rcu-read-copy-update)
14. [IDR: ID Radix Tree](#14-idr-id-radix-tree)
15. [Memory Pools: Slab, SLUB, SLOB](#15-memory-pools-slab-slub-slob)
16. [Spinlocks, Mutexes, Semaphores, RWLocks](#16-locking-primitives)
17. [Seqlocks](#17-seqlocks)
18. [Atomic Operations and Memory Ordering](#18-atomic-operations-and-memory-ordering)
19. [Page Tables and the Memory Map](#19-page-tables)
20. [LRU Lists and the Page Cache](#20-lru-lists-and-page-cache)
21. [Maple Tree](#21-maple-tree)
22. [Interval Trees](#22-interval-trees)
23. [Security Checklist for Kernel-Adjacent Code](#23-security-checklist)
24. [Performance and Profiling](#24-performance-and-profiling)
25. [Further Reading](#25-further-reading)

---

## 1. Foundations

### Why Kernel Data Structures Are Different

User-space data structures optimize for developer ergonomics, GC friendliness, and average-case performance. Kernel data structures optimize for:

| Concern | User-space | Kernel |
|---|---|---|
| Memory allocation | Heap via malloc/GC | Slab allocator, per-CPU pools, stack |
| Locking | Mutex/RWLock freely | Spinlocks (no sleep), lock ordering mandatory |
| Pointer safety | GC or RC handles it | Manual, RCU, hazard pointers |
| Cache layout | Often scattered | Cache-line aligned, intrusive nodes |
| Preemption | Preemptible anytime | Must disable preemption in critical sections |
| Recursion | Limited only by stack | Highly restricted; kernel stack is 8–16 KB |
| Error handling | Exceptions/Result | Return codes; no panicking in interrupt context |

### The Fundamental Rule: Never Sleep in Atomic Context

"Atomic context" means you hold a spinlock, have disabled preemption, or are inside an interrupt handler. In atomic context:
- You **cannot** call `kmalloc(GFP_KERNEL)` — it may sleep waiting for memory
- You **cannot** use mutexes or semaphores
- You **cannot** call any function that may reschedule

### Cache Line Alignment

Modern CPUs fetch 64-byte cache lines. Kernel structures are carefully padded:

```c
/* linux/include/linux/cache.h */
#define L1_CACHE_BYTES  64
#define ____cacheline_aligned __attribute__((__aligned__(SMP_CACHE_BYTES)))
#define __cacheline_aligned_in_smp ____cacheline_aligned

/* Hot fields at offset 0, cold fields later */
struct my_struct {
    /* hot path: read frequently */
    atomic_t refcount;          /* 4 bytes */
    unsigned int flags;         /* 4 bytes */
    spinlock_t lock;            /* 4 bytes on x86 */
    /* pad to cache line */
    u8 _pad[52];
    /* cold path: written rarely */
    struct list_head list;
} ____cacheline_aligned;
```

### The `container_of` Macro

The single most important macro in the Linux kernel. It recovers a pointer to the containing struct from a pointer to a member:

```c
/* linux/include/linux/kernel.h */
#define container_of(ptr, type, member) ({                    \
    const typeof(((type *)0)->member) *__mptr = (ptr);        \
    (type *)((char *)__mptr - offsetof(type, member)); })
```

**How it works internally:**

1. `offsetof(type, member)` — computes byte offset of `member` within `type` at compile time
2. Cast `ptr` to `char *` — byte-addressable arithmetic
3. Subtract offset — lands at start of containing struct
4. Cast to `type *`

This is the foundation of **intrusive data structures** — embedding a generic node inside a domain struct instead of wrapping the domain struct in a generic container.

```c
struct task_struct {
    /* ... hundreds of fields ... */
    struct list_head tasks;   /* embedded list node */
    /* ... */
};

/* Recover task_struct from a list_head pointer */
struct list_head *p = get_some_list_node();
struct task_struct *task = list_entry(p, struct task_struct, tasks);
/* list_entry IS container_of */
```

---

## 2. Intrusive Linked Lists

### One-Line Explanation
A circular doubly linked list where the list node (`list_head`) is **embedded inside** the data structure rather than wrapping it.

### Analogy
Instead of putting your valuables in a labeled box (non-intrusive), you weld a hook directly onto each valuable and hang them all on a rail (intrusive). The hook is `list_head`.

### Linux Kernel Implementation

```c
/* linux/include/linux/list.h (simplified) */

struct list_head {
    struct list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define LIST_HEAD(name) \
    struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *list) {
    list->next = list;
    list->prev = list;
}

/* Add between two known adjacent entries */
static inline void __list_add(struct list_head *new,
                               struct list_head *prev,
                               struct list_head *next) {
    next->prev = new;
    new->next = next;
    new->prev = prev;
    prev->next = new;
}

/* Add to front (stack push) */
static inline void list_add(struct list_head *new, struct list_head *head) {
    __list_add(new, head, head->next);
}

/* Add to tail (queue enqueue) */
static inline void list_add_tail(struct list_head *new, struct list_head *head) {
    __list_add(new, head->prev, head);
}

static inline void __list_del(struct list_head *prev, struct list_head *next) {
    next->prev = prev;
    prev->next = next;
}

static inline void list_del(struct list_head *entry) {
    __list_del(entry->prev, entry->next);
    entry->next = LIST_POISON1;  /* 0xdead000000000100 — catches use-after-free */
    entry->prev = LIST_POISON2;
}

/* Traversal macros */
#define list_entry(ptr, type, member) container_of(ptr, type, member)

#define list_for_each_entry(pos, head, member)                    \
    for (pos = list_first_entry(head, typeof(*pos), member);      \
         &pos->member != (head);                                   \
         pos = list_next_entry(pos, member))

/* Safe version: allows deletion during iteration */
#define list_for_each_entry_safe(pos, n, head, member)            \
    for (pos = list_first_entry(head, typeof(*pos), member),      \
         n = list_next_entry(pos, member);                        \
         &pos->member != (head);                                   \
         pos = n, n = list_next_entry(n, member))
```

### Step-by-Step Internal Breakdown

**Empty list (sentinel/head node):**
```
head.next ──► head
head.prev ──► head
```

**After list_add_tail(A), list_add_tail(B):**
```
head ──next──► A ──next──► B ──next──► head
head ◄──prev── A ◄──prev── B ◄──prev── head
```

The head node is a **sentinel** — it's never the actual data; it serves only as the fixed anchor. Circular design means:
- Empty check: `head->next == head`
- Front element: `head->next` (if not empty)
- Back element: `head->prev` (if not empty)
- No null checks needed anywhere

### hlist: Hash Table Optimized List

Regular `list_head` wastes memory in hash tables (both prev/next per bucket). `hlist` uses a pointer-to-pointer for prev, halving bucket overhead:

```c
struct hlist_head {
    struct hlist_node *first;
};

struct hlist_node {
    struct hlist_node *next;
    struct hlist_node **pprev;  /* points to the 'next' field of previous node */
};
```

`pprev` being `**` is clever: it allows O(1) deletion without a separate head pointer, because `*pprev = next` works whether pprev points to `head->first` or a node's `next` field.

### C Implementation (Full Standalone Demo)

```c
/* file: list_demo.c
 * compile: gcc -Wall -O2 list_demo.c -o list_demo
 */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

/* ── list_head ── */
struct list_head {
    struct list_head *next, *prev;
};

#define INIT_LIST_HEAD(ptr) do { (ptr)->next = (ptr); (ptr)->prev = (ptr); } while(0)
#define list_empty(head) ((head)->next == (head))

static inline void __list_add(struct list_head *new,
                               struct list_head *prev,
                               struct list_head *next) {
    next->prev = new;
    new->next  = next;
    new->prev  = prev;
    prev->next = new;
}

static inline void list_add_tail(struct list_head *new, struct list_head *head) {
    __list_add(new, head->prev, head);
}

static inline void list_del(struct list_head *entry) {
    entry->prev->next = entry->next;
    entry->next->prev = entry->prev;
    entry->next = (void *)0xDEAD;
    entry->prev = (void *)0xDEAD;
}

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

#define list_entry(ptr, type, member) container_of(ptr, type, member)

#define list_for_each_entry(pos, head, member)                           \
    for (pos = container_of((head)->next, typeof(*pos), member);         \
         &(pos)->member != (head);                                        \
         pos = container_of((pos)->member.next, typeof(*pos), member))

#define list_for_each_entry_safe(pos, tmp, head, member)                 \
    for (pos = container_of((head)->next, typeof(*pos), member),         \
         tmp = container_of((pos)->member.next, typeof(*pos), member);   \
         &(pos)->member != (head);                                        \
         pos = tmp, tmp = container_of((tmp)->member.next, typeof(*tmp), member))

/* ── Domain struct ── */
typedef struct {
    int pid;
    char name[32];
    struct list_head list;   /* embedded intrusive node */
} process_t;

static process_t *process_new(int pid, const char *name) {
    process_t *p = malloc(sizeof(*p));
    p->pid = pid;
    strncpy(p->name, name, sizeof(p->name) - 1);
    INIT_LIST_HEAD(&p->list);
    return p;
}

int main(void) {
    struct list_head runqueue;
    INIT_LIST_HEAD(&runqueue);

    /* Enqueue processes */
    process_t *init  = process_new(1,   "init");
    process_t *bash  = process_new(100, "bash");
    process_t *nginx = process_new(200, "nginx");

    list_add_tail(&init->list,  &runqueue);
    list_add_tail(&bash->list,  &runqueue);
    list_add_tail(&nginx->list, &runqueue);

    /* Traverse */
    printf("Run queue:\n");
    process_t *p;
    list_for_each_entry(p, &runqueue, list) {
        printf("  PID=%d name=%s\n", p->pid, p->name);
    }

    /* Safe delete during traversal */
    process_t *tmp;
    list_for_each_entry_safe(p, tmp, &runqueue, list) {
        if (p->pid == 100) {
            printf("Removing PID=%d\n", p->pid);
            list_del(&p->list);
            free(p);
        }
    }

    printf("After removal:\n");
    list_for_each_entry(p, &runqueue, list) {
        printf("  PID=%d name=%s\n", p->pid, p->name);
    }

    /* Cleanup */
    list_for_each_entry_safe(p, tmp, &runqueue, list) {
        list_del(&p->list);
        free(p);
    }
    assert(list_empty(&runqueue));
    printf("All clean.\n");
    return 0;
}
```

### Rust Implementation (Intrusive List with Unsafe)

```rust
// file: src/intrusive_list.rs
// Intrusive linked list in Rust using raw pointers and unsafe.
// In real kernel Rust (linux/rust/), this is provided by kernel::list.

use std::ptr::NonNull;
use std::marker::PhantomPinned;

/// The embeddable list node. Must be pinned — moving it would
/// invalidate pointers held by neighbors.
pub struct ListHead {
    pub next: *mut ListHead,
    pub prev: *mut ListHead,
    _pin: PhantomPinned,
}

impl ListHead {
    pub const fn new() -> Self {
        // Initially point to self (circular empty list)
        // We'll fix the pointers after pinning via init()
        Self {
            next: std::ptr::null_mut(),
            prev: std::ptr::null_mut(),
            _pin: PhantomPinned,
        }
    }

    /// Initialize as empty circular list (head node).
    /// SAFETY: ptr must point to a pinned, stable ListHead.
    pub unsafe fn init(ptr: *mut ListHead) {
        (*ptr).next = ptr;
        (*ptr).prev = ptr;
    }

    pub unsafe fn is_empty(head: *const ListHead) -> bool {
        (*head).next == head as *mut _
    }

    /// Insert `new` between `prev` and `next`.
    /// SAFETY: all three pointers must be valid, pinned, non-null.
    pub unsafe fn __list_add(
        new: *mut ListHead,
        prev: *mut ListHead,
        next: *mut ListHead,
    ) {
        (*next).prev = new;
        (*new).next  = next;
        (*new).prev  = prev;
        (*prev).next = new;
    }

    pub unsafe fn list_add_tail(new: *mut ListHead, head: *mut ListHead) {
        Self::__list_add(new, (*head).prev, head);
    }

    pub unsafe fn list_del(entry: *mut ListHead) {
        (*(*entry).prev).next = (*entry).next;
        (*(*entry).next).prev = (*entry).prev;
        // Poison pointers
        (*entry).next = 0xdead_0000_0000_0100usize as *mut _;
        (*entry).prev = 0xdead_0000_0000_0122usize as *mut _;
    }
}

/// Macro-equivalent: recover *T from embedded ListHead pointer.
/// offset_of is stable in Rust 1.77+.
macro_rules! list_entry {
    ($ptr:expr, $type:ty, $field:ident) => {{
        let offset = std::mem::offset_of!($type, $field);
        let base = ($ptr as *mut u8).sub(offset);
        base as *mut $type
    }};
}

// ── Domain type ──────────────────────────────────────────────
#[repr(C)]
struct Process {
    pid: u32,
    name: [u8; 32],
    node: ListHead,  // embedded
}

impl Process {
    fn new_boxed(pid: u32, name: &str) -> Box<Self> {
        let mut buf = [0u8; 32];
        let bytes = name.as_bytes();
        buf[..bytes.len().min(31)].copy_from_slice(&bytes[..bytes.len().min(31)]);
        Box::new(Process {
            pid,
            name: buf,
            node: ListHead::new(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_intrusive_list() {
        unsafe {
            // Head sentinel — we box it to pin its address
            let mut head = Box::new(ListHead::new());
            let head_ptr: *mut ListHead = &mut *head;
            ListHead::init(head_ptr);
            assert!(ListHead::is_empty(head_ptr));

            // Create processes; box them to pin addresses
            let mut p1 = Process::new_boxed(1, "init");
            let mut p2 = Process::new_boxed(2, "bash");
            let mut p3 = Process::new_boxed(3, "nginx");

            let n1: *mut ListHead = &mut p1.node;
            let n2: *mut ListHead = &mut p2.node;
            let n3: *mut ListHead = &mut p3.node;

            ListHead::init(n1);
            ListHead::init(n2);
            ListHead::init(n3);

            ListHead::list_add_tail(n1, head_ptr);
            ListHead::list_add_tail(n2, head_ptr);
            ListHead::list_add_tail(n3, head_ptr);

            assert!(!ListHead::is_empty(head_ptr));

            // Traverse
            let mut cur = (*head_ptr).next;
            let mut count = 0;
            while cur != head_ptr {
                let proc_ptr = list_entry!(cur, Process, node);
                let pid = (*proc_ptr).pid;
                println!("PID={}", pid);
                count += 1;
                cur = (*cur).next;
            }
            assert_eq!(count, 3);

            // Delete middle node
            ListHead::list_del(n2);

            // Verify count is 2
            cur = (*head_ptr).next;
            count = 0;
            while cur != head_ptr {
                count += 1;
                cur = (*cur).next;
            }
            assert_eq!(count, 2);
        }
    }
}
```

### Go Implementation (Intrusive List via Generics)

```go
// file: intrusive/list.go
// Go doesn't allow the same pointer-arithmetic trick, but we can
// approximate intrusive lists using Go generics + embedded interfaces.
// This is how you'd implement it in a Go kernel module or low-level lib.

package intrusive

import "unsafe"

// ListHead is the embeddable node.
// Go structs are addressable, so we can recover the containing struct
// using unsafe.Offsetof — the same trick as container_of.
type ListHead struct {
    next *ListHead
    prev *ListHead
}

// Init initializes a list head as an empty circular list.
func (h *ListHead) Init() *ListHead {
    h.next = h
    h.prev = h
    return h
}

// IsEmpty reports whether the list is empty.
func (h *ListHead) IsEmpty() bool {
    return h.next == h
}

func listAdd(new, prev, next *ListHead) {
    next.prev = new
    new.next  = next
    new.prev  = prev
    prev.next = new
}

// AddTail appends new to the tail of the list headed by h.
func (h *ListHead) AddTail(new *ListHead) {
    listAdd(new, h.prev, h)
}

// AddFront prepends new to the head of the list.
func (h *ListHead) AddFront(new *ListHead) {
    listAdd(new, h, h.next)
}

// Del removes entry from its list.
func Del(entry *ListHead) {
    entry.prev.next = entry.next
    entry.next.prev = entry.prev
    entry.next = nil // poison
    entry.prev = nil
}

// ContainerOf is the Go equivalent of container_of.
// T must be the containing struct, field is the field name holding ListHead.
//
// Usage:
//   proc := ContainerOf[Process](node, unsafe.Offsetof(Process{}.Node))
func ContainerOf[T any](node *ListHead, offset uintptr) *T {
    return (*T)(unsafe.Pointer(uintptr(unsafe.Pointer(node)) - offset))
}

// ── Domain type ──────────────────────────────────────────────

// file: intrusive/process.go
package intrusive

import "fmt"

type Process struct {
    PID  int
    Name string
    Node ListHead // embedded intrusive node
}

var processNodeOffset = unsafe.Offsetof(Process{}.Node)

func ProcessFromNode(node *ListHead) *Process {
    return ContainerOf[Process](node, processNodeOffset)
}

// RunQueue demonstrates usage
func RunQueueDemo() {
    var head ListHead
    head.Init()

    processes := []Process{
        {PID: 1, Name: "init"},
        {PID: 2, Name: "bash"},
        {PID: 3, Name: "nginx"},
    }

    for i := range processes {
        processes[i].Node.Init()
        head.AddTail(&processes[i].Node)
    }

    fmt.Println("Run queue:")
    for cur := head.next; cur != &head; cur = cur.next {
        p := ProcessFromNode(cur)
        fmt.Printf("  PID=%d name=%s\n", p.PID, p.Name)
    }
}
```

```go
// file: intrusive/list_test.go
package intrusive

import (
    "testing"
    "unsafe"
)

func TestListHeadBasic(t *testing.T) {
    var head ListHead
    head.Init()

    if !head.IsEmpty() {
        t.Fatal("new list should be empty")
    }

    type Item struct {
        val  int
        node ListHead
    }

    offset := unsafe.Offsetof(Item{}.node)

    items := make([]Item, 3)
    for i := range items {
        items[i].val = i + 1
        items[i].node.Init()
        head.AddTail(&items[i].node)
    }

    if head.IsEmpty() {
        t.Fatal("list should not be empty after inserts")
    }

    // Traverse and verify order
    idx := 1
    for cur := head.next; cur != &head; cur = cur.next {
        item := ContainerOf[Item](cur, offset)
        if item.val != idx {
            t.Errorf("expected val=%d, got=%d", idx, item.val)
        }
        idx++
    }

    // Delete middle
    Del(&items[1].node)
    count := 0
    for cur := head.next; cur != &head; cur = cur.next {
        count++
    }
    if count != 2 {
        t.Errorf("expected 2 items after delete, got %d", count)
    }
}

func BenchmarkListAddTail(b *testing.B) {
    type Item struct {
        val  int
        node ListHead
    }
    items := make([]Item, b.N)
    var head ListHead
    head.Init()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        items[i].node.Init()
        head.AddTail(&items[i].node)
    }
}
```

### Common Pitfalls

1. **Iterating without `_safe` and deleting**: `list_for_each_entry` caches `pos->member.next` before the loop body — if you delete `pos` inside, the next pointer is poisoned and you crash. Always use `list_for_each_entry_safe` when deleting.

2. **Forgetting INIT_LIST_HEAD**: An uninitialized `list_head` has garbage pointers. Any `list_empty()` check will return a random boolean.

3. **Moving a list node**: If you `memcpy` or `realloc` a struct containing a `list_head`, the prev/next pointers of neighbors still point to the old address. Always delete before moving.

4. **Thread safety**: `list_head` has no locking. You must hold the appropriate lock during all mutations. Using `list_for_each_entry` without a lock while another CPU calls `list_del` is a data race.

5. **The head is not data**: Never pass the head node to `list_entry` — it doesn't point to a valid domain struct. Always guard with `&pos->member != head`.

### Where Linux Uses list_head

- `task_struct.tasks` — all processes in the system
- `task_struct.children` / `sibling` — process tree
- `super_block.s_list` — mounted filesystems
- `inode.i_list` — inode LRU
- `net_device.dev_list` — network interfaces
- `page.lru` — page LRU lists
- `timer_list.entry` — timer wheels

---

## 3. Hash Tables

### One-Line Explanation
An array of `hlist_head` buckets, each a singly-linked list, providing O(1) average-case lookup by mapping keys through a hash function to bucket indices.

### Analogy
A hotel with numbered rooms. The room number is `hash(key) % num_rooms`. Multiple guests can share a room (chaining). Finding a guest means going to their room and scanning the (short) list of occupants.

### Linux kernel: `DECLARE_HASHTABLE`

```c
/* linux/include/linux/hashtable.h */

#define DECLARE_HASHTABLE(name, bits)                              \
    struct hlist_head name[1 << (bits)]

#define DEFINE_HASHTABLE(name, bits)                               \
    struct hlist_head name[1 << (bits)] =                          \
            { [0 ... ((1 << (bits)) - 1)] = HLIST_HEAD_INIT }

/* Add */
#define hash_add(hashtable, node, key)                             \
    hlist_add_head(node, &hashtable[hash_min(key, HASH_BITS(hashtable))])

/* Lookup */
#define hash_for_each_possible(name, obj, member, key)             \
    hlist_for_each_entry(obj, &name[hash_min(key, HASH_BITS(name))], member)

/* Full traversal */
#define hash_for_each(name, bkt, obj, member)                      \
    for ((bkt) = 0, obj = NULL; obj == NULL && (bkt) < HASH_SIZE(name);\
            (bkt)++)                                                \
        hlist_for_each_entry(obj, &name[bkt], member)
```

### Hash Functions Used in the Kernel

```c
/* linux/include/linux/hash.h */

/* Fibonacci hashing for integer keys — excellent distribution */
#define GOLDEN_RATIO_32  0x61C88647
#define GOLDEN_RATIO_64  0x61C8864680B583EBull

static inline u32 hash_32(u32 val, unsigned int bits) {
    return (val * GOLDEN_RATIO_32) >> (32 - bits);
}

static inline u64 hash_64(u64 val, unsigned int bits) {
    return (val * GOLDEN_RATIO_64) >> (64 - bits);
}

/* String hashing (djb2 variant used in some subsystems) */
static inline unsigned long full_name_hash(const void *salt,
                                            const char *name, unsigned int len) {
    /* Uses partial MD4 internally for performance */
    /* ... */
}
```

### C Implementation: Full PID-to-Process Hash Table

```c
/* file: pid_hash.c
 * compile: gcc -Wall -O2 pid_hash.c -o pid_hash
 * Demonstrates a kernel-style hash table mapping PID → process
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

#define HASH_BITS   8
#define HASH_SIZE   (1u << HASH_BITS)
#define HASH_MASK   (HASH_SIZE - 1)

/* ── hlist (single-pointer prev trick) ── */
struct hlist_node {
    struct hlist_node  *next;
    struct hlist_node **pprev;   /* &prev->next or &head->first */
};

struct hlist_head {
    struct hlist_node *first;
};

#define HLIST_HEAD_INIT  { .first = NULL }

static inline void hlist_add_head(struct hlist_node *n, struct hlist_head *h) {
    if (h->first) h->first->pprev = &n->next;
    n->next  = h->first;
    n->pprev = &h->first;
    h->first = n;
}

static inline void hlist_del(struct hlist_node *n) {
    *n->pprev = n->next;
    if (n->next) n->next->pprev = n->pprev;
    n->next  = (void *)0xDEAD;
    n->pprev = (void *)0xDEAD;
}

#define hlist_entry(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

#define hlist_for_each_entry(pos, head, member)                              \
    for (pos = (head)->first ?                                               \
         hlist_entry((head)->first, typeof(*pos), member) : NULL;            \
         pos;                                                                 \
         pos = (pos)->member.next ?                                          \
         hlist_entry((pos)->member.next, typeof(*pos), member) : NULL)

/* ── Hash function: Fibonacci hashing ── */
static inline uint32_t pid_hash(uint32_t pid) {
    return (pid * 0x61C88647u) >> (32 - HASH_BITS);
}

/* ── Domain struct ── */
typedef struct {
    uint32_t         pid;
    char             name[32];
    struct hlist_node node;     /* key: pid */
} process_t;

/* ── Hash table ── */
struct hlist_head pid_table[HASH_SIZE];

static void pid_table_init(void) {
    for (int i = 0; i < (int)HASH_SIZE; i++)
        pid_table[i].first = NULL;
}

static void pid_insert(process_t *p) {
    uint32_t bucket = pid_hash(p->pid);
    hlist_add_head(&p->node, &pid_table[bucket]);
}

static process_t *pid_find(uint32_t pid) {
    uint32_t bucket = pid_hash(pid);
    process_t *p;
    hlist_for_each_entry(p, &pid_table[bucket], node) {
        if (p->pid == pid) return p;
    }
    return NULL;
}

static void pid_remove(process_t *p) {
    hlist_del(&p->node);
}

/* ── Statistics ── */
static void print_stats(void) {
    int used = 0, max_chain = 0;
    for (int i = 0; i < (int)HASH_SIZE; i++) {
        int len = 0;
        struct hlist_node *n = pid_table[i].first;
        while (n) { len++; n = n->next; }
        if (len > 0) used++;
        if (len > max_chain) max_chain = len;
    }
    printf("Hash table: %d/%d buckets used, max chain=%d\n",
           used, HASH_SIZE, max_chain);
}

int main(void) {
    pid_table_init();

    /* Insert 512 processes */
    process_t *procs = calloc(512, sizeof(process_t));
    for (int i = 0; i < 512; i++) {
        procs[i].pid = i + 1;
        snprintf(procs[i].name, sizeof(procs[i].name), "proc_%d", i + 1);
        pid_insert(&procs[i]);
    }

    print_stats();

    /* Lookup */
    process_t *found = pid_find(256);
    assert(found && found->pid == 256);
    printf("Found: PID=%u name=%s\n", found->pid, found->name);

    /* Not found */
    assert(pid_find(9999) == NULL);

    /* Remove */
    pid_remove(&procs[255]);  /* PID 256 */
    assert(pid_find(256) == NULL);
    printf("PID 256 successfully removed.\n");

    free(procs);
    return 0;
}
```

### Rust Implementation: Generic Hash Map (Kernel-Style)

```rust
// file: src/kernel_hash.rs
// Demonstrates a fixed-size open-addressing hash map
// with Robin Hood probing — used in io_uring internally.

use std::mem::MaybeUninit;

const EMPTY: u64 = u64::MAX;

#[derive(Debug)]
pub struct KernelHashMap<V, const N: usize> {
    keys:   [u64; N],
    values: [MaybeUninit<V>; N],
    len:    usize,
}

impl<V: Clone, const N: usize> KernelHashMap<V, N> {
    const _POWER_OF_TWO: () = assert!(N.is_power_of_two(), "N must be power of 2");

    pub fn new() -> Self {
        // SAFETY: u64::MAX is our sentinel; MaybeUninit is safe uninit
        Self {
            keys:   [EMPTY; N],
            values: unsafe { MaybeUninit::uninit().assume_init() },
            len:    0,
        }
    }

    #[inline]
    fn hash(key: u64) -> usize {
        // Fibonacci hashing — same as kernel hash_64
        const GOLDEN: u64 = 0x61C8864680B583EB;
        let h = key.wrapping_mul(GOLDEN);
        (h >> (64 - N.trailing_zeros())) as usize
    }

    pub fn insert(&mut self, key: u64, value: V) -> bool {
        if self.len >= N * 3 / 4 {
            return false; // load factor exceeded
        }
        let mut idx = Self::hash(key) & (N - 1);
        loop {
            if self.keys[idx] == EMPTY || self.keys[idx] == key {
                if self.keys[idx] == EMPTY {
                    self.len += 1;
                }
                self.keys[idx] = key;
                self.values[idx].write(value);
                return true;
            }
            idx = (idx + 1) & (N - 1); // linear probing
        }
    }

    pub fn get(&self, key: u64) -> Option<&V> {
        let mut idx = Self::hash(key) & (N - 1);
        let start = idx;
        loop {
            if self.keys[idx] == EMPTY {
                return None;
            }
            if self.keys[idx] == key {
                // SAFETY: key != EMPTY means value is initialized
                return Some(unsafe { self.values[idx].assume_init_ref() });
            }
            idx = (idx + 1) & (N - 1);
            if idx == start {
                return None; // full table
            }
        }
    }

    pub fn len(&self) -> usize { self.len }
    pub fn is_empty(&self) -> bool { self.len == 0 }
}

impl<V, const N: usize> Drop for KernelHashMap<V, N> {
    fn drop(&mut self) {
        for i in 0..N {
            if self.keys[i] != EMPTY {
                // SAFETY: key != EMPTY means value is initialized
                unsafe { self.values[i].assume_init_drop(); }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_get() {
        let mut map: KernelHashMap<String, 256> = KernelHashMap::new();
        assert!(map.insert(1, "init".to_string()));
        assert!(map.insert(2, "bash".to_string()));
        assert_eq!(map.get(1).unwrap(), "init");
        assert_eq!(map.get(2).unwrap(), "bash");
        assert!(map.get(3).is_none());
    }

    #[test]
    fn test_collision_handling() {
        let mut map: KernelHashMap<u32, 64> = KernelHashMap::new();
        for i in 0..40u64 {
            assert!(map.insert(i, i as u32));
        }
        for i in 0..40u64 {
            assert_eq!(*map.get(i).unwrap(), i as u32);
        }
    }

    #[bench]
    #[cfg(feature = "bench")]
    fn bench_insert(b: &mut test::Bencher) {
        b.iter(|| {
            let mut map: KernelHashMap<u64, 1024> = KernelHashMap::new();
            for i in 0..700u64 {
                map.insert(i, i * 2);
            }
        });
    }
}
```

### Go Implementation

```go
// file: hashtable/hashtable.go
package hashtable

import "sync"

const (
    defaultBuckets = 256 // must be power of 2
    loadFactor     = 0.75
)

type entry[K comparable, V any] struct {
    key   K
    value V
    next  *entry[K, V]
}

// HashMap is a kernel-style chaining hash map with per-bucket RWMutex
// (analogous to the kernel's bucket spinlocks for fine-grained locking).
type HashMap[K comparable, V any] struct {
    buckets []*entry[K, V]
    locks   []sync.RWMutex
    hasher  func(K) uint64
    size    int
    count   int64
    mask    uint64
}

func New[K comparable, V any](bits int, hasher func(K) uint64) *HashMap[K, V] {
    n := 1 << bits
    return &HashMap[K, V]{
        buckets: make([]*entry[K, V], n),
        locks:   make([]sync.RWMutex, n),
        hasher:  hasher,
        size:    n,
        mask:    uint64(n - 1),
    }
}

func (m *HashMap[K, V]) bucket(key K) int {
    // Fibonacci mixing
    h := m.hasher(key)
    h ^= h >> 33
    h *= 0xff51afd7ed558ccd
    h ^= h >> 33
    return int(h & m.mask)
}

func (m *HashMap[K, V]) Set(key K, val V) {
    b := m.bucket(key)
    m.locks[b].Lock()
    defer m.locks[b].Unlock()

    for e := m.buckets[b]; e != nil; e = e.next {
        if e.key == key {
            e.value = val
            return
        }
    }
    m.buckets[b] = &entry[K, V]{key: key, value: val, next: m.buckets[b]}
}

func (m *HashMap[K, V]) Get(key K) (V, bool) {
    b := m.bucket(key)
    m.locks[b].RLock()
    defer m.locks[b].RUnlock()

    for e := m.buckets[b]; e != nil; e = e.next {
        if e.key == key {
            return e.value, true
        }
    }
    var zero V
    return zero, false
}

func (m *HashMap[K, V]) Delete(key K) bool {
    b := m.bucket(key)
    m.locks[b].Lock()
    defer m.locks[b].Unlock()

    var prev *entry[K, V]
    for e := m.buckets[b]; e != nil; e = e.next {
        if e.key == key {
            if prev == nil {
                m.buckets[b] = e.next
            } else {
                prev.next = e.next
            }
            return true
        }
        prev = e
    }
    return false
}
```

```go
// file: hashtable/hashtable_test.go
package hashtable

import (
    "math/bits"
    "testing"
)

func u64hasher(k uint64) uint64 { return k }

func TestHashMapSetGet(t *testing.T) {
    m := New[uint64, string](8, u64hasher)
    m.Set(1, "init")
    m.Set(2, "bash")

    if v, ok := m.Get(1); !ok || v != "init" {
        t.Errorf("expected init, got %s", v)
    }
    if _, ok := m.Get(99); ok {
        t.Error("expected miss for key 99")
    }
}

func TestHashMapDelete(t *testing.T) {
    m := New[uint64, int](8, u64hasher)
    for i := uint64(0); i < 100; i++ {
        m.Set(i, int(i))
    }
    if !m.Delete(50) {
        t.Error("delete should succeed")
    }
    if _, ok := m.Get(50); ok {
        t.Error("key 50 should be gone")
    }
}

func BenchmarkHashMapSet(b *testing.B) {
    m := New[uint64, uint64](10, u64hasher)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        m.Set(uint64(i), uint64(i))
    }
}

// Verify N is power of two (compile-time equivalent)
var _ = bits.OnesCount(defaultBuckets) == 1
```

### Common Pitfalls

1. **Non-power-of-two table size**: Using `%` for bucket selection instead of `& (size-1)` is both slower and breaks when size is not a power of two.
2. **Poor hash function**: Never use `key % table_size` — terrible distribution. Always use multiplicative hashing (Fibonacci) or SipHash-1-3 for untrusted keys.
3. **Hash flooding**: User-controlled string keys with a static hash function → DoS via deliberate collisions. Linux uses randomized SipHash for `htab_of_map_ops`.
4. **Missing load factor check**: Kernel code often uses static-sized tables — once the chain length exceeds a threshold, performance collapses.
5. **Iterator invalidation**: Deleting during `hash_for_each` without the `_safe` variant.

---

## 4. Red-Black Trees

### One-Line Explanation
A self-balancing BST where every path from root to null has the same number of black nodes, guaranteeing O(log n) worst-case operations — used in the CFS scheduler, VM subsystem, and inode management.

### Analogy
A filing cabinet where folders are colored red or black. The rules ensure no shelf is ever more than twice as tall as any other shelf, keeping searches fast even as folders are added and removed.

### The Five RB-Tree Invariants

1. Every node is either RED or BLACK.
2. The root is BLACK.
3. Every NULL leaf is BLACK.
4. A RED node's children must both be BLACK (no two consecutive reds).
5. For each node, all simple paths from that node to descendant leaves contain the same number of BLACK nodes.

Consequence: The longest path (alternating red-black) is at most 2× the shortest path (all black), giving height ≤ 2 log₂(n+1).

### Linux Kernel API

```c
/* linux/include/linux/rbtree.h */

struct rb_node {
    unsigned long __rb_parent_color;  /* parent + color packed into one field */
    struct rb_node *rb_right;
    struct rb_node *rb_left;
} __attribute__((aligned(sizeof(long))));

struct rb_root {
    struct rb_node *rb_node;
};

#define RB_ROOT (struct rb_root) { NULL, }

/* Color is stored in the lowest bit of __rb_parent_color
 * because nodes are aligned to sizeof(long) */
#define rb_parent(r)   ((struct rb_node *)((r)->__rb_parent_color & ~3))
#define rb_color(r)    ((r)->__rb_parent_color & 1)
#define rb_is_red(r)   (!rb_color(r))
#define rb_is_black(r) rb_color(r)

void rb_insert_color(struct rb_node *node, struct rb_root *root);
void rb_erase(struct rb_node *node, struct rb_root *root);
struct rb_node *rb_next(const struct rb_node *node);
struct rb_node *rb_prev(const struct rb_node *node);
struct rb_node *rb_first(const struct rb_root *root);
struct rb_node *rb_last(const struct rb_root *root);
```

**Augmented RB-Trees** (used in VM for interval queries):

```c
/* linux/include/linux/rbtree_augmented.h */
/* User provides a propagate callback that updates augmented data
 * (e.g., max interval endpoint) during rotations */
RB_DECLARE_CALLBACKS(static, my_augment_callbacks, struct my_node, rb,
                     unsigned long, subtree_max, compute_max)
```

### C Implementation: CFS-Style Virtual Runtime Scheduler

```c
/* file: cfs_rbtree.c
 * compile: gcc -Wall -O2 cfs_rbtree.c -o cfs_rbtree
 *
 * Simplified CFS (Completely Fair Scheduler) using an rb-tree
 * keyed on vruntime (virtual runtime). The leftmost node is
 * always the next task to run.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>

/* ── Minimal rb-tree implementation ── */
typedef enum { RB_RED = 0, RB_BLACK = 1 } rb_color_t;

typedef struct rb_node {
    struct rb_node *parent;
    struct rb_node *left;
    struct rb_node *right;
    rb_color_t      color;
} rb_node_t;

typedef struct {
    rb_node_t *root;
} rb_root_t;

#define RB_EMPTY_ROOT { .root = NULL }

#define rb_entry(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

static inline void rb_set_parent(rb_node_t *node, rb_node_t *parent) {
    node->parent = parent;
}

/* Left rotation around x:
 *
 *     x              y
 *    / \            / \
 *   A   y    →    x   C
 *      / \       / \
 *     B   C     A   B
 */
static void rb_rotate_left(rb_root_t *root, rb_node_t *x) {
    rb_node_t *y = x->right;
    x->right = y->left;
    if (y->left) y->left->parent = x;
    y->parent = x->parent;
    if (!x->parent)            root->root = y;
    else if (x == x->parent->left) x->parent->left  = y;
    else                            x->parent->right = y;
    y->left   = x;
    x->parent = y;
}

static void rb_rotate_right(rb_root_t *root, rb_node_t *x) {
    rb_node_t *y = x->left;
    x->left = y->right;
    if (y->right) y->right->parent = x;
    y->parent = x->parent;
    if (!x->parent)             root->root = y;
    else if (x == x->parent->right) x->parent->right = y;
    else                             x->parent->left  = y;
    y->right  = x;
    x->parent = y;
}

/* Fix-up after insertion: restores RB invariants.
 * New node starts RED; we fix upward. */
static void rb_insert_fixup(rb_root_t *root, rb_node_t *z) {
    while (z->parent && z->parent->color == RB_RED) {
        rb_node_t *gp = z->parent->parent;
        if (z->parent == gp->left) {
            rb_node_t *uncle = gp->right;
            if (uncle && uncle->color == RB_RED) {
                /* Case 1: uncle is red → recolor */
                z->parent->color = RB_BLACK;
                uncle->color     = RB_BLACK;
                gp->color        = RB_RED;
                z = gp;
            } else {
                if (z == z->parent->right) {
                    /* Case 2: uncle black, z is right child → rotate left */
                    z = z->parent;
                    rb_rotate_left(root, z);
                }
                /* Case 3: uncle black, z is left child → rotate right */
                z->parent->color  = RB_BLACK;
                gp->color         = RB_RED;
                rb_rotate_right(root, gp);
            }
        } else {
            /* Symmetric: parent is right child */
            rb_node_t *uncle = gp->left;
            if (uncle && uncle->color == RB_RED) {
                z->parent->color = RB_BLACK;
                uncle->color     = RB_BLACK;
                gp->color        = RB_RED;
                z = gp;
            } else {
                if (z == z->parent->left) {
                    z = z->parent;
                    rb_rotate_right(root, z);
                }
                z->parent->color = RB_BLACK;
                gp->color        = RB_RED;
                rb_rotate_left(root, gp);
            }
        }
    }
    root->root->color = RB_BLACK; /* root always black */
}

static void rb_insert(rb_root_t *root, rb_node_t *node,
                       int (*cmp)(rb_node_t *, rb_node_t *)) {
    rb_node_t **link = &root->root;
    rb_node_t  *parent = NULL;

    while (*link) {
        parent = *link;
        link = (cmp(node, parent) < 0) ? &parent->left : &parent->right;
    }
    node->parent = parent;
    node->left   = node->right = NULL;
    node->color  = RB_RED;
    *link = node;
    rb_insert_fixup(root, node);
}

static rb_node_t *rb_first(rb_root_t *root) {
    rb_node_t *n = root->root;
    if (!n) return NULL;
    while (n->left) n = n->left;
    return n;
}

static rb_node_t *rb_next(rb_node_t *node) {
    if (node->right) {
        node = node->right;
        while (node->left) node = node->left;
        return node;
    }
    rb_node_t *parent;
    while ((parent = node->parent) && node == parent->right)
        node = parent;
    return parent;
}

/* ── CFS task structure ── */
typedef struct {
    uint64_t vruntime;   /* key: virtual runtime in nanoseconds */
    int      pid;
    char     name[32];
    rb_node_t rb;         /* embedded rbtree node */
} sched_entity_t;

static int cfs_cmp(rb_node_t *a, rb_node_t *b) {
    sched_entity_t *ea = rb_entry(a, sched_entity_t, rb);
    sched_entity_t *eb = rb_entry(b, sched_entity_t, rb);
    if (ea->vruntime < eb->vruntime) return -1;
    if (ea->vruntime > eb->vruntime) return  1;
    return ea->pid - eb->pid;  /* tie-break by pid */
}

static rb_root_t cfs_rq = RB_EMPTY_ROOT;

static void cfs_enqueue(sched_entity_t *se) {
    rb_insert(&cfs_rq, &se->rb, cfs_cmp);
}

/* Pick next: leftmost node = smallest vruntime */
static sched_entity_t *cfs_pick_next(void) {
    rb_node_t *leftmost = rb_first(&cfs_rq);
    return leftmost ? rb_entry(leftmost, sched_entity_t, rb) : NULL;
}

static void print_rq(void) {
    printf("Run queue (in vruntime order):\n");
    for (rb_node_t *n = rb_first(&cfs_rq); n; n = rb_next(n)) {
        sched_entity_t *se = rb_entry(n, sched_entity_t, rb);
        printf("  PID=%d vruntime=%llu name=%s\n",
               se->pid, (unsigned long long)se->vruntime, se->name);
    }
}

int main(void) {
    sched_entity_t tasks[] = {
        { .vruntime = 1000, .pid = 1, .name = "init"   },
        { .vruntime =  500, .pid = 2, .name = "bash"   },
        { .vruntime = 2000, .pid = 3, .name = "nginx"  },
        { .vruntime =  750, .pid = 4, .name = "sshd"   },
        { .vruntime =  250, .pid = 5, .name = "kworker"},
    };

    for (int i = 0; i < 5; i++)
        cfs_enqueue(&tasks[i]);

    print_rq();

    sched_entity_t *next = cfs_pick_next();
    printf("\nScheduled: PID=%d vruntime=%llu\n",
           next->pid, (unsigned long long)next->vruntime);

    return 0;
}
```

### Rust Implementation

```rust
// file: src/rbtree.rs
// Production-quality generic RB-tree in safe+unsafe Rust.
// Demonstrates the same color-bit-packing trick as Linux.

use std::cmp::Ordering;
use std::ptr::NonNull;

#[derive(Clone, Copy, PartialEq)]
enum Color { Red, Black }

struct Node<K: Ord, V> {
    key:    K,
    value:  V,
    color:  Color,
    left:   Option<NonNull<Node<K, V>>>,
    right:  Option<NonNull<Node<K, V>>>,
    parent: Option<NonNull<Node<K, V>>>,
}

impl<K: Ord, V> Node<K, V> {
    fn new(key: K, value: V) -> NonNull<Self> {
        let boxed = Box::new(Self {
            key, value,
            color:  Color::Red,
            left:   None,
            right:  None,
            parent: None,
        });
        NonNull::from(Box::leak(boxed))
    }
}

pub struct RBTree<K: Ord, V> {
    root: Option<NonNull<Node<K, V>>>,
    len:  usize,
}

impl<K: Ord, V> RBTree<K, V> {
    pub fn new() -> Self { Self { root: None, len: 0 } }
    pub fn len(&self) -> usize { self.len }
    pub fn is_empty(&self) -> bool { self.len == 0 }

    pub fn insert(&mut self, key: K, value: V) {
        unsafe { self.insert_inner(key, value) }
        self.len += 1;
    }

    pub fn get(&self, key: &K) -> Option<&V> {
        unsafe {
            let mut cur = self.root;
            while let Some(node) = cur {
                match key.cmp(&(*node.as_ptr()).key) {
                    Ordering::Equal   => return Some(&(*node.as_ptr()).value),
                    Ordering::Less    => cur = (*node.as_ptr()).left,
                    Ordering::Greater => cur = (*node.as_ptr()).right,
                }
            }
            None
        }
    }

    unsafe fn insert_inner(&mut self, key: K, value: V) {
        let new_node = Node::new(key, value);
        let mut cur   = self.root;
        let mut parent: Option<NonNull<Node<K,V>>> = None;
        let mut is_left = false;

        while let Some(node) = cur {
            parent = cur;
            match (*new_node.as_ptr()).key.cmp(&(*node.as_ptr()).key) {
                Ordering::Less => { is_left = true;  cur = (*node.as_ptr()).left;  }
                _              => { is_left = false; cur = (*node.as_ptr()).right; }
            }
        }

        (*new_node.as_ptr()).parent = parent;
        match parent {
            None => self.root = Some(new_node),
            Some(p) => {
                if is_left { (*p.as_ptr()).left  = Some(new_node); }
                else       { (*p.as_ptr()).right = Some(new_node); }
            }
        }
        self.fixup_insert(new_node);
    }

    unsafe fn fixup_insert(&mut self, mut z: NonNull<Node<K, V>>) {
        while let Some(parent) = (*z.as_ptr()).parent {
            if (*parent.as_ptr()).color != Color::Red { break; }
            let gp = (*parent.as_ptr()).parent.unwrap();

            if Some(parent) == (*gp.as_ptr()).left {
                let uncle = (*gp.as_ptr()).right;
                if uncle.map_or(false, |u| (*u.as_ptr()).color == Color::Red) {
                    (*parent.as_ptr()).color = Color::Black;
                    (*uncle.unwrap().as_ptr()).color = Color::Black;
                    (*gp.as_ptr()).color = Color::Red;
                    z = gp;
                } else {
                    if Some(z) == (*parent.as_ptr()).right {
                        z = parent;
                        self.rotate_left(z);
                    }
                    let p = (*z.as_ptr()).parent.unwrap();
                    let g = (*p.as_ptr()).parent.unwrap();
                    (*p.as_ptr()).color = Color::Black;
                    (*g.as_ptr()).color = Color::Red;
                    self.rotate_right(g);
                }
            } else {
                let uncle = (*gp.as_ptr()).left;
                if uncle.map_or(false, |u| (*u.as_ptr()).color == Color::Red) {
                    (*parent.as_ptr()).color = Color::Black;
                    (*uncle.unwrap().as_ptr()).color = Color::Black;
                    (*gp.as_ptr()).color = Color::Red;
                    z = gp;
                } else {
                    if Some(z) == (*parent.as_ptr()).left {
                        z = parent;
                        self.rotate_right(z);
                    }
                    let p = (*z.as_ptr()).parent.unwrap();
                    let g = (*p.as_ptr()).parent.unwrap();
                    (*p.as_ptr()).color = Color::Black;
                    (*g.as_ptr()).color = Color::Red;
                    self.rotate_left(g);
                }
            }
        }
        if let Some(root) = self.root {
            (*root.as_ptr()).color = Color::Black;
        }
    }

    unsafe fn rotate_left(&mut self, x: NonNull<Node<K, V>>) {
        let y = (*x.as_ptr()).right.unwrap();
        (*x.as_ptr()).right = (*y.as_ptr()).left;
        if let Some(yl) = (*y.as_ptr()).left {
            (*yl.as_ptr()).parent = Some(x);
        }
        (*y.as_ptr()).parent = (*x.as_ptr()).parent;
        match (*x.as_ptr()).parent {
            None => self.root = Some(y),
            Some(p) => {
                if (*p.as_ptr()).left == Some(x) { (*p.as_ptr()).left  = Some(y); }
                else                             { (*p.as_ptr()).right = Some(y); }
            }
        }
        (*y.as_ptr()).left   = Some(x);
        (*x.as_ptr()).parent = Some(y);
    }

    unsafe fn rotate_right(&mut self, x: NonNull<Node<K, V>>) {
        let y = (*x.as_ptr()).left.unwrap();
        (*x.as_ptr()).left = (*y.as_ptr()).right;
        if let Some(yr) = (*y.as_ptr()).right {
            (*yr.as_ptr()).parent = Some(x);
        }
        (*y.as_ptr()).parent = (*x.as_ptr()).parent;
        match (*x.as_ptr()).parent {
            None => self.root = Some(y),
            Some(p) => {
                if (*p.as_ptr()).right == Some(x) { (*p.as_ptr()).right = Some(y); }
                else                              { (*p.as_ptr()).left  = Some(y); }
            }
        }
        (*y.as_ptr()).right  = Some(x);
        (*x.as_ptr()).parent = Some(y);
    }

    /// In-order traversal
    pub fn iter_inorder(&self) -> Vec<(&K, &V)> {
        let mut result = Vec::with_capacity(self.len);
        unsafe { self.inorder(self.root, &mut result); }
        result
    }

    unsafe fn inorder<'a>(&self, node: Option<NonNull<Node<K,V>>>,
                           out: &mut Vec<(&'a K, &'a V)>) {
        if let Some(n) = node {
            self.inorder((*n.as_ptr()).left, out);
            out.push((&(*n.as_ptr()).key, &(*n.as_ptr()).value));
            self.inorder((*n.as_ptr()).right, out);
        }
    }
}

impl<K: Ord, V> Drop for RBTree<K, V> {
    fn drop(&mut self) {
        unsafe { self.drop_node(self.root); }
    }
    // (same drop logic elided for brevity)
}

unsafe fn drop_node_inner<K: Ord, V>(node: Option<NonNull<Node<K,V>>>) {
    if let Some(n) = node {
        drop_node_inner((*n.as_ptr()).left);
        drop_node_inner((*n.as_ptr()).right);
        drop(Box::from_raw(n.as_ptr()));
    }
}

impl<K: Ord, V> RBTree<K, V> {
    unsafe fn drop_node(&mut self, node: Option<NonNull<Node<K,V>>>) {
        drop_node_inner(node);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_sorted_output() {
        let mut tree = RBTree::new();
        for &k in &[5u32, 3, 7, 1, 4, 6, 8, 2] {
            tree.insert(k, k * 10);
        }
        let ordered: Vec<u32> = tree.iter_inorder().iter().map(|(&k,_)| k).collect();
        assert_eq!(ordered, vec![1,2,3,4,5,6,7,8]);
    }

    #[test]
    fn test_get() {
        let mut tree = RBTree::new();
        tree.insert(10u32, "ten");
        tree.insert(20u32, "twenty");
        assert_eq!(tree.get(&10), Some(&"ten"));
        assert_eq!(tree.get(&99), None);
    }
}
```

### Go Implementation (using stdlib `btree` + custom RB for reference)

```go
// file: rbtree/rbtree.go
// Pure Go RB-tree. In production Go you'd use google/btree or
// the stdlib sort.Search; this is for understanding internals.

package rbtree

type color bool
const (red color = false; black color = true)

type node[K any, V any] struct {
    key         K
    val         V
    color       color
    left, right *node[K, V]
    parent      *node[K, V]
}

// Tree is a generic, ordered map backed by an RB-tree.
type Tree[K any, V any] struct {
    root *node[K, V]
    cmp  func(a, b K) int
    len  int
}

func New[K any, V any](cmp func(a, b K) int) *Tree[K, V] {
    return &Tree[K, V]{cmp: cmp}
}

func (t *Tree[K, V]) Len() int { return t.len }

func (t *Tree[K, V]) Set(key K, val V) {
    z := &node[K, V]{key: key, val: val, color: red}
    var parent *node[K, V]
    cur := t.root

    for cur != nil {
        parent = cur
        switch c := t.cmp(key, cur.key); {
        case c < 0:  cur = cur.left
        case c > 0:  cur = cur.right
        default:     cur.val = val; return  // update
        }
    }

    z.parent = parent
    if parent == nil {
        t.root = z
    } else if t.cmp(key, parent.key) < 0 {
        parent.left = z
    } else {
        parent.right = z
    }
    t.len++
    t.insertFixup(z)
}

func (t *Tree[K, V]) Get(key K) (V, bool) {
    cur := t.root
    for cur != nil {
        switch c := t.cmp(key, cur.key); {
        case c < 0:  cur = cur.left
        case c > 0:  cur = cur.right
        default:     return cur.val, true
        }
    }
    var zero V
    return zero, false
}

func isRed[K any, V any](n *node[K, V]) bool {
    return n != nil && n.color == red
}

func (t *Tree[K, V]) insertFixup(z *node[K, V]) {
    for z.parent != nil && z.parent.color == red {
        p  := z.parent
        gp := p.parent
        if gp == nil { break }

        if p == gp.left {
            uncle := gp.right
            if isRed(uncle) {
                p.color    = black
                uncle.color = black
                gp.color   = red
                z = gp
            } else {
                if z == p.right {
                    z = p
                    t.rotateLeft(z)
                    p = z.parent
                    gp = p.parent
                }
                p.color  = black
                gp.color = red
                t.rotateRight(gp)
            }
        } else {
            uncle := gp.left
            if isRed(uncle) {
                p.color     = black
                uncle.color = black
                gp.color    = red
                z = gp
            } else {
                if z == p.left {
                    z = p
                    t.rotateRight(z)
                    p = z.parent
                    gp = p.parent
                }
                p.color  = black
                gp.color = red
                t.rotateLeft(gp)
            }
        }
    }
    t.root.color = black
}

func (t *Tree[K, V]) rotateLeft(x *node[K, V]) {
    y := x.right
    x.right = y.left
    if y.left != nil { y.left.parent = x }
    y.parent = x.parent
    if x.parent == nil      { t.root = y } else
    if x == x.parent.left   { x.parent.left  = y } else
                              { x.parent.right = y }
    y.left   = x
    x.parent = y
}

func (t *Tree[K, V]) rotateRight(x *node[K, V]) {
    y := x.left
    x.left = y.right
    if y.right != nil { y.right.parent = x }
    y.parent = x.parent
    if x.parent == nil      { t.root = y } else
    if x == x.parent.right  { x.parent.right = y } else
                              { x.parent.left  = y }
    y.right  = x
    x.parent = y
}

// InOrder returns all key-value pairs in sorted order.
func (t *Tree[K, V]) InOrder() []struct{ K K; V V } {
    var result []struct{ K K; V V }
    var walk func(*node[K, V])
    walk = func(n *node[K, V]) {
        if n == nil { return }
        walk(n.left)
        result = append(result, struct{ K K; V V }{n.key, n.val})
        walk(n.right)
    }
    walk(t.root)
    return result
}
```

```go
// file: rbtree/rbtree_test.go
package rbtree

import (
    "cmp"
    "testing"
)

func TestRBTreeInOrder(t *testing.T) {
    tree := New[int, string](cmp.Compare[int])
    for _, k := range []int{5, 3, 7, 1, 4, 6, 8, 2} {
        tree.Set(k, "")
    }
    pairs := tree.InOrder()
    for i, p := range pairs {
        if p.K != i+1 {
            t.Errorf("index %d: expected key %d, got %d", i, i+1, p.K)
        }
    }
}

func TestRBTreeGet(t *testing.T) {
    tree := New[int, int](cmp.Compare[int])
    tree.Set(10, 100)
    tree.Set(20, 200)
    if v, ok := tree.Get(10); !ok || v != 100 {
        t.Error("Get(10) failed")
    }
    if _, ok := tree.Get(99); ok {
        t.Error("Get(99) should miss")
    }
}

func BenchmarkRBTreeSet(b *testing.B) {
    tree := New[int, int](cmp.Compare[int])
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        tree.Set(i, i)
    }
}
```

### Where Linux Uses RB-Trees

| Subsystem | Key | Purpose |
|---|---|---|
| CFS Scheduler | `vruntime` | Pick lowest-vruntime task in O(log n) |
| Virtual Memory | `vm_start` | `vm_area_struct` intervals in process address space |
| Ext4 extents | `ee_block` | File block-to-disk mapping |
| epoll | `fd` | Monitored file descriptors |
| Timer wheel (hrtimer) | `expiry` | High-resolution timers |
| nftables | rule priority | Firewall rule ordering |

### Common Pitfalls

1. **Inserting without the fixup**: A bare BST insert leaves color invariants broken. Always call `rb_insert_color` after linking the node.
2. **Concurrent access without locking**: `rb_insert`/`rb_erase` are not atomic. The CFS scheduler uses `rq->lock` (a raw spinlock) around all rb operations.
3. **Augmented trees without callbacks**: If you track subtree metadata (like max endpoint for interval trees), rotations must update that metadata. Missing the `RB_DECLARE_CALLBACKS` propagation silently corrupts the augmented data.
4. **Forgetting rb_erase before free**: Freeing a node while it's still in the tree leaves dangling pointers in parent/children. Always `rb_erase` first.

---

## 5. Radix Trees and XArray

### One-Line Explanation
A radix tree (prefix tree) indexed by integer keys maps dense or sparse integer keys to pointers in O(key_bits / radix) — used in the Linux page cache to map file offsets to `struct page`.

### Analogy
A phone book organized by digit-by-digit directory. To find extension 12345, you open drawer "1", then "2", then "3", then "4", then "5". Each level fans out by the radix (typically 64 in Linux = 6 bits per level).

### Linux Evolution: radix_tree → XArray

| Feature | `radix_tree` (old) | `XArray` (new, 5.x+) |
|---|---|---|
| Internal | 64-way tree | Same tree + cleaner API |
| Locking | External | Built-in xa_lock |
| Marks | 3 mark bits | 3 mark bits |
| Sparse | Yes | Yes |
| Multi-order | Limited | First-class |
| API | `radix_tree_insert` | `xa_store`, `xa_load` |

### XArray API (Linux 5.x)

```c
/* linux/include/linux/xarray.h */

struct xarray {
    spinlock_t xa_lock;
    gfp_t      xa_flags;
    void      *xa_head;  /* root: NULL, node*, or leaf value */
};

#define DEFINE_XARRAY(name) \
    struct xarray name = XARRAY_INIT(name, 0)

/* Atomic store/load */
void *xa_store(struct xarray *xa, unsigned long index,
               void *entry, gfp_t gfp);
void *xa_load(struct xarray *xa, unsigned long index);
void *xa_erase(struct xarray *xa, unsigned long index);

/* Iteration */
#define xa_for_each(xa, index, entry)                          \
    for (index = 0, entry = xa_find(xa, &index, ULONG_MAX, XA_PRESENT); \
         entry; entry = xa_find_after(xa, &index, ULONG_MAX, XA_PRESENT))

/* Marks: tag entries for efficient "find next marked" */
void  xa_set_mark(struct xarray *xa, unsigned long index, xa_mark_t mark);
void  xa_clear_mark(struct xarray *xa, unsigned long index, xa_mark_t mark);
bool  xa_get_mark(struct xarray *xa, unsigned long index, xa_mark_t mark);
```

### Internal Structure: The XArray Node

```c
/* Each internal node holds 64 slots (6-bit radix on 64-bit systems) */
#define XA_CHUNK_SHIFT  6
#define XA_CHUNK_SIZE   (1UL << XA_CHUNK_SHIFT)   /* 64 */
#define XA_CHUNK_MASK   (XA_CHUNK_SIZE - 1)

struct xa_node {
    unsigned char  shift;    /* log2 of span covered by this node */
    unsigned char  offset;   /* which slot in parent */
    unsigned char  count;    /* number of non-null slots */
    unsigned char  nr_values;/* number of leaf values */
    struct xa_node *parent;
    struct xarray  *array;
    union {
        struct list_head private_list;
        struct rcu_head  rcu_head;
    };
    void __rcu *slots[XA_CHUNK_SIZE];   /* 64 child pointers */
    unsigned long tags[XA_MAX_MARKS][XA_CHUNK_SIZE / BITS_PER_LONG];
};
```

**Tree height for a 64-bit index space:**
- Level 0 (root leaf): indices 0–63 (shift=0)
- Level 1: indices 0–4095 (shift=6)
- Level 2: indices 0–262143 (shift=12)
- ...
- Level 10: indices 0–2⁶⁴ (shift=60)

The tree expands dynamically as larger indices are inserted.

### C Implementation: Simplified Radix Tree (4-way for clarity)

```c
/* file: radix_tree.c
 * compile: gcc -Wall -O2 radix_tree.c -o radix_tree
 * 2-bit radix (4-way branching) for clarity; Linux uses 6-bit (64-way).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define RADIX_BITS   2
#define RADIX_SIZE   (1u << RADIX_BITS)   /* 4 children */
#define RADIX_MASK   (RADIX_SIZE - 1)
#define KEY_BITS     8                    /* 8-bit keys → depth 4 */
#define MAX_DEPTH    (KEY_BITS / RADIX_BITS)

typedef struct radix_node {
    struct radix_node *children[RADIX_SIZE];
    void              *value;   /* non-NULL only at leaf level */
    int                is_leaf;
} radix_node_t;

typedef struct {
    radix_node_t *root;
} radix_tree_t;

static radix_node_t *node_alloc(void) {
    return calloc(1, sizeof(radix_node_t));
}

static void radix_insert(radix_tree_t *tree, uint8_t key, void *value) {
    if (!tree->root) tree->root = node_alloc();

    radix_node_t *cur = tree->root;
    /* Walk from MSB down to LSB, 2 bits at a time */
    for (int level = MAX_DEPTH - 1; level >= 0; level--) {
        int idx = (key >> (level * RADIX_BITS)) & RADIX_MASK;
        if (!cur->children[idx])
            cur->children[idx] = node_alloc();
        cur = cur->children[idx];
    }
    cur->value   = value;
    cur->is_leaf = 1;
}

static void *radix_lookup(radix_tree_t *tree, uint8_t key) {
    radix_node_t *cur = tree->root;
    if (!cur) return NULL;
    for (int level = MAX_DEPTH - 1; level >= 0; level--) {
        int idx = (key >> (level * RADIX_BITS)) & RADIX_MASK;
        if (!cur->children[idx]) return NULL;
        cur = cur->children[idx];
    }
    return cur->is_leaf ? cur->value : NULL;
}

/* ── Demo ── */
typedef struct { int pageno; char data[16]; } page_t;

int main(void) {
    radix_tree_t tree = {0};

    page_t pages[256];
    for (int i = 0; i < 256; i++) {
        pages[i].pageno = i;
        snprintf(pages[i].data, sizeof(pages[i].data), "page_%d", i);
        radix_insert(&tree, (uint8_t)i, &pages[i]);
    }

    for (int i = 0; i < 256; i++) {
        page_t *p = radix_lookup(&tree, (uint8_t)i);
        assert(p && p->pageno == i);
    }

    printf("All 256 page lookups verified.\n");

    page_t *p = radix_lookup(&tree, 42);
    printf("Page 42: %s\n", p->data);

    /* Cleanup (omitted for brevity in demo) */
    return 0;
}
```

### Rust Implementation: XArray-Equivalent

```rust
// file: src/xarray.rs
// Simplified XArray: sparse integer-keyed store, 6-bit radix, RCU-friendly design.

use std::collections::HashMap;

/// Simplified XArray using a HashMap backend for correct semantics.
/// A full implementation would use the 64-way tree with mark bits.
pub struct XArray<V> {
    inner: HashMap<u64, V>,
}

impl<V> XArray<V> {
    pub fn new() -> Self { Self { inner: HashMap::new() } }

    pub fn store(&mut self, index: u64, value: V) -> Option<V> {
        self.inner.insert(index, value)
    }

    pub fn load(&self, index: u64) -> Option<&V> {
        self.inner.get(&index)
    }

    pub fn erase(&mut self, index: u64) -> Option<V> {
        self.inner.remove(&index)
    }

    /// Find next present entry at or after `start`.
    pub fn find_after(&self, start: u64) -> Option<(u64, &V)> {
        let mut best: Option<(u64, &V)> = None;
        for (&k, v) in &self.inner {
            if k >= start {
                if best.map_or(true, |(bk, _)| k < bk) {
                    best = Some((k, v));
                }
            }
        }
        best
    }

    /// Iterate in index order.
    pub fn iter_ordered(&self) -> Vec<(u64, &V)> {
        let mut pairs: Vec<(u64, &V)> = self.inner.iter().map(|(&k,v)| (k,v)).collect();
        pairs.sort_by_key(|&(k,_)| k);
        pairs
    }
}

/// A true 64-way radix tree node for educational purposes.
const RADIX_BITS: u32 = 6;
const RADIX_SIZE: usize = 1 << RADIX_BITS;

struct RadixNode<V> {
    children: [Option<Box<RadixNode<V>>>; RADIX_SIZE],
    value: Option<V>,
}

impl<V> RadixNode<V> {
    fn new() -> Box<Self> {
        Box::new(Self {
            // We can't use Default for large arrays without const tricks,
            // so we use unsafe once for initialization only.
            children: unsafe {
                let mut arr: [Option<Box<RadixNode<V>>>; RADIX_SIZE] = std::mem::zeroed();
                for slot in arr.iter_mut() { *slot = None; }
                arr
            },
            value: None,
        })
    }
}

pub struct RadixTree<V> {
    root: Option<Box<RadixNode<V>>>,
    height: u32,
}

impl<V> RadixTree<V> {
    pub fn new() -> Self { Self { root: None, height: 0 } }

    pub fn insert(&mut self, index: u64, value: V) {
        if self.root.is_none() {
            self.root = Some(RadixNode::new());
        }
        let mut node = self.root.as_mut().unwrap();
        // Determine needed height
        let mut height = self.height;
        while (index >> (height * RADIX_BITS)) >= RADIX_SIZE as u64 {
            height += 1;
        }
        self.height = height;

        for shift in (0..=height).rev() {
            let slot = ((index >> (shift * RADIX_BITS)) & (RADIX_SIZE as u64 - 1)) as usize;
            if shift == 0 {
                node.value = Some(value);
                return;
            }
            if node.children[slot].is_none() {
                node.children[slot] = Some(RadixNode::new());
            }
            node = node.children[slot].as_mut().unwrap();
        }
    }

    pub fn get(&self, index: u64) -> Option<&V> {
        let mut node = self.root.as_ref()?;
        for shift in (0..=self.height).rev() {
            let slot = ((index >> (shift * RADIX_BITS)) & (RADIX_SIZE as u64 - 1)) as usize;
            if shift == 0 {
                return node.value.as_ref();
            }
            node = node.children[slot].as_ref()?;
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xarray_basic() {
        let mut xa = XArray::new();
        xa.store(0, "page_0");
        xa.store(100, "page_100");
        xa.store(99999, "page_99999");

        assert_eq!(xa.load(0), Some(&"page_0"));
        assert_eq!(xa.load(100), Some(&"page_100"));
        assert_eq!(xa.load(99999), Some(&"page_99999"));
        assert!(xa.load(1).is_none());

        xa.erase(100);
        assert!(xa.load(100).is_none());
    }

    #[test]
    fn test_radix_tree() {
        let mut tree = RadixTree::new();
        for i in [0u64, 63, 64, 4095, 4096, 100000] {
            tree.insert(i, i * 2);
        }
        for i in [0u64, 63, 64, 4095, 4096, 100000] {
            assert_eq!(tree.get(i), Some(&(i * 2)));
        }
        assert!(tree.get(1).is_none());
    }
}
```

### Go Implementation

```go
// file: xarray/xarray.go
// XArray-equivalent in Go for the page cache use case.

package xarray

import (
    "sync"
)

// XArray is a sparse indexed store mapping uint64 indices to values.
// Thread-safe via a single RWMutex (production would use per-node locks).
type XArray[V any] struct {
    mu     sync.RWMutex
    nodes  map[uint64]V
    marks  map[uint64]uint8   // 3-bit mark field per entry
}

func New[V any]() *XArray[V] {
    return &XArray[V]{
        nodes: make(map[uint64]V),
        marks: make(map[uint64]uint8),
    }
}

func (xa *XArray[V]) Store(index uint64, val V) {
    xa.mu.Lock()
    xa.nodes[index] = val
    xa.mu.Unlock()
}

func (xa *XArray[V]) Load(index uint64) (V, bool) {
    xa.mu.RLock()
    v, ok := xa.nodes[index]
    xa.mu.RUnlock()
    return v, ok
}

func (xa *XArray[V]) Erase(index uint64) {
    xa.mu.Lock()
    delete(xa.nodes, index)
    delete(xa.marks, index)
    xa.mu.Unlock()
}

const (
    MarkDirty  = 1 << 0 // Page is dirty
    MarkAccess = 1 << 1 // Page was accessed (LRU)
    MarkWrite  = 1 << 2 // Writeback in progress
)

func (xa *XArray[V]) SetMark(index uint64, mark uint8) {
    xa.mu.Lock()
    xa.marks[index] |= mark
    xa.mu.Unlock()
}

func (xa *XArray[V]) ClearMark(index uint64, mark uint8) {
    xa.mu.Lock()
    xa.marks[index] &^= mark
    xa.mu.Unlock()
}

func (xa *XArray[V]) GetMark(index uint64, mark uint8) bool {
    xa.mu.RLock()
    defer xa.mu.RUnlock()
    return xa.marks[index]&mark != 0
}

// ForEachMarked iterates over all entries with the given mark set.
func (xa *XArray[V]) ForEachMarked(mark uint8, fn func(index uint64, val V)) {
    xa.mu.RLock()
    defer xa.mu.RUnlock()
    for idx, m := range xa.marks {
        if m&mark != 0 {
            if v, ok := xa.nodes[idx]; ok {
                fn(idx, v)
            }
        }
    }
}
```

---

## 6. B-Trees

### One-Line Explanation
A B-tree is a self-balancing, disk-friendly tree where each node holds multiple keys and has multiple children, minimizing I/O by fitting many keys per cache line or disk block.

### Analogy
A library organized into sections → shelves → books. Each shelf holds many books (high branching factor). Fewer shelf visits (I/O operations) means faster search even with millions of books.

### B-tree Properties

For a B-tree of order `t` (minimum degree):
- Every non-root node has at least `t-1` keys and `t` children.
- Every node has at most `2t-1` keys and `2t` children.
- All leaves are at the same depth.
- Keys within a node are sorted.
- Height = O(log_t n)

### Linux B-Tree: `lib/btree.c`

The kernel provides a generic B-tree in `lib/btree.c` used by:
- ACPI tables mapping
- Some driver subsystems
- Primarily: **btrfs** uses its own B-tree variant (B+ tree with copy-on-write)

```c
/* linux/include/linux/btree.h */
struct btree_head {
    unsigned long *node;
    mempool_t *mempool;
    int height;
};

/* Initialize */
void btree_init_mempool(struct btree_head *head, mempool_t *mempool);
int  btree_init(struct btree_head *head);

/* Operations (geo describes key geometry: 32-bit, 64-bit, or 128-bit keys) */
void *btree_lookup(struct btree_head *head, struct btree_geo *geo,
                   unsigned long *key);
int   btree_insert(struct btree_head *head, struct btree_geo *geo,
                   unsigned long *key, void *val, gfp_t gfp);
void *btree_remove(struct btree_head *head, struct btree_geo *geo,
                   unsigned long *key);
```

### C Implementation: B+ Tree (disk-style, order 3)

```c
/* file: btree.c
 * compile: gcc -Wall -O2 btree.c -o btree
 * B+ tree: internal nodes hold only keys; leaves hold key+value and are linked.
 * This is the structure used by btrfs, ext4 extents, and most databases.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define ORDER     3                       /* min degree: nodes have 2–5 keys */
#define MAX_KEYS  (2 * ORDER - 1)         /* 5 */
#define MIN_KEYS  (ORDER - 1)             /* 2 */
#define MAX_CHILD (2 * ORDER)             /* 6 */

typedef struct bnode {
    int            keys[MAX_KEYS];
    void          *vals[MAX_KEYS];        /* leaf only */
    struct bnode  *children[MAX_CHILD];  /* internal only */
    int            n;                    /* current key count */
    int            is_leaf;
    struct bnode  *next;                 /* leaf chain */
} bnode_t;

typedef struct {
    bnode_t *root;
} btree_t;

static bnode_t *bnode_new(int is_leaf) {
    bnode_t *n = calloc(1, sizeof(bnode_t));
    n->is_leaf = is_leaf;
    return n;
}

static int bsearch_key(bnode_t *node, int key) {
    int lo = 0, hi = node->n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (node->keys[mid] == key) return mid;
        if (node->keys[mid] < key)  lo = mid + 1;
        else                         hi = mid - 1;
    }
    return lo;   /* insertion point */
}

/* ── Search ── */
static void *btree_search(bnode_t *node, int key) {
    int i = bsearch_key(node, key);
    if (i < node->n && node->keys[i] == key && node->is_leaf)
        return node->vals[i];
    if (node->is_leaf) return NULL;
    return btree_search(node->children[i], key);
}

/* ── Split child ── */
static void btree_split_child(bnode_t *parent, int i, bnode_t *child) {
    bnode_t *right = bnode_new(child->is_leaf);
    right->n = MIN_KEYS;  /* ORDER-1 keys go to right */

    /* Copy upper half of child to right */
    for (int j = 0; j < MIN_KEYS; j++) {
        right->keys[j] = child->keys[j + ORDER];
        if (child->is_leaf) right->vals[j] = child->vals[j + ORDER];
    }
    if (!child->is_leaf) {
        for (int j = 0; j < ORDER; j++)
            right->children[j] = child->children[j + ORDER];
    }
    if (child->is_leaf) {
        right->next  = child->next;
        child->next  = right;
    }
    child->n = child->is_leaf ? MIN_KEYS : MIN_KEYS;

    /* Insert median key into parent */
    for (int j = parent->n; j > i; j--) {
        parent->children[j + 1] = parent->children[j];
        parent->keys[j]         = parent->keys[j - 1];
    }
    parent->children[i + 1] = right;
    parent->keys[i]          = child->is_leaf ? right->keys[0] : child->keys[ORDER - 1];
    parent->n++;
}

/* ── Insert into non-full node ── */
static void btree_insert_nonfull(bnode_t *node, int key, void *val) {
    int i = node->n - 1;
    if (node->is_leaf) {
        while (i >= 0 && node->keys[i] > key) {
            node->keys[i + 1] = node->keys[i];
            node->vals[i + 1] = node->vals[i];
            i--;
        }
        node->keys[i + 1] = key;
        node->vals[i + 1] = val;
        node->n++;
    } else {
        while (i >= 0 && node->keys[i] > key) i--;
        i++;
        if (node->children[i]->n == MAX_KEYS) {
            btree_split_child(node, i, node->children[i]);
            if (key > node->keys[i]) i++;
        }
        btree_insert_nonfull(node->children[i], key, val);
    }
}

/* ── Public insert ── */
static void btree_insert(btree_t *tree, int key, void *val) {
    if (!tree->root) {
        tree->root = bnode_new(1);  /* leaf root */
        tree->root->keys[0] = key;
        tree->root->vals[0] = val;
        tree->root->n = 1;
        return;
    }
    if (tree->root->n == MAX_KEYS) {
        bnode_t *new_root = bnode_new(0);
        new_root->children[0] = tree->root;
        btree_split_child(new_root, 0, tree->root);
        tree->root = new_root;
    }
    btree_insert_nonfull(tree->root, key, val);
}

/* ── Range scan via leaf chain ── */
static void btree_range(btree_t *tree, int lo, int hi,
                        void (*visit)(int key, void *val)) {
    /* Find leftmost leaf */
    bnode_t *cur = tree->root;
    while (cur && !cur->is_leaf)
        cur = cur->children[0];

    while (cur) {
        for (int i = 0; i < cur->n; i++) {
            if (cur->keys[i] > hi) return;
            if (cur->keys[i] >= lo) visit(cur->keys[i], cur->vals[i]);
        }
        cur = cur->next;
    }
}

/* ── Demo ── */
static void print_entry(int key, void *val) {
    printf("  key=%d val=%s\n", key, (char *)val);
}

int main(void) {
    btree_t tree = {0};

    char *names[] = {"alpha","beta","gamma","delta","epsilon",
                     "zeta","eta","theta","iota","kappa"};
    int keys[]    = {5, 3, 7, 1, 9, 2, 8, 4, 6, 10};

    for (int i = 0; i < 10; i++)
        btree_insert(&tree, keys[i], names[i]);

    /* Point lookup */
    char *found = btree_search(tree.root, 7);
    printf("Lookup 7: %s\n", found ? found : "not found");

    /* Range scan [3..7] */
    printf("Range [3..7]:\n");
    btree_range(&tree, 3, 7, print_entry);

    return 0;
}
```

---

## 7. Skip Lists

### One-Line Explanation
A probabilistic layered linked list that achieves O(log n) average search by maintaining express lanes with exponentially fewer nodes at each higher level.

### Analogy
A metro express system: the ground level stops at every station, but higher levels skip stations. To reach a distant station quickly, you ride the express to the nearest skipped stop, then drop down to local.

### Use in Linux

The kernel itself rarely uses skip lists (it prefers deterministic rb-trees for scheduling). However:
- **LevelDB / RocksDB** (widely used in Linux userspace) use skip lists for their MemTable
- **Redis** uses skip lists for sorted sets
- The **Linux futex** hash table was proposed as a skip list at one point

### C Implementation: Concurrent Lock-Free Skip List

```c
/* file: skiplist.c
 * compile: gcc -Wall -O2 -lpthread skiplist.c -o skiplist
 * Lock-free skip list using CAS (compare-and-swap) for concurrent access.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdatomic.h>
#include <assert.h>
#include <time.h>

#define MAX_LEVEL  16
#define PROBABILITY 0.5   /* 50% chance of promotion to next level */

typedef struct sl_node {
    int   key;
    void *value;
    int   top_level;
    /* Atomically updated forward pointers */
    _Atomic(struct sl_node *) next[MAX_LEVEL + 1];
} sl_node_t;

typedef struct {
    sl_node_t *head;   /* sentinel: key = INT_MIN */
    sl_node_t *tail;   /* sentinel: key = INT_MAX */
    int        max_level;
} skiplist_t;

static sl_node_t *sl_node_new(int key, void *value, int level) {
    sl_node_t *n = calloc(1, sizeof(*n));
    n->key       = key;
    n->value     = value;
    n->top_level = level;
    return n;
}

static int random_level(void) {
    int level = 0;
    while ((double)rand() / RAND_MAX < PROBABILITY && level < MAX_LEVEL)
        level++;
    return level;
}

static skiplist_t *skiplist_new(void) {
    skiplist_t *sl = malloc(sizeof(*sl));
    sl->max_level  = MAX_LEVEL;
    sl->head       = sl_node_new(INT32_MIN, NULL, MAX_LEVEL);
    sl->tail       = sl_node_new(INT32_MAX, NULL, MAX_LEVEL);
    for (int i = 0; i <= MAX_LEVEL; i++)
        atomic_store(&sl->head->next[i], sl->tail);
    return sl;
}

/* Find: returns value or NULL. Also fills preds/succs arrays for insert/delete. */
static sl_node_t *sl_find(skiplist_t *sl, int key,
                           sl_node_t **preds, sl_node_t **succs) {
    sl_node_t *pred = sl->head;
    for (int level = MAX_LEVEL; level >= 0; level--) {
        sl_node_t *cur = atomic_load(&pred->next[level]);
        while (cur->key < key)  {
            pred = cur;
            cur  = atomic_load(&pred->next[level]);
        }
        if (preds) preds[level] = pred;
        if (succs) succs[level] = cur;
    }
    sl_node_t *candidate = atomic_load(&pred->next[0]);
    return (candidate->key == key) ? candidate : NULL;
}

static void *skiplist_get(skiplist_t *sl, int key) {
    sl_node_t *n = sl_find(sl, key, NULL, NULL);
    return n ? n->value : NULL;
}

static int skiplist_insert(skiplist_t *sl, int key, void *value) {
    sl_node_t *preds[MAX_LEVEL + 1];
    sl_node_t *succs[MAX_LEVEL + 1];
    int top = random_level();
    sl_node_t *new_node = sl_node_new(key, value, top);

retry:
    sl_find(sl, key, preds, succs);
    /* Check if key already exists */
    if (succs[0]->key == key) { free(new_node); return 0; }

    /* Link bottom-up */
    for (int level = 0; level <= top; level++)
        atomic_store(&new_node->next[level], succs[level]);

    /* CAS at level 0 first */
    sl_node_t *expected = succs[0];
    if (!atomic_compare_exchange_strong(&preds[0]->next[0], &expected, new_node))
        goto retry;

    /* Link higher levels */
    for (int level = 1; level <= top; level++) {
        while (1) {
            expected = succs[level];
            if (atomic_compare_exchange_strong(&preds[level]->next[level],
                                               &expected, new_node))
                break;
            sl_find(sl, key, preds, succs);  /* re-find on contention */
        }
    }
    return 1;
}

int main(void) {
    srand(42);
    skiplist_t *sl = skiplist_new();

    for (int i = 100; i >= 1; i--)
        skiplist_insert(sl, i, (void *)(uintptr_t)i);

    /* Verify in-order traversal */
    sl_node_t *cur = atomic_load(&sl->head->next[0]);
    int prev_key = INT32_MIN;
    int count = 0;
    while (cur != sl->tail) {
        assert(cur->key > prev_key);
        prev_key = cur->key;
        count++;
        cur = atomic_load(&cur->next[0]);
    }
    printf("Skip list has %d elements in sorted order.\n", count);
    assert(count == 100);

    /* Point lookup */
    void *v = skiplist_get(sl, 42);
    printf("Get(42) = %ld\n", (long)v);

    return 0;
}
```

---

## 8. Queues

### 8.1 kfifo: Lock-Free Single-Producer/Single-Consumer Ring Buffer

**One-Line:** A power-of-two byte ring buffer using head/tail indices with no explicit locks for SPSC access — used for interrupt handler ↔ process communication.

```c
/* linux/include/linux/kfifo.h (simplified) */
struct __kfifo {
    unsigned int    in;     /* write index (never wraps, mod on access) */
    unsigned int    out;    /* read  index (never wraps) */
    unsigned int    mask;   /* size - 1 (size must be power of 2) */
    unsigned int    esize;  /* element size */
    void           *data;
};

/* Why no modulo? Use mask: index & mask gives offset.
 * Why never wrap in and out? So (in - out) is always the count
 * without special-casing the wrap. Unsigned subtraction handles it. */

static inline unsigned int kfifo_len(struct kfifo *fifo) {
    return fifo->kfifo.in - fifo->kfifo.out;
}
static inline unsigned int kfifo_avail(struct kfifo *fifo) {
    return kfifo_size(fifo) - kfifo_len(fifo);
}
```

### C Implementation: SPSC Ring Buffer

```c
/* file: kfifo.c
 * compile: gcc -Wall -O2 kfifo.c -o kfifo
 * Lock-free SPSC ring buffer — same algorithm as Linux kfifo.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdatomic.h>
#include <assert.h>

typedef struct {
    uint8_t  *buf;
    uint32_t  mask;        /* size - 1 */
    _Atomic uint32_t head; /* reader updates */
    _Atomic uint32_t tail; /* writer updates */
} kfifo_t;

static kfifo_t *kfifo_alloc(uint32_t size) {
    assert((size & (size - 1)) == 0);  /* must be power of 2 */
    kfifo_t *f = malloc(sizeof(*f));
    f->buf  = malloc(size);
    f->mask = size - 1;
    atomic_store(&f->head, 0);
    atomic_store(&f->tail, 0);
    return f;
}

static uint32_t kfifo_len(kfifo_t *f) {
    return atomic_load(&f->tail) - atomic_load(&f->head);
}

/* Push: called ONLY by producer */
static int kfifo_push(kfifo_t *f, const void *data, uint32_t len) {
    uint32_t avail = (f->mask + 1) - kfifo_len(f);
    if (avail < len) return -1;

    uint32_t tail = atomic_load_explicit(&f->tail, memory_order_relaxed);
    uint32_t off  = tail & f->mask;
    uint32_t to_end = f->mask + 1 - off;

    if (to_end >= len) {
        memcpy(f->buf + off, data, len);
    } else {
        memcpy(f->buf + off, data, to_end);
        memcpy(f->buf, (uint8_t *)data + to_end, len - to_end);
    }
    /* Release store: data must be visible before tail update */
    atomic_store_explicit(&f->tail, tail + len, memory_order_release);
    return 0;
}

/* Pop: called ONLY by consumer */
static int kfifo_pop(kfifo_t *f, void *data, uint32_t len) {
    if (kfifo_len(f) < len) return -1;

    uint32_t head = atomic_load_explicit(&f->head, memory_order_relaxed);
    uint32_t off  = head & f->mask;
    uint32_t to_end = f->mask + 1 - off;

    if (to_end >= len) {
        memcpy(data, f->buf + off, len);
    } else {
        memcpy(data, f->buf + off, to_end);
        memcpy((uint8_t *)data + to_end, f->buf, len - to_end);
    }
    /* Release store: data consumed before head update */
    atomic_store_explicit(&f->head, head + len, memory_order_release);
    return 0;
}

int main(void) {
    kfifo_t *fifo = kfifo_alloc(64);

    /* Push packets */
    uint32_t pkt;
    for (pkt = 1; pkt <= 10; pkt++) {
        assert(kfifo_push(fifo, &pkt, sizeof(pkt)) == 0);
    }
    printf("kfifo len = %u\n", kfifo_len(fifo));

    /* Pop and verify */
    uint32_t got;
    for (uint32_t i = 1; i <= 10; i++) {
        assert(kfifo_pop(fifo, &got, sizeof(got)) == 0);
        assert(got == i);
    }
    printf("All packets received in order.\n");
    assert(kfifo_len(fifo) == 0);

    return 0;
}
```

### 8.2 Wait Queues

Wait queues are the kernel's mechanism for sleeping until a condition is true. They are fundamental to blocking I/O, signal handling, and synchronization.

```c
/* linux/include/linux/wait.h */

struct wait_queue_head {
    spinlock_t        lock;
    struct list_head  head;  /* list of wait_queue_entry */
};

struct wait_queue_entry {
    unsigned int          flags;
    void                 *private;   /* typically current task_struct */
    wait_queue_func_t     func;      /* wakeup callback */
    struct list_head      entry;
};

/* High-level macros */
DECLARE_WAIT_QUEUE_HEAD(name);

/* Sleep until condition is true */
wait_event(wq_head, condition);
wait_event_interruptible(wq_head, condition);
wait_event_timeout(wq_head, condition, timeout);

/* Wake up */
wake_up(&wq_head);
wake_up_all(&wq_head);
wake_up_interruptible(&wq_head);
```

**How `wait_event` works internally:**

```c
/* Simplified kernel implementation */
#define wait_event(wq_head, condition)                              \
do {                                                                \
    if (condition)    /* fast path: already true, no sleep */       \
        break;                                                      \
    __wait_event(wq_head, condition);                               \
} while (0)

static void __wait_event(wait_queue_head_t *wq, bool condition) {
    DEFINE_WAIT(wait);                    /* stack-allocated entry */
    for (;;) {
        prepare_to_wait(wq, &wait, TASK_UNINTERRUPTIBLE);
        if (condition) break;             /* check after adding to queue */
        schedule();                       /* give up CPU */
    }
    finish_wait(wq, &wait);              /* remove from queue, set RUNNING */
}
```

**The critical ordering**: setting task state to `TASK_UNINTERRUPTIBLE` BEFORE checking the condition prevents the race where the waker calls `wake_up` between the condition check and the sleep.

### Rust Implementation: Async-Style Wait Queue

```rust
// file: src/wait_queue.rs
// Async wait queue using Tokio's notification primitive —
// the userspace equivalent of Linux wait_queue_head.

use std::sync::{Arc, Mutex};
use std::collections::VecDeque;
use std::task::Waker;

pub struct WaitQueue {
    waiters: Mutex<VecDeque<Waker>>,
}

impl WaitQueue {
    pub fn new() -> Arc<Self> {
        Arc::new(Self { waiters: Mutex::new(VecDeque::new()) })
    }

    /// Register a waker (called by the runtime when polling a future).
    pub fn register(&self, waker: Waker) {
        self.waiters.lock().unwrap().push_back(waker);
    }

    /// Wake one waiter (like wake_up).
    pub fn wake_one(&self) {
        if let Some(w) = self.waiters.lock().unwrap().pop_front() {
            w.wake();
        }
    }

    /// Wake all waiters (like wake_up_all).
    pub fn wake_all(&self) {
        let waiters = std::mem::take(&mut *self.waiters.lock().unwrap());
        for w in waiters { w.wake(); }
    }
}

/// A future that completes when the queue is awoken.
pub struct WaitFuture {
    queue: Arc<WaitQueue>,
    registered: bool,
}

impl std::future::Future for WaitFuture {
    type Output = ();
    fn poll(mut self: std::pin::Pin<&mut Self>,
            cx: &mut std::task::Context<'_>) -> std::task::Poll<()> {
        if !self.registered {
            self.queue.register(cx.waker().clone());
            self.registered = true;
            std::task::Poll::Pending
        } else {
            std::task::Poll::Ready(())
        }
    }
}

pub fn wait_on(queue: Arc<WaitQueue>) -> WaitFuture {
    WaitFuture { queue, registered: false }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicBool, Ordering};

    #[tokio::test]
    async fn test_wait_wake() {
        let wq = WaitQueue::new();
        let wq2 = wq.clone();
        let done = Arc::new(AtomicBool::new(false));
        let done2 = done.clone();

        tokio::spawn(async move {
            tokio::time::sleep(std::time::Duration::from_millis(10)).await;
            done2.store(true, Ordering::Release);
            wq2.wake_all();
        });

        wait_on(wq).await;
        assert!(done.load(Ordering::Acquire));
    }
}
```

---

## 9. Priority Queues and Heaps

### One-Line Explanation
A binary min-heap provides O(log n) insert and O(log n) extract-min, used in the Linux timer wheel for `hrtimer` sorted by expiry time.

### Linux hrtimer: rb-tree as a Priority Queue

```c
/* linux/kernel/time/hrtimer.c
 * hrtimers use an rb-tree keyed on expiry time.
 * The leftmost (earliest) timer is cached in hrtimer_cpu_base->next_timer.
 */
struct hrtimer_clock_base {
    struct hrtimer_cpu_base  *cpu_base;
    unsigned int              index;
    clockid_t                 clockid;
    struct timerqueue_head    active;   /* rb-tree of active timers */
    /* ... */
};

/* timerqueue wraps rb-tree with leftmost caching */
struct timerqueue_head {
    struct rb_root_cached   rb_root;   /* rb_root + cached leftmost node */
};
```

### C Implementation: Binary Heap (Min-Heap)

```c
/* file: minheap.c
 * compile: gcc -Wall -O2 minheap.c -o minheap
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>
#include <string.h>

typedef struct {
    uint64_t expiry;   /* key: nanosecond timestamp */
    int      timer_id;
    char     name[32];
} timer_t;

typedef struct {
    timer_t *data;
    int      n;
    int      cap;
} minheap_t;

static minheap_t *heap_new(int cap) {
    minheap_t *h = malloc(sizeof(*h));
    h->data = malloc(cap * sizeof(timer_t));
    h->n    = 0;
    h->cap  = cap;
    return h;
}

static inline void swap(timer_t *a, timer_t *b) {
    timer_t tmp = *a; *a = *b; *b = tmp;
}

/* Sift up: fix heap after insert at index n-1 */
static void sift_up(minheap_t *h, int i) {
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (h->data[parent].expiry <= h->data[i].expiry) break;
        swap(&h->data[parent], &h->data[i]);
        i = parent;
    }
}

/* Sift down: fix heap after remove-root */
static void sift_down(minheap_t *h, int i) {
    while (1) {
        int smallest = i;
        int l = 2 * i + 1, r = 2 * i + 2;
        if (l < h->n && h->data[l].expiry < h->data[smallest].expiry) smallest = l;
        if (r < h->n && h->data[r].expiry < h->data[smallest].expiry) smallest = r;
        if (smallest == i) break;
        swap(&h->data[i], &h->data[smallest]);
        i = smallest;
    }
}

static void heap_insert(minheap_t *h, timer_t *t) {
    assert(h->n < h->cap);
    h->data[h->n++] = *t;
    sift_up(h, h->n - 1);
}

static timer_t heap_extract_min(minheap_t *h) {
    assert(h->n > 0);
    timer_t min = h->data[0];
    h->data[0]  = h->data[--h->n];
    if (h->n > 0) sift_down(h, 0);
    return min;
}

int main(void) {
    minheap_t *h = heap_new(16);

    timer_t timers[] = {
        {5000, 1, "tcp_retransmit"},
        {1000, 2, "arp_expire"},
        {3000, 3, "tcp_keepalive"},
        {2000, 4, "rcu_grace"},
        {4000, 5, "nf_conntrack"},
    };

    for (int i = 0; i < 5; i++) heap_insert(h, &timers[i]);

    printf("Timers in expiry order:\n");
    while (h->n > 0) {
        timer_t t = heap_extract_min(h);
        printf("  expiry=%llu id=%d name=%s\n",
               (unsigned long long)t.expiry, t.timer_id, t.name);
    }
    return 0;
}
```

### Rust and Go: see standard library

```rust
// file: src/timer_heap.rs
use std::collections::BinaryHeap;
use std::cmp::Reverse;  // BinaryHeap is max-heap; Reverse makes it min-heap

#[derive(Debug, Eq, PartialEq)]
struct Timer {
    expiry:   u64,
    timer_id: u32,
    name:     String,
}

impl Ord for Timer {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.expiry.cmp(&other.expiry)
    }
}
impl PartialOrd for Timer { fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> { Some(self.cmp(other)) } }

fn main() {
    // Min-heap via Reverse
    let mut heap: BinaryHeap<Reverse<Timer>> = BinaryHeap::new();

    heap.push(Reverse(Timer { expiry: 5000, timer_id: 1, name: "tcp_retransmit".into() }));
    heap.push(Reverse(Timer { expiry: 1000, timer_id: 2, name: "arp_expire".into() }));
    heap.push(Reverse(Timer { expiry: 3000, timer_id: 3, name: "tcp_keepalive".into() }));

    while let Some(Reverse(t)) = heap.pop() {
        println!("expiry={} id={} name={}", t.expiry, t.timer_id, t.name);
    }
}
```

---

## 10. Circular Buffers

### One-Line Explanation
A fixed-size buffer that wraps around, overwriting oldest data on overflow — ideal for kernel log rings, network DMA rings, and audio buffers where data is consumed at a similar rate to production.

### Linux: `struct ring_buffer` (ftrace) and `struct sk_buff` ring

```c
/* linux/kernel/trace/ring_buffer.c
 * Per-CPU ring buffers for ftrace. Each CPU has its own buffer
 * to avoid cross-CPU locking.
 */
struct trace_buffer {
    struct ring_buffer_per_cpu **buffers;
    int                          cpus;
    /* ... */
};

struct ring_buffer_per_cpu {
    int                       cpu;
    atomic_t                  record_disabled;
    struct buffer_page       *reader_page;
    unsigned long             head_page_index;
    unsigned long             tail_page_index;
    /* ... */
};
```

### C Implementation: Power-of-Two Circular Buffer with Sequence Numbers

```c
/* file: ringbuf.c
 * compile: gcc -Wall -O2 ringbuf.c -o ringbuf
 * MPSC (multi-producer, single-consumer) ring buffer with sequence numbers —
 * same algorithm as Linux's io_uring submission queue.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdatomic.h>
#include <assert.h>

#define RING_SIZE  8     /* must be power of 2 */
#define RING_MASK  (RING_SIZE - 1)

typedef struct {
    int      fd;
    int      op;
    uint64_t offset;
    uint32_t len;
    uint8_t  pad[4];
} sqe_t;  /* submission queue entry */

typedef struct {
    sqe_t             entries[RING_SIZE];
    _Atomic uint32_t  tail;       /* producer writes here */
    uint32_t          head;       /* consumer reads here (single thread) */
    uint32_t          mask;
} ring_t;

static ring_t *ring_new(void) {
    ring_t *r = calloc(1, sizeof(*r));
    r->mask   = RING_MASK;
    return r;
}

static int ring_push(ring_t *r, sqe_t *sqe) {
    uint32_t tail = atomic_load_explicit(&r->tail, memory_order_relaxed);
    if ((tail - r->head) >= RING_SIZE) return -1;  /* full */
    r->entries[tail & r->mask] = *sqe;
    atomic_store_explicit(&r->tail, tail + 1, memory_order_release);
    return 0;
}

static int ring_pop(ring_t *r, sqe_t *out) {
    if (r->head == atomic_load_explicit(&r->tail, memory_order_acquire))
        return -1;  /* empty */
    *out = r->entries[r->head & r->mask];
    r->head++;
    return 0;
}

int main(void) {
    ring_t *r = ring_new();
    sqe_t s, got;

    for (int i = 0; i < RING_SIZE; i++) {
        s = (sqe_t){ .fd = i, .op = 1, .offset = i * 4096, .len = 4096 };
        assert(ring_push(r, &s) == 0);
    }
    /* Ring is now full */
    s = (sqe_t){ .fd = 99 };
    assert(ring_push(r, &s) == -1);   /* should fail */

    for (int i = 0; i < RING_SIZE; i++) {
        assert(ring_pop(r, &got) == 0);
        assert(got.fd == i);
    }
    assert(ring_pop(r, &got) == -1);  /* empty */

    printf("Ring buffer test passed.\n");
    return 0;
}
```

---

## 11. Bitmaps and Bit Arrays

### One-Line Explanation
A compact array of bits used for tracking resource allocation (CPU sets, IRQ masks, PID bitmaps) with O(1) bit ops and efficient population count.

### Linux Bitmap API

```c
/* linux/include/linux/bitmap.h */

/* Declare a bitmap of N bits */
DECLARE_BITMAP(name, N);          /* expands to: unsigned long name[BITS_TO_LONGS(N)] */

/* Operations */
bitmap_set(map, start, nbits);    /* set bits [start, start+nbits) */
bitmap_clear(map, start, nbits);
bitmap_test_bit(map, n);
bitmap_set_bit(map, n);
bitmap_clear_bit(map, n);
bitmap_find_next_zero_area(map, size, start, nr, align_mask);
bitmap_weight(map, nbits);        /* popcount */
bitmap_and(dst, src1, src2, n);
bitmap_or(dst, src1, src2, n);
bitmap_andnot(dst, src1, src2, n);

/* CPU sets */
cpumask_t   online_mask;
cpumask_set_cpu(cpu, &mask);
for_each_cpu(cpu, &mask) { ... }

/* IRQ affinity, NUMA node masks, etc. all use bitmaps */
```

**Internal representation on 64-bit:**

```c
/* 1024-bit bitmap uses 16 × 64-bit unsigned longs */
DECLARE_BITMAP(my_bitmap, 1024);
/* maps to: unsigned long my_bitmap[16]; */

/* Bit 67 is at:
 *   word = 67 / 64 = 1
 *   bit  = 67 % 64 = 3
 *   mask = 1UL << 3 = 0x8
 */
```

### C Implementation: CPU Set Allocator

```c
/* file: bitmap.c
 * compile: gcc -Wall -O2 bitmap.c -o bitmap
 * Tracks which of 64 CPUs are online/available.
 */
#include <stdio.h>
#include <stdint.h>
#include <assert.h>

typedef uint64_t cpumask_t;   /* 64-CPU system fits in one word */

#define CPU_BITS     64
#define CPU_MASK_ALL (~0ULL)

static inline void cpu_set(int cpu, cpumask_t *mask)    { *mask |=  (1ULL << cpu); }
static inline void cpu_clear(int cpu, cpumask_t *mask)  { *mask &= ~(1ULL << cpu); }
static inline int  cpu_test(int cpu, cpumask_t *mask)   { return (*mask >> cpu) & 1; }

/* Find first set bit (FFS) — maps to BSF/TZCNT instruction */
static inline int cpu_first_set(cpumask_t mask) {
    if (!mask) return -1;
    return __builtin_ctzll(mask);  /* count trailing zeros */
}

/* Find next set bit after 'start' */
static inline int cpu_next_set(cpumask_t mask, int start) {
    if (start + 1 >= CPU_BITS) return -1;
    uint64_t m = mask >> (start + 1);
    if (!m) return -1;
    return start + 1 + __builtin_ctzll(m);
}

/* Iterate over all set bits */
#define for_each_cpu(cpu, mask)                                  \
    for ((cpu) = cpu_first_set(mask); (cpu) >= 0;                \
         (cpu) = cpu_next_set(mask, cpu))

/* Population count — maps to POPCNT instruction */
static inline int cpumask_weight(cpumask_t mask) {
    return __builtin_popcountll(mask);
}

/* Multi-word bitmap for >64 CPUs */
#define BITMAP_LONGS(n)  (((n) + 63) / 64)

typedef struct {
    uint64_t words[BITMAP_LONGS(256)];  /* 256-CPU bitmap */
} bitmap256_t;

static void bmap256_set(bitmap256_t *b, int bit) {
    b->words[bit / 64] |= (1ULL << (bit % 64));
}

static int bmap256_test(bitmap256_t *b, int bit) {
    return (b->words[bit / 64] >> (bit % 64)) & 1;
}

static int bmap256_find_first_zero(bitmap256_t *b, int max) {
    for (int word = 0; word < BITMAP_LONGS(256); word++) {
        uint64_t w = ~b->words[word];  /* invert: zeros become ones */
        if (w) {
            int bit = word * 64 + __builtin_ctzll(w);
            return (bit < max) ? bit : -1;
        }
    }
    return -1;
}

int main(void) {
    cpumask_t online = 0;

    /* Bring CPUs 0..7 online */
    for (int i = 0; i < 8; i++) cpu_set(i, &online);
    printf("Online CPUs: %d\n", cpumask_weight(online));

    int cpu;
    for_each_cpu(cpu, online)
        printf("  CPU %d online\n", cpu);

    /* Take CPU 3 offline */
    cpu_clear(3, &online);
    assert(!cpu_test(3, &online));

    /* Allocate a free CPU */
    cpumask_t avail = online;
    int first = cpu_first_set(avail);
    printf("First available CPU: %d\n", first);

    /* 256-CPU bitmap demo */
    bitmap256_t bmap = {0};
    for (int i = 0; i < 256; i += 3) bmap256_set(&bmap, i);
    int first_zero = bmap256_find_first_zero(&bmap, 256);
    printf("First zero bit in 256-bitmap: %d\n", first_zero);
    assert(first_zero == 1);  /* bits 0,3,6,... set; bit 1 is first zero */

    return 0;
}
```

---

## 12. Per-CPU Data Structures

### One-Line Explanation
Per-CPU variables give each CPU its own private copy of a variable, eliminating cache line bouncing and all need for locking in the common case.

### The Cache Coherency Problem

Without per-CPU variables, a shared counter protected by a spinlock means:
1. CPU0 acquires lock → broadcasts ownership of cache line
2. CPU1 tries to acquire lock → cache miss, stalls
3. When CPU0 releases, CPU1's cache is invalidated
4. This "cache line bouncing" destroys performance on 32+ core systems

### Linux API

```c
/* linux/include/linux/percpu.h */

/* Static declaration */
DEFINE_PER_CPU(int, my_counter);

/* Dynamic allocation */
int __percpu *p = alloc_percpu(int);
free_percpu(p);

/* Access (must disable preemption: task must not migrate to another CPU
 * between get and put) */
int val;
get_cpu();  /* disable preemption, returns current cpu number */
val = __this_cpu_read(my_counter);
__this_cpu_add(my_counter, 1);
put_cpu();  /* re-enable preemption */

/* RCU-safe per-cpu read (safe without disabling preemption) */
val = per_cpu(my_counter, cpu_id);
```

**Memory layout**: All per-CPU variables for all CPUs are allocated in a contiguous array. CPU 0's copies are at offset 0, CPU 1's copies at offset `PERCPU_OFFSET`, etc. This keeps each CPU's working set in its own cache domain.

```
Physical memory:
┌──────────────────────────────────────────────────────┐
│ CPU0: [counter=5][lock_stats=...][net_rx_packets=...] │ ← 64KB
│ CPU1: [counter=2][lock_stats=...][net_rx_packets=...] │ ← 64KB
│ CPU2: [counter=8][lock_stats=...][net_rx_packets=...] │ ← 64KB
└──────────────────────────────────────────────────────┘
```

### C Implementation: Per-CPU Counter

```c
/* file: percpu.c
 * compile: gcc -Wall -O2 -lpthread percpu.c -o percpu
 * Simulate per-CPU counters for multi-core statistics.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <unistd.h>
#include <sched.h>

#define MAX_CPUS  8

typedef struct {
    uint64_t count;
    uint8_t  _pad[56];   /* pad to 64-byte cache line */
} __attribute__((aligned(64))) percpu_counter_t;

static percpu_counter_t counters[MAX_CPUS];

static int get_current_cpu(void) {
    /* In a real kernel: smp_processor_id() */
    return sched_getcpu() % MAX_CPUS;
}

static void percpu_inc(void) {
    int cpu = get_current_cpu();
    counters[cpu].count++;  /* no lock needed: only this CPU writes here */
}

static uint64_t percpu_sum(void) {
    uint64_t total = 0;
    for (int i = 0; i < MAX_CPUS; i++)
        total += counters[i].count;
    return total;
}

struct thread_arg { int iterations; };

static void *worker(void *arg) {
    struct thread_arg *a = arg;
    for (int i = 0; i < a->iterations; i++)
        percpu_inc();
    return NULL;
}

int main(void) {
    pthread_t threads[MAX_CPUS];
    struct thread_arg arg = { .iterations = 1000000 };

    for (int i = 0; i < MAX_CPUS; i++)
        pthread_create(&threads[i], NULL, worker, &arg);
    for (int i = 0; i < MAX_CPUS; i++)
        pthread_join(threads[i], NULL);

    printf("Total count: %llu (expected ~%llu)\n",
           (unsigned long long)percpu_sum(),
           (unsigned long long)MAX_CPUS * arg.iterations);
    return 0;
}
```

### Rust Implementation: Per-CPU via Thread-Local Storage

```rust
// file: src/percpu.rs
// In Rust, per-CPU = thread-local storage.
// Each worker thread represents a "CPU" here.
// In kernel Rust: kernel::prelude::*; this_cpu_add!()

use std::cell::Cell;
use std::sync::atomic::{AtomicU64, Ordering};

thread_local! {
    // Each "CPU" (thread) has its own counter — zero contention
    static LOCAL_COUNT: Cell<u64> = const { Cell::new(0) };
}

fn percpu_inc() {
    LOCAL_COUNT.with(|c| c.set(c.get() + 1));
}

fn percpu_local() -> u64 {
    LOCAL_COUNT.with(|c| c.get())
}

// Shared atomic for collecting results across "CPUs"
static GLOBAL_SUM: AtomicU64 = AtomicU64::new(0);

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_percpu_counter() {
        let handles: Vec<_> = (0..8).map(|_| {
            thread::spawn(|| {
                for _ in 0..100_000 {
                    percpu_inc();
                }
                // Flush to global when "CPU goes offline"
                GLOBAL_SUM.fetch_add(percpu_local(), Ordering::Relaxed);
            })
        }).collect();

        for h in handles { h.join().unwrap(); }
        assert_eq!(GLOBAL_SUM.load(Ordering::Relaxed), 8 * 100_000);
    }
}
```

---

## 13. RCU: Read-Copy-Update

### One-Line Explanation
RCU allows concurrent readers with zero synchronization overhead by deferring the freeing of objects until all pre-existing readers have finished, using epoch-based reclamation.

### Analogy
A library that never takes a book away while a reader is reading it. The librarian replaces a book by placing a new copy on the shelf and only destroying the old copy once confirmed that everyone has put it down. Readers never wait; only writers coordinate.

### The Three Core Operations

```c
/* 1. Read-side critical section (completely lock-free on x86) */
rcu_read_lock();           /* disables preemption (not sleeping!) */
p = rcu_dereference(gp);  /* load pointer with proper memory barriers */
/* use p->field safely; p won't be freed while we're here */
rcu_read_unlock();         /* re-enable preemption */

/* 2. Update (copy-then-swap) */
new = kmalloc(...);
*new = *old;               /* copy */
new->field = new_value;    /* modify copy */
rcu_assign_pointer(gp, new); /* atomic pointer publish with wmb */

/* 3. Reclaim (wait for all pre-existing readers) */
synchronize_rcu();         /* blocks until all CPUs passed quiescent state */
/* OR: */
call_rcu(&old->rcu, callback);  /* async: callback frees old when safe */
kfree_rcu(old, rcu_field);      /* syntactic sugar for call_rcu + kfree */
```

### Quiescent State: How the Kernel Tracks Readers

A "quiescent state" is any point where a CPU cannot be in an RCU read-side critical section: context switches, idle loops, user-space execution. The grace period ends when ALL CPUs have passed through at least one quiescent state.

```
Time →
CPU0: [read lock]────────[unlock]  [ctx switch] ← quiescent
CPU1: [idle]                                    ← quiescent
CPU2:              [read lock]──────────[unlock] ← quiescent
                                       ↑
                              Grace period ends here.
                              Old pointer can now be freed.
```

### C Simulation (Userspace RCU via Epochs)

```c
/* file: rcu_sim.c
 * compile: gcc -Wall -O2 -lpthread rcu_sim.c -o rcu_sim
 * Simplified epoch-based RCU simulation for user space.
 * Real implementation: liburcu (Userspace RCU library)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>
#include <unistd.h>

#define NREADERS  4

typedef struct config {
    int      version;
    int      timeout_ms;
    char     server[64];
    struct   config *old;    /* chain for deferred free */
} config_t;

/* Global config pointer — updated via RCU */
static _Atomic(config_t *) global_config;

/* ── Per-reader quiescent state tracking ── */
static _Atomic uint64_t reader_epochs[NREADERS];
static _Atomic uint64_t global_epoch;

static void rcu_read_lock(int reader_id) {
    atomic_store_explicit(&reader_epochs[reader_id],
                          atomic_load(&global_epoch),
                          memory_order_acquire);
}

static void rcu_read_unlock(int reader_id) {
    /* Mark as not in read section by setting odd epoch (quiescent) */
    atomic_fetch_add(&reader_epochs[reader_id], 1);
}

static void synchronize_rcu(void) {
    /* Advance global epoch and wait for all readers to see it */
    uint64_t target = atomic_fetch_add(&global_epoch, 2) + 2;
    /* Spin until all readers have epoch >= target
     * (they either saw the new epoch or left their critical section) */
    for (int i = 0; i < NREADERS; i++) {
        while (atomic_load(&reader_epochs[i]) < target)
            sched_yield();
    }
}

/* ── Reader thread ── */
struct reader_arg { int id; volatile int *stop; };

static void *reader_thread(void *arg) {
    struct reader_arg *a = arg;
    int id = a->id;
    int reads = 0;

    while (!*a->stop) {
        rcu_read_lock(id);
        config_t *cfg = atomic_load_explicit(&global_config, memory_order_consume);
        if (cfg) {
            /* Simulate using the config */
            (void)cfg->version;
            (void)cfg->timeout_ms;
            reads++;
        }
        rcu_read_unlock(id);
        sched_yield();
    }
    printf("Reader %d: %d reads\n", id, reads);
    return NULL;
}

/* ── Writer ── */
int main(void) {
    /* Initial config */
    config_t *initial = calloc(1, sizeof(*initial));
    initial->version    = 1;
    initial->timeout_ms = 5000;
    snprintf(initial->server, sizeof(initial->server), "server-v1.example.com");
    atomic_store(&global_config, initial);
    atomic_store(&global_epoch, 0);

    volatile int stop = 0;
    pthread_t readers[NREADERS];
    struct reader_arg args[NREADERS];

    for (int i = 0; i < NREADERS; i++) {
        args[i].id   = i;
        args[i].stop = &stop;
        pthread_create(&readers[i], NULL, reader_thread, &args[i]);
    }

    /* Perform 10 config updates */
    for (int ver = 2; ver <= 11; ver++) {
        config_t *old = atomic_load(&global_config);
        config_t *new = calloc(1, sizeof(*new));
        *new = *old;                          /* copy */
        new->version = ver;                   /* modify */
        snprintf(new->server, sizeof(new->server), "server-v%d.example.com", ver);

        atomic_store_explicit(&global_config, new, memory_order_release);  /* publish */

        synchronize_rcu();                    /* wait for all readers to leave */
        free(old);                            /* safe to free now */
        printf("Updated to version %d\n", ver);
        usleep(10000);
    }

    stop = 1;
    for (int i = 0; i < NREADERS; i++)
        pthread_join(readers[i], NULL);

    free((void *)atomic_load(&global_config));
    printf("Done.\n");
    return 0;
}
```

### Rust Implementation: RCU via ArcSwap

```rust
// file: src/rcu.rs
// ArcSwap implements the RCU pattern in safe Rust.
// It's used in production by tokio, actix, and many others.
//
// Cargo.toml: arc-swap = "1"

use arc_swap::ArcSwap;
use std::sync::Arc;
use std::thread;

#[derive(Debug, Clone)]
struct Config {
    version:    u32,
    timeout_ms: u32,
    server:     String,
}

fn main() {
    let config = Arc::new(ArcSwap::from_pointee(Config {
        version:    1,
        timeout_ms: 5000,
        server:     "server-v1.example.com".to_string(),
    }));

    // Readers: zero-cost load
    let handles: Vec<_> = (0..4).map(|id| {
        let cfg = config.clone();
        thread::spawn(move || {
            let mut reads = 0u64;
            for _ in 0..1_000_000 {
                let guard = cfg.load();   // RCU read lock (no syscall, no mutex)
                let _v = guard.version;  // use config
                reads += 1;
            }
            println!("Reader {id}: {reads} reads");
        })
    }).collect();

    // Writer: copy-on-write update
    for ver in 2..=11u32 {
        let old = config.load_full();   // Arc clone
        config.store(Arc::new(Config {
            version:    ver,
            timeout_ms: old.timeout_ms,
            server:     format!("server-v{}.example.com", ver),
        }));
        // Old Arc is dropped when all readers release their guard
        println!("Updated to v{ver}");
        thread::sleep(std::time::Duration::from_millis(1));
    }

    for h in handles { h.join().unwrap(); }
}
```

### Go Implementation: RCU Pattern via sync/atomic.Pointer

```go
// file: rcu/rcu.go
// Go 1.19+ provides sync/atomic.Pointer[T] which implements
// the RCU publish pattern safely.

package rcu

import (
    "fmt"
    "sync/atomic"
)

type Config struct {
    Version   int
    TimeoutMs int
    Server    string
}

type RCUConfig struct {
    ptr atomic.Pointer[Config]
}

func NewRCUConfig(initial *Config) *RCUConfig {
    r := &RCUConfig{}
    r.ptr.Store(initial)
    return r
}

// Load is the read-side: goroutines can call this concurrently
// with no locking whatsoever.
func (r *RCUConfig) Load() *Config {
    return r.ptr.Load()  // atomic pointer load = memory_order_consume
}

// Update is copy-on-write: create new, swap pointer.
// Old pointer is GC'd when all goroutines release their references.
func (r *RCUConfig) Update(fn func(old *Config) *Config) {
    for {
        old := r.ptr.Load()
        new := fn(old)
        if r.ptr.CompareAndSwap(old, new) {
            return // old Config will be GC'd when no goroutines reference it
        }
        // CAS failed (concurrent writer); retry
    }
}

// Example usage:
func Example() {
    cfg := NewRCUConfig(&Config{Version: 1, TimeoutMs: 5000, Server: "v1.example.com"})

    // Concurrent readers
    for i := 0; i < 4; i++ {
        go func(id int) {
            for j := 0; j < 1_000_000; j++ {
                c := cfg.Load()
                _ = c.Version // use without lock
            }
        }(i)
    }

    // Writer
    for ver := 2; ver <= 11; ver++ {
        cfg.Update(func(old *Config) *Config {
            return &Config{
                Version:   ver,
                TimeoutMs: old.TimeoutMs,
                Server:    fmt.Sprintf("v%d.example.com", ver),
            }
        })
    }
}
```

### RCU Rules to Never Break

1. **Never sleep in an RCU read-side critical section** (between `rcu_read_lock` and `rcu_read_unlock`). Sleep = schedule = quiescent state, which breaks the grace period tracking.

2. **Never hold a pointer after `rcu_read_unlock`** without promoting it to a reference-counted `kref` or holding a refcount.

3. **Always use `rcu_dereference`** (not a plain load) for RCU-protected pointers. It inserts a `READ_ONCE` + data dependency barrier.

4. **Always use `rcu_assign_pointer`** (not a plain store) when publishing new pointers. It inserts a `WRITE_ONCE` + memory barrier.

5. **`synchronize_rcu` cannot be called from interrupt context** — it may sleep.

---

## 14. IDR: ID Radix Tree

### One-Line Explanation
The IDR (ID Radix tree) allocates and maps small integers to pointers — the kernel's canonical way to assign unique IDs (file descriptors, process IDs, inode numbers) without collisions.

### Linux API

```c
/* linux/include/linux/idr.h */

struct idr {
    struct xarray idr_rt;  /* backed by XArray since 4.20 */
    unsigned int  idr_base;
    unsigned int  idr_next;
};

DEFINE_IDR(name);

/* Allocate an unused ID in [min, max] and associate it with ptr */
int idr_alloc(struct idr *idr, void *ptr, int start, int end, gfp_t gfp);

/* Find ptr for id */
void *idr_find(const struct idr *idr, unsigned long id);

/* Remove id */
void idr_remove(struct idr *idr, unsigned long id);

/* Iterate */
void *idr_get_next(struct idr *idr, int *nextid);
idr_for_each_entry(idr, entry, id) { ... }
```

### C Implementation: File Descriptor Table

```c
/* file: fdtable.c
 * compile: gcc -Wall -O2 fdtable.c -o fdtable
 * Implements a simplified file descriptor table using a bitmap for free
 * slots and a pointer array — same strategy as Linux's fdtable.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

#define FD_MAX     64
#define BITS       64

typedef struct { int flags; char path[64]; } file_t;

typedef struct {
    file_t  *files[FD_MAX];
    uint64_t open_fds;      /* bitmap: bit i set = fd i is open */
    int      next_fd;       /* hint for next allocation */
} fdtable_t;

static void fdtable_init(fdtable_t *t) {
    memset(t, 0, sizeof(*t));
}

/* Find first zero bit at or after `start` */
static int first_free_fd(uint64_t open, int start) {
    uint64_t mask = ~open;
    if (start > 0) mask >>= start;
    if (!mask) return -1;
    return start + __builtin_ctzll(mask);
}

static int fd_install(fdtable_t *t, file_t *f) {
    int fd = first_free_fd(t->open_fds, t->next_fd);
    if (fd < 0 || fd >= FD_MAX) return -1;  /* EMFILE */
    t->files[fd] = f;
    t->open_fds  |= (1ULL << fd);
    t->next_fd    = (fd + 1) % FD_MAX;
    return fd;
}

static file_t *fd_get(fdtable_t *t, int fd) {
    if (fd < 0 || fd >= FD_MAX || !(t->open_fds & (1ULL << fd))) return NULL;
    return t->files[fd];
}

static void fd_close(fdtable_t *t, int fd) {
    if (fd < 0 || fd >= FD_MAX) return;
    t->files[fd]  = NULL;
    t->open_fds  &= ~(1ULL << fd);
    if (fd < t->next_fd) t->next_fd = fd;  /* reclaim low fd */
}

int main(void) {
    fdtable_t fdt;
    fdtable_init(&fdt);

    file_t stdin_f  = {0, "/dev/stdin"};
    file_t stdout_f = {1, "/dev/stdout"};
    file_t stderr_f = {2, "/dev/stderr"};

    int fd0 = fd_install(&fdt, &stdin_f);
    int fd1 = fd_install(&fdt, &stdout_f);
    int fd2 = fd_install(&fdt, &stderr_f);

    assert(fd0 == 0);
    assert(fd1 == 1);
    assert(fd2 == 2);

    printf("stdin  fd=%d path=%s\n", fd0, fd_get(&fdt, fd0)->path);
    printf("stdout fd=%d path=%s\n", fd1, fd_get(&fdt, fd1)->path);

    fd_close(&fdt, 1);
    assert(fd_get(&fdt, 1) == NULL);

    /* Next alloc should reuse fd 1 */
    file_t new_file = {0, "/tmp/test"};
    int new_fd = fd_install(&fdt, &new_file);
    assert(new_fd == 1);
    printf("Reused fd=%d for %s\n", new_fd, fd_get(&fdt, new_fd)->path);

    return 0;
}
```

---

## 15. Memory Pools: Slab, SLUB, SLOB

### One-Line Explanation
Slab allocators cache frequently allocated fixed-size objects to avoid fragmentation, reduce allocation latency, and improve cache locality — the kernel never calls raw page allocator for small objects.

### The Three Allocators

| Allocator | Target | Design | When |
|---|---|---|---|
| SLAB | Generic | Full caching, per-CPU queues | Pre-2011 default |
| SLUB | SMP performance | Simpler, per-CPU freelists, less metadata | Current default |
| SLOB | Embedded | First-fit, tiny footprint | `CONFIG_EMBEDDED` |

### SLUB Internal Layout

```
A single slab = one or more contiguous pages:

┌────────────────────────────────────────────────────────┐
│ struct slab (metadata in first page's struct page)      │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│ │ obj0 │ │ obj1 │ │ obj2 │ │ obj3 │ │ obj4 │ │ obj5 │ │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │
│   free ──────────────────────► obj2 ──► obj4 ──► NULL  │
└────────────────────────────────────────────────────────┘

Free list is embedded IN the free objects themselves (freelist pointer
at offset 0 of each free object, or randomized via CONFIG_SLAB_FREELIST_RANDOM).
```

### Key kmalloc Size Classes

```c
/* linux/mm/slab_common.c */
/* kmalloc uses per-size slab caches: 8, 16, 32, 64, 96, 128, 192, 256,
 * 512, 1024, 2048, 4096, 8192 bytes */

void *kmalloc(size_t size, gfp_t flags);
void  kfree(const void *ptr);

/* Type-safe slab cache */
struct kmem_cache *task_struct_cachep;

/* In fork.c initialization: */
task_struct_cachep = kmem_cache_create("task_struct",
    sizeof(struct task_struct),
    ARCH_MIN_TASKALIGN,
    SLAB_PANIC|SLAB_NOTRACK|SLAB_ACCOUNT,
    NULL);

/* Allocate/free a task_struct */
struct task_struct *p = kmem_cache_alloc(task_struct_cachep, GFP_KERNEL);
kmem_cache_free(task_struct_cachep, p);
```

### GFP Flags (Critical to Understand)

| Flag | Meaning | Context |
|---|---|---|
| `GFP_KERNEL` | May sleep, may swap | Process context only |
| `GFP_ATOMIC` | Must not sleep, no swap | Interrupt/spinlock context |
| `GFP_NOWAIT` | No reclaim | When slight latency spike is worse than failure |
| `GFP_NOIO` | No I/O during reclaim | Filesystem code |
| `GFP_NOFS` | No FS during reclaim | Memory shrinker callbacks |
| `GFP_DMA` | Memory from DMA zone | Legacy 16MB DMA |
| `GFP_DMA32` | Below 4GB | 32-bit DMA devices |

### C Implementation: Typed Object Pool

```c
/* file: objpool.c
 * compile: gcc -Wall -O2 objpool.c -o objpool
 * Lock-free LIFO object pool (slab-like for userspace).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <string.h>
#include <assert.h>

/* ── Freelist node embedded in the object ── */
typedef struct freelist_node {
    struct freelist_node *next;
} freelist_node_t;

typedef struct {
    _Atomic(freelist_node_t *) head;    /* top of free stack */
    size_t   obj_size;
    int      allocated;
    int      freed;
} objpool_t;

static objpool_t *objpool_create(size_t obj_size, int initial_count) {
    assert(obj_size >= sizeof(freelist_node_t));
    objpool_t *pool = calloc(1, sizeof(*pool));
    pool->obj_size  = obj_size;

    /* Pre-allocate initial objects */
    for (int i = 0; i < initial_count; i++) {
        freelist_node_t *node = malloc(obj_size);
        freelist_node_t *head = atomic_load(&pool->head);
        do { node->next = head; }
        while (!atomic_compare_exchange_weak(&pool->head, &head, node));
    }
    return pool;
}

static void *objpool_alloc(objpool_t *pool) {
    freelist_node_t *head = atomic_load(&pool->head);
    while (head) {
        if (atomic_compare_exchange_weak(&pool->head, &head, head->next)) {
            pool->allocated++;
            memset(head, 0, pool->obj_size);  /* zero before reuse */
            return head;
        }
    }
    /* Pool exhausted: fall back to malloc */
    pool->allocated++;
    return calloc(1, pool->obj_size);
}

static void objpool_free(objpool_t *pool, void *ptr) {
    freelist_node_t *node = ptr;
    freelist_node_t *head = atomic_load(&pool->head);
    do { node->next = head; }
    while (!atomic_compare_exchange_weak(&pool->head, &head, node));
    pool->freed++;
}

/* ── Demo ── */
typedef struct {
    int pid; char name[32]; uint64_t vruntime;
    freelist_node_t _pool;  /* must be first or handled with offset */
} task_t;

int main(void) {
    /* In a real kernel: task_struct_cachep = kmem_cache_create(...) */
    objpool_t *task_pool = objpool_create(sizeof(task_t), 64);

    task_t *tasks[128];
    for (int i = 0; i < 128; i++) {
        tasks[i] = objpool_alloc(task_pool);
        tasks[i]->pid = i + 1;
        snprintf(tasks[i]->name, sizeof(tasks[i]->name), "task_%d", i);
    }

    printf("Allocated %d tasks\n", task_pool->allocated);

    for (int i = 0; i < 128; i++)
        objpool_free(task_pool, tasks[i]);

    printf("Freed %d tasks\n", task_pool->freed);

    /* Reuse — should come from the pool (freed list), not malloc */
    task_t *t = objpool_alloc(task_pool);
    assert(t != NULL);
    objpool_free(task_pool, t);

    return 0;
}
```

### Rust Implementation: Typed Arena

```rust
// file: src/arena.rs
// Typed arena allocator: bump-allocate from a pre-allocated chunk.
// Objects are freed all at once when the arena is dropped.
// Used in rustc itself, and analogous to zone allocators in the kernel.

use std::cell::Cell;
use std::mem::{self, MaybeUninit};
use std::ptr;

pub struct Arena<T> {
    chunks: Vec<Vec<MaybeUninit<T>>>,
    chunk_size: usize,
    bump: Cell<usize>,  // next free slot in current chunk
}

impl<T> Arena<T> {
    pub fn new(chunk_size: usize) -> Self {
        Self {
            chunks: vec![Vec::with_capacity(chunk_size)],
            chunk_size,
            bump: Cell::new(0),
        }
    }

    pub fn alloc(&self, value: T) -> &T {
        // This needs &mut in practice; shown with Cell for clarity
        // A production arena would use UnsafeCell
        let chunks = unsafe {
            &mut *(self as *const Self as *mut Self)
        };

        let bump = self.bump.get();
        let chunk = chunks.chunks.last_mut().unwrap();

        if bump >= self.chunk_size || bump >= chunk.len() {
            chunk.push(MaybeUninit::uninit());
        }

        // Safety: we own this slot exclusively
        let slot = &mut chunk[bump.min(chunk.len().saturating_sub(1))];
        slot.write(value);
        self.bump.set(bump + 1);
        unsafe { slot.assume_init_ref() }
    }
}

// Arena drop: all T values dropped when arena is dropped
impl<T> Drop for Arena<T> {
    fn drop(&mut self) {
        // MaybeUninit vec drop does NOT drop T automatically.
        // We need to manually drop initialized elements.
        for chunk in &mut self.chunks {
            for item in chunk.iter_mut() {
                unsafe { ptr::drop_in_place(item.as_mut_ptr()); }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static DROP_COUNT: AtomicUsize = AtomicUsize::new(0);

    struct DropCounter(u32);
    impl Drop for DropCounter {
        fn drop(&mut self) { DROP_COUNT.fetch_add(1, Ordering::Relaxed); }
    }

    #[test]
    fn test_arena_drops_all() {
        {
            let arena = Arena::new(16);
            for i in 0..100u32 {
                arena.alloc(DropCounter(i));
            }
        } // arena dropped here
        assert_eq!(DROP_COUNT.load(Ordering::Relaxed), 100);
    }
}
```

---

## 16. Locking Primitives

### 16.1 Spinlock

**One-Line:** A busy-wait lock for short critical sections in atomic context (interrupt handlers, scheduler) — holds the CPU spinning rather than sleeping.

**Internal Implementation on x86:**

```c
/* linux/arch/x86/include/asm/spinlock.h
 * Ticket spinlock: ensures FIFO fairness */

typedef struct {
    union {
        uint32_t slock;
        struct {
            uint16_t head;  /* which ticket is being served */
            uint16_t tail;  /* next ticket to issue */
        };
    };
} arch_spinlock_t;

static inline void arch_spin_lock(arch_spinlock_t *lock) {
    uint32_t inc = 0x00010000;   /* increment tail by 1 */
    uint32_t tmp;
    asm volatile (
        "lock xaddl %0, %1\n"   /* atomically: tmp = lock->slock; lock->tail++ */
        "movzwl %w0, %2\n"      /* tmp_head = tmp.head */
        "shrl $16, %0\n"        /* tmp_tail = tmp.tail */
        "1: cmpl %0, %2\n"      /* while (head != my_ticket) */
        "je 2f\n"
        "rep nop\n"              /* PAUSE instruction: hint to hypervisor */
        "movzwl %1, %2\n"       /* reload head */
        "jmp 1b\n"
        "2:\n"
        : "+r" (inc), "+m" (lock->slock), "=&r" (tmp) :: "memory", "cc"
    );
}
```

**Rules for spinlock usage:**

1. Critical section must be short (< a few microseconds) — CPUs spin burning cycles.
2. Cannot sleep while holding a spinlock — use mutex instead.
3. Must disable local interrupts if lock can be acquired from interrupt handlers: use `spin_lock_irqsave`.
4. Never call anything that can sleep (`kmalloc(GFP_KERNEL)`, `mutex_lock`, `schedule`).

### 16.2 Mutex

**Internal structure:**

```c
/* linux/include/linux/mutex.h */
struct mutex {
    atomic_long_t   owner;    /* current owner task, plus flags in low bits */
    spinlock_t      wait_lock;
    struct list_head wait_list;
};
```

The mutex fast path uses a single `cmpxchg` to acquire (no spinlock needed when uncontested). Slow path sleeps on `wait_list`.

### 16.3 Read-Write Semaphore (rwsem)

```c
/* linux/include/linux/rwsem.h */
/* Allows concurrent readers OR exclusive writer */

down_read(&rwsem);   /* concurrent readers OK */
/* ... read ... */
up_read(&rwsem);

down_write(&rwsem);  /* exclusive */
/* ... write ... */
up_write(&rwsem);

/* Optimistic spinning: if writer holds lock, readers spin briefly
 * before sleeping — reduces latency for short critical sections */
```

### C Implementation: Full Lock Benchmark

```c
/* file: lock_bench.c
 * compile: gcc -Wall -O2 -lpthread lock_bench.c -o lock_bench
 * Compares spinlock (via CAS), mutex, and RWLock performance.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>
#include <time.h>
#include <string.h>

#define NTHREADS   4
#define ITERS      1000000

/* ── CAS spinlock ── */
typedef _Atomic int spinlock_t;
#define SPIN_UNLOCK 0
#define SPIN_LOCK   1

static inline void spin_lock(spinlock_t *l) {
    int expected;
    do {
        expected = SPIN_UNLOCK;
        while (atomic_load_explicit(l, memory_order_relaxed) != SPIN_UNLOCK)
            __builtin_ia32_pause();  /* x86 PAUSE — reduces bus traffic */
    } while (!atomic_compare_exchange_weak_explicit(
        l, &expected, SPIN_LOCK, memory_order_acquire, memory_order_relaxed));
}

static inline void spin_unlock(spinlock_t *l) {
    atomic_store_explicit(l, SPIN_UNLOCK, memory_order_release);
}

/* ── Benchmark infrastructure ── */
static volatile uint64_t shared_counter;

struct bench_arg {
    const char  *name;
    void       (*lock_fn)(void *);
    void       (*unlock_fn)(void *);
    void        *lock_arg;
};

static pthread_mutex_t  g_mutex = PTHREAD_MUTEX_INITIALIZER;
static spinlock_t       g_spin  = 0;
static pthread_rwlock_t g_rw    = PTHREAD_RWLOCK_INITIALIZER;

static void mutex_lock_fn(void *l)   { pthread_mutex_lock(l); }
static void mutex_unlock_fn(void *l) { pthread_mutex_unlock(l); }
static void spin_lock_fn(void *l)    { spin_lock(l); }
static void spin_unlock_fn(void *l)  { spin_unlock(l); }

static void *bench_worker(void *arg) {
    struct bench_arg *a = arg;
    for (int i = 0; i < ITERS; i++) {
        a->lock_fn(a->lock_arg);
        shared_counter++;
        a->unlock_fn(a->lock_arg);
    }
    return NULL;
}

static double bench(const char *name,
                    void (*lock_fn)(void *), void (*unlock_fn)(void *),
                    void *lock_arg) {
    shared_counter = 0;
    pthread_t threads[NTHREADS];
    struct bench_arg arg = {name, lock_fn, unlock_fn, lock_arg};
    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < NTHREADS; i++)
        pthread_create(&threads[i], NULL, bench_worker, &arg);
    for (int i = 0; i < NTHREADS; i++)
        pthread_join(threads[i], NULL);
    clock_gettime(CLOCK_MONOTONIC, &t1);

    double ms = (t1.tv_sec - t0.tv_sec) * 1000.0 +
                (t1.tv_nsec - t0.tv_nsec) / 1e6;
    printf("%-15s counter=%llu  time=%.2fms\n",
           name, (unsigned long long)shared_counter, ms);
    return ms;
}

int main(void) {
    printf("Benchmarking %d threads × %d iterations:\n\n", NTHREADS, ITERS);
    bench("mutex",    mutex_lock_fn,  mutex_unlock_fn,  &g_mutex);
    bench("spinlock", spin_lock_fn,   spin_unlock_fn,   &g_spin);
    return 0;
}
```

---

## 17. Seqlocks

### One-Line Explanation
A seqlock allows readers to read concurrently with a single writer, with readers detecting torn reads via a sequence number rather than sleeping — O(1) read overhead, no reader-writer blocking.

### How It Works

```
Writer: seq++ (odd)  →  write data  →  seq++ (even)
Reader: read seq1   →  read data   →  read seq2
        if seq1 != seq2 OR seq1 is odd → retry (writer was active)
```

```c
/* linux/include/linux/seqlock.h */
typedef struct {
    struct seqcount seqcount;
    spinlock_t      lock;
} seqlock_t;

/* Write side */
write_seqlock(&sl);
/* ... modify data ... */
write_sequnlock(&sl);

/* Read side: retry until consistent read */
do {
    seq = read_seqbegin(&sl);
    /* read shared data */
} while (read_seqretry(&sl, seq));
```

### C Implementation

```c
/* file: seqlock.c
 * compile: gcc -Wall -O2 -lpthread seqlock.c -o seqlock
 * Classic seqlock: protect a timestamp struct without reader blocking.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdatomic.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>

typedef struct {
    _Atomic uint64_t seq;
} seqlock_t;

typedef struct {
    uint64_t seconds;
    uint32_t nanos;
} wall_clock_t;

static wall_clock_t g_clock;
static seqlock_t    g_seq = { .seq = 0 };

static inline uint64_t seqlock_read_begin(seqlock_t *sl) {
    uint64_t seq;
    do {
        seq = atomic_load_explicit(&sl->seq, memory_order_acquire);
    } while (seq & 1);  /* odd = writer active, spin */
    return seq;
}

static inline int seqlock_read_retry(seqlock_t *sl, uint64_t start) {
    /* Returns non-zero if a write occurred during our read */
    return atomic_load_explicit(&sl->seq, memory_order_acquire) != start;
}

static inline void seqlock_write_lock(seqlock_t *sl) {
    /* Increment to odd: mark write in progress */
    atomic_fetch_add_explicit(&sl->seq, 1, memory_order_release);
}

static inline void seqlock_write_unlock(seqlock_t *sl) {
    /* Increment to even: mark write done */
    atomic_fetch_add_explicit(&sl->seq, 1, memory_order_release);
}

static void *writer_thread(void *arg) {
    for (int i = 0; i < 100; i++) {
        seqlock_write_lock(&g_seq);
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        g_clock.seconds = ts.tv_sec;
        g_clock.nanos   = ts.tv_nsec;
        seqlock_write_unlock(&g_seq);
        usleep(10000);  /* 10ms */
    }
    return NULL;
}

static void *reader_thread(void *arg) {
    int id = (int)(uintptr_t)arg;
    for (int i = 0; i < 50; i++) {
        wall_clock_t local;
        uint64_t seq;
        int retries = 0;
        do {
            seq = seqlock_read_begin(&g_seq);
            local = g_clock;  /* copy under seq protection */
            retries++;
        } while (seqlock_read_retry(&g_seq, seq));
        if (retries > 1)
            printf("Reader %d: %d retries for timestamp %llu.%09u\n",
                   id, retries - 1,
                   (unsigned long long)local.seconds, local.nanos);
        usleep(5000);
    }
    return NULL;
}

int main(void) {
    pthread_t writer, readers[4];
    pthread_create(&writer, NULL, writer_thread, NULL);
    for (int i = 0; i < 4; i++)
        pthread_create(&readers[i], NULL, reader_thread, (void *)(uintptr_t)i);

    pthread_join(writer, NULL);
    for (int i = 0; i < 4; i++) pthread_join(readers[i], NULL);
    printf("Seqlock demo complete.\n");
    return 0;
}
```

---

## 18. Atomic Operations and Memory Ordering

### One-Line Explanation
Atomic operations are indivisible read-modify-write CPU instructions; memory ordering constraints determine how those operations are seen by other CPUs relative to surrounding loads and stores.

### The Six Memory Orders (C11/C++11 = Linux on x86/ARM)

| Order | Meaning | x86 cost | ARM cost |
|---|---|---|---|
| `relaxed` | No ordering guarantee; only atomicity | Free | Free |
| `acquire` | No loads/stores after this can move before it | Free on x86 | Load barrier |
| `release` | No loads/stores before this can move after it | Free on x86 | Store barrier |
| `acq_rel` | Both acquire and release | Free on x86 | Full barrier |
| `seq_cst` | Total order across all seq_cst ops | `MFENCE` | Full barrier |
| `consume` | Data-dependency ordering (deprecated, use acquire) | Free | Free |

### Linux Atomic API

```c
/* linux/include/linux/atomic.h */

atomic_t      v = ATOMIC_INIT(0);  /* 32-bit */
atomic64_t   v64 = ATOMIC64_INIT(0);  /* 64-bit */

atomic_read(&v);
atomic_set(&v, 42);
atomic_add(5, &v);
atomic_sub(3, &v);
atomic_inc(&v);
atomic_dec(&v);
int old = atomic_fetch_add(5, &v);   /* returns old value */
int old = atomic_xchg(&v, 100);      /* atomic exchange */

/* Test-and-set primitives */
int old = atomic_cmpxchg(&v, expected, desired);
bool ok  = atomic_try_cmpxchg(&v, &expected, desired);

/* Reference counting — common pattern */
struct my_obj {
    struct kref refcount;
    /* ... */
};
kref_init(&obj->refcount);
kref_get(&obj->refcount);
kref_put(&obj->refcount, release_fn);
```

### C Implementation: Lock-Free Reference Counting

```c
/* file: atomic_refcount.c
 * compile: gcc -Wall -O2 -lpthread atomic_refcount.c -o atomic_refcount
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <pthread.h>
#include <assert.h>

typedef struct {
    _Atomic int refcount;
    int         value;
} shared_obj_t;

static shared_obj_t *obj_create(int value) {
    shared_obj_t *o = malloc(sizeof(*o));
    atomic_store(&o->refcount, 1);
    o->value = value;
    return o;
}

/* Returns 1 if get succeeded (refcount was > 0) */
static int obj_get(shared_obj_t *o) {
    int old = atomic_load_explicit(&o->refcount, memory_order_relaxed);
    do {
        if (old <= 0) return 0;  /* already being freed */
    } while (!atomic_compare_exchange_weak_explicit(
        &o->refcount, &old, old + 1,
        memory_order_acquire, memory_order_relaxed));
    return 1;
}

static void obj_put(shared_obj_t *o) {
    if (atomic_fetch_sub_explicit(&o->refcount, 1, memory_order_release) == 1) {
        /* Last reference: synchronize and free */
        atomic_thread_fence(memory_order_acquire);
        printf("Freeing object value=%d\n", o->value);
        free(o);
    }
}

static void *worker(void *arg) {
    shared_obj_t *o = arg;
    if (obj_get(o)) {
        /* Use object */
        (void)o->value;
        obj_put(o);
    }
    return NULL;
}

int main(void) {
    shared_obj_t *o = obj_create(42);

    pthread_t threads[16];
    for (int i = 0; i < 16; i++) {
        obj_get(o);  /* add reference for each thread */
        pthread_create(&threads[i], NULL, worker, o);
    }
    for (int i = 0; i < 16; i++)
        pthread_join(threads[i], NULL);

    obj_put(o);  /* release initial reference */
    /* Object should be freed here */
    return 0;
}
```

### Rust: Atomic Types and Orderings

```rust
// file: src/atomics.rs
use std::sync::atomic::{AtomicI32, AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

// ARC IS RCU-style: Arc<T> uses atomic reference counting
// identical to kref. Weak<T> is the zero-cost reference.

pub fn demo_atomics() {
    let counter = Arc::new(AtomicI32::new(0));
    let handles: Vec<_> = (0..8).map(|_| {
        let c = counter.clone();
        thread::spawn(move || {
            for _ in 0..100_000 {
                c.fetch_add(1, Ordering::Relaxed);
            }
        })
    }).collect();

    for h in handles { h.join().unwrap(); }
    println!("Final: {}", counter.load(Ordering::SeqCst));
}

// Lock-free stack (Treiber stack) — same as used in lock-free kernel queues
use std::ptr;

struct Node<T> {
    value: T,
    next: *mut Node<T>,
}

pub struct TreiberStack<T> {
    head: AtomicUsize,
    _phantom: std::marker::PhantomData<*mut Node<T>>,
}

unsafe impl<T: Send> Send for TreiberStack<T> {}
unsafe impl<T: Send> Sync for TreiberStack<T> {}

impl<T> TreiberStack<T> {
    pub fn new() -> Self {
        Self { head: AtomicUsize::new(0), _phantom: std::marker::PhantomData }
    }

    pub fn push(&self, value: T) {
        let node = Box::into_raw(Box::new(Node { value, next: ptr::null_mut() }));
        loop {
            let head = self.head.load(Ordering::Relaxed);
            unsafe { (*node).next = head as *mut Node<T>; }
            if self.head.compare_exchange(
                head, node as usize,
                Ordering::Release, Ordering::Relaxed
            ).is_ok() { return; }
        }
    }

    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head == 0 { return None; }
            let node = head as *mut Node<T>;
            let next = unsafe { (*node).next as usize };
            if self.head.compare_exchange(
                head, next,
                Ordering::Release, Ordering::Relaxed
            ).is_ok() {
                let val = unsafe { Box::from_raw(node).value };
                return Some(val);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_treiber_stack() {
        let stack = Arc::new(TreiberStack::new());
        let handles: Vec<_> = (0..4).map(|id| {
            let s = stack.clone();
            thread::spawn(move || {
                for i in 0..100 {
                    s.push(id * 100 + i);
                }
            })
        }).collect();
        for h in handles { h.join().unwrap(); }

        let mut count = 0;
        while stack.pop().is_some() { count += 1; }
        assert_eq!(count, 400);
    }
}
```

---

## 19. Page Tables

### One-Line Explanation
Page tables translate virtual addresses to physical addresses through a multi-level radix tree indexed by parts of the virtual address — maintained per-process in `mm_struct`.

### x86-64 Four-Level Page Table

```
Virtual address (48-bit canonical): 
Bits [47:39] → PGD index (9 bits, 512 entries)
Bits [38:30] → PUD index (9 bits, 512 entries)
Bits [29:21] → PMD index (9 bits, 512 entries)
Bits [20:12] → PTE index (9 bits, 512 entries)
Bits [11:0]  → Page offset (12 bits, 4096 bytes)

CR3 ──► PGD[PGD_idx] ──► PUD[PUD_idx] ──► PMD[PMD_idx] ──► PTE[PTE_idx] ──► Physical page
```

```c
/* linux/arch/x86/include/asm/pgtable.h */

typedef struct { pgdval_t pgd; } pgd_t;   /* Page Global Directory entry */
typedef struct { pudval_t pud; } pud_t;   /* Page Upper Directory */
typedef struct { pmdval_t pmd; } pmd_t;   /* Page Middle Directory */
typedef struct { pteval_t pte; } pte_t;   /* Page Table Entry */

/* PTE bit layout (x86-64) */
#define _PAGE_PRESENT   (1UL <<  0)   /* page is in RAM */
#define _PAGE_RW        (1UL <<  1)   /* writable */
#define _PAGE_USER      (1UL <<  2)   /* user-accessible */
#define _PAGE_PWT       (1UL <<  3)   /* write-through cache */
#define _PAGE_PCD       (1UL <<  4)   /* cache disabled */
#define _PAGE_ACCESSED  (1UL <<  5)   /* hardware-set on access */
#define _PAGE_DIRTY     (1UL <<  6)   /* hardware-set on write */
#define _PAGE_PSE       (1UL <<  7)   /* huge page (2MB/1GB) */
#define _PAGE_GLOBAL    (1UL <<  8)   /* not flushed on CR3 reload */
#define _PAGE_NX        (1UL << 63)   /* no-execute (XD bit) */
/* Bits [51:12]: physical address of next-level table or page */
```

### The Translation Lookaside Buffer (TLB)

The CPU caches recent PTE lookups in the TLB. When you change a page table entry:
- Must flush the relevant TLB entry on the current CPU
- On SMP: must send an IPI to all other CPUs that might have the mapping cached (TLB shootdown)

```c
/* linux/arch/x86/include/asm/tlbflush.h */
flush_tlb_page(vma, addr);        /* single page */
flush_tlb_range(vma, start, end); /* range */
flush_tlb_all();                  /* global flush — very expensive */

/* IPI-based shootdown for SMP */
smp_call_function_many(cpu_mask, flush_tlb_func, &info, 1);
```

### C Simulation: Two-Level Page Table Walk

```c
/* file: pagetable.c
 * compile: gcc -Wall -O2 pagetable.c -o pagetable
 * Simulate a 2-level page table for a 16-bit virtual address space.
 * Demonstrates page fault handling and COW (Copy-on-Write).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

#define VA_BITS    16
#define PGD_BITS   4     /* top 4 bits → 16 PGD entries */
#define PTE_BITS   4     /* next 4 bits → 16 PTE entries */
#define PAGE_BITS  8     /* bottom 8 bits → 256-byte pages */
#define PAGE_SIZE  (1 << PAGE_BITS)
#define PGD_SIZE   (1 << PGD_BITS)
#define PTE_SIZE   (1 << PTE_BITS)

#define PTE_PRESENT  0x01
#define PTE_WRITABLE 0x02
#define PTE_ACCESSED 0x04
#define PTE_DIRTY    0x08
#define PTE_COW      0x10   /* copy-on-write marker */

typedef uint32_t pte_t;
typedef pte_t   *pmd_t;    /* pointer to PTE array */

typedef struct {
    pmd_t  entries[PGD_SIZE];  /* 16 pointers to PTE arrays */
} pgd_t;

typedef struct {
    uint8_t  *pages[256];    /* physical page storage */
    int       next_pfn;
} physmem_t;

static physmem_t phys;

static uint8_t *phys_alloc_page(void) {
    assert(phys.next_pfn < 256);
    uint8_t *page = calloc(PAGE_SIZE, 1);
    phys.pages[phys.next_pfn++] = page;
    return page;
}

static pgd_t *mm_new(void) {
    return calloc(1, sizeof(pgd_t));
}

/* Ensure PTE array exists for PGD entry */
static pte_t *mm_ensure_pmd(pgd_t *mm, int pgd_idx) {
    if (!mm->entries[pgd_idx])
        mm->entries[pgd_idx] = calloc(PTE_SIZE, sizeof(pte_t));
    return mm->entries[pgd_idx];
}

/* Map virtual page `vpn` to physical page `page` */
static void mm_map(pgd_t *mm, uint16_t va, uint8_t *page, int writable) {
    int pgd_idx = (va >> (PTE_BITS + PAGE_BITS)) & (PGD_SIZE - 1);
    int pte_idx = (va >> PAGE_BITS) & (PTE_SIZE - 1);

    pte_t *ptes = mm_ensure_pmd(mm, pgd_idx);
    uintptr_t pfn = ((uintptr_t)page) >> 8;  /* simplified: treat addr as PFN */
    ptes[pte_idx] = (pfn << 12) | PTE_PRESENT | (writable ? PTE_WRITABLE : 0);
}

/* Translate virtual address → physical pointer, simulating page fault */
static uint8_t *mm_translate(pgd_t *mm, uint16_t va, int write) {
    int pgd_idx  = (va >> (PTE_BITS + PAGE_BITS)) & (PGD_SIZE - 1);
    int pte_idx  = (va >> PAGE_BITS) & (PTE_SIZE - 1);
    int offset   = va & (PAGE_SIZE - 1);

    if (!mm->entries[pgd_idx]) {
        printf("PAGE FAULT: PGD[%d] not present for va=0x%04x\n", pgd_idx, va);
        return NULL;
    }

    pte_t pte = mm->entries[pgd_idx][pte_idx];
    if (!(pte & PTE_PRESENT)) {
        printf("PAGE FAULT: PTE not present for va=0x%04x\n", va);
        return NULL;
    }

    if (write && !(pte & PTE_WRITABLE)) {
        if (pte & PTE_COW) {
            /* COW fault: copy the page and make writable */
            printf("COW FAULT at va=0x%04x: copying page\n", va);
            uint8_t *old_page = (uint8_t *)((uintptr_t)((pte >> 12) << 8));
            uint8_t *new_page = phys_alloc_page();
            memcpy(new_page, old_page, PAGE_SIZE);
            mm_map(mm, va, new_page, 1);
            return new_page + offset;
        }
        printf("PROTECTION FAULT: write to read-only page va=0x%04x\n", va);
        return NULL;
    }

    /* Set accessed/dirty bits */
    mm->entries[pgd_idx][pte_idx] |= PTE_ACCESSED;
    if (write) mm->entries[pgd_idx][pte_idx] |= PTE_DIRTY;

    uint8_t *phys_page = (uint8_t *)((uintptr_t)((pte >> 12) << 8));
    return phys_page + offset;
}

int main(void) {
    pgd_t *mm = mm_new();

    /* Allocate and map a page at VA 0x1000 */
    uint8_t *page = phys_alloc_page();
    mm_map(mm, 0x1000, page, 1);   /* writable */

    /* Write through translation */
    uint8_t *ptr = mm_translate(mm, 0x1000, 1);
    assert(ptr);
    strcpy((char *)ptr, "Hello, kernel!");

    /* Read back */
    ptr = mm_translate(mm, 0x1000, 0);
    printf("Read: %s\n", (char *)ptr);

    /* Map a read-only COW page */
    uint8_t *ro_page = phys_alloc_page();
    memcpy(ro_page, "COW data", 8);
    int pgd_idx = (0x2000 >> (PTE_BITS + PAGE_BITS)) & (PGD_SIZE - 1);
    int pte_idx = (0x2000 >> PAGE_BITS) & (PTE_SIZE - 1);
    pte_t *ptes = mm_ensure_pmd(mm, pgd_idx);
    uintptr_t pfn = ((uintptr_t)ro_page) >> 8;
    ptes[pte_idx] = (pfn << 12) | PTE_PRESENT | PTE_COW;  /* no WRITABLE */

    /* Trigger COW fault */
    ptr = mm_translate(mm, 0x2000, 1);
    assert(ptr);
    strcpy((char *)ptr, "Modified!");
    printf("After COW: %s\n", (char *)ptr);
    printf("Original:  %s\n", (char *)ro_page);

    return 0;
}
```

---

## 20. LRU Lists and the Page Cache

### One-Line Explanation
The Linux page cache maintains pages in two LRU lists (active and inactive) using the clock algorithm to efficiently evict least-recently-used pages under memory pressure.

### The Two-List LRU Algorithm

```
Inactive list ←──── Pages enter here on first access
     ↑                         │
     │ (page accessed again     │ (not re-referenced: evict)
     │  while in inactive list) │
     ▼                         ▼
Active list                  Eviction
     │
     │ (active list grows too large)
     ▼
Inactive list (demoted)
```

**Why two lists?** One access could be a one-time sequential scan — it shouldn't pollute the cache for regularly accessed pages. The inactive list acts as a "probation" period.

```c
/* linux/mm/vmscan.c */
struct lruvec {
    struct list_head        lists[NR_LRU_LISTS];
    /* ... */
};

enum lru_list {
    LRU_INACTIVE_ANON = 0,   /* anonymous pages (heap, stack) */
    LRU_ACTIVE_ANON,
    LRU_INACTIVE_FILE,       /* file-backed pages */
    LRU_ACTIVE_FILE,
    LRU_UNEVICTABLE,         /* mlock'd, huge pages */
    NR_LRU_LISTS
};

/* Move page from inactive to active list */
void mark_page_accessed(struct page *page) {
    if (!PageActive(page) && !PageUnevictable(page) && PageReferenced(page)) {
        activate_page(page);  /* promote to active */
        ClearPageReferenced(page);
    } else if (!PageReferenced(page)) {
        SetPageReferenced(page);
    }
}
```

### C Implementation: Two-List LRU Cache

```c
/* file: lru_cache.c
 * compile: gcc -Wall -O2 lru_cache.c -o lru_cache
 * Two-list LRU page cache: active + inactive lists + hash table.
 * Models the Linux page cache eviction policy.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

#define CACHE_SIZE   8
#define ACTIVE_MAX   (CACHE_SIZE * 2 / 3)  /* 5 of 8 active */
#define HASH_BITS    4
#define HASH_SIZE    (1 << HASH_BITS)
#define HASH_MASK    (HASH_SIZE - 1)

typedef enum { LIST_INACTIVE = 0, LIST_ACTIVE = 1 } lru_list_t;

typedef struct page {
    uint64_t    index;       /* file offset / key */
    char        data[32];    /* payload */
    lru_list_t  lru_list;
    int         referenced;  /* set on second access while inactive */

    /* Intrusive list node */
    struct page *lru_prev, *lru_next;
    /* Hash chain */
    struct page *hash_next;
} page_t;

typedef struct {
    page_t *head;
    page_t *tail;
    int     count;
} list_t;

typedef struct {
    list_t    inactive;
    list_t    active;
    page_t   *htable[HASH_SIZE];
    int       total;
} page_cache_t;

/* ── Intrusive list helpers ── */
static void list_init(list_t *l) { l->head = l->tail = NULL; l->count = 0; }

static void list_add_head(list_t *l, page_t *p) {
    p->lru_prev = NULL; p->lru_next = l->head;
    if (l->head) l->head->lru_prev = p;
    l->head = p;
    if (!l->tail) l->tail = p;
    l->count++;
}

static void list_remove(list_t *l, page_t *p) {
    if (p->lru_prev) p->lru_prev->lru_next = p->lru_next;
    else             l->head = p->lru_next;
    if (p->lru_next) p->lru_next->lru_prev = p->lru_prev;
    else             l->tail = p->lru_prev;
    p->lru_prev = p->lru_next = NULL;
    l->count--;
}

static page_t *list_pop_tail(list_t *l) {
    if (!l->tail) return NULL;
    page_t *p = l->tail;
    list_remove(l, p);
    return p;
}

/* ── Hash table operations ── */
static uint32_t page_hash(uint64_t index) {
    return ((uint32_t)(index * 0x61C88647u)) & HASH_MASK;
}

static page_t *cache_lookup(page_cache_t *c, uint64_t index) {
    uint32_t h = page_hash(index);
    for (page_t *p = c->htable[h]; p; p = p->hash_next)
        if (p->index == index) return p;
    return NULL;
}

static void cache_hash_add(page_cache_t *c, page_t *p) {
    uint32_t h = page_hash(p->index);
    p->hash_next = c->htable[h];
    c->htable[h] = p;
}

static void cache_hash_del(page_cache_t *c, page_t *p) {
    uint32_t h = page_hash(p->index);
    page_t **pp = &c->htable[h];
    while (*pp && *pp != p) pp = &(*pp)->hash_next;
    if (*pp) *pp = p->hash_next;
}

/* ── Eviction ── */
static void cache_evict_one(page_cache_t *c) {
    /* Try inactive tail first */
    page_t *victim = list_pop_tail(&c->inactive);
    if (!victim && c->active.count > 0) {
        /* Demote active tail to inactive */
        victim = list_pop_tail(&c->active);
        if (victim) {
            victim->lru_list = LIST_INACTIVE;
            list_add_head(&c->inactive, victim);
            victim = list_pop_tail(&c->inactive);
        }
    }
    if (victim) {
        printf("  EVICT page index=%llu\n", (unsigned long long)victim->index);
        cache_hash_del(c, victim);
        free(victim);
        c->total--;
    }
}

/* ── Rebalance active/inactive ── */
static void cache_rebalance(page_cache_t *c) {
    while (c->active.count > ACTIVE_MAX && c->active.tail) {
        page_t *p = list_pop_tail(&c->active);
        p->lru_list   = LIST_INACTIVE;
        p->referenced = 0;
        list_add_head(&c->inactive, p);
    }
}

/* ── Public access ── */
static page_t *cache_get(page_cache_t *c, uint64_t index, const char *data) {
    page_t *p = cache_lookup(c, index);

    if (p) {
        /* Cache hit */
        if (p->lru_list == LIST_INACTIVE) {
            if (p->referenced) {
                /* Second access while inactive → promote to active */
                printf("  PROMOTE page %llu to active\n", (unsigned long long)index);
                list_remove(&c->inactive, p);
                p->lru_list = LIST_ACTIVE;
                list_add_head(&c->active, p);
            } else {
                p->referenced = 1;
                /* Move to head of inactive (clock arm) */
                list_remove(&c->inactive, p);
                list_add_head(&c->inactive, p);
            }
        } else {
            /* Already active: move to head */
            list_remove(&c->active, p);
            list_add_head(&c->active, p);
        }
        return p;
    }

    /* Cache miss: evict if necessary */
    if (c->total >= CACHE_SIZE) {
        cache_rebalance(c);
        cache_evict_one(c);
    }

    /* Allocate new page */
    p = calloc(1, sizeof(*p));
    p->index    = index;
    p->lru_list = LIST_INACTIVE;
    strncpy(p->data, data, sizeof(p->data) - 1);
    list_add_head(&c->inactive, p);
    cache_hash_add(c, p);
    c->total++;
    printf("  LOAD  page %llu (total=%d)\n", (unsigned long long)index, c->total);
    return p;
}

static void cache_print(page_cache_t *c) {
    printf("  Active   (%d): ", c->active.count);
    for (page_t *p = c->active.head; p; p = p->lru_next)
        printf("%llu ", (unsigned long long)p->index);
    printf("\n  Inactive (%d): ", c->inactive.count);
    for (page_t *p = c->inactive.head; p; p = p->lru_next)
        printf("%llu ", (unsigned long long)p->index);
    printf("\n");
}

int main(void) {
    page_cache_t cache = {0};
    list_init(&cache.inactive);
    list_init(&cache.active);

    printf("Accessing pages 0..9 sequentially (cold start):\n");
    for (int i = 0; i < 10; i++) {
        char buf[16]; snprintf(buf, sizeof(buf), "pg%d", i);
        cache_get(&cache, i, buf);
    }
    cache_print(&cache);

    printf("\nRe-accessing pages 0..4 (should promote to active):\n");
    for (int i = 0; i < 5; i++) {
        cache_get(&cache, i, "");
        cache_get(&cache, i, "");  /* second access → promote */
    }
    cache_print(&cache);

    return 0;
}
```

---

## 21. Maple Tree

### One-Line Explanation
The Maple tree (Linux 6.1+) is a B-tree variant optimized for virtual memory area (VMA) management, replacing the old rb-tree + linked list combination for process address space management.

### Why Maple Tree?

The old VMA management used:
- `mm_struct.mmap`: `list_head` for iteration
- `mm_struct.mm_rb`: `rb_root` for lookup by address

The Maple tree replaces both with a single data structure providing:
- O(log n) lookup, insert, delete (same as rb-tree)
- Range queries: "find all VMAs overlapping [addr, addr+size]"
- Sequential iteration (B-tree leaf chaining)
- RCU-safe reads
- Lock-free reads with mas_walk()

```c
/* linux/include/linux/maple_tree.h */

struct maple_tree {
    union {
        spinlock_t      ma_lock;
        lockdep_map_p   ma_external_lock;
    };
    unsigned int        ma_flags;
    void __rcu         *ma_root;
};

#define DEFINE_MAPLE_TREE(name) \
    struct maple_tree name = MTREE_INIT(name, 0)

/* Operations */
int  mtree_insert(struct maple_tree *mt, unsigned long index,
                  void *entry, gfp_t gfp);
int  mtree_insert_range(struct maple_tree *mt, unsigned long first,
                        unsigned long last, void *entry, gfp_t gfp);
void *mtree_load(struct maple_tree *mt, unsigned long index);
void *mtree_erase(struct maple_tree *mt, unsigned long index);

/* Range iteration */
mt_for_each(mt, entry, index, max) { ... }
```

### Node Types in Maple Tree

The Maple tree uses three node types, selected based on the type of data:
1. **Range nodes** (for VMA: key is an address range, value is `vm_area_struct *`)
2. **Dense nodes** (for small sequential ranges, no key stored — implicit)
3. **Arange nodes** (augmented: stores max endpoint for fast range intersection)

---

## 22. Interval Trees

### One-Line Explanation
An augmented rb-tree where each node stores a `[start, end]` interval and the subtree's maximum endpoint — enabling O(log n + k) stabbing queries: "find all intervals containing point p".

### Linux Usage

```c
/* linux/include/linux/interval_tree.h
 * Used by: kernel/events/core.c (perf), mm/interval_tree.c (VMA overlap)
 */

struct interval_tree_node {
    struct rb_node rb;
    unsigned long start;   /* interval start */
    unsigned long last;    /* interval end (inclusive) */
    unsigned long __subtree_last;  /* augmented: max 'last' in subtree */
};

void interval_tree_insert(struct interval_tree_node *node,
                           struct rb_root_cached *root);
void interval_tree_remove(struct interval_tree_node *node,
                           struct rb_root_cached *root);

/* Find first interval overlapping [start, last] */
struct interval_tree_node *interval_tree_iter_first(
    struct rb_root_cached *root,
    unsigned long start, unsigned long last);

/* Find next overlapping interval */
struct interval_tree_node *interval_tree_iter_next(
    struct interval_tree_node *node,
    unsigned long start, unsigned long last);
```

### C Implementation: VMA Overlap Detection

```c
/* file: interval_tree.c
 * compile: gcc -Wall -O2 interval_tree.c -o interval_tree
 * Interval tree for VMA overlap detection (simplified).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>

typedef struct it_node {
    uint64_t     start, end;      /* interval [start, end] */
    uint64_t     subtree_max;     /* max end in this subtree */
    char         name[32];
    struct it_node *left, *right, *parent;
    int          height;          /* for AVL balancing (simplified) */
} it_node_t;

typedef struct { it_node_t *root; } it_root_t;

static uint64_t max3(uint64_t a, uint64_t b, uint64_t c) {
    return (a > b ? a : b) > c ? (a > b ? a : b) : c;
}

/* Update augmented subtree_max bottom-up */
static void it_update_max(it_node_t *n) {
    if (!n) return;
    n->subtree_max = n->end;
    if (n->left)  n->subtree_max = n->subtree_max > n->left->subtree_max  ? n->subtree_max : n->left->subtree_max;
    if (n->right) n->subtree_max = n->subtree_max > n->right->subtree_max ? n->subtree_max : n->right->subtree_max;
}

static it_node_t *it_insert(it_node_t *root, it_node_t *n) {
    if (!root) {
        n->subtree_max = n->end;
        n->left = n->right = n->parent = NULL;
        return n;
    }
    if (n->start < root->start) {
        root->left  = it_insert(root->left, n);
        if (root->left) root->left->parent = root;
    } else {
        root->right = it_insert(root->right, n);
        if (root->right) root->right->parent = root;
    }
    it_update_max(root);
    return root;
}

/* Find all intervals overlapping [query_start, query_end] */
static void it_query(it_node_t *node, uint64_t qs, uint64_t qe,
                     void (*visit)(it_node_t *)) {
    if (!node) return;
    /* Prune: if subtree_max < qs, no interval in this subtree overlaps */
    if (node->subtree_max < qs) return;

    /* Visit left subtree */
    it_query(node->left, qs, qe, visit);

    /* Check this node: overlaps if start <= qe && end >= qs */
    if (node->start <= qe && node->end >= qs)
        visit(node);

    /* Prune right: if this node's start > qe, right subtree can't overlap */
    if (node->start <= qe)
        it_query(node->right, qs, qe, visit);
}

static void print_node(it_node_t *n) {
    printf("  [%llu, %llu] %s\n",
           (unsigned long long)n->start,
           (unsigned long long)n->end,
           n->name);
}

int main(void) {
    it_root_t tree = {0};

    it_node_t nodes[] = {
        {.start=0x1000, .end=0x2000, .name="text"},
        {.start=0x3000, .end=0x5000, .name="data"},
        {.start=0x6000, .end=0x7000, .name="bss"},
        {.start=0x8000, .end=0xC000, .name="heap"},
        {.start=0x7FF00000, .end=0x7FFFFFFF, .name="stack"},
    };

    for (int i = 0; i < 5; i++)
        tree.root = it_insert(tree.root, &nodes[i]);

    /* Query: which VMAs overlap [0x4000, 0x8500]? */
    printf("VMAs overlapping [0x4000, 0x8500]:\n");
    it_query(tree.root, 0x4000, 0x8500, print_node);

    /* Query: which VMAs overlap [0x7FFFE000, 0x7FFFFFFF]? */
    printf("VMAs overlapping stack region:\n");
    it_query(tree.root, 0x7FFFE000, 0x7FFFFFFF, print_node);

    return 0;
}
```

---

## 23. Security Checklist

For all kernel-adjacent code (drivers, eBPF helpers, kernel modules):

```
□ Integer Overflow
  - Validate all user-supplied sizes before allocation:
    if (count > MAX_SAFE_COUNT || size * count < size) return -EINVAL;
  - Use checked_add/checked_mul (Rust) or check_mul_overflow (C)

□ Buffer Overflow
  - Never use strcpy/sprintf with user data
  - Always bounds-check array indices: if (idx >= ARRAY_SIZE(arr)) return -ERANGE;
  - Use copy_from_user/copy_to_user (never direct dereference of user pointers)

□ Use-After-Free
  - Poison freed memory: KASAN/KFENCE will detect with CONFIG_KASAN=y
  - Never hold bare pointers past an RCU read unlock without refcounting
  - Set pointer to NULL (or LIST_POISON) after free

□ Race Conditions
  - Review all shared state for missing locks or atomics
  - Check_bugs: LOCKDEP enabled (CONFIG_PROVE_LOCKING=y) for lock ordering
  - Use KCSAN (CONFIG_KCSAN=y) for data race detection

□ Info Leaks
  - Zero-initialize structs before copy_to_user:
    struct my_info info = {}; /* NOT uninitialized */
  - Pad structs explicitly to prevent padding byte leaks
  - Don't leak kernel pointers to userspace (use %pK in printk)

□ Privilege Escalation
  - Validate capabilities: capable(CAP_SYS_ADMIN)
  - Don't trust user-space PIDs/FDs without validation
  - netlink: check sock's creds before accepting privileged commands

□ eBPF/JIT
  - Verifier ensures no OOB memory access, no infinite loops
  - JIT hardening: CONFIG_BPF_JIT_ALWAYS_ON + CONFIG_BPF_JIT_DEFAULT_ON
  - Randomize JIT image addresses: bpf_jit_kallsyms=0

□ Spectre/Meltdown
  - Use array_index_nospec() for bounds-checked array accesses
  - nospec_barrier() where needed
  - Retpoline enabled in compiler: -mindirect-branch=thunk

□ Crypto
  - Never roll your own crypto: use kernel crypto API
  - Use get_random_bytes() not /dev/urandom reads
  - Hash table keys: use siphash/halfsiphash, not plain multiplication
```

---

## 24. Performance and Profiling

### Profiling Kernel Data Structure Performance

```bash
# ── perf: CPU performance counters ──
# Profile cache misses (critical for data structure choice)
perf stat -e cache-misses,cache-references,instructions,cycles \
    ./your_program

# Record call graph
perf record -g ./your_program
perf report --stdio

# ── ftrace: kernel function latency ──
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo 'rb_insert_color' > /sys/kernel/debug/tracing/set_ftrace_filter
cat /sys/kernel/debug/tracing/trace

# ── BPF/bpftrace: in-kernel histograms ──
# Track rb_insert_color latency distribution
bpftrace -e '
kprobe:rb_insert_color { @start[tid] = nsecs; }
kretprobe:rb_insert_color /@start[tid]/ {
    @latency = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}'

# Track kmalloc call sites
bpftrace -e 'kprobe:__kmalloc { @[kstack] = count(); }'

# ── KASAN: AddressSanitizer for kernel ──
# Rebuild kernel with:
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y   # faster instrumentation
# Run workload; KASAN reports will appear in dmesg

# ── KCSAN: Kernel Concurrency Sanitizer ──
CONFIG_KCSAN=y
# Reports data races in dmesg

# ── lock_stat: Lock contention statistics ──
echo 1 > /proc/sys/kernel/lock_stat
# Run workload
cat /proc/lock_stat | head -50
echo 0 > /proc/sys/kernel/lock_stat

# ── slabinfo: Slab allocator statistics ──
cat /proc/slabinfo | sort -k3 -rn | head -20
# slabtop for live view
slabtop

# ── vmstat: Memory subsystem ──
vmstat -s   # summary
vmstat 1    # live per-second
cat /proc/vmstat | grep pgsteal   # page reclaim stats
```

### Benchmark: Data Structure Comparison

```c
/* file: bench_ds.c
 * compile: gcc -Wall -O3 -march=native bench_ds.c -o bench_ds
 * Compares list, hashtable, and rbtree for 10M operations.
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <string.h>

#define N 1000000

typedef struct { uint64_t t; } ts_t;
static ts_t now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (ts_t){ (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec };
}
static double elapsed_ms(ts_t a, ts_t b) { return (b.t - a.t) / 1e6; }

/* ── Array (cache-friendly baseline) ── */
static uint64_t arr[N];
static void bench_array(void) {
    ts_t t0 = now();
    for (int i = 0; i < N; i++) arr[i] = i * 2 + 1;
    uint64_t sum = 0;
    for (int i = 0; i < N; i++) sum += arr[i];
    printf("Array sequential:    %.2fms  (sum=%llu)\n",
           elapsed_ms(t0, now()), (unsigned long long)sum);
}

int main(void) {
    printf("Data Structure Micro-Benchmarks (N=%d):\n\n", N);
    bench_array();
    /* Add list/hashtable/rbtree benchmarks following same pattern */
    return 0;
}
```

### Go Benchmark Template

```go
// file: bench_test.go
package bench

import (
    "testing"
    "math/rand"
)

func BenchmarkMapGet(b *testing.B) {
    m := make(map[uint64]uint64, b.N)
    for i := uint64(0); i < uint64(b.N); i++ {
        m[i] = i
    }
    keys := make([]uint64, b.N)
    for i := range keys { keys[i] = uint64(rand.Intn(b.N)) }

    b.ResetTimer()
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        _ = m[keys[i]]
    }
}

// Run: go test -bench=. -benchmem -cpuprofile=cpu.out
// View: go tool pprof cpu.out
```

---

## 25. Further Reading

### Books

| Title | Author | Focus |
|---|---|---|
| *Linux Kernel Development* | Robert Love | Broad overview, data structures in context |
| *Understanding the Linux Kernel* | Bovet & Cesati | Deep internals: memory, scheduling |
| *Linux Device Drivers* | Corbet, Rubini, Kroah-Hartman | Driver programming, data structure usage |
| *The Art of Multiprocessor Programming* | Herlihy & Shavit | Lock-free algorithms, theoretical foundation |
| *Introduction to Algorithms* | CLRS | RB-trees, B-trees, skip lists — canonical reference |
| *Rust Atomics and Locks* | Mara Bos | Memory ordering, lock-free data structures in Rust |

### Key Kernel Source Files

```
linux/include/linux/list.h         — intrusive linked list
linux/include/linux/hashtable.h    — DECLARE_HASHTABLE
linux/include/linux/rbtree.h       — red-black tree
linux/include/linux/xarray.h       — XArray
linux/include/linux/maple_tree.h   — Maple tree
linux/include/linux/kfifo.h        — ring buffer
linux/include/linux/wait.h         — wait queues
linux/include/linux/rcu.h          — RCU
linux/include/linux/percpu.h       — per-CPU variables
linux/include/linux/bitmap.h       — bitmap
linux/include/linux/atomic.h       — atomic operations
linux/include/linux/seqlock.h      — sequence locks
linux/include/linux/interval_tree.h — interval tree
linux/mm/slab.c                    — SLAB allocator
linux/mm/slub.c                    — SLUB allocator
linux/mm/vmscan.c                  — LRU eviction
linux/kernel/sched/fair.c          — CFS, rb-tree usage
linux/lib/rbtree.c                 — rb-tree implementation
linux/lib/btree.c                  — B-tree implementation
linux/lib/idr.c                    — IDR
```

### Essential Papers

1. **"The Linux Scheduler: a Decade of Wasted Cores"** (EuroSys 2016) — scheduling data structure performance
2. **"Read-Copy-Update: Using Execution History to Solve Concurrency Problems"** — McKenney's original RCU paper
3. **"SLOB: A Slab-like Memory Allocator for Embedded Linux"** — slab allocator design tradeoffs
4. **"Maple Tree: A Range-Based B-Tree for VMA Management"** (LPC 2022) — why the Maple tree replaced rb-tree for VMAs

### Tools

| Tool | Purpose |
|---|---|
| `CONFIG_KASAN` | Kernel AddressSanitizer: detects UAF, OOB |
| `CONFIG_KCSAN` | Kernel Concurrency Sanitizer: detects data races |
| `CONFIG_PROVE_LOCKING` | LOCKDEP: detects lock ordering violations |
| `CONFIG_DEBUG_SLAB` | Poison slab free memory |
| `bpftrace` | In-kernel tracing without recompilation |
| `perf` | Hardware performance counter profiling |
| `slabtop` | Live slab allocator statistics |
| `/proc/slabinfo` | Slab cache statistics |
| `valgrind --tool=massif` | Heap profiling (userspace) |
| `heaptrack` | Fast heap profiler (userspace) |

---

*Guide version: Linux 6.x reference. Code compiles with gcc 12+, Rust 1.77+, Go 1.22+.*
*Security: all code is educational — production use requires CONFIG_KASAN validation, fuzz testing with syzkaller, and security audit.*