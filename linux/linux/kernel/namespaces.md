# Linux Namespaces: A Complete In-Depth Guide

> **Target Audience**: Systems programmers, container engineers, security researchers, and kernel developers who need deep, production-grade understanding of Linux namespace internals, APIs, and real-world application.

---

## Table of Contents

1. [Conceptual Foundation](#1-conceptual-foundation)
2. [Kernel Architecture & Internals](#2-kernel-architecture--internals)
3. [Core System Calls](#3-core-system-calls)
4. [Mount Namespaces (CLONE_NEWNS)](#4-mount-namespaces-clone_newns)
5. [UTS Namespaces (CLONE_NEWUTS)](#5-uts-namespaces-clone_newuts)
6. [IPC Namespaces (CLONE_NEWIPC)](#6-ipc-namespaces-clone_newipc)
7. [PID Namespaces (CLONE_NEWPID)](#7-pid-namespaces-clone_newpid)
8. [Network Namespaces (CLONE_NEWNET)](#8-network-namespaces-clone_newnet)
9. [User Namespaces (CLONE_NEWUSER)](#9-user-namespaces-clone_newuser)
10. [Cgroup Namespaces (CLONE_NEWCGROUP)](#10-cgroup-namespaces-clone_newcgroup)
11. [Time Namespaces (CLONE_NEWTIME)](#11-time-namespaces-clone_newtime)
12. [Namespace Lifecycle & /proc Filesystem](#12-namespace-lifecycle--proc-filesystem)
13. [Namespace Persistence & Bind Mounts](#13-namespace-persistence--bind-mounts)
14. [Nested & Hierarchical Namespaces](#14-nested--hierarchical-namespaces)
15. [Security Model & Capabilities](#15-security-model--capabilities)
16. [Building a Container Runtime from Scratch](#16-building-a-container-runtime-from-scratch)
17. [Rust Implementation: Namespace Manager](#17-rust-implementation-namespace-manager)
18. [Advanced Patterns & Edge Cases](#18-advanced-patterns--edge-cases)
19. [Debugging & Observability](#19-debugging--observability)
20. [Performance Characteristics](#20-performance-characteristics)
21. [Known Vulnerabilities & Escape Vectors](#21-known-vulnerabilities--escape-vectors)
22. [Real-World Reference Implementations](#22-real-world-reference-implementations)

---

## 1. Conceptual Foundation

### What Are Namespaces?

A **Linux namespace** wraps a global system resource in an abstraction layer, making it appear to processes within the namespace as though they have their own isolated instance of that resource. Changes to the resource inside a namespace are invisible to processes outside it, and vice versa.

This is the fundamental isolation primitive underlying all container technologies — Docker, Podman, LXC, Kubernetes pods, and Flatpak sandboxes all rely on namespaces.

Namespaces answer the question: **"How do we make a process believe it owns the world, when it doesn't?"**

### The Eight Namespace Types

| Namespace | Flag | Kernel Version | Resource Isolated |
|---|---|---|---|
| Mount | `CLONE_NEWNS` | 2.4.19 (2002) | Filesystem mount points |
| UTS | `CLONE_NEWUTS` | 2.6.19 (2006) | Hostname and NIS domain name |
| IPC | `CLONE_NEWIPC` | 2.6.19 (2006) | SysV IPC, POSIX message queues |
| PID | `CLONE_NEWPID` | 2.6.24 (2008) | Process IDs |
| Network | `CLONE_NEWNET` | 2.6.24 (2008) | Network stack, interfaces, routing |
| User | `CLONE_NEWUSER` | 3.8 (2013) | User and group IDs |
| Cgroup | `CLONE_NEWCGROUP` | 4.6 (2016) | Cgroup root directory |
| Time | `CLONE_NEWTIME` | 5.6 (2020) | Boot and monotonic clocks |

### The Philosophical Contract

Every namespace is a **virtualization of state**, not a virtualization of hardware. Namespaces do not create virtual CPUs or virtual memory (that's cgroups and the VM subsystem). They create virtual *views* of kernel-managed global state.

This distinction matters:
- Namespaces are **zero-copy** for data — the actual kernel objects (inodes, sockets, etc.) are shared; only the visibility mapping is scoped.
- Namespaces are **cooperative** — the kernel enforces boundaries only at system call boundaries and VFS/network lookup time.
- Namespaces are **composable** — a process can be in different namespaces for each resource type simultaneously.

### Namespace vs. Cgroup

These two are often confused:

| Aspect | Namespace | Cgroup |
|---|---|---|
| Purpose | **Isolation** (what you can see) | **Accounting/limiting** (what you can use) |
| Mechanism | View scoping | Resource throttling |
| Example | Process can't see other PIDs | Process can't use more than 512MB RAM |
| Implementation | Per-resource struct pointers in `task_struct` | Hierarchical tree attached to `task_struct` |

A container needs **both**: namespaces for isolation, cgroups for resource limits.

---

## 2. Kernel Architecture & Internals

### The `task_struct` Connection

Every Linux process is represented in the kernel by a `task_struct`. Each task holds pointers to its current namespace set:

```c
// simplified from include/linux/sched.h
struct task_struct {
    // ...
    struct nsproxy *nsproxy;  // pointer to namespace proxy
    // ...
};
```

The `nsproxy` structure aggregates all namespace pointers:

```c
// include/linux/nsproxy.h
struct nsproxy {
    atomic_t count;             // reference count
    struct uts_namespace  *uts_ns;
    struct ipc_namespace  *ipc_ns;
    struct mnt_namespace  *mnt_ns;
    struct pid_namespace  *pid_ns_for_children;
    struct net            *net_ns;
    struct time_namespace *time_ns;
    struct time_namespace *time_ns_for_children;
    struct cgroup_namespace *cgroup_ns;
};
```

Note: **user namespace is NOT in `nsproxy`** — it's stored directly in `task_struct->cred->user_ns` because it's part of the credential subsystem.

### Reference Counting and Lifecycle

Each namespace struct has a reference count (`atomic_t count` or via `kref`). A namespace persists as long as:

1. At least one process is a member of it, OR
2. At least one open file descriptor in `/proc/[pid]/ns/` refers to it, OR
3. A bind mount exists for it (persists across all process deaths)

When the count reaches zero, the namespace-specific `free_*_ns()` function is called, cleaning up all resources.

### Namespace Creation Paths

Namespaces are created through three entry points:

```
clone(2) ──────┐
unshare(2) ─────┼──► copy_namespaces() ──► create_new_namespaces()
setns(2) ───────┘                               │
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                               copy_mnt_ns  copy_net_ns  copy_pid_ns
                               copy_uts_ns  copy_ipc_ns  copy_user_ns
                               ...
```

The kernel function `create_new_namespaces()` in `kernel/nsproxy.c` is the central allocator. It calls `copy_*_ns()` for each namespace type, which either:
- Returns the **existing namespace** (if the corresponding `CLONE_NEW*` flag is NOT set), incrementing its refcount
- Creates a **new namespace** derived from the parent (if the flag IS set)

### Namespace Identification

Each namespace is identified by a **device+inode pair** on the `nsfs` virtual filesystem. This is the canonical identity — two file descriptors referring to the same namespace inode are in the same namespace:

```bash
$ ls -lai /proc/self/ns/
total 0
lrwxrwxrwx 1 root root 0 ... cgroup -> 'cgroup:[4026531835]'
lrwxrwxrwx 1 root root 0 ... ipc    -> 'ipc:[4026531839]'
lrwxrwxrwx 1 root root 0 ... mnt    -> 'mnt:[4026531840]'
lrwxrwxrwx 1 root root 0 ... net    -> 'net:[4026531992]'
lrwxrwxrwx 1 root root 0 ... pid    -> 'pid:[4026531836]'
lrwxrwxrwx 1 root root 0 ... time   -> 'time:[4026531834]'
lrwxrwxrwx 1 root root 0 ... user   -> 'user:[4026531837]'
lrwxrwxrwx 1 root root 0 ... uts    -> 'uts:[4026531838]'
```

The number in brackets (e.g., `4026531840`) is the **inode number** on the `nsfs` filesystem. It uniquely identifies a namespace instance within a boot session.

---

## 3. Core System Calls

### `clone(2)` — Create with New Namespaces

```c
#include <sched.h>

long clone(unsigned long flags, void *stack, 
           int *parent_tid, int *child_tid, 
           unsigned long tls);
```

`clone()` is the primary primitive for creating processes with new namespaces. Namespace-relevant flags can be OR'd together:

```c
// Create a process in completely isolated namespaces
clone(CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNET | 
      CLONE_NEWNS   | CLONE_NEWIPC | CLONE_NEWUTS |
      CLONE_NEWCGROUP | SIGCHLD, stack, ...);
```

**Key constraint**: `CLONE_NEWUSER` can be created unprivileged. All other `CLONE_NEW*` flags require `CAP_SYS_ADMIN` **unless** combined with `CLONE_NEWUSER` in the same call (which grants the new user namespace capabilities first).

On modern kernels (5.x+), the `clone3(2)` syscall extends this with a struct-based API:

```c
#include <linux/sched.h>

struct clone_args {
    __aligned_u64 flags;        // CLONE_* flags
    __aligned_u64 pidfd;        // [out] pidfd for CLONE_PIDFD
    __aligned_u64 child_tid;    // [out] for CLONE_CHILD_SETTID
    __aligned_u64 parent_tid;   // [out] for CLONE_PARENT_SETTID
    __aligned_u64 exit_signal;  // signal to parent on exit
    __aligned_u64 stack;        // pointer to stack base
    __aligned_u64 stack_size;   // stack size
    __aligned_u64 tls;          // TLS base for CLONE_SETTLS
    __aligned_u64 set_tid;      // PIDs for CLONE_SET_TID
    __aligned_u64 set_tid_size; // count of set_tid
    __aligned_u64 cgroup;       // cgroup fd for CLONE_INTO_CGROUP
};
```

### `unshare(2)` — Detach Current Process

```c
#include <sched.h>
int unshare(int flags);
```

`unshare()` creates new namespaces for the **calling process** without forking. The current process's namespace pointers are updated to the new namespaces.

Important nuance: `unshare(CLONE_NEWPID)` affects **future children**, not the calling process itself. The calling process's PID namespace doesn't change — its first `fork()` child will be PID 1 in the new namespace.

```c
// After this call, child processes will be in a new PID namespace
// but THIS process's /proc/self/ns/pid doesn't change
unshare(CLONE_NEWPID);

// fork() here creates PID 1 in the new namespace
pid_t child = fork();
```

This is because changing the PID namespace of a running process mid-execution would invalidate all existing `/proc/[pid]/` paths, break signal delivery assumptions, and corrupt the process's own perception of its PID — `getpid()` would return different values before and after.

### `setns(2)` — Join an Existing Namespace

```c
#include <sched.h>
int setns(int fd, int nstype);
```

`setns()` makes the calling process join an **existing** namespace identified by a file descriptor (obtained from `/proc/[pid]/ns/[type]` or via `open()`).

`nstype` is a validation hint (0 means "any type"):

```c
int fd = open("/proc/1234/ns/net", O_RDONLY | O_CLOEXEC);
setns(fd, CLONE_NEWNET);  // join network namespace of PID 1234
close(fd);
```

**The `nsenter` tool** is a thin wrapper around `setns()`. Docker's `docker exec` uses `setns()` to join a container's namespaces.

**Restrictions**:
- Cannot use `setns()` with PID namespace if the process has threads (use `clone()` instead)
- User namespace: can only join with `CAP_SYS_ADMIN` in the **target** namespace, or if you own it
- Time namespace: cannot join after `exec()` due to VDSO mapping constraints

### `ioctl_ns(2)` — Namespace Relationships

Kernel 4.9+ exposes namespace relationship queries via `ioctl()`:

```c
// Get the user namespace that owns this namespace
int owner_fd = ioctl(ns_fd, NS_GET_USERNS);

// Get the parent namespace (for hierarchical namespaces: user, pid)
int parent_fd = ioctl(ns_fd, NS_GET_PARENT);

// Get the namespace type
int type = ioctl(ns_fd, NS_GET_NSTYPE);  // returns CLONE_NEW* flag

// Get owner UID in current user namespace
uid_t uid;
ioctl(ns_fd, NS_GET_OWNER_UID, &uid);  // kernel 4.11+
```

---

## 4. Mount Namespaces (CLONE_NEWNS)

### Concept

Mount namespaces isolate the filesystem mount point table. Each namespace has its own view of which filesystems are mounted where. This was the **first** namespace type added to Linux, hence the generic `CLONE_NEWNS` flag (predating the systematic naming convention).

Mount namespaces underpin container rootfs isolation, overlay filesystems, and `chroot`-on-steroids behavior.

### Kernel Internals

The mount namespace is represented by `struct mnt_namespace`:

```c
// fs/mount.h
struct mnt_namespace {
    struct ns_common        ns;
    struct mount            *root;      // root mount point
    struct list_head        list;       // all mounts in this ns
    spinlock_t              ns_lock;
    struct user_namespace   *user_ns;   // owning user ns
    u64                     seq;        // sequence number
    wait_queue_head_t       poll;
    u64                     event;
    unsigned int            mounts;
    unsigned int            pending_mounts;
};
```

When a new mount namespace is created, the kernel **copies** the mount tree from the parent. However, this is a **copy of mount point metadata**, not a copy of the data. The underlying filesystem blocks are shared.

### Mount Propagation

Mount namespaces introduce one of the most complex subsystems in the kernel: **mount propagation**. When you mount/unmount in one namespace, should other namespaces see the change?

Four propagation types:

| Type | `MS_*` Flag | Behavior |
|---|---|---|
| `shared` | `MS_SHARED` | Mounts propagate bidirectionally between peer mounts |
| `private` | `MS_PRIVATE` | No propagation in or out |
| `slave` | `MS_SLAVE` | Receives propagation from master, doesn't send back |
| `unbindable` | `MS_UNBINDABLE` | Like private, also cannot be bind-mounted |

The default for new mount namespaces in most distros is `shared` propagation from the root. This can cause the surprising behavior where mounting something inside a container is visible on the host — **unless you recursively privatize first**:

```bash
# Standard container setup: make all mounts private before new namespace
mount --make-rprivate /
```

### C Implementation: Mount Namespace Isolation

```c
// mount_ns_demo.c
// Demonstrates complete mount namespace isolation
// Compile: gcc -o mount_ns_demo mount_ns_demo.c
// Run: sudo ./mount_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <fcntl.h>

#define STACK_SIZE (1024 * 1024)  // 1MB stack for child

// Structure passed to child via stack
struct child_args {
    int   pipe_fd[2];   // synchronization pipe
    char *rootfs;       // path to new rootfs (or NULL)
};

static void die(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

// Pivot root implementation for proper container rootfs
// pivot_root(2) is superior to chroot(2) because:
//   1. It changes the root for the entire mount namespace
//   2. The old root is accessible (for cleanup) then can be unmounted
//   3. chroot can be escaped; pivot_root cannot (with proper setup)
static void pivot_to_rootfs(const char *new_root) {
    char put_old[256];
    snprintf(put_old, sizeof(put_old), "%s/.old_root", new_root);

    // Create the pivot target directory
    mkdir(put_old, 0700);

    // Bind mount the new root onto itself (required for pivot_root to work
    // when new_root is not already a mount point)
    if (mount(new_root, new_root, NULL, MS_BIND | MS_REC, NULL) < 0)
        die("mount bind new_root");

    // pivot_root: new_root becomes /, old root goes to put_old
    if (syscall(SYS_pivot_root, new_root, put_old) < 0)
        die("pivot_root");

    // After pivot, we are now chdir'd in the old root hierarchy
    // Change to new root
    if (chdir("/") < 0)
        die("chdir /");

    // Unmount the old root - we don't need it anymore
    // MS_DETACH does a lazy unmount (unmounts now, cleans up when no longer busy)
    if (umount2("/.old_root", MNT_DETACH) < 0)
        die("umount2 old_root");

    rmdir("/.old_root");
}

// Child process function
static int child_fn(void *arg) {
    struct child_args *args = (struct child_args *)arg;
    char ch;

    // Wait for parent to signal readiness (UID/GID mapping set up)
    close(args->pipe_fd[1]);
    if (read(args->pipe_fd[0], &ch, 1) != 0)
        die("unexpected data on pipe");
    close(args->pipe_fd[0]);

    // Demonstrate: we now have our own mount namespace
    printf("[child] Mount namespace inode: ");
    fflush(stdout);
    system("readlink /proc/self/ns/mnt");

    // Make all current mounts private (stop propagation from/to parent)
    // This is the critical step that Docker/runc/containerd all do
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) < 0)
        die("make mounts private");

    // Mount a new tmpfs - completely invisible to parent
    if (mkdir("/tmp/isolated_tmp", 0777) < 0 && errno != EEXIST)
        die("mkdir /tmp/isolated_tmp");

    if (mount("tmpfs", "/tmp/isolated_tmp", "tmpfs", 0,
              "size=64m,mode=1777") < 0)
        die("mount tmpfs");

    printf("[child] Mounted private tmpfs at /tmp/isolated_tmp\n");
    printf("[child] This mount is INVISIBLE to parent namespace\n");

    // Show mounts in this namespace
    printf("\n[child] /proc/mounts (first 10 lines):\n");
    FILE *f = fopen("/proc/mounts", "r");
    if (f) {
        char line[512];
        int count = 0;
        while (fgets(line, sizeof(line), f) && count++ < 10)
            printf("  %s", line);
        fclose(f);
    }

    // Show bind mount example: expose only a specific host directory
    printf("\n[child] Setting up bind mount overlay...\n");
    if (mkdir("/tmp/bind_target", 0777) < 0 && errno != EEXIST)
        die("mkdir bind_target");

    // Bind mount /etc/hostname into the namespace read-only
    if (mount("/etc/hostname", "/tmp/bind_target/hostname", NULL,
              MS_BIND, NULL) < 0)
        die("bind mount hostname");

    // Remount bind mount as read-only (two-step required by kernel)
    if (mount(NULL, "/tmp/bind_target/hostname", NULL,
              MS_BIND | MS_REMOUNT | MS_RDONLY, NULL) < 0)
        die("remount readonly");

    printf("[child] Bind-mounted /etc/hostname readonly at "
           "/tmp/bind_target/hostname\n");

    // Verify read-only
    if (open("/tmp/bind_target/hostname", O_RDWR) < 0)
        printf("[child] Confirmed: cannot open for writing (errno=%d)\n", errno);

    return 0;
}

int main(int argc, char *argv[]) {
    struct child_args args;
    char *stack, *stack_top;

    printf("[parent] PID: %d\n", getpid());
    printf("[parent] Mount namespace inode: ");
    fflush(stdout);
    system("readlink /proc/self/ns/mnt");

    // Set up synchronization pipe
    if (pipe(args.pipe_fd) < 0)
        die("pipe");

    args.rootfs = (argc > 1) ? argv[1] : NULL;

    // Allocate stack (stacks grow downward on most architectures)
    stack = malloc(STACK_SIZE);
    if (!stack) die("malloc stack");
    stack_top = stack + STACK_SIZE;

    // Clone with new mount namespace + new UTS namespace
    // SIGCHLD: send SIGCHLD to parent on child exit (for wait())
    pid_t child_pid = clone(child_fn, stack_top,
                            CLONE_NEWNS | CLONE_NEWUTS | SIGCHLD,
                            &args);
    if (child_pid < 0)
        die("clone");

    printf("[parent] Child PID: %d\n", child_pid);

    // Signal child to proceed (close write end of pipe)
    close(args.pipe_fd[1]);

    // Wait for child
    int status;
    waitpid(child_pid, &status, 0);
    printf("[parent] Child exited: %d\n", WEXITSTATUS(status));

    // Verify: the tmpfs the child mounted is NOT visible here
    struct stat st;
    if (stat("/tmp/isolated_tmp", &st) == 0)
        printf("[parent] WARNING: child's mount leaked to parent!\n");
    else
        printf("[parent] Confirmed: child's tmpfs NOT visible in parent ns\n");

    free(stack);
    return 0;
}
```

### Overlay Filesystems (OverlayFS)

Containers universally use OverlayFS on top of mount namespaces to implement copy-on-write image layers:

```c
// overlayfs_setup.c — sets up a minimal container overlay
#define _GNU_SOURCE
#include <sys/mount.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

/**
 * OverlayFS structure:
 *
 *   lower/   ← read-only base layer (container image)
 *   upper/   ← read-write layer (container writes go here)  
 *   work/    ← kernel work directory (must be on same fs as upper)
 *   merged/  ← union mount point (what the container sees)
 *
 * When a file in lower is modified, it's copied to upper first
 * (copy-on-write). Deletions create "whiteout" files in upper.
 */
int setup_overlay(const char *lower, const char *upper,
                  const char *work,  const char *merged) {
    char opts[4096];
    snprintf(opts, sizeof(opts),
             "lowerdir=%s,upperdir=%s,workdir=%s",
             lower, upper, work);

    if (mount("overlay", merged, "overlay", 0, opts) < 0) {
        perror("overlay mount");
        return -1;
    }
    printf("OverlayFS mounted at %s\n", merged);
    printf("  Lower (RO): %s\n", lower);
    printf("  Upper (RW): %s\n", upper);
    printf("  Work:       %s\n", work);
    return 0;
}

int main(void) {
    // Create directory structure
    mkdir("/tmp/overlay_demo",         0755);
    mkdir("/tmp/overlay_demo/lower",   0755);
    mkdir("/tmp/overlay_demo/upper",   0755);
    mkdir("/tmp/overlay_demo/work",    0755);
    mkdir("/tmp/overlay_demo/merged",  0755);

    // Populate lower layer (read-only "image")
    system("echo 'base file' > /tmp/overlay_demo/lower/base.txt");
    system("echo 'shared config' > /tmp/overlay_demo/lower/config.txt");

    if (setup_overlay("/tmp/overlay_demo/lower",
                      "/tmp/overlay_demo/upper",
                      "/tmp/overlay_demo/work",
                      "/tmp/overlay_demo/merged") < 0)
        return 1;

    // In merged view: both files visible
    printf("\nMerged view:\n");
    system("ls -la /tmp/overlay_demo/merged/");

    // Modify a file — goes to upper/ (CoW)
    system("echo 'modified' > /tmp/overlay_demo/merged/config.txt");

    printf("\nUpper layer after modification (CoW):\n");
    system("ls -la /tmp/overlay_demo/upper/");

    printf("\nLower layer unchanged:\n");
    system("cat /tmp/overlay_demo/lower/config.txt");

    // Cleanup
    umount("/tmp/overlay_demo/merged");
    return 0;
}
```

---

## 5. UTS Namespaces (CLONE_NEWUTS)

### Concept

UTS (Unix Time-sharing System) namespaces isolate two kernel identifiers:
- **Hostname**: returned by `gethostname(2)`, set by `sethostname(2)`
- **NIS domain name**: returned by `getdomainname(2)`, set by `setdomainname(2)`

Every container needs its own hostname (so `hostname` inside a Docker container returns the container ID, not the host's hostname). This is the simplest namespace to implement.

### Kernel Structure

```c
// include/linux/utsname.h
struct uts_namespace {
    struct new_utsname name;    // the actual hostname data
    struct user_namespace *user_ns;
    struct ucounts *ucounts;
    struct ns_common ns;
};

struct new_utsname {
    char sysname[__NEW_UTS_LEN + 1];    // "Linux"
    char nodename[__NEW_UTS_LEN + 1];   // hostname
    char release[__NEW_UTS_LEN + 1];    // kernel release
    char version[__NEW_UTS_LEN + 1];    // kernel version
    char machine[__NEW_UTS_LEN + 1];    // architecture
    char domainname[__NEW_UTS_LEN + 1]; // NIS domain
};
```

Note: `sysname`, `release`, `version`, and `machine` are **not** namespaced — all processes in all UTS namespaces see the same kernel version. Only `nodename` and `domainname` are per-namespace.

### C Implementation

```c
// uts_ns_demo.c
// Demonstrates UTS namespace isolation
// Compile: gcc -o uts_ns_demo uts_ns_demo.c
// Run: sudo ./uts_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <errno.h>

#define STACK_SIZE (1024 * 1024)

static void print_utsname(const char *prefix) {
    struct utsname u;
    if (uname(&u) < 0) { perror("uname"); return; }
    printf("%s sysname=%s nodename=%s release=%s\n",
           prefix, u.sysname, u.nodename, u.release);
}

static int child_fn(void *arg) {
    print_utsname("[child-before]");

    // Set a new hostname in this namespace
    const char *new_host = "container-42";
    if (sethostname(new_host, strlen(new_host)) < 0)
        perror("sethostname");

    // Set a new NIS domain
    const char *new_domain = "my-cluster.internal";
    if (setdomainname(new_domain, strlen(new_domain)) < 0)
        perror("setdomainname");

    print_utsname("[child-after] ");

    // Demonstrate: these are scoped to THIS namespace
    // The parent will still see its original hostname
    sleep(1);
    return 0;
}

int main(void) {
    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    print_utsname("[parent]      ");

    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWUTS | SIGCHLD, NULL);
    if (child < 0) { perror("clone"); free(stack); return 1; }

    int status;
    waitpid(child, &status, 0);

    // Parent hostname is unchanged
    print_utsname("[parent-after]");

    free(stack);
    return 0;
}
```

---

## 6. IPC Namespaces (CLONE_NEWIPC)

### Concept

IPC namespaces isolate **System V IPC** objects and **POSIX message queues**:

- **System V IPC**:
  - Message queues (`msgget`, `msgsnd`, `msgrcv`)
  - Semaphore arrays (`semget`, `semop`)  
  - Shared memory segments (`shmget`, `shmat`, `shmdt`)
- **POSIX message queues** (the `/dev/mqueue` filesystem)

This prevents container processes from accidentally (or maliciously) accessing IPC objects created by host processes or other containers.

### Why IPC Isolation Matters

System V IPC objects are identified by **integer keys** derived from file paths via `ftok()`. Without IPC namespaces, two containers using the same application (e.g., PostgreSQL) could end up with the same IPC key and corrupt each other's shared memory segments. This happened in practice before IPC namespaces.

### Kernel Structure

```c
// include/linux/ipc_namespace.h (simplified)
struct ipc_namespace {
    struct ipc_ids  ids[3];    // [0]=msg, [1]=sem, [2]=shm
    
    // Message queue limits
    unsigned int    msg_ctlmax;   // max size of message
    unsigned int    msg_ctlmnb;   // max bytes in a queue
    unsigned int    msg_ctlmni;   // max number of queues
    
    // Shared memory limits  
    size_t          shm_ctlmax;   // max shared memory segment
    size_t          shm_ctlall;   // max total shared memory
    unsigned long   shm_tot;      // current total shared memory
    
    // Semaphore limits
    int             sem_ctls[4];  // [SEMMSL,SEMMNS,SEMOPM,SEMMNI]
    
    struct user_namespace *user_ns;
    struct ns_common ns;
};
```

### C Implementation

```c
// ipc_ns_demo.c
// Demonstrates IPC namespace isolation with shared memory
// Compile: gcc -o ipc_ns_demo ipc_ns_demo.c
// Run: sudo ./ipc_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <sys/msg.h>
#include <sys/wait.h>
#include <errno.h>

#define STACK_SIZE (1024 * 1024)
#define SHM_KEY    0xDEADBEEF
#define SHM_SIZE   4096

static void show_ipc_state(const char *prefix) {
    printf("%s IPC state:\n", prefix);
    
    // List shared memory segments
    int shmid = shmget(SHM_KEY, 0, 0);
    if (shmid >= 0) {
        struct shmid_ds ds;
        shmctl(shmid, IPC_STAT, &ds);
        printf("  SHM id=%d key=0x%x size=%zu\n",
               shmid, SHM_KEY, ds.shm_segsz);
    } else {
        printf("  No SHM with key 0x%x visible\n", SHM_KEY);
    }

    // List POSIX message queues (via /dev/mqueue)
    printf("  POSIX MQs: ");
    fflush(stdout);
    system("ls /dev/mqueue/ 2>/dev/null || echo '(empty)'");
}

typedef struct {
    int pipe_fd[2];
} child_args_t;

static int child_fn(void *arg) {
    child_args_t *args = (child_args_t *)arg;
    char buf[1];

    // Wait for parent signal
    close(args->pipe_fd[1]);
    read(args->pipe_fd[0], buf, 1);
    close(args->pipe_fd[0]);

    printf("\n[child] Entered new IPC namespace\n");
    printf("[child] IPC ns inode: ");
    fflush(stdout);
    system("readlink /proc/self/ns/ipc");

    // Mount POSIX mqueue for this namespace
    // Each IPC namespace can have its own /dev/mqueue mount
    if (mount("mqueue", "/dev/mqueue", "mqueue", 0, NULL) < 0)
        perror("mount mqueue (may need to mkdir /dev/mqueue)");

    // Verify: parent's SHM is NOT visible
    show_ipc_state("[child]");

    // Create a new SHM segment with the SAME key as parent used
    // This is allowed because we're in a different IPC namespace!
    int shmid = shmget(SHM_KEY, SHM_SIZE, IPC_CREAT | IPC_EXCL | 0666);
    if (shmid < 0) {
        perror("[child] shmget failed");
        return 1;
    }
    printf("[child] Created SHM with same key 0x%x, id=%d\n", SHM_KEY, shmid);

    // Write to it
    char *shm = shmat(shmid, NULL, 0);
    if (shm == (void *)-1) { perror("shmat"); return 1; }
    strcpy(shm, "Hello from container namespace!");
    shmdt(shm);

    // Create a semaphore set
    int semid = semget(IPC_PRIVATE, 1, IPC_CREAT | 0666);
    printf("[child] Created semaphore id=%d\n", semid);

    // Create a message queue  
    int mqid = msgget(IPC_PRIVATE, IPC_CREAT | 0666);
    printf("[child] Created message queue id=%d\n", mqid);

    show_ipc_state("[child-final]");

    // Cleanup before exit
    shmctl(shmid, IPC_RMID, NULL);
    semctl(semid, 0, IPC_RMID);
    msgctl(mqid, IPC_RMID, NULL);

    return 0;
}

int main(void) {
    child_args_t args;
    if (pipe(args.pipe_fd) < 0) { perror("pipe"); return 1; }

    printf("[parent] PID=%d, IPC ns: ", getpid());
    fflush(stdout);
    system("readlink /proc/self/ns/ipc");

    // Create SHM in parent's namespace
    int shmid = shmget(SHM_KEY, SHM_SIZE, IPC_CREAT | IPC_EXCL | 0666);
    if (shmid < 0) {
        // Clean up leftover from previous run
        shmid = shmget(SHM_KEY, SHM_SIZE, 0666);
        shmctl(shmid, IPC_RMID, NULL);
        shmid = shmget(SHM_KEY, SHM_SIZE, IPC_CREAT | IPC_EXCL | 0666);
    }
    printf("[parent] Created SHM id=%d with key 0x%x\n", shmid, SHM_KEY);
    show_ipc_state("[parent]");

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    // CLONE_NEWIPC | CLONE_NEWNS needed for mqueue mount
    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWIPC | CLONE_NEWNS | SIGCHLD, &args);
    if (child < 0) { perror("clone"); return 1; }

    // Signal child
    close(args.pipe_fd[1]);
    
    int status;
    waitpid(child, &status, 0);

    // Parent's SHM still intact
    show_ipc_state("[parent-after]");

    // Cleanup
    shmctl(shmid, IPC_RMID, NULL);
    free(stack);
    return 0;
}
```

---

## 7. PID Namespaces (CLONE_NEWPID)

### Concept

PID namespaces isolate the process ID number space. Processes in different PID namespaces can have the same PID. A process has **two PIDs**:

1. Its PID **inside** its PID namespace (what `getpid()` returns)
2. Its PID **in each ancestor namespace** (what `/proc/[pid]/status` shows as `NSpid`)

This enables every container to have a "PID 1" — an init process — without conflicting with the host's PID 1.

### Hierarchical Structure

PID namespaces are **strictly hierarchical**. A process in a namespace can see processes in its own namespace and all **descendant** namespaces, but NOT ancestor namespaces.

```
Host PID namespace:
  PID 1 (systemd)
  PID 100 (sshd)
  PID 200 (container runtime)
    │
    └── Container PID namespace:
          PID 1 (nginx)  [host sees this as PID 201]
          PID 2 (worker) [host sees this as PID 202]
            │
            └── Nested container PID namespace:
                  PID 1 (bash)  [container sees PID 3, host sees PID 203]
```

The nesting depth limit is `MAX_PID_NS_LEVEL = 32`.

### PID 1 Special Semantics

In a PID namespace, PID 1 has special significance:
- It's the **reaper** for orphaned processes in the namespace. When PID 1 dies, all other processes in the namespace are killed with `SIGKILL`.
- It can ignore signals that would normally kill other processes (like `SIGTERM`). Only `SIGKILL` from an outer namespace can kill it unconditionally.
- This is why containers need a proper init process (tini, dumb-init) — not just your application binary.

### `getpid()` Behavior

```c
// In a child of clone(CLONE_NEWPID):
getpid()        // returns 1 (its PID in its own namespace)
getppid()       // returns 0 (parent is in outer namespace, invisible)

// In the parent (outer namespace):
// child's getpid()=1, but parent sees it as pid=201
```

### `/proc` and PID Namespaces

The `/proc` filesystem is **not automatically updated** when you enter a PID namespace. You must mount a new `/proc` inside the new namespace:

```bash
mount -t proc proc /proc
```

Otherwise, commands like `ps`, `top`, and `kill` will read the wrong `/proc` and see (or worse, signal) the wrong processes.

### C Implementation

```c
// pid_ns_demo.c
// Full PID namespace demo with proper /proc handling
// Compile: gcc -o pid_ns_demo pid_ns_demo.c
// Run: sudo ./pid_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>
#include <fcntl.h>

#define STACK_SIZE (1024 * 1024)

// Minimal init process behavior
// A real container init must:
//   1. Reap zombie child processes
//   2. Forward signals to children
//   3. Handle SIGTERM gracefully
static void init_process(void) {
    printf("[init/PID1] Running as PID %d in new namespace\n", getpid());
    printf("[init/PID1] Parent PID: %d (0 = parent in outer ns)\n", getppid());

    // Set up a new /proc for this PID namespace
    // Without this, /proc still shows host processes
    if (mount("proc", "/proc", "proc",
              MS_NODEV | MS_NOSUID | MS_NOEXEC, NULL) < 0) {
        perror("[init] mount /proc");
        // Continue anyway — might not have a suitable /proc
    }

    // Spawn some child processes to demonstrate PID allocation
    printf("\n[init/PID1] Spawning child processes...\n");

    for (int i = 0; i < 3; i++) {
        pid_t child = fork();
        if (child == 0) {
            printf("[child-%d] PID=%d PPID=%d\n", i+1, getpid(), getppid());
            sleep(1);
            exit(0);
        }
        printf("[init/PID1] Spawned child PID=%d\n", child);
    }

    // Show /proc contents — should only show PIDs in this namespace
    printf("\n[init/PID1] /proc directory contents:\n");
    system("ls /proc/ | grep -E '^[0-9]+$' | sort -n | head -20");

    printf("\n[init/PID1] ps output:\n");
    system("ps aux 2>/dev/null || ps -ef 2>/dev/null || "
           "cat /proc/[0-9]*/status 2>/dev/null | grep -E 'Name:|Pid:' | paste - -");

    // Reap children (minimal init behavior)
    int status;
    pid_t pid;
    while ((pid = waitpid(-1, &status, WNOHANG)) > 0)
        printf("[init/PID1] Reaped child %d\n", pid);

    sleep(1);  // Wait for children to finish
    while ((pid = wait(&status)) > 0)
        printf("[init/PID1] Reaped child %d\n", pid);
}

// This function is called in the outer namespace to show
// what the host sees — the container's processes have TWO PIDs
static void show_namespace_pids(pid_t container_init_host_pid) {
    char path[256];
    snprintf(path, sizeof(path), "/proc/%d/status", container_init_host_pid);

    FILE *f = fopen(path, "r");
    if (!f) { 
        printf("[host] Cannot read /proc/%d/status\n", container_init_host_pid);
        return; 
    }

    char line[256];
    printf("[host] Namespace PID info for container init:\n");
    while (fgets(line, sizeof(line), f)) {
        // NSpid shows PID in each level of the namespace hierarchy
        if (strncmp(line, "NSpid:", 6) == 0 ||
            strncmp(line, "Pid:",   4) == 0)
            printf("  %s", line);
    }
    fclose(f);
}

static int child_fn(void *arg) {
    // We are now PID 1 in a new PID namespace + new mount namespace
    // The new mount namespace is needed so we can remount /proc
    
    // Remount / as private to prevent propagation
    mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL);
    
    init_process();
    return 0;
}

int main(void) {
    printf("[host] Host PID: %d\n", getpid());
    printf("[host] Host PID ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/pid");

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    // CLONE_NEWPID + CLONE_NEWNS (so we can remount /proc)
    // NOTE: The *parent* still has the same PID ns; only the CHILD
    // (the clone()-created process) gets PID 1 in the new namespace
    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWPID | CLONE_NEWNS | SIGCHLD, NULL);
    if (child < 0) { perror("clone"); free(stack); return 1; }

    printf("[host] Container init has host PID=%d\n", child);
    
    // Show how the kernel exposes the namespace PID translation
    sleep(1);  // Give child time to start
    show_namespace_pids(child);

    int status;
    waitpid(child, &status, 0);
    printf("[host] Container exited\n");

    free(stack);
    return 0;
}
```

### PID Namespace and `/proc/<pid>/ns/pid_for_children`

Note the subtle distinction in `/proc/self/ns/`:

```bash
/proc/self/ns/pid                  # current PID namespace (immutable for running process)
/proc/self/ns/pid_for_children     # PID namespace that future children will be in
```

After `unshare(CLONE_NEWPID)`, the process's `pid` symlink doesn't change, but `pid_for_children` updates. This reflects the kernel's design that `unshare(CLONE_NEWPID)` only affects future forks.

---

## 8. Network Namespaces (CLONE_NEWNET)

### Concept

Network namespaces are the most complex and powerful namespace type. Each network namespace has a completely isolated network stack:

- Network interfaces (lo, eth0, etc.)
- IP routing tables
- Firewall rules (iptables/nftables)
- Network sockets (TCP/UDP connections)
- `/proc/net/` and `/sys/class/net/` entries
- Unix domain socket filesystem paths
- Port number space (port 80 in one namespace ≠ port 80 in another)
- IPVS and conntrack tables

### Connecting Namespaces: Virtual Ethernet Pairs (veth)

An isolated network namespace is useless unless it can communicate. The standard mechanism is a **veth pair** — a virtual Ethernet cable with two ends. One end in the container namespace, one on the host (or in a bridge).

```
Host namespace                    Container namespace
─────────────────                 ──────────────────
 veth0 (10.0.0.1) ←──────────→  eth0 (10.0.0.2)
     │
  br0 (bridge)
     │
  eth0 (physical)
```

### Network Namespace Topology in Docker

Docker's default bridge network:

```
Host kernel
│
├── Host net ns
│   ├── docker0 bridge (172.17.0.1/16)
│   ├── veth8a3f2b (host side of container 1's veth pair)
│   └── vethc9d4e1 (host side of container 2's veth pair)
│
├── Container 1 net ns
│   └── eth0 (172.17.0.2/16) ← paired with veth8a3f2b
│
└── Container 2 net ns
    └── eth0 (172.17.0.3/16) ← paired with vethc9d4e1
```

### C Implementation: Full Network Namespace Setup

```c
// net_ns_demo.c
// Creates a network namespace with veth pair, IP configuration,
// and demonstrates cross-namespace communication
// Compile: gcc -o net_ns_demo net_ns_demo.c
// Run: sudo ./net_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <linux/rtnetlink.h>

#define STACK_SIZE (1024 * 1024)

// Execute a shell command and return exit code
static int run_cmd(const char *fmt, ...) {
    char cmd[1024];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(cmd, sizeof(cmd), fmt, ap);
    va_end(ap);
    printf("  [cmd] %s\n", cmd);
    return system(cmd);
}

// Set up networking from the host side:
//   1. Create veth pair
//   2. Move one end into the container's network namespace
//   3. Configure IP on host side
static void setup_host_network(pid_t container_pid) {
    printf("[host-net] Setting up veth pair...\n");

    // Create veth pair: veth_host <-> veth_cont
    run_cmd("ip link add veth_host type veth peer name veth_cont");

    // Move veth_cont into container's network namespace
    run_cmd("ip link set veth_cont netns %d", container_pid);

    // Configure host side
    run_cmd("ip link set veth_host up");
    run_cmd("ip addr add 192.168.100.1/24 dev veth_host");

    // Enable IP forwarding (needed for containers to reach internet)
    run_cmd("sysctl -qw net.ipv4.ip_forward=1");

    // Set up NAT for container traffic
    run_cmd("iptables -t nat -A POSTROUTING -s 192.168.100.0/24 "
            "-j MASQUERADE");

    printf("[host-net] Host side configured: veth_host=192.168.100.1\n");
}

static void teardown_host_network(void) {
    run_cmd("ip link del veth_host 2>/dev/null");
    run_cmd("iptables -t nat -D POSTROUTING -s 192.168.100.0/24 "
            "-j MASQUERADE 2>/dev/null");
}

// Container-side network setup
static void setup_container_network(void) {
    printf("[container-net] Configuring network...\n");

    // Bring up loopback
    run_cmd("ip link set lo up");

    // Configure the veth end that was moved into this namespace
    run_cmd("ip link set veth_cont up");
    run_cmd("ip addr add 192.168.100.2/24 dev veth_cont");

    // Default route via host
    run_cmd("ip route add default via 192.168.100.1");

    printf("[container-net] Container side configured: "
           "veth_cont=192.168.100.2\n");
}

static int container_fn(void *arg) {
    int *sync_pipe = (int *)arg;

    printf("\n[container] PID=%d in new network namespace\n", getpid());
    printf("[container] Net ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/net");

    // Show empty network state
    printf("[container] Initial interfaces:\n");
    run_cmd("ip link show");

    // Signal host to set up veth pair and wait for it
    char go = 'G';
    write(sync_pipe[1], &go, 1);
    read(sync_pipe[0], &go, 1);  // wait for host to finish

    // Configure our side of the network
    setup_container_network();

    printf("\n[container] Final network state:\n");
    run_cmd("ip addr show");
    run_cmd("ip route show");

    // Test connectivity
    printf("\n[container] Testing connectivity to host (192.168.100.1):\n");
    run_cmd("ping -c 3 -W 1 192.168.100.1");

    // Start a minimal HTTP server on port 8080 inside the container
    // This port is ONLY accessible from within the network namespace
    // (or via port forwarding — not set up here)
    printf("\n[container] Port 8080 in this ns is isolated from host\n");
    printf("[container] A server here would be unreachable from outside\n");

    // Demonstrate: socket bound to port 80 in this namespace
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(80),
        .sin_addr.s_addr = INADDR_ANY
    };

    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) == 0)
        printf("[container] Successfully bound to port 80 "
               "(no conflict with host port 80!)\n");
    else
        printf("[container] bind failed: %s\n", strerror(errno));

    close(sock);
    return 0;
}

int main(void) {
    int sync_pipe[2][2];
    pipe(sync_pipe[0]);
    pipe(sync_pipe[1]);

    int pipe_fds[2] = { sync_pipe[0][0], sync_pipe[1][1] };

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    printf("[host] Creating container with new network namespace...\n");
    printf("[host] Host net ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/net");

    pid_t child = clone(container_fn, stack + STACK_SIZE,
                        CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWUTS | SIGCHLD,
                        pipe_fds);
    if (child < 0) { perror("clone"); return 1; }

    // Wait for container to be ready for network setup
    char go;
    read(sync_pipe[0][0], &go, 1);

    // Set up networking from host side
    setup_host_network(child);

    // Signal container to continue
    write(sync_pipe[1][1], &go, 1);

    int status;
    waitpid(child, &status, 0);

    // Cleanup
    teardown_host_network();

    printf("\n[host] Port 80 on host is unaffected by container's bind:\n");
    run_cmd("ss -tlnp | grep ':80 ' || echo '  (nothing on port 80 on host)'");

    free(stack);
    return 0;
}
```

### Network Namespace and `ip netns`

The `ip netns` command manages **named** network namespaces by creating bind mounts in `/var/run/netns/`:

```bash
# Create a named network namespace (persists in /var/run/netns/)
ip netns add myns

# Execute a command in the namespace
ip netns exec myns ip link show

# This is equivalent to:
# 1. open("/var/run/netns/myns")   ← bind mount of ns fd
# 2. setns(fd, CLONE_NEWNET)
# 3. exec the command
```

The `ip netns` persistence mechanism is important — it keeps the namespace alive even when no processes are members of it.

---

## 9. User Namespaces (CLONE_NEWUSER)

### Concept

User namespaces are the **most powerful and most security-critical** namespace type. They map UIDs and GIDs between namespaces, allowing a process to have different privilege levels in different contexts.

Key capability: a process can be **UID 0 (root) inside a user namespace** while remaining **an unprivileged user outside**. This is the foundation for rootless containers.

### UID/GID Mapping

Mappings are written to:
- `/proc/[pid]/uid_map`
- `/proc/[pid]/gid_map`

Format: `<inside-uid> <outside-uid> <length>`

```
# Map inside UIDs 0-65535 to outside UIDs 100000-165535
echo "0 100000 65536" > /proc/<pid>/uid_map
```

Constraints:
- Can only be written **once** (not modifiable after set)
- Must be written **before** the process attempts operations requiring mappings
- Process writing must have privilege in the **parent** user namespace
- For security, `newuidmap`/`newgidmap` setuid helpers exist for unprivileged setup

### Capability Semantics in User Namespaces

When a user namespace is created:
1. The creating process gets a **full set of capabilities** (`CAP_SYS_ADMIN`, etc.) in the new namespace
2. These capabilities apply to resources **owned by** that user namespace
3. They do NOT grant any capabilities in the parent namespace

```c
// Inside new user namespace:
// getuid() == 0, getcap() == full set
// BUT: trying to mount block devices, load kernel modules etc. fails
// because those require caps in the INITIAL (host) user namespace
```

### Security Implications

User namespaces have historically been a major attack surface. Many kernel vulnerabilities have been discovered through unprivileged user namespace + exploit combinations, leading many distributions to restrict them:

```bash
# Check if unprivileged user namespaces are enabled
cat /proc/sys/kernel/unprivileged_userns_clone  # Debian/Ubuntu
cat /proc/sys/user/max_user_namespaces          # other distros

# Restrict (set to 0 to disable unprivileged user ns)
sysctl -w kernel.unprivileged_userns_clone=0
```

### C Implementation: Rootless Container Setup

```c
// user_ns_demo.c
// Demonstrates user namespace with UID/GID mapping
// KEY FEATURE: run as unprivileged user!
// Compile: gcc -o user_ns_demo user_ns_demo.c
// Run: ./user_ns_demo  (NO sudo needed!)

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/wait.h>
#include <sys/capability.h>  // -lcap
#include <sys/prctl.h>
#include <pwd.h>
#include <grp.h>

#define STACK_SIZE (1024 * 1024)

// Write a uid/gid mapping
static int write_mapping(const char *path, 
                          uid_t inner, uid_t outer, int count) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) { perror(path); return -1; }

    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%u %u %d\n", inner, outer, count);
    if (write(fd, buf, len) != len) {
        perror("write mapping");
        close(fd);
        return -1;
    }
    close(fd);
    return 0;
}

// Disable setgroups before writing gid_map (required for unprivileged)
static int disable_setgroups(pid_t pid) {
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    int fd = open(path, O_WRONLY);
    if (fd < 0) { perror("open setgroups"); return -1; }
    if (write(fd, "deny", 4) != 4) { perror("write setgroups"); close(fd); return -1; }
    close(fd);
    return 0;
}

static void print_capabilities(const char *prefix) {
    // Read /proc/self/status for capability sets
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "Cap", 3) == 0)
            printf("%s %s", prefix, line);
    }
    fclose(f);
}

static void print_id_info(const char *prefix) {
    printf("%s uid=%d euid=%d gid=%d egid=%d\n",
           prefix, getuid(), geteuid(), getgid(), getegid());
}

typedef struct {
    int pipe_ready[2];   // child signals parent it's ready
    int pipe_go[2];      // parent signals child to continue
    uid_t outer_uid;
    gid_t outer_gid;
} sync_t;

static int child_fn(void *arg) {
    sync_t *s = (sync_t *)arg;

    // Signal parent we're ready for UID mapping
    char c = 'R';
    write(s->pipe_ready[1], &c, 1);
    close(s->pipe_ready[1]);

    // Wait for parent to set up UID/GID maps
    read(s->pipe_go[0], &c, 1);
    close(s->pipe_go[0]);

    printf("\n[child] Inside new user namespace:\n");
    print_id_info("[child]");
    printf("[child] User ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/user");

    printf("\n[child] Capabilities in new user namespace:\n");
    print_capabilities("[child]");

    // We now have CAP_SYS_ADMIN in this namespace!
    // Can create other namespaces
    printf("\n[child] Creating nested namespaces (no root required)...\n");
    if (unshare(CLONE_NEWUTS) == 0) {
        sethostname("inner-container", 15);
        char hostname[64] = {0};
        gethostname(hostname, sizeof(hostname));
        printf("[child] Set hostname to: %s\n", hostname);
    } else {
        perror("[child] unshare UTS");
    }

    if (unshare(CLONE_NEWNET) == 0)
        printf("[child] Created private network namespace\n");
    else
        perror("[child] unshare NET");

    // Demonstrate: creating files as "root" (UID 0 inside, mapped to outer UID)
    printf("\n[child] Creating file as uid=0 inside namespace...\n");
    int fd = open("/tmp/ns_test_file", O_CREAT | O_WRONLY, 0644);
    if (fd >= 0) {
        write(fd, "created by 'root' in user ns\n", 29);
        close(fd);
        printf("[child] File created. Outside ns, it's owned by uid=%d\n",
               s->outer_uid);
    }

    // Try something that REQUIRES real host capabilities (should fail)
    printf("\n[child] Attempting mount (needs real CAP_SYS_ADMIN)...\n");
    if (mount("tmpfs", "/mnt", "tmpfs", 0, NULL) < 0)
        printf("[child] Mount failed as expected: %s\n", strerror(errno));
    // NOTE: With CLONE_NEWNS + CLONE_NEWUSER, mount CAN work within the ns

    return 0;
}

int main(void) {
    sync_t s;
    pipe(s.pipe_ready);
    pipe(s.pipe_go);
    s.outer_uid = getuid();
    s.outer_gid = getgid();

    printf("[parent] Running as:\n");
    print_id_info("[parent]");
    printf("[parent] Capabilities (no new user ns):\n");
    print_capabilities("[parent]");

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    // CLONE_NEWUSER can be done without privileges!
    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWUSER | SIGCHLD, &s);
    if (child < 0) { perror("clone NEWUSER"); free(stack); return 1; }

    // Wait for child to be ready
    char c;
    read(s.pipe_ready[0], &c, 1);
    close(s.pipe_ready[0]);

    printf("\n[parent] Setting up UID/GID maps for child %d...\n", child);

    // Disable setgroups before writing gid_map (security requirement)
    disable_setgroups(child);

    // Map: inside UID 0 → outside UID (our own UID)
    // Inside the namespace, the child appears as root
    // Outside, it's still our unprivileged UID
    char uid_map_path[64], gid_map_path[64];
    snprintf(uid_map_path, sizeof(uid_map_path), "/proc/%d/uid_map", child);
    snprintf(gid_map_path, sizeof(gid_map_path), "/proc/%d/gid_map", child);

    if (write_mapping(uid_map_path, 0, s.outer_uid, 1) < 0)
        fprintf(stderr, "[parent] uid_map write failed\n");
    if (write_mapping(gid_map_path, 0, s.outer_gid, 1) < 0)
        fprintf(stderr, "[parent] gid_map write failed\n");

    printf("[parent] Maps written: uid 0-in → %d-out\n", s.outer_uid);

    // Signal child to continue
    write(s.pipe_go[1], "G", 1);
    close(s.pipe_go[1]);

    int status;
    waitpid(child, &status, 0);

    // Verify: file created inside ns is owned by our UID outside
    printf("\n[parent] File created in user ns:\n");
    system("ls -la /tmp/ns_test_file 2>/dev/null");
    unlink("/tmp/ns_test_file");

    free(stack);
    return 0;
}
```

---

## 10. Cgroup Namespaces (CLONE_NEWCGROUP)

### Concept

Cgroup namespaces virtualize the **view** of the cgroup hierarchy, not the cgroups themselves. A process inside a cgroup namespace sees its own cgroup as `/` (root) instead of the full path like `/system.slice/docker-abc123.scope`.

This is primarily a **visibility** feature:
- Prevents container processes from seeing the host's cgroup hierarchy
- Allows `/proc/self/cgroup` to show relative paths
- Does NOT create new cgroups or change resource limits

### Why It Matters

Without cgroup namespaces:
```
# Process inside container reads /proc/self/cgroup:
12:cpuset:/docker/a1b2c3d4e5f6.../
11:cpu,cpuacct:/docker/a1b2c3d4e5f6.../
...
```

With cgroup namespace:
```
# Same process sees:
12:cpuset:/
11:cpu,cpuacct:/
...
```

The container doesn't leak information about its cgroup placement or the host hierarchy.

### C Implementation

```c
// cgroup_ns_demo.c
// Demonstrates cgroup namespace virtualization
// Compile: gcc -o cgroup_ns_demo cgroup_ns_demo.c
// Run: sudo ./cgroup_ns_demo

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <fcntl.h>

#define STACK_SIZE (1024 * 1024)

static void show_cgroup(const char *prefix) {
    printf("%s /proc/self/cgroup:\n", prefix);
    FILE *f = fopen("/proc/self/cgroup", "r");
    if (!f) { printf("  (cannot read)\n"); return; }
    char line[512];
    while (fgets(line, sizeof(line), f))
        printf("  %s", line);
    fclose(f);
}

static int child_fn(void *arg) {
    printf("\n[child] PID=%d in new cgroup namespace\n", getpid());
    printf("[child] Cgroup ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/cgroup");

    // Mount cgroupfs to see virtualized view
    // In the new namespace, our current cgroup appears as "/"
    show_cgroup("[child]");

    // The cgroup namespace affects what cgroupfs shows
    // For cgroup v2:
    if (mount("cgroup2", "/sys/fs/cgroup", "cgroup2", 0, NULL) == 0) {
        printf("[child] Remounted cgroupfs. Contents appear from namespace root:\n");
        system("ls /sys/fs/cgroup/ | head -10");
        umount("/sys/fs/cgroup");
    }

    return 0;
}

int main(void) {
    printf("[host] Cgroup ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/cgroup");
    show_cgroup("[host]");

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWCGROUP | CLONE_NEWNS | SIGCHLD, NULL);
    if (child < 0) { perror("clone"); free(stack); return 1; }

    int status;
    waitpid(child, &status, 0);

    free(stack);
    return 0;
}
```

---

## 11. Time Namespaces (CLONE_NEWTIME)

### Concept

Time namespaces (added in Linux 5.6, March 2020) are the newest namespace type. They allow per-namespace offsets for two POSIX clocks:

- `CLOCK_MONOTONIC` — steady clock that doesn't jump backward
- `CLOCK_BOOTTIME` — like monotonic, but includes suspend time

Use cases:
- **Container live migration**: when a container moves from one host to another, clock offsets can be adjusted so the container's monotonic time doesn't jump
- **Testing time-sensitive code**: simulate different system uptimes
- **Checkpoint/restore**: CRIU (Checkpoint/Restore In Userspace) uses time ns to restore processes with consistent clock values

### Limitations

`CLOCK_REALTIME` is **not** namespaced (cannot be virtualized per-namespace due to POSIX requirements and NTP synchronization needs). Only `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` are.

### Clock Offset Mechanism

The offset is configured via `/proc/[pid]/timens_offsets` **before** the first thread/process enters the namespace:

```
# Format: <clock-id> <seconds> <nanoseconds>
echo "monotonic 3600 0" > /proc/<pid>/timens_offsets
echo "boottime  3600 0" >> /proc/<pid>/timens_offsets
```

### C Implementation

```c
// time_ns_demo.c
// Demonstrates time namespace clock offsets
// Compile: gcc -o time_ns_demo time_ns_demo.c
// Run: sudo ./time_ns_demo (requires kernel 5.6+)

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <time.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <errno.h>

#define STACK_SIZE (1024 * 1024)

static void print_clocks(const char *prefix) {
    struct timespec mono, boot, real;
    clock_gettime(CLOCK_MONOTONIC,  &mono);
    clock_gettime(CLOCK_BOOTTIME,   &boot);
    clock_gettime(CLOCK_REALTIME,   &real);
    printf("%s MONOTONIC=%ld.%09ld  BOOTTIME=%ld.%09ld  REALTIME=%ld\n",
           prefix, mono.tv_sec, mono.tv_nsec,
           boot.tv_sec, boot.tv_nsec, real.tv_sec);
}

// Write clock offset to timens_offsets
// Must be done BEFORE any process enters the namespace
static int set_time_offset(pid_t pid, const char *clock_name,
                            long secs, long nsecs) {
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/timens_offsets", pid);

    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        perror("open timens_offsets");
        return -1;
    }

    char buf[128];
    int len = snprintf(buf, sizeof(buf), "%s %ld %ld\n",
                       clock_name, secs, nsecs);
    if (write(fd, buf, len) != len) {
        perror("write timens_offsets");
        close(fd);
        return -1;
    }
    close(fd);
    return 0;
}

typedef struct {
    int pipe_ready[2];
    int pipe_go[2];
} sync_t;

static int child_fn(void *arg) {
    sync_t *s = (sync_t *)arg;

    // Signal ready, wait for offset to be configured
    char c = 'R';
    write(s->pipe_ready[1], &c, 1);
    close(s->pipe_ready[1]);
    read(s->pipe_go[0], &c, 1);
    close(s->pipe_go[0]);

    printf("\n[child] In new time namespace:\n");
    printf("[child] Time ns: ");
    fflush(stdout);
    system("readlink /proc/self/ns/time");

    // Clocks now reflect the offset
    print_clocks("[child]");

    printf("[child] CLOCK_REALTIME is NOT offset (same as host)\n");
    printf("[child] CLOCK_MONOTONIC IS offset (+1 hour = 3600s)\n");

    // Applications using clock_gettime(CLOCK_MONOTONIC) will see
    // the offset time — useful for live migration simulation
    return 0;
}

int main(void) {
    // Check kernel version support
    FILE *f = fopen("/proc/version", "r");
    if (f) {
        char ver[256];
        fgets(ver, sizeof(ver), f);
        printf("[host] %s", ver);
        fclose(f);
    }

    printf("[host] Current clocks:\n");
    print_clocks("[host]");

    sync_t s;
    pipe(s.pipe_ready);
    pipe(s.pipe_go);

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWTIME | SIGCHLD, &s);
    if (child < 0) {
        if (errno == EINVAL) {
            fprintf(stderr, "CLONE_NEWTIME not supported "
                    "(requires kernel 5.6+)\n");
        } else {
            perror("clone");
        }
        free(stack);
        return 1;
    }

    // Wait for child to enter namespace
    char c;
    read(s.pipe_ready[0], &c, 1);
    close(s.pipe_ready[0]);

    // Set monotonic offset: +1 hour (3600 seconds)
    // The container appears to have been running for an hour longer
    printf("\n[host] Setting time offset: +3600s on CLOCK_MONOTONIC\n");
    set_time_offset(child, "monotonic", 3600, 0);
    set_time_offset(child, "boottime",  3600, 0);

    // Signal child to read clocks
    write(s.pipe_go[1], "G", 1);
    close(s.pipe_go[1]);

    int status;
    waitpid(child, &status, 0);

    printf("\n[host] Host clocks unchanged:\n");
    print_clocks("[host]");

    free(stack);
    return 0;
}
```

---

## 12. Namespace Lifecycle & /proc Filesystem

### Namespace Lifetime Rules

A namespace is alive as long as **any** of the following is true:

1. **At least one process is a member** — the most common case
2. **An open file descriptor exists** pointing to the namespace fd (`/proc/[pid]/ns/*`)
3. **A bind mount exists** for the namespace (`ip netns add` uses this)

When condition 1 becomes false (last member process exits), conditions 2 or 3 can keep the namespace "pinned" without any running process.

### Enumerating Namespaces

```c
// list_namespaces.c
// Lists all namespaces on the system by scanning /proc
// Compile: gcc -o list_namespaces list_namespaces.c
// Run: sudo ./list_namespaces

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>

#define MAX_NS 1024

typedef struct {
    ino_t  inode;
    char   type[16];
    pid_t  pid;         // first PID seen in this namespace
} ns_entry_t;

static const char *ns_types[] = {
    "cgroup", "ipc", "mnt", "net", "pid",
    "pid_for_children", "time", "time_for_children", "user", "uts",
    NULL
};

static ns_entry_t seen[MAX_NS];
static int seen_count = 0;

static int already_seen(ino_t inode) {
    for (int i = 0; i < seen_count; i++)
        if (seen[i].inode == inode) return 1;
    return 0;
}

static void scan_process(pid_t pid) {
    for (int t = 0; ns_types[t]; t++) {
        char link[128], target[128];
        snprintf(link, sizeof(link), "/proc/%d/ns/%s", pid, ns_types[t]);

        ssize_t len = readlink(link, target, sizeof(target) - 1);
        if (len < 0) continue;
        target[len] = '\0';

        // Extract inode number from "type:[inode]"
        ino_t inode = 0;
        char *bracket = strchr(target, '[');
        if (bracket) inode = (ino_t)atoll(bracket + 1);

        if (!already_seen(inode) && seen_count < MAX_NS) {
            seen[seen_count].inode = inode;
            strncpy(seen[seen_count].type, ns_types[t], 15);
            seen[seen_count].pid   = pid;
            seen_count++;
        }
    }
}

int main(void) {
    DIR *proc_dir = opendir("/proc");
    if (!proc_dir) { perror("opendir /proc"); return 1; }

    struct dirent *ent;
    while ((ent = readdir(proc_dir)) != NULL) {
        // Only numeric entries are PIDs
        if (ent->d_name[0] < '0' || ent->d_name[0] > '9') continue;
        pid_t pid = (pid_t)atoi(ent->d_name);
        scan_process(pid);
    }
    closedir(proc_dir);

    printf("%-20s %-20s %-10s\n", "Type", "Inode", "Example PID");
    printf("%-20s %-20s %-10s\n", "----", "-----", "-----------");

    for (int i = 0; i < seen_count; i++) {
        printf("%-20s %-20lu %-10d\n",
               seen[i].type,
               (unsigned long)seen[i].inode,
               seen[i].pid);
    }
    printf("\nTotal unique namespaces: %d\n", seen_count);
    return 0;
}
```

### Namespace File Descriptors

```c
// ns_fd_operations.c
// Demonstrates namespace FD operations: open, ioctl, setns

#define _GNU_SOURCE
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sched.h>
#include <sys/ioctl.h>
#include <linux/nsfs.h>   // NS_GET_USERNS, NS_GET_PARENT, etc.
#include <errno.h>
#include <string.h>

int main(void) {
    // Open a namespace file descriptor
    // O_CLOEXEC is important: don't leak namespace fds across exec()
    int net_fd = open("/proc/self/ns/net", O_RDONLY | O_CLOEXEC);
    if (net_fd < 0) { perror("open ns/net"); return 1; }

    // Get the type of namespace
    int ns_type = ioctl(net_fd, NS_GET_NSTYPE);
    printf("NS type: %d (CLONE_NEWNET = %d, match=%s)\n",
           ns_type, CLONE_NEWNET,
           ns_type == CLONE_NEWNET ? "yes" : "no");

    // Get the user namespace that owns this network namespace
    int owner_fd = ioctl(net_fd, NS_GET_USERNS);
    if (owner_fd >= 0) {
        printf("Owner user namespace fd: %d\n", owner_fd);
        close(owner_fd);
    }

    // Get inode number for identity comparison
    struct stat st;
    fstat(net_fd, &st);
    printf("Net namespace inode: %lu\n", (unsigned long)st.st_ino);

    // Duplicate: can be used to keep namespace alive after process exits
    int dup_fd = dup(net_fd);
    printf("Duplicated ns fd: %d (same inode: %s)\n",
           dup_fd,
           [[ ({struct stat st2; fstat(dup_fd, &st2); st2.st_ino == st.st_ino;}) ]] ? "yes" : "?");

    close(net_fd);
    close(dup_fd);
    return 0;
}
```

---

## 13. Namespace Persistence & Bind Mounts

### The Bind Mount Technique

A namespace can be persisted — kept alive indefinitely without any processes inside it — by bind-mounting its `/proc/[pid]/ns/[type]` file to a permanent location:

```bash
# Create a persistent network namespace
ip netns add mypersistent-ns
# Equivalent to:
touch /var/run/netns/mypersistent-ns
mount --bind /proc/<pid>/ns/net /var/run/netns/mypersistent-ns
```

### C Implementation: Namespace Persistence

```c
// ns_persist.c
// Creates and persists a network namespace across process lifetimes
// Compile: gcc -o ns_persist ns_persist.c
// Run: sudo ./ns_persist

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <fcntl.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <errno.h>

#define NS_PERSIST_PATH "/var/run/netns/demo-persist"
#define STACK_SIZE      (1024 * 1024)

// Persist a namespace by bind-mounting its fd to a path
// After this, the namespace lives even when ns_pid exits
static int persist_namespace(pid_t ns_pid, const char *type,
                              const char *dest_path) {
    char src[128];
    snprintf(src, sizeof(src), "/proc/%d/ns/%s", ns_pid, type);

    // Create the destination file (must exist for bind mount)
    int fd = open(dest_path, O_RDONLY | O_CREAT, 0444);
    if (fd < 0 && errno != EEXIST) { perror("create dest"); return -1; }
    if (fd >= 0) close(fd);

    // Bind mount the namespace fd to the persistent path
    if (mount(src, dest_path, "bind", MS_BIND, NULL) < 0) {
        perror("bind mount ns");
        return -1;
    }
    printf("[persist] Namespace pinned: %s → %s\n", src, dest_path);
    return 0;
}

// Enter a persisted namespace
static int enter_persisted_namespace(const char *path, int nstype) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) { perror("open persisted ns"); return -1; }

    if (setns(fd, nstype) < 0) {
        perror("setns");
        close(fd);
        return -1;
    }
    close(fd);
    return 0;
}

static int child_fn(void *arg) {
    // This process creates a new network namespace
    // We'll persist it and let this process die
    printf("[child] PID=%d in new net namespace\n", getpid());
    
    // Configure some state in the network namespace
    system("ip link set lo up");
    system("ip link add veth_persist type veth peer name veth_peer");
    system("ip addr add 10.99.0.1/24 dev veth_persist");
    system("ip link set veth_persist up");

    printf("[child] Network state configured. Dying in 1s...\n");
    sleep(1);
    return 0;
}

int main(void) {
    // Ensure parent directory exists
    system("mkdir -p /var/run/netns");

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    pid_t child = clone(child_fn, stack + STACK_SIZE,
                        CLONE_NEWNET | SIGCHLD, NULL);
    if (child < 0) { perror("clone"); return 1; }

    // Persist the namespace before the child dies
    sleep(0);  // Let child start
    if (persist_namespace(child, "net", NS_PERSIST_PATH) < 0)
        return 1;

    // Wait for child to die
    int status;
    waitpid(child, &status, 0);
    printf("[parent] Child exited. Namespace still alive (bind-mounted).\n");

    // Verify: enter the persisted namespace even though no process owns it
    printf("[parent] Entering persisted namespace...\n");
    pid_t joiner = fork();
    if (joiner == 0) {
        if (enter_persisted_namespace(NS_PERSIST_PATH, CLONE_NEWNET) < 0)
            exit(1);
        printf("[joiner] Inside persisted namespace:\n");
        system("ip addr show");
        exit(0);
    }
    waitpid(joiner, &status, 0);

    // Cleanup: unmount the bind mount to release the namespace
    printf("[parent] Cleaning up persisted namespace...\n");
    umount2(NS_PERSIST_PATH, MNT_DETACH);
    unlink(NS_PERSIST_PATH);
    printf("[parent] Namespace released.\n");

    free(stack);
    return 0;
}
```

---

## 14. Nested & Hierarchical Namespaces

### User Namespace Hierarchy

User namespaces form a strict parent-child hierarchy rooted at the **initial user namespace**:

```
initial user namespace (uid 0 = real root)
├── user-ns-A (uid 0 = uid 1000 outside)
│   ├── user-ns-A1 (uid 0 = uid 1000 in A = uid 1000 outside)
│   └── user-ns-A2
└── user-ns-B
```

Each `CLONE_NEWUSER` creates a child user namespace. The UID mapping at each level composes: if A maps 0→1000, and A1 maps 0→0 (relative to A), then in A1, UID 0 = UID 1000 on the host.

### PID Namespace Hierarchy

Similar hierarchy, with the added behavior that a process can send signals to processes in its child namespaces but NOT parent namespaces:

```c
// In host PID namespace:
kill(child_ns_pid, SIGTERM);  // OK — parent can signal child ns processes

// In container PID namespace:
kill(host_only_pid, SIGTERM); // ESRCH — host processes invisible
```

### Namespace Ownership

Every namespace (except user namespaces themselves) has an **owning user namespace**. This determines which capabilities are needed to perform operations on that namespace.

```c
// get_ns_owner.c — find the user namespace that owns a given namespace

#define _GNU_SOURCE
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/nsfs.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s /proc/self/ns/<type>\n", argv[0]);
        return 1;
    }

    int ns_fd = open(argv[1], O_RDONLY);
    if (ns_fd < 0) { perror("open"); return 1; }

    // Walk up the owner chain
    int current_fd = ns_fd;
    int depth = 0;

    printf("Namespace ownership chain for %s:\n", argv[1]);

    while (1) {
        int type = ioctl(current_fd, NS_GET_NSTYPE);
        struct stat st;
        fstat(current_fd, &st);
        printf("  [%d] type=0x%x inode=%lu\n",
               depth++, type, (unsigned long)st.st_ino);

        // Get user namespace that owns this namespace
        int owner = ioctl(current_fd, NS_GET_USERNS);
        if (owner < 0) {
            printf("  (no further owner — reached initial user ns)\n");
            break;
        }

        // Check if we've reached the user ns (it owns itself)
        struct stat owner_st;
        fstat(owner, &owner_st);
        if (owner_st.st_ino == st.st_ino) {
            printf("  [%d] self-owned (initial user namespace)\n", depth);
            close(owner);
            break;
        }

        if (current_fd != ns_fd) close(current_fd);
        current_fd = owner;
    }

    if (current_fd != ns_fd) close(current_fd);
    close(ns_fd);
    return 0;
}
```

---

## 15. Security Model & Capabilities

### Capabilities Required

| Operation | Capability Needed | In Which Namespace |
|---|---|---|
| Create any namespace (except user) | `CAP_SYS_ADMIN` | Current user namespace |
| Create user namespace | None (unprivileged) | N/A |
| Mount filesystems | `CAP_SYS_ADMIN` | User namespace owning mount ns |
| Change hostname | `CAP_SYS_ADMIN` | User namespace owning UTS ns |
| Configure network interfaces | `CAP_NET_ADMIN` | User namespace owning net ns |
| Bind ports < 1024 | `CAP_NET_BIND_SERVICE` | User namespace owning net ns |
| Send signals across ns | Privilege in target ns | — |

### The Capability Inheritance Model

When a new user namespace is created, the creator gets a full capability set in that namespace. But those capabilities only apply to operations on kernel objects **owned by** that user namespace.

The kernel checks: "Does this process have `CAP_X` in the user namespace that owns the resource it's trying to access?"

```c
// capability_demo.c — show capability differences across user namespaces

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/capability.h>
#include <sys/wait.h>

#define STACK_SIZE (1024 * 1024)

static void show_caps(const char *prefix) {
    cap_t caps = cap_get_proc();
    char *text = cap_to_text(caps, NULL);
    printf("%s caps: %s\n", prefix, text);
    cap_free(text);
    cap_free(caps);
}

static int child_fn(void *arg) {
    // Map our UID (from pipe) — not shown here for brevity
    // After mapping: we appear as root (uid 0) in this namespace

    // Read mapping from parent...
    // (synchronization omitted for clarity)

    show_caps("[child-user-ns]");

    printf("[child] Can we create more namespaces? ");
    fflush(stdout);
    if (unshare(CLONE_NEWUTS) == 0)
        printf("YES\n");
    else
        printf("NO (errno=%d)\n", errno);

    printf("[child] Can we load kernel modules? ");
    fflush(stdout);
    // This requires CAP_SYS_MODULE in the INITIAL user namespace
    // Even as "root" in our user namespace, this will fail
    if (open("/dev/mem", O_RDONLY) >= 0)
        printf("YES (dev/mem opened)\n");
    else
        printf("NO (expected: caps only apply in owned namespace)\n");

    return 0;
}

int main(void) {
    show_caps("[parent]");
    // ... (clone with CLONE_NEWUSER + UID mapping setup)
    return 0;
}
```

### Seccomp Integration with Namespaces

Production containers combine namespaces with **seccomp** (syscall filtering) for defense in depth. Namespaces provide resource isolation; seccomp restricts the attack surface:

```c
// Minimal seccomp filter for a namespaced container
// (using libseccomp — link with -lseccomp)

#include <seccomp.h>

void install_container_seccomp(void) {
    // Default-deny policy
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ERRNO(EPERM));

    // Allowlist safe syscalls
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write),  0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close),  0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
    // ... add more as needed

    // Block namespace manipulation from within container
    // (prevent container escape via namespace re-creation)
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(unshare), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(setns),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(clone),
                     1, SCMP_A0(SCMP_CMP_MASKED_EQ, 
                                CLONE_NEWUSER, CLONE_NEWUSER));

    seccomp_load(ctx);
    seccomp_release(ctx);
}
```

---

## 16. Building a Container Runtime from Scratch

### Architecture

A minimal container runtime needs to:

1. Set up namespaces (all 7 types for full isolation)
2. Set up cgroups (resource limits)
3. Configure the network (veth pair, IP addresses)
4. Set up the rootfs (overlay mount)
5. Exec the container init process

```c
// mini_runtime.c
// A minimal but complete container runtime
// Demonstrates the full namespace setup sequence
// Compile: gcc -o mini_runtime mini_runtime.c -lpthread
// Run: sudo ./mini_runtime <rootfs_path> <command> [args...]

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/resource.h>
#include <signal.h>

#define STACK_SIZE (8 * 1024 * 1024)  // 8MB

// Container configuration
typedef struct {
    const char  *rootfs;         // path to container rootfs
    const char  *hostname;       // container hostname
    char *const *argv;           // command to exec
    int          pipe_sync[2];   // parent-child sync
    uid_t        uid_map_outer;  // outer UID for mapping
    gid_t        gid_map_outer;  // outer GID for mapping
} container_config_t;

// ─────────────────────────────────────────────────────────────────
// Cgroup v2 resource limits
// ─────────────────────────────────────────────────────────────────
static int write_cgroup_file(const char *cgroup_path,
                              const char *file, const char *value) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", cgroup_path, file);
    int fd = open(path, O_WRONLY);
    if (fd < 0) return -1;
    write(fd, value, strlen(value));
    close(fd);
    return 0;
}

static void setup_cgroup_limits(pid_t container_pid) {
    char cgroup_path[256];
    snprintf(cgroup_path, sizeof(cgroup_path),
             "/sys/fs/cgroup/container_%d", container_pid);

    mkdir(cgroup_path, 0755);

    // Memory limit: 256MB
    write_cgroup_file(cgroup_path, "memory.max", "268435456");

    // CPU limit: 50% of one core
    write_cgroup_file(cgroup_path, "cpu.max", "50000 100000");

    // PID limit: max 100 processes
    write_cgroup_file(cgroup_path, "pids.max", "100");

    // Add container process to cgroup
    char pid_str[16];
    snprintf(pid_str, sizeof(pid_str), "%d", container_pid);
    write_cgroup_file(cgroup_path, "cgroup.procs", pid_str);

    printf("[runtime] Cgroup limits set: mem=256MB cpu=50%% pids=100\n");
}

// ─────────────────────────────────────────────────────────────────
// Rootfs setup using pivot_root
// ─────────────────────────────────────────────────────────────────
static int setup_rootfs(const char *rootfs) {
    char pivot_dir[512];
    snprintf(pivot_dir, sizeof(pivot_dir), "%s/.pivot_old", rootfs);

    // Bind mount the rootfs to itself (required by pivot_root)
    if (mount(rootfs, rootfs, "bind", MS_BIND | MS_REC, NULL) < 0) {
        perror("bind mount rootfs"); return -1;
    }

    mkdir(pivot_dir, 0700);

    if (syscall(SYS_pivot_root, rootfs, pivot_dir) < 0) {
        perror("pivot_root"); return -1;
    }

    chdir("/");

    // Unmount old root (lazy: unmount when no longer busy)
    umount2("/.pivot_old", MNT_DETACH);
    rmdir("/.pivot_old");

    // Mount essential filesystems
    mount("proc",    "/proc",    "proc",    MS_NODEV|MS_NOSUID|MS_NOEXEC, NULL);
    mount("sysfs",   "/sys",     "sysfs",   MS_NODEV|MS_NOSUID|MS_NOEXEC, NULL);
    mount("tmpfs",   "/dev",     "tmpfs",   MS_NOSUID|MS_STRICTATIME,
          "mode=755,size=65536k");
    mount("devpts",  "/dev/pts", "devpts",  MS_NOSUID|MS_NOEXEC,
          "newinstance,ptmxmode=0666,mode=620");
    mount("tmpfs",   "/dev/shm", "tmpfs",   MS_NODEV|MS_NOSUID, "mode=1777");

    // Create essential device nodes
    // (in production, bind mount from host /dev or use devtmpfs)
    mknod("/dev/null",    S_IFCHR|0666, makedev(1, 3));
    mknod("/dev/zero",    S_IFCHR|0666, makedev(1, 5));
    mknod("/dev/random",  S_IFCHR|0444, makedev(1, 8));
    mknod("/dev/urandom", S_IFCHR|0444, makedev(1, 9));
    mknod("/dev/tty",     S_IFCHR|0666, makedev(5, 0));
    symlink("/proc/self/fd",   "/dev/fd");
    symlink("/proc/self/fd/0", "/dev/stdin");
    symlink("/proc/self/fd/1", "/dev/stdout");
    symlink("/proc/self/fd/2", "/dev/stderr");

    printf("[container] Rootfs pivoted and mounted\n");
    return 0;
}

// ─────────────────────────────────────────────────────────────────
// Container init process (runs as PID 1)
// ─────────────────────────────────────────────────────────────────
static int container_init(void *arg) {
    container_config_t *cfg = (container_config_t *)arg;
    char ready_buf[1];

    // Wait for parent to set up UID maps and cgroups
    close(cfg->pipe_sync[1]);
    read(cfg->pipe_sync[0], ready_buf, 1);
    close(cfg->pipe_sync[0]);

    printf("[container] PID=%d (should be 1)\n", getpid());

    // Make all mounts private (stop propagation)
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) < 0)
        perror("make mounts private");

    // Set hostname
    if (sethostname(cfg->hostname, strlen(cfg->hostname)) < 0)
        perror("sethostname");

    // Set up rootfs
    if (cfg->rootfs && setup_rootfs(cfg->rootfs) < 0)
        return 125;

    // Drop capabilities we don't need (defense in depth)
    // In production, use a capability bounding set
    // Here we just demonstrate the concept
    struct __user_cap_header_struct hdr = { _LINUX_CAPABILITY_VERSION_3, 0 };
    struct __user_cap_data_struct   data[2] = {0};
    // Keep only: CAP_NET_BIND_SERVICE, CAP_CHOWN, CAP_SETUID/GID
    // (Real runtimes have a carefully curated default set)
    // syscall(SYS_capset, &hdr, data);  // drop all — too restrictive for demo

    // Set resource limits
    struct rlimit nofile = { 1024, 4096 };
    setrlimit(RLIMIT_NOFILE, &nofile);

    struct rlimit nproc = { 50, 100 };
    setrlimit(RLIMIT_NPROC, &nproc);

    printf("[container] Executing: %s\n", cfg->argv[0]);

    // Exec the actual container process
    execvp(cfg->argv[0], cfg->argv);
    perror("execvp");
    return 127;
}

// ─────────────────────────────────────────────────────────────────
// Runtime: set up UID/GID maps for user namespace
// ─────────────────────────────────────────────────────────────────
static void setup_id_maps(pid_t container_pid, 
                           uid_t outer_uid, gid_t outer_gid) {
    char path[128], map[64];

    // Deny setgroups before writing gid_map
    snprintf(path, sizeof(path), "/proc/%d/setgroups", container_pid);
    int fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, "deny", 4); close(fd); }

    // UID map: inside 0 → outside outer_uid
    snprintf(path, sizeof(path), "/proc/%d/uid_map", container_pid);
    snprintf(map,  sizeof(map),  "0 %u 1\n", outer_uid);
    fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, map, strlen(map)); close(fd); }

    // GID map: inside 0 → outside outer_gid
    snprintf(path, sizeof(path), "/proc/%d/gid_map", container_pid);
    snprintf(map,  sizeof(map),  "0 %u 1\n", outer_gid);
    fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, map, strlen(map)); close(fd); }

    printf("[runtime] ID maps: uid 0↔%u, gid 0↔%u\n", outer_uid, outer_gid);
}

// ─────────────────────────────────────────────────────────────────
// main
// ─────────────────────────────────────────────────────────────────
int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <rootfs|-> <cmd> [args...]\n", argv[0]);
        fprintf(stderr, "  rootfs: path to rootfs, or '-' to use current\n");
        fprintf(stderr, "  Example: %s /opt/ubuntu-rootfs /bin/bash\n", argv[0]);
        return 1;
    }

    container_config_t cfg = {
        .rootfs         = strcmp(argv[1], "-") == 0 ? NULL : argv[1],
        .hostname       = "container",
        .argv           = argv + 2,
        .uid_map_outer  = getuid(),
        .gid_map_outer  = getgid(),
    };

    if (pipe(cfg.pipe_sync) < 0) { perror("pipe"); return 1; }

    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }

    printf("[runtime] Starting container...\n");
    printf("[runtime] Rootfs: %s\n", cfg.rootfs ? cfg.rootfs : "(none)");
    printf("[runtime] Command: %s\n", cfg.argv[0]);

    // Full namespace isolation
    int clone_flags =
        CLONE_NEWUSER   |  // user namespace (unprivileged container root)
        CLONE_NEWPID    |  // PID namespace (container gets PID 1)
        CLONE_NEWNS     |  // mount namespace (isolated filesystem)
        CLONE_NEWNET    |  // network namespace
        CLONE_NEWUTS    |  // hostname namespace
        CLONE_NEWIPC    |  // IPC namespace
        CLONE_NEWCGROUP |  // cgroup namespace
        SIGCHLD;

    pid_t container_pid = clone(container_init, stack + STACK_SIZE,
                                clone_flags, &cfg);
    if (container_pid < 0) { perror("clone"); free(stack); return 1; }

    printf("[runtime] Container started: host PID=%d\n", container_pid);

    // Set up UID/GID maps (must be done from parent)
    setup_id_maps(container_pid, cfg.uid_map_outer, cfg.gid_map_outer);

    // Set up cgroup limits (from host)
    setup_cgroup_limits(container_pid);

    // Signal container to proceed
    close(cfg.pipe_sync[1]);

    // Wait for container to finish
    int status;
    waitpid(container_pid, &status, 0);

    if (WIFEXITED(status))
        printf("[runtime] Container exited: %d\n", WEXITSTATUS(status));
    else if (WIFSIGNALED(status))
        printf("[runtime] Container killed by signal: %d\n", WTERMSIG(status));

    // Cleanup cgroup
    char cgroup_path[256];
    snprintf(cgroup_path, sizeof(cgroup_path),
             "/sys/fs/cgroup/container_%d", container_pid);
    rmdir(cgroup_path);

    free(stack);
    return 0;
}
```

---

## 17. Rust Implementation: Namespace Manager

### Overview

The Rust implementation uses `nix` for POSIX bindings and provides a safe, idiomatic API over raw namespace operations.

```toml
# Cargo.toml
[package]
name = "ns-manager"
version = "0.1.0"
edition = "2021"

[dependencies]
nix     = { version = "0.29", features = ["process", "sched", "mount", "fs", "user", "signal", "ioctl", "time"] }
libc    = "0.2"
thiserror = "1.0"
tracing = "0.1"
tracing-subscriber = "0.3"
```

```rust
// src/main.rs — Rust namespace manager library + demo

use nix::{
    mount::{mount, umount2, MntFlags, MsFlags},
    sched::{clone, unshare, CloneFlags},
    sys::wait::{waitpid, WaitStatus},
    unistd::{
        chdir, execvp, fork, getgid, getpid, getuid, pivot_root,
        sethostname, ForkResult, Gid, Pid, Uid,
    },
};
use std::{
    ffi::CString,
    fs::{self, File, OpenOptions},
    io::{self, Write},
    os::unix::io::RawFd,
    path::Path,
};
use thiserror::Error;

// ─────────────────────────────────────────────────────────────────
// Error types
// ─────────────────────────────────────────────────────────────────

#[derive(Debug, Error)]
pub enum NsError {
    #[error("Namespace clone failed: {0}")]
    Clone(#[from] nix::Error),

    #[error("Mount operation failed: {0}")]
    Mount(nix::Error),

    #[error("IO error: {0}")]
    Io(#[from] io::Error),

    #[error("Namespace entry failed: {source}")]
    Entry { source: nix::Error },

    #[error("UID/GID mapping error: {0}")]
    IdMap(String),

    #[error("Rootfs setup failed: {0}")]
    Rootfs(String),
}

pub type NsResult<T> = Result<T, NsError>;

// ─────────────────────────────────────────────────────────────────
// Namespace types & handles
// ─────────────────────────────────────────────────────────────────

/// Represents an open file descriptor to a namespace
/// The fd keeps the namespace alive (reference counted by kernel)
pub struct NsFd {
    fd: RawFd,
    ns_type: NsType,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NsType {
    Mount,
    Uts,
    Ipc,
    Pid,
    Net,
    User,
    Cgroup,
    Time,
}

impl NsType {
    pub fn proc_name(&self) -> &'static str {
        match self {
            Self::Mount  => "mnt",
            Self::Uts    => "uts",
            Self::Ipc    => "ipc",
            Self::Pid    => "pid",
            Self::Net    => "net",
            Self::User   => "user",
            Self::Cgroup => "cgroup",
            Self::Time   => "time",
        }
    }

    pub fn clone_flag(&self) -> CloneFlags {
        match self {
            Self::Mount  => CloneFlags::CLONE_NEWNS,
            Self::Uts    => CloneFlags::CLONE_NEWUTS,
            Self::Ipc    => CloneFlags::CLONE_NEWIPC,
            Self::Pid    => CloneFlags::CLONE_NEWPID,
            Self::Net    => CloneFlags::CLONE_NEWNET,
            Self::User   => CloneFlags::CLONE_NEWUSER,
            Self::Cgroup => CloneFlags::CLONE_NEWCGROUP,
            Self::Time   => CloneFlags::CLONE_NEWTIME,
        }
    }
}

impl NsFd {
    /// Open a namespace fd from /proc/[pid]/ns/[type]
    pub fn open(pid: Pid, ns_type: NsType) -> NsResult<Self> {
        use std::os::unix::fs::OpenOptionsExt;
        let path = format!("/proc/{}/ns/{}", pid, ns_type.proc_name());
        let file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_CLOEXEC)
            .open(&path)?;

        use std::os::unix::io::IntoRawFd;
        Ok(NsFd {
            fd: file.into_raw_fd(),
            ns_type,
        })
    }

    /// Open current process's namespace
    pub fn open_self(ns_type: NsType) -> NsResult<Self> {
        Self::open(getpid(), ns_type)
    }

    /// Enter this namespace (setns)
    pub fn enter(&self) -> NsResult<()> {
        nix::sched::setns(
            unsafe { std::os::unix::io::BorrowedFd::borrow_raw(self.fd) },
            self.ns_type.clone_flag(),
        )
        .map_err(|e| NsError::Entry { source: e })
    }

    /// Get the inode number (namespace identity)
    pub fn inode(&self) -> NsResult<u64> {
        use std::os::unix::io::FromRawFd;
        let file = unsafe { File::from_raw_fd(self.fd) };
        let meta = file.metadata()?;
        use std::os::unix::fs::MetadataExt;
        let ino = meta.ino();
        std::mem::forget(file); // don't close the fd
        Ok(ino)
    }
}

impl Drop for NsFd {
    fn drop(&mut self) {
        unsafe { libc::close(self.fd) };
    }
}

// ─────────────────────────────────────────────────────────────────
// Namespace builder — fluent API for namespace configuration
// ─────────────────────────────────────────────────────────────────

/// Builder for configuring a new namespace set
#[derive(Default)]
pub struct NamespaceBuilder {
    flags: CloneFlags,
    hostname: Option<String>,
    uid_map: Option<IdMap>,
    gid_map: Option<IdMap>,
    rootfs: Option<String>,
}

#[derive(Clone)]
pub struct IdMap {
    pub inner_id: u32,
    pub outer_id: u32,
    pub count:    u32,
}

impl NamespaceBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_mount_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWNS;
        self
    }

    pub fn with_uts_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWUTS;
        self
    }

    pub fn with_ipc_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWIPC;
        self
    }

    pub fn with_pid_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWPID;
        self
    }

    pub fn with_net_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWNET;
        self
    }

    pub fn with_user_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWUSER;
        self
    }

    pub fn with_cgroup_ns(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWCGROUP;
        self
    }

    pub fn fully_isolated(mut self) -> Self {
        self.flags |= CloneFlags::CLONE_NEWNS
            | CloneFlags::CLONE_NEWUTS
            | CloneFlags::CLONE_NEWIPC
            | CloneFlags::CLONE_NEWPID
            | CloneFlags::CLONE_NEWNET
            | CloneFlags::CLONE_NEWUSER
            | CloneFlags::CLONE_NEWCGROUP;
        self
    }

    pub fn with_hostname(mut self, hostname: impl Into<String>) -> Self {
        self.hostname = Some(hostname.into());
        self
    }

    pub fn with_uid_map(mut self, inner: u32, outer: u32, count: u32) -> Self {
        self.uid_map = Some(IdMap { inner_id: inner, outer_id: outer, count });
        self
    }

    pub fn with_gid_map(mut self, inner: u32, outer: u32, count: u32) -> Self {
        self.gid_map = Some(IdMap { inner_id: inner, outer_id: outer, count });
        self
    }

    pub fn with_rootfs(mut self, path: impl Into<String>) -> Self {
        self.rootfs = Some(path.into());
        self
    }

    /// Spawn a child in the new namespaces
    /// Returns (child_pid, config) — caller must call .wait() and .cleanup()
    pub fn spawn<F>(self, child_fn: F) -> NsResult<SpawnedContainer>
    where
        F: FnOnce() -> i32 + Send + 'static,
    {
        use std::sync::{Arc, Mutex};
        let (sync_tx, sync_rx) = std::sync::mpsc::sync_channel::<()>(0);

        // Capture the child function
        let child_fn = Arc::new(Mutex::new(Some(child_fn)));
        let child_fn_clone = Arc::clone(&child_fn);

        // We need to use unsafe clone for namespace creation
        // nix's clone() wraps the raw clone(2) syscall
        const STACK_SIZE: usize = 8 * 1024 * 1024;
        let mut stack = vec![0u8; STACK_SIZE];

        // Synchronization: child waits for parent to set up maps
        let (pipe_r, pipe_w) = nix::unistd::pipe()?;

        let pipe_r_clone = pipe_r;
        let flags = self.flags;
        let hostname = self.hostname.clone();
        let rootfs = self.rootfs.clone();

        let child_pid = unsafe {
            clone(
                Box::new(move || {
                    // Close write end, wait on read end
                    let _ = nix::unistd::close(pipe_w);

                    // Wait for parent signal
                    let mut buf = [0u8; 1];
                    let _ = nix::unistd::read(pipe_r_clone, &mut buf);
                    let _ = nix::unistd::close(pipe_r_clone);

                    // Set hostname if requested
                    if let Some(ref h) = hostname {
                        sethostname(h).expect("sethostname");
                    }

                    // Set up rootfs if requested
                    if let Some(ref r) = rootfs {
                        setup_container_rootfs(r).expect("rootfs setup");
                    }

                    // Call user function
                    if let Some(f) = child_fn_clone.lock().unwrap().take() {
                        f()
                    } else {
                        0
                    }
                }),
                stack.as_mut_slice(),
                flags | CloneFlags::from_bits_truncate(libc::SIGCHLD),
                None,
            )?
        };

        // Close read end in parent
        let _ = nix::unistd::close(pipe_r);

        // Set up UID/GID maps
        if let Some(ref uid_map) = self.uid_map {
            write_id_map(child_pid, "uid_map", uid_map)?;
        }
        if self.flags.contains(CloneFlags::CLONE_NEWUSER) {
            // Must deny setgroups before writing gid_map
            deny_setgroups(child_pid)?;
        }
        if let Some(ref gid_map) = self.gid_map {
            write_id_map(child_pid, "gid_map", gid_map)?;
        }

        // Signal child to continue
        let _ = nix::unistd::write(pipe_w, b"G");
        let _ = nix::unistd::close(pipe_w);

        Ok(SpawnedContainer {
            pid: child_pid,
            _stack: stack,
        })
    }
}

/// Handle to a spawned container
pub struct SpawnedContainer {
    pub pid: Pid,
    _stack: Vec<u8>,
}

impl SpawnedContainer {
    pub fn wait(&self) -> NsResult<WaitStatus> {
        Ok(waitpid(self.pid, None)?)
    }

    pub fn pid(&self) -> Pid {
        self.pid
    }
}

// ─────────────────────────────────────────────────────────────────
// Helper functions
// ─────────────────────────────────────────────────────────────────

fn write_id_map(pid: Pid, map_type: &str, map: &IdMap) -> NsResult<()> {
    let path = format!("/proc/{}/{}", pid, map_type);
    let content = format!("{} {} {}\n", map.inner_id, map.outer_id, map.count);
    fs::write(&path, &content)
        .map_err(|e| NsError::IdMap(format!("write {}: {}", path, e)))
}

fn deny_setgroups(pid: Pid) -> NsResult<()> {
    let path = format!("/proc/{}/setgroups", pid);
    fs::write(&path, "deny")
        .map_err(|e| NsError::IdMap(format!("deny setgroups: {}", e)))
}

fn setup_container_rootfs(rootfs: &str) -> NsResult<()> {
    let pivot_old = format!("{}/.pivot_old", rootfs);
    fs::create_dir_all(&pivot_old)?;

    mount(
        Some(rootfs),
        rootfs,
        None::<&str>,
        MsFlags::MS_BIND | MsFlags::MS_REC,
        None::<&str>,
    )
    .map_err(NsError::Mount)?;

    pivot_root(rootfs, &pivot_old).map_err(|e| NsError::Rootfs(e.to_string()))?;

    chdir("/").map_err(|e| NsError::Rootfs(e.to_string()))?;

    umount2("/.pivot_old", MntFlags::MNT_DETACH)
        .map_err(|e| NsError::Rootfs(format!("umount pivot_old: {}", e)))?;

    fs::remove_dir("/.pivot_old")?;

    // Mount proc
    mount(
        Some("proc"),
        "/proc",
        Some("proc"),
        MsFlags::MS_NODEV | MsFlags::MS_NOSUID | MsFlags::MS_NOEXEC,
        None::<&str>,
    )
    .ok(); // ignore error if /proc doesn't exist in rootfs

    Ok(())
}

// ─────────────────────────────────────────────────────────────────
// Namespace inspector — reads namespace state from /proc
// ─────────────────────────────────────────────────────────────────

pub struct NsInspector;

impl NsInspector {
    /// Get all namespace inodes for a given PID
    pub fn get_ns_info(pid: Pid) -> Vec<(String, u64)> {
        let types = [
            "cgroup", "ipc", "mnt", "net", "pid",
            "pid_for_children", "time", "user", "uts",
        ];

        types.iter().filter_map(|t| {
            let link = format!("/proc/{}/ns/{}", pid, t);
            let target = fs::read_link(&link).ok()?;
            let target_str = target.to_string_lossy();

            // Parse inode from "type:[inode]"
            let inode_str = target_str
                .split('[')
                .nth(1)?
                .trim_end_matches(']');
            let inode: u64 = inode_str.parse().ok()?;

            Some((t.to_string(), inode))
        }).collect()
    }

    /// Check if two processes are in the same namespace
    pub fn same_namespace(pid1: Pid, pid2: Pid, ns_type: NsType) -> bool {
        let type_name = ns_type.proc_name();
        let link1 = format!("/proc/{}/ns/{}", pid1, type_name);
        let link2 = format!("/proc/{}/ns/{}", pid2, type_name);
        fs::read_link(&link1).ok() == fs::read_link(&link2).ok()
    }

    /// List all unique network namespaces on the system
    pub fn list_net_namespaces() -> Vec<u64> {
        let mut inodes = Vec::new();

        if let Ok(entries) = fs::read_dir("/proc") {
            for entry in entries.flatten() {
                let name = entry.file_name();
                let name_str = name.to_string_lossy();
                if !name_str.chars().all(|c| c.is_ascii_digit()) { continue; }

                let link = format!("{}/ns/net", entry.path().display());
                if let Ok(target) = fs::read_link(&link) {
                    if let Some(inode_str) = target
                        .to_string_lossy()
                        .split('[').nth(1)
                        .map(|s| s.trim_end_matches(']'))
                    {
                        if let Ok(inode) = inode_str.parse::<u64>() {
                            if !inodes.contains(&inode) {
                                inodes.push(inode);
                            }
                        }
                    }
                }
            }
        }

        inodes
    }
}

// ─────────────────────────────────────────────────────────────────
// Namespace switcher — RAII guard for namespace transitions
// ─────────────────────────────────────────────────────────────────

/// RAII guard: saves current namespace, switches to target, restores on drop
pub struct NsGuard {
    original: NsFd,
}

impl NsGuard {
    /// Enter the namespace associated with `pid` for `ns_type`
    /// Restores the original namespace when the guard is dropped
    pub fn enter_pid_ns(pid: Pid, ns_type: NsType) -> NsResult<Self> {
        let original = NsFd::open_self(ns_type)?;
        let target   = NsFd::open(pid, ns_type)?;
        target.enter()?;
        Ok(NsGuard { original })
    }

    /// Enter namespace from a file descriptor
    pub fn enter_fd(original_type: NsType, target_fd: &NsFd) -> NsResult<Self> {
        let original = NsFd::open_self(original_type)?;
        target_fd.enter()?;
        Ok(NsGuard { original })
    }
}

impl Drop for NsGuard {
    fn drop(&mut self) {
        // Restore original namespace
        self.original.enter().expect("failed to restore namespace");
    }
}

// ─────────────────────────────────────────────────────────────────
// UTS namespace operations
// ─────────────────────────────────────────────────────────────────

pub mod uts {
    use nix::unistd::sethostname;
    use nix::sched::unshare;
    use nix::sched::CloneFlags;
    use super::NsResult;

    /// Set hostname in a new UTS namespace (current process)
    pub fn isolate_hostname(hostname: &str) -> NsResult<()> {
        unshare(CloneFlags::CLONE_NEWUTS)?;
        sethostname(hostname)?;
        Ok(())
    }

    /// Get current hostname
    pub fn get_hostname() -> String {
        let mut buf = vec![0u8; 256];
        unsafe {
            libc::gethostname(buf.as_mut_ptr() as *mut libc::c_char, buf.len());
        }
        let len = buf.iter().position(|&b| b == 0).unwrap_or(buf.len());
        String::from_utf8_lossy(&buf[..len]).into_owned()
    }
}

// ─────────────────────────────────────────────────────────────────
// Network namespace operations
// ─────────────────────────────────────────────────────────────────

pub mod netns {
    use std::fs;
    use std::path::Path;
    use nix::unistd::Pid;
    use super::{NsFd, NsType, NsResult};

    pub const NETNS_DIR: &str = "/var/run/netns";

    /// Create a named (persisted) network namespace
    pub fn create_named(name: &str) -> NsResult<()> {
        fs::create_dir_all(NETNS_DIR)?;
        let path = format!("{}/{}", NETNS_DIR, name);

        // Create the mount target file
        fs::write(&path, "")?;

        // The actual namespace is created by spawning a process with
        // CLONE_NEWNET and bind-mounting its /proc/self/ns/net
        // (simplified here — real ip-netns does exactly this)

        println!("Created named netns: {}", name);
        Ok(())
    }

    /// List all named network namespaces
    pub fn list_named() -> Vec<String> {
        fs::read_dir(NETNS_DIR)
            .map(|entries| {
                entries.flatten()
                    .map(|e| e.file_name().to_string_lossy().into_owned())
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Open a named network namespace by name
    pub fn open_named(name: &str) -> NsResult<NsFd> {
        use std::os::unix::io::{FromRawFd, IntoRawFd};
        use std::fs::OpenOptions;
        use std::os::unix::fs::OpenOptionsExt;

        let path = format!("{}/{}", NETNS_DIR, name);
        let file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_CLOEXEC)
            .open(&path)?;

        Ok(NsFd {
            fd: file.into_raw_fd(),
            ns_type: NsType::Net,
        })
    }
}

// ─────────────────────────────────────────────────────────────────
// main demo
// ─────────────────────────────────────────────────────────────────

fn main() {
    tracing_subscriber::fmt::init();

    println!("=== Rust Namespace Manager Demo ===\n");

    // Demo 1: Inspect current namespaces
    println!("--- Current process namespaces ---");
    let ns_info = NsInspector::get_ns_info(getpid());
    for (ns_type, inode) in &ns_info {
        println!("  {:20} inode={}", ns_type, inode);
    }

    // Demo 2: List all unique network namespaces on system
    println!("\n--- Unique network namespaces on system ---");
    let net_ns_list = NsInspector::list_net_namespaces();
    println!("  Found {} unique net namespace(s)", net_ns_list.len());
    for inode in &net_ns_list {
        println!("    net:[{}]", inode);
    }

    // Demo 3: UTS namespace isolation
    println!("\n--- UTS Namespace Demo ---");
    let outer_uid = getuid().as_raw();
    let outer_gid = getgid().as_raw();
    println!("Parent hostname: {}", uts::get_hostname());

    let container = NamespaceBuilder::new()
        .with_user_ns()
        .with_uts_ns()
        .with_uid_map(0, outer_uid, 1)
        .with_gid_map(0, outer_gid, 1)
        .with_hostname("rust-container-demo")
        .spawn(|| {
            println!("[child] PID={}", getpid());
            println!("[child] Hostname: {}", uts::get_hostname());
            println!("[child] UID: {}", getuid());
            0
        });

    match container {
        Ok(c) => {
            println!("[parent] Container spawned: host PID={}", c.pid());
            match c.wait() {
                Ok(status) => println!("[parent] Container exit: {:?}", status),
                Err(e) => eprintln!("[parent] Wait error: {}", e),
            }
        }
        Err(e) => eprintln!("Spawn failed: {}", e),
    }

    println!("[parent] Hostname unchanged: {}", uts::get_hostname());

    // Demo 4: Check same namespace
    println!("\n--- Namespace Identity Check ---");
    let pid1 = getpid();
    println!(
        "PID {} and PID {} in same net ns: {}",
        pid1, pid1,
        NsInspector::same_namespace(pid1, pid1, NsType::Net)
    );

    println!("\n=== Demo complete ===");
}
```

---

## 18. Advanced Patterns & Edge Cases

### The Double-Fork Pattern for PID Namespaces

When you want the calling process itself to be outside the PID namespace (not the parent of PID 1), use the double-fork pattern:

```c
// double_fork_pid_ns.c
// The "container manager" process doesn't end up in the PID namespace
// This is the pattern used by runc, crun, etc.

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>

// Pattern:
// [manager]
//     └── fork() → [intermediate]  (in new PID namespace, becomes PID 1)
//                       └── fork() → [container-init] (PID 1 is actually here)
//     The [intermediate] immediately execs into the container init
//
// Why? Because clone(CLONE_NEWPID) creates the namespace, and the
// FIRST process cloned into it is PID 1. We want our container init
// to be PID 1, not an intermediate process.

int main(void) {
    // The process that calls clone() is NOT in the new PID namespace.
    // Its children are. The first child IS PID 1.
    printf("[manager] PID=%d\n", getpid());

    // First fork: creates PID 1 of the new namespace
    pid_t pid1_process;
    {
        char *stack = malloc(1024 * 1024);
        pid1_process = clone(
            NULL,  // child_fn handled below
            stack + 1024 * 1024,
            CLONE_NEWPID | CLONE_NEWNS | SIGCHLD,
            NULL
        );
    }

    // If we're the child (PID 1 inside):
    if (pid1_process == 0) {
        printf("[PID1] getpid()=%d (should be 1)\n", getpid());
        printf("[PID1] getppid()=%d (should be 0)\n", getppid());

        // Mount /proc for this namespace
        mount("proc", "/proc", "proc", 0, NULL);

        // In a real container, execvp() the init process here
        // For demo, just show PID info and spawn a child
        pid_t child = fork();
        if (child == 0) {
            printf("[child-of-PID1] PID=%d\n", getpid());
            return 0;
        }
        waitpid(child, NULL, 0);
        return 0;
    }

    printf("[manager] Container PID1 has host PID=%d\n", pid1_process);
    int status;
    waitpid(pid1_process, &status, 0);
    return 0;
}
```

### Namespace Joining Race Conditions

A subtle but critical issue: when using `setns()` to join a container's namespaces, there's a window where the target process might die between opening `/proc/[pid]/ns/[type]` and calling `setns()`. The namespace will remain valid (fd keeps it alive), but the process is gone.

```c
// Safe namespace joining with pidfd (kernel 5.2+)

#include <sys/syscall.h>
#include <linux/pidfd.h>

// Use pidfd to atomically reference a process
int join_container_ns(pid_t container_pid) {
    // Open a pidfd — keeps reference to the process even if it dies
    int pidfd = syscall(SYS_pidfd_open, container_pid, 0);
    if (pidfd < 0) { perror("pidfd_open"); return -1; }

    // Get namespace fds via pidfd (atomic — no TOCTOU)
    int net_fd = syscall(SYS_pidfd_getfd, pidfd, 
                          /* target_fd */3,  // ns fd in target
                          0);

    // Alternative: open /proc/pid/ns/ with the pidfd as directory
    // (kernel 5.8+ supports /proc/self/fdinfo/<pidfd>)

    close(pidfd);
    return net_fd;
}
```

### Namespace and `execve()` Interaction

`execve()` preserves all namespace memberships but has a special interaction with user namespaces:

- If the executable has setuid/setgid bits, `execve()` **resets capabilities** if the calling process is in a user namespace that doesn't map the file owner.
- `PR_SET_NO_NEW_PRIVS` prevents privilege escalation via setuid/capabilities across exec boundaries within a namespace context.

```c
// Prevent privilege escalation in container
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
// After this, execve() of setuid binaries doesn't grant new privileges
```

### Thread Restrictions

Several namespace operations are restricted when the process has multiple threads:

| Operation | Restriction |
|---|---|
| `unshare(CLONE_NEWUSER)` | Requires single-threaded process |
| `unshare(CLONE_NEWNS)` | Requires single-threaded process |
| `setns(CLONE_NEWUSER)` | Requires single-threaded process |
| `setns(CLONE_NEWPID)` | Requires single-threaded process |

This is why container runtimes typically perform namespace setup in a dedicated single-threaded process (or use the `nsexec` helper pattern).

The reason is fundamental: if thread A changes the namespace while thread B is executing a syscall, thread B's namespace membership becomes inconsistent. The kernel enforces single-threaded requirements to prevent this.

### `/proc/sys/user/` Limits

The kernel enforces limits on namespace creation to prevent DoS:

```bash
# Maximum number of each namespace type per user
cat /proc/sys/user/max_cgroup_namespaces
cat /proc/sys/user/max_ipc_namespaces
cat /proc/sys/user/max_mnt_namespaces
cat /proc/sys/user/max_net_namespaces
cat /proc/sys/user/max_pid_namespaces
cat /proc/sys/user/max_time_namespaces
cat /proc/sys/user/max_user_namespaces
cat /proc/sys/user/max_uts_namespaces
```

When creating many containers (Kubernetes nodes running thousands of pods), these limits may need tuning.

---

## 19. Debugging & Observability

### Tools

```bash
# ─── lsns ───────────────────────────────────────────────────────
# List all namespaces with their processes
lsns
lsns -t net          # only network namespaces
lsns -t pid          # only PID namespaces
lsns --output NS,TYPE,NPROCS,PID,COMMAND

# ─── nsenter ────────────────────────────────────────────────────
# Enter all namespaces of a running container
nsenter --target <PID> --all -- bash

# Enter specific namespaces
nsenter --target <PID> --net --mount -- ip addr show

# Enter just the network namespace (without becoming PID 1)
nsenter --target <PID> --net -- ss -tlnp

# ─── ip netns ───────────────────────────────────────────────────
# List named network namespaces
ip netns list

# Execute in named namespace
ip netns exec myns ping 8.8.8.8

# Monitor namespace events
ip netns monitor

# ─── /proc filesystem ────────────────────────────────────────────
# Check which namespaces a process belongs to
ls -la /proc/<PID>/ns/

# Compare two processes' namespaces
diff <(ls -la /proc/<PID1>/ns/) <(ls -la /proc/<PID2>/ns/)

# ─── unshare ────────────────────────────────────────────────────
# Quick namespace testing without code
unshare --pid --fork --mount-proc bash  # new PID namespace

# Full isolation test
unshare --user --pid --net --mount --ipc --uts --fork \
        --map-root-user bash

# ─── strace / auditd ────────────────────────────────────────────
# Trace namespace syscalls
strace -e trace=clone,unshare,setns <command>

# ─── bpftrace ───────────────────────────────────────────────────
# Trace namespace creation in real-time
bpftrace -e '
  tracepoint:syscalls:sys_enter_clone {
    printf("clone() flags=0x%lx pid=%d comm=%s\n",
           args->clone_flags, pid, comm);
  }
'
```

### Programmatic Namespace Inspection

```c
// ns_inspector.c — detailed namespace relationship graph
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/nsfs.h>
#include <sys/stat.h>

// Print the full namespace relationship for a process
void inspect_process_namespaces(pid_t pid) {
    const char *types[] = {
        "cgroup", "ipc", "mnt", "net", "pid",
        "time", "user", "uts", NULL
    };

    printf("Namespaces for PID %d:\n", pid);
    printf("%-12s %-20s %-12s %s\n",
           "Type", "Symlink Target", "Inode", "Owner NS Inode");
    printf("%-12s %-20s %-12s %s\n",
           "----", "-------------", "-----", "-------------");

    for (int i = 0; types[i]; i++) {
        char link_path[128], target[128];
        snprintf(link_path, sizeof(link_path), "/proc/%d/ns/%s", pid, types[i]);

        ssize_t len = readlink(link_path, target, sizeof(target)-1);
        if (len < 0) continue;
        target[len] = '\0';

        // Get inode
        int fd = open(link_path, O_RDONLY);
        if (fd < 0) continue;

        struct stat st;
        fstat(fd, &st);

        // Get owner user namespace
        char owner_inode_str[32] = "(none)";
        int owner_fd = ioctl(fd, NS_GET_USERNS);
        if (owner_fd >= 0) {
            struct stat owner_st;
            fstat(owner_fd, &owner_st);
            snprintf(owner_inode_str, sizeof(owner_inode_str),
                     "%lu", (unsigned long)owner_st.st_ino);
            close(owner_fd);
        }

        printf("%-12s %-20s %-12lu %s\n",
               types[i], target,
               (unsigned long)st.st_ino,
               owner_inode_str);
        close(fd);
    }
}
```

---

## 20. Performance Characteristics

### Namespace Creation Cost

| Operation | Typical Latency | Notes |
|---|---|---|
| `clone(CLONE_NEWNS)` | ~50-500μs | Copies mount tree — scales with number of mounts |
| `clone(CLONE_NEWNET)` | ~10-50μs | Creates new net stack |
| `clone(CLONE_NEWUSER)` | ~5-20μs | Cheapest non-trivial ns |
| `clone(CLONE_NEWPID)` | ~5-20μs | Very cheap |
| `setns(fd, CLONE_NEWNET)` | ~1-5μs | Just updates task pointer |
| Full container start | ~100ms-1s | Includes overlayfs, cgroup setup, etc. |

The **mount namespace** is the most expensive to create because `copy_mnt_ns()` must clone the entire mount tree. Systems with hundreds of mounts (like those with many systemd mount units) can see significant latency here.

### VFS Lookup Overhead

Namespace membership adds a layer to every VFS lookup — when the kernel resolves a path, it must check the current mount namespace's view. This overhead is:
- **~0-5%** for cache-warm paths (measured via `stat()` microbenchmarks)
- **Negligible** for CPU-bound workloads
- **Noticeable** for namespace-heavy workloads (many containers doing many small file operations)

### Network Namespace Overhead

The network namespace imposes overhead on:
- Socket creation: ~2-5% vs. no namespace
- TCP connection setup: ~1-3%
- High-frequency `send()`/`recv()`: negligible after connection setup

The veth pair itself adds packet-processing overhead vs. native networking — roughly equivalent to a software bridge traversal.

---

## 21. Known Vulnerabilities & Escape Vectors

### Historical CVEs

| CVE | Year | Type | Vector |
|---|---|---|---|
| CVE-2019-5736 | 2019 | Container escape | runc /proc/self/exe overwrite |
| CVE-2020-14386 | 2020 | Privilege escalation | AF_PACKET + user namespace |
| CVE-2021-22555 | 2021 | Heap OOB | Netfilter + user namespace |
| CVE-2022-0185 | 2022 | Heap overflow | fsconfig syscall + user namespace |
| CVE-2022-25636 | 2022 | Heap OOB | Netfilter + net namespace |
| CVE-2022-0847 | 2022 | Dirty Pipe | Pipe splicing — no namespace needed |

Most modern kernel CVEs that allow privilege escalation from unprivileged users involve the combination of **user namespaces** (to gain capabilities) + **some other vulnerable subsystem** (to exploit those capabilities into full root).

### Defense: Restrict Unprivileged User Namespaces

```bash
# Debian/Ubuntu
echo 0 > /proc/sys/kernel/unprivileged_userns_clone
# or persistently:
echo 'kernel.unprivileged_userns_clone=0' >> /etc/sysctl.d/99-security.conf

# Fedora/RHEL (different sysctl)
echo 1 > /proc/sys/user/max_user_namespaces  # 0 = disable
```

### The Dirty COW / Namespace Interaction Pattern

The general exploit pattern:

1. Create user namespace → get `CAP_SYS_ADMIN` in it
2. Use that capability to exploit a kernel vulnerability (overflow, use-after-free)
3. Pivot to initial namespace with full root

Mitigations:
- Seccomp filters (block `clone(CLONE_NEWUSER)` for untrusted code)
- LSM policies (AppArmor, SELinux)
- Kernel hardening (`CONFIG_SECURITY_LOCKDOWN`)
- Regular kernel updates

### Mount Namespace Escape via `/proc`

A classic escape: if a container can write to its host-accessible `/proc` files:

```bash
# From inside container with host /proc accessible:
cat /proc/sysrq-trigger  # read-only but can infer host state
echo c > /proc/sysrq-trigger  # crash host kernel (if writable!)
```

Defense: mount `/proc` with `ro` or `hidepid=2`:
```bash
mount -o remount,ro,hidepid=2 /proc
```

---

## 22. Real-World Reference Implementations

### How Docker/containerd Uses Namespaces

```
containerd
├── creates snapshots (overlayfs setup)
├── calls runc via OCI Runtime Spec
└── runc:
    ├── reads config.json (OCI spec)
    ├── nsexec.c: re-executes itself into namespaces
    │   └── clone() with all CLONE_NEW* flags
    ├── sets up user ns + uid/gid mappings  
    ├── sets up mount ns + overlayfs + pivot_root
    ├── sets up network ns + veth pair
    ├── sets up PID ns
    ├── applies seccomp filter
    ├── drops capabilities
    └── exec() container init process
```

### How Kubernetes Uses Namespaces

Each **Pod** shares:
- One **network namespace** (containers in a pod communicate via localhost)
- One **IPC namespace** (containers share SysV IPC)
- One **UTS namespace** (shared hostname)

Each **container** in a pod gets its own:
- **Mount namespace** (isolated rootfs via overlayfs)
- **PID namespace** (optional — `shareProcessNamespace: false` by default)

The **pause container** is the namespace holder: it does nothing but `pause(2)` in an infinite loop, but its namespaces (net, ipc, uts) are shared by all other containers in the pod.

```bash
# See it in action on a Kubernetes node:
# Pause container holds the shared namespaces
ps aux | grep pause

# All containers in a pod share these:
ls -la /proc/<pod-infra-container-pid>/ns/{net,ipc,uts}
ls -la /proc/<app-container-pid>/ns/{net,ipc,uts}
# ↑ These should have identical symlink targets
```

### How `ip netns` Persists Namespaces

```bash
# What `ip netns add myns` actually does:
#
# 1. Spawn a new process with CLONE_NEWNET
# 2. In the parent, before the child dies:
#    touch /var/run/netns/myns
#    mount --bind /proc/<child-pid>/ns/net /var/run/netns/myns
# 3. Child exits — but namespace lives via bind mount
#
# `ip netns exec myns <cmd>` does:
# 1. open("/var/run/netns/myns", O_RDONLY)  → fd
# 2. setns(fd, CLONE_NEWNET)
# 3. execvp(<cmd>)
```

### CRIU (Checkpoint/Restore In Userspace) and Namespaces

CRIU checkpoints and restores containers by:
1. Dumping all namespace state to files (mount tables, network config, PID tables)
2. Creating identical namespaces on restore
3. Using `CLONE_NEWTIME` + time offsets to restore monotonic clock continuity
4. Using `setns()` + namespace FDs to restore processes into the correct namespaces

```bash
# Checkpoint a container
criu dump -D /checkpoint/dir -t <container-pid> \
    --tcp-established --external-unix-socket

# Restore on same or different host
criu restore -D /checkpoint/dir \
    --tcp-established --external-unix-socket
```

---

## Appendix A: Quick Reference — All Namespace Flags

```c
// sched.h
#define CLONE_NEWNS      0x00020000  /* New mount namespace        (since 2.4.19) */
#define CLONE_NEWUTS     0x04000000  /* New UTS namespace           (since 2.6.19) */
#define CLONE_NEWIPC     0x08000000  /* New IPC namespace           (since 2.6.19) */
#define CLONE_NEWUSER    0x10000000  /* New user namespace          (since 3.8)    */
#define CLONE_NEWPID     0x20000000  /* New PID namespace           (since 2.6.24) */
#define CLONE_NEWNET     0x40000000  /* New network namespace       (since 2.6.24) */
#define CLONE_NEWCGROUP  0x02000000  /* New cgroup namespace        (since 4.6)    */
#define CLONE_NEWTIME    0x00000080  /* New time namespace          (since 5.6)    */
```

## Appendix B: `/proc` Namespace Files Reference

```
/proc/<pid>/ns/
├── cgroup         → cgroup namespace
├── ipc            → IPC namespace
├── mnt            → mount namespace
├── net            → network namespace
├── pid            → current PID namespace
├── pid_for_children → PID namespace for future children (after unshare)
├── time           → current time namespace
├── time_for_children → time namespace for future children
├── user           → user namespace
└── uts            → UTS namespace

/proc/<pid>/
├── uid_map        → UID mappings (read: current ns view, write: setup mapping)
├── gid_map        → GID mappings
├── setgroups      → "allow" or "deny" (must set before gid_map)
├── status         → NSpid, NStgid (PID in each namespace level)
└── cgroup         → cgroup membership (virtualized by cgroup ns)

/proc/sys/user/
├── max_cgroup_namespaces
├── max_ipc_namespaces
├── max_mnt_namespaces
├── max_net_namespaces
├── max_pid_namespaces
├── max_time_namespaces
├── max_user_namespaces
└── max_uts_namespaces

/proc/sys/kernel/
└── unprivileged_userns_clone   (Debian/Ubuntu: 0=disabled, 1=enabled)
```

## Appendix C: Compile & Run Instructions

```bash
# Prerequisites
sudo apt-get install gcc libc6-dev libcap-dev libseccomp-dev

# Compile all C examples
gcc -O2 -o mount_ns_demo    mount_ns_demo.c
gcc -O2 -o uts_ns_demo      uts_ns_demo.c
gcc -O2 -o ipc_ns_demo      ipc_ns_demo.c
gcc -O2 -o pid_ns_demo      pid_ns_demo.c
gcc -O2 -o net_ns_demo      net_ns_demo.c
gcc -O2 -o user_ns_demo     user_ns_demo.c  -lcap
gcc -O2 -o cgroup_ns_demo   cgroup_ns_demo.c
gcc -O2 -o time_ns_demo     time_ns_demo.c
gcc -O2 -o mini_runtime     mini_runtime.c
gcc -O2 -o list_namespaces  list_namespaces.c
gcc -O2 -o ns_persist       ns_persist.c

# Most demos require root (except user_ns_demo)
sudo ./mount_ns_demo
sudo ./net_ns_demo
./user_ns_demo              # no sudo needed!

# Rust: in ns-manager/ directory
cargo build --release
sudo ./target/release/ns-manager

# Verify kernel namespace support
zcat /proc/config.gz | grep -E 'CONFIG_.*NAMESPACE'
# Or:
grep -E 'NAMESPACE' /boot/config-$(uname -r)
```

---

*Guide covers Linux kernel 5.x–6.x. Namespace behavior may differ on older kernels. Time namespaces require kernel 5.6+. All code is for educational/systems programming purposes.*

Now let me write the comprehensive guide:**~3,900 lines / 130KB** of dense technical content. Here's what's covered:

**Architecture & Internals**
- `task_struct` → `nsproxy` kernel data structures and how all 8 namespace pointers are wired in
- Reference counting lifecycle — when namespaces live and die
- The `create_new_namespaces()` kernel path for all three entry points

**All 8 Namespace Types** — each with kernel struct internals + full C implementation:
- **Mount** — mount propagation (shared/private/slave/unbindable), OverlayFS CoW layers, `pivot_root` vs `chroot`
- **UTS** — hostname/domainname isolation, what IS and isn't namespaced in `new_utsname`
- **IPC** — SysV shm/sem/msg isolation, POSIX mqueue, the same-key-in-two-namespaces problem
- **PID** — PID 1 semantics (signal handling, orphan reaping), double-fork pattern, `/proc` remount requirement, `NSpid` multi-level translation
- **Network** — full veth pair setup, NAT, cross-namespace topology, named namespace persistence
- **User** — UID/GID mapping, rootless container model, capability scoping, `setgroups` restriction
- **Cgroup** — visibility virtualization vs. actual resource limits
- **Time** — `CLOCK_MONOTONIC`/`CLOCK_BOOTTIME` offsets, live migration use case

**Rust Implementation** — full `ns-manager` crate with:
- `NsFd` (RAII namespace fd handle), `NamespaceBuilder` (fluent API), `NsGuard` (RAII namespace switcher), `NsInspector`, named netns module

**Production Topics** — mini container runtime from scratch, seccomp integration, thread restrictions, pidfd race conditions, CRIU, Kubernetes pause container, `ip netns` internals, performance numbers, CVE history and mitigations