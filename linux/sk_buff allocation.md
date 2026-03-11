# sk_buff Allocation: Comprehensive Deep Dive

**Summary**: The sk_buff (socket buffer) is Linux's fundamental network packet representation, combining metadata and data in a unified structure optimized for zero-copy forwarding and header manipulation. Allocation strategies balance performance (slab caches, cloning) against memory pressure, with distinct paths for RX (NIC→kernel), TX (kernel→NIC), and forwarding. Security boundaries rely on proper reference counting, avoiding UAF/double-free bugs, and isolating user-accessible metadata from kernel state. Understanding sk_buff lifecycle—allocation, manipulation, clone/copy semantics, and destruction—is critical for writing secure networking code, eBPF programs, or custom network stacks. Performance hinges on cache-locality, minimizing allocations, and leveraging headroom/tailroom for header operations without reallocation.

---

## Core Architecture & Memory Layout

### 1. The sk_buff Structure Anatomy

```
╔═══════════════════════════════════════════════════════════════╗
║                    sk_buff (metadata)                          ║
║  ~240 bytes on x86_64 (kernel 5.10+)                          ║
╠═══════════════════════════════════════════════════════════════╣
║ struct sk_buff {                                               ║
║   union { struct sk_buff *next; rb_node; };  // list/rb-tree  ║
║   struct sock *sk;              // owning socket               ║
║   struct net_device *dev;       // ingress/egress device       ║
║   ktime_t tstamp;               // timestamp                   ║
║   unsigned int len;             // data length                 ║
║   unsigned int data_len;        // paged data length           ║
║   __u16 mac_len, hdr_len;       // header lengths              ║
║   __u16 queue_mapping;          // multi-queue mapping         ║
║   __u8 pkt_type:3;              // PACKET_{HOST|BROADCAST|...} ║
║   void (*destructor)(sk_buff*); // custom cleanup              ║
║                                                                 ║
║   // Data pointers (critical for understanding):               ║
║   unsigned char *head;          // buffer start                ║
║   unsigned char *data;          // payload start               ║
║   unsigned char *tail;          // payload end                 ║
║   unsigned char *end;           // buffer end                  ║
║                                                                 ║
║   // Reference counting:                                       ║
║   refcount_t users;             // refcount for sk_buff        ║
║   atomic_t dataref;             // refcount for data buffer    ║
║ }                                                               ║
╚═══════════════════════════════════════════════════════════════╝
         |
         | points to
         v
╔═══════════════════════════════════════════════════════════════╗
║              Data Buffer (contiguous memory)                   ║
╠═══════════════════════════════════════════════════════════════╣
║  [headroom] [data] [tailroom] [skb_shared_info]               ║
║      ↑        ↑        ↑                                       ║
║     head    data     tail/end                                  ║
╚═══════════════════════════════════════════════════════════════╝

Memory Layout Detail:
┌────────────────────────────────────────────────────────────────┐
│  head                                                       end │
│   ↓                                                          ↓  │
│   [─────headroom─────][───────data───────][───tailroom────]   │
│                        ↑                  ↑                     │
│                       data               tail                   │
│                                                                  │
│  headroom = data - head  (for prepending headers)              │
│  tailroom = end - tail   (for appending data)                  │
│  len = tail - data                                              │
└────────────────────────────────────────────────────────────────┘
```

### 2. Allocation Paths

```
Allocation Decision Tree:
═══════════════════════════════════════════════════════════════

┌─────────────────┐
│ Need sk_buff?   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Size?   │
    └─┬───┬───┘
      │   │
  <=2K│   │>2K
      │   │
      │   └──────> alloc_skb_with_frags() → paged allocation
      │
      └──> Small/Normal Path
           │
      ┌────▼──────────────────────────────┐
      │ alloc_skb(size, gfp_mask)         │
      │   ↓                                │
      │ kmem_cache_alloc_node(skbuff_head_cache, ...) │
      │   + kmalloc(size + sizeof(skb_shared_info))   │
      └────┬───────────────────────────────┘
           │
      ┌────▼─────────────────────────────────────────────┐
      │ Layout Result:                                    │
      │ [sk_buff metadata][headroom][data][tailroom]     │
      │                    [skb_shared_info]              │
      └───────────────────────────────────────────────────┘

Special Cases:
══════════════
1. __alloc_skb() - Core allocator
2. alloc_skb_fclone() - Pre-allocate for clone (faster)
3. __netdev_alloc_skb() - Device driver allocation (NUMA-aware)
4. __napi_alloc_skb() - NAPI context (per-CPU cache)
5. build_skb() - Wrap existing buffer (zero-copy from page pool)
```

---

## Deep Dive: Allocation Implementation

### 3. Core Allocation Code Path

**File**: `net/core/skbuff.c`

```c
/* Core sk_buff allocation */
struct sk_buff *__alloc_skb(unsigned int size, gfp_t gfp_mask,
                             int flags, int node)
{
    struct kmem_cache *cache;
    struct sk_buff *skb;
    u8 *data;
    bool pfmemalloc;

    /* Step 1: Allocate sk_buff structure from slab cache */
    cache = (flags & SKB_ALLOC_FCLONE)
            ? skbuff_fclone_cache  // Fast-clone cache
            : skbuff_head_cache;   // Normal cache
    
    skb = kmem_cache_alloc_node(cache, gfp_mask & ~GFP_DMA, node);
    if (unlikely(!skb))
        return NULL;

    /* Step 2: Allocate data buffer */
    size = SKB_DATA_ALIGN(size);  // Align to L1 cache line
    size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
    
    data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
    if (unlikely(!data))
        goto nodata;

    /* Step 3: Initialize sk_buff pointers */
    memset(skb, 0, offsetof(struct sk_buff, tail));
    skb->truesize = SKB_TRUESIZE(size);
    skb->pfmemalloc = pfmemalloc;
    refcount_set(&skb->users, 1);
    skb->head = data;
    skb->data = data;
    skb_reset_tail_pointer(skb, 0);
    skb->end = skb->tail + size;
    
    /* Step 4: Initialize skb_shared_info at end of buffer */
    atomic_set(&(skb_shinfo(skb)->dataref), 1);
    skb_shinfo(skb)->nr_frags = 0;
    skb_shinfo(skb)->gso_size = 0;
    
    return skb;

nodata:
    kmem_cache_free(cache, skb);
    return NULL;
}
```

### 4. Slab Cache Strategy

```c
/* Initialization: net/core/skbuff.c */
void __init skb_init(void)
{
    /* Cache for sk_buff structures (no data) */
    skbuff_head_cache = kmem_cache_create(
        "skbuff_head_cache",
        sizeof(struct sk_buff),
        0,
        SLAB_HWCACHE_ALIGN | SLAB_PANIC,
        NULL);

    /* Cache for fast cloning (sk_buff + clone) */
    skbuff_fclone_cache = kmem_cache_create(
        "skbuff_fclone_cache",
        sizeof(struct sk_buff_fclones),  // 2x sk_buff + fclone metadata
        0,
        SLAB_HWCACHE_ALIGN | SLAB_PANIC,
        NULL);
}

/* Fast-clone structure */
struct sk_buff_fclones {
    struct sk_buff skb1;
    struct sk_buff skb2;
    refcount_t fclone_ref;
};
```

**Why Slab Caches?**
- **Cache-line alignment**: Reduces false sharing on SMP
- **Object reuse**: Minimizes allocation overhead (hot path)
- **NUMA awareness**: Per-node caches reduce cross-node traffic
- **Predictable size**: sk_buff is fixed-size, perfect for slabs

---

## Clone vs Copy Semantics (Critical for Security)

### 5. Cloning: Shared Data, Independent Metadata

```c
/* Create a shallow copy (shared data buffer) */
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff *n;

    /* Fast path: use pre-allocated fclone if available */
    if (skb->fclone == SKB_FCLONE_ORIG &&
        refcount_read(&skbuff_fclone(skb)->fclone_ref) == 1) {
        n = &skbuff_fclone(skb)->skb2;
        refcount_set(&skbuff_fclone(skb)->fclone_ref, 2);
    } else {
        /* Slow path: allocate new sk_buff */
        n = kmem_cache_alloc(skbuff_head_cache, gfp_mask);
        if (!n)
            return NULL;
        n->fclone = SKB_FCLONE_UNAVAILABLE;
    }

    /* Copy metadata, share data buffer */
    memcpy(n, skb, offsetof(struct sk_buff, tail));
    
    /* CRITICAL: Increment data buffer refcount */
    atomic_inc(&(skb_shinfo(skb)->dataref));
    
    /* Independent reference count for new sk_buff */
    refcount_set(&n->users, 1);
    
    /* Shared pointers (both point to same buffer) */
    n->head = skb->head;
    n->data = skb->data;
    n->tail = skb->tail;
    n->end = skb->end;

    return n;
}
```

**Clone Use Cases**:
- **Packet forwarding**: Send same packet to multiple destinations
- **tcpdump/BPF**: Inspection without modifying original
- **Queueing**: Hold packet in multiple queues

**Security Implication**: Modifying cloned data affects all clones → **COW (Copy-On-Write)** required before mutation.

### 6. Copying: Independent Data + Metadata

```c
/* Deep copy: independent buffer */
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask)
{
    int headerlen = skb_headroom(skb);
    unsigned int size = skb_end_offset(skb) + skb->data_len;
    struct sk_buff *n;

    /* Allocate new sk_buff + buffer */
    n = __alloc_skb(size, gfp_mask, 0, NUMA_NO_NODE);
    if (!n)
        return NULL;

    /* Reserve headroom */
    skb_reserve(n, headerlen);

    /* Copy linear data */
    skb_put(n, skb->len);
    skb_copy_from_linear_data(skb, n->data, skb->len);

    /* Copy paged fragments if present */
    if (skb_copy_bits(skb, 0, n->data, skb->len))
        goto fail;

    /* Copy metadata (cb[], priority, etc.) */
    skb_copy_header(n, skb);
    return n;

fail:
    kfree_skb(n);
    return NULL;
}
```

**Copy Use Cases**:
- **Modification required**: When you need to change packet contents
- **Isolation**: Security boundaries (e.g., namespace crossing)
- **Partial copy**: Extract headers only

---

## Memory Management & Reference Counting

### 7. Lifetime Management

```
Reference Counting Model:
═════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────┐
│  sk_buff Structure (skb->users)                          │
│  - Tracks how many kernel subsystems hold the sk_buff    │
│  - Freed when users == 0                                 │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ owns
                 ▼
┌──────────────────────────────────────────────────────────┐
│  Data Buffer (skb_shinfo(skb)->dataref)                  │
│  - Tracks how many sk_buffs share the data               │
│  - Freed when dataref == 0                               │
└──────────────────────────────────────────────────────────┘

Example Flow:
════════════
1. alloc_skb()        → skb->users=1, dataref=1
2. skb_clone(skb)     → skb->users=1, clone->users=1, dataref=2
3. kfree_skb(skb)     → skb freed, dataref=1 (data still alive)
4. kfree_skb(clone)   → clone freed, dataref=0 → data freed

CRITICAL Functions:
═══════════════════
- skb_get(skb)        : refcount_inc(&skb->users)
- kfree_skb(skb)      : decrement users, free if 0
- consume_skb(skb)    : same as kfree_skb (but not drop, for tracing)
- skb_shared(skb)     : refcount_read(&skb->users) != 1
- skb_cloned(skb)     : atomic_read(&skb_shinfo(skb)->dataref) != 1
```

### 8. Copy-On-Write (COW) for Cloned Buffers

```c
/* Ensure exclusive access to data buffer */
static inline int skb_cow(struct sk_buff *skb, unsigned int headroom)
{
    /* Check if data is shared */
    if (skb_cloned(skb) || skb_headroom(skb) < headroom)
        return pskb_expand_head(skb, headroom, 0, GFP_ATOMIC);
    return 0;
}

/* Expand buffer (forces copy if cloned) */
int pskb_expand_head(struct sk_buff *skb, int nhead, int ntail, gfp_t gfp)
{
    int size = nhead + skb_end_offset(skb) + ntail;
    u8 *data;

    /* Allocate new buffer */
    size = SKB_DATA_ALIGN(size);
    data = kmalloc(size + sizeof(struct skb_shared_info), gfp);
    if (!data)
        return -ENOMEM;

    /* Copy old data to new buffer */
    skb_copy_from_linear_data(skb, data + nhead, skb_headlen(skb));

    /* Decrement old dataref, free if last user */
    atomic_dec(&(skb_shinfo(skb)->dataref));
    
    /* Update pointers to new buffer */
    skb->head = data;
    skb->data = data + nhead;
    skb_set_tail_pointer(skb, skb->len);
    skb->end = skb->head + size;

    /* New buffer has dataref=1 */
    atomic_set(&(skb_shinfo(skb)->dataref), 1);
    
    return 0;
}
```

---

## Practical Examples & Use Cases

### 9. Driver RX Allocation (NAPI Context)

```c
/* Network driver receiving packet (e.g., Intel e1000e) */
static struct sk_buff *driver_receive_packet(struct rx_ring *rx_ring,
                                               unsigned int length)
{
    struct sk_buff *skb;
    void *va;  // Virtual address from page pool

    /* Option 1: build_skb (zero-copy, fastest) */
    va = page_pool_dev_alloc_va(rx_ring->page_pool);
    if (!va)
        return NULL;
    
    skb = build_skb(va, rx_ring->frag_size);
    if (!skb) {
        page_pool_put_page(rx_ring->page_pool, virt_to_page(va), false);
        return NULL;
    }
    
    /* Reserve headroom (for header push later) */
    skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
    
    /* Set data length */
    __skb_put(skb, length);
    
    /* Option 2: Traditional allocation (if page pool not available) */
    // skb = napi_alloc_skb(&rx_ring->napi, length);
    
    /* Attach to device */
    skb->dev = rx_ring->netdev;
    skb->protocol = eth_type_trans(skb, rx_ring->netdev);
    
    return skb;
}
```

### 10. Header Manipulation

```c
/* Adding headers (prepend) */
void add_custom_header(struct sk_buff *skb)
{
    struct custom_hdr *hdr;
    
    /* Ensure headroom available */
    if (skb_cow_head(skb, sizeof(struct custom_hdr)) < 0)
        return -ENOMEM;
    
    /* Push header (moves data pointer backward) */
    hdr = (struct custom_hdr *)skb_push(skb, sizeof(struct custom_hdr));
    
    /* Fill header */
    hdr->type = CUSTOM_TYPE;
    hdr->length = skb->len;
}

/* Removing headers (pull) */
void remove_eth_header(struct sk_buff *skb)
{
    /* Pull Ethernet header (14 bytes) */
    skb_pull(skb, ETH_HLEN);
    
    /* Or reset to network header */
    skb_reset_network_header(skb);
}

/* Accessing headers */
void parse_packet(struct sk_buff *skb)
{
    struct ethhdr *eth = eth_hdr(skb);
    struct iphdr *iph = ip_hdr(skb);
    struct tcphdr *tcph = tcp_hdr(skb);
    
    printk("src_mac=%pM dst_mac=%pM\n", eth->h_source, eth->h_dest);
    printk("src_ip=%pI4 dst_ip=%pI4\n", &iph->saddr, &iph->daddr);
    printk("src_port=%u dst_port=%u\n", ntohs(tcph->source), ntohs(tcph->dest));
}
```

---

## Security Implications & Threat Model

### 11. Vulnerability Classes

```
Threat Model:
═════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ 1. Use-After-Free (UAF)                                     │
├─────────────────────────────────────────────────────────────┤
│ Root Cause: Improper refcount management                    │
│ Example:                                                     │
│   skb = alloc_skb(...);                                     │
│   kfree_skb(skb);                                           │
│   skb->len = 1234;  ← UAF!                                  │
│                                                              │
│ Mitigation:                                                  │
│   - Always use skb_get() before passing to async contexts   │
│   - NULL pointers after free in debug builds                │
│   - Use KASAN (Kernel Address Sanitizer)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. Buffer Overflow                                          │
├─────────────────────────────────────────────────────────────┤
│ Root Cause: Writing beyond tail without bounds check        │
│ Example:                                                     │
│   memcpy(skb_tail_pointer(skb), data, len); ← no check!    │
│                                                              │
│ Mitigation:                                                  │
│   - Always use skb_put() / skb_put_data()                   │
│   - Check: skb_tailroom(skb) >= len                         │
│   - Use skb_cow_data() for expansion                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. Data Leakage (Uninitialized Memory)                     │
├─────────────────────────────────────────────────────────────┤
│ Root Cause: Exposing uninitialized tailroom/headroom        │
│ Example:                                                     │
│   skb = alloc_skb(1500, GFP_KERNEL);                        │
│   skb_put(skb, 100);  ← 100 bytes valid, 1400 uninitialized │
│   send_to_userspace(skb);  ← leak!                          │
│                                                              │
│ Mitigation:                                                  │
│   - Use __GFP_ZERO flag: alloc_skb(size, GFP_KERNEL|__GFP_ZERO)│
│   - Explicitly zero: memset(skb->data, 0, len)              │
│   - Validate len before copy to userspace                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 4. Clone Confusion (Shared Data Mutation)                  │
├─────────────────────────────────────────────────────────────┤
│ Root Cause: Modifying shared buffer without COW             │
│ Example:                                                     │
│   clone = skb_clone(orig, GFP_ATOMIC);                      │
│   *(u32*)clone->data = malicious_value;  ← affects orig!    │
│                                                              │
│ Mitigation:                                                  │
│   - Check skb_cloned() before write                         │
│   - Use skb_cow() to force copy                             │
│   - Assume all clones are hostile in security contexts      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 5. Race Conditions (Concurrent Access)                     │
├─────────────────────────────────────────────────────────────┤
│ Root Cause: Multiple CPUs/threads accessing same sk_buff    │
│ Example:                                                     │
│   CPU0: skb->len = new_len;                                 │
│   CPU1: if (skb->len > MTU) ...  ← race!                    │
│                                                              │
│ Mitigation:                                                  │
│   - sk_buff ownership is single-threaded by design          │
│   - Use skb_queue_* for multi-producer/consumer             │
│   - Lock socket (lock_sock) when accessing sk->sk_*         │
└─────────────────────────────────────────────────────────────┘
```

### 12. Secure Coding Patterns

```c
/* ✅ SAFE: Proper bounds checking */
int safe_append_data(struct sk_buff *skb, const void *data, unsigned int len)
{
    /* Check available tailroom */
    if (skb_tailroom(skb) < len) {
        /* Attempt to expand */
        if (pskb_expand_head(skb, 0, len - skb_tailroom(skb), GFP_ATOMIC))
            return -ENOMEM;
    }
    
    /* Safe copy with bounds check */
    skb_put_data(skb, data, len);
    return 0;
}

/* ✅ SAFE: COW before modification */
int safe_modify_cloned(struct sk_buff *skb, unsigned int offset, u32 value)
{
    /* Ensure exclusive ownership */
    if (skb_cloned(skb)) {
        if (skb_cow(skb, 0) < 0)
            return -ENOMEM;
    }
    
    /* Now safe to modify */
    *(u32 *)(skb->data + offset) = value;
    return 0;
}

/* ✅ SAFE: Refcount management */
void safe_async_processing(struct sk_buff *skb)
{
    /* Increment refcount before queuing */
    skb_get(skb);
    
    if (queue_work(wq, &work)) {
        /* Work will call consume_skb(skb) when done */
    } else {
        /* Failed to queue, drop our reference */
        kfree_skb(skb);
    }
}

/* ❌ UNSAFE: No bounds check */
void unsafe_append(struct sk_buff *skb, const void *data, unsigned int len)
{
    memcpy(skb_tail_pointer(skb), data, len);  // OVERFLOW!
    skb->tail += len;  // Wrong! Use skb_put()
}

/* ❌ UNSAFE: Modifying shared data */
void unsafe_modify(struct sk_buff *skb)
{
    *(u32 *)skb->data = 0xdeadbeef;  // May affect clones!
}
```

---

## Performance Optimization

### 13. Allocation Strategies

```c
/* Per-CPU page pools (modern drivers, kernel 5.4+) */
struct page_pool_params pp_params = {
    .order = 0,
    .pool_size = 256,
    .nid = NUMA_NO_NODE,
    .dev = dev,
    .dma_dir = DMA_FROM_DEVICE,
    .max_len = PAGE_SIZE,
};

struct page_pool *pp = page_pool_create(&pp_params);

/* Fast RX path with page pool */
static struct sk_buff *fast_rx_alloc(struct page_pool *pp, unsigned int len)
{
    void *va = page_pool_dev_alloc_va(pp);
    struct sk_buff *skb = build_skb(va, PAGE_SIZE);
    
    skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
    __skb_put(skb, len);
    
    return skb;
}

/* Bulk allocation for TX (reduce syscall overhead) */
static struct sk_buff **alloc_skb_bulk(unsigned int count, unsigned int size)
{
    struct sk_buff **skbs = kmalloc_array(count, sizeof(struct sk_buff *), GFP_KERNEL);
    int i;
    
    for (i = 0; i < count; i++) {
        skbs[i] = alloc_skb(size, GFP_KERNEL);
        if (!skbs[i])
            goto fail;
    }
    return skbs;
    
fail:
    while (--i >= 0)
        kfree_skb(skbs[i]);
    kfree(skbs);
    return NULL;
}
```

### 14. Benchmarking & Profiling

```bash
# Build kernel module for testing
cat > skb_bench.c << 'EOF'
#include <linux/module.h>
#include <linux/skbuff.h>
#include <linux/ktime.h>

static int __init skb_bench_init(void)
{
    ktime_t start, end;
    struct sk_buff *skb;
    int i, iterations = 100000;
    s64 elapsed_ns;
    
    /* Benchmark alloc_skb */
    start = ktime_get();
    for (i = 0; i < iterations; i++) {
        skb = alloc_skb(1500, GFP_KERNEL);
        kfree_skb(skb);
    }
    end = ktime_get();
    elapsed_ns = ktime_to_ns(ktime_sub(end, start));
    pr_info("alloc_skb: %lld ns/op\n", elapsed_ns / iterations);
    
    /* Benchmark skb_clone */
    skb = alloc_skb_fclone(1500, GFP_KERNEL);
    start = ktime_get();
    for (i = 0; i < iterations; i++) {
        struct sk_buff *clone = skb_clone(skb, GFP_KERNEL);
        kfree_skb(clone);
    }
    end = ktime_get();
    elapsed_ns = ktime_to_ns(ktime_sub(end, start));
    pr_info("skb_clone (fclone): %lld ns/op\n", elapsed_ns / iterations);
    kfree_skb(skb);
    
    return 0;
}

static void __exit skb_bench_exit(void) {}
module_init(skb_bench_init);
module_exit(skb_bench_exit);
MODULE_LICENSE("GPL");
EOF

# Compile and run
cat > Makefile << 'EOF'
obj-m += skb_bench.o
KDIR := /lib/modules/$(shell uname -r)/build
all:
	make -C $(KDIR) M=$(PWD) modules
clean:
	make -C $(KDIR) M=$(PWD) clean
EOF

make
sudo insmod skb_bench.ko
dmesg | tail -5
sudo rmmod skb_bench
```

---

## Testing & Fuzzing

### 15. Unit Testing with KUnit

```c
/* tests/skb_test.c */
#include <kunit/test.h>
#include <linux/skbuff.h>

static void test_skb_alloc_free(struct kunit *test)
{
    struct sk_buff *skb;
    
    skb = alloc_skb(1500, GFP_KERNEL);
    KUNIT_ASSERT_NOT_NULL(test, skb);
    KUNIT_EXPECT_EQ(test, skb->len, 0);
    KUNIT_EXPECT_GE(test, skb_tailroom(skb), 1500);
    
    kfree_skb(skb);
}

static void test_skb_clone_refcount(struct kunit *test)
{
    struct sk_buff *orig, *clone;
    
    orig = alloc_skb(100, GFP_KERNEL);
    KUNIT_ASSERT_NOT_NULL(test, orig);
    
    /* Initial refcount */
    KUNIT_EXPECT_EQ(test, refcount_read(&orig->users), 1);
    KUNIT_EXPECT_EQ(test, atomic_read(&skb_shinfo(orig)->dataref), 1);
    
    /* Clone increases dataref, not users */
    clone = skb_clone(orig, GFP_KERNEL);
    KUNIT_ASSERT_NOT_NULL(test, clone);
    KUNIT_EXPECT_EQ(test, refcount_read(&orig->users), 1);
    KUNIT_EXPECT_EQ(test, refcount_read(&clone->users), 1);
    KUNIT_EXPECT_EQ(test, atomic_read(&skb_shinfo(orig)->dataref), 2);
    
    kfree_skb(clone);
    KUNIT_EXPECT_EQ(test, atomic_read(&skb_shinfo(orig)->dataref), 1);
    
    kfree_skb(orig);
}

static void test_skb_cow(struct kunit *test)
{
    struct sk_buff *orig, *clone;
    u32 *data;
    
    orig = alloc_skb(100, GFP_KERNEL);
    skb_put(orig, 4);
    data = (u32 *)orig->data;
    *data = 0x12345678;
    
    clone = skb_clone(orig, GFP_KERNEL);
    
    /* Verify shared */
    KUNIT_EXPECT_TRUE(test, skb_cloned(clone));
    
    /* COW forces copy */
    KUNIT_EXPECT_EQ(test, skb_cow(clone, 0), 0);
    KUNIT_EXPECT_FALSE(test, skb_cloned(clone));
    
    /* Verify independent buffers */
    *(u32 *)clone->data = 0xDEADBEEF;
    KUNIT_EXPECT_EQ(test, *(u32 *)orig->data, 0x12345678);
    KUNIT_EXPECT_EQ(test, *(u32 *)clone->data, 0xDEADBEEF);
    
    kfree_skb(orig);
    kfree_skb(clone);
}

static struct kunit_case skb_test_cases[] = {
    KUNIT_CASE(test_skb_alloc_free),
    KUNIT_CASE(test_skb_clone_refcount),
    KUNIT_CASE(test_skb_cow),
    {}
};

static struct kunit_suite skb_test_suite = {
    .name = "skb",
    .test_cases = skb_test_cases,
};

kunit_test_suite(skb_test_suite);
```

### 16. Fuzzing with Syzkaller

```go
// sys/linux/skb.txt (syzkaller description)
include <linux/skbuff.h>

alloc_skb(size intptr, gfp_mask flags[gfp_flags]) sk_buff_ptr
alloc_skb_with_frags(header_len intptr, data_len intptr, max_page_order intptr, errcode ptr[out, int32], gfp_mask flags[gfp_flags]) sk_buff_ptr
__napi_alloc_skb(napi ptr[in, napi_struct], length intptr, gfp_mask flags[gfp_flags]) sk_buff_ptr

skb_clone(skb sk_buff_ptr, gfp_mask flags[gfp_flags]) sk_buff_ptr
skb_copy(skb sk_buff_ptr, gfp_mask flags[gfp_flags]) sk_buff_ptr

skb_put(skb sk_buff_ptr, len intptr) ptr[out, int8]
skb_push(skb sk_buff_ptr, len intptr) ptr[out, int8]
skb_pull(skb sk_buff_ptr, len intptr) ptr[out, int8]

kfree_skb(skb sk_buff_ptr)
consume_skb(skb sk_buff_ptr)

gfp_flags = GFP_KERNEL, GFP_ATOMIC, GFP_NOWAIT, __GFP_ZERO
```

```bash
# Run syzkaller (requires setup)
./bin/syz-manager -config=skb.cfg
```

---

## Rollout/Rollback & Production Considerations

### 17. Memory Pressure Handling

```c
/* Graceful degradation under memory pressure */
struct sk_buff *resilient_alloc_skb(unsigned int size)
{
    struct sk_buff *skb;
    
    /* Try normal allocation first */
    skb = alloc_skb(size, GFP_ATOMIC | __GFP_NOWARN);
    if (likely(skb))
        return skb;
    
    /* Fallback: try smaller size */
    if (size > 512) {
        skb = alloc_skb(512, GFP_ATOMIC | __GFP_NOWARN);
        if (skb) {
            pr_warn_ratelimited("SKB allocation reduced: %u -> 512\n", size);
            return skb;
        }
    }
    
    /* Last resort: use emergency reserves (PF_MEMALLOC) */
    skb = alloc_skb(size, GFP_ATOMIC | __GFP_MEMALLOC);
    if (skb)
        pr_err_ratelimited("SKB allocation from emergency reserves\n");
    
    return skb;
}

/* Monitoring allocation failures */
static atomic_long_t skb_alloc_failures = ATOMIC_LONG_INIT(0);

void track_skb_allocation(void)
{
    struct sk_buff *skb = alloc_skb(1500, GFP_ATOMIC);
    if (!skb) {
        atomic_long_inc(&skb_alloc_failures);
        /* Alert monitoring system */
    } else {
        kfree_skb(skb);
    }
}
```

### 18. Observability & Debugging

```bash
# Tracing sk_buff allocations
sudo bpftrace -e '
kprobe:__alloc_skb {
    @allocs[comm] = count();
    @sizes[comm] = hist(arg0);
}
kprobe:kfree_skb {
    @frees[comm] = count();
}
interval:s:1 {
    print(@allocs);
    print(@frees);
    print(@sizes);
    clear(@allocs); clear(@frees); clear(@sizes);
}'

# Track allocation latency
sudo perf probe -a '__alloc_skb size=%di'
sudo perf record -e probe:__alloc_skb -aR sleep 10
sudo perf script

# Memory leak detection
echo 1 > /sys/kernel/debug/kmemleak
# ... run workload ...
cat /sys/kernel/debug/kmemleak

# Slab cache stats
sudo slabtop -o | grep skb
cat /proc/slabinfo | grep skb
```

---

## Advanced Topics

### 19. Scatter-Gather (Fragmented sk_buff)

```c
/* skb_shared_info for paged data */
struct skb_shared_info {
    atomic_t dataref;
    unsigned short nr_frags;        // Number of fragments
    skb_frag_t frags[MAX_SKB_FRAGS]; // 17 on x86_64
    struct sk_buff *frag_list;       // Chained sk_buffs
    
    /* For GRO/GSO */
    unsigned short gso_size;
    unsigned short gso_segs;
    unsigned short gso_type;
};

/* Add page fragment (zero-copy) */
int skb_add_rx_frag(struct sk_buff *skb, int i, struct page *page,
                     int off, int size, unsigned int truesize)
{
    skb_fill_page_desc(skb, i, page, off, size);
    skb->len += size;
    skb->data_len += size;
    skb->truesize += truesize;
    return 0;
}

/* Iterate fragments */
void process_fragments(struct sk_buff *skb)
{
    struct skb_shared_info *shinfo = skb_shinfo(skb);
    int i;
    
    /* Linear data */
    process_data(skb->data, skb_headlen(skb));
    
    /* Paged fragments */
    for (i = 0; i < shinfo->nr_frags; i++) {
        skb_frag_t *frag = &shinfo->frags[i];
        void *addr = skb_frag_address(frag);
        unsigned int size = skb_frag_size(frag);
        
        process_data(addr, size);
    }
    
    /* Chained sk_buffs */
    struct sk_buff *frag_iter;
    skb_walk_frags(skb, frag_iter) {
        process_fragments(frag_iter);  // Recursive
    }
}
```

### 20. eBPF Integration

```c
/* BPF program accessing sk_buff */
SEC("tc/ingress")
int tc_inspect_skb(struct __sk_buff *skb)
{
    /* BPF sees __sk_buff (stable ABI), kernel converts to sk_buff */
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;
    struct ethhdr *eth = data;
    
    /* Bounds check required */
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;
    
    /* Modify packet (affects underlying sk_buff) */
    if (eth->h_proto == bpf_htons(ETH_P_IP)) {
        struct iphdr *iph = (void *)(eth + 1);
        if ((void *)(iph + 1) > data_end)
            return TC_ACT_OK;
        
        /* Example: zero out TOS field */
        bpf_skb_store_bytes(skb, 
                             offsetof(struct ethhdr, h_proto) + sizeof(*eth) + 
                             offsetof(struct iphdr, tos),
                             &(u8){0}, 1, 0);
    }
    
    return TC_ACT_OK;
}
```

---

## References & Further Reading

**Kernel Source**:
- `include/linux/skbuff.h` - Main header
- `net/core/skbuff.c` - Implementation
- `Documentation/networking/skbuff.rst` - Official docs

**Papers**:
- "The Design and Implementation of Open vSwitch" (NSDI 2015) - sk_buff in high-performance contexts
- "Linux Kernel Networking: Implementation and Theory" - Rami Rosen

**Security**:
- CVE-2016-9793 (UAF in skb_copy_and_csum_datagram_iovec)
- CVE-2019-17666 (buffer overflow in rtlwifi driver sk_buff handling)

**Performance**:
- XDP (eXpress Data Path) - bypasses sk_buff for extreme performance
- AF_XDP (Address Family XDP) - userspace zero-copy alternative

**Tools**:
- `crash` - Kernel crash dump analyzer (inspect sk_buff in core dumps)
- `bpftrace` - Dynamic tracing of sk_buff functions
- `Syzkaller` - Kernel fuzzer with sk_buff coverage

---

## Next 3 Steps

1. **Build Kernel Module**: Create `skb_lab.c` implementing safe allocation, clone/copy, and header manipulation. Compile with `make M=$(pwd)` and test with different sizes/flags. Add KASAN (`CONFIG_KASAN=y`) to catch memory bugs.

2. **eBPF sk_buff Inspector**: Write TC/XDP BPF program that traces `__alloc_skb` and `kfree_skb`, logging size, caller, and latency. Use `bpftrace` or `libbpf` to attach and visualize allocation patterns under load.

3. **Fuzz Testing**: Set up syzkaller with sk_buff-focused corpus. Run 24hr fuzzing campaign targeting `alloc_skb`, `skb_clone`, `pskb_expand_head`. Analyze crashes with `addr2line` and propose patches upstream if novel bugs found.