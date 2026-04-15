// SPDX-License-Identifier: GPL-2.0
/*
 * prog_tests/xdp_filter_test.c
 *
 * Kernel selftest for xdp_filter.bpf.c
 * Location in kernel tree: tools/testing/selftests/bpf/prog_tests/
 *
 * Run:
 *   cd tools/testing/selftests/bpf
 *   make -j$(nproc)
 *   sudo ./test_progs -t xdp_filter
 *
 * Uses the BPF_PROG_TEST_RUN infrastructure to inject synthetic packets
 * directly into the BPF program without requiring a real NIC.
 *
 * References:
 *   tools/testing/selftests/bpf/prog_tests/  (read all existing tests)
 *   tools/testing/selftests/bpf/test_progs.h (test framework API)
 */

#include <test_progs.h>     /* ASSERT_OK, ASSERT_EQ, RUN_TESTS, ... */
#include <net/if.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <arpa/inet.h>
#include "xdp_filter.skel.h"

/* ── Packet builder helpers ───────────────────────────────────────────────── */

#define PKT_BUF_SZ  256

/*
 * build_ipv4_pkt - construct a minimal Ethernet + IPv4 packet in buf.
 * Returns the packet size.
 */
static size_t build_ipv4_pkt(uint8_t *buf, size_t buf_sz,
                              uint32_t src_ip_ne,    /* network byte order */
                              uint32_t dst_ip_ne)
{
    struct ethhdr *eth = (void *)buf;
    struct iphdr  *ip  = (void *)(eth + 1);
    size_t         pkt_sz = sizeof(*eth) + sizeof(*ip);

    ASSERT_GE(buf_sz, pkt_sz, "buf too small");

    memset(buf, 0, pkt_sz);

    /* Ethernet: set EtherType to IPv4 */
    eth->h_proto = htons(ETH_P_IP);

    /* IPv4 minimal header */
    ip->version  = 4;
    ip->ihl      = 5;
    ip->ttl      = 64;
    ip->protocol = IPPROTO_ICMP;
    ip->saddr    = src_ip_ne;
    ip->daddr    = dst_ip_ne;
    ip->tot_len  = htons(sizeof(*ip));

    return pkt_sz;
}

/* ── Test cases ───────────────────────────────────────────────────────────── */

/*
 * test_xdp_filter_pass
 * Verify that packets from an unknown source IP are passed (XDP_PASS = 2).
 */
static void test_xdp_filter_pass(void)
{
    struct xdp_filter_bpf *skel;
    struct bpf_prog_test_run_attr tattr = {};
    uint8_t pkt[PKT_BUF_SZ];
    size_t  pkt_sz;
    int     err, prog_fd;

    skel = xdp_filter_bpf__open_and_load();
    if (!ASSERT_OK_PTR(skel, "open_and_load"))
        return;

    /* Build a packet from 10.0.0.1 → 10.0.0.2 */
    pkt_sz = build_ipv4_pkt(pkt, sizeof(pkt),
                             inet_addr("10.0.0.1"),
                             inet_addr("10.0.0.2"));

    prog_fd = bpf_program__fd(skel->progs.xdp_filter_prog);

    tattr.prog_fd    = prog_fd;
    tattr.data_in    = pkt;
    tattr.data_size_in = pkt_sz;

    err = bpf_prog_test_run_xattr(&tattr);
    ASSERT_OK(err,          "prog_test_run");
    ASSERT_EQ(tattr.retval, XDP_PASS, "expected XDP_PASS for unknown source");

    xdp_filter_bpf__destroy(skel);
}

/*
 * test_xdp_filter_block
 * Add 192.168.1.100 to the blocklist and verify packets from it are dropped.
 */
static void test_xdp_filter_block(void)
{
    struct xdp_filter_bpf *skel;
    struct bpf_prog_test_run_attr tattr = {};
    uint8_t pkt[PKT_BUF_SZ];
    size_t  pkt_sz;
    int     err, prog_fd, map_fd;
    uint32_t block_ip;
    uint8_t  flag = 1;

    skel = xdp_filter_bpf__open_and_load();
    if (!ASSERT_OK_PTR(skel, "open_and_load"))
        return;

    /*
     * Insert into blocklist map.
     * Key MUST be in network byte order — matches BPF program's ip->saddr.
     * inet_addr() returns network-order on all POSIX platforms.
     */
    block_ip = inet_addr("192.168.1.100");      /* already network order */
    map_fd   = bpf_map__fd(skel->maps.blocklist);
    err = bpf_map_update_elem(map_fd, &block_ip, &flag, BPF_ANY);
    ASSERT_OK(err, "blocklist update");

    pkt_sz = build_ipv4_pkt(pkt, sizeof(pkt),
                             block_ip,
                             inet_addr("10.0.0.1"));

    prog_fd = bpf_program__fd(skel->progs.xdp_filter_prog);
    tattr.prog_fd      = prog_fd;
    tattr.data_in      = pkt;
    tattr.data_size_in = pkt_sz;

    err = bpf_prog_test_run_xattr(&tattr);
    ASSERT_OK(err,          "prog_test_run");
    ASSERT_EQ(tattr.retval, XDP_DROP, "expected XDP_DROP for blocked IP");

    /* Verify STAT_BLOCK counter incremented */
    {
        int stats_fd = bpf_map__fd(skel->maps.stats);
        int nr_cpus  = libbpf_num_possible_cpus();
        uint64_t vals[nr_cpus];
        uint32_t stat_idx = 1; /* STAT_BLOCK */
        uint64_t total    = 0;

        ASSERT_OK(bpf_map_lookup_elem(stats_fd, &stat_idx, vals), "stats lookup");
        for (int i = 0; i < nr_cpus; i++)
            total += vals[i];
        ASSERT_GT(total, 0ULL, "STAT_BLOCK must be > 0");
    }

    xdp_filter_bpf__destroy(skel);
}

/*
 * test_xdp_filter_rate_limit
 * Send > RATE_LIMIT_PPS packets from one source and verify drops occur.
 *
 * Note: bpf_prog_test_run uses a fake ktime that starts at 0 and does NOT
 * advance automatically. We set repeat= to simulate multiple packets in the
 * same time window and check that STAT_RATE is non-zero.
 */
static void test_xdp_filter_rate_limit(void)
{
    struct xdp_filter_bpf *skel;
    LIBBPF_OPTS(bpf_test_run_opts, opts,
        .repeat = 2000,                 /* 2000 runs in same fake time window */
    );
    uint8_t pkt[PKT_BUF_SZ];
    size_t  pkt_sz;
    int     err, prog_fd, stats_fd;
    uint64_t rate_drops = 0;

    skel = xdp_filter_bpf__open_and_load();
    if (!ASSERT_OK_PTR(skel, "open_and_load"))
        return;

    pkt_sz = build_ipv4_pkt(pkt, sizeof(pkt),
                             inet_addr("172.16.0.1"),
                             inet_addr("10.0.0.1"));

    prog_fd   = bpf_program__fd(skel->progs.xdp_filter_prog);
    opts.data_in      = pkt;
    opts.data_size_in = pkt_sz;

    /* Run 2000 times — should trigger rate limiter after 1000 */
    err = bpf_prog_test_run_opts(prog_fd, &opts);
    ASSERT_OK(err, "prog_test_run repeat");

    /* Sum per-CPU STAT_RATE (idx=2) */
    {
        int nr_cpus  = libbpf_num_possible_cpus();
        uint64_t vals[nr_cpus];
        uint32_t stat_idx = 2; /* STAT_RATE */

        stats_fd = bpf_map__fd(skel->maps.stats);
        ASSERT_OK(bpf_map_lookup_elem(stats_fd, &stat_idx, vals), "stats lookup");
        for (int i = 0; i < nr_cpus; i++)
            rate_drops += vals[i];
    }

    ASSERT_GT(rate_drops, 0ULL, "rate limiter must have dropped some packets");
    printf("  rate_drops=%llu (from 2000 packets, limit=1000)\n", rate_drops);

    xdp_filter_bpf__destroy(skel);
}

/*
 * test_xdp_filter_non_ip_pass
 * ARP and other non-IPv4 frames must be passed unconditionally.
 */
static void test_xdp_filter_non_ip_pass(void)
{
    struct xdp_filter_bpf *skel;
    LIBBPF_OPTS(bpf_test_run_opts, opts);
    uint8_t pkt[PKT_BUF_SZ] = {};
    struct ethhdr *eth = (void *)pkt;
    int err, prog_fd;

    skel = xdp_filter_bpf__open_and_load();
    if (!ASSERT_OK_PTR(skel, "open_and_load"))
        return;

    eth->h_proto = htons(0x0806);   /* ARP */

    prog_fd = bpf_program__fd(skel->progs.xdp_filter_prog);
    opts.data_in      = pkt;
    opts.data_size_in = sizeof(struct ethhdr) + 28; /* ARP is 28 bytes */

    err = bpf_prog_test_run_opts(prog_fd, &opts);
    ASSERT_OK(err, "prog_test_run arp");
    ASSERT_EQ(opts.retval, XDP_PASS, "ARP must pass");

    xdp_filter_bpf__destroy(skel);
}

/* ── Test suite entry point ───────────────────────────────────────────────── */
void test_xdp_filter(void)
{
    RUN_TESTS(test_xdp_filter_pass);
    RUN_TESTS(test_xdp_filter_block);
    RUN_TESTS(test_xdp_filter_rate_limit);
    RUN_TESTS(test_xdp_filter_non_ip_pass);
}
