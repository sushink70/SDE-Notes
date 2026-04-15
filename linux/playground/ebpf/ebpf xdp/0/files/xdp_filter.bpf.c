// SPDX-License-Identifier: GPL-2.0
/*
 * xdp_filter.bpf.c — XDP packet filter: IP blocklist + per-source rate limiting
 *
 * Kernel-side BPF program using CO-RE (Compile Once – Run Everywhere).
 * Attach via libbpf or ip link. Maps are pinned under /sys/fs/bpf/xdp_filter/.
 *
 * Build: clang -O2 -g -target bpf -D__TARGET_ARCH_x86 \
 *         -I/usr/include/x86_64-linux-gnu \
 *         -c xdp_filter.bpf.c -o xdp_filter.bpf.o
 *
 * Authors: (your name)
 * Kernel docs: Documentation/bpf/  Documentation/networking/xdp-tutorial/
 */

#include "vmlinux.h"             /* BTF-based kernel type definitions (bpftool btf dump) */
#include <bpf/bpf_helpers.h>    /* bpf_map_lookup_elem, bpf_ktime_get_ns, ... */
#include <bpf/bpf_endian.h>     /* bpf_ntohs, bpf_ntohl                       */

/* ── Compile-time constants ──────────────────────────────────────────────── */
#define ETH_P_IP        0x0800
#define IPPROTO_TCP     6
#define IPPROTO_UDP     17
#define MAX_ENTRIES     65536
#define RATE_LIMIT_PPS  1000        /* max packets/sec per source IP            */
#define NS_PER_SEC      1000000000ULL

/* ── Per-IP packet accounting ────────────────────────────────────────────── */
struct pkt_count {
    __u64 count;            /* packets seen in current window */
    __u64 last_reset_ns;    /* ktime of last window reset     */
};

/* ── BPF Maps ────────────────────────────────────────────────────────────── */

/*
 * blocklist: src_ip (network byte-order u32) → u8 flag
 * Userspace adds entries; 1 = drop all traffic from this IP.
 */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key,   __u32);
    __type(value, __u8);
} blocklist SEC(".maps");

/*
 * rate_map: src_ip → pkt_count  (LRU evicts stale entries automatically)
 */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key,   __u32);
    __type(value, struct pkt_count);
} rate_map SEC(".maps");

/*
 * stats: per-CPU array indexed by STAT_* constants.
 * Per-CPU avoids atomic contention on hot-path counters.
 */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 4);
    __type(key,   __u32);
    __type(value, __u64);
} stats SEC(".maps");

/* stats array indices */
#define STAT_PASS   0   /* packets forwarded                  */
#define STAT_BLOCK  1   /* packets dropped via blocklist      */
#define STAT_RATE   2   /* packets dropped via rate limiter   */
#define STAT_PARSE  3   /* packets that failed header parse   */

/* ── Helper: bump a stats counter (always_inline keeps verifier happy) ───── */
static __always_inline void inc_stat(__u32 idx)
{
    __u64 *val = bpf_map_lookup_elem(&stats, &idx);
    if (val)
        __sync_fetch_and_add(val, 1);   /* atomic on per-CPU slot */
}

/* ── XDP entry point ─────────────────────────────────────────────────────── */
SEC("xdp")
int xdp_filter_prog(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    /* ── 1. Parse Ethernet header ────────────────────────────────────────── */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) {   /* bounds check: REQUIRED by verifier */
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    /* Only handle IPv4; pass everything else up the stack */
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    /* ── 2. Parse IPv4 header ─────────────────────────────────────────────── */
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) {
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    /*
     * Variable-length IHL: ensure we don't walk past the header.
     * ip->ihl is in 32-bit words; minimum legal value is 5 (20 bytes).
     */
    if (ip->ihl < 5) {
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    /*
     * src_ip kept in NETWORK byte-order throughout.
     * Maps are keyed and populated by userspace using htonl() — consistent.
     */
    __u32 src_ip = ip->saddr;

    /* ── 3. Blocklist check ───────────────────────────────────────────────── */
    __u8 *blocked = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked && *blocked) {
        inc_stat(STAT_BLOCK);
        return XDP_DROP;
    }

    /* ── 4. Rate limiting (token-bucket approximation per 1-second window) ── */
    __u64 now = bpf_ktime_get_ns();
    struct pkt_count *cnt = bpf_map_lookup_elem(&rate_map, &src_ip);

    if (!cnt) {
        /* First packet from this source: insert fresh entry */
        struct pkt_count new_cnt = {
            .count        = 1,
            .last_reset_ns = now,
        };
        bpf_map_update_elem(&rate_map, &src_ip, &new_cnt, BPF_ANY);
        inc_stat(STAT_PASS);
        return XDP_PASS;
    }

    /* Reset counter when the 1-second window expires */
    if (now - cnt->last_reset_ns >= NS_PER_SEC) {
        cnt->count        = 1;
        cnt->last_reset_ns = now;
        inc_stat(STAT_PASS);
        return XDP_PASS;
    }

    /* Increment and evaluate against threshold */
    cnt->count++;
    if (cnt->count > RATE_LIMIT_PPS) {
        inc_stat(STAT_RATE);
        return XDP_DROP;
    }

    inc_stat(STAT_PASS);
    return XDP_PASS;
}

/* Required: license must be GPL for maps that use GPL-only helpers */
char LICENSE[] SEC("license") = "GPL";
