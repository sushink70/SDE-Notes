# System Calls: Comprehensive Deep Dive

**EXECUTIVE SUMMARY**
System calls are the fundamental interface between user-space processes and the kernel, representing a critical security boundary and privilege escalation mechanism in modern operating systems. They enable controlled access to hardware resources, enforce isolation, and implement the principle of least privilege through ring-based protection. Understanding syscalls is essential for secure systems engineering, as they are the primary attack surface for privilege escalation, side-channel attacks, and kernel exploits. This guide covers architectural mechanisms (int 0x80, syscall/sysenter, vDSO), security boundaries (ring transitions, ASLR, seccomp), performance implications (context switching costs, vDSO optimization), and practical tooling for auditing, tracing, and hardening syscall-based systems.

---

## 1. FOUNDATIONAL CONCEPTS & ARCHITECTURE

### What Are System Calls?

System calls are **synchronous software interrupts** that transfer execution from unprivileged user mode (ring 3) to privileged kernel mode (ring 0), allowing controlled access to:
- Hardware resources (CPU, memory, I/O devices)
- Privileged instructions (page table manipulation, interrupt handling)
- Kernel data structures (process tables, file descriptors)

**Key Properties:**
- **Synchronous**: Triggered explicitly by user code (vs. asynchronous hardware interrupts)
- **Security boundary**: Primary mechanism enforcing user/kernel separation
- **Numbered interface**: Each syscall has a unique number (e.g., `write` = 1 on x86-64)
- **ABI contract**: Stable interface between userland and kernel

### Architecture Overview (x86-64 Linux)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER SPACE (Ring 3)                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│  │  Application │────▶│  libc/musl   │────▶│  Syscall     │       │
│  │  (your code) │     │  (wrapper)   │     │  Stub        │       │
│  └──────────────┘     └──────────────┘     └──────┬───────┘       │
│                                                     │               │
│                                                     │ syscall/int   │
└─────────────────────────────────────────────────────┼───────────────┘
                                                      │
                    ┌─────────────────────────────────▼──────┐
                    │     PRIVILEGE LEVEL TRANSITION         │
                    │   Ring 3 → Ring 0 (CPU enforced)       │
                    └─────────────────────────────────────┬──┘
                                                          │
┌─────────────────────────────────────────────────────────▼─────────┐
│                     KERNEL SPACE (Ring 0)                         │
│  ┌────────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │ Entry Point    │───▶│  Syscall     │───▶│  Handler        │  │
│  │ (entry_64.S)   │    │  Dispatcher  │    │  (sys_write)    │  │
│  └────────────────┘    └──────────────┘    └────────┬────────┘  │
│                                                      │            │
│  ┌───────────────────────────────────────────────────▼──────────┐│
│  │         Kernel Subsystems                                    ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ││
│  │  │   VFS    │ │   MM     │ │   NET    │ │   IPC    │       ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │              Hardware Abstraction Layer                      ││
│  │         (Device Drivers, DMA, Interrupt Handlers)            ││
│  └──────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │   HARDWARE    │
                          │  (Ring -1/-2) │
                          └───────────────┘
```

---

## 2. SYSCALL MECHANISMS: DEEP DIVE

### 2.1 Historical Evolution

**int 0x80 (Legacy, i386)**
```asm
; Old mechanism (slow, ~300 cycles overhead)
mov eax, 4          ; syscall number (write)
mov ebx, 1          ; fd (stdout)
mov ecx, msg        ; buffer
mov edx, len        ; count
int 0x80            ; software interrupt
```

**Problems:**
- Expensive microcode interrupt handling
- Full context save/restore
- Pipeline flush

**sysenter/sysexit (Pentium II+)**
```asm
; Fast path, but complex setup
; Requires MSR configuration by kernel
sysenter            ; ~75 cycles
```

**syscall/sysret (AMD64/Intel 64 - Modern)**
```asm
; Current standard on x86-64
mov rax, 1          ; syscall number (write)
mov rdi, 1          ; arg1: fd
mov rsi, msg        ; arg2: buf
mov rdx, len        ; arg3: count
syscall             ; ~50-70 cycles
```

### 2.2 Calling Convention (x86-64 Linux)

**Register Mapping:**
```
rax = syscall number
rdi = arg1
rsi = arg2
rdx = arg3
r10 = arg4  (NOT rcx! rcx holds return address)
r8  = arg5
r9  = arg6
```

**Return value:** `rax` contains result (-errno on error)

### 2.3 Kernel Entry Point (Linux x86-64)

```c
// arch/x86/entry/entry_64.S (simplified)

ENTRY(entry_SYSCALL_64)
    // Save user registers to kernel stack
    SAVE_REGS
    
    // Switch to kernel GS segment
    SWAPGS
    
    // Load kernel stack
    movq PER_CPU_VAR(cpu_current_top_of_stack), %rsp
    
    // Push user stack pointer
    pushq %rcx    // RIP
    pushq %r11    // RFLAGS
    
    // Validate syscall number
    cmpq $__NR_syscall_max, %rax
    ja 1f
    
    // Call handler via syscall table
    call *sys_call_table(, %rax, 8)
    
    // Restore user context
    RESTORE_REGS
    SWAPGS
    sysretq

1:  // Invalid syscall
    movq $-ENOSYS, %rax
    jmp return_path
END(entry_SYSCALL_64)
```

### 2.4 vDSO (Virtual Dynamic Shared Object)

**Problem:** Some syscalls (gettimeofday, clock_gettime) are called frequently but don't need kernel privileges.

**Solution:** vDSO maps kernel code into userspace for zero-cost syscalls.

```c
// Userspace sees these as normal functions
#include <time.h>

struct timespec ts;
// NO syscall! Maps to vDSO code
clock_gettime(CLOCK_MONOTONIC, &ts);
```

**vDSO mapping inspection:**
```bash
cat /proc/self/maps | grep vdso
# 7ffff7ffa000-7ffff7ffc000 r-xp 00000000 00:00 0 [vdso]

readelf -s /proc/self/exe | grep FUNC | grep clock_gettime
```

---

## 3. HANDS-ON: MAKING SYSCALLS

### 3.1 Raw Syscall (No libc)

**hello_raw.c**
```c
// Compile: gcc -nostdlib -static -o hello_raw hello_raw.c
// Run: ./hello_raw

#define SYS_write 1
#define SYS_exit  60

void _start(void) {
    const char msg[] = "Hello from raw syscall!\n";
    long ret;
    
    // Inline assembly for syscall
    __asm__ volatile (
        "syscall"
        : "=a" (ret)                    // Output: rax
        : "a" (SYS_write),              // rax = 1
          "D" (1),                      // rdi = stdout
          "S" (msg),                    // rsi = buffer
          "d" (sizeof(msg) - 1)         // rdx = count
        : "rcx", "r11", "memory"        // Clobbered
    );
    
    __asm__ volatile (
        "syscall"
        : 
        : "a" (SYS_exit), "D" (0)
        : "rcx", "r11", "memory"
    );
}
```

**Build & verify:**
```bash
gcc -nostdlib -static -o hello_raw hello_raw.c
file hello_raw
# statically linked, not stripped

strace ./hello_raw
# write(1, "Hello from raw syscall!\n", 24) = 24
# exit(0)                                 = ?

objdump -d hello_raw | grep -A 20 _start
```

### 3.2 Using syscall() Wrapper

**syscall_wrapper.c**
```c
#define _GNU_SOURCE
#include <unistd.h>
#include <sys/syscall.h>
#include <stdio.h>
#include <errno.h>

int main(void) {
    // Direct syscall invocation
    long ret = syscall(SYS_write, 1, "Direct syscall\n", 15);
    if (ret < 0) {
        errno = -ret;
        perror("syscall");
        return 1;
    }
    
    // Get PID via syscall
    pid_t pid = syscall(SYS_getpid);
    printf("PID: %d\n", pid);
    
    return 0;
}
```

**Compile & test:**
```bash
gcc -o syscall_wrapper syscall_wrapper.c
strace -c ./syscall_wrapper  # Count syscalls
ltrace ./syscall_wrapper     # Library calls
```

### 3.3 Pure Assembly Syscall

**hello.S**
```asm
.intel_syntax noprefix
.global _start

.section .rodata
msg:
    .ascii "Hello from pure asm!\n"
    msg_len = . - msg

.section .text
_start:
    # write(1, msg, msg_len)
    mov rax, 1              # SYS_write
    mov rdi, 1              # stdout
    lea rsi, [rip + msg]    # RIP-relative addressing
    mov rdx, msg_len
    syscall
    
    # exit(0)
    mov rax, 60             # SYS_exit
    xor rdi, rdi            # status = 0
    syscall
```

**Build:**
```bash
as --64 -o hello.o hello.S
ld -o hello hello.o
./hello
```

---

## 4. TRACING & DEBUGGING SYSCALLS

### 4.1 strace - System Call Tracer

```bash
# Basic tracing
strace ls

# Trace specific syscalls
strace -e open,openat,read cat /etc/passwd

# Trace with timing
strace -T -ttt ls  # Absolute timestamps + duration

# Trace network syscalls
strace -e trace=network curl https://example.com

# Trace syscall failures only
strace -Z cat /nonexistent 2>&1 | grep ENOENT

# Attach to running process
strace -p $(pidof nginx)

# Count syscalls by time
strace -c make -j8

# Full syscall detail
strace -v -s 4096 -o trace.log ./myapp
```

### 4.2 perf - Performance Analysis

```bash
# Count syscalls
perf stat -e 'syscalls:sys_enter_*' ./workload

# Trace specific syscall
perf trace -e openat ls

# Record syscalls with stack traces
perf record -e 'syscalls:sys_enter_write' -g -- ./app
perf report

# Syscall latency
perf trace record -- ./app
perf trace report
```

### 4.3 BPF/bpftrace - Modern Tracing

**syscall_count.bt**
```c
// Count syscalls per process
tracepoint:raw_syscalls:sys_enter {
    @[comm, args->id] = count();
}

END {
    print(@);
    clear(@);
}
```

**Run:**
```bash
sudo bpftrace syscall_count.bt

# One-liner: syscall latency histogram
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @start[tid] = nsecs; } \
    tracepoint:raw_syscalls:sys_exit /@start[tid]/ { \
    @latency = hist(nsecs - @start[tid]); delete(@start[tid]); }'
```

### 4.4 seccomp-tools

```bash
# Dump seccomp profile
seccomp-tools dump ./program

# Disassemble BPF filter
seccomp-tools disasm -f filter.bpf
```

---

## 5. SECURITY BOUNDARIES & THREAT MODEL

### 5.1 Attack Surface Analysis

**Syscall Table as Attack Vector:**
```
┌──────────────────────────────────────────────────────┐
│              ATTACK SURFACE                          │
├──────────────────────────────────────────────────────┤
│ 1. Syscall Number Validation                         │
│    - OOB reads if number unchecked                   │
│    - ret2syscall ROP gadgets                         │
│                                                       │
│ 2. Argument Validation                               │
│    - User pointer dereference (TOCTOU)               │
│    - Integer overflows in size parameters            │
│    - Uninitialized kernel stack leaks                │
│                                                       │
│ 3. Capability Checks                                 │
│    - CAP_SYS_ADMIN bypass                            │
│    - Namespace escape                                │
│                                                       │
│ 4. Race Conditions                                   │
│    - TOCTOU in copy_from_user()                      │
│    - Concurrent mmap/munmap races                    │
│                                                       │
│ 5. Side Channels                                     │
│    - Spectre/Meltdown via syscall timing             │
│    - Cache-based covert channels                     │
└──────────────────────────────────────────────────────┘
```

### 5.2 Mitigations

**Kernel Protections:**
```bash
# KASLR (Kernel ASLR)
cat /proc/cmdline | grep kaslr
# Should NOT see nokaslr

# SMEP/SMAP (Supervisor Mode Execution/Access Prevention)
grep -E 'smep|smap' /proc/cpuinfo

# KPTI (Kernel Page Table Isolation - Meltdown mitigation)
cat /sys/devices/system/cpu/vulnerabilities/meltdown

# Spectre/Retpoline
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
```

**Userspace Hardening:**

**seccomp-bpf (Syscall Filtering)**
```c
// seccomp_filter.c - Minimal seccomp example
#include <stdio.h>
#include <seccomp.h>
#include <unistd.h>

int main(void) {
    scmp_filter_ctx ctx;
    
    // Default deny
    ctx = seccomp_init(SCMP_ACT_KILL);
    if (!ctx) return 1;
    
    // Allowlist specific syscalls
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
    
    // Conditional rule: only allow write to stdout/stderr
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                    SCMP_A0(SCMP_CMP_LE, 2));
    
    // Load filter
    if (seccomp_load(ctx) < 0) {
        perror("seccomp_load");
        return 1;
    }
    
    printf("Seccomp loaded\n");  // OK
    
    // This will be killed
    getpid();  // Not in allowlist -> SIGSYS
    
    return 0;
}
```

**Build:**
```bash
gcc -o seccomp_filter seccomp_filter.c -lseccomp
./seccomp_filter
# Seccomp loaded
# Bad system call (core dumped)
```

**Raw BPF Filter:**
```c
// raw_seccomp.c - Direct BPF programming
#include <stdio.h>
#include <stddef.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/syscall.h>
#include <unistd.h>

#define ALLOW_SYSCALL(name) \
    BPF_JUMP(BPF_JMP+BPF_JEQ+BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_ALLOW)

int main(void) {
    struct sock_filter filter[] = {
        // Load architecture
        BPF_STMT(BPF_LD+BPF_W+BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP+BPF_JEQ+BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_KILL),
        
        // Load syscall number
        BPF_STMT(BPF_LD+BPF_W+BPF_ABS, offsetof(struct seccomp_data, nr)),
        
        // Allowlist
        ALLOW_SYSCALL(read),
        ALLOW_SYSCALL(write),
        ALLOW_SYSCALL(exit),
        ALLOW_SYSCALL(exit_group),
        
        // Default deny
        BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_KILL),
    };
    
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
    
    write(1, "Locked down\n", 12);
    getpid();  // Killed
    
    return 0;
}
```

**Build & test:**
```bash
gcc -o raw_seccomp raw_seccomp.c
./raw_seccomp
strace ./raw_seccomp 2>&1 | grep -A2 seccomp
```

---

## 6. PERFORMANCE CHARACTERISTICS

### 6.1 Syscall Cost Breakdown

```
┌────────────────────────────────────────┐
│   Typical Syscall Overhead (x86-64)    │
├────────────────────────────────────────┤
│ User→Kernel transition:    ~50-70 ns   │
│ Context switch (full):    ~1-5 µs      │
│ Argument copy:            ~10-100 ns   │
│ Capability checks:        ~50-200 ns   │
│ Actual work:              VARIABLE     │
│ Return path:              ~30-50 ns    │
├────────────────────────────────────────┤
│ TOTAL (minimal syscall):  ~150-500 ns  │
│ Cached vDSO call:         ~5-20 ns     │
└────────────────────────────────────────┘
```

### 6.2 Benchmark

**syscall_bench.c**
```c
#define _GNU_SOURCE
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

#define ITERATIONS 10000000

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    uint64_t start, end;
    
    // Benchmark getpid() syscall
    start = rdtsc();
    for (int i = 0; i < ITERATIONS; i++) {
        syscall(SYS_getpid);
    }
    end = rdtsc();
    printf("getpid() syscall: %lu cycles/call\n", 
           (end - start) / ITERATIONS);
    
    // Benchmark vDSO call
    struct timespec ts;
    start = rdtsc();
    for (int i = 0; i < ITERATIONS; i++) {
        clock_gettime(CLOCK_MONOTONIC, &ts);
    }
    end = rdtsc();
    printf("clock_gettime() (vDSO): %lu cycles/call\n", 
           (end - start) / ITERATIONS);
    
    // Function call baseline
    volatile int x = 0;
    start = rdtsc();
    for (int i = 0; i < ITERATIONS; i++) {
        x++;
    }
    end = rdtsc();
    printf("Baseline increment: %lu cycles/op\n", 
           (end - start) / ITERATIONS);
    
    return 0;
}
```

**Run:**
```bash
gcc -O2 -o syscall_bench syscall_bench.c
./syscall_bench
# Typical output:
# getpid() syscall: 85 cycles/call
# clock_gettime() (vDSO): 25 cycles/call
# Baseline increment: 1 cycles/op

# Verify with perf
perf stat -e cycles,instructions ./syscall_bench
```

---

## 7. ADVANCED TOPICS

### 7.1 Syscall Interposition

**LD_PRELOAD hooking:**
```c
// hook_write.c - Intercept write() calls
#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>

ssize_t write(int fd, const void *buf, size_t count) {
    // Get original write()
    static ssize_t (*real_write)(int, const void *, size_t) = NULL;
    if (!real_write) {
        real_write = dlsym(RTLD_NEXT, "write");
    }
    
    // Log to stderr
    const char prefix[] = "[HOOKED] ";
    real_write(2, prefix, sizeof(prefix) - 1);
    
    // Call original
    return real_write(fd, buf, count);
}
```

**Use:**
```bash
gcc -shared -fPIC -o hook_write.so hook_write.c -ldl
LD_PRELOAD=./hook_write.so ls
```

### 7.2 ptrace-based Syscall Injection

**inject_syscall.c**
```c
// Inject syscall into running process
#include <sys/ptrace.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <pid>\n", argv[0]);
        return 1;
    }
    
    pid_t target = atoi(argv[1]);
    struct user_regs_struct regs, orig_regs;
    
    // Attach to target
    if (ptrace(PTRACE_ATTACH, target, NULL, NULL) < 0) {
        perror("PTRACE_ATTACH");
        return 1;
    }
    waitpid(target, NULL, 0);
    
    // Save original registers
    ptrace(PTRACE_GETREGS, target, NULL, &orig_regs);
    regs = orig_regs;
    
    // Inject write(2, "INJECTED\n", 9)
    regs.rax = 1;    // SYS_write
    regs.rdi = 2;    // stderr
    regs.rsi = 0;    // Will cause EFAULT, just demo
    regs.rdx = 9;
    ptrace(PTRACE_SETREGS, target, NULL, &regs);
    
    // Execute single syscall
    ptrace(PTRACE_SINGLESTEP, target, NULL, NULL);
    waitpid(target, NULL, 0);
    
    // Restore original state
    ptrace(PTRACE_SETREGS, target, NULL, &orig_regs);
    ptrace(PTRACE_DETACH, target, NULL, NULL);
    
    return 0;
}
```

### 7.3 Kernel Module - Custom Syscall

**NOTE:** Modifying syscall table is generally discouraged. Use proper kernel APIs.

```c
// custom_syscall.c - Example only (DON'T DO IN PRODUCTION)
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/syscalls.h>

asmlinkage long sys_mycall(int arg) {
    printk(KERN_INFO "Custom syscall called: %d\n", arg);
    return arg * 2;
}

static int __init mod_init(void) {
    printk(KERN_INFO "Custom syscall loaded\n");
    return 0;
}

static void __exit mod_exit(void) {
    printk(KERN_INFO "Custom syscall unloaded\n");
}

module_init(mod_init);
module_exit(mod_exit);
MODULE_LICENSE("GPL");
```

---

## 8. SECURITY TESTING & FUZZING

### 8.1 Syscall Fuzzer

**syzkaller** - Kernel fuzzer from Google
```bash
# Clone and build
git clone https://github.com/google/syzkaller
cd syzkaller
make

# Create config
cat > my.cfg <<EOF
{
    "target": "linux/amd64",
    "http": "127.0.0.1:56741",
    "workdir": "/tmp/syzkaller",
    "kernel_obj": "/path/to/kernel",
    "image": "/path/to/image.img",
    "sshkey": "/path/to/ssh/key",
    "syzkaller": "$PWD",
    "procs": 8,
    "type": "qemu",
    "vm": {
        "count": 4,
        "kernel": "/path/to/bzImage",
        "cpu": 2,
        "mem": 2048
    }
}
EOF

# Run fuzzer
./bin/syz-manager -config=my.cfg
```

### 8.2 Trinity - Syscall Fuzzer

```bash
git clone https://github.com/kernelslacker/trinity
cd trinity
./configure && make

# Fuzz specific syscalls
./trinity -c openat -c close -c read -c write

# Run with seccomp
./trinity --enable-seccomp

# Children processes
./trinity -C 8 -N 100000
```

### 8.3 Custom Fuzzer

**fuzz_syscalls.c**
```c
// Simple random syscall fuzzer (DANGEROUS - use in VM)
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <time.h>

#define MAX_SYSCALL 440  // Adjust for your kernel

int main(void) {
    srand(time(NULL));
    
    for (int i = 0; i < 10000; i++) {
        long nr = rand() % MAX_SYSCALL;
        long arg1 = rand();
        long arg2 = rand();
        long arg3 = rand();
        
        // Random syscall with random args
        syscall(nr, arg1, arg2, arg3);
        
        if (i % 100 == 0) {
            printf("Iteration %d\n", i);
        }
    }
    
    return 0;
}
```

---

## 9. CONTAINER & NAMESPACE ISOLATION

### 9.1 Syscalls in Containers

**docker_syscall_audit.sh**
```bash
#!/bin/bash
# Audit syscalls from container

CONTAINER_ID=$(docker run -d alpine sleep 3600)

# Trace container syscalls
strace -f -p $(docker inspect -f '{{.State.Pid}}' $CONTAINER_ID) \
    -o container_trace.log &

# Execute in container
docker exec $CONTAINER_ID sh -c 'ls && cat /etc/hosts'

# Stop tracing
killall strace

# Analyze
grep '^[0-9]' container_trace.log | \
    awk '{print $2}' | sort | uniq -c | sort -rn | head -20

docker rm -f $CONTAINER_ID
```

### 9.2 Seccomp Profiles for Containers

**docker_seccomp.json**
```json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64"],
    "syscalls": [
        {
            "names": [
                "read", "write", "open", "close", "stat",
                "fstat", "lstat", "poll", "lseek", "mmap",
                "mprotect", "munmap", "brk", "rt_sigaction",
                "rt_sigprocmask", "ioctl", "access", "pipe",
                "select", "sched_yield", "mremap", "dup",
                "dup2", "nanosleep", "getpid", "socket",
                "connect", "accept", "sendto", "recvfrom",
                "bind", "listen", "getsockname", "getpeername",
                "socketpair", "setsockopt", "getsockopt",
                "clone", "fork", "vfork", "execve", "exit",
                "wait4", "kill", "uname", "fcntl", "flock",
                "fsync", "fdatasync", "truncate", "ftruncate",
                "getcwd", "chdir", "fchdir", "rename",
                "mkdir", "rmdir", "link", "unlink", "readlink",
                "chmod", "fchmod", "chown", "fchown",
                "lchown", "umask", "gettimeofday", "getrlimit",
                "getrusage", "sysinfo", "times", "getuid",
                "getgid", "setuid", "setgid", "geteuid",
                "getegid", "setpgid", "getppid", "setsid",
                "getpgrp", "setgroups", "getgroups", "setreuid",
                "setregid", "sigaltstack", "mknod", "statfs",
                "fstatfs", "getpriority", "setpriority",
                "prctl", "arch_prctl", "setrlimit", "sync",
                "acct", "settimeofday", "mount", "umount2",
                "swapon", "swapoff", "reboot", "sethostname",
                "setdomainname", "iopl", "ioperm", "init_module",
                "delete_module", "quotactl", "readv", "writev",
                "pread64", "pwrite64", "sysctl", "madvise",
                "mincore", "gettid", "readahead", "setxattr",
                "lsetxattr", "fsetxattr", "getxattr",
                "lgetxattr", "fgetxattr", "listxattr",
                "llistxattr", "flistxattr", "removexattr",
                "lremovexattr", "fremovexattr", "tkill",
                "futex", "sched_setaffinity", "sched_getaffinity",
                "set_tid_address", "fadvise64", "timer_create",
                "timer_settime", "timer_gettime", "timer_getoverrun",
                "timer_delete", "clock_settime", "clock_gettime",
                "clock_getres", "clock_nanosleep", "exit_group",
                "epoll_wait", "epoll_ctl", "tgkill", "utimes",
                "mbind", "set_mempolicy", "get_mempolicy",
                "mq_open", "mq_unlink", "mq_timedsend",
                "mq_timedreceive", "mq_notify", "mq_getsetattr",
                "openat", "mkdirat", "mknodat", "fchownat",
                "newfstatat", "unlinkat", "renameat", "linkat",
                "symlinkat", "readlinkat", "fchmodat", "faccessat",
                "pselect6", "ppoll", "unshare", "set_robust_list",
                "get_robust_list", "splice", "tee", "sync_file_range",
                "vmsplice", "utimensat", "epoll_pwait",
                "fallocate", "timerfd_create", "eventfd",
                "timerfd_settime", "timerfd_gettime", "accept4",
                "signalfd4", "eventfd2", "epoll_create1",
                "dup3", "pipe2", "inotify_init1", "preadv",
                "pwritev", "recvmmsg", "prlimit64",
                "sendmmsg", "getcpu", "sched_setattr",
                "sched_getattr", "renameat2", "getrandom",
                "memfd_create", "execveat", "socket",
                "socketpair", "bind", "connect", "listen",
                "accept4", "getsockopt", "setsockopt",
                "getsockname", "getpeername", "sendto",
                "sendmsg", "recvfrom", "recvmsg", "shutdown"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
```

**Use:**
```bash
docker run --security-opt seccomp=docker_seccomp.json alpine sh
```

---

## 10. DEBUGGING KERNEL ISSUES

### 10.1 Kernel Debugging Setup

```bash
# Build kernel with debug symbols
cd linux-source
make menuconfig
# Enable: Kernel hacking → Compile-time checks → Debug info

# KGDB over serial
# Add to kernel cmdline: kgdboc=ttyS0,115200 kgdbwait

# Crash dumps
apt-get install kdump-tools
systemctl enable kdump-tools

# After crash
crash /usr/lib/debug/boot/vmlinux-$(uname -r) /var/crash/*
```

### 10.2 SystemTap - Dynamic Tracing

**trace_syscalls.stp**
```c
// Trace all syscalls with arguments
probe syscall.* {
    printf("%s: %s(%s)\n", execname(), name, argstr)
}

probe timer.s(10) {
    exit()
}
```

**Run:**
```bash
sudo stap trace_syscalls.stp

# Specific syscall with stack
sudo stap -e 'probe syscall.open { 
    printf("%s -> %s\n", execname(), filename); 
    print_backtrace(); 
}'
```

---

## 11. THREAT MITIGATION CHECKLIST

```
┌─────────────────────────────────────────────────────┐
│         PRODUCTION SYSCALL HARDENING                │
├─────────────────────────────────────────────────────┤
│ □ Enable KASLR (kernel randomization)              │
│ □ Enable SMEP/SMAP (prevent kernel exec userspace) │
│ □ Enable KPTI (Meltdown mitigation)                │
│ □ Deploy seccomp-bpf profiles (container & apps)   │
│ □ Use landlock LSM for fine-grained restrictions   │
│ □ Audit with SELinux/AppArmor                      │
│ □ Monitor syscall anomalies (falco, osquery)       │
│ □ Restrict CAP_SYS_ADMIN (least privilege)         │
│ □ Use user namespaces (avoid root in containers)   │
│ □ Enable kernel lockdown mode                      │
│ □ Regular kernel updates (CVE patching)            │
│ □ Syscall interposition monitoring (audit logs)    │
│ □ Stack canaries + NX bit (userspace)              │
│ □ Fuzzing in CI/CD (syzkaller/trinity)            │
└─────────────────────────────────────────────────────┘
```

---

## 12. ROLL-OUT PLAN FOR SYSCALL HARDENING

### Phase 1: Audit (Week 1-2)
```bash
# Step 1: Baseline syscall inventory
sudo strace -c -f -p $(pgrep -f 'your-app') > baseline.txt

# Step 2: Generate seccomp profile
docker run --rm -it --security-opt seccomp=unconfined your-image
# Run workload, then:
seccomp-tools dump ./your-app > profile.json

# Step 3: Test profile in audit mode
# Modify profile.json: "defaultAction": "SCMP_ACT_LOG"
docker run --security-opt seccomp=profile.json your-image
dmesg | grep SECCOMP
```

### Phase 2: Staging (Week 3-4)
```bash
# Deploy with permissive profile
kubectl apply -f pod-seccomp-audit.yaml
# Monitor violations
kubectl logs -f pod | grep 'Operation not permitted'

# Iterate profile
seccomp-tools merge profile1.json profile2.json > merged.json
```

### Phase 3: Production (Week 5+)
```bash
# Enable enforcement
# "defaultAction": "SCMP_ACT_ERRNO"
kubectl apply -f pod-seccomp-enforce.yaml

# Monitor dashboards
# - Syscall latency (p99)
# - SECCOMP violation rate
# - Container restart frequency
```

### Rollback Plan
```bash
# Immediate: Disable seccomp
kubectl patch pod my-pod -p '{"spec":{"securityContext":{"seccompProfile":null}}}'

# Remove profile from all pods
kubectl get pods -o json | jq '.items[].spec.securityContext.seccompProfile = null' | kubectl apply -f -
```

---

## 13. REFERENCES & FURTHER READING

**Essential Reading:**
- **Linux Kernel Documentation**: https://www.kernel.org/doc/html/latest/
  - `Documentation/userspace-api/index.rst`
  - `Documentation/admin-guide/kernel-parameters.txt`
- **The Linux Programming Interface** (Michael Kerrisk) - Chapters 3, 6, 35
- **Linux System Programming** (Robert Love)
- **Understanding the Linux Kernel** (Bovet & Cesati) - Chapter 10

**Source Code:**
- Linux syscall entry: `arch/x86/entry/entry_64.S`
- Syscall table: `arch/x86/entry/syscalls/syscall_64.tbl`
- Seccomp: `kernel/seccomp.c`
- BPF: `kernel/bpf/`

**Tools & Repos:**
- strace: https://github.com/strace/strace
- seccomp: https://github.com/seccomp/libseccomp
- syzkaller: https://github.com/google/syzkaller
- trinity: https://github.com/kernelslacker/trinity
- bpftrace: https://github.com/iovisor/bpftrace

**Security:**
- CVE Database: https://cve.mitre.org (search "syscall")
- Linux Kernel Security: https://kernsec.org
- Seccomp profiles: https://github.com/moby/moby/tree/master/profiles/seccomp

**Papers:**
- "Spectre Attacks" (Kocher et al.)
- "Meltdown" (Lipp et al.)
- "Flexible OS Support and Applications with landlock LSM"

---

## NEXT 3 STEPS

1. **Build syscall tracer in Go/Rust**
   ```bash
   # Rust: Use nix crate for raw syscalls
   cargo new syscall-tracer
   # Add: nix = "0.27", libc = "0.2"
   
   # Go: Use x/sys/unix
   go mod init syscall-demo
   go get golang.org/x/sys/unix
   ```

2. **Implement eBPF syscall monitor**
   ```bash
   # Install libbpf-dev, clang, llvm
   git clone https://github.com/libbpf/libbpf-bootstrap
   cd libbpf-bootstrap/examples/c
   # Modify syscall example
   ```

3. **Deploy seccomp in Kubernetes**
   ```bash
   # Create PSP/PSS with seccomp
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: Pod
   metadata:
     name: secure-pod
   spec:
     securityContext:
       seccompProfile:
         type: Localhost
         localhostProfile: profiles/audit.json
     containers:
     - name: app
       image: your-image
   EOF
   ```

**Questions to verify understanding:**
1. What happens when a syscall number exceeds `__NR_syscall_max`?
2. Why does `rcx` NOT hold arg4 in x86-64 syscalls?
3. How does vDSO avoid kernel transitions?