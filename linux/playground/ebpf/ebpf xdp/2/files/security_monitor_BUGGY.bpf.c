// SPDX-License-Identifier: GPL-2.0-only
/*
 * security_monitor_BUGGY.bpf.c
 *
 * Intentionally contains TWO bugs for debugging demonstration:
 *
 * BUG #1 — CODE BUG (verifier-caught or runtime memory issue):
 *   Location: emit_event_buggy()
 *   Type: Missing NULL-check after bpf_ringbuf_reserve()
 *   Effect: BPF verifier REJECTS the program at load time with:
 *           "R1 type=mem_or_null expected=mem"
 *   Why: The verifier models bpf_ringbuf_reserve() as returning
 *        PTR_TO_MEM_OR_NULL. Any write through the pointer without
 *        a prior NULL-check is a verifier violation.
 *   Lesson: The BPF verifier enforces memory safety via type tracking.
 *           Unlike kernel modules, a buggy BPF program fails at load,
 *           not at runtime — this is a key safety property of BPF.
 *
 * BUG #2 — LOGIC BUG (passes verifier, wrong runtime behavior):
 *   Location: bprm_check_security_buggy()
 *   Type: Operator precedence / bit-mask error in uid extraction
 *   Effect: uid is always computed as 0 (root) because of wrong shift.
 *           The blocked_uids policy check silently never fires for
 *           non-root UIDs. All exec attempts pass through regardless
 *           of UID policy entries.
 *   Why: bpf_get_current_uid_gid() packs: uid in bits[31:0], gid in bits[63:32]
 *        The correct extraction is: uid = uid_gid & 0xFFFFFFFF
 *        The bug: uid = uid_gid >> 32  (extracts GID, not UID)
 *        This passes verifier (valid u32 arithmetic) but logic is wrong.
 *   Lesson: Logic bugs pass verifier. They require behavioral testing:
 *           write a test that executes as UID 65534 and verify it IS blocked.
 *
 * How to reproduce and diagnose:
 *   See: docs/debugging_guide.md
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "security_monitor.h"

char LICENSE[] SEC("license") = "GPL";

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 18);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key,   __u32);
    __type(value, __u8);
} blocked_uids SEC(".maps");

/* ============================================================
 * BUG #1: Missing NULL-check (CODE BUG — verifier rejects)
 * ============================================================
 *
 * SYMPTOM when loading:
 *   libbpf: prog 'bprm_check_security': -- BEGIN PROG LOAD LOG --
 *   0: (85) call bpf_ringbuf_reserve#131
 *   1: (7b) *(u64 *)(r0 +0) = r1     <-- ERROR HERE
 *   R0 type=mem_or_null expected=mem
 *   processed 2 insns ... verification time 1 usec
 *   stack depth 0
 *   Error: Permission denied
 *
 * HOW TO DIAGNOSE:
 *   $ strace -e bpf ./security_monitor 2>&1 | grep -A5 "BPF_PROG_LOAD"
 *   $ bpftool prog load security_monitor.bpf.o /sys/fs/bpf/test 2>&1
 *
 *   To see full verifier log:
 *   $ cat /proc/sys/kernel/bpf_log_level   # 0=off, 1=err, 2=full
 *   Set via: sysctl kernel.bpf_stats_enabled=1
 *
 *   In libbpf: set bpf_object_open_opts.kernel_log_level = 2
 *   or set env: BPF_LOG_LEVEL=2
 *
 * FIX: Add NULL-check before writing through the pointer.
 */
static __always_inline int emit_event_buggy(__u32 type, __u32 inode)
{
    struct lsm_event *e;

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);

    /* ❌ BUG #1: Writing through e WITHOUT checking for NULL.
     *    Remove the next two lines and replace with the fix below. */
    e->event_type = type;    /* BPF verifier ERROR: R0 type=mem_or_null */
    e->inode      = inode;

    /* ✅ FIX #1 (replace the two lines above):
     *
     *   if (!e)
     *       return -1;
     *   e->event_type = type;
     *   e->inode      = inode;
     *   bpf_ringbuf_submit(e, 0);
     *   return 0;
     */

    bpf_ringbuf_submit(e, 0);
    return 0;
}

/* ============================================================
 * BUG #2: Wrong bit-shift for UID extraction (LOGIC BUG)
 * ============================================================
 *
 * SYMPTOM:
 *   Policy map has entry {uid=65534, action=DENY}.
 *   Running as UID 65534: exec is NOT blocked (should be blocked).
 *   Running as root (uid=0): exec incorrectly gets denied sometimes.
 *
 * HOW TO DIAGNOSE:
 *
 *   Step 1 — Add bpf_printk() debug trace:
 *     Insert before the map lookup:
 *       bpf_printk("uid_gid=0x%llx extracted_uid=%u\n", uid_gid, uid);
 *     Then read output:
 *       $ cat /sys/kernel/debug/tracing/trace_pipe
 *
 *   Step 2 — Inspect maps with bpftool:
 *     $ bpftool map dump id <id>   # verify entry exists for uid 65534
 *
 *   Step 3 — Attach kprobe on bpf_get_current_uid_gid and print:
 *     Write a separate kprobe BPF program to log the raw return value.
 *
 *   Step 4 — Write a unit test (see tests/test_uid_policy.sh):
 *     Run: sudo -u nobody /usr/bin/id
 *     Expect: "Operation not permitted"
 *     Actual (buggy): command runs successfully
 *
 *   Step 5 — Use bpftool prog tracelog or perf script to correlate events.
 *
 * ROOT CAUSE:
 *   bpf_get_current_uid_gid() return value layout:
 *     bits[31:0]  = uid (current_uid)
 *     bits[63:32] = gid (current_gid)
 *
 *   Bug:   uid = (__u32)(uid_gid >> 32);  // extracts GID bits → always 0 for root
 *   Fix:   uid = (__u32)(uid_gid & 0xFFFFFFFF);  // extracts UID bits
 *
 * IMPORTANT: The verifier CANNOT catch this. The arithmetic is type-safe.
 * This class of bug requires behavioral testing, not just BPF load testing.
 */
SEC("lsm/bprm_check_security")
int BPF_PROG(bprm_check_security_buggy, struct linux_binprm *bprm)
{
    __u64 uid_gid;
    __u32 uid;
    __u8 *action;

    uid_gid = bpf_get_current_uid_gid();

    /* ❌ BUG #2: Wrong shift — extracts GID (bits 63:32) not UID (bits 31:0).
     *    For normal users, GID may be 0 (wheel group) → uid always appears as 0.
     *    The UID policy check never correctly identifies non-root users. */
    uid = (__u32)(uid_gid >> 32);   /* WRONG: this is the GID, not UID */

    /* ✅ FIX #2:
     *    uid = (__u32)(uid_gid & 0xFFFFFFFF);
     */

    action = bpf_map_lookup_elem(&blocked_uids, &uid);
    if (action && *action == POLICY_DENY) {
        emit_event_buggy(EVENT_EXEC_BLOCKED, 0);
        return -EPERM;
    }

    return 0;
}
