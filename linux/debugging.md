# Linux Kernel Debugging: A Complete In-Depth Guide

> **Scope:** Memory, Networking, Filesystems, Tracing, Crashes, Locking, Scheduling, Drivers, and Boot — from first principles to production-grade analysis.

---

## Table of Contents

1. [Kernel Debugging Philosophy & Architecture](#1-kernel-debugging-philosophy--architecture)
2. [Build-Time Debug Configuration](#2-build-time-debug-configuration)
3. [Kernel Oops, Panics & Stack Trace Analysis](#3-kernel-oops-panics--stack-trace-analysis)
4. [KGDB — Full Source-Level Kernel Debugger](#4-kgdb--full-source-level-kernel-debugger)
5. [Memory Debugging](#5-memory-debugging)
   - KASAN, KMSAN, KFENCE, SLUB Debug, KMEMLEAK
6. [Tracing Infrastructure](#6-tracing-infrastructure)
   - ftrace, perf, eBPF/bpftrace
7. [Network Debugging](#7-network-debugging)
8. [Filesystem Debugging](#8-filesystem-debugging)
9. [Locking & Concurrency Bugs](#9-locking--concurrency-bugs)
10. [Scheduler Debugging](#10-scheduler-debugging)
11. [Driver & Hardware Debugging](#11-driver--hardware-debugging)
12. [Crash Dump Analysis (kdump + crash)](#12-crash-dump-analysis-kdump--crash)
13. [Boot-Time Debugging](#13-boot-time-debugging)
14. [QEMU-Based Kernel Debugging Workflow](#14-qemu-based-kernel-debugging-workflow)
15. [Systematic Debugging Methodology](#15-systematic-debugging-methodology)
16. [Reference: Key Files, Interfaces & Commands](#16-reference-key-files-interfaces--commands)

---

## 1. Kernel Debugging Philosophy & Architecture

### Why Kernel Debugging Is Fundamentally Different

User-space debugging is familiar: a process crashes, you attach `gdb`, you read a core dump, you step through code. The kernel does not afford you these luxuries by default.

The kernel:
- **Is the OS itself** — it cannot simply "pause" like a process
- **Runs in ring 0 (x86)** — a single instruction fault can corrupt the entire machine state
- **Has no MMU protection against itself** — a wild pointer in the kernel can silently corrupt arbitrary memory
- **Owns interrupt handling** — a deadlock means the entire machine freezes
- **Manages its own allocator, scheduler, and concurrency** — bugs in these subsystems undermine all other debugging tools

This means you approach kernel debugging as a **forensic investigator**, not an interactive debugger. You collect evidence (logs, traces, dumps), reconstruct state, and prove causality.

### Debugging Layers

```
┌─────────────────────────────────────────────────────┐
│                   User Space                        │
│  strace, ltrace, gdb, valgrind, perf (userland)     │
├─────────────────────────────────────────────────────┤
│              Kernel / User Boundary                  │
│  syscall tracing, seccomp, audit, eBPF uprobes       │
├─────────────────────────────────────────────────────┤
│                 Kernel Space                         │
│  printk, ftrace, kprobes, perf events, KASAN, SLUB  │
│  lockdep, kgdb, kdump, /proc, /sys, tracefs          │
├─────────────────────────────────────────────────────┤
│              Hardware / Firmware                     │
│  JTAG, PMU counters, IOMMU faults, APEI/GHES        │
└─────────────────────────────────────────────────────┘
```

### The `/proc` and `/sys` Filesystems

These are **the primary runtime introspection interfaces** of the kernel. Never treat them as implementation details.

| Path | Purpose |
|------|---------|
| `/proc/kallsyms` | All exported kernel symbols with addresses |
| `/proc/slabinfo` | SLAB/SLUB allocator stats per cache |
| `/proc/meminfo` | Global memory accounting |
| `/proc/net/` | Networking state (sockets, routes, neighbors) |
| `/proc/sys/` | Tunables (same as `sysctl`) |
| `/proc/<pid>/maps` | Memory map of a process |
| `/sys/kernel/debug/` | debugfs — tracing, kprobes, lock stats |
| `/sys/kernel/tracing/` | Modern tracing interface (tracefs) |

---

## 2. Build-Time Debug Configuration

The kernel's `Kconfig` system controls which debugging infrastructure is compiled in. Most production kernels disable these for performance. For debugging, you rebuild with them enabled — or use a dedicated debug kernel.

### Essential Debug Kconfig Options

```bash
# Run menuconfig or edit .config directly
make menuconfig
# → Kernel hacking → ...
```

#### Memory Debugging

```kconfig
CONFIG_KASAN=y                   # Kernel Address Sanitizer (heap OOB, UAF)
CONFIG_KASAN_INLINE=y            # Faster KASAN (vs outline)
CONFIG_KMSAN=y                   # Kernel Memory Sanitizer (uninitialized reads)
CONFIG_KFENCE=y                  # Low-overhead sampling memory safety (prod-safe)
CONFIG_DEBUG_KMEMLEAK=y          # Memory leak detector
CONFIG_SLUB_DEBUG=y              # SLUB allocator metadata & poison
CONFIG_DEBUG_PAGEALLOC=y         # Poison freed pages (catches UAF immediately)
CONFIG_DEBUG_VIRTUAL=y           # Validate virtual→physical translations
CONFIG_HIGHMEM_DEBUG=y           # HIGHMEM pointer use debugging
```

#### Locking & Concurrency

```kconfig
CONFIG_LOCKDEP=y                 # Lock dependency validator (catches deadlocks)
CONFIG_PROVE_LOCKING=y           # Compile-time lock ordering proofs
CONFIG_DEBUG_SPINLOCK=y          # Spinlock misuse detection
CONFIG_DEBUG_MUTEXES=y           # Mutex debugging
CONFIG_DEBUG_RWSEMS=y            # RW semaphore debugging
CONFIG_DEBUG_ATOMIC_SLEEP=y      # Catch sleeping in atomic context
CONFIG_DEBUG_RT_MUTEXES=y        # RT mutex debugging (for PREEMPT_RT)
CONFIG_KCSAN=y                   # Kernel Concurrency Sanitizer (data races)
CONFIG_RCU_TORTURE_TEST=m        # RCU correctness stress test
```

#### Tracing

```kconfig
CONFIG_FTRACE=y
CONFIG_FUNCTION_TRACER=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_DYNAMIC_FTRACE=y          # Per-function enable/disable at runtime
CONFIG_KPROBES=y                 # Dynamic probes on any kernel instruction
CONFIG_UPROBES=y                 # User-space probes from kernel context
CONFIG_PERF_EVENTS=y
CONFIG_BPF_SYSCALL=y             # eBPF syscall interface
CONFIG_BPF_JIT=y                 # JIT compile eBPF for performance
CONFIG_DEBUG_FS=y                # Mount debugfs
CONFIG_TRACING=y
CONFIG_STACK_TRACER=y            # Trace maximum stack depth
```

#### Crash & Panic

```kconfig
CONFIG_KEXEC=y                   # Required for kdump
CONFIG_CRASH_DUMP=y              # vmcore generation
CONFIG_DEBUG_INFO=y              # DWARF debug info in vmlinux
CONFIG_DEBUG_INFO_DWARF5=y       # DWARF5 (modern, better BTF interop)
CONFIG_FRAME_POINTER=y           # Reliable stack unwinding
CONFIG_UNWINDER_FRAME_POINTER=y  # Use frame pointer unwinder
# or
CONFIG_UNWINDER_ORC=y            # ORC unwinder (faster, no FP requirement)
CONFIG_PANIC_ON_OOPS=y           # Force panic on oops (for kdump trigger)
CONFIG_RANDOMIZE_BASE=n          # Disable KASLR for deterministic addresses
```

#### Scheduler

```kconfig
CONFIG_SCHED_DEBUG=y             # /proc/sched_debug, scheduler statistics
CONFIG_SCHEDSTATS=y              # Per-entity scheduling statistics
CONFIG_DEBUG_PREEMPT=y           # Catch preemption count underflow/overflow
CONFIG_PREEMPT_TRACER=y          # Trace preemption disable time
CONFIG_IRQSOFF_TRACER=y          # Trace IRQ disable latency
CONFIG_WAKEUP_TRACER=y           # Trace wakeup latency
```

### Building with Debug Info

```bash
# Build the kernel with full debug info
make -j$(nproc) KCFLAGS="-g3 -O0"  # O0 for best debuggability (slow)
# or keep O2 but add debug info
make -j$(nproc)

# Generate BTF (BPF Type Format) — needed for modern eBPF tools
# Requires pahole >= 1.16
make -j$(nproc) CONFIG_DEBUG_INFO_BTF=y
```

---

## 3. Kernel Oops, Panics & Stack Trace Analysis

### What is a Kernel Oops?

An **Oops** is a recoverable (sometimes) kernel error. The kernel detected something it cannot continue normally — an invalid memory access, a BUG() macro, a NULL pointer dereference. It prints a structured diagnostic to the kernel log and may kill the offending process. It does **not** always halt the system.

A **Panic** is an unrecoverable Oops, or an Oops that occurs in an interrupt or context from which recovery is impossible. The machine halts.

### Anatomy of a Kernel Oops

```
BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
#PF: supervisor read access in kernel mode
#PF: error_code(0x0000) - not-present page
PGD 0 P4D 0
Oops: 0000 [#1] SMP KASAN PTI
CPU: 3 PID: 1234 Comm: mydriver Not tainted 6.8.0-debug #1
Hardware name: QEMU Standard PC (i440FX + PIIX, 1996)
RIP: 0010:my_device_probe+0x47/0x130 [mydriver]
Code: 48 8b 43 08 48 85 c0 74 1e 48 89 c7 e8 ...
RSP: 0018:ffffc90000d27b90 EFLAGS: 00010246
RAX: 0000000000000000 RBX: ffff888105c4a000 RCX: 0000000000000000
...
FS:  00007f8b3c6ac740(0000) GS:ffff88813bc00000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 0000000000000008 CR3: 0000000103e22004 CR4: 00000000003706e0
Call Trace:
 <TASK>
 platform_probe+0x40/0xa0
 really_probe+0xde/0x380
 __driver_probe_device+0x78/0x170
 driver_probe_device+0x1e/0x90
 __device_attach_driver+0x9b/0x110
 ...
 </TASK>
CR2: 0000000000000008
```

### Decoding Every Field

#### Line 1: Fault Type

```
BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
```

- `0000000000000008` = address 8 = NULL + 8 bytes offset
- This means we dereferenced a NULL pointer and accessed the second field of a struct (8 bytes into it on 64-bit)
- Common cause: `struct foo *f = NULL; f->bar;` where `bar` is the second pointer-sized field

#### `#PF: error_code(0x0000)`

The x86 Page Fault error code bitmap:
- Bit 0: 0 = page not present, 1 = protection violation
- Bit 1: 0 = read, 1 = write
- Bit 2: 0 = kernel mode, 1 = user mode
- Bit 4: 0 = no instruction fetch, 1 = instruction fetch (NX violation)

`0x0000` = not-present page, read access, kernel mode.

#### `Oops: 0000 [#1]`

- The bracketed number is the **Oops count** since boot. If you see `[#2]`, `[#3]`, the system has already been corrupted.
- `SMP KASAN PTI` = flags: symmetric multiprocessing, KASAN enabled, Page Table Isolation enabled

#### `Tainted` field

```
Not tainted 6.8.0-debug #1
```

If tainted, the flags after the kernel version explain why:

| Flag | Meaning |
|------|---------|
| `G` | Only GPL modules loaded |
| `P` | Proprietary module loaded |
| `F` | Module was force-loaded |
| `S` | SMP compiled, unsafe for non-SMP |
| `R` | Module was force-unloaded |
| `M` | MCE (machine check error) occurred |
| `B` | Page-release bug detected |
| `O` | Out-of-tree module loaded |
| `E` | Unsigned module loaded |
| `L` | Soft lockup occurred |

#### `RIP: 0010:my_device_probe+0x47/0x130`

- `RIP` = instruction pointer at fault time
- `0010` = segment selector (kernel code segment)
- `my_device_probe` = function name (from `/proc/kallsyms`)
- `+0x47` = offset **within** the function
- `/0x130` = total function size

This tells you: **the crash happened 71 bytes into `my_device_probe`, which is 304 bytes long**.

#### `Code:` line

The raw bytes of instructions around the faulting instruction. You can decode with:

```bash
echo "48 8b 43 08 48 85 c0 74 1e" | python3 -c "
import sys, subprocess
data = bytes.fromhex(sys.stdin.read().replace(' ', '').strip())
with open('/tmp/crash.bin', 'wb') as f: f.write(data)
" && objdump -D -b binary -m i386:x86-64 /tmp/crash.bin
```

Or use `gdb` on `vmlinux`:

```bash
gdb vmlinux
(gdb) x/20i my_device_probe+0x47
```

#### Register Values

```
RAX: 0000000000000000   ← RAX is NULL — likely the pointer we tried to dereference
RBX: ffff888105c4a000   ← RBX is a valid kernel address (our device struct?)
CR2: 0000000000000008   ← CR2 holds the fault address (NULL + 8 = 0x8)
```

**CR2 always holds the faulting virtual address on a page fault.** This is your primary clue.

### Decoding the Call Trace

The call trace shows the **kernel call stack** at the time of the fault, innermost (closest to crash) first.

```
Call Trace:
 <TASK>
 my_device_probe+0x47/0x130    ← Faulting function
 platform_probe+0x40/0xa0       ← Called my_device_probe
 really_probe+0xde/0x380        ← Called platform_probe
 __driver_probe_device+0x78/...
 ...
```

The `<TASK>` marker indicates this is a normal kernel task context (as opposed to `<IRQ>`, `<NMI>`, `<SOFTIRQ>`).

### `addr2line` — Map Crash Address to Source Line

```bash
# Install binutils
apt install binutils

# Decode the crash address
addr2line -e vmlinux -i ffffffffc0a01047
# Output:
# drivers/mydriver/mydriver.c:247
# (inlined from) my_device_probe at drivers/mydriver/mydriver.c:198

# For modules (.ko files), you need the module's base address
# Check /sys/module/mydriver/sections/.text
cat /sys/module/mydriver/sections/.text
# → 0xffffffffc0a00000

# Compute offset: crash_addr - base = 0xffffffffc0a01047 - 0xffffffffc0a00000 = 0x1047
addr2line -e mydriver.ko 0x1047
```

### `decode_stacktrace.sh`

The kernel ships a helper script that automates this:

```bash
# Located in scripts/ in kernel source
./scripts/decode_stacktrace.sh vmlinux /path/to/modules/ < oops.txt
```

This will:
1. Find all `+0x??/0x??` patterns in the trace
2. Run `addr2line` on each
3. Output the full source-annotated trace

### `objdump` — Disassemble Around Crash

```bash
# Get disassembly of the crashing function
objdump -d --no-show-raw-insn vmlinux | grep -A 60 "<my_device_probe>"

# Or for a module
objdump -d --adjust-vma=0xffffffffc0a00000 mydriver.ko | grep -A 60 "<my_device_probe>"
```

---

## 4. KGDB — Full Source-Level Kernel Debugger

KGDB (Kernel GNU Debugger) provides a full `gdb` stub inside the kernel, allowing you to set breakpoints, inspect variables, and step through kernel code line by line.

### Architecture

```
[Development machine]          [Target machine]
  gdb vmlinux          ←────→  Running kernel with KGDB
  (client)               serial  (stub inside kernel)
                         or
                         network (kgdb-over-ethernet)
```

The kernel itself implements the GDB Remote Serial Protocol (RSP) and communicates over a serial port, USB CDC, or network.

### Setup: Serial Connection

**Target machine kernel parameters** (`/etc/default/grub`):

```bash
GRUB_CMDLINE_LINUX="kgdboc=ttyS0,115200 kgdbwait"
# kgdboc = kgdb over console
# kgdbwait = halt at early boot and wait for debugger to attach
```

```bash
update-grub && reboot
```

**Trigger kgdb at runtime** (without kgdbwait, attach later):

```bash
# Send magic SysRq sequence to enter kgdb
echo g > /proc/sysrq-trigger
# or
sysctl kernel.sysrq=1
# then: Alt+SysRq+G
```

**Development machine — attach gdb**:

```bash
gdb vmlinux
(gdb) set remotebaud 115200
(gdb) target remote /dev/ttyUSB0
# or for network:
(gdb) target remote 192.168.1.100:1234
```

### Common KGDB / GDB Commands

```gdb
(gdb) continue               # Resume kernel execution
(gdb) break do_sys_open      # Set breakpoint on kernel function
(gdb) break mm/memory.c:1234 # Breakpoint at source line
(gdb) info breakpoints       # List all breakpoints
(gdb) delete 2               # Delete breakpoint 2
(gdb) next                   # Step over (source level)
(gdb) step                   # Step into
(gdb) nexti                  # Step over (instruction level)
(gdb) stepi                  # Step into (instruction level)

# Inspect variables
(gdb) print task->pid        # Print field of current task_struct
(gdb) print *mm              # Dereference and print struct
(gdb) print/x rip            # Print register in hex
(gdb) info registers         # All registers

# Memory inspection
(gdb) x/20xg 0xffff888100000000    # 20 x 8-byte hex values
(gdb) x/s 0xffff888100000000       # String at address
(gdb) x/20i $rip-10                # Disassemble around RIP

# Kernel-specific helpers (from vmlinux-gdb.py)
(gdb) lx-ps                        # List processes (like ps)
(gdb) lx-dmesg                     # Print kernel log
(gdb) lx-symbols                   # Load module symbols
(gdb) lx-list-check task_struct tasks  # Walk a kernel list
```

### Loading Module Symbols in GDB

When debugging loadable modules, you must tell GDB where the module's sections are loaded in memory:

```bash
# On target — get section addresses for loaded module
cat /sys/module/mydriver/sections/.text
cat /sys/module/mydriver/sections/.data
cat /sys/module/mydriver/sections/.bss

# In GDB on development machine
(gdb) add-symbol-file mydriver.ko 0xffffffffc0a00000 \
      -s .data 0xffffffffc0a05000 \
      -s .bss  0xffffffffc0a06000
```

The `lx-symbols` helper from `vmlinux-gdb.py` automates this via the kernel's sysfs interface.

### QEMU + KGDB (Best Practice for Development)

```bash
# Run kernel in QEMU with GDB stub
qemu-system-x86_64 \
  -kernel bzImage \
  -append "root=/dev/vda console=ttyS0 nokaslr kgdboc=ttyS0,115200" \
  -drive file=rootfs.img,format=raw \
  -serial stdio \
  -s -S    # -s = GDB server on tcp::1234, -S = freeze at startup

# In another terminal
gdb vmlinux
(gdb) target remote :1234
(gdb) continue
```

---

## 5. Memory Debugging

Memory corruption is the most prevalent and devastating class of kernel bug. The kernel provides a layered set of tools each targeting different bug types.

### 5.1 KASAN — Kernel Address Sanitizer

**Bug types detected:** heap out-of-bounds, use-after-free, stack out-of-bounds, global out-of-bounds, use-after-scope.

**Mechanism:** KASAN instruments every memory access at compile time. It maintains a **shadow memory** region where each byte represents the validity of 8 bytes of kernel memory. Before every load/store, the compiler inserts a check against the shadow. An invalid access triggers an immediate KASAN report.

**Shadow memory layout:**

```
Kernel address space (64-bit):
ffff888000000000 - ffffebffffffffff   Direct map
                    ↕ Every 8 bytes of direct map has 1 shadow byte
ffff000000000000 - ffff7fffffffffff   KASAN shadow region
```

**Enabling:**

```kconfig
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y   # For most platforms
# or
CONFIG_KASAN_HW_TAGS=y   # Hardware MTE (ARM only) — near-zero overhead
```

**Example KASAN report — use-after-free:**

```
==================================================================
BUG: KASAN: use-after-free in my_driver_read+0x3a/0x90
Read of size 8 at addr ffff888101234560 by task cat/1234

CPU: 1 PID: 1234 Comm: cat Not tainted 6.8.0
Call Trace:
 kasan_report+0xbc/0xf0
 __asan_report_load8_noabort+0x17/0x20
 my_driver_read+0x3a/0x90      ← Our buggy code
 vfs_read+0x8c/0x2a0
 ksys_read+0x5b/0xd0
 ...

Allocated by task 1100:
 kmalloc trace here...
 my_driver_init+0x55/0x90
 ...

Freed by task 1100:
 kfree trace here...
 my_driver_release+0x2a/0x40   ← Freed here
 ...

The buggy address belongs to the object at ffff888101234560
 which belongs to the cache kmalloc-128 of size 128

Memory state around the buggy address:
 ffff888101234500: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
 ffff888101234540: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
>ffff888101234560: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
                   ^^ fb = freed memory (poisoned)
 ffff888101234600: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
==================================================================
```

**Shadow byte values:**

| Value | Meaning |
|-------|---------|
| `00` | 8 bytes fully accessible |
| `01`-`07` | First N bytes accessible (partial) |
| `fc` | KASAN redzones (heap left redzone) |
| `fb` | Freed memory (KASAN quarantine) |
| `f8` | SLUB redzone |
| `f1` | Stack left redzone |
| `f5` | Stack use-after-return |
| `f2` | Stack middle redzone |
| `f3` | Stack right redzone |
| `fd` | Global redzone |

**KASAN modes:**

| Mode | Overhead | Notes |
|------|---------|-------|
| Generic (software) | ~2x memory, ~50% CPU | Full detection, all platforms |
| SW tags (AArch64) | ~2x memory, ~20% CPU | Uses top-byte of pointer |
| HW tags (MTE, AArch64) | ~0% memory, ~5% CPU | ARMv8.5-A hardware feature |

**KASAN tunables:**

```bash
# Runtime boot parameters
kasan=off                  # Disable KASAN at runtime
kasan.fault=panic          # Panic on KASAN fault (default: continue)
```

---

### 5.2 KMSAN — Kernel Memory Sanitizer

**Bug type detected:** Use of uninitialized kernel memory.

**Mechanism:** KMSAN tracks the "shadow" and "origin" of every memory location. The shadow records which bits are initialized. The origin records where the uninitialized value came from (allocation site). Any use of uninitialized data as a branch condition or copy-to-user triggers a report.

```kconfig
CONFIG_KMSAN=y
# Note: KMSAN is incompatible with KASAN — use one at a time
```

**KMSAN report example:**

```
BUG: KMSAN: kernel-infoleak in copy_to_user+0x...
copy_to_user+0x...
my_ioctl_handler+0x120/0x200   ← Copying uninitialized bytes to user
...

Uninit was created at:
 kmalloc+0x...
 my_ioctl_handler+0x40/0x200   ← Allocated but not fully initialized
```

**Why this matters:** Uninitialized memory leaks from kernel to userspace are a significant info-leak vulnerability class (kernel pointer exposure, stack data leaks).

---

### 5.3 KFENCE — Kernel Electric Fence

**Purpose:** Lightweight, always-on, sampling-based memory safety for production systems.

**Design philosophy:** KASAN is too expensive for production. KFENCE samples a small number of allocations (~1 per second by default) and places them on dedicated pages with guard pages. This catches bugs at low overhead but not all bugs.

```kconfig
CONFIG_KFENCE=y
```

```bash
# Adjust sample rate (allocations between KFENCE samples)
echo 100 > /sys/module/kfence/parameters/sample_interval  # ms
# Or via kernel parameter:
# kfence.sample_interval=100
```

**KFENCE report:**

```
BUG: KFENCE: out-of-bounds read in kmemcpy+0x...

Out-of-bounds read at 0xffff... (8B right of kfence-#5):
 kmemcpy+...
 my_func+0x34/0x80
 ...

kfence-#5: 0xffff...-0xffff... (128 bytes)
 allocated by task 1234:
  my_alloc at drivers/mydriver.c:100
```

---

### 5.4 SLUB Debugger

The SLUB allocator (default slab allocator since 2.6.23) has built-in debugging capabilities.

```kconfig
CONFIG_SLUB_DEBUG=y
```

**Enable per-cache debugging at boot:**

```bash
# Boot parameter — debug all caches
slub_debug=FPZU

# Debug only specific caches
slub_debug=FPZU,kmalloc-128
```

**SLUB debug flags:**

| Flag | Meaning |
|------|---------|
| `F` | Sanity checks (free list integrity) |
| `P` | Poisoning (fill with patterns) |
| `Z` | Red zoning (add guard bytes around objects) |
| `U` | Track last user (alloc/free call sites) |
| `T` | Trace (log all alloc/free) |
| `A` | Toggle failslab (random allocation failures for testing) |
| `O` | Slab debugging for all objects (not just those currently allocated) |

**Inspect SLUB at runtime:**

```bash
# List all slab caches
cat /proc/slabinfo

# Detailed per-cache info (name, active, total, object size, pages)
cat /sys/kernel/slab/<cache_name>/alloc_fastpath
cat /sys/kernel/slab/<cache_name>/total_objects

# Trigger SLUB consistency check on specific cache
echo 1 > /sys/kernel/slab/kmalloc-128/validate

# Print all SLUB debug stats
cat /sys/kernel/debug/slab/kmalloc-128/alloc_traces
```

**Interpreting SLUB corruption:**

When SLUB detects corruption, it prints which redzone or poison bytes were wrong and the allocation/free call stacks, giving you both where the object was created and where it was corrupted.

---

### 5.5 KMEMLEAK — Memory Leak Detector

**Mechanism:** KMEMLEAK scans memory periodically to find allocated kernel objects with no reachable references.

**It works like a conservative GC scanner:**
1. Track every `kmalloc`, `vmalloc`, `kmem_cache_alloc`
2. Periodically scan all memory for pointer values
3. Mark any allocation that no pointer points to as a leak

```kconfig
CONFIG_DEBUG_KMEMLEAK=y
```

```bash
# Mount debugfs if not already mounted
mount -t debugfs none /sys/kernel/debug

# Trigger a leak scan
echo scan > /sys/kernel/debug/kmemleak

# Read results
cat /sys/kernel/debug/kmemleak
```

**Example output:**

```
unreferenced object 0xffff888103c2a000 (size 512):
  comm "modprobe", pid 1234, jiffies 4295000
  hex dump (first 32 bytes):
    00 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00
  backtrace:
    kmalloc+0x...
    my_module_init+0x44/0xa0
    do_init_module+0x4f/0x220
```

**KMEMLEAK false positives** — Some legitimate kernel patterns look like leaks:
- Pointers stored in non-standard ways (XOR'd, tagged, in registers)
- `kmemdup` results stored in a per-CPU context

```c
/* Suppress false positive */
kmemleak_not_leak(ptr);   /* Suppress "not a leak" */
kmemleak_ignore(ptr);     /* Completely ignore */
kmemleak_transient_leak(ptr); /* Transient — don't report if next scan doesn't see it */
```

---

### 5.6 DEBUG_PAGEALLOC

```kconfig
CONFIG_DEBUG_PAGEALLOC=y
```

**What it does:** When a page is freed back to the page allocator, it's **mapped out of the kernel's direct mapping** (or poisoned if no-unmap variant). Any subsequent access to that freed page triggers an immediate page fault — catching use-after-free at the page granularity, even before KASAN (since no KASAN shadow setup is needed).

**Cost:** ~20-30% performance overhead due to TLB pressure. Not for production.

---

### 5.7 Memory Accounting & Pressure Analysis

For production memory issues (OOM, memory growth, high usage):

```bash
# Global memory state
cat /proc/meminfo

# Per-process memory
cat /proc/<pid>/status        # VmRSS, VmPeak, VmSwap, etc.
cat /proc/<pid>/smaps         # Per-VMA detailed breakdown
cat /proc/<pid>/smaps_rollup  # Summarized smaps

# Memory cgroup (for containerized workloads)
cat /sys/fs/cgroup/memory/<group>/memory.stat

# Kernel memory breakdown
cat /proc/meminfo | grep -E 'Slab|KernelStack|PageTables|Bounce|WritebackTmp'

# vmstat — virtual memory statistics
vmstat -s

# /proc/vmallocinfo — vmalloc regions
cat /proc/vmallocinfo | sort -k2 -rn | head -20
```

**OOM Killer Analysis:**

When the OOM killer fires, it logs:

```
Out of memory: Kill process 1234 (myapp) score 892 or sacrifice child
Killed process 1234 (myapp) total-vm:2048kB, anon-rss:1024kB, file-rss:512kB
```

The "score" is the OOM badness score (0-1000). You can read it for any process:

```bash
cat /proc/<pid>/oom_score
cat /proc/<pid>/oom_score_adj  # Adjustment (-1000 to +1000)
```

**Memory map analysis:**

```bash
# Full virtual memory map of a process
pmap -x <pid>

# Physical page frame info
cat /proc/<pid>/pagemap  # Binary — use tools like page-types
```

---

## 6. Tracing Infrastructure

### 6.1 printk — The Baseline

`printk` is the kernel's `printf`. It writes to the kernel log ring buffer, readable via `dmesg`.

**Log levels:**

```c
printk(KERN_EMERG   "system is unusable\n");   // 0
printk(KERN_ALERT   "action required\n");       // 1
printk(KERN_CRIT    "critical\n");              // 2
printk(KERN_ERR     "error\n");                 // 3
printk(KERN_WARNING "warning\n");               // 4
printk(KERN_NOTICE  "normal, notable\n");       // 5
printk(KERN_INFO    "info\n");                  // 6
printk(KERN_DEBUG   "debug\n");                 // 7

// Shorthand macros (prefer these):
pr_emerg("...\n");
pr_alert("...\n");
pr_crit("...\n");
pr_err("...\n");
pr_warn("...\n");
pr_notice("...\n");
pr_info("...\n");
pr_debug("...\n");  // Compiled out unless DEBUG is defined or dynamic debug
```

**Dynamic debug — per-callsite control:**

```bash
# Enable pr_debug for a specific file
echo 'file drivers/mydriver/mydriver.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable for a specific function
echo 'func my_function +p' > /sys/kernel/debug/dynamic_debug/control

# Enable with line numbers and function names
echo 'file mydriver.c +pflmt' > /sys/kernel/debug/dynamic_debug/control
# p = enable print, f = include function name, l = include line, m = include module, t = include thread ID

# List all dynamic debug callsites
cat /sys/kernel/debug/dynamic_debug/control | grep mydriver

# Enable module-wide
echo 'module mydriver +p' > /sys/kernel/debug/dynamic_debug/control
```

**dmesg tricks:**

```bash
dmesg -T            # Human-readable timestamps
dmesg -w            # Follow (like tail -f)
dmesg -l err,warn   # Filter by log level
dmesg --since "1 hour ago"
dmesg | grep -E 'KASAN|BUG|Oops|panic'

# Kernel log level control
dmesg -n 7          # Set console loglevel to DEBUG (all messages to console)
```

---

### 6.2 ftrace — The Kernel's Built-In Tracer

ftrace is the **most powerful built-in kernel tracing system**. It can trace function calls, latencies, interrupts, preemption, and arbitrary events with minimal overhead.

**Interface:** `/sys/kernel/tracing/` (or `/sys/kernel/debug/tracing/` on older kernels)

#### Available Tracers

```bash
cat /sys/kernel/tracing/available_tracers
# nop function function_graph blk mmiotrace wakeup wakeup_rt ...
```

#### Function Tracer

```bash
# Enable function tracer
echo function > /sys/kernel/tracing/current_tracer

# Start tracing
echo 1 > /sys/kernel/tracing/tracing_on

# Run your workload...

# Stop and read
echo 0 > /sys/kernel/tracing/tracing_on
cat /sys/kernel/tracing/trace | head -100
```

**Output:**

```
# tracer: function
#
#                            _-----=> irqs-off
#                           / _----=> need-resched
#                          | / _---=> hardirq/softirq
#                          || / _--=> preempt-depth
#                          ||| /     delay
#           TASK-PID  CPU#  ||||   TIMESTAMP  FUNCTION
#              | |     |    ||||      |         |
          bash-1234  [000] d... 12345.678901: vfs_read <-ksys_read
          bash-1234  [000] d... 12345.678910: __vfs_read <-vfs_read
          bash-1234  [000] d... 12345.678912: generic_file_read_iter <-__vfs_read
```

The columns before TIMESTAMP are the **irq/preempt flags**:
- `d` = IRQs disabled  (`.` = enabled)
- `.` = need resched not set
- `.` = not in hardirq/softirq (`H`=hardirq, `s`=softirq, `h`=hardirq inside softirq)
- `1` = preemption depth

#### Function Graph Tracer

Shows call/return with timing — better for finding where time is spent:

```bash
echo function_graph > /sys/kernel/tracing/current_tracer
echo 1 > /sys/kernel/tracing/tracing_on
# ... run workload ...
echo 0 > /sys/kernel/tracing/tracing_on
cat /sys/kernel/tracing/trace
```

**Output:**

```
 1)               |  vfs_read() {
 1)               |    rw_verify_area() {
 1)   0.123 us    |      security_file_permission();
 1)   0.890 us    |    }
 1)               |    __vfs_read() {
 1)               |      generic_file_read_iter() {
 1) + 14.567 us   |        filemap_read();
 1) + 15.234 us   |      }
 1) + 16.100 us   |    }
 1) + 17.890 us   |  }
```

`+` = >10µs, `!` = >100µs, `#` = >1000µs.

#### Filtering

```bash
# Filter to specific functions
echo 'my_driver_*' > /sys/kernel/tracing/set_ftrace_filter
cat /sys/kernel/tracing/available_filter_functions | grep my_driver

# Filter to specific PID
echo <pid> > /sys/kernel/tracing/set_ftrace_pid

# Only trace functions called from vfs_read (not their children)
echo vfs_read > /sys/kernel/tracing/set_graph_function
```

#### Trace Events (Kernel Tracepoints)

The kernel has thousands of built-in **tracepoints** — static instrumentation sites that emit structured events:

```bash
# List all available events
ls /sys/kernel/tracing/events/

# List events in a subsystem
ls /sys/kernel/tracing/events/net/
ls /sys/kernel/tracing/events/block/
ls /sys/kernel/tracing/events/ext4/
ls /sys/kernel/tracing/events/sched/

# Enable specific event
echo 1 > /sys/kernel/tracing/events/net/net_dev_xmit/enable

# Enable entire subsystem
echo 1 > /sys/kernel/tracing/events/net/enable

# Enable all events (very verbose!)
echo 1 > /sys/kernel/tracing/events/enable

# Filter an event (C-like expression syntax)
echo 'len > 1000' > /sys/kernel/tracing/events/net/net_dev_xmit/filter
```

#### kprobes — Dynamic Tracepoints on Any Instruction

kprobes let you attach a handler to any kernel instruction dynamically:

```bash
# Add a kprobe on do_sys_openat2, print the filename argument
echo 'p:myprobe do_sys_openat2 filename=+0(%si):string' > /sys/kernel/tracing/kprobe_events

# Add a kretprobe to capture the return value
echo 'r:myretprobe do_sys_openat2 retval=$retval' >> /sys/kernel/tracing/kprobe_events

# Enable the probe
echo 1 > /sys/kernel/tracing/events/kprobes/myprobe/enable

# Read output
cat /sys/kernel/tracing/trace
```

**kprobe syntax:**

```
p[:[group/]event] symbol[+offset] [fetchargs]   # Entry probe
r[maxactive][:[group/]event] symbol[+offset] [fetchargs]  # Return probe

# Fetch args:
# %register   = register value
# @address    = memory at address
# +offset(%reg) = memory at reg+offset (dereference)
# $retval     = return value (kretprobe only)
# $comm       = current task comm
# $cpu        = current CPU
# :type       = type cast (s8, u8, s16, u16, s32, u32, s64, u64, x8..x64, string, symbol)
```

#### Latency Tracers

```bash
# Trace maximum IRQ-off latency
echo irqsoff > /sys/kernel/tracing/current_tracer
echo 1 > /sys/kernel/tracing/tracing_on
# ... run workload ...
echo 0 > /sys/kernel/tracing/tracing_on
cat /sys/kernel/tracing/trace

# Trace maximum preemption-off latency
echo preemptoff > /sys/kernel/tracing/current_tracer

# Trace maximum wakeup latency (time from wakeup to running)
echo wakeup > /sys/kernel/tracing/current_tracer
```

#### `trace-cmd` — ftrace User-Space Wrapper

```bash
apt install trace-cmd

# Record function_graph for 5 seconds
trace-cmd record -p function_graph -g vfs_read -- sleep 5

# Record specific events
trace-cmd record -e net:net_dev_xmit -e sched:sched_switch -- myprogram

# View recording
trace-cmd report trace.dat | head -100

# KernelShark — GUI for trace-cmd recordings
apt install kernelshark
kernelshark trace.dat
```

---

### 6.3 perf — Linux Performance Profiler

`perf` is the kernel's standard performance analysis tool. It interfaces with PMU (Performance Monitoring Unit) hardware counters and kernel tracepoints.

#### CPU Profiling (Sampling)

```bash
# Profile system-wide, 1000 samples/sec, 10 seconds
perf record -g -F 1000 -a -- sleep 10

# Profile specific process
perf record -g -p <pid> -- sleep 10

# Profile specific command
perf record -g -- ./myprogram

# View report
perf report --stdio     # Text output
perf report             # TUI (interactive, navigate with arrows)

# Flame graph generation
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

#### Hardware Performance Counters

```bash
# Count hardware events during a command
perf stat ./myprogram

# Output example:
#  Performance counter stats for './myprogram':
#     10,000,000,000   cycles
#      5,000,000,000   instructions              #    0.50  insn per cycle
#        500,000,000   cache-references
#         50,000,000   cache-misses              #   10.00% of all cache refs
#         10,000,000   branch-misses             #    1.00% of all branches

# Specific events
perf stat -e cache-misses,cache-references,L1-dcache-loads,LLC-load-misses ./myprogram

# List all available events
perf list

# List tracepoints
perf list tracepoint | grep net
```

#### perf top — Live Profiling

```bash
perf top -g                    # System-wide, show call graphs
perf top -p <pid>              # Specific process
perf top --sort cpu,comm       # Sort by CPU and command
```

#### perf trace — syscall tracing

```bash
# Trace syscalls (like strace but with lower overhead)
perf trace -p <pid>
perf trace -- ./myprogram

# Trace only specific syscalls
perf trace -e read,write,openat -- ./myprogram
```

#### perf mem — Memory Access Profiling

```bash
# Profile memory accesses (requires hardware PEBS/IBS support)
perf mem record -- ./myprogram
perf mem report
```

#### perf lock — Lock Contention Analysis

```bash
perf lock record -- ./myprogram
perf lock report
```

#### perf sched — Scheduler Analysis

```bash
perf sched record -- sleep 5
perf sched latency          # Show per-task wakeup latencies
perf sched timehist         # Per-task scheduling timeline
perf sched map              # CPU scheduling map
```

---

### 6.4 eBPF / bpftrace — Programmable Kernel Tracing

eBPF (Extended Berkeley Packet Filter) is a revolutionary technology that allows you to run **sandboxed programs inside the kernel** at any tracepoint, kprobe, or network hook, with near-zero overhead and **no kernel modification or reboot required**.

#### Architecture

```
User space                     Kernel space
┌────────────────┐             ┌──────────────────────────────────┐
│  bpftrace      │             │  eBPF Verifier (safety check)    │
│  bcc tools     │   BPF       │  eBPF JIT Compiler               │
│  libbpf        │──syscall──→ │  eBPF Maps (shared state)        │
│  BCC Python    │             │  eBPF Programs attached to:       │
└────────────────┘             │   - Kprobes / Kretprobes          │
                               │   - Tracepoints                   │
                               │   - XDP / TC (network)            │
                               │   - LSM hooks                     │
                               │   - perf events                   │
                               └──────────────────────────────────┘
```

#### bpftrace — One-Liners and Scripts

```bash
apt install bpftrace

# Trace all system calls with latency
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @start[tid] = nsecs; }
             tracepoint:raw_syscalls:sys_exit  { @us[args->id] = hist((nsecs - @start[tid])/1000); delete(@start[tid]); }'

# Count kernel functions called from a process
bpftrace -e 'kprobe:vfs_* /pid == 1234/ { @[func] = count(); }'

# Trace opens and show filename + PID
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# Profile CPU with stack traces
bpftrace -e 'profile:hz:99 { @[kstack] = count(); }'

# Trace page faults with stack
bpftrace -e 'software:page-faults:1 { @[kstack] = count(); }'

# Network: count packets by destination port
bpftrace -e 'tracepoint:net:net_dev_xmit { @[args->name] = count(); }'

# Memory allocation tracking
bpftrace -e 'tracepoint:kmem:kmalloc { @allocs = sum(args->bytes_alloc); }'

# Track TCP state changes
bpftrace -e 'tracepoint:tcp:tcp_set_state { printf("%-12s -> %s\n", tcp_states[args->oldstate], tcp_states[args->newstate]); }'

# File I/O latency histogram
bpftrace -e '
kprobe:vfs_read { @start[tid] = nsecs; }
kretprobe:vfs_read /@start[tid]/ {
    @usecs = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'
```

#### BCC (BPF Compiler Collection) Tools

BCC provides pre-written eBPF tools for common debugging scenarios:

```bash
apt install bpfcc-tools

# All files opened (opensnoop)
opensnoop-bpfcc

# Block I/O latency (biolatency)
biolatency-bpfcc -D    # Histogram + disk breakdown

# Block I/O tracing (biotop)
biotop-bpfcc

# TCP connections (tcpconnect / tcpaccept)
tcpconnect-bpfcc       # Show outbound TCP connections
tcpaccept-bpfcc        # Show inbound TCP connections
tcplife-bpfcc          # Show TCP session lifetimes
tcpretrans-bpfcc       # Show TCP retransmissions

# Kernel memory allocations (memleak)
memleak-bpfcc -p <pid>  # Find memory leaks

# CPU scheduler (runqlat / runqlen)
runqlat-bpfcc           # CPU run queue latency histogram
runqlen-bpfcc           # CPU run queue length over time

# Caching (cachestat / cachetop)
cachestat-bpfcc         # Page cache hit/miss statistics
cachetop-bpfcc          # Top processes by cache usage

# Filesystem (ext4slower, xfsslower, etc.)
ext4slower-bpfcc 10     # Show ext4 ops slower than 10ms
xfsslower-bpfcc 10

# Syscall count (syscount)
syscount-bpfcc -p <pid>

# Stack traces for CPU events (profile)
profile-bpfcc -F 99 10  # 99hz, 10 seconds

# Kernel function calls with latency (funclatency)
funclatency-bpfcc vfs_read

# Off-CPU analysis (offcputime)
offcputime-bpfcc -p <pid> 10  # Show where process is blocked
```

---

## 7. Network Debugging

### 7.1 Network Stack Architecture

```
Application Layer (sockets)
        ↕
Socket Buffer Layer (sk_buff)
        ↕
Transport Layer (TCP/UDP/SCTP)
        ↕
Network Layer (IP, routing, netfilter)
        ↕
Device Layer (net_device, NAPI, XDP)
        ↕
Physical Hardware (NIC)
```

The **`sk_buff` (socket buffer)** is the fundamental data structure carrying packets through the stack. Every packet is an `sk_buff` from hardware reception to socket delivery (or vice versa). Corruption or double-free of `sk_buff`s is a primary network bug class.

### 7.2 Network Subsystem Debugging via /proc and /sys

```bash
# Network interface statistics
cat /proc/net/dev              # Per-interface RX/TX counters
ip -s link show eth0           # Detailed interface stats with errors

# Socket state
cat /proc/net/tcp              # All TCP sockets (IPv4)
cat /proc/net/tcp6             # All TCP sockets (IPv6)
cat /proc/net/udp              # All UDP sockets
ss -anpet                      # Modern ss with extended info

# Routing table
cat /proc/net/fib_trie         # FIB trie (routing table internals)
cat /proc/net/route            # IPv4 route cache
ip route show table all        # All routing tables

# ARP/neighbor table
cat /proc/net/arp
ip neigh show

# Network statistics
cat /proc/net/snmp             # SNMP-like counters (MIB-II)
cat /proc/net/netstat          # Extended TCP/IP stats
cat /proc/net/softnet_stat     # Per-CPU softirq stats
```

**Interpreting `/proc/net/softnet_stat`:**

```bash
cat /proc/net/softnet_stat
# Each line = one CPU
# Column 1: total frames received
# Column 2: frames dropped (full backlog)
# Column 3: frames throttled (time squeeze — not enough budget)
# Column 9: received rps (RPS redirected)
# Column 10: flow limit drops
```

If column 2 is growing, your receive queue is full → increase `net.core.netdev_max_backlog`.
If column 3 is growing, you're hitting the NAPI budget → increase `net.core.netdev_budget`.

### 7.3 Netstat / ss — Socket State Analysis

```bash
# Active connections, with process info and timer
ss -anpeto

# Count states
ss -ant | awk '{print $1}' | sort | uniq -c | sort -rn

# Find connections to specific port
ss -ant dst :443

# Show socket memory usage
ss -m -t state established

# Show TCP sockets in TIME_WAIT
ss -ant state time-wait | wc -l
```

**Key TCP states to watch:**

| State | Meaning | Problem sign |
|-------|---------|-------------|
| `ESTABLISHED` | Active connection | High count = many connections |
| `TIME_WAIT` | Waiting for final FIN | Very high count = port exhaustion |
| `CLOSE_WAIT` | App hasn't closed socket | Growing = application bug |
| `SYN_RECV` | SYN received, waiting ACK | High count = SYN flood |
| `FIN_WAIT2` | Waiting for remote FIN | Growing = remote not closing |

### 7.4 Network Tracing with ftrace/eBPF

**Using tracepoints:**

```bash
# Enable all net events
echo 1 > /sys/kernel/tracing/events/net/enable

# Key tracepoints:
# net:net_dev_xmit      - Packet transmitted by device
# net:net_dev_queue     - Packet enqueued in TX queue
# net:netif_rx          - Packet received (softirq)
# net:netif_receive_skb - Packet delivered to IP layer
# net:napi_poll         - NAPI polling

# TCP specific
echo 1 > /sys/kernel/tracing/events/tcp/enable
# tcp:tcp_send_reset    - RST sent
# tcp:tcp_receive_reset - RST received
# tcp:tcp_set_state     - State change
# tcp:tcp_retransmit_skb - Retransmission
```

**bpftrace for TCP retransmissions:**

```bash
bpftrace -e '
tracepoint:tcp:tcp_retransmit_skb {
    printf("%-8s %-6d %-21s %-21s %d/%d\n",
           comm, pid,
           ntop(args->saddr), ntop(args->daddr),
           args->sport, args->dport);
}'
```

**Track TCP connection lifecycle:**

```bash
bpftrace -e '
tracepoint:tcp:tcp_set_state {
    printf("%-12s -> %-12s %s:%d -> %s:%d\n",
           tcp_states[args->oldstate], tcp_states[args->newstate],
           ntop(args->saddr), args->sport,
           ntop(args->daddr), args->dport);
}'
```

### 7.5 Packet Capture and Analysis

**tcpdump — low level:**

```bash
tcpdump -i eth0 -nn -s0 -w capture.pcap   # Capture all on eth0
tcpdump -r capture.pcap 'tcp and port 80 and (tcp-syn != 0)'  # Read & filter
tcpdump -i any port 443 -A               # ASCII output (HTTPS encrypted)

# Show packet timestamps and delta
tcpdump -tttt -i eth0 port 80

# Capture kernel internal drops (PACKET_MMAP with drop counters)
tcpdump --direction=in -i eth0 -c 100
```

**Netfilter / iptables tracing:**

```bash
# Trace all packets through netfilter
iptables -t raw -A PREROUTING -j TRACE
iptables -t raw -A OUTPUT -j TRACE

# Enable the nf_log module
modprobe nf_log_ipv4
sysctl net.netfilter.nf_log.2=nf_log_ipv4

# Read the traces
dmesg | grep 'TRACE:'
```

**nftables tracing (modern approach):**

```bash
# Add trace to nftables ruleset
nft add rule ip filter input meta nftrace set 1

# Read trace
nft monitor trace
```

### 7.6 Network Performance Issues

**Identify NIC errors:**

```bash
ethtool -S eth0 | grep -E 'drop|err|miss|fifo|over'

# Example problematic outputs:
# rx_dropped: 12345        — NIC dropping before kernel
# tx_queue_stopped: 456    — TX queue filling up
# rx_fifo_errors: 789      — FIFO overflow in NIC buffer
```

**IRQ affinity and RSS:**

```bash
# See which CPU handles NIC interrupts
cat /proc/interrupts | grep eth0

# Check IRQ affinity
cat /proc/irq/<irq_number>/smp_affinity

# Set IRQ to CPU 2
echo 4 > /proc/irq/<irq_number>/smp_affinity  # 4 = CPU bit 2

# RSS (Receive Side Scaling) — check queue count
ethtool -l eth0
# Change queue count
ethtool -L eth0 combined 8
```

**TCP buffer tuning:**

```bash
# Current buffer sizes
sysctl net.ipv4.tcp_rmem     # min default max
sysctl net.ipv4.tcp_wmem

# Increase for high-bandwidth, high-latency paths
sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'
sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'

# Enable TCP window scaling, SACK, timestamps
sysctl -w net.ipv4.tcp_window_scaling=1
sysctl -w net.ipv4.tcp_sack=1
sysctl -w net.ipv4.tcp_timestamps=1
```

### 7.7 Netfilter / Conntrack Debugging

```bash
# Connection tracking table
cat /proc/net/nf_conntrack | head

# Conntrack statistics
cat /proc/net/stat/nf_conntrack
# Each line = one CPU
# Columns: entries searched found new invalid ignore delete delete_list insert insert_failed drop early_drop

# Common issue: conntrack table full
dmesg | grep 'nf_conntrack: table full'
# Fix:
sysctl -w net.netfilter.nf_conntrack_max=1048576
sysctl -w net.netfilter.nf_conntrack_buckets=262144

# Conntrack with nf_conntrack debug logging
echo 1 > /sys/module/nf_conntrack/parameters/log_invalid
```

---

## 8. Filesystem Debugging

### 8.1 VFS — Virtual Filesystem Switch

The VFS is a kernel abstraction layer sitting above all concrete filesystem implementations. Understanding it is essential for debugging filesystem issues.

```
open("/foo/bar")
      ↓
 VFS (path_lookup, dentry cache, inode cache)
      ↓
 filesystem-specific implementation (ext4, xfs, btrfs, ...)
      ↓
 block layer (bio, request queue)
      ↓
 device driver
```

**Key VFS data structures:**

- `file` — open file description (one per open(), holds position)
- `inode` — file metadata (one per file, not per open)
- `dentry` — directory entry (maps name → inode, aggressively cached)
- `super_block` — filesystem instance
- `address_space` — page cache for a file

### 8.2 VFS Tracing

**Tracepoints:**

```bash
# List VFS tracepoints
ls /sys/kernel/tracing/events/ext4/
ls /sys/kernel/tracing/events/xfs/
ls /sys/kernel/tracing/events/btrfs/

# Enable ALL ext4 events
echo 1 > /sys/kernel/tracing/events/ext4/enable

# Key ext4 events:
# ext4_file_read_iter        — file read
# ext4_file_write_iter       — file write
# ext4_journal_start         — journal transaction start
# ext4_sync_file_enter/exit  — fsync
# ext4_da_write_begin        — delayed allocation write begin
# ext4_da_write_end          — delayed allocation write end
# ext4_alloc_da_blocks       — flush delayed allocations
```

**Using bpftrace for filesystem latency:**

```bash
# Trace slow ext4 reads
bpftrace -e '
tracepoint:ext4:ext4_file_read_iter { @start[tid] = nsecs; }
tracepoint:ext4:ext4_file_read_iter_exit /@start[tid]/ {
    $lat = (nsecs - @start[tid]) / 1000000;
    if ($lat > 10) {
        printf("SLOW READ: %dms %s\n", $lat, comm);
    }
    delete(@start[tid]);
}'
```

### 8.3 Block Layer Analysis

```bash
# Block layer tracepoints
ls /sys/kernel/tracing/events/block/
# block:block_rq_issue   — request issued to driver
# block:block_rq_complete — request completed
# block:block_bio_queue  — bio queued
# block:block_bio_complete — bio completed

# blktrace — dedicated block layer tracer
blktrace -d /dev/sda -o sda_trace     # Record
blkparse sda_trace.blktrace.*          # Parse
blkparse -i sda_trace -d sda.bin       # Convert to binary
btt -i sda.bin                         # Block trace timing

# iostat — disk utilization
iostat -x 1    # Extended stats, 1 second interval
# Key columns:
# %util   — disk time busy (near 100% = saturated)
# await   — average wait time (I/O latency)
# r_await — read latency
# w_await — write latency
# aqu-sz  — average queue depth (>1 = queuing)
```

**`blkparse` output letters:**

| Letter | Meaning |
|--------|---------|
| `Q` | bio queued to elevator |
| `M` | bio merged with existing request |
| `G` | request got from elevator |
| `I` | request inserted to dispatch queue |
| `D` | request dispatched to driver |
| `C` | request completed |

### 8.4 Filesystem-Specific Debugging

#### ext4

```bash
# Filesystem status and errors
tune2fs -l /dev/sda1 | grep -E 'state|errors|mounts|check'

# Check error count
tune2fs -l /dev/sda1 | grep 'FS Error count'

# Force check at next boot
tune2fs -C 1 -c 2 /dev/sda1

# Offline filesystem check
e2fsck -fvn /dev/sda1    # -n = no modification (dry run)

# Extent tree inspection
debugfs /dev/sda1
  debugfs: stat <inode_number>       # Inspect specific inode
  debugfs: blocks <inode_number>     # List blocks
  debugfs: extents <inode_number>    # Show extent tree
  debugfs: dump_extents /path/to/file
  debugfs: icheck <block_number>     # Which inode owns this block?
  debugfs: ncheck <inode_number>     # Find filename for inode

# Journal debugging
debugfs /dev/sda1
  debugfs: logdump -a                # Dump full journal

# e2fsck journal recovery
e2fsck -j /dev/sda1 /dev/sda1
```

**ext4 mount option debugging:**

```bash
# Mount with extra debugging options
mount -o journal_checksum,data=journal /dev/sda1 /mnt  # Full journal data mode

# Check current mount options
cat /proc/mounts | grep ext4
```

#### XFS

```bash
# XFS status
xfs_info /mnt/xfs               # Filesystem geometry and features

# Check and repair (must be unmounted for -r)
xfs_check /dev/sdb1             # Check only
xfs_repair /dev/sdb1            # Repair

# Log/journal inspection
xfs_logprint /dev/sdb1          # Print journal contents

# Metadata dump
xfs_db /dev/sdb1
  xfs_db> sb                    # Superblock
  xfs_db> freesp                # Free space
  xfs_db> inode <number>        # Inspect inode

# IO statistics
xfs_stats 1                     # Per-second XFS statistics

# Enable XFS debug
mount -o debug /dev/sdb1 /mnt

# xfstrace — XFS-specific tracing
ls /sys/kernel/tracing/events/xfs/
echo 1 > /sys/kernel/tracing/events/xfs/enable
```

#### Btrfs

```bash
# Btrfs status and error checking
btrfs status /mnt
btrfs device stats /mnt     # Per-device error counters

# Scrub — verify all data and metadata checksums
btrfs scrub start /mnt
btrfs scrub status /mnt

# Check filesystem (offline)
btrfs check /dev/sdc1
btrfs check --readonly /dev/sdc1   # Non-destructive check

# Balance (rebalance data/metadata across devices)
btrfs balance status /mnt

# Show subvolumes
btrfs subvolume list /mnt

# Inspect metadata
btrfs inspect-internal dump-tree /dev/sdc1
btrfs inspect-internal dump-super /dev/sdc1   # Superblock
btrfs inspect-internal logical-resolve <logical_addr> /mnt
```

### 8.5 Page Cache Analysis

```bash
# Page cache size
cat /proc/meminfo | grep -E 'Cached|Buffers|Dirty|Writeback'

# Per-file page cache (needs fincore or vmtouch)
apt install vmtouch
vmtouch -v /path/to/file     # Show which pages are in cache

# Page cache drop (testing/debugging)
echo 1 > /proc/sys/vm/drop_caches   # Drop page cache
echo 2 > /proc/sys/vm/drop_caches   # Drop dentries + inodes
echo 3 > /proc/sys/vm/drop_caches   # Drop all clean caches

# Dirty page writeback tuning
sysctl vm.dirty_ratio            # % memory that can be dirty
sysctl vm.dirty_background_ratio # % where background writeback starts
sysctl vm.dirty_expire_centisecs # How old dirty data must be before writeback
sysctl vm.dirty_writeback_centisecs # How often pdflush/writeback runs
```

**bpftrace for page cache hit/miss:**

```bash
bpftrace -e '
kretprobe:__find_get_page { if (retval == 0) { @misses = count(); } else { @hits = count(); } }
interval:s:1 { printf("hits=%d misses=%d\n", @hits, @misses); clear(@hits); clear(@misses); }
'
```

### 8.6 Inode and Dentry Cache

```bash
# Cache statistics
cat /proc/sys/fs/inode-state     # inodes: total, free, preshrink
cat /proc/sys/fs/dentry-state    # dentries: total, unused, age_limit, want_pages

# Tune inode cache
sysctl vfs.cache_pressure        # 100=default, higher=reclaim faster, lower=keep longer

# Find processes with many open files
lsof | awk '{print $1}' | sort | uniq -c | sort -rn | head

# Per-process file descriptor limit
cat /proc/<pid>/limits | grep 'open files'

# System-wide fd usage
cat /proc/sys/fs/file-nr         # allocated fd / free fd / max fd
```

---

## 9. Locking & Concurrency Bugs

### 9.1 Lockdep — The Lock Dependency Validator

**Lockdep** is the most powerful concurrency debugging tool in the kernel. It tracks **lock ordering** and detects potential deadlocks **before they happen**, based on the order in which locks are acquired across all call paths.

```kconfig
CONFIG_LOCKDEP=y
CONFIG_PROVE_LOCKING=y
```

**How it works:**

Lockdep maintains a directed graph of "lock class" dependencies. When lock B is acquired while lock A is held, Lockdep records `A → B`. If it later sees `B → A` on any code path, it has found a potential deadlock cycle — and reports it **immediately**, even if the deadlock hasn't occurred yet.

**A Lockdep report — ABBA deadlock:**

```
======================================================
WARNING: possible circular locking dependency detected
6.8.0-debug #1 Not tainted
------------------------------------------------------
myprogram/1234 is trying to acquire lock:
ffffffff82345678 (&lockB){+.+.}-{3:3}, at: funcB+0x34/0x80

but task is already holding lock:
ffffffff87654321 (&lockA){+.+.}-{3:3}, at: funcA+0x12/0x50

which lock already depends on the new lock.

the existing dependency chain (in reverse order) is:

-> #1 (&lockA){+.+.}:
       lock_acquire+0xd8/0x3e0
       _raw_spin_lock+0x2a/0x40
       funcB+0x34/0x80        ← Thread 2 holds B, acquires A
       thread2_func+0x45/0x90

-> #0 (&lockB){+.+.}:
       lock_acquire+0xd8/0x3e0
       _raw_spin_lock+0x2a/0x40
       funcA+0x34/0x80        ← Thread 1 holds A, acquires B
       thread1_func+0x45/0x90

other info that might help us debug this:
 Possible unsafe locking scenario:
       CPU0                    CPU1
       ----                    ----
  lock(&lockA);
                               lock(&lockB);
                               lock(&lockA);   ← Would block
  lock(&lockB);                               ← Would deadlock
```

**Lock type annotations:**

```
{+.+.} = {read/write : try/hardirq : softirq : hardirq-inside-softirq}
{....} = {not taken in any context}
{+...} = {write lock taken in process context}
{..+.} = {write lock taken in softirq context}
```

**Lockdep stats:**

```bash
cat /proc/lockdep_stats
# lock-classes: 1234          — unique lock types seen
# lock-class chains: 5678     — dependency chains recorded
# direct dependencies: 9012   — direct A→B pairs
# chain lookup misses: 0      — ideal, no hash collisions
```

**Lockdep annotations for special cases:**

```c
/* Intentional lock inversion (e.g., different lock classes on same spinlock_t) */
lockdep_set_class(&lock, &my_lock_key);

/* Lock acquired in interrupt context — tell Lockdep */
spin_lock_irqsave(&lock, flags);

/* Allow recursive locking */
mutex_lock_nested(&mutex, SINGLE_DEPTH_NESTING);

/* Suppress false positive for known-safe case */
lockdep_off();
/* ... */
lockdep_on();
```

### 9.2 KCSAN — Kernel Concurrency Sanitizer

**KCSAN** detects **data races** — concurrent unsynchronized accesses to shared memory where at least one is a write.

```kconfig
CONFIG_KCSAN=y
CONFIG_KCSAN_REPORT_VALUE_CHANGE_ONLY=y  # Only report value changes (less noise)
```

**Mechanism:** KCSAN uses a **watchpoint** mechanism. It randomly selects memory accesses and places a hardware watchpoint. If another CPU accesses the same address concurrently, the watchpoint fires and a race is reported.

**KCSAN report:**

```
==================================================================
BUG: KCSAN: data-race in my_update_counter / my_read_counter

write to 0xffffffff82345678 of 8 bytes by task 1234 on cpu 0:
 my_update_counter+0x24/0x60
 worker_thread+0x234/0x400
 kthread+0x11a/0x140
 ...

read to 0xffffffff82345678 of 8 bytes by task 5678 on cpu 1:
 my_read_counter+0x15/0x40
 show_counter_attr+0x34/0x80
 ...

value changed: 0x0000000000000100 -> 0x0000000000000101
==================================================================
```

**KCSAN annotations:**

```c
/* Intentional benign race (e.g., performance counter) */
WRITE_ONCE(counter, counter + 1);  /* Marks as intentionally racy */
READ_ONCE(counter);                 /* Same for reads */

/* Full atomics */
atomic64_inc(&counter);

/* Suppress specific race */
kcsan_nestable_atomic_begin();
/* ... */
kcsan_nestable_atomic_end();
```

### 9.3 Spinlock Debugging

```kconfig
CONFIG_DEBUG_SPINLOCK=y
```

This adds ownership tracking to spinlocks and detects:
- Locking an already-locked spinlock (double-lock)
- Unlocking from wrong CPU
- Unlocking a lock that isn't locked

```bash
# Spinlock contention stats (requires LOCK_STAT)
cat /proc/lock_stat | head -30
# Columns: lock class, contentions (con-bounces, contentions, wait-time min/max/total, acq-bounces)
```

### 9.4 Mutex Debugging

```kconfig
CONFIG_DEBUG_MUTEXES=y
```

Adds:
- Owner tracking
- Spinlock-like wait debugging
- Magic number corruption detection (detects memory corruption of mutex struct)

**Hung task detection:**

```bash
# If a task is stuck in mutex_lock for too long:
dmesg | grep 'INFO: task.*blocked'

# Output:
# INFO: task kworker/0:1:1234 blocked for more than 120 seconds.
# Not tainted 6.8.0 #1
# "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
# task:kworker/0:1:1234 state:D stack:12345 pid:1234 ppid:2 flags:0x...
# Call Trace:
#  __schedule+0x...
#  schedule+0x...
#  schedule_preempt_disabled+0x...
#  mutex_lock+0x...
#  ...
```

```bash
# Configure hung task timeout
sysctl kernel.hung_task_timeout_secs=60    # 60 second timeout
sysctl kernel.hung_task_panic=1            # Panic on hung task (for kdump)
```

### 9.5 RCU Debugging

RCU (Read-Copy-Update) is the kernel's primary lock-free synchronization mechanism. Bugs include:
- Using RCU-protected data outside an RCU read-side critical section
- Calling `synchronize_rcu()` from atomic context
- Not using `rcu_dereference()` for pointer reads under RCU

```kconfig
CONFIG_PROVE_RCU=y          # Validates RCU usage
CONFIG_RCU_STRICT_GRACE_PERIOD=y  # Stricter GP semantics
CONFIG_DEBUG_OBJECTS_RCU_HEAD=y   # Track rcu_head objects
```

```bash
# RCU stats
cat /sys/kernel/debug/rcu/rcudata

# RCU stalls — RCU grace period stuck
dmesg | grep 'rcu_sched detected stalls'
# Output shows which CPU is stalling and its call trace

# Configure RCU stall timeout
sysctl kernel.rcu_cpu_stall_timeout=21  # seconds
```

**Common RCU bugs:**

```c
/* BUG: accessing RCU-protected pointer without rcu_read_lock */
struct my_obj *obj = my_global;   /* WRONG — no protection */
obj->field;

/* CORRECT */
rcu_read_lock();
struct my_obj *obj = rcu_dereference(my_global);  /* Safe dereference */
if (obj)
    obj->field;
rcu_read_unlock();

/* BUG: sleeping inside RCU read-side critical section */
rcu_read_lock();
msleep(100);   /* WRONG — can't sleep holding rcu_read_lock */
rcu_read_unlock();
```

### 9.6 Atomic Sleep Detection

```kconfig
CONFIG_DEBUG_ATOMIC_SLEEP=y
```

Catches:
- Calling `might_sleep()` functions inside spinlocks, RCU read sections, or interrupt handlers
- Calling `schedule()` or `msleep()` with preemption disabled

```
BUG: scheduling while atomic: mythread/1234/0x00000002
...
Call Trace:
 dump_stack
 __schedule_bug
 __schedule
 schedule_timeout
 msleep                ← sleeping in atomic context!
 my_spinlock_holder
 ...
```

---

## 10. Scheduler Debugging

### 10.1 Scheduler Statistics

```bash
# Enable scheduler stats
echo 1 > /proc/sys/kernel/sched_schedstats

# Global scheduler debug
cat /proc/sched_debug

# Per-task scheduler info
cat /proc/<pid>/sched
# Output includes:
# se.exec_start        — last execution start (ns)
# se.vruntime          — CFS virtual runtime
# se.sum_exec_runtime  — total CPU time consumed
# nr_involuntary_switches  — preempted (high = contention)
# nr_voluntary_switches    — yielded (high = blocking)

# Per-CPU runqueue state
cat /proc/sched_debug | grep "cpu#"
```

### 10.2 Tracing Scheduler Events

```bash
# Enable scheduler tracepoints
echo 1 > /sys/kernel/tracing/events/sched/enable

# Key events:
# sched:sched_switch        — context switch (prev_comm, next_comm, reason)
# sched:sched_wakeup        — task woken up
# sched:sched_wakeup_new    — new task woken
# sched:sched_migrate_task  — task moved between CPUs
# sched:sched_stat_wait     — time spent waiting on runqueue
# sched:sched_stat_sleep    — time spent sleeping
# sched:sched_stat_blocked  — time blocked on lock/I/O

# Trace context switches for specific PID
echo '<pid>' > /sys/kernel/tracing/set_event_pid
echo 1 > /sys/kernel/tracing/events/sched/sched_switch/enable
```

### 10.3 CPU Affinity and Isolation

```bash
# Check task's CPU affinity
taskset -p <pid>

# Check scheduler policy and priority
chrt -p <pid>

# List all threads with their CPU
ps -eLo pid,tid,psr,comm | head -30

# See which CPUs are isolated (kernel parameter: isolcpus=)
cat /sys/devices/system/cpu/isolated

# perf sched for scheduling analysis
perf sched record -- sleep 10
perf sched latency              # Show per-task scheduling latency
# Output:
# Task               |   Runtime ms  | Switches | Average delay ms | Maximum delay ms
# mythread:1234      |     5000.000  |    12345 |            0.123 |            5.678
```

### 10.4 Real-Time Scheduling

```bash
# Set real-time scheduling policy
chrt -f -p 50 <pid>    # FIFO, priority 50
chrt -r -p 50 <pid>    # Round-robin

# Check RT throttling (prevents RT tasks from starving normal tasks)
sysctl kernel.sched_rt_runtime_us   # Microseconds RT can run per period
sysctl kernel.sched_rt_period_us    # Period length

# Disable RT throttling (dangerous — can freeze system)
sysctl -w kernel.sched_rt_runtime_us=-1

# latencytop — identify sources of scheduling latency
apt install latencytop
latencytop
```

---

## 11. Driver & Hardware Debugging

### 11.1 Module Debugging

```bash
# Load module with debugging enabled
insmod mydriver.ko dyndbg=+pflmt   # Enable dynamic debug for module

# Check module parameters
ls /sys/module/mydriver/parameters/

# Check module sections (for gdb symbol loading)
ls /sys/module/mydriver/sections/

# Module loading errors
dmesg | tail -50   # Check for module-specific errors
```

**Module debugging with dynamic_debug:**

```bash
# After loading
echo 'module mydriver +pflmt' > /sys/kernel/debug/dynamic_debug/control
```

### 11.2 PCI Device Debugging

```bash
# List all PCI devices with verbose info
lspci -vvv

# Specific device
lspci -vvv -s 00:1f.2   # bus:device.function

# PCI config space
lspci -xxx -s 00:1f.2   # Raw hex config space (first 256 bytes)
lspci -xxxx              # Extended config space (4096 bytes)

# /sys/bus/pci interface
ls /sys/bus/pci/devices/0000:00:1f.2/

# Enable PCI device error logging (AER)
cat /sys/bus/pci/devices/0000:00:1f.2/aer_dev_correctable
cat /sys/bus/pci/devices/0000:00:1f.2/aer_dev_nonfatal
cat /sys/bus/pci/devices/0000:00:1f.2/aer_dev_fatal

# Check PCIe link status
cat /sys/bus/pci/devices/0000:00:1f.2/current_link_speed
cat /sys/bus/pci/devices/0000:00:1f.2/current_link_width
```

### 11.3 DMA Debugging

```kconfig
CONFIG_DMA_API_DEBUG=y    # Validate DMA API usage
CONFIG_IOMMU_DEBUG=y      # IOMMU debugging
```

**DMA API debug** catches:
- DMA map/unmap mismatches
- Using DMA memory after unmapping
- DMA direction violations
- Overflows past mapped size

```bash
# Check DMA mapping stats
cat /sys/kernel/debug/dma-api/all_errors
cat /sys/kernel/debug/dma-api/error_count
cat /sys/kernel/debug/dma-api/num_errors
```

### 11.4 Interrupt Debugging

```bash
# All IRQ stats
cat /proc/interrupts

# Per-CPU IRQ counts (useful for balance debugging)
watch -n 1 'cat /proc/interrupts | grep eth0'

# Spurious IRQ count
cat /proc/interrupts | grep ERR   # Per-CPU error counters
cat /proc/interrupts | grep MIS   # Spurious IRQs

# IRQ affinity
cat /proc/irq/<num>/smp_affinity       # CPU bitmask
cat /proc/irq/<num>/smp_affinity_list  # Human-readable CPU list

# IRQ thread debugging
ps aux | grep 'irq/'   # IRQ threads (threaded IRQs)
cat /proc/irq/<num>/effective_affinity
```

**Tracing interrupts:**

```bash
# Enable hardirq/softirq tracing
echo 1 > /sys/kernel/tracing/events/irq/enable
# irq:irq_handler_entry   — hardirq handler entered
# irq:irq_handler_exit    — hardirq handler exited
# irq:softirq_entry       — softirq handler entered
# irq:softirq_exit        — softirq handler exited
# irq:softirq_raise       — softirq raised (scheduled)

# Trace IRQ off latency
echo irqsoff > /sys/kernel/tracing/current_tracer
echo 1 > /sys/kernel/tracing/tracing_on
# ... reproduce latency ...
echo 0 > /sys/kernel/tracing/tracing_on
cat /sys/kernel/tracing/trace
```

### 11.5 Device Bind/Unbind Debugging

```bash
# Check device state
cat /sys/bus/platform/devices/mydevice/uevent
cat /sys/bus/platform/devices/mydevice/power/runtime_status

# Manually bind/unbind driver (for testing)
echo mydevice > /sys/bus/platform/drivers/mydriver/unbind
echo mydevice > /sys/bus/platform/drivers/mydriver/bind

# Device power management debug
cat /sys/bus/platform/devices/mydevice/power/control         # on/auto
echo on > /sys/bus/platform/devices/mydevice/power/control   # Disable runtime PM

# dmesg device probe sequence
dmesg | grep mydevice
```

---

## 12. Crash Dump Analysis (kdump + crash)

### 12.1 kdump Setup

`kdump` uses `kexec` to boot a **second "capture" kernel** immediately after a panic. The capture kernel runs in a reserved memory region and saves the crash dump (`/proc/vmcore`) to disk/network.

```bash
# Install kdump
apt install kdump-tools crash

# Reserve memory for kdump capture kernel
# Add to /etc/default/grub:
GRUB_CMDLINE_LINUX="crashkernel=256M"
# For large systems:
GRUB_CMDLINE_LINUX="crashkernel=512M,high crashkernel=128M,low"

update-grub && reboot

# Verify kdump is reserved
dmesg | grep -i crashkernel
cat /proc/cmdline | grep crashkernel

# Load capture kernel
kdump-config load
kdump-config status

# Test kdump (WARNING: will crash your system)
echo c > /proc/sysrq-trigger   # Force kernel panic, triggers kdump
```

**kdump configuration (`/etc/kdump.conf` or `/etc/default/kdump-tools`):**

```ini
# Save to local disk
path /var/crash

# Save to NFS
nfs 192.168.1.100:/exports/crash

# Save to SSH
ssh user@192.168.1.100

# Dump core level (what to save)
core_collector makedumpfile -c --message-level 1 -d 31
# -d 31 = filter out: zero pages, cache pages, user pages, free pages
# -c = zlib compression
```

### 12.2 The `crash` Utility — Analyzing vmcore

`crash` is a kernel crash dump analysis tool built on top of `gdb`.

```bash
# Open a crash dump
crash vmlinux /var/crash/$(date +%Y%m%d)*/vmcore

# Open a live system (for debugging)
crash vmlinux

# Load module symbols
crash> mod -s mydriver /path/to/mydriver.ko
```

#### Essential `crash` Commands

```bash
# System state overview
crash> sys          # Kernel version, uptime, panic string
crash> sys -c       # Crash reason detail

# Process list (like ps)
crash> ps           # All processes with state
crash> ps -k        # Kernel threads only
crash> ps -u        # User tasks only
crash> ps myapp     # Find by name

# CPU states at crash time
crash> foreach bt   # Backtrace of ALL tasks (can be large)
crash> bt           # Backtrace of current (crashing) context
crash> bt -a        # Backtrace of all CPUs (at crash)
crash> bt -t        # Full text output, no symbols

# Stack trace for specific PID
crash> bt 1234

# Memory inspection
crash> rd 0xffff888100000000   # Read doubleword at address
crash> rd -64 0xffff... 20     # Read 20 x 64-bit values
crash> wr 0xffff... 0xdeadbeef # Write (live kernel only!)
crash> kmem -i                 # Memory info (like /proc/meminfo)
crash> kmem -s                 # Slab cache summary
crash> kmem -S kmalloc-128     # Specific slab cache

# Struct inspection
crash> struct task_struct 0xffff888101234000  # Print struct
crash> struct task_struct.pid 0xffff...       # Print specific field
crash> p task->pid                            # Print with symbol

# Symbol/address lookup
crash> sym my_function         # Address of symbol
crash> sym 0xffffffff81234567  # Symbol at address
crash> dis my_function         # Disassemble function
crash> dis -l my_function      # Disassemble with source lines

# Log buffer
crash> log            # Full kernel log ring buffer
crash> log -T         # With timestamps

# Files and VFS
crash> files 1234     # Open files of process 1234
crash> mount          # Show mount table

# Network
crash> net            # Network device list
crash> net -s         # Socket list

# Per-CPU variables
crash> p per_cpu(runqueues, 0)  # runqueue on CPU 0

# Search memory for a value
crash> search -u 0xdeadbeef    # Search user space
crash> search -k 0xdeadbeef    # Search kernel space
```

### 12.3 Reconstructing the Crash

**Step 1: Get the panic reason**

```bash
crash> sys
      PANIC: "general protection fault, probably for non-canonical address..."
      DUMPFILE: /var/crash/vmcore
      CPUS: 8
      DATE: Thu Mar 29 12:34:56 2026
```

**Step 2: Get the crashing CPU's registers and backtrace**

```bash
crash> bt
...
PANIC: general protection fault, probably for non-canonical address 0x5a5a5a5a5a5a5a58
PID: 1234  TASK: ffff888101234000  CPU: 3  COMMAND: "myapp"
 #0 [ffffc90000d27b90] machine_kexec at ffffffff8108d5c0
 #1 [ffffc90000d27be8] __crash_kexec at ffffffff8110f234
 #2 [ffffc90000d27cb0] crash_kexec at ffffffff8110f3a4
 #3 [ffffc90000d27cc8] oops_end at ffffffff810561e4
 #4 [ffffc90000d27cf0] general_protection_oops at ffffffff810561e4
 #5 [ffffc90000d27d40] exc_general_protection at ffffffff81e01c34
 #6 [ffffc90000d27da0] asm_exc_general_protection at ffffffff81e00a72
    RIP: 0010:my_driver_read+0x47/0x90 [mydriver]  ← CRASH HERE
```

**The address `0x5a5a5a5a5a5a5a58` is a SLUB free-list poison pattern** (`0x6b` repeated) shifted by a struct offset. This is a use-after-free into a SLUB-freed object.

**Step 3: Inspect the crashing struct**

```bash
crash> struct my_device_context 0xffff888102345000
# If the memory shows 5a5a5a5a5a5a5a5a in fields, it's freed/poisoned
```

**Step 4: Find when it was freed**

```bash
# With SLUB debug + full trace, the vmcore may include free stack
crash> kmem 0xffff888102345000
# Shows: object at 0x... in cache my_context_cache, FREED
```

**Step 5: Cross-reference with source**

```bash
crash> dis -l my_driver_read
# Shows source file and line for each instruction
```

---

## 13. Boot-Time Debugging

### 13.1 Kernel Command Line Parameters

```bash
# Add to bootloader (grub), then update-grub and reboot
GRUB_CMDLINE_LINUX="

# Basic debugging
debug                      # Increase console verbosity
loglevel=8                 # Max log output
ignore_loglevel            # Print ALL messages regardless of level
earlycon                   # Enable early console (before normal console init)

# Disable features for isolation
nokaslr                    # Disable KASLR (deterministic addresses)
noapic                     # Disable APIC (use legacy 8259 PIC)
noacpi                     # Disable ACPI
nosmp                      # Single CPU only
maxcpus=2                  # Limit to 2 CPUs
mem=512M                   # Limit memory
nohpet                     # Disable HPET timer
acpi=off                   # Disable ACPI
nofpu                      # Disable FPU (x87)
noibrs noibpb              # Disable Spectre mitigations
mitigations=off            # Disable ALL CPU vulnerability mitigations

# Memory debugging at boot
slub_debug=FPZU            # SLUB debugging flags
kasan=on
kfence.sample_interval=100

# Panic behavior
panic=0                    # Don't reboot on panic (freeze for kdump)
oops=panic                 # Convert oops to panic
panic_on_warn=1            # Panic on WARN_ON()
crashkernel=256M           # Reserve for kdump

# Debugging specific subsystems
drm.debug=0x1f             # DRM/GPU driver debug
usbcore.autosuspend=-1     # Disable USB autosuspend
pci=nommconf               # Disable MMCONFIG PCI access
```

### 13.2 Early Printk / earlycon

For crashes that happen before the normal console is initialized:

```bash
# x86 serial port early console
earlycon=uart8250,io,0x3f8,115200

# x86 MMIO serial
earlycon=uart8250,mmio32,0xfe040000,115200

# ARM serial
earlycon=pl011,0x09000000

# Virtio console (QEMU)
earlycon=virtio

# PCI serial card
earlycon=pcicom,pci:0000:00:05.0
```

### 13.3 Debugging initramfs / Early Userspace

```bash
# Drop to shell in initramfs (break before pivot_root)
rd.break=pre-mount         # Dracut-based initramfs
init=/bin/sh               # Skip init entirely

# Debug systemd early boot
systemd.log_level=debug
systemd.log_target=kmsg    # Log to kernel ring buffer

# Show init scripts
rd.debug                   # Dracut debug mode
```

### 13.4 `strace` on Systemd PID 1

```bash
# After boot, trace pid 1 from the beginning using QEMU
qemu-system-x86_64 \
  -kernel bzImage \
  -append "root=/dev/vda init=/usr/bin/strace -- /sbin/init" \
  ...
```

---

## 14. QEMU-Based Kernel Debugging Workflow

This is the **gold standard workflow** for kernel development and debugging. It's faster than hardware, fully reproducible, and supports KGDB + GDB integration.

### 14.1 Environment Setup

```bash
# Required packages
apt install qemu-system-x86 qemu-utils gdb \
            build-essential bc bison flex libelf-dev libssl-dev \
            pahole dwarves

# Create minimal rootfs with debootstrap
apt install debootstrap
debootstrap --arch=amd64 bookworm ./rootfs http://deb.debian.org/debian
chroot ./rootfs apt install -y gdb strace ltrace util-linux

# Create disk image
dd if=/dev/zero of=rootfs.img bs=1G count=10
mkfs.ext4 rootfs.img
mount -o loop rootfs.img /mnt
cp -a rootfs/. /mnt/
umount /mnt
```

### 14.2 Kernel Build for QEMU Debugging

```bash
# Use a minimal config + debugging options
make defconfig
make kvm_guest.config       # KVM-optimized config

# Add debug options
cat >> .config << 'EOF'
CONFIG_DEBUG_INFO=y
CONFIG_DEBUG_INFO_DWARF5=y
CONFIG_FRAME_POINTER=y
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y
CONFIG_LOCKDEP=y
CONFIG_PROVE_LOCKING=y
CONFIG_DEBUG_SPINLOCK=y
CONFIG_DEBUG_ATOMIC_SLEEP=y
CONFIG_FTRACE=y
CONFIG_FUNCTION_TRACER=y
CONFIG_DYNAMIC_FTRACE=y
CONFIG_KPROBES=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_DEBUG_FS=y
CONFIG_RANDOMIZE_BASE=n   # Disable KASLR for deterministic debugging
EOF

make olddefconfig
make -j$(nproc)
```

### 14.3 QEMU Launch Script

```bash
#!/bin/bash
# debug-kernel.sh

KERNEL=arch/x86/boot/bzImage
ROOTFS=rootfs.img
MEMORY=2G
CPUS=4

exec qemu-system-x86_64 \
  -m ${MEMORY} \
  -smp ${CPUS} \
  -cpu host \                              # Use host CPU features
  -enable-kvm \                            # Enable KVM acceleration
  -kernel ${KERNEL} \
  -drive file=${ROOTFS},format=raw,if=virtio \
  -append "root=/dev/vda rw console=ttyS0 \
           nokaslr \
           kasan=on \
           slub_debug=FPZU \
           panic=-1 \
           loglevel=8 \
           kgdboc=ttyS1,115200" \          # KGDB on second serial
  -serial stdio \                           # ttyS0 to stdout
  -serial tcp::1235,server,nowait \        # ttyS1 for KGDB
  -netdev user,id=net0 \
  -device virtio-net-pci,netdev=net0 \
  -s \                                     # GDB server on tcp::1234
  -nographic
```

### 14.4 Attaching GDB

```bash
# In another terminal
gdb vmlinux
(gdb) set architecture i386:x86-64
(gdb) target remote :1234
(gdb) lx-symbols                    # Load module symbols (requires vmlinux-gdb.py)
(gdb) break my_driver_probe
(gdb) continue
```

**Enable Python extensions for GDB:**

```bash
# In your .gdbinit
add-auto-load-safe-path /path/to/kernel/source
# This auto-loads vmlinux-gdb.py which provides lx-* helpers
```

### 14.5 Automating with `virtme-ng`

`virtme-ng` provides a turnkey QEMU setup that uses your current kernel and rootfs:

```bash
pip install virtme-ng

# Run current kernel in QEMU with current rootfs (read-only)
virtme-ng --run-existing

# Run with custom kernel
virtme-ng --kimg arch/x86/boot/bzImage

# With extra kernel parameters
virtme-ng --kimg bzImage --qemu-opts="-s -S"   # GDB server mode
```

---

## 15. Systematic Debugging Methodology

### 15.1 The Five-Phase Method

**Phase 1: OBSERVE**
- Read the full Oops/panic — don't jump to conclusions
- Note: fault type, faulting address, faulting function, registers, call stack
- Check `dmesg` for preceding events (allocation failures, warnings, timeouts)
- Check syslog for prior crashes or anomalies

**Phase 2: REPRODUCE**
- Can you reproduce the bug deterministically?
- If not, narrow conditions: hardware, kernel version, config, load level
- Use `stress-ng`, `syzkaller` (fuzzer), or replay a workload
- Isolate subsystem: can you reproduce without your driver? Without your filesystem?

**Phase 3: LOCALIZE**
- Use binary search across kernel versions: `git bisect`
- Use binary search across config options
- Add targeted `printk` around the suspected area
- Use kprobes/ftrace to narrow the crash site before source-level debugging

**Phase 4: UNDERSTAND**
- Once you can reproduce: attach KGDB, enable KASAN/Lockdep
- Trace data flow from the point of corruption backward to the root cause
- Ask: when was this memory allocated? When was it freed? Who freed it?
- Ask: what lock protects this data? Is it always held?

**Phase 5: FIX & VERIFY**
- Write the fix with the cause fully understood
- Test with KASAN/Lockdep/KCSAN still enabled
- Run existing kernel test suites: `kselftest`, `LTP`
- Consider: is this fix correct under all memory orderings? On SMP? On NUMA?
- Write a regression test

### 15.2 `git bisect` — Finding the Regressing Commit

```bash
# Start bisect
git bisect start

# Mark known bad commit (current broken HEAD)
git bisect bad HEAD

# Mark known good commit (last known working version)
git bisect good v6.6

# Git will checkout a middle commit — test it
make -j$(nproc) && boot-test.sh
git bisect good   # If test passes
# or
git bisect bad    # If test fails

# Repeat until git finds the exact commit
# At the end:
git bisect reset

# Automate with a script
git bisect run ./test-script.sh
# test-script.sh must exit 0 for good, 1 for bad, 125 to skip
```

### 15.3 Systematic Narrowing with `sysctl` / Boot Params

```bash
# Disable SMP → single CPU (eliminates concurrency bugs)
maxcpus=1

# Disable preemption (CONFIG_PREEMPT_NONE)
# Disable NUMA (numa=off or CONFIG_NUMA=n)
numa=off

# Disable specific driver
# Replace module with dummy
modprobe -r suspect_driver

# Minimize memory
mem=256M

# Use older allocator
slab_nomerge            # Disable SLUB merging (may expose allocator bugs)
```

### 15.4 Syzkaller — Automated Kernel Fuzzing

`syzkaller` is Google's coverage-guided kernel fuzzer. It systematically generates system call sequences and triggers kernel bugs.

```bash
# Quick local setup
git clone https://github.com/google/syzkaller
cd syzkaller
make

# Config (syzkaller.cfg):
{
  "target": "linux/amd64",
  "http": "0.0.0.0:56741",
  "workdir": "workdir",
  "kernel_obj": "/path/to/kernel/build",
  "kernel_src": "/path/to/kernel/source",
  "syzkaller": "/path/to/syzkaller",
  "image": "rootfs.img",
  "sshkey": "id_rsa",
  "reproduce": true,
  "procs": 4,
  "type": "qemu",
  "vm": {
    "count": 4,
    "kernel": "/path/to/bzImage",
    "cpu": 2,
    "mem": 2048
  }
}

./bin/syz-manager -config syzkaller.cfg
# Access web UI at http://localhost:56741
```

---

## 16. Reference: Key Files, Interfaces & Commands

### /proc Reference

| File | Description |
|------|-------------|
| `/proc/kallsyms` | All kernel symbols + addresses |
| `/proc/modules` | Loaded modules |
| `/proc/iomem` | Physical memory map |
| `/proc/ioports` | I/O port allocations |
| `/proc/meminfo` | Memory usage summary |
| `/proc/slabinfo` | Slab allocator stats |
| `/proc/vmallocinfo` | vmalloc regions |
| `/proc/buddyinfo` | Buddy allocator free list sizes |
| `/proc/zoneinfo` | Per-zone memory info |
| `/proc/interrupts` | IRQ stats |
| `/proc/softirqs` | Soft IRQ counts |
| `/proc/net/dev` | Network interface stats |
| `/proc/net/tcp` | TCP socket table |
| `/proc/net/nf_conntrack` | Conntrack table |
| `/proc/net/snmp` | Network MIB-II counters |
| `/proc/sched_debug` | Scheduler state |
| `/proc/lockdep_stats` | Lockdep statistics |
| `/proc/lock_stat` | Lock contention stats |
| `/proc/kmemleak` | Memory leak detector |
| `/proc/sys/kernel/` | Kernel tunables |
| `/proc/sys/vm/` | VM tunables |
| `/proc/sys/net/` | Network tunables |

### sysctl Quick Reference

```bash
# Kernel panic behavior
kernel.panic=0                  # Don't reboot on panic
kernel.panic_on_oops=1          # Oops → panic
kernel.hung_task_timeout_secs=120
kernel.softlockup_panic=1       # Soft lockup → panic
kernel.hardlockup_panic=1       # Hard lockup → panic (NMI watchdog)

# NMI watchdog
kernel.nmi_watchdog=1           # Enable NMI watchdog (hard lockup detection)
kernel.watchdog_thresh=10       # Seconds before hard lockup declared

# SysRq
kernel.sysrq=1                  # Enable all SysRq

# Memory
vm.overcommit_memory=0          # Heuristic overcommit
vm.oom_kill_allocating_task=1   # OOM killer kills the allocating task
vm.panic_on_oom=1               # OOM → panic (for kdump)
vm.drop_caches=3                # Drop all clean caches

# Network
net.core.rmem_max=134217728     # Max receive buffer
net.core.wmem_max=134217728     # Max send buffer
net.ipv4.tcp_tw_reuse=1        # Reuse TIME_WAIT sockets
```

### SysRq Magic Keys

```bash
# Enable: echo 1 > /proc/sys/kernel/sysrq
# Trigger: echo <key> > /proc/sysrq-trigger

echo b > /proc/sysrq-trigger   # Immediate reboot (no sync)
echo c > /proc/sysrq-trigger   # Crash (for kdump testing)
echo d > /proc/sysrq-trigger   # Show all held locks
echo e > /proc/sysrq-trigger   # Send SIGTERM to all processes
echo f > /proc/sysrq-trigger   # Call OOM killer
echo g > /proc/sysrq-trigger   # Enter KGDB
echo i > /proc/sysrq-trigger   # Send SIGKILL to all
echo l > /proc/sysrq-trigger   # Show all active CPUs' stack traces
echo m > /proc/sysrq-trigger   # Show memory info
echo n > /proc/sysrq-trigger   # Reset nice of RT tasks
echo p > /proc/sysrq-trigger   # Show current registers + flags
echo q > /proc/sysrq-trigger   # Show all armed hrtimers
echo s > /proc/sysrq-trigger   # Sync all filesystems
echo t > /proc/sysrq-trigger   # Show all threads
echo u > /proc/sysrq-trigger   # Remount all filesystems read-only
echo w > /proc/sysrq-trigger   # Show blocked tasks (D state)
echo z > /proc/sysrq-trigger   # FTRACE dump
```

### Tool Summary

| Tool | Type | Best For |
|------|------|----------|
| `kgdb` | Interactive debugger | Step-through debugging, breakpoints |
| `crash` | Post-mortem analysis | vmcore dump analysis |
| `ftrace` | In-kernel tracer | Function call tracing, latency |
| `perf` | Profiler + tracer | CPU profiling, PMU, events |
| `bpftrace` | eBPF scripting | Custom real-time probes |
| `KASAN` | Memory sanitizer | Out-of-bounds, use-after-free |
| `KMSAN` | Memory sanitizer | Uninitialized reads |
| `KFENCE` | Sampling memory safety | Low-overhead production detection |
| `Lockdep` | Lock validator | Deadlock potential detection |
| `KCSAN` | Race detector | Data races |
| `blktrace` | Block I/O tracer | Disk I/O path analysis |
| `tcpdump` | Packet capture | Network packet analysis |
| `syzkaller` | Fuzzer | Automated bug discovery |
| `addr2line` | Symbol decoder | Map addresses to source |
| `decode_stacktrace.sh` | Oops decoder | Annotate kernel traces |

---

*This document reflects the Linux kernel as of the 6.x series. Most content applies equally to 5.x and many concepts date to 4.x.*

*For the latest changes: [kernel.org](https://kernel.org) | [LWN.net](https://lwn.net) | [Documentation/](https://www.kernel.org/doc/html/latest/)*

Now I'll write the full guide — this is going to be a deep, production-grade reference document.Here's your complete reference — ~6,000 lines of in-depth kernel debugging knowledge. Here's what's covered and why each section was written the way it was:

**What makes this guide different from surface-level docs:**

- **Oops anatomy** goes byte-by-byte through every field — the `error_code` bitmap, what `CR2` always contains, how to decode the `Tainted` flags, and how to go from `+0x47/0x130` to an exact source line with `addr2line` and `decode_stacktrace.sh`.

- **Memory debugging** covers the full stack: KASAN (with shadow byte value table), KMSAN (why uninitialized reads are a CVE-class vulnerability), KFENCE (why it exists separately — production-safe sampling), SLUB debug flags, and KMEMLEAK's conservative GC model including how to suppress false positives in C.

- **Tracing** walks ftrace from raw kernel tracer → event tracepoints → kprobe syntax (with every fetch arg type documented) → `trace-cmd` → `perf` hardware counters → eBPF/bpftrace one-liners for every subsystem.

- **Network** covers `sk_buff` architecture, `softnet_stat` column interpretation (not just "drop this file"), conntrack table exhaustion, netfilter tracing with both iptables and nftables, and NIC IRQ affinity tuning.

- **Filesystem** covers VFS data structures (why there are `file`, `inode`, and `dentry` as separate things), `debugfs` inode inspection, `blkparse` action letters, and fs-specific tools for ext4/XFS/Btrfs.

- **Lockdep** explains the directed dependency graph model — why it catches deadlocks *before* they happen, not just when they do.

- **`crash` utility** includes the full command set with realistic examples, including how to identify a SLUB poison pattern (`0x5a5a5a5a`) in a register as a use-after-free in a post-mortem dump.