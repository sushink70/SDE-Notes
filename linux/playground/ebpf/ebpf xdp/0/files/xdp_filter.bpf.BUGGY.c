// SPDX-License-Identifier: GPL-2.0
/*
 * xdp_filter.bpf.BUGGY.c — INTENTIONALLY BROKEN version for training
 *
 * BUG #1 (CODE BUG — operator error):
 *   Line ~72: `if (ip->ihl = 5)` — assignment (=) instead of comparison (==).
 *   Effect:   Always sets ihl to 5, overwrites the actual header field in-place
 *             (the verifier may catch this or it silently mutates packets).
 *             In practice clang warns: "using the result of an assignment as a
 *             condition without parentheses [-Wparentheses]" but still compiles.
 *   Fix:      Change `=` to `<`.
 *
 * BUG #2 (LOGIC BUG — byte-order mismatch):
 *   Line ~62: `__u32 src_ip = bpf_ntohl(ip->saddr);`  — converts to HOST order.
 *   Effect:   The map key is now in host byte-order, but userspace populates
 *             the blocklist using network byte-order (htonl / inet_aton).
 *             Result: blocklist lookups ALWAYS MISS — blocked IPs are never dropped.
 *   Fix:      Remove bpf_ntohl(); keep src_ip = ip->saddr (network order).
 *
 * See xdp_filter.bpf.c for the correct version and full documentation.
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define ETH_P_IP        0x0800
#define MAX_ENTRIES     65536
#define RATE_LIMIT_PPS  1000
#define NS_PER_SEC      1000000000ULL

struct pkt_count {
    __u64 count;
    __u64 last_reset_ns;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key,   __u32);
    __type(value, __u8);
} blocklist SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key,   __u32);
    __type(value, struct pkt_count);
} rate_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 4);
    __type(key,   __u32);
    __type(value, __u64);
} stats SEC(".maps");

#define STAT_PASS   0
#define STAT_BLOCK  1
#define STAT_RATE   2
#define STAT_PARSE  3

static __always_inline void inc_stat(__u32 idx)
{
    __u64 *val = bpf_map_lookup_elem(&stats, &idx);
    if (val)
        __sync_fetch_and_add(val, 1);
}

SEC("xdp")
int xdp_filter_prog(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) {
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) {
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    /* ══════════════════════════════════════════════════════════════
     * BUG #2 (LOGIC BUG): byte-order mismatch
     *   WRONG:  __u32 src_ip = bpf_ntohl(ip->saddr);
     *   REASON: ip->saddr is already in network byte-order.
     *           bpf_ntohl() converts it to host byte-order.
     *           The blocklist map was populated by userspace with
     *           htonl() values (network order), so this lookup will
     *           ALWAYS miss on little-endian machines (x86_64/arm64).
     *   FIX:    __u32 src_ip = ip->saddr;  // keep network order
     * ══════════════════════════════════════════════════════════════ */
    __u32 src_ip = bpf_ntohl(ip->saddr);   /* <── BUG #2 HERE */

    /* ══════════════════════════════════════════════════════════════
     * BUG #1 (CODE BUG): assignment used as condition
     *   WRONG:  if (ip->ihl = 5)
     *   REASON: Single `=` assigns 5 to ihl, always evaluating true.
     *           This clobbers the packet's actual IHL field in the
     *           kernel's skb/page view and skips the < 5 guard,
     *           allowing malformed headers to proceed.
     *   FIX:    if (ip->ihl < 5)
     * ══════════════════════════════════════════════════════════════ */
    if (ip->ihl = 5) {                      /* <── BUG #1 HERE */
        inc_stat(STAT_PARSE);
        return XDP_PASS;
    }

    __u8 *blocked = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked && *blocked) {
        inc_stat(STAT_BLOCK);
        return XDP_DROP;
    }

    __u64 now = bpf_ktime_get_ns();
    struct pkt_count *cnt = bpf_map_lookup_elem(&rate_map, &src_ip);

    if (!cnt) {
        struct pkt_count new_cnt = { .count = 1, .last_reset_ns = now };
        bpf_map_update_elem(&rate_map, &src_ip, &new_cnt, BPF_ANY);
        inc_stat(STAT_PASS);
        return XDP_PASS;
    }

    if (now - cnt->last_reset_ns >= NS_PER_SEC) {
        cnt->count        = 1;
        cnt->last_reset_ns = now;
        inc_stat(STAT_PASS);
        return XDP_PASS;
    }

    cnt->count++;
    if (cnt->count > RATE_LIMIT_PPS) {
        inc_stat(STAT_RATE);
        return XDP_DROP;
    }

    inc_stat(STAT_PASS);
    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
