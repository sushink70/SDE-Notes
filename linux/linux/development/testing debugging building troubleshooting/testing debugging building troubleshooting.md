# Linux Kernel Development: Complete Mastery Guide
## Testing · Debugging · Building · Troubleshooting

> *"The kernel is not magic — it is engineering made rigorous. Master the tools, master the craft."*

---

## Table of Contents

1. [Mental Model: How to Think Like a Kernel Developer](#1-mental-model)
2. [Linux Kernel Architecture — Deep Overview](#2-kernel-architecture)
3. [Kernel Source Tree Anatomy](#3-source-tree)
4. [Build System: Kbuild, Kconfig, Makefiles](#4-build-system)
5. [Kernel Configuration Mastery](#5-kernel-configuration)
6. [Compilation Pipeline](#6-compilation-pipeline)
7. [The Master Decision Tree: What to Do After a Change](#7-master-decision-tree)
8. [QEMU: Lightweight Fast Testing](#8-qemu-testing)
9. [initramfs: Building a Minimal Root Filesystem](#9-initramfs)
10. [QEMU + Full Debian Userspace](#10-qemu-debian)
11. [GDB Kernel Debugging with QEMU](#11-gdb-debugging)
12. [Cross-Compilation for ARM / Raspberry Pi 4B](#12-cross-compilation)
13. [VMware Workstation: Driver Testing](#13-vmware-testing)
14. [Kernel Modules: Build, Load, Unload](#14-kernel-modules)
15. [Rust in the Linux Kernel](#15-rust-kernel)
16. [printk and Logging System](#16-printk-logging)
17. [Dynamic Debug](#17-dynamic-debug)
18. [ftrace: Function Tracer](#18-ftrace)
19. [kprobes and kretprobes](#19-kprobes)
20. [eBPF for Kernel Observation](#20-ebpf)
21. [KASAN: Kernel Address Sanitizer](#21-kasan)
22. [KFENCE: Kernel Electric Fence](#22-kfence)
23. [KCSAN: Kernel Concurrency Sanitizer](#23-kcsan)
24. [UBSAN: Undefined Behavior Sanitizer](#24-ubsan)
25. [Lockdep: Lock Dependency Validator](#25-lockdep)
26. [RCU: Read-Copy-Update](#26-rcu)
27. [Oops, Panic, and BUG() Analysis](#27-oops-panic)
28. [dmesg: Reading the Kernel Ring Buffer](#28-dmesg)
29. [sysfs, procfs, and debugfs](#29-virtual-filesystems)
30. [perf: Performance Analysis](#30-perf)
31. [Crash Dump Analysis with kdump + crash](#31-kdump-crash)
32. [Tracing with trace-cmd and kernelshark](#32-trace-cmd)
33. [Kernel Testing Frameworks: KUnit and kselftest](#33-kunit-kselftest)
34. [Syzkaller: Kernel Fuzzing](#34-syzkaller)
35. [Submitting Patches: The Kernel Workflow](#35-patch-workflow)
36. [Cognitive Strategies for Kernel Mastery](#36-cognitive-strategies)

---

## 1. Mental Model: How to Think Like a Kernel Developer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE KERNEL DEVELOPER'S MINDSET                           │
│                                                                             │
│   USER SPACE         │         KERNEL SPACE                                 │
│   (Your App)         │         (The Kernel)                                 │
│                      │                                                      │
│   "I want file.txt"  │  ← syscall → VFS → ext4 driver → block layer        │
│   "I want memory"    │  ← mmap/brk → memory manager → page allocator       │
│   "I want network"   │  ← socket() → net stack → NIC driver → hardware     │
│                      │                                                      │
│   YOU CONTROL        │  YOU NOW CONTROL THIS SIDE                           │
│   behavior           │  correctness, performance, safety, hardware          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Four Laws of Kernel Development

```
LAW 1: No Safety Net
        ┌──────────┐     User Space: segfault → process dies, OS survives
        │ CRASH =  │     Kernel Space: NULL deref → ENTIRE SYSTEM dies
        │ MACHINE  │     One bug kills ALL processes. No exceptions.
        │ DIES     │
        └──────────┘

LAW 2: No Blocking in Interrupt Context
        Hardware IRQ fires → ISR runs → CANNOT sleep/block/schedule
        Violating this = deadlock or SYSTEM FREEZE

LAW 3: Memory Ownership is Explicit
        kmalloc() → you own it → you MUST kfree() it
        No garbage collector. No RAII (in C). No mercy.

LAW 4: Concurrency is Everywhere
        Multiple CPUs run kernel code SIMULTANEOUSLY
        Interrupts can preempt your code AT ANY INSTRUCTION
        Spinlocks, mutexes, RCU — you choose, you own the bugs
```

### Mental Model: The Privilege Ring

```
        Ring 3 (User Space)
       ┌──────────────────────────────────┐
       │  bash, vim, your_program.exe     │  ← Can only do safe things
       │  Cannot touch hardware directly  │  ← Must ask kernel via syscall
       └──────────────────┬───────────────┘
                          │ syscall (int 0x80 / syscall instruction)
       ┌──────────────────▼───────────────┐
       │  Ring 0 (Kernel Space)           │  ← Absolute power
       │  Kernel code runs here           │  ← One mistake = system crash
       │  Direct hardware access          │  ← You are God, be humble
       └──────────────────────────────────┘
```

---

## 2. Linux Kernel Architecture — Deep Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        LINUX KERNEL ARCHITECTURE                             │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Process   │  │  Memory    │  │  Virtual   │  │  Network   │            │
│  │  Scheduler │  │  Manager   │  │  FS (VFS)  │  │  Stack     │            │
│  │  (CFS,RT)  │  │  (VMM)     │  │            │  │  (TCP/IP)  │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │               │               │               │                    │
│  ┌─────▼───────────────▼───────────────▼───────────────▼──────┐             │
│  │                    SYSTEM CALL INTERFACE                     │             │
│  │  read() write() open() fork() mmap() socket() ioctl()...   │             │
│  └─────────────────────────────────────────────────────────────┘             │
│        │               │               │               │                    │
│  ┌─────▼──────┐  ┌─────▼──────┐  ┌────▼───────┐  ┌───▼────────┐            │
│  │  Device    │  │  Block     │  │  Char      │  │  Net       │            │
│  │  Drivers   │  │  Layer     │  │  Devices   │  │  Drivers   │            │
│  └─────┬──────┘  └─────┬──────┘  └────┬───────┘  └───┬────────┘            │
│        │               │               │               │                    │
│  ┌─────▼───────────────▼───────────────▼───────────────▼──────┐             │
│  │                       HARDWARE                              │             │
│  │  CPU  │  RAM  │  Disk  │  NIC  │  GPU  │  USB  │  I2C/SPI │             │
│  └─────────────────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Kernel Subsystems at a Glance

```
SUBSYSTEM          LOCATION IN SOURCE     WHAT IT DOES
─────────────────────────────────────────────────────────────────────
Scheduler          kernel/sched/          Decides which process runs next
Memory Manager     mm/                    Pages, VMAs, slab, buddy allocator
VFS                fs/                    Unified file interface over ext4/xfs/etc
Network Stack      net/                   TCP, UDP, IP, sockets, netfilter
Block Layer        block/                 I/O scheduling, bio, request queues
Device Model       drivers/base/          sysfs, kobjects, device tree binding
IRQ Subsystem      kernel/irq/            Interrupt routing, affinity, threading
RCU                kernel/rcu/            Lock-free read-side synchronization
Workqueues         kernel/workqueue.c     Deferred kernel work
Timers             kernel/time/           HRtimers, jiffies, clocksource
Tracing            kernel/trace/          ftrace, kprobes, perf events
Security           security/              LSM, SELinux, AppArmor
```

---

## 3. Kernel Source Tree Anatomy

```
linux/
├── arch/               ← Architecture-specific code
│   ├── x86/            ← Intel/AMD: boot, paging, syscall entry
│   ├── arm64/          ← AArch64: Pi 4B, modern ARM
│   ├── arm/            ← 32-bit ARM
│   └── riscv/          ← RISC-V (growing fast)
│
├── block/              ← Block I/O layer (bio, elevators, blk-mq)
├── crypto/             ← Cryptography algorithms
├── drivers/            ← ALL device drivers (largest directory!)
│   ├── char/           ← Character devices
│   ├── net/            ← Network card drivers
│   ├── gpu/drm/        ← Display/GPU drivers
│   ├── usb/            ← USB subsystem
│   ├── i2c/            ← I2C bus drivers
│   ├── spi/            ← SPI bus drivers
│   └── gpio/           ← GPIO drivers
│
├── fs/                 ← Filesystems: ext4, xfs, btrfs, procfs, sysfs
├── include/            ← Kernel header files
│   ├── linux/          ← Core kernel headers (your most-read directory)
│   └── uapi/linux/     ← Headers exported to userspace
│
├── init/               ← Kernel initialization (main.c → start_kernel())
├── ipc/                ← IPC: pipes, message queues, shared memory
├── kernel/             ← Core kernel: sched, rcu, irq, locking, tracing
├── lib/                ← Library functions (rbtree, list, radix-tree)
├── mm/                 ← Memory management (VMM, slab, page allocator)
├── net/                ← Network stack (TCP/IP, sockets, netfilter)
├── rust/               ← Rust kernel infrastructure (since 6.1)
├── samples/            ← Example drivers and code (study these!)
├── scripts/            ← Build scripts, checkpatch.pl
├── security/           ← LSM framework, SELinux, AppArmor
├── sound/              ← ALSA audio subsystem
├── tools/              ← Userspace kernel tools (perf, selftests)
│   ├── perf/           ← Performance analysis tool
│   └── testing/        ← kselftest infrastructure
│
├── Kconfig             ← Root configuration file
├── Kbuild              ← Root build rules
├── Makefile            ← Top-level Makefile
└── Documentation/      ← Kernel documentation (read this!)
    ├── admin-guide/
    ├── core-api/
    ├── driver-api/
    └── rust/           ← Rust-specific kernel docs
```

**Key Concept — `include/linux/`**: This is your bible. Every time you see an unfamiliar kernel API, its declaration is here.

```
include/linux/
├── list.h          ← Doubly-linked list (kernel's most-used data structure)
├── slab.h          ← kmalloc, kfree, kmem_cache
├── spinlock.h      ← Spinlocks, rwlocks
├── mutex.h         ← Sleeping mutexes
├── rcu.h           ← RCU primitives
├── fs.h            ← inode, file, dentry, super_block
├── netdevice.h     ← net_device structure
├── interrupt.h     ← IRQ request/free, interrupt handlers
├── workqueue.h     ← INIT_WORK, schedule_work
├── device.h        ← struct device
├── module.h        ← MODULE_LICENSE, module_init/exit
└── printk.h        ← pr_info, pr_err, pr_debug
```

---

## 4. Build System: Kbuild, Kconfig, Makefiles

### Concept: What is Kbuild?

Kbuild is the Linux kernel's custom build system. It is **not** regular Make — it has its own language of variables, rules, and recursive descent through directories.

```
┌─────────────────────────────────────────────────────────────┐
│                     KBUILD PIPELINE                         │
│                                                             │
│  Kconfig files          → Configuration options (.config)  │
│       ↓                                                     │
│  make menuconfig        → User selects features            │
│       ↓                                                     │
│  .config file           → Records all y/n/m choices        │
│       ↓                                                     │
│  include/generated/     → Auto-generated C headers         │
│  autoconf.h             → #define CONFIG_* macros          │
│       ↓                                                     │
│  Makefile + Kbuild      → Build rules per directory        │
│       ↓                                                     │
│  vmlinux (ELF binary)   → Uncompressed kernel              │
│       ↓                                                     │
│  arch/x86/boot/bzImage  → Compressed bootable kernel       │
│  OR                                                         │
│  arch/arm64/boot/Image  → ARM64 kernel image               │
└─────────────────────────────────────────────────────────────┘
```

### Kconfig Syntax — Understanding Configuration Options

```kconfig
# Example: drivers/mydriver/Kconfig

config MY_DRIVER
    tristate "My example driver"        # tristate = y(built-in) / m(module) / n(disabled)
    depends on X86 && PCI               # Only show if these are enabled
    select DMA_ENGINE                   # Automatically enable DMA_ENGINE
    help
      This driver does something useful.
      Say Y to build into kernel, M for module, N to skip.

config MY_DRIVER_DEBUG
    bool "Enable debug output"          # bool = y(yes) / n(no) only
    depends on MY_DRIVER
    default n
```

### Kbuild Makefile Syntax

```makefile
# drivers/mydriver/Makefile
# "obj-$(CONFIG_MY_DRIVER)" expands to:
#   obj-y   when CONFIG_MY_DRIVER=y   → built into vmlinux
#   obj-m   when CONFIG_MY_DRIVER=m   → built as .ko module
#   obj-    when CONFIG_MY_DRIVER=n   → not built at all

obj-$(CONFIG_MY_DRIVER) += mydriver.o

# Multi-file driver:
mydriver-y := core.o irq.o dma.o

# Conditional object inclusion:
mydriver-$(CONFIG_MY_DRIVER_DEBUG) += debug.o

# CFLAGS for this directory only:
ccflags-y := -DDEBUG_EXTRA
```

### Build Targets Cheat Sheet

```
COMMAND                         WHAT IT DOES
─────────────────────────────────────────────────────────────────────────────
make help                       Show ALL available targets
make defconfig                  Default config for current arch
make allnoconfig                Minimal config (everything disabled)
make allyesconfig               Everything enabled (huge, slow)
make menuconfig                 Interactive TUI config editor
make xconfig                    Qt-based GUI config editor
make oldconfig                  Update .config for new kernel version
make localmodconfig             Config based on currently loaded modules
─────────────────────────────────────────────────────────────────────────────
make -j$(nproc)                 Compile with all CPU cores
make bzImage                    Build only the kernel image (x86)
make Image                      Build only the kernel image (ARM64)
make modules                    Build only modules
make modules_install            Install modules to /lib/modules/$(uname -r)/
make install                    Install kernel to /boot/
─────────────────────────────────────────────────────────────────────────────
make M=drivers/mydriver         Build only one module directory
make M=drivers/mydriver clean   Clean one module
─────────────────────────────────────────────────────────────────────────────
make headers_install            Export userspace headers (uapi)
make tags / cscope              Generate editor tag files
make compile_commands.json      Generate clangd index (for IDE support)
─────────────────────────────────────────────────────────────────────────────
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image   Cross compile ARM64
─────────────────────────────────────────────────────────────────────────────
```

---

## 5. Kernel Configuration Mastery

### The .config File

```
# Example .config entries:
CONFIG_SMP=y               # Symmetric multiprocessing (multiple CPUs)
CONFIG_PREEMPT=y           # Kernel preemption
CONFIG_DEBUG_KERNEL=y      # Enables debug options
CONFIG_KASAN=y             # Kernel Address Sanitizer
CONFIG_LOCKDEP=y           # Lock dependency validator
CONFIG_FUNCTION_TRACER=y   # Enable ftrace
CONFIG_KGDB=y              # Kernel GDB stub
CONFIG_MODULES=y           # Enable loadable modules
CONFIG_MY_DRIVER=m         # My driver as a module
```

### Must-Have Debug Config Options

```
# In .config or via menuconfig:

# ── GENERAL DEBUGGING ────────────────────────────────────────────
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_INFO=y              # Include DWARF debug symbols (needed for GDB)
CONFIG_DEBUG_INFO_DWARF4=y       # DWARF4 format (GDB compatible)
CONFIG_GDB_SCRIPTS=y             # GDB helper scripts for kernel structs

# ── MEMORY DEBUGGING ─────────────────────────────────────────────
CONFIG_KASAN=y                   # Catch use-after-free, out-of-bounds
CONFIG_KASAN_INLINE=y            # Faster KASAN (more binary bloat)
CONFIG_KFENCE=y                  # Low-overhead memory safety
CONFIG_DEBUG_SLAB=y              # Slab allocator debugging
CONFIG_SLUB_DEBUG=y              # SLUB allocator debug
CONFIG_DEBUG_PAGEALLOC=y         # Poison freed pages

# ── CONCURRENCY DEBUGGING ────────────────────────────────────────
CONFIG_LOCKDEP=y                 # Lock dependency checking
CONFIG_PROVE_LOCKING=y           # Prove no deadlock cycles
CONFIG_DEBUG_ATOMIC_SLEEP=y      # Detect sleeping in atomic context
CONFIG_KCSAN=y                   # Data race detector

# ── UNDEFINED BEHAVIOR ───────────────────────────────────────────
CONFIG_UBSAN=y                   # Undefined behavior sanitizer

# ── TRACING ──────────────────────────────────────────────────────
CONFIG_FUNCTION_TRACER=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_KPROBES=y
CONFIG_KRETPROBES=y
CONFIG_FTRACE_SYSCALLS=y

# ── GDB / QEMU DEBUGGING ─────────────────────────────────────────
CONFIG_KGDB=y
CONFIG_KGDB_SERIAL_CONSOLE=y
CONFIG_FRAME_POINTER=y           # Proper stack traces
CONFIG_RANDOMIZE_BASE=n          # Disable KASLR for GDB (predictable addresses)
```

### Quick Config for Development Kernel

```bash
# Start from a minimal working config:
make defconfig

# Then enable debug features non-interactively:
./scripts/config --enable DEBUG_KERNEL
./scripts/config --enable DEBUG_INFO
./scripts/config --enable KASAN
./scripts/config --enable LOCKDEP
./scripts/config --enable PROVE_LOCKING
./scripts/config --enable KGDB
./scripts/config --disable RANDOMIZE_BASE  # For GDB to work predictably

# Resolve new dependencies:
make olddefconfig
```

---

## 6. Compilation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KERNEL COMPILATION PIPELINE (x86_64)                     │
│                                                                             │
│  Source Files (.c, .S, .rs)                                                 │
│        │                                                                    │
│        ▼  (gcc / clang / rustc with special flags)                          │
│  Object Files (.o)                                                           │
│        │  Each directory builds its own built-in.a (archive)               │
│        ▼                                                                    │
│  Linked vmlinux (ELF)                                                       │
│  ├── .text   (executable code)                                              │
│  ├── .data   (initialized data)                                             │
│  ├── .bss    (uninitialized data)                                           │
│  ├── .rodata (read-only data: strings, const)                               │
│  └── __ksymtab (exported symbol table)                                      │
│        │                                                                    │
│        ▼  (objcopy + gzip/lz4/zstd)                                         │
│  arch/x86/boot/bzImage                                                      │
│  ├── setup.bin (real-mode boot code)                                        │
│  └── vmlinux.bin.gz (compressed kernel)                                     │
│        │                                                                    │
│        ▼  (GRUB / bootloader loads this)                                    │
│  Boot → Decompress → Jump to start_kernel()                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compilation Commands

```bash
# ── STEP 1: Install dependencies ─────────────────────────────────────
sudo apt install build-essential flex bison libssl-dev libelf-dev \
    bc libncurses-dev dwarves pahole gcc g++

# ── STEP 2: Get source ───────────────────────────────────────────────
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

# Or use a stable release:
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.tar.xz
tar xf linux-6.12.tar.xz && cd linux-6.12

# ── STEP 3: Configure ────────────────────────────────────────────────
make defconfig              # Start with sane defaults
make menuconfig             # Customize interactively

# ── STEP 4: Compile ──────────────────────────────────────────────────
make -j$(nproc) 2>&1 | tee build.log
# -j$(nproc): use all CPU cores
# tee build.log: save output to file for analysis

# ── STEP 5: Check for warnings ───────────────────────────────────────
grep -i "warning\|error" build.log | head -50

# ── STEP 6: Build only a single file (fast iteration) ────────────────
make kernel/sched/core.o          # Compile just one file
make M=drivers/mydriver/          # Compile just one module directory

# ── STEP 7: Compile with verbose output ──────────────────────────────
make V=1 -j$(nproc)               # See exact commands run
make V=2 -j$(nproc)               # Even more verbose

# ── STEP 8: Compile with clang (alternative compiler) ────────────────
make CC=clang -j$(nproc)
```

### Understanding Compiler Flags

```
KEY KERNEL COMPILER FLAGS (set by Kbuild, not you — but you should know them):

-ffreestanding     → No standard library, no assumptions about runtime
-fno-common        → No common symbols (required for kernel)
-fno-stack-protector   → Kernel manages its own stack (no glibc SSP)
-mno-red-zone      → No red zone (required for x86_64 kernel — interrupts!)
-mcmodel=kernel    → Use kernel code model for addressing
-pg                → (with CONFIG_FUNCTION_TRACER) adds mcount() calls
-O2                → Optimization level (kernel always optimizes)
-g                 → (with CONFIG_DEBUG_INFO) DWARF symbols
```

---

## 7. The Master Decision Tree: What to Do After a Change

```
YOU MADE A KERNEL SOURCE CHANGE
│
├─────────────────────────────────────────────────────────────────────
│  WHAT TYPE OF CHANGE?
│
├── [A] Quick logic change (scheduler, memory, syscall, core kernel)
│   │   Examples: Changed CFS weight calc, fixed page fault handler,
│   │             tweaked syscall behavior, modified memory allocator
│   │
│   └── STRATEGY: QEMU + initramfs (fastest possible feedback loop)
│       ├── Time to boot: ~2-5 seconds
│       ├── No full OS needed — just your kernel + tiny busybox rootfs
│       ├── See Section 8 (QEMU) and Section 9 (initramfs)
│       └── Check: dmesg output, /proc entries, custom test program
│
├── [B] Testing with systemd / real userspace / real init system
│   │   Examples: Cgroup changes, namespace isolation, udev rules,
│   │             real service behavior, PAM, D-Bus interaction
│   │
│   └── STRATEGY: QEMU + Debian cloud image
│       ├── Full Debian runs inside QEMU VM
│       ├── Boot time: ~15-30 seconds
│       ├── Can run apt, systemctl, any real application
│       └── See Section 10 (QEMU + Debian)
│
├── [C] Debugging: GDB, breakpoints, inspect memory, step through code
│   │   Examples: Chasing NULL deref, understanding execution flow,
│   │             inspecting kernel data structures, race condition hunt
│   │
│   └── STRATEGY: QEMU with -s -S + GDB attached to vmlinux
│       ├── QEMU -s: opens :1234 gdbserver
│       ├── QEMU -S: freezes CPU at boot (wait for GDB connect)
│       ├── GDB: target remote :1234, then full debug power
│       └── See Section 11 (GDB Debugging)
│
├── [D] ARM driver, GPIO, SPI, I2C, Pi-specific code
│   │   Examples: I2C device driver, SPI display, GPIO expander,
│   │             Pi-specific DMA, BCM2711 peripheral
│   │
│   └── STRATEGY: Cross-compile → deploy to Raspberry Pi 4B
│       ├── Build on x86 host, run on ARM64 Pi
│       ├── Use scp or NFS to deploy module/kernel
│       ├── UART serial console for kernel output
│       └── See Section 12 (Cross-Compilation)
│
└── [E] Device driver, VMware-specific, PCI passthrough, specific hardware
    │   Examples: VMXNET3 driver, PVSCSI, VMware balloon driver,
    │             virtio drivers, hypervisor interaction
    │
    └── STRATEGY: VMware Workstation with Debian VM
        ├── Full hardware virtualization with device emulation
        ├── Snapshot before testing (revert on crash!)
        ├── Serial console for kernel messages
        └── See Section 13 (VMware Testing)
```

### When to Use Multiple Strategies

```
ITERATIVE DEVELOPMENT WORKFLOW:
─────────────────────────────────────────────────────────────────

1. Write/Edit code
       │
       ▼
2. make -j$(nproc) (or make M=drivers/mydir/)
       │
       ├── BUILD FAILS → fix compile errors → back to step 1
       │
       └── BUILD SUCCEEDS
               │
               ▼
3. Quick sanity test (QEMU + initramfs)
       │
       ├── CRASH/PANIC → GDB debug mode → fix → back to step 1
       │
       └── BASIC TEST PASSES
               │
               ▼
4. Full userspace test (QEMU + Debian)
       │
       ├── FAIL → more debugging → back to step 1
       │
       └── PASS
               │
               ▼
5. Hardware test (Pi 4B / VMware)
       │
       ├── FAIL → hardware-specific debug
       │
       └── PASS → Submit patch / merge
```

---

## 8. QEMU: Lightweight Fast Testing

### Concept: What is QEMU?

**QEMU** (Quick Emulator) is a machine emulator and virtualizer. In kernel development:
- It emulates an **entire computer** in software
- Your kernel boots inside this virtual machine
- If the kernel panics, only the QEMU process dies — your host is safe
- You can run 10 different kernel versions simultaneously

```
YOUR HOST MACHINE (x86_64, Linux)
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  qemu-system-x86_64 process                                    │
│  ┌──────────────────────────────────────────────┐             │
│  │   VIRTUAL MACHINE                            │             │
│  │   ┌──────────────────────────────────────┐  │             │
│  │   │  YOUR KERNEL (bzImage)               │  │             │
│  │   │  Boots, runs, panics if buggy        │  │             │
│  │   └──────────────────────────────────────┘  │             │
│  │   Virtual CPU │ Virtual RAM │ Virtual Disk   │             │
│  └──────────────────────────────────────────────┘             │
│                                                                │
│  Host kernel is completely safe from VM crashes               │
└────────────────────────────────────────────────────────────────┘
```

### QEMU Installation

```bash
# Debian/Ubuntu:
sudo apt install qemu-system-x86 qemu-system-arm \
    qemu-system-aarch64 ovmf

# Fedora/RHEL:
sudo dnf install qemu-kvm qemu-system-aarch64

# Check version:
qemu-system-x86_64 --version
```

### QEMU Command Anatomy

```bash
qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \   # The kernel to boot
    -initrd initramfs.cpio.gz \       # Initial root filesystem
    -append "console=ttyS0 nokaslr"\ # Kernel command line args
    -nographic \                      # No GUI, use terminal
    -m 512M \                         # 512MB RAM
    -smp 2 \                          # 2 virtual CPUs
    -enable-kvm \                     # Use KVM acceleration (10x faster!)
    -s \                              # GDB server on :1234
    -S                                # Freeze at start (wait for GDB)
```

### QEMU Flags Reference

```
FLAG                        MEANING
─────────────────────────────────────────────────────────────────────────────
-kernel <bzImage>           Kernel image to boot
-initrd <file>              Initial RAM disk (initramfs)
-append "..."               Kernel command line (like GRUB)
-m 512M                     RAM size (512MB)
-smp 4                      Number of virtual CPUs
-enable-kvm                 Use Linux KVM for hardware acceleration
-nographic                  No graphical window (use terminal I/O)
-serial stdio               Redirect serial port to terminal (for console)
-serial mon:stdio           Serial + QEMU monitor multiplexed
-monitor telnet::4444,server,nowait   QEMU monitor on telnet port 4444
-s                          GDB stub: listens on tcp::1234
-S                          Freeze CPU at startup (waits for GDB 'c')
-hda disk.img               Attach a disk image as /dev/sda
-cdrom image.iso            Attach ISO as CDROM
-net none                   No networking
-net nic -net user          Simple userspace networking (NAT)
-netdev tap,id=n0 ...       TAP networking (bridge to host)
-drive format=raw,...       Fine-grained disk attachment
-virtfs ...                 Share a host directory into guest (9p)
-snapshot                   Don't modify disk image (discard writes)
─────────────────────────────────────────────────────────────────────────────
```

### Kernel Command Line Parameters (the -append string)

```
PARAMETER                   MEANING
─────────────────────────────────────────────────────────────────────────────
console=ttyS0               Send kernel console output to first serial port
console=ttyAMA0             ARM serial port
nokaslr                     Disable KASLR (needed for GDB with fixed addresses)
noapic                      Disable APIC (workaround for some VM issues)
panic=1                     Reboot 1s after kernel panic (or panic=0 to halt)
loglevel=7                  Max verbosity (0=emergency to 7=debug)
init=/bin/sh                Start /bin/sh instead of /sbin/init
root=/dev/sda1              Use /dev/sda1 as root filesystem
rootfstype=ext4             Root filesystem type
rw                          Mount root read-write
ro                          Mount root read-only
kgdbwait                    Wait for GDB at boot (with KGDB enabled)
kgdboc=ttyS0,115200         GDB over serial port (console)
earlyprintk=serial,ttyS0    Kernel output before console is fully set up
debug                       Enable extra debug output
ftrace=function             Start with ftrace enabled at boot
─────────────────────────────────────────────────────────────────────────────
```

---

## 9. initramfs: Building a Minimal Root Filesystem

### Concept: What is initramfs?

**initramfs** (initial RAM filesystem) is a tiny filesystem that the kernel mounts as its first root filesystem — all in RAM, loaded at boot. It contains:
- A minimal init program
- Essential tools (busybox gives you sh, ls, mount, etc.)
- Your test programs

```
BOOT SEQUENCE WITH INITRAMFS:
──────────────────────────────────────────────────────────────────

BIOS/UEFI
    │
    ▼
Bootloader (GRUB/QEMU)
    │ loads bzImage + initramfs.cpio.gz into RAM
    ▼
Kernel decompresses itself
    │
    ▼
Kernel initializes hardware/subsystems
    │
    ▼
Kernel unpacks initramfs.cpio.gz → tmpfs at /
    │
    ▼
Kernel executes /init (or /sbin/init)  ← YOUR FIRST USERSPACE PROCESS
    │
    ▼
Your test program runs, tests kernel, exits
    │
    ▼
(Optional) Pivot to real rootfs OR
           Kernel panics with "No init found" if /init missing
```

### Building initramfs with BusyBox

```
Concept: BusyBox
BusyBox is a single binary (~1MB) that contains 300+ Unix utilities.
It uses symlinks so that ls → busybox, cat → busybox, etc.
Perfect for minimal rootfs: small, self-contained, no dependencies.
```

```bash
# ── STEP 1: Download and compile BusyBox ─────────────────────────────
wget https://busybox.net/downloads/busybox-1.36.1.tar.bz2
tar xf busybox-1.36.1.tar.bz2
cd busybox-1.36.1

make defconfig
# Enable static linking (no shared libs needed in initramfs):
make menuconfig
# Navigate: Settings → Build static binary (no shared libs) → enable
make -j$(nproc)
make install   # Creates _install/ directory with all symlinks
cd ..

# ── STEP 2: Build the initramfs directory structure ───────────────────
mkdir -p initramfs/{bin,sbin,etc,proc,sys,dev,tmp,lib}

# Copy BusyBox:
cp busybox-1.36.1/_install/bin/busybox initramfs/bin/
# Create essential symlinks:
ln -s busybox initramfs/bin/sh
ln -s busybox initramfs/bin/ls
ln -s busybox initramfs/bin/cat
ln -s busybox initramfs/bin/dmesg

# ── STEP 3: Create the /init script ──────────────────────────────────
cat > initramfs/init << 'EOF'
#!/bin/sh
# This is PID 1 — the first process the kernel runs

# Mount essential virtual filesystems:
mount -t proc none /proc       # Process info
mount -t sysfs none /sys       # Device info
mount -t devtmpfs none /dev    # Device files

echo "=== Kernel Test Environment ==="
echo "Kernel: $(cat /proc/version)"

# Mount debugfs (for ftrace, kprobes, etc.):
mount -t debugfs none /sys/kernel/debug 2>/dev/null

# Run your test program:
if [ -x /bin/my_test ]; then
    /bin/my_test
fi

# Start a shell for interactive exploration:
echo "Dropping to shell. Type 'poweroff' to exit."
exec /bin/sh

EOF
chmod +x initramfs/init

# ── STEP 4: Add your test program ────────────────────────────────────
# Compile test program statically (no dynamic libs in initramfs):
cat > my_test.c << 'EOF'
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

int main() {
    char buf[256];
    int fd;

    printf("[TEST] Starting kernel feature test\n");

    // Example: Read from procfs
    fd = open("/proc/version", O_RDONLY);
    if (fd >= 0) {
        int n = read(fd, buf, sizeof(buf)-1);
        buf[n] = '\0';
        printf("[TEST] Kernel version: %s\n", buf);
        close(fd);
    }

    printf("[TEST] Done.\n");
    return 0;
}
EOF
gcc -static -o initramfs/bin/my_test my_test.c

# ── STEP 5: Package into a CPIO archive ──────────────────────────────
cd initramfs
find . | cpio -H newc -o | gzip -9 > ../initramfs.cpio.gz
cd ..

echo "initramfs.cpio.gz created: $(du -sh initramfs.cpio.gz)"

# ── STEP 6: Boot it! ─────────────────────────────────────────────────
qemu-system-x86_64 \
    -kernel linux/arch/x86/boot/bzImage \
    -initrd initramfs.cpio.gz \
    -append "console=ttyS0 nokaslr loglevel=7" \
    -nographic \
    -m 256M \
    -enable-kvm
```

### Automating the Test Loop (Fast Iteration)

```bash
#!/bin/bash
# fast_test.sh — rebuild kernel + initramfs and boot in QEMU

set -e

KERNEL_DIR=~/linux
INITRD=~/initramfs.cpio.gz

echo "[1/3] Rebuilding kernel..."
cd $KERNEL_DIR
make -j$(nproc) bzImage 2>&1 | tail -5

echo "[2/3] Rebuilding initramfs..."
cd ~/initramfs
# Recompile test program if changed:
gcc -static -o bin/my_test ~/my_test.c
find . | cpio -H newc -o | gzip -9 > $INITRD

echo "[3/3] Booting in QEMU..."
qemu-system-x86_64 \
    -kernel $KERNEL_DIR/arch/x86/boot/bzImage \
    -initrd $INITRD \
    -append "console=ttyS0 nokaslr panic=1" \
    -nographic \
    -m 256M \
    -enable-kvm \
    -no-reboot
```

---

## 10. QEMU + Full Debian Userspace

### When You Need a Real OS

```
initramfs is great for:          Debian image is needed for:
────────────────────────         ──────────────────────────────
Simple kernel tests              systemd behavior testing
Checking dmesg output            udev / device manager tests
Testing procfs/sysfs             Real application testing
Speed (2-5 sec boot)             Namespace / cgroup testing
Small disk footprint             apt install anything you need
```

### Creating a Debian Disk Image

```bash
# ── METHOD 1: Use prebuilt cloud image ───────────────────────────────
# Fastest: download a ready-made Debian cloud image
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-nocloud-amd64.qcow2

# Resize if needed (default is ~2GB):
qemu-img resize debian-12-nocloud-amd64.qcow2 +8G

# ── METHOD 2: Build with debootstrap (full control) ──────────────────
# Install tools:
sudo apt install debootstrap qemu-img

# Create a 4GB raw disk image:
qemu-img create -f raw debian.img 4G

# Format it:
sudo mkfs.ext4 debian.img

# Mount and install Debian base:
mkdir /tmp/debian-root
sudo mount -o loop debian.img /tmp/debian-root
sudo debootstrap --arch=amd64 bookworm /tmp/debian-root \
    https://deb.debian.org/debian/

# Chroot and configure:
sudo chroot /tmp/debian-root /bin/bash << 'CHROOT'
# Set root password:
echo "root:root" | chpasswd

# Install essential packages:
apt install -y systemd udev login util-linux procps kmod

# Set up serial console (important for QEMU -nographic):
systemctl enable serial-getty@ttyS0.service

# Configure fstab:
echo "/dev/sda / ext4 errors=remount-ro 0 1" > /etc/fstab

exit
CHROOT

sudo umount /tmp/debian-root
```

### Booting Debian with Your Custom Kernel

```bash
# Boot Debian with your kernel (not the kernel in the image):
qemu-system-x86_64 \
    -kernel linux/arch/x86/boot/bzImage \
    -drive file=debian-12-nocloud-amd64.qcow2,format=qcow2 \
    -append "root=/dev/sda1 rw console=ttyS0 nokaslr" \
    -nographic \
    -m 2G \
    -smp 2 \
    -enable-kvm \
    -net nic,model=virtio \
    -net user,hostfwd=tcp::2222-:22    # SSH via localhost:2222
```

### Installing Your Kernel Modules into the Image

```bash
# Method 1: Install modules to a staging directory, then copy to image
make INSTALL_MOD_PATH=/tmp/mod-staging modules_install

# Mount the image and copy modules:
sudo mount -o loop debian.img /tmp/debian-root
sudo cp -r /tmp/mod-staging/lib/modules/* /tmp/debian-root/lib/modules/
sudo umount /tmp/debian-root

# Method 2: 9P virtfs (share host directory into guest — no copy needed!)
qemu-system-x86_64 \
    -kernel linux/arch/x86/boot/bzImage \
    -drive file=debian.img,format=raw \
    -append "root=/dev/sda rw console=ttyS0 nokaslr" \
    -nographic -m 2G -smp 2 -enable-kvm \
    -virtfs local,path=/tmp/mod-staging,mount_tag=modules,security_model=mapped

# Inside guest:
# mount -t 9p modules /mnt/modules
# cp -r /mnt/modules/lib/modules/* /lib/modules/
# depmod -a
```

---

## 11. GDB Kernel Debugging with QEMU

### Concept: What is GDB Kernel Debugging?

**GDB** (GNU Debugger) is THE debugger for C programs. With QEMU's built-in GDB stub (`-s` flag), you can:
- Set **breakpoints** (stop execution at any kernel function)
- **Step** through code line by line
- **Inspect** memory, registers, variables
- Read kernel **data structures** in real-time

```
HOST MACHINE                              QEMU VM
┌──────────────────────────┐             ┌────────────────────────┐
│                          │             │                        │
│  gdb vmlinux             │ ←─TCP:1234─→│ QEMU GDB stub         │
│  (target remote :1234)   │             │ (-s flag)              │
│                          │             │                        │
│  ┌────────────────────┐  │             │  Kernel running...     │
│  │ b schedule         │  │             │  (stopped at -S)       │
│  │ b do_page_fault    │  │             │  or                    │
│  │ p current->pid     │  │             │  (running, hit BP)     │
│  │ x/20wx $rsp        │  │             │                        │
│  └────────────────────┘  │             └────────────────────────┘
└──────────────────────────┘
```

### Step-by-Step GDB Debugging Workflow

```bash
# ── TERMINAL 1: Start QEMU paused, waiting for GDB ───────────────────
qemu-system-x86_64 \
    -kernel linux/arch/x86/boot/bzImage \
    -initrd initramfs.cpio.gz \
    -append "console=ttyS0 nokaslr kgdbwait" \
    -nographic \
    -m 512M \
    -enable-kvm \
    -s \     # GDB server on :1234
    -S       # Stop immediately, wait for GDB to connect

# QEMU will now sit frozen, waiting for GDB.

# ── TERMINAL 2: Connect GDB ──────────────────────────────────────────
gdb linux/vmlinux   # vmlinux = ELF with full symbols (NOT bzImage!)

# Inside GDB:
(gdb) set architecture i386:x86-64   # Set target architecture
(gdb) target remote :1234             # Connect to QEMU
# GDB is now connected. Kernel is frozen at very early boot.

(gdb) continue                        # Let kernel boot
# Wait for kernel to boot...

# ── SETTING BREAKPOINTS ──────────────────────────────────────────────
(gdb) break schedule                  # Break when scheduler runs
(gdb) break do_page_fault             # Break on page fault
(gdb) break my_driver_probe           # Break in your driver
(gdb) break kernel/sched/core.c:1234  # Break at specific line

(gdb) continue                        # Run until breakpoint hit

# ── WHEN BREAKPOINT HITS ─────────────────────────────────────────────
(gdb) backtrace                       # Show call stack
(gdb) backtrace full                  # Show with local variables
(gdb) frame 2                         # Select stack frame 2
(gdb) info locals                     # Show local variables
(gdb) print current                   # Print current task_struct ptr
(gdb) print current->pid              # Print current process PID
(gdb) print current->comm             # Print current process name

# ── STEPPING ─────────────────────────────────────────────────────────
(gdb) next                            # Next line (step over functions)
(gdb) step                            # Step into function calls
(gdb) nexti                           # Next machine instruction
(gdb) stepi                           # Step one machine instruction
(gdb) finish                          # Run to end of current function

# ── MEMORY INSPECTION ────────────────────────────────────────────────
(gdb) x/20wx $rsp                     # 20 words at stack pointer
(gdb) x/s 0xffffffff81234567          # String at kernel address
(gdb) x/10i $rip                      # 10 instructions at instruction pointer
(gdb) info registers                  # All CPU registers
(gdb) print *(struct task_struct*)0xffff888... # Cast and dereference

# ── WATCHPOINTS ──────────────────────────────────────────────────────
(gdb) watch my_global_var             # Stop when variable written
(gdb) rwatch my_global_var            # Stop when variable read

# ── KERNEL-SPECIFIC GDB SCRIPTS ──────────────────────────────────────
# If CONFIG_GDB_SCRIPTS=y was set, load helper scripts:
(gdb) source linux/scripts/gdb/vmlinux-gdb.py

# Now you can use kernel-aware commands:
(gdb) lx-ps                           # List all processes (like ps aux)
(gdb) lx-dmesg                        # Print kernel ring buffer
(gdb) lx-symbols                      # Load module symbols
(gdb) lx-list-check                   # Check list integrity
```

### GDB + KASLR (Important!)

```
KASLR = Kernel Address Space Layout Randomization
        The kernel loads at a RANDOM base address each boot.
        This breaks GDB because symbols have fixed addresses in vmlinux.

Solutions:
1. Disable KASLR:  -append "nokaslr"  (simplest for development)
2. Or find the offset and tell GDB:
   (gdb) add-symbol-file vmlinux <actual_load_address>
   # Find actual address from: cat /proc/kallsyms | grep startup_64
```

### GDB Automation Script

```bash
# gdb_kernel.sh — automate GDB kernel debug session
cat > gdb_kernel.gdb << 'EOF'
set architecture i386:x86-64
target remote :1234
set pagination off
add-auto-load-safe-path /home/user/linux

# Load kernel GDB helpers
source /home/user/linux/scripts/gdb/vmlinux-gdb.py

# Set your breakpoints here:
break panic
break oops_begin
# break my_function

# Commands to run when hitting panic:
define hook-stop
  echo === STOPPED ===\n
  backtrace
end

continue
EOF

gdb linux/vmlinux -x gdb_kernel.gdb
```

---

## 12. Cross-Compilation for ARM / Raspberry Pi 4B

### Concept: Cross-Compilation

**Cross-compilation** means: compile code on machine A (your x86_64 laptop) that runs on machine B (ARM64 Raspberry Pi). The compiler itself runs on x86_64 but generates ARM64 machine code.

```
YOUR LAPTOP (x86_64)                    RASPBERRY PI 4B (ARM64 / AArch64)
┌──────────────────────────┐            ┌──────────────────────────────┐
│                          │            │                              │
│  aarch64-linux-gnu-gcc   │            │  BCM2711 SoC               │
│  (runs on x86)           │            │  Cortex-A72 cores          │
│  generates ARM64 code    │ ──scp──→   │  4GB RAM                   │
│                          │            │  GPIO/I2C/SPI/UART         │
│  Output: Image           │            │  Boots your kernel!        │
│  Output: mydriver.ko     │            │                              │
└──────────────────────────┘            └──────────────────────────────┘
```

### Cross-Compilation Setup

```bash
# ── Install cross-compiler toolchain ─────────────────────────────────
sudo apt install gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
    g++-aarch64-linux-gnu

# Verify:
aarch64-linux-gnu-gcc --version
# Output: aarch64-linux-gnu-gcc 12.x.x ...

# ── Cross-compile the kernel ─────────────────────────────────────────
cd linux/

# Set architecture and cross-compiler prefix:
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# Use the Pi 4 defconfig (includes BCM2711 SoC support):
make bcm2711_defconfig

# Optionally customize:
make menuconfig

# Compile (produces arch/arm64/boot/Image):
make -j$(nproc) Image modules dtbs
# Image     = uncompressed kernel for Pi 4
# modules   = all .ko files
# dtbs      = Device Tree Blobs (hardware description for ARM)

# ── Deploy to Pi 4B via SCP ──────────────────────────────────────────
PI_IP=192.168.1.100

# Copy kernel image:
scp arch/arm64/boot/Image pi@$PI_IP:/boot/kernel8.img
# (Pi 4B loads kernel8.img for 64-bit mode)

# Copy Device Tree:
scp arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dtb \
    pi@$PI_IP:/boot/

# Install modules:
make INSTALL_MOD_PATH=/tmp/pi-mods modules_install
scp -r /tmp/pi-mods/lib/modules/* pi@$PI_IP:/lib/modules/

# ── On the Pi: rebuild module dependency database ─────────────────────
ssh pi@$PI_IP "sudo depmod -a && sudo reboot"
```

### Building Only a Single Module for Pi

```bash
# Much faster — just recompile the module, not the whole kernel:

export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# Build a specific module against the already-compiled kernel tree:
make M=drivers/mydriver/ modules

# The output is: drivers/mydriver/mydriver.ko

# Copy to Pi:
scp drivers/mydriver/mydriver.ko pi@$PI_IP:/home/pi/

# On Pi:
# sudo insmod /home/pi/mydriver.ko
# dmesg | tail -20
```

### Pi Serial Console Setup (Critical for Kernel Debugging)

```
Why serial console?
  - HDMI might not work if your kernel is broken
  - SSH requires a working TCP stack (might be broken)
  - Serial console works at the very earliest kernel boot stage
  - You can see panic messages before the system dies

Pi 4 UART Wiring to USB-TTL Adapter:
  Pi Pin 6  (GND) ──────→ Adapter GND (black)
  Pi Pin 8  (TX)  ──────→ Adapter RX  (white)
  Pi Pin 10 (RX)  ──────→ Adapter TX  (green)
```

```bash
# In /boot/config.txt on Pi:
enable_uart=1

# In /boot/cmdline.txt on Pi:
console=serial0,115200 console=tty1 root=/dev/mmcblk0p2 ...

# On your laptop, connect to Pi serial:
screen /dev/ttyUSB0 115200
# Or:
minicom -b 115200 -D /dev/ttyUSB0
# Or:
picocom -b 115200 /dev/ttyUSB0
```

### NFS Root for Rapid Iteration (Advanced)

```bash
# Instead of copying files to SD card every time:
# Boot Pi with root filesystem served over network (NFS).
# Change kernel on host → Pi boots new kernel immediately.

# On HOST laptop:
sudo apt install nfs-kernel-server

# Create NFS export directory:
sudo mkdir -p /nfs/pi-root
# (populate with Pi rootfs via debootstrap or copy from SD card)

# Export it:
echo "/nfs/pi-root *(rw,sync,no_root_squash,no_subtree_check)" | \
    sudo tee -a /etc/exports
sudo exportfs -ra

# Pi boot cmdline.txt:
# root=/dev/nfs nfsroot=192.168.1.50:/nfs/pi-root,tcp,nfsvers=3 \
#   rw ip=dhcp console=serial0,115200
```

---

## 13. VMware Workstation: Driver Testing

### When to Use VMware

```
VMware Workstation is preferred over QEMU when:
┌─────────────────────────────────────────────────────────────────┐
│ ✓ Testing VMware-specific drivers (VMXNET3, PVSCSI, SVGA)      │
│ ✓ Testing PCI device enumeration                                │
│ ✓ Need precise hardware emulation of specific devices           │
│ ✓ Using VMware's snapshot system (critical safety feature!)     │
│ ✓ Testing with VMware Workstation-hosted GUIs                   │
│ ✓ Your team uses VMware for standardized test environments      │
└─────────────────────────────────────────────────────────────────┘
```

### VMware Setup for Kernel Development

```
ALWAYS CREATE A SNAPSHOT BEFORE TESTING:
  VM → Snapshot → Take Snapshot → "Before kernel test"

  If your kernel panics and corrupts the VM:
  VM → Snapshot → Revert to Snapshot → instant recovery

  This is non-negotiable. Crashes in kernel development
  can corrupt the virtual disk. Snapshots save you.
```

```bash
# ── INSIDE THE DEBIAN VM ──────────────────────────────────────────────

# Install build tools in VM:
sudo apt install build-essential linux-headers-$(uname -r) \
    git vim

# Method 1: Build kernel inside VM (slow, no cross-compilation)
# Clone kernel in VM, make defconfig, make -j$(nproc)

# Method 2: Compile on host, transfer to VM (faster)
# On host: compile the module
make M=drivers/mydriver/ modules

# Transfer via VMware shared folder:
# VMware → VM Settings → Options → Shared Folders → Add
# Host path: /home/user/linux/drivers/mydriver
# Guest path: /mnt/hgfs/mydriver (VMware Tools must be installed)

# In VM:
cp /mnt/hgfs/mydriver/mydriver.ko /tmp/
sudo insmod /tmp/mydriver.ko
dmesg | tail -20

# Method 3: SCP (VMware NAT network)
# Find VM IP: (in VM) ip addr
# On host:
scp drivers/mydriver/mydriver.ko user@VM_IP:/home/user/
```

### VMware Serial Console for Kernel Messages

```
In VMware VM settings → Add → Serial Port → Output to file
Select a file on your host, e.g.: /tmp/vm-serial.log

In VM /etc/default/grub:
  GRUB_CMDLINE_LINUX="console=tty0 console=ttyS0,115200n8"
  GRUB_TERMINAL="serial"
  GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"

sudo update-grub

On host, read serial output:
  tail -f /tmp/vm-serial.log
```

---

## 14. Kernel Modules: Build, Load, Unload

### Concept: What is a Kernel Module?

A **kernel module** (`.ko` file) is a piece of code that can be dynamically loaded into (and unloaded from) the running kernel — without rebooting. It runs in kernel space with full kernel privileges.

```
RUNNING KERNEL
┌─────────────────────────────────────────────────────┐
│  Core kernel (vmlinux)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │scheduler │  │  memory  │  │  VFS     │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                                          ↑          │
│  ┌─────────────────────────────────────┐ │ insmod   │
│  │  mydriver.ko (loaded module)        │─┘          │
│  │  Has: init_module, exit_module     │             │
│  └─────────────────────────────────────┘            │
│                    ↓ rmmod                          │
│  Module unloaded, memory freed                      │
└─────────────────────────────────────────────────────┘
```

### Minimal Kernel Module in C

```c
// mymodule.c — The smallest useful kernel module
//
// Concepts used:
//   module_init()  = function to call when module is loaded (insmod)
//   module_exit()  = function to call when module is unloaded (rmmod)
//   pr_info()      = kernel's printf (goes to dmesg)
//   MODULE_LICENSE = required to avoid "taint" warnings
//   MODULE_AUTHOR  = metadata
//   THIS_MODULE    = pointer to this module's struct module

#include <linux/init.h>      // module_init, module_exit
#include <linux/module.h>    // MODULE_* macros
#include <linux/kernel.h>    // pr_info, KERN_INFO

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name <your@email.com>");
MODULE_DESCRIPTION("Minimal example kernel module");
MODULE_VERSION("1.0");

// This function runs when you do: sudo insmod mymodule.ko
// Return 0 = success, negative errno = failure
static int __init mymodule_init(void)
{
    pr_info("mymodule: loaded successfully!\n");
    pr_info("mymodule: PID of loading process: %d\n", current->pid);
    return 0;  // 0 = success; -ENOMEM, -EINVAL etc. = failure
}

// This function runs when you do: sudo rmmod mymodule
// Must undo everything init did
static void __exit mymodule_exit(void)
{
    pr_info("mymodule: unloaded\n");
}

module_init(mymodule_init);  // Register init function
module_exit(mymodule_exit);  // Register exit function
```

```makefile
# Makefile for out-of-tree module build
# Must be in the same directory as mymodule.c

# KDIR = path to built kernel source tree
KDIR ?= /lib/modules/$(shell uname -r)/build

obj-m := mymodule.o    # Build mymodule.c → mymodule.o → mymodule.ko

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# To build against a custom kernel (not the running one):
# make KDIR=/path/to/linux/build/directory
```

```bash
# ── Build ────────────────────────────────────────────────────────────
make

# ── Load ─────────────────────────────────────────────────────────────
sudo insmod mymodule.ko

# ── Verify loaded ────────────────────────────────────────────────────
lsmod | grep mymodule
dmesg | tail -5   # See pr_info output

# ── Inspect module info ──────────────────────────────────────────────
modinfo mymodule.ko

# ── Unload ───────────────────────────────────────────────────────────
sudo rmmod mymodule
dmesg | tail -5   # See exit message

# ── Load with parameters ─────────────────────────────────────────────
# First add to module:
# module_param(myparam, int, 0644);
# MODULE_PARM_DESC(myparam, "An integer parameter");
sudo insmod mymodule.ko myparam=42
```

### A More Complete Driver Module in C

```c
// char_driver.c — A complete character device driver
// Concepts:
//   Character device = exposes /dev/mydevice file
//   User can open(), read(), write(), close() it
//   ioctl() for custom control commands

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>          // file_operations, alloc_chrdev_region
#include <linux/cdev.h>        // cdev_init, cdev_add
#include <linux/device.h>      // class_create, device_create
#include <linux/uaccess.h>     // copy_to_user, copy_from_user
#include <linux/slab.h>        // kmalloc, kfree

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kernel Dev");
MODULE_DESCRIPTION("Character device example");

#define DEVICE_NAME "mychardev"
#define CLASS_NAME  "myclass"
#define BUFFER_SIZE 1024

// Per-device structure (our device's state):
struct my_dev {
    struct cdev cdev;          // Kernel's character device structure
    char *buffer;              // Our data buffer
    size_t buf_len;            // Current data length
    // In a real driver: add spinlock for concurrent access
};

static dev_t dev_num;          // Major:Minor number (assigned by kernel)
static struct class *dev_class;
static struct my_dev *my_device;

// Called when user opens /dev/mychardev
static int my_open(struct inode *inode, struct file *file)
{
    // Store pointer to our device struct in file's private_data
    // (so read/write/release can find it)
    struct my_dev *dev = container_of(inode->i_cdev, struct my_dev, cdev);
    file->private_data = dev;
    pr_info("mychardev: opened\n");
    return 0;
}

// Called when user reads from /dev/mychardev
// buf = userspace buffer, count = bytes requested
// Returns: bytes actually copied, or negative errno
static ssize_t my_read(struct file *file, char __user *buf,
                        size_t count, loff_t *ppos)
{
    struct my_dev *dev = file->private_data;

    // Don't read past end of our buffer:
    if (*ppos >= dev->buf_len)
        return 0;  // EOF
    if (count > dev->buf_len - *ppos)
        count = dev->buf_len - *ppos;

    // CRITICAL: Cannot use memcpy() to copy to userspace!
    // Must use copy_to_user() — it handles page faults safely
    if (copy_to_user(buf, dev->buffer + *ppos, count))
        return -EFAULT;  // Bad userspace address

    *ppos += count;
    return count;
}

// Called when user writes to /dev/mychardev
static ssize_t my_write(struct file *file, const char __user *buf,
                         size_t count, loff_t *ppos)
{
    struct my_dev *dev = file->private_data;

    if (count > BUFFER_SIZE)
        count = BUFFER_SIZE;

    // copy_from_user: safe copy from userspace to kernelspace
    if (copy_from_user(dev->buffer, buf, count))
        return -EFAULT;

    dev->buf_len = count;
    pr_info("mychardev: received %zu bytes\n", count);
    return count;
}

// Called when user closes /dev/mychardev
static int my_release(struct inode *inode, struct file *file)
{
    pr_info("mychardev: closed\n");
    return 0;
}

// Function pointer table: maps file operations to our functions
static const struct file_operations my_fops = {
    .owner   = THIS_MODULE,
    .open    = my_open,
    .read    = my_read,
    .write   = my_write,
    .release = my_release,
};

static int __init chardev_init(void)
{
    int ret;

    // Allocate device number (kernel chooses major number):
    ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
    if (ret < 0) {
        pr_err("mychardev: cannot allocate major number\n");
        return ret;
    }
    pr_info("mychardev: major=%d minor=%d\n",
            MAJOR(dev_num), MINOR(dev_num));

    // Allocate our device structure:
    my_device = kzalloc(sizeof(*my_device), GFP_KERNEL);
    if (!my_device) {
        ret = -ENOMEM;
        goto err_chrdev;
    }

    // Allocate data buffer:
    my_device->buffer = kmalloc(BUFFER_SIZE, GFP_KERNEL);
    if (!my_device->buffer) {
        ret = -ENOMEM;
        goto err_dev;
    }

    // Initialize the cdev structure:
    cdev_init(&my_device->cdev, &my_fops);
    my_device->cdev.owner = THIS_MODULE;

    // Add cdev to kernel:
    ret = cdev_add(&my_device->cdev, dev_num, 1);
    if (ret < 0) {
        pr_err("mychardev: cannot add cdev\n");
        goto err_buf;
    }

    // Create /sys/class/myclass/ (udev uses this to create /dev/mychardev):
    dev_class = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(dev_class)) {
        ret = PTR_ERR(dev_class);
        goto err_cdev;
    }

    // Create /dev/mychardev:
    if (IS_ERR(device_create(dev_class, NULL, dev_num, NULL, DEVICE_NAME))) {
        ret = -EFAULT;
        goto err_class;
    }

    pr_info("mychardev: initialized. /dev/%s created.\n", DEVICE_NAME);
    return 0;

    // Error path: undo everything in reverse order (LIFO)
err_class:
    class_destroy(dev_class);
err_cdev:
    cdev_del(&my_device->cdev);
err_buf:
    kfree(my_device->buffer);
err_dev:
    kfree(my_device);
err_chrdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

static void __exit chardev_exit(void)
{
    device_destroy(dev_class, dev_num);
    class_destroy(dev_class);
    cdev_del(&my_device->cdev);
    kfree(my_device->buffer);
    kfree(my_device);
    unregister_chrdev_region(dev_num, 1);
    pr_info("mychardev: unloaded\n");
}

module_init(chardev_init);
module_exit(chardev_exit);
```

---

## 15. Rust in the Linux Kernel

### Concept: Why Rust in the Kernel?

Rust was added to the Linux kernel in version **6.1** (December 2022). The motivation:

```
C in the kernel:
  ✓ Decades of proven code
  ✗ Buffer overflows (most kernel CVEs!)
  ✗ Use-after-free bugs
  ✗ Race conditions easy to write
  ✗ NULL pointer dereferences

Rust in the kernel:
  ✓ Memory safety guaranteed by compiler
  ✓ No use-after-free (ownership system)
  ✓ No data races (Send/Sync types)
  ✓ Null safety (Option<T> instead of raw pointers)
  ✗ Learning curve
  ✗ Smaller ecosystem (kernel APIs still being wrapped)
```

### Rust Kernel Infrastructure

```
linux/rust/
├── alloc/          ← Custom allocator (uses kmalloc, not malloc)
├── kernel/         ← Safe Rust wrappers around kernel C APIs
│   ├── sync/       ← Mutex<T>, SpinLock<T>, RwLock<T> wrappers
│   ├── task.rs     ← Task/process abstraction
│   ├── error.rs    ← Error type wrapping Linux errno codes
│   ├── print.rs    ← pr_info!, pr_err! macros
│   ├── device.rs   ← Device abstraction
│   └── module.rs   ← module! macro
└── macros/         ← Procedural macros (module!, vtable!, etc.)
```

### Minimal Rust Kernel Module

```rust
// mymodule.rs — Minimal Rust kernel module
// File location: samples/rust/rust_minimal.rs (in kernel tree)
// Or your out-of-tree module

// The `module!` macro is the Rust equivalent of MODULE_LICENSE etc.
// It generates all the required C-compatible module metadata.

use kernel::prelude::*;

module! {
    type: RustMinimal,
    name: "rust_minimal",
    author: "Your Name",
    description: "Minimal Rust kernel module",
    license: "GPL",
}

// Our module's state structure.
// This is stored by the kernel and passed to our methods.
struct RustMinimal {
    numbers: Vec<i32>,
}

// Implement the `KernelModule` trait (like module_init + module_exit combined):
impl kernel::Module for RustMinimal {
    // Called on insmod:
    fn init(_name: &'static CStr, _module: &'static ThisModule)
        -> Result<Self>
    {
        // pr_info! is like pr_info() in C:
        pr_info!("Rust minimal module: loaded!\n");

        let mut numbers = Vec::try_with_capacity(3)?;
        // try_push = infallible allocation (returns Result):
        numbers.try_push(72)?;
        numbers.try_push(108)?;
        numbers.try_push(200)?;

        pr_info!("Rust minimal module: numbers = {:?}\n", numbers);

        Ok(RustMinimal { numbers })
    }
}

// When `RustMinimal` is dropped (rmmod), this runs:
impl Drop for RustMinimal {
    fn drop(&mut self) {
        pr_info!("Rust minimal module: unloaded! numbers were {:?}\n",
                 self.numbers);
        // numbers is automatically freed here — Rust ownership!
        // No kfree() needed. No memory leak possible.
    }
}
```

### Rust Character Device (More Complex)

```rust
// rust_chardev.rs — Rust character device driver
use kernel::{
    file::{self, File},
    io_buffer::{IoBufferReader, IoBufferWriter},
    miscdev,
    prelude::*,
    sync::Mutex,
};

module! {
    type: RustCharDev,
    name: "rust_chardev",
    author: "Kernel Dev",
    description: "Rust character device example",
    license: "GPL",
}

// Our device's shared state, protected by a Mutex:
struct DeviceData {
    contents: Vec<u8>,
}

struct RustCharDev {
    // miscdev registers a misc device (simpler than full chrdev):
    _dev: Pin<Box<miscdev::Registration<RustCharDev>>>,
}

// Safety: This is a file operation trait implementation.
// Rust's trait system enforces we implement only valid operations.
#[vtable]
impl file::Operations for RustCharDev {
    type Data = Arc<Mutex<DeviceData>>;
    type OpenData = Arc<Mutex<DeviceData>>;

    fn open(shared: &Arc<Mutex<DeviceData>>, _file: &File)
        -> Result<Arc<Mutex<DeviceData>>>
    {
        pr_info!("rust_chardev: opened\n");
        Ok(shared.clone())  // Return reference to shared state
    }

    fn read(
        data: ArcBorrow<'_, Mutex<DeviceData>>,
        _file: &File,
        writer: &mut impl IoBufferWriter,
        offset: u64,
    ) -> Result<usize> {
        let locked = data.lock();
        let offset = offset as usize;

        if offset >= locked.contents.len() {
            return Ok(0);  // EOF
        }

        let slice = &locked.contents[offset..];
        let len = writer.write_slice(slice)?;
        Ok(len)
    }

    fn write(
        data: ArcBorrow<'_, Mutex<DeviceData>>,
        _file: &File,
        reader: &mut impl IoBufferReader,
        _offset: u64,
    ) -> Result<usize> {
        let mut locked = data.lock();
        let bytes = reader.read_all()?;
        locked.contents = bytes;
        pr_info!("rust_chardev: received {} bytes\n", locked.contents.len());
        Ok(locked.contents.len())
    }
}

impl kernel::Module for RustCharDev {
    fn init(_name: &'static CStr, module: &'static ThisModule)
        -> Result<Self>
    {
        pr_info!("rust_chardev: initializing\n");

        let state = Arc::try_new(Mutex::new(DeviceData {
            contents: Vec::new(),
        }))?;

        Ok(RustCharDev {
            _dev: miscdev::Registration::new_pinned(
                fmt!("rust_chardev"),
                state,
                module,
            )?,
        })
    }
}
```

### Building Rust Modules

```bash
# Enable Rust support in kernel config:
make menuconfig
# → General setup → Rust support → Enable

# Or:
./scripts/config --enable RUST

# Verify Rust toolchain is correct:
make LLVM=1 rustavailable

# Build kernel with Rust:
make LLVM=1 -j$(nproc)

# Build a single Rust module:
make LLVM=1 M=samples/rust/

# For out-of-tree Rust module:
# Makefile:
#   obj-m := my_rust_module.o
#   my_rust_module-objs := my_rust_module.o
# (Build system handles .rs extension automatically)
make LLVM=1 -C /path/to/linux M=$(PWD) modules
```

---

## 16. printk and Logging System

### Concept: printk

`printk()` is the kernel's logging function. Unlike `printf()`:
- It is **interrupt-safe** (can be called from interrupt handlers)
- Output goes to the **kernel ring buffer** (viewed with `dmesg`)
- Has **log levels** (Emergency to Debug)
- Available **everywhere** in the kernel

```
LOG LEVELS (from most to least severe):
─────────────────────────────────────────────────────────────────────────────
LEVEL       MACRO        VALUE   WHEN TO USE
─────────────────────────────────────────────────────────────────────────────
EMERGENCY   pr_emerg()   0       System is unusable (imminent crash)
ALERT       pr_alert()   1       Action must be taken immediately
CRITICAL    pr_crit()    2       Critical condition
ERROR       pr_err()     3       Error condition (something failed)
WARNING     pr_warn()    4       Warning (possible problem)
NOTICE      pr_notice()  5       Normal but significant event
INFO        pr_info()    6       Informational messages
DEBUG       pr_debug()   7       Debug-only (compiled out unless DEBUG)
─────────────────────────────────────────────────────────────────────────────
```

### printk Usage

```c
// Basic usage:
pr_info("Driver loaded, version %d\n", VERSION);
pr_err("Failed to allocate memory: %d\n", ret);
pr_warn("Unexpected state: %u\n", state);
pr_debug("Loop iteration %d, value = %lld\n", i, value);

// With device context (preferred in drivers):
// dev_info/dev_err adds device name prefix automatically
dev_info(&pdev->dev, "probed successfully\n");
dev_err(&pdev->dev, "register_netdev failed: %d\n", err);
dev_warn(&pdev->dev, "deprecated feature used\n");

// Rate-limited (prevent log spam):
pr_info_ratelimited("Interrupt received, count=%d\n", count);

// Once only (print first occurrence only):
pr_info_once("Driver first used at %s\n", __func__);

// With hex dump (for debugging binary data):
print_hex_dump_bytes("data: ", DUMP_PREFIX_OFFSET, buf, len);

// Full hex dump with ASCII:
print_hex_dump(KERN_DEBUG, "buf: ", DUMP_PREFIX_ADDRESS,
               16, 1, buf, len, true);
```

### Controlling Log Level at Runtime

```bash
# See current log level (console_loglevel):
cat /proc/sys/kernel/printk
# Output: 4   4   1   7
# Fields: console_loglevel default_message_loglevel min_console_loglevel default_console_loglevel

# Temporarily show ALL messages (level 8 = show everything):
echo 8 > /proc/sys/kernel/printk

# Or:
dmesg -n 8

# Show only errors and above (level 4):
echo 4 > /proc/sys/kernel/printk

# Enable pr_debug() (normally compiled in but suppressed):
# At kernel command line: dyndbg="module mymodule +p"
# Or at runtime: see Section 17 (Dynamic Debug)
```

### Reading dmesg

```bash
dmesg                      # Print all messages
dmesg | tail -50           # Last 50 messages
dmesg -T                   # Human-readable timestamps
dmesg -w                   # Watch in real time (like tail -f)
dmesg --level=err,warn     # Show only errors and warnings
dmesg -c                   # Print and clear ring buffer
dmesg | grep "mydriver"    # Filter for your driver
```

---

## 17. Dynamic Debug

### Concept

Dynamic debug allows you to **enable/disable** specific `pr_debug()` / `dev_dbg()` calls at runtime — without recompiling. Each debug statement has an entry in debugfs that you can flip on/off.

```bash
# Enable dynamic debug (requires CONFIG_DYNAMIC_DEBUG=y):

# Enable ALL debug for your module:
echo "module mymodule +p" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for a specific file:
echo "file drivers/mydriver/core.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for a specific function:
echo "func my_driver_probe +p" > /sys/kernel/debug/dynamic_debug/control

# Enable and add file/line prefix to output:
echo "module mymodule +pflm" > /sys/kernel/debug/dynamic_debug/control
# p = enable, f = show function name, l = show line number, m = show module name

# Disable all debug for a module:
echo "module mymodule -p" > /sys/kernel/debug/dynamic_debug/control

# See all dynamic debug entries:
cat /sys/kernel/debug/dynamic_debug/control | grep mymodule
```

---

## 18. ftrace: Function Tracer

### Concept: What is ftrace?

**ftrace** is the Linux kernel's built-in tracing framework. It can:
- Trace **every function call** in the kernel
- Show function **call graphs** (who calls whom)
- Record **events** (scheduler switches, system calls, IRQs)
- Measure **function latency**

All without recompiling. All from debugfs.

```
ftrace ARCHITECTURE:
────────────────────────────────────────────────────────────

Every kernel function compiled with -pg has:
  my_func:
      call mcount       ← inserted by compiler
      ... actual code ...

ftrace hooks mcount() to:
  - Do nothing (default, zero overhead)
  - Record function name in ring buffer
  - Record call graph
  - Call kprobes
  - Measure time

RING BUFFER: Circular buffer in kernel memory.
  Your trace is stored here, then you read it from debugfs.
```

### ftrace Usage

```bash
# ── SETUP ────────────────────────────────────────────────────────────
# Mount debugfs if not already mounted:
mount -t debugfs none /sys/kernel/debug
cd /sys/kernel/debug/tracing

# ── LIST AVAILABLE TRACERS ───────────────────────────────────────────
cat available_tracers
# Output: function function_graph blk mmiotrace nop

# ── FUNCTION TRACER ──────────────────────────────────────────────────
# Trace every function call:
echo function > current_tracer
echo 1 > tracing_on
sleep 1
echo 0 > tracing_on
cat trace | head -50

# ── FILTER: Trace only specific functions ────────────────────────────
echo my_driver_* > set_ftrace_filter      # Glob pattern
echo do_page_fault >> set_ftrace_filter   # Add more functions
cat set_ftrace_filter                     # Verify filter

echo function > current_tracer
echo 1 > tracing_on
# ... trigger your code path ...
echo 0 > tracing_on
cat trace

# ── FUNCTION GRAPH TRACER (shows call tree with timing) ──────────────
echo function_graph > current_tracer
echo my_driver_probe > set_graph_function   # Only graph this function
echo 1 > tracing_on
# ... trigger probe ...
echo 0 > tracing_on
cat trace
# Output looks like:
#  1)               |  my_driver_probe() {
#  1)   0.875 us    |    dev_set_drvdata();
#  1)   2.140 us    |    request_irq();
#  1) + 15.820 us   |  }

# ── EVENT TRACING ────────────────────────────────────────────────────
# List available events:
cat available_events | grep sched

# Enable scheduler events:
echo 1 > events/sched/sched_switch/enable
echo 1 > events/sched/sched_wakeup/enable
echo 1 > tracing_on
sleep 0.1
echo 0 > tracing_on
cat trace

# Enable all events in a subsystem:
echo 1 > events/sched/enable
echo 1 > events/irq/enable

# ── TRACE MARKERS (annotate trace from userspace) ─────────────────────
# From userspace program:
echo "my test begin" > /sys/kernel/debug/tracing/trace_marker
# This marker appears in the ftrace output with timestamp!

# ── LATENCY TRACER ───────────────────────────────────────────────────
# Find max interrupt latency:
echo irqsoff > current_tracer
echo 1 > tracing_on
# ... run workload ...
echo 0 > tracing_on
cat trace  # Shows the longest IRQ-disabled period and why

# ── RESET ────────────────────────────────────────────────────────────
echo nop > current_tracer          # Disable tracing
echo > set_ftrace_filter           # Clear function filter
echo > trace                       # Clear trace buffer
```

### trace-cmd: Easier ftrace Interface

```bash
# Install:
sudo apt install trace-cmd

# Record function calls for 5 seconds:
sudo trace-cmd record -p function -F my_program

# Record events:
sudo trace-cmd record -e sched:sched_switch -e irq:irq_handler_entry sleep 1

# Show report:
trace-cmd report

# Record specific functions:
sudo trace-cmd record -p function -l my_driver_\* my_test_program
```

---

## 19. kprobes and kretprobes

### Concept

**kprobes** let you insert a callback at **any kernel instruction address** — without modifying source or rebooting. Like a software breakpoint that calls your function instead of stopping.

**kretprobes** additionally hook the **return** of a function (to measure execution time, capture return value, etc.).

```
NORMAL EXECUTION:               WITH KPROBE:
────────────────                ────────────────────────────────────
schedule():                     schedule():
  instruction A                   int3 (breakpoint) ← kprobe inserted
  instruction B                   ↓
  instruction C                 kprobe handler called:
  ...                             do_your_thing();
                                  ↓
                                  single-step original instruction A
                                  ↓
                                  instruction B
                                  instruction C
```

### kprobes in Code (C)

```c
// kprobe_example.c — Instrument kernel functions with kprobes

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>

MODULE_LICENSE("GPL");

// Pre-handler: called just BEFORE the probed function executes
static int pre_do_fork(struct kprobe *p, struct pt_regs *regs)
{
    // pt_regs contains CPU registers at probe point
    // For do_fork: first argument in rdi register
    pr_info("kprobe: do_fork called! flags=0x%lx\n", regs->di);
    return 0;  // 0 = continue, non-zero = abort
}

// Post-handler: called just AFTER the probed instruction
static void post_do_fork(struct kprobe *p, struct pt_regs *regs,
                         unsigned long flags)
{
    pr_info("kprobe: do_fork instruction completed\n");
}

// Define the kprobe:
static struct kprobe kp = {
    .symbol_name = "kernel_clone",  // Function to probe (new name for do_fork)
    .pre_handler = pre_do_fork,
    .post_handler = post_do_fork,
};

static int __init kprobe_init(void)
{
    int ret = register_kprobe(&kp);
    if (ret < 0) {
        pr_err("kprobe: register_kprobe failed: %d\n", ret);
        return ret;
    }
    pr_info("kprobe: planted at %p\n", kp.addr);
    return 0;
}

static void __exit kprobe_exit(void)
{
    unregister_kprobe(&kp);
    pr_info("kprobe: removed\n");
}

module_init(kprobe_init);
module_exit(kprobe_exit);
```

### kretprobe Example

```c
// kretprobe_example.c — Measure execution time of a kernel function

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>

MODULE_LICENSE("GPL");

// Per-instance data (stored for each active call):
struct my_data {
    ktime_t entry_time;
};

// Called on function ENTRY:
static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    struct my_data *data = (struct my_data *)ri->data;
    data->entry_time = ktime_get();
    return 0;
}

// Called on function RETURN:
static int return_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    struct my_data *data = (struct my_data *)ri->data;
    s64 delta_ns = ktime_to_ns(ktime_sub(ktime_get(), data->entry_time));

    // regs_return_value(regs) = the function's return value
    pr_info("kretprobe: vfs_read returned %ld, took %lld ns\n",
            regs_return_value(regs), delta_ns);
    return 0;
}

static struct kretprobe my_kretprobe = {
    .handler     = return_handler,
    .entry_handler = entry_handler,
    .data_size   = sizeof(struct my_data),
    .maxactive   = 20,              // Max simultaneous instances
    .kp.symbol_name = "vfs_read",
};

static int __init kretprobe_init(void)
{
    int ret = register_kretprobe(&my_kretprobe);
    if (ret < 0) {
        pr_err("register_kretprobe failed: %d\n", ret);
        return ret;
    }
    return 0;
}

static void __exit kretprobe_exit(void)
{
    unregister_kretprobe(&my_kretprobe);
}

module_init(kretprobe_init);
module_exit(kretprobe_exit);
```

---

## 20. eBPF for Kernel Observation

### Concept: What is eBPF?

**eBPF** (extended Berkeley Packet Filter) lets you run **sandboxed programs inside the kernel** without writing kernel modules. The kernel verifies eBPF programs are safe before running them.

```
Traditional approach:     eBPF approach:
  Write kernel module       Write eBPF program (C subset)
  Compile                   Compile with clang → eBPF bytecode
  insmod (can crash kernel) Kernel VERIFIER checks it's safe
  Test                      Load into kernel (JIT compiled)
  rmmod                     Safe: no invalid memory, no loops, terminates
                            Attach to: kprobe, tracepoint, syscall, network
```

### BCC Tools (Pre-built eBPF programs)

```bash
# Install BCC tools:
sudo apt install bpfcc-tools linux-headers-$(uname -r)

# trace system calls made by a process:
sudo opensnoop-bpfcc         # Trace open() calls
sudo execsnoop-bpfcc         # Trace exec() (new processes)
sudo tcpconnect-bpfcc        # Trace TCP connections
sudo biolatency-bpfcc        # Block I/O latency histogram
sudo funccount-bpfcc 'vfs_*' # Count all vfs_* function calls
sudo trace-bpfcc 'do_sys_open "%s", arg2'  # Trace with format string
```

### Writing eBPF in C with libbpf

```c
// minimal_ebpf.bpf.c — eBPF kernel-side program
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

// SEC() macro places program in correct ELF section
// "kprobe/sys_openat" attaches to sys_openat syscall
SEC("kprobe/sys_openat")
int trace_open(struct pt_regs *ctx)
{
    // bpf_get_current_pid_tgid() = (tgid << 32) | pid
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    char comm[16];
    bpf_get_current_comm(comm, sizeof(comm));

    // bpf_printk writes to /sys/kernel/debug/tracing/trace_pipe
    bpf_printk("PID %d (%s) called openat\n", pid, comm);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

```bash
# Compile eBPF program:
clang -O2 -target bpf -c minimal_ebpf.bpf.c -o minimal_ebpf.bpf.o

# Load and see output:
# (Use bpftool or a loader program)
bpftool prog load minimal_ebpf.bpf.o /sys/fs/bpf/my_prog \
    type kprobe

# Read output:
cat /sys/kernel/debug/tracing/trace_pipe
```

---

## 21. KASAN: Kernel Address Sanitizer

### Concept

**KASAN** catches memory errors in the kernel:
- **Use-after-free**: accessing memory after `kfree()`
- **Out-of-bounds**: writing past end of allocated buffer
- **Stack buffer overflow**: going past a stack variable
- **Global out-of-bounds**: past a global array

```
HOW KASAN WORKS:
────────────────────────────────────────────────────────────────

Every 8 bytes of real memory → 1 byte of "shadow memory"

Shadow byte meanings:
  0x00 = all 8 bytes accessible
  0x01 = only first 1 byte accessible (partial access)
  0xff = memory is poisoned (freed, out-of-bounds, etc.)

Before every memory access, compiler inserts a check:
  shadow = addr >> 3 + KASAN_SHADOW_OFFSET;
  if (*shadow != 0) → KASAN REPORT! BUG!

OVERHEAD:
  Memory: 1/8 extra for shadow (12.5%)
  CPU: ~2x slower (extra check per access)
  → Only enable in development/testing, not production
```

### KASAN in Action

```c
// This code would trigger KASAN:
static int __init bad_alloc_example(void)
{
    char *buf = kmalloc(10, GFP_KERNEL);

    // ❌ USE AFTER FREE:
    kfree(buf);
    buf[0] = 'A';    // KASAN detects this!

    // ❌ OUT OF BOUNDS:
    char *buf2 = kmalloc(10, GFP_KERNEL);
    buf2[15] = 'B';  // KASAN detects this!
    kfree(buf2);

    return 0;
}
```

### KASAN Report Output

```
==================================================================
BUG: KASAN: use-after-free in my_function+0x42/0x80
Write of size 1 at addr ffff8880048c1000 by task insmod/1234

CPU: 0 PID: 1234 Comm: insmod Tainted: G O
Call Trace:
 dump_stack+0x9a/0xd0
 print_address_description+0x74/0x260
 kasan_report+0x150/0x190
 my_function+0x42/0x80
 mymodule_init+0x25/0x40
 do_one_initcall+0x57/0x2e0

Allocated by task 1234:
 kmalloc+0x7f/0x90
 mymodule_init+0x15/0x40

Freed by task 1234:
 kfree+0xa8/0x2e0
 mymodule_init+0x20/0x40
==================================================================

How to read this:
  Line 1: Type (use-after-free) + function where it happened
  Line 2: Type of access (write), size (1 byte), address
  Call Trace: The backtrace showing how we got here
  Allocated by: Where was this memory allocated?
  Freed by: Where was it freed?
```

### Enabling KASAN

```bash
# In kernel config:
./scripts/config --enable KASAN
./scripts/config --enable KASAN_INLINE    # Better performance
./scripts/config --set-val KASAN_SHADOW_OFFSET ""  # Auto-computed

make olddefconfig
make -j$(nproc)
```

---

## 22. KFENCE: Kernel Electric Fence

### Concept

**KFENCE** is a lightweight (low-overhead!) alternative to KASAN. It:
- Uses a dedicated "electric fence" pool of pages
- Allocations near page boundaries → out-of-bounds → page fault → caught
- Randomly samples allocations (not all) → very low overhead
- Safe to run in **production** (unlike KASAN)

```
KFENCE POOL LAYOUT:
──────────────────────────────────────────────────────────────

  Guard page │  Object  │  Guard page │  Object  │  Guard page
  (no access)│ (valid)  │ (no access) │ (valid)  │ (no access)

If you write past "Object" → hit "Guard page" → page fault → KFENCE report
```

```bash
# Enable in config:
./scripts/config --enable KFENCE
./scripts/config --set-val KFENCE_SAMPLE_INTERVAL 100  # Sample every 100ms

# At runtime, force KFENCE for all allocations (testing):
echo 1 > /sys/kernel/debug/kfence/toggle
```

---

## 23. KCSAN: Kernel Concurrency Sanitizer

### Concept

**KCSAN** detects **data races** — when two threads access the same memory concurrently without proper synchronization.

```
DATA RACE EXAMPLE:
────────────────────────────────────────────────────────────────

CPU 0:                          CPU 1:
  counter++;                      counter++;
  // = read counter               // = read counter
  //   add 1                      //   add 1
  //   write counter              //   write counter

EXPECTED: counter increases by 2
ACTUAL: Both CPUs read same value, both write value+1 → counter increases by 1!

KCSAN catches this by:
  - Randomly setting watchpoints on memory accesses
  - If another CPU accesses the same memory concurrently → REPORT!
```

```bash
# Enable KCSAN:
./scripts/config --enable KCSAN

# It runs automatically — violations appear in dmesg:
# ==================================================================
# BUG: KCSAN: data-race in counter_increment / counter_increment
# Read of size 4 at ffff... by task A:
# Write of size 4 at ffff... by task B:
# ==================================================================
```

---

## 24. UBSAN: Undefined Behavior Sanitizer

### Concept

**UBSAN** catches C undefined behavior:
- Integer overflow (signed integers)
- Array index out of bounds
- Null pointer dereference
- Shift operations out of range
- Type misalignment

```c
// These would be caught by UBSAN:

int x = INT_MAX;
x++;              // ❌ Signed integer overflow (UB in C)

int arr[5];
arr[10] = 1;      // ❌ Out-of-bounds (UBSAN + KASAN)

int y = 1;
y << 50;          // ❌ Shift past type size

struct __attribute__((packed)) bad { int x; };
struct bad *p = (struct bad *)((char*)ptr + 1);
p->x = 5;         // ❌ Misaligned access
```

```bash
./scripts/config --enable UBSAN
./scripts/config --enable UBSAN_BOUNDS
./scripts/config --enable UBSAN_SHIFT
./scripts/config --enable UBSAN_INTEGER_WRAP
```

---

## 25. Lockdep: Lock Dependency Validator

### Concept

**Lockdep** tracks lock acquisition order to find potential **deadlocks** — even before they happen in production.

```
DEADLOCK SCENARIO:
────────────────────────────────────────────────────────────────

CPU 0:                          CPU 1:
  lock(A)                         lock(B)
  ...                             ...
  lock(B) ← WAITS for CPU 1       lock(A) ← WAITS for CPU 0
  (CPU 0 holds A, wants B)        (CPU 1 holds B, wants A)
  DEADLOCK!

LOCKDEP DETECTION:
  Lockdep sees: "thread X: acquired A, then acquired B"
  Later sees:   "thread Y: acquired B, then tried to acquire A"
  Conclusion:   "CIRCULAR DEPENDENCY! Potential deadlock!"
  Reports it IMMEDIATELY, before actual deadlock occurs.
```

### Lockdep Output

```
============================================
WARNING: possible circular locking dependency detected
6.1.0 #1 Tainted: G
--------------------------------------------
swapper/0 is trying to acquire lock:
ffff888003a8c9a0 (&dev->mutex){+.+.}, at: device_del+0x7a/0x3c0

but task is already holding lock:
ffffffff82a5c200 (subsys mutex#3){+.+.}, at: bus_remove_device+0x5b/0x100

which lock already depends on the new lock.

the existing dependency chain (in reverse order) is:
-> #1 (subsys mutex#3) { ... }
-> #0 (&dev->mutex) { ... }

Possible unsafe locking scenario:
      CPU0                    CPU1
      ----                    ----
 lock(&dev->mutex);
                         lock(subsys mutex#3);
                         lock(&dev->mutex);
 lock(subsys mutex#3);
 *** DEADLOCK ***
```

### Lockdep Annotations in Code

```c
// When lockdep reports a false positive (you KNOW it's safe):
// Use lock_acquire() and lock_release() hints
// Or restructure to avoid the dependency

// Common annotations:
lockdep_assert_held(&my_lock);        // Assert lock is held here
lockdep_assert_irqs_disabled();        // Assert IRQs are off
lockdep_set_class(&lock, &lock_class); // Group related locks

// For nested locks that are really the same "class":
mutex_lock_nested(&parent->lock, LOCK_LEVEL_PARENT);
mutex_lock_nested(&child->lock, LOCK_LEVEL_CHILD);
```

---

## 26. RCU: Read-Copy-Update

### Concept: The Big Idea

**RCU** is the kernel's most powerful synchronization mechanism for **read-heavy** data structures. The key insight:

```
TRADITIONAL APPROACH (rwlock):
  Reader: acquire read-lock → read data → release read-lock
  Writer: acquire write-lock (blocks all readers!) → update → release
  PROBLEM: Writers block readers. Bad for performance.

RCU APPROACH:
  Reader: rcu_read_lock() → read data → rcu_read_unlock()
           NO ACTUAL LOCKING. Zero overhead for readers!
  Writer: (1) Make a COPY of the data structure
          (2) Modify the copy
          (3) Atomically swap pointer to new copy
          (4) Wait for all readers to finish (grace period)
          (5) Free the old version

RESULT:
  Readers: NEVER blocked, never wait, minimal overhead
  Writers: Can update without blocking readers
  Cost: Memory (old + new copy exist simultaneously during update)
```

```
RCU TIMELINE:
────────────────────────────────────────────────────────────────────────────

                    Old data   ←── reader 1 sees this
                       │
Writer:  Copy → Modify → Swap pointer
                                   New data ←── reader 2+ see this
                       │
                  Grace period (wait for reader 1 to finish)
                       │
                  Free old data (safe! reader 1 is gone)
```

### RCU in Code (C)

```c
// rcu_example.c — RCU for a shared pointer

#include <linux/rcupdate.h>
#include <linux/slab.h>
#include <linux/spinlock.h>

// Our data structure:
struct my_data {
    int value;
    struct rcu_head rcu;   // Required for RCU-protected structs
};

// The RCU-protected pointer:
static struct my_data __rcu *global_data;

// Reader: can run on any CPU, concurrently with writers
static int read_value(void)
{
    struct my_data *data;
    int val;

    rcu_read_lock();   // Mark beginning of RCU read-side critical section
                       // (disables preemption on non-preemptible kernel)

    // rcu_dereference: safe way to read RCU pointer
    // Adds memory barriers to prevent CPU reordering
    data = rcu_dereference(global_data);

    if (data)
        val = data->value;
    else
        val = -1;

    rcu_read_unlock();  // Mark end of RCU critical section

    return val;
}

// Callback: called when grace period ends (all readers gone)
static void free_old_data(struct rcu_head *head)
{
    struct my_data *data = container_of(head, struct my_data, rcu);
    kfree(data);
}

// Writer: updates the shared data
static void update_value(int new_value)
{
    struct my_data *new_data, *old_data;

    // Allocate and initialize new version:
    new_data = kmalloc(sizeof(*new_data), GFP_KERNEL);
    new_data->value = new_value;

    // Atomically swap the pointer:
    // rcu_assign_pointer adds write memory barrier
    old_data = rcu_dereference_protected(global_data, 1);
    rcu_assign_pointer(global_data, new_data);

    // Schedule freeing of old data after grace period:
    // call_rcu() = asynchronous (non-blocking)
    if (old_data)
        call_rcu(&old_data->rcu, free_old_data);

    // OR: synchronize_rcu() = synchronous (blocks until grace period done)
    // if (old_data) {
    //     synchronize_rcu();
    //     kfree(old_data);
    // }
}
```

---

## 27. Oops, Panic, and BUG() Analysis

### Concept: The Three Death Modes

```
BUG()                        OOPS                         PANIC
─────────────────────────────────────────────────────────────────────
Explicit assertion failure    Hardware exception           Fatal, unrecoverable
Written by developer          NULL deref, bad pointer      System must stop
"This should never happen"    Usually recoverable          Reboots if panic=1
Prints stack trace            Prints registers + stack     Prints everything
May or may not crash          Process killed or kernel     Machine dies
  (depending on context)        panics                      (or hangs)
```

### Anatomy of a Kernel Oops

```
Example Oops output:
────────────────────────────────────────────────────────────────────────────

BUG: kernel NULL pointer dereference, address: 0000000000000008
                                               ^^^^^^^^^^^^^^^^
                                               The BAD address accessed!

#PF: supervisor write access in kernel mode
#PF: error_code(0x0002) - not-present page

CPU: 1 PID: 2345 Comm: test_prog Not tainted 6.1.0
RIP: 0010:my_driver_write+0x42/0xa0 [mydriver]
     ^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^
     CS    Function + offset         Module name

Code: 48 89 e5 48 8b 45 f8 48 8b 40 08 48 89 ...
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      Raw bytes of the faulting instruction + surrounding code

RSP: 0018:ffffc90001adbc80 EFLAGS: 00010286
RAX: 0000000000000000 RBX: ffff888003c41800 RCX: 0000000000000000
RDX: 000000000000000a RSI: 00007fff12345670 RDI: ffff888003c41800
                   ^ RAX = 0 = NULL pointer was being dereferenced

Call Trace:
 <TASK>
 vfs_write+0xb8/0x2a0
 ksys_write+0x55/0xc0
 __x64_sys_write+0x1d/0x30
 do_syscall_64+0x3d/0x90
 entry_SYSCALL_64_after_hwframe+0x46/0xb0

RIP: 0033:0x7f0000123456   ← Userspace that made the syscall
```

### How to Decode an Oops

```bash
# Method 1: addr2line — find source file and line
addr2line -e vmlinux 0xffffffff81234567
# Or for a module:
addr2line -e mydriver.ko 0x42   # offset from the oops

# Method 2: gdb
gdb vmlinux
(gdb) list *(my_driver_write+0x42)
# Shows the exact source line!

# Method 3: objdump — show disassembly
objdump -d --start-address=0xffffffff81234500 \
           --stop-address=0xffffffff812345c0 vmlinux

# Method 4: decode_stacktrace.sh (kernel script)
cat oops.txt | ./scripts/decode_stacktrace.sh vmlinux

# Method 5: faddr2line (for modules)
./scripts/faddr2line mydriver.ko my_driver_write+0x42
```

### Writing Defensive Code to Avoid Oops

```c
// ── ALWAYS CHECK RETURN VALUES ────────────────────────────────────
void *buf = kmalloc(size, GFP_KERNEL);
if (!buf) {
    pr_err("kmalloc failed!\n");
    return -ENOMEM;
}

// ── USE WARN_ON() FOR SOFT ASSERTIONS ─────────────────────────────
// Prints stack trace but doesn't kill the system:
if (WARN_ON(ptr == NULL))
    return -EINVAL;

// ── USE BUG_ON() FOR HARD ASSERTIONS ─────────────────────────────
// Kills the system if triggered (use sparingly):
BUG_ON(irqs_disabled() && !in_atomic());

// ── USE IS_ERR() FOR POINTER-ENCODED ERRORS ──────────────────────
// Many kernel functions return ERR_PTR(-ENOMEM) on error:
struct my_dev *dev = create_device();
if (IS_ERR(dev)) {
    int err = PTR_ERR(dev);  // Extract the error code
    pr_err("create_device failed: %d\n", err);
    return err;
}

// ── CHECK FOR NULL BEFORE DEREFERENCING ──────────────────────────
if (dev && dev->ops && dev->ops->probe)
    dev->ops->probe(dev);

// ── USE container_of SAFELY ──────────────────────────────────────
// container_of(ptr, type, member) — derive enclosing structure
struct my_dev *dev = container_of(work, struct my_dev, work_item);
```

### Common Oops Causes and Fixes

```
OOPS SIGNATURE              LIKELY CAUSE                    FIX
────────────────────────────────────────────────────────────────────────────
NULL pointer @ 0x00000008   Struct member access via NULL   Check pointer before use
NULL pointer @ 0x00000000   Direct NULL dereference          Add null check
Bad address (0xdead...)      Use after free (poisoned mem)   Use KASAN to find UAF
Bad address (random high)    Stack corruption / overflow      Stack canaries, KASAN
Kernel BUG at file:line      BUG() / BUG_ON() triggered       Fix the condition
divide error: 0000           Division by zero                 Check divisor
general protection fault     Unaligned access / bad segment   Check pointer math
stack smashing detected      Stack buffer overflow             KASAN, bounds checking
────────────────────────────────────────────────────────────────────────────
```

---

## 28. dmesg: Reading the Kernel Ring Buffer

### The Ring Buffer

```
KERNEL RING BUFFER:
──────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────┐
│                  Ring Buffer (size: ~256KB default)     │
│                                                        │
│  [  0.000000] Booting Linux 6.1.0                      │
│  [  0.001234] ACPI: LAPIC (id: 0)                      │
│  [  0.123456] pci 0000:00:01.0: found device           │
│  [  1.234567] eth0: Link up (1000Mbps)                 │
│  [  5.678901] mydriver: probed successfully            │
│  [ 42.123456] WARNING: possible circular locking...    │
│  [999.999999] ← oldest messages get overwritten        │
└────────────────────────────────────────────────────────┘
            ↑
         printk() writes here from anywhere in kernel
         dmesg reads this buffer
```

### dmesg Mastery

```bash
# ── BASIC USAGE ──────────────────────────────────────────────────────
dmesg                          # Print entire ring buffer
dmesg | less                   # Paginated view
dmesg -T                       # Human-readable timestamps
dmesg -H                       # Human-readable (color + timestamps)
dmesg -w                       # Live follow mode (like tail -f)
dmesg -c                       # Print and clear buffer
dmesg -C                       # Clear buffer silently

# ── FILTERING ─────────────────────────────────────────────────────────
dmesg --level=err              # Only errors
dmesg --level=err,warn,notice  # Errors + warnings + notices
dmesg -f kern                  # Kernel facility only
dmesg | grep -i "mydriver"     # Text filter

# ── TIMESTAMPS ────────────────────────────────────────────────────────
# Kernel timestamps are seconds since boot:
# [  42.123456] = 42 seconds after boot

# Convert to absolute time with -T:
dmesg -T | grep "mydriver"

# ── PERSISTENCE ───────────────────────────────────────────────────────
# By default, dmesg is lost on reboot.
# Enable persistent logging:
# systemd-journald (reads dmesg): journalctl -k
# Or enable pstore (kernel-level persistence to flash/RAM):
./scripts/config --enable PSTORE
./scripts/config --enable PSTORE_RAM

# ── RING BUFFER SIZE ──────────────────────────────────────────────────
# At kernel command line:
# log_buf_len=16M   → 16MB ring buffer (useful for verbose debugging)

# At runtime:
dmesg --buffer-size 8192
```

---

## 29. sysfs, procfs, and debugfs

### Three Virtual Filesystems

```
FILESYSTEM   MOUNT POINT              PURPOSE
─────────────────────────────────────────────────────────────────────────────
procfs       /proc                    Process information, kernel parameters
sysfs        /sys                     Device model, kobjects, hardware topology
debugfs      /sys/kernel/debug        Debugging interface (ftrace lives here)
─────────────────────────────────────────────────────────────────────────────

These are NOT real filesystems (no disk). They are:
  - Kernel data structures exposed as files
  - Read/write to a "file" → calls a kernel function
  - Perfect for debugging: expose internal state without recompiling
```

### Creating procfs Entries

```c
// procfs_example.c — Expose driver state via /proc/mydriver

#include <linux/proc_fs.h>
#include <linux/seq_file.h>

static int my_state = 42;
static struct proc_dir_entry *proc_entry;

// Called when user reads /proc/mydriver:
static int mydriver_show(struct seq_file *m, void *v)
{
    seq_printf(m, "Driver state: %d\n", my_state);
    seq_printf(m, "Version: 1.0\n");
    return 0;
}

// seq_open hooks our show function:
static int mydriver_open(struct inode *inode, struct file *file)
{
    return single_open(file, mydriver_show, NULL);
}

static const struct proc_ops mydriver_proc_ops = {
    .proc_open    = mydriver_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static int __init mydriver_init(void)
{
    // Create /proc/mydriver:
    proc_entry = proc_create("mydriver", 0444, NULL, &mydriver_proc_ops);
    if (!proc_entry)
        return -ENOMEM;
    return 0;
}

static void __exit mydriver_exit(void)
{
    proc_remove(proc_entry);
}
```

### Creating debugfs Entries

```c
// debugfs_example.c — Expose variables via /sys/kernel/debug/mydriver/

#include <linux/debugfs.h>

static struct dentry *debug_dir;    // Our directory
static u32 debug_counter = 0;
static char debug_message[256] = "hello";

static int __init debugfs_init(void)
{
    // Create /sys/kernel/debug/mydriver/:
    debug_dir = debugfs_create_dir("mydriver", NULL);
    if (IS_ERR(debug_dir))
        return PTR_ERR(debug_dir);

    // Create /sys/kernel/debug/mydriver/counter (read/write u32):
    debugfs_create_u32("counter", 0644, debug_dir, &debug_counter);

    // Create /sys/kernel/debug/mydriver/message (read/write string):
    debugfs_create_str("message", 0644, debug_dir, &debug_message[0]);

    // Create /sys/kernel/debug/mydriver/regs (custom file):
    // Use debugfs_create_file() for complex read/write behavior

    return 0;
}

static void __exit debugfs_exit(void)
{
    debugfs_remove_recursive(debug_dir);
}

// Usage from shell:
// cat /sys/kernel/debug/mydriver/counter   → reads debug_counter
// echo 100 > /sys/kernel/debug/mydriver/counter  → sets debug_counter=100
```

### sysfs Attributes

```c
// sysfs_example.c — Driver attribute in /sys/class/myclass/mydev/

#include <linux/device.h>
#include <linux/sysfs.h>

// Show function: called on 'cat /sys/class/myclass/mydev/my_attr'
static ssize_t my_attr_show(struct device *dev,
                             struct device_attribute *attr, char *buf)
{
    return sysfs_emit(buf, "42\n");
}

// Store function: called on 'echo value > /sys/.../my_attr'
static ssize_t my_attr_store(struct device *dev,
                              struct device_attribute *attr,
                              const char *buf, size_t count)
{
    int val;
    if (kstrtoint(buf, 10, &val))   // Parse integer safely
        return -EINVAL;
    pr_info("Received: %d\n", val);
    return count;
}

// DEVICE_ATTR(name, permissions, show_fn, store_fn)
static DEVICE_ATTR_RW(my_attr);   // Read-write attribute
// Or: DEVICE_ATTR_RO(my_attr)    // Read-only
// Or: DEVICE_ATTR_WO(my_attr)    // Write-only
```

---

## 30. perf: Performance Analysis

### Concept: What is perf?

**perf** is Linux's performance analysis tool. It uses **hardware performance counters** (PMU) in the CPU to measure:
- CPU cycles, instructions, cache misses
- Branch mispredictions  
- Context switches, page faults
- Any kernel/user function's execution count and time

```bash
# ── INSTALL ───────────────────────────────────────────────────────────
sudo apt install linux-perf   # Debian
# OR: perf is in linux source: tools/perf/

# ── SYSTEM-WIDE STATISTICS ───────────────────────────────────────────
sudo perf stat ls
# Output:
#    0.82 msec task-clock    # How long the CPU was busy
#       1 context-switches
#   1,234 instructions       # Total CPU instructions executed
#     456 cycles             # Total CPU cycles
#   0.271 insns per cycle    # IPC (higher is better)

# ── PROFILING: Find which functions use the most CPU ──────────────────
sudo perf record -g ./my_program    # -g = collect call graphs
sudo perf report                     # Interactive report

# ── PROFILING THE KERNEL ──────────────────────────────────────────────
sudo perf record -a -g sleep 5      # Profile entire system for 5s
sudo perf report                     # See top functions

# ── TRACING KERNEL FUNCTIONS ──────────────────────────────────────────
sudo perf trace ./my_program         # Trace syscalls (like strace)
sudo perf trace -e net:*             # Trace network events

# ── COUNTING EVENTS ───────────────────────────────────────────────────
sudo perf stat -e cache-misses,cache-references,instructions ./prog
sudo perf stat -e L1-dcache-load-misses ./prog   # L1 cache miss rate

# ── FLAME GRAPHS ──────────────────────────────────────────────────────
sudo perf record -F 999 -a -g -- sleep 10
sudo perf script | FlameGraph/stackcollapse-perf.pl | \
    FlameGraph/flamegraph.pl > flame.svg
```

---

## 31. Crash Dump Analysis with kdump + crash

### Concept: kdump

**kdump** captures a kernel crash dump when the system panics. Then you analyze it offline with the `crash` tool — like doing a postmortem on a dead kernel.

```
NORMAL BOOT:                    KERNEL PANICS:
  Kernel 1 (production)           Kernel 1 DIES
                                     ↓
                                  kexec boots Kernel 2 (capture kernel)
                                  (was pre-loaded in reserved memory)
                                     ↓
                                  Kernel 2 dumps Kernel 1's memory to disk
                                  (/var/crash/vmcore)
                                     ↓
                                  crash tool analyzes vmcore offline
```

```bash
# ── SETUP kdump ───────────────────────────────────────────────────────
sudo apt install kdump-tools linux-crashdump crash

# Reserve memory for capture kernel:
# In /etc/default/grub:
# GRUB_CMDLINE_LINUX="crashkernel=256M"
sudo update-grub
sudo reboot

# Verify kdump is ready:
kdump-config show
cat /proc/iomem | grep "Crash kernel"

# ── FORCE A CRASH (for testing kdump) ────────────────────────────────
echo 1 > /proc/sys/kernel/sysrq
echo c > /proc/sysrq-trigger      # Force kernel panic!
# Machine reboots, dumps to /var/crash/

# ── ANALYZE WITH crash ────────────────────────────────────────────────
sudo crash /usr/lib/debug/boot/vmlinux-6.1.0 /var/crash/202412*/vmcore

# Inside crash:
crash> bt                # Backtrace of crashed thread
crash> bt -a             # Backtrace of all threads
crash> ps               # Process list at time of crash
crash> log              # Print kernel log (dmesg before crash)
crash> files            # Open files
crash> vm               # Virtual memory info
crash> struct task_struct ffff888... # Inspect struct
crash> dis panic        # Disassemble panic function
crash> help             # All available commands
```

---

## 32. trace-cmd and kernelshark

```bash
# ── trace-cmd: command-line ftrace frontend ───────────────────────────

# Record scheduler events for 5 seconds:
sudo trace-cmd record -e sched:sched_switch -e sched:sched_wakeup \
    -e irq:irq_handler_entry sleep 5

# Show text report:
trace-cmd report | head -100

# ── kernelshark: GUI visualization of trace data ──────────────────────
sudo apt install kernelshark
kernelshark trace.dat    # Opens GUI timeline of recorded events
```

---

## 33. Kernel Testing Frameworks: KUnit and kselftest

### KUnit: Unit Testing Inside the Kernel

```
Concept: KUnit
  Like JUnit/pytest but for kernel code.
  Tests run INSIDE the kernel (as a module or built-in).
  No userspace needed. Catches regressions in core functions.
```

```c
// my_driver_test.c — KUnit tests for your driver

#include <kunit/test.h>
#include "mydriver.h"

// A test case:
static void test_parse_header_valid(struct kunit *test)
{
    struct my_header hdr;
    int ret;

    ret = parse_header(&hdr, valid_data, sizeof(valid_data));

    // KUNIT_EXPECT_* = soft assertion (test continues on failure)
    KUNIT_EXPECT_EQ(test, ret, 0);
    KUNIT_EXPECT_EQ(test, hdr.version, 1);
    KUNIT_EXPECT_STREQ(test, hdr.name, "expected_name");
}

static void test_parse_header_truncated(struct kunit *test)
{
    struct my_header hdr;
    int ret;

    ret = parse_header(&hdr, valid_data, 5);  // Too short!

    // KUNIT_ASSERT_* = hard assertion (test stops on failure)
    KUNIT_ASSERT_EQ(test, ret, -EINVAL);
}

// Test suite definition:
static struct kunit_case mydriver_test_cases[] = {
    KUNIT_CASE(test_parse_header_valid),
    KUNIT_CASE(test_parse_header_truncated),
    {}  // Terminator
};

static struct kunit_suite mydriver_test_suite = {
    .name = "mydriver",
    .test_cases = mydriver_test_cases,
};

kunit_test_suite(mydriver_test_suite);
MODULE_LICENSE("GPL");
```

```bash
# Run KUnit tests (requires CONFIG_KUNIT=y):

# Option 1: kunit.py tool (easiest):
./tools/testing/kunit/kunit.py run --filter_glob="mydriver*"

# Option 2: Run in QEMU directly:
# Build kernel with CONFIG_KUNIT=y and CONFIG_MY_DRIVER_KUNIT_TEST=y
# Boot in QEMU, test results appear in dmesg:
dmesg | grep -E "PASSED|FAILED|KUNIT"

# Option 3: Load as module:
sudo insmod mydriver_test.ko
dmesg | tail -30
```

### kselftest: Integration Testing

```bash
# kselftest = userspace test programs in tools/testing/selftests/

# Run all selftests:
sudo make -C tools/testing/selftests run_tests

# Run specific subsystem tests:
sudo make -C tools/testing/selftests/mm run_tests      # Memory tests
sudo make -C tools/testing/selftests/net run_tests     # Network tests
sudo make -C tools/testing/selftests/futex run_tests   # Futex tests

# Writing a kselftest:
# Create: tools/testing/selftests/mysubsystem/my_test.c
# Add to: tools/testing/selftests/mysubsystem/Makefile
#   TEST_PROGS := my_test
# Normal C userspace program that exercises kernel behavior
# Use ksft_print_msg(), ksft_test_result_pass(), ksft_exit_pass()
```

---

## 34. Syzkaller: Kernel Fuzzing

### Concept: What is Fuzzing?

**Fuzzing** = automatically generating random/mutated inputs to find bugs. **Syzkaller** fuzzes the **kernel's system call interface** — it calls syscalls with random arguments to find:
- Kernel panics
- Memory corruption (via KASAN)
- Deadlocks (via lockdep)
- Use-after-free bugs

```
SYZKALLER ARCHITECTURE:
────────────────────────────────────────────────────────────────

  syz-manager (host)
      │
      ├── Generates syscall programs (grammar-based, not random)
      │   e.g.: socket() → bind() → listen() → accept() → ...
      │
      ├── Runs QEMU VMs with kernel-under-test
      │
      ├── Loads syz-executor into VM
      │
      └── VM runs syscall programs, reports crashes back to manager
              │
              ↓ If crash detected:
              Minimize the reproducer
              Save crash report
              Report to kernel developers
```

```bash
# Install syzkaller (complex — brief overview):
go install github.com/google/syzkaller/syz-manager@latest

# Syzkaller needs: QEMU + KASAN + KCOV (Coverage instrumentation)
./scripts/config --enable KCOV
./scripts/config --enable KASAN

# Configuration file (syzkaller.cfg):
# {
#   "target": "linux/amd64",
#   "http": "127.0.0.1:56741",
#   "workdir": "/tmp/syzkaller-work",
#   "kernel_obj": "/path/to/linux",
#   "image": "/path/to/debian.img",
#   "kernel_src": "/path/to/linux",
#   "syzkaller": "/path/to/syzkaller",
#   "procs": 4,
#   "type": "qemu",
#   "vm": { "count": 2, "kernel": "/path/to/bzImage" }
# }

syz-manager -config syzkaller.cfg
# Open http://127.0.0.1:56741 in browser to see status
```

---

## 35. Submitting Patches: The Kernel Workflow

```
THE LINUX PATCH SUBMISSION PIPELINE:
─────────────────────────────────────────────────────────────────────────────

  Your code change
       │
       ▼
  git format-patch -1              # Create .patch file from last commit
       │
       ▼
  ./scripts/checkpatch.pl my.patch # Validate style (MANDATORY!)
       │
       ├── ERRORS? Fix them. Kernel has STRICT coding style.
       │
       └── OK ────────────────────────────────────────────────────────→
                                                                        │
  ./scripts/get_maintainer.pl my.patch  # Find who to send patch to    │
  ← Tells you: maintainer@, mailinglist@                               │
                                                                        │
  git send-email --to=maintainer@... \                                  │
                 --cc=list@vger.kernel.org \                            │
                 my.patch                                               │
       │                                                                │
       ▼
  Community review (1-4 weeks)
       │
       ├── "Acked-by: Maintainer" → Patch accepted into subsystem tree
       ├── "Reviewed-by: ..." → Code reviewed, no objection
       ├── "Tested-by: ..." → Tested on hardware
       └── "Changes requested" → Fix and resubmit (v2, v3, ...)
       │
       ▼
  Subsystem tree (e.g., net-next, drm-next)
       │
       ▼ (every merge window, ~10 weeks)
  Linus pulls subsystem trees into mainline linux-next
       │
       ▼
  YOUR CODE IS IN THE LINUX KERNEL!
```

### checkpatch.pl (Non-Negotiable)

```bash
# ALWAYS run before sending:
./scripts/checkpatch.pl --strict my.patch

# Check a C file directly:
./scripts/checkpatch.pl --no-tree -f drivers/mydriver/core.c

# Common errors:
#   ERROR: code indent should use tabs not spaces
#   WARNING: line over 80 characters
#   ERROR: trailing whitespace
#   WARNING: Missing a blank line after function declarations
#   ERROR: do not use C99 // comments (use /* */ instead — NO! C99 is OK now)
#   WARNING: Avoid CamelCase (use_underscores_instead)
```

### Kernel Coding Style Essentials

```c
// ── INDENTATION: TABS (not spaces), 8-space tab width ────────────────
if (condition)
	do_something();   // ← TAB, not spaces

// ── BRACES: Opening brace on same line (except functions) ─────────────
if (condition) {
	do_something();
}

void my_function(void)         // ← Opening brace on NEXT line for functions
{
	...
}

// ── LINE LENGTH: ~80 chars preferred, 100 max ─────────────────────────

// ── NAMING: lowercase_with_underscores (no CamelCase) ─────────────────
int my_variable;
void my_function(void);
struct my_struct { ... };
#define MY_MACRO 42

// ── STATIC FUNCTIONS: mark as static if only used in one file ─────────
static int helper_function(int x) { ... }

// ── ERROR HANDLING: goto for cleanup (C's RAII equivalent) ────────────
int my_init(void)
{
	int ret;

	ret = step_one();
	if (ret) goto err_step_one;

	ret = step_two();
	if (ret) goto err_step_two;

	return 0;

err_step_two:
	undo_step_one();
err_step_one:
	return ret;
}
```

---

## 36. Cognitive Strategies for Kernel Mastery

### Mental Models for Deep Understanding

```
MODEL 1: THE OWNERSHIP GRAPH
  For every kernel resource, ask:
    Who allocated it?  → Who must free it?
    Who can access it? → What lock protects it?
    What is its lifetime? → When can it be accessed safely?

  Draw this on paper for complex subsystems.
  Most kernel bugs violate this model.

MODEL 2: THE CONCURRENCY MATRIX
  List all functions that touch shared data.
  Ask: Can any two run simultaneously?
    ↓ Yes → What prevents data corruption?
    ↓ No  → Why? (single-threaded? lock? CPU affinity?)

MODEL 3: THE EXECUTION CONTEXT HIERARCHY
  Process context (can sleep, can kmalloc with GFP_KERNEL)
    └── Softirq context (cannot sleep, use GFP_ATOMIC)
          └── Hardirq context (cannot sleep, stack is tiny!)
                └── NMI context (almost nothing is safe!)

  Every kernel function must know its execution context.
  Wrong context = deadlock, corruption, or crash.

MODEL 4: THE REFERENCE COUNT INVARIANT
  refcount == 0 → object is DEAD (do not access!)
  refcount > 0 → object is ALIVE (safe to access while holding ref)
  
  get_device() / put_device()
  kobject_get() / kobject_put()
  These are the kernel's safe memory management pattern.
```

### Deliberate Practice Plan for Kernel Mastery

```
STAGE 1: FOUNDATION (Weeks 1-4)
  ─────────────────────────────
  ✓ Build the kernel from source daily
  ✓ Write 5 different kernel modules (char dev, procfs, sysfs, timer, workqueue)
  ✓ Trigger and decode 3 different Oops messages intentionally
  ✓ Use KASAN to find a self-inserted bug
  ✓ Trace a syscall through the kernel with ftrace from start to driver

STAGE 2: SUBSYSTEM DEPTH (Weeks 5-12)
  ────────────────────────────────────
  ✓ Pick ONE subsystem (driver model, memory management, or networking)
  ✓ Read its entire source code in Documentation/ first
  ✓ Read 10 recent patches in that subsystem (git log --oneline)
  ✓ Write a non-trivial driver or subsystem component
  ✓ Test with QEMU + KASAN + Lockdep + KUnit

STAGE 3: DEBUGGING MASTERY (Weeks 13-20)
  ────────────────────────────────────────
  ✓ Reproduce and fix a real CVE (from kernel security advisories)
  ✓ Use syzkaller to find a bug in your own driver
  ✓ Do a GDB live debug session — set breakpoints in scheduler
  ✓ Analyze a kdump from a real panic
  ✓ Optimize a kernel hot path using perf + flame graphs

STAGE 4: COMMUNITY (Weeks 21+)
  ────────────────────────────
  ✓ Submit your first patch (even a documentation fix counts)
  ✓ Review other people's patches on the mailing list
  ✓ Respond to review comments, iterate
  ✓ Build a reputation in a subsystem over months
```

### The Kernel Developer's Reading List

```
BOOKS (in order of reading):
  1. "Linux Device Drivers" 3rd ed — Corbet, Rubini, Kroah-Hartman
     (Free online: lwn.net/Kernel/LDD3/)
  2. "Understanding the Linux Kernel" 3rd ed — Bovet, Cesati
  3. "Linux Kernel Development" 3rd ed — Robert Love
  4. "Professional Linux Kernel Architecture" — Mauerer

ONLINE RESOURCES:
  1. LWN.net — The authoritative kernel news and deep-dives
  2. kernel.org/doc — Official documentation
  3. git.kernel.org — Read REAL patches from masters
  4. kernelnewbies.org — Beginner-friendly explanations
  5. Elixir (elixir.bootlin.com) — Cross-referenced kernel source

MAILING LISTS:
  1. linux-kernel@vger.kernel.org — Main list (high volume!)
  2. linux-drivers@vger.kernel.org — Driver discussions
  3. linux-mm@kvack.org — Memory management
  4. netdev@vger.kernel.org — Networking

TALKS:
  1. Greg Kroah-Hartman's kernel talks (YouTube)
  2. Linux Plumbers Conference recordings
  3. LCE (Linux Conf Europe) recordings
```

### Psychological Flow in Kernel Development

```
THE FLOW STATE FOR KERNEL WORK:
────────────────────────────────────────────────────────────────

1. SINGLE FILE FOCUS
   Close all unrelated tabs. Open only:
   - The source file you're changing
   - Its header file
   - One reference (Documentation/ or LWN article)
   
2. THE 25-MINUTE KERNEL SESSION
   Set timer: 25 minutes of pure kernel reading/coding.
   No interruptions. This is Pomodoro for deep systems work.
   After: 5 min break (walk, stretch — kernel work is cognitively heavy)

3. EXPLAIN IT TO UNDERSTAND IT
   After reading a subsystem, write a one-page explanation
   as if teaching someone. Gaps in your explanation = gaps in understanding.
   (This is the Feynman Technique applied to kernel internals)

4. CHUNKING KERNEL CONCEPTS
   The kernel is 30 million lines — you CANNOT read it all.
   Chunk by subsystem: "Today I understand slab allocator."
   Build a mental map of chunks: slab → buddy → VMAs → mmap.
   Each chunk becomes a fast-access node in your knowledge graph.

5. THE DEBUG JOURNAL
   Keep a log: "Bug: X. Hypothesis: Y. Test: Z. Result: W."
   After 20 entries, you will see YOUR PERSONAL BUG PATTERNS.
   Most kernel developers have 3-5 patterns they repeatedly make.
   Know yours. Fix them at the level of habit.
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    KERNEL DEV QUICK REFERENCE                               │
│                                                                             │
│  BUILD KERNEL:     make -j$(nproc) bzImage modules                         │
│  BUILD MODULE:     make M=drivers/mydir/ modules                           │
│  LOAD MODULE:      sudo insmod mymod.ko                                    │
│  UNLOAD MODULE:    sudo rmmod mymod                                        │
│  VIEW LOGS:        dmesg -wT                                               │
│  BOOT QEMU:        qemu-system-x86_64 -kernel bzImage -initrd init.cpio.gz │
│                    -append "console=ttyS0 nokaslr" -nographic -m 512M      │
│  GDB ATTACH:       gdb vmlinux → target remote :1234                       │
│  FUNCTION TRACE:   echo function > /sys/kernel/debug/tracing/current_tracer│
│  ENABLE DEBUG:     echo "module X +p" > .../dynamic_debug/control          │
│  CHECK STYLE:      ./scripts/checkpatch.pl --strict my.patch               │
│  GET MAINTAINER:   ./scripts/get_maintainer.pl my.patch                    │
│                                                                             │
│  MEMORY:    kmalloc() / kfree()    |  vmalloc() / vfree()                  │
│  LOCKING:   spin_lock() / unlock() |  mutex_lock() / unlock()              │
│  IRQ-SAFE:  spin_lock_irqsave()    |  spin_unlock_irqrestore()             │
│  RCU READ:  rcu_read_lock()        |  rcu_read_unlock()                    │
│  RCU WRITE: rcu_assign_pointer()   |  synchronize_rcu() / call_rcu()      │
│                                                                             │
│  pr_info("msg %d\n", val)    dev_err(&dev, "failed %d\n", ret)            │
│  WARN_ON(condition)           BUG_ON(fatal_condition)                      │
│  IS_ERR(ptr)  PTR_ERR(ptr)   ERR_PTR(-ENOMEM)                             │
│  container_of(ptr, type, member)   offsetof(type, member)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*"Every kernel expert was once a complete beginner who refused to stop debugging."*

*— The path from `insmod` to mainline contributor is built one oops at a time.*

**137KB · 3,646 lines · 36 sections** — here's what's inside, organized as your complete kernel development field manual:

---

### What's Covered

**Architecture & Source**
Kernel privilege rings, subsystem map, full source tree anatomy — know where everything lives before touching it.

**Build System**
Kbuild, Kconfig syntax, Makefile variables (`obj-$(CONFIG_*)` idiom), and every `make` target you'll ever need.

**The Master Decision Tree** (your original flowchart, expanded)
Each branch explains *why* you pick that strategy, with the full iterative workflow loop: edit → build → test → debug → repeat.

**QEMU + initramfs**
Complete walkthrough: build BusyBox statically, create CPIO archive, write the `/init` script, add your test program, boot in 2 seconds. Includes a `fast_test.sh` automation script.

**GDB Kernel Debugging**
Every command you need: breakpoints, backtrace, `lx-ps`, `lx-dmesg`, memory inspection, stepping, watchpoints, and how to handle KASLR correctly.

**Cross-Compilation → Pi 4B**
Full pipeline: `ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-`, module-only builds, SCP deploy, serial console wiring, and NFS root for rapid iteration.

**C Driver Examples**
A complete character device driver with `cdev`, `file_operations`, `copy_to_user/from_user`, proper error-path `goto` cleanup, and `sysfs` class creation.

**Rust Kernel Modules**
The `module!` macro, `KernelModule` trait, ownership-based cleanup via `Drop`, and a Rust character device with `Arc<Mutex<T>>` shared state.

**All Sanitizers**: KASAN (with oops anatomy), KFENCE, KCSAN, UBSAN — what each catches, how to enable it, how to read the output.

**Lockdep, RCU, ftrace, kprobes, eBPF, perf, kdump/crash, KUnit, kselftest, Syzkaller** — each with code examples and shell commands.

**Patch Submission Workflow**
`checkpatch.pl` → `get_maintainer.pl` → `git send-email` → review cycle → mainline.

**Cognitive Mastery Section**
Four mental models (ownership graph, concurrency matrix, execution context hierarchy, refcount invariant), a staged 21-week deliberate practice plan, and the Feynman/Pomodoro/debug-journal techniques adapted specifically for kernel work.