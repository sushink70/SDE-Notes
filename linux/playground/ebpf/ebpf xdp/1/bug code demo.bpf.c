// SPDX-License-Identifier: GPL-2.0
// File: c/bugs/bug_code_demo.bpf.c
//
// ══════════════════════════════════════════════════════════════
//  INTENTIONAL CODE BUG DEMO
// ══════════════════════════════════════════════════════════════
//
// BUG TYPE: Missing bounds check → verifier REJECTION
//
// This is the #1 mistake beginners make.
// The eBPF verifier enforces memory safety at load time.
// If you dereference a pointer without checking it against data_end,
// the verifier rejects the program with:
//   "invalid mem access 'pkt_ptr'"
//
// SYMPTOM: Program fails to load, not a runtime crash.
//   $ ip link set dev eth0 xdp obj bug_code.bpf.o sec xdp
//   Error: Prog section 'xdp' rejected: Permission denied (EPERM)
//   dmesg output:
//   [  123.456] bpf-verifier: R1 invalid mem access 'pkt_ptr'
//
// HOW TO DEBUG:
//   # See verifier output (verbose):
//   sudo bpftool prog load bug_code.bpf.o /sys/fs/bpf/test 2>&1
//   # Or use llvm-objdump to inspect bytecode:
//   llvm-objdump -d bug_code.bpf.o

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>

// ── BUGGY VERSION ──────────────────────────────────────────────────────────

SEC("xdp")
int xdp_buggy(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;

    // ❌ BUG: Accessing eth->h_proto WITHOUT checking that (eth+1) <= data_end
    // The verifier sees this as a potential out-of-bounds read and REJECTS it.
    __u16 proto = eth->h_proto;  // ← VERIFIER REJECTS HERE

    if (proto == 0x0800)
        return XDP_PASS;

    return XDP_DROP;
}

// ── FIXED VERSION ──────────────────────────────────────────────────────────
//
// FIX: Add bounds check BEFORE dereferencing any packet pointer.
// Rule: Every packet pointer access must be guarded by:
//   if ((void *)(ptr + sizeof(*ptr)) > data_end) return XDP_DROP;

SEC("xdp_fixed")
int xdp_fixed(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;

    // ✅ FIX: Check BEFORE accessing any field
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    __u16 proto = eth->h_proto;  // ← Now safe

    if (proto == 0x0800)
        return XDP_PASS;

    return XDP_DROP;
}

char LICENSE[] SEC("license") = "GPL";