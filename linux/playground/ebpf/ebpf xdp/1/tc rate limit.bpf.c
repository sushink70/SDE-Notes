// SPDX-License-Identifier: GPL-2.0
// File: c/kern/tc_rate_limit.bpf.c
//
// TC (Traffic Control) classifier — attaches AFTER the network stack
// processes a packet (egress). Useful for:
//   - Shaping outbound traffic
//   - Marking DSCP/TOS bits
//   - Logging egress per flow
//
// DIFFERENCE FROM XDP:
//   XDP = ingress only, before skb allocation, fastest path.
//   TC  = ingress OR egress, full sk_buff available, slightly heavier.
//
// ATTACH:
//   tc qdisc add dev eth0 clsact
//   tc filter add dev eth0 egress bpf da obj tc_rate_limit.bpf.o sec tc
//
// DETACH:
//   tc filter del dev eth0 egress
//   tc qdisc del dev eth0 clsact

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Token-bucket rate limiter state per destination IP
struct token_bucket {
    __u64 tokens;          // current tokens (bytes)
    __u64 last_refill_ns;  // last refill timestamp (nanoseconds)
};

#define BUCKET_CAPACITY   (1 * 1024 * 1024)   // 1 MB burst
#define REFILL_RATE_BPS   (100 * 1024)         // 100 KB/s refill rate

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 4096);
    __type(key,   __u32);  // dst IPv4
    __type(value, struct token_bucket);
} rate_buckets SEC(".maps");

// Per-CPU drop counter for observability
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key,   __u32);
    __type(value, __u64);
} egress_drops SEC(".maps");

SEC("tc")
int tc_rate_limiter(struct __sk_buff *skb)
{
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return TC_ACT_OK;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return TC_ACT_OK;

    __u32 dst_ip  = iph->daddr;
    __u32 pkt_len = skb->len;
    __u64 now_ns  = bpf_ktime_get_ns();

    struct token_bucket *bucket = bpf_map_lookup_elem(&rate_buckets, &dst_ip);
    if (!bucket) {
        // First packet to this dst — create full bucket
        struct token_bucket new_bucket = {
            .tokens        = BUCKET_CAPACITY,
            .last_refill_ns = now_ns,
        };
        bpf_map_update_elem(&rate_buckets, &dst_ip, &new_bucket, BPF_ANY);
        return TC_ACT_OK;
    }

    // Refill tokens based on elapsed time
    __u64 elapsed_ns = now_ns - bucket->last_refill_ns;
    // tokens_to_add = elapsed_ns * REFILL_RATE_BPS / 1e9
    // Avoid __u64 division issues — use shift approximation for 100KB/s
    // 100KB/s ≈ 100 bytes per 1ms = 1 byte per 10µs = 1 byte per 10000ns
    __u64 new_tokens = elapsed_ns / 10000;  // ~100KB/s approximation
    bucket->tokens += new_tokens;
    if (bucket->tokens > BUCKET_CAPACITY)
        bucket->tokens = BUCKET_CAPACITY;
    bucket->last_refill_ns = now_ns;

    // Consume tokens
    if (bucket->tokens >= pkt_len) {
        bucket->tokens -= pkt_len;
        return TC_ACT_OK;
    }

    // Not enough tokens — drop
    __u32 key = 0;
    __u64 *drops = bpf_map_lookup_elem(&egress_drops, &key);
    if (drops)
        __sync_fetch_and_add(drops, 1);

    return TC_ACT_SHOT;  // TC equivalent of XDP_DROP
}

char LICENSE[] SEC("license") = "GPL";