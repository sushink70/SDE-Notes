// SPDX-License-Identifier: GPL-2.0
// File: c/user/loader.c
//
// Userspace loader using libbpf (the canonical modern approach).
// Loads xdp_pkt_counter.bpf.o, attaches to a NIC, then polls maps.
//
// BUILD:
//   gcc -O2 -Wall -o loader loader.c stats.c \
//       -lbpf -lelf -lz
//
// USAGE:
//   sudo ./loader <interface> [poll_interval_sec]
//   sudo ./loader eth0 1
//
// DEPENDENCIES:
//   apt install libbpf-dev libelf-dev zlib1g-dev clang llvm

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <net/if.h>            // if_nametoindex
#include <sys/resource.h>      // setrlimit for BPF memlock

#include <bpf/bpf.h>           // bpf() syscall wrappers
#include <bpf/libbpf.h>        // libbpf high-level API

// ─── Globals ─────────────────────────────────────────────────────────────────

static volatile int keep_running = 1;

// ─── Stats struct (must mirror the BPF-side definition) ──────────────────────
struct pkt_stats {
    unsigned long long packets;
    unsigned long long bytes;
    unsigned long long drops;
};

// ─── Signal Handling ─────────────────────────────────────────────────────────

static void sig_handler(int sig)
{
    (void)sig;
    keep_running = 0;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

// Raise locked memory limit so BPF maps can be allocated.
// Required on kernels < 5.11 (newer kernels use memcg accounting instead).
static void raise_memlock_limit(void)
{
    struct rlimit rl = {
        .rlim_cur = RLIM_INFINITY,
        .rlim_max = RLIM_INFINITY,
    };
    if (setrlimit(RLIMIT_MEMLOCK, &rl)) {
        fprintf(stderr, "Warning: setrlimit failed: %s\n", strerror(errno));
    }
}

// Read a PERCPU_ARRAY map value: aggregates all CPU slices into one total.
static int read_percpu_stats(int map_fd, __u32 key, struct pkt_stats *out)
{
    int nr_cpus = libbpf_num_possible_cpus();
    if (nr_cpus < 0) return -1;

    // libbpf allocates per-CPU value array: nr_cpus × sizeof(struct pkt_stats)
    struct pkt_stats *values = calloc(nr_cpus, sizeof(*values));
    if (!values) return -ENOMEM;

    int ret = bpf_map_lookup_elem(map_fd, &key, values);
    if (ret) {
        free(values);
        return ret;
    }

    // Aggregate across CPUs
    memset(out, 0, sizeof(*out));
    for (int i = 0; i < nr_cpus; i++) {
        out->packets += values[i].packets;
        out->bytes   += values[i].bytes;
        out->drops   += values[i].drops;
    }

    free(values);
    return 0;
}

// libbpf logging callback — useful during development
static int libbpf_print_fn(enum libbpf_print_level level,
                            const char *format, va_list args)
{
    if (level == LIBBPF_DEBUG)
        return 0;  // suppress debug spam; change to see full detail
    return vfprintf(stderr, format, args);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <interface> [poll_sec]\n", argv[0]);
        return 1;
    }

    const char *ifname    = argv[1];
    int         poll_sec  = (argc >= 3) ? atoi(argv[2]) : 2;

    // Validate interface
    unsigned int ifindex = if_nametoindex(ifname);
    if (!ifindex) {
        fprintf(stderr, "Interface '%s' not found: %s\n",
                ifname, strerror(errno));
        return 1;
    }

    raise_memlock_limit();
    libbpf_set_print(libbpf_print_fn);

    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    // ── Open BPF object file ─────────────────────────────────────────────
    // libbpf parses the ELF sections, sets up map/prog skeletons
    struct bpf_object *obj = bpf_object__open("xdp_pkt_counter.bpf.o");
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object: %s\n",
                strerror(-libbpf_get_error(obj)));
        return 1;
    }

    // ── Load (verifies + JIT-compiles) ───────────────────────────────────
    int ret = bpf_object__load(obj);
    if (ret) {
        fprintf(stderr, "Failed to load BPF object: %s\n", strerror(-ret));
        bpf_object__close(obj);
        return 1;
    }

    // ── Find the XDP program by name ────────────────────────────────────
    struct bpf_program *prog = bpf_object__find_program_by_name(
                                    obj, "xdp_pkt_counter");
    if (!prog) {
        fprintf(stderr, "BPF program 'xdp_pkt_counter' not found\n");
        bpf_object__close(obj);
        return 1;
    }

    int prog_fd = bpf_program__fd(prog);

    // ── Attach to NIC via XDP ─────────────────────────────────────────
    // XDP flags:
    //   XDP_FLAGS_SKB_MODE    → generic (works everywhere, slowest)
    //   XDP_FLAGS_DRV_MODE    → native driver support (fast)
    //   XDP_FLAGS_HW_MODE     → NIC offload (fastest, rare support)
    //
    // Start with SKB mode for compatibility:
    unsigned int xdp_flags = 0;  // kernel picks best available
    ret = bpf_xdp_attach(ifindex, prog_fd, xdp_flags, NULL);
    if (ret) {
        fprintf(stderr, "Failed to attach XDP to %s: %s\n",
                ifname, strerror(-ret));
        bpf_object__close(obj);
        return 1;
    }

    printf("XDP program attached to %s (ifindex=%u)\n", ifname, ifindex);
    printf("Press Ctrl+C to detach and exit.\n\n");

    // ── Get map fd for reading stats ──────────────────────────────────
    struct bpf_map *map = bpf_object__find_map_by_name(obj, "proto_stats_map");
    if (!map) {
        fprintf(stderr, "Map 'proto_stats_map' not found\n");
        goto cleanup;
    }
    int map_fd = bpf_map__fd(map);

    // ── Polling loop ─────────────────────────────────────────────────
    const char *proto_names[] = {
        [1]  = "ICMP",
        [6]  = "TCP",
        [17] = "UDP",
        [58] = "ICMPv6",
        [0]  = "TOTAL",
    };

    while (keep_running) {
        sleep(poll_sec);

        printf("\033[2J\033[H");  // clear screen
        printf("=== XDP Packet Counter — %s ===\n\n", ifname);
        printf("%-10s  %12s  %12s  %10s\n",
               "Proto", "Packets", "Bytes", "Drops");
        printf("%-10s  %12s  %12s  %10s\n",
               "----------", "------------", "------------", "----------");

        // Print total first (key=0)
        __u32 keys[] = {0, 1, 6, 17, 58, 255};
        const char *names[] = {"TOTAL", "ICMP", "TCP", "UDP", "ICMPv6", "OTHER"};

        for (int i = 0; i < 6; i++) {
            struct pkt_stats stats = {0};
            if (read_percpu_stats(map_fd, keys[i], &stats) == 0) {
                printf("%-10s  %12llu  %12llu  %10llu\n",
                       names[i],
                       stats.packets,
                       stats.bytes,
                       stats.drops);
            }
        }
    }

cleanup:
    printf("\nDetaching XDP from %s...\n", ifname);
    bpf_xdp_detach(ifindex, xdp_flags, NULL);
    bpf_object__close(obj);
    printf("Done.\n");
    return 0;
}