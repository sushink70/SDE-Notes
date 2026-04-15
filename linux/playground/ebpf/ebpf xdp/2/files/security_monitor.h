#ifndef SECURITY_MONITOR_H
#define SECURITY_MONITOR_H

/*
 * security_monitor.h — shared ABI between BPF kernel-side and userspace loader.
 *
 * Design rules:
 *   - All types must be fixed-width (no pointer-width sensitivity across arches).
 *   - Enums backed by __u32 for stable wire format.
 *   - Padding explicit, no compiler-inserted gaps in ringbuf payloads.
 *   - This file is included by BOTH BPF C and userspace C (guarded sections).
 *
 * References:
 *   kernel/bpf/ringbuf.c
 *   include/uapi/linux/bpf.h
 *   Documentation/bpf/ringbuf.rst
 */

#include <linux/types.h>   /* __u8, __u32, __u64 — kernel-uapi portable */

/* ------------------------------------------------------------------ */
/* Event type identifiers                                               */
/* ------------------------------------------------------------------ */
enum event_type {
    EVENT_EXEC_BLOCKED      = 1,  /* bprm_check_security denied exec   */
    EVENT_FILE_OPEN_DENIED  = 2,  /* file_open LSM hook denied          */
    EVENT_SOCKET_BLOCKED    = 3,  /* socket_connect LSM hook denied     */
    EVENT_PTRACE_BLOCKED    = 4,  /* ptrace_access_check denied         */
};

/* ------------------------------------------------------------------ */
/* Ringbuf event payload                                                */
/*                                                                      */
/* Kept ≤ 256 bytes so a single cache line pair holds most events.     */
/* ------------------------------------------------------------------ */
#define TASK_COMM_LEN   16
#define PATH_LEN        128

struct lsm_event {
    __u64  timestamp_ns;              /* bpf_ktime_get_ns() at hook entry   */
    __u32  event_type;                /* enum event_type                    */
    __u32  pid;                       /* tgid (process id, userspace sense) */
    __u32  tid;                       /* tid  (thread id)                   */
    __u32  uid;                       /* effective uid                      */
    __u32  gid;                       /* effective gid                      */
    __u32  inode;                     /* inode number of target file        */
    __u32  dev;                       /* device of target file              */
    __u32  padding;                   /* explicit: align to 8 bytes         */
    char   comm[TASK_COMM_LEN];       /* task command name                  */
    char   path[PATH_LEN];            /* best-effort path (may be partial)  */
};

/* ------------------------------------------------------------------ */
/* Policy key used in blocked_inodes / blocked_uids maps               */
/* ------------------------------------------------------------------ */
struct policy_key {
    __u32  inode;
    __u32  dev;
};

/* Policy action values */
#define POLICY_DENY     1
#define POLICY_AUDIT    2   /* log but allow */

/* ------------------------------------------------------------------ */
/* Userspace-only helpers (not compiled into BPF object)               */
/* ------------------------------------------------------------------ */
#ifndef __BPF_TRACING__
#include <stdint.h>
#include <time.h>

static inline const char *event_type_str(uint32_t t)
{
    switch (t) {
    case EVENT_EXEC_BLOCKED:     return "EXEC_BLOCKED";
    case EVENT_FILE_OPEN_DENIED: return "FILE_OPEN_DENIED";
    case EVENT_SOCKET_BLOCKED:   return "SOCKET_BLOCKED";
    case EVENT_PTRACE_BLOCKED:   return "PTRACE_BLOCKED";
    default:                     return "UNKNOWN";
    }
}
#endif /* !__BPF_TRACING__ */

#endif /* SECURITY_MONITOR_H */
