# File Descriptors: A Complete Systems Engineering Guide
### C · Rust · Go — Internals, Patterns, and Production Engineering

---

## Table of Contents

1. [What Is a File Descriptor?](#1-what-is-a-file-descriptor)
2. [Kernel Data Structures](#2-kernel-data-structures)
3. [The Three Standard Descriptors](#3-the-three-standard-descriptors)
4. [Core Syscalls](#4-core-syscalls)
5. [File Descriptor Flags and Status Flags](#5-file-descriptor-flags-and-status-flags)
6. [Descriptor Duplication: dup, dup2, dup3](#6-descriptor-duplication-dup-dup2-dup3)
7. [File Descriptor Limits](#7-file-descriptor-limits)
8. [Inheritance: fork, exec, and O_CLOEXEC](#8-inheritance-fork-exec-and-o_cloexec)
9. [Nonblocking I/O](#9-nonblocking-io)
10. [I/O Multiplexing: select, poll, epoll, kqueue](#10-io-multiplexing-select-poll-epoll-kqueue)
11. [Pipes and Named Pipes (FIFOs)](#11-pipes-and-named-pipes-fifos)
12. [Socket File Descriptors](#12-socket-file-descriptors)
13. [Memory-Mapped Files (mmap)](#13-memory-mapped-files-mmap)
14. [sendfile and Zero-Copy I/O](#14-sendfile-and-zero-copy-io)
15. [Passing File Descriptors over Unix Sockets (SCM_RIGHTS)](#15-passing-file-descriptors-over-unix-sockets-scm_rights)
16. [Inspecting Descriptors: /proc and lsof](#16-inspecting-descriptors-proc-and-lsof)
17. [File Descriptor Leaks](#17-file-descriptor-leaks)
18. [C Implementation: Full Reference](#18-c-implementation-full-reference)
19. [Rust Implementation: Safe and Unsafe](#19-rust-implementation-safe-and-unsafe)
20. [Go Implementation: Internals and Patterns](#20-go-implementation-internals-and-patterns)
21. [Cross-Language FD Interop: C↔Rust↔Go](#21-cross-language-fd-interop-crustgo)
22. [Async I/O: io_uring (Linux 5.1+)](#22-async-io-io_uring-linux-51)
23. [Security Hardening Checklist](#23-security-hardening-checklist)
24. [Production Patterns and War Stories](#24-production-patterns-and-war-stories)
25. [Profiling and Observability](#25-profiling-and-observability)
26. [Exercises](#26-exercises)
27. [Further Reading](#27-further-reading)

---

## 1. What Is a File Descriptor?

**One-line answer:** A file descriptor (FD) is a small non-negative integer that the kernel returns to a process as an opaque handle to an open "file" — where "file" means anything the kernel can do I/O on.

The POSIX abstraction is remarkable: regular files, directories, devices, pipes, sockets, terminals, timers (`timerfd`), event queues (`eventfd`), signals (`signalfd`), and memory (`memfd`) all share the same integer handle, the same `read`/`write` interface, and the same `close` lifecycle.

```
Process address space          Kernel space
┌─────────────────┐           ┌──────────────────────────────────────┐
│ fd = 3          │──────────▶│ struct file (open file description)  │
│ fd = 4          │──────────▶│   file_pos, flags, f_ops, f_inode   │
│ fd = 5          │──────────▶│ struct socket / pipe / inode ...     │
└─────────────────┘           └──────────────────────────────────────┘
```

**The abstraction holds for:**

| Resource          | How you get an FD                    |
|-------------------|--------------------------------------|
| Regular file      | `open(2)`, `openat(2)`               |
| Directory         | `open(2)` with `O_DIRECTORY`         |
| Character device  | `open("/dev/tty", ...)`              |
| Block device      | `open("/dev/sda", ...)`              |
| FIFO/named pipe   | `open(fifo_path, ...)` / `mkfifo(3)` |
| Anonymous pipe    | `pipe(2)`, `pipe2(2)`                |
| TCP/UDP socket    | `socket(2)`                          |
| Unix socket       | `socket(AF_UNIX, ...)`               |
| epoll instance    | `epoll_create1(2)`                   |
| inotify instance  | `inotify_init1(2)`                   |
| timerfd           | `timerfd_create(2)`                  |
| eventfd           | `eventfd(2)`                         |
| signalfd          | `signalfd(2)`                        |
| memfd             | `memfd_create(2)`                    |
| io_uring instance | `io_uring_setup(2)`                  |
| pidfd             | `pidfd_open(2)`                      |
| userfaultfd       | `userfaultfd(2)`                     |

---

## 2. Kernel Data Structures

This is the most important section — understanding these three tables makes every puzzling FD behavior make sense.

### 2.1 Three-Level Table Architecture

```
Per-process FD table          System-wide open file table      Inode table (VFS)
┌────────────────────┐        ┌──────────────────────────┐     ┌───────────────┐
│ fd 0  → *file_A   │───────▶│ struct file (file_A)     │────▶│ inode 47      │
│ fd 1  → *file_B   │───────▶│   f_pos   = 0            │     │   i_mode      │
│ fd 2  → *file_B   │──┐     │   f_flags = O_RDWR       │     │   i_size      │
│ fd 3  → *file_C   │  │     │   f_count = 1            │     │   i_blocks    │
│ fd 4  → NULL      │  │     │   f_op    = &ext4_f_ops  │     └───────────────┘
│ ...               │  └────▶│ struct file (file_B)     │────▶│ inode 47      │
└────────────────────┘        │   f_pos   = 1024         │     │  (same inode!)│
                              │   f_flags = O_WRONLY     │     └───────────────┘
                              │   f_count = 2  ◀── refs  │
                              └──────────────────────────┘
```

**Layer 1 — Per-process file descriptor table (`files_struct`)**

Defined in `include/linux/fdtable.h`. Each process has one. It is an array of pointers to `struct file`. The integer FD is just the index into this array.

Key fields:
- `fd_array[]` — inline array for the first 64 descriptors (avoids allocation for small processes)
- `fdt` — pointer to `fdtable` struct which holds a dynamically grown `fd[]` array
- `close_on_exec` — bitmap; FDs with this bit set are closed when `execve` is called
- `open_fds` — bitmap of open descriptors
- `next_fd` — hint for the next FD to allocate (always picks the lowest available)

**Layer 2 — Open file description (`struct file`)**

This is the "open file description" (not "descriptor"!). The distinction matters enormously:

- `f_pos` — current file offset, **per open file description**, not per inode
- `f_flags` — `O_RDONLY`, `O_WRONLY`, `O_NONBLOCK`, etc., set at `open()` time
- `f_count` — reference count; decremented by `close()`, freed when it hits 0
- `f_op` — pointer to `file_operations` vtable (`read`, `write`, `mmap`, `poll`, `ioctl`, ...)
- `f_inode` — pointer to the inode
- `f_cred` — credentials at the time of `open()`

**Layer 3 — Inode (`struct inode`)**

The actual file metadata: permissions, ownership, timestamps, block map. Multiple open file descriptions can point to the same inode.

### 2.2 Why the Three-Layer Design Matters

**Scenario A: Two processes open the same file independently**

```
Process 1: fd 3 → file_desc_1 (f_pos=0)  ─┐
                                            ├─▶ inode 47
Process 2: fd 3 → file_desc_2 (f_pos=512) ─┘
```

Each has its own position. Reads/writes are independent.

**Scenario B: `dup(fd)` within one process**

```
fd 3 → ─┐
         ├─▶ file_desc_1 (f_pos=0, f_count=2)  ─▶ inode 47
fd 4 → ─┘
```

Both FDs share **one** open file description. A read through fd 3 advances the position seen by fd 4. Closing fd 3 decrements `f_count` to 1; the description lives until fd 4 is also closed.

**Scenario C: `fork()`**

```
Parent fd 5 → ─┐
                ├─▶ file_desc_X (f_count=2) ─▶ inode 99
Child  fd 5 → ─┘
```

Fork copies the FD table, bumping `f_count` on every referenced `struct file`. Parent and child share position — if the parent writes 100 bytes, the child's position advances too. This is intentional and used by shells to implement pipelines.

**Scenario D: `dup2(old, new)` for shell redirection**

```bash
# ls > /tmp/out.txt
# Shell does: fd = open("/tmp/out.txt", O_WRONLY|O_CREAT|O_TRUNC)
#             dup2(fd, STDOUT_FILENO)
#             close(fd)
```

After `dup2(5, 1)`:
```
fd 1 → ─┐
         ├─▶ file_desc for /tmp/out.txt
fd 5 → ─┘
```

Now anything written to stdout goes to the file.

### 2.3 Linux Source References

```
fs/file.c          — FD table allocation, get_unused_fd_flags, __alloc_fd
fs/open.c          — do_sys_open, do_filp_open
include/linux/fs.h — struct file, struct inode, file_operations
include/linux/fdtable.h — struct files_struct, struct fdtable
```

---

## 3. The Three Standard Descriptors

By POSIX convention (and Linux kernel startup):

| FD | POSIX name      | C macro         | Default destination     |
|----|-----------------|-----------------|-------------------------|
| 0  | `STDIN_FILENO`  | `stdin`         | Terminal (keyboard)     |
| 1  | `STDOUT_FILENO` | `stdout`        | Terminal (screen)       |
| 2  | `STDERR_FILENO` | `stderr`        | Terminal (screen)       |

These are **just convention**. The kernel does not treat them specially after PID 1 sets them up. A daemon that closes all three and reopens them to `/dev/null` is perfectly valid.

The kernel initializes FD 0, 1, 2 for `init` (PID 1) by opening `/dev/console`. Every subsequent process inherits them through `fork` + `exec`.

---

## 4. Core Syscalls

### 4.1 `open` / `openat`

```c
#include <fcntl.h>
int open(const char *pathname, int flags);
int open(const char *pathname, int flags, mode_t mode);   // when O_CREAT
int openat(int dirfd, const char *pathname, int flags, mode_t mode);
```

**`openat` is always preferred** in production code. It prevents TOCTOU (time-of-check/time-of-use) races and works correctly in chroot/container environments. Using `AT_FDCWD` as `dirfd` is equivalent to `open`.

Kernel path: `sys_openat` → `do_sys_open` → `do_filp_open` → `path_openat` → VFS layer → filesystem driver.

### 4.2 `close`

```c
int close(int fd);
```

Decrements `f_count` on the open file description. When it hits 0, the description is freed and the inode's reference count is decremented.

**Critical production bug:** `close` can fail (e.g., on NFS — it flushes dirty pages). Always check the return value. Many programs don't, and data is silently lost.

```c
if (close(fd) == -1) {
    perror("close");
    // handle: data may not be flushed
}
```

After `close`, the FD number is **immediately** available for reuse. This is the source of "stale FD" bugs in multithreaded programs.

### 4.3 `read` / `write`

```c
ssize_t read(int fd, void *buf, size_t count);
ssize_t write(int fd, const void *buf, size_t count);
```

Both can return less than `count` — this is not an error. It's called a **short read/write** and you must loop:

```c
ssize_t write_all(int fd, const void *buf, size_t count) {
    size_t written = 0;
    while (written < count) {
        ssize_t n = write(fd, (const char*)buf + written, count - written);
        if (n < 0) {
            if (errno == EINTR) continue;   // signal interrupted — retry
            return -1;
        }
        written += (size_t)n;
    }
    return (ssize_t)written;
}
```

### 4.4 `pread` / `pwrite`

Positional I/O — reads/writes at a specific offset without changing `f_pos`. Thread-safe for concurrent access to the same FD.

```c
ssize_t pread(int fd, void *buf, size_t count, off_t offset);
ssize_t pwrite(int fd, const void *buf, size_t count, off_t offset);
```

### 4.5 `lseek`

```c
off_t lseek(int fd, off_t offset, int whence);
// whence: SEEK_SET, SEEK_CUR, SEEK_END, SEEK_DATA, SEEK_HOLE
```

`SEEK_DATA` / `SEEK_HOLE` enable sparse file navigation — jump over holes (unwritten regions that read as zero) without reading them.

```c
// Discover the size of a file portably
off_t size = lseek(fd, 0, SEEK_END);
lseek(fd, 0, SEEK_SET);  // rewind
```

### 4.6 `readv` / `writev` (Scatter-Gather I/O)

```c
#include <sys/uio.h>
ssize_t readv(int fd, const struct iovec *iov, int iovcnt);
ssize_t writev(int fd, const struct iovec *iov, int iovcnt);

struct iovec {
    void   *iov_base;  // buffer address
    size_t  iov_len;   // buffer length
};
```

A single syscall reads/writes from multiple discontiguous buffers. Eliminates the copy needed to assemble a contiguous buffer before sending. Essential for high-performance network I/O (HTTP headers + body in one `writev`).

### 4.7 `fcntl`

The Swiss-army knife for FD manipulation:

```c
#include <fcntl.h>
int fcntl(int fd, int cmd, ...);
```

| cmd                  | Purpose                                          |
|----------------------|--------------------------------------------------|
| `F_DUPFD`            | Duplicate FD, return ≥ arg                       |
| `F_DUPFD_CLOEXEC`    | Duplicate + set `FD_CLOEXEC`                     |
| `F_GETFD`            | Get FD flags (`FD_CLOEXEC`)                      |
| `F_SETFD`            | Set FD flags                                     |
| `F_GETFL`            | Get file status flags (`O_NONBLOCK`, `O_RDWR`)   |
| `F_SETFL`            | Set file status flags (only some are changeable) |
| `F_GETLK`/`F_SETLK`  | Advisory record locking (`struct flock`)         |
| `F_OFD_GETLK`        | Open file description lock (Linux 3.15+)         |
| `F_SETOWN`           | Set PID/PGID for `SIGIO`/`SIGURG`                |
| `F_SETSIG`           | Set signal for async I/O notification            |
| `F_ADD_SEALS`        | Add seals to `memfd` (immutability controls)     |

**Set a file nonblocking at runtime:**

```c
int flags = fcntl(fd, F_GETFL, 0);
if (flags == -1) { perror("fcntl F_GETFL"); exit(1); }
if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
    perror("fcntl F_SETFL");
    exit(1);
}
```

### 4.8 `ioctl`

Device-specific operations that don't fit the `read`/`write` model:

```c
int ioctl(int fd, unsigned long request, ...);
```

Used for: terminal settings (`TIOCGWINSZ`), network interface control (`SIOCGIFADDR`), disk management, video devices, custom kernel modules. Each device driver defines its own request codes.

### 4.9 `fstat` / `fstatat`

Retrieve inode metadata without a path:

```c
#include <sys/stat.h>
int fstat(int fd, struct stat *statbuf);
int fstatat(int dirfd, const char *path, struct stat *statbuf, int flags);
```

`fstatat` with `AT_EMPTY_PATH` and `dirfd` is equivalent to `fstat(dirfd, ...)`.

### 4.10 `ftruncate` / `fallocate`

```c
int ftruncate(int fd, off_t length);
int fallocate(int fd, int mode, off_t offset, off_t len);
```

`fallocate` preallocates disk space without writing data — crucial for avoiding fragmentation and mid-write ENOSPC errors. With `FALLOC_FL_PUNCH_HOLE`, it creates sparse holes.

---

## 5. File Descriptor Flags and Status Flags

There are **two distinct sets of flags** for each FD:

### 5.1 FD Flags (per-descriptor, not per-description)

Controlled via `F_GETFD`/`F_SETFD`:

| Flag          | Value | Meaning                                             |
|---------------|-------|-----------------------------------------------------|
| `FD_CLOEXEC`  | 1     | Close this FD when `execve` is called               |

This is the **only** FD flag in POSIX. Linux adds no others at this layer.

Because `FD_CLOEXEC` lives in the FD table entry (Layer 1), it is **not** shared between `dup`'d descriptors. Each duplicate has its own bit.

### 5.2 File Status Flags (per-description, shared between dup'd FDs)

Controlled via `F_GETFL`/`F_SETFL`:

| Flag          | At open | Changeable | Meaning                                     |
|---------------|---------|------------|---------------------------------------------|
| `O_RDONLY`    | ✓       | ✗          | Read-only                                   |
| `O_WRONLY`    | ✓       | ✗          | Write-only                                  |
| `O_RDWR`      | ✓       | ✗          | Read-write                                  |
| `O_CREAT`     | ✓       | ✗          | Create if not exists (needs `mode`)         |
| `O_EXCL`      | ✓       | ✗          | Fail if file exists (atomic create)         |
| `O_TRUNC`     | ✓       | ✗          | Truncate to zero on open                    |
| `O_APPEND`    | ✓       | ✓          | All writes go to end (atomic w.r.t. kernel) |
| `O_NONBLOCK`  | ✓       | ✓          | Non-blocking I/O                            |
| `O_SYNC`      | ✓       | ✓          | Synchronous writes (data+metadata)          |
| `O_DSYNC`     | ✓       | ✓          | Synchronous writes (data only)              |
| `O_DIRECT`    | ✓       | ✓          | Bypass page cache (DMA to userspace)        |
| `O_NOATIME`   | ✓       | ✓          | Don't update access time on read            |
| `O_CLOEXEC`   | ✓       | ✗          | Set FD_CLOEXEC atomically at open time      |
| `O_PATH`      | ✓       | ✗          | FD for path ops only, no I/O               |
| `O_TMPFILE`   | ✓       | ✗          | Create anonymous temp file                  |
| `O_DIRECTORY` | ✓       | ✗          | Fail if not a directory                     |
| `O_NOFOLLOW`  | ✓       | ✗          | Fail if final component is a symlink        |
| `O_NOCTTY`    | ✓       | ✗          | Don't make this process's controlling tty   |

**Key insight:** The access mode (`O_RDONLY`, `O_WRONLY`, `O_RDWR`) and creation flags (`O_CREAT`, `O_EXCL`, `O_TRUNC`) **cannot** be changed after `open`. Only status flags like `O_NONBLOCK`, `O_APPEND`, `O_SYNC` can be modified with `F_SETFL`.

### 5.3 `O_APPEND` Atomicity

`O_APPEND` makes writes atomic at the kernel level: the kernel atomically seeks to end + writes. This is why `O_APPEND` is the correct way to have multiple processes log to the same file. **Without it**, concurrent writers will overwrite each other.

```c
int logfd = open("/var/log/myapp.log",
                 O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
```

However: `O_APPEND` atomicity is only guaranteed for writes up to `PIPE_BUF` bytes (4096 on Linux) on pipes. For regular files, the POSIX spec says it's atomic, and Linux upholds this.

### 5.4 `O_DIRECT` and Alignment Requirements

Bypasses the kernel page cache, sending I/O directly between user buffers and storage. Required for databases that implement their own page cache (PostgreSQL, RocksDB).

Constraints (device-dependent, but typically):
- Buffer address must be aligned to `512` or `4096` bytes (use `posix_memalign`)
- Transfer size must be a multiple of the block size
- File offset must be a multiple of the block size

```c
void *buf;
posix_memalign(&buf, 4096, 4096);  // 4KB aligned buffer
int fd = open("data.bin", O_RDWR | O_DIRECT | O_CREAT, 0644);
pread(fd, buf, 4096, 0);
```

---

## 6. Descriptor Duplication: dup, dup2, dup3

### 6.1 `dup`

```c
int dup(int oldfd);
```

Creates a new FD pointing to the same open file description. The new FD is the **lowest available** integer.

### 6.2 `dup2`

```c
int dup2(int oldfd, int newfd);
```

Atomically: if `newfd` is open, close it; then make `newfd` point to the same description as `oldfd`. The atomicity prevents a race window where another thread could grab `newfd` between close and dup.

Shell redirection implementation:
```c
// Redirect stdout to a file
int fd = open("output.txt", O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
dup2(fd, STDOUT_FILENO);  // fd 1 now points to output.txt
close(fd);                // original fd no longer needed
// Now exec the child — its stdout goes to output.txt
```

### 6.3 `dup3` (Linux-specific)

```c
#define _GNU_SOURCE
#include <fcntl.h>
int dup3(int oldfd, int newfd, int flags);
// flags: O_CLOEXEC
```

Like `dup2` but atomically sets `O_CLOEXEC`. Also fails if `oldfd == newfd` (unlike `dup2`).

**Always use `dup3` or `F_DUPFD_CLOEXEC` in production** to avoid leaking FDs across `exec`.

### 6.4 `dup` vs `dup2` Internals

Both call `__do_dup2` in `fs/file.c`. The key operation is:

1. Validate `oldfd` (look up in `files->fdt->fd[oldfd]`)
2. Acquire `files->file_lock`
3. If `newfd` has an existing entry, flush it to close list
4. Install `struct file*` at `fdt->fd[newfd]`
5. Release lock; actually call `filp_close` on the old `newfd` entry

---

## 7. File Descriptor Limits

### 7.1 Per-Process Limits

```bash
ulimit -n          # soft limit (current process)
ulimit -Hn         # hard limit (maximum settable soft limit by non-root)
```

In `/etc/security/limits.conf`:
```
*    soft    nofile    65536
*    hard    nofile    1048576
```

In systemd unit files:
```ini
[Service]
LimitNOFILE=1048576
```

Programmatic query:
```c
#include <sys/resource.h>
struct rlimit rl;
getrlimit(RLIMIT_NOFILE, &rl);
printf("soft=%lu hard=%lu\n", rl.rlim_cur, rl.rlim_max);
// Raise soft limit to hard limit
rl.rlim_cur = rl.rlim_max;
setrlimit(RLIMIT_NOFILE, &rl);
```

### 7.2 System-Wide Limits

```bash
cat /proc/sys/fs/file-max       # max FDs across all processes
cat /proc/sys/fs/file-nr        # current: open, free, max
sysctl -w fs.file-max=2097152   # set at runtime
```

### 7.3 `NR_OPEN` Kernel Constant

The hard ceiling per process is `NR_OPEN` = 1,048,576 (1M) on 64-bit Linux, regardless of `rlimit`. This is the size of the `open_fds` bitmap.

### 7.4 FD Table Allocation Strategy

The kernel starts every process with an inline array of 64 FDs (the `fd_array` inside `files_struct`). When more are needed:
- Round up to next multiple of `BITS_PER_LONG` (64)
- Allocate new `fdtable`
- Copy old entries
- RCU-protect the swap

This means processes using < 64 FDs have zero heap allocation overhead for the FD table.

### 7.5 Checking Available FDs

```c
// How many FDs can we still open?
long available_fds(void) {
    struct rlimit rl;
    getrlimit(RLIMIT_NOFILE, &rl);

    DIR *proc_fd = opendir("/proc/self/fd");
    long count = 0;
    struct dirent *ent;
    while ((ent = readdir(proc_fd)) != NULL) {
        if (ent->d_name[0] != '.') count++;
    }
    closedir(proc_fd);

    return (long)rl.rlim_cur - count;
}
```

---

## 8. Inheritance: fork, exec, and O_CLOEXEC

### 8.1 `fork` Inheritance

`fork()` creates a copy of the parent's FD table. Every open FD in the parent is also open in the child, pointing to the same open file descriptions (incrementing their `f_count`).

```
Parent FD table         Child FD table (copy)
fd 0 → file_A    →     fd 0 → file_A   (f_count: 2 for each)
fd 1 → file_B    →     fd 1 → file_B
fd 3 → socket_C  →     fd 3 → socket_C
```

**Implication:** If the child doesn't `close` inherited sockets, the parent's `close` won't trigger TCP `FIN` because `f_count` is still > 0. Classic bug in servers that forget to close the listening socket in the child after `accept`.

### 8.2 `exec` and `FD_CLOEXEC`

After `execve`, by default **all FDs remain open**. Only FDs with `FD_CLOEXEC` set are closed.

```c
// DANGEROUS: fd 3 leaks into the execed process
int fd = open("secret.txt", O_RDONLY);
execl("/bin/sh", "sh", "-c", "cat /proc/self/fd", NULL);

// SAFE: fd 3 is closed before the new program runs
int fd = open("secret.txt", O_RDONLY | O_CLOEXEC);
execl("/bin/sh", "sh", "-c", "cat /proc/self/fd", NULL);
```

**Rule:** Always use `O_CLOEXEC` when opening files. Use `SOCK_CLOEXEC` for sockets. Use `F_DUPFD_CLOEXEC` for dup. The window between `open` and `fcntl(fd, F_SETFD, FD_CLOEXEC)` is a real race in multithreaded programs.

### 8.3 The `O_CLOEXEC` Race

```c
// BROKEN in multithreaded program:
int fd = open("file", O_RDONLY);   // <-- another thread forks here
fcntl(fd, F_SETFD, FD_CLOEXEC);   // <-- too late, child got fd without cloexec

// FIXED:
int fd = open("file", O_RDONLY | O_CLOEXEC);  // atomic
```

Linux 2.6.23+ guarantees atomicity of `O_CLOEXEC` at open time.

### 8.4 Explicitly Closing All FDs After Fork

For daemon processes that want a clean slate after fork:

```c
// Method 1: iterate /proc/self/fd (efficient, avoids closing non-existent FDs)
void close_all_fds_except(int *keep, int nkeep) {
    DIR *dir = opendir("/proc/self/fd");
    if (!dir) {
        // Fallback: brute force
        struct rlimit rl;
        getrlimit(RLIMIT_NOFILE, &rl);
        for (int fd = 3; fd < (int)rl.rlim_cur; fd++) {
            int skip = 0;
            for (int i = 0; i < nkeep; i++) if (keep[i] == fd) { skip = 1; break; }
            if (!skip) close(fd);
        }
        return;
    }
    int dirfd = dirfd(dir);
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        int fd = atoi(ent->d_name);
        if (fd == dirfd) continue;
        int skip = 0;
        for (int i = 0; i < nkeep; i++) if (keep[i] == fd) { skip = 1; break; }
        if (!skip) close(fd);
    }
    closedir(dir);
}
```

`close_range(3, UINT_MAX, 0)` (Linux 5.9+) closes a range of FDs in one syscall — the most efficient method.

---

## 9. Nonblocking I/O

### 9.1 Blocking vs Nonblocking

In blocking mode, `read` sleeps until data is available; `write` sleeps until the kernel can accept the data. The process is descheduled, consuming no CPU.

In nonblocking mode (`O_NONBLOCK`), syscalls return immediately with `EAGAIN` (or `EWOULDBLOCK`, same value on Linux) when they would block.

```c
int fd = open("myfifo", O_RDONLY | O_NONBLOCK);

char buf[1024];
ssize_t n = read(fd, buf, sizeof(buf));
if (n == -1) {
    if (errno == EAGAIN) {
        // No data available right now
    } else {
        perror("read");
    }
}
```

### 9.2 Why Nonblocking Matters

A server managing 10,000 concurrent connections **cannot** dedicate a thread per connection — that's 10,000 threads × ~8MB stack = 80GB memory. Instead, one thread uses an event loop:

1. Wait for any FD to become ready (`epoll_wait`)
2. `read`/`write` the ready FDs (guaranteed not to block because we checked)
3. Repeat

This is the C10K pattern, the foundation of nginx, Redis, Node.js, Tokio, and every modern event-driven server.

### 9.3 EAGAIN Handling for Writes

Even a `write` that is "ready" per `epoll` might return `EAGAIN` if the kernel buffer fills up mid-write (rare but real with large writes). Always handle it:

```c
// Write with backpressure handling
ssize_t write_nonblocking(int fd, const char *buf, size_t len) {
    size_t written = 0;
    while (written < len) {
        ssize_t n = write(fd, buf + written, len - written);
        if (n > 0) {
            written += n;
        } else if (n == -1 && errno == EAGAIN) {
            // Kernel buffer full — must wait for EPOLLOUT
            return (ssize_t)written;  // caller should buffer the rest
        } else if (n == -1 && errno == EINTR) {
            continue;
        } else {
            return -1;
        }
    }
    return (ssize_t)written;
}
```

---

## 10. I/O Multiplexing: select, poll, epoll, kqueue

### 10.1 `select` — The Original (1983)

```c
#include <sys/select.h>
int select(int nfds, fd_set *readfds, fd_set *writefds,
           fd_set *exceptfds, struct timeval *timeout);

FD_ZERO(&rfds);
FD_SET(fd, &rfds);
select(fd + 1, &rfds, NULL, NULL, NULL);
```

**Limitations:**
- FD limit: `FD_SETSIZE` = 1024 (kernel-compiled constant)
- O(nfds) kernel scan every call — copies the entire fd_set to kernel and back
- Caller must rebuild fd_sets after each call (they're consumed)
- Not thread-safe to add/remove FDs

### 10.2 `poll` — Removing the 1024 Limit

```c
#include <poll.h>
int poll(struct pollfd *fds, nfds_t nfds, int timeout);

struct pollfd {
    int   fd;
    short events;   // POLLIN, POLLOUT, POLLERR, POLLHUP, POLLRDHUP
    short revents;  // filled by kernel
};
```

- No `FD_SETSIZE` limit (heap-allocated array)
- Still O(n) kernel scan and O(n) copy in/out per call
- FD array doesn't need rebuilding (check `revents`)

### 10.3 `epoll` — Linux Scalable Multiplexing

```c
#include <sys/epoll.h>

// Create epoll instance
int epfd = epoll_create1(EPOLL_CLOEXEC);

// Register interest in an FD
struct epoll_event ev;
ev.events = EPOLLIN | EPOLLET;  // ET = edge-triggered
ev.data.fd = client_fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &ev);

// Wait for events (blocks until activity or timeout)
struct epoll_event events[MAX_EVENTS];
int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);
for (int i = 0; i < n; i++) {
    handle_event(events[i].data.fd, events[i].events);
}
```

**How it works internally:**

The epoll instance maintains a red-black tree of registered FDs (for O(log n) add/remove) and a linked list of ready FDs. When a registered FD becomes ready, the driver's `poll` callback adds it to the ready list via a wait queue callback. `epoll_wait` just harvests from the ready list — O(1) if events are ready, O(timeout) otherwise.

**Level-Triggered (LT) vs Edge-Triggered (ET):**

| Mode             | Trigger condition                           | Behavior on EAGAIN |
|------------------|---------------------------------------------|--------------------|
| Level-Triggered  | FD is readable/writable (state-based)       | epoll_wait returns it again next call |
| Edge-Triggered   | New data arrived since last `epoll_wait`    | epoll_wait won't report it again until new data arrives |

ET is more efficient (fewer wake-ups) but requires reading until `EAGAIN` on every notification:

```c
// Edge-triggered: must drain completely
if (events[i].events & EPOLLIN) {
    while (1) {
        ssize_t n = read(fd, buf, sizeof(buf));
        if (n > 0) {
            process(buf, n);
        } else if (n == -1 && errno == EAGAIN) {
            break;  // drained
        } else if (n == 0) {
            // EOF — peer closed connection
            epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
            close(fd);
            break;
        }
    }
}
```

**`EPOLLONESHOT`:** After one event, the FD is automatically deregistered. Prevents a race where two threads both receive events for the same FD.

**`EPOLLEXCLUSIVE`:** Multiple epoll instances share one FD; with `EXCLUSIVE`, only one is woken per event (avoid thundering herd).

**`EPOLLRDHUP`:** Detects peer half-close (TCP FIN received). Without this, you'd detect it only when `read` returns 0.

### 10.4 `kqueue` — BSD/macOS

```c
#include <sys/event.h>
int kq = kqueue();

struct kevent kev;
EV_SET(&kev, fd, EVFILT_READ, EV_ADD | EV_CLEAR, 0, 0, NULL);
kevent(kq, &kev, 1, NULL, 0, NULL);  // register

struct kevent events[16];
int n = kevent(kq, NULL, 0, events, 16, NULL);  // wait
```

`kqueue` is architecturally superior to epoll: changes and waits are in one syscall, it handles files (not just sockets), vnodes, signals, processes, timers, and user-defined events all in one API.

### 10.5 Performance Comparison

| API      | Time complexity per wakeup | FD limit    | OS             |
|----------|----------------------------|-------------|----------------|
| select   | O(nfds)                    | 1024        | All POSIX      |
| poll     | O(nfds)                    | Unlimited   | All POSIX      |
| epoll    | O(1) amortized             | Unlimited   | Linux          |
| kqueue   | O(1) amortized             | Unlimited   | BSD, macOS     |
| io_uring | O(1) amortized             | Unlimited   | Linux ≥ 5.1    |

---

## 11. Pipes and Named Pipes (FIFOs)

### 11.1 Anonymous Pipes

```c
int pipefd[2];
pipe2(pipefd, O_CLOEXEC);  // pipefd[0]=read end, pipefd[1]=write end

pid_t pid = fork();
if (pid == 0) {
    // Child: producer
    close(pipefd[0]);           // close unused read end
    write(pipefd[1], "hello", 5);
    close(pipefd[1]);
    exit(0);
} else {
    // Parent: consumer
    close(pipefd[1]);           // close unused write end
    char buf[16];
    ssize_t n = read(pipefd[0], buf, sizeof(buf));
    close(pipefd[0]);
}
```

**Important:** Must close the unused end in each process. If the parent forgets to close `pipefd[1]` (write end), the child's `read` will never get EOF — `f_count` on the write end is still 1 (parent holds it), so the kernel doesn't send EOF.

**Pipe buffer capacity:** Default 65536 bytes (16 pages) on Linux. Configurable per-pipe with `fcntl(pipefd[1], F_SETPIPE_SZ, new_size)`.

**Atomicity:** Writes ≤ `PIPE_BUF` (4096 bytes on Linux) are atomic. Multiple writers writing ≤ `PIPE_BUF` bytes will not interleave.

### 11.2 Named Pipes (FIFOs)

```c
mkfifo("/tmp/myfifo", 0600);

// Writer (can be a different process)
int wfd = open("/tmp/myfifo", O_WRONLY);  // blocks until reader opens

// Reader
int rfd = open("/tmp/myfifo", O_RDONLY);  // blocks until writer opens
```

FIFOs have no backing storage — data flows through kernel buffers. They appear in the filesystem for naming purposes only.

### 11.3 `splice` for Pipe-to-Socket Zero-Copy

```c
#define _GNU_SOURCE
#include <fcntl.h>
// Move data from fd_in to fd_out via a pipe (zero-copy in kernel)
ssize_t splice(int fd_in,  loff_t *off_in,
               int fd_out, loff_t *off_out,
               size_t len, unsigned int flags);
```

`splice` transfers data between FDs using the pipe as an intermediary without any user-space copies. Nginx uses this heavily.

---

## 12. Socket File Descriptors

### 12.1 Socket Creation and Lifecycle

```c
// TCP server skeleton
int sfd = socket(AF_INET6, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);

// Socket options (set before bind)
int yes = 1;
setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
setsockopt(sfd, SOL_SOCKET, SO_REUSEPORT, &yes, sizeof(yes));

struct sockaddr_in6 addr = {
    .sin6_family = AF_INET6,
    .sin6_port   = htons(8080),
    .sin6_addr   = in6addr_any,
};
bind(sfd, (struct sockaddr *)&addr, sizeof(addr));
listen(sfd, SOMAXCONN);  // SOMAXCONN = 4096 on modern Linux

// Accept loop
while (1) {
    struct sockaddr_storage client_addr;
    socklen_t addrlen = sizeof(client_addr);
    int cfd = accept4(sfd, (struct sockaddr *)&client_addr, &addrlen,
                      SOCK_CLOEXEC | SOCK_NONBLOCK);
    // handle cfd with epoll
}
```

`accept4` is the correct form — sets `SOCK_CLOEXEC | SOCK_NONBLOCK` atomically.

### 12.2 Important Socket Options

| Option                    | Level        | Effect                                          |
|---------------------------|--------------|-------------------------------------------------|
| `SO_REUSEADDR`            | `SOL_SOCKET` | Allow rebind after crash (TIME_WAIT bypass)     |
| `SO_REUSEPORT`            | `SOL_SOCKET` | Multiple sockets on same port (load balance)    |
| `SO_KEEPALIVE`            | `SOL_SOCKET` | TCP keepalives (detect dead peers)              |
| `TCP_NODELAY`             | `IPPROTO_TCP`| Disable Nagle's algorithm (low latency)         |
| `TCP_CORK`                | `IPPROTO_TCP`| Buffer until full or uncorked (throughput)      |
| `TCP_FASTOPEN`            | `IPPROTO_TCP`| Send data in SYN (reduces latency by 1 RTT)     |
| `SO_SNDBUF`/`SO_RCVBUF`  | `SOL_SOCKET` | Socket buffer sizes (auto-tuned by default)     |
| `SO_LINGER`               | `SOL_SOCKET` | Close behavior: wait for data vs RST            |
| `IP_TRANSPARENT`          | `IPPROTO_IP` | Bind to non-local IPs (transparent proxy)       |
| `SO_ATTACH_BPF`           | `SOL_SOCKET` | Attach eBPF program to socket for filtering     |

### 12.3 `SO_REUSEPORT` Internals

With `SO_REUSEPORT`, multiple sockets (even across processes) can bind to the same `IP:port`. The kernel load-balances incoming connections using a hash of the 4-tuple. This allows:
- Multiple worker processes each calling `accept()` without lock contention
- Zero-downtime restarts: new worker binds before old worker exits

### 12.4 `socketpair`

```c
int sv[2];
socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, sv);
```

Creates a connected pair of Unix sockets. Both ends can read and write. Used as a bidirectional pipe, and for FD passing.

---

## 13. Memory-Mapped Files (mmap)

### 13.1 The mmap Syscall

```c
#include <sys/mman.h>
void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);
int munmap(void *addr, size_t length);
int msync(void *addr, size_t length, int flags);
int madvise(void *addr, size_t length, int advice);
```

`mmap` maps a file (or anonymous memory) into the process's virtual address space. The kernel uses the same page cache pages as `read`/`write` — no double-buffering.

```c
// Map entire file read-only
int fd = open("data.bin", O_RDONLY | O_CLOEXEC);
struct stat st;
fstat(fd, &st);
void *p = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
close(fd);  // fd can be closed immediately after mmap; mapping persists
// Access data directly:
uint32_t val = *(uint32_t*)p;
munmap(p, st.st_size);
```

### 13.2 Protection Flags

| `prot`         | Effect                           |
|----------------|----------------------------------|
| `PROT_READ`    | Pages are readable               |
| `PROT_WRITE`   | Pages are writable               |
| `PROT_EXEC`    | Pages are executable             |
| `PROT_NONE`    | No access (guard pages)          |

### 13.3 Map Flags

| `flags`              | Meaning                                                          |
|----------------------|------------------------------------------------------------------|
| `MAP_SHARED`         | Changes are written back to the file, visible to other maps      |
| `MAP_PRIVATE`        | Copy-on-write; changes not written back                          |
| `MAP_ANONYMOUS`      | No file backing; `fd` must be -1                                 |
| `MAP_FIXED`          | Must map at exactly `addr`; dangerous — can clobber existing maps |
| `MAP_FIXED_NOREPLACE`| Like `MAP_FIXED` but fails if `addr` is already occupied         |
| `MAP_POPULATE`       | Prefault pages into memory (avoid page faults later)             |
| `MAP_HUGETLB`        | Use huge pages (2MB / 1GB) — reduces TLB pressure               |
| `MAP_LOCKED`         | Lock pages in RAM (no swap) — like `mlock`                       |
| `MAP_NORESERVE`      | Don't reserve swap space — risk of SIGBUS on access              |
| `MAP_GROWSDOWN`      | Stack-like: can grow toward lower addresses                      |

### 13.4 `madvise` Hints

```c
madvise(p, len, MADV_SEQUENTIAL);  // prefetch linearly
madvise(p, len, MADV_RANDOM);      // don't prefetch
madvise(p, len, MADV_WILLNEED);    // prefault now
madvise(p, len, MADV_DONTNEED);    // discard pages (free RAM)
madvise(p, len, MADV_FREE);        // pages can be reclaimed (lazy free)
madvise(p, len, MADV_HUGEPAGE);    // enable transparent huge pages
madvise(p, len, MADV_DONTFORK);    // child doesn't inherit these pages
```

### 13.5 `msync` for Durability

`MAP_SHARED` writes eventually flush but aren't durable without explicit sync:

```c
msync(p, len, MS_SYNC);   // blocking flush to storage
msync(p, len, MS_ASYNC);  // schedule flush, don't wait
```

### 13.6 `memfd_create`

Creates an anonymous file with no filesystem path. Useful for creating shareable anonymous memory:

```c
#define _GNU_SOURCE
#include <sys/mman.h>
int fd = memfd_create("mysharedmem", MFD_CLOEXEC | MFD_ALLOW_SEALING);
ftruncate(fd, 4096);
void *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
// Pass fd to another process via SCM_RIGHTS; they mmap it too — shared memory
```

---

## 14. sendfile and Zero-Copy I/O

### 14.1 `sendfile`

```c
#include <sys/sendfile.h>
ssize_t sendfile(int out_fd, int in_fd, off_t *offset, size_t count);
```

Copies data from `in_fd` (file) to `out_fd` (socket) entirely in kernel space — no data ever reaches userspace. Used by every high-performance HTTP server.

```c
// Serve a file over TCP
int file_fd = open("index.html", O_RDONLY | O_CLOEXEC);
struct stat st;
fstat(file_fd, &st);
off_t offset = 0;
while (offset < st.st_size) {
    ssize_t sent = sendfile(conn_fd, file_fd, &offset, st.st_size - offset);
    if (sent < 0) {
        if (errno == EAGAIN) { /* wait for EPOLLOUT */ }
        else { perror("sendfile"); break; }
    }
}
```

### 14.2 `copy_file_range`

```c
ssize_t copy_file_range(int fd_in,  loff_t *off_in,
                        int fd_out, loff_t *off_out,
                        size_t len, unsigned int flags);
```

Like `sendfile` but both FDs must be regular files. The kernel can use reflinks (COW sharing of extents) on filesystems like Btrfs, XFS, OCFS2 — a constant-time "copy" that shares blocks until written.

---

## 15. Passing File Descriptors over Unix Sockets (SCM_RIGHTS)

File descriptors can be transferred between unrelated processes (no parent-child relationship) using Unix domain sockets and ancillary data.

```c
// Sender
void send_fd(int sock, int fd_to_send) {
    struct msghdr msg = {0};
    char buf[CMSG_SPACE(sizeof(int))];
    memset(buf, 0, sizeof(buf));

    struct iovec iov;
    char dummy = 'x';
    iov.iov_base = &dummy;
    iov.iov_len  = 1;
    msg.msg_iov    = &iov;
    msg.msg_iovlen = 1;

    msg.msg_control    = buf;
    msg.msg_controllen = sizeof(buf);

    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    cmsg->cmsg_level = SOL_SOCKET;
    cmsg->cmsg_type  = SCM_RIGHTS;
    cmsg->cmsg_len   = CMSG_LEN(sizeof(int));
    memcpy(CMSG_DATA(cmsg), &fd_to_send, sizeof(int));

    sendmsg(sock, &msg, 0);
}

// Receiver
int recv_fd(int sock) {
    struct msghdr msg = {0};
    char buf[CMSG_SPACE(sizeof(int))];
    memset(buf, 0, sizeof(buf));

    struct iovec iov;
    char dummy;
    iov.iov_base = &dummy;
    iov.iov_len  = 1;
    msg.msg_iov    = &iov;
    msg.msg_iovlen = 1;
    msg.msg_control    = buf;
    msg.msg_controllen = sizeof(buf);

    recvmsg(sock, &msg, 0);

    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    int received_fd;
    memcpy(&received_fd, CMSG_DATA(cmsg), sizeof(int));
    return received_fd;
}
```

The kernel copies the `struct file*` pointer into the receiving process's FD table, incrementing `f_count`. The receiving process gets a **new FD number** pointing to the same open file description. This is how:
- `systemd` passes pre-bound sockets to services
- Privilege-separated daemons hand off accepted connections
- Chrome passes audio/GPU FDs to sandboxed processes

---

## 16. Inspecting Descriptors: /proc and lsof

### 16.1 `/proc/self/fd`

```bash
ls -la /proc/self/fd
# lrwxrwxrwx 1 user user 0 fd/0 -> /dev/pts/0
# lrwxrwxrwx 1 user user 0 fd/1 -> /dev/pts/0
# lrwxrwxrwx 1 user user 0 fd/3 -> /path/to/file
# lrwxrwxrwx 1 user user 0 fd/4 -> socket:[12345]
# lrwxrwxrwx 1 user user 0 fd/5 -> pipe:[67890]
```

### 16.2 `/proc/self/fdinfo`

```bash
cat /proc/self/fdinfo/3
# pos:    0
# flags:  0100002  (O_RDWR | O_CLOEXEC in octal)
# mnt_id: 25
```

### 16.3 `/proc/<pid>/maps` for mmap

Shows all virtual memory mappings including mmap'd files.

### 16.4 `lsof`

```bash
lsof -p <pid>          # all FDs for a process
lsof -i TCP:8080       # all processes with that port open
lsof +D /var/log       # all FDs under a directory
lsof -u root           # all FDs for user root
lsof -d 0-9            # FDs numbered 0 through 9
```

### 16.5 `ss` and `netstat` for Sockets

```bash
ss -tlnp               # TCP listening sockets with PIDs
ss -s                  # socket statistics summary
ss -o state established '( dport = :80 or sport = :80 )'
```

---

## 17. File Descriptor Leaks

### 17.1 What Causes FD Leaks?

1. `open`/`socket`/`accept` without matching `close`
2. Exception/early-return paths that skip `close`
3. Forgetting to close the unused pipe end after `fork`
4. Libraries that open FDs (OpenSSL, libcurl) but you don't close them properly
5. `dup` or `accept4` loops that don't close on error
6. Long-lived processes that open files in request handlers

### 17.2 Symptoms

```bash
# Process hits EMFILE (too many open files)
open: Too many open files
accept: Too many open files

# Check
ls /proc/<pid>/fd | wc -l        # count open FDs
cat /proc/<pid>/limits | grep files
```

### 17.3 Detection Tools

```bash
# lsof with count summary
lsof -p <pid> | awk '{print $5}' | sort | uniq -c | sort -rn

# strace: trace open/close calls
strace -e trace=open,openat,close,socket,accept4 -p <pid>

# Valgrind with --track-fds
valgrind --track-fds=yes ./myprogram

# AddressSanitizer (detects use-after-close, not leaks directly)
# LeakSanitizer + custom FD tracking
```

### 17.4 Detecting in Code: FD Accounting

```c
// Simple FD watermark tracker (debug builds only)
#ifdef DEBUG
#include <stdio.h>
#include <dirent.h>
int count_open_fds(void) {
    DIR *d = opendir("/proc/self/fd");
    int count = 0;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL)
        if (ent->d_name[0] != '.') count++;
    closedir(d);
    return count - 1;  // subtract the dirfd itself
}
#define FD_WATERMARK_START int _fd_before = count_open_fds()
#define FD_WATERMARK_END \
    do { int _fd_after = count_open_fds(); \
         if (_fd_after != _fd_before) \
             fprintf(stderr, "FD LEAK: %d FDs leaked at %s:%d\n", \
                     _fd_after - _fd_before, __FILE__, __LINE__); \
    } while(0)
#else
#define FD_WATERMARK_START
#define FD_WATERMARK_END
#endif
```

---

## 18. C Implementation: Full Reference

### File: `fd_demo.c`

```c
/*
 * fd_demo.c — Comprehensive file descriptor demonstration in C
 * Compile: gcc -O2 -Wall -Wextra -o fd_demo fd_demo.c
 * Run:     ./fd_demo
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <sys/epoll.h>
#include <sys/sendfile.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <assert.h>

/* ─── 1. Basic open/read/write/close ─── */

static void demo_basic_io(void) {
    puts("\n=== 1. Basic I/O ===");

    // O_CLOEXEC: always set. O_TMPFILE: no dir entry created.
    int fd = open("/tmp/fd_demo_test.txt",
                  O_RDWR | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd == -1) { perror("open"); return; }

    const char *msg = "Hello, file descriptors!\n";
    ssize_t written = write(fd, msg, strlen(msg));
    printf("Written: %zd bytes, fd=%d\n", written, fd);

    // Rewind using lseek
    if (lseek(fd, 0, SEEK_SET) == -1) { perror("lseek"); goto done; }

    char buf[64];
    ssize_t nread = read(fd, buf, sizeof(buf) - 1);
    buf[nread] = '\0';
    printf("Read back: %s", buf);

    // fstat: file metadata without a path
    struct stat st;
    fstat(fd, &st);
    printf("File size: %lld bytes, inode: %llu\n",
           (long long)st.st_size, (unsigned long long)st.st_ino);

done:
    if (close(fd) == -1) perror("close");  // always check!
    unlink("/tmp/fd_demo_test.txt");
}

/* ─── 2. pread/pwrite: positional, thread-safe ─── */

static void demo_pread_pwrite(void) {
    puts("\n=== 2. pread/pwrite ===");

    int fd = open("/tmp/fd_demo_pos.bin",
                  O_RDWR | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd == -1) { perror("open"); return; }

    uint64_t vals[4] = {0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0xABCDEF01};
    pwrite(fd, vals, sizeof(vals), 0);

    // Read middle two words without seeking
    uint64_t out[2];
    pread(fd, out, sizeof(out), sizeof(uint64_t));
    printf("pread[1]=%#llx, pread[2]=%#llx\n",
           (unsigned long long)out[0], (unsigned long long)out[1]);

    close(fd);
    unlink("/tmp/fd_demo_pos.bin");
}

/* ─── 3. dup2: stdout redirection ─── */

static void demo_dup2(void) {
    puts("\n=== 3. dup2 redirection ===");

    int fd = open("/tmp/fd_demo_dup.txt",
                  O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd == -1) { perror("open"); return; }

    // Save original stdout
    int saved_stdout = dup(STDOUT_FILENO);
    dup2(fd, STDOUT_FILENO);
    close(fd);

    // This goes to the file, not the terminal
    printf("This line is in the file.\n");
    fflush(stdout);

    // Restore stdout
    dup2(saved_stdout, STDOUT_FILENO);
    close(saved_stdout);

    printf("Back to terminal.\n");

    // Verify
    int verify = open("/tmp/fd_demo_dup.txt", O_RDONLY | O_CLOEXEC);
    char buf[64];
    ssize_t n = read(verify, buf, sizeof(buf)-1);
    buf[n] = '\0';
    printf("File contains: %s", buf);
    close(verify);
    unlink("/tmp/fd_demo_dup.txt");
}

/* ─── 4. Pipe: parent-child communication ─── */

static void demo_pipe(void) {
    puts("\n=== 4. Pipe ===");

    int pipefd[2];
    if (pipe2(pipefd, O_CLOEXEC) == -1) { perror("pipe2"); return; }

    pid_t pid = fork();
    if (pid == -1) { perror("fork"); return; }

    if (pid == 0) {
        // Child: write end
        close(pipefd[0]);  // MUST close read end in child
        const char *msg = "data from child";
        write(pipefd[1], msg, strlen(msg));
        close(pipefd[1]);
        exit(0);
    } else {
        // Parent: read end
        close(pipefd[1]);  // MUST close write end in parent
        char buf[64];
        ssize_t n = read(pipefd[0], buf, sizeof(buf)-1);
        buf[n] = '\0';
        printf("Parent received: '%s'\n", buf);
        close(pipefd[0]);
        waitpid(pid, NULL, 0);
    }
}

/* ─── 5. mmap: memory-mapped file ─── */

static void demo_mmap(void) {
    puts("\n=== 5. mmap ===");

    const char *path = "/tmp/fd_demo_mmap.bin";
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd == -1) { perror("open"); return; }

    const size_t SIZE = 4096;
    ftruncate(fd, SIZE);  // set size before mmap

    uint8_t *p = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); close(fd); return; }

    close(fd);  // fd can be closed after mmap

    memset(p, 0xAB, SIZE);

    // Flush to disk
    if (msync(p, SIZE, MS_SYNC) == -1) perror("msync");

    // Verify via read
    int rfd = open(path, O_RDONLY | O_CLOEXEC);
    uint8_t buf[4];
    read(rfd, buf, sizeof(buf));
    printf("mmap wrote 0x%02X, file has 0x%02X\n", 0xAB, buf[0]);
    close(rfd);

    munmap(p, SIZE);
    unlink(path);
}

/* ─── 6. epoll: non-blocking I/O multiplexing ─── */

static void demo_epoll(void) {
    puts("\n=== 6. epoll ===");

    int pipefd[2];
    pipe2(pipefd, O_CLOEXEC | O_NONBLOCK);

    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd == -1) { perror("epoll_create1"); return; }

    struct epoll_event ev = {
        .events = EPOLLIN | EPOLLET,
        .data.fd = pipefd[0],
    };
    epoll_ctl(epfd, EPOLL_CTL_ADD, pipefd[0], &ev);

    // Write to pipe in a child thread (simulate async data)
    pid_t pid = fork();
    if (pid == 0) {
        close(epfd);
        close(pipefd[0]);
        usleep(100000);  // 100ms
        write(pipefd[1], "event!", 6);
        close(pipefd[1]);
        exit(0);
    }

    close(pipefd[1]);  // parent doesn't write

    struct epoll_event events[4];
    printf("Waiting on epoll...\n");
    int n = epoll_wait(epfd, events, 4, 2000);  // 2s timeout
    if (n > 0) {
        char buf[16];
        ssize_t r = read(pipefd[0], buf, sizeof(buf)-1);
        buf[r] = '\0';
        printf("epoll got: '%s'\n", buf);
    }

    close(pipefd[0]);
    close(epfd);
    waitpid(pid, NULL, 0);
}

/* ─── 7. writev: scatter-gather I/O ─── */

static void demo_writev(void) {
    puts("\n=== 7. writev (scatter-gather) ===");

    int fd = open("/tmp/fd_demo_writev.txt",
                  O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);

    struct iovec iov[3];
    const char *header = "HEADER:";
    const char *body   = "body content";
    const char *footer = ":FOOTER\n";

    iov[0].iov_base = (void*)header; iov[0].iov_len = strlen(header);
    iov[1].iov_base = (void*)body;   iov[1].iov_len = strlen(body);
    iov[2].iov_base = (void*)footer; iov[2].iov_len = strlen(footer);

    ssize_t total = writev(fd, iov, 3);
    printf("writev wrote %zd bytes in one syscall\n", total);

    close(fd);
    unlink("/tmp/fd_demo_writev.txt");
}

/* ─── 8. FD limit query ─── */

static void demo_fd_limits(void) {
    puts("\n=== 8. FD limits ===");

    struct rlimit rl;
    getrlimit(RLIMIT_NOFILE, &rl);
    printf("Soft limit: %lu, Hard limit: %lu\n",
           (unsigned long)rl.rlim_cur, (unsigned long)rl.rlim_max);

    // Count currently open FDs
    DIR *d = opendir("/proc/self/fd");
    int count = 0;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL)
        if (ent->d_name[0] != '.') count++;
    closedir(d);
    printf("Currently open FDs (approx): %d\n", count);
}

/* ─── 9. O_TMPFILE: anonymous temp file ─── */

static void demo_tmpfile(void) {
    puts("\n=== 9. O_TMPFILE ===");

    // Creates a file with no directory entry (unlinked immediately)
    int fd = open("/tmp", O_RDWR | O_TMPFILE | O_CLOEXEC, 0600);
    if (fd == -1) { perror("open O_TMPFILE (may need Linux 3.11+)"); return; }

    write(fd, "secret data", 11);

    // Give it a name when ready (atomically):
    // linkat(fd, "", AT_FDCWD, "/tmp/final_name.txt", AT_EMPTY_PATH);
    // Without linkat, it disappears when fd is closed

    printf("O_TMPFILE fd=%d, no directory entry exists\n", fd);
    close(fd);
}

/* ─── main ─── */

int main(void) {
    demo_basic_io();
    demo_pread_pwrite();
    demo_dup2();
    demo_pipe();
    demo_mmap();
    demo_epoll();
    demo_writev();
    demo_fd_limits();
    demo_tmpfile();
    puts("\nAll demos complete.");
    return 0;
}
```

### File: `fd_echo_server.c` — Production Echo Server

```c
/*
 * fd_echo_server.c — Production-grade non-blocking echo server using epoll
 * Compile: gcc -O2 -Wall -Wextra -o echo_server fd_echo_server.c
 * Test:    nc localhost 8080
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <signal.h>

#define MAX_EVENTS   64
#define LISTEN_PORT  8080
#define BACKLOG      SOMAXCONN
#define BUF_SIZE     4096

static int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static int create_listener(void) {
    int fd = socket(AF_INET6, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    if (fd == -1) { perror("socket"); exit(1); }

    int yes = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
    setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &yes, sizeof(yes));

    struct sockaddr_in6 addr = {
        .sin6_family = AF_INET6,
        .sin6_port   = htons(LISTEN_PORT),
        .sin6_addr   = in6addr_any,
    };
    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        perror("bind"); exit(1);
    }
    if (listen(fd, BACKLOG) == -1) {
        perror("listen"); exit(1);
    }
    return fd;
}

static volatile int running = 1;

static void sighandler(int sig) { (void)sig; running = 0; }

int main(void) {
    signal(SIGPIPE, SIG_IGN);   // don't die on broken pipe
    signal(SIGTERM, sighandler);
    signal(SIGINT,  sighandler);

    int listen_fd = create_listener();
    printf("Listening on [::]:%d\n", LISTEN_PORT);

    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd == -1) { perror("epoll_create1"); exit(1); }

    struct epoll_event ev = {
        .events  = EPOLLIN,
        .data.fd = listen_fd,
    };
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    struct epoll_event events[MAX_EVENTS];
    char buf[BUF_SIZE];

    while (running) {
        int n = epoll_wait(epfd, events, MAX_EVENTS, 1000);
        if (n == -1) {
            if (errno == EINTR) continue;
            perror("epoll_wait"); break;
        }

        for (int i = 0; i < n; i++) {
            int fd = events[i].data.fd;

            if (fd == listen_fd) {
                // Accept all pending connections
                while (1) {
                    int cfd = accept4(listen_fd, NULL, NULL,
                                      SOCK_CLOEXEC | SOCK_NONBLOCK);
                    if (cfd == -1) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                        perror("accept4"); break;
                    }
                    // Disable Nagle for low-latency echo
                    int yes = 1;
                    setsockopt(cfd, IPPROTO_TCP, TCP_NODELAY, &yes, sizeof(yes));

                    struct epoll_event cev = {
                        .events  = EPOLLIN | EPOLLET | EPOLLRDHUP,
                        .data.fd = cfd,
                    };
                    epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &cev);
                    printf("Accepted fd=%d\n", cfd);
                }
            } else {
                // Client data or disconnect
                if (events[i].events & (EPOLLHUP | EPOLLERR | EPOLLRDHUP)) {
                    printf("Client fd=%d disconnected\n", fd);
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);
                    continue;
                }

                if (events[i].events & EPOLLIN) {
                    // Edge-triggered: drain until EAGAIN
                    while (1) {
                        ssize_t nr = read(fd, buf, sizeof(buf));
                        if (nr > 0) {
                            // Echo back
                            ssize_t sent = 0;
                            while (sent < nr) {
                                ssize_t sw = write(fd, buf + sent, nr - sent);
                                if (sw < 0) {
                                    if (errno == EAGAIN) break;
                                    goto disconnect;
                                }
                                sent += sw;
                            }
                        } else if (nr == 0 || (nr == -1 && errno != EAGAIN)) {
                            goto disconnect;
                        } else {
                            break; // EAGAIN
                        }
                    }
                    continue;
disconnect:
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);
                }
            }
        }
    }

    close(listen_fd);
    close(epfd);
    puts("Server shut down cleanly.");
    return 0;
}
```

---

## 19. Rust Implementation: Safe and Unsafe

### 19.1 The Rust I/O Type Hierarchy

```
std::fs::File
    ↓  implements
AsRawFd        → fn as_raw_fd(&self) -> RawFd     // borrow without transfer
IntoRawFd      → fn into_raw_fd(self) -> RawFd     // consume and take ownership
FromRawFd      → unsafe fn from_raw_fd(fd: RawFd) -> Self

std::os::unix::io::OwnedFd   (Rust 1.63+)  — owned, auto-closes
std::os::unix::io::BorrowedFd<'fd>         — borrowed view, lifetime-checked
```

The new `OwnedFd` / `BorrowedFd` types (via the `io-safety` RFC) close the unsafety gaps in the old `RawFd` API.

### File: `src/main.rs` — Comprehensive Rust FD Demos

```rust
// Cargo.toml:
// [dependencies]
// nix = { version = "0.27", features = ["fs", "io", "poll", "socket", "net", "event", "mman", "process"] }
// tokio = { version = "1", features = ["full"] }

use std::fs::{File, OpenOptions};
use std::io::{self, Read, Write, Seek, SeekFrom};
use std::os::unix::io::{AsRawFd, FromRawFd, IntoRawFd, OwnedFd, BorrowedFd};
use std::os::unix::fs::OpenOptionsExt;

fn main() -> io::Result<()> {
    demo_basic_io()?;
    demo_raw_fd()?;
    demo_owned_fd()?;
    demo_mmap()?;
    demo_pipe()?;
    demo_nonblocking()?;
    Ok(())
}

// ─── 1. Basic safe I/O ───────────────────────────────────────────────────────

fn demo_basic_io() -> io::Result<()> {
    println!("\n=== 1. Basic safe I/O ===");

    // OpenOptions + custom_flags sets O_CLOEXEC (always on in Rust on Unix)
    let path = "/tmp/rust_fd_demo.txt";
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(true)
        .mode(0o600)        // from OpenOptionsExt
        .open(path)?;

    let fd = file.as_raw_fd();
    println!("Opened fd={fd}");

    file.write_all(b"Rust file descriptor demo\n")?;
    file.seek(SeekFrom::Start(0))?;

    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    print!("Read: {contents}");

    // File is closed when it drops — RAII guarantees no leak
    std::fs::remove_file(path)?;
    Ok(())
}

// ─── 2. RawFd: escape hatch for syscalls ─────────────────────────────────────

fn demo_raw_fd() -> io::Result<()> {
    println!("\n=== 2. RawFd & pread ===");

    let file = File::open("/etc/hostname")?;
    let fd: std::os::unix::io::RawFd = file.as_raw_fd();

    // Call pread directly via libc
    let mut buf = [0u8; 64];
    let n = unsafe {
        libc::pread(fd, buf.as_mut_ptr() as *mut libc::c_void, buf.len(), 0)
    };
    if n < 0 {
        return Err(io::Error::last_os_error());
    }
    println!("pread hostname: {}", std::str::from_utf8(&buf[..n as usize]).unwrap().trim());

    // file drops here, fd becomes invalid — that's fine, we didn't store RawFd separately
    Ok(())
}

// ─── 3. OwnedFd: safe ownership transfer ─────────────────────────────────────

fn demo_owned_fd() -> io::Result<()> {
    println!("\n=== 3. OwnedFd ownership ===");

    let file = File::create("/tmp/owned_fd_test.txt")?;
    let raw = file.into_raw_fd();  // File dropped, fd NOT closed

    // Wrap in OwnedFd — now the type system tracks ownership
    let owned: OwnedFd = unsafe { OwnedFd::from_raw_fd(raw) };

    // Borrow it safely
    let borrowed: BorrowedFd<'_> = owned.as_fd();
    println!("OwnedFd={}, BorrowedFd={}", owned.as_raw_fd(), borrowed.as_raw_fd());

    // Turn back into File for high-level I/O
    let mut file2: File = File::from(owned);  // OwnedFd → File
    file2.write_all(b"OwnedFd demo\n")?;

    std::fs::remove_file("/tmp/owned_fd_test.txt")?;
    Ok(())
}

// ─── 4. mmap via nix ─────────────────────────────────────────────────────────

fn demo_mmap() -> io::Result<()> {
    println!("\n=== 4. mmap ===");

    use nix::sys::mman::{mmap, munmap, msync, MapFlags, ProtFlags, MsFlags};
    use std::num::NonZeroUsize;

    let path = "/tmp/rust_mmap_demo.bin";
    let file = OpenOptions::new()
        .read(true).write(true).create(true).truncate(true)
        .mode(0o600)
        .open(path)?;
    let fd = file.as_raw_fd();

    let size = 4096usize;
    nix::unistd::ftruncate(unsafe { OwnedFd::from_raw_fd(fd) }, size as i64)
        .map_err(|e| io::Error::from_raw_os_error(e as i32))?;

    // NOTE: We must not drop `file` before we use fd in mmap.
    // Here fd is still valid because `file` is alive.
    let ptr = unsafe {
        mmap::<File>(
            None,
            NonZeroUsize::new(size).unwrap(),
            ProtFlags::PROT_READ | ProtFlags::PROT_WRITE,
            MapFlags::MAP_SHARED,
            Some(&file),
            0,
        ).map_err(|e| io::Error::from_raw_os_error(e as i32))?
    };

    // Write to mapped memory
    unsafe {
        let slice = std::slice::from_raw_parts_mut(ptr.as_ptr() as *mut u8, size);
        slice[..5].copy_from_slice(b"HELLO");
        msync(ptr, size, MsFlags::MS_SYNC)
            .map_err(|e| io::Error::from_raw_os_error(e as i32))?;
    }

    // Verify by reading the file normally
    let mut verify = File::open(path)?;
    let mut buf = [0u8; 5];
    verify.read_exact(&mut buf)?;
    println!("mmap wrote: {}", std::str::from_utf8(&buf).unwrap());

    unsafe {
        munmap(ptr, size).map_err(|e| io::Error::from_raw_os_error(e as i32))?;
    }
    std::fs::remove_file(path)?;
    Ok(())
}

// ─── 5. Pipe with thread communication ───────────────────────────────────────

fn demo_pipe() -> io::Result<()> {
    println!("\n=== 5. Pipe ===");

    use nix::unistd::{pipe2, read, write};
    use nix::fcntl::OFlag;

    let (read_fd, write_fd) = pipe2(OFlag::O_CLOEXEC)
        .map_err(|e| io::Error::from_raw_os_error(e as i32))?;

    let write_owned: OwnedFd = unsafe { OwnedFd::from_raw_fd(write_fd) };
    let read_owned:  OwnedFd = unsafe { OwnedFd::from_raw_fd(read_fd) };

    let handle = std::thread::spawn(move || {
        let raw = write_owned.as_raw_fd();
        let msg = b"hello from thread";
        unsafe { libc::write(raw, msg.as_ptr() as *const libc::c_void, msg.len()) };
        // write_owned dropped here → pipe write end closed
    });

    let mut buf = [0u8; 64];
    let n = unsafe {
        libc::read(read_owned.as_raw_fd(),
                   buf.as_mut_ptr() as *mut libc::c_void, buf.len())
    };
    if n > 0 {
        println!("Pipe received: {}", std::str::from_utf8(&buf[..n as usize]).unwrap());
    }

    handle.join().unwrap();
    Ok(())
}

// ─── 6. Non-blocking I/O with poll ───────────────────────────────────────────

fn demo_nonblocking() -> io::Result<()> {
    println!("\n=== 6. Nonblocking I/O ===");

    use nix::unistd::pipe2;
    use nix::fcntl::OFlag;
    use nix::poll::{poll, PollFd, PollFlags};

    let (rfd, wfd) = pipe2(OFlag::O_CLOEXEC | OFlag::O_NONBLOCK)
        .map_err(|e| io::Error::from_raw_os_error(e as i32))?;

    let rfd_owned: OwnedFd = unsafe { OwnedFd::from_raw_fd(rfd) };
    let wfd_owned: OwnedFd = unsafe { OwnedFd::from_raw_fd(wfd) };

    // Non-blocking read — will get EAGAIN immediately
    let mut buf = [0u8; 16];
    let n = unsafe {
        libc::read(rfd_owned.as_raw_fd(),
                   buf.as_mut_ptr() as *mut libc::c_void, buf.len())
    };
    println!("Non-blocking read returned {n} (errno={})",
             if n < 0 { io::Error::last_os_error().raw_os_error().unwrap_or(0) } else { 0 });

    // Write some data then poll for readability
    let msg = b"async data";
    unsafe {
        libc::write(wfd_owned.as_raw_fd(),
                    msg.as_ptr() as *const libc::c_void, msg.len());
    }

    let mut fds = [PollFd::new(rfd_owned.as_fd(), PollFlags::POLLIN)];
    let ready = poll(&mut fds, 1000).map_err(|e| io::Error::from_raw_os_error(e as i32))?;
    println!("poll returned {ready} ready FD(s)");

    if fds[0].revents().unwrap_or(PollFlags::empty()).contains(PollFlags::POLLIN) {
        let n = unsafe {
            libc::read(rfd_owned.as_raw_fd(),
                       buf.as_mut_ptr() as *mut libc::c_void, buf.len())
        };
        println!("After poll read: {}", std::str::from_utf8(&buf[..n as usize]).unwrap());
    }

    Ok(())
}
```

### File: `src/bin/tokio_server.rs` — Async Tokio Echo Server

```rust
// Cargo.toml:
// [dependencies]
// tokio = { version = "1", features = ["full"] }

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;
use std::os::unix::io::AsRawFd;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let listener = TcpListener::bind("[::]:8080").await?;
    println!("Listening on fd={}", listener.as_raw_fd());

    loop {
        let (mut socket, addr) = listener.accept().await?;
        println!("Client {} on fd={}", addr, socket.as_raw_fd());

        tokio::spawn(async move {
            let mut buf = vec![0u8; 4096];
            loop {
                match socket.read(&mut buf).await {
                    Ok(0) => break,  // EOF
                    Ok(n) => {
                        if socket.write_all(&buf[..n]).await.is_err() { break; }
                    }
                    Err(_) => break,
                }
            }
        });
    }
}
```

### File: `src/bin/safe_fd_wrapper.rs` — Safe FD Abstractions

```rust
use std::os::unix::io::{AsRawFd, OwnedFd, FromRawFd};
use std::io;

/// A file descriptor that is guaranteed to be valid for the lifetime of this struct.
/// Wraps OwnedFd to add domain-specific checks.
pub struct SafeFd {
    inner: OwnedFd,
}

impl SafeFd {
    /// Open a file with mandatory O_CLOEXEC.
    pub fn open(path: &str, flags: libc::c_int, mode: libc::mode_t) -> io::Result<Self> {
        let flags = flags | libc::O_CLOEXEC;  // enforce CLOEXEC
        let fd = unsafe { libc::open(path.as_ptr() as *const libc::c_char, flags, mode) };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Self { inner: unsafe { OwnedFd::from_raw_fd(fd) } })
    }

    /// Borrow the raw fd for syscalls without transferring ownership.
    pub fn as_raw(&self) -> libc::c_int {
        self.inner.as_raw_fd()
    }

    /// Read at offset without moving f_pos (thread-safe).
    pub fn pread(&self, buf: &mut [u8], offset: i64) -> io::Result<usize> {
        let n = unsafe {
            libc::pread(
                self.as_raw(),
                buf.as_mut_ptr() as *mut libc::c_void,
                buf.len(),
                offset,
            )
        };
        if n < 0 { Err(io::Error::last_os_error()) } else { Ok(n as usize) }
    }

    /// Write all bytes at offset (loops on short writes).
    pub fn pwrite_all(&self, buf: &[u8], offset: i64) -> io::Result<()> {
        let mut written = 0usize;
        while written < buf.len() {
            let n = unsafe {
                libc::pwrite(
                    self.as_raw(),
                    buf[written..].as_ptr() as *const libc::c_void,
                    buf.len() - written,
                    offset + written as i64,
                )
            };
            match n {
                n if n > 0 => written += n as usize,
                n if n < 0 => {
                    let err = io::Error::last_os_error();
                    if err.raw_os_error() == Some(libc::EINTR) { continue; }
                    return Err(err);
                }
                _ => return Err(io::Error::new(io::ErrorKind::WriteZero, "write returned 0")),
            }
        }
        Ok(())
    }

    /// Duplicate the FD, returning a new OwnedFd.
    pub fn try_clone(&self) -> io::Result<SafeFd> {
        let newfd = unsafe { libc::fcntl(self.as_raw(), libc::F_DUPFD_CLOEXEC, 0) };
        if newfd < 0 { return Err(io::Error::last_os_error()); }
        Ok(Self { inner: unsafe { OwnedFd::from_raw_fd(newfd) } })
    }
}

// No explicit close needed — OwnedFd's Drop calls close(2).

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_pread_pwrite() {
        let path = "/tmp/rust_safe_fd_test.bin";
        let fd = SafeFd::open(path,
            libc::O_RDWR | libc::O_CREAT | libc::O_TRUNC, 0o600).unwrap();

        let data = b"test data for pread/pwrite";
        fd.pwrite_all(data, 0).unwrap();

        let mut buf = vec![0u8; data.len()];
        let n = fd.pread(&mut buf, 0).unwrap();
        assert_eq!(n, data.len());
        assert_eq!(&buf, data);

        std::fs::remove_file(path).unwrap();
    }

    #[test]
    fn test_clone_shares_description() {
        let path = "/tmp/rust_clone_test.txt";
        let fd1 = SafeFd::open(path,
            libc::O_RDWR | libc::O_CREAT | libc::O_TRUNC, 0o600).unwrap();
        let fd2 = fd1.try_clone().unwrap();

        // Both point to same open file description
        assert_ne!(fd1.as_raw(), fd2.as_raw());  // different FD numbers
        // Write via fd1, read via fd2 at same position (shared f_pos via dup)
        // (Positional tests are cleaner with pread/pwrite)

        std::fs::remove_file(path).unwrap();
    }
}
```

### 19.2 Rust FD Safety Rules

```rust
// ❌ WRONG: double-close
let file = File::open("x").unwrap();
let raw = file.as_raw_fd();
let _another = unsafe { File::from_raw_fd(raw) };
// file drops → close(raw)
// _another drops → close(raw) AGAIN — undefined behavior!

// ✅ CORRECT: into_raw_fd transfers ownership
let file = File::open("x").unwrap();
let raw = file.into_raw_fd();  // file is consumed, won't close
let owned = unsafe { OwnedFd::from_raw_fd(raw) };  // now owned

// ❌ WRONG: storing RawFd beyond the source's lifetime
let raw: RawFd;
{
    let file = File::open("x").unwrap();
    raw = file.as_raw_fd();
}  // file drops → fd closed → raw is stale!
let mut buf = [0u8; 16];
unsafe { libc::read(raw, buf.as_mut_ptr() as *mut _, 16) };  // UB!

// ✅ CORRECT: use BorrowedFd<'_> which is lifetime-gated
fn needs_fd<'a>(fd: BorrowedFd<'a>) { /* can't outlive source */ }
let file = File::open("x").unwrap();
needs_fd(file.as_fd());  // BorrowedFd lifetime tied to `file`
```

### 19.3 Tokio's FD Internals

Tokio wraps OS sockets in `mio::net::TcpStream`, which:
1. Sets `O_NONBLOCK` on the socket
2. Registers it with `epoll`/`kqueue` via `mio::Registry`
3. Associates it with a Tokio `Waker`
4. When `epoll_wait` fires, the Waker is called → the relevant `async` task is scheduled

`tokio::net::TcpStream::as_raw_fd()` gives the underlying FD, usable with `unsafe` syscalls.

`AsyncFd<T>` is Tokio's low-level primitive for wrapping any nonblocking FD into an async-compatible type:

```rust
use tokio::io::unix::AsyncFd;
use std::os::unix::io::OwnedFd;

let fd: OwnedFd = /* some nonblocking fd */;
let async_fd = AsyncFd::new(fd)?;

loop {
    let mut guard = async_fd.readable().await?;  // async wait for POLLIN
    guard.try_io(|inner| {
        let n = unsafe {
            libc::read(inner.as_raw_fd(), buf.as_mut_ptr() as *mut _, buf.len())
        };
        if n < 0 {
            let err = std::io::Error::last_os_error();
            if err.raw_os_error() == Some(libc::EAGAIN) {
                return Err(err);  // tell AsyncFd to re-arm
            }
        }
        Ok(n)
    })?;
}
```

---

## 20. Go Implementation: Internals and Patterns

### 20.1 Go's FD Abstraction Stack

```
User code
    │
    ▼
os.File
    │  wraps
    ▼
internal/poll.FD        ← Go runtime's FD type
    │  contains
    ▼
poll.fdMutex            ← concurrent access guard
poll.pollDesc           ← netpoller hook
    │  calls
    ▼
runtime/netpoll_epoll.go  (Linux)
runtime/netpoll_kqueue.go (BSD/macOS)
    │  calls
    ▼
epoll_wait / kqueue syscall
```

Every `os.File` is a thin wrapper around `internal/poll.FD`. The Go runtime runs a **network poller** goroutine (or uses OS threads with epoll/kqueue) to multiplex all I/O. When `Read`/`Write` would block, the goroutine is parked and the M (OS thread) picks up another runnable G.

### 20.2 `os.NewFile` — Wrapping an Existing FD

```go
// os.NewFile takes ownership of the fd
// name is for error messages only; it doesn't affect behavior
file := os.NewFile(uintptr(fd), "myfile")
if file == nil {
    // fd was negative
}
```

**Critical:** After `os.NewFile`, calling `file.Close()` will close the underlying OS fd. Don't close it elsewhere.

### 20.3 Finalizers and FD Lifecycle

Go's `os.File` has a runtime finalizer set via `runtime.SetFinalizer`. If the file is GC'd without being explicitly closed, the finalizer calls `Close()`. This is a **safety net, not a guarantee**:
- The GC may not run before the process opens too many files
- Finalizers don't run if the program exits via `os.Exit`
- **Always** call `defer f.Close()` explicitly

### File: `fd_demo.go` — Comprehensive Go FD Demos

```go
// fd_demo.go
// Run: go run fd_demo.go

//go:build linux

package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"runtime"
	"syscall"
	"time"
	"unsafe"
)

func main() {
	demoBasicIO()
	demoRawSyscall()
	demoPipe()
	demoSocketPair()
	demoNonblockingPoll()
	demoEpoll()
	demoFDInheritance()
	demoMmap()
	demoFDLimits()
}

// ─── 1. Basic os.File I/O ──────────────────────────────────────────────────

func demoBasicIO() {
	fmt.Println("\n=== 1. Basic os.File I/O ===")

	path := "/tmp/go_fd_demo.txt"
	// os.OpenFile mirrors open(2); O_CLOEXEC is always set by Go on Unix
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		if err := f.Close(); err != nil { // always check close error
			log.Printf("close error: %v", err)
		}
		os.Remove(path)
	}()

	fmt.Printf("Opened fd=%d\n", f.Fd()) // Fd() returns uintptr

	if _, err := f.WriteString("Hello from Go!\n"); err != nil {
		log.Fatal(err)
	}

	// Seek to start
	if _, err := f.Seek(0, io.SeekStart); err != nil {
		log.Fatal(err)
	}

	content, err := io.ReadAll(f)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Read: %s", content)

	// fstat
	info, _ := f.Stat()
	fmt.Printf("Size=%d Mode=%v\n", info.Size(), info.Mode())
}

// ─── 2. Raw syscalls ────────────────────────────────────────────────────────

func demoRawSyscall() {
	fmt.Println("\n=== 2. Raw syscalls (pread) ===")

	f, err := os.Open("/etc/hostname")
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	// Explicit pread(2) syscall
	buf := make([]byte, 64)
	n, _, errno := syscall.Syscall6(
		syscall.SYS_PREAD64,
		uintptr(f.Fd()),
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(len(buf)),
		0, 0, 0,
	)
	if errno != 0 {
		log.Fatalf("pread: %v", errno)
	}
	fmt.Printf("pread hostname: %s\n", buf[:n])

	// Alternatively, via syscall.Pread (portable)
	n2, err := syscall.Pread(int(f.Fd()), buf, 0)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("syscall.Pread: %s\n", buf[:n2])
}

// ─── 3. Pipes ────────────────────────────────────────────────────────────────

func demoPipe() {
	fmt.Println("\n=== 3. Pipes ===")

	r, w, err := os.Pipe() // returns *os.File pair
	if err != nil {
		log.Fatal(err)
	}

	done := make(chan struct{})
	go func() {
		defer close(done)
		defer w.Close()
		fmt.Fprintf(w, "data from goroutine")
	}()

	defer r.Close()
	content, _ := io.ReadAll(r)
	<-done
	fmt.Printf("Pipe received: %s\n", content)
}

// ─── 4. socketpair + FD passing ─────────────────────────────────────────────

func demoSocketPair() {
	fmt.Println("\n=== 4. socketpair ===")

	fds, err := syscall.Socketpair(syscall.AF_UNIX, syscall.SOCK_STREAM|syscall.SOCK_CLOEXEC, 0)
	if err != nil {
		log.Fatal(err)
	}

	// Wrap in os.File for idiomatic use
	a := os.NewFile(uintptr(fds[0]), "sock-a")
	b := os.NewFile(uintptr(fds[1]), "sock-b")
	defer a.Close()
	defer b.Close()

	go func() {
		a.WriteString("hello via socketpair")
		a.Close() // send EOF
	}()

	content, _ := io.ReadAll(b)
	fmt.Printf("socketpair received: %s\n", content)
}

// ─── 5. Non-blocking I/O via net package ─────────────────────────────────────

func demoNonblockingPoll() {
	fmt.Println("\n=== 5. Nonblocking I/O (net package) ===")

	// net.Listen uses nonblocking sockets internally
	// All reads/writes block at the goroutine level, not OS thread level
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	defer ln.Close()

	addr := ln.Addr().String()
	fmt.Printf("Listening on %s\n", addr)

	go func() {
		conn, err := ln.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		conn.SetDeadline(time.Now().Add(2 * time.Second))
		buf := make([]byte, 32)
		n, _ := conn.Read(buf)
		conn.Write(buf[:n]) // echo
	}()

	conn, err := net.DialTimeout("tcp", addr, 2*time.Second)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	conn.Write([]byte("ping"))
	buf := make([]byte, 8)
	n, _ := conn.Read(buf)
	fmt.Printf("Echo response: %s\n", buf[:n])
}

// ─── 6. Direct epoll usage ────────────────────────────────────────────────

func demoEpoll() {
	fmt.Println("\n=== 6. Direct epoll ===")

	// Create pipe
	var pipefd [2]int
	if err := syscall.Pipe2(pipefd[:], syscall.O_CLOEXEC|syscall.O_NONBLOCK); err != nil {
		log.Fatal(err)
	}
	rfd, wfd := pipefd[0], pipefd[1]
	defer syscall.Close(rfd)

	// Create epoll instance
	epfd, err := syscall.EpollCreate1(syscall.EPOLL_CLOEXEC)
	if err != nil {
		log.Fatal(err)
	}
	defer syscall.Close(epfd)

	ev := syscall.EpollEvent{
		Events: syscall.EPOLLIN | syscall.EPOLLET,
		Fd:     int32(rfd),
	}
	syscall.EpollCtl(epfd, syscall.EPOLL_CTL_ADD, rfd, &ev)

	// Write from goroutine
	go func() {
		time.Sleep(100 * time.Millisecond)
		syscall.Write(wfd, []byte("epoll event!"))
		syscall.Close(wfd)
	}()

	events := make([]syscall.EpollEvent, 4)
	fmt.Println("Waiting on epoll_wait...")
	n, err := syscall.EpollWait(epfd, events, 2000)
	if err != nil || n == 0 {
		log.Println("epoll_wait: no events or error")
		return
	}
	buf := make([]byte, 32)
	nr, _ := syscall.Read(int(events[0].Fd), buf)
	fmt.Printf("epoll received: %s\n", buf[:nr])
}

// ─── 7. FD inheritance across exec ────────────────────────────────────────

func demoFDInheritance() {
	fmt.Println("\n=== 7. FD inheritance (exec) ===")

	// Create a temp file
	f, err := os.CreateTemp("", "go_fd_inherit_*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.Remove(f.Name())
	f.WriteString("inherited content")
	f.Seek(0, io.SeekStart)

	// In Go, os.File has O_CLOEXEC by default (since Go 1.5)
	// To explicitly pass an FD to a child process, use ExtraFiles:
	cmd := &struct{ Files []*os.File }{Files: []*os.File{f}}
	_ = cmd  // illustrative only; use exec.Command with Cmd.ExtraFiles in practice

	// ExtraFiles example (the actual pattern):
	// cmd := exec.Command("cat")
	// cmd.ExtraFiles = []*os.File{f}      // becomes fd 3 in child (0,1,2 are std)
	// cmd.Stdout = os.Stdout
	// cmd.Run()

	fmt.Println("Go sets O_CLOEXEC by default; use cmd.ExtraFiles to pass FDs to children")
	f.Close()
}

// ─── 8. mmap via syscall ──────────────────────────────────────────────────

func demoMmap() {
	fmt.Println("\n=== 8. mmap ===")

	path := "/tmp/go_mmap_demo.bin"
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		log.Fatal(err)
	}
	defer os.Remove(path)

	size := 4096
	f.Truncate(int64(size))

	data, err := syscall.Mmap(
		int(f.Fd()),
		0,
		size,
		syscall.PROT_READ|syscall.PROT_WRITE,
		syscall.MAP_SHARED,
	)
	f.Close() // fd can be closed after mmap

	if err != nil {
		log.Fatal(err)
	}
	defer syscall.Munmap(data)

	copy(data[:5], []byte("HELLO"))

	// Msync
	_, _, errno := syscall.Syscall(syscall.SYS_MSYNC,
		uintptr(unsafe.Pointer(&data[0])),
		uintptr(size),
		syscall.MS_SYNC)
	if errno != 0 {
		log.Printf("msync: %v", errno)
	}

	// Verify
	verify, _ := os.ReadFile(path)
	fmt.Printf("mmap wrote: %s\n", verify[:5])
}

// ─── 9. FD limits ────────────────────────────────────────────────────────

func demoFDLimits() {
	fmt.Println("\n=== 9. FD limits ===")

	var rlimit syscall.Rlimit
	syscall.Getrlimit(syscall.RLIMIT_NOFILE, &rlimit)
	fmt.Printf("Soft: %d, Hard: %d\n", rlimit.Cur, rlimit.Max)

	// Count open FDs
	entries, err := os.ReadDir("/proc/self/fd")
	if err != nil {
		log.Println(err)
		return
	}
	fmt.Printf("Open FDs: %d (including /proc/self/fd dir)\n", len(entries))

	// Go runtime version
	fmt.Printf("GOMAXPROCS: %d, NumGoroutine: %d\n",
		runtime.GOMAXPROCS(0), runtime.NumGoroutine())
}
```

### File: `server/main.go` — Production Go Server

```go
// server/main.go — Production TCP server with graceful shutdown
// Run: go run ./server
// Test: nc localhost 9090

package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stderr, nil))

	// Use net.ListenConfig to set socket options before Listen
	lc := net.ListenConfig{
		Control: func(network, address string, c syscall.RawConn) error {
			return c.Control(func(fd uintptr) {
				// SO_REUSEPORT for multi-process load balancing
				syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET,
					syscall.SO_REUSEPORT, 1)
				// Increase recv buffer
				syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET,
					syscall.SO_RCVBUF, 256*1024)
			})
		},
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	ln, err := lc.Listen(ctx, "tcp6", "[::]:9090")
	if err != nil {
		log.Error("listen failed", "err", err)
		os.Exit(1)
	}
	log.Info("listening", "addr", ln.Addr(), "fd", getFD(ln))

	var wg sync.WaitGroup
	server := &echoServer{log: log, ln: ln, wg: &wg}

	// Graceful shutdown on signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		sig := <-sigCh
		log.Info("received signal", "signal", sig)
		ln.Close()   // causes Accept to return error → server stops accepting
		cancel()
	}()

	server.serve()

	// Wait for all handlers to finish with deadline
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
		log.Info("all connections closed cleanly")
	case <-time.After(30 * time.Second):
		log.Warn("shutdown timeout; forcing exit")
	}
}

type echoServer struct {
	log *slog.Logger
	ln  net.Listener
	wg  *sync.WaitGroup
}

func (s *echoServer) serve() {
	for {
		conn, err := s.ln.Accept()
		if err != nil {
			s.log.Info("accept stopped", "err", err)
			return
		}
		s.wg.Add(1)
		go s.handleConn(conn)
	}
}

func (s *echoServer) handleConn(conn net.Conn) {
	defer s.wg.Done()
	defer conn.Close()

	tc := conn.(*net.TCPConn)
	tc.SetNoDelay(true)        // TCP_NODELAY
	tc.SetKeepAlive(true)
	tc.SetKeepAlivePeriod(30 * time.Second)

	// Set read/write deadlines to prevent goroutine leaks
	conn.SetDeadline(time.Now().Add(5 * time.Minute))

	buf := make([]byte, 4096)
	for {
		n, err := conn.Read(buf)
		if n > 0 {
			conn.SetDeadline(time.Now().Add(5 * time.Minute)) // reset on activity
			if _, werr := conn.Write(buf[:n]); werr != nil {
				break
			}
		}
		if err != nil {
			break
		}
	}
}

func getFD(ln net.Listener) uintptr {
	tc := ln.(*net.TCPListener)
	f, _ := tc.File()
	defer f.Close()
	return f.Fd()
}
```

### 20.3 Go's Runtime Net Poller Internals

```
┌─────────────────────────────────────────────────────────┐
│                    Go Runtime                           │
│                                                         │
│  G1 (goroutine)   G2 (goroutine)   G3 (goroutine)      │
│  conn.Read()      conn.Write()      time.Sleep()        │
│       │                │                                │
│  [park G1]        [park G2]                             │
│       │                │                                │
│  ┌────▼────────────────▼──────────────────────┐         │
│  │        netpoll goroutine                   │         │
│  │   epoll_wait(epfd, events, -1)             │         │
│  │   ┌── fd ready ──▶ wake G1/G2             │         │
│  └──────────────────────────────────────────┘          │
│                                                         │
│  M (OS thread 1)    M (OS thread 2)                     │
│  runs G3            blocked in epoll_wait               │
└─────────────────────────────────────────────────────────┘
```

When a goroutine calls `conn.Read()` and no data is available:
1. `internal/poll.FD.Read()` calls `runtime.netpollblock()`
2. The goroutine state changes from `_Grunning` to `_Gwaiting`
3. The M picks another runnable G
4. When epoll fires, `runtime.netpollready()` moves the G to `_Grunnable`
5. The scheduler picks it up on the next scheduling point

### 20.4 `exec.Cmd` and FD Management

```go
import "os/exec"

// ExtraFiles: explicitly passed FDs (become fd 3, 4, 5... in child)
// Go automatically sets O_CLOEXEC on all other FDs
cmd := exec.Command("child_binary")
cmd.Stdin  = os.Stdin
cmd.Stdout = os.Stdout
cmd.Stderr = os.Stderr

// Pass a file as fd 3 to the child
f, _ := os.Open("config.json")
cmd.ExtraFiles = []*os.File{f}  // child sees this as fd 3

// In child: os.NewFile(3, "config.json").Read(...)

cmd.Run()
f.Close()

// SysProcAttr for deeper FD control
cmd.SysProcAttr = &syscall.SysProcAttr{
    Cloneflags: syscall.CLONE_NEWPID | syscall.CLONE_NEWNS,
}
```

---

## 21. Cross-Language FD Interop: C↔Rust↔Go

### 21.1 Passing FDs via Environment Variable

The simplest method: open an FD, convert to string, set env var, exec child.

**Parent (Go):**
```go
f, _ := os.Open("shared.db")
cmd := exec.Command("./rust_child")
cmd.Env = append(os.Environ(),
    fmt.Sprintf("DB_FD=%d", f.Fd()))
// Must NOT close f before cmd.Start()
cmd.ExtraFiles = []*os.File{f}
// fd 3 in child if it's the first ExtraFile
```

**Child (Rust):**
```rust
use std::env;
use std::os::unix::io::FromRawFd;
use std::fs::File;

let fd: i32 = env::var("DB_FD").unwrap().parse().unwrap();
let file = unsafe { File::from_raw_fd(fd) };
// Now use file normally
```

### 21.2 Go CGo: Passing FDs to C

```go
// #include <unistd.h>
// void c_write_fd(int fd, const char* msg) { write(fd, msg, strlen(msg)); }
import "C"
import "os"

f, _ := os.Create("/tmp/cgo_test.txt")
C.c_write_fd(C.int(f.Fd()), C.CString("written by C\n"))
f.Close()
```

### 21.3 Rust FFI: Accepting FD from C

```rust
// In a shared library callable from C:
#[no_mangle]
pub extern "C" fn rust_process_fd(fd: libc::c_int) -> libc::c_int {
    use std::os::unix::io::FromRawFd;
    use std::fs::File;
    use std::io::Write;

    // SAFETY: caller guarantees fd is valid and we won't double-close
    // We use ManuallyDrop to avoid closing a fd we don't own
    let mut file = std::mem::ManuallyDrop::new(unsafe { File::from_raw_fd(fd) });
    match file.write_all(b"written by Rust\n") {
        Ok(_) => 0,
        Err(_) => -1,
    }
}
```

---

## 22. Async I/O: io_uring (Linux 5.1+)

`io_uring` is a kernel interface for async I/O that eliminates syscall overhead by using two shared ring buffers (submission queue and completion queue) between user and kernel space.

### 22.1 Architecture

```
Userspace                         Kernel
┌──────────────────┐              ┌──────────────────────┐
│ Submission Queue │──── kthread ▶│ io_uring_sq_thread   │
│ (SQE ring buf)   │              │ (processes SQEs)     │
│                  │◀────────────│                      │
│ Completion Queue │              │ Posts CQEs on done   │
│ (CQE ring buf)   │              └──────────────────────┘
└──────────────────┘
     ↑ mmap'd shared memory — no copies, no syscalls for I/O submission
```

### 22.2 Rust: `tokio-uring`

```toml
[dependencies]
tokio-uring = "0.4"
```

```rust
use tokio_uring::fs::File;

fn main() {
    tokio_uring::start(async {
        let file = File::open("large_file.bin").await.unwrap();
        let buf = vec![0u8; 65536];
        let (res, buf) = file.read_at(buf, 0).await;
        let n = res.unwrap();
        println!("io_uring read {} bytes", n);
    });
}
```

### 22.3 Go: `iouring-go`

Go's standard library uses epoll, not io_uring, for its netpoller. Third-party crates like `iceber/iouring-go` expose io_uring directly.

### 22.4 Direct `liburing` / Syscall Usage (C)

```c
#include <liburing.h>

struct io_uring ring;
io_uring_queue_init(128, &ring, 0);

// Submit a read
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe, fd, buf, len, offset);
sqe->user_data = (uint64_t)ctx;  // user tag for completion
io_uring_submit(&ring);

// Wait for completion (can batch many ops)
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
int result = cqe->res;  // bytes read, or negative errno
io_uring_cqe_seen(&ring, cqe);

io_uring_queue_exit(&ring);
```

---

## 23. Security Hardening Checklist

### 23.1 Mandatory at Open Time

- [ ] **Always use `O_CLOEXEC`** on every `open`, `socket`, `accept4`, `dup`, `pipe2`, `epoll_create1`
- [ ] **Use `O_NOFOLLOW`** when the path shouldn't be a symlink (TOCTOU prevention)
- [ ] **Use `openat(2)`** instead of `open(2)` to prevent TOCTOU on directory paths
- [ ] **Use `O_PATH`** for directory traversal checks without opening for I/O
- [ ] **Validate `open()` with `fstat()`** after open to verify you got what you expected (file type, ownership)
- [ ] **Check that the opened path is under the expected directory** using `openat` + `fstatat` with `AT_EMPTY_PATH`

### 23.2 FD Lifetime and Ownership

- [ ] **Never store `RawFd` across function boundaries** without wrapping in `OwnedFd` (Rust) or careful documentation
- [ ] **Check `close()` return value** — data loss on NFS/network filesystems
- [ ] **Use `dup3`/`F_DUPFD_CLOEXEC`** instead of `dup`/`fcntl` — avoid the race window
- [ ] **Audit all code paths** that can fail between `open` and `close` — use RAII in C++ / Rust Drop / Go defer
- [ ] **Set FD limits** appropriate to your workload (`ulimit`, `LimitNOFILE` in systemd)

### 23.3 File Operations

- [ ] **Use `O_TMPFILE` + `linkat`** for atomic file creation (prevents partial writes being visible)
- [ ] **Use `fsync`/`fdatasync`** before renaming for durable write semantics
- [ ] **Prefer `pwrite` over `lseek+write`** in multithreaded contexts
- [ ] **Use `flock` or POSIX record locks** for file-based mutual exclusion; document which type
- [ ] **Set appropriate `umask`** and pass explicit `mode` to `open` — never rely on umask alone for security

### 23.4 Process and Fork Security

- [ ] **Close all unused FDs after `fork`** before `exec` (use `close_range` on Linux 5.9+)
- [ ] **Audit `ExtraFiles`** in Go's `exec.Cmd` — explicitly decide which FDs children inherit
- [ ] **Use `PR_SET_NO_NEW_PRIVS`** before exec to prevent setuid escalation
- [ ] **Use `seccomp` to restrict syscalls** in sandboxed children

### 23.5 Socket Security

- [ ] **Verify peer credentials** on Unix sockets via `SO_PEERCRED` / `SCM_CREDENTIALS`
- [ ] **Set `TCP_FASTOPEN` carefully** — TFO data can be replayed (not idempotent operations)
- [ ] **Use `SO_RCVTIMEO`/`SO_SNDTIMEO`** or deadlines to prevent goroutine/thread leaks
- [ ] **Bind to specific addresses**, not `0.0.0.0`, unless needed
- [ ] **Implement backpressure** — don't accept more connections than you can handle

### 23.6 mmap Security

- [ ] **Verify mapped file contents** after mmap before parsing — the underlying file can change (TOCTOU via mmap)
- [ ] **Use `MAP_PRIVATE`** when you don't want to write back to the file
- [ ] **Don't execute mapped writable memory** (`PROT_WRITE | PROT_EXEC`) — W^X policy
- [ ] **Use `mlock`** for sensitive data (keys, passwords) to prevent swapping

### 23.7 `/proc/self/fd` and Information Leakage

- [ ] **Check `/proc/self/fd`** in tests to detect FD leaks
- [ ] **Don't log FD numbers** in production (reveals internal state)
- [ ] **Use `memfd_create` with `MFD_ALLOW_SEALING`** and add seals for read-only shared memory

---

## 24. Production Patterns and War Stories

### 24.1 Pattern: Atomic File Update

The only safe way to update a file so readers never see a partial write:

```c
// Write to temp file in same directory, then rename
void write_atomically(const char *final_path, const void *data, size_t len) {
    char tmp_path[PATH_MAX];
    snprintf(tmp_path, sizeof(tmp_path), "%s.XXXXXX", final_path);

    // O_TMPFILE alternative:
    // int fd = open(dir, O_RDWR|O_TMPFILE|O_CLOEXEC, 0600);
    // ... write ...
    // linkat(fd, "", AT_FDCWD, final_path, AT_EMPTY_PATH);

    int fd = mkstemp(tmp_path);  // creates with O_CLOEXEC on Linux
    fcntl(fd, F_SETFD, FD_CLOEXEC);  // ensure if mkstemp doesn't

    write_all(fd, data, len);
    fsync(fd);                    // flush data to storage
    close(fd);

    // Atomic rename — readers see either old or new, never partial
    rename(tmp_path, final_path);
    // fsync the directory to persist the directory entry
    int dir_fd = open(dirname(tmp_path), O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    fsync(dir_fd);
    close(dir_fd);
}
```

### 24.2 Pattern: Connection Draining for Zero-Downtime Restart

```go
// On SIGUSR2: start new process with SO_REUSEPORT, stop accepting in old
// The old process drains existing connections

func (s *Server) gracefulStop(ctx context.Context) {
    s.listener.Close()     // stop accepting new connections

    done := make(chan struct{})
    go func() {
        s.wg.Wait()        // wait for active handlers
        close(done)
    }()

    select {
    case <-done:
    case <-ctx.Done():     // deadline
        s.forceCloseAll()
    }
}
```

### 24.3 War Story: The Zombie Pipe

A service would hang under load. After 6 hours, a single request would time out with no error logs.

Root cause: A `pipe()` was created to communicate with a child process. The parent held both ends and only closed the write end after `fork`. The child's `read()` on the pipe never got `EOF` because the parent still held the write end open (forgot `close(pipefd[1])` in parent). After `RLIMIT_NOFILE` exhaustion, `accept()` returned `EMFILE`; the error was silently swallowed, making the service appear to hang.

**Fix:** Always close pipe ends immediately after `fork`. Use `pipe2(O_CLOEXEC)` to prevent leaking across exec boundaries.

### 24.4 War Story: The NFS Close Failure

A batch job wrote financial records to an NFS-mounted path. `write()` succeeded. `close()` returned -1 with `errno=ENOSPC` (disk full on the NFS server). The error was not checked. 40,000 records were silently dropped.

**Fix:** Always check `close()` return value on files you've written.

### 24.5 War Story: The Descriptor Stampede

After an outage, a service restarted and tried to accept connections. `accept()` immediately returned `EMFILE` because a misconfiguration caused 65,000 FDs to be opened (each request leaked 1 FD). The process was at its soft limit of 65,536. Under load, it couldn't accept new connections while existing ones leaked.

**Fix:** Per-request FD accounting in tests. Production monitoring: alert when `open FDs > 80% of RLIMIT_NOFILE`. Reset the soft limit to `min(hard_limit, 1048576)` at startup.

### 24.6 Pattern: FD Leak Testing

```go
// In Go tests: verify no FD leaks across test cases
func countFDs() int {
    entries, _ := os.ReadDir("/proc/self/fd")
    return len(entries)
}

func TestNoFDLeak(t *testing.T) {
    before := countFDs()
    doSomethingThatMightLeak()
    runtime.GC()  // trigger finalizers
    after := countFDs()
    if after > before {
        t.Errorf("FD leak: %d FDs before, %d after", before, after)
    }
}
```

---

## 25. Profiling and Observability

### 25.1 Monitoring Open FD Count

**Linux `/proc`:**
```bash
# Open FDs for PID
ls /proc/<pid>/fd | wc -l

# System-wide
cat /proc/sys/fs/file-nr  # alloc, free, max
```

**Prometheus metric (Go):**
```go
import (
    "os"
    "github.com/prometheus/client_golang/prometheus"
)

var openFDs = prometheus.NewGaugeFunc(prometheus.GaugeOpts{
    Name: "process_open_fds",
    Help: "Number of open file descriptors",
}, func() float64 {
    entries, _ := os.ReadDir("/proc/self/fd")
    return float64(len(entries))
})

func init() { prometheus.MustRegister(openFDs) }
```

### 25.2 Tracing FD Operations with `strace`

```bash
# Trace all FD-related syscalls for a process
strace -f -e trace=openat,close,read,write,fcntl,dup3,socket,accept4,pipe2 \
       -p <pid> 2>&1 | head -200

# With timestamps and FD tracking
strace -f -T -tt -e trace=file,network -p <pid>

# Count syscalls
strace -c -p <pid>
```

### 25.3 `perf` for I/O Performance

```bash
# Count I/O syscalls
perf stat -e syscalls:sys_enter_read,syscalls:sys_enter_write -p <pid> sleep 10

# Trace slow file I/O
perf trace -e syscalls:sys_exit_read --filter 'ret > 0' -p <pid>

# Profile file I/O latency
bpftrace -e 'kretprobe:vfs_read { @lat = hist(nsecs); }'
```

### 25.4 eBPF for FD Tracing

```python
#!/usr/bin/env python3
# fd_tracer.py — trace all open()/close() calls system-wide
from bcc import BPF

prog = r"""
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

BPF_HASH(fd_counts, u32, u64);  // pid -> open fd count

TRACEPOINT_PROBE(syscalls, sys_exit_openat) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (args->ret >= 0) {
        u64 *cnt = fd_counts.lookup_or_init(&pid, &(u64){0});
        (*cnt)++;
    }
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_close) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u64 *cnt = fd_counts.lookup(&pid);
    if (cnt && *cnt > 0) (*cnt)--;
    return 0;
}
"""

b = BPF(text=prog)
print("Tracing FD open/close... Ctrl-C to stop")
while True:
    import time; time.sleep(5)
    for k, v in b["fd_counts"].items():
        print(f"PID {k.value}: {v.value} FDs open")
```

### 25.5 Go's `pprof` for File Descriptor Analysis

```go
import _ "net/http/pprof"
import "net/http"

func main() {
    go http.ListenAndServe(":6060", nil)
    // ...
}
```

```bash
# Goroutine dump — see goroutines blocked in I/O
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Trace: see when goroutines are scheduled around I/O
go tool trace <(curl -s http://localhost:6060/debug/pprof/trace?seconds=5)
```

---

## 26. Exercises

### 26.1 Beginner

**Exercise 1: Write a safe `write_all` in C**
Implement a `write_all(int fd, const void *buf, size_t len)` that correctly handles short writes and `EINTR`. Add a test using a pipe with a tiny buffer (`fcntl(fd, F_SETPIPE_SZ, 512)`).

**Exercise 2: FD count monitor in Rust**
Write a function `fn current_open_fds() -> usize` that reads `/proc/self/fd`. Write a `#[test]` that asserts no FD leak across 100 iterations of opening and closing a temp file.

**Exercise 3: Shell pipeline in Go**
Implement `pipe("ls -la | grep .go | wc -l")` in Go using `os.Pipe()` and `exec.Cmd.Stdin`/`Stdout`. Don't use `sh -c`.

### 26.2 Intermediate

**Exercise 4: epoll chat server (C)**
Build a multi-client chat server in C using `epoll` in edge-triggered mode. Requirements:
- Accept clients on port 7070
- Broadcast each message to all other connected clients
- Handle client disconnects cleanly
- No `select`/`poll`; pure `epoll_wait`

**Exercise 5: `tail -f` implementation (Rust)**
Implement `tail -f filename` in Rust using `inotify` (Linux) or `kqueue` (macOS) via `nix`. Print new lines as they appear. Handle log rotation (`IN_MOVE_SELF`, `IN_CREATE`).

**Exercise 6: mmap key-value store (Go)**
Implement a simple fixed-size key-value store backed by `mmap` in Go. Use `syscall.Mmap` with `MAP_SHARED`. Keys are 16 bytes, values are 256 bytes. Support `Put`, `Get`. Make it crash-safe by writing a length prefix and checksum before each record.

### 26.3 Advanced

**Exercise 7: FD passing daemon (C + Go)**
Build a privilege-separated architecture:
- Privileged C daemon: binds to port 80, accepts connections, passes FDs via Unix socket (`SCM_RIGHTS`)
- Unprivileged Go handler: receives FDs, handles HTTP requests, drops capabilities before serving
- Implement the full handshake with `sendmsg`/`recvmsg`

**Exercise 8: io_uring file server (Rust)**
Using `tokio-uring`, build an HTTP/1.1 file server that serves static files. Requirements:
- Use `read_fixed` (registered buffers) for zero-copy reads
- Use `write` with fixed buffer pool
- Benchmark against a standard `tokio` implementation with `hyperfine`

**Exercise 9: Go runtime netpoller analysis**
- Add `GODEBUG=schedtrace=100` to observe the scheduler
- Write a load test that creates 50,000 concurrent connections
- Use `pprof` goroutine profile to observe park/unpark patterns
- Explain the difference in CPU usage between your echo server and a blocking thread-per-connection server

---

## 27. Further Reading

### Books

| Title | Why |
|-------|-----|
| *The Linux Programming Interface* — Michael Kerrisk | The definitive reference on every syscall covered here; read chapters 5, 23, 44, 56, 57, 63 |
| *Systems Performance* — Brendan Gregg | Chapter 8 covers file systems and I/O from a performance perspective |
| *Unix Network Programming Vol. 1* — W. Richard Stevens | Deep coverage of socket FDs, select/poll/epoll, nonblocking I/O |
| *Programming Rust* — Blandy, Orendorff, Tindall | Chapter on I/O and the `std::io` module; covers ownership of FDs |
| *The Go Programming Language* — Donovan & Kernighan | Chapter 8 covers goroutine + channel patterns; Chapter 9 covers `sync` |

### Articles and Docs

| Resource | Topic |
|----------|-------|
| [man7.org](https://man7.org/linux/man-pages/) | Primary source for every syscall manpage |
| [Russ Cox — "Go Concurrency Patterns: Timing Out, Moving On"](https://go.dev/blog/concurrency-timeouts) | Practical patterns for FD-based timeouts in Go |
| [io_uring explained — Jens Axboe](https://kernel.dk/io_uring.pdf) | Original io_uring design document |
| [Cloudflare — "Why does one NGINX worker take all the load?"](https://blog.cloudflare.com/the-sad-state-of-linux-socket-balancing/) | SO_REUSEPORT and epoll interaction |
| [Tokio internals — Carl Lerche](https://tokio.rs/blog/2019-10-scheduler) | How Tokio's scheduler parks/unparks on I/O |
| [io-safety RFC (Rust)](https://github.com/rust-lang/rfcs/blob/master/text/3128-io-safety.md) | The rationale for `OwnedFd`/`BorrowedFd` |

### Reference Repositories

| Repo | What to study |
|------|---------------|
| [tokio-rs/tokio](https://github.com/tokio-rs/tokio) | `tokio/src/io/unix/async_fd.rs`, `mio/src/sys/unix/` — the epoll glue |
| [nginx/nginx](https://github.com/nginx/nginx) | `src/event/ngx_epoll_module.c` — production epoll usage |
| [axboe/liburing](https://github.com/axboe/liburing) | Complete io_uring userspace library with examples |
| [cloudflare/boring](https://github.com/cloudflare/boringssl) | TLS socket FD wrapping |
| [golang/go](https://github.com/golang/go) | `src/runtime/netpoll_epoll.go`, `src/internal/poll/fd_unix.go` |
| [nix-rust/nix](https://github.com/nix-rust/nix) | Idiomatic Rust wrappers for every Unix syscall covered here |

---

*Guide version: 2025-Q3 | Linux kernel ≥ 6.x | Rust ≥ 1.75 | Go ≥ 1.22*