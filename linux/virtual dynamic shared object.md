# Virtual Dynamic Shared Object (vDSO)
### A Complete, In-Depth Technical Reference
#### Linux Kernel Internals · C & Rust Implementations · Architecture Deep-Dive

---

## Table of Contents

1. [Introduction & Motivation](#1-introduction--motivation)
2. [The System Call Problem — Why vDSO Exists](#2-the-system-call-problem--why-vdso-exists)
3. [vDSO Architecture & Kernel Implementation](#3-vdso-architecture--kernel-implementation)
4. [ELF Structure of the vDSO](#4-elf-structure-of-the-vdso)
5. [Memory Mapping & ASLR](#5-memory-mapping--aslr)
6. [vDSO Symbols & Exported Functions](#6-vdso-symbols--exported-functions)
7. [The vsyscall Mechanism (Legacy)](#7-the-vsyscall-mechanism-legacy)
8. [Auxiliary Vector (AT_SYSINFO_EHDR)](#8-auxiliary-vector-at_sysinfo_ehdr)
9. [vvar — The Shared Data Page](#9-vvar--the-shared-data-page)
10. [Clock & Timekeeping Internals](#10-clock--timekeeping-internals)
11. [C Implementation — Deep Dive](#11-c-implementation--deep-dive)
12. [Rust Implementation — Deep Dive](#12-rust-implementation--deep-dive)
13. [Architecture-Specific Differences](#13-architecture-specific-differences)
14. [Security: ASLR, Spectre, and vDSO](#14-security-aslr-spectre-and-vdso)
15. [Debugging & Inspection Tools](#15-debugging--inspection-tools)
16. [Performance Benchmarks & Analysis](#16-performance-benchmarks--analysis)
17. [Advanced: Writing a Custom vDSO Consumer](#17-advanced-writing-a-custom-vdso-consumer)
18. [vDSO in Containers & Sandboxes](#18-vdso-in-containers--sandboxes)
19. [Common Pitfalls & Edge Cases](#19-common-pitfalls--edge-cases)
20. [Summary & Reference Table](#20-summary--reference-table)

---

## 1. Introduction & Motivation

The **virtual Dynamic Shared Object** (vDSO) is a small shared library that the Linux kernel automatically maps into the address space of every user-space process. It is "virtual" because it does not exist as a file on disk — it lives entirely in kernel memory and is exported to user space as a read-only, executable ELF shared library at process start time.

Its primary purpose is to accelerate a specific class of system calls — those that are **frequent, read-only, and whose data can be safely exposed to user space** — by allowing them to execute entirely in user space, eliminating the overhead of the kernel boundary crossing (the `syscall` / `sysenter` trap instruction and the associated privilege-level switch).

### What Makes vDSO Necessary?

Modern applications call `clock_gettime()` millions of times per second. Profiling, logging frameworks, distributed tracing, metrics, animations, game engines, networking stacks — all of them need high-resolution timestamps. If every call crossed the kernel boundary, the overhead would be prohibitive.

The vDSO solves this in an elegant way: the kernel maps a page of memory into user space that contains:

- **Executable code** — the implementation of the "fast path" for certain syscalls.
- **Shared data** (via `vvar`) — kernel-managed variables that the vDSO code reads directly, such as the current time, monotonic clock offset, and coarse time values.

Because this data is mapped read-only into user space, user-space code can read it without any privilege switch, and because it's updated by the kernel whenever a timer interrupt fires, it remains consistent and accurate.

---

## 2. The System Call Problem — Why vDSO Exists

### The Cost of a Traditional System Call

To understand vDSO, you must first internalize the full cost of a system call on x86-64 Linux:

```
User Space                    Kernel Space
-----------                   ------------
  SYSCALL instruction
  → saves registers (rip, rflags, rsp, rcx, r11)
  → switches privilege level (ring 3 → ring 0)
  → switches page tables (CR3 register write) [PTI]
  → flushes TLB (Meltdown mitigation: KPTI)
  → jumps to system call entry point
  → dispatches through syscall table
  → executes syscall handler
  → returns via SYSRET
  → restores registers
  → switches back to user page tables
  → TLB flush (again, with KPTI)
User Space resumes
```

Each of these steps has a measurable cost:

| Step | Approximate Cost |
|------|-----------------|
| `SYSCALL` / `SYSRET` instructions | ~20-30 cycles (no KPTI) |
| KPTI page table switch (CR3 write) | ~100-200 cycles (TLB flush) |
| Kernel entry/exit overhead | ~50-100 cycles |
| Cache warming (new code/data paths) | variable, often 100-500 cycles |
| **Total round trip (with KPTI)** | **~1,000-4,000 cycles** |

On a 3 GHz CPU, 4,000 cycles = ~1.3 microseconds per syscall. If your application calls `clock_gettime()` 1 million times per second, that's **1.3 seconds per second** — more CPU time than is available.

### The vDSO Solution

The vDSO eliminates all of this:

```
User Space
-----------
  call [vdso_clock_gettime]
  → reads vvar page (shared kernel data, no privilege switch)
  → performs arithmetic (timestamp reconstruction)
  → returns to caller
Total: ~20-40 cycles
```

This is a **50-100x speedup** versus a traditional syscall with KPTI.

### Which Syscalls Can Be Accelerated?

Not all syscalls can be moved to user space. vDSO only applies to syscalls that are:

1. **Idempotent / read-only**: They don't modify kernel state.
2. **Based on kernel-exported data**: Their answer can be derived from data the kernel can safely share.
3. **Latency-sensitive**: The overhead of a full syscall is significant relative to the work performed.

The canonical examples are:
- `clock_gettime()` — reads time from kernel clock data
- `gettimeofday()` — reads wall clock time
- `clock_getres()` — returns clock resolution (static/infrequently changing)
- `time()` — returns coarse seconds since epoch
- `getcpu()` — returns current CPU and NUMA node (on some architectures)

---

## 3. vDSO Architecture & Kernel Implementation

### Kernel Build-Time Construction

The vDSO is compiled as part of the kernel build process. In the kernel source tree, its location is architecture-specific:

```
arch/x86/entry/vdso/          # x86-64 vDSO sources
arch/arm64/kernel/vdso/       # ARM64 vDSO sources
arch/riscv/kernel/vdso/       # RISC-V vDSO sources
```

For x86-64, the key files are:

```
arch/x86/entry/vdso/
├── vdso.lds.S          # Linker script — defines ELF layout, symbols
├── vclock_gettime.c    # clock_gettime / gettimeofday implementations
├── vgetcpu.c           # getcpu implementation
├── vdso32/             # 32-bit compat vDSO
│   ├── vclock_gettime.c
│   └── vdso32.lds.S
└── Makefile
```

The Makefile compiles these with a restricted set of compiler flags:

```makefile
# From arch/x86/entry/vdso/Makefile (simplified)
VDSO_LDFLAGS := -shared -soname linux-vdso.so.1 \
                -z max-page-size=4096 \
                --hash-style=both \
                --build-id \
                -Bsymbolic

# No standard library linkage
CFLAGS_vdso := -fPIC -fno-stack-protector -fno-omit-frame-pointer \
               -fno-asynchronous-unwind-tables -fno-common \
               -O2 -nostdlib
```

Crucially:
- **`-fPIC`**: Position-Independent Code, mandatory for shared libraries loaded at arbitrary addresses.
- **`-nostdlib`**: No libc — the vDSO cannot call into glibc, it must be entirely self-contained.
- **`-fno-stack-protector`**: Stack canaries require `__stack_chk_guard` from libc — not available.
- **`-fno-asynchronous-unwind-tables`**: Keeps the ELF binary small — no `.eh_frame` bloat.

### The Resulting Binary

The build produces a special ELF `.so` that is embedded directly into the kernel binary as raw bytes:

```c
// arch/x86/entry/vdso/vdso-image-64.c (generated at build time)
// This file is auto-generated; the actual vDSO ELF bytes are embedded here
const struct vdso_image vdso_image_64 = {
    .data = raw_data,       // The actual ELF bytes
    .size = 8192,           // Must be page-aligned
    .text_mapping = { ... },
    .alt_mapping = { ... },
};
```

### Runtime Mapping — `arch_setup_additional_pages()`

When the kernel creates a new process (`exec()`), it calls `arch_setup_additional_pages()` to map the vDSO:

```c
// arch/x86/entry/vdso/vma.c (simplified)
int arch_setup_additional_pages(struct linux_binprm *bprm, int uses_interp)
{
    struct mm_struct *mm = current->mm;
    unsigned long addr;
    int ret;

    // Pick a random address (ASLR)
    addr = vdso_addr(current->mm->start_stack, vdso_image_64.size);

    // Map the vDSO text (executable, read-only) into user address space
    ret = map_vdso_randomized(&vdso_image_64);

    // Store the vDSO base address in mm_struct for later access
    mm->context.vdso = (void __user *)addr;

    return ret;
}
```

The `map_vdso_randomized()` function sets up two distinct mappings:

1. **`vvar` page(s)**: Mapped read-only, contains the clock data the vDSO code reads. Located at `vdso_base - PAGE_SIZE * n`.
2. **vDSO text**: The ELF shared library itself, mapped read-only + executable.

### vDSO Image Structure in the Kernel

```c
// include/linux/vdso/datapage.h / include/vdso/datapage.h
struct vdso_image {
    void *data;             // Pointer to ELF data in kernel .rodata
    unsigned long size;     // Size (multiple of PAGE_SIZE)

    // Offsets of special sections within the ELF
    long sym_vvar_start;    // Offset of vvar mapping relative to text
    long sym_pvclock_page;  // Paravirt clock page offset (for VMs)
    long sym_hvclock_page;  // Hyper-V clock page offset

    // ALT patching for runtime CPU feature detection
    const struct vdso_patch_def *alternatives;
    unsigned int num_alternatives;
};
```

### Process Memory Layout After exec()

```
High addresses
┌──────────────────────────────────────┐
│         [kernel space]               │
├──────────────────────────────────────┤  ← 0xFFFF800000000000
│         ...                          │
├──────────────────────────────────────┤
│         [stack]                      │
│         grows downward               │
├──────────────────────────────────────┤
│         vDSO text (.so)              │  ← AT_SYSINFO_EHDR
│         (read-only, executable)      │
├──────────────────────────────────────┤
│         vvar page(s)                 │
│         (read-only data)             │
├──────────────────────────────────────┤
│         [heap]                       │
│         grows upward                 │
├──────────────────────────────────────┤
│         [bss / data / text]          │
└──────────────────────────────────────┘
Low addresses
```

---

## 4. ELF Structure of the vDSO

The vDSO is a proper ELF shared library. You can dump and inspect it from any running process:

```bash
# Extract the vDSO from a running process (PID 1 = init/systemd)
cat /proc/self/maps | grep vdso
# Output example:
# 7fff12345000-7fff12347000 r-xp 00000000 00:00 0   [vdso]

# Dump it to disk
dd if=/proc/self/mem of=/tmp/vdso.so \
   bs=1 skip=$((0x7fff12345000)) \
   count=$((0x2000)) 2>/dev/null

# Or use the simpler approach:
cat /proc/self/mem | \
  python3 -c "
import sys, mmap
with open('/proc/self/maps') as f:
    for line in f:
        if '[vdso]' in line:
            start, end = [int(x, 16) for x in line.split()[0].split('-')]
            with open('/proc/self/mem', 'rb') as m:
                m.seek(start)
                sys.stdout.buffer.write(m.read(end - start))
" > /tmp/vdso.so

# Inspect it
readelf -h /tmp/vdso.so     # ELF header
readelf -S /tmp/vdso.so     # Section headers
readelf -d /tmp/vdso.so     # Dynamic section
readelf -s /tmp/vdso.so     # Symbol table
objdump -d /tmp/vdso.so     # Disassembly
```

### ELF Header

```
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 ...
  Class:                             ELF64
  Data:                              2's complement, little endian
  Type:                              DYN (Shared object file)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x0
  Start of program headers:          64 (bytes into file)
  Start of section headers:          ...
```

### Key Sections

| Section | Purpose |
|---------|---------|
| `.text` | Executable code for vDSO functions |
| `.rodata` | Read-only data (lookup tables, etc.) |
| `.dynsym` | Dynamic symbol table (exported symbols) |
| `.dynstr` | String table for dynamic symbols |
| `.gnu.version` | Symbol versioning |
| `.gnu.version_d` | Version definitions (e.g., `LINUX_2.6`) |
| `.dynamic` | ELF dynamic linking info |
| `.eh_frame` | DWARF unwind tables (for stack unwinding) |
| `.note.linux.build-id` | Build ID for debugging |

### Exported Symbol Versioning

The vDSO exports symbols with version strings, allowing glibc and other consumers to verify compatibility:

```bash
readelf -s /tmp/vdso.so | grep FUNC
# Output:
#      1: 0000000000000a40   430 FUNC    GLOBAL DEFAULT   13 clock_gettime@@LINUX_2.6
#      2: 0000000000000bf0   131 FUNC    GLOBAL DEFAULT   13 __vdso_clock_gettime@@LINUX_2.6
#      3: 0000000000000c80    60 FUNC    GLOBAL DEFAULT   13 gettimeofday@@LINUX_2.6
#      4: 0000000000000cc0    55 FUNC    GLOBAL DEFAULT   13 time@@LINUX_2.6
#      5: 0000000000000d00    71 FUNC    GLOBAL DEFAULT   13 clock_getres@@LINUX_2.6
#      6: 0000000000000d50    90 FUNC    GLOBAL DEFAULT   13 getcpu@@LINUX_2.6
```

Each function has two names: `clock_gettime` (unversioned alias) and `__vdso_clock_gettime` (the actual implementation). glibc binds to the versioned symbol.

---

## 5. Memory Mapping & ASLR

### Address Space Layout Randomization

The vDSO is subject to ASLR. Its base address is randomized at every process start. The kernel computes the address using entropy from the stack placement:

```c
// arch/x86/entry/vdso/vma.c (simplified)
static unsigned long vdso_addr(unsigned long start, unsigned len)
{
    unsigned long addr, end;
    unsigned offset;

    end = (start + stack_maxrandom_size(TASK_SIZE)) & ~(VDSO_ALIGN - 1);
    if (end >= TASK_SIZE)
        end = TASK_SIZE;
    end -= len;

    // Use the ASLR bits from the stack address
    offset = get_random_u32() % (((end - PAGE_SIZE) >> PAGE_SHIFT) + 1);
    addr = start + (offset << PAGE_SHIFT);

    if (addr > end)
        addr = end;
    return addr;
}
```

### Checking ASLR Randomization

```bash
# Run this multiple times — the vDSO address changes each time
for i in $(seq 5); do
    cat /proc/$(sh -c 'echo $BASHPID')/maps 2>/dev/null | grep vdso || \
    (sleep 0.01 && cat /proc/self/maps | grep vdso)
done

# Or use this one-liner to check entropy
for i in $(seq 10); do
    grep vdso /proc/self/maps | awk '{print $1}' | cut -d'-' -f1
done
```

### Disabling ASLR (for debugging)

```bash
# Disable ASLR system-wide (not recommended in production)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Disable only for a single process using personality(2)
setarch $(uname -m) -R ./your_binary

# In C:
#include <sys/personality.h>
personality(ADDR_NO_RANDOMIZE);
```

### VMA Flags for vDSO Mappings

The vDSO VMAs have specific flags visible in `/proc/PID/maps`:

```
7ffe...000-7ffe...000 r--p 00000000 00:00 0  [vvar]
7ffe...000-7ffe...000 r-xp 00000000 00:00 0  [vdso]
```

| Flag | Meaning |
|------|---------|
| `r--p` | Read-only, private (vvar) — no write, no execute |
| `r-xp` | Read + execute, private (vdso text) — no write |
| `00:00 0` | No backing device/inode — anonymous mapping |

The `p` (private) flag is important: even though all processes share the same physical pages (the kernel's copy), the mapping is tagged as private to prevent processes from seeing each other's modifications (though writes would cause a segfault anyway since the pages are read-only).

---

## 6. vDSO Symbols & Exported Functions

### x86-64 Linux vDSO Exports

```c
// The four main vDSO functions on x86-64:

// 1. High-resolution clock — the primary use case
int __vdso_clock_gettime(clockid_t clk_id, struct timespec *ts);

// 2. POSIX-legacy wall clock
int __vdso_gettimeofday(struct timeval *tv, struct timezone *tz);

// 3. Coarse seconds since epoch
time_t __vdso_time(time_t *tloc);

// 4. Clock resolution query
int __vdso_clock_getres(clockid_t clk_id, struct timespec *res);

// 5. CPU and NUMA node identification
long __vdso_getcpu(unsigned *cpu, unsigned *node, struct getcpu_cache *unused);
```

### Supported `clockid_t` Values in vDSO

Not all clock IDs are handled by the vDSO fast path. Those that fall through require a real syscall:

| `clockid_t` | vDSO Handled? | Description |
|-------------|--------------|-------------|
| `CLOCK_REALTIME` | ✅ Yes | Wall clock time |
| `CLOCK_MONOTONIC` | ✅ Yes | Monotonic time since boot |
| `CLOCK_REALTIME_COARSE` | ✅ Yes | Low-res wall clock (faster) |
| `CLOCK_MONOTONIC_COARSE` | ✅ Yes | Low-res monotonic (faster) |
| `CLOCK_BOOTTIME` | ✅ Yes (kernel 5.x+) | Like MONOTONIC + suspend time |
| `CLOCK_TAI` | ✅ Yes (recent) | International Atomic Time |
| `CLOCK_THREAD_CPUTIME_ID` | ❌ No | Per-thread CPU time |
| `CLOCK_PROCESS_CPUTIME_ID` | ❌ No | Per-process CPU time |

### ARM64 vDSO Exports

```c
// AArch64 has a slightly different set:
int __kernel_clock_gettime(clockid_t, struct __kernel_timespec *);
int __kernel_clock_getres(clockid_t, struct __kernel_timespec *);
int __kernel_gettimeofday(struct __kernel_old_timeval *, struct timezone *);
__kernel_long_t __kernel_time(__kernel_long_t *);
```

---

## 7. The vsyscall Mechanism (Legacy)

Before vDSO, Linux had `vsyscall` — a simpler, less flexible mechanism. Understanding it clarifies why vDSO is superior.

### How vsyscall Worked

`vsyscall` mapped a fixed page at address `0xFFFFFFFFFF600000` (a fixed virtual address, not randomized) in every 64-bit process. This page contained stub functions at fixed offsets:

```
0xFFFFFFFFFF600000: gettimeofday()
0xFFFFFFFFFF600400: time()
0xFFFFFFFFFF600800: getcpu()
```

User code could call these directly:

```c
// This was legal:
typedef int (*gettimeofday_t)(struct timeval *, struct timezone *);
gettimeofday_t fn = (gettimeofday_t)0xFFFFFFFFFF600000;
fn(&tv, &tz);
```

### vsyscall Problems

1. **Fixed address = no ASLR**: The page is always at the same address, making it a prime ROP (Return-Oriented Programming) gadget source for exploits.
2. **Only 3 functions**: Hard-coded offsets meant it was difficult to add new functions.
3. **Emulation overhead**: Modern kernels implement vsyscall as `trap-and-emulate` — calling into it triggers a page fault, which the kernel catches and emulates. This is actually *slower* than a real syscall.

### vsyscall Today — Emulation Modes

```bash
# Check vsyscall mode on your kernel
cat /boot/config-$(uname -r) | grep VSYSCALL

# CONFIG_LEGACY_VSYSCALL_EMULATE=y  → trap and emulate (slow, but works)
# CONFIG_LEGACY_VSYSCALL_XONLY=y    → execute-only (SIGSEGV on read)
# CONFIG_LEGACY_VSYSCALL_NONE=y     → disabled entirely
```

**vDSO replaced vsyscall entirely** for new code. glibc has used vDSO exclusively since glibc 2.14 (2011).

---

## 8. Auxiliary Vector (AT_SYSINFO_EHDR)

The critical question: *how does user space find the vDSO?*

The answer is the **auxiliary vector** (auxv) — a data structure the kernel places on the stack immediately after `envp[]` during `execve()`.

### Stack Layout at Process Start

```
High addresses
┌──────────────────────┐
│  [kernel provides]   │
│  argc                │  ← rsp (stack pointer at _start)
│  argv[0]             │
│  argv[1]             │
│  ...                 │
│  argv[n] = NULL      │
│  envp[0]             │
│  envp[1]             │
│  ...                 │
│  envp[m] = NULL      │
│  AT_NULL (0, 0)      │  ← end of auxv
│  AT_SYSINFO_EHDR     │  ← vDSO base address!
│  AT_PHDR             │  ← program header address
│  AT_ENTRY            │  ← entry point
│  AT_PAGESZ           │  ← page size
│  ...more auxv...     │
│  [strings for argv]  │
│  [strings for envp]  │
└──────────────────────┘
Low addresses
```

### Reading the Auxiliary Vector

```bash
# Print all aux vector entries for the current process
LD_SHOW_AUXV=1 /bin/true

# Output (relevant lines):
# AT_SYSINFO_EHDR: 0x7fff12345000  ← This IS the vDSO base address
# AT_PAGESZ:       4096
# AT_CLKTCK:       100
# AT_PHDR:         0x400040
# AT_ENTRY:        0x401000
```

### Programmatic Access to auxv

```c
#include <sys/auxv.h>

// getauxval() is the POSIX-ish interface
unsigned long vdso_base = getauxval(AT_SYSINFO_EHDR);
```

### Manual auxv Parsing (no libc)

In a raw `_start` implementation (no CRT, no glibc), you parse the auxv manually:

```c
// Assuming standard ELF startup: rsp → argc, argv[], envp[], auxv[]
static unsigned long get_at_sysinfo_ehdr(unsigned long *sp)
{
    int argc = (int)*sp;
    char **argv = (char **)(sp + 1);
    char **envp = argv + argc + 1;

    // Skip over envp[]
    char **env = envp;
    while (*env) env++;
    env++; // skip NULL terminator

    // Now at auxv
    typedef struct { unsigned long type, val; } Elf64_auxv_t;
    Elf64_auxv_t *auxv = (Elf64_auxv_t *)env;

    for (; auxv->type != AT_NULL; auxv++) {
        if (auxv->type == AT_SYSINFO_EHDR)
            return auxv->val;
    }
    return 0;
}
```

---

## 9. vvar — The Shared Data Page

The **vvar** page is the beating heart of vDSO. It is a page (or pages) of kernel memory mapped read-only into user space, containing the time data that vDSO functions read directly without any syscall.

### The `vdso_data` Structure

In the kernel source (`include/vdso/datapage.h`):

```c
// Simplified from kernel source — the actual struct is architecture-specific
// and has changed significantly across kernel versions.

struct vdso_timestamp {
    u64 sec;    // Seconds
    u64 nsec;   // Nanoseconds (scaled)
};

struct vdso_data {
    u32 seq;                        // Sequence counter (seqlock)
    s32 clock_mode;                 // Hardware clock mode (TSC, HPET, etc.)

    u64 cycle_last;                 // Last TSC value read by kernel
    u64 mask;                       // Mask for clocksource bits
    u32 mult;                       // Clocksource multiplier
    u32 shift;                      // Clocksource shift

    struct vdso_timestamp basetime[VDSO_BASES];  // One per clock ID

    s32 tz_minuteswest;             // Timezone offset
    s32 tz_dsttime;                 // DST flag

    u32 hrtimer_res;                // hrtimer resolution
    u32 __unused;

    struct arch_vdso_data arch_data; // Architecture-specific extensions
} ____cacheline_aligned;
```

### The seqlock Protocol

The most critical concept in vDSO data reading is the **seqlock** (sequence lock). Because the kernel writes to `vdso_data` while user space reads it, and because there's no mutex (that would require a syscall), vDSO uses an optimistic concurrency mechanism:

**Write side (kernel, on timer interrupt):**
```c
// kernel/time/vsyscall.c (simplified)
void update_vsyscall(struct timekeeper *tk)
{
    // Increment seq to ODD — signals write in progress
    vdso_write_begin(vdata);

    // Update all fields
    vdata->cycle_last = tk->tkr_mono.cycle_last;
    vdata->mult = tk->tkr_mono.mult;
    vdata->shift = tk->tkr_mono.shift;
    // ... update basetime[], etc.

    // Increment seq to EVEN — signals write complete
    vdso_write_end(vdata);
}
```

**Read side (vDSO user-space code):**
```c
// arch/x86/entry/vdso/vclock_gettime.c (simplified logic)
static __always_inline int do_clock_gettime(clockid_t clk, struct timespec64 *ts)
{
    const struct vdso_data *vd = __arch_get_k_vdso_data();
    u32 seq;

    do {
        // Read sequence counter
        seq = vdso_read_begin(vd);

        // If seq is ODD → kernel is writing → spin
        // If seq is EVEN → consistent state → proceed

        // Read clock data
        u64 cycles = __arch_get_hw_counter(vd->clock_mode);
        u64 ns = vdso_calc_ns(vd, cycles, vd->basetime[clk].nsec);
        ts->tv_sec = vd->basetime[clk].sec;
        ts->tv_nsec = ns;

    // Retry if seq changed (kernel wrote while we were reading)
    } while (unlikely(vdso_read_retry(vd, seq)));

    return 0;
}
```

The retry loop is the key: if the kernel modified `vdso_data` while we were reading (seq changed), we simply retry. In the common case (no concurrent kernel write), we read once and return.

### Viewing vvar Contents

```bash
# Check vvar mapping
cat /proc/self/maps | grep vvar
# 7fff12344000-7fff12345000 r--p 00000000 00:00 0  [vvar]

# vvar is read-only — any write attempt triggers SIGSEGV
# You can read it as raw bytes:
dd if=/proc/self/mem of=/tmp/vvar.bin \
   bs=4096 skip=$((0x7fff12344000 / 4096)) count=1 2>/dev/null

# Use gdb to inspect it at runtime:
# (gdb) info proc mappings
# (gdb) x/20gx 0x7fff12344000
```

---

## 10. Clock & Timekeeping Internals

### How `clock_gettime(CLOCK_MONOTONIC)` Works End-to-End

The vDSO implementation of `clock_gettime` for `CLOCK_MONOTONIC` performs the following steps entirely in user space:

```
1. Access vdso_data via the vvar mapping
2. Read seq (seqlock — must be even)
3. Read cycle_last (last TSC value kernel recorded)
4. Read mult, shift, basetime[CLOCK_MONOTONIC]
5. Issue RDTSC instruction to get current TSC value
6. Compute delta: delta_tsc = current_tsc - cycle_last
7. Convert to nanoseconds: delta_ns = (delta_tsc * mult) >> shift
8. Add to base: total_ns = basetime.nsec + delta_ns
9. Normalize: handle nsec overflow into seconds
10. Verify seq unchanged (retry if not)
11. Return {tv_sec, tv_nsec}
```

### TSC — The Time Stamp Counter

The TSC (Time Stamp Counter) is a 64-bit hardware counter on x86 CPUs that increments at approximately the CPU's nominal frequency. The `RDTSC` instruction reads it in ~20 cycles with no privilege requirement.

```asm
; RDTSC instruction
rdtsc           ; Writes TSC into EDX:EAX (high 32 bits : low 32 bits)
shl rdx, 32
or rax, rdx     ; rax = full 64-bit TSC value
```

### TSC Stability Issues

Not all TSCs are equal:

| TSC Type | Characteristic | vDSO Compatible? |
|----------|---------------|-----------------|
| **Invariant TSC** | Fixed frequency, unaffected by P-states/C-states | ✅ Yes |
| **Constant TSC** | Fixed frequency, but may drift across sockets | ✅ Usually |
| **Unstable TSC** | Frequency changes with CPU speed | ❌ No — falls back to syscall |

```bash
# Check TSC stability on your CPU
dmesg | grep -i tsc
# Look for: "tsc: Marking TSC unstable due to..." (bad)
# Or: "TSC: clocksource=tsc-early, mask=0xffffffffffffffff" (good)

# Also:
grep flags /proc/cpuinfo | head -1 | tr ' ' '\n' | grep -E "constant_tsc|nonstop_tsc|tsc_reliable"
```

### The clocksource Multiplier/Shift

Converting raw TSC cycles to nanoseconds requires knowing the TSC frequency. The kernel pre-computes `mult` and `shift` such that:

```
nanoseconds = (cycles * mult) >> shift
```

This avoids floating-point division in user space. The kernel updates `mult` and `shift` in `vdso_data` and the vDSO reads them directly.

Example calculation:
```
TSC frequency: 3,000,000,000 Hz (3 GHz)
We want: 1 cycle → 1/3 nanoseconds ≈ 0.333 ns

mult  = (1e9 * 2^shift) / 3e9
shift = 22 (chosen to maximize precision without overflow)
mult  = (1e9 * 4194304) / 3e9 = 1398101

Verify: (1 * 1398101) >> 22 = 1398101 / 4194304 ≈ 0.333 ns ✓
```

---

## 11. C Implementation — Deep Dive

### 11.1 Basic vDSO Usage via glibc

Most C programs use the vDSO without knowing it, because glibc wraps `clock_gettime()`:

```c
// This already uses vDSO transparently via glibc:
#include <time.h>

struct timespec ts;
clock_gettime(CLOCK_MONOTONIC, &ts);
// No syscall is made! glibc found vDSO at startup and calls directly into it.
```

### 11.2 Finding and Calling vDSO Functions Manually

```c
// vdso_manual.c — Manually locate and call vDSO functions
// Compile: gcc -O2 -o vdso_manual vdso_manual.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <sys/auxv.h>
#include <elf.h>

// ─── ELF Parsing Types ──────────────────────────────────────────────────────

typedef struct {
    void *addr;   // Base address of vDSO in memory
    Elf64_Ehdr *ehdr;
    Elf64_Shdr *shdrs;
    Elf64_Sym  *dynsyms;
    const char *dynstrtab;
    size_t      dynsym_count;
} VdsoInfo;

// ─── Parse the vDSO ELF ─────────────────────────────────────────────────────

static int vdso_parse(VdsoInfo *info)
{
    unsigned long base = getauxval(AT_SYSINFO_EHDR);
    if (!base) {
        fprintf(stderr, "AT_SYSINFO_EHDR not found — no vDSO\n");
        return -1;
    }

    info->addr  = (void *)base;
    info->ehdr  = (Elf64_Ehdr *)base;

    // Validate ELF magic
    if (memcmp(info->ehdr->e_ident, ELFMAG, SELFMAG) != 0) {
        fprintf(stderr, "Invalid ELF magic at vDSO base\n");
        return -1;
    }

    // Validate it's a 64-bit shared library
    if (info->ehdr->e_ident[EI_CLASS] != ELFCLASS64 ||
        info->ehdr->e_type != ET_DYN) {
        fprintf(stderr, "Unexpected ELF class or type\n");
        return -1;
    }

    // Section headers
    info->shdrs = (Elf64_Shdr *)(base + info->ehdr->e_shoff);

    // Find .dynsym and .dynstr sections
    const char *shstrtab = (const char *)(base +
        info->shdrs[info->ehdr->e_shstrndx].sh_offset);

    info->dynsyms   = NULL;
    info->dynstrtab = NULL;

    for (int i = 0; i < info->ehdr->e_shnum; i++) {
        Elf64_Shdr *shdr = &info->shdrs[i];
        const char *name = shstrtab + shdr->sh_name;

        if (strcmp(name, ".dynsym") == 0) {
            info->dynsyms     = (Elf64_Sym *)(base + shdr->sh_offset);
            info->dynsym_count = shdr->sh_size / sizeof(Elf64_Sym);
        } else if (strcmp(name, ".dynstr") == 0) {
            info->dynstrtab = (const char *)(base + shdr->sh_offset);
        }
    }

    if (!info->dynsyms || !info->dynstrtab) {
        fprintf(stderr, "Could not find .dynsym or .dynstr\n");
        return -1;
    }

    return 0;
}

// ─── Look Up a Symbol by Name ────────────────────────────────────────────────

static void *vdso_sym(const VdsoInfo *info, const char *name)
{
    for (size_t i = 0; i < info->dynsym_count; i++) {
        Elf64_Sym *sym = &info->dynsyms[i];

        // Only FUNC symbols
        if (ELF64_ST_TYPE(sym->st_info) != STT_FUNC)
            continue;
        if (sym->st_value == 0)
            continue;

        const char *sym_name = info->dynstrtab + sym->st_name;

        // Match full name or with __vdso_ prefix
        if (strcmp(sym_name, name) == 0 ||
            (strncmp(sym_name, "__vdso_", 7) == 0 &&
             strcmp(sym_name + 7, name) == 0)) {
            // Symbol value is an offset from ELF load address
            return (void *)((uintptr_t)info->addr + sym->st_value);
        }
    }
    return NULL;
}

// ─── Function Pointer Types ──────────────────────────────────────────────────

typedef int (*fn_clock_gettime)(clockid_t, struct timespec *);
typedef int (*fn_gettimeofday)(struct timeval *, struct timezone *);
typedef time_t (*fn_time)(time_t *);
typedef int (*fn_clock_getres)(clockid_t, struct timespec *);
typedef long (*fn_getcpu)(unsigned *, unsigned *, void *);

// ─── Print All vDSO Symbols ──────────────────────────────────────────────────

static void vdso_dump_symbols(const VdsoInfo *info)
{
    printf("vDSO base address: %p\n", info->addr);
    printf("vDSO ELF symbols:\n");
    printf("  %-40s %-18s %s\n", "Name", "Address", "Size");
    printf("  %-40s %-18s %s\n", "----", "-------", "----");

    for (size_t i = 0; i < info->dynsym_count; i++) {
        Elf64_Sym *sym = &info->dynsyms[i];
        if (ELF64_ST_TYPE(sym->st_info) != STT_FUNC || sym->st_value == 0)
            continue;

        void *addr = (void *)((uintptr_t)info->addr + sym->st_value);
        printf("  %-40s %p %zu bytes\n",
               info->dynstrtab + sym->st_name,
               addr,
               (size_t)sym->st_size);
    }
}

// ─── Benchmark: vDSO vs Syscall ──────────────────────────────────────────────

static void benchmark(fn_clock_gettime vdso_fn)
{
    const int ITERATIONS = 10000000;
    struct timespec ts, t_start, t_end;
    long long ns_vdso, ns_syscall;

    // Benchmark vDSO
    clock_gettime(CLOCK_MONOTONIC, &t_start);
    for (int i = 0; i < ITERATIONS; i++) {
        vdso_fn(CLOCK_MONOTONIC, &ts);
        __asm__ volatile("" :: "r"(ts.tv_nsec) : "memory");  // prevent optimization
    }
    clock_gettime(CLOCK_MONOTONIC, &t_end);
    ns_vdso = (t_end.tv_sec - t_start.tv_sec) * 1000000000LL +
               (t_end.tv_nsec - t_start.tv_nsec);

    // Benchmark forced syscall (using syscall() to bypass vDSO)
    clock_gettime(CLOCK_MONOTONIC, &t_start);
    for (int i = 0; i < ITERATIONS; i++) {
        // Force real syscall by bypassing glibc wrapper
        syscall(228, CLOCK_MONOTONIC, &ts);  // 228 = __NR_clock_gettime on x86-64
        __asm__ volatile("" :: "r"(ts.tv_nsec) : "memory");
    }
    clock_gettime(CLOCK_MONOTONIC, &t_end);
    ns_syscall = (t_end.tv_sec - t_start.tv_sec) * 1000000000LL +
                  (t_end.tv_nsec - t_start.tv_nsec);

    printf("\n=== Benchmark Results (%d iterations) ===\n", ITERATIONS);
    printf("vDSO clock_gettime:    %6.1f ns/call\n", (double)ns_vdso / ITERATIONS);
    printf("Syscall clock_gettime: %6.1f ns/call\n", (double)ns_syscall / ITERATIONS);
    printf("Speedup:               %.1fx\n", (double)ns_syscall / ns_vdso);
}

// ─── Main ────────────────────────────────────────────────────────────────────

int main(void)
{
    VdsoInfo vdso;
    if (vdso_parse(&vdso) != 0)
        return 1;

    vdso_dump_symbols(&vdso);

    // Look up clock_gettime
    fn_clock_gettime cgt = vdso_sym(&vdso, "clock_gettime");
    if (!cgt) {
        fprintf(stderr, "clock_gettime not found in vDSO\n");
        return 1;
    }
    printf("\nclock_gettime found at: %p\n", (void *)cgt);

    // Call it directly
    struct timespec ts;
    int ret = cgt(CLOCK_MONOTONIC, &ts);
    printf("CLOCK_MONOTONIC: %ld.%09ld (ret=%d)\n", ts.tv_sec, ts.tv_nsec, ret);

    // Test gettimeofday
    fn_gettimeofday gtod = vdso_sym(&vdso, "gettimeofday");
    if (gtod) {
        struct timeval tv;
        gtod(&tv, NULL);
        printf("gettimeofday: %ld.%06ld\n", tv.tv_sec, tv.tv_usec);
    }

    // Test getcpu
    fn_getcpu gcpu = vdso_sym(&vdso, "getcpu");
    if (gcpu) {
        unsigned cpu, node;
        gcpu(&cpu, &node, NULL);
        printf("Current CPU: %u, NUMA node: %u\n", cpu, node);
    }

    // Run benchmark
    benchmark(cgt);

    return 0;
}
```

### 11.3 vDSO-Based Raw TSC Reader (Zero-Overhead Timing)

```c
// tsc_timing.c — Use vDSO to get TSC mult/shift, then read TSC directly
// Compile: gcc -O2 -o tsc_timing tsc_timing.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/auxv.h>
#include <elf.h>

// Access the vvar page directly — this requires knowing its offset
// relative to the vDSO base. The offset is architecture-defined.
// On x86-64, vvar is at vdso_base - 1 or 2 pages (kernel version dependent).

// Read TSC directly — this is what the vDSO does internally
static inline uint64_t rdtsc(void)
{
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

// Serializing RDTSC — ensures all prior instructions complete first
// Critical for accurate microbenchmarks
static inline uint64_t rdtscp(uint32_t *aux)
{
    uint32_t lo, hi;
    __asm__ volatile("rdtscp" : "=a"(lo), "=d"(hi), "=c"(*aux));
    return ((uint64_t)hi << 32) | lo;
}

// CPUID serialization before RDTSC — the gold standard for benchmarking
static inline uint64_t rdtsc_serialized(void)
{
    uint32_t eax, ebx, ecx, edx;
    __asm__ volatile("cpuid"
        : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
        : "0"(0)
        :);
    return rdtsc();
}

// Convert TSC cycles to nanoseconds using kernel-provided mult/shift
// These values must be read from vvar/vdso_data
static inline uint64_t cycles_to_ns(uint64_t cycles, uint32_t mult, uint32_t shift)
{
    // Avoid 128-bit overflow: use __uint128_t for intermediate
    return ((__uint128_t)cycles * mult) >> shift;
}

int main(void)
{
    // Demonstrate direct TSC reading with overhead measurement
    const int N = 100;
    uint64_t samples[N];
    uint32_t cpu;

    printf("Direct TSC measurements (rdtscp):\n");
    for (int i = 0; i < N; i++) {
        uint64_t t0 = rdtscp(&cpu);
        // Minimal work — measure the overhead of rdtscp itself
        uint64_t t1 = rdtscp(&cpu);
        samples[i] = t1 - t0;
    }

    // Compute statistics
    uint64_t min = UINT64_MAX, max = 0, sum = 0;
    for (int i = 0; i < N; i++) {
        if (samples[i] < min) min = samples[i];
        if (samples[i] > max) max = samples[i];
        sum += samples[i];
    }
    printf("  rdtscp overhead: min=%lu, max=%lu, avg=%lu cycles\n",
           min, max, sum / N);

    printf("\nNote: Convert cycles→ns using vdso_data.mult and .shift\n");
    printf("(vvar page must be parsed — see kernel source for offset)\n");

    return 0;
}
```

### 11.4 No-libc vDSO Consumer (Bare Metal ELF)

This demonstrates how to use the vDSO in a program with no C runtime — only raw Linux syscalls and the vDSO:

```c
// nolibc_vdso.c — Program with _start, no CRT, no glibc
// Compile: gcc -O2 -nostdlib -static-pie -o nolibc_vdso nolibc_vdso.c
// Note: -static-pie creates a position-independent executable

#include <stdint.h>
#include <elf.h>

// Linux syscall interface
#define SYS_write  1
#define SYS_exit   60
#define AT_NULL    0
#define AT_SYSINFO_EHDR 33

static long syscall3(long n, long a, long b, long c)
{
    long ret;
    __asm__ volatile(
        "syscall"
        : "=a"(ret)
        : "0"(n), "D"(a), "S"(b), "d"(c)
        : "rcx", "r11", "memory"
    );
    return ret;
}

static void write_str(const char *s)
{
    int len = 0;
    while (s[len]) len++;
    syscall3(SYS_write, 1, (long)s, len);
}

// ─── Minimal ELF parsing to find vDSO clock_gettime ─────────────────────────

static void *find_vdso_sym(void *vdso_base, const char *target)
{
    Elf64_Ehdr *ehdr = vdso_base;
    Elf64_Shdr *shdrs = (Elf64_Shdr *)((char *)vdso_base + ehdr->e_shoff);
    const char *shstrtab = (char *)vdso_base +
                           shdrs[ehdr->e_shstrndx].sh_offset;

    Elf64_Sym  *dynsym   = NULL;
    const char *dynstrtab = NULL;
    size_t      dynsym_n  = 0;

    for (int i = 0; i < ehdr->e_shnum; i++) {
        const char *name = shstrtab + shdrs[i].sh_name;
        // strcmp without libc
        int eq;
        eq = 1;
        for (int j = 0; ; j++) {
            if (name[j] != ".dynsym"[j]) { eq = 0; break; }
            if (!name[j]) break;
        }
        if (eq) {
            dynsym  = (Elf64_Sym *)((char *)vdso_base + shdrs[i].sh_offset);
            dynsym_n = shdrs[i].sh_size / sizeof(Elf64_Sym);
        }
        eq = 1;
        for (int j = 0; ; j++) {
            if (name[j] != ".dynstr"[j]) { eq = 0; break; }
            if (!name[j]) break;
        }
        if (eq)
            dynstrtab = (char *)vdso_base + shdrs[i].sh_offset;
    }

    if (!dynsym || !dynstrtab) return 0;

    for (size_t i = 0; i < dynsym_n; i++) {
        if (ELF64_ST_TYPE(dynsym[i].st_info) != STT_FUNC) continue;
        if (!dynsym[i].st_value) continue;
        const char *sname = dynstrtab + dynsym[i].st_name;
        // Find "clock_gettime" or "__vdso_clock_gettime"
        int match = 1;
        const char *t = target;
        const char *s = sname;
        // Check for __vdso_ prefix
        if (s[0]=='_' && s[1]=='_' && s[2]=='v' && s[3]=='d' &&
            s[4]=='s' && s[5]=='o' && s[6]=='_') s += 7;
        for (; *t && *s; t++, s++) {
            if (*t != *s) { match = 0; break; }
        }
        if (match && !*t && !*s)
            return (char *)vdso_base + dynsym[i].st_value;
    }
    return 0;
}

// ─── Parse auxiliary vector from stack ──────────────────────────────────────

static unsigned long parse_auxv(unsigned long *sp)
{
    int argc = (int)*sp;
    char **argv = (char **)(sp + 1);
    char **envp = argv + argc + 1;
    while (*envp) envp++;
    envp++;  // skip NULL

    typedef struct { unsigned long type, val; } Auxv;
    Auxv *auxv = (Auxv *)envp;
    for (; auxv->type != AT_NULL; auxv++)
        if (auxv->type == AT_SYSINFO_EHDR)
            return auxv->val;
    return 0;
}

// ─── Minimal number→string conversion ───────────────────────────────────────

static void write_u64(uint64_t n)
{
    char buf[21];
    int i = 20;
    buf[i] = '\0';
    if (!n) { buf[--i] = '0'; }
    while (n) { buf[--i] = '0' + (n % 10); n /= 10; }
    int len = 20 - i;
    syscall3(SYS_write, 1, (long)(buf + i), len);
}

// ─── Entry Point ─────────────────────────────────────────────────────────────

struct timespec { long tv_sec; long tv_nsec; };

void _start_c(unsigned long *sp)
{
    unsigned long vdso_base = parse_auxv(sp);

    write_str("=== No-libc vDSO Demo ===\n");

    if (!vdso_base) {
        write_str("ERROR: No vDSO found\n");
        syscall3(SYS_exit, 1, 0, 0);
    }

    write_str("vDSO base: 0x");
    // Print hex address
    char hex[17] = "0000000000000000";
    for (int i = 15; i >= 0; i--) {
        int nibble = vdso_base & 0xF;
        hex[i] = nibble < 10 ? '0' + nibble : 'a' + nibble - 10;
        vdso_base >>= 4;
    }
    syscall3(SYS_write, 1, (long)hex, 16);
    write_str("\n");

    // Restore base (we shifted it above — in real code, save it first)
    unsigned long base = parse_auxv(sp); // re-parse for demo purposes
    typedef int (*cgt_t)(int, struct timespec *);
    cgt_t cgt = find_vdso_sym((void *)base, "clock_gettime");

    if (!cgt) {
        write_str("ERROR: clock_gettime not found in vDSO\n");
        syscall3(SYS_exit, 1, 0, 0);
    }

    write_str("clock_gettime found!\n");

    struct timespec ts;
    int ret = cgt(1, &ts);  // 1 = CLOCK_MONOTONIC

    write_str("CLOCK_MONOTONIC: ");
    write_u64((uint64_t)ts.tv_sec);
    write_str(".");
    // Zero-pad nanoseconds to 9 digits
    char nsec_str[10] = "000000000";
    uint64_t ns = (uint64_t)ts.tv_nsec;
    for (int i = 8; i >= 0 && ns; i--) {
        nsec_str[i] = '0' + (ns % 10);
        ns /= 10;
    }
    syscall3(SYS_write, 1, (long)nsec_str, 9);
    write_str("\n");

    write_str("ret = ");
    write_u64((uint64_t)(ret < 0 ? -ret : ret));
    write_str("\n");

    syscall3(SYS_exit, 0, 0, 0);
    __builtin_unreachable();
}

// Naked _start — set up the C call convention and jump to _start_c
__attribute__((naked)) void _start(void)
{
    __asm__ volatile(
        "mov %rsp, %rdi\n"   // First argument: stack pointer
        "call _start_c\n"
        "ud2\n"              // Should never reach here
    );
}
```

### 11.5 vDSO Inspection Tool

```c
// vdso_inspect.c — Comprehensive vDSO inspector
// Compile: gcc -O0 -g -o vdso_inspect vdso_inspect.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/auxv.h>
#include <elf.h>

// Parse and pretty-print the entire vDSO ELF
void inspect_vdso(void)
{
    unsigned long base = getauxval(AT_SYSINFO_EHDR);
    if (!base) { fprintf(stderr, "No vDSO\n"); return; }

    Elf64_Ehdr *ehdr = (Elf64_Ehdr *)base;

    printf("━━━ vDSO ELF Header ━━━\n");
    printf("  Type:       %s\n", ehdr->e_type == ET_DYN ? "ET_DYN (Shared Object)" : "Other");
    printf("  Machine:    0x%x (%s)\n", ehdr->e_machine,
           ehdr->e_machine == EM_X86_64 ? "x86-64" :
           ehdr->e_machine == EM_AARCH64 ? "AArch64" : "Other");
    printf("  Entry:      0x%lx\n", ehdr->e_entry);
    printf("  Sections:   %d\n", ehdr->e_shnum);
    printf("  PH entries: %d\n", ehdr->e_phnum);

    // Section headers
    Elf64_Shdr *shdrs = (Elf64_Shdr *)(base + ehdr->e_shoff);
    const char *shstrtab = (char *)(base + shdrs[ehdr->e_shstrndx].sh_offset);

    printf("\n━━━ Section Headers ━━━\n");
    printf("  %-20s %-12s %-12s %-10s\n", "Name", "Type", "Offset", "Size");
    for (int i = 0; i < ehdr->e_shnum; i++) {
        const char *type_str = "?";
        switch (shdrs[i].sh_type) {
            case SHT_NULL:     type_str = "NULL";     break;
            case SHT_PROGBITS: type_str = "PROGBITS"; break;
            case SHT_SYMTAB:   type_str = "SYMTAB";   break;
            case SHT_DYNSYM:   type_str = "DYNSYM";   break;
            case SHT_STRTAB:   type_str = "STRTAB";   break;
            case SHT_RELA:     type_str = "RELA";      break;
            case SHT_HASH:     type_str = "HASH";      break;
            case SHT_DYNAMIC:  type_str = "DYNAMIC";   break;
            case SHT_NOTE:     type_str = "NOTE";      break;
            case SHT_GNU_VERNEED: type_str = "VERNEED"; break;
            case SHT_GNU_VERDEF:  type_str = "VERDEF";  break;
            case SHT_GNU_VERSYM:  type_str = "VERSYM";  break;
        }
        printf("  %-20s %-12s 0x%-10lx %lu\n",
               shstrtab + shdrs[i].sh_name,
               type_str,
               shdrs[i].sh_offset,
               shdrs[i].sh_size);
    }

    // Program headers
    Elf64_Phdr *phdrs = (Elf64_Phdr *)(base + ehdr->e_phoff);
    printf("\n━━━ Program Headers ━━━\n");
    printf("  %-15s %-12s %-12s %-10s %-8s\n",
           "Type", "VAddr", "PAddr", "FileSize", "Flags");
    for (int i = 0; i < ehdr->e_phnum; i++) {
        const char *type_str = "?";
        switch (phdrs[i].p_type) {
            case PT_LOAD:    type_str = "PT_LOAD";    break;
            case PT_DYNAMIC: type_str = "PT_DYNAMIC"; break;
            case PT_NOTE:    type_str = "PT_NOTE";    break;
            case PT_GNU_EH_FRAME: type_str = "PT_GNU_EH_FRAME"; break;
            case PT_GNU_STACK:    type_str = "PT_GNU_STACK";    break;
        }
        char flags[4] = "---";
        if (phdrs[i].p_flags & PF_R) flags[0] = 'R';
        if (phdrs[i].p_flags & PF_W) flags[1] = 'W';
        if (phdrs[i].p_flags & PF_X) flags[2] = 'X';
        printf("  %-15s 0x%010lx 0x%010lx %-10lu %s\n",
               type_str,
               phdrs[i].p_vaddr,
               phdrs[i].p_paddr,
               phdrs[i].p_filesz,
               flags);
    }

    // Dynamic symbols
    Elf64_Sym *dynsyms = NULL;
    const char *dynstrtab = NULL;
    size_t dynsym_count = 0;

    for (int i = 0; i < ehdr->e_shnum; i++) {
        const char *name = shstrtab + shdrs[i].sh_name;
        if (!strcmp(name, ".dynsym")) {
            dynsyms = (Elf64_Sym *)(base + shdrs[i].sh_offset);
            dynsym_count = shdrs[i].sh_size / sizeof(Elf64_Sym);
        } else if (!strcmp(name, ".dynstr")) {
            dynstrtab = (char *)(base + shdrs[i].sh_offset);
        }
    }

    if (dynsyms && dynstrtab) {
        printf("\n━━━ Dynamic Symbols ━━━\n");
        printf("  %-45s %-18s %-8s %s\n", "Name", "Address", "Size", "Bind");
        for (size_t i = 0; i < dynsym_count; i++) {
            if (ELF64_ST_TYPE(dynsyms[i].st_info) == STT_FUNC &&
                dynsyms[i].st_value) {
                void *addr = (void *)(base + dynsyms[i].st_value);
                const char *bind = ELF64_ST_BIND(dynsyms[i].st_info) == STB_GLOBAL
                                   ? "GLOBAL" : "LOCAL";
                printf("  %-45s %p %-8lu %s\n",
                       dynstrtab + dynsyms[i].st_name,
                       addr,
                       (unsigned long)dynsyms[i].st_size,
                       bind);
            }
        }
    }
}

int main(void)
{
    inspect_vdso();

    // Also print relevant /proc entries
    printf("\n━━━ Memory Maps (vDSO related) ━━━\n");
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps) {
        char line[256];
        while (fgets(line, sizeof(line), maps)) {
            if (strstr(line, "vdso") || strstr(line, "vvar"))
                printf("  %s", line);
        }
        fclose(maps);
    }

    return 0;
}
```

---

## 12. Rust Implementation — Deep Dive

### 12.1 Safe vDSO Wrapper in Rust

```rust
// vdso/src/lib.rs
// A safe, idiomatic Rust wrapper around vDSO functionality
//
// Cargo.toml:
// [dependencies]
// libc = "0.2"
//
// [features]
// raw_tsc = []  # Enable raw TSC access

use std::ffi::CStr;
use std::ptr;

/// Error types for vDSO operations
#[derive(Debug, Clone, PartialEq)]
pub enum VdsoError {
    /// AT_SYSINFO_EHDR not found in auxiliary vector
    NoVdso,
    /// ELF magic mismatch — not a valid ELF file
    InvalidElf,
    /// Unexpected ELF class (not 64-bit)
    WrongElfClass,
    /// Symbol not found in vDSO
    SymbolNotFound(String),
    /// Platform not supported
    UnsupportedPlatform,
}

impl std::fmt::Display for VdsoError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            VdsoError::NoVdso => write!(f, "vDSO not available (AT_SYSINFO_EHDR missing)"),
            VdsoError::InvalidElf => write!(f, "Invalid ELF magic at vDSO base"),
            VdsoError::WrongElfClass => write!(f, "vDSO is not a 64-bit ELF"),
            VdsoError::SymbolNotFound(s) => write!(f, "Symbol '{}' not found in vDSO", s),
            VdsoError::UnsupportedPlatform => write!(f, "Platform not supported"),
        }
    }
}

impl std::error::Error for VdsoError {}

// ─── ELF Types (64-bit) ──────────────────────────────────────────────────────

const ELFMAG: [u8; 4] = [0x7f, b'E', b'L', b'F'];
const ELFCLASS64: u8 = 2;
const ET_DYN: u16 = 3;
const STT_FUNC: u8 = 2;
const SHT_DYNSYM: u32 = 11;
const SHT_STRTAB: u32 = 3;

#[repr(C)]
struct Elf64Ehdr {
    e_ident:     [u8; 16],
    e_type:      u16,
    e_machine:   u16,
    e_version:   u32,
    e_entry:     u64,
    e_phoff:     u64,
    e_shoff:     u64,
    e_flags:     u32,
    e_ehsize:    u16,
    e_phentsize: u16,
    e_phnum:     u16,
    e_shentsize: u16,
    e_shnum:     u16,
    e_shstrndx:  u16,
}

#[repr(C)]
struct Elf64Shdr {
    sh_name:      u32,
    sh_type:      u32,
    sh_flags:     u64,
    sh_addr:      u64,
    sh_offset:    u64,
    sh_size:      u64,
    sh_link:      u32,
    sh_info:      u32,
    sh_addralign: u64,
    sh_entsize:   u64,
}

#[repr(C)]
struct Elf64Sym {
    st_name:  u32,
    st_info:  u8,
    st_other: u8,
    st_shndx: u16,
    st_value: u64,
    st_size:  u64,
}

// ─── Symbol Information ───────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct VdsoSymbol {
    pub name:    String,
    pub address: usize,
    pub size:    u64,
}

// ─── Core vDSO Structure ─────────────────────────────────────────────────────

/// Parsed representation of the kernel's vDSO
pub struct Vdso {
    base:         *const u8,
    size:         usize,
    symbols:      Vec<VdsoSymbol>,
}

// SAFETY: The vDSO is mapped read-only and valid for the lifetime of the process.
// We only hold a raw pointer to read-only memory, so Send + Sync are safe.
unsafe impl Send for Vdso {}
unsafe impl Sync for Vdso {}

impl Vdso {
    /// Parse the vDSO from the current process's address space.
    ///
    /// This reads the auxiliary vector to find the vDSO base address
    /// (AT_SYSINFO_EHDR), then parses the ELF to extract all exported symbols.
    pub fn new() -> Result<Self, VdsoError> {
        // Only support x86-64, AArch64, and riscv64 for now
        #[cfg(not(any(
            target_arch = "x86_64",
            target_arch = "aarch64",
            target_arch = "riscv64"
        )))]
        return Err(VdsoError::UnsupportedPlatform);

        let base = Self::find_vdso_base()?;

        let mut vdso = Vdso {
            base,
            size: 0,
            symbols: Vec::new(),
        };

        // SAFETY: base comes from AT_SYSINFO_EHDR which the kernel guarantees
        // is a valid, mapped ELF header for the lifetime of the process.
        unsafe { vdso.parse_elf()? };

        Ok(vdso)
    }

    /// Find the vDSO base address via the auxiliary vector.
    fn find_vdso_base() -> Result<*const u8, VdsoError> {
        // Use getauxval() from libc to find AT_SYSINFO_EHDR
        // AT_SYSINFO_EHDR = 33
        let val = unsafe { libc::getauxval(libc::AT_SYSINFO_EHDR) };
        if val == 0 {
            Err(VdsoError::NoVdso)
        } else {
            Ok(val as *const u8)
        }
    }

    /// Parse the ELF structure of the vDSO.
    ///
    /// # Safety
    /// `self.base` must point to a valid, mapped ELF file.
    unsafe fn parse_elf(&mut self) -> Result<(), VdsoError> {
        let base = self.base;
        let ehdr = &*(base as *const Elf64Ehdr);

        // Validate ELF magic
        if ehdr.e_ident[..4] != ELFMAG {
            return Err(VdsoError::InvalidElf);
        }

        // Validate 64-bit ELF
        if ehdr.e_ident[4] != ELFCLASS64 {
            return Err(VdsoError::WrongElfClass);
        }

        // Section headers
        let shdrs_base = base.add(ehdr.e_shoff as usize) as *const Elf64Shdr;
        let shnum = ehdr.e_shnum as usize;

        // String table for section names
        let shstrtab_shdr = &*shdrs_base.add(ehdr.e_shstrndx as usize);
        let shstrtab = base.add(shstrtab_shdr.sh_offset as usize);

        // Find .dynsym and .dynstr sections
        let mut dynsym_ptr: *const Elf64Sym = ptr::null();
        let mut dynsym_count: usize = 0;
        let mut dynstrtab: *const u8 = ptr::null();

        for i in 0..shnum {
            let shdr = &*shdrs_base.add(i);
            let sh_name = CStr::from_ptr(shstrtab.add(shdr.sh_name as usize) as *const i8)
                .to_str()
                .unwrap_or("");

            match (shdr.sh_type, sh_name) {
                (SHT_DYNSYM, ".dynsym") => {
                    dynsym_ptr = base.add(shdr.sh_offset as usize) as *const Elf64Sym;
                    dynsym_count = (shdr.sh_size / shdr.sh_entsize) as usize;
                    self.size = (shdr.sh_offset + shdr.sh_size) as usize;
                }
                (SHT_STRTAB, ".dynstr") => {
                    dynstrtab = base.add(shdr.sh_offset as usize);
                }
                _ => {}
            }
        }

        if dynsym_ptr.is_null() || dynstrtab.is_null() {
            // vDSO exists but has unusual structure — still not an error
            return Ok(());
        }

        // Extract all function symbols
        for i in 0..dynsym_count {
            let sym = &*dynsym_ptr.add(i);

            // Only export FUNC symbols with non-zero values
            let st_type = sym.st_info & 0xF;
            if st_type != STT_FUNC || sym.st_value == 0 {
                continue;
            }

            let raw_name = CStr::from_ptr(dynstrtab.add(sym.st_name as usize) as *const i8)
                .to_str()
                .unwrap_or("")
                .to_string();

            let address = (base as usize) + sym.st_value as usize;

            self.symbols.push(VdsoSymbol {
                name: raw_name,
                address,
                size: sym.st_size,
            });
        }

        Ok(())
    }

    /// Get the vDSO base address.
    pub fn base_address(&self) -> usize {
        self.base as usize
    }

    /// Get all exported symbols.
    pub fn symbols(&self) -> &[VdsoSymbol] {
        &self.symbols
    }

    /// Find a symbol by name.
    ///
    /// Matches both `name` and `__vdso_name` variants.
    pub fn find_symbol(&self, name: &str) -> Option<&VdsoSymbol> {
        let vdso_name = format!("__vdso_{}", name);
        let kernel_name = format!("__kernel_{}", name); // ARM64 convention

        self.symbols.iter().find(|s| {
            s.name == name || s.name == vdso_name || s.name == kernel_name
        })
    }

    /// Get a function pointer from the vDSO by symbol name.
    ///
    /// # Safety
    /// The caller must ensure the function signature `F` matches the actual
    /// vDSO function signature. Incorrect signatures lead to undefined behavior.
    pub unsafe fn get_fn<F: Copy>(&self, name: &str) -> Result<F, VdsoError> {
        let sym = self.find_symbol(name)
            .ok_or_else(|| VdsoError::SymbolNotFound(name.to_string()))?;

        // Transmute the address to the function pointer type.
        // This is sound only if F exactly matches the vDSO function's ABI.
        let fn_ptr: F = std::mem::transmute_copy(&sym.address);
        Ok(fn_ptr)
    }
}

// ─── High-Level Clock API ─────────────────────────────────────────────────────

/// Function pointer type for `clock_gettime`
type ClockGettimeFn = unsafe extern "C" fn(libc::clockid_t, *mut libc::timespec) -> libc::c_int;

/// Function pointer type for `gettimeofday`
type GettimeofdayFn = unsafe extern "C" fn(*mut libc::timeval, *mut libc::timezone) -> libc::c_int;

/// Function pointer type for `getcpu`
type GetcpuFn = unsafe extern "C" fn(*mut u32, *mut u32, *mut libc::c_void) -> libc::c_long;

/// High-level, safe interface to vDSO clock functions.
pub struct VdsoClock {
    clock_gettime_fn:  Option<ClockGettimeFn>,
    gettimeofday_fn:   Option<GettimeofdayFn>,
    getcpu_fn:         Option<GetcpuFn>,
}

impl VdsoClock {
    /// Resolve vDSO clock functions. Falls back gracefully if not available.
    pub fn new(vdso: &Vdso) -> Self {
        // SAFETY: We use the correct C function signatures as defined by the
        // Linux ABI for these vDSO exports. The types match the kernel's
        // exported function signatures exactly.
        let clock_gettime_fn = unsafe {
            vdso.get_fn::<ClockGettimeFn>("clock_gettime").ok()
        };
        let gettimeofday_fn = unsafe {
            vdso.get_fn::<GettimeofdayFn>("gettimeofday").ok()
        };
        let getcpu_fn = unsafe {
            vdso.get_fn::<GetcpuFn>("getcpu").ok()
        };

        VdsoClock { clock_gettime_fn, gettimeofday_fn, getcpu_fn }
    }

    /// Get monotonic time. Falls back to libc if vDSO unavailable.
    pub fn monotonic_time(&self) -> std::time::Duration {
        let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };

        if let Some(f) = self.clock_gettime_fn {
            // SAFETY: ts is a valid, initialized mutable reference.
            // f is a valid function pointer from the vDSO.
            unsafe { f(libc::CLOCK_MONOTONIC, &mut ts) };
        } else {
            // Fallback to libc (which itself likely uses vDSO)
            unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts) };
        }

        std::time::Duration::new(ts.tv_sec as u64, ts.tv_nsec as u32)
    }

    /// Get real (wall clock) time.
    pub fn realtime(&self) -> std::time::Duration {
        let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };

        if let Some(f) = self.clock_gettime_fn {
            unsafe { f(libc::CLOCK_REALTIME, &mut ts) };
        } else {
            unsafe { libc::clock_gettime(libc::CLOCK_REALTIME, &mut ts) };
        }

        std::time::Duration::new(ts.tv_sec as u64, ts.tv_nsec as u32)
    }

    /// Get coarse monotonic time (faster, lower resolution).
    pub fn monotonic_coarse(&self) -> std::time::Duration {
        let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };

        if let Some(f) = self.clock_gettime_fn {
            unsafe { f(libc::CLOCK_MONOTONIC_COARSE, &mut ts) };
        } else {
            unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC_COARSE, &mut ts) };
        }

        std::time::Duration::new(ts.tv_sec as u64, ts.tv_nsec as u32)
    }

    /// Get current CPU and NUMA node.
    pub fn current_cpu(&self) -> Option<(u32, u32)> {
        let f = self.getcpu_fn?;
        let mut cpu: u32 = 0;
        let mut node: u32 = 0;
        // SAFETY: pointers are valid stack variables, f is a valid vDSO fn ptr.
        unsafe { f(&mut cpu, &mut node, ptr::null_mut()) };
        Some((cpu, node))
    }

    /// Check if vDSO clock_gettime is available.
    pub fn has_vdso_clock(&self) -> bool {
        self.clock_gettime_fn.is_some()
    }
}

// ─── Instant — Monotonic Clock Wrapper ───────────────────────────────────────

/// A monotonic instant using the vDSO for maximum performance.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Instant {
    nanos: u64,
}

impl Instant {
    pub fn now(clock: &VdsoClock) -> Self {
        let d = clock.monotonic_time();
        Instant {
            nanos: d.as_secs() * 1_000_000_000 + d.subsec_nanos() as u64,
        }
    }

    pub fn elapsed_since(&self, earlier: Instant) -> std::time::Duration {
        let nanos = self.nanos.saturating_sub(earlier.nanos);
        std::time::Duration::from_nanos(nanos)
    }

    pub fn as_nanos(&self) -> u64 {
        self.nanos
    }
}
```

### 12.2 Rust Benchmark & Usage

```rust
// src/main.rs — vDSO benchmark and demonstration

mod vdso; // The lib above

use vdso::{Vdso, VdsoClock, Instant};
use std::time::Instant as StdInstant;

fn benchmark_vdso_vs_std(clock: &VdsoClock) {
    const N: usize = 10_000_000;

    // Warm up
    for _ in 0..1000 {
        let _ = clock.monotonic_time();
    }

    // Benchmark vDSO
    let start = StdInstant::now();
    let mut checksum = 0u64;
    for _ in 0..N {
        let t = clock.monotonic_time();
        checksum ^= t.as_nanos() as u64; // prevent optimization
    }
    let vdso_ns = start.elapsed().as_nanos() / N as u128;

    // Benchmark std::time::Instant (also uses vDSO via libc, but with more overhead)
    let start = StdInstant::now();
    let mut checksum2 = 0u64;
    for _ in 0..N {
        let t = StdInstant::now();
        checksum2 ^= t.elapsed().as_nanos() as u64;
    }
    let std_ns = start.elapsed().as_nanos() / N as u128;

    // Prevent dead code elimination
    println!("checksums: {} {} (ignore these)", checksum, checksum2);

    println!("\n=== Benchmark Results ({} iterations) ===", N);
    println!("  Direct vDSO clock_gettime: {} ns/call", vdso_ns);
    println!("  std::time::Instant::now(): {} ns/call", std_ns);
}

fn main() {
    println!("=== vDSO Rust Demo ===\n");

    // Parse the vDSO
    let vdso = match Vdso::new() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Failed to parse vDSO: {}", e);
            std::process::exit(1);
        }
    };

    println!("vDSO base address: {:#x}", vdso.base_address());
    println!("\nExported symbols:");
    for sym in vdso.symbols() {
        println!("  {:45} @ {:#x}  ({} bytes)", sym.name, sym.address, sym.size);
    }

    // Create clock interface
    let clock = VdsoClock::new(&vdso);
    println!("\nvDSO clock_gettime available: {}", clock.has_vdso_clock());

    // Demonstrate usage
    let mono = clock.monotonic_time();
    println!("\nCLOCK_MONOTONIC:       {}.{:09}s", mono.as_secs(), mono.subsec_nanos());

    let real = clock.realtime();
    println!("CLOCK_REALTIME:        {}.{:09}s", real.as_secs(), real.subsec_nanos());

    let coarse = clock.monotonic_coarse();
    println!("CLOCK_MONOTONIC_COARSE:{}.{:09}s", coarse.as_secs(), coarse.subsec_nanos());

    if let Some((cpu, node)) = clock.current_cpu() {
        println!("Current CPU: {}, NUMA node: {}", cpu, node);
    }

    // High-level Instant usage
    let t0 = Instant::now(&clock);
    std::thread::sleep(std::time::Duration::from_millis(10));
    let t1 = Instant::now(&clock);
    println!("\nElapsed (10ms sleep): {:?}", t1.elapsed_since(t0));

    // Run benchmarks
    benchmark_vdso_vs_std(&clock);
}
```

### 12.3 Raw TSC Access in Rust

```rust
// tsc.rs — Direct TSC access from Rust with vDSO-derived calibration

/// Read the TSC with RDTSC instruction.
/// Not serializing — instruction reordering can occur.
#[cfg(target_arch = "x86_64")]
#[inline(always)]
pub fn rdtsc() -> u64 {
    let lo: u32;
    let hi: u32;
    // SAFETY: RDTSC is always available on x86-64 and has no side effects.
    unsafe {
        std::arch::asm!(
            "rdtsc",
            out("eax") lo,
            out("edx") hi,
            options(nostack, nomem, preserves_flags),
        );
    }
    ((hi as u64) << 32) | (lo as u64)
}

/// Serializing TSC read using RDTSCP.
/// Ensures all prior instructions complete before reading.
/// Also returns the current CPU ID in `aux` bits [11:0] and processor ID in [31:12].
#[cfg(target_arch = "x86_64")]
#[inline(always)]
pub fn rdtscp() -> (u64, u32) {
    let lo: u32;
    let hi: u32;
    let aux: u32;
    unsafe {
        std::arch::asm!(
            "rdtscp",
            out("eax") lo,
            out("edx") hi,
            out("ecx") aux,
            options(nostack, nomem),
        );
    }
    (((hi as u64) << 32) | (lo as u64), aux)
}

/// Fully serialized RDTSC using CPUID as a memory barrier before reading.
/// This is the most accurate method for benchmarking start points.
#[cfg(target_arch = "x86_64")]
#[inline(always)]
pub fn rdtsc_start() -> u64 {
    let lo: u32;
    let hi: u32;
    unsafe {
        std::arch::asm!(
            // CPUID serializes — nothing after this can execute before CPUID completes
            "xor eax, eax",
            "cpuid",
            "rdtsc",
            out("eax") lo,
            out("edx") hi,
            // CPUID clobbers eax, ebx, ecx, edx — declare them
            lateout("ebx") _,
            lateout("ecx") _,
            options(nostack),
        );
    }
    ((hi as u64) << 32) | (lo as u64)
}

/// Use RDTSCP + CPUID for end-of-benchmark serialization.
#[cfg(target_arch = "x86_64")]
#[inline(always)]
pub fn rdtsc_end() -> u64 {
    let lo: u32;
    let hi: u32;
    unsafe {
        std::arch::asm!(
            "rdtscp",       // Serializes retiring instructions
            "push rax",
            "push rdx",
            "xor eax, eax",
            "cpuid",        // Prevent subsequent code from moving before RDTSCP
            "pop rdx",
            "pop rax",
            out("eax") lo,
            out("edx") hi,
            lateout("ecx") _,
            lateout("ebx") _,
            options(nostack),
        );
    }
    ((hi as u64) << 32) | (lo as u64)
}

/// A high-resolution timer using raw TSC for maximum precision microbenchmarking.
pub struct TscTimer {
    tsc_per_ns: f64,  // TSC ticks per nanosecond
}

impl TscTimer {
    /// Calibrate TSC frequency against CLOCK_MONOTONIC via the vDSO.
    pub fn calibrate(clock: &crate::vdso::VdsoClock) -> Self {
        const SAMPLE_DURATION_NS: u64 = 100_000_000; // 100ms

        let t0_ns = clock.monotonic_time().as_nanos() as u64;
        let t0_tsc = rdtsc_start();

        // Spin for ~100ms
        loop {
            let t_ns = clock.monotonic_time().as_nanos() as u64;
            if t_ns - t0_ns >= SAMPLE_DURATION_NS {
                break;
            }
        }

        let t1_ns = clock.monotonic_time().as_nanos() as u64;
        let t1_tsc = rdtsc_end();

        let elapsed_ns = (t1_ns - t0_ns) as f64;
        let elapsed_tsc = (t1_tsc - t0_tsc) as f64;

        TscTimer {
            tsc_per_ns: elapsed_tsc / elapsed_ns,
        }
    }

    /// Convert TSC cycles to nanoseconds.
    #[inline(always)]
    pub fn cycles_to_ns(&self, cycles: u64) -> f64 {
        cycles as f64 / self.tsc_per_ns
    }

    /// Measure the execution time of a closure in nanoseconds.
    pub fn measure<F, R>(&self, f: F) -> (R, f64)
    where
        F: FnOnce() -> R,
    {
        let start = rdtsc_start();
        let result = f();
        let end = rdtsc_end();
        let ns = self.cycles_to_ns(end - start);
        (result, ns)
    }
}
```

### 12.4 Cargo.toml

```toml
[package]
name = "vdso-demo"
version = "0.1.0"
edition = "2021"

[dependencies]
libc = "0.2"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1

# Required for no_std vDSO access (advanced use)
[features]
no_std = []
```

---

## 13. Architecture-Specific Differences

### x86-64

- **vDSO name**: `linux-vdso.so.1`
- **Clock source**: TSC (Time Stamp Counter) via `RDTSC`/`RDTSCP`
- **Exported symbols**: `clock_gettime`, `gettimeofday`, `time`, `clock_getres`, `getcpu`
- **vvar location**: One or two pages immediately before vDSO text
- **vsyscall**: Fixed at `0xFFFFFFFFFF600000` (emulated, deprecated)

### AArch64 (ARM64)

- **vDSO name**: `linux-vdso.so.1`
- **Clock source**: `CNTVCT_EL0` (virtual counter register, user-accessible)
- **Exported symbols**: `__kernel_clock_gettime`, `__kernel_gettimeofday`, `__kernel_time`, `__kernel_clock_getres`
- **vvar location**: Separate `vvar` mapping, same pattern as x86
- **Special**: AArch64 CPUs expose `CNTVCT_EL0` directly to EL0 (user space), making it even faster than x86 RDTSC (no serialization needed)

```asm
// AArch64: Reading the virtual counter directly
mrs x0, cntvct_el0      // Read virtual counter — ~5 cycles, no privilege needed
mrs x1, cntfrq_el0      // Read counter frequency (for calibration)
```

### RISC-V (rv64)

- **Clock source**: `rdtime` pseudo-instruction
- **vDSO name**: `linux-vdso.so.1`
- **Exported symbols**: `__vdso_clock_gettime`, `__vdso_clock_getres`, `__vdso_gettimeofday`

```asm
// RISC-V: Reading the time register
rdtime a0       // Read machine-mode time register (user-accessible on Linux)
```

### 32-bit x86 (i386)

- **vDSO**: Separate `linux-gate.so.1` (older terminology)
- **vsyscall page**: Maps syscall mechanism (sysenter vs int 0x80)
- **Key difference**: On i386, the vDSO also provides the optimal syscall entry mechanism, not just data access

### Comparison Table

| Feature | x86-64 | AArch64 | RISC-V | i386 |
|---------|--------|---------|--------|------|
| HW counter | RDTSC | CNTVCT_EL0 | rdtime | RDTSC (TSC) |
| Serialized read | RDTSCP/CPUID | Not needed | Not needed | CPUID+RDTSC |
| User-space access | Always | Via kernel config | Via kernel | Controlled |
| vDSO name | linux-vdso.so.1 | linux-vdso.so.1 | linux-vdso.so.1 | linux-gate.so.1 |
| Cycles to read | ~20 | ~5 | ~5 | ~25 |

---

## 14. Security: ASLR, Spectre, and vDSO

### ASLR and vDSO

The vDSO participates in ASLR (Address Space Layout Randomization). Its base address is randomized each time a process is started, making it harder for exploits to predict the location of executable code (to use as ROP gadgets).

```bash
# Demonstrate ASLR: vDSO address differs between runs
for i in $(seq 5); do
    grep vdso /proc/self/maps | awk '{print $1}' | cut -d'-' -f1
done
# Output (different each run due to ASLR):
# 7f4a12345000
# 7f1b98765000
# 7fff10203000
# ...
```

### Spectre and vDSO Design

The Spectre vulnerability (CVE-2017-5753) exploits speculative execution to read kernel memory from user space. KPTI (Kernel Page Table Isolation) was the mitigation:

**Before KPTI:**
- Kernel and user page tables coexist — only permissions differ
- Syscall: just a trap, no CR3 switch
- `clock_gettime` with vDSO: ~20 cycles; without vDSO: ~100 cycles

**After KPTI:**
- Separate page tables for kernel and user mode
- Syscall: trap + CR3 switch + TLB flush + CR3 switch back
- `clock_gettime` with vDSO: still ~20 cycles (**unchanged!**)
- `clock_gettime` without vDSO (real syscall): ~2,000-4,000 cycles

**KPTI made vDSO dramatically more important.** It increased the cost of real syscalls by 10-20x, but vDSO-accelerated calls were unaffected.

### vDSO and Exploit Mitigation

The vDSO is both a security feature and a potential security concern:

**Benefits:**
- Avoids syscalls → reduces kernel attack surface for timing attacks
- Randomized address (ASLR) makes ROP harder

**Concerns:**
- The vDSO is executable user-space memory — it can be used as a source of ROP gadgets
- However, since it's randomized with ASLR, its gadgets are at unpredictable addresses
- The vDSO is read-only — it cannot be modified to inject shellcode

### seccomp and vDSO

When a process uses `seccomp` to restrict syscalls, vDSO calls are **not** affected:

```c
// seccomp blocks the clock_gettime SYSCALL instruction
// but NOT the vDSO call (which doesn't use SYSCALL at all)

// This will be blocked by seccomp(CLOCK_GETTIME):
syscall(__NR_clock_gettime, CLOCK_MONOTONIC, &ts);  // BLOCKED

// This will NOT be blocked (goes through vDSO):
clock_gettime(CLOCK_MONOTONIC, &ts);  // ALLOWED (no syscall made)
```

This is important for sandboxed applications: they can still get timestamps without requiring the `clock_gettime` syscall to be whitelisted.

---

## 15. Debugging & Inspection Tools

### Verify vDSO is Being Used (strace)

```bash
# strace shows NO clock_gettime syscall if vDSO is working:
strace -e trace=clock_gettime ./your_program

# If vDSO is working, you see NO clock_gettime lines in strace output
# (strace intercepts the SYSCALL instruction, but vDSO doesn't use it)

# Confirm it's mapped:
strace -e trace=mmap ./your_program 2>&1 | head -5
```

### gdb Inspection

```bash
# Inspect vDSO in gdb:
gdb ./your_program
(gdb) run
(gdb) info proc mappings
# Look for [vdso] and [vvar] entries

# Set a breakpoint in the vDSO:
(gdb) info sharedlibrary
(gdb) break clock_gettime  # gdb knows about vDSO symbols

# Disassemble vDSO code:
(gdb) disassemble clock_gettime
```

### Dump vDSO for Analysis

```bash
#!/bin/bash
# extract_vdso.sh — Extract vDSO from current process and disassemble

VDSO_LINE=$(cat /proc/self/maps | grep '\[vdso\]')
START=$(echo $VDSO_LINE | cut -d'-' -f1)
END=$(echo $VDSO_LINE | cut -d' ' -f1 | cut -d'-' -f2)
SIZE=$(( 0x$END - 0x$START ))

echo "vDSO: 0x$START - 0x$END (${SIZE} bytes)"

# Dump using dd + /proc/self/mem
dd if=/proc/self/mem of=/tmp/vdso_dump.so \
   iflag=skip_bytes,count_bytes \
   skip=$(( 16#$START )) \
   count=$SIZE 2>/dev/null

echo "Written to /tmp/vdso_dump.so"

# Analyze it
echo ""
echo "=== readelf -s ==="
readelf -s /tmp/vdso_dump.so

echo ""
echo "=== objdump -d ==="
objdump -d --no-show-raw-insn /tmp/vdso_dump.so
```

### perf and vDSO

```bash
# Profile to see if clock_gettime is in vDSO or real syscall:
perf stat -e syscalls:sys_enter_clock_gettime ./your_program

# If count is 0 → vDSO is handling all calls
# If count > 0 → Some calls are real syscalls (falling through)

# Detailed profiling:
perf record -g ./your_program
perf report
# Look for [vdso] in the symbol column
```

### ltrace for vDSO calls

```bash
# ltrace shows library calls — DOES capture vDSO calls since it hooks the PLT
ltrace -e clock_gettime ./your_program
# Output:
# clock_gettime(1, {tv_sec=..., tv_nsec=...}) = 0
```

---

## 16. Performance Benchmarks & Analysis

### Typical Results (x86-64, Intel, with KPTI)

| Method | Cycles | Nanoseconds | Notes |
|--------|--------|-------------|-------|
| vDSO `clock_gettime` | 20-40 | 7-15 ns | Invariant TSC, no ring switch |
| vDSO `gettimeofday` | 20-35 | 7-12 ns | Same path, slightly less work |
| vDSO `clock_gettime` (coarse) | 10-15 | 3-5 ns | Read vvar directly, no TSC |
| Raw `RDTSC` | 20-25 | 7-8 ns | No namespace conversion |
| `libc clock_gettime` | 25-50 | 8-17 ns | Same as vDSO (libc uses it) |
| Real `syscall` (no KPTI) | 100-200 | 33-67 ns | Just the trap overhead |
| Real `syscall` (KPTI on) | 1000-3000 | 333-1000 ns | TLB flush each direction |
| `syscall` (IBRS + KPTI) | 2000-5000 | 667-1667 ns | Spectre mitigations |

### Why CLOCK_MONOTONIC_COARSE is Faster

`CLOCK_MONOTONIC_COARSE` doesn't read the TSC at all. It simply reads pre-computed values from the vvar page (updated only at each timer tick, typically 4ms on HZ=250 systems):

```c
// Fast path for COARSE clocks — just read vvar, no TSC math
static noinline int do_coarse(const struct vdso_data *vd, clockid_t clk,
                               struct __kernel_timespec *ts)
{
    const struct vdso_timestamp *vdso_ts = &vd->basetime[clk];
    u32 seq;

    do {
        seq = vdso_read_begin(vd);
        ts->tv_sec  = vdso_ts->sec;
        ts->tv_nsec = vdso_ts->nsec;
    } while (unlikely(vdso_read_retry(vd, seq)));

    return 0;
}
// No RDTSC! Just a memory read + seqlock. ~10 cycles total.
```

### Choosing the Right Clock

```
┌──────────────────────────────────────────────────────────────────┐
│  Which clock should I use?                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Need sub-millisecond accuracy?                                   │
│  ├── YES → CLOCK_MONOTONIC or CLOCK_REALTIME                     │
│  │         (full TSC resolution, ~7ns overhead)                  │
│  └── NO  → CLOCK_MONOTONIC_COARSE or CLOCK_REALTIME_COARSE      │
│            (timer tick resolution ~1-4ms, ~3ns overhead)         │
│                                                                   │
│  Need to compare across processes/machines?                       │
│  ├── YES → CLOCK_REALTIME (wall clock)                           │
│  └── NO  → CLOCK_MONOTONIC (no jumps, no NTP adjustments)       │
│                                                                   │
│  Need to survive suspend/hibernate?                               │
│  └── YES → CLOCK_BOOTTIME (includes sleep time)                  │
│                                                                   │
│  Benchmarking at nanosecond granularity?                         │
│  └── Use RDTSC directly + TscTimer calibration                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 17. Advanced: Writing a Custom vDSO Consumer

### Scenario: High-Frequency Trading Timestamp Library

```c
// hft_timer.h — Production-grade timestamp library using vDSO + TSC
// For latency-critical code paths (order entry, market data processing)

#pragma once
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/auxv.h>
#include <elf.h>
#include <time.h>

// ─── Global State (initialized once at startup) ───────────────────────────────

typedef int (*clock_gettime_fn)(clockid_t, struct timespec *);

struct hft_timer_state {
    clock_gettime_fn  cgt;          // vDSO clock_gettime function pointer
    uint32_t          tsc_mult;     // TSC → ns multiplier (from kernel calibration)
    uint32_t          tsc_shift;    // TSC → ns shift
    uint64_t          epoch_tsc;    // TSC at initialization
    uint64_t          epoch_ns;     // Nanoseconds at initialization (monotonic)
    int               tsc_stable;   // Is TSC invariant on this CPU?
};

extern struct hft_timer_state g_hft_timer;

// Initialize — call once at startup
int hft_timer_init(void);

// Get current time in nanoseconds (monotonic)
static inline __attribute__((always_inline)) uint64_t hft_now_ns(void)
{
    if (__builtin_expect(g_hft_timer.tsc_stable, 1)) {
        // Fast path: raw RDTSC + pre-computed mult/shift
        uint32_t lo, hi;
        __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
        uint64_t tsc = ((uint64_t)hi << 32) | lo;
        uint64_t delta_tsc = tsc - g_hft_timer.epoch_tsc;
        uint64_t delta_ns = ((__uint128_t)delta_tsc * g_hft_timer.tsc_mult)
                            >> g_hft_timer.tsc_shift;
        return g_hft_timer.epoch_ns + delta_ns;
    } else {
        // Slow path: vDSO clock_gettime (still no syscall)
        struct timespec ts;
        g_hft_timer.cgt(CLOCK_MONOTONIC, &ts);
        return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
    }
}

// Measure elapsed time in nanoseconds
static inline uint64_t hft_elapsed_ns(uint64_t start_ns)
{
    return hft_now_ns() - start_ns;
}
```

```c
// hft_timer.c — Implementation

#include "hft_timer.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

struct hft_timer_state g_hft_timer = {0};

static void *find_symbol(void *base, const char *target)
{
    Elf64_Ehdr *ehdr = base;
    Elf64_Shdr *shdrs = (void *)((char *)base + ehdr->e_shoff);
    const char *shstr = (char *)base + shdrs[ehdr->e_shstrndx].sh_offset;

    Elf64_Sym  *syms = NULL;
    const char *strtab = NULL;
    size_t      nsyms = 0;

    for (int i = 0; i < ehdr->e_shnum; i++) {
        const char *n = shstr + shdrs[i].sh_name;
        if (!strcmp(n, ".dynsym")) {
            syms  = (void *)((char *)base + shdrs[i].sh_offset);
            nsyms = shdrs[i].sh_size / sizeof(*syms);
        } else if (!strcmp(n, ".dynstr")) {
            strtab = (char *)base + shdrs[i].sh_offset;
        }
    }
    if (!syms || !strtab) return NULL;

    for (size_t i = 0; i < nsyms; i++) {
        if ((syms[i].st_info & 0xF) != 2 || !syms[i].st_value) continue;
        const char *name = strtab + syms[i].st_name;
        if (!strcmp(name, target)) return (char *)base + syms[i].st_value;
        // Try __vdso_ prefix
        if (!strncmp(name, "__vdso_", 7) && !strcmp(name + 7, target))
            return (char *)base + syms[i].st_value;
    }
    return NULL;
}

static int check_invariant_tsc(void)
{
    // Check for invariant TSC via CPUID leaf 0x80000007
    uint32_t eax, ebx, ecx, edx;
    __asm__ volatile("cpuid"
        : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
        : "0"(0x80000007), "2"(0));
    return (edx & (1 << 8)) != 0;  // Bit 8: Invariant TSC
}

int hft_timer_init(void)
{
    unsigned long vdso_base = getauxval(AT_SYSINFO_EHDR);
    if (!vdso_base) return -1;

    g_hft_timer.cgt = find_symbol((void *)vdso_base, "clock_gettime");
    if (!g_hft_timer.cgt) return -1;

    // Check TSC stability
    g_hft_timer.tsc_stable = check_invariant_tsc();

    // Get current monotonic time for epoch
    struct timespec ts;
    g_hft_timer.cgt(CLOCK_MONOTONIC, &ts);
    g_hft_timer.epoch_ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    // Capture TSC at same moment
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    g_hft_timer.epoch_tsc = ((uint64_t)hi << 32) | lo;

    // Read mult/shift from vdso_data (simplified — real impl reads from vvar)
    // For now, calibrate empirically
    // Measure TSC ticks over 10ms using clock_gettime
    uint64_t t0_ns = g_hft_timer.epoch_ns;
    uint64_t t0_tsc = g_hft_timer.epoch_tsc;

    // Spin 10ms
    do {
        g_hft_timer.cgt(CLOCK_MONOTONIC, &ts);
    } while ((uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec - t0_ns < 10000000);

    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    uint64_t t1_tsc = ((uint64_t)hi << 32) | lo;
    uint64_t t1_ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    double tsc_per_ns = (double)(t1_tsc - t0_tsc) / (double)(t1_ns - t0_ns);

    // Compute mult/shift: ns = (tsc * mult) >> shift
    // Choose shift = 22 for balance of precision vs range
    g_hft_timer.tsc_shift = 22;
    g_hft_timer.tsc_mult = (uint32_t)((1.0 / tsc_per_ns) * (1ULL << 22) + 0.5);

    fprintf(stderr, "HFT Timer: TSC stable=%d, mult=%u, shift=%u, %.3f GHz\n",
            g_hft_timer.tsc_stable,
            g_hft_timer.tsc_mult,
            g_hft_timer.tsc_shift,
            tsc_per_ns);

    return 0;
}
```

---

## 18. vDSO in Containers & Sandboxes

### Docker and vDSO

Docker containers share the host kernel — and therefore the same vDSO. The vDSO is mapped into every container's processes just like in the host:

```bash
# Inside a Docker container:
cat /proc/self/maps | grep vdso
# 7fff12345000-7fff12347000 r-xp 00000000 00:00 0  [vdso]
# Works exactly as on the host
```

### Kubernetes and vDSO

Same as Docker — the kernel is shared, vDSO is always available unless explicitly restricted.

### gVisor (User-Space Kernel)

gVisor (`runsc`) intercepts all syscalls and provides its own kernel implementation. However, gVisor **also provides a vDSO** that maps into guest processes — its own version, not the host kernel's. This allows `clock_gettime` to work efficiently inside gVisor without crossing into the host kernel.

### seccomp-BPF and vDSO

seccomp filters operate at the syscall boundary. Since vDSO calls don't generate a `SYSCALL` instruction, they bypass seccomp entirely:

```c
// seccomp program that blocks clock_gettime SYSCALL
// will NOT block vDSO clock_gettime
struct sock_filter filter[] = {
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clock_gettime, 1, 0),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),
};
// This does NOT prevent vDSO clock_gettime from working!
```

### Disabling vDSO for Testing

```bash
# Disable vDSO for a single process (useful for strace profiling, testing)
LD_PRELOAD="" VDSO_DISABLE=1 ./your_program  # (some distros support this)

# Force disable via personality:
setarch $(uname -m) --addr-no-randomize --whole-seconds ./prog

# In C — disable vDSO by clearing AT_SYSINFO_EHDR:
// Manually clear it in the auxiliary vector before exec
// (complex — typically done by specialized test frameworks)
```

---

## 19. Common Pitfalls & Edge Cases

### Pitfall 1: Assuming vDSO is Always Present

```c
// WRONG:
unsigned long base = getauxval(AT_SYSINFO_EHDR);
Elf64_Ehdr *ehdr = (Elf64_Ehdr *)base;  // NULL dereference if no vDSO!

// CORRECT:
unsigned long base = getauxval(AT_SYSINFO_EHDR);
if (!base) {
    // vDSO not available — fall back to syscall
    fallback_to_syscall();
    return;
}
```

### Pitfall 2: vDSO Clock Falling Back to Syscall

Not all clock IDs are handled by the vDSO. When an unsupported clock ID is requested, the vDSO code falls back to making a real syscall:

```c
// vDSO handles this (fast):
clock_gettime(CLOCK_MONOTONIC, &ts);

// vDSO cannot handle this (falls back to syscall):
clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &ts);
```

Verify with strace:

```bash
strace -e clock_gettime ./program 2>&1 | grep "clock_gettime"
# Any output here means a REAL syscall was made for that call
```

### Pitfall 3: TSC Instability

On some systems (VMs, heterogeneous CPU clusters, older hardware), the TSC is not invariant. The vDSO detects this at boot time and falls back to a different clock source (HPET, etc.). In this case, `clock_gettime` via vDSO may still not make a syscall but will read from HPET via vvar instead of using RDTSC.

```bash
# Check clocksource in use:
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
# "tsc"   → TSC in use (fast vDSO path)
# "hpet"  → HPET in use (slower, but still no syscall via vDSO)
# "acpi_pm" → Very slow, possibly making real syscalls

# Check available clocksources:
cat /sys/devices/system/clocksource/clocksource0/available_clocksource
```

### Pitfall 4: Direct vvar Access is Not Supported API

The `vvar` page layout is **not a stable ABI**. Its structure (`struct vdso_data`) changes between kernel versions. You should never parse vvar directly in user code — only the vDSO code itself (which is kernel-version-matched) should access it.

```c
// WRONG — vvar structure is not stable ABI:
struct vdso_data *vd = (struct vdso_data *)(vdso_base - PAGE_SIZE);
uint64_t sec = vd->basetime[0].sec;  // Will break across kernel versions

// CORRECT — use the vDSO function:
clock_gettime(CLOCK_REALTIME, &ts);  // Let vDSO handle vvar access
```

### Pitfall 5: vDSO Code Cannot Call glibc

The vDSO is compiled without libc. Any attempt to call a glibc function from within vDSO code would fail at link time. This is by design — the vDSO must be entirely self-contained.

### Pitfall 6: Function Pointer Casting Must Match Exactly

```c
// WRONG: wrong return type
typedef void (*bad_fn_t)(clockid_t, struct timespec *);
bad_fn_t fn = vdso_sym(&vdso, "clock_gettime");
fn(CLOCK_MONOTONIC, &ts);  // Undefined behavior — int return discarded incorrectly

// CORRECT: must exactly match the ABI
typedef int (*cgt_t)(clockid_t, struct timespec *);
cgt_t fn = (cgt_t)vdso_sym(&vdso, "clock_gettime");
int ret = fn(CLOCK_MONOTONIC, &ts);
```

### Pitfall 7: Multi-Architecture ELF Parsing

On 32-bit ARM or x86 systems, you need `Elf32_Ehdr`, `Elf32_Shdr`, `Elf32_Sym` etc. Using 64-bit types on a 32-bit vDSO will produce garbage.

```c
#if defined(__LP64__)
  typedef Elf64_Ehdr Elf_Ehdr;
  typedef Elf64_Shdr Elf_Shdr;
  typedef Elf64_Sym  Elf_Sym;
#else
  typedef Elf32_Ehdr Elf_Ehdr;
  typedef Elf32_Shdr Elf_Shdr;
  typedef Elf32_Sym  Elf_Sym;
#endif
```

---

## 20. Summary & Reference Table

### Core Concepts Summary

| Concept | Description |
|---------|-------------|
| **vDSO** | A kernel-built shared library mapped into every process, providing fast user-space implementations of select syscalls |
| **vvar** | Read-only kernel data page(s) containing clock state that vDSO functions read without privilege switch |
| **AT_SYSINFO_EHDR** | Auxiliary vector entry that gives the vDSO base address to user space |
| **seqlock** | Optimistic concurrency protocol used to read consistent vvar data without locking |
| **TSC** | x86 hardware counter (`RDTSC`) used to compute sub-tick time deltas |
| **KPTI** | Kernel Page Table Isolation — Meltdown mitigation that makes real syscalls much more expensive; makes vDSO value much higher |
| **vsyscall** | Legacy fixed-address mechanism, deprecated in favor of vDSO |

### vDSO Exported Functions Reference

| Function | Clock IDs Handled | Fallback? | Use Case |
|----------|------------------|-----------|---------|
| `clock_gettime` | REALTIME, MONOTONIC, REALTIME_COARSE, MONOTONIC_COARSE, BOOTTIME, TAI | Yes (real syscall) | General timestamps |
| `gettimeofday` | Wall clock only | No (always vDSO) | Legacy POSIX |
| `time` | Seconds only | No | Coarse wall clock |
| `clock_getres` | All above | Partial | Clock resolution query |
| `getcpu` | N/A | No | CPU affinity detection |

### Key Files in Linux Kernel Source

| File | Purpose |
|------|---------|
| `arch/x86/entry/vdso/vclock_gettime.c` | x86-64 vDSO `clock_gettime` implementation |
| `arch/x86/entry/vdso/vma.c` | vDSO mapping into process address space |
| `arch/x86/entry/vdso/vdso.lds.S` | vDSO ELF linker script |
| `include/vdso/datapage.h` | `vdso_data` structure definition |
| `kernel/time/vsyscall.c` | Kernel-side vvar update logic |
| `arch/arm64/kernel/vdso/` | ARM64 vDSO implementation |

### Quick Command Reference

```bash
# Find vDSO in process memory
cat /proc/self/maps | grep -E 'vdso|vvar'

# Extract vDSO ELF to file
vdso_start=$(awk '/\[vdso\]/{split($1,a,"-"); print "0x"a[1]}' /proc/self/maps)
size=$(awk '/\[vdso\]/{split($1,a,"-"); printf "%d\n", strtonum("0x"a[2])-strtonum("0x"a[1])}' /proc/self/maps)
dd if=/proc/self/mem bs=1 skip=$((vdso_start)) count=$size of=/tmp/vdso.so 2>/dev/null

# Inspect symbols
readelf -s /tmp/vdso.so

# Disassemble
objdump -d /tmp/vdso.so

# Check TSC clock source
cat /sys/devices/system/clocksource/clocksource0/current_clocksource

# Verify vDSO is used (no syscalls)
strace -e clock_gettime ./program

# Check aux vector
LD_SHOW_AUXV=1 /bin/true 2>&1 | grep SYSINFO

# Check KPTI
dmesg | grep -i "page table isolation\|PTI\|KPTI"

# Check CPU TSC invariance
grep flags /proc/cpuinfo | head -1 | tr ' ' '\n' | grep -E 'constant_tsc|nonstop_tsc'
```

---

*This guide covers Linux kernel vDSO internals as of kernels 5.x–6.x. Specific `vdso_data` layouts and vvar offsets vary by kernel version and architecture. Always use the vDSO's exported functions rather than directly parsing vvar in production code.*

*References: Linux kernel source tree, `man 7 vdso`, `man 2 clock_gettime`, Intel Software Developer's Manual (Vol. 3, RDTSC/RDTSCP), Cloudflare blog on KPTI overhead.*

Here's a complete breakdown of what the guide covers across all 20 sections:

**Foundational concepts** — Why vDSO exists, the full anatomy of a syscall cost (registers, privilege switch, CR3 write, TLB flush, KPTI), and the exact speedup breakdown. KPTI (Meltdown mitigation) made syscalls 10-20x more expensive and made vDSO dramatically more valuable.

**Kernel internals** — How the vDSO is compiled at kernel build time (with `–nostdlib`, `-fPIC`, `-fno-stack-protector`), embedded as raw bytes in the kernel image, and mapped into every process via `arch_setup_additional_pages()` at exec time.

**ELF structure** — Complete section/program header breakdown, how to extract and disassemble the vDSO live from `/proc/self/mem`, and the symbol versioning scheme (`clock_gettime@@LINUX_2.6`).

**vvar and seqlock** — The beating heart: the kernel's `vdso_data` struct, the seqlock protocol (why seq must be even before reading, and why you spin-retry on concurrent kernel writes), and how `CLOCK_MONOTONIC_COARSE` bypasses TSC entirely for even lower overhead.

**C implementations** — A full manual ELF parser + symbol resolver, a no-libc `_start` implementation that calls vDSO with zero CRT, a comprehensive inspector tool, and a production-grade HFT timestamp library using raw RDTSC + vDSO-calibrated `mult/shift`.

**Rust implementation** — A fully safe `Vdso` struct with ELF parsing, a `VdsoClock` wrapper with proper `unsafe` encapsulation, a `TscTimer` using inline asm for `rdtsc`/`rdtscp`/serialized variants, and idiomatic ergonomics throughout.

**Security, containers, pitfalls** — ASLR interaction, Spectre/KPTI relationship, seccomp bypass behavior, gVisor's own vDSO, and 7 concrete pitfalls with correct fixes.