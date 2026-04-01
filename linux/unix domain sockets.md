# UNIX Domain Sockets in Linux — Complete, In-Depth Guide

> **Audience:** Systems programmers building toward world-class mastery.
> **Languages:** C (primary systems reference), Rust (ownership/safety), Go (idiomatic concurrency).
> **Scope:** Internals → APIs → IPC patterns → gRPC integration → production hardening.

---

## Table of Contents

1. [Mental Model First: What Problem Are We Solving?](#1-mental-model-first)
2. [IPC Taxonomy — Where UDS Fits](#2-ipc-taxonomy)
3. [What Is a UNIX Domain Socket?](#3-what-is-a-unix-domain-socket)
4. [Socket Types](#4-socket-types)
5. [Namespace: Filesystem vs Abstract](#5-namespace-filesystem-vs-abstract)
6. [Kernel Internals — What Happens Under the Hood](#6-kernel-internals)
7. [Socket Lifecycle & System Calls](#7-socket-lifecycle--system-calls)
8. [Permissions, Ownership & Security](#8-permissions-ownership--security)
9. [Ancillary Data — cmsg Framework](#9-ancillary-data--cmsg-framework)
10. [Credential Passing (SCM_CREDENTIALS)](#10-credential-passing-scm_credentials)
11. [File Descriptor Passing (SCM_RIGHTS)](#11-file-descriptor-passing-scm_rights)
12. [Performance Characteristics](#12-performance-characteristics)
13. [C Implementation — Production Grade](#13-c-implementation--production-grade)
14. [Rust Implementation — Ownership-Safe](#14-rust-implementation--ownership-safe)
15. [Go Implementation — Idiomatic Concurrency](#15-go-implementation--idiomatic-concurrency)
16. [gRPC over UNIX Domain Sockets](#16-grpc-over-unix-domain-sockets)
17. [Advanced Patterns & Edge Cases](#17-advanced-patterns--edge-cases)
18. [Observability & Debugging](#18-observability--debugging)
19. [Production Hardening Checklist](#19-production-hardening-checklist)

---

## 1. Mental Model First

Before touching any API, build the right mental model. A socket is a **bidirectional communication endpoint** managed by the kernel. Two processes can each hold one end of a "virtual wire" — data written into one end flows out the other.

**Why UNIX Domain Sockets (UDS) instead of TCP loopback (127.0.0.1)?**

TCP loopback goes through the full network stack:
```
Process A → socket syscall → TCP layer → IP layer → loopback device driver
         → IP layer → TCP layer → socket buffer → Process B
```

UDS skips all of that:
```
Process A → socket syscall → kernel copy (or zero-copy) → socket buffer → Process B
```

No IP routing. No TCP sequence numbers. No checksums. No port exhaustion. Just shared kernel memory with a synchronization mechanism.

**Cognitive anchor:** Think of UDS as a **named pipe with superpowers** — it has a filesystem identity, supports multiple clients, and can transfer file descriptors and credentials.

---

## 2. IPC Taxonomy — Where UDS Fits

Inter-Process Communication (IPC) mechanisms on Linux, ordered by complexity and capability:

```
IPC Mechanism        | Bidirectional | Multiple Clients | FD Passing | Network Transparency
---------------------|---------------|------------------|------------|---------------------
Pipe (anonymous)     | No (half)     | No               | No         | No
Named Pipe (FIFO)    | No (half)     | Yes (reads race) | No         | No
UNIX Domain Socket   | Yes           | Yes              | Yes        | No
TCP Socket           | Yes           | Yes              | No         | Yes
Shared Memory (SHM)  | Yes           | Yes              | No         | No
Message Queue (mq)   | Yes (1-way)   | Yes              | No         | No
Signal              | 1-bit msg      | No               | No         | No
```

**Key insight:** UDS is the only IPC mechanism that allows both **bidirectional, multi-client communication** AND **file descriptor passing** — which makes it uniquely powerful for privilege separation architectures.

---

## 3. What Is a UNIX Domain Socket?

A UNIX Domain Socket is defined by:

- **Address Family:** `AF_UNIX` (also written `AF_LOCAL`) — signals the kernel this is a local-only socket.
- **Identity:** Either a **filesystem path** (e.g., `/run/myapp.sock`) or an **abstract name** (a null-byte prefix).
- **Kernel Representation:** A pair of `struct sock` objects linked together, living in kernel space.

### The `sockaddr_un` Structure

Every socket needs an address. For UDS, the address is:

```c
#include <sys/un.h>

struct sockaddr_un {
    sa_family_t sun_family;   /* Always AF_UNIX */
    char        sun_path[108]; /* Path or abstract name */
};
```

**Important:** `sun_path[108]` is only 108 bytes (POSIX minimum). On Linux it's exactly 108. This is a hard limit — paths longer than 107 characters (plus null terminator) will fail with `ENAMETOOLONG`.

**Abstract namespace:** If `sun_path[0] == '\0'`, the remaining bytes form the abstract name. The length is determined not by a null terminator but by the `addrlen` passed to `bind()`.

---

## 4. Socket Types

Three socket types exist for UDS, each with different delivery guarantees:

### 4.1 SOCK_STREAM

- **Analogy:** TCP — a reliable, ordered byte stream.
- **Behavior:** Data arrives in order, no message boundaries (the kernel may coalesce writes).
- **Use when:** You need a continuous data stream, like proxies, database connections, or shell I/O.
- **Connection model:** Requires `listen()` + `accept()` on server, `connect()` on client.

```
Writer: write(fd, "Hello", 5); write(fd, " World", 6);
Reader may see: "Hello World" in one read, or "Hello" then " World", etc.
Message boundaries are NOT preserved.
```

### 4.2 SOCK_DGRAM

- **Analogy:** UDP — connectionless, datagram-oriented.
- **Behavior:** Each `sendto()` produces exactly one `recvfrom()`. Message boundaries ARE preserved.
- **Use when:** You need discrete messages with clear boundaries.
- **Connection model:** No `listen()`/`accept()`. Server binds, client sends. No persistent connection.
- **Caution:** Unlike UDP over a network, UDS datagrams are **reliable** (no packet loss) within a running kernel — but if the receiver's buffer is full, `sendto()` blocks or returns `EAGAIN`.

### 4.3 SOCK_SEQPACKET

- **Analogy:** SCTP on a local machine — ordered, reliable, message-boundary-preserving.
- **Behavior:** Like STREAM (connection-oriented) but like DGRAM (message boundaries preserved).
- **Use when:** You want the reliability of streams with the message framing of datagrams.
- **Rare:** Less common but powerful for structured message protocols.

```
SOCK_STREAM:    Ordered + Reliable + NO boundaries  (byte stream)
SOCK_DGRAM:     NO order guarantee + Reliable* + boundaries  (datagrams)
SOCK_SEQPACKET: Ordered + Reliable + boundaries  (best of both)
```

*Reliable on localhost — sender blocks if receiver buffer full.

---

## 5. Namespace: Filesystem vs Abstract

### 5.1 Filesystem Namespace

The socket file appears in the filesystem:

```c
struct sockaddr_un addr = {0};
addr.sun_family = AF_UNIX;
strncpy(addr.sun_path, "/run/myapp/service.sock", sizeof(addr.sun_path) - 1);
```

**Properties:**
- Visible via `ls -la /run/myapp/`. Shows as `srwxrwxrwx` (`s` = socket).
- **Persists after crash.** If your server crashes, the socket file remains. Next `bind()` fails with `EADDRINUSE`. You must `unlink()` before re-binding.
- Access controlled by filesystem permissions (uid/gid/mode bits).
- Works across filesystem namespaces that share the same mount.

**Lifecycle pattern:**

```
Server starts → unlink(path) [ignore ENOENT] → bind() → listen() → accept() ...
Server exits  → close(fd) → unlink(path)
```

### 5.2 Abstract Namespace

```c
struct sockaddr_un addr = {0};
addr.sun_family = AF_UNIX;
/* sun_path[0] = '\0', rest is the name */
memcpy(addr.sun_path + 1, "myapp_service", 13);
socklen_t addrlen = sizeof(sa_family_t) + 1 + 13; /* Must pass exact length */
```

**Properties:**
- NOT visible in the filesystem. Cannot be found with `ls`.
- **Automatically cleaned up** when all file descriptors referencing it are closed.
- No permission bits — any process in the same **network namespace** can connect.
- Isolated per network namespace (useful in containers).

**Trade-off:**

| Property | Filesystem | Abstract |
|---|---|---|
| Visibility | `ls`, `stat` | Only via `/proc/net/unix` |
| Cleanup on crash | Manual `unlink()` | Automatic |
| Access control | Filesystem ACLs | Network namespace only |
| Cross-namespace | Mount namespace | Network namespace |

---

## 6. Kernel Internals — What Happens Under the Hood

Understanding the kernel internals makes you a better debugger and optimizer.

### 6.1 Kernel Data Structures

When you create a UDS socket, the kernel allocates:

```
struct socket        ← VFS layer (file descriptor table entry points here)
  └── struct sock    ← Protocol-specific socket state
        ├── sk_receive_queue  ← skb list (incoming data)
        ├── sk_write_queue    ← skb list (outgoing data, usually empty for UDS)
        ├── sk_sndbuf         ← Send buffer size limit
        ├── sk_rcvbuf         ← Receive buffer size limit
        └── unix_sock         ← UDS-specific extension
              ├── path        ← Filesystem path (if bound)
              ├── peer        ← Pointer to connected peer's sock
              └── addr        ← Bound address
```

### 6.2 Data Transfer Path

For `SOCK_STREAM`, when Process A calls `write(fd, buf, n)`:

1. Kernel copies `n` bytes from userspace `buf` into an `sk_buff` (socket buffer).
2. The `sk_buff` is enqueued on the **peer's** `sk_receive_queue`.
3. The peer process (B) sleeping in `read()` is woken up via `sk->sk_data_ready` callback.
4. Process B copies data from `sk_buff` into its userspace buffer.
5. `sk_buff` is freed.

**Two copies:** userspace A → kernel → userspace B. This is the fundamental cost.

**Can we do zero-copy?** For large transfers, `sendfile()` works between file descriptors, but for UDS-to-UDS, the kernel still needs the intermediate buffer. `splice()` can reduce copies in a pipeline.

### 6.3 Buffer Sizes

Default socket buffer sizes (check with `sysctl`):

```bash
sysctl net.core.rmem_default  # Default receive buffer: 212992 bytes (~208 KB)
sysctl net.core.wmem_default  # Default send buffer:    212992 bytes (~208 KB)
sysctl net.core.rmem_max      # Max receive buffer: 134217728 bytes (128 MB)
sysctl net.core.wmem_max      # Max send buffer:    134217728 bytes (128 MB)
```

You can increase per-socket:
```c
int rcvbuf = 4 * 1024 * 1024; /* 4 MB */
setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));
/* Kernel doubles the value internally (for overhead), so actual = 8 MB */
```

### 6.4 The Accept Queue

When a client calls `connect()`, the kernel performs the handshake internally and places the new connection on the **accept queue** (also called the backlog queue). The server calls `accept()` to dequeue a connection.

```
Client connect() → kernel handshake → accept_queue → server accept() → new fd
```

If the accept queue overflows (more pending connections than `backlog` argument to `listen()`), new `connect()` calls block or fail with `EAGAIN` depending on O_NONBLOCK.

---

## 7. Socket Lifecycle & System Calls

### 7.1 Server Lifecycle (SOCK_STREAM)

```
socket() → bind() → listen() → accept() loop → recv/send → close()
                                                           → unlink()
```

### 7.2 Client Lifecycle (SOCK_STREAM)

```
socket() → connect() → send/recv → close()
```

### 7.3 System Call Reference

#### `socket(2)` — Create a socket

```c
int fd = socket(AF_UNIX, SOCK_STREAM, 0);
/*               ^         ^            ^
                 domain    type         protocol (0 = default for domain/type) */
```

Returns a file descriptor. On error, returns `-1` and sets `errno`.

Add `SOCK_NONBLOCK | SOCK_CLOEXEC` flags (Linux 2.6.27+) to atomically set these on creation:

```c
int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
```

**Why `SOCK_CLOEXEC` matters:** Without it, if your process forks and execs a child, the child inherits open socket file descriptors — a security and resource leak. `SOCK_CLOEXEC` sets `FD_CLOEXEC` atomically, no TOCTOU race.

#### `bind(2)` — Assign an address to a socket

```c
struct sockaddr_un addr = {0};
addr.sun_family = AF_UNIX;
strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

/* addrlen must be the ACTUAL size of the address, not sizeof(addr) */
socklen_t addrlen = offsetof(struct sockaddr_un, sun_path) + strlen(addr.sun_path) + 1;

if (bind(fd, (struct sockaddr *)&addr, addrlen) == -1) {
    perror("bind");
}
```

**`offsetof` is critical:** `sizeof(struct sockaddr_un)` would be 110 bytes (2 + 108), but you only want to pass the bytes you've actually filled. Some kernels accept `sizeof(addr)`, but the correct form uses `offsetof`.

#### `listen(2)` — Mark socket as passive

```c
#define BACKLOG 128
listen(fd, BACKLOG);
```

`BACKLOG` is the maximum length of the accept queue. Linux caps this at `net.core.somaxconn` (default 4096 on modern kernels). Classic value is 128, but high-throughput servers use 1024+.

#### `accept(2)` / `accept4(2)` — Accept a connection

```c
struct sockaddr_un client_addr = {0};
socklen_t client_len = sizeof(client_addr);

/* accept4 is Linux-specific but lets us set flags atomically */
int client_fd = accept4(server_fd,
                        (struct sockaddr *)&client_addr,
                        &client_len,
                        SOCK_CLOEXEC | SOCK_NONBLOCK);
```

**`accept4`** (Linux 2.6.28) is preferred — it atomically sets `SOCK_CLOEXEC` and `SOCK_NONBLOCK` on the returned fd, avoiding race conditions with fork.

#### `connect(2)` — Connect to a server

```c
if (connect(fd, (struct sockaddr *)&addr, addrlen) == -1) {
    if (errno == EAGAIN || errno == EINPROGRESS) {
        /* Non-blocking: use poll/epoll to wait for writability */
    }
}
```

For blocking sockets, `connect()` returns when the kernel completes the internal handshake. For non-blocking, it returns `-1` with `errno = EINPROGRESS`, and you poll for `POLLOUT`.

#### `send(2)` / `recv(2)` — Transfer data

```c
ssize_t n = send(fd, buf, len, MSG_NOSIGNAL);
/*                              ^ Don't raise SIGPIPE if peer closed */

ssize_t n = recv(fd, buf, sizeof(buf), MSG_WAITALL);
/*                                     ^ Block until all bytes received */
```

**`MSG_NOSIGNAL`:** Without this flag, writing to a socket whose peer has closed raises `SIGPIPE` (default action: terminate the process). Always use `MSG_NOSIGNAL` on UDS, or globally set `signal(SIGPIPE, SIG_IGN)`.

#### `sendmsg(2)` / `recvmsg(2)` — Advanced: ancillary data

Used for fd-passing, credential-passing. Covered in section 9.

#### `shutdown(2)` — Half-close

```c
shutdown(fd, SHUT_WR);   /* Stop sending, peer gets EOF */
shutdown(fd, SHUT_RD);   /* Stop receiving */
shutdown(fd, SHUT_RDWR); /* Both */
```

`shutdown()` signals intent to the peer. `close()` decrements the reference count but doesn't signal until the last reference is dropped (important if you've forked).

#### `close(2)` — Release file descriptor

```c
close(fd);
```

When the last fd referring to the socket is closed, the kernel tears down the connection.

#### `unlink(2)` — Remove the socket file

```c
unlink("/run/myapp/service.sock");
```

Only for filesystem-namespace sockets. Abstract sockets are auto-cleaned.

---

## 8. Permissions, Ownership & Security

### 8.1 Socket File Permissions

When `bind()` creates a socket file, it inherits the process `umask`:

```bash
$ umask 0022
$ # Socket created with mode 0666 & ~0022 = 0644
$ ls -la /run/myapp.sock
srw-r--r-- 1 root root 0 Apr  1 10:00 /run/myapp.sock
```

To set specific permissions:

```c
/* Set umask before bind() */
mode_t old_umask = umask(0117); /* Only owner can rw, group can r */
bind(fd, ...);
umask(old_umask); /* Restore */

/* Or chmod after bind */
chmod("/run/myapp.sock", 0660);
```

### 8.2 Connection Authentication

The kernel can attach **peer credentials** to a connection. When a client connects, the server can retrieve the client's `uid`, `gid`, and `pid`:

```c
struct ucred cred;
socklen_t cred_len = sizeof(cred);
getsockopt(client_fd, SOL_SOCKET, SO_PEERCRED, &cred, &cred_len);
/* cred.uid, cred.gid, cred.pid are now available */
```

`SO_PEERCRED` is automatically filled by the kernel at `connect()` time — it **cannot be forged** by userspace (unlike SCM_CREDENTIALS which can lie about pid, but not uid/gid for unprivileged processes).

### 8.3 Security Model Summary

```
Layer 1: Filesystem permissions on the socket path  ← coarse-grained
Layer 2: SO_PEERCRED / SCM_CREDENTIALS              ← fine-grained, kernel-verified
Layer 3: Application-level authentication            ← tokens, capabilities
```

---

## 9. Ancillary Data — cmsg Framework

**Ancillary data** (also called control messages) is extra metadata that accompanies a regular message. This is how the kernel allows you to pass **file descriptors** and **credentials** alongside data.

The mechanism uses `sendmsg()` / `recvmsg()` with `struct msghdr`:

```c
struct msghdr {
    void         *msg_name;       /* Optional address (for DGRAM) */
    socklen_t     msg_namelen;    /* Size of address */
    struct iovec *msg_iov;        /* Scatter-gather array of data buffers */
    size_t        msg_iovlen;     /* Number of elements in msg_iov */
    void         *msg_control;    /* Ancillary data buffer */
    size_t        msg_controllen; /* Length of ancillary data buffer */
    int           msg_flags;      /* Flags (set by recvmsg) */
};
```

**`struct iovec`** — scatter-gather I/O:
```c
struct iovec {
    void  *iov_base; /* Pointer to data buffer */
    size_t iov_len;  /* Length of buffer */
};
```

The ancillary data is structured as a sequence of `struct cmsghdr` headers, each followed by data:

```c
struct cmsghdr {
    size_t cmsg_len;   /* Total length including header + data */
    int    cmsg_level; /* Originating protocol (SOL_SOCKET for UDS) */
    int    cmsg_type;  /* Protocol-specific type (SCM_RIGHTS, SCM_CREDENTIALS) */
    /* Data follows, aligned to CMSG_ALIGN boundary */
};
```

**Navigation macros (always use these, never do pointer arithmetic manually):**

```c
CMSG_FIRSTHDR(msghdr)      /* Pointer to first cmsghdr */
CMSG_NXTHDR(msghdr, cmsg) /* Pointer to next cmsghdr */
CMSG_DATA(cmsg)            /* Pointer to data after cmsghdr */
CMSG_LEN(data_len)         /* Total cmsghdr size for data_len bytes of data */
CMSG_SPACE(data_len)       /* Space needed in buffer (includes alignment padding) */
```

---

## 10. Credential Passing (SCM_CREDENTIALS)

Allows a process to send its credentials (uid, gid, pid) with a message.

### 10.1 Sender Side

```c
/* Enable credential sending (server must also enable SO_PASSCRED) */
int enable = 1;
setsockopt(fd, SOL_SOCKET, SO_PASSCRED, &enable, sizeof(enable));

struct ucred creds = {
    .pid = getpid(),
    .uid = getuid(),
    .gid = getgid(),
};

char cmsg_buf[CMSG_SPACE(sizeof(struct ucred))];
struct iovec iov = { .iov_base = "auth", .iov_len = 4 };
struct msghdr msg = {
    .msg_iov        = &iov,
    .msg_iovlen     = 1,
    .msg_control    = cmsg_buf,
    .msg_controllen = sizeof(cmsg_buf),
};

struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_CREDENTIALS;
cmsg->cmsg_len   = CMSG_LEN(sizeof(struct ucred));
memcpy(CMSG_DATA(cmsg), &creds, sizeof(struct ucred));

sendmsg(fd, &msg, 0);
```

**Kernel enforcement:** An unprivileged process can only send its own real uid/gid. A privileged process (CAP_SETUID) can send arbitrary credentials.

### 10.2 Receiver Side

```c
int enable = 1;
setsockopt(server_fd, SOL_SOCKET, SO_PASSCRED, &enable, sizeof(enable));

char data[64];
char cmsg_buf[CMSG_SPACE(sizeof(struct ucred))];
struct iovec iov = { .iov_base = data, .iov_len = sizeof(data) };
struct msghdr msg = {
    .msg_iov        = &iov,
    .msg_iovlen     = 1,
    .msg_control    = cmsg_buf,
    .msg_controllen = sizeof(cmsg_buf),
};

recvmsg(fd, &msg, 0);

for (struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
     cmsg != NULL;
     cmsg = CMSG_NXTHDR(&msg, cmsg)) {
    if (cmsg->cmsg_level == SOL_SOCKET &&
        cmsg->cmsg_type  == SCM_CREDENTIALS) {
        struct ucred cred;
        memcpy(&cred, CMSG_DATA(cmsg), sizeof(struct ucred));
        printf("peer pid=%d uid=%d gid=%d\n", cred.pid, cred.uid, cred.gid);
    }
}
```

---

## 11. File Descriptor Passing (SCM_RIGHTS)

This is **one of the most powerful features of UDS**. A process can pass an open file descriptor to another process — the receiving process gets a new fd referring to the same kernel file object (same open file description, including offset and flags).

**Use cases:**
- **Privilege separation:** A privileged process opens a sensitive file, passes the fd to an unprivileged worker.
- **Connection hand-off:** A load balancer accepts a connection, passes the fd to a worker process.
- **Zero-copy data sharing:** Pass a `memfd_create()` fd to avoid copying large data.

### 11.1 Sender Side

```c
/* fd_to_send is the file descriptor we want to give to the other process */
int fd_to_send = open("/etc/sensitive_config", O_RDONLY);

char cmsg_buf[CMSG_SPACE(sizeof(int))]; /* Space for one fd */
char data[1] = {'x'}; /* Must send at least 1 byte of data with fd */
struct iovec iov = { .iov_base = data, .iov_len = 1 };
struct msghdr msg = {
    .msg_iov        = &iov,
    .msg_iovlen     = 1,
    .msg_control    = cmsg_buf,
    .msg_controllen = sizeof(cmsg_buf),
};

struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_RIGHTS;
cmsg->cmsg_len   = CMSG_LEN(sizeof(int));
memcpy(CMSG_DATA(cmsg), &fd_to_send, sizeof(int));

sendmsg(fd, &msg, 0);
close(fd_to_send); /* Sender can close its copy now */
```

**Important:** You must send at least 1 byte of regular data alongside the ancillary data — otherwise `sendmsg()` returns `EINVAL`.

### 11.2 Receiver Side

```c
char data[1];
char cmsg_buf[CMSG_SPACE(sizeof(int))];
struct iovec iov = { .iov_base = data, .iov_len = 1 };
struct msghdr msg = {
    .msg_iov        = &iov,
    .msg_iovlen     = 1,
    .msg_control    = cmsg_buf,
    .msg_controllen = sizeof(cmsg_buf),
};

recvmsg(fd, &msg, 0);

int received_fd = -1;
for (struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
     cmsg != NULL;
     cmsg = CMSG_NXTHDR(&msg, cmsg)) {
    if (cmsg->cmsg_level == SOL_SOCKET &&
        cmsg->cmsg_type  == SCM_RIGHTS) {
        memcpy(&received_fd, CMSG_DATA(cmsg), sizeof(int));
        /* received_fd is now a valid fd in THIS process */
    }
}
```

**Kernel mechanics:** When the sender calls `sendmsg()` with SCM_RIGHTS, the kernel increments the reference count of the underlying file object. When the receiver calls `recvmsg()`, the kernel installs a new fd in the receiver's fd table pointing to the same file object. Even if the sender closes its fd, the file remains open because the reference count is > 0.

**FD leak risk:** If the receiver never calls `recvmsg()` and the kernel discards the message (buffer overflow), the kernel properly decrements the file reference count. But if you receive a message and discard the fd without closing it, you have a file descriptor leak.

---

## 12. Performance Characteristics

### 12.1 Latency Benchmark (approximate, modern hardware)

```
Mechanism           | Round-trip latency
--------------------|-------------------
UDS (SOCK_STREAM)   | ~3–6 µs
TCP loopback        | ~20–50 µs
Named Pipe (FIFO)   | ~2–4 µs
Shared Memory       | ~0.5–2 µs (with mutex)
```

UDS is ~5–10x faster than TCP loopback because it skips:
- IP header processing
- TCP segmentation/reassembly  
- Checksum computation
- Routing table lookups
- Network namespace traversal

### 12.2 Throughput

For large transfers, UDS throughput can reach **50–100 GB/s** on modern systems (limited by memory bandwidth, not protocol overhead). TCP loopback peaks at ~20–40 GB/s.

### 12.3 Cache Behavior

**L1/L2 cache effects:** Small messages (< 4 KB) fit in L1/L2 cache. The kernel copy path is extremely efficient for these sizes. Throughput drops at larger sizes when pressure exceeds cache capacity.

**Buffer alignment:** The kernel's `sk_buff` structure aligns data to 16-byte boundaries. If your data is also aligned, SIMD copy routines (memcpy) operate at maximum efficiency.

**Huge pages for socket buffers:** On systems processing millions of messages, pinning socket buffer memory to huge pages (2 MB THP) reduces TLB misses:
```bash
echo always > /sys/kernel/mm/transparent_hugepage/enabled
```

### 12.4 Non-Blocking I/O and epoll

For high-concurrency servers, use epoll with non-blocking sockets:

```
epoll_create1() → epoll_ctl(EPOLL_CTL_ADD) → epoll_wait() loop
```

UDS sockets work identically to TCP sockets with epoll. The kernel wakes up the epoll fd when data arrives.

**Edge-triggered (EPOLLET) vs Level-triggered (EPOLLIN):**

- **Level-triggered (default):** epoll notifies you as long as data is available. Easier to use, but may deliver redundant notifications.
- **Edge-triggered:** epoll notifies only when the state changes (new data arrives). More efficient but you **must** read until EAGAIN or you'll miss data.

---

## 13. C Implementation — Production Grade

### 13.1 Common Utilities Header

```c
/* uds_common.h */
#ifndef UDS_COMMON_H
#define UDS_COMMON_H

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <fcntl.h>

/* Named constants — no magic numbers */
#define UDS_SOCKET_PATH     "/tmp/production_service.sock"
#define UDS_BACKLOG         128
#define UDS_MAX_MSG_SIZE    (4096)
#define UDS_MAX_CLIENTS     (64)
#define UDS_RECV_TIMEOUT_S  (30)

/* Result type for explicit error handling */
typedef enum {
    UDS_OK    =  0,
    UDS_ERROR = -1,
} uds_result_t;

/* Compute actual addrlen for a filesystem-path socket */
static inline socklen_t uds_addrlen(const struct sockaddr_un *addr) {
    return (socklen_t)(offsetof(struct sockaddr_un, sun_path)
                       + strlen(addr->sun_path) + 1);
}

/* Set a file descriptor to non-blocking mode */
static inline uds_result_t fd_set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return UDS_ERROR;
    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) return UDS_ERROR;
    return UDS_OK;
}

/* Reliably read exactly n bytes (handles partial reads) */
static inline ssize_t read_exact(int fd, void *buf, size_t n) {
    size_t total = 0;
    char  *ptr   = (char *)buf;
    while (total < n) {
        ssize_t nread = recv(fd, ptr + total, n - total, 0);
        if (nread == 0)  return (ssize_t)total; /* EOF */
        if (nread == -1) {
            if (errno == EINTR) continue; /* Interrupted by signal, retry */
            return -1;
        }
        total += (size_t)nread;
    }
    return (ssize_t)total;
}

/* Reliably write exactly n bytes (handles partial writes) */
static inline ssize_t write_exact(int fd, const void *buf, size_t n) {
    size_t  total = 0;
    const char *ptr = (const char *)buf;
    while (total < n) {
        ssize_t nwritten = send(fd, ptr + total, n - total, MSG_NOSIGNAL);
        if (nwritten == -1) {
            if (errno == EINTR) continue;
            return -1;
        }
        total += (size_t)nwritten;
    }
    return (ssize_t)total;
}

#endif /* UDS_COMMON_H */
```

### 13.2 Server — Epoll-Based, Non-Blocking

```c
/* uds_server.c
 * Production-grade UDS server using epoll edge-triggered I/O.
 * Handles multiple clients without threads.
 *
 * Build: gcc -Wall -Wextra -O2 -o uds_server uds_server.c
 */

#include "uds_common.h"
#include <sys/epoll.h>
#include <sys/stat.h>

/* Protocol: 4-byte length prefix (network byte order) + payload */
#define PROTO_HDR_SIZE  4
#define MAX_EVENTS      64

/* Per-client state */
typedef struct {
    int     fd;
    char    recv_buf[UDS_MAX_MSG_SIZE];
    size_t  recv_pos;  /* How many bytes received so far */
    uint8_t state;     /* 0 = reading header, 1 = reading body */
    uint32_t expected; /* Body length from header */
} client_state_t;

static client_state_t clients[UDS_MAX_CLIENTS];
static volatile sig_atomic_t g_running = 1;

static void signal_handler(int sig) {
    (void)sig;
    g_running = 0;
}

/* Create and configure the listening socket */
static int create_server_socket(const char *path) {
    /* Remove stale socket file (crash recovery) */
    if (unlink(path) == -1 && errno != ENOENT) {
        perror("unlink");
        return -1;
    }

    int sfd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (sfd == -1) { perror("socket"); return -1; }

    /* Enable SO_REUSEADDR equivalent for UDS: allow quick rebind */
    int optval = 1;
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    if (strlen(path) >= sizeof(addr.sun_path)) {
        fprintf(stderr, "Socket path too long (max %zu chars)\n",
                sizeof(addr.sun_path) - 1);
        close(sfd);
        return -1;
    }
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    /* Restrict access: only owner can connect */
    mode_t old_umask = umask(0177);
    int ret = bind(sfd, (struct sockaddr *)&addr, uds_addrlen(&addr));
    umask(old_umask);

    if (ret == -1) { perror("bind"); close(sfd); return -1; }
    if (listen(sfd, UDS_BACKLOG) == -1) { perror("listen"); close(sfd); return -1; }

    return sfd;
}

static void client_init(client_state_t *c, int fd) {
    memset(c, 0, sizeof(*c));
    c->fd    = fd;
    c->state = 0; /* Reading header */
}

static void client_cleanup(client_state_t *c, int epfd) {
    epoll_ctl(epfd, EPOLL_CTL_DEL, c->fd, NULL);
    close(c->fd);
    c->fd = -1;
}

/* Find a free client slot */
static client_state_t *client_alloc(void) {
    for (int i = 0; i < UDS_MAX_CLIENTS; i++) {
        if (clients[i].fd == -1) return &clients[i];
    }
    return NULL;
}

/* Process data available on a client fd */
static void handle_client(client_state_t *c, int epfd) {
    /* Edge-triggered: must read until EAGAIN */
    for (;;) {
        ssize_t n;

        if (c->state == 0) {
            /* Reading 4-byte length header */
            size_t remaining = PROTO_HDR_SIZE - c->recv_pos;
            n = recv(c->fd, c->recv_buf + c->recv_pos, remaining, 0);
        } else {
            /* Reading body */
            size_t remaining = c->expected - (c->recv_pos - PROTO_HDR_SIZE);
            n = recv(c->fd, c->recv_buf + c->recv_pos, remaining, 0);
        }

        if (n == 0) {
            /* EOF: client closed connection */
            printf("Client fd=%d disconnected\n", c->fd);
            client_cleanup(c, epfd);
            return;
        }
        if (n == -1) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) return; /* Done for now */
            if (errno == EINTR) continue;
            perror("recv");
            client_cleanup(c, epfd);
            return;
        }

        c->recv_pos += (size_t)n;

        if (c->state == 0 && c->recv_pos == PROTO_HDR_SIZE) {
            /* Parse length from big-endian header */
            uint32_t body_len;
            memcpy(&body_len, c->recv_buf, sizeof(uint32_t));
            /* ntohl: network (big-endian) to host byte order */
            c->expected = __builtin_bswap32(body_len);

            if (c->expected == 0 || c->expected > UDS_MAX_MSG_SIZE - PROTO_HDR_SIZE) {
                fprintf(stderr, "Invalid message length %u\n", c->expected);
                client_cleanup(c, epfd);
                return;
            }
            c->state = 1; /* Now reading body */
        }

        if (c->state == 1 &&
            c->recv_pos == PROTO_HDR_SIZE + c->expected) {
            /* Complete message received */
            char *payload = c->recv_buf + PROTO_HDR_SIZE;
            payload[c->expected] = '\0';
            printf("Received from fd=%d: [%u bytes] %s\n",
                   c->fd, c->expected, payload);

            /* Echo back */
            if (write_exact(c->fd, c->recv_buf, PROTO_HDR_SIZE + c->expected) == -1) {
                perror("write_exact");
                client_cleanup(c, epfd);
                return;
            }

            /* Reset for next message */
            c->recv_pos = 0;
            c->state    = 0;
        }
    }
}

int main(void) {
    /* Initialize client table */
    for (int i = 0; i < UDS_MAX_CLIENTS; i++) clients[i].fd = -1;

    /* Set up signal handling for clean shutdown */
    struct sigaction sa = { .sa_handler = signal_handler };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    signal(SIGPIPE, SIG_IGN); /* Ignore broken pipe */

    int server_fd = create_server_socket(UDS_SOCKET_PATH);
    if (server_fd == -1) return EXIT_FAILURE;

    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd == -1) { perror("epoll_create1"); return EXIT_FAILURE; }

    /* Add server fd to epoll */
    struct epoll_event ev = {
        .events  = EPOLLIN | EPOLLET,
        .data.fd = server_fd,
    };
    epoll_ctl(epfd, EPOLL_CTL_ADD, server_fd, &ev);

    struct epoll_event events[MAX_EVENTS];
    printf("Server listening on %s\n", UDS_SOCKET_PATH);

    while (g_running) {
        int n = epoll_wait(epfd, events, MAX_EVENTS, 1000 /* ms timeout */);
        if (n == -1) {
            if (errno == EINTR) continue;
            perror("epoll_wait");
            break;
        }

        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == server_fd) {
                /* Accept all pending connections (edge-triggered) */
                for (;;) {
                    int cfd = accept4(server_fd, NULL, NULL,
                                      SOCK_NONBLOCK | SOCK_CLOEXEC);
                    if (cfd == -1) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        if (errno == EINTR) continue;
                        perror("accept4");
                        break;
                    }

                    client_state_t *c = client_alloc();
                    if (!c) {
                        fprintf(stderr, "Too many clients, rejecting fd=%d\n", cfd);
                        close(cfd);
                        continue;
                    }

                    client_init(c, cfd);

                    struct epoll_event cev = {
                        .events  = EPOLLIN | EPOLLET | EPOLLHUP | EPOLLERR,
                        .data.ptr = c,
                    };
                    epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &cev);
                    printf("New client fd=%d\n", cfd);
                }
            } else {
                client_state_t *c = events[i].data.ptr;
                if (events[i].events & (EPOLLHUP | EPOLLERR)) {
                    client_cleanup(c, epfd);
                } else {
                    handle_client(c, epfd);
                }
            }
        }
    }

    /* Cleanup */
    close(epfd);
    close(server_fd);
    unlink(UDS_SOCKET_PATH);
    printf("Server shut down cleanly\n");
    return EXIT_SUCCESS;
}
```

### 13.3 Client

```c
/* uds_client.c
 * Build: gcc -Wall -Wextra -O2 -o uds_client uds_client.c
 */

#include "uds_common.h"
#include <stdint.h>

static int connect_to_server(const char *path) {
    int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd == -1) { perror("socket"); return -1; }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr *)&addr, uds_addrlen(&addr)) == -1) {
        perror("connect");
        close(fd);
        return -1;
    }

    return fd;
}

static int send_message(int fd, const char *msg) {
    size_t   msg_len = strlen(msg);
    uint32_t net_len = __builtin_bswap32((uint32_t)msg_len); /* htonl */

    char hdr[PROTO_HDR_SIZE];
    memcpy(hdr, &net_len, sizeof(net_len));

    if (write_exact(fd, hdr, PROTO_HDR_SIZE) == -1) return -1;
    if (write_exact(fd, msg, msg_len)         == -1) return -1;
    return 0;
}

static int recv_message(int fd, char *buf, size_t bufsz) {
    char hdr[PROTO_HDR_SIZE];
    if (read_exact(fd, hdr, PROTO_HDR_SIZE) != PROTO_HDR_SIZE) return -1;

    uint32_t net_len;
    memcpy(&net_len, hdr, sizeof(net_len));
    uint32_t body_len = __builtin_bswap32(net_len);

    if (body_len == 0 || body_len >= bufsz) return -1;
    if (read_exact(fd, buf, body_len) != (ssize_t)body_len) return -1;
    buf[body_len] = '\0';
    return (int)body_len;
}

int main(void) {
    int fd = connect_to_server(UDS_SOCKET_PATH);
    if (fd == -1) return EXIT_FAILURE;

    const char *messages[] = {
        "Hello, UNIX Domain Socket!",
        "Production-grade IPC",
        "Fast and reliable",
    };
    size_t nmsg = sizeof(messages) / sizeof(messages[0]);

    char recv_buf[UDS_MAX_MSG_SIZE];

    for (size_t i = 0; i < nmsg; i++) {
        if (send_message(fd, messages[i]) == -1) {
            fprintf(stderr, "Send failed: %s\n", strerror(errno));
            break;
        }

        int n = recv_message(fd, recv_buf, sizeof(recv_buf));
        if (n == -1) {
            fprintf(stderr, "Recv failed: %s\n", strerror(errno));
            break;
        }

        printf("Echo [%d bytes]: %s\n", n, recv_buf);
    }

    close(fd);
    return EXIT_SUCCESS;
}
```

---

## 14. Rust Implementation — Ownership-Safe

Rust's `std::os::unix::net` module provides type-safe wrappers. For production, we use `tokio` for async I/O.

### 14.1 Cargo.toml

```toml
[package]
name = "uds-rust"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
bytes = "1"
thiserror = "1"
tracing = "0.1"
tracing-subscriber = "0.3"

[[bin]]
name = "server"
path = "src/server.rs"

[[bin]]
name = "client"
path = "src/client.rs"
```

### 14.2 Protocol Module

```rust
// src/proto.rs
//! Length-prefixed framing protocol: 4-byte BE length + payload

use bytes::{Buf, BufMut, Bytes, BytesMut};
use std::io;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

pub const MAX_MESSAGE_SIZE: u32 = 4 * 1024 * 1024; // 4 MB hard limit

/// Encode a message: 4-byte big-endian length prefix + payload
pub fn encode(payload: &[u8]) -> Bytes {
    let len = payload.len() as u32;
    let mut buf = BytesMut::with_capacity(4 + payload.len());
    buf.put_u32(len);    // Big-endian by default in bytes crate
    buf.put(payload);
    buf.freeze()
}

/// Read one framed message from an async reader
///
/// # Errors
/// Returns `io::Error` on read failure or if the message exceeds `MAX_MESSAGE_SIZE`
pub async fn read_message<R: AsyncReadExt + Unpin>(reader: &mut R) -> io::Result<Bytes> {
    // Read 4-byte header
    let body_len = reader.read_u32().await?; // Reads big-endian u32

    if body_len > MAX_MESSAGE_SIZE {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            format!("Message too large: {} bytes (max {})", body_len, MAX_MESSAGE_SIZE),
        ));
    }

    // Read body
    let mut buf = vec![0u8; body_len as usize];
    reader.read_exact(&mut buf).await?;
    Ok(Bytes::from(buf))
}

/// Write one framed message to an async writer
pub async fn write_message<W: AsyncWriteExt + Unpin>(
    writer: &mut W,
    payload: &[u8],
) -> io::Result<()> {
    let framed = encode(payload);
    writer.write_all(&framed).await?;
    writer.flush().await
}
```

### 14.3 Server

```rust
// src/server.rs
//! Async UNIX Domain Socket server using Tokio.
//! Each client is handled in its own spawned task.

mod proto;

use std::path::Path;
use tokio::net::UnixListener;
use tokio::signal;
use tracing::{error, info, warn};

const SOCKET_PATH: &str = "/tmp/rust_production.sock";
const MAX_CONCURRENT_CLIENTS: usize = 1024;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .with_target(false)
        .with_thread_ids(true)
        .init();

    // Remove stale socket (crash recovery) — ignore ENOENT
    if Path::new(SOCKET_PATH).exists() {
        std::fs::remove_file(SOCKET_PATH)?;
    }

    let listener = UnixListener::bind(SOCKET_PATH)?;
    info!("Server listening on {}", SOCKET_PATH);

    // Semaphore to cap concurrent client tasks
    let semaphore = std::sync::Arc::new(tokio::sync::Semaphore::new(MAX_CONCURRENT_CLIENTS));

    loop {
        tokio::select! {
            accept_result = listener.accept() => {
                match accept_result {
                    Ok((stream, _addr)) => {
                        let permit = match semaphore.clone().try_acquire_owned() {
                            Ok(p) => p,
                            Err(_) => {
                                warn!("Too many clients, dropping connection");
                                continue;
                            }
                        };

                        tokio::spawn(async move {
                            let _permit = permit; // Held for task lifetime
                            if let Err(e) = handle_client(stream).await {
                                // Expected: client disconnected mid-message
                                if e.kind() != std::io::ErrorKind::UnexpectedEof {
                                    error!("Client error: {}", e);
                                }
                            }
                        });
                    }
                    Err(e) => {
                        error!("Accept error: {}", e);
                    }
                }
            }

            // Graceful shutdown on Ctrl+C or SIGTERM
            _ = signal::ctrl_c() => {
                info!("Shutdown signal received");
                break;
            }
        }
    }

    // Cleanup socket file
    let _ = std::fs::remove_file(SOCKET_PATH);
    info!("Server shut down cleanly");
    Ok(())
}

async fn handle_client(mut stream: tokio::net::UnixStream) -> std::io::Result<()> {
    // Get peer credentials (uid/gid/pid)
    let creds = stream.peer_cred()?;
    info!(
        "New client: pid={}, uid={}, gid={}",
        creds.pid().unwrap_or(0),
        creds.uid(),
        creds.gid()
    );

    // Split into read + write halves to allow independent borrow
    let (mut reader, mut writer) = stream.split();

    loop {
        match proto::read_message(&mut reader).await {
            Ok(msg) => {
                let text = String::from_utf8_lossy(&msg);
                info!("Received ({} bytes): {}", msg.len(), text);

                // Echo back
                proto::write_message(&mut writer, &msg).await?;
            }
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => {
                info!("Client disconnected");
                return Ok(());
            }
            Err(e) => return Err(e),
        }
    }
}
```

### 14.4 Client

```rust
// src/client.rs
mod proto;

use tokio::net::UnixStream;
use tracing::info;

const SOCKET_PATH: &str = "/tmp/rust_production.sock";

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt().with_target(false).init();

    let mut stream = UnixStream::connect(SOCKET_PATH).await?;
    info!("Connected to {}", SOCKET_PATH);

    let (mut reader, mut writer) = stream.split();

    let messages = [
        "Hello from Rust!",
        "Ownership-safe IPC",
        "Zero-cost abstractions",
    ];

    for msg in &messages {
        proto::write_message(&mut writer, msg.as_bytes()).await?;
        info!("Sent: {}", msg);

        let response = proto::read_message(&mut reader).await?;
        info!("Echo: {}", String::from_utf8_lossy(&response));
    }

    Ok(())
}
```

### 14.5 File Descriptor Passing in Rust

```rust
// fd_pass.rs — Demonstrate SCM_RIGHTS in Rust using std::os::unix
use std::io::{self, IoSlice, IoSliceMut};
use std::os::unix::io::{AsRawFd, FromRawFd, OwnedFd, RawFd};
use std::os::unix::net::UnixStream;

/// Send a file descriptor over a UnixStream
pub fn send_fd(sock: &UnixStream, fd_to_send: RawFd) -> io::Result<()> {
    use std::mem;

    // We must send at least 1 byte of data
    let data = [0u8; 1];
    let iov = [IoSlice::new(&data)];

    // Ancillary data buffer: cmsghdr + one int
    let cmsg_space = unsafe { libc::CMSG_SPACE(mem::size_of::<RawFd>() as u32) as usize };
    let mut cmsg_buf = vec![0u8; cmsg_space];

    let mut msg: libc::msghdr = unsafe { mem::zeroed() };
    msg.msg_iov    = iov.as_ptr() as *mut _;
    msg.msg_iovlen = iov.len();
    msg.msg_control    = cmsg_buf.as_mut_ptr() as *mut _;
    msg.msg_controllen = cmsg_buf.len();

    unsafe {
        let cmsg = libc::CMSG_FIRSTHDR(&msg);
        (*cmsg).cmsg_level = libc::SOL_SOCKET;
        (*cmsg).cmsg_type  = libc::SCM_RIGHTS;
        (*cmsg).cmsg_len   = libc::CMSG_LEN(mem::size_of::<RawFd>() as u32) as _;
        std::ptr::write(libc::CMSG_DATA(cmsg) as *mut RawFd, fd_to_send);
    }

    let ret = unsafe { libc::sendmsg(sock.as_raw_fd(), &msg, 0) };
    if ret == -1 {
        return Err(io::Error::last_os_error());
    }
    Ok(())
}

/// Receive a file descriptor from a UnixStream
pub fn recv_fd(sock: &UnixStream) -> io::Result<OwnedFd> {
    use std::mem;

    let mut data = [0u8; 1];
    let mut iov  = [IoSliceMut::new(&mut data)];

    let cmsg_space = unsafe { libc::CMSG_SPACE(mem::size_of::<RawFd>() as u32) as usize };
    let mut cmsg_buf = vec![0u8; cmsg_space];

    let mut msg: libc::msghdr = unsafe { mem::zeroed() };
    msg.msg_iov        = iov.as_mut_ptr() as *mut _;
    msg.msg_iovlen     = iov.len();
    msg.msg_control    = cmsg_buf.as_mut_ptr() as *mut _;
    msg.msg_controllen = cmsg_buf.len();

    let ret = unsafe { libc::recvmsg(sock.as_raw_fd(), &mut msg, 0) };
    if ret == -1 {
        return Err(io::Error::last_os_error());
    }

    let cmsg = unsafe { libc::CMSG_FIRSTHDR(&msg) };
    if cmsg.is_null() {
        return Err(io::Error::new(io::ErrorKind::InvalidData, "No ancillary data"));
    }

    unsafe {
        if (*cmsg).cmsg_level == libc::SOL_SOCKET && (*cmsg).cmsg_type == libc::SCM_RIGHTS {
            let mut fd: RawFd = -1;
            std::ptr::copy_nonoverlapping(
                libc::CMSG_DATA(cmsg) as *const u8,
                &mut fd as *mut RawFd as *mut u8,
                mem::size_of::<RawFd>(),
            );
            Ok(OwnedFd::from_raw_fd(fd)) // OwnedFd closes on drop
        } else {
            Err(io::Error::new(io::ErrorKind::InvalidData, "Expected SCM_RIGHTS"))
        }
    }
}
```

**Ownership insight:** `OwnedFd` in Rust wraps a raw file descriptor and **closes it on drop**. This prevents fd leaks — one of the most common UDS fd-passing bugs in C code.

---

## 15. Go Implementation — Idiomatic Concurrency

Go's `net` package provides first-class UDS support with `"unix"` network type.

### 15.1 Server

```go
// server.go
// Production-grade UDS server in Go.
// Uses goroutines per connection — Go's scheduler handles the concurrency.
package main

import (
    "bufio"
    "encoding/binary"
    "errors"
    "fmt"
    "io"
    "log/slog"
    "net"
    "os"
    "os/signal"
    "sync"
    "syscall"
)

const (
    SocketPath     = "/tmp/go_production.sock"
    MaxMessageSize = 4 * 1024 * 1024 // 4 MB
    MaxClients     = 1024
)

// Server manages the UDS server lifecycle.
type Server struct {
    listener net.Listener
    wg       sync.WaitGroup
    sem      chan struct{} // Semaphore for max clients
    log      *slog.Logger
}

// NewServer creates a new UDS server bound to path.
func NewServer(path string) (*Server, error) {
    // Remove stale socket
    if err := os.Remove(path); err != nil && !errors.Is(err, os.ErrNotExist) {
        return nil, fmt.Errorf("remove stale socket: %w", err)
    }

    l, err := net.Listen("unix", path)
    if err != nil {
        return nil, fmt.Errorf("listen on %s: %w", path, err)
    }

    // Restrict permissions to owner only
    if err := os.Chmod(path, 0600); err != nil {
        l.Close()
        return nil, fmt.Errorf("chmod socket: %w", err)
    }

    return &Server{
        listener: l,
        sem:      make(chan struct{}, MaxClients),
        log:      slog.Default(),
    }, nil
}

// Serve accepts connections until ctx is done.
func (s *Server) Serve() error {
    for {
        conn, err := s.listener.Accept()
        if err != nil {
            // Check if we're shutting down
            if errors.Is(err, net.ErrClosed) {
                return nil
            }
            s.log.Error("accept failed", "err", err)
            continue
        }

        // Acquire semaphore (non-blocking)
        select {
        case s.sem <- struct{}{}:
        default:
            s.log.Warn("max clients reached, dropping connection")
            conn.Close()
            continue
        }

        s.wg.Add(1)
        go func(c net.Conn) {
            defer s.wg.Done()
            defer func() { <-s.sem }() // Release semaphore slot
            defer c.Close()

            if err := s.handleConn(c); err != nil {
                if !errors.Is(err, io.EOF) &&
                    !errors.Is(err, io.ErrUnexpectedEOF) &&
                    !errors.Is(err, net.ErrClosed) {
                    s.log.Error("client error", "err", err)
                }
            }
        }(conn)
    }
}

// Shutdown gracefully stops the server.
func (s *Server) Shutdown() {
    s.listener.Close()
    s.wg.Wait()
    os.Remove(SocketPath)
}

// handleConn processes messages from one client connection.
func (s *Server) handleConn(conn net.Conn) error {
    // Get peer credentials (Unix-specific)
    unixConn, ok := conn.(*net.UnixConn)
    if !ok {
        return fmt.Errorf("not a UnixConn")
    }

    // Read peer credentials via SO_PEERCRED
    rawConn, err := unixConn.SyscallConn()
    if err == nil {
        var cred *syscall.Ucred
        rawConn.Control(func(fd uintptr) {
            cred, err = syscall.GetsockoptUcred(int(fd), syscall.SOL_SOCKET, syscall.SO_PEERCRED)
        })
        if err == nil && cred != nil {
            s.log.Info("new client",
                "pid", cred.Pid,
                "uid", cred.Uid,
                "gid", cred.Gid,
            )
        }
    }

    reader := bufio.NewReaderSize(conn, 65536)
    writer := bufio.NewWriterSize(conn, 65536)

    for {
        msg, err := readMessage(reader)
        if err != nil {
            return err
        }

        s.log.Info("received", "bytes", len(msg), "payload", string(msg))

        // Echo back
        if err := writeMessage(writer, msg); err != nil {
            return fmt.Errorf("write: %w", err)
        }
        if err := writer.Flush(); err != nil {
            return fmt.Errorf("flush: %w", err)
        }
    }
}

// readMessage reads a length-prefixed message.
// Format: [4-byte big-endian length][payload]
func readMessage(r io.Reader) ([]byte, error) {
    var lenBuf [4]byte
    if _, err := io.ReadFull(r, lenBuf[:]); err != nil {
        return nil, err
    }

    msgLen := binary.BigEndian.Uint32(lenBuf[:])
    if msgLen == 0 || msgLen > MaxMessageSize {
        return nil, fmt.Errorf("invalid message length: %d", msgLen)
    }

    buf := make([]byte, msgLen)
    if _, err := io.ReadFull(r, buf); err != nil {
        return nil, err
    }
    return buf, nil
}

// writeMessage writes a length-prefixed message.
func writeMessage(w io.Writer, msg []byte) error {
    var lenBuf [4]byte
    binary.BigEndian.PutUint32(lenBuf[:], uint32(len(msg)))

    if _, err := w.Write(lenBuf[:]); err != nil {
        return err
    }
    if _, err := w.Write(msg); err != nil {
        return err
    }
    return nil
}

func main() {
    srv, err := NewServer(SocketPath)
    if err != nil {
        slog.Error("create server", "err", err)
        os.Exit(1)
    }
    slog.Info("server started", "path", SocketPath)

    // Handle shutdown signals
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        <-sigCh
        slog.Info("shutting down")
        srv.Shutdown()
    }()

    if err := srv.Serve(); err != nil {
        slog.Error("serve error", "err", err)
    }
}
```

### 15.2 Client

```go
// client.go
package main

import (
    "bufio"
    "encoding/binary"
    "fmt"
    "io"
    "log/slog"
    "net"
    "os"
    "time"
)

const SocketPath = "/tmp/go_production.sock"

type Client struct {
    conn   *net.UnixConn
    reader *bufio.Reader
    writer *bufio.Writer
}

func Dial(path string) (*Client, error) {
    conn, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: path, Net: "unix"})
    if err != nil {
        return nil, fmt.Errorf("dial %s: %w", path, err)
    }

    // Set deadlines for all operations
    conn.SetDeadline(time.Now().Add(30 * time.Second))

    return &Client{
        conn:   conn,
        reader: bufio.NewReaderSize(conn, 65536),
        writer: bufio.NewWriterSize(conn, 65536),
    }, nil
}

func (c *Client) Send(msg []byte) error {
    var lenBuf [4]byte
    binary.BigEndian.PutUint32(lenBuf[:], uint32(len(msg)))
    if _, err := c.writer.Write(lenBuf[:]); err != nil {
        return err
    }
    if _, err := c.writer.Write(msg); err != nil {
        return err
    }
    return c.writer.Flush()
}

func (c *Client) Recv() ([]byte, error) {
    var lenBuf [4]byte
    if _, err := io.ReadFull(c.reader, lenBuf[:]); err != nil {
        return nil, err
    }
    msgLen := binary.BigEndian.Uint32(lenBuf[:])
    if msgLen > 4*1024*1024 {
        return nil, fmt.Errorf("message too large: %d", msgLen)
    }
    buf := make([]byte, msgLen)
    if _, err := io.ReadFull(c.reader, buf); err != nil {
        return nil, err
    }
    return buf, nil
}

func (c *Client) Close() { c.conn.Close() }

func main() {
    client, err := Dial(SocketPath)
    if err != nil {
        slog.Error("dial", "err", err)
        os.Exit(1)
    }
    defer client.Close()

    messages := []string{
        "Hello from Go!",
        "Goroutine-based concurrency",
        "Idiomatic channel patterns",
    }

    for _, msg := range messages {
        if err := client.Send([]byte(msg)); err != nil {
            slog.Error("send", "err", err)
            return
        }
        slog.Info("sent", "msg", msg)

        resp, err := client.Recv()
        if err != nil {
            slog.Error("recv", "err", err)
            return
        }
        slog.Info("echo", "response", string(resp))
    }
}
```

### 15.3 File Descriptor Passing in Go

```go
// fd_pass_go.go — SCM_RIGHTS in Go using syscall package
package main

import (
    "fmt"
    "net"
    "os"
    "syscall"
)

// SendFd sends a file descriptor over a Unix socket connection.
// At least 1 byte of data must accompany the fd.
func SendFd(conn *net.UnixConn, fd int) error {
    rights := syscall.UnixRights(fd)
    n, oobn, err := conn.WriteMsgUnix(
        []byte{0}, // dummy 1-byte payload
        rights,
        nil,
    )
    if err != nil {
        return fmt.Errorf("WriteMsgUnix: %w", err)
    }
    if n != 1 || oobn != len(rights) {
        return fmt.Errorf("incomplete write: n=%d oobn=%d", n, oobn)
    }
    return nil
}

// RecvFd receives a file descriptor from a Unix socket connection.
// Returns an *os.File wrapping the received fd.
func RecvFd(conn *net.UnixConn) (*os.File, error) {
    buf     := make([]byte, 1)
    oob     := make([]byte, syscall.CmsgSpace(4)) // Space for 1 int32

    n, oobn, _, _, err := conn.ReadMsgUnix(buf, oob)
    if err != nil {
        return nil, fmt.Errorf("ReadMsgUnix: %w", err)
    }
    if n != 1 {
        return nil, fmt.Errorf("expected 1 data byte, got %d", n)
    }

    // Parse control messages
    scms, err := syscall.ParseSocketControlMessage(oob[:oobn])
    if err != nil {
        return nil, fmt.Errorf("parse control message: %w", err)
    }

    for _, scm := range scms {
        fds, err := syscall.ParseUnixRights(&scm)
        if err != nil {
            continue
        }
        if len(fds) > 0 {
            // Wrap in os.File for automatic close-on-GC
            return os.NewFile(uintptr(fds[0]), "received_fd"), nil
        }
    }

    return nil, fmt.Errorf("no file descriptor found in control message")
}
```

---

## 16. gRPC over UNIX Domain Sockets

gRPC is a high-performance RPC framework built on HTTP/2. When both client and server are on the same machine, running gRPC over UDS eliminates TCP overhead while keeping gRPC's rich feature set: streaming, deadlines, interceptors, load balancing, and Protobuf serialization.

### 16.1 Why gRPC over UDS?

```
Standard gRPC:    Client → TCP loopback → Server
                  Overhead: TCP + TLS (optional) + HTTP/2 framing

gRPC over UDS:    Client → UNIX socket → Server
                  Overhead: HTTP/2 framing only (no TCP, no IP)
                  Latency improvement: ~30–50%
                  Throughput improvement: 20–40%
```

**Real-world use:** Docker daemon, containerd, kubelet, and most Kubernetes control plane components communicate internally via gRPC over UDS (e.g., `/run/containerd/containerd.sock`).

### 16.2 Proto Definition

```protobuf
// service.proto
syntax = "proto3";

package myservice.v1;

option go_package = "github.com/example/uds-grpc/proto";

service EchoService {
    // Unary RPC
    rpc Echo(EchoRequest) returns (EchoResponse);

    // Server-side streaming
    rpc StreamEcho(EchoRequest) returns (stream EchoResponse);

    // Bidirectional streaming
    rpc BidiEcho(stream EchoRequest) returns (stream EchoResponse);
}

message EchoRequest {
    string message  = 1;
    uint32 repeat   = 2; // For streaming: repeat N times
}

message EchoResponse {
    string message    = 1;
    uint64 sequence   = 2;
    int64  timestamp_ns = 3;
}
```

### 16.3 Go gRPC Server over UDS

```go
// grpc_server.go
package main

import (
    "context"
    "fmt"
    "log/slog"
    "net"
    "os"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc/peer"
    "google.golang.org/grpc/status"

    pb "github.com/example/uds-grpc/proto"
)

const GRPCSocketPath = "/tmp/grpc_service.sock"

// echoServer implements the EchoService interface.
type echoServer struct {
    pb.UnimplementedEchoServiceServer
    seq uint64
}

// Echo implements unary RPC.
func (s *echoServer) Echo(ctx context.Context, req *pb.EchoRequest) (*pb.EchoResponse, error) {
    // Extract peer info from context
    if p, ok := peer.FromContext(ctx); ok {
        slog.Info("echo request", "peer", p.Addr.String())
    }

    if req.Message == "" {
        return nil, status.Error(codes.InvalidArgument, "message must not be empty")
    }

    s.seq++
    return &pb.EchoResponse{
        Message:     fmt.Sprintf("Echo: %s", req.Message),
        Sequence:    s.seq,
        TimestampNs: time.Now().UnixNano(),
    }, nil
}

// StreamEcho implements server-side streaming.
func (s *echoServer) StreamEcho(req *pb.EchoRequest, stream pb.EchoService_StreamEchoServer) error {
    repeat := req.Repeat
    if repeat == 0 { repeat = 1 }
    if repeat > 100 {
        return status.Error(codes.InvalidArgument, "repeat must be <= 100")
    }

    for i := uint32(0); i < repeat; i++ {
        // Check for client cancellation
        if err := stream.Context().Err(); err != nil {
            return status.FromContextError(err).Err()
        }

        s.seq++
        if err := stream.Send(&pb.EchoResponse{
            Message:     fmt.Sprintf("[%d/%d] %s", i+1, repeat, req.Message),
            Sequence:    s.seq,
            TimestampNs: time.Now().UnixNano(),
        }); err != nil {
            return err
        }

        time.Sleep(10 * time.Millisecond) // Simulate work
    }
    return nil
}

// BidiEcho implements bidirectional streaming.
func (s *echoServer) BidiEcho(stream pb.EchoService_BidiEchoServer) error {
    for {
        req, err := stream.Recv()
        if err != nil {
            return err // io.EOF means client is done
        }

        s.seq++
        if err := stream.Send(&pb.EchoResponse{
            Message:     fmt.Sprintf("Bidi: %s", req.Message),
            Sequence:    s.seq,
            TimestampNs: time.Now().UnixNano(),
        }); err != nil {
            return err
        }
    }
}

func main() {
    // Remove stale socket
    os.Remove(GRPCSocketPath)

    // Create UDS listener
    lis, err := net.Listen("unix", GRPCSocketPath)
    if err != nil {
        slog.Error("listen failed", "err", err)
        os.Exit(1)
    }
    os.Chmod(GRPCSocketPath, 0600)

    // Build gRPC server with options
    srv := grpc.NewServer(
        // Limit on incoming message size
        grpc.MaxRecvMsgSize(4*1024*1024),
        grpc.MaxSendMsgSize(4*1024*1024),

        // Unary interceptor for logging/auth
        grpc.UnaryInterceptor(loggingInterceptor),
    )

    pb.RegisterEchoServiceServer(srv, &echoServer{})

    slog.Info("gRPC server listening", "path", GRPCSocketPath)
    if err := srv.Serve(lis); err != nil {
        slog.Error("serve error", "err", err)
    }
}

// loggingInterceptor is a unary server interceptor.
func loggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    slog.Info("RPC",
        "method", info.FullMethod,
        "duration", time.Since(start),
        "err", err,
    )
    return resp, err
}
```

### 16.4 Go gRPC Client over UDS

```go
// grpc_client.go
package main

import (
    "context"
    "fmt"
    "io"
    "log/slog"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"

    pb "github.com/example/uds-grpc/proto"
)

const GRPCSocketPath = "/tmp/grpc_service.sock"

func main() {
    // Connect via UDS: "unix://" prefix tells gRPC to use UDS
    conn, err := grpc.NewClient(
        "unix://"+GRPCSocketPath,
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithDefaultCallOptions(
            grpc.MaxCallRecvMsgSize(4*1024*1024),
        ),
    )
    if err != nil {
        slog.Error("dial failed", "err", err)
        return
    }
    defer conn.Close()

    client := pb.NewEchoServiceClient(conn)
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    // --- Unary RPC ---
    slog.Info("=== Unary RPC ===")
    resp, err := client.Echo(ctx, &pb.EchoRequest{Message: "Hello gRPC over UDS!"})
    if err != nil {
        slog.Error("echo failed", "err", err)
        return
    }
    slog.Info("response",
        "message", resp.Message,
        "sequence", resp.Sequence,
        "latency_us", time.Duration(resp.TimestampNs),
    )

    // --- Server Streaming ---
    slog.Info("=== Server Streaming ===")
    stream, err := client.StreamEcho(ctx, &pb.EchoRequest{
        Message: "Streaming test",
        Repeat:  3,
    })
    if err != nil {
        slog.Error("stream echo failed", "err", err)
        return
    }
    for {
        msg, err := stream.Recv()
        if err == io.EOF { break }
        if err != nil { slog.Error("stream recv", "err", err); break }
        fmt.Printf("  Stream[%d]: %s\n", msg.Sequence, msg.Message)
    }

    // --- Bidirectional Streaming ---
    slog.Info("=== Bidirectional Streaming ===")
    bidi, err := client.BidiEcho(ctx)
    if err != nil {
        slog.Error("bidi failed", "err", err)
        return
    }

    messages := []string{"ping", "pong", "done"}
    for _, m := range messages {
        bidi.Send(&pb.EchoRequest{Message: m})
        resp, err := bidi.Recv()
        if err != nil { break }
        fmt.Printf("  Bidi: sent=%s, recv=%s\n", m, resp.Message)
    }
    bidi.CloseSend()
}
```

### 16.5 Rust gRPC over UDS (tonic)

```rust
// Cargo.toml additions for gRPC:
// tonic = { version = "0.11", features = ["transport"] }
// prost = "0.12"
// tokio = { version = "1", features = ["full"] }
// tower = "0.4"
// hyper-util = { version = "0.1", features = ["tokio"] }

// src/grpc_server.rs
use std::path::Path;
use tokio::net::UnixListener;
use tokio_stream::wrappers::UnixListenerStream;
use tonic::{transport::Server, Request, Response, Status};

// Generated by tonic-build from .proto file
// pub mod proto { tonic::include_proto!("myservice.v1"); }
// For illustration, we inline the trait:

pub struct EchoServiceImpl;

// In real code, this would be the tonic-generated trait implementation.
// The key pattern for UDS with tonic:
pub async fn run_grpc_server() -> Result<(), Box<dyn std::error::Error>> {
    let socket_path = "/tmp/tonic_grpc.sock";

    if Path::new(socket_path).exists() {
        std::fs::remove_file(socket_path)?;
    }

    let uds = UnixListener::bind(socket_path)?;
    let stream = UnixListenerStream::new(uds);

    // Build the tonic server
    Server::builder()
        // Add service: .add_service(EchoServiceServer::new(EchoServiceImpl))
        .serve_with_incoming(stream)
        .await?;

    Ok(())
}

// src/grpc_client.rs — Connect to UDS gRPC server from Rust (tonic)
use hyper_util::rt::TokioIo;
use tokio::net::UnixStream;
use tonic::transport::{Channel, Endpoint, Uri};
use tower::service_fn;

pub async fn connect_uds_channel(path: &str) -> Result<Channel, Box<dyn std::error::Error>> {
    let path = path.to_string();

    // The URI scheme doesn't matter for UDS — we override the connector.
    let channel = Endpoint::try_from("http://[::]:50051")?
        .connect_with_connector(service_fn(move |_: Uri| {
            let path = path.clone();
            async move {
                let stream = UnixStream::connect(&path).await?;
                Ok::<_, std::io::Error>(TokioIo::new(stream))
            }
        }))
        .await?;

    Ok(channel)
}

// Usage:
// let channel = connect_uds_channel("/tmp/tonic_grpc.sock").await?;
// let client = EchoServiceClient::new(channel);
```

### 16.6 gRPC over UDS — Architecture Summary

```
Client Process                    Server Process
    |                                  |
    | grpc.NewClient("unix:///tmp/x")  |
    |     ↓                            |
    | HTTP/2 over UnixConn             |
    |     ↓                            |
    | Protobuf serialization           |
    |     ↓                            |
    | ←——— UNIX Domain Socket ———→     |
    |                     ↓            |
    |              net.Listen("unix")  |
    |                     ↓            |
    |              grpc.Server.Serve() |
    |                     ↓            |
    |              Protobuf deserialize|
    |                     ↓            |
    |              Handler function    |
```

**Key gRPC + UDS integration points:**
- **No TLS required** for local communication — UDS provides OS-level isolation.
- **Peer credentials** replace certificate-based auth — use `SO_PEERCRED` in an interceptor.
- **Connection pooling** — gRPC multiplexes multiple RPCs over a single HTTP/2 connection (single UDS connection per client).

---

## 17. Advanced Patterns & Edge Cases

### 17.1 Autobind (Linux-Only)

Binding a SOCK_DGRAM socket with `addrlen = sizeof(sa_family_t)` causes the kernel to auto-assign a unique abstract address:

```c
struct sockaddr_un addr = { .sun_family = AF_UNIX };
/* Pass ONLY the family size — kernel assigns address */
bind(fd, (struct sockaddr *)&addr, sizeof(sa_family_t));

/* Retrieve the assigned address */
struct sockaddr_un bound_addr;
socklen_t len = sizeof(bound_addr);
getsockname(fd, (struct sockaddr *)&bound_addr, &len);
/* bound_addr.sun_path[0] = '\0', rest is a 5-char hex address */
```

Useful for reply addressing in datagram protocols without managing names manually.

### 17.2 socketpair(2) — Anonymous Connected Pair

Creates two connected sockets without binding or listening:

```c
int fds[2];
socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, fds);
/* fds[0] and fds[1] are connected to each other */
/* Write to fds[0], read from fds[1], and vice versa */
```

**Use case:** Parent-child IPC after `fork()`. The parent keeps `fds[0]`, child keeps `fds[1]`, both close the other. This is how `popen()` works internally and how many privilege-separation architectures (like OpenSSH's privsep) operate.

```c
int fds[2];
socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, fds);

pid_t pid = fork();
if (pid == 0) {
    /* Child: use fds[1] */
    close(fds[0]);
    /* child_main(fds[1]); */
} else {
    /* Parent: use fds[0] */
    close(fds[1]);
    /* parent_main(fds[0]); */
}
```

### 17.3 Handling EINTR Correctly

Any blocking system call can be interrupted by a signal and return `EINTR`. This is NOT an error — it means "retry":

```c
ssize_t safe_recv(int fd, void *buf, size_t len) {
    for (;;) {
        ssize_t n = recv(fd, buf, len, 0);
        if (n == -1 && errno == EINTR) continue; /* Signal interrupted — retry */
        return n; /* Success or real error */
    }
}
```

With `SA_RESTART` in signal handlers (`sigaction` flag), most syscalls auto-restart after `EINTR`. But `recv()` with a timeout does NOT auto-restart — always handle `EINTR` explicitly.

### 17.4 MSG_PEEK — Non-Destructive Read

Read data without consuming it from the queue:

```c
char peek_buf[4];
ssize_t n = recv(fd, peek_buf, sizeof(peek_buf), MSG_PEEK);
/* Data is still in the queue; next recv() will return it again */
```

Useful for protocol detection: peek at the first few bytes to determine the protocol, then dispatch to the appropriate handler.

### 17.5 SO_RCVTIMEO / SO_SNDTIMEO — Socket Timeouts

Set timeouts on blocking operations:

```c
struct timeval tv = { .tv_sec = 30, .tv_usec = 0 };
setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
/* Now recv() returns -1 with errno=EAGAIN after 30 seconds */
```

For production code, prefer `poll()`/`epoll()` + non-blocking sockets over timeout options — timeouts are less predictable under load.

### 17.6 Detecting Peer Death

When a peer process dies or closes its socket end:
- `recv()` returns `0` (EOF on `SOCK_STREAM`).
- `poll()` reports `POLLHUP`.
- `send()` returns `-1` with `errno = EPIPE` (and sends `SIGPIPE` unless `MSG_NOSIGNAL`).

```c
/* Reliable peer-death detection using SO_ERROR after poll POLLHUP */
int err = 0;
socklen_t err_len = sizeof(err);
getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &err_len);
if (err == ECONNRESET || err == EPIPE) {
    /* Peer died unexpectedly */
}
```

### 17.7 Abstract Namespace in Network Namespaces

Abstract sockets are scoped to the **network namespace**, not the filesystem. This means:

- Container A with its own network namespace cannot connect to container B's abstract socket.
- Filesystem-path sockets CAN be shared across containers that share a volume mount.
- When designing container-based microservices, choose namespace type accordingly.

### 17.8 Passing Multiple File Descriptors

You can pass multiple fds in one `sendmsg()`:

```c
int fds[3] = { fd1, fd2, fd3 };
char cmsg_buf[CMSG_SPACE(sizeof(fds))];

struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_len   = CMSG_LEN(sizeof(fds));
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_RIGHTS;
memcpy(CMSG_DATA(cmsg), fds, sizeof(fds));
```

The kernel limit on fds per message is `SCM_MAX_FD` = 253 (Linux).

---

## 18. Observability & Debugging

### 18.1 List All UDS Sockets

```bash
# All UDS sockets on the system
ss -x -a

# With process info (requires root or matching uid)
ss -x -a -p

# Specific socket
ss -x -a src "/tmp/myapp.sock"
```

**Output columns:**
```
Netid  State    Recv-Q Send-Q  Local Address:Port  Peer Address:Port
u_str  LISTEN   0      128     /tmp/myapp.sock 0    * 0
u_str  ESTAB    0      0       /tmp/myapp.sock 1234 * 5678
```

### 18.2 Inspect via /proc/net/unix

```bash
cat /proc/net/unix
# Or more readable:
cat /proc/net/unix | awk 'NR==1 || /LISTEN|ESTAB/'
```

For abstract sockets, the name is shown with `@` prefix (replacing the leading null byte).

### 18.3 Strace — System Call Tracing

```bash
# Trace UDS-related syscalls of a running process
strace -e trace=network -p <PID>

# Trace a new process
strace -e trace=socket,bind,connect,sendmsg,recvmsg ./my_server
```

### 18.4 lsof — List Open Sockets

```bash
lsof -U                          # All UDS sockets
lsof -U -p <PID>                 # Specific process
lsof /tmp/myapp.sock             # Who has this socket open
```

### 18.5 socat — UDS Testing Tool

```bash
# Connect to a UDS server and interact manually
socat - UNIX-CONNECT:/tmp/myapp.sock

# Create a simple echo server for testing
socat UNIX-LISTEN:/tmp/test.sock,fork EXEC:'cat'

# Bridge UDS to TCP (useful for remote debugging)
socat TCP-LISTEN:9999,fork UNIX-CONNECT:/tmp/myapp.sock
```

### 18.6 perf — Performance Analysis

```bash
# Profile syscall overhead in a UDS server
perf stat -e syscalls:sys_enter_recvmsg,syscalls:sys_enter_sendmsg ./server

# Record flamegraph
perf record -g ./server
perf report
```

### 18.7 bpftrace — eBPF Tracing

```bash
# Trace all UDS connect attempts
bpftrace -e 'tracepoint:syscalls:sys_enter_connect {
    printf("PID %d connecting\n", pid);
}'

# Measure UDS recv latency
bpftrace -e '
kprobe:unix_stream_recvmsg { @start[tid] = nsecs; }
kretprobe:unix_stream_recvmsg {
    $lat = nsecs - @start[tid];
    @latency = hist($lat);
    delete(@start[tid]);
}'
```

---

## 19. Production Hardening Checklist

### Security

- [ ] **Set restrictive permissions** on socket file (`0600` or `0660`, not `0777`).
- [ ] **Verify peer credentials** via `SO_PEERCRED` or `SCM_CREDENTIALS` before accepting commands.
- [ ] **Validate all message lengths** before allocation — prevent integer overflow and excessive allocation.
- [ ] **Use abstract namespace** only when no filesystem-level access control is needed.
- [ ] **Set `SOCK_CLOEXEC`** on all sockets to prevent fd leakage across `exec()`.
- [ ] **Never trust `pid` from `SO_PEERCRED`** without cross-checking `/proc/<pid>/exe` — pid can be recycled.

### Reliability

- [ ] **Remove stale socket file** at startup with `unlink()` (handle `ENOENT`).
- [ ] **Remove socket file at shutdown** with `unlink()`.
- [ ] **Handle `EINTR`** on all blocking calls.
- [ ] **Use `MSG_NOSIGNAL`** or `signal(SIGPIPE, SIG_IGN)` to handle broken pipe.
- [ ] **Implement reconnect logic** in clients with exponential backoff.
- [ ] **Heartbeat / keepalive** for long-lived connections.
- [ ] **Handle EOF** (`recv()` returns 0) as a normal disconnection.

### Performance

- [ ] **Use `accept4()`** instead of `accept()` to avoid extra `fcntl()` calls.
- [ ] **Increase socket buffer sizes** for high-throughput scenarios (`SO_RCVBUF`, `SO_SNDBUF`).
- [ ] **Use `sendmsg()` with scatter-gather I/O** (`struct iovec`) to avoid extra copies.
- [ ] **Tune backlog** in `listen()` to match expected concurrency.
- [ ] **Use `epoll` with edge-triggered mode** for high-connection-count servers.
- [ ] **Profile with `perf`** and `bpftrace` to find bottlenecks.

### Correctness

- [ ] **Length-prefix all messages** on `SOCK_STREAM` — byte streams have no inherent boundaries.
- [ ] **Handle partial reads/writes** — network I/O can return less than requested.
- [ ] **Close received file descriptors** if they are not used — fd leaks are silent and fatal under load.
- [ ] **Use atomic flag** for server shutdown, not raw `exit()` from signal handler.
- [ ] **Test under `valgrind --tool=helgrind`** for race conditions in multi-threaded servers.

### Operational

- [ ] **Expose metrics** (connection count, message rate, latency percentiles) via Prometheus or similar.
- [ ] **Log peer credentials** (pid, uid) on connection for audit trails.
- [ ] **Use systemd socket activation** (`SD_LISTEN_FDS`) for zero-downtime restarts.
- [ ] **Document the socket path** in `/etc/`, not hardcoded deep in source.

---

## Appendix A: Systemd Socket Activation

Systemd can pre-create the socket and pass the fd to your process, allowing zero-downtime restarts:

```ini
# /etc/systemd/system/myservice.socket
[Unit]
Description=My Service UDS Socket

[Socket]
ListenStream=/run/myservice/service.sock
SocketMode=0660
SocketUser=myservice
SocketGroup=mygroup

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myservice.service
[Unit]
Description=My Service
Requires=myservice.socket

[Service]
ExecStart=/usr/bin/myservice
# Systemd passes the socket fd via SD_LISTEN_FDS env var
```

In your server:
```c
#include <systemd/sd-daemon.h>

int n = sd_listen_fds(0); /* Number of socket fds passed by systemd */
if (n > 0) {
    int server_fd = SD_LISTEN_FDS_START; /* First socket fd */
    /* Use server_fd directly — no bind/listen needed */
}
```

---

## Appendix B: Key errno Values for UDS

| errno | Name | Meaning |
|---|---|---|
| `EACCES` | Permission denied | Socket file not accessible, or `connect()` refused by file permissions |
| `EADDRINUSE` | Address in use | Socket file already exists (`bind()` failed) |
| `ECONNREFUSED` | Connection refused | No server listening at the path |
| `ENOENT` | No such file | Socket path doesn't exist |
| `ENAMETOOLONG` | Name too long | Path > 107 chars |
| `EAGAIN` / `EWOULDBLOCK` | Try again | Non-blocking op would block |
| `EPIPE` | Broken pipe | Peer closed connection |
| `EMFILE` | Too many open files | Process fd limit reached |
| `ENOMEM` | Out of memory | Kernel can't allocate socket buffer |

---

## Appendix C: Quick Reference Card

```
CREATE:     socket(AF_UNIX, SOCK_STREAM|SOCK_CLOEXEC, 0)
BIND:       bind(fd, &addr, offsetof(sockaddr_un, sun_path) + strlen(path) + 1)
LISTEN:     listen(fd, 128)
ACCEPT:     accept4(fd, &client_addr, &len, SOCK_CLOEXEC|SOCK_NONBLOCK)
CONNECT:    connect(fd, &addr, addrlen)
SEND:       send(fd, buf, len, MSG_NOSIGNAL)
RECV:       recv(fd, buf, sizeof(buf), 0)
SEND_FD:    sendmsg() with cmsghdr{SOL_SOCKET, SCM_RIGHTS, fd}
RECV_FD:    recvmsg() + CMSG_FIRSTHDR() + CMSG_DATA()
PEER_CRED:  getsockopt(fd, SOL_SOCKET, SO_PEERCRED, &ucred, &len)
CLEANUP:    close(fd); unlink(path);  [for filesystem sockets]
DEBUG:      ss -xap | grep myapp
            lsof -U -p <PID>
            socat - UNIX-CONNECT:/tmp/myapp.sock
```

---

*End of Guide — UNIX Domain Sockets in Linux*
*Cover: Internals → C → Rust → Go → gRPC → Production*

Now let me build the comprehensive guide. This will be a large, deeply structured `.md` file.Here's your complete guide. Let me walk you through what's inside and the key mental models to internalize:

---

**What the guide covers — and why in that order:**

The guide follows the **abstraction stack from bottom to top** — the same order a kernel engineer would think. You cannot master UDS APIs without understanding *why* they are shaped the way they are, so it starts with kernel internals (`struct sock`, `sk_buff`, the accept queue, copy paths) before touching a single line of user code.

**The three most important insights to absorb first:**

1. **UDS is not "local TCP"** — it's a completely different kernel subsystem. TCP loopback still traverses the IP and TCP layers; UDS goes directly from one process's `sk_receive_queue` to another's. The difference is not just latency — it's that UDS exposes entirely different capabilities (fd passing, credential passing) that TCP cannot offer at any speed.

2. **`SOCK_STREAM` has no message boundaries.** This is the single most common UDS bug. If you `write("hello")` and `write("world")`, the receiver may `read("helloworld")` in one call. Every production protocol must implement its own framing — the guide shows a 4-byte length-prefix approach, which is the industry standard (used by gRPC, containerd, dockerd, etc.).

3. **fd passing via `SCM_RIGHTS` is architecturally profound.** It enables *privilege separation* at the OS level: a root process opens a privileged file or socket, then hands the fd to an unprivileged worker. The worker never needed to open the resource itself. This is how OpenSSH privsep, Chrome's sandbox, and systemd socket activation work.

**On the gRPC section:** The URL scheme `unix:///path` is the critical piece — most developers get stuck here. The guide also covers the Rust `tonic` pattern where you must override the connector with `tower::service_fn` because tonic's default connector doesn't speak UDS natively.

**Recommended study sequence:** Read sections 3 → 6 → 7 → 13 (C server) in one sitting, building and running the code. Then tackle sections 9–11 (ancillary data) separately — they require focused attention. gRPC (section 16) builds on everything before it.