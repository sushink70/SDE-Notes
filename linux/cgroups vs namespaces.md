# Linux cgroups, Namespaces & gRPC — The Complete Deep-Dive Guide

> **Mindset**: You are not just learning APIs. You are learning how the Linux kernel isolates, limits, and virtualizes resources — the very foundation of every container, cloud function, and distributed system you will ever build. Master this, and Docker, Kubernetes, gRPC microservices are just vocabulary.

---

## Table of Contents

1. [Foundational Vocabulary](#1-foundational-vocabulary)
2. [Linux Process Model — The Prerequisite](#2-linux-process-model--the-prerequisite)
3. [Linux Namespaces — Deep Dive](#3-linux-namespaces--deep-dive)
   - 3.1 What is a Namespace?
   - 3.2 All 8 Namespace Types
   - 3.3 Key System Calls: clone, unshare, setns
   - 3.4 /proc Filesystem & Namespace Inspection
   - 3.5 User Namespaces — Special Case
4. [Linux cgroups v1 — Deep Dive](#4-linux-cgroups-v1--deep-dive)
   - 4.1 What is a cgroup?
   - 4.2 Hierarchy & Subsystems
   - 4.3 All Controllers Explained
   - 4.4 The /sys/fs/cgroup Virtual Filesystem
5. [Linux cgroups v2 — The Unified Hierarchy](#5-linux-cgroups-v2--the-unified-hierarchy)
   - 5.1 Why v2 Was Created
   - 5.2 Unified Hierarchy Model
   - 5.3 Delegation & Subtree Control
   - 5.4 PSI — Pressure Stall Information
6. [cgroups vs Namespaces — The Master Comparison](#6-cgroups-vs-namespaces--the-master-comparison)
7. [How Containers Use Both](#7-how-containers-use-both)
8. [C Implementations](#8-c-implementations)
9. [Go Implementations](#9-go-implementations)
10. [Rust Implementations](#10-rust-implementations)
11. [gRPC — Complete Concepts Guide](#11-grpc--complete-concepts-guide)
    - 11.1 What is gRPC?
    - 11.2 Protocol Buffers
    - 11.3 Service Types & Streaming
    - 11.4 Interceptors & Middleware
    - 11.5 gRPC in C
    - 11.6 gRPC in Go
    - 11.7 gRPC in Rust (tonic)
12. [gRPC in Containerized/Namespaced Environments](#12-grpc-in-containerized--namespaced-environments)
13. [Mental Models & Cognitive Frameworks](#13-mental-models--cognitive-frameworks)

---

## 1. Foundational Vocabulary

Before we go deep, align on every term used throughout this guide.

```
TERM             MEANING
─────────────────────────────────────────────────────────────────────
Process          A running program. Has a PID, memory space, file descriptors.
Thread           A lightweight process sharing memory with its parent process.
PID              Process ID — unique number the kernel assigns to each process.
Kernel           The core of Linux. Manages hardware, memory, processes, files.
System Call      A request from userspace (your code) to the kernel.
Virtual FS       A filesystem that exists only in memory; /proc and /sys are examples.
Subsystem        A kernel component (memory, CPU, I/O) that can be controlled.
Controller       In cgroups, a subsystem that limits/monitors a specific resource.
Isolation        Making one thing invisible or unreachable from another.
Resource Limit   A hard cap: "this process group can use at most 512MB RAM".
Namespace        A kernel mechanism that makes a process believe it has its own
                 isolated view of some system resource.
cgroup           A kernel mechanism that limits or measures resource usage of
                 a group of processes.
Hierarchy        A tree structure. Parent nodes contain child nodes.
Mount            Attaching a filesystem to a directory so it's accessible.
Socket           A communication endpoint (like a phone jack) for processes.
IPC              Inter-Process Communication — pipes, message queues, shared mem.
Capability       A fine-grained Linux privilege (like CAP_NET_ADMIN, CAP_SYS_PTRACE).
UID/GID          User ID / Group ID — who owns a process or file.
Pivot Root       A system call that changes the root filesystem of a process.
OCI              Open Container Initiative — standard for container formats/runtimes.
Protobuf         Protocol Buffers — Google's binary serialization format.
RPC              Remote Procedure Call — calling a function on another machine.
gRPC             Google's high-performance RPC framework using HTTP/2 + Protobuf.
Stub             Auto-generated client code that makes RPC calls look like local calls.
```

---

## 2. Linux Process Model — The Prerequisite

### 2.1 What is a Process?

Every command you run becomes a process. The kernel tracks each process with a **Process Control Block (PCB)** — a data structure containing:

```
Process Control Block (PCB)
┌─────────────────────────────────────────┐
│  PID       : 1337                       │
│  PPID      : 1 (parent PID)             │
│  UID/GID   : 1000 / 1000               │
│  State     : RUNNING / SLEEPING / etc   │
│  Memory    : Virtual address space ptr  │
│  Files     : File descriptor table ptr  │
│  Namespace : Namespace pointers (×8)    │  ← Key for our topic
│  cgroup    : cgroup membership ptr      │  ← Key for our topic
│  Signals   : Signal handlers            │
│  CPU affin : Which CPUs allowed         │
└─────────────────────────────────────────┘
```

### 2.2 The Process Tree

Linux processes form a tree. Process 1 (`init` or `systemd`) is the root. Every process has a parent.

```
                    [PID 1: systemd]
                   /       |        \
          [sshd:1234]  [bash:5678]  [nginx:9012]
              |              |
         [bash:4321]    [python:6789]
```

- `fork()` → creates a child process (copy of parent)
- `exec()` → replaces process image with a new program
- `wait()` → parent waits for child to finish

### 2.3 Why This Matters

When we use **namespaces**, we change what a process *sees*. When we use **cgroups**, we change what a process *can use*. Both attach to the PCB. Understanding the PCB makes namespace/cgroup semantics crystal clear.

---

## 3. Linux Namespaces — Deep Dive

### 3.1 What is a Namespace?

**Mental Model**: Imagine you live in a city. You know all the houses (processes), all the streets (network), all the hostnames (DNS). Now imagine putting you in a *bubble*. Inside the bubble, you see different houses, different street names, a different hostname — but the real city hasn't changed. You're just *isolated* from seeing it.

A **Linux namespace** is that bubble. It gives a process (and its children) an **isolated view** of a specific system resource. The resource still exists globally in the kernel, but the process sees only its namespace's version.

```
WITHOUT NAMESPACES:
┌────────────────────────────────────────────────────────────┐
│                      KERNEL GLOBAL VIEW                    │
│  PIDs: 1,2,3,...,1000  │  Hostname: myserver               │
│  Network: eth0, lo     │  Mounts: /, /proc, /home          │
│  Users: root(0),bob(1) │  IPC: shmem_key_42               │
└────────────────────────────────────────────────────────────┘
        ↑ all processes see this same global reality

WITH NAMESPACES:
┌───────────────────────────┐   ┌───────────────────────────┐
│   Namespace A (container) │   │   Namespace B (container) │
│  PIDs: 1,2,3 (own tree)   │   │  PIDs: 1,2 (own tree)     │
│  Hostname: web-container  │   │  Hostname: db-container   │
│  Network: eth0, lo (veth) │   │  Network: eth0 (veth)     │
│  Mounts: overlayfs root   │   │  Mounts: overlayfs root   │
└───────────────────────────┘   └───────────────────────────┘
        ↑ each container sees its own isolated world
```

### 3.2 All 8 Namespace Types

Linux currently has **8 namespace types**. Each isolates a different aspect of the OS.

---

#### (A) PID Namespace — `CLONE_NEWPID`

**Concept**: Each namespace has its own PID number space. A process can be PID 1 *inside* its namespace, but PID 5837 from the host's perspective.

**Why it matters**: In a container, the first process is always PID 1 — the init. It doesn't know (or care) that from the host it's actually PID 5837.

```
HOST VIEW                        CONTAINER VIEW
─────────────────────────────    ─────────────────────────────
systemd (PID 1)                  bash (PID 1)  ← thinks it's init!
  └── docker (PID 512)               └── nginx (PID 2)
        └── bash (PID 5837) ──────► mapped to PID 1 inside
              └── nginx (PID 5838) ──► mapped to PID 2 inside
```

**Key rule**: The parent namespace always has visibility into child namespace PIDs. The child namespace cannot see parent namespace PIDs.

**Nested PID namespaces**:
```
┌─────────────────────────────────────────┐
│  Host NS: PID 1, 2, 3, ..., 5837, 5838 │
│  ┌─────────────────────────────────┐    │
│  │  Container NS: PID 1, 2         │    │
│  │  ┌─────────────────────────┐   │    │
│  │  │  Nested NS: PID 1       │   │    │
│  │  └─────────────────────────┘   │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

#### (B) Network Namespace — `CLONE_NEWNET`

**Concept**: Each network namespace has its own:
- Network interfaces (eth0, lo)
- IP addresses
- Routing tables
- Firewall rules (iptables)
- Network sockets

**Why it matters**: Two containers can both have a process listening on port 8080 — they don't conflict because they live in different network namespaces.

```
HOST NETWORK NS
  eth0: 192.168.1.100
  lo:   127.0.0.1

CONTAINER A NETWORK NS          CONTAINER B NETWORK NS
  eth0: 10.0.0.2 (veth pair)      eth0: 10.0.0.3 (veth pair)
  lo:   127.0.0.1                  lo:   127.0.0.1
  Port 8080: nginx                 Port 8080: apache  ← NO CONFLICT

Virtual Ethernet (veth) pairs bridge between namespaces:
  Host veth0 ──────────── Container A eth0
  Host veth1 ──────────── Container B eth0
  Both routed through a bridge (docker0 / cni0)
```

---

#### (C) Mount Namespace — `CLONE_NEWNS`

**Concept**: Each mount namespace has its own view of the filesystem tree. Mounts (attaching filesystems to directories) in one namespace don't affect others.

**Why it matters**: A container can have a completely different filesystem root (`/`) — it sees its own `/bin`, `/etc`, `/lib` — while the host has its own. This is how containers get isolated filesystems.

```
HOST MOUNT NS                    CONTAINER MOUNT NS
/                                /
├── bin/ (host binaries)         ├── bin/ (Ubuntu 22.04 binaries)
├── etc/ (host config)           ├── etc/ (container config)
├── home/ (host users)           ├── home/ (empty or different)
├── proc/ (host processes)       ├── proc/ (container processes)
└── sys/  (host sysfs)           └── sys/  (container sysfs)

The container's / is usually an overlayfs:
  ┌──────────────────┐
  │  Upper Layer     │  ← container writes (ephemeral)
  ├──────────────────┤
  │  Lower Layer     │  ← base image (read-only, shared)
  └──────────────────┘
```

**The `pivot_root` syscall**: Used to make a new directory the root filesystem. `chroot` is the simpler cousin (doesn't create a namespace, just changes root for a process).

---

#### (D) UTS Namespace — `CLONE_NEWUTS`

**Concept**: UTS = UNIX Time-sharing System. This namespace isolates the **hostname** and **domain name**. (`uname -n` returns namespace-specific values.)

**Why it matters**: Each container can have its own hostname without affecting the host.

```
Host: hostname = "prod-server-01"
Container A: hostname = "web-app"
Container B: hostname = "database"

All coexist on the same machine.
```

---

#### (E) IPC Namespace — `CLONE_NEWIPC`

**Concept**: IPC = Inter-Process Communication. This namespace isolates:
- System V IPC: message queues, semaphores, shared memory segments
- POSIX message queues

**Why it matters**: Processes in different IPC namespaces can't communicate through shared memory or message queues, preventing accidental or malicious cross-container IPC.

```
Container A IPC NS         Container B IPC NS
  shmem key 42 → A's data    shmem key 42 → B's data (different!)
  msgq id 7    → A's queue   msgq id 7    → B's queue (different!)
```

---

#### (F) User Namespace — `CLONE_NEWUSER`

**Concept**: The most powerful and complex namespace. It maps user/group IDs. A process can be **root (UID 0) inside its namespace** while being **unprivileged (UID 1000) on the host**.

**Why it matters**: Rootless containers! You can run a container as root inside without actually being root on the host. This is a major security improvement.

```
HOST VIEW                        CONTAINER VIEW
  UID 1000 (bob)     ─────────►  UID 0 (root inside container)
  UID 1001 (alice)   ─────────►  UID 1 (inside container)

/proc/self/uid_map in the container:
  0   1000   1    ← container UID 0 maps to host UID 1000
  1   1001   100  ← container UIDs 1-100 map to host 1001-1100
```

**Capabilities inside user namespaces**: Within a user namespace, a process can have full capabilities (CAP_SYS_ADMIN, etc.) but only within that namespace's scope. The kernel checks capabilities relative to the namespace.

---

#### (G) cgroup Namespace — `CLONE_NEWCGROUP`

**Concept**: Virtualizes the view of the cgroup hierarchy. Processes inside see their cgroup root as `/` — they don't see the full host cgroup tree.

**Why it matters**: Prevents containers from knowing where they are in the host's cgroup hierarchy — an information leak prevention.

```
HOST cgroup tree:
  /
  └── system.slice
        └── docker
              └── container_abc123    ← this is the container's actual position

CONTAINER'S VIEW of its cgroup tree:
  /    ← container thinks this IS the root
  └── (its cgroup children appear here)
```

---

#### (H) Time Namespace — `CLONE_NEWTIME`

**Concept**: Added in Linux 5.6 (2020). Allows per-namespace offsets for `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME`. Processes in a time namespace can have a different perception of how long the system has been running.

**Why it matters**: Useful for checkpoint/restore (CRIU) — when restoring a container, the monotonic clock can be adjusted so timers continue correctly.

---

### 3.3 Key System Calls

These are the three primary syscalls for working with namespaces.

#### `clone()` — Create a new process in new namespaces

```
clone(fn, stack, flags, arg)
  fn    = function to run in the new process
  stack = stack memory for the new process
  flags = CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS | ...
  arg   = argument to fn

When flags include CLONE_NEW*, the new process is created
inside newly created namespaces of those types.
```

#### `unshare()` — Move current process to new namespaces

```
unshare(flags)
  flags = CLONE_NEWPID | CLONE_NEWNET | ...

The calling process detaches from its current namespace
and moves into a new, fresh namespace.

Example: unshare --pid --fork bash
→ bash now runs in a new PID namespace
```

#### `setns()` — Join an existing namespace

```
setns(fd, nstype)
  fd     = file descriptor to /proc/<pid>/ns/<type>
  nstype = namespace type (or 0 to infer)

Allows a process to join a namespace that already exists.
Used by: docker exec (to enter a running container's namespaces)
```

### 3.4 /proc Filesystem & Namespace Inspection

Every process's namespaces are visible through `/proc`:

```
/proc/<pid>/ns/
  cgroup   → symlink to cgroup namespace
  ipc      → symlink to IPC namespace
  mnt      → symlink to mount namespace
  net      → symlink to network namespace
  pid      → symlink to PID namespace
  pid_for_children → PID namespace for child processes
  time     → symlink to time namespace
  time_for_children
  user     → symlink to user namespace
  uts      → symlink to UTS namespace

Example:
  ls -la /proc/1/ns/
  lrwxrwxrwx  net -> net:[4026531992]
  lrwxrwxrwx  pid -> pid:[4026531836]
              ↑             ↑
         type          inode number (unique ID for this namespace)

Two processes sharing the same namespace will have
the same inode number for that namespace type.
```

**How to check if two processes are in the same namespace**:
```bash
# Compare inode numbers
readlink /proc/PID1/ns/net
readlink /proc/PID2/ns/net
# If equal → same network namespace
```

### 3.5 Namespace Lifecycle

```
CREATION:
  clone() / unshare() → new namespace created
  The creating process becomes the first member

MEMBERSHIP:
  fork() → child inherits parent's namespaces (unless CLONE_NEW* flags set)
  setns() → join an existing namespace

DESTRUCTION:
  When the LAST process in a namespace exits → namespace destroyed
  EXCEPTION: A bind mount on /proc/<pid>/ns/<type> keeps it alive
  (This is how "persistent namespaces" work)

Namespace Reference Counting:
  Kernel maintains a refcount for each namespace.
  Decremented when a process leaves/dies.
  Destroyed when refcount reaches 0 (unless bind-mounted).
```

---

## 4. Linux cgroups v1 — Deep Dive

### 4.1 What is a cgroup?

**Mental Model**: Namespaces = walls (what you can see). cgroups = budget (what you can spend).

A **cgroup (control group)** is a kernel mechanism to:
1. **Limit** resource usage (max 512MB RAM, 50% CPU)
2. **Account** for resource usage (how much CPU has this group used?)
3. **Control** access to resources (prioritize this group over that)
4. **Isolate** resource usage (different groups don't share limits)

```
ANALOGY: Department Budgets in a Company

Company (Linux kernel)
├── Engineering Dept (cgroup: /engineering)
│     Budget: $100k CPU, $50k RAM         ← limits
│     Spent so far: $30k CPU, $20k RAM    ← accounting
│     Priority: High                       ← scheduling weight
│
├── Marketing Dept (cgroup: /marketing)
│     Budget: $50k CPU, $30k RAM
│
└── HR Dept (cgroup: /hr)
      Budget: $20k CPU, $10k RAM

Processes are assigned to departments.
No department can exceed its budget.
```

### 4.2 cgroup v1 Hierarchy

In cgroups v1, each **subsystem (controller)** has its **own separate hierarchy tree**. This is the key architectural fact.

```
cgroup v1 Architecture:

/sys/fs/cgroup/
  ├── cpu/               ← CPU controller hierarchy
  │     ├── system/
  │     │     └── docker/
  │     │           └── container_abc/    ← processes: [5837, 5838]
  │     └── user/
  │
  ├── memory/            ← Memory controller hierarchy (SEPARATE TREE)
  │     ├── system/
  │     │     └── docker/
  │     │           └── container_abc/    ← same processes, but in memory tree
  │     └── user/
  │
  ├── blkio/             ← Block I/O controller hierarchy (SEPARATE TREE)
  ├── net_cls/           ← Network classifier
  ├── devices/           ← Device access control
  └── ...

KEY PROBLEM: The same set of processes must be managed in
MULTIPLE separate trees — one per subsystem. This leads to
inconsistencies and complexity.
```

### 4.3 All cgroup v1 Controllers

#### `cpu` Controller

Controls CPU time allocation.

```
Files in /sys/fs/cgroup/cpu/<group>/
  cpu.shares          → Relative weight (default 1024)
                        Group with 2048 gets 2× more CPU than one with 1024
  cpu.cfs_period_us   → CFS period in microseconds (default 100000 = 100ms)
  cpu.cfs_quota_us    → Max CPU time per period (-1 = unlimited)
                        Setting 50000 with period 100000 = 50% of 1 CPU
  cpu.stat            → Statistics: throttled_time, nr_throttled, etc.

EXAMPLE: Limit to 0.5 CPU cores
  echo 100000 > cpu.cfs_period_us
  echo 50000  > cpu.cfs_quota_us
  → Process can use at most 50ms per 100ms period = 0.5 cores

EXAMPLE: On 4-core machine, limit to 2 cores
  echo 100000 > cpu.cfs_period_us
  echo 200000 > cpu.cfs_quota_us
  → 200ms per 100ms = 2 CPU-equivalents
```

#### `memory` Controller

Controls memory usage.

```
Files in /sys/fs/cgroup/memory/<group>/
  memory.limit_in_bytes       → Hard memory limit (bytes)
  memory.soft_limit_in_bytes  → Soft limit (best-effort)
  memory.memsw.limit_in_bytes → Memory + swap limit
  memory.usage_in_bytes       → Current usage
  memory.max_usage_in_bytes   → Peak usage recorded
  memory.failcnt              → Number of times limit was hit
  memory.oom_control          → OOM killer config
  memory.stat                 → Detailed stats (cache, rss, swap, etc.)

OOM (Out of Memory) Killer:
  When a process group exceeds memory.limit_in_bytes:
  → If oom_control.oom_kill_disable=0: kernel kills a process in the group
  → If oom_control.oom_kill_disable=1: processes hang waiting for memory

EXAMPLE: Limit to 512MB
  echo 536870912 > memory.limit_in_bytes   # 512 * 1024 * 1024
```

#### `blkio` Controller

Controls block device I/O.

```
Files:
  blkio.weight                → Proportional I/O weight (10-1000, default 500)
  blkio.throttle.read_bps_device  → Max read bytes/sec per device
  blkio.throttle.write_bps_device → Max write bytes/sec per device
  blkio.throttle.read_iops_device → Max read IOPS per device
  blkio.throttle.write_iops_device→ Max write IOPS per device

EXAMPLE: Limit writes to 10MB/s on /dev/sda (major:minor = 8:0)
  echo "8:0 10485760" > blkio.throttle.write_bps_device
```

#### `cpuset` Controller

Assigns processes to specific CPUs and memory nodes (NUMA).

```
Files:
  cpuset.cpus       → Allowed CPUs: "0-3" or "0,2,4"
  cpuset.mems       → Allowed memory nodes: "0" or "0-1"
  cpuset.cpu_exclusive → Exclusive CPU ownership
  cpuset.mem_exclusive → Exclusive memory node ownership

EXAMPLE: Pin container to CPUs 2 and 3 only
  echo "2-3" > cpuset.cpus
  echo "0"   > cpuset.mems

USE CASE: Isolate latency-sensitive workloads to dedicated cores.
```

#### `devices` Controller

Controls which device files a group can access.

```
Files:
  devices.allow   → Whitelist: "c 1:* rwm" (allow all char devices with major 1)
  devices.deny    → Blacklist: "a" (deny all)
  devices.list    → Current rules

Format: <type> <major:minor> <permissions>
  type: b=block, c=char, a=all
  permissions: r=read, w=write, m=mknod

EXAMPLE: Docker's default deny-all + selective allow:
  echo "a" > devices.deny         # deny everything
  echo "c 1:3 rwm" > devices.allow # allow /dev/null
  echo "c 1:5 rwm" > devices.allow # allow /dev/zero
  echo "c 5:0 rwm" > devices.allow # allow /dev/tty
```

#### `net_cls` & `net_prio` Controllers

```
net_cls: Tags network packets with a class ID
  → Used with tc (traffic control) for QoS

net_prio: Sets per-interface network priority
  → echo "eth0 5" > net_prio.ifpriomap
```

#### `freezer` Controller

Freezes and thaws all processes in a group (like SIGSTOP/SIGCONT but for the whole group atomically).

```
  echo FROZEN > freezer.state   # suspend all processes
  echo THAWED > freezer.state   # resume all processes

USE CASE: Live migration — freeze container, copy memory, restore elsewhere
```

#### `pids` Controller

Limits the number of processes/threads.

```
  pids.max     → Maximum PIDs allowed in group
  pids.current → Current number of PIDs

EXAMPLE: Prevent fork bombs
  echo 100 > pids.max
  → Container cannot create more than 100 processes total
```

### 4.4 The /sys/fs/cgroup Virtual Filesystem

```
/sys/fs/cgroup is a tmpfs (in-memory filesystem).
Interacting with it IS the cgroup API.

To create a cgroup (just mkdir):
  mkdir /sys/fs/cgroup/memory/myapp
  → Kernel auto-creates all control files

To add a process to a cgroup:
  echo <PID> > /sys/fs/cgroup/memory/myapp/cgroup.procs
  → All threads of that process join

To read a value:
  cat /sys/fs/cgroup/memory/myapp/memory.usage_in_bytes

To set a limit:
  echo 104857600 > /sys/fs/cgroup/memory/myapp/memory.limit_in_bytes

To destroy a cgroup (rmdir, but must be empty first):
  rmdir /sys/fs/cgroup/memory/myapp
```

---

## 5. Linux cgroups v2 — The Unified Hierarchy

### 5.1 Why v2 Was Created

cgroups v1 had major architectural problems:

```
PROBLEM 1: Multiple separate hierarchies
  A process belongs to separate trees for CPU, memory, blkio.
  These can be inconsistent: different subtrees have different members.
  Makes it hard to reason about "what controls apply to this process?"

PROBLEM 2: No unified accounting
  Cross-subsystem queries were complex.

PROBLEM 3: Thread-level granularity was messy (threaded mode complexity)

PROBLEM 4: Delegation was unsafe
  Unprivileged users couldn't safely manage cgroups.

SOLUTION: cgroups v2 — One unified hierarchy for all controllers.
```

### 5.2 Unified Hierarchy Model

In cgroups v2, there is **exactly one tree**. All controllers operate on the same hierarchy.

```
cgroup v2 Unified Hierarchy:

/sys/fs/cgroup/               ← root cgroup
  cgroup.controllers          ← lists available controllers
  cgroup.subtree_control      ← which controllers are enabled for children
  │
  ├── system.slice/
  │     cgroup.controllers
  │     cgroup.subtree_control
  │     memory.max = 4G
  │     cpu.max = "max 100000"   ← cpu and memory on SAME node!
  │     │
  │     └── docker/
  │           memory.max = 2G
  │           cpu.max = "200000 100000"
  │           │
  │           └── container_abc/
  │                 memory.max = 512M
  │                 cpu.max = "50000 100000"
  │                 cgroup.procs = [5837, 5838]
  │
  └── user.slice/
        memory.max = 2G
```

### 5.3 Key v2 Files

```
UNIVERSAL FILES (every cgroup node):
  cgroup.type              → "domain" | "domain threaded" | "threaded"
  cgroup.procs             → list of PIDs in this cgroup
  cgroup.threads           → list of TIDs (threaded mode)
  cgroup.controllers       → available controllers at this level
  cgroup.subtree_control   → enabled controllers for children
  cgroup.events            → populated, frozen events
  cgroup.stat              → nr_descendants, nr_dying_descendants

MEMORY CONTROLLER (v2):
  memory.current           → current usage
  memory.min               → memory protection (never OOM below this)
  memory.low               → soft memory protection
  memory.high              → throttling threshold (SIGKILL NOT sent)
  memory.max               → hard limit (OOM kill threshold)
  memory.swap.current      → current swap usage
  memory.swap.max          → swap limit

  IMPORTANT v2 DIFFERENCE:
  memory.high > memory.max > OOM
  Processes are throttled (slowed) when above memory.high
  before hitting memory.max and getting OOM killed.
  This allows for gentler handling.

CPU CONTROLLER (v2):
  cpu.weight               → Proportional weight (1-10000, default 100)
  cpu.weight.nice          → Nice-based weight (-20 to 19)
  cpu.max                  → "<quota> <period>" e.g., "50000 100000" = 50%
  cpu.stat                 → usage_usec, user_usec, system_usec, throttled

I/O CONTROLLER (v2, replaces blkio):
  io.weight                → "default <weight>" or "<major:minor> <weight>"
  io.max                   → "<major:minor> rbps=X wbps=Y riops=Z wiops=W"
  io.stat                  → per-device stats
  io.pressure              → PSI data for I/O

PIDS CONTROLLER (v2):
  pids.max                 → limit
  pids.current             → count
```

### 5.4 PSI — Pressure Stall Information

This is a v2 exclusive feature. PSI gives you *how much* resource pressure the system is under.

```
CONCEPT: PSI measures "time wasted waiting for a resource"

/sys/fs/cgroup/<group>/memory.pressure:
  some avg10=0.05 avg60=0.10 avg300=0.08 total=12345
  full avg10=0.00 avg60=0.01 avg300=0.01 total=1234

  "some" = at least one task was stalled waiting for memory
  "full" = ALL tasks were stalled (effectively zero progress)
  avg10/60/300 = exponentially weighted moving average (%)
  total = total microseconds stalled

USE CASE: Proactive resource management
  Monitor PSI metrics → if memory.pressure "some" avg10 > 50%
  → proactively reclaim memory before OOM happens
  → much better than reacting to OOM kills
```

### 5.5 v1 vs v2 Comparison Table

```
Feature                     cgroups v1              cgroups v2
─────────────────────────────────────────────────────────────────────
Hierarchy                   Multiple (per-subsystem) Single unified
Controller config           Per-hierarchy            Per-node in tree
Process membership          Multiple trees possible  One tree only
Thread control              cgroup.procs only        threaded mode
Memory protection           limit_in_bytes only      min, low, high, max
CPU quota notation          cfs_quota_us/period_us   cpu.max "quota period"
I/O controller name         blkio                    io
PSI support                 No                       Yes
Delegation safety           Problematic              Safe (cgroup.subtree_control)
Rootless containers         Difficult                Well-supported
Kernel                      2.6.24+ (2008)           4.5+ (2016), full by 5.x
```

---

## 6. cgroups vs Namespaces — The Master Comparison

This is the critical conceptual distinction. Many beginners confuse these two.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THE FUNDAMENTAL DISTINCTION                          │
│                                                                         │
│   NAMESPACES: Answer "What can a process SEE?"                         │
│   CGROUPS:    Answer "What can a process USE?"                         │
│                                                                         │
│   Namespaces = Isolation = Visibility = Perception                     │
│   cgroups    = Limits    = Resources  = Consumption                    │
└─────────────────────────────────────────────────────────────────────────┘
```

```
DETAILED COMPARISON:

Aspect              Namespaces                    cgroups
────────────────────────────────────────────────────────────────────────────
Primary Goal        Isolate what process sees     Limit what process consumes
Analogy             Walls & Blinders              Budget & Throttle
Scope               Visibility / Access           Resource Usage
Types               8 types (pid/net/mnt/uts/...) Subsystems (cpu/mem/io/...)
Direction           Perception filter             Resource enforcer
Default behavior    No isolation (all share global) No limits (unrestricted use)
Security role       Prevent information leakage   Prevent resource exhaustion
Hierarchy           Each type has own tree         v1: per-subsystem; v2: unified
Kernel mechanism    Task struct ns pointers        Task struct css_set pointer
Reversible?         Via setns() (join another)    Change cgroup.procs
PID visibility      Can hide host PIDs             Counts all PIDs against limit
Network             Each gets own network stack    Can throttle bandwidth
Memory              Separate /proc view            Hard memory limits + OOM
CPU                 No CPU isolation               Quota / weight control
Rootless            User NS enables rootless ops   v2 + user NS for rootless

────────────────────────────────────────────────────────────────────────────
INTERACTION:
  Both are INDEPENDENT mechanisms. A container uses BOTH simultaneously.
  
  Namespace alone: "I can't see outside, but I could consume all RAM"
  cgroup alone:    "I'm limited to 512MB, but I can see all host processes"
  Both together:   Full container isolation (what Docker/Kubernetes use)
────────────────────────────────────────────────────────────────────────────
```

### The Container = Namespaces + cgroups

```
CONTAINER CREATION PROCESS:

1. Create namespaces (clone with CLONE_NEW* flags):
   CLONE_NEWPID   → own PID space (PID 1 = container init)
   CLONE_NEWNET   → own network interfaces
   CLONE_NEWNS    → own mount points
   CLONE_NEWUTS   → own hostname
   CLONE_NEWIPC   → own IPC objects
   CLONE_NEWUSER  → own UID/GID mapping (rootless)
   CLONE_NEWCGROUP→ own cgroup root view

2. Set up cgroups (resource limits):
   memory.max = 512M
   cpu.max    = "100000 100000"  (1 CPU)
   pids.max   = 100

3. Set up filesystem (pivot_root or chroot):
   overlayfs: image layers (lower) + container writes (upper)

4. Drop capabilities (security hardening):
   Remove CAP_SYS_PTRACE, CAP_SYS_ADMIN, etc.

5. Apply seccomp profile (syscall filtering):
   Deny dangerous syscalls: ptrace, mount, create_module, etc.

RESULT: A fully isolated, resource-limited process group.
        This IS what a container is.
```

---

## 7. How Containers Use Both

### 7.1 OCI Runtime Specification

The **Open Container Initiative (OCI)** defines a standard for container runtimes. `runc` is the reference implementation.

```
OCI Runtime Contract:
  config.json defines:
    - Process (entrypoint, env, uid/gid)
    - Root filesystem (path, readonly)
    - Mounts (bind mounts, /proc, /sys, tmpfs)
    - Namespaces (which to create)
    - Linux resources (cgroup limits)
    - Seccomp profile
    - Capabilities
    - Hooks (prestart, poststart, poststop)
```

### 7.2 runc execution flow

```
docker run ubuntu bash
     │
     ▼
Docker daemon
     │ creates bundle (rootfs + config.json)
     ▼
containerd
     │ calls
     ▼
runc
  ├─ reads config.json
  ├─ calls clone() with CLONE_NEW* flags
  │     → new PID, NET, MNT, UTS, IPC namespace
  ├─ sets up cgroup:
  │     mkdir /sys/fs/cgroup/memory/docker/<id>
  │     echo 536870912 > memory.max
  │     echo <pid> > cgroup.procs
  ├─ sets up veth pair (network)
  ├─ pivot_root to container's overlayfs
  ├─ mounts /proc, /sys, /dev inside container
  ├─ drops capabilities
  ├─ applies seccomp filter
  └─ exec() the entrypoint (bash)
```

### 7.3 Kubernetes and cgroups

```
Kubernetes cgroup topology:

/sys/fs/cgroup/
  └── kubepods/                        ← all K8s workloads
        ├── burstable/                 ← QoS class: Burstable
        │     └── pod<uid>/
        │           ├── <container-id>/
        │           │     memory.max = request + headroom
        │           │     cpu.max = request quota
        │           └── <container-id>/
        │
        ├── besteffort/                ← QoS class: BestEffort
        │     └── pod<uid>/
        │
        └── guaranteed/               ← QoS class: Guaranteed
              └── pod<uid>/
                    └── <container-id>/
                          memory.max = memory.min = limit
                          cpu.max = exact limit
```

---

## 8. C Implementations

### 8.1 Creating a PID + UTS Namespace in C

```c
/* namespace_demo.c
 * Creates a new PID and UTS namespace.
 * Sets a custom hostname inside, runs a shell.
 *
 * Compile: gcc -o namespace_demo namespace_demo.c
 * Run:     sudo ./namespace_demo
 */

#define _GNU_SOURCE         /* Required for clone(), unshare() on Linux */
#include <sched.h>          /* clone(), CLONE_NEW* flags */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>         /* fork, exec, getpid */
#include <sys/wait.h>       /* waitpid */
#include <sys/types.h>

/* Stack size for the child process created by clone() */
#define STACK_SIZE (1024 * 1024)   /* 1 MB */

/*
 * child_fn: This function runs INSIDE the new namespaces.
 * The 'arg' parameter can carry data from parent to child.
 */
static int child_fn(void *arg) {
    /* We're now in a new PID namespace: we are PID 1 here */
    printf("[child] PID inside namespace: %d\n", getpid());

    /* Set a custom hostname in the new UTS namespace */
    if (sethostname("my-container", 12) == -1) {
        perror("sethostname");
        return 1;
    }

    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    printf("[child] Hostname inside namespace: %s\n", hostname);

    /* Mount a new /proc for our PID namespace
     * Without this, /proc shows the host's processes */
    if (system("mount -t proc proc /proc") != 0) {
        fprintf(stderr, "Failed to mount /proc\n");
        return 1;
    }

    /* Now exec bash — user gets a shell inside the namespace */
    char *args[] = {"/bin/bash", NULL};
    execv("/bin/bash", args);

    /* If we get here, execv failed */
    perror("execv");
    return 1;
}

int main(void) {
    /* Allocate stack for the child.
     * Stack grows DOWN on x86/x86-64, so pass the TOP of the buffer. */
    char *stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    char *stack_top = stack + STACK_SIZE;

    printf("[parent] PID: %d\n", getpid());

    /*
     * clone() flags:
     *   CLONE_NEWPID  → new PID namespace
     *   CLONE_NEWUTS  → new UTS (hostname) namespace
     *   CLONE_NEWNS   → new mount namespace (so /proc mount doesn't affect host)
     *   SIGCHLD       → send SIGCHLD to parent when child dies (like fork)
     */
    pid_t child_pid = clone(
        child_fn,
        stack_top,
        CLONE_NEWPID | CLONE_NEWUTS | CLONE_NEWNS | SIGCHLD,
        NULL
    );

    if (child_pid == -1) {
        perror("clone");
        free(stack);
        exit(EXIT_FAILURE);
    }

    printf("[parent] Child PID (host view): %d\n", child_pid);

    /* Wait for child to finish */
    int status;
    if (waitpid(child_pid, &status, 0) == -1) {
        perror("waitpid");
    }

    free(stack);
    return 0;
}
```

### 8.2 Setting cgroup Memory Limit in C

```c
/* cgroup_memory.c
 * Creates a cgroup v2 with a memory limit,
 * then moves the current process into it.
 *
 * Compile: gcc -o cgroup_memory cgroup_memory.c
 * Run:     sudo ./cgroup_memory
 * Requires: cgroup v2 mounted at /sys/fs/cgroup
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>

#define CGROUP_BASE   "/sys/fs/cgroup"
#define CGROUP_NAME   "myapp_demo"
#define CGROUP_PATH   CGROUP_BASE "/" CGROUP_NAME

/*
 * write_to_file: Helper to write a string to a cgroup control file.
 * path  = file path e.g. /sys/fs/cgroup/myapp_demo/memory.max
 * value = string value e.g. "536870912\n"
 */
static int write_to_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY);
    if (fd == -1) {
        fprintf(stderr, "open(%s): %s\n", path, strerror(errno));
        return -1;
    }
    ssize_t written = write(fd, value, strlen(value));
    close(fd);
    if (written == -1) {
        fprintf(stderr, "write(%s): %s\n", path, strerror(errno));
        return -1;
    }
    return 0;
}

/*
 * setup_cgroup: Creates the cgroup directory and configures limits.
 */
static int setup_cgroup(void) {
    /* Step 1: Create the cgroup directory
     * mkdir() on /sys/fs/cgroup causes the kernel to auto-create
     * all cgroup control files in that directory. */
    if (mkdir(CGROUP_PATH, 0755) == -1 && errno != EEXIST) {
        fprintf(stderr, "mkdir(%s): %s\n", CGROUP_PATH, strerror(errno));
        return -1;
    }
    printf("Created cgroup: %s\n", CGROUP_PATH);

    /* Step 2: Enable memory and pids controllers for this cgroup.
     * We write to the PARENT's cgroup.subtree_control to allow
     * this child to use memory and pids controllers. */
    if (write_to_file(CGROUP_BASE "/cgroup.subtree_control",
                      "+memory +pids") != 0) {
        fprintf(stderr, "Warning: could not enable controllers "
                "(may already be enabled)\n");
    }

    /* Step 3: Set memory limit to 128MB */
    long memory_limit = 128L * 1024 * 1024;  /* 128 MB in bytes */
    char limit_str[64];
    snprintf(limit_str, sizeof(limit_str), "%ld", memory_limit);
    if (write_to_file(CGROUP_PATH "/memory.max", limit_str) != 0) {
        return -1;
    }
    printf("Set memory.max = %ld bytes (128 MB)\n", memory_limit);

    /* Step 4: Set PID limit (prevent fork bombs) */
    if (write_to_file(CGROUP_PATH "/pids.max", "50") != 0) {
        return -1;
    }
    printf("Set pids.max = 50\n");

    return 0;
}

/*
 * join_cgroup: Moves the calling process into the cgroup.
 * Writing to cgroup.procs moves a process (and all its threads)
 * into the cgroup.
 */
static int join_cgroup(void) {
    char pid_str[32];
    /* getpid() returns current process ID */
    snprintf(pid_str, sizeof(pid_str), "%d", (int)getpid());

    if (write_to_file(CGROUP_PATH "/cgroup.procs", pid_str) != 0) {
        return -1;
    }
    printf("Moved PID %s into cgroup %s\n", pid_str, CGROUP_NAME);
    return 0;
}

/*
 * read_cgroup_stat: Reads and prints current memory usage.
 */
static void read_cgroup_stat(void) {
    char path[256];
    snprintf(path, sizeof(path), "%s/memory.current", CGROUP_PATH);

    FILE *f = fopen(path, "r");
    if (!f) {
        perror("fopen memory.current");
        return;
    }
    long current_usage;
    if (fscanf(f, "%ld", &current_usage) == 1) {
        printf("Current memory usage: %ld bytes (%.2f MB)\n",
               current_usage, (double)current_usage / (1024 * 1024));
    }
    fclose(f);
}

int main(void) {
    printf("=== cgroup v2 Memory Limit Demo ===\n");
    printf("Process PID: %d\n\n", getpid());

    /* Set up the cgroup with limits */
    if (setup_cgroup() != 0) {
        fprintf(stderr, "Failed to set up cgroup\n");
        exit(EXIT_FAILURE);
    }

    /* Move current process into the cgroup */
    if (join_cgroup() != 0) {
        fprintf(stderr, "Failed to join cgroup\n");
        exit(EXIT_FAILURE);
    }

    printf("\nProcess is now running inside cgroup with 128MB memory limit.\n");
    read_cgroup_stat();

    /* Demonstrate: allocate memory and watch usage */
    printf("\nAllocating 64MB of memory...\n");
    char *buf = malloc(64 * 1024 * 1024);
    if (buf) {
        /* Touch each page (4096 bytes apart) to actually allocate physical RAM
         * malloc() is lazy — pages are only allocated when accessed */
        for (long i = 0; i < 64 * 1024 * 1024; i += 4096) {
            buf[i] = (char)(i & 0xFF);
        }
        printf("Allocated and touched 64MB.\n");
        read_cgroup_stat();
        free(buf);
    }

    printf("\nDemo complete. To clean up the cgroup:\n");
    printf("  sudo rmdir %s\n", CGROUP_PATH);

    return 0;
}
```

### 8.3 Full Container Simulation in C

```c
/* mini_container.c
 * A minimal container runtime demonstrating:
 *   - PID namespace
 *   - UTS namespace (custom hostname)
 *   - Mount namespace (new /proc)
 *   - Network namespace
 *   - cgroup memory limit
 *
 * Compile: gcc -o mini_container mini_container.c
 * Run:     sudo ./mini_container
 */

#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#define STACK_SIZE      (1 * 1024 * 1024)
#define CGROUP_PATH     "/sys/fs/cgroup/mini_container"
#define CONTAINER_HOSTNAME "mini-container"

/* Write a string to a file */
static void write_file(const char *path, const char *data) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        /* Non-fatal: cgroup files might not be writable depending on setup */
        return;
    }
    write(fd, data, strlen(data));
    close(fd);
}

/* Setup cgroup limits for the container process */
static void setup_cgroup(pid_t pid) {
    mkdir(CGROUP_PATH, 0755);

    /* Enable controllers */
    write_file("/sys/fs/cgroup/cgroup.subtree_control", "+memory +pids +cpu");

    /* Memory limit: 256MB */
    write_file(CGROUP_PATH "/memory.max", "268435456");

    /* PID limit: 64 processes */
    write_file(CGROUP_PATH "/pids.max", "64");

    /* CPU: allow 50% of one CPU (50ms per 100ms period) */
    write_file(CGROUP_PATH "/cpu.max", "50000 100000");

    /* Add the child process to this cgroup */
    char pid_str[32];
    snprintf(pid_str, sizeof(pid_str), "%d\n", pid);
    write_file(CGROUP_PATH "/cgroup.procs", pid_str);

    printf("[parent] cgroup configured at %s\n", CGROUP_PATH);
    printf("[parent] Limits: 256MB memory, 64 PIDs, 50%% CPU\n");
}

/* Cleanup cgroup */
static void cleanup_cgroup(void) {
    rmdir(CGROUP_PATH);
}

/* Function that runs inside the container */
static int container_main(void *arg) {
    (void)arg;

    /* We're now in new PID, UTS, MNT, NET namespaces */
    printf("[container] PID (inside namespace): %d\n", getpid());

    /* Set custom hostname */
    sethostname(CONTAINER_HOSTNAME, strlen(CONTAINER_HOSTNAME));

    char host[256];
    gethostname(host, sizeof(host));
    printf("[container] Hostname: %s\n", host);

    /* Remount /proc to reflect our PID namespace
     * MS_NOSUID, MS_NODEV, MS_NOEXEC are security flags */
    if (mount("proc", "/proc", "proc",
              MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) != 0) {
        perror("[container] mount /proc");
        /* Non-fatal if we don't have permission */
    }

    printf("[container] Starting bash in isolated environment...\n");
    printf("[container] Try: ps aux, hostname, ip addr\n\n");

    /* Drop into a shell */
    char *argv[] = {"/bin/bash", "--norc", NULL};
    char *envp[] = {
        "PATH=/bin:/usr/bin:/sbin:/usr/sbin",
        "PS1=[container]\\$ ",
        "TERM=xterm-256color",
        NULL
    };
    execve("/bin/bash", argv, envp);

    perror("[container] execve");
    return 1;
}

int main(int argc, char *argv[]) {
    (void)argc; (void)argv;

    if (getuid() != 0) {
        fprintf(stderr, "Must run as root (for namespace + cgroup setup)\n");
        return 1;
    }

    printf("=== Mini Container Runtime ===\n");
    printf("[parent] Host PID: %d\n", getpid());

    /* Allocate stack for child */
    char *stack = malloc(STACK_SIZE);
    if (!stack) { perror("malloc"); return 1; }
    char *stack_top = stack + STACK_SIZE;

    /*
     * clone() with all isolation namespaces:
     *   CLONE_NEWPID   → isolated PID space
     *   CLONE_NEWUTS   → isolated hostname
     *   CLONE_NEWNS    → isolated mounts
     *   CLONE_NEWNET   → isolated network stack
     *   CLONE_NEWIPC   → isolated IPC objects
     *   SIGCHLD        → notify parent on child exit
     */
    int clone_flags = CLONE_NEWPID | CLONE_NEWUTS | CLONE_NEWNS
                    | CLONE_NEWNET | CLONE_NEWIPC | SIGCHLD;

    pid_t child_pid = clone(container_main, stack_top, clone_flags, NULL);
    if (child_pid == -1) {
        perror("clone");
        free(stack);
        return 1;
    }

    printf("[parent] Container process (host PID): %d\n", child_pid);

    /* Set up cgroup BEFORE child does much work */
    setup_cgroup(child_pid);

    /* Wait for container to exit */
    int status;
    waitpid(child_pid, &status, 0);
    printf("[parent] Container exited with status: %d\n",
           WIFEXITED(status) ? WEXITSTATUS(status) : -1);

    cleanup_cgroup();
    free(stack);
    return 0;
}
```

---

## 9. Go Implementations

### 9.1 Namespace Demo in Go

```go
// namespace_demo.go
// Demonstrates running a child process in new namespaces.
//
// Run: sudo go run namespace_demo.go
package main

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

/*
 * HOW THIS WORKS IN GO:
 * Go uses os/exec.Cmd to launch processes.
 * cmd.SysProcAttr allows setting Linux-specific process attributes,
 * including namespace flags via Cloneflags.
 *
 * Cloneflags is a uintptr that accepts CLONE_NEW* constants.
 * These are the same constants as in C's <sched.h>.
 */

func runInNamespaces() error {
	fmt.Printf("[parent] Host PID: %d\n", os.Getpid())

	// Build the command to run inside the namespace
	// We re-execute ourselves with a special argument to run as "child"
	cmd := exec.Command("/proc/self/exe", "child")
	//                  ↑ /proc/self/exe = path to current executable
	//                  "child" = argument indicating child mode

	// Inherit stdin/stdout/stderr so the child's output is visible
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// SysProcAttr: Linux process attributes
	cmd.SysProcAttr = &syscall.SysProcAttr{
		// Cloneflags: OR together all CLONE_NEW* flags you want
		Cloneflags: syscall.CLONE_NEWPID |   // new PID namespace
			syscall.CLONE_NEWUTS |            // new hostname namespace
			syscall.CLONE_NEWNS |             // new mount namespace
			syscall.CLONE_NEWIPC,             // new IPC namespace

		// Unshareflags can unshare additional namespaces after fork
		// (different from Cloneflags: happens in child after fork)
		// Unshareflags: syscall.CLONE_NEWNET,

		// UidMappings / GidMappings for user namespaces:
		// UidMappings: []syscall.SysProcIDMap{{ContainerID: 0, HostID: os.Getuid(), Size: 1}},
	}

	return cmd.Run()
}

// childProcess: runs inside the new namespaces
func childProcess() {
	fmt.Printf("[child] PID inside namespace: %d\n", os.Getpid())
	// Note: this should print "1" if PID namespace is correctly set

	// Set hostname in the UTS namespace
	if err := syscall.Sethostname([]byte("go-container")); err != nil {
		fmt.Printf("[child] Sethostname error: %v\n", err)
	}

	hostname, _ := os.Hostname()
	fmt.Printf("[child] Hostname inside namespace: %s\n", hostname)

	// Mount /proc to reflect our PID namespace
	// mount("proc", "/proc", "proc", MS_NOSUID|MS_NODEV|MS_NOEXEC, "")
	if err := syscall.Mount("proc", "/proc", "proc",
		syscall.MS_NOSUID|syscall.MS_NODEV|syscall.MS_NOEXEC, ""); err != nil {
		fmt.Printf("[child] Mount /proc warning: %v\n", err)
	}

	// Execute bash inside the container
	bash, err := exec.LookPath("bash")
	if err != nil {
		fmt.Printf("[child] bash not found: %v\n", err)
		os.Exit(1)
	}

	cmd := exec.Command(bash)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = []string{
		"PATH=/bin:/usr/bin:/sbin:/usr/sbin",
		`PS1=[go-container]\$ `,
		"TERM=xterm-256color",
	}

	if err := cmd.Run(); err != nil {
		fmt.Printf("[child] bash error: %v\n", err)
	}
}

func main() {
	// Check if we're running as the child (inside namespace)
	// This is the "re-execute" pattern used by runc and lxc
	if len(os.Args) > 1 && os.Args[1] == "child" {
		childProcess()
		return
	}

	// Parent: set up namespaces and launch child
	if err := runInNamespaces(); err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}
```

### 9.2 cgroup v2 Manager in Go

```go
// cgroup_manager.go
// A structured cgroup v2 manager demonstrating:
//   - Creating cgroups
//   - Setting resource limits
//   - Adding processes
//   - Reading statistics
//   - Cleanup
//
// Run: sudo go run cgroup_manager.go
package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const cgroupRoot = "/sys/fs/cgroup"

/*
 * CgroupManager manages a single cgroup v2 node.
 * All operations are file I/O on the cgroupfs virtual filesystem.
 */
type CgroupManager struct {
	Name string
	Path string // full path: /sys/fs/cgroup/<Name>
}

// NewCgroupManager creates a new cgroup and returns the manager.
func NewCgroupManager(name string) (*CgroupManager, error) {
	path := filepath.Join(cgroupRoot, name)

	// Creating the directory IS creating the cgroup.
	// The kernel populates it with control files automatically.
	if err := os.MkdirAll(path, 0755); err != nil {
		return nil, fmt.Errorf("create cgroup dir %s: %w", path, err)
	}

	return &CgroupManager{Name: name, Path: path}, nil
}

// EnableControllers enables specific controllers in the parent cgroup.
// In cgroup v2, controllers must be explicitly delegated from parent to child.
func (cm *CgroupManager) EnableControllers(controllers ...string) error {
	// Write "+memory +pids +cpu" to parent's cgroup.subtree_control
	parentControl := filepath.Join(cgroupRoot, "cgroup.subtree_control")
	value := "+" + strings.Join(controllers, " +")
	return cm.writeFile(parentControl, value)
}

// SetMemoryMax sets the hard memory limit.
// bytes=-1 means unlimited.
func (cm *CgroupManager) SetMemoryMax(bytes int64) error {
	var value string
	if bytes == -1 {
		value = "max"
	} else {
		value = strconv.FormatInt(bytes, 10)
	}
	return cm.writeFile(filepath.Join(cm.Path, "memory.max"), value)
}

// SetMemoryHigh sets the soft memory limit (throttles before OOM).
func (cm *CgroupManager) SetMemoryHigh(bytes int64) error {
	value := strconv.FormatInt(bytes, 10)
	return cm.writeFile(filepath.Join(cm.Path, "memory.high"), value)
}

// SetCPUMax sets CPU quota.
// quota: microseconds of CPU per period (-1 for unlimited)
// period: period in microseconds (default 100000 = 100ms)
func (cm *CgroupManager) SetCPUMax(quotaUs, periodUs int64) error {
	var value string
	if quotaUs == -1 {
		value = fmt.Sprintf("max %d", periodUs)
	} else {
		value = fmt.Sprintf("%d %d", quotaUs, periodUs)
	}
	return cm.writeFile(filepath.Join(cm.Path, "cpu.max"), value)
}

// SetPIDsMax sets the maximum number of processes allowed.
func (cm *CgroupManager) SetPIDsMax(max int) error {
	return cm.writeFile(filepath.Join(cm.Path, "pids.max"),
		strconv.Itoa(max))
}

// AddProcess adds a process (by PID) to this cgroup.
// All threads of the process are moved together.
func (cm *CgroupManager) AddProcess(pid int) error {
	return cm.writeFile(
		filepath.Join(cm.Path, "cgroup.procs"),
		strconv.Itoa(pid),
	)
}

// AddCurrentProcess adds the calling process to this cgroup.
func (cm *CgroupManager) AddCurrentProcess() error {
	return cm.AddProcess(os.Getpid())
}

// Stats holds current resource statistics.
type Stats struct {
	MemoryCurrentBytes int64
	PIDsCurrent        int
}

// GetStats reads current resource usage statistics.
func (cm *CgroupManager) GetStats() (*Stats, error) {
	stats := &Stats{}

	// Read memory.current
	memStr, err := os.ReadFile(filepath.Join(cm.Path, "memory.current"))
	if err == nil {
		stats.MemoryCurrentBytes, _ = strconv.ParseInt(
			strings.TrimSpace(string(memStr)), 10, 64)
	}

	// Read pids.current
	pidsStr, err := os.ReadFile(filepath.Join(cm.Path, "pids.current"))
	if err == nil {
		pidsCurrent, _ := strconv.ParseInt(
			strings.TrimSpace(string(pidsStr)), 10, 64)
		stats.PIDsCurrent = int(pidsCurrent)
	}

	return stats, nil
}

// ListProcesses returns all PIDs currently in this cgroup.
func (cm *CgroupManager) ListProcesses() ([]int, error) {
	data, err := os.ReadFile(filepath.Join(cm.Path, "cgroup.procs"))
	if err != nil {
		return nil, err
	}

	var pids []int
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		if line == "" {
			continue
		}
		pid, err := strconv.Atoi(line)
		if err == nil {
			pids = append(pids, pid)
		}
	}
	return pids, nil
}

// Destroy removes the cgroup. The cgroup must have no processes.
func (cm *CgroupManager) Destroy() error {
	pids, err := cm.ListProcesses()
	if err == nil && len(pids) > 0 {
		return errors.New("cgroup still has processes; move them out first")
	}
	return os.Remove(cm.Path)
}

// writeFile is a helper to write a string to a cgroup control file.
func (cm *CgroupManager) writeFile(path, value string) error {
	err := os.WriteFile(path, []byte(value), 0)
	if err != nil {
		return fmt.Errorf("write %s=%q: %w", path, value, err)
	}
	return nil
}

func main() {
	fmt.Println("=== Go cgroup v2 Manager Demo ===")
	fmt.Printf("Current PID: %d\n\n", os.Getpid())

	// Create the cgroup
	cm, err := NewCgroupManager("go_demo_app")
	if err != nil {
		fmt.Printf("Error creating cgroup: %v\n", err)
		os.Exit(1)
	}
	defer func() {
		// Cleanup on exit
		if err := cm.Destroy(); err != nil {
			fmt.Printf("Cleanup warning: %v\n", err)
		} else {
			fmt.Println("Cgroup destroyed.")
		}
	}()

	fmt.Printf("Created cgroup: %s\n", cm.Path)

	// Enable controllers
	if err := cm.EnableControllers("memory", "pids", "cpu"); err != nil {
		fmt.Printf("EnableControllers warning: %v\n", err)
	}

	// Set limits:
	//   256MB memory hard limit
	//   192MB memory soft limit (throttle above this)
	//   50% of 1 CPU
	//   100 max PIDs
	limits := []struct {
		name string
		fn   func() error
	}{
		{"memory.max=256MB", func() error {
			return cm.SetMemoryMax(256 * 1024 * 1024)
		}},
		{"memory.high=192MB", func() error {
			return cm.SetMemoryHigh(192 * 1024 * 1024)
		}},
		{"cpu.max=50%", func() error {
			return cm.SetCPUMax(50000, 100000) // 50ms per 100ms
		}},
		{"pids.max=100", func() error {
			return cm.SetPIDsMax(100)
		}},
	}

	for _, l := range limits {
		if err := l.fn(); err != nil {
			fmt.Printf("Set %s: WARNING: %v\n", l.name, err)
		} else {
			fmt.Printf("Set %s: OK\n", l.name)
		}
	}

	// Add current process to cgroup
	if err := cm.AddCurrentProcess(); err != nil {
		fmt.Printf("AddCurrentProcess: %v\n", err)
	} else {
		fmt.Printf("Process %d added to cgroup\n", os.Getpid())
	}

	// Read stats
	stats, _ := cm.GetStats()
	if stats != nil {
		fmt.Printf("\nCurrent Stats:\n")
		fmt.Printf("  Memory: %.2f MB\n",
			float64(stats.MemoryCurrentBytes)/(1024*1024))
		fmt.Printf("  PIDs:   %d\n", stats.PIDsCurrent)
	}

	// Allocate 64MB to see memory accounting
	fmt.Println("\nAllocating 64MB...")
	buf := make([]byte, 64*1024*1024)
	for i := range buf {
		buf[i] = byte(i) // touch every byte to force physical allocation
	}

	stats, _ = cm.GetStats()
	if stats != nil {
		fmt.Printf("After allocation:\n")
		fmt.Printf("  Memory: %.2f MB\n",
			float64(stats.MemoryCurrentBytes)/(1024*1024))
	}

	fmt.Println("\nDemo complete.")
}
```

### 9.3 Namespace Inspector in Go

```go
// ns_inspector.go
// Inspects namespace information for any process via /proc.
//
// Usage: sudo go run ns_inspector.go <pid>
//        sudo go run ns_inspector.go self
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// NamespaceInfo holds information about one namespace.
type NamespaceInfo struct {
	Type  string
	Inode string // The unique inode identifies which namespace instance
}

// GetNamespaces reads all namespace symlinks for a given PID.
// /proc/<pid>/ns/ contains symlinks like:
//   net -> net:[4026531992]
//              ↑ type  ↑ inode number
func GetNamespaces(pid string) ([]NamespaceInfo, error) {
	nsPath := filepath.Join("/proc", pid, "ns")

	entries, err := os.ReadDir(nsPath)
	if err != nil {
		return nil, fmt.Errorf("readdir %s: %w", nsPath, err)
	}

	var namespaces []NamespaceInfo
	for _, entry := range entries {
		symlink := filepath.Join(nsPath, entry.Name())

		// Read the symlink: "net:[4026531992]"
		target, err := os.Readlink(symlink)
		if err != nil {
			continue
		}

		// Parse "net:[4026531992]" → type="net", inode="4026531992"
		// Format: <type>:[<inode>]
		parts := strings.SplitN(target, ":[", 2)
		inode := ""
		if len(parts) == 2 {
			inode = strings.TrimSuffix(parts[1], "]")
		}

		namespaces = append(namespaces, NamespaceInfo{
			Type:  entry.Name(),
			Inode: inode,
		})
	}
	return namespaces, nil
}

// CompareNamespaces shows which namespaces two processes share.
func CompareNamespaces(pid1, pid2 string) {
	ns1, err1 := GetNamespaces(pid1)
	ns2, err2 := GetNamespaces(pid2)

	if err1 != nil || err2 != nil {
		fmt.Printf("Error: %v %v\n", err1, err2)
		return
	}

	// Build maps for easy lookup
	map1 := make(map[string]string)
	for _, ns := range ns1 {
		map1[ns.Type] = ns.Inode
	}
	map2 := make(map[string]string)
	for _, ns := range ns2 {
		map2[ns.Type] = ns.Inode
	}

	fmt.Printf("\n%-12s %-20s %-20s %s\n", "NAMESPACE", "PID "+pid1, "PID "+pid2, "SHARED?")
	fmt.Println(strings.Repeat("─", 65))

	nsTypes := []string{"cgroup", "ipc", "mnt", "net", "pid", "time", "user", "uts"}
	for _, t := range nsTypes {
		i1 := map1[t]
		i2 := map2[t]
		shared := "NO (isolated)"
		if i1 == i2 && i1 != "" {
			shared = "YES (same namespace)"
		}
		fmt.Printf("%-12s %-20s %-20s %s\n", t, i1, i2, shared)
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: ns_inspector <pid|self> [pid2]")
		os.Exit(1)
	}

	pid := os.Args[1]
	if pid == "self" {
		pid = strconv.Itoa(os.Getpid())
	}

	// Show namespaces for one process
	fmt.Printf("=== Namespaces for PID %s ===\n\n", pid)
	namespaces, err := GetNamespaces(pid)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("%-12s %s\n", "TYPE", "INODE (namespace ID)")
	fmt.Println(strings.Repeat("─", 35))
	for _, ns := range namespaces {
		fmt.Printf("%-12s %s\n", ns.Type, ns.Inode)
	}

	// Compare two processes if second PID given
	if len(os.Args) >= 3 {
		pid2 := os.Args[2]
		if pid2 == "self" {
			pid2 = strconv.Itoa(os.Getpid())
		}
		fmt.Printf("\n=== Namespace Comparison: %s vs %s ===\n", pid, pid2)
		CompareNamespaces(pid, pid2)
	}
}
```

---

## 10. Rust Implementations

### 10.1 cgroup v2 Manager in Rust

```rust
// cgroup_manager.rs
// Rust implementation of a cgroup v2 manager.
//
// Key Rust concepts used:
//   - Result<T, E> for error handling (no exceptions)
//   - std::fs for file I/O
//   - std::path::PathBuf for path manipulation
//   - Drop trait for cleanup (RAII pattern)
//
// Run: sudo cargo run

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

const CGROUP_ROOT: &str = "/sys/fs/cgroup";

/// CgroupManager owns a cgroup and its associated resources.
/// When dropped, it attempts to destroy the cgroup (RAII).
pub struct CgroupManager {
    pub name: String,
    pub path: PathBuf,
}

impl CgroupManager {
    /// Create a new cgroup under the cgroup v2 root.
    /// This creates the directory, which instructs the kernel
    /// to populate it with control files.
    pub fn new(name: &str) -> io::Result<Self> {
        let path = PathBuf::from(CGROUP_ROOT).join(name);

        // mkdir → kernel creates cgroup and control files
        fs::create_dir_all(&path)
            .map_err(|e| io::Error::new(
                e.kind(),
                format!("create cgroup '{}': {}", path.display(), e)
            ))?;

        println!("[cgroup] Created: {}", path.display());

        Ok(Self {
            name: name.to_string(),
            path,
        })
    }

    /// Enable resource controllers in the parent cgroup's subtree_control.
    /// In cgroup v2, a child can only use controllers that its parent
    /// has explicitly enabled.
    pub fn enable_controllers(&self, controllers: &[&str]) -> io::Result<()> {
        let parent_control = PathBuf::from(CGROUP_ROOT)
            .join("cgroup.subtree_control");

        // Format: "+memory +pids +cpu"
        let value: String = controllers.iter()
            .map(|c| format!("+{}", c))
            .collect::<Vec<_>>()
            .join(" ");

        self.write_file(&parent_control, &value)
    }

    /// Set hard memory limit in bytes.
    /// Use None for "unlimited" (writes "max").
    pub fn set_memory_max(&self, bytes: Option<u64>) -> io::Result<()> {
        let value = match bytes {
            Some(b) => b.to_string(),
            None    => "max".to_string(),
        };
        self.write_cgroup_file("memory.max", &value)
    }

    /// Set soft memory limit (throttle, not kill).
    pub fn set_memory_high(&self, bytes: u64) -> io::Result<()> {
        self.write_cgroup_file("memory.high", &bytes.to_string())
    }

    /// Set CPU quota.
    /// quota_us: microseconds of CPU time per period (None = unlimited)
    /// period_us: period length in microseconds
    ///
    /// Example: set_cpu_max(Some(50_000), 100_000) → 50% of 1 CPU
    ///          set_cpu_max(None, 100_000)          → unlimited
    pub fn set_cpu_max(&self, quota_us: Option<u64>, period_us: u64) -> io::Result<()> {
        let value = match quota_us {
            Some(q) => format!("{} {}", q, period_us),
            None    => format!("max {}", period_us),
        };
        self.write_cgroup_file("cpu.max", &value)
    }

    /// Set maximum number of PIDs (processes + threads).
    pub fn set_pids_max(&self, max: u64) -> io::Result<()> {
        self.write_cgroup_file("pids.max", &max.to_string())
    }

    /// Add a process by PID to this cgroup.
    /// Writing to cgroup.procs moves the entire process (all threads).
    pub fn add_process(&self, pid: u32) -> io::Result<()> {
        self.write_cgroup_file("cgroup.procs", &pid.to_string())
    }

    /// Add the current process to this cgroup.
    pub fn add_current_process(&self) -> io::Result<()> {
        self.add_process(std::process::id())
    }

    /// Read current memory usage in bytes.
    pub fn memory_current(&self) -> io::Result<u64> {
        let content = self.read_cgroup_file("memory.current")?;
        content.trim().parse::<u64>()
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))
    }

    /// Read current number of PIDs.
    pub fn pids_current(&self) -> io::Result<u64> {
        let content = self.read_cgroup_file("pids.current")?;
        content.trim().parse::<u64>()
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))
    }

    /// List all PIDs currently in this cgroup.
    pub fn list_processes(&self) -> io::Result<Vec<u32>> {
        let content = self.read_cgroup_file("cgroup.procs")?;
        let pids = content.lines()
            .filter(|l| !l.is_empty())
            .filter_map(|l| l.parse::<u32>().ok())
            .collect();
        Ok(pids)
    }

    /// Read memory pressure information (PSI).
    pub fn memory_pressure(&self) -> io::Result<String> {
        self.read_cgroup_file("memory.pressure")
    }

    // ─── Private helpers ─────────────────────────────────────────────

    fn write_cgroup_file(&self, filename: &str, value: &str) -> io::Result<()> {
        let path = self.path.join(filename);
        self.write_file(&path, value)
    }

    fn write_file(&self, path: &Path, value: &str) -> io::Result<()> {
        fs::write(path, value.as_bytes())
            .map_err(|e| io::Error::new(
                e.kind(),
                format!("write {}={:?}: {}", path.display(), value, e)
            ))
    }

    fn read_cgroup_file(&self, filename: &str) -> io::Result<String> {
        let path = self.path.join(filename);
        fs::read_to_string(&path)
            .map_err(|e| io::Error::new(
                e.kind(),
                format!("read {}: {}", path.display(), e)
            ))
    }
}

/// RAII cleanup: when CgroupManager goes out of scope, destroy the cgroup.
/// rmdir() on the cgroup directory deletes it (only if empty of processes).
impl Drop for CgroupManager {
    fn drop(&mut self) {
        // Move any remaining processes to parent cgroup before rmdir
        match self.list_processes() {
            Ok(pids) if !pids.is_empty() => {
                eprintln!("[cgroup] Warning: {} still has {} processes",
                         self.name, pids.len());
                // Move them to root cgroup
                for pid in pids {
                    let root_procs = PathBuf::from(CGROUP_ROOT)
                        .join("cgroup.procs");
                    let _ = fs::write(&root_procs, pid.to_string());
                }
            }
            _ => {}
        }

        match fs::remove_dir(&self.path) {
            Ok(()) => println!("[cgroup] Destroyed: {}", self.path.display()),
            Err(e) => eprintln!("[cgroup] Destroy warning: {}", e),
        }
    }
}

fn main() -> io::Result<()> {
    println!("=== Rust cgroup v2 Manager Demo ===");
    println!("PID: {}", std::process::id());

    // Create the cgroup — will be destroyed when cm goes out of scope
    let cm = CgroupManager::new("rust_demo")?;

    // Enable controllers (may fail if not root or already enabled)
    match cm.enable_controllers(&["memory", "pids", "cpu"]) {
        Ok(_)  => println!("Controllers enabled"),
        Err(e) => eprintln!("Enable controllers warning: {}", e),
    }

    // Configure limits
    let config = [
        ("memory.max = 256MB", cm.set_memory_max(Some(256 * 1024 * 1024))),
        ("memory.high = 192MB", cm.set_memory_high(192 * 1024 * 1024)),
        ("cpu.max = 50%", cm.set_cpu_max(Some(50_000), 100_000)),
        ("pids.max = 64", cm.set_pids_max(64)),
    ];

    for (label, result) in config {
        match result {
            Ok(_)  => println!("  Set {}: OK", label),
            Err(e) => println!("  Set {}: WARN: {}", label, e),
        }
    }

    // Join cgroup
    match cm.add_current_process() {
        Ok(_)  => println!("\nProcess {} joined cgroup", std::process::id()),
        Err(e) => eprintln!("Join cgroup: {}", e),
    }

    // Read initial stats
    if let Ok(mem) = cm.memory_current() {
        println!("Memory usage: {:.2} MB", mem as f64 / (1024.0 * 1024.0));
    }
    if let Ok(pids) = cm.pids_current() {
        println!("PID count: {}", pids);
    }

    // Allocate 64MB to demonstrate memory accounting
    println!("\nAllocating 64MB...");
    let mut buffer: Vec<u8> = Vec::with_capacity(64 * 1024 * 1024);
    // Touch every byte to force physical page allocation
    for i in 0..(64 * 1024 * 1024usize) {
        buffer.push((i & 0xFF) as u8);
    }

    if let Ok(mem) = cm.memory_current() {
        println!("Memory after alloc: {:.2} MB", mem as f64 / (1024.0 * 1024.0));
    }

    // Read PSI data
    match cm.memory_pressure() {
        Ok(psi) => {
            println!("\nMemory PSI:\n{}", psi);
        }
        Err(_) => {} // PSI might not be enabled
    }

    // buffer and cm both dropped here → memory freed, cgroup destroyed
    println!("\nExiting — cgroup will be auto-destroyed (RAII)");
    Ok(())
}
```

### 10.2 Namespace Inspector in Rust

```rust
// ns_inspector.rs
// Reads and displays namespace information for processes.
//
// Usage: sudo cargo run -- <pid>

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

/// NamespaceEntry represents one namespace symlink from /proc/<pid>/ns/
#[derive(Debug, Clone)]
struct NamespaceEntry {
    ns_type: String,    // e.g., "net", "pid", "mnt"
    inode:   String,    // e.g., "4026531992"
    raw:     String,    // e.g., "net:[4026531992]"
}

/// Read all namespace entries for a given PID.
/// /proc/<pid>/ns/ contains symlinks for each namespace type.
fn read_namespaces(pid: &str) -> Result<Vec<NamespaceEntry>, String> {
    let ns_path = PathBuf::from("/proc").join(pid).join("ns");

    let entries = fs::read_dir(&ns_path)
        .map_err(|e| format!("Cannot read {}: {}", ns_path.display(), e))?;

    let mut namespaces = Vec::new();

    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().to_string();
        let symlink_path = entry.path();

        // Read the symlink target: "net:[4026531992]"
        let target = fs::read_link(&symlink_path)
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_default();

        // Parse "net:[4026531992]"
        let inode = target
            .split(":[")
            .nth(1)
            .map(|s| s.trim_end_matches(']').to_string())
            .unwrap_or_default();

        namespaces.push(NamespaceEntry {
            ns_type: name,
            inode,
            raw: target,
        });
    }

    // Sort by namespace type for consistent output
    namespaces.sort_by(|a, b| a.ns_type.cmp(&b.ns_type));
    Ok(namespaces)
}

/// Print namespace information for one PID.
fn print_namespaces(pid: &str) {
    println!("=== Namespaces for PID {} ===\n", pid);
    println!("{:<12} {:<20} {}", "TYPE", "INODE", "RAW");
    println!("{}", "─".repeat(55));

    match read_namespaces(pid) {
        Ok(nss) => {
            for ns in &nss {
                println!("{:<12} {:<20} {}", ns.ns_type, ns.inode, ns.raw);
            }
        }
        Err(e) => eprintln!("Error: {}", e),
    }
}

/// Compare namespaces between two PIDs and show which are shared.
fn compare_namespaces(pid1: &str, pid2: &str) {
    let ns1 = match read_namespaces(pid1) {
        Ok(v)  => v,
        Err(e) => { eprintln!("Error reading PID {}: {}", pid1, e); return; }
    };
    let ns2 = match read_namespaces(pid2) {
        Ok(v)  => v,
        Err(e) => { eprintln!("Error reading PID {}: {}", pid2, e); return; }
    };

    // Build inode maps: ns_type → inode
    let map1: HashMap<_, _> = ns1.iter()
        .map(|ns| (ns.ns_type.as_str(), ns.inode.as_str()))
        .collect();
    let map2: HashMap<_, _> = ns2.iter()
        .map(|ns| (ns.ns_type.as_str(), ns.inode.as_str()))
        .collect();

    println!("\n=== Namespace Comparison: PID {} vs {} ===\n", pid1, pid2);
    println!("{:<12} {:<22} {:<22} {}",
             "NAMESPACE",
             &format!("PID {}", pid1),
             &format!("PID {}", pid2),
             "SHARED?");
    println!("{}", "─".repeat(75));

    let ns_types = ["cgroup", "ipc", "mnt", "net", "pid", "time", "user", "uts"];
    for t in &ns_types {
        let i1 = map1.get(t).copied().unwrap_or("N/A");
        let i2 = map2.get(t).copied().unwrap_or("N/A");
        let shared = if i1 == i2 && i1 != "N/A" {
            "✓ SHARED (same ns)"
        } else {
            "✗ ISOLATED"
        };
        println!("{:<12} {:<22} {:<22} {}", t, i1, i2, shared);
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: ns_inspector <pid|self> [pid2]");
        std::process::exit(1);
    }

    let pid1 = if args[1] == "self" {
        std::process::id().to_string()
    } else {
        args[1].clone()
    };

    print_namespaces(&pid1);

    if args.len() >= 3 {
        let pid2 = if args[2] == "self" {
            std::process::id().to_string()
        } else {
            args[2].clone()
        };
        compare_namespaces(&pid1, &pid2);
    }
}
```

---

## 11. gRPC — Complete Concepts Guide

### 11.1 What is gRPC?

**Mental Model**: Imagine you want to call a function that lives on a different computer. Without RPC, you'd manually serialize data, send HTTP, parse the response. With gRPC, it *looks* like a local function call — the complexity is hidden.

```
WITHOUT gRPC:
  Client:
    data = json.dumps({"user_id": 42})
    response = http.post("https://server/GetUser", data)
    user = json.loads(response.body)

WITH gRPC:
  Client:
    user = stub.GetUser(GetUserRequest(user_id=42))
    ← looks exactly like a local function call!

gRPC handles:
  - Serialization (Protocol Buffers)
  - Transport (HTTP/2)
  - Connection management (connection pooling, keepalives)
  - Load balancing (client-side or proxy)
  - Error codes (richer than HTTP status)
  - Streaming (bidirectional)
  - Deadlines / timeouts
  - Cancellation
  - Metadata (like HTTP headers)
```

### 11.2 gRPC Architecture

```
gRPC Architecture:

CLIENT                                         SERVER
┌─────────────────────────┐          ┌──────────────────────────────┐
│  Application Code       │          │  Application Code            │
│  stub.GetUser(req)      │          │  func (s) GetUser(req) {..}  │
│         │               │          │         ↑                    │
│  ┌──────▼────────┐      │          │  ┌──────┴──────────┐         │
│  │  Stub         │      │          │  │  Skeleton        │         │
│  │ (auto-generated│     │          │  │ (auto-generated) │         │
│  │  from .proto) │      │          │  └──────┬──────────┘         │
│  └──────┬────────┘      │          │         │                    │
│         │               │          │  ┌──────▼──────────┐         │
│  ┌──────▼────────┐      │          │  │  gRPC Runtime   │         │
│  │  gRPC Channel │      │          │  │  (server core)  │         │
│  │  (HTTP/2 conn)│      │          │  └──────┬──────────┘         │
│  └──────┬────────┘      │          │         │                    │
└─────────┼───────────────┘          └─────────┼────────────────────┘
          │                                     │
          └──────────── HTTP/2 ─────────────────┘
                    (binary frames,
                     multiplexed streams,
                     header compression)
```

### 11.3 Protocol Buffers (Protobuf)

**Concept**: Protobuf is a language-neutral, binary serialization format. You define your data structures in a `.proto` file. The `protoc` compiler generates code in C, Go, Rust, Python, Java, etc.

**Why binary instead of JSON?**
```
JSON (text):
  {"user_id":42,"name":"Alice","active":true}
  → 44 bytes
  → parsing requires string scanning

Protobuf (binary):
  0x08 0x2A 0x12 0x05 0x41 0x6C 0x69 0x63 0x65 0x18 0x01
  → ~11 bytes
  → parsing is direct memory reads (much faster)
  → typically 3-10× smaller than JSON
  → typically 5-10× faster to parse

TRADE-OFF: Binary is not human-readable (need schema to decode).
```

#### Protobuf Message Encoding

```
Each field in a proto message is encoded as:
  [tag][value]
  
  tag = (field_number << 3) | wire_type
  
Wire types:
  0 = Varint     (int32, int64, uint32, uint64, bool, enum)
  1 = 64-bit     (fixed64, sfixed64, double)
  2 = LEN-prefix (string, bytes, embedded messages, repeated)
  5 = 32-bit     (fixed32, sfixed32, float)

EXAMPLE: message User { uint32 id = 1; string name = 2; }
  User{id: 42, name: "Alice"}
  
  Field 1 (id=42):
    tag = (1 << 3) | 0 = 0x08
    value = varint(42) = 0x2A
    bytes: 08 2A
  
  Field 2 (name="Alice"):
    tag = (2 << 3) | 2 = 0x12
    len = 5 → 0x05
    value = "Alice" = 41 6C 69 63 65
    bytes: 12 05 41 6C 69 63 65
  
  Total: 08 2A 12 05 41 6C 69 63 65  (9 bytes vs 44 bytes JSON)
```

#### .proto File Example

```protobuf
// user_service.proto
syntax = "proto3";    // Use proto3 (modern version)

// Package declaration — affects generated code namespacing
package userservice;

// Go package path (Go-specific option)
option go_package = "github.com/example/userservice;userservice";

// Message: like a struct. Each field has a type, name, and number.
// Field numbers are permanent (never change them in a live system!).
message User {
  uint32 id         = 1;   // field number 1
  string name       = 2;
  string email      = 3;
  bool   active     = 4;
  repeated string roles = 5;  // repeated = slice/array
}

// Request message for GetUser RPC
message GetUserRequest {
  uint32 user_id = 1;
}

// Request for ListUsers with pagination
message ListUsersRequest {
  int32 page_size  = 1;
  string page_token = 2;
}

// Response wrapping a list of users
message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
}

// A stream of events
message UserEvent {
  enum EventType {
    UNKNOWN   = 0;   // proto3 requires 0 as default
    CREATED   = 1;
    UPDATED   = 2;
    DELETED   = 3;
  }
  EventType type = 1;
  User      user = 2;
  int64     timestamp_ms = 3;
}

// Empty message (like void)
message Empty {}

// Service definition — this is the gRPC API contract
service UserService {
  // Unary RPC: one request → one response
  rpc GetUser (GetUserRequest) returns (User);

  // Server-streaming: one request → stream of responses
  rpc WatchUsers (Empty) returns (stream UserEvent);

  // Client-streaming: stream of requests → one response
  rpc BulkCreateUsers (stream User) returns (Empty);

  // Bidirectional streaming: stream both ways simultaneously
  rpc Chat (stream UserEvent) returns (stream UserEvent);
}
```

### 11.4 The Four gRPC Service Types

```
1. UNARY RPC (most common)
   Client sends ONE request, gets ONE response.

   Client         Server
     │──── req ────►│
     │◄─── res ─────│

   Use: GetUser, CreateOrder, Login

2. SERVER STREAMING
   Client sends ONE request, gets a STREAM of responses.

   Client         Server
     │──── req ────►│
     │◄─── res1 ────│
     │◄─── res2 ────│
     │◄─── res3 ────│
     │◄─── END ─────│

   Use: SubscribeToOrders, GetLargeDataset, WatchFileChanges

3. CLIENT STREAMING
   Client sends a STREAM of requests, gets ONE response.

   Client         Server
     │──── req1 ───►│
     │──── req2 ───►│
     │──── req3 ───►│
     │──── END ────►│
     │◄─── res ─────│

   Use: UploadFile, BulkInsert, SendMetricsBatch

4. BIDIRECTIONAL STREAMING
   Both client and server send streams simultaneously.
   Neither waits for the other (full duplex, like a phone call).

   Client         Server
     │──── req1 ───►│
     │◄─── res1 ────│
     │──── req2 ───►│
     │◄─── res2 ────│
     │──── req3 ───►│
     │◄─── res3 ────│

   Use: Chat, Gaming, Real-time analytics, Trading feeds
```

### 11.5 gRPC Status Codes

```
gRPC has 16 status codes (richer than HTTP's 5 classes):

Code  Name                  Meaning
─────────────────────────────────────────────────────────────────
0     OK                    Success
1     CANCELLED             Client cancelled the request
2     UNKNOWN               Unknown error
3     INVALID_ARGUMENT      Client sent bad data
4     DEADLINE_EXCEEDED     Timeout before completion
5     NOT_FOUND             Resource doesn't exist
6     ALREADY_EXISTS        Resource already exists (duplicate)
7     PERMISSION_DENIED     Not authorized for this action
8     RESOURCE_EXHAUSTED    Rate limit / quota exceeded
9     FAILED_PRECONDITION   Operation not valid in current state
10    ABORTED               Concurrency conflict (retry)
11    OUT_OF_RANGE          Value outside valid range
12    UNIMPLEMENTED         Method not implemented on server
13    INTERNAL              Internal server error
14    UNAVAILABLE           Server temporarily unavailable (retry)
15    DATA_LOSS             Unrecoverable data loss
16    UNAUTHENTICATED       Missing or invalid auth credentials

KEY INSIGHT:
  UNAVAILABLE (14) → retry with backoff (transient)
  INTERNAL (13)    → do NOT retry (server bug)
  DEADLINE_EXCEEDED → depends on idempotency
```

### 11.6 Interceptors (Middleware)

```
Interceptors in gRPC are like middleware in HTTP frameworks.
They wrap the RPC execution to add cross-cutting concerns.

Execution Flow (unary):

  Client                            Server
    │                                │
    ▼                                ▼
┌──────────────────┐          ┌──────────────────┐
│ Client Interceptor│          │ Server Interceptor│
│  (auth headers,  │          │  (auth verify,   │
│   logging,       │          │   rate limiting, │
│   retry,         │          │   logging,       │
│   tracing)       │          │   metrics)       │
└─────────┬────────┘          └─────────┬────────┘
          │ HTTP/2                       │
          └──────────────────────────────┘

Interceptor chain (each calls next):
  AuthInterceptor
    └── LogInterceptor
          └── MetricsInterceptor
                └── actual RPC handler
```

### 11.7 gRPC in C

```c
/* grpc_server.c
 * A minimal gRPC server in C using the core gRPC C library.
 * 
 * NOTE: C gRPC is low-level. Real production C code uses
 * the C++ wrapper or generates code from protoc.
 * 
 * Install: apt-get install libgrpc-dev
 * Compile: gcc -o grpc_server grpc_server.c -lgrpc -lprotobuf-c
 *
 * This demonstrates the core concepts: channel, completion queue,
 * server builder, call handling.
 */

#include <grpc/grpc.h>
#include <grpc/grpc_security.h>
#include <grpc/support/alloc.h>
#include <grpc/support/log.h>
#include <grpc/support/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * gRPC CORE CONCEPTS:
 *
 * Channel:          A connection to a gRPC endpoint.
 * Completion Queue: An event queue. Operations post events here when done.
 *                   The server polls this to know when work is ready.
 * Call:             One RPC in flight.
 * Metadata:         Like HTTP headers — key-value pairs sent with a call.
 * Byte Buffer:      Raw bytes containing the serialized protobuf message.
 */

#define LISTEN_ADDR "0.0.0.0:50051"

/*
 * A simple echo server that responds to any message with the same bytes.
 * In real usage, you'd deserialize the protobuf, process, re-serialize.
 */
static void run_server(void) {
    /* Initialize gRPC library — MUST be called first */
    grpc_init();

    /* grpc_server: the server object */
    grpc_server *server = grpc_server_create(NULL, NULL);

    /*
     * Completion Queue (CQ): An event-driven queue.
     * When an RPC arrives, a "new call" event is posted to the CQ.
     * When a send completes, a "send done" event is posted.
     * We block on grpc_completion_queue_next() to get these events.
     */
    grpc_completion_queue *cq = grpc_completion_queue_create_for_next(NULL);

    /*
     * Register the completion queue with the server.
     * This is where incoming RPC events will be dispatched.
     */
    grpc_server_register_completion_queue(server, cq, NULL);

    /*
     * Add an insecure listening port (no TLS).
     * For production: use grpc_ssl_server_credentials_create().
     */
    int port = grpc_server_add_insecure_http2_port(server, LISTEN_ADDR);
    if (port == 0) {
        fprintf(stderr, "Failed to bind to %s\n", LISTEN_ADDR);
        goto cleanup;
    }
    printf("Server listening on %s (port %d)\n", LISTEN_ADDR, port);

    /* Start the server — begins accepting connections */
    grpc_server_start(server);

    /*
     * Request the first incoming call.
     * grpc_server_request_call() tells the server:
     * "When the next RPC arrives, post an event to this CQ
     *  and fill in these structs."
     */
    grpc_call *call = NULL;
    grpc_call_details call_details;
    grpc_metadata_array request_metadata;
    grpc_call_details_init(&call_details);
    grpc_metadata_array_init(&request_metadata);

    void *tag = (void *)1;  /* User-defined tag to identify events */
    grpc_call_error err = grpc_server_request_call(
        server, &call, &call_details, &request_metadata, cq, cq, tag
    );
    if (err != GRPC_CALL_OK) {
        fprintf(stderr, "request_call error: %d\n", err);
        goto cleanup;
    }

    printf("Waiting for incoming RPCs...\n");

    /*
     * Event loop: Poll the completion queue.
     * grpc_completion_queue_next() blocks until an event arrives
     * (or timeout, or shutdown).
     */
    gpr_timespec deadline = gpr_time_add(
        gpr_now(GPR_CLOCK_REALTIME),
        gpr_time_from_seconds(30, GPR_TIMESPAN)  /* 30s timeout */
    );

    grpc_event event = grpc_completion_queue_next(cq, deadline, NULL);

    switch (event.type) {
        case GRPC_OP_COMPLETE:
            printf("RPC arrived! Method: %s\n",
                   grpc_slice_to_c_string(call_details.method));

            /*
             * Now we'd:
             * 1. Read the request: grpc_op with GRPC_OP_RECV_MESSAGE
             * 2. Deserialize the protobuf bytes
             * 3. Process the request
             * 4. Serialize the response
             * 5. Send: grpc_op with GRPC_OP_SEND_MESSAGE
             * 6. Send status: GRPC_OP_SEND_STATUS_FROM_SERVER
             */
            printf("(In production: deserialize request, process, send response)\n");
            break;

        case GRPC_QUEUE_TIMEOUT:
            printf("Timed out waiting for RPCs\n");
            break;

        case GRPC_QUEUE_SHUTDOWN:
            printf("Queue shutdown\n");
            break;
    }

    /* Cleanup */
    if (call) grpc_call_unref(call);
    grpc_call_details_destroy(&call_details);
    grpc_metadata_array_destroy(&request_metadata);

    grpc_server_shutdown_and_notify(server, cq, NULL);
    grpc_completion_queue_shutdown(cq);
    grpc_completion_queue_destroy(cq);

cleanup:
    grpc_server_destroy(server);
    grpc_shutdown();
}

int main(void) {
    gpr_log_verbosity_init();
    run_server();
    return 0;
}
```

### 11.8 gRPC in Go

```go
// File structure:
//   proto/user.proto        (service definition)
//   server/main.go          (gRPC server)
//   client/main.go          (gRPC client)
//
// Generate code:
//   protoc --go_out=. --go-grpc_out=. proto/user.proto
//
// go.mod dependencies:
//   google.golang.org/grpc
//   google.golang.org/protobuf

// ─── server/main.go ────────────────────────────────────────────────────────

package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	// This would be the generated package from protoc
	// pb "github.com/example/userservice"
)

/*
 * For this example, we define the interfaces inline
 * (normally these are generated by protoc from .proto files).
 *
 * IN REAL CODE: Run protoc, import the generated package,
 * embed the Unimplemented*Server for forward compatibility.
 */

// ── Simulated generated types (normally from protoc) ──────────────────────

type User struct {
	Id     uint32
	Name   string
	Email  string
	Active bool
}

type GetUserRequest struct{ UserId uint32 }
type ListUsersRequest struct{ PageSize int32 }
type Empty struct{}
type UserEvent struct {
	Type      string
	User      *User
	Timestamp int64
}

// ─── Server Implementation ─────────────────────────────────────────────────

// UserServiceServer is the interface we implement.
// (Normally embedded from generated code for forward compat.)
type userServer struct {
	mu    sync.RWMutex
	users map[uint32]*User
}

func newUserServer() *userServer {
	s := &userServer{users: make(map[uint32]*User)}
	// Seed with some test data
	s.users[1] = &User{Id: 1, Name: "Alice", Email: "alice@example.com", Active: true}
	s.users[2] = &User{Id: 2, Name: "Bob", Email: "bob@example.com", Active: true}
	return s
}

/*
 * GetUser: Unary RPC handler.
 * 
 * Parameters:
 *   ctx: carries deadline, cancellation, metadata (like headers)
 *   req: the deserialized request message
 * Returns:
 *   (*User, error): response and gRPC status error
 */
func (s *userServer) GetUser(ctx context.Context, req *GetUserRequest) (*User, error) {
	// Extract metadata (like HTTP request headers)
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if authTokens := md.Get("authorization"); len(authTokens) > 0 {
			log.Printf("Auth token: %s", authTokens[0])
		}
	}

	// Check context deadline — important for long operations
	if deadline, ok := ctx.Deadline(); ok {
		remaining := time.Until(deadline)
		log.Printf("GetUser called with %v remaining before deadline", remaining)
	}

	s.mu.RLock()
	user, ok := s.users[req.UserId]
	s.mu.RUnlock()

	if !ok {
		// Return a gRPC status error — NOT a plain error
		// This propagates as a proper gRPC status code to the client
		return nil, status.Errorf(
			codes.NotFound,
			"user %d not found", req.UserId,
		)
	}

	return user, nil
}

/*
 * WatchUsers: Server-streaming RPC.
 * The server sends multiple responses over time.
 * 
 * stream.Send() sends one message to the client.
 * Returns when done (stream is closed automatically).
 */
func (s *userServer) WatchUsers(
	req *Empty,
	stream interface{ Send(*UserEvent) error },
) error {
	// Simulate sending 3 events over 3 seconds
	events := []UserEvent{
		{Type: "CREATED", User: &User{Id: 3, Name: "Charlie"}, Timestamp: time.Now().UnixMilli()},
		{Type: "UPDATED", User: &User{Id: 1, Name: "Alice V2"},  Timestamp: time.Now().UnixMilli()},
		{Type: "DELETED", User: &User{Id: 2, Name: "Bob"},       Timestamp: time.Now().UnixMilli()},
	}

	for i, event := range events {
		// Check if client cancelled
		// This is crucial — don't do work after client is gone
		select {
		case <-stream.(interface{ Context() context.Context }).Context().Done():
			log.Printf("Client cancelled stream after %d events", i)
			return status.Error(codes.Cancelled, "client cancelled")
		default:
		}

		e := event // copy for loop variable capture
		if err := stream.Send(&e); err != nil {
			// Send failed — client disconnected
			return fmt.Errorf("send event %d: %w", i, err)
		}

		log.Printf("Sent event %d/%d: %s", i+1, len(events), event.Type)
		time.Sleep(time.Second)
	}

	// Returning nil closes the stream with OK status
	return nil
}

// ─── Interceptors (Middleware) ─────────────────────────────────────────────

/*
 * LoggingInterceptor: A unary server interceptor that logs all RPCs.
 * 
 * Signature: func(ctx, req, info, handler) (interface{}, error)
 *   info.FullMethod = "/packagename.ServiceName/MethodName"
 *   handler = the next handler in the chain (or the actual RPC impl)
 */
func loggingInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	start := time.Now()
	log.Printf("[gRPC] --> %s", info.FullMethod)

	// Call the next handler (the actual RPC implementation)
	resp, err := handler(ctx, req)

	duration := time.Since(start)

	// Extract status code for logging
	code := codes.OK
	if err != nil {
		code = status.Code(err)
	}

	log.Printf("[gRPC] <-- %s | %v | %v", info.FullMethod, code, duration)
	return resp, err
}

/*
 * AuthInterceptor: Validates authorization metadata.
 */
func authInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	// Extract metadata
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Error(codes.Unauthenticated, "no metadata provided")
	}

	tokens := md.Get("authorization")
	if len(tokens) == 0 {
		return nil, status.Error(codes.Unauthenticated, "authorization token required")
	}

	// Validate token (simplified)
	if tokens[0] != "Bearer valid-token" {
		return nil, status.Error(codes.Unauthenticated, "invalid token")
	}

	return handler(ctx, req)
}

// ─── Main: Start the gRPC Server ──────────────────────────────────────────

func runServer() {
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	/*
	 * Create gRPC server with interceptors chained together.
	 * Interceptors execute in order: logging → auth → handler
	 *
	 * For multiple interceptors, use grpc.ChainUnaryInterceptor().
	 */
	grpcServer := grpc.NewServer(
		grpc.ChainUnaryInterceptor(
			loggingInterceptor, // runs first (outer)
			authInterceptor,    // runs second (inner)
		),
		// For TLS: grpc.Creds(credentials.NewServerTLSFromCert(&cert))
	)

	// Register service implementation with the server
	// pb.RegisterUserServiceServer(grpcServer, newUserServer())
	// (In real code, this is the generated registration function)

	log.Printf("gRPC server listening on :50051")
	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}

// ─── client/main.go ────────────────────────────────────────────────────────
// (This would be a separate file/package in real code)

func runClient() {
	/*
	 * Create a gRPC channel (connection) to the server.
	 * grpc.Dial is the entry point for clients.
	 *
	 * Options:
	 *   grpc.WithInsecure()              → no TLS (dev only)
	 *   grpc.WithTransportCredentials()  → TLS
	 *   grpc.WithBlock()                 → wait until connected
	 *   grpc.WithTimeout()               → connection timeout
	 */
	conn, err := grpc.Dial(
		"localhost:50051",
		grpc.WithInsecure(), // Don't do this in production!
		grpc.WithBlock(),
		grpc.WithTimeout(5*time.Second),

		// Client-side interceptor:
		grpc.WithUnaryInterceptor(func(
			ctx context.Context,
			method string,
			req, reply interface{},
			cc *grpc.ClientConn,
			invoker grpc.UnaryInvoker,
			opts ...grpc.CallOption,
		) error {
			// Add auth token to all outgoing requests
			ctx = metadata.AppendToOutgoingContext(ctx,
				"authorization", "Bearer valid-token",
			)
			return invoker(ctx, method, req, reply, cc, opts...)
		}),
	)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	// Create a stub (client proxy)
	// stub := pb.NewUserServiceClient(conn)

	// Make a unary call with deadline
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Receive metadata from server (like HTTP response headers)
	var header, trailer metadata.MD

	// user, err := stub.GetUser(ctx,
	//     &pb.GetUserRequest{UserId: 1},
	//     grpc.Header(&header),
	//     grpc.Trailer(&trailer),
	// )

	log.Printf("Response headers: %v", header)
	log.Printf("Response trailers: %v", trailer)
	_ = ctx
}

func main() {
	// Run server in goroutine, then test with client
	go runServer()
	time.Sleep(100 * time.Millisecond) // Let server start
	runClient()
}
```

### 11.9 gRPC in Rust (tonic)

```rust
// Cargo.toml dependencies:
// [dependencies]
// tonic = "0.11"
// prost = "0.12"
// tokio = { version = "1", features = ["full"] }
// tower = "0.4"
//
// [build-dependencies]
// tonic-build = "0.11"
//
// build.rs:
// fn main() {
//     tonic_build::compile_protos("proto/user.proto").unwrap();
// }

// src/server.rs

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tonic::{
    transport::Server,
    Request, Response, Status,
    metadata::MetadataValue,
};

/*
 * TONIC CONCEPTS:
 *
 * tonic is the canonical Rust gRPC library.
 * It builds on:
 *   - tokio: async runtime (for async/await)
 *   - prost: Protocol Buffer serialization/deserialization
 *   - tower: middleware/service abstraction
 *   - hyper: HTTP/2 transport layer
 *
 * RUST ASYNC/AWAIT:
 *   gRPC operations are inherently async (network I/O).
 *   Rust uses async fn + .await for non-blocking operations.
 *   tokio is the most common async runtime.
 */

// In real code, these types are generated by tonic-build from .proto files
// and included via: pub mod user_service { tonic::include_proto!("userservice"); }

// Simulated generated types:
#[derive(Debug, Clone)]
pub struct User {
    pub id:     u32,
    pub name:   String,
    pub email:  String,
    pub active: bool,
}

#[derive(Debug)]
pub struct GetUserRequest { pub user_id: u32 }

#[derive(Debug)]
pub struct UserEvent {
    pub event_type: String,
    pub user:       Option<User>,
    pub timestamp:  i64,
}

/// The in-memory user store — shared state across all RPC handlers.
/// Arc = Atomic Reference Counted (shared ownership across threads)
/// RwLock = Multiple readers OR one writer at a time (like a read-write lock)
type UserStore = Arc<RwLock<HashMap<u32, User>>>;

/// UserServiceImpl is the concrete implementation of the gRPC service.
/// Each method corresponds to one RPC defined in the .proto file.
pub struct UserServiceImpl {
    store: UserStore,
}

impl UserServiceImpl {
    pub fn new() -> Self {
        let mut store = HashMap::new();
        store.insert(1, User { id: 1, name: "Alice".into(), email: "alice@example.com".into(), active: true });
        store.insert(2, User { id: 2, name: "Bob".into(),   email: "bob@example.com".into(),   active: true });

        Self {
            store: Arc::new(RwLock::new(store)),
        }
    }
}

/*
 * In real tonic code, you implement the trait generated from your .proto:
 *   #[tonic::async_trait]
 *   impl UserService for UserServiceImpl { ... }
 *
 * We show the same pattern with an inline implementation.
 */

impl UserServiceImpl {
    /*
     * get_user: Unary RPC implementation.
     *
     * tonic::Request<T>:
     *   .into_inner()      → the protobuf message T
     *   .metadata()        → request metadata (like HTTP headers)
     *   .extensions()      → type-safe extensions (set by interceptors)
     *
     * Returns Result<tonic::Response<T>, tonic::Status>:
     *   Ok(Response::new(msg)) → success, msg is the response proto
     *   Err(Status::not_found("...")) → gRPC error status
     */
    pub async fn get_user(
        &self,
        request: Request<GetUserRequest>,
    ) -> Result<Response<User>, Status> {
        // Extract auth token from metadata
        let token = request.metadata()
            .get("authorization")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");

        if !token.starts_with("Bearer ") {
            return Err(Status::unauthenticated("authorization token required"));
        }

        let req = request.into_inner();

        // Read from the store (async read lock)
        let store = self.store.read().await;
        let user = store.get(&req.user_id)
            .ok_or_else(|| Status::not_found(
                format!("user {} not found", req.user_id)
            ))?;

        // Build response with optional metadata (like HTTP response headers)
        let mut response = Response::new(user.clone());
        response.metadata_mut().insert(
            "x-server",
            MetadataValue::from_static("rust-grpc-server"),
        );

        Ok(response)
    }

    /*
     * watch_users: Server-streaming RPC.
     *
     * tokio::sync::mpsc: multi-producer, single-consumer channel
     * We spawn a task that sends events into the channel,
     * and wrap the receiver as a stream for tonic to send to the client.
     *
     * ReceiverStream converts mpsc::Receiver into a futures::Stream,
     * which tonic can send as a streaming response.
     */
    pub async fn watch_users(
        &self,
        request: Request<()>,
    ) -> Result<Response<tokio_stream::wrappers::ReceiverStream<Result<UserEvent, Status>>>, Status> {
        let _ = request; // unused in this example

        // Channel with buffer size 10
        let (tx, rx) = tokio::sync::mpsc::channel(10);
        let store = Arc::clone(&self.store);

        // Spawn a background task that produces events
        tokio::spawn(async move {
            let users: Vec<User> = {
                let s = store.read().await;
                s.values().cloned().collect()
            };

            for user in users {
                let event = UserEvent {
                    event_type: "SNAPSHOT".to_string(),
                    timestamp: chrono_now_ms(),
                    user: Some(user),
                };

                // Send the event; if send fails, client disconnected
                if tx.send(Ok(event)).await.is_err() {
                    eprintln!("Client disconnected from stream");
                    return;
                }

                // Simulate real-time delay
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            }
            // When this task completes (tx dropped), stream ends with OK
        });

        // Wrap the receiver as a Stream and return it
        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

/// Placeholder for chrono timestamp (would use chrono crate)
fn chrono_now_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

/*
 * TONIC INTERCEPTOR / TOWER MIDDLEWARE:
 *
 * tonic integrates with the Tower service abstraction.
 * An interceptor is a function: fn(Request<()>) -> Result<Request<()>, Status>
 * Applied server-side: Server::builder().layer(interceptor(my_fn))
 */
fn auth_interceptor(
    req: Request<()>,
) -> Result<Request<()>, Status> {
    // Extract and validate token
    match req.metadata().get("authorization") {
        Some(token) if token.to_str().map(|t| t.starts_with("Bearer ")).unwrap_or(false) => {
            Ok(req)
        }
        _ => Err(Status::unauthenticated("valid Bearer token required")),
    }
}

/// Start the gRPC server.
/// tokio::main sets up the async runtime.
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let service = UserServiceImpl::new();

    println!("gRPC server listening on {}", addr);

    /*
     * Server::builder()
     *   .layer(...)        → add Tower middleware layers
     *   .add_service(...)  → register a service (from generated code)
     *   .serve(addr)       → bind and start serving (async, blocks until shutdown)
     */
    Server::builder()
        // Apply auth interceptor to all requests
        // .layer(tonic::service::interceptor(auth_interceptor))
        // .add_service(UserServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}

// ─── src/client.rs ─────────────────────────────────────────────────────────

pub mod client {
    use tonic::transport::Channel;
    use tonic::metadata::MetadataValue;
    use tonic::Request;

    /*
     * gRPC Client in Rust:
     * 1. Connect: Channel::from_static("http://[::1]:50051").connect().await
     * 2. Create stub: UserServiceClient::new(channel)
     * 3. Make calls with Request<T>
     */

    pub async fn run() -> Result<(), Box<dyn std::error::Error>> {
        // Create channel (connection to server)
        let channel = Channel::from_static("http://[::1]:50051")
            .connect()
            .await?;

        // In real code: let mut client = UserServiceClient::new(channel);

        // Add metadata to request (like HTTP request headers)
        let mut request = Request::new(/* GetUserRequest { user_id: 1 } */ ());
        request.metadata_mut().insert(
            "authorization",
            MetadataValue::from_static("Bearer valid-token"),
        );

        // Set a deadline for the call
        request.set_timeout(std::time::Duration::from_secs(5));

        // In real code:
        // let response = client.get_user(request).await?;
        // println!("Got user: {:?}", response.into_inner());

        Ok(())
    }
}
```

---

## 12. gRPC in Containerized / Namespaced Environments

### 12.1 Network Namespace + gRPC

```
When running gRPC services in containers, each container has its own
network namespace. Here's how traffic flows:

External Client
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  HOST NETWORK NAMESPACE                                     │
│  eth0: 203.0.113.1 (public IP)                             │
│  docker0: 172.17.0.1 (bridge)                              │
│                                                             │
│  iptables DNAT:                                            │
│    0.0.0.0:50051 → 172.17.0.2:50051  (container A)        │
│    0.0.0.0:50052 → 172.17.0.3:50051  (container B)        │
│                 │                                           │
│                 ▼ (via veth pair)                           │
│  ┌─────────────────────────┐  ┌────────────────────────┐  │
│  │ CONTAINER A NET NS      │  │ CONTAINER B NET NS     │  │
│  │ eth0: 172.17.0.2        │  │ eth0: 172.17.0.3       │  │
│  │ gRPC server :50051      │  │ gRPC server :50051     │  │
│  │ (UserService)           │  │ (OrderService)         │  │
│  └─────────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

KEY INSIGHT: Both containers use port 50051, no conflict,
because they're in separate network namespaces.
```

### 12.2 Service Mesh Pattern with gRPC

```
In Kubernetes, gRPC services use a sidecar proxy (Envoy) for:
  - Load balancing (HTTP/2 header-based routing)
  - mTLS (mutual TLS between services)
  - Circuit breaking
  - Distributed tracing

POD A                              POD B
┌─────────────────────┐           ┌─────────────────────┐
│  ┌───────────────┐  │           │  ┌───────────────┐  │
│  │  gRPC Client  │  │           │  │  gRPC Server  │  │
│  │  (UserService)│  │           │  │  (OrderSvc)   │  │
│  └──────┬────────┘  │           │  └──────▲────────┘  │
│         │           │           │         │           │
│  ┌──────▼────────┐  │           │  ┌──────┴────────┐  │
│  │ Envoy Sidecar │◄─┼──gRPC────►┼─►│ Envoy Sidecar │  │
│  │ (interceptor) │  │  (HTTP/2) │  │ (interceptor) │  │
│  └───────────────┘  │           │  └───────────────┘  │
│  NET NS: 10.0.0.1   │           │  NET NS: 10.0.0.2   │
│  cgroup: 512MB mem  │           │  cgroup: 1GB mem    │
└─────────────────────┘           └─────────────────────┘
```

### 12.3 cgroup Resource Limits for gRPC Services

```
PRACTICAL GUIDANCE FOR gRPC SERVICES:

1. MEMORY:
   gRPC maintains connection pools and message buffers.
   A busy gRPC server handling 1000 concurrent streams
   may use: 1000 × (stream buffer ~64KB) = ~64MB just for buffers.
   
   Set memory.max = peak_usage + 20% headroom
   Set memory.high = 80% of memory.max (enable throttling before OOM)

2. CPU:
   gRPC serialization (protobuf) is CPU-intensive at high RPS.
   Streaming RPCs hold connections — fewer cores = more queueing.
   
   Set cpu.max = estimated_rps × time_per_request × cores_needed
   
   Example: 10,000 RPS × 1ms per request = 10 CPU-seconds/second = 10 cores
            cpu.max = "1000000 100000"  (10 cores = 1000ms per 100ms)

3. NETWORK (net namespace + traffic control):
   Use tc (traffic control) with cgroup net_cls:
   tc filter add dev eth0 protocol ip parent 1:0 handle 0x10001 \
      cgroup classid flowid 1:10
   tc class add dev eth0 parent 1: classid 1:10 htb rate 100mbit

4. PIDs:
   Each gRPC stream may spawn goroutines/threads.
   A misbehaving server can create thousands.
   pids.max = expected_goroutines × safety_factor
   
   For a Go gRPC server: each connection = ~2 goroutines + 1 per stream
   1000 connections × 10 streams × 3 goroutines = 30,000 goroutines
   pids.max = 50000 (with headroom)
```

---

## 13. Mental Models & Cognitive Frameworks

### 13.1 The Abstraction Ladder

```
LEVEL 7: Kubernetes (uses cgroups + namespaces + gRPC internally)
    ▲
LEVEL 6: Docker / containerd / runc (orchestrates all primitives)
    ▲
LEVEL 5: OCI spec (standardizes container interface)
    ▲
LEVEL 4: Namespaces + cgroups (Linux primitives)
    ▲
LEVEL 3: clone/unshare/setns + /sys/fs/cgroup (syscalls + VFS)
    ▲
LEVEL 2: Linux kernel subsystems (ns_proxy, cgroup_css_set)
    ▲
LEVEL 1: Hardware (CPU rings, MMU, DMA)

A top-1% engineer can explain ANY level and navigate between them.
Debugging requires descending the ladder; design requires ascending.
```

### 13.2 Pattern Recognition Framework

```
WHEN YOU SEE:              THINK:
─────────────────────────────────────────────────────────────
"isolated" process         → namespace (what it sees)
"limited" process          → cgroup (what it can use)
"container"                → both namespaces + cgroups + rootfs
"OOM killed"               → memory cgroup limit hit
"throttled"                → cpu cgroup quota hit
"fork bomb"                → pids cgroup limit needed
"two services same port"   → different network namespaces
"root inside container"    → user namespace mapping
"can't see other processes"→ PID namespace isolation
"/proc shows wrong info"   → need to mount proc in PID namespace
"gRPC NOT_FOUND"           → check your lookup logic
"gRPC DEADLINE_EXCEEDED"   → timeout too short or server overloaded
"gRPC UNAVAILABLE"         → retry with backoff (transient)
"gRPC UNAUTHENTICATED"     → check metadata / interceptor
```

### 13.3 Deliberate Practice Roadmap

```
WEEK 1-2: NAMESPACES
  Day 1-2: Read /proc/<pid>/ns for processes on your system.
           Compare init (PID 1) vs a Docker container vs yourself.
  Day 3-4: Write the C clone() example by hand. Modify it.
           Add network namespace. Add IPC namespace.
  Day 5-7: Write the Go re-execute pattern. Understand WHY we
           re-exec (PID namespace takes effect only for new processes).

WEEK 3-4: CGROUPS
  Day 1-2: Explore /sys/fs/cgroup on your system (if cgroup v2).
           Find the cgroups Docker creates. Read memory.current for
           running containers.
  Day 3-4: Write the C cgroup demo. Deliberately exceed the memory
           limit. Observe the OOM kill.
  Day 5-7: Implement the Go cgroup manager. Add CPU throttling.
           Use stress-ng to stress-test and observe throttling via
           cpu.stat (nr_throttled, throttled_usec).

WEEK 5-6: INTEGRATION
  Day 1-3: Write a mini container runtime (combine both).
           Start with just PID + UTS namespace.
           Add mount namespace + proc remount.
           Add cgroup limits.
  Day 4-7: Study runc source code. Map each step to what you wrote.

WEEK 7-8: gRPC
  Day 1-2: Write a .proto file. Compile with protoc. Read generated Go code.
  Day 3-4: Implement unary + server streaming server in Go.
  Day 5-6: Add interceptors for logging + auth.
  Day 7-8: Implement the Rust tonic version of the same service.

WEEK 9-10: SYSTEMS INTEGRATION
  Run your gRPC service inside a container you created with your
  mini container runtime. Observe:
  - Network namespacing (how to expose the port)
  - Memory usage under load (cgroup monitoring)
  - PID namespace (observe your gRPC server's goroutines)
```

### 13.4 The 3-Layer Mental Debug Protocol

```
When something breaks in containerized/gRPC systems:

LAYER 1 — VISIBILITY (namespaces)
  Q: Can the process see what it needs?
  Check: network interfaces (ip addr), routes (ip route),
         DNS resolution (cat /etc/resolv.conf),
         filesystem (ls /proc, ls /dev),
         /proc/self/ns/* (are you in the right namespace?)

LAYER 2 — RESOURCES (cgroups)
  Q: Does the process have enough resources?
  Check: memory.current vs memory.max (are we near the limit?),
         cpu.stat → throttled_usec (is CPU being throttled?),
         pids.current vs pids.max (running out of PIDs?)

LAYER 3 — COMMUNICATION (gRPC)
  Q: Is the RPC succeeding?
  Check: status code (OK? UNAVAILABLE? DEADLINE_EXCEEDED?),
         interceptor logs (is auth failing?),
         network connectivity (is the target port reachable?),
         metadata (are required headers present?)
```

### 13.5 Cognitive Chunking Summary

```
CHUNK: "NAMESPACE = PERCEPTION FILTER"
  A namespace makes one set of global resources appear as a
  process-specific private view. 8 types, each for different
  resource kind. Created via clone/unshare, joined via setns.

CHUNK: "CGROUP = RESOURCE BUDGET"
  A cgroup applies limits, priorities, and accounting to groups
  of processes. v1 = per-subsystem trees; v2 = one unified tree.
  Interface is entirely via /sys/fs/cgroup virtual filesystem.

CHUNK: "CONTAINER = NS + CG + ROOTFS"
  A container is nothing magic — it's a process in multiple
  namespaces (isolated view), with cgroup limits (bounded use),
  and an overlayfs as its root filesystem.

CHUNK: "gRPC = IDL + TRANSPORT + STREAMING"
  .proto file defines the contract (IDL).
  HTTP/2 over TCP is the transport.
  4 streaming modes: unary, server, client, bidirectional.
  Interceptors handle cross-cutting concerns.
  Status codes communicate errors richly.
```

---

## Quick Reference Decision Tree

```
You need to...
    │
    ├─► Make process invisible to others?
    │     → PID namespace (CLONE_NEWPID)
    │
    ├─► Give process its own hostname?
    │     → UTS namespace (CLONE_NEWUTS)
    │
    ├─► Give process its own network interfaces?
    │     → Network namespace (CLONE_NEWNET)
    │
    ├─► Give process its own filesystem view?
    │     → Mount namespace (CLONE_NEWNS) + pivot_root
    │
    ├─► Let process be "root" without being root?
    │     → User namespace (CLONE_NEWUSER)
    │
    ├─► Prevent process from using too much RAM?
    │     → cgroup memory.max
    │
    ├─► Prevent process from using too much CPU?
    │     → cgroup cpu.max
    │
    ├─► Prevent fork bombs?
    │     → cgroup pids.max
    │
    ├─► Call a function on a remote server?
    │     → gRPC unary RPC
    │
    ├─► Subscribe to a stream of remote events?
    │     → gRPC server streaming
    │
    ├─► Upload a batch of data to a remote server?
    │     → gRPC client streaming
    │
    └─► Real-time bidirectional communication?
          → gRPC bidirectional streaming
```

---

*"The man who moves a mountain begins by carrying away small stones." — Confucius*

*You are not learning Docker or Kubernetes. You are learning the kernel-level reality that all of them are built on. That knowledge never expires.*

Now let me write the comprehensive guide directly:Here's a breakdown of what's covered in the guide:

**Kernel Foundation.** Starts at `task_struct` — the single kernel object that holds pointers to both `nsproxy` (all namespace memberships) and `css_set` (all cgroup memberships). Every clone flag, every subsystem controller, every resource limit traces back through these two pointers.

**8 Namespace Types, fully detailed.** Each one includes the kernel struct (simplified from actual kernel headers), the exact syscall flags, the security threat it closes, and the gaps it leaves open. User namespaces get extra attention on the UID/GID mapping file format and the capability delegation model — that's where most container escapes originate.

**Cgroup v1 vs v2 — architectural differences.** V1's independent per-subsystem hierarchies vs v2's unified hierarchy, the "no internal processes" rule, thread mode, delegation model, and PSI (Pressure Stall Information). The v1 design flaws are explained structurally, not just by assertion.

**All major controllers.** CPU (CFS bandwidth control, `cpu.weight`, `cpu.max`), memory (`memory.max`, `memory.high`, `memory.min`, OOM group), I/O, PID, CPUset/NUMA, devices (v1 + v2 eBPF replacement), freezer.

**C / Go / Rust implementations.** Full buildable programs: namespace-aware `clone(2)`, cgroup v2 CRUD, user namespace UID mapping (rootless pattern), and namespace introspection/comparison utilities — the kind of code you'd find inside `runc` or `containerd`.

**Threat model table** covers 15+ attack vectors (fork bombs, namespace escapes, user ns LPEs, IPC injection, cgroup relay attacks) with concrete kernel sysctl/seccomp/LSM mitigations.

**Next 3 Steps** push toward: (1) live cgroup telemetry from running containers, (2) building a minimal OCI runtime yourself, (3) CVE deep-dives (0492, 5736, Dirty Pipe) as practical study anchors.

Now let me write the comprehensive guide directly:Here's a breakdown of what's covered in the guide:

**Kernel Foundation.** Starts at `task_struct` — the single kernel object that holds pointers to both `nsproxy` (all namespace memberships) and `css_set` (all cgroup memberships). Every clone flag, every subsystem controller, every resource limit traces back through these two pointers.

**8 Namespace Types, fully detailed.** Each one includes the kernel struct (simplified from actual kernel headers), the exact syscall flags, the security threat it closes, and the gaps it leaves open. User namespaces get extra attention on the UID/GID mapping file format and the capability delegation model — that's where most container escapes originate.

**Cgroup v1 vs v2 — architectural differences.** V1's independent per-subsystem hierarchies vs v2's unified hierarchy, the "no internal processes" rule, thread mode, delegation model, and PSI (Pressure Stall Information). The v1 design flaws are explained structurally, not just by assertion.

**All major controllers.** CPU (CFS bandwidth control, `cpu.weight`, `cpu.max`), memory (`memory.max`, `memory.high`, `memory.min`, OOM group), I/O, PID, CPUset/NUMA, devices (v1 + v2 eBPF replacement), freezer.

**C / Go / Rust implementations.** Full buildable programs: namespace-aware `clone(2)`, cgroup v2 CRUD, user namespace UID mapping (rootless pattern), and namespace introspection/comparison utilities — the kind of code you'd find inside `runc` or `containerd`.

**Threat model table** covers 15+ attack vectors (fork bombs, namespace escapes, user ns LPEs, IPC injection, cgroup relay attacks) with concrete kernel sysctl/seccomp/LSM mitigations.

**Next 3 Steps** push toward: (1) live cgroup telemetry from running containers, (2) building a minimal OCI runtime yourself, (3) CVE deep-dives (0492, 5736, Dirty Pipe) as practical study anchors.