# Unix Tooling in Linux: A Comprehensive Deep-Dive

> A production-grade reference covering Linux kernel internals, Unix philosophy, system programming, and every essential tool — with C and Rust implementations throughout.

---

## Table of Contents

1. [Unix Philosophy & Design Principles](#1-unix-philosophy--design-principles)
2. [Linux Kernel Architecture](#2-linux-kernel-architecture)
3. [System Calls: The Kernel Interface](#3-system-calls-the-kernel-interface)
4. [Process Model: Lifecycle, Memory & Scheduling](#4-process-model-lifecycle-memory--scheduling)
5. [File Descriptors, I/O & the VFS](#5-file-descriptors-io--the-vfs)
6. [Signals: Asynchronous Process Control](#6-signals-asynchronous-process-control)
7. [Inter-Process Communication (IPC)](#7-inter-process-communication-ipc)
8. [Pipes & Redirection](#8-pipes--redirection)
9. [The Shell: Bash, Zsh & POSIX](#9-the-shell-bash-zsh--posix)
10. [Text Processing: grep, sed, awk](#10-text-processing-grep-sed-awk)
11. [File System Tools & Navigation](#11-file-system-tools--navigation)
12. [Process Monitoring & Management Tools](#12-process-monitoring--management-tools)
13. [Networking Tools & Internals](#13-networking-tools--internals)
14. [Memory Management: Kernel & User Space](#14-memory-management-kernel--user-space)
15. [Linux Namespaces & Containers](#15-linux-namespaces--containers)
16. [Cgroups: Resource Control](#16-cgroups-resource-control)
17. [Security: Permissions, Capabilities & LSMs](#17-security-permissions-capabilities--lsms)
18. [System Performance & Profiling](#18-system-performance--profiling)
19. [Storage, Block Devices & Filesystems](#19-storage-block-devices--filesystems)
20. [Package Management Internals](#20-package-management-internals)
21. [Kernel Modules & Device Drivers](#21-kernel-modules--device-drivers)
22. [Timers, Clocks & Time in Linux](#22-timers-clocks--time-in-linux)
23. [Synchronization Primitives](#23-synchronization-primitives)
24. [eBPF: Programmable Kernel Observability](#24-ebpf-programmable-kernel-observability)
25. [Build Systems & Compilation Toolchain](#25-build-systems--compilation-toolchain)
26. [Debugging Tools: gdb, strace, ltrace, valgrind](#26-debugging-tools-gdb-strace-ltrace-valgrind)
27. [Rust Systems Programming on Linux](#27-rust-systems-programming-on-linux)

---

## 1. Unix Philosophy & Design Principles

### 1.1 The Original Tenets (Ken Thompson, Dennis Ritchie, Doug McIlroy)

Unix was designed at Bell Labs starting in 1969. The philosophy that emerged is not just aesthetic — it is an engineering discipline that has proven extraordinarily durable:

**McIlroy's Maxims (1978):**
1. Write programs that do one thing and do it well.
2. Write programs to work together.
3. Write programs to handle text streams, because that is a universal interface.

This isn't religion — it's engineering economics. Small, composable programs are:
- Easier to test in isolation
- Replaceable without disrupting the whole pipeline
- Easier to reason about (bounded complexity)
- Combinable in ways their authors never anticipated

### 1.2 Everything is a File

In Unix, the abstraction of a **file descriptor** is universal:

| Object | File-like representation |
|---|---|
| Regular file | `/home/user/data.txt` |
| Directory | `/etc/` |
| Block device | `/dev/sda` |
| Character device | `/dev/tty` |
| Named pipe | `/tmp/my_fifo` |
| Unix domain socket | `/run/docker.sock` |
| Network socket | (anonymous fd) |
| Kernel data | `/proc/cpuinfo` |
| Hardware | `/sys/class/net/eth0/` |

This uniformity means a single set of syscalls (`read`, `write`, `close`, `ioctl`) operates on all of them. Programs don't need to know what they're reading from — they just read.

### 1.3 Worse is Better (Richard Gabriel, 1989)

Gabriel described the "New Jersey style" that Unix embodied:
- **Simplicity** of interface is paramount (over correctness of implementation)
- **Interface** over implementation — keep the API simple even if the implementation is complex
- This is why `fork()` survived for decades: weird, somewhat broken, but simple to reason about

### 1.4 The Pipeline Model

The `|` operator is one of the most powerful inventions in software history. It allows:

```bash
# Each program is unaware of the others
cat /var/log/syslog \
  | grep "ERROR" \
  | awk '{print $1, $2, $NF}' \
  | sort \
  | uniq -c \
  | sort -rn \
  | head -20
```

This pipeline:
1. Streams data (no temp files, no RAM blowup on large inputs)
2. Runs all stages **concurrently** — the kernel connects stdout of each to stdin of the next via pipe buffers
3. Each program is independently testable
4. Replacing `awk` with a Rust binary doesn't change anything else

---

## 2. Linux Kernel Architecture

### 2.1 Kernel vs. User Space

The CPU operates in two fundamental privilege levels (x86: Ring 0 and Ring 3):

```
┌─────────────────────────────────────────────────────────┐
│                    User Space (Ring 3)                  │
│  Process A │ Process B │ Process C │ libc │ libpthread  │
├─────────────────────────────────────────────────────────┤
│              System Call Interface (trap gate)          │
├─────────────────────────────────────────────────────────┤
│                  Linux Kernel (Ring 0)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Process  │ │   VFS    │ │  Network │ │  Memory   │  │
│  │ Sched.   │ │ Layer    │ │  Stack   │ │  Manager  │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Device Drivers / HAL                │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                      Hardware                           │
│       CPU    │    RAM    │   Storage   │   Network      │
└─────────────────────────────────────────────────────────┘
```

User space processes cannot access hardware directly. They must cross into kernel space via **system calls**. This boundary is enforced in hardware — attempting to execute privileged instructions in Ring 3 causes a General Protection Fault.

### 2.2 Monolithic vs. Microkernel Design

Linux is a **monolithic kernel with loadable modules**:

- All kernel subsystems (scheduler, VFS, network stack, memory manager) share the same address space
- Modules (drivers) can be loaded/unloaded at runtime but run in kernel space
- Communication between subsystems is via direct function calls — fast
- A bug in a driver can crash the entire kernel (no memory isolation between subsystems)

**Contrast with microkernels** (Mach, QNX, seL4):
- Each subsystem runs as a separate user-space server
- Communication via IPC (message passing)
- A crashing driver doesn't take down the kernel
- Higher IPC overhead makes them slower for I/O-intensive workloads

Linux chose performance. The monolithic approach is vindicated by Linux's dominance in servers, embedded systems, mobile (Android), and supercomputers.

### 2.3 Key Kernel Subsystems

#### Process Scheduler (CFS — Completely Fair Scheduler)

The CFS (introduced in 2.6.23) manages CPU allocation:
- Uses a **red-black tree** (self-balancing BST) ordered by `vruntime` (virtual runtime)
- Each task accumulates `vruntime` while running; the task with smallest `vruntime` runs next
- This naturally provides proportional CPU sharing: a process that slept is "behind" and gets priority
- `nice` values weight vruntime accumulation (lower nice = slower vruntime growth = more CPU)

```c
// kernel/sched/fair.c (simplified)
struct sched_entity {
    struct load_weight  load;
    struct rb_node      run_node;    // position in CFS red-black tree
    u64                 vruntime;    // accumulated virtual runtime
    // ...
};

static void update_curr(struct cfs_rq *cfs_rq) {
    struct sched_entity *curr = cfs_rq->curr;
    u64 now = rq_clock_task(rq_of(cfs_rq));
    u64 delta_exec = now - curr->exec_start;
    
    // vruntime increases proportional to real time, inversely to load weight
    curr->vruntime += calc_delta_fair(delta_exec, curr);
    update_min_vruntime(cfs_rq);
}
```

#### Virtual File System (VFS)

The VFS is an abstraction layer between system calls and concrete filesystem implementations:

```
read() syscall
     │
     ▼
  VFS layer
  (inode, dentry, file ops)
     │
     ├──► ext4_file_read_iter()
     ├──► xfs_file_read_iter()
     ├──► nfs_file_read()
     └──► tmpfs_file_read()
```

Every filesystem registers a set of `file_operations`, `inode_operations`, and `super_operations`. The VFS dispatches to these via function pointers — a classic vtable pattern in C.

#### Memory Management

The kernel manages:
- **Physical memory**: tracked via page frames, buddy allocator for large allocations, slab allocator for small kernel objects
- **Virtual memory**: each process has a `mm_struct` describing its address space, populated via VMAs (Virtual Memory Areas)
- **Page tables**: hardware-walked by MMU to translate virtual → physical addresses
- **Page cache**: the kernel caches file data in RAM — reads go to the page cache, writes are buffered until writeback

#### Network Stack

Linux implements the full TCP/IP stack in kernel space:
- Socket layer (POSIX API)
- Protocol layer (TCP, UDP, ICMP, SCTP, etc.)
- IP routing and netfilter (iptables/nftables hooks)
- Device driver layer (NIC drivers)

Packets flow through a series of hooks. `netfilter` installs callbacks at these hooks for packet filtering, NAT, and connection tracking.

### 2.4 The `/proc` and `/sys` Filesystems

These are **pseudo-filesystems** — they have no backing storage. They're interfaces to live kernel data structures:

```bash
# Process memory map
cat /proc/self/maps

# Kernel configuration
cat /proc/config.gz | gunzip | grep CONFIG_CFS

# CPU info from kernel
cat /proc/cpuinfo

# Network statistics
cat /proc/net/dev

# Mounted filesystems
cat /proc/mounts

# System calls available
cat /proc/sys/kernel/osrelease
```

`/sys` (sysfs) exposes the kernel's device model — every device, driver, and bus is represented:

```bash
# All network interfaces
ls /sys/class/net/

# NIC speed
cat /sys/class/net/eth0/speed

# Block device scheduler
cat /sys/block/sda/queue/scheduler

# Change to mq-deadline
echo mq-deadline > /sys/block/sda/queue/scheduler
```

---

## 3. System Calls: The Kernel Interface

### 3.1 What is a System Call?

A system call is the mechanism by which user-space programs request kernel services. On x86-64 Linux, the `syscall` instruction:
1. Saves user-space registers
2. Loads kernel's CS/SS selectors and RSP from MSRs (Model Specific Registers)
3. Jumps to `entry_SYSCALL_64` in the kernel
4. Kernel dispatches via `sys_call_table[rax]`
5. Returns via `sysretq`

The syscall number is in `rax`. Arguments go in `rdi, rsi, rdx, r10, r8, r9` (up to 6 args).

```c
// Minimal "Hello, World" using raw syscalls — no libc
// Demonstrates the real interface to the kernel

// x86-64 Linux syscall numbers
#define SYS_write  1
#define SYS_exit   60
#define STDOUT_FD  1

void _start(void) {
    // write(1, "Hello\n", 6)
    __asm__ volatile (
        "mov $1,  %%rax\n"   // syscall number: write
        "mov $1,  %%rdi\n"   // fd: stdout
        "lea msg(%%rip), %%rsi\n"  // buf
        "mov $7,  %%rdx\n"   // count
        "syscall\n"
        ::: "rax", "rdi", "rsi", "rdx"
    );
    
    // exit(0)
    __asm__ volatile (
        "mov $60, %%rax\n"   // syscall number: exit
        "xor %%rdi, %%rdi\n" // status: 0
        "syscall\n"
        ::: "rax", "rdi"
    );
    
    __asm__ (".section .rodata\nmsg: .ascii \"Hello\\n\\0\"");
}
```

Compile with: `gcc -nostdlib -static -o hello hello.c`

### 3.2 Syscall Overhead

Each syscall crossing incurs:
- Register save/restore (~40 cycles)
- Cache/TLB pollution from mode switch
- KPTI (Kernel Page Table Isolation) overhead on Meltdown-mitigated systems: separate page tables for user/kernel

This is why:
- `read()` with a 1-byte buffer is 100-1000x slower than buffered I/O (libc's `fread` buffers in user space)
- `vDSO` (Virtual Dynamic Shared Object) maps certain kernel code into user space to avoid mode switching for frequent, safe calls like `gettimeofday()`

```bash
# See vDSO mapping
cat /proc/self/maps | grep vdso
# 7ffd xxxxxx000-7ffd xxxxxx001 r-xp [vdso]
```

### 3.3 Tracing System Calls with `strace`

`strace` uses `ptrace(PTRACE_SYSCALL)` to intercept every syscall:

```bash
# Trace all syscalls
strace ls /tmp

# Count syscalls (summary at end)
strace -c ls /tmp

# Trace specific syscalls
strace -e trace=openat,read,write ls /tmp

# Trace with timestamps
strace -T ls /tmp           # time in each syscall
strace -tt ls /tmp          # absolute timestamps

# Attach to running process
strace -p 1234

# Follow forks
strace -f bash -c "sleep 1"

# Output to file
strace -o /tmp/trace.txt ls
```

**Reading `strace` output:**

```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
# ^^^syscall    ^^^arguments                               ^^^return value

read(3, "\177ELF\2\1\1\0\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0"..., 832) = 832
# fd=3, reading ELF header, 832 bytes requested, 832 bytes returned

close(3) = 0
```

### 3.4 The C Implementation of Key Syscalls

**`write()` system call path in the kernel:**

```c
// fs/read_write.c
SYSCALL_DEFINE3(write, unsigned int, fd, const char __user *, buf, size_t, count)
{
    return ksys_write(fd, buf, count);
}

ssize_t ksys_write(unsigned int fd, const char __user *buf, size_t count)
{
    struct fd f = fdget_pos(fd);     // get file* from fd table
    ssize_t ret = -EBADF;

    if (f.file) {
        loff_t pos, *ppos = file_ppos(f.file);
        if (ppos) {
            pos = *ppos;
            ppos = &pos;
        }
        ret = vfs_write(f.file, buf, count, ppos);
        // ... update position
        fdput_pos(f);
    }
    return ret;
}

ssize_t vfs_write(struct file *file, const char __user *buf, size_t count, loff_t *pos)
{
    // ... permission checks, size checks ...
    
    if (file->f_op->write)
        ret = file->f_op->write(file, buf, count, pos);
    else if (file->f_op->write_iter)
        ret = new_sync_write(file, buf, count, pos);
    // This dispatches to the actual filesystem driver
    return ret;
}
```

### 3.5 Rust: Safe Syscall Wrappers

The `nix` crate provides safe Rust wrappers around Unix syscalls:

```rust
use nix::unistd::{read, write, close, pipe, fork, ForkResult};
use nix::sys::wait::waitpid;
use std::os::unix::io::RawFd;

fn main() {
    // pipe() creates two fds: read end and write end
    let (read_fd, write_fd): (RawFd, RawFd) = pipe().expect("pipe failed");
    
    match unsafe { fork() }.expect("fork failed") {
        ForkResult::Parent { child } => {
            close(write_fd).unwrap();
            
            let mut buf = [0u8; 128];
            let n = read(read_fd, &mut buf).unwrap();
            println!("Parent read {} bytes: {:?}", n, &buf[..n]);
            
            close(read_fd).unwrap();
            waitpid(child, None).unwrap();
        }
        ForkResult::Child => {
            close(read_fd).unwrap();
            
            let msg = b"hello from child\n";
            write(write_fd, msg).unwrap();
            
            close(write_fd).unwrap();
            std::process::exit(0);
        }
    }
}
```

For raw syscalls in Rust without any abstraction:

```rust
// Using the `syscall` crate or inline asm for raw syscalls
use std::arch::asm;

unsafe fn raw_write(fd: i64, buf: *const u8, count: usize) -> isize {
    let ret: isize;
    asm!(
        "syscall",
        in("rax") 1i64,    // SYS_write
        in("rdi") fd,
        in("rsi") buf,
        in("rdx") count,
        out("rcx") _,      // clobbered by syscall
        out("r11") _,      // clobbered by syscall
        lateout("rax") ret,
    );
    ret
}
```

---

## 4. Process Model: Lifecycle, Memory & Scheduling

### 4.1 Process vs. Thread in Linux

Linux uses a unified concept: **task** (`struct task_struct`). Both processes and threads are tasks. The difference is in what they **share**:

| Resource | Process (fork) | Thread (clone with CLONE_VM) |
|---|---|---|
| Address space (mm_struct) | Separate copy-on-write | Shared |
| File descriptor table | Separate (after fork) | Shared (with CLONE_FILES) |
| Signal handlers | Separate (after fork) | Shared (with CLONE_SIGHAND) |
| PID | New PID | Same TGID, new PID |

`fork()` calls `clone()` internally with no CLONE_* flags set. `pthread_create()` calls `clone()` with `CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD`.

### 4.2 `fork()`, `exec()`, and `wait()` — The POSIX Triad

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <string.h>

// This is how the shell implements command execution
int run_command(char *const argv[]) {
    pid_t pid = fork();
    
    if (pid < 0) {
        // fork failed — system is out of resources
        perror("fork");
        return -1;
    }
    
    if (pid == 0) {
        // CHILD PROCESS
        // After fork(), child is an exact copy of parent
        // — same memory (copy-on-write), same fds, same signal masks
        
        // exec replaces the entire process image:
        // — new code, data, stack
        // — but keeps: open fds (unless O_CLOEXEC), PID, PPID, signal mask
        execvp(argv[0], argv);
        
        // If execvp returns, it failed
        fprintf(stderr, "exec '%s': %s\n", argv[0], strerror(errno));
        _exit(127);  // _exit, not exit — don't run atexit handlers
    }
    
    // PARENT PROCESS
    int status;
    pid_t waited = waitpid(pid, &status, 0);
    if (waited < 0) {
        perror("waitpid");
        return -1;
    }
    
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    } else if (WIFSIGNALED(status)) {
        fprintf(stderr, "killed by signal %d\n", WTERMSIG(status));
        return -1;
    }
    return -1;
}

int main(void) {
    char *args[] = { "ls", "-la", "/tmp", NULL };
    int ret = run_command(args);
    printf("exit code: %d\n", ret);
    return ret;
}
```

### 4.3 Copy-on-Write (COW) Fork

When `fork()` is called, the kernel does **not** copy all parent memory immediately. Instead:

1. The child's page tables point to the same physical pages as the parent
2. Both parent and child page table entries are marked **read-only**
3. On the first write to a shared page, a page fault occurs
4. The kernel allocates a new physical page, copies the content, and updates the faulting process's page table entry to point to the new page
5. Both processes now have independent copies of that page

This makes `fork()` followed immediately by `exec()` essentially free (exec discards the address space anyway) — which is why it's viable as a process creation primitive.

### 4.4 The `task_struct`: Heart of the Process Model

```c
// include/linux/sched.h (abbreviated and annotated)
struct task_struct {
    // Thread info — CPU-specific data, stack pointer
    struct thread_info thread_info;
    
    // State: TASK_RUNNING, TASK_INTERRUPTIBLE, TASK_UNINTERRUPTIBLE, etc.
    unsigned int __state;
    
    // Scheduling
    int prio;                   // effective priority
    int static_prio;            // priority set by nice
    int normal_prio;            // calculated from static_prio
    unsigned int rt_priority;   // real-time priority (0-99)
    const struct sched_class *sched_class;  // CFS, RT, IDLE...
    struct sched_entity se;     // CFS scheduling entity
    
    // Identity
    pid_t pid;         // unique per-task ID
    pid_t tgid;        // thread group ID (PID of the first thread)
    
    // Relationships
    struct task_struct __rcu *real_parent;
    struct task_struct __rcu *parent;
    struct list_head children;  // list of children
    struct list_head sibling;   // next sibling
    
    // Memory
    struct mm_struct *mm;       // user-space address space (NULL for kernel threads)
    struct mm_struct *active_mm;
    
    // File system
    struct fs_struct *fs;       // root, pwd
    struct files_struct *files; // open file descriptors
    
    // Signal handling
    struct signal_struct *signal;
    struct sighand_struct __rcu *sighand;
    sigset_t blocked;           // blocked signals
    
    // Credentials
    const struct cred __rcu *cred;  // UID, GID, capabilities
    
    // Namespaces
    struct nsproxy *nsproxy;    // PID, net, mount, UTS namespaces
    
    // Timing
    u64 utime, stime;           // user/kernel CPU time
    u64 start_time;             // process start (monotonic)
    
    // ... hundreds more fields
};
```

### 4.5 Process States and Transitions

```
                   ┌─────────────────────────────────────┐
                   │                                     │
                   ▼                                     │
fork()──► TASK_RUNNING (runnable) ──► CPU runs ──► preempted
              ▲         │                │
              │         │ wait for I/O   │ yield/sleep
              │         ▼               ▼
              │   TASK_INTERRUPTIBLE  TASK_UNINTERRUPTIBLE
              │   (woken by signal    (only woken by event,
              │    or event)           not signals — "D" state)
              │         │               │
              └─────────┴───────────────┘
                   woken up (event ready)
                        │
                        ▼ exit()
                   TASK_ZOMBIE
                   (wait for parent to waitpid)
                        │
                        ▼ parent calls wait
                   TASK_DEAD (removed)
```

**The "D" state (TASK_UNINTERRUPTIBLE)** is critical to understand:
- Process is waiting for an event that cannot be interrupted (typically I/O)
- `kill -9` will NOT kill a process in D state
- Common cause: NFS mounts that become unresponsive, hung SCSI devices
- `ps aux` shows `D` in the STAT column

```bash
# Find processes in uninterruptible sleep
ps aux | awk '$8 == "D"'
```

### 4.6 Scheduling Classes and Priority

Linux has multiple scheduling classes in priority order:

1. **stop_sched_class**: migration threads, highest priority
2. **dl_sched_class**: SCHED_DEADLINE — earliest deadline first
3. **rt_sched_class**: SCHED_FIFO, SCHED_RR — real-time tasks (priority 1-99)
4. **fair_sched_class**: SCHED_NORMAL, SCHED_BATCH — CFS (nice -20 to 19)
5. **idle_sched_class**: SCHED_IDLE — runs only when nothing else can

```bash
# View and change scheduling policy
chrt -p 1234              # view process scheduling
chrt -f -p 50 1234        # set SCHED_FIFO priority 50
chrt -r -p 50 1234        # set SCHED_RR priority 50
chrt -o -p 0 1234         # set SCHED_OTHER (normal CFS)

# Set nice value (-20 to 19, lower = higher priority)
nice -n -10 ./cpu-intensive-program
renice -n 5 -p 1234

# Set real-time deadline scheduling
chrt --deadline --sched-runtime 5000000 --sched-deadline 10000000 \
     --sched-period 10000000 -p 0 ./realtime-program
```

### 4.7 Rust: Process Creation and Management

```rust
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};

fn main() {
    // Spawn a child process with piped I/O
    let mut child = Command::new("grep")
        .arg("-r")
        .arg("ERROR")
        .arg("/var/log/")
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("failed to spawn grep");

    // Stream output line by line
    if let Some(stdout) = child.stdout.take() {
        let reader = BufReader::new(stdout);
        for line in reader.lines().flatten() {
            println!("Found: {}", line);
        }
    }

    let status = child.wait().expect("failed to wait");
    println!("Exited with: {}", status);
}
```

```rust
// Low-level fork/exec using nix
use nix::unistd::{fork, execvp, ForkResult};
use nix::sys::wait::{waitpid, WaitStatus};
use std::ffi::CString;

fn main() {
    let program = CString::new("ls").unwrap();
    let args = vec![
        CString::new("ls").unwrap(),
        CString::new("-la").unwrap(),
        CString::new("/tmp").unwrap(),
    ];

    match unsafe { fork() }.unwrap() {
        ForkResult::Child => {
            execvp(&program, &args).expect("execvp failed");
            unreachable!();
        }
        ForkResult::Parent { child } => {
            match waitpid(child, None).unwrap() {
                WaitStatus::Exited(_, code) => {
                    println!("Child exited with code {}", code);
                }
                WaitStatus::Signaled(_, sig, _) => {
                    println!("Child killed by signal {:?}", sig);
                }
                _ => {}
            }
        }
    }
}
```

---

## 5. File Descriptors, I/O & the VFS

### 5.1 The File Descriptor Table

Every process has a **file descriptor table** — an array of pointers to `struct file` objects in the kernel. File descriptors (integers starting at 0) are indices into this table.

```
Process FD Table          Kernel Open File Table        Inode Table
┌──────┬────────┐         ┌───────────────────┐         ┌───────────┐
│ fd 0 │ ──────►│────────►│ file* (stdin)     │────────►│ /dev/tty  │
│ fd 1 │ ──────►│────────►│ file* (stdout)    │────────►│ /dev/tty  │
│ fd 2 │ ──────►│────────►│ file* (stderr)    │────────►│ /dev/tty  │
│ fd 3 │ ──────►│────────►│ file* (/etc/foo)  │────────►│ inode 423 │
│ fd 4 │ ──────►│────────►│ file* (pipe)      │────────►│ pipe buf  │
└──────┴────────┘         └───────────────────┘         └───────────┘
```

Key insight: **multiple FDs can point to the same open file** (via `dup()`), and **multiple processes can share the same open file table entry** (via `fork()`). The file position cursor (`f_pos`) lives in `struct file`, so duplicated FDs share position; opened independently, they have separate positions.

### 5.2 Opening, Reading, Writing: The Full Path

```c
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>

// Low-level I/O demonstration — no buffering (unlike stdio)
int main(void) {
    // open() flags:
    // O_RDWR   — read and write
    // O_CREAT  — create if not exists
    // O_TRUNC  — truncate to zero on open
    // O_APPEND — all writes go to end (atomic with single write call)
    // O_SYNC   — every write waits for I/O completion (fsync on each write)
    // O_DIRECT — bypass page cache (raw I/O, must use aligned buffers)
    // O_NONBLOCK — non-blocking mode (I/O returns EAGAIN instead of blocking)
    // O_CLOEXEC — close on exec (essential for security in multi-threaded programs)
    
    int fd = open("/tmp/demo.txt",
                  O_RDWR | O_CREAT | O_TRUNC | O_CLOEXEC,
                  S_IRUSR | S_IWUSR | S_IRGRP); // 0640
    
    if (fd < 0) { perror("open"); exit(1); }
    
    // Write — note: write() may write LESS than requested
    const char *data = "Hello, kernel I/O!\n";
    ssize_t written = 0;
    ssize_t total = (ssize_t)strlen(data);  // would use strlen from string.h
    
    while (written < total) {
        ssize_t n = write(fd, data + written, total - written);
        if (n < 0) {
            if (errno == EINTR) continue;  // interrupted by signal, retry
            perror("write"); exit(1);
        }
        written += n;
    }
    
    // Seek back to beginning
    if (lseek(fd, 0, SEEK_SET) < 0) { perror("lseek"); exit(1); }
    
    // Read — same pattern: may return less than requested
    char buf[64];
    ssize_t nread = read(fd, buf, sizeof(buf) - 1);
    if (nread < 0) { perror("read"); exit(1); }
    buf[nread] = '\0';
    
    printf("Read back: %s", buf);
    
    // fsync: flush all pending writes to stable storage
    // fdatasync: only data, not metadata (faster)
    if (fsync(fd) < 0) { perror("fsync"); exit(1); }
    
    close(fd);
    return 0;
}
```

### 5.3 Buffered I/O (stdio) vs. Direct Syscalls

libc wraps raw syscalls with buffering:

```c
// stdio uses a userspace buffer to batch syscalls
FILE *f = fopen("/etc/passwd", "r");

// fgets reads from internal buffer (size: BUFSIZ = 8192)
// Only calls read() when buffer is empty
char line[256];
while (fgets(line, sizeof(line), f)) {
    // process line
}

fclose(f);

// vs. raw I/O — each getchar() is potentially a syscall!
int fd = open("/etc/passwd", O_RDONLY);
char c;
while (read(fd, &c, 1) == 1) {
    // This is 100-1000x slower for text processing
}
close(fd);
```

**When to use raw I/O:**
- Network programming (you control buffering yourself)
- Binary file formats (no line-buffering issues)
- `O_DIRECT` (DMA-friendly, page-cache bypassing)
- When you need `select()`/`poll()`/`epoll()` integration

### 5.4 `dup()`, `dup2()`: File Descriptor Manipulation

```c
// Shell redirection: command > file
// is implemented as:
int fd = open("output.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
dup2(fd, STDOUT_FILENO);  // stdout now points to output.txt
close(fd);                // fd no longer needed
execvp("ls", args);       // ls writes to stdout — which is now the file

// Pipeline: cmd1 | cmd2
// is implemented as:
int pfd[2];
pipe(pfd);       // pfd[0] = read end, pfd[1] = write end

// cmd1: stdout -> pipe write end
dup2(pfd[1], STDOUT_FILENO);
close(pfd[0]); close(pfd[1]);
execvp("cmd1", cmd1_args);

// cmd2: stdin -> pipe read end
dup2(pfd[0], STDIN_FILENO);
close(pfd[0]); close(pfd[1]);
execvp("cmd2", cmd2_args);
```

### 5.5 `epoll`: Scalable I/O Multiplexing

`select()` and `poll()` are O(n) — they scan all fds every call. `epoll` is O(1) for event delivery:

```c
#include <sys/epoll.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#define MAX_EVENTS 64

// This is the pattern behind nginx, Node.js event loops, etc.
int main(void) {
    // Create epoll instance
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) { perror("epoll_create1"); exit(1); }
    
    // Register stdin for reading
    struct epoll_event ev = {
        .events = EPOLLIN | EPOLLET,  // edge-triggered
        .data.fd = STDIN_FILENO
    };
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, STDIN_FILENO, &ev) < 0) {
        perror("epoll_ctl");
        exit(1);
    }
    
    struct epoll_event events[MAX_EVENTS];
    
    // Event loop
    while (1) {
        int nfds = epoll_wait(epfd, events, MAX_EVENTS, -1); // -1 = no timeout
        
        if (nfds < 0) {
            if (errno == EINTR) continue;
            perror("epoll_wait");
            break;
        }
        
        for (int i = 0; i < nfds; i++) {
            int fd = events[i].data.fd;
            
            if (events[i].events & EPOLLIN) {
                char buf[4096];
                ssize_t n;
                
                // Edge-triggered: MUST read all available data
                while ((n = read(fd, buf, sizeof(buf))) > 0) {
                    write(STDOUT_FILENO, buf, n);
                }
                
                if (n == 0) {
                    printf("EOF on fd %d\n", fd);
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                } else if (errno != EAGAIN && errno != EWOULDBLOCK) {
                    perror("read");
                }
            }
            
            if (events[i].events & EPOLLERR) {
                fprintf(stderr, "Error on fd %d\n", fd);
            }
        }
    }
    
    close(epfd);
    return 0;
}
```

**Edge-triggered vs. Level-triggered:**
- **Level-triggered (default)**: `epoll_wait` returns as long as data is available. Safe, but can cause "thundering herd" with many threads.
- **Edge-triggered (EPOLLET)**: Returns only when the state changes (e.g., new data arrives). Must drain the buffer completely. More efficient but harder to get right.

### 5.6 `mmap`: Memory-Mapped Files

`mmap` maps a file (or anonymous memory) into the process's virtual address space:

```c
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

int main(void) {
    int fd = open("/etc/passwd", O_RDONLY);
    struct stat st;
    fstat(fd, &st);
    
    // Map the entire file into memory
    // After this, the kernel will page-fault in data as needed
    // from the page cache — no explicit read() calls needed
    char *data = mmap(NULL,              // let kernel choose address
                      st.st_size,        // map full file
                      PROT_READ,         // read-only
                      MAP_PRIVATE,       // changes don't affect file
                      fd,
                      0);                // offset into file
    
    close(fd);  // fd can be closed after mmap
    
    if (data == MAP_FAILED) { perror("mmap"); return 1; }
    
    // Access file data directly as memory
    printf("First 40 chars: %.40s\n", data);
    
    // Search using C string functions (the whole file is in memory)
    char *root_line = strstr(data, "root:");
    if (root_line) {
        char *newline = memchr(root_line, '\n', data + st.st_size - root_line);
        if (newline) {
            printf("root entry: %.*s\n", (int)(newline - root_line), root_line);
        }
    }
    
    munmap(data, st.st_size);
    return 0;
}
```

**mmap use cases:**
- **Large file processing**: avoids double-buffering (kernel page cache + user buffer)
- **Shared memory IPC**: `MAP_SHARED` allows multiple processes to share memory
- **Zero-copy I/O**: `sendfile()` and similar use page cache directly
- **Executable loading**: the kernel mmap's ELF segments into process address space

### 5.7 Rust: Async I/O with Tokio

```rust
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    println!("Listening on :8080");

    loop {
        let (mut socket, addr) = listener.accept().await?;
        println!("Connection from {}", addr);

        // Spawn a lightweight task per connection
        // Tokio maps these onto a thread pool using epoll internally
        tokio::spawn(async move {
            let mut buf = vec![0u8; 4096];

            loop {
                let n = match socket.read(&mut buf).await {
                    Ok(0) => return,   // EOF
                    Ok(n) => n,
                    Err(e) => {
                        eprintln!("Read error: {}", e);
                        return;
                    }
                };

                // Echo back
                if socket.write_all(&buf[..n]).await.is_err() {
                    return;
                }
            }
        });
    }
}
```

Tokio's event loop internally uses `epoll` (Linux), `kqueue` (macOS/BSD), or IOCP (Windows). The `async/await` machinery in Rust compiles down to state machines that are polled by the runtime — no threads per connection, just epoll-driven futures.

---

## 6. Signals: Asynchronous Process Control

### 6.1 What Are Signals?

Signals are asynchronous notifications delivered to a process. They interrupt normal execution — the kernel forcibly transfers control to a signal handler (or takes a default action).

```
Signal delivery:
  Hardware/Kernel event ──► kernel sets pending bit in task_struct ──►
  On next return to user space (or next scheduling point) ──►
  Kernel checks pending & ~blocked ──►
  Saves user context on stack ──►
  Jumps to signal handler ──►
  Handler executes ──►
  sigreturn() restores user context
```

### 6.2 Signal Table

| Signal | Number | Default Action | Description |
|---|---|---|---|
| SIGHUP | 1 | Terminate | Terminal hang up / daemon reload |
| SIGINT | 2 | Terminate | Ctrl+C |
| SIGQUIT | 3 | Core dump | Ctrl+\\ |
| SIGILL | 4 | Core dump | Illegal instruction |
| SIGTRAP | 5 | Core dump | Debugger breakpoint |
| SIGABRT | 6 | Core dump | `abort()` call |
| SIGBUS | 7 | Core dump | Bus error (misaligned access) |
| SIGFPE | 8 | Core dump | Floating point exception |
| SIGKILL | 9 | Terminate | **Cannot be caught or ignored** |
| SIGUSR1 | 10 | Terminate | User-defined |
| SIGSEGV | 11 | Core dump | Segmentation fault |
| SIGUSR2 | 12 | Terminate | User-defined |
| SIGPIPE | 13 | Terminate | Write to broken pipe |
| SIGALRM | 14 | Terminate | `alarm()` timer |
| SIGTERM | 15 | Terminate | Graceful termination request |
| SIGCHLD | 17 | Ignore | Child stopped or terminated |
| SIGCONT | 18 | Continue | Continue if stopped |
| SIGSTOP | 19 | Stop | **Cannot be caught or ignored** |
| SIGTSTP | 20 | Stop | Ctrl+Z |
| SIGWINCH | 28 | Ignore | Terminal window size changed |

### 6.3 Signal Handling in C

```c
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

// IMPORTANT: Signal handlers have severe restrictions.
// Only async-signal-safe functions may be called:
//   write(), _exit(), signal(), kill(), self-pipe trick
// NOT safe: printf, malloc, pthread_mutex_lock, fopen

volatile sig_atomic_t shutdown_requested = 0;
volatile sig_atomic_t reload_requested = 0;

// The self-pipe trick for signal-safe event loop integration
static int signal_pipe[2];

static void signal_handler(int signum) {
    // Write signal number to pipe — async-signal-safe
    unsigned char byte = (unsigned char)signum;
    write(signal_pipe[1], &byte, 1);
}

int main(void) {
    // Create self-pipe
    if (pipe(signal_pipe) < 0) { perror("pipe"); exit(1); }
    
    // Set write end non-blocking (handler won't block if pipe is full)
    int flags = fcntl(signal_pipe[1], F_GETFL);
    fcntl(signal_pipe[1], F_SETFL, flags | O_NONBLOCK);
    
    // sigaction is preferred over signal() — more control, more portable
    struct sigaction sa = {
        .sa_handler = signal_handler,
        .sa_flags = SA_RESTART,  // restart interrupted syscalls
    };
    sigemptyset(&sa.sa_mask);
    
    // Block all signals during handler execution (prevent re-entrancy)
    sigfillset(&sa.sa_mask);
    
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGHUP,  &sa, NULL);  // reload config
    
    // Ignore SIGPIPE — handle broken pipe via EPIPE error in write()
    signal(SIGPIPE, SIG_IGN);
    
    printf("Server running (PID %d). Send SIGTERM or SIGINT to stop.\n", getpid());
    printf("Send SIGHUP to reload config.\n");
    
    // Event loop — monitor the self-pipe
    fd_set rfds;
    while (1) {
        FD_ZERO(&rfds);
        FD_SET(signal_pipe[0], &rfds);
        // Add other fds here...
        
        int ret = select(signal_pipe[0] + 1, &rfds, NULL, NULL, NULL);
        if (ret < 0 && errno == EINTR) continue;
        
        if (FD_ISSET(signal_pipe[0], &rfds)) {
            unsigned char signum;
            read(signal_pipe[0], &signum, 1);
            
            switch (signum) {
                case SIGTERM:
                case SIGINT:
                    printf("\nShutdown requested (signal %d)\n", signum);
                    goto shutdown;
                case SIGHUP:
                    printf("Reloading configuration...\n");
                    // reload config here
                    break;
            }
        }
    }
    
shutdown:
    printf("Cleanup...\n");
    close(signal_pipe[0]);
    close(signal_pipe[1]);
    return 0;
}
```

### 6.4 Signal Masking and `sigprocmask`

```c
// Block signals temporarily (e.g., during critical section)
sigset_t old_mask, block_mask;
sigemptyset(&block_mask);
sigaddset(&block_mask, SIGTERM);
sigaddset(&block_mask, SIGINT);

// Block SIGTERM and SIGINT
sigprocmask(SIG_BLOCK, &block_mask, &old_mask);

// --- critical section: cannot be interrupted by SIGTERM/SIGINT ---
// modify shared data structures, etc.

// Restore original mask
sigprocmask(SIG_SETMASK, &old_mask, NULL);
// Pending signals are now delivered
```

### 6.5 `kill`, `pkill`, `killall` Commands

```bash
# Send signal to PID
kill -15 1234        # SIGTERM (graceful)
kill -9 1234         # SIGKILL (force)
kill -HUP 1234       # SIGHUP (reload)
kill -STOP 1234      # SIGSTOP (pause)
kill -CONT 1234      # SIGCONT (resume)

# Send to process group (negative PID)
kill -15 -1234       # all processes in group 1234

# By name
pkill -15 nginx      # SIGTERM to all 'nginx' processes
pkill -HUP nginx     # reload all nginx workers
killall -9 java      # SIGKILL all java processes

# pkill with full command matching
pkill -f "python manage.py"   # match full command line

# Send signal and wait for process to die
kill -15 1234 && while kill -0 1234 2>/dev/null; do sleep 0.1; done

# List all signals
kill -l
```

---

## 7. Inter-Process Communication (IPC)

### 7.1 IPC Mechanisms Overview

| Mechanism | Scope | Kernel Involvement | Latency | Throughput |
|---|---|---|---|---|
| Pipe | Parent-child | High | Low | Medium |
| Named Pipe (FIFO) | Any process | High | Low | Medium |
| Unix Domain Socket | Any process (same host) | High | Very Low | High |
| Shared Memory | Any process | Low (after setup) | Minimal | Very High |
| Message Queue (POSIX) | Any process | High | Low | Medium |
| Signal | Any process | High | Very Low | 1 bit |
| Semaphore | Any process | Medium | Low | N/A |
| `eventfd` | Related processes | Medium | Very Low | High |
| `memfd` | Any process | Medium | Low | High |

### 7.2 Pipes

```c
// Bidirectional pipe between parent and child
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    int parent_to_child[2], child_to_parent[2];
    pipe(parent_to_child);
    pipe(child_to_parent);
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child
        close(parent_to_child[1]);  // don't need write end
        close(child_to_parent[0]); // don't need read end
        
        char buf[256];
        ssize_t n = read(parent_to_child[0], buf, sizeof(buf)-1);
        buf[n] = '\0';
        printf("Child received: %s\n", buf);
        
        const char *response = "Hello back, parent!";
        write(child_to_parent[1], response, strlen(response));
        
        close(parent_to_child[0]);
        close(child_to_parent[1]);
        _exit(0);
    }
    
    // Parent
    close(parent_to_child[0]);
    close(child_to_parent[1]);
    
    const char *msg = "Hello, child!";
    write(parent_to_child[1], msg, strlen(msg));
    close(parent_to_child[1]);  // signal EOF to child
    
    char buf[256];
    ssize_t n = read(child_to_parent[0], buf, sizeof(buf)-1);
    buf[n] = '\0';
    printf("Parent received: %s\n", buf);
    
    close(child_to_parent[0]);
    wait(NULL);
    return 0;
}
```

**Pipe internals:**
- Kernel allocates a ring buffer (default 64KB since Linux 2.6.11, configurable via `fcntl(F_SETPIPE_SZ)`)
- `write()` to a full pipe blocks (or returns EAGAIN if O_NONBLOCK)
- `read()` from empty pipe blocks (or returns 0 if all write ends closed = EOF)
- Maximum atomic write: PIPE_BUF (4096 bytes on Linux) — writes up to PIPE_BUF are atomic

### 7.3 POSIX Shared Memory

```c
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

// Producer process
int main_producer(void) {
    // Create shared memory object
    int fd = shm_open("/my_shm", O_CREAT | O_RDWR, 0600);
    ftruncate(fd, 4096);
    
    char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    
    strcpy(mem, "Hello from producer!");
    printf("Written to shared memory\n");
    
    // In real code, use a semaphore to signal consumer
    sleep(5);
    
    munmap(mem, 4096);
    shm_unlink("/my_shm");  // producer cleans up
    return 0;
}

// Consumer process
int main_consumer(void) {
    int fd = shm_open("/my_shm", O_RDONLY, 0);
    
    char *mem = mmap(NULL, 4096, PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    
    printf("Read from shared memory: %s\n", mem);
    
    munmap(mem, 4096);
    return 0;
}
```

### 7.4 Unix Domain Sockets

Unix domain sockets are the highest-performance local IPC mechanism with full socket semantics:

```c
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#define SOCKET_PATH "/tmp/demo.sock"

// Server
void run_server(void) {
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    
    struct sockaddr_un addr = { .sun_family = AF_UNIX };
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);
    
    unlink(SOCKET_PATH);
    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 5);
    
    printf("Server listening on %s\n", SOCKET_PATH);
    
    int client_fd = accept(server_fd, NULL, NULL);
    
    char buf[256];
    ssize_t n = recv(client_fd, buf, sizeof(buf)-1, 0);
    buf[n] = '\0';
    printf("Server received: %s\n", buf);
    
    const char *reply = "ACK";
    send(client_fd, reply, strlen(reply), 0);
    
    close(client_fd);
    close(server_fd);
    unlink(SOCKET_PATH);
}

// Also supports passing file descriptors between processes via SCM_RIGHTS:
void send_fd(int socket_fd, int fd_to_send) {
    char buf[1] = {0};
    struct iovec iov = { .iov_base = buf, .iov_len = 1 };
    
    char cmsg_buf[CMSG_SPACE(sizeof(int))];
    struct msghdr msg = {
        .msg_iov = &iov,
        .msg_iovlen = 1,
        .msg_control = cmsg_buf,
        .msg_controllen = sizeof(cmsg_buf)
    };
    
    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    cmsg->cmsg_level = SOL_SOCKET;
    cmsg->cmsg_type = SCM_RIGHTS;
    cmsg->cmsg_len = CMSG_LEN(sizeof(int));
    memcpy(CMSG_DATA(cmsg), &fd_to_send, sizeof(int));
    
    sendmsg(socket_fd, &msg, 0);
    // The receiving process gets a new fd pointing to the same file object
}
```

---

## 8. Pipes & Redirection

### 8.1 Shell Pipe Internals

When you write `cmd1 | cmd2` in bash, the shell:

1. Creates a pipe: `pipe(pfd)`
2. Forks child1 for `cmd1`, redirects its stdout to `pfd[1]`
3. Forks child2 for `cmd2`, redirects its stdin to `pfd[0]`
4. Closes both pipe ends in parent
5. Both children exec their respective commands
6. Parent waits for both children

All three processes run concurrently. The pipe's 64KB buffer acts as a flow-control mechanism — `cmd1` blocks when the buffer is full, `cmd2` blocks when it's empty.

### 8.2 Redirection Operators

```bash
# stdout to file (truncate)
command > file.txt

# stdout to file (append)
command >> file.txt

# stderr to file
command 2> errors.txt

# stdout and stderr to same file
command > all.txt 2>&1
command &> all.txt          # bash shorthand

# stderr to stdout (e.g., in pipeline)
command 2>&1 | grep ERROR

# stdin from file
command < input.txt

# Here document (heredoc) — stdin from inline text
cat << EOF
line 1
line 2
EOF

# Here string — stdin from single string
grep pattern <<< "search this string"

# Redirect specific fd
command 3>debug.log    # fd 3 to file
command 3>&1           # fd 3 to stdout

# /dev/null — discard output
command > /dev/null 2>&1
command &> /dev/null
```

### 8.3 Process Substitution

Process substitution creates a temporary named pipe or `/dev/fd/N` path:

```bash
# diff two command outputs without temp files
diff <(sort file1.txt) <(sort file2.txt)

# Read output of multiple commands
while IFS= read -r line; do
    echo "Got: $line"
done < <(find /etc -name "*.conf" 2>/dev/null)

# Pass command output as file argument
command --config <(generate-config)

# Capture to multiple consumers (tee + process substitution)
cat largefile.txt | tee >(gzip > compressed.gz) >(md5sum > checksum.md5) > /dev/null
```

### 8.4 `tee`: Splitting Output

```bash
# Write to file AND stdout simultaneously
make 2>&1 | tee build.log

# Append mode
./run-tests.sh | tee -a test-results.log

# Multiple files
./deploy.sh | tee deploy.log deployment-$(date +%Y%m%d).log

# Using tee with sudo to write to privileged files
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf > /dev/null
```

### 8.5 Named Pipes (FIFOs)

```bash
# Create named pipe
mkfifo /tmp/my_pipe

# Producer (blocks until consumer is reading)
echo "data" > /tmp/my_pipe &

# Consumer (blocks until producer writes)
cat /tmp/my_pipe

# Use case: connect two unrelated programs
tail -f /var/log/syslog > /tmp/log_pipe &
grep --line-buffered "ERROR" < /tmp/log_pipe | mail -s "Errors" admin@example.com

# Cleanup
rm /tmp/my_pipe
```

### 8.6 Pipe Performance and `splice()`

The `splice()` system call moves data between file descriptors without copying to user space — kernel-to-kernel:

```c
#include <fcntl.h>
#include <unistd.h>
#include <sys/sendfile.h>

// Efficient file copy using splice (zero-copy in kernel)
int copy_file_splice(int in_fd, int out_fd, off_t size) {
    int pfd[2];
    pipe(pfd);
    
    while (size > 0) {
        ssize_t n;
        
        // Move data from in_fd into pipe (no user-space copy)
        n = splice(in_fd, NULL, pfd[1], NULL,
                   (size > 65536) ? 65536 : size,
                   SPLICE_F_MOVE | SPLICE_F_MORE);
        if (n <= 0) break;
        
        // Move from pipe to out_fd (no user-space copy)
        splice(pfd[0], NULL, out_fd, NULL, n, SPLICE_F_MOVE);
        size -= n;
    }
    
    close(pfd[0]);
    close(pfd[1]);
    return 0;
}

// sendfile: specialized for network (socket) + file
// Used by nginx, lighttpd for static file serving
void serve_file(int client_sock, int file_fd, off_t file_size) {
    off_t offset = 0;
    sendfile(client_sock, file_fd, &offset, file_size);
    // Data goes: file page cache → network buffer → NIC
    // Never enters user space
}
```

---

## 9. The Shell: Bash, Zsh & POSIX

### 9.1 Shell Architecture

A shell is a program that:
1. Reads input (from terminal or script)
2. Parses it (tokenization, syntax tree)
3. Expands it (glob, variable, command substitution)
4. Executes it (fork/exec, builtins)
5. Handles job control (foreground/background, signals)

### 9.2 Variable Expansion and Parameter Substitution

```bash
# Basic assignment and expansion
name="world"
echo "Hello, $name"          # Hello, world
echo "Hello, ${name}"        # Hello, world (explicit boundary)

# Default values
echo "${var:-default}"       # use 'default' if var is unset or empty
echo "${var:=default}"       # assign 'default' if var is unset or empty
echo "${var:+override}"      # use 'override' if var is set and non-empty
echo "${var:?error message}" # error and exit if var is unset or empty

# String operations
str="Hello, World!"
echo "${#str}"               # 13 (length)
echo "${str:7}"              # World! (substring from index 7)
echo "${str:7:5}"            # World (substring, 5 chars from index 7)
echo "${str/World/Linux}"    # Hello, Linux! (replace first)
echo "${str//l/L}"           # HeLLo, WorLd! (replace all)
echo "${str#Hello, }"        # World! (strip prefix)
echo "${str%!}"              # Hello, World (strip suffix)
echo "${str,,}"              # hello, world! (lowercase, bash 4+)
echo "${str^^}"              # HELLO, WORLD! (uppercase, bash 4+)

# Arrays
arr=(alpha beta gamma delta)
echo "${arr[0]}"             # alpha
echo "${arr[-1]}"            # delta (last element, bash 4.3+)
echo "${arr[@]}"             # all elements
echo "${#arr[@]}"            # 4 (array length)
echo "${arr[@]:1:2}"         # beta gamma (slice)
echo "${!arr[@]}"            # 0 1 2 3 (indices)

# Associative arrays (bash 4+)
declare -A colors
colors[red]="#FF0000"
colors[green]="#00FF00"
echo "${colors[red]}"        # #FF0000
echo "${!colors[@]}"         # all keys
```

### 9.3 Conditionals and Tests

```bash
# test / [ ] / [[ ]] comparison

# [[ ]] is bash-specific, more powerful:
# - No word splitting (safe with unquoted variables)
# - Supports regex matching with =~
# - Supports && || instead of -a -o

# File tests
[[ -e "$file" ]]    # exists
[[ -f "$file" ]]    # is regular file
[[ -d "$dir" ]]     # is directory
[[ -L "$link" ]]    # is symlink
[[ -r "$file" ]]    # readable
[[ -w "$file" ]]    # writable
[[ -x "$file" ]]    # executable
[[ -s "$file" ]]    # exists and non-empty
[[ "$f1" -nt "$f2" ]]  # f1 newer than f2
[[ "$f1" -ot "$f2" ]]  # f1 older than f2

# String tests
[[ -z "$str" ]]     # empty string
[[ -n "$str" ]]     # non-empty string
[[ "$a" == "$b" ]]  # string equality
[[ "$a" != "$b" ]]  # string inequality
[[ "$str" =~ ^[0-9]+$ ]]  # regex match (bash)
[[ "$str" < "$other" ]]   # lexicographic less than
[[ "$str" > "$other" ]]   # lexicographic greater than

# Integer tests
[[ $n -eq 0 ]]      # equal
[[ $n -ne 0 ]]      # not equal
[[ $n -lt 10 ]]     # less than
[[ $n -le 10 ]]     # less than or equal
[[ $n -gt 10 ]]     # greater than
[[ $n -ge 10 ]]     # greater than or equal

# Arithmetic evaluation (C-like)
(( a > b ))
(( a++ ))
(( result = a * b + c ))
```

### 9.4 Loops and Control Flow

```bash
#!/usr/bin/env bash
# Production-grade shell scripting patterns

set -euo pipefail      # exit on error, undefined var, pipe failure
IFS=$'\n\t'            # safe word splitting

# Trap for cleanup
cleanup() {
    local exit_code=$?
    echo "Cleaning up (exit code: $exit_code)..." >&2
    rm -f /tmp/my_temp_file.*
    exit $exit_code
}
trap cleanup EXIT INT TERM

# C-style for loop
for (( i=0; i<10; i++ )); do
    echo "i = $i"
done

# Range with brace expansion
for i in {1..10}; do echo "$i"; done
for i in {0..100..10}; do echo "$i"; done  # step of 10

# Iterate over array
files=(*.log)
for f in "${files[@]}"; do
    [[ -f "$f" ]] || continue
    echo "Processing $f"
done

# While loop with read
while IFS=: read -r user _ uid gid _ home shell; do
    echo "User: $user, UID: $uid, Shell: $shell"
done < /etc/passwd

# Process substitution in while
while IFS= read -r line; do
    echo ">>> $line"
done < <(find /etc -name "*.conf" 2>/dev/null | sort)

# Case statement
case "$OSTYPE" in
    linux-gnu*)   echo "Linux" ;;
    darwin*)      echo "macOS" ;;
    cygwin|msys)  echo "Windows" ;;
    *)            echo "Unknown: $OSTYPE" ;;
esac

# select for interactive menus
PS3="Select option: "
select option in "Deploy" "Rollback" "Status" "Exit"; do
    case $option in
        Deploy)   deploy; break ;;
        Rollback) rollback; break ;;
        Status)   status ;;
        Exit)     break ;;
        *)        echo "Invalid option" ;;
    esac
done
```

### 9.5 Functions

```bash
# Function definition
log() {
    local level="${1:-INFO}"
    local message="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$timestamp] [$level] $message" >&2
}

# Function with return value via stdout (command substitution)
get_container_ip() {
    local container_name="$1"
    docker inspect \
        --format='{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
        "$container_name" 2>/dev/null
}

ip=$(get_container_ip "my-container")

# Passing arrays to functions
process_files() {
    local -n files_ref="$1"   # nameref — reference to caller's array
    for f in "${files_ref[@]}"; do
        echo "Processing: $f"
    done
}

my_files=("a.txt" "b.txt" "c.txt")
process_files my_files

# Recursive function
factorial() {
    local n="$1"
    if (( n <= 1 )); then
        echo 1
    else
        local sub
        sub=$(factorial $(( n - 1 )))
        echo $(( n * sub ))
    fi
}

echo "10! = $(factorial 10)"
```

### 9.6 String Processing with Shell Builtins

```bash
# Read CSV without external tools
while IFS=',' read -r col1 col2 col3; do
    echo "Col1=$col1 Col2=$col2 Col3=$col3"
done < data.csv

# String splitting
IFS='/' read -ra parts <<< "/usr/local/bin/python3"
for part in "${parts[@]}"; do
    echo "$part"
done

# Check if command exists (portable)
command_exists() {
    command -v "$1" &>/dev/null
}

if command_exists docker; then
    echo "Docker is available"
fi

# Trim whitespace
trim() {
    local str="$1"
    str="${str#"${str%%[![:space:]]*}"}"  # trim leading
    str="${str%"${str##*[![:space:]]}"}"  # trim trailing
    echo "$str"
}

# URL encode
urlencode() {
    local str="$1"
    local out=""
    local i char
    for (( i=0; i<${#str}; i++ )); do
        char="${str:$i:1}"
        case "$char" in
            [a-zA-Z0-9.~_-]) out+="$char" ;;
            *) printf -v hex '%%%02X' "'$char"; out+="$hex" ;;
        esac
    done
    echo "$out"
}
```

### 9.7 Job Control

```bash
# Background job
long-running-command &
# PID of last background job:
bg_pid=$!

# Wait for specific job
wait $bg_pid

# List jobs
jobs -l

# Bring to foreground
fg %1          # job 1
fg %long-run   # job matching "long-run"

# Send to background (if already running)
# 1. Ctrl+Z  (sends SIGTSTP, suspends)
# 2. bg       (sends SIGCONT, resumes in background)

# Disown — remove from job table (survives shell exit)
command &
disown $!

# nohup — redirect output, ignore SIGHUP
nohup long-command > output.log 2>&1 &

# Run process immune to hangup, in background, with output captured
nohup bash -c 'while true; do echo "running"; sleep 1; done' \
    > /tmp/output.log 2>&1 &
echo "PID: $!"
```

---

## 10. Text Processing: grep, sed, awk

### 10.1 `grep`: Pattern Searching

`grep` is backed by sophisticated regex engines. Understanding the engine type matters:

```bash
# Basic regex (BRE) — default
grep 'pattern' file
grep '^start' file          # anchored to line start
grep 'end$' file            # anchored to line end
grep 'a\+' file             # one or more 'a' (BRE — backslash before +)
grep '\(foo\|bar\)' file    # alternation in BRE

# Extended regex (ERE) — -E flag or egrep
grep -E 'pattern' file
grep -E 'a+' file           # one or more 'a' (ERE — no backslash)
grep -E '(foo|bar)' file    # alternation in ERE
grep -E '^[0-9]{1,3}\.[0-9]{1,3}' file   # IP address prefix

# Perl-Compatible Regex (PCRE) — -P flag (GNU grep)
grep -P '\b\w{5}\b' file    # exactly 5-letter words
grep -P '(?<=foo)bar' file  # lookbehind assertion
grep -P '^\d+\.\d+\.\d+\.\d+$' file  # full IPv4

# Flags
grep -i 'error' file        # case-insensitive
grep -v 'debug' file        # invert match (exclude)
grep -n 'todo' file         # show line numbers
grep -c 'error' file        # count matching lines
grep -l 'TODO' src/*.py     # list files with matches
grep -L 'TODO' src/*.py     # list files WITHOUT matches
grep -r 'TODO' ./src/       # recursive
grep -R 'TODO' ./src/       # recursive, follow symlinks
grep -A 3 'ERROR' log       # 3 lines After match
grep -B 3 'ERROR' log       # 3 lines Before match
grep -C 3 'ERROR' log       # 3 lines Context (before+after)
grep -o 'ERROR.*' log       # print only matched portion
grep -h 'pattern' dir/      # suppress filename in output
grep -H 'pattern' file      # always print filename
grep -w 'word' file         # match whole words only
grep -x 'exactline' file    # match whole line only
grep -m 5 'pattern' file    # stop after 5 matches
grep -q 'pattern' file      # quiet — exit code only (use in scripts)
grep --color=always 'err' f # highlight matches

# Real-world examples
# Find processes using a port
ss -tlnp | grep ':8080'

# Find files containing specific string, show line numbers
grep -rn 'TODO\|FIXME\|HACK' --include='*.py' ./

# Count errors by type
grep -oP 'ERROR:\s+\K\w+' app.log | sort | uniq -c | sort -rn

# Extract IP addresses
grep -oP '\b(?:\d{1,3}\.){3}\d{1,3}\b' /var/log/nginx/access.log | sort -u
```

### 10.2 `sed`: Stream Editor

`sed` reads line by line and applies editing commands. It's a one-pass, line-oriented tool:

```bash
# Basic substitution: s/pattern/replacement/flags
sed 's/foo/bar/'          # replace first occurrence per line
sed 's/foo/bar/g'         # replace all occurrences (global)
sed 's/foo/bar/2'         # replace second occurrence
sed 's/foo/bar/gi'        # global, case-insensitive
sed 's/foo/bar/w out.txt' # write changed lines to file

# Delimiter can be anything (useful with paths)
sed 's|/usr/local|/usr|g' file
sed 's#/etc#/config#g' file

# Addresses (select which lines to operate on)
sed '5s/foo/bar/'          # only line 5
sed '2,8s/foo/bar/'        # lines 2 through 8
sed '/pattern/s/foo/bar/'  # lines matching pattern
sed '/start/,/end/s/x/y/'  # between start and end patterns
sed '$s/foo/bar/'           # last line
sed '1~2s/foo/bar/'         # odd lines (1, 3, 5...)
sed '0~2s/foo/bar/'         # even lines (2, 4, 6...)

# Negation
sed '/pattern/!s/foo/bar/'  # lines NOT matching pattern

# Deletion
sed '/^$/d'                 # delete empty lines
sed '/^#/d'                 # delete comment lines
sed '5d'                    # delete line 5
sed '2,8d'                  # delete lines 2-8
sed '/start/,/end/d'        # delete block between patterns

# Print (with -n to suppress default output)
sed -n '5p'                 # print only line 5
sed -n '2,8p'               # print lines 2-8
sed -n '/pattern/p'         # print matching lines (like grep)
sed -n '/start/,/end/p'     # print block

# Insertion and appending
sed '5i\new line before 5'  # insert before line 5
sed '5a\new line after 5'   # append after line 5
sed '/pattern/a\appended'   # append after matching lines

# Transform (translate characters)
sed 'y/abc/ABC/'            # translate a->A, b->B, c->C

# Multiple commands
sed -e 's/foo/bar/' -e 's/baz/qux/'
sed 's/foo/bar/; s/baz/qux/'

# In-place editing (-i) — ALWAYS use a backup extension in production
sed -i.bak 's/foo/bar/g' file.txt   # creates file.txt.bak
sed -i 's/foo/bar/g' file.txt       # no backup (dangerous)

# Capture groups
sed 's/\(first\) \(second\)/\2 \1/'    # swap words (BRE)
sed -E 's/(first) (second)/\2 \1/'    # ERE with -E

# Real-world examples
# Strip ANSI color codes
sed 's/\x1B\[[0-9;]*[mK]//g' colored.log

# Extract section between markers
sed -n '/^---BEGIN---$/,/^---END---$/p' file

# Replace multi-line block (GNU sed)
sed '/START/,/END/{/START/d; /END/d; s/old/new/}' file

# Comment out lines matching pattern
sed -i '/DEBUG_SETTING/s/^/#/' config.file

# Uncomment lines
sed -i '/DEBUG_SETTING/s/^#//' config.file
```

### 10.3 `awk`: Pattern-Action Programming Language

`awk` is a complete programming language designed for structured text processing:

```bash
# Structure: awk 'pattern { action }' file
# Built-in variables:
# $0      — entire line
# $1..$NF — fields (NF = number of fields)
# NR      — record (line) number
# FNR     — record number in current file
# FS      — field separator (default: whitespace)
# OFS     — output field separator
# RS      — record separator (default: \n)
# ORS     — output record separator
# FILENAME — current filename

# Basic field printing
awk '{print $1}' file               # first field
awk '{print $NF}' file              # last field
awk '{print $1, $3}' file           # fields 1 and 3
awk '{print NR, $0}' file           # line numbers

# Field separator
awk -F: '{print $1}' /etc/passwd    # colon-separated
awk -F',' '{print $2}' data.csv     # CSV
awk 'BEGIN{FS=":"} {print $1}' /etc/passwd

# Pattern matching
awk '/error/' file                   # lines matching regex
awk '!/^#/' file                    # lines not starting with #
awk '$3 > 100' file                 # numeric comparison
awk '$1 == "GET"' access.log        # string comparison
awk 'NR==5' file                    # only line 5
awk 'NR>=5 && NR<=10' file          # lines 5-10

# BEGIN and END blocks
awk 'BEGIN {print "Header"} {print} END {print "Total:", NR}' file

# Arithmetic and aggregation
# Sum a column
awk '{sum += $1} END {print sum}' numbers.txt

# Average
awk '{sum += $1; count++} END {print sum/count}' numbers.txt

# Min/Max
awk 'NR==1{min=$1; max=$1} {if($1<min)min=$1; if($1>max)max=$1} END{print min, max}' file

# Count occurrences (word frequency)
awk '{for(i=1;i<=NF;i++) freq[$i]++} END{for(w in freq) print freq[w], w}' file \
    | sort -rn | head -20

# Process /etc/passwd for users with bash shell
awk -F: '$7 == "/bin/bash" {print $1, $3}' /etc/passwd

# Nginx access log analysis
awk '{
    status[$9]++
    bytes += $10
} END {
    for (s in status) print s, status[s]
    print "Total bytes:", bytes
}' /var/log/nginx/access.log

# Printf formatting
awk '{printf "%-20s %5d %8.2f\n", $1, $2, $3}' data.txt

# Multi-line records (RS = "")
awk 'BEGIN{RS=""; FS="\n"} {print "Record", NR, "has", NF, "lines"}' multi.txt

# String functions
awk '{print length($0)}' file           # line length
awk '{print toupper($0)}' file          # uppercase
awk '{print tolower($0)}' file          # lowercase
awk '{print substr($0, 5, 10)}' file    # substring
awk '{gsub(/foo/, "bar"); print}' file  # global substitute
awk '{if (sub(/^ERROR/, "WARN")) print}' file  # substitute and check

# Split and join
awk '{n=split($1,a,":"); for(i=1;i<=n;i++) print a[i]}' file

# Associative arrays
awk '{count[$1]++} END{for(k in count) print k, count[k]}' file

# Getline for reading other files
awk '{
    while ((getline line < "/etc/passwd") > 0) {
        split(line, f, ":")
        users[f[1]] = f[3]
    }
    close("/etc/passwd")
    print $1, "UID:", users[$1]
}' usernames.txt

# Real-world: parse JSON-like logs
awk -F'"' '/level":"error"/{
    for(i=1;i<=NF;i++) {
        if($i=="message") { print $(i+2) }
    }
}' app.log
```

### 10.4 `sort` and `uniq`

```bash
# sort
sort file                       # alphabetical
sort -r file                    # reverse
sort -n file                    # numeric
sort -rn file                   # numeric reverse
sort -k2 file                   # by field 2
sort -k2,2 file                 # by field 2 only
sort -k2n file                  # field 2 numeric
sort -k2 -k3n file              # primary: field2 alpha, secondary: field3 numeric
sort -t: -k3n /etc/passwd       # by UID (numeric, colon-separated)
sort -u file                    # sort + remove duplicates
sort --parallel=4 bigfile       # parallel sort
sort -S 2G bigfile              # use 2GB memory buffer
sort -T /tmp bigfile            # temp dir for merge files
sort --human-numeric-sort file  # handle 1K, 2M, 3G correctly
sort -V versions.txt            # version sort (1.10 > 1.9)

# uniq (must be sorted first, or use sort -u)
sort file | uniq                # remove duplicates
sort file | uniq -c             # count occurrences
sort file | uniq -d             # show only duplicates
sort file | uniq -u             # show only unique lines
sort file | uniq -i             # case-insensitive
```

### 10.5 `cut`, `paste`, `join`

```bash
# cut — extract columns
cut -d: -f1 /etc/passwd         # field 1, colon-delimited
cut -d: -f1,7 /etc/passwd       # fields 1 and 7
cut -c1-5 file                  # characters 1-5
cut -c1-5,10-15 file            # characters 1-5 and 10-15
cut -d, -f2- file               # field 2 to end

# paste — merge files side by side
paste file1 file2               # tab-delimited columns
paste -d, file1 file2           # comma-delimited
paste -s file                   # serial (all on one line)
paste -d'\n' file1 file2        # interleave lines

# join — relational join on a field
sort -k1 users.txt > users.sorted
sort -k1 data.txt > data.sorted
join users.sorted data.sorted   # inner join on field 1
join -a1 users.sorted data.sorted  # left outer join
join -1 2 -2 1 a.txt b.txt     # join file1 field2 with file2 field1
```

---

## 11. File System Tools & Navigation

### 11.1 `find`: Filesystem Search

`find` is one of the most powerful Unix tools. It traverses directory trees and evaluates expressions:

```bash
# Basic find
find /path -name "*.log"            # by name (case-sensitive)
find /path -iname "*.log"           # case-insensitive
find /path -type f                  # files only
find /path -type d                  # directories only
find /path -type l                  # symlinks only
find /path -type b                  # block devices
find /path -type c                  # character devices
find /path -type p                  # named pipes

# Time-based
find /path -mtime -7                # modified < 7 days ago
find /path -mtime +30               # modified > 30 days ago
find /path -mtime 0                 # modified today
find /path -newer reference.txt     # newer than file
find /path -mmin -60                # modified < 60 minutes ago
find /path -atime -1                # accessed < 1 day ago
find /path -ctime -1                # inode changed < 1 day ago

# Size-based
find /path -size +100M              # > 100 MB
find /path -size -1k                # < 1 KB
find /path -size 0                  # empty files
find /path -empty                   # empty files and directories

# Permission-based
find /path -perm 644                # exact permissions
find /path -perm -644               # at least these permissions
find /path -perm /644               # any of these permissions set
find /path -perm /o+w               # world-writable
find /path -perm -4000              # setuid bit
find /path -perm -2000              # setgid bit

# Ownership
find /path -user alice              # owned by alice
find /path -group developers        # group is developers
find /path -nouser                  # no corresponding user
find /path -nogroup                 # no corresponding group

# Logical operators
find /path -name "*.log" -o -name "*.txt"   # OR
find /path -name "*.log" -a -mtime -7       # AND (implicit)
find /path ! -name "*.log"                  # NOT
find /path \( -name "*.log" -o -name "*.txt" \) -mtime -7

# Depth control
find /path -maxdepth 2              # max 2 levels deep
find /path -mindepth 1              # skip top level

# Actions
find /path -name "*.log" -print     # print (default)
find /path -name "*.log" -print0    # null-terminated (safe for filenames with spaces)
find /path -name "*.log" -ls        # long listing (like ls -l)
find /path -name "*.log" -delete    # delete (careful!)
find /path -name "*.log" -exec rm {} \;        # exec per file (slow)
find /path -name "*.log" -exec rm {} +         # exec with multiple files (faster)
find /path -name "*.log" -execdir command {} + # exec in file's directory

# Real-world examples

# Find and delete files older than 30 days in /tmp
find /tmp -maxdepth 1 -type f -mtime +30 -delete

# Find large files
find / -type f -size +1G 2>/dev/null | sort -k5 -rn

# Find duplicates by checksum
find . -type f -print0 | xargs -0 md5sum | sort | uniq -w32 -d

# Bulk rename: replace spaces with underscores
find . -name "* *" -type f -print0 | \
    while IFS= read -r -d '' f; do
        mv "$f" "${f// /_}"
    done

# Find files not modified in 90 days and archive them
find /archive -type f -mtime +90 -print0 | \
    tar -czf archive.tar.gz --null -T -

# Find and fix permissions
find /var/www -type f -exec chmod 644 {} +
find /var/www -type d -exec chmod 755 {} +
```

### 11.2 `xargs`: Build and Execute Commands

```bash
# Basic usage: read stdin, build argument list
find . -name "*.py" | xargs wc -l

# Null-terminated (safe for filenames with special characters)
find . -name "*.log" -print0 | xargs -0 rm

# Parallel execution (-P)
find . -name "*.jpg" -print0 | xargs -0 -P4 -I{} convert {} {}.png

# Limit args per invocation (-n)
echo "a b c d e" | xargs -n2 echo  # echo a b, echo c d, echo e

# Replace string (-I)
cat urls.txt | xargs -I{} curl -o {}.html {}

# Interactive confirmation (-p)
find . -name "*.bak" | xargs -p rm

# Verbose (-t)
echo "test" | xargs -t echo

# From file
xargs -a filelist.txt rm
```

### 11.3 Filesystem Navigation Tools

```bash
# ls with useful options
ls -la              # long format with hidden files
ls -lh              # human-readable sizes
ls -lt              # sorted by modification time (newest first)
ls -ltr             # sorted by time, reversed (oldest first)
ls -lS              # sorted by size (largest first)
ls -lR              # recursive
ls -1               # one file per line
ls -d */            # directories only
ls --color=always   # force color (useful when piping to less)

# tree — directory visualization
tree -L 2           # max depth 2
tree -d             # directories only
tree -h             # human-readable sizes
tree -a             # include hidden files
tree --gitignore    # respect .gitignore
tree -I "*.pyc|__pycache__"  # ignore patterns

# du — disk usage
du -sh *            # summary of each item in current dir
du -sh /path        # summary of directory
du -h --max-depth=1 /    # top-level directory sizes
du -h | sort -h    # sorted by size
du -h --exclude=proc --exclude=sys /

# df — filesystem disk space
df -h               # human-readable
df -i               # inode usage
df -T               # show filesystem type
df -h /             # specific filesystem

# stat — file details
stat file.txt
# File: file.txt
# Size: 1234        Blocks: 8    IO Block: 4096   regular file
# Device: fd01h/64769d  Inode: 12345   Links: 1
# Access: (0644/-rw-r--r--)  Uid: (1000/user)  Gid: (1000/user)
# Access: 2024-01-01 00:00:00
# Modify: 2024-01-01 00:00:00
# Change: 2024-01-01 00:00:00

# realpath and readlink
realpath ../relative/path    # absolute path
readlink -f symlink          # resolve symlink to real path
readlink symlink             # what does symlink point to
```

### 11.4 `lsof`: List Open Files

`lsof` (list open files) is invaluable for debugging:

```bash
# List all open files
lsof

# By process
lsof -p 1234           # files opened by PID 1234
lsof -c nginx          # files opened by nginx processes

# By file/directory
lsof /var/log          # what has /var/log open
lsof /dev/sda1         # what has this device open

# Network files (sockets)
lsof -i                # all network connections
lsof -i :80            # port 80
lsof -i :22-25         # ports 22 to 25
lsof -i TCP            # all TCP
lsof -i UDP            # all UDP
lsof -i tcp:443        # TCP port 443
lsof -i @192.168.1.1   # connections to IP
lsof -i 6              # IPv6 only

# Show listening ports
lsof -i -sTCP:LISTEN
lsof -i -sTCP:ESTABLISHED

# Find which process is using a port
lsof -i :8080 -t       # just PID

# Find deleted files still open (disk space not released)
lsof | grep deleted
lsof | grep '(deleted)'

# Repeat every 5 seconds
lsof -r 5 -i :80
```

### 11.5 Filesystem Types and Mounting

```bash
# View current mounts
mount                  # all mounts
mount -t ext4          # only ext4 mounts
cat /proc/mounts       # kernel's view
findmnt                # tree view
findmnt -t ext4        # by type

# Mount
mount /dev/sdb1 /mnt/data
mount -t ext4 /dev/sdb1 /mnt/data
mount -o ro,noatime /dev/sdb1 /mnt/data     # read-only, no access time updates
mount -o remount,rw /                       # remount root read-write
mount --bind /source /dest                  # bind mount (same data, two paths)
mount -t tmpfs -o size=512M tmpfs /tmp      # tmpfs (RAM-backed)

# Unmount
umount /mnt/data
umount -l /mnt/data   # lazy unmount (when busy)
umount -f /mnt/nfs    # force (NFS)

# /etc/fstab format:
# device    mountpoint    fstype    options    dump    pass
# UUID=xxx  /             ext4      defaults   0       1
# UUID=xxx  /home         ext4      defaults   0       2

# Create filesystem
mkfs.ext4 /dev/sdb1
mkfs.xfs /dev/sdb1
mkfs.btrfs /dev/sdb1
mkfs.vfat -F32 /dev/sdc1    # FAT32

# Check and repair filesystem (unmounted)
fsck /dev/sdb1
fsck.ext4 -f /dev/sdb1      # force check
e2fsck -p /dev/sdb1         # auto-repair

# Resize filesystem
resize2fs /dev/sdb1          # ext4 (after lvextend or partition resize)
xfs_growfs /mount/point      # XFS (can grow online)
```

---

## 12. Process Monitoring & Management Tools

### 12.1 `ps`: Process Snapshot

```bash
# BSD-style (no dash)
ps aux                    # all processes, user-oriented format
ps auxf                   # with forest (process tree)
ps auxww                  # wide output (no truncation)

# UNIX-style (with dash)
ps -ef                    # all processes, full format
ps -ejf                   # with process group and session
ps -eo pid,ppid,user,comm,pcpu,pmem,stat  # custom columns

# Useful columns
# pid    — process ID
# ppid   — parent PID
# pgid   — process group ID
# sid    — session ID
# tty    — controlling terminal
# stat   — process state (R,S,D,Z,T,W,I,X)
# pcpu   — CPU percentage
# pmem   — memory percentage
# vsz    — virtual memory size (KB)
# rss    — resident set size (KB)
# comm   — command name
# args   — full command with args

# Find specific process
ps aux | grep nginx
pgrep nginx               # just PIDs
pgrep -l nginx            # PID and name
pgrep -a nginx            # PID and full command

# Process tree
ps -ejf | head -30
pstree                    # ASCII tree
pstree -p                 # with PIDs
pstree -u                 # with users
pstree 1234               # subtree from PID

# Sort by CPU
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10

# Watch processes
watch -n1 'ps aux --sort=-%cpu | head -20'
```

### 12.2 `top` and `htop`

```bash
# top
top                    # interactive process viewer
top -b -n1             # batch mode, one snapshot
top -b -d5 -n12        # 5-second intervals, 12 iterations
top -p 1234,5678       # specific PIDs
top -u alice           # specific user

# top interactive commands:
# k     — kill process
# r     — renice
# P     — sort by CPU
# M     — sort by memory
# T     — sort by time
# c     — toggle command/name
# 1     — per-CPU stats
# m     — toggle memory display
# H     — show threads
# V     — forest view
# q     — quit

# htop (more user-friendly)
htop                   # interactive
htop -u alice          # user filter
htop -p 1234,5678      # PIDs
htop -s PERCENT_CPU    # sort by CPU
htop -d 5              # 5 second delay

# Understanding top output:
# load average: 1.23, 0.89, 0.67
#               1min  5min  15min
# Load > nCPUs means CPU is overloaded
```

### 12.3 `vmstat`, `iostat`, `mpstat`

```bash
# vmstat — virtual memory statistics
vmstat 1              # update every 1 second
vmstat 1 10           # 10 samples, 1 second apart
vmstat -S M 1         # sizes in MB

# vmstat columns:
# Procs:    r=runnable  b=blocked
# Memory:   swpd free buff cache (KB)
# Swap:     si=swap-in so=swap-out (KB/s)
# IO:       bi=blocks-in bo=blocks-out (blocks/s)
# System:   in=interrupts cs=context-switches per sec
# CPU%:     us sy id wa st (user, sys, idle, iowait, stolen)

# iostat — I/O statistics
iostat 1              # all devices, 1 second interval
iostat -x 1           # extended stats
iostat -xz 1          # extended, skip zero-activity devices
iostat -h 1           # human-readable sizes
iostat -d sda 1       # specific device

# iostat -x columns:
# r/s    — reads per second
# w/s    — writes per second
# rMB/s  — read MB/s
# wMB/s  — write MB/s
# rrqm/s — read requests merged per second
# wrqm/s — write requests merged per second
# await  — average I/O wait time (ms)
# r_await— average read wait time (ms)
# w_await— average write wait time (ms)
# svctm  — average service time (ms) [deprecated]
# %util  — percentage of time device was busy

# mpstat — per-CPU statistics
mpstat 1              # all CPUs combined
mpstat -P ALL 1       # per-CPU breakdown
mpstat -P 0,2,4 1     # specific CPUs

# sar — historical system data (from sysstat)
sar -u 1 10           # CPU utilization
sar -r 1 10           # memory utilization
sar -b 1 10           # I/O stats
sar -n DEV 1 10       # network device stats
sar -q 1 10           # run queue
```

### 12.4 `/proc` — Live Process Data

```bash
# Process-specific /proc files
/proc/$pid/cmdline   # full command line (null-separated)
/proc/$pid/environ   # environment variables (null-separated)
/proc/$pid/maps      # memory map
/proc/$pid/smaps     # detailed memory map with sizes
/proc/$pid/status    # human-readable status
/proc/$pid/stat      # machine-readable status (used by ps)
/proc/$pid/fd/       # open file descriptors
/proc/$pid/fdinfo/   # fd details (position, flags)
/proc/$pid/io        # I/O counters
/proc/$pid/net/      # network stats (per-namespace)
/proc/$pid/cwd       # symlink to working directory
/proc/$pid/exe       # symlink to executable
/proc/$pid/root      # symlink to root directory (chroot)

# Examples
cat /proc/1/status | grep -E 'Name|Pid|State|Threads|VmRSS'
ls -la /proc/self/fd           # my open fds
cat /proc/self/maps            # my memory map
strings /proc/self/environ     # my environment (null-separated)
cat /proc/meminfo              # system memory info
cat /proc/cpuinfo              # CPU info
cat /proc/interrupts           # hardware interrupts per CPU
cat /proc/softirqs             # software interrupts
cat /proc/slabinfo             # kernel slab allocator stats
cat /proc/buddyinfo            # buddy allocator (page frames)
cat /proc/vmstat               # VM statistics
cat /proc/net/tcp              # TCP connections (hex)
cat /proc/net/tcp6             # IPv6 TCP
cat /proc/net/udp              # UDP sockets
cat /proc/diskstats            # disk I/O stats
```

---

## 13. Networking Tools & Internals

### 13.1 The Linux Network Stack

Data path for incoming packet:

```
NIC hardware
    │ DMA → ring buffer
    ▼
NAPI (New API) softirq
    │ driver processes ring buffer
    ▼
netif_receive_skb()
    │
    ▼
netfilter: PREROUTING hook
    │  (iptables/nftables: mangle, raw, conntrack)
    ▼
IP routing decision
    │
    ├─► LOCAL_IN → netfilter: INPUT → socket receive buffer → userspace read()
    └─► FORWARD → netfilter: FORWARD → netfilter: POSTROUTING → egress
```

### 13.2 `ss` and `netstat`

```bash
# ss (socket statistics) — preferred over netstat
ss -tunap          # TCP, UDP, no resolution, all, process
ss -tlnp           # TCP listening ports
ss -ulnp           # UDP listening ports
ss -xlnp           # Unix sockets
ss -s              # summary statistics

# Filter by state
ss -t state established
ss -t state time-wait
ss -t state listen
ss -t state close-wait

# Filter by port
ss -tlnp sport :22
ss -tlnp dport :443

# Filter by address
ss dst 192.168.1.1
ss src 192.168.1.1
ss '( dport = :http or dport = :https )'

# ss output columns:
# Netid  State    Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
# TCP    ESTAB    0       0       10.0.0.1:ssh        10.0.0.2:54321  users:(("sshd",pid=1234,fd=3))

# netstat (older, still useful)
netstat -tlnp      # listening TCP ports
netstat -s         # protocol statistics
netstat -r         # routing table
netstat -i         # interface statistics
```

### 13.3 `ip`: Network Configuration

```bash
# ip link — network interfaces
ip link show                          # all interfaces
ip link show eth0                     # specific interface
ip link set eth0 up                   # bring up
ip link set eth0 down                 # bring down
ip link set eth0 mtu 9000             # jumbo frames
ip link set eth0 promisc on           # promiscuous mode
ip link add veth0 type veth peer name veth1   # veth pair

# ip addr — IP addresses
ip addr show                          # all addresses
ip addr show eth0                     # specific interface
ip addr add 192.168.1.100/24 dev eth0  # add IP
ip addr del 192.168.1.100/24 dev eth0  # remove IP
ip addr flush dev eth0                # remove all IPs

# ip route — routing table
ip route show                         # routing table
ip route add default via 192.168.1.1  # add default gateway
ip route add 10.0.0.0/8 via 172.16.0.1 dev eth1
ip route del 10.0.0.0/8
ip route get 8.8.8.8                  # which route would be used
ip route flush cache                  # flush route cache

# ip neigh — ARP table
ip neigh show                         # ARP cache
ip neigh flush dev eth0               # flush ARP for interface

# ip netns — network namespaces
ip netns add myns                     # create namespace
ip netns list                         # list namespaces
ip netns exec myns ip link show       # run in namespace
ip link set eth1 netns myns           # move interface to namespace

# Network namespace with veth pair (container-like setup)
ip netns add container
ip link add veth0 type veth peer name veth1
ip link set veth1 netns container
ip addr add 10.0.0.1/24 dev veth0
ip link set veth0 up
ip netns exec container ip addr add 10.0.0.2/24 dev veth1
ip netns exec container ip link set veth1 up
ip netns exec container ip route add default via 10.0.0.1
```

### 13.4 `curl` and `wget`

```bash
# curl — comprehensive HTTP client
curl https://example.com                              # GET
curl -X POST https://api.example.com/data             # POST
curl -X POST -H "Content-Type: application/json" \
     -d '{"key":"value"}' https://api.example.com/    # JSON POST
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/
curl -u user:password https://api.example.com/        # basic auth
curl -o output.html https://example.com               # save to file
curl -O https://example.com/file.zip                  # save with original name
curl -L https://example.com/redirect                  # follow redirects
curl -I https://example.com                           # HEAD request only
curl -v https://example.com                           # verbose (headers)
curl -s https://example.com                           # silent (no progress)
curl --compressed https://example.com                 # accept gzip
curl -k https://self-signed.example.com               # skip TLS verification (insecure)
curl --cacert /path/to/ca.crt https://example.com     # custom CA cert
curl --cert /path/to/client.crt --key /path/to/key.pem https://example.com
curl -x http://proxy:3128 https://example.com         # use proxy
curl --retry 3 --retry-delay 2 https://example.com    # retry on failure
curl -w "%{http_code} %{time_total}\n" -o /dev/null -s https://example.com
curl --max-time 10 https://example.com                # timeout
curl -r 0-99 https://example.com/file.zip             # range request (byte ranges)
curl -C - -O https://example.com/large.iso            # resume download
curl --data-urlencode "q=hello world" https://search.example.com  # URL encode

# curl with output formatting
curl -s https://api.example.com | jq '.results[]'

# Multiple requests
curl https://api.example.com/1 https://api.example.com/2  # sequential
```

### 13.5 `tcpdump` and `wireshark`

```bash
# tcpdump — packet capture
tcpdump -i eth0                           # capture on eth0
tcpdump -i any                            # all interfaces
tcpdump -n                                # no name resolution
tcpdump -nn                               # no name/port resolution
tcpdump -v                                # verbose
tcpdump -vv                               # more verbose
tcpdump -X                                # hex + ASCII
tcpdump -w capture.pcap                   # write to file
tcpdump -r capture.pcap                   # read from file
tcpdump -c 100                            # capture 100 packets
tcpdump -s 0                              # full packet (no truncation)

# Filters (Berkeley Packet Filter — BPF)
tcpdump host 192.168.1.1                  # to/from IP
tcpdump src host 192.168.1.1              # from IP
tcpdump dst host 192.168.1.1              # to IP
tcpdump port 80                           # port 80
tcpdump tcp port 443                      # TCP HTTPS
tcpdump udp port 53                       # DNS
tcpdump 'tcp[tcpflags] & tcp-syn != 0'   # TCP SYN packets
tcpdump 'tcp[tcpflags] == tcp-syn'        # ONLY SYN (no SYN-ACK)
tcpdump 'tcp[13] & 4 != 0'              # TCP RST
tcpdump 'ip[2:2] > 100'                 # IP packets > 100 bytes
tcpdump not port 22                       # exclude SSH
tcpdump 'host 10.0.0.1 and port 443'    # AND
tcpdump 'host 10.0.0.1 or host 10.0.0.2'# OR
tcpdump net 10.0.0.0/24                  # entire subnet

# Real-world usage
# Monitor HTTP traffic
sudo tcpdump -i eth0 -A -s 0 'tcp port 80' | grep -i 'GET\|POST\|HTTP'

# Capture TLS handshakes
sudo tcpdump -i eth0 'tcp[20:2] == 0x1603'

# Check for retransmissions
sudo tcpdump -i eth0 'tcp[13] & 8 != 0'   # PSH flag (data segments)
```

### 13.6 DNS Tools

```bash
# dig — comprehensive DNS lookup
dig example.com                         # A record
dig example.com A                       # explicit A record
dig example.com AAAA                    # IPv6
dig example.com MX                      # mail servers
dig example.com NS                      # name servers
dig example.com TXT                     # text records
dig example.com SOA                     # start of authority
dig example.com ANY                     # all records
dig -x 8.8.8.8                          # reverse lookup (PTR)
dig @8.8.8.8 example.com               # query specific server
dig +short example.com                  # just the answer
dig +noall +answer example.com          # clean output
dig +trace example.com                  # trace delegation from root
dig +dnssec example.com                 # check DNSSEC
dig +tcp example.com                    # force TCP

# nslookup (older, interactive)
nslookup example.com
nslookup example.com 8.8.8.8

# host — simple lookup
host example.com
host -t MX example.com
host 8.8.8.8                            # reverse lookup
```

---

## 14. Memory Management: Kernel & User Space

### 14.1 The Linux Memory Architecture

Virtual address space layout on x86-64 Linux (48-bit VA):

```
0xFFFFFFFFFFFFFFFF
    ┌──────────────────────┐ ← ffff_ffff_ffff_ffff
    │  Kernel Space        │   (kernel direct map, vmalloc, etc.)
    │  (128 TB)            │
    └──────────────────────┘ ← ffff_8000_0000_0000
    
    [Non-canonical gap — accessing causes #GP fault]
    
    ┌──────────────────────┐ ← 0000_7fff_ffff_ffff
    │  User Space          │
    │  (128 TB)            │
    │                      │
    │  Stack (grows down)  │ ← RLIMIT_STACK (default 8MB)
    │          │           │
    │          ▼           │
    │                      │
    │  mmap region         │ ← shared libs, mmap'd files
    │          │           │
    │          ▼           │
    │                      │
    │  Heap (grows up)     │ ← brk()/sbrk() or mmap
    │          ▲           │
    │          │           │
    │  BSS (uninit data)   │
    │  Data (init data)    │
    │  Text (code)         │
0x0000000000400000         │ typical ELF load address
    └──────────────────────┘ ← 0x0000_0000_0000_0000
```

### 14.2 Physical Memory Management

The kernel tracks physical memory using **page frames**. On x86-64, pages are 4KB (huge pages: 2MB or 1GB).

**Buddy Allocator**: Manages free pages in power-of-2 groups (order 0 = 1 page, order 1 = 2 pages, ..., order 11 = 2048 pages):

```
Free lists:
Order 0: [page][page][page]...   (1 page = 4KB)
Order 1: [2pages][2pages]...     (8KB)
Order 2: [4pages]...             (16KB)
...
Order 11: [2048pages]...         (8MB)

Allocation of 3 pages:
→ round up to 4 pages (order 2)
→ take from order-2 free list
→ if empty, split an order-3 block
```

```bash
# View buddy allocator state
cat /proc/buddyinfo
# Node 0, zone   Normal  100  200  300  100  50  20  10  5  2  1  0
# (free blocks at each order 0..10)
```

**Slab Allocator (SLUB in modern kernels)**: Manages small kernel objects efficiently by keeping caches of frequently allocated/freed sizes:

```bash
# View slab caches
cat /proc/slabinfo | head -20
sudo slabtop                    # interactive slab usage
```

### 14.3 Virtual Memory Areas (VMAs)

Each process's address space is described by a set of VMAs — contiguous regions with uniform properties:

```c
// include/linux/mm_types.h (simplified)
struct vm_area_struct {
    unsigned long vm_start;     // start virtual address
    unsigned long vm_end;       // end virtual address (exclusive)
    struct vm_area_struct *vm_next, *vm_prev;
    
    pgprot_t vm_page_prot;      // page protection flags
    unsigned long vm_flags;     // VM_READ, VM_WRITE, VM_EXEC, VM_SHARED, ...
    
    struct file *vm_file;       // backing file (if any)
    unsigned long vm_pgoff;     // offset into file (pages)
    
    const struct vm_operations_struct *vm_ops;  // fault handler, etc.
    
    // For anonymous (heap/stack) VMAs:
    struct anon_vma *anon_vma;
};
```

```bash
# View process VMAs
cat /proc/self/maps
# 55a123400000-55a12340c000 r--p 00000000 fd:01 1234567 /usr/bin/bash
# ^start         ^end        perm type  offset  dev  inode  pathname

# smaps — detailed per-VMA stats
cat /proc/self/smaps | head -50
# Shows: Size, Rss, Pss, Shared_Clean, Shared_Dirty, Private_Clean, Private_Dirty
```

### 14.4 The OOM Killer

When the system runs out of memory, the **OOM (Out of Memory) Killer** selects and kills a process:

```bash
# Each process has an OOM score (0-1000)
cat /proc/1234/oom_score        # current score (higher = more likely to die)
cat /proc/1234/oom_score_adj    # adjustment (-1000 to 1000)

# Protect a process from OOM killer
echo -1000 > /proc/1234/oom_score_adj   # will never be killed

# Make a process a preferred victim
echo 1000 > /proc/1234/oom_score_adj    # first to die

# System-wide OOM behavior
sysctl vm.overcommit_memory     # 0=heuristic, 1=always allow, 2=strict
sysctl vm.overcommit_ratio      # % of RAM+swap allowed when strict
sysctl vm.oom_kill_allocating_task  # kill allocating task vs. best candidate
```

When OOM triggers, the kernel logs:

```
Out of memory: Killed process 1234 (java) total-vm:2048000kB, anon-rss:1900000kB
```

### 14.5 Memory Tools

```bash
# free — system memory summary
free -h             # human-readable
free -m             # megabytes
free -s 5           # update every 5 seconds

# Understanding free output:
#               total    used    free    shared  buff/cache  available
# Mem:          7.7Gi   3.2Gi   1.1Gi   231Mi   3.4Gi       4.0Gi
# Swap:         2.0Gi   0       2.0Gi

# "available" = free + reclaimable buff/cache
# This is the real free memory for applications

# /proc/meminfo
cat /proc/meminfo
# MemTotal    — total RAM
# MemFree     — completely free
# MemAvailable — estimatation of available for new apps
# Buffers     — raw disk cache (block I/O)
# Cached      — page cache (file I/O)
# SwapCached  — swap cached in RAM
# Active      — recently used pages (hard to reclaim)
# Inactive    — less recently used (easier to reclaim)

# pmap — process memory map
pmap -x 1234        # detailed for PID
pmap -d 1234        # with device info

# valgrind — memory error detection
valgrind --leak-check=full ./program
valgrind --tool=massif ./program    # memory profiler
```

### 14.6 C: Manual Memory Management

```c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// malloc/free — heap allocation
void heap_demo(void) {
    // malloc: allocate, uninitialized
    int *arr = malloc(100 * sizeof(int));
    if (!arr) { perror("malloc"); exit(1); }
    
    // calloc: allocate + zero-initialize
    int *zero_arr = calloc(100, sizeof(int));
    
    // realloc: resize
    arr = realloc(arr, 200 * sizeof(int));
    if (!arr) { perror("realloc"); exit(1); }
    
    // Always free what you allocate
    free(arr);
    free(zero_arr);
}

// brk/sbrk — extend the heap segment directly (low-level, avoid in modern code)
void brk_demo(void) {
    void *heap_start = sbrk(0);  // current break
    void *allocated = sbrk(4096);  // extend by 4096 bytes
    printf("Allocated at: %p\n", allocated);
    brk(heap_start);  // return to original break
}

// mmap for large allocations
void large_alloc_demo(void) {
    size_t size = 1024UL * 1024 * 1024;  // 1GB
    
    // mmap anonymous memory — not backed by a file
    // Kernel doesn't allocate physical pages until accessed (lazy allocation)
    void *mem = mmap(NULL, size,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS,
                     -1, 0);
    
    if (mem == MAP_FAILED) { perror("mmap"); exit(1); }
    
    // mlock: prevent swapping (useful for real-time or security)
    if (mlock(mem, size) < 0) {
        perror("mlock (might need CAP_IPC_LOCK or increase RLIMIT_MEMLOCK)");
    }
    
    // madvise: hint to kernel about usage pattern
    madvise(mem, size, MADV_SEQUENTIAL);  // expect sequential access
    madvise(mem, size, MADV_WILLNEED);   // prefetch
    madvise(mem, size, MADV_DONTNEED);   // can discard pages
    
    munmap(mem, size);
}
```

---

## 15. Linux Namespaces & Containers

### 15.1 What Are Namespaces?

Namespaces are the kernel mechanism underlying containers. They partition global kernel resources so each process sees its own isolated version:

| Namespace | Flag | Isolates |
|---|---|---|
| Mount | CLONE_NEWNS | Filesystem mounts |
| UTS | CLONE_NEWUTS | Hostname, domain name |
| IPC | CLONE_NEWIPC | SysV IPC, POSIX MQ |
| PID | CLONE_NEWPID | Process IDs |
| Network | CLONE_NEWNET | Network devices, IPs, ports, routes |
| User | CLONE_NEWUSER | UIDs, GIDs |
| Cgroup | CLONE_NEWCGROUP | Cgroup root |
| Time | CLONE_NEWTIME | Boot/monotonic clocks |

### 15.2 Creating Namespaces

```bash
# unshare — run command in new namespaces
unshare --uts bash              # new hostname namespace
hostname container-1            # change hostname in this ns only

# New network namespace
unshare --net bash
ip link show                    # only loopback
ip link set lo up
ping -c1 127.0.0.1              # works

# New PID namespace
unshare --pid --fork --mount-proc bash
ps aux                          # only sees processes in this namespace
# PID 1 is bash

# Full container-like isolation
unshare --pid --net --uts --ipc --mount --fork --user \
    --map-root-user bash

# nsenter — enter existing namespace
nsenter --target 1234 --pid --net    # enter PID and net namespace of PID 1234
nsenter -t 1234 --all                # all namespaces
nsenter --target $(docker inspect -f '{{.State.Pid}}' mycontainer) --net
```

### 15.3 Namespace C Implementation

```c
#define _GNU_SOURCE
#include <sched.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <sys/mount.h>

#define STACK_SIZE (1024 * 1024)

struct child_args {
    char **argv;
};

static int child_fn(void *arg) {
    struct child_args *args = arg;
    
    // Now running in new namespaces
    
    // Set hostname (UTS namespace)
    sethostname("container", 9);
    
    // Mount proc (mount namespace)
    mount("proc", "/proc", "proc", 0, NULL);
    
    // Execute the requested command
    execvp(args->argv[0], args->argv);
    perror("execvp");
    return 1;
}

// Minimal container runtime
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        return 1;
    }
    
    char *stack = malloc(STACK_SIZE);
    char *stack_top = stack + STACK_SIZE;  // stack grows down
    
    struct child_args args = { .argv = &argv[1] };
    
    // Clone with new namespaces
    int flags = CLONE_NEWPID     // new PID namespace (child is PID 1)
              | CLONE_NEWUTS     // new hostname
              | CLONE_NEWNS      // new mount namespace
              | CLONE_NEWIPC     // new IPC
              | SIGCHLD;         // signal parent on exit
    
    pid_t child = clone(child_fn, stack_top, flags, &args);
    if (child < 0) {
        perror("clone");
        exit(1);
    }
    
    waitpid(child, NULL, 0);
    free(stack);
    return 0;
}
```

### 15.4 `/proc/[pid]/ns/` — Namespace Files

```bash
# Each namespace is represented by a file (actually a bind-able inode)
ls -la /proc/self/ns/
# lrwxrwxrwx cgroup -> cgroup:[4026531835]
# lrwxrwxrwx ipc    -> ipc:[4026531839]
# lrwxrwxrwx mnt    -> mnt:[4026531840]
# lrwxrwxrwx net    -> net:[4026531992]
# lrwxrwxrwx pid    -> pid:[4026531836]
# lrwxrwxrwx user   -> user:[4026531837]
# lrwxrwxrwx uts    -> uts:[4026531838]

# Same inode number = same namespace
ls -lai /proc/1/ns/ /proc/self/ns/

# Preserve a namespace by bind-mounting (even after all processes exit)
mount --bind /proc/self/ns/net /tmp/my_net_ns
# Then later: nsenter --net=/tmp/my_net_ns bash
```

---

## 16. Cgroups: Resource Control

### 16.1 What Are Cgroups?

Control groups (cgroups) limit, account, and isolate resource usage (CPU, memory, I/O, network) for groups of processes. They are the other half of the container story (namespaces = isolation, cgroups = resource limits).

Two versions:
- **cgroups v1**: Multiple hierarchies, one per controller
- **cgroups v2**: Unified hierarchy (all controllers in one tree) — preferred in modern systems

### 16.2 cgroups v2 Interface

```bash
# Check if cgroups v2 is active
mount | grep cgroup
# cgroup2 on /sys/fs/cgroup type cgroup2

# The hierarchy root
ls /sys/fs/cgroup/
# cgroup.controllers   cgroup.max.descendants  cgroup.stat
# cgroup.events        cgroup.procs            cgroup.subtree_control
# cpu.stat             io.stat                 memory.current
# ...

# Enable controllers in root (may need root)
echo "+memory +cpu +io" > /sys/fs/cgroup/cgroup.subtree_control

# Create a cgroup
mkdir /sys/fs/cgroup/myapp

# Enable memory controller for this cgroup
echo "+memory +cpu" > /sys/fs/cgroup/myapp/cgroup.subtree_control

# Set memory limit: 256MB
echo $((256 * 1024 * 1024)) > /sys/fs/cgroup/myapp/memory.max

# Set CPU weight (100 = default, range 1-10000)
echo 50 > /sys/fs/cgroup/myapp/cpu.weight

# Set CPU maximum: 50% of one CPU each 100ms period
echo "50000 100000" > /sys/fs/cgroup/myapp/cpu.max

# Add process to cgroup
echo $$ > /sys/fs/cgroup/myapp/cgroup.procs

# Read statistics
cat /sys/fs/cgroup/myapp/memory.current    # current memory usage
cat /sys/fs/cgroup/myapp/memory.stat       # detailed stats
cat /sys/fs/cgroup/myapp/cpu.stat          # CPU usage

# OOM behavior: memory.oom.group
echo 1 > /sys/fs/cgroup/myapp/memory.oom.group   # kill entire group on OOM
```

### 16.3 Using `systemd` for Cgroup Management

```bash
# systemd-run — run a transient service with resource limits
systemd-run --scope -p MemoryMax=256M -p CPUQuota=50% ./myapp

# Existing service resource limits
systemctl set-property nginx.service MemoryMax=512M
systemctl set-property nginx.service CPUQuota=25%
systemctl set-property nginx.service IOWriteBandwidthMax="/dev/sda 10M"

# View cgroup of a service
systemctl status nginx | grep CGroup
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current

# cgroupsv2 with systemd
systemd-cgls            # tree view of all cgroups
systemd-cgtop           # top-like view of cgroup resource usage
```

### 16.4 C: Writing to Cgroups

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>

// Programmatically create a cgroup and limit a process
int setup_cgroup(const char *name, long memory_bytes, int pid) {
    char path[256];
    char value[64];
    int fd;
    
    // Create cgroup directory
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s", name);
    if (mkdir(path, 0755) < 0 && errno != EEXIST) {
        perror("mkdir cgroup");
        return -1;
    }
    
    // Set memory limit
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s/memory.max", name);
    fd = open(path, O_WRONLY);
    snprintf(value, sizeof(value), "%ld\n", memory_bytes);
    write(fd, value, strlen(value));
    close(fd);
    
    // Add process
    snprintf(path, sizeof(path), "/sys/fs/cgroup/%s/cgroup.procs", name);
    fd = open(path, O_WRONLY);
    snprintf(value, sizeof(value), "%d\n", pid);
    write(fd, value, strlen(value));
    close(fd);
    
    return 0;
}

int main(void) {
    pid_t child = fork();
    if (child == 0) {
        // Child process — will be memory-limited
        char *buf;
        long allocated = 0;
        
        while (1) {
            buf = malloc(1024 * 1024);  // allocate 1MB at a time
            if (!buf) break;
            memset(buf, 0, 1024 * 1024);  // touch all pages
            allocated += 1024 * 1024;
            printf("Allocated: %ldMB\n", allocated / (1024*1024));
            sleep(1);
        }
        printf("Allocation failed at %ldMB\n", allocated / (1024*1024));
        return 0;
    }
    
    // Parent: set up 64MB cgroup for child
    sleep(1);  // let child start
    setup_cgroup("test_limit", 64 * 1024 * 1024, child);
    
    waitpid(child, NULL, 0);
    return 0;
}
```

---

## 17. Security: Permissions, Capabilities & LSMs

### 17.1 Traditional Unix Permissions

```bash
# Permission bits: rwxrwxrwx (user, group, other)
# r=4, w=2, x=1

ls -l file
# -rwxr-xr-x 1 alice devs 1234 Jan 1 00:00 file
#  ^^^       owner group

# chmod — change permissions
chmod 755 file          # rwxr-xr-x
chmod u+x file          # add execute for owner
chmod go-w file         # remove write from group and other
chmod a+r file          # add read for all
chmod u=rwx,go=rx file  # explicit setting

# chown — change owner
chown alice file
chown alice:devs file
chown :devs file         # change group only
chown -R alice:devs dir/ # recursive

# chgrp — change group
chgrp devs file

# Special bits
chmod +s file            # setuid on file: runs as owner, not caller
chmod g+s dir/           # setgid on directory: new files inherit dir's group
chmod +t dir/            # sticky bit: only owner can delete files in dir
# Common: chmod 1777 /tmp — sticky world-writable

# umask — default permission mask
umask               # show current (e.g., 0022)
umask 027           # set: new files = 640, dirs = 750
# umask is subtracted from 666 (files) or 777 (dirs)

# ACLs — more granular than traditional permissions
getfacl file                        # view ACL
setfacl -m u:alice:rwx file        # give alice rwx
setfacl -m g:devs:rx file          # give devs group rx
setfacl -m o::- file               # remove all other permissions
setfacl -x u:alice file            # remove alice's ACL entry
setfacl -b file                    # remove all ACLs
setfacl -d -m g:devs:rx dir/       # default ACL for new files in dir
```

### 17.2 Linux Capabilities

Capabilities split root's omnipotence into fine-grained privileges:

```bash
# Key capabilities:
# CAP_NET_BIND_SERVICE  — bind to ports < 1024
# CAP_NET_RAW          — raw sockets (ping)
# CAP_SYS_PTRACE       — ptrace any process (strace, gdb)
# CAP_SYS_ADMIN        — broad system admin (mount, namespaces)
# CAP_SYS_TIME         — set system time
# CAP_SETUID/SETGID    — change UIDs/GIDs
# CAP_DAC_OVERRIDE     — bypass file permissions
# CAP_KILL             — send signals to any process
# CAP_NET_ADMIN        — configure networking
# CAP_SYS_CHROOT       — use chroot

# View capabilities of a process
cat /proc/self/status | grep -i cap
# CapInh: 0000000000000000
# CapPrm: 0000000000000000
# CapEff: 0000000000000000  ← effective capabilities (hex bitmask)
# CapBnd: 000001ffffffffff  ← bounding set
# CapAmb: 0000000000000000  ← ambient

# capsh — shell with capabilities
capsh --print                   # current capabilities

# getcap / setcap — file capabilities
getcap /usr/bin/ping
# /usr/bin/ping = cap_net_raw+ep
setcap cap_net_bind_service+ep /usr/local/bin/myserver   # bind to port 80
setcap cap_net_raw+ep /usr/local/bin/my-ping
setcap -r /usr/local/bin/myserver    # remove capabilities
```

```c
#include <sys/capability.h>
#include <stdio.h>

// Check and manipulate capabilities programmatically
void show_capabilities(void) {
    cap_t caps = cap_get_proc();
    char *text = cap_to_text(caps, NULL);
    printf("Capabilities: %s\n", text);
    cap_free(text);
    cap_free(caps);
}

// Drop all capabilities after startup
void drop_capabilities(void) {
    cap_t empty = cap_init();   // empty capability set
    
    if (cap_set_proc(empty) < 0) {
        perror("cap_set_proc");
    }
    
    cap_free(empty);
    
    // Also set PR_SET_NO_NEW_PRIVS so exec can't regain them
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
}

// Selectively keep needed capability
void keep_only_net_bind(void) {
    cap_t caps = cap_get_proc();
    
    // Clear effective and permitted sets
    cap_clear(caps);
    
    // Keep only CAP_NET_BIND_SERVICE
    cap_value_t cap_list[] = { CAP_NET_BIND_SERVICE };
    cap_set_flag(caps, CAP_EFFECTIVE, 1, cap_list, CAP_SET);
    cap_set_flag(caps, CAP_PERMITTED, 1, cap_list, CAP_SET);
    
    cap_set_proc(caps);
    cap_free(caps);
}
```

### 17.3 SELinux and AppArmor (Linux Security Modules)

```bash
# SELinux (Red Hat/Fedora/RHEL/CentOS)
getenforce                  # Enforcing / Permissive / Disabled
setenforce 0                # set Permissive (temporary)
sestatus                    # full status

# Every file and process has a label:
ls -Z /etc/passwd
# -rw-r--r--. root root system_u:object_r:passwd_file_t:s0 /etc/passwd
ps -Z | grep nginx
# system_u:system_r:httpd_t:s0   nginx

# SELinux policy management
semanage port -l            # list allowed ports
semanage port -a -t http_port_t -p tcp 8080   # allow httpd on 8080
semanage fcontext -l | grep nginx
restorecon -Rv /var/www/html    # restore default contexts
chcon -t httpd_sys_content_t /var/www/myfile   # change context

# Troubleshoot denials
ausearch -m avc -ts recent  # recent AVC denials
audit2why < /var/log/audit/audit.log   # explain denials
audit2allow -a              # generate policy from denials

# AppArmor (Ubuntu/Debian)
aa-status                   # profile status
aa-enforce /usr/sbin/nginx  # put in enforce mode
aa-complain /usr/sbin/nginx # put in complain mode (log only)
apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx  # reload profile

# Example AppArmor profile snippet:
# /usr/sbin/nginx {
#   /var/www/html/ r,
#   /var/www/html/** r,
#   /var/log/nginx/*.log w,
#   /run/nginx.pid w,
#   network tcp,
# }
```

---

## 18. System Performance & Profiling

### 18.1 Performance Analysis Methodology (USE Method)

Brendan Gregg's USE method for resource analysis:
- **U**tilization: % time the resource is busy
- **S**aturation: degree of extra work queued
- **E**rrors: error events

Apply to: CPUs, memory, network, storage, every resource.

```bash
# CPU Utilization
mpstat -P ALL 1     # per-CPU
sar -u 1 10

# CPU Saturation
vmstat 1 | awk '{print $1}'   # run queue length (r column)
# r > nCPUs means saturation

# Memory Utilization
free -h             # used vs available

# Memory Saturation
vmstat 1 | awk '{print $7, $8}'  # si (swap in), so (swap out)
# Nonzero si/so = memory is saturated, system is swapping

# Disk Utilization
iostat -xz 1 | awk '/^[a-z]/{print $1, $NF}'  # device and %util

# Disk Saturation
iostat -xz 1 | awk '/^[a-z]/{print $1, $11}'  # avgqu-sz (queue depth)

# Network Utilization
ip -s link show eth0   # bytes sent/received
sar -n DEV 1 5         # per-second rates
```

### 18.2 `perf`: Linux Performance Counters

`perf` is the primary Linux profiling tool, using hardware PMU (Performance Monitoring Unit) counters:

```bash
# CPU performance counters
perf stat ./myprogram               # event summary
perf stat -e cycles,instructions,cache-misses ./myprogram
perf stat -a sleep 5               # system-wide for 5 seconds

# Flame graph profiling (sampling)
perf record -g ./myprogram         # record with call graph
perf record -F 99 -g -p 1234 -- sleep 30  # sample PID at 99Hz
perf report                        # interactive report
perf report --stdio                # text report

# Generate flame graph (with Brendan Gregg's scripts)
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg

# Tracing
perf trace ./myprogram             # trace syscalls (like strace, lower overhead)
perf trace -p 1234                 # trace existing process
perf trace -e 'syscalls:sys_enter_read' -a sleep 10

# Hardware events
perf list                          # all available events
perf stat -e L1-dcache-load-misses,LLC-load-misses ./myprogram

# Annotate — see which lines are hot
perf annotate --stdio              # after perf record
```

### 18.3 `flamegraph`: Visualizing Performance

```bash
# Install tools
git clone https://github.com/brendangregg/FlameGraph

# Profile and generate flame graph
perf record -F 99 -ag -- sleep 30
perf script | ./FlameGraph/stackcollapse-perf.pl | \
    ./FlameGraph/flamegraph.pl > perf.svg

# eBPF-based profiling (Linux 4.9+)
bpftrace -e 'profile:hz:99 { @[kstack] = count(); }'

# Profile off-CPU time
offcputime -f 5 | flamegraph.pl > offcpu.svg
```

### 18.4 `strace` for Performance Analysis

```bash
# Find slow syscalls
strace -T -p 1234 2>&1 | awk '{
    match($0, /<([0-9.]+)>/, a)
    if (a[1] != "" && a[1]+0 > 0.01)
        print $0
}'

# Count syscalls to find chattiness
strace -c -p 1234
# % time     seconds  usecs/call     calls    errors syscall
# -------  ---------  ----------  --------  -------- --------
#  40.54      0.1234        1234       100        0 futex
#  30.23      0.0921         921       100        0 read

# Summarize file access
strace -e trace=file -p 1234 2>&1 | grep -v ENOENT
```

### 18.5 Benchmarking Tools

```bash
# CPU benchmark
sysbench cpu --threads=4 run
stress-ng --cpu 4 --timeout 60s --metrics-brief

# Memory bandwidth
mbw 1024           # 1GB test
sysbench memory --memory-total-size=4G run

# Storage I/O
fio --name=randread --rw=randread --bs=4k --size=1G --numjobs=4 --iodepth=32
fio --name=seqwrite --rw=write --bs=128k --size=4G --numjobs=1

# Network
iperf3 -s                           # server
iperf3 -c server_ip -t 30          # client, 30 second test
iperf3 -c server_ip -P 4 -t 30    # 4 parallel streams

# HTTP benchmarks
wrk -t4 -c100 -d30s http://localhost:8080/
ab -n 10000 -c 100 http://localhost:8080/
```

---

## 19. Storage, Block Devices & Filesystems

### 19.1 Block Layer Architecture

```
Application
    │ read()/write()
    ▼
Page Cache / VFS
    │ submit_bio()
    ▼
Block Layer
    │
    ├── I/O Scheduler (mq-deadline, kyber, bfq, none)
    │   (merges and reorders requests for efficiency)
    ├── Device Mapper (LVM, dm-crypt, md-raid)
    └── Driver (NVMe, SCSI, virtio-blk)
    │
    ▼
Hardware (SSD, HDD, NVMe)
```

### 19.2 LVM: Logical Volume Management

```bash
# PV (Physical Volume) → VG (Volume Group) → LV (Logical Volume)

# Create PV
pvcreate /dev/sdb /dev/sdc
pvs                             # view PVs
pvdisplay /dev/sdb              # detailed

# Create VG
vgcreate data_vg /dev/sdb /dev/sdc
vgs                             # view VGs
vgdisplay data_vg

# Create LV
lvcreate -L 100G -n data_lv data_vg       # 100GB LV
lvcreate -l 100%FREE -n data_lv data_vg  # use all free space
lvs                             # view LVs

# Create filesystem and mount
mkfs.ext4 /dev/data_vg/data_lv
mount /dev/data_vg/data_lv /data

# Extend LV
lvextend -L +50G /dev/data_vg/data_lv
resize2fs /dev/data_vg/data_lv          # ext4
xfs_growfs /data                         # xfs

# Snapshot (for backup)
lvcreate -L 10G -s -n data_snap /dev/data_vg/data_lv
mount -o ro /dev/data_vg/data_snap /mnt/snap
# Back up from /mnt/snap
umount /mnt/snap
lvremove /dev/data_vg/data_snap
```

### 19.3 I/O Schedulers

```bash
# View available schedulers
cat /sys/block/sda/queue/scheduler
# [mq-deadline] kyber bfq none

# Change scheduler
echo kyber > /sys/block/nvme0n1/queue/scheduler   # NVMe: none or kyber
echo mq-deadline > /sys/block/sda/queue/scheduler # HDD: mq-deadline or bfq

# I/O scheduler choice:
# none       — NVMe SSDs (hardware queue does the scheduling)
# kyber      — SSDs, low latency, simple
# mq-deadline — Default, good for most cases
# bfq        — Desktop/interactive, better latency fairness

# Queue depth
cat /sys/block/nvme0n1/queue/nr_requests   # max queue depth
echo 256 > /sys/block/nvme0n1/queue/nr_requests

# Read-ahead
blockdev --getra /dev/sda                 # current read-ahead (sectors)
blockdev --setra 256 /dev/sda            # set 128KB read-ahead
```

### 19.4 Filesystem Tuning

```bash
# ext4 tuning
# tune2fs — modify ext4 parameters
tune2fs -l /dev/sda1                    # show parameters
tune2fs -c 50 /dev/sda1                # check every 50 mounts
tune2fs -i 0 /dev/sda1                 # disable time-based check
tune2fs -o journal_data_writeback /dev/sda1  # writeback mode (faster, less safe)
tune2fs -E lazy_itable_init=1 /dev/sda1

# Mount options that affect performance
# noatime    — don't update access time (big improvement)
# nodiratime — don't update directory access time
# relatime   — update access time only if < modification time (compromise)
# data=writeback — fastest, writes data before journal
# data=ordered  — default, safe
# barrier=0  — disable write barriers (faster, unsafe on power failure)
# discard    — TRIM for SSDs (or use fstrim instead)
mount -o noatime,nodiratime /dev/sda1 /data

# fstrim — TRIM SSD (or use discard mount option)
fstrim -v /               # TRIM root filesystem
fstrim -av                # all mounted filesystems
# systemd handles this via fstrim.timer: weekly by default

# XFS tuning
xfs_info /data            # show XFS parameters
xfs_repair /dev/sda1      # repair (offline)

# Btrfs
btrfs filesystem usage /data    # usage stats
btrfs device stats /data        # device error stats
btrfs scrub start /data         # verify checksums
btrfs balance start /data       # rebalance data
btrfs subvolume list /data      # list subvolumes
btrfs subvolume snapshot /data /data_snap   # create snapshot
```

---

## 20. Package Management Internals

### 20.1 dpkg / apt (Debian/Ubuntu)

```bash
# dpkg — low-level package manager
dpkg -i package.deb             # install .deb file
dpkg -r package                 # remove (keep configs)
dpkg -P package                 # purge (remove + configs)
dpkg -l                         # list installed packages
dpkg -l 'nginx*'                # search installed packages
dpkg -L nginx                   # list files in package
dpkg -S /usr/bin/python3        # which package owns this file
dpkg --get-selections            # all packages with status
dpkg -s nginx                   # package status/info
dpkg-reconfigure nginx          # re-run configuration

# dpkg database
ls /var/lib/dpkg/info/          # package file lists
ls /var/lib/dpkg/alternatives/  # update-alternatives data
cat /var/lib/dpkg/status        # installed packages database

# apt — high-level, dependency-resolving
apt update                      # refresh package index
apt upgrade                     # upgrade all packages
apt full-upgrade                # upgrade + remove obsolete
apt install nginx               # install
apt install -y nginx            # non-interactive
apt remove nginx                # remove
apt purge nginx                 # remove + configs
apt autoremove                  # remove orphaned dependencies
apt search nginx                # search
apt show nginx                  # package info
apt list --installed            # installed packages
apt list --upgradable           # upgradable packages
apt-cache policy nginx          # version + source info
apt-cache depends nginx         # package dependencies
apt-cache rdepends nginx        # reverse dependencies

# Package sources
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/
```

### 20.2 rpm / dnf / yum (Red Hat/Fedora)

```bash
# rpm — low-level
rpm -ivh package.rpm            # install with verbose progress
rpm -Uvh package.rpm            # upgrade
rpm -e package                  # erase/remove
rpm -qa                         # query all installed
rpm -qi nginx                   # package info
rpm -ql nginx                   # files in package
rpm -qf /usr/sbin/nginx         # which package owns file
rpm -qd nginx                   # docs
rpm -qc nginx                   # config files
rpm --verify nginx               # verify package integrity
rpm --checksig package.rpm      # verify signature

# dnf (modern Fedora/RHEL 8+)
dnf install nginx
dnf remove nginx
dnf update
dnf search nginx
dnf info nginx
dnf list installed
dnf list available
dnf provides /usr/bin/python3   # which package provides file
dnf history                     # transaction history
dnf history undo 5              # undo transaction 5
dnf module list                 # AppStream modules
dnf module install php:8.1      # install PHP module stream

# Package groups
dnf group list
dnf group install "Development Tools"
```

### 20.3 Snap, Flatpak, and AppImage

```bash
# Snap — Canonical's sandboxed package format
snap install code               # install VS Code
snap list                       # installed snaps
snap refresh                    # update all snaps
snap refresh code               # update specific
snap remove code                # uninstall
snap info code                  # package info
snap connections code           # snap interfaces/permissions

# Flatpak — sandboxed, distro-agnostic
flatpak install flathub com.spotify.Client
flatpak run com.spotify.Client
flatpak list
flatpak update
flatpak uninstall com.spotify.Client
flatpak permissions             # app permissions

# AppImage — self-contained, no install needed
chmod +x MyApp.AppImage
./MyApp.AppImage                # run directly
```

---

## 21. Kernel Modules & Device Drivers

### 21.1 Kernel Module Basics

```bash
# List loaded modules
lsmod
# Module                  Size  Used by
# btrfs                1474560  0
# xt_conntrack           20480  1

# Load/unload modules
modprobe ext4               # load with dependencies
modprobe -r ext4            # remove module
insmod ./mymodule.ko        # load specific .ko file (no dep resolution)
rmmod mymodule              # remove by name

# Module information
modinfo ext4                # module info
modinfo -p ext4             # module parameters

# Set module parameters
modprobe usbcore autosuspend=5
echo 5 > /sys/module/usbcore/parameters/autosuspend

# Persistent module loading
echo "ext4" >> /etc/modules-load.d/ext4.conf

# Blacklist a module
echo "blacklist nouveau" > /etc/modprobe.d/blacklist-nouveau.conf
update-initramfs -u         # Debian: rebuild initrd
dracut -f                   # RHEL: rebuild initrd

# Module dependencies
depmod -a                   # rebuild module dependency database
cat /lib/modules/$(uname -r)/modules.dep
```

### 21.2 Writing a Minimal Kernel Module in C

```c
// hello_module.c — minimal Linux kernel module
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Educational kernel module");
MODULE_VERSION("1.0");

// Module parameter — adjustable at load time and via /sys/module
static int count = 5;
module_param(count, int, S_IRUGO | S_IWUSR);
MODULE_PARM_DESC(count, "Number of greetings (default: 5)");

static struct proc_dir_entry *proc_entry;

// Called when /proc/hello_module is read
static int hello_show(struct seq_file *m, void *v) {
    int i;
    for (i = 0; i < count; i++) {
        seq_printf(m, "Hello from kernel space! (iteration %d)\n", i + 1);
    }
    return 0;
}

static int hello_open(struct inode *inode, struct file *file) {
    return single_open(file, hello_show, NULL);
}

static const struct proc_ops hello_fops = {
    .proc_open    = hello_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

// Module initialization — called on insmod/modprobe
static int __init hello_init(void) {
    printk(KERN_INFO "hello_module: loaded with count=%d\n", count);
    
    // Create /proc/hello_module
    proc_entry = proc_create("hello_module", 0444, NULL, &hello_fops);
    if (!proc_entry) {
        printk(KERN_ERR "hello_module: failed to create /proc entry\n");
        return -ENOMEM;
    }
    
    return 0;  // 0 = success
}

// Module cleanup — called on rmmod
static void __exit hello_exit(void) {
    proc_remove(proc_entry);
    printk(KERN_INFO "hello_module: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);
```

```makefile
# Makefile for out-of-tree kernel module
obj-m += hello_module.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install: all
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a
```

```bash
# Build and load
make
sudo insmod hello_module.ko count=3
dmesg | tail -5             # see printk output
cat /proc/hello_module      # read from proc
sudo rmmod hello_module
```

---

## 22. Timers, Clocks & Time in Linux

### 22.1 Clock Sources

Linux maintains multiple clocks:

| Clock | `CLOCK_*` ID | Description |
|---|---|---|
| Realtime | CLOCK_REALTIME | Wall clock (UTC), can jump |
| Monotonic | CLOCK_MONOTONIC | Always increasing, no leap seconds |
| Monotonic Raw | CLOCK_MONOTONIC_RAW | Like MONOTONIC, no NTP adjustments |
| Boot time | CLOCK_BOOTTIME | Monotonic + time in suspend |
| Process CPU | CLOCK_PROCESS_CPUTIME_ID | CPU time for this process |
| Thread CPU | CLOCK_THREAD_CPUTIME_ID | CPU time for this thread |

```c
#include <time.h>
#include <stdio.h>

// High-resolution timing
void timing_demo(void) {
    struct timespec start, end;
    
    // Monotonic clock — best for measuring elapsed time
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // ... do work ...
    for (volatile int i = 0; i < 1000000; i++);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("Elapsed: %.9f seconds\n", elapsed);
    
    // Wall clock
    clock_gettime(CLOCK_REALTIME, &start);
    printf("Unix timestamp: %ld.%09ld\n", start.tv_sec, start.tv_nsec);
    
    // CPU time of this process
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start);
    printf("Process CPU time: %ld.%09ld\n", start.tv_sec, start.tv_nsec);
}

// Interval timers
#include <signal.h>
#include <sys/time.h>

static volatile int timer_fired = 0;

void timer_handler(int sig) {
    timer_fired++;
}

void interval_timer_demo(void) {
    signal(SIGALRM, timer_handler);
    
    struct itimerval timer = {
        .it_interval = { .tv_sec = 0, .tv_usec = 100000 },  // repeat every 100ms
        .it_value    = { .tv_sec = 0, .tv_usec = 100000 },  // first fire after 100ms
    };
    
    setitimer(ITIMER_REAL, &timer, NULL);
    
    sleep(1);
    printf("Timer fired %d times in 1 second\n", timer_fired);
}

// timerfd — timer as file descriptor (integrates with epoll)
#include <sys/timerfd.h>

int timerfd_demo(void) {
    int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
    
    struct itimerspec spec = {
        .it_interval = { .tv_sec = 1, .tv_nsec = 0 },  // repeat every second
        .it_value    = { .tv_sec = 1, .tv_nsec = 0 },  // fire after 1s
    };
    
    timerfd_settime(tfd, 0, &spec, NULL);
    
    // Now tfd is readable when timer fires
    // Can be added to epoll alongside other fds!
    uint64_t expirations;
    read(tfd, &expirations, sizeof(expirations));
    printf("Timer fired %lu times\n", expirations);
    
    close(tfd);
    return 0;
}
```

### 22.2 Time Synchronization

```bash
# NTP / chrony (modern Linux)
timedatectl status          # system time status
timedatectl set-ntp true    # enable NTP
timedatectl set-timezone UTC
timedatectl list-timezones

chronyc tracking            # sync status
chronyc sources             # NTP sources
chronyc sourcestats         # source statistics
chronyc makestep            # force time step

# systemd-timesyncd (lightweight NTP client)
systemctl status systemd-timesyncd
cat /etc/systemd/timesyncd.conf

# Date manipulation
date                            # current date/time
date -u                         # UTC
date +"%Y-%m-%d %H:%M:%S"      # custom format
date -d "2024-01-01"           # parse date
date -d "now + 7 days"         # relative date
date -d "@1704067200"          # from Unix timestamp
date +%s                        # current Unix timestamp
```

---

## 23. Synchronization Primitives

### 23.1 Mutexes, Semaphores, and Condition Variables (pthreads)

```c
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>

// Mutex — mutual exclusion
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int shared_counter = 0;

void *increment_counter(void *arg) {
    for (int i = 0; i < 100000; i++) {
        pthread_mutex_lock(&mutex);
        shared_counter++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

// Read-Write lock — multiple readers or one writer
pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

void *reader(void *arg) {
    pthread_rwlock_rdlock(&rwlock);
    // multiple readers can hold this simultaneously
    printf("Reading: %d\n", shared_counter);
    pthread_rwlock_unlock(&rwlock);
    return NULL;
}

void *writer(void *arg) {
    pthread_rwlock_wrlock(&rwlock);
    // exclusive write access
    shared_counter = 0;
    pthread_rwlock_unlock(&rwlock);
    return NULL;
}

// Condition variable — wait for condition, signal/broadcast
pthread_mutex_t cond_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
int items_available = 0;

void *producer(void *arg) {
    pthread_mutex_lock(&cond_mutex);
    items_available = 10;
    pthread_cond_signal(&cond);      // wake one waiter
    // pthread_cond_broadcast(&cond); // wake all waiters
    pthread_mutex_unlock(&cond_mutex);
    return NULL;
}

void *consumer(void *arg) {
    pthread_mutex_lock(&cond_mutex);
    
    // Must loop — spurious wakeups are possible
    while (items_available == 0) {
        pthread_cond_wait(&cond, &cond_mutex);  // atomically unlock + sleep
    }
    
    items_available--;
    pthread_mutex_unlock(&cond_mutex);
    return NULL;
}

// POSIX semaphore
sem_t semaphore;

void semaphore_demo(void) {
    sem_init(&semaphore, 0, 1);  // initial value 1 (binary semaphore)
    
    sem_wait(&semaphore);    // P() — decrement, block if 0
    // critical section
    sem_post(&semaphore);    // V() — increment, wake waiter
    
    sem_destroy(&semaphore);
}
```

### 23.2 Atomic Operations

```c
#include <stdatomic.h>
#include <pthread.h>

// C11 atomics — compiler guarantees these are atomic without locks
atomic_int atomic_counter = ATOMIC_VAR_INIT(0);

void *atomic_increment(void *arg) {
    for (int i = 0; i < 100000; i++) {
        atomic_fetch_add(&atomic_counter, 1);
        // Also: atomic_store, atomic_load, atomic_exchange,
        //        atomic_compare_exchange_strong, atomic_compare_exchange_weak
    }
    return NULL;
}

// Memory ordering
// memory_order_relaxed   — no synchronization guarantee
// memory_order_acquire   — establish happens-before for subsequent reads
// memory_order_release   — establish happens-before for preceding writes
// memory_order_acq_rel   — acquire + release (for read-modify-write)
// memory_order_seq_cst   — total sequential consistency (default, slowest)

atomic_flag flag = ATOMIC_FLAG_INIT;

void spinlock_lock(atomic_flag *lock) {
    while (atomic_flag_test_and_set_explicit(lock, memory_order_acquire))
        ;  // spin
}

void spinlock_unlock(atomic_flag *lock) {
    atomic_flag_clear_explicit(lock, memory_order_release);
}
```

### 23.3 Rust: `std::sync` and `std::atomic`

```rust
use std::sync::{Arc, Mutex, RwLock, Condvar};
use std::sync::atomic::{AtomicI64, Ordering};
use std::thread;

// Mutex
fn mutex_example() {
    let counter = Arc::new(Mutex::new(0i64));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let h = thread::spawn(move || {
            let mut c = counter.lock().unwrap();
            *c += 1;
            // MutexGuard auto-unlocks when dropped
        });
        handles.push(h);
    }

    for h in handles { h.join().unwrap(); }
    println!("Counter: {}", *counter.lock().unwrap());
}

// Atomics — lock-free
fn atomic_example() {
    let counter = Arc::new(AtomicI64::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let h = thread::spawn(move || {
            counter.fetch_add(1, Ordering::Relaxed);
        });
        handles.push(h);
    }

    for h in handles { h.join().unwrap(); }
    println!("Atomic counter: {}", counter.load(Ordering::SeqCst));
}

// Channel — message passing (preferred in Rust)
fn channel_example() {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel::<String>();
    
    let producer = thread::spawn(move || {
        for i in 0..5 {
            tx.send(format!("message {}", i)).unwrap();
        }
    });

    let consumer = thread::spawn(move || {
        for msg in rx {
            println!("Received: {}", msg);
        }
    });

    producer.join().unwrap();
    consumer.join().unwrap();
}
```

---

## 24. eBPF: Programmable Kernel Observability

### 24.1 What is eBPF?

eBPF (extended Berkeley Packet Filter) is a revolutionary kernel technology that allows running sandboxed programs in the kernel without modifying kernel source or loading kernel modules. The kernel verifies eBPF programs for safety before loading them.

Use cases:
- **Observability**: trace any kernel/user function, syscall, network packet
- **Networking**: high-performance packet filtering, load balancing (XDP)
- **Security**: system call filtering, runtime threat detection (Falco)
- **Performance**: profiling, latency measurement

### 24.2 BCC and bpftrace Tools

```bash
# bpftrace — high-level eBPF scripting
bpftrace -l 'tracepoint:syscalls:*'           # list all syscall tracepoints
bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("exec: %s\n", str(args->filename)); }'
bpftrace -e 'profile:hz:99 { @[kstack] = count(); }'    # CPU flame graph data
bpftrace -e 'kretprobe:vfs_read { @bytes = hist(retval); }'  # read size histogram
bpftrace -e 'tracepoint:sched:sched_switch { @[args->next_comm] = count(); }'

# One-liner: system call counts by process
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# bpftrace script
cat << 'EOF' > syscall_latency.bt
tracepoint:syscalls:sys_enter_read
{
    @start[tid] = nsecs;
}

tracepoint:syscalls:sys_exit_read
/ @start[tid] /
{
    @latency = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}

END { clear(@start); }
EOF

bpftrace syscall_latency.bt

# BCC tools (Python-based eBPF tools)
# Install: apt install bpfcc-tools / yum install bcc-tools

opensnoop              # trace file opens
execsnoop              # trace process execution
tcpconnect             # trace TCP connections initiated
tcpaccept              # trace TCP connections accepted
tcpretrans             # trace TCP retransmissions
tcplife                # trace TCP connection lifespans
biolatency -D          # block I/O latency histogram, by disk
biosnoop               # trace block I/O with PID
runqlat                # scheduler run queue latency
cpudist                # on-CPU time distribution
offcputime             # off-CPU time analysis
fileslower 10          # files slower than 10ms
dbslower               # DB queries slower than threshold
mysqld_qslower         # MySQL slow queries
funccount              # count function calls
funclatency            # function call latency
trace 'do_sys_open "%s", arg2'    # trace with arguments
```

### 24.3 eBPF C Program Example

```c
// Simple eBPF program: count syscalls by PID
// Compiled with clang, loaded with libbpf

// eBPF kernel-side code (runs in kernel)
// Filename: syscall_count.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

// BPF map: key=PID, value=syscall count
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, u32);
    __type(value, u64);
    __uint(max_entries, 10240);
} syscall_counts SEC(".maps");

SEC("tracepoint/raw_syscalls/sys_enter")
int count_syscalls(struct trace_event_raw_sys_enter *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u64 *count = bpf_map_lookup_elem(&syscall_counts, &pid);
    
    if (count) {
        (*count)++;
    } else {
        u64 one = 1;
        bpf_map_update_elem(&syscall_counts, &pid, &one, BPF_ANY);
    }
    
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 25. Build Systems & Compilation Toolchain

### 25.1 GCC and Clang

```bash
# Compilation stages
gcc -E source.c            # Preprocessor only (expand macros, includes)
gcc -S source.c            # Compile to assembly (.s)
gcc -c source.c            # Compile to object file (.o)
gcc source.c -o binary     # Full compilation

# Important flags
gcc -O0 source.c           # No optimization (debug)
gcc -O1 source.c           # Basic optimization
gcc -O2 source.c           # Standard optimization (production)
gcc -O3 source.c           # Aggressive optimization
gcc -Os source.c           # Optimize for size
gcc -Og source.c           # Optimize for debugging

gcc -g source.c            # Debug symbols (DWARF)
gcc -g3 source.c           # Maximum debug info including macros
gcc -Wall -Wextra source.c # Enable most warnings
gcc -Werror source.c       # Treat warnings as errors
gcc -pedantic source.c     # Strict ISO compliance

# Security hardening
gcc -D_FORTIFY_SOURCE=2    # Buffer overflow protection in libc
gcc -fstack-protector-strong  # Stack canary
gcc -fPIE -pie             # Position-Independent Executable (ASLR)
gcc -fPIC                  # Position-Independent Code (shared libs)
gcc -z now -z relro        # Linker: read-only GOT after startup
gcc -fsanitize=address     # AddressSanitizer (memory error detection)
gcc -fsanitize=thread      # ThreadSanitizer (data race detection)
gcc -fsanitize=undefined   # UndefinedBehaviorSanitizer

# Cross compilation
gcc --target=aarch64-linux-gnu source.c  # compile for ARM64
aarch64-linux-gnu-gcc source.c           # using cross compiler

# Linking
gcc obj1.o obj2.o -o binary            # link objects
gcc source.c -lm -lpthread -o binary   # link libraries
gcc source.c -L/usr/local/lib -lmylib  # custom library path
gcc -static source.c -o binary-static  # static linking

# Inspect binary
file binary                 # type information
readelf -h binary           # ELF header
readelf -S binary           # section headers
readelf -d binary           # dynamic section (shared libs)
objdump -d binary           # disassemble
objdump -D binary           # disassemble all sections
nm binary                   # symbol table
ldd binary                  # shared library dependencies
strings binary              # printable strings
strip binary                # remove symbols (smaller binary)
size binary                 # section sizes
```

### 25.2 Make and CMake

```makefile
# Makefile — classic build system
# Variables
CC      := gcc
CFLAGS  := -Wall -Wextra -O2 -g -std=c11
LDFLAGS := -lm -lpthread
SRCDIR  := src
OBJDIR  := obj
BINDIR  := bin

# Automatic variables:
# $@ — target name
# $< — first prerequisite
# $^ — all prerequisites
# $* — stem (without suffix)

SOURCES := $(wildcard $(SRCDIR)/*.c)
OBJECTS := $(patsubst $(SRCDIR)/%.c, $(OBJDIR)/%.o, $(SOURCES))
TARGET  := $(BINDIR)/myapp

# Phony targets (not files)
.PHONY: all clean install test

all: $(TARGET)

# Link
$(TARGET): $(OBJECTS) | $(BINDIR)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

# Compile with automatic dependency generation
$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

# Include auto-generated dependency files
-include $(OBJECTS:.o=.d)

$(OBJDIR) $(BINDIR):
	mkdir -p $@

clean:
	rm -rf $(OBJDIR) $(BINDIR)

install: $(TARGET)
	install -Dm755 $(TARGET) /usr/local/bin/myapp

# Run tests
test: $(TARGET)
	./run_tests.sh
```

```cmake
# CMakeLists.txt — modern CMake
cmake_minimum_required(VERSION 3.20)
project(MyProject VERSION 1.0.0 LANGUAGES C CXX)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# C++ standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags
add_compile_options(
    -Wall -Wextra -Wpedantic
    $<$<CONFIG:Release>:-O2>
    $<$<CONFIG:Debug>:-g -fsanitize=address,undefined>
)

# Find packages
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)

# Static library
add_library(mylib STATIC
    src/network.c
    src/parser.c
    src/utils.c
)
target_include_directories(mylib PUBLIC include)

# Executable
add_executable(myapp src/main.c)
target_link_libraries(myapp
    PRIVATE mylib
    PRIVATE Threads::Threads
    PRIVATE OpenSSL::SSL OpenSSL::Crypto
)

# Installation
install(TARGETS myapp DESTINATION bin)
install(FILES include/mylib.h DESTINATION include)

# Tests
enable_testing()
add_executable(test_parser tests/test_parser.c)
target_link_libraries(test_parser PRIVATE mylib)
add_test(NAME parser_tests COMMAND test_parser)
```

```bash
# CMake build workflow
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --parallel $(nproc)
ctest --verbose
cmake --install . --prefix /usr/local
```

### 25.3 Cargo (Rust)

```bash
# Project setup
cargo new myproject --bin        # binary project
cargo new mylib --lib            # library project
cargo init                       # in existing directory

# Build
cargo build                      # debug build
cargo build --release            # optimized release build
cargo build --target x86_64-unknown-linux-musl  # statically linked

# Run
cargo run                        # build + run
cargo run -- --arg1 value1       # pass args to program

# Test
cargo test                       # all tests
cargo test test_name             # specific test
cargo test -- --nocapture        # show println output

# Benchmarks (requires nightly or criterion)
cargo bench

# Dependencies
cargo add serde                  # add dependency
cargo add serde --features derive
cargo update                     # update dependencies
cargo audit                      # check for security vulnerabilities

# Cross-compilation
rustup target add aarch64-unknown-linux-gnu
cargo build --target aarch64-unknown-linux-gnu

# Cargo.toml
cat > Cargo.toml << 'EOF'
[package]
name = "myapp"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "myapp"
path = "src/main.rs"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
clap = { version = "4", features = ["derive"] }
tracing = "0.1"
tracing-subscriber = "0.3"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true

[profile.dev]
opt-level = 0
debug = true
EOF
```

---

## 26. Debugging Tools: gdb, strace, ltrace, valgrind

### 26.1 `gdb`: GNU Debugger

```bash
# Launch
gdb ./myprogram
gdb ./myprogram core          # debug from core dump
gdb -p 1234                   # attach to running process
gdb --args ./myprogram arg1 arg2

# Core dump setup
ulimit -c unlimited            # enable core dumps
echo "/tmp/core.%e.%p" > /proc/sys/kernel/core_pattern
./myprogram                    # if it crashes, creates core file
gdb ./myprogram /tmp/core.myprogram.1234
```

```gdb
# GDB Commands

# Execution control
run                    # start program
run arg1 arg2          # with args
continue               # continue after breakpoint
next (n)               # step over
step (s)               # step into
finish                 # run until function returns
until 42               # run until line 42
jump 100               # jump to line 100 (dangerous)
kill                   # kill inferior

# Breakpoints
break main             # break at function
break file.c:42        # break at line
break *0x400592        # break at address
info breakpoints       # list breakpoints
delete 1               # delete breakpoint 1
disable 1              # disable breakpoint
enable 1               # enable breakpoint
condition 1 x > 10     # conditional breakpoint
commands 1             # commands to run at breakpoint 1
  printf "x = %d\n", x
  continue
end
watch x                # watchpoint — stop when x changes
rwatch x               # stop when x is read
awatch x               # stop on read or write

# Inspection
print x                # print variable
print *ptr             # dereference pointer
print arr[0]@10        # print 10 elements of array
display x              # auto-print on each stop
x/10i $pc             # examine 10 instructions at PC
x/16xb 0x404000       # 16 hex bytes at address
x/s 0x404000          # string at address

# Stack
backtrace (bt)         # call stack
frame 3                # switch to frame 3
up / down              # navigate frames
info locals            # local variables
info args              # function arguments

# Threads
info threads           # list threads
thread 2               # switch to thread 2
thread apply all bt    # backtrace all threads

# Memory
ptype struct task      # print type definition
info registers         # all registers
info register rsp      # specific register
set variable x = 42   # modify variable
set *(int*)0x404000 = 99  # write to memory

# Source
list 40                # source around line 40
list function_name     # source of function
directory /src/path    # add source path

# Signals
handle SIGSEGV stop print   # stop on SIGSEGV
handle SIGALRM noprint nostop pass  # pass SIGALRM to program

# Python scripting in GDB
python gdb.execute("break main")
```

### 26.2 `valgrind`: Memory Error Detection

```bash
# Memcheck — detect memory errors
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --error-exitcode=1 \
         ./myprogram

# Types of errors detected:
# - Use of uninitialized memory
# - Reading/writing past end of malloc'd blocks
# - Reading/writing freed memory
# - Memory leaks (definitely lost, indirectly lost, possibly lost)
# - Double-free

# Callgrind — CPU profiling
valgrind --tool=callgrind ./myprogram
callgrind_annotate callgrind.out.PID

# Massif — heap profiler
valgrind --tool=massif ./myprogram
ms_print massif.out.PID

# Helgrind — thread error detection
valgrind --tool=helgrind ./myprogram
```

### 26.3 `ltrace`: Library Call Tracer

```bash
# Trace library calls (unlike strace which traces syscalls)
ltrace ./myprogram
ltrace -l libssl.so.1.1 ./myprogram  # specific library only
ltrace -S ./myprogram                  # include syscalls

# Example output:
# malloc(1024)                                         = 0x55a1234b8280
# fopen("/etc/config", "r")                            = 0x7f1234567890
# strcmp("hello", "world")                             = -15
```

### 26.4 Rust Debugging

```bash
# Build with debug info
cargo build                    # debug by default

# GDB / LLDB
rust-gdb target/debug/myapp   # GDB with Rust pretty printers
rust-lldb target/debug/myapp  # LLDB

# Environment variables
RUST_BACKTRACE=1 cargo run     # show backtrace on panic
RUST_BACKTRACE=full cargo run  # full backtrace
RUST_LOG=debug cargo run       # if using log/tracing crate

# AddressSanitizer
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build   # ThreadSanitizer
RUSTFLAGS="-Z sanitizer=memory" cargo +nightly build   # MemorySanitizer

# cargo-flamegraph
cargo flamegraph               # profile + generate flame graph

# Miri — undefined behavior detector (interpreter)
cargo +nightly miri run        # run under Miri interpreter
cargo +nightly miri test
```

---

## 27. Rust Systems Programming on Linux

### 27.1 File I/O

```rust
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::Path;

fn file_io_patterns() -> io::Result<()> {
    // Simple read entire file
    let content = fs::read_to_string("/etc/hostname")?;
    println!("Hostname: {}", content.trim());

    // Buffered reading — efficient for large files
    let file = File::open("/etc/passwd")?;
    let reader = BufReader::new(file);
    
    for line in reader.lines() {
        let line = line?;
        if line.starts_with('#') { continue; }
        let fields: Vec<&str> = line.splitn(7, ':').collect();
        if fields.len() >= 7 {
            println!("User: {} Shell: {}", fields[0], fields[6]);
        }
    }

    // Buffered writing
    let file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open("/tmp/output.txt")?;
    
    let mut writer = BufWriter::new(file);
    for i in 0..1000 {
        writeln!(writer, "Line {}", i)?;
    }
    writer.flush()?;   // BufWriter must be flushed explicitly

    // Memory-mapped file access
    use memmap2::MmapOptions;
    let file = File::open("/etc/passwd")?;
    let mmap = unsafe { MmapOptions::new().map(&file)? };
    let content = std::str::from_utf8(&mmap).unwrap_or("<binary>");
    println!("First 50 chars: {}", &content[..50.min(content.len())]);

    Ok(())
}
```

### 27.2 Process and Signal Handling in Rust

```rust
use signal_hook::{consts::*, iterator::Signals};
use std::thread;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

fn graceful_shutdown_example() -> anyhow::Result<()> {
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    // Register signal handlers
    let mut signals = Signals::new(&[SIGTERM, SIGINT, SIGHUP])?;
    
    thread::spawn(move || {
        for sig in signals.forever() {
            match sig {
                SIGTERM | SIGINT => {
                    eprintln!("Received shutdown signal {}", sig);
                    r.store(false, Ordering::SeqCst);
                }
                SIGHUP => {
                    eprintln!("Received SIGHUP — reload config");
                    // trigger config reload
                }
                _ => unreachable!()
            }
        }
    });

    // Main loop
    while running.load(Ordering::SeqCst) {
        // do work
        thread::sleep(std::time::Duration::from_millis(100));
    }

    println!("Shutting down gracefully...");
    Ok(())
}
```

### 27.3 Networking in Rust

```rust
use std::net::{TcpListener, TcpStream};
use std::io::{Read, Write, BufRead, BufReader};
use std::thread;

// Single-threaded TCP server (synchronous)
fn sync_tcp_server() -> std::io::Result<()> {
    let listener = TcpListener::bind("0.0.0.0:8080")?;
    println!("Listening on :8080");

    for stream in listener.incoming() {
        let stream = stream?;
        thread::spawn(|| handle_connection(stream));
    }
    Ok(())
}

fn handle_connection(mut stream: TcpStream) {
    let peer = stream.peer_addr().unwrap();
    println!("Connection from {}", peer);

    let mut reader = BufReader::new(stream.try_clone().unwrap());
    let mut request_line = String::new();
    reader.read_line(&mut request_line).unwrap();

    let response = b"HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\nHello World!";
    stream.write_all(response).unwrap();
}

// Async server with Tokio (production pattern)
use tokio::net::TcpListener as AsyncTcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn async_tcp_server() -> std::io::Result<()> {
    let listener = AsyncTcpListener::bind("0.0.0.0:8080").await?;
    
    loop {
        let (mut socket, addr) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buf = [0u8; 1024];
            loop {
                match socket.read(&mut buf).await {
                    Ok(0) => break,    // connection closed
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

### 27.4 Linux-Specific APIs in Rust

```rust
use nix::sys::socket::{
    socket, bind, listen, accept, recv, send,
    AddressFamily, SockType, SockFlag, SockAddr
};
use nix::unistd::{read, write, close};
use std::os::unix::io::RawFd;

// Direct inotify usage for file system monitoring
use inotify::{Inotify, WatchMask};

fn watch_directory() -> std::io::Result<()> {
    let mut inotify = Inotify::init()?;
    
    inotify.watches().add(
        "/etc/",
        WatchMask::MODIFY | WatchMask::CREATE | WatchMask::DELETE,
    )?;

    let mut buffer = [0u8; 4096];
    loop {
        let events = inotify.read_events_blocking(&mut buffer)?;
        for event in events {
            if let Some(name) = event.name {
                println!("Event {:?} on: {:?}", event.mask, name);
            }
        }
    }
}

// procfs crate for reading /proc
use procfs::process::Process;

fn process_info(pid: i32) -> procfs::ProcResult<()> {
    let process = Process::new(pid)?;
    
    let stat = process.stat()?;
    println!("Name: {}", stat.comm);
    println!("State: {:?}", stat.state());
    println!("Virtual memory: {} bytes", stat.vsize);
    println!("RSS: {} pages", stat.rss);
    
    let maps = process.maps()?;
    for map in maps {
        println!("{:x?}-{:x?} {:?} {:?}",
            map.address.0, map.address.1,
            map.perms, map.pathname);
    }
    
    Ok(())
}

// Using libc directly for platform-specific calls
use libc::{self, c_int, c_void, size_t, ssize_t};

unsafe fn raw_sendfile(out_fd: c_int, in_fd: c_int, offset: &mut libc::off_t, count: size_t) -> ssize_t {
    libc::sendfile(out_fd, in_fd, offset, count)
}

// seccomp-bpf for sandboxing
// Restrict syscalls a process can make
use seccompiler::{
    BpfProgram, SeccompAction, SeccompFilter, SeccompRule, SeccompCondition,
    CompareOp,
};

fn sandbox_with_seccomp() -> Result<(), Box<dyn std::error::Error>> {
    // Allow only specific syscalls, deny everything else
    let filter = SeccompFilter::new(
        [
            (libc::SYS_read as i64, vec![SeccompRule::new(vec![])?]),
            (libc::SYS_write as i64, vec![SeccompRule::new(vec![])?]),
            (libc::SYS_exit_group as i64, vec![SeccompRule::new(vec![])?]),
            (libc::SYS_brk as i64, vec![SeccompRule::new(vec![])?]),
        ].into(),
        SeccompAction::KillProcess,  // kill on denied syscall
        SeccompAction::Allow,
        std::env::consts::ARCH.try_into()?,
    )?;
    
    let bpf_prog: BpfProgram = filter.try_into()?;
    seccompiler::apply_filter(&bpf_prog)?;
    
    // From this point, only read/write/exit_group/brk are allowed
    Ok(())
}
```

---

## Appendix A: Essential One-Liners

```bash
# System info
uname -a                                    # kernel, hostname, arch
lscpu | grep -E 'Architecture|CPU\(s\)|Thread'  # CPU info
lsmem | grep -i total                        # memory info
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT          # block devices
lshw -short 2>/dev/null                     # hardware summary

# Find the process eating the most CPU
ps aux --sort=-%cpu | awk 'NR<=6{print}' 

# Find all open listening ports
ss -tlnp | awk 'NR>1{print $4}' | sort -u

# Real-time network I/O per process
nethogs eth0

# Disk usage sorted, human-readable, top 20
du -h /var --max-depth=2 2>/dev/null | sort -rh | head -20

# Count lines of code by extension
find . -name "*.rs" | xargs wc -l | tail -1

# Recursively replace string in files
grep -rl "old_string" --include="*.py" . | xargs sed -i 's/old_string/new_string/g'

# Generate strong password
openssl rand -base64 32

# Watch for new files in a directory
inotifywait -m -e create /tmp/

# Extract substring matching a pattern from logs
grep -oP 'duration=\K[0-9.]+' app.log | awk '{s+=$1; n++} END{print s/n " avg ms"}'

# Kill all processes matching name
pkill -f "pattern" || true

# Check if port is open remotely
timeout 3 bash -c "echo >/dev/tcp/host/port" && echo "open" || echo "closed"

# Run command on remote host
ssh user@host 'command --option'

# Copy file tree with attributes
rsync -avzP source/ dest/

# Quick HTTP server
python3 -m http.server 8080

# Base64 encode/decode
echo "hello" | base64
echo "aGVsbG8K" | base64 -d

# JSON pretty print
echo '{"a":1}' | python3 -m json.tool
echo '{"a":1}' | jq '.'

# Watch file for changes
inotifywait -e modify -m /etc/nginx/nginx.conf | while read; do nginx -s reload; done

# Generate self-signed TLS cert
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Check SSL certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates

# System call count for a command
strace -c -e trace=all command 2>&1 | tail -20

# Memory map of PID
cat /proc/PID/maps | awk '{print $5}' | sort | uniq -c | sort -rn
```

---

## Appendix B: Kernel Tuning (`sysctl`)

```bash
# View all settings
sysctl -a

# Network tuning
sysctl net.core.somaxconn=65535          # listen() backlog
sysctl net.ipv4.tcp_max_syn_backlog=65535
sysctl net.core.netdev_max_backlog=65535
sysctl net.ipv4.tcp_fin_timeout=15       # FIN_WAIT timeout (default 60)
sysctl net.ipv4.tcp_keepalive_time=300   # keepalive interval
sysctl net.ipv4.ip_local_port_range="1024 65535"
sysctl net.ipv4.tcp_tw_reuse=1          # reuse TIME_WAIT sockets
sysctl net.core.rmem_max=134217728      # socket receive buffer max (128MB)
sysctl net.core.wmem_max=134217728      # socket send buffer max
sysctl net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl net.ipv4.tcp_wmem="4096 65536 134217728"

# Virtual memory
sysctl vm.swappiness=10                 # prefer RAM over swap (0-100)
sysctl vm.dirty_ratio=10               # start sync writeback at 10% dirty
sysctl vm.dirty_background_ratio=5     # start background writeback at 5%
sysctl vm.overcommit_memory=1          # allow overcommit (containers)
sysctl vm.nr_hugepages=512             # allocate 512 huge pages (1GB)

# Kernel
sysctl kernel.pid_max=4194304          # max PID
sysctl kernel.threads-max=4194304      # max threads
sysctl kernel.ngroups_max=65536        # max supplementary groups
sysctl kernel.dmesg_restrict=1         # restrict dmesg to root
sysctl kernel.kptr_restrict=2          # hide kernel pointers
sysctl kernel.perf_event_paranoid=-1   # allow perf for all (dangerous)

# File system
sysctl fs.file-max=2097152             # system-wide file descriptor limit
sysctl fs.inotify.max_user_watches=524288

# Make persistent
echo "net.core.somaxconn=65535" >> /etc/sysctl.conf
sysctl -p                               # reload from file
sysctl -p /etc/sysctl.d/99-custom.conf
```

---

## Appendix C: Cheat Sheet — Key Signals for Daemons

| Action | Signal | Command |
|---|---|---|
| Graceful stop | SIGTERM (15) | `kill -15 $pid` |
| Force kill | SIGKILL (9) | `kill -9 $pid` |
| Reload config | SIGHUP (1) | `kill -HUP $pid` |
| Reopen logs | SIGUSR1 (10) | `kill -USR1 $pid` |
| Graceful rotate | SIGUSR2 (12) | `kill -USR2 $pid` |
| Pause | SIGSTOP (19) | `kill -STOP $pid` |
| Resume | SIGCONT (18) | `kill -CONT $pid` |
| Core dump | SIGQUIT (3) | `kill -QUIT $pid` |

---

*End of Guide — Version 1.0 | April 2026*

I'll write this directly — it's going to be a very large, deeply technical document. Building it now.**5,204 lines / 158KB** of dense, production-grade reference material. Here's what's covered across the 27 chapters:

**Kernel Internals** — The full architecture from Ring 0/Ring 3 privilege separation down to `task_struct`, CFS scheduler red-black tree vruntime math, VFS dispatch tables, buddy allocator, slab/SLUB, and page table mechanics. Raw syscall assembly (no libc), the `entry_SYSCALL_64` path, and KPTI overhead explained.

**Process Model** — COW fork internals, all task states including why `D` state can't be killed, clone flags that distinguish threads from processes, SCHED_DEADLINE/CFS/RT scheduling classes, and real priority math.

**I/O Subsystem** — FD table → open file table → inode relationships, `epoll` edge vs. level triggered, `mmap` mechanics, `sendfile`/`splice` zero-copy paths, and full async Tokio internals (how it maps to epoll).

**IPC** — Pipe ring buffers, PIPE_BUF atomicity, POSIX shm, Unix domain socket `SCM_RIGHTS` (passing file descriptors between processes), all IPC mechanisms with latency/throughput tradeoffs.

**Namespaces & Containers** — All 8 namespace types, `clone()` flags that implement them, a minimal container runtime in C using `clone()`, namespace persistence via bind mounts.

**cgroups v2** — Unified hierarchy, memory/CPU controllers, OOM kill groups, systemd integration, programmatic C API to cgroups.

**C and Rust throughout** — Raw syscalls in assembly, signal handlers with the self-pipe trick, pthread mutex/condvar/rwlock/atomics, Rust's `nix` crate for low-level ops, Tokio for async I/O, `signal-hook` for graceful shutdown, `inotify`, `seccomp-bpf` sandboxing, and direct `libc` calls.

**Tooling** — Deep coverage of `grep`/`sed`/`awk` including engine internals, `find`/`xargs` production patterns, `perf` flame graphs, `bpftrace`/BCC for eBPF observability, `gdb` with full command reference, `valgrind` memcheck/callgrind/helgrind, kernel module writing and loading.

