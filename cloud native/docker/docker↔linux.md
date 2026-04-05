# Docker ↔ Linux: Complete Kernel-Level Internals Guide

> **Kernel version context:** Linux v6.8+ (mainline), Docker Engine v26+, containerd v1.7+, runc v1.1+
> **Target audience:** Kernel developers, systems programmers, low-level container internals

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Linux Namespaces — Isolation Primitives](#2-linux-namespaces--isolation-primitives)
3. [Control Groups (cgroups v1 & v2)](#3-control-groups-cgroups-v1--v2)
4. [Union Filesystems — OverlayFS Deep Dive](#4-union-filesystems--overlayfs-deep-dive)
5. [Container Runtime Stack — dockerd → containerd → runc](#5-container-runtime-stack--dockerd--containerd--runc)
6. [Linux Capabilities & Privilege Model](#6-linux-capabilities--privilege-model)
7. [Seccomp BPF — Syscall Filtering](#7-seccomp-bpf--syscall-filtering)
8. [LSM Integration — AppArmor & SELinux](#8-lsm-integration--apparmor--selinux)
9. [Networking Internals — veth, bridge, netfilter, iptables](#9-networking-internals--veth-bridge-netfilter-iptables)
10. [Container Networking Deep Dive — XDP, eBPF, tc](#10-container-networking-deep-dive--xdp-ebpf-tc)
11. [Process Lifecycle — clone(2), execve(2), wait(2)](#11-process-lifecycle--clone2-execve2-wait2)
12. [Signal Handling & PID 1 Problem](#12-signal-handling--pid-1-problem)
13. [Device Access — /dev, devtmpfs, device cgroups](#13-device-access--dev-devtmpfs-device-cgroups)
14. [Memory Management — OOM, hugepages, memory limits](#14-memory-management--oom-hugepages-memory-limits)
15. [Copy-on-Write & Page Cache Interaction](#15-copy-on-write--page-cache-interaction)
16. [Go Implementation — containerd & Docker Engine](#16-go-implementation--containerd--docker-engine)
17. [C Implementation — runc & libcontainer](#17-c-implementation--runc--libcontainer)
18. [Rust Implementation — youki container runtime](#18-rust-implementation--youki-container-runtime)
19. [eBPF for Container Observability](#19-ebpf-for-container-observability)
20. [Kernel Tracing — ftrace, perf for container debugging](#20-kernel-tracing--ftrace-perf-for-container-debugging)
21. [rootless Containers — user namespaces deep dive](#21-rootless-containers--user-namespaces-deep-dive)
22. [OCI Runtime Specification & Kernel Interface](#22-oci-runtime-specification--kernel-interface)

---

## 1. Architecture Overview

```
+---------------------------------------------------------------+
|                    USER SPACE                                 |
|                                                               |
|  docker CLI          docker-compose          BuildKit         |
|      |                    |                      |            |
|      v                    v                      v            |
|  +--------------------------------------------------+         |
|  |           dockerd (Docker Engine Daemon)         |         |
|  |   REST API / gRPC   image mgmt  volume mgmt      |         |
|  +------------------+-------------------------------+         |
|                     |  gRPC (containerd API)                  |
|                     v                                         |
|  +--------------------------------------------------+         |
|  |           containerd (High-level runtime)        |         |
|  |  snapshotter  content-store  events  task-api    |         |
|  +------------------+-------------------------------+         |
|                     |  execve + pipe (OCI bundle)             |
|                     v                                         |
|  +--------------------------------------------------+         |
|  |         runc / crun / youki (OCI runtime)        |         |
|  |  libcontainer   namespace setup   cgroup config  |         |
|  +------------------+-------------------------------+         |
|                     |                                         |
+---------------------|------------------------------------------+
                       | SYSCALL BOUNDARY
+---------------------|------------------------------------------+
|                    KERNEL SPACE                               |
|                     |                                         |
|   +----------------------------------------------------------+|
|   |            clone(2) / unshare(2) / setns(2)             ||
|   +----------------------------------------------------------+|
|          |             |             |           |            |
|          v             v             v           v            |
|   +-----------+ +----------+ +-----------+ +----------+      |
|   | NAMESPACES| | CGROUPS  | | OVERLAYFS | |NETFILTER |      |
|   | pid,net   | | memory   | | layer     | |iptables  |      |
|   | mnt,uts   | | cpu,io   | | mgmt      | |nftables  |      |
|   | ipc,user  | | cgroup v2| |           | |XDP       |      |
|   | time      | |          | |           | |          |      |
|   +-----------+ +----------+ +-----------+ +----------+      |
|          |             |             |           |            |
|          v             v             v           v            |
|   +----------------------------------------------------------+|
|   |        VFS / Page Cache / Block Layer / Net Stack       ||
|   +----------------------------------------------------------+|
|   |              Hardware Abstraction Layer                  ||
|   +----------------------------------------------------------+|
+---------------------------------------------------------------+
```

**Key kernel source trees:**

| Component | Kernel Source Path |
|---|---|
| Namespaces | `kernel/nsproxy.c`, `include/linux/nsproxy.h` |
| PID namespace | `kernel/pid_namespace.c` |
| Network namespace | `net/core/net_namespace.c` |
| Mount namespace | `fs/namespace.c` |
| cgroups v2 | `kernel/cgroup/cgroup.c` |
| OverlayFS | `fs/overlayfs/` |
| seccomp | `kernel/seccomp.c` |
| capabilities | `kernel/capability.c` |
| veth driver | `drivers/net/veth.c` |
| bridge | `net/bridge/br_main.c` |

---

## 2. Linux Namespaces — Isolation Primitives

Namespaces are the **core isolation mechanism** in Linux that Docker builds on. Each namespace type wraps a specific global resource and presents a private view to processes within it.

```
task_struct (include/linux/sched.h)
+---------------------------------------+
|  pid_t pid                            |
|  pid_t tgid                           |
|  struct nsproxy *nsproxy  ----------->+
|  struct cred    *cred                 |   nsproxy (include/linux/nsproxy.h)
|  ...                                  |   +-------------------------------+
+---------------------------------------+   |  struct uts_namespace  *uts_ns |
                                            |  struct ipc_namespace  *ipc_ns |
                                            |  struct mnt_namespace  *mnt_ns |
                                            |  struct pid_namespace  *pid_ns |
                                            |  struct net            *net_ns |
                                            |  struct time_namespace *time_ns|
                                            |  struct cgroup_namespace *cgns |
                                            +-------------------------------+
```

### Namespace Types and Clone Flags

| Namespace | Flag | Isolates | Kernel File |
|---|---|---|---|
| Mount | `CLONE_NEWNS` | Filesystem mount points | `fs/namespace.c` |
| UTS | `CLONE_NEWUTS` | Hostname, NIS domain | `kernel/utsname.c` |
| IPC | `CLONE_NEWIPC` | SysV IPC, POSIX MQ | `ipc/namespace.c` |
| PID | `CLONE_NEWPID` | Process IDs | `kernel/pid_namespace.c` |
| Network | `CLONE_NEWNET` | Net devices, IPs, routing | `net/core/net_namespace.c` |
| User | `CLONE_NEWUSER` | UID/GID mappings | `kernel/user_namespace.c` |
| Cgroup | `CLONE_NEWCGROUP` | cgroup root | `kernel/cgroup/namespace.c` |
| Time | `CLONE_NEWTIME` | Boot/monotonic clocks | `kernel/time/namespace.c` |

### Kernel Data Structures

```c
// include/linux/nsproxy.h
struct nsproxy {
    atomic_t count;
    struct uts_namespace  *uts_ns;
    struct ipc_namespace  *ipc_ns;
    struct mnt_namespace  *mnt_ns;
    struct pid_namespace  *pid_ns_for_children;
    struct net            *net_ns;
    struct time_namespace *time_ns;
    struct time_namespace *time_ns_for_children;
    struct cgroup_namespace *cgroup_ns;
};

// kernel/nsproxy.c — copy_namespaces() called from copy_process()
int copy_namespaces(unsigned long flags, struct task_struct *tsk)
{
    struct nsproxy *old_ns = tsk->nsproxy;
    struct user_namespace *user_ns = task_cred_xxx(tsk, user_ns);
    struct nsproxy *new_ns;

    if (likely(!(flags & (CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC |
                          CLONE_NEWPID | CLONE_NEWNET |
                          CLONE_NEWCGROUP | CLONE_NEWTIME)))) {
        get_nsproxy(old_ns);
        return 0;
    }
    // ...
    new_ns = create_new_namespaces(flags, tsk, user_ns, tsk->fs);
    // ...
}
```

### syscall path: clone(2) with namespace flags

```c
// kernel/fork.c — kernel_clone()
pid_t kernel_clone(struct kernel_clone_args *args)
{
    struct task_struct *p;
    // ...
    p = copy_process(NULL, 0, NUMA_NO_NODE, args);
    // copy_process() calls:
    //   copy_namespaces(clone_flags, p)  -> namespace isolation
    //   copy_creds(p, clone_flags)       -> capability/user setup
    //   copy_mm(clone_flags, p)          -> address space
    //   copy_files(clone_flags, p)       -> file descriptors
    //   copy_signal(clone_flags, p)      -> signal handlers
    // ...
}

// Syscall entry point
SYSCALL_DEFINE5(clone, unsigned long, clone_flags,
    unsigned long, newsp, int __user *, parent_tidptr,
    unsigned long, tls, int __user *, child_tidptr)
{
    struct kernel_clone_args args = {
        .flags      = (lower_32_bits(clone_flags) & ~CSIGNAL),
        .pidfd      = parent_tidptr,
        .child_tid  = child_tidptr,
        .parent_tid = parent_tidptr,
        .exit_signal = (lower_32_bits(clone_flags) & CSIGNAL),
        .stack      = newsp,
        .tls        = tls,
    };
    return kernel_clone(&args);
}
```

### PID Namespace Deep Dive

```
Host PID namespace
  pid=1  (systemd)
  pid=234 (dockerd)
  pid=891 (containerd)
  pid=1024 (runc)
     |
     | CLONE_NEWPID
     v
  Container PID namespace
    pid=1  (container init / entrypoint)  <-- appears as pid=1 inside
    pid=2  (worker process)
    pid=3  (another process)
    
    (host sees these as pid=1025, 1026, 1027)
```

```c
// kernel/pid_namespace.c
struct pid_namespace {
    struct idr        idr;           // pid -> struct pid mapping
    struct rcu_head   rcu;
    unsigned int      level;         // nesting level (host=0)
    struct pid_namespace *parent;    // parent ns
    struct user_namespace *user_ns;
    struct ucounts   *ucounts;
    struct work_struct proc_work;
    kgid_t            pid_gid;
    int               hide_pid;      // /proc/sys/kernel/ns_last_pid
    int               reboot;
    struct ns_common  ns;
    struct bpf_prog   *bacct_prog;
} __randomize_layout;
```

```c
// Reading /proc/PID/ns/pid — each ns has a unique inode
// fs/proc/namespaces.c
static const struct proc_ns_operations pidns_for_children_operations = {
    .name        = "pid_for_children",
    .real_ns_name = "pid",
    .type        = CLONE_NEWPID,
    .get         = pidns_get,
    .put         = pidns_put,
    .install     = pidns_install,
    .owner       = pidns_owner,
    .get_parent  = pidns_get_parent,
};
```

### Network Namespace Internals

```c
// include/net/net_namespace.h
struct net {
    // refcounting
    refcount_t          passive;
    spinlock_t          rules_mod_lock;
    
    // core network structures
    struct list_head    list;         // list of all net namespaces
    struct list_head    exit_list;
    struct llist_node   cleanup_list;
    
    struct user_namespace *user_ns;
    struct ucounts       *ucounts;
    
    struct idr           netns_ids;
    struct ns_common     ns;
    
    struct ref_tracker_dir refcnt_tracker;
    
    struct list_head    dev_base_head;  // all net_devices in this ns
    struct hlist_head   *dev_name_head;
    struct hlist_head   *dev_index_head;
    
    // loopback device
    struct net_device   *loopback_dev;
    
    // routing tables, ARP, neighbor tables
    struct netns_ipv4   ipv4;
    struct netns_ipv6   ipv6;
    struct netns_nf     nf;           // netfilter hooks per namespace
    struct netns_xt     xt;           // xtables
    struct netns_ct     ct;           // conntrack
    
    // socket infrastructure
    struct sock         *rtnl;        // rtnetlink socket
    struct sock         *genl_sock;
    
    // ...hundreds more fields
};
```

### C: Creating a Network Namespace Manually

```c
// Demonstrates what runc does when setting up container networking
// compile: gcc -o ns_demo ns_demo.c

#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>

#define STACK_SIZE (1024 * 1024)

static char child_stack[STACK_SIZE];

static int child_fn(void *arg)
{
    // Inside new namespaces
    printf("[child] PID: %d\n", getpid());   // will print 1
    printf("[child] hostname: ");
    fflush(stdout);
    
    // Set hostname in new UTS namespace
    if (sethostname("container", 9) < 0) {
        perror("sethostname");
        return 1;
    }
    system("hostname");
    
    // Mount new procfs for this PID namespace
    if (mount("proc", "/proc", "proc",
              MS_NOEXEC | MS_NOSUID | MS_NODEV, NULL) < 0) {
        perror("mount proc");
        return 1;
    }
    
    // Show network interfaces (only loopback in new net ns)
    system("ip link show");
    
    execl("/bin/sh", "sh", NULL);
    return 0;
}

int main(void)
{
    pid_t child;
    int flags = CLONE_NEWPID |   // new PID namespace
                CLONE_NEWUTS |   // new hostname
                CLONE_NEWNET |   // new network stack
                CLONE_NEWNS  |   // new mount namespace
                CLONE_NEWIPC |   // new IPC namespace
                SIGCHLD;

    printf("[parent] Creating namespaces with flags=0x%x\n", flags);

    child = clone(child_fn, child_stack + STACK_SIZE, flags, NULL);
    if (child < 0) {
        perror("clone");
        return 1;
    }

    printf("[parent] Child PID (host view): %d\n", child);
    
    // Inspect child's namespace links
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/ns/pid", child);
    printf("[parent] Child PID ns: %s\n", path);

    waitpid(child, NULL, 0);
    return 0;
}
```

### Shell: Inspecting Namespace of a Running Container

```bash
#!/bin/bash
# Get the PID of the first process in a container
CONTAINER_ID="$1"
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' "$CONTAINER_ID")

echo "=== Container: $CONTAINER_ID (host PID: $CONTAINER_PID) ==="

echo "--- Namespaces ---"
ls -la /proc/$CONTAINER_PID/ns/

echo ""
echo "--- Namespace inodes (compare with host) ---"
for ns in cgroup ipc mnt net pid time user uts; do
    host_ns=$(readlink /proc/1/ns/$ns 2>/dev/null)
    cont_ns=$(readlink /proc/$CONTAINER_PID/ns/$ns 2>/dev/null)
    if [ "$host_ns" = "$cont_ns" ]; then
        echo "  $ns: SHARED ($cont_ns)"
    else
        echo "  $ns: ISOLATED (container=$cont_ns, host=$host_ns)"
    fi
done

echo ""
echo "--- Enter network namespace ---"
echo "Run: sudo nsenter -t $CONTAINER_PID -n ip addr"
```

---

## 3. Control Groups (cgroups v1 & v2)

cgroups provide **resource accounting and limiting**. Docker uses them to enforce CPU, memory, I/O, and network constraints.

```
cgroup v2 unified hierarchy (since Linux 4.5, default in most distros)

/sys/fs/cgroup/                          <- cgroup root (host)
  ├── memory.max                         <- unlimited (host root)
  ├── cpu.max                            <- "max 100000"
  ├── system.slice/
  │   ├── docker.service/
  │   │   └── (dockerd cgroup)
  │   └── containerd.service/
  │       └── (containerd cgroup)
  └── system.slice/docker-<id>.scope/    <- per-container cgroup
      ├── memory.max                     <- e.g. "524288000\n" (500MB)
      ├── memory.current                 <- current usage
      ├── memory.pressure                <- PSI metrics
      ├── cpu.max                        <- "50000 100000" = 50% CPU
      ├── cpu.weight                     <- CPU shares (v2 equivalent)
      ├── io.max                         <- block device I/O limits
      ├── pids.max                       <- max processes
      └── cgroup.procs                   <- PIDs in this cgroup
```

### Kernel cgroup v2 Structures

```c
// kernel/cgroup/cgroup.c
// include/linux/cgroup-defs.h

struct cgroup {
    struct cgroup_subsys_state self;
    unsigned long flags;
    int level;               // depth in hierarchy
    int max_depth;
    int nr_descendants;
    int nr_dying_descendants;
    int64_t ancestor_ids[];  // fast ancestor lookup
    
    struct kernfs_node *kn;  // backing kernfs node
    struct cgroup_file procs_file;   // cgroup.procs
    struct cgroup_file events_file;  // cgroup.events
    
    u16 subtree_control;    // enabled controllers bitmask
    u16 subtree_ss_mask;    // subsystem mask
    
    struct list_head cset_links;  // css_set links
    struct list_head e_csets[CGROUP_SUBSYS_COUNT];
    
    struct cgroup *dom_cgroup;   // domain for legacy behavior
};

// Per-task cgroup state (embedded in task_struct)
struct css_set {
    struct cgroup_subsys_state *subsys[CGROUP_SUBSYS_COUNT];
    refcount_t refcount;
    struct css_set *dom_cset;
    struct cgroup *dfl_cgrp;
    int nr_tasks;
    struct list_head tasks;   // list of tasks using this css_set
    struct list_head mg_tasks;
    struct list_head dying_tasks;
    struct list_head task_iters;
    struct list_head e_cset_node[CGROUP_SUBSYS_COUNT];
    struct list_head threaded_csets;
    struct list_head threaded_csets_node;
    struct hlist_node hlist;
    struct list_head cgrp_links;
    struct list_head mg_src_preload_node;
    struct list_head mg_dst_preload_node;
    struct list_head mg_node;
    struct cgroup *mg_src_cgrp;
    struct cgroup *mg_dst_cgrp;
    struct css_set *mg_dst_cset;
    bool dead;
    struct rcu_head rcu_head;
};
```

### Memory Controller

```c
// mm/memcontrol.c
// include/linux/memcontrol.h

struct mem_cgroup {
    struct cgroup_subsys_state css;  // must be first!
    
    struct mem_cgroup_id id;
    
    // per-node page caches and swap
    struct mem_cgroup_per_node __percpu *nodeinfo;
    
    // OOM configuration
    bool            oom_group;
    bool            oom_lock;
    int             under_oom;
    int             swappiness;
    
    // limits
    struct page_counter memory;    // memory.max
    struct page_counter swap;      // memory.swap.max
    struct page_counter memsw;     // memory+swap combined
    struct page_counter kmem;      // kernel memory (v1 only)
    struct page_counter tcpmem;    // tcp memory
    
    // thresholds for events
    struct mem_cgroup_thresholds thresholds;
    struct mem_cgroup_thresholds memsw_thresholds;
    
    // per-cpu stats
    struct memcg_vmstats __percpu *vmstats_percpu;
    struct memcg_vmstats *vmstats;
    
    // OOM killer selection
    struct list_head        oom_notify;
    unsigned long           move_charge_at_immigrate;
    spinlock_t              move_lock;
    unsigned long           move_lock_flags;
    
    // PSI (pressure stall info)
    struct psi_group psi;
};

// charge a page to a cgroup — called from mm/page_alloc.c
int mem_cgroup_charge(struct folio *folio, struct mm_struct *mm, gfp_t gfp)
{
    struct mem_cgroup *memcg;
    // ... lookup memcg from mm->memcg
    // ... call try_charge() which enforces memory.max
    // ... if over limit -> invoke reclaim or OOM
}
```

### CPU Controller (v2 — Bandwidth + Weight)

```c
// kernel/sched/ext.c, kernel/sched/fair.c
// CPU bandwidth limiting: cpu.max = "quota period" (microseconds)
// Docker --cpus=0.5 -> writes "50000 100000" to cpu.max

// kernel/cgroup/cpuset.c for cpuset (CPU affinity)
// cpu.weight = 100 default, proportional fair share
```

### C: Reading cgroup v2 Stats Programmatically

```c
// Read container memory usage from cgroupv2 — what docker stats does
// gcc -o cgroup_stats cgroup_stats.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>
#include <errno.h>

#define CGROUP_ROOT "/sys/fs/cgroup"
#define BUF_SIZE    4096

static long read_cgroup_value(const char *cgroup_path, const char *file)
{
    char full_path[512];
    char buf[64];
    int fd;
    long val;

    snprintf(full_path, sizeof(full_path), "%s/%s", cgroup_path, file);
    fd = open(full_path, O_RDONLY);
    if (fd < 0) return -1;

    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) return -1;
    buf[n] = '\0';

    if (strcmp(buf, "max\n") == 0) return LONG_MAX;
    val = strtol(buf, NULL, 10);
    return val;
}

static void print_container_cgroup_stats(const char *container_id)
{
    // Find cgroup by container ID prefix
    char pattern[128];
    char cgroup_path[512];
    DIR *dir;
    struct dirent *ent;
    
    // Docker places containers under:
    // /sys/fs/cgroup/system.slice/docker-<full-id>.scope
    // or /sys/fs/cgroup/docker/<full-id>  (depends on cgroup driver)
    snprintf(pattern, sizeof(pattern), "docker-%s", container_id);
    
    dir = opendir(CGROUP_ROOT "/system.slice");
    if (!dir) {
        perror("opendir");
        return;
    }

    while ((ent = readdir(dir)) != NULL) {
        if (strncmp(ent->d_name, pattern, strlen(pattern)) == 0) {
            snprintf(cgroup_path, sizeof(cgroup_path),
                     "%s/system.slice/%s", CGROUP_ROOT, ent->d_name);
            break;
        }
    }
    closedir(dir);

    if (!cgroup_path[0]) {
        fprintf(stderr, "cgroup not found for container %s\n", container_id);
        return;
    }

    printf("=== cgroup v2 stats for %s ===\n", cgroup_path);
    
    long mem_current = read_cgroup_value(cgroup_path, "memory.current");
    long mem_max     = read_cgroup_value(cgroup_path, "memory.max");
    long pids_current = read_cgroup_value(cgroup_path, "pids.current");
    long pids_max    = read_cgroup_value(cgroup_path, "pids.max");

    printf("memory.current: %ld bytes (%.2f MB)\n", 
           mem_current, mem_current / 1048576.0);
    if (mem_max == LONG_MAX)
        printf("memory.max:     unlimited\n");
    else
        printf("memory.max:     %ld bytes (%.2f MB)\n",
               mem_max, mem_max / 1048576.0);
    printf("pids.current:   %ld\n", pids_current);
    printf("pids.max:       %ld\n", pids_max);

    // Read detailed memory stats
    char stat_path[512];
    snprintf(stat_path, sizeof(stat_path), "%s/memory.stat", cgroup_path);
    FILE *f = fopen(stat_path, "r");
    if (f) {
        char line[128];
        printf("\n--- memory.stat (selected) ---\n");
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "anon ", 5) == 0   ||
                strncmp(line, "file ", 5) == 0   ||
                strncmp(line, "slab ", 5) == 0   ||
                strncmp(line, "pgfault ", 8) == 0)
                printf("  %s", line);
        }
        fclose(f);
    }
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <container-id-prefix>\n", argv[0]);
        return 1;
    }
    print_container_cgroup_stats(argv[1]);
    return 0;
}
```

### Shell: Applying cgroup Limits (what Docker does)

```bash
#!/bin/bash
# Mirrors what runc/libcontainer does when applying cgroup constraints
# for: docker run --memory=512m --cpus=0.5 --pids-limit=100

CGROUP_SCOPE="system.slice/docker-test.scope"
CGROUP_PATH="/sys/fs/cgroup/$CGROUP_SCOPE"

# Create cgroup scope (systemd transient unit does this via D-Bus)
mkdir -p "$CGROUP_PATH"

# Enable controllers in parent
echo "+memory +cpu +pids +io" > /sys/fs/cgroup/system.slice/cgroup.subtree_control

# Memory limit: 512 MiB
echo $((512 * 1024 * 1024)) > "$CGROUP_PATH/memory.max"

# CPU bandwidth: 50% = 50ms per 100ms period
echo "50000 100000" > "$CGROUP_PATH/cpu.max"

# PID limit
echo "100" > "$CGROUP_PATH/pids.max"

# Block I/O limit (device 8:0 = /dev/sda)
# Format: "MAJ:MIN rbps=N wbps=N riops=N wiops=N"
echo "8:0 wbps=10485760" > "$CGROUP_PATH/io.max"  # 10MB/s write

# Add process to cgroup
echo $$ > "$CGROUP_PATH/cgroup.procs"

echo "Cgroup configured: $CGROUP_PATH"
cat "$CGROUP_PATH/memory.max"
cat "$CGROUP_PATH/cpu.max"

# Now exec the container init
exec "$@"
```

---

## 4. Union Filesystems — OverlayFS Deep Dive

Docker uses **OverlayFS** (since kernel 3.18, production-ready ~4.0) as its default storage driver. OverlayFS stacks a read-write "upper" layer on top of read-only "lower" layers.

```
Container view (merged)
+-------------------------------+
|  /etc/hostname  (upper: RW)   |  <-- modified file in container
|  /bin/sh        (lower: RO)   |  <-- from base image
|  /lib/libc.so   (lower: RO)   |  <-- from base image
|  /app/main      (upper: RW)   |  <-- new file created in container
+-------------------------------+
        |          |
        v          v
+----------+  +------------------+
|  upper   |  |   lower layers   |
|  (RW)    |  |  layer N (RO)    |
| workdir  |  |  layer N-1 (RO)  |
|          |  |  ...             |
|          |  |  layer 0 (RO)    |
+----------+  +------------------+

/var/lib/docker/overlay2/
  <layer-id>/
    diff/        <- actual file content
    link         <- short ID symlink
    lower        <- colon-separated list of lower layer IDs
    merged/      <- mount point (only when container running)
    work/        <- OverlayFS work directory (opaque operations)
```

### OverlayFS VFS Internals

```c
// fs/overlayfs/super.c  — overlay_fill_super()
// fs/overlayfs/inode.c  — inode operations
// fs/overlayfs/dir.c    — directory operations
// fs/overlayfs/file.c   — file operations
// fs/overlayfs/copy_up.c — CoW on first write

// Core OverlayFS private inode data
// fs/overlayfs/ovl_entry.h
struct ovl_inode {
    union {
        struct ovl_dir_cache *cache;    // dir cache
        const char           *lowerdata_redirect;
    };
    const char          *redirect;      // path redirect
    u64                  version;       // for directory version
    unsigned long        flags;
    struct inode         vfs_inode;     // embedded VFS inode
    struct dentry       *__upperdentry; // upper layer dentry
    struct ovl_entry    *oe;            // lower layer stack
    struct mutex         lock;
};

// ovl_entry: represents a stack of lower inodes
struct ovl_entry {
    unsigned int    __numlower;
    struct ovl_path lowerstack[];  // array of (layer, dentry) pairs
};

// Copy-up: triggered on first write to lower-layer file
// fs/overlayfs/copy_up.c
int ovl_copy_up(struct dentry *dentry)
{
    // 1. Create file in upper layer
    // 2. Copy data from lower to upper using vfs_copy_file_range()
    // 3. Copy metadata (owner, mode, timestamps, xattrs)
    // 4. Atomically rename to final upper path
    // 5. Update inode to point to upper
}
```

### OverlayFS Mount — what Docker does

```bash
# Docker's overlay2 driver mount call (simplified)
# equivalent to:
mount -t overlay overlay \
  -o lowerdir=/var/lib/docker/overlay2/abc123/diff:\
              /var/lib/docker/overlay2/def456/diff:\
              /var/lib/docker/overlay2/base/diff,\
     upperdir=/var/lib/docker/overlay2/container-rw/diff,\
     workdir=/var/lib/docker/overlay2/container-rw/work \
  /var/lib/docker/overlay2/container-rw/merged
```

```c
// The kernel receives this as a mount(2) syscall:
// fs/namespace.c -> do_mount() -> do_new_mount() -> vfs_get_tree()
//   -> overlay_get_tree() -> ovl_fill_super()

// OverlayFS superblock private data
// fs/overlayfs/super.c
struct ovl_fs {
    struct ovl_layer       upper_layer;
    struct ovl_layer       *lower_layers;
    unsigned int           numlower;
    unsigned int           numlowerfs;
    
    // OverlayFS behavior flags
    struct ovl_config      config;
    
    // VFS superblock for each layer
    struct vfsmount        *upper_mnt;
    
    // NFS export support
    struct ovl_inode_cache *inode_cache;
    
    // Various UUID for detection
    bool                   same_sb;    // same underlying superblock
    bool                   upper_disconnected;
};
```

### Whiteout Files

When a file from a lower layer is deleted in a container, OverlayFS creates a **whiteout** — a character device (0,0) in the upper layer:

```c
// fs/overlayfs/dir.c — ovl_unlink()
static int ovl_unlink(struct inode *dir, struct dentry *dentry)
{
    // if file is in lower layer:
    //   create whiteout in upper: mknod(path, S_IFCHR, 0) + set "overlay.opaque" xattr
    // if file is in upper layer:
    //   just unlink from upper
}
```

```bash
# Inspect Docker image layers
docker image inspect ubuntu:22.04 | jq '.[0].GraphDriver'

# See actual OverlayFS layers
ls /var/lib/docker/overlay2/

# Check a specific layer's diff
ls /var/lib/docker/overlay2/<layer-id>/diff/

# See a running container's OverlayFS mounts
mount | grep overlay
cat /proc/mounts | grep overlay

# Inspect copy-up in action with inotifywait
strace -e trace=openat,write docker run -it ubuntu bash
```

---

## 5. Container Runtime Stack — dockerd → containerd → runc

```
docker run ubuntu bash
    |
    | HTTP/Unix socket: POST /containers/create
    | (unix:///var/run/docker.sock)
    v
dockerd (moby/moby)
    |
    | gRPC: containerd.services.containers.v1.Containers/Create
    |       containerd.services.tasks.v1.Tasks/Create
    | (unix:///run/containerd/containerd.sock)
    v
containerd (containerd/containerd)
    |
    | Creates OCI bundle:
    |   /run/containerd/io.containerd.runtime.v2.task/
    |       default/<container-id>/
    |           config.json    (OCI spec)
    |           rootfs/        (bind-mounted from overlayfs)
    |
    | Spawns: containerd-shim-runc-v2
    v
containerd-shim-runc-v2
    |
    | execve("/usr/bin/runc", ["runc", "create", ...])
    v
runc (opencontainers/runc)
    |
    | 1. Parse config.json (OCI spec)
    | 2. Create namespaces via clone(2)
    | 3. Setup cgroups (write to /sys/fs/cgroup)
    | 4. Apply seccomp filter (prctl PR_SET_SECCOMP)
    | 5. Drop capabilities (capset)
    | 6. chroot/pivot_root into rootfs
    | 7. exec container process (execve)
    v
container process (bash)
```

### OCI Runtime Spec (config.json)

```json
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": true,
    "user": { "uid": 0, "gid": 0 },
    "args": ["/bin/bash"],
    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
    "cwd": "/",
    "capabilities": {
      "bounding":  ["CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_FSETID", "CAP_FOWNER",
                    "CAP_MKNOD", "CAP_NET_RAW", "CAP_SETGID", "CAP_SETUID",
                    "CAP_SETFCAP", "CAP_SETPCAP", "CAP_NET_BIND_SERVICE",
                    "CAP_SYS_CHROOT", "CAP_KILL", "CAP_AUDIT_WRITE"],
      "permitted": [...],
      "effective": [...]
    },
    "rlimits": [{"type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024}],
    "noNewPrivileges": true
  },
  "root": { "path": "rootfs", "readonly": false },
  "mounts": [
    {"destination": "/proc",    "type": "proc",    "source": "proc"},
    {"destination": "/dev",     "type": "tmpfs",   "source": "tmpfs",
     "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]},
    {"destination": "/dev/pts", "type": "devpts",  "source": "devpts",
     "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620"]},
    {"destination": "/sys",     "type": "sysfs",   "source": "sysfs",
     "options": ["nosuid", "noexec", "nodev", "ro"]}
  ],
  "linux": {
    "namespaces": [
      {"type": "pid"},   {"type": "ipc"},  {"type": "uts"},
      {"type": "mount"}, {"type": "network"}
    ],
    "resources": {
      "memory": {"limit": 536870912},
      "cpu": {"quota": 50000, "period": 100000}
    },
    "seccomp": { ... },
    "cgroupsPath": "/system.slice/docker-abc123.scope",
    "maskedPaths": ["/proc/acpi", "/proc/kcore", "/sys/firmware"],
    "readonlyPaths": ["/proc/sys", "/proc/sysrq-trigger"]
  }
}
```

### runc nsexec — The Namespace Join Dance

runc uses a special Go+C hybrid startup for namespace setup. The issue: Go's runtime spawns multiple OS threads before `main()` runs, making namespace operations unreliable (namespaces are per-thread in Linux). runc solves this with a C constructor that runs **before the Go runtime**:

```c
// vendor/github.com/opencontainers/runc/libcontainer/nsenter/nsexec.c
// This is compiled into a shared library loaded via cgo
// It runs as a C constructor before Go's runtime initializes

// The key insight: we need to manipulate namespaces on a single-threaded
// process. Go's runtime starts threads early. So we fork() from C before Go starts.

__attribute__((constructor)) void nsexec(void)
{
    // Called before Go runtime starts
    // Read parent pipe for instructions
    // fork() into new namespaces
    // setns() to join existing namespaces
    // signal parent when ready
}

// Three stages:
// Stage 0: Read instructions from parent via pipe
// Stage 1: Clone into new namespaces (CLONE_NEWNS | CLONE_NEWPID | ...)
// Stage 2: setns() to join each namespace from file descriptors
//          passed by parent (for --pid-file, --net etc.)
```

```
runc create
    |
    +-- fork()  [C constructor, before Go runtime]
    |       |
    |       | Stage 1: clone() with CLONE_NEWPID | CLONE_NEWNS | ...
    |       |
    |       +-- fork()  [now in new namespaces]
    |               |
    |               | Stage 2: mount rootfs, setup /dev, /proc
    |               |          apply seccomp, drop caps
    |               |          write pidfile, signal parent
    |               |
    |               | execve(container_process)
    |
    +-- Go runtime starts (in parent)
        Waits for signal from C child
        Writes cgroup limits
        Returns control to containerd-shim
```

---

## 6. Linux Capabilities & Privilege Model

Docker does NOT run as fully privileged root. Instead, it uses Linux capabilities to grant specific privileges.

```
Full root (all 40 capabilities)
+-----------------------------------------------+
| CAP_SYS_ADMIN  CAP_SYS_PTRACE  CAP_NET_ADMIN  |
| CAP_SYS_MODULE CAP_SYS_RAWIO   CAP_SYS_BOOT   |
| ... (dangerous: can escape container)          |
+-----------------------------------------------+
                    |
                    | Docker default drop
                    v
Docker default capability set (bounding set)
+-----------------------------------------------+
| CAP_CHOWN        CAP_DAC_OVERRIDE CAP_FSETID  |
| CAP_FOWNER       CAP_MKNOD        CAP_NET_RAW |
| CAP_SETGID       CAP_SETUID       CAP_SETFCAP |
| CAP_SETPCAP      CAP_NET_BIND_SERVICE          |
| CAP_SYS_CHROOT   CAP_KILL         CAP_AUDIT_WRITE|
+-----------------------------------------------+

Dropped by default (require --cap-add):
  CAP_SYS_ADMIN    -- mount, BPF, sysctl, etc.
  CAP_NET_ADMIN    -- interface config, routing
  CAP_SYS_PTRACE   -- ptrace other processes
  CAP_SYS_MODULE   -- load kernel modules
  CAP_SYS_RAWIO    -- raw I/O port access
```

### Kernel Capability Structures

```c
// include/linux/cred.h
struct cred {
    // ...
    kuid_t      uid;       // real UID
    kgid_t      gid;       // real GID
    kuid_t      suid;      // saved UID
    kgid_t      sgid;      // saved GID
    kuid_t      euid;      // effective UID
    kgid_t      egid;      // effective GID
    kuid_t      fsuid;     // FS UID
    kgid_t      fsgid;     // FS GID
    
    kernel_cap_t cap_inheritable;  // caps child can inherit
    kernel_cap_t cap_permitted;    // caps this process may set
    kernel_cap_t cap_effective;    // currently active caps
    kernel_cap_t cap_bset;         // bounding set cap
    kernel_cap_t cap_ambient;      // ambient caps (kernel 4.3+)
    // ...
};

// include/uapi/linux/capability.h
typedef struct __user_cap_data_struct {
    __u32 effective;
    __u32 permitted;
    __u32 inheritable;
} __user *cap_user_data_t;

// kernel/capability.c — sys_capset()
SYSCALL_DEFINE2(capset, cap_user_header_t, header,
    const cap_user_data_t, data)
{
    // validate against current permitted set
    // update task credentials
    // audit the change
}
```

### C: Applying Capability Restrictions (runc style)

```c
// Mirrors runc's capability setup in libcontainer/capabilities.go
// gcc -o cap_setup cap_setup.c -lcap

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/capability.h>
#include <linux/securebits.h>
#include <errno.h>

// Docker's default capability set (Docker v26+)
static const cap_value_t docker_default_caps[] = {
    CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FSETID, CAP_FOWNER,
    CAP_MKNOD, CAP_NET_RAW, CAP_SETGID, CAP_SETUID,
    CAP_SETFCAP, CAP_SETPCAP, CAP_NET_BIND_SERVICE,
    CAP_SYS_CHROOT, CAP_KILL, CAP_AUDIT_WRITE,
};
#define NUM_DEFAULT_CAPS (sizeof(docker_default_caps)/sizeof(docker_default_caps[0]))

int setup_capabilities(void)
{
    cap_t caps;
    cap_value_t cap_list[CAP_LAST_CAP + 1];
    int i;

    // Step 1: Clear all capabilities
    caps = cap_init();
    if (!caps) {
        perror("cap_init");
        return -1;
    }

    // Step 2: Set only Docker's default set
    for (i = 0; i < (int)NUM_DEFAULT_CAPS; i++) {
        cap_list[i] = docker_default_caps[i];
    }

    if (cap_set_flag(caps, CAP_EFFECTIVE,   NUM_DEFAULT_CAPS, cap_list, CAP_SET) < 0 ||
        cap_set_flag(caps, CAP_PERMITTED,   NUM_DEFAULT_CAPS, cap_list, CAP_SET) < 0 ||
        cap_set_flag(caps, CAP_INHERITABLE, NUM_DEFAULT_CAPS, cap_list, CAP_SET) < 0) {
        perror("cap_set_flag");
        cap_free(caps);
        return -1;
    }

    if (cap_set_proc(caps) < 0) {
        perror("cap_set_proc");
        cap_free(caps);
        return -1;
    }
    cap_free(caps);

    // Step 3: Set bounding set — drop all caps NOT in docker set
    for (i = 0; i <= CAP_LAST_CAP; i++) {
        int in_default = 0;
        for (int j = 0; j < (int)NUM_DEFAULT_CAPS; j++) {
            if ((cap_value_t)i == docker_default_caps[j]) {
                in_default = 1;
                break;
            }
        }
        if (!in_default) {
            if (prctl(PR_CAPBSET_DROP, i, 0, 0, 0) < 0) {
                if (errno != EINVAL) {
                    perror("PR_CAPBSET_DROP");
                    return -1;
                }
            }
        }
    }

    // Step 4: Set securebits — prevent privilege escalation via setuid binaries
    if (prctl(PR_SET_SECUREBITS,
              SECBIT_NO_SETUID_FIXUP | SECBIT_NO_SETUID_FIXUP_LOCKED |
              SECBIT_NOROOT | SECBIT_NOROOT_LOCKED,
              0, 0, 0) < 0) {
        perror("PR_SET_SECUREBITS");
        return -1;
    }

    // Step 5: Prevent privilege escalation (no_new_privs)
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    printf("Capabilities configured successfully\n");
    return 0;
}

int main(void)
{
    if (setup_capabilities() < 0)
        return 1;

    // Print current capabilities
    cap_t caps = cap_get_proc();
    char *caps_str = cap_to_text(caps, NULL);
    printf("Current caps: %s\n", caps_str);
    cap_free(caps_str);
    cap_free(caps);

    return 0;
}
```

---

## 7. Seccomp BPF — Syscall Filtering

Docker applies a seccomp profile that **blocks dangerous syscalls** using Berkeley Packet Filter programs evaluated in the kernel.

```
Container process -> syscall -> kernel entry
                                    |
                                    | seccomp BPF program
                                    | (evaluated in kernel)
                                    |
                        +-----------+-----------+
                        |                       |
                   SECCOMP_RET_ALLOW    SECCOMP_RET_KILL_PROCESS
                   (continue)           (SIGSYS delivered)
                        |
                   SECCOMP_RET_ERRNO(X) (return -EPERM to process)
                   SECCOMP_RET_TRACE    (notify ptrace tracer)
                   SECCOMP_RET_USER_NOTIF (notify userspace via fd)
```

### Kernel Seccomp Implementation

```c
// kernel/seccomp.c
// include/linux/seccomp.h

struct seccomp_filter {
    refcount_t          usage;
    bool                log;
    bool                wait_killable_recv;
    struct action_cache cache;      // per-arch action cache
    struct seccomp_filter *prev;    // linked list (filters stack)
    struct bpf_prog     *prog;      // the BPF program
    struct notification  *notif;    // for SECCOMP_RET_USER_NOTIF
    struct mutex         notify_lock;
    wait_queue_head_t    wqh;
};

// task_struct embeds:
struct seccomp {
    int     mode;            // SECCOMP_MODE_DISABLED / FILTER
    atomic_t filter_count;  // number of filters installed
    struct seccomp_filter *filter;
};

// Entry point: called from syscall entry paths
// arch/x86/entry/common.c -> do_syscall_64() -> secure_computing()
static inline int secure_computing(const struct seccomp_data *sd)
{
    if (unlikely(test_thread_flag(TIF_SECCOMP)))
        return __secure_computing(sd);
    return 0;
}

// __secure_computing runs the BPF program chain
int __seccomp_filter(int this_syscall, const struct seccomp_data *sd,
                     const bool recheck_after_trace)
{
    u32 filter_ret, action;
    struct seccomp_filter *match = NULL;
    
    // Walk filter chain, execute each BPF program
    filter_ret = seccomp_run_filters(sd, &match);
    action = filter_ret & SECCOMP_RET_ACTION_FULL;
    
    switch (action) {
    case SECCOMP_RET_ALLOW:
        return 0;
    case SECCOMP_RET_KILL_PROCESS:
        do_exit(SIGSYS);  // never returns
    case SECCOMP_RET_KILL_THREAD:
        do_exit(SIGSYS);
    case SECCOMP_RET_ERRNO:
        syscall_set_return_value(current, current_pt_regs(),
                                 -seccomp_ret_errno(filter_ret), 0);
        return -1;
    case SECCOMP_RET_TRACE:
        // wake ptrace tracer
    case SECCOMP_RET_USER_NOTIF:
        // notify via file descriptor (used by rootless, sysbox)
    }
}
```

### Docker's Default Seccomp Profile

Docker blocks ~44 syscalls by default. Key blocked ones:

```
Blocked (SCMP_ACT_ERRNO):
  keyctl, add_key, request_key    -- kernel keyring
  ptrace                          -- process introspection
  personality (not native ABI)    -- ABI emulation
  acct                            -- process accounting
  settimeofday, stime, clock_adjtime  -- time modification
  swapon, swapoff                 -- swap control
  syslog                          -- kernel log
  mount, umount2                  -- unless CAP_SYS_ADMIN
  create_module, init_module,
  finit_module, delete_module     -- kernel modules
  iopl, ioperm                    -- I/O ports
  kexec_load, kexec_file_load     -- kernel replacement
  open_by_handle_at               -- bypass path restrictions
  perf_event_open                 -- unless perf_event_paranoid allows
  ...
```

### C: Installing a Seccomp Filter

```c
// Demonstrates how runc installs seccomp filters via prctl(2)
// gcc -o seccomp_demo seccomp_demo.c -lseccomp

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <errno.h>
#include <string.h>
#include <stddef.h>

// BPF filter that allows most syscalls but blocks ptrace and reboot
// Equivalent to libseccomp's SCMP_ACT_ERRNO(EPERM) on specific syscalls

#define VALIDATE_ARCH                                           \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,                        \
             (offsetof(struct seccomp_data, arch))),           \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64,   \
             1, 0),                                            \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)

#define LOAD_SYSCALL_NR                                        \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,                       \
             (offsetof(struct seccomp_data, nr)))

#define BLOCK_SYSCALL(nr)                                      \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, nr, 0, 1),           \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))

#define ALLOW_ALL                                              \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)

static struct sock_filter docker_like_filter[] = {
    VALIDATE_ARCH,
    LOAD_SYSCALL_NR,
    BLOCK_SYSCALL(__NR_ptrace),
    BLOCK_SYSCALL(__NR_reboot),
    BLOCK_SYSCALL(__NR_init_module),
    BLOCK_SYSCALL(__NR_finit_module),
    BLOCK_SYSCALL(__NR_delete_module),
    BLOCK_SYSCALL(__NR_kexec_load),
    BLOCK_SYSCALL(__NR_syslog),
    ALLOW_ALL,
};

int install_seccomp(void)
{
    struct sock_fprog prog = {
        .len    = sizeof(docker_like_filter) / sizeof(docker_like_filter[0]),
        .filter = docker_like_filter,
    };

    // no_new_privs must be set first (or have CAP_SYS_ADMIN)
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    // Install the filter via prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, prog)
    // or equivalently: syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog)
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) < 0) {
        perror("prctl(PR_SET_SECCOMP)");
        return -1;
    }

    printf("Seccomp filter installed (%zu instructions)\n",
           prog.len);
    return 0;
}

int main(void)
{
    if (install_seccomp() < 0)
        return 1;

    printf("Testing: open() - should work: ");
    fflush(stdout);
    FILE *f = fopen("/dev/null", "r");
    if (f) { fclose(f); printf("OK\n"); }
    else printf("BLOCKED\n");

    printf("Testing: ptrace() - should be blocked: ");
    fflush(stdout);
    long ret = syscall(__NR_ptrace, 0, 0, 0, 0);
    if (ret < 0 && errno == EPERM)
        printf("BLOCKED (EPERM) - correct!\n");
    else
        printf("allowed (unexpected)\n");

    return 0;
}
```

### Using libseccomp (Docker's actual approach)

```c
// Docker uses libseccomp (which wraps BPF generation)
// runc/libcontainer/seccomp/seccomp_linux.go calls into C via cgo

#include <seccomp.h>

scmp_filter_ctx ctx;
ctx = seccomp_init(SCMP_ACT_ALLOW);  // default: allow

// Add rules
seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(ptrace),   0);
seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(kexec_load), 0);
seccomp_rule_add(ctx, SCMP_ACT_KILL,         SCMP_SYS(add_key),  0);

// Conditional rule: allow clone() but not with CLONE_NEWUSER 
// (prevents namespace escalation inside container)
seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(clone), 1,
    SCMP_A0(SCMP_CMP_MASKED_EQ, CLONE_NEWUSER, CLONE_NEWUSER));

// Load into kernel
seccomp_load(ctx);
seccomp_release(ctx);
```

---

## 8. LSM Integration — AppArmor & SELinux

Linux Security Modules (LSM) provide **mandatory access control** hooks throughout the kernel.

```
Kernel LSM hook architecture (security/security.c):

Process syscall
    |
    v
Kernel operation (e.g., open file)
    |
    v
security_file_open()  <- LSM hook
    |
    +-- call_int_hook(file_open, 0, file, cred)
    |       |
    |       +-- apparmor_file_open()   -> check AppArmor profile
    |       +-- selinux_file_open()    -> check SELinux policy
    |       +-- smack_file_open()      -> check Smack labels
    |
    v
Allow or EACCES/EPERM
```

### AppArmor — Docker's Default LSM

```
# Docker AppArmor profile (simplified from /etc/apparmor.d/docker-default)
# Applied via aa_change_profile() or aa_change_onexec() in runc

profile docker-default flags=(attach_disconnected,mediate_deleted) {
  # Deny raw network access
  network raw,
  network packet,

  # Capability restrictions (in addition to Linux capabilities)
  deny capability mac_admin,
  deny capability mac_override,
  deny capability sys_log,
  deny capability sys_time,
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability net_admin,

  # File access rules
  file,
  umount,

  # Deny specific dangerous mounts
  deny mount fstype=debugfs,
  deny mount fstype=tracefs,
  
  # Allow /proc but not dangerous paths
  /proc/sys/kernel/shm* rw,
  deny /proc/sys/kernel/core_pattern w,
  deny /proc/kcore rwl,
  
  # ptrace/signal restrictions
  ptrace (trace,read) peer=docker-default,
  signal (send,receive) peer=docker-default,
}
```

```c
// kernel/security/apparmor/lsm.c
// AppArmor LSM hooks registration
static struct security_hook_list apparmor_hooks[] __ro_after_init = {
    LSM_HOOK_INIT(ptrace_access_check, apparmor_ptrace_access_check),
    LSM_HOOK_INIT(ptrace_traceme, apparmor_ptrace_traceme),
    LSM_HOOK_INIT(capget, apparmor_capget),
    LSM_HOOK_INIT(capable, apparmor_capable),
    LSM_HOOK_INIT(sb_mount, apparmor_sb_mount),
    LSM_HOOK_INIT(sb_umount, apparmor_sb_umount),
    LSM_HOOK_INIT(sb_pivotroot, apparmor_sb_pivotroot),
    LSM_HOOK_INIT(path_link, apparmor_path_link),
    LSM_HOOK_INIT(path_unlink, apparmor_path_unlink),
    LSM_HOOK_INIT(path_symlink, apparmor_path_symlink),
    LSM_HOOK_INIT(path_mkdir, apparmor_path_mkdir),
    LSM_HOOK_INIT(path_rmdir, apparmor_path_rmdir),
    LSM_HOOK_INIT(path_mknod, apparmor_path_mknod),
    LSM_HOOK_INIT(path_rename, apparmor_path_rename),
    LSM_HOOK_INIT(path_chmod, apparmor_path_chmod),
    LSM_HOOK_INIT(path_chown, apparmor_path_chown),
    LSM_HOOK_INIT(file_open, apparmor_file_open),
    LSM_HOOK_INIT(file_lock, apparmor_file_lock),
    LSM_HOOK_INIT(socket_create, apparmor_socket_create),
    LSM_HOOK_INIT(socket_bind, apparmor_socket_bind),
    LSM_HOOK_INIT(socket_connect, apparmor_socket_connect),
    // ... ~60 more hooks
};
```

---

## 9. Networking Internals — veth, bridge, netfilter, iptables

```
Container A (net ns A)          Container B (net ns B)
+-------------------+           +-------------------+
|   eth0: 172.17.0.2|           |   eth0: 172.17.0.3|
|   (veth peer)     |           |   (veth peer)     |
+--------+----------+           +--------+----------+
         |veth0                          |veth1
         |                               |
+--------+---------+--------------------+----------+
|              docker0 bridge (172.17.0.1)          |
|   net/bridge/br_main.c                            |
|   L2 forwarding between containers                |
+-------------------+---------+--------------------+
                    |         |
              iptables     iptables
              MASQUERADE   DNAT
              (outbound)   (port mapping)
                    |
            +-------+-------+
            |  eth0 (host)  |
            |  (real NIC)   |
            +-------+-------+
                    |
                 Internet
```

### veth (Virtual Ethernet) Pairs

veth pairs are **tunnel-like network devices** — packets sent into one end come out the other. Docker creates one veth per container, places one end in the container net namespace and the other in the host.

```c
// drivers/net/veth.c
// veth_xmit() — core transmit function
static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *rcv_priv, *priv = netdev_priv(dev);
    struct veth_rq *rq = NULL;
    struct net_device *rcv;
    int length = skb->len;
    bool use_napi = false;
    int rxq;

    rcu_read_lock();
    rcv = rcu_dereference(priv->peer);  // the OTHER end of the pair
    if (unlikely(!rcv)) {
        kfree_skb(skb);
        goto drop;
    }
    // ... deliver skb to peer's receive queue
    veth_forward_skb(rcv, skb, rq, use_napi);
    // ...
}

// Creating a veth pair: RTNETLINK NEWLINK with IFLA_INFO_KIND="veth"
// net/core/rtnetlink.c -> rtnl_newlink() -> veth_newlink()
static int veth_newlink(struct net *src_net, struct net_device *dev,
                        struct nlattr *tb[], struct nlattr *data[],
                        struct netlink_ext_ack *extack)
{
    // Create peer device in target namespace
    // net = rtnl_link_get_net(src_net, tbp[IFLA_NET_NS_PID])
    // peer = rtnl_create_link(net, ifname, ...)
    // register both devices
    // set priv->peer pointers
}
```

### How Docker Creates a veth Pair

```go
// github.com/moby/moby/libnetwork/drivers/bridge/bridge_linux.go
// (simplified)

func (d *driver) CreateEndpoint(nid, eid string, ifInfo driverapi.InterfaceInfo,
    epOptions map[string]interface{}) error {
    
    // Create veth pair via netlink
    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{
            Name:  "veth" + generateIfaceName(),
            MTU:   d.config.Mtu,
        },
        PeerName: "eth0",  // name inside container
    }
    
    if err := netlink.LinkAdd(veth); err != nil {
        return err
    }
    
    // Move peer into container's network namespace
    peer, _ := netlink.LinkByName(veth.PeerName)
    netlink.LinkSetNsFd(peer, int(containerNsFd))
    
    // Add host end to bridge
    hostVeth, _ := netlink.LinkByName(veth.Name)
    netlink.LinkSetMaster(hostVeth, bridge)
    
    // Bring up both ends
    netlink.LinkSetUp(hostVeth)
    // peer brought up inside container
}
```

### Bridge Networking Internals

```c
// net/bridge/br_main.c — the docker0 bridge

struct net_bridge {
    spinlock_t              lock;
    spinlock_t              hash_lock;
    struct hlist_head       frame_handle_list;
    
    struct net_device       *dev;           // the bridge netdev
    struct pcpu_sw_netstats __percpu *stats;
    
    struct rhashtable       fdb_hash_tbl;   // forwarding database (MAC table)
    struct list_head        port_list;      // attached ports (veth ends)
    
    __be32                  designated_root;
    __be32                  bridge_id;
    
    // STP (spanning tree) config
    unsigned long           stp_enabled;
    
    // VLAN support
    struct net_bridge_vlan_group __rcu *vlgrp;
    
    // netfilter hooks
    u8                      nf_call_iptables;
    u8                      nf_call_ip6tables;
    u8                      nf_call_arptables;
};

// Frame forwarding: br_handle_frame() in net/bridge/br_input.c
rx_handler_result_t br_handle_frame(struct sk_buff **pskb)
{
    // 1. NF_BR_PRE_ROUTING (netfilter hook)
    // 2. MAC lookup in FDB
    // 3. If known unicast: forward to specific port
    // 4. If unknown/broadcast: flood to all ports
    // 5. NF_BR_FORWARD (netfilter hook)
    // 6. NF_BR_POST_ROUTING (netfilter hook)
}
```

### iptables & DOCKER chain

Docker manages iptables rules for NAT (outbound) and DNAT (port mapping):

```bash
# What Docker creates in iptables
# iptables -t nat -L -n -v

# PREROUTING: incoming packets -> DOCKER chain
Chain PREROUTING (policy ACCEPT)
  DOCKER  all -- anywhere  anywhere  ADDRTYPE match dst-type LOCAL

# DOCKER chain: port mappings (DNAT)
Chain DOCKER (2 references)
  DNAT  tcp -- anywhere  anywhere  tcp dpt:8080 to:172.17.0.2:80

# POSTROUTING: outbound NAT (masquerade for container traffic)  
Chain POSTROUTING (policy ACCEPT)
  MASQUERADE  all -- 172.17.0.0/16  anywhere  # container -> internet

# FORWARD chain: inter-container traffic
Chain FORWARD (policy DROP)
  DOCKER-USER     all -- anywhere  anywhere
  DOCKER-ISOLATION-STAGE-1  all -- anywhere  anywhere
  ACCEPT  all -- anywhere  anywhere  ctstate RELATED,ESTABLISHED
  DOCKER  all -- anywhere  anywhere
  ACCEPT  all -- 172.17.0.0/16  anywhere
  ACCEPT  all -- anywhere  172.17.0.0/16
```

```c
// kernel netfilter hooks that implement iptables
// net/netfilter/x_tables.c, net/ipv4/netfilter/

// The NF_HOOK macro (include/linux/netfilter.h)
static inline int NF_HOOK(uint8_t pf, unsigned int hook,
                           struct net *net, struct sock *sk,
                           struct sk_buff *skb,
                           struct net_device *in, struct net_device *out,
                           int (*okfn)(struct net *, struct sock *, struct sk_buff *))
{
    int ret = nf_hook(pf, hook, net, sk, skb, in, out, okfn);
    if (ret == 1)
        ret = okfn(net, sk, skb);
    return ret;
}

// Hook points in IPv4 stack:
// NF_INET_PRE_ROUTING   -> PREROUTING   (port mapping: DNAT)
// NF_INET_LOCAL_IN      -> INPUT
// NF_INET_FORWARD       -> FORWARD      (container routing)
// NF_INET_LOCAL_OUT     -> OUTPUT
// NF_INET_POST_ROUTING  -> POSTROUTING  (masquerade: SNAT)
```

---

## 10. Container Networking Deep Dive — XDP, eBPF, tc

Modern container networking (Cilium, Calico eBPF mode) bypasses iptables entirely using XDP and tc BPF programs.

```
Packet receive path with XDP/eBPF:

NIC -> DMA -> ring buffer
           |
           v
    XDP program (runs before kernel network stack)
    (attached via NETDEV_XDP_ACT_BASIC or offloaded to NIC)
           |
    +------+------+
    |             |
  XDP_DROP    XDP_PASS / XDP_TX / XDP_REDIRECT
  (drop early)    |
                  v
         kernel network stack
         (netif_receive_skb)
                  |
                  v
         tc (traffic control) ingress hook
         BPF program (cls_bpf / act_bpf)
                  |
                  v
         netfilter (iptables/nftables)
                  |
                  v
         socket / application
```

### eBPF for Container Networking (Cilium style)

```c
// BPF program to implement container policy at tc level
// Compiled with: clang -O2 -target bpf -c container_policy.bpf.c

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Map: container IP -> allowed dst port bitmask
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);   // source IP
    __type(value, __u64); // allowed port bitmask
} container_policy SEC(".maps");

// Map: packet statistics per container
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);   // container IP
    __type(value, __u64); // packet count
} pkt_count SEC(".maps");

SEC("tc")
int container_egress_filter(struct __sk_buff *skb)
{
    void *data_end = (void *)(long)skb->data_end;
    void *data     = (void *)(long)skb->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;
    
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return TC_ACT_OK;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_OK;
    
    __u32 src_ip = ip->saddr;
    
    // Lookup policy for this container
    __u64 *allowed_ports = bpf_map_lookup_elem(&container_policy, &src_ip);
    if (!allowed_ports)
        return TC_ACT_SHOT;  // deny if no policy
    
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
        if ((void *)(tcp + 1) > data_end)
            return TC_ACT_SHOT;
        
        __u16 dport = bpf_ntohs(tcp->dest);
        
        // Check if destination port is allowed
        if (dport < 64 && !(*allowed_ports & (1ULL << dport)))
            return TC_ACT_SHOT;
        if (dport >= 64 && dport < 128 &&
            !(*allowed_ports & (1ULL << (dport - 64))))
            return TC_ACT_SHOT;
    }
    
    // Update packet counter
    __u64 *counter = bpf_map_lookup_elem(&pkt_count, &src_ip);
    if (counter)
        __sync_fetch_and_add(counter, 1);
    
    return TC_ACT_OK;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Attach BPF program to container's veth interface
# (what Cilium/Calico do, bypassing iptables)

CONTAINER_ID="abc123"
VETH=$(ip link | grep -A1 "$(docker inspect $CONTAINER_ID \
    --format '{{.NetworkSettings.SandboxKey}}'" | awk '{print $2}' | tr -d ':')

# Attach tc BPF program
tc qdisc add dev $VETH clsact
tc filter add dev $VETH egress bpf da obj container_policy.bpf.o sec tc
tc filter add dev $VETH ingress bpf da obj container_policy.bpf.o sec tc

# Show attached programs
tc filter show dev $VETH egress
```

---

## 11. Process Lifecycle — clone(2), execve(2), wait(2)

```
dockerd                  containerd              runc                container
  |                          |                     |                    |
  | POST /containers/create  |                     |                    |
  |------------------------->|                     |                    |
  |                          | containerd-shim      |                    |
  |                          |--fork()------------>|                    |
  |                          |                     | clone(CLONE_NEWPID |
  |                          |                     |    |CLONE_NEWNS    |
  |                          |                     |    |CLONE_NEWNET..):|
  |                          |                     |    |               |
  |                          |                     | parent stays as    |
  |                          |                     | namespace manager  |
  |                          |                     |    |               |
  |                          |                     |    v  (child)      |
  |                          |                     | pivot_root         |
  |                          |                     | mount /proc        |
  |                          |                     | apply seccomp      |
  |                          |                     | drop caps          |
  |                          |                     |    |               |
  |                          |                     | execve(entrypoint) |
  |                          |                     |    |               |
  |                          |                     |    v               |
  |                          |                     |                  bash
  |                          |                     |                 (pid=1 in ns)
```

### pivot_root vs chroot

runc uses `pivot_root(2)` (not `chroot`) for stronger isolation:

```c
// libcontainer/rootfs_linux.go -> pivotRoot() -> syscall.PivotRoot()
// kernel implementation: fs/namespace.c -> sys_pivot_root()

// pivot_root makes new_root the new filesystem root
// old_root becomes accessible at put_old (for unmounting)
SYSCALL_DEFINE2(pivot_root, const char __user *, new_root,
                const char __user *, put_old)
{
    struct path new, old, parent_path, root_parent, root;
    struct mount *new_mnt, *root_mnt, *old_mnt, *old_mnt_parent;
    struct mountpoint *old_mp, *root_mp;
    
    // Validation:
    // - new_root must be a mount point
    // - put_old must be under new_root
    // - new_root != current root
    
    // Atomic swap of root mount
    // This is stronger than chroot: process cannot escape with
    // chroot("../../../") tricks because there's no ".." above new root
}
```

```c
// runc pivot_root sequence (libcontainer/rootfs_linux.go)
// Translated to C for clarity:

#define _GNU_SOURCE
#include <sys/syscall.h>
#include <sys/mount.h>
#include <unistd.h>
#include <fcntl.h>

int container_pivot_root(const char *rootfs)
{
    int old_root_fd, new_root_fd;
    
    // Bind mount rootfs to itself (needed for pivot_root)
    if (mount(rootfs, rootfs, NULL, MS_BIND | MS_REC, NULL) < 0)
        return -1;

    // Open handles before changing root
    old_root_fd = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    new_root_fd = open(rootfs, O_RDONLY | O_DIRECTORY | O_CLOEXEC);

    // Change to new root
    if (fchdir(new_root_fd) < 0) return -1;

    // pivot_root: "." becomes new root, old root accessible via old_root_fd
    if (syscall(SYS_pivot_root, ".", ".") < 0) return -1;

    // fchdir to old root via preserved fd
    fchdir(old_root_fd);

    // Unmount old root (recursive, lazy)
    if (umount2(".", MNT_DETACH) < 0) return -1;

    // Move back to new root
    if (chdir("/") < 0) return -1;

    close(old_root_fd);
    close(new_root_fd);
    return 0;
}
```

---

## 12. Signal Handling & PID 1 Problem

In a container, the container's init process has **PID 1**. This is special in Linux:

```
Linux kernel signal behavior:
- SIGKILL / SIGSTOP: always delivered, even to PID 1
- Other signals: if PID 1 has no handler registered -> IGNORED
  (unlike other processes where default action applies)

This means:
  docker stop <container>
      -> sends SIGTERM to PID 1
      -> if PID 1 is a shell script or app without SIGTERM handler
      -> SIGTERM is IGNORED
      -> Docker waits 10 seconds
      -> sends SIGKILL
      -> container force-killed

  Solution: use a proper init (tini, dumb-init) as PID 1
```

```c
// kernel/signal.c — sig_ignored()
static bool sig_ignored(struct task_struct *t, int sig, bool from_ancestor_ns)
{
    if (sigismember(&t->blocked, sig))
        return false;

    if (!task_is_ignored(t, sig))
        return false;

    // PID 1 init process: never ignore SIGKILL/SIGSTOP
    // But other signals to pid 1: only if explicitly handled
    if (is_global_init(t)) {
        // PID 1 in root namespace gets special treatment
        // signals are only delivered if handler is installed
    }

    return true;
}

// is_global_init() checks if task is PID 1 in ROOT namespace
// NOT container's PID 1 — that's just a regular process from host's view
// Container's PID 1 does NOT get init's special signal immunity
// unless it's in its own PID namespace (which it always is in Docker)
```

```c
// tini (krallin/tini) — what Docker uses as --init
// Simplified version of what tini does:

#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>

// Forward all signals to child process group
static pid_t child_pid = -1;

static void signal_handler(int sig)
{
    if (child_pid > 0)
        kill(-child_pid, sig);  // send to entire process group
}

int main(int argc, char *argv[])
{
    // Register handlers for all signals we want to forward
    struct sigaction sa = { .sa_handler = signal_handler };
    for (int i = 1; i < NSIG; i++)
        sigaction(i, &sa, NULL);

    // Fork the actual container process
    child_pid = fork();
    if (child_pid == 0) {
        // Child: become new session leader, reset signal handlers
        setsid();
        execvp(argv[1], &argv[1]);
    }

    // PID 1 reaping loop: must reap ALL zombie children
    // (orphaned processes get reparented to PID 1)
    int status;
    pid_t pid;
    while (1) {
        pid = waitpid(-1, &status, 0);
        if (pid == child_pid) {
            // Main child exited, propagate exit code
            if (WIFEXITED(status))
                return WEXITSTATUS(status);
            return 128 + WTERMSIG(status);
        }
        // else: reap other orphaned zombie
    }
}
```

---

## 13. Device Access — /dev, devtmpfs, device cgroups

```
Container /dev hierarchy:

/dev/
  null        (c 1:3)   - always present
  zero        (c 1:5)   - always present  
  full        (c 1:7)   - always present
  random      (c 1:8)   - always present
  urandom     (c 1:9)   - always present
  tty         (c 5:0)   - always present
  pts/        (devpts)  - pseudo-terminals
  shm/        (tmpfs)   - shared memory
  
  [host devices are NOT mounted by default]
  [docker run --device adds specific devices]
```

### Device cgroup Controller

```c
// kernel/cgroup/devices.c  (v1) / ebpf device program (v2)
// In cgroup v2, device access control is done via BPF:

// include/uapi/linux/bpf.h
// BPF_PROG_TYPE_CGROUP_DEVICE: attached to cgroup, called on device access

// runc generates and attaches a BPF program for each container:
// opencontainers/runc/libcontainer/cgroups/ebpf/devicefilter/devicefilter.go
SEC("cgroup/dev")
int device_filter(struct bpf_cgroup_dev_ctx *ctx)
{
    // ctx->access_type: BPF_DEVCG_ACC_READ/WRITE/MKNOD
    // ctx->major, ctx->minor: device numbers
    // ctx->type: BPF_DEVCG_DEV_CHAR / BPF_DEVCG_DEV_BLOCK
    
    // Allow list approach:
    // Check if (type, major, minor) matches allowed device list
    // Default: deny
    
    __u32 key = 0;
    __u64 *val = bpf_map_lookup_elem(&allowed_devices, &key);
    
    // Allow /dev/null (1:3), /dev/zero (1:5), /dev/random (1:8) etc.
    if (ctx->type == BPF_DEVCG_DEV_CHAR) {
        if (ctx->major == 1 && (ctx->minor == 3 || ctx->minor == 5 ||
                                 ctx->minor == 7 || ctx->minor == 8 ||
                                 ctx->minor == 9))
            return 1;  // allow
        if (ctx->major == 5 && ctx->minor == 0)
            return 1;  // /dev/tty
        if (ctx->major == 5 && ctx->minor == 2)
            return 1;  // /dev/ptmx
        if (ctx->major == 136)
            return 1;  // /dev/pts/*
    }
    return 0;  // deny all others
}
```

### Passing Host Devices to Container

```bash
# docker run --device /dev/nvidia0:/dev/nvidia0
# runc translates this to:

# 1. Add device node to container rootfs:
mknod -m 666 /container/rootfs/dev/nvidia0 c 195 0

# 2. Add to device cgroup allow list (v1) or BPF program (v2)
echo "c 195:0 rwm" > /sys/fs/cgroup/.../devices.allow  # v1

# 3. Bind mount into container namespace:
mount --bind /dev/nvidia0 /container/rootfs/dev/nvidia0
```

---

## 14. Memory Management — OOM, hugepages, memory limits

### OOM Killer in Container Context

```c
// mm/oom_kill.c — oom_kill_process()
// When container exceeds memory.max, kernel runs OOM killer

// OOM score calculation (simplified)
long oom_badness(struct task_struct *p, unsigned long totalpages)
{
    long points;
    long adj;

    // base score: RSS + swap usage as percentage of total memory
    points = get_mm_rss(p->mm) + get_mm_counter(p->mm, MM_SWAPENTS)
           + mm_pgtables_bytes(p->mm) / PAGE_SIZE;
    
    // adjust by /proc/PID/oom_score_adj (-1000 to +1000)
    adj = (long)p->signal->oom_score_adj;
    if (adj == OOM_SCORE_ADJ_MIN)
        return LONG_MIN;

    points = points * (1000 + adj) / 1000;
    return points;
}

// With cgroup v2 memory.oom.group=1:
// All processes in the cgroup are killed together
// (avoids killing only one process of a multi-process app)
```

### Memory Stats from Kernel's Perspective

```bash
# Per-container memory info
CPID=$(docker inspect --format '{{.State.Pid}}' <container>)

# From proc
cat /proc/$CPID/status | grep -E 'Vm|Rss|Swap'

# From cgroup v2
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/memory.stat
# anon: anonymous memory (heap/stack)
# file: page cache (file-backed)
# kernel: kernel memory (slab, stack, page tables)
# pgfault: minor page faults
# pgmajfault: major page faults (disk I/O)

# Memory pressure (PSI)
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/memory.pressure
# some avg10=0.00 avg60=0.00 avg300=0.00 total=0
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

### Hugepages in Containers

```c
// Docker supports --hugepages-mount= and --mount type=tmpfs,tmpfs-mode=1770
// Kernel hugepage allocation: mm/hugetlb.c

// Container config.json for hugepages:
// "hugepageLimits": [{"pageSize": "2MB", "limit": 524288000}]

// runc writes:
// echo 250 > /sys/fs/cgroup/hugetlb.2MB.limit_in_bytes  (v1)
// or equivalent BPF approach in v2

// Anonymous hugepage allocation from container:
// mmap(NULL, 2MB, PROT_READ|PROT_WRITE,
//      MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0)
// -> kernel: hugetlb_mmap() -> alloc_huge_page() -> dequeue_huge_page_vma()
```

---

## 15. Copy-on-Write & Page Cache Interaction

```
Multiple containers sharing the same image layer:

Container A                Container B
  |                          |
  | reads /lib/libc.so       | reads /lib/libc.so
  v                          v
OverlayFS lower dir        OverlayFS lower dir
  |                          |
  +-------->  Page Cache  <--+
             (single copy
              in kernel)
             
- Both containers read from the SAME physical pages
- No duplication: efficient for memory
- On write (CoW): OverlayFS copy-up creates new page in upper layer
```

```c
// fs/overlayfs/copy_up.c
// copy_up triggered by write -> ovl_write_iter() -> ovl_copy_up()
int ovl_copy_up_with_data(struct dentry *dentry)
{
    // 1. Create upper dir if needed
    err = ovl_copy_up_one(dentry->d_parent, ...);
    
    // 2. Create the file in upper
    // using vfs_create() or vfs_mknod()
    
    // 3. Copy data: vfs_copy_file_range() uses sendfile-like mechanism
    // This reads from lower's page cache and writes to upper
    // kernel splice path: do_splice_direct() -> splice_file_to_pipe()
    err = ovl_copy_up_data(old_path, new_path, stat.size);
    
    // 4. Copy metadata
    err = ovl_copy_xattr(old_path.dentry, new.dentry);
    
    // 5. Atomic: rename new to final path
    err = vfs_rename(...);
}

// The interesting part: after copy-up, the inode in upper and lower
// both exist. OverlayFS redirects all future accesses to upper inode.
// Lower inode's page cache can be evicted freely.
```

---

## 16. Go Implementation — containerd & Docker Engine

### containerd Task API (gRPC client)

```go
// How dockerd calls containerd to create a container task
// Similar to: github.com/containerd/containerd/client.go

package main

import (
    "context"
    "fmt"
    "os"
    "syscall"

    "github.com/containerd/containerd"
    "github.com/containerd/containerd/cio"
    "github.com/containerd/containerd/namespaces"
    "github.com/containerd/containerd/oci"
    "github.com/opencontainers/runtime-spec/specs-go"
)

func runContainer(ctx context.Context, imageRef string, cmd []string) error {
    // Connect to containerd socket
    client, err := containerd.New("/run/containerd/containerd.sock")
    if err != nil {
        return fmt.Errorf("connecting to containerd: %w", err)
    }
    defer client.Close()

    // Use "default" containerd namespace (Docker uses "moby")
    ctx = namespaces.WithNamespace(ctx, "default")

    // Pull image (downloads layers, stores in content store)
    image, err := client.Pull(ctx, imageRef,
        containerd.WithPullUnpack,  // unpack layers to snapshotter
    )
    if err != nil {
        return fmt.Errorf("pulling image: %w", err)
    }

    // Create container with OCI spec
    // oci.WithImageConfig sets up process, env, working dir from image
    // oci.WithNewSnapshot uses overlayfs snapshotter
    container, err := client.NewContainer(ctx,
        "my-container-id",
        containerd.WithImage(image),
        containerd.WithNewSnapshot("my-container-snapshot", image),
        containerd.WithNewSpec(
            oci.WithImageConfig(image),
            oci.WithProcessArgs(cmd...),
            // Add custom namespaces, capabilities etc.
            withContainerSpec(),
        ),
    )
    if err != nil {
        return fmt.Errorf("creating container: %w", err)
    }
    defer container.Delete(ctx, containerd.WithSnapshotCleanup)

    // Create task (this forks runc)
    task, err := container.NewTask(ctx, cio.NewCreator(cio.WithStdio))
    if err != nil {
        return fmt.Errorf("creating task: %w", err)
    }
    defer task.Delete(ctx)

    // Wait channel for exit status
    exitStatusC, err := task.Wait(ctx)
    if err != nil {
        return fmt.Errorf("waiting: %w", err)
    }

    // Start the container process (sends SIGCONT to runc's init)
    if err = task.Start(ctx); err != nil {
        return fmt.Errorf("starting task: %w", err)
    }

    // Wait for exit
    status := <-exitStatusC
    code, _, err := status.Result()
    if err != nil {
        return fmt.Errorf("exit status error: %w", err)
    }
    fmt.Printf("Container exited with code %d\n", code)
    return nil
}

func withContainerSpec() oci.SpecOpts {
    return func(ctx context.Context, client oci.Client,
        c *containers.Container, s *specs.Spec) error {
        
        // Set Linux-specific options
        s.Linux = &specs.Linux{
            // Namespaces
            Namespaces: []specs.LinuxNamespace{
                {Type: specs.PIDNamespace},
                {Type: specs.NetworkNamespace},
                {Type: specs.IPCNamespace},
                {Type: specs.UTSNamespace},
                {Type: specs.MountNamespace},
            },
            // cgroup path
            CgroupsPath: "/system.slice/my-container.scope",
            // Resource limits
            Resources: &specs.LinuxResources{
                Memory: &specs.LinuxMemory{
                    Limit: func() *int64 { l := int64(512 * 1024 * 1024); return &l }(),
                },
                CPU: &specs.LinuxCPU{
                    Quota:  func() *int64 { q := int64(50000); return &q }(),
                    Period: func() *uint64 { p := uint64(100000); return &p }(),
                },
            },
            // Masked paths
            MaskedPaths: []string{
                "/proc/acpi", "/proc/kcore", "/proc/keys",
                "/proc/latency_stats", "/proc/timer_list",
                "/proc/timer_stats", "/proc/sched_debug",
                "/proc/scsi", "/sys/firmware",
            },
            // Read-only paths
            ReadonlyPaths: []string{
                "/proc/asound", "/proc/bus", "/proc/fs",
                "/proc/irq", "/proc/sys", "/proc/sysrq-trigger",
            },
        }
        return nil
    }
}
```

### containerd Snapshotter (OverlayFS Integration)

```go
// github.com/containerd/containerd/snapshots/overlay/overlay.go
// Snapshotter manages the OverlayFS layer stack

type snapshotter struct {
    root string  // /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs
    ms   *storage.MetaStore
    upperdirLabel bool
    indexOff      bool
    userxattr      bool
    ms             *storage.MetaStore
}

// Prepare: create a writable snapshot (for container RW layer)
func (o *snapshotter) Prepare(ctx context.Context, key, parent string,
    opts ...snapshots.Opt) ([]mount.Mount, error) {
    
    // Get all parents (lower layers) from metadata store
    // Build lowerdir=L1:L2:L3 string for mount options
    
    id, info, err := storage.CreateSnapshot(ctx, snapshots.KindActive, key, parent, opts...)
    
    // Determine layer paths
    snapshotDir := filepath.Join(o.root, "snapshots", id)
    
    return o.mounts(snapshotDir, id, info.Parent), nil
}

func (o *snapshotter) mounts(dir string, id string, parent string) []mount.Mount {
    var options []string
    
    // Build lowerdir from parent chain
    if parent != "" {
        lowers := o.parentIDsToSnapshotDirs(parent)
        options = append(options, "lowerdir="+strings.Join(lowers, ":"))
    }
    options = append(options,
        "upperdir="+filepath.Join(dir, "fs"),
        "workdir="+filepath.Join(dir, "work"),
    )
    
    return []mount.Mount{{
        Source:  "overlay",
        Type:    "overlay",
        Options: options,
    }}
}
```

### netlink: Creating veth Pairs in Go

```go
// github.com/vishvananda/netlink — used by Docker's libnetwork

package main

import (
    "fmt"
    "net"
    "os"
    "runtime"

    "github.com/vishvananda/netlink"
    "github.com/vishvananda/netns"
)

func setupContainerNetworking(containerPID int, containerIP string) error {
    hostVethName := fmt.Sprintf("veth%d", containerPID)
    containerVethName := "eth0"

    // Create veth pair in host namespace
    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{
            Name: hostVethName,
            MTU:  1500,
        },
        PeerName: containerVethName,
    }

    if err := netlink.LinkAdd(veth); err != nil {
        return fmt.Errorf("creating veth pair: %w", err)
    }

    // Get bridge (docker0)
    bridge, err := netlink.LinkByName("docker0")
    if err != nil {
        return fmt.Errorf("getting bridge: %w", err)
    }

    // Add host veth to bridge
    hostVeth, err := netlink.LinkByName(hostVethName)
    if err != nil {
        return fmt.Errorf("getting host veth: %w", err)
    }

    if err := netlink.LinkSetMaster(hostVeth, bridge); err != nil {
        return fmt.Errorf("setting master: %w", err)
    }

    if err := netlink.LinkSetUp(hostVeth); err != nil {
        return fmt.Errorf("bringing up host veth: %w", err)
    }

    // Move container veth to container network namespace
    containerNs, err := netns.GetFromPid(containerPID)
    if err != nil {
        return fmt.Errorf("getting container ns: %w", err)
    }
    defer containerNs.Close()

    containerVeth, err := netlink.LinkByName(containerVethName)
    if err != nil {
        return fmt.Errorf("getting container veth: %w", err)
    }

    if err := netlink.LinkSetNsFd(containerVeth, int(containerNs)); err != nil {
        return fmt.Errorf("moving veth to container ns: %w", err)
    }

    // Configure IP inside container namespace
    // Must run in container's net namespace
    runtime.LockOSThread()
    defer runtime.UnlockOSThread()

    origNs, _ := netns.Get()
    defer origNs.Close()

    if err := netns.Set(containerNs); err != nil {
        return fmt.Errorf("entering container ns: %w", err)
    }
    defer netns.Set(origNs)

    // Inside container ns:
    link, err := netlink.LinkByName(containerVethName)
    if err != nil {
        return fmt.Errorf("finding eth0 in container ns: %w", err)
    }

    ip, ipNet, _ := net.ParseCIDR(containerIP + "/24")
    ipNet.IP = ip
    addr := &netlink.Addr{IPNet: ipNet}

    if err := netlink.AddrAdd(link, addr); err != nil {
        return fmt.Errorf("adding IP: %w", err)
    }

    if err := netlink.LinkSetUp(link); err != nil {
        return fmt.Errorf("bringing up eth0: %w", err)
    }

    // Add default route via bridge IP
    route := &netlink.Route{
        LinkIndex: link.Attrs().Index,
        Gw:        net.ParseIP("172.17.0.1"),
    }
    if err := netlink.RouteAdd(route); err != nil {
        return fmt.Errorf("adding default route: %w", err)
    }

    return nil
}

func main() {
    if len(os.Args) < 3 {
        fmt.Fprintf(os.Stderr, "Usage: %s <container-pid> <container-ip>\n", os.Args[0])
        os.Exit(1)
    }
    // ... parse args and call setupContainerNetworking
}
```

---

## 17. C Implementation — runc & libcontainer

### Minimal Container Runtime in C

```c
// A minimal container runtime demonstrating the core syscalls Docker uses
// gcc -o miniruntime miniruntime.c -static -Wall -Wextra
// Must run as root (or with user namespace support)

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <linux/sched.h>
#include <linux/limits.h>

#define STACK_SIZE (4 * 1024 * 1024)  // 4MB stack for child
#define ROOTFS     "./rootfs"          // container rootfs directory

struct container_config {
    char *rootfs;
    char *hostname;
    char **argv;
    int   argc;
    uid_t uid;
    gid_t gid;
};

static char container_stack[STACK_SIZE];

// Write uid_map or gid_map for user namespace
static int write_mapping(pid_t pid, const char *map_file,
                          uid_t inside, uid_t outside, unsigned count)
{
    char path[PATH_MAX];
    char mapping[64];
    int fd;

    snprintf(path, sizeof(path), "/proc/%d/%s", pid, map_file);
    snprintf(mapping, sizeof(mapping), "%u %u %u\n", inside, outside, count);

    fd = open(path, O_WRONLY);
    if (fd < 0) { perror("open map"); return -1; }
    if (write(fd, mapping, strlen(mapping)) < 0) {
        perror("write map"); close(fd); return -1;
    }
    close(fd);
    return 0;
}

// Write "deny" to /proc/PID/setgroups (required before gid_map)
static int deny_setgroups(pid_t pid)
{
    char path[PATH_MAX];
    int fd;
    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    fd = open(path, O_WRONLY);
    if (fd < 0) { perror("open setgroups"); return -1; }
    if (write(fd, "deny", 4) < 0) {
        perror("write setgroups"); close(fd); return -1;
    }
    close(fd);
    return 0;
}

// Container init function — runs inside new namespaces
static int container_init(void *arg)
{
    struct container_config *cfg = (struct container_config *)arg;
    
    // 1. Set hostname in new UTS namespace
    if (sethostname(cfg->hostname, strlen(cfg->hostname)) < 0) {
        perror("sethostname"); return 1;
    }
    
    // 2. Setup mounts
    // Make mount namespace private (prevent propagation to host)
    if (mount(NULL, "/", NULL, MS_PRIVATE | MS_REC, NULL) < 0) {
        perror("make private"); return 1;
    }
    
    // Bind mount the rootfs to itself (required for pivot_root)
    if (mount(cfg->rootfs, cfg->rootfs, NULL, MS_BIND | MS_REC, NULL) < 0) {
        perror("bind rootfs"); return 1;
    }
    
    // Create .pivot_old inside rootfs for old root
    char pivot_old[PATH_MAX];
    snprintf(pivot_old, sizeof(pivot_old), "%s/.pivot_old", cfg->rootfs);
    if (mkdir(pivot_old, 0700) < 0 && errno != EEXIST) {
        perror("mkdir pivot_old"); return 1;
    }
    
    // pivot_root: new_root = rootfs, put_old = rootfs/.pivot_old
    if (syscall(SYS_pivot_root, cfg->rootfs, pivot_old) < 0) {
        perror("pivot_root"); return 1;
    }
    
    // chdir to new root
    if (chdir("/") < 0) { perror("chdir /"); return 1; }
    
    // Unmount old root
    if (umount2("/.pivot_old", MNT_DETACH) < 0) {
        perror("umount old root"); return 1;
    }
    if (rmdir("/.pivot_old") < 0) {
        perror("rmdir .pivot_old"); /* non-fatal */
    }
    
    // 3. Mount essential filesystems
    // proc
    mkdir("/proc", 0755);
    if (mount("proc", "/proc", "proc",
              MS_NODEV | MS_NOEXEC | MS_NOSUID, NULL) < 0) {
        perror("mount proc"); return 1;
    }
    
    // tmpfs for /dev
    mkdir("/dev", 0755);
    if (mount("tmpfs", "/dev", "tmpfs",
              MS_NOSUID | MS_STRICTATIME,
              "mode=755,size=65536k") < 0) {
        perror("mount dev tmpfs"); return 1;
    }
    
    // Create standard device nodes
    mknod("/dev/null",    S_IFCHR | 0666, makedev(1, 3));
    mknod("/dev/zero",    S_IFCHR | 0666, makedev(1, 5));
    mknod("/dev/random",  S_IFCHR | 0444, makedev(1, 8));
    mknod("/dev/urandom", S_IFCHR | 0444, makedev(1, 9));
    mknod("/dev/tty",     S_IFCHR | 0666, makedev(5, 0));
    
    // 4. Drop capabilities (simplified — just set no_new_privs)
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("no_new_privs"); return 1;
    }
    
    // 5. Set UID/GID
    if (cfg->gid != 0 && setgid(cfg->gid) < 0) {
        perror("setgid"); return 1;
    }
    if (cfg->uid != 0 && setuid(cfg->uid) < 0) {
        perror("setuid"); return 1;
    }
    
    // 6. Execute container process
    execvp(cfg->argv[0], cfg->argv);
    perror("execvp");
    return 1;
}

int main(int argc, char *argv[])
{
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <rootfs> <cmd> [args...]\n", argv[0]);
        return 1;
    }

    struct container_config cfg = {
        .rootfs   = argv[1],
        .hostname = "container",
        .argv     = &argv[2],
        .argc     = argc - 2,
        .uid      = 0,
        .gid      = 0,
    };

    // Namespace flags — mirrors Docker's default set
    int clone_flags =
        CLONE_NEWPID |     // New PID namespace
        CLONE_NEWNS  |     // New mount namespace
        CLONE_NEWUTS |     // New hostname
        CLONE_NEWIPC |     // New IPC
        CLONE_NEWNET |     // New network
        // CLONE_NEWUSER | // User ns (uncomment for rootless)
        SIGCHLD;           // Signal parent on exit

    printf("[host] Launching container in rootfs: %s\n", cfg.rootfs);
    printf("[host] Command: %s\n", cfg.argv[0]);

    pid_t container_pid = clone(container_init, 
                                container_stack + STACK_SIZE,
                                clone_flags,
                                &cfg);
    if (container_pid < 0) {
        perror("clone");
        return 1;
    }

    printf("[host] Container PID (host view): %d\n", container_pid);

    // For rootless (CLONE_NEWUSER): write UID/GID mappings here
    // deny_setgroups(container_pid);
    // write_mapping(container_pid, "uid_map", 0, getuid(), 1);
    // write_mapping(container_pid, "gid_map", 0, getgid(), 1);

    // Wait for container to exit
    int wstatus;
    if (waitpid(container_pid, &wstatus, 0) < 0) {
        perror("waitpid");
        return 1;
    }

    if (WIFEXITED(wstatus)) {
        printf("[host] Container exited with status %d\n", WEXITSTATUS(wstatus));
        return WEXITSTATUS(wstatus);
    }
    if (WIFSIGNALED(wstatus)) {
        printf("[host] Container killed by signal %d\n", WTERMSIG(wstatus));
        return 128 + WTERMSIG(wstatus);
    }
    return 1;
}
```

---

## 18. Rust Implementation — youki container runtime

youki is an OCI-compliant container runtime written in Rust, usable as a drop-in replacement for runc.

```rust
// Demonstrates the core namespace + cgroup setup in Rust
// Cargo.toml deps: nix, oci-spec-rs, cgroups-rs, caps

use std::path::Path;
use std::fs::{self, File};
use std::io::Write;
use std::os::unix::io::RawFd;

use nix::sched::{clone, CloneFlags};
use nix::sys::wait::{waitpid, WaitStatus};
use nix::unistd::{
    chdir, execvp, fork, getpid, pivot_root, sethostname,
    Pid, ForkResult,
};
use nix::mount::{mount, MntFlags, MsFlags};

/// Namespace flags for a standard container
/// mirrors CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWNET
const CONTAINER_CLONE_FLAGS: CloneFlags = CloneFlags::from_bits_truncate(
    CloneFlags::CLONE_NEWPID.bits()
    | CloneFlags::CLONE_NEWNS.bits()
    | CloneFlags::CLONE_NEWUTS.bits()
    | CloneFlags::CLONE_NEWIPC.bits()
    | CloneFlags::CLONE_NEWNET.bits()
);

/// Container configuration — maps to OCI spec subset
#[derive(Debug, Clone)]
pub struct ContainerConfig {
    pub rootfs:   std::path::PathBuf,
    pub hostname: String,
    pub command:  Vec<String>,
    pub uid:      u32,
    pub gid:      u32,
    pub mem_limit: Option<u64>,   // bytes
    pub cpu_quota: Option<i64>,   // microseconds per 100ms period
}

/// Setup cgroup v2 limits
/// Writes to /sys/fs/cgroup/system.slice/<scope>/
fn setup_cgroups(scope: &str, cfg: &ContainerConfig) -> Result<(), Box<dyn std::error::Error>> {
    let cgroup_path = Path::new("/sys/fs/cgroup/system.slice").join(scope);
    fs::create_dir_all(&cgroup_path)?;

    // Enable controllers in parent
    let parent = Path::new("/sys/fs/cgroup/system.slice/cgroup.subtree_control");
    fs::write(parent, "+memory +cpu +pids")?;

    // Set memory limit
    if let Some(limit) = cfg.mem_limit {
        let mem_max = cgroup_path.join("memory.max");
        fs::write(&mem_max, limit.to_string())?;
        println!("  memory.max = {} bytes", limit);
    }

    // Set CPU bandwidth
    if let Some(quota) = cfg.cpu_quota {
        let cpu_max = cgroup_path.join("cpu.max");
        fs::write(&cpu_max, format!("{} 100000", quota))?;
        println!("  cpu.max = {} 100000", quota);
    }

    // Add current process to cgroup
    let procs_file = cgroup_path.join("cgroup.procs");
    let pid = std::process::id();
    fs::write(&procs_file, pid.to_string())?;
    println!("  Added PID {} to cgroup", pid);

    Ok(())
}

/// Setup mounts inside container
fn setup_mounts(rootfs: &Path) -> Result<(), Box<dyn std::error::Error>> {
    // Make root mount private
    mount(
        None::<&str>, "/",
        None::<&str>,
        MsFlags::MS_PRIVATE | MsFlags::MS_REC,
        None::<&str>,
    )?;

    // Bind mount rootfs to itself (pivot_root requirement)
    mount(
        Some(rootfs), rootfs,
        None::<&str>,
        MsFlags::MS_BIND | MsFlags::MS_REC,
        None::<&str>,
    )?;

    // Create .pivot_old directory
    let pivot_old = rootfs.join(".pivot_old");
    fs::create_dir_all(&pivot_old)?;

    // pivot_root
    pivot_root(rootfs, &pivot_old)?;
    chdir("/")?;

    // Unmount old root
    nix::mount::umount2("/.pivot_old", MntFlags::MNT_DETACH)?;
    fs::remove_dir("/.pivot_old").ok(); // non-fatal

    // Mount /proc
    fs::create_dir_all("/proc")?;
    mount(
        Some("proc"), "/proc",
        Some("proc"),
        MsFlags::MS_NODEV | MsFlags::MS_NOEXEC | MsFlags::MS_NOSUID,
        None::<&str>,
    )?;

    // Mount /dev as tmpfs
    fs::create_dir_all("/dev")?;
    mount(
        Some("tmpfs"), "/dev",
        Some("tmpfs"),
        MsFlags::MS_NOSUID | MsFlags::MS_STRICTATIME,
        Some("mode=755,size=65536k"),
    )?;

    Ok(())
}

/// Drop capabilities — youki's approach using caps crate  
fn setup_capabilities() -> Result<(), Box<dyn std::error::Error>> {
    use caps::{CapSet, Capability, CapsHashSet};

    // Docker's default cap set
    let docker_caps: CapsHashSet = [
        Capability::CAP_CHOWN,
        Capability::CAP_DAC_OVERRIDE,
        Capability::CAP_FSETID,
        Capability::CAP_FOWNER,
        Capability::CAP_MKNOD,
        Capability::CAP_NET_RAW,
        Capability::CAP_SETGID,
        Capability::CAP_SETUID,
        Capability::CAP_SETFCAP,
        Capability::CAP_SETPCAP,
        Capability::CAP_NET_BIND_SERVICE,
        Capability::CAP_SYS_CHROOT,
        Capability::CAP_KILL,
        Capability::CAP_AUDIT_WRITE,
    ].iter().cloned().collect();

    // Set all four cap sets to docker defaults
    caps::set(None, CapSet::Bounding,     &docker_caps)?;
    caps::set(None, CapSet::Permitted,    &docker_caps)?;
    caps::set(None, CapSet::Effective,    &docker_caps)?;
    caps::set(None, CapSet::Inheritable,  &docker_caps)?;

    // Set no_new_privs
    unsafe {
        libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    }

    Ok(())
}

/// The container init function — runs inside new namespaces
fn container_init(cfg: ContainerConfig) -> Result<(), Box<dyn std::error::Error>> {
    // Step 1: Set hostname in UTS namespace
    sethostname(cfg.hostname.as_bytes())?;
    println!("[container] hostname: {}", cfg.hostname);

    // Step 2: Setup cgroups (while still root, before dropping privs)
    let scope = format!("miniruntime-{}.scope", std::process::id());
    setup_cgroups(&scope, &cfg)?;

    // Step 3: Setup filesystem
    setup_mounts(&cfg.rootfs)?;

    // Step 4: Setup capabilities
    setup_capabilities()?;

    // Step 5: Execute container command
    println!("[container] PID: {} (should be 1 for first process)", 
             getpid());
    println!("[container] Executing: {:?}", cfg.command);

    let cmd = std::ffi::CString::new(cfg.command[0].clone())?;
    let args: Vec<std::ffi::CString> = cfg.command
        .iter()
        .map(|s| std::ffi::CString::new(s.as_str()).unwrap())
        .collect();

    execvp(&cmd, &args)?;
    unreachable!("execvp returned");
}

pub fn run_container(cfg: ContainerConfig) -> Result<i32, Box<dyn std::error::Error>> {
    println!("[host] Starting container");
    println!("[host] Rootfs: {:?}", cfg.rootfs);
    println!("[host] Command: {:?}", cfg.command);

    // Allocate stack for child process
    let mut stack = vec![0u8; 4 * 1024 * 1024];
    let cfg_clone = cfg.clone();

    // clone() with namespace flags
    let child_pid = unsafe {
        clone(
            Box::new(move || {
                container_init(cfg_clone)
                    .map(|_| 0)
                    .unwrap_or_else(|e| {
                        eprintln!("Container init error: {}", e);
                        1
                    })
            }),
            stack.as_mut_slice(),
            CONTAINER_CLONE_FLAGS,
            Some(libc::SIGCHLD),
        )?
    };

    println!("[host] Container PID (host view): {}", child_pid);

    // Wait for container to exit
    match waitpid(child_pid, None)? {
        WaitStatus::Exited(_, code) => {
            println!("[host] Container exited with code {}", code);
            Ok(code)
        }
        WaitStatus::Signaled(_, sig, _) => {
            println!("[host] Container killed by signal {:?}", sig);
            Ok(128 + sig as i32)
        }
        other => {
            eprintln!("[host] Unexpected wait status: {:?}", other);
            Ok(1)
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <rootfs> <cmd> [args...]", args[0]);
        std::process::exit(1);
    }

    let cfg = ContainerConfig {
        rootfs:    Path::new(&args[1]).to_path_buf(),
        hostname:  "container".to_string(),
        command:   args[2..].to_vec(),
        uid:       0,
        gid:       0,
        mem_limit: Some(512 * 1024 * 1024),  // 512MB
        cpu_quota: Some(50000),               // 50% CPU
    };

    match run_container(cfg) {
        Ok(code) => std::process::exit(code),
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    }
}
```

---

## 19. eBPF for Container Observability

### bpftrace: Trace Container Syscalls

```bash
#!/usr/bin/env bpftrace
// Trace all syscalls made by processes in a specific container
// Usage: bpftrace container_syscalls.bt <container-pid>

// First get container PID namespace inode
// CONTAINER_PID_NS=$(stat -Lc %i /proc/<container-pid>/ns/pid)

BEGIN {
    printf("Tracing container syscalls. Ctrl+C to stop.\n");
    printf("%-20s %-8s %-8s %s\n", "COMM", "PID", "SYSCALL", "RETURN");
}

// Hook on raw syscall entry
// Filter by matching PID namespace inode to isolate container
tracepoint:raw_syscalls:sys_enter {
    // Check if this process is in our target container
    // by comparing /proc/self/ns/pid inode
    $ns_inum = ((struct task_struct *)curtask)->nsproxy->pid_ns_for_children->ns.inum;
    
    // Replace 4026532XXX with actual namespace inode
    if ($ns_inum == $1) {
        printf("%-20s %-8d %-8d\n", comm, pid, args->id);
    }
}

tracepoint:raw_syscalls:sys_exit {
    $ns_inum = ((struct task_struct *)curtask)->nsproxy->pid_ns_for_children->ns.inum;
    if ($ns_inum == $1 && args->ret < 0) {
        printf("  FAILED: syscall=%d ret=%d\n", args->id, args->ret);
    }
}
```

### eBPF: Monitor Container OOM Events

```c
// ebpf_oom_monitor.bpf.c
// Attach to oom_kill_process to detect container OOM kills

#include <linux/bpf.h>
#include <linux/sched.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct oom_event {
    __u32 pid;
    __u32 tgid;
    __u64 mem_used;
    char  comm[16];
    char  cgroup_name[64];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(int));
} oom_events SEC(".maps");

// Attach to oom_kill_process in mm/oom_kill.c
SEC("kprobe/oom_kill_process")
int BPF_KPROBE(trace_oom_kill, struct oom_control *oc,
               const char *message)
{
    struct oom_event event = {};
    struct task_struct *task;
    
    // Get victim task
    task = (struct task_struct *)BPF_CORE_READ(oc, chosen);
    if (!task)
        return 0;
    
    event.pid  = BPF_CORE_READ(task, pid);
    event.tgid = BPF_CORE_READ(task, tgid);
    bpf_probe_read_kernel_str(&event.comm, sizeof(event.comm),
                              BPF_CORE_READ(task, comm));
    
    // Read cgroup name for container identification
    struct css_set *cgroups = BPF_CORE_READ(task, cgroups);
    struct cgroup *cgrp = BPF_CORE_READ(cgroups, dfl_cgrp);
    struct kernfs_node *kn = BPF_CORE_READ(cgrp, kn);
    bpf_probe_read_kernel_str(&event.cgroup_name, sizeof(event.cgroup_name),
                              BPF_CORE_READ(kn, name));
    
    // Get memory usage
    struct mm_struct *mm = BPF_CORE_READ(task, mm);
    if (mm) {
        event.mem_used = BPF_CORE_READ(mm, total_vm) * 4096; // approximate
    }
    
    bpf_perf_event_output(ctx, &oom_events, BPF_F_CURRENT_CPU,
                          &event, sizeof(event));
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### bpftrace: Container Network I/O

```bash
# Monitor container network traffic volume
# Attaches to kernel's tcp_sendmsg and tcp_recvmsg

bpftrace -e '
kprobe:tcp_sendmsg {
    $task = (struct task_struct *)curtask;
    $ns_inum = $task->nsproxy->net_ns->ns.inum;
    @send_by_ns[$ns_inum] = sum(arg2);  // arg2 = size
}
kprobe:tcp_recvmsg {
    $task = (struct task_struct *)curtask;
    $ns_inum = $task->nsproxy->net_ns->ns.inum;
    @recv_by_ns[$ns_inum] = sum(arg2);
}
interval:s:5 {
    print(@send_by_ns);
    print(@recv_by_ns);
    clear(@send_by_ns);
    clear(@recv_by_ns);
}'
```

---

## 20. Kernel Tracing — ftrace, perf for container debugging

### ftrace: Trace namespace clone events

```bash
# Trace clone() calls with CLONE_NEWPID (new PID namespace creation)
# = detecting new container starts

echo 1 > /sys/kernel/debug/tracing/events/syscalls/sys_enter_clone/enable
echo 'clone_flags & 0x20000000' > \
    /sys/kernel/debug/tracing/events/syscalls/sys_enter_clone/filter
cat /sys/kernel/debug/tracing/trace

# Trace OverlayFS copy-up events (file modification in container)
echo 1 > /sys/kernel/debug/tracing/events/overlay/oevent/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

### perf: Container CPU profiling

```bash
# Profile all processes in a container's cgroup
CGROUP_PATH="/sys/fs/cgroup/system.slice/docker-$(docker inspect --format '{{.Id}}' <name>).scope"

# Record for 10 seconds
perf record -g --cgroup="$CGROUP_PATH" -o container.perf sleep 10

# Generate flamegraph
perf script -i container.perf | stackcollapse-perf.pl | flamegraph.pl > flame.svg

# Per-container CPU time accounting
perf stat --cgroup="$CGROUP_PATH" sleep 10
```

### ftrace: function graph tracing for container syscalls

```bash
# Trace all kernel functions called from a specific container PID
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' <container>)

cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo $CONTAINER_PID > set_ftrace_pid
echo 1 > tracing_on

# Let it run...
sleep 2
echo 0 > tracing_on

# The output shows full kernel call graph for the container
head -100 trace
```

---

## 21. rootless Containers — user namespaces deep dive

Rootless containers run without any root privileges on the host, using user namespaces to map container UID 0 to a non-root host UID.

```
Host UID: 1000 (regular user)
         |
         | clone(CLONE_NEWUSER | CLONE_NEWPID | ...)
         v
User namespace
  container UID 0  <-> host UID 1000  (via uid_map: "0 1000 1")
  container UID 1  <-> host UID 100001 (via uid_map: "1 100001 65535")
  
/etc/subuid: username:100001:65535
/etc/subgid: username:100001:65535

uid_map format: <inside-uid> <outside-uid> <count>
e.g., "0 1000 1\n1 100001 65535"
  -> uid 0 in container maps to uid 1000 on host
  -> uids 1-65535 in container map to 100001-165535 on host
```

```c
// kernel/user_namespace.c
// The uid_map/gid_map write triggers:
// proc_uid_map_write() -> map_write() -> new_idmap_permitted()

struct uid_gid_map {
    u32 nr_extents;        // number of mappings
    union {
        struct uid_gid_extent {
            u32 first;     // first UID in child namespace
            u32 lower_first; // first UID in parent namespace
            u32 count;     // number of UIDs in range
        } extent[UID_GID_MAP_MAX_BASE_EXTENTS];
        struct {
            struct uid_gid_extent *forward;  // sorted by child UID
            struct uid_gid_extent *reverse;  // sorted by parent UID
        };
    };
};

// Capability check for user namespace operations:
// Even though container thinks it's root (UID 0),
// the REAL check is against host UID 1000 in this case.
// Most sensitive operations require the mapping to exist
// AND the host UID to have the relevant real capability.

// For example: mounting filesystems inside user namespace:
// - requires CLONE_NEWNS inside CLONE_NEWUSER
// - the mount is permitted because user owns the namespace
// - but the underlying filesystem must be safe (no suid binaries etc.)
```

### Shell: rootless container with slirp4netns

```bash
#!/bin/bash
# Demonstrates rootless container networking setup
# Similar to what podman (rootless) does

# Step 1: Create user namespace + other namespaces
unshare --user --pid --mount --net --uts --ipc --fork \
    --map-root-user bash << 'CONTAINER_INIT'

# Inside the new namespaces, we appear as root
echo "Container UID: $(id)"       # uid=0(root) gid=0(root)
echo "Container PID: $$"          # 1

# Mount proc for our PID namespace
mount -t proc proc /proc

# Set hostname  
hostname container-rootless

# Network: lo only by default (no real network)
ip link set lo up

# For real networking, slirp4netns runs outside and provides
# a tap device into this network namespace via a socket pair

CONTAINER_INIT

# Step 2: Outside the container, slirp4netns provides user-space NAT:
# slirp4netns --configure --mtu=65520 --disable-host-loopback \
#     $CONTAINER_PID eth0
```

---

## 22. OCI Runtime Specification & Kernel Interface

The OCI Runtime Spec defines the **complete kernel interface** a container runtime must configure:

```
OCI Spec Lifecycle:
  
create  -> setup namespaces, mounts, cgroups, seccomp
           container process is paused (waiting for start)
           
start   -> exec the container process
           (send SIGCONT to the waiting runc init)
           
state   -> return current container state as JSON
           (running, created, stopped)
           
kill    -> send signal to container init process
           (SIGTERM for graceful, SIGKILL for force)
           
delete  -> cleanup: umount overlayfs, remove cgroup,
           delete namespaces (by closing all references)
```

### Complete syscall sequence for docker run

```
# Syscalls made during: docker run --rm ubuntu echo hello

1. socket(AF_UNIX, SOCK_STREAM, 0)           # open dockerd socket
2. connect(3, {sa_family=AF_UNIX, sun_path="/var/run/docker.sock"})
3. sendto(3, "POST /containers/create ...")  # create container

# dockerd -> containerd (gRPC)
4. socket(AF_UNIX, SOCK_STREAM, 0)
5. connect(4, {sun_path="/run/containerd/containerd.sock"})

# containerd -> runc (fork+exec)
6. clone(CLONE_VM|CLONE_VFORK|SIGCHLD)       # Go runtime fork
7. execve("/usr/bin/runc", ["runc", "create",...])

# runc nsexec (C constructor, before Go runtime):
8. clone(CLONE_NEWPID|CLONE_NEWNS|CLONE_NEWNET|
         CLONE_NEWUTS|CLONE_NEWIPC|SIGCHLD)   # create namespaces

# Inside child (container setup):
9.  mount("none", "/", NULL, MS_PRIVATE|MS_REC)  # private mounts
10. mount(rootfs, rootfs, NULL, MS_BIND|MS_REC)  # bind rootfs
11. syscall(SYS_pivot_root, rootfs, pivot_old)   # pivot
12. mount("proc", "/proc", "proc", ...)          # mount /proc
13. mount("tmpfs", "/dev", "tmpfs", ...)         # mount /dev
14. mknod("/dev/null", S_IFCHR, makedev(1,3))    # device nodes
15. prctl(PR_SET_NO_NEW_PRIVS, 1)                # security
16. prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER)   # seccomp
17. capset(...)                                  # drop capabilities
18. write(cgroup_procs_fd, pid)                  # join cgroup
19. execve("/bin/echo", ["echo", "hello"])        # exec!

# echo runs, prints "hello", exits

# Cleanup:
20. wait4(container_pid, ...)                    # reap
21. unshare(0)  (namespaces cleaned up automatically)
22. rmdir(cgroup_path)                           # remove cgroup
23. umount2(overlay_merged, MNT_DETACH)          # unmount overlay
```

---

## Quick Reference: Kernel Source Paths

| Feature | Kernel Source File |
|---|---|
| `clone(2)` syscall | `kernel/fork.c` |
| `pivot_root(2)` | `fs/namespace.c` |
| Namespace proxy | `kernel/nsproxy.c` |
| PID namespace | `kernel/pid_namespace.c` |
| Network namespace | `net/core/net_namespace.c` |
| Mount namespace | `fs/namespace.c` |
| User namespace | `kernel/user_namespace.c` |
| cgroup v2 core | `kernel/cgroup/cgroup.c` |
| Memory controller | `mm/memcontrol.c` |
| CPU scheduler (cfs) | `kernel/sched/fair.c` |
| OverlayFS | `fs/overlayfs/` |
| OverlayFS copy-up | `fs/overlayfs/copy_up.c` |
| seccomp BPF | `kernel/seccomp.c` |
| Capabilities | `kernel/capability.c` |
| veth driver | `drivers/net/veth.c` |
| Linux bridge | `net/bridge/br_main.c` |
| netfilter core | `net/netfilter/core.c` |
| iptables | `net/netfilter/x_tables.c` |
| AppArmor LSM | `security/apparmor/lsm.c` |
| SELinux LSM | `security/selinux/hooks.c` |
| OOM killer | `mm/oom_kill.c` |
| Hugepages | `mm/hugetlb.c` |
| cgroup devices BPF | `kernel/cgroup/cgroup.c` |
| task_struct | `include/linux/sched.h` |
| cred (capabilities) | `include/linux/cred.h` |
| net struct | `include/net/net_namespace.h` |
| seccomp filter | `include/linux/seccomp.h` |
| cgroup defs | `include/linux/cgroup-defs.h` |

## Key Kernel Configuration Options

```bash
# Essential kernel configs for container support
# Check your kernel: zcat /proc/config.gz | grep -E 'NAMESPACE|CGROUP|OVERLAY'

CONFIG_NAMESPACES=y
CONFIG_UTS_NS=y
CONFIG_IPC_NS=y
CONFIG_PID_NS=y
CONFIG_NET_NS=y
CONFIG_USER_NS=y        # rootless containers
CONFIG_CGROUPS=y
CONFIG_CGROUP_V2=y      # required for cgroup v2
CONFIG_MEMCG=y
CONFIG_MEMCG_SWAP=y
CONFIG_BLK_CGROUP=y
CONFIG_CGROUP_SCHED=y
CONFIG_CFS_BANDWIDTH=y
CONFIG_CGROUP_PIDS=y
CONFIG_CGROUP_HUGETLB=y
CONFIG_CGROUP_NET_PRIO=y
CONFIG_CGROUP_DEVICE=y
CONFIG_OVERLAY_FS=y
CONFIG_SECCOMP=y
CONFIG_SECCOMP_FILTER=y
CONFIG_SECURITY_APPARMOR=y
CONFIG_SECURITY_SELINUX=y
CONFIG_VETH=y           # or =m
CONFIG_BRIDGE=y         # or =m
CONFIG_NETFILTER=y
CONFIG_NF_CONNTRACK=y
CONFIG_NF_NAT=y
CONFIG_IP_NF_IPTABLES=y
CONFIG_IP_NF_NAT=y
CONFIG_IP_NF_FILTER=y
CONFIG_BPF_SYSCALL=y    # eBPF
CONFIG_BPF_JIT=y
CONFIG_CGROUP_BPF=y     # cgroup BPF programs (device filter, net)
CONFIG_HUGETLBFS=y
CONFIG_TMPFS=y
CONFIG_DEVPTS_FS=y
CONFIG_EXPERT=y
CONFIG_MULTIUSER=y
```

---

## References

- `Documentation/admin-guide/cgroup-v2.rst` — cgroup v2 interface spec
- `Documentation/filesystems/overlayfs.rst` — OverlayFS guide  
- `Documentation/userspace-api/seccomp_filter.rst` — seccomp BPF interface
- `Documentation/security/apparmor.rst` — AppArmor integration
- `Documentation/networking/vxlan.rst` — container overlay networking
- `Documentation/bpf/` — BPF subsystem docs
- LWN: "Namespaces in operation" series (lwn.net/Articles/531114)
- LWN: "Control groups, part 1-7" series
- opencontainers/runc — `libcontainer/` for reference implementation
- containerd/containerd — `snapshots/overlay/` for snapshotting
- youki-dev/youki — Rust OCI runtime reference
- kernel.org/doc/html/latest/filesystems/overlayfs.html

Now let me write the comprehensive guide as a `.md` file:Here's what the guide covers across **22 chapters**:

**Core Isolation (Chapters 2–5)**
The deepest section. Covers every namespace type with `nsproxy`, `pid_namespace`, and `net` struct layouts from `include/linux/nsproxy.h` and `net/core/net_namespace.c`. Shows the exact `clone(2)` → `copy_process()` → `copy_namespaces()` call chain. Includes runc's **nsexec C constructor trick** — the reason runc forks from C before Go's runtime spawns threads (since namespaces are per-thread and Go starts multiple threads early).

**Security Stack (Chapters 6–8)**
Full capability model from `kernel/capability.c`, seccomp BPF program construction at the `sock_filter` instruction level, and AppArmor LSM hook registration (`~60 hooks` shown). The C seccomp demo shows what `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER)` looks like with raw BPF instructions — exactly what runc generates via libseccomp.

**Networking (Chapters 9–10)**
`veth_xmit()` from `drivers/net/veth.c`, bridge forwarding from `net/bridge/br_input.c`, full iptables DOCKER chain, and a tc BPF program that does per-container egress filtering the way Cilium does it — bypassing netfilter entirely.

**Implementations**
- **Go**: containerd gRPC task creation + overlay snapshotter + netlink veth setup (what libnetwork actually does)
- **C**: A working minimal container runtime (~300 LOC) doing `clone()` → `pivot_root()` → capability drop → `execve()` — the entire Docker flow in one file
- **Rust**: youki-style runtime with `nix` crate doing namespaces, cgroups v2 writes, and caps management

**Tracing (Chapters 19–20)**
`bpftrace` scripts that filter by PID namespace inode (so you only trace one container), an eBPF OOM monitor attached to `kprobe/oom_kill_process` that reads cgroup name from `task_struct`, and ftrace/perf cgroup-scoped profiling commands.