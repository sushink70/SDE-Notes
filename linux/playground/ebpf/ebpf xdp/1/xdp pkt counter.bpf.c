// SPDX-License-Identifier: GPL-2.0
// File: c/kern/xdp_pkt_counter.bpf.c
//
// XDP (eXpress Data Path) packet counter — runs in kernel context
// at the earliest point a packet can be processed (driver/NIC level).
//
// HOW TO READ THIS FILE:
//   Every eBPF program is a C function that the kernel JIT-compiles.
//   The verifier checks it for safety BEFORE loading.
//   Map declarations become shared memory between kernel and userspace.
//
// BUILD:
//   clang -O2 -g -Wall -target bpf \
//         -D__TARGET_ARCH_x86 \
//         -I/usr/include/$(uname -m)-linux-gnu \
//         -c xdp_pkt_counter.bpf.c -o xdp_pkt_counter.bpf.o
//
// LOAD (manual, for learning):
//   ip link set dev eth0 xdp obj xdp_pkt_counter.bpf.o sec xdp
//
// LOAD (via loader program):
//   ./loader eth0

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// ─── Data Structures ─────────────────────────────────────────────────────────

// Per-protocol stats stored in the BPF map
struct pkt_stats {
    __u64 packets;   // total packet count
    __u64 bytes;     // total byte count
    __u64 drops;     // packets dropped by this program
};

// Key for the stats map (L4 protocol number: TCP=6, UDP=17, ICMP=1, etc.)
// We also use key 0 for "total" and key 255 for "other"
#define PROTO_KEY_TOTAL  0
#define PROTO_KEY_OTHER  255

// ─── BPF Maps ────────────────────────────────────────────────────────────────
//
// LEARNING NOTE: Maps are the IPC mechanism between eBPF and userspace.
// They persist in kernel memory; userspace reads them via bpf() syscall.
// The SEC() macro marks sections that libbpf/bpftool parse to auto-pin maps.

// Per-CPU array map: each CPU has its own slot — ZERO lock contention.
// Aggregation happens in userspace when reading.
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 256);         // one slot per L4 proto (0-255)
    __type(key,   __u32);
    __type(value, struct pkt_stats);
} proto_stats_map SEC(".maps");

// Hash map: tracks per-source-IP drop decisions (for rate limiting demo)
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH); // LRU: auto-evicts oldest entries
    __uint(max_entries, 1024);
    __type(key,   __u32);  // src IPv4 addr
    __type(value, __u64);  // drop counter
} src_drop_map SEC(".maps");

// ─── Helpers ─────────────────────────────────────────────────────────────────

// Safe bounds-checked pointer advance.
// The verifier REQUIRES every pointer be checked against data_end before
// dereferencing. This helper centralises that check.
//
// Returns: pointer advanced by `size` bytes, or NULL if out of bounds.
static __always_inline void *safe_advance(void *ptr, void *data_end,
                                          __u32 size)
{
    if ((__u8 *)ptr + size > (__u8 *)data_end)
        return NULL;
    return (__u8 *)ptr + size;
}

// Update the per-CPU stats for a given protocol key
static __always_inline void record_packet(__u32 proto_key,
                                          __u32 pkt_len,
                                          int dropped)
{
    struct pkt_stats *s;
    __u32 total_key = PROTO_KEY_TOTAL;

    // ── per-protocol slot
    s = bpf_map_lookup_elem(&proto_stats_map, &proto_key);
    if (s) {
        s->packets++;
        s->bytes   += pkt_len;
        s->drops   += dropped;
    }

    // ── total slot
    s = bpf_map_lookup_elem(&proto_stats_map, &total_key);
    if (s) {
        s->packets++;
        s->bytes   += pkt_len;
        s->drops   += dropped;
    }
}

// ─── Main XDP Program ────────────────────────────────────────────────────────
//
// SEC("xdp") tells libbpf this is an XDP attach point.
// The function receives an xdp_md context: pointers to the raw packet frame.
//
// Return values (XDP actions):
//   XDP_PASS    → send packet up the normal network stack
//   XDP_DROP    → silently discard (fastest path, no alloc)
//   XDP_TX      → bounce packet back out same NIC
//   XDP_REDIRECT → send to another NIC/CPU
//   XDP_ABORTED → drop + trigger xdp:xdp_exception tracepoint (debugging)

SEC("xdp")
int xdp_pkt_counter(struct xdp_md *ctx)
{
    // Raw packet bounds — everything must stay between data and data_end
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    __u32 pkt_len    = (__u32)(data_end - data);
    __u32 proto_key  = PROTO_KEY_OTHER;
    int   action     = XDP_PASS;

    // ── Layer 2: Ethernet header ──────────────────────────────────────────
    struct ethhdr *eth = data;

    // CRITICAL: Must verify eth header fits in packet before accessing fields.
    // Without this check the verifier REJECTS the program.
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    __u16 h_proto = bpf_ntohs(eth->h_proto);

    // ── Layer 3: IP ───────────────────────────────────────────────────────
    if (h_proto == ETH_P_IP) {
        struct iphdr *iph = (void *)(eth + 1);
        if ((void *)(iph + 1) > data_end)
            return XDP_DROP;

        // Verify IHL (internet header length) — variable-length IP header
        // iph->ihl is the number of 32-bit words; min valid is 5 (= 20 bytes)
        if (iph->ihl < 5)
            return XDP_DROP;

        proto_key = iph->protocol;   // TCP=6, UDP=17, ICMP=1, …

        // ── Layer 4 header access (demo: parse TCP flags) ─────────────────
        if (iph->protocol == IPPROTO_TCP) {
            // Advance past the IP header (variable length via ihl*4)
            struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
            if ((void *)(tcph + 1) > data_end)
                goto record;

            // Example policy: drop TCP SYN-only (no ACK) from un-known sources
            // Real use-case: SYN-flood mitigation at XDP layer
            if (tcph->syn && !tcph->ack) {
                __u32 src_ip = iph->saddr;
                __u64 *drop_cnt = bpf_map_lookup_elem(&src_drop_map, &src_ip);
                if (!drop_cnt) {
                    // First SYN — allow + track
                    __u64 init = 1;
                    bpf_map_update_elem(&src_drop_map, &src_ip, &init,
                                        BPF_NOEXIST);
                } else {
                    __sync_fetch_and_add(drop_cnt, 1);
                    // After 10 SYN-only packets from same src → drop
                    if (*drop_cnt > 10) {
                        action = XDP_DROP;
                        record_packet(proto_key, pkt_len, 1);
                        return action;
                    }
                }
            }
        }

    } else if (h_proto == ETH_P_IPV6) {
        struct ipv6hdr *ip6h = (void *)(eth + 1);
        if ((void *)(ip6h + 1) > data_end)
            return XDP_DROP;
        proto_key = ip6h->nexthdr;

    } else if (h_proto == ETH_P_ARP) {
        proto_key = 0xFE;  // custom key for ARP
    }

record:
    record_packet(proto_key, pkt_len, 0);

    // Debug: emit a trace message readable via /sys/kernel/debug/tracing/trace_pipe
    // ONLY enable in development — has ~100ns overhead per call
#ifdef DEBUG_TRACE
    bpf_printk("XDP: proto=%u len=%u action=%d\n", proto_key, pkt_len, action);
#endif

    return action;
}

// ─── License ─────────────────────────────────────────────────────────────────
// MANDATORY: Without this the verifier rejects the program.
// Use GPL-compatible license to access GPL-exported kernel helpers.
char LICENSE[] SEC("license") = "GPL";