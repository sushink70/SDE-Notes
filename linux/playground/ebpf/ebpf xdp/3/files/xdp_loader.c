// SPDX-License-Identifier: GPL-2.0
/*
 * XDP Security Loader — Userspace Control Plane
 *
 * What this does:
 *   1. Loads the BPF ELF object (compiled from xdp_security.bpf.c).
 *   2. Attaches the XDP program to a network interface.
 *   3. Manages maps: add/remove IPs from blocklist/allowlist.
 *   4. Polls statistics in a loop and prints them.
 *   5. Gracefully detaches on SIGINT/SIGTERM.
 *
 * Key concept — "libbpf skeleton":
 *   Running `bpftool gen skeleton xdp_security.bpf.o > xdp_security.skel.h`
 *   generates a type-safe C header that wraps all map/program handles.
 *   This avoids raw bpf() syscalls and is the modern idiomatic approach.
 *
 * References:
 *   tools/lib/bpf/libbpf.h
 *   Documentation/bpf/libbpf/
 *   https://libbpf.readthedocs.io/
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <arpa/inet.h>          /* inet_pton, inet_ntop                     */
#include <net/if.h>             /* if_nametoindex                           */
#include <sys/resource.h>       /* setrlimit, RLIMIT_MEMLOCK                */
#include <bpf/libbpf.h>         /* bpf_object, bpf_program, bpf_map …      */
#include <bpf/bpf.h>            /* bpf_map_update_elem, bpf_map_lookup_elem */
#include "xdp_security.skel.h"  /* auto-generated skeleton header           */

/* ─── CONSTANTS ─────────────────────────────────────────────────────────── */
#define STATS_INTERVAL_SEC   2
#define XDP_FLAGS_SKB_MODE   (1U << 1)   /* Generic/SKB mode (slower, portable) */
#define XDP_FLAGS_DRV_MODE   (1U << 2)   /* Native driver XDP (fast path)       */
#define XDP_FLAGS_HW_MODE    (1U << 3)   /* Hardware offload XDP (fastest)      */

/* ─── GLOBALS ────────────────────────────────────────────────────────────── */
static volatile int keep_running = 1;
static struct xdp_security_bpf *skel = NULL;  /* libbpf skeleton object     */
static int ifindex = -1;                       /* interface index for detach */
static __u32 attached_xdp_id = 0;             /* BPF prog ID for cleanup    */

/* ─── SIGNAL HANDLER ─────────────────────────────────────────────────────── */
static void handle_signal(int sig)
{
    (void)sig;
    keep_running = 0;
}

/* ─── LIBBPF LOGGING CALLBACK ───────────────────────────────────────────── */
/* Key concept — libbpf verbosity:
 * libbpf prints verifier logs, loading errors, etc.
 * We forward them to stderr for debugging. */
static int libbpf_print_fn(enum libbpf_print_level level,
                           const char *format, va_list args)
{
    if (level == LIBBPF_DEBUG)
        return 0;  /* suppress debug noise; change to see verifier logs */
    return vfprintf(stderr, format, args);
}

/* ─── MEMORY LOCK SETUP ──────────────────────────────────────────────────── */
/* Key concept — RLIMIT_MEMLOCK:
 * BPF maps are locked in kernel memory (mlock'd) so they don't get swapped.
 * Non-root users (and even root in older kernels) need to raise this limit.
 * Modern kernels (5.11+) use memcg accounting instead — but we set it anyway
 * for maximum compatibility. */
static void bump_memlock_rlimit(void)
{
    struct rlimit r = { RLIM_INFINITY, RLIM_INFINITY };
    if (setrlimit(RLIMIT_MEMLOCK, &r)) {
        fprintf(stderr, "Warning: failed to set RLIMIT_MEMLOCK: %s\n",
                strerror(errno));
    }
}

/* ─── STATISTICS PRINTER ─────────────────────────────────────────────────── */
/* Key concept — reading PERCPU_ARRAY maps:
 * Each CPU has its own copy.  We must call bpf_map_lookup_elem
 * with a buffer of size (num_cpus * sizeof(value)) and sum across CPUs. */

struct xdp_stats {
    __u64 total_pkts;
    __u64 dropped_blocklist;
    __u64 dropped_rate_limit;
    __u64 dropped_syn_flood;
    __u64 passed_pkts;
    __u64 passed_allowlist;
};

static void print_stats(int map_fd)
{
    int num_cpus = libbpf_num_possible_cpus();
    /* Allocate per-cpu buffer — one struct per CPU */
    struct xdp_stats *percpu_stats = calloc(num_cpus,
                                            sizeof(struct xdp_stats));
    if (!percpu_stats) {
        fprintf(stderr, "OOM allocating percpu buffer\n");
        return;
    }

    struct xdp_stats totals = {};
    __u32 key = 0;

    if (bpf_map_lookup_elem(map_fd, &key, percpu_stats) == 0) {
        for (int cpu = 0; cpu < num_cpus; cpu++) {
            totals.total_pkts          += percpu_stats[cpu].total_pkts;
            totals.dropped_blocklist   += percpu_stats[cpu].dropped_blocklist;
            totals.dropped_rate_limit  += percpu_stats[cpu].dropped_rate_limit;
            totals.dropped_syn_flood   += percpu_stats[cpu].dropped_syn_flood;
            totals.passed_pkts         += percpu_stats[cpu].passed_pkts;
            totals.passed_allowlist    += percpu_stats[cpu].passed_allowlist;
        }
    }

    printf("\033[2J\033[H");  /* clear terminal */
    printf("╔══════════════════════════════════════════╗\n");
    printf("║        XDP Security — Live Stats         ║\n");
    printf("╠══════════════════════════════════════════╣\n");
    printf("║  Total Packets       : %16llu ║\n", totals.total_pkts);
    printf("║  Passed              : %16llu ║\n", totals.passed_pkts);
    printf("║  Passed (allowlist)  : %16llu ║\n", totals.passed_allowlist);
    printf("║  Dropped (blocklist) : %16llu ║\n", totals.dropped_blocklist);
    printf("║  Dropped (rate limit): %16llu ║\n", totals.dropped_rate_limit);
    printf("║  Dropped (SYN flood) : %16llu ║\n", totals.dropped_syn_flood);
    printf("╚══════════════════════════════════════════╝\n");
    printf("  [Ctrl-C to stop]\n");

    free(percpu_stats);
}

/* ─── MAP MANAGEMENT ─────────────────────────────────────────────────────── */

static int block_ip(int map_fd, const char *ip_str)
{
    __u32 ip;
    __u8  val = 1;

    if (inet_pton(AF_INET, ip_str, &ip) != 1) {
        fprintf(stderr, "Invalid IP: %s\n", ip_str);
        return -1;
    }
    return bpf_map_update_elem(map_fd, &ip, &val, BPF_ANY);
}

static int unblock_ip(int map_fd, const char *ip_str)
{
    __u32 ip;
    if (inet_pton(AF_INET, ip_str, &ip) != 1) {
        fprintf(stderr, "Invalid IP: %s\n", ip_str);
        return -1;
    }
    return bpf_map_delete_elem(map_fd, &ip);
}

static int allowlist_ip(int map_fd, const char *ip_str)
{
    __u32 ip;
    __u8  val = 1;
    if (inet_pton(AF_INET, ip_str, &ip) != 1) {
        fprintf(stderr, "Invalid IP: %s\n", ip_str);
        return -1;
    }
    return bpf_map_update_elem(map_fd, &ip, &val, BPF_ANY);
}

/* ─── CLEANUP ────────────────────────────────────────────────────────────── */
static void cleanup(void)
{
    if (ifindex > 0) {
        /* Detach XDP program from interface */
        bpf_xdp_detach(ifindex, XDP_FLAGS_DRV_MODE, NULL);
        printf("\nXDP program detached from interface.\n");
    }
    if (skel)
        xdp_security_bpf__destroy(skel);  /* frees maps + programs */
}

/* ─── USAGE ──────────────────────────────────────────────────────────────── */
static void usage(const char *prog)
{
    fprintf(stderr,
        "Usage: %s <interface> [options]\n"
        "Options:\n"
        "  --block   <ip>    Add IP to blocklist\n"
        "  --unblock <ip>    Remove IP from blocklist\n"
        "  --allow   <ip>    Add IP to allowlist\n"
        "  --mode    drv|skb XDP attachment mode (default: drv)\n"
        "\nExamples:\n"
        "  %s eth0\n"
        "  %s eth0 --block 192.168.1.100\n"
        "  %s eth0 --allow 10.0.0.1\n",
        prog, prog, prog, prog);
}

/* ─── MAIN ───────────────────────────────────────────────────────────────── */
int main(int argc, char **argv)
{
    int    err;
    int    stats_fd;
    __u32  xdp_flags = XDP_FLAGS_DRV_MODE;  /* default: native driver mode */
    const char *ifname = NULL;

    /* Parse arguments */
    if (argc < 2) {
        usage(argv[0]);
        return 1;
    }
    ifname = argv[1];

    /* Extra options: block/unblock/allow must be handled AFTER skel open */
    const char *block_ip_str   = NULL;
    const char *unblock_ip_str = NULL;
    const char *allow_ip_str   = NULL;

    for (int i = 2; i < argc; i++) {
        if (!strcmp(argv[i], "--block")   && i+1 < argc) block_ip_str   = argv[++i];
        if (!strcmp(argv[i], "--unblock") && i+1 < argc) unblock_ip_str = argv[++i];
        if (!strcmp(argv[i], "--allow")   && i+1 < argc) allow_ip_str   = argv[++i];
        if (!strcmp(argv[i], "--mode") && i+1 < argc) {
            if (!strcmp(argv[i+1], "skb")) xdp_flags = XDP_FLAGS_SKB_MODE;
            i++;
        }
    }

    /* ── SETUP ── */
    signal(SIGINT,  handle_signal);
    signal(SIGTERM, handle_signal);
    bump_memlock_rlimit();
    libbpf_set_print(libbpf_print_fn);

    /* Resolve interface name → index */
    ifindex = if_nametoindex(ifname);
    if (!ifindex) {
        fprintf(stderr, "Interface '%s' not found: %s\n",
                ifname, strerror(errno));
        return 1;
    }

    /* ── OPEN BPF SKELETON ──
     * This mmaps the BPF ELF, creates map fds, but does NOT load yet. */
    skel = xdp_security_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }

    /* Optionally tune map sizes before loading */
    /* skel->maps.ip_blocklist->max_entries = 131072; */

    /* ── LOAD BPF PROGRAMS ──
     * This invokes the BPF verifier.  Verifier errors appear here. */
    err = xdp_security_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load BPF programs: %d\n", err);
        goto cleanup;
    }
    printf("BPF programs loaded and verified successfully.\n");

    /* ── APPLY STATIC RULES (before attaching) ── */
    if (block_ip_str) {
        err = block_ip(bpf_map__fd(skel->maps.ip_blocklist), block_ip_str);
        printf("Block %s: %s\n", block_ip_str, err ? "FAILED" : "OK");
    }
    if (unblock_ip_str) {
        err = unblock_ip(bpf_map__fd(skel->maps.ip_blocklist), unblock_ip_str);
        printf("Unblock %s: %s\n", unblock_ip_str, err ? "FAILED" : "OK");
    }
    if (allow_ip_str) {
        err = allowlist_ip(bpf_map__fd(skel->maps.ip_allowlist), allow_ip_str);
        printf("Allow %s: %s\n", allow_ip_str, err ? "FAILED" : "OK");
    }

    /* ── ATTACH XDP PROGRAM TO INTERFACE ── */
    err = bpf_xdp_attach(ifindex,
                         bpf_program__fd(skel->progs.xdp_security_prog),
                         xdp_flags, NULL);
    if (err) {
        fprintf(stderr, "Failed to attach XDP to %s (ifindex %d): %s\n"
                        "Try --mode skb for generic mode.\n",
                ifname, ifindex, strerror(-err));
        goto cleanup;
    }
    printf("XDP program attached to %s (ifindex=%d, mode=%s)\n",
           ifname, ifindex,
           (xdp_flags == XDP_FLAGS_SKB_MODE) ? "SKB/generic" : "native driver");

    /* ── STATS LOOP ── */
    stats_fd = bpf_map__fd(skel->maps.xdp_stats_map);
    while (keep_running) {
        sleep(STATS_INTERVAL_SEC);
        print_stats(stats_fd);
    }

cleanup:
    cleanup();
    return err < 0 ? 1 : 0;
}
