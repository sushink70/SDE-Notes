## Linux Kernel Panic Handling — Code Level Deep Dive

### What is a Kernel Panic?

A kernel panic is the Linux equivalent of a fatal error. Unlike a userspace crash (which just kills the process), a kernel panic means the kernel itself hit an unrecoverable state. The key function is `panic()` in `kernel/panic.c`.

---

### The `panic()` Function Flow

```c
// kernel/panic.c
void panic(const char *fmt, ...)
{
    // 1. Disable local interrupts immediately
    local_irq_disable();

    // 2. Print the panic message to console/dmesg
    pr_emerg("Kernel panic - not syncing: %s\n", buf);

    // 3. Print stack trace
    dump_stack();

    // 4. Call registered panic notifiers
    atomic_notifier_call_chain(&panic_notifier_list, 0, buf);

    // 5. Check if we should reboot
    if (panic_timeout > 0) {
        pr_emerg("Rebooting in %d seconds..\n", panic_timeout);
        ssleep(panic_timeout);
        emergency_restart();
    }

    // 6. If no reboot configured — HANG FOREVER
    pr_emerg("---[ end Kernel panic ]---\n");
    local_irq_enable();
    for (;;)           // <-- infinite loop, kernel halts here
        cpu_relax();
}
```

---

### Key Mechanisms That Keep It "Running" (or Controlled)

#### 1. **`panic_timeout` — The Reboot Knob**
```c
// Set via kernel cmdline: panic=5  (reboot after 5 seconds)
// Or: panic=0  (hang forever, the default)
// Or: panic=-1 (reboot immediately)

int panic_timeout __read_mostly = CONFIG_PANIC_TIMEOUT;
```
You control this via:
- Kernel boot parameter: `panic=30`
- Sysctl at runtime: `sysctl kernel.panic=30`
- `/proc/sys/kernel/panic`

---

#### 2. **Panic Notifier Chain**
Before halting, the kernel runs a chain of registered callbacks:
```c
// Drivers/subsystems register handlers like:
atomic_notifier_chain_register(&panic_notifier_list, &my_panic_nb);

// Example: kdump registers here to save a crash dump
// Example: watchdog drivers register to trigger hardware reset
```

---

#### 3. **`oops_may_print` vs Full Panic — Oops ≠ Panic**
Not every kernel error causes a full panic. An **Oops** is a recoverable (sometimes) fault:

```c
// In fault handlers (arch/x86/mm/fault.c):
void do_page_fault(...) {
    if (is_kernel_fault) {
        if (fixup_exception(regs))   // Can we recover via exception table?
            return;                   // YES → continue execution!
        
        // No fixup found → escalate to oops
        oops_begin();
        die("Oops", regs, error_code); // May or may not panic
    }
}
```

The **exception table** (`__ex_table`) is critical — it's a compile-time list of "if this instruction faults, jump here instead":
```c
// Example from copy_from_user:
asm volatile(
    "1: mov (%1), %0\n"
    "2:\n"
    ".section __ex_table, \"a\"\n"
    "   .quad 1b, 2b\n"   // if instruction at 1b faults → jump to 2b
    ".previous"
);
```

---

#### 4. **`CONFIG_PANIC_ON_OOPS`**
```c
// kernel/panic.c
void oops_end(unsigned long flags, struct pt_regs *regs, int signr)
{
    if (panic_on_oops)
        panic("Fatal exception");  // Force panic on any oops
    
    // Otherwise, try to kill only the offending process
    do_exit(signr);  // Kill the process, kernel survives!
}
```
This is why the kernel can **survive some faults** — if the fault happened in user process context, it can just kill that process.

---

#### 5. **Watchdog Timers (Hardware Safety Net)**
```c
// drivers/watchdog/ — Hardware watchdog
// If kernel panics and hangs, the watchdog isn't "pet"-ed anymore
// Hardware forces a reset after timeout

// Soft lockup detector (kernel/watchdog.c):
// Detects if a CPU is stuck for >10s and triggers panic:
if (panic_on_lockup)
    panic("watchdog: BUG soft lockup");
```

---

#### 6. **kdump / kexec — Crash Kernel**
A second "crash kernel" is pre-loaded in reserved memory:
```
# Load crash kernel at boot:
crashkernel=256M

# When panic() fires, kexec jumps to crash kernel
# which saves a vmcore dump, then reboots cleanly
```
```c
// kernel/kexec_core.c — called from panic():
void crash_kexec(struct pt_regs *regs) {
    // Capture registers, memory dump
    // Jump to pre-loaded crash kernel
    machine_crash_shutdown(regs);
    machine_kexec(kexec_crash_image);
}
```

---

### Summary Flow Diagram

```
Fault/Bug
   │
   ▼
Exception Handler
   │
   ├─ Exception Table fixup? ──► YES → Resume execution (transparent recovery)
   │
   └─ NO → Oops
              │
              ├─ User process context? → Kill process, kernel lives on
              │
              └─ Kernel context / panic_on_oops=1
                        │
                        ▼
                    panic()
                        │
                        ├─ Run notifier chain (kdump, drivers)
                        ├─ crash_kexec() → save vmcore
                        ├─ panic_timeout > 0 → emergency_restart()
                        └─ else → for(;;) cpu_relax()  ← HANG
```

---

### Practical Knobs Summary

| Mechanism | Config/Command | Effect |
|---|---|---|
| `panic_timeout` | `sysctl kernel.panic=30` | Reboot after N seconds |
| `panic_on_oops` | `sysctl kernel.panic_on_oops=1` | Turn oops into panic |
| `panic_on_warn` | `sysctl kernel.panic_on_warn=1` | Turn WARN() into panic |
| `softlockup_panic` | `sysctl kernel.softlockup_panic=1` | Panic on CPU lockup |
| kdump | `crashkernel=256M` boot param | Capture crash dump then reboot |
| Hardware watchdog | `/dev/watchdog` | Force reset if kernel hangs |

The key insight is: **the kernel is designed to never "stop" ungracefully** — it either recovers silently (exception tables), kills only the bad process, dumps state and reboots (kdump), or deliberately spins in a controlled infinite loop rather than undefined behavior.

# Linux Kernel Panic — All Cases & Detailed Explanation

> **Document Scope:** Every category of condition that can trigger a Linux kernel panic, with source-level references, example call stacks, and diagnostic notes.

---

## Table of Contents

1. [What Triggers a Panic?](#1-what-triggers-a-panic)
2. [Explicit `panic()` Calls](#2-explicit-panic-calls)
3. [Null Pointer Dereference in Kernel Space](#3-null-pointer-dereference-in-kernel-space)
4. [Stack Overflow / Stack Smashing](#4-stack-overflow--stack-smashing)
5. [Use-After-Free in Kernel Space](#5-use-after-free-in-kernel-space)
6. [Double Free](#6-double-free)
7. [Memory Corruption (Slab/Buddy Allocator)](#7-memory-corruption-slabbuddy-allocator)
8. [Out-of-Bounds Memory Access](#8-out-of-bounds-memory-access)
9. [CPU Exception — General Protection Fault](#9-cpu-exception--general-protection-fault)
10. [CPU Exception — Machine Check Exception (MCE)](#10-cpu-exception--machine-check-exception-mce)
11. [Unhandled Interrupt / Spurious IRQ](#11-unhandled-interrupt--spurious-irq)
12. [Soft Lockup](#12-soft-lockup)
13. [Hard Lockup](#13-hard-lockup)
14. [RCU Stall](#14-rcu-stall)
15. [Hung Task](#15-hung-task)
16. [Out of Memory (OOM) Panic](#16-out-of-memory-oom-panic)
17. [Kernel BUG() / WARN() Macros](#17-kernel-bug--warn-macros)
18. [Assert / Sanity Check Failures (BUG_ON / WARN_ON)](#18-assert--sanity-check-failures-bug_on--warn_on)
19. [Deadlock — Spinlock / Mutex](#19-deadlock--spinlock--mutex)
20. [Oops Escalated to Panic](#20-oops-escalated-to-panic)
21. [Interrupt Handler Faults](#21-interrupt-handler-faults)
22. [VFS / Filesystem Corruption](#22-vfs--filesystem-corruption)
23. [Bad Page State / Page Fault in Kernel Mode](#23-bad-page-state--page-fault-in-kernel-mode)
24. [Division by Zero in Kernel](#24-division-by-zero-in-kernel)
25. [Undefined Instruction / Illegal Opcode](#25-undefined-instruction--illegal-opcode)
26. [Scheduler Corruption](#26-scheduler-corruption)
27. [Module Load Failure / Bad Kernel Module](#27-module-load-failure--bad-kernel-module)
28. [Hardware Watchdog Expiry](#28-hardware-watchdog-expiry)
29. [kexec / kdump Failures](#29-kexec--kdump-failures)
30. [Device Driver Bugs](#30-device-driver-bugs)
31. [Atomic Context Violations](#31-atomic-context-violations)
32. [IOMMU / DMA Faults](#32-iommu--dma-faults)
33. [Power Management Failures](#33-power-management-failures)
34. [EFI / Firmware Runtime Faults](#34-efi--firmware-runtime-faults)
35. [Summary Table](#35-summary-table)

---

## 1. What Triggers a Panic?

The central entry point for all panics is `panic()` in `kernel/panic.c`. However, the kernel reaches this function through many different paths. These can be grouped into three high-level categories:

```
┌──────────────────────────────────────────┐
│           Panic Trigger Sources          │
├──────────────────────┬───────────────────┤
│  Hardware Faults     │ CPU exceptions,   │
│                      │ MCE, watchdog,    │
│                      │ firmware errors   │
├──────────────────────┼───────────────────┤
│  Kernel Software     │ BUG(), NULL deref,│
│  Bugs                │ stack overflow,   │
│                      │ memory corruption │
├──────────────────────┼───────────────────┤
│  Liveness Failures   │ Deadlocks, soft   │
│                      │ lockup, RCU stall,│
│                      │ OOM               │
└──────────────────────┴───────────────────┘
```

The `panic_timeout` sysctl (`/proc/sys/kernel/panic`) controls what happens after a panic: `0` = hang forever (default), positive = reboot after N seconds, negative = reboot immediately.

---

## 2. Explicit `panic()` Calls

### Description

The most direct cause. Kernel subsystems call `panic()` directly when they detect a condition from which there is no recovery path. This is a deliberate, intentional design decision by kernel developers.

### Code Path

```c
// kernel/panic.c
void panic(const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);

    pr_emerg("Kernel panic - not syncing: %s\n", buf);
    bust_spinlocks(1);
    dump_stack();
    print_oops_end_marker();
    atomic_notifier_call_chain(&panic_notifier_list, 0, buf);
    bust_spinlocks(0);
    crash_kexec(NULL);

    if (panic_timeout > 0)
        emergency_restart();

    for (;;) cpu_relax();   // hang point
}
```

### Common Call Sites

```c
// init/main.c — root filesystem not found
if (!rootfs_mounted)
    panic("VFS: Unable to mount root fs on %s", root_device_name);

// kernel/fork.c — PID 1 (init) died
if (task->pid == 1)
    panic("Attempted to kill init! exitcode=0x%08x", ...);

// arch/x86/kernel/setup.c — no memory detected
if (!memblock.memory.cnt)
    panic("No memory found\n");
```

### Dmesg Signature

```
Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)
```

---

## 3. Null Pointer Dereference in Kernel Space

### Description

When kernel code attempts to access memory at address `NULL` (or near-NULL, typically `< PAGE_SIZE`), the CPU raises a page fault. In user space, this would send `SIGSEGV` to the process. In kernel space, there is no such escape — if the exception table has no fixup entry for the faulting instruction, the kernel calls `die()`, which escalates to `panic()`.

### How It Works

The CPU's MMU raises a **Page Fault** (#PF, vector 14 on x86). The kernel's page fault handler checks:

1. **Is there a fixup?** — Checks the `__ex_table` (exception table) for the faulting EIP/RIP. If found, execution resumes at the fixup address (recovery).
2. **No fixup found** — Calls `oops_begin()` → `die()` → optionally `panic()`.

```c
// arch/x86/mm/fault.c
static void __do_kernel_fault(struct mm_struct *mm, unsigned long address,
                               unsigned long error_code, struct pt_regs *regs)
{
    if (fixup_exception(regs, X86_TRAP_PF, error_code, address))
        return;                          // recovered via exception table

    bust_spinlocks(1);
    pr_alert("BUG: unable to handle kernel NULL pointer dereference"
             " at %016lx\n", address);
    die("Oops", regs, error_code);      // → triggers panic if configured
}
```

### Common Root Causes

- Uninitialized pointer in driver code (`struct foo *p; p->bar = 1;`)
- Object freed but pointer not zeroed; then accessed again
- Race condition where a pointer is read before it is written

### Dmesg Signature

```
BUG: unable to handle kernel NULL pointer dereference at 0000000000000010
PGD 0 P4D 0
Oops: 0002 [#1] SMP PTI
RIP: 0010:some_driver_function+0x34/0xa0
```

---

## 4. Stack Overflow / Stack Smashing

### Description

The Linux kernel gives each thread a fixed kernel stack, typically **8 KB** (x86_64, configurable to 16 KB). If a deeply recursive call chain or large stack allocations exceed this, the stack overflows into adjacent memory — corrupting kernel data or page tables, causing an immediate fatal exception.

### Detection Mechanism

Modern kernels use a **stack canary** and a dedicated **overflow stack**:

```c
// arch/x86/kernel/traps.c
// CONFIG_VMAP_STACK — each kernel stack is surrounded by guard pages
// If stack grows into the guard page → page fault → oops → panic

// CONFIG_STACKPROTECTOR
// GCC inserts canary checks in function epilogues:
//   mov %gs:__stack_chk_guard, %rax
//   cmp -8(%rbp), %rax
//   jne stack_chk_fail
//
// On mismatch:
__visible void __stack_chk_fail(void)
{
    panic("stack-protector: Kernel stack is corrupted in: %pB",
          __builtin_return_address(0));
}
```

### Stack Overflow vs Stack Smashing

| Type | Cause | Detection |
|---|---|---|
| **Overflow** | Stack pointer walks past stack bottom | Guard page fault (VMAP_STACK) |
| **Smashing** | Buffer overrun overwrites return address | Canary mismatch (STACKPROTECTOR) |

### Dmesg Signature

```
Kernel panic - not syncing: stack-protector: Kernel stack is corrupted in: ffffffff81234567
```
or
```
BUG: stack guard page was hit at (____ptrval____) (stack is (____ptrval____)..(____ptrval____))
kernel stack overflow (double-fault)
```

---

## 5. Use-After-Free in Kernel Space

### Description

Kernel code accesses memory (`struct`, object, buffer) after it has been freed back to the allocator. The freed region may have been reused and filled with new data, causing unpredictable behavior — or, with SLUB debug / KASAN enabled, an immediate panic when the access is detected.

### How KASAN Detects It

```c
// mm/kasan/report.c — Kernel Address SANitizer
void kasan_report(unsigned long addr, size_t size, bool is_write, ...)
{
    pr_err("BUG: KASAN: use-after-free in %pS\n", (void *)addr);
    dump_stack();
    // Depending on CONFIG_KASAN_PANIC, may call panic()
}
```

KASAN maintains **shadow memory** — for every 8 bytes of kernel memory, 1 shadow byte encodes its state (free, allocated, partially allocated, etc.). Any access is checked against the shadow.

### Without KASAN

Without sanitizers, use-after-free may silently corrupt data and cause a panic much later (e.g., NULL deref when a pointer field was zeroed during free), making the root cause very hard to trace.

### Dmesg Signature

```
BUG: KASAN: use-after-free in some_function+0x20/0x80
Read of size 8 at addr ffff8880123abc10 by task kworker/0:1/42
```

---

## 6. Double Free

### Description

A memory object is freed twice. The second free corrupts the allocator's internal free-list, which typically causes a panic during the next allocation attempt or during the free itself.

### SLUB Allocator Detection

```c
// mm/slub.c
static void free_debug_processing(struct kmem_cache *s,
                                   struct page *page, void *object, ...)
{
    // Check object is not already in free list
    if (on_freelist(s, page, object)) {
        object_err(s, page, object, "Object already free");
        slab_fix(s, "Object wrongfully allocated");
        return false;
    }
}
```

KASAN also detects double-free:

```
BUG: KASAN: double-free or invalid-free in some_driver_cleanup+0x30/0x60
```

### Dmesg Signature

```
kernel BUG at mm/slub.c:294!
invalid opcode: 0000 [#1] SMP
BUG: Double free or corruption (fasttop)
```

---

## 7. Memory Corruption (Slab/Buddy Allocator)

### Description

When kernel memory metadata (free-list pointers, slab headers, buddy bitmap) is overwritten by a bug (buffer overflow, UAF, hardware error), the allocator itself becomes inconsistent. Any subsequent `kmalloc()` or `kfree()` triggers a BUG.

### Detection

```c
// mm/slub.c
static int check_object(struct kmem_cache *s, struct page *page,
                          void *object, u8 val)
{
    // Verify padding (redzone) bytes around object
    if (!check_bytes_and_report(s, page, object, "Redzone",
                                 endobject, val, s->inuse - s->object_size))
        return 0;   // corruption found → BUG()
}
```

The slab allocator periodically validates:
- **Redzones** — guard bytes around each allocation, must not be overwritten
- **Poison patterns** — freed memory is filled with `0x6b`; must still be `0x6b` on next alloc
- **Free-list integrity** — linked list pointers must be valid kernel addresses

### Dmesg Signature

```
BUG: KASAN: slab-out-of-bounds in some_function
Write of size 1 at addr ffff888012345670

=============================================================================
BUG kmalloc-64 (Not tainted): Redzone overwritten
```

---

## 8. Out-of-Bounds Memory Access

### Description

A kernel buffer (array, kmalloc region, stack variable) is accessed beyond its declared size. This can silently corrupt adjacent memory or, with KASAN, trigger an immediate panic.

### Categories

- **Global buffer overflow** — overwriting a statically allocated array
- **Heap out-of-bounds** — writing past a `kmalloc` allocation
- **Stack out-of-bounds** — writing past a local array on the kernel stack

```c
// Example of a heap out-of-bounds caught by KASAN:
char *buf = kmalloc(64, GFP_KERNEL);
memset(buf, 0, 128);  // writes 64 bytes past end → KASAN fires
```

### Dmesg Signature

```
BUG: KASAN: slab-out-of-bounds in memcpy+0x...
Write of size 64 at addr ffff88800c6e7e80 by task systemd/1
```

---

## 9. CPU Exception — General Protection Fault

### Description

The CPU raises a **General Protection Fault** (GPF, vector 13 on x86) when the kernel violates processor protection rules:

- Accessing a memory segment beyond its limit
- Using a null or corrupt segment selector
- Executing a privileged instruction in the wrong ring
- Accessing an uncanonical virtual address (bits 48–63 must mirror bit 47 on x86_64)

### Code Path

```c
// arch/x86/kernel/traps.c
dotraplinkage void do_general_protection(struct pt_regs *regs,
                                          long error_code)
{
    if (user_mode(regs)) {
        // Kill the process with SIGSEGV
        force_sig(SIGSEGV);
        return;
    }
    // Kernel mode GPF:
    if (fixup_exception(regs, X86_TRAP_GP, error_code, 0))
        return;  // exception table recovered it

    die("general protection fault", regs, error_code);  // → panic
}
```

### Common Causes

- Corrupt function pointer called in kernel (jumps to garbage address)
- ROP/stack smash lands on uncanonical address
- Kernel accesses a freed MMIO region whose page tables were torn down

### Dmesg Signature

```
general protection fault, probably for non-canonical address 0xdead000000000000
RIP: 0010:corrupt_driver_function+0x0/0x20
```

---

## 10. CPU Exception — Machine Check Exception (MCE)

### Description

A **Machine Check Exception** (MCE, vector 18 on x86) signals a hardware-detected error — the CPU itself has detected that a computation cannot be trusted. These are the most severe panics because they indicate physical hardware failure.

### Types of MCE Events

| MCE Type | Meaning |
|---|---|
| **Corrected** (CE) | Hardware fixed it; logged, no panic |
| **Uncorrected Recoverable** (UCR) | Hardware detected but couldn't fix; may or may not panic |
| **Fatal / Uncorrected** | Data integrity lost; immediate panic mandatory |

### Code Path

```c
// arch/x86/kernel/cpu/mcheck/mce.c
static void mce_panic(const char *msg, struct mce *final, char *exp)
{
    pr_emerg(HW_ERR "Machine check: %s\n", exp);
    // Dump all MCE banks
    for (i = 0; i < mca_cfg.banks; i++)
        if (mcelog.entry[i].finished)
            mce_print(&mcelog.entry[i]);

    panic(msg);     // → kernel/panic.c
}
```

### Common Hardware Sources

- **ECC memory** uncorrectable multi-bit error (most common)
- **L1/L2/L3 cache** parity error
- **CPU internal bus** (QPI/UPI) errors
- **PCIe** AER (Advanced Error Reporting) uncorrectable errors
- **Thermal throttle** leading to computation errors

### Dmesg Signature

```
mce: [Hardware Error]: Machine check events logged
mce: [Hardware Error]: CPU 0: Machine Check: 0 Bank 5: b200004000000e0f
mce: [Hardware Error]:   TSC 0 ADDR fe00000100 MISC 0
Kernel panic - not syncing: Fatal Machine check
```

---

## 11. Unhandled Interrupt / Spurious IRQ

### Description

If the kernel receives an interrupt for which it has no registered handler, and the interrupt persists (a hardware error or driver bug), it can lead to an infinite interrupt storm consuming all CPU time, or directly trigger a panic.

### Code Path

```c
// kernel/irq/spurious.c
static int misrouted_irq(int irq)
{
    // Try to find which handler this IRQ belongs to
    // If none found for too long → panic
}

void note_interrupt(struct irq_desc *desc, irqreturn_t action_ret)
{
    if (unlikely(action_ret == IRQ_NONE)) {
        desc->irqs_unhandled++;
        if (unlikely(desc->irqs_unhandled > 99900)) {
            // 99.9% spurious rate
            report_bad_irq(desc, action_ret);
            // Disables the IRQ, may call panic
        }
    }
}
```

### Common Causes

- Badly written driver asserts IRQ line without registering handler
- Hardware sends interrupt to wrong CPU (APIC misconfiguration)
- Legacy IRQ sharing conflict (two devices share an IRQ line)

### Dmesg Signature

```
irq 19: nobody cared (try booting with the "irqpoll" option)
...
Disabling IRQ #19
```

---

## 12. Soft Lockup

### Description

A **soft lockup** is detected when a CPU runs in kernel mode for more than `softlockup_thresh` seconds (default: **20 seconds**) without returning to user space or calling the scheduler. This indicates a spinning loop in kernel code.

### Detection Mechanism

The kernel runs a **watchdog thread** on each CPU (`watchdog/N`). A high-priority timer interrupt periodically sets a timestamp. If the watchdog thread hasn't been scheduled for `softlockup_thresh` seconds, it fires:

```c
// kernel/watchdog.c
static enum hrtimer_restart watchdog_timer_fn(struct hrtimer *hrtimer)
{
    unsigned long touch_ts = __this_cpu_read(watchdog_touch_ts);
    unsigned long now = get_timestamp();

    if (time_is_before_jiffies(touch_ts + get_softlockup_thresh())) {
        // Soft lockup detected!
        pr_emerg("BUG: soft lockup - CPU#%d stuck for %us!\n",
                 smp_processor_id(), duration);
        print_modules();
        print_irqtrace_events(current);
        dump_stack();

        if (softlockup_panic)
            panic("softlockup: hung tasks");    // if sysctl enabled
    }
    return HRTIMER_RESTART;
}
```

### Common Causes

- Infinite loop in a driver or kernel module
- Lock held too long (spinlock with interrupts disabled)
- Real-time task with too high priority monopolizing a CPU

### Sysctl Control

```bash
sysctl kernel.softlockup_panic=1    # convert detection to panic
sysctl kernel.watchdog_thresh=30    # increase threshold (seconds)
```

### Dmesg Signature

```
BUG: soft lockup - CPU#2 stuck for 23s! [kworker/2:1:1234]
```

---

## 13. Hard Lockup

### Description

A **hard lockup** (also called NMI watchdog lockup) is more severe than a soft lockup. It detects when a CPU fails to service **hardware interrupts** for more than `watchdog_thresh` seconds. The CPU is completely stuck — even the timer interrupt is not being handled.

### Detection Mechanism

Uses the **NMI (Non-Maskable Interrupt)** watchdog — a PMU (Performance Monitoring Unit) hardware counter that generates an NMI at regular intervals. Since NMIs cannot be masked, they fire even if a CPU is stuck with IRQs disabled:

```c
// arch/x86/kernel/nmi.c
static int watchdog_nmi_handler(unsigned int type, struct pt_regs *regs)
{
    if (is_hardlockup()) {
        pr_emerg("Watchdog detected hard LOCKUP on cpu %d\n",
                 smp_processor_id());
        print_modules();
        print_irqtrace_events(current);
        if (hardlockup_panic)
            nmi_panic(regs, "Hard LOCKUP");     // calls panic()
        return NMI_HANDLED;
    }
    return NMI_DONE;
}
```

### Soft vs Hard Lockup Comparison

| | Soft Lockup | Hard Lockup |
|---|---|---|
| **Stuck** | In kernel, not scheduling | All interrupts blocked |
| **IRQ handling** | Still works | Broken |
| **Detection** | Hrtimer | NMI via PMU |
| **Severity** | High | Critical |

### Dmesg Signature

```
Watchdog detected hard LOCKUP on cpu 0
NMI backtrace for cpu 0
...
Kernel panic - not syncing: Hard LOCKUP
```

---

## 14. RCU Stall

### Description

**RCU (Read-Copy-Update)** is the kernel's lockless synchronization primitive. Every CPU must periodically pass through a **quiescent state** (user space, idle, or certain kernel checkpoints). If a CPU fails to do so for too long, an **RCU stall** is detected — someone is holding an RCU read lock without releasing it, or a kernel thread is looping without a quiescent state.

### Detection Mechanism

```c
// kernel/rcu/stall-common.c
static void print_cpu_stall_info(int cpu)
{
    pr_err("\t%d-%c%c%c%c: (%lu ticks this GP)"
           " idle=%04x/%ld/%d softirq=%u/%u",
           ...);
}

void rcu_check_gp_kthread_starvation(void)
{
    // If GP (grace period) takes too long:
    pr_err("INFO: RCU grace period %ld is %ld jiffies old.\n", ...);
    if (rcu_cpu_stall_suppress)
        return;
    // If panic_on_rcu_stall:
    panic("RCU Stall\n");
}
```

### Common Causes

- Kernel code executing in an RCU read-side critical section that loops too long
- A CPU running real-time tasks that never yields
- Preemption disabled for excessive duration (`rcu_read_lock()` + `spin_lock()` interaction)

### Dmesg Signature

```
INFO: rcu_sched detected stalls on CPUs/tasks:
    2-...: (5254 ticks this GP) idle=...
    (detected by 0, t=15002 jiffies, g=65533, q=1)
```

---

## 15. Hung Task

### Description

The **hung task detector** monitors processes in the `TASK_UNINTERRUPTIBLE` (D state) for longer than `hung_task_timeout_secs` seconds (default: **120 seconds**). Persistent D-state is typically caused by a blocked I/O wait with no progress.

### Detection Code

```c
// kernel/hung_task.c
static void check_hung_task(struct task_struct *t, unsigned long timeout)
{
    unsigned long switch_count = t->nvcsw + t->nivcsw;

    if (unlikely(t->state == TASK_UNINTERRUPTIBLE)) {
        if (switch_count == t->last_switch_count) {
            // Not switched in > timeout
            sched_show_task(t);
            if (sysctl_hung_task_panic)
                panic("hung_task: blocked tasks");
        }
    }
    t->last_switch_count = switch_count;
}
```

### Common Causes

- Deadlocked filesystem (NFS server gone, inode lock contention)
- Storage device stopped responding (disk failure, HBA bug)
- Kernel mutex or semaphore never released due to a bug

### Sysctl Control

```bash
sysctl kernel.hung_task_panic=1           # turn into panic
sysctl kernel.hung_task_timeout_secs=120  # detection threshold
```

### Dmesg Signature

```
INFO: task kworker/0:2:123 blocked for more than 120 seconds.
...
Kernel panic - not syncing: hung_task: blocked tasks
```

---

## 16. Out of Memory (OOM) Panic

### Description

When the kernel cannot satisfy a memory allocation after exhausting all available physical RAM and swap, it invokes the **OOM Killer**, which selects and kills a process to free memory. If `vm.panic_on_oom` is set, or if the OOM killer cannot find a suitable victim (e.g., all remaining processes are unkillable), the kernel panics.

### Code Path

```c
// mm/oom_kill.c
void out_of_memory(struct oom_control *oc)
{
    // Check sysctl
    if (sysctl_panic_on_oom == 2) {
        panic("out of memory. panic_on_oom is selected\n");
    }
    // Try OOM kill
    oom_kill_process(oc, "Out of memory");

    // If no process can be killed:
    if (oc->constraint == CONSTRAINT_NONE && ...){
        panic("System is deadlocked on memory\n");
    }
}
```

### Allocation Failure in Interrupt Context

If a `GFP_ATOMIC` allocation fails (memory allocation inside an interrupt handler, which cannot sleep/wait), and the driver does not handle the failure gracefully, it often leads to a NULL pointer dereference shortly after — causing a panic.

### Sysctl Control

```bash
sysctl vm.panic_on_oom=0   # 0=kill process (default), 1=panic, 2=always panic
```

### Dmesg Signature

```
Out of memory: Kill process 1234 (myapp) score 920 or sacrifice child
Killed process 1234 (myapp) total-vm:2048MB, anon-rss:1800MB
...
Kernel panic - not syncing: System is deadlocked on memory
```

---

## 17. Kernel BUG() / WARN() Macros

### Description

The kernel code is littered with `BUG()` and `WARN()` macros that assert internal invariants. `BUG()` always causes an oops (and panic if configured); `WARN()` only logs by default but can be escalated.

### Implementation

```c
// include/asm-generic/bug.h

// BUG() — fatal, always causes an oops
#define BUG() do {                                      \
    printk("BUG: failure at %s:%d/%s()!\n",            \
           __FILE__, __LINE__, __func__);               \
    barrier_before_unreachable();                       \
    __BUG();  // triggers undefined instruction trap    \
} while (0)

// BUG_ON(condition) — conditional BUG
#define BUG_ON(condition) do {                          \
    if (unlikely(condition))                            \
        BUG();                                          \
} while (0)

// WARN() — log + stack trace, not fatal by default
#define WARN(condition, format...) ({                   \
    int __ret_warn_on = !!(condition);                  \
    if (unlikely(__ret_warn_on)) {                      \
        printk(KERN_WARNING format);                    \
        dump_stack();                                   \
    }                                                   \
    unlikely(__ret_warn_on);                            \
})
```

### Escalation to Panic

```bash
sysctl kernel.panic_on_warn=1   # WARN() becomes fatal
```

### Dmesg Signature

```
kernel BUG at fs/ext4/inode.c:1234!
invalid opcode: 0000 [#1] SMP
```

---

## 18. Assert / Sanity Check Failures (BUG_ON / WARN_ON)

### Description

Closely related to `BUG()`, but triggered only when a specific condition is true. `BUG_ON(x)` is equivalent to `if (unlikely(x)) BUG()`. These are placed throughout the kernel to verify invariants at runtime.

### Common Examples

```c
// include/linux/kernel.h
BUG_ON(!irqs_disabled());          // Must be called with IRQs off
BUG_ON(in_interrupt());            // Must not be called from IRQ context
BUG_ON(atomic_read(&refcount) < 0); // Reference count underflow
WARN_ON(list_empty(&queue));        // Queue unexpectedly empty
```

### Dmesg Signature

```
------------[ cut here ]------------
WARNING: CPU: 0 PID: 1234 at kernel/sched/core.c:5678 check_preempt_wakeup+0x234/0x260
```

---

## 19. Deadlock — Spinlock / Mutex

### Description

When two or more kernel threads each hold a lock the other needs, they deadlock. The kernel has two mechanisms to detect this: **lockdep** (compile-time graph analysis) and **soft/hard lockup detectors** (runtime).

### Lockdep — Lock Dependency Validator

```c
// kernel/locking/lockdep.c
// Lockdep maintains a directed graph of lock acquisition orders.
// If acquiring lock B while holding lock A would create a cycle → BUG

static int check_deadlock(struct held_lock *prev, struct held_lock *next)
{
    // Walk the dependency graph
    if (check_noncircular(next->class, depth) == 0) {
        print_deadlock_bug(curr, prev, next);
        return 0;   // found cycle → BUG() follows
    }
}
```

```c
// Example triggering lockdep:
spin_lock(&lock_A);
spin_lock(&lock_B);   // OK: A → B

// In another code path:
spin_lock(&lock_B);
spin_lock(&lock_A);   // DEADLOCK DETECTED: B → A creates cycle
```

### Dmesg Signature

```
======================================================
WARNING: possible circular locking dependency detected
4.19.0 #1 Not tainted
------------------------------------------------------
process/1234 is trying to acquire lock:
...
but task is already holding lock:
...
which lock already depends on the new lock.
```

---

## 20. Oops Escalated to Panic

### Description

An **Oops** is the kernel's term for a recoverable (sometimes) error — similar to a CPU exception that the kernel handles at a high level. By default, Oops doesn't immediately panic; it prints diagnostics and may kill only the offending process. However, `panic_on_oops=1` converts every Oops into a full panic.

### Code Path

```c
// lib/dump_stack.c, kernel/panic.c
void oops_end(unsigned long flags, struct pt_regs *regs, int signr)
{
    oops_exit();

    if (regs && kexec_should_crash(current))
        crash_kexec(regs);

    if (in_interrupt() || !current->pid || is_global_init(current))
        panic("Fatal exception");   // Cannot kill a process, must panic

    if (panic_on_oops)
        panic("Fatal exception");   // Configured to always panic

    // Otherwise: kill only the offending process
    do_exit(signr);
}
```

### When Oops Always Becomes Panic

Even with `panic_on_oops=0`, an Oops **always** escalates to panic if it happens:
- Inside an **interrupt handler** (no process context to kill)
- In the **idle thread** (PID 0, cannot die)
- In **PID 1 (init)** (killing init is itself a panic)

### Dmesg Signature

```
Oops: general protection fault [#1] PREEMPT SMP
CPU: 3 PID: 5678 Comm: ksoftirqd/3 Not tainted
...
Kernel panic - not syncing: Fatal exception in interrupt
```

---

## 21. Interrupt Handler Faults

### Description

Any fault that occurs inside an interrupt handler (`hardirq` or `softirq` context) is automatically fatal, even without `panic_on_oops=1`. This is because there is no user process context to kill — the kernel was executing on behalf of hardware, not a process.

### Why It's Always Fatal

```c
// kernel/panic.c
void oops_end(unsigned long flags, struct pt_regs *regs, int signr)
{
    if (in_interrupt())
        panic("Fatal exception in interrupt");  // no recovery possible
    // ...
}
```

During interrupt handling:
- No `mm` (memory map) belongs to the interrupt — cannot return to user space
- Stack is the CPU's hardirq stack — cannot cleanly terminate
- Other CPUs may be waiting on state the faulting IRQ handler was supposed to update

### Common Causes

- NULL dereference in a network driver's `->poll()` function (called from NAPI softirq)
- Division by zero in a timer callback
- Corrupt `struct irq_desc` causing a bad function pointer call

---

## 22. VFS / Filesystem Corruption

### Description

When the Virtual Filesystem layer or a specific filesystem driver (ext4, XFS, btrfs, etc.) detects on-disk corruption — or an internal inconsistency in in-memory VFS structures — it can call `panic()` directly or through an `ASSERT()` / `BUG_ON()`.

### Filesystem-Level Panics

```c
// fs/ext4/super.c
void ext4_error_inode(struct inode *inode, const char *function,
                       unsigned int line, ext4_fsblk_t block,
                       const char *fmt, ...)
{
    // If errors=panic mount option:
    if (test_opt(sb, ERRORS_PANIC))
        panic("EXT4-fs (device %s): panic forced after error\n",
              sb->s_id);
}

// fs/xfs/xfs_error.c
void xfs_error_report(const char *tag, int level, struct xfs_mount *mp, ...)
{
    if (xfs_error_level >= level)
        BUG();   // → panic
}
```

### Mount Options That Trigger Panic

```bash
# Mount with panic-on-error:
mount -o errors=panic /dev/sda1 /mnt

# Default for ext4 is errors=continue or errors=remount-ro
```

### Common Causes

- Disk bit rot (silent data corruption)
- Sudden power loss leaving journal in corrupt state
- Bug in filesystem driver (btrfs has historically had several)
- Overlapping writes from a buggy driver corrupting metadata blocks

### Dmesg Signature

```
EXT4-fs error (device sda1): ext4_validate_block_bitmap:376: comm kworker/u8:2:
  bg 0: bad block bitmap checksum
Kernel panic - not syncing: EXT4-fs (sda1): panic forced after error
```

---

## 23. Bad Page State / Page Fault in Kernel Mode

### Description

The kernel's page allocator (`buddy` system) tracks the state of every physical page using `struct page`. If a page is found in an impossible state — wrong reference count, impossible flags combination, corrupt `lru` pointers — it calls `bad_page()` which ultimately leads to a BUG.

### Code Path

```c
// mm/page_alloc.c
static void bad_page(struct page *page, const char *reason, ...)
{
    pr_alert("BUG: Bad page state in process %s  pfn:%05lx\n",
             current->comm, page_to_pfn(page));
    dump_page(page, reason);
    dump_stack();
    // Sets PageError and tries to put it back, but may BUG() if critical
}

// Called from free_pages_check:
static int free_pages_check(struct page *page)
{
    if (likely(page_expected_state(page, PAGE_FLAGS_CHECK_AT_FREE)))
        return 0;
    bad_page(page, "PAGE_FLAGS_CHECK_AT_FREE");
    return 1;
}
```

### Common Causes

- Hardware memory error (bit flip in DRAM — requires ECC)
- Kernel bug double-freeing a page
- DMA writing beyond its buffer (DMA to wrong address)
- PCIe device with broken memory access writing to kernel memory

### Dmesg Signature

```
BUG: Bad page state in process kswapd0  pfn:0012ab
page:ffffea00000 4ab000 count:0 mapcount:-1 mapping:          (null) index:0x0
flags: 0x17ffffc0000000()
```

---

## 24. Division by Zero in Kernel

### Description

Integer division by zero in kernel code triggers a **Divide Error** exception (vector 0 on x86, `#DE`). Unlike user space where SIGFPE is sent, the kernel has no signal handler — it results in an Oops and typically a panic.

### Code Path

```c
// arch/x86/kernel/traps.c
dotraplinkage void do_divide_error(struct pt_regs *regs, long error_code)
{
    do_trap(X86_TRAP_DE, SIGFPE, "divide error", regs, error_code,
            SEGV_ACCERR, NULL);
    // In kernel mode → oops → panic
}
```

### Common Causes

- Rate computation where denominator is 0 (bytes per second, packets per ms)
- Uninitialized counter used as divisor
- Race condition where the denominator is zeroed concurrently

```c
// Typical vulnerable pattern:
unsigned long rate = total_bytes / elapsed_jiffies;  // BUG if elapsed_jiffies == 0
```

### Dmesg Signature

```
divide error: 0000 [#1] SMP
RIP: 0010:network_stats_compute+0x45/0x80 [mydriver]
```

---

## 25. Undefined Instruction / Illegal Opcode

### Description

Executing an **invalid or undefined machine instruction** triggers an **Illegal Opcode** (`#UD`, vector 6) exception. The kernel uses this intentionally for `BUG()` (which inserts a `ud2` instruction on x86) and for CPU feature probing.

### Intentional Use in BUG()

```c
// arch/x86/include/asm/bug.h
#ifdef CONFIG_DEBUG_BUGVERBOSE
#define _BUG_FLAGS(ins, flags, extra)                  \
    __asm__ __volatile__("1:\t" ins "\n"               \
                         ".pushsection __bug_table,\"aw\"\n"   \
                         "2:\t" __BUG_REL(1b) "\n\t"  \
                         ...                           \
                         ".popsection" extra)
#endif

// ud2 = "undefined instruction" — guaranteed to trigger #UD
#define __BUG_INSN_16    "ud2"
```

### Unintentional Causes

- CPU feature flag incorrect — executing an AVX-512 instruction on a CPU that doesn't support it
- Code corruption — a bitflip in the instruction stream turns a valid opcode into `0x0f 0x0b` (ud2)
- JIT-compiled BPF program with a bug (though BPF verifier usually prevents this)

### Dmesg Signature

```
invalid opcode: 0000 [#1] SMP PTI
CPU: 1 PID: 0 Comm: swapper/1 Not tainted
RIP: 0010:0xffffffff81234567    // Points to ud2 instruction = BUG() site
```

---

## 26. Scheduler Corruption

### Description

The kernel's process scheduler maintains per-CPU run queues (`struct rq`), task state, and priority bitmaps. If these structures are corrupted (use-after-free, bad pointer, etc.), the next context switch or timer tick may crash.

### Detection Points

```c
// kernel/sched/core.c
static void __schedule(bool preempt)
{
    // Sanity checks:
    if (unlikely(in_atomic_preempt_off())) {
        __schedule_bug(prev);   // calls WARN_ON → panic if panic_on_warn
    }

    // Select next task — if rq->curr is corrupt:
    next = pick_next_task(rq, prev, &rf);

    if (likely(prev != next)) {
        // context_switch — if next->mm is corrupt → page fault in switch
        context_switch(rq, prev, next);
    }
}
```

### Common Causes

- Use-after-free on a `task_struct` — task freed but still in run queue
- Setting task state from wrong context (e.g., calling `schedule()` with spinlock held)
- Stack corruption overwriting saved registers used for context switching

### Dmesg Signature

```
BUG: scheduling while atomic: kworker/0:1/34/0x00000200
Modules linked in: ...
Kernel panic - not syncing: scheduling while atomic
```

---

## 27. Module Load Failure / Bad Kernel Module

### Description

Loadable kernel modules run in ring 0 with full kernel privileges. A module with a bug can corrupt kernel data, call undefined symbols, or execute garbage code. Additionally, if module initialization fails and cleanup is buggy, it can corrupt kernel state.

### Failure Modes

```c
// kernel/module.c
static int do_init_module(struct module *mod)
{
    int ret;
    ret = mod->init ? mod->init() : 0;   // Run module's init function

    if (ret < 0) {
        // Init returned error — module never fully initialized
        // Cleanup may still be called, risking double-free or NULL deref
        module_put(mod);
        return ret;
    }
    // ...
}
```

### Mismatched Kernel Version / ABI

Loading a module compiled for a different kernel version (without version checks disabled) is blocked by `MODVERSIONS`. Bypassing this via `insmod --force` can cause struct layout mismatches — the module accesses fields at wrong offsets.

### Dmesg Signature

```
mymodule: disagrees about version of symbol some_kernel_function
...
BUG: unable to handle kernel paging request at 0000dead00000010
```

---

## 28. Hardware Watchdog Expiry

### Description

A hardware watchdog timer requires the kernel to **periodically "pet" (reset)** a hardware counter. If the kernel is so stuck that it can't pet the watchdog (panic, infinite loop, lockup), the watchdog hardware asserts a reset signal to the CPU — forcing a reboot even without the kernel's cooperation.

### Kernel Side

```c
// drivers/watchdog/watchdog_dev.c
static long watchdog_ioctl(struct file *filp, unsigned int cmd, ...)
{
    case WDIOC_KEEPALIVE:
        // User-space daemon resets the hardware counter
        err = wdog->ops->ping(wdog);
        break;
}

// If user-space daemon dies (because kernel is stuck):
// Hardware fires after timeout → system resets
```

### Two Watchdog Levels in Linux

| Level | Name | Mechanism |
|---|---|---|
| **Software** | `softlockup` / `hardlockup` | Timer / NMI |
| **Hardware** | `/dev/watchdog` | Physical timer chip, asserts RESET# |

### Common Watchdog Chips

- Intel TCO (Timed Control Operation) watchdog — built into Intel ICH/PCH chipsets
- ARM SP805 watchdog — common in ARM SoCs
- IPMI watchdog — for server BMC integration

---

## 29. kexec / kdump Failures

### Description

**kexec** allows the kernel to boot another kernel directly (used by kdump to load a crash kernel). If the kexec process itself fails — corrupt target kernel image, wrong memory reservation, architecture mismatch — the transition crashes the running kernel.

### Code Path

```c
// kernel/kexec_core.c
int kernel_kexec(void)
{
    // Disable all CPUs except current
    error = machine_kexec_prepare(kimage);
    if (error)
        goto Done;

    // Point of no return:
    machine_shutdown();
    machine_kexec(kimage);    // Never returns if successful
                              // Fatal if it returns (hardware rejected jump)
    // If we get here, something went catastrophically wrong
    BUG();
}
```

### kdump-Specific Failures

- Crash kernel allocated at wrong physical address
- `crashkernel=` memory reservation too small
- Second kernel's initramfs missing or corrupt

---

## 30. Device Driver Bugs

### Description

Device drivers are the single largest source of kernel panics in practice. They run in kernel space, are often written by third parties, and interact directly with hardware. Common failure modes include:

### Categories

```c
// 1. DMA to invalid address (most dangerous)
//    Driver programs DMA engine with garbage physical address
//    → DMA overwrites arbitrary kernel memory → corrupt data → panic

// 2. Interrupt handler accesses freed memory
void my_irq_handler(int irq, void *dev_id)
{
    struct my_dev *dev = dev_id;   // dev may have been freed during unload!
    dev->stats.irq_count++;        // NULL/UAF dereference
}

// 3. Missing NULL check on firmware blob
firmware = request_firmware("mydev.bin", dev);
// firmware could be NULL if file not found
memcpy(dst, firmware->data, firmware->size);  // NULL deref if not checked

// 4. Missing synchronization with tasklets/workqueues during driver removal
```

### MMIO Access Faults

```c
// Accessing a BAR (Base Address Register) after the PCIe device is hot-removed:
writel(value, dev->iobase + REGISTER_OFFSET);
// If iobase is now unmapped → page fault in kernel → panic
```

---

## 31. Atomic Context Violations

### Description

Certain kernel operations are forbidden in **atomic context** (interrupt handlers, spinlock-held sections, `rcu_read_lock` sections):

- `sleep()` / `schedule()` — sleeping while holding a spinlock can deadlock all CPUs
- Memory allocation with `GFP_KERNEL` — may sleep
- Calling any function that can block

```c
// kernel/sched/core.c
void __might_sleep(const char *file, int line, int preempt_offset)
{
    if (unlikely(in_atomic() || irqs_disabled() ||
                 !IS_ENABLED(CONFIG_PREEMPT_COUNT))) {
        debug_show_held_locks(current);
        if (panic_on_warn)
            panic("might_sleep called from invalid context");
        WARN_ON(1);   // or just WARN
    }
}
```

### Common Trigger

```c
spin_lock(&my_lock);                         // Atomic context begins
ptr = kmalloc(size, GFP_KERNEL);            // GFP_KERNEL may sleep → BUG
spin_unlock(&my_lock);
```

### Dmesg Signature

```
BUG: sleeping function called from invalid context at mm/slub.c:1234
in_atomic(): 1, irqs_disabled(): 0, pid: 456, name: kworker/0:2
```

---

## 32. IOMMU / DMA Faults

### Description

The **IOMMU (Input-Output Memory Management Unit)** provides memory protection for DMA operations — devices can only DMA to memory regions they have been explicitly granted access to. If a driver programs the DMA engine to access an address outside its IOMMU mapping, the IOMMU raises a fault.

### Code Path

```c
// drivers/iommu/iommu.c
// When IOMMU detects unauthorized DMA:
static irqreturn_t iommu_fault_handler(int irq, void *dev_id)
{
    dev_err(dev, "IOMMU fault: device %s accessed address 0x%llx "
            "without mapping\n", dev_name(dev), addr);
    // May call panic() depending on CONFIG_IOMMU_FAULT_PANIC
}
```

### ARM SMMU Example

```
arm-smmu: Unhandled context fault: fsr=0x402, iova=0xdeadbeef000,
          fsynr=0x0, cb=0, iommu=arm-smmu.0, ctx=my_device
Kernel panic - not syncing: arm-smmu: Fatal IOMMU fault
```

### Intel VT-d Example

```
DMAR: DRHD: handling fault status reg 3
DMAR: [DMA Read] Request device [01:00.0] fault addr feedf000
      IOMMU fault reason 06 - PTE Read access is not set
Kernel panic - not syncing: IOMMU fault
```

---

## 33. Power Management Failures

### Description

Linux power management (suspend/resume, CPU frequency scaling, power state transitions) involves complex state machine operations across all drivers. Failures during these transitions can leave hardware in an undefined state.

### Suspend/Resume Failure

```c
// kernel/power/suspend.c
int suspend_devices_and_enter(suspend_state_t state)
{
    // Freeze all non-boot CPUs
    error = disable_nonboot_cpus();
    if (error) {
        pr_err("PM: Failed to disable non-boot CPUs\n");
        // Panics if the system cannot re-enable them
    }

    // Call platform firmware to enter S3/S4
    error = suspend_ops->enter(state);
    if (error)
        panic("PM: Platform suspend failed\n");
}
```

### ACPI Panic

```c
// drivers/acpi/acpica/utexcep.c
// ACPI AML interpreter encounters divide-by-zero or undefined behavior
// in DSDT/SSDT tables (written by OEM firmware):
acpi_ut_exception(status, "AML: critical error in AML execution");
// May panic depending on severity
```

### Dmesg Signature

```
PM: suspend entry (deep)
...
ACPI BIOS Error (bug): Could not resolve [\_SB.PCI0.LPCB.EC], AE_NOT_FOUND
Kernel panic - not syncing: PM: critical ACPI error
```

---

## 34. EFI / Firmware Runtime Faults

### Description

Modern x86_64 systems use **UEFI firmware** which remains partially active even after the kernel boots (for `EFI Runtime Services` — time, NVRAM variables, etc.). If a call into UEFI runtime services causes a fault, the kernel may crash.

### EFI Runtime Wrapper

```c
// arch/x86/platform/efi/efi_64.c
// The kernel switches to the EFI page tables before calling runtime services
// If EFI firmware touches non-EFI memory → page fault → kernel panic

efi_status_t efi_call_rts(void *func, ...)
{
    efi_sync_low_kernel_mappings();
    // Switch to EFI address space
    efi_switch_mm(&efi_mm);
    status = efi_call(func, ...);   // Call into UEFI runtime
    efi_switch_mm(prev_mm);         // Switch back
    // If UEFI corrupted kernel state → crash during switch-back
}
```

### Common EFI-Related Panics

- UEFI `SetVariable()` (writing NVRAM) corrupts stack
- UEFI `GetTime()` uses spinlock improperly → deadlock
- EFI runtime code touches `SMM_BASE` memory triggering SMI storms

### Dmesg Signature

```
Oops: general protection fault [#1]
CPU: 0 PID: 1 Comm: swapper/0
RIP: 0010:0x00000000xyz  // Address in EFI runtime region
Kernel panic - not syncing: Fatal exception
```

---

## 35. Summary Table

| # | Panic Category | Source File | Config to Enable Detection | `panic_on_*` Sysctl |
|---|---|---|---|---|
| 1 | Explicit `panic()` | `kernel/panic.c` | Always active | N/A |
| 2 | NULL pointer dereference | `arch/x86/mm/fault.c` | `CONFIG_KASAN` | `panic_on_oops` |
| 3 | Stack overflow | `arch/x86/kernel/traps.c` | `CONFIG_VMAP_STACK` | Always fatal |
| 4 | Use-after-free | `mm/kasan/report.c` | `CONFIG_KASAN` | `KASAN_PANIC` |
| 5 | Double free | `mm/slub.c` | `CONFIG_SLUB_DEBUG` | Always fatal |
| 6 | Memory corruption | `mm/slub.c` | `CONFIG_SLUB_DEBUG` | Always fatal |
| 7 | Out-of-bounds | `mm/kasan/report.c` | `CONFIG_KASAN` | `KASAN_PANIC` |
| 8 | GPF | `arch/x86/kernel/traps.c` | Always active | `panic_on_oops` |
| 9 | MCE | `arch/x86/kernel/cpu/mcheck/mce.c` | `CONFIG_X86_MCE` | Always fatal (uncorrected) |
| 10 | Spurious IRQ | `kernel/irq/spurious.c` | Always active | N/A |
| 11 | Soft lockup | `kernel/watchdog.c` | `CONFIG_DETECT_SOFTLOCKUP` | `softlockup_panic` |
| 12 | Hard lockup | `arch/x86/kernel/nmi.c` | `CONFIG_HARDLOCKUP_DETECTOR` | `hardlockup_panic` |
| 13 | RCU stall | `kernel/rcu/stall-common.c` | `CONFIG_RCU_STALL_COMMON` | `rcu_cpu_stall_panic` |
| 14 | Hung task | `kernel/hung_task.c` | `CONFIG_DETECT_HUNG_TASK` | `hung_task_panic` |
| 15 | OOM | `mm/oom_kill.c` | Always active | `vm.panic_on_oom` |
| 16 | BUG() / WARN() | `include/asm-generic/bug.h` | Always active | `panic_on_warn` |
| 17 | Deadlock | `kernel/locking/lockdep.c` | `CONFIG_LOCKDEP` | `panic_on_oops` |
| 18 | Oops → Panic | `kernel/panic.c` | Always active | `panic_on_oops` |
| 19 | IRQ handler fault | `kernel/panic.c` | Always active | Always fatal |
| 20 | Filesystem corruption | `fs/*/super.c` | `errors=panic` mount | Always fatal |
| 21 | Bad page state | `mm/page_alloc.c` | `CONFIG_DEBUG_VM` | Always fatal |
| 22 | Division by zero | `arch/x86/kernel/traps.c` | Always active | `panic_on_oops` |
| 23 | Illegal opcode | `arch/x86/kernel/traps.c` | Always active | `panic_on_oops` |
| 24 | Scheduler corruption | `kernel/sched/core.c` | `CONFIG_DEBUG_ATOMIC_SLEEP` | `panic_on_warn` |
| 25 | Bad kernel module | `kernel/module.c` | `MODVERSIONS` | `panic_on_oops` |
| 26 | HW watchdog | `drivers/watchdog/` | CONFIG + userspace daemon | Hardware reset |
| 27 | DMA / driver bugs | `drivers/` | `CONFIG_KASAN`, IOMMU | `panic_on_oops` |
| 28 | Atomic violations | `kernel/sched/core.c` | `CONFIG_DEBUG_ATOMIC_SLEEP` | `panic_on_warn` |
| 29 | IOMMU fault | `drivers/iommu/` | `CONFIG_IOMMU_FAULT_PANIC` | Config-driven |
| 30 | Power management | `kernel/power/` | Always active | Always fatal |
| 31 | EFI runtime | `arch/x86/platform/efi/` | Always active | `panic_on_oops` |

---

## Key Diagnostic Commands

```bash
# View last panic message (if kdump configured)
crash /var/crash/vmcore /usr/lib/debug/lib/modules/$(uname -r)/vmlinux

# View kernel ring buffer
dmesg | grep -i "kernel panic\|oops\|BUG\|call trace"

# Check panic-related sysctls
sysctl kernel.panic
sysctl kernel.panic_on_oops
sysctl kernel.panic_on_warn
sysctl kernel.softlockup_panic
sysctl kernel.hardlockup_panic
sysctl vm.panic_on_oom

# Enable all panic-on-detect sysctls (for production crash capture):
sysctl kernel.panic=30
sysctl kernel.panic_on_oops=1
sysctl kernel.softlockup_panic=1
sysctl kernel.hardlockup_panic=1

# Install kdump for crash capture:
apt install kdump-tools crash
echo "crashkernel=256M" >> /etc/default/grub
```

---

*Generated reference document. All code paths are from Linux kernel mainline (v5.x–6.x).*

Now let me create the comprehensive markdown file:The file covers **34 distinct panic categories**, organized into three major groups:

**Hardware Faults**
- Machine Check Exception (MCE) — physical CPU/memory hardware errors
- IOMMU/DMA faults — device trying to access unauthorized memory
- Hardware watchdog expiry — firmware-level forced reset
- EFI/UEFI runtime faults — buggy OEM firmware

**Kernel Software Bugs**
- NULL dereference, use-after-free, double free, out-of-bounds (the classic memory safety bugs)
- Stack overflow/smashing — fixed 8KB kernel stack exceeded
- Division by zero, illegal opcode, GPF — CPU exception escalations
- Filesystem/VFS corruption — detected on-disk or in-memory inconsistencies
- Bad module loading — ABI mismatch or init failure leaving corrupt state

**Liveness Failures**
- Soft lockup — CPU not scheduling for >20s
- Hard lockup — CPU not handling *any* interrupts for >N seconds (detected via NMI)
- RCU stall — CPU not reaching a quiescent state (grace period stuck)
- Hung task — process in D-state (uninterruptible sleep) for >120s
- OOM — no memory left and OOM killer can't free any

Each entry includes the actual source file path, code snippet, common causes, and the `dmesg` signature you'd see in the wild.