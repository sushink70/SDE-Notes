// ═══════════════════════════════════════════════════════════════════════════
//  BUG DEMONSTRATION FILE — XDP Security
//  Two intentional bugs to teach debugging methodology.
//
//  Bug #1: CODE BUG — Missing bounds check (verifier will REJECT this)
//  Bug #2: LOGIC BUG — Wrong byte order comparison (silent correctness error)
// ═══════════════════════════════════════════════════════════════════════════

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key,   __u32);
    __type(value, __u8);
} blocklist SEC(".maps");

// ═══════════════════════════════════════════════════════════════════════════
//  BUG #1: CODE BUG — Missing bounds check
//
//  What is a "bounds check"?
//    The BPF verifier statically analyzes every possible execution path.
//    It tracks pointer ranges. If a pointer might go beyond data_end,
//    the verifier REJECTS the program with: "invalid mem access 'inv'"
//    Your program never runs — the kernel refuses to load it.
//
//  The bug:
//    We access ip->saddr WITHOUT checking that the full iphdr fits
//    within [data, data_end]. If a short packet arrives, we'd read
//    beyond the packet boundary — undefined behavior in hardware.
//
//  How to reproduce:
//    Compile: clang -target bpf -O2 -c xdp_bugs.bpf.c -o xdp_bugs.bpf.o
//    Load: bpftool prog load xdp_bugs.bpf.o /sys/fs/bpf/xdp_bugs
//    Error: "R2 invalid mem access 'inv'" (or similar verifier message)
// ═══════════════════════════════════════════════════════════════════════════
SEC("xdp/bug_code")
int xdp_bug_missing_bounds_check(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;

    // ✓ CORRECT: bounds check for ethernet header
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *ip = (struct iphdr *)(eth + 1);

    // ✗ BUG: NO bounds check for IP header!
    //   The verifier sees ip is a pointer into packet memory.
    //   Without checking (ip + 1) <= data_end, the verifier
    //   cannot prove ip->saddr is safe to read.
    //   VERIFIER ERROR: "invalid mem access 'inv'"
    __u32 src_ip = ip->saddr;   // ← BUG HERE — unguarded dereference

    __u8 *blocked = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked && *blocked == 1)
        return XDP_DROP;

    return XDP_PASS;
}

/*
 * ─── HOW TO DIAGNOSE BUG #1 ──────────────────────────────────────────────
 *
 * Step 1: Compile and try to load:
 *   clang -target bpf -g -O2 -c xdp_bugs.bpf.c -o xdp_bugs.bpf.o
 *   sudo bpftool prog load xdp_bugs.bpf.o /sys/fs/bpf/test_prog
 *
 * Step 2: Read the verifier output:
 *   libbpf: -- BEGIN DUMP CORE RELATIONS --
 *   ...
 *   13: (61) r3 = *(u32 *)(r2 +12)    ; ip->saddr
 *       R2 invalid mem access 'inv'
 *   processed 13 insns ... verification time 0 msec, peak states 1
 *   Error: failed to load BPF program: Permission denied
 *
 * Step 3: Understand verifier message:
 *   "R2 invalid mem access 'inv'" means register R2 holds an
 *   "invalid" (unbounded) pointer — the verifier lost track of bounds.
 *   Instruction "r3 = *(u32 *)(r2 +12)" is reading ip->saddr (offset 12).
 *
 * Step 4: Read verifier dump with verbose:
 *   sudo bpftool prog load xdp_bugs.bpf.o /sys/fs/bpf/test_prog \
 *        2>&1 | head -100
 *   # Or enable libbpf verbosity in your loader:
 *   libbpf_set_print(verbose_print_fn);
 *
 * ─── FIX FOR BUG #1 ───────────────────────────────────────────────────────
 * Add bounds check before dereferencing ip:
 *
 *   struct iphdr *ip = (struct iphdr *)(eth + 1);
 *   if ((void *)(ip + 1) > data_end)      // ← ADD THIS
 *       return XDP_DROP;
 *   __u32 src_ip = ip->saddr;             // ← now safe
 */

// ═══════════════════════════════════════════════════════════════════════════
//  BUG #2: LOGIC BUG — Wrong byte order comparison
//
//  What is "byte order"?
//    Numbers in memory can be stored in two ways:
//      Big-endian    (network order): most significant byte first
//                    e.g., 192.168.1.1 = 0xC0A80101
//      Little-endian (host order):    least significant byte first
//                    e.g., 192.168.1.1 = 0x0101A8C0
//
//    Network protocols (Ethernet, IP) use BIG-endian (network byte order).
//    x86/ARM CPUs use LITTLE-endian (host byte order).
//    You MUST convert between them when comparing.
//
//  The bug:
//    We check if h_proto == ETH_P_IP by comparing in host byte order.
//    ETH_P_IP = 0x0800 in host order.
//    But eth->h_proto is in NETWORK byte order = 0x0008 on little-endian.
//    0x0008 != 0x0800  → we NEVER process IPv4 packets!
//    No errors, no crashes — just silently wrong behavior.
//
//  This bug PASSES the verifier but produces WRONG results at runtime.
//
//  How to detect:
//    Load the program. Send IPv4 traffic. All packets pass through
//    (XDP_PASS) even blocked IPs — blocklist has zero effect.
// ═══════════════════════════════════════════════════════════════════════════
SEC("xdp/bug_logic")
int xdp_bug_byte_order(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    // ✗ BUG: Comparing network byte order value with host byte order constant.
    //   ETH_P_IP is defined as 0x0800 (host byte order).
    //   eth->h_proto is in network byte order = 0x0008 on x86.
    //   This comparison is ALWAYS false on little-endian machines.
    //   Effect: we never enter the IPv4 processing block → blocklist ignored.
    if (eth->h_proto != ETH_P_IP)     // ← BUG: should be bpf_htons(ETH_P_IP)
        return XDP_PASS;

    struct iphdr *ip = (struct iphdr *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_DROP;

    __u32 src_ip = ip->saddr;
    __u8 *blocked = bpf_map_lookup_elem(&blocklist, &src_ip);
    if (blocked && *blocked == 1)
        return XDP_DROP;

    return XDP_PASS;
}

/*
 * ─── HOW TO DIAGNOSE BUG #2 ──────────────────────────────────────────────
 *
 * Step 1: Load the program, attach to eth0.
 *
 * Step 2: Add an IP to the blocklist:
 *   sudo bpftool map update name blocklist key 0x01 0x00 0x00 0x7f \
 *        value 0x01
 *   # 127.0.0.1 in network byte order = 0x7f 0x00 0x00 0x01
 *   # We store in network byte order (same as ip->saddr)
 *
 * Step 3: Send a packet from 127.0.0.1 and check:
 *   ping -c 1 -I lo 127.0.0.1
 *   # XDP on loopback for testing
 *
 * Step 4: Check stats map — total_pkts increments but dropped_blocklist = 0.
 *   All packets PASS even though IP is blocked → logic bug confirmed.
 *
 * Step 5: Use bpf_printk to trace the issue:
 *   Add inside the XDP function:
 *   bpf_printk("h_proto=%x, expected=%x\n",
 *              eth->h_proto, bpf_htons(ETH_P_IP));
 *   Then: sudo cat /sys/kernel/debug/tracing/trace_pipe
 *   Output: h_proto=8  expected=8  ← wait, 0x0008 in decimal = 8
 *   Expected (host): 0x0800 = 2048 decimal
 *   That mismatch reveals the byte order problem.
 *
 * Step 6: Add bpftool prog trace:
 *   sudo bpftool prog tracelog
 *
 * ─── FIX FOR BUG #2 ───────────────────────────────────────────────────────
 * Use bpf_htons() to convert the constant to network byte order:
 *
 *   if (eth->h_proto != bpf_htons(ETH_P_IP))   // ← CORRECT
 *       return XDP_PASS;
 *
 * bpf_htons(0x0800) on little-endian = 0x0008 → matches eth->h_proto.
 *
 * Mental model for byte order in BPF:
 *   RULE: Everything arriving from the network is in NETWORK (big-endian) order.
 *   RULE: Always use bpf_htons()/bpf_ntohs() when comparing protocol fields.
 *   RULE: Map keys derived from packet data (like ip->saddr) stay in
 *         network order — be consistent: always store/compare in one order.
 */

char _license[] SEC("license") = "GPL";

// ═══════════════════════════════════════════════════════════════════════════
//  DEBUGGING TOOLKIT SUMMARY
//
//  Tool                What it shows
//  ──────────────────  ──────────────────────────────────────────────────
//  bpftool prog show   List all loaded BPF programs + IDs
//  bpftool prog dump   Disassemble BPF bytecode (pre-JIT)
//  bpftool map show    List all maps + sizes
//  bpftool map dump    Print map contents as hex
//  bpftool net show    Show XDP programs attached to interfaces
//  trace_pipe          bpf_printk() output stream
//  bpftool prog trace  Real-time instruction-level tracing (kernel 5.15+)
//  perf stat           CPU cycles / cache misses for BPF programs
//  ip link show        Interface stats including XDP drop counters
//
//  GDB cannot debug BPF kernel programs.
//  Use bpf_printk() as your "printf debugging" equivalent.
//  Use bpftool map dump to inspect state at any point.
// ═══════════════════════════════════════════════════════════════════════════
