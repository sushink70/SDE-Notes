// SPDX-License-Identifier: GPL-2.0-only
/*
 * security_monitor.bpf.c — BPF LSM (Linux Security Module) program.
 *
 * What this does:
 *   Attaches to three LSM security hooks via BPF_PROG_TYPE_LSM:
 *     1. bprm_check_security  → intercept execve(), enforce exec policy
 *     2. file_open            → audit/deny sensitive file access
 *     3. ptrace_access_check  → block ptrace on non-child processes
 *
 * Design choices:
 *   - Uses BPF CO-RE (Compile Once – Run Everywhere) via vmlinux.h +
 *     BPF_CORE_READ() macros. No kernel headers needed at load-time.
 *   - Events emitted via BPF_MAP_TYPE_RINGBUF (preferred over perf_event
 *     array since 5.8; lower overhead, no per-CPU loss on overflow).
 *   - Policy stored in BPF_MAP_TYPE_HASH keyed by {inode,dev}; userspace
 *     populates at startup and hot-reloads without program reload.
 *   - LSM hooks return 0 (allow) or negative errno (deny).
 *
 * Kernel requirements:
 *   CONFIG_BPF_LSM=y
 *   CONFIG_LSM="...,bpf"          (bpf must be in lsm= boot param or Kconfig)
 *   CONFIG_DEBUG_INFO_BTF=y       (for CO-RE / BTF)
 *   Linux ≥ 5.7 (BPF LSM landed in 5.7)
 *
 * References:
 *   Documentation/bpf/bpf_lsm.rst
 *   kernel/bpf/bpf_lsm.c
 *   include/linux/lsm_hooks.h
 *   samples/bpf/
 *   tools/lib/bpf/bpf_helpers.h
 */

/* vmlinux.h: single-header BTF-derived kernel type definitions.
 * Generated with: bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
 * Do NOT include individual kernel headers alongside it — they conflict. */
#include "vmlinux.h"

#include <bpf/bpf_helpers.h>       /* SEC, BPF_PROG, bpf_map_* helpers  */
#include <bpf/bpf_tracing.h>       /* BPF_PROG() macro for LSM/fentry    */
#include <bpf/bpf_core_read.h>     /* BPF_CORE_READ, BPF_CORE_READ_STR  */
#include "security_monitor.h"

/* ------------------------------------------------------------------ */
/* License — required; GPL allows use of GPL-only BPF helpers          */
/* ------------------------------------------------------------------ */
char LICENSE[] SEC("license") = "GPL";

/* ------------------------------------------------------------------ */
/* Maps                                                                 */
/* ------------------------------------------------------------------ */

/*
 * events: kernel→userspace ringbuf.
 * max_entries = total byte capacity; must be power-of-2 and PAGE_SIZE multiple.
 * 1<<18 = 256 KiB; tune based on event rate × sizeof(lsm_event).
 */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 18);   /* 256 KiB */
} events SEC(".maps");

/*
 * blocked_files: policy map keyed by {inode,dev}.
 * Userspace inserts entries; BPF side is read-only.
 * Value = POLICY_DENY or POLICY_AUDIT.
 */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key,   struct policy_key);
    __type(value, __u8);
} blocked_files SEC(".maps");

/*
 * blocked_uids: deny exec for specific UIDs (e.g., untrusted service accounts).
 * Key = uid, value = POLICY_DENY.
 */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key,   __u32);
    __type(value, __u8);
} blocked_uids SEC(".maps");

/*
 * stats: per-CPU atomic counters for hook invocations and denials.
 * Avoids ringbuf overhead for high-frequency metrics.
 */
struct hook_stats {
    __u64 total;
    __u64 denied;
};

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 4);    /* one slot per hook type enum value */
    __type(key,   __u32);
    __type(value, struct hook_stats);
} stats SEC(".maps");

/* ------------------------------------------------------------------ */
/* Internal helpers                                                     */
/* ------------------------------------------------------------------ */

/*
 * emit_event — reserve a ringbuf slot, populate, and submit.
 * Returns 0 on success, -1 if ringbuf full (event dropped).
 *
 * NOTE: bpf_ringbuf_reserve() may return NULL if ring is full.
 * The verifier requires a NULL-check before any write through the pointer.
 */
static __always_inline int
emit_event(__u32 type, __u32 inode, __u32 dev, int denied)
{
    struct lsm_event *e;
    __u64 uid_gid;
    __u64 pid_tgid;

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return -1;   /* ringbuf full — event dropped, stats still updated */

    pid_tgid = bpf_get_current_pid_tgid();
    uid_gid  = bpf_get_current_uid_gid();

    e->timestamp_ns = bpf_ktime_get_ns();
    e->event_type   = type;
    e->pid          = (__u32)(pid_tgid >> 32);
    e->tid          = (__u32)(pid_tgid & 0xFFFFFFFF);
    e->uid          = (__u32)(uid_gid  & 0xFFFFFFFF);
    e->gid          = (__u32)(uid_gid  >> 32);
    e->inode        = inode;
    e->dev          = dev;
    e->padding      = 0;

    bpf_get_current_comm(e->comm, sizeof(e->comm));

    /* path: best-effort; full dentry walk not available in LSM context */
    e->path[0] = '\0';

    bpf_ringbuf_submit(e, 0);
    return 0;
}

/*
 * update_stats — increment per-CPU stat counters.
 * key matches enum event_type slots (1-indexed, map has 4 entries 0-3).
 */
static __always_inline void
update_stats(__u32 hook_idx, int denied)
{
    struct hook_stats *s = bpf_map_lookup_elem(&stats, &hook_idx);
    if (s) {
        /* Per-CPU array: no lock needed, each CPU has its own copy */
        __sync_fetch_and_add(&s->total, 1);
        if (denied)
            __sync_fetch_and_add(&s->denied, 1);
    }
}

/* ------------------------------------------------------------------ */
/* LSM Hook 1: bprm_check_security — intercept execve()               */
/*                                                                      */
/* Called by the kernel after the binary is opened and before ELF      */
/* interpretation begins. Returning -EPERM aborts the exec.            */
/*                                                                      */
/* struct linux_binprm layout (CO-RE):                                 */
/*   bprm->file          = struct file *                                */
/*   bprm->file->f_inode = struct inode *                              */
/*   inode->i_ino        = unsigned long (inode number)                */
/*   inode->i_sb->s_dev  = dev_t (device)                              */
/* ------------------------------------------------------------------ */
SEC("lsm/bprm_check_security")
int BPF_PROG(bprm_check_security, struct linux_binprm *bprm)
{
    struct policy_key k = {};
    __u8 *action;
    __u32 uid;
    __u64 uid_gid;
    int deny = 0;

    /* Extract inode + device via CO-RE (handles kernel struct layout changes) */
    k.inode = (__u32)BPF_CORE_READ(bprm, file, f_inode, i_ino);
    k.dev   = (__u32)BPF_CORE_READ(bprm, file, f_inode, i_sb, s_dev);

    uid_gid = bpf_get_current_uid_gid();
    uid     = (__u32)(uid_gid & 0xFFFFFFFF);

    /* Check UID block list first */
    action = bpf_map_lookup_elem(&blocked_uids, &uid);
    if (action && *action == POLICY_DENY) {
        deny = 1;
        goto out;
    }

    /* Check file inode policy */
    action = bpf_map_lookup_elem(&blocked_files, &k);
    if (action && *action == POLICY_DENY)
        deny = 1;

out:
    update_stats(EVENT_EXEC_BLOCKED, deny);
    if (deny) {
        emit_event(EVENT_EXEC_BLOCKED, k.inode, k.dev, 1);
        return -EPERM;
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/* LSM Hook 2: file_open                                               */
/*                                                                      */
/* Called on every open(2)/openat(2). Heavier than exec hook;          */
/* keep the fast path short. Only emit ringbuf event if denied.        */
/*                                                                      */
/* Note: file->f_path.dentry is valid here (unlike some other hooks).  */
/* ------------------------------------------------------------------ */
SEC("lsm/file_open")
int BPF_PROG(file_open, struct file *file)
{
    struct policy_key k = {};
    __u8 *action;
    int deny = 0;

    k.inode = (__u32)BPF_CORE_READ(file, f_inode, i_ino);
    k.dev   = (__u32)BPF_CORE_READ(file, f_inode, i_sb, s_dev);

    action = bpf_map_lookup_elem(&blocked_files, &k);
    if (action) {
        if (*action == POLICY_DENY)
            deny = 1;
        /* POLICY_AUDIT: emit event but don't deny */
        emit_event(EVENT_FILE_OPEN_DENIED, k.inode, k.dev, deny);
    }

    update_stats(EVENT_FILE_OPEN_DENIED, deny);
    return deny ? -EACCES : 0;
}

/* ------------------------------------------------------------------ */
/* LSM Hook 3: ptrace_access_check                                     */
/*                                                                      */
/* Blocks ptrace of processes not owned by current UID unless root.    */
/* This prevents lateral credential theft in containerized envs.       */
/*                                                                      */
/* mode flags: PTRACE_MODE_READ, PTRACE_MODE_ATTACH (linux/ptrace.h)  */
/* ------------------------------------------------------------------ */
SEC("lsm/ptrace_access_check")
int BPF_PROG(ptrace_access_check, struct task_struct *child, unsigned int mode)
{
    __u32 current_uid, target_uid;
    __u64 uid_gid;
    int deny = 0;

    uid_gid    = bpf_get_current_uid_gid();
    current_uid = (__u32)(uid_gid & 0xFFFFFFFF);

    /* root (uid 0) always allowed at this hook level */
    if (current_uid == 0)
        return 0;

    target_uid = (__u32)BPF_CORE_READ(child, cred, uid.val);

    /*
     * Deny cross-uid ptrace. Same-uid attach still allowed for debuggers
     * on own processes (gdb, strace on own pid). For stricter policy,
     * also check mode & PTRACE_MODE_ATTACH and deny same-uid.
     */
    if (current_uid != target_uid) {
        deny = 1;
        emit_event(EVENT_PTRACE_BLOCKED,
                   (__u32)BPF_CORE_READ(child, pid), 0, 1);
    }

    update_stats(EVENT_PTRACE_BLOCKED, deny);
    return deny ? -EPERM : 0;
}
