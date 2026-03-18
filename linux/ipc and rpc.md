# Comprehensive Guide: IPC and RPC — From First Principles to Production

**Summary:** IPC (Inter-Process Communication) and RPC (Remote Procedure Call) are the fundamental communication substrates of every system you build — from kernel modules and container runtimes to service meshes and distributed databases. IPC operates at the OS boundary (same host, trust domain), while RPC abstracts function calls across process, host, or network boundaries with serialization, transport, and failure-handling semantics. Choosing the wrong primitive results in TOCTOU races, privilege escalation, denial of service, or tight coupling that kills operability. This guide covers every mechanism from pipes and shared memory to gRPC and Cap'n Proto — with security-first analysis, kernel internals, and production trade-offs for CNCF-grade systems.

---

## Part I: IPC — Inter-Process Communication

### 1.1 What IPC Is and Why It Exists

A process is an isolated execution unit — the kernel enforces that no two processes can directly read each other's virtual address space (barring explicit shared-memory mappings). IPC is the set of kernel-mediated or userspace-coordinated mechanisms that allow processes to exchange data, synchronize state, or signal events while preserving or deliberately relaxing isolation boundaries.

The key design axes are:

| Axis | Options |
|------|---------|
| **Directionality** | Unidirectional vs. bidirectional |
| **Synchrony** | Synchronous (blocking) vs. asynchronous |
| **Persistence** | Volatile (process-lifetime) vs. persistent (filesystem, kernel object) |
| **Capacity** | Byte-stream vs. message-oriented |
| **Identity** | Anonymous vs. named (addressable by third parties) |
| **Kernel involvement** | Every operation vs. zero-copy after setup |

---

### 1.2 Pipes

#### Anonymous Pipes

The oldest and simplest IPC. A kernel buffer (typically 64KB on Linux, tunable via `fcntl(F_SETPIPE_SZ)`) with one read end and one write end.

```c
// Classic shell: ls | grep foo — kernel plumbing
int pipefd[2];
pipe2(pipefd, O_CLOEXEC);   // pipefd[0]=read, pipefd[1]=write

pid_t pid = fork();
if (pid == 0) {              // child: writer
    close(pipefd[0]);
    write(pipefd[1], "hello", 5);
    _exit(0);
}
// parent: reader
close(pipefd[1]);
char buf[16];
read(pipefd[0], buf, sizeof(buf));
```

**Kernel internals:** A pipe is a circular buffer in kernel space. `write()` copies from userspace into this buffer; `read()` copies back out. With `splice(2)` and `vmsplice(2)` you can move data between pipes and file descriptors without userspace copies (zero-copy IO for pipelines).

```
User   ──write()──►  [kernel pipe buffer 64KB]  ──read()──►  User
Process A                 (circular queue)                  Process B
```

**Semantics:**
- `PIPE_BUF` (4096 bytes on Linux) writes are atomic — no interleaving from multiple writers
- Writes block when full; reads block when empty
- Read returns 0 (EOF) when all write ends are closed
- `O_NONBLOCK` turns block into `EAGAIN`

**Security:** Anonymous pipes are only shareable via `fork()` — they cannot be discovered by arbitrary processes. The child inherits the fd table. **Use `O_CLOEXEC` always** to prevent fd leakage across `exec()` — a critical security control because if a setuid binary is exec'd, it should not inherit pipe fds from the privileged parent unless explicitly intended.

#### Named Pipes (FIFOs)

```bash
mkfifo /run/myservice/input.fifo   # creates a filesystem inode
```

```c
// Writer
int wfd = open("/run/myservice/input.fifo", O_WRONLY);
write(wfd, msg, len);

// Reader
int rfd = open("/run/myservice/input.fifo", O_RDONLY);
read(rfd, buf, sizeof(buf));
```

`open()` on a FIFO **blocks** until both ends are open — unless `O_NONBLOCK` is used. This can be a deadlock trap: if writer opens first and reader never comes, writer blocks forever.

**Real-world use case:** `containerd`'s shim v2 protocol uses a named pipe (or Unix socket) per-container to communicate between the shim process and the container runtime. `systemd` uses FIFOs for sd_notify and readiness signaling (`$NOTIFY_SOCKET`).

**Security threat:** FIFO is a filesystem object — it obeys DAC (permissions) and optionally MAC (SELinux/AppArmor). An attacker with write access to the parent directory can replace the FIFO with a symlink. **Mitigation:** Use `O_NOFOLLOW` when opening, place in a directory with sticky bit and restricted write, verify inode with `fstat()` after open to confirm it's `S_ISFIFO`.

---

### 1.3 Signals

Signals are asynchronous notifications delivered by the kernel to a process. They preempt normal execution and invoke a signal handler (or default action: terminate, core dump, stop, ignore).

```c
// Reliable signal handling with signalfd (preferred in modern code)
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGTERM);
sigaddset(&mask, SIGHUP);
sigprocmask(SIG_BLOCK, &mask, NULL);     // Block them from async delivery

int sfd = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);
// Now sfd is pollable — integrates with epoll
struct signalfd_siginfo info;
read(sfd, &info, sizeof(info));
```

**Signal table relevant to systems work:**

| Signal | Default | Use |
|--------|---------|-----|
| `SIGTERM` | Terminate | Graceful shutdown (containers, daemons) |
| `SIGKILL` | Terminate | Uncatchable — kernel enforced |
| `SIGHUP` | Terminate | Config reload (nginx, sshd) |
| `SIGCHLD` | Ignore | Child process state change |
| `SIGPIPE` | Terminate | Write to closed pipe/socket — always handle or `SIG_IGN` |
| `SIGUSR1/2` | Terminate | Application-defined |
| `SIGSTOP/CONT` | Stop/Resume | `cgroups` freezer uses SIGSTOP semantics |
| `SIGSEGV` | Core dump | Memory violation |

**Signal safety:** Only async-signal-safe functions (listed in `signal-safety(7)`) may be called from a signal handler. `malloc`, `printf`, `pthread_mutex_lock` are **not** safe. The modern solution is `signalfd` which converts signals to readable events, usable in the event loop without async-safety constraints.

**Real-world:** Kubernetes sends `SIGTERM` to container PID 1, waits `terminationGracePeriodSeconds`, then `SIGKILL`. Container runtimes (`runc`, `crun`) manage this via the shim. If your PID 1 is a shell script, it may not propagate `SIGTERM` to children — causing zombie processes and slow rollouts.

**Security:** Signals are a vector for race conditions. `TOCTOU` attacks using `SIGSTOP`/`SIGCONT` to pause a setuid process between a privilege check and a privileged operation. **Mitigation:** Use `prctl(PR_SET_DUMPABLE, 0)` on sensitive processes; `seccomp` to restrict `kill(2)` system call; proper process group management.

---

### 1.4 POSIX Message Queues

Message queues are kernel-maintained ordered queues of discrete messages with priority. Unlike pipes (byte streams), each `mq_send` / `mq_receive` is atomic and delivers a complete message.

```c
#include <mqueue.h>

// Create/open queue
struct mq_attr attr = {
    .mq_flags   = 0,
    .mq_maxmsg  = 10,       // max messages in queue
    .mq_msgsize = 256,      // max message size in bytes
    .mq_curmsgs = 0
};

mqd_t mqd = mq_open("/myqueue", O_CREAT | O_RDWR | O_CLOEXEC,
                    0600, &attr);

// Send with priority
mq_send(mqd, msg, len, priority);   // higher priority = delivered first

// Async notification via signal or thread
struct sigevent sev = {
    .sigev_notify = SIGEV_THREAD,
    .sigev_notify_function = on_message,
};
mq_notify(mqd, &sev);

mq_close(mqd);
mq_unlink("/myqueue");   // remove from /dev/mqueue
```

POSIX MQs are visible under `/dev/mqueue` (mount `mqueue` filesystem). Limits in `/proc/sys/fs/mqueue/`.

**vs. pipes:** Message queues preserve message boundaries (no framing needed), support priorities, and can notify via signals/threads. Pipes are simpler and have higher throughput for streaming data.

**Real-world:** Used in real-time systems (PREEMPT_RT), avionics (DO-178C), and embedded Linux where message ordering with priority matters. Also in `qemu` for cross-VM communication experiments.

**Security:** Queue names are global (any process with path can open it). Use restrictive permissions. A malicious process can fill the queue (`mq_maxmsg` limit) causing `mq_send` to block or fail — DoS vector. **Mitigation:** Non-blocking sends with `O_NONBLOCK`, monitoring queue depth.

---

### 1.5 Shared Memory

The highest-throughput IPC — producer and consumer map the same physical pages into their virtual address spaces. No kernel copy on the data path.

#### POSIX Shared Memory

```c
// Producer
int shm_fd = shm_open("/myshm", O_CREAT | O_RDWR | O_EXCL, 0600);
ftruncate(shm_fd, 4096);
void *addr = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                  MAP_SHARED, shm_fd, 0);
memcpy(addr, data, len);
munmap(addr, 4096);

// Consumer
int shm_fd = shm_open("/myshm", O_RDONLY, 0);
void *addr = mmap(NULL, 4096, PROT_READ, MAP_SHARED, shm_fd, 0);
// read data
```

Backed by `tmpfs` on `/dev/shm`. The `shm_fd` is a real fd — supports `fstat`, `ftruncate`, `fchmod`, `fchown`, `memfd_create`.

#### `memfd_create` — Anonymous, Fd-Passed Shared Memory

```c
// Create anonymous shared memory
int memfd = memfd_create("my_region", MFD_CLOEXEC | MFD_ALLOW_SEALING);
ftruncate(memfd, size);

// Seal it to prevent resize (security hardening)
fcntl(memfd, F_ADD_SEALS, F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_SEAL);

// Pass fd to trusted peer via Unix socket SCM_RIGHTS
// (covered in socket section)
```

`memfd_create` + `SCM_RIGHTS` is the modern, secure shared memory pattern. No filesystem name, no race on path. Used heavily in Wayland (frame buffers), `virtiofsd`, and container image layer transfer.

#### Synchronization on Shared Memory

Raw shared memory has no synchronization — you need to layer on:

```c
// Option 1: POSIX semaphores
sem_t *sem = sem_open("/mysem", O_CREAT, 0600, 1);
sem_wait(sem);
// critical section on shared memory
sem_post(sem);

// Option 2: Futex (fast userspace mutex) — what pthreads use internally
// Option 3: Atomic operations (C11 atomics / GCC __sync_*)
// Option 4: Lock-free ring buffer (SPSC: no locks needed)
```

**SPSC (Single-Producer Single-Consumer) ring buffer** — the highest-performance pattern, zero locks, used in DPDK, io_uring, LMAX Disruptor:

```
                    ┌─────────────────────────────────┐
                    │   Shared Ring Buffer             │
  Producer          │  [0][1][2][3][4][5][6][7]       │          Consumer
  writes to         │         ↑head        ↑tail       │          reads from
  tail (atomic)     └─────────────────────────────────┘          head (atomic)

  head == tail: empty
  (tail+1) % N == head: full
  Sequence numbers + memory barriers ensure coherency
```

**Real-world:** DPDK (kernel bypass networking) uses a shared ring buffer between the NIC driver and packet processing cores. vhost-net (virtio) uses a vring (virtqueue) in shared memory between QEMU and the guest kernel. `io_uring` uses two shared rings (submission/completion) between kernel and userspace — zero syscall on hot path once set up.

**Security threats:**
- **Confused deputy:** If a privileged process maps shared memory writable to an unprivileged process, the unprivileged process can corrupt the privileged process's data structures
- **Memory unsafety:** If a privileged process trusts data in shared memory without validation — TOCTOU. The consumer can modify data after the producer checks it
- **Covert channels:** Shared memory is a high-bandwidth covert channel between VMs if hypervisor doesn't enforce isolation (Spectre/Meltdown exploited this)

**Mitigation:** Map shared memory with minimal permissions (`PROT_READ` if you only read). Validate all data received from untrusted peers. Use `memfd_create` + sealing to prevent size changes. Prefer message-passing over shared state when crossing trust boundaries.

---

### 1.6 Unix Domain Sockets

The most versatile IPC for local communication. Full socket API (stream, datagram, sequential packet), but in-kernel — no TCP stack, no IP headers, no loopback device.

```c
// Server (abstract namespace — no filesystem path)
int sfd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
struct sockaddr_un addr = { .sun_family = AF_UNIX };
addr.sun_path[0] = '\0';                          // abstract: first byte is null
strcpy(addr.sun_path + 1, "myservice.sock");      // name starts at offset 1
socklen_t addrlen = offsetof(struct sockaddr_un, sun_path) + 1 + strlen("myservice.sock");

bind(sfd, (struct sockaddr*)&addr, addrlen);
listen(sfd, 128);
```

**Filesystem vs. Abstract namespace:**

| | Filesystem Socket | Abstract Socket |
|--|--|--|
| Cleanup on crash | No (stale socket file) | Yes (auto-cleaned) |
| Filesystem permissions | Yes (DAC/MAC) | No (any process can connect) |
| Visible to tools | `ls`, `ss -x` | `ss -xp` only |
| Container crossing | Via bind-mount | No (namespaced) |
| Security | Path-based access control | Only by kernel namespace |

**Peer credentials — the killer feature:**

```c
// After accept(), get peer's UID/GID/PID — kernel-certified, unforgeable
struct ucred cred;
socklen_t len = sizeof(cred);
getsockopt(conn_fd, SOL_SOCKET, SO_PEERCRED, &cred, &len);
// cred.pid, cred.uid, cred.gid — use for authorization decisions
```

This is the foundation of `systemd`'s socket activation, `dbus`, `containerd`'s CRI socket, Docker's `/var/run/docker.sock`, and basically every Unix daemon's access control model.

**Passing file descriptors — SCM_RIGHTS:**

```c
// Transmit fd across process boundary (the fd number changes, the underlying
// kernel object is the same — reference count incremented)
struct msghdr msg = {0};
struct cmsghdr *cmsg;
char buf[CMSG_SPACE(sizeof(int))];
msg.msg_control = buf;
msg.msg_controllen = sizeof(buf);

cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_RIGHTS;
cmsg->cmsg_len   = CMSG_LEN(sizeof(int));
memcpy(CMSG_DATA(cmsg), &fd_to_send, sizeof(int));

sendmsg(sock_fd, &msg, 0);
```

`SCM_RIGHTS` is used by:
- Wayland: passing GPU buffer fds to the compositor
- Container runtimes: passing container stdio fds to the shim
- `systemd-socket-activation`: passing pre-bound sockets to services
- `virtiofsd`: passing memory fds to QEMU
- Any sandbox escape mitigation: pass a pre-opened fd instead of letting the sandboxed process open a path

**SOCK_SEQPACKET** — the underrated option: message-oriented (like datagram) but connection-oriented with in-order delivery (like stream). Ideal for IPC protocols where you want message framing without manual length-prefix encoding.

**Real-world architectures using Unix sockets:**

```
containerd (CRI socket)
  /run/containerd/containerd.sock   ←── kubelet (grpc over uds)
         │
         ├── shim v2 (per container)
         │     /run/containerd/s/<id>/shim.sock   ←── containerd
         │           │
         │           └── runc/crun (spawns container)
         │
         └── snapshotter plugin
               /run/containerd/plugins/overlayfs.sock

dockerd
  /var/run/docker.sock   ←── docker CLI, docker SDK clients
  (this is a Unix socket exposing HTTP/REST API — massive attack surface
   if bind-mounted into containers!)
```

**Security:** `/var/run/docker.sock` bind-mounted into a container = full host root. Unix socket security depends on directory permissions, socket file permissions, and peer credential verification. Implement authorization at the socket layer using `SO_PEERCRED` + a policy engine (OPA, Cedar).

---

### 1.7 Netlink Sockets

Netlink is the Linux kernel's IPC mechanism for kernel↔userspace and process↔process communication about kernel subsystems. It's a socket family (`AF_NETLINK`) with multiple protocol families:

| Protocol | Purpose |
|----------|---------|
| `NETLINK_ROUTE` | Routing, interface, ARP, neighbor tables |
| `NETLINK_NETFILTER` | iptables/nftables rule management |
| `NETLINK_AUDIT` | Linux audit subsystem |
| `NETLINK_KOBJECT_UEVENT` | udev events (hotplug) |
| `NETLINK_CONNECTOR` | Process events (fork, exec, exit) |
| `NETLINK_GENERIC` | Generic extensible family — used by nl80211 (WiFi), OVS, etc. |

```c
// Monitor process events (fork/exec/exit) via Netlink Connector
int sock = socket(PF_NETLINK, SOCK_DGRAM | SOCK_CLOEXEC, NETLINK_CONNECTOR);
struct sockaddr_nl sa = { .nl_family = AF_NETLINK,
                          .nl_groups = CN_IDX_PROC };
bind(sock, (struct sockaddr*)&sa, sizeof(sa));

// Subscribe to process events
struct cn_msg *cn_hdr; // ... set op = PROC_CN_MCAST_LISTEN
send(sock, ...);
// Now receive fork/exec/exit events
```

**Real-world:** `cilium` uses Netlink extensively to install eBPF programs and manage TC/XDP hooks. `iproute2` (`ip`, `tc`, `ss`) is primarily a Netlink client. Container runtimes use Netlink to configure network namespaces (VETH pairs, bridge assignment). `runc`'s network setup calls into `netlink` Go library.

---

### 1.8 eventfd, timerfd, signalfd — The Unified Event Model

Linux's `*fd` interfaces allow you to treat async events as readable file descriptors, integrable into `epoll` for a unified event loop — the foundation of every modern async runtime:

```c
// eventfd: lightweight counter/semaphore as an fd
int efd = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK | EFD_SEMAPHORE);
uint64_t val = 1;
write(efd, &val, sizeof(val));   // signal
read(efd, &val, sizeof(val));    // wait (EFD_SEMAPHORE: decrements by 1)

// timerfd: timer as an fd
int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
struct itimerspec ts = { .it_interval = {1, 0}, .it_value = {1, 0} };
timerfd_settime(tfd, 0, &ts, NULL);
// read(tfd, ...) returns number of expirations

// All of these go into one epoll fd:
epoll_ctl(epfd, EPOLL_CTL_ADD, efd, &ev_eventfd);
epoll_ctl(epfd, EPOLL_CTL_ADD, tfd, &ev_timerfd);
epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev_signalfd);  // signalfd from before
epoll_ctl(epfd, EPOLL_CTL_ADD, server_sock, &ev_accept);
```

**The unified epoll event loop pattern:**

```
┌─────────────────────────────────────────────────────┐
│                    epoll_wait()                      │
│  ┌─────────┬──────────┬──────────┬───────────────┐  │
│  │ eventfd │ timerfd  │signalfd  │ unix socket   │  │
│  │ (tasks) │(timeouts)│(SIGTERM) │ (IPC clients) │  │
│  └─────────┴──────────┴──────────┴───────────────┘  │
└─────────────────────────────────────────────────────┘
         ↓ one syscall, handles all events
```

This is the architecture used by `systemd`, `containerd`, `io_uring`-based runtimes, Tokio's reactor (in Rust), and Go's netpoller.

---

### 1.9 io_uring — Modern Async IPC and I/O

`io_uring` (Linux 5.1+) is a shared-memory ring buffer between kernel and userspace for submitting I/O operations and receiving completions without syscalls on the hot path.

```
                 Submission Queue (SQ)         Completion Queue (CQ)
User                                            
space   ──── write ops here ──────────────────── read results here ────

             ┌──────────────┐                  ┌──────────────┐
             │  SQ Ring     │                  │  CQ Ring     │
Shared       │  [sqe][sqe]  │    kernel        │  [cqe][cqe]  │
memory       │  head↑ tail↑ │ ──processes──►   │  head↑ tail↑ │
             └──────────────┘                  └──────────────┘
                                                
Kernel       io_uring_enter() only needed to notify kernel if it's
             not in SQPOLL mode (kernel thread polls SQ continuously)
```

```c
struct io_uring ring;
io_uring_queue_init(256, &ring, IORING_SETUP_SQPOLL);  // kernel polling thread

// Submit a read without syscall
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe, fd, buf, len, offset);
sqe->user_data = (uint64_t)ctx;
io_uring_submit(&ring);  // may not even syscall if SQPOLL

// Poll completions
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
// cqe->res = bytes read, cqe->user_data = ctx
io_uring_cqe_seen(&ring, cqe);
```

**io_uring operations relevant to IPC:** `IORING_OP_SEND`, `IORING_OP_RECV`, `IORING_OP_SENDMSG`, `IORING_OP_RECVMSG`, `IORING_OP_ACCEPT`, `IORING_OP_CONNECT`, `IORING_OP_POLL_ADD`, `IORING_OP_SPLICE`.

**Security:** io_uring has had significant CVEs (CVE-2022-29582, CVE-2023-2598). Many container/sandbox environments disable it via `seccomp`. Check `IORING_SETUP_REGISTERED_FD_ONLY` and `IORING_SETUP_NO_FIXED_FILES` for hardened configurations. In production containers, restrict via `seccomp` profile or disable with `io_uring_enter` filter.

---

### 1.10 D-Bus

D-Bus is a structured message-passing system for Linux userspace IPC, primarily used by system daemons. It provides object model (methods, signals, properties), introspection, service activation, and access control.

```
┌──────────────────────────────────────────────────────────┐
│                     dbus-daemon                          │
│                   (message router)                       │
│   ┌─────────────────────────────────────────────────┐   │
│   │  System Bus (/run/dbus/system_bus_socket)        │   │
│   │  Session Bus ($DBUS_SESSION_BUS_ADDRESS)         │   │
│   └─────────────────────────────────────────────────┘   │
│              ↑              ↑             ↑              │
│          NetworkManager  systemd       BlueZ             │
└──────────────────────────────────────────────────────────┘
```

D-Bus policies (in `/etc/dbus-1/system.d/`) control who can own names, send/receive messages:

```xml
<policy user="root">
  <allow own="org.freedesktop.NetworkManager"/>
  <allow send_destination="org.freedesktop.NetworkManager"/>
</policy>
<policy context="default">
  <deny own="org.freedesktop.NetworkManager"/>
  <allow send_destination="org.freedesktop.NetworkManager"
         send_interface="org.freedesktop.DBus.Introspectable"/>
</policy>
```

**Real-world:** `systemd`, `NetworkManager`, `BlueZ`, `Avahi`, `polkit`. In containers and cloud-native systems, D-Bus is typically replaced by gRPC/Unix socket direct protocols. `dbus-broker` is the modern, more secure D-Bus implementation (replaces `dbus-daemon`), with better isolation and performance.

---

### 1.11 SysV IPC (Legacy)

SysV IPC (message queues, shared memory, semaphores) predates POSIX IPC. It uses integer keys (not names/fds), persists across process lifetimes (even if all processes exit), is not reference-counted, and uses a different syscall interface (`msgget/shmget/semget`). It has no fd semantics, no `O_CLOEXEC`, and is harder to use securely.

```bash
ipcs -a        # list all SysV IPC objects
ipcrm -M key   # remove shared memory segment by key
```

**Avoid in new code.** Use POSIX equivalents. The primary reason you encounter SysV IPC is in legacy databases (PostgreSQL uses SysV semaphores on some platforms), commercial software, and old Linux distributions.

---

## Part II: RPC — Remote Procedure Call

### 2.1 What RPC Is

RPC is the abstraction of a function call that may execute in a different process, on a different host, across a network. It hides the communication details behind a procedure call interface. The fundamental components are:

```
┌────────────────────────────────────────────────────────────────────┐
│  Client Process                        Server Process              │
│                                                                    │
│  result = RemoteAdd(a, b)              func Add(a, b int) int {   │
│       │                                    return a + b            │
│       ▼                                }                           │
│  [Client Stub]                         [Server Stub]               │
│       │                                       ↑                    │
│  Serialization                          Deserialization            │
│  (marshal args)                         (unmarshal args)           │
│       │                                       │                    │
│  [Transport Layer: TCP/TLS/UDS/HTTP]          │                    │
│       └───────────────────────────────────────┘                    │
└────────────────────────────────────────────────────────────────────┘
```

**The 8 fallacies of distributed computing** (Peter Deutsch) apply to every RPC system:
1. The network is reliable
2. Latency is zero
3. Bandwidth is infinite
4. The network is secure
5. Topology doesn't change
6. There is one administrator
7. Transport cost is zero
8. The network is homogeneous

A good RPC framework forces you to confront these.

---

### 2.2 Serialization Formats — The Foundation

Before choosing an RPC framework, understand the serialization layer, since it dominates CPU time and wire size.

#### Protocol Buffers (protobuf)

Google's binary serialization format. Schema-defined, field-numbered, backward/forward compatible.

```protobuf
syntax = "proto3";

package compute.v1;

message CreateVMRequest {
  string name       = 1;
  int32  vcpus      = 2;
  int64  memory_mb  = 3;
  repeated string tags = 4;
  VMDisk disk       = 5;
}

message VMDisk {
  string image_id   = 1;
  int64  size_gb    = 2;
  DiskType type     = 3;
}

enum DiskType {
  DISK_TYPE_UNSPECIFIED = 0;
  DISK_TYPE_SSD         = 1;
  DISK_TYPE_HDD         = 2;
}

message CreateVMResponse {
  string vm_id     = 1;
  string status    = 2;
}
```

**Encoding:** Each field is encoded as `(field_number << 3) | wire_type` followed by the value. Wire types: 0=varint, 1=64-bit, 2=length-delimited, 5=32-bit. This enables unknown fields to be skipped (forward compatibility) and old fields to be ignored (backward compatibility).

```
┌──────────────────────────────────────────────────────┐
│ Field 1 (name="vm-abc"): 0x0A 0x06 0x76 0x6D...    │
│ Field 2 (vcpus=4):        0x10 0x04                  │
│ Field 3 (memory_mb=2048): 0x18 0x80 0x10             │
│ (varints are LEB128 encoded)                         │
└──────────────────────────────────────────────────────┘
```

Key property: **no schema required at decode time for skipping fields** — the wire type encodes the length. This is critical for schema evolution.

#### FlatBuffers

Zero-copy, zero-parse serialization. The serialized bytes are the object — no deserialization step. Reads access the buffer directly with offset arithmetic.

```
┌─────────────────────────────────────────────────────┐
│  FlatBuffer wire format                              │
│                                                     │
│  [root offset][vtable][data fields...]              │
│       ↑                                             │
│  Pointer into buffer — reads are direct memory      │
│  accesses with bounds checking, no heap allocation  │
└─────────────────────────────────────────────────────┘
```

**Use case:** High-frequency telemetry, game networking, robotics, DPDK packet metadata. Used in TensorFlow Lite inference.

**Security:** Because FlatBuffers requires explicit bounds checking via the verifier step, you must call `flatbuffers::Verifier` before trusting a buffer from an untrusted source. Skipping this leads to out-of-bounds reads.

#### Cap'n Proto

Designed by Kenton Varda (protobuf author) to fix protobuf's parsing overhead. Uses a capability-based RPC system (`capnp rpc`). In-memory format identical to wire format (like FlatBuffers but with stronger RPC semantics).

```capnp
struct CreateVMRequest {
  name      @0 :Text;
  vcpus     @1 :Int32;
  memoryMb  @2 :Int64;
  disk      @3 :VMDisk;
}

interface VMService {
  createVM @0 (request: CreateVMRequest) -> (response: CreateVMResponse);
  # Capabilities can be passed as interface references:
  getBootstrap @1 () -> (cap: AnyPointer);
}
```

Cap'n Proto RPC supports **promise pipelining**: you can use the result of a call as an argument to the next call before the first completes, eliminating a round trip. Useful for distributed object systems.

#### MessagePack

Binary JSON. Same data model as JSON, more compact encoding. Good for dynamic schemas and polyglot environments.

#### Comparison

| Format | Parse Speed | Size | Schema | Zero-copy | Streaming | Best For |
|--------|------------|------|--------|-----------|-----------|----------|
| JSON | Slow | Large | Optional | No | No | REST APIs, config |
| Protobuf | Fast | Small | Required | No | Yes (delimited) | gRPC, most RPC |
| FlatBuffers | Zero | Small | Required | Yes | No | HFT, games, telemetry |
| Cap'n Proto | Zero | Small | Required | Yes | Yes | Capability RPC |
| MessagePack | Medium | Medium | Optional | No | No | Polyglot, Redis |
| Avro | Fast | Small | Required (side-channel) | No | Yes | Kafka, Hadoop |
| CBOR | Medium | Medium | Optional | No | No | IoT, COSE, CDDL |

---

### 2.3 gRPC — The Dominant Cloud-Native RPC

gRPC is Google's RPC framework: protobuf serialization over HTTP/2, with full duplex streaming, multiplexing, header compression, and first-class TLS. It is the de facto RPC standard in CNCF/Kubernetes ecosystems.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         gRPC Stack                              │
│                                                                 │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │ Protobuf IDL │─codegen─►  Generated Client/Server Stubs   │  │
│  └──────────────┘         └──────────────────────────────────┘  │
│                                    │                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                  gRPC Core                             │     │
│  │  Interceptors → Channel → Codec → Compressor           │     │
│  └────────────────────────────────────────────────────────┘     │
│                            │                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              HTTP/2 Transport                          │     │
│  │  Streams  │  Flow Control  │  Header Compression (HPACK)│    │
│  └────────────────────────────────────────────────────────┘     │
│                            │                                    │
│              TLS 1.3 (mTLS for service-to-service)             │
│                            │                                    │
│              TCP / Unix Domain Socket                          │
└─────────────────────────────────────────────────────────────────┘
```

#### HTTP/2 Framing for gRPC

Each gRPC message becomes:
1. An HTTP/2 HEADERS frame (method, path, content-type, metadata)
2. An HTTP/2 DATA frame with: `[compression flag (1 byte)][message length (4 bytes)][protobuf bytes]`

Multiple concurrent RPCs are multiplexed on a single TCP connection as HTTP/2 streams — solving head-of-line blocking that existed in HTTP/1.1.

```
TCP Connection
├── Stream 1: CreateVM() RPC
├── Stream 3: ListVMs() RPC (concurrent)
├── Stream 5: WatchVMs() streaming RPC (long-lived)
└── Stream 7: Health check
```

#### RPC Types

```protobuf
service VMService {
  // Unary: one request, one response
  rpc CreateVM(CreateVMRequest) returns (CreateVMResponse);

  // Server-streaming: one request, many responses
  rpc WatchVMEvents(WatchRequest) returns (stream VMEvent);

  // Client-streaming: many requests, one response
  rpc BulkCreateVMs(stream CreateVMRequest) returns (BulkResponse);

  // Bidirectional streaming: many requests, many responses
  rpc Console(stream ConsoleInput) returns (stream ConsoleOutput);
}
```

#### Go Implementation

```go
// server/main.go
type vmServer struct {
    pb.UnimplementedVMServiceServer
    store VMStore
}

func (s *vmServer) CreateVM(ctx context.Context,
    req *pb.CreateVMRequest) (*pb.CreateVMResponse, error) {

    // Extract peer metadata for authz
    peer, _ := peer.FromContext(ctx)
    md, _ := metadata.FromIncomingContext(ctx)

    // Validate input
    if req.GetVcpus() > 128 {
        return nil, status.Errorf(codes.InvalidArgument,
            "vcpu count %d exceeds maximum 128", req.GetVcpus())
    }

    // Create VM
    id, err := s.store.Create(ctx, req)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "store: %v", err)
    }

    return &pb.CreateVMResponse{VmId: id, Status: "CREATING"}, nil
}

func main() {
    // mTLS configuration
    cert, _ := tls.LoadX509KeyPair("server.crt", "server.key")
    caCert, _ := os.ReadFile("ca.crt")
    caPool := x509.NewCertPool()
    caPool.AppendCertsFromPEM(caCert)

    tlsCfg := &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientAuth:   tls.RequireAndVerifyClientCert,
        ClientCAs:    caPool,
        MinVersion:   tls.VersionTLS13,
    }

    srv := grpc.NewServer(
        grpc.Creds(credentials.NewTLS(tlsCfg)),
        grpc.ChainUnaryInterceptor(
            otelgrpc.UnaryServerInterceptor(),    // tracing
            authInterceptor,                       // authn/authz
            rateLimitInterceptor,                  // rate limiting
            validationInterceptor,                 // input validation
        ),
        grpc.ChainStreamInterceptor(
            otelgrpc.StreamServerInterceptor(),
            streamAuthInterceptor,
        ),
        grpc.MaxRecvMsgSize(4*1024*1024),          // 4MB limit
        grpc.KeepaliveParams(keepalive.ServerParameters{
            MaxConnectionIdle: 30 * time.Minute,
            Time:              10 * time.Second,
            Timeout:           5 * time.Second,
        }),
    )

    pb.RegisterVMServiceServer(srv, &vmServer{})
    reflection.Register(srv)   // for grpcurl/grpc-gateway in dev

    lis, _ := net.Listen("tcp", ":8443")
    srv.Serve(lis)
}
```

#### gRPC-go Client with Connection Pooling and Retry

```go
conn, err := grpc.NewClient("vm-service:8443",
    grpc.WithTransportCredentials(credentials.NewTLS(clientTLSCfg)),
    grpc.WithDefaultServiceConfig(`{
        "methodConfig": [{
            "name": [{"service": "compute.v1.VMService"}],
            "retryPolicy": {
                "maxAttempts": 4,
                "initialBackoff": "0.1s",
                "maxBackoff": "1s",
                "backoffMultiplier": 2,
                "retryableStatusCodes": ["UNAVAILABLE", "RESOURCE_EXHAUSTED"]
            },
            "timeout": "10s"
        }],
        "loadBalancingConfig": [{"round_robin": {}}]
    }`),
    grpc.WithStatsHandler(otelgrpc.NewClientHandler()),
)
```

**gRPC status codes and their meaning:**

| Code | Meaning | Client action |
|------|---------|--------------|
| `OK` | Success | — |
| `CANCELLED` | Client cancelled | — |
| `INVALID_ARGUMENT` | Bad request | Fix and retry |
| `NOT_FOUND` | Resource missing | Don't retry |
| `ALREADY_EXISTS` | Conflict | Don't retry |
| `PERMISSION_DENIED` | Authn/authz failure | Don't retry |
| `RESOURCE_EXHAUSTED` | Rate limit/quota | Retry with backoff |
| `FAILED_PRECONDITION` | State issue | Don't retry |
| `UNAVAILABLE` | Service down | Retry with backoff |
| `DEADLINE_EXCEEDED` | Timeout | Retry if idempotent |
| `INTERNAL` | Server bug | Maybe retry once |

**gRPC interceptors — the middleware chain:**

```go
// Auth interceptor extracting JWT from metadata
func authInterceptor(ctx context.Context, req interface{},
    info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {

    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }

    tokens := md.Get("authorization")
    if len(tokens) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing token")
    }

    claims, err := validateJWT(strings.TrimPrefix(tokens[0], "Bearer "))
    if err != nil {
        return nil, status.Errorf(codes.Unauthenticated, "invalid token: %v", err)
    }

    // Inject claims into context for handlers
    ctx = context.WithValue(ctx, claimsKey{}, claims)
    return handler(ctx, req)
}
```

---

### 2.4 gRPC Real-World Architecture in Kubernetes

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Kubernetes Control Plane                          │
│                                                                      │
│  kubelet ─── gRPC (CRI) ──► containerd ─── gRPC ──► shim v2        │
│     │                           │                                    │
│     │         ┌─────────────────┘                                    │
│     │         │  /run/containerd/containerd.sock (Unix socket)       │
│     │                                                                │
│     └── gRPC (CSI) ──► CSI Driver (ceph-csi, aws-ebs-csi)          │
│     │        /var/lib/kubelet/plugins/<driver>/csi.sock              │
│     │                                                                │
│     └── gRPC (CNI-like) ──► Node-local services                     │
│                                                                      │
│  kube-apiserver ─── gRPC ──► etcd  (port 2379/2380)                │
│  kube-apiserver ──── REST/Protobuf ──► kubectl/clients              │
│                                                                      │
│  Istio/Envoy ─── xDS (gRPC streaming) ──► istiod                   │
│  Cilium agent ─── Hubble (gRPC) ──► Hubble relay                   │
└──────────────────────────────────────────────────────────────────────┘
```

**xDS protocol** (Envoy's API): A set of gRPC services (LDS, RDS, CDS, EDS, SDS, ADS) that service meshes use to push configuration to data-plane proxies. The bidirectional streaming RPC model allows istiod to push policy updates to thousands of Envoy sidecars without polling.

---

### 2.5 gRPC Security Deep Dive

#### mTLS — Mutual TLS

Standard gRPC security for service-to-service. Both client and server present certificates:

```
Client                                    Server
  │─── ClientHello ──────────────────────► │
  │◄── ServerHello + Certificate ──────── │
  │─── ClientCertificate ────────────────► │  ← mutual authentication
  │◄── (verify) ─── Finished ──────────── │
  │─── Application Data (HTTP/2) ────────► │
```

In a Kubernetes service mesh (Istio, Linkerd), mTLS is transparently injected:
- Certificates issued by the mesh CA (SPIFFE/SPIRE)
- Identity encoded as SPIFFE URI: `spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>`
- Certificates rotated automatically (short-lived, e.g., 24h)

#### Token-based AuthN via gRPC Metadata

```go
// Per-RPC credentials
type jwtCreds struct{ token string }
func (j *jwtCreds) GetRequestMetadata(ctx context.Context, uri ...string) (map[string]string, error) {
    return map[string]string{"authorization": "Bearer " + j.token}, nil
}
func (j *jwtCreds) RequireTransportSecurity() bool { return true }

conn, _ := grpc.NewClient(addr,
    grpc.WithTransportCredentials(tlsCreds),
    grpc.WithPerRPCCredentials(&jwtCreds{token: workloadToken}),
)
```

#### gRPC Authorization Policy (Envoy/Istio)

```yaml
# Istio AuthorizationPolicy
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: vm-service-authz
spec:
  selector:
    matchLabels:
      app: vm-service
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/compute/sa/scheduler"   # SPIFFE identity
  to:
  - operation:
      methods: ["POST"]
      paths: ["/compute.v1.VMService/CreateVM"]
```

---

### 2.6 JSON-RPC

A simple, stateless RPC protocol using JSON. Spec at jsonrpc.org. Used where simplicity trumps performance.

```json
// Request
{"jsonrpc":"2.0","id":1,"method":"vm.create","params":{"name":"test","vcpus":4}}

// Response
{"jsonrpc":"2.0","id":1,"result":{"vm_id":"vm-abc123"}}

// Error
{"jsonrpc":"2.0","id":1,"error":{"code":-32602,"message":"Invalid params"}}

// Notification (no id — no response expected)
{"jsonrpc":"2.0","method":"vm.status_changed","params":{"vm_id":"vm-abc","status":"RUNNING"}}

// Batch
[{"jsonrpc":"2.0","id":1,...}, {"jsonrpc":"2.0","id":2,...}]
```

**Error codes:** -32700 Parse error, -32600 Invalid Request, -32601 Method not found, -32602 Invalid params, -32603 Internal error. Application-defined errors: -32000 to -32099.

**Real-world:** Ethereum JSON-RPC (the blockchain node API), Bitcoin Core RPC, Language Server Protocol (LSP used by every IDE), OpenBMC (hardware management).

---

### 2.7 Apache Thrift

Facebook's polyglot RPC framework. IDL generates code in 25+ languages. Binary, compact, and JSON protocols. Supports multiplexing, framing, and multiple transport layers.

```thrift
namespace go compute.v1

struct CreateVMRequest {
  1: required string name,
  2: required i32 vcpus,
  3: required i64 memory_mb,
  4: optional list<string> tags,
}

exception VMException {
  1: i32 error_code,
  2: string message,
}

service VMService {
  CreateVMResponse createVM(1: CreateVMRequest req) throws (1: VMException ex),
  void deleteVM(1: string vm_id) throws (1: VMException ex),
  oneway void triggerGC(),  // fire and forget
}
```

```bash
thrift --gen go:package_prefix=github.com/myorg/compute/ vm.thrift
```

**Used in:** Cassandra (CQL used to be Thrift), HBase, Scribe. Now mostly legacy in Cassandra world (replaced by CQL/native protocol).

---

### 2.8 Apache Avro + Schema Registry

Avro is a dynamic schema format tightly coupled with Kafka's ecosystem. Schema is stored separately (in a Schema Registry, not embedded in messages), enabling very compact messages (just field values, no names or types on the wire).

```json
{
  "type": "record",
  "name": "VMEvent",
  "namespace": "com.myorg.compute",
  "fields": [
    {"name": "vm_id", "type": "string"},
    {"name": "event_type", "type": {"type": "enum", "name": "EventType",
      "symbols": ["CREATED", "STARTED", "STOPPED", "DELETED"]}},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"}
  ]
}
```

```
Kafka Message
┌──────────────────────────────────┐
│ magic byte (0x00) | schema_id(4B)│  ← Confluent wire format
│ avro payload (no field names)    │  ← consumer looks up schema by ID
└──────────────────────────────────┘
```

**Schema evolution rules:** Backward compatible (new schema reads old data): add fields with defaults, remove required fields. Forward compatible (old schema reads new data): add fields with defaults. Full compatible: both.

**Real-world:** Kafka → Flink → data lake pipelines. Confluent Platform. Used for high-volume event streaming where wire size matters.

---

### 2.9 REST vs RPC: When to Use What

This is a recurring architectural debate. The distinction matters in systems design:

| | REST (Resource-oriented) | RPC (Action-oriented) |
|--|--|--|
| **Abstraction** | Resources (nouns) | Operations (verbs) |
| **Interface** | HTTP methods on URIs | Named procedures |
| **Caching** | HTTP cache semantics (GET cacheable) | Explicit (non-trivial) |
| **Browser compatibility** | Native | Needs grpc-web |
| **Schema** | OpenAPI/JSON Schema (optional) | IDL required |
| **Streaming** | SSE/WebSocket (add-on) | First-class |
| **Type safety** | Generated from OpenAPI | Native IDL types |
| **Versioning** | URI `/v1/`, `/v2/` | Package namespaces |
| **Best for** | Public APIs, CRUD resources | Internal service-to-service |

**Practical rule:** Use REST/HTTP+JSON for external-facing APIs (clients are browsers, third parties, curl users). Use gRPC for internal service-to-service communication where you control both ends, need streaming, or performance matters.

**gRPC-Gateway:** Auto-generates an HTTP/JSON reverse proxy from your proto file — lets you serve both gRPC and REST from one service:

```protobuf
import "google/api/annotations.proto";

service VMService {
  rpc CreateVM(CreateVMRequest) returns (CreateVMResponse) {
    option (google.api.http) = {
      post: "/v1/vms"
      body: "*"
    };
  }
}
```

---

### 2.10 Connect Protocol

A newer protocol from Buf that is compatible with gRPC and gRPC-Web but also works natively with standard HTTP/1.1+. Libraries in Go, TypeScript, Swift, Kotlin, Rust.

```
gRPC        → HTTP/2 + application/grpc
gRPC-Web    → HTTP/1.1 or HTTP/2 + application/grpc-web
Connect     → HTTP/1.1 or HTTP/2 + application/connect+proto (or +json)
```

Connect is increasingly used where grpc-web (which requires a proxy) was previously necessary.

---

### 2.11 NATS and Message-Oriented RPC

For async, decoupled, or pub/sub RPC patterns, NATS (and JetStream) provides:

```
Request-Reply (pseudo-RPC):
Publisher ──publish("vm.create", req)──► NATS ──► Subscriber
                                              ◄──── reply(resp) ────
(reply-to inbox injected by client: _INBOX.abc123)

Fan-out:
Publisher ──publish("vm.events.>")──► NATS ──► Sub 1 (logger)
                                           └──► Sub 2 (alerter)

Queue Group (load balance):
Publisher ──► NATS ──► [workers in group "vm-processors"] → one receives
```

NATS pub/sub RPC is used in:
- Async task dispatch (container image pulls, VM provisioning queues)
- Event streaming between microservices
- NATS JetStream for durable, exactly-once delivery with consumer acknowledgments

---

### 2.12 Envoy xDS: Push-Based Configuration RPC

xDS (discovery service) is a gRPC-based streaming RPC protocol used by Envoy and Cilium for runtime configuration:

```
Control Plane (istiod)
    │
    │  BiDi streaming gRPC (ADS — Aggregated Discovery Service)
    │
    ▼
Data Plane (Envoy sidecar)

Flow:
1. Envoy: sends DiscoveryRequest{type_url: "type.googleapis.com/envoy.config.listener.v3.Listener", version_info: ""}
2. Control plane: sends DiscoveryResponse{resources: [Listener{...}], version_info: "v2", nonce: "abc"}
3. Envoy: ACK DiscoveryRequest{version_info: "v2", response_nonce: "abc"} or NACK with error
```

This push model (rather than poll) enables sub-second configuration propagation to thousands of proxies. The version + nonce mechanism provides exactly-once semantics over a streaming connection.

---

### 2.13 RPC Failure Modes and Mitigation

```
┌────────────────────────────────────────────────────────────────────┐
│                    Failure Taxonomy                                │
│                                                                    │
│  Network partition ─── client sends, server never receives        │
│  Server crash ──────── mid-processing, partial work done          │
│  Timeout ───────────── work may or may not have completed         │
│  Slow consumer ─────── back-pressure, queue buildup               │
│  Retry storm ───────── cascading retry amplification              │
│  Split brain ───────── two clients believe they own resource      │
└────────────────────────────────────────────────────────────────────┘
```

**Idempotency:** The single most important property for safe retries. Assign client-generated idempotency keys:

```protobuf
message CreateVMRequest {
  string idempotency_key = 1;  // e.g., UUID generated by client
  string name = 2;
  // ...
}
```

Server stores `(idempotency_key → response)` in a durable store (Redis, Postgres). On duplicate, return cached response. This makes a non-idempotent operation (resource creation) safe to retry.

**Circuit Breaker pattern:**

```
CLOSED ──(failures > threshold)──► OPEN ──(timeout elapsed)──► HALF-OPEN
  ↑                                  │ (fail fast)                 │
  └─────────────(success)────────────┘                            │
                                     ◄──────(try one request)──────┘
```

Libraries: `go-resilience`, `hystrix-go`, `gobreaker`, Envoy's circuit breaker (native in data plane).

**Deadline propagation:** Deadlines should be propagated through call chains, not reset at each hop:

```go
// Don't: set new timeout at each service
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)  // wrong if upstream had 2s left

// Do: propagate existing deadline, but cap at service's own limit
deadline, ok := ctx.Deadline()
remaining := time.Until(deadline)
maxTimeout := 5 * time.Second
if !ok || remaining > maxTimeout {
    remaining = maxTimeout
}
ctx, cancel = context.WithTimeout(ctx, remaining)
```

gRPC propagates deadlines as `grpc-timeout` header automatically if you pass context correctly.

---

### 2.14 RPC Over Unix Sockets

High-performance local RPC (same host) over Unix domain sockets — bypasses TCP stack, no loopback:

```go
// gRPC over UDS — used by containerd, kubelet↔CRI
conn, _ := grpc.NewClient("unix:///run/containerd/containerd.sock",
    grpc.WithTransportCredentials(insecure.NewCredentials()),  // UDS: no TLS needed
    // BUT: use SO_PEERCRED for authorization instead
)

// Server
lis, _ := net.Listen("unix", "/run/myservice/rpc.sock")
os.Chmod("/run/myservice/rpc.sock", 0660)     // restrict access
// Ownership: root:mygroup, mode 0660
```

**Performance:** gRPC over UDS achieves ~2-3x higher throughput vs TCP loopback because there's no TCP segmentation, checksum computation, or loopback device overhead.

**Security:** No network interception possible. Use `SO_PEERCRED` for identity. File permissions and SELinux/AppArmor labels for access control.

---

## Part III: Security Threat Model

### 3.1 IPC Attack Surface

```
┌──────────────────────────────────────────────────────────────────┐
│                    IPC Threat Model                              │
│                                                                  │
│  Attack Vector          │  Mechanism            │  Mitigation   │
│─────────────────────────┼───────────────────────┼──────────────│
│  FIFO symlink attack    │  replace FIFO w/ link │  O_NOFOLLOW  │
│  Shared mem poisoning   │  write to shm before  │  Validate    │
│                         │  privileged reads     │  all shm     │
│  Signal injection       │  kill(pid, sig) from  │  seccomp     │
│                         │  unprivileged proc    │  sigprocmask │
│  Pipe fd leak           │  inherit fd across    │  O_CLOEXEC   │
│                         │  exec()               │  everywhere  │
│  UDS path race          │  bind squatting       │  abstract ns │
│  MQ flood               │  fill queue, DoS      │  O_NONBLOCK  │
│  SysV IPC leak          │  persistent on crash  │  POSIX IPC   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 RPC Attack Surface

```
┌──────────────────────────────────────────────────────────────────┐
│                    RPC Threat Model                              │
│                                                                  │
│  Threat                 │  Impact               │  Mitigation   │
│─────────────────────────┼───────────────────────┼──────────────│
│  No mTLS                │  MITM, data exposure  │  mTLS always │
│  Cert pinning bypass    │  MITM with valid cert  │  SPIFFE      │
│  Proto injection        │  Data corruption      │  Validate    │
│  Large message DoS      │  OOM server           │  MaxRecvMsg  │
│  RPC amplification      │  Retry storm          │  Rate limit  │
│  Reflection endpoint    │  Schema disclosure    │  Disable prod│
│  Unauthn streaming      │  Resource exhaustion  │  Auth on 1st │
│  Slow client attack     │  Stream starvation    │  Keepalive   │
│  Deserialization bomb   │  CPU/memory           │  Size limits │
│  Header injection       │  SSRF, log poisoning  │  Sanitize md │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Defense-in-Depth Layering

```
Application Layer:   Input validation, business logic authz
  │
RPC Layer:           Rate limiting, auth interceptors, message size limits
  │
Transport Layer:     mTLS, certificate rotation (SPIRE), ALPN pinning
  │
Network Layer:       Network policy (Cilium/Calico), firewall rules
  │
OS Layer:            seccomp BPF, AppArmor/SELinux, namespaces, cgroups
  │
Hardware Layer:      SGX enclaves, TPM attestation, secure boot
```

---

## Part IV: Architecture View

### Local Process Communication Decision Tree

```
Need to communicate between processes?
            │
            ├── Same host?
            │       │
            │       ├── High throughput, shared trust?
            │       │       └── Shared memory + ring buffer (DPDK, io_uring)
            │       │
            │       ├── Need message framing + identity?
            │       │       └── Unix Domain Socket (SOCK_SEQPACKET or STREAM)
            │       │               └── mTLS or SO_PEERCRED for authz
            │       │
            │       ├── Simple parent→child data pipeline?
            │       │       └── Anonymous pipe (fork + pipe2)
            │       │
            │       ├── Discrete messages + priorities?
            │       │       └── POSIX MQ
            │       │
            │       └── Async notification only?
            │               └── eventfd / signalfd
            │
            └── Cross-host?
                    │
                    ├── Low latency, type-safe, streaming?
                    │       └── gRPC (protobuf/HTTP2/mTLS)
                    │
                    ├── Browser client or public API?
                    │       └── REST/HTTP+JSON or Connect protocol
                    │
                    ├── Event streaming, async, decoupled?
                    │       └── NATS / Kafka (Avro or protobuf)
                    │
                    ├── Zero-copy, ultra-low latency?
                    │       └── RDMA (InfiniBand/RoCE) or DPDK + shared memory
                    │
                    └── Legacy/polyglot enterprise?
                            └── Thrift or JSON-RPC
```

---

## Part V: Production Considerations

### 5.1 Observability

Every RPC call needs three signals:

**Metrics (RED method):**
- Rate: `grpc_server_handled_total{grpc_method="CreateVM"}`
- Errors: `grpc_server_handled_total{grpc_code!="OK"}`
- Duration: `grpc_server_handling_seconds_bucket`

**Traces (OpenTelemetry):**
```go
// gRPC interceptor injects trace context into HTTP/2 headers
// "traceparent" W3C header propagates across service boundaries
conn, _ := grpc.NewClient(addr,
    grpc.WithStatsHandler(otelgrpc.NewClientHandler(
        otelgrpc.WithTracerProvider(tracerProvider),
        otelgrpc.WithPropagators(propagation.TraceContext{}),
    )),
)
```

**Logs:** Structured, with trace ID, method, peer identity, status code, duration. Never log request bodies (may contain secrets).

### 5.2 Load Balancing gRPC

gRPC multiplexes streams on one HTTP/2 connection — L4 load balancers (AWS NLB, kube-proxy) won't distribute individual RPCs, only connections. Solutions:

- **Client-side load balancing:** gRPC name resolver + `round_robin` policy (works with Kubernetes headless service DNS)
- **L7 proxy:** Envoy, Linkerd, or NGINX stream gRPC-aware — distributes per-RPC
- **gRPC-LB protocol:** Used by GCP's GFE; grpc client queries a lookaside load balancer

### 5.3 API Versioning and Schema Evolution

```
Protobuf best practices:
  - Never reuse field numbers (deleted fields: mark reserved)
  - Never change field types
  - New required fields = breaking change (use optional everywhere)
  - Use package versioning: compute.v1, compute.v2
  - Version negotiation via gRPC metadata headers

reserved 4, 5;           // prevent reuse of deleted field numbers
reserved "old_name";     // prevent reuse of deleted field names
```

### 5.4 Roll-out/Rollback Plan

```
Rolling update with API compatibility:
  Phase 1: Deploy v2 server (serves both v1 + v2 protos)
  Phase 2: Deploy v2 clients (send v2 protos)
  Phase 3: Deprecate v1 handling
  Phase 4: Remove v1 code

Rollback trigger:
  - gRPC error rate > 1% for 5 minutes → auto-rollback
  - P99 latency > 2x baseline → alert + manual review
  - Use Kubernetes progressive delivery (Argo Rollouts, Flagger)
    with Prometheus metrics as rollout gate
```

---

## Part VI: Tests, Fuzzing, and Benchmarks

```bash
# Unit test gRPC server with bufconn (in-memory transport)
import "google.golang.org/grpc/test/bufconn"
lis := bufconn.Listen(1 << 20)
srv := grpc.NewServer(interceptors...)
pb.RegisterVMServiceServer(srv, &vmServer{})
go srv.Serve(lis)
conn, _ := grpc.NewClient("passthrough:///test",
    grpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {
        return lis.DialContext(ctx)
    }),
    grpc.WithTransportCredentials(insecure.NewCredentials()),
)

# Fuzz gRPC deserialization
go-fuzz -func FuzzCreateVMRequest

# Benchmark
go test -bench=BenchmarkCreateVM -benchmem -count=5 ./...

# Integration test: grpcurl
grpcurl -insecure -d '{"name":"test","vcpus":4}' \
    localhost:8443 compute.v1.VMService/CreateVM

# Load test: ghz
ghz --insecure --proto vm.proto --call compute.v1.VMService.CreateVM \
    -d '{"name":"test","vcpus":4}' -n 10000 -c 50 localhost:8443

# Shared memory fuzzing: AFL++ on C IPC code
AFL_USE_ASAN=1 AFL_USE_UBSAN=1 afl-fuzz -i corpus -o findings ./ipc_consumer @@
```

---

## References

- *Linux man pages:* `pipe(7)`, `unix(7)`, `socket(7)`, `mq_overview(7)`, `shm_overview(7)`, `netlink(7)`, `io_uring(7)`
- *Stevens, APUE:* Chapter 15 (IPC), Chapter 17 (Advanced IPC) — foundational
- *gRPC Specification:* https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
- *SPIFFE/SPIRE:* https://spiffe.io — workload identity for service mTLS
- *Buf/Connect Protocol:* https://connectrpc.com/docs/protocol
- *io_uring:* Lord of the io_uring — https://unixism.net/lsp/
- *Protobuf encoding:* https://protobuf.dev/programming-guides/encoding/
- *Envoy xDS API:* https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol
- *DPDK ring library:* https://doc.dpdk.org/guides/prog_guide/ring_lib.html
- *CVE-2022-29582 io_uring:* kernel.org advisory

---

## Next 3 Steps

1. **Audit your IPC surface:** Run `lsof -U` (Unix sockets), `ipcs -a` (SysV IPC), `ls -la /proc/*/fd | grep pipe` (open pipes) on a production node. For each, answer: who owns it, what trust boundary does it cross, is data validated on both sides, what's the DoS surface?

2. **Instrument your gRPC services:** Add `otelgrpc` interceptors if not present, ensure `grpc_server_handled_total` and `grpc_server_handling_seconds` are scraped by Prometheus. Set `MaxRecvMsgSize`, `MaxSendMsgSize`, and keepalive parameters explicitly — defaults are often too permissive.

3. **Replace any SysV IPC or raw shared memory with memfd + SCM_RIGHTS:** Identify legacy `shmget/semget/msgget` usage (`ipcs -a`), model the trust boundary, replace with `memfd_create` + Unix socket `SCM_RIGHTS` + explicit sealing (`F_SEAL_WRITE` after handoff), and add a FlatBuffers or protobuf validation layer on the consumer side before processing any data from the shared region.

# Summary

Short: IPC (inter-process communication) is how *processes* on the same machine exchange data and coordinate; RPC (remote procedure call) is a higher-level request/response abstraction that makes calling remote services look like local procedure calls. This guide explains mechanisms, tradeoffs, design patterns, security, testing, performance, and real-world scenarios — with concrete design and rollout recommendations.

---

# 1) Quick conceptual map

* **IPC** — local-machine mechanisms: pipes/FIFOs, UNIX domain sockets, shared memory + semaphores, POSIX message queues, signals, memory mapped files, D-Bus, etc. Best for low latency, tight coupling between processes.
* **RPC** — networked procedure call abstractions: HTTP/JSON RPC, gRPC (HTTP/2 + Protobuf), Thrift, Apache Avro RPC, JSON-RPC, XML-RPC, custom binary protocols. Best for decoupled microservices, cross-language interoperability, distributed systems.
* **Where they overlap** — UNIX domain sockets and loopback TCP can serve as both IPC and RPC channels. Serialization, framing, flow control and authentication are common concerns.

---

# 2) Foundations and primitives (detailed)

## Pipes & FIFOs

* **What:** unidirectional (pipes) or named FIFO (bidirectional with two FIFOs). Stream of bytes.
* **Semantics:** byte stream, blocking/non-blocking I/O, atomicity guarantees for writes up to PIPE_BUF (POSIX).
* **Use cases:** parent→child streaming, simple producer/consumer, shell pipelines.
* **Tradeoffs:** low overhead, no message framing, access control via filesystem permissions.

## UNIX domain sockets

* **What:** socket API over filesystem namespace; supports SOCK_STREAM, SOCK_DGRAM, SOCK_SEQPACKET.
* **Semantics:** local socket with file system permissions, supports credentials passing (SO_PEERCRED), SCM_RIGHTS (fd passing).
* **Use cases:** container runtimes (docker engine), DB local clients (Postgres can use it), system daemons (systemd, journald), language runtimes.
* **Tradeoffs:** low latency, full duplex, supports file descriptor passing; best choice when process isolation but low latency needed.

## Shared memory + synchronization (POSIX shm, mmap)

* **What:** memory region visible to multiple processes; needs synchronization (mutex, futex, semaphores).
* **Semantics:** fastest path for bulk data; need careful memory ordering, cache coherency considerations on multicore.
* **Use cases:** high throughput streaming (media, sensors), zero-copy IPC in databases and in-memory stores.
* **Tradeoffs:** complexity: race conditions, ABA, memory visibility, lifecycle cleanup, security (who can mmap), page alignment and NUMA considerations.

## POSIX message queues & System V IPC

* **What:** structured message queues with priority; kernel managed.
* **Use cases:** OS-level message passing, real-time systems.
* **Tradeoffs:** kernel overhead, limits in queue sizes, portability quirks.

## Signals

* **What:** async notifications to processes (SIGTERM, SIGUSR1).
* **Use cases:** simple notifications, process lifecycle management.
* **Tradeoffs:** low data capacity, racey, limited semantics.

## D-Bus & Message Buses

* **What:** higher-level IPC bus for desktop/OS services (e.g., session/system buses in Linux). Provides service discovery, authentication.
* **Use cases:** desktop services (GNOME/KDE), system services.
* **Tradeoffs:** higher latency, feature rich (auth, namespacing).

---

# 3) RPC: architecture and components (in-depth)

An RPC system typically includes:

* **IDL (Interface Definition Language)** or schema: describes methods, request/response types, options (Protobuf, Thrift, OpenAPI/Swagger).
* **Code generation / stubs:** client and server skeletons (marshal/unmarshal + transport glue).
* **Transport:** TCP, TLS, HTTP/1.1 or HTTP/2, WebSockets, QUIC, or UNIX domain sockets for local calls.
* **Serialization:** JSON, Protobuf, MessagePack, CBOR, FlatBuffers, Cap’n Proto — tradeoffs: size, speed, forward/backward compatibility, zero-copy capabilities.
* **Middleware / Interceptors:** auth, retries, metrics, tracing, circuit breakers.
* **Service discovery & load balancing:** DNS, Consul, etcd, Kubernetes Service, sidecars.
* **Observability:** metrics (latency histograms p50/p95/p99), distributed tracing (OpenTelemetry), structured logs, health checks.

### Important RPC patterns

* **Unary (request→response)** — simplest.
* **Server streaming** — one request → stream of messages.
* **Client streaming** — stream of messages → one response.
* **Bidirectional streaming** — two-way concurrent streams (gRPC supports all).
* **Pub/Sub** — not RPC per se; message broker decouples producers/consumers.
* **Command & Event models** — synchronous vs eventual consistency tradeoffs.

---

# 4) Serialization & schema management

* **Protobuf/FlatBuffers/Cap’n Proto**: compact binary, schema required; strong for performance and versioning.
* **JSON/MessagePack**: human readable (JSON), flexible; versioning via tolerant decoders; slower and larger.
* **Design rules:** use explicit field numbers (Protobuf), never reuse numeric tags, prefer optional fields for forward compatibility, document schema changes and migration strategy.
* **Versioning strategies:** additive-only changes, multi-version support, compatibility tests (contract tests), API gateways for translation.

---

# 5) Performance characteristics & tradeoffs

* **Latency:** shared memory < UNIX sockets < loopback TCP < network TCP. Serialization adds overhead.
* **Throughput:** depends on batching, framing, zero-copy. Shared memory + ring buffers give highest throughput.
* **Concurrency:** choose non-blocking I/O and async frameworks for high-concurrency servers (epoll/kqueue/io_uring on Linux).
* **Framing & pipelining:** length-prefixed framing reduces ambiguity; HTTP/2 multiplexing reduces head-of-line blocking.
* **Backpressure:** must implement in streaming scenarios — flow control (HTTP/2 windowing, application-layer credits).

---

# 6) Reliability, consistency & semantics

* **Idempotence:** critical for safe retries. Design RPCs to be idempotent where possible.
* **Exactly-once vs at-least-once:** networked systems usually achieve at-least-once; exactly-once requires consensus or deduplication (request IDs + dedupe store).
* **Ordering guarantees:** provide sequence numbers if order matters, or rely on session affinity with single connection/stream.
* **Transactions:** distributed transactions (2PC) are expensive; prefer compensation patterns or saga-based approaches.

---

# 7) Security model & hardening (threats + mitigations)

## Threats

* Eavesdropping / MitM on transport.
* Replay attacks.
* Authentication/authorization bypass.
* Deserialization attacks and code execution.
* Resource exhaustion (DoS), memory corruption via malformed messages.
* Privilege escalation via shared resources (fd passing, shm).
* Data leakage via logs/traces.

## Mitigations

* **Transport security:** mTLS (mutual TLS) for service-to-service; or TLS for client-server. Prefer ALPN (HTTP/2) where possible.
* **Authentication:** JWTs, OAuth2, SPIFFE/SPIRE for mTLS identities, token rotation, short-lived certs.
* **Authorization:** RBAC, ABAC, scope-limited tokens; principle of least privilege for sockets and shm files (filesystem permissions).
* **Input validation & safe deserialization:** use strict schema validators; avoid `eval`/unrestricted deserialization. Run deserializers with memory/CPU limits where possible.
* **Rate limiting and quotas:** client- and service-side rate limiting to prevent abuse.
* **Resource limits & sandboxing:** cgroups, namespaces, seccomp, chroot; run services as non-root.
* **Replay protection:** include nonces/timestamps, signatures, and short expiry.
* **Logging redaction & secure observability:** avoid logging secrets; secure telemetry pipelines.
* **Auditing & monitoring:** detect anomalous traffic patterns, spikes in latency or error rates, unauthorized socket access.

---

# 8) Real-world use cases & scenarios (concrete)

## Use case A — Low-latency local IPC (database engine + storage process)

* **Problem:** DB engine and storage process need to exchange large pages without copy.
* **Solution:** memory-mapped shared memory + ring buffer for control messages; use futexes for notification; use capability-based permissions for shared memory segments. Use versioned message structures for compatibility.
* **Concerns:** careful memory ordering, NUMA locality, cleanup on crash, watchdog to reclaim segments.

## Use case B — Microservices RPC at scale (cloud service)

* **Problem:** many language polyglot services, need strong typing, streaming, low overhead.
* **Solution:** gRPC + Protobuf, mTLS via SPIRE, service mesh for observability and L7 routing. Use client-side load balancing + health checks. Fail fast, deadlines, retries with exponential backoff + jitter.
* **Concerns:** probe/health check design, head-of-line blocking, versioned API rollout, schema registry, backward compatibility.

## Use case C — Local system daemon (container runtime, e.g., containerd)

* **Problem:** secure local control plane accessible to root/UID owners.
* **Solution:** UNIX domain socket with strict filesystem permissions and peer-credential checks (SO_PEERCRED); validate every request; use SELinux/AppArmor profiles.
* **Concerns:** fd passing, attacks via compromised client process, define ACLs.

## Use case D — Edge/IoT device control

* **Problem:** intermittent network, constrained device.
* **Solution:** design RPC to support offline buffering, sequence numbers, idempotent commands, delta updates, compact serialization (CBOR/Protobuf). Use DTLS or mTLS with pre-provisioned certs and device attestation.
* **Concerns:** certificate rotation, secure boot, limited CPU for crypto (use hardware crypto modules).

## Use case E — Browser renderer ↔ GPU process

* **Problem:** isolate GPU driver faults; high-frequency command passing.
* **Solution:** broker process with UNIX domain sockets for small control messages and shared memory for large buffers; capability passing for GPU buffers via SCM_RIGHTS; watchdog process to restart hung GPU service.
* **Concerns:** sandboxing, race conditions, memory leaks causing OOM.

---

# 9) Design checklist for building an RPC/IPC system

1. Define API surface with IDL + semantics (error codes, idempotency) and lifecycle (CRUD, commands).
2. Choose transport: UNIX socket for local, HTTP/2 or QUIC for network.
3. Choose serialization: Protobuf/FlatBuffers for performance, JSON for compatibility.
4. Plan for authentication & authorization (mTLS, tokens).
5. Define timeouts, retry policies, and backoff + jitter.
6. Add observability hooks (tracing spans per RPC, latency histograms).
7. Implement graceful shutdown, health checks, connection draining.
8. Add monitoring and alarms for p50/p99 latency, error rate, saturation.
9. Create compatibility tests and automated contract tests.
10. Provide a migration/versioning path.

---

# 10) Stubs, codegen and deployment workflow

* Use IDL to generate client/server stubs (gRPC: `protoc --go_out=... --go-grpc_out=...`).
* Keep business logic separate from transport glue (separation of concerns).
* Automate schema change validation (CI contract tests — e.g., pact or custom integration tests).
* Build release artifacts per language and publish versioned API packages.
* Continuous deployment: use CI to run contract tests and performance benchmarks before canary.

---

# 11) Testing, fuzzing and benchmarking (practical steps)

## Unit & contract tests

* Unit-test serialization/deserialization, boundary conditions, nil/empty fields.
* Contract tests: run the generated server in CI and call all RPC methods with both valid and invalid payloads to verify behavior.

## Integration tests

* Deploy a test instance with instrumentation; run end-to-end flows under test data.
* Use test harnesses to simulate network failure, high latency, and partial failures.

## Fuzzing for robustness

* **Targets:** deserializers, IDL-generated parsers, server request handlers.
* **Tools:** `libFuzzer`/`AFL`/`honggfuzz` for native code; `go-fuzz` for Go code; `jazzer` for Java.
* **Approach:** feed mutated serialized messages to server endpoints (both direct call and via network stack). Monitor for panics, leaks, unexpected behavior.
* **Automated:** run fuzzers in CI for critical code paths; use sanitizers (ASAN, UBSAN) where supported.

## Load & latency benchmarks

* **Tools:** `wrk`, `vegeta`, `ghz` (for gRPC), `hey`, custom harnesses.
* **Metrics to measure:** throughput (rps), latency distribution (p50/p90/p95/p99/p999), CPU, memory, connection churn, system calls per second.
* **Procedure:**

  * Isolate benchmark environment (no noisy neighbors).
  * Use increasing concurrency to identify saturation point.
  * Profile (`pprof`, `perf`, flame graphs) at saturation and p99 spikes.
  * Measure tail latency under realistic workload mixtures.

Example `wrk` command for HTTP unary endpoint:

```
wrk -t12 -c400 -d30s -H "Authorization: Bearer <token>" http://127.0.0.1:8080/v1/echo
```

Example `ghz` for gRPC:

```
ghz --insecure --proto proto/service.proto \
    --call pkg.Service.Method -n 100000 -c 200 \
    -d '{"field":"value"}' localhost:50051
```

(Adjust for your environment and security.)

---

# 12) Observability best practices

* Emit structured logs with correlation IDs.
* Use distributed tracing (OpenTelemetry) — propagate trace and baggage headers.
* Capture metrics: request counts, success/failure, latency histograms, open connections, queue lengths.
* Track resource-based metrics: file descriptors, shm segments, memory pools.
* Alert on error bursts, slow responses, increasing p99.

---

# 13) Rollout & rollback plan (production)

1. **Canary**: Deploy new RPC/IDL changes to a small % of traffic. Validate metrics (error rate, latency) and run compatibility tests.
2. **Progressive rollout**: Increase traffic to new version once canary passes. Use health checks and traffic steering.
3. **Feature flags & backwards**: If schema changes are non-backward compatible, use adapter layer or flag to enable new behavior only for clients that support it.
4. **Rollback triggers**: Thresholds for error rate, latency, or failed health checks. Implement automatic revert in orchestration (k8s rollback, or route traffic back to stable revision).
5. **Post-mortem**: Capture traces and logs from canary window for RCA.

Rollback checklist:

* Stop sending traffic to canary.
* Re-route DNS/load-balancer to stable revision.
* If DB migrations involved, ensure reversible or have migration rollback procedures.
* Remove schema changes only after old clients drained.

---

# 14) Threat model + mitigations (concise table)

| Threat                  |           Likely vector | Mitigation                                  |
| ----------------------- | ----------------------: | ------------------------------------------- |
| Eavesdropping / MitM    |       Network transport | TLS/mTLS, HSM for keys                      |
| Unauthorized access     | Open sockets, weak auth | ACLs, UNIX socket perms, token scopes       |
| Resource exhaustion     |       High request rate | Rate limiting, quotas, autoscale            |
| Replay                  |       Captured requests | Nonces, timestamps, signed tokens           |
| Deserialization exploit |         Untrusted input | Strict schema, safe parsers, sanitize       |
| Privilege escalation    |           FD/SHM misuse | Capability checks, seccomp, drop privileges |
| Data leak in logs       |         Logging secrets | Redaction, structured logs, access control  |

---

# 15) Implementation patterns & anti-patterns

## Patterns

* **Proxy/Adapter:** use API gateway or sidecar to centralize cross-cutting concerns (auth, rate limit).
* **Circuit breaker:** prevent cascading failures.
* **Bulkhead isolation:** limit resource pools per client/tenant.
* **Backpressure and flow control:** avoid unbounded memory growth.

## Anti-patterns

* **Synchronous blocking at high scale** for long-running ops — causes thread exhaustion.
* **Retry without idempotency** — causes duplicate side effects.
* **Monolithic schemas that change frequently without versioning** — break clients.
* **Exposing admin sockets without auth** — serious security risk.

---

# 16) Practical recipes (short)

## Make local RPC fast & safe for an internal service

* Use UNIX domain sockets + protobuf over length-prefixed frames.
* Authenticate clients using SO_PEERCRED + token validation.
* Use fixed-size pre-allocated ring buffers for hot paths; fall back to socket for control commands.
* Limit shm segments to owner UID and set umask 077.

## Make gRPC service production-ready

* Use Protobuf for IDL; generate code for server/client.
* Enforce deadlines via context cancellation.
* Implement interceptor: auth, metrics, tracing, and panic recovery.
* Configure connection pooling, keepalive, and TLS with cert rotation.
* Add readiness and liveness probes, graceful drain.

---

# 17) References & further reading

(Recommended canonical materials)

* POSIX man pages: `pipe(2)`, `socket(2)`, `shm_open(3)`, `mmap(2)`.
* gRPC documentation and guides (search “gRPC official docs”).
* Protobuf language guide (search “Protocol Buffers developer guide”).
* ZeroMQ guide (patterns and sockets).
* OpenTelemetry for traces and metrics.
* “Designing Data-Intensive Applications” (for distributed system design patterns).
* RFC 7230 (HTTP/1.1), HTTP/2 spec — for transport semantics.

---

# 18) Next 3 concrete steps I recommend you take

1. **Choose pattern:** pick whether IPC (local, low-latency) or RPC (networked, polyglot) matches your workload and list the non-functional requirements (latency p50/p99, throughput, security).
2. **Prototype a minimal flow:** implement a simple unary RPC (e.g., gRPC with a single `Echo` method or UNIX socket + Protobuf locally). Add tracing and a basic interceptor for auth.
3. **Run basic tests:** unit + contract tests, a small load test (wrk/ghz) to measure baseline p50/p99 and run a deserialization fuzzer against your endpoint.

---

If you want, I can immediately:

* produce a compact **API design template** (IDL example + compatibility rules),
* provide a **small code prototype** (gRPC + Protobuf or UNIX socket + Go/Rust example) with build/test/run commands, or
* generate **a checklist and CI workflow** that runs contract tests, fuzzing, and benchmarks.

Tell me which one you want now and which language/stack you prefer (Go, Rust, C++, Python, TypeScript). I will produce the artifact straight away.


**Short answer:**
If two microservices run on the **same machine**, the best communication method in most production systems is **RPC over UNIX Domain Sockets (UDS)** (e.g., gRPC over UDS). It provides **high performance, strong API contracts, security via filesystem permissions, and simpler service design** compared with raw IPC mechanisms.

Below is the engineering reasoning and alternatives.

---

# 1. Communication options when microservices run on the same system

Even on one machine, you have multiple design choices.

| Method                   | Type      | Latency   | Complexity | Typical Use                        |
| ------------------------ | --------- | --------- | ---------- | ---------------------------------- |
| Shared Memory            | IPC       | Ultra-low | Very high  | High-frequency trading, DB engines |
| Pipes / FIFOs            | IPC       | Low       | Low        | Parent-child processes             |
| UNIX Domain Sockets      | IPC       | Very low  | Medium     | System daemons, container runtimes |
| Loopback TCP (127.0.0.1) | RPC       | Low       | Medium     | Traditional microservices          |
| gRPC over UDS            | RPC + IPC | Very low  | Medium     | Modern microservices               |
| Message Broker           | Async RPC | Higher    | High       | Event-driven systems               |

For **microservices**, the best balance is usually:

**gRPC over UNIX domain sockets**

---

# 2. Why UNIX Domain Socket RPC is usually the best

## 1) Lower latency than TCP

Local sockets bypass parts of the network stack.

Approximate latency comparison:

```
Shared Memory        ~10–100 ns
UNIX Domain Socket   ~1–10 µs
Loopback TCP         ~10–50 µs
Network RPC          ~100+ µs
```

So UDS is **3–5x faster than localhost TCP**.

Reason:

* No IP routing
* No TCP congestion control
* No packet encapsulation

---

## 2) Better security model

UNIX sockets use **filesystem permissions**.

Example:

```
/var/run/payment-service.sock
```

You can control access:

```
chmod 660 payment-service.sock
chown payment:orders payment-service.sock
```

The OS enforces:

* user identity
* group permissions

Additionally Linux provides:

```
SO_PEERCRED
```

Which lets a service identify the client **UID, PID, GID**.

This is widely used by:

* Docker daemon
* containerd
* systemd
* PostgreSQL

---

## 3) Strong API contracts with RPC

Using RPC frameworks gives you:

* **IDL (interface definition language)**
* **type safety**
* **versioning**
* **code generation**

Example with **Protocol Buffers**.

Service definition:

```
service PaymentService {
  rpc Charge(ChargeRequest) returns (ChargeResponse);
}
```

Benefits:

* consistent API
* backward compatibility
* auto-generated clients

---

## 4) Observability and production tooling

RPC frameworks provide built-in:

* retries
* timeouts
* tracing
* metrics
* interceptors
* authentication

IPC primitives like shared memory **do not**.

---

## 5) Easy migration to distributed architecture

Many teams start with services on one machine but later move to multiple nodes.

If you use:

```
gRPC + Protobuf
```

Switching from:

```
UNIX socket
```

to

```
TCP + TLS
```

is trivial.

Example:

```
unix:///var/run/service.sock
```

→ later

```
dns:///payment-service:50051
```

No API changes required.

---

# 3. When other IPC methods are better

## Shared memory

Best when:

* extremely high throughput
* zero-copy data
* large binary blobs

Example:

* database engines
* trading systems
* GPU pipelines

But drawbacks:

* complex synchronization
* memory safety risks
* harder debugging
* difficult upgrades

---

## Pipes

Best for:

* simple producer-consumer
* short-lived processes

Example:

```
grep | sort | uniq
```

Not ideal for microservices.

---

## Loopback TCP

Useful when:

* service already built for network
* container orchestration
* language libraries expect TCP

Downside:

* slower than UDS

---

# 4. Real-world examples

## Docker

Communication:

```
docker CLI → dockerd
```

Uses:

```
/var/run/docker.sock
```

UNIX socket.

---

## Kubernetes container runtime

Communication:

```
kubelet → containerd
```

Uses:

```
/run/containerd/containerd.sock
```

---

## PostgreSQL local connections

Postgres supports:

```
TCP
UNIX socket
```

Local clients usually use:

```
/var/run/postgresql/.s.PGSQL.5432
```

Because it is faster.

---

# 5. Typical architecture

Example with two services.

```
+-------------------+
| Order Service     |
|                   |
| gRPC client       |
+---------+---------+
          |
          | UNIX domain socket
          |
+---------v---------+
| Payment Service   |
|                   |
| gRPC server       |
+-------------------+
```

Socket path:

```
/run/microservices/payment.sock
```

---

# 6. Security considerations

When using local sockets:

### Use filesystem permissions

```
chmod 660 socket
```

### Verify peer credentials

Check:

```
UID
PID
GID
```

### Limit socket location

Use:

```
/run/
```

Not:

```
/tmp
```

---

# 7. Performance tuning

Important parameters:

### connection pooling

Reuse connections.

### message size

Avoid very large payloads.

### serialization

Prefer:

* Protobuf
* FlatBuffers

Instead of JSON.

### batching

Batch requests when possible.

---

# 8. When asynchronous messaging is better

Sometimes synchronous RPC is not ideal.

Use message queues when:

* events
* eventual consistency
* decoupled systems

Examples:

* Kafka
* NATS
* RabbitMQ

Pattern:

```
Order Service → Event Bus → Payment Service
```

---

# 9. Decision guideline

Use this simple rule.

```
Same machine
│
├─ extremely high throughput?
│      └─ Shared memory
│
├─ microservices architecture?
│      └─ gRPC over UNIX socket
│
├─ simple parent-child processes?
│      └─ Pipes
│
└─ distributed systems?
       └─ RPC over TCP (gRPC/HTTP)
```

---

# 10. Practical recommendation (industry)

For **two microservices on the same host**:

**Best option**

```
gRPC + Protobuf + UNIX Domain Socket
```

Reasons:

* low latency
* type-safe APIs
* secure local communication
* easy observability
* future-proof for distributed systems

---

✅ If you want, I can also explain:

* **How Kubernetes services communicate internally (CNI + kube-proxy + RPC)**
* **How service mesh changes RPC communication (mTLS, sidecars)**
* **Deep performance comparison: Shared memory vs UDS vs TCP** (with kernel-level explanation).
