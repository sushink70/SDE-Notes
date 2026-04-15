// SPDX-License-Identifier: GPL-2.0
/*
 * XDP Security Subsystem — Kernel-Space BPF Program
 *
 * Purpose  : Drop blocked IPs, rate-limit packet storms, detect SYN floods.
 * Layer    : XDP (eXpress Data Path) — runs BEFORE skb allocation.
 * Loaded by: xdp_loader (userspace) via libbpf.
 *
 * Mental Model
 * ─────────────
 *  NIC Driver
 *      │
 *      ▼  ◄─── XDP hook fires HERE (earliest possible point)
 *  [xdp_security_prog]
 *      │
 *      ├─── XDP_DROP   : packet silently discarded in driver ring buffer
 *      ├─── XDP_PASS   : hand packet up the network stack (normal path)
 *      ├─── XDP_TX     : bounce packet back out same interface
 *      └─── XDP_REDIRECT: forward to another iface / CPU / socket
 *
 * References:
 *  - linux/samples/bpf/
 *  - Documentation/bpf/
 *  - tools/lib/bpf/
 *  - https://github.com/xdp-project/xdp-tutorial
 */

/* ─── INCLUDES ─────────────────────────────────────────────────────────────
 *
 * These are UAPI (User-space API) kernel headers.  They define the packet
 * structs (ethhdr, iphdr, tcphdr …) and BPF helper prototypes.
 *
 * Key concept — "UAPI": headers shared between kernel and userspace.
 * Found in: include/uapi/linux/  in the kernel tree.
 */
#include <linux/bpf.h>          /* core BPF types: xdp_md, BPF_MAP_TYPE_*  */
#include <linux/if_ether.h>     /* struct ethhdr, ETH_P_IP                  */
#include <linux/ip.h>           /* struct iphdr                              */
#include <linux/ipv6.h>         /* struct ipv6hdr                            */
#include <linux/tcp.h>          /* struct tcphdr                             */
#include <linux/udp.h>          /* struct udphdr                             */
#include <linux/icmp.h>         /* struct icmphdr                            */
#include <linux/in.h>           /* IPPROTO_TCP, IPPROTO_UDP …               */
#include <bpf/bpf_helpers.h>    /* bpf_map_lookup_elem, bpf_printk …        */
#include <bpf/bpf_endian.h>     /* bpf_htons, bpf_ntohs (network byte order)*/

/* ─── CONSTANTS ─────────────────────────────────────────────────────────── */
#define MAX_BLOCKED_IPS     65536   /* max entries in blocklist map          */
#define MAX_TRACKED_IPS     100000  /* max entries in rate-limit map         */
#define RATE_LIMIT_PKTS     500     /* pkts/sec threshold before auto-block  */
#define SYN_FLOOD_THRESHOLD 200     /* SYN pkts/sec before blocking src      */
#define NANOSEC_PER_SEC     1000000000ULL

/* ─── BPF MAP DEFINITIONS ───────────────────────────────────────────────────
 *
 * Key concept — "BPF Map":
 *   A key-value store that lives in kernel memory.
 *   Both kernel BPF programs AND userspace programs can read/write maps.
 *   Think of it as shared memory between kernel and userspace.
 *
 * Map Types used here:
 *   BPF_MAP_TYPE_HASH     — hash table, O(1) lookup, fixed max_entries
 *   BPF_MAP_TYPE_LRU_HASH — like HASH but evicts least-recently-used entries
 *                           (prevents memory exhaustion from unseen IPs)
 *   BPF_MAP_TYPE_ARRAY    — indexed by integer, useful for counters/stats
 *   BPF_MAP_TYPE_PERCPU_ARRAY — one slot per CPU, avoids lock contention
 *
 * SEC(".maps") — tells the BPF ELF loader to place this in the maps section.
 */

/* Blocklist: src_ip → blocked (1=blocked, 0=allowed) */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_BLOCKED_IPS);
    __type(key,   __u32);   /* IPv4 source address (network byte order) */
    __type(value, __u8);    /* 1 = DROP, 0 = PASS                       */
} ip_blocklist SEC(".maps");

/* Allowlist / whitelist: src_ip → 1 (always pass, skip all checks) */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key,   __u32);
    __type(value, __u8);
} ip_allowlist SEC(".maps");

/* Per-IP packet rate tracking: src_ip → {count, timestamp_ns} */
struct rate_entry {
    __u64 count;         /* packets seen in current window */
    __u64 window_start;  /* nanosecond timestamp of window start */
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key,   __u32);
    __type(value, struct rate_entry);
} pkt_rate_map SEC(".maps");

/* Per-IP SYN flood tracking: src_ip → {syn_count, timestamp_ns} */
struct syn_entry {
    __u64 syn_count;
    __u64 window_start;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key,   __u32);
    __type(value, struct syn_entry);
} syn_flood_map SEC(".maps");

/* Statistics counters (per-CPU for lock-free updates) */
struct stats {
    __u64 total_pkts;
    __u64 dropped_blocklist;
    __u64 dropped_rate_limit;
    __u64 dropped_syn_flood;
    __u64 passed_pkts;
    __u64 passed_allowlist;
};

/* Key concept — PERCPU_ARRAY:
 * Each CPU has its own copy of the stats struct.
 * No atomic operations needed → zero contention → very fast.
 * Userspace sums all per-CPU values to get totals. */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key,   __u32);
    __type(value, struct stats);
} xdp_stats_map SEC(".maps");

/* ─── HELPER MACROS ──────────────────────────────────────────────────────── */

/* Key concept — Bounds Check:
 * The BPF verifier REJECTS any program that might access memory out of bounds.
 * Every pointer dereference MUST be guarded: (ptr + 1) > data_end → return.
 * This is not optional — the kernel will refuse to load unchecked programs. */
#define BOUNDS_CHECK(ptr, end) \
    if ((void *)((ptr) + 1) > (end)) return XDP_DROP

/* Safe inline stat increment — looks up percpu array slot 0 */
static __always_inline void stats_inc(__u64 *field_offset_unused,
                                      int field)
{
    __u32 key = 0;
    struct stats *s = bpf_map_lookup_elem(&xdp_stats_map, &key);
    if (!s) return;
    /* We use __sync_fetch_and_add for the percpu case even though
     * percpu maps don't need it; it's a good habit for shared maps. */
    switch (field) {
        case 0: __sync_fetch_and_add(&s->total_pkts,          1); break;
        case 1: __sync_fetch_and_add(&s->dropped_blocklist,   1); break;
        case 2: __sync_fetch_and_add(&s->dropped_rate_limit,  1); break;
        case 3: __sync_fetch_and_add(&s->dropped_syn_flood,   1); break;
        case 4: __sync_fetch_and_add(&s->passed_pkts,         1); break;
        case 5: __sync_fetch_and_add(&s->passed_allowlist,    1); break;
    }
}

/* ─── RATE LIMITER ───────────────────────────────────────────────────────── */

/* Returns 1 if src_ip exceeds RATE_LIMIT_PKTS pkts/sec, else 0.
 *
 * Algorithm — Sliding Window (1 second):
 *   1. Get current time (bpf_ktime_get_ns).
 *   2. If elapsed >= 1s → reset window, count = 1, allow.
 *   3. Else → increment count.
 *   4. If count > threshold → BLOCK.
 *
 * Why bpf_ktime_get_ns?
 *   It's a BPF helper that returns monotonic nanoseconds.
 *   We cannot call gettimeofday() from kernel BPF programs.
 */
static __always_inline int is_rate_limited(__u32 src_ip)
{
    struct rate_entry *entry;
    struct rate_entry  new_entry;
    __u64 now = bpf_ktime_get_ns();

    entry = bpf_map_lookup_elem(&pkt_rate_map, &src_ip);
    if (!entry) {
        /* First packet from this IP */
        new_entry.count        = 1;
        new_entry.window_start = now;
        bpf_map_update_elem(&pkt_rate_map, &src_ip,
                            &new_entry, BPF_ANY);
        return 0;
    }

    if ((now - entry->window_start) >= NANOSEC_PER_SEC) {
        /* New 1-second window */
        entry->count        = 1;
        entry->window_start = now;
        return 0;
    }

    entry->count++;
    if (entry->count > RATE_LIMIT_PKTS)
        return 1;

    return 0;
}

/* ─── SYN FLOOD DETECTOR ──────────────────────────────────────────────────── */

/* Returns 1 if src_ip is sending too many SYN packets (SYN flood). */
static __always_inline int is_syn_flood(__u32 src_ip,
                                        struct tcphdr *tcp)
{
    struct syn_entry *entry;
    struct syn_entry  new_entry;
    __u64 now = bpf_ktime_get_ns();

    /* Only care about SYN packets (SYN=1, ACK=0) */
    if (!tcp->syn || tcp->ack)
        return 0;

    entry = bpf_map_lookup_elem(&syn_flood_map, &src_ip);
    if (!entry) {
        new_entry.syn_count    = 1;
        new_entry.window_start = now;
        bpf_map_update_elem(&syn_flood_map, &src_ip,
                            &new_entry, BPF_ANY);
        return 0;
    }

    if ((now - entry->window_start) >= NANOSEC_PER_SEC) {
        entry->syn_count    = 1;
        entry->window_start = now;
        return 0;
    }

    entry->syn_count++;
    if (entry->syn_count > SYN_FLOOD_THRESHOLD)
        return 1;

    return 0;
}

/* ─── MAIN XDP PROGRAM ───────────────────────────────────────────────────────
 *
 * Key concept — SEC("xdp"):
 *   This annotation marks the function as an XDP program.
 *   The BPF ELF loader reads this section name to know which attach type to use.
 *
 * struct xdp_md — the XDP metadata context:
 *   data     : __u32 pointer to start of packet data
 *   data_end : __u32 pointer to end of packet data
 *   data_meta: __u32 metadata area (before data, for passing info to TC layer)
 *   ingress_ifindex: interface index packet arrived on
 *   rx_queue_index : receive queue index
 */
SEC("xdp")
int xdp_security_prog(struct xdp_md *ctx)
{
    /* Key concept — void* casting from __u32:
     * xdp_md stores data/data_end as __u32 offsets.
     * We cast them to void* for pointer arithmetic.
     * (long) cast avoids 32-bit truncation on 64-bit systems. */
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr  *eth;
    struct iphdr   *ip  = NULL;
    struct tcphdr  *tcp = NULL;
    __u32           src_ip = 0;
    int             ret;

    /* ── STATS: total packets ── */
    stats_inc(NULL, 0);

    /* ─────────────────────────────────────────────────────────────
     * LAYER 2 — Ethernet Header Parse
     * Layout: [dst_mac:6][src_mac:6][ethertype:2][payload...]
     * ───────────────────────────────────────────────────────────── */
    eth = data;
    BOUNDS_CHECK(eth, data_end);  /* verifier: ensure eth fits in packet */

    /* Only process IPv4 for now (0x0800).
     * bpf_htons converts 0x0800 from host to network byte order. */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    /* ─────────────────────────────────────────────────────────────
     * LAYER 3 — IPv4 Header Parse
     * Layout: [ver/ihl:1][tos:1][tot_len:2][id:2][frag:2]
     *         [ttl:1][proto:1][checksum:2][saddr:4][daddr:4][options...]
     * ───────────────────────────────────────────────────────────── */
    ip = (struct iphdr *)(eth + 1);
    BOUNDS_CHECK(ip, data_end);

    src_ip = ip->saddr;  /* Network byte order — matches map keys */

    /* ── ALLOWLIST CHECK: always pass trusted IPs ── */
    {
        __u8 *allowed = bpf_map_lookup_elem(&ip_allowlist, &src_ip);
        if (allowed && *allowed == 1) {
            stats_inc(NULL, 5);
            return XDP_PASS;
        }
    }

    /* ── BLOCKLIST CHECK: drop known bad IPs ── */
    {
        __u8 *blocked = bpf_map_lookup_elem(&ip_blocklist, &src_ip);
        if (blocked && *blocked == 1) {
            stats_inc(NULL, 1);
            /* Optional: log to BPF ring buffer for audit trail */
            bpf_printk("XDP DROP: blocklisted src=%pI4\n", &src_ip);
            return XDP_DROP;
        }
    }

    /* ── RATE LIMIT CHECK ── */
    if (is_rate_limited(src_ip)) {
        /* Auto-add to blocklist to avoid future lookups */
        __u8 block_val = 1;
        bpf_map_update_elem(&ip_blocklist, &src_ip, &block_val, BPF_ANY);
        stats_inc(NULL, 2);
        bpf_printk("XDP DROP: rate-limit src=%pI4\n", &src_ip);
        return XDP_DROP;
    }

    /* ─────────────────────────────────────────────────────────────
     * LAYER 4 — TCP Header Parse (if TCP)
     * ───────────────────────────────────────────────────────────── */
    if (ip->protocol == IPPROTO_TCP) {
        /* ip->ihl = IP header length in 32-bit words (min 5 = 20 bytes).
         * We must skip options: tcp starts at ip + (ihl * 4) bytes.
         * Key concept — ihl: Internet Header Length field. */
        __u32 ip_hdr_size = ip->ihl * 4;

        /* Ensure ip_hdr_size is at least 20 bytes (minimum valid IHL=5) */
        if (ip_hdr_size < sizeof(struct iphdr))
            return XDP_DROP;

        tcp = (struct tcphdr *)((void *)ip + ip_hdr_size);
        BOUNDS_CHECK(tcp, data_end);

        /* ── SYN FLOOD DETECTION ── */
        if (is_syn_flood(src_ip, tcp)) {
            __u8 block_val = 1;
            bpf_map_update_elem(&ip_blocklist, &src_ip, &block_val, BPF_ANY);
            stats_inc(NULL, 3);
            bpf_printk("XDP DROP: SYN flood src=%pI4\n", &src_ip);
            return XDP_DROP;
        }
    }

    /* ── ALL CHECKS PASSED ── */
    stats_inc(NULL, 4);
    return XDP_PASS;
}

/* ─── LICENSE ────────────────────────────────────────────────────────────────
 * REQUIRED: kernel requires GPL-compatible license for BPF programs
 * that use GPL-only helpers (like bpf_ktime_get_ns). */
char _license[] SEC("license") = "GPL";
