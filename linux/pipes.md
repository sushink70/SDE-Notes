# Linux Pipes: A Complete & Comprehensive Guide

> **Kernel version context**: Unless otherwise noted, all analysis targets **Linux 6.8+** (mainline).  
> Source references: `fs/pipe.c`, `include/linux/pipe_fs_i.h`, `fs/splice.c`, `fs/fifo.c`

---

## Table of Contents

1. [Conceptual Foundation](#1-conceptual-foundation)
2. [Anonymous Pipes — User API](#2-anonymous-pipes--user-api)
3. [Named Pipes (FIFOs)](#3-named-pipes-fifos)
4. [Kernel Internals: Data Structures](#4-kernel-internals-data-structures)
5. [Kernel Internals: Code Paths](#5-kernel-internals-code-paths)
6. [Pipe Capacity, Limits & Tunables](#6-pipe-capacity-limits--tunables)
7. [Pipe Flags & Modes](#7-pipe-flags--modes)
8. [Zero-Copy: splice(), tee(), vmsplice()](#8-zero-copy-splice-tee-vmsplice)
9. [Shell Pipelines — Deep Dive](#9-shell-pipelines--deep-dive)
10. [Signals: SIGPIPE & EPIPE](#10-signals-sigpipe--epipe)
11. [Bidirectional & Full-Duplex Pipes](#11-bidirectional--full-duplex-pipes)
12. [Pipe vs. Other IPC Mechanisms](#12-pipe-vs-other-ipc-mechanisms)
13. [Advanced: Pipe Tricks & Patterns](#13-advanced-pipe-tricks--patterns)
14. [Networking Stack & Pipes](#14-networking-stack--pipes)
15. [Pipes in Containers & Cloud](#15-pipes-in-containers--cloud)
16. [Security: Pipe-Related Attacks & Mitigations](#16-security-pipe-related-attacks--mitigations)
17. [Debugging & Tracing Pipes](#17-debugging--tracing-pipes)
18. [Performance Characteristics](#18-performance-characteristics)
19. [Pipe in Kernel Driver / Module Code](#19-pipe-in-kernel-driver--module-code)
20. [Reference Summary](#20-reference-summary)

---

## 1. Conceptual Foundation

### 1.1 What is a Pipe?

A **pipe** is a unidirectional, buffered, byte-stream IPC channel implemented entirely in kernel memory. It has no filesystem backing (anonymous pipe) or an inode entry with no data blocks on disk (named pipe). Data written at one end is consumed from the other end in strict FIFO order.

```
Producer (writer)                       Consumer (reader)
    fd[1] ──────► [ kernel ring buffer ] ──────► fd[0]
    (write end)     (pipe_inode_info)             (read end)
```

Key properties:
- **Half-duplex**: single direction of data flow per pipe instance.
- **Byte-stream**: no message boundaries; `write(n)` + `write(m)` != two `read()` calls of n and m.
- **Kernel-buffered**: writer does not block until buffer full; reader does not block until buffer non-empty (default blocking mode).
- **Flow-controlled**: backpressure is automatic — writer blocks when buffer full.
- **Lifetime**: Anonymous pipe lives as long as at least one fd referencing each end is open.

### 1.2 POSIX Guarantees

From POSIX.1-2017 (`pipe(2)` and `write(2)`):

- Writes of `<= PIPE_BUF` bytes (4096 on Linux) are **atomic**: either all bytes are written or none (no interleaving with concurrent writers).
- Writes of `> PIPE_BUF` bytes may be interleaved.
- `PIPE_BUF` is defined in `<limits.h>` and verified via `fpathconf(fd, _PC_PIPE_BUF)`.

```c
/* include/uapi/linux/limits.h */
#define PIPE_BUF        4096
```

### 1.3 Historical Context

Pipes were introduced by Ken Thompson in Unix V3 (1973), inspired by Doug McIlroy's vision of composable tools. The `|` operator in shell remains one of Unix's most powerful ideas. Linux re-implemented pipes with:
- Page-based ring buffers (vs. original fixed-size kernel buffers).
- `splice()`/`tee()` zero-copy extensions (Linux 2.6.17).
- Pipe capacity increase to 64 KiB default (Linux 2.6.11).
- `F_SETPIPE_SZ` / `F_GETPIPE_SZ` dynamic resizing (Linux 2.6.35).
- Packet mode (`O_DIRECT` on pipes, Linux 3.4).
- CVE-2022-0847 "Dirty Pipe" (Linux 5.8-5.16.11) — page-cache write via pipe splicing.

---

## 2. Anonymous Pipes — User API

### 2.1 `pipe(2)` / `pipe2(2)`

```c
#include <unistd.h>
#include <fcntl.h>

int pipe(int pipefd[2]);
int pipe2(int pipefd[2], int flags);  /* Linux 2.6.27+ */
```

`pipefd[0]` = read end, `pipefd[1]` = write end.

`pipe2()` accepts:
| Flag | Effect |
|---|---|
| `O_NONBLOCK` | Set `O_NONBLOCK` on both fds atomically |
| `O_CLOEXEC` | Set `FD_CLOEXEC` on both fds atomically |
| `O_DIRECT` | Packet mode (each write is a discrete message) |

### 2.2 Minimal Producer/Consumer

```c
/* tools/pipe_demo.c — kernel-style, no stdlib */
#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>

#define MSG "hello from parent\n"

int main(void)
{
    int pfd[2];
    pid_t child;
    char buf[64];
    ssize_t n;

    if (pipe2(pfd, O_CLOEXEC) < 0)
        return 1;

    child = fork();
    if (child == 0) {
        /* child: reader */
        close(pfd[1]);                       /* close write end */
        n = read(pfd[0], buf, sizeof(buf));
        write(STDOUT_FILENO, buf, n);
        close(pfd[0]);
        return 0;
    }

    /* parent: writer */
    close(pfd[0]);                           /* close read end */
    write(pfd[1], MSG, sizeof(MSG) - 1);
    close(pfd[1]);                           /* EOF to child */
    waitpid(child, NULL, 0);
    return 0;
}
```

**Critical rule**: Always close the unused end in each process. Failing to close `pfd[1]` in the child means the read end will never see EOF — the child blocks forever on `read()`.

### 2.3 File Descriptor Layout After `fork()`

```
Before fork():
  Parent:  fd[0]=read  fd[1]=write
                |              |
           [ pipe kernel object (pipe_inode_info) ]

After fork():
  Parent:  fd[0]  fd[1]  <- must close fd[0]
  Child:   fd[0]  fd[1]  <- must close fd[1]
                |
     pipe_inode_info.readers=2, .writers=2

After closing unused ends:
  Parent:         fd[1]  --> writer
  Child:   fd[0]         --> reader
                |
     pipe_inode_info.readers=1, .writers=1
```

### 2.4 Connecting Pipe to stdin/stdout with `dup2()`

This is exactly what a shell does when you write `cmd1 | cmd2`:

```c
/* Shell pipe plumbing — simplified */
int pfd[2];
pipe2(pfd, O_CLOEXEC);

if (fork() == 0) {
    /* cmd1: stdout -> write end */
    dup2(pfd[1], STDOUT_FILENO);
    close(pfd[0]); close(pfd[1]);
    execlp("cmd1", "cmd1", NULL);
}

if (fork() == 0) {
    /* cmd2: stdin <- read end */
    dup2(pfd[0], STDIN_FILENO);
    close(pfd[0]); close(pfd[1]);
    execlp("cmd2", "cmd2", NULL);
}

close(pfd[0]); close(pfd[1]);  /* parent closes both */
wait(NULL); wait(NULL);
```

`dup2(oldfd, newfd)` atomically duplicates `oldfd` onto `newfd`, closing `newfd` first if open. After `dup2(pfd[1], STDOUT_FILENO)`, fd 1 points to the write end of the pipe.

---

## 3. Named Pipes (FIFOs)

### 3.1 Creation

```bash
mkfifo /tmp/myfifo                  # shell
mkfifo -m 0600 /tmp/myfifo          # with explicit permissions
```

```c
#include <sys/stat.h>
int mkfifo(const char *pathname, mode_t mode);  /* POSIX */
int mknod(const char *pathname, S_IFIFO | mode, 0);  /* lower-level */
```

A FIFO has a directory entry and inode (managed by the filesystem's `fifo_inode_operations`), but **no data blocks on disk**. All data lives in the same `pipe_inode_info` ring buffer as anonymous pipes.

```
Filesystem namespace:
  /tmp/myfifo  ---> inode (S_IFIFO, i_pipe = pipe_inode_info*)
                        |
                  [ kernel ring buffer ]
                        |
  Writer opens  <-------+-------> Reader opens
  (O_WRONLY)            |         (O_RDONLY)
```

### 3.2 Open Semantics (Blocking vs Non-Blocking)

FIFO open has unique blocking semantics unlike regular files:

| Writer calls `open(O_WRONLY)` | Reader calls `open(O_RDONLY)` | Result |
|---|---|---|
| No reader yet | — | Writer **blocks** until a reader opens |
| — | No writer yet | Reader **blocks** until a writer opens |
| With `O_NONBLOCK` | No reader | Returns `ENXIO` immediately |
| — | With `O_NONBLOCK`, no writer | Returns fd immediately (read returns 0/EOF) |

```bash
# Terminal 1 — blocks until Terminal 2 opens the read end
echo "data" > /tmp/myfifo

# Terminal 2
cat /tmp/myfifo
```

### 3.3 FIFO Use Case: Avoiding Temporary Files

```bash
# Without FIFO — temp file needed
gzip -dc large.gz > /tmp/unpacked && sort /tmp/unpacked > sorted.txt

# With process substitution (bash FIFO internally)
sort <(gzip -dc large.gz) > sorted.txt

# Explicit FIFO
mkfifo /tmp/fifo
gzip -dc large.gz > /tmp/fifo &
sort /tmp/fifo > sorted.txt
rm /tmp/fifo
```

### 3.4 FIFO in `procfs`

```bash
ls -la /proc/self/fd/          # shows open fds
stat /tmp/myfifo               # shows inode, S_IFIFO in mode
lsof /tmp/myfifo               # shows which processes have it open
```

```
File: /tmp/myfifo
Size: 0               Blocks: 0          IO Block: 4096  fifo
Device: fd01h/64769d  Inode: 3145729     Links: 1
Access: (0600/prw-------)
```

---

## 4. Kernel Internals: Data Structures

### 4.1 `pipe_inode_info` — The Core

```c
/* include/linux/pipe_fs_i.h */
struct pipe_inode_info {
    struct mutex        mutex;          /* protect pipe internals */
    wait_queue_head_t   rd_wait;        /* readers wait here */
    wait_queue_head_t   wr_wait;        /* writers wait here */
    unsigned int        head;           /* producer index (write to bufs[head % ring_size]) */
    unsigned int        tail;           /* consumer index (read from bufs[tail % ring_size]) */
    unsigned int        max_usage;      /* max # of bufs ever used */
    unsigned int        ring_size;      /* total # of slots (must be power of 2) */
#ifdef CONFIG_WATCH_QUEUE
    struct watch_queue  *watch_queue;
#endif
    unsigned int        nr_accounted;   /* # pipe_bufs charged to user */
    unsigned int        readers;        /* # of reader fds */
    unsigned int        writers;        /* # of writer fds */
    unsigned int        files;          /* # of files attached (splice) */
    unsigned int        r_counter;      /* # readers who have ever opened */
    unsigned int        w_counter;      /* # writers who have ever opened */
    bool                poll_usage;     /* has been polled? enables wake_up_all */
    struct page         **tmp_page;     /* cached page for writes */
    struct fasync_struct *fasync_readers;
    struct fasync_struct *fasync_writers;
    struct pipe_buffer  *bufs;          /* ring buffer of pipe_buffer slots */
    struct user_struct  *user;          /* user who created the pipe */
};
```

> Source: `include/linux/pipe_fs_i.h`, `fs/pipe.c`

### 4.2 `pipe_buffer` — Individual Slot

```c
/* include/linux/pipe_fs_i.h */
struct pipe_buffer {
    struct page     *page;      /* the page containing data */
    unsigned int    offset;     /* byte offset within page */
    unsigned int    len;        /* byte length of data in this buffer */
    const struct pipe_buf_operations *ops;
    unsigned int    flags;      /* PIPE_BUF_FLAG_* */
    unsigned long   private;    /* ops-specific private data */
};
```

`pipe_buf_operations`:
```c
struct pipe_buf_operations {
    /*
     * ->confirm() verifies that the data in the pipe_buffer is there
     * and that the contents are good.
     */
    int  (*confirm)(struct pipe_inode_info *, struct pipe_buffer *);
    /*
     * When the contents of this pipe_buffer has been completely
     * consumed by a reader, ->release() is called.
     */
    void (*release)(struct pipe_inode_info *, struct pipe_buffer *);
    /*
     * Attempt to take ownership of the pipe_buffer for writing.
     */
    bool (*try_steal)(struct pipe_inode_info *, struct pipe_buffer *);
    /*
     * Get a reference to the pipe_buffer.
     */
    bool (*get)(struct pipe_inode_info *, struct pipe_buffer *);
};
```

Different implementations:
- `anon_pipe_buf_ops` — for data written by `write()` into pipe.
- `page_cache_pipe_buf_ops` — for data spliced from page cache.
- `user_page_pipe_buf_ops` — for `vmsplice()` from user pages.

### 4.3 Ring Buffer Layout

```
pipe_inode_info.bufs[] — circular ring (ring_size slots):

  Index:  0       1       2       3       4       5       6       7
        +-------+-------+-------+-------+-------+-------+-------+-------+
  bufs: | buf   | buf   | buf   | buf   | buf   | buf   | buf   | buf   |
        +-------+-------+-------+-------+-------+-------+-------+-------+
                    ^                       ^
                   tail                   head
               (next read)            (next write)

  Occupied: bufs[tail % ring_size] through bufs[(head-1) % ring_size]
  Free:     bufs[head % ring_size] through bufs[(tail-1) % ring_size]

  used  = head - tail          (# filled slots)
  avail = ring_size - used     (# free slots)
  FULL  = used == ring_size
  EMPTY = head == tail
```

Each slot holds one `page` (4096 bytes), so:
- **Default capacity** = 16 slots x 4096 bytes = **65536 bytes (64 KiB)**
- Configurable up to `/proc/sys/fs/pipe-max-size` (1 MiB default)

### 4.4 Inode Relationship

```
struct inode {
    umode_t             i_mode;       /* S_IFIFO */
    struct pipe_inode_info *i_pipe;   /* <- points here for FIFOs & pipes */
    ...
};

get_pipe_inode()  ---> alloc_inode() + alloc_pipe_info()
                            |
                    pipe_inode_info allocated
                    ring_size = PIPE_DEF_BUFFERS (16)
                    bufs      = kcalloc(ring_size, sizeof(pipe_buffer))
```

For anonymous pipes: `pipefs` is a pseudo-filesystem (`fs/pipe.c`) — pipes get inodes from this internal VFS mount, never visible to userspace `ls`.

For FIFOs: the inode lives in the actual filesystem (`ext4`, `tmpfs`, etc.), but `i_pipe` points to the same `pipe_inode_info` mechanism.

---

## 5. Kernel Internals: Code Paths

### 5.1 `pipe(2)` Syscall Path

```
sys_pipe2(pipefd, flags)
    +-- do_pipe2(fds, flags)
            +-- __do_pipe_flags(fds, files, flags)
                    |-- create_pipe_files(files, flags)
                    |       |-- get_pipe_inode()
                    |       |       |-- new_inode(pipe_mnt->mnt_sb)
                    |       |       +-- alloc_pipe_info()
                    |       |               |-- kcalloc(PIPE_DEF_BUFFERS, sizeof(pipe_buffer))
                    |       |               +-- init mutex, waitqueues
                    |       |-- alloc_file_pseudo(inode, ..., &pipefifo_fops)  --> read fd
                    |       +-- alloc_file_pseudo(inode, ..., &pipefifo_fops)  --> write fd
                    +-- copy_to_user(pipefd, fds, sizeof(fds))
```

> `fs/pipe.c`: `do_pipe2()`, `create_pipe_files()`, `alloc_pipe_info()`

### 5.2 `write()` Path

```
write(fd, buf, count)
    +-- ksys_write()
            +-- vfs_write()
                    +-- pipe_write()   [fs/pipe.c]
                            |
                            |-- lock_pipe_fast(pipe) / mutex_lock(&pipe->mutex)
                            |-- loop while bytes_to_write > 0:
                            |     |-- if pipe_full(pipe->head, pipe->tail, pipe->max_usage):
                            |     |       pipe_wait_writable(pipe)  <- blocks on wr_wait
                            |     |-- grab free slot: buf = &pipe->bufs[head & mask]
                            |     |-- if buf->page == NULL: alloc_page(GFP_HIGHUSER)
                            |     |-- copy_page_from_iter(buf->page, offset, bytes, from)
                            |     |       +-- copy_from_user() if iter is iovec
                            |     |-- buf->offset = offset; buf->len = bytes;
                            |     +-- pipe->head++
                            |-- wake_up_interruptible_sync_poll(&pipe->rd_wait, EPOLLIN|EPOLLRDNORM)
                            +-- mutex_unlock(&pipe->mutex)
```

Atomicity for `count <= PIPE_BUF`:
- If `count` bytes fit in the remaining space of current page, done in one copy.
- If not and pipe is full, sleep — wake up only when enough space for `count` bytes exists.

### 5.3 `read()` Path

```
read(fd, buf, count)
    +-- ksys_read()
            +-- vfs_read()
                    +-- pipe_read()    [fs/pipe.c]
                            |
                            |-- mutex_lock(&pipe->mutex)
                            |-- loop while bytes_wanted > 0:
                            |     |-- if pipe_empty(pipe->head, pipe->tail):
                            |     |       if !pipe->writers: break (EOF)
                            |     |       pipe_wait_readable(pipe) <- blocks on rd_wait
                            |     |-- buf = &pipe->bufs[tail & mask]
                            |     |-- bytes = min(buf->len, bytes_wanted)
                            |     |-- copy_page_to_iter(buf->page, buf->offset, bytes, to)
                            |     |-- buf->offset += bytes; buf->len -= bytes
                            |     +-- if buf->len == 0:
                            |               pipe_buf_release(pipe, buf)  <- releases page
                            |               pipe->tail++
                            |-- wake_up_interruptible_sync_poll(&pipe->wr_wait, EPOLLOUT|EPOLLWRNORM)
                            +-- mutex_unlock(&pipe->mutex)
```

### 5.4 EOF Detection

```
Reader gets EOF (read returns 0) when:
  pipe_empty(head, tail) == true  AND  pipe->writers == 0

Writer gets EPIPE / SIGPIPE when:
  pipe->readers == 0  (no reader end open)
```

### 5.5 `poll()` / `select()` / `epoll` on Pipes

Pipes implement `pipe_poll()`:

```c
/* fs/pipe.c */
static __poll_t pipe_poll(struct file *filp, poll_table *wait)
{
    struct pipe_inode_info *pipe = filp->private_data;
    __poll_t mask = 0;

    poll_wait(filp, &pipe->rd_wait, wait);
    poll_wait(filp, &pipe->wr_wait, wait);

    if (!pipe_empty(pipe->head, pipe->tail))
        mask |= EPOLLIN | EPOLLRDNORM;
    if (!pipe_full(pipe->head, pipe->tail, pipe->max_usage))
        mask |= EPOLLOUT | EPOLLWRNORM;
    if (!pipe->writers)
        mask |= EPOLLHUP;
    if (!pipe->readers)
        mask |= EPOLLERR;

    return mask;
}
```

`epoll` works correctly on both ends. `EPOLLHUP` is set on the read end when all write fds are closed (EOF incoming).

---

## 6. Pipe Capacity, Limits & Tunables

### 6.1 Default Capacity

```
Default pipe ring_size: 16 pages = 16 x 4096 = 65536 bytes (64 KiB)

Defined in: include/linux/pipe_fs_i.h
  #define PIPE_DEF_BUFFERS   16
  #define PIPE_MAX_SIZE      (1048576)   /* 1 MiB -- sysctl default */
```

### 6.2 System-Wide Limits

```bash
# Maximum single pipe size (bytes)
cat /proc/sys/fs/pipe-max-size          # default: 1048576 (1 MiB)

# Maximum total pipe memory across all unprivileged users
cat /proc/sys/fs/pipe-user-pages-hard  # default: 0 (disabled)
cat /proc/sys/fs/pipe-user-pages-soft  # default: 16384 pages = 64 MiB
```

```
sysctl knobs:
  fs.pipe-max-size          -- upper bound for F_SETPIPE_SZ
  fs.pipe-user-pages-soft   -- soft per-user limit; exceed -> pipe size capped at 1 page
  fs.pipe-user-pages-hard   -- hard per-user limit; exceed -> EPERM
```

> Implementation: `fs/pipe.c: pipe_set_size()`, `account_pipe_buffers()`

### 6.3 Resizing a Pipe (`F_SETPIPE_SZ`)

```c
#include <fcntl.h>

/* Get current capacity */
int cap = fcntl(pfd[0], F_GETPIPE_SZ);

/* Set new capacity (rounded up to nearest page multiple) */
int ret = fcntl(pfd[1], F_SETPIPE_SZ, 1024 * 1024);  /* 1 MiB */
if (ret < 0)
    perror("F_SETPIPE_SZ");  /* EPERM if > pipe-max-size and unprivileged */
```

Rules:
- `CAP_SYS_RESOURCE` required to set size > `fs.pipe-max-size`.
- New `ring_size` = smallest power of 2 that holds the requested bytes.
- Cannot shrink below current data occupancy.
- Can be set on either end (read or write fd).

```bash
# Check a process's pipe sizes via /proc
ls -la /proc/<pid>/fd/
cat /proc/<pid>/fdinfo/<fd>    # shows pipe-related info
```

### 6.4 `/proc/sys/fs/` Sysctl Table

```
/proc/sys/fs/
|-- pipe-max-size           -> max size of a single pipe (bytes)
|-- pipe-user-pages-hard    -> hard limit: pages per user across all pipes
|-- pipe-user-pages-soft    -> soft limit: pages per user across all pipes
+-- nr_open                 -> max open fds per process (affects pipe fds)
```

---

## 7. Pipe Flags & Modes

### 7.1 `O_NONBLOCK`

```c
/* Set at creation */
pipe2(pfd, O_NONBLOCK);

/* Or set later */
int flags = fcntl(pfd[0], F_GETFL);
fcntl(pfd[0], F_SETFL, flags | O_NONBLOCK);
```

Behavior with `O_NONBLOCK`:

| Operation | Condition | Result |
|---|---|---|
| `read()` | Pipe empty, writers exist | Returns `-1`, `errno = EAGAIN` |
| `read()` | Pipe empty, no writers | Returns `0` (EOF) |
| `write()` | Pipe full | Returns `-1`, `errno = EAGAIN` |
| `write(n <= PIPE_BUF)` | Partial space | Returns `-1`, `errno = EAGAIN` (atomic) |
| `write(n > PIPE_BUF)` | Partial space | Returns bytes written so far |

### 7.2 `O_DIRECT` — Packet Mode (Linux 3.4+)

```c
pipe2(pfd, O_DIRECT);
```

In packet mode (also called "message mode"), each `write()` creates a discrete, separately-readable message. A `read()` either returns exactly one message or `ENOBUFS` if the buffer is too small.

```c
/* Writer */
write(pfd[1], "hello", 5);   /* message 1 */
write(pfd[1], "world", 5);   /* message 2 */

/* Reader with O_DIRECT */
char buf[64];
read(pfd[0], buf, 64);   /* reads "hello" -- 5 bytes */
read(pfd[0], buf, 64);   /* reads "world" -- 5 bytes */

/* Without O_DIRECT, read() could return "helloworld" in one call */
```

Implemented via `PIPE_BUF_FLAG_PACKET` on each `pipe_buffer`.

### 7.3 `O_CLOEXEC`

```c
pipe2(pfd, O_CLOEXEC);
```

Sets `FD_CLOEXEC` on both ends atomically. The file descriptors are automatically closed on `execve()`. This avoids the TOCTOU race of:
```c
pipe(pfd);
fcntl(pfd[0], F_SETFD, FD_CLOEXEC);   /* <- race window */
fcntl(pfd[1], F_SETFD, FD_CLOEXEC);
```

**Always use `O_CLOEXEC` in new code.**

---

## 8. Zero-Copy: `splice()`, `tee()`, `vmsplice()`

These system calls move data through pipes **without copying between kernel and userspace**. Data moves as page references.

### 8.1 `splice(2)` — Move Data Between fd and Pipe

```c
#include <fcntl.h>

ssize_t splice(int fd_in,  loff_t *off_in,
               int fd_out, loff_t *off_out,
               size_t len, unsigned int flags);
```

Constraint: **at least one of `fd_in` or `fd_out` must be a pipe**.

```
Case 1: file -> pipe
  splice(file_fd, &off, pipe_wr, NULL, len, flags)
  Page cache pages are linked into pipe_buffer -- zero copy.

Case 2: pipe -> file / socket
  splice(pipe_rd, NULL, sock_fd, NULL, len, flags)
  Pages sent from pipe directly to socket send buffer.

Case 3: pipe -> pipe
  splice(pipe_rd, NULL, pipe_wr, NULL, len, flags)
  Moves pipe_buffer entries (page references) between pipes.
```

```c
/* Efficient file copy using splice + pipe */
int pipe_copy(int src_fd, int dst_fd, size_t size)
{
    int pfd[2];
    ssize_t n, written;

    if (pipe2(pfd, O_CLOEXEC) < 0)
        return -1;

    while (size > 0) {
        n = splice(src_fd, NULL, pfd[1], NULL,
                   min(size, (size_t)65536), SPLICE_F_MOVE);
        if (n <= 0) break;

        written = splice(pfd[0], NULL, dst_fd, NULL, n, SPLICE_F_MOVE);
        if (written != n) break;

        size -= n;
    }
    close(pfd[0]); close(pfd[1]);
    return size == 0 ? 0 : -1;
}
```

Flags for `splice()`:
| Flag | Meaning |
|---|---|
| `SPLICE_F_MOVE` | Move pages rather than copy (hint; kernel may ignore) |
| `SPLICE_F_NONBLOCK` | Don't block on pipe I/O (still may block on fd) |
| `SPLICE_F_MORE` | Hint that more data follows (like `MSG_MORE` for sockets) |

### 8.2 `tee(2)` — Duplicate Pipe Data (Read Without Consuming)

```c
ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags);
```

Both `fd_in` and `fd_out` must be pipes. `tee()` copies page references from the read end of `fd_in` into `fd_out` **without consuming** the data from `fd_in`. This allows a pipe to be "listened to" by multiple consumers.

```
                     +---------------------------> logger_pipe_wr
                     |
source_fd ---> tee --+  (data stays in source_pipe)
                     |
                     +---> source_pipe (readable again)
                                 |
                             consumer
```

```c
/* tee: duplicate stdin to a log file while passing through */
int log_fd = open("log.txt", O_WRONLY|O_CREAT|O_TRUNC, 0644);
int pfd[2];
pipe2(pfd, O_CLOEXEC);

/* fork logger */
if (fork() == 0) {
    close(pfd[1]);
    while (1) {
        ssize_t n = tee(STDIN_FILENO, pfd[1], INT_MAX, SPLICE_F_NONBLOCK);
        if (n <= 0) break;
        splice(pfd[0], NULL, log_fd, NULL, n, 0);
    }
    return 0;
}
/* main: data still readable from STDIN_FILENO */
splice(STDIN_FILENO, NULL, STDOUT_FILENO, NULL, INT_MAX, 0);
```

### 8.3 `vmsplice(2)` — Userspace Memory into Pipe

```c
#include <sys/uio.h>
ssize_t vmsplice(int fd, const struct iovec *iov,
                 unsigned long nr_segs, unsigned int flags);
```

`fd` must be the **write end** of a pipe. Moves userspace pages into the pipe without copying. After `vmsplice()`, the pages are owned by the pipe — **do not modify the memory** until the pipe is drained.

```c
char buf[4096] __attribute__((aligned(4096)));
struct iovec iov = { .iov_base = buf, .iov_len = 4096 };

/* Fill buf with data */
memset(buf, 'A', 4096);

/* Zero-copy push into pipe */
vmsplice(pfd[1], &iov, 1, SPLICE_F_GIFT);
/* SPLICE_F_GIFT: gift the pages to the kernel; do NOT access buf after this */
```

### 8.4 Zero-Copy Data Flow Architecture

```
Disk / NIC
    |
    v
Page Cache (struct page)
    |
    |  splice(file, pipe)
    v
pipe_buffer[] ---- page ref ----> same struct page (NO COPY)
    |
    |  splice(pipe, socket)
    v
Socket send buffer ---- page ref ----> same struct page (NO COPY)
    |
    v
NIC DMA

Result: 0 user-kernel copies, 0 kernel-kernel copies
        Only page frame references moved.
```

---

## 9. Shell Pipelines — Deep Dive

### 9.1 Shell Pipeline Execution Model

When bash processes `cmd1 | cmd2 | cmd3`:

```
bash                          Pipeline Group (PGID = cmd1's PID)
 |
 |-- pipe(p1)  -------------------------------------------------------+
 |-- pipe(p2)  -------------------------------------------+           |
 |                                                         |           |
 |-- fork -> cmd1:                                         |           |
 |     dup2(p1[1], STDOUT) -- cmd1 stdout -> p1 write end-+           |
 |     close(p1[0], p1[1], p2[0], p2[1])                             |
 |     exec("cmd1")                                                    |
 |                                                                     |
 |-- fork -> cmd2:                                                     |
 |     dup2(p1[0], STDIN)  -- cmd2 stdin  <- p1 read end  -----------+
 |     dup2(p2[1], STDOUT) -- cmd2 stdout -> p2 write end ---+
 |     close(p1[0], p1[1], p2[0], p2[1])                    |
 |     exec("cmd2")                                          |
 |                                                           |
 +-- fork -> cmd3:                                           |
       dup2(p2[0], STDIN)  -- cmd3 stdin  <- p2 read end ---+
       close(p1[0], p1[1], p2[0], p2[1])
       exec("cmd3")

bash: close all pipe fds, waitpid() for all three.
```

### 9.2 Pipeline Return Code

In bash, `$?` after a pipeline equals **the exit code of the last command**. To get all exit codes:

```bash
# Get all statuses with PIPESTATUS
ls nonexistent | sort | wc -l
echo "${PIPESTATUS[@]}"    # e.g., "2 0 0"

# Enable pipefail -- pipeline fails if any command fails
set -o pipefail
cat /dev/null | grep "foo" | wc -l
echo $?   # 1 (grep failed) instead of 0
```

### 9.3 `|&` — stderr + stdout

```bash
# bash 4.0+: pipe both stdout and stderr
cmd1 |& cmd2
# Equivalent to:
cmd1 2>&1 | cmd2
```

Kernel perspective: this is just `dup2(pfd[1], STDERR_FILENO)` in addition to `dup2(pfd[1], STDOUT_FILENO)` before `exec()`.

### 9.4 Process Substitution

```bash
diff <(sort file1) <(sort file2)
```

Bash creates **named pipes** (FIFOs) or uses `/dev/fd/N` (which uses `O_RDONLY` open of a pipe fd passed via `/proc/self/fd/`). The substitution `<(cmd)` expands to `/dev/fd/63` (or similar), which is the read end of a pipe fed by `cmd` running asynchronously.

```bash
# See what bash creates:
ls -la /proc/self/fd/ in a subshell during process substitution
bash -c 'ls -la /proc/self/fd/ > >(cat)'
# You'll see entries like: fd/63 -> pipe:[12345]
```

### 9.5 Here-Strings and Here-Docs

```bash
grep "pattern" <<< "search string"
```

Internally, bash writes the string into a pipe and redirects stdin from the pipe's read end — same mechanism, just automated.

```bash
wc -l << 'EOF'
line one
line two
EOF
```

Here-docs: bash writes the heredoc to a **temporary file** (not a pipe) in older implementations, or to a pipe in newer implementations. You can verify:

```bash
strace -e trace=pipe,open,write bash -c 'cat << EOF
hello
EOF' 2>&1 | head -30
```

### 9.6 Subshell and Pipe Variable Scope Trap

```bash
count=0
echo "a b c" | while read word; do
    count=$((count + 1))    # runs in subshell!
done
echo $count   # prints 0, not 3!
```

The right side of a pipe runs in a subshell — variable changes are lost. Fix:

```bash
# bash 4.2+: lastpipe option (right side runs in current shell)
shopt -s lastpipe
count=0
echo "a b c" | while read word; do count=$((count+1)); done
echo $count   # 3

# Or use process substitution (left side):
while read word; do count=$((count+1)); done < <(echo "a b c")
```

---

## 10. Signals: SIGPIPE & EPIPE

### 10.1 Mechanics

```
Writer side:

  write() on pipe with no reader fds open
       |
       v
  pipe_write() detects pipe->readers == 0
       |
       |-- send_signal(current, SIGPIPE, ...)   <- deliver to writer
       +-- return -EPIPE                         <- errno = EPIPE

Default disposition of SIGPIPE: terminate process.
```

### 10.2 Handling SIGPIPE

```c
#include <signal.h>

/* Option 1: Ignore SIGPIPE, check write() return value */
signal(SIGPIPE, SIG_IGN);
/* write() will return -1 with errno == EPIPE */

/* Option 2: Custom handler */
void sigpipe_handler(int sig)
{
    /* log, set flag, etc. */
    write(STDERR_FILENO, "pipe broken\n", 12);
}
signal(SIGPIPE, sigpipe_handler);

/* Option 3: Use MSG_NOSIGNAL for socket-like pipes */
send(sockfd, buf, len, MSG_NOSIGNAL);
/* For pipes: use write() + SIG_IGN */
```

### 10.3 Common SIGPIPE Scenarios

```bash
# head closes its stdin after reading 10 lines;
# yes gets SIGPIPE when it tries to write more
yes | head -10

# curl's pipe to grep -- curl gets SIGPIPE when grep exits
curl -s https://example.com | grep "title" | head -1
```

### 10.4 `EPIPE` vs `SIGPIPE`

| | `SIGPIPE` | `EPIPE` |
|---|---|---|
| Type | Signal (async) | `errno` value (synchronous) |
| When | Delivered before `write()` returns | `write()` returns `-1`, `errno=EPIPE` |
| Suppress | `SIG_IGN` or custom handler | Automatically if `SIGPIPE` is ignored |
| Note | Default action kills process | Ignored if SIGPIPE is handled |

---

## 11. Bidirectional & Full-Duplex Pipes

### 11.1 Why Anonymous Pipes are Half-Duplex

A single `pipe()` call creates one unidirectional channel. For bidirectional communication, two pipes are needed:

```
Process A                              Process B
  pfd1[1] ----------------------------------------> pfd1[0]   (A->B)
  pfd2[0] <---------------------------------------- pfd2[1]   (B->A)
```

```c
int to_child[2], from_child[2];
pipe2(to_child, O_CLOEXEC);
pipe2(from_child, O_CLOEXEC);

if (fork() == 0) {
    dup2(to_child[0],   STDIN_FILENO);
    dup2(from_child[1], STDOUT_FILENO);
    close(to_child[0]); close(to_child[1]);
    close(from_child[0]); close(from_child[1]);
    execlp("bc", "bc", NULL);
}

close(to_child[0]); close(from_child[1]);
/* Parent: write to to_child[1], read from from_child[0] */
```

**Deadlock hazard**: Both parent and child doing synchronous read/write can deadlock if both block waiting for the other. Use `epoll` + non-blocking I/O, or separate threads.

### 11.2 `socketpair()` — True Bidirectional Channel

```c
#include <sys/socket.h>
int sv[2];
socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
/* sv[0] and sv[1] are both read-write */
```

`socketpair()` with `AF_UNIX` + `SOCK_STREAM` is semantically equivalent to two pipes but uses `unix_stream_ops` internally. It supports `sendmsg()`/`recvmsg()` with `SCM_RIGHTS` (fd passing) and `SCM_CREDENTIALS`.

```
socketpair vs pipe:
  pipe:        unidirectional, lighter, faster for one-way
  socketpair:  bidirectional, supports ancillary data (fd passing)
               uses struct unix_sock, slightly heavier
```

### 11.3 File Descriptor Passing Over Pipes/Sockets

FD passing is possible only over `AF_UNIX` sockets (not pipes). It allows transferring open file descriptors between unrelated processes:

```c
/* Sender */
struct msghdr   msg  = {};
struct cmsghdr *cmsg;
char            buf[CMSG_SPACE(sizeof(int))];
int             fd_to_send = open("/tmp/test", O_RDONLY);

msg.msg_control    = buf;
msg.msg_controllen = sizeof(buf);
cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type  = SCM_RIGHTS;
cmsg->cmsg_len   = CMSG_LEN(sizeof(int));
*(int *)CMSG_DATA(cmsg) = fd_to_send;

sendmsg(sv[0], &msg, 0);

/* Receiver gets a new fd in its table pointing to the same file */
```

---

## 12. Pipe vs. Other IPC Mechanisms

```
IPC Comparison Table:
+-----------------+----------+----------+----------+---------+----------+----------+
| Mechanism       | Persist  | Kernel   | Network  | Msg     | FD Pass  | Perf     |
|                 | w/o proc | Buffer   | Trans.   | Bounds  |          |          |
+-----------------+----------+----------+----------+---------+----------+----------+
| Anon Pipe       | No       | 64 KiB   | No       | No      | No       | *****    |
| Named FIFO      | Yes(name)| 64 KiB   | No       | No      | No       | *****    |
| AF_UNIX Stream  | Yes(path)| SO_SNDBUF| No       | No      | Yes      | ****     |
| AF_UNIX Dgram   | Yes(path)| SO_SNDBUF| No       | Yes     | Yes      | ****     |
| POSIX MQ        | Optional | mq_attr  | No       | Yes     | No       | ****     |
| SysV MsgQ       | Yes      | MSGMNB   | No       | Yes     | No       | ***      |
| Shared Memory   | Yes      | -        | No       | No      | No       | *****    |
| TCP Socket      | No       | SO_SNDBUF| Yes      | No      | No       | ***      |
| eventfd         | No       | 64-bit   | No       | No      | No       | *****    |
+-----------------+----------+----------+----------+---------+----------+----------+
```

### 12.1 Pipe vs. Unix Domain Socket

```
Use pipe when:
  - Simple parent->child or producer->consumer
  - No need for message boundaries
  - Maximum throughput, minimum overhead
  - No fd passing needed

Use AF_UNIX socket when:
  - Bidirectional without two pipes
  - Need fd passing (SCM_RIGHTS)
  - Need credential passing (SCM_CREDENTIALS)
  - Unrelated processes (no shared parent)
  - Need SOCK_DGRAM message semantics
```

### 12.2 Pipe vs. POSIX Message Queue

```bash
# Create a message queue
mq_open("/myqueue", O_CREAT|O_RDWR, 0600, &attr);
```

```
Use POSIX MQ when:
  - Strict message boundaries required
  - Priority-ordered delivery needed (mq_send with priority)
  - Persistence across process restarts (optional)
  - Multiple unrelated producers/consumers
  - mq_notify() for async notification

pipe advantage: ~2x faster for streaming data, no message overhead
MQ advantage:   message framing, priorities, mq_timedsend/receive
```

---

## 13. Advanced: Pipe Tricks & Patterns

### 13.1 Self-pipe Trick (Signal-safe `select`/`epoll` Wakeup)

Classic technique to make signals work with `select()`/`epoll_wait()`:

```c
int self_pipe[2];
pipe2(self_pipe, O_NONBLOCK | O_CLOEXEC);

/* Signal handler: write 1 byte to wake up epoll */
void sigchld_handler(int sig)
{
    char byte = 'x';
    write(self_pipe[1], &byte, 1);   /* async-signal-safe */
}
signal(SIGCHLD, sigchld_handler);

/* Main loop: add self_pipe[0] to epoll */
epoll_ctl(epfd, EPOLL_CTL_ADD, self_pipe[0], &ev);

/* On epoll event for self_pipe[0]: */
char buf[32];
read(self_pipe[0], buf, sizeof(buf));   /* drain */
/* Now safely call waitpid(), etc. */
```

Linux 2.6.27+ provides `signalfd(2)` as a cleaner alternative, but the self-pipe trick works on all Unix systems.

### 13.2 `popen()` / `pclose()` — Pipe to a Shell Command

```c
#include <stdio.h>

FILE *fp = popen("ls -la /proc", "r");   /* "r" or "w" */
char line[256];
while (fgets(line, sizeof(line), fp))
    fputs(line, stdout);
int status = pclose(fp);   /* returns waitpid() status */
```

`popen()` internally: `pipe()` + `fork()` + `dup2()` + `exec("/bin/sh", "-c", cmd)`. Avoid in kernel modules and security-sensitive code (shell injection risk).

### 13.3 Pipe as a Semaphore / Mutex

```c
/* Writer "P" operation: take token */
char token;
read(sem_pipe[0], &token, 1);   /* blocks until token available */

/* ... critical section ... */

/* Reader "V" operation: release token */
write(sem_pipe[1], "x", 1);    /* put token back */
```

The atomic PIPE_BUF guarantee makes single-byte writes/reads race-free for semaphore use. Pre-fill with N tokens for a counting semaphore.

### 13.4 Pipe as Event Notification Channel

```c
/* Notifier */
write(event_pipe[1], "\x01", 1);

/* Waiter -- using epoll */
struct epoll_event ev;
epoll_wait(epfd, &ev, 1, -1);
/* Drain */
char buf;
read(event_pipe[0], &buf, 1);
```

`eventfd(2)` is more efficient for pure notification (no data), but pipes work everywhere and carry data.

### 13.5 Multi-Reader Fan-Out with `tee()`

```
                                +--> reader1
source_data ---> source_pipe ---+
                      |         +--> tee_pipe --> reader2
                      |
                      +--> (data still available for reader1)
```

```c
/* Fan data from one pipe to N pipes using tee() */
int src[2], dst1[2], dst2[2];
pipe2(src, O_CLOEXEC);
pipe2(dst1, O_CLOEXEC);
pipe2(dst2, O_CLOEXEC);

/* Demultiplexer process */
while (1) {
    ssize_t n = tee(src[0], dst1[1], 65536, 0);   /* copy to dst1 */
    if (n <= 0) break;
    splice(src[0], NULL, dst2[1], NULL, n, 0);     /* move to dst2 */
}
```

### 13.6 Bash Pipeline Tricks

```bash
# Parallel gzip compression using tee + fifos
mkfifo /tmp/f1 /tmp/f2
tee /tmp/f1 /tmp/f2 < bigfile > /dev/null &
gzip < /tmp/f1 > part1.gz &
gzip < /tmp/f2 > part2.gz
wait

# Transparent logging of a pipeline
cmd1 | tee >(logger -t myprog) | cmd2

# Time only the first command
{ time cmd1; } 2>&1 | cmd2

# Coprocess (bash 4.0+) -- bidirectional pipe to a background process
coproc BC { bc; }
echo "3 + 4" >&"${BC[1]}"
read result <&"${BC[0]}"
echo $result   # 7
```

---

## 14. Networking Stack & Pipes

### 14.1 Pipe + Socket: `sendfile()` and `splice()`

The networking stack integrates with pipes primarily through `splice()`. The canonical "zero-copy HTTP server" pattern:

```c
/* Serve file over TCP socket using splice -- zero copy */
int file_fd = open(path, O_RDONLY);
int pipe_fds[2];
pipe2(pipe_fds, O_CLOEXEC);
off_t offset = 0;
size_t file_size = stat_result.st_size;

while (file_size > 0) {
    /* Page cache -> pipe (zero copy) */
    ssize_t n = splice(file_fd, &offset, pipe_fds[1], NULL,
                       min(file_size, (size_t)65536),
                       SPLICE_F_MOVE | SPLICE_F_MORE);
    /* pipe -> socket (zero copy) */
    ssize_t sent = splice(pipe_fds[0], NULL, client_sock, NULL,
                          n, SPLICE_F_MOVE | SPLICE_F_MORE);
    file_size -= sent;
}
```

Data path:
```
Disk --DMA---> Page Cache
                  |
         splice(file->pipe)
                  |
              pipe_buffer[] (page refs)
                  |
         splice(pipe->socket)
                  |
              sk_buff (page frags pointing to same pages)
                  |
              NIC DMA ---> Network
```

### 14.2 `pipe()` in Netfilter / eBPF

eBPF programs can interact with pipes indirectly via `bpf_redirect_map()` with `DEVMAP` and through `BPF_MAP_TYPE_RINGBUF` (kernel ring buffer — conceptually similar to a pipe). The actual `pipe_inode_info` is not directly accessible from eBPF.

For inter-process data flows monitored by eBPF:

```c
/* bpftrace: trace all pipe writes */
tracepoint:syscalls:sys_enter_write
/args->fd > 2/  /* not stdin/stdout/stderr */
{
    /* Check if fd is a pipe via fdinfo */
    printf("PID %d write(%d, %d bytes)\n", pid, args->fd, args->count);
}
```

```bash
# ftrace: trace pipe_write
echo 'pipe_write' > /sys/kernel/debug/tracing/set_ftrace_filter
echo 'function' > /sys/kernel/debug/tracing/current_tracer
cat /sys/kernel/debug/tracing/trace
```

### 14.3 XDP and Pipes

XDP (eXpress Data Path) operates before the socket layer and has no direct pipe interaction. However, `AF_XDP` sockets feed data via a ring-buffer mechanism that is architecturally analogous to pipes:

```
NIC ---> XDP ---> AF_XDP socket (UMEM fill/completion rings)
                      |
                 userspace polling
                      |
                 can write to pipes for further processing
```

### 14.4 Netlink + Pipes Pattern

```bash
# Monitor routing table changes, pipe through processing
ip monitor route | while read line; do
    echo "$line" | grep -E 'add|del'
done

# strace shows:
# socket(AF_NETLINK, SOCK_RAW|SOCK_CLOEXEC, NETLINK_ROUTE) = 5
# pipe2([6, 7], O_CLOEXEC) = 0   <- bash creates pipeline pipe
```

---

## 15. Pipes in Containers & Cloud

### 15.1 Pipe Namespaces

Pipes are **not** namespaced by Linux namespaces. They live in the filesystem namespace only via FIFOs. Anonymous pipes are referenced purely by file descriptors, which are per-process.

```
Linux Namespace effects on pipes:
  PID namespace:    No effect on pipe existence; affects PIDs in /proc
  Mount namespace:  FIFOs in a bind mount are isolated per namespace
  Network ns:       No effect
  User ns:          Affects pipe ownership (uid/gid mapping)
  IPC ns:          Affects SysV/POSIX IPC, NOT pipes
  UTS/time ns:     No effect
```

### 15.2 Pipes in Containers (Docker / LXC)

Inside a container, pipe behavior is identical to the host. Pipes cross container boundaries only via:

1. **Shared bind mounts**: A FIFO in a shared volume is accessible from both host and container.
2. **`docker exec` stdin/stdout**: Docker connects to the container's PID 1 process via pipes and ptrace-based fd passing.

```bash
# Pipe from host into running container
echo "data" | docker exec -i mycontainer /bin/cat

# Internally Docker creates a pipe between:
#   docker CLI (host) --pipe---> dockerd --Unix socket---> containerd
#   containerd ---> runc ---> container stdin pipe
```

### 15.3 Kubernetes: Pod Logs and `kubectl exec`

`kubectl logs` / `kubectl exec -i` uses HTTP/2 streaming, but within each node and pod, the mechanism is:

```
kubelet
  |
  +-- CRI (containerd/crio)
          |
          +-- runc container
                  |
                  |-- stdin:  pipe from kubelet-side goroutine
                  |-- stdout: pipe to kubelet-side goroutine
                  +-- stderr: pipe to kubelet-side goroutine
                          |
                   streamed over HTTP/2 to kubectl
```

```bash
# Check pipe fds in a Kubernetes container
kubectl exec -it mypod -- ls -la /proc/1/fd/
# 0 -> pipe:[12345]   (stdin)
# 1 -> pipe:[12346]   (stdout)
# 2 -> pipe:[12347]   (stderr)
```

### 15.4 cgroups and Pipe Memory

Pipe buffers are allocated from kernel memory (not anonymous user memory). They are accounted under `memory.kmem.usage_in_bytes` in cgroups v1, or `memory.current` (kmem included) in cgroups v2.

```bash
# Check cgroup v2 pipe memory contribution
cat /sys/fs/cgroup/<slice>/memory.stat | grep anon
# pipe buffers show up under "kernel_stack" or "slab" categories

# Limit pipe-induced memory pressure per cgroup
echo "200M" > /sys/fs/cgroup/mygroup/memory.max
```

Implication: A runaway pipe producer (writing faster than consumer reads) can exhaust cgroup memory limits.

### 15.5 Cloud-Native Patterns Using Pipes

#### Log Aggregation Sidecar Pattern

```
Application Container          Logging Sidecar Container
      |                              |
  stdout/stderr ---------------> shared emptyDir volume FIFO
   (via pipe)                        |
                                 fluentd/vector reads FIFO
                                      |
                              ---> Cloud Logging (GCP/AWS/Azure)
```

```yaml
# Kubernetes: shared volume for FIFO-based log forwarding
volumes:
- name: log-pipe
  emptyDir: {}
containers:
- name: app
  volumeMounts:
  - name: log-pipe
    mountPath: /var/log/pipe
  command: ["sh", "-c", "mkfifo /var/log/pipe/out; app > /var/log/pipe/out"]
- name: log-sidecar
  volumeMounts:
  - name: log-pipe
    mountPath: /var/log/pipe
  command: ["sh", "-c", "cat /var/log/pipe/out | fluent-bit ..."]
```

#### AWS / GCP CLI Pipe Patterns

```bash
# Stream S3 data through local processing without temp files
aws s3 cp s3://bucket/large.csv.gz - | \
    gzip -dc | \
    awk -F',' '{print $1, $3}' | \
    sort -k2 -rn | \
    head -100 | \
    aws s3 cp - s3://bucket/result.txt

# GCP: stream BigQuery results
bq query --format=csv 'SELECT * FROM dataset.table' | \
    python3 process.py | \
    gsutil cp - gs://bucket/output.jsonl
```

### 15.6 Pipe Limits in Containerized Environments

Key limits to set in production:

```bash
# /proc/sys/fs/pipe-max-size -- writable by root or CAP_SYS_RESOURCE
# In Kubernetes, apply via sysctl:
# spec.securityContext.sysctls (namespaced sysctls only)
# pipe-max-size is NOT a namespaced sysctl -> must be set on node level

# Node-level tuning (applies to all containers on node):
sysctl -w fs.pipe-max-size=2097152        # 2 MiB max pipe
sysctl -w fs.pipe-user-pages-soft=65536  # 256 MiB total per user
```

---

## 16. Security: Pipe-Related Attacks & Mitigations

### 16.1 CVE-2022-0847 — Dirty Pipe

**Affected**: Linux 5.8 - 5.16.11, 5.15.25, 5.10.102  
**Discovery**: Max Kellermann (February 2022)  
**Impact**: Unprivileged user can overwrite **read-only** page-cache pages (including SUID binaries)

Root cause: `pipe_buffer.flags` was not zeroed when a pipe buffer was reused after a partial merge. The `PIPE_BUF_FLAG_CAN_MERGE` flag persisted, allowing subsequent `splice()` + `write()` to write into page-cache pages at arbitrary offsets.

```c
/* Dirty Pipe exploit sketch (conceptual) */
int pfd[2];
pipe(pfd);

/* 1. Fill pipe with dummy data to set PIPE_BUF_FLAG_CAN_MERGE */
for (int i = 0; i < 16; i++)
    write(pfd[1], "x", 1);

/* 2. Drain all but last buffer */
for (int i = 0; i < 16; i++) {
    char c;
    read(pfd[0], &c, 1);
}

/* 3. splice from target file (e.g., /etc/passwd) into pipe */
int tfd = open("/etc/passwd", O_RDONLY);
splice(tfd, &offset, pfd[1], NULL, 1, 0);

/* 4. write() now merges into the page-cache page! */
write(pfd[1], "evil_data", 9);  /* overwrites /etc/passwd in page cache */
```

**Fix** (`fs/pipe.c`):
```c
/* v5.16.11 fix: zero flags on pipe_buf release */
static void anon_pipe_buf_release(struct pipe_inode_info *pipe,
                                   struct pipe_buffer *buf)
{
    struct page *page = buf->page;
    buf->flags = 0;   /* <- critical fix: clear PIPE_BUF_FLAG_CAN_MERGE */
    ...
}
```

Also added: initialization of `pipe_buffer.flags = 0` in `pipe_write()` when allocating new buffer slot.

### 16.2 Pipe-Based Privilege Escalation Patterns

```
TOCTOU via FIFO:
  If a privileged program opens a path that an attacker can replace with a FIFO,
  the program's read will block waiting for a writer (attacker-controlled).

Mitigation:
  - Use O_NOFOLLOW to avoid symlink races
  - Use openat(dirfd, name, O_NOFOLLOW) with a trusted dirfd
  - Privileged code should not open paths provided by untrusted users
```

### 16.3 Pipe Exhaustion (DoS)

An unprivileged user can create many large pipes to exhaust kernel memory:

```c
/* DoS: create many pipes with maximum size */
int pfd[2];
pipe(pfd);
fcntl(pfd[1], F_SETPIPE_SZ, 1024*1024);  /* 1 MiB per pipe */
/* repeat 1000 times -> 1 GiB of kernel memory */
```

Mitigations:
- `fs.pipe-user-pages-soft` and `fs.pipe-user-pages-hard` sysctls.
- cgroup memory limits (counts kernel memory).
- Container resource limits (`ulimit -n` limits fd count, indirectly limits pipes).

### 16.4 Seccomp and Pipes

```c
/* seccomp: allow pipe2 but restrict flags */
/* BPF filter example using libseccomp */
scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
/* Block O_DIRECT (packet mode) in pipe2 */
seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(pipe2),
                 1, SCMP_A1(SCMP_CMP_MASKED_EQ, O_DIRECT, O_DIRECT));
seccomp_load(ctx);
```

### 16.5 LSM Hooks for Pipes

```c
/* security/security.c -- LSM hooks called on pipe operations */
int security_inode_create(...)   /* FIFO creation */
int security_file_permission(...) /* pipe read/write */

/* SELinux pipe policy example */
/* allow confined_t pipe_t:fifo_file { read write }; */
```

AppArmor pipe mediation:
```
# AppArmor profile
/tmp/myfifo rw,       # allow read/write on named pipe
```

---

## 17. Debugging & Tracing Pipes

### 17.1 `strace` — Observe Pipe Syscalls

```bash
# Trace pipe creation and I/O in a pipeline
strace -e trace=pipe2,read,write,close -f bash -c 'echo hello | cat'

# Output example:
# pipe2([3, 4], O_CLOEXEC)      = 0
# [pid 12345] write(4, "hello\n", 6) = 6
# [pid 12346] read(3, "hello\n", 4096) = 6
```

### 17.2 `lsof` — List Open Pipe FDs

```bash
lsof -p <pid>          # show all open files including pipes
lsof | grep FIFO       # find all open FIFOs
lsof +E -p <pid>       # show pipe endpoints

# Output:
# bash  1234  user  1w  FIFO  0,14  0t0  56789 pipe
# cat   1235  user  0r  FIFO  0,14  0t0  56789 pipe
# (same inode 56789 = they share the same pipe)
```

### 17.3 `/proc/PID/fdinfo/N` — Pipe Details

```bash
cat /proc/<pid>/fdinfo/<fd>
# pos:	0
# flags:	0100001      <- O_WRONLY | O_NONBLOCK (octal)
# mnt_id:	13
# ino:	56789
# pipe-read-size:	65536
# pipe-write-size:	65536
```

### 17.4 `ftrace` — Kernel-Level Pipe Tracing

```bash
# Trace pipe_write and pipe_read functions
cd /sys/kernel/debug/tracing

echo 0 > tracing_on
echo 'pipe_write pipe_read' > set_ftrace_filter
echo 'function_graph' > current_tracer
echo 1 > tracing_on

# Run your workload
cat /dev/urandom | dd bs=4096 count=100 of=/dev/null

echo 0 > tracing_on
cat trace | head -50
```

### 17.5 `bpftrace` — Dynamic Pipe Analysis

```bash
# Trace large pipe writes (>4096 bytes)
bpftrace -e '
tracepoint:syscalls:sys_enter_write
/args->count > 4096/
{
    printf("PID=%d COMM=%s fd=%d size=%d\n",
           pid, comm, args->fd, args->count);
}'

# Measure pipe write latency
bpftrace -e '
kprobe:pipe_write { @start[tid] = nsecs; }
kretprobe:pipe_write /@start[tid]/
{
    @latency_ns = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}'

# Count pipe operations per process
bpftrace -e '
kprobe:pipe_write { @writes[comm]++; }
kprobe:pipe_read  { @reads[comm]++;  }
interval:s:5 { print(@writes); print(@reads); clear(@writes); clear(@reads); }'
```

### 17.6 `perf` — Pipe Performance Profiling

```bash
# Count pipe_write calls system-wide for 10s
perf stat -e 'syscalls:sys_enter_write' -a sleep 10

# Record pipe-intensive workload
perf record -g -e syscalls:sys_enter_write -p <pid> sleep 5
perf report --sort=dso,sym

# Trace pipe write/read latency with perf trace
perf trace -e write,read -p <pid> 2>&1 | grep -E 'pipe|fifo'
```

### 17.7 Finding All Pipes System-Wide

```bash
# Find all pipes system-wide (requires root or same UID)
find /proc/*/fd -type l -exec ls -la {} \; 2>/dev/null | grep pipe:

# Pipe capacity info
cat /proc/<pid>/fdinfo/<fd> | grep pipe
```

---

## 18. Performance Characteristics

### 18.1 Throughput Benchmarks (Approximate, modern x86-64)

```
Pipe throughput (single core, blocking writes):
  Small writes (1 byte):     ~400 MB/s   (syscall overhead dominates)
  Medium writes (4 KiB):    ~3.2 GB/s
  Large writes (64 KiB):    ~4.8 GB/s   (single memcpy, full buffer)
  splice() (64 KiB):        ~8.0 GB/s   (zero-copy, no user<->kernel copy)
```

### 18.2 Latency

```
Round-trip pipe latency (write + read, same process):
  ~1-2 us    (no contention, hot cache)
  ~5-20 us   (cross-core, parent->child)
```

### 18.3 Performance Optimization Tips

```
1. Increase pipe buffer size for streaming:
   fcntl(pfd[1], F_SETPIPE_SZ, 1024*1024)   -> reduce write() blocking frequency

2. Use splice() instead of read()+write() for fd-to-fd transfers.

3. Use O_NONBLOCK + epoll for multiplexing multiple pipes:
   -> avoids thread-per-pipe overhead

4. Align writes to PIPE_BUF (4096) boundaries:
   -> maximizes pages per pipe_buffer slot
   -> avoids partial-page fills that waste kernel memory

5. Large writes (multiples of 4096) are most efficient:
   -> each 4096-byte chunk maps to one pipe_buffer slot (one page)
   -> avoids copy_page_from_iter overhead of combining partial pages

6. Avoid context-switch ping-pong:
   -> batch data: write large chunks rather than many small writes
   -> reader should batch reads too (read into large buffer)

7. CPU affinity: pin producer and consumer to same NUMA node.
   -> pipe page allocations stay local, avoid NUMA crossing penalty
```

### 18.4 `vmsplice()` for Maximum Throughput

```c
/* Producer: map pages, vmsplice into pipe (zero-copy from user) */
void *buf = mmap(NULL, PIPE_SIZE, PROT_READ|PROT_WRITE,
                 MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE, -1, 0);

/* Fill buf with data */
memset(buf, 'A', PIPE_SIZE);

struct iovec iov = { buf, PIPE_SIZE };
/* SPLICE_F_GIFT transfers page ownership; don't touch buf after this */
vmsplice(pfd[1], &iov, 1, SPLICE_F_GIFT);

/* Consumer: splice from pipe to socket */
splice(pfd[0], NULL, sockfd, NULL, PIPE_SIZE, SPLICE_F_MOVE);
```

---

## 19. Pipe in Kernel Driver / Module Code

### 19.1 Creating a Pipe from Kernel Space

Kernel code generally doesn't use `pipe()` directly (that's a syscall for userspace). Internally, drivers and subsystems use pipe infrastructure via:

```c
/* Create pipe from kernel -- used by watch_queue, io_uring, etc. */
struct pipe_inode_info *pipe;

pipe = alloc_pipe_info();
if (!pipe)
    return -ENOMEM;

/* Access pipe_buffer ring directly */
pipe->ring_size = PIPE_DEF_BUFFERS;
pipe->bufs = kcalloc(pipe->ring_size, sizeof(struct pipe_buffer), GFP_KERNEL);
```

### 19.2 Splicing Data from a Driver into a Pipe

The `splice_read` file operation allows a driver to feed data into a pipe via `splice()`:

```c
/* Driver: implement f_op->splice_read */
static ssize_t mydrv_splice_read(struct file *file, loff_t *ppos,
                                  struct pipe_inode_info *pipe,
                                  size_t len, unsigned int flags)
{
    struct pipe_buffer *buf;
    struct page *page;
    unsigned int head;

    /* Get next free pipe slot */
    if (pipe_full(pipe->head, pipe->tail, pipe->max_usage))
        return -EAGAIN;

    head = pipe->head;
    buf = &pipe->bufs[head & (pipe->ring_size - 1)];

    page = alloc_page(GFP_KERNEL);
    if (!page)
        return -ENOMEM;

    /* Copy device data into page */
    copy_from_device(page_address(page), len);

    buf->page   = page;
    buf->offset = 0;
    buf->len    = len;
    buf->ops    = &anon_pipe_buf_ops;
    buf->flags  = 0;
    pipe->head++;

    return len;
}

static const struct file_operations mydrv_fops = {
    .splice_read = mydrv_splice_read,
    /* ... */
};
```

### 19.3 `io_uring` and Pipes (Linux 5.5+)

`io_uring` supports `IORING_OP_SPLICE` and `IORING_OP_TEE`, enabling async zero-copy splice operations through pipes without blocking the calling thread:

```c
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_splice(sqe,
    in_fd,   /* source */
    -1,      /* offset (-1 for pipes) */
    out_fd,  /* destination (must be pipe or vice versa) */
    -1,
    len,
    SPLICE_F_MOVE);
io_uring_submit(&ring);
```

### 19.4 Kernel Pipe Usage: Watch Queue (Linux 5.8+)

`watch_queue` in the kernel uses pipes as notification channels for key/keyring events, hardware events, and mount notifications:

```c
/* include/linux/watch_queue.h */
struct watch_queue {
    struct pipe_inode_info  *pipe;   /* <- a pipe is the backing store */
    struct rcu_head         rcu;
    struct wqueue_filter    *filter;
    /* ... */
};
```

```bash
# Userspace: open /dev/watch_queue and ioctl to set up notifications
# The fd is a pipe read end; events arrive as pipe_buffer entries
```

---

## 20. Reference Summary

### 20.1 Key Kernel Source Files

```
fs/pipe.c                    -- Core pipe implementation: pipe_read, pipe_write,
                               pipe_poll, alloc_pipe_info, do_pipe2
fs/splice.c                  -- splice(), tee(), vmsplice() implementation
fs/fifo.c                    -- Named pipe (FIFO) open handling: fifo_open()
include/linux/pipe_fs_i.h    -- pipe_inode_info, pipe_buffer structs
include/uapi/linux/limits.h  -- PIPE_BUF definition
include/linux/splice.h       -- splice-related structs and flags
kernel/watch_queue.c         -- watch_queue (pipe-backed notification)
io_uring/splice.c            -- io_uring splice/tee ops
```

### 20.2 Key Kernel Functions

```
alloc_pipe_info()       -- allocate pipe_inode_info + bufs ring
free_pipe_info()        -- free pipe_inode_info
get_pipe_inode()        -- create inode in pipefs with pipe_inode_info
pipe_write()            -- vfs write handler (f_op->write_iter)
pipe_read()             -- vfs read handler (f_op->read_iter)
pipe_poll()             -- vfs poll handler
do_splice_to()          -- copy data from file into pipe
do_splice_from()        -- copy data from pipe to file
iter_file_splice_write()-- generic splice write via iov_iter
```

### 20.3 Syscalls Reference

```c
pipe(pipefd)                            /* unistd.h */
pipe2(pipefd, flags)                    /* unistd.h -- Linux 2.6.27+ */
mkfifo(pathname, mode)                  /* sys/stat.h */
fcntl(fd, F_GETPIPE_SZ)                /* fcntl.h -- Linux 2.6.35+ */
fcntl(fd, F_SETPIPE_SZ, size)          /* fcntl.h -- Linux 2.6.35+ */
splice(fd_in, off_in, fd_out, off_out, len, flags)  /* fcntl.h */
tee(fd_in, fd_out, len, flags)         /* fcntl.h */
vmsplice(fd, iov, nr_segs, flags)      /* fcntl.h */
```

### 20.4 Key `/proc` and Sysctl Paths

```
/proc/sys/fs/pipe-max-size          -- max pipe capacity (bytes)
/proc/sys/fs/pipe-user-pages-hard   -- hard per-user page limit
/proc/sys/fs/pipe-user-pages-soft   -- soft per-user page limit
/proc/<pid>/fd/<n>                  -- symlink: "pipe:[inode]"
/proc/<pid>/fdinfo/<n>              -- pipe-read-size, pipe-write-size
```

### 20.5 ASCII Architecture: Complete Pipe Subsystem

```
User Space                    Kernel Space
-------------------------------------------------------------
  write(fd,buf,n)
        |
        v
  +-------------+
  |  VFS layer  |  sys_write() -> ksys_write() -> vfs_write()
  +------+------+
         |  f_op->write_iter = pipe_write
         v
  +-------------------------------------------------------------+
  |                    pipe_write()  [fs/pipe.c]                |
  |                                                             |
  |  mutex_lock(pipe->mutex)                                    |
  |  while (bytes > 0):                                         |
  |    if full -> pipe_wait_writable() ----------------+        |
  |    buf = bufs[head & mask]                         |        |
  |    page = alloc_page() or reuse                    |        |
  |    copy_page_from_iter(page, data) <- user copy    |        |
  |    buf->len = bytes; head++                        |        |
  |  wake_up(rd_wait) ----------------------------+   |        |
  |  mutex_unlock()                               |   |        |
  +-----------------------------------------------+---+--------+
                                                  |   |
  +-----------------------------------------------+---v--------+
  |                 pipe_inode_info                |            |
  |  +------------------------------------------+ |            |
  |  |  bufs[]  ring_size=16                    | |            |
  |  |  [0][1][2][3]...[15]  (pipe_buffer each) | |            |
  |  |  tail^              ^head                | |            |
  |  +------------------------------------------+ |            |
  |  mutex, rd_wait <------------------------------+            |
  |  wr_wait <--------------------------------------------------+
  +-------------------------------------------------------------+
         |  pipe_read()
         |  mutex_lock()
         |  copy_page_to_iter(page, buf) --> user copy
         |  tail++; wake_up(wr_wait)
         v
  +-------------+
  |  VFS layer  |  read() returns to userspace
  +-------------+
         |
         v
  read(fd,buf,n) returns in userspace

splice() path (zero-copy):
  file_fd --[page cache pages]--> pipe_buffer[] --[page refs]--> dst_fd
              NO user copy                         NO kernel copy
```

### 20.6 Further Reading

```
Kernel Documentation:
  Documentation/filesystems/pipes.rst        (sparse; prefer kernel source)
  Documentation/core-api/iov_iter.rst        (iov_iter used in pipe I/O)
  Documentation/watch_queue.rst              (pipe-backed notifications)

LWN Articles:
  https://lwn.net/Articles/118750/   -- splice() introduction (2005)
  https://lwn.net/Articles/879090/   -- Dirty Pipe (CVE-2022-0847) analysis
  https://lwn.net/Articles/164887/   -- tee() and vmsplice()
  https://lwn.net/Articles/531114/   -- F_SETPIPE_SZ and pipe limits

Books:
  "Linux Kernel Development" -- Robert Love, Ch. 17 (Block I/O), IPC
  "The Linux Programming Interface" -- Kerrisk, Ch. 44 (Pipes), Ch. 63 (epoll)
  "Advanced Programming in the UNIX Environment" -- Stevens, Ch. 15

Source exploration order:
  1. include/linux/pipe_fs_i.h       <- data structures
  2. fs/pipe.c                       <- pipe_write, pipe_read, alloc_pipe_info
  3. fs/fifo.c                       <- fifo_open, open semantics
  4. fs/splice.c                     <- splice, tee, vmsplice
  5. io_uring/splice.c               <- async splice
  6. kernel/watch_queue.c            <- pipe-backed notifications
```

---

*Kernel 6.8+ | Source: https://elixir.bootlin.com/linux/latest/source/fs/pipe.c*

~3,200 lines covering the full depth. Here's what's inside:

**20 chapters**, structured from fundamentals to advanced kernel internals:

| Chapter | Coverage |
|---|---|
| 1–3 | Conceptual model, POSIX guarantees, `pipe(2)`/`pipe2(2)` API, FIFOs, open-blocking semantics |
| 4 | `pipe_inode_info`, `pipe_buffer`, `pipe_buf_operations` with full struct dumps; ring buffer layout |
| 5 | Complete kernel code paths: `sys_pipe2()` → `alloc_pipe_info()`, `pipe_write()` → `copy_page_from_iter()`, `pipe_read()`, `pipe_poll()` |
| 6–7 | Capacity tunables (`F_SETPIPE_SZ`, sysctl knobs), `O_NONBLOCK`, `O_DIRECT` packet mode, `O_CLOEXEC` |
| 8 | `splice()`/`tee()`/`vmsplice()` zero-copy internals with page-ref data flow diagram |
| 9 | Shell pipeline execution — `fork()`+`dup2()`+`exec()` plumbing, `PIPESTATUS`, `|&`, process substitution, `lastpipe` trap |
| 10 | `SIGPIPE`/`EPIPE` mechanics from `pipe_write()` → `send_signal()`, suppression patterns |
| 11 | Bidirectional pipes, `socketpair()`, `SCM_RIGHTS` fd passing |
| 12 | IPC comparison table: pipe vs Unix socket vs POSIX MQ vs shared memory |
| 13 | Self-pipe trick, `popen()`, pipe-as-semaphore, `tee()` fan-out, bash coprocess |
| 14 | `splice()`-based zero-copy HTTP, eBPF/bpftrace integration, XDP, Netlink piping |
| 15 | Container/Kubernetes internals (Docker stdin pipes, `kubectl exec` path, cgroup kmem accounting), cloud CLI patterns, sidecar log FIFO |
| 16 | **CVE-2022-0847 Dirty Pipe** — root cause, exploit sketch, exact kernel fix; FIFO TOCTOU, pipe exhaustion DoS, seccomp filtering, LSM hooks |
| 17 | `strace`, `lsof`, `/proc/PID/fdinfo`, `ftrace`, `bpftrace` one-liners, `perf` |
| 18 | Throughput/latency numbers, NUMA-aware tuning, `vmsplice()` max-throughput pattern |
| 19 | `alloc_pipe_info()` from kernel code, `f_op->splice_read` driver implementation, `io_uring` async splice, `watch_queue` |
| 20 | Full source file map, function reference, syscall signatures, sysctl paths, reading list |